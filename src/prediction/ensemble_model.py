#%% 
from domain.snapshot import FPLSnapshot
from prediction.base_model_runner import PlayerFixturePrediction
from prediction.base_model_runner import BaseCatBoostModelRunner


class PreSeasonModelRunner(BaseCatBoostModelRunner):

    def predict_for_snapshot(self, snapshot: FPLSnapshot) -> list[PlayerFixturePrediction]:
        return super().predict_for_snapshot(snapshot)


pre_season_model_runner = PreSeasonModelRunner(artifact_path="./artifacts/pre_season_model.joblib")

#%% 