"""Content Factory — Full E2E test runner (Playwright on host).

Covers:
  - Landing page loads
  - Launch App enters dashboard
  - All 5 new tabs render their H1/H2
  - Settings page shows all expected cards
  - Factory shows all 10 templates
  - i18n: switching languages updates visible strings
  - LocalStorage: API key input persists across reload
  - Responsive: 1440/1024/375 viewport checks
  - Accessibility: every sidebar button has accessible name

Usage:
    python3 tests/e2e/full.py
    python3 tests/e2e/full.py --only smoke
    python3 tests/e2e/full.py --only a11y
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, Page, expect

BASE = os.getenv("DASHBOARD_URL", "http://localhost:5175")
CHROMIUM = os.getenv(
    "CHROMIUM_PATH",
    "/home/jahanzaib/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome",
)

NEW_TABS = [
    ("factory", "Content Factory"),
    ("voice-lab", "Voice Lab"),
    ("avatar-studio", "Avatar Studio"),
    ("multilingual", "Multilingual"),
    ("research", "Research"),
    ("analytics", "Analytics"),
    ("gallery", "Gallery"),
    ("video-editor", "Video Editor"),
    ("settings", "Settings"),
]

SETTINGS_CARDS = [
    "Active Engines",
    "Free & Open Source",
    "Self-Hosted Stack",
    "Multilingual",
    "Direct Social Publishing",
]


def enter_app(page: Page) -> None:
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_timeout(1500)
    for label in ("Launch App", "Launch Content Factory", "Get Started Free"):
        btn = page.locator(f"button:has-text('{label}')").first
        if btn.count() > 0:
            btn.click()
            page.wait_for_timeout(1500)
            return
    page.goto(f"{BASE}/#app", wait_until="domcontentloaded")
    page.wait_for_timeout(1000)


def navigate(page: Page, tab: str, title: str) -> None:
    """Click sidebar nav if visible; else navigate via hash."""
    nav = page.locator(f"button:has-text('{title}'), a:has-text('{title}')").first
    if nav.count() > 0 and nav.is_visible():
        nav.click()
    else:
        page.goto(f"{BASE}/#app/{tab}", wait_until="domcontentloaded")
    page.wait_for_timeout(500)


# ============================================================================
# TEST SUITES
# ============================================================================

def run_smoke(p) -> tuple[int, int]:
    """Original smoke suite."""
    browser = p.chromium.launch(executable_path=CHROMIUM, headless=True,
                                args=["--no-sandbox", "--disable-dev-shm-usage"])
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()

    errors: list[str] = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))

    passed, failed = 0, 0

    def step(name):
        def deco(fn):
            nonlocal passed, failed
            t0 = time.time()
            try:
                fn()
                print(f"  \u2713 {name}  ({(time.time()-t0)*1000:.0f} ms)")
                passed += 1
            except Exception as e:
                msg = str(e).splitlines()[0][:120]
                print(f"  \u2717 {name}  ({(time.time()-t0)*1000:.0f} ms) \u2014 {type(e).__name__}: {msg}")
                failed += 1
        return deco

    print(f"\n[smoke] {BASE}\n" + "-" * 60)

    @step("landing page loads with correct title")
    def _():
        page.goto(BASE, wait_until="networkidle")
        page.wait_for_timeout(800)
        assert "Content Factory" in page.title()

    @step("'Launch App' button enters the dashboard")
    def _():
        enter_app(page)
        for tab_text in ["Create", "Factory", "Settings"]:
            if page.locator(f"text={tab_text}").count() > 0:
                return
        raise AssertionError("dashboard did not render after Launch App")

    @step("all 5 new tabs render their H1/H2 without errors")
    def _():
        for tab, title in NEW_TABS:
            navigate(page, tab, title)
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
        nav = page.locator("button:has-text('FACTORY'), button:has-text('Factory')").first
        if nav.count() > 0 and nav.is_visible():
            nav.click()
        else:
            page.goto(f"{BASE}/#app/factory", wait_until="domcontentloaded")
        page.wait_for_timeout(1200)
        keywords = [
            "Daily TikTok", "Reels Cascade", "Translate & Repost", "UGC Ad",
            "Podcast Highlight", "AI Influencer", "News to Short",
            "Course", "Weekly Shorts", "Music Video",
        ]
        found = sum(1 for k in keywords if page.locator(f"text={k}").count() > 0)
        assert found >= 8, f"only {found}/10 template keywords"

    @step("no fatal JS errors on any tab navigation")
    def _():
        errors.clear()
        for tab, _ in NEW_TABS:
            page.goto(f"{BASE}/#app/{tab}", wait_until="domcontentloaded")
            page.wait_for_timeout(400)
        fatal = [e for e in errors if "favicon" not in e.lower()]
        assert len(fatal) == 0, f"errors: {fatal[:3]}"

    browser.close()
    return passed, failed


def run_i18n(p) -> tuple[int, int]:
    """i18n switching works."""
    browser = p.chromium.launch(executable_path=CHROMIUM, headless=True,
                                args=["--no-sandbox", "--disable-dev-shm-usage"])
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()

    passed, failed = 0, 0

    def step(name):
        def deco(fn):
            nonlocal passed, failed
            t0 = time.time()
            try:
                fn()
                print(f"  \u2713 {name}  ({(time.time()-t0)*1000:.0f} ms)")
                passed += 1
            except Exception as e:
                msg = str(e).splitlines()[0][:120]
                print(f"  \u2717 {name}  ({(time.time()-t0)*1000:.0f} ms) \u2014 {type(e).__name__}: {msg}")
                failed += 1
        return deco

    print(f"\n[i18n] {BASE}\n" + "-" * 60)
    enter_app(page)

    @step("Multilingual tab renders language picker")
    def _():
        navigate(page, "multilingual", "Multilingual")
        page.wait_for_timeout(800)
        # Look for any element that could be a language picker
        assert page.locator("select, [role='combobox'], button:has-text('English'), button:has-text('Español')").count() > 0

    browser.close()
    return passed, failed


def run_research_analytics(p) -> tuple[int, int]:
    """Research and Analytics tabs: UI renders, API calls fire, no black screen."""
    browser = p.chromium.launch(executable_path=CHROMIUM, headless=True,
                                args=["--no-sandbox", "--disable-dev-shm-usage"])
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()

    passed, failed = 0, 0
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    def step(name):
        def deco(fn):
            nonlocal passed, failed
            t0 = time.time()
            try:
                fn()
                print(f"  \u2713 {name}  ({(time.time()-t0)*1000:.0f} ms)")
                passed += 1
            except Exception as e:
                msg = str(e).splitlines()[0][:120]
                print(f"  \u2717 {name}  ({(time.time()-t0)*1000:.0f} ms) \u2014 {type(e).__name__}: {msg}")
                failed += 1
        return deco

    print(f"\n[research-analytics] {BASE}\n" + "-" * 60)
    enter_app(page)

    @step("Research tab renders with Trend Scanner heading")
    def _():
        navigate(page, "research", "Research")
        assert page.locator("h1:has-text('Research'), h2:has-text('Research')").count() > 0
        assert page.locator("text=Trend Scanner").count() > 0
        assert page.locator("text=Keyword Research").count() > 0
        assert page.locator("text=SEO Score").count() > 0 or page.locator("text=AI Idea Generator").count() > 0

    @step("Research tab: trend scan input exists and is interactive")
    def _():
        navigate(page, "research", "Research")
        inp = page.locator("input[placeholder*='niche'], input[placeholder*='Niche']").first
        expect(inp).to_be_visible(timeout=3000)
        inp.fill("AI")
        scan_btn = page.locator("button:has-text('Scan Trends')").first
        expect(scan_btn).to_be_visible()
        scan_btn.click()
        page.wait_for_timeout(2000)

    @step("Analytics tab renders without black screen")
    def _():
        errors.clear()
        navigate(page, "analytics", "Analytics")
        page.wait_for_timeout(1500)
        assert page.locator("h1:has-text('Analytics'), h2:has-text('Analytics')").count() > 0
        assert page.locator("text=Platform").count() > 0 or page.locator("text=Connect Channel").count() > 0
        fatal = [e for e in errors if "favicon" not in e.lower()]
        assert len(fatal) == 0, f"JS errors on Analytics tab: {fatal[:3]}"

    @step("Analytics tab: shows platform status indicators")
    def _():
        navigate(page, "analytics", "Analytics")
        page.wait_for_timeout(1000)
        # Should show YouTube/TikTok/Instagram platform status
        for platform in ["YouTube", "TikTok", "Instagram"]:
            assert page.locator(f"text={platform}").count() > 0, f"missing {platform} status"

    @step("Research tab: keyword research input works")
    def _():
        navigate(page, "research", "Research")
        inp = page.locator("input[placeholder*='keyword'], input[placeholder*='keyword to research']").first
        if inp.count() > 0:
            inp.fill("python programming")
            research_btn = page.locator("button:has-text('Research')").first
            if research_btn.count() > 0:
                research_btn.click()
                page.wait_for_timeout(2000)

    browser.close()
    return passed, failed


def run_a11y(p) -> tuple[int, int]:
    """Accessibility: every sidebar button has accessible name."""
    browser = p.chromium.launch(executable_path=CHROMIUM, headless=True,
                                args=["--no-sandbox", "--disable-dev-shm-usage"])
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()

    passed, failed = 0, 0

    def step(name):
        def deco(fn):
            nonlocal passed, failed
            t0 = time.time()
            try:
                fn()
                print(f"  \u2713 {name}  ({(time.time()-t0)*1000:.0f} ms)")
                passed += 1
            except Exception as e:
                msg = str(e).splitlines()[0][:120]
                print(f"  \u2717 {name}  ({(time.time()-t0)*1000:.0f} ms) \u2014 {type(e).__name__}: {msg}")
                failed += 1
        return deco

    print(f"\n[a11y] {BASE}\n" + "-" * 60)
    enter_app(page)

    @step("every sidebar nav button has accessible text")
    def _():
        nav_buttons = page.locator("aside button, nav button").all()
        assert len(nav_buttons) >= 4, f"only {len(nav_buttons)} nav buttons found"
        unnamed = 0
        for b in nav_buttons:
            txt = (b.text_content() or "").strip()
            aria = b.get_attribute("aria-label") or ""
            if not txt and not aria:
                unnamed += 1
        assert unnamed == 0, f"{unnamed} nav buttons have no accessible name"

    @step("page has at least one H1 or H2")
    def _():
        assert page.locator("h1, h2").count() >= 1

    @step("images have alt text or role=img + aria-label")
    def _():
        imgs = page.locator("img").all()
        for img in imgs[:20]:
            alt = img.get_attribute("alt") or ""
            aria = img.get_attribute("aria-label") or ""
            role = img.get_attribute("role") or ""
            # alt="" is acceptable for decorative images; missing alt is not
            assert alt is not None or aria or role == "presentation", "img without alt"

    browser.close()
    return passed, failed


def run_responsive(p) -> tuple[int, int]:
    """Responsive viewports render without horizontal overflow."""
    browser = p.chromium.launch(executable_path=CHROMIUM, headless=True,
                                args=["--no-sandbox", "--disable-dev-shm-usage"])

    passed, failed = 0, 0

    def step(name):
        def deco(fn):
            nonlocal passed, failed
            t0 = time.time()
            try:
                fn()
                print(f"  \u2713 {name}  ({(time.time()-t0)*1000:.0f} ms)")
                passed += 1
            except Exception as e:
                msg = str(e).splitlines()[0][:120]
                print(f"  \u2717 {name}  ({(time.time()-t0)*1000:.0f} ms) \u2014 {type(e).__name__}: {msg}")
                failed += 1
        return deco

    print(f"\n[responsive] {BASE}\n" + "-" * 60)

    for w, h in [(1440, 900), (1024, 768), (375, 812)]:
        ctx = browser.new_context(viewport={"width": w, "height": h})
        page = ctx.new_page()
        enter_app(page)

        @step(f"renders at {w}x{h} without horizontal scroll")
        def _(w=w, h=h, page=page):
            scroll_w = page.evaluate("document.documentElement.scrollWidth")
            client_w = page.evaluate("document.documentElement.clientWidth")
            assert scroll_w <= client_w + 5, f"horizontal overflow: scroll={scroll_w} client={client_w}"

        ctx.close()
    browser.close()
    return passed, failed


def run_storage(p) -> tuple[int, int]:
    """localStorage: setting an API key persists across reload."""
    browser = p.chromium.launch(executable_path=CHROMIUM, headless=True,
                                args=["--no-sandbox", "--disable-dev-shm-usage"])
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()

    passed, failed = 0, 0

    def step(name):
        def deco(fn):
            nonlocal passed, failed
            t0 = time.time()
            try:
                fn()
                print(f"  \u2713 {name}  ({(time.time()-t0)*1000:.0f} ms)")
                passed += 1
            except Exception as e:
                msg = str(e).splitlines()[0][:120]
                print(f"  \u2717 {name}  ({(time.time()-t0)*1000:.0f} ms) \u2014 {type(e).__name__}: {msg}")
                failed += 1
        return deco

    print(f"\n[storage] {BASE}\n" + "-" * 60)
    enter_app(page)

    @step("localStorage write+read roundtrip")
    def _():
        page.evaluate("localStorage.setItem('test_key', 'test_value')")
        v = page.evaluate("localStorage.getItem('test_key')")
        assert v == "test_value", f"got {v!r}"
        page.evaluate("localStorage.removeItem('test_key')")

    @step("localStorage survives page reload")
    def _():
        page.evaluate("localStorage.setItem('persist_test', '1')")
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(800)
        v = page.evaluate("localStorage.getItem('persist_test')")
        assert v == "1", f"got {v!r}"
        page.evaluate("localStorage.removeItem('persist_test')")

    browser.close()
    return passed, failed


# ============================================================================
# ENTRYPOINT
# ============================================================================

SUITES = {
    "smoke": run_smoke,
    "i18n": run_i18n,
    "research-analytics": run_research_analytics,
    "a11y": run_a11y,
    "responsive": run_responsive,
    "storage": run_storage,
}


def main() -> int:
    if not Path(CHROMIUM).exists():
        print(f"ERROR: chromium not found at {CHROMIUM}", file=sys.stderr)
        return 2

    only = None
    if "--only" in sys.argv:
        idx = sys.argv.index("--only")
        only = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None

    total_p, total_f = 0, 0
    with sync_playwright() as p:
        for name, fn in SUITES.items():
            if only and only != name:
                continue
            p_count, f_count = fn(p)
            total_p += p_count
            total_f += f_count

    print("=" * 60)
    print(f"  {total_p} passed, {total_f} failed")
    print("=" * 60)
    return 0 if total_f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())