const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const EXPECT_W12D = process.env.ERPW_WAREHOUSE_W12D_EXPECT_POLISH === "1"
  || Boolean(process.env.ERPW_WAREHOUSE_W12D_ASSET_ROOT || process.env.ERPW_WAREHOUSE_W12D_ARTIFACT_DIR || process.env.ERPW_WAREHOUSE_W12D_TIMEOUT);
const TIMEOUT = Number(process.env.ERPW_WAREHOUSE_W12D_TIMEOUT || process.env.ERPW_WAREHOUSE_W5B_TIMEOUT || process.env.ERPW_WAREHOUSE_W5A_TIMEOUT || 60000);
const SMOKE_LABEL = EXPECT_W12D ? "w12d-picking-review-polish" : "w5b-picking";
const SUMMARY_FILE = EXPECT_W12D ? "warehouse-w12d-picking-review-polish-summary.json" : "warehouse-w5b-picking-review-summary.json";
const ARTIFACT_DIR = process.env.ERPW_WAREHOUSE_W12D_ARTIFACT_DIR || process.env.ERPW_WAREHOUSE_W5B_ARTIFACT_DIR || path.join(
  fs.existsSync("/freeze-artifacts") ? "/freeze-artifacts" : path.join(__dirname, "artifacts"),
  `warehouse-${SMOKE_LABEL}-${new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z")}`
);
const ASSET_ROOT = process.env.ERPW_WAREHOUSE_W12D_ASSET_ROOT || process.env.ERPW_WAREHOUSE_W5B_ASSET_ROOT || process.env.ERPW_WAREHOUSE_W5A_ASSET_ROOT || "";

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
const ACTIVE_VIEWPORTS = EXPECT_W12D
  ? [...VIEWPORTS, { key: "mobile-390", width: 390, height: 844 }]
  : VIEWPORTS;

const FORBIDDEN_ACTION_RE = /\b(Receive|Ship|Dispatch|Post|Submit|Cancel|Amend|Reconcile|Stock Entry|Purchase Receipt|Delivery Note|Stock Reconciliation|Pick List|Reserve|Unreserve|Assign Serial|Assign Batch|Pack|Scan|Item Price|Default Supplier|Item Supplier)\b/i;
const FORBIDDEN_COPY_RE = /\b(Productized|native ERP|governed|deferred|route only|mutation|backend|frontend|framework|Frappe|smoke|test|Quick Find|\bSearch\b)\b/i;
const NATIVE_ROUTE_RE = /\/desk\/Form\/|\/app\/|#Form\/|query-report|\/desk\/List\//i;
const VALUATION_RE = /stock value|valuation rate|stock_value|valuation_rate|base_net_rate|amount|profit|margin|cost|gl|accounting/i;

fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
const PICKING_WORKFLOW_TASKS = new Map();

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

function remember(list, item, limit = 100) {
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
  page.on("pageerror", (error) => remember(diagnostics.pageErrors, { message: bounded(error && error.message ? error.message : String(error), 900), stack: bounded(error && error.stack ? error.stack : "", 1200) }));
  page.on("requestfailed", (request) => remember(diagnostics.failedRequests, { url: bounded(request.url()), method: request.method(), failure: request.failure() }));
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

function requestMethodArgs(request) {
  let body = {};
  try {
    body = request.postDataJSON() || {};
  } catch (error) {
    body = {};
  }
  if (body.args) {
    if (typeof body.args === "string") {
      try {
        return JSON.parse(body.args || "{}") || {};
      } catch (error) {
        return {};
      }
    }
    if (typeof body.args === "object") return body.args || {};
  }
  return body || {};
}

function recordOverrideHit(diagnostics, key, request, extra = {}) {
  remember(diagnostics.overrideHits, { key, url: bounded(request.url()), method: request.method(), postData: bounded(request.postData() || "", 500), ...extra }, 140);
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
      status: "w5b_outbound_picking_review",
      title: "Warehouse Console",
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
    fetched_at: "2026-05-29 00:00:00",
  };
}

function sourceOutboundRows() {
  return [
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
  ];
}

function sourceOutboundPayload(filters = {}) {
  const rows = sourceOutboundRows().filter((row) => {
    if (filters.state && row.state_key !== filters.state) return false;
    if (filters.customer && !row.customer.toLowerCase().includes(String(filters.customer).toLowerCase())) return false;
    if (filters.sales_order && !row.sales_order.toLowerCase().includes(String(filters.sales_order).toLowerCase())) return false;
    return true;
  });
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
  const cards = [
    ["due_today", "Picking Due Today", "Required today."],
    ["overdue", "Overdue Picking", "Past delivery date."],
    ["ready_to_pick", "Ready to Pick", "Visible stock posture looks ready."],
    ["needs_stock_review", "Needs Stock Review", "Stock posture needs warehouse review."],
  ].map(([key, title, note]) => ({ key, label: title, title, value: counts[key], state: "live", note, empty_message: "No outbound picking needs attention." }));
  return {
    workspace: sourceSidebarPayload(true).workspace,
    context: { has_warehouse_access: true, role_family: "Warehouse", role_variant: "warehouse_manager", can_view_valuation: false },
    state: rows.length ? { kind: "ready", title: "Warehouse Console ready", detail: "Stock visibility and warehouse posture are available for review." } : { kind: "empty", title: "No outbound picking needs attention", detail: "No outbound picking needs attention." },
    page: { title: "Outbound Picking", key: "outbound_picking" },
    summary: { title: "Outbound Picking", subtitle: "Pending customer demand waiting for warehouse review.", chips: [{ label: "Read-only" }, { label: `${rows.length} shown` }] },
    controls: {
      fields: [
        { key: "sales_order", label: "Sales Order", type: "text", value: filters.sales_order || "", placeholder: "Filter order" },
        { key: "customer", label: "Customer", type: "text", value: filters.customer || "", placeholder: "Filter customer" },
        { key: "warehouse", label: "Warehouse", type: "text", value: filters.warehouse || "", placeholder: "Filter warehouse" },
        { key: "state", label: "Picking State", type: "select", value: filters.state || "", options: [{ label: "All", value: "" }, { label: "Needs Stock Review", value: "needs_stock_review" }, { label: "Ready to Pick", value: "ready_to_pick" }] },
      ],
      actions: [{ key: "refresh", label: "Refresh" }, { key: "reset_filters", label: "Reset" }, { key: "apply_filters", label: "Apply", kind: "primary" }],
      scopeChips: ["Sales Orders", "Read-only outbound"],
    },
    cards,
    groups,
    rows,
    action_targets: {},
    valuation: { visible: false, fields: [] },
    fetched_at: "2026-05-29 00:00:00",
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
      line_count: 1,
      item_count: 1,
      ready_line_count: row.state_key === "ready_to_pick" ? 1 : 0,
      review_line_count: row.state_key === "needs_stock_review" ? 1 : 0,
      status: row.status,
    },
    summary_cards: [
      { key: "state", label: "Picking State", value: row.state_label, note: row.age_label },
      { key: "delivered", label: "Delivered", value: row.delivered_percent, note: "Quantity already delivered." },
      { key: "open_lines", label: "Open Lines", value: 1, note: row.remaining_summary },
      { key: "readiness", label: "Readiness", value: row.state_key === "ready_to_pick" ? 1 : 0, note: row.state_key === "needs_stock_review" ? "1 lines need review" : "0 lines need review" },
    ],
    tabs: [{ key: "item_lines", label: "Item Lines", count: 1 }, { key: "stock_readiness", label: "Stock Readiness", count: 1 }],
    workflow_task: PICKING_WORKFLOW_TASKS.get(row.sales_order) || { available: false },
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
    allowed_actions: [{ key: "refresh", label: "Refresh", kind: "read_only" }, { key: "back_to_outbound", label: "Back to outbound picking", kind: "navigation" }],
    action_targets: { outbound_queue: { route: "warehouse-console-worklist", queue_key: "outbound_picking" } },
    valuation: { visible: false, fields: [] },
    fetched_at: "2026-05-29 00:00:00",
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
  await context.route("**/api/method/erp_workspace_ui.warehouse_console.service.save_warehouse_picking_task_draft**", async (route) => {
    const body = requestMethodArgs(route.request());
    const salesOrder = body.sales_order || "SO-REVIEW";
    const sourceWarehouse = body.source_warehouse || "Short - M";
    const rawLines = typeof body.lines === "string" ? JSON.parse(body.lines || "[]") : (body.lines || []);
    const lines = Array.isArray(rawLines) ? rawLines : (Array.isArray(rawLines.lines) ? rawLines.lines : []);
    const task = {
      available: true,
      task_id: `WPT-SMOKE-${salesOrder}`,
      sales_order: salesOrder,
      source_warehouse: sourceWarehouse,
      status: "In Progress",
      decision: "",
      line_count: lines.length,
      manager_decision_available: true,
      lines: lines.map((line) => ({
        item_code: line.item_code || "",
        source_warehouse: line.source_warehouse || sourceWarehouse,
        picked_qty: line.picked_qty == null ? "0" : String(line.picked_qty),
        packed_qty: line.packed_qty == null ? "0" : String(line.packed_qty),
        short_qty: line.short_qty == null ? "0" : String(line.short_qty),
        damaged_qty: line.damaged_qty == null ? "0" : String(line.damaged_qty),
        not_found_qty: line.not_found_qty == null ? "0" : String(line.not_found_qty),
        exception_type: line.exception_type || "",
        evidence_reference: line.evidence_reference || "",
        line_status: line.exception_type ? "Needs Review" : "Draft",
      })),
      stock_effect: {
        stock_posted: false,
        delivery_note_created: false,
        pick_list_created: false,
        stock_reservation_created: false,
      },
      valuation: { visible: false, fields: [] },
    };
    PICKING_WORKFLOW_TASKS.set(salesOrder, task);
    recordOverrideHit(diagnostics, "warehouse-picking-task-draft", route.request(), { fulfilled: true, salesOrder, lineCount: lines.length });
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ message: { state: { kind: "ready", title: "Picking task draft ready", detail: "Custom picking task recorded." }, page: { title: "Picking Task Draft", key: "picking_task_draft", sales_order: salesOrder }, task, stock_effect: task.stock_effect, valuation: task.valuation } }),
    });
  });
  await context.route("**/api/method/erp_workspace_ui.warehouse_console.service.save_warehouse_picking_manager_decision**", async (route) => {
    const body = requestMethodArgs(route.request());
    const decision = body.decision || "approve_clean_pick";
    const task = Array.from(PICKING_WORKFLOW_TASKS.values()).find((item) => item.task_id === body.task_id) || Array.from(PICKING_WORKFLOW_TASKS.values())[0];
    const statusByDecision = {
      request_repick: "Repick Requested",
      approve_clean_pick: "Clean Pick Approved",
      approve_partial_pick: "Partial Pick Reviewed",
      mark_shortage_review: "Shortage Review",
      escalate_to_sales: "Sales Review Needed",
      mark_pack_ready: "Pack Ready",
      mark_dispatch_handoff: "Outbound Review Ready",
    };
    if (task) {
      task.status = statusByDecision[decision] || "Manager Review";
      task.decision = decision;
      task.manager_decision_available = false;
      PICKING_WORKFLOW_TASKS.set(task.sales_order, task);
    }
    recordOverrideHit(diagnostics, "warehouse-picking-manager-decision", route.request(), { fulfilled: true, decision });
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ message: { state: { kind: "ready", title: "Picking manager decision ready", detail: "Custom picking task decision recorded." }, page: { title: "Picking Manager Decision", key: "picking_manager_decision", sales_order: task ? task.sales_order : "" }, task, status: task ? task.status : "", stock_effect: task ? task.stock_effect : {}, valuation: { visible: false, fields: [] } } }),
    });
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

async function diagnosticSnapshot(page, diagnostics, label) {
  const screenshot = await capture(page, `${safeName(label)}-diagnostic`).catch(() => "");
  const snapshot = await page.evaluate(() => ({
    url: location.href,
    route: window.frappe && typeof frappe.get_route === "function" ? frappe.get_route() : null,
    text: String((document.querySelector('.sales-console-shell[data-erpw-workspace="warehouse"]') || document.body).innerText || "").replace(/\s+/g, " ").slice(0, 1600),
    outboundShellCount: document.querySelectorAll('.warehouse-outbound-shell[data-warehouse-view="outbound-picking"]').length,
    pickingShellCount: document.querySelectorAll('.warehouse-picking-shell[data-warehouse-view="picking-review"]').length,
    pickingLineCount: document.querySelectorAll("[data-warehouse-picking-line]").length,
    pickingReadinessCount: document.querySelectorAll("[data-warehouse-picking-readiness-row]").length,
    diagnostics: window.erpWorkspaceWarehouseConsole && window.erpWorkspaceWarehouseConsole.diagnostics ? { ...window.erpWorkspaceWarehouseConsole.diagnostics } : {},
  })).catch((error) => ({ error: error && error.message ? error.message : String(error) }));
  snapshot.screenshot = screenshot;
  remember(diagnostics.snapshots, { label, ...snapshot }, 30);
  return snapshot;
}

async function waitForOutboundReady(page, diagnostics, label) {
  try {
    await page.waitForFunction(() => {
      const shell = document.querySelector('.warehouse-outbound-shell[data-erpw-workspace="warehouse"][data-warehouse-view="outbound-picking"]');
      return Boolean(shell
        && shell.getAttribute("data-erpw-console-runtime") === "ready"
        && shell.querySelectorAll("[data-warehouse-outbound-queue-card]").length >= 4
        && shell.querySelectorAll("[data-warehouse-outbound-row]").length >= 1
        && shell.querySelector("[data-warehouse-row-open-picking-detail]"));
    }, null, { timeout: TIMEOUT });
  } catch (error) {
    error.details = { ...(error.details || {}), snapshot: await diagnosticSnapshot(page, diagnostics, `${label}-outbound-timeout`) };
    throw error;
  }
}

async function waitForPickingReady(page, diagnostics, label) {
  try {
    await page.waitForFunction((expectW12D) => {
      const shell = document.querySelector('.warehouse-picking-shell[data-erpw-workspace="warehouse"][data-warehouse-view="picking-review"]');
      return Boolean(shell
        && shell.getAttribute("data-erpw-console-runtime") === "ready"
        && shell.querySelectorAll("[data-warehouse-picking-card]").length >= 4
        && shell.querySelectorAll("[data-warehouse-picking-line]").length >= 1
        && shell.querySelectorAll("[data-warehouse-picking-tab]").length >= 2
        && (!expectW12D || (
          shell.querySelector("[data-warehouse-picking-command]")
          && shell.querySelectorAll("[data-warehouse-picking-identity-chip]").length >= 5
          && shell.querySelectorAll("[data-warehouse-picking-command-fact]").length >= 4
          && shell.querySelectorAll("[data-warehouse-picking-readiness-card]").length >= 4
          && shell.querySelector("[data-warehouse-picking-guardrail]")
          && shell.querySelector("[data-warehouse-picking-workflow-shell]")
          && shell.querySelectorAll("[data-warehouse-picking-workflow-status]").length >= 6
          && shell.querySelectorAll("[data-warehouse-picking-workflow-control]").length >= 2
          && shell.querySelectorAll("[data-warehouse-picking-evidence-row]").length >= 1
          && shell.querySelectorAll("[data-warehouse-picking-exception-category]").length >= 6
          && shell.querySelectorAll("[data-warehouse-picking-manager-decision]").length >= 6
          && shell.querySelector("[data-warehouse-picking-delivery-policy]")
          && shell.querySelectorAll("[data-warehouse-picking-line-card]").length >= 1
          && shell.querySelectorAll("[data-warehouse-picking-line-fact]").length >= 5
        )));
    }, EXPECT_W12D, { timeout: TIMEOUT });
  } catch (error) {
    error.details = { ...(error.details || {}), snapshot: await diagnosticSnapshot(page, diagnostics, `${label}-picking-timeout`) };
    throw error;
  }
}

async function openRoute(page, routeParts, expectedPath, diagnostics, label, viewKind) {
  const canRoute = await page.evaluate(() => Boolean(window.frappe && typeof frappe.set_route === "function")).catch(() => false);
  if (canRoute) {
    await page.evaluate((parts) => frappe.set_route(...parts), routeParts);
    await page.waitForURL((url) => url.pathname === expectedPath || url.pathname === `/app/${routeParts.join("/")}`, { timeout: TIMEOUT });
  } else {
    await page.goto(routeUrl(expectedPath), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  }
  if (viewKind === "picking") {
    if (ASSET_ROOT) await waitForOverrideHit(page, diagnostics, "warehouse-picking-detail", label);
    await waitForPickingReady(page, diagnostics, label);
  } else {
    if (ASSET_ROOT) await waitForOverrideHit(page, diagnostics, "warehouse-outbound-queue", label);
    await waitForOutboundReady(page, diagnostics, label);
  }
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
    const actionText = Array.from(shellRoot.querySelectorAll("button, a, [role=button]")).filter(visible).map((node) => (node.innerText || node.getAttribute("aria-label") || node.getAttribute("href") || "").replace(/\s+/g, " ").trim()).filter(Boolean).join(" ");
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
      outboundShellCount: Array.from(document.querySelectorAll('.warehouse-outbound-shell[data-warehouse-view="outbound-picking"]')).filter(visible).length,
      pickingShellCount: Array.from(document.querySelectorAll('.warehouse-picking-shell[data-warehouse-view="picking-review"]')).filter(visible).length,
      pickingCardCount: Array.from(document.querySelectorAll("[data-warehouse-picking-card]")).filter(visible).length,
      pickingLineCount: Array.from(document.querySelectorAll("[data-warehouse-picking-line]")).filter(visible).length,
      pickingReadinessCount: Array.from(document.querySelectorAll("[data-warehouse-picking-readiness-row]")).filter(visible).length,
      pickingCommandCount: Array.from(document.querySelectorAll("[data-warehouse-picking-command]")).filter(visible).length,
      pickingIdentityChipCount: Array.from(document.querySelectorAll("[data-warehouse-picking-identity-chip]")).filter(visible).length,
      pickingCommandFactCount: Array.from(document.querySelectorAll("[data-warehouse-picking-command-fact]")).filter(visible).length,
      pickingReadinessCardCount: Array.from(document.querySelectorAll("[data-warehouse-picking-readiness-card]")).filter(visible).length,
      pickingGuardrailCount: Array.from(document.querySelectorAll("[data-warehouse-picking-guardrail]")).filter(visible).length,
      pickingWorkflowShellCount: Array.from(document.querySelectorAll("[data-warehouse-picking-workflow-shell]")).filter(visible).length,
      pickingWorkflowStatusCount: Array.from(document.querySelectorAll("[data-warehouse-picking-workflow-status]")).filter(visible).length,
      pickingWorkflowControlCount: Array.from(document.querySelectorAll("[data-warehouse-picking-workflow-control]")).filter(visible).length,
      pickingWorkflowEvidenceRowCount: Array.from(document.querySelectorAll("[data-warehouse-picking-evidence-row]")).filter(visible).length,
      pickingWorkflowExceptionCount: Array.from(document.querySelectorAll("[data-warehouse-picking-exception-category]")).filter(visible).length,
      pickingWorkflowManagerDecisionCount: Array.from(document.querySelectorAll("[data-warehouse-picking-manager-decision]")).filter(visible).length,
      pickingWorkflowDeliveryPolicyCount: Array.from(document.querySelectorAll("[data-warehouse-picking-delivery-policy]")).filter(visible).length,
      pickingWorkflowActiveControlCount: Array.from(document.querySelectorAll("[data-warehouse-picking-workflow-shell] button, [data-warehouse-picking-workflow-shell] a, [data-warehouse-picking-workflow-shell] [role=button]")).filter(visible).length,
      pickingLineCardCount: Array.from(document.querySelectorAll("[data-warehouse-picking-line-card]")).filter(visible).length,
      pickingLineFactCount: Array.from(document.querySelectorAll("[data-warehouse-picking-line-fact]")).filter(visible).length,
      pickingDetailHeadCount: Array.from(document.querySelectorAll("[data-warehouse-picking-detail-head]")).filter(visible).length,
      tabCount: Array.from(document.querySelectorAll("[data-warehouse-picking-tab]")).filter(visible).length,
      detailButtonCount: Array.from(document.querySelectorAll("[data-warehouse-row-open-picking-detail]")).filter(visible).length,
      contentSearchVisible: Array.from(shellRoot.querySelectorAll("[data-erpw-sales-search-open], input[type='search'], [placeholder*='Search'], [aria-label*='Search']")).some(visible),
      searchUtilityVisible: Array.from(document.querySelectorAll("[data-erpw-sales-search-open]")).some(visible),
      pageHeadCount: Array.from(document.querySelectorAll(".page-head")).filter(visible).length,
      horizontalOverflow: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
      diagnostics: window.erpWorkspaceWarehouseConsole && window.erpWorkspaceWarehouseConsole.diagnostics ? { ...window.erpWorkspaceWarehouseConsole.diagnostics } : {},
      hasExportedPickingRenderer: Boolean(window.erpWorkspaceWarehouseConsole && typeof window.erpWorkspaceWarehouseConsole.renderPickingReview === "function"),
      hasPagePickingRenderer: Boolean(window.frappe && frappe.pages && frappe.pages["warehouse-console-picking"] && typeof frappe.pages["warehouse-console-picking"].__erpwRenderWarehousePickingReview === "function"),
    };
  });
}

function assertCleanWarehouseUi(state, context) {
  assert(state.shellCount === 1, "Warehouse shell count must remain 1", { context, state });
  assert(state.headerCount === 1, "Warehouse header count must remain 1", { context, state });
  assert(!state.pageHeadCount || state.pageHeadCount <= 1, "Frappe page chrome must not duplicate", { context, state });
  assert(state.sidebarCount <= 1, "Warehouse sidebar count must not duplicate", { context, state });
  assert(state.horizontalOverflow <= 2, "Warehouse page has horizontal overflow", { context, state });
  assert(!state.contentSearchVisible, "Warehouse Picking Review content must not expose page-local search", { context, state });
  assert(!FORBIDDEN_ACTION_RE.test(state.actionText), "Forbidden stock or picking action control is visible", { context, state });
  assert(!FORBIDDEN_COPY_RE.test(state.text), "Developer or governance copy is visible", { context, state });
  assert(!VALUATION_RE.test(state.text), "Valuation or commercial text is visible", { context, state });
  assert(!NATIVE_ROUTE_RE.test(`${state.hrefs} ${state.actionText}`), "Native route target is visible", { context, state });
}

function assertW12DPickingPolish(state, context, options = {}) {
  if (!EXPECT_W12D) return;
  const requireLineCards = options.requireLineCards !== false;
  assert(state.pickingCommandCount === 1, "Picking command header did not render exactly once", { context, state });
  assert(state.pickingIdentityChipCount >= 5, "Picking identity chips did not render", { context, state });
  assert(state.pickingCommandFactCount >= 4, "Picking command facts did not render", { context, state });
  assert(state.pickingReadinessCardCount >= 4, "Picking readiness cards did not render", { context, state });
  assert(state.pickingGuardrailCount === 1, "Picking read-only guardrail did not render exactly once", { context, state });
  assert(state.pickingWorkflowShellCount === 1, "Picking workflow shell did not render exactly once", { context, state });
  assert(state.pickingWorkflowStatusCount >= 6, "Picking workflow status strip did not render", { context, state });
  assert(state.pickingWorkflowControlCount >= 2, "Picking custom workflow controls did not render", { context, state });
  assert(state.pickingWorkflowEvidenceRowCount >= 1, "Picking evidence preview did not render", { context, state });
  assert(state.pickingWorkflowExceptionCount >= 6, "Picking exception categories did not render", { context, state });
  assert(state.pickingWorkflowManagerDecisionCount >= 6, "Picking manager decision preview did not render", { context, state });
  assert(state.pickingWorkflowDeliveryPolicyCount === 1, "Picking outbound document policy did not render exactly once", { context, state });
  assert(state.pickingWorkflowActiveControlCount >= 2, "Picking custom workflow controls did not activate", { context, state });
  if (requireLineCards) {
    assert(state.pickingLineCardCount >= 1, "Picking item line cards did not render", { context, state });
    assert(state.pickingLineFactCount >= 5, "Picking item line facts did not render", { context, state });
  }
  assert(state.pickingDetailHeadCount === 1, "Picking detail header did not render exactly once", { context, state });
}

async function exerciseUser(browser, user) {
  const diagnostics = makeDiagnostics(user.key);
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await installSourceOverrides(context, diagnostics);
  if (EXPECT_W12D) {
    await context.addInitScript(() => {
      window.__erpwWarehouseExpectW12D = true;
    });
  }
  const page = await context.newPage();
  attachDiagnostics(page, diagnostics);
  try {
    await login(page, user);
    await openRoute(page, ["warehouse-console-worklist", "outbound-picking"], "/desk/warehouse-console-worklist/outbound-picking", diagnostics, `${user.key}:queue`, "outbound");
    let state = await snapshot(page);
    assertCleanWarehouseUi(state, `${user.key}:queue`);
    assert(state.detailButtonCount >= 1, "Outbound queue did not expose picking review drilldown", { user: user.key, state });

    await page.locator("[data-warehouse-row-open-picking-detail]").first().click();
    await page.waitForURL((url) => /\/(?:desk|app)\/warehouse-console-picking\//.test(url.pathname), { timeout: TIMEOUT });
    if (ASSET_ROOT) await waitForOverrideHit(page, diagnostics, "warehouse-picking-detail", `${user.key}:row-drilldown`);
    await waitForPickingReady(page, diagnostics, `${user.key}:row-drilldown`);
    const directSalesOrder = await page.evaluate(() => {
      const route = window.frappe && typeof frappe.get_route === "function" ? frappe.get_route() : null;
      if (Array.isArray(route) && route[0] === "warehouse-console-picking" && route[1]) return route[1];
      const parts = location.pathname.split("/").filter(Boolean);
      return parts[parts.length - 1] || "";
    });
    assert(directSalesOrder && directSalesOrder !== "warehouse-console-picking", "Picking review route did not expose a concrete Sales Order", { user: user.key, directSalesOrder });
    state = await snapshot(page);
    assertCleanWarehouseUi(state, `${user.key}:row-drilldown`);
    assertW12DPickingPolish(state, `${user.key}:row-drilldown`);
    assert(state.pickingCardCount >= 4, "Picking review cards did not render", { user: user.key, state });
    assert(state.pickingLineCount >= 1, "Picking review lines did not render", { user: user.key, state });
    assert(state.tabCount >= 2, "Picking review tabs did not render", { user: user.key, state });
    await page.locator('[data-warehouse-picking-count-save]').first().click();
    await waitForOverrideHit(page, diagnostics, "warehouse-picking-task-draft", `${user.key}:picking-task-draft`);
    await waitForPickingReady(page, diagnostics, `${user.key}:picking-task-draft`);
    state = await snapshot(page);
    assertCleanWarehouseUi(state, `${user.key}:picking-task-draft`);
    assertW12DPickingPolish(state, `${user.key}:picking-task-draft`);
    assert((state.diagnostics || {}).pickingTaskDraftSaved >= 1, "W16C picking draft did not complete", { user: user.key, state, diagnostics });
    await page.locator('[data-warehouse-picking-manager-action="approve_clean_pick"]').first().click();
    await waitForOverrideHit(page, diagnostics, "warehouse-picking-manager-decision", `${user.key}:picking-manager-decision`);
    await page.waitForFunction(() => {
      const status = document.querySelector("[data-warehouse-picking-workflow-status-message]");
      return Boolean(status && /Manager decision recorded/i.test(status.innerText || ""));
    }, null, { timeout: TIMEOUT });
    state = await snapshot(page);
    assertCleanWarehouseUi(state, `${user.key}:picking-manager-decision`);
    assert((state.diagnostics || {}).pickingManagerDecisionSaved >= 1, "W16C picking manager decision did not complete", { user: user.key, state, diagnostics });
    await capture(page, `${user.key}-picking-review`);

    await page.locator('[data-warehouse-picking-tab="stock_readiness"]').click();
    state = await snapshot(page);
    assert(state.pickingReadinessCount >= 1, "Picking readiness rows did not render", { user: user.key, state });
    assertCleanWarehouseUi(state, `${user.key}:stock-readiness-tab`);
    assertW12DPickingPolish(state, `${user.key}:stock-readiness-tab`, { requireLineCards: false });
    if (EXPECT_W12D) await capture(page, `${user.key}-picking-review-stock-readiness`);

    await page.locator('[data-warehouse-picking-tab="item_lines"]').click();
    state = await snapshot(page);
    assert(state.pickingLineCardCount >= 1, "Picking item line cards did not render after returning to item lines", { user: user.key, state });
    assertCleanWarehouseUi(state, `${user.key}:item-lines-tab`);
    assertW12DPickingPolish(state, `${user.key}:item-lines-tab`);

    await page.locator("[data-warehouse-picking-refresh]").click();
    await waitForPickingReady(page, diagnostics, `${user.key}:refresh`);
    state = await snapshot(page);
    assertCleanWarehouseUi(state, `${user.key}:refresh`);
    assertW12DPickingPolish(state, `${user.key}:refresh`);

    await page.reload({ waitUntil: "domcontentloaded", timeout: TIMEOUT });
    await waitForPickingReady(page, diagnostics, `${user.key}:refresh-page`);
    state = await snapshot(page);
    assertCleanWarehouseUi(state, `${user.key}:refresh-page`);
    assertW12DPickingPolish(state, `${user.key}:refresh-page`);

    await page.locator("[data-warehouse-picking-back]").click();
    await page.waitForURL((url) => /\/(?:desk|app)\/warehouse-console-worklist\/outbound-picking$/.test(url.pathname), { timeout: TIMEOUT });
    await waitForOutboundReady(page, diagnostics, `${user.key}:back-to-queue`);
    state = await snapshot(page);
    assertCleanWarehouseUi(state, `${user.key}:back-to-queue`);
    if (EXPECT_W12D) await capture(page, `${user.key}-back-to-outbound-queue`);

    for (const viewport of ACTIVE_VIEWPORTS) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await collapseBodySidebarForNarrowViewport(page);
      const directPickingPath = `/desk/warehouse-console-picking/${encodeURIComponent(directSalesOrder)}`;
      await openRoute(page, ["warehouse-console-picking", directSalesOrder], directPickingPath, diagnostics, `${user.key}:${viewport.key}:direct`, "picking");
      await collapseBodySidebarForNarrowViewport(page);
      state = await snapshot(page);
      assertCleanWarehouseUi(state, `${user.key}:${viewport.key}:direct`);
      assertW12DPickingPolish(state, `${user.key}:${viewport.key}:direct`);
      assert(state.pickingShellCount === 1, "Picking review shell count must remain 1", { user: user.key, viewport, state });
      assert(state.pickingLineCount >= 1, "Picking review lines did not render", { user: user.key, viewport, state });
      await capture(page, `${user.key}-${viewport.key}-picking-review`);
    }

    state = await snapshot(page);
    assert(state.hasExportedPickingRenderer, "Warehouse exported picking renderer is missing", { user: user.key, state, diagnostics });
    assert(state.hasPagePickingRenderer, "Warehouse page picking renderer is missing", { user: user.key, state, diagnostics });
    assert((state.diagnostics || {}).renderPickingReviewEntered >= 1, "Warehouse picking renderer was not entered", { user: user.key, state, diagnostics });
    assert((state.diagnostics || {}).pickingServiceCallAttempted >= 1, "Warehouse picking service call was not attempted", { user: user.key, state, diagnostics });
    if (ASSET_ROOT) {
      assert(diagnostics.overrideHits.some((hit) => hit.key === "desk-page-getpage" && hit.page === "warehouse-console-picking"), "Warehouse picking getpage source override was not used", { user: user.key, diagnostics });
      assert(diagnostics.overrideHits.some((hit) => hit.key === "warehouse-page-asset"), "Warehouse page asset source override was not used", { user: user.key, diagnostics });
      assert(diagnostics.overrideHits.some((hit) => hit.key === "warehouse-picking-detail"), "Warehouse picking detail source override was not used", { user: user.key, diagnostics });
    }
    assert(!diagnostics.consoleErrors.some((entry) => entry.type === "error"), "Warehouse W5B smoke recorded console errors", { user: user.key, diagnostics });
    assert(diagnostics.pageErrors.length === 0, "Warehouse W5B smoke recorded page errors", { user: user.key, diagnostics });
    assert(diagnostics.failedResponses.length === 0, "Warehouse W5B smoke recorded failed responses", { user: user.key, diagnostics });
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
  assert(AUTHORIZED_USERS.length > 0, "No Warehouse W5B smoke credentials were provided. Set ERPW_WAREHOUSE_MANAGER_USERNAME/PASSWORD or ERPW_WAREHOUSE_USER_USERNAME/PASSWORD.");
  const browser = await chromium.launch({ headless: process.env.ERPW_HEADLESS !== "0" });
  const summary = { status: "pass", phase: EXPECT_W12D ? "W12D" : "W5B", artifactDir: ARTIFACT_DIR, sourceOverride: Boolean(ASSET_ROOT), authorizedUsers: AUTHORIZED_USERS.map((user) => user.key), authorized: [] };
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
  console.log(`Warehouse ${EXPECT_W12D ? "W12D picking review polish" : "W5B picking review"} smoke passed. Summary: ${path.join(ARTIFACT_DIR, SUMMARY_FILE)}`);
})().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exit(1);
});
