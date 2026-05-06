const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const OUT_DIR = process.env.ERPW_SALES_LEAKAGE_OUT || path.join(process.cwd(), "artifacts", "sales-native-leakage-smoke");
const TIMEOUT = Number(process.env.ERPW_SALES_LEAKAGE_TIMEOUT || 70000);
const WORKLIST_METHOD_PATH = "/api/method/erp_workspace_ui.sales_console.worklist.get_sales_console_worklist_context";
const REPORT_METHOD_PATH = "/api/method/erp_workspace_ui.sales_console.report.get_sales_console_report_context";

const USER = {
  label: "Sales Manager",
  username: process.env.ERPW_MANAGER_USERNAME || process.env.ERPW_USERNAME,
  password: process.env.ERPW_MANAGER_PASSWORD || process.env.ERPW_PASSWORD,
};

const FORBIDDEN_MUTATION_LABELS = new Set([
  "Submit",
  "Cancel",
  "Amend",
  "Close",
  "Unclose",
  "Approve",
  "Reject",
  "Receive",
  "Bill",
  "Pay",
  "Set Default Supplier",
  "Update Item Price",
  "Delete",
]);

const NATIVE_LEAK_LABELS = new Set([
  "Open ERP Form",
  "Open Standard List",
  "Open Standard Report",
  "Open Native List",
  "Open Native Report",
]);

const OVERVIEW_ACTIONS = new Set(["new_quotation", "new_sales_order", "open_customer", "open_item"]);
const LIST_ACTIONS = new Set([
  "refresh",
  "reset_filters",
  "apply_filters",
  "new_quotation",
  "new_sales_order",
  "create_customer",
  "back_to_customers",
  "edit_customer",
  "back_to_items",
  "save_customer_profile",
  "cancel_customer_editor",
  "open_record",
]);
const REPORT_ACTIONS = new Set(["refresh", "back_to_console"]);

const PRODUCTIZED_ROUTES = [
  { key: "overview", route: "/desk/sales-console", root: ".sales-console-shell", kind: "overview" },
  { key: "quotation_directory", route: "/desk/sales-console-worklist/quotation-directory", root: ".erpw-list-shell", kind: "list" },
  { key: "sales_order_directory", route: "/desk/sales-console-worklist/sales-order-directory", root: ".erpw-list-shell", kind: "list" },
  { key: "customer_directory", route: "/desk/sales-console-worklist/customer-directory", root: ".erpw-list-shell", kind: "list" },
  { key: "item_directory", route: "/desk/sales-console-worklist/item-directory", root: ".erpw-list-shell", kind: "list" },
  { key: "sales_analytics", route: "/desk/sales-console-report/sales-analytics", root: ".erpw-report-shell", kind: "report" },
  { key: "sales_order_analysis", route: "/desk/sales-console-report/sales-order-analysis", root: ".erpw-report-shell", kind: "report" },
  { key: "trend_analysis", route: "/desk/sales-console-report/trend-analysis", root: ".erpw-report-shell", kind: "report" },
  { key: "collections_status", route: "/desk/sales-console-report/collections-status", root: ".erpw-report-shell", kind: "report" },
  { key: "item_wise_sales_history", route: "/desk/sales-console-report/item-wise-sales-history", root: ".erpw-report-shell", kind: "report" },
];

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
  return String(value || "page").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "page";
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

async function waitForManagedSurface(page, config) {
  await page.locator(config.root).first().waitFor({ state: "visible", timeout: TIMEOUT });
  if (config.kind === "list") {
    await page.waitForFunction(() => {
      const shell = document.querySelector(".erpw-list-shell");
      return shell && shell.getAttribute("aria-busy") !== "true";
    }, null, { timeout: TIMEOUT });
  }
  if (config.kind === "report") {
    await page.waitForFunction(() => {
      const shell = document.querySelector(".erpw-report-shell");
      return shell && shell.getAttribute("aria-busy") !== "true";
    }, null, { timeout: TIMEOUT });
  }
}

async function openProductizedRoute(page, config) {
  await page.goto(routeUrl(config.route), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  if (/\/login(?:[/?#]|$)/.test(page.url())) throw new Error(`${config.key}: redirected to login`);
  await waitForManagedSurface(page, config);
}

async function openFirstDetail(page, directoryRoute, detailPattern, key) {
  const responsePromise = page.waitForResponse((response) => response.url().includes(WORKLIST_METHOD_PATH), { timeout: TIMEOUT }).catch(() => null);
  await page.goto(routeUrl(directoryRoute), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  await responsePromise;
  await waitForManagedSurface(page, { root: ".erpw-list-shell", kind: "list" });
  const row = page.locator(".erpw-list-inline-open:visible").first();
  await row.waitFor({ state: "visible", timeout: TIMEOUT });
  const detailResponse = page.waitForResponse((response) => response.url().includes(WORKLIST_METHOD_PATH), { timeout: TIMEOUT }).catch(() => null);
  await row.click();
  await detailResponse;
  await page.waitForFunction((pattern) => new RegExp(pattern).test(window.location.pathname), detailPattern, { timeout: TIMEOUT });
  await waitForManagedSurface(page, { root: ".erpw-list-shell", kind: "list" });
  return { key, root: ".erpw-list-shell", kind: "list" };
}

async function scanSurface(page, config, report) {
  const scan = await page.evaluate(({ rootSelector, kind, forbiddenLabels, nativeLabels, overviewActions, listActions, reportActions }) => {
    const root = document.querySelector(rootSelector);
    if (!root) return { missingRoot: rootSelector };
    const visible = (node) => {
      const style = window.getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
    };
    const interactive = Array.from(root.querySelectorAll("button, a, [role='button']")).filter(visible).map((node) => ({
      tag: node.tagName.toLowerCase(),
      text: (node.textContent || "").replace(/\s+/g, " ").trim(),
      href: node.getAttribute("href") || "",
      overviewKey: node.getAttribute("data-action-key") || "",
      listKey: node.getAttribute("data-erpw-list-action-key") || "",
      reportKey: node.getAttribute("data-erpw-report-action-key") || "",
      className: node.className || "",
    }));
    const forbidden = interactive.filter((item) => forbiddenLabels.includes(item.text));
    const nativeLeaks = interactive.filter((item) => nativeLabels.includes(item.text));
    const rawHrefs = interactive.filter((item) => {
      if (!item.href || item.href === "#") return false;
      let path = item.href;
      try {
        path = new URL(item.href, window.location.origin).pathname;
      } catch (error) {
        path = item.href.split(/[?#]/)[0] || item.href;
      }
      if (!path) return false;
      if (/^\/(?:desk|app)\/sales-console(?:-|\/|$)/.test(path)) return false;
      return /^\/(?:desk|app)\//.test(path);
    });
    let unknownActions = [];
    if (kind === "overview") {
      unknownActions = interactive
        .filter((item) => item.overviewKey)
        .filter((item) => !overviewActions.includes(item.overviewKey));
    } else if (kind === "list") {
      unknownActions = interactive
        .filter((item) => item.listKey)
        .filter((item) => !listActions.includes(item.listKey));
    } else if (kind === "report") {
      unknownActions = interactive
        .filter((item) => item.reportKey)
        .filter((item) => !reportActions.includes(item.reportKey) && !String(item.className || "").includes("erpw-report-cell-link"));
    }
    return {
      interactiveCount: interactive.length,
      forbidden,
      nativeLeaks,
      rawHrefs,
      unknownActions,
    };
  }, {
    rootSelector: config.root,
    kind: config.kind,
    forbiddenLabels: Array.from(FORBIDDEN_MUTATION_LABELS),
    nativeLabels: Array.from(NATIVE_LEAK_LABELS),
    overviewActions: Array.from(OVERVIEW_ACTIONS),
    listActions: Array.from(LIST_ACTIONS),
    reportActions: Array.from(REPORT_ACTIONS),
  });

  assert(!scan.missingRoot, `${config.key}: managed surface missing`, scan);
  assert(scan.forbidden.length === 0, `${config.key}: forbidden mutation labels visible`, scan);
  assert(scan.nativeLeaks.length === 0, `${config.key}: native leakage labels visible`, scan);
  assert(scan.rawHrefs.length === 0, `${config.key}: raw ERPNext href leakage visible`, scan);
  assert(scan.unknownActions.length === 0, `${config.key}: visible action is not classified by smoke manifest`, scan);

  const screenshot = path.join(OUT_DIR, `${safeFileKey(config.key)}.png`);
  await page.screenshot({ path: screenshot, fullPage: true });
  report.pages[config.key] = Object.assign({ url: page.url(), screenshot }, scan);
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
  const report = { role: USER.label, username: USER.username, pages: {} };

  try {
    await login(page);
    for (const config of PRODUCTIZED_ROUTES) {
      await openProductizedRoute(page, config);
      await scanSurface(page, config, report);
      console.log(`[pass] ${config.key}`);
    }
    const customerDetail = await openFirstDetail(page, "/desk/sales-console-worklist/customer-directory", "/sales-console-worklist/customer-detail/", "customer_detail");
    await scanSurface(page, customerDetail, report);
    console.log("[pass] customer_detail");
    const itemDetail = await openFirstDetail(page, "/desk/sales-console-worklist/item-directory", "/sales-console-worklist/item-detail/", "item_detail");
    await scanSurface(page, itemDetail, report);
    console.log("[pass] item_detail");
    report.status = "passed";
  } catch (error) {
    report.status = "failed";
    report.error = error.message;
    report.details = error.details || null;
    await page.screenshot({ path: path.join(OUT_DIR, "failure.png"), fullPage: true }).catch(() => {});
    console.error(`[fail] ${error.message}`);
    if (error.details) console.error(JSON.stringify(error.details, null, 2));
    process.exitCode = 1;
  } finally {
    await context.close();
    await browser.close();
    fs.writeFileSync(path.join(OUT_DIR, "sales-native-leakage-report.json"), `${JSON.stringify(report, null, 2)}\n`, "utf8");
    console.log(`report=${path.join(OUT_DIR, "sales-native-leakage-report.json")}`);
  }
})();
