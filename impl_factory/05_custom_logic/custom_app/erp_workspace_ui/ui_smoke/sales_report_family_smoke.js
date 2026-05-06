const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const OUT_DIR = process.env.ERPW_SALES_REPORTS_OUT || path.join(process.cwd(), "artifacts", "sales-report-family-smoke");
const TIMEOUT = Number(process.env.ERPW_SALES_REPORTS_TIMEOUT || 70000);
const REPORT_METHOD = "erp_workspace_ui.sales_console.report.get_sales_console_report_context";
const APPLY_FROM_DATE = process.env.ERPW_SALES_REPORTS_FROM || "2026-04-01";
const APPLY_TO_DATE = process.env.ERPW_SALES_REPORTS_TO || "2026-04-30";

const USER = {
  label: "Sales Manager",
  username: process.env.ERPW_MANAGER_USERNAME || process.env.ERPW_USERNAME,
  password: process.env.ERPW_MANAGER_PASSWORD || process.env.ERPW_PASSWORD,
};

const REPORTS = [
  { key: "sales_analytics", title: "Sales Analytics", route: "/desk/sales-console-report/sales-analytics" },
  { key: "sales_order_analysis", title: "Sales Order Analysis", route: "/desk/sales-console-report/sales-order-analysis", changeDates: true },
  { key: "trend_analysis", title: "Trend Analysis", route: "/desk/sales-console-report/trend-analysis" },
  { key: "collections_status", title: "Collections Status", route: "/desk/sales-console-report/collections-status" },
  { key: "item_wise_sales_history", title: "Item-wise Sales History", route: "/desk/sales-console-report/item-wise-sales-history" },
];

const VALID_STATE_KINDS = new Set(["ready", "empty", "restricted", "unavailable", "error"]);

function requireValue(value, name) {
  if (!value) throw new Error(`Missing ${name}`);
  return value;
}

function routeUrl(route) {
  return new URL(route, BASE_URL).toString();
}

function normalizeText(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function safeFileKey(value) {
  return String(value || "report").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "report";
}

function assert(condition, message, details = {}) {
  if (!condition) {
    const error = new Error(message);
    error.details = details;
    throw error;
  }
}

function extractArgs(postData) {
  const params = new URLSearchParams(postData || "");
  const args = {};
  for (const [key, value] of params.entries()) {
    if (key === "filter_overrides") {
      try {
        args[key] = JSON.parse(value);
      } catch (error) {
        args[key] = value;
      }
    } else {
      args[key] = value;
    }
  }
  return args;
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

async function waitForReportContext(page, reportKey, predicate) {
  const response = await page.waitForResponse((res) => {
    if (!res.url().includes(`/api/method/${REPORT_METHOD}`)) return false;
    if (res.request().method() !== "POST") return false;
    const args = extractArgs(res.request().postData() || "");
    if (args.report_key !== reportKey) return false;
    return predicate ? predicate(args) : true;
  }, { timeout: TIMEOUT });
  assert(response.ok(), `${reportKey}: report context response failed`, { status: response.status(), url: response.url() });
  return extractArgs(response.request().postData() || "");
}

async function openReport(page, report) {
  const responsePromise = waitForReportContext(page, report.key).catch(() => null);
  await page.goto(routeUrl(report.route), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  if (/\/login(?:[/?#]|$)/.test(page.url())) throw new Error(`${report.key}: redirected to login`);
  await responsePromise;
  await page.locator(".erpw-report-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  await page.waitForFunction(() => {
    const shell = document.querySelector(".erpw-report-shell");
    return shell && shell.getAttribute("aria-busy") !== "true";
  }, null, { timeout: TIMEOUT });
}

async function snapshot(page) {
  return page.evaluate(() => {
    const visible = (node) => {
      if (!node) return false;
      const style = window.getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
    };
    const stateNode = document.querySelector(".erpw-report-state");
    const stateKind = stateNode
      ? Array.from(stateNode.classList).find((name) => name !== "erpw-report-state") || ""
      : "ready";
    const fields = Array.from(document.querySelectorAll("[data-erpw-control-key]"));
    const actions = Array.from(document.querySelectorAll("[data-erpw-report-action-key]")).filter(visible);
    return {
      url: window.location.href,
      path: window.location.pathname,
      title: (document.querySelector(".erpw-report-title") || {}).textContent || "",
      stateKind,
      stateTitle: (document.querySelector(".erpw-report-state-title") || {}).textContent || "",
      fields: fields.map((node) => ({
        key: node.getAttribute("data-erpw-control-key"),
        value: node.value || "",
        tag: node.tagName,
        type: node.type || "",
      })),
      buttons: Array.from(document.querySelectorAll(".erpw-report-control-button")).filter(visible).map((node) => node.textContent.replace(/\s+/g, " ").trim()),
      actions: actions.map((node) => ({
        key: node.getAttribute("data-erpw-report-action-key"),
        text: node.textContent.replace(/\s+/g, " ").trim(),
      })),
      tableRows: document.querySelectorAll(".erpw-report-table tbody tr").length,
      cellLinks: document.querySelectorAll(".erpw-report-cell-link").length,
      shellCount: Array.from(document.querySelectorAll(".erpw-report-shell")).filter(visible).length,
      pageHeadCount: Array.from(document.querySelectorAll(".page-head")).filter(visible).length,
      companyFieldCount: document.querySelectorAll('[data-erpw-control-key="company"]').length,
      rawReportCount: Array.from(document.querySelectorAll(".query-report, .report-wrapper, .dt-scrollable")).filter(visible).length,
    };
  });
}

function valuesByKey(snap) {
  const values = {};
  for (const field of snap.fields || []) values[field.key] = field.value;
  return values;
}

async function assertNoFullReload(page, label, action) {
  const marker = `${Date.now()}-${Math.random()}`;
  const before = await page.evaluate((value) => {
    window.__erpwReportSmokeMarker = value;
    return {
      marker: window.__erpwReportSmokeMarker,
      navCount: performance.getEntriesByType("navigation").length,
      path: window.location.pathname,
    };
  }, marker);
  await action();
  const after = await page.evaluate(() => ({
    marker: window.__erpwReportSmokeMarker,
    navCount: performance.getEntriesByType("navigation").length,
    path: window.location.pathname,
  }));
  assert(after.marker === before.marker, `${label}: page context was replaced`, { before, after });
  assert(after.navCount === before.navCount, `${label}: full page navigation count changed`, { before, after });
  assert(after.path === before.path, `${label}: route path changed`, { before, after });
}

async function waitUntilNotBusy(page) {
  await page.waitForFunction(() => {
    const shell = document.querySelector(".erpw-report-shell");
    return shell && shell.getAttribute("aria-busy") !== "true";
  }, null, { timeout: TIMEOUT });
}

async function clickApply(page, report, predicate) {
  const argsPromise = waitForReportContext(page, report.key, predicate);
  await page.locator("button[type='submit']:has-text('Apply')").click();
  const args = await argsPromise;
  await waitUntilNotBusy(page);
  return args;
}

async function clickReset(page, report) {
  const argsPromise = waitForReportContext(page, report.key, (args) => !args.filter_overrides);
  await page.locator(".erpw-report-control-reset:has-text('Reset')").click();
  const args = await argsPromise;
  await waitUntilNotBusy(page);
  return args;
}

async function clickRefresh(page, report) {
  const argsPromise = waitForReportContext(page, report.key);
  await page.locator('[data-erpw-report-action-key="refresh"]:visible').first().click();
  const args = await argsPromise;
  await waitUntilNotBusy(page);
  return args;
}

async function runReport(page, report, output) {
  await openReport(page, report);
  const initial = await snapshot(page);
  const initialValues = valuesByKey(initial);

  assert(normalizeText(initial.title) === report.title, `${report.key}: wrong report title`, initial);
  assert(VALID_STATE_KINDS.has(initial.stateKind), `${report.key}: invalid state kind`, initial);
  assert(!["restricted", "unavailable", "error"].includes(initial.stateKind), `${report.key}: manager report did not load as review surface`, initial);
  assert(initial.shellCount === 1, `${report.key}: report shell count mismatch`, initial);
  assert(initial.pageHeadCount <= 1, `${report.key}: duplicate page header`, initial);
  assert(initial.companyFieldCount === 0, `${report.key}: company filter field should not be visible`, initial);
  assert(initial.rawReportCount === 0, `${report.key}: raw ERP report surface is visible`, initial);
  assert(initial.actions.some((item) => item.key === "refresh"), `${report.key}: Refresh action missing`, initial);
  assert(initial.actions.some((item) => item.key === "back_to_console"), `${report.key}: Back action missing`, initial);
  if (initial.fields.length) {
    assert(initial.buttons.includes("Apply"), `${report.key}: Apply button missing`, initial);
    assert(initial.buttons.includes("Reset"), `${report.key}: Reset button missing`, initial);
  }

  if (report.changeDates) {
    await page.locator('[data-erpw-control-key="from_date"]').fill(APPLY_FROM_DATE);
    await page.locator('[data-erpw-control-key="to_date"]').fill(APPLY_TO_DATE);
  }

  const applyPredicate = report.changeDates
    ? (args) => {
        const overrides = args.filter_overrides || {};
        return overrides.from_date === APPLY_FROM_DATE && overrides.to_date === APPLY_TO_DATE;
      }
    : null;
  const applyArgs = await assertNoFullReload(page, `${report.key} apply`, () => clickApply(page, report, applyPredicate));
  const afterApply = await snapshot(page);
  if (report.changeDates) {
    const applied = valuesByKey(afterApply);
    assert(applied.from_date === APPLY_FROM_DATE && applied.to_date === APPLY_TO_DATE, `${report.key}: date filters did not persist after Apply`, { applied });
  }

  await assertNoFullReload(page, `${report.key} reset`, () => clickReset(page, report));
  const afterReset = await snapshot(page);
  const resetValues = valuesByKey(afterReset);
  Object.keys(initialValues).forEach((key) => {
    assert(resetValues[key] === initialValues[key], `${report.key}: Reset did not restore ${key}`, { initialValues, resetValues });
  });

  await assertNoFullReload(page, `${report.key} refresh`, () => clickRefresh(page, report));
  const afterRefresh = await snapshot(page);
  assert(VALID_STATE_KINDS.has(afterRefresh.stateKind), `${report.key}: invalid state kind after Refresh`, afterRefresh);

  const screenshot = path.join(OUT_DIR, `${safeFileKey(report.key)}.png`);
  await page.screenshot({ path: screenshot, fullPage: true });
  output.reports[report.key] = {
    title: normalizeText(initial.title),
    stateKind: initial.stateKind,
    initialValues,
    afterApplyValues: valuesByKey(afterApply),
    afterResetValues: resetValues,
    afterRefreshState: afterRefresh.stateKind,
    tableRows: afterRefresh.tableRows,
    cellLinks: afterRefresh.cellLinks,
    applyPostedOverrides: applyArgs && applyArgs.filter_overrides ? applyArgs.filter_overrides : null,
    screenshot,
  };
}

(async () => {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  requireValue(USER.username, "Sales Manager username");
  requireValue(USER.password, "Sales Manager password");

  const browser = await chromium.launch({ headless: process.env.ERPW_HEADLESS !== "0" });
  const context = await browser.newContext({
    baseURL: BASE_URL,
    ignoreHTTPSErrors: true,
    viewport: { width: 1440, height: 1100 },
  });
  const page = await context.newPage();
  const consoleMessages = [];
  const pageErrors = [];
  page.on("console", (message) => {
    if (["error", "warning"].includes(message.type())) consoleMessages.push({ type: message.type(), text: message.text(), location: message.location() || {} });
  });
  page.on("pageerror", (error) => pageErrors.push(error.message));

  const output = {
    role: USER.label,
    username: USER.username,
    reports: {},
    consoleMessages,
    pageErrors,
  };

  try {
    await login(page);
    for (const report of REPORTS) {
      await runReport(page, report, output);
      console.log(`[pass] ${report.key}`);
    }
    const relevantConsoleErrors = consoleMessages.filter((entry) => {
      if (entry.type !== "error") return false;
      const text = String(entry.text || "");
      const url = String((entry.location || {}).url || "");
      const combined = `${text} ${url}`;
      if (/favicon|socket|manifest|Invalid origin/i.test(combined)) return false;
      if (/Failed to load resource: the server responded with a status of 400/i.test(text) && /socket\.io/i.test(url)) return false;
      return true;
    });
    assert(pageErrors.length === 0, "Sales report page JS errors detected", { pageErrors });
    assert(relevantConsoleErrors.length === 0, "Sales report console errors detected", { consoleErrors: relevantConsoleErrors });
    output.status = "passed";
  } catch (error) {
    output.status = "failed";
    output.error = error.message;
    output.details = error.details || null;
    await page.screenshot({ path: path.join(OUT_DIR, "failure.png"), fullPage: true }).catch(() => {});
    console.error(`[fail] ${error.message}`);
    if (error.details) console.error(JSON.stringify(error.details, null, 2));
    process.exitCode = 1;
  } finally {
    await context.close();
    await browser.close();
    fs.writeFileSync(path.join(OUT_DIR, "sales-report-family-report.json"), `${JSON.stringify(output, null, 2)}\n`, "utf8");
    console.log(`report=${path.join(OUT_DIR, "sales-report-family-report.json")}`);
  }
})();
