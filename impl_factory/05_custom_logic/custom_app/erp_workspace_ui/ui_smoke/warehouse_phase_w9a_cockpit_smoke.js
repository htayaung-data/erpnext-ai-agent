const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const EXPECT_W12K = process.env.ERPW_WAREHOUSE_W9A_EXPECT_W12K === "1";
const PHASE_LABEL = process.env.ERPW_WAREHOUSE_W9A_PHASE_LABEL || (EXPECT_W12K ? "Warehouse W12K cockpit polish" : "Warehouse W9A cockpit");
const SUMMARY_NAME = process.env.ERPW_WAREHOUSE_W9A_SUMMARY_NAME || (EXPECT_W12K ? "warehouse-w12k-cockpit-polish-summary.json" : "warehouse-w9a-cockpit-summary.json");
const TIMEOUT = Number(process.env.ERPW_WAREHOUSE_W12K_TIMEOUT || process.env.ERPW_WAREHOUSE_W9A_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_WAREHOUSE_W12K_ARTIFACT_DIR || process.env.ERPW_WAREHOUSE_W9A_ARTIFACT_DIR || path.join(
  fs.existsSync("/freeze-artifacts") ? "/freeze-artifacts" : path.join(__dirname, "artifacts"),
  `${EXPECT_W12K ? "warehouse-w12k-cockpit-polish" : "warehouse-w9a-cockpit"}-${new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z")}`
);
const ASSET_ROOT = process.env.ERPW_WAREHOUSE_W12K_ASSET_ROOT || process.env.ERPW_WAREHOUSE_W9A_ASSET_ROOT || "";

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
    },
    search: { enabled: false },
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
    allowed_actions: [{ key: "refresh", label: "Refresh", kind: "read_only" }],
    action_targets: {},
    fetched_at: "2026-05-30 09:00:00",
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
    const isWorklist = /warehouse-console-worklist/i.test(text);
    const file = isWorklist
      ? "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/warehouse_console_worklist.js"
      : "erp_workspace_ui/erp_workspace_ui/page/warehouse_console/warehouse_console.js";
    const name = isWorklist ? "warehouse-console-worklist" : "warehouse-console";
    const script = readSource(file);
    recordOverrideHit(diagnostics, "desk-page-getpage", request, { fulfilled: Boolean(script), page: name });
    const pageDoc = { doctype: "Page", name, page_name: name, title: "Warehouse Console", module: "ERP Workspace UI", standard: "Yes", content: "", script };
    return route.fulfill({ status: script ? 200 : 404, contentType: "application/json", body: JSON.stringify({ docs: [pageDoc], message: pageDoc }) });
  });
  const methodPayloads = [
    ["get_warehouse_console_overview", "warehouse-overview", () => overviewPayload()],
    ["get_warehouse_console_sidebar_context", "warehouse-sidebar", () => sidebarPayload()],
    ["get_warehouse_inbound_receiving_queue", "warehouse-inbound", () => inboundPayload()],
    ["get_warehouse_outbound_picking_queue", "warehouse-outbound", () => outboundPayload()],
    ["get_warehouse_stock_exceptions", "warehouse-stock-exceptions", () => stockExceptionsPayload()],
    ["get_warehouse_movement_visibility_queue", "warehouse-movement-visibility", () => movementPayload()],
    ["get_warehouse_transfer_visibility_queue", "warehouse-transfer-visibility", () => transferPayload()],
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
    return Boolean(shell && shell.querySelector("[data-warehouse-cockpit-command]") && shell.querySelector("[data-warehouse-cockpit-pulse]") && shell.querySelector("[data-warehouse-cockpit-start]") && shell.querySelector("[data-warehouse-cockpit-work]") && shell.querySelector("[data-warehouse-cockpit-risk]") && shell.querySelector("[data-warehouse-cockpit-movement]"));
  }, null, { timeout: TIMEOUT });
}

async function waitForWorklist(page, viewName) {
  await page.waitForFunction((expectedView) => {
    const shell = document.querySelector(`.sales-console-shell[data-erpw-workspace="warehouse"][data-warehouse-view="${expectedView}"]`);
    return Boolean(shell && (shell.querySelector("[data-warehouse-inbound-queue-card], [data-warehouse-movement-card], [data-warehouse-stock-exception-card], [data-warehouse-transfer-card]") || shell.querySelector("[data-warehouse-movement-empty], [data-warehouse-stock-exception-empty], [data-warehouse-transfer-empty]")));
  }, viewName, { timeout: TIMEOUT });
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
      headerCount: Array.from(document.querySelectorAll(".warehouse-console-header, .warehouse-inbound-queue-header, .warehouse-receiving-header")).filter(visible).length,
      cockpitCount: Array.from(document.querySelectorAll("[data-warehouse-cockpit='ready']")).filter(visible).length,
      commandCount: Array.from(document.querySelectorAll("[data-warehouse-cockpit-command]")).filter(visible).length,
      commandChipCount: Array.from(document.querySelectorAll("[data-warehouse-cockpit-command-chip]")).filter(visible).length,
      pulseCount: Array.from(document.querySelectorAll("[data-warehouse-cockpit-pulse-card]")).filter(visible).length,
      startCount: Array.from(document.querySelectorAll("[data-warehouse-cockpit-start-card]")).filter(visible).length,
      workCount: Array.from(document.querySelectorAll("[data-warehouse-cockpit-work] .warehouse-console-inbound-panel")).filter(visible).length,
      riskCount: Array.from(document.querySelectorAll("[data-warehouse-cockpit-risk] [data-warehouse-cockpit-route-card]")).filter(visible).length,
      movementCount: Array.from(document.querySelectorAll("[data-warehouse-cockpit-movement] [data-warehouse-cockpit-route-card]")).filter(visible).length,
      guardrailCount: Array.from(document.querySelectorAll("[data-warehouse-cockpit-guardrail]")).filter(visible).length,
      inboundActionCount: Array.from(document.querySelectorAll("[data-warehouse-open-inbound]")).filter(visible).length,
      outboundActionCount: Array.from(document.querySelectorAll("[data-warehouse-open-outbound]")).filter(visible).length,
      stockExceptionActionCount: Array.from(document.querySelectorAll("[data-warehouse-open-stock-exceptions]")).filter(visible).length,
      movementActionCount: Array.from(document.querySelectorAll("[data-warehouse-open-movement]")).filter(visible).length,
      transferActionCount: Array.from(document.querySelectorAll("[data-warehouse-open-transfer]")).filter(visible).length,
      refreshActionCount: Array.from(document.querySelectorAll("[data-warehouse-refresh]")).filter(visible).length,
      searchUtilityVisible: Array.from(document.querySelectorAll("[data-erpw-sales-search-open]")).some(visible),
      horizontalOverflow: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
    };
  });
}

function assertClean(state, context) {
  assert(state.shellCount === 1, "Warehouse shell count must remain 1", { context, state });
  assert(state.headerCount === 1, "Warehouse header count must remain 1", { context, state });
  assert(state.horizontalOverflow <= 2, "Warehouse page has horizontal overflow", { context, state });
  assert(!state.searchUtilityVisible, "Warehouse search entry must stay inactive", { context, state });
  assert(!FORBIDDEN_ACTION_RE.test(state.actionText), "Forbidden stock action control is visible", { context, state });
  assert(!FORBIDDEN_COPY_RE.test(state.text), "Developer or search copy is visible", { context, state });
  assert(!VALUATION_RE.test(state.text), "Valuation, accounting, or commercial text is visible", { context, state });
  assert(!NATIVE_ROUTE_RE.test(`${state.hrefs} ${state.actionText} ${(state.routeTargets || []).join(" ")}`), "Native route target is visible", { context, state });
}

function assertW12KCockpit(state, contextLabel) {
  assert(state.commandCount === 1, "Cockpit command area must render once", { context: contextLabel, state });
  assert(state.commandChipCount >= 3, "Cockpit command chips did not render", { context: contextLabel, state });
  assert(state.refreshActionCount === 1, "Cockpit refresh control must render once", { context: contextLabel, state });
  assert(state.inboundActionCount >= 2, "Inbound receiving navigation is missing", { context: contextLabel, state });
  assert(state.outboundActionCount >= 2, "Outbound picking navigation is missing", { context: contextLabel, state });
  assert(state.stockExceptionActionCount >= 2, "Stock exceptions navigation is missing", { context: contextLabel, state });
  assert(state.movementActionCount >= 2, "Movement visibility navigation is missing", { context: contextLabel, state });
  assert(state.transferActionCount >= 2, "Transfer visibility navigation is missing", { context: contextLabel, state });
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
  assert((state.text || "").includes("Read-only guardrail"), "Read-only guardrail label is missing", { context: contextLabel, state });
  assert(state.warehousePageHeadCount <= 1, "Duplicate Warehouse page head chrome is visible", { context: contextLabel, state });
  assert(state.allPageHeadCount === 0, "Frappe page-head chrome is visible in Warehouse cockpit", { context: contextLabel, state });
  assert((state.sidebarDuplicates || []).length === 0, "Duplicate Warehouse sidebar items are visible", { context: contextLabel, state });
}

async function assertCockpit(page, contextLabel) {
  await waitForCockpit(page);
  const state = await snapshot(page);
  assertClean(state, contextLabel);
  assert(state.cockpitCount === 1, "Cockpit shell did not render", { context: contextLabel, state });
  assert(state.pulseCount >= 6, "Warehouse pulse cards did not render", { context: contextLabel, state });
  assert(state.startCount >= 4, "Start Here cards did not render", { context: contextLabel, state });
  assert(state.workCount >= 2, "Work To Do paired cards did not render", { context: contextLabel, state });
  assert(state.riskCount >= 2, "Risks To Resolve cards did not render", { context: contextLabel, state });
  assert(state.movementCount >= 2, "Movement To Understand cards did not render", { context: contextLabel, state });
  assert(state.guardrailCount === 1, "Read-only guardrail did not render", { context: contextLabel, state });
  if (EXPECT_W12K) assertW12KCockpit(state, contextLabel);
  return state;
}

async function exerciseRouteAction(page, selector, expectedPath, viewName, contextLabel) {
  await page.locator(selector).first().click();
  await page.waitForURL((url) => url.pathname === expectedPath || url.pathname === expectedPath.replace("/desk/", "/app/"), { timeout: TIMEOUT });
  await waitForWorklist(page, viewName);
  assertClean(await snapshot(page), contextLabel);
}

async function exerciseUser(browser, user, viewport) {
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

    if (viewport.key === "desktop-1440") {
      await exerciseRouteAction(page, "[data-warehouse-open-inbound]", "/desk/warehouse-console-worklist/inbound-receiving", "inbound-receiving", `${user.key}:inbound`);
      if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-inbound");
      await openRoute(page, ["warehouse-console"], "/desk/warehouse-console", waitForCockpit);

      await exerciseRouteAction(page, "[data-warehouse-open-outbound]", "/desk/warehouse-console-worklist/outbound-picking", "outbound-picking", `${user.key}:outbound`);
      if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-outbound");
      await openRoute(page, ["warehouse-console"], "/desk/warehouse-console", waitForCockpit);

      await exerciseRouteAction(page, "[data-warehouse-open-stock-exceptions]", "/desk/warehouse-console-worklist/stock-exceptions", "stock-exceptions", `${user.key}:stock-exceptions`);
      if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-stock-exceptions");
      await openRoute(page, ["warehouse-console"], "/desk/warehouse-console", waitForCockpit);

      await exerciseRouteAction(page, "[data-warehouse-open-movement]", "/desk/warehouse-console-worklist/movement-visibility", "movement-visibility", `${user.key}:movement`);
      if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-movement-visibility");
      await openRoute(page, ["warehouse-console"], "/desk/warehouse-console", waitForCockpit);

      await exerciseRouteAction(page, "[data-warehouse-open-transfer]", "/desk/warehouse-console-worklist/transfer-visibility", "transfer-visibility", `${user.key}:transfer`);
      if (ASSET_ROOT) await waitForOverrideHit(diagnostics, "warehouse-transfer-visibility");
      await openRoute(page, ["warehouse-console"], "/desk/warehouse-console", waitForCockpit);
    }

    diagnostics.snapshots.push({ name: `${user.key}-${viewport.key}:final`, sidebarCollapsed: viewport.width <= 520 ? await collapseBodySidebarForNarrowViewport(page) : true, state: await snapshot(page), screenshot: await capture(page, `${user.key}-${viewport.key}-cockpit`) });
  } finally {
    await context.close();
  }
  return diagnostics;
}

async function main() {
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
