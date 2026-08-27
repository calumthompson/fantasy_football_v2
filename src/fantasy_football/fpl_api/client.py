"""HTTP client for the public Fantasy Premier League API."""

import json
from typing import Any, Dict
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import ValidationError

from .errors import FPLTransportError, FPLValidationError
from .models import BootstrapData


class FPLClient:
    """Download and validate public FPL data."""

    def __init__(
        self,
        base_url: str = "https://fantasy.premierleague.com/api",
        timeout: float = 15.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_bootstrap_data(self) -> BootstrapData:
        """Fetch the core players, teams and gameweeks dataset."""
        payload = self._get_json("bootstrap-static/")
        try:
            return BootstrapData.model_validate(payload)
        except ValidationError as exc:
            raise FPLValidationError(
                "bootstrap-static response did not match the expected schema:\n"
                f"{exc}"
            ) from exc

    def _get_json(self, path: str) -> Dict[str, Any]:
        request = Request(
            f"{self.base_url}/{path.lstrip('/')}",
            headers={"Accept": "application/json", "User-Agent": "fantasy-football/0.1"},
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.load(response)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise FPLTransportError(f"Could not fetch {request.full_url}: {exc}") from exc

        if not isinstance(payload, dict):
            raise FPLTransportError(
                f"Expected a JSON object from {request.full_url}, got {type(payload).__name__}"
            )
        return payload

