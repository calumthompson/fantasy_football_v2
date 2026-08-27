from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def load_gw_data(season: str) -> pd.DataFrame:
    """
    Load the historic merged gameweek data for a given season.

    Args:
        season (str): The season for which to load the data (e.g., '2022-23').

    """

    data_path = (
        Path.cwd().parents[4]
        / "historic_data"
        / "data"
        / season
        / "gws"
        / "merged_gw.csv"
    )
    return pd.read_csv(data_path)


def create_lagged_feature(
    df: pd.DataFrame, feature_name: str, lag: int, agg_func: str,  groupby_cols: list = ['element']
) -> pd.DataFrame:
    """
    Create a lagged feature in the DataFrame.

    Args:
        df (pd.DataFrame): The input DataFrame.
        feature_name (str): The name of the feature to lag.
        lag (int): The number of periods to lag.
        groupby_cols (list): Columns to group by before creating the lagged feature.

    Returns:
        pd.DataFrame: DataFrame with the new lagged feature.
    """
    df = df.sort_values(groupby_cols + ["GW"])
    df[f"{feature_name}_lag_{lag}"] = (
        df.groupby(groupby_cols)[feature_name].shift(lag)
    )
    return df


def add_historic_rolling_features(
    df: pd.DataFrame,
    feature_column: str,
    windows: tuple[int, ...] = (1, 3, 6, 9, 12),
) -> pd.DataFrame:
    """Add rolling means and standard deviations for one historic feature."""
    result = df.sort_values(["element", "GW"]).copy()
    history = result.groupby("element", sort=False)[feature_column].shift(1)
    grouped_history = history.groupby(result["element"], sort=False)

    for window in windows:
        rolling = grouped_history.rolling(window=window, min_periods=1)
        result[f"calc_{feature_column}_mean_last_{window}_gw"] = (
            rolling.mean().reset_index(level="element", drop=True)
        )
        result[f"calc_{feature_column}_stdev_last_{window}_gw"] = (
            rolling.std(ddof=0).reset_index(level="element", drop=True)
        )

    return result


def create_correlation_matrix(
    df: pd.DataFrame, columns: list[str], target_variable: str
) -> pd.DataFrame:
    """Return the correlation matrix for a variable and the target variable."""
    return df[columns + [target_variable]].corr()[target_variable].sort_values(ascending=False)


def plot_calculated_feature_correlations(df: pd.DataFrame):
    """Plot pairwise correlations between every calculated feature."""
    feature_columns = [column for column in df.columns if column.startswith("calc_")]
    if not feature_columns:
        raise ValueError("DataFrame has no calculated feature columns prefixed 'calc_'.")

    correlations = df[feature_columns].corr()
    feature_count = len(feature_columns)
    figure_size = max(12, feature_count * 0.28)
    figure, axis = plt.subplots(figsize=(figure_size, figure_size))
    heatmap = axis.imshow(
        correlations.to_numpy(copy=False),
        cmap="coolwarm",
        vmin=-1,
        vmax=1,
        interpolation="none",
    )

    positions = range(feature_count)
    labels = [column.removeprefix("calc_") for column in feature_columns]
    axis.set_xticks(positions, labels=labels, rotation=90, fontsize=7)
    axis.set_yticks(positions, labels=labels, fontsize=7)
    axis.set_title("Calculated feature correlations", pad=16)
    figure.colorbar(heatmap, ax=axis, label="Pearson correlation", shrink=0.8)
    figure.tight_layout()
    plt.show()
    return figure, axis
