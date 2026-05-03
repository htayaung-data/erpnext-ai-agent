const { chromium } = require("playwright");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const TIMEOUT = Number(process.env.ERPW_PROCUREMENT_SMOKE_TIMEOUT || 60000);

const USERS = [
  {
    key: "manager",
    label: "Manager",
    username: process.env.ERPW_MANAGER_USERNAME,
    password: process.env.ERPW_MANAGER_PASSWORD,
  },
  {
    key: "user",
    label: "User",
    username: process.env.ERPW_USER_USERNAME,
    password: process.env.ERPW_USER_PASSWORD,
  },
].filter((user) => user.username && user.password);

const WORKLISTS = [
  { key: "rfq_directory", route: "/desk/procurement-console-worklist/rfq-directory" },
  { key: "rfqs_awaiting_supplier_response", route: "/desk/procurement-console-worklist/rfqs-awaiting-supplier-response" },
  { key: "rfqs_partially_quoted", route: "/desk/procurement-console-worklist/rfqs-partially-quoted" },
  { key: "supplier_quotation_directory", route: "/desk/procurement-console-worklist/supplier-quotation-directory" },
  { key: "supplier_quotations_to_compare", route: "/desk/procurement-console-worklist/supplier-quotations-to-compare" },
  { key: "supplier_quotations_expiring", route: "/desk/procurement-console-worklist/supplier-quotations-expiring" },
];

const FORBIDDEN_ACTION_RE = /(create|edit|submit|approve|reject|default_supplier|set_default_supplier|item_price|make_purchase_order|supplier_portal|send_email)/i;

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

function stateKind(payload) {
  return payload && payload.results && payload.results.state ? payload.results.state.kind : payload && payload.state ? payload.state.kind : "missing";
}

function valuesFromContainer(value) {
  if (Array.isArray(value)) return value;
  if (value && typeof value === "object") return Object.values(value);
  return [];
}

function pushAction(actions, action) {
  if (!action) return;
  if (typeof action === "string") {
    actions.push({ key: action, label: action });
    return;
  }
  if (typeof action === "object") actions.push(action);
}

function collectCellActions(cell) {
  const actions = [];
  if (!cell || typeof cell !== "object") return actions;
  if (cell.actionKey) pushAction(actions, { key: cell.actionKey, label: cell.actionKey });
  pushAction(actions, cell.action);
  pushAction(actions, cell.target);
  return actions;
}

function collectActions(payload) {
  const actions = [];
  const controls = payload && payload.controls ? payload.controls : {};
  valuesFromContainer(controls.actions).forEach((action) => pushAction(actions, action));
  ((payload && payload.results && payload.results.rows) || []).forEach((row) => {
    valuesFromContainer(row.actions).forEach((action) => pushAction(actions, action));
    valuesFromContainer(row.cells).forEach((cell) => {
      collectCellActions(cell).forEach((action) => pushAction(actions, action));
    });
  });
  return actions;
}

function assertNoForbiddenActions(payload, label) {
  const offenders = collectActions(payload)
    .map((action) => `${action.key || ""} ${action.label || ""} ${action.type || ""} ${action.method || ""}`)
    .filter((value) => FORBIDDEN_ACTION_RE.test(value));
  assert(offenders.length === 0, `${label}: forbidden mutation action exposed`, { offenders });
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
    page.waitForURL(/\/(?:app|desk)(?:[/?#]|$)/, { waitUntil: "domcontentloaded", timeout: TIMEOUT }),
    loginButton.click(),
  ]);
}

async function openDeskRoute(page, route) {
  await page.goto(routeUrl(route), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  if (/\/login(?:[/?#]|$)/.test(page.url())) {
    throw new Error(`Route ${route} redirected to login`);
  }
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

async function checkWorklistApi(page, queueKey) {
  const response = await callMethod(page, "erp_workspace_ui.procurement_console.worklist.get_procurement_console_worklist_context", {
    queue_key: queueKey,
  });
  assert(response.ok, `${queueKey}: worklist API failed`, response);
  const payload = response.data.message || {};
  const state = stateKind(payload);
  assert(["ready", "empty", "restricted", "unavailable"].includes(state), `${queueKey}: invalid state kind`, { state, payload });
  assertNoForbiddenActions(payload, queueKey);

  if (state === "ready" || state === "empty") {
    const actions = ((payload.controls || {}).actions || []).map((action) => action.key);
    assert(
      actions.slice(0, 3).join(",") === "refresh,reset_filters,apply_filters",
      `${queueKey}: backend action order mismatch`,
      { actions }
    );
  }
  return state;
}

async function checkWorklistPage(page, user, item, apiState) {
  await openDeskRoute(page, item.route);
  await page.locator(".erpw-list-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  await page.waitForFunction(() => {
    const shell = document.querySelector(".erpw-list-shell");
    const text = shell ? shell.textContent.replace(/\s+/g, " ") : "";
    return text.includes("Apply") || text.includes("No visible") || text.includes("restricted") || text.includes("unavailable");
  }, null, { timeout: TIMEOUT });

  const actionKeys = await page.locator("[data-erpw-list-action-key]").evaluateAll((nodes) =>
    nodes.map((node) => node.getAttribute("data-erpw-list-action-key"))
  );
  const forbidden = actionKeys.filter((key) => FORBIDDEN_ACTION_RE.test(key || ""));
  assert(forbidden.length === 0, `${user.label}: ${item.key} forbidden UI action exposed`, { forbidden });
  if (apiState === "ready" || apiState === "empty") {
    assert(
      actionKeys.slice(0, 3).join(",") === "apply_filters,reset_filters,refresh",
      `${user.label}: ${item.key} UI action order mismatch`,
      { actionKeys }
    );
  }
  return { apiState, url: page.url(), actionKeys: actionKeys.slice(0, 3) };
}

async function checkComparisonReport(page, user) {
  const response = await callMethod(page, "erp_workspace_ui.procurement_console.report.get_procurement_console_report_context", {
    report_key: "supplier_quotation_comparison",
  });
  assert(response.ok, `${user.label}: comparison report API failed`, response);
  const payload = response.data.message || {};
  const state = stateKind(payload);
  assert(["ready", "empty", "restricted", "unavailable"].includes(state), `${user.label}: comparison report invalid state`, { state, payload });
  assertNoForbiddenActions(payload, "supplier_quotation_comparison");

  if (state === "ready" || state === "empty") {
    const actions = ((payload.controls || {}).actions || []).map((action) => action.key);
    assert(actions.slice(0, 2).join(",") === "refresh,back_to_console", `${user.label}: comparison report action order mismatch`, { actions });
  }

  await openDeskRoute(page, "/desk/procurement-console-report/supplier-quotation-comparison");
  await page.locator(".erpw-report-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  const pageText = normalizeText(await page.locator(".erpw-report-shell").first().innerText({ timeout: TIMEOUT }));
  assert(/Supplier Quotation Comparison|unavailable|restricted/i.test(pageText), `${user.label}: comparison report did not render expected shell`, { pageText });
  const actionKeys = await page.locator("[data-erpw-report-action-key]").evaluateAll((nodes) =>
    nodes.map((node) => node.getAttribute("data-erpw-report-action-key"))
  );
  const forbidden = actionKeys.filter((key) => FORBIDDEN_ACTION_RE.test(key || ""));
  assert(forbidden.length === 0, `${user.label}: comparison report forbidden UI action exposed`, { forbidden });
  return { apiState: state, url: page.url(), actionKeys: actionKeys.slice(0, 4) };
}

async function checkReadyProcurementUser(page, user, report) {
  await openDeskRoute(page, "/desk/procurement-console");
  await page.locator(".sales-console-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  await page.waitForFunction(() => {
    const shell = document.querySelector(".sales-console-shell");
    return shell && shell.getAttribute("data-erpw-console-bootstrap") === "ready";
  }, null, { timeout: TIMEOUT });

  report.worklists = {};
  for (const item of WORKLISTS) {
    const apiState = await checkWorklistApi(page, item.key);
    if (user.key === "manager") {
      assert(
        apiState === "ready" || apiState === "empty",
        `${user.label}: ${item.key} did not expose the Phase 2 buyer surface`,
        { apiState }
      );
    }
    report.worklists[item.key] = await checkWorklistPage(page, user, item, apiState);
  }
  report.report = await checkComparisonReport(page, user);
  if (user.key === "manager") {
    assert(
      report.report.apiState === "ready" || report.report.apiState === "empty",
      `${user.label}: comparison report did not expose the governed Phase 2 wrapper`,
      report.report
    );
  }
}

async function checkRestrictedProcurementRoute(page, user, report) {
  await openDeskRoute(page, "/desk/procurement-console");
  await page.locator(".sales-console-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  const pageText = normalizeText(await page.locator(".sales-console-shell").first().innerText({ timeout: TIMEOUT }));
  assert(/restricted/i.test(pageText), `${user.label}: restricted direct URL did not render restricted state`, { pageText });
  report.directRoute = "restricted";
}

async function runUser(browser, user) {
  const context = await browser.newContext({
    baseURL: BASE_URL,
    ignoreHTTPSErrors: true,
    viewport: { width: 1440, height: 1000 },
  });
  const page = await context.newPage();
  const pageErrors = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));

  const report = { user: user.key };
  try {
    await login(page, user);
    await openDeskRoute(page, "/desk/sales-console");

    const bootstrap = await callMethod(page, "erp_workspace_ui.procurement_console.service.get_procurement_console_bootstrap");
    assert(bootstrap.ok, `${user.label}: bootstrap API failed`, bootstrap);
    const state = bootstrap.data && bootstrap.data.message && bootstrap.data.message.state ? bootstrap.data.message.state.kind : "missing";
    report.bootstrapState = state;

    if (state === "ready") {
      await checkReadyProcurementUser(page, user, report);
    } else {
      assert(state === "restricted", `${user.label}: unexpected Procurement bootstrap state`, { state, bootstrap });
      await checkRestrictedProcurementRoute(page, user, report);
    }

    assert(pageErrors.length === 0, `${user.label}: page JS error`, { pageErrors });
    return report;
  } finally {
    await context.close();
  }
}

(async () => {
  assert(USERS.length > 0, "No smoke users are available in environment variables");
  const browser = await chromium.launch({ headless: true });
  try {
    const reports = [];
    for (const user of USERS) {
      reports.push(await runUser(browser, user));
    }
    console.log(JSON.stringify({ ok: true, baseUrl: BASE_URL, reports }, null, 2));
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error.stack || error.message);
  if (error.details) console.error(JSON.stringify(error.details, null, 2));
  process.exit(1);
});
