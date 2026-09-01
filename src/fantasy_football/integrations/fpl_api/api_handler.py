from datetime import UTC, datetime
from typing import Any

import requests
from loguru import logger
from pydantic import ValidationError
from tqdm import tqdm

from fantasy_football.domain.models import (
    BootstrapDataRaw,
    Fixture,
    FPLSnapshot,
    GameWeek,
    Manager,
    ManagerTeamPicks,
    Player,
    PlayerFixturePerformance,
    PlayerSeasonPerformance,
    Team,
)

_API_ADDRESS = "https://fantasy.premierleague.com/api"

_BOOTSTRAP_STATIC_URL = "{api_address}/bootstrap-static/"
_FIXTURE_DATA_URL = "{api_address}/fixtures/"
_PLAYER_DATA_URL = "{api_address}/element-summary/{player_id}/"

_MANAGER_URL = "{api_address}/entry/{manager_id}/"
_MANAGER_TEAM_URL = "{api_address}/entry/{manager_id}/event/{gameweek}/picks"


class FPLAPIError(RuntimeError):
    """Raised when FPL data cannot be downloaded or parsed."""

    def __init__(self, message: str) -> None:
        logger.error(message)
        super().__init__(message)


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
    def parse_position_names(records: list[dict[str, Any]]) -> dict[int, str]:
        try:
            return {record["id"]: record["singular_name_short"] for record in records}
        except (KeyError, TypeError) as error:
            raise FPLAPIError(f"Unable to parse FPL position data: {error}") from error

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
                    expected_goal_involvements=record["expected_goal_involvements"],
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
            clearances_blocks_interceptions=record["clearances_blocks_interceptions"],
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
                    away_team_difficulty=record["team_a_difficulty"],
                    home_team_difficulty=record["team_h_difficulty"],
                )
                for record in records
            ]
        except (KeyError, TypeError, ValidationError) as error:
            raise FPLAPIError(f"Unable to parse FPL fixture data: {error}") from error

    @staticmethod
    def parse_manager(record: dict[str, Any]) -> Manager:
        try:
            return Manager(
                manager_id=record["id"],
                most_recent_gameweek=record["current_event"],
                current_points=record["summary_overall_points"],
            )
        except (KeyError, TypeError, ValidationError) as error:
            raise FPLAPIError(f"Unable to parse FPL manager data: {error}") from error

    @staticmethod
    def parse_manager_team_picks(record: dict[str, Any]) -> ManagerTeamPicks:
        try:
            picks = record["picks"]
            if not isinstance(picks, list) or not all(
                isinstance(pick, dict) for pick in picks
            ):
                raise TypeError("picks must be a list of records")

            captain_ids = [pick["element"] for pick in picks if pick["is_captain"]]
            vice_captain_ids = [
                pick["element"] for pick in picks if pick["is_vice_captain"]
            ]
            if len(captain_ids) != 1:
                raise ValueError("manager picks must contain exactly one captain")
            if len(vice_captain_ids) != 1:
                raise ValueError("manager picks must contain exactly one vice-captain")

            return ManagerTeamPicks(
                selected_player_ids=[pick["element"] for pick in picks],
                captain_player_id=captain_ids[0],
                vice_captain_player_id=vice_captain_ids[0],
            )
        except (KeyError, TypeError, ValueError, ValidationError) as error:
            raise FPLAPIError(
                f"Unable to parse FPL manager team picks: {error}"
            ) from error


class FPLAPIClient:
    """Download FPL API data and return validated objects."""

    def __init__(
        self,
        manager_id: int,
        timeout: float = 15.0,
        session: requests.Session | None = None,
        parser: FPLParser | None = None,
    ) -> None:
        self._timeout = timeout
        self._session = session or requests.Session()
        self._parser = parser or FPLParser()
        self.manager_id = manager_id

    def _get_json(self, url: str) -> Any:
        try:
            response = self._session.get(url, timeout=self._timeout)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as error:
            raise FPLAPIError(
                f"Failed to load FPL API data from {url}: {error}"
            ) from error

    def fetch_bootstrap(self) -> BootstrapDataRaw:
        data = self._get_json(_BOOTSTRAP_STATIC_URL.format(api_address=_API_ADDRESS))
        try:
            bootstrap = BootstrapDataRaw.model_validate(data)
        except ValidationError as error:
            raise FPLAPIError(f"Invalid FPL bootstrap data: {error}") from error
        logger.info("Loaded FPL bootstrap data")
        return bootstrap

    def fetch_fixtures(self) -> list[dict[str, Any]]:
        data = self._get_json(_FIXTURE_DATA_URL.format(api_address=_API_ADDRESS))
        if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
            raise FPLAPIError("fixtures returned an unexpected response shape")
        logger.info("Loaded {} FPL fixtures", len(data))
        return data

    def fetch_player_summary(self, player_id: int) -> dict[str, Any]:
        data = self._get_json(
            _PLAYER_DATA_URL.format(api_address=_API_ADDRESS, player_id=player_id)
        )
        if not isinstance(data, dict):
            raise FPLAPIError(
                f"element-summary for player {player_id} returned an unexpected response shape"
            )
        return data

    def fetch_manager_data(self) -> dict[str, Any]:
        data = self._get_json(
            _MANAGER_URL.format(api_address=_API_ADDRESS, manager_id=self.manager_id)
        )
        if not isinstance(data, dict):
            raise FPLAPIError(
                f"Error loading manager data for manager {self.manager_id}"
            )
        return data

    def fetch_manager_team_data(self, gameweek: int) -> dict[str, Any]:
        data = self._get_json(
            _MANAGER_TEAM_URL.format(
                api_address=_API_ADDRESS, manager_id=self.manager_id, gameweek=gameweek
            )
        )
        if not isinstance(data, dict):
            raise FPLAPIError(
                f"Error loading team data for manager {self.manager_id} gameweek {gameweek}"
            )
        return data

    def _load_players(
        self,
        bootstrap_elements: list[dict[str, Any]],
        teams: list[Team],
        position_names: dict[int, str],
    ) -> list[Player]:
        """Load every player with current and most recent completed-season history."""

        team_names = {team.team_season_id: team.name for team in teams}

        players: list[Player] = []
        for player_record in tqdm(
            bootstrap_elements, desc="Loading FPL players", unit="player"
        ):
            if not isinstance(player_record, dict) or "id" not in player_record:
                raise FPLAPIError("bootstrap-static contains an invalid player record")

            summary = self.fetch_player_summary(player_record["id"])

            player = self._parser.parse_player(
                player_record,
                summary,
                team_names,
                position_names,
            )

            players.append(player)
            logger.debug("Loaded player data for {}", player.web_name)
        return players

    def load_snapshot(self) -> FPLSnapshot:

        started_at = datetime.now(UTC)

        # Load and parse bootstrap data
        bootstrap = self.fetch_bootstrap()
        teams = self._parser.parse_teams(bootstrap.teams)
        gameweeks = self._parser.parse_gameweeks(bootstrap.events)
        position_names = self._parser.parse_position_names(bootstrap.element_types)

        # Load and parse fixture data
        raw_fixtures = self.fetch_fixtures()
        fixtures = self._parser.parse_fixtures(raw_fixtures)

        # Load and parse player performance data
        players = self._load_players(
            bootstrap.elements,
            teams,
            position_names,
        )

        # Load manager data
        manager = self._parser.parse_manager(self.fetch_manager_data())

        # Load ids of the managers current team
        manager_team_picks = self._parser.parse_manager_team_picks(
            self.fetch_manager_team_data(manager.most_recent_gameweek)
        )

        retrieved_at = datetime.now(UTC)
        time_to_complete = retrieved_at - started_at

        logger.info(f"FPL data pulled from API in {time_to_complete.seconds}s")

        return FPLSnapshot(
            started_at=started_at,
            retrieved_at=datetime.now(UTC),
            time_to_complete=time_to_complete,
            gameweeks=gameweeks,
            teams=teams,
            fixtures=fixtures,
            players=players,
            manager=manager,
            current_manager_team_picks=manager_team_picks,
        )
