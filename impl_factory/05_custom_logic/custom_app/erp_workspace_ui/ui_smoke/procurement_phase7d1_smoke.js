const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const TIMEOUT = Number(process.env.ERPW_PROCUREMENT_SMOKE_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_PROCUREMENT_PHASE7D1_ARTIFACT_DIR || path.join(__dirname, "artifacts", "procurement-phase7d1");
const SESSION_FILE = process.env.ERPW_PHASE7D1_SESSION_FILE || "";
fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

const sessionMap = SESSION_FILE && fs.existsSync(SESSION_FILE) ? JSON.parse(fs.readFileSync(SESSION_FILE, "utf8")) : {};
const USERS = [
  {
    key: "manager",
    label: "Purchase Manager",
    username: process.env.ERPW_PURCHASE_MANAGER_USERNAME || process.env.ERPW_MANAGER_USERNAME || (sessionMap.manager || {}).username,
    password: process.env.ERPW_PURCHASE_MANAGER_PASSWORD || process.env.ERPW_MANAGER_PASSWORD,
    sid: (sessionMap.manager || {}).sid,
  },
  {
    key: "user",
    label: "Purchase User",
    username: process.env.ERPW_PURCHASE_USER_USERNAME || process.env.ERPW_USER_USERNAME || (sessionMap.user || {}).username,
    password: process.env.ERPW_PURCHASE_USER_PASSWORD || process.env.ERPW_USER_PASSWORD,
    sid: (sessionMap.user || {}).sid,
  },
].filter((user) => user.username && (user.password || user.sid));

const NATIVE_LABEL_RE = /Open ERP Form|Open ERP Supplier Form|Open ERP Item Form|Advanced ERP Form/i;
const RAW_NATIVE_ROUTE_RE = /\/desk\/Form\/|\/app\//i;
const OUTPUT_PDF_METHOD = "erp_workspace_ui.procurement_console.document_output.download_document_pdf";

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
  if (user.sid) {
    const host = new URL(BASE_URL).hostname;
    await page.context().addCookies([{ name: "sid", value: user.sid, domain: host, path: "/", secure: true, httpOnly: false, sameSite: "Lax" }]);
    await page.goto(routeUrl("/desk"), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
    if (/\/login(?:[/?#]|$)/.test(page.url())) throw new Error(`Session login failed for ${user.key}`);
    await page.waitForFunction(() => Boolean(window.frappe), null, { timeout: TIMEOUT });
    return;
  }
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
    try {
      const response = await frappe.call({ method, args });
      return { ok: true, message: response.message, response };
    } catch (error) {
      return { ok: false, message: error.message || String(error), error: { message: error.message, exc: error.exc } };
    }
  }, { method, args });
}

async function assertNoNativeEscape(page, label) {
  const state = await page.evaluate(() => {
    const visible = (node) => {
      if (!node) return false;
      const style = window.getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
    };
    const text = (document.body.innerText || "").replace(/\s+/g, " ").trim();
    const actions = Array.from(document.querySelectorAll("button, a, [role='button']"))
      .filter(visible)
      .map((node) => ({ text: (node.textContent || "").replace(/\s+/g, " ").trim(), href: node.getAttribute("href") || "", route: node.getAttribute("data-route") || "" }));
    return {
      url: location.href,
      route: window.frappe && typeof frappe.get_route === "function" ? frappe.get_route() : null,
      text,
      actions,
      modalText: Array.from(document.querySelectorAll(".modal.show")).filter(visible).map((node) => (node.innerText || "").replace(/\s+/g, " ").trim()).join(" "),
    };
  });
  if (NATIVE_LABEL_RE.test(state.text) || RAW_NATIVE_ROUTE_RE.test(state.url) || /Internal Server Error|Traceback|Server Error/i.test(state.modalText)) {
    await capture(page, `${label}-native-leakage-failure`);
  }
  assert(!NATIVE_LABEL_RE.test(state.text), `${label}: native ERP form escape label is visible`, state);
  assert(!RAW_NATIVE_ROUTE_RE.test(state.url), `${label}: current URL leaked to raw native route`, state);
  assert(!state.actions.some((action) => NATIVE_LABEL_RE.test(action.text)), `${label}: action list exposes native ERP form escape`, state);
  assert(!state.actions.some((action) => RAW_NATIVE_ROUTE_RE.test(action.href) || RAW_NATIVE_ROUTE_RE.test(action.route)), `${label}: visible action links to raw native route`, state);
  assert(!/Internal Server Error|Traceback|Server Error/i.test(state.modalText), `${label}: framework error modal visible`, state);
  return state;
}

function assertContextHasNoNativeEscape(payload, label) {
  const text = JSON.stringify(payload || {});
  assert(!/open_erp_form|open_supplier_form|open_item_form|advanced_erp_form/i.test(text), `${label}: context exposes native action key`, payload);
  assert(!NATIVE_LABEL_RE.test(text), `${label}: context exposes native label`, payload);
  const targets = (payload || {}).action_targets || {};
  for (const [key, target] of Object.entries(targets)) {
    assert((target || {}).kind !== "form", `${label}: context exposes raw form target ${key}`, target);
  }
}

async function getFirst(page, doctype, fields, filters = []) {
  const result = await page.evaluate(async ({ doctype, fields, filters }) => {
    const response = await frappe.call({ method: "frappe.client.get_list", args: { doctype, fields, filters, limit_page_length: 1, order_by: "modified desc" } });
    return (response.message || [])[0] || null;
  }, { doctype, fields, filters });
  assert(result && result.name, `No ${doctype} fixture was available`, { doctype, filters });
  return result;
}

async function fixtures(page) {
  const supplier = await getFirst(page, "Supplier", ["name", "supplier_name"]);
  const item = await getFirst(page, "Item", ["name", "item_name"], [["Item", "is_purchase_item", "=", 1]]);
  const warehouse = await getFirst(page, "Warehouse", ["name"], [["Warehouse", "is_group", "=", 0]]).catch(() => ({ name: "" }));
  return { supplier: supplier.name, item: item.name, warehouse: warehouse.name || "" };
}

async function saveDraft(page, method, payload, label) {
  const response = await callMethod(page, method, { payload });
  assert(response.ok, `${label}: save method failed`, response);
  const message = response.message || {};
  assert((message.state || {}).kind === "ready", `${label}: save did not return ready state`, message);
  return message;
}

async function createDrafts(page, values) {
  const today = "2026-05-17";
  const schedule = "2026-06-01";
  const pr = await saveDraft(page, "erp_workspace_ui.procurement_console.managed_purchase_request.save_managed_purchase_request_draft", {
    header: { transaction_date: today, schedule_date: schedule, material_request_type: "Purchase" },
    items: [{ item_code: values.item, qty: 1, schedule_date: schedule, warehouse: values.warehouse }],
  }, "Purchase Request");
  const rfq = await saveDraft(page, "erp_workspace_ui.procurement_console.managed_rfq.save_managed_rfq_draft", {
    header: { transaction_date: today, schedule_date: schedule, subject: "Phase 7D1 Native Escape Audit" },
    suppliers: [{ supplier: values.supplier }],
    items: [{ item_code: values.item, qty: 1, schedule_date: schedule, warehouse: values.warehouse }],
  }, "RFQ");
  const sq = await saveDraft(page, "erp_workspace_ui.procurement_console.managed_supplier_quotation.save_managed_supplier_quotation_draft", {
    header: { supplier: values.supplier, transaction_date: today, valid_till: schedule },
    items: [{ item_code: values.item, qty: 1, rate: 100 }],
  }, "Supplier Quotation");
  const po = await saveDraft(page, "erp_workspace_ui.procurement_console.managed_purchase_order.save_managed_purchase_order", {
    header: { supplier: values.supplier, transaction_date: today, schedule_date: schedule, set_warehouse: values.warehouse },
    items: [{ item_code: values.item, qty: 1, rate: 100, schedule_date: schedule, warehouse: values.warehouse }],
  }, "Purchase Order");
  return {
    pr: ((pr.form || {}).name) || (pr.route || "").split("/").pop(),
    rfq: ((rfq.form || {}).name) || (rfq.route || "").split("/").pop(),
    sq: ((sq.form || {}).name) || (sq.route || "").split("/").pop(),
    po: ((po.form || {}).name) || (po.route || "").split("/").pop(),
  };
}

async function assertRouteClean(page, route, selector, label, expectedTexts = []) {
  await openDeskRoute(page, route);
  await page.locator(selector).first().waitFor({ state: "visible", timeout: TIMEOUT });
  await capture(page, label);
  const state = await assertNoNativeEscape(page, label);
  for (const expected of expectedTexts) {
    assert(new RegExp(expected, "i").test(state.text || ""), `${label}: expected productized text missing: ${expected}`, state);
  }
  return state;
}

async function assertPdfEndpoint(page, doctype, name, supplier, expectedFilePart, label) {
  const params = new URLSearchParams({ doctype, name });
  if (supplier) params.set("supplier", supplier);
  const url = routeUrl(`/api/method/${OUTPUT_PDF_METHOD}?${params.toString()}`);
  const response = await page.context().request.get(url);
  const body = await response.body().catch(() => Buffer.alloc(0));
  const text = response.ok() ? "" : await response.text().catch(() => "");
  const disposition = response.headers()["content-disposition"] || "";
  assert(response.ok(), `${label}: productized PDF endpoint failed`, { url, status: response.status(), text });
  assert(disposition.includes(name), `${label}: PDF filename missing document name`, { disposition, name });
  assert(disposition.includes(expectedFilePart), `${label}: PDF filename missing expected fragment`, { disposition, expectedFilePart });
  assert(body.length > 500, `${label}: PDF response body is unexpectedly small`, { length: body.length, disposition });
}

async function assertProductizedPreview(page, buttonText, label, expectedText) {
  await page.locator(`button:has-text('${buttonText}')`).first().click();
  await page.locator(".erpw-output-modal-backdrop").first().waitFor({ state: "visible", timeout: TIMEOUT });
  const modalText = await page.locator(".erpw-output-modal-backdrop").first().innerText({ timeout: TIMEOUT });
  assert(new RegExp(expectedText, "i").test(modalText), `${label}: expected preview text missing`, { modalText });
  assert(!/\bPrint\b|Get PDF/i.test(modalText), `${label}: native print controls leaked into productized preview`, { modalText });
  await capture(page, `${label}-preview`);
  await page.locator(".erpw-output-modal-close").first().click({ force: true }).catch(() => {});
  await page.locator(".erpw-output-modal-backdrop").waitFor({ state: "detached", timeout: 5000 }).catch(() => {});
}

async function runForUser(browser, user) {
  const context = await browser.newContext({ viewport: { width: 1136, height: 768 }, ignoreHTTPSErrors: true });
  const page = await context.newPage();
  try {
    await login(page, user);
    const values = await fixtures(page);
    const docs = await createDrafts(page, values);

    const contextChecks = [
      ["erp_workspace_ui.procurement_console.supplier_detail.get_supplier_detail_context", { supplier: values.supplier }, "Supplier Detail context"],
      ["erp_workspace_ui.procurement_console.items.get_item_detail_context", { item: values.item }, "Item Detail context"],
      ["erp_workspace_ui.procurement_console.document_reviews.get_purchase_request_review_context", { material_request: docs.pr }, "PR Review context"],
      ["erp_workspace_ui.procurement_console.document_reviews.get_rfq_review_context", { request_for_quotation: docs.rfq }, "RFQ Review context"],
      ["erp_workspace_ui.procurement_console.document_reviews.get_supplier_quotation_review_context", { supplier_quotation: docs.sq }, "SQ Review context"],
      ["erp_workspace_ui.procurement_console.managed_purchase_request.get_managed_purchase_request_context", { name: docs.pr }, "Managed PR context"],
      ["erp_workspace_ui.procurement_console.managed_rfq.get_managed_rfq_context", { name: docs.rfq }, "Managed RFQ context"],
      ["erp_workspace_ui.procurement_console.managed_supplier_quotation.get_managed_supplier_quotation_context", { name: docs.sq }, "Managed SQ context"],
      ["erp_workspace_ui.procurement_console.managed_purchase_order.get_managed_purchase_order_context", { name: docs.po }, "Managed PO context"],
    ];
    for (const [method, args, label] of contextChecks) {
      const response = await callMethod(page, method, args);
      assert(response.ok, `${label}: API failed`, response);
      assertContextHasNoNativeEscape(response.message, `${user.key} ${label}`);
    }

    await assertRouteClean(page, `/desk/procurement-console-supplier/${encodeURIComponent(values.supplier)}`, ".erpw-procurement-supplier-detail-shell", `${user.key}-supplier-detail`, ["Supplier"]);
    await assertRouteClean(page, `/desk/procurement-console-item/${encodeURIComponent(values.item)}`, ".erpw-procurement-item-detail-shell", `${user.key}-item-detail`, ["Buying Item|Item Detail"]);
    await assertRouteClean(page, `/desk/procurement-console-purchase-request-review/${encodeURIComponent(docs.pr)}`, ".erpw-procurement-purchase-request-review-shell", `${user.key}-purchase-request-review`, ["Purchase Request"]);
    await assertRouteClean(page, `/desk/procurement-console-rfq-review/${encodeURIComponent(docs.rfq)}`, ".erpw-procurement-rfq-review-shell", `${user.key}-rfq-review`, ["Supplier Communication", "Preview RFQ", "Download RFQ PDF", "Send RFQ"]);
    await assertProductizedPreview(page, "Preview RFQ", `${user.key}-rfq-review`, "Draft / Not sent");
    await assertPdfEndpoint(page, "Request for Quotation", docs.rfq, values.supplier, "DRAFT-NOT-SENT", `${user.key} RFQ`);
    await assertRouteClean(page, `/desk/procurement-console-supplier-quotation-review/${encodeURIComponent(docs.sq)}`, ".erpw-procurement-supplier-quotation-review-shell", `${user.key}-supplier-quotation-review`, ["Supplier Quotation"]);

    await assertRouteClean(page, `/desk/procurement-console-purchase-request-form/${encodeURIComponent(docs.pr)}`, ".erpw-managed-pr-page", `${user.key}-managed-pr-saved`, ["Review Request"]);
    await assertRouteClean(page, `/desk/procurement-console-rfq-form/${encodeURIComponent(docs.rfq)}`, ".erpw-managed-rfq-page", `${user.key}-managed-rfq-saved`, ["Supplier Communication", "Preview RFQ", "Download RFQ PDF", "Send RFQ"]);
    const sendButton = page.locator("button:has-text('Send RFQ')").first();
    await sendButton.waitFor({ state: "visible", timeout: TIMEOUT });
    assert(await sendButton.isDisabled(), `${user.key}: Send RFQ must remain disabled`, { route: page.url() });
    await assertRouteClean(page, `/desk/procurement-console-supplier-quotation-form/${encodeURIComponent(docs.sq)}`, ".erpw-managed-sq-page", `${user.key}-managed-sq-saved`, ["Review Quotation"]);
    await assertRouteClean(page, `/desk/procurement-console-purchase-order-form/${encodeURIComponent(docs.po)}`, ".erpw-managed-po-page", `${user.key}-managed-po-saved`, ["Document Output", "Preview Purchase Order", "Download PO PDF", "Review Purchase Order"]);
    await assertProductizedPreview(page, "Preview Purchase Order", `${user.key}-managed-po`, "Draft / Not for supplier");
    await assertPdfEndpoint(page, "Purchase Order", docs.po, null, "DRAFT-NOT-FOR-SUPPLIER", `${user.key} PO`);

    return { user: user.key, docs, supplier: values.supplier, item: values.item };
  } finally {
    await context.close();
  }
}

(async () => {
  assert(USERS.length >= 2, "Both Purchase Manager and Purchase User credentials or sessions are required", { users: USERS.map((user) => user.key) });
  const browser = await chromium.launch({ headless: true });
  const results = [];
  try {
    for (const user of USERS) {
      results.push(await runForUser(browser, user));
    }
    const summaryPath = path.join(ARTIFACT_DIR, "summary.json");
    fs.writeFileSync(summaryPath, JSON.stringify({ ok: true, results }, null, 2));
    console.log(JSON.stringify({ ok: true, artifactDir: ARTIFACT_DIR, results }, null, 2));
  } catch (error) {
    const summaryPath = path.join(ARTIFACT_DIR, "summary.json");
    fs.writeFileSync(summaryPath, JSON.stringify({ ok: false, message: error.message, details: error.details || {}, stack: error.stack }, null, 2));
    console.error(JSON.stringify({ ok: false, message: error.message, details: error.details || {}, artifactDir: ARTIFACT_DIR }, null, 2));
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
})();
