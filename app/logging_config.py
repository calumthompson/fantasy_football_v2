import sys
from collections import deque

import streamlit as st
from loguru import logger


def configure_logging() -> None:
    if "logs" not in st.session_state:
        st.session_state.logs = deque(maxlen=200)

    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add(
        lambda message: st.session_state.logs.append(str(message).rstrip()),
        level="INFO",
        format="{time:HH:mm:ss} | {level:<8} | {message}",
    )
