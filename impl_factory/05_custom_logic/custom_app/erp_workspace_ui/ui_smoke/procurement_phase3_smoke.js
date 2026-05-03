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
  { key: "purchase_orders_due_soon", route: "/desk/procurement-console-worklist/purchase-orders-due-soon" },
  { key: "purchase_orders_overdue", route: "/desk/procurement-console-worklist/purchase-orders-overdue" },
  { key: "purchase_orders_late_or_unreceived", route: "/desk/procurement-console-worklist/purchase-orders-late-or-unreceived" },
  { key: "purchase_orders_partially_received", route: "/desk/procurement-console-worklist/purchase-orders-partially-received" },
  { key: "purchase_orders_not_billed_visibility", route: "/desk/procurement-console-worklist/purchase-orders-not-billed-visibility" },
  { key: "purchase_orders_supplier_follow_up", route: "/desk/procurement-console-worklist/purchase-orders-supplier-follow-up" },
];

const FORBIDDEN_ACTION_RE = /(approve|reject|submit|cancel|amend|close|unclose|receive|receipt|bill|invoice|pay|payment|item_price|default_supplier|set_default_supplier|supplier_ack|acknowledg)/i;

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

function stateKind(payload) {
  return payload && payload.results && payload.results.state ? payload.results.state.kind : payload && payload.state ? payload.state.kind : "missing";
}

function collectActions(payload) {
  const actions = [];
  const controls = payload && payload.controls ? payload.controls : {};
  valuesFromContainer(controls.actions).forEach((action) => pushAction(actions, action));
  ((payload && payload.results && payload.results.rows) || []).forEach((row) => {
    valuesFromContainer(row.actions).forEach((action) => pushAction(actions, action));
    valuesFromContainer(row.cells).forEach((cell) => {
      if (cell && typeof cell === "object" && cell.actionKey) pushAction(actions, { key: cell.actionKey, label: cell.actionKey });
    });
  });
  Object.values((payload && payload.action_targets) || {}).forEach((target) => pushAction(actions, target));
  return actions;
}

function assertNoForbiddenActions(payload, label) {
  const offenders = collectActions(payload)
    .map((action) => `${action.key || ""} ${action.label || ""} ${action.kind || ""} ${action.route || ""} ${action.doctype || ""}`)
    .filter((value) => FORBIDDEN_ACTION_RE.test(value));
  assert(offenders.length === 0, `${label}: forbidden mutation action exposed`, { offenders });
}

function assertNoNativePurchaseOrderFormTargets(payload, label) {
  const targets = Object.values((payload && payload.action_targets) || {});
  const offenders = targets.filter((target) => target && target.kind === "form" && target.doctype === "Purchase Order");
  assert(offenders.length === 0, `${label}: native Purchase Order form target exposed`, { offenders });
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
  if (/\/login(?:[/?#]|$)/.test(page.url())) throw new Error(`Route ${route} redirected to login`);
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

async function checkWorklist(page, item, user) {
  const response = await callMethod(page, "erp_workspace_ui.procurement_console.worklist.get_procurement_console_worklist_context", {
    queue_key: item.key,
  });
  assert(response.ok, `${item.key}: worklist API failed`, response);
  const payload = response.data.message || {};
  const state = stateKind(payload);
  assert(["ready", "empty", "restricted", "unavailable"].includes(state), `${item.key}: invalid state`, { state, payload });
  assertNoForbiddenActions(payload, item.key);
  assertNoNativePurchaseOrderFormTargets(payload, item.key);
  if (user.key === "manager") {
    assert(state === "ready" || state === "empty", `${item.key}: manager did not receive Phase 3 queue`, { state });
  }

  await openDeskRoute(page, item.route);
  await page.locator(".erpw-list-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  const actionKeys = await page.locator("[data-erpw-list-action-key]").evaluateAll((nodes) =>
    nodes.map((node) => node.getAttribute("data-erpw-list-action-key"))
  );
  const forbidden = actionKeys.filter((key) => FORBIDDEN_ACTION_RE.test(key || ""));
  assert(forbidden.length === 0, `${item.key}: forbidden UI action exposed`, { forbidden });
  if (state === "ready" || state === "empty") {
    assert(actionKeys.slice(0, 3).join(",") === "apply_filters,reset_filters,refresh", `${item.key}: UI action order mismatch`, { actionKeys });
  }
  return { apiState: state, actionKeys: actionKeys.slice(0, 3), firstRow: ((payload.results || {}).rows || [])[0] || null };
}

async function checkDetail(page, purchaseOrderName) {
  const route = purchaseOrderName
    ? `/desk/procurement-console-po-follow-up/${encodeURIComponent(purchaseOrderName)}`
    : "/desk/procurement-console-po-follow-up";
  await openDeskRoute(page, route);
  await page.locator(".erpw-procurement-po-follow-up-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  const text = normalizeText(await page.locator(".erpw-procurement-po-follow-up-shell").first().innerText({ timeout: TIMEOUT }));
  assert(/Purchase Order|follow-up|required|Item lines|unavailable/i.test(text), "Detail page did not render expected read-only shell", { text });
  const detailResponse = await callMethod(page, "erp_workspace_ui.procurement_console.purchase_order_detail.get_purchase_order_follow_up_detail_context", {
    purchase_order: purchaseOrderName || "",
  });
  assert(detailResponse.ok, "Detail API failed", detailResponse);
  const payload = detailResponse.data.message || {};
  assert(["ready", "restricted", "unavailable", "empty"].includes((payload.detail && payload.detail.state && payload.detail.state.kind) || "missing"), "Detail API invalid state", payload);
  assertNoForbiddenActions(payload, "po_follow_up_detail");
  return { route, state: payload.detail && payload.detail.state ? payload.detail.state.kind : "missing" };
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
    await openDeskRoute(page, "/desk/procurement-console");
    const bootstrap = await callMethod(page, "erp_workspace_ui.procurement_console.service.get_procurement_console_bootstrap");
    assert(bootstrap.ok, `${user.label}: bootstrap failed`, bootstrap);
    const state = bootstrap.data && bootstrap.data.message && bootstrap.data.message.state ? bootstrap.data.message.state.kind : "missing";
    report.bootstrapState = state;
    if (state === "ready") {
      report.worklists = {};
      let firstPoName = process.env.ERPW_PROCUREMENT_PO_NAME || "";
      for (const item of WORKLISTS) {
        const result = await checkWorklist(page, item, user);
        report.worklists[item.key] = result;
        if (!firstPoName && result.firstRow && result.firstRow.name) firstPoName = result.firstRow.name;
      }
      report.detail = await checkDetail(page, firstPoName);
    } else {
      assert(state === "restricted", `${user.label}: unexpected bootstrap state`, { state });
      await openDeskRoute(page, "/desk/procurement-console-worklist/purchase-orders-overdue");
      await page.locator(".erpw-list-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
      report.restrictedRoute = true;
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
