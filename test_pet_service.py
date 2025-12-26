import os
import re
import sys
import unittest
import json

# Ensure repo root is in path so `import src.*` works
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from src.feature_core.services.steam.games_aggregation_service import SteamGamesAggregationService
from src.feature_core.services.pet_service import PetService
from src.storage.prompt_manager import PromptManager


class CapturingPromptManager:
    def __init__(self, real: PromptManager):
        self._real = real
        self.last_name = None
        self.last_kwargs = None

    def get_prompt(self, name: str, **kwargs):
        self.last_name = name
        self.last_kwargs = kwargs
        return self._real.get_prompt(name, **kwargs)


class MockSteamManager:
    def __init__(self, cache):
        self.cache = cache


class TestPetServiceBuildSayHelloPrompt(unittest.TestCase):
    def test_build_say_hello_prompt_with_real_cache(self):
        # 1) Load REAL cache from disk (avoid SteamRepository -> PyQt6 dependency)
        cache_path = os.path.join(current_dir, "config", "steam_data.json")
        self.assertTrue(os.path.exists(cache_path), f"Missing real steam cache file: {cache_path}")
        with open(cache_path, "r", encoding="utf-8") as f:
            cache = json.load(f)
        self.assertIsInstance(cache, dict)
        self.assertTrue(cache, "steam cache should not be empty")

        # 2) Mimic app startup behavior: ensure cache['games'] derived from games_accounts
        agg_service = SteamGamesAggregationService()
        agg_service.ensure_games_from_accounts(cache)

        steam_manager = MockSteamManager(cache)
        prompt_manager = CapturingPromptManager(PromptManager())
        pet_service = PetService()

        # 3) Execute
        prompt = pet_service.build_say_hello_prompt(prompt_manager, steam_manager)

        # Print prompt and kwargs for inspection
        print("\n[PetService] Generated prompt:\n" + str(prompt))
        print("\n[PetService] Prompt kwargs:")
        for k in sorted((prompt_manager.last_kwargs or {}).keys()):
            print(f"  - {k}: {prompt_manager.last_kwargs.get(k)}")

        # 4) Assert prompt manager was called correctly
        self.assertEqual(prompt_manager.last_name, "say_hello")
        self.assertIsInstance(prompt, str)
        self.assertTrue(len(prompt) > 0)

        # 5) Assert kwargs schema (keep it stable, avoid over-fitting to specific cache contents)
        kwargs = prompt_manager.last_kwargs
        self.assertIsInstance(kwargs, dict)

        expected_keys = {
            "current_datetime",
            "persona_name",
            "steam_level",
            "total_playtime_hours",
            "recent_games",
            "owned_games_count",
            "last_logoff",
            "time_created",
            "account_age_days",
        }
        self.assertTrue(expected_keys.issubset(set(kwargs.keys())))

        # current_datetime format: YYYY-MM-DD HH:MM
        self.assertRegex(kwargs["current_datetime"], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")

        # persona_name comes from cache summary if present
        summary = cache.get("summary") if isinstance(cache.get("summary"), dict) else {}
        if summary.get("personaname"):
            self.assertEqual(kwargs["persona_name"], summary.get("personaname"))

        # steam_level should be numeric string or '?'
        self.assertTrue(re.match(r"^(\d+|\?)$", str(kwargs["steam_level"])) is not None)

        # owned_games_count: prefer cache['games']['count'] when available
        games_total = cache.get("games") if isinstance(cache.get("games"), dict) else None
        if games_total and isinstance(games_total.get("count"), int) and games_total.get("count") > 0:
            self.assertEqual(kwargs["owned_games_count"], str(games_total.get("count")))

        # recent_games is now structured data; formatting is handled inside PromptManager
        self.assertIsInstance(kwargs["recent_games"], list)
        for row in kwargs["recent_games"]:
            self.assertIsInstance(row, dict)
            # Keep schema flexible: require at least a name when present
            if row:
                self.assertIn("name", row)

        # final prompt should have placeholders substituted
        self.assertNotIn("{recent_games}", prompt)
        self.assertIn("【最近玩过】", prompt)


if __name__ == "__main__":
    unittest.main()
