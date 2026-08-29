"""Loading and inference utilities for the fixture-level ensemble model."""

from pathlib import Path

import joblib
import pandas as pd


DEFAULT_ENSEMBLE_ARTIFACT_PATH = (
    Path(__file__).resolve().parent / "artifacts" / "ensemble_model.joblib"
)
ENSEMBLE_FEATURES = (
    "GW",
    "preseason_model_score",
    "inseason_model_score",
    "position",
    "team",
    "opponent",
    "was_home",
    "is_double_gameweek",
    "team_promoted",
    "opponent_promoted",
)
ENSEMBLE_CATEGORICAL_FEATURES = ("position", "team", "opponent")


class EnsemblePredictor:
    """Load the production ensemble artifact and predict fixture points."""

    def __init__(self, artifact_path: str | Path = DEFAULT_ENSEMBLE_ARTIFACT_PATH):
        artifact = joblib.load(Path(artifact_path))
        self.model = artifact["model"]
        self.feature_columns = tuple(artifact["feature_columns"])
        self.categorical_columns = tuple(artifact["categorical_columns"])

    def predict(self, features: pd.DataFrame) -> pd.Series:
        missing_columns = set(self.feature_columns) - set(features.columns)
        if missing_columns:
            raise ValueError(f"Missing ensemble features: {sorted(missing_columns)}")

        model_input = features.loc[:, self.feature_columns].copy()
        model_input.loc[:, self.categorical_columns] = (
            model_input.loc[:, self.categorical_columns]
            .fillna("__MISSING__")
            .astype(str)
        )
        return pd.Series(
            self.model.predict(model_input),
            index=features.index,
            name="predicted_points",
        )
