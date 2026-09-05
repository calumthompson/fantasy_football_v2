import pandas as pd
import streamlit as st

from app.components.my_team.current_team import (
    _forecast_points_by_gameweek,
    _get_next_gameweek,
)
from app.services.app_data import AppData
from optimiser import create_optimal_team


def render_optimal_team(app_data: AppData) -> None:
    """Show the optimal £100m squad for a selected forecast gameweek."""
    st.subheader("Best predicted team")
    st.caption(
        "Each gameweek is optimised independently across all players: "
        "15 players within £100m, with 2 goalkeepers, 5 defenders, "
        "5 midfielders, 3 forwards and at most 3 players per club. "
        "Forecast totals include all 15 players, without captain multipliers."
    )
    snapshot = app_data.snapshot
    predictions = {
        (prediction.player_id, prediction.fixture_id): prediction.predicted_points
        for prediction in app_data.predictions.results
    }
    next_gameweek = _get_next_gameweek(snapshot)
    gameweeks = sorted(
        {
            fixture.gameweek_number
            for player in snapshot.players
            for fixture in player.upcoming_fixtures
            if fixture.gameweek_number is not None
            and (next_gameweek is None or fixture.gameweek_number >= next_gameweek)
            and (player.player_id, fixture.fixture_id) in predictions
        }
    )
    if not gameweeks:
        st.info("No upcoming gameweeks with predictions are available.")
        return

    gameweek = st.selectbox(
        "Gameweek",
        gameweeks,
        format_func=lambda number: f"GW{number}",
        key="optimal_team_gameweek",
    )
    candidates = pd.DataFrame(
        [
            {
                "name": player.web_name,
                "Status": player.status,
                "Next round playing chance": player.chance_of_playing_next_round,
                "position": player.position,
                "team": player.team_name,
                "value": player.value,
                "Opponents": ", ".join(
                    fixture.opponent_team_name
                    for fixture in player.upcoming_fixtures
                    if fixture.gameweek_number == gameweek
                )
                or "Blank",
                "Forecast": _forecast_points_by_gameweek(
                    player, [gameweek], predictions
                )[gameweek],
            }
            for player in snapshot.players
        ]
    )
    try:
        squad = create_optimal_team(candidates, target_column="Forecast")
    except ValueError as error:
        st.info(f"No optimal team available: {error}")
        return

    columns = st.columns(2)
    columns[0].metric(
        f"GW{gameweek} squad forecast", f"{squad['Forecast'].sum():.2f} pts"
    )
    columns[1].metric("Squad cost", f"£{squad['value'].sum() / 10:.1f}m")
    squad = squad.sort_values(
        ["position", "Forecast"],
        ascending=[True, False],
        key=lambda column: (
            column.map({"GKP": 0, "DEF": 1, "MID": 2, "FWD": 3})
            if column.name == "position"
            else column
        ),
    ).rename(
        columns={
            "name": "Player",
            "position": "Position",
            "team": "Team",
            "value": "Cost",
        }
    )
    squad["Cost"] = squad["Cost"] / 10
    st.dataframe(
        squad,
        hide_index=True,
        use_container_width=True,
        height=(len(squad) + 1) * 35 + 3,
        column_config={
            "Next round playing chance": st.column_config.NumberColumn(format="%d%%"),
            "Cost": st.column_config.NumberColumn(format="£%.1fm"),
            "Forecast": st.column_config.NumberColumn(format="%.2f pts"),
        },
    )
    st.caption(
        "Fixture forecasts are summed for double gameweeks; missing forecasts count as zero."
    )
