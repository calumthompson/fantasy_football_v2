import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import numpy as np
import pandas as pd

from prediction.models.base_model import BaseCatBoostModel
from training.transformations import create_trended_calculations


class FrameRunner(BaseCatBoostModel):
    def _generate_dataframe_from_snapshot(self, snapshot):
        return snapshot.copy()


class PredictionRegressions(unittest.TestCase):
    def test_position_normalization_for_both_prediction_entrypoints(self):
        runner = object.__new__(FrameRunner)
        model = Mock()
        model.predict.side_effect = lambda frame: np.where(frame.position == "GK", 2.0, 3.0)
        runner.artifact = SimpleNamespace(
            model=model, feature_columns=["position"], model_name="test"
        )
        frame = pd.DataFrame({"player_id": [1, 2, 3], "position": ["GKP", "GK", "DEF"]})
        np.testing.assert_array_equal(runner.predict_for_dataframe(frame), [2, 2, 3])
        result = runner.predict_for_snapshot(frame)
        self.assertEqual([r.predicted_points for r in result.results], [2, 2, 3])
        self.assertEqual(frame.position.tolist(), ["GKP", "GK", "DEF"])

    def test_notebook_preserves_fixture_feature_alignment(self):
        # Interleaved players expose the original independent-index-reset bug.
        history = pd.DataFrame({
            "player_id": [2, 1, 2, 1], "GW": [2, 1, 1, 2],
            "fixture_id": [4, 1, 3, 2], "minutes": [40, 10, 30, 20],
        })
        notebook = json.loads((Path(__file__).resolve().parents[1] /
            "training/notebooks/in_season_model.ipynb").read_text())
        namespace = dict(
            pd=pd, TRAINING_SEASONS=["2023-24"], NUMERIC_FEATURES=["minutes"],
            EXTRA_NUMERIC_FEATURES=[], ROLLING_WINDOWS=[1, 3], CATEGORICAL_COLUMNS=[],
            load_historic_player_fixture_data=lambda season: history.copy(),
            create_trended_calculations=create_trended_calculations,
        )
        for marker in ("fixture_history_df = pd.concat(", "calculated_features_df = create_trended_calculations("):
            source = next("".join(c["source"]) for c in notebook["cells"]
                          if c["cell_type"] == "code" and "".join(c["source"]).startswith(marker))
            exec(source, namespace)
        frame = namespace["fixture_history_df"]
        np.testing.assert_array_equal(frame.minutes, frame.calc_minutes_mean_last_1_fixtures)
        np.testing.assert_array_equal(frame.calc_minutes_mean_last_3_fixtures, [10, 15, 30, 35])


if __name__ == "__main__":
    unittest.main()
