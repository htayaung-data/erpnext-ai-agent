const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const EXPECT_W12C = process.env.ERPW_WAREHOUSE_W12C_EXPECT_POLISH === "1"
  || Boolean(process.env.ERPW_WAREHOUSE_W12C_ASSET_ROOT || process.env.ERPW_WAREHOUSE_W12C_ARTIFACT_DIR || process.env.ERPW_WAREHOUSE_W12C_TIMEOUT);
const TIMEOUT = Number(process.env.ERPW_WAREHOUSE_W12C_TIMEOUT || process.env.ERPW_WAREHOUSE_W5A_TIMEOUT || process.env.ERPW_WAREHOUSE_W4A_TIMEOUT || 60000);
const SMOKE_LABEL = EXPECT_W12C ? "w12c-outbound-polish" : "w5a-outbound";
const SUMMARY_FILE = EXPECT_W12C ? "warehouse-w12c-outbound-polish-summary.json" : "warehouse-w5a-outbound-summary.json";
const ARTIFACT_DIR = process.env.ERPW_WAREHOUSE_W12C_ARTIFACT_DIR || process.env.ERPW_WAREHOUSE_W5A_ARTIFACT_DIR || path.join(
  fs.existsSync("/freeze-artifacts") ? "/freeze-artifacts" : path.join(__dirname, "artifacts"),
  `warehouse-${SMOKE_LABEL}-${new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z")}`
);
const ASSET_ROOT = process.env.ERPW_WAREHOUSE_W12C_ASSET_ROOT || process.env.ERPW_WAREHOUSE_W5A_ASSET_ROOT || "";
const WARM_TARGET_MS = Number(process.env.ERPW_WAREHOUSE_W12C_WARM_TARGET_MS || process.env.ERPW_WAREHOUSE_W5A_WARM_TARGET_MS || 3000);

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

const VIEWPORTS = [
  { key: "laptop-1136", width: 1136, height: 768 },
  { key: "laptop-1240", width: 1240, height: 768 },
  { key: "desktop-1440", width: 1440, height: 900 },
];
const ACTIVE_VIEWPORTS = EXPECT_W12C
  ? [...VIEWPORTS, { key: "mobile-390", width: 390, height: 844 }]
  : VIEWPORTS;

const FORBIDDEN_ACTION_RE = /\b(Receive|Ship|Dispatch|Post|Submit|Cancel|Amend|Reconcile|Stock Entry|Purchase Receipt|Delivery Note|Stock Reconciliation|Pick List|Reserve|Unreserve|Assign Serial|Assign Batch|Item Price|Default Supplier|Item Supplier)\b/i;
const FORBIDDEN_COPY_RE = /\b(Productized|native ERP|governed|deferred|route only|mutation|backend|frontend|framework|Frappe|smoke|test|Quick Find|\bSearch\b)\b/i;
const NATIVE_ROUTE_RE = /\/desk\/Form\/|\/app\/|#Form\/|query-report|\/desk\/List\//i;
const VALUATION_RE = /stock value|valuation rate|stock_value|valuation_rate|base_net_rate|amount/i;

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

function bounded(value, length = 700) {
  const text = String(value || "");
  return text.length > length ? `${text.slice(0, length)}...` : text;
}

function remember(list, item, limit = 80) {
  list.push(item);
  if (list.length > limit) list.shift();
}

function makeDiagnostics(label) {
  return { label, consoleErrors: [], pageErrors: [], failedResponses: [], failedRequests: [], overrideHits: [], snapshots: [] };
}

function attachDiagnostics(page, diagnostics) {
  page.on("console", (message) => {
    if (!["error", "warning"].includes(message.type())) return;
    remember(diagnostics.consoleErrors, { type: message.type(), text: bounded(message.text(), 900), location: message.location() });
  });
  page.on("pageerror", (error) => {
    remember(diagnostics.pageErrors, { message: bounded(error && error.message ? error.message : String(error), 900), stack: bounded(error && error.stack ? error.stack : "", 1200) });
  });
  page.on("requestfailed", (request) => {
    remember(diagnostics.failedRequests, { url: bounded(request.url()), method: request.method(), failure: request.failure() });
  });
  page.on("response", (response) => {
    if (response.ok()) return;
    const url = response.url();
    if (!/warehouse|desk_page|getpage|assets\/erp_workspace_ui|api\/method/i.test(url)) return;
    remember(diagnostics.failedResponses, { url: bounded(url), status: response.status(), statusText: response.statusText() });
  });
}

function requestText(request) {
  let jsonText = "";
  try {
    jsonText = JSON.stringify(request.postDataJSON() || {});
  } catch (error) {
    jsonText = "";
  }
  return `${request.url()} ${request.postData() || ""} ${jsonText}`;
}

function recordOverrideHit(diagnostics, key, request, extra = {}) {
  remember(diagnostics.overrideHits, { key, url: bounded(request.url()), method: request.method(), postData: bounded(request.postData() || "", 500), ...extra }, 120);
}

function sourceSidebarPayload(allowed = true) {
  const items = allowed ? [
    { key: "warehouse_console_home", label: "Overview", icon: "item", target: { kind: "page", route: "warehouse-console" } },
    { key: "inbound_receiving", label: "Inbound Receiving", icon: "quotation", target: { kind: "worklist", queue_key: "inbound_receiving" } },
    { key: "outbound_picking", label: "Outbound Picking", icon: "order", target: { kind: "worklist", queue_key: "outbound_picking" } },
  ] : [];
  return {
    workspace: {
      workspace_id: "warehouse",
      status: "w5a_outbound_picking",
      title: "Warehouse Console",
      mode_label: "Warehouse Workspace",
      routes: {
        home: "warehouse-console",
        home_path: "/desk/warehouse-console",
        worklist: "warehouse-console-worklist",
        worklist_path: "/desk/warehouse-console-worklist",
        receiving: "warehouse-console-receiving",
        receiving_path: "/desk/warehouse-console-receiving",
        picking: "warehouse-console-picking",
        picking_path: "/desk/warehouse-console-picking",
      },
      search: { enabled: false },
    },
    context: { has_warehouse_access: allowed, role_family: "Warehouse", role_variant: "warehouse_manager", can_view_valuation: false },
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
    fetched_at: "2026-05-28 00:00:00",
  };
}

function sourceOutboundRows() {
  return [
    {
      key: "SO-OVERDUE",
      name: "SO-OVERDUE",
      sales_order: "SO-OVERDUE",
      primary_id: "SO-OVERDUE",
      customer: "Apex Retail",
      partner: "Apex Retail",
      required_date: "2026-05-24",
      target_warehouse: "Stores - M",
      line_count: 1,
      item_count: 1,
      delivered_percent: "0%",
      remaining_summary: "4 Nos remaining",
      status: "To Deliver",
      state_key: "overdue",
      state_label: "Overdue",
      age_label: "Overdue 4d",
      lines: [{ item_code: "ITEM-101", item_name: "Phone Case", remaining_qty: "4", uom: "Nos", target_warehouse: "Stores - M", required_date: "2026-05-24" }],
    },
    {
      key: "SO-TODAY",
      name: "SO-TODAY",
      sales_order: "SO-TODAY",
      primary_id: "SO-TODAY",
      customer: "Today Retail",
      partner: "Today Retail",
      required_date: "2026-05-28",
      target_warehouse: "Main - M",
      line_count: 1,
      item_count: 1,
      delivered_percent: "0%",
      remaining_summary: "6 Nos remaining",
      status: "To Deliver and Bill",
      state_key: "due_today",
      state_label: "Due Today",
      age_label: "Due today",
      lines: [{ item_code: "ITEM-102", item_name: "Screen Guard", remaining_qty: "6", uom: "Nos", target_warehouse: "Main - M", required_date: "2026-05-28" }],
    },
    {
      key: "SO-READY",
      name: "SO-READY",
      sales_order: "SO-READY",
      primary_id: "SO-READY",
      customer: "Ready Customer",
      partner: "Ready Customer",
      required_date: "2026-06-01",
      target_warehouse: "Main - M",
      line_count: 1,
      item_count: 1,
      delivered_percent: "0%",
      remaining_summary: "5 Nos remaining",
      status: "To Deliver",
      state_key: "ready_to_pick",
      state_label: "Ready to Pick",
      age_label: "Due 2026-06-01",
      lines: [{ item_code: "ITEM-103", item_name: "Bluetooth Speaker", remaining_qty: "5", uom: "Nos", target_warehouse: "Main - M", required_date: "2026-06-01" }],
    },
    {
      key: "SO-PARTIAL",
      name: "SO-PARTIAL",
      sales_order: "SO-PARTIAL",
      primary_id: "SO-PARTIAL",
      customer: "Partial Customer",
      partner: "Partial Customer",
      required_date: "2026-06-02",
      target_warehouse: "Main - M",
      line_count: 1,
      item_count: 1,
      delivered_percent: "45%",
      remaining_summary: "6 Nos remaining",
      status: "To Deliver",
      state_key: "partially_picked",
      state_label: "Partially Picked",
      age_label: "Due 2026-06-02",
      lines: [{ item_code: "ITEM-104", item_name: "Cable Pack", remaining_qty: "6", uom: "Nos", target_warehouse: "Main - M", required_date: "2026-06-02" }],
    },
    {
      key: "SO-REVIEW",
      name: "SO-REVIEW",
      sales_order: "SO-REVIEW",
      primary_id: "SO-REVIEW",
      customer: "Review Customer",
      partner: "Review Customer",
      required_date: "2026-06-03",
      target_warehouse: "Short - M",
      line_count: 1,
      item_count: 1,
      delivered_percent: "0%",
      remaining_summary: "8 Nos remaining",
      status: "To Deliver",
      state_key: "needs_stock_review",
      state_label: "Needs Stock Review",
      age_label: "Due 2026-06-03",
      lines: [{ item_code: "ITEM-105", item_name: "Power Bank", remaining_qty: "8", uom: "Nos", target_warehouse: "Short - M", required_date: "2026-06-03" }],
    },
  ];
}

function outboundGroups(rows) {
  const groupSpecs = [
    ["overdue", "Overdue", "Past delivery date."],
    ["due_today", "Due Today", "Required today."],
    ["ready_to_pick", "Ready to Pick", "Visible stock posture looks ready."],
    ["partially_picked", "Partially Picked", "Some quantity has already moved."],
    ["needs_stock_review", "Needs Stock Review", "Stock posture needs warehouse review."],
    ["expected_soon", "Expected Soon", "Due in the next 14 days."],
  ];
  const groups = groupSpecs.map(([key, title, summary]) => ({ key, title, summary, rows: rows.filter((row) => row.state_key === key) }));
  const counts = Object.fromEntries(groupSpecs.map(([key]) => [key, groups.find((group) => group.key === key).rows.length]));
  return { groups, counts };
}

function sourceOutboundPayload(filters = {}) {
  const rows = sourceOutboundRows().filter((row) => {
    if (filters.state && row.state_key !== filters.state) return false;
    if (filters.customer && !row.customer.toLowerCase().includes(String(filters.customer).toLowerCase())) return false;
    if (filters.sales_order && !row.sales_order.toLowerCase().includes(String(filters.sales_order).toLowerCase())) return false;
    if (filters.warehouse && !row.target_warehouse.toLowerCase().includes(String(filters.warehouse).toLowerCase())) return false;
    return true;
  });
  const { groups, counts } = outboundGroups(rows);
  const cards = [
    ["due_today", "Picking Due Today", "Required today."],
    ["overdue", "Overdue Picking", "Past delivery date."],
    ["ready_to_pick", "Ready to Pick", "Visible stock posture looks ready."],
    ["needs_stock_review", "Needs Stock Review", "Stock posture needs warehouse review."],
  ].map(([key, title, note]) => ({ key, label: title, title, value: counts[key], state: "live", note, empty_message: "No outbound picking needs attention." }));
  return {
    workspace: sourceSidebarPayload(true).workspace,
    context: { has_warehouse_access: true, role_family: "Warehouse", role_variant: "warehouse_manager", can_view_valuation: false },
    state: rows.length
      ? { kind: "ready", title: "Warehouse Console ready", detail: "Stock visibility and warehouse posture are available for review." }
      : { kind: "empty", title: "No outbound picking needs attention", detail: "No outbound picking needs attention." },
    page: { title: "Outbound Picking", key: "outbound_picking" },
    summary: {
      title: "Outbound Picking",
      subtitle: "Pending customer demand waiting for warehouse review.",
      chips: [{ label: "Read-only" }, { label: `${rows.length} shown` }],
    },
    controls: {
      fields: [
        { key: "sales_order", label: "Sales Order", type: "text", value: filters.sales_order || "", placeholder: "Filter order" },
        { key: "customer", label: "Customer", type: "text", value: filters.customer || "", placeholder: "Filter customer" },
        { key: "warehouse", label: "Warehouse", type: "text", value: filters.warehouse || "", placeholder: "Filter warehouse" },
        {
          key: "state",
          label: "Picking State",
          type: "select",
          value: filters.state || "",
          options: [
            { label: "All", value: "" },
            { label: "Overdue", value: "overdue" },
            { label: "Due Today", value: "due_today" },
            { label: "Ready to Pick", value: "ready_to_pick" },
            { label: "Partially Picked", value: "partially_picked" },
            { label: "Needs Stock Review", value: "needs_stock_review" },
            { label: "Expected Soon", value: "expected_soon" },
          ],
        },
      ],
      actions: [
        { key: "refresh", label: "Refresh" },
        { key: "reset_filters", label: "Reset" },
        { key: "apply_filters", label: "Apply", kind: "primary" },
      ],
      scopeChips: ["Sales Orders", "Read-only outbound"],
    },
    cards,
    groups,
    rows,
    action_targets: {},
    valuation: { visible: false, fields: [] },
    fetched_at: "2026-05-28 00:00:00",
  };
}

function sourcePickingPayload(order = "SO-REVIEW") {
  const row = sourceOutboundRows().find((item) => item.sales_order === order) || sourceOutboundRows()[0];
  return {
    workspace: sourceSidebarPayload(true).workspace,
    context: { has_warehouse_access: true, role_family: "Warehouse", role_variant: "warehouse_manager", can_view_valuation: false },
    state: { kind: "ready", title: "Warehouse Console ready", detail: "Stock visibility and warehouse posture are available for review." },
    page: { title: "Picking Review", key: "picking_review", sales_order: row.sales_order },
    header: {
      sales_order: row.sales_order,
      customer: row.customer,
      required_date: row.required_date,
      target_warehouse: row.target_warehouse,
      state_key: row.state_key,
      state_label: row.state_label,
      age_label: row.age_label,
      delivered_percent: row.delivered_percent,
      remaining_summary: row.remaining_summary,
      line_count: row.line_count,
      item_count: row.item_count,
      ready_line_count: row.state_key === "ready_to_pick" ? 1 : 0,
      review_line_count: row.state_key === "needs_stock_review" ? 1 : 0,
      status: row.status,
    },
    summary_cards: [
      { key: "state", label: "Picking State", value: row.state_label, note: row.age_label },
      { key: "delivered", label: "Delivered", value: row.delivered_percent, note: "Quantity already delivered." },
      { key: "open_lines", label: "Open Lines", value: row.line_count, note: row.remaining_summary },
      { key: "readiness", label: "Readiness", value: row.state_key === "ready_to_pick" ? 1 : 0, note: row.state_key === "needs_stock_review" ? "1 lines need review" : "0 lines need review" },
    ],
    tabs: [
      { key: "item_lines", label: "Item Lines", count: row.lines.length },
      { key: "stock_readiness", label: "Stock Readiness", count: row.lines.length },
    ],
    lines: row.lines.map((line) => ({
      item_code: line.item_code,
      item_name: line.item_name,
      ordered_qty: row.state_key === "ready_to_pick" ? "5" : "8",
      delivered_qty: "0",
      pending_qty: line.remaining_qty,
      uom: line.uom,
      source_warehouse: line.target_warehouse,
      required_date: line.required_date,
      readiness: row.state_key === "ready_to_pick" ? "Ready" : "Needs Stock Review",
      availability: row.state_key === "ready_to_pick" ? "12 available" : "2 available",
    })),
    allowed_actions: [
      { key: "refresh", label: "Refresh", kind: "read_only" },
      { key: "back_to_outbound", label: "Back to outbound picking", kind: "navigation" },
    ],
    action_targets: { outbound_queue: { route: "warehouse-console-worklist", queue_key: "outbound_picking" } },
    valuation: { visible: false, fields: [] },
    fetched_at: "2026-05-28 00:00:00",
  };
}

function sourceInboundPayload() {
  return {
    state: { kind: "ready", title: "Warehouse Console ready", detail: "Stock visibility and warehouse posture are available for review." },
    counts: { overdue: 1, due_today: 1, partially_received: 1, expected_soon: 1 },
    cards: [
      { key: "due_today", label: "Receiving Due Today", title: "Receiving Due Today", value: 1, state: "live", note: "Expected today.", empty_message: "No inbound receiving needs attention." },
      { key: "overdue", label: "Overdue Receiving", title: "Overdue Receiving", value: 1, state: "live", note: "Past required date.", empty_message: "No inbound receiving needs attention." },
      { key: "partially_received", label: "Partially Received", title: "Partially Received", value: 1, state: "live", note: "Some quantity has arrived.", empty_message: "No inbound receiving needs attention." },
      { key: "expected_soon", label: "Expected Soon", title: "Expected Soon", value: 1, state: "live", note: "Due in the next 14 days.", empty_message: "No inbound receiving needs attention." },
    ],
    preview_rows: [
      { key: "PO-OVERDUE", purchase_order: "PO-OVERDUE", supplier: "Acme Supply", required_date: "2026-05-24", target_warehouse: "Stores - M", remaining_summary: "16 Nos remaining", state_label: "Overdue", age_label: "Overdue 4d" },
    ],
    groups: [],
    total_count: 4,
    queue_key: "inbound_receiving",
    queue_route: "warehouse-console-worklist",
    row_limit: 50,
    horizon_days: 14,
  };
}

function sourceOverviewPayload() {
  const outbound = sourceOutboundPayload();
  const inbound = sourceInboundPayload();
  return {
    workspace: sourceSidebarPayload(true).workspace,
    context: { has_warehouse_access: true, role_family: "Warehouse", role_variant: "warehouse_manager", can_view_valuation: false },
    state: { kind: "ready", title: "Warehouse Console ready", detail: "Stock visibility and warehouse posture are available for review." },
    navigation: { items: sourceSidebarPayload(true).sidebar.items },
    sidebar: sourceSidebarPayload(true).sidebar,
    kpis: [
      { key: "active_warehouses", label: "Active Warehouses", value: 4, state: "live", note: "Warehouse locations available for stock review." },
      { key: "stocked_items", label: "Stocked Items", value: 18, state: "live", note: "Item and warehouse positions with stock on hand." },
      { key: "low_stock", label: "Low Stock", value: 2, state: "live", note: "Projected quantity below zero." },
      { key: "receiving_due", label: "Receiving Due", value: 1, state: "live", note: "Submitted purchase orders due for review." },
      { key: "outbound_due", label: "Picking Due", value: 1, state: "live", note: "Submitted sales orders due for warehouse picking review." },
      { key: "transfer_requests", label: "Transfer Requests", value: 2, state: "live", note: "Internal warehouse requests waiting for review." },
    ],
    inbound,
    outbound: {
      state: outbound.state,
      counts: outboundGroups(sourceOutboundRows()).counts,
      cards: outbound.cards,
      preview_rows: sourceOutboundRows().slice(0, 5),
      groups: outbound.groups,
      total_count: 5,
      queue_key: "outbound_picking",
      queue_route: "warehouse-console-worklist",
      row_limit: 50,
      horizon_days: 14,
    },
    sections: [
      { key: "needs_attention", title: "Needs Attention", summary: "Warehouse work that may need review today.", cards: [
        { key: "low_stock", title: "Low Stock", value: 2, state: "live", note: "Projected quantity below zero." },
        { key: "overdue", title: "Overdue Receiving", value: 1, state: "live", note: "Past required date." },
        { key: "overdue", title: "Overdue Picking", value: 1, state: "live", note: "Past delivery date." },
      ] },
      { key: "inbound_work", title: "Inbound Work", summary: "Expected supplier stock due into warehouse.", cards: inbound.cards },
      { key: "outbound_work", title: "Outbound Work", summary: "Picking posture visible to Warehouse roles.", cards: outbound.cards },
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
    fetched_at: "2026-05-28 00:00:00",
  };
}

async function installSourceOverrides(context, diagnostics) {
  if (!ASSET_ROOT) return;
  const assetMappings = [
    { key: "warehouse-page-asset", pattern: /\/assets\/erp_workspace_ui\/js\/warehouse_console\/warehouse_console_page\.js(?:\?|$)/, file: "erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js", contentType: "application/javascript" },
    { key: "workspace-registry-asset", pattern: /\/assets\/erp_workspace_ui\/js\/runtime\/console\/workspace_registry\.js(?:\?|$)/, file: "erp_workspace_ui/public/js/runtime/console/workspace_registry.js", contentType: "application/javascript" },
    { key: "workspace-sidebar-asset", pattern: /\/assets\/erp_workspace_ui\/js\/runtime\/console\/workspace_console_sidebar\.js(?:\?|$)/, file: "erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js", contentType: "application/javascript" },
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
    const text = requestText(request);
    if (!/warehouse-console/i.test(text)) return route.continue();
    const isPicking = /warehouse-console-picking/i.test(text);
    const isWorklist = /warehouse-console-worklist/i.test(text);
    const file = isPicking
      ? "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_picking/warehouse_console_picking.js"
      : isWorklist
      ? "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/warehouse_console_worklist.js"
      : "erp_workspace_ui/erp_workspace_ui/page/warehouse_console/warehouse_console.js";
    const name = isPicking ? "warehouse-console-picking" : isWorklist ? "warehouse-console-worklist" : "warehouse-console";
    const script = readSource(file);
    recordOverrideHit(diagnostics, "desk-page-getpage", request, { fulfilled: Boolean(script), page: name });
    const pageDoc = { doctype: "Page", name, page_name: name, title: isPicking ? "Picking Review" : isWorklist ? "Outbound Picking" : "Warehouse Console", module: "ERP Workspace UI", standard: "Yes", content: "", script };
    return route.fulfill({ status: script ? 200 : 404, contentType: "application/json", body: JSON.stringify({ docs: [pageDoc], message: pageDoc }) });
  });
  await context.route("**/api/method/erp_workspace_ui.warehouse_console.service.get_warehouse_console_overview**", async (route) => {
    recordOverrideHit(diagnostics, "warehouse-overview", route.request(), { fulfilled: true });
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ message: sourceOverviewPayload() }) });
  });
  await context.route("**/api/method/erp_workspace_ui.warehouse_console.service.get_warehouse_outbound_picking_queue**", async (route) => {
    let filters = {};
    try {
      const body = route.request().postDataJSON() || {};
      const raw = body.filters;
      filters = typeof raw === "string" ? JSON.parse(raw || "{}") : (raw || {});
    } catch (error) {
      filters = {};
    }
    recordOverrideHit(diagnostics, "warehouse-outbound-queue", route.request(), { fulfilled: true, filters });
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ message: sourceOutboundPayload(filters) }) });
  });
  await context.route("**/api/method/erp_workspace_ui.warehouse_console.service.get_warehouse_picking_review**", async (route) => {
    let salesOrder = "SO-REVIEW";
    try {
      const body = route.request().postDataJSON() || {};
      salesOrder = body.sales_order || salesOrder;
    } catch (error) {
      salesOrder = "SO-REVIEW";
    }
    recordOverrideHit(diagnostics, "warehouse-picking-detail", route.request(), { fulfilled: true, salesOrder });
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ message: sourcePickingPayload(salesOrder) }) });
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

async function gotoDeskAndWait(page) {
  await page.goto(routeUrl("/desk"), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  await page.waitForURL((url) => url.pathname === "/desk/warehouse-console" || url.pathname === "/app/warehouse-console", { timeout: TIMEOUT });
}

async function diagnosticSnapshot(page, diagnostics, label) {
  const screenshot = await capture(page, `${safeName(label)}-diagnostic`).catch(() => "");
  const snapshot = await page.evaluate(() => {
    const shell = document.querySelector('.sales-console-shell[data-erpw-workspace="warehouse"]');
    return {
      url: location.href,
      route: window.frappe && typeof frappe.get_route === "function" ? frappe.get_route() : null,
      shellView: shell ? shell.getAttribute("data-warehouse-view") || "" : "",
      shellText: shell ? String(shell.innerText || "").replace(/\s+/g, " ").trim().slice(0, 1600) : "",
      kpiCount: document.querySelectorAll(".warehouse-console-kpi-card").length,
      outboundCardCount: document.querySelectorAll("[data-warehouse-outbound-card]").length,
      outboundPreviewCount: document.querySelectorAll("[data-warehouse-outbound-preview-row]").length,
      outboundShellCount: document.querySelectorAll('.warehouse-outbound-shell[data-warehouse-view="outbound-picking"]').length,
      queueCardCount: document.querySelectorAll("[data-warehouse-outbound-queue-card]").length,
      filterCount: document.querySelectorAll("[data-warehouse-filter-key]").length,
      groupCount: document.querySelectorAll("[data-warehouse-outbound-group]").length,
      rowCount: document.querySelectorAll("[data-warehouse-outbound-row]").length,
      emptyCount: document.querySelectorAll("[data-warehouse-outbound-empty]").length,
      diagnostics: window.erpWorkspaceWarehouseConsole && window.erpWorkspaceWarehouseConsole.diagnostics
        ? { ...window.erpWorkspaceWarehouseConsole.diagnostics }
        : {},
      hasWorklistRenderer: Boolean(window.erpWorkspaceWarehouseConsole && typeof window.erpWorkspaceWarehouseConsole.renderWarehouseWorklist === "function"),
      hasOutboundRenderer: Boolean(window.erpWorkspaceWarehouseConsole && typeof window.erpWorkspaceWarehouseConsole.renderOutboundQueue === "function"),
    };
  }).catch((error) => ({ error: error && error.message ? error.message : String(error) }));
  snapshot.screenshot = screenshot;
  remember(diagnostics.snapshots, { label, ...snapshot }, 20);
  return snapshot;
}

async function waitForWarehouseOverviewReady(page, diagnostics, label) {
  try {
    await page.waitForFunction(() => {
      const shell = document.querySelector('.sales-console-shell[data-erpw-workspace="warehouse"]');
      if (!shell || shell.classList.contains("warehouse-inbound-shell")) return false;
      const ready = shell.getAttribute("data-erpw-console-bootstrap") === "ready" || shell.getAttribute("data-erpw-console-runtime") === "ready";
      return ready
        && document.querySelectorAll(".warehouse-console-kpi-card").length >= 6
        && document.querySelectorAll("[data-warehouse-outbound-card]").length >= 4
        && (document.querySelectorAll("[data-warehouse-outbound-preview-row]").length >= 1 || !ASSET_ROOT);
    }, null, { timeout: TIMEOUT });
  } catch (error) {
    error.details = { ...(error.details || {}), snapshot: await diagnosticSnapshot(page, diagnostics, `${label}-overview-timeout`) };
    throw error;
  }
}

async function waitForWarehouseOutboundReady(page, diagnostics, label) {
  try {
    await page.waitForFunction((expectRows) => {
      const shell = document.querySelector('.warehouse-outbound-shell[data-erpw-workspace="warehouse"][data-warehouse-view="outbound-picking"]');
      if (!shell) return false;
      const ready = shell.getAttribute("data-erpw-console-runtime") === "ready";
      const hasCards = shell.querySelectorAll("[data-warehouse-outbound-queue-card]").length >= 4;
      const hasFilters = shell.querySelectorAll("[data-warehouse-filter-key]").length >= 4;
      const hasGroups = shell.querySelectorAll("[data-warehouse-outbound-group]").length >= 6;
      const hasRowsOrEmpty = shell.querySelectorAll("[data-warehouse-outbound-row]").length >= (expectRows ? 1 : 0) || shell.querySelector("[data-warehouse-outbound-empty]");
      const expectW12C = Boolean(window.__erpwWarehouseExpectW12C);
      const hasPolish = !expectW12C || (
        shell.querySelectorAll("[data-warehouse-outbound-command-chip]").length >= 3
        && shell.querySelector("[data-warehouse-outbound-guardrail]")
        && shell.querySelectorAll("[data-warehouse-outbound-row-fact]").length >= (expectRows ? 4 : 0)
      );
      return ready && hasCards && hasFilters && hasGroups && hasRowsOrEmpty && hasPolish;
    }, Boolean(ASSET_ROOT), { timeout: TIMEOUT });
  } catch (error) {
    error.details = { ...(error.details || {}), snapshot: await diagnosticSnapshot(page, diagnostics, `${label}-outbound-timeout`) };
    throw error;
  }
}

async function waitForWarehousePickingReady(page, diagnostics, label) {
  try {
    await page.waitForFunction(() => {
      const shell = document.querySelector('.warehouse-picking-shell[data-erpw-workspace="warehouse"][data-warehouse-view="picking-review"]');
      return Boolean(shell
        && shell.getAttribute("data-erpw-console-runtime") === "ready"
        && shell.querySelectorAll("[data-warehouse-picking-card]").length >= 4
        && shell.querySelectorAll("[data-warehouse-picking-line]").length >= 1);
    }, null, { timeout: TIMEOUT });
  } catch (error) {
    error.details = { ...(error.details || {}), snapshot: await diagnosticSnapshot(page, diagnostics, `${label}-picking-timeout`) };
    throw error;
  }
}

async function waitForOverrideHit(page, diagnostics, key, label) {
  const started = Date.now();
  while (Date.now() - started < TIMEOUT) {
    if (diagnostics.overrideHits.some((hit) => hit.key === key)) return;
    await page.waitForTimeout(100);
  }
  const snapshot = await diagnosticSnapshot(page, diagnostics, `${label}-${key}-timeout`);
  const error = new Error(`Expected source override was not used: ${key}`);
  error.details = { diagnostics, snapshot };
  throw error;
}

async function openOutboundRoute(page, diagnostics, label) {
  const canRoute = await page.evaluate(() => Boolean(window.frappe && typeof frappe.set_route === "function")).catch(() => false);
  if (canRoute) {
    await page.evaluate(() => frappe.set_route("warehouse-console-worklist", "outbound-picking"));
    await page.waitForURL((url) => url.pathname === "/desk/warehouse-console-worklist/outbound-picking" || url.pathname === "/app/warehouse-console-worklist/outbound-picking", { timeout: TIMEOUT });
  } else {
    await page.goto(routeUrl("/desk/warehouse-console-worklist/outbound-picking"), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  }
  if (ASSET_ROOT) await waitForOverrideHit(page, diagnostics, "warehouse-outbound-queue", label);
  await waitForWarehouseOutboundReady(page, diagnostics, label);
}

async function collapseBodySidebarForNarrowViewport(page) {
  const viewport = page.viewportSize();
  if (!viewport || viewport.width > 520) return;
  await page.evaluate(() => {
    const sidebar = document.querySelector(".body-sidebar-container.expanded");
    if (!sidebar) return;
    const controls = Array.from(sidebar.querySelectorAll("button, a, [role='button'], [tabindex]"));
    const collapseControl = controls.find((node) => /\bCollapse\b/i.test((node.innerText || node.getAttribute("aria-label") || "").trim()));
    if (collapseControl && typeof collapseControl.click === "function") {
      collapseControl.click();
    }
  });
  await page.waitForTimeout(250);
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
    return {
      url: location.href,
      route: window.frappe && typeof frappe.get_route === "function" ? frappe.get_route() : null,
      text,
      actionText,
      hrefs,
      shellCount: Array.from(document.querySelectorAll('.sales-console-shell[data-erpw-workspace="warehouse"]')).filter(visible).length,
      headerCount: Array.from(document.querySelectorAll(".warehouse-console-header, .warehouse-inbound-queue-header, .warehouse-receiving-header")).filter(visible).length,
      sidebarCount: Array.from(document.querySelectorAll(".erpw-sales-console-sidebar")).filter(visible).length,
      kpiCount: Array.from(document.querySelectorAll(".warehouse-console-kpi-card")).filter(visible).length,
      outboundCardCount: Array.from(document.querySelectorAll("[data-warehouse-outbound-card]")).filter(visible).length,
      outboundPreviewCount: Array.from(document.querySelectorAll("[data-warehouse-outbound-preview-row]")).filter(visible).length,
      queueCardCount: Array.from(document.querySelectorAll("[data-warehouse-outbound-queue-card]")).filter(visible).length,
      queueGroupCount: Array.from(document.querySelectorAll("[data-warehouse-outbound-group]")).filter(visible).length,
      queueRowCount: Array.from(document.querySelectorAll("[data-warehouse-outbound-row]")).filter(visible).length,
      queueCommandChipCount: Array.from(document.querySelectorAll("[data-warehouse-outbound-command-chip]")).filter(visible).length,
      queueGuardrailCount: Array.from(document.querySelectorAll("[data-warehouse-outbound-guardrail]")).filter(visible).length,
      queueRowFactCount: Array.from(document.querySelectorAll("[data-warehouse-outbound-row-fact]")).filter(visible).length,
      detailButtonCount: Array.from(document.querySelectorAll("[data-warehouse-row-open-detail], [data-warehouse-row-open-picking-detail]")).filter(visible).length,
      filterCount: Array.from(document.querySelectorAll("[data-warehouse-filter-key]")).filter(visible).length,
      expandedLineCount: Array.from(document.querySelectorAll(".warehouse-inbound-line")).filter(visible).length,
      searchUtilityVisible: Array.from(document.querySelectorAll("[data-erpw-sales-search-open]")).some(visible),
      pageHeadCount: Array.from(document.querySelectorAll(".page-head")).filter(visible).length,
      horizontalOverflow: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
      state: shell && shell.getAttribute ? shell.getAttribute("data-warehouse-console-state") || "" : "",
      diagnostics: window.erpWorkspaceWarehouseConsole && window.erpWorkspaceWarehouseConsole.diagnostics
        ? { ...window.erpWorkspaceWarehouseConsole.diagnostics }
        : {},
      hasWorklistRenderer: Boolean(window.erpWorkspaceWarehouseConsole && typeof window.erpWorkspaceWarehouseConsole.renderWarehouseWorklist === "function"),
      hasOutboundRenderer: Boolean(window.erpWorkspaceWarehouseConsole && typeof window.erpWorkspaceWarehouseConsole.renderOutboundQueue === "function"),
    };
  });
}

function assertCleanWarehouseUi(state, context) {
  assert(state.shellCount === 1, "Warehouse shell count must remain 1", { context, state });
  assert(state.headerCount === 1, "Warehouse header count must remain 1", { context, state });
  assert(!state.pageHeadCount || state.pageHeadCount <= 1, "Frappe page chrome must not duplicate", { context, state });
  assert(state.sidebarCount <= 1, "Warehouse sidebar count must not duplicate", { context, state });
  assert(state.horizontalOverflow <= 2, "Warehouse page has horizontal overflow", { context, state });
  assert(!state.searchUtilityVisible, "Warehouse search entry must stay inactive in W5A", { context, state });
  assert(!FORBIDDEN_ACTION_RE.test(state.actionText), "Forbidden stock or outbound action control is visible", { context, state });
  assert(!FORBIDDEN_COPY_RE.test(state.text), "Developer or governance copy is visible", { context, state });
  assert(!VALUATION_RE.test(state.text), "Valuation text is visible", { context, state });
  assert(!NATIVE_ROUTE_RE.test(`${state.hrefs} ${state.actionText}`), "Native route target is visible", { context, state });
}

async function exerciseUser(browser, user) {
  const diagnostics = makeDiagnostics(user.key);
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await installSourceOverrides(context, diagnostics);
  if (EXPECT_W12C) {
    await context.addInitScript(() => {
      window.__erpwWarehouseExpectW12C = true;
    });
  }
  const page = await context.newPage();
  attachDiagnostics(page, diagnostics);
  const routeCalls = [];
  page.on("request", (request) => {
    const match = request.url().match(/\/api\/method\/([^?#]+)/);
    if (match && /warehouse_console/.test(match[1])) routeCalls.push(match[1]);
  });
  try {
    await login(page, user);
    await gotoDeskAndWait(page);
    await waitForWarehouseOverviewReady(page, diagnostics, `${user.key}:desk-landing`);
    let state = await snapshot(page);
    assertCleanWarehouseUi(state, `${user.key}:desk-landing`);
    assert(state.kpiCount >= 6, "Overview KPI cards did not render", { user: user.key, state });
    assert(state.outboundCardCount >= 4, "Overview outbound cards did not render", { user: user.key, state });
    if (ASSET_ROOT) assert(state.outboundPreviewCount >= 1, "Overview outbound preview did not render", { user: user.key, state });
    await capture(page, `${user.key}-overview-landing`);

    for (const viewport of ACTIVE_VIEWPORTS) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await collapseBodySidebarForNarrowViewport(page);
      const started = Date.now();
      await openOutboundRoute(page, diagnostics, `${user.key}:${viewport.key}:queue`);
      await collapseBodySidebarForNarrowViewport(page);
      const firstMs = Date.now() - started;
      state = await snapshot(page);
      assertCleanWarehouseUi(state, `${user.key}:${viewport.key}:queue`);
      assert(state.queueCardCount >= 4, "Outbound queue summary cards did not render", { user: user.key, viewport, state });
      assert(state.queueGroupCount >= 6, "Outbound queue groups did not render", { user: user.key, viewport, state });
      if (ASSET_ROOT) assert(state.queueRowCount >= 1, "Outbound queue rows did not render", { user: user.key, viewport, state });
      assert(state.filterCount >= 4, "Outbound filters did not render", { user: user.key, viewport, state });
      assert(state.detailButtonCount >= 1, "Outbound rows must expose picking review navigation", { user: user.key, viewport, state });
      if (EXPECT_W12C) {
        assert(state.queueCommandChipCount >= 3, "Outbound command chips did not render", { user: user.key, viewport, state });
        assert(state.queueGuardrailCount === 1, "Outbound read-only guardrail did not render exactly once", { user: user.key, viewport, state });
        if (ASSET_ROOT) assert(state.queueRowFactCount >= 4, "Outbound fact cards did not render", { user: user.key, viewport, state });
      }

      await page.locator('[data-warehouse-filter-key="customer"]').fill("Review");
      await page.locator('[data-warehouse-filter-key="state"]').selectOption("needs_stock_review");
      await page.locator("button[data-warehouse-filter-apply]").click();
      await waitForWarehouseOutboundReady(page, diagnostics, `${user.key}:${viewport.key}:apply`);
      state = await snapshot(page);
      assertCleanWarehouseUi(state, `${user.key}:${viewport.key}:apply`);
      if (ASSET_ROOT) assert(/SO-REVIEW/.test(state.text), "Outbound filter did not show expected source row", { user: user.key, viewport, state });

      await page.locator("button[data-warehouse-filter-reset]").click();
      await waitForWarehouseOutboundReady(page, diagnostics, `${user.key}:${viewport.key}:reset`);
      state = await snapshot(page);
      assertCleanWarehouseUi(state, `${user.key}:${viewport.key}:reset`);

      await page.locator("button[data-warehouse-filter-refresh]").click();
      await waitForWarehouseOutboundReady(page, diagnostics, `${user.key}:${viewport.key}:refresh`);
      state = await snapshot(page);
      assertCleanWarehouseUi(state, `${user.key}:${viewport.key}:refresh`);

      if (state.queueRowCount > 0) {
        await page.locator("button[data-warehouse-row-toggle]").first().click();
        state = await snapshot(page);
        assert(state.expandedLineCount >= 1, "Outbound row lines did not expand inline", { user: user.key, viewport, state });
        assertCleanWarehouseUi(state, `${user.key}:${viewport.key}:expand`);
      }
      if (EXPECT_W12C && viewport.key === "desktop-1440" && state.detailButtonCount > 0) {
        await page.locator("button[data-warehouse-row-open-picking-detail]").first().click();
        await page.waitForURL((url) => /\/(?:desk|app)\/warehouse-console-picking\//.test(url.pathname), { timeout: TIMEOUT });
        if (ASSET_ROOT) await waitForOverrideHit(page, diagnostics, "warehouse-picking-detail", `${user.key}:${viewport.key}:drilldown`);
        await waitForWarehousePickingReady(page, diagnostics, `${user.key}:${viewport.key}:drilldown`);
        state = await snapshot(page);
        assertCleanWarehouseUi(state, `${user.key}:${viewport.key}:drilldown`);
        assert(/\/(?:desk|app)\/warehouse-console-picking\//.test(new URL(state.url).pathname), "Outbound drilldown did not use custom picking review route", { user: user.key, viewport, state });
        assert(!NATIVE_ROUTE_RE.test(`${state.hrefs} ${state.actionText}`), "Outbound drilldown exposed a native route target", { user: user.key, viewport, state });
        await capture(page, `${user.key}-${viewport.key}-outbound-drilldown-target`);
        await openOutboundRoute(page, diagnostics, `${user.key}:${viewport.key}:return-after-drilldown`);
        state = await snapshot(page);
        assertCleanWarehouseUi(state, `${user.key}:${viewport.key}:return-after-drilldown`);
      }
      await capture(page, `${user.key}-${viewport.key}-outbound-queue`);

      const warmStarted = Date.now();
      await openOutboundRoute(page, diagnostics, `${user.key}:${viewport.key}:warm`);
      const warmMs = Date.now() - warmStarted;
      assert(warmMs < WARM_TARGET_MS, "Warehouse outbound warm route exceeded target", { user: user.key, viewport, warmMs, firstMs });
    }

    state = await snapshot(page);
    assert(state.hasWorklistRenderer, "Warehouse generic worklist renderer is missing", { user: user.key, state, diagnostics });
    assert(state.hasOutboundRenderer, "Warehouse exported outbound renderer is missing", { user: user.key, state, diagnostics });
    assert((state.diagnostics || {}).renderOutboundQueueEntered >= 1, "Warehouse outbound renderer was not entered", { user: user.key, state, diagnostics });
    assert((state.diagnostics || {}).outboundQueueServiceCallAttempted >= 1, "Warehouse outbound queue service call was not attempted", { user: user.key, state, diagnostics });
    if (ASSET_ROOT) {
      assert(diagnostics.overrideHits.some((hit) => hit.key === "desk-page-getpage" && hit.page === "warehouse-console-worklist"), "Warehouse worklist getpage source override was not used", { user: user.key, diagnostics });
      assert(diagnostics.overrideHits.some((hit) => hit.key === "warehouse-page-asset"), "Warehouse page asset source override was not used", { user: user.key, diagnostics });
      assert(diagnostics.overrideHits.some((hit) => hit.key === "warehouse-outbound-queue"), "Warehouse outbound queue source override was not used", { user: user.key, diagnostics });
      if (EXPECT_W12C) {
        assert(diagnostics.overrideHits.some((hit) => hit.key === "desk-page-getpage" && hit.page === "warehouse-console-picking"), "Warehouse picking getpage source override was not used", { user: user.key, diagnostics });
        assert(diagnostics.overrideHits.some((hit) => hit.key === "warehouse-picking-detail"), "Warehouse picking detail source override was not used", { user: user.key, diagnostics });
      }
    }
    assert(!diagnostics.consoleErrors.some((entry) => entry.type === "error"), "Warehouse W5A smoke recorded console errors", { user: user.key, diagnostics });
    assert(diagnostics.pageErrors.length === 0, "Warehouse W5A smoke recorded page errors", { user: user.key, diagnostics });
    assert(diagnostics.failedResponses.length === 0, "Warehouse W5A smoke recorded failed responses", { user: user.key, diagnostics });
    await context.close();
    return { user: user.key, routeCalls, diagnostics };
  } catch (error) {
    await capture(page, `${user.key}-failure`).catch(() => "");
    error.details = { ...(error.details || {}), diagnostics };
    await context.close().catch(() => {});
    throw error;
  }
}

(async () => {
  assert(AUTHORIZED_USERS.length > 0, "No Warehouse W5A smoke credentials were provided. Set ERPW_WAREHOUSE_MANAGER_USERNAME/PASSWORD or ERPW_WAREHOUSE_USER_USERNAME/PASSWORD.");
  const browser = await chromium.launch({ headless: process.env.ERPW_HEADLESS !== "0" });
  const summary = {
    status: "pass",
    phase: EXPECT_W12C ? "W12C" : "W5A",
    artifactDir: ARTIFACT_DIR,
    sourceOverride: Boolean(ASSET_ROOT),
    authorizedUsers: AUTHORIZED_USERS.map((user) => user.key),
    authorized: [],
  };
  try {
    for (const user of AUTHORIZED_USERS) {
      summary.authorized.push(await exerciseUser(browser, user));
    }
    fs.writeFileSync(path.join(ARTIFACT_DIR, SUMMARY_FILE), `${JSON.stringify(summary, null, 2)}\n`);
  } catch (error) {
    summary.status = "fail";
    summary.error = error && error.message ? error.message : String(error);
    summary.details = error && error.details ? error.details : {};
    fs.writeFileSync(path.join(ARTIFACT_DIR, SUMMARY_FILE), `${JSON.stringify(summary, null, 2)}\n`);
    throw error;
  } finally {
    await browser.close();
  }
  console.log(`Warehouse ${EXPECT_W12C ? "W12C outbound polish" : "W5A outbound"} smoke passed. Summary: ${path.join(ARTIFACT_DIR, SUMMARY_FILE)}`);
})().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exit(1);
});
