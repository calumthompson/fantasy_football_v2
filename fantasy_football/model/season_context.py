"""Season-specific facts that are known before the season starts."""


PROMOTED_TEAMS_BY_SEASON: dict[str, frozenset[str]] = {
    "2025-26": frozenset({"Burnley", "Leeds", "Sunderland"}),
}


def get_promoted_teams(season: str) -> frozenset[str]:
    """Return the configured promoted clubs for a Premier League season."""
    try:
        return PROMOTED_TEAMS_BY_SEASON[season]
    except KeyError as error:
        raise ValueError(
            f"Promoted teams have not been configured for season {season!r}."
        ) from error
