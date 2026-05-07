const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const OUT_DIR = process.env.ERPW_SALES_WORKLISTS_OUT || path.join(process.cwd(), "artifacts", "sales-worklist-shell-smoke");
const TIMEOUT = Number(process.env.ERPW_SALES_WORKLISTS_TIMEOUT || 60000);
const WORKLIST_METHOD_PATH = "/api/method/erp_workspace_ui.sales_console.worklist.get_sales_console_worklist_context";

const USER = {
  label: "Sales Manager",
  username: process.env.ERPW_MANAGER_USERNAME || process.env.ERPW_USERNAME,
  password: process.env.ERPW_MANAGER_PASSWORD || process.env.ERPW_PASSWORD,
};

const WORKLISTS = [
  {
    key: "quotation_directory",
    title: "Quotations",
    route: "/desk/sales-console-worklist/quotation-directory",
    datePair: true,
    filterValues: { date_start: "2026-01-01", date_end: "2026-12-31" },
  },
  {
    key: "sales_order_directory",
    title: "Sales Orders",
    route: "/desk/sales-console-worklist/sales-order-directory",
    datePair: true,
    filterValues: { date_start: "2026-01-01", date_end: "2026-12-31" },
  },
  {
    key: "customer_directory",
    title: "Customers",
    route: "/desk/sales-console-worklist/customer-directory",
    linkDoctype: "Customer",
  },
  {
    key: "item_directory",
    title: "Items",
    route: "/desk/sales-console-worklist/item-directory",
    linkDoctype: "Item",
  },
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
  return String(value || "worklist").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "worklist";
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

async function waitForWorklistApi(page) {
  return page.waitForResponse(
    (response) => response.url().includes(WORKLIST_METHOD_PATH) && response.request().method() === "POST",
    { timeout: TIMEOUT }
  );
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

async function openWorklist(page, item) {
  const responsePromise = waitForWorklistApi(page).catch(() => null);
  await page.goto(routeUrl(item.route), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  if (/\/login(?:[/?#]|$)/.test(page.url())) throw new Error(`${item.key}: redirected to login`);
  await responsePromise;
  await waitForWorklistReady(page, item.title);
}

async function visibleActionKeys(page) {
  return page.locator("[data-erpw-list-action-key]:visible").evaluateAll((nodes) =>
    nodes.map((node) => ({
      key: node.getAttribute("data-erpw-list-action-key"),
      scope: node.getAttribute("data-erpw-list-action-scope"),
      text: node.textContent.replace(/\s+/g, " ").trim(),
    }))
  );
}

async function fieldValues(page) {
  return page.locator("[data-erpw-list-field-key]").evaluateAll((nodes) => {
    const values = {};
    nodes.forEach((node) => {
      const type = node.getAttribute("data-erpw-list-field-type") || "";
      if (type === "hidden") return;
      values[node.getAttribute("data-erpw-list-field-key")] = node.value || "";
    });
    return values;
  });
}

async function assertNoFullReload(page, label, action) {
  const marker = `${Date.now()}-${Math.random()}`;
  const before = await page.evaluate((value) => {
    window.__erpwWorklistSmokeMarker = value;
    return {
      marker: window.__erpwWorklistSmokeMarker,
      navCount: performance.getEntriesByType("navigation").length,
      path: window.location.pathname,
    };
  }, marker);
  await action();
  const after = await page.evaluate(() => ({
    marker: window.__erpwWorklistSmokeMarker,
    navCount: performance.getEntriesByType("navigation").length,
    path: window.location.pathname,
  }));
  assert(after.marker === before.marker, `${label}: page context was replaced`, { before, after });
  assert(after.navCount === before.navCount, `${label}: full page navigation count changed`, { before, after });
  assert(after.path === before.path, `${label}: route path changed during in-place filter action`, { before, after });
}

async function clickToolbarAction(page, key, label) {
  const button = page.locator(`[data-erpw-list-action-key="${key}"][data-erpw-list-action-scope="toolbar"]:visible`).first();
  await button.waitFor({ state: "visible", timeout: TIMEOUT });
  const responsePromise = waitForWorklistApi(page);
  await button.click();
  const response = await responsePromise;
  assert(response.ok(), `${label}: worklist API response failed`, { status: response.status(), url: response.url() });
  await page.waitForFunction(() => {
    const shell = document.querySelector(".erpw-list-shell");
    return shell && shell.getAttribute("aria-busy") !== "true";
  }, null, { timeout: TIMEOUT });
}

async function setFilters(page, values) {
  for (const [key, value] of Object.entries(values || {})) {
    const field = page.locator(`[data-erpw-list-field-key="${key}"]:visible`).first();
    await field.waitFor({ state: "visible", timeout: TIMEOUT });
    await field.fill(value);
  }
}

async function assertActionAlignment(page, item, report) {
  const layout = await page.evaluate(() => {
    const visible = (node) => {
      if (!node) return false;
      const style = window.getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
    };
    const actionGroup = Array.from(document.querySelectorAll(".erpw-list-command-action-cell .erpw-list-toolbar-actions, .erpw-list-action-field .erpw-list-toolbar-actions"))
      .find(visible);
    const targetInput = document.querySelector('[data-erpw-list-field-key="date_start"]')
      || Array.from(document.querySelectorAll("[data-erpw-list-field-key]")).find((node) => visible(node) && node.getAttribute("data-erpw-list-field-type") !== "hidden");
    if (!actionGroup || !targetInput) return null;
    const actionRect = actionGroup.getBoundingClientRect();
    const inputRect = targetInput.getBoundingClientRect();
    const actionCenter = actionRect.top + actionRect.height / 2;
    const inputCenter = inputRect.top + inputRect.height / 2;
    return {
      action: { top: actionRect.top, height: actionRect.height, center: actionCenter },
      target: { key: targetInput.getAttribute("data-erpw-list-field-key"), top: inputRect.top, height: inputRect.height, center: inputCenter },
      centerDelta: Math.abs(actionCenter - inputCenter),
    };
  });
  assert(layout, `${item.key}: action toolbar or target filter field missing for alignment check`);
  assert(layout.centerDelta <= 12, `${item.key}: action toolbar is not vertically aligned with filter row`, layout);
  report.actionAlignment[item.key] = layout;
}

async function assertDatePairLayout(page, item, report) {
  const layout = await page.evaluate(() => {
    const startInput = document.querySelector('[data-erpw-list-field-key="date_start"]');
    const endInput = document.querySelector('[data-erpw-list-field-key="date_end"]');
    const start = startInput && startInput.closest(".erpw-list-control-field");
    const end = endInput && endInput.closest(".erpw-list-control-field");
    if (!start || !end) return null;
    const startRect = start.getBoundingClientRect();
    const endRect = end.getBoundingClientRect();
    return {
      start: { top: startRect.top, left: startRect.left, right: startRect.right, width: startRect.width },
      end: { top: endRect.top, left: endRect.left, right: endRect.right, width: endRect.width },
      sameRowDelta: Math.abs(startRect.top - endRect.top),
    };
  });
  assert(layout, `${item.key}: date pair fields missing`);
  assert(layout.sameRowDelta <= 8, `${item.key}: date pair is not on the same desktop row`, layout);
  report.datePairLayouts[item.key] = layout;
}

async function assertFocusStability(page, item, report) {
  const before = await page.locator(".erpw-list-controls-strip").first().boundingBox();
  const firstField = page.locator("[data-erpw-list-field-key]:visible").first();
  if ((await firstField.count()) > 0) {
    await firstField.focus();
    await page.waitForTimeout(180);
  }
  const after = await page.locator(".erpw-list-controls-strip").first().boundingBox();
  if (!before || !after) return;
  const delta = Math.abs(after.height - before.height);
  assert(delta <= 6, `${item.key}: filter panel changed height on focus`, { before, after, delta });
  report.focusStability[item.key] = { before, after, delta };
}

async function firstInlineOpenText(page) {
  const label = page.locator(".erpw-list-inline-open-label:visible").first();
  if ((await label.count()) === 0) return "";
  return normalizeText(await label.innerText({ timeout: TIMEOUT }));
}

async function assertLinkAutocomplete(page, item, report) {
  const input = page.locator(`[data-erpw-list-link-doctype="${item.linkDoctype}"]:visible`).first();
  await input.waitFor({ state: "visible", timeout: TIMEOUT });
  const seed = item.linkDoctype === "Customer" ? "Aung" : "USB";
  await input.fill(seed);
  await page.waitForFunction((doctype) => {
    const inputNode = document.querySelector(`[data-erpw-list-link-doctype="${doctype}"]`);
    const field = inputNode && inputNode.closest(".erpw-list-control-field");
    const panel = field && field.querySelector(".erpw-list-link-suggestions");
    return panel && panel.hidden === false;
  }, item.linkDoctype, { timeout: TIMEOUT });
  const state = await input.evaluate((node) => {
    const field = node.closest(".erpw-list-control-field");
    const panel = field && field.querySelector(".erpw-list-link-suggestions");
    return {
      doctype: node.getAttribute("data-erpw-list-link-doctype"),
      expanded: node.getAttribute("aria-expanded"),
      optionCount: panel ? panel.querySelectorAll("[data-erpw-list-link-option]").length : 0,
      text: panel ? panel.textContent.replace(/\s+/g, " ").trim() : "",
    };
  });
  assert(state.doctype === item.linkDoctype, `${item.key}: link doctype mismatch`, state);
  assert(state.expanded === "true", `${item.key}: autocomplete did not open`, state);
  assert(state.optionCount > 0, `${item.key}: autocomplete returned no options`, state);
  report.autocomplete[item.key] = state;
  await page.keyboard.press("Escape").catch(() => {});
}

async function exerciseApplyResetRefresh(page, item, report) {
  const initialActions = await visibleActionKeys(page);
  for (const key of ["apply_filters", "reset_filters", "refresh"]) {
    assert(initialActions.some((action) => action.key === key && action.scope === "toolbar"), `${item.key}: missing toolbar action ${key}`, { initialActions });
  }

  const values = Object.assign({}, item.filterValues || {});
  if (item.linkDoctype) {
    const seedText = await firstInlineOpenText(page);
    values.keyword = normalizeText(seedText).split(/\s+/).find(Boolean) || "";
  }
  await setFilters(page, values);

  await assertNoFullReload(page, `${item.key} apply`, () => clickToolbarAction(page, "apply_filters", `${item.key} apply`));
  await assertNoFullReload(page, `${item.key} reset`, () => clickToolbarAction(page, "reset_filters", `${item.key} reset`));
  const resetValues = await fieldValues(page);
  Object.entries(resetValues).forEach(([key, value]) => {
    if (key === "view") return;
    assert(value === "", `${item.key}: reset did not clear ${key}`, resetValues);
  });
  await assertNoFullReload(page, `${item.key} refresh`, () => clickToolbarAction(page, "refresh", `${item.key} refresh`));
  report.actions[item.key] = initialActions;
}

async function runWorklist(page, item, report) {
  await openWorklist(page, item);
  await assertFocusStability(page, item, report);
  await assertActionAlignment(page, item, report);
  if (item.datePair) await assertDatePairLayout(page, item, report);
  if (item.linkDoctype) await assertLinkAutocomplete(page, item, report);
  await exerciseApplyResetRefresh(page, item, report);
  const inlineOpenCount = await page.locator(".erpw-list-inline-open:visible").count();
  assert(inlineOpenCount > 0, `${item.key}: shared inline row link affordance missing`);
  const screenshot = path.join(OUT_DIR, `${safeFileKey(item.key)}.png`);
  await page.screenshot({ path: screenshot, fullPage: true });
  report.screenshots.push(screenshot);
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
    actions: {},
    autocomplete: {},
    actionAlignment: {},
    datePairLayouts: {},
    focusStability: {},
    screenshots: [],
    consoleMessages,
  };

  try {
    await login(page);
    for (const item of WORKLISTS) {
      await runWorklist(page, item, report);
      console.log(`[pass] ${item.key}`);
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
    fs.writeFileSync(path.join(OUT_DIR, "sales-worklist-shell-report.json"), `${JSON.stringify(report, null, 2)}\n`, "utf8");
    console.log(`report=${path.join(OUT_DIR, "sales-worklist-shell-report.json")}`);
  }
})();
