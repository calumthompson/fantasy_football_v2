from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

import joblib
from catboost import CatBoost
from pydantic import BaseModel

from domain.snapshot import FPLSnapshot
from prediction.artifacts.schema import CatBoostArtifactSchema


class PlayerFixturePrediction(BaseModel):
    player_id: int
    fixture_id: int
    predicted_points: float


class BaseModelRunner(ABC):
    @abstractmethod
    def predict_for_snapshot(
        self, snapshot: FPLSnapshot
    ) -> list[PlayerFixturePrediction]:
        """Generate fixture-level predictions for a snapshot."""


class BaseCatBoostModelRunner(BaseModelRunner):
    """Load and validate the artifact shared by CatBoost model runners."""

    artifact_type: ClassVar[type[CatBoostArtifactSchema]] = CatBoostArtifactSchema

    def __init__(self, artifact_path: str | Path) -> None:
        self.artifact_path = Path(artifact_path)
        raw_artifact = joblib.load(self.artifact_path)
        self.artifact = self.artifact_type.model_validate(raw_artifact)

        # Keep this alias for concise use in concrete prediction runners.
        self._model = self.artifact.model

    @property
    def model(self) -> CatBoost:
        return self.artifact.model

    @property
    def feature_columns(self) -> tuple[str, ...]:
        return self.artifact.feature_columns

    @property
    def categorical_columns(self) -> tuple[str, ...]:
        return self.artifact.categorical_columns
