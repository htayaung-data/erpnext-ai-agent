const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = process.env.ERPW_BASE_URL || 'https://meet.erpbosai.com';
const TIMEOUT = Number(process.env.ERPW_PROCUREMENT_PHASE7K_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_PROCUREMENT_PHASE7K_ARTIFACT_DIR || path.join(fs.existsSync('/freeze-artifacts') ? '/freeze-artifacts' : path.join(__dirname, 'artifacts'), `procurement-phase7k-${new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z')}`);
const ASSET_OVERRIDE_ROOT = process.env.ERPW_PROCUREMENT_PHASE7K_ASSET_ROOT || '';
fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

const USERS = [
  { key: 'manager', label: 'Purchase Manager', username: process.env.ERPW_PURCHASE_MANAGER_USERNAME || process.env.ERPW_MANAGER_USERNAME, password: process.env.ERPW_PURCHASE_MANAGER_PASSWORD || process.env.ERPW_MANAGER_PASSWORD },
  { key: 'user', label: 'Purchase User', username: process.env.ERPW_PURCHASE_USER_USERNAME || process.env.ERPW_USER_USERNAME, password: process.env.ERPW_PURCHASE_USER_PASSWORD || process.env.ERPW_USER_PASSWORD },
].filter((user) => user.username && user.password);

const VIEWPORTS = [
  { key: 'laptop-1136', width: 1136, height: 768 },
  { key: 'laptop-1240', width: 1240, height: 768 },
  { key: 'desktop-1440', width: 1440, height: 900 },
];

const FORBIDDEN_TEXT_RE = /Open ERP Form|Open ERP Supplier Form|Open ERP Item Form|Advanced ERP Form|Internal Server Error|Traceback|Confirm\s+test\s+send|Email Queue|Communication|Contact|Portal User|Item Price|Default Supplier|Submit Purchase|Approve Purchase|Create Purchase Receipt|Create Purchase Invoice|Payment Entry|Receive Items|Bill Purchase Order/i;
const NATIVE_ROUTE_RE = /\/desk\/Form\/|\/app\//i;

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

async function capture(page, name, options = {}) {
  const file = path.join(ARTIFACT_DIR, `${safeFileName(name)}.png`);
  await page.screenshot({ path: file, fullPage: Boolean(options.fullPage), animations: 'disabled' });
  return file;
}

async function installAssetOverrides(context) {
  if (!ASSET_OVERRIDE_ROOT) return;
  const overrides = [
    { pattern: '**/assets/erp_workspace_ui/js/procurement_console/procurement_console_page.js*', file: 'procurement_console_page.js', contentType: 'application/javascript' },
    { pattern: '**/assets/erp_workspace_ui/css/erp_workspace_ui.css*', file: 'erp_workspace_ui.css', contentType: 'text/css' },
  ];
  for (const item of overrides) {
    await context.route(item.pattern, async (route) => {
      const file = path.join(ASSET_OVERRIDE_ROOT, item.file);
      if (fs.existsSync(file)) return route.fulfill({ path: file, contentType: item.contentType });
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

async function openOverview(page) {
  const pathName = '/desk/procurement-console';
  const canRoute = await page.evaluate(() => Boolean(window.frappe && typeof frappe.set_route === 'function')).catch(() => false);
  if (canRoute) {
    await page.evaluate(() => frappe.set_route('procurement-console'));
    await page.waitForURL((current) => current.pathname === pathName, { waitUntil: 'domcontentloaded', timeout: TIMEOUT });
  } else {
    await page.goto(routeUrl(pathName), { waitUntil: 'domcontentloaded', timeout: TIMEOUT });
  }
  await page.waitForFunction(() => Boolean(window.frappe), null, { timeout: TIMEOUT });
  await page.waitForSelector('.sales-console-shell[data-erpw-workspace=procurement]', { state: 'visible', timeout: TIMEOUT });
  await page.waitForFunction(() => {
    const shell = document.querySelector('.sales-console-shell[data-erpw-workspace=procurement]');
    return shell && shell.getAttribute('data-erpw-console-bootstrap') === 'ready';
  }, null, { timeout: TIMEOUT });
}

async function callMethod(page, method, args = {}) {
  return page.evaluate(async ({ method, args }) => {
    const response = await frappe.call({ method, args });
    return response && response.message !== undefined ? response.message : response;
  }, { method, args });
}

function rows(payload) {
  return payload && payload.results && Array.isArray(payload.results.rows) ? payload.results.rows : [];
}

function cellValue(row, key) {
  const cell = row && row.cells ? row.cells[key] : null;
  if (cell && typeof cell === 'object') return cell.value || cell.meta || '';
  return cell || '';
}

function firstNonEmpty(...values) {
  return values.map((value) => String(value || '').trim()).find(Boolean) || '';
}

async function worklistPayload(page, queueKey) {
  return callMethod(page, 'erp_workspace_ui.procurement_console.worklist.get_procurement_console_worklist_context', { queue_key: queueKey, filters: {} });
}

async function discoverFixtures(page) {
  const supplierRow = rows(await worklistPayload(page, 'supplier_directory'))[0];
  const itemRow = rows(await worklistPayload(page, 'buying_item_directory'))[0];
  const requestRow = rows(await worklistPayload(page, 'purchase_request_directory'))[0];
  const rfqRow = rows(await worklistPayload(page, 'rfq_directory'))[0];
  const sqRow = rows(await worklistPayload(page, 'supplier_quotation_directory'))[0];
  const poRow = rows(await worklistPayload(page, 'purchase_order_directory'))[0];
  assert(supplierRow && itemRow && requestRow && rfqRow && sqRow && poRow, 'Missing fixture rows for Quick Find smoke', { supplierRow, itemRow, requestRow, rfqRow, sqRow, poRow });
  return {
    supplier: { query: firstNonEmpty(cellValue(supplierRow, 'supplier'), supplierRow.name), group: 'suppliers', path: '/desk/procurement-console-supplier/' },
    item: { query: firstNonEmpty(cellValue(itemRow, 'item'), itemRow.name), group: 'buying_items', path: '/desk/procurement-console-item/' },
    request: { query: requestRow.name, group: 'purchase_requests', path: '/desk/procurement-console-purchase-request-review/' },
    rfq: { query: rfqRow.name, group: 'rfqs', path: '/desk/procurement-console-rfq-review/' },
    sq: { query: sqRow.name, group: 'supplier_quotations', path: '/desk/procurement-console-supplier-quotation-review/' },
    po: { query: poRow.name, group: 'purchase_orders', path: '/desk/procurement-console-po-follow-up/' },
    report: { query: 'report', group: 'reports', path: '/desk/procurement-console-report/' },
  };
}

async function quickFindState(page) {
  return page.evaluate(() => {
    const visible = (node) => {
      if (!node) return false;
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
    };
    const rectFor = (node) => {
      if (!node || !visible(node)) return null;
      const rect = node.getBoundingClientRect();
      return { top: rect.top, bottom: rect.bottom, left: rect.left, right: rect.right, width: rect.width, height: rect.height };
    };
    const section = document.querySelector('[data-procurement-quick-find]');
    const input = document.querySelector('[data-procurement-quick-find-input]');
    const suggestions = document.querySelector('[data-procurement-quick-find-suggestions]');
    const preview = document.querySelector('[data-procurement-quick-find-preview]');
    const createActions = document.querySelector('[data-section-key="create-actions"]');
    const readiness = document.querySelector('[data-procurement-manager-readiness]');
    const note = section ? section.querySelector('.sales-console-section-note') : null;
    const bodyText = (document.body.innerText || '').replace(/\s+/g, ' ').trim();
    const actionText = Array.from(document.querySelectorAll('button, a, [role=button]')).filter(visible).map((node) => (node.innerText || node.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim()).filter(Boolean).join(' ');
    return {
      url: location.href,
      route: window.frappe && typeof frappe.get_route === 'function' ? frappe.get_route() : null,
      sectionVisible: Boolean(section && visible(section)),
      inputVisible: Boolean(input && visible(input)),
      inputValue: input ? input.value : '',
      placeholder: input ? input.getAttribute('placeholder') : '',
      noteText: note ? (note.innerText || '').replace(/\s+/g, ' ').trim() : '',
      quickFindRect: rectFor(section),
      createActionsRect: rectFor(createActions),
      readinessRect: rectFor(readiness),
      suggestionsVisible: Boolean(suggestions && visible(suggestions) && !suggestions.hidden),
      groupKeys: suggestions ? Array.from(suggestions.querySelectorAll('[data-procurement-quick-find-group]')).filter(visible).map((node) => node.getAttribute('data-procurement-quick-find-group')) : [],
      optionCount: suggestions ? Array.from(suggestions.querySelectorAll('[data-procurement-quick-find-option]')).filter(visible).length : 0,
      previewVisible: Boolean(preview && visible(preview) && !preview.hidden),
      previewText: preview ? (preview.innerText || '').replace(/\s+/g, ' ').trim() : '',
      openButtonVisible: Boolean(preview && Array.from(preview.querySelectorAll('[data-procurement-quick-find-open]')).some(visible)),
      shellCount: Array.from(document.querySelectorAll('.sales-console-shell[data-erpw-workspace=procurement]')).filter(visible).length,
      horizontalOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      bodyText,
      actionText,
      modalText: Array.from(document.querySelectorAll('.modal.show')).filter(visible).map((node) => (node.innerText || '').replace(/\s+/g, ' ').trim()).join(' '),
    };
  });
}

function assertClean(state, label) {
  assert(state.shellCount <= 1, `${label}: duplicate Procurement shell`, state);
  assert(state.horizontalOverflow <= 2, `${label}: horizontal overflow`, state);
  assert(!NATIVE_ROUTE_RE.test(state.url), `${label}: native route leaked`, state);
  assert(!FORBIDDEN_TEXT_RE.test(state.actionText), `${label}: forbidden action text visible`, state);
  assert(!FORBIDDEN_TEXT_RE.test(state.modalText), `${label}: forbidden modal text visible`, state);
}

function assertWorkbenchRhythm(state, label) {
  assert(state.noteText === 'Preview before opening', `${label}: Quick Find note copy mismatch`, state);
  assert(state.createActionsRect && state.quickFindRect, `${label}: Start Buying Work or Quick Find rect missing`, state);
  assert(state.createActionsRect.top < state.quickFindRect.top, `${label}: Start Buying Work must appear above Quick Find`, state);
  if (state.readinessRect) {
    assert(state.quickFindRect.top < state.readinessRect.top, `${label}: Quick Find must appear above Readiness Review`, state);
  }
}

async function searchAndPreview(page, fixture, label) {
  await openOverview(page);
  const input = page.locator('[data-procurement-quick-find-input]').first();
  await input.waitFor({ state: 'visible', timeout: TIMEOUT });
  await input.fill('');
  await input.fill(fixture.query.slice(0, 36));
  await page.waitForFunction((group) => {
    const panel = document.querySelector('[data-procurement-quick-find-suggestions]');
    return panel && !panel.hidden && panel.querySelector(`[data-procurement-quick-find-group="${group}"] [data-procurement-quick-find-option]`);
  }, fixture.group, { timeout: TIMEOUT });
  let state = await quickFindState(page);
  assert(state.url.includes('/desk/procurement-console'), `${label}: typing auto-navigated`, state);
  assert(state.groupKeys.includes(fixture.group), `${label}: expected group not rendered`, state);
  assert(state.optionCount > 0, `${label}: no suggestions rendered`, state);
  assertWorkbenchRhythm(state, `${label} suggestions`);
  assertClean(state, `${label} suggestions`);
  await page.locator(`[data-procurement-quick-find-group="${fixture.group}"] [data-procurement-quick-find-option]`).first().click();
  await page.waitForSelector('[data-procurement-quick-find-preview]:not([hidden]) [data-procurement-quick-find-open]', { state: 'visible', timeout: TIMEOUT });
  state = await quickFindState(page);
  assert(state.url.includes('/desk/procurement-console'), `${label}: selection auto-navigated`, state);
  assert(state.previewVisible && state.openButtonVisible, `${label}: preview/open not visible`, state);
  assert(!/\/desk\/Form\/|\/app\//i.test(state.previewText), `${label}: preview includes native route text`, state);
  assertWorkbenchRhythm(state, `${label} preview`);
  assertClean(state, `${label} preview`);
  return state;
}

async function openSelected(page, fixture, label) {
  await page.locator('[data-procurement-quick-find-open]').first().click();
  await page.waitForURL((current) => current.pathname.startsWith(fixture.path), { waitUntil: 'domcontentloaded', timeout: TIMEOUT });
  const url = page.url();
  assert(!NATIVE_ROUTE_RE.test(url), `${label}: Open routed to native URL`, { url });
}

async function assertEscapeCloses(page, fixture) {
  await openOverview(page);
  const input = page.locator('[data-procurement-quick-find-input]').first();
  await input.fill(fixture.query.slice(0, 36));
  await page.waitForSelector('[data-procurement-quick-find-suggestions]', { state: 'visible', timeout: TIMEOUT });
  await input.press('Escape');
  const state = await quickFindState(page);
  assert(!state.suggestionsVisible, 'Escape did not close Quick Find suggestions', state);
}

async function runForUser(browser, user) {
  const context = await browser.newContext();
  await installAssetOverrides(context);
  const page = await context.newPage();
  const consoleMessages = [];
  const pageErrors = [];
  page.on('console', (message) => {
    if (['error', 'warning'].includes(message.type())) consoleMessages.push(`${message.type()}: ${message.text()}`);
  });
  page.on('pageerror', (error) => pageErrors.push(error.message || String(error)));
  await login(page, user);
  await openOverview(page);
  const fixtures = await discoverFixtures(page);
  const results = { user: user.key, screenshots: {}, checks: [] };

  for (const viewport of VIEWPORTS) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await openOverview(page);
    let state = await quickFindState(page);
    assert(state.sectionVisible && state.inputVisible, `${user.key} ${viewport.key}: Quick Find not visible`, state);
    assert(state.placeholder === 'Find supplier, item, request, RFQ, quotation, order, or report', `${user.key} ${viewport.key}: placeholder mismatch`, state);
    assertWorkbenchRhythm(state, `${user.key} ${viewport.key} empty`);
    assertClean(state, `${user.key} ${viewport.key} empty`);
    results.screenshots[`${viewport.key}-empty`] = await capture(page, `${user.key}-${viewport.key}-quick-find-empty`);
    const previewState = await searchAndPreview(page, fixtures.supplier, `${user.key} ${viewport.key} supplier`);
    results.screenshots[`${viewport.key}-supplier-preview`] = await capture(page, `${user.key}-${viewport.key}-supplier-preview`);
    results.checks.push({ viewport: viewport.key, supplierPreview: previewState.previewText });
  }

  if (user.key === 'manager') {
    const managerChecks = [
      ['item', fixtures.item],
      ['request', fixtures.request],
      ['rfq', fixtures.rfq],
      ['supplier-quotation', fixtures.sq],
      ['purchase-order', fixtures.po],
      ['report', fixtures.report],
    ];
    await page.setViewportSize({ width: 1136, height: 768 });
    for (const [label, fixture] of managerChecks) {
      await searchAndPreview(page, fixture, `manager ${label}`);
      results.screenshots[`${label}-preview`] = await capture(page, `manager-${label}-preview`);
      await openSelected(page, fixture, `manager ${label}`);
      await openOverview(page);
    }
    await assertEscapeCloses(page, fixtures.supplier);
  } else {
    await page.setViewportSize({ width: 1136, height: 768 });
    await searchAndPreview(page, fixtures.report, 'user report');
    await openSelected(page, fixtures.report, 'user report');
  }

  assert(pageErrors.length === 0, `${user.key}: page errors`, { pageErrors });
  assert(!consoleMessages.some((line) => /Internal Server Error|Traceback/i.test(line)), `${user.key}: console errors`, { consoleMessages });
  await context.close();
  return results;
}

async function main() {
  assert(USERS.length >= 2, 'Purchase Manager and Purchase User credentials are required');
  const browser = await chromium.launch({ headless: process.env.ERPW_HEADLESS !== '0' });
  const results = [];
  try {
    for (const user of USERS) {
      results.push(await runForUser(browser, user));
    }
  } finally {
    await browser.close();
  }
  const summary = { status: 'pass', artifactDir: ARTIFACT_DIR, assetOverrideRoot: ASSET_OVERRIDE_ROOT || null, results };
  fs.writeFileSync(path.join(ARTIFACT_DIR, 'phase7k-summary.json'), JSON.stringify(summary, null, 2));
  console.log(JSON.stringify(summary, null, 2));
}

main().catch((error) => {
  const failure = { status: 'fail', message: error.message, details: error.details || {}, stack: error.stack };
  fs.writeFileSync(path.join(ARTIFACT_DIR, 'phase7k-summary.json'), JSON.stringify(failure, null, 2));
  console.error(failure);
  process.exit(1);
});
