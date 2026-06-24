"""
Local CosyVoice TTS + voice clone server.

Wraps CosyVoice 0.5B / 300M models for fast local TTS in 9 languages
with cross-lingual zero-shot voice cloning. Designed to run in the
dedicated `cf-cosyvoice` Docker service so its CUDA context doesn't
fight the backend for VRAM.

Endpoints:
  POST /tts  body: {"text": str, "voice_id"?: str, "language"?: str, "speed"?: float}
        -> {"audio_path": str, "duration_ms": float}
  POST /clone  body: multipart with audio file + voice_name
        -> {"voice_id": str, "out_path": str}
  GET  /voices
        -> {"voices": [{voice_id, name, language, gender, style}]}
"""
from __future__ import annotations

import argparse
import logging
import os
import time
import uuid
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

# In-memory voice library
_VOICES: Dict[str, Dict[str, Any]] = {}
MODEL_DIR = os.getenv("COSYVOICE_MODEL_DIR", "/models/cosyvoice")


def create_app():  # pragma: no cover - optional FastAPI server
    from fastapi import FastAPI, HTTPException, UploadFile, File, Form
    from pydantic import BaseModel
    import uvicorn

    app = FastAPI(title="CosyVoice Local Server", version="0.1.0")

    class TTSReq(BaseModel):
        text: str
        voice_id: Optional[str] = None
        language: str = "auto"
        speed: float = 1.0

    @app.post("/tts")
    def tts(req: TTSReq):
        if not os.path.isdir(MODEL_DIR):
            raise HTTPException(503, f"CosyVoice model not found at {MODEL_DIR}")
        try:
            from cosyvoice.cli.cosyvoice import CosyVoice2
            import torchaudio

            cv = CosyVoice2(MODEL_DIR, load_jit=False, load_trt=False, fp16=True)

            # Select speaker preset or use default
            speaker = req.voice_id or "English_Graceful_Lady"
            if req.language and req.language != "auto":
                speaker = f"{req.language}_{speaker.split('_')[-1]}" if '_' in speaker else speaker

            results = list(cv.inference_sft(req.text, speaker, speed=req.speed))
            if not results:
                raise HTTPException(500, "CosyVoice returned empty results")

            # Save the first result
            out = f"/tmp/cosyvoice_{uuid.uuid4().hex[:8]}.wav"
            torchaudio.save(out, results[0]["tts_speech"], 22050)
            duration_ms = results[0]["tts_speech"].shape[1] / 22050 * 1000
            return {"audio_path": out, "duration_ms": duration_ms, "model": MODEL_DIR}
        except ImportError as e:
            raise HTTPException(503, f"CosyVoice dependencies not installed: {e}")
        except Exception as e:
            log.exception(f"[cosyvoice] TTS failed: {e}")
            raise HTTPException(500, f"TTS generation failed: {e}")

    @app.post("/clone")
    async def clone(name: str = Form(...), file: UploadFile = File(...)):
        if not os.path.isdir(MODEL_DIR):
            raise HTTPException(503, f"CosyVoice model not found at {MODEL_DIR}")
        try:
            from cosyvoice.cli.cosyvoice import CosyVoice2
            import torchaudio

            # Save uploaded audio
            upload_path = f"/tmp/cosyvoice_clone_{uuid.uuid4().hex[:8]}.wav"
            content = await file.read()
            with open(upload_path, "wb") as f:
                f.write(content)

            cv = CosyVoice2(MODEL_DIR, load_jit=False, load_trt=False, fp16=True)

            # Load reference audio
            speech, sr = torchaudio.load(upload_path)
            if sr != 16000:
                speech = torchaudio.functional.resample(speech, sr, 16000)

            # Run zero-shot voice cloning
            results = list(cv.inference_zero_shot(
                req.text if hasattr(req, 'text') else "Hello, this is a test.",
                speech,
                name,
                language="auto",
            ))
            if not results:
                raise HTTPException(500, "Voice cloning returned empty results")

            # Save cloned audio
            out = f"/tmp/cosyvoice_cloned_{uuid.uuid4().hex[:8]}.wav"
            torchaudio.save(out, results[0]["tts_speech"], 22050)

            voice_id = name.lower().replace(" ", "_")
            _VOICES[voice_id] = {
                "voice_id": voice_id,
                "name": name,
                "language": "multilingual",
                "gender": "neutral",
                "style": "cloned",
                "created_at": time.time(),
            }
            return {"voice_id": voice_id, "name": name, "audio_path": out, "model": MODEL_DIR}
        except ImportError as e:
            raise HTTPException(503, f"CosyVoice dependencies not installed: {e}")
        except Exception as e:
            log.exception(f"[cosyvoice] Clone failed: {e}")
            raise HTTPException(500, f"Voice cloning failed: {e}")

    @app.get("/voices")
    def voices() -> Dict[str, List[Dict[str, Any]]]:
        return {"voices": list(_VOICES.values())}

    return app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8004)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()
    import uvicorn
    app = create_app()
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
