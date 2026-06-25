"""
Speaker Diarization engine — pyannote-audio.

Identifies who spoke when in an audio/video file.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from .base import BaseEngine, EngineCapability, EngineHealth, EngineResult, engine_method, EngineError

log = logging.getLogger(__name__)


class PyannoteDiarizeEngine(BaseEngine):
    """Speaker diarization using pyannote-audio (local, free for non-commercial)."""
    provider_id = "pyannote"
    display_name = "pyannote-audio (local, free)"
    capability = EngineCapability.SPEAKER_DIARIZE
    cost_hint = "Free (local GPU, non-commercial)"
    hardware_hint = "2GB+ VRAM"
    requires_key = False
    key_env_var = None

    def __init__(self) -> None:
        self._pipeline = None
        self._hf_token = os.getenv("HF_TOKEN", os.getenv("HUGGING_FACE_HUB_TOKEN", ""))

    def _ensure_pipeline(self):
        if self._pipeline is None:
            try:
                from pyannote.audio import Pipeline
                log.info("[pyannote] Loading diarization pipeline...")
                self._pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=self._hf_token or None,
                )
                import torch
                if torch.cuda.is_available():
                    self._pipeline.to(torch.device("cuda"))
                log.info("[pyannote] Diarization pipeline loaded")
            except ImportError as e:
                raise EngineError("pyannote.audio not installed: pip install pyannote.audio") from e
        return self._pipeline

    async def health(self) -> EngineHealth:
        if not self._hf_token:
            return EngineHealth(healthy=False, detail="HF_TOKEN not set (required for pyannote models)")
        try:
            self._ensure_pipeline()
            return EngineHealth(healthy=True, detail="pyannote diarization ready")
        except Exception as e:
            return EngineHealth(healthy=False, detail=f"{type(e).__name__}: {e}")

    @engine_method
    async def diarize(
        self,
        audio_path: str,
        num_speakers: Optional[int] = None,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Identify speakers and their time segments in audio."""
        if not os.path.exists(audio_path):
            raise EngineError(f"audio file not found: {audio_path}")

        pipeline = self._ensure_pipeline()

        # Build kwargs
        kwargs = {}
        if num_speakers is not None:
            kwargs["num_speakers"] = num_speakers
        if min_speakers is not None:
            kwargs["min_speakers"] = min_speakers
        if max_speakers is not None:
            kwargs["max_speakers"] = max_speakers

        diarization = pipeline(audio_path, **kwargs)

        # Convert to structured output
        segments = []
        speaker_times = {}
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            seg = {
                "start": round(turn.start, 3),
                "end": round(turn.end, 3),
                "duration": round(turn.end - turn.start, 3),
                "speaker": speaker,
            }
            segments.append(seg)
            speaker_times[speaker] = speaker_times.get(speaker, 0) + seg["duration"]

        return {
            "segment_count": len(segments),
            "speaker_count": len(speaker_times),
            "segments": segments,
            "speaker_times": speaker_times,
        }


__all__ = ["PyannoteDiarizeEngine"]
