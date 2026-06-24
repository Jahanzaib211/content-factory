"""
LLM routing engine using LiteLLM.

LiteLLM gives us a single `completion()` interface that delegates to
OpenAI, Anthropic, Google Gemini, MiniMax, local vLLM, Ollama, etc.
It is the canonical OSS LLM router (51.4k stars, MIT) and is used
in production by Netflix, Rocket Money, etc.

The existing `minimax_client.py` continues to work — this is a parallel
additive path. The Settings UI engine picker will show both:
  - "MiniMax (minimax_client.py)" — current behavior
  - "LiteLLM router (multi-provider)" — opt-in, requires litellm pip install
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional

from .base import BaseEngine, EngineCapability, EngineHealth, EngineResult, engine_method, EngineError

log = logging.getLogger(__name__)


class LiteLLMRouterEngine(BaseEngine):
    provider_id = "litellm"
    display_name = "LiteLLM router (MiniMax / Gemini / Ollama / vLLM)"
    capability = EngineCapability.LLM
    cost_hint = "Provider-dependent; MiniMax ~$0.30/M tokens"
    hardware_hint = "any (cloud or local)"
    requires_key = False
    key_env_var = None

    def __init__(self) -> None:
        self.minimax_key = os.getenv("MINIMAX_API_KEY", "")
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.vllm_base = os.getenv("VLLM_API_BASE", "http://vllm:8001/v1")
        self.ollama_base = os.getenv("OLLAMA_API_BASE", "http://ollama:11434")

    def _resolve_model(self) -> str:
        """Pick the active model based on which keys are set + LiteLLM naming."""
        if self.minimax_key:
            return "openai/MiniMax-M3"  # OpenAI-compatible endpoint at api.MiniMax.io
        if self.gemini_key:
            return "gemini/gemini-2.0-flash"
        if self.openai_key:
            return "gpt-4o-mini"
        # Local fallback
        return f"hosted_vllm/{os.getenv('VLLM_MODEL', 'Qwen2.5-7B-Instruct-AWQ')}"

    def _api_base(self) -> Optional[str]:
        m = self._resolve_model()
        if m.startswith("openai/MiniMax"):
            return os.getenv("MINIMAX_BASE_URL", "https://api.MiniMax.io/v1")
        if m.startswith("hosted_vllm"):
            return self.vllm_base
        return None

    async def health(self) -> EngineHealth:
        if not (self.minimax_key or self.gemini_key or self.openai_key):
            return EngineHealth(
                healthy=False,
                detail="No API keys set (MINIMAX_API_KEY, GEMINI_API_KEY, or OPENAI_API_KEY)",
            )
        try:
            import litellm  # type: ignore  # noqa: F401
            return EngineHealth(healthy=True, detail=f"router ready, model={self._resolve_model()}")
        except ImportError as e:
            return EngineHealth(healthy=False, detail=f"litellm not installed: {e}")

    @engine_method
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """Generate text via the configured provider. Returns dict with `text`, `usage`, `model`."""
        try:
            import litellm  # type: ignore
        except ImportError as e:
            raise EngineError("litellm not installed. `pip install litellm`.") from e

        model = self._resolve_model()
        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        api_base = self._api_base()
        if api_base:
            kwargs["api_base"] = api_base
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = litellm.completion(**kwargs)
        except Exception as e:
            raise EngineError(f"LiteLLM completion failed: {type(e).__name__}: {e}") from e

        text = response.choices[0].message.content or ""
        usage = {}
        if hasattr(response, "usage") and response.usage:
            u = response.usage
            usage = {
                "prompt_tokens": getattr(u, "prompt_tokens", 0),
                "completion_tokens": getattr(u, "completion_tokens", 0),
                "total_tokens": getattr(u, "total_tokens", 0),
            }
        return {"text": text, "usage": usage, "model": model}


__all__ = ["LiteLLMRouterEngine"]
