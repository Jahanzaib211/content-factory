"""Engine registry unit tests.

Validates the engines package: registry, capability coverage, API key handling.
Run: pytest tests/test_engines_registry.py -v
"""
import pytest

from engines import (
    list_providers,
    get_engine,
    FeatureFlags,
    EngineCapability,
)


def test_list_providers_takes_capability_arg():
    """list_providers(capability) returns a list of provider dicts."""
    out = list_providers(EngineCapability.LLM)
    assert isinstance(out, list)
    if out:
        e = out[0]
        assert "provider_id" in e
        assert "display_name" in e
        assert "capability" in e


def test_all_capabilities_return_lists():
    """Every EngineCapability must produce a list (possibly empty)."""
    for cap in EngineCapability:
        out = list_providers(cap)
        assert isinstance(out, list), f"{cap.value} returned non-list"


def test_critical_capabilities_have_providers():
    """Core capabilities must each have at least one provider."""
    for cap in (EngineCapability.LLM, EngineCapability.TTS, EngineCapability.STORAGE,
                EngineCapability.SOCIAL_POST, EngineCapability.STT):
        out = list_providers(cap)
        assert len(out) >= 1, f"{cap.value} has no providers"


def test_get_engine_returns_active_engine():
    """get_engine(capability) returns the active engine for known capability."""
    try:
        eng = get_engine(EngineCapability.LLM)
    except RuntimeError:
        pytest.skip("LLM engine not configured (no key)")
    if eng is None:
        pytest.skip("LLM engine returned None")
    assert hasattr(eng, "name") or hasattr(eng, "provider_id")


def test_get_engine_unknown_capability_raises():
    """get_engine on a bad capability should not silently return None."""
    with pytest.raises((RuntimeError, AttributeError, ValueError, TypeError, KeyError)):
        get_engine("__definitely_not_a_real_capability__")


def test_feature_flags_use_minimax_video_default_true():
    """Default behaviour: use_minimax_video defaults to True (env-controlled)."""
    import os
    saved = os.environ.pop("USE_MINIMAX_VIDEO", None)
    try:
        flags = FeatureFlags()
        assert flags.use_minimax_video() is True
    finally:
        if saved is not None:
            os.environ["USE_MINIMAX_VIDEO"] = saved


def test_feature_flags_use_minimax_video_respects_env():
    """With USE_MINIMAX_VIDEO=0, use_minimax_video should be False."""
    import os
    os.environ["USE_MINIMAX_VIDEO"] = "0"
    try:
        flags = FeatureFlags()
        assert flags.use_minimax_video() is False
    finally:
        os.environ.pop("USE_MINIMAX_VIDEO", None)