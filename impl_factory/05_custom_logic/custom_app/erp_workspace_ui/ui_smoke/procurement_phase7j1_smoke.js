const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = process.env.ERPW_BASE_URL || 'https://meet.erpbosai.com';
const TIMEOUT = Number(process.env.ERPW_PROCUREMENT_PHASE7J1_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_PROCUREMENT_PHASE7J1_ARTIFACT_DIR || path.join(fs.existsSync('/freeze-artifacts') ? '/freeze-artifacts' : path.join(__dirname, 'artifacts'), `procurement-phase7j1-${new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z')}`);
const ASSET_OVERRIDE_ROOT = process.env.ERPW_PROCUREMENT_PHASE7J1_ASSET_ROOT || '';

fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

const USERS = [
  { key: 'manager', label: 'Purchase Manager', username: process.env.ERPW_MANAGER_USERNAME || process.env.ERPW_PURCHASE_MANAGER_USERNAME, password: process.env.ERPW_MANAGER_PASSWORD || process.env.ERPW_PURCHASE_MANAGER_PASSWORD },
  { key: 'user', label: 'Purchase User', username: process.env.ERPW_USER_USERNAME || process.env.ERPW_PURCHASE_USER_USERNAME, password: process.env.ERPW_USER_PASSWORD || process.env.ERPW_PURCHASE_USER_PASSWORD },
].filter((user) => user.username && user.password);

const VIEWPORTS = [
  { key: 'laptop-1136', width: 1136, height: 768 },
  { key: 'laptop-1240', width: 1240, height: 768 },
  { key: 'desktop-1440', width: 1440, height: 900 },
];

const REQUIRED_GROUPS = ['Supplier readiness', 'Item buying readiness', 'RFQ communication', 'Document quality', 'Order follow-up'];
const FORBIDDEN_TEXT_RE = /Open ERP Form|Open ERP Supplier Form|Open ERP Item Form|Advanced ERP Form|Internal Server Error|Traceback|Email suppliers|Confirm\s+test\s+send|Submit Purchase|Submit RFQ|Submit Supplier Quotation|Submit Purchase Order|Approve Purchase|Reject Purchase|Cancel Purchase|Amend Purchase|Create Supplier Quotation|Create Purchase Order|Receive Items|Create Purchase Receipt|Create Purchase Invoice|Bill Purchase Order|Make Payment|Payment Entry|Pay Supplier|Set default supplier|Update item price/i;
const NATIVE_ROUTE_RE = /\/desk\/Form\/|\/app\//i;
const PAGE_EVENTS = new WeakMap();

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
  await page.screenshot({ path: file, fullPage: true });
  return file;
}

async function installAssetOverrides(context) {
  if (!ASSET_OVERRIDE_ROOT) return;
  await context.route('**/assets/erp_workspace_ui/js/procurement_console/procurement_readiness_ui.js*', async (route) => {
    const file = path.join(ASSET_OVERRIDE_ROOT, 'procurement_readiness_ui.js');
    if (fs.existsSync(file)) {
      return route.fulfill({ path: file, contentType: 'application/javascript' });
    }
    return route.continue();
  });
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

function visible(node) {
  if (!node) return false;
  const rect = node.getBoundingClientRect();
  const style = window.getComputedStyle(node);
  return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
}

async function overviewState(page) {
  const events = PAGE_EVENTS.get(page) || { console: [], pageErrors: [] };
  const state = await page.evaluate((requiredGroups) => {
    const isVisible = (node) => {
      if (!node) return false;
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
    };
    const section = document.querySelector('[data-procurement-manager-readiness]');
    const rectFor = (node) => {
      if (!node) return null;
      const rect = node.getBoundingClientRect();
      return { top: rect.top, left: rect.left, right: rect.right, bottom: rect.bottom, width: rect.width, height: rect.height };
    };
    const chips = section ? Array.from(section.querySelectorAll('[data-procurement-readiness-severity]')).filter(isVisible).map((node) => ({ severity: node.getAttribute('data-procurement-readiness-severity'), text: (node.innerText || '').trim(), rect: rectFor(node) })) : [];
    const groupCards = section ? Array.from(section.querySelectorAll('[data-procurement-readiness-group-card]')).filter(isVisible).map((node) => ({ key: node.getAttribute('data-procurement-readiness-group-card'), text: (node.innerText || '').replace(/\s+/g, ' ').trim(), rect: rectFor(node), critical: node.classList.contains('has-critical') })) : [];
    const topIssues = section ? Array.from(section.querySelectorAll('[data-procurement-readiness-top-issue]')).filter(isVisible).map((node) => ({ severity: node.getAttribute('data-readiness-severity'), group: node.getAttribute('data-readiness-group'), text: (node.innerText || '').replace(/\s+/g, ' ').trim(), rect: rectFor(node) })) : [];
    const expanded = section ? section.querySelector('[data-procurement-readiness-expanded-list]') : null;
    const toggle = section ? section.querySelector('[data-procurement-readiness-toggle]') : null;
    const visibleRows = section ? Array.from(section.querySelectorAll('[data-procurement-readiness-issue]')).filter(isVisible) : [];
    const nextSection = section ? section.nextElementSibling : null;
    const bodyText = (document.body.innerText || '').replace(/\s+/g, ' ').trim();
    const actionText = Array.from(document.querySelectorAll('button, a, [role=button]')).filter(isVisible).map((node) => (node.innerText || node.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim()).filter(Boolean).join(' ');
    return {
      url: location.href,
      route: window.frappe && typeof frappe.get_route === 'function' ? frappe.get_route() : null,
      bodyText,
      actionText,
      shellCount: Array.from(document.querySelectorAll('.sales-console-shell[data-erpw-workspace=procurement]')).filter(isVisible).length,
      managerReadinessCount: Array.from(document.querySelectorAll('[data-procurement-manager-readiness]')).filter(isVisible).length,
      title: section ? ((section.querySelector('[data-procurement-manager-readiness-title]') || {}).innerText || '').trim() : '',
      subtitle: section ? ((section.querySelector('.sales-console-section-note') || {}).innerText || '').trim() : '',
      sectionRect: rectFor(section),
      nextSectionRect: rectFor(nextSection),
      severityChips: chips,
      groupCards,
      requiredGroupsPresent: requiredGroups.filter((label) => groupCards.some((card) => card.text.includes(label))),
      topIssues,
      visibleIssueRows: visibleRows.length,
      expandedHidden: expanded ? expanded.hidden : null,
      expandedVisibleRows: expanded ? Array.from(expanded.querySelectorAll('[data-procurement-readiness-issue]')).filter(isVisible).length : 0,
      toggleText: toggle ? (toggle.innerText || '').trim() : '',
      toggleExpanded: toggle ? toggle.getAttribute('aria-expanded') : null,
      horizontalOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      modalText: Array.from(document.querySelectorAll('.modal.show')).filter(isVisible).map((node) => (node.innerText || '').replace(/\s+/g, ' ').trim()).join(' '),
    };
  }, REQUIRED_GROUPS);
  return Object.assign(state, { console: events.console || [], pageErrors: events.pageErrors || [] });
}

function assertClean(state, label) {
  assert(state.shellCount === 1, `${label}: expected one Procurement overview shell`, state);
  assert(state.horizontalOverflow <= 2, `${label}: page-level horizontal overflow`, state);
  assert(!NATIVE_ROUTE_RE.test(state.url), `${label}: native route leaked`, state);
  assert(!FORBIDDEN_TEXT_RE.test(state.actionText), `${label}: forbidden action text visible`, state);
  assert(!FORBIDDEN_TEXT_RE.test(state.modalText), `${label}: forbidden framework/modal text visible`, state);
  assert((state.pageErrors || []).length === 0, `${label}: page errors detected`, state);
}

async function assertManagerOverview(page, viewport) {
  await page.setViewportSize({ width: viewport.width, height: viewport.height });
  await openOverview(page);
  await page.waitForSelector('[data-procurement-manager-readiness]', { state: 'visible', timeout: TIMEOUT });
  await page.waitForSelector('[data-procurement-readiness-top-issue]', { state: 'visible', timeout: TIMEOUT });
  const defaultScreenshot = await capture(page, `manager-${viewport.key}-overview-compressed`);
  const state = await overviewState(page);
  assertClean(state, `manager ${viewport.key}`);
  assert(state.managerReadinessCount === 1, `manager ${viewport.key}: compressed readiness queue missing`, state);
  assert(state.title === 'Readiness Review Queue', `manager ${viewport.key}: readiness title mismatch`, state);
  assert(/Supplier, item, document, and communication exceptions needing manager attention\./.test(state.subtitle), `manager ${viewport.key}: readiness subtitle mismatch`, state);
  assert(state.severityChips.length >= 3, `manager ${viewport.key}: severity count chips missing`, state);
  for (const severity of ['critical', 'warning', 'info']) {
    assert(state.severityChips.some((chip) => chip.severity === severity), `manager ${viewport.key}: ${severity} chip missing`, state);
  }
  assert(state.groupCards.length === REQUIRED_GROUPS.length, `manager ${viewport.key}: readiness category cards missing`, state);
  assert(state.requiredGroupsPresent.length === REQUIRED_GROUPS.length, `manager ${viewport.key}: readiness category labels missing`, state);
  assert(state.topIssues.length >= 1 && state.topIssues.length <= 3, `manager ${viewport.key}: default visible top issue count is not compressed`, state);
  assert(state.topIssues[0].rect.top < viewport.height + 40, `manager ${viewport.key}: first top issue is too far below the initial viewport`, state);
  assert(state.visibleIssueRows === state.topIssues.length, `manager ${viewport.key}: default issue list is longer than top issues`, state);
  assert(state.expandedHidden === true, `manager ${viewport.key}: full issue list should be collapsed by default`, state);
  assert(state.toggleText === 'View all readiness issues', `manager ${viewport.key}: expand control missing`, state);
  assert(state.sectionRect && state.sectionRect.height <= 720, `manager ${viewport.key}: readiness queue is too tall for overview`, state);

  await page.locator('[data-procurement-readiness-toggle]').click();
  await page.waitForFunction(() => {
    const section = document.querySelector('[data-procurement-manager-readiness]');
    const expanded = section && section.querySelector('[data-procurement-readiness-expanded-list]');
    return expanded && expanded.hidden === false;
  }, null, { timeout: TIMEOUT });
  const expandedScreenshot = await capture(page, `manager-${viewport.key}-overview-expanded`);
  const expandedState = await overviewState(page);
  assertClean(expandedState, `manager ${viewport.key} expanded`);
  assert(expandedState.toggleText === 'Show top readiness issues', `manager ${viewport.key}: collapse control missing after expand`, expandedState);
  assert(expandedState.expandedVisibleRows >= expandedState.topIssues.length, `manager ${viewport.key}: expanded list did not reveal grouped issues`, expandedState);

  await page.locator('[data-procurement-readiness-toggle]').click();
  await page.waitForFunction(() => {
    const section = document.querySelector('[data-procurement-manager-readiness]');
    const expanded = section && section.querySelector('[data-procurement-readiness-expanded-list]');
    return expanded && expanded.hidden === true;
  }, null, { timeout: TIMEOUT });
  const collapsedState = await overviewState(page);
  assert(collapsedState.expandedHidden === true, `manager ${viewport.key}: readiness queue did not collapse`, collapsedState);
  return { viewport: viewport.key, defaultScreenshot, expandedScreenshot, state, expandedState, collapsedState };
}

async function assertUserOverview(page, viewport) {
  await page.setViewportSize({ width: viewport.width, height: viewport.height });
  await openOverview(page);
  await page.waitForFunction(() => {
    const shell = document.querySelector('.sales-console-shell[data-erpw-workspace=procurement]');
    return shell && shell.getAttribute('data-erpw-console-bootstrap') === 'ready';
  }, null, { timeout: TIMEOUT });
  await page.waitForTimeout(350);
  const screenshot = await capture(page, `user-${viewport.key}-overview-no-manager-readiness`);
  const state = await overviewState(page);
  assertClean(state, `user ${viewport.key}`);
  assert(state.managerReadinessCount === 0, `user ${viewport.key}: manager readiness must remain absent`, state);
  assert(!/Readiness Review Queue/i.test(state.bodyText), `user ${viewport.key}: manager readiness title leaked`, state);
  return { viewport: viewport.key, screenshot, state };
}

async function runForUser(browser, user) {
  const context = await browser.newContext();
  await installAssetOverrides(context);
  const page = await context.newPage();
  PAGE_EVENTS.set(page, { console: [], pageErrors: [] });
  page.on('console', (message) => {
    if (message.type() === 'error') PAGE_EVENTS.get(page).console.push(message.text());
  });
  page.on('pageerror', (error) => PAGE_EVENTS.get(page).pageErrors.push({ message: error.message, stack: error.stack }));
  await login(page, user);
  const results = [];
  for (const viewport of VIEWPORTS) {
    if (user.key === 'manager') results.push(await assertManagerOverview(page, viewport));
    else results.push(await assertUserOverview(page, viewport));
  }
  await context.close();
  return { user: user.key, results };
}

(async () => {
  assert(USERS.length === 2, 'Phase 7J1 smoke requires Purchase Manager and Purchase User credentials', { users: USERS.map((user) => user.key) });
  const browser = await chromium.launch({ headless: process.env.ERPW_HEADLESS !== '0' });
  const results = [];
  try {
    for (const user of USERS) {
      results.push(await runForUser(browser, user));
    }
    const summary = { status: 'pass', artifactDir: ARTIFACT_DIR, assetOverrideRoot: ASSET_OVERRIDE_ROOT || null, results };
    fs.writeFileSync(path.join(ARTIFACT_DIR, 'phase7j1-summary.json'), JSON.stringify(summary, null, 2));
    console.log(JSON.stringify(summary, null, 2));
  } catch (error) {
    const failure = { status: 'fail', error: error.message, details: error.details || {}, artifactDir: ARTIFACT_DIR };
    fs.writeFileSync(path.join(ARTIFACT_DIR, 'phase7j1-summary.json'), JSON.stringify(failure, null, 2));
    console.error(JSON.stringify(failure, null, 2));
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
})();
