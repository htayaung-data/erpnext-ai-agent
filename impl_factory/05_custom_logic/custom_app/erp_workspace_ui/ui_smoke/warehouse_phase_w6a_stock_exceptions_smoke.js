const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const TIMEOUT = Number(process.env.ERPW_WAREHOUSE_W6A_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_WAREHOUSE_W6A_ARTIFACT_DIR || path.join(
  fs.existsSync("/freeze-artifacts") ? "/freeze-artifacts" : path.join(__dirname, "artifacts"),
  `warehouse-w6a-stock-exceptions-${new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z")}`
);
const ASSET_ROOT = process.env.ERPW_WAREHOUSE_W6A_ASSET_ROOT || "";

const AUTHORIZED_USERS = [
  {
    key: "warehouse-manager",
    username: process.env.ERPW_WAREHOUSE_MANAGER_USERNAME || process.env.ERPW_STOCK_MANAGER_USERNAME,
    password: process.env.ERPW_WAREHOUSE_MANAGER_PASSWORD || process.env.ERPW_STOCK_MANAGER_PASSWORD,
  },
  {
    key: "warehouse-user",
    username: process.env.ERPW_WAREHOUSE_USER_USERNAME || process.env.ERPW_STOCK_USER_USERNAME || process.env.ERPW_USER_USERNAME,
    password: process.env.ERPW_WAREHOUSE_USER_PASSWORD || process.env.ERPW_STOCK_USER_PASSWORD || process.env.ERPW_USER_PASSWORD,
  },
].filter((user) => user.username && user.password);

const VIEWPORTS = [
  { key: "laptop-1136", width: 1136, height: 768 },
  { key: "laptop-1240", width: 1240, height: 768 },
  { key: "desktop-1440", width: 1440, height: 900 },
];

const FORBIDDEN_ACTION_RE = /\b(Receive|Ship|Dispatch|Post|Submit|Cancel|Amend|Reconcile|Stock Entry|Purchase Receipt|Delivery Note|Stock Reconciliation|Pick List|Reserve|Unreserve|Assign Serial|Assign Batch|Pack|Scan|Allocate|Item Price|Default Supplier|Item Supplier)\b/i;
const FORBIDDEN_COPY_RE = /\b(Productized|native ERP|governed|deferred|route only|mutation|backend|frontend|framework|Frappe|smoke|test|Quick Find)\b/i;
const NATIVE_ROUTE_RE = /\/desk\/Form\/|\/app\/|#Form\/|query-report|\/desk\/List\//i;
const VALUATION_RE = /stock value|valuation rate|stock_value|valuation_rate|base_net_rate|\bamount\b|profit|margin|\bcost\b|\bgl\b|accounting|buying price|selling price|item price/i;

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

function readSource(relativePath) {
  const file = ASSET_ROOT ? path.join(ASSET_ROOT, relativePath) : "";
  return file && fs.existsSync(file) ? fs.readFileSync(file, "utf8") : "";
}

function remember(list, item, limit = 120) {
  list.push(item);
  if (list.length > limit) list.shift();
}

function makeDiagnostics(label) {
  return { label, consoleErrors: [], pageErrors: [], failedResponses: [], failedRequests: [], overrideHits: [], snapshots: [] };
}

function attachDiagnostics(page, diagnostics) {
  page.on("console", (message) => {
    if (["error", "warning"].includes(message.type())) {
      remember(diagnostics.consoleErrors, { type: message.type(), text: message.text().slice(0, 900), location: message.location() });
    }
  });
  page.on("pageerror", (error) => remember(diagnostics.pageErrors, { message: error && error.message ? error.message : String(error) }));
  page.on("requestfailed", (request) => remember(diagnostics.failedRequests, { url: request.url(), method: request.method(), failure: request.failure() }));
  page.on("response", (response) => {
    if (!response.ok() && /warehouse|desk_page|getpage|assets\/erp_workspace_ui|api\/method/i.test(response.url())) {
      remember(diagnostics.failedResponses, { url: response.url(), status: response.status(), statusText: response.statusText() });
    }
  });
}

function requestText(request) {
  try {
    return `${request.url()} ${request.postData() || ""} ${JSON.stringify(request.postDataJSON() || {})}`;
  } catch (error) {
    return `${request.url()} ${request.postData() || ""}`;
  }
}

function recordOverrideHit(diagnostics, key, request, extra = {}) {
  remember(diagnostics.overrideHits, { key, url: request.url(), method: request.method(), ...extra }, 160);
}

function sidebarItems() {
  return [
    { key: "warehouse_console_home", label: "Overview", icon: "item", target: { kind: "page", route: "warehouse-console" } },
    { key: "inbound_receiving", label: "Inbound Receiving", icon: "quotation", target: { kind: "worklist", queue_key: "inbound_receiving" } },
    { key: "outbound_picking", label: "Outbound Picking", icon: "order", target: { kind: "worklist", queue_key: "outbound_picking" } },
    { key: "stock_exceptions", label: "Stock Exceptions", icon: "report", target: { kind: "worklist", queue_key: "stock_exceptions" } },
  ];
}

function workspacePayload() {
  return {
    workspace_id: "warehouse",
    status: "w6a_stock_exceptions_visibility",
    title: "Warehouse Console",
    routes: {
      home: "warehouse-console",
      worklist: "warehouse-console-worklist",
      receiving: "warehouse-console-receiving",
      picking: "warehouse-console-picking",
    },
    methods: {
      overview: "erp_workspace_ui.warehouse_console.service.get_warehouse_console_overview",
      stockExceptions: "erp_workspace_ui.warehouse_console.service.get_warehouse_stock_exceptions",
    },
    search: { enabled: false },
  };
}

function sidebarPayload() {
  const items = sidebarItems();
  return {
    workspace: workspacePayload(),
    context: { has_warehouse_access: true, role_family: "Warehouse", role_variant: "warehouse_manager", can_view_valuation: false },
    state: { kind: "ready", title: "Warehouse Console ready", detail: "Stock visibility and warehouse posture are available for review." },
    sidebar: { workspace_id: "warehouse", title: "Warehouse Console", mode_label: "Warehouse Workspace", scope_label: "Stock workbench", active_key: "warehouse_console_home", home_key: "warehouse_console_home", items, sections: [{ key: "workspace", label: "Workspace", items }] },
    fetched_at: "2026-05-29 00:00:00",
  };
}

function overviewPayload() {
  return {
    workspace: workspacePayload(),
    context: sidebarPayload().context,
    state: { kind: "ready", title: "Warehouse Console ready", detail: "Stock visibility and warehouse posture are available for review." },
    navigation: { items: sidebarItems() },
    sidebar: sidebarPayload().sidebar,
    kpis: [
      { key: "active_warehouses", label: "Active Warehouses", value: 4, note: "Warehouse locations available for stock review.", state: "live" },
      { key: "stocked_items", label: "Stocked Items", value: 8, note: "Item and warehouse positions with stock on hand.", state: "live" },
      { key: "low_stock", label: "Low Stock", value: 1, note: "Projected quantity below zero.", state: "live" },
      { key: "outbound_due", label: "Picking Due", value: 2, note: "Submitted sales orders due for warehouse picking review.", state: "live" },
    ],
    sections: [],
    inbound: { cards: [], preview_rows: [], counts: {} },
    outbound: { cards: [], preview_rows: [], counts: {} },
    stock_exceptions: stockPayload(),
    allowed_actions: [{ key: "refresh", label: "Refresh", kind: "read_only" }],
    action_targets: {},
    fetched_at: "2026-05-29 00:00:00",
  };
}

function stockRows() {
  return [
    {
      key: "SO-REVIEW:ITEM-105:Short - M",
      sales_order: "SO-REVIEW",
      customer: "Review Customer",
      item_code: "ITEM-105",
      item_name: "Power Bank",
      required_date: "2026-06-03",
      pending_qty: "8",
      delivered_qty: "0",
      uom: "Nos",
      source_warehouse: "Short - M",
      available_qty: "2",
      projected_qty: "2",
      short_qty: "6",
      expected_inbound_qty: "10",
      expected_inbound_date: "2026-06-05",
      expected_inbound_order: "PO-SOON",
      exception_key: "inbound_cover_expected",
      exception_label: "Inbound Cover Expected",
      urgency_label: "Due 2026-06-03",
      explanation: "Visible stock is short, with inbound cover expected soon.",
      route_targets: { picking: { route: "warehouse-console-picking", sales_order: "SO-REVIEW" }, receiving: { route: "warehouse-console-receiving", purchase_order: "PO-SOON" } },
    },
    {
      key: "SO-AGING:ITEM-220:Main - M",
      sales_order: "SO-AGING",
      customer: "Aging Customer",
      item_code: "ITEM-220",
      item_name: "Urgent Kit",
      required_date: "2026-05-28",
      pending_qty: "5",
      delivered_qty: "0",
      uom: "Nos",
      source_warehouse: "Main - M",
      available_qty: "1",
      projected_qty: "1",
      short_qty: "4",
      expected_inbound_qty: "0",
      expected_inbound_date: "",
      expected_inbound_order: "",
      exception_key: "urgent_aging",
      exception_label: "Urgent / Aging Demand",
      urgency_label: "Overdue 1d",
      explanation: "Demand is due now or past due and visible stock is short.",
      route_targets: { picking: { route: "warehouse-console-picking", sales_order: "SO-AGING" } },
    },
  ];
}

function stockPayload(filters = {}) {
  const rows = stockRows().filter((row) => {
    if (filters.state && row.exception_key !== filters.state) return false;
    if (filters.warehouse && !row.source_warehouse.toLowerCase().includes(String(filters.warehouse).toLowerCase())) return false;
    if (filters.text && !`${row.sales_order} ${row.customer} ${row.item_code} ${row.item_name}`.toLowerCase().includes(String(filters.text).toLowerCase())) return false;
    return true;
  });
  const groupKeys = [
    ["needs_stock_review", "Needs Stock Review", "Short stock without a near inbound cover."],
    ["inbound_cover_expected", "Inbound Cover Expected", "Short demand with supplier stock expected soon."],
    ["urgent_aging", "Urgent / Aging Demand", "Short demand that is due now or past due."],
    ["warehouse_posture_missing", "Warehouse Posture Missing", "Lines missing warehouse or stock posture."],
  ];
  const groups = groupKeys.map(([key, title, summary]) => ({ key, title, summary, rows: rows.filter((row) => row.exception_key === key) }));
  const counts = Object.fromEntries(groups.map((group) => [group.key, group.rows.length]));
  return {
    workspace: workspacePayload(),
    context: sidebarPayload().context,
    state: rows.length ? { kind: "ready", title: "Warehouse Console ready", detail: "Stock visibility and warehouse posture are available for review." } : { kind: "empty", title: "No stock exceptions need attention", detail: "No stock exceptions need attention." },
    page: { title: "Stock Exceptions", key: "stock_exceptions" },
    summary: { title: "Stock Exceptions", subtitle: "Outbound blockers, inbound cover, and warehouse posture gaps.", chips: [{ label: "Read-only" }, { label: `${rows.length} shown` }] },
    controls: {
      fields: [
        { key: "state", label: "Exception State", type: "select", value: filters.state || "", options: groupKeys.map(([key, title]) => ({ label: title, value: key })).concat([{ label: "All", value: "" }]).reverse() },
        { key: "warehouse", label: "Warehouse", type: "text", value: filters.warehouse || "", placeholder: "Filter warehouse" },
        { key: "text", label: "Order, Item, Customer", type: "text", value: filters.text || "", placeholder: "Filter order, item, or customer" },
      ],
    },
    cards: [
      { key: "total_exceptions", label: "Total Exceptions", title: "Total Exceptions", value: rows.length, state: "live", note: "Rows needing warehouse review." },
      { key: "shortage_risk", label: "Shortage Risk", title: "Shortage Risk", value: (counts.needs_stock_review || 0) + (counts.urgent_aging || 0), state: "live", note: "Demand short of visible stock posture." },
      { key: "inbound_cover_soon", label: "Inbound Cover Soon", title: "Inbound Cover Soon", value: counts.inbound_cover_expected || 0, state: "live", note: "Supplier stock expected within 14 days." },
      { key: "missing_posture", label: "Missing Warehouse Posture", title: "Missing Warehouse Posture", value: counts.warehouse_posture_missing || 0, state: "live", note: "Warehouse or stock posture is incomplete." },
    ],
    groups,
    rows,
    action_targets: { picking: { route: "warehouse-console-picking" }, receiving: { route: "warehouse-console-receiving" } },
    fetched_at: "2026-05-29 00:00:00",
  };
}

function pickingPayload(salesOrder = "SO-REVIEW") {
  return {
    workspace: workspacePayload(),
    context: sidebarPayload().context,
    state: { kind: "ready", title: "Warehouse Console ready", detail: "Stock visibility and warehouse posture are available for review." },
    page: { title: "Picking Review", key: "picking_review", sales_order: salesOrder },
    header: { sales_order: salesOrder, customer: "Review Customer", target_warehouse: "Short - M", age_label: "Due 2026-06-03", remaining_summary: "8 Nos remaining" },
    summary_cards: [
      { key: "state", label: "Picking State", value: "Needs Stock Review", note: "Due 2026-06-03" },
      { key: "delivered", label: "Delivered", value: "0%", note: "Quantity already delivered." },
      { key: "open_lines", label: "Open Lines", value: 1, note: "8 Nos remaining" },
      { key: "readiness", label: "Readiness", value: 0, note: "1 lines need review" },
    ],
    tabs: [{ key: "item_lines", label: "Item Lines", count: 1 }, { key: "stock_readiness", label: "Stock Readiness", count: 1 }],
    lines: [{ item_code: "ITEM-105", item_name: "Power Bank", ordered_qty: "8", delivered_qty: "0", pending_qty: "8", uom: "Nos", source_warehouse: "Short - M", readiness: "Needs Stock Review", availability: "Available 2" }],
  };
}

function receivingPayload(purchaseOrder = "PO-SOON") {
  return {
    workspace: workspacePayload(),
    context: sidebarPayload().context,
    state: { kind: "ready", title: "Warehouse Console ready", detail: "Stock visibility and warehouse posture are available for review." },
    page: { title: "Receiving Review", key: "receiving_review", purchase_order: purchaseOrder },
    header: { purchase_order: purchaseOrder, supplier: "Soon Supply", target_warehouse: "Short - M", age_label: "Due 2026-06-05", remaining_summary: "10 Nos remaining" },
    summary_cards: [
      { key: "state", label: "Receiving State", value: "Expected Soon", note: "Due 2026-06-05" },
      { key: "received", label: "Received", value: "0%", note: "Quantity already received." },
      { key: "open_lines", label: "Open Lines", value: 1, note: "10 Nos remaining" },
      { key: "history", label: "Receipt History", value: 0, note: "Recent receipts visible." },
    ],
    tabs: [{ key: "item_lines", label: "Item Lines", count: 1 }, { key: "receipt_history", label: "Receipt History", count: 0 }],
    lines: [{ item_code: "ITEM-105", item_name: "Power Bank", ordered_qty: "10", received_qty: "0", remaining_qty: "10", uom: "Nos", target_warehouse: "Short - M", status: "Open" }],
    receipt_history: [],
  };
}

async function installSourceOverrides(context, diagnostics) {
  if (!ASSET_ROOT) return;
  const mappings = [
    ["workspace-registry", /\/assets\/erp_workspace_ui\/js\/runtime\/console\/workspace_registry\.js(?:\?|$)/, "erp_workspace_ui/public/js/runtime/console/workspace_registry.js"],
    ["workspace-sidebar", /\/assets\/erp_workspace_ui\/js\/runtime\/console\/workspace_console_sidebar\.js(?:\?|$)/, "erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js"],
    ["warehouse-page-asset", /\/assets\/erp_workspace_ui\/js\/warehouse_console\/warehouse_console_page\.js(?:\?|$)/, "erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js"],
  ];
  for (const [key, pattern, file] of mappings) {
    await context.route((url) => pattern.test(url.pathname + url.search), async (route) => {
      const body = readSource(file);
      recordOverrideHit(diagnostics, key, route.request(), { fulfilled: Boolean(body) });
      if (body) return route.fulfill({ status: 200, body, contentType: "application/javascript" });
      return route.continue();
    });
  }
  await context.route("**/api/method/frappe.desk.desk_page.getpage**", async (route) => {
    const request = route.request();
    const text = requestText(request);
    if (!/warehouse-console/i.test(text)) return route.continue();
    const isReceiving = /warehouse-console-receiving/i.test(text);
    const isPicking = /warehouse-console-picking/i.test(text);
    const isWorklist = /warehouse-console-worklist/i.test(text);
    const file = isReceiving
      ? "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_receiving/warehouse_console_receiving.js"
      : isPicking
        ? "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_picking/warehouse_console_picking.js"
        : isWorklist
          ? "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/warehouse_console_worklist.js"
          : "erp_workspace_ui/erp_workspace_ui/page/warehouse_console/warehouse_console.js";
    const name = isReceiving ? "warehouse-console-receiving" : isPicking ? "warehouse-console-picking" : isWorklist ? "warehouse-console-worklist" : "warehouse-console";
    const script = readSource(file);
    recordOverrideHit(diagnostics, "desk-page-getpage", request, { fulfilled: Boolean(script), page: name });
    const pageDoc = { doctype: "Page", name, page_name: name, title: "Warehouse Console", module: "ERP Workspace UI", standard: "Yes", content: "", script };
    return route.fulfill({ status: script ? 200 : 404, contentType: "application/json", body: JSON.stringify({ docs: [pageDoc], message: pageDoc }) });
  });
  const methodPayloads = [
    ["get_warehouse_console_overview", "warehouse-overview", () => overviewPayload()],
    ["get_warehouse_console_sidebar_context", "warehouse-sidebar", () => sidebarPayload()],
    ["get_warehouse_picking_review", "warehouse-picking-detail", (body) => pickingPayload(body.sales_order)],
    ["get_warehouse_receiving_review", "warehouse-receiving-detail", (body) => receivingPayload(body.purchase_order)],
    ["get_warehouse_stock_exceptions", "warehouse-stock-exceptions", (body) => {
      const raw = body.filters;
      const filters = typeof raw === "string" ? JSON.parse(raw || "{}") : (raw || {});
      return stockPayload(filters);
    }],
  ];
  for (const [method, key, payload] of methodPayloads) {
    await context.route(`**/api/method/erp_workspace_ui.warehouse_console.service.${method}**`, async (route) => {
      let body = {};
      try {
        body = route.request().postDataJSON() || {};
      } catch (error) {
        body = {};
      }
      recordOverrideHit(diagnostics, key, route.request(), { fulfilled: true });
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ message: payload(body) }) });
    });
  }
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

async function waitForOverrideHit(diagnostics, key) {
  const started = Date.now();
  while (Date.now() - started < TIMEOUT) {
    if (diagnostics.overrideHits.some((hit) => hit.key === key)) return;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`Expected source override was not used: ${key}`);
}

async function waitForStock(page) {
  await page.waitForFunction(() => {
    const shell = document.querySelector('[data-warehouse-stock-exception-shell="true"][data-warehouse-view="stock-exceptions"]');
    return Boolean(shell
      && shell.getAttribute("data-erpw-console-runtime") === "ready"
      && shell.querySelectorAll("[data-warehouse-stock-exception-card]").length >= 4
      && shell.querySelectorAll("[data-warehouse-stock-exception-group]").length >= 4
      && (shell.querySelectorAll("[data-warehouse-stock-exception-row]").length >= 1 || shell.querySelector("[data-warehouse-stock-exception-empty]")));
  }, null, { timeout: TIMEOUT });
}

async function waitForOverview(page) {
  await page.waitForFunction(() => Boolean(document.querySelector('.sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-console-kpi-card')), null, { timeout: TIMEOUT });
}

async function waitForPicking(page) {
  await page.waitForFunction(() => Boolean(document.querySelector('.warehouse-picking-shell[data-warehouse-view="picking-review"] [data-warehouse-picking-line]')), null, { timeout: TIMEOUT });
}

async function waitForReceiving(page) {
  await page.waitForFunction(() => Boolean(document.querySelector('.warehouse-receiving-shell[data-warehouse-view="receiving-review"] [data-warehouse-receiving-line]')), null, { timeout: TIMEOUT });
}

async function openRoute(page, parts, pathName, wait) {
  const canRoute = await page.evaluate(() => Boolean(window.frappe && typeof frappe.set_route === "function")).catch(() => false);
  if (canRoute) {
    await page.evaluate((routeParts) => frappe.set_route(...routeParts), parts);
    await page.waitForURL((url) => url.pathname === pathName || url.pathname === `/app/${parts.join("/")}`, { timeout: TIMEOUT });
  } else {
    await page.goto(routeUrl(pathName), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  }
  await wait(page);
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
    const text = ((shell && shell.innerText) || "").replace(/\s+/g, " ").trim();
    const actionText = Array.from((shell || document).querySelectorAll("button, a, [role=button]")).filter(visible).map((node) => (node.innerText || node.getAttribute("aria-label") || node.getAttribute("href") || "").replace(/\s+/g, " ").trim()).filter(Boolean).join(" ");
    const hrefs = Array.from((shell || document).querySelectorAll("a[href]")).map((node) => node.getAttribute("href") || "").join(" ");
    return {
      url: location.href,
      route: window.frappe && typeof frappe.get_route === "function" ? frappe.get_route() : null,
      text,
      actionText,
      hrefs,
      shellCount: Array.from(document.querySelectorAll('.sales-console-shell[data-erpw-workspace="warehouse"]')).filter(visible).length,
      headerCount: Array.from(document.querySelectorAll(".warehouse-console-header, .warehouse-inbound-queue-header, .warehouse-receiving-header")).filter(visible).length,
      sidebarCount: Array.from(document.querySelectorAll(".erpw-sales-console-sidebar")).filter(visible).length,
      sidebarText: Array.from(document.querySelectorAll(".erpw-sales-console-sidebar")).map((node) => node.innerText || "").join(" "),
      stockShellCount: Array.from(document.querySelectorAll('[data-warehouse-stock-exception-shell="true"][data-warehouse-view="stock-exceptions"]')).filter(visible).length,
      stockCardCount: Array.from(document.querySelectorAll("[data-warehouse-stock-exception-card]")).filter(visible).length,
      stockGroupCount: Array.from(document.querySelectorAll("[data-warehouse-stock-exception-group]")).filter(visible).length,
      stockRowCount: Array.from(document.querySelectorAll("[data-warehouse-stock-exception-row]")).filter(visible).length,
      stockFilterCount: Array.from(document.querySelectorAll("[data-warehouse-filter-key]")).filter(visible).length,
      pickingRouteButtonCount: Array.from(document.querySelectorAll("[data-warehouse-stock-exception-route-picking]")).filter(visible).length,
      receivingRouteButtonCount: Array.from(document.querySelectorAll("[data-warehouse-stock-exception-route-receiving]")).filter(visible).length,
      searchUtilityVisible: Array.from(document.querySelectorAll("[data-erpw-sales-search-open]")).some(visible),
      horizontalOverflow: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
      diagnostics: window.erpWorkspaceWarehouseConsole && window.erpWorkspaceWarehouseConsole.diagnostics ? { ...window.erpWorkspaceWarehouseConsole.diagnostics } : {},
      hasExportedStockRenderer: Boolean(window.erpWorkspaceWarehouseConsole && typeof window.erpWorkspaceWarehouseConsole.renderStockExceptions === "function"),
    };
  });
}

function assertClean(state, context) {
  assert(state.shellCount === 1, "Warehouse shell count must remain 1", { context, state });
  assert(state.headerCount === 1, "Warehouse header count must remain 1", { context, state });
  assert(state.sidebarCount <= 1, "Warehouse sidebar count must not duplicate", { context, state });
  assert(state.horizontalOverflow <= 2, "Warehouse page has horizontal overflow", { context, state });
  assert(!state.searchUtilityVisible, "Warehouse search entry must stay inactive in W6A", { context, state });
  assert(!FORBIDDEN_ACTION_RE.test(state.actionText), "Forbidden stock action control is visible", { context, state });
  assert(!FORBIDDEN_COPY_RE.test(state.text), "Developer or governance copy is visible", { context, state });
  assert(!VALUATION_RE.test(state.text), "Valuation, accounting, or commercial text is visible", { context, state });
  assert(!NATIVE_ROUTE_RE.test(`${state.hrefs} ${state.actionText}`), "Native route target is visible", { context, state });
}

async function exerciseUser(browser, user) {
  const diagnostics = makeDiagnostics(user.key);
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await installSourceOverrides(context, diagnostics);
  const page = await context.newPage();
  attachDiagnostics(page, diagnostics);
  try {
    await login(page, user);
    await openRoute(page, ["warehouse-console"], "/desk/warehouse-console", waitForOverview);
    let state = await snapshot(page);
    assertClean(state, `${user.key}:overview`);
    assert(/Stock Exceptions/.test(`${state.text} ${state.actionText} ${state.sidebarText}`), "Stock Exceptions navigation was not visible", { user: user.key, state });
    assert(/Open stock exceptions/i.test(state.actionText), "Open stock exceptions action was not visible", { user: user.key, state });

    await openRoute(page, ["warehouse-console-worklist", "stock-exceptions"], "/desk/warehouse-console-worklist/stock-exceptions", waitForStock);
    if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-stock-exceptions");
    state = await snapshot(page);
    assertClean(state, `${user.key}:stock`);
    assert(state.stockShellCount === 1, "Stock Exceptions shell count must be 1", { user: user.key, state });
    assert(state.stockCardCount >= 4, "Stock exception summary cards did not render", { user: user.key, state });
    assert(state.stockGroupCount >= 4, "Stock exception groups did not render", { user: user.key, state });
    assert(state.stockRowCount >= 1, "Stock exception rows did not render", { user: user.key, state });
    assert(state.stockFilterCount >= 3, "Stock exception filters did not render", { user: user.key, state });
    assert(state.pickingRouteButtonCount >= 1, "Stock exception picking route button did not render", { user: user.key, state });
    assert(state.receivingRouteButtonCount >= 1, "Stock exception receiving route button did not render", { user: user.key, state });
    await capture(page, `${user.key}-stock-exceptions`);

    await page.locator('[data-warehouse-filter-key="state"]').selectOption("inbound_cover_expected");
    await page.locator("[data-warehouse-filter-apply]").click();
    await waitForStock(page);
    assertClean(await snapshot(page), `${user.key}:apply`);

    await page.locator("[data-warehouse-filter-reset]").click();
    await waitForStock(page);
    assertClean(await snapshot(page), `${user.key}:reset`);

    await page.locator("[data-warehouse-filter-refresh]").click();
    await waitForStock(page);
    assertClean(await snapshot(page), `${user.key}:refresh`);

    await page.locator("[data-warehouse-stock-exception-route-picking]").first().click();
    await page.waitForURL((url) => /\/(?:desk|app)\/warehouse-console-picking\//.test(url.pathname), { timeout: TIMEOUT });
    await waitForPicking(page);
    state = await snapshot(page);
    assertClean(state, `${user.key}:picking`);
    assert(/warehouse-console-picking/.test(state.url), "Picking link did not stay inside Warehouse route", { user: user.key, state });

    await page.goBack({ waitUntil: "domcontentloaded", timeout: TIMEOUT });
    await waitForStock(page);

    await page.locator("[data-warehouse-stock-exception-route-receiving]").first().click();
    await page.waitForURL((url) => /\/(?:desk|app)\/warehouse-console-receiving\//.test(url.pathname), { timeout: TIMEOUT });
    await waitForReceiving(page);
    state = await snapshot(page);
    assertClean(state, `${user.key}:receiving`);
    assert(/warehouse-console-receiving/.test(state.url), "Receiving link did not stay inside Warehouse route", { user: user.key, state });

    await page.goBack({ waitUntil: "domcontentloaded", timeout: TIMEOUT });
    await waitForStock(page);
    await page.reload({ waitUntil: "domcontentloaded", timeout: TIMEOUT });
    await waitForStock(page);
    assertClean(await snapshot(page), `${user.key}:reload`);

    await openRoute(page, ["warehouse-console-worklist", "stock-exceptions"], "/desk/warehouse-console-worklist/stock-exceptions", waitForStock);
    await openRoute(page, ["warehouse-console-worklist", "stock-exceptions"], "/desk/warehouse-console-worklist/stock-exceptions", waitForStock);
    assertClean(await snapshot(page), `${user.key}:repeat`);

    for (const viewport of VIEWPORTS) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await openRoute(page, ["warehouse-console-worklist", "stock-exceptions"], "/desk/warehouse-console-worklist/stock-exceptions", waitForStock);
      state = await snapshot(page);
      assertClean(state, `${user.key}:${viewport.key}`);
      assert(state.stockShellCount === 1, "Stock Exceptions shell count must remain 1", { user: user.key, viewport, state });
      await capture(page, `${user.key}-${viewport.key}-stock-exceptions`);
    }

    state = await snapshot(page);
    assert(state.hasExportedStockRenderer, "Warehouse exported stock exception renderer is missing", { user: user.key, state, diagnostics });
    assert((state.diagnostics || {}).renderStockExceptionsEntered >= 1, "Warehouse stock exceptions renderer was not entered", { user: user.key, state, diagnostics });
    assert((state.diagnostics || {}).stockExceptionsServiceCallAttempted >= 1, "Warehouse stock exceptions service call was not attempted", { user: user.key, state, diagnostics });
    if (ASSET_ROOT) {
      assert(diagnostics.overrideHits.some((hit) => hit.key === "desk-page-getpage" && hit.page === "warehouse-console-worklist"), "Warehouse worklist getpage source override was not used", { user: user.key, diagnostics });
      assert(diagnostics.overrideHits.some((hit) => hit.key === "warehouse-page-asset"), "Warehouse page asset source override was not used", { user: user.key, diagnostics });
      assert(diagnostics.overrideHits.some((hit) => hit.key === "warehouse-stock-exceptions"), "Warehouse stock exceptions source override was not used", { user: user.key, diagnostics });
    }
    assert(!diagnostics.consoleErrors.some((entry) => entry.type === "error"), "Warehouse W6A smoke recorded console errors", { user: user.key, diagnostics });
    assert(diagnostics.pageErrors.length === 0, "Warehouse W6A smoke recorded page errors", { user: user.key, diagnostics });
    assert(diagnostics.failedResponses.length === 0, "Warehouse W6A smoke recorded failed responses", { user: user.key, diagnostics });
    await context.close();
    return { user: user.key, diagnostics };
  } catch (error) {
    await capture(page, `${user.key}-failure`).catch(() => "");
    error.details = { ...(error.details || {}), diagnostics };
    await context.close().catch(() => {});
    throw error;
  }
}

(async () => {
  assert(AUTHORIZED_USERS.length > 0, "No Warehouse W6A smoke credentials were provided. Set ERPW_WAREHOUSE_MANAGER_USERNAME/PASSWORD or ERPW_WAREHOUSE_USER_USERNAME/PASSWORD.");
  const browser = await chromium.launch({ headless: process.env.ERPW_HEADLESS !== "0" });
  const summary = { status: "pass", artifactDir: ARTIFACT_DIR, sourceOverride: Boolean(ASSET_ROOT), authorizedUsers: AUTHORIZED_USERS.map((user) => user.key), authorized: [] };
  try {
    for (const user of AUTHORIZED_USERS) {
      summary.authorized.push(await exerciseUser(browser, user));
    }
    fs.writeFileSync(path.join(ARTIFACT_DIR, "warehouse-w6a-stock-exceptions-summary.json"), `${JSON.stringify(summary, null, 2)}\n`);
  } catch (error) {
    summary.status = "fail";
    summary.error = error && error.message ? error.message : String(error);
    summary.details = error && error.details ? error.details : {};
    fs.writeFileSync(path.join(ARTIFACT_DIR, "warehouse-w6a-stock-exceptions-summary.json"), `${JSON.stringify(summary, null, 2)}\n`);
    throw error;
  } finally {
    await browser.close();
  }
  console.log(`Warehouse W6A stock exceptions smoke passed. Summary: ${path.join(ARTIFACT_DIR, "warehouse-w6a-stock-exceptions-summary.json")}`);
})().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exit(1);
});
