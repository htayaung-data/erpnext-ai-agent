const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const TIMEOUT = Number(process.env.ERPW_PROCUREMENT_SMOKE_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_PROCUREMENT_ARTIFACT_DIR || path.join(__dirname, "artifacts", "procurement-responsive-filters");
fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
const USERS = [
  { key: "manager", username: process.env.ERPW_MANAGER_USERNAME, password: process.env.ERPW_MANAGER_PASSWORD },
  { key: "user", username: process.env.ERPW_USER_USERNAME, password: process.env.ERPW_USER_PASSWORD },
].filter((user) => user.username && user.password);
const VIEWPORTS = [{ key: "desktop-1240", width: 1240, height: 768 }, { key: "desktop-1440", width: 1440, height: 900 }];
const REPORTS = [
  ["reports-index", "Reports Index", "/desk/procurement-console-report", false],
  ["quote-comparison", "Quote Comparison", "/desk/procurement-console-report/supplier-quotation-comparison", true],
  ["purchase-order-analysis", "Purchase Order Analysis", "/desk/procurement-console-report/purchase-order-analysis", true],
  ["demand-to-order-coverage", "Demand-to-Order Coverage", "/desk/procurement-console-report/demand-to-order-coverage", true],
  ["item-purchase-history", "Item Purchase History", "/desk/procurement-console-report/item-purchase-history", true],
];
const WORKLISTS = [
  ["supplier-directory", "Supplier Directory", "/desk/procurement-console-worklist/supplier-directory"],
  ["purchase-request-directory", "Purchase Request Directory", "/desk/procurement-console-worklist/purchase-request-directory"],
  ["purchase-order-directory", "Purchase Order Directory", "/desk/procurement-console-worklist/purchase-order-directory"],
  ["rfq-directory", "RFQ Directory", "/desk/procurement-console-worklist/rfq-directory"],
  ["supplier-quotation-directory", "Supplier Quotation Directory", "/desk/procurement-console-worklist/supplier-quotation-directory"],
  ["buying-items-directory", "Buying Items Directory", "/desk/procurement-console-worklist/buying-item-directory"],
  ["purchase-orders-open", "Open Purchase Orders", "/desk/procurement-console-worklist/purchase-orders-open"],
  ["purchase-orders-overdue", "Overdue Purchase Orders", "/desk/procurement-console-worklist/purchase-orders-overdue"],
  ["purchase-orders-due-soon", "Purchase Orders Due Soon", "/desk/procurement-console-worklist/purchase-orders-due-soon"],
  ["purchase-orders-supplier-follow-up", "Supplier Follow-up", "/desk/procurement-console-worklist/purchase-orders-supplier-follow-up"],
];
const DETAIL_QUEUES = [
  ["purchase_order_directory", "po-detail", "PO Follow-up Detail", (name) => `/desk/procurement-console-po-follow-up/${encodeURIComponent(name)}`, ".erpw-procurement-po-follow-up-shell"],
  ["purchase_request_directory", "purchase-request-review", "Purchase Request Review", (name) => `/desk/procurement-console-purchase-request-review/${encodeURIComponent(name)}`, ".erpw-procurement-review-shell"],
  ["rfq_directory", "rfq-review", "RFQ Review", (name) => `/desk/procurement-console-rfq-review/${encodeURIComponent(name)}`, ".erpw-procurement-review-shell"],
  ["supplier_quotation_directory", "supplier-quotation-review", "Supplier Quotation Review", (name) => `/desk/procurement-console-supplier-quotation-review/${encodeURIComponent(name)}`, ".erpw-procurement-review-shell"],
  ["supplier_directory", "supplier-detail", "Supplier Detail", (name) => `/desk/procurement-console-supplier/${encodeURIComponent(name)}`, ".erpw-procurement-supplier-detail-shell"],
  ["buying_item_directory", "item-detail", "Item Detail", (name) => `/desk/procurement-console-item/${encodeURIComponent(name)}`, ".erpw-procurement-item-detail-shell"],
];
function routeUrl(route) { return new URL(route, BASE_URL).toString(); }
function safe(value) { return String(value || "shot").toLowerCase().replace(/[^a-z0-9_-]+/g, "-").replace(/^-+|-+$/g, ""); }
function assert(condition, message, details = {}) { if (!condition) { const error = new Error(message); error.details = details; throw error; } }
async function login(page, user) {
  await page.goto(routeUrl("/login"), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  await page.locator("#login_email, input[name='usr'], input[name='login_email'], input[type='email'], input[type='text']").first().fill(user.username);
  await page.locator("#login_password, input[name='pwd'], input[name='login_password'], input[type='password']").first().fill(user.password);
  await Promise.all([page.waitForURL(/\/(?:app|desk)(?:[/?#]|$)/, { waitUntil: "domcontentloaded", timeout: TIMEOUT }), page.locator("button:has-text('Login'), button.btn-login, .btn-login").first().click()]);
}
async function callMethod(page, method, args = {}) {
  return page.evaluate(async ({ method, args, timeout }) => {
    const body = new URLSearchParams();
    Object.entries(args || {}).forEach(([key, value]) => body.set(key, typeof value === "string" ? value : JSON.stringify(value)));
    const response = await fetch(`/api/method/${method}`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "X-Frappe-CSRF-Token": (window.frappe && window.frappe.csrf_token) || "" }, body, signal: AbortSignal.timeout(timeout) });
    return { ok: response.ok, status: response.status, data: await response.json().catch(() => ({})) };
  }, { method, args, timeout: TIMEOUT });
}
async function resolveDetails(page) {
  const details = [];
  for (const [queue, key, label, routeFor, shell] of DETAIL_QUEUES) {
    const response = await callMethod(page, "erp_workspace_ui.procurement_console.worklist.get_procurement_console_worklist_context", { queue_key: queue }).catch(() => null);
    const row = response && response.ok ? ((((response.data.message || {}).results || {}).rows || [])[0] || {}) : {};
    const name = row.name || row.key;
    if (name) details.push({ key, label, route: routeFor(name), shell });
  }
  return details;
}
async function openPage(page, route, shell) {
  const targetUrl = routeUrl(route);
  const targetPath = new URL(targetUrl).pathname;
  const canUseDeskRouter = await page.evaluate(() => Boolean(window.frappe && typeof frappe.set_route === "function")).catch(() => false);
  if (canUseDeskRouter && targetPath.startsWith("/desk/")) {
    const parts = targetPath.replace(/^\/desk\/?/, "").split("/").filter(Boolean).map((part) => {
      try { return decodeURIComponent(part); } catch (error) { return part; }
    });
    await page.evaluate((routeParts) => frappe.set_route.apply(frappe, routeParts), parts);
    await page.waitForURL((url) => url.pathname === targetPath, { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  } else {
    await page.goto(targetUrl, { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  }
  await page.locator(shell).first().waitFor({ state: "visible", timeout: TIMEOUT });
  await page.waitForTimeout(450);
}
async function measure(page, type) {
  return page.evaluate((type) => {
    const visible = (node) => { if (!node) return false; const style = getComputedStyle(node); const box = node.getBoundingClientRect(); return style.display !== "none" && style.visibility !== "hidden" && box.width > 0 && box.height > 0; };
    const rect = (node) => { if (!node) return null; const box = node.getBoundingClientRect(); return { top: Math.round(box.top), left: Math.round(box.left), right: Math.round(box.right), bottom: Math.round(box.bottom), width: Math.round(box.width), height: Math.round(box.height) }; };
    const shellSelector = type === "report" ? ".erpw-report-shell" : type === "list" ? ".erpw-list-shell" : ".erpw-procurement-po-follow-up-shell, .erpw-procurement-review-shell, .erpw-procurement-supplier-detail-shell, .erpw-procurement-item-detail-shell";
    const controls = document.querySelector(type === "report" ? ".erpw-report-controls" : ".erpw-list-controls-strip");
    const action = controls && controls.querySelector(type === "report" ? ".erpw-report-command-actions" : ".erpw-list-command-action-cell .erpw-list-toolbar-actions, .erpw-list-toolbar-actions");
    const fields = controls ? Array.from(controls.querySelectorAll(type === "report" ? ".erpw-report-control-field" : ".erpw-list-control-field:not(.erpw-list-action-field)")).filter(visible).map((node) => rect(node.querySelector("input, select, textarea") || node)) : [];
    const buttons = action ? Array.from(action.querySelectorAll("button")).filter(visible).map((button) => Object.assign({ text: button.textContent.trim() }, rect(button))) : [];
    const viewport = { width: window.innerWidth, height: window.innerHeight };
    const controlsRect = rect(controls);
    const actionRect = rect(action);
    const clipped = (box) => box && (box.left < 0 || box.right > viewport.width || (controlsRect && (box.left < controlsRect.left || box.right > controlsRect.right)));
    return { url: location.href, viewport, shell: rect(document.querySelector(shellSelector)), controls: controlsRect, action: actionRect, fields, buttons, actionClipped: clipped(actionRect), clippedButtons: buttons.filter(clipped), clippedFields: fields.filter(clipped), shellCount: Array.from(document.querySelectorAll(".erpw-report-shell, .erpw-list-shell, .erpw-procurement-po-follow-up-shell, .erpw-procurement-review-shell, .erpw-procurement-supplier-detail-shell, .erpw-procurement-item-detail-shell")).filter(visible).length, horizontalOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth };
  }, type);
}
async function checkFilterPage(page, item, type, user, viewport) {
  await openPage(page, item.route, type === "report" ? ".erpw-report-shell" : ".erpw-list-shell");
  const data = await measure(page, type);
  assert(data.horizontalOverflow <= 1, `${item.label}: horizontal overflow at ${viewport.key}`, data);
  assert(data.action && !data.actionClipped, `${item.label}: clipped action group at ${viewport.key}`, data);
  assert(data.clippedButtons.length === 0, `${item.label}: clipped action button at ${viewport.key}`, data);
  assert(data.clippedFields.length === 0, `${item.label}: clipped filter field at ${viewport.key}`, data);
  for (const label of ["Apply", "Reset", "Refresh"]) {
    await page.locator(`${type === "report" ? ".erpw-report-command-actions" : ".erpw-list-toolbar-actions"} button:has-text("${label}")`).first().click();
    await page.waitForTimeout(220);
  }
  await page.screenshot({ path: path.join(ARTIFACT_DIR, `${user.key}-${viewport.key}-${safe(item.key)}.png`), fullPage: true });
  return data;
}
async function waitForSingleShell(page) {
  await page.waitForFunction(() => {
    const visible = (node) => {
      const style = getComputedStyle(node);
      const box = node.getBoundingClientRect();
      return style.display !== "none" && style.visibility !== "hidden" && box.width > 0 && box.height > 0;
    };
    return Array.from(document.querySelectorAll(".erpw-report-shell, .erpw-list-shell, .erpw-procurement-po-follow-up-shell, .erpw-procurement-review-shell, .erpw-procurement-supplier-detail-shell, .erpw-procurement-item-detail-shell")).filter(visible).length === 1;
  }, { timeout: TIMEOUT });
}
async function checkStaticPage(page, item, user, viewport) {
  await openPage(page, item.route, item.shell);
  await waitForSingleShell(page);
  const data = await measure(page, "detail");
  assert(data.horizontalOverflow <= 1, `${item.label}: horizontal overflow at ${viewport.key}`, data);
  assert(data.shellCount === 1, `${item.label}: duplicate shell at ${viewport.key}`, data);
  await page.screenshot({ path: path.join(ARTIFACT_DIR, `${user.key}-${viewport.key}-${safe(item.key)}.png`), fullPage: true });
  return data;
}
async function runUser(user) {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const errors = [];
  const failures = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (msg) => { if (msg.type() === "error") errors.push(msg.text()); });
  page.on("response", (response) => { if (response.status() >= 400 && !/favicon|manifest|socket.io/.test(response.url())) failures.push({ url: response.url(), status: response.status() }); });
  const measurements = [];
  try {
    await page.setViewportSize({ width: 1240, height: 768 });
    await login(page, user);
    const details = await resolveDetails(page);
    for (const viewport of VIEWPORTS) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      for (const [key, label, route, hasFilter] of REPORTS) {
        await openPage(page, route, ".erpw-report-shell");
        const data = await measure(page, "report");
        assert(data.horizontalOverflow <= 1, `${label}: horizontal overflow at ${viewport.key}`, data);
        if (hasFilter) {
          assert(data.action && !data.actionClipped, `${label}: clipped action group at ${viewport.key}`, data);
          assert(data.clippedButtons.length === 0, `${label}: clipped action button at ${viewport.key}`, data);
          assert(data.clippedFields.length === 0, `${label}: clipped filter field at ${viewport.key}`, data);
          for (const actionLabel of ["Apply", "Reset", "Refresh"]) { await page.locator(`.erpw-report-command-actions button:has-text("${actionLabel}")`).first().click(); await page.waitForTimeout(220); }
        }
        await page.screenshot({ path: path.join(ARTIFACT_DIR, `${user.key}-${viewport.key}-${safe(key)}.png`), fullPage: true });
        measurements.push({ user: user.key, viewport: viewport.key, type: "report", key, data });
      }
      for (const [key, label, route] of WORKLISTS) measurements.push({ user: user.key, viewport: viewport.key, type: "worklist", key, data: await checkFilterPage(page, { key, label, route }, "list", user, viewport) });
      if (viewport.key === "desktop-1240") for (const detail of details) measurements.push({ user: user.key, viewport: viewport.key, type: "detail", key: detail.key, data: await checkStaticPage(page, detail, user, viewport) });
    }
    assert(failures.length === 0, `${user.key}: failed network responses`, { failures });
    assert(errors.length === 0, `${user.key}: page JS errors`, { errors });
    fs.writeFileSync(path.join(ARTIFACT_DIR, `${user.key}-measurements.json`), JSON.stringify(measurements, null, 2));
    await browser.close();
    return { user: user.key, measurements: measurements.length };
  } catch (error) {
    fs.writeFileSync(path.join(ARTIFACT_DIR, `${user.key}-partial-measurements.json`), JSON.stringify(measurements, null, 2));
    await page.screenshot({ path: path.join(ARTIFACT_DIR, `${user.key}-failure.png`), fullPage: true }).catch(() => {});
    await browser.close();
    error.message = `${user.key}: ${error.message}`;
    throw error;
  }
}
(async () => {
  assert(USERS.length > 0, "No smoke users configured");
  const results = [];
  for (const user of USERS) results.push(await runUser(user));
  fs.writeFileSync(path.join(ARTIFACT_DIR, "summary.json"), JSON.stringify({ ok: true, users: results, viewports: VIEWPORTS }, null, 2));
  console.log(JSON.stringify({ ok: true, artifactDir: ARTIFACT_DIR, users: results }, null, 2));
})().catch((error) => { console.error(error && error.stack || error); process.exit(1); });
