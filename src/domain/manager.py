from pydantic import BaseModel


class Manager(BaseModel):
    manager_id: int
    team_name: str
    most_recent_gameweek: int
    current_points: int
    bank: int
    entered_leagues: list[int]


class ManagerTeamPicks(BaseModel):
    selected_player_ids: list[int]
    substitute_player_ids: list[int]
    captain_player_id: int
    vice_captain_player_id: int


class RivalTeam(BaseModel):
    manager_id: int
    team_name: str