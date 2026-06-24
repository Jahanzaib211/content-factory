"""
MiniMax-native video + image generation engine.

Wraps MiniMax's image-01 (T2I/I2I) and S2V-01 (subject-reference to video)
plus Hailuo-2.3-Fast (T2V) APIs. Returns EngineResult with file paths/URLs.

Endpoint base: https://api.MiniMax.io  (overridable via MINIMAX_BASE_URL)
Auth: Bearer header with MiniMax API key.

This is ADDITIVE — does not touch saasshorts.py. Existing fal.ai code path
remains the default until USE_MINIMAX_VIDEO is wired into the call sites
(separate change in a follow-up commit).
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any, Dict, List, Optional

import httpx

from .base import BaseEngine, EngineCapability, EngineHealth, EngineResult, engine_method, EngineError

log = logging.getLogger(__name__)

MINIMAX_BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.MiniMax.io")
MINIMAX_API_KEY_ENV = "MINIMAX_API_KEY"

IMAGE_MODEL = "image-01"
S2V_MODEL = "S2V-01"
HAILUO_FAST_MODEL = "MiniMax-Hailuo-2.3-Fast"

POLL_INTERVAL_SEC = 5
POLL_TIMEOUT_SEC = 600  # 10 min


class MiniMaxVideoEngine(BaseEngine):
    provider_id = "minimax"
    display_name = "MiniMax (image-01 / S2V-01 / Hailuo-2.3-Fast)"
    capability = EngineCapability.IMAGE
    cost_hint = "$0.0035/image, $0.19-0.56/video"
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
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _resolve_key(self) -> str:
        key = os.getenv(MINIMAX_API_KEY_ENV)
        if not key:
            raise EngineError(
                f"{MINIMAX_API_KEY_ENV} not set. Add it to your environment or Settings."
            )
        return key

    async def health(self) -> EngineHealth:
        try:
            api_key = self._resolve_key()
            client = await self._client()
            start = time.perf_counter()
            # Lightweight: hit /v1/models (OpenAI-compatible)
            r = await client.get(
                f"{self.base_url}/v1/models",
                headers=self._headers(api_key),
            )
            latency = (time.perf_counter() - start) * 1000
            if r.status_code == 200:
                return EngineHealth(healthy=True, detail="ok", latency_ms=latency)
            return EngineHealth(
                healthy=False, detail=f"HTTP {r.status_code}", latency_ms=latency
            )
        except Exception as e:
            return EngineHealth(healthy=False, detail=f"{type(e).__name__}: {e}")

    @engine_method
    async def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "9:16",
        n: int = 1,
        seed: Optional[int] = None,
        response_format: str = "url",
    ) -> Dict[str, Any]:
        """Text-to-image via MiniMax image-01. Returns dict with `image_urls` (or base64)."""
        if not prompt:
            raise EngineError("prompt is required")
        if len(prompt) > 1500:
            raise EngineError("prompt exceeds 1500 chars")
        api_key = self._resolve_key()
        client = await self._client()
        payload: Dict[str, Any] = {
            "model": IMAGE_MODEL,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "response_format": response_format,
            "n": max(1, min(9, n)),
            "prompt_optimizer": True,
        }
        if seed is not None:
            payload["seed"] = seed
        r = await client.post(
            f"{self.base_url}/v1/image_generation",
            headers=self._headers(api_key),
            json=payload,
        )
        if r.status_code >= 400:
            raise EngineError(f"MiniMax image error {r.status_code}: {r.text[:500]}")
        data = r.json()
        return data

    @engine_method
    async def generate_image_i2i(
        self,
        prompt: str,
        image_url: str,
        aspect_ratio: str = "9:16",
        n: int = 1,
    ) -> Dict[str, Any]:
        """Image-to-image: transform an input image guided by a prompt."""
        if not prompt or not image_url:
            raise EngineError("prompt and image_url are required")
        api_key = self._resolve_key()
        client = await self._client()
        payload: Dict[str, Any] = {
            "model": IMAGE_MODEL,
            "prompt": prompt,
            "image": image_url,
            "aspect_ratio": aspect_ratio,
            "n": max(1, min(9, n)),
        }
        r = await client.post(
            f"{self.base_url}/v1/image_generation",
            headers=self._headers(api_key),
            json=payload,
        )
        if r.status_code >= 400:
            raise EngineError(f"MiniMax i2i error {r.status_code}: {r.text[:500]}")
        return r.json()

    @engine_method
    async def generate_video_s2v(
        self,
        prompt: str,
        subject_image_url: str,
        model: str = S2V_MODEL,
    ) -> Dict[str, Any]:
        """Subject-reference to video: animate a portrait with a prompt.

        Returns dict with `task_id`. Use `poll_video_task()` to check status,
        then `download_video()` once `status == "Success"`.
        """
        if not prompt or not subject_image_url:
            raise EngineError("prompt and subject_image_url are required")
        api_key = self._resolve_key()
        client = await self._client()
        payload = {
            "model": model,
            "prompt": prompt,
            "subject_reference": [
                {"type": "character", "image": [subject_image_url]}
            ],
        }
        r = await client.post(
            f"{self.base_url}/v1/video_generation",
            headers=self._headers(api_key),
            json=payload,
        )
        if r.status_code >= 400:
            raise EngineError(f"MiniMax S2V error {r.status_code}: {r.text[:500]}")
        data = r.json()
        return data

    @engine_method
    async def generate_video_t2v(
        self,
        prompt: str,
        model: str = HAILUO_FAST_MODEL,
        duration: int = 6,
    ) -> Dict[str, Any]:
        """Text-to-video via Hailuo-2.3-Fast. Returns task_id."""
        if not prompt:
            raise EngineError("prompt is required")
        api_key = self._resolve_key()
        client = await self._client()
        payload = {
            "model": model,
            "prompt": prompt,
            "duration": duration,
        }
        r = await client.post(
            f"{self.base_url}/v1/video_generation",
            headers=self._headers(api_key),
            json=payload,
        )
        if r.status_code >= 400:
            raise EngineError(f"MiniMax T2V error {r.status_code}: {r.text[:500]}")
        return r.json()

    @engine_method
    async def poll_video_task(self, task_id: str) -> Dict[str, Any]:
        """Poll a video generation task. Returns latest status dict."""
        if not task_id:
            raise EngineError("task_id required")
        api_key = self._resolve_key()
        client = await self._client()
        r = await client.get(
            f"{self.base_url}/v1/query/video_generation",
            headers=self._headers(api_key),
            params={"task_id": task_id},
        )
        if r.status_code >= 400:
            raise EngineError(f"MiniMax poll error {r.status_code}: {r.text[:500]}")
        return r.json()

    @engine_method
    async def download_video(self, file_id: str) -> bytes:
        """Download generated video bytes by file_id. URL is valid 1 hour."""
        if not file_id:
            raise EngineError("file_id required")
        api_key = self._resolve_key()
        client = await self._client()
        r = await client.get(
            f"{self.base_url}/v1/files/retrieve",
            headers=self._headers(api_key),
            params={"file_id": file_id},
        )
        if r.status_code >= 400:
            raise EngineError(f"MiniMax retrieve error {r.status_code}: {r.text[:500]}")
        meta = r.json().get("file", {})
        download_url = meta.get("download_url")
        if not download_url:
            raise EngineError("No download_url in response")
        # Then download the actual bytes
        v = await client.get(download_url, timeout=httpx.Timeout(600.0))
        if v.status_code >= 400:
            raise EngineError(f"download failed: HTTP {v.status_code}")
        return v.content

    async def wait_for_video(
        self, task_id: str, timeout_sec: int = POLL_TIMEOUT_SEC
    ) -> Dict[str, Any]:
        """Poll until status is Success/Fail or timeout. Returns the last poll response."""
        start = time.time()
        last: Dict[str, Any] = {}
        while time.time() - start < timeout_sec:
            res = await self.poll_video_task(task_id)
            data = res.data if hasattr(res, "data") else res
            if isinstance(data, EngineResult):
                data = data.data
            last = data or {}
            status = last.get("status")
            if status == "Success":
                return last
            if status == "Fail":
                raise EngineError(f"Video generation failed: {last}")
            await asyncio.sleep(POLL_INTERVAL_SEC)
        raise EngineError(f"Video generation timed out after {timeout_sec}s")


__all__ = ["MiniMaxVideoEngine", "IMAGE_MODEL", "S2V_MODEL", "HAILUO_FAST_MODEL"]
