const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const TIMEOUT = Number(process.env.ERPW_WAREHOUSE_W3_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_WAREHOUSE_W3_ARTIFACT_DIR || path.join(
  fs.existsSync("/freeze-artifacts") ? "/freeze-artifacts" : path.join(__dirname, "artifacts"),
  `warehouse-w3-${new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z")}`
);
const ASSET_ROOT = process.env.ERPW_WAREHOUSE_W3_ASSET_ROOT || "";

const AUTHORIZED_USERS = [
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

const UNAUTHORIZED_USERS = [
  {
    key: "purchase-manager",
    label: "Purchase Manager",
    username: process.env.ERPW_PURCHASE_MANAGER_USERNAME,
    password: process.env.ERPW_PURCHASE_MANAGER_PASSWORD,
  },
  {
    key: "sales-manager",
    label: "Sales Manager",
    username: process.env.ERPW_SALES_MANAGER_USERNAME,
    password: process.env.ERPW_SALES_MANAGER_PASSWORD,
  },
].filter((user) => user.username && user.password);

const VIEWPORTS = [
  { key: "laptop-1136", width: 1136, height: 768 },
  { key: "laptop-1240", width: 1240, height: 768 },
  { key: "desktop-1440", width: 1440, height: 900 },
];

const FORBIDDEN_ACTION_RE = /\b(Receive|Ship|Dispatch|Post|Submit|Cancel|Amend|Reconcile|Stock Entry|Purchase Receipt|Delivery Note|Stock Reconciliation|Reserve|Unreserve|Assign Serial|Assign Batch|Item Price|Default Supplier|Item Supplier)\b/i;
const FORBIDDEN_COPY_RE = /\b(Productized|native ERP|governed|deferred|route only|mutation|backend|frontend|framework|Frappe|smoke|test)\b/i;
const NATIVE_ROUTE_RE = /\/desk\/Form\/|\/app\/|#Form\/|query-report|\/desk\/List\//i;
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

function bounded(value, length = 500) {
  const text = String(value || "");
  return text.length > length ? `${text.slice(0, length)}...` : text;
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
    fallbackInjectionUsed: false,
  };
}

function remember(list, item, limit = 40) {
  list.push(item);
  if (list.length > limit) list.shift();
}

function attachPageDiagnostics(page, diagnostics) {
  page.on("console", (message) => {
    if (!["error", "warning"].includes(message.type())) return;
    remember(diagnostics.consoleErrors, {
      type: message.type(),
      text: bounded(message.text(), 700),
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
      url: bounded(request.url(), 700),
      method: request.method(),
      failure: request.failure(),
    });
  });
  page.on("response", (response) => {
    if (response.ok()) return;
    const url = response.url();
    if (!/warehouse|desk_page|getpage|assets\/erp_workspace_ui|api\/method/i.test(url)) return;
    remember(diagnostics.failedResponses, {
      url: bounded(url, 700),
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
    url: bounded(request.url(), 700),
    method: request.method(),
    postData: bounded(request.postData() || "", 500),
    ...extra,
  }, 80);
}

async function diagnosticSnapshot(page, diagnostics, label) {
  const screenshot = await capture(page, `${safeName(label)}-before-timeout`).catch(() => "");
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
      hasWarehouseRenderer: Boolean(window.frappe && frappe.pages && frappe.pages["warehouse-console"] && frappe.pages["warehouse-console"].__erpwWarehouseConsoleRenderer),
      hasWarehouseShell: Boolean(document.querySelector('.sales-console-shell[data-erpw-workspace="warehouse"]')),
      hasWarehouseAssetScript: scripts.some((src) => /warehouse_console_page\.js/.test(src)),
      hasWorkspaceRegistry: Boolean(window.erpWorkspaceUiWorkspaceRegistry),
      hasSidebarRuntime: Boolean(window.erpWorkspaceConsoleSidebar),
      scriptSources: scripts.filter((src) => /erp_workspace_ui|warehouse/i.test(src)).slice(-20),
    };
  }).catch((error) => ({ error: error && error.message ? error.message : String(error) }));
  snapshot.screenshot = screenshot;
  remember(diagnostics.snapshots, { label, ...snapshot }, 20);
  return snapshot;
}

async function injectWarehouseSourceScripts(page, diagnostics) {
  if (!ASSET_ROOT) return;
  diagnostics.fallbackInjectionUsed = true;
  const files = [
    ["workspace-registry", "erp_workspace_ui/public/js/runtime/console/workspace_registry.js"],
    ["workspace-sidebar", "erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js"],
    ["warehouse-page", "erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js"],
  ];
  for (const [key, file] of files) {
    const body = readSource(file);
    remember(diagnostics.overrideHits, {
      key: `manual-inject:${key}`,
      file,
      loaded: Boolean(body),
    }, 80);
    if (body) await page.addScriptTag({ content: body });
  }
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

async function installSourceOverrides(context, diagnostics) {
  if (!ASSET_ROOT) return;
  const assetMappings = [
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

async function waitForWarehouseShell(page, diagnostics, label) {
  try {
    await page.waitForSelector('.sales-console-shell[data-erpw-workspace="warehouse"]', { state: "visible", timeout: TIMEOUT });
  } catch (error) {
    const snapshot = await diagnosticSnapshot(page, diagnostics, `${label}-shell-timeout`);
    error.details = {
      ...(error.details || {}),
      diagnostics,
      snapshot,
    };
    throw error;
  }
}

async function openWarehouse(page, diagnostics, label) {
  const targetPath = "/desk/warehouse-console";
  const startedAt = Date.now();
  const canRoute = await page.evaluate(() => Boolean(window.frappe && typeof frappe.set_route === "function")).catch(() => false);
  if (canRoute) {
    await page.evaluate(() => frappe.set_route("warehouse-console"));
    await page.waitForURL((url) => url.pathname === targetPath || url.pathname === "/app/warehouse-console", { timeout: TIMEOUT });
  } else {
    await page.goto(routeUrl(targetPath), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  }
  await page.waitForFunction(() => Boolean(window.frappe), null, { timeout: TIMEOUT });
  if (ASSET_ROOT) {
    const shellReady = await page.waitForSelector('.sales-console-shell[data-erpw-workspace="warehouse"]', { state: "visible", timeout: 3000 }).then(() => true).catch(() => false);
    if (!shellReady) {
      await diagnosticSnapshot(page, diagnostics, `${label}-pre-inject`);
      await injectWarehouseSourceScripts(page, diagnostics);
    }
  }
  await waitForWarehouseShell(page, diagnostics, label);
  return Date.now() - startedAt;
}

async function measureWarmWarehouseRender(page) {
  const startedAt = Date.now();
  await page.evaluate(() => {
    const shell = document.querySelector('.sales-console-shell[data-erpw-workspace="warehouse"]');
    if (shell) shell.remove();
    const pageDef = window.frappe && frappe.pages && frappe.pages["warehouse-console"];
    const wrapper = document.getElementById("body") || (frappe.container && frappe.container.page && frappe.container.page.wrapper);
    if (pageDef && typeof pageDef.on_page_show === "function") {
      pageDef.on_page_show(wrapper);
    } else if (pageDef && typeof pageDef.on_page_load === "function") {
      pageDef.on_page_load(wrapper);
    }
  });
  await waitForWarehouseReady(page);
  return Date.now() - startedAt;
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
    const globalBodyText = (document.body && document.body.innerText || "").replace(/\s+/g, " ").trim().slice(0, 1200);
    const globalActionText = Array.from(document.querySelectorAll("button, a, [role=button]"))
      .filter(visible)
      .map((node) => (node.innerText || node.getAttribute("aria-label") || node.getAttribute("href") || "").replace(/\s+/g, " ").trim())
      .filter(Boolean)
      .join(" ")
      .slice(0, 1200);
    return {
      url: location.href,
      route: window.frappe && typeof frappe.get_route === "function" ? frappe.get_route() : null,
      text,
      actionText,
      hrefs,
      globalBodyText,
      globalActionText,
      shellCount: Array.from(document.querySelectorAll('.sales-console-shell[data-erpw-workspace="warehouse"]')).filter(visible).length,
      headerCount: Array.from(document.querySelectorAll(".warehouse-console-header")).filter(visible).length,
      sidebarWarehouseEntryCount: Array.from(document.querySelectorAll(".erpw-sales-console-sidebar-link")).filter((node) => visible(node) && /Overview/i.test(node.innerText || "")).length,
      searchUtilityVisible: Array.from(document.querySelectorAll("[data-erpw-sales-search-open]")).some(visible),
      kpiCount: Array.from(document.querySelectorAll(".warehouse-console-kpi-card")).filter(visible).length,
      sectionCount: Array.from(document.querySelectorAll("[data-warehouse-section]")).filter(visible).length,
      horizontalOverflow: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
      bodyWidth: document.documentElement.clientWidth,
      state: shell && shell.getAttribute ? shell.getAttribute("data-warehouse-console-state") || "" : "",
    };
  });
}

function assertAuthorizedSnapshot(state, user) {
  assert(state.shellCount === 1, "Warehouse shell count must remain 1", { user, state });
  assert(state.headerCount === 1, "Warehouse header count must remain 1", { user, state });
  assert(state.kpiCount >= 6, "Warehouse KPI cards did not render", { user, state });
  assert(state.sectionCount >= 5, "Warehouse overview sections did not render", { user, state });
  assert(state.horizontalOverflow <= 2, "Warehouse overview has horizontal overflow", { user, state });
  assert(!state.searchUtilityVisible, "Warehouse search entry must stay inactive in W3", { user, state });
  assert(!FORBIDDEN_ACTION_RE.test(state.actionText), "Forbidden stock action control is visible", { user, state });
  assert(!FORBIDDEN_COPY_RE.test(state.text), "Developer or governance copy is visible", { user, state });
  assert(!VALUATION_RE.test(state.text), "Valuation text is visible", { user, state });
  assert(!NATIVE_ROUTE_RE.test(`${state.hrefs} ${state.actionText}`), "Native route target is visible", { user, state });
}

async function exerciseAuthorizedUser(browser, user) {
  const diagnostics = makeDiagnostics(user.key);
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await installSourceOverrides(context, diagnostics);
  const page = await context.newPage();
  attachPageDiagnostics(page, diagnostics);
  const routeCalls = [];
  page.on("request", (request) => {
    const match = request.url().match(/\/api\/method\/([^?#]+)/);
    if (match && /warehouse_console/.test(match[1])) routeCalls.push(match[1]);
  });
  try {
    await login(page, user);
    const timings = [];
    for (const viewport of VIEWPORTS) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      const firstBootstrapMs = await openWarehouse(page, diagnostics, `${user.key}-${viewport.key}`);
      await waitForWarehouseReady(page);
      assert(!diagnostics.fallbackInjectionUsed, "Warehouse source page required fallback source injection", { user: user.key, viewport, diagnostics });
      const warmSameSessionMs = await measureWarmWarehouseRender(page);
      const state = await snapshot(page);
      assertAuthorizedSnapshot(state, `${user.key}:${viewport.key}`);
      assert(!diagnostics.consoleErrors.some((entry) => entry.type === "error"), "Warehouse source smoke recorded console errors", { user: user.key, viewport, diagnostics });
      assert(diagnostics.pageErrors.length === 0, "Warehouse source smoke recorded page errors", { user: user.key, viewport, diagnostics });
      assert(warmSameSessionMs < Number(process.env.ERPW_WAREHOUSE_W3_WARM_TARGET_MS || 2500), "Warehouse warm route exceeded target", { warmSameSessionMs, firstBootstrapMs, user: user.key, viewport, diagnostics });
      timings.push({ viewport: viewport.key, firstBootstrapMs, warmSameSessionMs });
      await capture(page, `${user.key}-${viewport.key}-overview`);
    }
    const overviewCalls = routeCalls.filter((method) => method.includes("get_warehouse_console_overview"));
    assert(overviewCalls.length <= (VIEWPORTS.length * 2) + 2, "Warehouse overview made too many repeated API calls", { overviewCalls, timings, diagnostics });
    await context.close();
    return { user: user.key, routeCalls, timings, diagnostics };
  } catch (error) {
    error.details = { ...(error.details || {}), diagnostics };
    await context.close().catch(() => {});
    throw error;
  }
}

async function exerciseUnauthorizedUser(browser, user) {
  const diagnostics = makeDiagnostics(user.key);
  const context = await browser.newContext({ viewport: { width: 1240, height: 768 } });
  await installSourceOverrides(context, diagnostics);
  const page = await context.newPage();
  attachPageDiagnostics(page, diagnostics);
  await login(page, user);
  await openWarehouse(page, diagnostics, `${user.key}-restricted`);
  await waitForWarehouseReady(page);
  const state = await snapshot(page);
  await capture(page, `${user.key}-restricted`);
  if (!ASSET_ROOT) {
    assert(state.state === "restricted", "Unauthorized user should receive controlled restricted state", { user, state, diagnostics });
    assert(state.sidebarWarehouseEntryCount === 0, "Unauthorized user should not see Warehouse sidebar entry", { user, state, diagnostics });
  }
  await context.close();
  return { user: user.key, state: state.state || "source-override", diagnostics };
}

(async () => {
  assert(AUTHORIZED_USERS.length > 0, "No Warehouse smoke credentials were provided. Set ERPW_WAREHOUSE_MANAGER_USERNAME/PASSWORD or ERPW_STOCK_USER_USERNAME/PASSWORD.");
  const browser = await chromium.launch({ headless: process.env.ERPW_HEADLESS !== "0" });
  const summary = {
    status: "pass",
    artifactDir: ARTIFACT_DIR,
    sourceOverride: Boolean(ASSET_ROOT),
    authorizedUsers: AUTHORIZED_USERS.map((user) => user.key),
    unauthorizedUsers: UNAUTHORIZED_USERS.map((user) => user.key),
    authorized: [],
    unauthorized: [],
  };
  try {
    for (const user of AUTHORIZED_USERS) {
      summary.authorized.push(await exerciseAuthorizedUser(browser, user));
    }
    if (UNAUTHORIZED_USERS.length) {
      summary.unauthorized.push(await exerciseUnauthorizedUser(browser, UNAUTHORIZED_USERS[0]));
    }
    fs.writeFileSync(path.join(ARTIFACT_DIR, "warehouse-w3-summary.json"), `${JSON.stringify(summary, null, 2)}\n`);
  } catch (error) {
    summary.status = "fail";
    summary.error = error && error.message ? error.message : String(error);
    summary.details = error && error.details ? error.details : {};
    fs.writeFileSync(path.join(ARTIFACT_DIR, "warehouse-w3-summary.json"), `${JSON.stringify(summary, null, 2)}\n`);
    throw error;
  } finally {
    await browser.close();
  }
  console.log(`Warehouse W3 smoke passed. Summary: ${path.join(ARTIFACT_DIR, "warehouse-w3-summary.json")}`);
})().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exit(1);
});
