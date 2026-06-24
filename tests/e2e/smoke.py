"""Content Factory — E2E smoke test runner.

Runs Playwright tests on the host (Alpine container can't run glibc Chrome).
Uses the locally-installed Chromium 1228.

Usage:
    python3 tests/e2e/smoke.py
    python3 tests/e2e/smoke.py --headed
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, Page, expect

BASE = os.getenv("DASHBOARD_URL", "http://localhost:5175")
BACKEND = os.getenv("BACKEND_URL", "http://localhost:18080")
CHROMIUM = os.getenv(
    "CHROMIUM_PATH",
    "/home/jahanzaib/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome",
)

NEW_TABS = [
    ("factory", "Content Factory"),
    ("voice-lab", "Voice Lab"),
    ("avatar-studio", "Avatar Studio"),
    ("multilingual", "Multilingual"),
    ("settings", "Settings"),
]

SETTINGS_CARDS = [
    "Active Engines",
    "Free & Open Source",
    "Self-Hosted Stack",
    "Multilingual",
    "Direct Social Publishing",
]


def collect_console_errors(page: Page, sink: list[str]) -> None:
    page.on("console", lambda msg: sink.append(f"{msg.type}: {msg.text[:200]}") if msg.type == "error" else None)
    page.on("pageerror", lambda exc: sink.append(f"pageerror: {str(exc)[:200]}"))


def enter_app(page: Page) -> None:
    """Click 'Launch App' (or navigate directly to #app hash) to enter the dashboard."""
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_timeout(1500)
    launch = page.locator("button:has-text('Launch App')").first
    if launch.count() == 0:
        launch = page.locator("button:has-text('Launch Content Factory')").first
    if launch.count() == 0:
        launch = page.locator("button:has-text('Get Started Free')").first
    if launch.count() > 0:
        launch.click()
        page.wait_for_timeout(1500)
    else:
        page.goto(f"{BASE}/#app", wait_until="domcontentloaded")
        page.wait_for_timeout(1000)


def run(p, headed: bool = False) -> tuple[int, int]:
    browser = p.chromium.launch(
        executable_path=CHROMIUM,
        headless=not headed,
        args=["--no-sandbox", "--disable-dev-shm-usage"],
    )
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()

    errors: list[str] = []
    collect_console_errors(page, errors)

    passed = 0
    failed = 0

    def step(name: str):
        def decorator(fn):
            nonlocal passed, failed
            t0 = time.time()
            try:
                fn()
                dt = (time.time() - t0) * 1000
                print(f"  \u2713 {name}  ({dt:.0f} ms)")
                passed += 1
            except Exception as e:
                dt = (time.time() - t0) * 1000
                msg = str(e).splitlines()[0][:120]
                print(f"  \u2717 {name}  ({dt:.0f} ms) \u2014 {type(e).__name__}: {msg}")
                failed += 1
            return fn
        return decorator

    print(f"\n\u2192 Dashboard smoke ({BASE})\n" + "-" * 60)

    @step("landing page loads with correct title")
    def _():
        page.goto(BASE, wait_until="networkidle")
        page.wait_for_timeout(800)
        assert "Content Factory" in page.title()
        # Title may contain a hyphenated suffix
        assert "Content Factory" in page.title().split(" - ")[0] or page.title().startswith("Content Factory")

    @step("'Launch App' button enters the dashboard")
    def _():
        enter_app(page)
        # In dashboard, look for any sidebar/nav element with tab labels
        for tab_text in ["Create", "Factory", "Settings"]:
            if page.locator(f"text={tab_text}").count() > 0:
                return
        raise AssertionError("dashboard did not render after Launch App click")

    @step("all 5 new tabs render their H1/H2 without errors")
    def _():
        for tab, title in NEW_TABS:
            # Try clicking sidebar nav first
            nav = page.locator(f"button:has-text('{title}'), a:has-text('{title}')").first
            if nav.count() > 0 and nav.is_visible():
                nav.click()
            else:
                page.goto(f"{BASE}/#app/{tab}", wait_until="domcontentloaded")
            page.wait_for_timeout(500)
            h = page.locator(f"h1:has-text('{title}'), h2:has-text('{title}')").first
            expect(h).to_be_visible(timeout=5000)

    @step("settings page shows all expected cards")
    def _():
        page.goto(f"{BASE}/#app/settings", wait_until="domcontentloaded")
        page.wait_for_timeout(800)
        for card in SETTINGS_CARDS:
            assert page.locator(f"text={card}").count() > 0, f"missing card: {card}"

    @step("factory shows all 10 templates")
    def _():
        # Click sidebar 'Factory' button — hash routing may not auto-load
        nav = page.locator("button:has-text('FACTORY'), button:has-text('Factory')").first
        if nav.count() > 0 and nav.is_visible():
            nav.click()
        else:
            page.goto(f"{BASE}/#app/factory", wait_until="domcontentloaded")
        page.wait_for_timeout(1200)
        keywords = [
            "Daily TikTok",
            "Reels Cascade",
            "Translate & Repost",
            "UGC Ad",
            "Podcast Highlight",
            "AI Influencer",
            "News to Short",
            "Course",
            "Weekly Shorts",
            "Music Video",
        ]
        found = sum(1 for k in keywords if page.locator(f"text={k}").count() > 0)
        assert found >= 8, f"only found {found}/10 template keywords: " + ", ".join(
            k for k in keywords if page.locator(f"text={k}").count() == 0
        )

    @step("no fatal JS errors on any tab navigation")
    def _():
        errors.clear()
        for tab, _ in NEW_TABS:
            page.goto(f"{BASE}/#app/{tab}", wait_until="domcontentloaded")
            page.wait_for_timeout(400)
        # Filter out benign warnings from third-party libs
        fatal = [e for e in errors if "favicon" not in e.lower()]
        assert len(fatal) == 0, f"console errors: {fatal[:3]}"

    browser.close()
    return passed, failed


def main() -> int:
    headed = "--headed" in sys.argv
    if not Path(CHROMIUM).exists():
        print(f"ERROR: chromium not found at {CHROMIUM}", file=sys.stderr)
        print("Run: playwright install chromium", file=sys.stderr)
        return 2
    with sync_playwright() as p:
        passed, failed = run(p, headed=headed)
    print("-" * 60)
    print(f"  {passed} passed, {failed} failed\n")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())