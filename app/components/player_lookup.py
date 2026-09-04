import pandas as pd
import streamlit as st

from app.services.app_data import AppData


def render_player_lookup(app_data: AppData) -> None:
    snapshot = app_data.snapshot
    players_by_label = {
        f"{player.web_name} — {player.team_name} ({player.position})": player
        for player in snapshot.players
    }

    selected_label = st.selectbox(
        "Player name",
        options=sorted(players_by_label),
        index=None,
        placeholder="Type a player's name…",
    )
    if selected_label is None:
        st.info("Search for and select a player to view their fixtures.")
        return

    player = players_by_label[selected_label]
    st.subheader(player.web_name)
    summary_columns = st.columns(3)
    summary_columns[0].metric("Team", player.team_name)
    summary_columns[1].metric("Position", player.position)
    summary_columns[2].metric("Player ID", player.player_id)
    if player.news:
        st.warning(player.news)

    team_names = {team.team_season_id: team.name for team in snapshot.teams}
    history_rows = []
    for performance in sorted(
        player.this_season_performance,
        key=lambda performance: performance.kickoff_time,
        reverse=True,
    ):
        row = performance.model_dump()
        row["opponent"] = team_names.get(
            performance.opponent_team_season_id,
            str(performance.opponent_team_season_id),
        )
        row["venue"] = "Home" if performance.was_home else "Away"
        history_rows.append(row)

    st.markdown("#### Past fixtures")
    if history_rows:
        history = pd.DataFrame(history_rows)
        leading_columns = [
            "gameweek_number",
            "kickoff_time",
            "opponent",
            "venue",
            "total_points",
        ]
        history = history[
            leading_columns
            + [column for column in history.columns if column not in leading_columns]
        ]
        st.dataframe(
            history,
            hide_index=True,
            use_container_width=True,
            column_config={
                "kickoff_time": st.column_config.DatetimeColumn(
                    format="DD MMM YYYY HH:mm"
                ),
            },
        )
    else:
        st.info("No past fixtures are available for this player.")

    predictions = {
        (prediction.player_id, prediction.fixture_id): prediction.predicted_points
        for prediction in app_data.predictions.results
    }
    upcoming_rows = [
        {
            "Gameweek": fixture.gameweek_number,
            "Kickoff": fixture.kickoff_time,
            "Opponent": fixture.opponent_team_name,
            "Venue": "Home" if fixture.is_home else "Away",
            "Fixture difficulty": fixture.player_game_difficulty,
            "Opponent difficulty": fixture.opponent_game_difficulty,
            "Predicted points": predictions.get(
                (player.player_id, fixture.fixture_id),
                0.0,
            ),
            "Fixture ID": fixture.fixture_id,
        }
        for fixture in sorted(
            player.upcoming_fixtures,
            key=lambda fixture: (
                fixture.gameweek_number is None,
                fixture.gameweek_number or 0,
                fixture.kickoff_time is None,
                fixture.kickoff_time,
            ),
        )
    ]

    st.markdown("#### Upcoming fixtures")
    if upcoming_rows:
        st.dataframe(
            pd.DataFrame(upcoming_rows),
            hide_index=True,
            use_container_width=True,
            column_config={
                "Kickoff": st.column_config.DatetimeColumn(format="DD MMM YYYY HH:mm"),
                "Predicted points": st.column_config.NumberColumn(format="%.2f"),
            },
        )
    else:
        st.info("No upcoming fixtures are available for this player.")
