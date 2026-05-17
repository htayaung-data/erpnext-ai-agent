const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = process.env.ERPW_BASE_URL || 'https://meet.erpbosai.com';
const TIMEOUT = Number(process.env.ERPW_PROCUREMENT_DETAIL_PERF_TIMEOUT || 60000);
const API_COUNT_THRESHOLD = Number(process.env.ERPW_PROCUREMENT_DETAIL_API_THRESHOLD || 8);
const DETAIL_CALL_THRESHOLD = Number(process.env.ERPW_PROCUREMENT_DETAIL_CONTEXT_CALL_THRESHOLD || 3);
const READY_THRESHOLD_MS = Number(process.env.ERPW_PROCUREMENT_DETAIL_READY_THRESHOLD_MS || 2500);
const ARTIFACT_DIR = process.env.ERPW_PROCUREMENT_DETAIL_PERFORMANCE_OUT
  ? path.dirname(process.env.ERPW_PROCUREMENT_DETAIL_PERFORMANCE_OUT)
  : path.join(fs.existsSync('/freeze-artifacts') ? '/freeze-artifacts' : path.join(__dirname, 'artifacts'), `procurement-detail-performance-${new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z')}`);
const SUMMARY_PATH = process.env.ERPW_PROCUREMENT_DETAIL_PERFORMANCE_OUT || path.join(ARTIFACT_DIR, 'procurement-detail-performance-summary.json');
const ASSET_OVERRIDE_ROOT = process.env.ERPW_PROCUREMENT_DETAIL_ASSET_ROOT || '';

fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

const USERS = [
  { key: 'manager', label: 'Purchase Manager', username: process.env.ERPW_MANAGER_USERNAME, password: process.env.ERPW_MANAGER_PASSWORD },
  { key: 'user', label: 'Purchase User', username: process.env.ERPW_USER_USERNAME, password: process.env.ERPW_USER_PASSWORD },
].filter((user) => user.username && user.password);

const VIEWPORTS = [
  { key: 'laptop-1136', width: 1136, height: 768 },
  { key: 'desktop-1440', width: 1440, height: 900 },
];

const TARGETS = [
  {
    key: 'supplier-detail',
    label: 'Supplier Detail',
    seed: process.env.ERPW_PROCUREMENT_SUPPLIER_NAME || 'Shwe Taung Electronics Supply',
    routeFor: (name) => `/desk/procurement-console-supplier/${encodeURIComponent(name)}`,
    shell: '.erpw-procurement-supplier-detail-shell',
    contentNeedle: 'Supplier buying profile',
    method: 'erp_workspace_ui.procurement_console.supplier_detail.get_supplier_detail_context',
    asset: '/assets/erp_workspace_ui/js/procurement_console/procurement_console_supplier_page.js',
  },
  {
    key: 'buying-item-detail',
    label: 'Buying Item Detail',
    seed: process.env.ERPW_PROCUREMENT_ITEM_CODE || 'SPH-SAM-A15-6/128',
    routeFor: (name) => `/desk/procurement-console-item/${encodeURIComponent(name)}`,
    shell: '.erpw-procurement-item-detail-shell',
    contentNeedle: 'Buying item profile',
    method: 'erp_workspace_ui.procurement_console.items.get_item_detail_context',
    asset: '/assets/erp_workspace_ui/js/procurement_console/procurement_console_item_page.js',
  },
  {
    key: 'purchase-order-follow-up-detail',
    label: 'Purchase Order Follow-up Detail',
    seed: process.env.ERPW_PROCUREMENT_PURCHASE_ORDER || 'PUR-ORD-2026-00227',
    routeFor: (name) => `/desk/procurement-console-po-follow-up/${encodeURIComponent(name)}`,
    shell: '.erpw-procurement-po-follow-up-shell',
    contentNeedle: 'Purchase Order',
    method: 'erp_workspace_ui.procurement_console.purchase_order_detail.get_purchase_order_follow_up_detail_context',
    asset: '/assets/erp_workspace_ui/js/procurement_console/procurement_console_po_follow_up_page.js',
  },
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

async function installAssetOverrides(context) {
  if (!ASSET_OVERRIDE_ROOT) return;
  await context.route('**/assets/erp_workspace_ui/js/procurement_console/*.js*', async (route) => {
    const pathname = new URL(route.request().url()).pathname;
    const target = TARGETS.find((item) => item.asset === pathname);
    const file = target ? path.join(ASSET_OVERRIDE_ROOT, path.basename(pathname)) : '';
    if (file && fs.existsSync(file)) {
      return route.fulfill({ path: file, contentType: 'application/javascript' });
    }
    return route.continue();
  });
}

async function login(page, user) {
  await page.goto(routeUrl('/login'), { waitUntil: 'domcontentloaded', timeout: TIMEOUT });
  const userField = page.locator("#login_email, input[name='usr'], input[name='login_email'], input[type='email'], input[type='text']").first();
  const passwordField = page.locator("#login_password, input[name='pwd'], input[name='login_password'], input[type='password']").first();
  const loginButton = page.locator("button:has-text('Login'), button.btn-login, .btn-login").first();
  await userField.waitFor({ state: 'visible', timeout: TIMEOUT });
  await userField.fill(user.username);
  await passwordField.fill(user.password);
  await Promise.all([
    page.waitForURL(/\/(?:app|desk)(?:[/?#]|$)/, { waitUntil: 'domcontentloaded', timeout: TIMEOUT }),
    loginButton.click(),
  ]);
}

async function measureTarget(page, user, viewport, target) {
  const requestStarts = new Map();
  const responses = [];
  const consoleErrors = [];
  const pageErrors = [];
  const onRequest = (request) => requestStarts.set(request, { at: Date.now(), method: request.method() });
  const onResponse = (response) => {
    const request = response.request();
    const start = requestStarts.get(request) || { at: Date.now(), method: request.method() };
    let methodPath = null;
    try { methodPath = new URL(response.url()).pathname.replace(/^\/api\/method\//, ''); } catch (error) {}
    responses.push({ url: response.url(), method: start.method, methodPath, status: response.status(), durationMs: Date.now() - start.at });
  };
  const onConsole = (message) => { if (message.type() === 'error') consoleErrors.push(message.text()); };
  const onPageError = (error) => pageErrors.push({ message: error.message, stack: error.stack });
  page.on('request', onRequest);
  page.on('response', onResponse);
  page.on('console', onConsole);
  page.on('pageerror', onPageError);

  const route = target.routeFor(target.seed);
  const startedAt = Date.now();
  let shellVisibleMs = null;
  let contentVisibleMs = null;
  let screenshotPath = null;
  let shellSnapshot = null;

  try {
    const shellPromise = page.locator(target.shell).first().waitFor({ state: 'visible', timeout: TIMEOUT }).then(() => { shellVisibleMs = Date.now() - startedAt; });
    await page.goto(routeUrl(route), { waitUntil: 'domcontentloaded', timeout: TIMEOUT });
    await page.evaluate(() => {
      const boot = window.erpWorkspaceUiBoot || {};
      if (typeof boot.scheduleProcurementDirectPage === 'function') boot.scheduleProcurementDirectPage();
      else if (typeof boot.ensureProcurementDirectPage === 'function') boot.ensureProcurementDirectPage();
    }).catch(() => {});
    await shellPromise;
    await page.waitForFunction(({ selector, needle }) => {
      const shell = document.querySelector(selector);
      if (!shell) return false;
      const text = (shell.innerText || '').replace(/\s+/g, ' ').trim();
      return text.length > 250 && text.toLowerCase().includes(String(needle).toLowerCase());
    }, { selector: target.shell, needle: target.contentNeedle }, { timeout: TIMEOUT });
    contentVisibleMs = Date.now() - startedAt;
    await page.waitForLoadState('networkidle', { timeout: 8000 }).catch(() => {});
    await page.locator(target.shell).first().waitFor({ state: 'visible', timeout: 15000 });
    await page.waitForTimeout(300);
    for (let attempt = 0; attempt < 30; attempt += 1) {
      shellSnapshot = await page.evaluate((selector) => {
        const visible = (node) => {
          const rect = node.getBoundingClientRect();
          const style = window.getComputedStyle(node);
          return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
        };
        return {
          url: window.location.href,
          shellCount: Array.from(document.querySelectorAll(selector)).filter(visible).length,
          pageHeadCount: Array.from(document.querySelectorAll('.page-head')).filter(visible).length,
          hasInternalServerError: /Internal Server Error|Traceback|Report context failed|Detail context failed/i.test(document.body.innerText || ''),
          horizontalOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        };
      }, target.shell);
      if (shellSnapshot.shellCount === 1) break;
      await page.waitForTimeout(250);
    }
    screenshotPath = path.join(ARTIFACT_DIR, `${user.key}-${viewport.key}-${target.key}.png`);
    await page.screenshot({ path: screenshotPath, fullPage: true });
  } finally {
    page.off('request', onRequest);
    page.off('response', onResponse);
    page.off('console', onConsole);
    page.off('pageerror', onPageError);
  }

  const apiResponses = responses.filter((response) => /\/api\/method\//.test(response.url));
  const detailResponses = apiResponses.filter((response) => response.methodPath === target.method);
  const failedResponses = responses.filter((response) => response.status >= 400);
  const grouped = new Map();
  for (const response of apiResponses) {
    const key = `${response.method} ${response.methodPath}`;
    const current = grouped.get(key) || { key, count: 0, maxMs: 0, totalMs: 0 };
    current.count += 1;
    current.maxMs = Math.max(current.maxMs, response.durationMs || 0);
    current.totalMs += response.durationMs || 0;
    grouped.set(key, current);
  }

  const result = {
    user: user.key,
    viewport: viewport.key,
    target: target.key,
    route,
    shellVisibleMs,
    contentVisibleMs,
    totalNetworkCount: responses.length,
    apiCount: apiResponses.length,
    detailContextCallCount: detailResponses.length,
    failedHttpResponses: failedResponses,
    duplicateApiCalls: Array.from(grouped.values()).filter((item) => item.count > 1).sort((a, b) => b.count - a.count),
    slowestApiCalls: apiResponses.slice().sort((a, b) => b.durationMs - a.durationMs).slice(0, 8),
    consoleErrors,
    pageErrors,
    shellSnapshot,
    detailTrace: await page.evaluate(() => Array.isArray(window.__erpwProcurementDetailPerfTrace) ? window.__erpwProcurementDetailPerfTrace.slice() : []),
    screenshotPath,
  };

  assert(shellSnapshot && shellSnapshot.shellCount === 1, `${target.label}: expected one visible detail shell`, result);
  assert(!shellSnapshot.hasInternalServerError, `${target.label}: backend error text surfaced`, result);
  assert(shellSnapshot.horizontalOverflow <= 2, `${target.label}: page-level horizontal overflow`, result);
  assert(failedResponses.length === 0, `${target.label}: failed HTTP response during detail load`, result);
  assert(pageErrors.length === 0, `${target.label}: browser page error during detail load`, result);
  assert(result.apiCount <= API_COUNT_THRESHOLD, `${target.label}: API count regression`, result);
  assert(result.detailContextCallCount <= DETAIL_CALL_THRESHOLD, `${target.label}: duplicate detail context calls`, result);
  assert(result.contentVisibleMs <= READY_THRESHOLD_MS, `${target.label}: detail ready time exceeded threshold`, result);
  return result;
}

async function run() {
  assert(USERS.length === 2, 'Procurement detail performance smoke requires Purchase Manager and Purchase User credentials', { users: USERS.map((user) => user.key) });
  const browser = await chromium.launch({ headless: process.env.ERPW_HEADLESS !== '0' });
  const summary = {
    artifactRoot: ARTIFACT_DIR,
    baseUrl: BASE_URL,
    assetOverrideRoot: ASSET_OVERRIDE_ROOT || null,
    thresholds: { apiCount: API_COUNT_THRESHOLD, detailContextCalls: DETAIL_CALL_THRESHOLD, readyMs: READY_THRESHOLD_MS },
    results: [],
    failures: [],
  };
  try {
    for (const user of USERS) {
      for (const viewport of VIEWPORTS) {
        for (const target of TARGETS) {
          const context = await browser.newContext({ viewport, ignoreHTTPSErrors: true });
          await context.addInitScript(() => {
            window.__erpwProcurementDetailPerfTrace = [];
          });
          await installAssetOverrides(context);
          const page = await context.newPage();
          try {
            await login(page, user);
            const result = await measureTarget(page, user, viewport, target);
            summary.results.push(result);
            console.log(`${user.key} ${viewport.key} ${target.key}: ready=${result.contentVisibleMs}ms api=${result.apiCount} detailCalls=${result.detailContextCallCount}`);
          } catch (error) {
            const failurePath = path.join(ARTIFACT_DIR, `${user.key}-${viewport.key}-${target.key}-failure.png`);
            await page.screenshot({ path: failurePath, fullPage: true }).catch(() => {});
            const failure = { user: user.key, viewport: viewport.key, target: target.key, message: error.message, details: error.details || null, stack: error.stack, screenshotPath: failurePath };
            summary.failures.push(failure);
            throw error;
          } finally {
            await context.close();
          }
        }
      }
    }
  } finally {
    await browser.close();
    fs.writeFileSync(SUMMARY_PATH, JSON.stringify(summary, null, 2));
    console.log(`PROCUREMENT_DETAIL_PERFORMANCE_SUMMARY=${SUMMARY_PATH}`);
  }
}

run().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exit(1);
});