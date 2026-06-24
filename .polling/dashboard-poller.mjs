// Polls http://localhost:5175/ until it returns HTTP 200, then uses Playwright + Chromium
// (already installed at ~/.cache/ms-playwright/chromium-1228) to take a screenshot for proof.
//
// Usage: node dashboard-poller.mjs
//   - Set OPENSHORTS_URL / OPENSHORTS_BACKEND / OPENSHORTS_RENDERER env vars to override.
//   - Exits 0 on success (screenshot saved), 1 on failure.
//
// This script does NOT install anything new, does NOT touch any other process on the host,
// and reuses an existing Playwright cache. Safe to run alongside the dashboard.

import { chromium } from "/home/jahanzaib/.npm/_npx/705bc6b22212b352/node_modules/playwright-core/index.mjs";
import http from "node:http";

const DASHBOARD = process.env.OPENSHORTS_URL || "http://localhost:5175/";
const BACKEND = process.env.OPENSHORTS_BACKEND || "http://localhost:18080/";
const RENDERER = process.env.OPENSHORTS_RENDERER || "http://localhost:13100/";
const TIMEOUT_MS = Number(process.env.POLL_TIMEOUT_MS || 60 * 60 * 1000); // 1h default
const INTERVAL_MS = Number(process.env.POLL_INTERVAL_MS || 5000);

const startedAt = Date.now();

function probe(url) {
  return new Promise((resolve) => {
    const req = http.get(url, { timeout: 4000 }, (res) => {
      // Drain body so socket can be reused
      res.resume();
      resolve({ ok: res.statusCode >= 200 && res.statusCode < 400, status: res.statusCode });
    });
    req.on("timeout", () => { req.destroy(); resolve({ ok: false, error: "timeout" }); });
    req.on("error", (e) => resolve({ ok: false, error: e.code || e.message }));
  });
}

async function waitFor(url, label) {
  process.stdout.write(`[poll] waiting for ${label} at ${url} ... `);
  while (Date.now() - startedAt < TIMEOUT_MS) {
    const r = await probe(url);
    if (r.ok) {
      console.log(`HTTP ${r.status} OK`);
      return r;
    }
    process.stdout.write(`${r.status ?? r.error ?? "?"} `);
    await new Promise((r) => setTimeout(r, INTERVAL_MS));
  }
  throw new Error(`Timed out waiting for ${label} at ${url}`);
}

async function main() {
  // 1) Wait for dashboard (Vite dev server) and backend to come up
  await waitFor(DASHBOARD, "dashboard");
  await waitFor(BACKEND, "backend");
  // Renderer is optional for the dashboard to load — probe but don't block on it
  const renderer = await probe(RENDERER);
  console.log(`[probe] renderer ${RENDERER} -> ${renderer.ok ? "HTTP " + renderer.status : (renderer.error || "down")} (non-blocking)`);

  // 2) Use Playwright + the cached Chromium binary to load the dashboard and take a screenshot
  const chromiumPath = "/home/jahanzaib/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome";
  console.log(`[playwright] launching chromium at ${chromiumPath}`);
  const browser = await chromium.launch({
    executablePath: chromiumPath,
    args: ["--no-sandbox", "--disable-dev-shm-usage"],
  });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  page.on("console", (msg) => console.log(`[browser:${msg.type()}] ${msg.text()}`));
  page.on("pageerror", (err) => console.log(`[browser:pageerror] ${err.message}`));
  page.on("requestfailed", (req) =>
    console.log(`[browser:requestfailed] ${req.method()} ${req.url()} -- ${req.failure()?.errorText}`)
  );

  const resp = await page.goto(DASHBOARD, { waitUntil: "domcontentloaded", timeout: 30000 });
  console.log(`[playwright] GET ${DASHBOARD} -> HTTP ${resp?.status()}`);
  // Give the React app a moment to render
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(2000);

  const title = await page.title();
  const url = page.url();
  const heading = await page.evaluate(() => {
    const h = document.querySelector("h1, h2");
    return h ? h.textContent?.trim() : null;
  });
  const bodyText = (await page.evaluate(() => document.body.innerText || "")).slice(0, 500);

  const out = "/tmp/openshorts-dashboard.png";
  await page.screenshot({ path: out, fullPage: false });
  console.log(`[playwright] screenshot saved -> ${out}`);

  await browser.close();

  console.log(JSON.stringify({
    ok: true,
    dashboard: DASHBOARD,
    title,
    finalUrl: url,
    firstHeading: heading,
    bodySnippet: bodyText,
    screenshot: out,
    elapsedSec: Math.round((Date.now() - startedAt) / 1000),
  }, null, 2));
}

main().catch((e) => {
  console.error("[fatal]", e?.stack || e?.message || e);
  process.exit(1);
});
