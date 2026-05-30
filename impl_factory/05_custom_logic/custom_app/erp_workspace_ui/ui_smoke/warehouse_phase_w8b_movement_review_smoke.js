const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const TIMEOUT = Number(process.env.ERPW_WAREHOUSE_W8B_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_WAREHOUSE_W8B_ARTIFACT_DIR || path.join(
  fs.existsSync("/freeze-artifacts") ? "/freeze-artifacts" : path.join(__dirname, "artifacts"),
  `warehouse-w8b-movement-review-${new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z")}`
);
const ASSET_ROOT = process.env.ERPW_WAREHOUSE_W8B_ASSET_ROOT || "";
const STOCK_POSTURE_TOKEN = Buffer.from(JSON.stringify({
  item_code: "ITEM-103",
  purchase_order: "",
  sales_order: "",
  stock_exception_token: "",
  warehouse: "Main - M",
})).toString("hex");
const MOVEMENT_REVIEW_TOKEN = Buffer.from(JSON.stringify({
  movement_id: "MAT-MOV-0001",
  return_route: { route: "warehouse-console-worklist", queue_key: "movement_visibility" },
})).toString("hex");

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

const FORBIDDEN_ACTION_RE = /\b(Open Stock Entry|Open Ledger|Stock Ledger|Stock Balance|Receive|Ship|Dispatch|Post|Submit|Cancel|Amend|Reconcile|Stock Entry|Purchase Receipt|Delivery Note|Stock Reconciliation|Pick List|Reserve|Unreserve|Assign Serial|Assign Batch|Pack|Scan|Allocate|Create|Edit|Save|Update Stock|Adjust|Print|Email)\b/i;
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

function hasOverrideHit(diagnostics, key) {
  return (diagnostics.overrideHits || []).some((entry) => entry.key === key);
}

function sidebarItems() {
  return [
    { key: "warehouse_console_home", label: "Overview", icon: "item", target: { kind: "page", route: "warehouse-console" } },
    { key: "inbound_receiving", label: "Inbound Receiving", icon: "quotation", target: { kind: "worklist", queue_key: "inbound_receiving" } },
    { key: "outbound_picking", label: "Outbound Picking", icon: "order", target: { kind: "worklist", queue_key: "outbound_picking" } },
    { key: "stock_exceptions", label: "Stock Exceptions", icon: "report", target: { kind: "worklist", queue_key: "stock_exceptions" } },
    { key: "movement_visibility", label: "Movement Visibility", icon: "stock", target: { kind: "worklist", queue_key: "movement_visibility" } },
  ];
}

function workspacePayload() {
  return {
    workspace_id: "warehouse",
    status: "w8b_movement_review",
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
      movementVisibility: "erp_workspace_ui.warehouse_console.service.get_warehouse_movement_visibility_queue",
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
      { key: "transfer_requests", label: "Movement Watch", value: 2, note: "Recorded movement posture available.", state: "live" },
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

function movementRows() {
  return [
    {
      key: "MAT-MOV-0001",
      movement_id: "MAT-MOV-0001",
      movement_type: "Material Transfer",
      purpose: "Material Transfer",
      posting_date: "2026-05-29",
      posting_time: "09:15:00",
      source_warehouse: "Stores - M",
      target_warehouse: "Main - M",
      direction_label: "Stores - M to Main - M",
      item_count: 2,
      quantity_summary: "7 Nos",
      group_key: "internal_transfers",
      group_label: "Internal Transfers",
      route_targets: {
        movement_review: { route: "warehouse-console-movement", context_token: MOVEMENT_REVIEW_TOKEN },
        stock_posture: { route: "warehouse-console-stock-posture", context_token: STOCK_POSTURE_TOKEN },
      },
      sample_items: [
        { item_code: "ITEM-103", item_name: "Bluetooth Speaker", qty: "5", uom: "Nos", source_warehouse: "Stores - M", target_warehouse: "Main - M", route_target: { route: "warehouse-console-stock-posture", context_token: STOCK_POSTURE_TOKEN } },
        { item_code: "ITEM-104", item_name: "Cable Pack", qty: "2", uom: "Nos", source_warehouse: "Stores - M", target_warehouse: "Main - M", route_target: { route: "warehouse-console-stock-posture", context_token: STOCK_POSTURE_TOKEN } },
      ],
    },
    {
      key: "MAT-MOV-0002",
      movement_id: "MAT-MOV-0002",
      movement_type: "Material Receipt",
      purpose: "Material Receipt",
      posting_date: "2026-05-28",
      posting_time: "10:20:00",
      source_warehouse: "",
      target_warehouse: "Receiving - M",
      direction_label: "Into Receiving - M",
      item_count: 1,
      quantity_summary: "10 Nos",
      group_key: "receipts",
      group_label: "Receipts",
      route_targets: { stock_posture: { route: "warehouse-console-stock-posture", context_token: STOCK_POSTURE_TOKEN } },
      sample_items: [
        { item_code: "ITEM-105", item_name: "Power Bank", qty: "10", uom: "Nos", source_warehouse: "", target_warehouse: "Receiving - M", route_target: { route: "warehouse-console-stock-posture", context_token: STOCK_POSTURE_TOKEN } },
      ],
    },
  ];
}

function movementPayload() {
  const rows = movementRows();
  return {
    workspace: workspacePayload(),
    context: sidebarPayload().context,
    state: { kind: "ready", title: "Warehouse Console ready", detail: "Movement visibility is available for review." },
    page: { title: "Movement Visibility", key: "movement_visibility" },
    summary: { title: "Movement Visibility", subtitle: "Recorded stock movement posture across warehouses.", chips: [{ label: "Read-only" }, { label: `${rows.length} shown` }] },
    controls: {
      fields: [
        { key: "state", label: "Movement State", type: "select", value: "", options: [{ label: "All", value: "" }, { label: "Internal Transfers", value: "internal_transfers" }, { label: "Receipts", value: "receipts" }] },
        { key: "warehouse", label: "Warehouse", type: "text", value: "", placeholder: "Filter warehouse" },
        { key: "movement", label: "Movement ID", type: "text", value: "", placeholder: "Filter movement" },
      ],
    },
    cards: [
      { key: "total_movements", label: "Total Movements", title: "Total Movements", value: rows.length, state: "live", note: "Latest 14 day window." },
      { key: "internal_transfers", label: "Internal Transfers", title: "Internal Transfers", value: 1, state: "live", note: "Warehouse-to-warehouse posture." },
      { key: "receipts", label: "Receipts", title: "Receipts", value: 1, state: "live", note: "Stock arriving into warehouse." },
      { key: "needs_review", label: "Needs Review", title: "Needs Review", value: 0, state: "live", note: "Warehouse posture needs checking." },
    ],
    groups: [
      { key: "internal_transfers", title: "Internal Transfers", summary: "Warehouse-to-warehouse movements recorded recently.", rows: [rows[0]] },
      { key: "receipts", title: "Receipts", summary: "Stock arriving into a warehouse.", rows: [rows[1]] },
      { key: "issues", title: "Issues", summary: "Stock leaving a warehouse for operational use.", rows: [] },
      { key: "adjustments_repack", title: "Adjustments and Repack", summary: "Recorded adjustment or repack movements.", rows: [] },
      { key: "needs_review", title: "Needs Review", summary: "Movements with incomplete warehouse posture.", rows: [] },
    ],
    rows,
    action_targets: { stock_posture: { route: "warehouse-console-stock-posture" } },
    fetched_at: "2026-05-29 00:00:00",
  };
}

function movementReviewPayload(contextToken = MOVEMENT_REVIEW_TOKEN) {
  return {
    workspace: workspacePayload(),
    context: sidebarPayload().context,
    state: { kind: "ready", title: "Warehouse Console ready", detail: "Movement review is available." },
    page: { title: "Movement Review", key: "movement_review", context_token: contextToken, movement_id: "MAT-MOV-0001" },
    header: {
      movement_id: "MAT-MOV-0001",
      purpose: "Warehouse Movement",
      movement_type: "Warehouse Movement",
      posting_date: "2026-05-29",
      posting_time: "09:15:00",
      source_warehouse: "Stores - M",
      target_warehouse: "Main - M",
      direction_label: "Stores - M to Main - M",
      docstatus_label: "Posted",
      item_count: 2,
      quantity_summary: "7 Nos",
      context_token: contextToken,
      fetched_at: "2026-05-29 00:00:00",
    },
    parent: {
      movement_id: "MAT-MOV-0001",
      purpose: "Warehouse Movement",
      movement_type: "Warehouse Movement",
      posting_date: "2026-05-29",
      posting_time: "09:15:00",
      source_warehouse: "Stores - M",
      target_warehouse: "Main - M",
      direction_label: "Stores - M to Main - M",
      docstatus_label: "Posted",
      item_count: 2,
      quantity_summary: "7 Nos",
    },
    direction_panel: {
      key: "direction",
      title: "Direction",
      summary: "Movement between warehouse locations.",
      items: [
        { label: "From", value: "Stores - M" },
        { label: "To", value: "Main - M" },
        { label: "Direction", value: "Stores - M to Main - M" },
      ],
    },
    related_panel: {
      key: "related",
      title: "Related Reviews",
      summary: "Custom Warehouse routes for stock posture only.",
      items: [{ label: "Stock posture", value: "2 item reviews" }],
    },
    summary_cards: [
      { key: "items", label: "Items", value: "2", note: "Lines in this movement" },
      { key: "quantity", label: "Quantity", value: "7 Nos", note: "Operational quantity" },
      { key: "warehouses", label: "Warehouses", value: "2", note: "Warehouse locations involved" },
      { key: "posture", label: "Posture Links", value: "2", note: "Custom stock posture reviews" },
    ],
    line_groups: [
      {
        key: "warehouse_movement",
        title: "Movement Lines",
        summary: "Item movement posture for this posted record.",
        rows: [
          { item_code: "ITEM-103", item_name: "Bluetooth Speaker", stock_uom: "Nos", quantity: "5", source_warehouse: "Stores - M", target_warehouse: "Main - M", direction_label: "Stores - M to Main - M", line_note: "Warehouse movement between locations.", stock_posture_route: { route: "warehouse-console-stock-posture", context_token: STOCK_POSTURE_TOKEN } },
          { item_code: "ITEM-104", item_name: "Cable Pack", stock_uom: "Nos", quantity: "2", source_warehouse: "Stores - M", target_warehouse: "Main - M", direction_label: "Stores - M to Main - M", line_note: "Warehouse movement between locations.", stock_posture_route: { route: "warehouse-console-stock-posture", context_token: STOCK_POSTURE_TOKEN } },
        ],
      },
    ],
    related_routes: [
      { key: "ITEM-103-Main-M", title: "ITEM-103", label: "Review stock posture", detail: "Main - M", route_target: { route: "warehouse-console-stock-posture", context_token: STOCK_POSTURE_TOKEN } },
    ],
    allowed_actions: [{ key: "refresh", label: "Refresh", kind: "read_only" }, { key: "back", label: "Back", kind: "navigation" }],
    action_targets: { back: { route: "warehouse-console-worklist", queue_key: "movement_visibility" } },
    fetched_at: "2026-05-29 00:00:00",
  };
}

function stockPosturePayload(contextToken = STOCK_POSTURE_TOKEN) {
  return {
    workspace: workspacePayload(),
    context: sidebarPayload().context,
    state: { kind: "ready", title: "Warehouse Console ready", detail: "Stock posture is available for review." },
    page: { title: "Stock Posture Review", key: "stock_posture_review", context_token: contextToken },
    header: { title: "Stock Posture Review", subtitle: "Item and warehouse posture.", context_token: contextToken, item_code: "ITEM-103", item_name: "Bluetooth Speaker", warehouse: "Main - M", posture_label: "Available", explanation: "Visible stock covers current movement posture.", fetched_at: "2026-05-29 00:00:00" },
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
      related: { title: "Related Reviews", summary: "Return to Warehouse movement visibility.", items: [] },
    },
    outbound_rows: [],
    inbound_rows: [],
    related_rows: [{ key: "movement", title: "Movement Visibility", label: "Warehouse Movement", detail: "Return to the movement board.", route_target: { route: "warehouse-console-worklist", queue_key: "movement_visibility" } }],
    allowed_actions: [{ key: "refresh", label: "Refresh", kind: "read_only" }, { key: "back", label: "Back", kind: "navigation" }],
    action_targets: { back: { route: "warehouse-console-worklist", queue_key: "movement_visibility" } },
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
    const file = isMovementReview
      ? "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_movement/warehouse_console_movement.js"
      : isStockPosture
      ? "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_stock_posture/warehouse_console_stock_posture.js"
      : isWorklist
        ? "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/warehouse_console_worklist.js"
        : "erp_workspace_ui/erp_workspace_ui/page/warehouse_console/warehouse_console.js";
    const name = isMovementReview ? "warehouse-console-movement" : isStockPosture ? "warehouse-console-stock-posture" : isWorklist ? "warehouse-console-worklist" : "warehouse-console";
    const script = readSource(file);
    recordOverrideHit(diagnostics, "desk-page-getpage", request, { fulfilled: Boolean(script), page: name });
    const pageDoc = { doctype: "Page", name, page_name: name, title: "Warehouse Console", module: "ERP Workspace UI", standard: "Yes", content: "", script };
    return route.fulfill({ status: script ? 200 : 404, contentType: "application/json", body: JSON.stringify({ docs: [pageDoc], message: pageDoc }) });
  });
  const methodPayloads = [
    ["get_warehouse_console_overview", "warehouse-overview", () => overviewPayload()],
    ["get_warehouse_console_sidebar_context", "warehouse-sidebar", () => sidebarPayload()],
    ["get_warehouse_movement_visibility_queue", "warehouse-movement-visibility", () => movementPayload()],
    ["get_warehouse_movement_review", "warehouse-movement-review", (body) => movementReviewPayload(body.context || body.context_token)],
    ["get_warehouse_stock_posture_review", "warehouse-stock-posture-review", (body) => stockPosturePayload(body.context_token)],
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

async function waitForMovement(page) {
  await page.waitForFunction(() => {
    const shell = document.querySelector('[data-warehouse-movement-shell="true"][data-warehouse-view="movement-visibility"]');
    return Boolean(shell && shell.querySelector("[data-warehouse-movement-card]") && (shell.querySelector("[data-warehouse-movement-row]") || shell.querySelector("[data-warehouse-movement-empty]")));
  }, null, { timeout: TIMEOUT });
}

async function waitForMovementReview(page) {
  await page.waitForFunction(() => {
    const shell = document.querySelector('[data-warehouse-movement-review-shell="true"][data-warehouse-view="movement-review"]');
    return Boolean(shell && shell.querySelector("[data-warehouse-movement-review-card]") && (shell.querySelector("[data-warehouse-movement-review-line]") || shell.querySelector("[data-warehouse-movement-review-empty]")));
  }, null, { timeout: TIMEOUT });
}

async function waitForStockPosture(page) {
  await page.waitForFunction(() => Boolean(document.querySelector('[data-warehouse-stock-posture-shell="true"][data-warehouse-view="stock-posture-review"] [data-warehouse-stock-posture-panel="stock"]')), null, { timeout: TIMEOUT });
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
      movementShellCount: Array.from(document.querySelectorAll('[data-warehouse-movement-shell="true"][data-warehouse-view="movement-visibility"]')).filter(visible).length,
      movementCardCount: Array.from(document.querySelectorAll("[data-warehouse-movement-card]")).filter(visible).length,
      movementGroupCount: Array.from(document.querySelectorAll("[data-warehouse-movement-group]")).filter(visible).length,
      movementRowCount: Array.from(document.querySelectorAll("[data-warehouse-movement-row]")).filter(visible).length,
      movementEmptyCount: Array.from(document.querySelectorAll("[data-warehouse-movement-empty]")).filter(visible).length,
      movementRouteReviewCount: Array.from(document.querySelectorAll("[data-warehouse-movement-route-review]")).filter(visible).length,
      movementRouteStockPostureCount: Array.from(document.querySelectorAll("[data-warehouse-movement-route-stock-posture]")).filter(visible).length,
      movementReviewShellCount: Array.from(document.querySelectorAll('[data-warehouse-movement-review-shell="true"][data-warehouse-view="movement-review"]')).filter(visible).length,
      movementReviewCardCount: Array.from(document.querySelectorAll("[data-warehouse-movement-review-card]")).filter(visible).length,
      movementReviewPanelCount: Array.from(document.querySelectorAll("[data-warehouse-movement-review-panel], [data-warehouse-movement-review-related-panel]")).filter(visible).length,
      movementReviewLineGroupCount: Array.from(document.querySelectorAll("[data-warehouse-movement-review-line-group]")).filter(visible).length,
      movementReviewLineCount: Array.from(document.querySelectorAll("[data-warehouse-movement-review-line]")).filter(visible).length,
      movementReviewEmptyCount: Array.from(document.querySelectorAll("[data-warehouse-movement-review-empty]")).filter(visible).length,
      movementReviewRouteStockPostureCount: Array.from(document.querySelectorAll("[data-warehouse-movement-review-route-stock-posture], [data-warehouse-movement-review-related-row]")).filter(visible).length,
      stockPostureShellCount: Array.from(document.querySelectorAll('[data-warehouse-stock-posture-shell="true"][data-warehouse-view="stock-posture-review"]')).filter(visible).length,
      searchUtilityVisible: Array.from(document.querySelectorAll("[data-erpw-sales-search-open]")).some(visible),
      horizontalOverflow: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
      diagnostics: window.erpWorkspaceWarehouseConsole && window.erpWorkspaceWarehouseConsole.diagnostics ? { ...window.erpWorkspaceWarehouseConsole.diagnostics } : {},
      hasExportedMovementRenderer: Boolean(window.erpWorkspaceWarehouseConsole && typeof window.erpWorkspaceWarehouseConsole.renderMovementVisibility === "function"),
      hasExportedMovementReviewRenderer: Boolean(window.erpWorkspaceWarehouseConsole && typeof window.erpWorkspaceWarehouseConsole.renderMovementReview === "function"),
    };
  });
}

function assertClean(state, context) {
  assert(state.shellCount === 1, "Warehouse shell count must remain 1", { context, state });
  assert(state.headerCount === 1, "Warehouse header count must remain 1", { context, state });
  assert(state.horizontalOverflow <= 2, "Warehouse page has horizontal overflow", { context, state });
  assert(!state.searchUtilityVisible, "Warehouse search entry must stay inactive in W8B", { context, state });
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
    assertClean(await snapshot(page), `${user.key}:overview`);

    await openRoute(page, ["warehouse-console-worklist", "movement-visibility"], "/desk/warehouse-console-worklist/movement-visibility", waitForMovement);
    if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-movement-visibility");
    let state = await snapshot(page);
    assertClean(state, `${user.key}:movement`);
    assert(state.hasExportedMovementRenderer, "Movement renderer was not exported", { user: user.key, state });
    assert(state.movementShellCount === 1, "Movement shell count must be 1", { user: user.key, state });
    assert(state.movementCardCount >= 4, "Movement summary cards did not render", { user: user.key, state });
    assert(state.movementGroupCount >= 5, "Movement groups did not render", { user: user.key, state });
    assert(state.movementRowCount >= 1 || state.movementEmptyCount >= 1, "Movement rows or empty state did not render", { user: user.key, state });
    if (ASSET_ROOT) assert(state.movementRouteReviewCount >= 1, "Source movement review route did not render", { user: user.key, state });

    if (await page.locator("[data-warehouse-movement-route-review]").count()) {
      await page.locator("[data-warehouse-movement-route-review]").first().click();
      await page.waitForURL((url) => /\/(?:desk|app)\/warehouse-console-movement\//.test(url.pathname), { timeout: TIMEOUT });
      await waitForMovementReview(page);
      if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-movement-review");
      state = await snapshot(page);
      assertClean(state, `${user.key}:movement-review-from-row`);
      assert(state.hasExportedMovementReviewRenderer, "Movement review renderer was not exported", { user: user.key, state });
      assert(state.movementReviewShellCount === 1, "Movement review shell count must be 1", { user: user.key, state });
      assert(state.movementReviewCardCount >= 4, "Movement review summary cards did not render", { user: user.key, state });
      assert(state.movementReviewPanelCount >= 2, "Movement review panels did not render", { user: user.key, state });
      assert(state.movementReviewLineGroupCount >= 1, "Movement review line groups did not render", { user: user.key, state });
      assert(state.movementReviewLineCount >= 1 || state.movementReviewEmptyCount >= 1, "Movement review lines or empty state did not render", { user: user.key, state });
    }

    await openRoute(page, ["warehouse-console-movement", MOVEMENT_REVIEW_TOKEN], `/desk/warehouse-console-movement/${MOVEMENT_REVIEW_TOKEN}`, waitForMovementReview);
    state = await snapshot(page);
    assertClean(state, `${user.key}:movement-review-direct`);
    assert(state.movementReviewShellCount === 1, "Direct movement review shell count must be 1", { user: user.key, state });

    await page.reload({ waitUntil: "domcontentloaded", timeout: TIMEOUT });
    await waitForMovementReview(page);
    assertClean(await snapshot(page), `${user.key}:movement-review-reload`);

    await openRoute(page, ["warehouse-console-movement", MOVEMENT_REVIEW_TOKEN], `/desk/warehouse-console-movement/${MOVEMENT_REVIEW_TOKEN}`, waitForMovementReview);
    await openRoute(page, ["warehouse-console-movement", MOVEMENT_REVIEW_TOKEN], `/desk/warehouse-console-movement/${MOVEMENT_REVIEW_TOKEN}`, waitForMovementReview);
    assertClean(await snapshot(page), `${user.key}:movement-review-repeat`);

    if (await page.locator("[data-warehouse-movement-review-route-stock-posture]").count()) {
      await page.locator("[data-warehouse-movement-review-route-stock-posture]").first().click();
      await page.waitForURL((url) => /\/(?:desk|app)\/warehouse-console-stock-posture\//.test(url.pathname), { timeout: TIMEOUT });
      await waitForStockPosture(page);
      if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-stock-posture-review");
      assertClean(await snapshot(page), `${user.key}:movement-review-stock-posture`);
      await page.goBack({ waitUntil: "domcontentloaded", timeout: TIMEOUT }).catch(() => {});
      await waitForMovementReview(page);
    }

    await page.locator("[data-warehouse-movement-review-refresh]").click();
    await waitForMovementReview(page);
    assertClean(await snapshot(page), `${user.key}:movement-review-refresh`);

    await page.locator("[data-warehouse-movement-review-back]").click();
    await page.waitForURL((url) => /\/(?:desk|app)\/warehouse-console-worklist\/movement-visibility/.test(url.pathname), { timeout: TIMEOUT });
    await waitForMovement(page);
    assertClean(await snapshot(page), `${user.key}:movement-review-back`);

    await page.reload({ waitUntil: "domcontentloaded", timeout: TIMEOUT });
    await waitForMovement(page);
    assertClean(await snapshot(page), `${user.key}:movement-reload`);

    await openRoute(page, ["warehouse-console-worklist", "movement-visibility"], "/desk/warehouse-console-worklist/movement-visibility", waitForMovement);
    await openRoute(page, ["warehouse-console-worklist", "movement-visibility"], "/desk/warehouse-console-worklist/movement-visibility", waitForMovement);
    assertClean(await snapshot(page), `${user.key}:movement-repeat`);

    const filterCount = await page.locator("[data-warehouse-filter-key]").count();
    if (filterCount >= 1) {
      await page.locator("[data-warehouse-filter-apply]").click();
      await waitForMovement(page);
      await page.locator("[data-warehouse-filter-reset]").click();
      await waitForMovement(page);
      await page.locator("[data-warehouse-filter-refresh]").click();
      await waitForMovement(page);
      assertClean(await snapshot(page), `${user.key}:movement-filters`);
    }

    state = await snapshot(page);
    assert(
      (state.diagnostics || {}).movementVisibilityServiceCallAttempted >= 1 || hasOverrideHit(diagnostics, "warehouse-movement-visibility"),
      "Warehouse movement visibility service call was not attempted",
      { user: user.key, state, diagnostics }
    );
    assert(
      (state.diagnostics || {}).movementReviewServiceCallAttempted >= 1 || hasOverrideHit(diagnostics, "warehouse-movement-review"),
      "Warehouse movement review service call was not attempted",
      { user: user.key, state, diagnostics }
    );
    if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-page-asset");
    diagnostics.snapshots.push({ name: `${user.key}:final`, state, screenshot: await capture(page, `${user.key}-movement-review-final`) });
  } finally {
    await context.close();
  }
  return diagnostics;
}

async function main() {
  assert(AUTHORIZED_USERS.length >= 1, "Warehouse credentials are required for W8B smoke", {
    missing: [
      "ERPW_WAREHOUSE_MANAGER_USERNAME/ERPW_WAREHOUSE_MANAGER_PASSWORD",
      "ERPW_WAREHOUSE_USER_USERNAME/ERPW_WAREHOUSE_USER_PASSWORD",
    ],
  });
  const browser = await chromium.launch({ headless: process.env.ERPW_HEADLESS !== "0" });
  const summary = { ok: false, artifactDir: ARTIFACT_DIR, sourceOverride: Boolean(ASSET_ROOT), users: [], diagnostics: [] };
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
    const summaryPath = path.join(ARTIFACT_DIR, "warehouse-w8b-movement-review-summary.json");
    fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2));
    if (summary.ok) {
      console.log(`Warehouse W8B movement review smoke passed. Summary: ${summaryPath}`);
    } else {
      console.error(`Warehouse W8B movement review smoke failed. Summary: ${summaryPath}`);
    }
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
