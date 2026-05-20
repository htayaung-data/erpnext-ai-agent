const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const TIMEOUT = Number(process.env.ERPW_PROCUREMENT_SMOKE_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_PROCUREMENT_PHASE7H1_ARTIFACT_DIR || path.join(__dirname, "artifacts", "procurement-phase7h1");
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

const FORBIDDEN_LABELS = ["Open ERP Form", "Open ERP Supplier Form", "Open ERP Item Form", "Advanced ERP Form", "Insufficient Permissions", "Internal Server Error", "Traceback", ["Confirm", "test", "send"].join(" ")];
const FORBIDDEN_TEXT_RE = new RegExp(FORBIDDEN_LABELS.map((label) => label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|"), "i");
const FORBIDDEN_ACTION_RE = /(email suppliers|submit|approve|reject|cancel|amend|create supplier quotation|create purchase order|receive|bill|pay|set default supplier|update item price)/i;
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
    const readinessSourceText = Array.from(document.querySelectorAll(".erpw-readiness-row-source")).filter(visible).map((node) => (node.innerText || "").replace(/\s+/g, " ").trim()).join("\n");
    return {
      url: location.href,
      route: window.frappe && typeof frappe.get_route === "function" ? frappe.get_route() : null,
      bodyText: (document.body.innerText || "").replace(/\s+/g, " ").trim(),
      actionText: Array.from(document.querySelectorAll("button, a, [role='button']")).filter(visible).map((node) => (node.innerText || node.getAttribute("aria-label") || "").replace(/\s+/g, " ").trim()).filter(Boolean).join(" "),
      modalCount: modals.length,
      modalText: modals.join(" "),
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
      readinessCards: document.querySelectorAll("[data-procurement-readiness-card]").length,
      managerReadinessCards: document.querySelectorAll("[data-procurement-manager-readiness]").length,
      managerReadinessText: (document.querySelector("[data-procurement-manager-readiness]") || {}).innerText || "",
      readinessSourceText,
      nativeFormIndicators: document.querySelectorAll(".form-layout, .form-page").length,
    };
  });
  return Object.assign(state, { console: events.console || [], pageErrors: events.pageErrors || [] });
}

async function captureDiagnostics(page, label, error) {
  const state = await pageState(page).catch((diagnosticError) => ({ diagnosticError: diagnosticError.message }));
  const screenshot = await capture(page, `${label}-failure`).catch(() => "");
  const file = path.join(ARTIFACT_DIR, `${safeFileName(label)}-failure.json`);
  fs.writeFileSync(file, JSON.stringify({ error: error && error.message, details: error && error.details || {}, screenshot, state }, null, 2));
  return file;
}

async function assertCleanPage(page, label) {
  const state = await pageState(page);
  if (state.modalCount || FORBIDDEN_TEXT_RE.test(state.bodyText) || FORBIDDEN_TEXT_RE.test(state.modalText) || NATIVE_ROUTE_RE.test(state.url)) {
    await capture(page, `${label}-unexpected-state`);
  }
  assert(state.modalCount === 0, "Framework modal must not be visible", state);
  assert(!FORBIDDEN_TEXT_RE.test(state.bodyText), "Forbidden/native/framework text leaked", state);
  assert(!FORBIDDEN_TEXT_RE.test(state.modalText), "Forbidden/native/framework modal leaked", state);
  assert(!NATIVE_ROUTE_RE.test(state.url), "Native route leaked", state);
  assert(state.scrollWidth <= state.clientWidth + 2, "Page has horizontal overflow", state);
  assert(!/\?\s+[^\s]/.test(state.readinessSourceText), "Readiness source separator must not render as question mark", state);
}

async function login(page, user) {
  await page.goto(routeUrl("/login"), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  await page.locator("#login_email, input[name='usr'], input[type='email'], input[type='text']").first().fill(user.username);
  await page.locator("#login_password, input[name='pwd'], input[type='password']").first().fill(user.password);
  await Promise.all([
    page.waitForURL(/\/(?:app|desk)(?:[/?#]|$)/, { waitUntil: "domcontentloaded", timeout: TIMEOUT }),
    page.locator("button:has-text('Login'), button.btn-login, .btn-login").first().click(),
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

async function callMethod(page, method, args) {
  return page.evaluate(async ({ method, args }) => {
    const response = await frappe.call({ method, args: args || {} });
    return response && response.message;
  }, { method, args });
}

async function getWorklist(page, queueKey, filters) {
  return callMethod(page, "erp_workspace_ui.procurement_console.worklist.get_procurement_console_worklist_context", { queue_key: queueKey, filters: filters || {} });
}

function cellValue(row, key) {
  const cell = row && row.cells ? row.cells[key] : null;
  if (cell && typeof cell === "object") return String(cell.value || cell.label || "");
  return String(cell || "");
}

function rowName(row) {
  return String(row && (row.name || row.key) || "");
}

async function pickFixtures(page) {
  const supplierContext = await getWorklist(page, "supplier_directory", {});
  const supplierRows = supplierContext && supplierContext.results && Array.isArray(supplierContext.results.rows) ? supplierContext.results.rows : [];
  const supplier = supplierRows.find((row) => cellValue(row, "readiness") === "Known trading record");
  const newSupplier = supplierRows.find((row) => cellValue(row, "readiness") === "New supplier - review needed") || null;

  const itemContext = await getWorklist(page, "buying_item_directory", {});
  const itemRows = itemContext && itemContext.results && Array.isArray(itemContext.results.rows) ? itemContext.results.rows : [];
  const item = itemRows.find((row) => ["Existing buying activity", "Catalog evidence found"].includes(cellValue(row, "readiness")));
  const newItem = itemRows.find((row) => cellValue(row, "readiness") === "New item - review needed") || null;

  const fallback = await page.evaluate(async () => {
    const pick = async (doctype, filters, fields) => {
      const result = await frappe.call({ method: "frappe.client.get_list", args: { doctype, filters: filters || {}, fields, limit_page_length: 1 } });
      return (result.message || [])[0] || null;
    };
    return {
      rfq: await pick("Request for Quotation", {}, ["name"]),
      autocompleteSupplier: await pick("Supplier", { disabled: 0 }, ["name", "supplier_name"]),
      autocompleteItem: await pick("Item", { is_purchase_item: 1, disabled: 0 }, ["name", "item_name"]),
      warehouse: await pick("Warehouse", {}, ["name"]).catch(() => null),
    };
  });

  assert(supplier, "No historical supplier with inferred Known trading record was found", { supplierRows: supplierRows.slice(0, 10).map((row) => ({ name: rowName(row), readiness: cellValue(row, "readiness") })) });
  assert(item, "No historical/catalog buying item with inferred evidence label was found", { itemRows: itemRows.slice(0, 10).map((row) => ({ name: rowName(row), readiness: cellValue(row, "readiness") })) });
  assert(fallback.rfq && fallback.rfq.name, "No RFQ fixture available", fallback);
  assert(fallback.autocompleteSupplier && fallback.autocompleteSupplier.name, "No supplier fixture available for RFQ autocomplete", fallback);
  assert(fallback.autocompleteItem && fallback.autocompleteItem.name, "No item fixture available for RFQ autocomplete", fallback);

  return {
    supplier: { name: rowName(supplier), label: cellValue(supplier, "supplier"), readiness: cellValue(supplier, "readiness") },
    newSupplier: newSupplier ? { name: rowName(newSupplier), label: cellValue(newSupplier, "supplier"), readiness: cellValue(newSupplier, "readiness") } : null,
    item: { name: rowName(item), label: cellValue(item, "item"), readiness: cellValue(item, "readiness") },
    newItem: newItem ? { name: rowName(newItem), label: cellValue(newItem, "item"), readiness: cellValue(newItem, "readiness") } : null,
    rfqName: fallback.rfq.name,
    autocomplete: fallback,
  };
}

async function assertDirectoryLabel(page, userKey, queueSlug, expectedLabel, label) {
  await page.setViewportSize({ width: 1440, height: 900 });
  await openDeskRoute(page, `/desk/procurement-console-worklist/${queueSlug}`);
  await page.waitForFunction((text) => (document.body.innerText || "").includes(text), expectedLabel, { timeout: TIMEOUT });
  const state = await pageState(page);
  assert(state.bodyText.includes(expectedLabel), `${label} directory label missing`, state);
  await assertCleanPage(page, `${userKey}-${label}-directory`);
  await capture(page, `${userKey}-${label}-directory`);
}

async function assertOverview(page, user, fixtures) {
  await page.setViewportSize({ width: 1440, height: 900 });
  await openDeskRoute(page, "/desk/procurement-console");
  await page.waitForFunction(() => /Procurement Console/i.test(document.body.innerText || ""), null, { timeout: TIMEOUT });
  const state = await pageState(page);
  if (user.key === "manager") {
    assert(state.managerReadinessCards === 1, "Purchase Manager overview must show Readiness Review Queue", state);
    const queueText = String(state.managerReadinessText || "");
    assert(!queueText.includes(fixtures.supplier.name), "Historical supplier must not appear as manager exception", { queueText, fixture: fixtures.supplier });
    assert(!queueText.includes(fixtures.item.name), "Historical item must not appear as manager exception", { queueText, fixture: fixtures.item });
    assert(!/Known trading record|Existing buying activity|Catalog evidence found/i.test(queueText), "Inferred history labels should not be queued as exceptions", { queueText });
    if (fixtures.newSupplier || fixtures.newItem) {
      assert(/New supplier - review needed|New item - review needed|Hold for sourcing/i.test(queueText), "Manager queue did not show available real exceptions", { queueText, newSupplier: fixtures.newSupplier, newItem: fixtures.newItem });
    }
  } else {
    assert(state.managerReadinessCards === 0, "Purchase User overview must not show Readiness Review Queue", state);
    assert(!/Readiness Review Queue/i.test(state.bodyText), "Purchase User saw manager readiness heading", state);
  }
  await assertCleanPage(page, `${user.key}-overview`);
  await capture(page, `${user.key}-overview`);
}

async function assertSupplierDetail(page, userKey, supplier) {
  await page.setViewportSize({ width: 1136, height: 768 });
  await openDeskRoute(page, `/desk/procurement-console-supplier/${encodeURIComponent(supplier.name)}`);
  await page.waitForSelector("[data-erpw-supplier-readiness-card]", { state: "visible", timeout: TIMEOUT });
  await page.waitForFunction((label) => (document.body.innerText || "").includes(label), supplier.readiness, { timeout: TIMEOUT });
  const state = await pageState(page);
  assert(state.bodyText.includes("Supplier Buying Profile"), "Supplier Buying Profile card missing", state);
  assert(state.bodyText.includes("Known trading record"), "Historical supplier inferred label missing on detail", state);
  assert(!/No profile\s+(warning|review|issue)/i.test(state.bodyText), "Supplier detail leaked fake no-profile warning", state);
  await assertCleanPage(page, `${userKey}-supplier-detail`);
  await capture(page, `${userKey}-supplier-detail-known-trading-record`);
}

async function assertItemDetail(page, userKey, item) {
  await page.setViewportSize({ width: 1136, height: 768 });
  await openDeskRoute(page, `/desk/procurement-console-item/${encodeURIComponent(item.name)}`);
  await page.waitForSelector("[data-erpw-item-buying-profile-card]", { state: "visible", timeout: TIMEOUT });
  await page.waitForFunction((label) => (document.body.innerText || "").includes(label), item.readiness, { timeout: TIMEOUT });
  const state = await pageState(page);
  assert(state.bodyText.includes("Buying Procurement Context"), "Buying Procurement Context card missing", state);
  assert(/Existing buying activity|Catalog evidence found/.test(state.bodyText), "Historical/catalog item inferred label missing on detail", state);
  assert(!/Not reviewed\s+(warning|issue)/i.test(state.bodyText), "Buying item detail leaked fake not-reviewed warning", state);
  await assertCleanPage(page, `${userKey}-item-detail`);
  await capture(page, `${userKey}-item-detail-inferred-buying`);
}

async function assertRfqCommunication(page, userKey, rfqName) {
  await page.setViewportSize({ width: 1136, height: 768 });
  await openDeskRoute(page, `/desk/procurement-console-rfq-review/${encodeURIComponent(rfqName)}`);
  await page.waitForSelector("[data-rfq-review-output-card]", { state: "visible", timeout: TIMEOUT });
  await page.waitForSelector("[data-rfq-readiness-panel]", { state: "visible", timeout: TIMEOUT });
  const state = await pageState(page);
  assert(/Supplier Communication/i.test(state.bodyText), "RFQ Supplier Communication missing", state);
  assert(/Preview RFQ/i.test(state.actionText), "Preview RFQ action missing", state);
  assert(/Download RFQ PDF/i.test(state.actionText), "Download RFQ PDF action missing", state);
  assert(/Send RFQ/i.test(state.bodyText), "Disabled Send RFQ label missing", state);
  assert(await page.locator("[data-rfq-send-disabled]").count() >= 1, "Send RFQ must remain disabled", state);
  assert(!/Email suppliers|Get PDF|Print/i.test(state.actionText), "Native email/print leakage", state);
  await assertCleanPage(page, `${userKey}-rfq-review`);
  await capture(page, `${userKey}-rfq-review-communication`);
}

async function clearOrphanedModalBackdrops(page) {
  const state = await page.evaluate(() => {
    const visible = (node) => {
      if (!node) return false;
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
    };
    const visibleModals = Array.from(document.querySelectorAll(".modal.show")).filter(visible);
    const backdrops = Array.from(document.querySelectorAll(".modal-backdrop"));
    if (!visibleModals.length && backdrops.length) {
      backdrops.forEach((node) => node.remove());
      document.body.classList.remove("modal-open");
      document.body.style.removeProperty("padding-right");
    }
    return { visibleModalCount: visibleModals.length, backdropCount: backdrops.length };
  });
  assert(state.visibleModalCount === 0, "Visible modal must not be present before autocomplete", state);
}

async function openNewRfqForm(page) {
  await openDeskRoute(page, "/desk/procurement-console-rfq-form/new");
  await page.waitForSelector(".erpw-managed-rfq-page [data-erpw-managed-rfq-form]", { state: "visible", timeout: TIMEOUT });
  await clearOrphanedModalBackdrops(page);
}

function shortQuery(value) {
  const text = String(value || "").trim();
  if (!text) return "a";
  return text.slice(0, Math.min(4, text.length));
}

async function clearRfqSuggestions(page) {
  await page.evaluate(() => document.querySelectorAll(".erpw-managed-rfq-suggestions").forEach((node) => node.remove()));
}

async function assertAutocomplete(page, userKey, kind, selector, query, viewport) {
  await page.setViewportSize(viewport);
  await openNewRfqForm(page);
  await clearRfqSuggestions(page);
  const input = page.locator(selector).first();
  await input.waitFor({ state: "visible", timeout: TIMEOUT });
  await input.click();
  await input.fill("");
  await input.type(query || "a", { delay: 12 });
  await page.waitForSelector(".erpw-managed-rfq-suggestions", { state: "visible", timeout: TIMEOUT });
  await page.waitForTimeout(120);
  const metrics = await page.evaluate((selector) => {
    const visible = (node) => {
      if (!node) return false;
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
    };
    const input = document.querySelector(selector);
    const menu = document.querySelector(".erpw-managed-rfq-suggestions");
    const protectedNodes = Array.from(document.querySelectorAll(".erpw-child-actions-toolbar, .erpw-child-toolbar-actions, .page-head")).filter(visible);
    const protectedBottom = protectedNodes.reduce((bottom, node) => Math.max(bottom, node.getBoundingClientRect().bottom + 8), 12);
    const inputRect = input ? input.getBoundingClientRect() : null;
    const menuRect = menu ? menu.getBoundingClientRect() : null;
    return {
      input: inputRect ? { left: inputRect.left, right: inputRect.right, top: inputRect.top, bottom: inputRect.bottom, width: inputRect.width } : null,
      menu: menuRect ? { left: menuRect.left, right: menuRect.right, top: menuRect.top, bottom: menuRect.bottom, width: menuRect.width, height: menuRect.height } : null,
      protectedBottom,
      bodyWidth: Math.ceil(Math.max(document.body.scrollWidth, document.documentElement.scrollWidth)),
      viewportWidth: window.innerWidth,
      viewportHeight: window.innerHeight,
      suggestionCount: menu ? menu.querySelectorAll(".erpw-managed-rfq-suggestion").length : 0,
      overflowY: menu ? window.getComputedStyle(menu).overflowY : "",
    };
  }, selector);
  assert(metrics.input && metrics.menu, `${kind} autocomplete geometry missing`, metrics);
  assert(metrics.suggestionCount > 0, `${kind} autocomplete suggestions missing`, metrics);
  assert(metrics.menu.top >= metrics.input.bottom - 3, `${kind} autocomplete should open below the active input when below-space is usable`, metrics);
  assert(metrics.menu.top >= metrics.protectedBottom - 2, `${kind} autocomplete must not cover toolbar/header`, metrics);
  assert(metrics.menu.right <= metrics.viewportWidth + 2, `${kind} autocomplete must not overflow viewport horizontally`, metrics);
  assert(metrics.menu.bottom <= metrics.viewportHeight + 2, `${kind} autocomplete must stay inside viewport with capped height`, metrics);
  assert(metrics.bodyWidth <= metrics.viewportWidth + 2, `${kind} autocomplete caused horizontal overflow`, metrics);
  assert(/auto|scroll/i.test(metrics.overflowY), `${kind} autocomplete must remain internally scrollable`, metrics);
  await assertCleanPage(page, `${userKey}-new-rfq-${kind}-autocomplete-${viewport.width}`);
  await capture(page, `${userKey}-new-rfq-${kind}-autocomplete-${viewport.width}`);
  await clearRfqSuggestions(page);
}

async function assertAutocompletePlacement(page, userKey, fixtures) {
  const values = fixtures.autocomplete;
  const supplierQuery = shortQuery(values.autocompleteSupplier.name || values.autocompleteSupplier.supplier_name);
  const itemQuery = shortQuery(values.autocompleteItem.name || values.autocompleteItem.item_name);
  const warehouseQuery = shortQuery((values.warehouse && values.warehouse.name) || "warehouse");
  const viewports = [{ width: 1136, height: 768 }, { width: 1440, height: 900 }];
  for (const viewport of viewports) {
    await assertAutocomplete(page, userKey, "supplier", '[data-supplier-field="supplier"]', supplierQuery, viewport);
    await assertAutocomplete(page, userKey, "item", '[data-row-field="item_code"]', itemQuery, viewport);
    await assertAutocomplete(page, userKey, "warehouse", '[data-row-field="warehouse"]', warehouseQuery, viewport);
  }
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
    const fixtures = await pickFixtures(page);
    await assertDirectoryLabel(page, user.key, "supplier-directory", "Known trading record", "supplier");
    await assertDirectoryLabel(page, user.key, "buying-item-directory", fixtures.item.readiness, "item");
    await assertOverview(page, user, fixtures);
    await assertSupplierDetail(page, user.key, fixtures.supplier);
    await assertItemDetail(page, user.key, fixtures.item);
    await assertRfqCommunication(page, user.key, fixtures.rfqName);
    await assertAutocompletePlacement(page, user.key, fixtures);
    return { user: user.key, status: "pass", supplier: fixtures.supplier, item: fixtures.item, newSupplier: fixtures.newSupplier, newItem: fixtures.newItem };
  } catch (error) {
    await captureDiagnostics(page, user.key, error);
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
    results.push(await runForUser(user));
  }
  fs.writeFileSync(path.join(ARTIFACT_DIR, "phase7h1-summary.json"), JSON.stringify({ status: "pass", results }, null, 2));
  console.log(`Phase 7H1 smoke passed. Artifacts: ${ARTIFACT_DIR}`);
})().catch((error) => {
  fs.writeFileSync(path.join(ARTIFACT_DIR, "phase7h1-summary.json"), JSON.stringify({ status: "fail", error: error.message, details: error.details || {} }, null, 2));
  console.error(error);
  process.exit(1);
});