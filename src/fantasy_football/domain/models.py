from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field


class BootstrapDataRaw(BaseModel):
    """Required record collections returned by the FPL bootstrap endpoint."""

    events: list[dict[str, Any]]
    teams: list[dict[str, Any]]
    elements: list[dict[str, Any]]
    element_types: list[dict[str, Any]]


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


class Team(BaseModel):
    """A Premier League team identified across and within FPL seasons."""

    team_fixed_id: int
    team_season_id: int
    name: str


class PlayerPerformanceStats(BaseModel):
    """Performance fields shared by fixture and season player records."""

    total_points: int
    minutes: int
    goals_scored: int
    assists: int
    clean_sheets: int
    goals_conceded: int
    own_goals: int
    penalties_saved: int
    penalties_missed: int
    yellow_cards: int
    red_cards: int
    saves: int
    bonus: int
    bps: int
    influence: float
    creativity: float
    threat: float
    ict_index: float
    clearances_blocks_interceptions: int
    recoveries: int
    tackles: int
    defensive_contribution: int
    starts: int
    expected_goals: float
    expected_assists: float
    expected_goal_involvements: float
    expected_goals_conceded: float


class PlayerFixturePerformance(PlayerPerformanceStats):
    """One player's observed performance in one current-season fixture."""

    player_id: int
    fixture_id: int
    opponent_team_season_id: int
    was_home: bool
    kickoff_time: datetime
    home_team_score: int
    away_team_score: int
    gameweek_number: int
    modified: bool
    value: int
    transfers_balance: int
    selected: int
    transfers_in: int
    transfers_out: int


class PlayerSeasonPerformance(PlayerPerformanceStats):
    """One player's aggregate FPL record for a previous season."""

    season_name: str
    player_fixed_id: int
    start_cost: int
    end_cost: int


class Player(BaseModel):
    """A current FPL player and the history needed for model inference."""

    player_id: int
    player_fixed_id: int
    first_name: str
    second_name: str
    web_name: str
    team_season_id: int
    team_fixed_id: int
    team_name: str
    position_id: int
    position: str
    last_season_performance: PlayerSeasonPerformance | None
    this_season_performance: list[PlayerFixturePerformance]


class Manager(BaseModel):
    manager_id: int
    most_recent_gameweek: int
    current_points: int


class ManagerTeamPicks(BaseModel):
    selected_player_ids: list[int]
    substitute_player_ids: list[int]
    captain_player_id: int
    vice_captain_player_id: int


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
