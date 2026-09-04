import streamlit as st
from app.tabs.my_team import render_my_team
from components.log_viewer import clear_logs
from app.services.app_data import load_app_data
from logging_config import configure_logging
from tabs.technical import render_technical

from settings import DEFAULT_MANAGER_ID

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
    load_app_data.clear(manager_id)

try:
    with st.spinner("Loading FPL data..."):
        app_data = load_app_data(manager_id)
except Exception as error:  # noqa: BLE001
    st.error(f"Unable to load FPL data: {error}")
    st.stop()

if force_refresh:
    st.success("FPL data refreshed")

with my_team:
    render_my_team(app_data)

with technical:
    render_technical(app_data, force_refresh)
