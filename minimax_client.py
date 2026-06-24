"""
Unified AI provider client.

Exposes a single `models.generate_content(...)` interface that delegates to
either Google Gemini (google-genai SDK) or MiniMax (OpenAI-compatible HTTP).

Usage:
    from minimax_client import get_client

    client = get_client("gemini", api_key=...)
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)

    client = get_client("minimax", api_key=...)
    response = client.models.generate_content(model="MiniMax-M3", contents=prompt)
"""

import os
import json
import time
import base64
import mimetypes
from typing import Any, List, Optional, Union


# ---------- Provider registry ----------

GEMINI = "gemini"
MINIMAX = "minimax"

# MiniMax (MiniMax) uses an OpenAI-compatible Chat Completions API.
# Models available on Plus tier:
#   - MiniMax-M3     : flagship reasoning+multimodal model (1M context)
#   - MiniMax-M2.7   : previous generation
#   - Image / speech / music also available
MINIMAX_BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.MiniMax.io/v1")
MINIMAX_DEFAULT_MODEL = os.getenv("MINIMAX_MODEL", "MiniMax-M3")
MINIMAX_VL_MODEL = os.getenv("MINIMAX_VL_MODEL", "MiniMax-M3")


def detect_provider(minimax_key: Optional[str], gemini_key: Optional[str]) -> str:
    """Pick the active provider.

    Prefer MiniMax when its key is set; fall back to Gemini. Returns the
    provider name (one of MINIMAX / GEMINI). Raises ValueError if neither is set.
    """
    if minimax_key:
        return MINIMAX
    if gemini_key:
        return GEMINI
    raise ValueError("No AI provider API key provided (set MiniMax or Gemini key).")


def resolve_key(minimax_key: Optional[str], gemini_key: Optional[str]) -> tuple[str, str]:
    """Return (provider, api_key) based on which keys are available."""
    provider = detect_provider(minimax_key, gemini_key)
    key = minimax_key if provider == MINIMAX else gemini_key
    return provider, key


def resolve_key_from_env() -> tuple[str, str]:
    """Same as resolve_key but reads from environment variables."""
    return resolve_key(
        os.getenv("MINIMAX_API_KEY"),
        os.getenv("GEMINI_API_KEY"),
    )


# ---------- MiniMax client (OpenAI-compatible) ----------


class MiniMaxGenerateResponse:
    """Mimics google-genai's response shape: .text, .usage_metadata, .candidates."""

    def __init__(self, text: str, usage: Optional[dict] = None):
        # M3 emits <think>...</think> reasoning blocks by default — strip them
        # so downstream JSON parsers don't choke.
        self.text = _strip_thinking(text)
        self.usage_metadata = _to_genai_usage(usage) if usage else None
        self.candidates = [{"content": {"parts": [{"text": self.text}]}}]


class MiniMaxFilesAPI:
    """File upload shim. MiniMax doesn't have a Gemini-like File API, so for
    video analysis we read the file and pass its bytes inline as a data URI
    (works for image inputs on VL models). For local video analysis the
    transcoded transcript is sent as text instead — see `analyze_with_minimax`.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key

    def upload(self, file: str):
        path = file
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        size = os.path.getsize(path)
        return _MiniMaxFile(name=path, size=size)


class _MiniMaxFile:
    def __init__(self, name: str, size: int):
        self.name = name
        self.size = size


class MiniMaxModelsAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate_content(
        self,
        model: Optional[str] = None,
        contents: Any = None,
        config: Any = None,
    ):
        """Generate content via MiniMax's /chat/completions endpoint.

        `contents` may be:
          - a plain str (text-only prompt)
          - a list of mixed Parts/strings/Files. For multimodal prompts we
            detect images/files and inline them as data URIs (VL models).
        """
        import httpx

        model_name = model or MINIMAX_DEFAULT_MODEL
        json_mode = bool(getattr(config, "response_mime_type", None) == "application/json") if config else False

        messages = _build_messages(contents)
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4096,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        url = f"{MINIMAX_BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=120.0) as client:
            resp = client.post(url, headers=headers, json=payload)

        if resp.status_code >= 400:
            raise RuntimeError(f"MiniMax API error {resp.status_code}: {resp.text[:500]}")

        data = resp.json()
        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return MiniMaxGenerateResponse(text=text, usage=data.get("usage"))


class MiniMaxClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.files = MiniMaxFilesAPI(api_key)
        self.models = MiniMaxModelsAPI(api_key)


# ---------- Gemini client (thin wrapper exposing the same interface) ----------


class GeminiGenerateResponse:
    def __init__(self, inner):
        self._inner = inner

    @property
    def text(self):
        return self._inner.text

    @property
    def usage_metadata(self):
        return getattr(self._inner, "usage_metadata", None)

    @property
    def candidates(self):
        return getattr(self._inner, "candidates", None)


class GeminiModelsAPI:
    def __init__(self, client):
        self._client = client

    def generate_content(self, model: Optional[str] = None, contents: Any = None, config: Any = None):
        kwargs = {}
        if config is not None:
            kwargs["config"] = config
        resp = self._client.models.generate_content(model=model, contents=contents, **kwargs)
        return GeminiGenerateResponse(resp)


class GeminiClientWrapper:
    def __init__(self, api_key: str):
        from google import genai as _genai
        self._client = _genai.Client(api_key=api_key)
        self.models = GeminiModelsAPI(self._client)
        self.files = self._client.files


# ---------- Factory ----------


def get_client(provider: str, api_key: str):
    provider = (provider or "").lower()
    if provider == MINIMAX:
        return MiniMaxClient(api_key=api_key)
    if provider == GEMINI:
        return GeminiClientWrapper(api_key=api_key)
    raise ValueError(f"Unknown AI provider: {provider!r}")


# ---------- Helpers ----------


def _strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks that MiniMax reasoning models emit."""
    import re
    if not text:
        return text
    # Strip the entire think block (multiline, greedy on closing tag)
    cleaned = re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL)
    return cleaned.strip()


def _to_genai_usage(usage: dict) -> Any:
    """Convert OpenAI-style usage into google-genai usage_metadata shape."""
    class _Usage:
        def __init__(self, d):
            self.prompt_token_count = d.get("prompt_tokens", 0)
            self.candidates_token_count = d.get("completion_tokens", 0)
            self.total_token_count = d.get("total_tokens", 0)
    return _Usage(usage)


def _file_to_data_uri(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    if not mime:
        mime = "application/octet-stream"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _build_messages(contents: Any) -> list:
    """Translate google-genai style `contents` to OpenAI chat messages."""
    if isinstance(contents, str):
        return [{"role": "user", "content": contents}]

    # If contents is a list, walk and merge parts into a single user message
    parts: list = []
    for item in contents:
        if isinstance(item, str):
            parts.append({"type": "text", "text": item})
            continue
        # google-genai Part objects expose .inline_data / .text
        text = getattr(item, "text", None)
        if text and not getattr(item, "inline_data", None) and not getattr(item, "file_data", None):
            parts.append({"type": "text", "text": text})
            continue
        inline = getattr(item, "inline_data", None)
        if inline is not None:
            data = getattr(inline, "data", None)
            mime = getattr(inline, "mime_type", "image/png")
            if data is not None:
                if isinstance(data, (bytes, bytearray)):
                    b64 = base64.b64encode(bytes(data)).decode("ascii")
                else:
                    b64 = data
                parts.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{b64}"},
                })
            continue
        # Our _MiniMaxFile shim → read & inline as data URI
        if isinstance(item, _MiniMaxFile):
            uri = _file_to_data_uri(item.name)
            parts.append({"type": "image_url", "image_url": {"url": uri}})
            continue
        # Last resort: stringify
        parts.append({"type": "text", "text": str(item)})

    if not parts:
        parts = [{"type": "text", "text": ""}]
    return [{"role": "user", "content": parts}]


def analyze_with_provider(
    provider: str,
    api_key: str,
    prompt: str,
    model: Optional[str] = None,
    json_mode: bool = False,
) -> MiniMaxGenerateResponse:
    """Convenience helper used by call sites that want a quick text-only call."""
    client = get_client(provider, api_key)
    config = None
    if json_mode:
        try:
            from google.genai import types as _types
            config = _types.GenerateContentConfig(response_mime_type="application/json")
        except Exception:
            class _Cfg:
                response_mime_type = "application/json"
            config = _Cfg()
    return client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )