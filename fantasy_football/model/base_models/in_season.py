"""Loading utilities for the selected in-season points model."""

from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from fantasy_football.model.training.utils import (
    add_historic_fixture_rolling_features,
)


SELECTED_IN_SEASON_MODEL_NAME = "Unweighted"
DEFAULT_IN_SEASON_ARTIFACT_PATH = (
    Path(__file__).resolve().parents[1] / "artifacts" / "in_season_model.joblib"
)
DEFAULT_IN_SEASON_SCORES_PATH = (
    Path(__file__).resolve().parents[1]
    / "artifacts"
    / "in_season_scores_2025_26.joblib"
)
DEFAULT_IN_SEASON_HISTORIC_FEATURES = (
    "assists",
    "clean_sheets",
    "creativity",
    "goals_conceded",
    "goals_scored",
    "ict_index",
    "influence",
    "own_goals",
    "penalties_missed",
    "penalties_saved",
    "red_cards",
    "saves",
    "selected",
    "starts",
    "threat",
    "transfers_balance",
    "value",
    "yellow_cards",
    "minutes",
)
DEFAULT_IN_SEASON_WINDOWS = (1, 3, 6, 9, 12)


def build_inseason_fixture_features(
    fixtures: pd.DataFrame,
    feature_columns: tuple[str, ...] = DEFAULT_IN_SEASON_HISTORIC_FEATURES,
    windows: tuple[int, ...] = DEFAULT_IN_SEASON_WINDOWS,
) -> pd.DataFrame:
    """Build deadline-safe rolling features while retaining fixture-level rows."""
    result = (
        fixtures.drop_duplicates(["element", "fixture"], keep="last")
        .reset_index(drop=True)
        .copy()
    )
    for feature_column in feature_columns:
        result = add_historic_fixture_rolling_features(
            result,
            feature_column=feature_column,
            windows=windows,
        )
    return result


def load_in_season_model(
    artifact_path: str | Path = DEFAULT_IN_SEASON_ARTIFACT_PATH,
) -> Any:
    """Load the unweighted CatBoost model selected by offline evaluation."""
    artifact = joblib.load(Path(artifact_path))
    artifact_model_name = artifact.get("model_name")
    if artifact_model_name != SELECTED_IN_SEASON_MODEL_NAME:
        raise ValueError(
            "Expected the selected in-season model artifact to be "
            f"{SELECTED_IN_SEASON_MODEL_NAME!r}, got {artifact_model_name!r}."
        )
    return artifact["model"]


def load_inseason_scores(
    scores_path: str | Path = DEFAULT_IN_SEASON_SCORES_PATH,
) -> pd.DataFrame:
    """Load fixture-level in-season scores exported for the ensemble."""
    scores = joblib.load(Path(scores_path))
    required_columns = {"element", "fixture", "GW", "inseason_model_score"}
    missing_columns = required_columns - set(scores.columns)
    if missing_columns:
        raise ValueError(f"Missing in-season score columns: {sorted(missing_columns)}")
    return scores.copy()
