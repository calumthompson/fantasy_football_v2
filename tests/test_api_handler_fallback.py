"""Tests for the FPL API example-response fallback."""

import unittest
from pathlib import Path
from unittest.mock import Mock

import requests

from fantasy_football.fpl_api.api_handler import FPLAPIClient, FPLAPIError


EXAMPLE_DIR = (
    Path(__file__).parents[1] / "fantasy_football" / "fpl_api" / "examples"
)


class FPLAPIClientFallbackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.session = Mock()
        self.session.get.side_effect = requests.ConnectionError("API unavailable")
        self.client = FPLAPIClient(
            session=self.session,
            example_dir=EXAMPLE_DIR,
        )

    def test_bootstrap_uses_example_when_api_is_unavailable(self) -> None:
        with self.assertWarnsRegex(RuntimeWarning, "using example response"):
            data = self.client.fetch_bootstrap()

        self.assertIn("elements", data)
        self.assertIn("teams", data)

    def test_fixtures_use_example_when_api_is_unavailable(self) -> None:
        with self.assertWarnsRegex(RuntimeWarning, "using example response"):
            data = self.client.fetch_fixtures()

        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_player_summary_uses_matching_player_example(self) -> None:
        with self.assertWarnsRegex(RuntimeWarning, "element-summary-1.json"):
            data = self.client.fetch_player_summary(1)

        self.assertIn("history", data)
        self.assertIn("history_past", data)

    def test_missing_player_example_raises_clear_error(self) -> None:
        with self.assertRaisesRegex(FPLAPIError, "element-summary-999999.json"):
            self.client.fetch_player_summary(999999)


if __name__ == "__main__":
    unittest.main()
