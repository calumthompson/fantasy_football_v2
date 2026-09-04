from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import streamlit as st

from domain.snapshot import FPLSnapshot


def _format_time(value: datetime) -> str:
    return value.astimezone(ZoneInfo("Europe/London")).strftime("%a %d %b %Y, %H:%M %Z")


def render_gameweek_header(snapshot: FPLSnapshot) -> None:
    """Show gameweek timing using the fixtures in the loaded FPL snapshot."""
    current = next((week for week in snapshot.gameweeks if week.is_current), None)
    upcoming = next((week for week in snapshot.gameweeks if week.is_next), None)

    st.header(f"Gameweek {current.number}" if current else "No current gameweek")
    end_column, start_column = st.columns(2)

    with end_column:
        st.markdown("**Current gameweek ends (estimated)**")
        fixtures = [
            fixture
            for fixture in snapshot.fixtures
            if current and fixture.gameweek_number == current.number
        ]
        if fixtures and all(fixture.kickoff_time is not None for fixture in fixtures):
            last_kickoff = max(
                fixture.kickoff_time
                for fixture in fixtures
                if fixture.kickoff_time is not None
            )
            st.write(_format_time(last_kickoff + timedelta(hours=2)))
            st.caption("Estimated final whistle: two hours after the last kickoff.")
        else:
            st.write("To be confirmed" if current else "Not applicable")

    with start_column:
        st.markdown(
            f"**Gameweek {upcoming.number} starts**"
            if upcoming
            else "**Next gameweek starts**"
        )
        fixtures = [
            fixture
            for fixture in snapshot.fixtures
            if upcoming and fixture.gameweek_number == upcoming.number
        ]
        if fixtures and all(fixture.kickoff_time is not None for fixture in fixtures):
            first_kickoff = min(
                fixture.kickoff_time
                for fixture in fixtures
                if fixture.kickoff_time is not None
            )
            st.write(_format_time(first_kickoff))
        else:
            st.write("To be confirmed" if upcoming else "No upcoming gameweek")
        if upcoming:
            st.caption(f"FPL deadline: {_format_time(upcoming.deadline)}")

    st.divider()
