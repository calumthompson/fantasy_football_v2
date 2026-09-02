from domain.models import (
    BootstrapDataRaw,
    Fixture,
    FPLSnapshot,
    GameWeek,
    Manager,
    ManagerTeamPicks,
    Player,
    PlayerFixturePerformance,
    PlayerPerformanceStats,
    PlayerSeasonPerformance,
    Team,
)
from integrations.fpl_api.api_handler import (
    FPLAPIClient,
    FPLAPIError,
    FPLParser,
)

__all__ = [
    "BootstrapDataRaw",
    "FPLAPIClient",
    "FPLAPIError",
    "FPLParser",
    "FPLSnapshot",
    "Fixture",
    "GameWeek",
    "Manager",
    "ManagerTeamPicks",
    "Player",
    "PlayerFixturePerformance",
    "PlayerPerformanceStats",
    "PlayerSeasonPerformance",
    "Team",
]


if __name__ == "__main__":

    import sys

    from loguru import logger

    logger.remove()
    logger.add(sys.stderr, level="INFO")

    client = FPLAPIClient(manager_id=9836874)

    snapshot = client.load_snapshot()

# %%
