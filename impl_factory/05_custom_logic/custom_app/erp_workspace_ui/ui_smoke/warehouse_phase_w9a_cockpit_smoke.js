const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const EXPECT_W12K = process.env.ERPW_WAREHOUSE_W9A_EXPECT_W12K === "1";
const EXPECT_W14B = process.env.ERPW_WAREHOUSE_W9A_EXPECT_W14B === "1";
const EXPECT_W14C = process.env.ERPW_WAREHOUSE_W9A_EXPECT_W14C === "1";
const EXPECT_W15B = process.env.ERPW_WAREHOUSE_W9A_EXPECT_W15B === "1";
const EXPECT_W15G = process.env.ERPW_WAREHOUSE_W9A_EXPECT_W15G === "1";
const PHASE_LABEL = process.env.ERPW_WAREHOUSE_W9A_PHASE_LABEL || (EXPECT_W15G ? "Warehouse W15G2 Internal Transfer shell" : (EXPECT_W15B ? "Warehouse W15B Action Center shell" : (EXPECT_W14C ? "Warehouse W14C Manager Readiness" : (EXPECT_W14B ? "Warehouse W14B Quick Find" : (EXPECT_W12K ? "Warehouse W12K cockpit polish" : "Warehouse W9A cockpit")))));
const SUMMARY_NAME = process.env.ERPW_WAREHOUSE_W9A_SUMMARY_NAME || (EXPECT_W15G ? "warehouse-w15g2-internal-transfer-summary.json" : (EXPECT_W15B ? "warehouse-w15b-action-center-summary.json" : (EXPECT_W14C ? "warehouse-w14c-manager-readiness-summary.json" : (EXPECT_W14B ? "warehouse-w14b-quick-find-summary.json" : (EXPECT_W12K ? "warehouse-w12k-cockpit-polish-summary.json" : "warehouse-w9a-cockpit-summary.json")))));
const TIMEOUT = Number(process.env.ERPW_WAREHOUSE_W15G_TIMEOUT || process.env.ERPW_WAREHOUSE_W15B_TIMEOUT || process.env.ERPW_WAREHOUSE_W14C_TIMEOUT || process.env.ERPW_WAREHOUSE_W14B_TIMEOUT || process.env.ERPW_WAREHOUSE_W12K_TIMEOUT || process.env.ERPW_WAREHOUSE_W9A_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_WAREHOUSE_W15G_ARTIFACT_DIR || process.env.ERPW_WAREHOUSE_W15B_ARTIFACT_DIR || process.env.ERPW_WAREHOUSE_W14C_ARTIFACT_DIR || process.env.ERPW_WAREHOUSE_W14B_ARTIFACT_DIR || process.env.ERPW_WAREHOUSE_W12K_ARTIFACT_DIR || process.env.ERPW_WAREHOUSE_W9A_ARTIFACT_DIR || path.join(
  fs.existsSync("/freeze-artifacts") ? "/freeze-artifacts" : path.join(__dirname, "artifacts"),
  `${EXPECT_W15G ? "warehouse-w15g2-internal-transfer" : (EXPECT_W15B ? "warehouse-w15b-action-center" : (EXPECT_W14C ? "warehouse-w14c-manager-readiness" : (EXPECT_W14B ? "warehouse-w14b-quick-find" : (EXPECT_W12K ? "warehouse-w12k-cockpit-polish" : "warehouse-w9a-cockpit"))))}-${new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z")}`
);
const ASSET_ROOT = process.env.ERPW_WAREHOUSE_W15G_ASSET_ROOT || process.env.ERPW_WAREHOUSE_W15B_ASSET_ROOT || process.env.ERPW_WAREHOUSE_W14C_ASSET_ROOT || process.env.ERPW_WAREHOUSE_W14B_ASSET_ROOT || process.env.ERPW_WAREHOUSE_W12K_ASSET_ROOT || process.env.ERPW_WAREHOUSE_W9A_ASSET_ROOT || "";

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
  { key: "desktop-1440", width: 1440, height: 900 },
  { key: "laptop-1240", width: 1240, height: 768 },
  { key: "laptop-1136", width: 1136, height: 768 },
  { key: "mobile-390", width: 390, height: 844 },
];

const FORBIDDEN_ACTION_RE = /\b(Receive|Ship|Dispatch|Post|Submit|Cancel|Amend|Reconcile|Stock Entry|Purchase Receipt|Delivery Note|Stock Reconciliation|Pick List|Reserve|Unreserve|Assign Serial|Assign Batch|Pack|Scan|Allocate|Create|Save|Transfer(?! Visibility)|Print|Email)\b/i;
const FORBIDDEN_COPY_RE = /\b(Productized|native ERP|governed|deferred|route only|mutation|backend|frontend|framework|Frappe|smoke|test)\b/i;
const NATIVE_ROUTE_RE = /\/desk\/Form\/|\/app\/|#Form\/|query-report|\/desk\/List\//i;
const VALUATION_RE = /stock value|valuation rate|stock_value|valuation_rate|incoming_rate|outgoing_rate|basic_rate|\brate\b|\bamount\b|base_amount|transfer_price|profit|margin|\bcost\b|\bgl\b|accounting|billing|payment|tax|item price|stock_queue/i;

fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

const workflowRecallState = {
  customerReturnIntake: null,
  supplierReturnCandidate: null,
  internalTransferCandidate: null,
  cycleCountTask: null,
};

function resetWorkflowRecallState() {
  workflowRecallState.customerReturnIntake = null;
  workflowRecallState.supplierReturnCandidate = null;
  workflowRecallState.internalTransferCandidate = null;
  workflowRecallState.cycleCountTask = null;
}

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

function assertWarehouseHandoffCopyIsPostureOnly(body, file) {
  if (!body || !/warehouse_console_page\.js$/.test(file)) return;
  const staleLabels = [
    "Escalate to Sales",
    "Escalate to Procurement",
    "Request Inventory/Admin review",
    "Record handoff review",
    "Document owner review",
    "outbound handoff readiness",
  ];
  const found = staleLabels.filter((label) => body.includes(label));
  assert(found.length === 0, "Warehouse source still contains active-sounding handoff labels", { file, found });
}

function remember(list, item, limit = 160) {
  list.push(item);
  if (list.length > limit) list.shift();
}

function makeDiagnostics(label) {
  return { label, consoleErrors: [], pageErrors: [], failedResponses: [], failedRequests: [], overrideHits: [], snapshots: [] };
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

function sidebarItems() {
  return [
    { key: "warehouse_console_home", label: "Overview", icon: "item", target: { kind: "page", route: "warehouse-console" } },
    { key: "inbound_receiving", label: "Inbound Receiving", icon: "quotation", target: { kind: "worklist", queue_key: "inbound_receiving" } },
    { key: "outbound_picking", label: "Outbound Picking", icon: "order", target: { kind: "worklist", queue_key: "outbound_picking" } },
    { key: "stock_exceptions", label: "Stock Exceptions", icon: "report", target: { kind: "worklist", queue_key: "stock_exceptions" } },
    { key: "returns_work_hub", label: "Returns", icon: "return", target: { kind: "worklist", queue_key: "returns_work_hub" } },
    { key: "internal_transfer_workflow", label: "Internal Transfer", icon: "stock", target: { kind: "worklist", queue_key: "internal_transfer_workflow" } },
    { key: "movement_visibility", label: "Movement Visibility", icon: "stock", target: { kind: "worklist", queue_key: "movement_visibility" } },
    { key: "transfer_visibility", label: "Transfer Visibility", icon: "branch", target: { kind: "worklist", queue_key: "transfer_visibility" } },
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
      inboundQueue: "erp_workspace_ui.warehouse_console.service.get_warehouse_inbound_receiving_queue",
      outboundQueue: "erp_workspace_ui.warehouse_console.service.get_warehouse_outbound_picking_queue",
      stockExceptions: "erp_workspace_ui.warehouse_console.service.get_warehouse_stock_exceptions",
      movementVisibility: "erp_workspace_ui.warehouse_console.service.get_warehouse_movement_visibility_queue",
      transferVisibility: "erp_workspace_ui.warehouse_console.service.get_warehouse_transfer_visibility_queue",
      quickFind: "erp_workspace_ui.warehouse_console.service.get_warehouse_quick_find_suggestions",
      workspaceSearch: "erp_workspace_ui.warehouse_console.service.search_warehouse_console_workspace",
      returnsWorkHub: "erp_workspace_ui.warehouse_console.service.get_warehouse_returns_work_hub",
      customerReturnIntakeDraft: "erp_workspace_ui.warehouse_console.service.save_warehouse_customer_return_intake_draft",
      customerReturnManagerDecision: "erp_workspace_ui.warehouse_console.service.save_warehouse_customer_return_manager_decision",
      supplierReturnCandidateDraft: "erp_workspace_ui.warehouse_console.service.save_warehouse_supplier_return_candidate_draft",
      supplierReturnManagerDecision: "erp_workspace_ui.warehouse_console.service.save_warehouse_supplier_return_manager_decision",
      internalTransferWorkflow: "erp_workspace_ui.warehouse_console.service.get_warehouse_internal_transfer_workflow",
      internalTransferCandidateDraft: "erp_workspace_ui.warehouse_console.service.save_warehouse_internal_transfer_candidate_draft",
      internalTransferManagerDecision: "erp_workspace_ui.warehouse_console.service.save_warehouse_internal_transfer_manager_decision",
      cycleCountWorkflow: "erp_workspace_ui.warehouse_console.service.get_warehouse_cycle_count_workflow",
      cycleCountTaskDraft: "erp_workspace_ui.warehouse_console.service.save_warehouse_cycle_count_task_draft",
      cycleCountManagerDecision: "erp_workspace_ui.warehouse_console.service.save_warehouse_cycle_count_manager_decision",
    },
    search: {
      enabled: true,
      mode: "warehouse_sidebar_search",
      placement: "sidebar_utility",
      placeholder: "Find purchase orders, sales orders, items, warehouses, or movements",
    },
  };
}

function sidebarPayload() {
  const items = sidebarItems();
  return {
    workspace: workspacePayload(),
    context: { has_warehouse_access: true, role_family: "Warehouse", role_variant: "warehouse_manager", can_view_valuation: false },
    state: { kind: "ready", title: "Warehouse Console ready", detail: "Warehouse cockpit is available." },
    sidebar: { workspace_id: "warehouse", title: "Warehouse Console", mode_label: "Warehouse Workspace", scope_label: "Stock workbench", active_key: "warehouse_console_home", home_key: "warehouse_console_home", items, sections: [{ key: "workspace", label: "Workspace", items }] },
    fetched_at: "2026-05-30 09:00:00",
  };
}

function summaryCards(prefix, values) {
  return values.map(([key, label, value, note]) => ({ key: `${prefix}_${key}`, label, title: label, value, state: "live", note }));
}

function queueControls() {
  return { fields: [{ key: "state", label: "State", type: "select", value: "", options: [{ label: "All", value: "" }] }] };
}

function inboundPayload() {
  const rows = [{ key: "PO-W9A-1", purchase_order: "PO-W9A-1", supplier: "Review Supplier", target_warehouse: "Main - M", required_date: "2026-05-30", age_label: "Due today", received_percent: "40%", status: "Partly received", line_count: 3, item_count: 3, remaining_summary: "12 Nos" }];
  return {
    workspace: workspacePayload(),
    context: sidebarPayload().context,
    state: { kind: "ready", title: "Inbound receiving ready", detail: "Inbound receiving is available." },
    page: { title: "Inbound Receiving", key: "inbound_receiving" },
    summary: { title: "Inbound Receiving", subtitle: "Supplier-side receiving posture.", chips: [{ label: "Read-only" }] },
    controls: queueControls(),
    cards: summaryCards("inbound", [["overdue", "Overdue", 1, "Supplier stock past due."], ["due", "Due Today", 1, "Expected today."], ["partial", "Partly Received", 1, "Receiving in progress."], ["soon", "Expected Soon", 2, "Next two weeks."]]),
    groups: [{ key: "due_today", title: "Due Today", summary: "Expected supplier stock due today.", rows }],
    rows,
    fetched_at: "2026-05-30 09:00:00",
  };
}

function outboundPayload() {
  const rows = [{ key: "SO-W9A-1", sales_order: "SO-W9A-1", customer: "Review Customer", target_warehouse: "Main - M", required_date: "2026-05-30", age_label: "Due today", delivered_percent: "0%", status: "Needs review", line_count: 2, item_count: 2, remaining_summary: "8 Nos", stock_state: "Needs review" }];
  return {
    workspace: workspacePayload(),
    context: sidebarPayload().context,
    state: { kind: "ready", title: "Outbound picking ready", detail: "Outbound picking is available." },
    page: { title: "Outbound Picking", key: "outbound_picking" },
    summary: { title: "Outbound Picking", subtitle: "Customer-side picking posture.", chips: [{ label: "Read-only" }] },
    controls: queueControls(),
    cards: summaryCards("outbound", [["overdue", "Overdue", 0, "Past due orders."], ["due", "Due Today", 1, "Customer demand due today."], ["short", "Stock Review", 1, "Posture needs checking."], ["soon", "Expected Soon", 2, "Next two weeks."]]),
    groups: [{ key: "due_today", title: "Due Today", summary: "Customer-side picking due today.", rows }],
    rows,
    fetched_at: "2026-05-30 09:00:00",
  };
}

function stockExceptionsPayload() {
  const rows = [{ key: "SO-W9A-1:ITEM-W9A:Main-M", sales_order: "SO-W9A-1", customer: "Review Customer", item_code: "ITEM-W9A", item_name: "Review Item", required_date: "2026-05-30", pending_qty: "8", delivered_qty: "0", uom: "Nos", source_warehouse: "Main - M", available_qty: "2", projected_qty: "2", short_qty: "6", expected_inbound_qty: "10", expected_inbound_date: "2026-06-01", exception_key: "shortage_risk", exception_label: "Needs Stock Review", urgency_label: "Due today", explanation: "Visible stock is short for open demand.", route_targets: { picking: { route: "warehouse-console-picking", sales_order: "SO-W9A-1" } } }];
  return {
    workspace: workspacePayload(),
    context: sidebarPayload().context,
    state: { kind: "ready", title: "Stock exceptions ready", detail: "Stock exceptions are available." },
    page: { title: "Stock Exceptions", key: "stock_exceptions" },
    summary: { title: "Stock Exceptions", subtitle: "Shortage and posture risks.", chips: [{ label: "Read-only" }] },
    controls: queueControls(),
    cards: [
      { key: "total_exceptions", label: "Total Exceptions", title: "Total Exceptions", value: rows.length, state: "live", note: "Rows needing review." },
      { key: "shortage_risk", label: "Shortage Risk", title: "Shortage Risk", value: 1, state: "live", note: "Demand short of stock posture." },
      { key: "inbound_cover_soon", label: "Inbound Cover Soon", title: "Inbound Cover Soon", value: 1, state: "live", note: "Supplier stock expected soon." },
      { key: "missing_posture", label: "Missing Posture", title: "Missing Posture", value: 0, state: "live", note: "Warehouse posture gaps." },
    ],
    groups: [{ key: "needs_stock_review", title: "Needs Stock Review", summary: "Demand needs warehouse posture review.", rows }],
    rows,
    fetched_at: "2026-05-30 09:00:00",
  };
}

function movementPayload() {
  const rows = [{ key: "MAT-W9A-1", movement_id: "MAT-W9A-1", movement_type: "Warehouse Movement", purpose: "Warehouse Movement", posting_date: "2026-05-30", posting_time: "09:15:00", source_warehouse: "Stores - M", target_warehouse: "Main - M", direction_label: "Stores - M to Main - M", item_count: 2, quantity_summary: "7 Nos", group_key: "internal_movements", group_label: "Internal Movements", route_targets: {}, sample_items: [] }];
  return {
    workspace: workspacePayload(),
    context: sidebarPayload().context,
    state: { kind: "ready", title: "Movement visibility ready", detail: "Movement visibility is available." },
    page: { title: "Movement Visibility", key: "movement_visibility" },
    summary: { title: "Movement Visibility", subtitle: "Posted movement posture across warehouses.", chips: [{ label: "Read-only" }] },
    controls: queueControls(),
    cards: summaryCards("movement", [["total", "Total Movements", rows.length, "Latest window."], ["internal", "Internal Movement", 1, "Warehouse-to-warehouse posture."], ["receipts", "Receipts", 0, "Stock arriving into warehouse."], ["review", "Needs Review", 0, "Posture needs checking."]]),
    groups: [{ key: "internal_movements", title: "Internal Movements", summary: "Warehouse-to-warehouse movements recorded recently.", rows }],
    rows,
    fetched_at: "2026-05-30 09:00:00",
  };
}

function transferPayload() {
  const rows = [
    {
      key: "MAT-TR-W12K-1",
      movement_id: "MAT-TR-W12K-1",
      movement_type: "Material Transfer",
      purpose: "Material Transfer",
      posting_date: "2026-05-30",
      posting_time: "10:05:00",
      source_warehouse: "Stores - M",
      target_warehouse: "Main - M",
      direction_label: "Stores - M to Main - M",
      item_count: 2,
      quantity_summary: "9 Nos",
      group_key: "direct_transfers",
      group_label: "Direct Transfers",
      sample_items: [
        { item_code: "ITEM-W12K-A", item_name: "Transfer Item A", quantity: "5", stock_uom: "Nos", source_warehouse: "Stores - M", target_warehouse: "Main - M" },
        { item_code: "ITEM-W12K-B", item_name: "Transfer Item B", quantity: "4", stock_uom: "Nos", source_warehouse: "Stores - M", target_warehouse: "Main - M" },
      ],
      route_targets: {
        movement: { token: "eyJtb3ZlbWVudF9pZCI6Ik1BVC1UUi1XMTJLLTEifQ" },
        stock_posture: { token: "eyJpdGVtX2NvZGUiOiJJVEVNLVcxMkstQSIsIndhcmVob3VzZSI6Ik1haW4gLSBNIn0" },
      },
    },
  ];
  return {
    workspace: workspacePayload(),
    context: sidebarPayload().context,
    state: { kind: "ready", title: "Transfer visibility ready", detail: "Transfer visibility is available." },
    page: { title: "Transfer Visibility", key: "transfer_visibility" },
    summary: { title: "Transfer Visibility", subtitle: "Posted warehouse-to-warehouse transfer posture.", chips: [{ label: "Read-only" }] },
    controls: queueControls(),
    cards: summaryCards("transfer", [["direct", "Direct Transfers", 1, "Warehouse-to-warehouse posture."], ["transit", "Transit Related", 0, "Transit posture needing review."], ["review", "Needs Review", 0, "Rows needing posture review."], ["recent", "Recently Posted", 1, "Latest posted transfer movement."]]),
    groups: [{ key: "direct_transfers", title: "Direct Transfers", summary: "Posted warehouse-to-warehouse movement records.", rows }],
    rows,
    fetched_at: "2026-05-30 09:00:00",
  };
}

function managerCenterPayload() {
  const receivingTarget = { kind: "warehouse_page", route: "warehouse-console-receiving", purchase_order: "PO-W14C-1" };
  const pickingTarget = { kind: "warehouse_page", route: "warehouse-console-picking", sales_order: "SO-W14C-1" };
  const exceptionTarget = { kind: "warehouse_page", route: "warehouse-console-stock-exception", context_token: "7b2273616c65735f6f72646572223a22534f2d573134432d31222c226974656d5f636f6465223a224954454d2d57313443222c2277617265686f757365223a224d61696e202d204d227d" };
  const movementTarget = { kind: "warehouse_page", route: "warehouse-console-movement", context_token: "7b226d6f76656d656e745f6964223a224d41542d573134432d31227d" };
  const groups = [
    {
      key: "arrival_review",
      title: "Arrival readiness",
      summary: "Supplier-side rows that need manager review.",
      items: [{
        key: "arrival:PO-W14C-1",
        title: "PO-W14C-1",
        subtitle: "Manager Supplier",
        status: "Overdue",
        detail: "12 Nos remaining",
        facts: [{ label: "Supplier", value: "Manager Supplier" }, { label: "Warehouse", value: "Main - M" }, { label: "Receiving", value: "40%" }],
        target: receivingTarget,
        action_label: "Review receiving",
      }],
    },
    {
      key: "pick_blockers",
      title: "Picking blockers",
      summary: "Customer-side rows blocked by timing or stock posture.",
      items: [{
        key: "picking:SO-W14C-1",
        title: "SO-W14C-1",
        subtitle: "Manager Customer",
        status: "Needs stock review",
        detail: "8 Nos remaining",
        facts: [{ label: "Customer", value: "Manager Customer" }, { label: "Warehouse", value: "Main - M" }, { label: "Picking", value: "0%" }],
        target: pickingTarget,
        action_label: "Review picking",
      }],
    },
    {
      key: "stock_posture",
      title: "Stock posture issues",
      summary: "Shortage and missing-posture rows needing review.",
      items: [{
        key: "exception:SO-W14C-1",
        title: "SO-W14C-1",
        subtitle: "ITEM-W14C",
        status: "Needs Stock Review",
        detail: "Visible stock is short for open demand.",
        facts: [{ label: "Item", value: "ITEM-W14C" }, { label: "Warehouse", value: "Main - M" }, { label: "Short", value: "6" }],
        target: exceptionTarget,
        action_label: "Review exception",
      }],
    },
    {
      key: "transfer_review",
      title: "Transfer review",
      summary: "Posted transfer visibility rows with incomplete posture.",
      items: [{
        key: "transfer:MAT-W14C-1",
        title: "MAT-W14C-1",
        subtitle: "Stores - M to Main - M",
        status: "Needs review",
        detail: "9 Nos",
        facts: [{ label: "Source", value: "Stores - M" }, { label: "Target", value: "Main - M" }, { label: "Items", value: "2" }],
        target: movementTarget,
        action_label: "Review movement",
      }],
    },
  ];
  return {
    visible: true,
    state: "ready",
    title: "Manager Readiness Center",
    subtitle: "Read-only triage for Warehouse blockers before any separate operation.",
    cards: groups.map((group) => ({ key: group.key, label: group.title, value: group.items.length, note: group.summary })),
    groups,
    empty_message: "No manager readiness blockers are visible right now.",
    boundary_note: "Review-only. Open custom Warehouse pages for detail; no stock or document changes are made here.",
  };
}

function actionCenterPayload() {
  const card = (key, title, value, note, routePart = "", buttonLabel = "Open queue", targetSection = "", statusLabel = "", cardRole = "queue", roleLabel = "") => {
    const payload = {
      key,
      title,
      value,
      note,
      state: routePart ? "live" : targetSection ? "hub" : "custom_workflow",
      card_role: cardRole,
      role_label: roleLabel || (cardRole === "queue" ? "Review queue" : cardRole === "visibility" ? "Read-only" : "Custom workflow"),
      status_label: statusLabel || (routePart ? "Review queue" : targetSection ? "Custom hub" : "Custom workflow"),
    };
    if (routePart) {
      payload.route = "warehouse-console-worklist";
      payload.route_part = routePart;
      payload.button_label = buttonLabel;
    }
    if (targetSection) {
      payload.target_section = targetSection;
      payload.button_label = buttonLabel;
    }
    return payload;
  };
  return {
    key: "w15b_action_center",
    title: "Warehouse Command Center",
    subtitle: "Start governed Warehouse work, open review pages, and inspect visibility routes without leaving custom workflow boundaries.",
    mode: "custom_workflow",
    mode_label: "Custom records only",
    state: "active",
    role_mode: "manager",
    sections: [
      {
        key: "work_entry",
        title: "Start Work",
        summary: "Open the page where the Warehouse user records or reviews custom workflow evidence.",
        cards: [
          card("arrival_checks", "Arrival checks", 2, "Supplier arrivals and count review start from the inbound queue.", "inbound-receiving", "Open inbound", "", "Review queue", "queue", "Queue"),
          card("picking_work", "Picking work", 2, "Customer demand and stock blockers start from the outbound queue.", "outbound-picking", "Open picking", "", "Review queue", "queue", "Queue"),
          card("return_intake", "Returns Work Hub", "Custom", "Customer and supplier returns continue in the dedicated Returns Work Hub.", "returns-work-hub", "Open returns", "", "Returns page", "custom_workflow", "Custom workflow"),
          card("internal_transfer", "Internal transfer", "Custom", "Transfer intent and source count evidence continue on the dedicated Internal Transfer page.", "internal-transfer-workflow", "Open transfer", "", "Transfer page", "custom_workflow", "Custom workflow"),
          card("cycle_counts", "Cycle Count", "Custom", "Blind count evidence and variance posture continue on the dedicated Cycle Count page.", "cycle-count-workflow", "Open cycle count", "", "Cycle Count page", "custom_workflow", "Custom workflow"),
        ],
      },
      {
        key: "manager_decisions",
        title: "Manager Review",
        summary: "Open review queues and workflow pages; manager actions appear only after custom evidence exists.",
        cards: [
          card("arrival_review", "Arrival review", 2, "Review supplier-side arrivals before any separate receiving document step.", "inbound-receiving", "Review arrivals"),
          card("picking_blockers", "Picking blockers", 2, "Review outbound demand and shortage blockers before release posture.", "outbound-picking", "Review blockers"),
          card("exception_resolution", "Exception resolution", 1, "Shortage and posture issues stay inside custom Warehouse review routes.", "stock-exceptions", "Review exceptions"),
          card("return_decisions", "Return decisions", "Custom", "Manager return posture stays inside the Returns Work Hub; separate handoff requests remain outside this active page.", "returns-work-hub", "Open returns", "", "Returns", "custom_workflow", "Workflow page"),
          card("internal_transfer_decisions", "Transfer decisions", "Custom", "Manager transfer posture stays inside the Internal Transfer page.", "internal-transfer-workflow", "Open transfer", "", "Transfer", "custom_workflow", "Workflow page"),
          card("inventory_variance", "Inventory variance", "Custom", "Manager variance posture stays inside the dedicated Cycle Count page; adjustment documents remain blocked.", "cycle-count-workflow", "Open cycle count", "", "Cycle Count", "custom_workflow", "Workflow page"),
        ],
      },
      {
        key: "visibility",
        title: "Visibility",
        summary: "Inspect posted movement and transfer posture without opening native ERP document routes.",
        cards: [
          card("movement_visibility", "Movement visibility", 1, "Trace posted movement evidence and item posture from the custom visibility page.", "movement-visibility", "Open movements", "", "Visibility", "visibility", "Read-only"),
          card("transfer_visibility", "Transfer visibility", 1, "Review inter-warehouse movement posture before any separate transfer action policy.", "transfer-visibility", "Review transfers", "", "Visibility", "visibility", "Read-only"),
        ],
      },
    ],
    guardrail: {
      title: "Custom workflow only",
      detail: "No ERPNext stock document is created here. Cards open custom Warehouse workflows or review queues only.",
    },
  };
}

function workflowBasePayload(key, title) {
  return {
    workspace: workspacePayload(),
    context: sidebarPayload().context,
    state: { kind: "ready", title: `${title} ready`, detail: "Custom Warehouse workflow state is available." },
    navigation: { items: sidebarItems() },
    sidebar: sidebarPayload().sidebar,
    page: { title, key },
    workflow: { key, record_recall_only: true, records: {}, selected: {}, manager: { can_manage: true, can_manage_customer: true, can_manage_supplier: true } },
    native_routes: [],
    stock_effect: false,
    stock_moved: false,
    stock_quantity_adjusted: false,
    stock_posted: false,
    stock_entry_created: false,
    stock_reconciliation_created: false,
    stock_ledger_updated: false,
    stock_balance_updated: false,
    valuation: { visible: false, fields: [] },
    fetched_at: "2026-05-30 09:00:00",
  };
}

function returnsWorkHubPayload() {
  const payload = workflowBasePayload("returns_work_hub", "Returns Work Hub");
  const customerRecords = workflowRecallState.customerReturnIntake ? [workflowRecallState.customerReturnIntake] : [];
  const supplierRecords = workflowRecallState.supplierReturnCandidate ? [workflowRecallState.supplierReturnCandidate] : [];
  payload.workflow.records = { customer_intakes: customerRecords, supplier_candidates: supplierRecords };
  payload.workflow.selected = { customer_intake: customerRecords[0] || {}, supplier_candidate: supplierRecords[0] || {} };
  return payload;
}

function internalTransferWorkflowPayload() {
  const payload = workflowBasePayload("internal_transfer_workflow", "Internal Transfer Workflow");
  const records = workflowRecallState.internalTransferCandidate ? [workflowRecallState.internalTransferCandidate] : [];
  payload.workflow.records = { candidates: records };
  payload.workflow.selected = { candidate: records[0] || {} };
  return payload;
}

function cycleCountWorkflowPayload() {
  const payload = workflowBasePayload("cycle_count_workflow", "Cycle Count Workflow");
  const records = workflowRecallState.cycleCountTask ? [workflowRecallState.cycleCountTask] : [];
  payload.workflow.records = { tasks: records };
  payload.workflow.selected = { task: records[0] || {} };
  return payload;
}

function overviewPayload() {
  return {
    workspace: workspacePayload(),
    context: sidebarPayload().context,
    state: { kind: "ready", title: "Warehouse Console ready", detail: "Warehouse cockpit is available." },
    navigation: { items: sidebarItems() },
    sidebar: sidebarPayload().sidebar,
    kpis: [
      { key: "active_warehouses", label: "Active Warehouses", value: 4, note: "Warehouse locations available for stock review.", state: "live" },
      { key: "stocked_items", label: "Stocked Items", value: 8, note: "Item and warehouse positions with stock on hand.", state: "live" },
      { key: "low_stock", label: "Low Stock", value: 1, note: "Projected quantity below zero.", state: "live" },
      { key: "receiving_due", label: "Receiving Due", value: 1, note: "Supplier-side review due today.", state: "live" },
      { key: "outbound_due", label: "Picking Due", value: 1, note: "Customer-side review due today.", state: "live" },
      { key: "transfer_requests", label: "Movement Watch", value: 2, note: "Movement visibility records.", state: "live" },
    ],
    sections: [],
    inbound: { ...inboundPayload(), cards: inboundPayload().cards, preview_rows: inboundPayload().rows, counts: { overdue: 1, due_today: 1, partially_received: 1, expected_soon: 2 } },
    outbound: { ...outboundPayload(), cards: outboundPayload().cards, preview_rows: outboundPayload().rows, counts: { overdue: 0, due_today: 1, short_stock: 1, expected_soon: 2 } },
    stock_exceptions: stockExceptionsPayload(),
    action_center: actionCenterPayload(),
    manager_center: EXPECT_W14C ? managerCenterPayload() : { visible: false, state: "hidden", groups: [], cards: [] },
    allowed_actions: [{ key: "refresh", label: "Refresh", kind: "read_only" }],
    action_targets: {},
    fetched_at: "2026-05-30 09:00:00",
  };
}

function quickFindPayload() {
  const receivingTarget = { kind: "warehouse_page", route: "warehouse-console-receiving", route_parts: ["PO-W14B-1"] };
  const pickingTarget = { kind: "warehouse_page", route: "warehouse-console-picking", route_parts: ["SO-W14B-1"] };
  const postureTarget = { kind: "warehouse_page", route: "warehouse-console-stock-posture", context_token: "7b226974656d5f636f6465223a224954454d2d57313442222c2277617265686f757365223a224d61696e202d204d227d" };
  const movementTarget = { kind: "warehouse_page", route: "warehouse-console-movement", context_token: "7b226d6f76656d656e745f6964223a224d41542d573134422d31227d" };
  const results = [
    {
      id: "receiving:PO-W14B-1",
      result_type: "receiving",
      group_key: "receiving",
      group: "Inbound Receiving",
      doctype: "Purchase Order",
      name: "PO-W14B-1",
      title: "PO-W14B-1",
      subtitle: "Quick Find Supplier",
      meta: "Open the custom Warehouse receiving review. No Purchase Receipt is created.",
      target: receivingTarget,
      primary_action_label: "Open receiving review",
      preview: {
        title: "PO-W14B-1",
        subtitle: "Quick Find Supplier",
        chips: ["Receiving"],
        facts: [
          { label: "Supplier", value: "Quick Find Supplier" },
          { label: "Expected", value: "2026-06-15" },
          { label: "Warehouse", value: "Main - M" },
        ],
        boundary_note: "Open the custom Warehouse receiving review. No Purchase Receipt is created.",
        target: receivingTarget,
        primary_action_label: "Open receiving review",
      },
    },
    {
      id: "picking:SO-W14B-1",
      result_type: "picking",
      group_key: "picking",
      group: "Outbound Picking",
      doctype: "Sales Order",
      name: "SO-W14B-1",
      title: "SO-W14B-1",
      subtitle: "Quick Find Customer",
      meta: "Open the custom Warehouse picking review. No Pick List or Delivery Note is created.",
      target: pickingTarget,
      primary_action_label: "Open picking review",
      preview: {
        title: "SO-W14B-1",
        subtitle: "Quick Find Customer",
        chips: ["Picking"],
        facts: [
          { label: "Customer", value: "Quick Find Customer" },
          { label: "Delivery", value: "2026-06-15" },
          { label: "Warehouse", value: "Main - M" },
        ],
        boundary_note: "Open the custom Warehouse picking review. No Pick List or Delivery Note is created.",
        target: pickingTarget,
        primary_action_label: "Open picking review",
      },
    },
    {
      id: "stock_posture:ITEM-W14B:Main - M",
      result_type: "stock_posture",
      group_key: "stock_posture",
      group: "Stock Posture",
      doctype: "Bin",
      name: "ITEM-W14B:Main - M",
      title: "ITEM-W14B",
      subtitle: "Main - M",
      meta: "Open the custom Warehouse stock posture review.",
      target: postureTarget,
      primary_action_label: "Review stock posture",
      preview: {
        title: "ITEM-W14B",
        subtitle: "Main - M",
        chips: ["Read-only posture"],
        facts: [{ label: "Warehouse", value: "Main - M" }, { label: "Actual", value: "12" }],
        boundary_note: "Open the custom Warehouse stock posture review. No Stock Ledger page is opened.",
        target: postureTarget,
        primary_action_label: "Review stock posture",
      },
    },
    {
      id: "movement:MAT-W14B-1",
      result_type: "movement",
      group_key: "movements",
      group: "Movement Review",
      doctype: "Stock Entry",
      name: "MAT-W14B-1",
      title: "MAT-W14B-1",
      subtitle: "Material Transfer",
      meta: "Open the custom Warehouse movement review.",
      target: movementTarget,
      primary_action_label: "Review movement",
      preview: {
        title: "MAT-W14B-1",
        subtitle: "Material Transfer",
        chips: ["Posted movement"],
        facts: [{ label: "Posted", value: "2026-06-15" }, { label: "Source", value: "Stores - M" }, { label: "Target", value: "Main - M" }],
        boundary_note: "Open the custom Warehouse movement review. No Stock Entry action is available.",
        target: movementTarget,
        primary_action_label: "Review movement",
      },
    },
  ];
  const groups = [
    { key: "receiving", label: "Inbound Receiving", results: [results[0]] },
    { key: "picking", label: "Outbound Picking", results: [results[1]] },
    { key: "stock_posture", label: "Stock Posture", results: [results[2]] },
    { key: "movements", label: "Movement Review", results: [results[3]] },
  ];
  return {
    state: "ready",
    query: "W14B",
    message: "4 visible Warehouse results found.",
    groups,
    results,
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
      assertWarehouseHandoffCopyIsPostureOnly(body, file);
      if (body) return route.fulfill({ status: 200, body, contentType: "application/javascript" });
      return route.continue();
    });
  }
  await context.route("**/api/method/frappe.desk.desk_page.getpage**", async (route) => {
    const request = route.request();
    const text = requestText(request);
    if (!/warehouse-console/i.test(text)) return route.continue();
    const pageSources = [
      ["warehouse-console-receiving", "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_receiving/warehouse_console_receiving.js"],
      ["warehouse-console-picking", "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_picking/warehouse_console_picking.js"],
      ["warehouse-console-stock-exception", "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_stock_exception/warehouse_console_stock_exception.js"],
      ["warehouse-console-stock-posture", "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_stock_posture/warehouse_console_stock_posture.js"],
      ["warehouse-console-movement", "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_movement/warehouse_console_movement.js"],
      ["warehouse-console-worklist", "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/warehouse_console_worklist.js"],
      ["warehouse-console", "erp_workspace_ui/erp_workspace_ui/page/warehouse_console/warehouse_console.js"],
    ];
    const match = pageSources.find(([pageName]) => new RegExp(pageName, "i").test(text)) || pageSources[pageSources.length - 1];
    const [name, file] = match;
    const script = readSource(file);
    recordOverrideHit(diagnostics, "desk-page-getpage", request, { fulfilled: Boolean(script), page: name });
    const pageDoc = { doctype: "Page", name, page_name: name, title: "Warehouse Console", module: "ERP Workspace UI", standard: "Yes", content: "", script };
    return route.fulfill({ status: script ? 200 : 404, contentType: "application/json", body: JSON.stringify({ docs: [pageDoc], message: pageDoc }) });
  });
  const methodPayloads = [
    ["get_warehouse_console_overview", "warehouse-overview", () => overviewPayload()],
    ["get_warehouse_returns_work_hub", "warehouse-returns-work-hub", () => returnsWorkHubPayload()],
    ["get_warehouse_internal_transfer_workflow", "warehouse-internal-transfer-workflow", () => internalTransferWorkflowPayload()],
    ["get_warehouse_cycle_count_workflow", "warehouse-cycle-count-workflow", () => cycleCountWorkflowPayload()],
    ["get_warehouse_console_sidebar_context", "warehouse-sidebar", () => sidebarPayload()],
    ["get_warehouse_inbound_receiving_queue", "warehouse-inbound", () => inboundPayload()],
    ["get_warehouse_outbound_picking_queue", "warehouse-outbound", () => outboundPayload()],
    ["get_warehouse_stock_exceptions", "warehouse-stock-exceptions", () => stockExceptionsPayload()],
    ["get_warehouse_movement_visibility_queue", "warehouse-movement-visibility", () => movementPayload()],
    ["get_warehouse_transfer_visibility_queue", "warehouse-transfer-visibility", () => transferPayload()],
    ["search_warehouse_console_workspace", "warehouse-quick-find", () => quickFindPayload()],
    ["get_warehouse_quick_find_suggestions", "warehouse-quick-find", () => quickFindPayload()],
    ["save_warehouse_customer_return_intake_draft", "customer-return-intake-draft", () => {
      workflowRecallState.customerReturnIntake = { intake_id: "WH-CR-W16D3-0001", intake_status: "Draft", manager_review_status: "Draft", customer: "W16D3 Customer", warehouse: "Yangon Main Warehouse - MMOB", line_count: 1, request_id: "w16d3-smoke" };
      return {
        intake: { intake_id: "WH-CR-W16D3-0001", status: "Draft" },
        no_effect: { stock_increased: false, sales_return_created: false, credit_note_created: false, delivery_note_created: false },
      };
    }],
    ["save_warehouse_supplier_return_candidate_draft", "supplier-return-candidate-draft", () => {
      workflowRecallState.supplierReturnCandidate = { candidate_id: "WH-SR-W16D4-0001", candidate_status: "Candidate Draft", manager_review_status: "Candidate Draft", supplier: "W16D4 Supplier", warehouse: "Yangon Main Warehouse - MMOB", line_count: 1, request_id: "w16d4-smoke" };
      return {
        candidate: { candidate_id: "WH-SR-W16D4-0001", candidate_status: "Candidate Draft" },
        no_effect: { stock_decreased: false, return_purchase_receipt_created: false, purchase_invoice_return_created: false, debit_note_created: false },
      };
    }],
    ["save_warehouse_internal_transfer_candidate_draft", "internal-transfer-candidate-draft", () => {
      workflowRecallState.internalTransferCandidate = { candidate_id: "WH-IT-W16E-0001", candidate_status: "Draft", manager_review_status: "Draft", source_warehouse: "Yangon Main Warehouse - MMOB", target_warehouse: "Target Warehouse - W16E", source_context: "warehouse_rebalance", line_count: 1, total_candidate_qty: "1", request_id: "w16e-smoke" };
      return {
        candidate: { candidate_id: "WH-IT-W16E-0001", candidate_status: "Draft" },
        stock_effect: false,
        stock_moved: false,
        stock_entry_created: false,
        stock_ledger_updated: false,
        stock_balance_updated: false,
      };
    }],
    ["save_warehouse_cycle_count_task_draft", "cycle-count-task-draft", () => {
      workflowRecallState.cycleCountTask = { task_id: "WH-CC-W16F-0001", count_status: "Count In Progress", manager_review_status: "Count In Progress", variance_status: "No variance", warehouse: "Yangon Main Warehouse - MMOB", count_source: "spot_count", count_scope: "item_specific", line_count: 1, request_id: "w16f-smoke" };
      return {
        task: { task_id: "WH-CC-W16F-0001", count_status: "Count In Progress" },
        stock_effect: false,
        stock_quantity_adjusted: false,
        stock_reconciliation_created: false,
        stock_entry_created: false,
        stock_ledger_updated: false,
        stock_balance_updated: false,
      };
    }],
    ["save_warehouse_cycle_count_manager_decision", "cycle-count-manager-decision", () => ({
      task: { task_id: "WH-CC-W16F-0001", count_status: "Clean Count", manager_review_status: "Clean Count" },
      decision: { decision: "mark_clean_count" },
      stock_effect: false,
      stock_quantity_adjusted: false,
      stock_reconciliation_created: false,
      stock_entry_created: false,
      stock_ledger_updated: false,
      stock_balance_updated: false,
    })],
    ["save_warehouse_customer_return_manager_decision", "customer-return-manager-decision", () => ({
      status: "Restock Candidate",
      intake: { intake_id: "WH-CR-W16D3-0001", intake_status: "Restock Candidate" },
      event_summary: { event_type: "marked_restock_candidate" },
      no_effect: { stock_increased: false, sales_return_created: false, credit_note_created: false, delivery_note_created: false },
    })],
    ["save_warehouse_supplier_return_manager_decision", "supplier-return-manager-decision", () => ({
      status: "Supplier Return Candidate",
      candidate: { candidate_id: "WH-SR-W16D4-0001", candidate_status: "Supplier Return Candidate" },
      event_summary: { event_type: "marked_supplier_return_candidate" },
      no_effect: { stock_decreased: false, return_purchase_receipt_created: false, purchase_invoice_return_created: false, debit_note_created: false },
    })],
  ];
  for (const [method, key, payload] of methodPayloads) {
    await context.route(`**/api/method/erp_workspace_ui.warehouse_console.service.${method}**`, async (route) => {
      recordOverrideHit(diagnostics, key, route.request(), { fulfilled: true });
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ message: payload() }) });
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

async function waitForCockpit(page) {
  await page.waitForFunction(() => {
    const shell = document.querySelector('.sales-console-shell[data-erpw-workspace="warehouse"][data-warehouse-cockpit="ready"]');
    return Boolean(shell && shell.querySelector("[data-warehouse-cockpit-command]") && shell.querySelector("[data-warehouse-cockpit-pulse]") && shell.querySelector("[data-warehouse-cockpit-start]") && shell.querySelector("[data-warehouse-action-center]"));
  }, null, { timeout: TIMEOUT });
}

async function waitForWorklist(page, viewName) {
  await page.waitForFunction((expectedView) => {
    const shell = document.querySelector(`.sales-console-shell[data-erpw-workspace="warehouse"][data-warehouse-view="${expectedView}"]`);
    return Boolean(shell && (shell.querySelector("[data-warehouse-inbound-queue-card], [data-warehouse-movement-card], [data-warehouse-stock-exception-card], [data-warehouse-transfer-card], [data-warehouse-returns-hub], [data-warehouse-internal-transfer-workflow], [data-warehouse-cycle-count-workflow]") || shell.querySelector("[data-warehouse-movement-empty], [data-warehouse-stock-exception-empty], [data-warehouse-transfer-empty]")));
  }, viewName, { timeout: TIMEOUT });
}

async function waitForUnsupportedWorklist(page) {
  await page.waitForFunction(() => {
    const shell = document.querySelector('.sales-console-shell[data-erpw-workspace="warehouse"][data-warehouse-unsupported-worklist="true"]');
    return Boolean(shell && shell.querySelector("[data-warehouse-unsupported-worklist-panel]"));
  }, null, { timeout: TIMEOUT });
}

async function waitForWarehouseRouteFirstPaint(page, contextLabel) {
  await page.waitForFunction(() => {
    const selectors = [
      "[data-warehouse-route-loading]",
      ".sales-console-shell[data-erpw-workspace='warehouse']",
      ".warehouse-receiving-shell[data-warehouse-view='receiving-review']",
      ".warehouse-picking-shell[data-warehouse-view='picking-review']",
      "[data-warehouse-unsupported-worklist='true']",
    ];
    return selectors.some((selector) => Boolean(document.querySelector(selector)));
  }, null, { timeout: Math.min(TIMEOUT, 5000) });
  const firstPaint = await page.evaluate(() => {
    const visible = (node) => {
      if (!node) return false;
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
    };
    return {
      loadingShells: Array.from(document.querySelectorAll("[data-warehouse-route-loading]")).filter(visible).length,
      finalShells: Array.from(document.querySelectorAll(".sales-console-shell[data-erpw-workspace='warehouse'], .warehouse-receiving-shell[data-warehouse-view='receiving-review'], .warehouse-picking-shell[data-warehouse-view='picking-review']")).filter(visible).length,
      bodyText: (document.body && document.body.innerText || "").replace(/\s+/g, " ").trim().slice(0, 220),
    };
  });
  assert(firstPaint.loadingShells + firstPaint.finalShells > 0, "Warehouse route showed a blank first paint", { context: contextLabel, firstPaint });
}

async function waitForOverrideHit(diagnostics, key) {
  const deadline = Date.now() + TIMEOUT;
  while (Date.now() < deadline) {
    if (diagnostics.overrideHits.some((hit) => hit.key === key)) return;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`Expected source override was not used: ${key}`);
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

async function openRoute(page, routeParts, pathName, wait) {
  const canRoute = await page.evaluate(() => Boolean(window.frappe && typeof frappe.set_route === "function")).catch(() => false);
  if (canRoute) {
    await page.evaluate((parts) => frappe.set_route(...parts), routeParts);
    await page.waitForURL((url) => url.pathname === pathName || url.pathname === `/app/${routeParts.join("/")}`, { timeout: TIMEOUT });
  } else {
    await page.goto(routeUrl(pathName), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  }
  await waitForWarehouseRouteFirstPaint(page, routeParts.join("/"));
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
    const routeTargets = Array.from((shell || document).querySelectorAll("[data-warehouse-cockpit-route-target]")).map((node) => node.getAttribute("data-warehouse-cockpit-route-target") || "").filter(Boolean);
    const sidebarLabels = Array.from(document.querySelectorAll('[data-erpw-sidebar-workspace="warehouse"] [data-erpw-sidebar-index]')).filter(visible).map((node) => (node.innerText || node.getAttribute("aria-label") || "").replace(/\s+/g, " ").trim()).filter(Boolean);
    const sidebarDuplicates = sidebarLabels.filter((label, index) => sidebarLabels.indexOf(label) !== index);
    const pageHeadText = Array.from(document.querySelectorAll(".page-head, .page-head-content, .title-area")).filter(visible).map((node) => (node.innerText || "").replace(/\s+/g, " ").trim()).filter((value) => /Warehouse Console|Warehouse Cockpit/i.test(value));
    return {
      url: location.href,
      route: window.frappe && typeof frappe.get_route === "function" ? frappe.get_route() : null,
      text,
      actionText,
      hrefs,
      routeTargets,
      sidebarLabels,
      sidebarDuplicates,
      warehousePageHeadCount: pageHeadText.length,
      allPageHeadCount: Array.from(document.querySelectorAll(".page-head")).filter(visible).length,
      shellCount: Array.from(document.querySelectorAll('.sales-console-shell[data-erpw-workspace="warehouse"]')).filter(visible).length,
      unsupportedWorklistCount: Array.from(document.querySelectorAll("[data-warehouse-unsupported-worklist]")).filter(visible).length,
      unsupportedWorklistPanelCount: Array.from(document.querySelectorAll("[data-warehouse-unsupported-worklist-panel]")).filter(visible).length,
      unsupportedWorklistOverviewActionCount: Array.from(document.querySelectorAll("[data-warehouse-unsupported-overview]")).filter(visible).length,
      headerCount: Array.from(document.querySelectorAll(".warehouse-console-header, .warehouse-inbound-queue-header, .warehouse-receiving-header")).filter(visible).length,
      cockpitCount: Array.from(document.querySelectorAll("[data-warehouse-cockpit='ready']")).filter(visible).length,
      commandCount: Array.from(document.querySelectorAll("[data-warehouse-cockpit-command]")).filter(visible).length,
      commandChipCount: Array.from(document.querySelectorAll("[data-warehouse-cockpit-command-chip]")).filter(visible).length,
      pulseCount: Array.from(document.querySelectorAll("[data-warehouse-cockpit-pulse-card]")).filter(visible).length,
      startCount: Array.from(document.querySelectorAll("[data-warehouse-cockpit-start-card]")).filter(visible).length,
      startCardKeys: Array.from(document.querySelectorAll("[data-warehouse-cockpit-start-card]")).filter(visible).map((node) => node.getAttribute("data-warehouse-cockpit-start-card") || "").filter(Boolean),
      startRouteTargets: Array.from(document.querySelectorAll("[data-warehouse-cockpit-start-card]")).filter(visible).map((node) => node.getAttribute("data-warehouse-cockpit-route-target") || "").filter(Boolean),
      workCount: Array.from(document.querySelectorAll("[data-warehouse-cockpit-work] .warehouse-console-inbound-panel")).filter(visible).length,
      riskCount: Array.from(document.querySelectorAll("[data-warehouse-cockpit-risk] [data-warehouse-cockpit-route-card]")).filter(visible).length,
      movementCount: Array.from(document.querySelectorAll("[data-warehouse-cockpit-movement] [data-warehouse-cockpit-route-card]")).filter(visible).length,
      legacyRouteSectionCount: Array.from(document.querySelectorAll("[data-warehouse-cockpit-work], [data-warehouse-cockpit-risk], [data-warehouse-cockpit-movement]")).filter(visible).length,
      guardrailCount: Array.from(document.querySelectorAll("[data-warehouse-cockpit-guardrail]")).filter(visible).length,
      inboundActionCount: Array.from(document.querySelectorAll("[data-warehouse-open-inbound]")).filter(visible).length,
      outboundActionCount: Array.from(document.querySelectorAll("[data-warehouse-open-outbound]")).filter(visible).length,
      stockExceptionActionCount: Array.from(document.querySelectorAll("[data-warehouse-open-stock-exceptions]")).filter(visible).length,
      movementActionCount: Array.from(document.querySelectorAll("[data-warehouse-open-movement]")).filter(visible).length,
      transferActionCount: Array.from(document.querySelectorAll("[data-warehouse-open-transfer]")).filter(visible).length,
      refreshActionCount: Array.from(document.querySelectorAll("[data-warehouse-refresh]")).filter(visible).length,
      quickFindCount: Array.from(document.querySelectorAll("[data-warehouse-quick-find]")).filter(visible).length,
      quickFindInputVisible: Array.from(document.querySelectorAll("[data-warehouse-quick-find-input]")).some(visible),
      quickFindOptionCount: Array.from(document.querySelectorAll("[data-warehouse-quick-find-option]")).filter(visible).length,
      quickFindPreviewVisible: Array.from(document.querySelectorAll("[data-warehouse-quick-find-preview]")).some(visible),
      managerCenterCount: Array.from(document.querySelectorAll("[data-warehouse-manager-center]")).filter(visible).length,
      managerCenterCardCount: Array.from(document.querySelectorAll("[data-warehouse-manager-center-card]")).filter(visible).length,
      managerCenterGroupCount: Array.from(document.querySelectorAll("[data-warehouse-manager-center-group]")).filter(visible).length,
      managerCenterItemCount: Array.from(document.querySelectorAll("[data-warehouse-manager-center-item]")).filter(visible).length,
      managerCenterActionCount: Array.from(document.querySelectorAll("[data-warehouse-manager-center-open]")).filter(visible).length,
      actionCenterCount: Array.from(document.querySelectorAll("[data-warehouse-action-center]")).filter(visible).length,
      actionCenterGroupCount: Array.from(document.querySelectorAll("[data-warehouse-action-center-group]")).filter(visible).length,
      actionCenterGroupKeys: Array.from(document.querySelectorAll("[data-warehouse-action-center-group]")).filter(visible).map((node) => node.getAttribute("data-warehouse-action-center-group") || "").filter(Boolean),
      actionCenterCardCount: Array.from(document.querySelectorAll("[data-warehouse-action-center-card]")).filter(visible).length,
      actionCenterCardKeys: Array.from(document.querySelectorAll("[data-warehouse-action-center-card]")).filter(visible).map((node) => node.getAttribute("data-warehouse-action-center-card") || "").filter(Boolean),
      actionCenterCardRoles: Array.from(document.querySelectorAll("[data-warehouse-action-center-card]")).filter(visible).map((node) => node.getAttribute("data-warehouse-action-center-card-role") || "").filter(Boolean),
      actionCenterRouteTargets: Array.from(document.querySelectorAll("[data-warehouse-action-center-card]")).filter(visible).map((node) => node.getAttribute("data-warehouse-cockpit-route-target") || "").filter(Boolean),
      actionCenterOpenCount: Array.from(document.querySelectorAll("[data-warehouse-action-center-open]")).filter(visible).length,
      actionCenterRoleBadgeCount: Array.from(document.querySelectorAll(".warehouse-action-center-role-badge")).filter(visible).length,
      actionCenterCustomMetricCount: Array.from(document.querySelectorAll("[data-warehouse-action-center-role='custom_workflow'] .sales-console-queue-count")).filter(visible).length,
      actionCenterVisibilityCount: Array.from(document.querySelectorAll("[data-warehouse-action-center-card-role='visibility']")).filter(visible).length,
      actionCenterCustomWorkflowCount: Array.from(document.querySelectorAll("[data-warehouse-action-center-card-role='custom_workflow']")).filter(visible).length,
      actionCenterGuardrailCount: Array.from(document.querySelectorAll("[data-warehouse-action-center-guardrail]")).filter(visible).length,
      actionCenterModes: Array.from(document.querySelectorAll("[data-warehouse-action-center-mode]")).map((node) => node.getAttribute("data-warehouse-action-center-mode") || "").filter(Boolean),
      actionCenterTargetSections: Array.from(document.querySelectorAll("[data-warehouse-action-center-target-section]")).map((node) => node.getAttribute("data-warehouse-action-center-target-section") || "").filter(Boolean),
      returnsOverviewSummaryCount: Array.from(document.querySelectorAll("[data-warehouse-returns-overview-summary]")).filter(visible).length,
      returnsOverviewSummaryCardCount: Array.from(document.querySelectorAll("[data-warehouse-returns-summary-card]")).filter(visible).length,
      returnsOverviewOpenCount: Array.from(document.querySelectorAll("[data-warehouse-returns-overview-open]")).filter(visible).length,
      returnsOpenRouteCount: Array.from(document.querySelectorAll("[data-warehouse-open-returns]")).filter(visible).length,
      returnsOverviewSaveClassCount: Array.from(document.querySelectorAll("[data-warehouse-returns-overview-open].warehouse-return-intake-save")).filter(visible).length,
      cycleCountOverviewSummaryCount: Array.from(document.querySelectorAll("[data-warehouse-cycle-count-overview-summary]")).filter(visible).length,
      cycleCountOverviewSummaryCardCount: Array.from(document.querySelectorAll("[data-warehouse-cycle-count-summary-card]")).filter(visible).length,
      cycleCountOverviewOpenCount: Array.from(document.querySelectorAll("[data-warehouse-cycle-count-overview-open]")).filter(visible).length,
      workflowPageShellCount: Array.from(document.querySelectorAll("[data-warehouse-workflow-page-shell]")).filter(visible).length,
      workflowPageShellKeys: Array.from(document.querySelectorAll("[data-warehouse-workflow-page-shell]")).filter(visible).map((node) => node.getAttribute("data-warehouse-workflow-page-shell") || "").filter(Boolean),
      workflowPageHeaderCount: Array.from(document.querySelectorAll("[data-warehouse-workflow-page-header]")).filter(visible).length,
      workflowCardCount: Array.from(document.querySelectorAll("[data-warehouse-workflow-card]")).filter(visible).length,
      workflowCardKinds: Array.from(document.querySelectorAll("[data-warehouse-workflow-card]")).filter(visible).map((node) => node.getAttribute("data-warehouse-workflow-kind") || "").filter(Boolean),
      workflowModeCount: Array.from(document.querySelectorAll("[data-warehouse-workflow-mode]")).filter(visible).length,
      workflowGuardrailCount: Array.from(document.querySelectorAll("[data-warehouse-workflow-guardrail]")).filter(visible).length,
      workflowBodyCount: Array.from(document.querySelectorAll("[data-warehouse-workflow-body]")).filter(visible).length,
      workflowPanelCount: Array.from(document.querySelectorAll("[data-warehouse-workflow-panel]")).filter(visible).length,
      returnsPageErrorCount: Array.from(document.querySelectorAll("[data-warehouse-returns-page-error]")).filter(visible).length,
      returnsHubCount: Array.from(document.querySelectorAll("[data-warehouse-returns-hub]")).filter(visible).length,
      returnsHubLaneCount: Array.from(document.querySelectorAll("[data-warehouse-returns-hub-lane]")).filter(visible).length,
      returnsHubSwitchCount: Array.from(document.querySelectorAll("[data-warehouse-returns-hub-switch]")).filter(visible).length,
      returnsHubSelectedLaneKeys: Array.from(document.querySelectorAll("[data-warehouse-returns-hub-switch][aria-selected='true']")).filter(visible).map((node) => node.getAttribute("data-warehouse-returns-hub-switch") || "").filter(Boolean),
      returnsHubVisiblePanelKeys: Array.from(document.querySelectorAll("[data-warehouse-returns-workbench-panel]")).filter(visible).map((node) => node.getAttribute("data-warehouse-returns-workbench-panel") || "").filter(Boolean),
      returnsHubGuardrailCount: Array.from(document.querySelectorAll("[data-warehouse-returns-hub-guardrail]")).filter(visible).length,
      returnsHubActiveControlCount: Array.from(document.querySelectorAll("[data-warehouse-returns-hub] button, [data-warehouse-returns-hub] a, [data-warehouse-returns-hub] [role=button]")).filter((node) => visible(node) && !node.disabled && node.getAttribute("aria-disabled") !== "true").length,
      customerReturnIntakeLaneCount: Array.from(document.querySelectorAll("[data-warehouse-customer-return-intake-lane]")).filter(visible).length,
      customerReturnIntakePanelCount: Array.from(document.querySelectorAll("[data-warehouse-customer-return-intake-panel]")).filter(visible).length,
      customerReturnIntakeFieldCount: Array.from(document.querySelectorAll("[data-warehouse-customer-return-field]")).filter(visible).length,
      customerReturnIntakeSaveCount: Array.from(document.querySelectorAll("[data-warehouse-customer-return-save]")).filter(visible).length,
      supplierReturnHubActiveControlCount: Array.from(document.querySelectorAll("[data-warehouse-returns-workbench-panel='supplier'] button, [data-warehouse-returns-workbench-panel='supplier'] a, [data-warehouse-returns-workbench-panel='supplier'] [role=button]")).filter((node) => visible(node) && !node.disabled && node.getAttribute("aria-disabled") !== "true").length,
      supplierReturnCandidateLaneCount: Array.from(document.querySelectorAll("[data-warehouse-supplier-return-candidate-lane]")).filter(visible).length,
      supplierReturnCandidatePanelCount: Array.from(document.querySelectorAll("[data-warehouse-supplier-return-candidate-panel]")).filter(visible).length,
      supplierReturnCandidateFieldCount: Array.from(document.querySelectorAll("[data-warehouse-supplier-return-field]")).filter(visible).length,
      supplierReturnCandidateSaveCount: Array.from(document.querySelectorAll("[data-warehouse-supplier-return-save]")).filter(visible).length,
      returnDecisionsHubControlCount: Array.from(document.querySelectorAll("[data-warehouse-return-decision-action]")).length,
      returnDecisionsPanelCount: Array.from(document.querySelectorAll("[data-warehouse-return-decisions-panel]")).filter(visible).length,
      returnDecisionsHubActiveControlCount: Array.from(document.querySelectorAll("[data-warehouse-return-decision-action]")).filter((node) => visible(node) && !node.disabled && node.getAttribute("aria-disabled") !== "true").length,
      plannedWorkflowGroupCount: Array.from(document.querySelectorAll("[data-warehouse-planned-workflows]")).filter(visible).length,
      plannedWorkflowCardCount: Array.from(document.querySelectorAll("[data-warehouse-planned-workflow-card]")).filter(visible).length,
      plannedWorkflowToggleCount: Array.from(document.querySelectorAll("[data-warehouse-planned-workflow-toggle]")).filter(visible).length,
      plannedWorkflowVisibleDetailCount: Array.from(document.querySelectorAll("[data-warehouse-planned-workflow-detail]")).filter(visible).length,
      plannedWorkflowExpandedKeys: Array.from(document.querySelectorAll("[data-warehouse-planned-workflow-detail]")).filter(visible).map((node) => node.getAttribute("data-warehouse-planned-workflow-detail") || "").filter(Boolean),
      customerReturnShellCount: Array.from(document.querySelectorAll("[data-warehouse-customer-return-shell]")).filter(visible).length,
      customerReturnStatusCount: Array.from(document.querySelectorAll("[data-warehouse-customer-return-status]")).filter(visible).length,
      customerReturnUserPreviewCount: Array.from(document.querySelectorAll("[data-warehouse-customer-return-user-preview]")).filter(visible).length,
      customerReturnManagerPreviewCount: Array.from(document.querySelectorAll("[data-warehouse-customer-return-manager-preview]")).filter(visible).length,
      customerReturnEvidencePreviewCount: Array.from(document.querySelectorAll("[data-warehouse-customer-return-evidence-preview]")).filter(visible).length,
      customerReturnPolicyCount: Array.from(document.querySelectorAll("[data-warehouse-customer-return-policy]")).filter(visible).length,
      customerReturnActiveControlCount: Array.from(document.querySelectorAll("[data-warehouse-customer-return-shell] button, [data-warehouse-customer-return-shell] a, [data-warehouse-customer-return-shell] [role=button]")).filter(visible).length,
      supplierReturnShellCount: Array.from(document.querySelectorAll("[data-warehouse-supplier-return-shell]")).filter(visible).length,
      supplierReturnStatusCount: Array.from(document.querySelectorAll("[data-warehouse-supplier-return-status]")).filter(visible).length,
      supplierReturnUserPreviewCount: Array.from(document.querySelectorAll("[data-warehouse-supplier-return-user-preview]")).filter(visible).length,
      supplierReturnManagerPreviewCount: Array.from(document.querySelectorAll("[data-warehouse-supplier-return-manager-preview]")).filter(visible).length,
      supplierReturnEvidencePreviewCount: Array.from(document.querySelectorAll("[data-warehouse-supplier-return-evidence-preview]")).filter(visible).length,
      supplierReturnPolicyCount: Array.from(document.querySelectorAll("[data-warehouse-supplier-return-policy]")).filter(visible).length,
      supplierReturnActiveControlCount: Array.from(document.querySelectorAll("[data-warehouse-supplier-return-shell] button, [data-warehouse-supplier-return-shell] a, [data-warehouse-supplier-return-shell] [role=button]")).filter(visible).length,
      internalTransferWorkflowPageCount: Array.from(document.querySelectorAll("[data-warehouse-internal-transfer-page]")).filter(visible).length,
      internalTransferWorkflowCount: Array.from(document.querySelectorAll("[data-warehouse-internal-transfer-workflow]")).filter(visible).length,
      internalTransferCandidatePanelCount: Array.from(document.querySelectorAll("[data-warehouse-internal-transfer-candidate-panel]")).filter(visible).length,
      internalTransferFieldCount: Array.from(document.querySelectorAll("[data-warehouse-internal-transfer-field]")).filter(visible).length,
      internalTransferSaveCount: Array.from(document.querySelectorAll("[data-warehouse-internal-transfer-save]")).filter(visible).length,
      internalTransferDecisionControlCount: Array.from(document.querySelectorAll("[data-warehouse-internal-transfer-decision-action]")).length,
      internalTransferDecisionActiveControlCount: Array.from(document.querySelectorAll("[data-warehouse-internal-transfer-decision-action]")).filter((node) => visible(node) && !node.disabled && node.getAttribute("aria-disabled") !== "true").length,
      cycleCountWorkflowPageCount: Array.from(document.querySelectorAll("[data-warehouse-cycle-count-page]")).filter(visible).length,
      cycleCountWorkflowCount: Array.from(document.querySelectorAll("[data-warehouse-cycle-count-workflow]")).filter(visible).length,
      cycleCountTaskPanelCount: Array.from(document.querySelectorAll("[data-warehouse-cycle-count-task-panel]")).filter(visible).length,
      cycleCountFieldCount: Array.from(document.querySelectorAll("[data-warehouse-cycle-count-field]")).filter(visible).length,
      cycleCountSaveCount: Array.from(document.querySelectorAll("[data-warehouse-cycle-count-save]")).filter(visible).length,
      cycleCountDecisionControlCount: Array.from(document.querySelectorAll("[data-warehouse-cycle-count-decision-action]")).length,
      cycleCountDecisionActiveControlCount: Array.from(document.querySelectorAll("[data-warehouse-cycle-count-decision-action]")).filter((node) => visible(node) && !node.disabled && node.getAttribute("aria-disabled") !== "true").length,
      internalTransferShellCount: Array.from(document.querySelectorAll("[data-warehouse-internal-transfer-shell]")).filter(visible).length,
      internalTransferStatusCount: Array.from(document.querySelectorAll("[data-warehouse-internal-transfer-status]")).filter(visible).length,
      internalTransferUserPreviewCount: Array.from(document.querySelectorAll("[data-warehouse-internal-transfer-user-preview]")).filter(visible).length,
      internalTransferManagerPreviewCount: Array.from(document.querySelectorAll("[data-warehouse-internal-transfer-manager-preview]")).filter(visible).length,
      internalTransferEvidencePreviewCount: Array.from(document.querySelectorAll("[data-warehouse-internal-transfer-evidence-preview]")).filter(visible).length,
      internalTransferPolicyCount: Array.from(document.querySelectorAll("[data-warehouse-internal-transfer-policy]")).filter(visible).length,
      internalTransferActiveControlCount: Array.from(document.querySelectorAll("[data-warehouse-internal-transfer-shell] button, [data-warehouse-internal-transfer-shell] a, [data-warehouse-internal-transfer-shell] [role=button]")).filter(visible).length,
      cycleCountShellCount: Array.from(document.querySelectorAll("[data-warehouse-cycle-count-shell]")).filter(visible).length,
      cycleCountStatusCount: Array.from(document.querySelectorAll("[data-warehouse-cycle-count-status]")).filter(visible).length,
      cycleCountUserPreviewCount: Array.from(document.querySelectorAll("[data-warehouse-cycle-count-user-preview]")).filter(visible).length,
      cycleCountManagerPreviewCount: Array.from(document.querySelectorAll("[data-warehouse-cycle-count-manager-preview]")).filter(visible).length,
      cycleCountEvidencePreviewCount: Array.from(document.querySelectorAll("[data-warehouse-cycle-count-evidence-preview]")).filter(visible).length,
      cycleCountPolicyCount: Array.from(document.querySelectorAll("[data-warehouse-cycle-count-policy]")).filter(visible).length,
      cycleCountActiveControlCount: Array.from(document.querySelectorAll("[data-warehouse-cycle-count-shell] button, [data-warehouse-cycle-count-shell] a, [data-warehouse-cycle-count-shell] [role=button]")).filter(visible).length,
      searchUtilityVisible: Array.from(document.querySelectorAll("[data-erpw-sales-search-open]")).some(visible),
      horizontalOverflow: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
    };
  });
}

function assertClean(state, context) {
  assert(state.shellCount === 1, "Warehouse shell count must remain 1", { context, state });
  assert(state.headerCount === 1, "Warehouse header count must remain 1", { context, state });
  assert(state.horizontalOverflow <= 2, "Warehouse page has horizontal overflow", { context, state });
  assert(state.searchUtilityVisible, "Warehouse sidebar search helper must be available", { context, state });
  assert(!FORBIDDEN_ACTION_RE.test(state.actionText), "Forbidden stock action control is visible", { context, state });
  assert(!FORBIDDEN_COPY_RE.test(state.text), "Developer or search copy is visible", { context, state });
  assert(!VALUATION_RE.test(state.text), "Valuation, accounting, or commercial text is visible", { context, state });
  assert(!NATIVE_ROUTE_RE.test(`${state.hrefs} ${state.actionText} ${(state.routeTargets || []).join(" ")}`), "Native route target is visible", { context, state });
}

function assertW12KCockpit(state, contextLabel) {
  assert(state.commandCount === 1, "Cockpit command area must render once", { context: contextLabel, state });
  assert(state.commandChipCount === 0, "Cockpit command chips should not duplicate read-only/freshness status in the hero", { context: contextLabel, state });
  assert(state.refreshActionCount === 1, "Cockpit refresh control must render once", { context: contextLabel, state });
  assert(state.inboundActionCount === 1, "Inbound receiving should have one top-level Start navigation control", { context: contextLabel, state });
  assert(state.outboundActionCount === 1, "Outbound picking should have one top-level Start navigation control", { context: contextLabel, state });
  assert(state.stockExceptionActionCount === 0, "Stock exceptions should stay in Review and Visibility, not Start Warehouse Work", { context: contextLabel, state });
  assert(state.movementActionCount === 0, "Movement visibility should stay in Review and Visibility, not Start Warehouse Work", { context: contextLabel, state });
  assert(state.transferActionCount === 0, "Transfer visibility should stay in Review and Visibility, not Start Warehouse Work", { context: contextLabel, state });
  const targets = state.routeTargets || [];
  [
    "warehouse-console-worklist/inbound-receiving",
    "warehouse-console-worklist/outbound-picking",
    "warehouse-console-worklist/stock-exceptions",
    "warehouse-console-worklist/movement-visibility",
    "warehouse-console-worklist/transfer-visibility",
  ].forEach((target) => {
    assert(targets.includes(target), `Cockpit route target missing: ${target}`, { context: contextLabel, state });
  });
  assert((state.text || "").includes("Transfer Visibility"), "Transfer Visibility card text is missing", { context: contextLabel, state });
  assert(!(state.text || "").includes("Read-only guardrail"), "Overview should not render the bottom read-only guardrail label", { context: contextLabel, state });
  assert(state.warehousePageHeadCount <= 1, "Duplicate Warehouse page head chrome is visible", { context: contextLabel, state });
  assert(state.allPageHeadCount === 0, "Frappe page-head chrome is visible in Warehouse cockpit", { context: contextLabel, state });
  assert((state.sidebarDuplicates || []).length === 0, "Duplicate Warehouse sidebar items are visible", { context: contextLabel, state });
}

function assertW14BQuickFind(state, contextLabel) {
  assert(state.quickFindCount === 0, "Warehouse Quick Find must not render in the cockpit content", { context: contextLabel, state });
  assert(!state.quickFindInputVisible, "Warehouse cockpit Quick Find input should be removed", { context: contextLabel, state });
  assert(state.searchUtilityVisible, "Warehouse Quick Find should be available as the sidebar search helper", { context: contextLabel, state });
  assert(!(state.text || "").includes("Preview before opening"), "Old cockpit Quick Find preview guidance is still visible", { context: contextLabel, state });
  assert(!NATIVE_ROUTE_RE.test(`${state.hrefs} ${state.actionText} ${(state.routeTargets || []).join(" ")}`), "Warehouse Quick Find exposed a native route", { context: contextLabel, state });
}

function assertW14CManagerCenter(state, contextLabel) {
  assert(state.managerCenterCount === 0, "Manager Readiness Center must be removed from the cockpit", { context: contextLabel, state });
  assert(state.managerCenterCardCount === 0, "Manager Readiness summary cards should be removed", { context: contextLabel, state });
  assert(state.managerCenterGroupCount === 0, "Manager Readiness groups should be removed", { context: contextLabel, state });
  assert(state.managerCenterItemCount === 0, "Manager Readiness items should be removed", { context: contextLabel, state });
  assert(state.managerCenterActionCount === 0, "Manager Readiness actions should be removed", { context: contextLabel, state });
  assert(!(state.text || "").includes("Manager Readiness Center"), "Manager Readiness Center title is still visible", { context: contextLabel, state });
}

function assertW16D2ReturnsHub(state, contextLabel) {
  assert(state.returnsOverviewSummaryCount === 0, "Overview must not duplicate the dedicated Returns work hub summary", { context: contextLabel, state });
  assert(state.returnsOverviewSummaryCardCount === 0, "Overview must not render inactive Returns lane cards below Action Center", { context: contextLabel, state });
  assert(state.returnsOverviewOpenCount === 0, "Overview must not use the removed Returns summary open action", { context: contextLabel, state });
  assert(state.cycleCountOverviewSummaryCount === 0, "Overview must not duplicate the dedicated Cycle Count work hub summary", { context: contextLabel, state });
  assert(state.cycleCountOverviewSummaryCardCount === 0, "Overview must not render inactive Cycle Count lane cards below Action Center", { context: contextLabel, state });
  assert(state.cycleCountOverviewOpenCount === 0, "Overview must not use the removed Cycle Count summary open action", { context: contextLabel, state });
  assert(state.returnsOpenRouteCount >= 2, "Overview should expose Returns navigation from Start Work and Action Center", { context: contextLabel, state });
  assert(state.returnsOverviewSaveClassCount === 0, "Overview Returns navigation must not reuse return save-button styling", { context: contextLabel, state });
  assert(state.returnsHubCount === 0, "Overview must not expose the active Returns workbench", { context: contextLabel, state });
  assert(state.customerReturnIntakeFieldCount === 0, "Overview must not expose customer return input fields", { context: contextLabel, state });
  assert(state.supplierReturnCandidateFieldCount === 0, "Overview must not expose supplier return input fields", { context: contextLabel, state });
  assert(state.returnDecisionsHubActiveControlCount === 0, "Overview must not expose active return manager controls", { context: contextLabel, state });
  assert((state.text || "").includes("Returns"), "Returns summary title is missing", { context: contextLabel, state });
  assert((state.text || "").includes("Open Returns"), "Overview Returns action is missing", { context: contextLabel, state });
  assert((state.actionCenterTargetSections || []).filter((target) => target === "returns-work-hub").length === 0, "Action Center should route to Returns Work Hub instead of Overview target sections", { context: contextLabel, state });
  assert(!/sales_returns_in_progress|sales-console-worklist|new_doc|frappe\.new_doc/i.test(`${state.text} ${state.hrefs} ${state.actionText} ${(state.routeTargets || []).join(" ")}`), "Overview Returns summary leaked Sales or native document routing", { context: contextLabel, state });
  assert(!NATIVE_ROUTE_RE.test(`${state.hrefs} ${state.actionText} ${(state.routeTargets || []).join(" ")}`), "Overview Returns summary exposed a native route", { context: contextLabel, state });
}

function assertReturnsWorkHubPage(state, contextLabel) {
  assert(state.returnsPageErrorCount === 0, "Dedicated Returns Work Hub rendered an error state", { context: contextLabel, state });
  assert(state.workflowPageShellCount === 1 && (state.workflowPageShellKeys || []).includes("returns"), "Returns Work Hub must use the shared workflow page shell", { context: contextLabel, state });
  assert(state.workflowPageHeaderCount === 1, "Returns Work Hub must use the shared workflow page header", { context: contextLabel, state });
  assert(state.workflowCardCount === 1 && (state.workflowCardKinds || []).includes("returns"), "Returns Work Hub must use the shared workflow card grammar", { context: contextLabel, state });
  assert(state.workflowModeCount === 1, "Returns Work Hub custom workflow mode badge is missing", { context: contextLabel, state });
  assert(state.workflowGuardrailCount === 1, "Returns Work Hub shared guardrail is missing", { context: contextLabel, state });
  assert(state.workflowBodyCount === 1, "Returns Work Hub shared workflow body is missing", { context: contextLabel, state });
  assert(state.returnsHubCount === 1, "Dedicated Returns Work Hub must render the active work hub once", { context: contextLabel, state });
  assert(state.returnsHubLaneCount === 3, "Dedicated Returns Work Hub selector cards are missing", { context: contextLabel, state });
  assert(state.returnsHubSwitchCount === 3, "Dedicated Returns Work Hub workflow switches are missing", { context: contextLabel, state });
  assert((state.returnsHubSelectedLaneKeys || []).length === 1 && state.returnsHubSelectedLaneKeys[0] === "customer", "Customer return workflow should be selected by default on Returns Work Hub", { context: contextLabel, state });
  assert((state.returnsHubVisiblePanelKeys || []).length === 1 && state.returnsHubVisiblePanelKeys[0] === "customer", "Only customer workbench panel should be visible by default on Returns Work Hub", { context: contextLabel, state });
  assert(state.returnsHubGuardrailCount === 1, "Dedicated Returns guardrail is missing", { context: contextLabel, state });
  assert(state.customerReturnIntakePanelCount === 1, "Customer return intake workbench panel must be visible by default", { context: contextLabel, state });
  assert(state.customerReturnIntakeFieldCount >= 9, "Customer return intake evidence fields are missing on Returns Work Hub", { context: contextLabel, state });
  assert(state.customerReturnIntakeSaveCount === 1, "Customer return intake save control must render once on Returns Work Hub", { context: contextLabel, state });
  assert(state.supplierReturnCandidatePanelCount === 0, "Supplier return candidate panel must stay hidden until selected", { context: contextLabel, state });
  assert(state.supplierReturnCandidateFieldCount === 0, "Supplier return candidate fields should be hidden until selected", { context: contextLabel, state });
  assert(state.returnDecisionsPanelCount === 0, "Return decisions panel must stay hidden until selected", { context: contextLabel, state });
  assert(state.returnDecisionsHubControlCount >= 6, "Return decision controls must exist on the dedicated Returns Work Hub", { context: contextLabel, state });
  assert(!NATIVE_ROUTE_RE.test(`${state.hrefs} ${state.actionText} ${(state.routeTargets || []).join(" ")}`), "Dedicated Returns Work Hub exposed a native route", { context: contextLabel, state });
}

function assertW15PlannedWorkflowGroup(state, contextLabel) {
  assert(state.plannedWorkflowGroupCount === 0, "Overview should not show planned workflow shells after W16F activation", { context: contextLabel, state });
  assert(state.plannedWorkflowCardCount === 0, "Overview should not show planned workflow cards after W16F activation", { context: contextLabel, state });
  assert(state.plannedWorkflowToggleCount === 0, "Overview should not show planned workflow toggles after W16F activation", { context: contextLabel, state });
  assert(state.plannedWorkflowVisibleDetailCount === 0, "Overview should not show expanded planned workflow details after W16F activation", { context: contextLabel, state });
  assert(state.customerReturnShellCount === 0, "Customer Return detail shell should not remain in planned workflow shells", { context: contextLabel, state });
  assert(state.supplierReturnShellCount === 0, "Supplier Return detail shell should not remain in planned workflow shells", { context: contextLabel, state });
  assert(state.internalTransferShellCount === 0, "Internal Transfer detail shell should not remain in planned workflow shells", { context: contextLabel, state });
  assert(state.cycleCountShellCount === 0, "Cycle Count detail shell should not remain in planned workflow shells", { context: contextLabel, state });
  const obsoletePlannedWorkflowTitle = ["Remaining", "planned", "workflow", "shells"].join(" ");
  assert(!(state.text || "").includes(obsoletePlannedWorkflowTitle), "Obsolete planned workflow group title should not render after W16F activation", { context: contextLabel, state });
  assert(!(state.text || "").includes("Internal transfer candidate"), "Internal Transfer should not remain as a planned workflow shell after W16E", { context: contextLabel, state });
  assert(!NATIVE_ROUTE_RE.test(`${state.hrefs} ${state.actionText} ${(state.routeTargets || []).join(" ")}`), "Planned workflow group exposed a native route", { context: contextLabel, state });
}


function assertW15BActionCenter(state, contextLabel) {
  const expectedStartCardKeys = [
    "inbound_due",
    "outbound_risk",
    "returns_work_hub",
    "internal_transfer_workflow",
    "cycle_count_workflow",
  ];
  const expectedStartTargets = [
    "warehouse-console-worklist/inbound-receiving",
    "warehouse-console-worklist/outbound-picking",
    "warehouse-console-worklist/returns-work-hub",
    "warehouse-console-worklist/internal-transfer-workflow",
    "warehouse-console-worklist/cycle-count-workflow",
  ];
  const expectedGroupKeys = ["manager_decisions", "visibility"];
  const expectedCardKeys = [
    "arrival_review",
    "picking_blockers",
    "exception_resolution",
    "return_decisions",
    "internal_transfer_decisions",
    "inventory_variance",
    "movement_visibility",
    "transfer_visibility",
  ];
  const expectedCardRoles = [
    "queue",
    "queue",
    "queue",
    "custom_workflow",
    "custom_workflow",
    "custom_workflow",
    "visibility",
    "visibility",
  ];
  const expectedActionCenterTargets = [
    "warehouse-console-worklist/inbound-receiving",
    "warehouse-console-worklist/outbound-picking",
    "warehouse-console-worklist/stock-exceptions",
    "warehouse-console-worklist/returns-work-hub",
    "warehouse-console-worklist/internal-transfer-workflow",
    "warehouse-console-worklist/cycle-count-workflow",
    "warehouse-console-worklist/movement-visibility",
    "warehouse-console-worklist/transfer-visibility",
  ];
  assert(JSON.stringify(state.startCardKeys || []) === JSON.stringify(expectedStartCardKeys), "Start Warehouse Work should contain only work-entry destinations", { context: contextLabel, state, expectedStartCardKeys });
  assert(JSON.stringify(state.startRouteTargets || []) === JSON.stringify(expectedStartTargets), "Start Warehouse Work route targets changed unexpectedly", { context: contextLabel, state, expectedStartTargets });
  assert(!(state.startCardKeys || []).includes("stock_exceptions"), "Stock Exceptions should not duplicate into Start Warehouse Work", { context: contextLabel, state });
  assert(!(state.startCardKeys || []).includes("movement_visibility"), "Movement Visibility should not duplicate into Start Warehouse Work", { context: contextLabel, state });
  assert(!(state.startCardKeys || []).includes("transfer_visibility"), "Transfer Visibility should not duplicate into Start Warehouse Work", { context: contextLabel, state });
  assert(state.actionCenterCount === 1, "Warehouse Action Center must render once", { context: contextLabel, state });
  assert(JSON.stringify(state.actionCenterGroupKeys || []) === JSON.stringify(expectedGroupKeys), "Warehouse Command Center groups changed unexpectedly", { context: contextLabel, state, expectedGroupKeys });
  assert(JSON.stringify(state.actionCenterCardKeys || []) === JSON.stringify(expectedCardKeys), "Warehouse Command Center card matrix changed unexpectedly", { context: contextLabel, state, expectedCardKeys });
  assert(JSON.stringify(state.actionCenterCardRoles || []) === JSON.stringify(expectedCardRoles), "Warehouse Command Center card roles changed unexpectedly", { context: contextLabel, state, expectedCardRoles });
  assert(JSON.stringify(state.actionCenterRouteTargets || []) === JSON.stringify(expectedActionCenterTargets), "Warehouse Command Center route targets changed unexpectedly", { context: contextLabel, state, expectedActionCenterTargets });
  assert(state.actionCenterGroupCount === expectedGroupKeys.length, "Warehouse Action Center group count changed unexpectedly", { context: contextLabel, state });
  assert(state.actionCenterCardCount === expectedCardKeys.length, "Warehouse Action Center card count changed unexpectedly", { context: contextLabel, state });
  assert(state.actionCenterOpenCount === expectedCardKeys.length, "Warehouse Action Center should have one route control per card", { context: contextLabel, state });
  assert(state.actionCenterRoleBadgeCount === 0, "Warehouse Command Center should not expose decorative role badges in the visible card UI", { context: contextLabel, state });
  assert(state.actionCenterCustomMetricCount === 0, "Custom workflow cards must not render Custom as a large side metric", { context: contextLabel, state });
  assert(state.actionCenterCustomWorkflowCount === 3, "Manager custom workflow cards should be explicitly marked", { context: contextLabel, state });
  assert(state.actionCenterVisibilityCount === 2, "Visibility cards should be separated from manager review cards", { context: contextLabel, state });
  assert(state.actionCenterGuardrailCount === 1, "Warehouse Action Center custom-workflow guardrail is missing", { context: contextLabel, state });
  assert((state.actionCenterModes || []).includes("custom_workflow"), "Warehouse Action Center must present as custom workflow", { context: contextLabel, state });
  assert((state.text || "").includes("Review and Visibility"), "Review and Visibility title is missing", { context: contextLabel, state });
  assert(!(state.text || "").includes("Warehouse Command Center"), "Overview should not expose the duplicate Warehouse Command Center label after W16G5I", { context: contextLabel, state });
  assert(!(state.actionCenterGroupKeys || []).includes("work_entry"), "Action Center must not duplicate the Start Work group after W16G5I", { context: contextLabel, state });
  assert(!(state.text || "").includes("Start Work"), "Action Center should not duplicate Start Work after W16G5I", { context: contextLabel, state });
  assert((state.text || "").includes("Manager Review"), "Warehouse Command Center manager-review group is missing", { context: contextLabel, state });
  assert((state.text || "").includes("Visibility"), "Warehouse Command Center visibility group is missing", { context: contextLabel, state });
  assert((state.text || "").includes("Custom workflow only"), "Warehouse Action Center custom-workflow guardrail copy is missing", { context: contextLabel, state });
  assert(!(state.text || "").includes("Shell only"), "Warehouse Action Center should not present as shell-only after W16 activations", { context: contextLabel, state });
  assert(!(state.text || "").includes("Action shell only"), "Warehouse Action Center should not expose action-shell wording after W16 activations", { context: contextLabel, state });
  assert(!(state.text || "").includes("future Warehouse work"), "Warehouse Action Center should not describe active workflows as future work", { context: contextLabel, state });
  assert(!(state.text || "").includes("planned workflow lane"), "Warehouse Action Center should not expose planned-lane wording after W16 activations", { context: contextLabel, state });
  assert(!(state.text || "").includes("Manager Readiness"), "Manager Readiness copy must not return with W15B", { context: contextLabel, state });
  assert(!FORBIDDEN_ACTION_RE.test(state.actionText), "Warehouse Action Center exposed a forbidden stock action control", { context: contextLabel, state });
}

async function assertCockpit(page, contextLabel) {
  await waitForCockpit(page);
  const state = await snapshot(page);
  assertClean(state, contextLabel);
  assert(state.cockpitCount === 1, "Cockpit shell did not render", { context: contextLabel, state });
  assert(state.pulseCount >= 6, "Warehouse pulse cards did not render", { context: contextLabel, state });
  assert(state.startCount === 5, "Start Warehouse Work should render five work-entry cards", { context: contextLabel, state });
  assert(state.workCount === 0, "Legacy Work To Do cards should not duplicate Start Warehouse Work or Action Center", { context: contextLabel, state });
  assert(state.riskCount === 0, "Legacy Risks To Resolve cards should not duplicate Start Warehouse Work or Action Center", { context: contextLabel, state });
  assert(state.movementCount === 0, "Legacy Movement To Understand cards should not duplicate Start Warehouse Work or Action Center", { context: contextLabel, state });
  assert(state.legacyRouteSectionCount === 0, "Legacy duplicated Overview route sections should not render", { context: contextLabel, state });
  assert(state.guardrailCount === 0, "Overview should not render the bottom read-only guardrail panel", { context: contextLabel, state });
  if (EXPECT_W12K) assertW12KCockpit(state, contextLabel);
  if (EXPECT_W14B) assertW14BQuickFind(state, contextLabel);
  if (EXPECT_W14C) assertW14CManagerCenter(state, contextLabel);
  if (EXPECT_W15B) assertW15BActionCenter(state, contextLabel);
  assertW16D2ReturnsHub(state, contextLabel);
  assertW15PlannedWorkflowGroup(state, contextLabel);
  assert(!(state.text || "").includes("Draft comes later"), "Overview should not expose draft-later wording", { context: contextLabel, state });
  assert(!(state.text || "").includes("preview-only"), "Overview should not expose preview-only planned wording", { context: contextLabel, state });
  return state;
}
async function selectReturnsWorkflow(page, key) {
  await page.locator(`[data-warehouse-returns-hub-switch="${key}"]`).first().click();
  await page.waitForFunction((expectedKey) => {
    const visible = (node) => {
      if (!node) return false;
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
    };
    const panels = Array.from(document.querySelectorAll("[data-warehouse-returns-workbench-panel]")).filter(visible);
    const selected = document.querySelector(`[data-warehouse-returns-hub-switch="${expectedKey}"][aria-selected="true"]`);
    return panels.length === 1 && panels[0].getAttribute("data-warehouse-returns-workbench-panel") === expectedKey && Boolean(selected);
  }, key, { timeout: TIMEOUT });
}

async function openReturnsWorkHub(page, diagnostics, contextLabel) {
  await page.locator("[data-warehouse-open-returns]").first().click();
  await page.waitForURL((url) => url.pathname === "/desk/warehouse-console-worklist/returns-work-hub" || url.pathname === "/app/warehouse-console-worklist/returns-work-hub", { timeout: TIMEOUT });
  await waitForWorklist(page, "returns-work-hub");
  if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-returns-work-hub");
  assertReturnsWorkHubPage(await snapshot(page), contextLabel);
}

async function exerciseCustomerReturnIntakeDraft(page, diagnostics, contextLabel) {
  if (!ASSET_ROOT) return;
  await selectReturnsWorkflow(page, "customer");
  await page.locator("[data-warehouse-customer-return-field='customer']").fill("W16D3 Customer");
  await page.locator("[data-warehouse-customer-return-field='return_authorization_reference']").fill("RMA-W16D3-001");
  await page.locator("[data-warehouse-customer-return-field='item_code']").fill("ITEM-W16D3");
  await page.locator("[data-warehouse-customer-return-field='returned_qty']").fill("2");
  await page.locator("[data-warehouse-customer-return-field='accepted_qty']").fill("2");
  const baseline = overrideHitCount(diagnostics, "customer-return-intake-draft");
  await page.locator("[data-warehouse-customer-return-save]").click();
  await waitForOverrideHit(diagnostics, "customer-return-intake-draft");
  assert(overrideHitCount(diagnostics, "customer-return-intake-draft") > baseline, "Customer return intake save did not call the custom draft method", { context: contextLabel });
  const statusText = await page.locator("[data-warehouse-customer-return-status-message]").first().innerText();
  assert(/Custom customer return draft saved/i.test(statusText), "Customer return intake save success message is missing", { context: contextLabel, statusText });
  assert(!/Sales Return created|Credit Note created|Delivery Note created|Stock Entry/i.test(statusText), "Customer return intake status implies ERP document creation", { context: contextLabel, statusText });
}

async function exerciseSupplierReturnCandidateDraft(page, diagnostics, contextLabel) {
  if (!ASSET_ROOT) return;
  await selectReturnsWorkflow(page, "supplier");
  await page.locator("[data-warehouse-supplier-return-field='supplier']").fill("W16D4 Supplier");
  await page.locator("[data-warehouse-supplier-return-field='supplier_return_reference']").fill("SUP-RET-W16D4-001");
  await page.locator("[data-warehouse-supplier-return-field='item_code']").fill("ITEM-W16D4");
  await page.locator("[data-warehouse-supplier-return-field='candidate_qty']").fill("2");
  await page.locator("[data-warehouse-supplier-return-field='condition_note']").fill("Supplier-return evidence ready for manager posture.");
  const baseline = overrideHitCount(diagnostics, "supplier-return-candidate-draft");
  await page.locator("[data-warehouse-supplier-return-save]").click();
  await waitForOverrideHit(diagnostics, "supplier-return-candidate-draft");
  assert(overrideHitCount(diagnostics, "supplier-return-candidate-draft") > baseline, "Supplier return candidate save did not call the custom draft method", { context: contextLabel });
  const statusText = await page.locator("[data-warehouse-supplier-return-status-message]").first().innerText();
  assert(/Custom supplier return candidate saved/i.test(statusText), "Supplier return candidate save success message is missing", { context: contextLabel, statusText });
  assert(!/supplier notified|stock decrease was created|debit note created|return purchase receipt created/i.test(statusText), "Supplier return status implies forbidden external or stock document behavior", { context: contextLabel, statusText });
}


async function exerciseReturnManagerDecisions(page, diagnostics, contextLabel) {
  if (!ASSET_ROOT) return;
  const refreshBaseline = overrideHitCount(diagnostics, "warehouse-returns-work-hub");
  await page.locator("[data-warehouse-returns-refresh]").first().click();
  await waitForOverrideHit(diagnostics, "warehouse-returns-work-hub");
  assert(overrideHitCount(diagnostics, "warehouse-returns-work-hub") > refreshBaseline, "Returns Work Hub refresh did not reload custom workflow records", { context: contextLabel });
  await waitForWorklist(page, "returns-work-hub");
  await selectReturnsWorkflow(page, "decisions");
  const customerBaseline = overrideHitCount(diagnostics, "customer-return-manager-decision");
  await page.locator("[data-warehouse-return-decision-source='customer'][data-warehouse-return-decision-decision='mark_restock_candidate']").click();
  await waitForOverrideHit(diagnostics, "customer-return-manager-decision");
  assert(overrideHitCount(diagnostics, "customer-return-manager-decision") > customerBaseline, "Customer return manager decision did not call the custom manager method", { context: contextLabel });
  const customerStatusText = await page.locator("[data-warehouse-return-decision-status-message]").first().innerText();
  assert(/Manager posture recorded/i.test(customerStatusText), "Customer return manager decision success message is missing", { context: contextLabel, customerStatusText });
  assert(!/Sales Return created|Credit Note created|Delivery Note created|Stock Entry/i.test(customerStatusText), "Customer return manager decision implies ERP document creation", { context: contextLabel, customerStatusText });

  const supplierBaseline = overrideHitCount(diagnostics, "supplier-return-manager-decision");
  await page.locator("[data-warehouse-return-decision-source='supplier'][data-warehouse-return-decision-decision='mark_supplier_return_candidate']").click();
  await waitForOverrideHit(diagnostics, "supplier-return-manager-decision");
  assert(overrideHitCount(diagnostics, "supplier-return-manager-decision") > supplierBaseline, "Supplier return manager decision did not call the custom manager method", { context: contextLabel });
  const supplierStatusText = await page.locator("[data-warehouse-return-decision-status-message]").first().innerText();
  assert(/Manager posture recorded/i.test(supplierStatusText), "Supplier return manager decision success message is missing", { context: contextLabel, supplierStatusText });
  assert(!/supplier notified|stock decrease was created|debit note created|return purchase receipt created/i.test(supplierStatusText), "Supplier return manager decision implies forbidden external or stock document behavior", { context: contextLabel, supplierStatusText });
}


function assertInternalTransferWorkflowPage(state, contextLabel) {
  assert(state.internalTransferWorkflowPageCount === 1, "Internal Transfer dedicated page must render once", { context: contextLabel, state });
  assert(state.workflowPageShellCount === 1 && (state.workflowPageShellKeys || []).includes("internal_transfer"), "Internal Transfer must use the shared workflow page shell", { context: contextLabel, state });
  assert(state.workflowPageHeaderCount === 1, "Internal Transfer must use the shared workflow page header", { context: contextLabel, state });
  assert(state.workflowCardCount === 1 && (state.workflowCardKinds || []).includes("internal_transfer"), "Internal Transfer must use the shared workflow card grammar", { context: contextLabel, state });
  assert(state.workflowModeCount === 1, "Internal Transfer custom workflow mode badge is missing", { context: contextLabel, state });
  assert(state.workflowGuardrailCount === 1, "Internal Transfer shared guardrail is missing", { context: contextLabel, state });
  assert(state.workflowBodyCount === 1, "Internal Transfer shared workflow body is missing", { context: contextLabel, state });
  assert(state.workflowPanelCount >= 2, "Internal Transfer shared workflow panels are missing", { context: contextLabel, state });
  assert(state.internalTransferWorkflowCount === 1, "Internal Transfer workflow body is missing", { context: contextLabel, state });
  assert(state.internalTransferCandidatePanelCount === 1, "Internal Transfer candidate evidence panel is missing", { context: contextLabel, state });
  assert(state.internalTransferFieldCount >= 14, "Internal Transfer candidate fields are missing", { context: contextLabel, state });
  assert(state.internalTransferSaveCount === 1, "Internal Transfer save control must render once", { context: contextLabel, state });
  assert(state.internalTransferDecisionControlCount >= 5, "Internal Transfer manager posture controls are missing", { context: contextLabel, state });
  assert(state.internalTransferDecisionActiveControlCount === 0, "Internal Transfer manager controls must stay disabled until a custom candidate is saved", { context: contextLabel, state });
  assert((state.text || "").includes("No Stock Entry"), "Internal Transfer Stock Entry guardrail is missing", { context: contextLabel, state });
  assert((state.text || "").includes("No stock is moved"), "Internal Transfer stock movement guardrail is missing", { context: contextLabel, state });
  assert(!NATIVE_ROUTE_RE.test(`${state.hrefs} ${state.actionText} ${(state.routeTargets || []).join(" ")}`), "Internal Transfer workflow exposed a native route", { context: contextLabel, state });
}

async function openInternalTransferWorkflow(page, diagnostics, contextLabel) {
  await page.locator("[data-warehouse-open-internal-transfer]").first().click();
  await page.waitForURL((url) => url.pathname === "/desk/warehouse-console-worklist/internal-transfer-workflow" || url.pathname === "/app/warehouse-console-worklist/internal-transfer-workflow", { timeout: TIMEOUT });
  await waitForWorklist(page, "internal-transfer-workflow");
  if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-internal-transfer-workflow");
  assertInternalTransferWorkflowPage(await snapshot(page), contextLabel);
}

async function exerciseInternalTransferCandidateDraft(page, diagnostics, contextLabel) {
  if (!ASSET_ROOT) return;
  await page.locator("[data-warehouse-internal-transfer-field='target_warehouse']").fill("Target Warehouse - W16E");
  await page.locator("[data-warehouse-internal-transfer-field='source_reference_text']").fill("W16E smoke transfer request");
  await page.locator("[data-warehouse-internal-transfer-field='transfer_reason']").fill("Smoke verified warehouse rebalance candidate");
  await page.locator("[data-warehouse-internal-transfer-field='item_code']").fill("ITEM-W16E");
  await page.locator("[data-warehouse-internal-transfer-field='requested_qty']").fill("1");
  await page.locator("[data-warehouse-internal-transfer-field='counted_qty']").fill("1");
  await page.locator("[data-warehouse-internal-transfer-field='transfer_candidate_qty']").fill("1");
  await page.locator("[data-warehouse-internal-transfer-field='evidence_reference']").fill("Count note W16E");
  const baseline = overrideHitCount(diagnostics, "internal-transfer-candidate-draft");
  await page.locator("[data-warehouse-internal-transfer-save]").click();
  await waitForOverrideHit(diagnostics, "internal-transfer-candidate-draft");
  assert(overrideHitCount(diagnostics, "internal-transfer-candidate-draft") > baseline, "Internal Transfer save did not call the custom draft method", { context: contextLabel });
  const statusText = await page.locator("[data-warehouse-internal-transfer-status-message]").first().innerText();
  assert(/Custom internal transfer candidate saved/i.test(statusText), "Internal Transfer save success message is missing", { context: contextLabel, statusText });
  assert(!/Stock Entry created|stock moved|ledger updated|balance updated/i.test(statusText), "Internal Transfer status implies stock document or movement behavior", { context: contextLabel, statusText });
  const state = await snapshot(page);
  assert(state.internalTransferDecisionActiveControlCount >= 1, "Internal Transfer manager controls should unlock after custom candidate save for manager context", { context: contextLabel, state });
  const refreshBaseline = overrideHitCount(diagnostics, "warehouse-internal-transfer-workflow");
  await page.locator("[data-warehouse-internal-transfer-refresh]").first().click();
  await waitForOverrideHit(diagnostics, "warehouse-internal-transfer-workflow");
  assert(overrideHitCount(diagnostics, "warehouse-internal-transfer-workflow") > refreshBaseline, "Internal Transfer refresh did not reload custom workflow records", { context: contextLabel });
  await waitForWorklist(page, "internal-transfer-workflow");
  const recalledState = await snapshot(page);
  assert(recalledState.internalTransferDecisionActiveControlCount >= 1, "Internal Transfer manager controls should remain active after refreshed custom record recall", { context: contextLabel, state: recalledState });
  assert((recalledState.text || "").includes("Loaded saved custom internal transfer candidate"), "Internal Transfer recall message is missing after refresh", { context: contextLabel, state: recalledState });
}


function assertCycleCountWorkflowPage(state, contextLabel) {
  assert(state.cycleCountWorkflowPageCount === 1, "Cycle Count dedicated page must render once", { context: contextLabel, state });
  assert(state.workflowPageShellCount === 1 && (state.workflowPageShellKeys || []).includes("cycle_count"), "Cycle Count must use the shared workflow page shell", { context: contextLabel, state });
  assert(state.workflowPageHeaderCount === 1, "Cycle Count must use the shared workflow page header", { context: contextLabel, state });
  assert(state.workflowCardCount === 1 && (state.workflowCardKinds || []).includes("cycle_count"), "Cycle Count must use the shared workflow card grammar", { context: contextLabel, state });
  assert(state.workflowModeCount === 1, "Cycle Count custom workflow mode badge is missing", { context: contextLabel, state });
  assert(state.workflowGuardrailCount === 1, "Cycle Count shared guardrail is missing", { context: contextLabel, state });
  assert(state.workflowBodyCount === 1, "Cycle Count shared workflow body is missing", { context: contextLabel, state });
  assert(state.workflowPanelCount >= 2, "Cycle Count shared workflow panels are missing", { context: contextLabel, state });
  assert(state.cycleCountWorkflowCount === 1, "Cycle Count workflow body is missing", { context: contextLabel, state });
  assert(state.cycleCountTaskPanelCount === 1, "Cycle Count task evidence panel is missing", { context: contextLabel, state });
  assert(state.cycleCountFieldCount >= 17, "Cycle Count task fields are missing", { context: contextLabel, state });
  assert(state.cycleCountSaveCount === 1, "Cycle Count save control must render once", { context: contextLabel, state });
  assert(state.cycleCountDecisionControlCount >= 7, "Cycle Count manager posture controls are missing", { context: contextLabel, state });
  assert(state.cycleCountDecisionActiveControlCount === 0, "Cycle Count manager controls must stay disabled until a custom task is saved", { context: contextLabel, state });
  assert((state.text || "").includes("No Stock Reconciliation"), "Cycle Count Stock Reconciliation guardrail is missing", { context: contextLabel, state });
  assert((state.text || "").includes("No Stock Entry"), "Cycle Count Stock Entry guardrail is missing", { context: contextLabel, state });
  assert((state.text || "").includes("No stock is adjusted"), "Cycle Count stock adjustment guardrail is missing", { context: contextLabel, state });
  assert(!NATIVE_ROUTE_RE.test(`${state.hrefs} ${state.actionText} ${(state.routeTargets || []).join(" ")}`), "Cycle Count workflow exposed a native route", { context: contextLabel, state });
}

async function openCycleCountWorkflow(page, diagnostics, contextLabel) {
  await page.locator("[data-warehouse-open-cycle-count]").first().click();
  await page.waitForURL((url) => url.pathname === "/desk/warehouse-console-worklist/cycle-count-workflow" || url.pathname === "/app/warehouse-console-worklist/cycle-count-workflow", { timeout: TIMEOUT });
  await waitForWorklist(page, "cycle-count-workflow");
  if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-cycle-count-workflow");
  assertCycleCountWorkflowPage(await snapshot(page), contextLabel);
}

async function exerciseCycleCountTaskDraft(page, diagnostics, contextLabel) {
  if (!ASSET_ROOT) return;
  await page.locator("[data-warehouse-cycle-count-field='location_reference_text']").fill("W16F smoke count zone");
  await page.locator("[data-warehouse-cycle-count-field='count_reason']").fill("Smoke verified blind count evidence");
  await page.locator("[data-warehouse-cycle-count-field='item_code']").fill("ITEM-W16F");
  await page.locator("[data-warehouse-cycle-count-field='line_location_reference_text']").fill("W16F smoke bin");
  await page.locator("[data-warehouse-cycle-count-field='counted_qty']").fill("1");
  await page.locator("[data-warehouse-cycle-count-field='reason_code']").fill("Smoke verified count");
  await page.locator("[data-warehouse-cycle-count-field='evidence_reference']").fill("Count note W16F");
  const baseline = overrideHitCount(diagnostics, "cycle-count-task-draft");
  await page.locator("[data-warehouse-cycle-count-save]").click();
  await waitForOverrideHit(diagnostics, "cycle-count-task-draft");
  assert(overrideHitCount(diagnostics, "cycle-count-task-draft") > baseline, "Cycle Count save did not call the custom task draft method", { context: contextLabel });
  const statusText = await page.locator("[data-warehouse-cycle-count-status-message]").first().innerText();
  assert(/Custom cycle count task saved/i.test(statusText), "Cycle Count save success message is missing", { context: contextLabel, statusText });
  assert(!/Stock Reconciliation created|Stock Entry created|stock adjusted|ledger updated|balance updated/i.test(statusText), "Cycle Count status implies stock document or adjustment behavior", { context: contextLabel, statusText });
  const refreshBaseline = overrideHitCount(diagnostics, "warehouse-cycle-count-workflow");
  await page.locator("[data-warehouse-cycle-count-refresh]").first().click();
  await waitForOverrideHit(diagnostics, "warehouse-cycle-count-workflow");
  assert(overrideHitCount(diagnostics, "warehouse-cycle-count-workflow") > refreshBaseline, "Cycle Count refresh did not reload custom workflow records", { context: contextLabel });
  await waitForWorklist(page, "cycle-count-workflow");
  const stateAfterSave = await snapshot(page);
  assert((stateAfterSave.text || "").includes("Loaded saved custom cycle count task"), "Cycle Count recall message is missing after refresh", { context: contextLabel, state: stateAfterSave });
  const managerBaseline = overrideHitCount(diagnostics, "cycle-count-manager-decision");
  if (stateAfterSave.cycleCountDecisionActiveControlCount >= 1) {
    await page.locator("[data-warehouse-cycle-count-decision='mark_clean_count']").click();
    await waitForOverrideHit(diagnostics, "cycle-count-manager-decision");
    assert(overrideHitCount(diagnostics, "cycle-count-manager-decision") > managerBaseline, "Cycle Count manager decision did not call the custom manager method", { context: contextLabel });
    const managerStatusText = await page.locator("[data-warehouse-cycle-count-status-message]").first().innerText();
    assert(/Manager posture recorded/i.test(managerStatusText), "Cycle Count manager decision success message is missing", { context: contextLabel, managerStatusText });
    assert(!/Stock Reconciliation created|Stock Entry created|stock adjusted|ledger updated|balance updated/i.test(managerStatusText), "Cycle Count manager status implies stock document or adjustment behavior", { context: contextLabel, managerStatusText });
  } else {
    assert(overrideHitCount(diagnostics, "cycle-count-manager-decision") === managerBaseline, "Cycle Count manager decision should not be called when manager controls are disabled", { context: contextLabel, state: stateAfterSave });
    assert((stateAfterSave.text || "").includes("Manager only"), "Cycle Count non-manager context should explain that manager posture controls are disabled", { context: contextLabel, state: stateAfterSave });
  }
}

async function assertNoRemainingPlannedWorkflowShells(page, contextLabel) {
  const state = await snapshot(page);
  assert(state.plannedWorkflowGroupCount === 0, "Overview should not show remaining planned workflow shells after W16F activation", { context: contextLabel, state });
  assert(state.plannedWorkflowCardCount === 0, "Overview should not show planned workflow cards after W16F activation", { context: contextLabel, state });
  assert(state.cycleCountShellCount === 0, "Cycle Count should no longer render as an inert planned shell", { context: contextLabel, state });
  assert(state.internalTransferShellCount === 0, "Internal Transfer should no longer render as an inert planned shell", { context: contextLabel, state });
}


async function exerciseRouteAction(page, selector, expectedPath, viewName, contextLabel) {
  await page.locator(selector).first().click();
  await page.waitForURL((url) => url.pathname === expectedPath || url.pathname === expectedPath.replace("/desk/", "/app/"), { timeout: TIMEOUT });
  await waitForWorklist(page, viewName);
  assertClean(await snapshot(page), contextLabel);
}

async function exerciseQuickFind(page, diagnostics, contextLabel) {
  await assertCockpit(page, `${contextLabel}:quick-find-start`);
  await page.locator("[data-erpw-sales-search-open]").first().click();
  await page.waitForSelector("[data-erpw-sales-search-input]", { state: "visible", timeout: TIMEOUT });
  await page.locator("[data-erpw-sales-search-input]").fill("PO-W14B");
  await page.waitForFunction(() => {
    const results = document.querySelector("[data-erpw-sales-search-results]");
    return results && !results.hidden && /PO-W14B-1/.test(results.textContent || "");
  }, null, { timeout: TIMEOUT });
  if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-quick-find");
  const resultCount = await page.locator("[data-erpw-sales-search-index]").count();
  assert(resultCount >= 1, "Warehouse sidebar Quick Find did not render suggestions", { context: contextLabel, resultCount });
  const resultText = (await page.locator("[data-erpw-sales-search-results]").first().innerText()).replace(/\s+/g, " ").trim();
  assert(/PO-W14B-1/.test(resultText), "Warehouse sidebar Quick Find missing receiving result", { context: contextLabel, resultText });
  assert(!NATIVE_ROUTE_RE.test(resultText), "Warehouse sidebar Quick Find exposed a native route", { context: contextLabel, resultText });
  await page.locator("[data-erpw-sales-search-index]").first().click();
  await page.waitForURL((url) => url.pathname === "/desk/warehouse-console-receiving/PO-W14B-1", { timeout: TIMEOUT });
  assert(!NATIVE_ROUTE_RE.test(page.url()), "Warehouse sidebar Quick Find opened a native ERP route", { context: contextLabel, url: page.url() });
}

async function exerciseUnsupportedWorklistRoute(page, diagnostics, contextLabel) {
  const serviceBaseline = [
    "warehouse-inbound",
    "warehouse-outbound",
    "warehouse-stock-exceptions",
    "warehouse-movement-visibility",
    "warehouse-transfer-visibility",
  ].reduce((acc, key) => Object.assign(acc, { [key]: overrideHitCount(diagnostics, key) }), {});
  await openRoute(page, ["warehouse-console-worklist", "unsupported-worklist-slug"], "/desk/warehouse-console-worklist/unsupported-worklist-slug", waitForUnsupportedWorklist);
  const state = await snapshot(page);
  assertClean(state, contextLabel);
  assert(state.unsupportedWorklistCount === 1, "Unsupported Warehouse worklist fallback must render once", { context: contextLabel, state });
  assert(state.unsupportedWorklistPanelCount === 1, "Unsupported Warehouse worklist fallback panel is missing", { context: contextLabel, state });
  assert(state.unsupportedWorklistOverviewActionCount === 1, "Unsupported Warehouse worklist fallback overview action is missing", { context: contextLabel, state });
  assert((state.text || "").includes("Warehouse worklist unavailable"), "Unsupported route fallback title is missing", { context: contextLabel, state });
  assert((state.text || "").includes("unsupported-worklist-slug"), "Unsupported route fallback does not show the requested slug", { context: contextLabel, state });
  assert(!/Inbound Receiving|Outbound Picking|Stock Exceptions|Movement Visibility|Transfer Visibility/.test(state.text || ""), "Unsupported route fallback leaked a stale worklist shell", { context: contextLabel, state });
  if (ASSET_ROOT) {
    Object.keys(serviceBaseline).forEach((key) => {
      assert(overrideHitCount(diagnostics, key) === serviceBaseline[key], "Unsupported worklist route made a queue service call", { context: contextLabel, key, before: serviceBaseline[key], after: overrideHitCount(diagnostics, key) });
    });
  }
}

async function exerciseUser(browser, user, viewport) {
  resetWorkflowRecallState();
  const diagnostics = makeDiagnostics(`${user.key}-${viewport.key}`);
  const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height } });
  await installSourceOverrides(context, diagnostics);
  const page = await context.newPage();
  attachDiagnostics(page, diagnostics);
  try {
    await login(page, user);
    await openRoute(page, ["warehouse-console"], "/desk/warehouse-console", waitForCockpit);
    if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-overview");
    const sidebarCollapsed = await collapseBodySidebarForNarrowViewport(page);
    if (viewport.width <= 520) assert(sidebarCollapsed, "Mobile body sidebar was not collapsed for Warehouse cockpit evidence", { user: user.key, viewport });
    await assertCockpit(page, `${user.key}:${viewport.key}:cockpit`);
    if (viewport.key === "desktop-1440") {
      await openReturnsWorkHub(page, diagnostics, `${user.key}:${viewport.key}:returns-work-hub`);
      await exerciseCustomerReturnIntakeDraft(page, diagnostics, `${user.key}:${viewport.key}:customer-return-intake`);
      await exerciseSupplierReturnCandidateDraft(page, diagnostics, `${user.key}:${viewport.key}:supplier-return-candidate`);
      await exerciseReturnManagerDecisions(page, diagnostics, `${user.key}:${viewport.key}:return-decisions`);
      await openRoute(page, ["warehouse-console"], "/desk/warehouse-console", waitForCockpit);
      await openInternalTransferWorkflow(page, diagnostics, `${user.key}:${viewport.key}:internal-transfer-workflow`);
      await exerciseInternalTransferCandidateDraft(page, diagnostics, `${user.key}:${viewport.key}:internal-transfer-candidate`);
      await openRoute(page, ["warehouse-console"], "/desk/warehouse-console", waitForCockpit);
      await openCycleCountWorkflow(page, diagnostics, `${user.key}:${viewport.key}:cycle-count-workflow`);
      await exerciseCycleCountTaskDraft(page, diagnostics, `${user.key}:${viewport.key}:cycle-count-task`);
      await openRoute(page, ["warehouse-console"], "/desk/warehouse-console", waitForCockpit);
      await assertNoRemainingPlannedWorkflowShells(page, `${user.key}:${viewport.key}:planned-workflows`);
    }

    await page.reload({ waitUntil: "domcontentloaded", timeout: TIMEOUT });
    await collapseBodySidebarForNarrowViewport(page);
    await assertCockpit(page, `${user.key}:${viewport.key}:reload`);

    const repeatBaseline = overrideHitCount(diagnostics, "warehouse-overview");
    await openRoute(page, ["warehouse-console"], "/desk/warehouse-console", waitForCockpit);
    await openRoute(page, ["warehouse-console"], "/desk/warehouse-console", waitForCockpit);
    await assertCockpit(page, `${user.key}:${viewport.key}:repeat`);
    if (EXPECT_W12K && ASSET_ROOT) assert(overrideHitCount(diagnostics, "warehouse-overview") === repeatBaseline, "Repeated cockpit route navigation made an unnecessary overview service call", { user: user.key, viewport: viewport.key, before: repeatBaseline, after: overrideHitCount(diagnostics, "warehouse-overview") });

    if (EXPECT_W12K) {
      const refreshBaseline = overrideHitCount(diagnostics, "warehouse-overview");
      await page.locator("[data-warehouse-refresh]").click();
      await waitForCockpit(page);
      await assertCockpit(page, `${user.key}:${viewport.key}:refresh`);
      if (ASSET_ROOT) assert(overrideHitCount(diagnostics, "warehouse-overview") > refreshBaseline, "Cockpit Refresh did not force overview reload", { user: user.key, viewport: viewport.key, before: refreshBaseline, after: overrideHitCount(diagnostics, "warehouse-overview") });
    }

    if (EXPECT_W14B && viewport.key === "desktop-1440") {
      await exerciseQuickFind(page, diagnostics, `${user.key}:quick-find`);
      await openRoute(page, ["warehouse-console"], "/desk/warehouse-console", waitForCockpit);
      await assertCockpit(page, `${user.key}:quick-find:return`);
    }

    if (viewport.key === "desktop-1440") {
      await exerciseUnsupportedWorklistRoute(page, diagnostics, `${user.key}:unsupported-worklist`);
      await openRoute(page, ["warehouse-console"], "/desk/warehouse-console", waitForCockpit);
      await assertCockpit(page, `${user.key}:unsupported-worklist:return`);
    }

    if (EXPECT_W14C && viewport.key === "desktop-1440") {
      await assertCockpit(page, `${user.key}:manager-center-removed`);
    }

    if (EXPECT_W15B && viewport.key === "desktop-1440") {
      await exerciseRouteAction(page, "[data-warehouse-action-center-card='arrival_checks'] [data-warehouse-action-center-open]", "/desk/warehouse-console-worklist/inbound-receiving", "inbound-receiving", `${user.key}:action-center-arrival`);
      if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-inbound");
      await openRoute(page, ["warehouse-console"], "/desk/warehouse-console", waitForCockpit);
      await assertCockpit(page, `${user.key}:action-center-return`);
    }

    if (viewport.key === "desktop-1440") {
      await exerciseRouteAction(page, "[data-warehouse-open-inbound]", "/desk/warehouse-console-worklist/inbound-receiving", "inbound-receiving", `${user.key}:inbound`);
      if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-inbound");
      await openRoute(page, ["warehouse-console"], "/desk/warehouse-console", waitForCockpit);

      await exerciseRouteAction(page, "[data-warehouse-open-outbound]", "/desk/warehouse-console-worklist/outbound-picking", "outbound-picking", `${user.key}:outbound`);
      if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-outbound");
      await openRoute(page, ["warehouse-console"], "/desk/warehouse-console", waitForCockpit);

      await exerciseRouteAction(page, "[data-warehouse-action-center-card='exception_resolution'] [data-warehouse-action-center-open]", "/desk/warehouse-console-worklist/stock-exceptions", "stock-exceptions", `${user.key}:stock-exceptions`);
      if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-stock-exceptions");
      await openRoute(page, ["warehouse-console"], "/desk/warehouse-console", waitForCockpit);

      await exerciseRouteAction(page, "[data-warehouse-action-center-card='movement_visibility'] [data-warehouse-action-center-open]", "/desk/warehouse-console-worklist/movement-visibility", "movement-visibility", `${user.key}:movement`);
      if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-movement-visibility");
      await openRoute(page, ["warehouse-console"], "/desk/warehouse-console", waitForCockpit);

      await exerciseRouteAction(page, "[data-warehouse-action-center-card='transfer_visibility'] [data-warehouse-action-center-open]", "/desk/warehouse-console-worklist/transfer-visibility", "transfer-visibility", `${user.key}:transfer`);
      if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-transfer-visibility");
      await openRoute(page, ["warehouse-console"], "/desk/warehouse-console", waitForCockpit);
    }

    diagnostics.snapshots.push({ name: `${user.key}-${viewport.key}:final`, sidebarCollapsed: viewport.width <= 520 ? await collapseBodySidebarForNarrowViewport(page) : true, state: await snapshot(page), screenshot: await capture(page, `${user.key}-${viewport.key}-cockpit`) });
  } finally {
    await context.close();
  }
  return diagnostics;
}

function assertW16G5GRouteWrapperSourceContracts() {
  if (!ASSET_ROOT) return;
  const requiredWrappers = [
    "erp_workspace_ui/erp_workspace_ui/page/warehouse_console/warehouse_console.js",
    "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/warehouse_console_worklist.js",
    "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_receiving/warehouse_console_receiving.js",
    "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_picking/warehouse_console_picking.js",
  ];
  requiredWrappers.forEach((file) => {
    const body = readSource(file);
    assert(body.includes("data-warehouse-route-loading"), "Warehouse route wrapper missing first-paint loading shell", { file });
    assert(body.includes('target === document.body || target.id === "body"'), "Warehouse route wrapper can leave loading shell in the global body", { file });
    assert(body.includes('(frappe.container && frappe.container.page && frappe.container.page.wrapper) || document.getElementById("body")'), "Warehouse route wrapper must prefer the active page wrapper before global body fallback", { file });
  });
  const worklistWrapper = readSource("erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/warehouse_console_worklist.js");
  assert(worklistWrapper.includes('return "unsupported-worklist";'), "Warehouse worklist wrapper must route stale slugs to unsupported fallback", { file: "warehouse_console_worklist.js" });
  assert(!/cycle_count_workflow"\) return "cycle-count-workflow";\s*return "inbound-receiving";/.test(worklistWrapper), "Warehouse worklist wrapper falls through stale slugs to inbound", { file: "warehouse_console_worklist.js" });
  const pageSource = readSource("erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js");
  assert(!/===\s*orde\b/.test(pageSource), "Warehouse detail route stale-response guard has a broken order reference", { file: "warehouse_console_page.js" });
  assert(!/\bisSupplie\b/.test(pageSource), "Warehouse return manager action references misspelled isSupplie variable", { file: "warehouse_console_page.js" });
  assert(pageSource.includes('document.querySelectorAll("[data-warehouse-route-loading]")'), "Warehouse real-render cleanup must remove stale route loading shells", { file: "warehouse_console_page.js" });
  const customWorkflowRouteBlock = pageSource.slice(pageSource.indexOf("function renderReturnsWorkHubLoading"), pageSource.indexOf("function loadInboundQueue"));
  assert(customWorkflowRouteBlock.includes("replaceWarehouseRouteHost(viewState, $root)"), "Warehouse custom workflow routes must render through the route host helper", { file: "warehouse_console_page.js" });
  assert(!customWorkflowRouteBlock.includes("replacePageBody(viewState.page, $root)"), "Warehouse custom workflow routes must not replace the whole page body", { file: "warehouse_console_page.js" });
  [
    ["renderReturnsWorkHubPagePayload", "renderReturnsWorkHubPage"],
    ["renderInternalTransferWorkflowPagePayload", "renderInternalTransferWorkflowPage"],
    ["renderCycleCountWorkflowPagePayload", "renderCycleCountWorkflowPage"],
  ].forEach(([payloadRenderer, routeRenderer]) => {
    const payloadCount = (pageSource.match(new RegExp(`function\\s+${payloadRenderer}\\(`, "g")) || []).length;
    const routeCount = (pageSource.match(new RegExp(`function\\s+${routeRenderer}\\(viewState, options\\)`, "g")) || []).length;
    assert(payloadCount === 1, "Warehouse custom workflow payload renderer must exist exactly once", { file: "warehouse_console_page.js", payloadRenderer, payloadCount });
    assert(routeCount === 1, "Warehouse custom workflow route renderer must exist exactly once", { file: "warehouse_console_page.js", routeRenderer, routeCount });
  });
  [
    "returnsWorkHubStaleResponseIgnored",
    "internalTransferWorkflowStaleResponseIgnored",
    "cycleCountWorkflowStaleResponseIgnored",
  ].forEach((marker) => {
    assert(pageSource.includes(marker), "Warehouse custom workflow route is missing stale-response protection", { file: "warehouse_console_page.js", marker });
  });
}

async function main() {
  assertW16G5GRouteWrapperSourceContracts();
  assert(AUTHORIZED_USERS.length >= 1, "Warehouse credentials are required for W9A smoke", {
    missing: [
      "ERPW_WAREHOUSE_MANAGER_USERNAME/ERPW_WAREHOUSE_MANAGER_PASSWORD",
      "ERPW_WAREHOUSE_USER_USERNAME/ERPW_WAREHOUSE_USER_PASSWORD",
    ],
  });
  const browser = await chromium.launch({ headless: process.env.ERPW_HEADLESS !== "0" });
  const summary = { ok: false, phase: PHASE_LABEL, artifactDir: ARTIFACT_DIR, sourceOverride: Boolean(ASSET_ROOT), users: [], diagnostics: [] };
  try {
    for (const user of AUTHORIZED_USERS) {
      for (const viewport of VIEWPORTS) {
        const diagnostics = await exerciseUser(browser, user, viewport);
        const hardConsoleErrors = diagnostics.consoleErrors.filter((entry) => !/favicon|sourcemap|manifest/i.test(entry.text || ""));
        assert(hardConsoleErrors.length === 0, "Browser console errors were recorded", { user: user.key, viewport: viewport.key, errors: hardConsoleErrors });
        assert(diagnostics.pageErrors.length === 0, "Page errors were recorded", { user: user.key, viewport: viewport.key, errors: diagnostics.pageErrors });
        assert(diagnostics.failedResponses.length === 0, "Failed Warehouse responses were recorded", { user: user.key, viewport: viewport.key, failedResponses: diagnostics.failedResponses });
        summary.diagnostics.push(diagnostics);
      }
      summary.users.push(user.key);
    }
    summary.ok = true;
  } catch (error) {
    summary.ok = false;
    summary.error = { message: error.message, details: error.details || {}, stack: error.stack };
    throw error;
  } finally {
    await browser.close();
    const summaryPath = path.join(ARTIFACT_DIR, SUMMARY_NAME);
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
