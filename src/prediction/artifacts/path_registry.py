from pathlib import Path

ARTIFACT_DIRECTORY = Path(__file__).resolve().parent / "trained_models"

PRE_SEASON_ARTIFACT_PATH = (
    ARTIFACT_DIRECTORY / "pre_season_model.joblib"
)

IN_SEASON_ARTIFACT_PATH = (
    ARTIFACT_DIRECTORY / "in_season_model.joblib"
)

ENSEMBLE_ARTIFACT_PATH = (
    ARTIFACT_DIRECTORY / "ensemble_model.joblib"
)