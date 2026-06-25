"""
Edge TTS Engine — free Microsoft Edge text-to-speech.

Uses Microsoft Edge's online TTS service (no API key required).
400+ voices across 70+ languages. Fast, natural-sounding.

Primary fallback when MiniMax/ElevenLabs are unavailable.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional

from .base import BaseEngine, EngineCapability, EngineHealth, EngineResult, engine_method, EngineError

log = logging.getLogger(__name__)

# Common voice presets (voice_id -> display info)
VOICE_PRESETS = {
    "en-US-GuyNeural": {"language": "English", "gender": "male", "style": "conversational"},
    "en-US-JennyNeural": {"language": "English", "gender": "female", "style": "conversational"},
    "en-US-AriaNeural": {"language": "English", "gender": "female", "style": "narration"},
    "en-US-DavisNeural": {"language": "English", "gender": "male", "style": "narration"},
    "en-US-AndrewNeural": {"language": "English", "gender": "male", "style": "narration"},
    "en-US-EmmaNeural": {"language": "English", "gender": "female", "style": "conversational"},
    "en-GB-SoniaNeural": {"language": "English", "gender": "female", "style": "narration"},
    "en-GB-RyanNeural": {"language": "English", "gender": "male", "style": "narration"},
    "es-ES-ElviraNeural": {"language": "Spanish", "gender": "female", "style": "conversational"},
    "es-ES-AlvaroNeural": {"language": "Spanish", "gender": "male", "style": "conversational"},
    "fr-FR-DeniseNeural": {"language": "French", "gender": "female", "style": "conversational"},
    "fr-FR-HenriNeural": {"language": "French", "gender": "male", "style": "conversational"},
    "de-DE-KatjaNeural": {"language": "German", "gender": "female", "style": "conversational"},
    "de-DE-ConradNeural": {"language": "German", "gender": "male", "style": "conversational"},
    "ja-JP-NanamiNeural": {"language": "Japanese", "gender": "female", "style": "conversational"},
    "ja-JP-KeitaNeural": {"language": "Japanese", "gender": "male", "style": "conversational"},
    "ko-KR-SunHiNeural": {"language": "Korean", "gender": "female", "style": "conversational"},
    "ko-KR-InJoonNeural": {"language": "Korean", "gender": "male", "style": "conversational"},
    "zh-CN-XiaoxiaoNeural": {"language": "Chinese", "gender": "female", "style": "conversational"},
    "zh-CN-YunxiNeural": {"language": "Chinese", "gender": "male", "style": "conversational"},
    "pt-BR-FranciscaNeural": {"language": "Portuguese", "gender": "female", "style": "conversational"},
    "pt-BR-AntonioNeural": {"language": "Portuguese", "gender": "male", "style": "conversational"},
    "hi-IN-SwaraNeural": {"language": "Hindi", "gender": "female", "style": "conversational"},
    "hi-IN-MadhurNeural": {"language": "Hindi", "gender": "male", "style": "conversational"},
    "ar-SA-ZariyahNeural": {"language": "Arabic", "gender": "female", "style": "conversational"},
    "ar-SA-HamedNeural": {"language": "Arabic", "gender": "male", "style": "conversational"},
}


class EdgeTTSEngine(BaseEngine):
    """Microsoft Edge TTS — free, no API key, 400+ voices, 70+ languages."""
    provider_id = "edge-tts"
    display_name = "Edge TTS (free, 400+ voices)"
    capability = EngineCapability.TTS
    cost_hint = "Free forever"
    hardware_hint = "cloud (Microsoft Edge service)"
    requires_key = False
    key_env_var = None

    def __init__(self) -> None:
        self._edge_tts = None

    def _ensure_import(self):
        if self._edge_tts is None:
            try:
                import edge_tts
                self._edge_tts = edge_tts
            except ImportError as e:
                raise EngineError(
                    "edge-tts not installed. `pip install edge-tts`"
                ) from e
        return self._edge_tts

    async def health(self) -> EngineHealth:
        try:
            edge_tts = self._ensure_import()
            # Quick test: list a few voices
            voices = await edge_tts.list_voices()
            if voices:
                return EngineHealth(healthy=True, detail=f"{len(voices)} voices available")
            return EngineHealth(healthy=False, detail="No voices returned")
        except Exception as e:
            return EngineHealth(healthy=False, detail=f"{type(e).__name__}: {e}")

    @engine_method
    async def synthesize(
        self,
        text: str,
        voice: str = "en-US-GuyNeural",
        rate: str = "+0%",
        volume: str = "+0%",
        pitch: str = "+0Hz",
        output: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Synthesize speech from text using Edge TTS.

        Args:
            text: Text to synthesize
            voice: Voice ID (e.g., "en-US-GuyNeural")
            rate: Speech rate adjustment (e.g., "+10%", "-20%")
            volume: Volume adjustment (e.g., "+0%")
            pitch: Pitch adjustment (e.g., "+0Hz", "+50Hz")
            output: Output file path (auto-generated if None)

        Returns:
            Dict with audio_path, duration_ms, voice, text
        """
        edge_tts = self._ensure_import()

        if not text.strip():
            raise EngineError("text cannot be empty")

        if not output:
            import uuid
            output = f"/tmp/edge_tts_{uuid.uuid4().hex[:8]}.mp3"

        communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume, pitch=pitch)
        await communicate.save(output)

        # Get duration using pydub or ffprobe
        duration_ms = 0
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_mp3(output)
            duration_ms = len(audio)
        except Exception:
            # Fallback: estimate from text length (~150 words/min)
            words = len(text.split())
            duration_ms = int(words / 2.5 * 1000)

        return {
            "audio_path": output,
            "duration_ms": duration_ms,
            "voice": voice,
            "text": text[:100],
        }

    @engine_method
    async def list_voices(
        self,
        language: Optional[str] = None,
        gender: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List available voices, optionally filtered by language/gender."""
        edge_tts = self._ensure_import()
        voices = await edge_tts.list_voices()

        result = []
        for v in voices:
            voice_id = v.get("ShortName", "")
            locale = v.get("Locale", "")
            gender_val = v.get("Gender", "")

            # Apply filters
            if language and language.lower() not in locale.lower():
                continue
            if gender and gender.lower() != gender_val.lower():
                continue

            result.append({
                "voice_id": voice_id,
                "name": v.get("FriendlyName", voice_id),
                "language": locale,
                "gender": gender_val,
                "locale": locale,
            })

        return result

    def get_preset_voices(self) -> List[Dict[str, Any]]:
        """Get curated preset voices for quick selection."""
        return [
            {"voice_id": k, **v}
            for k, v in VOICE_PRESETS.items()
        ]


__all__ = ["EdgeTTSEngine", "VOICE_PRESETS"]
