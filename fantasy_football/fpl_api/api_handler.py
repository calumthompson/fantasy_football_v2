#%%
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from warnings import warn

import requests
from pydantic import ValidationError

from fantasy_football.fpl_api.models import (
    FPLSnapshot,
    Fixture,
    GameWeek,
    Player,
    PlayerFixturePerformance,
    PlayerSeasonPerformance,
    Team,
)


_BOOTSTRAP_STATIC_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
_FIXTURE_DATA_URL = "https://fantasy.premierleague.com/api/fixtures/"
_PLAYER_DATA_URL = "https://fantasy.premierleague.com/api/element-summary/{element_id}/"
_DEFAULT_EXAMPLE_DIR = Path(__file__).parent / "examples"


class FPLAPIError(RuntimeError):
    """Raised when FPL data cannot be downloaded or parsed."""


class FPLParser:
    """Translate raw FPL API records into validated domain models."""

    @staticmethod
    def parse_gameweeks(records: list[dict[str, Any]]) -> list[GameWeek]:
        try:
            return [
                GameWeek(
                    number=record["id"],
                    deadline=record["deadline_time"],
                    is_previous=record["is_previous"],
                    is_current=record["is_current"],
                    is_next=record["is_next"],
                )
                for record in records
            ]
        except (KeyError, TypeError, ValidationError) as error:
            raise FPLAPIError(f"Unable to parse FPL gameweek data: {error}") from error

    @staticmethod
    def parse_teams(records: list[dict[str, Any]]) -> list[Team]:
        try:
            return [
                Team(
                    team_fixed_id=record["code"],
                    team_season_id=record["id"],
                    name=record["name"],
                )
                for record in records
            ]
        except (KeyError, TypeError, ValidationError) as error:
            raise FPLAPIError(f"Unable to parse FPL team data: {error}") from error

    @staticmethod
    def parse_player(
        player_record: dict[str, Any],
        summary: dict[str, Any],
        team_names: dict[int, str],
        position_names: dict[int, str],
    ) -> Player:
        try:
            history = [
                PlayerFixturePerformance(
                    player_id=record["element"],
                    fixture_id=record["fixture"],
                    opponent_team_season_id=record["opponent_team"],
                    was_home=record["was_home"],
                    kickoff_time=record["kickoff_time"],
                    home_team_score=record["team_h_score"],
                    away_team_score=record["team_a_score"],
                    gameweek_number=record["round"],
                    modified=record["modified"],
                    total_points=record["total_points"],
                    minutes=record["minutes"],
                    goals_scored=record["goals_scored"],
                    assists=record["assists"],
                    clean_sheets=record["clean_sheets"],
                    goals_conceded=record["goals_conceded"],
                    own_goals=record["own_goals"],
                    penalties_saved=record["penalties_saved"],
                    penalties_missed=record["penalties_missed"],
                    yellow_cards=record["yellow_cards"],
                    red_cards=record["red_cards"],
                    saves=record["saves"],
                    bonus=record["bonus"],
                    bps=record["bps"],
                    influence=record["influence"],
                    creativity=record["creativity"],
                    threat=record["threat"],
                    ict_index=record["ict_index"],
                    clearances_blocks_interceptions=record[
                        "clearances_blocks_interceptions"
                    ],
                    recoveries=record["recoveries"],
                    tackles=record["tackles"],
                    defensive_contribution=record["defensive_contribution"],
                    starts=record["starts"],
                    expected_goals=record["expected_goals"],
                    expected_assists=record["expected_assists"],
                    expected_goal_involvements=record[
                        "expected_goal_involvements"
                    ],
                    expected_goals_conceded=record["expected_goals_conceded"],
                    value=record["value"],
                    transfers_balance=record["transfers_balance"],
                    selected=record["selected"],
                    transfers_in=record["transfers_in"],
                    transfers_out=record["transfers_out"],
                )
                for record in summary["history"]
            ]

            past_record = max(
                summary["history_past"],
                key=lambda record: int(record["season_name"].split("/")[0]),
                default=None,
            )
            previous_season_history = (
                FPLParser._parse_season_history(past_record)
                if past_record is not None
                else None
            )

            team_id = player_record["team"]
            position_id = player_record["element_type"]
            return Player(
                player_id=player_record["id"],
                player_fixed_id=player_record["code"],
                first_name=player_record["first_name"],
                second_name=player_record["second_name"],
                web_name=player_record["web_name"],
                team_season_id=team_id,
                team_fixed_id=player_record["team_code"],
                team_name=team_names[team_id],
                position_id=position_id,
                position=position_names[position_id],
                last_season_performance=previous_season_history,
                this_season_performance=history,
            )
        except (KeyError, TypeError, ValueError, ValidationError) as error:
            player_id = player_record.get("id", "unknown")
            raise FPLAPIError(
                f"Unable to parse FPL player {player_id}: {error}"
            ) from error

    @staticmethod
    def _parse_season_history(record: dict[str, Any]) -> PlayerSeasonPerformance:
        return PlayerSeasonPerformance(
            season_name=record["season_name"],
            player_fixed_id=record["element_code"],
            start_cost=record["start_cost"],
            end_cost=record["end_cost"],
            total_points=record["total_points"],
            minutes=record["minutes"],
            goals_scored=record["goals_scored"],
            assists=record["assists"],
            clean_sheets=record["clean_sheets"],
            goals_conceded=record["goals_conceded"],
            own_goals=record["own_goals"],
            penalties_saved=record["penalties_saved"],
            penalties_missed=record["penalties_missed"],
            yellow_cards=record["yellow_cards"],
            red_cards=record["red_cards"],
            saves=record["saves"],
            bonus=record["bonus"],
            bps=record["bps"],
            influence=record["influence"],
            creativity=record["creativity"],
            threat=record["threat"],
            ict_index=record["ict_index"],
            clearances_blocks_interceptions=record[
                "clearances_blocks_interceptions"
            ],
            recoveries=record["recoveries"],
            tackles=record["tackles"],
            defensive_contribution=record["defensive_contribution"],
            starts=record["starts"],
            expected_goals=record["expected_goals"],
            expected_assists=record["expected_assists"],
            expected_goal_involvements=record["expected_goal_involvements"],
            expected_goals_conceded=record["expected_goals_conceded"],
        )

    @staticmethod
    def parse_fixtures(records: list[dict[str, Any]]) -> list[Fixture]:
        try:
            return [
                Fixture(
                    fixture_id=record["id"],
                    fixture_fixed_id=record["code"],
                    gameweek_number=record["event"],
                    kickoff_time=record["kickoff_time"],
                    finished=record["finished"],
                    started=record["started"],
                    away_team_season_id=record["team_a"],
                    home_team_season_id=record["team_h"],
                )
                for record in records
            ]
        except (KeyError, TypeError, ValidationError) as error:
            raise FPLAPIError(f"Unable to parse FPL fixture data: {error}") from error


class FPLAPIClient:
    """Download FPL API data and return validated objects."""

    def __init__(
        self,
        timeout: float = 15.0,
        session: requests.Session | None = None,
        parser: FPLParser | None = None,
        example_dir: Path | None = None,
    ) -> None:
        self._timeout = timeout
        self._session = session or requests.Session()
        self._parser = parser or FPLParser()
        self._example_dir = example_dir or _DEFAULT_EXAMPLE_DIR

    def _load_example_json(self, filename: str, api_error: Exception) -> Any:
        example_path = self._example_dir / filename
        try:
            with example_path.open(encoding="utf-8") as example_file:
                data = json.load(example_file)
        except (OSError, ValueError) as example_error:
            raise FPLAPIError(
                f"Failed to fetch FPL API data and could not load fallback "
                f"response {example_path}: {example_error}"
            ) from api_error

        warn(
            f"FPL API unavailable; using example response {example_path}",
            RuntimeWarning,
            stacklevel=2,
        )
        return data

    def _get_json(self, url: str, fallback_filename: str) -> Any:
        try:
            response = self._session.get(url, timeout=self._timeout)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as error:
            return self._load_example_json(fallback_filename, error)

    def fetch_bootstrap(self) -> dict[str, Any]:
        data = self._get_json(_BOOTSTRAP_STATIC_URL, "bootstrap-static.json")
        if not isinstance(data, dict):
            raise FPLAPIError("bootstrap-static returned an unexpected response shape")
        return data

    def fetch_fixtures(self) -> list[dict[str, Any]]:
        data = self._get_json(_FIXTURE_DATA_URL, "fixtures.json")
        if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
            raise FPLAPIError("fixtures returned an unexpected response shape")
        return data

    def fetch_player_summary(self, player_id: int) -> dict[str, Any]:
        data = self._get_json(
            _PLAYER_DATA_URL.format(element_id=player_id),
            f"element-summary-{player_id}.json",
        )
        if not isinstance(data, dict):
            raise FPLAPIError("element-summary returned an unexpected response shape")
        return data

    def load_players(self, bootstrap: dict[str, Any] | None = None) -> list[Player]:
        """Load every player with current and most recent completed-season history."""

        bootstrap = bootstrap or self.fetch_bootstrap()
        raw_players = bootstrap.get("elements")
        raw_teams = bootstrap.get("teams")
        raw_positions = bootstrap.get("element_types")
        if not isinstance(raw_players, list):
            raise FPLAPIError("bootstrap-static contains invalid player data")
        if not isinstance(raw_teams, list):
            raise FPLAPIError("bootstrap-static contains invalid team data")
        if not isinstance(raw_positions, list):
            raise FPLAPIError("bootstrap-static contains invalid position data")

        try:
            team_names = {record["id"]: record["name"] for record in raw_teams}
            position_names = {
                record["id"]: record["singular_name_short"]
                for record in raw_positions
            }
        except (KeyError, TypeError) as error:
            raise FPLAPIError(f"Unable to map FPL player metadata: {error}") from error

        players: list[Player] = []
        for player_record in raw_players:
            if not isinstance(player_record, dict) or "id" not in player_record:
                raise FPLAPIError("bootstrap-static contains an invalid player record")
            summary = self.fetch_player_summary(player_record["id"])
            players.append(
                self._parser.parse_player(
                    player_record,
                    summary,
                    team_names,
                    position_names,
                )
            )
        return players

    def load_snapshot(self, include_players: bool = False) -> FPLSnapshot:
        bootstrap = self.fetch_bootstrap()
        raw_gameweeks = bootstrap.get("events")
        if not isinstance(raw_gameweeks, list) or not all(
            isinstance(row, dict) for row in raw_gameweeks
        ):
            raise FPLAPIError("bootstrap-static contains invalid gameweek data")

        raw_teams = bootstrap.get("teams")
        if not isinstance(raw_teams, list) or not all(
            isinstance(row, dict) for row in raw_teams
        ):
            raise FPLAPIError("bootstrap-static contains invalid team data")

        raw_fixtures = self.fetch_fixtures()
        return FPLSnapshot(
            retrieved_at=datetime.now(UTC),
            gameweeks=self._parser.parse_gameweeks(raw_gameweeks),
            teams=self._parser.parse_teams(raw_teams),
            fixtures=self._parser.parse_fixtures(raw_fixtures),
            players=self.load_players(bootstrap) if include_players else [],
        )

    def load_full_snapshot(self) -> FPLSnapshot:
        """Load gameweeks, teams, fixtures and every player's histories."""

        return self.load_snapshot(include_players=True)

    def execute(self) -> FPLSnapshot:
        """Compatibility entry point; prefer ``load_snapshot`` in new code."""

        return self.load_snapshot()


# Temporary compatibility for code written against the original class name.
APIConnector = FPLAPIClient


if __name__ == "__main__":
    snapshot = FPLAPIClient().load_snapshot()
    print(
        f"Loaded {len(snapshot.gameweeks)} gameweeks, {len(snapshot.teams)} teams and "
        f"{len(snapshot.fixtures)} fixtures at {snapshot.retrieved_at.isoformat()}"
    )
