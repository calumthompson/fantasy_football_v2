import pandas as pd
import streamlit as st

from app.services.app_data import AppData


def render_current_team(app_data: AppData) -> None:
    snapshot = app_data.snapshot
    team_picks = snapshot.current_manager_team_picks

    previous_gameweek = next(
        (gameweek.number for gameweek in snapshot.gameweeks if gameweek.is_previous),
        None,
    )
    next_gameweek = next(
        (gameweek.number for gameweek in snapshot.gameweeks if gameweek.is_next),
        None,
    )

    if next_gameweek is None:
        upcoming_gameweeks = sorted(
            {
                fixture.gameweek_number
                for player in snapshot.players
                for fixture in player.upcoming_fixtures
                if fixture.gameweek_number is not None
            }
        )
        next_gameweek = upcoming_gameweeks[0] if upcoming_gameweeks else None

    forecast_gameweeks = [
        gameweek.number
        for gameweek in sorted(snapshot.gameweeks, key=lambda gameweek: gameweek.number)
        if next_gameweek is not None and gameweek.number >= next_gameweek
    ][:5]

    predictions = {
        (prediction.player_id, prediction.fixture_id): prediction.predicted_points
        for prediction in app_data.predictions.results
    }
    data_to_show = []

    for player_id in team_picks.selected_player_ids:
        player = snapshot.get_player_by_id(player_id)
        points_by_gameweek = {gameweek: 0.0 for gameweek in forecast_gameweeks}
        opponents_by_gameweek: dict[int, list[str]] = {}

        for fixture in player.upcoming_fixtures:
            gameweek = fixture.gameweek_number
            if gameweek in points_by_gameweek:
                points_by_gameweek[gameweek] += predictions.get(
                    (player.player_id, fixture.fixture_id),
                    0.0,
                )
                opponents_by_gameweek.setdefault(gameweek, []).append(
                    fixture.opponent_team_name
                )

        last_week_points = None
        if previous_gameweek is not None:
            last_week_points = sum(
                performance.total_points
                for performance in player.this_season_performance
                if performance.gameweek_number == previous_gameweek
            )

        next_three_gameweeks = forecast_gameweeks[:3]
        next_five_gameweeks = forecast_gameweeks[:5]
        data_to_show.append(
            {
                "Player": player.web_name,
                "Position": player.position,
                "Last week points": last_week_points,
                "Next opponent": ", ".join(
                    opponents_by_gameweek.get(next_gameweek, [])
                )
                or "Blank",
                "Next week forecast": points_by_gameweek.get(next_gameweek, 0.0),
                "Next 3 mean": (
                    sum(points_by_gameweek[gameweek] for gameweek in next_three_gameweeks)
                    / len(next_three_gameweeks)
                    if next_three_gameweeks
                    else 0.0
                ),
                "Next 5 mean": (
                    sum(points_by_gameweek[gameweek] for gameweek in next_five_gameweeks)
                    / len(next_five_gameweeks)
                    if next_five_gameweeks
                    else 0.0
                ),
            }
        )

    current_team = pd.DataFrame(data_to_show)
    st.dataframe(
        current_team,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Next week forecast": st.column_config.NumberColumn(format="%.2f"),
            "Next 3 mean": st.column_config.NumberColumn(format="%.2f"),
            "Next 5 mean": st.column_config.NumberColumn(format="%.2f"),
        },
    )
