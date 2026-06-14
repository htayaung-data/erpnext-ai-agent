const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const EXPECT_W12J = process.env.ERPW_WAREHOUSE_W8C_EXPECT_W12J === "1" || Boolean(process.env.ERPW_WAREHOUSE_W12J_ASSET_ROOT || process.env.ERPW_WAREHOUSE_W12J_ARTIFACT_DIR);
const TIMEOUT = Number((EXPECT_W12J && process.env.ERPW_WAREHOUSE_W12J_TIMEOUT) || process.env.ERPW_WAREHOUSE_W8C_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_WAREHOUSE_W8C_ARTIFACT_DIR || (EXPECT_W12J ? process.env.ERPW_WAREHOUSE_W12J_ARTIFACT_DIR : "") || path.join(
  fs.existsSync("/freeze-artifacts") ? "/freeze-artifacts" : path.join(__dirname, "artifacts"),
  `${EXPECT_W12J ? "warehouse-w12j-transfer-visibility-polish" : "warehouse-w8c-transfer-visibility"}-${new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z")}`
);
const ASSET_ROOT = process.env.ERPW_WAREHOUSE_W8C_ASSET_ROOT || (EXPECT_W12J ? process.env.ERPW_WAREHOUSE_W12J_ASSET_ROOT : "") || "";
const SUMMARY_FILE = process.env.ERPW_WAREHOUSE_W8C_SUMMARY_NAME || (EXPECT_W12J ? "warehouse-w12j-transfer-visibility-polish-summary.json" : "warehouse-w8c-transfer-visibility-summary.json");
const PHASE_LABEL = process.env.ERPW_WAREHOUSE_W8C_PHASE_LABEL || (EXPECT_W12J ? "Warehouse W12J transfer visibility polish" : "Warehouse W8C transfer visibility");
const MOVEMENT_TOKEN = Buffer.from(JSON.stringify({ movement_id: "MAT-MOV-0001", return_route: { route: "warehouse-console-worklist", queue_key: "transfer_visibility" } })).toString("hex");
const STOCK_POSTURE_TOKEN = Buffer.from(JSON.stringify({
  item_code: "ITEM-103",
  purchase_order: "",
  sales_order: "",
  stock_exception_token: "",
  warehouse: "Main - M",
})).toString("hex");
const RESPONSIVE_VIEWPORTS = [
  { key: "desktop-1440", width: 1440, height: 900 },
  { key: "laptop-1240", width: 1240, height: 768 },
  { key: "laptop-1136", width: 1136, height: 768 },
  { key: "mobile-390", width: 390, height: 844 },
];

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

const FORBIDDEN_ACTION_RE = /\b(Create Transfer|Issue Transfer|Receive Transfer|Complete Transfer|Execute Transfer|Create Stock Entry|Stock Entry|Purchase Receipt|Delivery Note|Stock Reconciliation|Pick List|Submit|Cancel|Amend|Reconcile|Reserve|Unreserve|Assign Serial|Assign Batch|Pack|Scan|Allocate|Update Stock|Adjust Stock)\b/i;
const FORBIDDEN_COPY_RE = /\b(Productized|native ERP|governed|deferred|route only|mutation|backend|frontend|framework|Frappe|smoke|test|Quick Find|\bSearch\b)\b/i;
const NATIVE_ROUTE_RE = /\/desk\/Form\/|\/app\/|#Form\/|query-report|\/desk\/List\//i;
const VALUATION_RE = /stock value|valuation rate|stock_value|valuation_rate|incoming_rate|outgoing_rate|basic_rate|\brate\b|\bamount\b|base_amount|transfer_price|profit|margin|\bcost\b|\bgl\b|accounting|billing|payment|tax|item price|stock_queue/i;

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

function remember(list, item, limit = 160) {
  list.push(item);
  if (list.length > limit) list.shift();
}

function makeDiagnostics(label) {
  return { label, consoleErrors: [], pageErrors: [], failedResponses: [], failedRequests: [], overrideHits: [], snapshots: [] };
}

function attachDiagnostics(page, diagnostics) {
  page.on("console", (message) => {
    if (["error", "warning"].includes(message.type())) remember(diagnostics.consoleErrors, { type: message.type(), text: message.text().slice(0, 900), location: message.location() });
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
  remember(diagnostics.overrideHits, { key, url: request.url(), method: request.method(), ...extra }, 180);
}

function overrideHitCount(diagnostics, key) {
  return diagnostics.overrideHits.filter((hit) => hit.key === key).length;
}

function sidebarItems() {
  return [
    { key: "warehouse_console_home", label: "Overview", icon: "item", target: { kind: "page", route: "warehouse-console" } },
    { key: "inbound_receiving", label: "Inbound Receiving", icon: "quotation", target: { kind: "worklist", queue_key: "inbound_receiving" } },
    { key: "outbound_picking", label: "Outbound Picking", icon: "order", target: { kind: "worklist", queue_key: "outbound_picking" } },
    { key: "stock_exceptions", label: "Stock Exceptions", icon: "report", target: { kind: "worklist", queue_key: "stock_exceptions" } },
    { key: "movement_visibility", label: "Movement Visibility", icon: "stock", target: { kind: "worklist", queue_key: "movement_visibility" } },
    { key: "transfer_visibility", label: "Transfer Visibility", icon: "stock", target: { kind: "worklist", queue_key: "transfer_visibility" } },
  ];
}

function workspacePayload() {
  return {
    workspace_id: "warehouse",
    status: "w8c_transfer_visibility",
    title: "Warehouse Console",
    routes: {
      home: "warehouse-console",
      worklist: "warehouse-console-worklist",
      receiving: "warehouse-console-receiving",
      picking: "warehouse-console-picking",
      stockException: "warehouse-console-stock-exception",
      stockPosture: "warehouse-console-stock-posture",
      movement: "warehouse-console-movement",
    },
    methods: {
      overview: "erp_workspace_ui.warehouse_console.service.get_warehouse_console_overview",
      transferVisibility: "erp_workspace_ui.warehouse_console.service.get_warehouse_transfer_visibility_queue",
      movementReview: "erp_workspace_ui.warehouse_console.service.get_warehouse_movement_review",
      stockPostureReview: "erp_workspace_ui.warehouse_console.service.get_warehouse_stock_posture_review",
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
      { key: "outbound_due", label: "Picking Due", value: 2, note: "Submitted sales orders due for warehouse picking review.", state: "live" },
      { key: "transfer_requests", label: "Movement Watch", value: 2, note: "Recorded transfer posture available.", state: "live" },
    ],
    sections: [],
    inbound: { cards: [], preview_rows: [], counts: {} },
    outbound: { cards: [], preview_rows: [], counts: {} },
    stock_exceptions: { cards: [], preview_rows: [], counts: {} },
    allowed_actions: [{ key: "refresh", label: "Refresh", kind: "read_only" }],
    action_targets: {},
    fetched_at: "2026-05-29 00:00:00",
  };
}

function transferRows() {
  return [
    {
      key: "MAT-MOV-0001",
      transfer_id: "MAT-MOV-0001",
      movement_id: "MAT-MOV-0001",
      movement_type: "Material Transfer",
      purpose: "Material Transfer",
      posting_date: "2026-05-29",
      posting_time: "09:15:00",
      source_warehouse: "Stores - M",
      target_warehouse: "Main - M",
      direction_label: "Stores - M to Main - M",
      posture_key: "direct_transfers",
      posture: "Direct Transfer",
      item_count: 2,
      quantity_summary: "7 Nos",
      group_key: "direct_transfers",
      group_label: "Direct Transfer",
      route_targets: { movement_review: { route: "warehouse-console-movement", context_token: MOVEMENT_TOKEN }, stock_posture: { route: "warehouse-console-stock-posture", context_token: STOCK_POSTURE_TOKEN } },
      sample_items: [
        { item_code: "ITEM-103", item_name: "Bluetooth Speaker", qty: "5", uom: "Nos", source_warehouse: "Stores - M", target_warehouse: "Main - M", route_target: { route: "warehouse-console-stock-posture", context_token: STOCK_POSTURE_TOKEN } },
        { item_code: "ITEM-104", item_name: "Cable Pack", qty: "2", uom: "Nos", source_warehouse: "Stores - M", target_warehouse: "Main - M", route_target: { route: "warehouse-console-stock-posture", context_token: STOCK_POSTURE_TOKEN } },
      ],
    },
    {
      key: "MAT-MOV-TRANSIT",
      transfer_id: "MAT-MOV-TRANSIT",
      movement_id: "MAT-MOV-TRANSIT",
      movement_type: "Material Transfer",
      purpose: "Material Transfer",
      posting_date: "2026-05-28",
      posting_time: "10:20:00",
      source_warehouse: "Transit - M",
      target_warehouse: "Main - M",
      direction_label: "Transit - M to Main - M",
      posture_key: "transit_related",
      posture: "Transit Related",
      item_count: 1,
      quantity_summary: "10 Nos",
      group_key: "transit_related",
      group_label: "Transit Related",
      route_targets: { movement_review: { route: "warehouse-console-movement", context_token: MOVEMENT_TOKEN }, stock_posture: { route: "warehouse-console-stock-posture", context_token: STOCK_POSTURE_TOKEN } },
      sample_items: [
        { item_code: "ITEM-105", item_name: "Power Bank", qty: "10", uom: "Nos", source_warehouse: "Transit - M", target_warehouse: "Main - M", route_target: { route: "warehouse-console-stock-posture", context_token: STOCK_POSTURE_TOKEN } },
      ],
    },
  ];
}

function transferPayload() {
  const rows = transferRows();
  return {
    workspace: workspacePayload(),
    context: sidebarPayload().context,
    state: { kind: "ready", title: "Warehouse Console ready", detail: "Transfer visibility is available for review." },
    page: { title: "Transfer Visibility", key: "transfer_visibility" },
    summary: { title: "Transfer Visibility", subtitle: "Read-only warehouse-to-warehouse transfer posture.", chips: [{ label: "Read-only" }, { label: "Submitted movement records" }, { label: `${rows.length} shown` }] },
    controls: {
      fields: [
        { key: "transfer_state", label: "Transfer Posture", type: "select", value: "", options: [{ label: "All", value: "" }, { label: "Direct Transfers", value: "direct_transfers" }, { label: "Transit Related", value: "transit_related" }, { label: "Needs Review", value: "needs_review" }] },
        { key: "date_window", label: "Date Window", type: "select", value: "last_14_days", options: [{ label: "Today", value: "today" }, { label: "Last 7 Days", value: "last_7_days" }, { label: "Last 14 Days", value: "last_14_days" }] },
        { key: "source_warehouse", label: "Source Warehouse", type: "text", value: "", placeholder: "Filter source warehouse" },
        { key: "target_warehouse", label: "Target Warehouse", type: "text", value: "", placeholder: "Filter target warehouse" },
        { key: "item", label: "Item", type: "text", value: "", placeholder: "Filter item" },
      ],
    },
    cards: [
      { key: "needs_review", label: "Needs Review", title: "Needs Review", value: 0, state: "live", note: "Missing or mixed warehouse posture." },
      { key: "direct_transfers", label: "Direct Transfers", title: "Direct Transfers", value: 1, state: "live", note: "Clear source and target warehouse posture." },
      { key: "transit_related", label: "Transit Related", title: "Transit Related", value: 1, state: "live", note: "Transit warehouse posture visible." },
      { key: "transfer_quantity", label: "Transfer Quantity", title: "Transfer Quantity", value: "17 Nos", state: "live", note: "Operational quantity summary." },
    ],
    groups: [
      { key: "direct_transfers", title: "Direct Transfers", summary: "Posted warehouse-to-warehouse transfers with clear direction.", rows: [rows[0]] },
      { key: "transit_related", title: "Transit Related", summary: "Transfers involving a transit warehouse posture.", rows: [rows[1]] },
      { key: "needs_review", title: "Needs Review", summary: "Transfers with incomplete or mixed warehouse posture.", rows: [] },
      { key: "recently_posted", title: "Recently Posted", summary: "Submitted transfer records visible in the current window.", rows: [] },
    ],
    rows,
    action_targets: { movement_review: { route: "warehouse-console-movement" }, stock_posture: { route: "warehouse-console-stock-posture" } },
    fetched_at: "2026-05-30 00:00:00",
  };
}

function stockPosturePayload(contextToken = STOCK_POSTURE_TOKEN) {
  return {
    workspace: workspacePayload(),
    context: sidebarPayload().context,
    state: { kind: "ready", title: "Warehouse Console ready", detail: "Stock posture is available for review." },
    page: { title: "Stock Posture Review", key: "stock_posture_review", context_token: contextToken },
    header: { title: "Stock Posture Review", subtitle: "Item and warehouse posture.", context_token: contextToken, item_code: "ITEM-103", item_name: "Bluetooth Speaker", warehouse: "Main - M", posture_label: "Available", explanation: "Visible stock covers current transfer posture.", fetched_at: "2026-05-29 00:00:00" },
    quantity_posture: { actual_qty: "12", available_qty: "12", projected_qty: "12", reserved_qty: "0" },
    summary_cards: [
      { key: "posture", label: "Posture", value: "Available", note: "Main - M" },
      { key: "available", label: "Available", value: "12", note: "Operational stock" },
      { key: "projected", label: "Projected", value: "12", note: "Projected posture" },
      { key: "open_demand", label: "Open Demand", value: "0", note: "No open demand in this fixture" },
      { key: "inbound_cover", label: "Inbound Cover", value: "0", note: "No inbound cover in this fixture" },
    ],
    panels: {
      stock: { title: "Stock Posture", summary: "Current visible stock for this warehouse.", items: [{ label: "Item", value: "ITEM-103 Bluetooth Speaker" }, { label: "Warehouse", value: "Main - M" }, { label: "Available", value: "12" }] },
      inbound: { title: "Inbound Cover", summary: "No inbound cover visible.", items: [] },
      outbound: { title: "Open Demand", summary: "No open outbound demand visible.", items: [] },
      related: { title: "Related Reviews", summary: "Return to Warehouse transfer visibility.", items: [] },
    },
    outbound_rows: [],
    inbound_rows: [],
    related_rows: [{ key: "movement", title: "Transfer Visibility", label: "Warehouse Movement", detail: "Return to the transfer board.", route_target: { route: "warehouse-console-worklist", queue_key: "transfer_visibility" } }],
    allowed_actions: [{ key: "refresh", label: "Refresh", kind: "read_only" }, { key: "back", label: "Back", kind: "navigation" }],
    action_targets: { back: { route: "warehouse-console-worklist", queue_key: "transfer_visibility" } },
    fetched_at: "2026-05-29 00:00:00",
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
    const isStockPosture = /warehouse-console-stock-posture/i.test(text);
    const isMovementReview = /warehouse-console-movement/i.test(text);
    const isWorklist = /warehouse-console-worklist/i.test(text);
    const file = isStockPosture
      ? "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_stock_posture/warehouse_console_stock_posture.js"
      : isMovementReview
        ? "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_movement/warehouse_console_movement.js"
        : isWorklist
        ? "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/warehouse_console_worklist.js"
        : "erp_workspace_ui/erp_workspace_ui/page/warehouse_console/warehouse_console.js";
    const name = isStockPosture ? "warehouse-console-stock-posture" : isMovementReview ? "warehouse-console-movement" : isWorklist ? "warehouse-console-worklist" : "warehouse-console";
    const script = readSource(file);
    recordOverrideHit(diagnostics, "desk-page-getpage", request, { fulfilled: Boolean(script), page: name });
    const pageDoc = { doctype: "Page", name, page_name: name, title: "Warehouse Console", module: "ERP Workspace UI", standard: "Yes", content: "", script };
    return route.fulfill({ status: script ? 200 : 404, contentType: "application/json", body: JSON.stringify({ docs: [pageDoc], message: pageDoc }) });
  });
  const methodPayloads = [
    ["get_warehouse_console_overview", "warehouse-overview", () => overviewPayload()],
    ["get_warehouse_console_sidebar_context", "warehouse-sidebar", () => sidebarPayload()],
    ["get_warehouse_transfer_visibility_queue", "warehouse-transfer-visibility", () => transferPayload()],
    ["get_warehouse_stock_posture_review", "warehouse-stock-posture-review", (body) => stockPosturePayload(body.context_token)],
    ["get_warehouse_movement_review", "warehouse-movement-review", () => ({ state: { kind: "ready", title: "Warehouse Console ready", detail: "Movement review available." }, page: { title: "Movement Review", key: "movement_review", context_token: MOVEMENT_TOKEN }, header: { title: "Movement Review", subtitle: "Posted transfer movement posture.", context_token: MOVEMENT_TOKEN, movement_id: "MAT-MOV-0001", purpose: "Material Transfer", movement_type: "Material Transfer", posting_date: "2026-05-29", posting_time: "09:15:00", source_warehouse: "Stores - M", target_warehouse: "Main - M", direction_label: "Stores - M to Main - M", docstatus_label: "Posted", freshness: "2026-05-30 00:00:00" }, summary_cards: [], panels: { direction: { title: "Movement Direction", items: [] }, related: { title: "Related Reviews", items: [] } }, line_groups: [], related_routes: [], action_targets: { back: { route: "warehouse-console-worklist", queue_key: "transfer_visibility" } }, fetched_at: "2026-05-30 00:00:00" })],
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
  await page.fill('input[name="usr"], input#login_email', user.username);
  await page.fill('input[name="pwd"], input#login_password', user.password);
  await Promise.all([
    page.waitForURL(/\/(?:app|desk)(?:[/?#]|$)/, { waitUntil: "domcontentloaded", timeout: TIMEOUT }).catch(() => {}),
    page.click('button[type="submit"], .btn-login'),
  ]);
}

async function waitForOverrideHit(diagnostics, key) {
  const deadline = Date.now() + TIMEOUT;
  while (Date.now() < deadline) {
    if (diagnostics.overrideHits.some((hit) => hit.key === key)) return;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`Expected source override was not used: ${key}`);
}

async function waitForOverview(page) {
  await page.waitForFunction(() => Boolean(document.querySelector('.sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-console-kpi-card')), null, { timeout: TIMEOUT });
}

async function waitForTransfer(page) {
  await page.waitForFunction(() => {
    const shell = document.querySelector('[data-warehouse-transfer-shell="true"][data-warehouse-view="transfer-visibility"]');
    const state = shell ? String(shell.getAttribute("data-warehouse-transfer-state") || "") : "";
    return Boolean(shell && state !== "loading" && shell.querySelector("[data-warehouse-transfer-card]") && (shell.querySelector("[data-warehouse-transfer-row]") || shell.querySelector("[data-warehouse-transfer-empty]")));
  }, null, { timeout: TIMEOUT });
}

async function waitForMovementReview(page) {
  await page.waitForFunction(() => Boolean(document.querySelector('[data-warehouse-movement-review-shell="true"][data-warehouse-view="movement-review"]')), null, { timeout: TIMEOUT });
}

async function waitForStockPosture(page) {
  await page.waitForFunction(() => Boolean(document.querySelector('[data-warehouse-stock-posture-shell="true"][data-warehouse-view="stock-posture-review"] [data-warehouse-stock-posture-panel="stock"]')), null, { timeout: TIMEOUT });
}

async function collapseBodySidebarForNarrowViewport(page) {
  const viewport = page.viewportSize();
  if (!viewport || viewport.width > 520) return true;
  const collapsed = await page.evaluate(() => {
    const expandedSidebar = document.querySelector(".body-sidebar-container.expanded");
    if (!expandedSidebar) return true;
    const controls = Array.from(expandedSidebar.querySelectorAll("button, a, [role='button'], [tabindex]"));
    const collapseControl = controls.find((node) => /\bCollapse\b/i.test((node.innerText || node.getAttribute("aria-label") || "").trim()));
    if (collapseControl && typeof collapseControl.click === "function") collapseControl.click();
    return false;
  });
  if (collapsed) return true;
  await page.waitForTimeout(250);
  return page.evaluate(() => !document.querySelector(".body-sidebar-container.expanded"));
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
      pageHeadCount: Array.from(document.querySelectorAll(".page-head")).filter(visible).length,
      headerCount: Array.from(document.querySelectorAll(".warehouse-console-header, .warehouse-inbound-queue-header, .warehouse-receiving-header")).filter(visible).length,
      transferShellCount: Array.from(document.querySelectorAll('[data-warehouse-transfer-shell="true"][data-warehouse-view="transfer-visibility"]')).filter(visible).length,
      transferState: document.querySelector('[data-warehouse-transfer-shell="true"][data-warehouse-view="transfer-visibility"]') ? document.querySelector('[data-warehouse-transfer-shell="true"][data-warehouse-view="transfer-visibility"]').getAttribute("data-warehouse-transfer-state") || "" : "",
      transferCommandCount: Array.from(document.querySelectorAll("[data-warehouse-transfer-command]")).filter(visible).length,
      transferCommandChipCount: Array.from(document.querySelectorAll("[data-warehouse-transfer-command-chip]")).filter(visible).length,
      transferCommandFactCount: Array.from(document.querySelectorAll("[data-warehouse-transfer-command-fact]")).filter(visible).length,
      transferGuardrailCount: Array.from(document.querySelectorAll("[data-warehouse-transfer-guardrail]")).filter(visible).length,
      transferCardCount: Array.from(document.querySelectorAll("[data-warehouse-transfer-card]")).filter(visible).length,
      transferSummaryCardCount: Array.from(document.querySelectorAll("[data-warehouse-transfer-summary-card]")).filter(visible).length,
      transferGroupCount: Array.from(document.querySelectorAll("[data-warehouse-transfer-group]")).filter(visible).length,
      transferRowCount: Array.from(document.querySelectorAll("[data-warehouse-transfer-row]")).filter(visible).length,
      transferRowFactCount: Array.from(document.querySelectorAll("[data-warehouse-transfer-row-fact]")).filter(visible).length,
      transferEmptyCount: Array.from(document.querySelectorAll("[data-warehouse-transfer-empty]")).filter(visible).length,
      transferRouteStockPostureCount: Array.from(document.querySelectorAll("[data-warehouse-transfer-route-stock-posture]")).filter(visible).length,
      transferRouteMovementCount: Array.from(document.querySelectorAll("[data-warehouse-transfer-route-movement]")).filter(visible).length,
      transferOpenWarehouseCount: Array.from(document.querySelectorAll("[data-warehouse-back-overview]")).filter(visible).length,
      transferApplyCount: Array.from(document.querySelectorAll("[data-warehouse-filter-apply]")).filter(visible).length,
      transferResetCount: Array.from(document.querySelectorAll("[data-warehouse-filter-reset]")).filter(visible).length,
      transferRefreshCount: Array.from(document.querySelectorAll("[data-warehouse-filter-refresh]")).filter(visible).length,
      transferDetailToggleCount: Array.from(document.querySelectorAll("[data-warehouse-row-toggle]")).filter(visible).length,
      stockPostureShellCount: Array.from(document.querySelectorAll('[data-warehouse-stock-posture-shell="true"][data-warehouse-view="stock-posture-review"]')).filter(visible).length,
      searchUtilityVisible: Array.from(document.querySelectorAll("[data-erpw-sales-search-open]")).some(visible),
      horizontalOverflow: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
      diagnostics: window.erpWorkspaceWarehouseConsole && window.erpWorkspaceWarehouseConsole.diagnostics ? { ...window.erpWorkspaceWarehouseConsole.diagnostics } : {},
      hasExportedTransferRenderer: Boolean(window.erpWorkspaceWarehouseConsole && typeof window.erpWorkspaceWarehouseConsole.renderTransferVisibility === "function"),
    };
  });
}

function assertClean(state, context) {
  assert(state.shellCount === 1, "Warehouse shell count must remain 1", { context, state });
  assert(state.pageHeadCount === 0, "Warehouse Frappe page-head chrome must not be visible", { context, state });
  assert(state.headerCount === 1, "Warehouse header count must remain 1", { context, state });
  assert(state.horizontalOverflow <= 2, "Warehouse page has horizontal overflow", { context, state });
  assert(!state.searchUtilityVisible, "Warehouse search entry must stay inactive in W8C", { context, state });
  assert(!FORBIDDEN_ACTION_RE.test(state.actionText), "Forbidden stock action control is visible", { context, state });
  assert(!FORBIDDEN_COPY_RE.test(state.text), "Developer or governance copy is visible", { context, state });
  assert(!VALUATION_RE.test(state.text), "Valuation, accounting, or commercial text is visible", { context, state });
  assert(!NATIVE_ROUTE_RE.test(`${state.hrefs} ${state.actionText}`), "Native route target is visible", { context, state });
}

function assertW12JPolish(state, context) {
  assert(state.transferShellCount === 1, "Transfer shell count must be 1", { context, state });
  assert(state.transferState !== "loading", "Transfer Visibility still shows loading state", { context, state });
  assert(state.transferCommandCount === 1, "Transfer command header did not render once", { context, state });
  assert(state.transferCommandChipCount === 0, "Transfer top badges should not render in premium queue layout", { context, state });
  assert(state.transferCommandFactCount === 0, "Transfer command fact strip should not render in premium queue layout", { context, state });
  assert(state.transferGuardrailCount === 0, "Transfer guardrail block should not render in premium queue layout", { context, state });
  assert(state.transferSummaryCardCount >= 4, "Transfer summary cards did not render", { context, state });
  assert(state.transferGroupCount >= 4, "Transfer groups did not render", { context, state });
  assert(state.transferRowFactCount >= 4 || state.transferEmptyCount >= 1, "Transfer row facts or controlled empty state did not render", { context, state });
  assert(state.transferOpenWarehouseCount === 0, "Open Warehouse page control should not render in premium queue layout", { context, state });
  assert(state.transferApplyCount === 1, "Transfer Apply control should render once", { context, state });
  assert(state.transferResetCount === 1, "Transfer Reset control should render once", { context, state });
  assert(state.transferRefreshCount === 1, "Transfer Refresh control should render once", { context, state });
  assert(state.transferDetailToggleCount >= 1 || state.transferEmptyCount >= 1, "Transfer row expansion or empty state did not render", { context, state });
  if (ASSET_ROOT) {
    assert(state.transferRouteMovementCount >= 1, "Source transfer movement route did not render", { context, state });
    assert(state.transferRouteStockPostureCount >= 1, "Source transfer stock posture route did not render", { context, state });
  }
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
    assertClean(await snapshot(page), `${user.key}:overview`);

    const cockpitTransferCount = await page.locator("[data-warehouse-open-transfer]").count();
    if (cockpitTransferCount >= 1) {
      await page.locator("[data-warehouse-open-transfer]").first().click();
      await page.waitForURL((url) => /\/(?:desk|app)\/warehouse-console-worklist\/transfer-visibility/.test(url.pathname), { timeout: TIMEOUT });
      await waitForTransfer(page);
      const cockpitState = await snapshot(page);
      assertClean(cockpitState, `${user.key}:transfer-cockpit-navigation`);
      diagnostics.snapshots.push({ name: `${user.key}:transfer-cockpit-navigation`, state: cockpitState, screenshot: await capture(page, `${user.key}-transfer-cockpit-navigation`) });
      await openRoute(page, ["warehouse-console"], "/desk/warehouse-console", waitForOverview);
      assertClean(await snapshot(page), `${user.key}:overview-after-transfer-cockpit`);
    }

    await openRoute(page, ["warehouse-console-worklist", "transfer-visibility"], "/desk/warehouse-console-worklist/transfer-visibility", waitForTransfer);
    if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-transfer-visibility");
    let state = await snapshot(page);
    assertClean(state, `${user.key}:transfer`);
    assert(state.hasExportedTransferRenderer, "Transfer renderer was not exported", { user: user.key, state });
    assert(state.transferShellCount === 1, "Transfer shell count must be 1", { user: user.key, state });
    assert(state.transferCardCount >= 4, "Transfer summary cards did not render", { user: user.key, state });
    assert(state.transferGroupCount >= 4, "Transfer groups did not render", { user: user.key, state });
    assert(state.transferRowCount >= 1 || state.transferEmptyCount >= 1, "Transfer rows or empty state did not render", { user: user.key, state });
    if (EXPECT_W12J) assertW12JPolish(state, `${user.key}:transfer`);
    diagnostics.snapshots.push({ name: `${user.key}:transfer-initial-1440`, state, screenshot: await capture(page, `${user.key}-transfer-initial-1440`) });

    for (const viewport of RESPONSIVE_VIEWPORTS) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      const sidebarCollapsed = await collapseBodySidebarForNarrowViewport(page);
      await waitForTransfer(page);
      const responsiveState = await snapshot(page);
      if (viewport.width <= 520) assert(sidebarCollapsed, "Mobile body sidebar was not collapsed for Transfer Visibility evidence", { user: user.key, viewport, state: responsiveState });
      assertClean(responsiveState, `${user.key}:transfer-${viewport.key}`);
      if (EXPECT_W12J) assertW12JPolish(responsiveState, `${user.key}:transfer-${viewport.key}`);
      diagnostics.snapshots.push({ name: `${user.key}:transfer-${viewport.key}`, sidebarCollapsed, state: responsiveState, screenshot: await capture(page, `${user.key}-transfer-${viewport.key}`) });
    }
    await page.setViewportSize({ width: 1440, height: 900 });

    await page.reload({ waitUntil: "domcontentloaded", timeout: TIMEOUT });
    await waitForTransfer(page);
    state = await snapshot(page);
    assertClean(state, `${user.key}:transfer-reload`);
    if (EXPECT_W12J) assertW12JPolish(state, `${user.key}:transfer-reload`);

    const repeatBaseline = overrideHitCount(diagnostics, "warehouse-transfer-visibility");
    await openRoute(page, ["warehouse-console-worklist", "transfer-visibility"], "/desk/warehouse-console-worklist/transfer-visibility", waitForTransfer);
    await openRoute(page, ["warehouse-console-worklist", "transfer-visibility"], "/desk/warehouse-console-worklist/transfer-visibility", waitForTransfer);
    state = await snapshot(page);
    assertClean(state, `${user.key}:transfer-repeat`);
    if (EXPECT_W12J) assertW12JPolish(state, `${user.key}:transfer-repeat`);
    if (ASSET_ROOT) assert(overrideHitCount(diagnostics, "warehouse-transfer-visibility") === repeatBaseline, "Repeated transfer route navigation made an unnecessary service call", { user: user.key, before: repeatBaseline, after: overrideHitCount(diagnostics, "warehouse-transfer-visibility"), state });

    const filterCount = await page.locator("[data-warehouse-filter-key]").count();
    if (filterCount >= 1) {
      const forcedBaseline = overrideHitCount(diagnostics, "warehouse-transfer-visibility");
      await page.locator("[data-warehouse-filter-apply]").click();
      await waitForTransfer(page);
      await page.locator("[data-warehouse-filter-reset]").click();
      await waitForTransfer(page);
      await page.locator("[data-warehouse-filter-refresh]").click();
      await waitForTransfer(page);
      state = await snapshot(page);
      assertClean(state, `${user.key}:transfer-filters`);
      if (EXPECT_W12J) {
        assertW12JPolish(state, `${user.key}:transfer-filters`);
        if (ASSET_ROOT) assert(overrideHitCount(diagnostics, "warehouse-transfer-visibility") > forcedBaseline, "Apply/Reset/Refresh did not force transfer visibility reload", { user: user.key, before: forcedBaseline, after: overrideHitCount(diagnostics, "warehouse-transfer-visibility"), state });
      }
    }

    const lineToggleCount = await page.locator("[data-warehouse-row-toggle]").count();
    if (lineToggleCount >= 1) {
      await page.locator("[data-warehouse-row-toggle]").first().click();
      state = await snapshot(page);
      if (EXPECT_W12J) assertW12JPolish(state, `${user.key}:transfer-expanded`);
      if (ASSET_ROOT) assert(state.transferRouteMovementCount >= 1, "Source transfer movement route did not render", { user: user.key, state });
      if (state.transferRouteMovementCount >= 1) {
        await page.locator("[data-warehouse-transfer-route-movement]").first().click();
        await page.waitForURL((url) => /\/(?:desk|app)\/warehouse-console-movement\//.test(url.pathname), { timeout: TIMEOUT });
        await waitForMovementReview(page);
        if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-movement-review");
        const movementState = await snapshot(page);
        assertClean(movementState, `${user.key}:transfer-movement-review`);
        diagnostics.snapshots.push({ name: `${user.key}:transfer-movement-review`, state: movementState, screenshot: await capture(page, `${user.key}-transfer-movement-review`) });
        await page.goBack({ waitUntil: "domcontentloaded", timeout: TIMEOUT }).catch(() => {});
        await waitForTransfer(page);
      }
      state = await snapshot(page);
      if (ASSET_ROOT) assert(state.transferRouteStockPostureCount >= 1, "Source transfer posture route did not render", { user: user.key, state });
      if (state.transferRouteStockPostureCount >= 1) {
        await page.locator("[data-warehouse-transfer-route-stock-posture]").first().click();
        await page.waitForURL((url) => /\/(?:desk|app)\/warehouse-console-stock-posture\//.test(url.pathname), { timeout: TIMEOUT });
        await waitForStockPosture(page);
        if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-stock-posture-review");
        const postureState = await snapshot(page);
        assertClean(postureState, `${user.key}:transfer-stock-posture`);
        diagnostics.snapshots.push({ name: `${user.key}:transfer-stock-posture`, state: postureState, screenshot: await capture(page, `${user.key}-transfer-stock-posture`) });
        await page.goBack({ waitUntil: "domcontentloaded", timeout: TIMEOUT }).catch(() => {});
        await waitForTransfer(page);
      }
    }

    state = await snapshot(page);
    assert((state.diagnostics || {}).transferVisibilityServiceCallAttempted >= 1, "Warehouse transfer visibility service call was not attempted", { user: user.key, state, diagnostics });
    if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-page-asset");
    diagnostics.snapshots.push({ name: `${user.key}:final`, state, screenshot: await capture(page, `${user.key}-transfer-final`) });
  } finally {
    await context.close();
  }
  return diagnostics;
}

async function main() {
  assert(AUTHORIZED_USERS.length >= 1, "Warehouse credentials are required for W8C smoke", {
    missing: [
      "ERPW_WAREHOUSE_MANAGER_USERNAME/ERPW_WAREHOUSE_MANAGER_PASSWORD",
      "ERPW_WAREHOUSE_USER_USERNAME/ERPW_WAREHOUSE_USER_PASSWORD",
    ],
  });
  const browser = await chromium.launch({ headless: process.env.ERPW_HEADLESS !== "0" });
  const summary = { ok: false, artifactDir: ARTIFACT_DIR, phase: PHASE_LABEL, sourceOverride: Boolean(ASSET_ROOT), users: [], diagnostics: [] };
  try {
    for (const user of AUTHORIZED_USERS) {
      const diagnostics = await exerciseUser(browser, user);
      const hardConsoleErrors = diagnostics.consoleErrors.filter((entry) => !/favicon|sourcemap|manifest/i.test(entry.text || ""));
      assert(hardConsoleErrors.length === 0, "Browser console errors were recorded", { user: user.key, errors: hardConsoleErrors });
      assert(diagnostics.pageErrors.length === 0, "Page errors were recorded", { user: user.key, errors: diagnostics.pageErrors });
      assert(diagnostics.failedResponses.length === 0, "Failed Warehouse responses were recorded", { user: user.key, failedResponses: diagnostics.failedResponses });
      summary.users.push(user.key);
      summary.diagnostics.push(diagnostics);
    }
    summary.ok = true;
  } catch (error) {
    summary.ok = false;
    summary.error = {
      message: error.message,
      details: error.details || {},
      stack: error.stack,
    };
    throw error;
  } finally {
    await browser.close();
    const summaryPath = path.join(ARTIFACT_DIR, SUMMARY_FILE);
    fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2));
    if (summary.ok) {
      console.log(`${PHASE_LABEL} smoke passed. Summary: ${summaryPath}`);
    } else {
      console.error(`${PHASE_LABEL} smoke failed. Summary: ${summaryPath}`);
    }
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
