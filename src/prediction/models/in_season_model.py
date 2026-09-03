import pandas as pd

from domain.snapshot import FPLSnapshot
from prediction.artifacts.io import load_trained_catboost_model
from prediction.artifacts.io import IN_SEASON_ARTIFACT_PATH
from prediction.models.base_model import BaseCatBoostModel, PlayerFixturePrediction


class InSeasonModelRunner(BaseCatBoostModel):

    def predict_for_snapshot(self, snapshot: FPLSnapshot) -> list[PlayerFixturePrediction]:
        return super().predict_for_snapshot(snapshot)


in_season_model = InSeasonModelRunner(artifact_path=IN_SEASON_ARTIFACT_PATH)
