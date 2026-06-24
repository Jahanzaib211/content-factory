"""
STT (speech-to-text) engines.

Two providers:
  - FasterWhisperLocalEngine: runs faster-whisper (CTranslate2, INT8) locally on CPU/GPU.
    99 languages, word-level timestamps, 4x faster than OpenAI Whisper. 1.5GB VRAM at large-v3.
  - MiniMaxSttEngine: stub for MiniMax's ASR API (when available; placeholder until
    MiniMax exposes an ASR endpoint, then we drop in httpx calls like the other engines).

Default = faster-whisper (local, free, no API key). Falls back to MiniMax ASR stub
when explicitly requested via the engine picker.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional

from .base import BaseEngine, EngineCapability, EngineHealth, EngineResult, engine_method, EngineError

log = logging.getLogger(__name__)


class FasterWhisperLocalEngine(BaseEngine):
    provider_id = "faster-whisper"
    display_name = "faster-whisper (local, 99 languages, word-level)"
    capability = EngineCapability.STT
    cost_hint = "Free (local CPU/GPU)"
    hardware_hint = "1.5GB VRAM @ large-v3 INT8, or CPU"
    requires_key = False
    key_env_var = None

    def __init__(self, model_size: str = "large-v3", device: str = "auto", compute_type: str = "int8") -> None:
        self.model_size = os.getenv("WHISPER_MODEL", model_size)
        self.device = os.getenv("WHISPER_DEVICE", device)
        self.compute_type = os.getenv("WHISPER_COMPUTE_TYPE", compute_type)
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel  # type: ignore
            except ImportError as e:
                raise EngineError(
                    "faster-whisper not installed. `pip install faster-whisper`"
                ) from e
            log.info(
                f"Loading faster-whisper {self.model_size} on {self.device} ({self.compute_type})..."
            )
            self._model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
        return self._model

    async def health(self) -> EngineHealth:
        try:
            start = time.perf_counter()
            self._ensure_model()
            return EngineHealth(healthy=True, detail=f"model={self.model_size}", latency_ms=(time.perf_counter() - start) * 1000)
        except Exception as e:
            return EngineHealth(healthy=False, detail=f"{type(e).__name__}: {e}")

    @engine_method
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        word_timestamps: bool = True,
        vad_filter: bool = True,
    ) -> Dict[str, Any]:
        """Transcribe an audio file. Returns dict with `text`, `language`, `segments`.

        `segments` is a list of dicts: {start, end, text, words?}.
        """
        import os as _os
        if not _os.path.exists(audio_path):
            raise EngineError(f"audio file not found: {audio_path}")
        model = self._ensure_model()
        segments_iter, info = model.transcribe(
            audio_path, language=language, word_timestamps=word_timestamps, vad_filter=vad_filter
        )
        out_segments: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []
        for seg in segments_iter:
            words = None
            if word_timestamps and getattr(seg, "words", None):
                words = [{"start": w.start, "end": w.end, "word": w.word, "probability": w.probability} for w in seg.words]
            out_segments.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text,
                "words": words,
            })
            full_text_parts.append(seg.text.strip())
        return {
            "text": " ".join(full_text_parts).strip(),
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
            "segments": out_segments,
        }


class MiniMaxSttEngine(BaseEngine):
    """Placeholder for MiniMax's STT API. Drop in httpx calls when MiniMax exposes one.

    Currently returns EngineError so the engine picker can show "no key" / "not available"
    states without breaking the registry.
    """
    provider_id = "minimax"
    display_name = "MiniMax ASR (coming soon)"
    capability = EngineCapability.STT
    cost_hint = "TBD"
    hardware_hint = "cloud"
    requires_key = True
    key_env_var = "MINIMAX_API_KEY"

    async def health(self) -> EngineHealth:
        return EngineHealth(healthy=False, detail="MiniMax STT API not yet exposed by provider; use faster-whisper local.")

    @engine_method
    def transcribe(self, audio_path: str, **kwargs: Any) -> Dict[str, Any]:
        raise EngineError("MiniMax STT is not yet available; use faster-whisper local engine.")


__all__ = ["FasterWhisperLocalEngine", "MiniMaxSttEngine"]
