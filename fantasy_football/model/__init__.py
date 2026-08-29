from typing import Any


def predict_upcoming_fixtures_from_fpl(*args: Any, **kwargs: Any) -> Any:
    """Load and invoke the live fixture prediction pipeline."""
    from fantasy_football.model.prediction_pipeline import (
        predict_upcoming_fixtures_from_fpl as _predict,
    )

    return _predict(*args, **kwargs)

__all__ = ["predict_upcoming_fixtures_from_fpl"]
