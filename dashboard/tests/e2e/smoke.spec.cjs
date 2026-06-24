// Smoke test (CommonJS-flavored to avoid Babel ESM quirks)
const { test, expect } = require('@playwright/test');

test('dashboard loads with correct title and sidebar', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (msg) => { if (msg.type() === 'error') errors.push('CONSOLE: ' + msg.text()); });

  await page.goto('/#app');
  await expect(page).toHaveTitle(/Content Factory/);
  await page.waitForTimeout(2000);

  const sidebarButtons = ['Clip Generator', 'AI Shorts', 'AI Agent', 'UGC Gallery',
    'YouTube Studio', 'Content Factory', 'Voice Lab',
    'Avatar Studio', 'Multilingual', 'Settings'];
  for (let i = 0; i < sidebarButtons.length; i++) {
    const label = sidebarButtons[i];
    await expect(page.locator('nav button:has-text("' + label + '")').first()).toBeVisible();
  }

  expect(errors.length, 'JS errors found: ' + errors.join(' | ')).toBe(0);
});

test('all 5 new tabs render their H1 without errors', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));

  await page.goto('/#app');
  await page.waitForTimeout(2000);

  const tabs = ['Voice Lab', 'Avatar Studio', 'Content Factory', 'Multilingual', 'Settings'];
  for (let i = 0; i < tabs.length; i++) {
    const tab = tabs[i];
    await page.locator('nav button:has-text("' + tab + '")').first().click();
    await page.waitForTimeout(800);
    await expect(page.locator('h1').first()).toHaveText(tab);
  }

  expect(errors.length, 'JS errors: ' + errors.join(' | ')).toBe(0);
});

test('settings page shows all expected cards', async ({ page }) => {
  await page.goto('/#app');
  await page.locator('nav button:has-text("Settings")').first().click();
  await page.waitForTimeout(2000);

  const cardTitles = await page.locator('.glass-panel h2').allTextContents();
  const expected = ['Active Engines', 'Free & Open Source', 'Self-Hosted Stack',
    'Multilingual', 'Direct Social Publishing'];
  for (let i = 0; i < expected.length; i++) {
    expect(cardTitles.join('|')).toContain(expected[i]);
  }
});

test('factory shows all 10 templates', async ({ page }) => {
  await page.goto('/#app');
  await page.locator('nav button:has-text("Content Factory")').first().click();
  await page.waitForTimeout(2000);
  const runBtns = await page.locator('button:has-text("Run this template")').count();
  expect(runBtns).toBe(10);
});

test('no JS errors on any tab navigation', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/#app');
  await page.waitForTimeout(2000);
  const tabs = ['Clip Generator', 'AI Shorts', 'AI Agent', 'UGC Gallery',
    'YouTube Studio', 'Content Factory', 'Voice Lab',
    'Avatar Studio', 'Multilingual', 'Settings'];
  for (let i = 0; i < tabs.length; i++) {
    await page.locator('nav button:has-text("' + tabs[i] + '")').first().click();
    await page.waitForTimeout(700);
  }
  expect(errors.length, 'JS errors: ' + errors.join(' | ')).toBe(0);
});
