"""
Analytics Engine — performance tracking across platforms.

Polls YouTube/TikTok/Instagram APIs for video metrics:
  - Views, likes, comments, shares, subscriber gain
  - Performance scoring per video
  - A/B testing results

All classes are async.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

log = logging.getLogger(__name__)

ANALYTICS_DIR = os.path.join("output", "analytics")
os.makedirs(ANALYTICS_DIR, exist_ok=True)


@dataclass
class VideoMetrics:
    platform: str
    video_id: str
    title: str = ""
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    subscribers_gained: int = 0
    watch_time_minutes: float = 0.0
    ctr: float = 0.0  # click-through rate
    retention_pct: float = 0.0  # average view duration %
    score: float = 0.0  # 0-100 performance score
    fetched_at: str = ""
    url: str = ""


@dataclass
class ChannelMetrics:
    platform: str
    channel_id: str
    channel_name: str = ""
    subscribers: int = 0
    total_views: int = 0
    total_videos: int = 0
    avg_views_per_video: float = 0.0
    growth_rate: float = 0.0  # % change over period
    fetched_at: str = ""


class YouTubeAnalytics:
    """Poll YouTube Data API v3 for video and channel metrics."""

    BASE = "https://www.googleapis.com/youtube/v3"

    def __init__(self):
        self._api_key = os.getenv("YOUTUBE_DATA_API_KEY", "")

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    async def get_video_metrics(self, video_id: str) -> Optional[VideoMetrics]:
        """Fetch metrics for a single YouTube video."""
        if not self.available:
            return None

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(
                    f"{self.BASE}/videos",
                    params={
                        "part": "snippet,statistics,contentDetails",
                        "id": video_id,
                        "key": self._api_key,
                    },
                )
                r.raise_for_status()
                items = r.json().get("items", [])
                if not items:
                    return None

                item = items[0]
                snippet = item.get("snippet", {})
                stats = item.get("statistics", {})

                views = int(stats.get("viewCount", 0))
                likes = int(stats.get("likeCount", 0))
                comments = int(stats.get("commentCount", 0))

                return VideoMetrics(
                    platform="youtube",
                    video_id=video_id,
                    title=snippet.get("title", ""),
                    views=views,
                    likes=likes,
                    comments=comments,
                    score=self._score_video(views, likes, comments),
                    fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    url=f"https://youtube.com/watch?v={video_id}",
                )
        except Exception as e:
            log.warning(f"YouTube video metrics failed for {video_id}: {e}")
            return None

    async def get_channel_metrics(self, channel_id: str) -> Optional[ChannelMetrics]:
        """Fetch channel-level metrics."""
        if not self.available:
            return None

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(
                    f"{self.BASE}/channels",
                    params={
                        "part": "snippet,statistics,contentDetails",
                        "id": channel_id,
                        "key": self._api_key,
                    },
                )
                r.raise_for_status()
                items = r.json().get("items", [])
                if not items:
                    return None

                item = items[0]
                snippet = item.get("snippet", {})
                stats = item.get("statistics", {})

                subs = int(stats.get("subscriberCount", 0))
                views = int(stats.get("viewCount", 0))
                videos = int(stats.get("videoCount", 0))

                return ChannelMetrics(
                    platform="youtube",
                    channel_id=channel_id,
                    channel_name=snippet.get("title", ""),
                    subscribers=subs,
                    total_views=views,
                    total_videos=videos,
                    avg_views_per_video=views / max(videos, 1),
                    fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                )
        except Exception as e:
            log.warning(f"YouTube channel metrics failed for {channel_id}: {e}")
            return None

    async def get_channel_videos(self, channel_id: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Get recent video IDs from a channel."""
        if not self.available:
            return []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # First get the uploads playlist
                r = await client.get(
                    f"{self.BASE}/channels",
                    params={
                        "part": "contentDetails",
                        "id": channel_id,
                        "key": self._api_key,
                    },
                )
                r.raise_for_status()
                items = r.json().get("items", [])
                if not items:
                    return []

                uploads_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

                # Get videos from uploads playlist
                r = await client.get(
                    f"{self.BASE}/playlistItems",
                    params={
                        "part": "snippet,contentDetails",
                        "playlistId": uploads_id,
                        "maxResults": max_results,
                        "key": self._api_key,
                    },
                )
                r.raise_for_status()
                return [
                    {
                        "video_id": item["contentDetails"]["videoId"],
                        "title": item["snippet"]["title"],
                        "published_at": item["snippet"]["publishedAt"],
                    }
                    for item in r.json().get("items", [])
                ]
        except Exception as e:
            log.warning(f"YouTube channel videos failed: {e}")
            return []

    def _score_video(self, views: int, likes: int, comments: int) -> float:
        """Score a video 0-100 based on engagement metrics."""
        if views == 0:
            return 0
        engagement_rate = (likes + comments * 2) / views
        # Normalize: 5% engagement = score 80, 10%+ = score 100
        score = min(100, engagement_rate * 1000)
        return round(score, 1)


class TikTokAnalytics:
    """TikTok analytics (requires TikTok Research API or scraping)."""

    def __init__(self):
        self._access_token = os.getenv("TIKTOK_ACCESS_TOKEN", "")

    @property
    def available(self) -> bool:
        return bool(self._access_token)

    async def get_video_metrics(self, video_id: str) -> Optional[VideoMetrics]:
        """Fetch TikTok video metrics. Requires Research API access."""
        if not self.available:
            return None

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(
                    f"https://open.tiktokapis.com/v2/video/query/",
                    params={"fields": "id,title,view_count,like_count,comment_count,share_count"},
                    headers={"Authorization": f"Bearer {self._access_token}"},
                    data={"video_ids": json.dumps([video_id])},
                )
                r.raise_for_status()
                data = r.json().get("data", {})
                videos = data.get("videos", [])
                if not videos:
                    return None

                v = videos[0]
                return VideoMetrics(
                    platform="tiktok",
                    video_id=video_id,
                    title=v.get("title", ""),
                    views=v.get("view_count", 0),
                    likes=v.get("like_count", 0),
                    comments=v.get("comment_count", 0),
                    shares=v.get("share_count", 0),
                    score=self._score(v),
                    fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    url=f"https://tiktok.com/@/video/{video_id}",
                )
        except Exception as e:
            log.warning(f"TikTok metrics failed for {video_id}: {e}")
            return None

    def _score(self, video: Dict) -> float:
        views = video.get("view_count", 0)
        likes = video.get("like_count", 0)
        comments = video.get("comment_count", 0)
        if views == 0:
            return 0
        return min(100, round(((likes + comments * 2) / views) * 1000, 1))


class InstagramAnalytics:
    """Instagram analytics via Graph API."""

    def __init__(self):
        self._access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")

    @property
    def available(self) -> bool:
        return bool(self._access_token)

    async def get_video_metrics(self, media_id: str) -> Optional[VideoMetrics]:
        """Fetch Instagram Reel/Post metrics."""
        if not self.available:
            return None

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(
                    f"https://graph.facebook.com/v19.0/{media_id}",
                    params={
                        "fields": "id,caption,like_count,comments_count,insights.metric(impressions,reach,engagement)",
                        "access_token": self._access_token,
                    },
                )
                r.raise_for_status()
                data = r.json()

                likes = data.get("like_count", 0)
                comments = data.get("comments_count", 0)
                insights = data.get("insights", {}).get("data", [])
                impressions = next(
                    (i["values"][0]["value"] for i in insights if i["name"] == "impressions"), 0
                )

                return VideoMetrics(
                    platform="instagram",
                    video_id=media_id,
                    title=data.get("caption", "")[:100],
                    views=impressions,
                    likes=likes,
                    comments=comments,
                    score=self._score(impressions, likes, comments),
                    fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    url=f"https://instagram.com/p/{media_id}",
                )
        except Exception as e:
            log.warning(f"Instagram metrics failed for {media_id}: {e}")
            return None

    def _score(self, impressions: int, likes: int, comments: int) -> float:
        if impressions == 0:
            return 0
        return min(100, round(((likes + comments * 2) / impressions) * 1000, 1))


class AnalyticsStore:
    """Local storage for analytics data. Persists to JSON."""

    def __init__(self):
        self._metrics_file = os.path.join(ANALYTICS_DIR, "metrics.json")
        self._channel_file = os.path.join(ANALYTICS_DIR, "channels.json")
        self._data = self._load(self._metrics_file, {"videos": []})
        self._channels = self._load(self._channel_file, {"channels": []})

    def _load(self, path: str, default: Any) -> Any:
        try:
            if os.path.exists(path):
                with open(path) as f:
                    return json.load(f)
        except Exception:
            pass
        return default

    def _save(self, path: str, data: Any) -> None:
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            log.warning(f"Analytics save failed: {e}")

    def store_video_metrics(self, metrics: VideoMetrics) -> None:
        """Store or update video metrics."""
        d = asdict(metrics)
        # Update or append
        found = False
        for i, v in enumerate(self._data["videos"]):
            if v["video_id"] == metrics.video_id and v["platform"] == metrics.platform:
                self._data["videos"][i] = d
                found = True
                break
        if not found:
            self._data["videos"].append(d)
        self._save(self._metrics_file, self._data)

    def store_channel_metrics(self, metrics: ChannelMetrics) -> None:
        """Store or update channel metrics."""
        d = asdict(metrics)
        found = False
        for i, c in enumerate(self._channels["channels"]):
            if c["channel_id"] == metrics.channel_id and c["platform"] == metrics.platform:
                self._channels["channels"][i] = d
                found = True
                break
        if not found:
            self._channels["channels"].append(d)
        self._save(self._channel_file, self._channels)

    def get_video_metrics(self, platform: str = "", limit: int = 50) -> List[Dict]:
        videos = self._data.get("videos", [])
        if platform:
            videos = [v for v in videos if v["platform"] == platform]
        return sorted(videos, key=lambda x: x.get("score", 0), reverse=True)[:limit]

    def get_channel_metrics(self, platform: str = "") -> List[Dict]:
        channels = self._channels.get("channels", [])
        if platform:
            channels = [c for c in channels if c["platform"] == platform]
        return channels

    def get_top_videos(self, n: int = 10) -> List[Dict]:
        return sorted(
            self._data.get("videos", []),
            key=lambda x: x.get("score", 0),
            reverse=True,
        )[:n]


class AnalyticsEngine:
    """Unified analytics engine — polls all platforms and stores results."""

    def __init__(self):
        self.youtube = YouTubeAnalytics()
        self.tiktok = TikTokAnalytics()
        self.instagram = InstagramAnalytics()
        self.store = AnalyticsStore()

    async def fetch_all_metrics(self, video_ids: Dict[str, str]) -> List[VideoMetrics]:
        """Fetch metrics for videos across platforms.

        video_ids: {"youtube": "abc123", "tiktok": "789", "instagram": "xyz"}
        """
        results = []

        if "youtube" in video_ids and self.youtube.available:
            m = await self.youtube.get_video_metrics(video_ids["youtube"])
            if m:
                results.append(m)
                self.store.store_video_metrics(m)

        if "tiktok" in video_ids and self.tiktok.available:
            m = await self.tiktok.get_video_metrics(video_ids["tiktok"])
            if m:
                results.append(m)
                self.store.store_video_metrics(m)

        if "instagram" in video_ids and self.instagram.available:
            m = await self.instagram.get_video_metrics(video_ids["instagram"])
            if m:
                results.append(m)
                self.store.store_video_metrics(m)

        return results

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get aggregated analytics for the dashboard."""
        all_videos = self.store.get_video_metrics()
        top = self.store.get_top_videos(10)
        channels = self.store.get_channel_metrics()

        total_views = sum(v.get("views", 0) for v in all_videos)
        total_likes = sum(v.get("likes", 0) for v in all_videos)
        avg_score = (
            sum(v.get("score", 0) for v in all_videos) / max(len(all_videos), 1)
        )

        return {
            "summary": {
                "total_videos": len(all_videos),
                "total_views": total_views,
                "total_likes": total_likes,
                "avg_score": round(avg_score, 1),
            },
            "top_videos": top,
            "channels": channels,
            "platforms": {
                "youtube": self.youtube.available,
                "tiktok": self.tiktok.available,
                "instagram": self.instagram.available,
            },
        }


__all__ = [
    "AnalyticsEngine",
    "YouTubeAnalytics",
    "TikTokAnalytics",
    "InstagramAnalytics",
    "AnalyticsStore",
    "VideoMetrics",
    "ChannelMetrics",
]
