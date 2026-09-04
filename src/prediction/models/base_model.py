from abc import ABC, abstractmethod
from loguru import logger
from pathlib import Path
from typing import ClassVar
import joblib
from catboost import CatBoost
import numpy as np
from pydantic import BaseModel
import pandas as pd
from datetime import datetime, UTC
from dataclasses import dataclass

from domain.snapshot import FPLSnapshot
from prediction.artifacts.schema import CatBoostArtifactSchema


def check_for_missing_columns_in_df(df: pd.DataFrame, required_columns: list[str]):
        missing_columns = [
            column
            for column in required_columns
            if column not in df.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Provided DataFrame is missing required columns: {missing_columns}"
            )


class PlayerFixturePrediction(BaseModel):
    player_id: int
    fixture_id: int | None = None
    predicted_points: float


@dataclass
class ModelResult:
    model_name: str | None
    scored_at: datetime
    results: list[PlayerFixturePrediction]

    def get_score_for_player_id(self, player_id: int, error_on_missing = True) -> float:

        scores = [result for result in self.results if result.player_id == player_id]

        if len(scores) == 0:
            if error_on_missing:
                raise ValueError(f"No {self.model_name} score found for player_id {player_id}")
            return np.nan

        if len(scores) > 1:
            raise ValueError({f"Duplicate scores found for player_id {player_id} for {self.model_name}"})

        return scores[0].predicted_points

    def get_score_for_player_and_fixture_id(self, player_id: int, fixture_id: int, error_on_missing = True) -> float:

        scores = [result for result in self.results if (result.player_id == player_id) and (result.fixture_id == fixture_id)]

        if len(scores) == 0:
            raise ValueError(f"No {self.model_name} score found for player_id {player_id} in fixture {fixture_id}")

        if len(scores) > 1:
            raise ValueError({f"Duplicate scores found for player_id {player_id} at fixture {fixture_id} for {self.model_name}"})

        return scores[0].predicted_points


class BaseCatBoostModel(ABC):
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
    def feature_columns(self) -> list[str]:
        return self.artifact.feature_columns

    @property
    def categorical_columns(self) -> list[str]:
        return self.artifact.categorical_columns

    @abstractmethod
    def _generate_dataframe_from_snapshot(self, snapshot: FPLSnapshot) -> pd.DataFrame:
        ...        
    
    def predict_for_snapshot(
        self, snapshot: FPLSnapshot
    ) -> ModelResult:

        logger.info(f"Generating {self.model} scores")
        start_at = datetime.now(UTC)

        df = self._generate_dataframe_from_snapshot(snapshot)

        check_for_missing_columns_in_df(df, self.feature_columns)

        df['predicted_points'] = self.model.predict(df[self.feature_columns])

        if "fixture_id" in df.columns:
            columns_to_save = ["player_id", "fixture_id", "predicted_points"]
        else:
            columns_to_save = ["player_id", "predicted_points"]


        results = [
                PlayerFixturePrediction.model_validate(record)
                for record in df[
                    columns_to_save
                ].to_dict(orient="records")
            ]

        logger.info(f"{self.model} scores generated in {(datetime.now(UTC) - start_at).seconds}s")

        return ModelResult(
            model_name=self.artifact.model_name,
            scored_at=datetime.now(UTC),
            results=results
        )

    def predict_for_dataframe(self, df: pd.DataFrame) -> pd.Series:

        check_for_missing_columns_in_df(df, self.feature_columns)

        return self.model.predict(df[self.feature_columns])
