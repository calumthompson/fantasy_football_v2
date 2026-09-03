#%%
import pandas as pd

from domain.snapshot import FPLSnapshot
from prediction.artifacts.io import load_trained_catboost_model
from prediction.artifacts.io import ENSEMBLE_ARTIFACT_PATH
from prediction.models.base_model import BaseCatBoostModel, PlayerFixturePrediction


"""
required columns = ['team',
 'position',
 'current_gw',
 'target_gw',
 'horizon',
 'was_home',
 'player_game_difficulty',
 'opponent_game_difficulty',
 'pre_season_model_score',
 'in_season_model_score']
"""


class EnsembleModelRunner(BaseCatBoostModel):

    def predict_for_snapshot(self, snapshot: FPLSnapshot) -> list[PlayerFixturePrediction]:

        in_season_model_scores

        dataframe_to_score = ...

        return self.predict_for_dataframe(dataframe_to_score)


ensemble_model = EnsembleModelRunner(artifact_path=ENSEMBLE_ARTIFACT_PATH)

ensemble_model.feature_columns
# %%
