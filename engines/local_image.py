"""
Local Image Generation engines — ComfyUI and Stable Diffusion.

Provides free, local image generation as alternatives to paid cloud APIs.
"""
from __future__ import annotations

import base64
import logging
import os
import time
from typing import Any, Dict, Optional

from .base import BaseEngine, EngineCapability, EngineHealth, EngineResult, engine_method, EngineError

log = logging.getLogger(__name__)

COMFYUI_URL = os.getenv("COMFYUI_URL", "http://comfyui:8188")


class ComfyUIEngine(BaseEngine):
    """ComfyUI image generation — local, free, supports SDXL/SD1.5/Flux."""
    provider_id = "comfyui"
    display_name = "ComfyUI (local, free, SDXL/Flux)"
    capability = EngineCapability.IMAGE
    cost_hint = "Free (local GPU)"
    hardware_hint = "4GB+ VRAM"
    requires_key = False
    key_env_var = None

    def __init__(self) -> None:
        self._base_url = COMFYUI_URL

    async def health(self) -> EngineHealth:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self._base_url}/system_stats")
                if r.status_code == 200:
                    return EngineHealth(healthy=True, detail=f"ComfyUI at {self._base_url}")
                return EngineHealth(healthy=False, detail=f"ComfyUI returned {r.status_code}")
        except Exception as e:
            return EngineHealth(healthy=False, detail=f"ComfyUI not reachable: {e}")

    @engine_method
    async def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 20,
        cfg_scale: float = 7.0,
        seed: int = -1,
        model: str = "sd_xl_base_1.0.safetensors",
        output: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate an image using ComfyUI API."""
        import httpx
        import uuid
        import json

        if not output:
            output = f"/tmp/comfyui_{uuid.uuid4().hex[:8]}.png"

        # Build ComfyUI workflow (simple txt2img)
        workflow = {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed if seed >= 0 else int(time.time()) % (2**32),
                    "steps": steps,
                    "cfg": cfg_scale,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1.0,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0],
                },
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": model},
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": width, "height": height, "batch_size": 1},
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": prompt, "clip": ["4", 1]},
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": negative_prompt, "clip": ["4", 1]},
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "content_factory", "images": ["8", 0]},
            },
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            # Queue prompt
            r = await client.post(f"{self._base_url}/prompt", json={"prompt": workflow})
            if r.status_code != 200:
                raise EngineError(f"ComfyUI queue failed: {r.text[:200]}")

            prompt_id = r.json().get("prompt_id")
            if not prompt_id:
                raise EngineError("ComfyUI returned no prompt_id")

            # Poll for completion
            for _ in range(300):  # 5 min timeout
                await __import__("asyncio").sleep(1.0)
                status_r = await client.get(f"{self._base_url}/history/{prompt_id}")
                if status_r.status_code == 200:
                    history = status_r.json()
                    if prompt_id in history:
                        outputs = history[prompt_id].get("outputs", {})
                        for node_id, node_output in outputs.items():
                            if "images" in node_output:
                                img_info = node_output["images"][0]
                                # Download the image
                                img_r = await client.get(
                                    f"{self._base_url}/view",
                                    params={"filename": img_info["filename"], "subfolder": img_info.get("subfolder", ""), "type": img_info.get("type", "output")},
                                )
                                if img_r.status_code == 200:
                                    with open(output, "wb") as f:
                                        f.write(img_r.content)
                                    return {
                                        "image_path": output,
                                        "width": width,
                                        "height": height,
                                        "prompt": prompt[:100],
                                        "model": model,
                                    }
            raise EngineError("ComfyUI generation timed out")


class LocalDiffusionEngine(BaseEngine):
    """Local Stable Diffusion via diffusers library — free, no API needed."""
    provider_id = "local-diffusion"
    display_name = "Local Diffusion (diffusers, free)"
    capability = EngineCapability.IMAGE
    cost_hint = "Free (local GPU)"
    hardware_hint = "4GB+ VRAM"
    requires_key = False
    key_env_var = None

    def __init__(self) -> None:
        self._pipe = None

    def _ensure_pipe(self):
        if self._pipe is None:
            try:
                import torch
                from diffusers import StableDiffusionXLPipeline
                log.info("[local-diffusion] Loading SDXL pipeline...")
                self._pipe = StableDiffusionXLPipeline.from_pretrained(
                    "stabilityai/stable-diffusion-xl-base-1.0",
                    torch_dtype=torch.float16,
                    use_safetensors=True,
                )
                if torch.cuda.is_available():
                    self._pipe = self._pipe.to("cuda")
                log.info("[local-diffusion] SDXL loaded")
            except ImportError as e:
                raise EngineError("diffusers not installed") from e
        return self._pipe

    async def health(self) -> EngineHealth:
        try:
            self._ensure_pipe()
            return EngineHealth(healthy=True, detail="Local SDXL ready")
        except Exception as e:
            return EngineHealth(healthy=False, detail=f"{type(e).__name__}: {e}")

    @engine_method
    async def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 20,
        cfg_scale: float = 7.0,
        seed: int = -1,
        output: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate an image using local diffusers pipeline."""
        import torch
        import uuid

        if not output:
            output = f"/tmp/diffusion_{uuid.uuid4().hex[:8]}.png"

        pipe = self._ensure_pipe()
        generator = torch.Generator().manual_seed(seed) if seed >= 0 else None

        result = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_inference_steps=steps,
            guidance_scale=cfg_scale,
            generator=generator,
        )
        image = result.images[0]
        image.save(output)

        return {
            "image_path": output,
            "width": width,
            "height": height,
            "prompt": prompt[:100],
            "model": "sdxl-base-1.0",
        }


__all__ = ["ComfyUIEngine", "LocalDiffusionEngine"]
