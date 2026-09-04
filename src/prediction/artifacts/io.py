import logging
from datetime import UTC, datetime
from pathlib import Path

import joblib
from catboost import CatBoost
from pydantic import ValidationError

from prediction.artifacts.schema import CatBoostArtifactSchema

logger = logging.getLogger(__name__)

ARTIFACT_DIRECTORY = Path(__file__).resolve().parent / "trained_models"


PRE_SEASON_ARTIFACT_PATH = (
    ARTIFACT_DIRECTORY / "pre_season_model.joblib"
)
IN_SEASON_ARTIFACT_PATH = (
    ARTIFACT_DIRECTORY / "in_season_model.joblib"
)
MINUTES_ARTIFACT_PATH = (
    ARTIFACT_DIRECTORY / "minutes_model.joblib"
)
ENSEMBLE_ARTIFACT_PATH = (
    ARTIFACT_DIRECTORY / "ensemble_model.joblib"
)

def save_trained_catboost_model(
        model: CatBoost,
        feature_columns: list[str],
        categorical_columns: list[str],
        model_name: str | None,
        model_version: str | None,
        save_path: Path | str
        ):

    artifact = CatBoostArtifactSchema(
        model=model,
        feature_columns=feature_columns,
        categorical_columns=categorical_columns,
        model_name=model_name,
        model_version=model_version,
        saved_at=datetime.now(UTC)
    )

    save_path = Path(save_path)

    save_path.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(
        artifact.model_dump(mode="python"),
        save_path,
    )

    logger.info("Model %s saved at %s", model_name, save_path)


def load_trained_catboost_model(
    load_path: Path | str
) -> CatBoostArtifactSchema:

    load_path = Path(load_path)

    raw_artifact = joblib.load(load_path)

    try:
         return CatBoostArtifactSchema.model_validate(raw_artifact)

    except ValidationError as e:
         raise ValidationError(f"Validation error occurred when trying to load artifact from {load_path}. \n {e}")
