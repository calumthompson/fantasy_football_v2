from collections import Counter

import pandas as pd
import streamlit as st

from app.services.app_data import AppData


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


def render_double_gameweeks(app_data: AppData) -> None:
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
