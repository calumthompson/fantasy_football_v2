from dataclasses import dataclass

import pandas as pd
import pulp

from domain.snapshot import FPLSnapshot
from prediction.models.base_model import ModelResult


@dataclass(frozen=True)
class TransferRecommendation:
    """The best legal one-player transfer for a manager's current squad."""

    outgoing_player_id: int
    outgoing_player_name: str
    incoming_player_id: int
    incoming_player_name: str
    position: str
    outgoing_value: int
    incoming_value: int
    bank: int
    outgoing_predicted_points: float
    incoming_predicted_points: float
    predicted_points_gain: float
    gameweeks: tuple[int, ...]


@dataclass(frozen=True)
class LineupRecommendation:
    """Recommended starters, captaincy, and substitutes for one gameweek."""

    gameweek: int
    starting_player_ids: tuple[int, ...]
    substitute_player_ids: tuple[int, ...]
    captain_player_id: int
    vice_captain_player_id: int
    predicted_points: dict[int, float]


def _get_upcoming_gameweeks(snapshot: FPLSnapshot) -> list[int]:
    next_gameweek = next(
        (gameweek.number for gameweek in snapshot.gameweeks if gameweek.is_next),
        None,
    )
    return sorted(
        {
            fixture.gameweek_number
            for player in snapshot.players
            for fixture in player.upcoming_fixtures
            if fixture.gameweek_number is not None
            and (next_gameweek is None or fixture.gameweek_number >= next_gameweek)
        }
    )


def _forecast_player_points(
    snapshot: FPLSnapshot,
    predictions: ModelResult,
    gameweeks: set[int],
) -> dict[int, float]:
    prediction_lookup = {
        (prediction.player_id, prediction.fixture_id): prediction.predicted_points
        for prediction in predictions.results
    }
    return {
        player.player_id: sum(
            prediction_lookup.get((player.player_id, fixture.fixture_id), 0.0)
            for fixture in player.upcoming_fixtures
            if fixture.gameweek_number in gameweeks
        )
        for player in snapshot.players
    }


def recommend_transfer(
    snapshot: FPLSnapshot,
    predictions: ModelResult,
    number_of_gameweeks: int = 5,
) -> TransferRecommendation:
    """Return the legal transfer with the largest forecast gain.

    Fixture predictions are summed across the next ``number_of_gameweeks``.
    The incoming player must play in the same position, keep the squad within
    the three-player club limit, and cost no more than the manager's bank plus
    the outgoing player's value.

    The public FPL picks endpoint does not expose purchase/selling prices, so
    the MVP uses each player's current value as their sale value.
    """
    if number_of_gameweeks < 1:
        raise ValueError("number_of_gameweeks must be at least 1")

    available_gameweeks = _get_upcoming_gameweeks(snapshot)
    gameweeks = tuple(available_gameweeks[:number_of_gameweeks])
    if not gameweeks:
        raise ValueError("No upcoming gameweeks are available")

    forecast = _forecast_player_points(snapshot, predictions, set(gameweeks))

    picked_ids = set(
        snapshot.current_manager_team_picks.selected_player_ids
        + snapshot.current_manager_team_picks.substitute_player_ids
    )
    squad = [
        snapshot.get_player_by_id(player_id) for player_id in sorted(picked_ids)
    ]
    club_counts: dict[int, int] = {}
    for player in squad:
        club_counts[player.team_season_id] = club_counts.get(player.team_season_id, 0) + 1

    best: TransferRecommendation | None = None
    for outgoing in squad:
        maximum_price = snapshot.manager.bank + outgoing.value
        for incoming in snapshot.players:
            if incoming.player_id in picked_ids:
                continue
            if incoming.position_id != outgoing.position_id:
                continue
            if incoming.value > maximum_price:
                continue

            incoming_club_count = club_counts.get(incoming.team_season_id, 0)
            if incoming.team_season_id == outgoing.team_season_id:
                incoming_club_count -= 1
            if incoming_club_count >= 3:
                continue

            outgoing_points = forecast[outgoing.player_id]
            incoming_points = forecast[incoming.player_id]
            recommendation = TransferRecommendation(
                outgoing_player_id=outgoing.player_id,
                outgoing_player_name=outgoing.web_name,
                incoming_player_id=incoming.player_id,
                incoming_player_name=incoming.web_name,
                position=outgoing.position,
                outgoing_value=outgoing.value,
                incoming_value=incoming.value,
                bank=snapshot.manager.bank,
                outgoing_predicted_points=outgoing_points,
                incoming_predicted_points=incoming_points,
                predicted_points_gain=incoming_points - outgoing_points,
                gameweeks=gameweeks,
            )
            if best is None or recommendation.predicted_points_gain > best.predicted_points_gain:
                best = recommendation

    if best is None:
        raise ValueError("No legal transfer is available")
    return best


def recommend_lineup_after_transfer(
    snapshot: FPLSnapshot,
    predictions: ModelResult,
    transfer: TransferRecommendation | None,
) -> LineupRecommendation:
    """Optimise the next-gameweek XI after applying a recommended transfer."""
    upcoming_gameweeks = _get_upcoming_gameweeks(snapshot)
    if not upcoming_gameweeks:
        raise ValueError("No upcoming gameweeks are available")
    gameweek = upcoming_gameweeks[0]
    forecast = _forecast_player_points(snapshot, predictions, {gameweek})

    squad_ids = set(
        snapshot.current_manager_team_picks.selected_player_ids
        + snapshot.current_manager_team_picks.substitute_player_ids
    )
    if transfer is not None:
        squad_ids.remove(transfer.outgoing_player_id)
        squad_ids.add(transfer.incoming_player_id)

    squad = [snapshot.get_player_by_id(player_id) for player_id in squad_ids]
    if len(squad) != 15:
        raise ValueError("A valid squad must contain exactly 15 players")

    problem = pulp.LpProblem("recommended_lineup", pulp.LpMaximize)
    selected = {
        player.player_id: pulp.LpVariable(
            f"start_{player.player_id}", cat="Binary"
        )
        for player in squad
    }
    problem += pulp.lpSum(
        selected[player.player_id] * forecast[player.player_id] for player in squad
    )
    problem += pulp.lpSum(selected.values()) == 11

    position_limits = {
        "GKP": (1, 1),
        "DEF": (3, 5),
        "MID": (2, 5),
        "FWD": (1, 3),
    }
    for position, (minimum, maximum) in position_limits.items():
        position_players = [
            selected[player.player_id] for player in squad if player.position == position
        ]
        problem += pulp.lpSum(position_players) >= minimum
        problem += pulp.lpSum(position_players) <= maximum

    status = problem.solve(pulp.PULP_CBC_CMD(msg=False))
    if pulp.LpStatus[status] != "Optimal":
        raise ValueError(f"No valid lineup found: {pulp.LpStatus[status]}")

    starting_ids = {
        player.player_id
        for player in squad
        if selected[player.player_id].value() > 0.5
    }
    starters = sorted(
        (player for player in squad if player.player_id in starting_ids),
        key=lambda player: (-forecast[player.player_id], player.web_name),
    )
    substitute_goalkeepers = sorted(
        (
            player
            for player in squad
            if player.player_id not in starting_ids and player.position == "GKP"
        ),
        key=lambda player: (-forecast[player.player_id], player.web_name),
    )
    substitute_outfielders = sorted(
        (
            player
            for player in squad
            if player.player_id not in starting_ids and player.position != "GKP"
        ),
        key=lambda player: (-forecast[player.player_id], player.web_name),
    )

    return LineupRecommendation(
        gameweek=gameweek,
        starting_player_ids=tuple(player.player_id for player in starters),
        substitute_player_ids=tuple(
            player.player_id
            for player in substitute_goalkeepers + substitute_outfielders
        ),
        captain_player_id=starters[0].player_id,
        vice_captain_player_id=starters[1].player_id,
        predicted_points=forecast,
    )


def create_optimal_team(
    data: pd.DataFrame,
    target_column: str,
    excluded_player_names: list[str] | None = None,
) -> pd.DataFrame:
    """Return the highest-scoring valid FPL squad within a £100m budget.

    Args:
        data: Candidate players and their squad attributes.
        target_column: Column maximised by the optimiser.
        excluded_player_names: Player names that cannot be selected.
    """
    position_constraints = {
        "GKP": 2,
        "DEF": 5,
        "MID": 5,
        "FWD": 3,
    }

    budget = 1000  # Player values are stored in tenths of a million pounds.
    max_players_per_team = 3

    required_columns = {"name", "position", "team", "value", target_column}
    missing_columns = required_columns.difference(data.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    excluded_player_names = excluded_player_names or []
    players = data.loc[~data["name"].isin(excluded_player_names)].reset_index(drop=True)
    if players[["position", "team", "value", target_column]].isna().any().any():
        raise ValueError("Position, team, value, and forecast columns cannot be null.")

    problem = pulp.LpProblem("the_draft", pulp.LpMaximize)
    selected = {
        index: pulp.LpVariable(f"select_{index}", cat="Binary")
        for index in players.index
    }

    problem += pulp.lpSum(
        selected[index] * players.at[index, target_column] for index in players.index
    )
    problem += (
        pulp.lpSum(
            selected[index] * players.at[index, "value"] for index in players.index
        )
        <= budget
    )

    for position, required_count in position_constraints.items():
        matching_players = players.index[players["position"] == position]
        problem += (
            pulp.lpSum(selected[index] for index in matching_players) == required_count
        )

    for team in players["team"].unique():
        matching_players = players.index[players["team"] == team]
        problem += (
            pulp.lpSum(selected[index] for index in matching_players)
            <= max_players_per_team
        )

    status = problem.solve(pulp.PULP_CBC_CMD(msg=False))
    if pulp.LpStatus[status] != "Optimal":
        raise ValueError(f"No valid team found: {pulp.LpStatus[status]}")

    selected_indices = [
        index for index in players.index if selected[index].value() > 0.5
    ]
    return players.loc[selected_indices].reset_index(drop=True)
