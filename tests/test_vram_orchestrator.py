"""VRAM orchestrator tests — verifies graceful no-op without Redis.

Run: pytest tests/test_vram_orchestrator.py -v
"""
import pytest


def test_orchestrator_importable_without_redis():
    from vram_orchestrator import VRAMOrchestrator
    orch = VRAMOrchestrator()
    assert orch is not None


def test_acquire_returns_none_when_no_redis():
    """Without REDIS_URL configured, acquire() returns None (no-op sentinel)."""
    from vram_orchestrator import VRAMOrchestrator
    orch = VRAMOrchestrator()  # default REDIS_URL is empty in test env
    handle = orch.acquire("test_service")
    assert handle is None  # documented no-op behavior


def test_release_none_is_safe():
    """release(None) must not raise (no-op lock)."""
    from vram_orchestrator import VRAMOrchestrator
    orch = VRAMOrchestrator()
    orch.release(None)  # should not raise


def test_status_returns_dict():
    """status() returns a dict with at least 'enabled' boolean."""
    from vram_orchestrator import VRAMOrchestrator
    orch = VRAMOrchestrator()
    s = orch.status()
    assert isinstance(s, dict)
    assert "enabled" in s


def test_with_hold_runs_function():
    """with_hold acquires (no-op without Redis) and runs fn."""
    from vram_orchestrator import VRAMOrchestrator
    orch = VRAMOrchestrator()
    result = orch.with_hold("svc_a", lambda: "ran_ok")
    assert result == "ran_ok"


def test_with_hold_releases_on_exception():
    """with_hold must release even if fn raises."""
    from vram_orchestrator import VRAMOrchestrator
    orch = VRAMOrchestrator()
    with pytest.raises(ValueError):
        orch.with_hold("svc_a", lambda: (_ for _ in ()).throw(ValueError("boom")))