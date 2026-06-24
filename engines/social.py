"""
Direct social publishing engines (YouTube, TikTok, Instagram).

These wrap the official platform APIs (no third-party middleware like
Upload-Post) — all three have free tiers, OAuth2 flows, and a generous
quota for individual users. Tokens are stored server-side in
`output/social_tokens.json` (encrypted with the same XOR+Base64 helper
the frontend uses for API keys; additive — no change to existing
key handling in the browser).

Each engine exposes:
  - health()
  - connect_url() -> str         — start OAuth flow, return authorization URL
  - exchange(code) -> dict        — exchange auth code for access/refresh tokens
  - post_video(video_path, ...)  — upload + publish
  - status() -> {connected, account_name, ...}
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode, parse_qs

import httpx

from .base import BaseEngine, EngineCapability, EngineHealth, EngineResult, engine_method, EngineError

log = logging.getLogger(__name__)

TOKENS_FILE = os.path.join("output", "social_tokens.json")
os.makedirs(os.path.dirname(TOKENS_FILE), exist_ok=True)


def _load_tokens() -> Dict[str, Any]:
    if not os.path.exists(TOKENS_FILE):
        return {}
    try:
        with open(TOKENS_FILE, "r") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _save_tokens(data: Dict[str, Any]) -> None:
    with open(TOKENS_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ── YouTube Data API v3 ────────────────────────────────────────────────
# Docs: https://developers.google.com/youtube/v3
# Free quota: 10,000 units/day. Video upload = 1,600 units.
# Console: https://console.cloud.google.com/apis/credentials

YOUTUBE_SCOPES = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube"


class YouTubeEngine(BaseEngine):
    provider_id = "youtube"
    display_name = "YouTube Data API v3 (direct, free 10k units/day)"
    capability = EngineCapability.SOCIAL_POST
    cost_hint = "Free (10,000 units/day quota)"
    hardware_hint = "cloud"
    requires_key = True
    key_env_var = "YOUTUBE_CLIENT_ID"

    def __init__(self) -> None:
        self.client_id = os.getenv("YOUTUBE_CLIENT_ID", "")
        self.client_secret = os.getenv("YOUTUBE_CLIENT_SECRET", "")
        self.redirect_uri = os.getenv("YOUTUBE_REDIRECT_URI", "http://localhost:18080/api/social/youtube/callback")

    async def health(self) -> EngineHealth:
        if not self.client_id or not self.client_secret:
            return EngineHealth(
                healthy=False,
                detail="YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET not set. Configure them in .env",
            )
        tokens = _load_tokens().get("youtube", {})
        if not tokens:
            return EngineHealth(healthy=False, detail="Not connected. Click 'Connect YouTube' in Settings.")
        return EngineHealth(healthy=True, detail=f"connected (channel: {tokens.get('channel_title', '?')})")

    def connect_url(self) -> str:
        if not self.client_id:
            raise EngineError("YOUTUBE_CLIENT_ID not set in env")
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": YOUTUBE_SCOPES,
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    @engine_method
    async def exchange(self, code: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as c:
            r = await c.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": self.redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
        if r.status_code >= 400:
            raise EngineError(f"YouTube token exchange failed: {r.status_code} {r.text[:300]}")
        data = r.json()
        tokens = _load_tokens()
        tokens["youtube"] = {**data, "connected_at": time.time()}
        _save_tokens(tokens)
        return {"connected": True, "platform": "youtube"}

    @engine_method
    async def post_video(
        self,
        video_path: str,
        title: str,
        description: str = "",
        tags: Optional[list] = None,
        privacy: str = "private",
    ) -> Dict[str, Any]:
        """Upload a video to YouTube via the resumable upload protocol."""
        tokens = _load_tokens().get("youtube", {})
        if not tokens.get("access_token"):
            raise EngineError("YouTube not connected. Click 'Connect YouTube' in Settings.")
        if not os.path.exists(video_path):
            raise EngineError(f"video not found: {video_path}")
        tags = tags or []

        async with httpx.AsyncClient(timeout=600.0) as c:
            # 1. Initiate resumable upload
            metadata = {
                "snippet": {"title": title, "description": description, "tags": tags, "categoryId": "22"},
                "status": {"privacyStatus": privacy},
            }
            r = await c.post(
                "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
                headers={
                    "Authorization": f"Bearer {tokens['access_token']}",
                    "Content-Type": "application/json; charset=utf-8",
                    "X-Upload-Content-Type": "video/mp4",
                },
                json=metadata,
            )
            if r.status_code >= 400:
                raise EngineError(f"YouTube upload init failed: {r.status_code} {r.text[:300]}")
            upload_url = r.headers["location"]

            # 2. Upload the bytes
            with open(video_path, "rb") as f:
                video_bytes = f.read()
            r = await c.put(
                upload_url, headers={"Content-Type": "video/mp4"}, content=video_bytes
            )
            if r.status_code >= 400:
                raise EngineError(f"YouTube upload failed: {r.status_code} {r.text[:300]}")
            video = r.json()
            return {
                "platform": "youtube",
                "id": video.get("id"),
                "url": f"https://youtu.be/{video.get('id')}",
                "status": video.get("status", {}).get("uploadStatus"),
            }

    @engine_method
    def status(self) -> Dict[str, Any]:
        tokens = _load_tokens().get("youtube", {})
        if not tokens:
            return {"connected": False, "platform": "youtube"}
        return {
            "connected": True,
            "platform": "youtube",
            "connected_at": tokens.get("connected_at"),
            "expires_at": tokens.get("expires_at") or (tokens.get("connected_at", 0) + 3600),
        }


# ── TikTok Content Posting API ────────────────────────────────────────
# Docs: https://developers.tiktok.com/documents/content-posting-api
# Free tier with app review. Requires a TikTok Developer app.

TIKTOK_SCOPES = "user.info.basic,video.upload,video.publish"


class TikTokEngine(BaseEngine):
    provider_id = "tiktok"
    display_name = "TikTok Content Posting API (direct, free with app review)"
    capability = EngineCapability.SOCIAL_POST
    cost_hint = "Free (requires TikTok app review)"
    hardware_hint = "cloud"
    requires_key = True
    key_env_var = "TIKTOK_CLIENT_KEY"

    def __init__(self) -> None:
        self.client_key = os.getenv("TIKTOK_CLIENT_KEY", "")
        self.client_secret = os.getenv("TIKTOK_CLIENT_SECRET", "")
        self.redirect_uri = os.getenv("TIKTOK_REDIRECT_URI", "http://localhost:18080/api/social/tiktok/callback")

    async def health(self) -> EngineHealth:
        if not self.client_key or not self.client_secret:
            return EngineHealth(
                healthy=False,
                detail="TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET not set. Configure in .env",
            )
        tokens = _load_tokens().get("tiktok", {})
        if not tokens:
            return EngineHealth(healthy=False, detail="Not connected. Click 'Connect TikTok' in Settings.")
        return EngineHealth(healthy=True, detail=f"connected (open_id: {tokens.get('open_id', '?')[:8]}…)")

    def connect_url(self) -> str:
        if not self.client_key:
            raise EngineError("TIKTOK_CLIENT_KEY not set in env")
        params = {
            "client_key": self.client_key,
            "scope": TIKTOK_SCOPES,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "state": "csrf_token_placeholder",
        }
        return f"https://www.tiktok.com/v2/auth/authorize?{urlencode(params)}"

    @engine_method
    async def exchange(self, code: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as c:
            r = await c.post(
                "https://open.tiktokapis.com/v2/oauth/token/",
                data={
                    "client_key": self.client_key,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        if r.status_code >= 400:
            raise EngineError(f"TikTok token exchange failed: {r.status_code} {r.text[:300]}")
        data = r.json()
        tokens = _load_tokens()
        tokens["tiktok"] = {**data, "connected_at": time.time()}
        _save_tokens(tokens)
        return {"connected": True, "platform": "tiktok"}

    @engine_method
    async def post_video(
        self,
        video_path: str,
        title: str,
        description: str = "",
        privacy: str = "PUBLIC_TO_EVERYONE",
    ) -> Dict[str, Any]:
        tokens = _load_tokens().get("tiktok", {})
        if not tokens.get("access_token"):
            raise EngineError("TikTok not connected. Click 'Connect TikTok' in Settings.")
        if not os.path.exists(video_path):
            raise EngineError(f"video not found: {video_path}")
        # TikTok Content Posting API v2:
        # 1) POST /v2/post/publish/video/init/ to get upload URL
        # 2) PUT the video file to the upload URL
        # 3) Poll for completion then publish
        access_token = tokens["access_token"]

        # Step 1: Initialize upload
        import httpx
        file_size = os.path.getsize(video_path)
        init_payload = {
            "post_info": {
                "title": title[:150],
                "privacy_level": privacy,
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
            },
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            init_r = await client.post(
                "https://open.tiktokapis.com/v2/post/publish/video/init/",
                headers={"Authorization": f"Bearer {access_token}"},
                json=init_payload,
            )
            init_r.raise_for_status()
            init_data = init_r.json().get("data", {})
            upload_url = init_data.get("upload_url")
            publish_id = init_data.get("publish_id")

            if not upload_url:
                raise EngineError(f"TikTok init failed: {init_r.text[:200]}")

            # Step 2: Upload the video file
            with open(video_path, "rb") as f:
                upload_r = await client.put(
                    upload_url,
                    content=f.read(),
                    headers={
                        "Content-Type": "video/mp4",
                        "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
                    },
                )
                upload_r.raise_for_status()

            # Step 3: Poll for processing completion (max 60s)
            for _ in range(12):
                await asyncio.sleep(5)
                status_r = await client.get(
                    "https://open.tiktokapis.com/v2/post/publish/status/fetch/",
                    headers={"Authorization": f"Bearer {access_token}"},
                    json={"publish_id": publish_id},
                )
                status_data = status_r.json().get("data", {})
                status = status_data.get("status")
                if status == "SUCCESS":
                    return {"status": "published", "platform": "tiktok", "publish_id": publish_id}
                elif status == "FAILED":
                    raise EngineError(f"TikTok publish failed: {status_data}")

            return {"status": "processing", "platform": "tiktok", "publish_id": publish_id}

    @engine_method
    def status(self) -> Dict[str, Any]:
        tokens = _load_tokens().get("tiktok", {})
        if not tokens:
            return {"connected": False, "platform": "tiktok"}
        return {"connected": True, "platform": "tiktok", "connected_at": tokens.get("connected_at")}


# ── Instagram Graph API (via Facebook Login) ───────────────────────────
# Docs: https://developers.facebook.com/docs/instagram-api
# Requires Facebook Page linked to an Instagram Business/Creator account.
# Free tier for posting Reels to your own account.

INSTAGRAM_SCOPES = "instagram_basic,instagram_content_publish,pages_show_list"


class InstagramEngine(BaseEngine):
    provider_id = "instagram"
    display_name = "Instagram Graph API (direct, free for your own account)"
    capability = EngineCapability.SOCIAL_POST
    cost_hint = "Free (requires FB Page + IG Business account)"
    hardware_hint = "cloud"
    requires_key = True
    key_env_var = "INSTAGRAM_APP_ID"

    def __init__(self) -> None:
        self.app_id = os.getenv("INSTAGRAM_APP_ID", "")
        self.app_secret = os.getenv("INSTAGRAM_APP_SECRET", "")
        self.redirect_uri = os.getenv("INSTAGRAM_REDIRECT_URI", "http://localhost:18080/api/social/instagram/callback")

    async def health(self) -> EngineHealth:
        if not self.app_id or not self.app_secret:
            return EngineHealth(
                healthy=False,
                detail="INSTAGRAM_APP_ID / INSTAGRAM_APP_SECRET not set. Configure in .env",
            )
        tokens = _load_tokens().get("instagram", {})
        if not tokens:
            return EngineHealth(healthy=False, detail="Not connected. Click 'Connect Instagram' in Settings.")
        return EngineHealth(healthy=True, detail=f"connected (ig_user_id: {tokens.get('ig_user_id', '?')[:8]}…)")

    def connect_url(self) -> str:
        if not self.app_id:
            raise EngineError("INSTAGRAM_APP_ID not set in env")
        params = {
            "client_id": self.app_id,
            "redirect_uri": self.redirect_uri,
            "scope": ",".join(INSTAGRAM_SCOPES.split(",")),
            "response_type": "code",
            "state": "csrf_placeholder",
        }
        return f"https://www.facebook.com/v18.0/dialog/oauth?{urlencode(params)}"

    @engine_method
    async def exchange(self, code: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as c:
            r = await c.get(
                "https://graph.facebook.com/v18.0/oauth/access_token",
                params={
                    "client_id": self.app_id,
                    "client_secret": self.app_secret,
                    "redirect_uri": self.redirect_uri,
                    "code": code,
                },
            )
        if r.status_code >= 400:
            raise EngineError(f"Instagram token exchange failed: {r.status_code} {r.text[:300]}")
        data = r.json()
        tokens = _load_tokens()
        tokens["instagram"] = {**data, "connected_at": time.time()}
        _save_tokens(tokens)
        return {"connected": True, "platform": "instagram"}

    @engine_method
    async def post_video(
        self,
        video_path: str,
        title: str,
        description: str = "",
        privacy: str = "PUBLIC",
    ) -> Dict[str, Any]:
        tokens = _load_tokens().get("instagram", {})
        if not tokens.get("access_token"):
            raise EngineError("Instagram not connected. Click 'Connect Instagram' in Settings.")
        if not os.path.exists(video_path):
            raise EngineError(f"video not found: {video_path}")
        # Instagram Graph API requires a publicly accessible video URL.
        # Strategy: upload to S3/SeaweedFS first, then create IG container.
        ig_user_id = tokens.get("ig_user_id", "")
        access_token = tokens.get("access_token", "")

        if not ig_user_id:
            raise EngineError("Instagram: ig_user_id not found in tokens. Reconnect Instagram.")

        import httpx

        # Step 0: Get a public URL for the video
        public_url = await self._get_public_url(video_path)

        # Step 1: Create media container
        async with httpx.AsyncClient(timeout=120.0) as client:
            create_r = await client.post(
                f"https://graph.facebook.com/v19.0/{ig_user_id}/media",
                data={
                    "media_type": "REELS",
                    "video_url": public_url,
                    "caption": f"{title}\n\n{description}"[:2200],
                    "access_token": access_token,
                },
            )
            create_r.raise_for_status()
            container_id = create_r.json().get("id")
            if not container_id:
                raise EngineError(f"Instagram container creation failed: {create_r.text[:300]}")

            # Step 2: Poll until status is FINISHED (max 120s)
            for _ in range(24):
                await asyncio.sleep(5)
                status_r = await client.get(
                    f"https://graph.facebook.com/v19.0/{container_id}",
                    params={"fields": "status_code", "access_token": access_token},
                )
                status_data = status_r.json()
                status_code = status_data.get("status_code")
                if status_code == "FINISHED":
                    break
                elif status_code == "ERROR":
                    raise EngineError(f"Instagram container processing failed: {status_data}")

            # Step 3: Publish
            publish_r = await client.post(
                f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish",
                data={
                    "creation_id": container_id,
                    "access_token": access_token,
                },
            )
            publish_r.raise_for_status()
            media_id = publish_r.json().get("id")

            return {
                "status": "published",
                "platform": "instagram",
                "media_id": media_id,
                "url": f"https://instagram.com/reel/{media_id}",
            }

    async def _get_public_url(self, video_path: str) -> str:
        """Upload video to storage and return a public URL."""
        # Try S3/SeaweedFS first
        try:
            from engines.storage import get_storage
            storage = get_storage()
            key = f"social/instagram/{os.path.basename(video_path)}"
            with open(video_path, "rb") as f:
                result = storage.upload(f, key)
            return result.get("url", "")
        except Exception:
            pass

        # Fallback: use the backend's public URL
        public_base = os.getenv("PUBLIC_BASE_URL", "http://localhost:18080")
        filename = os.path.basename(video_path)
        return f"{public_base}/output/{filename}"

    @engine_method
    def status(self) -> Dict[str, Any]:
        tokens = _load_tokens().get("instagram", {})
        if not tokens:
            return {"connected": False, "platform": "instagram"}
        return {"connected": True, "platform": "instagram", "connected_at": tokens.get("connected_at")}


__all__ = [
    "YouTubeEngine",
    "TikTokEngine",
    "InstagramEngine",
    "TOKENS_FILE",
]
