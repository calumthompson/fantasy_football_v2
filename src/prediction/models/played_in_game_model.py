import numpy as np
import pandas as pd

from prediction.artifacts.io import PLAYED_IN_GAME_ARTIFACT_PATH
from prediction.models.availability_model import AvailabilityModelRunner


class PlayedInGameModelRunner(AvailabilityModelRunner):
    def _predict_dataframe(self, df: pd.DataFrame) -> np.ndarray:
        return self.model.predict_proba(self._model_frame(df))[:, 1]


played_in_game_model = PlayedInGameModelRunner(
    artifact_path=PLAYED_IN_GAME_ARTIFACT_PATH
)
