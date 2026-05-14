const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const TIMEOUT = Number(process.env.ERPW_PROCUREMENT_SMOKE_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_PROCUREMENT_PHASE5B_ARTIFACT_DIR || path.join(__dirname, "artifacts", "procurement-phase5b");
fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

const USERS = [
  { key: "manager", label: "Purchase Manager", username: process.env.ERPW_MANAGER_USERNAME, password: process.env.ERPW_MANAGER_PASSWORD },
  { key: "user", label: "Purchase User", username: process.env.ERPW_USER_USERNAME, password: process.env.ERPW_USER_PASSWORD },
].filter((user) => user.username && user.password);

const FORBIDDEN_ACTION_RE = /(submit|send email|email supplier|supplier portal|create supplier quotation|create purchase order|purchase order|supplier quotation|item price|default supplier|set default supplier|receive|bill|pay|payment|invoice|phase 5b)/i;

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
  return String(value || "shot").replace(/[^a-z0-9_-]+/gi, "-").replace(/^-+|-+$/g, "").toLowerCase();
}

async function capture(page, name) {
  const file = path.join(ARTIFACT_DIR, `${safeFileName(name)}.png`);
  await page.screenshot({ path: file, fullPage: true });
  return file;
}

async function login(page, user) {
  await page.goto(routeUrl("/login"), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  const userField = page.locator("#login_email, input[name='usr'], input[name='login_email'], input[type='email'], input[type='text']").first();
  const passwordField = page.locator("#login_password, input[name='pwd'], input[name='login_password'], input[type='password']").first();
  const loginButton = page.locator("button:has-text('Login'), button.btn-login, .btn-login").first();
  await userField.waitFor({ state: "visible", timeout: TIMEOUT });
  await userField.fill(user.username);
  await passwordField.fill(user.password);
  await Promise.all([
    page.waitForURL(/\/(?:app|desk)(?:[/?#]|$)/, { waitUntil: "domcontentloaded", timeout: TIMEOUT }),
    loginButton.click(),
  ]);
}

async function openDeskRoute(page, route) {
  const url = routeUrl(route);
  const pathName = new URL(url).pathname;
  const canRoute = await page.evaluate(() => Boolean(window.frappe && typeof frappe.set_route === "function")).catch(() => false);
  if (canRoute && pathName.startsWith("/desk/")) {
    const parts = pathName.replace(/^\/desk\/?/, "").split("/").filter(Boolean).map((part) => decodeURIComponent(part));
    await page.evaluate((routeParts) => frappe.set_route.apply(frappe, routeParts), parts);
    await page.waitForURL((current) => current.pathname === pathName, { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  } else {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  }
  if (/\/login(?:[/?#]|$)/.test(page.url())) throw new Error(`Route ${route} redirected to login`);
  await page.waitForFunction(() => Boolean(window.frappe), null, { timeout: TIMEOUT });
}

async function waitForManagedRfq(page) {
  await page.waitForSelector(".erpw-managed-rfq-page .erpw-managed-rfq-card", { state: "visible", timeout: TIMEOUT });
}

async function stableRfqSnapshot(page, label) {
  await waitForManagedRfq(page);
  const state = await page.evaluate(() => {
    const visible = (node) => {
      if (!node) return false;
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
    };
    const shells = Array.from(document.querySelectorAll(".erpw-managed-rfq-page")).filter(visible);
    const shell = shells[0] || null;
    const buttons = shell ? Array.from(shell.querySelectorAll(".erpw-child-toolbar-action")).filter(visible).map((button) => button.textContent.trim()) : [];
    const removeRects = shell ? Array.from(shell.querySelectorAll(".erpw-managed-rfq-row-button")).map((button) => {
      const rect = button.getBoundingClientRect();
      return { text: button.textContent.trim(), right: Math.round(rect.right), visible: visible(button) };
    }) : [];
    const bodyWidth = Math.ceil(Math.max(document.body.scrollWidth, document.documentElement.scrollWidth));
    const viewportWidth = Math.ceil(window.innerWidth);
    const text = shell ? shell.innerText : document.body.innerText;
    return {
      url: location.pathname,
      shellCount: document.querySelectorAll(".erpw-managed-rfq-page").length,
      visibleShellCount: shells.length,
      bodyWidth,
      viewportWidth,
      buttons,
      removeRects,
      hasCompanyField: Boolean(shell && shell.querySelector('[data-field="company"]')),
      text,
    };
  });
  assert(state.visibleShellCount === 1 && state.shellCount === 1, `${label}: managed RFQ shell stacked`, state);
  assert(state.bodyWidth <= state.viewportWidth + 2, `${label}: horizontal overflow`, state);
  assert(state.buttons.includes("Save RFQ"), `${label}: Save RFQ action missing`, state);
  assert(!state.buttons.some((label) => /Open ERP Form/i.test(label)) || !/\/new$/.test(state.url), `${label}: Open ERP Form appeared before save`, state);
  assert(!state.hasCompanyField, `${label}: company field should not render in managed RFQ UI`, state);
  assert(!/\bDraft\b|Phase 5B/i.test(state.text || ""), `${label}: technical draft or phase text visible`, state);
  assert(!FORBIDDEN_ACTION_RE.test(state.buttons.join(" ")), `${label}: forbidden RFQ action visible`, state);
  assert(state.removeRects.every((rect) => !rect.visible || rect.right <= state.viewportWidth + 1), `${label}: remove action clips past viewport`, state);
  assert(!/\/desk\/(?:request-for-quotation|Form\/Request%20for%20Quotation|Form\/Request for Quotation)\//i.test(page.url()), `${label}: native RFQ route leaked`, state);
  return state;
}

async function assertFocusStable(page, label) {
  const before = await page.evaluate(() => Math.ceil(Math.max(document.body.scrollWidth, document.documentElement.scrollWidth)));
  await page.locator(".erpw-managed-rfq-page .supplier-link").first().focus();
  await page.waitForTimeout(125);
  const after = await page.evaluate(() => Math.ceil(Math.max(document.body.scrollWidth, document.documentElement.scrollWidth)));
  assert(Math.abs(after - before) <= 1, `${label}: focus changed body width`, { before, after });
}

async function getFixtureValues(page) {
  const values = await page.evaluate(async () => {
    const supplierResult = await frappe.call({ method: "frappe.client.get_list", args: { doctype: "Supplier", fields: ["name", "supplier_name"], limit_page_length: 1 } });
    const itemResult = await frappe.call({ method: "frappe.client.get_list", args: { doctype: "Item", filters: { is_purchase_item: 1, disabled: 0 }, fields: ["name", "item_name", "stock_uom"], limit_page_length: 1 } });
    const warehouseResult = await frappe.call({ method: "frappe.client.get_list", args: { doctype: "Warehouse", filters: { disabled: 0 }, fields: ["name"], limit_page_length: 1 } }).catch(() => ({ message: [] }));
    return { supplier: (supplierResult.message || [])[0] || null, item: (itemResult.message || [])[0] || null, warehouse: (warehouseResult.message || [])[0] || null };
  });
  assert(values.supplier && values.supplier.name, "No supplier available for managed RFQ smoke", values);
  assert(values.item && values.item.name, "No purchase item available for managed RFQ smoke", values);
  return values;
}

async function chooseAutocomplete(page, selector, value, screenshotName) {
  const input = page.locator(selector).first();
  await input.fill("");
  await input.type(String(value).slice(0, Math.min(6, String(value).length)));
  const suggestion = page.locator(".erpw-managed-rfq-suggestion").first();
  await suggestion.waitFor({ state: "visible", timeout: TIMEOUT });
  if (screenshotName) {
    const overlay = await suggestion.evaluate((node) => {
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return { top: rect.top, left: rect.left, right: rect.right, bottom: rect.bottom, zIndex: style.zIndex, viewportWidth: window.innerWidth, visible: rect.width > 0 && rect.height > 0 };
    });
    assert(overlay.visible && overlay.right <= window.innerWidth + 2, `${screenshotName}: autocomplete overlay clipped`, overlay);
    await capture(page, screenshotName);
  }
  await suggestion.click();
}

async function fillAndSaveRfq(page, userKey) {
  const { supplier, item, warehouse } = await getFixtureValues(page);
  await page.locator('[data-field="transaction_date"]').fill("2026-05-14");
  await page.locator('[data-field="schedule_date"]').fill("2026-05-21");
  await chooseAutocomplete(page, ".supplier-link", supplier.name, `${userKey}-supplier-autocomplete-1136`);
  await chooseAutocomplete(page, ".item-link", item.name, `${userKey}-item-autocomplete-1136`);
  await page.locator('[data-row-field="qty"]').first().fill("1");
  await page.locator('[data-row-field="schedule_date"]').first().fill("2026-05-21");
  if (warehouse && warehouse.name) await chooseAutocomplete(page, ".warehouse-link", warehouse.name);
  await page.locator("button:has-text('Save RFQ')").click();
  await page.waitForFunction(() => /procurement-console-rfq-form\/(?!new$)[^/]+$/.test(location.pathname), null, { timeout: TIMEOUT });
  await waitForManagedRfq(page);
  await capture(page, `${userKey}-managed-rfq-saved`);
  const saved = await page.evaluate(() => {
    const shell = document.querySelector(".erpw-managed-rfq-page");
    return { url: location.pathname, text: shell ? shell.innerText : document.body.innerText, actions: Array.from(shell ? shell.querySelectorAll(".erpw-child-toolbar-action") : []).map((button) => button.textContent.trim()) };
  });
  assert(/RFQ Recorded/.test(saved.text || ""), "RFQ Recorded status missing after save", saved);
  assert(saved.actions.some((label) => /Open ERP Form/i.test(label)), "Open ERP Form should appear only after saved RFQ", saved);
  assert(saved.actions.some((label) => /Review RFQ/i.test(label)), "Review RFQ action missing after save", saved);
  assert(!/Submit|Send Email|Supplier Portal|Create Supplier Quotation|Create Purchase Order/i.test(saved.text || ""), "Forbidden RFQ action text visible after save", saved);
}

async function verifyOverviewAction(page, user) {
  await openDeskRoute(page, "/desk/procurement-console");
  await page.waitForSelector('[data-section-key="create-actions"]', { state: "visible", timeout: TIMEOUT });
  await page.locator('[data-erpw-procurement-create-action="new_rfq"]').click();
  await page.waitForURL(/procurement-console-rfq-form\/new$/, { timeout: TIMEOUT });
  await stableRfqSnapshot(page, `${user.label} overview New RFQ`);
  await capture(page, `${user.key}-managed-rfq-new-overview`);
  return page.url().replace(/[#?].*$/, "");
}

async function verifyDirectoryAction(page, user, expectedUrl) {
  await openDeskRoute(page, "/desk/procurement-console-worklist/rfq-directory");
  await page.waitForSelector(".erpw-list-shell", { state: "visible", timeout: TIMEOUT });
  await capture(page, `${user.key}-rfq-directory-new-rfq`);
  await page.locator("button:has-text('New RFQ')").first().click();
  await page.waitForURL(/procurement-console-rfq-form\/new$/, { timeout: TIMEOUT });
  await stableRfqSnapshot(page, `${user.label} RFQ Directory New RFQ`);
  const actualUrl = page.url().replace(/[#?].*$/, "");
  assert(actualUrl === expectedUrl, "Overview and RFQ Directory must route to the same managed RFQ form", { expectedUrl, actualUrl });
}

async function verifyNoPrConversion(page, user) {
  const reviewName = process.env.ERPW_PROCUREMENT_DIRECT_PR_NAME || "MAT-MR-2026-00021";
  await openDeskRoute(page, `/desk/procurement-console-purchase-request-review/${encodeURIComponent(reviewName)}`);
  await page.waitForTimeout(600);
  const text = await page.evaluate(() => document.body.innerText || "");
  assert(!/\bCreate RFQ\b/i.test(text), `${user.label}: draft/internal Purchase Request exposed active Create RFQ`, { reviewName, text: text.slice(0, 1000) });
}

async function runForViewport(page, user, width, height) {
  await page.setViewportSize({ width, height });
  await openDeskRoute(page, "/desk/procurement-console-rfq-form/new");
  const state = await stableRfqSnapshot(page, `${user.label} managed RFQ ${width}x${height}`);
  await assertFocusStable(page, `${user.label} managed RFQ ${width}x${height}`);
  await capture(page, `${user.key}-managed-rfq-new-${width}x${height}`);
  return state;
}

async function runUser(browser, user) {
  const context = await browser.newContext({ baseURL: BASE_URL, ignoreHTTPSErrors: true, viewport: { width: 1136, height: 768 } });
  const page = await context.newPage();
  const errors = [];
  page.on("dialog", (dialog) => dialog.accept().catch(() => {}));
  page.on("pageerror", (error) => errors.push(error.message));
  try {
    await login(page, user);
    const report = { user: user.key, layouts: [] };
    for (const [width, height] of [[1136, 768], [1240, 768], [1440, 900]]) {
      report.layouts.push(await runForViewport(page, user, width, height));
    }
    await page.setViewportSize({ width: 1136, height: 768 });
    const overviewUrl = await verifyOverviewAction(page, user);
    await verifyDirectoryAction(page, user, overviewUrl);
    await fillAndSaveRfq(page, user.key);
    await verifyNoPrConversion(page, user);
    assert(errors.length === 0, `${user.label}: page JS error`, { errors });
    return report;
  } finally {
    await context.close();
  }
}

(async () => {
  assert(USERS.length > 0, "No smoke users are available in environment variables");
  const browser = await chromium.launch({ headless: true });
  try {
    const reports = [];
    for (const user of USERS) reports.push(await runUser(browser, user));
    console.log(JSON.stringify({ ok: true, baseUrl: BASE_URL, artifactDir: ARTIFACT_DIR, reports }, null, 2));
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error.stack || error.message);
  if (error.details) console.error(JSON.stringify(error.details, null, 2));
  process.exit(1);
});
