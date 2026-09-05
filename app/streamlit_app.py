from pathlib import Path
import sys

# Prefer deployed source over any older copy installed in site-packages.
project_dir = Path(__file__).resolve().parents[1]
for import_dir in (project_dir, project_dir / "src"):
    import_path = str(import_dir)
    if import_path not in sys.path:
        sys.path.insert(0, import_path)

import streamlit as st
from app.components.technical.log_viewer import clear_logs, render_log_viewer
from logging_config import configure_logging

from app.components.technical.app_data_inspector import render_app_data_inspector
from app.components.my_team.current_team import render_all_players, render_current_team
from app.components.fixtures.fixtures import render_fixtures
from app.components.gameweek_header import render_gameweek_header
from app.components.technical.model_features import render_model_features
from app.components.player_lookup.player_lookup import render_player_lookup
from app.components.my_team.transfer_recommendation import render_transfer_recommendation
from app.services.app_data import get_deployed_revision, load_app_data
from settings import DEFAULT_MANAGER_ID

st.set_page_config(layout="wide")

configure_logging()

# Initialise selected manager
if "manager_id" not in st.session_state:
    st.session_state.manager_id = DEFAULT_MANAGER_ID


with st.sidebar:
    manager_selector = st.container()
    force_refresh = st.button(
        "Refresh FPL data",
        type="primary",
        use_container_width=True,
    )

try:
    revision = get_deployed_revision()
    if force_refresh:
        clear_logs()
        load_app_data.clear(st.session_state.manager_id, revision)

    with st.spinner("Loading FPL data..."):
        app_data = load_app_data(st.session_state.manager_id, revision)
except Exception as error:  # noqa: BLE001
    st.error(f"Unable to load FPL data: {error}")
    st.stop()

# Manager selector
manager_names = {
    team.manager_id: team.team_name for team in app_data.snapshot.rival_teams
}
manager_names[app_data.snapshot.manager.manager_id] = app_data.snapshot.manager.team_name
manager_ids = list(manager_names)

with manager_selector:
    selected_manager_id = st.selectbox(
        "Manager",
        options=manager_ids,
        index=manager_ids.index(st.session_state.manager_id),
        format_func=lambda manager_id: f"{manager_names[manager_id]} ({manager_id})",
    )

if selected_manager_id != st.session_state.manager_id:
    st.session_state.manager_id = selected_manager_id
    st.rerun()

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
    render_app_data_inspector(app_data)
    render_log_viewer(force_refresh)
