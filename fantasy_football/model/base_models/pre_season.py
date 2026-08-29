"""API-compatible feature engineering and inference for the pre-season model."""

from pathlib import Path
from typing import Any, Sequence

import joblib
import pandas as pd


DEFAULT_CATEGORICAL_COLUMNS = ("position", "team")
DEFAULT_NUMERIC_FEATURES = (
    "total_points",
    "minutes",
    "assists",
    "bonus",
    "bps",
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
    "starts",
    "threat",
    "yellow_cards",
    "clearances_blocks_interceptions",
    "defensive_contribution",
    "recoveries",
    "tackles",
    "expected_goals",
    "expected_assists",
    "expected_goal_involvements",
    "expected_goals_conceded",
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
    return values.iloc[-1] if len(values) else float("nan")


def _first_non_null(series: pd.Series) -> Any:
    values = series.dropna()
    return values.iloc[0] if len(values) else float("nan")


def build_season_features(
    gameweeks: pd.DataFrame,
    feature_columns: Sequence[str] = DEFAULT_NUMERIC_FEATURES,
) -> pd.DataFrame:
    """Build fields reproducible from the FPL API ``history_past`` record.

    Numeric performance fields are season totals. Start and end cost correspond
    to the first and final available ``value`` in the season. Weekly means,
    standard deviations and trends are deliberately excluded because the live
    API does not expose the underlying historic fixture rows for past seasons.
    """
    required_columns = {"name", "GW", "value"}
    missing_columns = required_columns - set(gameweeks.columns)
    if missing_columns:
        raise ValueError(f"Missing gameweek columns: {sorted(missing_columns)}")

    data = gameweeks.sort_values(["name", "GW"]).copy()
    available_features = [
        column for column in feature_columns if column in data.columns
    ]
    rows: list[dict[str, Any]] = []

    for name, player_rows in data.groupby("name", sort=False):
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
            "start_cost": _first_non_null(
                pd.to_numeric(player_rows["value"], errors="coerce")
            ),
            "end_cost": _latest_non_null(
                pd.to_numeric(player_rows["value"], errors="coerce")
            ),
        }
        for column in available_features:
            values = pd.to_numeric(player_rows[column], errors="coerce")
            row[column] = values.sum(min_count=1)
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
