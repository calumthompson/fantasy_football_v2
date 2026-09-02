from datetime import datetime

from pydantic import BaseModel


class GameWeek(BaseModel):
    """A Fantasy Premier League gameweek."""

    number: int
    deadline: datetime
    is_previous: bool
    is_current: bool
    is_next: bool


class Fixture(BaseModel):
    """A Premier League match and its assigned FPL gameweek."""

    fixture_id: int
    fixture_fixed_id: int
    gameweek_number: int | None
    kickoff_time: datetime | None
    finished: bool
    started: bool | None
    away_team_season_id: int
    home_team_season_id: int
    away_team_difficulty: int
    home_team_difficulty: int
