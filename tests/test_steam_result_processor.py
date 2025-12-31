import os
import sys
import unittest

# Ensure repo root is in path so `import src.*` works
_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from src.feature_core.services.steam.games_aggregator import GamesAggregator
from src.feature_core.services.steam.games_aggregation_service import SteamGamesAggregationService
from src.feature_core.services.steam.profile_service import SteamProfileService
from src.feature_core.services.steam.price_service import SteamPriceService
from src.feature_core.services.steam.wishlist_service import SteamWishlistService
from src.feature_core.services.steam.achievement_service import SteamAchievementService
from src.feature_core.services.steam.steam_result_processor import (
    EmitError,
    EmitGamesStats,
    EmitPlayerSummary,
    SaveStep,
    SteamResultProcessor,
)


def _game_payload(appid: int = 1, *, minutes: int = 10) -> dict:
    return {
        "all_games": [
            {
                "appid": appid,
                "name": f"Game-{appid}",
                "playtime_forever": minutes,
                "playtime_2weeks": 0,
                "rtime_last_played": 1,
            }
        ]
    }


class TestSteamResultProcessor(unittest.TestCase):
    def setUp(self) -> None:
        self.cache = {}
        self.aggregator = GamesAggregator()
        self.primary_id = "A"

        self.processor = SteamResultProcessor(
            cache=self.cache,
            games_aggregator=self.aggregator,
            get_primary_id=lambda: self.primary_id,
            games_aggregation_service=SteamGamesAggregationService(),
            profile_service=SteamProfileService(),
            price_service=SteamPriceService(),
            wishlist_service=SteamWishlistService(),
            achievement_service=SteamAchievementService(),
        )

    def test_summary_emits_then_saves(self):
        result = {"type": "summary", "data": {"personaname": "p"}}
        outcome = self.processor.process(result)

        self.assertEqual(len(outcome.steps), 2)
        self.assertIsInstance(outcome.steps[0], EmitPlayerSummary)
        self.assertIsInstance(outcome.steps[1], SaveStep)
        self.assertEqual(outcome.steps[1].reason, "after_task")
        self.assertEqual(self.cache.get("summary", {}).get("personaname"), "p")

    def test_profile_and_games_finalizes_and_saves_twice_like_old_logic(self):
        # begin aggregation for two accounts
        self.aggregator.begin(["A", "B"], "A")

        # First account result -> not done yet: only after_task save
        r1 = {
            "type": "profile_and_games",
            "steam_id": "A",
            "data": {"games": _game_payload(1), "summary": {"personaname": "p"}},
        }
        o1 = self.processor.process(r1)
        self.assertEqual([type(s) for s in o1.steps], [SaveStep])
        self.assertEqual(o1.steps[0].reason, "after_task")

        # Second account result -> done: finalize emits + finalize save + after_task save
        r2 = {
            "type": "profile_and_games",
            "steam_id": "B",
            "data": {"games": _game_payload(2), "summary": {"personaname": "q"}},
        }
        o2 = self.processor.process(r2)

        self.assertGreaterEqual(len(o2.steps), 4)
        self.assertIsInstance(o2.steps[0], EmitPlayerSummary)
        self.assertIsInstance(o2.steps[1], EmitGamesStats)
        self.assertIsInstance(o2.steps[2], SaveStep)
        self.assertEqual(o2.steps[2].reason, "finalize")
        self.assertIsInstance(o2.steps[-1], SaveStep)
        self.assertEqual(o2.steps[-1].reason, "after_task")

        # cache should now have aggregated games derived from games_accounts
        self.assertIn("games_accounts", self.cache)
        self.assertIn("games", self.cache)
        self.assertIsInstance(self.cache.get("games", {}).get("all_games"), list)

    def test_error_finalizes_then_emits_error_and_no_after_task_save(self):
        # begin aggregation for two accounts
        self.aggregator.begin(["A", "B"], "A")

        # First succeeds
        r1 = {
            "type": "profile_and_games",
            "steam_id": "A",
            "data": {"games": _game_payload(1), "summary": {"personaname": "p"}},
        }
        self.processor.process(r1)

        # Second fails -> mark_error triggers finalize, then error, and returns early (no after_task save)
        r2 = {"type": "profile_and_games", "steam_id": "B", "error": "boom"}
        o2 = self.processor.process(r2)

        # Expected order: player_summary, games_stats, finalize save, error
        kinds = []
        for step in o2.steps:
            if isinstance(step, SaveStep):
                kinds.append(f"save:{step.reason}")
            else:
                kinds.append(type(step).__name__)

        self.assertEqual(kinds[-1], "EmitError")
        self.assertNotIn("save:after_task", kinds)
        self.assertIn("save:finalize", kinds)

        # and the last step is actually EmitError
        self.assertIsInstance(o2.steps[-1], EmitError)

    def test_data_none_produces_no_steps(self):
        result = {"type": "summary", "data": None}
        outcome = self.processor.process(result)
        self.assertEqual(outcome.steps, [])


if __name__ == "__main__":
    unittest.main()
