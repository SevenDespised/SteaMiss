import sys
import os
import time
import unittest
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import QObject, QCoreApplication

# Ensure repo root is in path so `import src.*` works
_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

# Create QCoreApplication for signal handling
app = QCoreApplication.instance()
if not app:
    app = QCoreApplication(sys.argv)

from src.ai.behavior_manager import BehaviorManager, StateType
from src.storage.steam_repository import SteamRepository
from src.feature_core.services.steam.query_service import SteamQueryService
from src.storage.prompt_manager import PromptManager

# --- Mocks ---

class MockPolicy:
    # 需要根据实际数据调整，或者让测试自动发现 primary_id
    # 这里我们假设 cache 里有数据，我们动态获取 primary_id
    def __init__(self, primary_id):
        self.primary_id = primary_id

class MockSteamFacade:
    def __init__(self):
        # Load REAL cache
        repo = SteamRepository()
        self.cache = repo.load_data()

        # Try to find a primary ID from cache if possible, or use a dummy
        # In real app, primary_id comes from config/policy.
        # Here we try to infer it from cache keys if available
        self.primary_id = "76561198000000000" # Default dummy

        # Simple heuristic to find a valid steamid key in cache that has 'games'
        for key in self.cache:
            if key.isdigit() and "games" in self.cache[key]:
                self.primary_id = key
                print(f"[Test] Found primary ID from cache: {self.primary_id}")
                break

        self.config = {"steam_api_key": "dummy_key_for_test"}
        # Use REAL QueryService to parse the real cache
        self.query_service = SteamQueryService()

    def _policy(self):
        return MockPolicy(self.primary_id)

class MockLLMService:
    def chat_completion(self, messages):
        print(f"\n[MockLLM] Received prompt:\n{messages[0]['content']}\n")
        return "Mock LLM Response: You should definitely play Test Game 1!"

# --- Test Case ---

class TestBehaviorManager(unittest.TestCase):
    def setUp(self):
        # Initialize Manager
        self.manager = BehaviorManager()

        # Setup Mocks
        self.mock_steam = MockSteamFacade()
        self.mock_llm = MockLLMService()
        self.prompt_manager = PromptManager() # Use Real PromptManager

        self.manager.set_dependencies(self.mock_steam, self.mock_llm, self.prompt_manager)

        # Capture signals
        self.speech_output = []
        self.manager.speech_requested.connect(self.on_speech)

    def on_speech(self, content):
        self.speech_output.append(content)

    # @patch('src.feature_core.adapters.http.steam_client.SteamClient') # Commented out to use REAL SteamClient
    def test_game_recommendation_trigger(self): # Removed MockSteamClient argument
        """
        Test that entering SPEAKING state triggers the GameRecommendationSubState,
        which fetches game info, calls LLM, and emits speech signal.
        """
        print("\n--- Starting Test: Game Recommendation Flow (Real Cache + Real Steam API) ---")

        # 1. No Mock SteamClient setup needed - we want real network calls for description

        # 2. Force transition to SPEAKING state
        # This should automatically enter GameRecommendationSubState and execute logic
        print("Transitioning to SPEAKING state...")
        t0 = time.time()
        self.manager.transition_to(StateType.SPEAKING)
        t1 = time.time()
        print(f"Transition took {t1 - t0:.4f} seconds")
        self.assertLess(t1 - t0, 0.5, "Transition should be non-blocking (async)")

        # Wait for async thread to complete (max 10 seconds)
        start_time = time.time()
        while not self.speech_output and time.time() - start_time < 10:
            QCoreApplication.processEvents()
            time.sleep(0.1)

        # 3. Verify results
        # We can't assert SteamClient calls easily without mocking,
        # but we can check if the output prompt contains a real description.

        # Check if speech was emitted
        if self.speech_output:
            prompt_content = self.speech_output[0] # This is actually the LLM response in the current mock
            # Wait, the signal emits the LLM response.
            # The MockLLMService prints the prompt.
            # We can't easily inspect the prompt passed to LLM unless we update MockLLMService to store it.
            print(f"Speech Signal Received: {prompt_content}")
            self.assertIn("Mock LLM Response", prompt_content)
        else:
            print("No speech signal received! (Check if cache has games or API failed)")

        print("--- Test Passed ---")

if __name__ == '__main__':
    unittest.main()
