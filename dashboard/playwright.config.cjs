// Playwright E2E config — CommonJS to match Playwright's internal transform.
const { defineConfig, devices } = require('@playwright/test');

const BASE = process.env.DASHBOARD_URL || 'http://localhost:5175';
const BACKEND = process.env.BACKEND_URL || 'http://localhost:18080';

module.exports = defineConfig({
  testDir: './tests/e2e',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: process.env.CI ? [['list'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: BASE,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    headless: true,
    viewport: { width: 1440, height: 900 },
    launchOptions: {
      // In container: /root/.cache/ms-playwright/...  On host: /home/jahanzaib/...
      executablePath: process.env.CHROMIUM_PATH || '/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome',
      args: ['--no-sandbox', '--disable-dev-shm-usage'],
    },
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
