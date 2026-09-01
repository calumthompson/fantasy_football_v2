import streamlit as st
from components.log_viewer import clear_logs
from data import refresh_fpl_data
from logging_config import configure_logging
from views.technical import render_technical

from fantasy_football.settings import DEFAULT_MANAGER_ID

configure_logging()

my_team, player_lookup, technical = st.tabs(["My team", "Player lookup", "Technical"])

with st.sidebar:
    manager_id = st.number_input("Manager ID", value=DEFAULT_MANAGER_ID)

    force_refresh = st.button(
        "Refresh FPL data",
        type="primary",
        use_container_width=True,
    )

if force_refresh:
    clear_logs()
    refresh_fpl_data.clear(manager_id)

try:
    with st.spinner("Loading FPL data..."):
        fpl_data = refresh_fpl_data(manager_id)
except Exception as error:  # noqa: BLE001
    st.error(f"Unable to load FPL data: {error}")
    st.stop()

if force_refresh:
    st.success("FPL data refreshed")


with technical:
    render_technical(fpl_data, force_refresh)
