const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = process.env.ERPW_BASE_URL || 'https://meet.erpbosai.com';
const TIMEOUT = Number(process.env.ERPW_PROCUREMENT_PHASE7J1_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_PROCUREMENT_PHASE7J1B_ARTIFACT_DIR || process.env.ERPW_PROCUREMENT_PHASE7J1_ARTIFACT_DIR || path.join(fs.existsSync('/freeze-artifacts') ? '/freeze-artifacts' : path.join(__dirname, 'artifacts'), `procurement-phase7j1b-${new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z')}`);
const ASSET_OVERRIDE_ROOT = process.env.ERPW_PROCUREMENT_PHASE7J1B_ASSET_ROOT || process.env.ERPW_PROCUREMENT_PHASE7J1_ASSET_ROOT || '';
const READINESS_METHOD_FRAGMENT = '/api/method/erp_workspace_ui.procurement_console.readiness.get_procurement_manager_readiness';

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

async function capture(page, name, options = {}) {
  const file = path.join(ARTIFACT_DIR, `${safeFileName(name)}.png`);
  await page.screenshot({ path: file, fullPage: Boolean(options.fullPage), animations: 'disabled' });
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
    const createActions = document.querySelector('[data-section-key="create-actions"]');
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
    const mainMessageNode = section ? section.querySelector('[data-procurement-readiness-main-message]') : null;
    const mainCount = section ? section.querySelector('[data-procurement-readiness-main-count]') : null;
    const mainText = section ? section.querySelector('[data-procurement-readiness-main-text]') : null;
    const visibleRows = section ? Array.from(section.querySelectorAll('[data-procurement-readiness-issue]')).filter(isVisible) : [];
    const nextSection = section ? section.nextElementSibling : null;
    const bodyText = (document.body.innerText || '').replace(/\s+/g, ' ').trim();
    const actionText = Array.from(document.querySelectorAll('button, a, [role=button]')).filter(isVisible).map((node) => (node.innerText || node.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim()).filter(Boolean).join(' ');
    const shellNodes = Array.from(document.querySelectorAll('.sales-console-shell[data-erpw-workspace=procurement]')).filter(isVisible);
    const textFor = (node) => (node.innerText || node.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim();
    const nodeInfo = (node) => ({
      tag: node.tagName ? node.tagName.toLowerCase() : '',
      className: node.className || '',
      dataRole: node.getAttribute('data-erpw-console-title') || node.getAttribute('data-page-route') || '',
      text: textFor(node),
      rect: rectFor(node),
    });
    const shellTitleNodes = shellNodes.length
      ? Array.from(shellNodes[0].querySelectorAll('h1, .sales-console-hero-title, [data-erpw-console-title]')).filter(isVisible).filter((node) => textFor(node) === 'Procurement Console')
      : [];
    const procurementConsoleTextNodes = Array.from(document.querySelectorAll('body *'))
      .filter(isVisible)
      .filter((node) => textFor(node) === 'Procurement Console')
      .map(nodeInfo);
    const mainProcurementHeaderNodes = procurementConsoleTextNodes.filter((node) => node.rect && node.rect.top < window.innerHeight + 4 && (/sales-console-title|sales-console-hero-title/.test(node.className || '') || node.dataRole));
    const sidebarBrandNodes = procurementConsoleTextNodes.filter((node) => node.rect && node.rect.top < window.innerHeight + 4 && (/sidebar-item-label|desk-sidebar|layout-side-section/.test(node.className || '') || node.rect.left < 220));
    const shellTitleCount = shellTitleNodes.length;
    return {
      url: location.href,
      route: window.frappe && typeof frappe.get_route === 'function' ? frappe.get_route() : null,
      bodyText,
      actionText,
      shellCount: shellNodes.length,
      shellTitleCount,
      mainProcurementHeaderCount: mainProcurementHeaderNodes.length,
      sidebarBrandCount: sidebarBrandNodes.length,
      procurementConsoleTextNodes,
      mainProcurementHeaderNodes,
      sidebarBrandNodes,
      viewport: { width: window.innerWidth, height: window.innerHeight, scrollY: window.scrollY },
      managerReadinessCount: Array.from(document.querySelectorAll('[data-procurement-manager-readiness]')).filter(isVisible).length,
      createActionsVisible: Boolean(createActions && isVisible(createActions)),
      kpiCardCount: Array.from(document.querySelectorAll('.sales-console-kpi-card')).filter(isVisible).length,
      queueCardCount: Array.from(document.querySelectorAll('.sales-console-queue-card')).filter(isVisible).length,
      readinessState: section ? section.getAttribute('data-procurement-manager-readiness-state') : null,
      title: section ? ((section.querySelector('[data-procurement-manager-readiness-title]') || {}).innerText || '').trim() : '',
      subtitle: section ? ((section.querySelector('.sales-console-section-note') || {}).innerText || '').trim() : '',
      mainMessage: mainMessageNode ? (mainMessageNode.innerText || '').replace(/\s+/g, ' ').trim() : '',
      mainMessageLabel: mainMessageNode ? (mainMessageNode.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim() : '',
      mainCountText: mainCount ? (mainCount.innerText || '').replace(/\s+/g, ' ').trim() : '',
      mainTextText: mainText ? (mainText.innerText || '').replace(/\s+/g, ' ').trim() : '',
      mainCountRect: rectFor(mainCount),
      mainTextRect: rectFor(mainText),
      mainCountTextGap: mainCount && mainText ? Math.round((mainText.getBoundingClientRect().left - mainCount.getBoundingClientRect().right) * 100) / 100 : null,
      sectionRect: rectFor(section),
      nextSectionRect: rectFor(nextSection),
      severityChips: chips,
      groupCards,
      categoryZeroChipNoise: groupCards.filter((card) => /0 Critical\s+0 Warning\s+0 Info/i.test(card.text)).map((card) => card.key),
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
  return Object.assign(state, { console: events.console || [], pageErrors: events.pageErrors || [], readinessApiCalls: events.readinessApiCalls || [] });
}

function assertClean(state, label) {
  assert(state.shellCount === 1, `${label}: expected one Procurement overview shell`, state);
  assert(state.shellTitleCount <= 1, `${label}: duplicate Procurement overview header`, state);
  assert((state.mainProcurementHeaderCount || 0) <= 1, `${label}: duplicate Procurement Console header text in main content`, state);
  assert((state.sidebarBrandCount || 0) <= 1, `${label}: duplicate Procurement Console sidebar branding`, state);
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
  const initialReadinessState = await overviewState(page);
  const loadingScreenshot = await capture(page, `manager-${viewport.key}-overview-readiness-${initialReadinessState.readinessState || 'initial'}`);
  if (initialReadinessState.readinessState === 'loading') {
    assert(initialReadinessState.createActionsVisible, `manager ${viewport.key}: create actions are blocked while readiness loads`, initialReadinessState);
    assert(initialReadinessState.kpiCardCount >= 3, `manager ${viewport.key}: KPI cards are blocked while readiness loads`, initialReadinessState);
    assert(initialReadinessState.queueCardCount >= 1, `manager ${viewport.key}: queue cards are blocked while readiness loads`, initialReadinessState);
  }
  await page.waitForSelector('[data-procurement-readiness-top-issue]', { state: 'visible', timeout: TIMEOUT });
  const defaultScreenshot = await capture(page, `manager-${viewport.key}-overview-compressed`);
  const state = await overviewState(page);
  assertClean(state, `manager ${viewport.key}`);
  assert(state.managerReadinessCount === 1, `manager ${viewport.key}: compressed readiness queue missing`, state);
  assert((state.readinessApiCalls || []).length >= 1, `manager ${viewport.key}: manager readiness API was not called asynchronously`, state);
  assert(state.readinessState === 'ready', `manager ${viewport.key}: readiness queue did not reach ready state`, state);
  assert(state.title === 'Readiness Review Queue', `manager ${viewport.key}: readiness title mismatch`, state);
  assert(/Business readiness exceptions needing manager attention\./.test(state.subtitle), `manager ${viewport.key}: readiness subtitle mismatch`, state);
  assert(/warning|critical|No readiness exceptions/i.test(state.mainMessageLabel || state.mainMessage), `manager ${viewport.key}: readiness main message missing`, state);
  assert(!/\d(?=[^\d\s])/.test(state.mainMessageLabel || state.mainMessage), `manager ${viewport.key}: readiness main message count is visually concatenated`, state);
  if (/^\d+$/.test(state.mainCountText || '')) {
    assert((state.mainCountTextGap || 0) >= 6, `manager ${viewport.key}: readiness main count and message are too tight`, state);
    assert(/item buying warnings need review|critical.*need review|info.*need review/i.test(state.mainTextText), `manager ${viewport.key}: readiness main message text missing`, state);
  }
  assert(state.severityChips.length >= 3, `manager ${viewport.key}: severity count chips missing`, state);
  for (const severity of ['critical', 'warning', 'info']) {
    assert(state.severityChips.some((chip) => chip.severity === severity), `manager ${viewport.key}: ${severity} chip missing`, state);
  }
  assert(state.groupCards.length === REQUIRED_GROUPS.length, `manager ${viewport.key}: readiness category cards missing`, state);
  assert((state.categoryZeroChipNoise || []).length === 0, `manager ${viewport.key}: category cards show repeated zero-chip noise`, state);
  assert(state.requiredGroupsPresent.length === REQUIRED_GROUPS.length, `manager ${viewport.key}: readiness category labels missing`, state);
  assert(state.topIssues.length >= 1 && state.topIssues.length <= 3, `manager ${viewport.key}: default visible top issue count is not compressed`, state);
  assert(state.topIssues[0].rect.top < viewport.height + 40, `manager ${viewport.key}: first top issue is too far below the initial viewport`, state);
  assert(state.visibleIssueRows === state.topIssues.length, `manager ${viewport.key}: default issue list is longer than top issues`, state);
  assert(state.expandedHidden === true, `manager ${viewport.key}: full issue list should be collapsed by default`, state);
  assert(state.toggleText === 'View all readiness issues', `manager ${viewport.key}: expand control missing`, state);
  assert(state.toggleExpanded === 'false', `manager ${viewport.key}: expand control should advertise collapsed state`, state);
  assert(state.sectionRect && state.sectionRect.height <= 720, `manager ${viewport.key}: readiness queue is too tall for overview`, state);
  const initialPath = new URL(state.url).pathname;
  const initialRoute = JSON.stringify(state.route || []);

  await page.locator('[data-procurement-readiness-toggle]').click();
  const expandedImmediateScreenshot = await capture(page, `manager-${viewport.key}-overview-expanded-immediate`);
  await page.waitForFunction(() => {
    const section = document.querySelector('[data-procurement-manager-readiness]');
    const expanded = section && section.querySelector('[data-procurement-readiness-expanded-list]');
    return expanded && expanded.hidden === false;
  }, null, { timeout: TIMEOUT });
  const expandedScreenshot = await capture(page, `manager-${viewport.key}-overview-expanded`);
  const expandedState = await overviewState(page);
  assertClean(expandedState, `manager ${viewport.key} expanded`);
  assert(new URL(expandedState.url).pathname === initialPath, `manager ${viewport.key}: expand changed route path`, { before: state, after: expandedState });
  assert(JSON.stringify(expandedState.route || []) === initialRoute, `manager ${viewport.key}: expand changed Frappe route`, { before: state, after: expandedState });
  assert(expandedState.expandedHidden === false, `manager ${viewport.key}: full issue list remained hidden after expand`, expandedState);
  assert(expandedState.toggleExpanded === 'true', `manager ${viewport.key}: expand control did not advertise expanded state`, expandedState);
  assert(expandedState.toggleText === 'Show top readiness issues', `manager ${viewport.key}: collapse control missing after expand`, expandedState);
  assert(expandedState.expandedVisibleRows > 0, `manager ${viewport.key}: expanded list has no visible rows`, expandedState);
  assert(expandedState.expandedVisibleRows >= expandedState.topIssues.length, `manager ${viewport.key}: expanded list did not reveal grouped issues`, expandedState);

  await page.waitForTimeout(350);
  const expandedSettledScreenshot = await capture(page, `manager-${viewport.key}-overview-expanded-settled`);
  const expandedSettledState = await overviewState(page);
  assertClean(expandedSettledState, `manager ${viewport.key} expanded settled`);
  assert(expandedSettledState.expandedHidden === false, `manager ${viewport.key}: expanded list became hidden after settle`, expandedSettledState);
  assert(expandedSettledState.expandedVisibleRows > 0, `manager ${viewport.key}: expanded list lost visible rows after settle`, expandedSettledState);

  await page.evaluate(() => window.scrollBy(0, Math.min(140, Math.max(0, document.documentElement.scrollHeight - window.innerHeight))));
  await page.waitForTimeout(150);
  const expandedScrolledScreenshot = await capture(page, `manager-${viewport.key}-overview-expanded-scrolled`);
  const expandedScrolledState = await overviewState(page);
  assertClean(expandedScrolledState, `manager ${viewport.key} expanded scrolled`);
  assert(new URL(expandedScrolledState.url).pathname === initialPath, `manager ${viewport.key}: scroll changed route path`, { before: expandedState, after: expandedScrolledState });
  assert(JSON.stringify(expandedScrolledState.route || []) === initialRoute, `manager ${viewport.key}: scroll changed Frappe route`, { before: expandedState, after: expandedScrolledState });
  await page.evaluate(() => window.scrollTo(0, 0));

  await page.locator('[data-procurement-readiness-toggle]').click();
  await page.waitForFunction(() => {
    const section = document.querySelector('[data-procurement-manager-readiness]');
    const expanded = section && section.querySelector('[data-procurement-readiness-expanded-list]');
    return expanded && expanded.hidden === true;
  }, null, { timeout: TIMEOUT });
  const collapsedState = await overviewState(page);
  assert(collapsedState.expandedHidden === true, `manager ${viewport.key}: readiness queue did not collapse`, collapsedState);
  assert(collapsedState.toggleExpanded === 'false', `manager ${viewport.key}: collapse control did not return to collapsed state`, collapsedState);
  assert(collapsedState.expandedVisibleRows === 0, `manager ${viewport.key}: collapsed grouped issue rows remain visible`, collapsedState);
  return {
    viewport: viewport.key,
    defaultScreenshot,
    loadingScreenshot,
    initialReadinessState,
    expandedScreenshot,
    expandedImmediateScreenshot,
    expandedSettledScreenshot,
    expandedScrolledScreenshot,
    state,
    expandedState,
    expandedSettledState,
    expandedScrolledState,
    collapsedState,
    expansionEvidence: {
      compressed: {
        expandedHidden: state.expandedHidden,
        expandedVisibleRows: state.expandedVisibleRows,
        toggleExpanded: state.toggleExpanded,
        toggleText: state.toggleText,
        readinessState: state.readinessState,
        mainMessage: state.mainMessage,
        categoryZeroChipNoise: state.categoryZeroChipNoise,
        shellCount: state.shellCount,
        shellTitleCount: state.shellTitleCount,
        mainProcurementHeaderCount: state.mainProcurementHeaderCount,
        sidebarBrandCount: state.sidebarBrandCount,
        procurementConsoleTextNodes: state.procurementConsoleTextNodes,
        route: state.route,
        url: state.url,
      },
      expanded: {
        expandedHidden: expandedState.expandedHidden,
        expandedVisibleRows: expandedState.expandedVisibleRows,
        toggleExpanded: expandedState.toggleExpanded,
        toggleText: expandedState.toggleText,
        shellCount: expandedState.shellCount,
        shellTitleCount: expandedState.shellTitleCount,
        mainProcurementHeaderCount: expandedState.mainProcurementHeaderCount,
        sidebarBrandCount: expandedState.sidebarBrandCount,
        procurementConsoleTextNodes: expandedState.procurementConsoleTextNodes,
        route: expandedState.route,
        url: expandedState.url,
      },
      expandedSettled: {
        expandedHidden: expandedSettledState.expandedHidden,
        expandedVisibleRows: expandedSettledState.expandedVisibleRows,
        toggleExpanded: expandedSettledState.toggleExpanded,
        toggleText: expandedSettledState.toggleText,
        shellCount: expandedSettledState.shellCount,
        shellTitleCount: expandedSettledState.shellTitleCount,
        mainProcurementHeaderCount: expandedSettledState.mainProcurementHeaderCount,
        sidebarBrandCount: expandedSettledState.sidebarBrandCount,
        procurementConsoleTextNodes: expandedSettledState.procurementConsoleTextNodes,
        route: expandedSettledState.route,
        url: expandedSettledState.url,
      },
      expandedScrolled: {
        expandedHidden: expandedScrolledState.expandedHidden,
        expandedVisibleRows: expandedScrolledState.expandedVisibleRows,
        toggleExpanded: expandedScrolledState.toggleExpanded,
        toggleText: expandedScrolledState.toggleText,
        shellCount: expandedScrolledState.shellCount,
        shellTitleCount: expandedScrolledState.shellTitleCount,
        mainProcurementHeaderCount: expandedScrolledState.mainProcurementHeaderCount,
        sidebarBrandCount: expandedScrolledState.sidebarBrandCount,
        procurementConsoleTextNodes: expandedScrolledState.procurementConsoleTextNodes,
        route: expandedScrolledState.route,
        url: expandedScrolledState.url,
      },
      collapsed: {
        expandedHidden: collapsedState.expandedHidden,
        expandedVisibleRows: collapsedState.expandedVisibleRows,
        toggleExpanded: collapsedState.toggleExpanded,
        toggleText: collapsedState.toggleText,
        shellCount: collapsedState.shellCount,
        shellTitleCount: collapsedState.shellTitleCount,
        mainProcurementHeaderCount: collapsedState.mainProcurementHeaderCount,
        sidebarBrandCount: collapsedState.sidebarBrandCount,
        procurementConsoleTextNodes: collapsedState.procurementConsoleTextNodes,
        route: collapsedState.route,
        url: collapsedState.url,
      },
    },
  };
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
  assert((state.readinessApiCalls || []).length === 0, `user ${viewport.key}: manager readiness API must not be called`, state);
  assert(!/Readiness Review Queue/i.test(state.bodyText), `user ${viewport.key}: manager readiness title leaked`, state);
  return { viewport: viewport.key, screenshot, state };
}

async function runForUser(browser, user) {
  const context = await browser.newContext();
  await installAssetOverrides(context);
  const page = await context.newPage();
  PAGE_EVENTS.set(page, { console: [], pageErrors: [], readinessApiCalls: [] });
  page.on('response', (response) => {
    const events = PAGE_EVENTS.get(page);
    if (events && response.url().includes(READINESS_METHOD_FRAGMENT)) {
      events.readinessApiCalls.push({ status: response.status(), url: response.url() });
    }
  });
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
