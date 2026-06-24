"""
Engines package: pluggable provider abstraction for Content Factory.

Each capability (LLM, STT, TTS, image, video, voice clone, music, storage,
social post) has one or more Engine implementations. The active engine per
capability is selected via the registry (env vars / Settings UI).

The legacy code paths in saasshorts.py / translate.py / s3_uploader.py /
social upload-post etc. remain untouched and still work. New code can
opt-in to the engines layer via:

    from engines import get_engine, EngineCapability
    tts = get_engine(EngineCapability.TTS)
    audio = await tts.synthesize("hello", voice_id="English_Graceful_Lady")

Additive only — no breaking changes to existing call sites.
"""
from __future__ import annotations

import os
import logging
from enum import Enum
from typing import Any, Dict, List, Optional

from .base import BaseEngine, EngineCapability, EngineHealth, EngineResult  # noqa: F401

log = logging.getLogger(__name__)

_REGISTRY: Dict["EngineCapability", List[BaseEngine]] = {}


class FeatureFlags:
    """Runtime feature flags. Read from env vars; can be overridden by Settings UI."""

    @staticmethod
    def use_minimax_video() -> bool:
        return os.getenv("USE_MINIMAX_VIDEO", "1") == "1"

    @staticmethod
    def use_minimax_tts() -> bool:
        return os.getenv("USE_MINIMAX_TTS", "1") == "1"

    @staticmethod
    def use_minimax_music() -> bool:
        return os.getenv("USE_MINIMAX_MUSIC", "1") == "1"

    @staticmethod
    def use_legacy_fal() -> bool:
        return os.getenv("USE_LEGACY_FAL", "0") == "1"

    @staticmethod
    def use_legacy_elevenlabs() -> bool:
        return os.getenv("USE_LEGACY_ELEVENLABS", "0") == "1"

    @staticmethod
    def use_legacy_s3() -> bool:
        return os.getenv("USE_LEGACY_S3", "0") == "1"

    @staticmethod
    def use_legacy_upload_post() -> bool:
        return os.getenv("USE_LEGACY_UPLOAD_POST", "1") == "1"


def register(engine: BaseEngine) -> None:
    """Register an engine. Idempotent."""
    if engine.capability not in _REGISTRY:
        _REGISTRY[engine.capability] = []
    if not any(e.provider_id == engine.provider_id for e in _REGISTRY[engine.capability]):
        _REGISTRY[engine.capability].append(engine)
        log.info(f"Registered engine: {engine.provider_id} for {engine.capability.value}")


def get_active(capability: EngineCapability) -> Optional[BaseEngine]:
    """Return the active engine for a capability (first registered, ordered by priority)."""
    engines = _REGISTRY.get(capability, [])
    return engines[0] if engines else None


def get_all(capability: EngineCapability) -> List[BaseEngine]:
    """Return all registered engines for a capability (in priority order)."""
    return list(_REGISTRY.get(capability, []))


def set_active(capability: EngineCapability, provider_id: str) -> bool:
    """Move the named engine to the front of the list (highest priority)."""
    engines = _REGISTRY.get(capability, [])
    for i, e in enumerate(engines):
        if e.provider_id == provider_id:
            engines.insert(0, engines.pop(i))
            log.info(f"Active engine for {capability.value}: {provider_id}")
            return True
    return False


def list_providers(capability: EngineCapability) -> List[Dict[str, Any]]:
    """Public registry snapshot for the Settings UI engine picker."""
    _ensure_bootstrap()
    out = []
    for e in get_all(capability):
        out.append(
            {
                "provider_id": e.provider_id,
                "display_name": e.display_name,
                "capability": e.capability.value,
                "cost_hint": e.cost_hint,
                "hardware_hint": e.hardware_hint,
                "requires_key": e.requires_key,
                "key_env_var": e.key_env_var,
            }
        )
    return out


def get_api_key_for(engine: BaseEngine) -> Optional[str]:
    """Read API key from env (engine key_env_var) or return None."""
    if not engine.requires_key or not engine.key_env_var:
        return None
    return os.getenv(engine.key_env_var)


def _bootstrap() -> None:
    """Register built-in engines. Called lazily on first get_active()."""
    from .minimax_video import MiniMaxVideoEngine
    from .minimax_speech import MiniMaxSpeechEngine
    from .minimax_music import MiniMaxMusicEngine
    from .stt import FasterWhisperLocalEngine, MiniMaxSttEngine
    from .voice_clone import MiniMaxVoiceCloneEngine, CosyVoiceLocalEngine
    from .storage import LocalStorageEngine, SeaweedFSEngine, S3StorageEngine
    from .social import YouTubeEngine, TikTokEngine, InstagramEngine
    from .llm import LiteLLMRouterEngine

    # Image / Video / Music
    register(MiniMaxVideoEngine())            # IMAGE + VIDEO
    register(MiniMaxMusicEngine())            # MUSIC

    # TTS / Voice Clone
    register(MiniMaxSpeechEngine())           # TTS
    register(MiniMaxVoiceCloneEngine())       # VOICE_CLONE
    register(CosyVoiceLocalEngine())          # VOICE_CLONE (local fallback)

    # STT
    register(FasterWhisperLocalEngine())      # STT (default, no key needed)
    register(MiniMaxSttEngine())              # STT (placeholder until MiniMax exposes ASR)

    # Storage
    register(LocalStorageEngine())            # STORAGE (default)
    register(SeaweedFSEngine())              # STORAGE (self-hosted S3)
    register(S3StorageEngine())               # STORAGE (AWS legacy)

    # Social
    register(YouTubeEngine())                 # SOCIAL_POST
    register(TikTokEngine())                  # SOCIAL_POST
    register(InstagramEngine())               # SOCIAL_POST

    # LLM router
    register(LiteLLMRouterEngine())           # LLM (unified multi-provider)


_bootstrapped = False


def _ensure_bootstrap() -> None:
    global _bootstrapped
    if not _bootstrapped:
        _bootstrap()
        _bootstrapped = True


def get_engine(capability: EngineCapability) -> BaseEngine:
    """Convenience: get the active engine for a capability, bootstrapping on first call."""
    _ensure_bootstrap()
    engine = get_active(capability)
    if engine is None:
        raise RuntimeError(
            f"No engine registered for capability {capability.value}. "
            f"Available providers: {list_providers(capability)}"
        )
    return engine


__all__ = [
    "BaseEngine",
    "EngineCapability",
    "EngineHealth",
    "EngineResult",
    "FeatureFlags",
    "register",
    "get_active",
    "get_all",
    "get_engine",
    "set_active",
    "list_providers",
    "get_api_key_for",
]
