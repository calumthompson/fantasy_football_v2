"""Apply the current availability policy to forecast scores."""

import settings


def adjust_for_availability(score: float, status: str) -> float:
    multiplier = (
        1.0
        if status == "Available"
        else settings.UNAVAILABLE_PLAYER_FORECAST_MULTIPLIER
    )
    return score * multiplier
