const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const OUT_DIR = process.env.ERPW_SALES_ORDER_ANALYSIS_OUT || path.join(process.env.TEMP || process.cwd(), "erpw-sales-order-analysis-smoke");
const TIMEOUT = Number(process.env.ERPW_SALES_ORDER_ANALYSIS_TIMEOUT || 60000);
const REPORT_ROUTE = process.env.ERPW_SALES_ORDER_ANALYSIS_ROUTE || "/desk/sales-console-report/sales-order-analysis";
const REPORT_METHOD = "erp_workspace_ui.sales_console.report.get_sales_console_report_context";
const EXPECTED_SHELL_VERSION = process.env.ERPW_REPORT_SHELL_VERSION || "";
const APPLY_FROM_DATE = process.env.ERPW_SALES_ORDER_ANALYSIS_FROM || "2026-04-01";
const APPLY_TO_DATE = process.env.ERPW_SALES_ORDER_ANALYSIS_TO || "2026-04-30";

const USERS = [
  {
    key: "manager",
    label: "Sales Manager",
    username: process.env.ERPW_MANAGER_USERNAME,
    password: process.env.ERPW_MANAGER_PASSWORD,
  },
  {
    key: "user",
    label: "Sales User",
    username: process.env.ERPW_USER_USERNAME,
    password: process.env.ERPW_USER_PASSWORD,
  },
];

function requireValue(value, name) {
  if (!value) throw new Error(`Missing ${name}`);
  return value;
}

function assert(condition, message, details = {}) {
  if (!condition) {
    const error = new Error(message);
    error.details = details;
    throw error;
  }
}

function normalizeText(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function routeUrl(route) {
  return new URL(route, BASE_URL).toString();
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

async function login(page, user) {
  await page.goto(routeUrl("/login"), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  const userField = page.locator("#login_email, input[name='usr'], input[name='login_email'], input[type='email'], input[type='text']").first();
  const passwordField = page.locator("#login_password, input[name='pwd'], input[name='login_password'], input[type='password']").first();
  const loginButton = page.locator("button:has-text('Login'), button.btn-login, .btn-login").first();

  await userField.waitFor({ state: "visible", timeout: TIMEOUT });
  await userField.fill(user.username);
  await passwordField.fill(user.password);
  await Promise.all([
    page.waitForURL(/\/(?:app|desk)(?:[/?#]|$)/, { timeout: TIMEOUT }),
    loginButton.click(),
  ]);
}

async function openReport(page) {
  await page.goto(routeUrl(REPORT_ROUTE), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  if (/\/login(?:[/?#]|$)/.test(page.url())) {
    throw new Error(`Route ${REPORT_ROUTE} redirected to login`);
  }
  await page.waitForFunction(() => Boolean(window.frappe), null, { timeout: TIMEOUT });
  await page.locator(".erpw-report-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  await page.locator("[data-erpw-control-key='from_date']").waitFor({ state: "visible", timeout: TIMEOUT });
  if (EXPECTED_SHELL_VERSION) {
    await page.waitForFunction((expected) => {
      const runtime = window.erpWorkspaceUiReportPage && window.erpWorkspaceUiReportPage.shell;
      return runtime && runtime.version === expected;
    }, EXPECTED_SHELL_VERSION, { timeout: TIMEOUT });
  }
}

async function waitForReportContext(page, predicate) {
  const response = await page.waitForResponse((res) => {
    if (!res.url().includes(`/api/method/${REPORT_METHOD}`)) return false;
    if (res.request().method() !== "POST") return false;
    const args = extractArgs(res.request().postData() || "");
    if (args.report_key !== "sales_order_analysis") return false;
    return predicate ? predicate(args) : true;
  }, { timeout: TIMEOUT });
  return extractArgs(response.request().postData() || "");
}

async function snapshot(page) {
  return page.evaluate(() => {
    const isVisible = (node) => {
      const style = window.getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
    };
    const fields = Array.from(document.querySelectorAll("[data-erpw-control-key]"));
    const actions = Array.from(document.querySelectorAll("[data-erpw-report-action-key]")).filter(isVisible);
    const buttons = Array.from(document.querySelectorAll(".erpw-report-control-button")).filter(isVisible);
    const runtime = window.erpWorkspaceUiReportPage && window.erpWorkspaceUiReportPage.shell;
    return {
      url: location.href,
      title: (document.querySelector(".erpw-report-title") || {}).textContent || "",
      shellVersion: runtime ? runtime.version : "",
      formClass: (document.querySelector("form") || {}).className || "",
      fields: fields.map((node) => ({
        key: node.getAttribute("data-erpw-control-key"),
        value: node.value,
        tag: node.tagName,
        type: node.type || "",
      })),
      actions: actions.map((node) => ({
        key: node.getAttribute("data-erpw-report-action-key"),
        text: node.textContent.replace(/\s+/g, " ").trim(),
      })),
      buttons: buttons.map((node) => node.textContent.replace(/\s+/g, " ").trim()),
      tableRows: document.querySelectorAll(".erpw-report-results tbody tr, .erpw-report-table tbody tr").length,
      stateText: (document.querySelector(".erpw-report-state-title") || {}).textContent || "",
    };
  });
}

function fieldValue(snapshotData, key) {
  const field = snapshotData.fields.find((item) => item.key === key);
  return field ? field.value : "";
}

async function runRole(browser, user) {
  requireValue(user.username, `${user.key} username`);
  requireValue(user.password, `${user.key} password`);

  const context = await browser.newContext({
    baseURL: BASE_URL,
    ignoreHTTPSErrors: true,
    viewport: { width: 1440, height: 1000 },
  });
  const page = await context.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });
  page.on("pageerror", (error) => pageErrors.push(error.message));

  try {
    await login(page, user);
    await openReport(page);
    const initial = await snapshot(page);
    const defaultFromDate = fieldValue(initial, "from_date");
    const defaultToDate = fieldValue(initial, "to_date");

    assert(normalizeText(initial.title) === "Sales Order Analysis", `${user.label}: wrong report title`, initial);
    assert(!EXPECTED_SHELL_VERSION || initial.shellVersion === EXPECTED_SHELL_VERSION, `${user.label}: unexpected report shell version`, initial);
    assert(initial.formClass.includes("erpw-report-command-panel"), `${user.label}: compact command panel missing`, initial);
    assert(defaultFromDate && defaultToDate, `${user.label}: date fields missing`, initial);
    assert(initial.buttons.includes("Apply") && initial.buttons.includes("Reset"), `${user.label}: apply/reset buttons missing`, initial);
    assert(
      initial.actions.map((action) => action.key).slice(0, 2).join(",") === "refresh,back_to_console",
      `${user.label}: report action order mismatch`,
      initial
    );

    await page.locator("[data-erpw-control-key='from_date']").fill(APPLY_FROM_DATE);
    await page.locator("[data-erpw-control-key='to_date']").fill(APPLY_TO_DATE);
    const applyArgsPromise = waitForReportContext(page, (args) => {
      const overrides = args.filter_overrides || {};
      return overrides.from_date === APPLY_FROM_DATE && overrides.to_date === APPLY_TO_DATE;
    });
    await page.locator("button[type='submit']:has-text('Apply')").click();
    const applyArgs = await applyArgsPromise;
    await page.waitForFunction(([fromDate, toDate]) => {
      const from = document.querySelector("[data-erpw-control-key='from_date']");
      const to = document.querySelector("[data-erpw-control-key='to_date']");
      return from && to && from.value === fromDate && to.value === toDate;
    }, [APPLY_FROM_DATE, APPLY_TO_DATE], { timeout: TIMEOUT });
    const afterApply = await snapshot(page);

    assert(!/[?]$/.test(page.url()), `${user.label}: apply caused native query reload`, { url: page.url() });
    assert(fieldValue(afterApply, "from_date") === APPLY_FROM_DATE, `${user.label}: from date did not persist after apply`, afterApply);
    assert(fieldValue(afterApply, "to_date") === APPLY_TO_DATE, `${user.label}: to date did not persist after apply`, afterApply);

    const resetArgsPromise = waitForReportContext(page, (args) => !args.filter_overrides);
    await page.locator(".erpw-report-control-reset:has-text('Reset')").click();
    const resetArgs = await resetArgsPromise;
    await page.waitForFunction(([fromDate, toDate]) => {
      const from = document.querySelector("[data-erpw-control-key='from_date']");
      const to = document.querySelector("[data-erpw-control-key='to_date']");
      return from && to && from.value === fromDate && to.value === toDate;
    }, [defaultFromDate, defaultToDate], { timeout: TIMEOUT });
    const afterReset = await snapshot(page);

    assert(!/[?]$/.test(page.url()), `${user.label}: reset caused native query reload`, { url: page.url() });
    assert(pageErrors.length === 0, `${user.label}: page JS error`, { pageErrors });
    const relevantConsoleErrors = consoleErrors.filter((text) => !/favicon|socket|manifest|Invalid origin/i.test(text));
    assert(relevantConsoleErrors.length === 0, `${user.label}: browser console error`, { consoleErrors: relevantConsoleErrors });

    return {
      role: user.label,
      status: "passed",
      defaults: { from_date: defaultFromDate, to_date: defaultToDate },
      applyOverrides: applyArgs.filter_overrides,
      resetPostedOverrides: resetArgs.filter_overrides || null,
      urlAfterApply: afterApply.url,
      urlAfterReset: afterReset.url,
      tableRowsAfterApply: afterApply.tableRows,
      stateAfterApply: normalizeText(afterApply.stateText),
      actions: initial.actions,
    };
  } catch (error) {
    await page.screenshot({ path: path.join(OUT_DIR, `${user.key}-sales-order-analysis-failure.png`), fullPage: true }).catch(() => {});
    throw Object.assign(error, { roleReport: { role: user.label, status: "failed", error: error.message, details: error.details || null } });
  } finally {
    await context.close();
  }
}

(async () => {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const browser = await chromium.launch({ headless: process.env.ERPW_HEADLESS !== "0" });
  const reports = [];
  try {
    for (const user of USERS) {
      const report = await runRole(browser, user);
      reports.push(report);
      console.log(`[pass] ${user.label}`);
    }
  } catch (error) {
    if (error.roleReport) reports.push(error.roleReport);
    console.error(`[fail] ${error.message}`);
    if (error.details) console.error(JSON.stringify(error.details, null, 2));
    process.exitCode = 1;
  } finally {
    await browser.close();
    const outputPath = path.join(OUT_DIR, "sales-order-analysis-report.json");
    fs.writeFileSync(outputPath, `${JSON.stringify(reports, null, 2)}\n`, "utf8");
    console.log(`report=${outputPath}`);
  }
})();
