import pandas as pd
import streamlit as st

from app.services.app_data import AppData
from prediction.availability import adjust_for_availability


def _get_next_gameweek(snapshot) -> int | None:
    next_gameweek = next(
        (gameweek.number for gameweek in snapshot.gameweeks if gameweek.is_next),
        None,
    )
    if next_gameweek is not None:
        return next_gameweek

    upcoming_gameweeks = sorted(
        {
            fixture.gameweek_number
            for player in snapshot.players
            for fixture in player.upcoming_fixtures
            if fixture.gameweek_number is not None
        }
    )
    return upcoming_gameweeks[0] if upcoming_gameweeks else None


def _get_forecast_gameweeks(snapshot, next_gameweek: int | None) -> list[int]:
    return [
        gameweek.number
        for gameweek in sorted(snapshot.gameweeks, key=lambda gameweek: gameweek.number)
        if next_gameweek is not None and gameweek.number >= next_gameweek
    ][:5]


def _forecast_points_by_gameweek(
    player,
    forecast_gameweeks: list[int],
    predictions: dict[tuple[int, int], float],
) -> dict[int, float]:
    points = {gameweek: 0.0 for gameweek in forecast_gameweeks}
    for fixture in player.upcoming_fixtures:
        if fixture.gameweek_number in points:
            points[fixture.gameweek_number] += predictions.get(
                (player.player_id, fixture.fixture_id),
                0.0,
            )
    return {
        gameweek: adjust_for_availability(score, player.status)
        for gameweek, score in points.items()
    }


def render_current_team(app_data: AppData) -> None:
    snapshot = app_data.snapshot
    team_picks = snapshot.current_manager_team_picks

    last_gameweek = snapshot.manager.most_recent_gameweek
    next_gameweek = _get_next_gameweek(snapshot)
    forecast_gameweeks = _get_forecast_gameweeks(snapshot, next_gameweek)

    predictions = {
        (prediction.player_id, prediction.fixture_id): prediction.predicted_points
        for prediction in app_data.predictions.results
    }

    data_to_show = []

    picked_player_ids = (
        team_picks.selected_player_ids + team_picks.substitute_player_ids
    )
    selected_player_ids = set(team_picks.selected_player_ids)

    for player_id in picked_player_ids:
        player = snapshot.get_player_by_id(player_id)
        points_by_gameweek = _forecast_points_by_gameweek(
            player, forecast_gameweeks, predictions
        )
        opponents_by_gameweek: dict[int, list[str]] = {}

        for fixture in player.upcoming_fixtures:
            gameweek = fixture.gameweek_number
            if gameweek in forecast_gameweeks:
                opponents_by_gameweek.setdefault(gameweek, []).append(
                    fixture.opponent_team_name
                )

        last_week_points = sum(
            performance.total_points
            for performance in player.this_season_performance
            if performance.gameweek_number == last_gameweek
        )

        next_three_gameweeks = forecast_gameweeks[:3]
        next_five_gameweeks = forecast_gameweeks[:5]
        data_to_show.append(
            {
                "Player": player.web_name,
                "Status": player.status,
                "Next round playing chance": player.chance_of_playing_next_round,
                "Team": player.team_name,
                "Position": player.position,
                "Selected": player_id in selected_player_ids,
                "Captaincy": (
                    "C"
                    if player_id == team_picks.captain_player_id
                    else "VC" if player_id == team_picks.vice_captain_player_id else ""
                ),
                "Last week points": last_week_points,
                "Next opponent": ", ".join(opponents_by_gameweek.get(next_gameweek, []))
                or "Blank",
                "Next week forecast": points_by_gameweek.get(next_gameweek, 0.0),
                "Next 3 mean": (
                    sum(
                        points_by_gameweek[gameweek]
                        for gameweek in next_three_gameweeks
                    )
                    / len(next_three_gameweeks)
                    if next_three_gameweeks
                    else 0.0
                ),
                "Next 5 mean": (
                    sum(
                        points_by_gameweek[gameweek] for gameweek in next_five_gameweeks
                    )
                    / len(next_five_gameweeks)
                    if next_five_gameweeks
                    else 0.0
                ),
            }
        )

    current_team = pd.DataFrame(data_to_show)
    st.subheader("Current squad")
    st.dataframe(
        current_team,
        hide_index=True,
        use_container_width=True,
        height=(len(current_team) + 1) * 35 + 3,
        column_config={
            "Next round playing chance": st.column_config.NumberColumn(format="%d%%"),
            "Next week forecast": st.column_config.NumberColumn(format="%.2f"),
            "Next 3 mean": st.column_config.NumberColumn(format="%.2f"),
            "Next 5 mean": st.column_config.NumberColumn(format="%.2f"),
        },
    )


def render_all_players(app_data: AppData) -> None:
    snapshot = app_data.snapshot
    next_gameweek = _get_next_gameweek(snapshot)
    forecast_gameweeks = _get_forecast_gameweeks(snapshot, next_gameweek)
    predictions = {
        (prediction.player_id, prediction.fixture_id): prediction.predicted_points
        for prediction in app_data.predictions.results
    }

    all_players = []
    for player in snapshot.players:
        points_by_gameweek = _forecast_points_by_gameweek(
            player, forecast_gameweeks, predictions
        )
        next_fixtures = [
            fixture
            for fixture in player.upcoming_fixtures
            if fixture.gameweek_number == next_gameweek
        ]
        row = {
            "Player": player.web_name,
            "Status": player.status,
            "Next round playing chance": player.chance_of_playing_next_round,
            "Position": player.position,
            "Next opponent": ", ".join(
                fixture.opponent_team_name for fixture in next_fixtures
            )
            or "Blank",
            "Next game difficulty": ", ".join(
                str(fixture.player_game_difficulty) for fixture in next_fixtures
            )
            or "Blank",
        }
        for number_of_gameweeks in range(1, 6):
            gameweeks = forecast_gameweeks[:number_of_gameweeks]
            row[f"Next {number_of_gameweeks} GW mean"] = (
                sum(points_by_gameweek[gameweek] for gameweek in gameweeks)
                / len(gameweeks)
                if gameweeks
                else 0.0
            )
        all_players.append(row)

    all_players_forecast = pd.DataFrame(all_players).sort_values(
        by="Next 5 GW mean",
        ascending=False,
    )
    mean_columns = {
        f"Next {number_of_gameweeks} GW mean": st.column_config.NumberColumn(
            format="%.2f"
        )
        for number_of_gameweeks in range(1, 6)
    }

    st.subheader("All-player forecast")
    st.dataframe(
        all_players_forecast,
        hide_index=True,
        use_container_width=True,
        column_config={
            **mean_columns,
            "Next round playing chance": st.column_config.NumberColumn(format="%d%%"),
        },
    )
