"""
Gallery Engine — unified content store for all pipeline outputs.

Every piece of content created (clips, factory outputs, AI shorts,
avatar animations, translations) flows through this gallery before
anything else. Users browse, curate, and publish from here.

Persistence: local JSON file at output/gallery.json.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

GALLERY_DIR = os.path.join("output", "gallery")
GALLERY_FILE = os.path.join("output", "gallery.json")
os.makedirs(GALLERY_DIR, exist_ok=True)


@dataclass
class GalleryItem:
    id: str
    title: str
    caption: str
    source: str  # "clip-generator", "factory", "ai-shorts", "avatar-studio", "multilingual", "research"
    template_id: str  # factory template id, or "clip", "short", "avatar", "translate"
    file_path: str  # relative path to video/image
    file_type: str  # "video", "image", "audio", "text"
    file_size: int  # bytes
    duration: float  # seconds (0 for non-video)
    thumbnail_path: str = ""  # optional thumbnail
    tags: List[str] = field(default_factory=list)
    platforms: List[str] = field(default_factory=list)  # posted to which platforms
    metadata: Dict[str, Any] = field(default_factory=dict)  # extra data (cost, engine, etc.)
    status: str = "ready"  # "ready", "processing", "published", "archived"
    created_at: str = ""
    updated_at: str = ""


class GalleryStore:
    """Persistent gallery store backed by JSON file."""

    def __init__(self, gallery_dir: str = GALLERY_DIR, gallery_file: str = GALLERY_FILE):
        self._dir = gallery_dir
        self._file = gallery_file
        self._items: Dict[str, GalleryItem] = {}
        self._load()

    def _load(self) -> None:
        try:
            if os.path.exists(self._file):
                with open(self._file) as f:
                    data = json.load(f)
                self._items = {
                    k: GalleryItem(**v) for k, v in data.items()
                }
                log.info(f"Gallery: loaded {len(self._items)} items")
        except Exception as e:
            log.warning(f"Gallery load failed: {e}")
            self._items = {}

    def _save(self) -> None:
        try:
            with open(self._file, "w") as f:
                json.dump(
                    {k: asdict(v) for k, v in self._items.items()},
                    f,
                    indent=2,
                    default=str,
                )
        except Exception as e:
            log.warning(f"Gallery save failed: {e}")

    def add(
        self,
        title: str,
        caption: str,
        source: str,
        template_id: str,
        file_path: str,
        file_type: str = "video",
        file_size: int = 0,
        duration: float = 0.0,
        thumbnail_path: str = "",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GalleryItem:
        """Add a new item to the gallery. Copies file to gallery dir."""
        item_id = uuid.uuid4().hex[:12]
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Copy file to gallery directory if it exists and isn't already there
        dest_path = file_path
        if os.path.exists(file_path) and not file_path.startswith(self._dir):
            ext = os.path.splitext(file_path)[1]
            dest_path = os.path.join(self._dir, f"{item_id}{ext}")
            try:
                shutil.copy2(file_path, dest_path)
            except Exception as e:
                log.warning(f"Gallery: failed to copy {file_path}: {e}")
                dest_path = file_path

        # Make path relative for frontend consumption
        rel_path = dest_path
        if os.path.isabs(rel_path):
            rel_path = os.path.relpath(rel_path, os.getcwd())

        item = GalleryItem(
            id=item_id,
            title=title,
            caption=caption,
            source=source,
            template_id=template_id,
            file_path=rel_path,
            file_type=file_type,
            file_size=file_size or (os.path.getsize(dest_path) if os.path.exists(dest_path) else 0),
            duration=duration,
            thumbnail_path=thumbnail_path,
            tags=tags or [],
            metadata=metadata or {},
            status="ready",
            created_at=now,
            updated_at=now,
        )
        self._items[item_id] = item
        self._save()
        log.info(f"Gallery: added {item_id} ({source}/{template_id}) — {title}")
        return item

    def get(self, item_id: str) -> Optional[GalleryItem]:
        return self._items.get(item_id)

    def list_items(
        self,
        source: str = "",
        template_id: str = "",
        status: str = "",
        tag: str = "",
        search: str = "",
        limit: int = 100,
        offset: int = 0,
    ) -> List[GalleryItem]:
        """List items with optional filters."""
        items = list(self._items.values())

        if source:
            items = [i for i in items if i.source == source]
        if template_id:
            items = [i for i in items if i.template_id == template_id]
        if status:
            items = [i for i in items if i.status == status]
        if tag:
            items = [i for i in items if tag in i.tags]
        if search:
            q = search.lower()
            items = [i for i in items if q in i.title.lower() or q in i.caption.lower() or any(q in t.lower() for t in i.tags)]

        # Sort newest first
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[offset:offset + limit]

    def update(self, item_id: str, **kwargs) -> Optional[GalleryItem]:
        """Update fields on a gallery item."""
        item = self._items.get(item_id)
        if not item:
            return None
        for key, val in kwargs.items():
            if hasattr(item, key):
                setattr(item, key, val)
        item.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        self._save()
        return item

    def delete(self, item_id: str) -> bool:
        """Delete a gallery item and its file."""
        item = self._items.pop(item_id, None)
        if not item:
            return False
        # Delete file from gallery dir
        if item.file_path and item.file_path.startswith(self._dir):
            try:
                os.remove(item.file_path)
            except OSError:
                pass
        self._save()
        return True

    def mark_published(self, item_id: str, platform: str) -> Optional[GalleryItem]:
        """Mark item as published to a platform."""
        item = self._items.get(item_id)
        if not item:
            return None
        if platform not in item.platforms:
            item.platforms.append(platform)
        item.status = "published"
        item.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        self._save()
        return item

    def get_stats(self) -> Dict[str, Any]:
        """Get gallery statistics."""
        items = list(self._items.values())
        by_source = {}
        for item in items:
            by_source[item.source] = by_source.get(item.source, 0) + 1
        total_size = sum(i.file_size for i in items)
        return {
            "total_items": len(items),
            "total_size": total_size,
            "by_source": by_source,
            "by_status": {
                status: sum(1 for i in items if i.status == status)
                for status in ("ready", "processing", "published", "archived")
            },
        }


__all__ = ["GalleryStore", "GalleryItem", "GALLERY_DIR", "GALLERY_FILE"]
