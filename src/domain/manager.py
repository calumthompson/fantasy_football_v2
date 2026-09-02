from pydantic import BaseModel


class Manager(BaseModel):
    manager_id: int
    most_recent_gameweek: int
    current_points: int


class ManagerTeamPicks(BaseModel):
    selected_player_ids: list[int]
    substitute_player_ids: list[int]
    captain_player_id: int
    vice_captain_player_id: int
