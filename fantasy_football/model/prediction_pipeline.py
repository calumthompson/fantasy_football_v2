"""Production pipeline for upcoming fixture-level FPL point forecasts."""

from typing import Protocol

import pandas as pd

from fantasy_football.fpl_api import FPLAPIClient, FPLSnapshot
from fantasy_football.model.base_models.in_season import (
    InSeasonPredictor,
    build_api_inseason_features,
)
from fantasy_football.model.base_models.pre_season import (
    PreSeasonPredictor,
    build_api_player_features,
)
from fantasy_football.model.ensemble import EnsemblePredictor
from fantasy_football.model.season_context import get_promoted_teams


class SnapshotLoader(Protocol):
    def load_full_snapshot(self) -> FPLSnapshot: ...


def _next_gameweek(snapshot: FPLSnapshot) -> int:
    upcoming_gameweeks = {
        fixture.gameweek_number
        for fixture in snapshot.fixtures
        if not fixture.started and fixture.gameweek_number is not None
    }
    if not upcoming_gameweeks:
        raise ValueError("The FPL snapshot has no scheduled upcoming fixtures")

    preferred_gameweeks = [
        gameweek.number
        for gameweek in snapshot.gameweeks
        if gameweek.is_current or gameweek.is_next
    ]
    for gameweek_number in preferred_gameweeks:
        if gameweek_number in upcoming_gameweeks:
            return gameweek_number
    return min(upcoming_gameweeks)


def _season_name(snapshot: FPLSnapshot, gameweek_number: int) -> str:
    gameweek = next(
        (
            gameweek
            for gameweek in snapshot.gameweeks
            if gameweek.number == gameweek_number
        ),
        None,
    )
    if gameweek is None:
        raise ValueError(f"Gameweek {gameweek_number} is missing from the snapshot")
    start_year = gameweek.deadline.year
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def predict_upcoming_fixtures_from_fpl(
    client: SnapshotLoader | None = None,
    preseason_predictor: PreSeasonPredictor | None = None,
    inseason_predictor: InSeasonPredictor | None = None,
    ensemble_predictor: EnsemblePredictor | None = None,
) -> pd.DataFrame:
    """Download FPL data and forecast points for the next gameweek's fixtures."""
    client = client or FPLAPIClient()
    preseason_predictor = preseason_predictor or PreSeasonPredictor()
    inseason_predictor = inseason_predictor or InSeasonPredictor()
    ensemble_predictor = ensemble_predictor or EnsemblePredictor()

    snapshot = client.load_full_snapshot()
    if not snapshot.players:
        raise ValueError("The FPL snapshot contains no players to score")

    gameweek_number = _next_gameweek(snapshot)
    season_name = _season_name(snapshot, gameweek_number)
    promoted_teams = get_promoted_teams(season_name)

    preseason_features = build_api_player_features(snapshot.players)
    preseason_features["preseason_model_score"] = preseason_predictor.predict(
        preseason_features
    ).to_numpy()
    preseason_scores = preseason_features.set_index("player_id")

    inseason_features = build_api_inseason_features(
        snapshot.players,
        snapshot.fixtures,
        gameweek_number,
    )
    inseason_features["inseason_model_score"] = inseason_predictor.predict(
        inseason_features
    ).to_numpy()

    players = {player.player_id: player for player in snapshot.players}
    fixtures = {fixture.fixture_id: fixture for fixture in snapshot.fixtures}
    teams = {team.team_season_id: team.name for team in snapshot.teams}
    rows = []
    for feature_row in inseason_features.itertuples(index=False):
        player = players[feature_row.element]
        fixture = fixtures[feature_row.fixture]
        was_home = player.team_season_id == fixture.home_team_season_id
        opponent_team_id = (
            fixture.away_team_season_id
            if was_home
            else fixture.home_team_season_id
        )
        team_name = teams[player.team_season_id]
        opponent_name = teams[opponent_team_id]
        player_preseason = preseason_scores.loc[player.player_id]
        rows.append(
            {
                "player_id": player.player_id,
                "player_fixed_id": player.player_fixed_id,
                "fixture_id": fixture.fixture_id,
                "GW": gameweek_number,
                "kickoff_time": fixture.kickoff_time,
                "name": player_preseason["name"],
                "web_name": player.web_name,
                "position": player.position,
                "team": team_name,
                "opponent": opponent_name,
                "was_home": int(was_home),
                "preseason_model_score": player_preseason[
                    "preseason_model_score"
                ],
                "inseason_model_score": feature_row.inseason_model_score,
            }
        )

    ensemble_features = pd.DataFrame(rows)
    ensemble_features["is_double_gameweek"] = (
        ensemble_features.groupby("player_id")["fixture_id"]
        .transform("nunique")
        .gt(1)
        .astype(int)
    )
    ensemble_features["team_promoted"] = (
        ensemble_features["team"].isin(promoted_teams).astype(int)
    )
    ensemble_features["opponent_promoted"] = (
        ensemble_features["opponent"].isin(promoted_teams).astype(int)
    )
    ensemble_features["predicted_points"] = ensemble_predictor.predict(
        ensemble_features
    ).to_numpy()
    ensemble_features["snapshot_retrieved_at"] = snapshot.retrieved_at

    return ensemble_features.sort_values(
        "predicted_points", ascending=False
    ).reset_index(drop=True)


if __name__ == "__main__":
    predictions = predict_upcoming_fixtures_from_fpl()
    print(predictions.head(20).to_string(index=False))
