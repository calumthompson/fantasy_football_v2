from pydantic import BaseModel


class Team(BaseModel):
    """A Premier League team identified across and within FPL seasons."""

    team_fixed_id: int
    team_season_id: int
    name: str
