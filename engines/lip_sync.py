"""
Local Lip-Sync engines — Wav2Lip and MuseTalk.

Free, local lip-sync alternatives to paid cloud services.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional

from .base import BaseEngine, EngineCapability, EngineHealth, EngineResult, engine_method, EngineError

log = logging.getLogger(__name__)

WAV2LIP_PATH = os.getenv("WAV2LIP_PATH", "/opt/wav2lip")
MUSETALK_URL = os.getenv("MUSETALK_URL", "http://musetalk:7860")


class Wav2LipEngine(BaseEngine):
    """Wav2Lip — free, local lip-sync from audio + face image/video."""
    provider_id = "wav2lip"
    display_name = "Wav2Lip (local, free)"
    capability = EngineCapability.LIP_SYNC
    cost_hint = "Free (local GPU)"
    hardware_hint = "2GB+ VRAM"
    requires_key = False
    key_env_var = None

    async def health(self) -> EngineHealth:
        if os.path.isdir(WAV2LIP_PATH):
            return EngineHealth(healthy=True, detail=f"Wav2Lip at {WAV2LIP_PATH}")
        return EngineHealth(healthy=False, detail=f"Wav2Lip not found at {WAV2LIP_PATH}")

    @engine_method
    async def lip_sync(
        self,
        face_path: str,
        audio_path: str,
        output: Optional[str] = None,
        smooth: bool = True,
    ) -> Dict[str, Any]:
        """Apply lip-sync to a face image/video using Wav2Lip."""
        import subprocess
        import uuid

        if not os.path.exists(face_path):
            raise EngineError(f"face file not found: {face_path}")
        if not os.path.exists(audio_path):
            raise EngineError(f"audio file not found: {audio_path}")

        if not output:
            output = f"/tmp/wav2lip_{uuid.uuid4().hex[:8]}.mp4"

        checkpoint = os.path.join(WAV2LIP_PATH, "wav2lip_gan.pth")
        if not os.path.exists(checkpoint):
            checkpoint = os.path.join(WAV2LIP_PATH, "models", "wav2lip_gan.pth")

        cmd = [
            "python", os.path.join(WAV2LIP_PATH, "inference.py"),
            "--checkpoint_path", checkpoint,
            "--face", face_path,
            "--audio", audio_path,
            "--outfile", output,
        ]
        if smooth:
            cmd.extend(["--pads", "0", "10", "0", "0"])

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if proc.returncode != 0:
            raise EngineError(f"Wav2Lip failed: {proc.stderr[:300]}")

        if not os.path.exists(output):
            raise EngineError("Wav2Lip produced no output file")

        return {
            "output_path": output,
            "face_path": face_path,
            "audio_path": audio_path,
        }


class MuseTalkEngine(BaseEngine):
    """MuseTalk — real-time lip-sync via API (self-hosted)."""
    provider_id = "musetalk"
    display_name = "MuseTalk (self-hosted, free)"
    capability = EngineCapability.LIP_SYNC
    cost_hint = "Free (self-hosted)"
    hardware_hint = "4GB+ VRAM"
    requires_key = False
    key_env_var = None

    async def health(self) -> EngineHealth:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{MUSETALK_URL}/health")
                if r.status_code == 200:
                    return EngineHealth(healthy=True, detail=f"MuseTalk at {MUSETALK_URL}")
                return EngineHealth(healthy=False, detail=f"MuseTalk returned {r.status_code}")
        except Exception as e:
            return EngineHealth(healthy=False, detail=f"MuseTalk not reachable: {e}")

    @engine_method
    async def lip_sync(
        self,
        face_path: str,
        audio_path: str,
        output: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Apply lip-sync using MuseTalk API."""
        import httpx
        import uuid

        if not output:
            output = f"/tmp/musetalk_{uuid.uuid4().hex[:8]}.mp4"

        async with httpx.AsyncClient(timeout=300.0) as client:
            with open(face_path, "rb") as face_f, open(audio_path, "rb") as audio_f:
                r = await client.post(
                    f"{MUSETALK_URL}/inference",
                    files={
                        "face": ("face.mp4", face_f, "video/mp4"),
                        "audio": ("audio.wav", audio_f, "audio/wav"),
                    },
                )
            if r.status_code != 200:
                raise EngineError(f"MuseTalk failed: {r.text[:200]}")

            with open(output, "wb") as f:
                f.write(r.content)

        return {
            "output_path": output,
            "face_path": face_path,
            "audio_path": audio_path,
        }


__all__ = ["Wav2LipEngine", "MuseTalkEngine"]
