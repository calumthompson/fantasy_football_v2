import streamlit as st

from fantasy_football.domain.models import FPLSnapshot
from fantasy_football.integrations.fpl_api import FPLAPIClient


@st.cache_data
def refresh_fpl_data(manager_id: int) -> FPLSnapshot:
    return FPLAPIClient(manager_id).load_snapshot()
