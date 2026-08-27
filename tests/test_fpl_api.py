"""Tests for strict FPL response validation."""

import copy
import json
import unittest
from pathlib import Path

from pydantic import ValidationError

from fantasy_football.fpl_api.models import BootstrapData


FIXTURE = Path(__file__).parent / "fixtures" / "bootstrap-static.json"


class BootstrapDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with FIXTURE.open(encoding="utf-8") as fixture:
            cls.payload = json.load(fixture)

    def test_response_is_stored_as_typed_objects(self) -> None:
        data = BootstrapData.model_validate(self.payload)

        self.assertEqual(data.elements[0].web_name, "Raya")
        self.assertEqual(data.elements[0].price, 6.0)
        self.assertEqual(data.teams[0].name, "Arsenal")

    def test_wrong_field_type_is_rejected(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["elements"][0]["now_cost"] = "60"

        with self.assertRaises(ValidationError) as error:
            BootstrapData.model_validate(payload)

        self.assertIn("elements.0.now_cost", str(error.exception))

    def test_unknown_field_is_rejected(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["elements"][0]["undocumented_field"] = 1

        with self.assertRaises(ValidationError):
            BootstrapData.model_validate(payload)


if __name__ == "__main__":
    unittest.main()
