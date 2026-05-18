const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const TIMEOUT = Number(process.env.ERPW_PROCUREMENT_SMOKE_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_PROCUREMENT_PHASE7F_ARTIFACT_DIR || process.env.ERPW_PROCUREMENT_ARTIFACT_DIR || path.join(__dirname, "artifacts", "procurement-phase7f-search");
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

const EXPECTED_LABELS = {
  supplier_directory: "Search supplier or group",
  buying_item_directory: "Search item, name, or group",
  purchase_request_directory: "Search request, item, or warehouse",
  requests_to_source: "Search request, item, or warehouse",
  purchase_order_directory: "Search order, supplier, or item",
  purchase_orders_supplier_follow_up: "Search order, supplier, or item",
  rfq_directory: "Search RFQ, supplier, or item",
  supplier_quotation_directory: "Search quotation, supplier, or item",
};
const FORBIDDEN_LABELS = ["Open ERP Form", "Open ERP Supplier Form", "Open ERP Item Form", "Advanced ERP Form", ["Confirm", "test", "send"].join(" "), "Insufficient Permissions", "Internal Server Error", "Traceback", "native email", "Get PDF"];
const FORBIDDEN_RE = new RegExp(FORBIDDEN_LABELS.map((label) => label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|"), "i");

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

async function callMethod(page, method, args = {}) {
  return page.evaluate(async ({ method, args }) => {
    const response = await frappe.call({ method, args });
    return response && response.message !== undefined ? response.message : response;
  }, { method, args });
}

async function worklistPayload(page, queueKey, filters = {}) {
  return callMethod(page, "erp_workspace_ui.procurement_console.worklist.get_procurement_console_worklist_context", {
    queue_key: queueKey,
    filters,
  });
}

async function clientGetList(page, doctype, filters, fields) {
  return page.evaluate(async ({ doctype, filters, fields }) => {
    try {
      const response = await frappe.call({ method: "frappe.client.get_list", args: { doctype, filters, fields, limit_page_length: 20 } });
      return response.message || [];
    } catch (error) {
      return [];
    }
  }, { doctype, filters, fields });
}

function rows(payload) {
  return payload && payload.results && Array.isArray(payload.results.rows) ? payload.results.rows : [];
}

function rowNames(payload) {
  return rows(payload).map((row) => row.name || row.key).filter(Boolean);
}

function cellValue(row, key) {
  const cell = row && row.cells ? row.cells[key] : null;
  if (cell && typeof cell === "object") return cell.value || cell.meta || "";
  return cell || "";
}

function firstNonEmpty(...values) {
  return values.map((value) => String(value || "").trim()).find(Boolean) || "";
}

function sectionRows(context, titlePart) {
  const sections = context && context.detail && Array.isArray(context.detail.sections) ? context.detail.sections : [];
  const section = sections.find((candidate) => String(candidate.title || "").toLowerCase().includes(String(titlePart || "").toLowerCase()));
  return section && section.table && Array.isArray(section.table.rows) ? section.table.rows : [];
}

async function reviewContext(page, method, nameArg, name) {
  return callMethod(page, method, { [nameArg]: name });
}

async function assertQueueSearch(page, queueKey, keyword, expectedName) {
  const payload = await worklistPayload(page, queueKey, { keyword });
  const names = rowNames(payload);
  assert(names.includes(expectedName), `${queueKey} search did not include expected row`, { queueKey, keyword, expectedName, names, state: payload && payload.results && payload.results.state });
}

async function discoverSearchFixtures(page) {
  const fixtures = {};

  const supplierPayload = await worklistPayload(page, "supplier_directory");
  const supplierRow = rows(supplierPayload)[0];
  assert(supplierRow, "Supplier Directory has no rows to test search");
  fixtures.supplier = {
    name: supplierRow.name,
    supplierTerm: firstNonEmpty(cellValue(supplierRow, "supplier"), supplierRow.name),
    groupTerm: firstNonEmpty(cellValue(supplierRow, "group")),
  };

  const itemPayload = await worklistPayload(page, "buying_item_directory");
  const itemRow = rows(itemPayload)[0];
  assert(itemRow, "Buying Item Directory has no rows to test search");
  fixtures.item = {
    name: itemRow.name,
    itemTerm: firstNonEmpty(cellValue(itemRow, "item"), itemRow.name),
    groupTerm: firstNonEmpty(cellValue(itemRow, "group")),
  };

  const requestPayload = await worklistPayload(page, "purchase_request_directory");
  const requestRow = rows(requestPayload)[0];
  assert(requestRow, "Purchase Request Directory has no rows to test search");
  const requestItems = await clientGetList(page, "Material Request Item", { parent: requestRow.name }, ["item_code", "item_name", "warehouse"]);
  const requestItem = requestItems[0] || {};
  fixtures.request = {
    name: requestRow.name,
    idTerm: requestRow.name,
    itemTerm: firstNonEmpty(requestItem.item_name, requestItem.item_code),
    warehouseTerm: firstNonEmpty(requestItem.warehouse),
  };

  const poPayload = await worklistPayload(page, "purchase_order_directory");
  const poRow = rows(poPayload)[0];
  assert(poRow, "Purchase Order Directory has no rows to test search");
  const poItems = await clientGetList(page, "Purchase Order Item", { parent: poRow.name }, ["item_code", "item_name"]);
  const poItem = poItems[0] || {};
  fixtures.po = {
    name: poRow.name,
    idTerm: poRow.name,
    supplierTerm: firstNonEmpty(poRow.cells && poRow.cells.order && poRow.cells.order.meta, cellValue(poRow, "supplier")),
    itemTerm: firstNonEmpty(poItem.item_name, poItem.item_code),
  };

  const rfqPayload = await worklistPayload(page, "rfq_directory");
  const rfqRow = rows(rfqPayload)[0];
  assert(rfqRow, "RFQ Directory has no rows to test search");
  const rfqContext = await reviewContext(page, "erp_workspace_ui.procurement_console.document_reviews.get_rfq_review_context", "request_for_quotation", rfqRow.name);
  const rfqSupplierRow = sectionRows(rfqContext, "suppliers")[0] || {};
  const rfqItemRow = sectionRows(rfqContext, "items")[0] || {};
  fixtures.rfq = {
    name: rfqRow.name,
    idTerm: rfqRow.name,
    supplierTerm: firstNonEmpty(rfqSupplierRow.cells && rfqSupplierRow.cells.supplier && rfqSupplierRow.cells.supplier.value, rfqSupplierRow.cells && rfqSupplierRow.cells.supplier && rfqSupplierRow.cells.supplier.meta),
    itemTerm: firstNonEmpty(rfqItemRow.cells && rfqItemRow.cells.item && rfqItemRow.cells.item.meta, rfqItemRow.cells && rfqItemRow.cells.item && rfqItemRow.cells.item.value),
  };

  const sqPayload = await worklistPayload(page, "supplier_quotation_directory");
  const sqRow = rows(sqPayload)[0];
  assert(sqRow, "Supplier Quotation Directory has no rows to test search");
  const sqContext = await reviewContext(page, "erp_workspace_ui.procurement_console.document_reviews.get_supplier_quotation_review_context", "supplier_quotation", sqRow.name);
  const sqItemRow = sectionRows(sqContext, "items")[0] || {};
  fixtures.sq = {
    name: sqRow.name,
    idTerm: sqRow.name,
    supplierTerm: firstNonEmpty(sqRow.cells && sqRow.cells.quotation && sqRow.cells.quotation.meta),
    itemTerm: firstNonEmpty(sqItemRow.cells && sqItemRow.cells.item && sqItemRow.cells.item.meta, sqItemRow.cells && sqItemRow.cells.item && sqItemRow.cells.item.value),
  };

  return fixtures;
}

async function assertApiSearchSemantics(page) {
  const fixtures = await discoverSearchFixtures(page);
  const checks = [
    ["supplier_directory", fixtures.supplier.supplierTerm, fixtures.supplier.name, "supplier name"],
    ["supplier_directory", fixtures.supplier.groupTerm, fixtures.supplier.name, "supplier group"],
    ["buying_item_directory", fixtures.item.itemTerm, fixtures.item.name, "item name"],
    ["buying_item_directory", fixtures.item.groupTerm, fixtures.item.name, "item group"],
    ["purchase_request_directory", fixtures.request.idTerm, fixtures.request.name, "request ID"],
    ["purchase_request_directory", fixtures.request.itemTerm, fixtures.request.name, "request item"],
    ["purchase_request_directory", fixtures.request.warehouseTerm, fixtures.request.name, "request warehouse"],
    ["purchase_order_directory", fixtures.po.idTerm, fixtures.po.name, "order ID"],
    ["purchase_order_directory", fixtures.po.supplierTerm, fixtures.po.name, "order supplier"],
    ["purchase_order_directory", fixtures.po.itemTerm, fixtures.po.name, "order item"],
    ["rfq_directory", fixtures.rfq.idTerm, fixtures.rfq.name, "RFQ ID"],
    ["rfq_directory", fixtures.rfq.supplierTerm, fixtures.rfq.name, "RFQ supplier"],
    ["rfq_directory", fixtures.rfq.itemTerm, fixtures.rfq.name, "RFQ item"],
    ["supplier_quotation_directory", fixtures.sq.idTerm, fixtures.sq.name, "quotation ID"],
    ["supplier_quotation_directory", fixtures.sq.supplierTerm, fixtures.sq.name, "quotation supplier"],
    ["supplier_quotation_directory", fixtures.sq.itemTerm, fixtures.sq.name, "quotation item"],
  ];
  for (const [queueKey, keyword, expectedName, label] of checks) {
    assert(keyword, `Missing search term for ${label}`, { queueKey, expectedName, fixtures });
    await assertQueueSearch(page, queueKey, keyword, expectedName);
  }
  return fixtures;
}

async function assertCleanWorklistPage(page, label) {
  const state = await page.evaluate(() => {
    const visible = (node) => {
      if (!node) return false;
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
    };
    const bodyText = (document.body.innerText || "").replace(/\s+/g, " ").trim();
    return {
      url: location.href,
      bodyText,
      modalText: Array.from(document.querySelectorAll(".modal.show")).filter(visible).map((node) => (node.innerText || "").replace(/\s+/g, " ").trim()).join(" "),
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
      shellCount: document.querySelectorAll(".erpw-list-shell").length,
    };
  });
  if (FORBIDDEN_RE.test(state.bodyText) || FORBIDDEN_RE.test(state.modalText) || state.scrollWidth > state.clientWidth + 2) {
    await capture(page, `${label}-unexpected-state`);
  }
  assert(!FORBIDDEN_RE.test(state.bodyText), "Forbidden/native text leaked", state);
  assert(!FORBIDDEN_RE.test(state.modalText), "Framework modal leaked", state);
  assert(state.scrollWidth <= state.clientWidth + 2, "Worklist has horizontal overflow", state);
  assert(state.shellCount === 1, "Worklist shell should render once", state);
}

async function assertVisibleLabels(page, userKey) {
  const viewports = [
    { width: 1136, height: 768 },
    { width: 1240, height: 768 },
    { width: 1440, height: 900 },
  ];
  for (const viewport of viewports) {
    await page.setViewportSize(viewport);
    for (const [queueKey, label] of Object.entries(EXPECTED_LABELS)) {
      const routeKey = queueKey.replace(/_/g, "-");
      await openDeskRoute(page, `/desk/procurement-console-worklist/${routeKey}`);
      await page.waitForSelector(".erpw-list-shell", { state: "visible", timeout: TIMEOUT });
      await page.getByText(label, { exact: true }).first().waitFor({ state: "visible", timeout: TIMEOUT });
      await assertCleanWorklistPage(page, `${userKey}-${queueKey}-${viewport.width}`);
      if (["rfq_directory", "purchase_order_directory", "supplier_quotation_directory"].includes(queueKey)) {
        await capture(page, `${userKey}-${queueKey}-${viewport.width}`);
      }
    }
  }
}

async function assertApplySearch(page, queueKey, keyword, expectedName, shotName) {
  const routeKey = queueKey.replace(/_/g, "-");
  await openDeskRoute(page, `/desk/procurement-console-worklist/${routeKey}`);
  await page.waitForSelector(".erpw-list-shell", { state: "visible", timeout: TIMEOUT });
  const search = page.locator('[data-erpw-list-field-key="keyword"]').first();
  await search.waitFor({ state: "visible", timeout: TIMEOUT });
  await search.fill(keyword);
  await page.locator('[data-erpw-list-action-key="apply_filters"]').first().click();
  await page.waitForFunction((name) => (document.body.innerText || "").includes(name), expectedName, { timeout: TIMEOUT });
  await assertCleanWorklistPage(page, shotName);
  await capture(page, shotName);
}

async function runForUser(browser, user) {
  const page = await browser.newPage({ viewport: { width: 1136, height: 768 } });
  try {
    await login(page, user);
    const fixtures = user.key === "manager" ? await assertApiSearchSemantics(page) : null;
    await assertVisibleLabels(page, user.key);
    if (fixtures) {
      await assertApplySearch(page, "rfq_directory", fixtures.rfq.supplierTerm, fixtures.rfq.name, "manager-rfq-supplier-search-applied");
      await assertApplySearch(page, "purchase_order_directory", fixtures.po.itemTerm, fixtures.po.name, "manager-po-item-search-applied");
      await assertApplySearch(page, "supplier_quotation_directory", fixtures.sq.itemTerm, fixtures.sq.name, "manager-sq-item-search-applied");
    }
  } catch (error) {
    await capture(page, `${user.key}-failure`);
    throw error;
  } finally {
    await page.close();
  }
}

async function main() {
  assert(USERS.length > 0, "At least one Purchase user credential is required");
  const browser = await chromium.launch({ headless: process.env.ERPW_HEADLESS !== "0" });
  try {
    for (const user of USERS) await runForUser(browser, user);
  } finally {
    await browser.close();
  }
  const report = { ok: true, artifactDir: ARTIFACT_DIR, users: USERS.map((user) => user.key), labels: EXPECTED_LABELS };
  fs.writeFileSync(path.join(ARTIFACT_DIR, "procurement-phase7f-search-report.json"), JSON.stringify(report, null, 2));
  console.log(`Phase 7F search smoke passed. Artifacts: ${ARTIFACT_DIR}`);
}

main().catch((error) => {
  const report = { ok: false, message: error.message, details: error.details || null, stack: error.stack };
  fs.writeFileSync(path.join(ARTIFACT_DIR, "procurement-phase7f-search-report.json"), JSON.stringify(report, null, 2));
  console.error(error);
  process.exit(1);
});
