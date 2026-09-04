import pandas as pd

from domain.snapshot import FPLSnapshot
from prediction.models.base_model import BaseCatBoostModel
from prediction.models.in_season_model import ROLLING_FEATURES, ROLLING_WINDOWS


class AvailabilityModelRunner(BaseCatBoostModel):
    """Build fixture-horizon features shared by the minutes/appearance models."""

    def _generate_dataframe_from_snapshot(self, snapshot: FPLSnapshot) -> pd.DataFrame:
        history_rows = []
        for player in snapshot.players:
            for fixture in player.this_season_performance:
                history_rows.append(
                    {
                        "player_id": player.player_id,
                        "kickoff_time": fixture.kickoff_time,
                        "target_gw": fixture.gameweek_number,
                        **{
                            feature: getattr(fixture, feature)
                            for feature in ROLLING_FEATURES
                        },
                    }
                )

        if not history_rows:
            return pd.DataFrame()

        history_df = pd.DataFrame(history_rows).sort_values(
            ["player_id", "kickoff_time"]
        )
        grouped = history_df.groupby("player_id", sort=False)
        calculated = {}
        for window in ROLLING_WINDOWS:
            rolling = grouped[list(ROLLING_FEATURES)].rolling(
                window=window, min_periods=1
            )
            for aggregation, values in (
                ("mean", rolling.mean()),
                ("stdev", rolling.std(ddof=0)),
            ):
                values = values.reset_index(level="player_id", drop=True).sort_index()
                for feature in ROLLING_FEATURES:
                    calculated[
                        f"calc_{feature}_{aggregation}_last_{window}_fixtures"
                    ] = values[feature]

        history_df = pd.concat(
            [history_df, pd.DataFrame(calculated, index=history_df.index)], axis=1
        )
        latest = grouped.tail(1).index
        latest_df = history_df.loc[latest].set_index("player_id")

        rows = []
        for player in snapshot.players:
            if player.player_id not in latest_df.index:
                continue
            player_state = latest_df.loc[player.player_id]
            current_gw = int(player_state["target_gw"])
            for fixture in player.upcoming_fixtures:
                if fixture.gameweek_number is None:
                    continue
                rows.append(
                    {
                        "player_id": player.player_id,
                        "fixture_id": fixture.fixture_id,
                        "position": player.position,
                        "target_gw": fixture.gameweek_number,
                        "current_gw": current_gw,
                        "horizon": fixture.gameweek_number - current_gw,
                        **{
                            column: player_state[column]
                            for column in latest_df.columns
                            if column.startswith("calc_")
                        },
                    }
                )

        return pd.DataFrame(rows)
    def _model_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        model_df = df[self.feature_columns].copy()
        for column in self.categorical_columns:
            model_df[column] = model_df[column].fillna("__MISSING__").astype(str)
        return model_df

    def _predict_dataframe(self, df: pd.DataFrame):
        return self.model.predict(self._model_frame(df))
