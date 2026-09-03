import streamlit as st
from dataclasses import dataclass

from domain.snapshot import FPLSnapshot
from integrations.fpl_api import FPLAPIClient
from prediction.models.base_model import PlayerFixturePrediction
from prediction.models.ensemble_model import ensemble_model



@dataclass
class AppData:
    snapshot: FPLSnapshot
    predictions: list[PlayerFixturePrediction]


@st.cache_data
def load_app_data(manager_id: int) -> AppData:

    snapshot = FPLAPIClient(manager_id).load_snapshot()

    return AppData(
        snapshot = snapshot,
        predictions=ensemble_model.predict_for_snapshot(snapshot)
    )


