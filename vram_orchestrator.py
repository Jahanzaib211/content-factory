"""
VRAM orchestrator (vram_orchestrator.py).

For solo / single-GPU deployments, heavy models can't all fit in VRAM
at once. This orchestrator:

  1. Tracks which GPU service currently holds the GPU
  2. Exposes acquire() / release() via a Redis-backed mutex
  3. Lets backend code say "load Wan 2.1, unload LLM" before each heavy op
  4. Falls back to no-op when no Redis is configured (single user, single
     process — common in solo deployments)

For solo usage this is typically a no-op: the GPU services are
already mutually exclusive (one profile at a time). But it's wired
for the case where a future enhancement wants concurrent vLLM + Wan
on the same GPU.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Optional

try:
    import redis  # type: ignore
    from redis.exceptions import LockError, LockNotOwnedError  # type: ignore
except ImportError:  # pragma: no cover
    redis = None
    LockError = Exception
    LockNotOwnedError = Exception

log = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "")  # empty -> no-op
GPU_HOLD_TIMEOUT_SEC = int(os.getenv("GPU_HOLD_TIMEOUT_SEC", "30"))


class VRAMOrchestrator:
    """Redis-backed GPU mutex. No-op when REDIS_URL is empty."""

    def __init__(self, redis_url: str = REDIS_URL) -> None:
        self.redis_url = redis_url
        self._client = None
        if redis and redis_url:
            try:
                self._client = redis.from_url(redis_url, decode_responses=True)
                self._client.ping()
                log.info(f"VRAM orchestrator connected to Redis at {redis_url}")
            except Exception as e:
                log.warning(f"VRAM orchestrator: Redis unreachable, falling back to no-op ({e})")
                self._client = None

    def _lock_name(self, key: str) -> str:
        return f"vram:lock:{key}"

    def acquire(self, key: str, timeout: int = GPU_HOLD_TIMEOUT_SEC) -> Optional[object]:
        """Acquire a named lock. Returns the lock object or None if no-op."""
        if not self._client:
            return None
        lock = self._client.lock(self._lock_name(key), timeout=timeout)
        try:
            got = lock.acquire(blocking=True, timeout=timeout)
            if got:
                return lock
            log.warning(f"VRAM orchestrator: failed to acquire {key} within {timeout}s")
            return None
        except (LockError, LockNotOwnedError) as e:
            log.warning(f"VRAM orchestrator: lock error on {key}: {e}")
            return None

    def release(self, lock) -> None:
        if lock is None:
            return
        try:
            lock.release()
        except (LockError, LockNotOwnedError) as e:
            log.warning(f"VRAM orchestrator: release error: {e}")

    def with_hold(self, key: str, fn, *args, **kwargs):
        """Context-manager-style helper: acquire key, run fn, release."""
        lock = self.acquire(key)
        try:
            return fn(*args, **kwargs)
        finally:
            self.release(lock)

    def status(self) -> dict:
        if not self._client:
            return {"enabled": False, "reason": "no REDIS_URL configured"}
        try:
            keys = self._client.keys("vram:lock:*")
            holders = {}
            for k in keys:
                name = k.replace("vram:lock:", "")
                holders[name] = "held" if self._client.exists(k) else "free"
            return {"enabled": True, "redis": self.redis_url, "locks": holders}
        except Exception as e:
            return {"enabled": False, "reason": str(e)}


# Singleton instance
_orchestrator: Optional[VRAMOrchestrator] = None


def get_orchestrator() -> VRAMOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = VRAMOrchestrator()
    return _orchestrator


__all__ = ["VRAMOrchestrator", "get_orchestrator"]
