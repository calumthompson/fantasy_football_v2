import streamlit as st
from components.log_viewer import render_log_viewer

from domain.models import FPLSnapshot


def render_technical(fpl_data: FPLSnapshot, force_refresh: bool) -> None:
    render_log_viewer(force_refresh)

    with st.expander("Inspect FPL snapshot"):
        st.json(
            fpl_data.model_dump(mode="json"),
            expanded=1,
        )
