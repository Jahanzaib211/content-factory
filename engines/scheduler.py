"""
Scheduler Engine — smart scheduling, recurring posts, best-time optimization.

Provides:
  - TimeOptimizer: find best posting times per platform
  - RecurringScheduler: cron-style recurring post scheduling
  - PlatformCropper: auto aspect-ratio adaptation per platform

All classes are async.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

log = logging.getLogger(__name__)

SCHEDULER_DIR = os.path.join("output", "scheduler")
os.makedirs(SCHEDULER_DIR, exist_ok=True)


# ── Best Time to Post ────────────────────────────────────────────────


@dataclass
class PostingSlot:
    platform: str
    day_of_week: str  # "monday", "tuesday", etc.
    hour: int  # 0-23 in user's timezone
    timezone: str
    confidence: float  # 0.0-1.0
    reason: str


class TimeOptimizer:
    """Find optimal posting times based on platform data and channel analytics."""

    # Platform-specific best times (research-backed defaults)
    DEFAULT_TIMES = {
        "youtube": [
            {"day": "friday", "hour": 15, "confidence": 0.8, "reason": "Pre-weekend viewing peak"},
            {"day": "saturday", "hour": 10, "confidence": 0.75, "reason": "Weekend morning browse"},
            {"day": "thursday", "hour": 14, "confidence": 0.7, "reason": "Pre-Friday engagement"},
            {"day": "tuesday", "hour": 16, "confidence": 0.65, "reason": "Mid-week afternoon"},
            {"day": "wednesday", "hour": 12, "confidence": 0.6, "reason": "Lunch break views"},
        ],
        "tiktok": [
            {"day": "tuesday", "hour": 10, "confidence": 0.85, "reason": "Morning commute scroll"},
            {"day": "thursday", "hour": 12, "confidence": 0.8, "reason": "Lunch break peak"},
            {"day": "friday", "hour": 17, "confidence": 0.75, "reason": "End-of-week wind down"},
            {"day": "saturday", "hour": 11, "confidence": 0.7, "reason": "Weekend leisure"},
            {"day": "sunday", "hour": 19, "confidence": 0.65, "reason": "Sunday evening scroll"},
        ],
        "instagram": [
            {"day": "monday", "hour": 11, "confidence": 0.8, "reason": "Monday motivation"},
            {"day": "wednesday", "hour": 14, "confidence": 0.75, "reason": "Mid-week engagement"},
            {"day": "friday", "hour": 13, "confidence": 0.7, "reason": "Pre-weekend buzz"},
            {"day": "saturday", "hour": 10, "confidence": 0.65, "reason": "Weekend morning"},
            {"day": "sunday", "hour": 20, "confidence": 0.6, "reason": "Sunday evening prep"},
        ],
    }

    async def get_best_times(
        self, platform: str, count: int = 5, timezone: str = "UTC"
    ) -> List[PostingSlot]:
        """Get best posting times for a platform."""
        defaults = self.DEFAULT_TIMES.get(platform, self.DEFAULT_TIMES["youtube"])

        # If we have channel analytics, refine with real data
        refined = await self._refine_with_analytics(platform, defaults)

        return [
            PostingSlot(
                platform=platform,
                day_of_week=s["day"],
                hour=s["hour"],
                timezone=timezone,
                confidence=s["confidence"],
                reason=s["reason"],
            )
            for s in refined[:count]
        ]

    async def _refine_with_analytics(
        self, platform: str, defaults: List[Dict]
    ) -> List[Dict]:
        """Refine default times with real channel analytics if available."""
        try:
            from engines.analytics import AnalyticsEngine
            analytics = AnalyticsEngine()
            if not analytics.youtube.available:
                return defaults

            # If we have stored metrics, look for patterns
            stored = analytics.store.get_video_metrics(platform)
            if not stored:
                return defaults

            # Basic refinement: boost times that match high-performing videos
            return defaults  # TODO: implement time-based pattern matching
        except Exception:
            return defaults


# ── Recurring Scheduler ──────────────────────────────────────────────


@dataclass
class RecurringSchedule:
    schedule_id: str
    template_id: str
    inputs: Dict[str, Any]
    platforms: List[str]  # ["youtube", "tiktok", "instagram"]
    cron_expression: str  # e.g., "0 9 * * 1,3,5" = Mon/Wed/Fri at 9am
    timezone: str
    enabled: bool = True
    created_at: str = ""
    last_run: str = ""
    next_run: str = ""
    run_count: int = 0


class RecurringScheduler:
    """Server-side recurring post scheduling with cron expressions."""

    def __init__(self):
        self._schedules_file = os.path.join(SCHEDULER_DIR, "recurring.json")
        self._schedules = self._load()

    def _load(self) -> Dict[str, RecurringSchedule]:
        try:
            if os.path.exists(self._schedules_file):
                with open(self._schedules_file) as f:
                    data = json.load(f)
                return {
                    k: RecurringSchedule(**v)
                    for k, v in data.items()
                }
        except Exception:
            pass
        return {}

    def _save(self) -> None:
        try:
            with open(self._schedules_file, "w") as f:
                json.dump(
                    {k: asdict(v) for k, v in self._schedules.items()},
                    f,
                    indent=2,
                    default=str,
                )
        except Exception as e:
            log.warning(f"Scheduler save failed: {e}")

    def create_schedule(
        self,
        template_id: str,
        inputs: Dict[str, Any],
        platforms: List[str],
        cron_expression: str,
        timezone: str = "UTC",
    ) -> RecurringSchedule:
        """Create a new recurring schedule."""
        import uuid
        schedule_id = uuid.uuid4().hex[:12]
        schedule = RecurringSchedule(
            schedule_id=schedule_id,
            template_id=template_id,
            inputs=inputs,
            platforms=platforms,
            cron_expression=cron_expression,
            timezone=timezone,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            next_run=self._calculate_next_run(cron_expression),
        )
        self._schedules[schedule_id] = schedule
        self._save()
        return schedule

    def list_schedules(self) -> List[RecurringSchedule]:
        return list(self._schedules.values())

    def get_schedule(self, schedule_id: str) -> Optional[RecurringSchedule]:
        return self._schedules.get(schedule_id)

    def delete_schedule(self, schedule_id: str) -> bool:
        if schedule_id in self._schedules:
            del self._schedules[schedule_id]
            self._save()
            return True
        return False

    def toggle_schedule(self, schedule_id: str, enabled: bool) -> bool:
        s = self._schedules.get(schedule_id)
        if s:
            s.enabled = enabled
            self._save()
            return True
        return False

    def _calculate_next_run(self, cron_expression: str) -> str:
        """Calculate next run time from cron expression. Simplified implementation."""
        # Parse basic cron: "minute hour day month weekday"
        parts = cron_expression.split()
        if len(parts) < 5:
            return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 3600))

        hour = int(parts[1]) if parts[1] != "*" else 9
        minute = int(parts[0]) if parts[0] != "*" else 0

        # Simple: next occurrence is tomorrow at the specified hour
        import datetime
        now = datetime.datetime.utcnow()
        tomorrow = now + datetime.timedelta(days=1)
        next_run = tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return next_run.strftime("%Y-%m-%dT%H:%M:%SZ")

    def get_due_schedules(self) -> List[RecurringSchedule]:
        """Get schedules that are due for execution."""
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        due = []
        for s in self._schedules.values():
            if s.enabled and s.next_run and s.next_run <= now:
                due.append(s)
        return due


# ── Platform Cropper ─────────────────────────────────────────────────


class PlatformCropper:
    """Auto aspect-ratio adaptation per platform using ffmpeg."""

    ASPECT_RATIOS = {
        "tiktok": {"width": 1080, "height": 1920, "label": "9:16"},
        "youtube_shorts": {"width": 1080, "height": 1920, "label": "9:16"},
        "youtube": {"width": 1920, "height": 1080, "label": "16:9"},
        "instagram_reels": {"width": 1080, "height": 1920, "label": "9:16"},
        "instagram_post": {"width": 1080, "height": 1080, "label": "1:1"},
        "instagram_stories": {"width": 1080, "height": 1920, "label": "9:16"},
    }

    def crop_for_platform(
        self, input_path: str, platform: str, output_path: str
    ) -> str:
        """Crop/resize video for a specific platform. Returns output path."""
        spec = self.ASPECT_RATIOS.get(platform, self.ASPECT_RATIOS["tiktok"])
        w, h = spec["width"], spec["height"]

        # Build ffmpeg filter
        vf = f"crop=min(iw\\,ih*{w}/{h}):min(ih\\,iw*{h}/{w}),scale={w}:{h}"

        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
            "-i", input_path,
            "-vf", vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "copy",
            output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(f"Crop failed: {result.stderr[:300]}")
        return output_path

    def crop_for_all_platforms(
        self, input_path: str, output_dir: str, platforms: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """Generate cropped versions for multiple platforms."""
        if platforms is None:
            platforms = ["tiktok", "youtube", "instagram_post"]

        results = {}
        for platform in platforms:
            out_path = os.path.join(output_dir, f"{platform}.mp4")
            try:
                self.crop_for_platform(input_path, platform, out_path)
                results[platform] = out_path
            except Exception as e:
                log.warning(f"Crop for {platform} failed: {e}")
                results[platform] = f"error: {e}"

        return results


__all__ = [
    "TimeOptimizer",
    "RecurringScheduler",
    "PlatformCropper",
    "PostingSlot",
    "RecurringSchedule",
]
