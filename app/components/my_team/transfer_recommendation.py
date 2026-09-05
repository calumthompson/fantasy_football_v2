import pandas as pd
import streamlit as st

from app.services.app_data import AppData
from optimiser import recommend_lineup_after_transfer, recommend_transfer


def _format_price(value: int) -> str:
    return f"£{value / 10:.1f}m"


def _get_opponents(player, gameweek: int) -> str:
    opponents = [
        fixture.opponent_team_name
        for fixture in player.upcoming_fixtures
        if fixture.gameweek_number == gameweek
    ]
    return ", ".join(opponents) or "Blank"


def _get_fixture_difficulties(player, gameweek: int) -> str:
    difficulties = [
        str(fixture.player_game_difficulty)
        for fixture in player.upcoming_fixtures
        if fixture.gameweek_number == gameweek
    ]
    return ", ".join(difficulties) or "Blank"


def _get_gameweek_points(player, gameweek: int) -> int:
    return sum(
        performance.total_points
        for performance in player.this_season_performance
        if performance.gameweek_number == gameweek
    )


def render_transfer_recommendation(app_data: AppData) -> None:
    """Show the best forecast transfer over the next five gameweeks."""
    st.subheader("Recommended transfer")

    try:
        recommendation = recommend_transfer(
            app_data.snapshot,
            app_data.predictions,
            number_of_gameweeks=5,
        )
    except ValueError as error:
        st.info(f"No transfer recommendation available: {error}")
        return

    gameweek_label = f"GW{recommendation.gameweeks[0]}–GW{recommendation.gameweeks[-1]}"
    apply_transfer = recommendation.predicted_points_gain > 0
    if not apply_transfer:
        st.info(
            "Hold the transfer. No legal move improves the five-gameweek forecast. "
            f"The best available move is {recommendation.outgoing_player_name} → "
            f"{recommendation.incoming_player_name} "
            f"({recommendation.predicted_points_gain:+.2f} points)."
        )
    else:
        st.success(
            f"Transfer **{recommendation.outgoing_player_name}** out and "
            f"**{recommendation.incoming_player_name}** in."
        )
        columns = st.columns(4)
        columns[0].metric("Position", recommendation.position)
        columns[1].metric(
            f"Forecast gain ({gameweek_label})",
            f"{recommendation.predicted_points_gain:+.2f} pts",
        )
        columns[2].metric(
            "Five-GW forecast",
            f"{recommendation.incoming_predicted_points:.2f} pts",
            delta=f"{recommendation.predicted_points_gain:+.2f}",
        )
        columns[3].metric("Price", _format_price(recommendation.incoming_value))

        available_funds = recommendation.bank + recommendation.outgoing_value
        st.caption(
            f"Budget: {_format_price(recommendation.bank)} in the bank + "
            f"{_format_price(recommendation.outgoing_value)} estimated sale value = "
            f"{_format_price(available_funds)} available. Sale value uses current price "
            "because the public FPL endpoint does not provide the manager's exact "
            "selling price."
        )

    _render_recommended_lineup(
        app_data,
        recommendation if apply_transfer else None,
    )


def _render_recommended_lineup(app_data: AppData, transfer) -> None:
    try:
        lineup = recommend_lineup_after_transfer(
            app_data.snapshot,
            app_data.predictions,
            transfer,
        )
    except ValueError as error:
        st.info(f"No lineup recommendation available: {error}")
        return

    snapshot = app_data.snapshot
    current_starter_ids = set(
        snapshot.current_manager_team_picks.selected_player_ids
    )
    current_substitute_ids = set(
        snapshot.current_manager_team_picks.substitute_player_ids
    )
    last_gameweek = snapshot.manager.most_recent_gameweek
    position_order = {"GKP": 0, "DEF": 1, "MID": 2, "FWD": 3}
    starters = [
        snapshot.get_player_by_id(player_id)
        for player_id in lineup.starting_player_ids
    ]
    starters.sort(
        key=lambda player: (
            position_order[player.position],
            -lineup.predicted_points[player.player_id],
        )
    )

    rows = []
    for player in starters:
        rows.append(
            {
                "Role": "Starting XI",
                "Player": player.web_name,
                "Status": player.status,
                "Next round playing chance": player.chance_of_playing_next_round,
                "Team": player.team_name,
                "Position": player.position,
                "Current cost": player.value / 10,
                "Next opponent": _get_opponents(player, lineup.gameweek),
                "Difficulty": _get_fixture_difficulties(player, lineup.gameweek),
                "Last week points": _get_gameweek_points(player, last_gameweek),
                "Transfer": (
                    "In"
                    if transfer is not None
                    and player.player_id == transfer.incoming_player_id
                    else ""
                ),
                "Lineup change": (
                    "From bench"
                    if player.player_id in current_substitute_ids
                    else ""
                ),
                "Captaincy": (
                    "C"
                    if player.player_id == lineup.captain_player_id
                    else "VC"
                    if player.player_id == lineup.vice_captain_player_id
                    else ""
                ),
                "Forecast": lineup.predicted_points[player.player_id],
            }
        )

    for bench_index, player_id in enumerate(lineup.substitute_player_ids):
        player = snapshot.get_player_by_id(player_id)
        bench_role = "Bench GK" if player.position == "GKP" else f"Bench {bench_index}"
        rows.append(
            {
                "Role": bench_role,
                "Player": player.web_name,
                "Status": player.status,
                "Next round playing chance": player.chance_of_playing_next_round,
                "Team": player.team_name,
                "Position": player.position,
                "Current cost": player.value / 10,
                "Next opponent": _get_opponents(player, lineup.gameweek),
                "Difficulty": _get_fixture_difficulties(player, lineup.gameweek),
                "Last week points": _get_gameweek_points(player, last_gameweek),
                "Transfer": (
                    "In"
                    if transfer is not None
                    and player.player_id == transfer.incoming_player_id
                    else ""
                ),
                "Lineup change": (
                    "To bench" if player.player_id in current_starter_ids else ""
                ),
                "Captaincy": "",
                "Forecast": lineup.predicted_points[player.player_id],
            }
        )

    if transfer is not None:
        outgoing_player = snapshot.get_player_by_id(transfer.outgoing_player_id)
        rows.append(
            {
                "Role": "Transferred out",
                "Player": outgoing_player.web_name,
                "Status": outgoing_player.status,
                "Next round playing chance": outgoing_player.chance_of_playing_next_round,
                "Team": outgoing_player.team_name,
                "Position": outgoing_player.position,
                "Current cost": outgoing_player.value / 10,
                "Next opponent": _get_opponents(outgoing_player, lineup.gameweek),
                "Difficulty": _get_fixture_difficulties(
                    outgoing_player, lineup.gameweek
                ),
                "Last week points": _get_gameweek_points(
                    outgoing_player, last_gameweek
                ),
                "Transfer": "Out",
                "Lineup change": "",
                "Captaincy": "",
                "Forecast": lineup.predicted_points[outgoing_player.player_id],
            }
        )

    st.subheader(f"Recommended team — GW{lineup.gameweek}")
    st.dataframe(
        pd.DataFrame(rows),
        hide_index=True,
        use_container_width=True,
        height=(len(rows) + 1) * 35 + 3,
        column_config={
            "Next round playing chance": st.column_config.NumberColumn(format="%d%%"),
            "Current cost": st.column_config.NumberColumn(format="£%.1fm"),
            "Forecast": st.column_config.NumberColumn(format="%.2f pts"),
        },
    )
    captain = snapshot.get_player_by_id(lineup.captain_player_id)
    vice_captain = snapshot.get_player_by_id(lineup.vice_captain_player_id)
    st.caption(
        f"Captain: {captain.web_name} · Vice-captain: {vice_captain.web_name}. "
        "The starting XI and captaincy are optimised for the next gameweek; "
        "outfield substitutes are ordered by forecast."
    )
