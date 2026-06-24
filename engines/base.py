"""
Base interface for all engines in Content Factory.

An Engine is a self-contained wrapper around a single AI capability
(LLM, STT, TTS, image, video, voice clone, music, storage, social post)
backed by one provider (e.g. MiniMax, local vLLM, ElevenLabs, local
ComfyUI, etc.). Multiple engines can be registered per capability;
the registry orders them by priority and the active one is used.

All async methods return EngineResult on success, raise EngineError
on failure. Implementations should not block the event loop.
"""
from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar, Union


class EngineCapability(str, Enum):
    LLM = "llm"
    STT = "stt"
    TTS = "tts"
    IMAGE = "image"
    VIDEO = "video"
    LIP_SYNC = "lip_sync"
    VOICE_CLONE = "voice_clone"
    MUSIC = "music"
    FACE_DETECT = "face_detect"
    OBJECT_TRACK = "object_track"
    SCENE_DETECT = "scene_detect"
    SPEAKER_DIARIZE = "speaker_diarize"
    TRANSLATION = "translation"
    STORAGE = "storage"
    SOCIAL_POST = "social_post"


@dataclass
class EngineHealth:
    healthy: bool
    detail: str = ""
    latency_ms: Optional[float] = None
    last_checked: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "healthy": self.healthy,
            "detail": self.detail,
            "latency_ms": self.latency_ms,
            "last_checked": self.last_checked,
        }


@dataclass
class EngineResult:
    """Generic result envelope. Implementations may attach typed payload."""

    success: bool
    data: Any = None
    error: Optional[str] = None
    cost_usd: float = 0.0
    duration_ms: float = 0.0
    provider: str = ""
    model: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "error": self.error,
            "cost_usd": self.cost_usd,
            "duration_ms": self.duration_ms,
            "provider": self.provider,
            "model": self.model,
            "metadata": self.metadata,
        }


class EngineError(RuntimeError):
    """Raised when an engine call fails. Use `code` to distinguish retryable errors."""


T = TypeVar("T")


class BaseEngine(ABC):
    provider_id: str = "base"
    display_name: str = "Base Engine"
    capability: EngineCapability = EngineCapability.LLM
    cost_hint: str = ""
    hardware_hint: str = "any"
    requires_key: bool = True
    key_env_var: Optional[str] = None

    @abstractmethod
    async def health(self) -> EngineHealth:
        """Probe liveness. Should not raise; return EngineHealth(healthy=False) on error."""

    async def execute(self, *args: Any, **kwargs: Any) -> EngineResult:
        """Capability-specific entry point. Subclasses typically expose
        domain-named async methods (synthesize, generate_image, etc.) and
        inherit this default `execute` shim. Override only if you want a
        single generic dispatch.
        """
        return EngineResult(
            success=False,
            error=(
                f"{self.__class__.__name__} does not implement execute(); "
                "call a domain method like synthesize() / generate_image() / etc."
            ),
            provider=self.provider_id,
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} provider={self.provider_id!r} cap={self.capability.value}>"


def engine_method(
    fn: Callable[..., Awaitable[T]],
) -> Callable[..., Awaitable[Union[T, EngineResult]]]:
    """Decorator: wraps an async method, catches errors, returns EngineResult envelope."""

    async def wrapper(self: BaseEngine, *args: Any, **kwargs: Any) -> EngineResult:
        start = time.perf_counter()
        try:
            data = await fn(self, *args, **kwargs)
            return EngineResult(
                success=True,
                data=data,
                duration_ms=(time.perf_counter() - start) * 1000,
                provider=self.provider_id,
            )
        except EngineError as e:
            return EngineResult(
                success=False,
                error=str(e),
                duration_ms=(time.perf_counter() - start) * 1000,
                provider=self.provider_id,
            )
        except Exception as e:  # pragma: no cover - last-resort guard
            return EngineResult(
                success=False,
                error=f"{type(e).__name__}: {e}",
                duration_ms=(time.perf_counter() - start) * 1000,
                provider=self.provider_id,
            )

    return wrapper


async def run_with_failover(
    engines: List[BaseEngine],
    method: str,
    *args: Any,
    **kwargs: Any,
) -> EngineResult:
    """Call `method` on each engine in order until one succeeds."""
    last_error: Optional[EngineResult] = None
    for e in engines:
        try:
            fn = getattr(e, method)
            result = await fn(*args, **kwargs)
            if isinstance(result, EngineResult) and result.success:
                return result
            last_error = result if isinstance(result, EngineResult) else None
        except Exception as exc:  # pragma: no cover
            last_error = EngineResult(
                success=False, error=f"{type(exc).__name__}: {exc}", provider=e.provider_id
            )
            continue
    if last_error is not None:
        return last_error
    return EngineResult(success=False, error="No engines available")


__all__ = [
    "BaseEngine",
    "EngineCapability",
    "EngineHealth",
    "EngineResult",
    "EngineError",
    "engine_method",
    "run_with_failover",
]
