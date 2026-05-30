/* global frappe, $ */

(function () {
  const workspaceRegistry = window.erpWorkspaceUiWorkspaceRegistry || {};
  const warehouseWorkspace = typeof workspaceRegistry.warehouse === "function" ? workspaceRegistry.warehouse() : null;
  const warehouseRoutes = warehouseWorkspace && warehouseWorkspace.routes ? warehouseWorkspace.routes : {};
  const warehouseMethods = warehouseWorkspace && warehouseWorkspace.methods ? warehouseWorkspace.methods : {};
  const PAGE_KEY = warehouseRoutes.home || "warehouse-console";
  const WORKLIST_PAGE_KEY = warehouseRoutes.worklist || "warehouse-console-worklist";
  const RECEIVING_PAGE_KEY = warehouseRoutes.receiving || "warehouse-console-receiving";
  const PICKING_PAGE_KEY = warehouseRoutes.picking || "warehouse-console-picking";
  const STOCK_EXCEPTION_PAGE_KEY = warehouseRoutes.stockException || warehouseRoutes.stock_exception || "warehouse-console-stock-exception";
  const STOCK_POSTURE_PAGE_KEY = warehouseRoutes.stockPosture || warehouseRoutes.stock_posture || "warehouse-console-stock-posture";
  const MOVEMENT_PAGE_KEY = warehouseRoutes.movement || warehouseRoutes.movement_review || "warehouse-console-movement";
  const INBOUND_QUEUE_KEY = "inbound_receiving";
  const OUTBOUND_QUEUE_KEY = "outbound_picking";
  const STOCK_EXCEPTIONS_KEY = "stock_exceptions";
  const MOVEMENT_VISIBILITY_KEY = "movement_visibility";
  const TRANSFER_VISIBILITY_KEY = "transfer_visibility";
  const OVERVIEW_METHOD = warehouseMethods.overview || "erp_workspace_ui.warehouse_console.service.get_warehouse_console_overview";
  const INBOUND_METHOD = warehouseMethods.inboundQueue || warehouseMethods.inbound_queue || "erp_workspace_ui.warehouse_console.service.get_warehouse_inbound_receiving_queue";
  const OUTBOUND_METHOD = warehouseMethods.outboundQueue || warehouseMethods.outbound_queue || "erp_workspace_ui.warehouse_console.service.get_warehouse_outbound_picking_queue";
  const STOCK_EXCEPTIONS_METHOD = warehouseMethods.stockExceptions || warehouseMethods.stock_exceptions || "erp_workspace_ui.warehouse_console.service.get_warehouse_stock_exceptions";
  const MOVEMENT_VISIBILITY_METHOD = warehouseMethods.movementVisibility || warehouseMethods.movement_visibility || "erp_workspace_ui.warehouse_console.service.get_warehouse_movement_visibility_queue";
  const TRANSFER_VISIBILITY_METHOD = warehouseMethods.transferVisibility || warehouseMethods.transfer_visibility || "erp_workspace_ui.warehouse_console.service.get_warehouse_transfer_visibility_queue";
  const RECEIVING_METHOD = warehouseMethods.receivingDetail || warehouseMethods.receiving_detail || "erp_workspace_ui.warehouse_console.service.get_warehouse_receiving_review";
  const PICKING_METHOD = warehouseMethods.pickingDetail || warehouseMethods.picking_detail || "erp_workspace_ui.warehouse_console.service.get_warehouse_picking_review";
  const STOCK_EXCEPTION_REVIEW_METHOD = warehouseMethods.stockExceptionReview || warehouseMethods.stock_exception_review || "erp_workspace_ui.warehouse_console.service.get_warehouse_stock_exception_review";
  const STOCK_POSTURE_REVIEW_METHOD = warehouseMethods.stockPostureReview || warehouseMethods.stock_posture_review || "erp_workspace_ui.warehouse_console.service.get_warehouse_stock_posture_review";
  const MOVEMENT_REVIEW_METHOD = warehouseMethods.movementReview || warehouseMethods.movement_review || "erp_workspace_ui.warehouse_console.service.get_warehouse_movement_review";
  const CONSOLE_RUNTIME_URL = "/assets/erp_workspace_ui/js/runtime/console/workspace_console_runtime.js";
  const BOOTSTRAP_RETRY_DELAYS = [350, 900, 1800];
  let consoleRuntimePromise = null;
  let overviewRenderSerial = 0;
  let activeOverviewRenderState = null;
  let activeOverviewGuardBound = false;
  let inboundRouteGuardBound = false;
  let inboundRouteRenderSerial = 0;
  let receivingRouteGuardBound = false;
  let receivingRouteRenderSerial = 0;
  let pickingRouteGuardBound = false;
  let pickingRouteRenderSerial = 0;
  let stockExceptionRouteGuardBound = false;
  let stockExceptionRouteRenderSerial = 0;
  let stockPostureRouteGuardBound = false;
  let stockPostureRouteRenderSerial = 0;
  let movementRouteGuardBound = false;
  let movementRouteRenderSerial = 0;

  function consoleRuntime() {
    return window.erpWorkspaceConsoleRuntime || {};
  }

  function hasConsoleRuntime() {
    const runtime = consoleRuntime();
    return Boolean(runtime && typeof runtime.escapeHtml === "function");
  }

  function ensureConsoleRuntime() {
    if (hasConsoleRuntime()) return Promise.resolve(consoleRuntime());
    if (consoleRuntimePromise) return consoleRuntimePromise;
    consoleRuntimePromise = new Promise((resolve, reject) => {
      frappe.require(CONSOLE_RUNTIME_URL, () => {
        if (hasConsoleRuntime()) {
          resolve(consoleRuntime());
          return;
        }
        reject(new Error("Shared console runtime is not loaded on this page."));
      });
    }).catch((error) => {
      consoleRuntimePromise = null;
      throw error;
    });
    return consoleRuntimePromise;
  }

  function escapeHtml(value) {
    const method = consoleRuntime().escapeHtml;
    if (typeof method === "function") return method(value);
    if (frappe.utils && typeof frappe.utils.escape_html === "function") {
      return frappe.utils.escape_html(value == null ? "" : String(value));
    }
    return String(value == null ? "" : value).replace(/[&<>"']/g, (character) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "\"": "&quot;",
      "'": "&#39;",
    }[character] || character));
  }

  function pathRouteParts() {
    const path = String((window.location && window.location.pathname) || "").replace(/^\/+/, "");
    const parts = path.split("/").filter(Boolean);
    const routeParts = parts[0] === "desk" || parts[0] === "app" ? parts.slice(1) : parts;
    return routeParts.map((part) => {
      try {
        return decodeURIComponent(part || "");
      } catch (error) {
        return part || "";
      }
    });
  }

  function normalizeQueueKey(value) {
    return String(value || "").trim().replace(/-/g, "_");
  }

  function activeWorklistQueueKey() {
    const pathRoute = pathRouteParts();
    if (String(pathRoute[0] || "") === WORKLIST_PAGE_KEY) return normalizeQueueKey(pathRoute[1] || INBOUND_QUEUE_KEY);
    const route = frappe.get_route ? frappe.get_route() : [];
    if (Array.isArray(route) && String(route[0] || "") === WORKLIST_PAGE_KEY) return normalizeQueueKey(route[1] || INBOUND_QUEUE_KEY);
    return "";
  }

  function isSupportedWorklistQueue(queueKey) {
    const key = normalizeQueueKey(queueKey);
    return key === INBOUND_QUEUE_KEY || key === OUTBOUND_QUEUE_KEY || key === STOCK_EXCEPTIONS_KEY || key === MOVEMENT_VISIBILITY_KEY || key === TRANSFER_VISIBILITY_KEY;
  }

  function worklistViewName(queueKey) {
    const key = normalizeQueueKey(queueKey);
    if (key === OUTBOUND_QUEUE_KEY) return "outbound-picking";
    if (key === STOCK_EXCEPTIONS_KEY) return "stock-exceptions";
    if (key === MOVEMENT_VISIBILITY_KEY) return "movement-visibility";
    if (key === TRANSFER_VISIBILITY_KEY) return "transfer-visibility";
    return "inbound-receiving";
  }

  function stableObjectSignature(value) {
    if (!value || typeof value !== "object") return "";
    return Object.keys(value).sort().map((key) => `${key}:${String(value[key] == null ? "" : value[key])}`).join("|");
  }

  function worklistLoadSignature(queueKey, filters) {
    return `${inboundRouteSignature()}::${normalizeQueueKey(queueKey)}::${stableObjectSignature(filters || {})}`;
  }

  function hasRenderedWorklistShell(viewState, queueKey) {
    const host = viewState && viewState.$host && viewState.$host.get ? viewState.$host.get(0) : null;
    if (!host || !document.documentElement.contains(host)) return false;
    const viewName = worklistViewName(queueKey);
    return Boolean(host.querySelector(`.sales-console-shell[data-erpw-workspace="warehouse"][data-warehouse-view="${viewName}"]`));
  }

  function isActiveWorklistQueue(queueKey) {
    return normalizeQueueKey(activeWorklistQueueKey()) === normalizeQueueKey(queueKey);
  }

  function overviewRouteSignature() {
    const pathRoute = pathRouteParts();
    if (Array.isArray(pathRoute) && String(pathRoute[0] || "") === PAGE_KEY) return pathRoute.join("|");
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) ? route.join("|") : "";
  }

  function isActiveWarehouseRoute() {
    const pathRoute = pathRouteParts();
    if (String(pathRoute[0] || "") === PAGE_KEY) return true;
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) && String(route[0] || "") === PAGE_KEY;
  }

  function inboundRouteSignature() {
    const pathRoute = pathRouteParts();
    if (String(pathRoute[0] || "") === WORKLIST_PAGE_KEY) return pathRoute.join("|");
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) ? route.join("|") : "";
  }

  function isActiveInboundRoute() {
    return activeWorklistQueueKey() === INBOUND_QUEUE_KEY;
  }

  function isActiveWarehouseWorklistRoute() {
    return isSupportedWorklistQueue(activeWorklistQueueKey());
  }

  function receivingRouteSignature() {
    const pathRoute = pathRouteParts();
    if (String(pathRoute[0] || "") === RECEIVING_PAGE_KEY) return pathRoute.join("|");
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) ? route.join("|") : "";
  }

  function receivingPurchaseOrderFromRoute() {
    const pathRoute = pathRouteParts();
    if (String(pathRoute[0] || "") === RECEIVING_PAGE_KEY) return String(pathRoute[1] || "");
    const route = frappe.get_route ? frappe.get_route() : [];
    if (Array.isArray(route) && String(route[0] || "") === RECEIVING_PAGE_KEY) return String(route[1] || "");
    return "";
  }

  function isActiveReceivingRoute() {
    const pathRoute = pathRouteParts();
    if (String(pathRoute[0] || "") === RECEIVING_PAGE_KEY) return true;
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) && String(route[0] || "") === RECEIVING_PAGE_KEY;
  }

  function pickingRouteSignature() {
    const pathRoute = pathRouteParts();
    if (String(pathRoute[0] || "") === PICKING_PAGE_KEY) return pathRoute.join("|");
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) ? route.join("|") : "";
  }

  function pickingSalesOrderFromRoute() {
    const pathRoute = pathRouteParts();
    if (String(pathRoute[0] || "") === PICKING_PAGE_KEY) return String(pathRoute[1] || "");
    const route = frappe.get_route ? frappe.get_route() : [];
    if (Array.isArray(route) && String(route[0] || "") === PICKING_PAGE_KEY) return String(route[1] || "");
    return "";
  }

  function isActivePickingRoute() {
    const pathRoute = pathRouteParts();
    if (String(pathRoute[0] || "") === PICKING_PAGE_KEY) return true;
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) && String(route[0] || "") === PICKING_PAGE_KEY;
  }

  function stockExceptionRouteSignature() {
    const pathRoute = pathRouteParts();
    if (String(pathRoute[0] || "") === STOCK_EXCEPTION_PAGE_KEY) return pathRoute.join("|");
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) ? route.join("|") : "";
  }

  function stockExceptionTokenFromRoute() {
    const pathRoute = pathRouteParts();
    if (String(pathRoute[0] || "") === STOCK_EXCEPTION_PAGE_KEY) return String(pathRoute[1] || "");
    const route = frappe.get_route ? frappe.get_route() : [];
    if (Array.isArray(route) && String(route[0] || "") === STOCK_EXCEPTION_PAGE_KEY) return String(route[1] || "");
    return "";
  }

  function isActiveStockExceptionRoute() {
    const pathRoute = pathRouteParts();
    if (String(pathRoute[0] || "") === STOCK_EXCEPTION_PAGE_KEY) return true;
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) && String(route[0] || "") === STOCK_EXCEPTION_PAGE_KEY;
  }

  function stockPostureRouteSignature() {
    const pathRoute = pathRouteParts();
    if (String(pathRoute[0] || "") === STOCK_POSTURE_PAGE_KEY) return pathRoute.join("|");
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) ? route.join("|") : "";
  }

  function stockPostureTokenFromRoute() {
    const pathRoute = pathRouteParts();
    if (String(pathRoute[0] || "") === STOCK_POSTURE_PAGE_KEY) return String(pathRoute[1] || "");
    const route = frappe.get_route ? frappe.get_route() : [];
    if (Array.isArray(route) && String(route[0] || "") === STOCK_POSTURE_PAGE_KEY) return String(route[1] || "");
    return "";
  }

  function isActiveStockPostureRoute() {
    const pathRoute = pathRouteParts();
    if (String(pathRoute[0] || "") === STOCK_POSTURE_PAGE_KEY) return true;
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) && String(route[0] || "") === STOCK_POSTURE_PAGE_KEY;
  }

  function movementRouteSignature() {
    const pathRoute = pathRouteParts();
    if (String(pathRoute[0] || "") === MOVEMENT_PAGE_KEY) return pathRoute.join("|");
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) ? route.join("|") : "";
  }

  function movementTokenFromRoute() {
    const pathRoute = pathRouteParts();
    if (String(pathRoute[0] || "") === MOVEMENT_PAGE_KEY) return String(pathRoute[1] || "");
    const route = frappe.get_route ? frappe.get_route() : [];
    if (Array.isArray(route) && String(route[0] || "") === MOVEMENT_PAGE_KEY) return String(route[1] || "");
    return "";
  }

  function isActiveMovementRoute() {
    const pathRoute = pathRouteParts();
    if (String(pathRoute[0] || "") === MOVEMENT_PAGE_KEY) return true;
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) && String(route[0] || "") === MOVEMENT_PAGE_KEY;
  }

  function warehouseConsoleDiagnostics() {
    const api = window.erpWorkspaceWarehouseConsole = window.erpWorkspaceWarehouseConsole || {};
    api.diagnostics = api.diagnostics || {};
    return api.diagnostics;
  }

  function markWarehouseDiagnostic(key) {
    const diagnostics = warehouseConsoleDiagnostics();
    diagnostics[key] = (diagnostics[key] || 0) + 1;
    diagnostics.lastEvent = key;
    diagnostics.lastEventAt = Date.now();
  }

  function ensureStyle() {
    if (document.getElementById("warehouse-console-shell-style")) return;
    const style = document.createElement("style");
    style.id = "warehouse-console-shell-style";
    style.textContent = `
      .warehouse-console-shell {
        width: min(1180px, calc(100% - 24px));
        min-width: 0;
      }
      .warehouse-console-header {
        display: grid;
        gap: 18px;
        padding: 22px;
        overflow: hidden;
        background: linear-gradient(135deg, #ffffff 0%, #f8fbfa 54%, #eef7f2 100%);
        border: 1px solid rgba(210, 225, 218, 0.92);
      }
      .warehouse-console-header-row {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 16px;
        align-items: start;
      }
      .warehouse-console-title {
        margin: 0;
        color: #17231f;
        font-size: 30px;
        line-height: 1.05;
        font-weight: 720;
        letter-spacing: 0;
      }
      .warehouse-console-note {
        margin-top: 6px;
        max-width: 760px;
        color: #52655d;
        font-size: 13px;
        line-height: 1.55;
      }
      .warehouse-console-refresh {
        min-height: 34px;
        padding: 0 14px;
        border: 1px solid rgba(177, 199, 189, 0.95);
        border-radius: 8px;
        background: #ffffff;
        color: #1f3b31;
        font-size: 12px;
        font-weight: 700;
      }
      .warehouse-cockpit-command-row {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 16px;
        align-items: start;
      }
      .warehouse-cockpit-chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 7px;
        margin-top: 12px;
      }
      .warehouse-cockpit-chip {
        display: inline-flex;
        align-items: center;
        min-height: 24px;
        padding: 0 9px;
        border: 1px solid rgba(188, 211, 200, 0.88);
        border-radius: 999px;
        background: rgba(244, 250, 247, 0.92);
        color: #29463c;
        font-size: 10.5px;
        font-weight: 760;
        letter-spacing: 0.04em;
        text-transform: uppercase;
      }
      .warehouse-cockpit-pulse {
        display: grid;
        gap: 9px;
      }
      .warehouse-cockpit-label {
        color: #597168;
        font-size: 11px;
        font-weight: 780;
        letter-spacing: 0.08em;
        line-height: 1.2;
        text-transform: uppercase;
      }
      .warehouse-cockpit-pulse-card {
        border-color: rgba(198, 220, 210, 0.98);
        background: linear-gradient(180deg, #ffffff 0%, #fbfdfc 100%);
      }
      .warehouse-cockpit-start,
      .warehouse-cockpit-route-section,
      .warehouse-cockpit-guardrail {
        min-width: 0;
        padding: 18px;
        border: 1px solid rgba(219, 231, 225, 0.96);
        border-radius: 8px;
        background: #ffffff;
      }
      .warehouse-cockpit-section-head {
        display: grid;
        gap: 4px;
        margin-bottom: 12px;
      }
      .warehouse-cockpit-section-title {
        margin: 0;
        color: #1f2b27;
        font-size: 16px;
        font-weight: 780;
        line-height: 1.25;
      }
      .warehouse-cockpit-section-note {
        color: #64766e;
        font-size: 12.5px;
        line-height: 1.45;
      }
      .warehouse-cockpit-start-grid,
      .warehouse-cockpit-route-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 9px;
      }
      .warehouse-cockpit-route-grid.is-two {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .warehouse-cockpit-start-card,
      .warehouse-cockpit-route-card {
        display: grid;
        grid-template-rows: auto auto 1fr auto;
        gap: 8px;
        min-width: 0;
        min-height: 148px;
        padding: 14px;
        border: 1px solid rgba(212, 226, 219, 0.98);
        border-radius: 8px;
        background: #fbfdfc;
      }
      .warehouse-cockpit-start-card.is-risk,
      .warehouse-cockpit-route-card.is-risk {
        border-color: rgba(227, 194, 135, 0.78);
        background: #fffaf0;
      }
      .warehouse-cockpit-start-card.is-movement,
      .warehouse-cockpit-route-card.is-movement {
        border-color: rgba(181, 209, 214, 0.88);
        background: #f6fbfb;
      }
      .warehouse-cockpit-card-kicker {
        color: #65776f;
        font-size: 10.5px;
        font-weight: 780;
        letter-spacing: 0.06em;
        line-height: 1.25;
        text-transform: uppercase;
      }
      .warehouse-cockpit-card-title {
        color: #20332d;
        font-size: 14px;
        font-weight: 780;
        line-height: 1.3;
      }
      .warehouse-cockpit-card-note {
        color: #65776f;
        font-size: 12px;
        line-height: 1.45;
      }
      .warehouse-cockpit-card-action {
        width: fit-content;
        min-height: 32px;
        padding: 0 11px;
        border: 1px solid rgba(177, 199, 189, 0.95);
        border-radius: 8px;
        background: #ffffff;
        color: #1f3b31;
        font-size: 12px;
        font-weight: 730;
      }
      .warehouse-cockpit-work-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
      }
      .warehouse-cockpit-guardrail {
        color: #52655d;
        font-size: 12.5px;
        line-height: 1.5;
        background: #f8fbfa;
      }
      .warehouse-console-kpi-grid {
        display: grid;
        grid-template-columns: repeat(6, minmax(0, 1fr));
        gap: 8px;
        min-width: 0;
      }
      .warehouse-console-kpi-card {
        min-width: 0;
        display: grid;
        gap: 7px;
        padding: 14px 14px 13px;
        border: 1px solid rgba(214, 228, 221, 0.96);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.9);
      }
      .warehouse-console-kpi-label {
        overflow-wrap: anywhere;
        color: #5f7169;
        font-size: 10.5px;
        font-weight: 760;
        letter-spacing: 0.05em;
        line-height: 1.25;
        text-transform: uppercase;
      }
      .warehouse-console-kpi-value {
        color: #17231f;
        font-size: 27px;
        font-weight: 760;
        line-height: 1;
      }
      .warehouse-console-kpi-meta {
        color: #667a71;
        font-size: 11.5px;
        line-height: 1.4;
      }
      .warehouse-console-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 14px;
      }
      .warehouse-console-section {
        min-width: 0;
        padding: 18px 18px 17px;
      }
      .warehouse-console-section-head {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 14px;
      }
      .warehouse-console-section-title {
        margin: 0;
        color: #1f2b27;
        font-size: 15px;
        font-weight: 760;
        line-height: 1.3;
      }
      .warehouse-console-section-note {
        color: #6a7b73;
        font-size: 12px;
        line-height: 1.4;
        text-align: right;
      }
      .warehouse-console-card-grid {
        display: grid;
        gap: 8px;
      }
      .warehouse-console-status-card {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: center;
        gap: 12px;
        min-width: 0;
        padding: 11px 12px;
        border: 1px solid rgba(224, 233, 229, 0.96);
        border-radius: 8px;
        background: #ffffff;
      }
      .warehouse-console-status-title {
        color: #263530;
        font-size: 13px;
        font-weight: 720;
        line-height: 1.35;
      }
      .warehouse-console-status-note {
        margin-top: 2px;
        color: #708178;
        font-size: 11.5px;
        line-height: 1.4;
      }
      .warehouse-console-status-value {
        min-width: 42px;
        text-align: right;
        color: #1f3b31;
        font-size: 20px;
        font-weight: 760;
        line-height: 1;
      }
      .warehouse-console-inbound-panel {
        display: grid;
        gap: 13px;
        min-width: 0;
        padding: 16px;
        border: 1px solid rgba(210, 225, 218, 0.92);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.76);
      }
      .warehouse-console-inbound-head,
      .warehouse-inbound-queue-head {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: start;
        gap: 14px;
      }
      .warehouse-console-inbound-title,
      .warehouse-inbound-queue-title {
        margin: 0;
        color: #1f2b27;
        font-size: 16px;
        font-weight: 760;
        line-height: 1.3;
      }
      .warehouse-console-inbound-note,
      .warehouse-inbound-queue-note {
        margin-top: 3px;
        color: #64766e;
        font-size: 12.5px;
        line-height: 1.45;
      }
      .warehouse-console-inbound-open,
      .warehouse-inbound-queue-button {
        min-height: 34px;
        padding: 0 12px;
        border: 1px solid rgba(177, 199, 189, 0.95);
        border-radius: 8px;
        background: #ffffff;
        color: #1f3b31;
        font-size: 12px;
        font-weight: 720;
      }
      .warehouse-console-inbound-cards,
      .warehouse-inbound-queue-cards {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 8px;
      }
      .warehouse-console-inbound-card,
      .warehouse-inbound-queue-card {
        min-width: 0;
        padding: 12px;
        border: 1px solid rgba(219, 231, 225, 0.96);
        border-radius: 8px;
        background: #ffffff;
      }
      .warehouse-console-inbound-card-label,
      .warehouse-inbound-queue-card-label {
        color: #667a71;
        font-size: 10.5px;
        font-weight: 760;
        letter-spacing: 0.05em;
        line-height: 1.25;
        text-transform: uppercase;
      }
      .warehouse-console-inbound-card-value,
      .warehouse-inbound-queue-card-value {
        margin-top: 7px;
        color: #17231f;
        font-size: 24px;
        font-weight: 760;
        line-height: 1;
      }
      .warehouse-console-inbound-card-note,
      .warehouse-inbound-queue-card-note {
        margin-top: 6px;
        color: #708178;
        font-size: 11.5px;
        line-height: 1.35;
      }
      .warehouse-console-inbound-preview {
        display: grid;
        gap: 7px;
      }
      .warehouse-console-inbound-row {
        display: grid;
        grid-template-columns: minmax(0, 1.15fr) minmax(0, 0.9fr) minmax(0, 0.75fr) auto;
        gap: 10px;
        align-items: center;
        min-width: 0;
        padding: 10px 11px;
        border: 1px solid rgba(224, 233, 229, 0.96);
        border-radius: 8px;
        background: #ffffff;
      }
      .warehouse-console-inbound-row strong,
      .warehouse-inbound-order {
        color: #263530;
        font-size: 13px;
        font-weight: 740;
        line-height: 1.3;
      }
      .warehouse-console-inbound-row span,
      .warehouse-inbound-meta {
        min-width: 0;
        color: #66786f;
        font-size: 12px;
        line-height: 1.35;
        overflow-wrap: anywhere;
      }
      .warehouse-inbound-shell {
        width: min(1180px, calc(100% - 24px));
        min-width: 0;
      }
      .warehouse-inbound-queue-header {
        display: grid;
        gap: 16px;
        padding: 22px;
        border: 1px solid rgba(210, 225, 218, 0.92);
        border-radius: 8px;
        background: linear-gradient(135deg, #ffffff 0%, #f8fbfa 58%, #eef7f2 100%);
      }
      .warehouse-inbound-controls {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr)) auto auto auto;
        gap: 8px;
        align-items: end;
        padding: 12px;
        border: 1px solid rgba(219, 231, 225, 0.96);
        border-radius: 8px;
        background: #ffffff;
      }
      .warehouse-inbound-field {
        display: grid;
        gap: 5px;
        min-width: 0;
      }
      .warehouse-inbound-field label {
        color: #64766e;
        font-size: 10.5px;
        font-weight: 760;
        letter-spacing: 0.05em;
        text-transform: uppercase;
      }
      .warehouse-inbound-field input,
      .warehouse-inbound-field select {
        width: 100%;
        min-width: 0;
        height: 34px;
        border: 1px solid rgba(205, 220, 213, 0.98);
        border-radius: 8px;
        background: #ffffff;
        color: #23352f;
        font-size: 12.5px;
        padding: 0 10px;
      }
      .warehouse-inbound-groups {
        display: grid;
        gap: 12px;
        margin-top: 14px;
      }
      .warehouse-inbound-group {
        min-width: 0;
        padding: 16px;
        border: 1px solid rgba(219, 231, 225, 0.96);
        border-radius: 8px;
        background: #ffffff;
      }
      .warehouse-inbound-group-head {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 10px;
      }
      .warehouse-inbound-group-title {
        margin: 0;
        color: #1f2b27;
        font-size: 14px;
        font-weight: 760;
      }
      .warehouse-inbound-group-note {
        color: #72837b;
        font-size: 12px;
      }
      .warehouse-inbound-row {
        display: grid;
        gap: 8px;
        min-width: 0;
        padding: 12px;
        border: 1px solid rgba(228, 236, 232, 0.98);
        border-radius: 8px;
        background: #fbfdfc;
      }
      .warehouse-inbound-row-main {
        display: grid;
        grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.85fr) minmax(0, 0.9fr) minmax(0, 0.75fr) auto;
        gap: 10px;
        align-items: center;
      }
      .warehouse-inbound-badge {
        display: inline-flex;
        align-items: center;
        width: fit-content;
        min-height: 22px;
        padding: 0 8px;
        border: 1px solid rgba(197, 217, 207, 0.9);
        border-radius: 999px;
        background: #f4faf7;
        color: #264239;
        font-size: 10.5px;
        font-weight: 760;
        text-transform: uppercase;
      }
      .warehouse-inbound-lines {
        display: none;
        gap: 6px;
        padding-top: 7px;
        border-top: 1px solid rgba(224, 233, 229, 0.96);
      }
      .warehouse-inbound-row.is-expanded .warehouse-inbound-lines {
        display: grid;
      }
      .warehouse-inbound-line {
        display: grid;
        grid-template-columns: minmax(0, 1fr) minmax(0, 0.5fr) minmax(0, 0.8fr);
        gap: 8px;
        color: #51645c;
        font-size: 12px;
        line-height: 1.35;
      }
      .warehouse-receiving-shell {
        width: min(1180px, calc(100% - 24px));
        min-width: 0;
      }
      .warehouse-receiving-header {
        display: grid;
        gap: 16px;
        padding: 22px;
        border: 1px solid rgba(210, 225, 218, 0.92);
        border-radius: 8px;
        background: linear-gradient(135deg, #ffffff 0%, #f8fbfa 58%, #eef7f2 100%);
      }
      .warehouse-receiving-head {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 14px;
        align-items: start;
      }
      .warehouse-receiving-title {
        margin: 0;
        color: #17231f;
        font-size: 26px;
        font-weight: 760;
        line-height: 1.08;
      }
      .warehouse-receiving-subtitle,
      .warehouse-receiving-note,
      .warehouse-receiving-meta {
        min-width: 0;
        color: #64766e;
        font-size: 12.5px;
        line-height: 1.45;
        overflow-wrap: anywhere;
      }
      .warehouse-receiving-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        justify-content: flex-end;
      }
      .warehouse-receiving-button {
        min-height: 34px;
        padding: 0 12px;
        border: 1px solid rgba(177, 199, 189, 0.95);
        border-radius: 8px;
        background: #ffffff;
        color: #1f3b31;
        font-size: 12px;
        font-weight: 720;
      }
      .warehouse-receiving-cards {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 8px;
      }
      .warehouse-receiving-card {
        min-width: 0;
        padding: 12px;
        border: 1px solid rgba(219, 231, 225, 0.96);
        border-radius: 8px;
        background: #ffffff;
      }
      .warehouse-receiving-card-label {
        color: #667a71;
        font-size: 10.5px;
        font-weight: 760;
        letter-spacing: 0.05em;
        line-height: 1.25;
        text-transform: uppercase;
      }
      .warehouse-receiving-card-value {
        margin-top: 7px;
        color: #17231f;
        font-size: 20px;
        font-weight: 760;
        line-height: 1.08;
      }
      .warehouse-receiving-card-note {
        margin-top: 6px;
        color: #708178;
        font-size: 11.5px;
        line-height: 1.35;
      }
      .warehouse-receiving-detail {
        display: grid;
        gap: 12px;
        margin-top: 14px;
        padding: 16px;
        border: 1px solid rgba(219, 231, 225, 0.96);
        border-radius: 8px;
        background: #ffffff;
      }
      .warehouse-receiving-tabs {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }
      .warehouse-receiving-tab {
        min-height: 32px;
        padding: 0 11px;
        border: 1px solid rgba(205, 220, 213, 0.98);
        border-radius: 8px;
        background: #f8fbfa;
        color: #29463c;
        font-size: 12px;
        font-weight: 720;
      }
      .warehouse-receiving-tab.is-active {
        border-color: rgba(42, 105, 76, 0.35);
        background: #eaf6f0;
      }
      .warehouse-receiving-panel {
        display: none;
        gap: 8px;
      }
      .warehouse-receiving-panel.is-active {
        display: grid;
      }
      .warehouse-receiving-line,
      .warehouse-receiving-history-row {
        display: grid;
        grid-template-columns: minmax(0, 1.15fr) minmax(0, 0.75fr) minmax(0, 0.75fr) minmax(0, 0.8fr) minmax(0, 0.7fr);
        gap: 10px;
        align-items: center;
        min-width: 0;
        padding: 11px 12px;
        border: 1px solid rgba(228, 236, 232, 0.98);
        border-radius: 8px;
        background: #fbfdfc;
      }
      .warehouse-receiving-history-row {
        grid-template-columns: minmax(0, 1fr) minmax(0, 0.75fr) minmax(0, 0.75fr) minmax(0, 0.9fr);
      }
      .warehouse-stock-exception-shell {
        width: min(1180px, calc(100% - 24px));
        min-width: 0;
      }
      .warehouse-stock-exception-row {
        display: grid;
        gap: 10px;
        min-width: 0;
        padding: 13px;
        border: 1px solid rgba(228, 236, 232, 0.98);
        border-radius: 8px;
        background: #fbfdfc;
      }
      .warehouse-stock-exception-row-main {
        display: grid;
        grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.9fr) minmax(0, 0.75fr) minmax(0, 0.95fr) auto;
        gap: 10px;
        align-items: center;
      }
      .warehouse-stock-exception-facts {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 8px;
        padding-top: 8px;
        border-top: 1px solid rgba(224, 233, 229, 0.96);
      }
      .warehouse-stock-exception-fact {
        min-width: 0;
        color: #51645c;
        font-size: 12px;
        line-height: 1.35;
      }
      .warehouse-stock-exception-review-shell {
        width: min(1180px, calc(100% - 24px));
        min-width: 0;
      }
      .warehouse-stock-exception-review-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
        min-width: 0;
        margin-top: 12px;
      }
      .warehouse-stock-exception-review-panel {
        display: grid;
        gap: 10px;
        min-width: 0;
        padding: 14px;
        border: 1px solid rgba(228, 236, 232, 0.98);
        border-radius: 8px;
        background: #fbfdfc;
      }
      .warehouse-stock-exception-review-facts {
        display: grid;
        gap: 8px;
      }
      .warehouse-stock-exception-review-fact {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        min-width: 0;
        padding: 9px 10px;
        border-radius: 8px;
        background: #f4f8f6;
        color: #51645c;
        font-size: 12px;
      }
      .warehouse-stock-exception-review-fact strong {
        min-width: 0;
        color: #24352f;
        font-size: 13px;
        text-align: right;
      }
      .warehouse-stock-exception-next-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px;
      }
      .warehouse-stock-exception-next-card {
        display: grid;
        gap: 6px;
        min-width: 0;
        min-height: 74px;
        padding: 11px;
        border: 1px solid rgba(212, 226, 219, 0.98);
        border-radius: 8px;
        background: #f8fbfa;
        color: #29463c;
        text-align: left;
      }
      .warehouse-stock-exception-next-card span {
        font-size: 12px;
        font-weight: 760;
      }
      .warehouse-stock-exception-next-card strong {
        color: #65756e;
        font-size: 12px;
        font-weight: 560;
        line-height: 1.35;
      }
      .warehouse-receiving-strong {
        color: #263530;
        font-size: 13px;
        font-weight: 740;
        line-height: 1.3;
      }
      .warehouse-console-state {
        padding: 20px;
      }
      .warehouse-console-state-title {
        margin: 0 0 8px;
        color: #1f2b27;
        font-size: 18px;
        font-weight: 740;
      }
      .warehouse-console-state-detail {
        color: #64746d;
        font-size: 13px;
        line-height: 1.55;
      }
      @media (max-width: 1240px) {
        .warehouse-console-kpi-grid {
          grid-template-columns: repeat(3, minmax(0, 1fr));
        }
        .warehouse-console-inbound-cards,
        .warehouse-inbound-queue-cards,
        .warehouse-receiving-cards {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .warehouse-cockpit-start-grid {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .warehouse-inbound-controls {
          grid-template-columns: repeat(4, minmax(0, 1fr));
        }
      }
      @media (max-width: 900px) {
        .warehouse-console-header-row,
        .warehouse-console-grid,
        .warehouse-console-inbound-head,
        .warehouse-inbound-queue-head,
        .warehouse-receiving-head,
        .warehouse-console-inbound-row,
        .warehouse-inbound-row-main,
        .warehouse-receiving-line,
        .warehouse-receiving-history-row,
        .warehouse-cockpit-command-row,
        .warehouse-cockpit-work-grid,
        .warehouse-cockpit-route-grid,
        .warehouse-cockpit-route-grid.is-two,
        .warehouse-cockpit-start-grid,
        .warehouse-stock-exception-review-grid,
        .warehouse-stock-exception-next-grid,
        .warehouse-stock-exception-row-main,
        .warehouse-stock-exception-facts {
          grid-template-columns: minmax(0, 1fr);
        }
        .warehouse-inbound-controls {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .warehouse-receiving-actions {
          justify-content: flex-start;
        }
        .warehouse-console-section-note {
          text-align: left;
        }
      }
      @media (max-width: 680px) {
        .warehouse-console-kpi-grid {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .warehouse-inbound-controls,
        .warehouse-inbound-line {
          grid-template-columns: minmax(0, 1fr);
        }
        .warehouse-inbound-controls .warehouse-inbound-queue-button,
        .warehouse-receiving-actions .warehouse-inbound-queue-button,
        .warehouse-receiving-actions .warehouse-receiving-button {
          width: 100%;
        }
      }
    `;
    document.head.appendChild(style);
  }

  function pageBodyElement(page) {
    if (page && page.body) {
      if (page.body.nodeType) return page.body;
      if (page.body.jquery && page.body[0]) return page.body[0];
    }
    return document.querySelector(".erpw-direct-warehouse-body");
  }

  function currentWarehouseHost() {
    return document.querySelector('.erpw-direct-warehouse-page[data-erpw-page-key="warehouse-console"]');
  }

  function ensureWarehouseBody(host) {
    if (!host) return null;
    let body = host.querySelector(".erpw-direct-warehouse-body");
    if (!body) {
      body = document.createElement("main");
      body.className = "layout-main-section erpw-direct-warehouse-body";
      host.appendChild(body);
    }
    return body;
  }

  function removeDuplicateWarehouseHosts(keepBody) {
    const keepHost = keepBody ? keepBody.closest('.erpw-direct-warehouse-page[data-erpw-page-key="warehouse-console"]') : null;
    document.querySelectorAll('.sales-console-shell[data-erpw-workspace="warehouse"]').forEach((shell) => {
      if (!keepBody || !keepBody.contains(shell)) shell.remove();
    });
    document.querySelectorAll('.erpw-direct-warehouse-page[data-erpw-page-key="warehouse-console"]').forEach((host) => {
      if (host !== keepHost) host.remove();
    });
  }

  function replacePageBody(page, $content) {
    const body = pageBodyElement(page);
    if (!body) return;
    removeDuplicateWarehouseHosts(body);
    body.innerHTML = "";
    $content.each((index, node) => body.appendChild(node));
  }

  function makeConsolePage(wrapper) {
    const existingHost = currentWarehouseHost();
    if (existingHost && document.body.contains(existingHost)) {
      return {
        body: ensureWarehouseBody(existingHost),
        set_title(title) {
          document.title = title || "Warehouse Console";
        },
      };
    }

    const $parent = $(wrapper);
    if (wrapper && wrapper.id === "body") {
      let $host = $parent.find('.erpw-direct-warehouse-page[data-erpw-page-key="warehouse-console"]').first();
      if (!$host.length) {
        $host = $('<div class="erpw-direct-warehouse-page" data-erpw-page-key="warehouse-console"></div>').appendTo($parent);
      }
      return {
        body: ensureWarehouseBody($host.get(0)),
        set_title(title) {
          document.title = title || "Warehouse Console";
        },
      };
    }
    $parent.empty().append(`
      <div class="erpw-direct-warehouse-page" data-erpw-page-key="warehouse-console">
        <main class="layout-main-section erpw-direct-warehouse-body"></main>
      </div>
    `);
    return {
      body: $parent.find(".erpw-direct-warehouse-body").first().get(0),
      set_title(title) {
        document.title = title || "Warehouse Console";
      },
    };
  }

  function renderState(page, state) {
    ensureStyle();
    const payloadState = state || {};
    const $root = $(`
      <div class="sales-console-shell warehouse-console-shell" data-erpw-workspace="warehouse" data-warehouse-console-state="${escapeHtml(payloadState.kind || "unavailable")}">
        <section class="warehouse-console-state">
          <h1 class="warehouse-console-state-title">${escapeHtml(payloadState.title || "Warehouse Console unavailable")}</h1>
          <div class="warehouse-console-state-detail">${escapeHtml(payloadState.detail || "Warehouse information could not be loaded. Refresh or try again.")}</div>
        </section>
      </div>
    `);
    replacePageBody(page, $root);
    cleanupOverviewPageHeads();
  }

  function renderLoadingState(page) {
    if (!isActiveWarehouseRoute()) return;
    ensureStyle();
    const $root = $(`
      <div class="sales-console-shell warehouse-console-shell" data-erpw-workspace="warehouse" data-erpw-console-runtime="loading" data-erpw-console-bootstrap="loading" data-erpw-overview-route-signature="${escapeHtml(overviewRouteSignature())}">
        <section class="warehouse-console-header">
          <div class="warehouse-console-header-row">
            <div>
              <h1 class="warehouse-console-title">Warehouse Console</h1>
              <div class="warehouse-console-note">Loading stock visibility and warehouse posture.</div>
            </div>
          </div>
        </section>
      </div>
    `);
    replacePageBody(page, $root);
    cleanupOverviewPageHeads();
  }

  function metricText(metric) {
    if (!metric) return "--";
    if (metric.state === "unavailable" || metric.value == null) return "N/A";
    return String(metric.value);
  }

  function metricNote(metric) {
    if (!metric) return "";
    return metric.note || metric.meta || "";
  }

  function renderKpi(metric) {
    return `
      <div class="warehouse-console-kpi-card" data-warehouse-kpi="${escapeHtml(metric.key || "")}">
        <div class="warehouse-console-kpi-label">${escapeHtml(metric.label || "")}</div>
        <div class="warehouse-console-kpi-value">${escapeHtml(metricText(metric))}</div>
        <div class="warehouse-console-kpi-meta">${escapeHtml(metricNote(metric))}</div>
      </div>
    `;
  }

  function metricByKey(metrics, key) {
    return (Array.isArray(metrics) ? metrics : []).find((metric) => String(metric && metric.key || "") === key) || {};
  }

  function cardByKey(cards, key) {
    return (Array.isArray(cards) ? cards : []).find((card) => String(card && card.key || "") === key) || {};
  }

  function metricNumber(metric) {
    const value = metric && metric.value;
    if (value == null || value === "") return 0;
    const numberValue = Number(value);
    return Number.isFinite(numberValue) ? numberValue : 0;
  }

  function countFrom(payload, key) {
    const counts = payload && payload.counts && typeof payload.counts === "object" ? payload.counts : {};
    const value = counts[key];
    const numberValue = Number(value);
    return Number.isFinite(numberValue) ? numberValue : 0;
  }

  function freshnessText(payload) {
    const fetchedAt = payload && payload.fetched_at ? String(payload.fetched_at) : "";
    if (!fetchedAt) return "Freshness checked";
    return `Fresh ${fetchedAt}`;
  }

  function cockpitPulseCards(payload, kpis) {
    const inbound = payload.inbound || {};
    const outbound = payload.outbound || {};
    const stockExceptions = payload.stock_exceptions || {};
    const receivingAttention = countFrom(inbound, "overdue") + countFrom(inbound, "due_today");
    const pickingAttention = countFrom(outbound, "overdue") + countFrom(outbound, "due_today") + countFrom(outbound, "short_stock");
    const exceptionCard = cardByKey(stockExceptions.cards || [], "total_exceptions");
    const activeWarehouses = metricByKey(kpis, "active_warehouses");
    const movementMetric = metricByKey(kpis, "transfer_requests");
    return [
      { key: "receiving_attention", label: "Receiving Attention", value: receivingAttention, note: "Supplier-side receiving review.", state: "live" },
      { key: "picking_attention", label: "Picking Attention", value: pickingAttention, note: "Customer-side picking review.", state: "live" },
      { key: "stock_exceptions", label: "Stock Exceptions", value: metricNumber(exceptionCard), note: "Shortage and posture issues.", state: "live" },
      { key: "movement_records", label: "Movement Records", value: metricNumber(movementMetric), note: "Posted movement visibility.", state: "live" },
      { key: "active_warehouse_posture", label: "Warehouse Posture", value: metricNumber(activeWarehouses), note: "Active locations in view.", state: "live" },
      { key: "freshness", label: "Freshness", value: "Now", note: freshnessText(payload), state: "live" },
    ];
  }

  function renderCockpitChip(label) {
    return `<span class="warehouse-cockpit-chip">${escapeHtml(label)}</span>`;
  }

  function renderPulseCard(metric) {
    return `
      <div class="warehouse-console-kpi-card warehouse-cockpit-pulse-card" data-warehouse-kpi="${escapeHtml(metric.key || "")}" data-warehouse-cockpit-pulse-card="${escapeHtml(metric.key || "")}">
        <div class="warehouse-console-kpi-label">${escapeHtml(metric.label || "")}</div>
        <div class="warehouse-console-kpi-value">${escapeHtml(metricText(metric))}</div>
        <div class="warehouse-console-kpi-meta">${escapeHtml(metricNote(metric))}</div>
      </div>
    `;
  }

  function renderCockpitStartCard(card) {
    return `
      <article class="warehouse-cockpit-start-card ${escapeHtml(card.variant || "")}" data-warehouse-cockpit-start-card="${escapeHtml(card.key || "")}">
        <div class="warehouse-cockpit-card-kicker">${escapeHtml(card.kicker || "")}</div>
        <div class="warehouse-cockpit-card-title">${escapeHtml(card.title || "")}</div>
        <div class="warehouse-cockpit-card-note">${escapeHtml(card.note || "")}</div>
        <button type="button" class="warehouse-cockpit-card-action" ${card.actionAttr}>${escapeHtml(card.action || "")}</button>
      </article>
    `;
  }

  function renderCockpitRouteCard(card) {
    return `
      <article class="warehouse-cockpit-route-card ${escapeHtml(card.variant || "")}" data-warehouse-cockpit-route-card="${escapeHtml(card.key || "")}">
        <div class="warehouse-cockpit-card-kicker">${escapeHtml(card.kicker || "")}</div>
        <div class="warehouse-cockpit-card-title">${escapeHtml(card.title || "")}</div>
        <div class="warehouse-cockpit-card-note">${escapeHtml(card.note || "")}</div>
        ${card.action ? `<button type="button" class="warehouse-cockpit-card-action" ${card.actionAttr}>${escapeHtml(card.action)}</button>` : ""}
      </article>
    `;
  }

  function renderCockpitStart(payload, kpis) {
    const inbound = payload.inbound || {};
    const outbound = payload.outbound || {};
    const stockExceptions = payload.stock_exceptions || {};
    const receivingAttention = countFrom(inbound, "overdue") + countFrom(inbound, "due_today");
    const pickingAttention = countFrom(outbound, "overdue") + countFrom(outbound, "due_today") + countFrom(outbound, "short_stock");
    const exceptionTotal = metricNumber(cardByKey(stockExceptions.cards || [], "total_exceptions"));
    const movementMetric = metricByKey(kpis, "transfer_requests");
    const cards = [
      {
        key: "inbound_due",
        kicker: receivingAttention ? `${receivingAttention} needs review` : "Supplier-side work",
        title: "Review inbound due soon",
        note: "Expected supplier stock and partial receiving posture.",
        action: "Open inbound receiving",
        actionAttr: "data-warehouse-open-inbound",
      },
      {
        key: "outbound_risk",
        kicker: pickingAttention ? `${pickingAttention} needs review` : "Customer-side work",
        title: "Review outbound picking risk",
        note: "Customer demand, pending quantity, and warehouse readiness.",
        action: "Open outbound picking",
        actionAttr: "data-warehouse-open-outbound",
      },
      {
        key: "stock_exceptions",
        kicker: exceptionTotal ? `${exceptionTotal} visible` : "Risk review",
        title: "Check stock exceptions",
        note: "Shortage risk, inbound cover, and posture gaps.",
        action: "Open stock exceptions",
        actionAttr: "data-warehouse-open-stock-exceptions",
        variant: "is-risk",
      },
      {
        key: "movement_visibility",
        kicker: metricText(movementMetric),
        title: "Inspect recent movement",
        note: "Posted movement visibility and item posture drilldowns.",
        action: "Open movement visibility",
        actionAttr: "data-warehouse-open-movement",
        variant: "is-movement",
      },
    ];
    return `
      <section class="warehouse-cockpit-start" data-warehouse-cockpit-start>
        <div class="warehouse-cockpit-section-head">
          <h2 class="warehouse-cockpit-section-title">Start Here</h2>
          <div class="warehouse-cockpit-section-note">Prioritized read-only starts using protected Warehouse routes.</div>
        </div>
        <div class="warehouse-cockpit-start-grid">${cards.map(renderCockpitStartCard).join("")}</div>
      </section>
    `;
  }

  function renderCockpitRiskSection() {
    const cards = [
      {
        key: "stock_exceptions",
        kicker: "Risk",
        title: "Stock Exceptions",
        note: "Shortage risk, inbound cover, and missing warehouse posture.",
        action: "Open stock exceptions",
        actionAttr: "data-warehouse-open-stock-exceptions",
        variant: "is-risk",
      },
      {
        key: "stock_posture_context",
        kicker: "Context detail",
        title: "Stock Posture",
        note: "Item and warehouse posture opens from protected review pages. It is not a top-level lookup.",
        variant: "is-risk",
      },
    ];
    return `
      <section class="warehouse-cockpit-route-section" data-warehouse-cockpit-risk>
        <div class="warehouse-cockpit-section-head">
          <h2 class="warehouse-cockpit-section-title">Risks To Resolve</h2>
          <div class="warehouse-cockpit-section-note">Understand blockers before warehouse work stalls.</div>
        </div>
        <div class="warehouse-cockpit-route-grid is-two">${cards.map(renderCockpitRouteCard).join("")}</div>
      </section>
    `;
  }

  function renderCockpitMovementSection() {
    const cards = [
      {
        key: "movement_visibility",
        kicker: "Visibility",
        title: "Movement Visibility",
        note: "Posted movement records grouped for operational review.",
        action: "Open movement visibility",
        actionAttr: "data-warehouse-open-movement",
        variant: "is-movement",
      },
      {
        key: "transfer_visibility",
        kicker: "Transfer posture",
        title: "Transfer Visibility",
        note: "Warehouse-to-warehouse transfer posture from submitted movement records.",
        action: "Open transfer visibility",
        actionAttr: "data-warehouse-open-transfer",
        variant: "is-movement",
      },
      {
        key: "movement_review_context",
        kicker: "Context detail",
        title: "Movement Review",
        note: "Detailed read-only review opens from Movement Visibility rows.",
        variant: "is-movement",
      },
    ];
    return `
      <section class="warehouse-cockpit-route-section" data-warehouse-cockpit-movement>
        <div class="warehouse-cockpit-section-head">
          <h2 class="warehouse-cockpit-section-title">Movement To Understand</h2>
          <div class="warehouse-cockpit-section-note">Review what already changed without leaving this read-only workspace.</div>
        </div>
        <div class="warehouse-cockpit-route-grid">${cards.map(renderCockpitRouteCard).join("")}</div>
      </section>
    `;
  }

  function cardValue(card) {
    if (!card) return "--";
    if (card.state === "unavailable" || card.value == null) return "N/A";
    return String(card.value);
  }

  function renderInboundCard(card) {
    return `
      <div class="warehouse-console-inbound-card" data-warehouse-inbound-card="${escapeHtml(card.key || "")}">
        <div class="warehouse-console-inbound-card-label">${escapeHtml(card.label || card.title || "")}</div>
        <div class="warehouse-console-inbound-card-value">${escapeHtml(cardValue(card))}</div>
        <div class="warehouse-console-inbound-card-note">${escapeHtml(card.note || "")}</div>
      </div>
    `;
  }

  function renderInboundPreviewRow(row) {
    return `
      <div class="warehouse-console-inbound-row" data-warehouse-inbound-preview-row="${escapeHtml(row.key || "")}">
        <div>
          <strong>${escapeHtml(row.purchase_order || row.name || "")}</strong>
          <span>${escapeHtml(row.supplier || "")}</span>
        </div>
        <span>${escapeHtml(row.target_warehouse || "")}</span>
        <span>${escapeHtml(row.age_label || row.required_date || "")}</span>
        <span>${escapeHtml(row.received_percent || "0%")}</span>
      </div>
    `;
  }

  function renderOutboundCard(card) {
    return `
      <div class="warehouse-console-inbound-card" data-warehouse-outbound-card="${escapeHtml(card.key || "")}">
        <div class="warehouse-console-inbound-card-label">${escapeHtml(card.label || card.title || "")}</div>
        <div class="warehouse-console-inbound-card-value">${escapeHtml(cardValue(card))}</div>
        <div class="warehouse-console-inbound-card-note">${escapeHtml(card.note || "")}</div>
      </div>
    `;
  }

  function renderOutboundPreviewRow(row) {
    return `
      <div class="warehouse-console-inbound-row" data-warehouse-outbound-preview-row="${escapeHtml(row.key || "")}">
        <div>
          <strong>${escapeHtml(row.sales_order || row.name || "")}</strong>
          <span>${escapeHtml(row.customer || row.partner || "")}</span>
        </div>
        <span>${escapeHtml(row.target_warehouse || "")}</span>
        <span>${escapeHtml(row.age_label || row.required_date || "")}</span>
        <span>${escapeHtml(row.delivered_percent || "0%")}</span>
      </div>
    `;
  }

  function renderInboundOverviewPanel(inbound) {
    const payload = inbound || {};
    const cards = Array.isArray(payload.cards) ? payload.cards.slice(0, 4) : [];
    const rows = Array.isArray(payload.preview_rows) ? payload.preview_rows.slice(0, 6) : [];
    const emptyMessage = payload.state && payload.state.kind === "empty" ? payload.state.detail : "No inbound receiving needs attention.";
    return `
      <section class="warehouse-console-inbound-panel" data-warehouse-section="inbound_priority">
        <div class="warehouse-console-inbound-head">
          <div>
            <h2 class="warehouse-console-inbound-title">Inbound Work</h2>
            <div class="warehouse-console-inbound-note">Expected supplier stock due into warehouse.</div>
          </div>
          <button class="warehouse-console-inbound-open" type="button" data-warehouse-open-inbound>Open inbound receiving</button>
        </div>
        <div class="warehouse-console-inbound-cards">${cards.map(renderInboundCard).join("")}</div>
        <div class="warehouse-console-inbound-preview">
          ${rows.length ? rows.map(renderInboundPreviewRow).join("") : `<div class="warehouse-console-inbound-row"><span>${escapeHtml(emptyMessage)}</span></div>`}
        </div>
      </section>
    `;
  }

  function renderOutboundOverviewPanel(outbound) {
    const payload = outbound || {};
    const cards = Array.isArray(payload.cards) ? payload.cards.slice(0, 4) : [];
    const rows = Array.isArray(payload.preview_rows) ? payload.preview_rows.slice(0, 6) : [];
    const emptyMessage = payload.state && payload.state.kind === "empty" ? payload.state.detail : "No outbound picking needs attention.";
    return `
      <section class="warehouse-console-inbound-panel warehouse-console-outbound-panel" data-warehouse-section="outbound_priority">
        <div class="warehouse-console-inbound-head">
          <div>
            <h2 class="warehouse-console-inbound-title">Outbound Work</h2>
            <div class="warehouse-console-inbound-note">Pending customer demand waiting for warehouse review.</div>
          </div>
          <button class="warehouse-console-inbound-open" type="button" data-warehouse-open-outbound>Open outbound picking</button>
        </div>
        <div class="warehouse-console-inbound-cards">${cards.map(renderOutboundCard).join("")}</div>
        <div class="warehouse-console-inbound-preview">
          ${rows.length ? rows.map(renderOutboundPreviewRow).join("") : `<div class="warehouse-console-inbound-row"><span>${escapeHtml(emptyMessage)}</span></div>`}
        </div>
      </section>
    `;
  }

  function renderStockExceptionsOverviewPanel(stockExceptions) {
    const payload = stockExceptions || {};
    const cards = Array.isArray(payload.cards) ? payload.cards.slice(0, 4) : [
      { key: "total_exceptions", label: "Total Exceptions", value: 0, note: "Rows needing warehouse review.", state: "live" },
      { key: "shortage_risk", label: "Shortage Risk", value: 0, note: "Demand short of visible stock posture.", state: "live" },
      { key: "inbound_cover_soon", label: "Inbound Cover Soon", value: 0, note: "Supplier stock expected soon.", state: "live" },
      { key: "missing_posture", label: "Missing Warehouse Posture", value: 0, note: "Warehouse or stock posture is incomplete.", state: "live" },
    ];
    const statePayload = payload.state || {};
    const emptyMessage = statePayload.kind === "empty" ? statePayload.detail : "Review stock exceptions across outbound blockers and inbound cover.";
    return `
      <section class="warehouse-console-inbound-panel warehouse-console-stock-exception-panel" data-warehouse-section="stock_exception_priority">
        <div class="warehouse-console-inbound-head">
          <div>
            <h2 class="warehouse-console-inbound-title">Stock Exceptions</h2>
            <div class="warehouse-console-inbound-note">Outbound blockers, inbound cover, and warehouse posture gaps.</div>
          </div>
          <button class="warehouse-console-inbound-open" type="button" data-warehouse-open-stock-exceptions>Open stock exceptions</button>
        </div>
        <div class="warehouse-console-inbound-cards">${cards.map(renderStockExceptionCard).join("")}</div>
        <div class="warehouse-console-inbound-preview">
          <div class="warehouse-console-inbound-row"><span>${escapeHtml(emptyMessage)}</span></div>
        </div>
      </section>
    `;
  }

  function renderSection(section) {
    const cards = Array.isArray(section.cards) ? section.cards.slice(0, 4) : [];
    const cardMarkup = cards.length ? cards.map((card) => `
      <div class="warehouse-console-status-card" data-warehouse-card="${escapeHtml(card.key || "")}">
        <div>
          <div class="warehouse-console-status-title">${escapeHtml(card.title || "")}</div>
          <div class="warehouse-console-status-note">${escapeHtml(card.note || card.empty_message || "")}</div>
        </div>
        <div class="warehouse-console-status-value">${escapeHtml(cardValue(card))}</div>
      </div>
    `).join("") : `
      <div class="warehouse-console-status-card">
        <div>
          <div class="warehouse-console-status-title">${escapeHtml(section.empty_message || "No warehouse work needs attention right now.")}</div>
        </div>
        <div class="warehouse-console-status-value">0</div>
      </div>
    `;
    return `
      <section class="warehouse-console-section" data-warehouse-section="${escapeHtml(section.key || "")}">
        <div class="warehouse-console-section-head">
          <h2 class="warehouse-console-section-title">${escapeHtml(section.title || "")}</h2>
          <div class="warehouse-console-section-note">${escapeHtml(section.summary || "")}</div>
        </div>
        <div class="warehouse-console-card-grid">${cardMarkup}</div>
      </section>
    `;
  }

  function renderOverview(page, payload) {
    ensureStyle();
    const kpis = Array.isArray(payload.kpis) ? payload.kpis.slice(0, 6) : [];
    const pulseCards = cockpitPulseCards(payload, kpis);
    const chips = ["Read-only", "Warehouse workspace", freshnessText(payload)];
    const $root = $(`
      <div class="sales-console-shell warehouse-console-shell" data-erpw-workspace="warehouse" data-erpw-console-runtime="ready" data-erpw-console-bootstrap="ready" data-warehouse-cockpit="ready">
        <section class="warehouse-console-header" data-warehouse-cockpit-command>
          <div class="warehouse-cockpit-command-row">
            <div>
              <h1 class="warehouse-console-title">Warehouse Console</h1>
              <div class="warehouse-console-note">Protected read-only workspace for inbound receiving, outbound picking, stock exceptions, and posted movement visibility.</div>
              <div class="warehouse-cockpit-chip-row">${chips.map(renderCockpitChip).join("")}</div>
            </div>
            <button class="warehouse-console-refresh" type="button" data-warehouse-refresh>Refresh</button>
          </div>
        </section>
        <section class="warehouse-cockpit-pulse" data-warehouse-cockpit-pulse>
          <div class="warehouse-cockpit-label">Warehouse Pulse</div>
          <div class="warehouse-console-kpi-grid warehouse-cockpit-pulse-grid">${pulseCards.map(renderPulseCard).join("")}</div>
        </section>
        ${renderCockpitStart(payload, kpis)}
        <section class="warehouse-cockpit-route-section" data-warehouse-cockpit-work>
          <div class="warehouse-cockpit-section-head">
            <h2 class="warehouse-cockpit-section-title">Work To Do</h2>
            <div class="warehouse-cockpit-section-note">Supplier-side receiving review and customer-side picking review are paired for daily operations.</div>
          </div>
          <div class="warehouse-cockpit-work-grid">
            ${renderInboundOverviewPanel(payload.inbound || {})}
            ${renderOutboundOverviewPanel(payload.outbound || {})}
          </div>
        </section>
        ${renderCockpitRiskSection()}
        ${renderCockpitMovementSection()}
        <section class="warehouse-cockpit-guardrail" data-warehouse-cockpit-guardrail>
          Warehouse Console is read-only in this phase. Stock updates stay in controlled ERP operations.
        </section>
      </div>
    `);
    $root.find("[data-warehouse-refresh]").on("click", (event) => {
      event.preventDefault();
      activeOverviewRenderState = null;
      $root.remove();
      render(directRenderWrapper());
    });
    $root.find("[data-warehouse-open-inbound]").on("click", (event) => {
      event.preventDefault();
      frappe.route_options = {};
      frappe.set_route(WORKLIST_PAGE_KEY, "inbound-receiving");
    });
    $root.find("[data-warehouse-open-outbound]").on("click", (event) => {
      event.preventDefault();
      frappe.route_options = {};
      frappe.set_route(WORKLIST_PAGE_KEY, "outbound-picking");
    });
    $root.find("[data-warehouse-open-stock-exceptions]").on("click", (event) => {
      event.preventDefault();
      frappe.route_options = {};
      frappe.set_route(WORKLIST_PAGE_KEY, "stock-exceptions");
    });
    $root.find("[data-warehouse-open-movement]").on("click", (event) => {
      event.preventDefault();
      frappe.route_options = {};
      frappe.set_route(WORKLIST_PAGE_KEY, "movement-visibility");
    });
    $root.find("[data-warehouse-open-transfer]").on("click", (event) => {
      event.preventDefault();
      frappe.route_options = {};
      frappe.set_route(WORKLIST_PAGE_KEY, "transfer-visibility");
    });
    replacePageBody(page, $root);
    cleanupOverviewPageHeads();
  }

  function fetchOverviewWithRetry(attempt) {
    return frappe.call({ method: OVERVIEW_METHOD }).catch((error) => {
      const nextDelay = BOOTSTRAP_RETRY_DELAYS[attempt || 0];
      if (!isActiveWarehouseRoute() || nextDelay == null) throw error;
      return new Promise((resolve) => {
        setTimeout(resolve, nextDelay);
      }).then(() => fetchOverviewWithRetry((attempt || 0) + 1));
    });
  }

  function cleanupOverviewPageHeads() {
    const route = frappe.get_route ? frappe.get_route() : [];
    const routeKey = Array.isArray(route) ? String(route[0] || "") : "";
    if (routeKey !== PAGE_KEY) return;
    document.querySelectorAll(".page-head").forEach((head) => {
      if (!(head instanceof HTMLElement)) return;
      const text = String(head.textContent || "").replace(/\s+/g, " ").trim();
      const hasManagedTitle = /Warehouse Console/i.test(text);
      if (!hasManagedTitle && (!text || text === "Actions")) {
        head.remove();
      }
    });
  }

  function rootHasWarehouseShell(root) {
    return Boolean(root && root.querySelector && root.querySelector('.sales-console-shell[data-erpw-workspace="warehouse"]'));
  }

  function cleanupDuplicateReadyShells() {
    const shells = Array.from(document.querySelectorAll('.sales-console-shell[data-erpw-workspace="warehouse"]'));
    if (shells.length <= 1) return shells[0] || null;
    shells.slice(1).forEach((shell) => shell.remove());
    removeDuplicateWarehouseHosts(shells[0] && shells[0].parentElement ? shells[0].parentElement : null);
    return shells[0] || null;
  }

  function hasReadyOverviewShell() {
    const shell = cleanupDuplicateReadyShells();
    return Boolean(shell && shell.getAttribute("data-erpw-console-runtime") === "ready" && shell.querySelector(".warehouse-console-kpi-card"));
  }

  function render(wrapper) {
    if (!isActiveWarehouseRoute()) return;
    if (hasReadyOverviewShell()) return;
    const routeSignature = overviewRouteSignature();
    const active = activeOverviewRenderState;
    if (active && active.routeSignature === routeSignature && active.root && document.body.contains(active.root)) {
      if (rootHasWarehouseShell(active.root)) return;
      activeOverviewRenderState = null;
    }
    const page = makeConsolePage(wrapper);
    renderLoadingState(page);
    const renderToken = ++overviewRenderSerial;
    activeOverviewRenderState = { routeSignature, token: renderToken, root: pageBodyElement(page) };
    ensureConsoleRuntime().then(() => fetchOverviewWithRetry(0)).then((response) => {
      if (!isActiveWarehouseRoute() || overviewRouteSignature() !== routeSignature) return;
      if (!activeOverviewRenderState || activeOverviewRenderState.token !== renderToken) return;
      const payload = response && response.message ? response.message : {};
      if (payload.state && payload.state.kind === "restricted") {
        renderState(page, payload.state);
        return;
      }
      renderOverview(page, payload);
    }).catch((error) => {
      if (!activeOverviewRenderState || activeOverviewRenderState.token !== renderToken) return;
      renderState(page, {
        kind: "error",
        title: "Warehouse Console could not be loaded",
        detail: error && error.message ? error.message : "Warehouse information could not be loaded. Refresh or try again.",
      });
    });
  }

  function directRenderWrapper() {
    return document.getElementById("body") || (frappe.container && frappe.container.page && frappe.container.page.wrapper);
  }

  function directInboundRenderWrapper() {
    const pageDef = frappe.pages && frappe.pages[WORKLIST_PAGE_KEY] ? frappe.pages[WORKLIST_PAGE_KEY] : null;
    if (pageDef && pageDef.wrapper) return pageDef.wrapper;
    return (frappe.container && frappe.container.page && frappe.container.page.wrapper) || document.getElementById("body");
  }

  function directReceivingRenderWrapper() {
    const pageDef = frappe.pages && frappe.pages[RECEIVING_PAGE_KEY] ? frappe.pages[RECEIVING_PAGE_KEY] : null;
    if (pageDef && pageDef.wrapper) return pageDef.wrapper;
    return (frappe.container && frappe.container.page && frappe.container.page.wrapper) || document.getElementById("body");
  }

  function directPickingRenderWrapper() {
    const pageDef = frappe.pages && frappe.pages[PICKING_PAGE_KEY] ? frappe.pages[PICKING_PAGE_KEY] : null;
    if (pageDef && pageDef.wrapper) return pageDef.wrapper;
    return (frappe.container && frappe.container.page && frappe.container.page.wrapper) || document.getElementById("body");
  }

  function directStockExceptionRenderWrapper() {
    const pageDef = frappe.pages && frappe.pages[STOCK_EXCEPTION_PAGE_KEY] ? frappe.pages[STOCK_EXCEPTION_PAGE_KEY] : null;
    if (pageDef && pageDef.wrapper) return pageDef.wrapper;
    return (frappe.container && frappe.container.page && frappe.container.page.wrapper) || document.getElementById("body");
  }

  function directStockPostureRenderWrapper() {
    const pageDef = frappe.pages && frappe.pages[STOCK_POSTURE_PAGE_KEY] ? frappe.pages[STOCK_POSTURE_PAGE_KEY] : null;
    if (pageDef && pageDef.wrapper) return pageDef.wrapper;
    return (frappe.container && frappe.container.page && frappe.container.page.wrapper) || document.getElementById("body");
  }

  function directMovementRenderWrapper() {
    const pageDef = frappe.pages && frappe.pages[MOVEMENT_PAGE_KEY] ? frappe.pages[MOVEMENT_PAGE_KEY] : null;
    if (pageDef && pageDef.wrapper) return pageDef.wrapper;
    return (frappe.container && frappe.container.page && frappe.container.page.wrapper) || document.getElementById("body");
  }

  function hasReadyWorklistShell(queueKey) {
    return Boolean(document.querySelector(`.sales-console-shell[data-erpw-workspace="warehouse"][data-warehouse-view="${worklistViewName(queueKey)}"]`));
  }

  function hasReadyInboundShell() {
    return hasReadyWorklistShell(INBOUND_QUEUE_KEY);
  }

  function shouldSelfRenderInbound() {
    const queueKey = activeWorklistQueueKey();
    return isSupportedWorklistQueue(queueKey) && !hasReadyWorklistShell(queueKey);
  }

  function renderActiveInboundRoute() {
    if (!shouldSelfRenderInbound()) return;
    const signature = inboundRouteSignature();
    const token = ++inboundRouteRenderSerial;
    markWarehouseDiagnostic("activeRouteGuardFired");
    const wrapper = directInboundRenderWrapper();
    if (!wrapper) return;
    window.setTimeout(() => {
      if (token !== inboundRouteRenderSerial || !shouldSelfRenderInbound() || inboundRouteSignature() !== signature) return;
      renderWarehouseWorklist(wrapper, activeWorklistQueueKey());
    }, 0);
  }

  function scheduleActiveInboundRender() {
    renderActiveInboundRoute();
    setTimeout(renderActiveInboundRoute, 80);
    setTimeout(renderActiveInboundRoute, 220);
    setTimeout(renderActiveInboundRoute, 700);
  }

  function bindActiveInboundGuard() {
    if (inboundRouteGuardBound || !window || typeof window.setInterval !== "function") return;
    inboundRouteGuardBound = true;
    window.setInterval(() => {
      if (shouldSelfRenderInbound()) renderActiveInboundRoute();
    }, 220);
  }

  function hasReadyReceivingShell() {
    const po = receivingPurchaseOrderFromRoute();
    const shell = document.querySelector('.warehouse-receiving-shell[data-warehouse-view="receiving-review"]');
    if (!shell) return false;
    return !po || String(shell.getAttribute("data-warehouse-receiving-order") || "") === po;
  }

  function shouldSelfRenderReceiving() {
    return isActiveReceivingRoute() && !hasReadyReceivingShell();
  }

  function renderActiveReceivingRoute() {
    if (!shouldSelfRenderReceiving()) return;
    const signature = receivingRouteSignature();
    const token = ++receivingRouteRenderSerial;
    markWarehouseDiagnostic("receivingActiveRouteGuardFired");
    const wrapper = directReceivingRenderWrapper();
    if (!wrapper) return;
    window.setTimeout(() => {
      if (token !== receivingRouteRenderSerial || !shouldSelfRenderReceiving() || receivingRouteSignature() !== signature) return;
      renderReceivingReview(wrapper, receivingPurchaseOrderFromRoute());
    }, 0);
  }

  function scheduleActiveReceivingRender() {
    renderActiveReceivingRoute();
    setTimeout(renderActiveReceivingRoute, 80);
    setTimeout(renderActiveReceivingRoute, 220);
    setTimeout(renderActiveReceivingRoute, 700);
  }

  function bindActiveReceivingGuard() {
    if (receivingRouteGuardBound || !window || typeof window.setInterval !== "function") return;
    receivingRouteGuardBound = true;
    window.setInterval(() => {
      if (shouldSelfRenderReceiving()) renderActiveReceivingRoute();
    }, 220);
  }

  function hasReadyPickingShell() {
    const order = pickingSalesOrderFromRoute();
    const shell = document.querySelector('.warehouse-picking-shell[data-warehouse-view="picking-review"]');
    if (!shell) return false;
    return !order || String(shell.getAttribute("data-warehouse-picking-order") || "") === order;
  }

  function shouldSelfRenderPicking() {
    return isActivePickingRoute() && !hasReadyPickingShell();
  }

  function renderActivePickingRoute() {
    if (!shouldSelfRenderPicking()) return;
    const signature = pickingRouteSignature();
    const token = ++pickingRouteRenderSerial;
    markWarehouseDiagnostic("pickingActiveRouteGuardFired");
    const wrapper = directPickingRenderWrapper();
    if (!wrapper) return;
    window.setTimeout(() => {
      if (token !== pickingRouteRenderSerial || !shouldSelfRenderPicking() || pickingRouteSignature() !== signature) return;
      renderPickingReview(wrapper, pickingSalesOrderFromRoute());
    }, 0);
  }

  function scheduleActivePickingRender() {
    renderActivePickingRoute();
    setTimeout(renderActivePickingRoute, 80);
    setTimeout(renderActivePickingRoute, 220);
    setTimeout(renderActivePickingRoute, 700);
  }

  function bindActivePickingGuard() {
    if (pickingRouteGuardBound || !window || typeof window.setInterval !== "function") return;
    pickingRouteGuardBound = true;
    window.setInterval(() => {
      if (shouldSelfRenderPicking()) renderActivePickingRoute();
    }, 220);
  }

  function hasReadyStockExceptionReviewShell() {
    const token = stockExceptionTokenFromRoute();
    const shell = document.querySelector('.warehouse-stock-exception-review-shell[data-warehouse-view="stock-exception-review"]');
    if (!shell) return false;
    return !token || String(shell.getAttribute("data-warehouse-stock-exception-token") || "") === token;
  }

  function shouldSelfRenderStockExceptionReview() {
    return isActiveStockExceptionRoute() && !hasReadyStockExceptionReviewShell();
  }

  function renderActiveStockExceptionRoute() {
    if (!shouldSelfRenderStockExceptionReview()) return;
    const signature = stockExceptionRouteSignature();
    const token = ++stockExceptionRouteRenderSerial;
    markWarehouseDiagnostic("stockExceptionActiveRouteGuardFired");
    const wrapper = directStockExceptionRenderWrapper();
    if (!wrapper) return;
    window.setTimeout(() => {
      if (token !== stockExceptionRouteRenderSerial || !shouldSelfRenderStockExceptionReview() || stockExceptionRouteSignature() !== signature) return;
      renderStockExceptionReview(wrapper, stockExceptionTokenFromRoute());
    }, 0);
  }

  function scheduleActiveStockExceptionRender() {
    renderActiveStockExceptionRoute();
    setTimeout(renderActiveStockExceptionRoute, 80);
    setTimeout(renderActiveStockExceptionRoute, 220);
    setTimeout(renderActiveStockExceptionRoute, 700);
  }

  function bindActiveStockExceptionGuard() {
    if (stockExceptionRouteGuardBound || !window || typeof window.setInterval !== "function") return;
    stockExceptionRouteGuardBound = true;
    window.setInterval(() => {
      if (shouldSelfRenderStockExceptionReview()) renderActiveStockExceptionRoute();
    }, 220);
  }

  function hasReadyStockPostureReviewShell() {
    const token = stockPostureTokenFromRoute();
    const shell = document.querySelector('.warehouse-stock-posture-shell[data-warehouse-view="stock-posture-review"]');
    if (!shell) return false;
    return !token || String(shell.getAttribute("data-warehouse-stock-posture-token") || "") === token;
  }

  function shouldSelfRenderStockPostureReview() {
    return isActiveStockPostureRoute() && !hasReadyStockPostureReviewShell();
  }

  function renderActiveStockPostureRoute() {
    if (!shouldSelfRenderStockPostureReview()) return;
    const signature = stockPostureRouteSignature();
    const token = ++stockPostureRouteRenderSerial;
    markWarehouseDiagnostic("stockPostureActiveRouteGuardFired");
    const wrapper = directStockPostureRenderWrapper();
    if (!wrapper) return;
    window.setTimeout(() => {
      if (token !== stockPostureRouteRenderSerial || !shouldSelfRenderStockPostureReview() || stockPostureRouteSignature() !== signature) return;
      renderStockPostureReview(wrapper, stockPostureTokenFromRoute());
    }, 0);
  }

  function scheduleActiveStockPostureRender() {
    renderActiveStockPostureRoute();
    setTimeout(renderActiveStockPostureRoute, 80);
    setTimeout(renderActiveStockPostureRoute, 220);
    setTimeout(renderActiveStockPostureRoute, 700);
  }

  function bindActiveStockPostureGuard() {
    if (stockPostureRouteGuardBound || !window || typeof window.setInterval !== "function") return;
    stockPostureRouteGuardBound = true;
    window.setInterval(() => {
      if (shouldSelfRenderStockPostureReview()) renderActiveStockPostureRoute();
    }, 220);
  }

  function hasReadyMovementReviewShell() {
    const token = movementTokenFromRoute();
    const shell = document.querySelector('.warehouse-movement-review-shell[data-warehouse-view="movement-review"]');
    if (!shell) return false;
    return !token || String(shell.getAttribute("data-warehouse-movement-review-token") || "") === token;
  }

  function shouldSelfRenderMovementReview() {
    return isActiveMovementRoute() && !hasReadyMovementReviewShell();
  }

  function renderActiveMovementRoute() {
    if (!shouldSelfRenderMovementReview()) return;
    const signature = movementRouteSignature();
    const token = ++movementRouteRenderSerial;
    markWarehouseDiagnostic("movementActiveRouteGuardFired");
    const wrapper = directMovementRenderWrapper();
    if (!wrapper) return;
    window.setTimeout(() => {
      if (token !== movementRouteRenderSerial || !shouldSelfRenderMovementReview() || movementRouteSignature() !== signature) return;
      renderMovementReview(wrapper, movementTokenFromRoute());
    }, 0);
  }

  function scheduleActiveMovementRender() {
    renderActiveMovementRoute();
    setTimeout(renderActiveMovementRoute, 80);
    setTimeout(renderActiveMovementRoute, 220);
    setTimeout(renderActiveMovementRoute, 700);
  }

  function bindActiveMovementGuard() {
    if (movementRouteGuardBound || !window || typeof window.setInterval !== "function") return;
    movementRouteGuardBound = true;
    window.setInterval(() => {
      if (shouldSelfRenderMovementReview()) renderActiveMovementRoute();
    }, 220);
  }

  function shouldSelfRenderOverview() {
    if (!isActiveWarehouseRoute()) return false;
    const shell = document.querySelector('.sales-console-shell[data-erpw-workspace="warehouse"]');
    if (!shell) return true;
    const runtimeState = shell.getAttribute("data-erpw-console-runtime") || "";
    const bootstrapState = shell.getAttribute("data-erpw-console-bootstrap") || "";
    if (runtimeState === "loading" || bootstrapState === "loading") return false;
    return !document.querySelector(".warehouse-console-kpi-card");
  }

  function renderActiveOverviewRoute() {
    if (!shouldSelfRenderOverview()) return;
    const wrapper = directRenderWrapper();
    if (!wrapper) return;
    render(wrapper);
  }

  function scheduleActiveOverviewRender() {
    renderActiveOverviewRoute();
    setTimeout(renderActiveOverviewRoute, 80);
    setTimeout(renderActiveOverviewRoute, 220);
    setTimeout(renderActiveOverviewRoute, 700);
  }

  function bindActiveOverviewGuard() {
    if (activeOverviewGuardBound || !window || typeof window.setInterval !== "function") return;
    activeOverviewGuardBound = true;
    window.setInterval(() => {
      if (shouldSelfRenderOverview()) renderActiveOverviewRoute();
    }, 220);
  }

  function collectInboundFilters($host) {
    const values = {};
    $host.find("[data-warehouse-filter-key]").each(function () {
      const key = String(this.getAttribute("data-warehouse-filter-key") || "").trim();
      const value = String($(this).val() || "").trim();
      if (key && value) values[key] = value;
    });
    return values;
  }

  function controlField(field) {
    const value = escapeHtml(field.value || "");
    if (field.type === "select") {
      const options = Array.isArray(field.options) ? field.options : [];
      return `
        <div class="warehouse-inbound-field" data-warehouse-inbound-filter-field="${escapeHtml(field.key || "")}">
          <label>${escapeHtml(field.label || "")}</label>
          <select data-warehouse-filter-key="${escapeHtml(field.key || "")}">
            ${options.map((option) => `<option value="${escapeHtml(option.value || "")}"${String(option.value || "") === String(field.value || "") ? " selected" : ""}>${escapeHtml(option.label || "")}</option>`).join("")}
          </select>
        </div>
      `;
    }
    return `
      <div class="warehouse-inbound-field" data-warehouse-inbound-filter-field="${escapeHtml(field.key || "")}">
        <label>${escapeHtml(field.label || "")}</label>
        <input type="text" value="${value}" placeholder="${escapeHtml(field.placeholder || "")}" data-warehouse-filter-key="${escapeHtml(field.key || "")}" />
      </div>
    `;
  }

  function renderQueueCard(card) {
    return `
      <div class="warehouse-inbound-queue-card" data-warehouse-inbound-queue-card="${escapeHtml(card.key || "")}" data-warehouse-outbound-queue-card="${escapeHtml(card.key || "")}">
        <div class="warehouse-inbound-queue-card-label">${escapeHtml(card.label || card.title || "")}</div>
        <div class="warehouse-inbound-queue-card-value">${escapeHtml(cardValue(card))}</div>
        <div class="warehouse-inbound-queue-card-note">${escapeHtml(card.note || "")}</div>
      </div>
    `;
  }

  function renderQueueRow(row) {
    const lines = Array.isArray(row.lines) ? row.lines : [];
    const rowKey = row.primary_id || row.purchase_order || row.sales_order || row.name || row.key || "";
    const partner = row.partner || row.supplier || row.customer || "";
    const progress = row.received_percent || row.delivered_percent || "0%";
    const detailButton = row.purchase_order
      ? '<button type="button" class="warehouse-inbound-queue-button" data-warehouse-row-open-detail>View details</button>'
      : row.sales_order
        ? '<button type="button" class="warehouse-inbound-queue-button" data-warehouse-row-open-picking-detail>View details</button>'
        : "";
    return `
      <article class="warehouse-inbound-row" data-warehouse-inbound-row="${escapeHtml(rowKey)}" data-warehouse-outbound-row="${escapeHtml(rowKey)}">
        <div class="warehouse-inbound-row-main">
          <div>
            <div class="warehouse-inbound-order">${escapeHtml(rowKey)}</div>
            <div class="warehouse-inbound-meta">${escapeHtml(partner)}</div>
          </div>
          <div class="warehouse-inbound-meta">${escapeHtml(row.target_warehouse || "")}</div>
          <div class="warehouse-inbound-meta">${escapeHtml(row.age_label || row.required_date || "")}</div>
          <div class="warehouse-inbound-meta">${escapeHtml(row.remaining_summary || "")} · ${escapeHtml(progress)}</div>
          <div class="warehouse-receiving-actions">
            ${detailButton}
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-row-toggle>View lines</button>
          </div>
        </div>
        <div class="warehouse-inbound-lines">
          ${lines.length ? lines.map((line) => `
            <div class="warehouse-inbound-line">
              <span>${escapeHtml(line.item_code || "")} ${escapeHtml(line.item_name || "")}</span>
              <span>${escapeHtml(line.remaining_qty || "")} ${escapeHtml(line.uom || "")}</span>
              <span>${escapeHtml(line.target_warehouse || "")}</span>
            </div>
          `).join("") : `<div class="warehouse-inbound-line"><span>No item line details available.</span></div>`}
        </div>
      </article>
    `;
  }

  function renderQueueGroup(group) {
    const rows = Array.isArray(group.rows) ? group.rows : [];
    return `
      <section class="warehouse-inbound-group" data-warehouse-inbound-group="${escapeHtml(group.key || "")}" data-warehouse-outbound-group="${escapeHtml(group.key || "")}">
        <div class="warehouse-inbound-group-head">
          <h2 class="warehouse-inbound-group-title">${escapeHtml(group.title || "")}</h2>
          <div class="warehouse-inbound-group-note">${escapeHtml(rows.length ? `${rows.length} shown` : group.summary || "")}</div>
        </div>
        <div class="warehouse-console-card-grid">
          ${rows.length ? rows.map(renderQueueRow).join("") : `<div class="warehouse-inbound-row" data-warehouse-inbound-empty data-warehouse-outbound-empty><span class="warehouse-inbound-meta">No work matches these filters.</span></div>`}
        </div>
      </section>
    `;
  }

  function renderStockExceptionCard(card) {
    return `
      <div class="warehouse-inbound-queue-card" data-warehouse-stock-exception-card="${escapeHtml(card.key || "")}">
        <div class="warehouse-inbound-queue-card-label">${escapeHtml(card.label || card.title || "")}</div>
        <div class="warehouse-inbound-queue-card-value">${escapeHtml(cardValue(card))}</div>
        <div class="warehouse-inbound-queue-card-note">${escapeHtml(card.note || "")}</div>
      </div>
    `;
  }

  function renderStockExceptionRow(row) {
    const targets = row.route_targets || {};
    const reviewTarget = targets.exception_review || {};
    const pickingTarget = targets.picking || {};
    const receivingTarget = targets.receiving || {};
    const reviewToken = reviewTarget.context_token || row.context_token || "";
    const reviewButton = reviewToken
      ? '<button type="button" class="warehouse-inbound-queue-button" data-warehouse-stock-exception-route-detail>Review exception</button>'
      : "";
    const pickingButton = pickingTarget.sales_order
      ? '<button type="button" class="warehouse-inbound-queue-button" data-warehouse-stock-exception-route-picking>View picking review</button>'
      : "";
    const receivingButton = receivingTarget.purchase_order
      ? '<button type="button" class="warehouse-inbound-queue-button" data-warehouse-stock-exception-route-receiving>View inbound review</button>'
      : "";
    return `
      <article class="warehouse-stock-exception-row" data-warehouse-stock-exception-row="${escapeHtml(row.key || "")}" data-warehouse-stock-exception-token="${escapeHtml(reviewToken)}" data-warehouse-stock-exception-sales-order="${escapeHtml(row.sales_order || "")}" data-warehouse-stock-exception-receiving-order="${escapeHtml(row.expected_inbound_order || "")}">
        <div class="warehouse-stock-exception-row-main">
          <div>
            <div class="warehouse-inbound-order">${escapeHtml(row.sales_order || "")}</div>
            <div class="warehouse-inbound-meta">${escapeHtml(row.customer || "")}</div>
          </div>
          <div>
            <div class="warehouse-inbound-order">${escapeHtml(row.item_code || "")}</div>
            <div class="warehouse-inbound-meta">${escapeHtml(row.item_name || "")}</div>
          </div>
          <div class="warehouse-inbound-meta">${escapeHtml(row.source_warehouse || "")}</div>
          <div>
            <span class="warehouse-inbound-badge">${escapeHtml(row.exception_label || "")}</span>
            <div class="warehouse-inbound-meta">${escapeHtml(row.urgency_label || "")}</div>
          </div>
          <div class="warehouse-receiving-actions">
            ${reviewButton}
            ${pickingButton}
            ${receivingButton}
          </div>
        </div>
        <div class="warehouse-stock-exception-facts">
          <div class="warehouse-stock-exception-fact">Pending ${escapeHtml(row.pending_qty || "0")} ${escapeHtml(row.uom || "")}</div>
          <div class="warehouse-stock-exception-fact">Available ${escapeHtml(row.available_qty || "N/A")} ? Projected ${escapeHtml(row.projected_qty || "N/A")}</div>
          <div class="warehouse-stock-exception-fact">Short ${escapeHtml(row.short_qty || "0")} ${escapeHtml(row.uom || "")}</div>
          <div class="warehouse-stock-exception-fact">Inbound ${escapeHtml(row.expected_inbound_qty || "0")} ${escapeHtml(row.expected_inbound_date || "")}</div>
        </div>
        <div class="warehouse-inbound-meta">${escapeHtml(row.explanation || "")}</div>
      </article>
    `;
  }

  function renderStockExceptionGroup(group) {
    const rows = Array.isArray(group.rows) ? group.rows : [];
    return `
      <section class="warehouse-inbound-group" data-warehouse-stock-exception-group="${escapeHtml(group.key || "")}">
        <div class="warehouse-inbound-group-head">
          <h2 class="warehouse-inbound-group-title">${escapeHtml(group.title || "")}</h2>
          <div class="warehouse-inbound-group-note">${escapeHtml(rows.length ? `${rows.length} shown` : group.summary || "")}</div>
        </div>
        <div class="warehouse-console-card-grid">
          ${rows.length ? rows.map(renderStockExceptionRow).join("") : `<div class="warehouse-stock-exception-row" data-warehouse-stock-exception-empty><span class="warehouse-inbound-meta">No stock exceptions match these filters.</span></div>`}
        </div>
      </section>
    `;
  }

  function renderStockExceptionsPayload(viewState, payload) {
    ensureStyle();
    const controls = payload.controls || {};
    const fields = Array.isArray(controls.fields) ? controls.fields : [];
    const cards = Array.isArray(payload.cards) ? payload.cards : [];
    const groups = Array.isArray(payload.groups) ? payload.groups : [];
    const statePayload = payload.state || {};
    const $root = $(`
      <div class="sales-console-shell warehouse-inbound-shell warehouse-stock-exception-shell" data-erpw-workspace="warehouse" data-warehouse-view="stock-exceptions" data-warehouse-queue-key="${STOCK_EXCEPTIONS_KEY}" data-warehouse-stock-exception-shell="true" data-erpw-console-runtime="ready">
        <section class="warehouse-inbound-queue-header">
          <div class="warehouse-inbound-queue-head">
            <div>
              <h1 class="warehouse-inbound-queue-title">${escapeHtml(payload.summary && payload.summary.title || "Stock Exceptions")}</h1>
              <div class="warehouse-inbound-queue-note">${escapeHtml(payload.summary && payload.summary.subtitle || "Outbound blockers, inbound cover, and warehouse posture gaps.")}</div>
            </div>
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-back-overview>Open Warehouse page</button>
          </div>
          <div class="warehouse-inbound-queue-cards">${cards.map(renderStockExceptionCard).join("")}</div>
          <div class="warehouse-inbound-controls">
            ${fields.map(controlField).join("")}
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-apply>Apply</button>
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-reset>Reset</button>
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-refresh>Refresh</button>
          </div>
        </section>
        <div class="warehouse-inbound-groups">
          ${statePayload.kind === "restricted" || statePayload.kind === "error"
            ? `<section class="warehouse-inbound-group" data-warehouse-stock-exception-group="state"><h2 class="warehouse-inbound-group-title">${escapeHtml(statePayload.title || "Stock exceptions unavailable")}</h2><div class="warehouse-inbound-meta" data-warehouse-stock-exception-empty>${escapeHtml(statePayload.detail || "Stock exceptions could not be loaded. Refresh or contact an administrator.")}</div></section>`
            : groups.map(renderStockExceptionGroup).join("")}
        </div>
      </div>
    `);
    $root.find("[data-warehouse-back-overview]").on("click", (event) => {
      event.preventDefault();
      frappe.set_route(PAGE_KEY);
    });
    $root.find("[data-warehouse-filter-apply]").on("click", (event) => {
      event.preventDefault();
      viewState.activeFilters = collectInboundFilters($root);
      loadInboundQueue(viewState, { force: true });
    });
    $root.find("[data-warehouse-filter-reset]").on("click", (event) => {
      event.preventDefault();
      viewState.activeFilters = {};
      loadInboundQueue(viewState, { force: true });
    });
    $root.find("[data-warehouse-filter-refresh]").on("click", (event) => {
      event.preventDefault();
      loadInboundQueue(viewState, { force: true });
    });
    $root.find("[data-warehouse-stock-exception-route-picking]").on("click", function (event) {
      event.preventDefault();
      const salesOrder = String($(this).closest("[data-warehouse-stock-exception-sales-order]").attr("data-warehouse-stock-exception-sales-order") || "").trim();
      if (salesOrder) frappe.set_route(PICKING_PAGE_KEY, salesOrder);
    });
    $root.find("[data-warehouse-stock-exception-route-detail]").on("click", function (event) {
      event.preventDefault();
      const token = String($(this).closest("[data-warehouse-stock-exception-token]").attr("data-warehouse-stock-exception-token") || "").trim();
      if (token) frappe.set_route(STOCK_EXCEPTION_PAGE_KEY, token);
    });
    $root.find("[data-warehouse-stock-exception-route-receiving]").on("click", function (event) {
      event.preventDefault();
      const purchaseOrder = String($(this).closest("[data-warehouse-stock-exception-receiving-order]").attr("data-warehouse-stock-exception-receiving-order") || "").trim();
      if (purchaseOrder) frappe.set_route(RECEIVING_PAGE_KEY, purchaseOrder);
    });
    removeDuplicateWarehouseHosts(viewState.$host.get(0));
    viewState.$host.empty().append($root);
  }

  function renderMovementCard(card) {
    return `
      <div class="warehouse-inbound-queue-card" data-warehouse-movement-card="${escapeHtml(card.key || "")}">
        <div class="warehouse-inbound-queue-card-label">${escapeHtml(card.label || card.title || "")}</div>
        <div class="warehouse-inbound-queue-card-value">${escapeHtml(cardValue(card))}</div>
        <div class="warehouse-inbound-queue-card-note">${escapeHtml(card.note || "")}</div>
      </div>
    `;
  }

  function renderMovementSampleItem(item) {
    const target = item.route_target || {};
    const token = target.route === STOCK_POSTURE_PAGE_KEY ? String(target.context_token || "") : "";
    const button = token
      ? `<button type="button" class="warehouse-inbound-queue-button" data-warehouse-movement-route-stock-posture data-warehouse-stock-posture-token="${escapeHtml(token)}">Review stock posture</button>`
      : "";
    return `
      <div class="warehouse-inbound-line" data-warehouse-movement-sample-item="${escapeHtml(item.item_code || "")}">
        <span>${escapeHtml(item.item_code || "")} ${escapeHtml(item.item_name || "")}</span>
        <span>${escapeHtml(item.qty || "0")} ${escapeHtml(item.uom || "")}</span>
        <span>${escapeHtml(item.target_warehouse || item.source_warehouse || "")}</span>
        <span>${button}</span>
      </div>
    `;
  }

  function renderMovementRow(row) {
    const items = Array.isArray(row.sample_items) ? row.sample_items : [];
    const targets = row.route_targets || {};
    const reviewTarget = targets.movement_review || {};
    const reviewToken = reviewTarget.route === MOVEMENT_PAGE_KEY ? String(reviewTarget.context_token || "") : "";
    const reviewButton = reviewToken
      ? `<button type="button" class="warehouse-inbound-queue-button" data-warehouse-movement-route-review data-warehouse-movement-review-token="${escapeHtml(reviewToken)}">Review movement</button>`
      : "";
    return `
      <article class="warehouse-inbound-row warehouse-stock-exception-row warehouse-movement-row" data-warehouse-movement-row="${escapeHtml(row.movement_id || row.key || "")}">
        <div class="warehouse-stock-exception-row-main">
          <div>
            <div class="warehouse-inbound-order">${escapeHtml(row.movement_id || "")}</div>
            <div class="warehouse-inbound-meta">${escapeHtml(row.posting_date || "")} ${escapeHtml(row.posting_time || "")}</div>
          </div>
          <div>
            <span class="warehouse-inbound-badge">${escapeHtml(row.movement_type || row.purpose || "")}</span>
            <div class="warehouse-inbound-meta">${escapeHtml(row.group_label || "")}</div>
          </div>
          <div class="warehouse-inbound-meta">${escapeHtml(row.direction_label || "")}</div>
          <div>
            <div class="warehouse-inbound-order">${escapeHtml(row.quantity_summary || "")}</div>
            <div class="warehouse-inbound-meta">${escapeHtml(row.item_count == null ? "0" : row.item_count)} items</div>
          </div>
          <div class="warehouse-receiving-actions">
            ${reviewButton}
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-row-toggle>View lines</button>
          </div>
        </div>
        <div class="warehouse-inbound-lines">
          ${items.length ? items.map(renderMovementSampleItem).join("") : `<div class="warehouse-inbound-line" data-warehouse-movement-empty><span>No item summary available.</span></div>`}
        </div>
      </article>
    `;
  }

  function renderMovementGroup(group) {
    const rows = Array.isArray(group.rows) ? group.rows : [];
    return `
      <section class="warehouse-inbound-group" data-warehouse-movement-group="${escapeHtml(group.key || "")}">
        <div class="warehouse-inbound-group-head">
          <h2 class="warehouse-inbound-group-title">${escapeHtml(group.title || "")}</h2>
          <div class="warehouse-inbound-group-note">${escapeHtml(rows.length ? `${rows.length} shown` : group.summary || "")}</div>
        </div>
        <div class="warehouse-console-card-grid">
          ${rows.length ? rows.map(renderMovementRow).join("") : `<div class="warehouse-stock-exception-row" data-warehouse-movement-empty><span class="warehouse-inbound-meta">No movement records match these filters.</span></div>`}
        </div>
      </section>
    `;
  }

  function renderMovementPayload(viewState, payload) {
    ensureStyle();
    const controls = payload.controls || {};
    const fields = Array.isArray(controls.fields) ? controls.fields : [];
    const cards = Array.isArray(payload.cards) ? payload.cards : [];
    const groups = Array.isArray(payload.groups) ? payload.groups : [];
    const statePayload = payload.state || {};
    const $root = $(`
      <div class="sales-console-shell warehouse-inbound-shell warehouse-movement-shell" data-erpw-workspace="warehouse" data-warehouse-view="movement-visibility" data-warehouse-queue-key="${MOVEMENT_VISIBILITY_KEY}" data-warehouse-movement-shell="true" data-erpw-console-runtime="ready">
        <section class="warehouse-inbound-queue-header">
          <div class="warehouse-inbound-queue-head">
            <div>
              <h1 class="warehouse-inbound-queue-title">${escapeHtml(payload.summary && payload.summary.title || "Movement Visibility")}</h1>
              <div class="warehouse-inbound-queue-note">${escapeHtml(payload.summary && payload.summary.subtitle || "Recorded stock movement posture across warehouses.")}</div>
            </div>
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-back-overview>Open Warehouse page</button>
          </div>
          <div class="warehouse-inbound-queue-cards">${cards.map(renderMovementCard).join("")}</div>
          <div class="warehouse-inbound-controls">
            ${fields.map(controlField).join("")}
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-apply>Apply</button>
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-reset>Reset</button>
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-refresh>Refresh</button>
          </div>
        </section>
        <div class="warehouse-inbound-groups">
          ${statePayload.kind === "restricted" || statePayload.kind === "error"
            ? `<section class="warehouse-inbound-group" data-warehouse-movement-group="state"><h2 class="warehouse-inbound-group-title">${escapeHtml(statePayload.title || "Movement visibility unavailable")}</h2><div class="warehouse-inbound-meta" data-warehouse-movement-empty>${escapeHtml(statePayload.detail || "Movement visibility could not be loaded. Refresh or contact an administrator.")}</div></section>`
            : groups.map(renderMovementGroup).join("")}
        </div>
      </div>
    `);
    $root.find("[data-warehouse-back-overview]").on("click", (event) => {
      event.preventDefault();
      frappe.set_route(PAGE_KEY);
    });
    $root.find("[data-warehouse-filter-apply]").on("click", (event) => {
      event.preventDefault();
      viewState.activeFilters = collectInboundFilters($root);
      loadInboundQueue(viewState, { force: true });
    });
    $root.find("[data-warehouse-filter-reset]").on("click", (event) => {
      event.preventDefault();
      viewState.activeFilters = {};
      loadInboundQueue(viewState, { force: true });
    });
    $root.find("[data-warehouse-filter-refresh]").on("click", (event) => {
      event.preventDefault();
      loadInboundQueue(viewState, { force: true });
    });
    $root.find("[data-warehouse-row-toggle]").on("click", function (event) {
      event.preventDefault();
      $(this).closest("[data-warehouse-movement-row]").toggleClass("is-expanded");
    });
    $root.find("[data-warehouse-movement-route-review]").on("click", function (event) {
      event.preventDefault();
      const token = String(this.getAttribute("data-warehouse-movement-review-token") || "").trim();
      if (token) frappe.set_route(MOVEMENT_PAGE_KEY, token);
    });
    $root.find("[data-warehouse-movement-route-stock-posture]").on("click", function (event) {
      event.preventDefault();
      const token = String(this.getAttribute("data-warehouse-stock-posture-token") || "").trim();
      if (token) frappe.set_route(STOCK_POSTURE_PAGE_KEY, token);
    });
    removeDuplicateWarehouseHosts(viewState.$host.get(0));
    viewState.$host.empty().append($root);
  }

  function renderTransferCard(card) {
    return `
      <div class="warehouse-inbound-queue-card" data-warehouse-transfer-card="${escapeHtml(card.key || "")}">
        <div class="warehouse-inbound-queue-card-label">${escapeHtml(card.label || card.title || "")}</div>
        <div class="warehouse-inbound-queue-card-value">${escapeHtml(cardValue(card))}</div>
        <div class="warehouse-inbound-queue-card-note">${escapeHtml(card.note || "")}</div>
      </div>
    `;
  }

  function transferItemCountLabel(count) {
    const value = count == null || count === "" ? 0 : Number(count);
    const normalized = Number.isFinite(value) ? value : count;
    return `${normalized} ${String(normalized) === "1" ? "item" : "items"}`;
  }

  function transferDirectionText(source, target, fallback) {
    const fromText = String(source || "").trim();
    const toText = String(target || "").trim();
    if (fromText && toText) return `${fromText} -> ${toText}`;
    if (fromText) return `${fromText} -> target needs review`;
    if (toText) return `Source needs review -> ${toText}`;
    return fallback || "Warehouse direction needs review";
  }

  function transferGroupEmptyText(group) {
    const key = String(group && group.key || "").trim();
    const messages = {
      direct_transfers: "No direct transfers match these filters. Clear source-to-target records will appear here.",
      transit_related: "No transit-related transfers match these filters. Transit warehouse posture will appear here.",
      needs_review: "No transfers need review for these filters. Missing or mixed warehouse posture will appear here.",
      recently_posted: "No recently posted transfers match these filters. Submitted transfer records in the selected window will appear here.",
    };
    return messages[key] || "No posted transfers match these filters.";
  }

  function renderTransferSampleItem(item) {
    const target = item.route_target || {};
    const token = target.route === STOCK_POSTURE_PAGE_KEY ? String(target.context_token || "") : "";
    const button = token
      ? `<button type="button" class="warehouse-inbound-queue-button" data-warehouse-transfer-route-stock-posture data-warehouse-stock-posture-token="${escapeHtml(token)}">Review stock posture</button>`
      : "";
    return `
      <div class="warehouse-inbound-line" data-warehouse-transfer-sample-item="${escapeHtml(item.item_code || "")}">
        <span>${escapeHtml(item.item_code || "")} ${escapeHtml(item.item_name || "")}</span>
        <span>${escapeHtml(item.qty || "0")} ${escapeHtml(item.uom || "")}</span>
        <span>${escapeHtml(transferDirectionText(item.source_warehouse, item.target_warehouse, ""))}</span>
        <span>${button}</span>
      </div>
    `;
  }

  function renderTransferRow(row) {
    const items = Array.isArray(row.sample_items) ? row.sample_items : [];
    const targets = row.route_targets || {};
    const reviewTarget = targets.movement_review || {};
    const reviewToken = reviewTarget.route === MOVEMENT_PAGE_KEY ? String(reviewTarget.context_token || "") : "";
    const postureTarget = targets.stock_posture || {};
    const postureToken = postureTarget.route === STOCK_POSTURE_PAGE_KEY ? String(postureTarget.context_token || "") : "";
    const reviewButton = reviewToken
      ? `<button type="button" class="warehouse-inbound-queue-button" data-warehouse-transfer-route-movement data-warehouse-transfer-movement-token="${escapeHtml(reviewToken)}">Review movement</button>`
      : "";
    const postureButton = postureToken
      ? `<button type="button" class="warehouse-inbound-queue-button" data-warehouse-transfer-route-stock-posture data-warehouse-stock-posture-token="${escapeHtml(postureToken)}">Review stock posture</button>`
      : "";
    return `
      <article class="warehouse-inbound-row warehouse-stock-exception-row warehouse-transfer-row" data-warehouse-transfer-row="${escapeHtml(row.transfer_id || row.key || "")}">
        <div class="warehouse-stock-exception-row-main">
          <div>
            <div class="warehouse-inbound-order">${escapeHtml(row.transfer_id || "")}</div>
            <div class="warehouse-inbound-meta">${escapeHtml(row.posting_date || "")} ${escapeHtml(row.posting_time || "")}</div>
          </div>
          <div>
            <span class="warehouse-inbound-badge">${escapeHtml(row.posture || row.group_label || "")}</span>
            <div class="warehouse-inbound-meta">${escapeHtml(row.movement_type || "Material Transfer")}</div>
          </div>
          <div class="warehouse-inbound-meta">${escapeHtml(transferDirectionText(row.source_warehouse, row.target_warehouse, row.direction_label || "Warehouse direction needs review"))}</div>
          <div>
            <div class="warehouse-inbound-order">${escapeHtml(row.quantity_summary || "")}</div>
            <div class="warehouse-inbound-meta">${escapeHtml(transferItemCountLabel(row.item_count))}</div>
          </div>
          <div class="warehouse-receiving-actions">
            ${reviewButton}
            ${postureButton}
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-row-toggle>View lines</button>
          </div>
        </div>
        <div class="warehouse-inbound-lines">
          ${items.length ? items.map(renderTransferSampleItem).join("") : `<div class="warehouse-inbound-line" data-warehouse-transfer-empty><span>No item summary visible for this transfer record.</span></div>`}
        </div>
      </article>
    `;
  }

  function renderTransferGroup(group) {
    const rows = Array.isArray(group.rows) ? group.rows : [];
    return `
      <section class="warehouse-inbound-group" data-warehouse-transfer-group="${escapeHtml(group.key || "")}">
        <div class="warehouse-inbound-group-head">
          <h2 class="warehouse-inbound-group-title">${escapeHtml(group.title || "")}</h2>
          <div class="warehouse-inbound-group-note">${escapeHtml(rows.length ? `${rows.length} shown` : group.summary || "")}</div>
        </div>
        <div class="warehouse-console-card-grid">
          ${rows.length ? rows.map(renderTransferRow).join("") : `<div class="warehouse-stock-exception-row" data-warehouse-transfer-empty><span class="warehouse-inbound-meta">${escapeHtml(transferGroupEmptyText(group))}</span></div>`}
        </div>
      </section>
    `;
  }

  function renderTransferPayload(viewState, payload) {
    ensureStyle();
    const controls = payload.controls || {};
    const fields = Array.isArray(controls.fields) ? controls.fields : [];
    const cards = Array.isArray(payload.cards) ? payload.cards : [];
    const groups = Array.isArray(payload.groups) ? payload.groups : [];
    const statePayload = payload.state || {};
    const unavailable = ["restricted", "error", "unavailable"].includes(String(statePayload.kind || ""));
    const $root = $(`
      <div class="sales-console-shell warehouse-inbound-shell warehouse-transfer-shell" data-erpw-workspace="warehouse" data-warehouse-view="transfer-visibility" data-warehouse-queue-key="${TRANSFER_VISIBILITY_KEY}" data-warehouse-transfer-shell="true" data-erpw-console-runtime="ready">
        <section class="warehouse-inbound-queue-header">
          <div class="warehouse-inbound-queue-head">
            <div>
              <h1 class="warehouse-inbound-queue-title">${escapeHtml(payload.summary && payload.summary.title || "Transfer Visibility")}</h1>
              <div class="warehouse-inbound-queue-note">${escapeHtml(payload.summary && payload.summary.subtitle || "Read-only warehouse-to-warehouse transfer posture.")}</div>
            </div>
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-back-overview>Open Warehouse page</button>
          </div>
          <div class="warehouse-inbound-queue-cards">${cards.map(renderTransferCard).join("")}</div>
          <div class="warehouse-inbound-controls">
            ${fields.map(controlField).join("")}
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-apply>Apply</button>
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-reset>Reset</button>
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-refresh>Refresh</button>
          </div>
        </section>
        <div class="warehouse-inbound-groups">
          ${unavailable
            ? `<section class="warehouse-inbound-group" data-warehouse-transfer-group="state"><h2 class="warehouse-inbound-group-title">${escapeHtml(statePayload.title || "Transfer visibility unavailable")}</h2><div class="warehouse-inbound-meta" data-warehouse-transfer-empty>${escapeHtml(statePayload.detail || "Transfer visibility could not be loaded. Refresh or contact an administrator.")}</div></section>`
            : groups.map(renderTransferGroup).join("")}
        </div>
      </div>
    `);
    $root.find("[data-warehouse-back-overview]").on("click", (event) => {
      event.preventDefault();
      frappe.set_route(PAGE_KEY);
    });
    $root.find("[data-warehouse-filter-apply]").on("click", (event) => {
      event.preventDefault();
      viewState.activeFilters = collectInboundFilters($root);
      loadInboundQueue(viewState, { force: true });
    });
    $root.find("[data-warehouse-filter-reset]").on("click", (event) => {
      event.preventDefault();
      viewState.activeFilters = {};
      loadInboundQueue(viewState, { force: true });
    });
    $root.find("[data-warehouse-filter-refresh]").on("click", (event) => {
      event.preventDefault();
      loadInboundQueue(viewState, { force: true });
    });
    $root.find("[data-warehouse-row-toggle]").on("click", function (event) {
      event.preventDefault();
      $(this).closest("[data-warehouse-transfer-row]").toggleClass("is-expanded");
    });
    $root.find("[data-warehouse-transfer-route-movement]").on("click", function (event) {
      event.preventDefault();
      const token = String(this.getAttribute("data-warehouse-transfer-movement-token") || "").trim();
      if (token) frappe.set_route(MOVEMENT_PAGE_KEY, token);
    });
    $root.find("[data-warehouse-transfer-route-stock-posture]").on("click", function (event) {
      event.preventDefault();
      const token = String(this.getAttribute("data-warehouse-stock-posture-token") || "").trim();
      if (token) frappe.set_route(STOCK_POSTURE_PAGE_KEY, token);
    });
    removeDuplicateWarehouseHosts(viewState.$host.get(0));
    viewState.$host.empty().append($root);
  }

  function renderTransferLoading(viewState) {
    renderTransferPayload(viewState, {
      page: { key: TRANSFER_VISIBILITY_KEY },
      summary: { title: "Transfer Visibility", subtitle: "Checking transfer visibility..." },
      controls: { fields: [], actions: [] },
      cards: [],
      groups: [],
      state: { kind: "loading", title: "Checking transfer visibility", detail: "Checking transfer visibility..." },
    });
  }

  function renderMovementLoading(viewState) {
    renderMovementPayload(viewState, {
      page: { key: MOVEMENT_VISIBILITY_KEY },
      summary: { title: "Movement Visibility", subtitle: "Checking movement visibility..." },
      controls: { fields: [], actions: [] },
      cards: [],
      groups: [],
      state: { kind: "loading", title: "Checking movement visibility", detail: "Checking movement visibility..." },
    });
  }

  function renderStockExceptionsLoading(viewState) {
    renderStockExceptionsPayload(viewState, {
      page: { key: STOCK_EXCEPTIONS_KEY },
      summary: { title: "Stock Exceptions", subtitle: "Checking stock exceptions..." },
      controls: { fields: [], actions: [] },
      cards: [],
      groups: [],
      state: { kind: "loading", title: "Checking stock exceptions", detail: "Checking stock exceptions..." },
    });
  }

  function makeReceivingPage(wrapper) {
    const existing = wrapper && wrapper.__erpwWarehouseReceivingReview;
    if (existing && existing.page && existing.$host && document.documentElement.contains(existing.$host.get(0))) {
      return existing;
    }
    const page = frappe.ui.make_app_page({
      parent: wrapper,
      title: "Receiving Review",
      single_column: true,
    });
    const $parent = page && page.body ? $(page.body) : $(wrapper);
    const $host = $('<section class="warehouse-receiving-route"></section>');
    $parent.empty().append($host);
    const state = { page, $host, purchaseOrder: "" };
    wrapper.__erpwWarehouseReceivingReview = state;
    return state;
  }

  function receivingSummaryText(header) {
    const parts = [header.purchase_order, header.supplier, header.target_warehouse].filter(Boolean);
    return parts.join(" · ");
  }

  function renderReceivingCard(card) {
    return `
      <div class="warehouse-receiving-card" data-warehouse-receiving-card="${escapeHtml(card.key || "")}">
        <div class="warehouse-receiving-card-label">${escapeHtml(card.label || "")}</div>
        <div class="warehouse-receiving-card-value">${escapeHtml(card.value == null ? "--" : card.value)}</div>
        <div class="warehouse-receiving-card-note">${escapeHtml(card.note || "")}</div>
      </div>
    `;
  }

  function renderReceivingLine(line) {
    return `
      <div class="warehouse-receiving-line" data-warehouse-receiving-line="${escapeHtml(line.item_code || "")}">
        <div>
          <div class="warehouse-receiving-strong">${escapeHtml(line.item_code || "")}</div>
          <div class="warehouse-receiving-meta">${escapeHtml(line.item_name || "")}</div>
        </div>
        <div class="warehouse-receiving-meta">Ordered ${escapeHtml(line.ordered_qty || "0")} ${escapeHtml(line.uom || "")}</div>
        <div class="warehouse-receiving-meta">Received ${escapeHtml(line.received_qty || "0")} ${escapeHtml(line.uom || "")}</div>
        <div class="warehouse-receiving-meta">Remaining ${escapeHtml(line.remaining_qty || "0")} ${escapeHtml(line.uom || "")}</div>
        <div class="warehouse-receiving-meta">${escapeHtml(line.status || "")} · ${escapeHtml(line.required_date || "")}</div>
      </div>
    `;
  }

  function renderReceivingHistoryRow(row) {
    return `
      <div class="warehouse-receiving-history-row" data-warehouse-receiving-history-row="${escapeHtml(row.receipt_id || "")}">
        <div>
          <div class="warehouse-receiving-strong">${escapeHtml(row.receipt_id || "")}</div>
          <div class="warehouse-receiving-meta">${escapeHtml(row.posting_date || "")}</div>
        </div>
        <div class="warehouse-receiving-meta">${escapeHtml(row.status || "")}</div>
        <div class="warehouse-receiving-meta">${escapeHtml(row.item_count == null ? "0" : row.item_count)} items</div>
        <div class="warehouse-receiving-meta">${escapeHtml(row.quantity_summary || "")}</div>
      </div>
    `;
  }

  function activateReceivingTab($root, tabKey) {
    const key = tabKey || "item_lines";
    $root.find("[data-warehouse-receiving-tab]").each(function () {
      $(this).toggleClass("is-active", String(this.getAttribute("data-warehouse-receiving-tab")) === key);
    });
    $root.find("[data-warehouse-receiving-panel]").each(function () {
      $(this).toggleClass("is-active", String(this.getAttribute("data-warehouse-receiving-panel")) === key);
    });
  }

  function renderReceivingReviewPayload(viewState, payload) {
    ensureStyle();
    const header = payload.header || {};
    const cards = Array.isArray(payload.summary_cards) ? payload.summary_cards : [];
    const tabs = Array.isArray(payload.tabs) ? payload.tabs : [];
    const lines = Array.isArray(payload.lines) ? payload.lines : [];
    const history = Array.isArray(payload.receipt_history) ? payload.receipt_history : [];
    const statePayload = payload.state || {};
    const unavailable = ["restricted", "error", "unavailable"].includes(String(statePayload.kind || ""));
    const $root = $(`
      <div class="sales-console-shell warehouse-receiving-shell" data-erpw-workspace="warehouse" data-warehouse-view="receiving-review" data-erpw-console-runtime="ready" data-warehouse-receiving-order="${escapeHtml(header.purchase_order || viewState.purchaseOrder || "")}">
        <section class="warehouse-receiving-header">
          <div class="warehouse-receiving-head">
            <div>
              <h1 class="warehouse-receiving-title">Receiving Review</h1>
              <div class="warehouse-receiving-subtitle">${escapeHtml(unavailable ? statePayload.detail || "Receiving work could not be loaded. Refresh or contact an administrator." : receivingSummaryText(header))}</div>
            </div>
            <div class="warehouse-receiving-actions">
              <button type="button" class="warehouse-receiving-button" data-warehouse-receiving-back>Back to inbound receiving</button>
              <button type="button" class="warehouse-receiving-button" data-warehouse-receiving-refresh>Refresh</button>
            </div>
          </div>
          ${unavailable ? `<div class="warehouse-console-state-detail" data-warehouse-receiving-empty>${escapeHtml(statePayload.title || "Receiving review unavailable")}</div>` : `
            <div class="warehouse-receiving-note">${escapeHtml(header.age_label || "")} · ${escapeHtml(header.remaining_summary || "")}</div>
            <div class="warehouse-receiving-cards">${cards.map(renderReceivingCard).join("")}</div>
          `}
        </section>
        <section class="warehouse-receiving-detail">
          <div class="warehouse-receiving-tabs">
            ${tabs.map((tab) => `<button type="button" class="warehouse-receiving-tab" data-warehouse-receiving-tab="${escapeHtml(tab.key || "")}">${escapeHtml(tab.label || "")} ${escapeHtml(tab.count == null ? "" : `(${tab.count})`)}</button>`).join("")}
          </div>
          <div class="warehouse-receiving-panel is-active" data-warehouse-receiving-panel="item_lines">
            ${lines.length ? lines.map(renderReceivingLine).join("") : `<div class="warehouse-receiving-line" data-warehouse-receiving-empty><span class="warehouse-receiving-meta">No item lines visible for this order.</span></div>`}
          </div>
          <div class="warehouse-receiving-panel" data-warehouse-receiving-panel="receipt_history">
            ${history.length ? history.map(renderReceivingHistoryRow).join("") : `<div class="warehouse-receiving-history-row" data-warehouse-receiving-empty><span class="warehouse-receiving-meta">No receipt history visible for this order.</span></div>`}
          </div>
        </section>
      </div>
    `);
    $root.find("[data-warehouse-receiving-back]").on("click", (event) => {
      event.preventDefault();
      frappe.set_route(WORKLIST_PAGE_KEY, "inbound-receiving");
    });
    $root.find("[data-warehouse-receiving-refresh]").on("click", (event) => {
      event.preventDefault();
      loadReceivingReview(viewState, viewState.purchaseOrder);
    });
    $root.find("[data-warehouse-receiving-tab]").on("click", function (event) {
      event.preventDefault();
      activateReceivingTab($root, String(this.getAttribute("data-warehouse-receiving-tab") || "item_lines"));
    });
    activateReceivingTab($root, "item_lines");
    removeDuplicateWarehouseHosts(viewState.$host.get(0));
    viewState.$host.empty().append($root);
  }

  function renderReceivingLoading(viewState) {
    renderReceivingReviewPayload(viewState, {
      state: { kind: "loading", title: "Checking receiving work", detail: "Checking receiving work..." },
      header: { purchase_order: viewState.purchaseOrder || "" },
      summary_cards: [],
      tabs: [
        { key: "item_lines", label: "Item Lines", count: 0 },
        { key: "receipt_history", label: "Receipt History", count: 0 },
      ],
      lines: [],
      receipt_history: [],
    });
  }

  function loadReceivingReview(viewState, purchaseOrder) {
    markWarehouseDiagnostic("receivingServiceCallAttempted");
    viewState.purchaseOrder = purchaseOrder || receivingPurchaseOrderFromRoute();
    renderReceivingLoading(viewState);
    return frappe.call({
      method: RECEIVING_METHOD,
      args: { purchase_order: viewState.purchaseOrder },
    }).then((response) => {
      renderReceivingReviewPayload(viewState, response && response.message ? response.message : {});
    }).catch(() => {
      renderReceivingReviewPayload(viewState, {
        state: { kind: "error", title: "Receiving review unavailable", detail: "Receiving work could not be loaded. Refresh or contact an administrator." },
        header: { purchase_order: viewState.purchaseOrder || "" },
        summary_cards: [],
        tabs: [
          { key: "item_lines", label: "Item Lines", count: 0 },
          { key: "receipt_history", label: "Receipt History", count: 0 },
        ],
        lines: [],
        receipt_history: [],
      });
    });
  }

  function renderReceivingReview(wrapper, purchaseOrder) {
    markWarehouseDiagnostic("renderReceivingReviewEntered");
    const viewState = makeReceivingPage(wrapper);
    if (window.erpWorkspaceConsoleSidebar && typeof window.erpWorkspaceConsoleSidebar.refresh === "function") {
      window.erpWorkspaceConsoleSidebar.refresh();
    }
    loadReceivingReview(viewState, purchaseOrder || receivingPurchaseOrderFromRoute());
  }

  function makePickingPage(wrapper) {
    const existing = wrapper && wrapper.__erpwWarehousePickingReview;
    if (existing && existing.page && existing.$host && document.documentElement.contains(existing.$host.get(0))) {
      return existing;
    }
    const page = frappe.ui.make_app_page({
      parent: wrapper,
      title: "Picking Review",
      single_column: true,
    });
    const $parent = page && page.body ? $(page.body) : $(wrapper);
    const $host = $('<section class="warehouse-picking-route"></section>');
    $parent.empty().append($host);
    const state = { page, $host, salesOrder: "" };
    wrapper.__erpwWarehousePickingReview = state;
    return state;
  }

  function pickingSummaryText(header) {
    const parts = [header.sales_order, header.customer, header.target_warehouse].filter(Boolean);
    return parts.join(" · ");
  }

  function renderPickingCard(card) {
    return `
      <div class="warehouse-receiving-card" data-warehouse-picking-card="${escapeHtml(card.key || "")}">
        <div class="warehouse-receiving-card-label">${escapeHtml(card.label || "")}</div>
        <div class="warehouse-receiving-card-value">${escapeHtml(card.value == null ? "--" : card.value)}</div>
        <div class="warehouse-receiving-card-note">${escapeHtml(card.note || "")}</div>
      </div>
    `;
  }

  function renderPickingLine(line) {
    return `
      <div class="warehouse-receiving-line" data-warehouse-picking-line="${escapeHtml(line.item_code || "")}">
        <div>
          <div class="warehouse-receiving-strong">${escapeHtml(line.item_code || "")}</div>
          <div class="warehouse-receiving-meta">${escapeHtml(line.item_name || "")}</div>
        </div>
        <div class="warehouse-receiving-meta">Ordered ${escapeHtml(line.ordered_qty || "0")} ${escapeHtml(line.uom || "")}</div>
        <div class="warehouse-receiving-meta">Delivered ${escapeHtml(line.delivered_qty || "0")} ${escapeHtml(line.uom || "")}</div>
        <div class="warehouse-receiving-meta">Pending ${escapeHtml(line.pending_qty || "0")} ${escapeHtml(line.uom || "")}</div>
        <div class="warehouse-receiving-meta">${escapeHtml(line.readiness || "")} · ${escapeHtml(line.availability || "")}</div>
      </div>
    `;
  }

  function renderPickingReadinessRow(line) {
    return `
      <div class="warehouse-receiving-history-row" data-warehouse-picking-readiness-row="${escapeHtml(line.item_code || "")}">
        <div>
          <div class="warehouse-receiving-strong">${escapeHtml(line.item_code || "")}</div>
          <div class="warehouse-receiving-meta">${escapeHtml(line.source_warehouse || "")}</div>
        </div>
        <div class="warehouse-receiving-meta">${escapeHtml(line.pending_qty || "0")} ${escapeHtml(line.uom || "")} pending</div>
        <div class="warehouse-receiving-meta">${escapeHtml(line.availability || "")}</div>
        <div class="warehouse-receiving-meta">${escapeHtml(line.readiness || "")}</div>
      </div>
    `;
  }

  function activatePickingTab($root, tabKey) {
    const key = tabKey || "item_lines";
    $root.find("[data-warehouse-picking-tab]").each(function () {
      $(this).toggleClass("is-active", String(this.getAttribute("data-warehouse-picking-tab")) === key);
    });
    $root.find("[data-warehouse-picking-panel]").each(function () {
      $(this).toggleClass("is-active", String(this.getAttribute("data-warehouse-picking-panel")) === key);
    });
  }

  function renderPickingReviewPayload(viewState, payload) {
    ensureStyle();
    const header = payload.header || {};
    const cards = Array.isArray(payload.summary_cards) ? payload.summary_cards : [];
    const tabs = Array.isArray(payload.tabs) ? payload.tabs : [];
    const lines = Array.isArray(payload.lines) ? payload.lines : [];
    const statePayload = payload.state || {};
    const unavailable = ["restricted", "error", "unavailable"].includes(String(statePayload.kind || ""));
    const $root = $(`
      <div class="sales-console-shell warehouse-receiving-shell warehouse-picking-shell" data-erpw-workspace="warehouse" data-warehouse-view="picking-review" data-erpw-console-runtime="ready" data-warehouse-picking-order="${escapeHtml(header.sales_order || viewState.salesOrder || "")}">
        <section class="warehouse-receiving-header">
          <div class="warehouse-receiving-head">
            <div>
              <h1 class="warehouse-receiving-title">Picking Review</h1>
              <div class="warehouse-receiving-subtitle">${escapeHtml(unavailable ? statePayload.detail || "Picking work could not be loaded. Refresh or contact an administrator." : pickingSummaryText(header))}</div>
            </div>
            <div class="warehouse-receiving-actions">
              <button type="button" class="warehouse-receiving-button" data-warehouse-picking-back>Back to outbound picking</button>
              <button type="button" class="warehouse-receiving-button" data-warehouse-picking-refresh>Refresh</button>
            </div>
          </div>
          ${unavailable ? `<div class="warehouse-console-state-detail" data-warehouse-picking-empty>${escapeHtml(statePayload.title || "Picking review unavailable")}</div>` : `
            <div class="warehouse-receiving-note">${escapeHtml(header.age_label || "")} · ${escapeHtml(header.remaining_summary || "")}</div>
            <div class="warehouse-receiving-cards">${cards.map(renderPickingCard).join("")}</div>
          `}
        </section>
        <section class="warehouse-receiving-detail">
          <div class="warehouse-receiving-tabs">
            ${tabs.map((tab) => `<button type="button" class="warehouse-receiving-tab" data-warehouse-picking-tab="${escapeHtml(tab.key || "")}">${escapeHtml(tab.label || "")} ${escapeHtml(tab.count == null ? "" : `(${tab.count})`)}</button>`).join("")}
          </div>
          <div class="warehouse-receiving-panel is-active" data-warehouse-picking-panel="item_lines">
            ${lines.length ? lines.map(renderPickingLine).join("") : `<div class="warehouse-receiving-line" data-warehouse-picking-empty><span class="warehouse-receiving-meta">No item lines visible for this order.</span></div>`}
          </div>
          <div class="warehouse-receiving-panel" data-warehouse-picking-panel="stock_readiness">
            ${lines.length ? lines.map(renderPickingReadinessRow).join("") : `<div class="warehouse-receiving-history-row" data-warehouse-picking-empty><span class="warehouse-receiving-meta">No stock readiness visible for this order.</span></div>`}
          </div>
        </section>
      </div>
    `);
    $root.find("[data-warehouse-picking-back]").on("click", (event) => {
      event.preventDefault();
      frappe.set_route(WORKLIST_PAGE_KEY, "outbound-picking");
    });
    $root.find("[data-warehouse-picking-refresh]").on("click", (event) => {
      event.preventDefault();
      loadPickingReview(viewState, viewState.salesOrder);
    });
    $root.find("[data-warehouse-picking-tab]").on("click", function (event) {
      event.preventDefault();
      activatePickingTab($root, String(this.getAttribute("data-warehouse-picking-tab") || "item_lines"));
    });
    activatePickingTab($root, "item_lines");
    removeDuplicateWarehouseHosts(viewState.$host.get(0));
    viewState.$host.empty().append($root);
  }

  function renderPickingLoading(viewState) {
    renderPickingReviewPayload(viewState, {
      state: { kind: "loading", title: "Checking picking work", detail: "Checking picking work..." },
      header: { sales_order: viewState.salesOrder || "" },
      summary_cards: [],
      tabs: [
        { key: "item_lines", label: "Item Lines", count: 0 },
        { key: "stock_readiness", label: "Stock Readiness", count: 0 },
      ],
      lines: [],
    });
  }

  function loadPickingReview(viewState, salesOrder) {
    markWarehouseDiagnostic("pickingServiceCallAttempted");
    viewState.salesOrder = salesOrder || pickingSalesOrderFromRoute();
    renderPickingLoading(viewState);
    return frappe.call({
      method: PICKING_METHOD,
      args: { sales_order: viewState.salesOrder },
    }).then((response) => {
      renderPickingReviewPayload(viewState, response && response.message ? response.message : {});
    }).catch(() => {
      renderPickingReviewPayload(viewState, {
        state: { kind: "error", title: "Picking review unavailable", detail: "Picking work could not be loaded. Refresh or contact an administrator." },
        header: { sales_order: viewState.salesOrder || "" },
        summary_cards: [],
        tabs: [
          { key: "item_lines", label: "Item Lines", count: 0 },
          { key: "stock_readiness", label: "Stock Readiness", count: 0 },
        ],
        lines: [],
      });
    });
  }

  function renderPickingReview(wrapper, salesOrder) {
    markWarehouseDiagnostic("renderPickingReviewEntered");
    const viewState = makePickingPage(wrapper);
    if (window.erpWorkspaceConsoleSidebar && typeof window.erpWorkspaceConsoleSidebar.refresh === "function") {
      window.erpWorkspaceConsoleSidebar.refresh();
    }
    loadPickingReview(viewState, salesOrder || pickingSalesOrderFromRoute());
  }

  function makeStockExceptionPage(wrapper) {
    const existing = wrapper && wrapper.__erpwWarehouseStockExceptionReview;
    if (existing && existing.page && existing.$host && document.documentElement.contains(existing.$host.get(0))) {
      return existing;
    }
    const page = frappe.ui.make_app_page({
      parent: wrapper,
      title: "Stock Exception Review",
      single_column: true,
    });
    const $parent = page && page.body ? $(page.body) : $(wrapper);
    const $host = $('<section class="warehouse-stock-exception-route"></section>');
    $parent.empty().append($host);
    const state = { page, $host, contextToken: "" };
    wrapper.__erpwWarehouseStockExceptionReview = state;
    return state;
  }

  function stockExceptionSummaryText(header) {
    const parts = [header.sales_order, header.item_code, header.source_warehouse].filter(Boolean);
    return parts.join(" · ");
  }

  function renderStockExceptionReviewCard(card) {
    return `
      <div class="warehouse-receiving-card" data-warehouse-stock-exception-review-card="${escapeHtml(card.key || "")}">
        <div class="warehouse-receiving-card-label">${escapeHtml(card.label || "")}</div>
        <div class="warehouse-receiving-card-value">${escapeHtml(card.value == null ? "--" : card.value)}</div>
        <div class="warehouse-receiving-card-note">${escapeHtml(card.note || "")}</div>
      </div>
    `;
  }

  function renderStockExceptionPanel(panel, panelKey) {
    const items = Array.isArray(panel.items) ? panel.items : [];
    const target = panel.route_target || {};
    const postureToken = target.route === STOCK_POSTURE_PAGE_KEY ? String(target.context_token || "") : "";
    return `
      <section class="warehouse-stock-exception-review-panel" data-warehouse-stock-exception-${escapeHtml(panelKey)}-panel>
        <div class="warehouse-inbound-group-head">
          <h2 class="warehouse-inbound-group-title">${escapeHtml(panel.title || "")}</h2>
          <div class="warehouse-inbound-group-note">${escapeHtml(panel.summary || "")}</div>
        </div>
        <div class="warehouse-stock-exception-review-facts">
          ${items.length ? items.map((item) => `
            <div class="warehouse-stock-exception-review-fact" data-warehouse-stock-exception-review-fact>
              <span>${escapeHtml(item.label || "")}</span>
              <strong>${escapeHtml(item.value == null ? "" : item.value)}</strong>
            </div>
          `).join("") : `<div class="warehouse-receiving-meta" data-warehouse-stock-exception-review-empty>No details visible for this section.</div>`}
        </div>
        ${postureToken ? `<button type="button" class="warehouse-receiving-button" data-warehouse-stock-exception-open-posture data-warehouse-stock-exception-posture-token="${escapeHtml(postureToken)}">Review stock posture</button>` : ""}
      </section>
    `;
  }

  function renderNextReviewPanel(panel) {
    const items = Array.isArray(panel.items) ? panel.items : [];
    return `
      <section class="warehouse-stock-exception-review-panel" data-warehouse-stock-exception-next-panel>
        <div class="warehouse-inbound-group-head">
          <h2 class="warehouse-inbound-group-title">${escapeHtml(panel.title || "Recommended Review")}</h2>
          <div class="warehouse-inbound-group-note">${escapeHtml(panel.summary || "")}</div>
        </div>
        <div class="warehouse-stock-exception-next-grid">
          ${items.length ? items.map((item) => {
            const target = item.target || {};
            const targetKind = target.context_token && target.route === STOCK_POSTURE_PAGE_KEY ? "stock_posture" : target.purchase_order ? "receiving" : target.sales_order ? "picking" : "stock";
            return `
              <button type="button" class="warehouse-stock-exception-next-card" data-warehouse-stock-exception-next-target="${escapeHtml(targetKind)}" data-warehouse-stock-exception-next-sales-order="${escapeHtml(target.sales_order || "")}" data-warehouse-stock-exception-next-purchase-order="${escapeHtml(target.purchase_order || "")}" data-warehouse-stock-exception-next-token="${escapeHtml(target.context_token || "")}">
                <span>${escapeHtml(item.label || "")}</span>
                <strong>${escapeHtml(item.value || "")}</strong>
              </button>
            `;
          }).join("") : `<div class="warehouse-receiving-meta" data-warehouse-stock-exception-review-empty>No review path visible.</div>`}
        </div>
      </section>
    `;
  }

  function renderStockExceptionRelatedRow(row) {
    const target = row.route_target || {};
    const targetKind = target.purchase_order ? "receiving" : target.sales_order ? "picking" : "";
    return `
      <button type="button" class="warehouse-receiving-history-row" data-warehouse-stock-exception-related-row="${escapeHtml(row.key || "")}" data-warehouse-stock-exception-related-target="${escapeHtml(targetKind)}" data-warehouse-stock-exception-related-sales-order="${escapeHtml(target.sales_order || "")}" data-warehouse-stock-exception-related-purchase-order="${escapeHtml(target.purchase_order || "")}">
        <div>
          <div class="warehouse-receiving-strong">${escapeHtml(row.title || "")}</div>
          <div class="warehouse-receiving-meta">${escapeHtml(row.label || "")}</div>
        </div>
        <div class="warehouse-receiving-meta">${escapeHtml(row.detail || "")}</div>
      </button>
    `;
  }

  function routeStockExceptionTarget(kind, salesOrder, purchaseOrder, contextToken) {
    if (kind === "stock_posture" && contextToken) {
      frappe.set_route(STOCK_POSTURE_PAGE_KEY, contextToken);
      return;
    }
    if (kind === "picking" && salesOrder) {
      frappe.set_route(PICKING_PAGE_KEY, salesOrder);
      return;
    }
    if (kind === "receiving" && purchaseOrder) {
      frappe.set_route(RECEIVING_PAGE_KEY, purchaseOrder);
      return;
    }
    frappe.set_route(WORKLIST_PAGE_KEY, "stock-exceptions");
  }

  function renderStockExceptionReviewPayload(viewState, payload) {
    ensureStyle();
    const header = payload.header || {};
    const cards = Array.isArray(payload.summary_cards) ? payload.summary_cards : [];
    const panels = payload.panels || {};
    const relatedRows = Array.isArray(payload.related_rows) ? payload.related_rows : [];
    const statePayload = payload.state || {};
    const unavailable = ["restricted", "error", "unavailable"].includes(String(statePayload.kind || ""));
    const $root = $(`
      <div class="sales-console-shell warehouse-receiving-shell warehouse-stock-exception-review-shell" data-erpw-workspace="warehouse" data-warehouse-view="stock-exception-review" data-erpw-console-runtime="ready" data-warehouse-stock-exception-review-shell="true" data-warehouse-stock-exception-token="${escapeHtml(header.context_token || viewState.contextToken || "")}">
        <section class="warehouse-receiving-header">
          <div class="warehouse-receiving-head">
            <div>
              <h1 class="warehouse-receiving-title">Stock Exception Review</h1>
              <div class="warehouse-receiving-subtitle">${escapeHtml(unavailable ? statePayload.detail || "Stock exception review could not be loaded. Refresh or contact an administrator." : stockExceptionSummaryText(header))}</div>
            </div>
            <div class="warehouse-receiving-actions">
              <button type="button" class="warehouse-receiving-button" data-warehouse-stock-exception-back>Back to stock exceptions</button>
              <button type="button" class="warehouse-receiving-button" data-warehouse-stock-exception-refresh>Refresh</button>
            </div>
          </div>
          ${unavailable ? `<div class="warehouse-console-state-detail" data-warehouse-stock-exception-review-empty>${escapeHtml(statePayload.title || "Stock exception review unavailable")}</div>` : `
            <div class="warehouse-receiving-note"><span class="warehouse-inbound-badge">${escapeHtml(header.exception_label || "")}</span> ${escapeHtml(header.urgency_label || "")} · ${escapeHtml(header.explanation || "")}</div>
            <div class="warehouse-receiving-cards">${cards.map(renderStockExceptionReviewCard).join("")}</div>
          `}
        </section>
        <section class="warehouse-stock-exception-review-grid">
          ${renderStockExceptionPanel(panels.demand || {}, "demand")}
          ${renderStockExceptionPanel(panels.stock || {}, "stock")}
          ${renderStockExceptionPanel(panels.inbound || {}, "inbound")}
          ${renderNextReviewPanel(panels.next_reviews || {})}
        </section>
        <section class="warehouse-receiving-detail" data-warehouse-stock-exception-related-panel>
          <div class="warehouse-inbound-group-head">
            <h2 class="warehouse-inbound-group-title">Related Reviews</h2>
            <div class="warehouse-inbound-group-note">Custom Warehouse review paths for this exception.</div>
          </div>
          <div class="warehouse-receiving-panel is-active">
            ${relatedRows.length ? relatedRows.map(renderStockExceptionRelatedRow).join("") : `<div class="warehouse-receiving-history-row" data-warehouse-stock-exception-review-empty><span class="warehouse-receiving-meta">No related review path visible.</span></div>`}
          </div>
        </section>
      </div>
    `);
    $root.find("[data-warehouse-stock-exception-back]").on("click", (event) => {
      event.preventDefault();
      frappe.set_route(WORKLIST_PAGE_KEY, "stock-exceptions");
    });
    $root.find("[data-warehouse-stock-exception-refresh]").on("click", (event) => {
      event.preventDefault();
      loadStockExceptionReview(viewState, viewState.contextToken);
    });
    $root.find("[data-warehouse-stock-exception-next-target]").on("click", function (event) {
      event.preventDefault();
      routeStockExceptionTarget(
        String(this.getAttribute("data-warehouse-stock-exception-next-target") || ""),
        String(this.getAttribute("data-warehouse-stock-exception-next-sales-order") || ""),
        String(this.getAttribute("data-warehouse-stock-exception-next-purchase-order") || ""),
        String(this.getAttribute("data-warehouse-stock-exception-next-token") || "")
      );
    });
    $root.find("[data-warehouse-stock-exception-related-target]").on("click", function (event) {
      event.preventDefault();
      routeStockExceptionTarget(
        String(this.getAttribute("data-warehouse-stock-exception-related-target") || ""),
        String(this.getAttribute("data-warehouse-stock-exception-related-sales-order") || ""),
        String(this.getAttribute("data-warehouse-stock-exception-related-purchase-order") || ""),
        ""
      );
    });
    $root.find("[data-warehouse-stock-exception-open-posture]").on("click", function (event) {
      event.preventDefault();
      const token = String(this.getAttribute("data-warehouse-stock-exception-posture-token") || "");
      if (token) frappe.set_route(STOCK_POSTURE_PAGE_KEY, token);
    });
    removeDuplicateWarehouseHosts(viewState.$host.get(0));
    viewState.$host.empty().append($root);
  }

  function renderStockExceptionReviewLoading(viewState) {
    renderStockExceptionReviewPayload(viewState, {
      state: { kind: "loading", title: "Checking stock exception", detail: "Checking stock exception..." },
      header: { context_token: viewState.contextToken || "" },
      summary_cards: [],
      panels: {
        demand: { title: "Demand at Risk", items: [] },
        stock: { title: "Stock Posture", items: [] },
        inbound: { title: "Inbound Cover", items: [] },
        next_reviews: { title: "Recommended Review", items: [] },
      },
      related_rows: [],
    });
  }

  function loadStockExceptionReview(viewState, contextToken) {
    markWarehouseDiagnostic("stockExceptionReviewServiceCallAttempted");
    viewState.contextToken = contextToken || stockExceptionTokenFromRoute();
    renderStockExceptionReviewLoading(viewState);
    return frappe.call({
      method: STOCK_EXCEPTION_REVIEW_METHOD,
      args: { context_token: viewState.contextToken },
    }).then((response) => {
      renderStockExceptionReviewPayload(viewState, response && response.message ? response.message : {});
    }).catch(() => {
      renderStockExceptionReviewPayload(viewState, {
        state: { kind: "error", title: "Stock exception review unavailable", detail: "Stock exception review could not be loaded. Refresh or contact an administrator." },
        header: { context_token: viewState.contextToken || "" },
        summary_cards: [],
        panels: {
          demand: { title: "Demand at Risk", items: [] },
          stock: { title: "Stock Posture", items: [] },
          inbound: { title: "Inbound Cover", items: [] },
          next_reviews: { title: "Recommended Review", items: [] },
        },
        related_rows: [],
      });
    });
  }

  function renderStockExceptionReview(wrapper, contextToken) {
    markWarehouseDiagnostic("renderStockExceptionReviewEntered");
    const viewState = makeStockExceptionPage(wrapper);
    if (window.erpWorkspaceConsoleSidebar && typeof window.erpWorkspaceConsoleSidebar.refresh === "function") {
      window.erpWorkspaceConsoleSidebar.refresh();
    }
    loadStockExceptionReview(viewState, contextToken || stockExceptionTokenFromRoute());
  }

  function makeStockPosturePage(wrapper) {
    const existing = wrapper && wrapper.__erpwWarehouseStockPostureReview;
    if (existing && existing.page && existing.$host && document.documentElement.contains(existing.$host.get(0))) {
      return existing;
    }
    const page = frappe.ui.make_app_page({
      parent: wrapper,
      title: "Stock Posture Review",
      single_column: true,
    });
    const $parent = page && page.body ? $(page.body) : $(wrapper);
    const $host = $('<section class="warehouse-stock-posture-route"></section>');
    $parent.empty().append($host);
    const state = { page, $host, contextToken: "" };
    wrapper.__erpwWarehouseStockPostureReview = state;
    return state;
  }

  function stockPostureSummaryText(header) {
    const parts = [header.item_code, header.item_name, header.warehouse].filter(Boolean);
    return parts.join(" - ");
  }

  function renderStockPostureCard(card) {
    return `
      <div class="warehouse-receiving-card" data-warehouse-stock-posture-card="${escapeHtml(card.key || "")}">
        <div class="warehouse-receiving-card-label">${escapeHtml(card.label || "")}</div>
        <div class="warehouse-receiving-card-value">${escapeHtml(card.value == null ? "--" : card.value)}</div>
        <div class="warehouse-receiving-card-note">${escapeHtml(card.note || "")}</div>
      </div>
    `;
  }

  function renderStockPosturePanel(panel, panelKey) {
    const items = Array.isArray(panel.items) ? panel.items : [];
    return `
      <section class="warehouse-stock-exception-review-panel" data-warehouse-stock-posture-panel="${escapeHtml(panelKey)}">
        <div class="warehouse-inbound-group-head">
          <h2 class="warehouse-inbound-group-title">${escapeHtml(panel.title || "")}</h2>
          <div class="warehouse-inbound-group-note">${escapeHtml(panel.summary || "")}</div>
        </div>
        <div class="warehouse-stock-exception-review-facts">
          ${items.length ? items.map((item) => `
            <div class="warehouse-stock-exception-review-fact" data-warehouse-stock-posture-fact>
              <span>${escapeHtml(item.label || "")}</span>
              <strong>${escapeHtml(item.value == null ? "" : item.value)}</strong>
            </div>
          `).join("") : `<div class="warehouse-receiving-meta" data-warehouse-stock-posture-empty>No details visible for this section.</div>`}
        </div>
      </section>
    `;
  }

  function stockPostureRouteKind(target) {
    const route = String((target && target.route) || "");
    if (route === PICKING_PAGE_KEY) return "picking";
    if (route === RECEIVING_PAGE_KEY) return "receiving";
    if (route === STOCK_EXCEPTION_PAGE_KEY) return "stock_exception";
    return "";
  }

  function renderStockPostureRelatedRow(row) {
    const target = row.route_target || {};
    const targetKind = stockPostureRouteKind(target);
    return `
      <button type="button" class="warehouse-receiving-history-row" data-warehouse-stock-posture-related-row="${escapeHtml(row.key || "")}" data-warehouse-stock-posture-related-target="${escapeHtml(targetKind)}" data-warehouse-stock-posture-related-sales-order="${escapeHtml(target.sales_order || "")}" data-warehouse-stock-posture-related-purchase-order="${escapeHtml(target.purchase_order || "")}" data-warehouse-stock-posture-related-token="${escapeHtml(target.context_token || "")}" ${targetKind ? `data-warehouse-stock-posture-route-${escapeHtml(targetKind.replace("_", "-"))}` : ""}>
        <div>
          <div class="warehouse-receiving-strong">${escapeHtml(row.title || "")}</div>
          <div class="warehouse-receiving-meta">${escapeHtml(row.label || "")}</div>
        </div>
        <div class="warehouse-receiving-meta">${escapeHtml(row.detail || "")}</div>
      </button>
    `;
  }

  function renderStockPostureDataRow(row, rowKind) {
    const target = row.route_target || {};
    const targetKind = stockPostureRouteKind(target);
    const title = row.sales_order || row.purchase_order || row.item_code || "";
    const dateText = row.required_date || row.expected_date || "";
    const qtyText = row.pending_qty ? `${row.pending_qty} ${row.uom || ""}` : row.expected_qty ? `${row.expected_qty} ${row.uom || ""}` : "";
    return `
      <button type="button" class="warehouse-receiving-history-row" data-warehouse-stock-posture-row="${escapeHtml(rowKind)}" data-warehouse-stock-posture-related-target="${escapeHtml(targetKind)}" data-warehouse-stock-posture-related-sales-order="${escapeHtml(target.sales_order || "")}" data-warehouse-stock-posture-related-purchase-order="${escapeHtml(target.purchase_order || "")}" data-warehouse-stock-posture-related-token="${escapeHtml(target.context_token || "")}" ${targetKind ? `data-warehouse-stock-posture-route-${escapeHtml(targetKind.replace("_", "-"))}` : ""}>
        <div>
          <div class="warehouse-receiving-strong">${escapeHtml(title)}</div>
          <div class="warehouse-receiving-meta">${escapeHtml(row.customer || row.supplier || row.status || "")}</div>
        </div>
        <div class="warehouse-receiving-meta">${escapeHtml([qtyText.trim(), dateText].filter(Boolean).join(" - "))}</div>
      </button>
    `;
  }

  function routeStockPostureTarget(target) {
    const route = String((target && target.route) || "");
    if (route === PICKING_PAGE_KEY && target.sales_order) {
      frappe.set_route(PICKING_PAGE_KEY, target.sales_order);
      return;
    }
    if (route === RECEIVING_PAGE_KEY && target.purchase_order) {
      frappe.set_route(RECEIVING_PAGE_KEY, target.purchase_order);
      return;
    }
    if (route === STOCK_EXCEPTION_PAGE_KEY && target.context_token) {
      frappe.set_route(STOCK_EXCEPTION_PAGE_KEY, target.context_token);
      return;
    }
    frappe.set_route(WORKLIST_PAGE_KEY, "stock-exceptions");
  }

  function routeStockPostureElement(element) {
    routeStockPostureTarget({
      route: String(element.getAttribute("data-warehouse-stock-posture-related-target") || "") === "picking" ? PICKING_PAGE_KEY
        : String(element.getAttribute("data-warehouse-stock-posture-related-target") || "") === "receiving" ? RECEIVING_PAGE_KEY
          : String(element.getAttribute("data-warehouse-stock-posture-related-target") || "") === "stock_exception" ? STOCK_EXCEPTION_PAGE_KEY
            : "",
      sales_order: String(element.getAttribute("data-warehouse-stock-posture-related-sales-order") || ""),
      purchase_order: String(element.getAttribute("data-warehouse-stock-posture-related-purchase-order") || ""),
      context_token: String(element.getAttribute("data-warehouse-stock-posture-related-token") || ""),
    });
  }

  function renderStockPostureReviewPayload(viewState, payload) {
    ensureStyle();
    const header = payload.header || {};
    const cards = Array.isArray(payload.summary_cards) ? payload.summary_cards : [];
    const panels = payload.panels || {};
    const inboundRows = Array.isArray(payload.inbound_rows) ? payload.inbound_rows : [];
    const outboundRows = Array.isArray(payload.outbound_rows) ? payload.outbound_rows : [];
    const relatedRows = Array.isArray(payload.related_rows) ? payload.related_rows : [];
    const statePayload = payload.state || {};
    const actionTargets = payload.action_targets || {};
    const backTarget = actionTargets.back || {};
    const unavailable = ["restricted", "error", "unavailable"].includes(String(statePayload.kind || ""));
    const $root = $(`
      <div class="sales-console-shell warehouse-receiving-shell warehouse-stock-posture-shell" data-erpw-workspace="warehouse" data-warehouse-view="stock-posture-review" data-erpw-console-runtime="ready" data-warehouse-stock-posture-shell="true" data-warehouse-stock-posture-token="${escapeHtml(header.context_token || viewState.contextToken || "")}">
        <section class="warehouse-receiving-header">
          <div class="warehouse-receiving-head">
            <div>
              <h1 class="warehouse-receiving-title">Stock Posture Review</h1>
              <div class="warehouse-receiving-subtitle">${escapeHtml(unavailable ? statePayload.detail || "Stock posture review could not be loaded. Refresh or contact an administrator." : stockPostureSummaryText(header))}</div>
            </div>
            <div class="warehouse-receiving-actions">
              <button type="button" class="warehouse-receiving-button" data-warehouse-stock-posture-back data-warehouse-stock-posture-back-route="${escapeHtml(backTarget.route || "")}" data-warehouse-stock-posture-back-sales-order="${escapeHtml(backTarget.sales_order || "")}" data-warehouse-stock-posture-back-purchase-order="${escapeHtml(backTarget.purchase_order || "")}" data-warehouse-stock-posture-back-token="${escapeHtml(backTarget.context_token || "")}">Back</button>
              <button type="button" class="warehouse-receiving-button" data-warehouse-stock-posture-refresh>Refresh</button>
            </div>
          </div>
          ${unavailable ? `<div class="warehouse-console-state-detail" data-warehouse-stock-posture-empty>${escapeHtml(statePayload.title || "Stock posture review unavailable")}</div>` : `
            <div class="warehouse-receiving-note"><span class="warehouse-inbound-badge">${escapeHtml(header.posture_label || "")}</span> ${escapeHtml(header.explanation || "")}</div>
            <div class="warehouse-receiving-cards">${cards.map(renderStockPostureCard).join("")}</div>
          `}
        </section>
        <section class="warehouse-stock-exception-review-grid">
          ${renderStockPosturePanel(panels.stock || {}, "stock")}
          ${renderStockPosturePanel(panels.inbound || {}, "inbound")}
          ${renderStockPosturePanel(panels.outbound || {}, "outbound")}
          ${renderStockPosturePanel(panels.related || {}, "related")}
        </section>
        <section class="warehouse-receiving-detail" data-warehouse-stock-posture-demand-panel>
          <div class="warehouse-inbound-group-head">
            <h2 class="warehouse-inbound-group-title">Open Demand</h2>
            <div class="warehouse-inbound-group-note">Submitted sales orders connected to this stock posture.</div>
          </div>
          <div class="warehouse-receiving-panel is-active">
            ${outboundRows.length ? outboundRows.map((row) => renderStockPostureDataRow(row, "outbound")).join("") : `<div class="warehouse-receiving-history-row" data-warehouse-stock-posture-empty><span class="warehouse-receiving-meta">No open outbound demand visible.</span></div>`}
          </div>
        </section>
        <section class="warehouse-receiving-detail" data-warehouse-stock-posture-inbound-panel>
          <div class="warehouse-inbound-group-head">
            <h2 class="warehouse-inbound-group-title">Inbound Cover</h2>
            <div class="warehouse-inbound-group-note">Submitted purchase orders expected for this stock posture.</div>
          </div>
          <div class="warehouse-receiving-panel is-active">
            ${inboundRows.length ? inboundRows.map((row) => renderStockPostureDataRow(row, "inbound")).join("") : `<div class="warehouse-receiving-history-row" data-warehouse-stock-posture-empty><span class="warehouse-receiving-meta">No inbound cover visible.</span></div>`}
          </div>
        </section>
        <section class="warehouse-receiving-detail" data-warehouse-stock-posture-related-panel>
          <div class="warehouse-inbound-group-head">
            <h2 class="warehouse-inbound-group-title">Related Reviews</h2>
            <div class="warehouse-inbound-group-note">Custom Warehouse review paths for this item and warehouse.</div>
          </div>
          <div class="warehouse-receiving-panel is-active">
            ${relatedRows.length ? relatedRows.map(renderStockPostureRelatedRow).join("") : `<div class="warehouse-receiving-history-row" data-warehouse-stock-posture-empty><span class="warehouse-receiving-meta">No related review path visible.</span></div>`}
          </div>
        </section>
      </div>
    `);
    $root.find("[data-warehouse-stock-posture-back]").on("click", function (event) {
      event.preventDefault();
      routeStockPostureTarget({
        route: String(this.getAttribute("data-warehouse-stock-posture-back-route") || ""),
        sales_order: String(this.getAttribute("data-warehouse-stock-posture-back-sales-order") || ""),
        purchase_order: String(this.getAttribute("data-warehouse-stock-posture-back-purchase-order") || ""),
        context_token: String(this.getAttribute("data-warehouse-stock-posture-back-token") || ""),
      });
    });
    $root.find("[data-warehouse-stock-posture-refresh]").on("click", (event) => {
      event.preventDefault();
      loadStockPostureReview(viewState, viewState.contextToken);
    });
    $root.find("[data-warehouse-stock-posture-related-target]").on("click", function (event) {
      event.preventDefault();
      routeStockPostureElement(this);
    });
    removeDuplicateWarehouseHosts(viewState.$host.get(0));
    viewState.$host.empty().append($root);
  }

  function renderStockPostureReviewLoading(viewState) {
    renderStockPostureReviewPayload(viewState, {
      state: { kind: "loading", title: "Checking stock posture", detail: "Checking stock posture..." },
      header: { context_token: viewState.contextToken || "" },
      summary_cards: [],
      panels: {
        stock: { title: "Stock Posture", items: [] },
        inbound: { title: "Inbound Cover", items: [] },
        outbound: { title: "Open Demand", items: [] },
        related: { title: "Related Reviews", items: [] },
      },
      inbound_rows: [],
      outbound_rows: [],
      related_rows: [],
    });
  }

  function loadStockPostureReview(viewState, contextToken) {
    markWarehouseDiagnostic("stockPostureReviewServiceCallAttempted");
    viewState.contextToken = contextToken || stockPostureTokenFromRoute();
    renderStockPostureReviewLoading(viewState);
    return frappe.call({
      method: STOCK_POSTURE_REVIEW_METHOD,
      args: { context_token: viewState.contextToken },
    }).then((response) => {
      renderStockPostureReviewPayload(viewState, response && response.message ? response.message : {});
    }).catch(() => {
      renderStockPostureReviewPayload(viewState, {
        state: { kind: "error", title: "Stock posture review unavailable", detail: "Stock posture review could not be loaded. Refresh or contact an administrator." },
        header: { context_token: viewState.contextToken || "" },
        summary_cards: [],
        panels: {
          stock: { title: "Stock Posture", items: [] },
          inbound: { title: "Inbound Cover", items: [] },
          outbound: { title: "Open Demand", items: [] },
          related: { title: "Related Reviews", items: [] },
        },
        inbound_rows: [],
        outbound_rows: [],
        related_rows: [],
      });
    });
  }

  function renderStockPostureReview(wrapper, contextToken) {
    markWarehouseDiagnostic("renderStockPostureReviewEntered");
    const viewState = makeStockPosturePage(wrapper);
    if (window.erpWorkspaceConsoleSidebar && typeof window.erpWorkspaceConsoleSidebar.refresh === "function") {
      window.erpWorkspaceConsoleSidebar.refresh();
    }
    loadStockPostureReview(viewState, contextToken || stockPostureTokenFromRoute());
  }

  function makeMovementPage(wrapper) {
    const existing = wrapper && wrapper.__erpwWarehouseMovementReview;
    if (existing && existing.page && existing.$host && document.documentElement.contains(existing.$host.get(0))) {
      return existing;
    }
    const page = frappe.ui.make_app_page({
      parent: wrapper,
      title: "Movement Review",
      single_column: true,
    });
    const $parent = page && page.body ? $(page.body) : $(wrapper);
    const $host = $('<section class="warehouse-movement-review-route"></section>');
    $parent.empty().append($host);
    const state = { page, $host, contextToken: "" };
    wrapper.__erpwWarehouseMovementReview = state;
    return state;
  }

  function movementSummaryText(header) {
    const parts = [header.movement_id, header.purpose || header.movement_type, header.direction_label].filter(Boolean);
    return parts.join(" - ");
  }

  function renderMovementReviewCard(card) {
    return `
      <div class="warehouse-receiving-card" data-warehouse-movement-review-card="${escapeHtml(card.key || "")}">
        <div class="warehouse-receiving-card-label">${escapeHtml(card.label || "")}</div>
        <div class="warehouse-receiving-card-value">${escapeHtml(card.value == null ? "--" : card.value)}</div>
        <div class="warehouse-receiving-card-note">${escapeHtml(card.note || "")}</div>
      </div>
    `;
  }

  function renderMovementReviewPanel(panel, panelKey) {
    const items = Array.isArray(panel.items) ? panel.items : [];
    return `
      <section class="warehouse-stock-exception-panel" data-warehouse-movement-review-panel="${escapeHtml(panelKey || "")}">
        <div class="warehouse-stock-exception-panel-title">${escapeHtml(panel.title || "")}</div>
        <div class="warehouse-inbound-meta">${escapeHtml(panel.summary || "")}</div>
        <div class="warehouse-stock-exception-panel-items">
          ${items.length ? items.map((item) => `
            <div class="warehouse-stock-exception-panel-item">
              <span>${escapeHtml(item.label || "")}</span>
              <strong>${escapeHtml(item.value || "")}</strong>
            </div>
          `).join("") : `<div class="warehouse-inbound-meta" data-warehouse-movement-review-empty>No related posture visible.</div>`}
        </div>
      </section>
    `;
  }

  function renderMovementReviewLine(line) {
    const target = line.stock_posture_route || {};
    const token = target.route === STOCK_POSTURE_PAGE_KEY ? String(target.context_token || "") : "";
    const postureButton = token
      ? `<button type="button" class="warehouse-receiving-button" data-warehouse-movement-review-route-stock-posture data-warehouse-stock-posture-token="${escapeHtml(token)}">Review stock posture</button>`
      : "";
    return `
      <div class="warehouse-receiving-line" data-warehouse-movement-review-line="${escapeHtml(line.item_code || "")}">
        <div>
          <div class="warehouse-receiving-strong">${escapeHtml(line.item_code || "")}</div>
          <div class="warehouse-receiving-meta">${escapeHtml(line.item_name || "")}</div>
        </div>
        <div class="warehouse-receiving-meta">${escapeHtml(line.quantity || "0")} ${escapeHtml(line.stock_uom || "")}</div>
        <div class="warehouse-receiving-meta">${escapeHtml(line.direction_label || "")}</div>
        <div class="warehouse-receiving-meta">${escapeHtml(line.line_note || "")}</div>
        <div class="warehouse-receiving-actions">${postureButton}</div>
      </div>
    `;
  }

  function renderMovementReviewLineGroup(group) {
    const rows = Array.isArray(group.rows) ? group.rows : [];
    return `
      <section class="warehouse-receiving-detail" data-warehouse-movement-review-line-group="${escapeHtml(group.key || "")}">
        <div class="warehouse-inbound-group-head">
          <h2 class="warehouse-inbound-group-title">${escapeHtml(group.title || "Movement Lines")}</h2>
          <div class="warehouse-inbound-group-note">${escapeHtml(rows.length ? `${rows.length} lines` : group.summary || "")}</div>
        </div>
        <div class="warehouse-receiving-panel is-active">
          ${rows.length ? rows.map(renderMovementReviewLine).join("") : `<div class="warehouse-receiving-history-row" data-warehouse-movement-review-empty><span class="warehouse-receiving-meta">No movement lines visible.</span></div>`}
        </div>
      </section>
    `;
  }

  function renderMovementRelatedRow(row) {
    const target = row.route_target || {};
    const token = target.route === STOCK_POSTURE_PAGE_KEY ? String(target.context_token || "") : "";
    return `
      <button type="button" class="warehouse-receiving-history-row" data-warehouse-movement-review-related-row="${escapeHtml(row.key || "")}" data-warehouse-movement-review-route-stock-posture="${escapeHtml(token)}">
        <div>
          <div class="warehouse-receiving-strong">${escapeHtml(row.title || "")}</div>
          <div class="warehouse-receiving-meta">${escapeHtml(row.label || "")}</div>
        </div>
        <div class="warehouse-receiving-meta">${escapeHtml(row.detail || "")}</div>
      </button>
    `;
  }

  function routeMovementBack(target) {
    const route = String((target && target.route) || "");
    const queueKey = normalizeQueueKey((target && target.queue_key) || "");
    if (route === WORKLIST_PAGE_KEY && queueKey === TRANSFER_VISIBILITY_KEY) {
      frappe.set_route(WORKLIST_PAGE_KEY, "transfer-visibility");
      return;
    }
    if (route === WORKLIST_PAGE_KEY && queueKey === MOVEMENT_VISIBILITY_KEY) {
      frappe.set_route(WORKLIST_PAGE_KEY, "movement-visibility");
      return;
    }
    frappe.set_route(WORKLIST_PAGE_KEY, "movement-visibility");
  }

  function renderMovementReviewPayload(viewState, payload) {
    ensureStyle();
    const header = payload.header || {};
    const cards = Array.isArray(payload.summary_cards) ? payload.summary_cards : [];
    const panels = payload.panels || {};
    const lineGroups = Array.isArray(payload.line_groups) ? payload.line_groups : [];
    const relatedRoutes = Array.isArray(payload.related_routes) ? payload.related_routes : [];
    const statePayload = payload.state || {};
    const actionTargets = payload.action_targets || {};
    const backTarget = actionTargets.back || {};
    const backQueueKey = normalizeQueueKey(backTarget.queue_key || "");
    const backLabel = backQueueKey === TRANSFER_VISIBILITY_KEY ? "Back to transfer visibility" : "Back to movement visibility";
    const unavailable = ["restricted", "error", "unavailable"].includes(String(statePayload.kind || ""));
    const $root = $(`
      <div class="sales-console-shell warehouse-receiving-shell warehouse-movement-review-shell" data-erpw-workspace="warehouse" data-warehouse-view="movement-review" data-erpw-console-runtime="ready" data-warehouse-movement-review-shell="true" data-warehouse-movement-review-token="${escapeHtml(header.context_token || viewState.contextToken || "")}">
        <section class="warehouse-receiving-header">
          <div class="warehouse-receiving-head">
            <div>
              <h1 class="warehouse-receiving-title">Movement Review</h1>
              <div class="warehouse-receiving-subtitle">${escapeHtml(unavailable ? statePayload.detail || "Movement review could not be loaded. Refresh or contact an administrator." : movementSummaryText(header))}</div>
            </div>
            <div class="warehouse-receiving-actions">
              <button type="button" class="warehouse-receiving-button" data-warehouse-movement-review-back data-warehouse-movement-review-back-route="${escapeHtml(backTarget.route || "")}" data-warehouse-movement-review-back-queue="${escapeHtml(backTarget.queue_key || "")}">${escapeHtml(backLabel)}</button>
              <button type="button" class="warehouse-receiving-button" data-warehouse-movement-review-refresh>Refresh</button>
            </div>
          </div>
          ${unavailable ? `<div class="warehouse-console-state-detail" data-warehouse-movement-review-empty>${escapeHtml(statePayload.title || "Movement review unavailable")}</div>` : `
            <div class="warehouse-receiving-note"><span class="warehouse-inbound-badge">${escapeHtml(header.docstatus_label || "Posted")}</span> ${escapeHtml(header.direction_label || "")}</div>
            <div class="warehouse-receiving-cards">${cards.map(renderMovementReviewCard).join("")}</div>
          `}
        </section>
        <section class="warehouse-stock-exception-review-grid">
          ${renderMovementReviewPanel(panels.direction || {}, "direction")}
          ${renderMovementReviewPanel(panels.related || {}, "related")}
        </section>
        ${lineGroups.length ? lineGroups.map(renderMovementReviewLineGroup).join("") : `<section class="warehouse-receiving-detail" data-warehouse-movement-review-line-group="empty"><div class="warehouse-receiving-history-row" data-warehouse-movement-review-empty><span class="warehouse-receiving-meta">No movement lines visible.</span></div></section>`}
        <section class="warehouse-receiving-detail" data-warehouse-movement-review-related-panel>
          <div class="warehouse-inbound-group-head">
            <h2 class="warehouse-inbound-group-title">Related Reviews</h2>
            <div class="warehouse-inbound-group-note">Custom Warehouse review paths for item and warehouse posture.</div>
          </div>
          <div class="warehouse-receiving-panel is-active">
            ${relatedRoutes.length ? relatedRoutes.map(renderMovementRelatedRow).join("") : `<div class="warehouse-receiving-history-row" data-warehouse-movement-review-empty><span class="warehouse-receiving-meta">No related stock posture visible.</span></div>`}
          </div>
        </section>
        <section class="warehouse-receiving-detail" data-warehouse-movement-review-footer>
          <div class="warehouse-inbound-meta">Read-only warehouse movement visibility for operational review.</div>
        </section>
      </div>
    `);
    $root.find("[data-warehouse-movement-review-back]").on("click", function (event) {
      event.preventDefault();
      routeMovementBack({
        route: String(this.getAttribute("data-warehouse-movement-review-back-route") || ""),
        queue_key: String(this.getAttribute("data-warehouse-movement-review-back-queue") || ""),
      });
    });
    $root.find("[data-warehouse-movement-review-refresh]").on("click", (event) => {
      event.preventDefault();
      loadMovementReview(viewState, viewState.contextToken);
    });
    $root.find("[data-warehouse-movement-review-route-stock-posture], [data-warehouse-movement-review-related-row]").on("click", function (event) {
      event.preventDefault();
      const token = String(this.getAttribute("data-warehouse-stock-posture-token") || this.getAttribute("data-warehouse-movement-review-route-stock-posture") || "").trim();
      if (token) frappe.set_route(STOCK_POSTURE_PAGE_KEY, token);
    });
    removeDuplicateWarehouseHosts(viewState.$host.get(0));
    viewState.$host.empty().append($root);
  }

  function renderMovementReviewLoading(viewState) {
    renderMovementReviewPayload(viewState, {
      state: { kind: "loading", title: "Checking movement review", detail: "Checking movement review..." },
      header: { context_token: viewState.contextToken || "" },
      summary_cards: [],
      panels: {
        direction: { title: "Movement Direction", items: [] },
        related: { title: "Related Reviews", items: [] },
      },
      line_groups: [],
      related_routes: [],
    });
  }

  function loadMovementReview(viewState, contextToken) {
    markWarehouseDiagnostic("movementReviewServiceCallAttempted");
    viewState.contextToken = contextToken || movementTokenFromRoute();
    renderMovementReviewLoading(viewState);
    return frappe.call({
      method: MOVEMENT_REVIEW_METHOD,
      args: { context: viewState.contextToken },
    }).then((response) => {
      renderMovementReviewPayload(viewState, response && response.message ? response.message : {});
    }).catch(() => {
      renderMovementReviewPayload(viewState, {
        state: { kind: "error", title: "Movement review unavailable", detail: "Movement review could not be loaded. Refresh or contact an administrator." },
        header: { context_token: viewState.contextToken || "" },
        summary_cards: [],
        panels: {
          direction: { title: "Movement Direction", items: [] },
          related: { title: "Related Reviews", items: [] },
        },
        line_groups: [],
        related_routes: [],
      });
    });
  }

  function renderMovementReview(wrapper, contextToken) {
    markWarehouseDiagnostic("renderMovementReviewEntered");
    const viewState = makeMovementPage(wrapper);
    if (window.erpWorkspaceConsoleSidebar && typeof window.erpWorkspaceConsoleSidebar.refresh === "function") {
      window.erpWorkspaceConsoleSidebar.refresh();
    }
    loadMovementReview(viewState, contextToken || movementTokenFromRoute());
  }

  function makeInboundPage(wrapper) {
    const existing = wrapper && wrapper.__erpwWarehouseInboundQueue;
    if (existing && existing.page && existing.$host && document.documentElement.contains(existing.$host.get(0))) {
      return existing;
    }
    const page = frappe.ui.make_app_page({
      parent: wrapper,
      title: "Inbound Receiving",
      single_column: true,
    });
    const $parent = page && page.body ? $(page.body) : $(wrapper);
    const $host = $('<section class="warehouse-inbound-route"></section>');
    $parent.empty().append($host);
    const state = {
      page,
      $host,
      activeFilters: {},
      requestSerial: 0,
      loadingSignature: "",
      loadingPromise: null,
      loadedSignature: "",
      lastPayload: null,
    };
    wrapper.__erpwWarehouseInboundQueue = state;
    return state;
  }

  function renderInboundQueuePayload(viewState, payload) {
    ensureStyle();
    const controls = payload.controls || {};
    const fields = Array.isArray(controls.fields) ? controls.fields : [];
    const cards = Array.isArray(payload.cards) ? payload.cards : [];
    const groups = Array.isArray(payload.groups) ? payload.groups : [];
    const statePayload = payload.state || {};
    const queueKey = normalizeQueueKey((payload.page && payload.page.key) || viewState.queueKey || activeWorklistQueueKey() || INBOUND_QUEUE_KEY);
    const viewName = worklistViewName(queueKey);
    const $root = $(`
      <div class="sales-console-shell warehouse-inbound-shell ${queueKey === OUTBOUND_QUEUE_KEY ? "warehouse-outbound-shell" : ""}" data-erpw-workspace="warehouse" data-warehouse-view="${escapeHtml(viewName)}" data-warehouse-queue-key="${escapeHtml(queueKey)}" data-erpw-console-runtime="ready">
        <section class="warehouse-inbound-queue-header">
          <div class="warehouse-inbound-queue-head">
            <div>
              <h1 class="warehouse-inbound-queue-title">${escapeHtml(payload.summary && payload.summary.title || "Inbound Receiving")}</h1>
              <div class="warehouse-inbound-queue-note">${escapeHtml(payload.summary && payload.summary.subtitle || "Expected supplier stock due into warehouse.")}</div>
            </div>
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-back-overview>Open Warehouse page</button>
          </div>
          <div class="warehouse-inbound-queue-cards">${cards.map(renderQueueCard).join("")}</div>
          <div class="warehouse-inbound-controls">
            ${fields.map(controlField).join("")}
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-apply>Apply</button>
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-reset>Reset</button>
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-refresh>Refresh</button>
          </div>
        </section>
        <div class="warehouse-inbound-groups">
          ${statePayload.kind === "restricted" || statePayload.kind === "error"
            ? `<section class="warehouse-inbound-group" data-warehouse-inbound-group="state" data-warehouse-outbound-group="state"><h2 class="warehouse-inbound-group-title">${escapeHtml(statePayload.title || "Warehouse worklist unavailable")}</h2><div class="warehouse-inbound-meta" data-warehouse-inbound-empty data-warehouse-outbound-empty>${escapeHtml(statePayload.detail || "Warehouse work could not be loaded. Refresh or contact an administrator.")}</div></section>`
            : groups.map(renderQueueGroup).join("")}
        </div>
      </div>
    `);
    $root.find("[data-warehouse-back-overview]").on("click", (event) => {
      event.preventDefault();
      frappe.set_route(PAGE_KEY);
    });
    $root.find("[data-warehouse-filter-apply]").on("click", (event) => {
      event.preventDefault();
      viewState.activeFilters = collectInboundFilters($root);
      loadInboundQueue(viewState, { force: true });
    });
    $root.find("[data-warehouse-filter-reset]").on("click", (event) => {
      event.preventDefault();
      viewState.activeFilters = {};
      loadInboundQueue(viewState, { force: true });
    });
    $root.find("[data-warehouse-filter-refresh]").on("click", (event) => {
      event.preventDefault();
      loadInboundQueue(viewState, { force: true });
    });
    $root.find("[data-warehouse-row-open-detail]").on("click", function (event) {
      event.preventDefault();
      const row = $(this).closest("[data-warehouse-inbound-row]");
      const purchaseOrder = String(row.attr("data-warehouse-inbound-row") || "").trim();
      if (purchaseOrder) frappe.set_route(RECEIVING_PAGE_KEY, purchaseOrder);
    });
    $root.find("[data-warehouse-row-open-picking-detail]").on("click", function (event) {
      event.preventDefault();
      const row = $(this).closest("[data-warehouse-outbound-row]");
      const salesOrder = String(row.attr("data-warehouse-outbound-row") || "").trim();
      if (salesOrder) frappe.set_route(PICKING_PAGE_KEY, salesOrder);
    });
    $root.find("[data-warehouse-row-toggle]").on("click", function (event) {
      event.preventDefault();
      $(this).closest("[data-warehouse-inbound-row]").toggleClass("is-expanded");
    });
    removeDuplicateWarehouseHosts(viewState.$host.get(0));
    viewState.$host.empty().append($root);
  }

  function renderInboundLoading(viewState) {
    const isOutbound = normalizeQueueKey(viewState.queueKey) === OUTBOUND_QUEUE_KEY;
    renderInboundQueuePayload(viewState, {
      page: { key: viewState.queueKey || INBOUND_QUEUE_KEY },
      summary: { title: isOutbound ? "Outbound Picking" : "Inbound Receiving", subtitle: isOutbound ? "Checking outbound work..." : "Checking inbound work..." },
      controls: { fields: [], actions: [] },
      cards: [],
      groups: [],
      state: { kind: "loading", title: isOutbound ? "Checking outbound work" : "Checking inbound work", detail: isOutbound ? "Checking outbound work..." : "Checking inbound work..." },
    });
  }

  function loadInboundQueue(viewState, options) {
    const queueKey = normalizeQueueKey(viewState.queueKey || activeWorklistQueueKey() || INBOUND_QUEUE_KEY);
    const force = Boolean(options && options.force);
    const signature = worklistLoadSignature(queueKey, viewState.activeFilters || {});
    if (!force && viewState.loadingPromise && viewState.loadingSignature === signature) {
      markWarehouseDiagnostic("worklistDuplicateLoadReused");
      return viewState.loadingPromise;
    }
    if (!force && viewState.loadedSignature === signature && hasRenderedWorklistShell(viewState, queueKey)) {
      markWarehouseDiagnostic("worklistDuplicateRenderSkipped");
      return Promise.resolve(viewState.lastPayload || {});
    }

    const isOutbound = queueKey === OUTBOUND_QUEUE_KEY;
    const isStockExceptions = queueKey === STOCK_EXCEPTIONS_KEY;
    const isMovementVisibility = queueKey === MOVEMENT_VISIBILITY_KEY;
    const isTransferVisibility = queueKey === TRANSFER_VISIBILITY_KEY;
    markWarehouseDiagnostic(isTransferVisibility ? "transferVisibilityServiceCallAttempted" : isMovementVisibility ? "movementVisibilityServiceCallAttempted" : isStockExceptions ? "stockExceptionsServiceCallAttempted" : isOutbound ? "outboundQueueServiceCallAttempted" : "queueServiceCallAttempted");
    viewState.queueKey = queueKey;
    const requestToken = (viewState.requestSerial || 0) + 1;
    viewState.requestSerial = requestToken;
    viewState.loadingSignature = signature;
    viewState.loadedSignature = "";

    const isCurrentRequest = () => (
      viewState.requestSerial === requestToken
      && viewState.loadingSignature === signature
      && isActiveWarehouseWorklistRoute()
      && isActiveWorklistQueue(queueKey)
    );
    const finishRequest = (renderer, payload) => {
      const shouldRender = isCurrentRequest();
      if (viewState.requestSerial === requestToken && viewState.loadingSignature === signature) {
        viewState.loadingPromise = null;
        viewState.loadingSignature = "";
      }
      if (!shouldRender) {
        markWarehouseDiagnostic("worklistStaleResponseIgnored");
        return payload;
      }
      viewState.loadedSignature = signature;
      viewState.lastPayload = payload;
      renderer(viewState, payload);
      return payload;
    };

    let method = INBOUND_METHOD;
    let loadingRenderer = renderInboundLoading;
    let payloadRenderer = renderInboundQueuePayload;
    let errorPayload = {
      page: { key: queueKey },
      summary: { title: isOutbound ? "Outbound Picking" : "Inbound Receiving", subtitle: "Warehouse work could not be loaded. Refresh or contact an administrator." },
      controls: { fields: [], actions: [{ key: "refresh", label: "Refresh" }] },
      cards: [],
      groups: [],
      state: { kind: "error", title: isOutbound ? "Outbound picking unavailable" : "Inbound receiving unavailable", detail: "Warehouse work could not be loaded. Refresh or contact an administrator." },
    };
    if (isOutbound) {
      method = OUTBOUND_METHOD;
    } else if (isStockExceptions) {
      method = STOCK_EXCEPTIONS_METHOD;
      loadingRenderer = renderStockExceptionsLoading;
      payloadRenderer = renderStockExceptionsPayload;
      errorPayload = {
        page: { key: STOCK_EXCEPTIONS_KEY },
        summary: { title: "Stock Exceptions", subtitle: "Stock exceptions could not be loaded. Refresh or contact an administrator." },
        controls: { fields: [], actions: [{ key: "refresh", label: "Refresh" }] },
        cards: [],
        groups: [],
        state: { kind: "error", title: "Stock exceptions unavailable", detail: "Stock exceptions could not be loaded. Refresh or contact an administrator." },
      };
    } else if (isMovementVisibility) {
      method = MOVEMENT_VISIBILITY_METHOD;
      loadingRenderer = renderMovementLoading;
      payloadRenderer = renderMovementPayload;
      errorPayload = {
        page: { key: MOVEMENT_VISIBILITY_KEY },
        summary: { title: "Movement Visibility", subtitle: "Movement visibility could not be loaded. Refresh or contact an administrator." },
        controls: { fields: [], actions: [{ key: "refresh", label: "Refresh" }] },
        cards: [],
        groups: [],
        state: { kind: "error", title: "Movement visibility unavailable", detail: "Movement visibility could not be loaded. Refresh or contact an administrator." },
      };
    } else if (isTransferVisibility) {
      method = TRANSFER_VISIBILITY_METHOD;
      loadingRenderer = renderTransferLoading;
      payloadRenderer = renderTransferPayload;
      errorPayload = {
        page: { key: TRANSFER_VISIBILITY_KEY },
        summary: { title: "Transfer Visibility", subtitle: "Transfer visibility could not be loaded. Refresh or contact an administrator." },
        controls: { fields: [], actions: [{ key: "refresh", label: "Refresh" }] },
        cards: [],
        groups: [],
        state: { kind: "error", title: "Transfer visibility unavailable", detail: "Transfer visibility could not be loaded. Refresh or contact an administrator." },
      };
    }

    loadingRenderer(viewState);
    const requestPromise = frappe.call({
      method,
      args: { queue_key: queueKey, filters: viewState.activeFilters || {} },
    }).then((response) => finishRequest(payloadRenderer, response && response.message ? response.message : {})).catch(() => finishRequest(payloadRenderer, errorPayload));
    viewState.loadingPromise = requestPromise;
    return requestPromise;
  }

  function renderWarehouseWorklist(wrapper, queueKey) {
    const resolvedQueueKey = normalizeQueueKey(queueKey || activeWorklistQueueKey() || INBOUND_QUEUE_KEY);
    markWarehouseDiagnostic(resolvedQueueKey === TRANSFER_VISIBILITY_KEY ? "renderTransferVisibilityEntered" : resolvedQueueKey === MOVEMENT_VISIBILITY_KEY ? "renderMovementVisibilityEntered" : resolvedQueueKey === STOCK_EXCEPTIONS_KEY ? "renderStockExceptionsEntered" : resolvedQueueKey === OUTBOUND_QUEUE_KEY ? "renderOutboundQueueEntered" : "renderInboundQueueEntered");
    const viewState = makeInboundPage(wrapper);
    viewState.queueKey = resolvedQueueKey;
    const signature = worklistLoadSignature(resolvedQueueKey, viewState.activeFilters || {});
    const duplicateInFlight = Boolean(viewState.loadingPromise && viewState.loadingSignature === signature);
    const duplicateLoaded = Boolean(viewState.loadedSignature === signature && hasRenderedWorklistShell(viewState, resolvedQueueKey));
    if (!duplicateInFlight && !duplicateLoaded && window.erpWorkspaceConsoleSidebar && typeof window.erpWorkspaceConsoleSidebar.refresh === "function") {
      window.erpWorkspaceConsoleSidebar.refresh();
    }
    loadInboundQueue(viewState);
  }

  function renderInboundQueue(wrapper) {
    renderWarehouseWorklist(wrapper, INBOUND_QUEUE_KEY);
  }

  function renderOutboundQueue(wrapper) {
    renderWarehouseWorklist(wrapper, OUTBOUND_QUEUE_KEY);
  }

  function renderStockExceptions(wrapper) {
    renderWarehouseWorklist(wrapper, STOCK_EXCEPTIONS_KEY);
  }

  function renderMovementVisibility(wrapper) {
    renderWarehouseWorklist(wrapper, MOVEMENT_VISIBILITY_KEY);
  }

  function renderTransferVisibility(wrapper) {
    renderWarehouseWorklist(wrapper, TRANSFER_VISIBILITY_KEY);
  }

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].__erpwWarehouseConsoleRenderer = true;
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) { render(wrapper); };
  frappe.pages[PAGE_KEY].on_page_show = function (wrapper) {
    if (window.erpWorkspaceConsoleSidebar && typeof window.erpWorkspaceConsoleSidebar.refresh === "function") {
      window.erpWorkspaceConsoleSidebar.refresh();
    }
    render(wrapper);
  };
  const warehouseConsoleApi = window.erpWorkspaceWarehouseConsole = window.erpWorkspaceWarehouseConsole || {};
  warehouseConsoleApi.renderInboundQueue = renderInboundQueue;
  warehouseConsoleApi.renderOutboundQueue = renderOutboundQueue;
  warehouseConsoleApi.renderWarehouseWorklist = renderWarehouseWorklist;
  warehouseConsoleApi.renderStockExceptions = renderStockExceptions;
  warehouseConsoleApi.renderMovementVisibility = renderMovementVisibility;
  warehouseConsoleApi.renderTransferVisibility = renderTransferVisibility;
  warehouseConsoleApi.renderReceivingReview = renderReceivingReview;
  warehouseConsoleApi.renderPickingReview = renderPickingReview;
  warehouseConsoleApi.renderStockExceptionReview = renderStockExceptionReview;
  warehouseConsoleApi.renderStockPostureReview = renderStockPostureReview;
  warehouseConsoleApi.renderMovementReview = renderMovementReview;
  warehouseConsoleApi.renderOverview = render;
  warehouseConsoleApi.diagnostics = warehouseConsoleApi.diagnostics || {};
  warehouseConsoleApi.diagnostics.exportedRendererReady = true;
  warehouseConsoleApi.diagnostics.exportedReceivingRendererReady = true;
  warehouseConsoleApi.diagnostics.exportedPickingRendererReady = true;
  warehouseConsoleApi.diagnostics.exportedStockExceptionsRendererReady = true;
  warehouseConsoleApi.diagnostics.exportedMovementVisibilityRendererReady = true;
  warehouseConsoleApi.diagnostics.exportedTransferVisibilityRendererReady = true;
  warehouseConsoleApi.diagnostics.exportedStockExceptionReviewRendererReady = true;
  warehouseConsoleApi.diagnostics.exportedStockPostureReviewRendererReady = true;
  warehouseConsoleApi.diagnostics.exportedMovementReviewRendererReady = true;

  frappe.pages[WORKLIST_PAGE_KEY] = frappe.pages[WORKLIST_PAGE_KEY] || {};
  frappe.pages[WORKLIST_PAGE_KEY].__erpwWarehouseInboundRenderer = true;
  frappe.pages[WORKLIST_PAGE_KEY].__erpwWarehouseWorklistRenderer = true;
  frappe.pages[WORKLIST_PAGE_KEY].__erpwRenderWarehouseInboundQueue = renderInboundQueue;
  frappe.pages[WORKLIST_PAGE_KEY].__erpwRenderWarehouseWorklist = renderWarehouseWorklist;
  frappe.pages[WORKLIST_PAGE_KEY].on_page_load = function (wrapper) { renderWarehouseWorklist(wrapper, activeWorklistQueueKey()); };
  frappe.pages[WORKLIST_PAGE_KEY].on_page_show = function (wrapper) { renderWarehouseWorklist(wrapper, activeWorklistQueueKey()); };

  frappe.pages[RECEIVING_PAGE_KEY] = frappe.pages[RECEIVING_PAGE_KEY] || {};
  frappe.pages[RECEIVING_PAGE_KEY].__erpwWarehouseReceivingRenderer = true;
  frappe.pages[RECEIVING_PAGE_KEY].__erpwRenderWarehouseReceivingReview = renderReceivingReview;
  frappe.pages[RECEIVING_PAGE_KEY].on_page_load = function (wrapper) { renderReceivingReview(wrapper, receivingPurchaseOrderFromRoute()); };
  frappe.pages[RECEIVING_PAGE_KEY].on_page_show = function (wrapper) { renderReceivingReview(wrapper, receivingPurchaseOrderFromRoute()); };

  frappe.pages[PICKING_PAGE_KEY] = frappe.pages[PICKING_PAGE_KEY] || {};
  frappe.pages[PICKING_PAGE_KEY].__erpwWarehousePickingRenderer = true;
  frappe.pages[PICKING_PAGE_KEY].__erpwRenderWarehousePickingReview = renderPickingReview;
  frappe.pages[PICKING_PAGE_KEY].on_page_load = function (wrapper) { renderPickingReview(wrapper, pickingSalesOrderFromRoute()); };
  frappe.pages[PICKING_PAGE_KEY].on_page_show = function (wrapper) { renderPickingReview(wrapper, pickingSalesOrderFromRoute()); };
  frappe.pages[STOCK_EXCEPTION_PAGE_KEY] = frappe.pages[STOCK_EXCEPTION_PAGE_KEY] || {};
  frappe.pages[STOCK_EXCEPTION_PAGE_KEY].__erpwWarehouseStockExceptionReviewRenderer = true;
  frappe.pages[STOCK_EXCEPTION_PAGE_KEY].__erpwRenderWarehouseStockExceptionReview = renderStockExceptionReview;
  frappe.pages[STOCK_EXCEPTION_PAGE_KEY].on_page_load = function (wrapper) { renderStockExceptionReview(wrapper, stockExceptionTokenFromRoute()); };
  frappe.pages[STOCK_EXCEPTION_PAGE_KEY].on_page_show = function (wrapper) { renderStockExceptionReview(wrapper, stockExceptionTokenFromRoute()); };
  frappe.pages[STOCK_POSTURE_PAGE_KEY] = frappe.pages[STOCK_POSTURE_PAGE_KEY] || {};
  frappe.pages[STOCK_POSTURE_PAGE_KEY].__erpwWarehouseStockPostureReviewRenderer = true;
  frappe.pages[STOCK_POSTURE_PAGE_KEY].__erpwRenderWarehouseStockPostureReview = renderStockPostureReview;
  frappe.pages[STOCK_POSTURE_PAGE_KEY].on_page_load = function (wrapper) { renderStockPostureReview(wrapper, stockPostureTokenFromRoute()); };
  frappe.pages[STOCK_POSTURE_PAGE_KEY].on_page_show = function (wrapper) { renderStockPostureReview(wrapper, stockPostureTokenFromRoute()); };
  frappe.pages[MOVEMENT_PAGE_KEY] = frappe.pages[MOVEMENT_PAGE_KEY] || {};
  frappe.pages[MOVEMENT_PAGE_KEY].__erpwWarehouseMovementReviewRenderer = true;
  frappe.pages[MOVEMENT_PAGE_KEY].__erpwRenderWarehouseMovementReview = renderMovementReview;
  frappe.pages[MOVEMENT_PAGE_KEY].on_page_load = function (wrapper) { renderMovementReview(wrapper, movementTokenFromRoute()); };
  frappe.pages[MOVEMENT_PAGE_KEY].on_page_show = function (wrapper) { renderMovementReview(wrapper, movementTokenFromRoute()); };
  scheduleActiveOverviewRender();
  bindActiveOverviewGuard();
  scheduleActiveInboundRender();
  bindActiveInboundGuard();
  scheduleActiveReceivingRender();
  bindActiveReceivingGuard();
  scheduleActivePickingRender();
  bindActivePickingGuard();
  scheduleActiveStockExceptionRender();
  bindActiveStockExceptionGuard();
  scheduleActiveStockPostureRender();
  bindActiveStockPostureGuard();
  scheduleActiveMovementRender();
  bindActiveMovementGuard();
})();
