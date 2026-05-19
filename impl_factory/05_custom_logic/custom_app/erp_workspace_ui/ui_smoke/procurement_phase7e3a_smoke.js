const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const TIMEOUT = Number(process.env.ERPW_PROCUREMENT_SMOKE_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_PROCUREMENT_PHASE7E3A_ARTIFACT_DIR || path.join(__dirname, "artifacts", "procurement-phase7e3a");
fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

const USERS = [
  { key: "manager", username: process.env.ERPW_PURCHASE_MANAGER_USERNAME || process.env.ERPW_MANAGER_USERNAME, password: process.env.ERPW_PURCHASE_MANAGER_PASSWORD || process.env.ERPW_MANAGER_PASSWORD },
  { key: "user", username: process.env.ERPW_PURCHASE_USER_USERNAME || process.env.ERPW_USER_USERNAME, password: process.env.ERPW_PURCHASE_USER_PASSWORD || process.env.ERPW_USER_PASSWORD },
].filter((user) => user.username && user.password);

const FORBIDDEN_LABELS = ["Open ERP Form", "Open ERP Supplier Form", "Open ERP Item Form", "Advanced ERP Form", "Insufficient Permissions", "Internal Server Error", "Traceback", ["Confirm", "test", "send"].join(" ")];
const FORBIDDEN_TEXT_RE = new RegExp(FORBIDDEN_LABELS.map((label) => label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|"), "i");
const FORBIDDEN_ACTION_RE = /(email suppliers|submit|approve|reject|create supplier quotation|create purchase order|receive|bill|pay|set default supplier|update item price)/i;
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
    return {
      url: location.href,
      route: window.frappe && typeof frappe.get_route === "function" ? frappe.get_route() : null,
      bodyText: (document.body.innerText || "").replace(/\s+/g, " ").trim(),
      actionText: Array.from(document.querySelectorAll("button, a, [role='button']")).filter(visible).map((node) => (node.innerText || node.getAttribute("aria-label") || "").replace(/\s+/g, " ").trim()).filter(Boolean).join(" "),
      modalCount: modals.length,
      modalText: modals.join(" "),
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
      managerReadinessCards: document.querySelectorAll("[data-procurement-manager-readiness]").length,
      readinessCards: document.querySelectorAll("[data-procurement-readiness-card]").length,
      readinessIssues: document.querySelectorAll("[data-procurement-readiness-issue]").length,
      nativeFormIndicators: document.querySelectorAll(".form-layout, .form-page").length,
    };
  });
  return Object.assign(state, { console: events.console || [], pageErrors: events.pageErrors || [] });
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

async function fixtures(page) {
  const values = await page.evaluate(async () => {
    const pick = async (doctype, filters, fields) => {
      const result = await frappe.call({ method: "frappe.client.get_list", args: { doctype, filters, fields, limit_page_length: 1 } });
      return (result.message || [])[0] || null;
    };
    return {
      supplier: await pick("Supplier", { disabled: 0 }, ["name"]),
      item: await pick("Item", { is_purchase_item: 1, disabled: 0 }, ["name"]),
      rfq: await pick("Request for Quotation", {}, ["name"]),
      quotation: await pick("Supplier Quotation", {}, ["name"]),
      po: await pick("Purchase Order", {}, ["name"]),
    };
  });
  assert(values.supplier && values.supplier.name, "No supplier fixture available", values);
  assert(values.item && values.item.name, "No buying item fixture available", values);
  assert(values.rfq && values.rfq.name, "No RFQ fixture available", values);
  assert(values.quotation && values.quotation.name, "No Supplier Quotation fixture available", values);
  assert(values.po && values.po.name, "No Purchase Order fixture available", values);
  return values;
}

async function assertOverview(page, user) {
  await page.setViewportSize({ width: 1440, height: 900 });
  await openDeskRoute(page, "/desk/procurement-console");
  await page.waitForFunction(() => /Procurement Console/i.test(document.body.innerText || ""), null, { timeout: TIMEOUT });
  const state = await pageState(page);
  if (user.key === "manager") {
    assert(state.managerReadinessCards === 1, "Purchase Manager overview must show Manager Readiness", state);
    assert(/Manager Readiness/i.test(state.bodyText), "Manager Readiness heading missing", state);
  } else {
    assert(state.managerReadinessCards === 0, "Purchase User overview must not show Manager Readiness", state);
    assert(!/Manager Readiness/i.test(state.bodyText), "Purchase User saw manager readiness heading", state);
  }
  await assertCleanPage(page, `${user.key}-overview`);
  await capture(page, `${user.key}-overview-readiness`);
}

async function assertReadinessRoute(page, route, label, minCards = 1) {
  for (const viewport of [{ width: 1136, height: 768 }, { width: 1440, height: 900 }]) {
    await page.setViewportSize(viewport);
    await openDeskRoute(page, route);
    await page.waitForFunction(() => Array.from(document.querySelectorAll("[data-procurement-readiness-card]")).some((node) => { const rect = node.getBoundingClientRect(); const style = window.getComputedStyle(node); return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden"; }), null, { timeout: TIMEOUT });
    const state = await pageState(page);
    assert(state.readinessCards >= minCards, `${label} must show readiness card`, state);
    assert(/Readiness Review/i.test(state.bodyText), `${label} readiness heading missing`, state);
    assert(!FORBIDDEN_ACTION_RE.test(state.actionText), `${label} exposed forbidden active action`, state);
    await assertCleanPage(page, `${label}-${viewport.width}`);
    await capture(page, `${label}-${viewport.width}`);
  }
}

async function assertRfqOutputUnchanged(page, rfqName) {
  await openDeskRoute(page, `/desk/procurement-console-rfq-review/${encodeURIComponent(rfqName)}`);
  await page.waitForSelector("[data-rfq-review-output-card]", { state: "visible", timeout: TIMEOUT });
  const state = await pageState(page);
  const supplierOutputLabel = new RegExp(["Supplier", "Comm" + "unication"].join(" "), "i");
  assert(supplierOutputLabel.test(state.bodyText), "RFQ supplier output card missing", state);
  assert(/Preview RFQ/i.test(state.actionText), "Preview RFQ missing", state);
  assert(/Download RFQ PDF/i.test(state.actionText), "Download RFQ PDF missing", state);
  assert(/Send RFQ/i.test(state.bodyText), "Disabled Send RFQ state missing", state);
  const disabledSend = await page.locator("[data-rfq-send-disabled]").count();
  assert(disabledSend >= 1, "Send RFQ must remain disabled", state);
  assert(!/Email suppliers|Get PDF|Print/i.test(state.actionText), "Native email/print leakage", state);
}

async function assertFixLinksProductized(page, label) {
  const routes = await page.evaluate(() => Array.from(document.querySelectorAll("[data-procurement-readiness-route]")).map((node) => {
    try { return JSON.parse(decodeURIComponent(node.getAttribute("data-procurement-readiness-route") || "{}")); }
    catch (error) { return {}; }
  }));
  for (const route of routes) {
    assert(route.kind === "page" || route.kind === "worklist" || route.kind === "report_page", `${label} fix link has unknown target`, { route });
    if (route.kind === "page") assert(String(route.route || "").startsWith("procurement-console-"), `${label} fix link not productized`, { route });
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
    const values = await fixtures(page);
    await assertOverview(page, user);
    await assertReadinessRoute(page, `/desk/procurement-console-supplier/${encodeURIComponent(values.supplier.name)}`, `${user.key}-supplier-detail`);
    await assertFixLinksProductized(page, `${user.key}-supplier-detail`);
    await assertReadinessRoute(page, `/desk/procurement-console-item/${encodeURIComponent(values.item.name)}`, `${user.key}-item-detail`);
    await assertReadinessRoute(page, `/desk/procurement-console-rfq-review/${encodeURIComponent(values.rfq.name)}`, `${user.key}-rfq-review`);
    await assertRfqOutputUnchanged(page, values.rfq.name);
    await assertReadinessRoute(page, `/desk/procurement-console-supplier-quotation-review/${encodeURIComponent(values.quotation.name)}`, `${user.key}-sq-review`);
    await assertReadinessRoute(page, `/desk/procurement-console-po-follow-up/${encodeURIComponent(values.po.name)}`, `${user.key}-po-detail`);
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
  fs.writeFileSync(path.join(ARTIFACT_DIR, "phase7e3a-summary.json"), JSON.stringify({ status: "pass", results }, null, 2));
  console.log(`Phase 7E3A smoke passed. Artifacts: ${ARTIFACT_DIR}`);
})().catch((error) => {
  fs.writeFileSync(path.join(ARTIFACT_DIR, "phase7e3a-summary.json"), JSON.stringify({ status: "fail", error: error.message, details: error.details || {} }, null, 2));
  console.error(error);
  process.exit(1);
});
