import pandas as pd

from training.config import (
    NUMERIC_FEATURES,
    ROLLING_WINDOWS,
)
from training.load_training_data import load_historic_player_fixture_data


def create_fixture_horizon_df(
    fixture_history_df: pd.DataFrame,
    max_horizon: int,
    calculated_columns: list[str],
    target_column: str,
):

    fixture_history_df = fixture_history_df.copy()

    end_of_gameweek_features_df = (
        fixture_history_df.sort_values(
            ["player_id", "season", "target_gw", "fixture_id"]
        )
        .groupby(
            ["player_id", "season", "target_gw"],
            sort=False,
        )
        .tail(1)[["player_id", "season", "target_gw", *calculated_columns]]
        .rename(columns={"target_gw": "current_gw"})
    )

    # Create every gameweek for every player so blank gameweeks can carry
    # forward the latest available feature state.

    player_gameweek_features_df = (
        fixture_history_df[["player_id", "season"]]
        .drop_duplicates()
        .merge(
            pd.DataFrame(
                {
                    "current_gw": range(
                        1,
                        int(fixture_history_df["target_gw"].max()) + 1,
                    )
                }
            ),
            how="cross",
        )
        .merge(
            end_of_gameweek_features_df,
            on=["player_id", "season", "current_gw"],
            how="left",
            validate="one_to_one",
        )
        .sort_values(["player_id", "season", "current_gw"])
    )

    player_gameweek_features_df[calculated_columns] = (
        player_gameweek_features_df.groupby(
            ["player_id", "season"],
            sort=False,
        )[calculated_columns].ffill()
    )

    # Create one row per target fixture and forecast horizon.

    fixture_history_with_horizons_df = fixture_history_df[
        [
            "player_id",
            "season",
            "fixture_id",
            "target_gw",
            "position",
            target_column,
        ]
    ].merge(
        pd.DataFrame({"horizon": range(1, max_horizon + 1)}),
        how="cross",
    )

    fixture_history_with_horizons_df["current_gw"] = (
        fixture_history_with_horizons_df["target_gw"]
        - fixture_history_with_horizons_df["horizon"]
    )

    # Require at least one completed gameweek of current-season information.

    fixture_history_with_horizons_df = fixture_history_with_horizons_df.loc[
        fixture_history_with_horizons_df["current_gw"] >= 1
    ]

    # Attach the feature state available at the end of current_gw.

    fixture_history_with_horizons_df = fixture_history_with_horizons_df.merge(
        player_gameweek_features_df,
        on=["player_id", "season", "current_gw"],
        how="left",
        validate="many_to_one",
    )

    return fixture_history_with_horizons_df


def create_trended_calculations(
    fixture_history_df: pd.DataFrame,
    rolling_windows=ROLLING_WINDOWS,
    numeric_features=NUMERIC_FEATURES,
):

    calculated_feature_dfs = []

    for window in rolling_windows:
        rolling_mean_df = (
            fixture_history_df.groupby(["player_id", "season"], sort=False)[
                numeric_features
            ]
            .rolling(window=window, min_periods=1)
            .mean()
            .reset_index(level=["player_id", "season"], drop=True)
            .sort_index()
        )
        rolling_mean_df.columns = [
            f"calc_{feature}_mean_last_{window}_fixtures"
            for feature in numeric_features
        ]

        rolling_stdev_df = (
            fixture_history_df.groupby(["player_id", "season"], sort=False)[
                numeric_features
            ]
            .rolling(window=window, min_periods=1)
            .std(ddof=0)
            .reset_index(level=["player_id", "season"], drop=True)
            .sort_index()
        )
        rolling_stdev_df.columns = [
            f"calc_{feature}_stdev_last_{window}_fixtures"
            for feature in numeric_features
        ]

        rolling_window_df = pd.concat(
            [rolling_mean_df, rolling_stdev_df],
            axis=1,
        ).astype("float32")

        calculated_feature_dfs.append(rolling_window_df)

    return pd.concat(calculated_feature_dfs, axis=1)


def create_ensemble_training_df(
    season: str,
    pre_season: str,
) -> pd.DataFrame:
    from prediction.models.in_season_model import in_season_model
    from prediction.models.pre_season_model import pre_season_model

    fixture_history_df = (
        load_historic_player_fixture_data(season)
        .rename(
            columns={
                "GW": "target_gw",
                "player_team_difficulty": "player_game_difficulty",
                "opponent_team_difficulty": "opponent_game_difficulty",
            }
        )
        .assign(season=season)
        .drop_duplicates()
        .sort_values(["player_id", "season", "target_gw", "fixture_id"])
        .reset_index(drop=True)
    )

    pre_season_history_df = (
        load_historic_player_fixture_data(pre_season)
        .groupby(["name", "position"])[NUMERIC_FEATURES]
        .sum(min_count=1)
        .rename(
            columns={feature: f"season_sum_{feature}" for feature in NUMERIC_FEATURES}
        )
        .reset_index()
    )

    pre_season_history_df["pre_season_model_score"] = (
        pre_season_model.predict_for_dataframe(pre_season_history_df)
    )

    fixture_history_df = fixture_history_df.merge(
        pre_season_history_df[["name", "position", "pre_season_model_score"]],
        on=["name", "position"],
        how="left",
        validate="many_to_one",
    )

    calculated_features_df = create_trended_calculations(
        fixture_history_df,
        rolling_windows=ROLLING_WINDOWS,
        numeric_features=NUMERIC_FEATURES,
    )

    # Each ensemble row represents the fixture being predicted. Shift the
    # aggregates so they contain only performances completed before it.
    calculated_features_df = calculated_features_df.groupby(
        [fixture_history_df["player_id"], fixture_history_df["season"]],
        sort=False,
    ).shift(1)

    fixture_history_df = pd.concat(
        [fixture_history_df, calculated_features_df],
        axis=1,
    )

    fixture_history_df["in_season_model_score"] = in_season_model.predict_for_dataframe(
        fixture_history_df
    )

    return fixture_history_df
