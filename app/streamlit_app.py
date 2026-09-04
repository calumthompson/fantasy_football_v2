import streamlit as st
from components.log_viewer import clear_logs, render_log_viewer
from logging_config import configure_logging

from app.components.app_data_inspector import render_app_data_inspector
from app.components.current_team import render_all_players, render_current_team
from app.components.fixtures import render_fixtures
from app.components.gameweek_header import render_gameweek_header
from app.components.model_features import render_model_features
from app.components.player_lookup import render_player_lookup
from app.components.transfer_recommendation import render_transfer_recommendation
from app.services.app_data import load_app_data
from settings import DEFAULT_MANAGER_ID

st.set_page_config(layout="wide")

configure_logging()

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

render_gameweek_header(app_data.snapshot)

my_team, fixtures, player_lookup, technical = st.tabs(
    ["My team", "Fixtures", "Player lookup", "Technical"]
)

with my_team:
    render_current_team(app_data)
    render_transfer_recommendation(app_data)

with player_lookup:
    render_player_lookup(app_data)
    render_all_players(app_data)

with fixtures:
    render_fixtures(app_data)

with technical:
    render_model_features()
    render_log_viewer(force_refresh)
    render_app_data_inspector(app_data)
