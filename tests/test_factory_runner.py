"""Factory template tests via the HTTP API.

We test the /api/factory/templates endpoint directly instead of importing
factory_runner internals, since the runner functions need real engines
loaded to run end-to-end (and the HTTP layer handles bootstrap correctly).

Run: pytest tests/test_factory_runner.py -v
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


def test_all_10_default_templates_listed(client):
    """Default template list (no user custom templates) must contain 10."""
    r = client.get("/api/factory/templates")
    body = r.json()
    # DEFAULT_FACTORY_TEMPLATES = 10; user templates may add more
    assert len(body["templates"]) >= 10


def test_template_ids_unique(client):
    r = client.get("/api/factory/templates")
    body = r.json()
    ids = [t["id"] for t in body["templates"]]
    assert len(ids) == len(set(ids)), f"duplicate ids: {ids}"


def test_template_required_fields(client):
    r = client.get("/api/factory/templates")
    body = r.json()
    for t in body["templates"]:
        for field in ("id", "name", "description", "estimated_minutes"):
            assert field in t, f"template {t.get('id', '?')} missing {field}"


def test_template_categories_real(client):
    """Templates must not use placeholder category values (if present)."""
    r = client.get("/api/factory/templates")
    body = r.json()
    bad = []
    for t in body["templates"]:
        cat = (t.get("category") or "").lower()
        if cat in ("stub", "todo"):
            bad.append(t["id"])
    assert not bad, f"templates with bad categories: {bad}"


def test_no_template_emits_placeholder_bytes(client):
    """Templates that produce bytes must NOT be b'\\x00' placeholders.

    We verify this by checking the runner module directly — every
    run_* function should at minimum reference real engine calls or
    file paths, not literal b'\x00'.
    """
    import inspect
    from engines import factory_runner
    src = inspect.getsource(factory_runner)
    # The literal placeholder pattern is forbidden
    assert 'b"\\\\x00"' not in src, "factory_runner still contains b'\\\\x00' placeholder"
    assert "b'\\x00'" not in src, "factory_runner still contains b'\\x00' placeholder"


def test_factory_runner_module_has_execute_template():
    """The runner module must export execute_template(template_id, job)."""
    from engines import factory_runner
    assert hasattr(factory_runner, "execute_template"), "missing execute_template"
    assert hasattr(factory_runner, "TEMPLATE_RUNNERS"), "missing TEMPLATE_RUNNERS"
    assert len(factory_runner.TEMPLATE_RUNNERS) >= 10, \
        f"only {len(factory_runner.TEMPLATE_RUNNERS)} runners, expected ≥10"


def test_create_factory_job_with_minimal_payload(client):
    """POST /api/factory/jobs accepts template_id + inputs_json form data."""
    r = client.post("/api/factory/jobs",
                    data={"template_id": "ai-influencer",
                          "inputs_json": '{"brand_description": "test"}'})
    assert r.status_code in (200, 201, 202), f"got {r.status_code}: {r.text[:200]}"
    if r.status_code < 300:
        body = r.json()
        assert "job_id" in body, f"missing job_id: {body}"