# Tests

This directory contains the full test suite for **Content Factory**.

## Layout

```
tests/
├── e2e/                          # Playwright tests (run on host)
│   ├── smoke.py                  # original 6-step smoke
│   └── full.py                   # full suite (smoke + i18n + a11y + responsive + storage)
├── test_engines_registry.py      # engines package unit tests
├── test_endpoints.py             # FastAPI endpoint smoke tests
├── test_factory_runner.py        # factory template + runner tests
└── test_vram_orchestrator.py     # GPU orchestrator unit tests
```

## Backend (pytest)

```bash
# inside backend container (has fastapi + httpx):
docker exec -u root -w /app openshorts-backend \
  python3 -m pytest tests/ -v --tb=short

# locally:
pip install fastapi pytest pytest-asyncio httpx
python3 -m pytest tests/ -v
```

Coverage:
- `test_engines_registry.py` — engine registry, capability coverage, feature flags
- `test_endpoints.py` — every documented /api/* route, asserts no 5xx
- `test_factory_runner.py` — 10 factory templates, unique IDs, required fields
- `test_vram_orchestrator.py` — Redis-backed GPU lock no-op fallback

## Frontend (Playwright on host)

The Alpine container can't run glibc Chromium, so Playwright runs on the host
with the locally-installed Chromium 1228.

```bash
# Verify Chromium path exists
ls /home/jahanzaib/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome

# Run smoke only:
python3 tests/e2e/smoke.py

# Run full suite (smoke + i18n + a11y + responsive + storage):
python3 tests/e2e/full.py
python3 tests/e2e/full.py --only a11y
```

`CHROMIUM_PATH`, `DASHBOARD_URL`, `BACKEND_URL` env vars override defaults.

## CI

See `.github/workflows/ci.yml`. Runs:
1. Backend pytest (ubuntu-latest)
2. Frontend `npm run lint`
3. Frontend `npm run build`
4. Playwright smoke (start backend + frontend preview, then run full suite)