#%%
import pandas as pd

from domain.snapshot import FPLSnapshot
from prediction.artifacts.io import load_trained_catboost_model
from prediction.artifacts.io import ENSEMBLE_ARTIFACT_PATH
from prediction.models.base_model import BaseCatBoostModel, PlayerFixturePrediction
from prediction.models.in_season_model import in_season_model
from prediction.models.pre_season_model import pre_season_model


"""
required columns = ['team',
 'position',
 'target_gw',
 'was_home',
 'player_game_difficulty',
 'opponent_game_difficulty',
 'pre_season_model_score',
 'in_season_model_score']
"""


class EnsembleModelRunner(BaseCatBoostModel):

    def _generate_dataframe_from_snapshot(self, snapshot: FPLSnapshot) -> pd.DataFrame:

        rows = []

        pre_season_model_results = pre_season_model.predict_for_snapshot(snapshot)
        in_season_model_results = in_season_model.predict_for_snapshot(snapshot)
        
        for player in snapshot.players:
            for fixture in player.upcoming_fixtures:

                rows.append(
                    {
                        "player_id": player.player_id,
                        "fixture_id": fixture.fixture_id,
                        "kickoff_time": fixture.kickoff_time,
                        "target_gw": fixture.gameweek_number,
                        "team": player.team_name,
                        "position": player.position,
                        "was_home": fixture.is_home,
                        'player_game_difficulty': fixture.player_game_difficulty,
                        'opponent_game_difficulty': fixture.opponent_game_difficulty,
                        'pre_season_model_score': pre_season_model_results.get_score_for_player_id(player.player_id, error_on_missing=False),
                        'in_season_model_score': in_season_model_results.get_score_for_player_id(player.player_id, error_on_missing=False)
                    }
                )
    
        df = pd.DataFrame(rows).sort_values(["player_id", "kickoff_time"])

        return df

ensemble_model = EnsembleModelRunner(artifact_path=ENSEMBLE_ARTIFACT_PATH)
# %%
