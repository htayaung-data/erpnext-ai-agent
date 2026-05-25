const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = process.env.ERPW_BASE_URL || 'https://meet.erpbosai.com';
const TIMEOUT = Number(process.env.ERPW_PROCUREMENT_PHASE7L_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_PROCUREMENT_PHASE7L_ARTIFACT_DIR || path.join(
  fs.existsSync('/freeze-artifacts') ? '/freeze-artifacts' : path.join(__dirname, 'artifacts'),
  `procurement-phase7l-${new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z')}`
);
const ASSET_ROOT = process.env.ERPW_PROCUREMENT_PHASE7L_ASSET_ROOT || '';
const SAMPLE_COUNT = Number(process.env.ERPW_PROCUREMENT_PHASE7L_SAMPLES || 2);
const DIRECT_API_SAMPLE_COUNT = Number(process.env.ERPW_PROCUREMENT_PHASE7L_DIRECT_API_SAMPLES || 10);
const READINESS_DIRECT_MEDIAN_MS = Number(process.env.ERPW_PROCUREMENT_PHASE7L_READINESS_MEDIAN_MS || 500);
const READINESS_DIRECT_P95_MS = Number(process.env.ERPW_PROCUREMENT_PHASE7L_READINESS_P95_MS || 650);
const READINESS_DIRECT_MAX_MS = Number(process.env.ERPW_PROCUREMENT_PHASE7L_READINESS_MAX_MS || 700);
const QUICK_FIND_DIRECT_MAX_MS = Number(process.env.ERPW_PROCUREMENT_PHASE7L_QUICK_FIND_MAX_MS || 300);

const BOOTSTRAP_METHOD = 'erp_workspace_ui.procurement_console.service.get_procurement_console_bootstrap';
const READINESS_METHOD = 'erp_workspace_ui.procurement_console.readiness.get_procurement_manager_readiness';
const QUICK_FIND_METHOD = 'erp_workspace_ui.procurement_console.service.get_procurement_quick_find_suggestions';
const ASSET_OVERRIDE_HITS = {};

const USERS = [
  { key: 'manager', label: 'Purchase Manager', username: process.env.ERPW_PURCHASE_MANAGER_USERNAME || process.env.ERPW_MANAGER_USERNAME, password: process.env.ERPW_PURCHASE_MANAGER_PASSWORD || process.env.ERPW_MANAGER_PASSWORD },
  { key: 'user', label: 'Purchase User', username: process.env.ERPW_PURCHASE_USER_USERNAME || process.env.ERPW_USER_USERNAME, password: process.env.ERPW_PURCHASE_USER_PASSWORD || process.env.ERPW_USER_PASSWORD },
].filter((user) => user.username && user.password);

const ROUTES = [
  { key: 'overview', label: 'Overview', route: '/desk/procurement-console', targetMs: 1200, shell: '.sales-console-shell[data-erpw-workspace="procurement"]', ready: () => document.querySelector('.sales-console-shell[data-erpw-workspace="procurement"][data-erpw-console-bootstrap="ready"] .sales-console-kpi-card') },
  { key: 'purchase-order-directory', label: 'Purchase Order Directory', route: '/desk/procurement-console-worklist/purchase-order-directory', targetMs: 1500, shell: '.erpw-list-shell.is-procurement-worklist', readyText: /Purchase order records|PURCHASE ORDER RECORDS/i },
  { key: 'supplier-detail', label: 'Supplier Detail', route: '/desk/procurement-console-supplier/Shwe%20Taung%20Electronics%20Supply', targetMs: 1500, shell: '.erpw-procurement-supplier-detail-shell', readyText: /Supplier Buying Profile|Orders|RFQs|Quotations/i },
  { key: 'buying-item-directory', label: 'Buying Item Directory', route: '/desk/procurement-console-worklist/buying-item-directory', targetMs: 1500, shell: '.erpw-list-shell.is-procurement-worklist', readyText: /Buying item records|BUYING ITEM RECORDS|Purchase-enabled item/i },
  { key: 'buying-item-detail', label: 'Buying Item Detail', route: '/desk/procurement-console-item/SPH-SAM-A15-6%2F128', targetMs: 1500, shell: '.erpw-procurement-item-detail-shell', readyText: /Item Buying Context|Suppliers & Prices|Quotation History/i },
  { key: 'purchase-order-follow-up', label: 'Purchase Order Follow-up', route: '/desk/procurement-console-po-follow-up/PUR-ORD-2026-00001', targetMs: 1500, shell: '.erpw-procurement-po-follow-up-shell', readyText: /Item lines|Downstream visibility/i },
];

fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

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

function safeName(value) {
  return String(value || 'artifact').replace(/[^a-z0-9_-]+/gi, '-').replace(/^-+|-+$/g, '').toLowerCase();
}

async function installAssetOverrides(context) {
  if (!ASSET_ROOT) return;
  const mappings = [
    { match: /\/assets\/erp_workspace_ui\/js\/procurement_console\/procurement_console_page\.js(?:\?|$)/, file: 'erp_workspace_ui/public/js/procurement_console/procurement_console_page.js' },
    { match: /\/assets\/erp_workspace_ui\/js\/procurement_console\/procurement_console_supplier_page\.js(?:\?|$)/, file: 'erp_workspace_ui/public/js/procurement_console/procurement_console_supplier_page.js' },
    { match: /\/assets\/erp_workspace_ui\/js\/procurement_console\/procurement_console_item_page\.js(?:\?|$)/, file: 'erp_workspace_ui/public/js/procurement_console/procurement_console_item_page.js' },
    { match: /\/assets\/erp_workspace_ui\/js\/procurement_console\/procurement_console_po_follow_up_page\.js(?:\?|$)/, file: 'erp_workspace_ui/public/js/procurement_console/procurement_console_po_follow_up_page.js' },
    { match: /procurement_console_worklist\.js(?:\?|$)/, file: 'erp_workspace_ui/erp_workspace_ui/page/procurement_console_worklist/procurement_console_worklist.js' },
  ];
  for (const mapping of mappings) {
    await context.route((url) => mapping.match.test(url.pathname + url.search), async (route) => {
      const filePath = path.join(ASSET_ROOT, mapping.file);
      if (fs.existsSync(filePath)) {
        ASSET_OVERRIDE_HITS[mapping.file] = (ASSET_OVERRIDE_HITS[mapping.file] || 0) + 1;
        return route.fulfill({ path: filePath, contentType: 'application/javascript' });
      }
      return route.continue();
    });
  }

  await context.route('**/api/method/frappe.desk.desk_page.getpage**', async (route) => {
    const filePath = path.join(ASSET_ROOT, 'erp_workspace_ui/erp_workspace_ui/page/procurement_console_worklist/procurement_console_worklist.js');
    if (!fs.existsSync(filePath)) return route.continue();
    const response = await route.fetch();
    const headers = response.headers();
    delete headers['content-length'];
    delete headers['content-encoding'];
    let body = await response.text();
    try {
      const payload = JSON.parse(body);
      const responseText = JSON.stringify(payload && payload.message ? payload.message : {});
      if (payload && payload.message && /procurement-console-worklist|erpw-procurement-console-worklist-page/i.test(responseText)) {
        payload.message.script = fs.readFileSync(filePath, 'utf8');
        body = JSON.stringify(payload);
        ASSET_OVERRIDE_HITS['frappe.desk.desk_page.getpage:procurement-console-worklist'] = (ASSET_OVERRIDE_HITS['frappe.desk.desk_page.getpage:procurement-console-worklist'] || 0) + 1;
      }
    } catch (error) {
      return route.fulfill({ response, body });
    }
    return route.fulfill({ status: response.status(), headers, body });
  });
}

async function login(page, user) {
  await page.goto(routeUrl('/login'), { waitUntil: 'domcontentloaded', timeout: TIMEOUT });
  await page.locator('#login_email, input[name=usr], input[name=login_email], input[type=email], input[type=text]').first().fill(user.username, { timeout: TIMEOUT });
  await page.locator('#login_password, input[name=pwd], input[name=login_password], input[type=password]').first().fill(user.password, { timeout: TIMEOUT });
  await Promise.all([
    page.waitForURL(/\/(?:app|desk)(?:[/?#]|$)/, { waitUntil: 'domcontentloaded', timeout: TIMEOUT }),
    page.locator('button.btn-login, .btn-login, button[type=submit]').first().click(),
  ]);
}

function routeParts(route) {
  const parts = route.replace(/^\/desk\/?/, '').split('/').filter(Boolean);
  return parts.map((part) => decodeURIComponent(part));
}

async function openRoute(page, route) {
  const parts = routeParts(route);
  const startedAt = await page.evaluate(() => performance.now());
  await page.evaluate((nextParts) => frappe.set_route.apply(frappe, nextParts), parts);
  await page.waitForURL((current) => current.pathname === new URL(routeUrl(route)).pathname, { timeout: TIMEOUT });
  return startedAt;
}

async function injectSourcePageOverrides(page) {
  if (!ASSET_ROOT) return;
  const worklistSource = path.join(ASSET_ROOT, 'erp_workspace_ui/erp_workspace_ui/page/procurement_console_worklist/procurement_console_worklist.js');
  if (fs.existsSync(worklistSource)) {
    await page.addScriptTag({ path: worklistSource });
    ASSET_OVERRIDE_HITS['script-tag:procurement-console-worklist'] = (ASSET_OVERRIDE_HITS['script-tag:procurement-console-worklist'] || 0) + 1;
  }
}

async function primeWarmRoutes(page) {
  for (const route of ROUTES) {
    try {
      await openRoute(page, route.route);
      await waitUseful(page, route);
    } catch (error) {
      const screenshot = await capture(page, `prime-failure-${route.key}`).catch(() => null);
      const snapshot = await pageSnapshot(page, route).catch(() => null);
      error.message = `Prime warm route failed for ${route.key}: ${error.message}`;
      error.details = Object.assign({}, error.details || {}, { routeKey: route.key, route: route.route, screenshot, snapshot });
      throw error;
    }
  }
  await injectSourcePageOverrides(page);
  await openRoute(page, '/desk/procurement-console');
  await waitUseful(page, ROUTES[0]);
}


async function waitUseful(page, routeConfig) {
  if (routeConfig.ready) {
    await page.waitForFunction(routeConfig.ready, null, { timeout: TIMEOUT });
  } else if (routeConfig.readyText) {
    await page.waitForFunction((source) => {
      const re = new RegExp(source, 'i');
      const text = document.body && document.body.innerText || '';
      return re.test(text) && !/Loading (?:Procurement|read-only|item|queue|follow-up)/i.test(text);
    }, routeConfig.readyText.source, { timeout: TIMEOUT });
  }
  return page.evaluate(() => performance.now());
}

function methodFromRequest(request) {
  const url = request.url();
  const match = url.match(/\/api\/method\/([^?#]+)/);
  if (match) return decodeURIComponent(match[1]);
  const postData = request.postData() || '';
  const cmd = postData.match(/(?:^|&)cmd=([^&]+)/);
  return cmd ? decodeURIComponent(cmd[1].replace(/\+/g, ' ')) : '';
}

function summarizeMethods(calls) {
  const methods = {};
  for (const call of calls) {
    methods[call.method] = (methods[call.method] || 0) + 1;
  }
  return methods;
}

function duplicateCustomMethods(calls) {
  return Object.entries(summarizeMethods(calls)).filter(([method, count]) => method.startsWith('erp_workspace_ui.procurement_console.') && count > 1).map(([method, count]) => ({ method, count }));
}

async function pageSnapshot(page, routeConfig) {
  return page.evaluate((shellSelector) => {
    const visible = (node) => {
      if (!node) return false;
      const rect = node.getBoundingClientRect();
      const style = getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
    };
    const text = (document.body.innerText || '').replace(/\s+/g, ' ').trim();
    return {
      url: location.href,
      textSample: text.slice(0, 1200),
      route: window.frappe && frappe.get_route ? frappe.get_route() : null,
      targetShellCount: document.querySelectorAll(shellSelector).length,
      procurementShellCount: document.querySelectorAll('.sales-console-shell[data-erpw-workspace="procurement"], .erpw-list-shell.is-procurement-worklist, .erpw-procurement-supplier-detail-shell, .erpw-procurement-item-detail-shell, .erpw-procurement-po-follow-up-shell').length,
      pageHeadCount: Array.from(document.querySelectorAll('.page-head')).filter(visible).length,
      sidebarBrandCount: Array.from(document.querySelectorAll('.layout-side-section, .desk-sidebar')).filter((node) => /Procurement Console/i.test(node.innerText || '')).length,
      loadingTextVisible: /Loading (?:Procurement|read-only|item|queue|follow-up)/i.test(text),
      horizontalOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      forbiddenText: /Open ERP Form|Open ERP Supplier Form|Open ERP Item Form|Advanced ERP Form|\/desk\/Form\/|\/app\/|Internal Server Error|Traceback|Confirm\s+test\s+send|Email Queue|Portal User|Create\s+(?:Communication|Contact|User|Item Price)|Update\s+Item Price|Set\s+Default Supplier|Default Supplier mutation|Submit Purchase|Approve Purchase|Create Purchase Receipt|Create Purchase Invoice|Payment Entry|Receive Items|Bill Purchase Order/i.test(text),
    };
  }, routeConfig.shell);
}

async function capture(page, name) {
  const file = path.join(ARTIFACT_DIR, `${safeName(name)}.png`);
  await page.screenshot({ path: file, fullPage: true, animations: 'disabled' });
  return file;
}

async function measureRoute(page, routeConfig, user, sample) {
  const calls = [];
  const failedResponses = [];
  const onRequest = (request) => {
    const method = methodFromRequest(request);
    if (method) calls.push({ method, url: request.url() });
  };
  const onResponse = (response) => {
    if (response.status() >= 400) failedResponses.push({ status: response.status(), url: response.url() });
  };
  page.on('request', onRequest);
  page.on('response', onResponse);
  const startedAt = await openRoute(page, routeConfig.route);
  const usefulAt = await waitUseful(page, routeConfig);
  await page.waitForTimeout(250);
  page.off('request', onRequest);
  page.off('response', onResponse);
  const snapshot = await pageSnapshot(page, routeConfig);
  const duplicateMethods = duplicateCustomMethods(calls);
  const screenshot = sample === SAMPLE_COUNT ? await capture(page, `${user.key}-${routeConfig.key}-warm`) : null;
  const result = {
    user: user.key,
    routeKey: routeConfig.key,
    route: routeConfig.route,
    sample,
    usefulMs: Math.round(usefulAt - startedAt),
    targetMs: routeConfig.targetMs,
    customApiRequests: calls,
    customApiCalls: calls.filter((call) => call.method.startsWith('erp_workspace_ui.procurement_console.')).length,
    methodCounts: summarizeMethods(calls),
    duplicateMethods,
    failedResponses,
    screenshot,
    snapshot,
  };
  assert(result.usefulMs <= routeConfig.targetMs, `${user.label} ${routeConfig.label}: warm useful content exceeded target`, result);
  assert(duplicateMethods.length === 0, `${user.label} ${routeConfig.label}: duplicate custom API calls`, result);
  assert(!failedResponses.some((entry) => entry.status >= 500), `${user.label} ${routeConfig.label}: failed HTTP response`, result);
  assert(snapshot.targetShellCount === 1, `${user.label} ${routeConfig.label}: duplicate or missing target shell`, result);
  assert(snapshot.pageHeadCount <= 1, `${user.label} ${routeConfig.label}: duplicate visible page head`, result);
  assert(snapshot.horizontalOverflow <= 4, `${user.label} ${routeConfig.label}: horizontal overflow`, result);
  assert(!snapshot.forbiddenText, `${user.label} ${routeConfig.label}: forbidden text visible`, result);
  return result;
}

async function callTimedApi(page, method, args) {
  return page.evaluate(async ({ method, args }) => {
    const started = performance.now();
    await frappe.call({ method, args });
    return performance.now() - started;
  }, { method, args });
}

function percentile(sortedDurations, p) {
  if (!sortedDurations.length) return 0;
  const index = Math.min(sortedDurations.length - 1, Math.ceil((p / 100) * sortedDurations.length) - 1);
  return sortedDurations[index];
}

async function directApiMeasure(page, method, args, samples, thresholds) {
  const warmupMs = Math.round(await callTimedApi(page, method, args));
  const durations = [];
  for (let i = 0; i < samples; i += 1) {
    durations.push(Math.round(await callTimedApi(page, method, args)));
  }
  const sorted = durations.slice().sort((a, b) => a - b);
  const max = Math.max(...durations);
  const median = sorted[Math.floor(sorted.length / 2)];
  const p95 = percentile(sorted, 95);
  const result = { method, warmupMs, durations, median, p95, max, thresholds };
  if (thresholds.medianMs != null) {
    assert(median <= thresholds.medianMs, `${method}: warm median duration exceeded`, result);
  }
  if (thresholds.p95Ms != null) {
    assert(p95 <= thresholds.p95Ms, `${method}: warm p95 duration exceeded`, result);
  }
  if (thresholds.maxMs != null) {
    assert(max <= thresholds.maxMs, `${method}: warm max duration exceeded`, result);
  }
  return result;
}

(async () => {
  assert(USERS.length === 2, 'Both Procurement Manager and User credentials are required');
  const browser = await chromium.launch({ headless: process.env.ERPW_HEADLESS !== '0' });
  const summary = { artifactRoot: ARTIFACT_DIR, assetRoot: ASSET_ROOT || null, assetOverrideHits: ASSET_OVERRIDE_HITS, routes: ROUTES, samples: SAMPLE_COUNT, results: [], directApi: [], userReadinessCalls: 0, failures: [] };
  try {
    for (const user of USERS) {
      const context = await browser.newContext({ viewport: { width: 1136, height: 768 }, serviceWorkers: 'block' });
      await installAssetOverrides(context);
      const page = await context.newPage();
      await login(page, user);
      await openRoute(page, '/desk/procurement-console');
      await waitUseful(page, ROUTES[0]);
      await primeWarmRoutes(page);
      if (user.key === 'manager') {
        summary.directApi.push(await directApiMeasure(page, READINESS_METHOD, {}, DIRECT_API_SAMPLE_COUNT, { medianMs: READINESS_DIRECT_MEDIAN_MS, p95Ms: READINESS_DIRECT_P95_MS, maxMs: READINESS_DIRECT_MAX_MS }));
        summary.directApi.push(await directApiMeasure(page, QUICK_FIND_METHOD, { query: 'sam', limit: 12 }, DIRECT_API_SAMPLE_COUNT, { maxMs: QUICK_FIND_DIRECT_MAX_MS }));
      }
      const readinessCalls = [];
      page.on('request', (request) => {
        if (methodFromRequest(request) === READINESS_METHOD) readinessCalls.push(request.url());
      });
      for (let sample = 1; sample <= SAMPLE_COUNT; sample += 1) {
        for (const route of ROUTES) {
          summary.results.push(await measureRoute(page, route, user, sample));
        }
      }
      if (user.key === 'user') {
        summary.userReadinessCalls = readinessCalls.length;
        assert(readinessCalls.length === 0, 'Purchase User triggered manager readiness API calls', { readinessCalls });
      }
      await context.close();
    }
    fs.writeFileSync(path.join(ARTIFACT_DIR, 'phase7l-performance-summary.json'), JSON.stringify(summary, null, 2) + '\n');
  } catch (error) {
    summary.failures.push({ message: error.message, details: error.details || null, stack: error.stack });
    fs.writeFileSync(path.join(ARTIFACT_DIR, 'phase7l-performance-summary.json'), JSON.stringify(summary, null, 2) + '\n');
    console.error(error.message);
    if (error.details) console.error(JSON.stringify(error.details, null, 2));
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
  console.log(JSON.stringify({ artifactRoot: ARTIFACT_DIR, failures: summary.failures.length, results: summary.results.length }, null, 2));
})();
