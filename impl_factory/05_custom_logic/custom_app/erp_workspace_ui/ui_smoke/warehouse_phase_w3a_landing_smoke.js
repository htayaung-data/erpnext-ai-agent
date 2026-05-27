const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const TIMEOUT = Number(process.env.ERPW_WAREHOUSE_W3A_TIMEOUT || process.env.ERPW_WAREHOUSE_W3_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_WAREHOUSE_W3A_ARTIFACT_DIR || path.join(
  fs.existsSync("/freeze-artifacts") ? "/freeze-artifacts" : path.join(__dirname, "artifacts"),
  `warehouse-w3a-landing-${new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z")}`
);
const ASSET_ROOT = process.env.ERPW_WAREHOUSE_W3A_ASSET_ROOT || process.env.ERPW_WAREHOUSE_W3_ASSET_ROOT || "";

const WAREHOUSE_USERS = [
  {
    key: "warehouse-manager",
    label: "Warehouse Manager",
    username: process.env.ERPW_WAREHOUSE_MANAGER_USERNAME || process.env.ERPW_STOCK_MANAGER_USERNAME,
    password: process.env.ERPW_WAREHOUSE_MANAGER_PASSWORD || process.env.ERPW_STOCK_MANAGER_PASSWORD,
  },
  {
    key: "warehouse-user",
    label: "Warehouse User",
    username: process.env.ERPW_WAREHOUSE_USER_USERNAME || process.env.ERPW_STOCK_USER_USERNAME || process.env.ERPW_USER_USERNAME,
    password: process.env.ERPW_WAREHOUSE_USER_PASSWORD || process.env.ERPW_STOCK_USER_PASSWORD || process.env.ERPW_USER_PASSWORD,
  },
].filter((user) => user.username && user.password);

const ADMIN_USERS = [
  {
    key: "system-manager",
    label: "System Manager",
    username: process.env.ERPW_SYSTEM_MANAGER_USERNAME || process.env.ERPW_ADMIN_USERNAME,
    password: process.env.ERPW_SYSTEM_MANAGER_PASSWORD || process.env.ERPW_ADMIN_PASSWORD,
  },
].filter((user) => user.username && user.password);

const FORBIDDEN_ACTION_RE = /\b(Receive|Ship|Dispatch|Post|Submit|Cancel|Amend|Reconcile|Stock Entry|Purchase Receipt|Delivery Note|Stock Reconciliation|Reserve|Unreserve|Assign Serial|Assign Batch|Item Price|Default Supplier|Item Supplier)\b/i;
const FORBIDDEN_COPY_RE = /\b(Productized|native ERP|governed|deferred|route only|mutation|backend|frontend|framework|Frappe|smoke|test)\b/i;
const NATIVE_ROUTE_RE = /\/desk\/Form\/|\/app\/(?!warehouse-console(?:$|[?#/]))|#Form\/|query-report|\/desk\/List\//i;
const VALUATION_RE = /stock value|valuation rate|stock_value|valuation_rate/i;

fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

function assert(condition, message, details = {}) {
  if (!condition) {
    const error = new Error(message);
    error.details = details;
    throw error;
  }
}

function routeUrl(route) {
  return new URL(route, BASE_URL).toString();
}

function safeName(value) {
  return String(value || "artifact").replace(/[^a-z0-9_-]+/gi, "-").replace(/^-+|-+$/g, "").toLowerCase();
}

function bounded(value, length = 700) {
  const text = String(value || "");
  return text.length > length ? `${text.slice(0, length)}...` : text;
}

async function capture(page, name) {
  const file = path.join(ARTIFACT_DIR, `${safeName(name)}.png`);
  await page.screenshot({ path: file, fullPage: true, animations: "disabled" });
  return file;
}

function sourceFile(relativePath) {
  return ASSET_ROOT ? path.join(ASSET_ROOT, relativePath) : "";
}

function readSource(relativePath) {
  const file = sourceFile(relativePath);
  return file && fs.existsSync(file) ? fs.readFileSync(file, "utf8") : "";
}

function makeDiagnostics(label) {
  return {
    label,
    consoleErrors: [],
    pageErrors: [],
    failedResponses: [],
    failedRequests: [],
    overrideHits: [],
    snapshots: [],
  };
}

function remember(list, item, limit = 80) {
  list.push(item);
  if (list.length > limit) list.shift();
}

function attachPageDiagnostics(page, diagnostics) {
  page.on("console", (message) => {
    if (!["error", "warning"].includes(message.type())) return;
    remember(diagnostics.consoleErrors, {
      type: message.type(),
      text: bounded(message.text(), 900),
      location: message.location(),
    });
  });
  page.on("pageerror", (error) => {
    remember(diagnostics.pageErrors, {
      message: bounded(error && error.message ? error.message : String(error), 900),
      stack: bounded(error && error.stack ? error.stack : "", 1200),
    });
  });
  page.on("requestfailed", (request) => {
    remember(diagnostics.failedRequests, {
      url: bounded(request.url(), 900),
      method: request.method(),
      failure: request.failure(),
    });
  });
  page.on("response", (response) => {
    if (response.ok()) return;
    const url = response.url();
    if (!/warehouse|desk_page|getpage|assets\/erp_workspace_ui|api\/method/i.test(url)) return;
    remember(diagnostics.failedResponses, {
      url: bounded(url, 900),
      status: response.status(),
      statusText: response.statusText(),
    });
  });
}

function requestText(request) {
  const url = request.url();
  const postData = request.postData() || "";
  let jsonText = "";
  try {
    const json = request.postDataJSON();
    jsonText = JSON.stringify(json || {});
  } catch (error) {
    jsonText = "";
  }
  return `${url} ${postData} ${jsonText}`;
}

function requestMentionsWarehouseConsole(request) {
  return /warehouse-console/i.test(requestText(request));
}

function recordOverrideHit(diagnostics, key, request, extra = {}) {
  if (!diagnostics) return;
  remember(diagnostics.overrideHits, {
    key,
    url: bounded(request.url(), 900),
    method: request.method(),
    postData: bounded(request.postData() || "", 500),
    ...extra,
  });
}

async function diagnosticSnapshot(page, diagnostics, label) {
  const screenshot = await capture(page, `${safeName(label)}-diagnostic`).catch(() => "");
  const snapshot = await page.evaluate(() => {
    const route = window.frappe && typeof frappe.get_route === "function" ? frappe.get_route() : null;
    const scripts = Array.from(document.scripts || []).map((script) => script.src || "").filter(Boolean);
    return {
      url: location.href,
      title: document.title,
      route,
      bodyText: (document.body && document.body.innerText || "").replace(/\s+/g, " ").trim().slice(0, 2400),
      hasFrappe: Boolean(window.frappe),
      hasWarehousePageDef: Boolean(window.frappe && frappe.pages && frappe.pages["warehouse-console"]),
      hasWarehouseShell: Boolean(document.querySelector('.sales-console-shell[data-erpw-workspace="warehouse"]')),
      hasWarehouseBoot: Boolean(window.erpWorkspaceUiBoot),
      hasWarehouseRegistry: Boolean(window.erpWorkspaceUiWorkspaceRegistry),
      scriptSources: scripts.filter((src) => /erp_workspace_ui|warehouse/i.test(src)).slice(-30),
    };
  }).catch((error) => ({ error: error && error.message ? error.message : String(error) }));
  snapshot.screenshot = screenshot;
  remember(diagnostics.snapshots, { label, ...snapshot }, 30);
  return snapshot;
}

function sourceSidebarPayload(allowed) {
  const items = allowed ? [{ key: "warehouse_console_home", label: "Overview", icon: "item", target: { kind: "page", route: "warehouse-console" } }] : [];
  return {
    workspace: {
      workspace_id: "warehouse",
      title: "Warehouse Console",
      routes: { home: "warehouse-console", home_path: "/desk/warehouse-console" },
      search: { enabled: false },
    },
    context: { has_warehouse_access: allowed },
    state: allowed
      ? { kind: "ready", title: "Warehouse Console ready", detail: "Stock visibility and warehouse posture are available for review." }
      : { kind: "restricted", title: "Warehouse Console is restricted", detail: "This page is available only to Warehouse roles." },
    sidebar: {
      workspace_id: "warehouse",
      title: "Warehouse Console",
      mode_label: "Warehouse Workspace",
      scope_label: allowed ? "Stock workbench" : "Restricted",
      active_key: "warehouse_console_home",
      home_key: "warehouse_console_home",
      items,
      sections: items.length ? [{ key: "workspace", label: "Workspace", items }] : [],
    },
    fetched_at: "2026-05-26 00:00:00",
  };
}

function sourceOverviewPayload() {
  return {
    workspace: {
      workspace_id: "warehouse",
      title: "Warehouse Console",
      routes: { home: "warehouse-console", home_path: "/desk/warehouse-console" },
      search: { enabled: false },
    },
    context: { has_warehouse_access: true, role_family: "Warehouse", role_variant: "warehouse_manager", can_view_valuation: false },
    state: { kind: "ready", title: "Warehouse Console ready", detail: "Stock visibility and warehouse posture are available for review." },
    sidebar: sourceSidebarPayload(true).sidebar,
    kpis: [
      { key: "active_warehouses", label: "Active Warehouses", value: 4, state: "live", note: "Warehouse locations available for stock review." },
      { key: "stocked_items", label: "Stocked Items", value: 18, state: "live", note: "Item and warehouse positions with stock on hand." },
      { key: "low_stock", label: "Low Stock", value: 2, state: "live", note: "Projected quantity below zero." },
      { key: "receiving_due", label: "Receiving Due", value: 3, state: "live", note: "Submitted purchase orders due for receipt." },
      { key: "outbound_due", label: "Outbound Due", value: 1, state: "live", note: "Open picking work visible to your role." },
      { key: "transfer_requests", label: "Transfer Requests", value: 2, state: "live", note: "Internal warehouse requests waiting for review." },
    ],
    sections: [
      { key: "needs_attention", title: "Needs Attention", summary: "Warehouse work that may need review today.", cards: [
        { key: "low_stock", title: "Low Stock", value: 2, state: "live", note: "Projected quantity below zero." },
        { key: "receiving_due", title: "Receiving Due", value: 3, state: "live", note: "Submitted purchase orders due for receipt." },
      ] },
      { key: "inbound_work", title: "Inbound Work", summary: "Receiving posture from visible purchase activity.", cards: [
        { key: "receiving_due", title: "Receiving Due", value: 3, state: "live", note: "Submitted purchase orders due for receipt." },
      ] },
      { key: "outbound_work", title: "Outbound Work", summary: "Picking posture visible to Warehouse roles.", cards: [
        { key: "outbound_due", title: "Outbound Due", value: 1, state: "live", note: "Open picking work visible to your role." },
      ] },
      { key: "stock_health", title: "Stock Health", summary: "Stocked items and projected shortages.", cards: [
        { key: "stocked_items", title: "Stocked Items", value: 18, state: "live", note: "Item and warehouse positions with stock on hand." },
        { key: "low_stock", title: "Low Stock", value: 2, state: "live", note: "Projected quantity below zero." },
      ] },
      { key: "movement_watch", title: "Movement Watch", summary: "Internal transfer demand visible to Warehouse roles.", cards: [
        { key: "transfer_requests", title: "Transfer Requests", value: 2, state: "live", note: "Internal warehouse requests waiting for review." },
      ] },
    ],
    allowed_actions: [{ key: "refresh", label: "Refresh", kind: "read_only" }],
    action_targets: {},
    valuation: { visible: false, fields: [] },
    fetched_at: "2026-05-26 00:00:00",
  };
}

async function installSourceOverrides(context, diagnostics) {
  if (!ASSET_ROOT) return;
  const assetMappings = [
    {
      key: "boot-asset",
      pattern: /\/assets\/erp_workspace_ui\/js\/erp_workspace_ui_boot\.js(?:\?|$)/,
      file: "erp_workspace_ui/public/js/erp_workspace_ui_boot.js",
      contentType: "application/javascript",
    },
    {
      key: "warehouse-page-asset",
      pattern: /\/assets\/erp_workspace_ui\/js\/warehouse_console\/warehouse_console_page\.js(?:\?|$)/,
      file: "erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js",
      contentType: "application/javascript",
    },
    {
      key: "workspace-registry-asset",
      pattern: /\/assets\/erp_workspace_ui\/js\/runtime\/console\/workspace_registry\.js(?:\?|$)/,
      file: "erp_workspace_ui/public/js/runtime/console/workspace_registry.js",
      contentType: "application/javascript",
    },
    {
      key: "workspace-sidebar-asset",
      pattern: /\/assets\/erp_workspace_ui\/js\/runtime\/console\/workspace_console_sidebar\.js(?:\?|$)/,
      file: "erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js",
      contentType: "application/javascript",
    },
  ];
  for (const mapping of assetMappings) {
    await context.route((url) => mapping.pattern.test(url.pathname + url.search), async (route) => {
      const body = readSource(mapping.file);
      recordOverrideHit(diagnostics, mapping.key, route.request(), { fulfilled: Boolean(body), file: mapping.file });
      if (body) return route.fulfill({ status: 200, body, contentType: mapping.contentType });
      return route.continue();
    });
  }
  await context.route("**/api/method/frappe.desk.desk_page.getpage**", async (route) => {
    const request = route.request();
    if (!requestMentionsWarehouseConsole(request)) return route.continue();
    const script = readSource("erp_workspace_ui/erp_workspace_ui/page/warehouse_console/warehouse_console.js");
    recordOverrideHit(diagnostics, "desk-page-getpage", request, { fulfilled: Boolean(script) });
    const pageDoc = {
      doctype: "Page",
      name: "warehouse-console",
      page_name: "warehouse-console",
      title: "Warehouse Console",
      module: "ERP Workspace UI",
      standard: "Yes",
      content: "",
      script,
    };
    return route.fulfill({
      status: script ? 200 : 404,
      contentType: "application/json",
      body: JSON.stringify({ docs: [pageDoc], message: pageDoc }),
    });
  });
  await context.route("**/api/method/erp_workspace_ui.warehouse_console.service.get_warehouse_console_overview**", async (route) => {
    recordOverrideHit(diagnostics, "warehouse-overview", route.request(), { fulfilled: true });
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ message: sourceOverviewPayload() }) });
  });
  await context.route("**/api/method/erp_workspace_ui.warehouse_console.service.get_warehouse_console_sidebar_context**", async (route) => {
    recordOverrideHit(diagnostics, "warehouse-sidebar", route.request(), { fulfilled: true });
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ message: sourceSidebarPayload(true) }) });
  });
}

async function login(page, user) {
  await page.goto(routeUrl("/login"), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  await page.locator("#login_email, input[name=usr], input[name=login_email], input[type=email], input[type=text]").first().fill(user.username, { timeout: TIMEOUT });
  await page.locator("#login_password, input[name=pwd], input[name=login_password], input[type=password]").first().fill(user.password, { timeout: TIMEOUT });
  await Promise.all([
    page.waitForURL(/\/(?:app|desk)(?:[/?#]|$)/, { waitUntil: "domcontentloaded", timeout: TIMEOUT }),
    page.locator("button.btn-login, .btn-login, button[type=submit]").first().click(),
  ]);
}

async function waitForWarehouseLanding(page, diagnostics, label) {
  try {
    await page.waitForFunction(() => {
      const path = String(window.location && window.location.pathname || "").replace(/\/+$/, "");
      const route = window.frappe && typeof frappe.get_route === "function" ? frappe.get_route() : [];
      return path === "/desk/warehouse-console" || path === "/app/warehouse-console" || String(route[0] || "") === "warehouse-console";
    }, null, { timeout: TIMEOUT });
    await page.waitForSelector('.sales-console-shell[data-erpw-workspace="warehouse"]', { state: "visible", timeout: TIMEOUT });
    await waitForWarehouseReady(page);
  } catch (error) {
    const snapshot = await diagnosticSnapshot(page, diagnostics, `${label}-landing-timeout`);
    error.details = { ...(error.details || {}), diagnostics, snapshot };
    throw error;
  }
}

async function waitForWarehouseReady(page) {
  await page.waitForFunction(() => {
    const shell = document.querySelector('.sales-console-shell[data-erpw-workspace="warehouse"]');
    const state = shell && shell.getAttribute("data-warehouse-console-state");
    return (shell && shell.getAttribute("data-erpw-console-bootstrap") === "ready" && document.querySelectorAll(".warehouse-console-kpi-card").length >= 6) || state === "restricted";
  }, null, { timeout: TIMEOUT });
}

async function snapshot(page) {
  return page.evaluate(() => {
    const visible = (node) => {
      if (!node) return false;
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
    };
    const shell = document.querySelector('.sales-console-shell[data-erpw-workspace="warehouse"]');
    const shellRoot = shell || document.createElement("div");
    const text = (shellRoot.innerText || "").replace(/\s+/g, " ").trim();
    const actionText = Array.from(shellRoot.querySelectorAll("button, a, [role=button]"))
      .filter(visible)
      .map((node) => (node.innerText || node.getAttribute("aria-label") || node.getAttribute("href") || "").replace(/\s+/g, " ").trim())
      .filter(Boolean)
      .join(" ");
    const hrefs = Array.from(shellRoot.querySelectorAll("a[href]")).map((node) => node.getAttribute("href") || "").join(" ");
    const route = window.frappe && typeof frappe.get_route === "function" ? frappe.get_route() : null;
    const path = String(window.location && window.location.pathname || "").replace(/\/+$/, "");
    return {
      url: location.href,
      path,
      route,
      isWarehouseRoute: path === "/desk/warehouse-console" || path === "/app/warehouse-console" || Boolean(route && String(route[0] || "") === "warehouse-console"),
      text,
      actionText,
      hrefs,
      shellCount: Array.from(document.querySelectorAll('.sales-console-shell[data-erpw-workspace="warehouse"]')).filter(visible).length,
      headerCount: Array.from(document.querySelectorAll(".warehouse-console-header")).filter(visible).length,
      kpiCount: Array.from(document.querySelectorAll(".warehouse-console-kpi-card")).filter(visible).length,
      sectionCount: Array.from(document.querySelectorAll("[data-warehouse-section]")).filter(visible).length,
      searchUtilityVisible: Array.from(document.querySelectorAll("[data-erpw-sales-search-open]")).some(visible),
      horizontalOverflow: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
      globalNativeWorkspaceText: (document.body && document.body.innerText || "").replace(/\s+/g, " ").trim().slice(0, 1400),
      state: shell && shell.getAttribute ? shell.getAttribute("data-warehouse-console-state") || "" : "",
    };
  });
}

function assertWarehouseState(state, user, step) {
  assert(state.isWarehouseRoute, "Warehouse user did not settle on Warehouse Console route", { user, step, state });
  assert(state.shellCount === 1, "Warehouse shell count must remain 1", { user, step, state });
  assert(state.headerCount === 1, "Warehouse header count must remain 1", { user, step, state });
  assert(state.kpiCount >= 6, "Warehouse KPI cards did not render", { user, step, state });
  assert(state.sectionCount >= 5, "Warehouse overview sections did not render", { user, step, state });
  assert(state.horizontalOverflow <= 2, "Warehouse landing has horizontal overflow", { user, step, state });
  assert(!state.searchUtilityVisible, "Warehouse search entry must stay inactive in W3A", { user, step, state });
  assert(!FORBIDDEN_ACTION_RE.test(state.actionText), "Forbidden stock action control is visible", { user, step, state });
  assert(!FORBIDDEN_COPY_RE.test(state.text), "Developer or governance copy is visible inside Warehouse shell", { user, step, state });
  assert(!VALUATION_RE.test(state.text), "Valuation text is visible inside Warehouse shell", { user, step, state });
  assert(!NATIVE_ROUTE_RE.test(`${state.hrefs} ${state.actionText}`), "Native route target is visible inside Warehouse shell", { user, step, state });
}

function assertNoRuntimeFailures(diagnostics, user, step) {
  assert(!diagnostics.consoleErrors.some((entry) => entry.type === "error"), "Landing smoke recorded console errors", { user, step, diagnostics });
  assert(diagnostics.pageErrors.length === 0, "Landing smoke recorded page errors", { user, step, diagnostics });
  assert(diagnostics.failedResponses.length === 0, "Landing smoke recorded failed Warehouse responses", { user, step, diagnostics });
}

async function verifyWarehouseLandingStep(page, diagnostics, user, step) {
  await waitForWarehouseLanding(page, diagnostics, `${user.key}-${step}`);
  const state = await snapshot(page);
  assertWarehouseState(state, user.key, step);
  await capture(page, `${user.key}-${step}`);
  assertNoRuntimeFailures(diagnostics, user.key, step);
  return state;
}

async function exerciseWarehouseUser(browser, user) {
  const diagnostics = makeDiagnostics(user.key);
  const context = await browser.newContext({ viewport: { width: 1240, height: 768 } });
  await installSourceOverrides(context, diagnostics);
  const page = await context.newPage();
  attachPageDiagnostics(page, diagnostics);
  const steps = [];
  try {
    await login(page, user);
    steps.push({ step: "login-landing", state: await verifyWarehouseLandingStep(page, diagnostics, user, "login-landing") });

    await page.goto(routeUrl("/desk"), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
    steps.push({ step: "plain-desk", state: await verifyWarehouseLandingStep(page, diagnostics, user, "plain-desk") });

    await page.reload({ waitUntil: "domcontentloaded", timeout: TIMEOUT });
    steps.push({ step: "refresh", state: await verifyWarehouseLandingStep(page, diagnostics, user, "refresh") });

    await page.goto(routeUrl("/desk/warehouse-console"), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
    steps.push({ step: "direct-route", state: await verifyWarehouseLandingStep(page, diagnostics, user, "direct-route") });

    await page.goto(routeUrl("/desk"), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
    steps.push({ step: "repeat-plain-desk", state: await verifyWarehouseLandingStep(page, diagnostics, user, "repeat-plain-desk") });

    await context.close();
    return { user: user.key, steps, diagnostics };
  } catch (error) {
    error.details = { ...(error.details || {}), diagnostics };
    await context.close().catch(() => {});
    throw error;
  }
}

async function exerciseAdminBypass(browser, user) {
  const diagnostics = makeDiagnostics(user.key);
  const context = await browser.newContext({ viewport: { width: 1240, height: 768 } });
  await installSourceOverrides(context, diagnostics);
  const page = await context.newPage();
  attachPageDiagnostics(page, diagnostics);
  try {
    await login(page, user);
    await page.goto(routeUrl("/desk"), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
    await page.waitForTimeout(1800);
    const state = await snapshot(page);
    await capture(page, `${user.key}-desk-bypass`);
    assert(!state.isWarehouseRoute, "Admin-style user must not be forced to Warehouse Console", { user: user.key, state, diagnostics });
    assert(state.shellCount === 0, "Admin-style user should not have Warehouse shell on native Desk", { user: user.key, state, diagnostics });
    assertNoRuntimeFailures(diagnostics, user.key, "admin-bypass");
    await context.close();
    return { user: user.key, state, diagnostics };
  } catch (error) {
    error.details = { ...(error.details || {}), diagnostics };
    await context.close().catch(() => {});
    throw error;
  }
}

(async () => {
  assert(WAREHOUSE_USERS.length > 0, "No Warehouse landing credentials were provided. Set ERPW_WAREHOUSE_MANAGER_USERNAME/PASSWORD or ERPW_WAREHOUSE_USER_USERNAME/PASSWORD.");
  const browser = await chromium.launch({ headless: process.env.ERPW_HEADLESS !== "0" });
  const summary = {
    status: "pass",
    artifactDir: ARTIFACT_DIR,
    sourceOverride: Boolean(ASSET_ROOT),
    warehouseUsers: WAREHOUSE_USERS.map((user) => user.key),
    adminUsers: ADMIN_USERS.map((user) => user.key),
    warehouse: [],
    adminBypass: [],
  };
  try {
    for (const user of WAREHOUSE_USERS) {
      summary.warehouse.push(await exerciseWarehouseUser(browser, user));
    }
    if (ADMIN_USERS.length) {
      summary.adminBypass.push(await exerciseAdminBypass(browser, ADMIN_USERS[0]));
    }
    fs.writeFileSync(path.join(ARTIFACT_DIR, "warehouse-w3a-landing-summary.json"), `${JSON.stringify(summary, null, 2)}\n`);
  } catch (error) {
    summary.status = "fail";
    summary.error = error && error.message ? error.message : String(error);
    summary.details = error && error.details ? error.details : {};
    fs.writeFileSync(path.join(ARTIFACT_DIR, "warehouse-w3a-landing-summary.json"), `${JSON.stringify(summary, null, 2)}\n`);
    throw error;
  } finally {
    await browser.close();
  }
  console.log(`Warehouse W3A landing smoke passed. Summary: ${path.join(ARTIFACT_DIR, "warehouse-w3a-landing-summary.json")}`);
})().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exit(1);
});
