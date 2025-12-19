from __future__ import annotations
import random
import time
import threading
from enum import Enum, auto
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.ai.behavior_manager import BehaviorManager

# --- State Interfaces & Enums ---

class StateType(Enum):
    IDLE = auto()
    SPEAKING = auto()

class SpeakingSubStateType(Enum):
    GAME_RECOMMENDATION = auto()

class AIState(ABC):
    """Abstract base class for main states."""
    @abstractmethod
    def enter(self, manager: 'BehaviorManager'):
        pass
    
    @abstractmethod
    def update(self, manager: 'BehaviorManager') -> str:
        """Returns the animation state name (e.g., 'idle', 'walk')."""
        pass
    
    @abstractmethod
    def exit(self, manager: 'BehaviorManager'):
        pass

class AISubState(ABC):
    """Abstract base class for sub-states (e.g., specific speaking topics)."""
    @abstractmethod
    def execute(self, manager: 'BehaviorManager'):
        pass

# --- Concrete States ---

class IdleState(AIState):
    def enter(self, manager: 'BehaviorManager'):
        pass

    def update(self, manager: 'BehaviorManager') -> str:
        # Random transition logic
        # 期望每 5 分钟触发一次
        # 只有当距离上次推荐超过 1 分钟（避免连续触发）时才进行随机判定
        if time.time() - manager.last_recommend_time > 60:
            if random.random() < 0.00033: 
                manager.transition_to(StateType.SPEAKING)

        return "idle"

    def exit(self, manager: 'BehaviorManager'):
        pass

class SpeakingState(AIState):
    def __init__(self):
        self.current_sub_state_type = None
        self.timer = 0

    def enter(self, manager: 'BehaviorManager'):
        self.timer = 0
        self.current_sub_state_type = SpeakingSubStateType.GAME_RECOMMENDATION
        
        sub_state = manager.get_speaking_sub_state(self.current_sub_state_type)
        if sub_state:
            sub_state.execute(manager)

    def update(self, manager: 'BehaviorManager') -> str:
        self.timer += 1
        # Speak for a while then go back to idle
        if self.timer > 300: # 5 seconds at 60fps
            manager.transition_to(StateType.IDLE)
        return "speaking"

    def exit(self, manager: 'BehaviorManager'):
        self.current_sub_state_type = None

class GameRecommendationSubState(AISubState):
    def execute(self, manager: 'BehaviorManager'):
        if not manager.steam_manager or not manager.llm_service:
            return

        # Update last recommend time
        manager.last_recommend_time = time.time()

        # Start async task
        threading.Thread(target=self._run_async_task, args=(manager,), daemon=True).start()

    def _run_async_task(self, manager: 'BehaviorManager'):
        try:
            # 1. Pick a game
            game = self._pick_game(manager)
            if not game:
                return

            # 2. Get Game Info
            appid = game.get("appid")
            name = game.get("name", "Unknown")
            playtime_forever = game.get("playtime_forever", 0) / 60.0 # hours
            playtime_2weeks = game.get("playtime_2weeks", 0) / 60.0 # hours
            
            # 3. Get Description (using SteamClient via a temporary instance or helper)
            from src.feature_core.adapters.http.steam_client import SteamClient
            api_key = manager.steam_manager.config.get("steam_api_key")
            if not api_key:
                return
                
            client = SteamClient(api_key)
            app_info_map = client.get_apps_info([appid])
            app_info = app_info_map.get(str(appid), {})
            short_description = app_info.get("short_description", "")
            
            # 4. Construct Prompt
            prompt_content = manager.prompt_manager.get_prompt(
                "active_game_recommendation",
                game_name=name,
                appid=appid,
                playtime_forever=f"{playtime_forever:.1f}",
                playtime_2weeks=f"{playtime_2weeks:.1f}",
                description=short_description
            )
            
            messages = [{"role": "user", "content": prompt_content}]

            # 5. Call LLM Service
            response = manager.llm_service.chat_completion(messages)
            
            if response:
                manager.request_speech(response)
        except Exception as e:
            print(f"[GameRecommendation] Error in async task: {e}")

    def _pick_game(self, manager):
        # Access cache via SteamFacadeQt
        cache = manager.steam_manager.cache
        # Try to get primary games list
        games_cache = manager.steam_manager.query_service.get_primary_games_cache(cache, manager.steam_manager._policy().primary_id)
        
        if not games_cache or not games_cache.get("all_games"):
            return None
            
        all_games = games_cache["all_games"]
        if not all_games:
            return None

        # Sort lists
        recent_games = sorted([g for g in all_games if g.get("playtime_2weeks", 0) > 0], 
                              key=lambda x: x.get("playtime_2weeks", 0), reverse=True)
        
        top_games = sorted([g for g in all_games if g.get("playtime_forever", 0) > 0], 
                           key=lambda x: x.get("playtime_forever", 0), reverse=True)

        # Random Logic
        roll = random.random()
        
        target_game = None
        
        if roll < 0.4: # 40% Recent
            if recent_games:
                candidates = recent_games[:5]
                target_game = random.choice(candidates)
            else:
                target_game = random.choice(all_games)
                
        elif roll < 0.8: # 40% All Time (0.4 + 0.4)
            if top_games:
                candidates = top_games[:10]
                target_game = random.choice(candidates)
            else:
                target_game = random.choice(all_games)
                
        else: # 20% Random
            target_game = random.choice(all_games)
            
        return target_game
