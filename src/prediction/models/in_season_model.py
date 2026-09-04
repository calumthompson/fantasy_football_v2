import pandas as pd

from domain.snapshot import FPLSnapshot
from prediction.artifacts.io import IN_SEASON_ARTIFACT_PATH
from prediction.models.base_model import BaseCatBoostModel


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
                        "total_points": fixture.total_points,
                        "minutes": fixture.minutes,
                        "ict_index": fixture.ict_index,
                        "creativity": fixture.creativity,
                        "threat": fixture.threat,
                        "assists": fixture.assists,
                        "expected_goal_involvements": fixture.expected_goal_involvements,
                    }
                )

        df = pd.DataFrame(rows).sort_values(["player_id", "kickoff_time"])

        player_level_grouping = df.groupby("player_id", sort=False)

        def rolling_metric(column: str, window: int, aggregation: str) -> pd.Series:
            rolling_values = player_level_grouping[column].rolling(
                window=window,
                min_periods=1,
            )
            if aggregation == "mean":
                values = rolling_values.mean()
            else:
                values = rolling_values.std(ddof=0)

            return values.reset_index(level="player_id", drop=True).sort_index()

        df["calc_total_points_mean_last_1_fixtures"] = rolling_metric(
            "total_points", 1, "mean"
        )
        df["calc_minutes_mean_last_1_fixtures"] = rolling_metric("minutes", 1, "mean")
        df["calc_ict_index_mean_last_1_fixtures"] = rolling_metric(
            "ict_index", 1, "mean"
        )

        df["calc_minutes_mean_last_3_fixtures"] = rolling_metric("minutes", 3, "mean")
        df["calc_total_points_mean_last_3_fixtures"] = rolling_metric(
            "total_points", 3, "mean"
        )

        df["calc_creativity_mean_last_6_fixtures"] = rolling_metric(
            "creativity", 6, "mean"
        )
        df["calc_ict_index_mean_last_6_fixtures"] = rolling_metric(
            "ict_index", 6, "mean"
        )

        df["calc_ict_index_mean_last_9_fixtures"] = rolling_metric(
            "ict_index", 9, "mean"
        )
        df["calc_total_points_mean_last_9_fixtures"] = rolling_metric(
            "total_points", 9, "mean"
        )

        df["calc_total_points_mean_last_12_fixtures"] = rolling_metric(
            "total_points", 12, "mean"
        )
        df["calc_minutes_mean_last_12_fixtures"] = rolling_metric("minutes", 12, "mean")
        df["calc_minutes_stdev_last_12_fixtures"] = rolling_metric(
            "minutes", 12, "stdev"
        )
        df["calc_ict_index_mean_last_12_fixtures"] = rolling_metric(
            "ict_index", 12, "mean"
        )
        df["calc_ict_index_stdev_last_12_fixtures"] = rolling_metric(
            "ict_index", 12, "stdev"
        )
        df["calc_creativity_mean_last_12_fixtures"] = rolling_metric(
            "creativity", 12, "mean"
        )
        df["calc_creativity_stdev_last_12_fixtures"] = rolling_metric(
            "creativity", 12, "stdev"
        )
        df["calc_threat_stdev_last_12_fixtures"] = rolling_metric("threat", 12, "stdev")
        df["calc_threat_mean_last_12_fixtures"] = rolling_metric("threat", 12, "mean")
        df["calc_assists_mean_last_12_fixtures"] = rolling_metric("assists", 12, "mean")
        df["calc_expected_goal_involvements_stdev_last_12_fixtures"] = rolling_metric(
            "expected_goal_involvements", 12, "stdev"
        )

        # We only want to score data as of the most recent fixture per player
        return df.sort_values(['player_id', 'kickoff_time']).groupby('player_id').last().reset_index()


in_season_model = InSeasonModelRunner(artifact_path=IN_SEASON_ARTIFACT_PATH)
