import pandas as pd

from domain.snapshot import FPLSnapshot
from prediction.artifacts.io import IN_SEASON_ARTIFACT_PATH
from prediction.models.base_model import BaseCatBoostModel

ROLLING_WINDOWS = (1, 3, 6, 9, 12)

ROLLING_FEATURES = (
    "total_points",
    "minutes",
    "goals_scored",
    "assists",
    "clean_sheets",
    "goals_conceded",
    "own_goals",
    "penalties_saved",
    "penalties_missed",
    "yellow_cards",
    "red_cards",
    "saves",
    "bonus",
    "bps",
    "influence",
    "creativity",
    "threat",
    "ict_index",
    "starts",
    "expected_goals",
    "expected_assists",
    "expected_goal_involvements",
    "expected_goals_conceded",
    "transfers_balance",
    "selected",
    "value",
    "player_game_difficulty",
    "opponent_game_difficulty",
)


class InSeasonModelRunner(BaseCatBoostModel):

    def _generate_dataframe_from_snapshot(self, snapshot: FPLSnapshot) -> pd.DataFrame:

        rows = []

        for player in snapshot.players:
            for fixture in player.this_season_performance:

                rows.append(
                    {
                        "player_id": player.player_id,
                        "fixture_id": fixture.fixture_id,
                        "kickoff_time": fixture.kickoff_time.date(),
                        **{
                            feature: getattr(fixture, feature)
                            for feature in ROLLING_FEATURES
                        },
                    }
                )

        df = pd.DataFrame(rows).sort_values(["player_id", "kickoff_time"])

        player_level_grouping = df.groupby("player_id", sort=False)

        calculated_features = {}
        for window in ROLLING_WINDOWS:
            rolling_values = player_level_grouping[list(ROLLING_FEATURES)].rolling(
                window=window,
                min_periods=1,
            )
            for aggregation, values in (
                ("mean", rolling_values.mean()),
                ("stdev", rolling_values.std(ddof=0)),
            ):
                values = values.reset_index(level="player_id", drop=True).sort_index()
                for feature in ROLLING_FEATURES:
                    calculated_features[
                        f"calc_{feature}_{aggregation}_last_{window}_fixtures"
                    ] = values[feature]

        df = pd.concat([df, pd.DataFrame(calculated_features, index=df.index)], axis=1)

        # We only want to score data as of the most recent fixture per player
        return (
            df.sort_values(["player_id", "kickoff_time"])
            .groupby("player_id")
            .last()
            .reset_index()
        )


in_season_model = InSeasonModelRunner(artifact_path=IN_SEASON_ARTIFACT_PATH)
