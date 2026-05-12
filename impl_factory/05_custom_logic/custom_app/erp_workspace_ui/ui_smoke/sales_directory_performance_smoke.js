const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const OUT_DIR = process.env.ERPW_SALES_PERFORMANCE_OUT || path.join(process.cwd(), "artifacts", "sales-directory-performance-smoke");
const TIMEOUT = Number(process.env.ERPW_SALES_PERFORMANCE_TIMEOUT || 60000);
const API_THRESHOLD_MS = Number(process.env.ERPW_SALES_DIRECTORY_API_THRESHOLD_MS || 900);
const SAMPLE_COUNT = Number(process.env.ERPW_SALES_DIRECTORY_PERF_SAMPLES || 3);
const METHOD_PATH = "/api/method/erp_workspace_ui.sales_console.worklist.get_sales_console_worklist_context";

const USER = {
  username: process.env.ERPW_MANAGER_USERNAME || process.env.ERPW_USERNAME,
  password: process.env.ERPW_MANAGER_PASSWORD || process.env.ERPW_PASSWORD,
};

const DIRECTORIES = [
  {
    key: "quotation_directory",
    title: "Quotations",
    route: "/desk/sales-console-worklist/quotation-directory",
    enforceApiThreshold: true,
  },
  {
    key: "sales_order_directory",
    title: "Sales Orders",
    route: "/desk/sales-console-worklist/sales-order-directory",
    enforceApiThreshold: true,
  },
  {
    key: "customer_directory",
    title: "Customers",
    route: "/desk/sales-console-worklist/customer-directory",
    enforceApiThreshold: false,
  },
  {
    key: "item_directory",
    title: "Items",
    route: "/desk/sales-console-worklist/item-directory",
    enforceApiThreshold: false,
  },
];

function requireValue(value, name) {
  if (!value) throw new Error(`Missing ${name}`);
  return value;
}

function routeUrl(route) {
  return new URL(route, BASE_URL).toString();
}

function safeFileKey(value) {
  return String(value || "artifact").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "artifact";
}

function average(values) {
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0;
}

function percentile(values, percentileValue) {
  if (!values.length) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const index = Math.min(sorted.length - 1, Math.ceil((percentileValue / 100) * sorted.length) - 1);
  return sorted[index];
}

function summarize(values) {
  return {
    samples: values.map((value) => Math.round(value)),
    avgMs: Math.round(average(values)),
    minMs: Math.round(Math.min(...values)),
    maxMs: Math.round(Math.max(...values)),
    p95Ms: Math.round(percentile(values, 95)),
  };
}

async function login(page) {
  requireValue(USER.username, "ERPW_MANAGER_USERNAME or ERPW_USERNAME");
  requireValue(USER.password, "ERPW_MANAGER_PASSWORD or ERPW_PASSWORD");
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

async function waitForWorklistReady(page, expectedTitle) {
  await page.locator(".erpw-list-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  await page.waitForFunction((title) => {
    const shell = document.querySelector(".erpw-list-shell");
    const titleNode = document.querySelector(".erpw-list-title");
    const stateTitle = document.querySelector(".erpw-list-state-title");
    const titleText = titleNode ? titleNode.textContent.replace(/\s+/g, " ").trim() : "";
    const stateText = stateTitle ? stateTitle.textContent.replace(/\s+/g, " ").trim() : "";
    return shell && shell.getAttribute("aria-busy") !== "true" && (titleText === title || /restricted|unavailable|failed/i.test(stateText));
  }, expectedTitle, { timeout: TIMEOUT });
}

async function measureApi(page, key) {
  return page.evaluate(async ({ methodPath, queueKey }) => {
    const start = performance.now();
    const body = new URLSearchParams();
    body.set("queue_key", queueKey);
    body.set("filters", "{}");
    const response = await fetch(methodPath, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Frappe-CSRF-Token": window.frappe && window.frappe.csrf_token ? window.frappe.csrf_token : "",
      },
      body,
    });
    const elapsedMs = performance.now() - start;
    let payload = null;
    try {
      payload = await response.json();
    } catch (error) {
      payload = { parseError: error.message };
    }
    const message = payload && payload.message ? payload.message : {};
    const rows = message.results && Array.isArray(message.results.rows) ? message.results.rows : [];
    return {
      status: response.status,
      ok: response.ok,
      elapsedMs,
      rowCount: rows.length,
      exception: payload && payload.exc ? payload.exc : null,
      stateKind: message.results && message.results.state ? message.results.state.kind : null,
    };
  }, { methodPath: METHOD_PATH, queueKey: key });
}

async function measureReady(page, item) {
  const start = Date.now();
  await page.goto(routeUrl(item.route), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  await waitForWorklistReady(page, item.title);
  return Date.now() - start;
}

async function main() {
  fs.rmSync(OUT_DIR, { recursive: true, force: true });
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const browser = await chromium.launch({ headless: process.env.ERPW_HEADLESS !== "0" });
  const context = await browser.newContext({ viewport: { width: 1366, height: 900 } });
  const page = await context.newPage();
  const pageErrors = [];
  const failedResponses = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("response", (response) => {
    if (response.status() >= 400 && response.url().includes(METHOD_PATH)) {
      failedResponses.push({ url: response.url(), status: response.status() });
    }
  });

  const report = {
    baseUrl: BASE_URL,
    apiThresholdMs: API_THRESHOLD_MS,
    sampleCount: SAMPLE_COUNT,
    directories: {},
    pageErrors,
    failedResponses,
    screenshots: [],
  };

  try {
    await login(page);
    for (const item of DIRECTORIES) {
      const readySamples = [];
      const apiSamples = [];
      let rowCount = null;
      for (let index = 0; index < SAMPLE_COUNT; index += 1) {
        readySamples.push(await measureReady(page, item));
        const screenshotPath = path.join(OUT_DIR, `${safeFileKey(item.key)}-${index + 1}.png`);
        await page.screenshot({ path: screenshotPath, fullPage: true });
        report.screenshots.push(screenshotPath);
        const apiResult = await measureApi(page, item.key);
        if (!apiResult.ok || apiResult.exception) {
          throw new Error(`${item.key}: API failed with status ${apiResult.status}`);
        }
        rowCount = apiResult.rowCount;
        apiSamples.push(apiResult.elapsedMs);
      }
      report.directories[item.key] = {
        route: item.route,
        rowCount,
        ready: summarize(readySamples),
        api: summarize(apiSamples),
        enforceApiThreshold: item.enforceApiThreshold,
      };
      if (item.enforceApiThreshold && report.directories[item.key].api.avgMs > API_THRESHOLD_MS) {
        throw new Error(`${item.key}: API average ${report.directories[item.key].api.avgMs}ms exceeds ${API_THRESHOLD_MS}ms threshold`);
      }
    }
    if (pageErrors.length) {
      throw new Error(`Page errors captured: ${pageErrors.join(" | ")}`);
    }
    if (failedResponses.length) {
      throw new Error(`Failed worklist responses captured: ${JSON.stringify(failedResponses)}`);
    }
    report.status = "passed";
  } catch (error) {
    report.status = "failed";
    report.error = error.message;
    const failurePath = path.join(OUT_DIR, "failure.png");
    try {
      await page.screenshot({ path: failurePath, fullPage: true });
      report.failureScreenshot = failurePath;
    } catch (screenshotError) {
      report.failureScreenshotError = screenshotError.message;
    }
    throw error;
  } finally {
    const reportPath = path.join(OUT_DIR, "sales-directory-performance-report.json");
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    await browser.close();
    console.log(JSON.stringify({ reportPath, status: report.status, directories: report.directories }, null, 2));
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
