"""
Video Editor Engine — wraps mcp-video Client for Content Factory.

Provides a high-level API for video editing operations:
  - trim, merge, crop, resize, rotate
  - text overlays, subtitles, watermarks
  - audio mixing, normalization, ducking
  - transitions, effects, filters
  - scene detection, transcription, quality checks
  - pipeline chaining for multi-step edits

All operations are synchronous (FFmpeg-based) and run in a thread pool
when called from async FastAPI endpoints.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


def get_editor():
    """Get mcp-video Client instance. Lazy import to avoid startup cost."""
    from mcp_video import Client
    return Client()


def trim(input_path: str, start: str = "0", duration: Optional[str] = None,
         end: Optional[str] = None, output: Optional[str] = None) -> Dict[str, Any]:
    """Trim a video segment."""
    editor = get_editor()
    result = editor.trim(input_path, start=start, duration=duration, end=end, output=output)
    return {"success": True, "output_path": result.output_path, "duration": getattr(result, 'duration', None)}


def merge(clips: List[str], output: Optional[str] = None,
          transitions: Optional[List[str]] = None) -> Dict[str, Any]:
    """Merge multiple clips into one."""
    editor = get_editor()
    result = editor.merge(clips, output=output, transitions=transitions)
    return {"success": True, "output_path": result.output_path}


def add_text(video: str, text: str, position: str = "top-center",
             font: Optional[str] = None, size: int = 48, color: str = "white",
             shadow: bool = True, start_time: Optional[float] = None,
             duration: Optional[float] = None, output: Optional[str] = None) -> Dict[str, Any]:
    """Overlay text on video."""
    editor = get_editor()
    result = editor.add_text(video, text, position=position, font=font, size=size,
                             color=color, shadow=shadow, start_time=start_time,
                             duration=duration, output=output)
    return {"success": True, "output_path": result.output_path}


def add_texts(video: str, texts: List[Dict[str, Any]],
              output: Optional[str] = None) -> Dict[str, Any]:
    """Overlay multiple text elements in a single FFmpeg pass."""
    editor = get_editor()
    result = editor.add_texts(video, texts, output=output)
    return {"success": True, "output_path": result.output_path}


def add_audio(video: str, audio: str, volume: float = 1.0,
              fade_in: float = 0.0, fade_out: float = 0.0,
              mix: bool = False, start_time: Optional[float] = None,
              output: Optional[str] = None) -> Dict[str, Any]:
    """Add or mix audio track onto video."""
    editor = get_editor()
    result = editor.add_audio(video, audio, volume=volume, fade_in=fade_in,
                              fade_out=fade_out, mix=mix, start_time=start_time,
                              output=output)
    return {"success": True, "output_path": result.output_path}


def resize(video: str, width: Optional[int] = None, height: Optional[int] = None,
           aspect_ratio: Optional[str] = None, output: Optional[str] = None) -> Dict[str, Any]:
    """Resize video or change aspect ratio."""
    editor = get_editor()
    result = editor.resize(video, width=width, height=height,
                           aspect_ratio=aspect_ratio, output=output)
    return {"success": True, "output_path": result.output_path}


def crop(video: str, width: Optional[int] = None, height: Optional[int] = None,
         x: Optional[int] = None, y: Optional[int] = None,
         output: Optional[str] = None) -> Dict[str, Any]:
    """Crop video to region."""
    editor = get_editor()
    result = editor.crop(video, width=width, height=height, x=x, y=y, output=output)
    return {"success": True, "output_path": result.output_path}


def rotate(video: str, angle: int = 0, flip_horizontal: bool = False,
           flip_vertical: bool = False, output: Optional[str] = None) -> Dict[str, Any]:
    """Rotate or flip video."""
    editor = get_editor()
    result = editor.rotate(video, angle=angle, flip_horizontal=flip_horizontal,
                           flip_vertical=flip_vertical, output=output)
    return {"success": True, "output_path": result.output_path}


def speed(video: str, factor: float = 1.0, output: Optional[str] = None) -> Dict[str, Any]:
    """Change video playback speed."""
    editor = get_editor()
    result = editor.speed(video, factor=factor, output=output)
    return {"success": True, "output_path": result.output_path}


def fade(video: str, fade_in: float = 0.0, fade_out: float = 0.0,
         output: Optional[str] = None) -> Dict[str, Any]:
    """Add fade in/out effects."""
    editor = get_editor()
    result = editor.fade(video, fade_in=fade_in, fade_out=fade_out, output=output)
    return {"success": True, "output_path": result.output_path}


def filter(video: str, filter_type: str, params: Optional[Dict] = None,
           output: Optional[str] = None) -> Dict[str, Any]:
    """Apply video filter (blur, sharpen, grayscale, sepia, invert, etc.)."""
    editor = get_editor()
    result = editor.filter(video, filter_type=filter_type, params=params, output=output)
    return {"success": True, "output_path": result.output_path}


def chroma_key(video: str, color: str = "0x00FF00", similarity: float = 0.01,
               output: Optional[str] = None) -> Dict[str, Any]:
    """Remove green screen background."""
    editor = get_editor()
    result = editor.chroma_key(video, color=color, similarity=similarity, output=output)
    return {"success": True, "output_path": result.output_path}


def overlay_video(background: str, overlay: str, position: str = "top-right",
                  width: Optional[int] = None, opacity: float = 0.8,
                  start_time: Optional[float] = None, duration: Optional[float] = None,
                  output: Optional[str] = None) -> Dict[str, Any]:
    """Picture-in-picture overlay."""
    editor = get_editor()
    result = editor.overlay_video(background, overlay, position=position, width=width,
                                  opacity=opacity, start_time=start_time,
                                  duration=duration, output=output)
    return {"success": True, "output_path": result.output_path}


def subtitles(video: str, subtitle_file: str, output: Optional[str] = None) -> Dict[str, Any]:
    """Burn SRT/VTT subtitles into video."""
    editor = get_editor()
    result = editor.subtitles(video, subtitle_file, output=output)
    return {"success": True, "output_path": result.output_path}


def watermark(video: str, image: str, position: str = "bottom-right",
              opacity: float = 0.7, output: Optional[str] = None) -> Dict[str, Any]:
    """Add image watermark."""
    editor = get_editor()
    result = editor.watermark(video, image, position=position, opacity=opacity, output=output)
    return {"success": True, "output_path": result.output_path}


def normalize_audio(video: str, target_lufs: float = -16.0,
                    output: Optional[str] = None) -> Dict[str, Any]:
    """Normalize audio loudness."""
    editor = get_editor()
    result = editor.normalize_audio(video, target_lufs=target_lufs, output=output)
    return {"success": True, "output_path": result.output_path}


def extract_audio(video: str, output: Optional[str] = None,
                  format: str = "mp3") -> Dict[str, Any]:
    """Extract audio track from video."""
    editor = get_editor()
    result = editor.extract_audio(video, output=output, format=format)
    return {"success": True, "output_path": result.output_path}


def thumbnail(video: str, timestamp: Optional[float] = None,
              output: Optional[str] = None) -> Dict[str, Any]:
    """Extract a thumbnail frame."""
    editor = get_editor()
    result = editor.thumbnail(video, timestamp=timestamp, output=output)
    return {"success": True, "output_path": result.output_path, "timestamp": getattr(result, 'timestamp', None)}


def detect_scenes(video: str, threshold: float = 0.3) -> Dict[str, Any]:
    """Detect scene changes in video."""
    editor = get_editor()
    result = editor.detect_scenes(video, threshold=threshold)
    return {"scenes": result.scenes, "scene_count": result.scene_count, "duration": result.duration}


def info(video: str) -> Dict[str, Any]:
    """Get video metadata."""
    editor = get_editor()
    result = editor.info(video)
    return {
        "duration": result.duration, "width": result.width, "height": result.height,
        "fps": result.fps, "codec": result.codec, "audio_codec": result.audio_codec,
        "bitrate": result.bitrate, "size_bytes": result.size_bytes,
        "aspect_ratio": result.aspect_ratio, "size_mb": result.size_mb,
    }


def convert(video: str, format: str = "mp4", quality: str = "high",
            output: Optional[str] = None) -> Dict[str, Any]:
    """Convert video format."""
    editor = get_editor()
    result = editor.convert(video, format=format, quality=quality, output=output)
    return {"success": True, "output_path": result.output_path}


def stabilize(video: str, smoothing: float = 15.0,
              output: Optional[str] = None) -> Dict[str, Any]:
    """Stabilize shaky footage."""
    editor = get_editor()
    result = editor.stabilize(video, smoothing=smoothing, output=output)
    return {"success": True, "output_path": result.output_path}


def effect_vignette(video: str, output: str, intensity: float = 0.5) -> Dict[str, Any]:
    """Apply vignette effect."""
    editor = get_editor()
    result = editor.effect_vignette(video, output=output, intensity=intensity)
    return {"success": True, "output_path": result.output_path}


def effect_chromatic_aberration(video: str, output: str,
                                 intensity: float = 2.0) -> Dict[str, Any]:
    """Apply chromatic aberration (glitch aesthetic)."""
    editor = get_editor()
    result = editor.effect_chromatic_aberration(video, output=output, intensity=intensity)
    return {"success": True, "output_path": result.output_path}


def effect_glow(video: str, output: str, intensity: float = 0.5) -> Dict[str, Any]:
    """Apply bloom/glow effect."""
    editor = get_editor()
    result = editor.effect_glow(video, output=output, intensity=intensity)
    return {"success": True, "output_path": result.output_path}


def transition_glitch(clip1: str, clip2: str, output: str,
                      duration: float = 0.5) -> Dict[str, Any]:
    """Glitch transition between two clips."""
    editor = get_editor()
    result = editor.transition_glitch(clip1, clip2, output=output, duration=duration)
    return {"success": True, "output_path": result.output_path}


def transition_morph(clip1: str, clip2: str, output: str,
                     duration: float = 0.6) -> Dict[str, Any]:
    """Morph transition between two clips."""
    editor = get_editor()
    result = editor.transition_morph(clip1, clip2, output=output, duration=duration)
    return {"success": True, "output_path": result.output_path}


def text_animated(video: str, text: str, output: str,
                  animation: str = "fade", position: str = "center",
                  start: float = 0, duration: float = 3.0) -> Dict[str, Any]:
    """Add animated text overlay."""
    editor = get_editor()
    result = editor.text_animated(video, text, output=output, animation=animation,
                                  position=position, start=start, duration=duration)
    return {"success": True, "output_path": result.output_path}


def layout_grid(clips: List[str], layout: str, output: str) -> Dict[str, Any]:
    """Create grid layout from multiple clips."""
    editor = get_editor()
    result = editor.layout_grid(clips, layout=layout, output=output)
    return {"success": True, "output_path": result.output_path}


def layout_pip(main: str, pip: str, output: str,
               position: str = "bottom-right", size: float = 0.25) -> Dict[str, Any]:
    """Picture-in-picture layout."""
    editor = get_editor()
    result = editor.layout_pip(main, pip, output=output, position=position, size=size)
    return {"success": True, "output_path": result.output_path}


def repurpose(video: str, output_dir: str,
              platforms: Optional[List[str]] = None) -> Dict[str, Any]:
    """Repurpose video for multiple platforms (YouTube Shorts, Reels, TikTok)."""
    editor = get_editor()
    result = editor.repurpose(video, output_dir=output_dir, platforms=platforms)
    return {"success": True, "output_path": getattr(result, 'output_path', output_dir)}


def pipeline(steps: List[Dict[str, Any]], output: Optional[str] = None) -> Dict[str, Any]:
    """Run a chain of editing operations."""
    editor = get_editor()
    result = editor.pipeline(steps, output_path=output)
    return {"success": True, "output_path": result.output_path}


def quality_check(video: str) -> Dict[str, Any]:
    """Check video quality (brightness, contrast, audio levels)."""
    editor = get_editor()
    result = editor.quality_check(video)
    return result


__all__ = [
    "trim", "merge", "add_text", "add_texts", "add_audio", "resize", "crop",
    "rotate", "speed", "fade", "filter", "chroma_key", "overlay_video",
    "subtitles", "watermark", "normalize_audio", "extract_audio", "thumbnail",
    "detect_scenes", "info", "convert", "stabilize", "effect_vignette",
    "effect_chromatic_aberration", "effect_glow", "transition_glitch",
    "transition_morph", "text_animated", "layout_grid", "layout_pip",
    "repurpose", "pipeline", "quality_check",
]
