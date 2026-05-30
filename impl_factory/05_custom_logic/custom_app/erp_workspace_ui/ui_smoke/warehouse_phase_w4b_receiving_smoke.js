const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const TIMEOUT = Number(process.env.ERPW_WAREHOUSE_W4B_TIMEOUT || process.env.ERPW_WAREHOUSE_W4A_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_WAREHOUSE_W4B_ARTIFACT_DIR || path.join(
  fs.existsSync("/freeze-artifacts") ? "/freeze-artifacts" : path.join(__dirname, "artifacts"),
  `warehouse-w4b-receiving-${new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z")}`
);
const ASSET_ROOT = process.env.ERPW_WAREHOUSE_W4B_ASSET_ROOT || process.env.ERPW_WAREHOUSE_W4A_ASSET_ROOT || "";
const WARM_TARGET_MS = Number(process.env.ERPW_WAREHOUSE_W4B_WARM_TARGET_MS || 3000);

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

const FORBIDDEN_ACTION_RE = /\b(Receive|Ship|Dispatch|Post|Submit|Cancel|Amend|Reconcile|Stock Entry|Purchase Receipt|Delivery Note|Stock Reconciliation|Reserve|Unreserve|Assign Serial|Assign Batch|Item Price|Default Supplier|Item Supplier)\b/i;
const FORBIDDEN_COPY_RE = /\b(Productized|native ERP|governed|deferred|route only|mutation|backend|frontend|framework|Frappe|smoke|test|Quick Find|\bSearch\b)\b/i;
const NATIVE_ROUTE_RE = /\/desk\/Form\/|\/app\/|#Form\/|query-report|\/desk\/List\//i;
const VALUATION_RE = /stock value|valuation rate|stock_value|valuation_rate|landed cost|billing|payment|tax/i;

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

function recordOverrideHit(diagnostics, key, request, extra = {}) {
  remember(diagnostics.overrideHits, { key, url: bounded(request.url()), method: request.method(), postData: bounded(request.postData() || "", 500), ...extra }, 120);
}

function sourceSidebarPayload(allowed = true) {
  const items = allowed ? [
    { key: "warehouse_console_home", label: "Overview", icon: "item", target: { kind: "page", route: "warehouse-console" } },
    { key: "inbound_receiving", label: "Inbound Receiving", icon: "quotation", target: { kind: "worklist", queue_key: "inbound_receiving" } },
  ] : [];
  return {
    workspace: {
      workspace_id: "warehouse",
      title: "Warehouse Console",
      routes: {
        home: "warehouse-console",
        home_path: "/desk/warehouse-console",
        worklist: "warehouse-console-worklist",
        worklist_path: "/desk/warehouse-console-worklist",
        receiving: "warehouse-console-receiving",
        receiving_path: "/desk/warehouse-console-receiving",
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

function sourceInboundRows() {
  return [
    {
      key: "PO-OVERDUE",
      name: "PO-OVERDUE",
      purchase_order: "PO-OVERDUE",
      supplier: "Acme Supply",
      required_date: "2026-05-24",
      target_warehouse: "Stores - M",
      line_count: 2,
      item_count: 2,
      received_percent: "0%",
      remaining_summary: "16 Nos remaining",
      status: "To Receive",
      state_key: "overdue",
      state_label: "Overdue",
      age_label: "Overdue 4d",
      lines: [
        { item_code: "ITEM-001", item_name: "Filter Kit", remaining_qty: "10", uom: "Nos", target_warehouse: "Stores - M", required_date: "2026-05-24" },
        { item_code: "ITEM-002", item_name: "Packing Roll", remaining_qty: "6", uom: "Nos", target_warehouse: "Stores - M", required_date: "2026-05-24" },
      ],
    },
    {
      key: "PO-PARTIAL",
      name: "PO-PARTIAL",
      purchase_order: "PO-PARTIAL",
      supplier: "Partial Goods",
      required_date: "2026-06-02",
      target_warehouse: "Main - M",
      line_count: 1,
      item_count: 1,
      received_percent: "35%",
      remaining_summary: "13 Nos remaining",
      status: "To Receive",
      state_key: "partially_received",
      state_label: "Partially Received",
      age_label: "Due 2026-06-02",
      lines: [
        { item_code: "ITEM-020", item_name: "Valve Set", remaining_qty: "13", uom: "Nos", target_warehouse: "Main - M", required_date: "2026-06-02" },
      ],
    },
  ];
}

function sourceInboundPayload(filters = {}) {
  const rows = sourceInboundRows().filter((row) => {
    if (filters.supplier && !row.supplier.toLowerCase().includes(String(filters.supplier).toLowerCase())) return false;
    if (filters.purchase_order && !row.purchase_order.toLowerCase().includes(String(filters.purchase_order).toLowerCase())) return false;
    return true;
  });
  const groupSpecs = [
    ["overdue", "Overdue", "Past required date."],
    ["due_today", "Due Today", "Expected today."],
    ["partially_received", "Partially Received", "Some quantity has arrived."],
    ["expected_soon", "Expected Soon", "Due in the next 14 days."],
  ];
  const groups = groupSpecs.map(([key, title, summary]) => ({ key, title, summary, rows: rows.filter((row) => row.state_key === key) }));
  const counts = Object.fromEntries(groupSpecs.map(([key]) => [key, groups.find((group) => group.key === key).rows.length]));
  const cards = [
    ["due_today", "Receiving Due Today", "Expected today."],
    ["overdue", "Overdue Receiving", "Past required date."],
    ["partially_received", "Partially Received", "Some quantity has arrived."],
    ["expected_soon", "Expected Soon", "Due in the next 14 days."],
  ].map(([key, title, note]) => ({ key, label: title, title, value: counts[key], state: "live", note, empty_message: "No inbound receiving needs attention." }));
  return {
    workspace: sourceSidebarPayload(true).workspace,
    context: { has_warehouse_access: true, role_family: "Warehouse", role_variant: "warehouse_manager", can_view_valuation: false },
    state: rows.length
      ? { kind: "ready", title: "Warehouse Console ready", detail: "Stock visibility and warehouse posture are available for review." }
      : { kind: "empty", title: "No inbound receiving needs attention", detail: "No receiving matches these filters." },
    page: { title: "Inbound Receiving", key: "inbound_receiving" },
    summary: { title: "Inbound Receiving", subtitle: "Expected supplier stock due into warehouse.", chips: [{ label: "Read-only" }, { label: `${rows.length} shown` }] },
    controls: {
      fields: [
        { key: "purchase_order", label: "Purchase Order", type: "text", value: filters.purchase_order || "", placeholder: "Filter order" },
        { key: "supplier", label: "Supplier", type: "text", value: filters.supplier || "", placeholder: "Filter supplier" },
        { key: "warehouse", label: "Warehouse", type: "text", value: filters.warehouse || "", placeholder: "Filter warehouse" },
        { key: "state", label: "Receiving State", type: "select", value: filters.state || "", options: [{ label: "All", value: "" }, { label: "Overdue", value: "overdue" }] },
      ],
      actions: [{ key: "refresh", label: "Refresh" }, { key: "reset_filters", label: "Reset" }, { key: "apply_filters", label: "Apply", kind: "primary" }],
      scopeChips: ["Purchase Orders", "Read-only inbound"],
    },
    cards,
    groups,
    rows,
    action_targets: {},
    valuation: { visible: false, fields: [] },
    fetched_at: "2026-05-28 00:00:00",
  };
}

function sourceOverviewPayload() {
  const inbound = sourceInboundPayload();
  return {
    workspace: sourceSidebarPayload(true).workspace,
    context: { has_warehouse_access: true, role_family: "Warehouse", role_variant: "warehouse_manager", can_view_valuation: false },
    state: { kind: "ready", title: "Warehouse Console ready", detail: "Stock visibility and warehouse posture are available for review." },
    sidebar: sourceSidebarPayload(true).sidebar,
    kpis: [
      { key: "active_warehouses", label: "Active Warehouses", value: 4, state: "live", note: "Warehouse locations available for stock review." },
      { key: "stocked_items", label: "Stocked Items", value: 18, state: "live", note: "Item and warehouse positions with stock on hand." },
      { key: "low_stock", label: "Low Stock", value: 2, state: "live", note: "Projected quantity below zero." },
      { key: "receiving_due", label: "Receiving Due", value: 1, state: "live", note: "Submitted purchase orders due for review." },
      { key: "outbound_due", label: "Outbound Due", value: 1, state: "live", note: "Open picking work visible to your role." },
      { key: "transfer_requests", label: "Transfer Requests", value: 2, state: "live", note: "Internal warehouse requests waiting for review." },
    ],
    inbound: { state: inbound.state, counts: { overdue: 1, due_today: 0, partially_received: 1, expected_soon: 0 }, cards: inbound.cards, preview_rows: inbound.rows, groups: inbound.groups, total_count: inbound.rows.length, queue_key: "inbound_receiving", queue_route: "warehouse-console-worklist", row_limit: 50, horizon_days: 14 },
    sections: [],
    allowed_actions: [{ key: "refresh", label: "Refresh", kind: "read_only" }],
    action_targets: {},
    valuation: { visible: false, fields: [] },
    fetched_at: "2026-05-28 00:00:00",
  };
}

function sourceReceivingPayload(po = "PO-OVERDUE") {
  const row = sourceInboundRows().find((item) => item.purchase_order === po) || sourceInboundRows()[0];
  return {
    workspace: sourceSidebarPayload(true).workspace,
    context: { has_warehouse_access: true, role_family: "Warehouse", role_variant: "warehouse_manager", can_view_valuation: false },
    state: { kind: "ready", title: "Warehouse Console ready", detail: "Stock visibility and warehouse posture are available for review." },
    page: { title: "Receiving Review", key: "receiving_review", purchase_order: row.purchase_order },
    header: {
      purchase_order: row.purchase_order,
      supplier: row.supplier,
      required_date: row.required_date,
      target_warehouse: row.target_warehouse,
      state_key: row.state_key,
      state_label: row.state_label,
      age_label: row.age_label,
      received_percent: row.received_percent,
      remaining_summary: row.remaining_summary,
      line_count: row.lines.length,
      item_count: row.lines.length,
      status: row.status,
    },
    summary_cards: [
      { key: "state", label: "Receiving State", value: row.state_label, note: row.age_label },
      { key: "received", label: "Received", value: row.received_percent, note: "Quantity already arrived." },
      { key: "open_lines", label: "Open Lines", value: row.lines.length, note: row.remaining_summary },
      { key: "items", label: "Items", value: row.lines.length, note: row.target_warehouse },
    ],
    tabs: [{ key: "item_lines", label: "Item Lines", count: row.lines.length }, { key: "receipt_history", label: "Receipt History", count: 1 }],
    lines: row.lines.map((line, index) => ({
      item_code: line.item_code,
      item_name: line.item_name,
      ordered_qty: index === 0 ? "10" : "6",
      received_qty: row.purchase_order === "PO-PARTIAL" ? "7" : "0",
      remaining_qty: line.remaining_qty,
      uom: line.uom,
      target_warehouse: line.target_warehouse,
      required_date: line.required_date,
      status: row.purchase_order === "PO-PARTIAL" ? "Partially arrived" : "Overdue",
    })),
    receipt_history: [{ receipt_id: "REC-0001", posting_date: "2026-05-25", status: "Recorded", item_count: 1, quantity_summary: "7 Nos" }],
    allowed_actions: [{ key: "refresh", label: "Refresh", kind: "read_only" }, { key: "back_to_inbound", label: "Back to inbound receiving", kind: "navigation" }],
    action_targets: { inbound_queue: { route: "warehouse-console-worklist", queue_key: "inbound_receiving" } },
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
    const isReceiving = /warehouse-console-receiving/i.test(text);
    const isWorklist = /warehouse-console-worklist/i.test(text);
    const file = isReceiving
      ? "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_receiving/warehouse_console_receiving.js"
      : isWorklist
        ? "erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/warehouse_console_worklist.js"
        : "erp_workspace_ui/erp_workspace_ui/page/warehouse_console/warehouse_console.js";
    const name = isReceiving ? "warehouse-console-receiving" : isWorklist ? "warehouse-console-worklist" : "warehouse-console";
    const script = readSource(file);
    recordOverrideHit(diagnostics, "desk-page-getpage", request, { fulfilled: Boolean(script), page: name });
    const pageDoc = { doctype: "Page", name, page_name: name, title: isReceiving ? "Receiving Review" : isWorklist ? "Inbound Receiving" : "Warehouse Console", module: "ERP Workspace UI", standard: "Yes", content: "", script };
    return route.fulfill({ status: script ? 200 : 404, contentType: "application/json", body: JSON.stringify({ docs: [pageDoc], message: pageDoc }) });
  });
  await context.route("**/api/method/erp_workspace_ui.warehouse_console.service.get_warehouse_console_overview**", async (route) => {
    recordOverrideHit(diagnostics, "warehouse-overview", route.request(), { fulfilled: true });
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ message: sourceOverviewPayload() }) });
  });
  await context.route("**/api/method/erp_workspace_ui.warehouse_console.service.get_warehouse_inbound_receiving_queue**", async (route) => {
    let filters = {};
    try {
      const body = route.request().postDataJSON() || {};
      const raw = body.filters;
      filters = typeof raw === "string" ? JSON.parse(raw || "{}") : (raw || {});
    } catch (error) {
      filters = {};
    }
    recordOverrideHit(diagnostics, "warehouse-inbound-queue", route.request(), { fulfilled: true, filters });
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ message: sourceInboundPayload(filters) }) });
  });
  await context.route("**/api/method/erp_workspace_ui.warehouse_console.service.get_warehouse_receiving_review**", async (route) => {
    let purchaseOrder = "PO-OVERDUE";
    try {
      const body = route.request().postDataJSON() || {};
      purchaseOrder = body.purchase_order || purchaseOrder;
    } catch (error) {
      purchaseOrder = "PO-OVERDUE";
    }
    recordOverrideHit(diagnostics, "warehouse-receiving-detail", route.request(), { fulfilled: true, purchaseOrder });
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ message: sourceReceivingPayload(purchaseOrder) }) });
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
    inboundShellCount: document.querySelectorAll('.warehouse-inbound-shell[data-warehouse-view="inbound-receiving"]').length,
    receivingShellCount: document.querySelectorAll('.warehouse-receiving-shell[data-warehouse-view="receiving-review"]').length,
    receivingLineCount: document.querySelectorAll("[data-warehouse-receiving-line]").length,
    receivingHistoryCount: document.querySelectorAll("[data-warehouse-receiving-history-row]").length,
    warehouseConsoleDiagnostics: window.erpWorkspaceWarehouseConsole && window.erpWorkspaceWarehouseConsole.diagnostics ? { ...window.erpWorkspaceWarehouseConsole.diagnostics } : {},
  })).catch((error) => ({ error: error && error.message ? error.message : String(error) }));
  snapshot.screenshot = screenshot;
  remember(diagnostics.snapshots, { label, ...snapshot }, 30);
  return snapshot;
}

async function waitForInboundReady(page, diagnostics, label) {
  try {
    await page.waitForFunction(() => {
      const shell = document.querySelector('.warehouse-inbound-shell[data-erpw-workspace="warehouse"][data-warehouse-view="inbound-receiving"]');
      return Boolean(shell
        && shell.getAttribute("data-erpw-console-runtime") === "ready"
        && shell.querySelectorAll("[data-warehouse-inbound-queue-card]").length >= 4
        && shell.querySelectorAll("[data-warehouse-inbound-row]").length >= 1
        && shell.querySelector("[data-warehouse-row-open-detail]"));
    }, null, { timeout: TIMEOUT });
  } catch (error) {
    error.details = { ...(error.details || {}), snapshot: await diagnosticSnapshot(page, diagnostics, `${label}-inbound-timeout`) };
    throw error;
  }
}

async function waitForReceivingReady(page, diagnostics, label) {
  try {
    await page.waitForFunction(() => {
      const shell = document.querySelector('.warehouse-receiving-shell[data-erpw-workspace="warehouse"][data-warehouse-view="receiving-review"]');
      return Boolean(shell
        && shell.getAttribute("data-erpw-console-runtime") === "ready"
        && shell.querySelectorAll("[data-warehouse-receiving-card]").length >= 4
        && shell.querySelectorAll("[data-warehouse-receiving-line]").length >= 1
        && shell.querySelectorAll("[data-warehouse-receiving-tab]").length >= 2);
    }, null, { timeout: TIMEOUT });
  } catch (error) {
    error.details = { ...(error.details || {}), snapshot: await diagnosticSnapshot(page, diagnostics, `${label}-receiving-timeout`) };
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
  if (viewKind === "receiving") {
    if (ASSET_ROOT) await waitForOverrideHit(page, diagnostics, "warehouse-receiving-detail", label);
    await waitForReceivingReady(page, diagnostics, label);
  } else {
    if (ASSET_ROOT) await waitForOverrideHit(page, diagnostics, "warehouse-inbound-queue", label);
    await waitForInboundReady(page, diagnostics, label);
  }
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
      inboundShellCount: Array.from(document.querySelectorAll('.warehouse-inbound-shell[data-warehouse-view="inbound-receiving"]')).filter(visible).length,
      receivingShellCount: Array.from(document.querySelectorAll('.warehouse-receiving-shell[data-warehouse-view="receiving-review"]')).filter(visible).length,
      receivingCardCount: Array.from(document.querySelectorAll("[data-warehouse-receiving-card]")).filter(visible).length,
      receivingLineCount: Array.from(document.querySelectorAll("[data-warehouse-receiving-line]")).filter(visible).length,
      receivingHistoryCount: Array.from(document.querySelectorAll("[data-warehouse-receiving-history-row]")).filter(visible).length,
      tabCount: Array.from(document.querySelectorAll("[data-warehouse-receiving-tab]")).filter(visible).length,
      detailButtonCount: Array.from(document.querySelectorAll("[data-warehouse-row-open-detail]")).filter(visible).length,
      searchUtilityVisible: Array.from(document.querySelectorAll("[data-erpw-sales-search-open]")).some(visible),
      horizontalOverflow: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
      bodyWidth: document.documentElement.clientWidth,
      warehouseConsoleDiagnostics: window.erpWorkspaceWarehouseConsole && window.erpWorkspaceWarehouseConsole.diagnostics ? { ...window.erpWorkspaceWarehouseConsole.diagnostics } : {},
      hasExportedReceivingRenderer: Boolean(window.erpWorkspaceWarehouseConsole && typeof window.erpWorkspaceWarehouseConsole.renderReceivingReview === "function"),
      hasPageReceivingRenderer: Boolean(window.frappe && frappe.pages && frappe.pages["warehouse-console-receiving"] && typeof frappe.pages["warehouse-console-receiving"].__erpwRenderWarehouseReceivingReview === "function"),
    };
  });
}

function assertCleanWarehouseUi(state, context) {
  assert(state.shellCount === 1, "Warehouse shell count must remain 1", { context, state });
  assert(state.headerCount === 1, "Warehouse header count must remain 1", { context, state });
  assert(state.sidebarCount <= 1, "Warehouse sidebar count must not duplicate", { context, state });
  assert(state.horizontalOverflow <= 2, "Warehouse page has horizontal overflow", { context, state });
  assert(!state.searchUtilityVisible, "Warehouse search entry must stay inactive in W4B", { context, state });
  assert(!FORBIDDEN_ACTION_RE.test(state.actionText), "Forbidden stock action control is visible", { context, state });
  assert(!FORBIDDEN_COPY_RE.test(state.text), "Developer or governance copy is visible", { context, state });
  assert(!VALUATION_RE.test(state.text), "Valuation or commercial text is visible", { context, state });
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

    await openRoute(page, ["warehouse-console-worklist", "inbound-receiving"], "/desk/warehouse-console-worklist/inbound-receiving", diagnostics, `${user.key}:queue`, "inbound");
    let state = await snapshot(page);
    assertCleanWarehouseUi(state, `${user.key}:queue`);
    assert(state.detailButtonCount >= 1, "Inbound queue did not expose receiving review drilldown", { user: user.key, state });

    await page.locator("[data-warehouse-row-open-detail]").first().click();
    await page.waitForURL((url) => /\/(?:desk|app)\/warehouse-console-receiving\//.test(url.pathname), { timeout: TIMEOUT });
    if (ASSET_ROOT) await waitForOverrideHit(page, diagnostics, "warehouse-receiving-detail", `${user.key}:row-drilldown`);
    await waitForReceivingReady(page, diagnostics, `${user.key}:row-drilldown`);
    state = await snapshot(page);
    assertCleanWarehouseUi(state, `${user.key}:row-drilldown`);
    assert(state.receivingCardCount >= 4, "Receiving review cards did not render", { user: user.key, state });
    assert(state.receivingLineCount >= 1, "Receiving review lines did not render", { user: user.key, state });
    assert(state.tabCount >= 2, "Receiving review tabs did not render", { user: user.key, state });
    await capture(page, `${user.key}-receiving-review`);

    await page.locator('[data-warehouse-receiving-tab="receipt_history"]').click();
    state = await snapshot(page);
    assertCleanWarehouseUi(state, `${user.key}:receipt-history-tab`);

    await page.locator("[data-warehouse-receiving-refresh]").click();
    await waitForReceivingReady(page, diagnostics, `${user.key}:refresh`);
    state = await snapshot(page);
    assertCleanWarehouseUi(state, `${user.key}:refresh`);

    await page.reload({ waitUntil: "domcontentloaded", timeout: TIMEOUT });
    await waitForReceivingReady(page, diagnostics, `${user.key}:refresh-page`);
    state = await snapshot(page);
    assertCleanWarehouseUi(state, `${user.key}:refresh-page`);
    const directPurchaseOrder = Array.isArray(state.route) && state.route[1] ? String(state.route[1]) : "PO-OVERDUE";

    await page.locator("[data-warehouse-receiving-back]").click();
    await page.waitForURL((url) => /\/(?:desk|app)\/warehouse-console-worklist\/inbound-receiving$/.test(url.pathname), { timeout: TIMEOUT });
    await waitForInboundReady(page, diagnostics, `${user.key}:back-to-queue`);
    state = await snapshot(page);
    assertCleanWarehouseUi(state, `${user.key}:back-to-queue`);

    for (const viewport of VIEWPORTS) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      const started = Date.now();
      await openRoute(page, ["warehouse-console-receiving", directPurchaseOrder], `/desk/warehouse-console-receiving/${encodeURIComponent(directPurchaseOrder)}`, diagnostics, `${user.key}:${viewport.key}:direct`, "receiving");
      const elapsedMs = Date.now() - started;
      state = await snapshot(page);
      assertCleanWarehouseUi(state, `${user.key}:${viewport.key}:direct`);
      assert(state.receivingShellCount === 1, "Receiving review shell count must remain 1", { user: user.key, viewport, state });
      assert(state.receivingLineCount >= 1, "Receiving review lines did not render", { user: user.key, viewport, state });
      assert(elapsedMs < WARM_TARGET_MS || viewport.key === "laptop-1136", "Warehouse receiving warm route exceeded target", { user: user.key, viewport, elapsedMs });
      await capture(page, `${user.key}-${viewport.key}-receiving-review`);
    }

    state = await snapshot(page);
    assert(state.hasExportedReceivingRenderer, "Warehouse exported receiving renderer is missing", { user: user.key, state, diagnostics });
    assert(state.hasPageReceivingRenderer, "Warehouse page receiving renderer is missing", { user: user.key, state, diagnostics });
    assert((state.warehouseConsoleDiagnostics || {}).renderReceivingReviewEntered >= 1, "Warehouse receiving renderer was not entered", { user: user.key, state, diagnostics });
    assert((state.warehouseConsoleDiagnostics || {}).receivingServiceCallAttempted >= 1, "Warehouse receiving service call was not attempted", { user: user.key, state, diagnostics });
    if (ASSET_ROOT) {
      assert(diagnostics.overrideHits.some((hit) => hit.key === "desk-page-getpage" && hit.page === "warehouse-console-receiving"), "Warehouse receiving getpage source override was not used", { user: user.key, diagnostics });
      assert(diagnostics.overrideHits.some((hit) => hit.key === "warehouse-page-asset"), "Warehouse page asset source override was not used", { user: user.key, diagnostics });
      assert(diagnostics.overrideHits.some((hit) => hit.key === "warehouse-receiving-detail"), "Warehouse receiving detail source override was not used", { user: user.key, diagnostics });
    }
    assert(!diagnostics.consoleErrors.some((entry) => entry.type === "error"), "Warehouse W4B smoke recorded console errors", { user: user.key, diagnostics });
    assert(diagnostics.pageErrors.length === 0, "Warehouse W4B smoke recorded page errors", { user: user.key, diagnostics });
    assert(diagnostics.failedResponses.length === 0, "Warehouse W4B smoke recorded failed responses", { user: user.key, diagnostics });
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
  assert(AUTHORIZED_USERS.length > 0, "No Warehouse W4B smoke credentials were provided. Set ERPW_WAREHOUSE_MANAGER_USERNAME/PASSWORD or ERPW_WAREHOUSE_USER_USERNAME/PASSWORD.");
  const browser = await chromium.launch({ headless: process.env.ERPW_HEADLESS !== "0" });
  const summary = { status: "pass", artifactDir: ARTIFACT_DIR, sourceOverride: Boolean(ASSET_ROOT), authorizedUsers: AUTHORIZED_USERS.map((user) => user.key), authorized: [] };
  try {
    for (const user of AUTHORIZED_USERS) {
      summary.authorized.push(await exerciseUser(browser, user));
    }
    fs.writeFileSync(path.join(ARTIFACT_DIR, "warehouse-w4b-receiving-summary.json"), `${JSON.stringify(summary, null, 2)}\n`);
  } catch (error) {
    summary.status = "fail";
    summary.error = error && error.message ? error.message : String(error);
    summary.details = error && error.details ? error.details : {};
    fs.writeFileSync(path.join(ARTIFACT_DIR, "warehouse-w4b-receiving-summary.json"), `${JSON.stringify(summary, null, 2)}\n`);
    throw error;
  } finally {
    await browser.close();
  }
  console.log(`Warehouse W4B receiving smoke passed. Summary: ${path.join(ARTIFACT_DIR, "warehouse-w4b-receiving-summary.json")}`);
})().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exit(1);
});
