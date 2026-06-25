"""
Translation engine — wraps translate.py as a pluggable engine.

Supports multiple providers: MiniMax LLM, ElevenLabs dubbing, faster-whisper transcription.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from .base import BaseEngine, EngineCapability, EngineHealth, EngineResult, engine_method, EngineError

log = logging.getLogger(__name__)


class TranslationEngine(BaseEngine):
    """Video translation + dubbing via translate.py pipeline."""
    provider_id = "translate"
    display_name = "Video Translation (multi-provider)"
    capability = EngineCapability.TRANSLATION
    cost_hint = "MiniMax LLM + ElevenLabs dubbing"
    hardware_hint = "cloud"
    requires_key = True
    key_env_var = "MINIMAX_API_KEY"

    async def health(self) -> EngineHealth:
        minimax_key = os.getenv("MINIMAX_API_KEY", "")
        elevenlabs_key = os.getenv("ELEVENLABS_API_KEY", "")
        if minimax_key or elevenlabs_key:
            return EngineHealth(healthy=True, detail="Translation available")
        return EngineHealth(healthy=False, detail="No translation API keys set")

    @engine_method
    async def translate_video(
        self,
        video_path: str,
        target_language: str = "es",
        source_language: str = "en",
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Translate and dub a video to another language."""
        import subprocess
        import uuid

        if not os.path.exists(video_path):
            raise EngineError(f"video not found: {video_path}")

        if not output_dir:
            output_dir = f"/tmp/translate_{uuid.uuid4().hex[:8]}"
        os.makedirs(output_dir, exist_ok=True)

        # Use the existing translate.py pipeline
        minimax_key = os.getenv("MINIMAX_API_KEY", "")
        elevenlabs_key = os.getenv("ELEVENLABS_API_KEY", "")

        if not minimax_key and not elevenlabs_key:
            raise EngineError("No translation API keys set (MINIMAX_API_KEY or ELEVENLABS_API_KEY)")

        try:
            # Import and run the translation pipeline
            from translate import translate_video as _translate
            result = _translate(
                video_path=video_path,
                target_lang=target_language,
                source_lang=source_language,
                minimax_key=minimax_key,
                elevenlabs_key=elevenlabs_key,
                output_dir=output_dir,
            )
            return result
        except ImportError:
            raise EngineError("translate.py module not available")
        except Exception as e:
            raise EngineError(f"Translation failed: {e}")


class ArgosTranslateEngine(BaseEngine):
    """Argos Translate — local, offline translation (no API needed)."""
    provider_id = "argos"
    display_name = "Argos Translate (local, free)"
    capability = EngineCapability.TRANSLATION
    cost_hint = "Free (local CPU)"
    hardware_hint = "any"
    requires_key = False
    key_env_var = None

    def __init__(self) -> None:
        self._translator = None

    def _ensure_translator(self, source_lang: str, target_lang: str):
        try:
            from argostranslate import translate as argos_translate
            installed = argos_translate.get_installed_languages()
            src = next((l for l in installed if l.code == source_lang), None)
            tgt = next((l for l in installed if l.code == target_lang), None)
            if src and tgt:
                return src.get_translation(tgt)
            raise EngineError(f"Language pair {source_lang}->{target_lang} not installed")
        except ImportError as e:
            raise EngineError("argos translate not installed: pip install argostranslate") from e

    async def health(self) -> EngineHealth:
        try:
            from argostranslate import translate as argos_translate
            langs = argos_translate.get_installed_languages()
            return EngineHealth(healthy=True, detail=f"{len(langs)} languages installed")
        except Exception as e:
            return EngineHealth(healthy=False, detail=f"{type(e).__name__}: {e}")

    @engine_method
    async def translate_text(
        self,
        text: str,
        source_lang: str = "en",
        target_lang: str = "es",
    ) -> Dict[str, Any]:
        """Translate text using Argos Translate (local, free)."""
        translation = self._ensure_translator(source_lang, target_lang)
        result = translation.translate(text)
        return {
            "translated_text": result,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "engine": "argos",
        }


__all__ = ["TranslationEngine", "ArgosTranslateEngine"]
