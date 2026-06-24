"""Backend endpoint smoke tests using FastAPI TestClient.

Validates routes exist, accept JSON, and return non-500 responses.
Mocks the engines where necessary so no live API keys are required.

Run: pytest tests/test_endpoints.py -v
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    import os
    os.environ.pop("MINIMAX_API_KEY", None)
    os.environ.pop("GEMINI_API_KEY", None)
    from app import app
    return TestClient(app)


# ---- Health & Engine Registry ----------------------------------------------

def test_engines_list_returns_capability_dict(client):
    """GET /api/engines/list returns {capability: [provider_dicts]}."""
    r = client.get("/api/engines/list")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "llm" in body
    assert "tts" in body
    assert isinstance(body["llm"], list)
    assert len(body["llm"]) >= 1


def test_engines_health(client):
    r = client.get("/api/engines/health")
    assert r.status_code == 200


def test_feature_flags_endpoint(client):
    r = client.get("/api/engines/feature-flags")
    assert r.status_code == 200
    assert isinstance(r.json(), dict)


# ---- Translation -----------------------------------------------------------

def test_translate_languages(client):
    r = client.get("/api/translate/languages")
    assert r.status_code == 200
    body = r.json()
    assert "languages" in body or isinstance(body, list)


# ---- Factory ---------------------------------------------------------------

def test_factory_templates_returns_at_least_10(client):
    r = client.get("/api/factory/templates")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "templates" in body
    assert len(body["templates"]) >= 10, f"expected ≥10 templates, got {len(body['templates'])}"


def test_factory_templates_have_required_fields(client):
    r = client.get("/api/factory/templates")
    body = r.json()
    for t in body["templates"]:
        for field in ("id", "name", "description", "estimated_minutes"):
            assert field in t, f"template {t.get('id', '?')} missing {field}"


def test_factory_templates_ids_unique(client):
    r = client.get("/api/factory/templates")
    body = r.json()
    ids = [t["id"] for t in body["templates"]]
    assert len(ids) == len(set(ids)), f"duplicate ids: {ids}"


def test_factory_jobs_list(client):
    """GET /api/factory/jobs returns a list (may be empty)."""
    r = client.get("/api/factory/jobs")
    assert r.status_code == 200
    body = r.json()
    assert "jobs" in body or isinstance(body, list)


# ---- Social ----------------------------------------------------------------

def test_social_connections_returns_per_platform(client):
    """Response shape: {youtube: {...}, tiktok: {...}, instagram: {...}}."""
    r = client.get("/api/social/connections")
    assert r.status_code == 200
    body = r.json()
    assert "youtube" in body
    assert "tiktok" in body
    assert "instagram" in body


def test_social_post_requires_payload(client):
    """POST /api/social/post with no payload → validation error (not 5xx)."""
    r = client.post("/api/social/post", json={})
    assert r.status_code in (400, 422), f"got {r.status_code}: {r.text[:120]}"


# ---- Voice Lab -------------------------------------------------------------

def test_voice_lab_library(client):
    r = client.get("/api/voice-lab/library")
    assert r.status_code == 200


def test_voice_lab_clone_requires_payload(client):
    r = client.post("/api/voice-lab/clone", json={})
    assert r.status_code in (400, 422)


# ---- i18n ------------------------------------------------------------------

def test_i18n_messages_nonempty(client):
    r = client.get("/api/i18n/messages")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, dict)
    assert len(body) >= 1
    # English must always be present
    assert "en" in body


def test_i18n_messages_english_has_keys(client):
    r = client.get("/api/i18n/messages")
    body = r.json()
    en = body.get("en", {})
    assert len(en) >= 5, f"english translations too few: {len(en)}"


# ---- Observability ---------------------------------------------------------

def test_observability_event_accepts_json(client):
    r = client.post("/api/observability/langfuse/event", json={
        "trace_id": "test-trace-1",
        "event_type": "test",
        "data": {"hello": "world"},
    })
    assert r.status_code in (200, 202)


# ---- Core Processing -------------------------------------------------------

def test_process_missing_url_returns_400(client):
    r = client.post("/api/process", json={})
    assert r.status_code in (400, 422)


def test_status_unknown_job(client):
    r = client.get("/api/status/does-not-exist")
    assert r.status_code in (200, 404)


def test_no_5xx_on_key_routes(client):
    """Smoke: probe key routes, all must respond 2xx/4xx (never 5xx)."""
    for method, path, body in [
        ("POST", "/api/translate", {}),
        ("POST", "/api/subtitle", {}),
        ("POST", "/api/hook", {}),
        ("POST", "/api/edit", {}),
        ("POST", "/api/voice-lab/test", {}),
    ]:
        if method == "POST":
            r = client.post(path, json=body)
        else:
            r = client.get(path)
        assert r.status_code < 500, f"{method} {path} → {r.status_code}: {r.text[:120]}"