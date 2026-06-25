"""
Computer Vision engines — face detection, scene detection, object tracking.

Wraps existing tools (MediaPipe, YOLOv8, PySceneDetect) as engine abstractions
so the pipeline can use them through the engine registry.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional

from .base import BaseEngine, EngineCapability, EngineHealth, EngineResult, engine_method, EngineError

log = logging.getLogger(__name__)


class MediaPipeFaceEngine(BaseEngine):
    """Face detection using MediaPipe (local, free, fast)."""
    provider_id = "mediapipe"
    display_name = "MediaPipe Face Detection (local, free)"
    capability = EngineCapability.FACE_DETECT
    cost_hint = "Free (local CPU/GPU)"
    hardware_hint = "any"
    requires_key = False
    key_env_var = None

    def __init__(self) -> None:
        self._detector = None

    def _ensure_model(self):
        if self._detector is None:
            try:
                import mediapipe as mp
                self._detector = mp.solutions.face_detection.FaceDetection(
                    model_selection=1, min_detection_confidence=0.5
                )
            except ImportError as e:
                raise EngineError("mediapipe not installed") from e
        return self._detector

    async def health(self) -> EngineHealth:
        try:
            self._ensure_model()
            return EngineHealth(healthy=True, detail="MediaPipe face detection ready")
        except Exception as e:
            return EngineHealth(healthy=False, detail=f"{type(e).__name__}: {e}")

    @engine_method
    async def detect_faces(
        self,
        image_path: str,
        min_confidence: float = 0.5,
    ) -> Dict[str, Any]:
        """Detect faces in an image. Returns list of bounding boxes."""
        if not os.path.exists(image_path):
            raise EngineError(f"image not found: {image_path}")

        import cv2
        detector = self._ensure_model()
        img = cv2.imread(image_path)
        if img is None:
            raise EngineError(f"failed to read image: {image_path}")

        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = detector.process(rgb)

        faces = []
        if results.detections:
            h, w = img.shape[:2]
            for det in results.detections:
                bbox = det.location_data.relative_bounding_box
                faces.append({
                    "x": int(bbox.xmin * w),
                    "y": int(bbox.ymin * h),
                    "width": int(bbox.width * w),
                    "height": int(bbox.height * h),
                    "confidence": det.score[0],
                })

        return {
            "face_count": len(faces),
            "faces": faces,
            "image_width": img.shape[1],
            "image_height": img.shape[0],
        }


class SceneDetectEngine(BaseEngine):
    """Scene boundary detection using PySceneDetect (local, free)."""
    provider_id = "scenedetect"
    display_name = "PySceneDetect (local, free)"
    capability = EngineCapability.SCENE_DETECT
    cost_hint = "Free (local CPU)"
    hardware_hint = "any"
    requires_key = False
    key_env_var = None

    async def health(self) -> EngineHealth:
        try:
            from scenedetect import open_video
            return EngineHealth(healthy=True, detail="PySceneDetect ready")
        except ImportError as e:
            return EngineHealth(healthy=False, detail=f"scenedetect not installed: {e}")

    @engine_method
    async def detect_scenes(
        self,
        video_path: str,
        threshold: float = 27.0,
        min_scene_len: float = 0.5,
    ) -> Dict[str, Any]:
        """Detect scene boundaries in a video."""
        if not os.path.exists(video_path):
            raise EngineError(f"video not found: {video_path}")

        try:
            from scenedetect import open_video, SceneManager
            from scenedetect.detectors import ContentDetector
        except ImportError as e:
            raise EngineError("scenedetect not installed") from e

        video = open_video(video_path)
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=threshold))
        scene_manager.detect_scenes(video)
        scene_list = scene_manager.get_scene_list()

        scenes = []
        for i, (start, end) in enumerate(scene_list):
            scenes.append({
                "scene_number": i + 1,
                "start_time": start.get_seconds(),
                "end_time": end.get_seconds(),
                "duration": (end - start).get_seconds(),
            })

        return {
            "scene_count": len(scenes),
            "scenes": scenes,
            "video_path": video_path,
        }


class YOLOObjectEngine(BaseEngine):
    """Object detection using YOLOv8/Ultralytics (local, free)."""
    provider_id = "yolov8"
    display_name = "YOLOv8 Object Detection (local, free)"
    capability = EngineCapability.OBJECT_TRACK
    cost_hint = "Free (local CPU/GPU)"
    hardware_hint = "1.5GB VRAM for yolov8n"
    requires_key = False
    key_env_var = None

    def __init__(self) -> None:
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            try:
                from ultralytics import YOLO
                self._model = YOLO("yolov8n.pt")
            except ImportError as e:
                raise EngineError("ultralytics not installed") from e
        return self._model

    async def health(self) -> EngineHealth:
        try:
            self._ensure_model()
            return EngineHealth(healthy=True, detail="YOLOv8n ready")
        except Exception as e:
            return EngineHealth(healthy=False, detail=f"{type(e).__name__}: {e}")

    @engine_method
    async def detect_objects(
        self,
        image_path: str,
        confidence: float = 0.5,
    ) -> Dict[str, Any]:
        """Detect objects in an image using YOLOv8."""
        if not os.path.exists(image_path):
            raise EngineError(f"image not found: {image_path}")

        model = self._ensure_model()
        results = model(image_path, conf=confidence, verbose=False)

        objects = []
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                objects.append({
                    "class_id": cls_id,
                    "class_name": model.names[cls_id],
                    "confidence": float(box.conf[0]),
                    "bbox": {
                        "x": int(box.xyxy[0][0]),
                        "y": int(box.xyxy[0][1]),
                        "width": int(box.xyxy[0][2] - box.xyxy[0][0]),
                        "height": int(box.xyxy[0][3] - box.xyxy[0][1]),
                    },
                })

        return {
            "object_count": len(objects),
            "objects": objects,
        }


__all__ = ["MediaPipeFaceEngine", "SceneDetectEngine", "YOLOObjectEngine"]
