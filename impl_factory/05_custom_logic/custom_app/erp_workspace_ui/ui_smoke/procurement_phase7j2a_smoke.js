const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const TIMEOUT = Number(process.env.ERPW_PROCUREMENT_PHASE7J2A_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_PROCUREMENT_PHASE7J2A_ARTIFACT_DIR || path.join(
  fs.existsSync("/freeze-artifacts") ? "/freeze-artifacts" : path.join(__dirname, "artifacts"),
  `procurement-phase7j2a-${new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z")}`
);
const ASSET_OVERRIDE_ROOT = process.env.ERPW_PROCUREMENT_PHASE7J2A_ASSET_ROOT || "";

fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

const USERS = [
  {
    key: "manager",
    label: "Purchase Manager",
    username: process.env.ERPW_PURCHASE_MANAGER_USERNAME || process.env.ERPW_MANAGER_USERNAME,
    password: process.env.ERPW_PURCHASE_MANAGER_PASSWORD || process.env.ERPW_MANAGER_PASSWORD,
  },
  {
    key: "user",
    label: "Purchase User",
    username: process.env.ERPW_PURCHASE_USER_USERNAME || process.env.ERPW_USER_USERNAME,
    password: process.env.ERPW_PURCHASE_USER_PASSWORD || process.env.ERPW_USER_PASSWORD,
  },
].filter((user) => user.username && user.password);

const VIEWPORTS = [
  { key: "laptop-1136", width: 1136, height: 768 },
  { key: "laptop-1240", width: 1240, height: 768 },
  { key: "desktop-1440", width: 1440, height: 900 },
];

const FORBIDDEN_TEXT_RE = /Open ERP Form|Open ERP Supplier Form|Open ERP Item Form|Advanced ERP Form|Internal Server Error|Traceback|Confirm\s+test\s+send|Submit Purchase|Submit RFQ|Submit Supplier Quotation|Submit Purchase Order|Approve Purchase|Reject Purchase|Cancel Purchase|Amend Purchase|Create Supplier Quotation|Create Purchase Order|Receive Items|Create Purchase Receipt|Create Purchase Invoice|Bill Purchase Order|Make Payment|Payment Entry|Pay Supplier|Set default supplier|Update item price/i;
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
  return String(value || "artifact").replace(/[^a-z0-9_-]+/gi, "-").replace(/^-+|-+$/g, "").toLowerCase();
}

async function capture(page, name) {
  const file = path.join(ARTIFACT_DIR, `${safeFileName(name)}.png`);
  await page.screenshot({ path: file, fullPage: true, animations: "disabled" });
  return file;
}

async function installAssetOverrides(context) {
  if (!ASSET_OVERRIDE_ROOT) return;
  const overrides = [
    { pattern: "**/assets/erp_workspace_ui/js/procurement_console/procurement_console_supplier_page.js*", file: "procurement_console_supplier_page.js" },
    { pattern: "**/assets/erp_workspace_ui/js/procurement_console/procurement_console_item_page.js*", file: "procurement_console_item_page.js" },
  ];
  for (const item of overrides) {
    await context.route(item.pattern, async (route) => {
      const file = path.join(ASSET_OVERRIDE_ROOT, item.file);
      if (fs.existsSync(file)) {
        return route.fulfill({ path: file, contentType: "application/javascript" });
      }
      return route.continue();
    });
  }
}

async function login(page, user) {
  await page.goto(routeUrl("/login"), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  const userField = page.locator("#login_email, input[name=usr], input[name=login_email], input[type=email], input[type=text]").first();
  const passwordField = page.locator("#login_password, input[name=pwd], input[name=login_password], input[type=password]").first();
  const loginButton = page.locator("button.btn-login, .btn-login, button[type=submit]").first();
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

async function fixtures(page) {
  const values = await page.evaluate(async () => {
    const supplierResult = await frappe.call({
      method: "frappe.client.get_list",
      args: { doctype: "Supplier", filters: { disabled: 0 }, fields: ["name", "supplier_name"], limit_page_length: 1 },
    });
    const itemResult = await frappe.call({
      method: "frappe.client.get_list",
      args: { doctype: "Item", filters: { is_purchase_item: 1, disabled: 0 }, fields: ["name", "item_name"], limit_page_length: 1 },
    });
    return {
      supplier: (supplierResult.message || [])[0] || null,
      item: (itemResult.message || [])[0] || null,
    };
  });
  assert(values.supplier && values.supplier.name, "No supplier fixture available", values);
  assert(values.item && values.item.name, "No buying item fixture available", values);
  return values;
}

async function pageState(page, type) {
  const events = PAGE_EVENTS.get(page) || { console: [], pageErrors: [], failedResponses: [] };
  const state = await page.evaluate((detailType) => {
    const isVisible = (node) => {
      if (!node) return false;
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
    };
    const textFor = (node) => (node && (node.innerText || node.textContent || "").replace(/\s+/g, " ").trim()) || "";
    const shellSelector = detailType === "supplier" ? ".erpw-procurement-supplier-detail-shell" : ".erpw-procurement-item-detail-shell";
    const profileSelector = detailType === "supplier" ? "[data-erpw-object-profile='supplier']" : "[data-erpw-object-profile='buying-item']";
    const cardSelector = detailType === "supplier" ? "[data-erpw-supplier-readiness-card]" : "[data-erpw-item-buying-profile-card]";
    const tabs = Array.from(document.querySelectorAll("[data-erpw-object-tab]")).filter(isVisible);
    const visiblePanels = Array.from(document.querySelectorAll("[data-erpw-object-tab-panel]")).filter(isVisible);
    const activeTab = document.querySelector("[data-erpw-object-tab].is-active");
    const activePanel = visiblePanels[0] || null;
    const nativeIndicators = Array.from(document.querySelectorAll(".form-layout, .form-page")).filter(isVisible);
    const modals = Array.from(document.querySelectorAll(".modal.show")).filter(isVisible);
    const buttons = Array.from(document.querySelectorAll("button, a, [role='button']")).filter(isVisible).map(textFor).filter(Boolean);
    const firstPanelTables = activePanel ? activePanel.querySelectorAll(".erpw-list-table").length : 0;
    const visibleRows = activePanel ? Array.from(activePanel.querySelectorAll("tbody tr")).filter(isVisible).length : 0;
    const hiddenRows = activePanel ? activePanel.querySelectorAll("tbody tr[hidden], [data-erpw-extra-row][hidden]").length : 0;
    return {
      url: location.href,
      route: window.frappe && typeof frappe.get_route === "function" ? frappe.get_route() : null,
      bodyText: textFor(document.body),
      domText: document.body.textContent || "",
      actionText: buttons.join(" "),
      shellCount: document.querySelectorAll(shellSelector).length,
      pageHeadCount: Array.from(document.querySelectorAll(".page-head")).filter(isVisible).length,
      profileCount: document.querySelectorAll(profileSelector).length,
      profileCardCount: document.querySelectorAll(cardSelector).length,
      tabLabels: tabs.map(textFor),
      activeTab: textFor(activeTab),
      visiblePanelCount: visiblePanels.length,
      activePanelText: textFor(activePanel),
      firstPanelTables,
      visibleRows,
      hiddenRows,
      showRecentButtons: Array.from(document.querySelectorAll("[data-erpw-show-recent]")).filter(isVisible).map(textFor),
      nativeIndicators: nativeIndicators.length,
      modalText: modals.map(textFor).join(" "),
      horizontalOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    };
  }, type);
  return Object.assign(state, events);
}

async function assertClean(page, type, label) {
  const state = await pageState(page, type);
  if (
    state.modalText ||
    FORBIDDEN_TEXT_RE.test(state.bodyText) ||
    FORBIDDEN_TEXT_RE.test(state.actionText) ||
    NATIVE_ROUTE_RE.test(state.url) ||
    state.horizontalOverflow > 2 ||
    (state.failedResponses || []).length
  ) {
    state.diagnosticScreenshot = await capture(page, `${label}-diagnostic`);
  }
  assert(state.shellCount === 1, `${label}: expected one productized detail shell`, state);
  assert(state.pageHeadCount <= 1, `${label}: duplicate native page head`, state);
  assert(state.profileCount === 1, `${label}: object profile tabs missing`, state);
  assert(state.visiblePanelCount === 1, `${label}: exactly one tab panel should be visible`, state);
  assert(state.nativeIndicators === 0, `${label}: native ERP form shell leaked`, state);
  assert(state.horizontalOverflow <= 2, `${label}: horizontal overflow`, state);
  assert(!state.modalText, `${label}: framework modal visible`, state);
  assert(!FORBIDDEN_TEXT_RE.test(state.bodyText), `${label}: forbidden text visible`, state);
  assert(!FORBIDDEN_TEXT_RE.test(state.actionText), `${label}: forbidden action visible`, state);
  assert(!NATIVE_ROUTE_RE.test(state.url), `${label}: native ERP route leaked`, state);
  assert((state.pageErrors || []).length === 0, `${label}: page errors detected`, state);
  assert((state.failedResponses || []).length === 0, `${label}: failed HTTP responses detected`, state);
  assert(!/Visibility only/i.test(state.domText), `${label}: stale Visibility only text remains in DOM`, state);
  return state;
}

async function clickTab(page, label) {
  const tab = page.locator("[data-erpw-object-tab]").filter({ hasText: label }).first();
  await tab.waitFor({ state: "visible", timeout: TIMEOUT });
  await tab.click();
  await page.waitForFunction((expected) => {
    const active = document.querySelector("[data-erpw-object-tab].is-active");
    return active && (active.innerText || "").trim() === expected;
  }, label, { timeout: TIMEOUT });
}

async function revealRowsIfAvailable(page) {
  const visibleReveal = page.locator("[data-erpw-object-tab-panel]:visible [data-erpw-show-recent]:visible").first();
  const count = await visibleReveal.count();
  if (!count) return { clicked: false };
  const before = await page.locator("[data-erpw-object-tab-panel]:visible tbody tr:visible").count().catch(() => 0);
  await visibleReveal.click();
  await page.waitForFunction((previous) => {
    return document.querySelectorAll("[data-erpw-object-tab-panel]:not([hidden]) tbody tr:not([hidden])").length > previous;
  }, before, { timeout: TIMEOUT }).catch(() => null);
  const after = await page.locator("[data-erpw-object-tab-panel]:visible tbody tr:visible").count().catch(() => 0);
  return { clicked: true, before, after };
}

async function assertSupplierDetail(page, user, supplier, viewport) {
  await page.setViewportSize(viewport);
  await openDeskRoute(page, `/desk/procurement-console-supplier/${encodeURIComponent(supplier)}`);
  await page.waitForSelector("[data-erpw-object-profile='supplier'] [data-erpw-object-tab]", { state: "visible", timeout: TIMEOUT });
  let state = await assertClean(page, "supplier", `${user.key}-supplier-${viewport.key}`);
  assert(state.activeTab === "Activity", `${user.key} supplier ${viewport.key}: Activity should be default tab`, state);
  ["Activity", "Readiness Guidance", "Orders", "RFQs", "Quotations", "References"].forEach((label) => {
    assert(state.tabLabels.includes(label), `${user.key} supplier ${viewport.key}: missing ${label} tab`, state);
  });
  assert(/Open or overdue purchase orders/i.test(state.activePanelText), `${user.key} supplier ${viewport.key}: Activity tab should show order posture`, state);
  assert(/Supplier quotations/i.test(state.activePanelText), `${user.key} supplier ${viewport.key}: Activity tab should show quotation context`, state);
  assert(state.visibleRows <= 15, `${user.key} supplier ${viewport.key}: first viewport should not expose long unbounded stacks`, state);
  const defaultScreenshot = await capture(page, `${user.key}-supplier-${viewport.key}-default`);
  const reveal = await revealRowsIfAvailable(page);
  await clickTab(page, "Readiness Guidance");
  state = await assertClean(page, "supplier", `${user.key}-supplier-${viewport.key}-readiness`);
  assert(/Readiness Review/i.test(state.bodyText), `${user.key} supplier ${viewport.key}: readiness guidance missing`, state);
  const readinessScreenshot = await capture(page, `${user.key}-supplier-${viewport.key}-readiness-guidance`);
  await clickTab(page, "References");
  state = await assertClean(page, "supplier", `${user.key}-supplier-${viewport.key}-references`);
  assert(/Supplier Buying Profile/i.test(state.bodyText), `${user.key} supplier ${viewport.key}: supplier profile missing`, state);
  if (user.key === "user") {
    assert(!/Edit Profile/i.test(state.actionText), "Purchase User must not see supplier edit affordance", state);
  }
  return { defaultScreenshot, readinessScreenshot, reveal, state };
}

async function assertItemDetail(page, user, itemCode, viewport) {
  await page.setViewportSize(viewport);
  await openDeskRoute(page, `/desk/procurement-console-item/${encodeURIComponent(itemCode)}`);
  await page.waitForSelector("[data-erpw-object-profile='buying-item'] [data-erpw-object-tab]", { state: "visible", timeout: TIMEOUT });
  let state = await assertClean(page, "item", `${user.key}-item-${viewport.key}`);
  assert(state.activeTab === "Suppliers & Prices", `${user.key} item ${viewport.key}: Suppliers & Prices should be default tab`, state);
  ["Suppliers & Prices", "Readiness Guidance", "Demand & Orders", "Quotation History", "References"].forEach((label) => {
    assert(state.tabLabels.includes(label), `${user.key} item ${viewport.key}: missing ${label} tab`, state);
  });
  assert(/Approved suppliers/i.test(state.activePanelText), `${user.key} item ${viewport.key}: Suppliers & Prices tab should show supplier references`, state);
  assert(/Supplier price review/i.test(state.activePanelText), `${user.key} item ${viewport.key}: Suppliers & Prices tab should show price references`, state);
  assert(state.visibleRows <= 12, `${user.key} item ${viewport.key}: default tab should keep bounded visible rows`, state);
  const defaultScreenshot = await capture(page, `${user.key}-item-${viewport.key}-default`);
  const reveal = await revealRowsIfAvailable(page);
  await clickTab(page, "Readiness Guidance");
  state = await assertClean(page, "item", `${user.key}-item-${viewport.key}-readiness`);
  assert(/Readiness Review/i.test(state.bodyText), `${user.key} item ${viewport.key}: readiness guidance missing`, state);
  const readinessScreenshot = await capture(page, `${user.key}-item-${viewport.key}-readiness-guidance`);
  await clickTab(page, "References");
  state = await assertClean(page, "item", `${user.key}-item-${viewport.key}-references`);
  assert(/Item Buying Context/i.test(state.bodyText), `${user.key} item ${viewport.key}: Item Buying Context label missing`, state);
  assert(!/Buying Procurement Context/i.test(state.domText), `${user.key} item ${viewport.key}: stale Buying Procurement Context label remains`, state);
  if (user.key === "user") {
    assert(!/Edit Context/i.test(state.actionText), "Purchase User must not see item edit affordance", state);
  }
  return { defaultScreenshot, readinessScreenshot, reveal, state };
}

async function runForUser(browser, user) {
  const context = await browser.newContext();
  await installAssetOverrides(context);
  const page = await context.newPage();
  PAGE_EVENTS.set(page, { console: [], pageErrors: [], failedResponses: [] });
  page.on("console", (message) => PAGE_EVENTS.get(page).console.push({ type: message.type(), text: message.text() }));
  page.on("pageerror", (error) => PAGE_EVENTS.get(page).pageErrors.push({ message: error.message, stack: error.stack }));
  page.on("response", (response) => {
    if (response.status() >= 400) {
      PAGE_EVENTS.get(page).failedResponses.push({ url: response.url(), status: response.status() });
    }
  });
  await login(page, user);
  const values = await fixtures(page);
  const result = { user: user.key, supplier: values.supplier.name, item: values.item.name, viewports: [] };
  for (const viewport of VIEWPORTS) {
    const supplier = await assertSupplierDetail(page, user, values.supplier.name, viewport);
    const item = await assertItemDetail(page, user, values.item.name, viewport);
    result.viewports.push({ viewport: viewport.key, supplier, item });
  }
  await context.close().catch(() => null);
  return result;
}

(async () => {
  assert(USERS.length >= 2, "Purchase Manager and Purchase User credentials are required for Phase 7J2A smoke");
  const browser = await chromium.launch({ headless: true });
  const results = [];
  try {
    for (const user of USERS) {
      results.push(await runForUser(browser, user));
    }
    const summary = { status: "pass", artifactDir: ARTIFACT_DIR, assetOverrideRoot: ASSET_OVERRIDE_ROOT || null, results };
    fs.writeFileSync(path.join(ARTIFACT_DIR, "phase7j2a-summary.json"), JSON.stringify(summary, null, 2));
    console.log(JSON.stringify(summary, null, 2));
  } catch (error) {
    const failure = { status: "fail", artifactDir: ARTIFACT_DIR, error: error.message, details: error.details || {} };
    fs.writeFileSync(path.join(ARTIFACT_DIR, "phase7j2a-summary.json"), JSON.stringify(failure, null, 2));
    console.error(JSON.stringify(failure, null, 2));
    process.exitCode = 1;
  } finally {
    await browser.close().catch(() => null);
  }
})();
