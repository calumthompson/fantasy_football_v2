import streamlit as st


def clear_logs() -> None:
    st.session_state.logs.clear()


def render_log_viewer(force_refresh: bool) -> None:
    with st.expander("Application logs", expanded=force_refresh):
        if st.button("Clear logs"):
            clear_logs()

        st.code(
            "\n".join(st.session_state.logs) or "No logs captured yet",
            language="text",
        )
