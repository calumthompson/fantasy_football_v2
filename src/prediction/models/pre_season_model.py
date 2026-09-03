#%%
import pandas as pd

from domain.snapshot import FPLSnapshot
from prediction.artifacts.io import load_trained_catboost_model
from prediction.artifacts.io import PRE_SEASON_ARTIFACT_PATH
from prediction.models.base_model import BaseCatBoostModel, PlayerFixturePrediction


class PreSeasonModelRunner(BaseCatBoostModel):

    """
    Required columns:

    'position',
    'season_sum_total_points',
    'season_sum_minutes',
    'season_sum_goals_scored',
    'season_sum_assists',
    'season_sum_clean_sheets',
    'season_sum_goals_conceded',
    'season_sum_own_goals',
    'season_sum_penalties_saved',
    'season_sum_penalties_missed',
    'season_sum_yellow_cards',
    'season_sum_red_cards',
    'season_sum_saves',
    'season_sum_bonus',
    'season_sum_bps',
    'season_sum_influence',
    'season_sum_creativity',
    'season_sum_threat',
    'season_sum_ict_index',
    'season_sum_starts',
    'season_sum_expected_goals',
    'season_sum_expected_assists',
    'season_sum_expected_goal_involvements',
    'season_sum_expected_goals_conceded'

    """

    def _generate_dataframe_from_snapshot(self, snapshot: FPLSnapshot) -> pd.DataFrame:

        for player in snapshot.players:
            


pre_season_model = PreSeasonModelRunner(artifact_path=PRE_SEASON_ARTIFACT_PATH)
