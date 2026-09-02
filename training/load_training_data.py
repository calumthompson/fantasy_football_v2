import os
import pandas as pd 
from pathlib import Path
from dotenv import load_dotenv
import re


load_dotenv()
_TRAINING_DATA_REPO_ADDRESS = Path(os.environ["TRAINING_DATA_REPO_ADDRESS"])


def load_historic_player_fixture_data(season: str) -> pd.DataFrame:
    """Load historic FPL data with one row per player-fixture."""
    _SEASON_PATTERN = re.compile(r"^(?P<start_year>\d{4})-(?P<end_year>\d{2})$")
    match = _SEASON_PATTERN.fullmatch(season)

    if match is None:
        raise ValueError(
            f"Invalid season {season!r}; expected format 'YYYY-YY', "
            "for example '2022-23'."
        )

    data_path = (
        _TRAINING_DATA_REPO_ADDRESS
        / "data"
        / season
        / "gws"
        / "merged_gw.csv"
    )

    fixture_data = pd.read_csv(data_path)
    return fixture_data.rename(columns={"element": "player_id", "fixture": "fixture_id"})


def load_team_data(season: str) -> pd.DataFrame:
    """Load the historic FPL team lookup for a season."""
    data_path = (
        _TRAINING_DATA_REPO_ADDRESS
        / "data"
        / season
        / "teams.csv"
    )
    return pd.read_csv(data_path)


def load_player_data(season: str) -> pd.DataFrame:
    """Load the historic raw player lookup, including stable player codes."""
    data_path = (
        _TRAINING_DATA_REPO_ADDRESS
        / "data"
        / season
        / "players_raw.csv"
    )
    return pd.read_csv(data_path)


def load_fixtures_data(season: str) -> pd.DataFrame:

    data_path = (
        _TRAINING_DATA_REPO_ADDRESS
        / "data"
        / season
        / "fixtures.csv"
    )
    return pd.read_csv(data_path)