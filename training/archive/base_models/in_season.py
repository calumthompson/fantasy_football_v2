"""Loading utilities for the selected in-season points model."""

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from domain.player import Player
from domain.GameWeek import Fixture
from training.archive.training.utils import (
    add_historic_fixture_rolling_features,
)

SELECTED_IN_SEASON_MODEL_NAME = "Unweighted"
DEFAULT_IN_SEASON_ARTIFACT_PATH = (
    Path(__file__).resolve().parents[1] / "artifacts" / "in_season_model.joblib"
)
DEFAULT_IN_SEASON_SCORES_PATH = (
    Path(__file__).resolve().parents[1]
    / "artifacts"
    / "in_season_scores_2025_26.joblib"
)
DEFAULT_IN_SEASON_HISTORIC_FEATURES = (
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
    "minutes",
)
DEFAULT_IN_SEASON_WINDOWS = (1, 3, 6, 9, 12)


def build_inseason_fixture_features(
    fixtures: pd.DataFrame,
    feature_columns: tuple[str, ...] = DEFAULT_IN_SEASON_HISTORIC_FEATURES,
    windows: tuple[int, ...] = DEFAULT_IN_SEASON_WINDOWS,
) -> pd.DataFrame:
    """Build deadline-safe rolling features while retaining fixture-level rows."""
    result = (
        fixtures.drop_duplicates(["element", "fixture"], keep="last")
        .reset_index(drop=True)
        .copy()
    )
    for feature_column in feature_columns:
        result = add_historic_fixture_rolling_features(
            result,
            feature_column=feature_column,
            windows=windows,
        )
    return result


def build_api_inseason_features(
    players: Sequence[Player],
    fixtures: Sequence[Fixture],
    gameweek_number: int,
) -> pd.DataFrame:
    """Build model features for every player-fixture in an upcoming gameweek."""
    target_fixtures = [
        fixture
        for fixture in fixtures
        if fixture.gameweek_number == gameweek_number and not fixture.started
    ]
    if not target_fixtures:
        raise ValueError(f"No upcoming fixtures found for gameweek {gameweek_number}")

    fixture_by_team: dict[int, list[Fixture]] = {}
    for fixture in target_fixtures:
        fixture_by_team.setdefault(fixture.home_team_season_id, []).append(fixture)
        fixture_by_team.setdefault(fixture.away_team_season_id, []).append(fixture)

    rows: list[dict[str, Any]] = []
    for player in players:
        for performance in player.this_season_performance:
            performance_values = performance.model_dump()
            rows.append(
                {
                    **performance_values,
                    "element": performance.player_id,
                    "fixture": performance.fixture_id,
                    "GW": performance.gameweek_number,
                    "is_prediction_row": False,
                }
            )

        for fixture in fixture_by_team.get(player.team_season_id, []):
            rows.append(
                {
                    "element": player.player_id,
                    "fixture": fixture.fixture_id,
                    "GW": gameweek_number,
                    "is_prediction_row": True,
                    **{
                        feature: float("nan")
                        for feature in DEFAULT_IN_SEASON_HISTORIC_FEATURES
                    },
                }
            )

    if not rows:
        raise ValueError("No player history or upcoming player-fixture rows were built")

    features = build_inseason_fixture_features(pd.DataFrame(rows))
    return features.loc[features["is_prediction_row"]].reset_index(drop=True)


class InSeasonPredictor:
    """Load the selected artifact and score fixture-level rolling features."""

    def __init__(
        self, artifact_path: str | Path = DEFAULT_IN_SEASON_ARTIFACT_PATH
    ) -> None:
        artifact = joblib.load(Path(artifact_path))
        artifact_model_name = artifact.get("model_name")
        if artifact_model_name != SELECTED_IN_SEASON_MODEL_NAME:
            raise ValueError(
                "Expected the selected in-season model artifact to be "
                f"{SELECTED_IN_SEASON_MODEL_NAME!r}, got {artifact_model_name!r}."
            )
        self.model = artifact["model"]
        self.feature_columns = tuple(artifact["feature_columns"])

    def predict(self, features: pd.DataFrame) -> pd.Series:
        missing_columns = set(self.feature_columns) - set(features.columns)
        if missing_columns:
            raise ValueError(
                f"Missing in-season model features: {sorted(missing_columns)}"
            )
        return pd.Series(
            self.model.predict(features.loc[:, self.feature_columns]),
            index=features.index,
            name="inseason_model_score",
        )


def load_in_season_model(
    artifact_path: str | Path = DEFAULT_IN_SEASON_ARTIFACT_PATH,
) -> Any:
    """Load the unweighted CatBoost model selected by offline evaluation."""
    return InSeasonPredictor(artifact_path).model


def load_inseason_scores(
    scores_path: str | Path = DEFAULT_IN_SEASON_SCORES_PATH,
) -> pd.DataFrame:
    """Load fixture-level in-season scores exported for the ensemble."""
    scores = joblib.load(Path(scores_path))
    required_columns = {"element", "fixture", "GW", "inseason_model_score"}
    missing_columns = required_columns - set(scores.columns)
    if missing_columns:
        raise ValueError(f"Missing in-season score columns: {sorted(missing_columns)}")
    return scores.copy()
