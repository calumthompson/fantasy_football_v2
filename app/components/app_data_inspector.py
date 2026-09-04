import streamlit as st


def render_app_data_inspector(app_data):
    with st.expander("Inspect FPL snapshot"):
        st.json(
            app_data.snapshot.model_dump(mode="json"),
            expanded=1,
        )