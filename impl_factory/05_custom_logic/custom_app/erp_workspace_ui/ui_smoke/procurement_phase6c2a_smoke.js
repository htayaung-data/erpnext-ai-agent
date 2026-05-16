const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const TIMEOUT = Number(process.env.ERPW_PROCUREMENT_SMOKE_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_PROCUREMENT_PHASE6C2A_ARTIFACT_DIR || path.join(__dirname, "artifacts", "procurement-phase6c2a");
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
const FORBIDDEN_ACTIVE_RE = /(submit|approve|reject|receive|purchase receipt|create receipt|bill|purchase invoice|create invoice|payment|pay|item price|default supplier|supplier portal|create supplier quotation|create purchase order|email suppliers)/i;
const FRAMEWORK_ERROR_RE = /(Insufficient Permissions|Email Account|Traceback|Server Error|Internal Server Error)/i;

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

async function visibleFrameworkState(page) {
  return page.evaluate(() => {
    const visible = (node) => {
      if (!node) return false;
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
    };
    const modals = Array.from(document.querySelectorAll(".modal.show")).filter(visible).map((modal) => (modal.innerText || "").replace(/\s+/g, " ").trim());
    return {
      modalCount: modals.length,
      modalText: modals.join(" "),
      bodyText: (document.body.innerText || "").replace(/\s+/g, " ").trim(),
    };
  });
}

async function assertNoFrameworkModal(page, label) {
  const state = await visibleFrameworkState(page);
  if (state.modalCount > 0 || FRAMEWORK_ERROR_RE.test(state.modalText) || FRAMEWORK_ERROR_RE.test(state.bodyText)) {
    await capture(page, `${label || "framework"}-unexpected-modal`);
  }
  assert(state.modalCount === 0, "Framework modal must not be visible", state);
  assert(!FRAMEWORK_ERROR_RE.test(state.modalText), "Framework permission/server modal leaked", state);
  assert(!FRAMEWORK_ERROR_RE.test(state.bodyText), "Framework permission/server error text leaked into page", state);
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
          header: { transaction_date: "2026-05-16", schedule_date: "2026-05-31" },
          suppliers: [{ supplier }],
          items: [{ item_code: item, qty: 1, schedule_date: "2026-05-31", warehouse: warehouse || "" }],
        }),
      },
    });
  }, { supplier: values.supplier.name, item: values.item.name, warehouse: values.warehouse && values.warehouse.name });
  const payload = response && response.message ? response.message : {};
  assert(payload.state && payload.state.kind === "ready", "RFQ save did not return ready", payload);
  assert(payload.form && payload.form.name, "RFQ save did not return a name", payload);
  return payload.form.name;
}

async function assertPdfEndpoint(page, rfqName, supplier) {
  const params = new URLSearchParams({ doctype: "Request for Quotation", name: rfqName, supplier });
  const url = routeUrl(`/api/method/${OUTPUT_PDF_METHOD}?${params.toString()}`);
  const response = await page.context().request.get(url);
  assert(response.ok(), "RFQ PDF endpoint did not return success", { url, status: response.status(), text: await response.text().catch(() => "") });
  const disposition = response.headers()["content-disposition"] || "";
  const body = await response.body();
  assert(disposition.includes(rfqName), "RFQ PDF filename missing RFQ name", { disposition });
  assert(disposition.includes("DRAFT-NOT-SENT"), "RFQ PDF filename missing DRAFT-NOT-SENT", { disposition });
  assert(body.length > 500, "RFQ PDF response body is unexpectedly small", { length: body.length, disposition });
}


async function openNewRfqForm(page) {
  await openDeskRoute(page, "/desk/procurement-console-rfq-form/new");
  await page.waitForSelector(".erpw-managed-rfq-page [data-erpw-managed-rfq-form]", { state: "visible", timeout: TIMEOUT });
  await assertNoFrameworkModal(page, "new-rfq-before-autocomplete");
}

function shortQuery(value) {
  const text = String(value || "").trim();
  if (!text) return "a";
  return text.slice(0, Math.min(4, text.length));
}

async function clearRfqSuggestions(page) {
  await page.evaluate(() => {
    document.querySelectorAll(".erpw-managed-rfq-suggestions").forEach((node) => node.remove());
  });
}

async function assertRfqAutocompletePlacement(page, userKey, kind, selector, query, viewport) {
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
  await assertNoFrameworkModal(page, `${userKey}-new-rfq-${kind}-autocomplete-${viewport.width}-modal`);
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
    const bodyWidth = Math.ceil(Math.max(document.body.scrollWidth, document.documentElement.scrollWidth));
    const text = menu ? (menu.innerText || "").replace(/\s+/g, " ").trim() : "";
    return {
      input: inputRect ? { left: inputRect.left, right: inputRect.right, top: inputRect.top, bottom: inputRect.bottom, width: inputRect.width } : null,
      menu: menuRect ? { left: menuRect.left, right: menuRect.right, top: menuRect.top, bottom: menuRect.bottom, width: menuRect.width, height: menuRect.height } : null,
      protectedBottom,
      bodyWidth,
      viewportWidth: window.innerWidth,
      viewportHeight: window.innerHeight,
      suggestionText: text,
      suggestionCount: menu ? menu.querySelectorAll(".erpw-managed-rfq-suggestion").length : 0,
      maxHeight: menu ? window.getComputedStyle(menu).maxHeight : "",
      overflowY: menu ? window.getComputedStyle(menu).overflowY : "",
    };
  }, selector);
  assert(metrics.input && metrics.menu, `${kind} autocomplete geometry missing`, metrics);
  assert(metrics.suggestionCount > 0, `${kind} autocomplete suggestions missing`, metrics);
  assert(metrics.menu.top >= metrics.input.bottom - 3, `${kind} autocomplete should open below the active input when below-space is usable`, metrics);
  assert(Math.abs(metrics.menu.left - metrics.input.left) <= 3, `${kind} autocomplete must remain horizontally attached to active input`, metrics);
  assert(metrics.menu.width >= metrics.input.width - 4, `${kind} autocomplete width must align with active input`, metrics);
  assert(metrics.menu.top >= metrics.protectedBottom - 2, `${kind} autocomplete must not cover the form toolbar/header`, metrics);
  assert(metrics.menu.right <= metrics.viewportWidth + 2, `${kind} autocomplete must not overflow viewport horizontally`, metrics);
  assert(metrics.menu.bottom <= metrics.viewportHeight + 2, `${kind} autocomplete must stay inside viewport with capped height`, metrics);
  assert(metrics.bodyWidth <= metrics.viewportWidth + 2, `${kind} autocomplete caused horizontal page overflow`, metrics);
  assert(/auto|scroll/i.test(metrics.overflowY), `${kind} autocomplete must be internally scrollable when capped`, metrics);
  await capture(page, `${userKey}-new-rfq-${kind}-autocomplete-${viewport.width}`);
  await clearRfqSuggestions(page);
}

async function assertNewRfqAutocompletePlacement(page, userKey, values) {
  const supplierQuery = shortQuery(values.supplier.name || values.supplier.supplier_name);
  const itemQuery = shortQuery(values.item.name || values.item.item_name);
  const warehouseQuery = shortQuery((values.warehouse && values.warehouse.name) || "warehouse");
  const viewports = [
    { width: 1136, height: 768 },
    { width: 1240, height: 768 },
    { width: 1440, height: 900 },
  ];
  for (const viewport of viewports) {
    await assertRfqAutocompletePlacement(page, userKey, "supplier", '[data-supplier-field="supplier"]', supplierQuery, viewport);
    await assertRfqAutocompletePlacement(page, userKey, "item", '[data-row-field="item_code"]', itemQuery, viewport);
    await assertRfqAutocompletePlacement(page, userKey, "warehouse", '[data-row-field="warehouse"]', warehouseQuery, viewport);
  }
}

async function assertReadinessPanel(page, userKey, rfqName, supplier) {
  await page.waitForSelector(".erpw-managed-rfq-page [data-managed-rfq-output-card]", { state: "visible", timeout: TIMEOUT });
  await page.waitForSelector("[data-rfq-readiness-panel]", { state: "visible", timeout: TIMEOUT });
  await page.waitForSelector("[data-rfq-recipient-row]", { state: "visible", timeout: TIMEOUT });
  await assertNoFrameworkModal(page, `${userKey}-rfq-readiness-before-state`);
  const state = await page.evaluate(() => {
    const visible = (node) => {
      if (!node) return false;
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
    };
    const shell = document.querySelector(".erpw-managed-rfq-page");
    const card = document.querySelector("[data-managed-rfq-output-card]");
    const panel = document.querySelector("[data-rfq-readiness-panel]");
    const activeButtons = Array.from(card.querySelectorAll("button")).filter((button) => visible(button) && !button.disabled).map((button) => (button.textContent || "").replace(/\s+/g, " ").trim());
    const disabledSend = card.querySelector("[data-rfq-send-disabled]");
    const rows = Array.from(card.querySelectorAll("[data-rfq-recipient-row]")).filter(visible).map((row) => ({
      text: (row.textContent || "").replace(/\s+/g, " ").trim(),
      status: row.getAttribute("data-rfq-readiness-status") || "",
    }));
    const text = (card.innerText || "").replace(/\s+/g, " ").trim();
    return {
      text,
      activeButtons,
      rows,
      outgoingState: (card.querySelector("[data-rfq-outgoing-email-state]") || {}).dataset ? card.querySelector("[data-rfq-outgoing-email-state]").dataset.rfqOutgoingEmailState : "",
      disabledSendText: disabledSend ? (disabledSend.textContent || "").trim() : "",
      disabledSendDisabled: disabledSend ? disabledSend.disabled : false,
      shellCount: Array.from(document.querySelectorAll(".erpw-managed-rfq-page")).filter(visible).length,
      panelCount: Array.from(document.querySelectorAll("[data-rfq-readiness-panel]")).filter(visible).length,
      bodyWidth: Math.ceil(Math.max(document.body.scrollWidth, document.documentElement.scrollWidth)),
      viewportWidth: Math.ceil(window.innerWidth),
      nativeEmailDialog: Boolean(document.querySelector(".email-dialog, .frappe-email, [data-fieldname='recipients']")),
      nativeLeak: /\/desk\/(?:Form|request-for-quotation)/i.test(location.pathname),
      panelVisible: visible(panel),
      shellText: (shell ? shell.innerText : "").replace(/\s+/g, " ").trim(),
    };
  });
  assert(state.shellCount === 1, "RFQ readiness shell count mismatch", state);
  assert(state.panelCount === 1, "RFQ readiness panel duplicated", state);
  assert(state.panelVisible, "RFQ readiness panel not visible", state);
  assert(state.bodyWidth <= state.viewportWidth + 2, "RFQ readiness page has horizontal overflow", state);
  assert(!state.nativeLeak, "RFQ readiness route leaked native path", state);
  assert(!state.nativeEmailDialog, "Native email dialog appeared", state);
  await assertNoFrameworkModal(page, `${userKey}-rfq-readiness-card`);
  assert(state.rows.length >= 1, "RFQ readiness recipient row missing", state);
  assert(state.rows.some((row) => /Ready|Missing email|Email unavailable|Invalid email|Send blocked/i.test(row.text)), "RFQ readiness row status missing", state);
  assert(/Recipient readiness/i.test(state.text), "Recipient readiness heading missing", state);
  assert(/RFQ email send is not enabled yet/i.test(state.text), "Blocked send explanation missing", state);
  assert(/Email unavailable|Outgoing email is not configured|Outgoing email availability could not be checked safely|Outgoing email setup exists but is not enabled/i.test(state.text), "Controlled outgoing email state missing", state);
  assert(!/Insufficient Permissions|Traceback|Server Error|Internal Server Error/i.test(state.text), "Framework error text leaked into readiness card", state);
  assert(/Preview RFQ/i.test(state.text) && /Download RFQ PDF/i.test(state.text), "Preview/PDF actions missing", state);
  assert(state.disabledSendText === "Send RFQ" && state.disabledSendDisabled, "Send RFQ must be disabled", state);
  assert(!state.activeButtons.some((label) => /Send|Email/i.test(label)), "Send/Email action must not be active", state);
  assert(!FORBIDDEN_ACTIVE_RE.test(state.activeButtons.join(" ")), "Active forbidden lifecycle action visible", state);
  await capture(page, `${userKey}-rfq-readiness-card-1136`);

  await page.selectOption("[data-rfq-output-supplier]", supplier);
  await assertNoFrameworkModal(page, `${userKey}-rfq-readiness-before-preview`);
  await page.locator("[data-rfq-output-preview]").click();
  await page.waitForSelector(".erpw-output-modal .erpw-output-preview-banner", { state: "visible", timeout: TIMEOUT });
  const preview = await page.evaluate((supplier) => {
    const modal = document.querySelector(".erpw-output-modal");
    const text = (modal ? modal.innerText : "").replace(/\s+/g, " ").trim();
    return {
      text,
      nativeControlsVisible: /(?:^|\s)(Print|Get PDF)(?:\s|$)/i.test(text),
      hasSupplier: text.includes(`Supplier: ${supplier}`),
    };
  }, supplier);
  assert(preview.text.includes("Draft / Not sent"), "RFQ preview missing draft watermark", preview);
  assert(preview.hasSupplier, "RFQ preview missing selected supplier context", preview);
  assert(!preview.nativeControlsVisible, "RFQ preview leaked native Print/Get PDF controls", preview);
  await assertNoFrameworkModal(page, `${userKey}-rfq-readiness-preview`);
  await capture(page, `${userKey}-rfq-readiness-preview-1136`);
  await page.locator(".erpw-output-modal-close").click({ force: true }).catch(async () => {
    await page.evaluate(() => document.querySelectorAll(".erpw-output-modal-backdrop").forEach((node) => node.remove()));
  });
  await page.locator(".erpw-output-modal-backdrop").waitFor({ state: "detached", timeout: 3000 }).catch(async () => {
    await page.evaluate(() => document.querySelectorAll(".erpw-output-modal-backdrop").forEach((node) => node.remove()));
  });

  await assertPdfEndpoint(page, rfqName, supplier);
}


async function assertReviewSupplierCommunication(page, userKey, rfqName, supplier) {
  const reviewRoute = `/desk/procurement-console-rfq-review/${encodeURIComponent(rfqName)}`;
  await page.setViewportSize({ width: 1136, height: 768 });
  await openDeskRoute(page, reviewRoute);
  await page.waitForSelector(".erpw-procurement-rfq-review-page [data-rfq-review-output-card]", { state: "visible", timeout: TIMEOUT });
  await page.waitForSelector(".erpw-procurement-rfq-review-page [data-rfq-readiness-panel]", { state: "visible", timeout: TIMEOUT });
  await page.waitForSelector(".erpw-procurement-rfq-review-page [data-rfq-recipient-row]", { state: "visible", timeout: TIMEOUT });
  await assertNoFrameworkModal(page, `${userKey}-rfq-review-communication-before-state`);
  const state = await page.evaluate(() => {
    const visible = (node) => {
      if (!node) return false;
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
    };
    const shell = document.querySelector(".erpw-procurement-rfq-review-page");
    const card = document.querySelector(".erpw-procurement-rfq-review-page [data-rfq-review-output-card]");
    const text = (card ? card.innerText : "").replace(/\s+/g, " ").trim();
    const activeButtons = card ? Array.from(card.querySelectorAll("button")).filter((button) => visible(button) && !button.disabled).map((button) => (button.textContent || "").replace(/\s+/g, " ").trim()) : [];
    const rows = card ? Array.from(card.querySelectorAll("[data-rfq-recipient-row]")).filter(visible).map((row) => ({
      text: (row.textContent || "").replace(/\s+/g, " ").trim(),
      status: row.getAttribute("data-rfq-readiness-status") || "",
    })) : [];
    const disabledSend = card ? card.querySelector("[data-rfq-send-disabled]") : null;
    return {
      text,
      activeButtons,
      rows,
      cardCount: Array.from(document.querySelectorAll(".erpw-procurement-rfq-review-page [data-rfq-review-output-card]")).filter(visible).length,
      panelCount: Array.from(document.querySelectorAll(".erpw-procurement-rfq-review-page [data-rfq-readiness-panel]")).filter(visible).length,
      disabledSendText: disabledSend ? (disabledSend.textContent || "").trim() : "",
      disabledSendDisabled: disabledSend ? disabledSend.disabled : false,
      bodyWidth: Math.ceil(Math.max(document.body.scrollWidth, document.documentElement.scrollWidth)),
      viewportWidth: Math.ceil(window.innerWidth),
      nativeEmailDialog: Boolean(document.querySelector(".email-dialog, .frappe-email, [data-fieldname='recipients']")),
      nativeLeak: /\/desk\/(?:Form|request-for-quotation)/i.test(location.pathname),
      shellText: (shell ? shell.innerText : "").replace(/\s+/g, " ").trim(),
    };
  });
  assert(state.cardCount === 1, "RFQ review Supplier Communication card duplicated or missing", state);
  assert(state.panelCount === 1, "RFQ review recipient readiness panel duplicated or missing", state);
  assert(state.bodyWidth <= state.viewportWidth + 2, "RFQ review output card has horizontal overflow", state);
  assert(!state.nativeLeak, "RFQ review leaked native path", state);
  assert(!state.nativeEmailDialog, "Native email dialog appeared on RFQ review", state);
  assert(/Supplier Communication/i.test(state.text), "RFQ review Supplier Communication heading missing", state);
  assert(/Draft \/ Not sent/i.test(state.text), "RFQ review draft status missing", state);
  assert(/Recipient readiness/i.test(state.text), "RFQ review recipient readiness missing", state);
  assert(/RFQ email send is not enabled yet/i.test(state.text), "RFQ review blocked send explanation missing", state);
  assert(/Email unavailable|Outgoing email is not configured|Outgoing email availability could not be checked safely|Outgoing email setup exists but is not enabled/i.test(state.text), "RFQ review controlled outgoing email state missing", state);
  assert(!/Insufficient Permissions|Email Account|Traceback|Server Error|Internal Server Error/i.test(state.text), "Framework error text leaked into RFQ review output card", state);
  assert(/Preview RFQ/i.test(state.text) && /Download RFQ PDF/i.test(state.text), "RFQ review preview/PDF actions missing", state);
  assert(state.rows.length >= 1, "RFQ review recipient rows missing", state);
  assert(state.rows.some((row) => /Ready|Missing email|Email unavailable|Invalid email|Send blocked/i.test(row.text)), "RFQ review recipient row status missing", state);
  assert(state.disabledSendText === "Send RFQ" && state.disabledSendDisabled, "RFQ review Send RFQ must be disabled", state);
  assert(!state.activeButtons.some((label) => /Send|Email/i.test(label)), "RFQ review Send/Email action must not be active", state);
  assert(!FORBIDDEN_ACTIVE_RE.test(state.activeButtons.join(" ")), "RFQ review active forbidden lifecycle action visible", state);
  await assertNoFrameworkModal(page, `${userKey}-rfq-review-communication-card`);
  await capture(page, `${userKey}-rfq-review-communication-card-1136`);

  await page.selectOption(".erpw-procurement-rfq-review-page [data-rfq-output-supplier]", supplier);
  await assertNoFrameworkModal(page, `${userKey}-rfq-review-before-preview`);
  await page.locator(".erpw-procurement-rfq-review-page [data-rfq-output-preview]").click();
  await page.waitForSelector(".erpw-output-modal .erpw-output-preview-banner", { state: "visible", timeout: TIMEOUT });
  const preview = await page.evaluate((supplier) => {
    const modal = document.querySelector(".erpw-output-modal");
    const text = (modal ? modal.innerText : "").replace(/\s+/g, " ").trim();
    return {
      text,
      nativeControlsVisible: /(?:^|\s)(Print|Get PDF)(?:\s|$)/i.test(text),
      hasSupplier: text.includes(`Supplier: ${supplier}`),
    };
  }, supplier);
  assert(preview.text.includes("Draft / Not sent"), "RFQ review preview missing draft watermark", preview);
  assert(preview.hasSupplier, "RFQ review preview missing selected supplier context", preview);
  assert(!preview.nativeControlsVisible, "RFQ review preview leaked native Print/Get PDF controls", preview);
  await assertNoFrameworkModal(page, `${userKey}-rfq-review-preview`);
  await capture(page, `${userKey}-rfq-review-preview-1136`);
  await page.locator(".erpw-output-modal-close").click({ force: true }).catch(async () => {
    await page.evaluate(() => document.querySelectorAll(".erpw-output-modal-backdrop").forEach((node) => node.remove()));
  });
  await page.locator(".erpw-output-modal-backdrop").waitFor({ state: "detached", timeout: 3000 }).catch(async () => {
    await page.evaluate(() => document.querySelectorAll(".erpw-output-modal-backdrop").forEach((node) => node.remove()));
  });
  await assertPdfEndpoint(page, rfqName, supplier);

  await openDeskRoute(page, reviewRoute);
  await page.waitForSelector(".erpw-procurement-rfq-review-page [data-rfq-readiness-panel]", { state: "visible", timeout: TIMEOUT });
  const repeat = await page.evaluate(() => Array.from(document.querySelectorAll(".erpw-procurement-rfq-review-page [data-rfq-readiness-panel]")).filter((node) => {
    const rect = node.getBoundingClientRect();
    const style = window.getComputedStyle(node);
    return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
  }).length);
  assert(repeat === 1, "Repeated RFQ review navigation duplicated Supplier Communication panel", { repeat });

  await page.setViewportSize({ width: 1440, height: 900 });
  await openDeskRoute(page, reviewRoute);
  await page.waitForSelector(".erpw-procurement-rfq-review-page [data-rfq-review-output-card]", { state: "visible", timeout: TIMEOUT });
  await page.waitForSelector(".erpw-procurement-rfq-review-page [data-rfq-readiness-panel]", { state: "visible", timeout: TIMEOUT });
  await assertNoFrameworkModal(page, `${userKey}-rfq-review-communication-card-1440`);
  await capture(page, `${userKey}-rfq-review-communication-card-1440`);
}

async function runForUser(browser, user) {
  const context = await browser.newContext({ viewport: { width: 1136, height: 768 }, acceptDownloads: true });
  const page = await context.newPage();
  page.on("console", (message) => {
    if (["error", "warning"].includes(message.type())) console.log(`[${user.key}] browser ${message.type()}: ${message.text()}`);
  });
  await login(page, user);
  const values = await fixtures(page);
  await assertNewRfqAutocompletePlacement(page, user.key, values);
  await page.setViewportSize({ width: 1136, height: 768 });
  const rfqName = await createRfq(page, values);
  const route = `/desk/procurement-console-rfq-form/${encodeURIComponent(rfqName)}`;

  await openDeskRoute(page, route);
  await assertReadinessPanel(page, user.key, rfqName, values.supplier.name);
  await assertReviewSupplierCommunication(page, user.key, rfqName, values.supplier.name);
  await openDeskRoute(page, route);
  await page.waitForSelector("[data-rfq-readiness-panel]", { state: "visible", timeout: TIMEOUT });
  await page.waitForSelector("[data-rfq-recipient-row]", { state: "visible", timeout: TIMEOUT });
  const repeat = await page.evaluate(() => Array.from(document.querySelectorAll("[data-rfq-readiness-panel]")).filter((node) => {
    const rect = node.getBoundingClientRect();
    const style = window.getComputedStyle(node);
    return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
  }).length);
  assert(repeat === 1, "Repeated navigation duplicated readiness panel", { repeat });

  await page.setViewportSize({ width: 1440, height: 900 });
  await openDeskRoute(page, route);
  await page.waitForSelector("[data-rfq-readiness-panel]", { state: "visible", timeout: TIMEOUT });
  await page.waitForSelector("[data-rfq-recipient-row]", { state: "visible", timeout: TIMEOUT });
  await assertNoFrameworkModal(page, `${user.key}-rfq-readiness-card-1440`);
  await capture(page, `${user.key}-rfq-readiness-card-1440`);
  await context.close();
  return { user: user.key, rfqName };
}

(async () => {
  if (!USERS.length) throw new Error("Set Purchase Manager/User credentials before running Phase 6C2A smoke.");
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
