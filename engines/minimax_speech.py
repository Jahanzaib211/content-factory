"""
MiniMax-native speech (TTS, voice clone, voice list) engine.

Wraps MiniMax's:
  - /v1/t2a_v2               — sync T2A (text-to-audio)
  - /v1/voice_clone          — rapid voice clone
  - /v1/voices               — list system + cloned voices
  - /v1/voice_design         — text-described voice

Models: speech-2.8-hd, speech-2.8-turbo, speech-2.6-hd, speech-02-hd, etc.
30+ languages via `language_boost` parameter.

ADDITIVE — does not touch translate.py / saasshorts.py.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional

import httpx

from .base import BaseEngine, EngineCapability, EngineHealth, EngineResult, engine_method, EngineError

log = logging.getLogger(__name__)

MINIMAX_BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.MiniMax.io")
MINIMAX_API_KEY_ENV = "MINIMAX_API_KEY"

# Curated set of system voices (full list via /v1/voices)
DEFAULT_VOICES = {
    "English_Graceful_Lady": {"language": "English", "gender": "female", "style": "graceful"},
    "English_Insightful_Speaker": {"language": "English", "gender": "male", "style": "insightful"},
    "English_radiant_girl": {"language": "English", "gender": "female", "style": "bright"},
    "English_Persuasive_Man": {"language": "English", "gender": "male", "style": "persuasive"},
    "English_Lucky_Robot": {"language": "English", "gender": "neutral", "style": "robotic"},
    "Chinese (Mandarin)_Lyrical_Voice": {"language": "Chinese", "gender": "female", "style": "lyrical"},
    "Japanese_Whisper_Belle": {"language": "Japanese", "gender": "female", "style": "whisper"},
    "Spanish_expressive_narrator": {"language": "Spanish", "gender": "male", "style": "narrator"},
}

LANGUAGE_BOOST_OPTIONS = [
    "auto", "Chinese", "English", "Arabic", "Russian", "Spanish", "French",
    "Portuguese", "German", "Turkish", "Dutch", "Ukrainian", "Vietnamese",
    "Indonesian", "Japanese", "Italian", "Korean", "Thai", "Polish",
    "Romanian", "Greek", "Czech", "Finnish", "Hindi", "Bulgarian", "Danish",
    "Hebrew", "Malay", "Persian", "Slovak", "Swedish", "Croatian", "Filipino",
    "Hungarian", "Norwegian", "Slovenian", "Catalan", "Nynorsk", "Tamil",
    "Afrikaans",
]


class MiniMaxSpeechEngine(BaseEngine):
    provider_id = "minimax"
    display_name = "MiniMax (speech-2.8-hd, 30+ languages)"
    capability = EngineCapability.TTS
    cost_hint = "$60-100/M chars"
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
                f"{self.base_url}/v1/voices",
                headers=self._headers(api_key),
            )
            latency = (time.perf_counter() - start) * 1000
            if r.status_code == 200:
                return EngineHealth(healthy=True, detail="ok", latency_ms=latency)
            return EngineHealth(healthy=False, detail=f"HTTP {r.status_code}", latency_ms=latency)
        except Exception as e:
            return EngineHealth(healthy=False, detail=f"{type(e).__name__}: {e}")

    @engine_method
    async def synthesize(
        self,
        text: str,
        voice_id: str = "English_Graceful_Lady",
        model: str = "speech-2.8-hd",
        language_boost: str = "auto",
        output_format: str = "mp3",
        speed: float = 1.0,
        emotion: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Text-to-speech. Returns dict with `audio_url` (hex or url depending on output_format).

        If `output_format="url"`, returns `{"audio_url": "https://..."}` (24h TTL).
        If `output_format="hex"`, returns `{"audio_hex": "..."}` plus length metadata.
        """
        if not text:
            raise EngineError("text is required")
        if len(text) > 10_000:
            raise EngineError("text exceeds 10,000 chars")
        api_key = self._resolve_key()
        client = await self._client()
        payload: Dict[str, Any] = {
            "model": model,
            "text": text,
            "stream": False,
            "output_format": output_format,
            "voice_setting": {
                "voice_id": voice_id,
                "speed": max(0.5, min(2.0, speed)),
                "vol": 1.0,
                "pitch": 0,
            },
            "audio_setting": {
                "sample_rate": 32000,
                "bitrate": 128000,
                "format": output_format if output_format in ("mp3", "wav", "flac", "pcm") else "mp3",
                "channel": 1,
            },
            "language_boost": language_boost,
        }
        if emotion:
            payload["voice_setting"]["emotion"] = emotion
        r = await client.post(
            f"{self.base_url}/v1/t2a_v2",
            headers=self._headers(api_key),
            json=payload,
        )
        if r.status_code >= 400:
            raise EngineError(f"MiniMax TTS error {r.status_code}: {r.text[:500]}")
        return r.json()

    @engine_method
    async def list_voices(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available voices. Returns list of {voice_id, language, gender, style}."""
        api_key = self._resolve_key()
        client = await self._client()
        params: Dict[str, Any] = {}
        if category:
            params["category"] = category
        r = await client.get(
            f"{self.base_url}/v1/voices",
            headers=self._headers(api_key),
            params=params,
        )
        if r.status_code >= 400:
            raise EngineError(f"MiniMax voices error {r.status_code}: {r.text[:500]}")
        data = r.json()
        # Normalize: API returns various shapes; coalesce to list of dicts
        if isinstance(data, dict) and "voices" in data:
            return data["voices"]
        if isinstance(data, list):
            return data
        return []

    @engine_method
    async def clone_voice(
        self,
        audio_file_path: str,
        voice_name: str,
        sample_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Rapid voice clone from an audio file (mp3/wav, 10s-5min)."""
        import os as _os
        if not _os.path.exists(audio_file_path):
            raise EngineError(f"audio file not found: {audio_file_path}")
        api_key = self._resolve_key()
        client = await self._client()
        with open(audio_file_path, "rb") as f:
            files = {"audio": (audio_file_path, f, "audio/mpeg")}
            data_form = {"name": voice_name}
            if sample_text:
                data_form["sample_text"] = sample_text
            r = await client.post(
                f"{self.base_url}/v1/voice_clone",
                headers={"Authorization": f"Bearer {api_key}"},
                files=files,
                data=data_form,
            )
        if r.status_code >= 400:
            raise EngineError(f"MiniMax clone error {r.status_code}: {r.text[:500]}")
        return r.json()

    @engine_method
    async def design_voice(
        self,
        description: str,
        voice_name: str,
    ) -> Dict[str, Any]:
        """Generate a new voice from a text description (e.g. 'deep British male, 40s')."""
        if not description or not voice_name:
            raise EngineError("description and voice_name are required")
        api_key = self._resolve_key()
        client = await self._client()
        r = await client.post(
            f"{self.base_url}/v1/voice_design",
            headers=self._headers(api_key),
            json={"description": description, "name": voice_name},
        )
        if r.status_code >= 400:
            raise EngineError(f"MiniMax voice design error {r.status_code}: {r.text[:500]}")
        return r.json()


__all__ = [
    "MiniMaxSpeechEngine",
    "DEFAULT_VOICES",
    "LANGUAGE_BOOST_OPTIONS",
]
