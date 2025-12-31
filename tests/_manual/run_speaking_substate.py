"""Manual runner for AI speaking substates.

Goal:
- Avoid waiting for random triggers.
- Keep prompt assembly real (PromptManager.get_prompt).
- Allow optionally calling the real LLM service (LLMService.stream_chat_completion).

Usage (from repo root):
  D:/project/SteaMiss/.venv/Scripts/python.exe tests/_manual/run_speaking_substate.py --substate news
  D:/project/SteaMiss/.venv/Scripts/python.exe tests/_manual/run_speaking_substate.py --substate free_game
  D:/project/SteaMiss/.venv/Scripts/python.exe tests/_manual/run_speaking_substate.py --substate discount
  D:/project/SteaMiss/.venv/Scripts/python.exe tests/_manual/run_speaking_substate.py --substate speaking --seed 1

Real LLM:
  - Ensure config/settings.json has llm_api_key/llm_base_url/llm_model.
  - Then pass --real-llm.

Notes:
- NewsPushSubState reads config/news_data.json on disk.
- FreeGamePushSubState expects steam_manager.cache['free_game'] = {"items": [...]}
- DiscountPushSubState expects steam_manager.cache['wishlist'] = [{"discount_pct": ...}, ...]
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
import threading
from dataclasses import dataclass
from typing import Any, Iterator


# Ensure we run with repo root as CWD so states that use relative paths work.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
os.chdir(_REPO_ROOT)


import src.ai.states as _states_module
from src.ai.states import (
    DiscountPushSubState,
    FreeGamePushSubState,
    NewsPushSubState,
    SpeakingState,
    SpeakingSubStateType,
    StateType,
)
from src.feature_core.services.llm_service import LLMService
from src.storage.config_manager import ConfigManager
from src.storage.prompt_manager import PromptManager


_TRACKED_THREADS: list[threading.Thread] = []


def _patch_states_threads() -> None:
    """Patch src.ai.states to create non-daemon tracked threads.

    Substates spawn threads as daemon=True in production. In this runner we want:
    - non-daemon to avoid interpreter-finalize crashes while printing
    - tracked so we can join deterministically
    """

    original_thread_cls = _states_module.threading.Thread

    class _TrackedThread(original_thread_cls):
        def __init__(self, *args, **kwargs):
            kwargs = dict(kwargs)
            # Force non-daemon so process won't exit mid-stream.
            kwargs["daemon"] = False
            super().__init__(*args, **kwargs)
            _TRACKED_THREADS.append(self)

    _states_module.threading.Thread = _TrackedThread


class _EchoLLMService:
    """Fallback LLM streamer when real LLM is not configured."""

    def stream_chat_completion(self, messages: list[dict]) -> Iterator[str]:
        content = ""
        try:
            content = str((messages or [{}])[0].get("content") or "")
        except Exception:
            content = ""
        preview = content.strip().replace("\r", "")
        if len(preview) > 200:
            preview = preview[:200] + "..."
        text = f"（mock LLM）收到 prompt 预览：\n{preview}\n"
        # stream in small chunks
        for i in range(0, len(text), 24):
            yield text[i : i + 24]
            time.sleep(0.02)


@dataclass
class _MiniSteamManager:
    cache: dict[str, Any]


class _MiniBehaviorManager:
    """A tiny stand-in for BehaviorManager, just enough for substate execution."""

    def __init__(self, *, cache: dict[str, Any], llm_service: Any, prompt_manager: PromptManager):
        self.steam_manager = _MiniSteamManager(cache=cache)
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager
        self.last_recommend_time = time.time()
        self._current_state_type = StateType.IDLE

        self._stream_started = threading.Event()
        self._stream_done = threading.Event()
        self._stream_done.set()
        self._active_request_id: str | None = None

        # used by SpeakingState.enter()
        self._speaking_sub_states = {
            SpeakingSubStateType.NEWS_PUSH: NewsPushSubState(),
            SpeakingSubStateType.FREE_GAME_PUSH: FreeGamePushSubState(),
            SpeakingSubStateType.DISCOUNT_PUSH: DiscountPushSubState(),
        }

    def get_speaking_sub_state(self, sub_state_type: SpeakingSubStateType):
        return self._speaking_sub_states.get(sub_state_type)

    def transition_to(self, state_type: StateType):
        self._current_state_type = state_type
        print(f"\n[transition_to] -> {state_type.name}\n")

    def request_speech_stream_started(self, request_id: str, interaction_context=None):
        self._active_request_id = request_id
        self._stream_done.clear()
        self._stream_started.set()
        print(f"\n[stream_started] request_id={request_id}")
        if interaction_context is not None:
            print(f"[interaction_context] {interaction_context}")
        print("\n--- LLM OUTPUT START ---\n")

    def request_speech_stream_delta(self, request_id: str, delta: str):
        sys.stdout.write(delta)
        sys.stdout.flush()

    def request_speech_stream_done(self, request_id: str):
        print("\n\n--- LLM OUTPUT DONE ---\n")
        if self._active_request_id == request_id:
            self._stream_done.set()

    def wait_stream_done(self, *, timeout_s: float) -> bool:
        # If no stream started, don't wait forever.
        if not self._stream_started.wait(timeout=min(2.0, timeout_s)):
            return True
        return self._stream_done.wait(timeout=timeout_s)


def _load_game_data_cache() -> dict[str, Any]:
    path = os.path.join("config", "game_data.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _ensure_minimum_cache(cache: dict[str, Any]) -> dict[str, Any]:
    cache = dict(cache or {})

    if "free_game" not in cache:
        cache["free_game"] = {
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "items": [
                {"title": "示例：Epic 免费游戏 A", "period": "现在 - 明天", "url": "https://store.epicgames.com/"},
                {"title": "示例：Epic 免费游戏 B", "period": "本周", "url": "https://store.epicgames.com/"},
            ],
        }

    if "wishlist" not in cache:
        cache["wishlist"] = [
            {"name": "示例：愿望单游戏 A", "discount_pct": 75, "price": "¥ 19.80"},
            {"name": "示例：愿望单游戏 B", "discount_pct": 40, "price": "¥ 68.00"},
        ]

    return cache


def _build_llm_service(*, use_real_llm: bool) -> Any:
    if not use_real_llm:
        return _EchoLLMService()

    config_manager = ConfigManager()
    llm = LLMService(config_manager)
    # If missing config, fall back to mock (avoid silent no-op generator)
    if not config_manager.get("llm_api_key") or not config_manager.get("llm_base_url") or not config_manager.get("llm_model"):
        print("[warn] LLM 配置缺失（config/settings.json: llm_api_key/llm_base_url/llm_model），将使用 mock LLM。")
        return _EchoLLMService()

    return llm


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--substate",
        choices=["news", "free_game", "discount", "speaking"],
        default="speaking",
        help="Which substate to run (or 'speaking' to run SpeakingState.enter()).",
    )
    parser.add_argument("--real-llm", action="store_true", help="Call real LLMService (requires config/settings.json)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed (useful when substate=speaking)")
    parser.add_argument(
        "--ensure-sample-cache",
        action="store_true",
        help="If cache fields are missing, inject sample free_game/wishlist entries.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Max seconds to wait for streaming output before stopping.",
    )

    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    _patch_states_threads()

    cache = _load_game_data_cache()
    if args.ensure_sample_cache:
        cache = _ensure_minimum_cache(cache)

    prompt_manager = PromptManager()
    llm_service = _build_llm_service(use_real_llm=bool(args.real_llm))

    manager = _MiniBehaviorManager(cache=cache, llm_service=llm_service, prompt_manager=prompt_manager)

    if args.substate == "news":
        NewsPushSubState().execute(manager)
        ok = manager.wait_stream_done(timeout_s=float(args.timeout))
        if not ok:
            print(f"[warn] stream timeout after {args.timeout}s")
        for t in list(_TRACKED_THREADS):
            t.join(timeout=0.2)
        return 0

    if args.substate == "free_game":
        FreeGamePushSubState().execute(manager)
        ok = manager.wait_stream_done(timeout_s=float(args.timeout))
        if not ok:
            print(f"[warn] stream timeout after {args.timeout}s")
        for t in list(_TRACKED_THREADS):
            t.join(timeout=0.2)
        return 0

    if args.substate == "discount":
        DiscountPushSubState().execute(manager)
        ok = manager.wait_stream_done(timeout_s=float(args.timeout))
        if not ok:
            print(f"[warn] stream timeout after {args.timeout}s")
        for t in list(_TRACKED_THREADS):
            t.join(timeout=0.2)
        return 0

    # speaking: pick among available registered substates
    SpeakingState().enter(manager)
    ok = manager.wait_stream_done(timeout_s=float(args.timeout))
    if not ok:
        print(f"[warn] stream timeout after {args.timeout}s")
    for t in list(_TRACKED_THREADS):
        t.join(timeout=0.2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
