from __future__ import annotations
import json
import logging
import os
import random
import time
import threading
import uuid
from enum import Enum, auto
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.ai.behavior_manager import BehaviorManager


logger = logging.getLogger(__name__)

# --- State Interfaces & Enums ---

class StateType(Enum):
    IDLE = auto()
    SPEAKING = auto()

class SpeakingSubStateType(Enum):
    GAME_RECOMMENDATION = auto()
    NEWS_PUSH = auto()
    FREE_GAME_PUSH = auto()
    DISCOUNT_PUSH = auto()

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

    def is_available(self, manager: 'BehaviorManager') -> bool:
        """Optional availability check.

        SpeakingState 会在 enter 时优先筛选可用子状态；默认认为可用。
        子状态如需“只在缓存存在时触发”，可覆盖本方法。
        """
        return True

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
        self.current_sub_state_type = None

        # 从已注册的子状态中随机挑选（不在 SpeakingState 内写死具体子状态）
        candidates: list[SpeakingSubStateType] = []
        try:
            items = list(getattr(manager, "_speaking_sub_states", {}).items())
        except Exception:
            items = []

        for sub_state_type, sub_state in items:
            try:
                is_available = getattr(sub_state, "is_available", None)
                if callable(is_available) and not bool(is_available(manager)):
                    continue
                candidates.append(sub_state_type)
            except Exception:
                # 子状态可用性判断失败则视为不可用，避免说话逻辑崩溃
                continue

        if not candidates:
            manager.transition_to(StateType.IDLE)
            return

        self.current_sub_state_type = random.choice(candidates)
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
        # 互动上下文由“气泡显示/隐藏”驱动，不在这里强制清理

class GameRecommendationSubState(AISubState):
    def execute(self, manager: 'BehaviorManager'):
        if not manager.steam_manager or not manager.llm_service or not manager.prompt_manager:
            return

        # Update last recommend time
        manager.last_recommend_time = time.time()

        # 取消上一条推荐的流式输出（如果有）
        prev_request_id = getattr(manager, "_active_game_recommendation_request_id", None)
        if isinstance(prev_request_id, str) and prev_request_id:
            manager.request_speech_stream_done(prev_request_id)

        request_id = uuid.uuid4().hex
        manager._active_game_recommendation_request_id = request_id

        # Start async task
        threading.Thread(target=self._run_async_task, args=(manager, request_id), daemon=True).start()

    def _run_async_task(self, manager: 'BehaviorManager', request_id: str):
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

            # 5. Stream LLM Service
            if getattr(manager, "_active_game_recommendation_request_id", None) != request_id:
                return

            # 以气泡显示为起点：仅在确定要显示气泡时，才设置推荐状态与互动上下文
            manager.current_recommended_game = game

            name_for_menu = name
            if len(name_for_menu) > 6:
                name_for_menu = name_for_menu[:6] + "..."

            interaction_context = {
                "label": f"启动：\n{name_for_menu}",
                "action": "launch_game",
                "kwargs": {"appid": appid},
            }

            manager.request_speech_stream_started(request_id, interaction_context=interaction_context)

            try:
                for delta in manager.llm_service.stream_chat_completion(messages):
                    if getattr(manager, "_active_game_recommendation_request_id", None) != request_id:
                        return
                    if not isinstance(delta, str) or not delta:
                        continue
                    manager.request_speech_stream_delta(request_id, delta)
            finally:
                if getattr(manager, "_active_game_recommendation_request_id", None) == request_id:
                    manager.request_speech_stream_done(request_id)
        except Exception as e:
            logger.exception("[GameRecommendation] Error in async task")
            raise

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


class NewsPushSubState(AISubState):
    """新闻推送：仅使用本地缓存（config/news_data.json），无缓存则不可用。"""

    _CACHE_PATH = os.path.join("config", "news_data.json")

    def is_available(self, manager: 'BehaviorManager') -> bool:
        items = self._load_cached_items()
        return bool(items)

    def execute(self, manager: 'BehaviorManager'):
        if not manager.llm_service or not manager.prompt_manager:
            return

        items = self._load_cached_items()
        if not items:
            return

        manager.last_recommend_time = time.time()

        prev_request_id = getattr(manager, "_active_news_push_request_id", None)
        if isinstance(prev_request_id, str) and prev_request_id:
            manager.request_speech_stream_done(prev_request_id)

        request_id = uuid.uuid4().hex
        manager._active_news_push_request_id = request_id

        threading.Thread(target=self._run_async_task, args=(manager, request_id, items), daemon=True).start()

    def _run_async_task(self, manager: 'BehaviorManager', request_id: str, items: list[dict]):
        try:
            if getattr(manager, "_active_news_push_request_id", None) != request_id:
                return

            text_items = self._format_items(items)
            prompt_content = manager.prompt_manager.get_prompt(
                "active_news_push",
                items=text_items,
            )
            messages = [{"role": "user", "content": prompt_content}]

            manager.request_speech_stream_started(request_id, interaction_context=None)
            try:
                for delta in manager.llm_service.stream_chat_completion(messages):
                    if getattr(manager, "_active_news_push_request_id", None) != request_id:
                        return
                    if not isinstance(delta, str) or not delta:
                        continue
                    manager.request_speech_stream_delta(request_id, delta)
            finally:
                if getattr(manager, "_active_news_push_request_id", None) == request_id:
                    manager.request_speech_stream_done(request_id)
        except Exception:
            logger.exception("[NewsPush] Error in async task")

    def _load_cached_items(self) -> list[dict]:
        try:
            if not os.path.exists(self._CACHE_PATH):
                return []
            with open(self._CACHE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return []
            items = data.get("items")
            if not isinstance(items, list):
                return []
            out: list[dict] = []
            for it in items:
                if isinstance(it, dict):
                    out.append(it)
            return out
        except Exception:
            return []

    def _format_items(self, items: list[dict], *, limit: int = 5) -> str:
        rows: list[str] = []
        for it in items[: int(limit or 0)]:
            title = str(it.get("title") or "").strip()
            source = str(it.get("source") or "").strip()
            link = str(it.get("link") or "").strip()
            if not title:
                continue
            parts = [f"- {title}"]
            if source:
                parts.append(f"（{source}）")
            if link:
                parts.append(f"{link}")
            rows.append(" ".join(parts))
        return "\n".join(rows)


class FreeGamePushSubState(AISubState):
    """免费游戏推送：仅使用 game data cache 中的 free_game 缓存。"""

    def is_available(self, manager: 'BehaviorManager') -> bool:
        return bool(self._get_cached_items(manager))

    def execute(self, manager: 'BehaviorManager'):
        if not manager.steam_manager or not manager.llm_service or not manager.prompt_manager:
            return

        items = self._get_cached_items(manager)
        if not items:
            return

        manager.last_recommend_time = time.time()

        prev_request_id = getattr(manager, "_active_free_game_push_request_id", None)
        if isinstance(prev_request_id, str) and prev_request_id:
            manager.request_speech_stream_done(prev_request_id)

        request_id = uuid.uuid4().hex
        manager._active_free_game_push_request_id = request_id

        threading.Thread(target=self._run_async_task, args=(manager, request_id, items), daemon=True).start()

    def _run_async_task(self, manager: 'BehaviorManager', request_id: str, items: list[dict]):
        try:
            if getattr(manager, "_active_free_game_push_request_id", None) != request_id:
                return

            text_items = self._format_items(items)
            prompt_content = manager.prompt_manager.get_prompt(
                "active_free_game_push",
                items=text_items,
            )
            messages = [{"role": "user", "content": prompt_content}]

            manager.request_speech_stream_started(request_id, interaction_context=None)
            try:
                for delta in manager.llm_service.stream_chat_completion(messages):
                    if getattr(manager, "_active_free_game_push_request_id", None) != request_id:
                        return
                    if not isinstance(delta, str) or not delta:
                        continue
                    manager.request_speech_stream_delta(request_id, delta)
            finally:
                if getattr(manager, "_active_free_game_push_request_id", None) == request_id:
                    manager.request_speech_stream_done(request_id)
        except Exception:
            logger.exception("[FreeGamePush] Error in async task")

    def _get_cached_items(self, manager: 'BehaviorManager') -> list[dict]:
        try:
            cache = getattr(manager.steam_manager, "cache", None)
            if not isinstance(cache, dict):
                return []

            payload = cache.get("free_game")
            if not isinstance(payload, dict):
                return []

            items = payload.get("items")
            if not isinstance(items, list):
                return []
            return [it for it in items if isinstance(it, dict)]
        except Exception:
            return []

    def _format_items(self, items: list[dict], *, limit: int = 6) -> str:
        # EpicService.build_info_window_items 会混入 header 行；这里做轻量筛选
        rows: list[str] = []
        for it in items:
            title = str(it.get("title") or "").strip()
            url = it.get("url")
            period = str(it.get("period") or "").strip()
            if not title:
                continue
            # 跳过统计/分组 header（通常 period 为空且 url 为 None）
            if url is None and ("当前免费" in title or "即将免费" in title or "统计：" in title):
                continue
            line = f"- {title}"
            if period:
                line += f"（{period}）"
            if isinstance(url, str) and url:
                line += f" {url}"
            rows.append(line)
            if len(rows) >= int(limit or 0):
                break
        return "\n".join(rows)


class DiscountPushSubState(AISubState):
    """折扣推送：仅使用 steam_manager.cache['wishlist']（折扣列表缓存），无缓存则不可用。"""

    def is_available(self, manager: 'BehaviorManager') -> bool:
        return bool(self._get_discount_items(manager))

    def execute(self, manager: 'BehaviorManager'):
        if not manager.steam_manager or not manager.llm_service or not manager.prompt_manager:
            return

        items = self._get_discount_items(manager)
        if not items:
            return

        manager.last_recommend_time = time.time()

        prev_request_id = getattr(manager, "_active_discount_push_request_id", None)
        if isinstance(prev_request_id, str) and prev_request_id:
            manager.request_speech_stream_done(prev_request_id)

        request_id = uuid.uuid4().hex
        manager._active_discount_push_request_id = request_id

        threading.Thread(target=self._run_async_task, args=(manager, request_id, items), daemon=True).start()

    def _run_async_task(self, manager: 'BehaviorManager', request_id: str, items: list[dict]):
        try:
            if getattr(manager, "_active_discount_push_request_id", None) != request_id:
                return

            text_items = self._format_items(items)
            prompt_content = manager.prompt_manager.get_prompt(
                "active_discount_push",
                items=text_items,
            )
            messages = [{"role": "user", "content": prompt_content}]

            manager.request_speech_stream_started(request_id, interaction_context=None)
            try:
                for delta in manager.llm_service.stream_chat_completion(messages):
                    if getattr(manager, "_active_discount_push_request_id", None) != request_id:
                        return
                    if not isinstance(delta, str) or not delta:
                        continue
                    manager.request_speech_stream_delta(request_id, delta)
            finally:
                if getattr(manager, "_active_discount_push_request_id", None) == request_id:
                    manager.request_speech_stream_done(request_id)
        except Exception:
            logger.exception("[DiscountPush] Error in async task")

    def _get_discount_items(self, manager: 'BehaviorManager') -> list[dict]:
        try:
            cache = getattr(manager.steam_manager, "cache", None)
            if not isinstance(cache, dict):
                return []
            rows = cache.get("wishlist")
            if not isinstance(rows, list):
                return []
            items = [r for r in rows if isinstance(r, dict)]
            # 仅保留有折扣的
            items = [r for r in items if int(r.get("discount_pct") or 0) > 0]
            items.sort(key=lambda x: int(x.get("discount_pct") or 0), reverse=True)
            return items
        except Exception:
            return []

    def _format_items(self, items: list[dict], *, limit: int = 5) -> str:
        rows: list[str] = []
        for it in items[: int(limit or 0)]:
            name = str(it.get("name") or "").strip()
            pct = it.get("discount_pct")
            price = str(it.get("price") or "").strip()
            if not name:
                continue
            line = f"- {name} -{pct}%"
            if price:
                line += f"（{price}）"
            rows.append(line)
        return "\n".join(rows)
