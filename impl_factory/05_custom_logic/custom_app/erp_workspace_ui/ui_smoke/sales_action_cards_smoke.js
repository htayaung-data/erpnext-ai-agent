const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const OUT_DIR = process.env.ERPW_SALES_ACTIONS_OUT || path.join(process.cwd(), "artifacts", "sales-action-cards-smoke");
const TIMEOUT = Number(process.env.ERPW_SALES_ACTIONS_TIMEOUT || 60000);

const USER = {
  label: "Sales Manager",
  username: process.env.ERPW_MANAGER_USERNAME || process.env.ERPW_USERNAME,
  password: process.env.ERPW_MANAGER_PASSWORD || process.env.ERPW_PASSWORD,
};

const ACTION_CONTRACT = {
  new_quotation: {
    label: "New Quotation",
    classification: "governed_native_action",
    nativeExceptionRef: "sales-managed-document-forms-v1",
    targetKind: "new_doc",
    expectedRoute: ["Form", "Quotation"],
  },
  new_sales_order: {
    label: "New Sales Order",
    classification: "governed_native_action",
    nativeExceptionRef: "sales-managed-document-forms-v1",
    targetKind: "new_doc",
    expectedRoute: ["Form", "Sales Order"],
  },
  open_customer: {
    label: "Customers",
    classification: "productized_navigation",
    targetKind: "worklist",
    expectedPath: "/desk/sales-console-worklist/customer-directory",
  },
  open_item: {
    label: "Items",
    classification: "productized_navigation",
    targetKind: "worklist",
    expectedPath: "/desk/sales-console-worklist/item-directory",
  },
};

function requireValue(value, name) {
  if (!value) throw new Error(`Missing ${name}`);
  return value;
}

function routeUrl(route) {
  return new URL(route, BASE_URL).toString();
}

function safeFileKey(value) {
  return String(value || "action").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "action";
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

async function openOverview(page) {
  await page.goto(routeUrl("/desk/sales-console"), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  if (/\/login(?:[/?#]|$)/.test(page.url())) throw new Error("Sales overview redirected to login");
  await page.locator(".sales-console-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  await page.waitForFunction(() => document.querySelectorAll(".sales-console-action[data-action-key]").length > 0, null, { timeout: TIMEOUT });
}

async function visibleActions(page) {
  return page.locator(".sales-console-action[data-action-key]").evaluateAll((nodes) =>
    nodes
      .filter((node) => {
        const style = window.getComputedStyle(node);
        const rect = node.getBoundingClientRect();
        return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
      })
      .map((node) => ({
        key: node.getAttribute("data-action-key"),
        tier: node.getAttribute("data-action-tier"),
        text: node.textContent.replace(/\s+/g, " ").trim(),
      }))
  );
}

async function currentRoute(page) {
  return page.evaluate(() => (window.frappe && typeof window.frappe.get_route === "function" ? window.frappe.get_route() : []));
}

async function clickVisibleAction(page, actionKey) {
  const locator = page.locator(`.sales-console-action[data-action-key="${actionKey}"]:visible`).first();
  await locator.waitFor({ state: "visible", timeout: TIMEOUT });
  await locator.click();
}

async function assertShellCounts(page, label) {
  const counts = await page.evaluate(() => {
    const visible = (node) => {
      if (!node) return false;
      const style = window.getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
    };
    const count = (selector) => Array.from(document.querySelectorAll(selector)).filter(visible).length;
    return {
      overview: count(".sales-console-shell"),
      list: count(".erpw-list-shell"),
      report: count(".erpw-report-shell"),
      pageHead: count(".page-head"),
    };
  });
  assert(counts.overview + counts.list + counts.report <= 1, `${label}: stacked managed shells after action`, counts);
  assert(counts.pageHead <= 1, `${label}: duplicate page headers after action`, counts);
  return counts;
}

async function assertInquiryAutocomplete(page, report) {
  await openOverview(page);
  const shellBefore = await page.locator(".sales-console-shell").first().boundingBox();
  const input = page.locator("[data-inquiry-input]:visible").first();
  await input.waitFor({ state: "visible", timeout: TIMEOUT });
  await input.fill("Aung");
  await page.waitForFunction(() => {
    const panel = document.querySelector("[data-inquiry-suggestions]");
    return panel && panel.hidden === false && panel.querySelectorAll(".sales-console-inquiry-suggestion").length > 0;
  }, null, { timeout: TIMEOUT });
  await page.waitForTimeout(180);
  const shellAfter = await page.locator(".sales-console-shell").first().boundingBox();
  const state = await page.evaluate(() => {
    const panel = document.querySelector("[data-inquiry-suggestions]");
    return {
      optionCount: panel ? panel.querySelectorAll(".sales-console-inquiry-suggestion").length : 0,
      text: panel ? panel.textContent.replace(/\s+/g, " ").trim() : "",
      hidden: panel ? panel.hidden : true,
    };
  });
  const widthDelta = shellBefore && shellAfter ? Math.abs(shellAfter.width - shellBefore.width) : 0;
  assert(state.optionCount > 0, "Sales overview inquiry autocomplete returned no suggestions", state);
  assert(widthDelta <= 6, "Sales overview shell width changed on inquiry focus", { shellBefore, shellAfter, widthDelta, state });
  const screenshot = path.join(OUT_DIR, "overview-inquiry-autocomplete.png");
  await page.screenshot({ path: screenshot, fullPage: true });
  report.inquiryAutocomplete = Object.assign({ screenshot, widthDelta }, state);
  await page.keyboard.press("Escape").catch(() => {});
}

async function checkAction(page, action, report) {
  const contract = ACTION_CONTRACT[action.key];
  assert(contract, `Visible Sales overview action is not classified: ${action.key}`, { action });

  await openOverview(page);
  await clickVisibleAction(page, action.key);

  if (contract.expectedPath) {
    await page.waitForFunction((expectedPath) => window.location.pathname.includes(expectedPath), contract.expectedPath, { timeout: TIMEOUT });
    await page.locator(".erpw-list-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  } else if (contract.expectedRoute) {
    await page.waitForFunction(
      ([routeType, doctype]) => {
        const route = window.frappe && typeof window.frappe.get_route === "function" ? window.frappe.get_route() : [];
        return Array.isArray(route) && route[0] === routeType && route[1] === doctype;
      },
      contract.expectedRoute,
      { timeout: TIMEOUT }
    );
  }

  const route = await currentRoute(page);
  const counts = await assertShellCounts(page, action.key);
  const screenshot = path.join(OUT_DIR, `${safeFileKey(action.key)}.png`);
  await page.screenshot({ path: screenshot, fullPage: true });
  report.actions.push({
    key: action.key,
    text: action.text,
    classification: contract.classification,
    targetKind: contract.targetKind,
    nativeExceptionRef: contract.nativeExceptionRef || null,
    route,
    url: page.url(),
    counts,
    screenshot,
  });
}

(async () => {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  requireValue(USER.username, "Sales Manager username");
  requireValue(USER.password, "Sales Manager password");

  const browser = await chromium.launch({ headless: process.env.ERPW_HEADLESS !== "0" });
  const context = await browser.newContext({
    baseURL: BASE_URL,
    ignoreHTTPSErrors: true,
    viewport: { width: 1440, height: 1200 },
  });
  const page = await context.newPage();
  const consoleMessages = [];
  page.on("console", (message) => {
    if (["error", "warning"].includes(message.type())) consoleMessages.push({ type: message.type(), text: message.text() });
  });

  const report = {
    role: USER.label,
    username: USER.username,
    actions: [],
    unknownActions: [],
    noOpActions: [],
    inquiryAutocomplete: null,
    consoleMessages,
  };

  try {
    await login(page);
    await openOverview(page);
    const actions = await visibleActions(page);
    report.visibleActions = actions;
    assert(actions.length > 0, "No visible Sales overview actions found");
    report.unknownActions = actions.filter((action) => !ACTION_CONTRACT[action.key]);
    assert(report.unknownActions.length === 0, "Visible Sales overview actions are not manifest-classified", {
      unknownActions: report.unknownActions,
    });
    await assertInquiryAutocomplete(page, report);

    for (const action of actions) {
      const beforeUrl = page.url();
      await checkAction(page, action, report);
      const afterUrl = page.url();
      if (beforeUrl === afterUrl) report.noOpActions.push(action.key);
    }
    assert(report.noOpActions.length === 0, "Sales overview action no-ops were found", { noOpActions: report.noOpActions });
    report.status = "passed";
    console.log(`[pass] Sales overview action cards (${actions.length})`);
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
    fs.writeFileSync(path.join(OUT_DIR, "sales-action-cards-report.json"), `${JSON.stringify(report, null, 2)}\n`, "utf8");
    console.log(`report=${path.join(OUT_DIR, "sales-action-cards-report.json")}`);
  }
})();
