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

        rows = []

        for player in snapshot.players:

            last_season_performance = player.last_season_performance

            if last_season_performance is None:
                continue

            rows.append(
                {
                    'player_id': player.player_id,
                    'position': player.position,
                    'sum_season_total_points': last_season_performance.total_points,
                    'sum_season_minutes': last_season_performance.minutes,
                    'sum_season_goals_scored': last_season_performance.goals_scored,
                    'sum_season_assists': last_season_performance.assists,
                    'sum_season_clean_sheets': last_season_performance.clean_sheets,
                    'sum_season_goals_conceded': last_season_performance.goals_conceded,
                    'sum_season_own_goals': last_season_performance.own_goals,
                    'sum_season_penalties_saved': last_season_performance.penalties_saved,
                    'sum_season_penalties_missed': last_season_performance.penalties_missed,
                    'sum_season_yellow_cards': last_season_performance.yellow_cards,
                    'sum_season_red_cards': last_season_performance.red_cards,
                    'sum_season_saves': last_season_performance.saves,
                    'sum_season_bonus': last_season_performance.bonus,
                    'sum_season_bps': last_season_performance.bps,
                    'sum_season_influence': last_season_performance.influence,
                    'sum_season_creativity': last_season_performance.creativity,
                    'sum_season_threat': last_season_performance.threat,
                    'sum_season_ict_index': last_season_performance.ict_index,
                    'sum_season_starts': last_season_performance.starts,
                    'sum_season_expected_goals': last_season_performance.expected_goals,
                    'sum_season_expected_assists': last_season_performance.expected_assists,
                    'sum_season_expected_goal_involvements': last_season_performance.expected_goal_involvements,
                    'sum_season_expected_goals_conceded': last_season_performance.expected_goals_conceded,
                }
            )

        return pd.DataFrame(rows)

pre_season_model = PreSeasonModelRunner(artifact_path=PRE_SEASON_ARTIFACT_PATH)
