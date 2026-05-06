const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const OUT_DIR = process.env.ERPW_SALES_VISUAL_OUT || path.join(process.cwd(), "artifacts", "sales-visual-stability-smoke");
const TIMEOUT = Number(process.env.ERPW_SALES_VISUAL_TIMEOUT || 70000);
const WORKLIST_METHOD_PATH = "/api/method/erp_workspace_ui.sales_console.worklist.get_sales_console_worklist_context";

const USER = {
  label: "Sales Manager",
  username: process.env.ERPW_MANAGER_USERNAME || process.env.ERPW_USERNAME,
  password: process.env.ERPW_MANAGER_PASSWORD || process.env.ERPW_PASSWORD,
};

const BASELINE_ROOT = path.join(process.cwd(), "artifacts", "sales-recovery-baseline-20260506T060311Z", "manager");
const BEFORE_DIR = path.join(OUT_DIR, "before");
const AFTER_DIR = path.join(OUT_DIR, "after");

const PAGES = [
  { key: "sales-overview", route: "/desk/sales-console", root: ".sales-console-shell", kind: "overview", before: "01-sales-overview.png" },
  { key: "quotation-directory", route: "/desk/sales-console-worklist/quotation-directory", root: ".erpw-list-shell", kind: "list", before: "02-quotation-directory.png" },
  { key: "sales-order-directory", route: "/desk/sales-console-worklist/sales-order-directory", root: ".erpw-list-shell", kind: "list", before: "03-sales-order-directory.png" },
  { key: "customer-directory", route: "/desk/sales-console-worklist/customer-directory", root: ".erpw-list-shell", kind: "list", before: "04-customer-directory.png" },
  { key: "customer-detail", derive: "customer", root: ".erpw-list-shell", kind: "list", before: "05-customer-detail.png" },
  { key: "customer-editor", route: "/desk/sales-console-worklist/customer-editor", root: ".erpw-list-shell", kind: "list", before: "07-customer-editor-new.png" },
  { key: "item-directory", route: "/desk/sales-console-worklist/item-directory", root: ".erpw-list-shell", kind: "list", before: "08-item-directory.png" },
  { key: "item-detail", derive: "item", root: ".erpw-list-shell", kind: "list", before: "09-item-detail.png" },
  { key: "sales-analytics", route: "/desk/sales-console-report/sales-analytics", root: ".erpw-report-shell", kind: "report", before: "10-sales-analytics.png" },
  { key: "sales-order-analysis", route: "/desk/sales-console-report/sales-order-analysis", root: ".erpw-report-shell", kind: "report", before: "11-sales-order-analysis.png" },
  { key: "trend-analysis", route: "/desk/sales-console-report/trend-analysis", root: ".erpw-report-shell", kind: "report", before: "12-trend-analysis.png" },
  { key: "collections-status", route: "/desk/sales-console-report/collections-status", root: ".erpw-report-shell", kind: "report", before: "13-collections-status.png" },
  { key: "item-wise-sales-history", route: "/desk/sales-console-report/item-wise-sales-history", root: ".erpw-report-shell", kind: "report", before: "14-item-wise-sales-history.png" },
];

const IMPLEMENTATION_COPY_PATTERNS = [
  /productized/i,
  /permission scope/i,
  /route key/i,
  /managed shell/i,
  /workspace adapter/i,
  /raw route/i,
];

function requireValue(value, name) {
  if (!value) throw new Error(`Missing ${name}`);
  return value;
}

function routeUrl(route) {
  return new URL(route, BASE_URL).toString();
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

function copyBaseline(page) {
  const source = path.join(BASELINE_ROOT, page.before || "");
  const target = path.join(BEFORE_DIR, `${safeFileKey(page.key)}.png`);
  if (fs.existsSync(source)) {
    fs.copyFileSync(source, target);
    return target;
  }
  return null;
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

async function waitForSurface(page, config) {
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

async function openRoute(page, config) {
  await page.goto(routeUrl(config.route), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  if (/\/login(?:[/?#]|$)/.test(page.url())) throw new Error(`${config.key}: redirected to login`);
  await waitForSurface(page, config);
}

async function openDerivedDetail(page, derive) {
  const route = derive === "customer" ? "/desk/sales-console-worklist/customer-directory" : "/desk/sales-console-worklist/item-directory";
  const pattern = derive === "customer" ? "/sales-console-worklist/customer-detail/" : "/sales-console-worklist/item-detail/";
  const responsePromise = page.waitForResponse((response) => response.url().includes(WORKLIST_METHOD_PATH), { timeout: TIMEOUT }).catch(() => null);
  await page.goto(routeUrl(route), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  await responsePromise;
  await waitForSurface(page, { root: ".erpw-list-shell", kind: "list" });
  const row = page.locator(".erpw-list-inline-open:visible").first();
  await row.waitFor({ state: "visible", timeout: TIMEOUT });
  const detailResponse = page.waitForResponse((response) => response.url().includes(WORKLIST_METHOD_PATH), { timeout: TIMEOUT }).catch(() => null);
  await row.click();
  await detailResponse;
  await page.waitForFunction((expected) => window.location.pathname.includes(expected), pattern, { timeout: TIMEOUT });
  await waitForSurface(page, { root: ".erpw-list-shell", kind: "list" });
}

async function focusStability(page, config) {
  const selector = `${config.root} .erpw-list-controls-strip, ${config.root} .erpw-report-controls`;
  const panel = page.locator(selector).first();
  if ((await panel.count()) === 0) return null;
  const before = await panel.boundingBox();
  const field = page.locator(`${config.root} input:visible, ${config.root} select:visible, ${config.root} textarea:visible`).first();
  if ((await field.count()) === 0) return null;
  await field.focus();
  await page.waitForTimeout(180);
  const after = await panel.boundingBox();
  if (!before || !after) return null;
  const delta = Math.abs(after.height - before.height);
  assert(delta <= 6, `${config.key}: control panel shifts on focus`, { before, after, delta });
  return { before, after, delta };
}

async function scanVisualSurface(page, config) {
  return page.evaluate(({ rootSelector, copyPatterns }) => {
    const root = document.querySelector(rootSelector);
    if (!root) return { missingRoot: rootSelector };
    const visible = (node) => {
      const style = window.getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
    };
    const viewportWidth = window.innerWidth || document.documentElement.clientWidth;
    const rootText = (root.textContent || "").replace(/\s+/g, " ").trim();
    const implementationCopy = copyPatterns.filter((pattern) => new RegExp(pattern.source, pattern.flags).test(rootText)).map((pattern) => pattern.source);
    const overflowingControls = Array.from(root.querySelectorAll("button, input, select, textarea, .sales-console-card, .sales-console-action, .erpw-list-controls-strip, .erpw-list-summary-card, .erpw-report-controls, .erpw-report-summary, .erpw-report-card"))
      .filter(visible)
      .map((node) => {
        const rect = node.getBoundingClientRect();
        const text = (node.textContent || node.value || "").replace(/\s+/g, " ").trim();
        return {
          tag: node.tagName.toLowerCase(),
          className: node.className || "",
          text,
          left: rect.left,
          right: rect.right,
          width: rect.width,
          clippedText: ["BUTTON", "SELECT"].includes(node.tagName) && node.scrollWidth > node.clientWidth + 3,
        };
      })
      .filter((item) => item.left < -6 || item.right > viewportWidth + 6 || item.clippedText);
    return {
      implementationCopy,
      overflowingControls,
      scrollWidth: document.documentElement.scrollWidth,
      viewportWidth,
      rootHeight: root.getBoundingClientRect().height,
    };
  }, { rootSelector: config.root, copyPatterns: IMPLEMENTATION_COPY_PATTERNS });
}

async function runPage(page, config, report) {
  if (config.derive) {
    await openDerivedDetail(page, config.derive);
  } else {
    await openRoute(page, config);
  }
  const beforePath = copyBaseline(config);
  const stability = await focusStability(page, config);
  const scan = await scanVisualSurface(page, config);
  assert(!scan.missingRoot, `${config.key}: managed surface missing`, scan);
  assert(scan.implementationCopy.length === 0, `${config.key}: implementation-facing copy visible`, scan);
  assert(scan.overflowingControls.length === 0, `${config.key}: visible control/card overflow detected`, scan);
  assert(scan.scrollWidth <= scan.viewportWidth + 8, `${config.key}: page has horizontal overflow`, scan);
  const afterPath = path.join(AFTER_DIR, `${safeFileKey(config.key)}.png`);
  await page.screenshot({ path: afterPath, fullPage: true });
  report.pages[config.key] = {
    url: page.url(),
    before: beforePath,
    after: afterPath,
    focusStability: stability,
    scan,
  };
}

(async () => {
  fs.mkdirSync(BEFORE_DIR, { recursive: true });
  fs.mkdirSync(AFTER_DIR, { recursive: true });
  requireValue(USER.username, "Sales Manager username");
  requireValue(USER.password, "Sales Manager password");

  const browser = await chromium.launch({ headless: process.env.ERPW_HEADLESS !== "0" });
  const context = await browser.newContext({
    baseURL: BASE_URL,
    ignoreHTTPSErrors: true,
    viewport: { width: 1440, height: 1100 },
  });
  const page = await context.newPage();
  const report = {
    role: USER.label,
    username: USER.username,
    viewport: { width: 1440, height: 1100 },
    beforeDir: BEFORE_DIR,
    afterDir: AFTER_DIR,
    mobileResponsive: {
      run: false,
      reason: "Task 8 changed copy and desktop density only; no breakpoint or responsive CSS changes were made.",
    },
    pages: {},
  };

  try {
    await login(page);
    for (const config of PAGES) {
      await runPage(page, config, report);
      console.log(`[pass] ${config.key}`);
    }
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
    fs.writeFileSync(path.join(OUT_DIR, "sales-visual-stability-report.json"), `${JSON.stringify(report, null, 2)}\n`, "utf8");
    console.log(`report=${path.join(OUT_DIR, "sales-visual-stability-report.json")}`);
  }
})();
