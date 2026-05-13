const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const TIMEOUT = Number(process.env.ERPW_PROCUREMENT_SMOKE_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_PROCUREMENT_PHASE5A_ARTIFACT_DIR || path.join(__dirname, "artifacts", "procurement-phase5a");
fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

const USERS = [
  { key: "manager", label: "Purchase Manager", username: process.env.ERPW_MANAGER_USERNAME, password: process.env.ERPW_MANAGER_PASSWORD },
  { key: "user", label: "Purchase User", username: process.env.ERPW_USER_USERNAME, password: process.env.ERPW_USER_PASSWORD },
].filter((user) => user.username && user.password);

const FORBIDDEN_ACTION_RE = /(submit|cancel|amend|stop|close|receive|bill|pay|payment|invoice|create purchase order|new rfq|new supplier quotation|item price|default supplier|set default supplier)/i;

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

async function waitForManagedForm(page) {
  await page.waitForSelector(".erpw-managed-pr-page .erpw-managed-pr-card", { state: "visible", timeout: TIMEOUT });
}

async function assertStableManagedForm(page, label) {
  await waitForManagedForm(page);
  const state = await page.evaluate(() => {
    const visiblePages = Array.from(document.querySelectorAll(".erpw-managed-pr-page")).filter((node) => {
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
    });
    const pageEl = visiblePages[0] || null;
    const shell = pageEl ? pageEl.querySelector(".erpw-managed-pr-shell") : null;
    const actionButtons = pageEl ? Array.from(pageEl.querySelectorAll(".erpw-child-toolbar-action")).map((button) => button.textContent.trim()) : [];
    const removeRects = pageEl ? Array.from(pageEl.querySelectorAll(".erpw-managed-pr-row-button")).map((button) => {
      const rect = button.getBoundingClientRect();
      const style = window.getComputedStyle(button);
      return {
        text: button.textContent.trim(),
        left: Math.round(rect.left),
        right: Math.round(rect.right),
        width: Math.round(rect.width),
        visible: rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden",
      };
    }) : [];
    const tableWrap = pageEl ? pageEl.querySelector(".erpw-managed-pr-table-wrap") : null;
    const tableWrapRect = tableWrap ? tableWrap.getBoundingClientRect() : null;
    const summary = pageEl ? pageEl.querySelector(".erpw-child-summary") : null;
    const summaryRect = summary ? summary.getBoundingClientRect() : null;
    const companyInput = pageEl ? pageEl.querySelector('[data-field="company"]') : null;
    const companyInputRect = companyInput ? companyInput.getBoundingClientRect() : null;
    const companyInputStyle = companyInput ? window.getComputedStyle(companyInput) : null;
    const companyContext = pageEl ? pageEl.querySelector(".erpw-managed-pr-context-card") : null;
    const companyContextRect = companyContext ? companyContext.getBoundingClientRect() : null;
    const bodyWidth = Math.ceil(Math.max(document.body.scrollWidth, document.documentElement.scrollWidth));
    const viewportWidth = Math.ceil(window.innerWidth);
    return {
      url: location.pathname,
      shellCount: document.querySelectorAll(".erpw-managed-pr-page").length,
      visibleShellCount: visiblePages.length,
      duplicateHeads: document.querySelectorAll(".page-head").length,
      hasForm: Boolean(shell && pageEl && pageEl.querySelector(".erpw-managed-pr-card")),
      actionButtons,
      bodyWidth,
      viewportWidth,
      documentWidth: Math.ceil(document.documentElement.scrollWidth),
      summaryHeight: summaryRect ? Math.round(summaryRect.height) : null,
      tableWrapRight: tableWrapRect ? Math.round(tableWrapRect.right) : null,
      tableWrapWidth: tableWrapRect ? Math.round(tableWrapRect.width) : null,
      removeRects,
      companyContextVisible: Boolean(companyContextRect && companyContextRect.width > 0 && companyContextRect.height > 0),
      companyInputVisible: Boolean(companyInputRect && companyInputRect.width > 0 && companyInputRect.height > 0 && companyInputStyle && companyInputStyle.display !== "none" && companyInputStyle.visibility !== "hidden"),
      duplicateDraftHeadings: pageEl ? (pageEl.innerText.match(/Purchase Request Draft/g) || []).length : 0,
      openErpBeforeSave: actionButtons.filter((label) => /Open ERP Form/i.test(label)).length,
      text: pageEl ? pageEl.innerText : document.body.innerText,
    };
  });
  assert(state.hasForm, `${label}: managed PR form did not render`, state);
  assert(state.shellCount === 1 && state.visibleShellCount === 1, `${label}: managed PR form shell stacked`, state);
  assert(state.bodyWidth <= state.viewportWidth + 2, `${label}: horizontal body overflow`, state);
  assert((state.summaryHeight || 0) > 0 && state.summaryHeight <= 130, `${label}: managed PR header still has an oversized empty band`, state);
  assert(state.duplicateDraftHeadings === 0, `${label}: duplicate Purchase Request Draft copy visible`, state);
  assert(state.companyContextVisible, `${label}: company context metadata is missing`, state);
  assert(!state.companyInputVisible, `${label}: company still renders as editable-looking form input`, state);
  assert(state.openErpBeforeSave === 0, `${label}: Open ERP Form must not appear before a managed Purchase Request draft is saved`, state);
  assert(state.removeRects.some((rect) => rect.visible && /Remove/i.test(rect.text)), `${label}: Remove line action is not visible`, state);
  assert(state.removeRects.every((rect) => !rect.visible || rect.right <= state.viewportWidth + 1), `${label}: Remove line action clips past viewport`, state);
  assert(!state.tableWrapRight || state.tableWrapRight <= state.viewportWidth + 1, `${label}: line-entry area clips past viewport`, state);
  assert(!FORBIDDEN_ACTION_RE.test(state.actionButtons.join(" ")), `${label}: forbidden action visible`, state);
  assert(!/\/desk\/Form\/Material Request\/new/i.test(page.url()), `${label}: native Material Request create route opened`, state);
  return state;
}

async function assertManagedFormFocusStable(page, label) {
  const before = await page.evaluate(() => {
    const shell = document.querySelector(".erpw-managed-pr-page .erpw-managed-pr-shell");
    return {
      bodyWidth: Math.ceil(Math.max(document.body.scrollWidth, document.documentElement.scrollWidth)),
      shellWidth: shell ? Math.round(shell.getBoundingClientRect().width) : 0,
    };
  });
  await page.locator(".erpw-managed-pr-page .item-link").first().focus();
  await page.waitForTimeout(125);
  const after = await page.evaluate(() => {
    const shell = document.querySelector(".erpw-managed-pr-page .erpw-managed-pr-shell");
    return {
      bodyWidth: Math.ceil(Math.max(document.body.scrollWidth, document.documentElement.scrollWidth)),
      shellWidth: shell ? Math.round(shell.getBoundingClientRect().width) : 0,
    };
  });
  assert(Math.abs(after.bodyWidth - before.bodyWidth) <= 1 && Math.abs(after.shellWidth - before.shellWidth) <= 1, `${label}: focus changed managed PR layout width`, { before, after });
}

async function getFixtureValues(page) {
  const values = await page.evaluate(async () => {
    const itemResult = await frappe.call({ method: "frappe.client.get_list", args: { doctype: "Item", filters: { is_purchase_item: 1, disabled: 0 }, fields: ["name", "item_name", "stock_uom"], limit_page_length: 1 } });
    const warehouseResult = await frappe.call({ method: "frappe.client.get_list", args: { doctype: "Warehouse", filters: { disabled: 0 }, fields: ["name"], limit_page_length: 1 } }).catch(() => ({ message: [] }));
    const item = (itemResult.message || [])[0] || null;
    const warehouse = (warehouseResult.message || [])[0] || null;
    return { item, warehouse };
  });
  assert(values.item && values.item.name, "No purchase item available for managed PR smoke", values);
  return values;
}

async function chooseAutocomplete(page, selector, value) {
  const input = page.locator(selector).first();
  await input.fill("");
  await input.type(String(value).slice(0, Math.min(6, String(value).length)));
  const suggestion = page.locator(".erpw-managed-pr-suggestion").first();
  await suggestion.waitFor({ state: "visible", timeout: TIMEOUT });
  await suggestion.click();
}

async function fillAndSaveDraft(page, userKey) {
  const { item, warehouse } = await getFixtureValues(page);
  await page.locator('[data-field="transaction_date"]').fill("2026-05-13");
  await page.locator('[data-field="schedule_date"]').fill("2026-05-20");
  await chooseAutocomplete(page, ".item-link", item.name);
  await page.locator('[data-row-field="qty"]').first().fill("1");
  await page.locator('[data-row-field="schedule_date"]').first().fill("2026-05-20");
  if (warehouse && warehouse.name) {
    await chooseAutocomplete(page, ".warehouse-link", warehouse.name);
  }
  await page.waitForFunction(() => {
    const uom = document.querySelector('[data-row-field="uom"]');
    return uom && String(uom.value || "").trim().length > 0;
  }, null, { timeout: TIMEOUT }).catch(() => {});
  await page.locator("button:has-text('Save Draft')").click();
  await page.waitForFunction(() => /procurement-console-purchase-request-form\/(?!new$)[^/]+$/.test(location.pathname), null, { timeout: TIMEOUT });
  await waitForManagedForm(page);
  await capture(page, `${userKey}-managed-pr-saved`);
  const state = await page.evaluate(() => ({
    url: location.pathname,
    actions: Array.from(document.querySelectorAll(".erpw-child-toolbar-action")).map((button) => button.textContent.trim()),
    message: document.querySelector("[data-managed-pr-message]") ? document.querySelector("[data-managed-pr-message]").textContent.trim() : "",
  }));
  assert(/procurement-console-purchase-request-form\/(?!new$)/.test(state.url), "Save Draft did not move to a saved managed PR route", state);
  assert(state.actions.some((label) => /Open ERP Form/i.test(label)), "Open ERP Form should appear only after save", state);
  assert(state.actions.some((label) => /Review Request/i.test(label)), "Review Request action missing after save", state);
}

async function verifyOverviewAction(page, user) {
  await openDeskRoute(page, "/desk/procurement-console");
  await page.waitForSelector('[data-section-key="create-actions"]', { state: "visible", timeout: TIMEOUT });
  await capture(page, `${user.key}-overview-before-new-pr`);
  await page.locator('[data-erpw-procurement-create-action="new_purchase_request"]').click();
  await page.waitForURL(/procurement-console-purchase-request-form\/new$/, { timeout: TIMEOUT });
  await assertStableManagedForm(page, `${user.label} overview New Purchase Request`);
  await capture(page, `${user.key}-managed-pr-new-overview`);
}

async function verifyDirectoryAction(page, user) {
  await openDeskRoute(page, "/desk/procurement-console-worklist/purchase-request-directory");
  await page.waitForSelector(".erpw-list-shell", { state: "visible", timeout: TIMEOUT });
  await capture(page, `${user.key}-purchase-requests-before-new-pr`);
  const createButton = page.locator("button:has-text('New Purchase Request')").first();
  await createButton.waitFor({ state: "visible", timeout: TIMEOUT });
  await createButton.click();
  await page.waitForURL(/procurement-console-purchase-request-form\/new$/, { timeout: TIMEOUT });
  await assertStableManagedForm(page, `${user.label} directory New Purchase Request`);
  await capture(page, `${user.key}-managed-pr-new-directory`);
}

async function verifyResponsive(page, user) {
  const sizes = [
    { width: 1136, height: 768 },
    { width: 1240, height: 768 },
    { width: 1440, height: 900 },
  ];
  for (const size of sizes) {
    await page.setViewportSize(size);
    await openDeskRoute(page, "/desk/procurement-console-purchase-request-form/new");
    const state = await assertStableManagedForm(page, `${user.label} ${size.width}x${size.height}`);
    await capture(page, `${user.key}-managed-pr-${size.width}x${size.height}`);
    assert(state.actionButtons.includes("Save Draft"), "Save Draft action missing at responsive size", state);
    await assertManagedFormFocusStable(page, `${user.label} ${size.width}x${size.height}`);
  }
}

async function runForUser(user) {
  const browser = await chromium.launch({ headless: process.env.ERPW_HEADLESS !== "0" });
  const page = await browser.newPage({ viewport: { width: 1240, height: 768 } });
  const errors = [];
  const failedResponses = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("response", (response) => {
    if (response.status() >= 400) failedResponses.push({ url: response.url(), status: response.status() });
  });
  try {
    await login(page, user);
    await verifyOverviewAction(page, user);
    await verifyDirectoryAction(page, user);
    await fillAndSaveDraft(page, user.key);
    await verifyResponsive(page, user);
    assert(!errors.length, `${user.label}: page JS errors`, { errors });
    assert(!failedResponses.filter((item) => !/socket.io|hot-update/.test(item.url)).length, `${user.label}: failed network responses`, { failedResponses });
  } finally {
    await browser.close();
  }
}

(async () => {
  assert(USERS.length > 0, "No Purchase Manager/User credentials were provided through env vars");
  for (const user of USERS) {
    await runForUser(user);
  }
  console.log(JSON.stringify({ status: "passed", users: USERS.map((user) => user.key), artifactDir: ARTIFACT_DIR }, null, 2));
})().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  if (error && error.details) console.error(JSON.stringify(error.details, null, 2));
  process.exit(1);
});
