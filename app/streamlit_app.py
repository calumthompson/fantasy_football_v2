from collections import deque
import sys

import streamlit as st
from loguru import logger

from fpl_api import FPLAPIClient, FPLSnapshot


@st.cache_data
def refresh_fpl_data(manager_id: int) -> FPLSnapshot:
    return FPLAPIClient(manager_id).load_snapshot()


if "logs" not in st.session_state:
    st.session_state.logs = deque(maxlen=200)

# Replace Loguru's default DEBUG terminal sink on every Streamlit rerun.
logger.remove()
logger.add(sys.stderr, level="INFO")

logger.add(
    lambda message: st.session_state.logs.append(str(message).rstrip()),
    level="INFO",
    format="{time:HH:mm:ss} | {level:<8} | {message}",
)

with st.sidebar:
    manager_id = st.number_input("Manager ID", value=9836874)

    force_refresh = st.button(
        "Refresh FPL data",
        type="primary",
        use_container_width=True,
    )

if force_refresh:
    # Show only messages produced by this refresh.
    st.session_state.logs.clear()
    refresh_fpl_data.clear(manager_id)

try:
    with st.spinner("Loading FPL data..."):
        fpl_data = refresh_fpl_data(manager_id)
except Exception as error:
    st.error(f"Unable to load FPL data: {error}")
    st.stop()

if force_refresh:
    st.success("FPL data refreshed")

with st.expander("Application logs", expanded=force_refresh):
    if st.button("Clear logs"):
        st.session_state.logs.clear()

    st.code(
        "\n".join(st.session_state.logs) or "No logs captured yet",
        language="text",
    )
