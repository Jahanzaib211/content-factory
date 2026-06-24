"""
ElevenLabs Video Translation/Dubbing Module

Uses ElevenLabs Dubbing API to translate video audio to different languages.

Content Factory Phase 3: when USE_MINIMAX_TTS=1 and MINIMAX_API_KEY is set,
the `translate_video` function dispatches to a MiniMax-based pipeline that
1) transcribes the source audio with faster-whisper, 2) translates via the
MiniMax LLM, 3) re-synthesizes the target audio with MiniMax TTS in the
target language, and 4) remuxes the new audio with the original video
(voice-only dub, no lip sync).
"""

import os
import time
import asyncio
import httpx
import subprocess
from typing import Optional

try:
    from engines import FeatureFlags
    from engines.minimax_speech import MiniMaxSpeechEngine
    from minimax_client import get_client as get_ai_client
except Exception:  # pragma: no cover - engines package is always present in CF
    FeatureFlags = None
    MiniMaxSpeechEngine = None
    get_ai_client = None

ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"

# Supported target languages for dubbing
SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "pl": "Polish",
    "hi": "Hindi",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
    "ar": "Arabic",
    "ru": "Russian",
    "tr": "Turkish",
    "nl": "Dutch",
    "sv": "Swedish",
    "id": "Indonesian",
    "fil": "Filipino",
    "ms": "Malay",
    "vi": "Vietnamese",
    "th": "Thai",
    "uk": "Ukrainian",
    "el": "Greek",
    "cs": "Czech",
    "fi": "Finnish",
    "ro": "Romanian",
    "da": "Danish",
    "bg": "Bulgarian",
    "hr": "Croatian",
    "sk": "Slovak",
    "ta": "Tamil",
}


def create_dubbing_project(
    video_path: str,
    target_language: str,
    api_key: str,
    source_language: Optional[str] = None,
) -> dict:
    """
    Create a new dubbing project with ElevenLabs.

    Args:
        video_path: Path to the video file
        target_language: Target language code (e.g., 'es', 'fr', 'de')
        api_key: ElevenLabs API key
        source_language: Source language code (auto-detected if None)

    Returns:
        dict with dubbing_id and expected_duration_sec
    """
    url = f"{ELEVENLABS_API_BASE}/dubbing"

    headers = {
        "xi-api-key": api_key,
    }

    # Prepare form data
    data = {
        "target_lang": target_language,
        "mode": "automatic",
        "num_speakers": "0",
        "watermark": "false",
    }

    if source_language:
        data["source_lang"] = source_language

    # Open and send the video file
    with open(video_path, "rb") as video_file:
        files = {
            "file": (os.path.basename(video_path), video_file, "video/mp4")
        }

        print(f"[ElevenLabs] Creating dubbing project for {target_language}...")
        with httpx.Client(timeout=300.0) as client:
            response = client.post(url, headers=headers, data=data, files=files)

    if response.status_code not in [200, 201]:
        error_msg = response.text
        try:
            error_data = response.json()
            error_msg = error_data.get("detail", {}).get("message", response.text)
        except:
            pass
        raise Exception(f"ElevenLabs API error: {error_msg}")

    result = response.json()
    print(f"[ElevenLabs] Dubbing project created: {result.get('dubbing_id')}")
    return result


def get_dubbing_status(dubbing_id: str, api_key: str) -> dict:
    """
    Check the status of a dubbing project.

    Returns:
        dict with status ('dubbing', 'dubbed', 'failed') and other metadata
    """
    url = f"{ELEVENLABS_API_BASE}/dubbing/{dubbing_id}"

    headers = {
        "xi-api-key": api_key,
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Failed to get dubbing status: {response.text}")

    return response.json()


def download_dubbed_video(
    dubbing_id: str,
    target_language: str,
    output_path: str,
    api_key: str
) -> str:
    """
    Download the dubbed video file.

    Args:
        dubbing_id: The dubbing project ID
        target_language: Target language code
        output_path: Where to save the dubbed video
        api_key: ElevenLabs API key

    Returns:
        Path to the downloaded file
    """
    url = f"{ELEVENLABS_API_BASE}/dubbing/{dubbing_id}/audio/{target_language}"

    headers = {
        "xi-api-key": api_key,
    }

    print(f"[ElevenLabs] Downloading dubbed video...")
    with httpx.Client(timeout=120.0) as client:
        with client.stream("GET", url, headers=headers) as response:
            if response.status_code != 200:
                raise Exception(f"Failed to download dubbed video: {response.text}")

            with open(output_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=8192):
                    f.write(chunk)

    print(f"[ElevenLabs] Dubbed video saved to: {output_path}")
    return output_path


def translate_video(
    video_path: str,
    output_path: str,
    target_language: str,
    api_key: str,
    source_language: Optional[str] = None,
    max_wait_seconds: int = 600,
    poll_interval: int = 5,
) -> str:
    """
    Translate a video to a target language.

    Dispatches to the MiniMax pipeline (faster-whisper + MiniMax LLM +
    MiniMax TTS, voice-only dub) when USE_MINIMAX_TTS=1 and
    MINIMAX_API_KEY is set; otherwise uses the legacy ElevenLabs dubbing
    API (full voice cloning + lip timing).

    Returns:
        Path to the translated video
    """
    if (
        FeatureFlags is not None
        and FeatureFlags.use_minimax_tts()
        and os.getenv("MINIMAX_API_KEY")
    ):
        try:
            print(
                f"[translate] Active engine: MiniMax TTS pipeline "
                f"(target={target_language}, source={source_language or 'auto'})"
            )
            return _translate_video_minimax(
                video_path=video_path,
                output_path=output_path,
                target_language=target_language,
                source_language=source_language,
            )
        except Exception as e:
            print(f"[translate] MiniMax pipeline failed ({e}), falling back to ElevenLabs")

    # Legacy ElevenLabs path (preserved verbatim)
    return _translate_video_elevenlabs(
        video_path=video_path,
        output_path=output_path,
        target_language=target_language,
        api_key=api_key,
        source_language=source_language,
        max_wait_seconds=max_wait_seconds,
        poll_interval=poll_interval,
    )


def _translate_video_elevenlabs(
    video_path: str,
    output_path: str,
    target_language: str,
    api_key: str,
    source_language: Optional[str] = None,
    max_wait_seconds: int = 600,
    poll_interval: int = 5,
) -> str:
    """Legacy ElevenLabs dubbing (preserved verbatim)."""
    project = create_dubbing_project(
        video_path=video_path,
        target_language=target_language,
        api_key=api_key,
        source_language=source_language,
    )
    dubbing_id = project["dubbing_id"]
    expected_duration = project.get("expected_duration_sec", 60)
    print(f"[ElevenLabs] Dubbing ID: {dubbing_id}, Expected duration: {expected_duration}s")
    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        if elapsed > max_wait_seconds:
            raise Exception(f"Dubbing timed out after {max_wait_seconds} seconds")
        status = get_dubbing_status(dubbing_id, api_key)
        current_status = status.get("status", "unknown")
        print(f"[ElevenLabs] Status: {current_status} (elapsed: {int(elapsed)}s)")
        if current_status == "dubbed":
            return download_dubbed_video(
                dubbing_id=dubbing_id,
                target_language=target_language,
                output_path=output_path,
                api_key=api_key,
            )
        elif current_status == "failed":
            error = status.get("error", "Unknown error")
            raise Exception(f"Dubbing failed: {error}")
        time.sleep(poll_interval)


def _translate_video_minimax(
    video_path: str,
    output_path: str,
    target_language: str,
    source_language: Optional[str] = None,
) -> str:
    """MiniMax TTS-based translation: STT -> translate -> TTS -> remux.

    1. Extract audio with ffmpeg.
    2. Transcribe with faster-whisper (local, 99 languages).
    3. Translate with MiniMax LLM (preserves tone, handles idioms).
    4. Re-synthesize in target language via MiniMax TTS.
    5. Remux new audio with the original video (no lip sync).
    """
    audio_in = video_path + ".src.wav"
    audio_out = video_path + ".tts.mp3"
    cmd_extract = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-ac", "1", "-ar", "16000", audio_in,
    ]
    subprocess.run(cmd_extract, check=True, capture_output=True)

    # STT
    from faster_whisper import WhisperModel
    model = WhisperModel("small", device="cpu", compute_type="int8")
    src_lang = source_language or "auto"
    segments, info = model.transcribe(audio_in, language=src_lang if src_lang != "auto" else None)
    transcript = " ".join(seg.text.strip() for seg in segments)
    detected_lang = getattr(info, "language", src_lang or "en")
    print(f"[translate] STT: {len(transcript)} chars, detected={detected_lang}")

    # Translate via MiniMax LLM
    target_name = SUPPORTED_LANGUAGES.get(target_language, target_language)
    detected_name = SUPPORTED_LANGUAGES.get(detected_lang, detected_lang)
    prompt = (
        f"Translate the following transcript from {detected_name} to {target_name}. "
        "Preserve the speaker's tone, energy, and any onomatopoeia. "
        "Output only the translated text, no commentary.\n\n"
        f"TRANSCRIPT:\n{transcript}"
    )
    client = get_ai_client("minimax", os.environ["MINIMAX_API_KEY"])
    response = client.models.generate_content(
        model="MiniMax-M3",
        contents=[prompt],
        config=None,
    )
    translated = (response.text or "").strip()
    print(f"[translate] LLM: {len(translated)} chars translated")

    # TTS
    language_boost_map = {
        "en": "English", "es": "Spanish", "fr": "French", "de": "German",
        "it": "Italian", "pt": "Portuguese", "ru": "Russian", "ja": "Japanese",
        "ko": "Korean", "zh": "Chinese", "ar": "Arabic", "hi": "Hindi",
        "tr": "Turkish", "nl": "Dutch", "pl": "Polish", "id": "Indonesian",
        "vi": "Vietnamese", "th": "Thai", "uk": "Ukrainian", "el": "Greek",
        "sv": "Swedish", "cs": "Czech", "fi": "Finnish", "he": "Hebrew",
        "ms": "Malay", "ro": "Romanian", "da": "Danish", "no": "Norwegian",
        "hu": "Hungarian", "sk": "Slovak", "bg": "Bulgarian", "hr": "Croatian",
    }
    language_boost = language_boost_map.get(target_language, "auto")

    async def _tts() -> bytes:
        eng = MiniMaxSpeechEngine()
        res = await eng.synthesize(
            text=translated, voice_id="English_Graceful_Lady",
            model="speech-2.8-hd", language_boost=language_boost,
        )
        if not res.success:
            raise RuntimeError(f"MiniMax TTS failed: {res.error}")
        data = res.data or {}
        if "audio_url" in data and data["audio_url"]:
            r = httpx.get(data["audio_url"], timeout=120.0)
            r.raise_for_status()
            return r.content
        if "data" in data and isinstance(data["data"], dict):
            hex_audio = data["data"].get("audio", "")
            if hex_audio:
                import binascii
                return binascii.unhexlify(hex_audio)
        if "audio_hex" in data:
            import binascii
            return binascii.unhexlify(data["audio_hex"])
        raise RuntimeError("MiniMax TTS: no audio in response")

    audio_bytes = asyncio.run(_tts())
    with open(audio_out, "wb") as f:
        f.write(audio_bytes)
    print(f"[translate] TTS: {len(audio_bytes)} bytes -> {audio_out}")

    # Remux
    cmd_remux = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_out,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path,
    ]
    subprocess.run(cmd_remux, check=True, capture_output=True)
    try:
        os.remove(audio_in)
        os.remove(audio_out)
    except OSError:
        pass
    print(f"[translate] ✅ Remuxed: {output_path}")
    return output_path


def get_supported_languages() -> dict:
    """Return dict of supported language codes and names."""
    return SUPPORTED_LANGUAGES.copy()
