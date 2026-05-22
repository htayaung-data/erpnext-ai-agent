const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = process.env.ERPW_BASE_URL || 'https://meet.erpbosai.com';
const TIMEOUT = Number(process.env.ERPW_PROCUREMENT_PHASE7J1B_PERFORMANCE_TIMEOUT || 90000);
const EXPECT_ASYNC = process.env.ERPW_PROCUREMENT_PHASE7J1B_EXPECT_ASYNC === '1';
const ARTIFACT_DIR = process.env.ERPW_PROCUREMENT_PHASE7J1B_PERFORMANCE_OUT || path.join(fs.existsSync('/freeze-artifacts') ? '/freeze-artifacts' : path.join(__dirname, 'artifacts'), `procurement-phase7j1b-performance-${new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z')}`);
const ASSET_OVERRIDE_ROOT = process.env.ERPW_PROCUREMENT_PHASE7J1B_ASSET_ROOT || '';
const BOOTSTRAP_METHOD = 'erp_workspace_ui.procurement_console.service.get_procurement_console_bootstrap';
const READINESS_METHOD = 'erp_workspace_ui.procurement_console.readiness.get_procurement_manager_readiness';
const READINESS_METHOD_FRAGMENT = `/api/method/${READINESS_METHOD}`;
const FIRST_USEFUL_TARGET_MS = Number(process.env.ERPW_PROCUREMENT_PHASE7J1B_FIRST_USEFUL_TARGET_MS || 1500);
const BOOTSTRAP_TARGET_MS = Number(process.env.ERPW_PROCUREMENT_PHASE7J1B_BOOTSTRAP_TARGET_MS || 1200);

fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

const USERS = [
  { key: 'manager', label: 'Purchase Manager', username: process.env.ERPW_MANAGER_USERNAME || process.env.ERPW_PURCHASE_MANAGER_USERNAME, password: process.env.ERPW_MANAGER_PASSWORD || process.env.ERPW_PURCHASE_MANAGER_PASSWORD },
  { key: 'user', label: 'Purchase User', username: process.env.ERPW_USER_USERNAME || process.env.ERPW_PURCHASE_USER_USERNAME, password: process.env.ERPW_USER_PASSWORD || process.env.ERPW_PURCHASE_USER_PASSWORD },
].filter((user) => user.username && user.password);

const VIEWPORTS = [
  { key: 'laptop-1136', width: 1136, height: 768 },
  { key: 'desktop-1440', width: 1440, height: 900 },
];

function assert(condition, message, details = {}) {
  if (!condition) {
    const error = new Error(message);
    error.details = details;
    throw error;
  }
}

function routeUrl(route) {
  return new URL(route, BASE_URL).toString();
}

function safeFileName(value) {
  return String(value || 'artifact').replace(/[^a-z0-9_-]+/gi, '-').replace(/^-+|-+$/g, '').toLowerCase();
}

async function capture(page, name) {
  const file = path.join(ARTIFACT_DIR, `${safeFileName(name)}.png`);
  await page.screenshot({ path: file, fullPage: false, animations: 'disabled' });
  return file;
}

async function installAssetOverrides(context) {
  if (!ASSET_OVERRIDE_ROOT) return;
  const overrides = [
    { pattern: '**/assets/erp_workspace_ui/js/procurement_console/procurement_console_page.js*', file: 'procurement_console_page.js' },
    { pattern: '**/assets/erp_workspace_ui/js/procurement_console/procurement_readiness_ui.js*', file: 'procurement_readiness_ui.js' },
  ];
  for (const item of overrides) {
    await context.route(item.pattern, async (route) => {
      const file = path.join(ASSET_OVERRIDE_ROOT, item.file);
      if (fs.existsSync(file)) {
        return route.fulfill({ path: file, contentType: 'application/javascript' });
      }
      return route.continue();
    });
  }
}

async function login(page, user) {
  await page.goto(routeUrl('/login'), { waitUntil: 'domcontentloaded', timeout: TIMEOUT });
  const userField = page.locator('#login_email, input[name=usr], input[name=login_email], input[type=email], input[type=text]').first();
  const passwordField = page.locator('#login_password, input[name=pwd], input[name=login_password], input[type=password]').first();
  const loginButton = page.locator('button.btn-login, .btn-login, button[type=submit]').first();
  await userField.waitFor({ state: 'visible', timeout: TIMEOUT });
  await userField.fill(user.username);
  await passwordField.fill(user.password);
  await Promise.all([
    page.waitForURL(/\/(?:app|desk)(?:[/?#]|$)/, { waitUntil: 'domcontentloaded', timeout: TIMEOUT }),
    loginButton.click(),
  ]);
}

async function callMethod(page, method) {
  return page.evaluate(async ({ methodName }) => {
    const startedAt = performance.now();
    try {
      const response = await frappe.call({ method: methodName });
      const durationMs = Math.round(performance.now() - startedAt);
      const payload = response && response.message ? response.message : {};
      return {
        ok: true,
        durationMs,
        keys: Object.keys(payload),
        hasManagerReadiness: Object.prototype.hasOwnProperty.call(payload, 'manager_readiness'),
        readinessVisible: Boolean(payload && payload.visible),
        summary: payload && payload.summary ? payload.summary : null,
      };
    } catch (error) {
      return {
        ok: false,
        durationMs: Math.round(performance.now() - startedAt),
        message: error && (error.message || error._server_messages || String(error)),
      };
    }
  }, { methodName: method });
}

function stats(samples) {
  const values = samples.map((sample) => sample.durationMs).filter((value) => Number.isFinite(value)).sort((a, b) => a - b);
  if (!values.length) return { min: null, median: null, max: null };
  return {
    min: values[0],
    median: values[Math.floor(values.length / 2)],
    max: values[values.length - 1],
  };
}

async function measureDirectMethods(page, user) {
  const bootstrapSamples = [];
  const readinessSamples = [];
  await callMethod(page, BOOTSTRAP_METHOD);
  for (let index = 0; index < 3; index += 1) {
    bootstrapSamples.push(await callMethod(page, BOOTSTRAP_METHOD));
  }
  if (user.key === 'manager') {
    await callMethod(page, READINESS_METHOD);
    for (let index = 0; index < 3; index += 1) {
      readinessSamples.push(await callMethod(page, READINESS_METHOD));
    }
  }
  return {
    bootstrapSamples,
    bootstrapStats: stats(bootstrapSamples),
    readinessSamples,
    readinessStats: stats(readinessSamples),
  };
}

async function openOverviewAndMeasure(page, viewport, user) {
  await page.setViewportSize({ width: viewport.width, height: viewport.height });
  const failedResponses = [];
  const readinessResponses = [];
  const pageErrors = [];
  const consoleErrors = [];
  const responseHandler = (response) => {
    const url = response.url();
    const status = response.status();
    if (status >= 400) failedResponses.push({ status, url });
    if (url.includes(READINESS_METHOD_FRAGMENT)) readinessResponses.push({ status, url });
  };
  const consoleHandler = (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  };
  const pageErrorHandler = (error) => pageErrors.push({ message: error.message, stack: error.stack });
  page.on('response', responseHandler);
  page.on('console', consoleHandler);
  page.on('pageerror', pageErrorHandler);

  const startedAt = Date.now();
  await page.goto(routeUrl('/desk/procurement-console'), { waitUntil: 'domcontentloaded', timeout: TIMEOUT });
  await page.waitForSelector('.sales-console-shell[data-erpw-workspace=procurement]', { state: 'visible', timeout: TIMEOUT });
  const shellVisibleMs = Date.now() - startedAt;
  await page.waitForFunction(() => {
    const visible = (node) => {
      if (!node) return false;
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
    };
    return Array.from(document.querySelectorAll('.sales-console-kpi-card')).filter(visible).length >= 3
      && visible(document.querySelector('[data-section-key="create-actions"]'))
      && Array.from(document.querySelectorAll('.sales-console-queue-card')).filter(visible).length >= 1;
  }, null, { timeout: TIMEOUT });
  const firstUsefulMs = Date.now() - startedAt;
  await page.waitForFunction(() => {
    const shell = document.querySelector('.sales-console-shell[data-erpw-workspace=procurement]');
    return shell && shell.getAttribute('data-erpw-console-bootstrap') === 'ready';
  }, null, { timeout: TIMEOUT });
  const bootstrapReadyMs = Date.now() - startedAt;

  let readinessState = null;
  let readinessReadyMs = null;
  if (user.key === 'manager') {
    await page.waitForSelector('[data-procurement-manager-readiness]', { state: 'visible', timeout: TIMEOUT });
    await page.waitForSelector('[data-procurement-manager-readiness-state="ready"]', { state: 'visible', timeout: TIMEOUT });
    readinessReadyMs = Date.now() - startedAt;
    readinessState = await page.locator('[data-procurement-manager-readiness]').first().evaluate((node) => ({
      state: node.getAttribute('data-procurement-manager-readiness-state'),
      fetchMs: Number(node.getAttribute('data-procurement-manager-readiness-fetch-ms') || 0),
      mainMessage: ((node.querySelector('[data-procurement-readiness-main-message]') || {}).innerText || '').replace(/\s+/g, ' ').trim(),
      topIssues: Array.from(node.querySelectorAll('[data-procurement-readiness-top-issue]')).filter((item) => {
        const rect = item.getBoundingClientRect();
        const style = window.getComputedStyle(item);
        return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
      }).length,
    }));
  } else {
    await page.waitForTimeout(350);
    const userReadinessCount = await page.locator('[data-procurement-manager-readiness]').count();
    readinessState = { count: userReadinessCount };
  }

  const layoutState = await page.evaluate(() => {
    const visible = (node) => {
      if (!node) return false;
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
    };
    return {
      shellCount: Array.from(document.querySelectorAll('.sales-console-shell[data-erpw-workspace=procurement]')).filter(visible).length,
      headerCount: Array.from(document.querySelectorAll('.sales-console-shell[data-erpw-workspace=procurement] [data-erpw-console-title], .sales-console-shell[data-erpw-workspace=procurement] .sales-console-hero-title')).filter(visible).filter((node) => (node.innerText || '').trim() === 'Procurement Console').length,
      horizontalOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      route: window.frappe && typeof frappe.get_route === 'function' ? frappe.get_route() : null,
    };
  });
  const screenshot = await capture(page, `${user.key}-${viewport.key}-overview-performance`);

  page.off('response', responseHandler);
  page.off('console', consoleHandler);
  page.off('pageerror', pageErrorHandler);

  return {
    user: user.key,
    viewport: viewport.key,
    shellVisibleMs,
    firstUsefulMs,
    bootstrapReadyMs,
    readinessReadyMs,
    readinessState,
    readinessResponses,
    failedResponses,
    pageErrors,
    consoleErrors,
    layoutState,
    screenshot,
  };
}

async function runForUser(browser, user) {
  const context = await browser.newContext();
  await installAssetOverrides(context);
  const page = await context.newPage();
  await login(page, user);
  const direct = await measureDirectMethods(page, user);
  const browserMeasurements = [];
  for (const viewport of VIEWPORTS) {
    browserMeasurements.push(await openOverviewAndMeasure(page, viewport, user));
  }
  await context.close();
  return { user: user.key, direct, browserMeasurements };
}

function validateResult(result) {
  for (const sample of result.direct.bootstrapSamples) {
    assert(sample.ok, `${result.user}: bootstrap API call failed`, sample);
    if (EXPECT_ASYNC) {
      assert(sample.hasManagerReadiness === false, `${result.user}: bootstrap still includes manager_readiness payload`, sample);
    }
  }
  if (EXPECT_ASYNC && result.user === 'manager') {
    assert(result.direct.bootstrapStats.median <= BOOTSTRAP_TARGET_MS, `${result.user}: bootstrap median exceeds target`, result.direct.bootstrapStats);
  }
  for (const sample of result.direct.readinessSamples || []) {
    assert(sample.ok, `${result.user}: readiness API call failed`, sample);
    assert(sample.readinessVisible === true, `${result.user}: readiness endpoint did not return visible manager payload`, sample);
  }
  for (const measurement of result.browserMeasurements) {
    assert(measurement.failedResponses.length === 0, `${result.user} ${measurement.viewport}: failed HTTP responses detected`, measurement);
    assert(measurement.pageErrors.length === 0, `${result.user} ${measurement.viewport}: page errors detected`, measurement);
    assert(measurement.layoutState.shellCount === 1, `${result.user} ${measurement.viewport}: duplicate Overview shell`, measurement);
    assert(measurement.layoutState.headerCount <= 1, `${result.user} ${measurement.viewport}: duplicate Overview header`, measurement);
    assert(measurement.layoutState.horizontalOverflow <= 2, `${result.user} ${measurement.viewport}: page horizontal overflow`, measurement);
    if (result.user === 'manager') {
      assert(measurement.readinessResponses.length >= 1, `${result.user} ${measurement.viewport}: readiness API was not called asynchronously`, measurement);
      assert(measurement.readinessState && measurement.readinessState.state === 'ready', `${result.user} ${measurement.viewport}: readiness did not render ready`, measurement);
      assert((measurement.readinessState.topIssues || 0) <= 3, `${result.user} ${measurement.viewport}: top issue list is not compressed`, measurement);
      if (EXPECT_ASYNC) {
        assert(measurement.firstUsefulMs <= FIRST_USEFUL_TARGET_MS, `${result.user} ${measurement.viewport}: first useful Overview render exceeded target`, measurement);
        assert(measurement.readinessReadyMs >= measurement.firstUsefulMs, `${result.user} ${measurement.viewport}: readiness timing did not follow first useful render`, measurement);
      }
    } else {
      assert(measurement.readinessResponses.length === 0, `${result.user} ${measurement.viewport}: Purchase User triggered manager readiness API`, measurement);
      assert(measurement.readinessState && measurement.readinessState.count === 0, `${result.user} ${measurement.viewport}: Purchase User saw manager readiness widget`, measurement);
    }
  }
}

(async () => {
  assert(USERS.length === 2, 'Phase 7J1B performance smoke requires Purchase Manager and Purchase User credentials', { users: USERS.map((user) => user.key) });
  const browser = await chromium.launch({ headless: process.env.ERPW_HEADLESS !== '0' });
  const results = [];
  try {
    for (const user of USERS) {
      const result = await runForUser(browser, user);
      validateResult(result);
      results.push(result);
    }
    const summary = {
      status: 'pass',
      expectAsync: EXPECT_ASYNC,
      artifactDir: ARTIFACT_DIR,
      assetOverrideRoot: ASSET_OVERRIDE_ROOT || null,
      bootstrapTargetMs: BOOTSTRAP_TARGET_MS,
      firstUsefulTargetMs: FIRST_USEFUL_TARGET_MS,
      results,
    };
    fs.writeFileSync(path.join(ARTIFACT_DIR, 'phase7j1b-performance-summary.json'), JSON.stringify(summary, null, 2));
    console.log(JSON.stringify(summary, null, 2));
  } catch (error) {
    const failure = {
      status: 'fail',
      expectAsync: EXPECT_ASYNC,
      artifactDir: ARTIFACT_DIR,
      assetOverrideRoot: ASSET_OVERRIDE_ROOT || null,
      error: error.message,
      details: error.details || {},
      results,
    };
    fs.writeFileSync(path.join(ARTIFACT_DIR, 'phase7j1b-performance-summary.json'), JSON.stringify(failure, null, 2));
    console.error(JSON.stringify(failure, null, 2));
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
})();
