const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const TIMEOUT = Number(process.env.ERPW_PROCUREMENT_SMOKE_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_PROCUREMENT_PHASE7E2A_ARTIFACT_DIR || path.join(__dirname, "artifacts", "procurement-phase7e2a");
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

const FORBIDDEN_LABELS = [
  "Open ERP Form",
  "Open ERP Supplier Form",
  "Open ERP Item Form",
  "Advanced ERP Form",
  ["Confirm", "test", "send"].join(" "),
  "Insufficient Permissions",
  "Internal Server Error",
  "Traceback",
];
const FORBIDDEN_TEXT_RE = new RegExp(FORBIDDEN_LABELS.map((label) => label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|"), "i");
const FORBIDDEN_ACTION_RE = /(submit|approve|reject|receive|bill|payment|supplier portal|create supplier quotation|create purchase order|email suppliers|send rfq)/i;
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
  return String(value || "shot").replace(/[^a-z0-9_-]+/gi, "-").replace(/^-+|-+$/g, "").toLowerCase();
}

async function capture(page, name) {
  const file = path.join(ARTIFACT_DIR, `${safeFileName(name)}.png`);
  await page.screenshot({ path: file, fullPage: true });
  return file;
}

async function pageState(page) {
  const events = PAGE_EVENTS.get(page) || { console: [], pageErrors: [] };
  const state = await page.evaluate(() => {
    const visible = (node) => {
      if (!node) return false;
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
    };
    const modals = Array.from(document.querySelectorAll(".modal.show")).filter(visible).map((node) => (node.innerText || "").replace(/\s+/g, " ").trim());
    return {
      url: location.href,
      route: window.frappe && typeof frappe.get_route === "function" ? frappe.get_route() : null,
      bodyText: (document.body.innerText || "").replace(/\s+/g, " ").trim(),
      actionText: Array.from(document.querySelectorAll("button, a, [role='button']")).filter(visible).map((node) => (node.innerText || node.getAttribute("aria-label") || "").replace(/\s+/g, " ").trim()).filter(Boolean).join(" "),
      modalCount: modals.length,
      modalText: modals.join(" "),
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
      itemBuyingProfileCards: document.querySelectorAll("[data-erpw-item-buying-profile-card]").length,
      nativeFormIndicators: document.querySelectorAll(".form-layout, .form-page").length,
      editButtons: document.querySelectorAll("[data-erpw-item-profile-edit]").length,
      saveButtons: document.querySelectorAll("[data-erpw-item-profile-save]").length,
    };
  });
  return Object.assign(state, { console: events.console || [], pageErrors: events.pageErrors || [] });
}

async function assertCleanPage(page, label) {
  const state = await pageState(page);
  if (state.modalCount || FORBIDDEN_TEXT_RE.test(state.bodyText) || FORBIDDEN_TEXT_RE.test(state.modalText)) {
    await capture(page, `${label}-unexpected-state`);
  }
  assert(state.modalCount === 0, "Framework modal must not be visible", state);
  assert(!FORBIDDEN_TEXT_RE.test(state.bodyText), "Forbidden/native/framework text leaked", state);
  assert(!FORBIDDEN_TEXT_RE.test(state.modalText), "Forbidden/native/framework modal leaked", state);
  assert(state.scrollWidth <= state.clientWidth + 2, "Page has horizontal overflow", state);
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

async function fixtures(page) {
  const values = await page.evaluate(async () => {
    const itemResult = await frappe.call({ method: "frappe.client.get_list", args: { doctype: "Item", filters: { is_purchase_item: 1, disabled: 0 }, fields: ["name", "item_name", "stock_uom"], limit_page_length: 1 } });
    const supplierResult = await frappe.call({ method: "frappe.client.get_list", args: { doctype: "Supplier", filters: { disabled: 0 }, fields: ["name", "supplier_name"], limit_page_length: 1 } });
    return {
      item: (itemResult.message || [])[0] || null,
      supplier: (supplierResult.message || [])[0] || null,
    };
  });
  assert(values.item && values.item.name, "No buying item available", values);
  assert(values.supplier && values.supplier.name, "No supplier available", values);
  return values;
}

async function assertDirectory(page, user, expectedText) {
  await openDeskRoute(page, "/desk/procurement-console-worklist/buying-item-directory");
  await page.waitForFunction(() => /Buying item records/i.test(document.body.innerText || ""), null, { timeout: TIMEOUT });
  const state = await pageState(page);
  assert(/Readiness/i.test(state.bodyText), "Buying Items directory must show readiness column/chip", state);
  if (expectedText) assert(new RegExp(expectedText, "i").test(state.bodyText), "Buying Items directory did not show expected readiness", state);
  assert(!FORBIDDEN_ACTION_RE.test(state.actionText), "Forbidden procurement action leaked on Buying Items Directory", state);
  await assertCleanPage(page, `${user.key}-buying-items-directory`);
  await capture(page, `${user.key}-buying-items-directory-1136`);
}

async function assertItemDetail(page, user, itemCode, canEdit) {
  for (const viewport of [{ width: 1136, height: 768 }, { width: 1240, height: 768 }, { width: 1440, height: 900 }]) {
    await page.setViewportSize(viewport);
    await openDeskRoute(page, `/desk/procurement-console-item/${encodeURIComponent(itemCode)}`);
    await page.waitForSelector("[data-erpw-item-buying-profile-card]", { state: "visible", timeout: TIMEOUT });
    const state = await pageState(page);
    assert(state.itemBuyingProfileCards === 1, "Buying Procurement Context card should appear once", state);
    assert(!FORBIDDEN_ACTION_RE.test(state.actionText), "Forbidden procurement action leaked on Buying Item Detail", state);
    await assertCleanPage(page, `${user.key}-buying-item-detail-${viewport.width}`);
    await capture(page, `${user.key}-buying-item-context-${viewport.width}`);
  }
  const state = await pageState(page);
  assert(canEdit ? state.editButtons === 1 : state.editButtons === 0, "Buying profile edit visibility did not match role", state);
}

async function saveManagerItemContext(page, itemCode, supplier) {
  await openDeskRoute(page, `/desk/procurement-console-item/${encodeURIComponent(itemCode)}`);
  await page.waitForSelector("[data-erpw-item-buying-profile-card]", { state: "visible", timeout: TIMEOUT });
  await page.locator("[data-erpw-item-profile-edit]").click();
  await page.locator("[data-erpw-item-profile-field='buying_readiness_status']").selectOption("Needs sourcing review");
  await page.locator("[data-erpw-item-profile-field='preferred_existing_supplier']").fill(supplier);
  await page.locator("[data-erpw-item-profile-field='supplier_part_no_context']").fill("PHASE7E2A-CONTEXT");
  await page.locator("[data-erpw-item-profile-field='procurement_lead_time_days']").fill("14");
  await page.locator("[data-erpw-item-profile-field='minimum_order_qty_context']").fill("12");
  await page.locator("[data-erpw-item-profile-field='buying_note']").fill("Smoke-managed item buying note.");
  await page.locator("[data-erpw-item-profile-field='readiness_note']").fill("Smoke sourcing review pending.");
  await Promise.all([
    page.waitForResponse((response) => response.url().includes("save_item_buying_profile") && response.ok(), { timeout: TIMEOUT }),
    page.locator("[data-erpw-item-profile-save]").click(),
  ]);
  await page.waitForFunction(() => /Needs sourcing review/i.test(document.body.innerText || ""), null, { timeout: TIMEOUT });
  const state = await pageState(page);
  assert(/PHASE7E2A-CONTEXT/i.test(state.bodyText), "Saved supplier part context not visible", state);
  assert(/14 days/i.test(state.bodyText), "Saved lead time not visible", state);
  assert(!/\d{2}:\d{2}:\d{2}\.\d+/.test(state.bodyText), "Last Updated must not show raw microsecond timestamp", state);
  await assertCleanPage(page, "manager-item-context-after-save");
  await capture(page, "manager-item-context-after-save");
}

async function runForUser(user) {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1136, height: 768 }, acceptDownloads: true });
  const page = await context.newPage();
  PAGE_EVENTS.set(page, { console: [], pageErrors: [] });
  page.on("console", (message) => PAGE_EVENTS.get(page).console.push({ type: message.type(), text: message.text() }));
  page.on("pageerror", (error) => PAGE_EVENTS.get(page).pageErrors.push({ message: error.message, stack: error.stack }));
  try {
    await login(page, user);
    const values = await fixtures(page);
    await assertDirectory(page, user, null);
    await assertItemDetail(page, user, values.item.name, user.key === "manager");
    if (user.key === "manager") {
      await saveManagerItemContext(page, values.item.name, values.supplier.name);
      await assertDirectory(page, user, "Needs sourcing review");
    }
    if (user.key === "user") {
      await assertCleanPage(page, "purchase-user-item-readonly");
    }
  } catch (error) {
    await capture(page, `${user.key}-failure`);
    const diagnostic = await pageState(page).catch((diagnosticError) => ({ diagnosticError: diagnosticError.message }));
    fs.writeFileSync(path.join(ARTIFACT_DIR, `${safeFileName(user.key)}-failure.json`), JSON.stringify({ error: error.message, details: error.details || {}, diagnostic }, null, 2));
    throw error;
  } finally {
    await context.close().catch(() => null);
    await browser.close().catch(() => null);
  }
}

(async () => {
  assert(USERS.length >= 1, "No procurement credentials supplied");
  const results = [];
  for (const user of USERS) {
    await runForUser(user);
    results.push({ user: user.key, status: "pass" });
  }
  fs.writeFileSync(path.join(ARTIFACT_DIR, "phase7e2a-summary.json"), JSON.stringify({ status: "pass", results }, null, 2));
  console.log(`Phase 7E2A smoke passed. Artifacts: ${ARTIFACT_DIR}`);
})().catch((error) => {
  fs.writeFileSync(path.join(ARTIFACT_DIR, "phase7e2a-summary.json"), JSON.stringify({ status: "fail", error: error.message, details: error.details || {} }, null, 2));
  console.error(error);
  process.exit(1);
});
