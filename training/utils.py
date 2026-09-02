import pandas as pd


def create_fixture_horizon_df(
        fixture_history_df: pd.DataFrame,
        max_horizon: int,
        calculated_columns: list[str],
        target_column: str
):
    
    end_of_gameweek_features_df = (
        fixture_history_df
        .sort_values(["player_id", "season", "target_gw", "fixture_id"])
        .groupby(
            ["player_id", "season", "target_gw"],
            sort=False,
        )
        .tail(1)[
            ["player_id", "season", "target_gw", *calculated_columns]
        ]
        .rename(columns={"target_gw": "current_gw"})
    )


    # Create every gameweek for every player so blank gameweeks can carry
    # forward the latest available feature state.

    player_gameweek_features_df = (
        fixture_history_df[
            ["player_id", "season"]
        ]
        .drop_duplicates()
        .merge(
            pd.DataFrame({
                "current_gw": range(
                    1,
                    int(fixture_history_df["target_gw"].max()) + 1,
                )
            }),
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
        player_gameweek_features_df
        .groupby(
            ["player_id", "season"],
            sort=False,
        )[calculated_columns]
        .ffill()
    )


    # Create one row per target fixture and forecast horizon.

    fixture_history_with_horizons_df = (
        fixture_history_df[
            [
                "player_id",
                "season",
                "fixture_id",
                "target_gw",
                "position",
                target_column,
            ]
        ]
        .merge(
            pd.DataFrame({
                "horizon": range(1, max_horizon + 1)
            }),
            how="cross",
        )
    )

    fixture_history_with_horizons_df["current_gw"] = (
        fixture_history_with_horizons_df["target_gw"]
        - fixture_history_with_horizons_df["horizon"]
    )


    # Require at least one completed gameweek of current-season information.

    fixture_history_with_horizons_df = (
        fixture_history_with_horizons_df.loc[
            fixture_history_with_horizons_df["current_gw"] >= 1
        ]
    )


    # Attach the feature state available at the end of current_gw.

    fixture_history_with_horizons_df = (
        fixture_history_with_horizons_df.merge(
            player_gameweek_features_df,
            on=["player_id", "season", "current_gw"],
            how="left",
            validate="many_to_one",
        )
    )

    return fixture_history_with_horizons_df