const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const TIMEOUT = Number(process.env.ERPW_PROCUREMENT_SMOKE_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_PROCUREMENT_PHASE6C1_ARTIFACT_DIR || path.join(__dirname, "artifacts", "procurement-phase6c1");
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
const FORBIDDEN_LIFECYCLE_RE = /(submit|approve|reject|receive|purchase receipt|create receipt|bill|purchase invoice|create invoice|payment|pay|item price|default supplier|supplier portal|create supplier quotation|create purchase order)/i;

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
  const response = await page.evaluate(async ({ supplier, item, warehouse }) => {
    return frappe.call({
      method: "erp_workspace_ui.procurement_console.managed_rfq.save_managed_rfq_draft",
      args: {
        payload: JSON.stringify({
          header: { transaction_date: "2026-05-15", schedule_date: "2026-05-30" },
          suppliers: [{ supplier }],
          items: [{ item_code: item, qty: 1, schedule_date: "2026-05-30", warehouse: warehouse || "" }],
        }),
      },
    });
  }, { supplier: values.supplier.name, item: values.item.name, warehouse: values.warehouse && values.warehouse.name });
  const payload = response && response.message ? response.message : {};
  assert(payload.state && payload.state.kind === "ready", "RFQ save did not return ready", payload);
  assert(payload.form && payload.form.name, "RFQ save did not return a name", payload);
  return payload.form.name;
}

async function createPo(page, values) {
  const response = await page.evaluate(async ({ supplier, item, warehouse }) => {
    return frappe.call({
      method: "erp_workspace_ui.procurement_console.managed_purchase_order.save_managed_purchase_order",
      args: {
        payload: JSON.stringify({
          header: { supplier, transaction_date: "2026-05-15", schedule_date: "2026-05-30", currency: "MMK", set_warehouse: warehouse || "" },
          items: [{ item_code: item, qty: 1, rate: 100, schedule_date: "2026-05-30", warehouse: warehouse || "" }],
        }),
      },
    });
  }, { supplier: values.supplier.name, item: values.item.name, warehouse: values.warehouse && values.warehouse.name });
  const payload = response && response.message ? response.message : {};
  assert(payload.state && payload.state.kind === "ready", "PO save did not return ready", payload);
  assert(payload.form && payload.form.name, "PO save did not return a name", payload);
  return payload.form.name;
}

async function assertPdfEndpoint(page, args, expectedNameFragments) {
  const params = new URLSearchParams();
  Object.keys(args).forEach((key) => params.set(key, args[key]));
  const url = routeUrl(`/api/method/${OUTPUT_PDF_METHOD}?${params.toString()}`);
  const response = await page.context().request.get(url);
  assert(response.ok(), "PDF endpoint did not return success", { url, status: response.status(), text: await response.text().catch(() => "") });
  const disposition = response.headers()["content-disposition"] || "";
  const body = await response.body();
  expectedNameFragments.forEach((fragment) => {
    assert(disposition.includes(fragment), "PDF filename missing expected fragment", { disposition, fragment });
  });
  assert(body.length > 500, "PDF response body is unexpectedly small", { length: body.length, disposition });
}

async function assertOutputChrome(page, type, userKey, name, supplier) {
  const prefix = type === "rfq" ? "rfq" : "po";
  const shellSelector = type === "rfq" ? ".erpw-managed-rfq-page" : ".erpw-managed-po-page";
  const cardSelector = type === "rfq" ? "[data-managed-rfq-output-card]" : "[data-managed-po-output-card]";
  await page.waitForSelector(`${shellSelector} ${cardSelector}`, { state: "visible", timeout: TIMEOUT });
  const state = await page.evaluate(({ shellSelector, cardSelector, type }) => {
    const visible = (node) => {
      if (!node) return false;
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
    };
    const shell = document.querySelector(shellSelector);
    const card = document.querySelector(cardSelector);
    const buttons = Array.from(card.querySelectorAll("button")).filter(visible).map((button) => ({
      text: (button.textContent || "").replace(/\s+/g, " ").trim(),
      disabled: button.disabled,
    }));
    const bodyWidth = Math.ceil(Math.max(document.body.scrollWidth, document.documentElement.scrollWidth));
    const viewportWidth = Math.ceil(window.innerWidth);
    return {
      text: (shell ? shell.innerText : document.body.innerText).replace(/\s+/g, " ").trim(),
      cardText: (card.innerText || "").replace(/\s+/g, " ").trim(),
      buttons,
      bodyWidth,
      viewportWidth,
      shellCount: Array.from(document.querySelectorAll(shellSelector)).filter(visible).length,
      nativeLeak: /\/desk\/(?:Form|request-for-quotation|purchase-order)/i.test(location.pathname),
      hasPreview: Boolean(card.querySelector(type === "rfq" ? "[data-rfq-output-preview]" : "[data-po-output-preview]")),
      hasDownload: Boolean(card.querySelector(type === "rfq" ? "[data-rfq-output-download]" : "[data-po-output-download]")),
    };
  }, { shellSelector, cardSelector, type });
  assert(state.shellCount === 1, `${type} output page shell count mismatch`, state);
  assert(state.bodyWidth <= state.viewportWidth + 2, `${type} output page has horizontal overflow`, state);
  assert(!state.nativeLeak, `${type} output route leaked native path`, state);
  assert(state.hasPreview && state.hasDownload, `${type} output buttons missing`, state);
  assert(!state.buttons.some((button) => /Email|Send/i.test(button.text) && !button.disabled), `${type} send action must not be active`, state);
  assert(/send/i.test(state.cardText), `${type} send block copy missing`, state);
  assert(!FORBIDDEN_LIFECYCLE_RE.test(state.buttons.filter((button) => !button.disabled).map((button) => button.text).join(" ")), `${type} active forbidden action visible`, state);
  if (type === "rfq") {
    assert(/Draft \/ Not sent/.test(state.cardText), "RFQ draft/not-sent status missing", state);
    assert(/governed RFQ send/.test(state.cardText), "RFQ governed-send block copy missing", state);
  } else {
    assert(/Draft \/ Not for supplier/.test(state.cardText), "PO draft/not-for-supplier status missing", state);
    assert(/not a supplier commitment/.test(state.cardText), "PO commitment warning missing", state);
  }
  await capture(page, `${userKey}-${prefix}-output-card-1136`);
  if (type === "rfq") await page.selectOption("[data-rfq-output-supplier]", supplier);
  await page.locator(type === "rfq" ? "[data-rfq-output-preview]" : "[data-po-output-preview]").click();
  await page.waitForSelector(".erpw-output-modal .erpw-output-preview-banner", { state: "visible", timeout: TIMEOUT });
  const previewText = await page.locator(".erpw-output-modal").innerText();
  if (type === "rfq") {
    assert(previewText.includes("Draft / Not sent"), "RFQ preview missing draft/not-sent watermark", { previewText });
    assert(previewText.includes(`Supplier: ${supplier}`), "RFQ preview missing selected supplier context", { previewText, supplier });
  } else {
    assert(previewText.includes("Draft / Not for supplier"), "PO preview missing draft/not-for-supplier watermark", { previewText });
  }
  await capture(page, `${userKey}-${prefix}-preview-1136`);
  await page.locator(".erpw-output-modal-close").click();
}

async function runForUser(browser, user) {
  const context = await browser.newContext({ viewport: { width: 1136, height: 768 }, acceptDownloads: true });
  const page = await context.newPage();
  const screenshots = [];
  page.on("console", (message) => {
    if (["error", "warning"].includes(message.type())) console.log(`[${user.key}] browser ${message.type()}: ${message.text()}`);
  });
  await login(page, user);
  const values = await fixtures(page);

  const rfqName = await createRfq(page, values);
  await openDeskRoute(page, `/desk/procurement-console-rfq-form/${encodeURIComponent(rfqName)}`);
  await assertOutputChrome(page, "rfq", user.key, rfqName, values.supplier.name);
  await assertPdfEndpoint(page, { doctype: "Request for Quotation", name: rfqName, supplier: values.supplier.name }, [rfqName, values.supplier.name.replace(/[^A-Za-z0-9._-]+/g, "-"), "DRAFT-NOT-SENT"]);

  const poName = await createPo(page, values);
  await openDeskRoute(page, `/desk/procurement-console-purchase-order-form/${encodeURIComponent(poName)}`);
  await assertOutputChrome(page, "po", user.key, poName, values.supplier.name);
  await assertPdfEndpoint(page, { doctype: "Purchase Order", name: poName }, [poName, "DRAFT-NOT-FOR-SUPPLIER"]);

  await page.setViewportSize({ width: 1440, height: 900 });
  await openDeskRoute(page, `/desk/procurement-console-rfq-form/${encodeURIComponent(rfqName)}`);
  await page.waitForSelector("[data-managed-rfq-output-card]", { state: "visible", timeout: TIMEOUT });
  screenshots.push(await capture(page, `${user.key}-rfq-output-card-1440`));
  await openDeskRoute(page, `/desk/procurement-console-purchase-order-form/${encodeURIComponent(poName)}`);
  await page.waitForSelector("[data-managed-po-output-card]", { state: "visible", timeout: TIMEOUT });
  screenshots.push(await capture(page, `${user.key}-po-output-card-1440`));
  await context.close();
  return { user: user.key, rfqName, poName, screenshots };
}

(async () => {
  if (!USERS.length) throw new Error("Set Purchase Manager/User credentials before running Phase 6C1 smoke.");
  const browser = await chromium.launch({ headless: true });
  const results = [];
  try {
    for (const user of USERS) results.push(await runForUser(browser, user));
  } finally {
    await browser.close();
  }
  const summary = { ok: true, artifactDir: ARTIFACT_DIR, results };
  fs.writeFileSync(path.join(ARTIFACT_DIR, "summary.json"), JSON.stringify(summary, null, 2));
  console.log(JSON.stringify(summary, null, 2));
})().catch((error) => {
  const summary = { ok: false, artifactDir: ARTIFACT_DIR, message: error.message, stack: error.stack, details: error.details || null };
  fs.writeFileSync(path.join(ARTIFACT_DIR, "summary.json"), JSON.stringify(summary, null, 2));
  console.error(JSON.stringify(summary, null, 2));
  process.exit(1);
});
