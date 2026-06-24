"""
MiniMax-native music generation engine.

Wraps MiniMax Music-2.6. Pricing: $0.15 per up-to-5-minute song (free tier available).
Lyrics generation: $0.01 per song.

ADDITIVE — does not touch saasshorts.py.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional

import httpx

from .base import BaseEngine, EngineCapability, EngineHealth, EngineResult, engine_method, EngineError

log = logging.getLogger(__name__)

MINIMAX_BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.MiniMax.io")
MINIMAX_API_KEY_ENV = "MINIMAX_API_KEY"

MUSIC_MODEL = "music-2.6"


class MiniMaxMusicEngine(BaseEngine):
    provider_id = "minimax"
    display_name = "MiniMax (music-2.6)"
    capability = EngineCapability.MUSIC
    cost_hint = "$0.15/song (Limited Free)"
    hardware_hint = "cloud"
    requires_key = True
    key_env_var = MINIMAX_API_KEY_ENV

    def __init__(self) -> None:
        self.base_url = os.getenv("MINIMAX_BASE_URL", "https://api.MiniMax.io")
        self._http: Optional[httpx.AsyncClient] = None

    async def _client(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=httpx.Timeout(120.0))
        return self._http

    def _headers(self, api_key: str) -> Dict[str, str]:
        return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def _resolve_key(self) -> str:
        key = os.getenv(MINIMAX_API_KEY_ENV)
        if not key:
            raise EngineError(f"{MINIMAX_API_KEY_ENV} not set")
        return key

    async def health(self) -> EngineHealth:
        try:
            api_key = self._resolve_key()
            client = await self._client()
            start = time.perf_counter()
            r = await client.get(
                f"{self.base_url}/v1/music_generation",
                headers=self._headers(api_key),
            )
            latency = (time.perf_counter() - start) * 1000
            return EngineHealth(
                healthy=r.status_code in (200, 405),
                detail=f"HTTP {r.status_code}",
                latency_ms=latency,
            )
        except Exception as e:
            return EngineHealth(healthy=False, detail=f"{type(e).__name__}: {e}")

    @engine_method
    async def generate_music(
        self,
        prompt: str,
        lyrics: Optional[str] = None,
        model: str = MUSIC_MODEL,
    ) -> Dict[str, Any]:
        """Generate a song from a style prompt (and optional lyrics)."""
        if not prompt:
            raise EngineError("prompt is required")
        api_key = self._resolve_key()
        client = await self._client()
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
        }
        if lyrics:
            payload["lyrics"] = lyrics
        r = await client.post(
            f"{self.base_url}/v1/music_generation",
            headers=self._headers(api_key),
            json=payload,
        )
        if r.status_code >= 400:
            raise EngineError(f"MiniMax music error {r.status_code}: {r.text[:500]}")
        return r.json()

    @engine_method
    async def generate_lyrics(self, prompt: str) -> Dict[str, Any]:
        """Generate lyrics from a theme/prompt."""
        if not prompt:
            raise EngineError("prompt is required")
        api_key = self._resolve_key()
        client = await self._client()
        r = await client.post(
            f"{self.base_url}/v1/lyrics_generation",
            headers=self._headers(api_key),
            json={"prompt": prompt},
        )
        if r.status_code >= 400:
            raise EngineError(f"MiniMax lyrics error {r.status_code}: {r.text[:500]}")
        return r.json()


__all__ = ["MiniMaxMusicEngine", "MUSIC_MODEL"]
