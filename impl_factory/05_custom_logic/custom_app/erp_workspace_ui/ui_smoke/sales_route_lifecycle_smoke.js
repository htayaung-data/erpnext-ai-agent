const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const OUT_DIR = process.env.ERPW_CAPTURE_ROOT || path.join(process.cwd(), "artifacts", "sales-route-lifecycle-smoke");
const TIMEOUT = Number(process.env.ERPW_ROUTE_LIFECYCLE_TIMEOUT || 60000);
const WORKLIST_METHOD = "erp_workspace_ui.sales_console.worklist.get_sales_console_worklist_context";

const USER = {
  label: "Sales Manager",
  username: process.env.ERPW_MANAGER_USERNAME || process.env.ERPW_USERNAME,
  password: process.env.ERPW_MANAGER_PASSWORD || process.env.ERPW_PASSWORD,
};

function requireValue(value, name) {
  if (!value) throw new Error(`Missing ${name}`);
  return value;
}

function normalizeText(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function routeUrl(route) {
  return new URL(route, BASE_URL).toString();
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function safeFileKey(value) {
  return String(value || "step").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "step";
}

function assert(condition, message, details = {}) {
  if (!condition) {
    const error = new Error(message);
    error.details = details;
    throw error;
  }
}

async function login(page) {
  await page.goto(routeUrl("/login"), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  const userField = page.locator("#login_email, input[name='usr'], input[name='login_email'], input[type='email'], input[type='text']").first();
  const passwordField = page.locator("#login_password, input[name='pwd'], input[name='login_password'], input[type='password']").first();
  const loginButton = page.locator("button:has-text('Login'), button.btn-login, .btn-login").first();
  await userField.waitFor({ state: "visible", timeout: TIMEOUT });
  await userField.fill(USER.username);
  await passwordField.fill(USER.password);
  await Promise.all([
    page.waitForURL(/\/(?:app|desk)(?:[/?#]|$)/, { waitUntil: "domcontentloaded", timeout: TIMEOUT }),
    loginButton.click(),
  ]);
  await page.waitForFunction(() => Boolean(window.frappe), null, { timeout: TIMEOUT });
}

async function callMethod(page, method, args = {}) {
  return page.evaluate(
    async ({ method, args }) => {
      const body = new URLSearchParams();
      for (const [key, value] of Object.entries(args || {})) {
        body.set(key, typeof value === "string" ? value : JSON.stringify(value));
      }
      const response = await fetch(`/api/method/${method}`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
          "X-Frappe-CSRF-Token": (window.frappe && window.frappe.csrf_token) || "",
        },
        body,
      });
      let data = null;
      try {
        data = await response.json();
      } catch (error) {
        data = { raw: await response.text() };
      }
      return { ok: response.ok, status: response.status, data };
    },
    { method, args }
  );
}

function firstCustomer(payload) {
  const rows = (((payload || {}).results || {}).rows || []);
  const targets = (payload || {}).action_targets || {};
  for (const row of rows) {
    const target = targets[`row:${row.key}:open_record`];
    const customer = target && target.filters && target.filters.customer;
    if (customer) return customer;
  }
  return rows[0] && rows[0].key ? String(rows[0].key) : "";
}

async function getCustomerSeed(page) {
  const response = await callMethod(page, WORKLIST_METHOD, { queue_key: "customer_directory" });
  assert(response.ok, "Customer directory context failed", response);
  const payload = response.data && response.data.message ? response.data.message : response.data;
  const customer = firstCustomer(payload);
  assert(customer, "No visible customer seed found for lifecycle detail smoke", {
    rowCount: payload && payload.results && Array.isArray(payload.results.rows) ? payload.results.rows.length : 0,
  });
  return customer;
}

async function waitForKind(page, kind) {
  await page.waitForFunction(() => Boolean(window.frappe), null, { timeout: TIMEOUT });
  const selectors = {
    overview: ".sales-console-shell",
    worklist: ".erpw-list-shell",
    report: ".erpw-report-shell",
    detail: ".erpw-list-shell",
  };
  await page.locator(selectors[kind]).first().waitFor({ state: "visible", timeout: TIMEOUT });
  await page.waitForFunction((expectedKind) => {
    const visible = (node) => {
      if (!node) return false;
      const style = window.getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
    };
    const count = (selector) => Array.from(document.querySelectorAll(selector)).filter(visible).length;
    if (expectedKind === "overview") return count(".sales-console-shell") === 1;
    if (expectedKind === "report") return count(".erpw-report-shell") === 1;
    return count(".erpw-list-shell") === 1;
  }, kind, { timeout: TIMEOUT });
  await page.waitForLoadState("networkidle", { timeout: 5000 }).catch(() => null);
}

async function snapshot(page) {
  return page.evaluate(() => {
    const visible = (node) => {
      if (!node) return false;
      const style = window.getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
    };
    const count = (selector) => Array.from(document.querySelectorAll(selector)).filter(visible).length;
    const text = (selector) => Array.from(document.querySelectorAll(selector)).filter(visible).map((node) => node.textContent.replace(/\s+/g, " ").trim()).filter(Boolean);
    return {
      url: window.location.href,
      route: window.frappe && window.frappe.get_route ? window.frappe.get_route() : [],
      counts: {
        overviewShell: count(".sales-console-shell"),
        listShell: count(".erpw-list-shell"),
        reportShell: count(".erpw-report-shell"),
        childShell: count(".erpw-child-shell"),
        childDraft: count(".erpw-child-draft-page"),
        formPage: count(".form-page"),
        pageHead: count(".page-head"),
        pageTitles: count(".page-title .title-text, .title-area .title-text"),
        worklistHosts: count(".erpw-sales-console-worklist-page"),
        reportHosts: count(".erpw-sales-console-report-page"),
      },
      titles: {
        frappe: text(".page-title .title-text, .title-area .title-text").slice(0, 6),
        overview: text(".sales-console-title").slice(0, 3),
        list: text(".erpw-list-title").slice(0, 3),
        report: text(".erpw-report-title").slice(0, 3),
      },
    };
  });
}

async function assertNoStack(page, kind, label, report) {
  const snap = await snapshot(page);
  const counts = snap.counts;
  const activeManagedShells = counts.overviewShell + counts.listShell + counts.reportShell;
  const visibleTitles = [
    ...(snap.titles.frappe || []),
    ...(snap.titles.overview || []),
    ...(snap.titles.list || []),
    ...(snap.titles.report || []),
  ].filter(Boolean);
  if (visibleTitles.some((title) => /sales-console-worklist|sales-console-report|sales console worklist|sales console report/i.test(title))) {
    report.titleWarnings.push({ label, titles: visibleTitles });
  }
  if (kind === "overview") {
    assert(counts.overviewShell === 1, `${label}: expected one overview shell`, snap);
    assert(counts.listShell === 0 && counts.reportShell === 0, `${label}: stale list/report shell visible on overview`, snap);
  } else if (kind === "report") {
    assert(counts.reportShell === 1, `${label}: expected one report shell`, snap);
    assert(counts.overviewShell === 0 && counts.listShell === 0, `${label}: stale overview/list shell visible on report`, snap);
  } else {
    assert(counts.listShell === 1, `${label}: expected one worklist/detail shell`, snap);
    assert(counts.overviewShell === 0 && counts.reportShell === 0, `${label}: stale overview/report shell visible on worklist/detail`, snap);
  }
  assert(activeManagedShells === 1, `${label}: active managed shell count is not one`, snap);
  assert(counts.formPage === 0, `${label}: native form chrome is visible on productized route`, snap);
  assert(counts.pageHead <= 1, `${label}: duplicate page heads visible`, snap);
  const stepNumber = String(report.steps.length + 1).padStart(2, "0");
  const screenshot = path.join(OUT_DIR, `${stepNumber}-${safeFileKey(label)}.png`);
  await page.screenshot({ path: screenshot, fullPage: true });
  report.steps.push({ label, kind, snapshot: snap, screenshot });
  report.screenshots.push(screenshot);
  return snap;
}

async function openRoute(page, route, kind, label, report) {
  await page.goto(routeUrl(route), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  if (/\/login(?:[/?#]|$)/.test(page.url())) throw new Error(`${label}: redirected to login`);
  await waitForKind(page, kind);
  return assertNoStack(page, kind, label, report);
}

async function captureHomeLanding(page, report) {
  await page.goto(routeUrl("/desk/sales-console-home"), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  if (/\/login(?:[/?#]|$)/.test(page.url())) throw new Error("Sales home first landing: redirected to login");

  const captures = [];
  let elapsed = 0;
  for (const point of [
    { label: "0.3s", wait: 300 },
    { label: "1.7s", wait: 1400 },
    { label: "5.7s", wait: 4000 },
  ]) {
    await page.waitForTimeout(point.wait);
    elapsed += point.wait;
    const snap = await snapshot(page);
    const screenshot = path.join(OUT_DIR, `sales-home-first-landing-${point.label.replace(/[^0-9a-z]+/gi, "-")}.png`);
    await page.screenshot({ path: screenshot, fullPage: true });
    captures.push({ label: point.label, elapsedMs: elapsed, snapshot: snap, screenshot });
    report.screenshots.push(screenshot);
  }

  const final = captures[captures.length - 1].snapshot;
  const bodyText = normalizeText(await page.locator("body").innerText({ timeout: 5000 }).catch(() => ""));
  assert(final.counts.overviewShell === 1, "Sales home first landing: overview shell not visible at 5.7s", { final, bodyText });
  assert(final.counts.listShell === 0 && final.counts.reportShell === 0, "Sales home first landing: stale non-overview shell visible", final);
  assert(/Sales Console/i.test(bodyText), "Sales home first landing: overview content missing", { final, bodyText });

  await waitForKind(page, "overview");
  const stackSnapshot = await assertNoStack(page, "overview", "Sales home first landing", report);
  report.homeLanding = { captures, stackSnapshot };
  return stackSnapshot;
}

async function clickSidebar(page, label, kind, expectedPath, report) {
  const link = page.locator(".erpw-sales-console-sidebar-link").filter({ hasText: label }).first();
  await link.waitFor({ state: "visible", timeout: TIMEOUT });
  await link.click();
  await page.waitForFunction((path) => window.location.pathname.includes(path), expectedPath, { timeout: TIMEOUT });
  await waitForKind(page, kind);
  return assertNoStack(page, kind, `Sidebar ${label}`, report);
}

function relevantConsoleErrors(entries) {
  return entries.filter((entry) => {
    const text = `${entry.text || ""} ${entry.location && entry.location.url ? entry.location.url : ""}`;
    return !/favicon|socket|manifest|Invalid origin|ResizeObserver loop/i.test(text);
  });
}

async function main() {
  requireValue(USER.username, "Sales Manager username");
  requireValue(USER.password, "Sales Manager password");
  ensureDir(OUT_DIR);
  const browser = await chromium.launch({ headless: process.env.ERPW_HEADLESS !== "0" });
  const report = { baseUrl: BASE_URL, outDir: OUT_DIR, steps: [], screenshots: [], titleWarnings: [] };
  const context = await browser.newContext({ baseURL: BASE_URL, ignoreHTTPSErrors: true, viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push({ text: msg.text(), location: msg.location() || {} });
  });
  page.on("pageerror", (error) => pageErrors.push(error.message || String(error)));

  try {
    await login(page);
    await captureHomeLanding(page, report);
    const customer = await getCustomerSeed(page);
    const customerRoute = `/desk/sales-console-worklist/customer-detail/${encodeURIComponent(customer)}`;

    await openRoute(page, "/desk/sales-console", "overview", "Direct overview", report);
    await clickSidebar(page, "Quotations", "worklist", "/sales-console-worklist/quotation-directory", report);
    await clickSidebar(page, "Sales Orders", "worklist", "/sales-console-worklist/sales-order-directory", report);
    await clickSidebar(page, "Customers", "worklist", "/sales-console-worklist/customer-directory", report);
    await clickSidebar(page, "Items", "worklist", "/sales-console-worklist/item-directory", report);
    await clickSidebar(page, "Overview", "overview", "/sales-console", report);
    await clickSidebar(page, "Quotations", "worklist", "/sales-console-worklist/quotation-directory", report);

    await openRoute(page, "/desk/sales-console", "overview", "Sequence overview", report);
    await openRoute(page, "/desk/sales-console-worklist/customer-directory", "worklist", "Sequence worklist", report);
    await openRoute(page, "/desk/sales-console-report/sales-order-analysis", "report", "Sequence report", report);
    await openRoute(page, customerRoute, "detail", "Sequence customer detail", report);

    await page.goBack({ waitUntil: "domcontentloaded", timeout: TIMEOUT });
    await waitForKind(page, "report");
    await assertNoStack(page, "report", "Back to report", report);

    await page.goBack({ waitUntil: "domcontentloaded", timeout: TIMEOUT });
    await waitForKind(page, "worklist");
    await assertNoStack(page, "worklist", "Back to worklist", report);

    await page.goForward({ waitUntil: "domcontentloaded", timeout: TIMEOUT });
    await waitForKind(page, "report");
    await assertNoStack(page, "report", "Forward to report", report);

    await openRoute(page, customerRoute, "detail", "Direct customer detail", report);
    await page.reload({ waitUntil: "domcontentloaded", timeout: TIMEOUT });
    await waitForKind(page, "detail");
    await assertNoStack(page, "detail", "Refresh customer detail", report);

    await page.screenshot({ path: path.join(OUT_DIR, "sales-route-lifecycle-final.png"), fullPage: true });
    report.screenshots.push(path.join(OUT_DIR, "sales-route-lifecycle-final.png"));

    const filteredConsoleErrors = relevantConsoleErrors(consoleErrors);
    report.consoleErrors = filteredConsoleErrors;
    report.pageErrors = pageErrors;
    report.runtimeWarnings = [
      ...filteredConsoleErrors.map((entry) => ({ kind: "console", text: entry.text, location: entry.location || {} })),
      ...pageErrors.map((text) => ({ kind: "pageerror", text })),
    ];
    fs.writeFileSync(path.join(OUT_DIR, "sales-route-lifecycle-report.json"), JSON.stringify(report, null, 2));
    console.log(JSON.stringify({ outDir: OUT_DIR, steps: report.steps.length, customer }, null, 2));
  } catch (error) {
    report.error = error.message || String(error);
    report.errorDetails = error.details || null;
    await page.screenshot({ path: path.join(OUT_DIR, "sales-route-lifecycle-failure.png"), fullPage: true }).catch(() => null);
    fs.writeFileSync(path.join(OUT_DIR, "sales-route-lifecycle-report.json"), JSON.stringify(report, null, 2));
    throw error;
  } finally {
    await context.close().catch(() => null);
    await browser.close().catch(() => null);
  }
}

main().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exit(1);
});
