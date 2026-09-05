from datetime import datetime, timedelta

from pydantic import BaseModel, Field

from domain.gameweek import Fixture, GameWeek
from domain.manager import Manager, ManagerTeamPicks, RivalTeam
from domain.models import Team
from domain.player import Player


class FPLSnapshot(BaseModel):
    """Validated FPL data retrieved as one logical snapshot."""

    started_at: datetime
    retrieved_at: datetime
    time_to_complete: timedelta
    gameweeks: list[GameWeek]
    teams: list[Team]
    fixtures: list[Fixture]
    players: list[Player] = Field(default_factory=list)
    manager: Manager
    current_manager_team_picks: ManagerTeamPicks
    rival_teams: list[RivalTeam]

    def get_player_by_id(self, player_id: int) -> Player:
        player = [player for player in self.players if player.player_id == player_id]

        if len(player) > 1:
            raise ValueError(f"Duplicate players found for ID {player_id}")
        return player[0]

    def get_current_team_picks(self) -> list[Player]:

        return [
            self.get_player_by_id(picked_id)
            for picked_id in self.current_manager_team_picks.selected_player_ids
        ]

    def get_current_team_subs(self) -> list[Player]:

        return [
            self.get_player_by_id(picked_id)
            for picked_id in self.current_manager_team_picks.substitute_player_ids
        ]
