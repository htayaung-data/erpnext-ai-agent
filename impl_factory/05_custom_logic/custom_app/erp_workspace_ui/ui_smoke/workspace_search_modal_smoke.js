const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = process.env.ERPW_BASE_URL || 'https://meet.erpbosai.com';
const TIMEOUT = Number(process.env.ERPW_WORKSPACE_SEARCH_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_WORKSPACE_SEARCH_ARTIFACT_DIR || path.join(fs.existsSync('/freeze-artifacts') ? '/freeze-artifacts' : path.join(__dirname, 'artifacts'), `workspace-search-${new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z')}`);
const ASSET_OVERRIDE_ROOT = process.env.ERPW_WORKSPACE_SEARCH_ASSET_ROOT || process.env.ERPW_PROCUREMENT_PHASE7K_ASSET_ROOT || '';
fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

const USERS = [
  {
    workspace: 'procurement',
    label: 'Procurement Search',
    route: '/desk/procurement-console',
    username: process.env.ERPW_PURCHASE_MANAGER_USERNAME,
    password: process.env.ERPW_PURCHASE_MANAGER_PASSWORD,
    queries: ['pur'],
    expectedGroup: 'PURCHASE REQUESTS',
    expectedBadge: 'Request',
    forbiddenText: /Material Request|Productized|native ERP|native form|route only|No native/i,
  },
  {
    workspace: 'sales',
    label: 'Sales Search',
    route: '/desk/sales-console',
    username: process.env.ERPW_SALES_MANAGER_USERNAME || process.env.ERPW_MANAGER_USERNAME,
    password: process.env.ERPW_SALES_MANAGER_PASSWORD || process.env.ERPW_MANAGER_PASSWORD,
    queries: ['35', 'ACC', 'quo', 'sales', 'customer'],
    expectedGroup: null,
    expectedBadge: null,
    forbiddenText: /Internal Server Error|Traceback/i,
  },
].filter((user) => user.username && user.password);

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
    { pattern: '**/assets/erp_workspace_ui/js/runtime/console/workspace_console_sidebar.js*', file: 'workspace_console_sidebar.js', contentType: 'application/javascript' },
    { pattern: '**/assets/erp_workspace_ui/css/erp_workspace_ui.css*', file: 'erp_workspace_ui.css', contentType: 'text/css' },
    { pattern: '**/assets/erp_workspace_ui/js/procurement_console/procurement_console_page.js*', file: 'procurement_console_page.js', contentType: 'application/javascript' },
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

async function openWorkspace(page, user) {
  await page.goto(routeUrl(user.route), { waitUntil: 'domcontentloaded', timeout: TIMEOUT });
  await page.waitForSelector('.sales-console-shell', { state: 'visible', timeout: TIMEOUT });
  await page.waitForFunction((workspace) => {
    const shell = document.querySelector('.sales-console-shell');
    if (!shell) return false;
    const text = document.body.innerText || '';
    if (workspace === 'procurement') return shell.getAttribute('data-erpw-workspace') === 'procurement' || /Procurement Console/i.test(text);
    if (workspace === 'sales') return shell.getAttribute('data-erpw-workspace') === 'sales' || /Sales Console/i.test(text);
    return true;
  }, user.workspace, { timeout: TIMEOUT });
}

async function openSearch(page, mode) {
  if (mode === 'keyboard') {
    await page.keyboard.press(process.platform === 'darwin' ? 'Meta+K' : 'Control+K');
  } else {
    await page.locator('[data-erpw-sales-search-open]').first().click();
  }
  const input = page.locator('.erpw-sales-console-search-dialog [data-erpw-sales-search-input]').first();
  await input.waitFor({ state: 'visible', timeout: TIMEOUT });
  return input;
}

async function searchState(page) {
  return page.evaluate(() => {
    const visible = (node) => {
      if (!node) return false;
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
    };
    const dialog = document.querySelector('.erpw-sales-console-search-dialog .modal.show') || document.querySelector('.erpw-sales-console-search-dialog');
    const bar = dialog ? dialog.querySelector('.erpw-sales-console-search-bar') : null;
    const input = dialog ? dialog.querySelector('[data-erpw-sales-search-input]') : null;
    const results = dialog ? dialog.querySelector('[data-erpw-sales-search-results]') : null;
    const barStyle = bar ? window.getComputedStyle(bar) : null;
    const inputStyle = input ? window.getComputedStyle(input) : null;
    const placeholderStyle = input ? window.getComputedStyle(input, '::placeholder') : null;
    return {
      url: location.href,
      dialogVisible: Boolean(dialog && visible(dialog)),
      dialogText: dialog ? (dialog.innerText || '').replace(/\s+/g, ' ').trim() : '',
      resultCount: results ? Array.from(results.querySelectorAll('.erpw-sales-console-search-result')).filter(visible).length : 0,
      groupLabels: results ? Array.from(results.querySelectorAll('.erpw-sales-console-search-group-label')).filter(visible).map((node) => (node.innerText || '').replace(/\s+/g, ' ').trim()) : [],
      badges: results ? Array.from(results.querySelectorAll('.erpw-sales-console-search-result-badge')).filter(visible).map((node) => (node.innerText || '').replace(/\s+/g, ' ').trim()) : [],
      barHeight: bar ? bar.getBoundingClientRect().height : 0,
      barShadow: barStyle ? barStyle.boxShadow : '',
      inputFontSize: inputStyle ? inputStyle.fontSize : '',
      placeholderColor: placeholderStyle ? placeholderStyle.color : '',
      inputColor: inputStyle ? inputStyle.color : '',
      horizontalOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    };
  });
}

async function fillUntilResults(page, input, user) {
  let last = null;
  for (const query of user.queries) {
    await input.fill('');
    await input.fill(query);
    await page.waitForTimeout(900);
    last = await searchState(page);
    if (last.resultCount > 0) return { query, state: last };
  }
  return { query: user.queries[user.queries.length - 1], state: last };
}

async function verifySearch(page, user, mode, screenshots) {
  await openWorkspace(page, user);
  await page.setViewportSize({ width: 1136, height: 768 });
  const input = await openSearch(page, mode);
  let state = await searchState(page);
  assert(state.dialogVisible, `${user.label}: search dialog did not open with ${mode}`, state);
  assert(state.barHeight > 0 && state.barHeight <= 58, `${user.label}: search input feels too heavy`, state);
  assert(state.placeholderColor && state.placeholderColor !== state.inputColor, `${user.label}: search placeholder should be lighter than input text`, state);
  const found = await fillUntilResults(page, input, user);
  state = found.state;
  assert(state && state.resultCount > 0, `${user.label}: search returned no grouped results`, { mode, state });
  if (user.expectedGroup) {
    assert(state.groupLabels.map((label) => label.toUpperCase()).includes(user.expectedGroup), `${user.label}: missing ${user.expectedGroup} group`, state);
  }
  if (user.expectedBadge) {
    assert(state.badges.some((badge) => String(badge || '').toUpperCase() === String(user.expectedBadge || '').toUpperCase()), `${user.label}: missing ${user.expectedBadge} badge`, state);
  }
  assert(!user.forbiddenText.test(state.dialogText), `${user.label}: forbidden search copy visible`, state);
  assert(state.horizontalOverflow <= 2, `${user.label}: search modal horizontal overflow`, state);
  screenshots[`${user.workspace}-${mode}`] = await capture(page, `${user.workspace}-search-${mode}-${found.query}`);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(150);
  state = await searchState(page);
  assert(!state.dialogVisible || !/\S/.test(state.dialogText), `${user.label}: Escape did not close Search dialog`, state);
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
  const screenshots = {};
  await verifySearch(page, user, 'keyboard', screenshots);
  await verifySearch(page, user, 'button', screenshots);
  assert(pageErrors.length === 0, `${user.label}: page errors`, { pageErrors });
  assert(!consoleMessages.some((line) => /Internal Server Error|Traceback/i.test(line)), `${user.label}: console failure`, { consoleMessages });
  await context.close();
  return { workspace: user.workspace, screenshots };
}

async function main() {
  assert(USERS.length >= 2, 'Procurement and Sales manager credentials are required');
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
  fs.writeFileSync(path.join(ARTIFACT_DIR, 'workspace-search-summary.json'), JSON.stringify(summary, null, 2));
  console.log(JSON.stringify(summary, null, 2));
}

main().catch((error) => {
  const failure = { status: 'fail', message: error.message, details: error.details || {}, stack: error.stack };
  fs.writeFileSync(path.join(ARTIFACT_DIR, 'workspace-search-summary.json'), JSON.stringify(failure, null, 2));
  console.error(failure);
  process.exit(1);
});
