import streamlit as st
from dataclasses import dataclass
from pathlib import Path
import subprocess

from domain.snapshot import FPLSnapshot
from integrations.fpl_api import FPLAPIClient
from prediction.models.base_model import ModelResult
from prediction.models.ensemble_model import ensemble_model



@dataclass
class AppData:
    snapshot: FPLSnapshot
    predictions: ModelResult


def get_deployed_revision() -> str:
    """Read the checked-out commit on every rerun to detect deployments."""
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        timeout=5,
    ).strip()


@st.cache_data
def load_app_data(manager_id: int, revision: str) -> AppData:
    """Cache each manager's data separately for each deployed Git revision."""

    snapshot = FPLAPIClient(manager_id).load_snapshot()
    model_results = ensemble_model.predict_for_snapshot(snapshot)

    return AppData(
        snapshot = snapshot,
        predictions=model_results
    )
