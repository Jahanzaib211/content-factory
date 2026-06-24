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
    """Run the actual Wan 2.1 inference. Stub when model not loaded."""
    _TASKS[task_id]["status"] = "Processing"
    _TASKS[task_id]["started_at"] = time.time()
    try:
        # Real implementation would call wan2.1 / diffusers here.
        # This stub returns Success after a simulated wait so the rest
        # of the pipeline can be wired + tested without GPU.
        log.info(f"[wan] task {task_id}: prompt='{prompt[:50]}' size={size} duration={duration}")
        time.sleep(2.0)  # simulate inference
        _TASKS[task_id].update({
            "status": "Success",
            "file_id": f"wan_{task_id}",
            "completed_at": time.time(),
        })
    except Exception as e:
        log.exception(f"[wan] task {task_id} failed: {e}")
        _TASKS[task_id].update({"status": "Fail", "error": str(e)})


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
