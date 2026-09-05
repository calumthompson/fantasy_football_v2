import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.components.my_team.current_team import _forecast_points_by_gameweek
from integrations.fpl_api.api_handler import FPLParser
from optimiser import _forecast_player_points


class PlayerAvailabilityTests(unittest.TestCase):
    def test_api_status_mapping_and_nullable_chance(self):
        bootstrap = json.loads(
            (Path(__file__).resolve().parents[1]
             / "src/integrations/fpl_api/examples/bootstrap-static.json").read_text()
        )
        record = bootstrap["elements"][0]
        for code, label in (
            ("a", "Available"), ("d", "Doubtful"), ("i", "Injured"),
            ("s", "Suspended"), ("u", "Unavailable"),
            ("n", "Not available"), ("new", "Unknown"), (None, "Unknown"),
        ):
            for chance in (None, 0, 25, 50, 75, 100):
                with self.subTest(code=code, chance=chance):
                    player = FPLParser.parse_player(
                        {**record, "status": code, "chance_of_playing_next_round": chance},
                        {"history": [], "history_past": [], "fixtures": []},
                        {record["team"]: "Test team"},
                        {record["element_type"]: "GKP"},
                        {},
                    )
                    self.assertEqual(player.status, label)
                    self.assertEqual(player.chance_of_playing_next_round, chance)
                    self.assertEqual(type(player).model_validate(player.model_dump()), player)

    def test_views_and_optimiser_apply_setting_once_across_gameweeks(self):
        fixtures = [
            SimpleNamespace(fixture_id=1, gameweek_number=2),
            SimpleNamespace(fixture_id=2, gameweek_number=2),
            SimpleNamespace(fixture_id=3, gameweek_number=3),
            SimpleNamespace(fixture_id=4, gameweek_number=3),
        ]
        lookup = {(1, 1): 4.0, (1, 2): 6.0, (1, 3): 8.0}
        predictions = SimpleNamespace(results=[
            SimpleNamespace(player_id=p, fixture_id=f, predicted_points=score)
            for (p, f), score in lookup.items()
        ])
        for status in ("Available", "Doubtful", "Injured", "Suspended", "Unavailable", "Not available", "Unknown"):
            player = SimpleNamespace(player_id=1, status=status, upcoming_fixtures=fixtures)
            for setting in (0.0, 0.25, 1.0):
                with self.subTest(status=status, setting=setting), patch(
                    "settings.UNAVAILABLE_PLAYER_FORECAST_MULTIPLIER", setting
                ):
                    factor = 1.0 if status == "Available" else setting
                    self.assertEqual(
                        _forecast_points_by_gameweek(player, [2, 3, 4], lookup),
                        {2: 10.0 * factor, 3: 8.0 * factor, 4: 0.0},
                    )
                    self.assertEqual(
                        _forecast_player_points(SimpleNamespace(players=[player]), predictions, {2, 3}),
                        {1: 18.0 * factor},
                    )


if __name__ == "__main__":
    unittest.main()
