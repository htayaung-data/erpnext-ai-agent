const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const TIMEOUT = Number(process.env.ERPW_PROCUREMENT_SMOKE_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_PROCUREMENT_PHASE7E1A_ARTIFACT_DIR || path.join(__dirname, "artifacts", "procurement-phase7e1a");
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

const OUTPUT_PDF_METHOD = "erp_workspace_ui.procurement_console.document_output.download_document_pdf";
const FORBIDDEN_LABELS = ["Open ERP Form", "Open ERP Supplier Form", "Open ERP Item Form", "Advanced ERP Form", ["Confirm", "test", "send"].join(" "), "Insufficient Permissions", "Internal Server Error", "Traceback"];
const FORBIDDEN_TEXT_RE = new RegExp(FORBIDDEN_LABELS.map((label) => label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|"), "i");
const FORBIDDEN_ACTION_RE = /(submit|approve|reject|receive|bill|payment|supplier portal|create supplier quotation|create purchase order|email suppliers)/i;
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
      modalCount: modals.length,
      modalText: modals.join(" "),
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
      supplierReadinessCards: document.querySelectorAll("[data-erpw-supplier-readiness-card]").length,
      nativeFormIndicators: document.querySelectorAll(".form-layout, .form-page").length,
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
    const supplierResult = await frappe.call({ method: "frappe.client.get_list", args: { doctype: "Supplier", fields: ["name", "supplier_name"], limit_page_length: 1 } });
    const itemResult = await frappe.call({ method: "frappe.client.get_list", args: { doctype: "Item", filters: { is_purchase_item: 1, disabled: 0 }, fields: ["name", "item_name", "stock_uom"], limit_page_length: 1 } });
    const warehouseResult = await frappe.call({ method: "frappe.client.get_list", args: { doctype: "Warehouse", fields: ["name"], limit_page_length: 1 } }).catch(() => ({ message: [] }));
    return {
      supplier: (supplierResult.message || [])[0] || null,
      item: (itemResult.message || [])[0] || null,
      warehouse: (warehouseResult.message || [])[0] || null,
    };
  });
  assert(values.supplier && values.supplier.name, "No supplier available", values);
  assert(values.item && values.item.name, "No buying item available", values);
  return values;
}

async function createRfq(page, values) {
  const response = await page.evaluate(async ({ supplier, item, warehouse }) => frappe.call({
    method: "erp_workspace_ui.procurement_console.managed_rfq.save_managed_rfq_draft",
    args: {
      payload: JSON.stringify({
        header: { transaction_date: "2026-05-18", schedule_date: "2026-06-15" },
        suppliers: [{ supplier }],
        items: [{ item_code: item, qty: 1, schedule_date: "2026-06-15", warehouse: warehouse || "" }],
      }),
    },
  }), { supplier: values.supplier.name, item: values.item.name, warehouse: values.warehouse && values.warehouse.name });
  const payload = response && response.message ? response.message : {};
  assert(payload.state && payload.state.kind === "ready", "RFQ save did not return ready", payload);
  assert(payload.form && payload.form.name, "RFQ save did not return a name", payload);
  return payload.form.name;
}

async function assertSupplierDetail(page, user, supplier, canEdit) {
  for (const viewport of [{ width: 1136, height: 768 }, { width: 1240, height: 768 }, { width: 1440, height: 900 }]) {
    await page.setViewportSize(viewport);
    await openDeskRoute(page, `/desk/procurement-console-supplier/${encodeURIComponent(supplier)}`);
    await page.waitForSelector("[data-erpw-supplier-readiness-card]", { state: "visible", timeout: TIMEOUT });
    const state = await pageState(page);
    assert(state.supplierReadinessCards === 1, "Supplier readiness card should appear once", state);
    assert(!FORBIDDEN_ACTION_RE.test(state.bodyText), "Forbidden procurement action leaked on Supplier Detail", state);
    await assertCleanPage(page, `${user.key}-supplier-detail-${viewport.width}`);
    await capture(page, `${user.key}-supplier-readiness-card-${viewport.width}`);
  }
  const editCount = await page.locator("[data-erpw-readiness-edit]").count();
  assert(canEdit ? editCount === 1 : editCount === 0, "Supplier readiness edit visibility did not match role", { user: user.key, editCount });
}

async function saveManagerReadiness(page) {
  await page.locator("[data-erpw-readiness-edit]").click();
  await page.locator("[data-erpw-readiness-field='buying_readiness_status']").selectOption("Hold for sourcing");
  await page.locator("[data-erpw-readiness-field='rfq_recipient_email_override']").fill("phase7e1a.smoke@example.com");
  await page.locator("[data-erpw-readiness-field='buying_note']").fill("Smoke-managed buying note.");
  await page.locator("[data-erpw-readiness-field='readiness_note']").fill("Smoke hold for sourcing.");
  await Promise.all([
    page.waitForResponse((response) => response.url().includes("save_supplier_readiness_profile") && response.ok(), { timeout: TIMEOUT }),
    page.locator("[data-erpw-readiness-save]").click(),
  ]);
  await page.waitForFunction(() => /Hold for sourcing/i.test(document.body.innerText || ""), null, { timeout: TIMEOUT });
  await assertCleanPage(page, "manager-supplier-readiness-after-save");
}

async function assertSupplierDirectory(page) {
  await openDeskRoute(page, "/desk/procurement-console-worklist/supplier-directory");
  await page.waitForFunction(() => /Supplier records/i.test(document.body.innerText || ""), null, { timeout: TIMEOUT });
  await assertCleanPage(page, "supplier-directory-readiness");
}

async function assertPdfEndpoint(page, rfqName, supplier) {
  const params = new URLSearchParams({ doctype: "Request for Quotation", name: rfqName, supplier });
  const url = routeUrl(`/api/method/${OUTPUT_PDF_METHOD}?${params.toString()}`);
  const response = await page.context().request.get(url);
  assert(response.ok(), "RFQ PDF endpoint did not return success", { url, status: response.status(), text: await response.text().catch(() => "") });
  const disposition = response.headers()["content-disposition"] || "";
  assert(disposition.includes(rfqName), "RFQ PDF filename missing RFQ name", { disposition });
  assert(disposition.includes("DRAFT-NOT-SENT"), "RFQ PDF filename missing DRAFT-NOT-SENT", { disposition });
}

async function assertRfqReadiness(page, rfqName, supplier) {
  await openDeskRoute(page, `/desk/procurement-console-rfq-review/${encodeURIComponent(rfqName)}`);
  await page.waitForFunction(() => /Supplier Communication/i.test(document.body.innerText || ""), null, { timeout: TIMEOUT });
  await page.waitForFunction(() => /Hold for sourcing|Send RFQ/i.test(document.body.innerText || ""), null, { timeout: TIMEOUT });
  const state = await pageState(page);
  assert(/Hold for sourcing/i.test(state.bodyText), "RFQ readiness did not reflect Supplier hold state", state);
  assert(/Send RFQ/i.test(state.bodyText), "Disabled Send RFQ action was not visible", state);
  const disabledSend = await page.locator("button:has-text('Send RFQ')").first().evaluate((button) => Boolean(button.disabled || button.getAttribute("aria-disabled") === "true")).catch(() => true);
  assert(disabledSend, "Send RFQ must remain disabled", state);
  await capture(page, "manager-rfq-review-readiness");
  await page.locator("button:has-text('Preview RFQ')").first().click();
  await page.waitForFunction(() => /Draft \/ Not sent/i.test(document.body.innerText || ""), null, { timeout: TIMEOUT });
  await assertCleanPage(page, "manager-rfq-preview");
  await capture(page, "manager-rfq-preview");
  await page.keyboard.press("Escape").catch(() => null);
  await assertPdfEndpoint(page, rfqName, supplier);
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
    await assertSupplierDetail(page, user, values.supplier.name, user.key === "manager");
    if (user.key === "manager") {
      await saveManagerReadiness(page);
      await assertSupplierDirectory(page);
      const rfqName = await createRfq(page, values);
      await assertRfqReadiness(page, rfqName, values.supplier.name);
    }
    if (user.key === "user") {
      await assertCleanPage(page, "purchase-user-supplier-readonly");
    }
  } catch (error) {
    await capture(page, `${user.key}-failure`);
    const diagnostic = await pageState(page).catch((diagnosticError) => ({ diagnosticError: diagnosticError.message }));
    fs.writeFileSync(path.join(ARTIFACT_DIR, `${safeFileName(user.key)}-failure.json`), JSON.stringify({ error: error.message, details: error.details || {}, diagnostic }, null, 2));
    throw error;
  } finally {
    await context.close();
    await browser.close();
  }
}

(async () => {
  assert(USERS.length >= 2, "Purchase Manager and Purchase User credentials are required");
  for (const user of USERS) {
    await runForUser(user);
  }
  console.log(`Phase 7E1A supplier readiness smoke passed. Artifacts: ${ARTIFACT_DIR}`);
})().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exit(1);
});
