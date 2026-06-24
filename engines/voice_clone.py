"""
Voice clone engines.

Two providers:
  - MiniMaxVoiceCloneEngine: rapid voice clone via MiniMax's /v1/voice_clone ($1.50/voice).
  - CosyVoiceLocalEngine: 5-second zero-shot or 1-minute few-shot clone, runs locally
    (60k stars on GitHub, the de-facto open-source voice cloning stack).
    Falls back automatically when MINIMAX_API_KEY is missing or use_minimax_tts is off.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional

import httpx

from .base import BaseEngine, EngineCapability, EngineHealth, EngineResult, engine_method, EngineError

log = logging.getLogger(__name__)


class MiniMaxVoiceCloneEngine(BaseEngine):
    provider_id = "minimax"
    display_name = "MiniMax Voice Clone (cloud, 10s sample, $1.50/voice)"
    capability = EngineCapability.VOICE_CLONE
    cost_hint = "$1.50/voice (one-time)"
    hardware_hint = "cloud"
    requires_key = True
    key_env_var = "MINIMAX_API_KEY"

    def __init__(self) -> None:
        self.base_url = os.getenv("MINIMAX_BASE_URL", "https://api.MiniMax.io")

    async def health(self) -> EngineHealth:
        key = os.getenv("MINIMAX_API_KEY")
        if not key:
            return EngineHealth(healthy=False, detail="MINIMAX_API_KEY not set")
        try:
            async with httpx.AsyncClient(timeout=10.0) as c:
                r = await c.get(f"{self.base_url}/v1/voices", headers={"Authorization": f"Bearer {key}"})
            return EngineHealth(healthy=r.status_code == 200, detail=f"HTTP {r.status_code}")
        except Exception as e:
            return EngineHealth(healthy=False, detail=f"{type(e).__name__}: {e}")

    @engine_method
    async def clone_from_file(
        self, audio_path: str, voice_name: str, sample_text: Optional[str] = None
    ) -> Dict[str, Any]:
        if not os.path.exists(audio_path):
            raise EngineError(f"audio file not found: {audio_path}")
        if not voice_name:
            raise EngineError("voice_name required")
        key = os.getenv("MINIMAX_API_KEY")
        if not key:
            raise EngineError("MINIMAX_API_KEY not set")
        async with httpx.AsyncClient(timeout=180.0) as c:
            with open(audio_path, "rb") as f:
                files = {"audio": (os.path.basename(audio_path), f, "audio/mpeg")}
                data: Dict[str, Any] = {"name": voice_name}
                if sample_text:
                    data["sample_text"] = sample_text
                r = await c.post(
                    f"{self.base_url}/v1/voice_clone",
                    headers={"Authorization": f"Bearer {key}"},
                    files=files, data=data,
                )
        if r.status_code >= 400:
            raise EngineError(f"MiniMax voice clone error {r.status_code}: {r.text[:500]}")
        return r.json()

    @engine_method
    async def list_voices(self) -> list:
        key = os.getenv("MINIMAX_API_KEY")
        if not key:
            raise EngineError("MINIMAX_API_KEY not set")
        async with httpx.AsyncClient(timeout=15.0) as c:
            r = await c.get(f"{self.base_url}/v1/voices", headers={"Authorization": f"Bearer {key}"})
        if r.status_code >= 400:
            raise EngineError(f"list voices error {r.status_code}: {r.text[:500]}")
        data = r.json()
        if isinstance(data, dict) and "voices" in data:
            return data["voices"]
        return data if isinstance(data, list) else []


class CosyVoiceLocalEngine(BaseEngine):
    """Local CosyVoice 300M / 0.5B for offline voice cloning.

    NOTE: requires the `cosyvoice` package + a downloaded model. We expose
    a `health()` that reports the state (model loaded or not) and a
    `clone_from_file()` that fails gracefully with a clear message if
    the model isn't installed. The actual clone is delegated to
    `cosyvoice.cli.cosyvoice.CosyVoice2` once available.

    Add to docker-compose to wire the runtime (see docker-compose.yml).
    """
    provider_id = "cosyvoice"
    display_name = "CosyVoice (local, cross-lingual clone)"
    capability = EngineCapability.VOICE_CLONE
    cost_hint = "Free (local, 2-8GB VRAM)"
    hardware_hint = "2GB VRAM (300M) or 8GB VRAM (0.5B)"
    requires_key = False
    key_env_var = None

    def __init__(self, model_dir: Optional[str] = None) -> None:
        self.model_dir = os.getenv("COSYVOICE_MODEL_DIR", model_dir or "/models/cosyvoice")

    async def health(self) -> EngineHealth:
        if not os.path.isdir(self.model_dir):
            return EngineHealth(
                healthy=False,
                detail=f"CosyVoice model not found at {self.model_dir}. Add cosyvoice service to docker-compose.",
            )
        try:
            import cosyvoice  # type: ignore  # noqa: F401
            return EngineHealth(healthy=True, detail=f"model={self.model_dir}")
        except ImportError:
            return EngineHealth(
                healthy=False,
                detail="cosyvoice package not installed. Use the comfyvoice Docker image.",
            )

    @engine_method
    async def clone_from_file(
        self, audio_path: str, voice_name: str, sample_text: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            from cosyvoice.cli.cosyvoice import CosyVoice2  # type: ignore
        except ImportError as e:
            raise EngineError(
                "cosyvoice package not installed. Run the cosyvoice Docker service."
            ) from e
        if not os.path.isdir(self.model_dir):
            raise EngineError(f"CosyVoice model dir not found: {self.model_dir}")
        if not os.path.exists(audio_path):
            raise EngineError(f"audio file not found: {audio_path}")
        cv = CosyVoice2(self.model_dir, load_jit=False, load_trt=False, fp16=True)
        # cosyvoice returns audio for each text segment. We accept a single
        # prompt text or default to a short sample if none provided.
        prompt_text = sample_text or "Hello, this is a sample of my cloned voice."
        import torchaudio  # type: ignore
        out_path = os.path.join("/tmp", f"cosyvoice_{voice_name}.wav")
        results = list(cv.inference_cross_lingual(prompt_text, audio_path))
        if not results:
            raise EngineError("CosyVoice produced no audio")
        # results: list of (text, speech_tensor) tuples
        speech = results[0][1]
        torchaudio.save(out_path, speech, sample_rate=cv.sample_rate)
        return {"voice_name": voice_name, "out_path": out_path, "model": self.model_dir}


__all__ = ["MiniMaxVoiceCloneEngine", "CosyVoiceLocalEngine"]
