const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const TIMEOUT = Number(process.env.ERPW_WAREHOUSE_W7A_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_WAREHOUSE_W7A_ARTIFACT_DIR || path.join(
  fs.existsSync("/freeze-artifacts") ? "/freeze-artifacts" : path.join(__dirname, "artifacts"),
  `warehouse-w7a-stock-posture-${new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z")}`
);
const ASSET_ROOT = process.env.ERPW_WAREHOUSE_W7A_ASSET_ROOT || "";
const STOCK_EXCEPTION_TOKEN = "7b226974656d5f636f6465223a224954454d2d313035222c2273616c65735f6f72646572223a22534f2d524556494557222c2277617265686f757365223a2253686f7274202d204d227d";
const STOCK_POSTURE_TOKEN = "7b226974656d5f636f6465223a224954454d2d313035222c2270757263686173655f6f72646572223a22504f2d534f4f4e222c2273616c65735f6f72646572223a22534f2d524556494557222c2273746f636b5f657863657074696f6e5f746f6b656e223a2237623232363937343635366435663633366636343635323233613232343935343435346432643331333033353232326332323733363136633635373335663666373236343635373232323361323235333466326435323435353634393435353732323263323237373631373236353638366637353733363532323361323235333638366637323734323032643230346432323764222c2277617265686f757365223a2253686f7274202d204d227d";
const LIVE_STOCK_POSTURE_TOKEN = process.env.ERPW_WAREHOUSE_W7A_LIVE_CONTEXT_TOKEN || Buffer.from(JSON.stringify({
  item_code: "SPH-SAM-A15-6/128",
  purchase_order: "",
  sales_order: "",
  stock_exception_token: "",
  warehouse: "Yangon Main Warehouse - MMOB",
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

const FORBIDDEN_ACTION_RE = /\b(Receive|Ship|Dispatch|Post|Submit|Cancel|Amend|Reconcile|Stock Entry|Purchase Receipt|Delivery Note|Stock Reconciliation|Pick List|Reserve|Unreserve|Assign Serial|Assign Batch|Pack|Scan|Allocate|Item Price|Default Supplier|Item Supplier)\b/i;
const FORBIDDEN_COPY_RE = /\b(Productized|native ERP|governed|deferred|route only|mutation|backend|frontend|framework|Frappe|smoke|test|Quick Find|\bSearch\b)\b/i;
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

function remember(list, item, limit = 140) {
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
    status: "w7a_stock_posture_review",
    title: "Warehouse Console",
    routes: {
      home: "warehouse-console",
      worklist: "warehouse-console-worklist",
      receiving: "warehouse-console-receiving",
      picking: "warehouse-console-picking",
      stockException: "warehouse-console-stock-exception",
      stockPosture: "warehouse-console-stock-posture",
    },
    methods: {
      overview: "erp_workspace_ui.warehouse_console.service.get_warehouse_console_overview",
      stockExceptions: "erp_workspace_ui.warehouse_console.service.get_warehouse_stock_exceptions",
      stockExceptionReview: "erp_workspace_ui.warehouse_console.service.get_warehouse_stock_exception_review",
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
      context_token: STOCK_EXCEPTION_TOKEN,
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
      route_targets: {
        exception_review: { route: "warehouse-console-stock-exception", context_token: STOCK_EXCEPTION_TOKEN },
        picking: { route: "warehouse-console-picking", sales_order: "SO-REVIEW" },
        receiving: { route: "warehouse-console-receiving", purchase_order: "PO-SOON" },
      },
    },
  ];
}

function stockPayload() {
  const rows = stockRows();
  return {
    workspace: workspacePayload(),
    context: sidebarPayload().context,
    state: { kind: "ready", title: "Warehouse Console ready", detail: "Stock visibility and warehouse posture are available for review." },
    page: { title: "Stock Exceptions", key: "stock_exceptions" },
    summary: { title: "Stock Exceptions", subtitle: "Outbound blockers, inbound cover, and warehouse posture gaps.", chips: [{ label: "Read-only" }, { label: `${rows.length} shown` }] },
    controls: {
      fields: [
        { key: "state", label: "Exception State", type: "select", value: "", options: [{ label: "All", value: "" }, { label: "Inbound Cover Expected", value: "inbound_cover_expected" }] },
        { key: "warehouse", label: "Warehouse", type: "text", value: "", placeholder: "Filter warehouse" },
        { key: "text", label: "Order, Item, Customer", type: "text", value: "", placeholder: "Filter order, item, or customer" },
      ],
    },
    cards: [
      { key: "total_exceptions", label: "Total Exceptions", title: "Total Exceptions", value: rows.length, state: "live", note: "Rows needing warehouse review." },
      { key: "shortage_risk", label: "Shortage Risk", title: "Shortage Risk", value: 0, state: "live", note: "Demand short of visible stock posture." },
      { key: "inbound_cover_soon", label: "Inbound Cover Soon", title: "Inbound Cover Soon", value: 1, state: "live", note: "Supplier stock expected within 14 days." },
      { key: "missing_posture", label: "Missing Warehouse Posture", title: "Missing Warehouse Posture", value: 0, state: "live", note: "Warehouse or stock posture is incomplete." },
    ],
    groups: [
      { key: "needs_stock_review", title: "Needs Stock Review", summary: "Short stock without a near inbound cover.", rows: [] },
      { key: "inbound_cover_expected", title: "Inbound Cover Expected", summary: "Short demand with supplier stock expected soon.", rows },
      { key: "urgent_aging", title: "Urgent / Aging Demand", summary: "Short demand that is due now or past due.", rows: [] },
      { key: "warehouse_posture_missing", title: "Warehouse Posture Missing", summary: "Lines missing warehouse or stock posture.", rows: [] },
    ],
    rows,
    action_targets: { picking: { route: "warehouse-console-picking" }, receiving: { route: "warehouse-console-receiving" } },
    fetched_at: "2026-05-29 00:00:00",
  };
}

function stockExceptionReviewPayload(contextToken = STOCK_EXCEPTION_TOKEN) {
  return {
    workspace: workspacePayload(),
    context: sidebarPayload().context,
    state: { kind: "ready", title: "Warehouse Console ready", detail: "Stock visibility and warehouse posture are available for review." },
    page: { title: "Stock Exception Review", key: "stock_exception_review", context_token: contextToken, sales_order: "SO-REVIEW", item_code: "ITEM-105", source_warehouse: "Short - M" },
    header: {
      title: "Inbound Cover Expected",
      subtitle: "Demand, stock posture, and inbound cover for this warehouse line.",
      exception_label: "Inbound Cover Expected",
      context_token: contextToken,
      sales_order: "SO-REVIEW",
      customer: "Review Customer",
      item_code: "ITEM-105",
      item_name: "Power Bank",
      source_warehouse: "Short - M",
      required_date: "2026-06-03",
      urgency_label: "Due 2026-06-03",
      explanation: "Visible stock is short, with inbound cover expected soon.",
    },
    summary_cards: [
      { key: "state", label: "Exception State", value: "Inbound Cover Expected", note: "Due 2026-06-03" },
      { key: "pending_qty", label: "Pending Demand", value: "8 Nos", note: "SO-REVIEW" },
      { key: "available_qty", label: "Available", value: "2", note: "Short - M" },
      { key: "inbound_cover", label: "Inbound Cover", value: "10", note: "2026-06-05" },
    ],
    panels: {
      demand: { title: "Demand at Risk", summary: "Visible stock is short, with inbound cover expected soon.", items: [{ label: "Sales Order", value: "SO-REVIEW" }, { label: "Customer", value: "Review Customer" }, { label: "Required Date", value: "2026-06-03" }, { label: "Pending Qty", value: "8 Nos" }] },
      stock: { title: "Stock Posture", summary: "Current visible stock compared with pending demand.", route_target: { route: "warehouse-console-stock-posture", context_token: STOCK_POSTURE_TOKEN }, items: [{ label: "Item", value: "ITEM-105 Power Bank" }, { label: "Warehouse", value: "Short - M" }, { label: "Available", value: "2" }, { label: "Projected", value: "2" }, { label: "Short Qty", value: "6 Nos" }] },
      inbound: { title: "Inbound Cover", summary: "Supplier stock expected soon.", items: [{ label: "Expected Qty", value: "10 Nos" }, { label: "Expected Date", value: "2026-06-05" }, { label: "Inbound Order", value: "PO-SOON" }] },
      next_reviews: { title: "Recommended Review", summary: "Read-only review paths available for this exception.", items: [
        { label: "Picking Posture", value: "Review outbound line readiness inside Warehouse.", target: { route: "warehouse-console-picking", sales_order: "SO-REVIEW" } },
        { label: "Stock Posture", value: "Review item and warehouse posture inside Warehouse.", target: { route: "warehouse-console-stock-posture", context_token: STOCK_POSTURE_TOKEN } },
        { label: "Inbound Cover", value: "Review expected supplier stock inside Warehouse.", target: { route: "warehouse-console-receiving", purchase_order: "PO-SOON" } },
      ] },
    },
    related_rows: [
      { key: "demand", title: "SO-REVIEW", label: "Outbound Demand", detail: "8 Nos pending", route_target: { route: "warehouse-console-picking", sales_order: "SO-REVIEW" } },
      { key: "inbound", title: "PO-SOON", label: "Inbound Cover", detail: "10 expected 2026-06-05", route_target: { route: "warehouse-console-receiving", purchase_order: "PO-SOON" } },
    ],
    action_targets: {
      stock_exceptions: { route: "warehouse-console-worklist", queue_key: "stock_exceptions" },
      picking: { route: "warehouse-console-picking", sales_order: "SO-REVIEW" },
      receiving: { route: "warehouse-console-receiving", purchase_order: "PO-SOON" },
      stock_posture: { route: "warehouse-console-stock-posture", context_token: STOCK_POSTURE_TOKEN },
    },
  };
}

function stockPosturePayload(contextToken = STOCK_POSTURE_TOKEN) {
  return {
    workspace: workspacePayload(),
    context: sidebarPayload().context,
    state: { kind: "ready", title: "Warehouse Console ready", detail: "Stock visibility and warehouse posture are available for review." },
    page: { title: "Stock Posture Review", key: "stock_posture_review", context_token: contextToken, item_code: "ITEM-105", warehouse: "Short - M" },
    header: { title: "Stock Posture Review", subtitle: "Item and warehouse posture for read-only operational review.", context_token: contextToken, item_code: "ITEM-105", item_name: "Power Bank", warehouse: "Short - M", posture_label: "Inbound Cover Expected", explanation: "Visible stock is short, with inbound cover expected soon.", fetched_at: "2026-05-29 00:00:00" },
    summary_cards: [
      { key: "posture", label: "Posture", value: "Inbound Cover Expected", note: "Visible stock is short, with inbound cover expected soon." },
      { key: "available", label: "Available", value: "2", note: "Current operational availability." },
      { key: "projected", label: "Projected", value: "2", note: "Projected warehouse quantity." },
      { key: "open_demand", label: "Open Demand", value: "8", note: "1 open lines" },
      { key: "inbound_cover", label: "Inbound Cover", value: "10", note: "2026-06-05" },
    ],
    panels: {
      stock: { title: "Stock Posture", summary: "Visible stock is short, with inbound cover expected soon.", items: [{ label: "Item", value: "ITEM-105 Power Bank" }, { label: "Warehouse", value: "Short - M" }, { label: "Actual Qty", value: "2" }, { label: "Available Qty", value: "2" }, { label: "Reserved Qty", value: "0" }, { label: "Projected Qty", value: "2" }] },
      inbound: { title: "Inbound Cover", summary: "Submitted purchase orders expected for this item and warehouse.", items: [{ label: "Expected Qty", value: "10" }, { label: "Next Expected Date", value: "2026-06-05" }, { label: "Inbound Orders", value: "1" }] },
      outbound: { title: "Open Demand", summary: "Submitted sales orders with pending demand for this item and warehouse.", items: [{ label: "Pending Qty", value: "8" }, { label: "Open Lines", value: "1" }, { label: "Next Required Date", value: "2026-06-03" }] },
      related: { title: "Related Reviews", summary: "Custom Warehouse review paths connected to this item and warehouse.", items: [{ label: "Picking Posture", value: "Review outbound readiness inside Warehouse." }, { label: "Inbound Cover", value: "Review expected inbound cover inside Warehouse." }] },
    },
    outbound_rows: [{ key: "SO-REVIEW:ITEM-105:Short - M", sales_order: "SO-REVIEW", customer: "Review Customer", item_code: "ITEM-105", item_name: "Power Bank", required_date: "2026-06-03", ordered_qty: "8", delivered_qty: "0", pending_qty: "8", uom: "Nos", warehouse: "Short - M", status: "To Deliver", route_target: { route: "warehouse-console-picking", sales_order: "SO-REVIEW" } }],
    inbound_rows: [{ key: "PO-SOON:ITEM-105:Short - M", purchase_order: "PO-SOON", supplier: "Soon Supply", item_code: "ITEM-105", item_name: "Power Bank", expected_date: "2026-06-05", expected_qty: "10", uom: "Nos", warehouse: "Short - M", status: "To Receive", route_target: { route: "warehouse-console-receiving", purchase_order: "PO-SOON" } }],
    related_rows: [
      { key: "picking", title: "SO-REVIEW", label: "Picking Posture", detail: "Review outbound readiness inside Warehouse.", route_target: { route: "warehouse-console-picking", sales_order: "SO-REVIEW" } },
      { key: "receiving", title: "PO-SOON", label: "Inbound Cover", detail: "Review expected inbound cover inside Warehouse.", route_target: { route: "warehouse-console-receiving", purchase_order: "PO-SOON" } },
      { key: "stock_exception", title: "Stock Exception", label: "Exception Review", detail: "Return to the stock exception context.", route_target: { route: "warehouse-console-stock-exception", context_token: STOCK_EXCEPTION_TOKEN } },
    ],
    action_targets: {
      back: { route: "warehouse-console-stock-exception", context_token: STOCK_EXCEPTION_TOKEN },
      picking: { route: "warehouse-console-picking", sales_order: "SO-REVIEW" },
      receiving: { route: "warehouse-console-receiving", purchase_order: "PO-SOON" },
      stock_exception: { route: "warehouse-console-stock-exception", context_token: STOCK_EXCEPTION_TOKEN },
    },
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
    summary_cards: [{ key: "state", label: "Picking State", value: "Needs Stock Review", note: "Due 2026-06-03" }],
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
    summary_cards: [{ key: "state", label: "Receiving State", value: "Expected Soon", note: "Due 2026-06-05" }],
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
    const isStockPosture = /warehouse-console-stock-posture/i.test(text);
    const isStockExceptionReview = /warehouse-console-stock-exception/i.test(text);
    const isReceiving = /warehouse-console-receiving/i.test(text);
    const isPicking = /warehouse-console-picking/i.test(text);
    const isWorklist = /warehouse-console-worklist/i.test(text);
    const file = isStockPosture
      ? "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_stock_posture/warehouse_console_stock_posture.js"
      : isStockExceptionReview
        ? "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_stock_exception/warehouse_console_stock_exception.js"
        : isReceiving
          ? "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_receiving/warehouse_console_receiving.js"
          : isPicking
            ? "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_picking/warehouse_console_picking.js"
            : isWorklist
              ? "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/warehouse_console_worklist.js"
              : "erp_workspace_ui/erp_workspace_ui/page/warehouse_console/warehouse_console.js";
    const name = isStockPosture ? "warehouse-console-stock-posture" : isStockExceptionReview ? "warehouse-console-stock-exception" : isReceiving ? "warehouse-console-receiving" : isPicking ? "warehouse-console-picking" : isWorklist ? "warehouse-console-worklist" : "warehouse-console";
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
    ["get_warehouse_stock_exception_review", "warehouse-stock-exception-review", (body) => stockExceptionReviewPayload(body.context_token)],
    ["get_warehouse_stock_posture_review", "warehouse-stock-posture-review", (body) => stockPosturePayload(body.context_token)],
    ["get_warehouse_stock_exceptions", "warehouse-stock-exceptions", () => stockPayload()],
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

async function waitForStock(page) {
  await page.waitForFunction(() => Boolean(document.querySelector('[data-warehouse-stock-exception-shell="true"][data-warehouse-view="stock-exceptions"] [data-warehouse-stock-exception-row], [data-warehouse-stock-exception-empty]')), null, { timeout: TIMEOUT });
}

async function waitForStockExceptionReview(page) {
  await page.waitForFunction(() => {
    const shell = document.querySelector('[data-warehouse-stock-exception-review-shell="true"][data-warehouse-view="stock-exception-review"]');
    return Boolean(shell
      && shell.querySelector("[data-warehouse-stock-exception-stock-panel]")
      && (
        shell.querySelector("[data-warehouse-stock-exception-open-posture]")
        || shell.querySelector("[data-warehouse-stock-exception-next-target='stock_posture']")
        || shell.querySelectorAll("[data-warehouse-stock-exception-review-card]").length >= 4
      ));
  }, null, { timeout: TIMEOUT });
}

async function waitForStockPosture(page) {
  await page.waitForFunction(() => {
    const shell = document.querySelector('[data-warehouse-stock-posture-shell="true"][data-warehouse-view="stock-posture-review"]');
    return Boolean(shell
      && shell.querySelector('[data-warehouse-stock-posture-panel="stock"]')
      && (
        shell.querySelectorAll("[data-warehouse-stock-posture-card]").length >= 5
        || shell.querySelector("[data-warehouse-stock-posture-route-picking]")
        || shell.querySelector("[data-warehouse-stock-posture-route-receiving]")
        || shell.querySelector("[data-warehouse-stock-posture-route-stock-exception]")
      ));
  }, null, { timeout: TIMEOUT });
}

async function waitForPicking(page) {
  await page.waitForFunction(() => Boolean(document.querySelector('.warehouse-picking-shell[data-warehouse-view="picking-review"]')), null, { timeout: TIMEOUT });
}

async function waitForReceiving(page) {
  await page.waitForFunction(() => Boolean(document.querySelector('.warehouse-receiving-shell[data-warehouse-view="receiving-review"]')), null, { timeout: TIMEOUT });
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
      stockShellCount: Array.from(document.querySelectorAll('[data-warehouse-stock-exception-shell="true"][data-warehouse-view="stock-exceptions"]')).filter(visible).length,
      stockReviewShellCount: Array.from(document.querySelectorAll('[data-warehouse-stock-exception-review-shell="true"][data-warehouse-view="stock-exception-review"]')).filter(visible).length,
      stockPostureShellCount: Array.from(document.querySelectorAll('[data-warehouse-stock-posture-shell="true"][data-warehouse-view="stock-posture-review"]')).filter(visible).length,
      stockPostureCardCount: Array.from(document.querySelectorAll("[data-warehouse-stock-posture-card]")).filter(visible).length,
      stockPosturePanelCount: Array.from(document.querySelectorAll("[data-warehouse-stock-posture-panel]")).filter(visible).length,
      stockPostureRowCount: Array.from(document.querySelectorAll("[data-warehouse-stock-posture-row], [data-warehouse-stock-posture-related-row]")).filter(visible).length,
      stockPostureEmptyCount: Array.from(document.querySelectorAll("[data-warehouse-stock-posture-empty]")).filter(visible).length,
      stockPostureRoutePickingCount: Array.from(document.querySelectorAll("[data-warehouse-stock-posture-route-picking]")).filter(visible).length,
      stockPostureRouteReceivingCount: Array.from(document.querySelectorAll("[data-warehouse-stock-posture-route-receiving]")).filter(visible).length,
      stockPostureRouteExceptionCount: Array.from(document.querySelectorAll("[data-warehouse-stock-posture-route-stock-exception]")).filter(visible).length,
      stockExceptionOpenPostureCount: Array.from(document.querySelectorAll("[data-warehouse-stock-exception-open-posture], [data-warehouse-stock-exception-next-target='stock_posture']")).filter(visible).length,
      searchUtilityVisible: Array.from(document.querySelectorAll("[data-erpw-sales-search-open]")).some(visible),
      horizontalOverflow: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
      diagnostics: window.erpWorkspaceWarehouseConsole && window.erpWorkspaceWarehouseConsole.diagnostics ? { ...window.erpWorkspaceWarehouseConsole.diagnostics } : {},
      hasExportedStockPostureRenderer: Boolean(window.erpWorkspaceWarehouseConsole && typeof window.erpWorkspaceWarehouseConsole.renderStockPostureReview === "function"),
    };
  });
}

function assertClean(state, context) {
  assert(state.shellCount === 1, "Warehouse shell count must remain 1", { context, state });
  assert(state.headerCount === 1, "Warehouse header count must remain 1", { context, state });
  assert(state.horizontalOverflow <= 2, "Warehouse page has horizontal overflow", { context, state });
  assert(!state.searchUtilityVisible, "Warehouse search entry must stay inactive in W7A", { context, state });
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

    await openRoute(page, ["warehouse-console-worklist", "stock-exceptions"], "/desk/warehouse-console-worklist/stock-exceptions", waitForStock);
    if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-stock-exceptions");
    let state = await snapshot(page);
    assertClean(state, `${user.key}:stock-exceptions`);

    const exceptionDetailCount = await page.locator("[data-warehouse-stock-exception-route-detail]").count();
    if (ASSET_ROOT) {
      assert(exceptionDetailCount >= 1, "Source stock exception review row did not render", { user: user.key, state });
    }
    if (exceptionDetailCount >= 1) {
      await page.locator("[data-warehouse-stock-exception-route-detail]").first().click();
      await page.waitForURL((url) => /\/(?:desk|app)\/warehouse-console-stock-exception\//.test(url.pathname), { timeout: TIMEOUT });
      await waitForStockExceptionReview(page);
      if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-stock-exception-review");
      state = await snapshot(page);
      assertClean(state, `${user.key}:stock-exception-review`);
      assert(state.stockExceptionOpenPostureCount >= 1, "Stock posture drilldown action did not render from stock exception review", { user: user.key, state });

      await page.locator("[data-warehouse-stock-exception-open-posture], [data-warehouse-stock-exception-next-target='stock_posture']").first().click();
      await page.waitForURL((url) => /\/(?:desk|app)\/warehouse-console-stock-posture\//.test(url.pathname), { timeout: TIMEOUT });
    } else {
      await openRoute(page, ["warehouse-console-stock-posture", LIVE_STOCK_POSTURE_TOKEN], `/desk/warehouse-console-stock-posture/${LIVE_STOCK_POSTURE_TOKEN}`, waitForStockPosture);
    }
    await waitForStockPosture(page);
    if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-stock-posture-review");
    state = await snapshot(page);
    assertClean(state, `${user.key}:stock-posture`);
    assert(state.stockPostureShellCount === 1, "Stock posture shell count must be 1", { user: user.key, state });
    assert(state.stockPostureCardCount >= 5, "Stock posture summary cards did not render", { user: user.key, state });
    assert(state.stockPosturePanelCount >= 4, "Stock posture panels did not render", { user: user.key, state });
    assert(state.stockPostureRowCount >= 3 || state.stockPostureEmptyCount >= 1, "Stock posture rows or empty state did not render", { user: user.key, state });
    if (ASSET_ROOT) {
      assert(state.stockPostureRoutePickingCount >= 1, "Stock posture picking route did not render", { user: user.key, state });
      assert(state.stockPostureRouteReceivingCount >= 1, "Stock posture receiving route did not render", { user: user.key, state });
      assert(state.stockPostureRouteExceptionCount >= 1, "Stock posture exception route did not render", { user: user.key, state });
    }
    const canRoutePicking = state.stockPostureRoutePickingCount >= 1;
    const canRouteReceiving = state.stockPostureRouteReceivingCount >= 1;
    const canRouteException = state.stockPostureRouteExceptionCount >= 1;
    await capture(page, `${user.key}-stock-posture`);

    await page.reload({ waitUntil: "domcontentloaded", timeout: TIMEOUT });
    await waitForStockPosture(page);
    assertClean(await snapshot(page), `${user.key}:stock-posture-reload`);

    const directToken = ASSET_ROOT ? STOCK_POSTURE_TOKEN : LIVE_STOCK_POSTURE_TOKEN;
    await openRoute(page, ["warehouse-console-stock-posture", directToken], `/desk/warehouse-console-stock-posture/${directToken}`, waitForStockPosture);
    await openRoute(page, ["warehouse-console-stock-posture", directToken], `/desk/warehouse-console-stock-posture/${directToken}`, waitForStockPosture);
    assertClean(await snapshot(page), `${user.key}:stock-posture-repeat`);

    if (canRoutePicking) {
      await page.locator("[data-warehouse-stock-posture-route-picking]").first().click();
      await page.waitForURL((url) => /\/(?:desk|app)\/warehouse-console-picking\//.test(url.pathname), { timeout: TIMEOUT });
      await waitForPicking(page);
      assertClean(await snapshot(page), `${user.key}:posture-picking`);
      await page.goBack({ waitUntil: "domcontentloaded", timeout: TIMEOUT });
      await waitForStockPosture(page);
    }

    if (canRouteReceiving) {
      await page.locator("[data-warehouse-stock-posture-route-receiving]").first().click();
      await page.waitForURL((url) => /\/(?:desk|app)\/warehouse-console-receiving\//.test(url.pathname), { timeout: TIMEOUT });
      await waitForReceiving(page);
      assertClean(await snapshot(page), `${user.key}:posture-receiving`);
      await page.goBack({ waitUntil: "domcontentloaded", timeout: TIMEOUT });
      await waitForStockPosture(page);
    }

    if (canRouteException) {
      await page.locator("[data-warehouse-stock-posture-route-stock-exception]").first().click();
      await page.waitForURL((url) => /\/(?:desk|app)\/warehouse-console-stock-exception\//.test(url.pathname), { timeout: TIMEOUT });
      await waitForStockExceptionReview(page);
      assertClean(await snapshot(page), `${user.key}:posture-exception`);
    }

    await openRoute(page, ["warehouse-console-stock-posture", directToken], `/desk/warehouse-console-stock-posture/${directToken}`, waitForStockPosture);
    await page.locator("[data-warehouse-stock-posture-refresh]").click();
    await waitForStockPosture(page);
    assertClean(await snapshot(page), `${user.key}:posture-refresh`);

    await page.locator("[data-warehouse-stock-posture-back]").click();
    if (canRouteException) {
      await page.waitForURL((url) => /\/(?:desk|app)\/warehouse-console-stock-exception\//.test(url.pathname), { timeout: TIMEOUT });
      await waitForStockExceptionReview(page);
    } else if (canRoutePicking) {
      await page.waitForURL((url) => /\/(?:desk|app)\/warehouse-console-picking\//.test(url.pathname), { timeout: TIMEOUT });
      await waitForPicking(page);
    } else if (canRouteReceiving) {
      await page.waitForURL((url) => /\/(?:desk|app)\/warehouse-console-receiving\//.test(url.pathname), { timeout: TIMEOUT });
      await waitForReceiving(page);
    } else {
      await page.waitForURL((url) => /\/(?:desk|app)\/warehouse-console-worklist\/stock-exceptions/.test(url.pathname), { timeout: TIMEOUT });
      await waitForStock(page);
    }
    assertClean(await snapshot(page), `${user.key}:posture-back`);

    state = await snapshot(page);
    assert(state.hasExportedStockPostureRenderer, "Warehouse exported stock posture renderer is missing", { user: user.key, state, diagnostics });
    assert((state.diagnostics || {}).renderStockPostureReviewEntered >= 1, "Warehouse stock posture renderer was not entered", { user: user.key, state, diagnostics });
    assert((state.diagnostics || {}).stockPostureReviewServiceCallAttempted >= 1, "Warehouse stock posture service call was not attempted", { user: user.key, state, diagnostics });
    if (ASSET_ROOT) {
      assert(diagnostics.overrideHits.some((hit) => hit.key === "desk-page-getpage" && hit.page === "warehouse-console-stock-posture"), "Warehouse stock posture getpage source override was not used", { user: user.key, diagnostics });
      assert(diagnostics.overrideHits.some((hit) => hit.key === "warehouse-page-asset"), "Warehouse page asset source override was not used", { user: user.key, diagnostics });
      assert(diagnostics.overrideHits.some((hit) => hit.key === "warehouse-stock-posture-review"), "Warehouse stock posture source override was not used", { user: user.key, diagnostics });
    }
    assert(!diagnostics.consoleErrors.some((entry) => entry.type === "error"), "Warehouse W7A smoke recorded console errors", { user: user.key, diagnostics });
    assert(diagnostics.pageErrors.length === 0, "Warehouse W7A smoke recorded page errors", { user: user.key, diagnostics });
    assert(diagnostics.failedResponses.length === 0, "Warehouse W7A smoke recorded failed responses", { user: user.key, diagnostics });
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
  assert(AUTHORIZED_USERS.length > 0, "No Warehouse W7A smoke credentials were provided. Set ERPW_WAREHOUSE_MANAGER_USERNAME/PASSWORD or ERPW_WAREHOUSE_USER_USERNAME/PASSWORD.");
  const browser = await chromium.launch({ headless: process.env.ERPW_HEADLESS !== "0" });
  const summary = { status: "pass", artifactDir: ARTIFACT_DIR, sourceOverride: Boolean(ASSET_ROOT), authorizedUsers: AUTHORIZED_USERS.map((user) => user.key), authorized: [] };
  try {
    for (const user of AUTHORIZED_USERS) {
      summary.authorized.push(await exerciseUser(browser, user));
    }
    fs.writeFileSync(path.join(ARTIFACT_DIR, "warehouse-w7a-stock-posture-summary.json"), `${JSON.stringify(summary, null, 2)}\n`);
  } catch (error) {
    summary.status = "fail";
    summary.error = error && error.message ? error.message : String(error);
    summary.details = error && error.details ? error.details : {};
    fs.writeFileSync(path.join(ARTIFACT_DIR, "warehouse-w7a-stock-posture-summary.json"), `${JSON.stringify(summary, null, 2)}\n`);
    throw error;
  } finally {
    await browser.close();
  }
  console.log(`Warehouse W7A stock posture smoke passed. Summary: ${path.join(ARTIFACT_DIR, "warehouse-w7a-stock-posture-summary.json")}`);
})().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exit(1);
});
