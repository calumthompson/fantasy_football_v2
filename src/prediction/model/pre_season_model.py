import pandas as pd

from domain.snapshot import FPLSnapshot
from prediction.artifacts.io import load_trained_catboost_model
from prediction.artifacts.path_registry import PRE_SEASON_ARTIFACT_PATH
from prediction.model.base_model import BaseCatBoostModel, PlayerFixturePrediction


class PreSeasonModelRunner(BaseCatBoostModel):

    def predict_for_snapshot(self, snapshot: FPLSnapshot) -> list[PlayerFixturePrediction]:
        return super().predict_for_snapshot(snapshot)


pre_season_model = PreSeasonModelRunner(artifact_path=PRE_SEASON_ARTIFACT_PATH)
