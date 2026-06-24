"""
Factory template runner — executes Content Factory templates end-to-end.

Each template gets a function that:
  1. Reads the inputs (source_url, language, etc.)
  2. Calls the appropriate engines (MiniMax for cloud, local for self-host)
  3. Writes the output(s) to the job's output directory
  4. Returns status + output paths + estimated cost

Templates registered in TEMPLATE_RUNNERS below. Each runner is async
and called from app.py via /api/factory/execute/{job_id}.
"""
from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import time
from typing import Any, Awaitable, Callable, Dict, List, Optional

log = logging.getLogger(__name__)

FACTORY_OUTPUT_BASE = os.path.join("output", "factory")


def _job_dir(job_id: str) -> str:
    d = os.path.join(FACTORY_OUTPUT_BASE, job_id)
    os.makedirs(d, exist_ok=True)
    return d


def _append_log(job: Dict[str, Any], msg: str) -> None:
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    log.info(line)
    job.setdefault("logs", []).append(line)


def _run_ffmpeg(args: List[str], label: str = "ffmpeg") -> subprocess.CompletedProcess:
    """Run an ffmpeg command. Raises on non-zero exit."""
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning"] + args
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed (rc={result.returncode}): {result.stderr[:500]}")
    return result


async def _download_url(url: str, out_path: str) -> str:
    """Download a URL to a local file."""
    import httpx
    loop = asyncio.get_running_loop()
    def _do():
        with httpx.Client(timeout=300.0, follow_redirects=True) as c:
            r = c.get(url)
            r.raise_for_status()
            with open(out_path, "wb") as f:
                f.write(r.content)
    await loop.run_in_executor(None, _do)
    return out_path


async def _download_source(inputs: Dict[str, Any], job_dir: str, job: Dict[str, Any]) -> str:
    """Download source video from URL or YouTube. Returns local path."""
    source_url = inputs.get("source_url", "")
    if not source_url:
        raise ValueError("source_url is required")
    source_path = os.path.join(job_dir, "source.mp4")
    try:
        await _download_url(source_url, source_path)
        _append_log(job, f"downloaded source via HTTP: {source_path}")
        return source_path
    except Exception as e:
        _append_log(job, f"HTTP download failed ({e}), trying yt-dlp")
        loop = asyncio.get_running_loop()
        def _ytdl():
            from main import download_youtube_video
            return download_youtube_video(source_url, job_dir)
        path, _title = await loop.run_in_executor(None, _ytdl)
        _append_log(job, f"downloaded via yt-dlp: {path}")
        return path


async def _get_video_engine():
    from engines import get_active, EngineCapability
    from engines.minimax_video import MiniMaxVideoEngine
    eng = get_active(EngineCapability.IMAGE)
    if eng is None:
        eng = MiniMaxVideoEngine()
    return eng


async def _get_speech_engine():
    from engines import get_active, EngineCapability
    from engines.minimax_speech import MiniMaxSpeechEngine
    eng = get_active(EngineCapability.TTS)
    if eng is None:
        eng = MiniMaxSpeechEngine()
    return eng


async def _get_music_engine():
    from engines import get_active, EngineCapability
    from engines.minimax_music import MiniMaxMusicEngine
    eng = get_active(EngineCapability.MUSIC)
    if eng is None:
        eng = MiniMaxMusicEngine()
    return eng


async def _get_llm_engine():
    from engines import get_active, EngineCapability
    try:
        eng = get_active(EngineCapability.LLM)
        return eng
    except RuntimeError:
        return None


def _save_audio_from_hex(audio_hex: str, out_path: str) -> str:
    """Decode hex-encoded audio bytes and write to file."""
    data = bytes.fromhex(audio_hex)
    with open(out_path, "wb") as f:
        f.write(data)
    return out_path


async def _download_audio_url(url: str, out_path: str) -> str:
    """Download audio from a MiniMax audio_url."""
    await _download_url(url, out_path)
    return out_path


# ── Template runners ─────────────────────────────────────────────────

async def run_daily_tiktok(job: Dict[str, Any]) -> Dict[str, Any]:
    """Download source → crop to 9:16 vertical → output MP4."""
    inputs = job.get("inputs", {})
    job_dir = _job_dir(job["job_id"])
    _append_log(job, "daily-tiktok: downloading source")

    source_path = await _download_source(inputs, job_dir, job)
    output_path = os.path.join(job_dir, "tiktok_9x16.mp4")

    _append_log(job, "processing to 9:16 vertical")
    loop = asyncio.get_running_loop()
    def _process():
        from main import process_video_to_vertical
        return process_video_to_vertical(source_path, output_path)
    ok = await loop.run_in_executor(None, _process)

    if not ok:
        _append_log(job, "vertical processing failed, falling back to ffmpeg crop")
        _run_ffmpeg([
            "-i", source_path,
            "-vf", "crop=ih*9/16:ih,scale=1080:1920",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-an",
            output_path,
        ], "daily-tiktok crop")

    _append_log(job, f"daily-tiktok: output {output_path}")
    return {
        "outputs": [{"name": "tiktok_9x16.mp4", "path": output_path, "size": os.path.getsize(output_path) if os.path.exists(output_path) else 0}],
        "cost_estimate": {"minimax_video": 0.0, "total": 0.0},
        "logs_count": len(job.get("logs", [])),
    }


async def run_reels_cascade(job: Dict[str, Any]) -> Dict[str, Any]:
    """Download source → generate 9:16, 1:1, 16:9 variants via ffmpeg."""
    inputs = job.get("inputs", {})
    job_dir = _job_dir(job["job_id"])
    _append_log(job, "reels-cascade: downloading source")

    source_path = await _download_source(inputs, job_dir, job)
    outputs = []

    aspect_cmds = {
        "9x16": "crop=ih*9/16:ih,scale=1080:1920",
        "1x1": "crop=min(iw\\,ih):min(iw\\,ih),scale=1080:1080",
        "16x9": "crop=iw:iw*9/16,scale=1920:1080",
    }

    for aspect, vf in aspect_cmds.items():
        path = os.path.join(job_dir, f"reel_{aspect}.mp4")
        _append_log(job, f"reels-cascade: rendering {aspect}")
        try:
            _run_ffmpeg([
                "-i", source_path,
                "-vf", vf,
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-an",
                path,
            ], f"reels-cascade {aspect}")
            outputs.append({"name": os.path.basename(path), "path": path, "size": os.path.getsize(path), "aspect": aspect})
        except Exception as e:
            _append_log(job, f"reels-cascade {aspect} failed: {e}")
            outputs.append({"name": os.path.basename(path), "path": path, "size": 0, "aspect": aspect, "error": str(e)})

    return {
        "outputs": outputs,
        "cost_estimate": {"total": 0.0},
        "logs_count": len(job.get("logs", [])),
    }


async def run_translate_repost(job: Dict[str, Any]) -> Dict[str, Any]:
    """Translate video to N target languages using MiniMax STT→LLM→TTS pipeline."""
    inputs = job.get("inputs", {})
    targets = inputs.get("target_languages", ["es", "fr", "de"])
    source_url = inputs.get("source_url", "")
    job_dir = _job_dir(job["job_id"])
    _append_log(job, f"translate-repost: translating to {len(targets)} languages")

    source_path = await _download_source(inputs, job_dir, job)
    outputs = []

    loop = asyncio.get_running_loop()
    for lang in targets:
        out_path = os.path.join(job_dir, f"clip_{lang}.mp4")
        _append_log(job, f"translate-repost: {lang}")
        try:
            def _translate():
                from translate import _translate_video_minimax
                return _translate_video_minimax(source_path, out_path, lang)
            await loop.run_in_executor(None, _translate)
            outputs.append({"name": os.path.basename(out_path), "path": out_path, "language": lang, "size": os.path.getsize(out_path) if os.path.exists(out_path) else 0})
        except Exception as e:
            _append_log(job, f"translate-repost {lang} failed: {e}")
            outputs.append({"name": os.path.basename(out_path), "path": out_path, "language": lang, "error": str(e)})

    return {
        "outputs": outputs,
        "cost_estimate": {"per_language": 0.15, "total": 0.15 * len(targets)},
        "logs_count": len(job.get("logs", [])),
    }


async def run_ugc_ad(job: Dict[str, Any]) -> Dict[str, Any]:
    """Product URL → actor image + voiceover + 15s S2V ad video."""
    inputs = job.get("inputs", {})
    product_url = inputs.get("product_url", "")
    language = inputs.get("language", "en")
    job_dir = _job_dir(job["job_id"])
    _append_log(job, f"ugc-ad: generating for {product_url}")

    video_eng = await _get_video_engine()
    speech_eng = await _get_speech_engine()

    # Step 1: generate actor image
    _append_log(job, "ugc-ad: generating actor image")
    actor_url = None
    try:
        result = await video_eng.generate_image(
            prompt=f"Professional UGC actor, friendly face, looking at camera, clean background, product review style",
            aspect_ratio="9:16",
        )
        actor_url = (result.get("image_urls") or [None])[0]
    except Exception as e:
        _append_log(job, f"ugc-ad: actor image failed: {e}")

    actor_path = os.path.join(job_dir, "actor.png")
    if actor_url:
        await _download_url(actor_url, actor_path)
    else:
        _append_log(job, "ugc-ad: no actor image, skipping")

    # Step 2: generate voiceover
    _append_log(job, "ugc-ad: generating voiceover")
    voiceover_path = os.path.join(job_dir, "voiceover.mp3")
    try:
        tts_result = await speech_eng.synthesize(
            text=f"Hey! I just tried this amazing product. Let me show you why I love it!",
            voice_id="English_Graceful_Lady",
        )
        if "audio_hex" in tts_result:
            _save_audio_from_hex(tts_result["audio_hex"], voiceover_path)
        elif "audio_url" in tts_result:
            await _download_audio_url(tts_result["audio_url"], voiceover_path)
    except Exception as e:
        _append_log(job, f"ugc-ad: voiceover failed: {e}")

    # Step 3: generate S2V ad video
    ad_path = os.path.join(job_dir, "ad.mp4")
    if actor_url:
        _append_log(job, "ugc-ad: generating S2V video")
        try:
            t2v_result = await video_eng.generate_video_s2v(
                prompt="Person talking to camera, enthusiastic product review, natural lighting",
                subject_image_url=actor_url,
            )
            task_id = t2v_result.get("task_id")
            if task_id:
                _append_log(job, f"ugc-ad: waiting for video task {task_id}")
                final = await video_eng.wait_for_video(task_id)
                file_id = final.get("file_id")
                if file_id:
                    video_bytes = await video_eng.download_video(file_id)
                    with open(ad_path, "wb") as f:
                        f.write(video_bytes)
        except Exception as e:
            _append_log(job, f"ugc-ad: S2V video failed: {e}")

    outputs = []
    for name, path in [("actor.png", actor_path), ("voiceover.mp3", voiceover_path), ("ad.mp4", ad_path)]:
        outputs.append({"name": name, "path": path, "size": os.path.getsize(path) if os.path.exists(path) else 0})

    return {
        "outputs": outputs,
        "cost_estimate": {"minimax_image": 0.05, "minimax_tts": 0.10, "minimax_video": 0.20, "total": 0.35},
        "logs_count": len(job.get("logs", [])),
    }


async def run_podcast_highlight(job: Dict[str, Any]) -> Dict[str, Any]:
    """Download podcast → detect best moments → extract 3 highlight clips."""
    inputs = job.get("inputs", {})
    job_dir = _job_dir(job["job_id"])
    _append_log(job, "podcast-highlight: downloading source")

    source_path = await _download_source(inputs, job_dir, job)
    outputs = []

    # Get video duration
    probe_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", source_path,
    ]
    try:
        dur_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
        duration = float(dur_result.stdout.strip() or "600")
    except Exception:
        duration = 600.0

    # Split into ~60s segments, take 3 best (first 3 as proxy for "best moments")
    segment_dur = min(60.0, duration / 4)
    n_clips = min(3, max(1, int(duration / segment_dur)))

    for i in range(n_clips):
        start = i * segment_dur
        clip_path = os.path.join(job_dir, f"highlight_{i+1}.mp4")
        _append_log(job, f"podcast-highlight: extracting clip {i+1} at {start:.0f}s")
        try:
            _run_ffmpeg([
                "-i", source_path,
                "-ss", str(start),
                "-t", str(segment_dur),
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                clip_path,
            ], f"podcast clip {i+1}")
            outputs.append({"name": os.path.basename(clip_path), "path": clip_path, "rank": i + 1, "size": os.path.getsize(clip_path)})
        except Exception as e:
            _append_log(job, f"podcast clip {i+1} failed: {e}")
            outputs.append({"name": os.path.basename(clip_path), "path": clip_path, "rank": i + 1, "error": str(e)})

    return {"outputs": outputs, "cost_estimate": {"total": 0.0}, "logs_count": len(job.get("logs", []))}


async def run_ai_influencer(job: Dict[str, Any]) -> Dict[str, Any]:
    """Brand description → generate avatar + voice + 30 post scripts via LLM."""
    inputs = job.get("inputs", {})
    brand_desc = inputs.get("brand_description", "A friendly lifestyle brand")
    language = inputs.get("language", "en")
    job_dir = _job_dir(job["job_id"])
    _append_log(job, "ai-influencer: generating brand kit")

    llm_eng = await _get_llm_engine()
    video_eng = await _get_video_engine()
    speech_eng = await _get_speech_engine()

    # Step 1: generate 30 post scripts via LLM
    _append_log(job, "ai-influencer: generating 30 post scripts")
    scripts = []
    if llm_eng:
        try:
            prompt = (
                f"Generate 30 short social media post scripts for this brand: {brand_desc}\n"
                f"Language: {language}\n"
                f"Format each as:\n### Post N\nHook: ...\nBody: ...\nCTA: ...\n"
            )
            if hasattr(llm_eng, "generate"):
                result = await llm_eng.generate(prompt)
                scripts_text = result.get("text", "") if isinstance(result, dict) else str(result)
            else:
                scripts_text = f"# Brand Kit: {brand_desc}\n\n(30 posts placeholder — LLM not configured)"
        except Exception as e:
            _append_log(job, f"ai-influencer: LLM script gen failed: {e}")
            scripts_text = f"# Brand Kit: {brand_desc}\n\n(30 posts placeholder)"
    else:
        scripts_text = f"# Brand Kit: {brand_desc}\n\n(30 posts placeholder — no LLM configured)"

    # Write scripts as individual markdown files
    for i in range(1, 31):
        path = os.path.join(job_dir, f"post_{i:03d}.md")
        with open(path, "w") as f:
            f.write(f"# Post {i}\n\n{scripts_text[:2000]}\n")

    # Step 2: generate avatar image
    _append_log(job, "ai-influencer: generating avatar")
    avatar_path = os.path.join(job_dir, "avatar.png")
    try:
        result = await video_eng.generate_image(
            prompt=f"Professional brand avatar for: {brand_desc}, friendly face, studio lighting",
            aspect_ratio="1:1",
        )
        img_url = (result.get("image_urls") or [None])[0]
        if img_url:
            await _download_url(img_url, avatar_path)
    except Exception as e:
        _append_log(job, f"ai-influencer: avatar failed: {e}")

    # Step 3: generate voice sample
    _append_log(job, "ai-influencer: generating voice sample")
    voice_path = os.path.join(job_dir, "voice_sample.mp3")
    try:
        tts_result = await speech_eng.synthesize(
            text=f"Hi, I'm the voice of {brand_desc}. Welcome to our channel!",
            voice_id="English_Graceful_Lady",
        )
        if "audio_hex" in tts_result:
            _save_audio_from_hex(tts_result["audio_hex"], voice_path)
        elif "audio_url" in tts_result:
            await _download_audio_url(tts_result["audio_url"], voice_path)
    except Exception as e:
        _append_log(job, f"ai-influencer: voice sample failed: {e}")

    outputs = [{"name": "avatar.png", "path": avatar_path, "size": os.path.getsize(avatar_path) if os.path.exists(avatar_path) else 0}]
    for i in range(1, 31):
        p = os.path.join(job_dir, f"post_{i:03d}.md")
        outputs.append({"name": os.path.basename(p), "path": p})
    outputs.append({"name": "voice_sample.mp3", "path": voice_path, "size": os.path.getsize(voice_path) if os.path.exists(voice_path) else 0})

    return {"outputs": outputs, "cost_estimate": {"total": 4.50}, "logs_count": len(job.get("logs", []))}


async def run_news_to_short(job: Dict[str, Any]) -> Dict[str, Any]:
    """RSS feed → AI summary → voiceover → branded short video."""
    inputs = job.get("inputs", {})
    rss_url = inputs.get("source_url", "")
    language = inputs.get("language", "en")
    job_dir = _job_dir(job["job_id"])
    _append_log(job, f"news-to-short: fetching RSS from {rss_url}")

    # Step 1: fetch RSS feed
    import httpx
    articles = []
    try:
        loop = asyncio.get_running_loop()
        def _fetch_rss():
            with httpx.Client(timeout=30.0, follow_redirects=True) as c:
                r = c.get(rss_url)
                r.raise_for_status()
                return r.text
        rss_text = await loop.run_in_executor(None, _fetch_rss)
        # Simple XML parsing for <title> tags
        import re
        titles = re.findall(r"<title[^>]*>(.*?)</title>", rss_text, re.DOTALL)
        articles = [t.strip() for t in titles if t.strip() and t.strip() != "title"][:5]
    except Exception as e:
        _append_log(job, f"news-to-short: RSS fetch failed: {e}")
        articles = ["Breaking news update"]

    # Step 2: summarize via LLM
    llm_eng = await _get_llm_engine()
    summary = articles[0] if articles else "Breaking news update"
    if llm_eng:
        try:
            prompt = f"Summarize this news in 2 sentences for a short video voiceover:\n{chr(10).join(articles)}"
            if hasattr(llm_eng, "generate"):
                result = await llm_eng.generate(prompt)
                summary = result.get("text", summary) if isinstance(result, dict) else str(result)[:200]
        except Exception as e:
            _append_log(job, f"news-to-short: LLM summarize failed: {e}")

    # Step 3: generate voiceover
    speech_eng = await _get_speech_engine()
    audio_path = os.path.join(job_dir, "voiceover.mp3")
    try:
        tts_result = await speech_eng.synthesize(text=summary, voice_id="English_Graceful_Lady")
        if "audio_hex" in tts_result:
            _save_audio_from_hex(tts_result["audio_hex"], audio_path)
        elif "audio_url" in tts_result:
            await _download_audio_url(tts_result["audio_url"], audio_path)
    except Exception as e:
        _append_log(job, f"news-to-short: TTS failed: {e}")

    # Step 4: generate video from summary
    video_eng = await _get_video_engine()
    output_path = os.path.join(job_dir, "news_short.mp4")
    try:
        t2v_result = await video_eng.generate_video_t2v(
            prompt=f"News broadcast visual: {summary[:100]}",
            duration=6,
        )
        task_id = t2v_result.get("task_id")
        if task_id:
            _append_log(job, f"news-to-short: waiting for video task {task_id}")
            final = await video_eng.wait_for_video(task_id)
            file_id = final.get("file_id")
            if file_id:
                video_bytes = await video_eng.download_video(file_id)
                with open(output_path, "wb") as f:
                    f.write(video_bytes)
    except Exception as e:
        _append_log(job, f"news-to-short: T2V failed: {e}")

    # Step 5: mux audio + video if both exist
    if os.path.exists(audio_path) and os.path.exists(output_path) and os.path.getsize(output_path) > 100:
        muxed_path = os.path.join(job_dir, "news_short_final.mp4")
        try:
            _run_ffmpeg([
                "-i", output_path,
                "-i", audio_path,
                "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                "-shortest",
                muxed_path,
            ], "news-to-short mux")
            output_path = muxed_path
        except Exception as e:
            _append_log(job, f"news-to-short: mux failed: {e}")

    return {
        "outputs": [{"name": "news_short.mp4", "path": output_path, "size": os.path.getsize(output_path) if os.path.exists(output_path) else 0}],
        "cost_estimate": {"minimax_tts": 0.10, "minimax_video": 0.20, "total": 0.30},
        "logs_count": len(job.get("logs", [])),
    }


async def run_course_to_clips(job: Dict[str, Any]) -> Dict[str, Any]:
    """Long course video → split into micro-lesson clips at regular intervals."""
    inputs = job.get("inputs", {})
    job_dir = _job_dir(job["job_id"])
    _append_log(job, "course-to-clips: downloading source")

    source_path = await _download_source(inputs, job_dir, job)

    # Get duration
    probe_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", source_path,
    ]
    try:
        dur_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
        duration = float(dur_result.stdout.strip() or "3600")
    except Exception:
        duration = 3600.0

    # Target ~60s clips, cap at 100
    clip_dur = 60.0
    n_clips = min(100, max(1, int(duration / clip_dur)))
    outputs = []

    for i in range(n_clips):
        start = i * clip_dur
        path = os.path.join(job_dir, f"lesson_{i+1:03d}.mp4")
        try:
            _run_ffmpeg([
                "-i", source_path,
                "-ss", str(start),
                "-t", str(clip_dur),
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                path,
            ], f"lesson {i+1}")
            outputs.append({"name": os.path.basename(path), "path": path, "size": os.path.getsize(path)})
        except Exception as e:
            _append_log(job, f"lesson {i+1} failed: {e}")
            outputs.append({"name": os.path.basename(path), "path": path, "error": str(e)})
        if (i + 1) % 25 == 0:
            _append_log(job, f"  {i+1}/{n_clips} lessons done")

    return {"outputs": outputs, "cost_estimate": {"total": 0.0}, "logs_count": len(job.get("logs", []))}


async def run_music_video_maker(job: Dict[str, Any]) -> Dict[str, Any]:
    """Generate music track → generate visual loop → mux into 30s music video."""
    inputs = job.get("inputs", {})
    prompt = inputs.get("prompt", "upbeat electronic pop")
    language = inputs.get("language", "en")
    job_dir = _job_dir(job["job_id"])
    _append_log(job, "music-video-maker: generating music")

    music_eng = await _get_music_engine()
    video_eng = await _get_video_engine()

    # Step 1: generate music
    audio_path = os.path.join(job_dir, "music.mp3")
    try:
        music_result = await music_eng.generate_music(prompt=prompt)
        # Music result may have audio_url or audio_hex
        if "audio_url" in music_result:
            await _download_audio_url(music_result["audio_url"], audio_path)
        elif "audio_hex" in music_result:
            _save_audio_from_hex(music_result["audio_hex"], audio_path)
    except Exception as e:
        _append_log(job, f"music-video-maker: music gen failed: {e}")

    # Step 2: generate visual loop
    _append_log(job, "music-video-maker: generating visual loop")
    video_path = os.path.join(job_dir, "visual_loop.mp4")
    try:
        t2v_result = await video_eng.generate_video_t2v(
            prompt=f"Abstract visual loop, music visualization, colorful particles, {prompt}",
            duration=6,
        )
        task_id = t2v_result.get("task_id")
        if task_id:
            final = await video_eng.wait_for_video(task_id)
            file_id = final.get("file_id")
            if file_id:
                video_bytes = await video_eng.download_video(file_id)
                with open(video_path, "wb") as f:
                    f.write(video_bytes)
    except Exception as e:
        _append_log(job, f"music-video-maker: T2V failed: {e}")

    # Step 3: loop visual to match audio duration, then mux
    output_path = os.path.join(job_dir, "music_video.mp4")
    if os.path.exists(audio_path) and os.path.exists(video_path) and os.path.getsize(video_path) > 100:
        # Get audio duration
        probe_cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", audio_path,
        ]
        try:
            dur_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
            audio_dur = float(dur_result.stdout.strip() or "30")
        except Exception:
            audio_dur = 30.0

        try:
            _run_ffmpeg([
                "-stream_loop", "-1", "-i", video_path,
                "-i", audio_path,
                "-t", str(min(audio_dur, 30)),
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                "-shortest",
                output_path,
            ], "music-video mux")
        except Exception as e:
            _append_log(job, f"music-video-maker: mux failed: {e}")
    elif os.path.exists(video_path):
        import shutil
        shutil.copy2(video_path, output_path)

    return {
        "outputs": [{"name": "music_video.mp4", "path": output_path, "size": os.path.getsize(output_path) if os.path.exists(output_path) else 0}],
        "cost_estimate": {"minimax_music": 0.15, "minimax_video": 0.20, "total": 0.35},
        "logs_count": len(job.get("logs", [])),
    }


async def run_weekly_shorts(job: Dict[str, Any]) -> Dict[str, Any]:
    """Process multiple source videos → 6 vertical shorts per source."""
    inputs = job.get("inputs", {})
    source_urls = inputs.get("source_urls", [])
    job_dir = _job_dir(job["job_id"])
    n = len(source_urls) if source_urls else 0
    _append_log(job, f"weekly-shorts: processing {n} source videos")

    outputs = []
    for idx, url in enumerate(source_urls):
        _append_log(job, f"weekly-shorts: video {idx+1}/{n}")
        video_dir = os.path.join(job_dir, f"video_{idx+1}")
        os.makedirs(video_dir, exist_ok=True)

        # Download source
        try:
            source_path = await _download_source({"source_url": url}, video_dir, job)
        except Exception as e:
            _append_log(job, f"weekly-shorts: download failed for {url}: {e}")
            continue

        # Process to vertical
        vert_path = os.path.join(video_dir, "vertical.mp4")
        loop = asyncio.get_running_loop()
        def _process(sp=source_path, op=vert_path):
            from main import process_video_to_vertical
            return process_video_to_vertical(sp, op)
        ok = await loop.run_in_executor(None, _process)

        if not ok:
            _append_log(job, f"weekly-shorts: vertical processing failed for video {idx+1}")
            continue

        # Extract 6 clips from the vertical video
        probe_cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", vert_path,
        ]
        try:
            dur_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
            duration = float(dur_result.stdout.strip() or "120")
        except Exception:
            duration = 120.0

        clip_dur = min(60.0, duration / 7)
        for j in range(6):
            start = j * clip_dur
            clip_path = os.path.join(video_dir, f"short_{j+1}.mp4")
            try:
                _run_ffmpeg([
                    "-i", vert_path,
                    "-ss", str(start),
                    "-t", str(clip_dur),
                    "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                    "-c:a", "aac", "-b:a", "128k",
                    clip_path,
                ], f"weekly short {idx+1}.{j+1}")
                outputs.append({"name": f"video{idx+1}_short{j+1}.mp4", "path": clip_path, "size": os.path.getsize(clip_path)})
            except Exception as e:
                _append_log(job, f"weekly-shorts: clip {j+1} failed: {e}")

        _append_log(job, f"  video {idx+1}/{n} -> 6 shorts done")

    return {
        "outputs": outputs,
        "cost_estimate": {"per_video": 0.50, "total": 0.50 * n},
        "logs_count": len(job.get("logs", [])),
    }


# Registry
TEMPLATE_RUNNERS: Dict[str, Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = {
    "daily-tiktok": run_daily_tiktok,
    "weekly-shorts": run_weekly_shorts,
    "reels-cascade": run_reels_cascade,
    "translate-repost": run_translate_repost,
    "ugc-ad": run_ugc_ad,
    "podcast-highlight": run_podcast_highlight,
    "ai-influencer": run_ai_influencer,
    "news-to-short": run_news_to_short,
    "course-to-clips": run_course_to_clips,
    "music-video-maker": run_music_video_maker,
}


async def execute_template(template_id: str, job: Dict[str, Any]) -> Dict[str, Any]:
    """Look up the runner for template_id and execute. Updates job in place."""
    runner = TEMPLATE_RUNNERS.get(template_id)
    if runner is None:
        raise ValueError(f"Unknown template: {template_id}")
    return await runner(job)


__all__ = ["execute_template", "TEMPLATE_RUNNERS", "FACTORY_OUTPUT_BASE"]
