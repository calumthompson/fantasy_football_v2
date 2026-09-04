from collections import Counter
from math import isfinite
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

if TYPE_CHECKING:
    from app.services.app_data import AppData


def _upcoming_gameweek_numbers(snapshot) -> list[int]:
    next_gameweek = next(
        (week.number for week in snapshot.gameweeks if week.is_next),
        snapshot.manager.most_recent_gameweek + 1,
    )
    return sorted(
        {week.number for week in snapshot.gameweeks if week.number >= next_gameweek}
    )


def _top_player_rows(snapshot, predictions, gameweek: int) -> list[dict]:
    """Rank complete gameweek forecasts, summing every assigned fixture."""
    scores = {
        (prediction.player_id, prediction.fixture_id): prediction.predicted_points
        for prediction in predictions.results
    }
    rows = []
    for player in snapshot.players:
        fixtures = {
            fixture.fixture_id: fixture
            for fixture in player.upcoming_fixtures
            if fixture.gameweek_number == gameweek
        }
        if not fixtures:
            continue
        points = [scores.get((player.player_id, fixture_id)) for fixture_id in fixtures]
        if any(point is None or not isfinite(point) for point in points):
            continue
        rows.append(
            {
                "Player": player.web_name,
                "Team": player.team_name,
                "Position": player.position,
                "Fixtures": len(fixtures),
                "Opponents": ", ".join(
                    f"{fixture.opponent_team_name} ({'H' if fixture.is_home else 'A'})"
                    for fixture in fixtures.values()
                ),
                "Predicted points": sum(points),
            }
        )
    return sorted(rows, key=lambda row: (-row["Predicted points"], row["Player"]))[:10]


def render_fixtures(app_data: "AppData") -> None:
    snapshot = app_data.snapshot
    st.subheader("Upcoming fixtures and predicted scorers")
    available = _upcoming_gameweek_numbers(snapshot)
    if not available:
        st.info("No upcoming gameweeks are available.")
        render_double_gameweeks(app_data)
        return

    selected = st.multiselect(
        "Gameweeks",
        options=available,
        default=available[:5],
        format_func=lambda number: f"GW{number}",
        key="fixtures_gameweeks",
    )
    st.caption(
        "Kickoff times use UK time (GMT/BST). Predictions are total points across "
        "all of a player's fixtures that week, including doubles. "
        "Players with missing predictions are excluded from the ranking."
    )
    team_names = {team.team_season_id: team.name for team in snapshot.teams}
    for gameweek in sorted(selected):
        with st.expander(f"Gameweek {gameweek}", expanded=True):
            fixtures = sorted(
                (f for f in snapshot.fixtures if f.gameweek_number == gameweek),
                key=lambda f: (f.kickoff_time is None, f.kickoff_time, f.fixture_id),
            )
            if fixtures:
                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "Kickoff": (
                                    fixture.kickoff_time.astimezone(
                                        ZoneInfo("Europe/London")
                                    ).strftime("%a %d %b %Y, %H:%M %Z")
                                    if fixture.kickoff_time
                                    else "To be confirmed"
                                ),
                                "Home": team_names.get(
                                    fixture.home_team_season_id,
                                    f"Team {fixture.home_team_season_id}",
                                ),
                                "Away": team_names.get(
                                    fixture.away_team_season_id,
                                    f"Team {fixture.away_team_season_id}",
                                ),
                                "Home difficulty": fixture.home_team_difficulty,
                                "Away difficulty": fixture.away_team_difficulty,
                            }
                            for fixture in fixtures
                        ]
                    ),
                    hide_index=True,
                    use_container_width=True,
                )
            else:
                st.info("No fixtures are currently scheduled for this gameweek.")

            st.markdown("#### Top 10 predicted scorers")
            rows = _top_player_rows(snapshot, app_data.predictions, gameweek)
            if rows:
                st.dataframe(
                    pd.DataFrame(rows),
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "Predicted points": st.column_config.NumberColumn(format="%.2f")
                    },
                )
            else:
                st.info(
                    "No complete player predictions are available for this gameweek."
                )

    if any(f.gameweek_number is None and not f.finished for f in snapshot.fixtures):
        st.caption(
            "Fixtures awaiting a gameweek assignment are excluded from weekly totals."
        )
    render_double_gameweeks(app_data)


def _upcoming_double_gameweeks(snapshot) -> list[dict[str, object]]:
    """Summarise future gameweeks in which at least one team plays twice."""
    next_gameweek = next(
        (gameweek.number for gameweek in snapshot.gameweeks if gameweek.is_next),
        snapshot.manager.most_recent_gameweek + 1,
    )
    team_names = {team.team_season_id: team.name for team in snapshot.teams}

    fixtures_by_gameweek: dict[int, list] = {}
    for fixture in snapshot.fixtures:
        if (
            fixture.gameweek_number is not None
            and fixture.gameweek_number >= next_gameweek
            and not fixture.finished
        ):
            fixtures_by_gameweek.setdefault(fixture.gameweek_number, []).append(fixture)

    squad = snapshot.get_current_team_picks() + snapshot.get_current_team_subs()
    rows = []
    for gameweek, fixtures in sorted(fixtures_by_gameweek.items()):
        fixture_counts = Counter(
            team_id
            for fixture in fixtures
            for team_id in (
                fixture.home_team_season_id,
                fixture.away_team_season_id,
            )
        )
        double_team_ids = {
            team_id for team_id, count in fixture_counts.items() if count > 1
        }
        if not double_team_ids:
            continue

        double_players = [
            player for player in squad if player.team_season_id in double_team_ids
        ]
        rows.append(
            {
                "Gameweek": gameweek,
                "Teams with doubles": len(double_team_ids),
                "My players with doubles": len(double_players),
                "Double teams": ", ".join(
                    sorted(
                        team_names.get(team_id, f"Team {team_id}")
                        for team_id in double_team_ids
                    )
                ),
                "My double players": ", ".join(
                    sorted(player.web_name for player in double_players)
                )
                or "None",
            }
        )

    return rows


def render_double_gameweeks(app_data: "AppData") -> None:
    st.subheader("Upcoming double gameweeks")
    st.caption(
        "Counts include your starting XI and substitutes. "
        "A team is counted when it has more than one scheduled fixture in a gameweek."
    )

    rows = _upcoming_double_gameweeks(app_data.snapshot)
    if not rows:
        st.info("There are no double gameweeks in the currently scheduled fixtures.")
        return

    st.dataframe(
        pd.DataFrame(rows),
        hide_index=True,
        use_container_width=True,
        column_config={
            "Gameweek": st.column_config.NumberColumn(format="GW%d"),
            "Teams with doubles": st.column_config.NumberColumn(format="%d"),
            "My players with doubles": st.column_config.NumberColumn(format="%d"),
        },
    )
