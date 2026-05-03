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
  const state = payload.results && payload.results.state ? payload.results.state.kind : "missing";
  assert(["ready", "empty", "restricted", "unavailable"].includes(state), `${queueKey}: invalid state kind`, { state, payload });

  if (state === "ready" || state === "empty") {
    const actions = ((payload.controls || {}).actions || []).map((action) => action.key);
    assert(
      actions.slice(0, 3).join(",") === "refresh,reset_filters,apply_filters",
      `${queueKey}: action order mismatch`,
      { actions }
    );
  }
  return state;
}

async function checkReadyProcurementUser(page, user, report) {
  await openDeskRoute(page, "/desk/procurement-console");
  await page.locator(".sales-console-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  await page.waitForFunction(() => {
    const shell = document.querySelector(".sales-console-shell");
    return shell && shell.getAttribute("data-erpw-console-bootstrap") === "ready";
  }, null, { timeout: TIMEOUT });

  const title = normalizeText(await page.locator(".sales-console-title").first().innerText({ timeout: TIMEOUT }));
  assert(title === "Procurement Console", `${user.label}: console title mismatch`, { title });

  const queueRoutes = [
    { key: "supplier_directory", route: "/desk/procurement-console-worklist/supplier-directory" },
    { key: "purchase_request_directory", route: "/desk/procurement-console-worklist/purchase-request-directory" },
    { key: "purchase_order_directory", route: "/desk/procurement-console-worklist/purchase-order-directory" },
    { key: "requests_to_source", route: "/desk/procurement-console-worklist/requests-to-source" },
    { key: "purchase_orders_open", route: "/desk/procurement-console-worklist/purchase-orders-open" },
  ];

  report.worklists = {};
  for (const item of queueRoutes) {
    const apiState = await checkWorklistApi(page, item.key);
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
    if (apiState === "ready" || apiState === "empty") {
      assert(
        actionKeys.slice(0, 3).join(",") === "refresh,reset_filters,apply_filters",
        `${user.label}: ${item.key} UI action order mismatch`,
        { actionKeys }
      );
    }
    report.worklists[item.key] = { apiState, url: page.url(), actionKeys: actionKeys.slice(0, 3) };
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
