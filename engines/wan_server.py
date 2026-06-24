"""
Local Wan 2.1 video generation engine (CPU/CUDA offload).

Wraps the Wan 2.1 model for image-to-video and text-to-video. Designed
to run in the dedicated `cf-wan-video` Docker service (see
docker-compose.yml) so its heavy CUDA context doesn't fight the
backend for VRAM.

Endpoint exposed: POST /generate
  body: {"prompt": str, "image_url"?: str, "duration": int, "size": "1280*720"}
  returns: {"task_id": str}

Status endpoint: GET /status/{task_id}
  returns: {"status": "Preparing|Queueing|Processing|Success|Fail", "file_id"?: str}

Download endpoint: GET /download/{file_id}
  returns: video/mp4 bytes
"""
from __future__ import annotations

import argparse
import logging
import os
import time
import uuid
from typing import Any, Dict, Optional

log = logging.getLogger(__name__)

# In-memory task store (single-process; production would use Redis)
_TASKS: Dict[str, Dict[str, Any]] = {}


def _process_task(task_id: str, prompt: str, image_url: Optional[str], duration: int, size: str) -> None:
    """Run the actual Wan 2.1 inference using diffusers."""
    _TASKS[task_id]["status"] = "Processing"
    _TASKS[task_id]["started_at"] = time.time()
    try:
        import torch
        from diffusers import WanPipeline, WanImageToVideoPipeline
        from diffusers.utils import export_to_video, load_image

        log.info(f"[wan] task {task_id}: prompt='{prompt[:50]}' size={size} duration={duration}")

        # Parse size
        width, height = [int(x) for x in size.split("*")]

        # Load model (cached after first load)
        global _wan_model, _wan_i2v_model
        if image_url:
            if _wan_i2v_model is None:
                log.info("[wan] Loading Wan 2.1 I2V model...")
                _wan_i2v_model = WanImageToVideoPipeline.from_pretrained(
                    "Wan-AI/Wan2.1-I2V-14B-720P",
                    torch_dtype=torch.bfloat16,
                )
                if torch.cuda.is_available():
                    _wan_i2v_model.to("cuda")
            model = _wan_i2v_model
            image = load_image(image_url)
            output = model(
                prompt=prompt,
                image=image,
                num_frames=int(duration * 8),  # ~8 fps
                width=width,
                height=height,
                num_inference_steps=50,
            ).frames[0]
        else:
            if _wan_model is None:
                log.info("[wan] Loading Wan 2.1 T2V model...")
                _wan_model = WanPipeline.from_pretrained(
                    "Wan-AI/Wan2.1-T2V-14B-720P",
                    torch_dtype=torch.bfloat16,
                )
                if torch.cuda.is_available():
                    _wan_model.to("cuda")
            model = _wan_model
            output = model(
                prompt=prompt,
                num_frames=int(duration * 8),
                width=width,
                height=height,
                num_inference_steps=50,
            ).frames[0]

        # Save video
        file_id = f"wan_{task_id}"
        out_path = f"/tmp/{file_id}.mp4"
        export_to_video(output, out_path, fps=8)

        _TASKS[task_id].update({
            "status": "Success",
            "file_id": file_id,
            "output_path": out_path,
            "completed_at": time.time(),
        })
    except Exception as e:
        log.exception(f"[wan] task {task_id} failed: {e}")
        _TASKS[task_id].update({"status": "Fail", "error": str(e)})


# Model cache (loaded once, reused across requests)
_wan_model = None
_wan_i2v_model = None


def create_app():  # pragma: no cover - optional FastAPI server
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn

    app = FastAPI(title="Wan 2.1 Local Server", version="0.1.0")

    class GenReq(BaseModel):
        prompt: str
        image_url: Optional[str] = None
        duration: int = 6
        size: str = "1280*720"

    @app.post("/generate")
    def generate(req: GenReq):
        task_id = uuid.uuid4().hex[:12]
        _TASKS[task_id] = {"status": "Queueing", "created_at": time.time(), "request": req.dict()}
        # Run synchronously for the stub; in production this would be a worker
        _process_task(task_id, req.prompt, req.image_url, req.duration, req.size)
        return {"task_id": task_id, **_TASKS[task_id]}

    @app.get("/status/{task_id}")
    def status(task_id: str):
        if task_id not in _TASKS:
            raise HTTPException(404, "task not found")
        return _TASKS[task_id]

    return app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8003)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()
    import uvicorn
    app = create_app()
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
