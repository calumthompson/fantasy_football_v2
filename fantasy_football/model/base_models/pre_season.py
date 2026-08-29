"""Feature engineering and inference for the pre-season points model."""

from pathlib import Path
from typing import Any, Sequence

import joblib
import numpy as np
import pandas as pd


DEFAULT_DECAY = 0.90
DEFAULT_CATEGORICAL_COLUMNS = ("position", "team")
DEFAULT_NUMERIC_FEATURES = (
    "assists",
    "clean_sheets",
    "creativity",
    "goals_conceded",
    "goals_scored",
    "ict_index",
    "influence",
    "own_goals",
    "penalties_missed",
    "penalties_saved",
    "red_cards",
    "saves",
    "selected",
    "starts",
    "threat",
    "transfers_balance",
    "value",
    "yellow_cards",
    "clearances_blocks_interceptions",
    "defensive_contribution",
    "recoveries",
    "tackles",
    "minutes",
)
DEFAULT_ARTIFACT_PATH = (
    Path(__file__).resolve().parents[1] / "artifacts" / "pre_season_model.joblib"
)
DEFAULT_PRESEASON_SCORES_PATH = (
    Path(__file__).resolve().parents[1]
    / "artifacts"
    / "pre_season_scores_2025_26.joblib"
)


def _latest_non_null(series: pd.Series) -> Any:
    values = series.dropna()
    return values.iloc[-1] if len(values) else np.nan


def _decayed_mean(values: pd.Series, decay: float) -> float:
    numeric_values = (
        pd.to_numeric(values, errors="coerce").dropna().to_numpy(dtype=float)
    )
    if not len(numeric_values):
        return np.nan
    weights = decay ** np.arange(len(numeric_values) - 1, -1, -1)
    return float(np.average(numeric_values, weights=weights))


def build_season_features(
    gameweeks: pd.DataFrame,
    feature_columns: Sequence[str] = DEFAULT_NUMERIC_FEATURES,
    decay: float = DEFAULT_DECAY,
) -> pd.DataFrame:
    """Aggregate one season of gameweek rows into one feature row per player."""
    required_columns = {"name", "GW", "minutes"}
    missing_columns = required_columns - set(gameweeks.columns)
    if missing_columns:
        raise ValueError(f"Missing gameweek columns: {sorted(missing_columns)}")

    data = gameweeks.sort_values(["name", "GW"]).copy()
    available_features = [
        column for column in feature_columns if column in data.columns
    ]
    rows: list[dict[str, Any]] = []

    for name, player_rows in data.groupby("name", sort=False):
        appearances = player_rows.loc[player_rows["minutes"].fillna(0).gt(0)]
        row: dict[str, Any] = {
            "name": name,
            "element": (
                _latest_non_null(player_rows["element"])
                if "element" in player_rows
                else np.nan
            ),
            "position": (
                _latest_non_null(player_rows["position"])
                if "position" in player_rows
                else "__MISSING__"
            ),
            "team": (
                _latest_non_null(player_rows["team"])
                if "team" in player_rows
                else "__MISSING__"
            ),
            "games_available": player_rows["GW"].nunique(),
            "appearances": appearances["GW"].nunique(),
            "minutes_sum": player_rows["minutes"].sum(),
        }
        for column in available_features:
            all_values = pd.to_numeric(player_rows[column], errors="coerce")
            played_values = pd.to_numeric(appearances[column], errors="coerce")
            row[f"{column}_sum"] = all_values.sum(min_count=1)
            row[f"{column}_mean"] = played_values.mean()
            row[f"{column}_std"] = played_values.std(ddof=0)
            row[f"{column}_decayed_mean"] = _decayed_mean(
                played_values, decay=decay
            )
        rows.append(row)

    return pd.DataFrame(rows)


class PreSeasonPredictor:
    """Load the trained pre-season artifact and produce ensemble-ready predictions."""

    def __init__(self, artifact_path: str | Path = DEFAULT_ARTIFACT_PATH) -> None:
        self.artifact_path = Path(artifact_path)
        artifact = joblib.load(self.artifact_path)
        self.model = artifact["model"]
        self.feature_columns = tuple(artifact["feature_columns"])
        self.categorical_columns = tuple(artifact["categorical_columns"])

    def predict(self, features: pd.DataFrame) -> pd.Series:
        """Predict early-season average points from player-level season features."""
        missing_columns = set(self.feature_columns) - set(features.columns)
        if missing_columns:
            raise ValueError(
                f"Missing pre-season model features: {sorted(missing_columns)}"
            )

        model_input = features.loc[:, self.feature_columns].copy()
        model_input.loc[:, self.categorical_columns] = (
            model_input.loc[:, self.categorical_columns]
            .fillna("__MISSING__")
            .astype(str)
        )
        predictions = self.model.predict(model_input)
        return pd.Series(
            predictions,
            index=features.index,
            name="preseason_expected_points",
        )


def load_preseason_scores(
    scores_path: str | Path = DEFAULT_PRESEASON_SCORES_PATH,
) -> pd.DataFrame:
    """Load the player-level pre-season scores exported for the ensemble."""
    scores = joblib.load(Path(scores_path))
    required_columns = {"code", "name", "preseason_model_score"}
    missing_columns = required_columns - set(scores.columns)
    if missing_columns:
        raise ValueError(f"Missing pre-season score columns: {sorted(missing_columns)}")
    return scores.loc[:, ["code", "name", "preseason_model_score"]].copy()
