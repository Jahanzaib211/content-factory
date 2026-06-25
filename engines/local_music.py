"""
Local Music Generation engines — AudioCraft (Meta) and Riffusion.

Free, local music generation as alternatives to paid cloud APIs.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional

from .base import BaseEngine, EngineCapability, EngineHealth, EngineResult, engine_method, EngineError

log = logging.getLogger(__name__)


class AudioCraftEngine(BaseEngine):
    """Meta AudioCraft — local music generation (MusicGen, AudioGen)."""
    provider_id = "audiocraft"
    display_name = "AudioCraft (Meta, local, free)"
    capability = EngineCapability.MUSIC
    cost_hint = "Free (local GPU)"
    hardware_hint = "4GB+ VRAM"
    requires_key = False
    key_env_var = None

    def __init__(self) -> None:
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            try:
                import torch
                from audiocraft.models import MusicGen
                log.info("[audiocraft] Loading MusicGen model...")
                self._model = MusicGen.get_pretrained("facebook/musicgen-small")
                log.info("[audiocraft] MusicGen loaded")
            except ImportError as e:
                raise EngineError("audiocraft not installed: pip install audiocraft") from e
        return self._model

    async def health(self) -> EngineHealth:
        try:
            self._ensure_model()
            return EngineHealth(healthy=True, detail="AudioCraft MusicGen ready")
        except Exception as e:
            return EngineHealth(healthy=False, detail=f"{type(e).__name__}: {e}")

    @engine_method
    async def generate_music(
        self,
        prompt: str,
        duration: float = 10.0,
        output: Optional[str] = None,
        temperature: float = 1.0,
        top_k: int = 250,
        top_p: float = 0.0,
    ) -> Dict[str, Any]:
        """Generate music from a text prompt."""
        import torch
        import uuid

        if not output:
            output = f"/tmp/audiocraft_{uuid.uuid4().hex[:8]}.wav"

        model = self._ensure_model()
        model.set_generation_params(
            duration=int(duration),
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
        )

        wav = model.generate([prompt])

        # Save audio
        import torchaudio
        torchaudio.save(output, wav[0].cpu(), sample_rate=32000)

        return {
            "audio_path": output,
            "duration_ms": int(duration * 1000),
            "prompt": prompt[:100],
            "model": "musicgen-small",
        }


class RiffusionEngine(BaseEngine):
    """Riffusion — spectrogram-based music generation via API."""
    provider_id = "riffusion"
    display_name = "Riffusion (spectrogram-based, free)"
    capability = EngineCapability.MUSIC
    cost_hint = "Free (local GPU or API)"
    hardware_hint = "2GB+ VRAM"
    requires_key = False
    key_env_var = None

    def __init__(self) -> None:
        self._api_url = os.getenv("RIFFUSION_URL", "http://riffusion:3000")

    async def health(self) -> EngineHealth:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self._api_url}/health")
                if r.status_code == 200:
                    return EngineHealth(healthy=True, detail=f"Riffusion at {self._api_url}")
                return EngineHealth(healthy=False, detail=f"Riffusion returned {r.status_code}")
        except Exception as e:
            return EngineHealth(healthy=False, detail=f"Riffusion not reachable: {e}")

    @engine_method
    async def generate_music(
        self,
        prompt: str,
        duration: float = 10.0,
        output: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate music via Riffusion API."""
        import httpx
        import uuid

        if not output:
            output = f"/tmp/riffusion_{uuid.uuid4().hex[:8]}.mp3"

        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                f"{self._api_url}/api/generate",
                json={"prompt": prompt, "duration": duration},
            )
            if r.status_code != 200:
                raise EngineError(f"Riffusion failed: {r.text[:200]}")

            with open(output, "wb") as f:
                f.write(r.content)

        return {
            "audio_path": output,
            "duration_ms": int(duration * 1000),
            "prompt": prompt[:100],
        }


__all__ = ["AudioCraftEngine", "RiffusionEngine"]
