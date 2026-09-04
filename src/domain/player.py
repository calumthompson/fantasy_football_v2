from datetime import UTC, datetime

from pydantic import BaseModel


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
    home_team_score: int | None
    away_team_score: int | None
    gameweek_number: int
    modified: bool
    value: int
    transfers_balance: int
    selected: int
    transfers_in: int
    transfers_out: int
    player_game_difficulty: int
    opponent_game_difficulty: int


class PlayerSeasonPerformance(PlayerPerformanceStats):
    """One player's aggregate FPL record for a previous season."""

    season_name: str
    player_fixed_id: int
    start_cost: int
    end_cost: int


class UpcomingFixture(BaseModel):
    """An upcoming fixture from one player's perspective."""

    fixture_id: int
    gameweek_number: int | None
    kickoff_time: datetime | None
    is_home: bool
    player_team_season_id: int
    opponent_team_season_id: int
    opponent_team_name: str
    player_game_difficulty: int
    opponent_game_difficulty: int


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
    value: int
    news: str
    last_season_performance: PlayerSeasonPerformance | None
    this_season_performance: list[PlayerFixturePerformance]
    upcoming_fixtures: list[UpcomingFixture]

    def get_most_recent_played_fixture(self) -> PlayerFixturePerformance | None:
        if not self.this_season_performance:
            return None

        return max(
            self.this_season_performance,
            key=lambda performance: performance.kickoff_time,
        )

    def get_last_week_total_points(self):

        last_week_performance = self.get_most_recent_played_fixture()

        if last_week_performance is None:
            return None
        return last_week_performance.total_points

    def get_next_fixture(self) -> UpcomingFixture:

        sorted_fixtures = sorted(self.upcoming_fixtures, key=lambda x: x.kickoff_time)

        most_recent = sorted_fixtures[0]

        if most_recent.kickoff_time > datetime.now(UTC):
            raise ValueError(
                f"Most recent fixture player for player_id {self.player_id} is in the future"
            )

        return most_recent
