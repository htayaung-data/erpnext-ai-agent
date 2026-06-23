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

  function activeWarehouseRouteKey() {
    const pathRoute = pathRouteParts();
    const pathKey = String(pathRoute[0] || "");
    if (pathKey) return pathKey;
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) ? String(route[0] || "") : "";
  }

  function isWarehouseOwnedRouteKey(routeKey) {
    const key = String(routeKey || "");
    return key === PAGE_KEY
      || key === WORKLIST_PAGE_KEY
      || key === RECEIVING_PAGE_KEY
      || key === PICKING_PAGE_KEY
      || key === STOCK_EXCEPTION_PAGE_KEY
      || key === STOCK_POSTURE_PAGE_KEY
      || key === MOVEMENT_PAGE_KEY;
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
        --warehouse-bg-page: #f6faf8;
        --warehouse-bg-soft: #f8fbfa;
        --warehouse-bg-muted: #eef7f2;
        --warehouse-surface: #ffffff;
        --warehouse-surface-quiet: #fbfdfc;
        --warehouse-surface-elevated: rgba(255, 255, 255, 0.96);
        --warehouse-border-soft: rgba(219, 231, 225, 0.96);
        --warehouse-border-strong: rgba(199, 219, 209, 0.98);
        --warehouse-text-strong: #17231f;
        --warehouse-text: #20332d;
        --warehouse-text-muted: #64766e;
        --warehouse-text-soft: #708178;
        --warehouse-accent: #1f7a5f;
        --warehouse-accent-soft: rgba(31, 122, 95, 0.1);
        --warehouse-success: #147a50;
        --warehouse-warning: #a66813;
        --warehouse-warning-soft: #fff8e9;
        --warehouse-risk: #a74728;
        --warehouse-neutral: #52655d;
        --warehouse-shadow-soft: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 12px 28px rgba(34, 56, 48, 0.05);
        --warehouse-shadow-panel: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 18px 44px rgba(34, 56, 48, 0.06);
        --warehouse-radius-sm: 8px;
        --warehouse-radius-md: 12px;
        --warehouse-radius-lg: 16px;
        --warehouse-space-1: 4px;
        --warehouse-space-2: 8px;
        --warehouse-space-3: 12px;
        --warehouse-space-4: 16px;
        --warehouse-space-5: 20px;
        --warehouse-focus-ring: 0 0 0 3px rgba(31, 122, 95, 0.16);
        width: min(1180px, calc(100% - 24px));
        min-width: 0;
      }
      .sales-console-shell[data-erpw-workspace="warehouse"].warehouse-visual-foundation,
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-foundation {
        box-sizing: border-box;
      }
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-command {
        display: grid;
        gap: var(--warehouse-space-4);
        padding: 22px;
        overflow: hidden;
        border: 1px solid var(--warehouse-border-strong);
        border-radius: var(--warehouse-radius-sm);
        background: linear-gradient(135deg, var(--warehouse-surface) 0%, var(--warehouse-bg-soft) 58%, var(--warehouse-bg-muted) 100%);
        box-shadow: var(--warehouse-shadow-panel);
      }
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-command-title {
        display: grid;
        gap: 5px;
        min-width: 0;
      }
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 7px;
      }
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-chip {
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
        line-height: 1.2;
        text-transform: uppercase;
      }
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-fact-strip,
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-summary-grid,
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-row-facts,
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-related-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: var(--warehouse-space-2);
        min-width: 0;
      }
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-fact,
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-summary-card,
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-related-card {
        min-width: 0;
        padding: 13px;
        border: 1px solid var(--warehouse-border-soft);
        border-radius: var(--warehouse-radius-sm);
        background: var(--warehouse-surface-elevated);
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset;
      }
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-fact-label,
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-summary-label {
        color: var(--warehouse-text-soft);
        font-size: 10.5px;
        font-weight: 760;
        letter-spacing: 0.05em;
        line-height: 1.25;
        text-transform: uppercase;
      }
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-fact-value,
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-summary-value {
        margin-top: 6px;
        color: var(--warehouse-text-strong);
        font-size: 22px;
        font-weight: 760;
        line-height: 1.05;
      }
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-fact-note,
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-summary-note {
        margin-top: 5px;
        color: var(--warehouse-text-muted);
        font-size: 11.5px;
        line-height: 1.38;
      }
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-row-card {
        display: grid;
        gap: var(--warehouse-space-3);
        min-width: 0;
        padding: 14px;
        border: 1px solid var(--warehouse-border-soft);
        border-radius: var(--warehouse-radius-sm);
        background: var(--warehouse-surface);
        box-shadow: var(--warehouse-shadow-soft);
      }
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-row-list {
        display: grid;
        grid-template-columns: minmax(0, 1fr);
        gap: var(--warehouse-space-2);
        min-width: 0;
      }
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-row-header {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: var(--warehouse-space-3);
        align-items: start;
        min-width: 0;
      }
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-action-strip {
        display: flex;
        flex-wrap: wrap;
        gap: var(--warehouse-space-2);
        align-items: center;
        justify-content: flex-end;
      }
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-filter-strip {
        min-width: 0;
      }
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-tab-strip {
        display: flex;
        flex-wrap: wrap;
        gap: var(--warehouse-space-2);
        min-width: 0;
      }
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-tab {
        min-height: 34px;
        padding: 0 12px;
        border: 1px solid var(--warehouse-border-soft);
        border-radius: var(--warehouse-radius-sm);
        background: var(--warehouse-surface);
        color: var(--warehouse-text);
        font-size: 12px;
        font-weight: 730;
      }
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-tab.is-active {
        border-color: rgba(31, 122, 95, 0.32);
        background: var(--warehouse-accent-soft);
        color: var(--warehouse-accent);
      }
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-guardrail,
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-fallback {
        min-width: 0;
        padding: var(--warehouse-space-4);
        border: 1px solid var(--warehouse-border-soft);
        border-radius: var(--warehouse-radius-sm);
        background: var(--warehouse-bg-soft);
        color: var(--warehouse-text-muted);
        font-size: 12.5px;
        line-height: 1.5;
      }
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-guardrail-title,
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-fallback-title {
        margin: 0 0 3px;
        color: var(--warehouse-text);
        font-size: 13px;
        font-weight: 780;
      }
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-loading-skeleton {
        min-height: 18px;
        border-radius: var(--warehouse-radius-sm);
        background: linear-gradient(90deg, rgba(209, 226, 218, 0.42), rgba(246, 250, 248, 0.92), rgba(209, 226, 218, 0.42));
        background-size: 180% 100%;
      }
      .sales-console-shell[data-erpw-workspace="warehouse"] .warehouse-visual-focus,
      .sales-console-shell[data-erpw-workspace="warehouse"] button:focus-visible,
      .sales-console-shell[data-erpw-workspace="warehouse"] [role=button]:focus-visible,
      .sales-console-shell[data-erpw-workspace="warehouse"] a:focus-visible {
        outline: 2px solid rgba(31, 122, 95, 0.36);
        outline-offset: 2px;
        box-shadow: var(--warehouse-focus-ring);
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
      .warehouse-cockpit-command-eyebrow {
        margin-bottom: 6px;
        color: #376455;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.08em;
        line-height: 1.2;
        text-transform: uppercase;
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
      .warehouse-cockpit-card-action:focus,
      .warehouse-console-refresh:focus,
      .warehouse-console-inbound-open:focus {
        outline: 2px solid rgba(31, 122, 95, 0.36);
        outline-offset: 2px;
        box-shadow: var(--warehouse-focus-ring);
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
      .warehouse-cockpit-guardrail strong {
        display: block;
        margin-bottom: 3px;
        color: #20332d;
        font-size: 13px;
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
        box-shadow: 0 18px 44px rgba(34, 56, 48, 0.06);
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
      .warehouse-inbound-command {
        display: grid;
        gap: 8px;
        min-width: 0;
      }
      .warehouse-inbound-queue-eyebrow {
        color: #376455;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.08em;
        line-height: 1.2;
        text-transform: uppercase;
      }
      .warehouse-inbound-chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 7px;
      }
      .warehouse-inbound-chip,
      .warehouse-inbound-status-chip {
        display: inline-flex;
        align-items: center;
        width: fit-content;
        max-width: 100%;
        min-height: 24px;
        padding: 0 9px;
        border: 1px solid rgba(195, 215, 206, 0.92);
        border-radius: 999px;
        background: #f5faf7;
        color: #25483c;
        font-size: 11px;
        font-weight: 760;
        line-height: 1.2;
        overflow-wrap: anywhere;
      }
      .warehouse-inbound-chip.is-read-only {
        border-color: rgba(55, 100, 85, 0.2);
        background: #eaf6f0;
      }
      .warehouse-inbound-queue-guardrail {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr);
        gap: 10px;
        align-items: center;
        padding: 13px 14px;
        border: 1px solid rgba(191, 126, 32, 0.22);
        border-radius: 8px;
        background: #fffaf1;
        color: #5f4721;
        font-size: 12.5px;
        line-height: 1.45;
      }
      .warehouse-inbound-queue-guardrail strong {
        color: #3c2f1b;
        font-weight: 800;
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
      .warehouse-inbound-row.is-receiving {
        gap: 10px;
        padding: 13px;
        background: #ffffff;
        box-shadow: 0 10px 28px rgba(34, 56, 48, 0.04);
      }
      .warehouse-outbound-row.is-picking {
        gap: 10px;
        padding: 13px;
        background: #ffffff;
        box-shadow: 0 10px 28px rgba(34, 56, 48, 0.04);
      }
      .warehouse-inbound-row-main {
        display: grid;
        grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.85fr) minmax(0, 0.9fr) minmax(0, 0.75fr) auto;
        gap: 10px;
        align-items: center;
      }
      .warehouse-inbound-row-summary {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 10px;
        align-items: start;
      }
      .warehouse-inbound-row-identity {
        display: grid;
        gap: 3px;
        min-width: 0;
      }
      .warehouse-inbound-row-facts {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 8px;
      }
      .warehouse-inbound-row-fact {
        min-width: 0;
        padding: 10px 11px;
        border: 1px solid rgba(224, 233, 229, 0.96);
        border-radius: 8px;
        background: #fbfdfc;
      }
      .warehouse-inbound-row-fact span {
        display: block;
        color: #667a71;
        font-size: 10px;
        font-weight: 760;
        letter-spacing: 0.05em;
        line-height: 1.25;
        text-transform: uppercase;
      }
      .warehouse-inbound-row-fact strong {
        display: block;
        margin-top: 5px;
        color: #17231f;
        font-size: 12.5px;
        font-weight: 760;
        line-height: 1.25;
        overflow-wrap: anywhere;
      }
      .warehouse-inbound-row-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        justify-content: flex-end;
      }
      .warehouse-inbound-status-chip.is-overdue {
        border-color: rgba(191, 126, 32, 0.28);
        background: #fff6e8;
        color: #6a4417;
      }
      .warehouse-inbound-status-chip.is-partially_received {
        border-color: rgba(86, 122, 147, 0.24);
        background: #f4f8fb;
        color: #254456;
      }
      .warehouse-inbound-status-chip.is-due_today {
        border-color: rgba(52, 130, 91, 0.24);
        background: #f4fbf7;
        color: #24563d;
      }
      .warehouse-outbound-status-chip.is-ready_to_pick {
        border-color: rgba(52, 130, 91, 0.24);
        background: #f4fbf7;
        color: #24563d;
      }
      .warehouse-outbound-status-chip.is-partially_picked {
        border-color: rgba(86, 122, 147, 0.24);
        background: #f4f8fb;
        color: #254456;
      }
      .warehouse-outbound-status-chip.is-needs_stock_review {
        border-color: rgba(191, 126, 32, 0.28);
        background: #fff6e8;
        color: #6a4417;
      }
      .warehouse-inbound-status-chip.is-inbound_cover_expected {
        border-color: rgba(52, 130, 91, 0.24);
        background: #f4fbf7;
        color: #24563d;
      }
      .warehouse-inbound-status-chip.is-urgent_aging,
      .warehouse-inbound-status-chip.is-needs_stock_review {
        border-color: rgba(191, 126, 32, 0.28);
        background: #fff6e8;
        color: #6a4417;
      }
      .warehouse-inbound-status-chip.is-warehouse_posture_missing {
        border-color: rgba(86, 122, 147, 0.24);
        background: #f4f8fb;
        color: #254456;
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
      .warehouse-inbound-row.is-receiving .warehouse-inbound-lines {
        padding-top: 9px;
      }
      .warehouse-outbound-row.is-picking .warehouse-inbound-lines {
        padding-top: 9px;
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
        box-shadow: 0 18px 44px rgba(34, 56, 48, 0.06);
      }
      .warehouse-receiving-head {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 16px;
        align-items: start;
      }
      .warehouse-receiving-command {
        display: grid;
        gap: 8px;
        min-width: 0;
      }
      .warehouse-receiving-eyebrow {
        color: #376455;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.08em;
        line-height: 1.2;
        text-transform: uppercase;
      }
      .warehouse-receiving-title {
        margin: 0;
        color: #17231f;
        font-size: 28px;
        font-weight: 790;
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
      .warehouse-receiving-chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 7px;
      }
      .warehouse-receiving-chip,
      .warehouse-receiving-history-pill,
      .warehouse-receiving-line-status {
        display: inline-flex;
        align-items: center;
        width: fit-content;
        max-width: 100%;
        min-height: 24px;
        padding: 0 9px;
        border: 1px solid rgba(195, 215, 206, 0.92);
        border-radius: 999px;
        background: #f5faf7;
        color: #25483c;
        font-size: 11px;
        font-weight: 760;
        line-height: 1.2;
        overflow-wrap: anywhere;
      }
      .warehouse-receiving-chip.is-read-only {
        border-color: rgba(55, 100, 85, 0.2);
        background: #eaf6f0;
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
      .warehouse-receiving-command-grid,
      .warehouse-receiving-cards,
      .warehouse-receiving-readiness,
      .warehouse-receiving-line-facts {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 8px;
      }
      .warehouse-receiving-card,
      .warehouse-receiving-readiness-card,
      .warehouse-receiving-command-fact,
      .warehouse-receiving-line-fact {
        min-width: 0;
        padding: 12px;
        border: 1px solid rgba(219, 231, 225, 0.96);
        border-radius: 8px;
        background: #ffffff;
      }
      .warehouse-receiving-readiness-card.is-ready {
        border-color: rgba(52, 130, 91, 0.22);
        background: #f4fbf7;
      }
      .warehouse-receiving-readiness-card.is-blocked {
        border-color: rgba(191, 126, 32, 0.24);
        background: #fff8ed;
      }
      .warehouse-receiving-readiness-card.is-received {
        border-color: rgba(86, 122, 147, 0.22);
        background: #f4f8fb;
      }
      .warehouse-receiving-readiness-card.is-unavailable {
        border-color: rgba(148, 111, 83, 0.22);
        background: #fbf6f2;
      }
      .warehouse-receiving-card-label,
      .warehouse-receiving-command-fact span,
      .warehouse-receiving-line-fact span {
        display: block;
        color: #667a71;
        font-size: 10.5px;
        font-weight: 760;
        letter-spacing: 0.05em;
        line-height: 1.25;
        text-transform: uppercase;
      }
      .warehouse-receiving-card-value,
      .warehouse-receiving-command-fact strong,
      .warehouse-receiving-line-fact strong {
        display: block;
        margin-top: 7px;
        color: #17231f;
        font-size: 20px;
        font-weight: 760;
        line-height: 1.08;
        overflow-wrap: anywhere;
      }
      .warehouse-receiving-command-fact strong,
      .warehouse-receiving-line-fact strong {
        font-size: 13px;
        line-height: 1.25;
      }
      .warehouse-receiving-card-note {
        margin-top: 6px;
        color: #708178;
        font-size: 11.5px;
        line-height: 1.35;
      }
      .warehouse-receiving-guardrail {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr);
        gap: 10px;
        align-items: center;
        margin-top: 12px;
        padding: 13px 14px;
        border: 1px solid rgba(191, 126, 32, 0.22);
        border-radius: 8px;
        background: #fffaf1;
        color: #5f4721;
        font-size: 12.5px;
        line-height: 1.45;
      }
      .warehouse-receiving-guardrail strong {
        color: #3c2f1b;
        font-weight: 800;
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
      .warehouse-receiving-detail-head {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 12px;
        align-items: start;
      }
      .warehouse-receiving-section-title {
        margin: 0 0 4px;
        color: #1c2b26;
        font-size: 16px;
        font-weight: 780;
        line-height: 1.2;
      }
      .warehouse-receiving-tabs {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        justify-content: flex-end;
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
        gap: 10px;
        align-items: center;
        min-width: 0;
        padding: 13px;
        border: 1px solid rgba(228, 236, 232, 0.98);
        border-radius: 8px;
        background: #fbfdfc;
      }
      .warehouse-receiving-line.is-blocked {
        border-color: rgba(191, 126, 32, 0.26);
        background: #fffaf1;
      }
      .warehouse-receiving-line.is-received {
        background: #f6faf8;
      }
      .warehouse-receiving-line-main {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 10px;
        align-items: start;
      }
      .warehouse-receiving-line-status {
        display: grid;
        gap: 2px;
        justify-items: start;
        min-height: 32px;
        padding: 6px 10px;
        border-radius: 8px;
      }
      .warehouse-receiving-line-status span {
        font-size: 9.5px;
        font-weight: 800;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }
      .warehouse-receiving-line-status strong {
        font-size: 11.5px;
        font-weight: 760;
      }
      .warehouse-receiving-line-status.is-blocked {
        border-color: rgba(191, 126, 32, 0.28);
        background: #fff6e8;
        color: #6a4417;
      }
      .warehouse-receiving-line-status.is-ready {
        border-color: rgba(52, 130, 91, 0.24);
        background: #f4fbf7;
        color: #24563d;
      }
      .warehouse-receiving-line-status.is-review {
        border-color: rgba(86, 122, 147, 0.24);
        background: #f4f8fb;
        color: #254456;
      }
      .warehouse-receiving-line-status.is-unavailable {
        border-color: rgba(148, 111, 83, 0.22);
        background: #fbf6f2;
        color: #604635;
      }
      .warehouse-picking-line.is-ready {
        border-color: rgba(52, 130, 91, 0.2);
        background: #f8fcfa;
      }
      .warehouse-picking-line.is-blocked {
        border-color: rgba(191, 126, 32, 0.26);
        background: #fffaf1;
      }
      .warehouse-picking-readiness-row.is-blocked {
        border-color: rgba(191, 126, 32, 0.24);
        background: #fffaf1;
      }
      .warehouse-receiving-history-row {
        grid-template-columns: minmax(0, 1fr) auto minmax(0, 0.6fr) minmax(0, 0.9fr);
      }
      .warehouse-receiving-history-note {
        padding: 10px 12px;
        border: 1px solid rgba(228, 236, 232, 0.98);
        border-radius: 8px;
        background: #f8fbfa;
        color: #64766e;
        font-size: 12px;
        line-height: 1.45;
      }
      .warehouse-receiving-state-panel {
        display: grid;
        gap: 6px;
        padding: 14px;
        border: 1px solid rgba(219, 231, 225, 0.96);
        border-radius: 8px;
        background: #ffffff;
        color: #64766e;
        font-size: 12.5px;
        line-height: 1.45;
      }
      .warehouse-receiving-state-panel strong {
        color: #1f2b27;
        font-size: 15px;
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
      .warehouse-stock-exception-row.is-premium {
        padding: 14px;
        background: #ffffff;
        box-shadow: 0 10px 28px rgba(34, 56, 48, 0.04);
      }
      .warehouse-stock-exception-row-summary {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 10px;
        align-items: start;
      }
      .warehouse-stock-exception-row-identity {
        display: grid;
        gap: 4px;
        min-width: 0;
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
      .warehouse-stock-exception-fact {
        min-width: 0;
        padding: 10px 11px;
        border: 1px solid rgba(224, 233, 229, 0.96);
        border-radius: 8px;
        background: #fbfdfc;
      }
      .warehouse-stock-exception-fact span {
        display: block;
        color: #667a71;
        font-size: 10px;
        font-weight: 760;
        letter-spacing: 0.05em;
        line-height: 1.25;
        text-transform: uppercase;
      }
      .warehouse-stock-exception-fact strong {
        display: block;
        margin-top: 5px;
        color: #17231f;
        font-size: 12.5px;
        font-weight: 760;
        line-height: 1.25;
        overflow-wrap: anywhere;
      }
      .warehouse-stock-exception-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        justify-content: flex-end;
      }
      .warehouse-stock-exception-details {
        display: none;
        gap: 8px;
        padding-top: 8px;
        border-top: 1px solid rgba(224, 233, 229, 0.96);
      }
      .warehouse-stock-exception-row.is-expanded .warehouse-stock-exception-details {
        display: grid;
      }
      .warehouse-stock-exception-detail {
        min-width: 0;
        padding: 10px 11px;
        border: 1px solid rgba(228, 236, 232, 0.98);
        border-radius: 8px;
        background: #f8fbfa;
        color: #51645c;
        font-size: 12px;
        line-height: 1.4;
      }
      .warehouse-stock-exception-guardrail {
        margin-top: 0;
      }
      .warehouse-stock-exception-review-shell {
        width: min(1180px, calc(100% - 24px));
        min-width: 0;
      }
      .warehouse-stock-exception-review-header {
        background:
          radial-gradient(circle at 94% 12%, rgba(48, 112, 92, 0.08), transparent 28%),
          linear-gradient(135deg, #ffffff 0%, #f7fbf9 58%, #eef7f2 100%);
      }
      .warehouse-stock-exception-review-command {
        display: grid;
        gap: 12px;
      }
      .warehouse-stock-exception-review-eyebrow {
        color: #376455;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.08em;
        line-height: 1.2;
        text-transform: uppercase;
      }
      .warehouse-stock-exception-review-chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 7px;
      }
      .warehouse-stock-exception-review-command-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 10px;
        min-width: 0;
        margin-top: 4px;
      }
      .warehouse-stock-exception-review-command-fact {
        min-width: 0;
        padding: 12px;
        border: 1px solid rgba(220, 232, 226, 0.98);
        border-radius: 8px;
        background: #ffffff;
      }
      .warehouse-stock-exception-review-command-fact span {
        display: block;
        color: #667a71;
        font-size: 10.5px;
        font-weight: 780;
        letter-spacing: 0.05em;
        line-height: 1.2;
        text-transform: uppercase;
      }
      .warehouse-stock-exception-review-command-fact strong {
        display: block;
        margin-top: 6px;
        color: #17231f;
        font-size: 13px;
        font-weight: 760;
        line-height: 1.3;
        overflow-wrap: anywhere;
      }
      .warehouse-stock-exception-review-guardrail {
        margin-top: 12px;
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
        padding: 16px;
        border: 1px solid rgba(228, 236, 232, 0.98);
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 10px 28px rgba(34, 56, 48, 0.04);
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
      .warehouse-stock-exception-review-related-panel {
        margin-top: 12px;
      }
      .warehouse-stock-posture-header {
        background:
          radial-gradient(circle at 92% 12%, rgba(48, 112, 92, 0.08), transparent 28%),
          linear-gradient(135deg, #ffffff 0%, #f7fbf9 58%, #eef7f2 100%);
      }
      .warehouse-stock-posture-command {
        display: grid;
        gap: 12px;
      }
      .warehouse-stock-posture-eyebrow {
        color: #376455;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.08em;
        line-height: 1.2;
        text-transform: uppercase;
      }
      .warehouse-stock-posture-chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 7px;
      }
      .warehouse-stock-posture-command-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 10px;
        min-width: 0;
        margin-top: 4px;
      }
      .warehouse-stock-posture-command-fact {
        min-width: 0;
        padding: 12px;
        border: 1px solid rgba(220, 232, 226, 0.98);
        border-radius: 8px;
        background: #ffffff;
      }
      .warehouse-stock-posture-command-fact span {
        display: block;
        color: #667a71;
        font-size: 10.5px;
        font-weight: 780;
        letter-spacing: 0.05em;
        line-height: 1.2;
        text-transform: uppercase;
      }
      .warehouse-stock-posture-command-fact strong {
        display: block;
        margin-top: 6px;
        color: #17231f;
        font-size: 13px;
        font-weight: 760;
        line-height: 1.3;
        overflow-wrap: anywhere;
      }
      .warehouse-stock-posture-guardrail,
      .warehouse-stock-posture-recommended-panel {
        margin-top: 12px;
      }
      .warehouse-stock-posture-recommended-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 8px;
      }
      .warehouse-stock-posture-recommended-card {
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
      .warehouse-stock-posture-recommended-card span {
        font-size: 12px;
        font-weight: 760;
      }
      .warehouse-stock-posture-recommended-card strong {
        color: #65756e;
        font-size: 12px;
        font-weight: 560;
        line-height: 1.35;
      }
      .warehouse-movement-command-header {
        background:
          radial-gradient(circle at 94% 10%, rgba(41, 120, 95, 0.08), transparent 28%),
          linear-gradient(135deg, #ffffff 0%, #f8fbfa 60%, #eef7f2 100%);
      }
      .warehouse-movement-command {
        display: grid;
        gap: 12px;
      }
      .warehouse-movement-eyebrow {
        color: #376455;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.08em;
        line-height: 1.2;
        text-transform: uppercase;
      }
      .warehouse-movement-chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 7px;
      }
      .warehouse-movement-command-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 10px;
        min-width: 0;
      }
      .warehouse-movement-command-fact,
      .warehouse-movement-row-fact {
        min-width: 0;
        padding: 11px;
        border: 1px solid rgba(220, 232, 226, 0.98);
        border-radius: 8px;
        background: #ffffff;
      }
      .warehouse-movement-command-fact span,
      .warehouse-movement-row-fact span {
        display: block;
        color: #667a71;
        font-size: 10.5px;
        font-weight: 780;
        letter-spacing: 0.05em;
        line-height: 1.2;
        text-transform: uppercase;
      }
      .warehouse-movement-command-fact strong,
      .warehouse-movement-row-fact strong {
        display: block;
        margin-top: 6px;
        color: #17231f;
        font-size: 13px;
        font-weight: 760;
        line-height: 1.3;
        overflow-wrap: anywhere;
      }
      .warehouse-movement-row {
        background: #ffffff;
        box-shadow: 0 10px 28px rgba(34, 56, 48, 0.04);
      }
      .warehouse-movement-row-main {
        display: grid;
        grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.75fr) minmax(0, 1.1fr) minmax(0, 0.75fr) auto;
        gap: 10px;
        align-items: center;
      }
      .warehouse-movement-row-facts {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 8px;
        padding-top: 8px;
        border-top: 1px solid rgba(224, 233, 229, 0.96);
      }
      .warehouse-movement-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        justify-content: flex-end;
      }
      .warehouse-movement-guardrail {
        margin-top: 12px;
      }
      .warehouse-movement-review-header {
        background:
          radial-gradient(circle at 92% 12%, rgba(41, 120, 95, 0.08), transparent 28%),
          linear-gradient(135deg, #ffffff 0%, #f8fbfa 60%, #eef7f2 100%);
      }
      .warehouse-movement-review-command {
        display: grid;
        gap: 12px;
        min-width: 0;
      }
      .warehouse-movement-review-eyebrow {
        color: #376455;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.08em;
        line-height: 1.2;
        text-transform: uppercase;
      }
      .warehouse-movement-review-chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 7px;
      }
      .warehouse-movement-review-command-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 10px;
        min-width: 0;
      }
      .warehouse-movement-review-command-fact,
      .warehouse-movement-review-line-fact {
        min-width: 0;
        padding: 11px;
        border: 1px solid rgba(220, 232, 226, 0.98);
        border-radius: 8px;
        background: #ffffff;
      }
      .warehouse-movement-review-command-fact span,
      .warehouse-movement-review-line-fact span {
        display: block;
        color: #667a71;
        font-size: 10.5px;
        font-weight: 780;
        letter-spacing: 0.05em;
        line-height: 1.2;
        text-transform: uppercase;
      }
      .warehouse-movement-review-command-fact strong,
      .warehouse-movement-review-line-fact strong {
        display: block;
        margin-top: 6px;
        color: #17231f;
        font-size: 13px;
        font-weight: 760;
        line-height: 1.3;
        overflow-wrap: anywhere;
      }
      .warehouse-movement-review-guardrail {
        margin-top: 12px;
      }
      .warehouse-movement-review-line-card {
        display: grid;
        gap: 10px;
        padding: 13px;
        border: 1px solid rgba(228, 236, 232, 0.98);
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 10px 28px rgba(34, 56, 48, 0.04);
      }
      .warehouse-movement-review-line-main {
        display: grid;
        grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.65fr) minmax(0, 1fr) auto;
        gap: 10px;
        align-items: center;
      }
      .warehouse-movement-review-line-facts {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 8px;
        padding-top: 8px;
        border-top: 1px solid rgba(224, 233, 229, 0.96);
      }
      .warehouse-transfer-command-header {
        background:
          radial-gradient(circle at 94% 10%, rgba(41, 120, 95, 0.08), transparent 28%),
          linear-gradient(135deg, #ffffff 0%, #f8fbfa 60%, #eef7f2 100%);
      }
      .warehouse-transfer-command {
        display: grid;
        gap: 12px;
        min-width: 0;
      }
      .warehouse-transfer-eyebrow {
        color: #376455;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.08em;
        line-height: 1.2;
        text-transform: uppercase;
      }
      .warehouse-transfer-chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 7px;
      }
      .warehouse-transfer-command-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 10px;
        min-width: 0;
      }
      .warehouse-transfer-command-fact,
      .warehouse-transfer-row-fact {
        min-width: 0;
        padding: 11px;
        border: 1px solid rgba(220, 232, 226, 0.98);
        border-radius: 8px;
        background: #ffffff;
      }
      .warehouse-transfer-command-fact span,
      .warehouse-transfer-row-fact span {
        display: block;
        color: #667a71;
        font-size: 10.5px;
        font-weight: 780;
        letter-spacing: 0.05em;
        line-height: 1.2;
        text-transform: uppercase;
      }
      .warehouse-transfer-command-fact strong,
      .warehouse-transfer-row-fact strong {
        display: block;
        margin-top: 6px;
        color: #17231f;
        font-size: 13px;
        font-weight: 760;
        line-height: 1.3;
        overflow-wrap: anywhere;
      }
      .warehouse-transfer-row {
        background: #ffffff;
        box-shadow: 0 10px 28px rgba(34, 56, 48, 0.04);
      }
      .warehouse-transfer-row-main {
        display: grid;
        grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.75fr) minmax(0, 1.1fr) minmax(0, 0.75fr) auto;
        gap: 10px;
        align-items: center;
      }
      .warehouse-transfer-row-facts {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 8px;
        padding-top: 8px;
        border-top: 1px solid rgba(224, 233, 229, 0.96);
      }
      .warehouse-transfer-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        justify-content: flex-end;
      }
      .warehouse-transfer-guardrail {
        margin-top: 12px;
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

      /* W13B3 corrective visual alignment: restrained Sales/Procurement family styling. */
      .sales-console-shell[data-erpw-workspace='warehouse'] {
        --warehouse-bg-page: #f7f9fc;
        --warehouse-bg-soft: #f8fafc;
        --warehouse-bg-muted: #eef2f7;
        --warehouse-surface: #ffffff;
        --warehouse-surface-quiet: #fbfdff;
        --warehouse-surface-elevated: rgba(255, 255, 255, 0.985);
        --warehouse-border-soft: rgba(226, 232, 240, 0.94);
        --warehouse-border-strong: rgba(203, 213, 225, 0.92);
        --warehouse-text-strong: #0f172a;
        --warehouse-text: #1e293b;
        --warehouse-text-muted: #64748b;
        --warehouse-text-soft: #748195;
        --warehouse-accent: #0f766e;
        --warehouse-accent-dark: #164e63;
        --warehouse-accent-2: #2563eb;
        --warehouse-accent-soft: rgba(15, 118, 110, 0.08);
        --warehouse-amber: #b7791f;
        --warehouse-amber-soft: rgba(245, 158, 11, 0.1);
        --warehouse-board-accent: #0f766e;
        --warehouse-board-accent-soft: rgba(15, 118, 110, 0.07);
        --warehouse-shadow-soft: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 6px 16px rgba(15, 23, 42, 0.035);
        --warehouse-shadow-panel: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 10px 24px rgba(15, 23, 42, 0.045);
        --warehouse-shadow-card: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 8px 18px rgba(15, 23, 42, 0.035);
        --warehouse-radius-sm: 8px;
        --warehouse-radius-md: 10px;
        --warehouse-radius-lg: 14px;
        color: var(--warehouse-text);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-console-shell,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-outbound-premium-shell {
        display: grid;
        gap: 14px;
        width: min(1180px, calc(100% - 24px));
        padding: 14px;
        border: 1px solid var(--warehouse-border-soft);
        border-radius: var(--warehouse-radius-lg);
        background: linear-gradient(180deg, rgba(248, 250, 252, 0.98), rgba(241, 245, 249, 0.92));
        box-shadow: var(--warehouse-shadow-panel);
        overflow: hidden;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell {
        --warehouse-board-accent: #2563eb;
        --warehouse-board-accent-soft: rgba(37, 99, 235, 0.07);
      }
      .warehouse-console-shell .warehouse-console-header {
        border: 1px solid rgba(30, 41, 59, 0.92);
        border-radius: var(--warehouse-radius-lg);
        background: linear-gradient(135deg, #111827 0%, #1e293b 56%, #0f172a 100%);
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.09) inset, 0 12px 26px rgba(15, 23, 42, 0.14);
        color: #f8fafc;
      }
      .warehouse-inbound-premium-shell .warehouse-inbound-queue-header,
      .warehouse-outbound-premium-shell .warehouse-inbound-queue-header {
        border: 1px solid var(--warehouse-border-soft);
        border-radius: var(--warehouse-radius-lg);
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        box-shadow: var(--warehouse-shadow-panel);
        color: var(--warehouse-text);
      }
      .warehouse-console-shell .warehouse-console-title {
        color: #ffffff;
        font-size: clamp(28px, 3vw, 36px);
        font-weight: 760;
        letter-spacing: 0;
        text-shadow: none;
      }
      .warehouse-inbound-premium-shell .warehouse-inbound-queue-title,
      .warehouse-outbound-premium-shell .warehouse-inbound-queue-title {
        color: var(--warehouse-text-strong);
        font-size: clamp(22px, 2.2vw, 28px);
        font-weight: 720;
        letter-spacing: 0;
      }
      .warehouse-console-shell .warehouse-console-note {
        color: rgba(226, 232, 240, 0.92);
        font-size: 13px;
        line-height: 1.52;
      }
      .warehouse-inbound-premium-shell .warehouse-inbound-queue-note,
      .warehouse-outbound-premium-shell .warehouse-inbound-queue-note {
        color: var(--warehouse-text-muted);
        font-size: 12.5px;
        line-height: 1.48;
      }
      .warehouse-console-shell .warehouse-cockpit-command-eyebrow {
        color: #93c5fd;
        letter-spacing: 0.08em;
      }
      .warehouse-inbound-premium-shell .warehouse-inbound-queue-eyebrow,
      .warehouse-outbound-premium-shell .warehouse-inbound-queue-eyebrow {
        color: #475569;
        letter-spacing: 0.07em;
      }
      .warehouse-console-shell .warehouse-visual-chip {
        border-color: rgba(148, 163, 184, 0.34);
        background: rgba(248, 250, 252, 0.1);
        color: #e2e8f0;
      }
      .warehouse-inbound-premium-shell .warehouse-visual-chip,
      .warehouse-outbound-premium-shell .warehouse-visual-chip,
      .warehouse-inbound-premium-shell .warehouse-inbound-chip,
      .warehouse-outbound-premium-shell .warehouse-inbound-chip,
      .warehouse-inbound-premium-shell .warehouse-inbound-status-chip,
      .warehouse-outbound-premium-shell .warehouse-inbound-status-chip {
        border-color: rgba(203, 213, 225, 0.92);
        background: #f8fafc;
        color: #334155;
      }
      .warehouse-inbound-premium-shell .warehouse-inbound-chip.is-read-only,
      .warehouse-outbound-premium-shell .warehouse-inbound-chip.is-read-only {
        border-color: rgba(15, 118, 110, 0.18);
        background: rgba(240, 253, 250, 0.78);
        color: #0f766e;
      }
      .warehouse-console-shell .warehouse-console-refresh,
      .warehouse-console-shell .warehouse-cockpit-card-action,
      .warehouse-console-shell .warehouse-console-inbound-open,
      .warehouse-inbound-premium-shell .warehouse-inbound-queue-button,
      .warehouse-outbound-premium-shell .warehouse-inbound-queue-button {
        min-height: 32px;
        padding: 0 11px;
        border: 1px solid rgba(203, 213, 225, 0.98);
        border-radius: var(--warehouse-radius-sm);
        background: #ffffff;
        color: #1e293b;
        font-size: 12px;
        font-weight: 680;
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 4px 10px rgba(15, 23, 42, 0.025);
        transition: border-color 0.16s ease, box-shadow 0.16s ease, transform 0.16s ease;
      }
      .warehouse-console-shell button:hover,
      .warehouse-inbound-premium-shell button:hover,
      .warehouse-outbound-premium-shell button:hover {
        border-color: rgba(148, 163, 184, 0.98);
        box-shadow: var(--warehouse-shadow-soft);
        transform: translateY(-1px);
      }
      .warehouse-console-shell .warehouse-cockpit-pulse,
      .warehouse-console-shell .warehouse-cockpit-start,
      .warehouse-console-shell .warehouse-cockpit-route-section,
      .warehouse-console-shell .warehouse-cockpit-guardrail,
      .warehouse-inbound-premium-shell .warehouse-inbound-group,
      .warehouse-outbound-premium-shell .warehouse-inbound-group,
      .warehouse-console-shell .warehouse-console-inbound-panel {
        border: 1px solid var(--warehouse-border-soft);
        border-radius: var(--warehouse-radius-md);
        background: #ffffff;
        box-shadow: var(--warehouse-shadow-soft);
      }
      .warehouse-console-shell .warehouse-cockpit-pulse,
      .warehouse-console-shell .warehouse-cockpit-start,
      .warehouse-console-shell .warehouse-cockpit-route-section {
        padding: 16px;
      }
      .warehouse-console-shell .warehouse-cockpit-section-title,
      .warehouse-inbound-premium-shell .warehouse-inbound-group-title,
      .warehouse-outbound-premium-shell .warehouse-inbound-group-title {
        color: var(--warehouse-text-strong);
        font-size: 15px;
        font-weight: 720;
      }
      .warehouse-console-shell .warehouse-cockpit-section-note,
      .warehouse-inbound-premium-shell .warehouse-inbound-group-note,
      .warehouse-outbound-premium-shell .warehouse-inbound-group-note {
        color: var(--warehouse-text-muted);
        font-size: 12px;
      }
      .warehouse-console-shell .warehouse-console-kpi-card,
      .warehouse-inbound-premium-shell .warehouse-inbound-queue-card,
      .warehouse-outbound-premium-shell .warehouse-inbound-queue-card,
      .warehouse-console-shell .warehouse-console-inbound-card,
      .warehouse-console-shell .warehouse-cockpit-start-card,
      .warehouse-console-shell .warehouse-cockpit-route-card {
        min-height: 0;
        padding: 12px;
        border: 1px solid var(--warehouse-border-soft);
        border-radius: var(--warehouse-radius-sm);
        background: #ffffff;
        box-shadow: none;
        overflow: hidden;
      }
      .warehouse-console-shell .warehouse-cockpit-start-card,
      .warehouse-console-shell .warehouse-cockpit-route-card {
        min-height: 132px;
        border-left: 3px solid rgba(15, 118, 110, 0.5);
      }
      .warehouse-console-shell .warehouse-cockpit-start-card.is-risk,
      .warehouse-console-shell .warehouse-cockpit-route-card.is-risk {
        border-left-color: rgba(183, 121, 31, 0.66);
        background: #fffdf7;
      }
      .warehouse-console-shell .warehouse-cockpit-start-card.is-movement,
      .warehouse-console-shell .warehouse-cockpit-route-card.is-movement {
        border-left-color: rgba(37, 99, 235, 0.5);
        background: #f8fbff;
      }
      .warehouse-console-shell .warehouse-console-kpi-card,
      .warehouse-inbound-premium-shell .warehouse-inbound-queue-card,
      .warehouse-outbound-premium-shell .warehouse-inbound-queue-card,
      .warehouse-console-shell .warehouse-console-inbound-card {
        border-top: 2px solid rgba(15, 118, 110, 0.24);
      }
      .warehouse-outbound-premium-shell .warehouse-inbound-queue-card {
        border-top-color: rgba(37, 99, 235, 0.24);
      }
      .warehouse-console-shell .warehouse-console-kpi-label,
      .warehouse-inbound-premium-shell .warehouse-inbound-queue-card-label,
      .warehouse-outbound-premium-shell .warehouse-inbound-queue-card-label,
      .warehouse-console-shell .warehouse-console-inbound-card-label,
      .warehouse-console-shell .warehouse-cockpit-card-kicker {
        color: var(--warehouse-text-soft);
        font-size: 10.5px;
        font-weight: 700;
        letter-spacing: 0.04em;
        line-height: 1.25;
        overflow-wrap: normal;
      }
      .warehouse-console-shell .warehouse-console-kpi-value,
      .warehouse-console-shell .warehouse-console-inbound-card-value {
        color: var(--warehouse-text-strong);
        font-size: clamp(22px, 2.4vw, 28px);
        font-weight: 720;
        line-height: 1;
      }
      .warehouse-inbound-premium-shell .warehouse-inbound-queue-card-value,
      .warehouse-outbound-premium-shell .warehouse-inbound-queue-card-value {
        color: var(--warehouse-text-strong);
        font-size: 20px;
        font-weight: 700;
        line-height: 1.05;
      }
      .warehouse-console-shell .warehouse-cockpit-card-title,
      .warehouse-inbound-premium-shell .warehouse-inbound-row-title,
      .warehouse-outbound-premium-shell .warehouse-inbound-row-title {
        color: var(--warehouse-text-strong);
        font-size: 14px;
        font-weight: 720;
      }
      .warehouse-console-shell .warehouse-cockpit-card-note,
      .warehouse-console-shell .warehouse-console-kpi-meta,
      .warehouse-console-shell .warehouse-console-inbound-card-note,
      .warehouse-inbound-premium-shell .warehouse-inbound-queue-card-note,
      .warehouse-outbound-premium-shell .warehouse-inbound-queue-card-note {
        color: var(--warehouse-text-muted);
        font-size: 11.5px;
        line-height: 1.38;
      }
      .warehouse-inbound-premium-shell .warehouse-inbound-controls,
      .warehouse-outbound-premium-shell .warehouse-inbound-controls {
        gap: 8px;
        padding: 12px;
        border: 1px solid var(--warehouse-border-soft);
        border-radius: var(--warehouse-radius-md);
        background: #ffffff;
        box-shadow: var(--warehouse-shadow-soft);
      }
      .warehouse-inbound-premium-shell .warehouse-inbound-field label,
      .warehouse-outbound-premium-shell .warehouse-inbound-field label {
        color: var(--warehouse-text-muted);
        font-size: 10.5px;
        font-weight: 700;
        letter-spacing: 0.04em;
      }
      .warehouse-inbound-premium-shell .warehouse-inbound-field input,
      .warehouse-inbound-premium-shell .warehouse-inbound-field select,
      .warehouse-outbound-premium-shell .warehouse-inbound-field input,
      .warehouse-outbound-premium-shell .warehouse-inbound-field select {
        height: 34px;
        border-color: var(--warehouse-border-strong);
        border-radius: var(--warehouse-radius-sm);
        background: #ffffff;
        box-shadow: none;
      }
      .warehouse-inbound-premium-shell .warehouse-inbound-row,
      .warehouse-outbound-premium-shell .warehouse-inbound-row {
        position: relative;
        padding: 12px;
        border: 1px solid var(--warehouse-border-soft);
        border-left: 3px solid var(--warehouse-board-accent);
        border-radius: var(--warehouse-radius-md);
        background: #ffffff;
        box-shadow: var(--warehouse-shadow-soft);
      }
      .warehouse-inbound-premium-shell .warehouse-inbound-row-fact,
      .warehouse-outbound-premium-shell .warehouse-inbound-row-fact {
        padding: 9px 10px;
        border-color: var(--warehouse-border-soft);
        border-radius: var(--warehouse-radius-sm);
        background: #f8fafc;
      }
      .warehouse-inbound-premium-shell .warehouse-inbound-lines,
      .warehouse-outbound-premium-shell .warehouse-inbound-lines {
        margin-top: 2px;
        padding: 10px;
        border: 1px solid var(--warehouse-border-soft);
        border-radius: var(--warehouse-radius-sm);
        background: #f8fafc;
      }

      @media (max-width: 1240px) {
        .warehouse-console-kpi-grid {
          grid-template-columns: repeat(3, minmax(0, 1fr));
        }
        .warehouse-console-inbound-cards,
        .warehouse-inbound-queue-cards,
        .warehouse-receiving-cards,
        .warehouse-receiving-command-grid,
        .warehouse-receiving-readiness,
        .warehouse-receiving-line-facts,
        .warehouse-stock-exception-review-command-grid,
        .warehouse-stock-posture-command-grid,
        .warehouse-stock-posture-recommended-grid,
        .warehouse-visual-fact-strip,
        .warehouse-visual-summary-grid,
        .warehouse-visual-row-facts,
        .warehouse-visual-related-grid,
        .warehouse-movement-command-grid,
        .warehouse-movement-row-facts,
        .warehouse-movement-review-command-grid,
        .warehouse-movement-review-line-facts,
        .warehouse-transfer-command-grid,
        .warehouse-transfer-row-facts {
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
        .warehouse-receiving-detail-head,
        .warehouse-receiving-line-main,
        .warehouse-receiving-history-row,
        .warehouse-receiving-guardrail,
        .warehouse-inbound-row-summary,
        .warehouse-inbound-queue-guardrail,
        .warehouse-console-inbound-row,
        .warehouse-inbound-row-main,
        .warehouse-receiving-line,
        .warehouse-cockpit-command-row,
        .warehouse-cockpit-work-grid,
        .warehouse-cockpit-route-grid,
        .warehouse-cockpit-route-grid.is-two,
        .warehouse-cockpit-start-grid,
        .warehouse-stock-exception-review-grid,
        .warehouse-stock-exception-review-command-grid,
        .warehouse-stock-posture-command-grid,
        .warehouse-stock-exception-next-grid,
        .warehouse-stock-posture-recommended-grid,
        .warehouse-movement-command-grid,
        .warehouse-movement-row-main,
        .warehouse-movement-row-facts,
        .warehouse-movement-review-command-grid,
        .warehouse-movement-review-line-main,
        .warehouse-movement-review-line-facts,
        .warehouse-visual-row-header,
        .warehouse-visual-fact-strip,
        .warehouse-visual-summary-grid,
        .warehouse-visual-row-facts,
        .warehouse-visual-related-grid,
        .warehouse-transfer-command-grid,
        .warehouse-transfer-row-main,
        .warehouse-transfer-row-facts,
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
        .warehouse-stock-exception-actions {
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
        .warehouse-inbound-line,
        .warehouse-inbound-row-facts,
        .warehouse-movement-row-facts,
        .warehouse-movement-review-line-facts,
        .warehouse-transfer-row-facts,
        .warehouse-receiving-command-grid,
        .warehouse-receiving-readiness,
        .warehouse-receiving-line-facts {
          grid-template-columns: minmax(0, 1fr);
        }
        .warehouse-visual-action-strip {
          justify-content: flex-start;
        }
        .warehouse-visual-action-strip > button,
        .warehouse-visual-action-strip > a,
        .warehouse-visual-action-strip > [role=button] {
          width: 100%;
          justify-content: center;
        }
        .warehouse-inbound-controls .warehouse-inbound-queue-button,
        .warehouse-receiving-actions .warehouse-inbound-queue-button,
        .warehouse-receiving-actions .warehouse-receiving-button {
          width: 100%;
        }
      }
      /* W13B3 responsive alignment for the in-scope Warehouse cockpit and boards. */
      @media (max-width: 640px) {
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-console-shell,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-outbound-premium-shell {
          width: min(100%, calc(100% - 12px));
          padding: 10px;
          gap: 12px;
        }
        .warehouse-console-shell .warehouse-console-header,
        .warehouse-inbound-premium-shell .warehouse-inbound-queue-header,
        .warehouse-outbound-premium-shell .warehouse-inbound-queue-header,
        .warehouse-console-shell .warehouse-cockpit-pulse,
        .warehouse-console-shell .warehouse-cockpit-start,
        .warehouse-console-shell .warehouse-cockpit-route-section,
        .warehouse-inbound-premium-shell .warehouse-inbound-group,
        .warehouse-outbound-premium-shell .warehouse-inbound-group {
          padding: 14px;
        }
        .warehouse-console-shell .warehouse-console-title {
          font-size: 28px;
          line-height: 1.08;
        }
        .warehouse-inbound-premium-shell .warehouse-inbound-queue-title,
        .warehouse-outbound-premium-shell .warehouse-inbound-queue-title {
          font-size: 22px;
          line-height: 1.12;
        }
        .warehouse-console-shell .warehouse-console-kpi-grid,
        .warehouse-console-shell .warehouse-console-inbound-cards,
        .warehouse-console-shell .warehouse-cockpit-start-grid,
        .warehouse-console-shell .warehouse-cockpit-route-grid,
        .warehouse-console-shell .warehouse-cockpit-route-grid.is-two,
        .warehouse-inbound-premium-shell .warehouse-inbound-queue-cards,
        .warehouse-outbound-premium-shell .warehouse-inbound-queue-cards,
        .warehouse-inbound-premium-shell .warehouse-inbound-controls,
        .warehouse-outbound-premium-shell .warehouse-inbound-controls,
        .warehouse-inbound-premium-shell .warehouse-inbound-row-facts,
        .warehouse-outbound-premium-shell .warehouse-inbound-row-facts {
          grid-template-columns: minmax(0, 1fr);
        }
        .warehouse-console-shell .warehouse-console-kpi-card,
        .warehouse-inbound-premium-shell .warehouse-inbound-queue-card,
        .warehouse-outbound-premium-shell .warehouse-inbound-queue-card,
        .warehouse-console-shell .warehouse-console-inbound-card,
        .warehouse-console-shell .warehouse-cockpit-start-card,
        .warehouse-console-shell .warehouse-cockpit-route-card {
          width: 100%;
          min-width: 0;
        }
        .warehouse-console-shell .warehouse-console-kpi-label,
        .warehouse-inbound-premium-shell .warehouse-inbound-queue-card-label,
        .warehouse-outbound-premium-shell .warehouse-inbound-queue-card-label,
        .warehouse-console-shell .warehouse-console-inbound-card-label {
          letter-spacing: 0.025em;
          word-break: normal;
          overflow-wrap: break-word;
        }
      }
      /* W15C2 shell-only receiving workflow preview. */
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-workflow-shell {
        display: grid;
        gap: 14px;
        margin-top: 14px;
        padding: 17px;
        border: 1px solid rgba(226, 232, 240, 0.86);
        border-radius: 18px;
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 10px 24px rgba(15, 23, 42, 0.04);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-workflow-head {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 12px;
        align-items: start;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-workflow-title {
        margin: 0;
        color: #0f172a;
        font-size: 17px;
        font-weight: 720;
        line-height: 1.2;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-workflow-subtitle {
        margin-top: 5px;
        max-width: 760px;
        color: #64748b;
        font-size: 12.5px;
        line-height: 1.45;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-workflow-badge {
        display: inline-flex;
        align-items: center;
        min-height: 24px;
        padding: 0 9px;
        border: 1px solid rgba(203, 213, 225, 0.92);
        border-radius: 999px;
        background: #f8fafc;
        color: #334155;
        font-size: 10.5px;
        font-weight: 720;
        letter-spacing: 0.018em;
        text-transform: uppercase;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-workflow-guardrail {
        padding: 11px 12px;
        border: 1px solid rgba(245, 158, 11, 0.22);
        border-radius: 13px;
        background: #fffbeb;
        color: #6b4e16;
        font-size: 12.5px;
        line-height: 1.45;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-workflow-guardrail strong {
        color: #3f2f10;
        font-weight: 760;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-workflow-status {
        display: grid;
        grid-template-columns: repeat(6, minmax(0, 1fr));
        gap: 8px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-workflow-status-step {
        min-width: 0;
        padding: 9px 10px;
        border: 1px solid rgba(226, 232, 240, 0.88);
        border-radius: 12px;
        background: #ffffff;
        color: #475569;
        font-size: 11.5px;
        font-weight: 680;
        line-height: 1.28;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-workflow-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-workflow-card {
        display: grid;
        gap: 10px;
        min-width: 0;
        padding: 14px;
        border: 1px solid rgba(226, 232, 240, 0.82);
        border-radius: 15px;
        background: #ffffff;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-workflow-card-title {
        color: #0f172a;
        font-size: 14px;
        font-weight: 720;
        line-height: 1.25;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-workflow-card-note {
        color: #64748b;
        font-size: 12px;
        line-height: 1.4;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-planned-actions,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-discrepancy-grid,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-manager-grid,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-count-grid {
        display: grid;
        gap: 8px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-count-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-planned-control,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-discrepancy-card,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-manager-card,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-count-row {
        min-width: 0;
        padding: 10px 11px;
        border: 1px solid rgba(226, 232, 240, 0.82);
        border-radius: 12px;
        background: #f8fafc;
        color: #334155;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-planned-control {
        opacity: 0.86;
        cursor: default;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-planned-control strong,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-discrepancy-card strong,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-manager-card strong,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-count-row-title {
        display: block;
        color: #0f172a;
        font-size: 12.5px;
        font-weight: 700;
        line-height: 1.28;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-planned-control span,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-discrepancy-card span,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-manager-card span {
        display: block;
        margin-top: 3px;
        color: #64748b;
        font-size: 11.5px;
        line-height: 1.36;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-count-fields {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 6px;
        margin-top: 8px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-count-field {
        min-width: 0;
        padding: 7px 8px;
        border: 1px solid rgba(226, 232, 240, 0.76);
        border-radius: 10px;
        background: #ffffff;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-count-field span {
        display: block;
        color: #64748b;
        font-size: 10px;
        font-weight: 680;
        letter-spacing: 0.01em;
        line-height: 1.22;
        text-transform: uppercase;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-count-field strong {
        display: block;
        margin-top: 4px;
        color: #0f172a;
        font-size: 11.5px;
        font-weight: 690;
        line-height: 1.25;
      }
      @media (max-width: 900px) {
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-workflow-status,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-workflow-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-count-grid {
          grid-template-columns: minmax(0, 1fr);
        }
      }
      @media (max-width: 640px) {
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-workflow-head,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell .warehouse-receiving-count-fields {
          grid-template-columns: minmax(0, 1fr);
        }
      }
      /* W13B3R2 typography and density repair for desktop board labels. */
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-console-shell .warehouse-console-kpi-label,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-console-shell .warehouse-console-inbound-card-label,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-console-shell .warehouse-cockpit-card-kicker,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell .warehouse-inbound-queue-card-label,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-card-label,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell .warehouse-inbound-row-fact span,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-row-fact span,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell .warehouse-inbound-field label,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-field label {
        letter-spacing: 0.012em;
        line-height: 1.22;
        overflow-wrap: normal;
        word-break: normal;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell .warehouse-inbound-row-fact,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-row-fact {
        padding: 8px 10px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell .warehouse-inbound-row-fact strong,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-row-fact strong {
        margin-top: 4px;
        font-size: 12px;
        line-height: 1.28;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell .warehouse-inbound-queue-card,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-card {
        padding: 11px 12px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell .warehouse-inbound-queue-card-value,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-card-value {
        margin-top: 5px;
        font-size: 19px;
      }
      /* W13B3R narrow visual repair: specificity fixes for hero contrast and mobile readability. */
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-console-shell .warehouse-console-header.warehouse-visual-command {
        border-color: rgba(30, 41, 59, 0.94);
        background: linear-gradient(135deg, #111827 0%, #1e293b 54%, #0f172a 100%);
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.08) inset, 0 12px 24px rgba(15, 23, 42, 0.14);
        color: #f8fafc;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-console-shell .warehouse-console-header.warehouse-visual-command .warehouse-console-title {
        color: #ffffff;
        text-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-console-shell .warehouse-console-header.warehouse-visual-command .warehouse-console-note {
        color: rgba(226, 232, 240, 0.94);
        text-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-console-shell .warehouse-console-header.warehouse-visual-command .warehouse-cockpit-command-eyebrow {
        color: #93c5fd;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-console-shell .warehouse-console-header.warehouse-visual-command .warehouse-visual-chip {
        border-color: rgba(148, 163, 184, 0.38);
        background: rgba(248, 250, 252, 0.1);
        color: #e2e8f0;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell .warehouse-inbound-row-fact span,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-row-fact span,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell .warehouse-inbound-queue-card-label,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-card-label {
        letter-spacing: 0.025em;
        line-height: 1.24;
        overflow-wrap: normal;
        word-break: normal;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell .warehouse-inbound-row-fact,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-row-fact {
        padding: 8px 9px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell .warehouse-inbound-row-fact strong,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-row-fact strong {
        font-size: 12px;
        line-height: 1.24;
        overflow-wrap: break-word;
        word-break: normal;
      }
      @media (max-width: 640px) {
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-console-shell .warehouse-console-kpi-grid.warehouse-visual-summary-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-console-shell .warehouse-console-inbound-cards.warehouse-visual-summary-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-console-shell .warehouse-cockpit-start-grid.warehouse-visual-related-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-console-shell .warehouse-cockpit-route-grid.warehouse-visual-related-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-console-shell .warehouse-cockpit-route-grid.warehouse-visual-related-grid.is-two,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell .warehouse-inbound-queue-cards.warehouse-visual-summary-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-cards.warehouse-visual-summary-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell .warehouse-inbound-row-facts.warehouse-visual-row-facts,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-row-facts.warehouse-visual-row-facts {
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell .warehouse-inbound-controls,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-controls,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell .warehouse-inbound-row-main,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-row-main,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-console-shell .warehouse-console-inbound-row {
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell .warehouse-inbound-row-actions,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-row-actions {
          justify-content: stretch;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell .warehouse-inbound-row-actions > button,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-row-actions > button {
          width: 100%;
          justify-content: center;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-console-shell .warehouse-console-kpi-label,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-console-shell .warehouse-console-inbound-card-label,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell .warehouse-inbound-queue-card-label,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-card-label,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell .warehouse-inbound-row-fact span,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-row-fact span {
          letter-spacing: 0.01em;
          overflow-wrap: break-word;
          word-break: normal;
        }
      }
      /* Overview-only shared UI alignment: mirror Sales/Procurement overview grammar. */
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared {
        width: min(1120px, calc(100% - 24px));
        padding: 4px 0 30px;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
        overflow: visible;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .sales-console-header.warehouse-console-header {
        padding: 24px 24px 22px;
        border: 0;
        border-radius: 16px;
        background:
          radial-gradient(circle at top right, rgba(45, 212, 191, 0.16), transparent 26%),
          radial-gradient(circle at bottom left, rgba(56, 189, 248, 0.12), transparent 30%),
          linear-gradient(145deg, #131b2d 0%, #1d2b43 52%, #0b1220 100%);
        box-shadow: 0 24px 44px rgba(15, 23, 42, 0.16), 0 1px 0 rgba(255, 255, 255, 0.06) inset;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-command-row {
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: start;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-header-context {
        justify-items: end;
        gap: 8px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-console-refresh {
        min-height: 30px;
        padding: 0 11px;
        border: 1px solid rgba(203, 213, 225, 0.92);
        border-radius: 9px;
        background: #f8fafc;
        color: #334155;
        font-size: 12px;
        font-weight: 700;
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .sales-console-title.warehouse-console-title {
        font-size: 31px;
        font-weight: 700;
        line-height: 1.05;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-console-kpi-grid.sales-console-kpi-grid {
        grid-template-columns: repeat(3, minmax(0, 1fr));
        border-radius: 18px;
        background: linear-gradient(180deg, rgba(55, 73, 98, 0.88) 0%, rgba(40, 56, 78, 0.82) 100%);
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.08) inset, 0 18px 28px rgba(8, 15, 28, 0.1);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-console-kpi-card.sales-console-kpi-card {
        padding: 18px 18px 17px;
        border: 0;
        border-radius: 0;
        border-top: 0;
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.02) 0%, rgba(255, 255, 255, 0.01) 100%);
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-console-kpi-label.sales-console-kpi-label {
        color: #9eb0c7;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-console-kpi-value.sales-console-kpi-value {
        color: #f8fafc;
        font-size: 32px;
        font-weight: 700;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-console-kpi-meta.sales-console-kpi-meta {
        color: #d4deea;
        font-size: 12px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-pulse-section {
        padding: 16px 20px 18px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-pulse-grid-secondary {
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-pulse-context-card {
        min-height: 88px;
        cursor: default;
        border-color: rgba(226, 232, 240, 0.95);
        box-shadow: 0 12px 24px rgba(15, 23, 42, 0.035);
        transition: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-pulse-context-card:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-pulse-context-card:focus,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-pulse-context-card:focus-visible {
        cursor: default;
        border-color: rgba(226, 232, 240, 0.95);
        box-shadow: 0 12px 24px rgba(15, 23, 42, 0.035);
        transform: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-pulse-context-card .sales-console-queue-count {
        font-size: 18px;
        font-weight: 700;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-pulse-context-card[data-warehouse-kpi='freshness'] .sales-console-queue-count {
        font-size: 14px;
        letter-spacing: 0;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-pulse-tools {
        display: inline-flex;
        align-items: center;
        justify-content: flex-end;
        gap: 10px;
        min-width: 0;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-section-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-section-note {
        max-width: 260px;
        text-align: right;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-start,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-route-section,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-guardrail {
        padding: 18px 20px 20px;
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.97);
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 12px 28px rgba(15, 23, 42, 0.04);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-start-grid.sales-console-action-groups {
        grid-template-columns: minmax(0, 1fr);
        gap: 10px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-start-grid .sales-console-action-strip.primary {
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-start-grid .sales-console-action-strip.secondary {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-action-card.sales-console-action {
        border-color: rgba(241, 245, 249, 0.96);
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 8px 18px rgba(15, 23, 42, 0.026);
        outline: 0;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-action-card.sales-console-action:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-action-card.sales-console-action:focus,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-action-card.sales-console-action:focus-visible {
        border-color: rgba(226, 232, 240, 0.98);
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 10px 22px rgba(15, 23, 42, 0.04);
        outline: 0;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-action-card.sales-console-action[data-warehouse-cockpit-route-target='warehouse-console-worklist/transfer-visibility'] {
        border-color: rgba(241, 245, 249, 0.96);
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 8px 18px rgba(15, 23, 42, 0.026);
        outline: 0;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-action-card.sales-console-action[data-warehouse-cockpit-route-target='warehouse-console-worklist/transfer-visibility']:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-action-card.sales-console-action[data-warehouse-cockpit-route-target='warehouse-console-worklist/transfer-visibility']:focus,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-action-card.sales-console-action[data-warehouse-cockpit-route-target='warehouse-console-worklist/transfer-visibility']:focus-visible {
        border-color: rgba(226, 232, 240, 0.98);
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 10px 22px rgba(15, 23, 42, 0.04);
        outline: 0;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-route-grid,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-work-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px 12px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-queue-card.sales-console-queue-card {
        position: relative;
        display: grid;
        grid-template-columns: minmax(0, 1fr) 112px;
        align-items: center;
        gap: 18px;
        min-height: 104px;
        padding: 17px 18px 17px 19px;
        border: 1px solid rgba(225, 232, 240, 0.95);
        border-left: 3px solid rgba(20, 184, 166, 0.34);
        border-radius: 16px;
        background: #ffffff;
        box-shadow: 0 12px 24px rgba(15, 23, 42, 0.035);
        overflow: hidden;
        transition: border-color 140ms ease, border-left-width 140ms ease, box-shadow 140ms ease, transform 140ms ease;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-queue-card.sales-console-queue-card:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared button.warehouse-cockpit-queue-card.sales-console-queue-card:focus-visible,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-work-card.sales-console-queue-card:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared button.warehouse-cockpit-work-card.sales-console-queue-card:focus-visible {
        border-color: rgba(203, 213, 225, 0.98);
        border-left-color: rgba(20, 184, 166, 0.56);
        border-left-width: 4px;
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 16px 28px rgba(15, 23, 42, 0.065);
        transform: translateY(-1px);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-queue-card.sales-console-queue-card.is-risk,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-queue-card.sales-console-queue-card.is-movement {
        border-color: rgba(225, 232, 240, 0.95);
        border-left-color: rgba(20, 184, 166, 0.34);
        background: #ffffff;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-work-card {
        width: 100%;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-work-card.sales-console-queue-card {
        position: relative;
        display: grid;
        grid-template-columns: minmax(0, 1fr) 112px;
        align-items: center;
        gap: 18px;
        min-height: 104px;
        padding: 17px 18px 17px 19px;
        border: 1px solid rgba(225, 232, 240, 0.95);
        border-left: 3px solid rgba(20, 184, 166, 0.34);
        border-radius: 16px;
        background: #ffffff;
        box-shadow: 0 12px 24px rgba(15, 23, 42, 0.035);
        overflow: hidden;
        transition: border-color 140ms ease, border-left-width 140ms ease, box-shadow 140ms ease, transform 140ms ease;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-work-card .sales-console-queue-side,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-queue-card .sales-console-queue-side {
        width: 112px;
        min-height: 70px;
        padding: 10px 12px;
        border: 1px solid rgba(210, 225, 225, 0.95);
        border-radius: 14px;
        background: linear-gradient(180deg, #fbfefd 0%, #f8fbfb 100%);
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.96);
        display: grid;
        align-content: center;
        justify-items: center;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-work-card .sales-console-queue-count,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-queue-card .sales-console-queue-count {
        color: #020617;
        font-size: 20px;
        font-weight: 700;
        line-height: 1;
        letter-spacing: 0;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-queue-card .sales-console-queue-count {
        font-size: 15px;
        line-height: 1.15;
        text-align: center;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-work-card .sales-console-queue-side-label,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-queue-card .sales-console-queue-side-label {
        margin-top: 4px;
        color: #64748b;
        font-size: 9px;
        font-weight: 700;
        letter-spacing: 0.035em;
        text-transform: uppercase;
        text-align: center;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-card-title {
        font-size: 14px;
        font-weight: 700;
        line-height: 1.25;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-card-note {
        max-width: 46ch;
        color: #52637a;
        line-height: 1.45;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-section {
        display: grid;
        gap: 16px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-subtitle {
        max-width: 640px;
        text-align: left;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-mode {
        align-self: start;
        display: inline-flex;
        align-items: center;
        min-height: 28px;
        padding: 0 10px;
        border: 1px solid rgba(203, 213, 225, 0.9);
        border-radius: 999px;
        background: rgba(248, 250, 252, 0.96);
        color: #475569;
        font-size: 11px;
        font-weight: 760;
        letter-spacing: 0.02em;
        text-transform: uppercase;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-groups {
        display: grid;
        gap: 14px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-group {
        display: grid;
        gap: 10px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-group-head {
        display: flex;
        align-items: end;
        justify-content: space-between;
        gap: 12px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-group-head h3 {
        margin: 0;
        color: #0f172a;
        font-size: 14px;
        font-weight: 760;
        line-height: 1.25;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-group-head p {
        max-width: 420px;
        margin: 0;
        color: #64748b;
        font-size: 12px;
        line-height: 1.45;
        text-align: right;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px 12px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-card.sales-console-queue-card {
        position: relative;
        display: grid;
        grid-template-columns: minmax(0, 1fr) 128px;
        align-items: center;
        gap: 18px;
        min-height: 102px;
        padding: 16px 17px;
        border: 1px solid rgba(225, 232, 240, 0.95);
        border-left: 3px solid rgba(20, 184, 166, 0.3);
        border-radius: 16px;
        background: #ffffff;
        box-shadow: 0 12px 24px rgba(15, 23, 42, 0.035);
        transition: border-color 140ms ease, border-left-width 140ms ease, box-shadow 140ms ease, transform 140ms ease;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-card.sales-console-queue-card.is-planned {
        border-left-color: rgba(148, 163, 184, 0.34);
        background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-card.sales-console-queue-card:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-card.sales-console-queue-card:focus-within {
        border-color: rgba(203, 213, 225, 0.98);
        border-left-width: 4px;
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 16px 28px rgba(15, 23, 42, 0.06);
        transform: translateY(-1px);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-card.is-planned:hover {
        border-left-color: rgba(148, 163, 184, 0.46);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-side {
        width: 128px;
        min-height: 70px;
        padding: 10px 12px;
        border: 1px solid rgba(210, 225, 225, 0.95);
        border-radius: 14px;
        background: linear-gradient(180deg, #fbfefd 0%, #f8fbfb 100%);
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.96);
        display: grid;
        align-content: center;
        justify-items: center;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-side .sales-console-queue-side-label {
        white-space: nowrap;
        letter-spacing: 0.02em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-open {
        margin-top: 7px;
        min-width: 96px;
        min-height: 26px;
        padding: 0 9px;
        border: 1px solid rgba(203, 213, 225, 0.95);
        border-radius: 9px;
        background: #ffffff;
        color: #0f172a;
        font-size: 10.5px;
        font-weight: 720;
        letter-spacing: 0;
        word-spacing: 2px;
        white-space: nowrap;
        box-shadow: 0 6px 12px rgba(15, 23, 42, 0.04);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-open:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-open:focus-visible {
        border-color: rgba(148, 163, 184, 0.9);
        outline: 0;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-guardrail {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 12px;
        border: 1px solid rgba(226, 232, 240, 0.95);
        border-radius: 14px;
        background: #f8fafc;
        color: #52637a;
        font-size: 12px;
        line-height: 1.4;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-guardrail strong {
        color: #0f172a;
        white-space: nowrap;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-shell {
        display: grid;
        gap: 16px;
        padding: 18px 20px 20px;
        border: 1px solid rgba(203, 213, 225, 0.94);
        border-radius: 16px;
        background:
          linear-gradient(180deg, rgba(255, 251, 235, 0.54) 0%, rgba(255, 255, 255, 0.98) 36%),
          #ffffff;
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 12px 28px rgba(15, 23, 42, 0.04);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-shell::before {
        content: "";
        display: block;
        width: 42px;
        height: 2px;
        margin: 0 0 2px;
        border-radius: 999px;
        background: rgba(217, 119, 6, 0.58);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-copy {
        display: grid;
        gap: 5px;
        min-width: 0;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-title {
        margin: 0;
        color: #0f172a;
        font-size: 17px;
        font-weight: 760;
        line-height: 1.25;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-subtitle {
        max-width: 680px;
        color: #52637a;
        font-size: 12.5px;
        line-height: 1.48;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-badge {
        display: inline-flex;
        align-items: center;
        min-height: 28px;
        padding: 0 10px;
        border: 1px solid rgba(245, 158, 11, 0.26);
        border-radius: 999px;
        background: rgba(255, 251, 235, 0.92);
        color: #92400e;
        font-size: 11px;
        font-weight: 760;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        white-space: nowrap;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-guardrail {
        padding: 11px 12px;
        border: 1px dashed rgba(245, 158, 11, 0.35);
        border-radius: 14px;
        background: rgba(255, 251, 235, 0.62);
        color: #52637a;
        font-size: 12px;
        line-height: 1.45;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-status-strip {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 8px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-status-chip {
        display: flex;
        align-items: center;
        min-height: 40px;
        padding: 9px 10px;
        border: 1px solid rgba(226, 232, 240, 0.92);
        border-radius: 12px;
        background: #ffffff;
        color: #334155;
        font-size: 12px;
        font-weight: 720;
        line-height: 1.2;
        box-shadow: 0 6px 14px rgba(15, 23, 42, 0.024);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-panel {
        display: grid;
        align-content: start;
        gap: 10px;
        padding: 14px;
        border: 1px solid rgba(226, 232, 240, 0.94);
        border-radius: 15px;
        background: rgba(255, 255, 255, 0.84);
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.026);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-panel h3 {
        margin: 0;
        color: #0f172a;
        font-size: 13px;
        font-weight: 760;
        line-height: 1.25;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-items {
        display: grid;
        gap: 7px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-planned {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        min-height: 36px;
        padding: 8px 10px;
        border: 1px solid rgba(226, 232, 240, 0.9);
        border-radius: 11px;
        background: #f8fafc;
        color: #334155;
        font-size: 12px;
        font-weight: 680;
        line-height: 1.25;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-planned::after {
        content: "Planned";
        color: #64748b;
        font-size: 10px;
        font-weight: 760;
        letter-spacing: 0.025em;
        text-transform: uppercase;
        white-space: nowrap;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-evidence-grid,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-owner-grid,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-policy-grid {
        display: grid;
        align-content: start;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-mini {
        display: flex;
        flex-direction: column;
        justify-content: center;
        min-height: 44px;
        padding: 9px 10px;
        border: 1px solid rgba(226, 232, 240, 0.9);
        border-radius: 11px;
        background: #ffffff;
        color: #334155;
        font-size: 12px;
        font-weight: 680;
        line-height: 1.28;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-mini span {
        display: block;
        margin-top: 3px;
        color: #64748b;
        font-size: 11px;
        font-weight: 600;
        line-height: 1.35;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-evidence-grid .warehouse-customer-return-mini:nth-child(odd):last-child {
        grid-column: 1 / -1;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-policy-panel {
        grid-column: 1 / -1;
      }

      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-shell.warehouse-supplier-return-shell {
        background:
          linear-gradient(180deg, rgba(239, 246, 255, 0.62) 0%, rgba(255, 255, 255, 0.98) 36%),
          #ffffff;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-shell.warehouse-supplier-return-shell::before {
        background: rgba(37, 99, 235, 0.42);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-supplier-return-shell .warehouse-customer-return-badge {
        border-color: rgba(37, 99, 235, 0.2);
        background: rgba(239, 246, 255, 0.9);
        color: #1d4ed8;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-supplier-return-shell .warehouse-customer-return-guardrail {
        border-color: rgba(37, 99, 235, 0.24);
        background: rgba(239, 246, 255, 0.56);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-shell.warehouse-internal-transfer-shell {
        background:
          linear-gradient(180deg, rgba(236, 253, 245, 0.66) 0%, rgba(255, 255, 255, 0.98) 36%),
          #ffffff;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-shell.warehouse-internal-transfer-shell::before {
        background: rgba(20, 184, 166, 0.48);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-internal-transfer-shell .warehouse-customer-return-badge {
        border-color: rgba(20, 184, 166, 0.22);
        background: rgba(240, 253, 250, 0.92);
        color: #0f766e;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-internal-transfer-shell .warehouse-customer-return-guardrail {
        border-color: rgba(20, 184, 166, 0.26);
        background: rgba(240, 253, 250, 0.62);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-planned-workflows {
        display: grid;
        gap: 14px;
        padding: 18px 20px 20px;
        border: 1px solid rgba(203, 213, 225, 0.94);
        border-radius: 18px;
        background:
          linear-gradient(180deg, rgba(248, 250, 252, 0.88) 0%, rgba(255, 255, 255, 0.98) 42%),
          #ffffff;
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 12px 28px rgba(15, 23, 42, 0.04);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-planned-workflows-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 14px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-planned-workflows-copy {
        display: grid;
        gap: 5px;
        min-width: 0;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-planned-workflows-title {
        margin: 0;
        color: #0f172a;
        font-size: 17px;
        font-weight: 780;
        line-height: 1.25;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-planned-workflows-subtitle {
        max-width: 760px;
        color: #52637a;
        font-size: 12.5px;
        line-height: 1.48;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-planned-workflows-mode {
        display: inline-flex;
        align-items: center;
        min-height: 28px;
        padding: 0 10px;
        border: 1px solid rgba(148, 163, 184, 0.34);
        border-radius: 999px;
        background: rgba(248, 250, 252, 0.9);
        color: #475569;
        font-size: 11px;
        font-weight: 760;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        white-space: nowrap;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-planned-workflows-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 10px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-planned-workflow-card {
        display: grid;
        gap: 10px;
        min-height: 166px;
        padding: 14px;
        border: 1px solid rgba(226, 232, 240, 0.94);
        border-radius: 15px;
        background: rgba(255, 255, 255, 0.9);
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.028);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-planned-workflow-card.is-expanded {
        border-color: rgba(20, 184, 166, 0.34);
        box-shadow: 0 12px 26px rgba(15, 118, 110, 0.08);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-planned-workflow-card-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 10px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-planned-workflow-title {
        color: #0f172a;
        font-size: 13px;
        font-weight: 760;
        line-height: 1.25;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-planned-workflow-kicker {
        display: inline-flex;
        align-items: center;
        min-height: 22px;
        padding: 0 8px;
        border-radius: 999px;
        background: #f8fafc;
        color: #64748b;
        font-size: 10px;
        font-weight: 760;
        letter-spacing: 0.025em;
        text-transform: uppercase;
        white-space: nowrap;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-planned-workflow-note,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-planned-workflow-guardrail {
        color: #52637a;
        font-size: 12px;
        line-height: 1.42;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-planned-workflow-guardrail {
        padding: 9px 10px;
        border: 1px dashed rgba(203, 213, 225, 0.9);
        border-radius: 12px;
        background: rgba(248, 250, 252, 0.78);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-planned-workflow-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-planned-workflow-meta span {
        display: inline-flex;
        align-items: center;
        min-height: 22px;
        padding: 0 8px;
        border: 1px solid rgba(226, 232, 240, 0.9);
        border-radius: 999px;
        color: #64748b;
        font-size: 10.5px;
        font-weight: 700;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-planned-workflow-toggle {
        justify-self: start;
        min-height: 30px;
        padding: 0 11px;
        border: 1px solid rgba(203, 213, 225, 0.95);
        border-radius: 999px;
        background: #ffffff;
        color: #0f172a;
        font-size: 11px;
        font-weight: 760;
        cursor: pointer;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-planned-workflow-toggle:hover {
        border-color: rgba(20, 184, 166, 0.38);
        color: #0f766e;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-planned-workflow-details {
        display: grid;
        gap: 12px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-planned-workflow-detail[hidden] {
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-planned-workflow-detail > .warehouse-customer-return-shell {
        margin-top: 0;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.026);
      }
      /* W15B overview hierarchy refinement: status, navigation, task, risk, movement, and control lanes must read differently. */
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-pulse-section {
        border-color: rgba(226, 232, 240, 0.92);
        background: linear-gradient(180deg, #ffffff 0%, #fbfcff 100%);
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 10px 24px rgba(15, 23, 42, 0.028);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-pulse-section .sales-console-section-title::after {
        content: "Status";
        margin-left: 9px;
        padding: 2px 7px;
        border: 1px solid rgba(203, 213, 225, 0.86);
        border-radius: 999px;
        color: #64748b;
        font-size: 9px;
        font-weight: 760;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        vertical-align: middle;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-start {
        border-color: rgba(204, 251, 241, 0.82);
        background:
          linear-gradient(180deg, rgba(240, 253, 250, 0.44) 0%, rgba(255, 255, 255, 0.98) 44%),
          #ffffff;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-start::before,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared [data-warehouse-cockpit-work]::before,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared [data-warehouse-cockpit-risk]::before,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared [data-warehouse-cockpit-movement]::before,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-section::before {
        content: "";
        display: block;
        width: 42px;
        height: 2px;
        margin: 0 0 14px;
        border-radius: 999px;
        background: rgba(20, 184, 166, 0.5);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared [data-warehouse-cockpit-work] {
        border-color: rgba(204, 251, 241, 0.86);
        background: linear-gradient(180deg, rgba(240, 253, 250, 0.5) 0%, #ffffff 42%);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared [data-warehouse-cockpit-risk] {
        border-color: rgba(253, 230, 138, 0.88);
        background: linear-gradient(180deg, rgba(255, 251, 235, 0.72) 0%, #ffffff 46%);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared [data-warehouse-cockpit-risk]::before {
        background: rgba(217, 119, 6, 0.62);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared [data-warehouse-cockpit-movement] {
        border-color: rgba(191, 219, 254, 0.9);
        background: linear-gradient(180deg, rgba(239, 246, 255, 0.72) 0%, #ffffff 46%);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared [data-warehouse-cockpit-movement]::before {
        background: rgba(37, 99, 235, 0.5);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-work-card.sales-console-queue-card {
        border-left-color: rgba(20, 184, 166, 0.5);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared [data-warehouse-cockpit-risk] .warehouse-cockpit-queue-card.sales-console-queue-card {
        border-left-color: rgba(217, 119, 6, 0.5);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared [data-warehouse-cockpit-risk] .warehouse-cockpit-queue-card.sales-console-queue-card:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared [data-warehouse-cockpit-risk] button.warehouse-cockpit-queue-card.sales-console-queue-card:focus-visible {
        border-left-color: rgba(217, 119, 6, 0.72);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared [data-warehouse-cockpit-movement] .warehouse-cockpit-queue-card.sales-console-queue-card {
        border-left-color: rgba(37, 99, 235, 0.45);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared [data-warehouse-cockpit-movement] .warehouse-cockpit-queue-card.sales-console-queue-card:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared [data-warehouse-cockpit-movement] button.warehouse-cockpit-queue-card.sales-console-queue-card:focus-visible {
        border-left-color: rgba(37, 99, 235, 0.66);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-section {
        border-color: rgba(203, 213, 225, 0.94);
        background:
          linear-gradient(180deg, rgba(248, 250, 252, 0.92) 0%, #ffffff 38%),
          #ffffff;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-section::before {
        background: rgba(71, 85, 105, 0.48);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-groups {
        grid-template-columns: minmax(0, 1fr);
        align-items: start;
        gap: 16px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-group {
        padding: 13px;
        border: 1px solid rgba(226, 232, 240, 0.94);
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.78);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-group[data-warehouse-action-center-group='work_entry'] {
        background: linear-gradient(180deg, rgba(240, 253, 250, 0.48) 0%, rgba(255, 255, 255, 0.9) 46%);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-group[data-warehouse-action-center-group='manager_decisions'] {
        background: linear-gradient(180deg, rgba(248, 250, 252, 0.96) 0%, rgba(255, 255, 255, 0.92) 46%);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px 12px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-card.sales-console-queue-card {
        min-height: 94px;
        border-left-color: rgba(20, 184, 166, 0.42);
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.026);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-group[data-warehouse-action-center-group='manager_decisions'] .warehouse-action-center-card.is-live {
        border-left-color: rgba(37, 99, 235, 0.42);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-card.sales-console-queue-card.is-planned {
        border-style: dashed;
        border-left-style: solid;
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        opacity: 0.9;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-card.sales-console-queue-card.is-planned:hover {
        transform: none;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.026);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-card.is-planned .sales-console-queue-count {
        color: #64748b;
        font-size: 13px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-card-action {
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-guardrail {
        padding: 13px 16px;
        border-style: dashed;
        background: #f8fafc;
        color: #475569;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-guardrail .warehouse-visual-guardrail-title {
        color: #0f172a;
      }
      @media (max-width: 740px) {
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-command-row,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-console-kpi-grid.sales-console-kpi-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-pulse-grid-secondary,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-start-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-route-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-work-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-planned-workflows-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-status-strip,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-evidence-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-owner-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-policy-grid {
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-customer-return-head,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-planned-workflows-head {
          display: grid;
          align-items: start;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-start-grid .sales-console-action-strip.primary,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-start-grid .sales-console-action-strip.secondary {
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-section-head {
          display: grid;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-section-note {
          max-width: none;
          text-align: left;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-pulse-tools {
          justify-content: flex-start;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-work-card.sales-console-queue-card,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-queue-card.sales-console-queue-card,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-card.sales-console-queue-card {
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-work-card .sales-console-queue-side,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-queue-card .sales-console-queue-side,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-side {
          width: 100%;
          min-height: 58px;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-group-head,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-guardrail {
          display: grid;
          align-items: start;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-action-center-group-head p {
          max-width: none;
          text-align: left;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-header-context,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-cockpit-chip-row {
          justify-items: start;
          justify-content: flex-start;
        }
      }
      /* Inbound Receiving Queue: confirmed Overview card standard, scoped to this queue only. */
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) {
        width: min(1120px, calc(100% - 24px));
        padding: 20px 0 30px;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
        overflow: visible;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-queue-header {
        display: grid;
        gap: 13px;
        padding: 2px 0 0;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-queue-head {
        display: grid;
        grid-template-columns: minmax(0, 1fr);
        align-items: start;
        gap: 8px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-queue-eyebrow {
        color: #475569;
        font-size: 11px;
        font-weight: 760;
        letter-spacing: 0.055em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-queue-title {
        margin-top: 2px;
        color: #020617;
        font-size: 28px;
        font-weight: 720;
        line-height: 1.08;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-queue-note {
        max-width: 640px;
        margin-top: 9px;
        color: #52637a;
        font-size: 13px;
        line-height: 1.48;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-chip-row {
        margin-top: 14px;
        gap: 7px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-chip {
        min-height: 24px;
        padding: 0 9px;
        border-color: rgba(203, 213, 225, 0.92);
        background: #f8fafc;
        color: #334155;
        font-size: 10.5px;
        letter-spacing: 0.02em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-chip.is-read-only {
        border-color: rgba(20, 184, 166, 0.28);
        background: #f0fdfa;
        color: #0f766e;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-queue-cards {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 14px;
        margin-top: 6px;
        padding: 0;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-queue-card {
        position: relative;
        min-height: 102px;
        padding: 16px 16px 16px 17px;
        border: 1px solid rgba(236, 242, 249, 0.86);
        border-radius: 18px;
        background: linear-gradient(145deg, #ffffff 0%, #ffffff 48%, #fbfdff 100%);
        box-shadow:
          0 1px 0 rgba(255, 255, 255, 1) inset,
          0 44px 88px rgba(255, 255, 255, 0.98),
          0 30px 64px rgba(148, 163, 184, 0.28),
          0 14px 30px rgba(15, 23, 42, 0.075);
        cursor: default;
        transition: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-queue-card::before {
        content: none;
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-queue-card::after {
        content: none;
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-queue-card:first-child {
        border-left: 1px solid rgba(236, 242, 249, 0.86);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-queue-card[data-warehouse-inbound-queue-card="overdue"] {
        border-color: rgba(236, 242, 249, 0.86);
        background: linear-gradient(145deg, #ffffff 0%, #ffffff 48%, #fbfdff 100%);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-queue-card:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-queue-card:focus,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-queue-card:focus-visible {
        border-color: rgba(236, 242, 249, 0.86);
        box-shadow:
          0 1px 0 rgba(255, 255, 255, 1) inset,
          0 44px 88px rgba(255, 255, 255, 0.98),
          0 30px 64px rgba(148, 163, 184, 0.28),
          0 14px 30px rgba(15, 23, 42, 0.075);
        transform: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-queue-card-label,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-field label {
        color: #475569;
        font-size: 10.5px;
        font-weight: 760;
        letter-spacing: 0.018em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-queue-card-label {
        display: block;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-queue-card-value {
        display: block;
        min-height: 0;
        margin-top: 8px;
        padding: 0;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
        color: #020617;
        font-size: 23px;
        font-weight: 740;
        line-height: 1;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-queue-card-note {
        margin-top: 7px;
        color: #52637a;
        font-size: 11.5px;
        line-height: 1.38;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-controls {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr)) auto auto auto;
        align-items: end;
        gap: 8px;
        padding: 12px;
        border: 1px solid rgba(226, 232, 240, 0.92);
        border-radius: 14px;
        background: #ffffff;
        box-shadow: 0 6px 14px rgba(15, 23, 42, 0.022);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-controls.is-loading {
        grid-template-columns: repeat(4, minmax(0, 1fr));
        align-items: stretch;
        background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-loading-field {
        display: grid;
        gap: 7px;
        min-width: 0;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-loading-field span {
        color: #64748b;
        font-size: 10.5px;
        font-weight: 760;
        letter-spacing: 0.018em;
        line-height: 1.22;
        text-transform: uppercase;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-loading-field i {
        display: block;
        width: 100%;
        height: 34px;
        border: 1px solid rgba(233, 239, 247, 0.9);
        border-radius: 10px;
        background: linear-gradient(90deg, #ffffff 0%, #f7f9fc 50%, #ffffff 100%);
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 8px 18px rgba(255, 255, 255, 0.78);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-loading-status {
        grid-column: 1 / -1;
        color: #64748b;
        font-size: 12px;
        line-height: 1.4;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-field input,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-field select {
        height: 34px;
        border-color: rgba(203, 213, 225, 0.95);
        border-radius: 10px;
        background: #ffffff;
        color: #0f172a;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-field input:focus,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-field input:focus-visible,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-field select:focus,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-field select:focus-visible {
        outline: none;
        border-color: rgba(148, 163, 184, 0.95);
        box-shadow: 0 0 0 3px rgba(148, 163, 184, 0.14);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-queue-button {
        min-height: 34px;
        padding: 0 12px;
        border-color: rgba(203, 213, 225, 0.95);
        border-radius: 10px;
        background: #ffffff;
        color: #1e293b;
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 5px 12px rgba(15, 23, 42, 0.025);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-queue-button:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-queue-button:focus-visible {
        border-color: rgba(148, 163, 184, 0.98);
        box-shadow: 0 10px 20px rgba(15, 23, 42, 0.055);
        transform: translateY(-1px);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-queue-guardrail {
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-group {
        padding: 0;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-group-title {
        color: #020617;
        font-size: 16px;
        font-weight: 720;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-group-note {
        color: #52637a;
        font-size: 12px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-visual-row-list {
        display: grid;
        gap: 12px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-row.is-receiving {
        display: grid;
        gap: 11px;
        padding: 16px 17px 16px 18px;
        border: 1px solid rgba(226, 232, 240, 0.82);
        border-left: 3px solid rgba(20, 184, 166, 0.46);
        border-radius: 16px;
        background: #ffffff;
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.026);
        transition: border-color 140ms ease, border-left-width 140ms ease, box-shadow 140ms ease, transform 140ms ease;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-row.is-receiving:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-row.is-receiving:focus-within {
        border-color: rgba(203, 213, 225, 0.98);
        border-left-color: rgba(20, 184, 166, 0.66);
        border-left-width: 4px;
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 10px 22px rgba(15, 23, 42, 0.045);
        transform: translateY(-1px);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-row.warehouse-visual-fallback {
        min-height: 54px;
        padding: 15px 17px;
        border: 1px solid rgba(226, 232, 240, 0.82);
        border-left: 3px solid rgba(148, 163, 184, 0.34);
        border-radius: 16px;
        background: #ffffff;
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.026);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-row-summary {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: start;
        gap: 14px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-order {
        color: #020617;
        font-size: 14px;
        font-weight: 720;
        line-height: 1.25;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-meta {
        color: #52637a;
        font-size: 12px;
        line-height: 1.42;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-status-chip {
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-row-facts {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 8px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-row-fact {
        padding: 9px 11px;
        border: 1px solid rgba(226, 232, 240, 0.78);
        border-radius: 12px;
        background: #fbfdff;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-row-fact span {
        color: #64748b;
        font-size: 10px;
        font-weight: 760;
        letter-spacing: 0.018em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-row-fact strong {
        margin-top: 5px;
        color: #020617;
        font-size: 12.5px;
        font-weight: 700;
        line-height: 1.3;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-lines {
        gap: 7px;
        padding: 13px 11px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-line {
        padding: 3px 0;
        line-height: 1.45;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-row-actions {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
      }
      @media (max-width: 900px) {
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-queue-cards,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-controls,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-row-facts {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
      }
      @media (max-width: 640px) {
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) {
          width: min(100%, calc(100% - 12px));
          padding: 4px 0 24px;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-queue-head,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-queue-cards,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-controls,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-row-summary,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-row-facts {
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-row-actions {
          display: grid;
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-inbound-premium-shell:not(.warehouse-outbound-premium-shell) .warehouse-inbound-row-actions > button {
          width: 100%;
        }
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell {
        width: min(1120px, calc(100% - 24px));
        padding: 20px 0 30px;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
        overflow: visible;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-shell.warehouse-outbound-premium-shell {
        width: min(1120px, calc(100% - 24px));
        padding: 20px 0 30px;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
        overflow: visible;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-header {
        display: grid;
        gap: 13px;
        padding: 2px 0 0;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-head {
        display: grid;
        grid-template-columns: minmax(0, 1fr);
        align-items: start;
        gap: 8px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-title {
        margin-top: 2px;
        color: #020617;
        font-size: 28px;
        font-weight: 720;
        line-height: 1.08;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-note {
        max-width: 640px;
        margin-top: 9px;
        color: #52637a;
        font-size: 13px;
        line-height: 1.48;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-chip-row,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-guardrail {
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-cards {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 14px;
        margin-top: 6px;
        padding: 0;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-card {
        position: relative;
        min-height: 102px;
        padding: 16px 16px 16px 17px;
        border: 1px solid rgba(236, 242, 249, 0.86);
        border-radius: 18px;
        background: linear-gradient(145deg, #ffffff 0%, #ffffff 48%, #fbfdff 100%);
        box-shadow:
          0 1px 0 rgba(255, 255, 255, 1) inset,
          0 44px 88px rgba(255, 255, 255, 0.98),
          0 30px 64px rgba(148, 163, 184, 0.28),
          0 14px 30px rgba(15, 23, 42, 0.075);
        cursor: default;
        transition: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-card::before,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-card::after {
        content: none;
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-card:first-child {
        border-left: 1px solid rgba(236, 242, 249, 0.86);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-card:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-card:focus,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-card:focus-visible {
        border-color: rgba(236, 242, 249, 0.86);
        box-shadow:
          0 1px 0 rgba(255, 255, 255, 1) inset,
          0 44px 88px rgba(255, 255, 255, 0.98),
          0 30px 64px rgba(148, 163, 184, 0.28),
          0 14px 30px rgba(15, 23, 42, 0.075);
        transform: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-card-label,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-field label {
        color: #475569;
        font-size: 10.5px;
        font-weight: 760;
        letter-spacing: 0.018em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-card-label {
        display: block;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-card-value {
        display: block;
        min-height: 0;
        margin-top: 8px;
        padding: 0;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
        color: #020617;
        font-size: 23px;
        font-weight: 740;
        line-height: 1;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-card-note {
        margin-top: 7px;
        color: #52637a;
        font-size: 11.5px;
        line-height: 1.38;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-controls {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr)) auto auto auto;
        align-items: end;
        gap: 8px;
        padding: 12px;
        border: 1px solid rgba(226, 232, 240, 0.86);
        border-radius: 16px;
        background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.035);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-controls.is-loading {
        grid-template-columns: repeat(4, minmax(0, 1fr));
        align-items: stretch;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-loading-field {
        display: grid;
        gap: 7px;
        min-width: 0;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-loading-field span {
        color: #475569;
        font-size: 10.5px;
        font-weight: 760;
        letter-spacing: 0.018em;
        text-transform: uppercase;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-loading-field i {
        display: block;
        width: 100%;
        height: 34px;
        border: 1px solid rgba(233, 239, 247, 0.9);
        border-radius: 10px;
        background: #ffffff;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-loading-status {
        grid-column: 1 / -1;
        color: #64748b;
        font-size: 12px;
        line-height: 1.4;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-field input,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-field select {
        height: 34px;
        border-color: rgba(203, 213, 225, 0.95);
        border-radius: 10px;
        background: #ffffff;
        color: #0f172a;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-field input:focus,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-field input:focus-visible,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-field select:focus,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-field select:focus-visible {
        outline: none;
        border-color: rgba(148, 163, 184, 0.95);
        box-shadow: 0 0 0 3px rgba(148, 163, 184, 0.14);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-button {
        min-height: 34px;
        padding: 0 12px;
        border-color: rgba(203, 213, 225, 0.95);
        border-radius: 10px;
        background: #ffffff;
        color: #1e293b;
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 5px 12px rgba(15, 23, 42, 0.025);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-button:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-button:focus-visible {
        border-color: rgba(148, 163, 184, 0.98);
        box-shadow: 0 10px 20px rgba(15, 23, 42, 0.055);
        transform: translateY(-1px);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-group {
        padding: 0;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-group-title {
        color: #020617;
        font-size: 16px;
        font-weight: 720;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-group-note {
        color: #52637a;
        font-size: 12px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-visual-row-list {
        display: grid;
        gap: 12px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-row.is-picking {
        display: grid;
        gap: 11px;
        padding: 16px 17px 16px 18px;
        border: 1px solid rgba(226, 232, 240, 0.82);
        border-left: 3px solid rgba(20, 184, 166, 0.46);
        border-radius: 16px;
        background: #ffffff;
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.026);
        transition: border-color 140ms ease, border-left-width 140ms ease, box-shadow 140ms ease, transform 140ms ease;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-row.is-picking:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-row.is-picking:focus-within {
        border-color: rgba(203, 213, 225, 0.98);
        border-left-color: rgba(20, 184, 166, 0.66);
        border-left-width: 4px;
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 10px 22px rgba(15, 23, 42, 0.045);
        transform: translateY(-1px);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-row.warehouse-visual-fallback {
        min-height: 54px;
        padding: 15px 17px;
        border: 1px solid rgba(226, 232, 240, 0.82);
        border-left: 3px solid rgba(148, 163, 184, 0.34);
        border-radius: 16px;
        background: #ffffff;
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.026);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-row-summary {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: start;
        gap: 14px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-order {
        color: #020617;
        font-size: 14px;
        font-weight: 720;
        line-height: 1.25;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-meta {
        color: #52637a;
        font-size: 12px;
        line-height: 1.42;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-status-chip {
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-row-facts {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 8px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-row-fact {
        padding: 9px 11px;
        border: 1px solid rgba(226, 232, 240, 0.78);
        border-radius: 12px;
        background: #fbfdff;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-row-fact span {
        color: #64748b;
        font-size: 10px;
        font-weight: 760;
        letter-spacing: 0.018em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-row-fact strong {
        margin-top: 5px;
        color: #020617;
        font-size: 12.5px;
        font-weight: 700;
        line-height: 1.3;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-lines {
        gap: 7px;
        padding: 13px 11px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-line {
        padding: 3px 0;
        line-height: 1.45;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-row-actions {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
      }
      @media (max-width: 900px) {
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-cards,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-controls,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-row-facts {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
      }
      @media (max-width: 640px) {
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell {
          width: min(100%, calc(100% - 12px));
          padding: 4px 0 24px;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-head,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-cards,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-controls,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-row-summary,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-row-facts {
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-row-actions {
          display: grid;
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-row-actions > button {
          width: 100%;
        }
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell {
        width: min(1120px, calc(100% - 24px));
        padding: 20px 0 30px;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
        overflow: visible;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-queue-header {
        display: grid;
        gap: 13px;
        padding: 2px 0 0;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-queue-head {
        display: grid;
        grid-template-columns: minmax(0, 1fr);
        align-items: start;
        gap: 8px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-queue-title {
        margin-top: 2px;
        color: #020617;
        font-size: 28px;
        font-weight: 720;
        line-height: 1.08;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-queue-note {
        max-width: 680px;
        margin-top: 9px;
        color: #52637a;
        font-size: 13px;
        line-height: 1.48;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-chip-row,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-stock-exception-guardrail {
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-queue-cards {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 14px;
        margin-top: 6px;
        padding: 0;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-queue-card {
        position: relative;
        min-height: 102px;
        padding: 16px 16px 16px 17px;
        border: 1px solid rgba(236, 242, 249, 0.86);
        border-radius: 18px;
        background: linear-gradient(145deg, #ffffff 0%, #ffffff 48%, #fbfdff 100%);
        box-shadow:
          0 1px 0 rgba(255, 255, 255, 1) inset,
          0 44px 88px rgba(255, 255, 255, 0.98),
          0 30px 64px rgba(148, 163, 184, 0.28),
          0 14px 30px rgba(15, 23, 42, 0.075);
        cursor: default;
        transition: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-queue-card::before,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-queue-card::after {
        content: none;
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-queue-card:first-child {
        border-left: 1px solid rgba(236, 242, 249, 0.86);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-queue-card:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-queue-card:focus,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-queue-card:focus-visible {
        border-color: rgba(236, 242, 249, 0.86);
        box-shadow:
          0 1px 0 rgba(255, 255, 255, 1) inset,
          0 44px 88px rgba(255, 255, 255, 0.98),
          0 30px 64px rgba(148, 163, 184, 0.28),
          0 14px 30px rgba(15, 23, 42, 0.075);
        transform: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-queue-card-label,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-field label {
        color: #475569;
        font-size: 10.5px;
        font-weight: 760;
        letter-spacing: 0.018em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-queue-card-value {
        display: block;
        min-height: 0;
        margin-top: 8px;
        padding: 0;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
        color: #020617;
        font-size: 23px;
        font-weight: 740;
        line-height: 1;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-queue-card-note {
        margin-top: 7px;
        color: #52637a;
        font-size: 11.5px;
        line-height: 1.38;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-controls {
        display: grid;
        grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1.18fr) auto auto auto;
        align-items: end;
        gap: 8px;
        padding: 12px;
        border: 1px solid rgba(226, 232, 240, 0.86);
        border-radius: 16px;
        background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.035);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-controls.is-loading {
        grid-template-columns: repeat(4, minmax(0, 1fr));
        align-items: stretch;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-loading-field {
        display: grid;
        gap: 7px;
        min-width: 0;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-loading-field span {
        color: #475569;
        font-size: 10.5px;
        font-weight: 760;
        letter-spacing: 0.018em;
        text-transform: uppercase;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-loading-field i {
        display: block;
        width: 100%;
        height: 34px;
        border: 1px solid rgba(233, 239, 247, 0.9);
        border-radius: 10px;
        background: #ffffff;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-loading-status {
        grid-column: 1 / -1;
        color: #64748b;
        font-size: 12px;
        line-height: 1.4;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-field input,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-field select {
        height: 34px;
        border-color: rgba(203, 213, 225, 0.95);
        border-radius: 10px;
        background: #ffffff;
        color: #0f172a;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-field input:focus,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-field input:focus-visible,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-field select:focus,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-field select:focus-visible {
        outline: none;
        border-color: rgba(148, 163, 184, 0.95);
        box-shadow: 0 0 0 3px rgba(148, 163, 184, 0.14);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-queue-button {
        min-height: 34px;
        padding: 0 12px;
        border-color: rgba(203, 213, 225, 0.95);
        border-radius: 10px;
        background: #ffffff;
        color: #1e293b;
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 5px 12px rgba(15, 23, 42, 0.025);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-queue-button:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-queue-button:focus-visible {
        border-color: rgba(148, 163, 184, 0.98);
        box-shadow: 0 10px 20px rgba(15, 23, 42, 0.055);
        transform: translateY(-1px);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-group {
        padding: 0;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-group-title {
        color: #020617;
        font-size: 16px;
        font-weight: 720;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-group-note {
        color: #52637a;
        font-size: 12px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-visual-row-list {
        display: grid;
        gap: 12px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-stock-exception-row.is-premium {
        display: grid;
        gap: 11px;
        padding: 16px 17px 16px 18px;
        border: 1px solid rgba(226, 232, 240, 0.82);
        border-left: 3px solid rgba(217, 119, 6, 0.42);
        border-radius: 16px;
        background: #ffffff;
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.026);
        transition: border-color 140ms ease, border-left-width 140ms ease, box-shadow 140ms ease, transform 140ms ease;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-stock-exception-row.warehouse-visual-fallback {
        min-height: 54px;
        padding: 15px 17px;
        border: 1px solid rgba(226, 232, 240, 0.82);
        border-left: 3px solid rgba(148, 163, 184, 0.34);
        border-radius: 16px;
        background: #ffffff;
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.026);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-stock-exception-row.is-premium:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-stock-exception-row.is-premium:focus-within {
        border-color: rgba(203, 213, 225, 0.98);
        border-left-color: rgba(217, 119, 6, 0.62);
        border-left-width: 4px;
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 10px 22px rgba(15, 23, 42, 0.045);
        transform: translateY(-1px);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-stock-exception-row-summary {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: start;
        gap: 14px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-order {
        color: #020617;
        font-size: 14px;
        font-weight: 720;
        line-height: 1.25;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-meta {
        color: #52637a;
        font-size: 12px;
        line-height: 1.42;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-status-chip {
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-stock-exception-facts {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 8px;
        padding-top: 0;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-stock-exception-fact {
        padding: 9px 11px;
        border: 1px solid rgba(226, 232, 240, 0.78);
        border-radius: 12px;
        background: #fbfdff;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-stock-exception-fact span {
        color: #64748b;
        font-size: 10px;
        font-weight: 760;
        letter-spacing: 0.018em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-stock-exception-fact strong {
        margin-top: 5px;
        color: #020617;
        font-size: 12.5px;
        font-weight: 700;
        line-height: 1.3;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-stock-exception-actions {
        display: flex;
        flex-wrap: wrap;
        justify-content: flex-end;
        gap: 8px;
        padding-top: 0;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-stock-exception-details {
        gap: 7px;
        padding: 13px 11px;
        border: 1px solid rgba(226, 232, 240, 0.78);
        border-radius: 12px;
        background: #fbfdff;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-stock-exception-detail {
        padding: 3px 0;
        border: 0;
        background: transparent;
        line-height: 1.45;
      }
      @media (max-width: 900px) {
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-queue-cards,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-controls,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-stock-exception-facts {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
      }
      @media (max-width: 640px) {
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell {
          width: min(100%, calc(100% - 12px));
          padding: 4px 0 24px;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-queue-head,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-queue-cards,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-controls,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-stock-exception-row-summary,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-stock-exception-facts {
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-stock-exception-actions {
          display: grid;
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-stock-exception-actions > button {
          width: 100%;
        }
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell {
        width: min(1120px, calc(100% - 24px));
        padding: 20px 0 30px;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
        overflow: visible;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-queue-header {
        display: grid;
        gap: 13px;
        padding: 2px 0 0;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-queue-head {
        display: grid;
        grid-template-columns: minmax(0, 1fr);
        align-items: start;
        gap: 8px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-queue-title {
        margin-top: 2px;
        color: #020617;
        font-size: 28px;
        font-weight: 720;
        line-height: 1.08;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-queue-note {
        max-width: 700px;
        margin-top: 9px;
        color: #52637a;
        font-size: 13px;
        line-height: 1.48;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-movement-chip-row,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-movement-guardrail,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-movement-command-grid {
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-queue-cards {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 14px;
        margin-top: 6px;
        padding: 0;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-queue-card {
        position: relative;
        min-height: 102px;
        padding: 16px 16px 16px 17px;
        border: 1px solid rgba(236, 242, 249, 0.86);
        border-radius: 18px;
        background: linear-gradient(145deg, #ffffff 0%, #ffffff 48%, #fbfdff 100%);
        box-shadow:
          0 1px 0 rgba(255, 255, 255, 1) inset,
          0 44px 88px rgba(255, 255, 255, 0.98),
          0 30px 64px rgba(148, 163, 184, 0.28),
          0 14px 30px rgba(15, 23, 42, 0.075);
        cursor: default;
        transition: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-queue-card::before,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-queue-card::after {
        content: none;
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-queue-card:first-child {
        border-left: 1px solid rgba(236, 242, 249, 0.86);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-queue-card:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-queue-card:focus,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-queue-card:focus-visible {
        border-color: rgba(236, 242, 249, 0.86);
        box-shadow:
          0 1px 0 rgba(255, 255, 255, 1) inset,
          0 44px 88px rgba(255, 255, 255, 0.98),
          0 30px 64px rgba(148, 163, 184, 0.28),
          0 14px 30px rgba(15, 23, 42, 0.075);
        transform: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-queue-card-label,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-field label {
        color: #475569;
        font-size: 10.5px;
        font-weight: 760;
        letter-spacing: 0.018em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-queue-card-value {
        display: block;
        min-height: 0;
        margin-top: 8px;
        padding: 0;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
        color: #020617;
        font-size: 23px;
        font-weight: 740;
        line-height: 1;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-queue-card-note {
        margin-top: 7px;
        color: #52637a;
        font-size: 11.5px;
        line-height: 1.38;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-controls {
        display: grid;
        grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1.18fr) auto auto auto;
        align-items: end;
        gap: 8px;
        padding: 12px;
        border: 1px solid rgba(226, 232, 240, 0.86);
        border-radius: 16px;
        background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.035);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-controls.is-loading {
        grid-template-columns: repeat(4, minmax(0, 1fr));
        align-items: stretch;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-loading-field {
        display: grid;
        gap: 7px;
        min-width: 0;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-loading-field span {
        color: #475569;
        font-size: 10.5px;
        font-weight: 760;
        letter-spacing: 0.018em;
        text-transform: uppercase;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-loading-field i {
        display: block;
        width: 100%;
        height: 34px;
        border: 1px solid rgba(233, 239, 247, 0.9);
        border-radius: 10px;
        background: #ffffff;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-loading-status {
        grid-column: 1 / -1;
        color: #64748b;
        font-size: 12px;
        line-height: 1.4;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-field input,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-field select {
        height: 34px;
        border-color: rgba(203, 213, 225, 0.95);
        border-radius: 10px;
        background: #ffffff;
        color: #0f172a;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-field input:focus,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-field input:focus-visible,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-field select:focus,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-field select:focus-visible {
        outline: none;
        border-color: rgba(148, 163, 184, 0.95);
        box-shadow: 0 0 0 3px rgba(148, 163, 184, 0.14);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-queue-button {
        min-height: 34px;
        padding: 0 12px;
        border-color: rgba(203, 213, 225, 0.95);
        border-radius: 10px;
        background: #ffffff;
        color: #1e293b;
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 5px 12px rgba(15, 23, 42, 0.025);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-queue-button:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-queue-button:focus-visible {
        border-color: rgba(148, 163, 184, 0.98);
        box-shadow: 0 10px 20px rgba(15, 23, 42, 0.055);
        transform: translateY(-1px);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-group {
        padding: 0;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-group-title {
        color: #020617;
        font-size: 16px;
        font-weight: 720;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-group-note {
        color: #52637a;
        font-size: 12px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-visual-row-list {
        display: grid;
        gap: 12px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-movement-row.is-premium {
        display: grid;
        gap: 11px;
        padding: 16px 17px 16px 18px;
        border: 1px solid rgba(226, 232, 240, 0.82);
        border-left: 3px solid rgba(15, 118, 110, 0.44);
        border-radius: 16px;
        background: #ffffff;
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.026);
        transition: border-color 140ms ease, border-left-width 140ms ease, box-shadow 140ms ease, transform 140ms ease;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-stock-exception-row.warehouse-visual-fallback {
        min-height: 54px;
        padding: 15px 17px;
        border: 1px solid rgba(226, 232, 240, 0.82);
        border-left: 3px solid rgba(148, 163, 184, 0.34);
        border-radius: 16px;
        background: #ffffff;
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.026);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-movement-row.is-premium:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-movement-row.is-premium:focus-within {
        border-color: rgba(203, 213, 225, 0.98);
        border-left-color: rgba(15, 118, 110, 0.62);
        border-left-width: 4px;
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 10px 22px rgba(15, 23, 42, 0.045);
        transform: translateY(-1px);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-movement-row-main {
        display: grid;
        grid-template-columns: minmax(0, 1fr) minmax(0, 0.72fr) minmax(0, 1fr) minmax(0, 0.72fr) auto;
        align-items: start;
        gap: 14px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-order {
        color: #020617;
        font-size: 14px;
        font-weight: 720;
        line-height: 1.25;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-meta {
        color: #52637a;
        font-size: 12px;
        line-height: 1.42;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-badge {
        display: inline-flex;
        align-items: center;
        min-height: 24px;
        border-color: rgba(203, 213, 225, 0.82);
        background: #f8fafc;
        color: #334155;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-movement-row-facts {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 8px;
        padding-top: 0;
        border-top: 0;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-movement-row-fact {
        padding: 9px 11px;
        border: 1px solid rgba(226, 232, 240, 0.78);
        border-radius: 12px;
        background: #fbfdff;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-movement-row-fact span {
        color: #64748b;
        font-size: 10px;
        font-weight: 760;
        letter-spacing: 0.018em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-movement-row-fact strong {
        margin-top: 5px;
        color: #020617;
        font-size: 12.5px;
        font-weight: 700;
        line-height: 1.3;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-movement-actions {
        display: flex;
        flex-wrap: wrap;
        justify-content: flex-end;
        gap: 8px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-lines {
        gap: 7px;
        padding: 13px 11px;
        border: 1px solid rgba(226, 232, 240, 0.78);
        border-radius: 12px;
        background: #fbfdff;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-line {
        padding: 3px 0;
        line-height: 1.45;
      }
      @media (max-width: 900px) {
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-queue-cards,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-controls,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-movement-row-facts {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
      }
      @media (max-width: 640px) {
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell {
          width: min(100%, calc(100% - 12px));
          padding: 4px 0 24px;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-queue-head,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-queue-cards,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-controls,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-movement-row-main,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-movement-row-facts {
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-movement-actions {
          display: grid;
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-movement-actions > button {
          width: 100%;
        }
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell {
        width: min(1120px, calc(100% - 24px));
        padding: 20px 0 30px;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
        overflow: visible;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-queue-header {
        display: grid;
        gap: 13px;
        padding: 2px 0 0;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-queue-head {
        display: grid;
        grid-template-columns: minmax(0, 1fr);
        align-items: start;
        gap: 8px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-queue-title {
        margin-top: 2px;
        color: #020617;
        font-size: 28px;
        font-weight: 720;
        line-height: 1.08;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-queue-note {
        max-width: 700px;
        margin-top: 9px;
        color: #52637a;
        font-size: 13px;
        line-height: 1.48;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-transfer-chip-row,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-transfer-guardrail,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-transfer-command-grid {
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-queue-cards {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 14px;
        margin-top: 6px;
        padding: 0;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-queue-card {
        position: relative;
        min-height: 102px;
        padding: 16px 16px 16px 17px;
        border: 1px solid rgba(236, 242, 249, 0.86);
        border-radius: 18px;
        background: linear-gradient(145deg, #ffffff 0%, #ffffff 48%, #fbfdff 100%);
        box-shadow:
          0 1px 0 rgba(255, 255, 255, 1) inset,
          0 44px 88px rgba(255, 255, 255, 0.98),
          0 30px 64px rgba(148, 163, 184, 0.28),
          0 14px 30px rgba(15, 23, 42, 0.075);
        cursor: default;
        transition: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-queue-card::before,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-queue-card::after {
        content: none;
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-queue-card:first-child {
        border-left: 1px solid rgba(236, 242, 249, 0.86);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-queue-card:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-queue-card:focus,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-queue-card:focus-visible {
        border-color: rgba(236, 242, 249, 0.86);
        box-shadow:
          0 1px 0 rgba(255, 255, 255, 1) inset,
          0 44px 88px rgba(255, 255, 255, 0.98),
          0 30px 64px rgba(148, 163, 184, 0.28),
          0 14px 30px rgba(15, 23, 42, 0.075);
        transform: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-queue-card-label,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-field label {
        color: #475569;
        font-size: 10.5px;
        font-weight: 760;
        letter-spacing: 0.018em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-queue-card-value {
        display: block;
        min-height: 0;
        margin-top: 8px;
        padding: 0;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
        color: #020617;
        font-size: 23px;
        font-weight: 740;
        line-height: 1;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-queue-card-note {
        margin-top: 7px;
        color: #52637a;
        font-size: 11.5px;
        line-height: 1.38;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-controls {
        display: grid;
        grid-template-columns: minmax(0, 0.85fr) minmax(0, 0.85fr) minmax(0, 1.08fr) minmax(0, 1.08fr) minmax(0, 0.9fr) auto auto auto;
        align-items: end;
        gap: 8px;
        padding: 12px;
        border: 1px solid rgba(226, 232, 240, 0.86);
        border-radius: 16px;
        background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.035);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-controls.is-loading {
        grid-template-columns: repeat(4, minmax(0, 1fr));
        align-items: stretch;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-loading-field {
        display: grid;
        gap: 7px;
        min-width: 0;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-loading-field span {
        color: #475569;
        font-size: 10.5px;
        font-weight: 760;
        letter-spacing: 0.018em;
        text-transform: uppercase;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-loading-field i {
        display: block;
        width: 100%;
        height: 34px;
        border: 1px solid rgba(233, 239, 247, 0.9);
        border-radius: 10px;
        background: #ffffff;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-loading-status {
        grid-column: 1 / -1;
        color: #64748b;
        font-size: 12px;
        line-height: 1.4;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-field input,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-field select {
        height: 34px;
        border-color: rgba(203, 213, 225, 0.95);
        border-radius: 10px;
        background: #ffffff;
        color: #0f172a;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-field input:focus,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-field input:focus-visible,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-field select:focus,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-field select:focus-visible {
        outline: none;
        border-color: rgba(148, 163, 184, 0.95);
        box-shadow: 0 0 0 3px rgba(148, 163, 184, 0.14);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-queue-button {
        min-height: 34px;
        padding: 0 12px;
        border-color: rgba(203, 213, 225, 0.95);
        border-radius: 10px;
        background: #ffffff;
        color: #1e293b;
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 5px 12px rgba(15, 23, 42, 0.025);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-queue-button:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-queue-button:focus-visible {
        border-color: rgba(148, 163, 184, 0.98);
        box-shadow: 0 10px 20px rgba(15, 23, 42, 0.055);
        transform: translateY(-1px);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-group {
        padding: 0;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-group-title {
        color: #020617;
        font-size: 16px;
        font-weight: 720;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-group-note {
        color: #52637a;
        font-size: 12px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-visual-row-list {
        display: grid;
        gap: 12px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-transfer-row.is-premium {
        display: grid;
        gap: 11px;
        padding: 16px 17px 16px 18px;
        border: 1px solid rgba(226, 232, 240, 0.82);
        border-left: 3px solid rgba(15, 118, 110, 0.44);
        border-radius: 16px;
        background: #ffffff;
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.026);
        transition: border-color 140ms ease, border-left-width 140ms ease, box-shadow 140ms ease, transform 140ms ease;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-stock-exception-row.warehouse-visual-fallback {
        min-height: 54px;
        padding: 15px 17px;
        border: 1px solid rgba(226, 232, 240, 0.82);
        border-left: 3px solid rgba(148, 163, 184, 0.34);
        border-radius: 16px;
        background: #ffffff;
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.026);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-transfer-row.is-premium:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-transfer-row.is-premium:focus-within {
        border-color: rgba(203, 213, 225, 0.98);
        border-left-color: rgba(15, 118, 110, 0.62);
        border-left-width: 4px;
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 10px 22px rgba(15, 23, 42, 0.045);
        transform: translateY(-1px);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-transfer-row-main {
        display: grid;
        grid-template-columns: minmax(0, 1fr) minmax(0, 0.72fr) minmax(0, 1fr) minmax(0, 0.72fr) auto;
        align-items: start;
        gap: 14px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-order {
        color: #020617;
        font-size: 14px;
        font-weight: 720;
        line-height: 1.25;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-meta {
        color: #52637a;
        font-size: 12px;
        line-height: 1.42;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-badge {
        display: inline-flex;
        align-items: center;
        min-height: 24px;
        border-color: rgba(203, 213, 225, 0.82);
        background: #f8fafc;
        color: #334155;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-transfer-row-facts {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 8px;
        padding-top: 0;
        border-top: 0;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-transfer-row-fact {
        padding: 9px 11px;
        border: 1px solid rgba(226, 232, 240, 0.78);
        border-radius: 12px;
        background: #fbfdff;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-transfer-row-fact span {
        color: #64748b;
        font-size: 10px;
        font-weight: 760;
        letter-spacing: 0.018em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-transfer-row-fact strong {
        margin-top: 5px;
        color: #020617;
        font-size: 12.5px;
        font-weight: 700;
        line-height: 1.3;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-transfer-actions {
        display: flex;
        flex-wrap: wrap;
        justify-content: flex-end;
        gap: 8px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-lines {
        gap: 7px;
        padding: 13px 11px;
        border: 1px solid rgba(226, 232, 240, 0.78);
        border-radius: 12px;
        background: #fbfdff;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-line {
        padding: 3px 0;
        line-height: 1.45;
      }
      @media (max-width: 900px) {
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-queue-cards,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-controls,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-transfer-row-facts {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
      }
      @media (max-width: 640px) {
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell {
          width: min(100%, calc(100% - 12px));
          padding: 4px 0 24px;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-queue-head,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-queue-cards,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-controls,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-transfer-row-main,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-transfer-row-facts {
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-transfer-actions {
          display: grid;
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-transfer-actions > button {
          width: 100%;
        }
      }
      /* W13 top-level typography normalization: keep Warehouse close to Sales/Procurement scale. */
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-premium-shell,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell {
        font-family: inherit;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-console-title,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-premium-shell .warehouse-inbound-queue-title,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-title,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-queue-title,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-queue-title,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-queue-title {
        font-size: clamp(24px, 1.9vw, 26px);
        line-height: 1.12;
        font-weight: 700;
        letter-spacing: -0.018em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-console-kpi-value,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-console-inbound-card-value {
        font-size: 22px;
        line-height: 1.12;
        font-weight: 690;
        letter-spacing: -0.012em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-premium-shell .warehouse-inbound-queue-card-value,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-card-value,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-queue-card-value,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-queue-card-value,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-queue-card-value {
        font-size: 19px;
        line-height: 1.14;
        font-weight: 680;
        letter-spacing: -0.01em;
      }
      @media (max-width: 640px) {
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-console-title,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-premium-shell .warehouse-inbound-queue-title,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-title,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-queue-title,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-queue-title,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-queue-title {
          font-size: 24px;
          letter-spacing: -0.012em;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-console-kpi-value,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-overview-shared .warehouse-console-inbound-card-value,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-inbound-premium-shell .warehouse-inbound-queue-card-value,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-outbound-premium-shell .warehouse-inbound-queue-card-value,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-premium-shell .warehouse-inbound-queue-card-value,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-premium-shell .warehouse-inbound-queue-card-value,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-transfer-premium-shell .warehouse-inbound-queue-card-value {
          font-size: 20px;
        }
      }
      /* Receiving Review premium alignment with confirmed Warehouse queue style. */
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] {
        width: min(1120px, calc(100% - 24px));
        padding: 20px 0 30px;
        border: 0;
        background: #ffffff;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-header {
        gap: 18px;
        padding: 0;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-head {
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 18px;
        align-items: start;
        padding-top: 4px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-eyebrow,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-chip-row {
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-title {
        color: #020617;
        font-size: clamp(24px, 1.9vw, 26px);
        font-weight: 700;
        line-height: 1.12;
        letter-spacing: -0.018em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-subtitle {
        max-width: 720px;
        margin-top: 8px;
        color: #475569;
        font-size: 13px;
        line-height: 1.5;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-actions {
        gap: 8px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-button {
        min-height: 34px;
        padding: 0 13px;
        border-color: rgba(203, 213, 225, 0.98);
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.94);
        color: #0f172a;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.035);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-button:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-button:focus-visible {
        border-color: rgba(148, 163, 184, 0.92);
        box-shadow: 0 10px 22px rgba(15, 23, 42, 0.055);
        transform: translateY(-1px);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-command-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0;
        overflow: hidden;
        margin-top: 4px;
        border: 1px solid rgba(226, 232, 240, 0.92);
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.92);
        box-shadow:
          0 14px 32px rgba(15, 23, 42, 0.035),
          inset 0 1px 0 rgba(255, 255, 255, 0.9);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-command-fact {
        padding: 14px 16px;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-command-fact + .warehouse-receiving-command-fact {
        border-left: 1px solid rgba(226, 232, 240, 0.88);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-command-fact span,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-card-label,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-line-fact span {
        color: #52637a;
        font-size: 10px;
        font-weight: 760;
        letter-spacing: 0.018em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-command-fact strong {
        margin-top: 6px;
        color: #020617;
        font-size: 13px;
        font-weight: 690;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-posture-panel {
        display: grid;
        gap: 14px;
        margin-top: 18px;
        padding: 16px;
        border: 1px solid rgba(226, 232, 240, 0.72);
        border-radius: 22px;
        background: #ffffff;
        box-shadow:
          0 24px 52px rgba(15, 23, 42, 0.055),
          0 8px 18px rgba(15, 23, 42, 0.028),
          inset 0 1px 0 rgba(255, 255, 255, 0.94);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-posture-head {
        display: flex;
        justify-content: space-between;
        gap: 14px;
        align-items: flex-start;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-posture-title {
        margin: 0;
        color: #020617;
        font-size: 17px;
        font-weight: 720;
        letter-spacing: -0.006em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-posture-note {
        margin-top: 5px;
        color: #64748b;
        font-size: 12px;
        line-height: 1.35;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-posture-layout {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-posture-block {
        display: grid;
        gap: 9px;
        min-width: 0;
        padding: 11px;
        border: 1px solid rgba(226, 232, 240, 0.62);
        border-radius: 17px;
        background: #fbfcfe;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-posture-kicker {
        color: #52637a;
        font-size: 10px;
        font-weight: 780;
        letter-spacing: 0.022em;
        text-transform: uppercase;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-posture-block .warehouse-receiving-readiness,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-posture-block .warehouse-receiving-cards {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px;
        margin: 0;
        background: transparent;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-readiness-card,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-card {
        min-height: 82px;
        padding: 12px 13px;
        border: 1px solid rgba(226, 232, 240, 0.58);
        border-radius: 14px;
        background: #ffffff;
        box-shadow:
          0 9px 18px rgba(15, 23, 42, 0.026),
          inset 0 1px 0 rgba(255, 255, 255, 0.92);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-card-value {
        margin-top: 5px;
        color: #020617;
        font-size: 18px;
        font-weight: 690;
        line-height: 1.12;
        letter-spacing: -0.01em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-card-note {
        margin-top: 5px;
        color: #52637a;
        font-size: 11.5px;
        line-height: 1.35;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-note {
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-guardrail {
        display: inline-flex;
        width: fit-content;
        max-width: 100%;
        gap: 8px;
        margin-top: 8px;
        margin-bottom: 4px;
        padding: 7px 11px;
        border: 1px solid rgba(226, 232, 240, 0.82);
        border-radius: 999px;
        background: rgba(248, 250, 252, 0.78);
        color: #52637a;
        font-size: 11.5px;
        line-height: 1.3;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-guardrail strong {
        color: #334155;
        font-weight: 760;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-detail {
        gap: 16px;
        margin-top: 18px;
        padding: 18px;
        border: 1px solid rgba(226, 232, 240, 0.84);
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.94);
        box-shadow: 0 18px 44px rgba(15, 23, 42, 0.045);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-detail-head {
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 14px;
        align-items: start;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-section-title {
        color: #020617;
        font-size: 17px;
        font-weight: 720;
        letter-spacing: -0.006em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-tab {
        min-height: 34px;
        padding: 0 13px;
        border-color: rgba(203, 213, 225, 0.9);
        border-radius: 12px;
        background: #ffffff;
        color: #334155;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.025);
        cursor: pointer;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-tab.is-active {
        border-color: rgba(20, 184, 166, 0.32);
        background: rgba(240, 253, 250, 0.82);
        color: #0f766e;
        box-shadow: 0 10px 22px rgba(15, 118, 110, 0.055);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-panel {
        gap: 15px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-panel:not(.is-active) {
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-panel.is-active {
        display: grid;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-line,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-history-row {
        position: relative;
        gap: 12px;
        padding: 16px 17px 16px 18px;
        border: 1px solid rgba(226, 232, 240, 0.72);
        border-radius: 18px;
        background:
          radial-gradient(circle at 4% 0%, rgba(255, 255, 255, 0.92), transparent 34%),
          linear-gradient(180deg, #f8fbff 0%, #f5f8fc 100%);
        box-shadow:
          0 16px 34px rgba(15, 23, 42, 0.045),
          inset 0 1px 0 rgba(255, 255, 255, 0.9);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-line.is-blocked {
        border-color: rgba(226, 232, 240, 0.72);
        background:
          radial-gradient(circle at 4% 0%, rgba(255, 255, 255, 0.92), transparent 34%),
          linear-gradient(180deg, #f8fbff 0%, #f5f8fc 100%);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-line:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-history-row:hover {
        border-color: rgba(226, 232, 240, 0.72);
        box-shadow:
          0 16px 34px rgba(15, 23, 42, 0.045),
          inset 0 1px 0 rgba(255, 255, 255, 0.9);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-line-facts {
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 8px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-line-fact {
        padding: 10px 11px;
        border: 1px solid rgba(226, 232, 240, 0.82);
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.96);
        box-shadow:
          0 6px 14px rgba(15, 23, 42, 0.025),
          inset 0 1px 0 rgba(255, 255, 255, 0.88);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-line-fact strong {
        margin-top: 5px;
        color: #020617;
        font-size: 12.5px;
        font-weight: 690;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-line-status {
        border-color: rgba(203, 213, 225, 0.88);
        border-radius: 999px;
        background: #ffffff;
        color: #334155;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] {
        width: min(1120px, calc(100% - 48px));
        padding: 18px 0 34px;
        background: #ffffff;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-header {
        gap: 18px;
        margin-bottom: 24px;
        padding: 0;
        border: 0;
        border-radius: 0;
        background: #ffffff;
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-head {
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: start;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-eyebrow {
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-title {
        color: #020617;
        font-size: clamp(24px, 1.9vw, 26px);
        font-weight: 700;
        line-height: 1.12;
        letter-spacing: -0.018em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-subtitle {
        max-width: 720px;
        margin-top: 8px;
        color: #475569;
        font-size: 13px;
        line-height: 1.5;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-chip-row {
        display: flex;
        margin-top: 4px;
        gap: 6px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-chip {
        min-height: 22px;
        padding: 0 8px;
        border-color: rgba(203, 213, 225, 0.78);
        background: rgba(248, 250, 252, 0.74);
        color: #475569;
        font-size: 10.5px;
        font-weight: 680;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-chip.is-read-only {
        border-color: rgba(20, 184, 166, 0.22);
        background: rgba(240, 253, 250, 0.72);
        color: #0f766e;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-actions {
        gap: 8px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-button {
        min-height: 34px;
        padding: 0 13px;
        border-color: rgba(203, 213, 225, 0.98);
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.94);
        color: #0f172a;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.035);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-button:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-button:focus-visible {
        border-color: rgba(148, 163, 184, 0.92);
        box-shadow: 0 10px 22px rgba(15, 23, 42, 0.055);
        transform: translateY(-1px);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-command-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0;
        overflow: hidden;
        margin-top: 4px;
        border: 1px solid rgba(226, 232, 240, 0.92);
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.92);
        box-shadow:
          0 14px 32px rgba(15, 23, 42, 0.035),
          inset 0 1px 0 rgba(255, 255, 255, 0.9);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-command-fact {
        padding: 14px 16px;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-command-fact + .warehouse-receiving-command-fact {
        border-left: 1px solid rgba(226, 232, 240, 0.88);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-command-fact span,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-card-label,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-line-fact span {
        color: #52637a;
        font-size: 10px;
        font-weight: 760;
        letter-spacing: 0.018em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-command-fact strong {
        margin-top: 6px;
        color: #020617;
        font-size: 13px;
        font-weight: 690;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-posture-panel {
        display: grid;
        gap: 14px;
        margin-top: 18px;
        padding: 16px;
        border: 1px solid rgba(226, 232, 240, 0.72);
        border-radius: 22px;
        background: #ffffff;
        box-shadow:
          0 24px 52px rgba(15, 23, 42, 0.055),
          0 8px 18px rgba(15, 23, 42, 0.028),
          inset 0 1px 0 rgba(255, 255, 255, 0.94);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-posture-head {
        display: flex;
        justify-content: space-between;
        gap: 14px;
        align-items: flex-start;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-posture-title {
        margin: 0;
        color: #020617;
        font-size: 17px;
        font-weight: 720;
        letter-spacing: -0.006em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-posture-note {
        margin-top: 5px;
        color: #64748b;
        font-size: 12px;
        line-height: 1.35;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-posture-layout {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-posture-block {
        display: grid;
        gap: 9px;
        min-width: 0;
        padding: 11px;
        border: 1px solid rgba(226, 232, 240, 0.62);
        border-radius: 17px;
        background: #fbfcfe;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-posture-kicker {
        color: #52637a;
        font-size: 10px;
        font-weight: 780;
        letter-spacing: 0.022em;
        text-transform: uppercase;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-posture-block .warehouse-receiving-readiness,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-posture-block .warehouse-receiving-cards {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px;
        margin: 0;
        background: transparent;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-readiness-card,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-card {
        min-height: 82px;
        padding: 12px 13px;
        border: 1px solid rgba(226, 232, 240, 0.58);
        border-radius: 14px;
        background: #ffffff;
        box-shadow:
          0 9px 18px rgba(15, 23, 42, 0.026),
          inset 0 1px 0 rgba(255, 255, 255, 0.92);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-card-value {
        margin-top: 5px;
        color: #020617;
        font-size: 18px;
        font-weight: 690;
        line-height: 1.12;
        letter-spacing: -0.01em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-card-note {
        margin-top: 5px;
        color: #52637a;
        font-size: 11.5px;
        line-height: 1.35;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-note {
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-guardrail {
        display: inline-flex;
        width: fit-content;
        max-width: 100%;
        gap: 8px;
        margin-top: 8px;
        margin-bottom: 4px;
        padding: 7px 11px;
        border: 1px solid rgba(226, 232, 240, 0.82);
        border-radius: 999px;
        background: rgba(248, 250, 252, 0.78);
        color: #52637a;
        font-size: 11.5px;
        line-height: 1.3;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-guardrail strong {
        color: #334155;
        font-weight: 760;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-detail {
        gap: 16px;
        margin-top: 18px;
        padding: 18px;
        border: 1px solid rgba(226, 232, 240, 0.84);
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.94);
        box-shadow: 0 18px 44px rgba(15, 23, 42, 0.045);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-detail-head {
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 14px;
        align-items: start;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-section-title {
        color: #020617;
        font-size: 17px;
        font-weight: 720;
        letter-spacing: -0.006em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-tab {
        min-height: 34px;
        padding: 0 13px;
        border-color: rgba(203, 213, 225, 0.9);
        border-radius: 12px;
        background: #ffffff;
        color: #334155;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.025);
        cursor: pointer;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-tab.is-active {
        border-color: rgba(20, 184, 166, 0.32);
        background: rgba(240, 253, 250, 0.82);
        color: #0f766e;
        box-shadow: 0 10px 22px rgba(15, 118, 110, 0.055);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-panel {
        gap: 15px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-panel:not(.is-active) {
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-panel.is-active {
        display: grid;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-line,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-history-row {
        position: relative;
        gap: 12px;
        padding: 16px 17px 16px 18px;
        border: 1px solid rgba(226, 232, 240, 0.72);
        border-radius: 18px;
        background:
          radial-gradient(circle at 4% 0%, rgba(255, 255, 255, 0.92), transparent 34%),
          linear-gradient(180deg, #f8fbff 0%, #f5f8fc 100%);
        box-shadow:
          0 16px 34px rgba(15, 23, 42, 0.045),
          inset 0 1px 0 rgba(255, 255, 255, 0.9);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-line:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-history-row:hover {
        border-color: rgba(226, 232, 240, 0.72);
        box-shadow:
          0 16px 34px rgba(15, 23, 42, 0.045),
          inset 0 1px 0 rgba(255, 255, 255, 0.9);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-line-facts {
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 8px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-line-fact {
        padding: 10px 11px;
        border: 1px solid rgba(226, 232, 240, 0.82);
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.96);
        box-shadow:
          0 6px 14px rgba(15, 23, 42, 0.025),
          inset 0 1px 0 rgba(255, 255, 255, 0.88);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-line-fact strong {
        margin-top: 5px;
        color: #020617;
        font-size: 12.5px;
        font-weight: 690;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-line-status {
        border-color: rgba(203, 213, 225, 0.88);
        border-radius: 999px;
        background: #ffffff;
        color: #334155;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] {
        width: min(1120px, calc(100% - 48px));
        padding: 18px 0 34px;
        background: #ffffff;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-header {
        gap: 18px;
        margin-bottom: 24px;
        padding: 0;
        border: 0;
        border-radius: 0;
        background: #ffffff;
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-receiving-head {
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: start;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-eyebrow {
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-receiving-title {
        color: #020617;
        font-size: clamp(24px, 1.9vw, 26px);
        font-weight: 700;
        line-height: 1.12;
        letter-spacing: -0.018em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-receiving-subtitle {
        max-width: 720px;
        margin-top: 8px;
        color: #475569;
        font-size: 13px;
        line-height: 1.5;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-chip-row {
        display: flex;
        flex-wrap: wrap;
        margin-top: 4px;
        gap: 6px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-chip-row .warehouse-inbound-chip {
        min-height: 22px;
        padding: 0 8px;
        border-color: rgba(203, 213, 225, 0.78);
        background: rgba(248, 250, 252, 0.74);
        color: #475569;
        font-size: 10.5px;
        font-weight: 680;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-chip-row .warehouse-inbound-chip.is-read-only {
        border-color: rgba(20, 184, 166, 0.22);
        background: rgba(240, 253, 250, 0.72);
        color: #0f766e;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-receiving-actions {
        gap: 8px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-receiving-button {
        min-height: 34px;
        padding: 0 13px;
        border-color: rgba(203, 213, 225, 0.98);
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.94);
        color: #0f172a;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.035);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-receiving-button:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-receiving-button:focus-visible {
        border-color: rgba(148, 163, 184, 0.92);
        box-shadow: 0 10px 22px rgba(15, 23, 42, 0.055);
        transform: translateY(-1px);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-command-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0;
        overflow: hidden;
        margin-top: 4px;
        border: 1px solid rgba(226, 232, 240, 0.92);
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.92);
        box-shadow:
          0 14px 32px rgba(15, 23, 42, 0.035),
          inset 0 1px 0 rgba(255, 255, 255, 0.9);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-command-fact {
        padding: 14px 16px;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-command-fact + .warehouse-stock-exception-review-command-fact {
        border-left: 1px solid rgba(226, 232, 240, 0.88);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-command-fact span,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-receiving-card-label,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-fact span {
        color: #52637a;
        font-size: 10px;
        font-weight: 760;
        letter-spacing: 0.018em;
        text-transform: uppercase;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-command-fact strong {
        margin-top: 6px;
        color: #020617;
        font-size: 13px;
        font-weight: 690;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-receiving-note {
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-posture-panel {
        display: grid;
        gap: 14px;
        margin-top: 18px;
        padding: 16px;
        border: 1px solid rgba(226, 232, 240, 0.72);
        border-radius: 22px;
        background: #ffffff;
        box-shadow:
          0 24px 52px rgba(15, 23, 42, 0.055),
          0 8px 18px rgba(15, 23, 42, 0.028),
          inset 0 1px 0 rgba(255, 255, 255, 0.94);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-posture-panel .warehouse-receiving-posture-layout {
        display: grid;
        grid-template-columns: minmax(0, 1fr);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-receiving-posture-title {
        margin: 0;
        color: #020617;
        font-size: 17px;
        font-weight: 720;
        letter-spacing: -0.006em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-receiving-posture-note {
        margin-top: 5px;
        color: #64748b;
        font-size: 12px;
        line-height: 1.35;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-receiving-posture-kicker {
        color: #52637a;
        font-size: 10px;
        font-weight: 780;
        letter-spacing: 0.022em;
        text-transform: uppercase;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-posture-block {
        display: grid;
        gap: 9px;
        min-width: 0;
        padding: 11px;
        border: 1px solid rgba(226, 232, 240, 0.62);
        border-radius: 17px;
        background: #fbfcfe;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-posture-block .warehouse-receiving-cards {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 8px;
        margin: 0;
        background: transparent;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-receiving-card {
        min-height: 82px;
        padding: 12px 13px;
        border: 1px solid rgba(226, 232, 240, 0.58);
        border-radius: 14px;
        background: #ffffff;
        box-shadow:
          0 9px 18px rgba(15, 23, 42, 0.026),
          inset 0 1px 0 rgba(255, 255, 255, 0.92);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-receiving-card-value {
        margin-top: 5px;
        color: #020617;
        font-size: 18px;
        font-weight: 690;
        line-height: 1.12;
        letter-spacing: -0.01em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-receiving-card-note {
        margin-top: 5px;
        color: #52637a;
        font-size: 11.5px;
        line-height: 1.35;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-guardrail {
        display: inline-flex;
        width: fit-content;
        max-width: 100%;
        gap: 8px;
        margin-top: 8px;
        margin-bottom: 4px;
        padding: 7px 11px;
        border: 1px solid rgba(226, 232, 240, 0.82);
        border-radius: 999px;
        background: rgba(248, 250, 252, 0.78);
        color: #52637a;
        font-size: 11.5px;
        line-height: 1.3;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-guardrail strong {
        color: #334155;
        font-weight: 760;
        white-space: nowrap;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 14px;
        margin-top: 18px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-panel,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-related-panel {
        gap: 13px;
        padding: 17px;
        border: 1px solid rgba(226, 232, 240, 0.76);
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.96);
        box-shadow: 0 18px 44px rgba(15, 23, 42, 0.04);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-inbound-group-title {
        color: #020617;
        font-size: 17px;
        font-weight: 720;
        letter-spacing: -0.006em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-inbound-group-note {
        color: #64748b;
        font-size: 12px;
        line-height: 1.35;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-facts {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-fact {
        display: grid;
        gap: 5px;
        align-items: start;
        justify-content: stretch;
        min-height: 58px;
        padding: 10px 11px;
        border: 1px solid rgba(226, 232, 240, 0.82);
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.96);
        box-shadow:
          0 6px 14px rgba(15, 23, 42, 0.025),
          inset 0 1px 0 rgba(255, 255, 255, 0.88);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-fact strong {
        color: #020617;
        font-size: 12.5px;
        font-weight: 690;
        line-height: 1.25;
        text-align: left;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-next-card,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] [data-warehouse-stock-exception-related-row] {
        border-color: rgba(226, 232, 240, 0.78);
        border-radius: 16px;
        background:
          radial-gradient(circle at 4% 0%, rgba(255, 255, 255, 0.92), transparent 34%),
          linear-gradient(180deg, #f8fbff 0%, #f5f8fc 100%);
        box-shadow:
          0 12px 26px rgba(15, 23, 42, 0.04),
          inset 0 1px 0 rgba(255, 255, 255, 0.9);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] {
        width: min(1120px, calc(100% - 48px));
        padding: 18px 0 34px;
        background: #ffffff;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-header {
        gap: 18px;
        margin-bottom: 24px;
        padding: 0;
        border: 0;
        border-radius: 0;
        background: #ffffff;
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-receiving-head {
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: start;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-eyebrow {
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-receiving-title {
        color: #020617;
        font-size: clamp(24px, 1.9vw, 26px);
        font-weight: 700;
        line-height: 1.12;
        letter-spacing: -0.018em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-receiving-subtitle {
        max-width: 720px;
        margin-top: 8px;
        color: #475569;
        font-size: 13px;
        line-height: 1.5;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-chip-row {
        display: flex;
        flex-wrap: wrap;
        margin-top: 4px;
        gap: 6px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-chip-row .warehouse-inbound-chip {
        min-height: 22px;
        padding: 0 8px;
        border-color: rgba(203, 213, 225, 0.78);
        background: rgba(248, 250, 252, 0.74);
        color: #475569;
        font-size: 10.5px;
        font-weight: 680;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-chip-row .warehouse-inbound-chip.is-read-only {
        border-color: rgba(20, 184, 166, 0.22);
        background: rgba(240, 253, 250, 0.72);
        color: #0f766e;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-receiving-actions {
        gap: 8px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-receiving-button {
        min-height: 34px;
        padding: 0 13px;
        border-color: rgba(203, 213, 225, 0.98);
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.94);
        color: #0f172a;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.035);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-receiving-button:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-receiving-button:focus-visible {
        border-color: rgba(148, 163, 184, 0.92);
        box-shadow: 0 10px 22px rgba(15, 23, 42, 0.055);
        transform: translateY(-1px);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-command-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0;
        overflow: hidden;
        margin-top: 4px;
        border: 1px solid rgba(226, 232, 240, 0.92);
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.92);
        box-shadow:
          0 14px 32px rgba(15, 23, 42, 0.035),
          inset 0 1px 0 rgba(255, 255, 255, 0.9);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-command-fact {
        padding: 14px 16px;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-command-fact + .warehouse-stock-posture-command-fact {
        border-left: 1px solid rgba(226, 232, 240, 0.88);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-command-fact span,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-receiving-card-label,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-exception-review-fact span {
        color: #52637a;
        font-size: 10px;
        font-weight: 760;
        letter-spacing: 0.018em;
        text-transform: uppercase;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-command-fact strong {
        margin-top: 6px;
        color: #020617;
        font-size: 13px;
        font-weight: 690;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-receiving-note {
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-review-posture-panel {
        display: grid;
        gap: 14px;
        margin-top: 0;
        margin-bottom: 18px;
        padding: 16px;
        border: 1px solid rgba(226, 232, 240, 0.72);
        border-radius: 22px;
        background: #ffffff;
        box-shadow:
          0 24px 52px rgba(15, 23, 42, 0.055),
          0 8px 18px rgba(15, 23, 42, 0.028),
          inset 0 1px 0 rgba(255, 255, 255, 0.94);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-review-posture-panel .warehouse-receiving-posture-layout {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-receiving-posture-title {
        margin: 0;
        color: #020617;
        font-size: 17px;
        font-weight: 720;
        letter-spacing: -0.006em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-receiving-posture-note {
        margin-top: 5px;
        color: #64748b;
        font-size: 12px;
        line-height: 1.35;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-receiving-posture-kicker {
        color: #52637a;
        font-size: 10px;
        font-weight: 780;
        letter-spacing: 0.022em;
        text-transform: uppercase;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-review-posture-block {
        display: grid;
        gap: 9px;
        min-width: 0;
        padding: 11px;
        border: 1px solid rgba(226, 232, 240, 0.62);
        border-radius: 17px;
        background: #fbfcfe;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-review-posture-block .warehouse-receiving-cards {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px;
        margin: 0;
        background: transparent;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-receiving-card {
        min-height: 82px;
        padding: 12px 13px;
        border: 1px solid rgba(226, 232, 240, 0.58);
        border-radius: 14px;
        background: #ffffff;
        box-shadow:
          0 9px 18px rgba(15, 23, 42, 0.026),
          inset 0 1px 0 rgba(255, 255, 255, 0.92);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-receiving-card-value {
        margin-top: 5px;
        color: #020617;
        font-size: 18px;
        font-weight: 690;
        line-height: 1.12;
        letter-spacing: -0.01em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-receiving-card-note {
        margin-top: 5px;
        color: #52637a;
        font-size: 11.5px;
        line-height: 1.35;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-guardrail {
        display: inline-flex;
        width: fit-content;
        max-width: 100%;
        gap: 8px;
        margin-top: 0;
        margin-bottom: 4px;
        padding: 7px 11px;
        border: 1px solid rgba(226, 232, 240, 0.82);
        border-radius: 999px;
        background: rgba(248, 250, 252, 0.78);
        color: #52637a;
        font-size: 11.5px;
        line-height: 1.3;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-guardrail strong {
        color: #334155;
        font-weight: 760;
        white-space: nowrap;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-exception-review-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 14px;
        margin-top: 18px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-exception-review-panel,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-receiving-detail {
        gap: 13px;
        padding: 17px;
        border: 1px solid rgba(226, 232, 240, 0.76);
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.96);
        box-shadow: 0 18px 44px rgba(15, 23, 42, 0.04);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-inbound-group-title {
        color: #020617;
        font-size: 17px;
        font-weight: 720;
        letter-spacing: -0.006em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-inbound-group-note {
        color: #64748b;
        font-size: 12px;
        line-height: 1.35;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-exception-review-facts {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-exception-review-fact {
        display: grid;
        gap: 5px;
        align-items: start;
        justify-content: stretch;
        min-height: 58px;
        padding: 10px 11px;
        border: 1px solid rgba(226, 232, 240, 0.82);
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.96);
        box-shadow:
          0 6px 14px rgba(15, 23, 42, 0.025),
          inset 0 1px 0 rgba(255, 255, 255, 0.88);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-exception-review-fact strong {
        color: #020617;
        font-size: 12.5px;
        font-weight: 690;
        line-height: 1.25;
        text-align: left;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-recommended-grid {
        gap: 8px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-recommended-card,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] [data-warehouse-stock-posture-row],
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] [data-warehouse-stock-posture-related-row] {
        border-color: rgba(226, 232, 240, 0.78);
        border-radius: 16px;
        background:
          radial-gradient(circle at 4% 0%, rgba(255, 255, 255, 0.92), transparent 34%),
          linear-gradient(180deg, #f8fbff 0%, #f5f8fc 100%);
        box-shadow:
          0 12px 26px rgba(15, 23, 42, 0.04),
          inset 0 1px 0 rgba(255, 255, 255, 0.9);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] {
        width: min(1120px, calc(100% - 48px));
        padding: 18px 0 34px;
        background: #ffffff;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-header {
        gap: 18px;
        margin-bottom: 24px;
        padding: 0;
        border: 0;
        border-radius: 0;
        background: #ffffff;
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-receiving-head {
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: start;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-eyebrow {
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-receiving-title {
        color: #020617;
        font-size: clamp(24px, 1.9vw, 26px);
        font-weight: 700;
        line-height: 1.12;
        letter-spacing: -0.018em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-receiving-subtitle {
        max-width: 720px;
        margin-top: 8px;
        color: #475569;
        font-size: 13px;
        line-height: 1.5;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-chip-row {
        display: flex;
        flex-wrap: wrap;
        margin-top: 4px;
        gap: 6px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-chip-row .warehouse-inbound-chip {
        min-height: 22px;
        padding: 0 8px;
        border-color: rgba(203, 213, 225, 0.78);
        background: rgba(248, 250, 252, 0.74);
        color: #475569;
        font-size: 10.5px;
        font-weight: 680;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-chip-row .warehouse-inbound-chip.is-read-only {
        border-color: rgba(20, 184, 166, 0.22);
        background: rgba(240, 253, 250, 0.72);
        color: #0f766e;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-receiving-actions {
        gap: 8px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-receiving-button {
        min-height: 34px;
        padding: 0 13px;
        border-color: rgba(203, 213, 225, 0.98);
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.94);
        color: #0f172a;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.035);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-receiving-button:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-receiving-button:focus-visible {
        border-color: rgba(148, 163, 184, 0.92);
        box-shadow: 0 10px 22px rgba(15, 23, 42, 0.055);
        transform: translateY(-1px);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-command-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0;
        overflow: hidden;
        margin-top: 4px;
        border: 1px solid rgba(226, 232, 240, 0.92);
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.92);
        box-shadow:
          0 14px 32px rgba(15, 23, 42, 0.035),
          inset 0 1px 0 rgba(255, 255, 255, 0.9);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-command-fact {
        padding: 14px 16px;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-command-fact + .warehouse-movement-review-command-fact {
        border-left: 1px solid rgba(226, 232, 240, 0.88);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-command-fact span,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-receiving-card-label,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-line-fact span,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-stock-exception-panel-item span {
        color: #52637a;
        font-size: 10px;
        font-weight: 760;
        letter-spacing: 0.018em;
        text-transform: uppercase;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-command-fact strong {
        margin-top: 6px;
        color: #020617;
        font-size: 13px;
        font-weight: 690;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-receiving-note {
        display: none;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-posture-panel {
        display: grid;
        gap: 14px;
        margin-top: 0;
        margin-bottom: 18px;
        padding: 16px;
        border: 1px solid rgba(226, 232, 240, 0.72);
        border-radius: 22px;
        background: #ffffff;
        box-shadow:
          0 24px 52px rgba(15, 23, 42, 0.055),
          0 8px 18px rgba(15, 23, 42, 0.028),
          inset 0 1px 0 rgba(255, 255, 255, 0.94);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-posture-panel .warehouse-receiving-posture-layout {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-receiving-posture-title {
        margin: 0;
        color: #020617;
        font-size: 17px;
        font-weight: 720;
        letter-spacing: -0.006em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-receiving-posture-note {
        margin-top: 5px;
        color: #64748b;
        font-size: 12px;
        line-height: 1.35;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-receiving-posture-kicker {
        color: #52637a;
        font-size: 10px;
        font-weight: 780;
        letter-spacing: 0.022em;
        text-transform: uppercase;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-posture-block {
        display: grid;
        gap: 9px;
        min-width: 0;
        padding: 11px;
        border: 1px solid rgba(226, 232, 240, 0.62);
        border-radius: 17px;
        background: #fbfcfe;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-posture-block .warehouse-receiving-cards {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px;
        margin: 0;
        background: transparent;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-receiving-card {
        min-height: 82px;
        padding: 12px 13px;
        border: 1px solid rgba(226, 232, 240, 0.58);
        border-radius: 14px;
        background: #ffffff;
        box-shadow:
          0 9px 18px rgba(15, 23, 42, 0.026),
          inset 0 1px 0 rgba(255, 255, 255, 0.92);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-receiving-card-value {
        margin-top: 5px;
        color: #020617;
        font-size: 18px;
        font-weight: 690;
        line-height: 1.12;
        letter-spacing: -0.01em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-receiving-card-note {
        margin-top: 5px;
        color: #52637a;
        font-size: 11.5px;
        line-height: 1.35;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-guardrail {
        display: inline-flex;
        width: fit-content;
        max-width: 100%;
        gap: 8px;
        margin-top: 0;
        margin-bottom: 4px;
        padding: 7px 11px;
        border: 1px solid rgba(226, 232, 240, 0.82);
        border-radius: 999px;
        background: rgba(248, 250, 252, 0.78);
        color: #52637a;
        font-size: 11.5px;
        line-height: 1.3;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-guardrail strong {
        color: #334155;
        font-weight: 760;
        white-space: nowrap;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-stock-exception-review-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 14px;
        margin-top: 18px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-stock-exception-panel,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-receiving-detail {
        gap: 13px;
        padding: 17px;
        border: 1px solid rgba(226, 232, 240, 0.76);
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.96);
        box-shadow: 0 18px 44px rgba(15, 23, 42, 0.04);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-stock-exception-panel-title,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-inbound-group-title {
        color: #020617;
        font-size: 17px;
        font-weight: 720;
        letter-spacing: -0.006em;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-inbound-meta,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-inbound-group-note {
        color: #64748b;
        font-size: 12px;
        line-height: 1.35;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-stock-exception-panel-items,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-line-facts {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-stock-exception-panel-item,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-line-fact {
        display: grid;
        gap: 5px;
        align-items: start;
        justify-content: stretch;
        min-height: 58px;
        padding: 10px 11px;
        border: 1px solid rgba(226, 232, 240, 0.82);
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.96);
        box-shadow:
          0 6px 14px rgba(15, 23, 42, 0.025),
          inset 0 1px 0 rgba(255, 255, 255, 0.88);
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-stock-exception-panel-item strong,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-line-fact strong {
        color: #020617;
        font-size: 12.5px;
        font-weight: 690;
        line-height: 1.25;
        text-align: left;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-line-card,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] [data-warehouse-movement-review-related-row] {
        border-color: rgba(226, 232, 240, 0.78);
        border-radius: 16px;
        background:
          radial-gradient(circle at 4% 0%, rgba(255, 255, 255, 0.92), transparent 34%),
          linear-gradient(180deg, #f8fbff 0%, #f5f8fc 100%);
        box-shadow:
          0 12px 26px rgba(15, 23, 42, 0.04),
          inset 0 1px 0 rgba(255, 255, 255, 0.9);
      }
      @media (max-width: 900px) {
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-posture-layout {
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-command-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-readiness,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-cards,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-line-facts {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
      }
      @media (max-width: 640px) {
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] {
          width: min(100%, calc(100% - 12px));
          padding: 4px 0 24px;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-head,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-detail-head,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-command-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-readiness,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-cards,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-line-main,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-line-facts {
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-actions,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-tabs {
          display: grid;
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-button,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-tab {
          width: 100%;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-command-fact + .warehouse-receiving-command-fact {
          border-left: 0;
          border-top: 1px solid rgba(226, 232, 240, 0.88);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-posture-panel {
          padding: 13px;
          border-radius: 18px;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-posture-block .warehouse-receiving-readiness,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-posture-block .warehouse-receiving-cards {
          grid-template-columns: minmax(0, 1fr);
        }
      }
      @media (max-width: 900px) {
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-posture-layout {
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-command-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-readiness,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-cards,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-line-facts {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
      }
      @media (max-width: 640px) {
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] {
          width: min(100%, calc(100% - 12px));
          padding: 4px 0 24px;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-head,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-detail-head,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-command-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-readiness,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-cards,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-line-main,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-line-facts {
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-actions,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-tabs {
          display: grid;
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-button,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-tab {
          width: 100%;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-command-fact + .warehouse-receiving-command-fact {
          border-left: 0;
          border-top: 1px solid rgba(226, 232, 240, 0.88);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-posture-panel {
          padding: 13px;
          border-radius: 18px;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-posture-block .warehouse-receiving-readiness,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-posture-block .warehouse-receiving-cards {
          grid-template-columns: minmax(0, 1fr);
        }
      }
      @media (max-width: 900px) {
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-command-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-posture-block .warehouse-receiving-cards,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-facts {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
      }
      @media (max-width: 640px) {
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] {
          width: min(100%, calc(100% - 12px));
          padding: 4px 0 24px;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-receiving-head,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-command-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-posture-block .warehouse-receiving-cards,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-facts,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-next-grid {
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-receiving-actions {
          display: grid;
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-receiving-button {
          width: 100%;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-command-fact + .warehouse-stock-exception-review-command-fact {
          border-left: 0;
          border-top: 1px solid rgba(226, 232, 240, 0.88);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-exception-review-shell[data-warehouse-view='stock-exception-review'] .warehouse-stock-exception-review-posture-panel {
          padding: 13px;
          border-radius: 18px;
        }
      }
      @media (max-width: 900px) {
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-review-posture-panel .warehouse-receiving-posture-layout {
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-command-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-review-posture-block .warehouse-receiving-cards,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-exception-review-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-exception-review-facts {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
      }
      @media (max-width: 640px) {
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] {
          width: min(100%, calc(100% - 12px));
          padding: 4px 0 24px;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-receiving-head,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-command-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-review-posture-panel .warehouse-receiving-posture-layout,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-review-posture-block .warehouse-receiving-cards,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-exception-review-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-exception-review-facts,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-recommended-grid {
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-receiving-actions {
          display: grid;
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-receiving-button {
          width: 100%;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-command-fact + .warehouse-stock-posture-command-fact {
          border-left: 0;
          border-top: 1px solid rgba(226, 232, 240, 0.88);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-stock-posture-shell[data-warehouse-view='stock-posture-review'] .warehouse-stock-posture-review-posture-panel {
          padding: 13px;
          border-radius: 18px;
        }
      }
      @media (max-width: 900px) {
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-posture-panel .warehouse-receiving-posture-layout {
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-command-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-posture-block .warehouse-receiving-cards,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-stock-exception-review-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-stock-exception-panel-items,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-line-facts {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
      }
      @media (max-width: 640px) {
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] {
          width: min(100%, calc(100% - 12px));
          padding: 4px 0 24px;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-receiving-head,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-command-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-posture-panel .warehouse-receiving-posture-layout,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-posture-block .warehouse-receiving-cards,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-stock-exception-review-grid,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-stock-exception-panel-items,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-line-main,
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-line-facts {
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-receiving-actions {
          display: grid;
          grid-template-columns: minmax(0, 1fr);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-receiving-button {
          width: 100%;
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-command-fact + .warehouse-movement-review-command-fact {
          border-left: 0;
          border-top: 1px solid rgba(226, 232, 240, 0.88);
        }
        .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-movement-review-shell[data-warehouse-view='movement-review'] .warehouse-movement-review-posture-panel {
          padding: 13px;
          border-radius: 18px;
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
      <div class="sales-console-shell warehouse-console-shell warehouse-visual-foundation" data-erpw-workspace="warehouse" data-warehouse-console-state="${escapeHtml(payloadState.kind || "unavailable")}" data-warehouse-visual-foundation="w13c1">
        <section class="warehouse-console-state warehouse-visual-fallback">
          <h1 class="warehouse-console-state-title">${escapeHtml(payloadState.title || "Warehouse Console unavailable")}</h1>
          <div class="warehouse-console-state-detail">${escapeHtml(payloadState.detail || "Warehouse information could not be loaded. Refresh or try again.")}</div>
        </section>
      </div>
    `);
    replacePageBody(page, $root);
    cleanupWarehousePageHeads();
  }

  function renderLoadingState(page) {
    if (!isActiveWarehouseRoute()) return;
    ensureStyle();
    const $root = $(`
      <div class="sales-console-shell warehouse-console-shell warehouse-visual-foundation" data-erpw-workspace="warehouse" data-erpw-console-runtime="loading" data-erpw-console-bootstrap="loading" data-warehouse-visual-foundation="w13c1" data-erpw-overview-route-signature="${escapeHtml(overviewRouteSignature())}">
        <section class="warehouse-console-header warehouse-visual-command">
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
    cleanupWarehousePageHeads();
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
    return `Fresh ${formatWarehouseFreshness(fetchedAt)}`;
  }

  function formatWarehouseFreshness(value) {
    const raw = String(value || "").trim();
    const match = raw.match(/^(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):(\d{2})(?::\d{2})?/);
    if (!match) return raw.replace(/\.\d+$/, "");
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const year = match[1];
    const monthIndex = Math.max(0, Math.min(11, Number(match[2]) - 1));
    const day = String(Number(match[3]));
    const hour24 = Number(match[4]);
    const minute = match[5];
    const period = hour24 >= 12 ? "PM" : "AM";
    const hour12 = hour24 % 12 || 12;
    return `${months[monthIndex]} ${day}, ${year} ${hour12}:${minute} ${period}`;
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
      { key: "freshness", label: "Freshness", value: "Current", note: freshnessText(payload), state: "live" },
    ];
  }

  function renderWarehouseAttrs(attrs) {
    return Object.keys(attrs || {}).map((key) => `${escapeHtml(key)}="${escapeHtml(attrs[key])}"`).join(" ");
  }

  function renderWarehouseChip(label, options) {
    const config = options || {};
    const attrs = renderWarehouseAttrs(config.attrs || {});
    const classes = `warehouse-visual-chip ${config.className || ""}`.trim();
    return `<span class="${escapeHtml(classes)}" ${attrs}>${escapeHtml(label)}</span>`;
  }

  function renderWarehouseFact(fact, options) {
    const config = options || {};
    const payload = fact || {};
    const attrs = renderWarehouseAttrs(config.attrs || {});
    const classes = `warehouse-visual-fact ${config.className || ""}`.trim();
    return `
      <div class="${escapeHtml(classes)}" ${attrs}>
        <div class="warehouse-visual-fact-label">${escapeHtml(payload.label || "")}</div>
        <div class="warehouse-visual-fact-value">${escapeHtml(payload.value == null ? "--" : payload.value)}</div>
        ${payload.note ? `<div class="warehouse-visual-fact-note">${escapeHtml(payload.note)}</div>` : ""}
      </div>
    `;
  }

  function renderWarehouseSummaryCard(card, options) {
    const config = options || {};
    const payload = card || {};
    const attrs = renderWarehouseAttrs(config.attrs || {});
    const classes = `warehouse-visual-summary-card ${config.className || ""}`.trim();
    return `
      <div class="${escapeHtml(classes)}" ${attrs}>
        <div class="warehouse-visual-summary-label">${escapeHtml(payload.label || payload.title || "")}</div>
        <div class="warehouse-visual-summary-value">${escapeHtml(payload.value == null ? "--" : payload.value)}</div>
        ${payload.note ? `<div class="warehouse-visual-summary-note">${escapeHtml(payload.note)}</div>` : ""}
      </div>
    `;
  }

  function renderWarehouseActionStrip(actions, options) {
    const config = options || {};
    const attrs = renderWarehouseAttrs(config.attrs || {});
    const classes = `warehouse-visual-action-strip ${config.className || ""}`.trim();
    return `<div class="${escapeHtml(classes)}" ${attrs}>${(actions || []).join("")}</div>`;
  }

  function renderWarehouseGuardrail(title, detail, options) {
    const config = options || {};
    const attrs = renderWarehouseAttrs(config.attrs || {});
    const classes = `warehouse-visual-guardrail ${config.className || ""}`.trim();
    return `
      <section class="${escapeHtml(classes)}" ${attrs}>
        <div class="warehouse-visual-guardrail-title">${escapeHtml(title || "Read-only guardrail")}</div>
        <div>${escapeHtml(detail || "")}</div>
      </section>
    `;
  }

  function renderWarehouseFallbackPanel(title, detail, options) {
    const config = options || {};
    const attrs = renderWarehouseAttrs(config.attrs || {});
    const classes = `warehouse-visual-fallback ${config.className || ""}`.trim();
    return `
      <section class="${escapeHtml(classes)}" ${attrs}>
        <div class="warehouse-visual-fallback-title">${escapeHtml(title || "Nothing visible right now")}</div>
        <div>${escapeHtml(detail || "The available information will appear here when it is ready.")}</div>
      </section>
    `;
  }

  function renderWarehouseRowCard(content, options) {
    const config = options || {};
    const attrs = renderWarehouseAttrs(config.attrs || {});
    const classes = `warehouse-visual-row-card ${config.className || ""}`.trim();
    return `<article class="${escapeHtml(classes)}" ${attrs}>${content || ""}</article>`;
  }

  function renderCockpitChip(label) {
    return `<span class="sales-console-header-chip warehouse-cockpit-chip" data-warehouse-cockpit-command-chip="1">${escapeHtml(label)}</span>`;
  }

  function renderPulseCard(metric) {
    return `
      <div class="sales-console-kpi-card warehouse-console-kpi-card warehouse-cockpit-pulse-card warehouse-visual-summary-card" data-warehouse-kpi="${escapeHtml(metric.key || "")}" data-warehouse-cockpit-pulse-card="${escapeHtml(metric.key || "")}">
        <div class="sales-console-kpi-label warehouse-console-kpi-label">${escapeHtml(metric.label || "")}</div>
        <div class="sales-console-kpi-value warehouse-console-kpi-value">${escapeHtml(metricText(metric))}</div>
        <div class="sales-console-kpi-meta warehouse-console-kpi-meta">${escapeHtml(metricNote(metric))}</div>
      </div>
    `;
  }

  function renderPulseContextCard(metric) {
    return `
      <article class="sales-console-queue-card regular warehouse-cockpit-pulse-context-card" data-warehouse-kpi="${escapeHtml(metric.key || "")}" data-warehouse-cockpit-pulse-card="${escapeHtml(metric.key || "")}">
        <div class="sales-console-queue-main">
          <div class="sales-console-queue-title">${escapeHtml(metric.label || "")}</div>
          <div class="sales-console-queue-meta">${escapeHtml(metricNote(metric))}</div>
        </div>
        <div class="sales-console-queue-side">
          <div class="sales-console-queue-count">${escapeHtml(metricText(metric))}</div>
          <div class="sales-console-queue-side-label">Visible</div>
        </div>
      </article>
    `;
  }

  function overviewIconMarkup(name) {
    const icons = {
      inbound: '<path d="M4 7h10v10H4z"></path><path d="M14 10h3l3 3v4h-6z"></path><path d="M7 19a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z"></path><path d="M17 19a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z"></path>',
      outbound: '<path d="M5 7h14l-1.5 9h-11z"></path><path d="M8 7a4 4 0 0 1 8 0"></path><path d="M9 20h.01"></path><path d="M15 20h.01"></path>',
      risk: '<path d="M12 3 2.8 19h18.4z"></path><path d="M12 8v5"></path><path d="M12 16h.01"></path>',
      movement: '<path d="M7 7h11"></path><path d="m14 4 4 3-4 3"></path><path d="M17 17H6"></path><path d="m10 14-4 3 4 3"></path>',
      transfer: '<path d="M6 8h12"></path><path d="m14 5 4 3-4 3"></path><path d="M18 16H6"></path><path d="m10 13-4 3 4 3"></path>',
    };
    return `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        ${icons[name] || icons.movement}
      </svg>
    `;
  }

  function renderCockpitActionCard(card, tier) {
    const actionTier = tier || "primary";
    return `
      <button class="sales-console-action ${escapeHtml(actionTier)} warehouse-cockpit-action-card" type="button" ${card.actionAttr || ""} data-warehouse-cockpit-start-card="${escapeHtml(card.key || "")}" data-warehouse-cockpit-route-target="${escapeHtml(card.target || "")}">
        <span class="sales-console-action-icon">${overviewIconMarkup(card.icon || "movement")}</span>
        <span class="sales-console-action-copy">
          <span class="sales-console-action-title">${escapeHtml(card.title || "")}</span>
          <span class="sales-console-action-meta">${escapeHtml(card.note || "")}</span>
        </span>
      </button>
    `;
  }

  function renderCockpitStartCard(card) {
    const sideValue = String(card.kicker || "").match(/^\d+/) ? String(card.kicker || "").match(/^\d+/)[0] : "Open";
    const sideLabel = String(card.kicker || "").match(/^\d+\s*(.+)$/) ? String(card.kicker || "").match(/^\d+\s*(.+)$/)[1] : (card.action || "Review").replace(/^Open\s+/i, "");
    return `
      <article class="sales-console-queue-card regular warehouse-cockpit-start-card warehouse-visual-related-card ${escapeHtml(card.variant || "")}" data-warehouse-cockpit-start-card="${escapeHtml(card.key || "")}" data-warehouse-cockpit-route-target="${escapeHtml(card.target || "")}">
        <div class="sales-console-queue-main">
          <div class="sales-console-queue-title warehouse-cockpit-card-title">${escapeHtml(card.title || "")}</div>
          <div class="sales-console-queue-meta warehouse-cockpit-card-note">${escapeHtml(card.note || "")}</div>
        </div>
        <div class="sales-console-queue-side">
          <div class="sales-console-queue-count">${escapeHtml(sideValue)}</div>
          <div class="sales-console-queue-side-label">${escapeHtml(sideLabel)}</div>
          <button type="button" class="warehouse-cockpit-card-action" ${card.actionAttr}>Open</button>
        </div>
      </article>
    `;
  }

  function renderCockpitRouteCard(card) {
    const sideValue = String(card.kicker || "").match(/^\d+/) ? String(card.kicker || "").match(/^\d+/)[0] : (card.action ? "Open" : "--");
    const sideLabel = String(card.kicker || "").match(/^\d+\s*(.+)$/) ? String(card.kicker || "").match(/^\d+\s*(.+)$/)[1] : (card.action || "Context").replace(/^Open\s+/i, "");
    const tag = card.action ? "button" : "article";
    const actionAttrs = card.action ? `type="button" ${card.actionAttr || ""}` : "";
    return `
      <${tag} class="sales-console-queue-card regular warehouse-cockpit-queue-card warehouse-visual-related-card ${escapeHtml(card.variant || "")}" ${actionAttrs} data-warehouse-cockpit-route-card="${escapeHtml(card.key || "")}" data-warehouse-cockpit-route-target="${escapeHtml(card.target || "")}">
        <div class="sales-console-queue-main">
          <div class="sales-console-queue-title warehouse-cockpit-card-title">${escapeHtml(card.title || "")}</div>
          <div class="sales-console-queue-meta warehouse-cockpit-card-note">${escapeHtml(card.note || "")}</div>
        </div>
        <div class="sales-console-queue-side">
          <div class="sales-console-queue-count">${escapeHtml(sideValue)}</div>
          <div class="sales-console-queue-side-label">${escapeHtml(sideLabel)}</div>
        </div>
      </${tag}>
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
        title: "Inbound Receiving",
        note: "Expected supplier stock and partial receiving posture.",
        action: "Open inbound receiving",
        actionAttr: "data-warehouse-open-inbound",
        icon: "inbound",
        target: "warehouse-console-worklist/inbound-receiving",
      },
      {
        key: "outbound_risk",
        kicker: pickingAttention ? `${pickingAttention} needs review` : "Customer-side work",
        title: "Outbound Picking",
        note: "Customer demand, pending quantity, and warehouse readiness.",
        action: "Open outbound picking",
        actionAttr: "data-warehouse-open-outbound",
        icon: "outbound",
        target: "warehouse-console-worklist/outbound-picking",
      },
      {
        key: "stock_exceptions",
        kicker: exceptionTotal ? `${exceptionTotal} visible` : "Risk review",
        title: "Stock Exceptions",
        note: "Shortage risk, inbound cover, and posture gaps.",
        action: "Open stock exceptions",
        actionAttr: "data-warehouse-open-stock-exceptions",
        icon: "risk",
        variant: "is-risk",
        target: "warehouse-console-worklist/stock-exceptions",
      },
      {
        key: "movement_visibility",
        kicker: metricText(movementMetric),
        title: "Movement Visibility",
        note: "Posted movement evidence and item posture drilldowns.",
        action: "Open movement visibility",
        actionAttr: "data-warehouse-open-movement",
        icon: "movement",
        variant: "is-movement",
        target: "warehouse-console-worklist/movement-visibility",
      },
      {
        key: "transfer_visibility",
        kicker: "Transfer posture",
        title: "Transfer Visibility",
        note: "Visibility across warehouses from posted movement records.",
        action: "Open transfer visibility",
        actionAttr: "data-warehouse-open-transfer",
        icon: "transfer",
        variant: "is-movement",
        target: "warehouse-console-worklist/transfer-visibility",
      },
    ];
    const primaryCards = cards.slice(0, 3);
    const secondaryCards = cards.slice(3);
    return `
      <section class="sales-console-card sales-console-section warehouse-cockpit-start" data-warehouse-cockpit-start>
        <div class="sales-console-section-head warehouse-cockpit-section-head">
          <h2 class="sales-console-section-title warehouse-cockpit-section-title">Start Warehouse Work</h2>
          <div class="sales-console-section-note warehouse-cockpit-section-note">Only review routes available in this workspace</div>
        </div>
        <div class="sales-console-action-groups warehouse-cockpit-start-grid warehouse-visual-related-grid">
          <div class="sales-console-action-strip primary">${primaryCards.map((card) => renderCockpitActionCard(card, "primary")).join("")}</div>
          <div class="sales-console-action-strip secondary">${secondaryCards.map((card) => renderCockpitActionCard(card, "secondary")).join("")}</div>
        </div>
      </section>
    `;
  }

  function renderActionCenterCard(card) {
    const payload = card || {};
    const route = payload.route || "";
    const routePart = payload.route_part || "";
    const hasRoute = route === WORKLIST_PAGE_KEY && isSupportedWorklistQueue(routePart);
    const routeView = hasRoute ? worklistViewName(routePart) : "";
    const routeTarget = hasRoute ? `${route}/${routeView}` : "";
    const value = payload.value == null || payload.value === "" ? "--" : String(payload.value);
    const sideLabel = payload.status_label || (hasRoute ? "Review queue" : "Planned");
    const stateClass = hasRoute ? "is-live" : "is-planned";
    const sideMarkup = hasRoute ? `
      <div class="sales-console-queue-side warehouse-action-center-side">
        <div class="sales-console-queue-count">${escapeHtml(value)}</div>
        <div class="sales-console-queue-side-label">${escapeHtml(sideLabel)}</div>
        <button class="warehouse-action-center-open" type="button" data-warehouse-action-center-open>${escapeHtml(payload.button_label || "Open queue")}</button>
      </div>
    ` : `
      <div class="sales-console-queue-side warehouse-action-center-side">
        <div class="sales-console-queue-count">${escapeHtml(value)}</div>
        <div class="sales-console-queue-side-label">${escapeHtml(sideLabel)}</div>
      </div>
    `;
    return `
      <article class="sales-console-queue-card regular warehouse-action-center-card ${stateClass}" data-warehouse-action-center-card="${escapeHtml(payload.key || "")}" data-warehouse-action-center-route="${escapeHtml(route)}" data-warehouse-action-center-route-part="${escapeHtml(routePart)}" data-warehouse-cockpit-route-target="${escapeHtml(routeTarget)}">
        <div class="sales-console-queue-main">
          <div class="sales-console-queue-title warehouse-cockpit-card-title">${escapeHtml(payload.title || "")}</div>
          <div class="sales-console-queue-meta warehouse-cockpit-card-note">${escapeHtml(payload.note || "")}</div>
        </div>
        ${sideMarkup}
      </article>
    `;
  }

  function renderActionCenterGroup(group) {
    const payload = group || {};
    const cards = Array.isArray(payload.cards) ? payload.cards : [];
    return `
      <section class="warehouse-action-center-group" data-warehouse-action-center-group="${escapeHtml(payload.key || "")}">
        <div class="warehouse-action-center-group-head">
          <h3>${escapeHtml(payload.title || "")}</h3>
          <p>${escapeHtml(payload.summary || "")}</p>
        </div>
        <div class="warehouse-action-center-grid">${cards.map(renderActionCenterCard).join("")}</div>
      </section>
    `;
  }

  function renderCockpitActionCenter(actionCenter) {
    const payload = actionCenter || {};
    const sections = Array.isArray(payload.sections) ? payload.sections : [];
    if (!sections.length) return "";
    return `
      <section class="sales-console-card sales-console-section warehouse-cockpit-route-section warehouse-action-center-section" data-warehouse-action-center data-warehouse-action-center-state="${escapeHtml(payload.state || "planning")}" data-warehouse-action-center-mode="${escapeHtml(payload.mode || "shell_only")}">
        <div class="sales-console-section-head warehouse-cockpit-section-head">
          <div>
            <h2 class="sales-console-section-title warehouse-cockpit-section-title">${escapeHtml(payload.title || "Warehouse Action Center")}</h2>
            <div class="sales-console-section-note warehouse-cockpit-section-note warehouse-action-center-subtitle">${escapeHtml(payload.subtitle || "")}</div>
          </div>
          <span class="warehouse-action-center-mode">Shell only</span>
        </div>
        <div class="warehouse-action-center-groups">${sections.map(renderActionCenterGroup).join("")}</div>
        ${payload.guardrail ? `
          <div class="warehouse-action-center-guardrail" data-warehouse-action-center-guardrail>
            <strong>${escapeHtml(payload.guardrail.title || "Action shell only")}</strong>
            <span>${escapeHtml(payload.guardrail.detail || "")}</span>
          </div>
        ` : ""}
      </section>
    `;
  }

  function renderCustomerReturnIntakeShell() {
    const statuses = [
      "Return Requested",
      "Physical Intake",
      "Inspection",
      "Manager Review",
      "Disposition Recommendation",
      "Sales / Finance Handoff",
    ];
    const userPreview = [
      "Receive returned goods",
      "Count returned quantity",
      "Record condition",
      "Add evidence reference",
      "Send to manager review",
    ];
    const managerPreview = [
      "Request reinspection",
      "Mark restock candidate",
      "Mark quarantine review",
      "Mark repair review",
      "Mark scrap candidate",
      "Reject return intake",
      "Escalate to Sales",
    ];
    const evidence = [
      ["Customer/source reference", "Sales-visible intake source"],
      ["Item identity", "Item and returned unit posture"],
      ["Returned quantity", "Physical count evidence"],
      ["Condition grade", "Inspection posture"],
      ["Evidence reference", "Future attachment or note reference"],
      ["Manager event", "Disposition review trail"],
      ["Sales escalation reference", "Customer-facing follow-up marker"],
    ];
    const ownership = [
      ["Warehouse", "Physical evidence"],
      ["Warehouse Manager", "Internal disposition recommendation"],
      ["Sales", "Customer authorization, communication, replacement, and refund decision"],
      ["Finance/Admin", "Credit, refund, write-off, and document governance"],
    ];
    const policy = [
      ["Sales Return", "Future policy only, blocked now"],
      ["Credit Note", "Future policy only, blocked now"],
      ["Return Delivery Note", "Future policy only, blocked now"],
      ["Stock Entry", "Future policy only, blocked now"],
      ["Reference handling", "Plain text/status only if later approved"],
    ];
    const plannedMarkup = (items) => items.map((item) => `
      <div class="warehouse-customer-return-planned" data-warehouse-customer-return-planned-control aria-disabled="true">${escapeHtml(item)}</div>
    `).join("");
    const miniMarkup = (items) => items.map((item) => `
      <div class="warehouse-customer-return-mini">
        ${escapeHtml(item[0])}
        <span>${escapeHtml(item[1])}</span>
      </div>
    `).join("");
    return `
      <section class="sales-console-card sales-console-section warehouse-customer-return-shell" data-warehouse-customer-return-shell>
        <div class="warehouse-customer-return-head">
          <div class="warehouse-customer-return-copy">
            <h2 class="warehouse-customer-return-title">Customer return intake</h2>
            <div class="warehouse-customer-return-subtitle">Planned workflow shell for physical return intake evidence, inspection posture, manager recommendation, and Sales or Finance handoff.</div>
          </div>
          <span class="warehouse-customer-return-badge">Shell only</span>
        </div>
        <div class="warehouse-customer-return-guardrail">
          No stock is increased, no Sales Return, Credit Note, Delivery Note, Stock Entry, or Stock Ledger entry is created from this shell.
        </div>
        <div class="warehouse-customer-return-status-strip">
          ${statuses.map((status) => `<div class="warehouse-customer-return-status-chip" data-warehouse-customer-return-status>${escapeHtml(status)}</div>`).join("")}
        </div>
        <div class="warehouse-customer-return-grid">
          <section class="warehouse-customer-return-panel" data-warehouse-customer-return-user-preview>
            <h3>Warehouse user preview</h3>
            <div class="warehouse-customer-return-items">${plannedMarkup(userPreview)}</div>
          </section>
          <section class="warehouse-customer-return-panel" data-warehouse-customer-return-manager-preview>
            <h3>Manager preview</h3>
            <div class="warehouse-customer-return-items">${plannedMarkup(managerPreview)}</div>
          </section>
          <section class="warehouse-customer-return-panel" data-warehouse-customer-return-evidence-preview>
            <h3>Evidence preview</h3>
            <div class="warehouse-customer-return-evidence-grid">${miniMarkup(evidence)}</div>
          </section>
          <section class="warehouse-customer-return-panel">
            <h3>Role ownership</h3>
            <div class="warehouse-customer-return-owner-grid">${miniMarkup(ownership)}</div>
          </section>
          <section class="warehouse-customer-return-panel warehouse-customer-return-policy-panel" data-warehouse-customer-return-policy>
            <h3>Future document policy</h3>
            <div class="warehouse-customer-return-policy-grid">${miniMarkup(policy)}</div>
          </section>
        </div>
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
        target: "warehouse-console-worklist/stock-exceptions",
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
      <section class="sales-console-card sales-console-section warehouse-cockpit-route-section" data-warehouse-cockpit-risk>
        <div class="sales-console-section-head warehouse-cockpit-section-head">
          <h2 class="sales-console-section-title warehouse-cockpit-section-title">Risks To Resolve</h2>
          <div class="sales-console-section-note warehouse-cockpit-section-note">Understand blockers before warehouse work stalls.</div>
        </div>
        <div class="sales-console-queue-grid warehouse-cockpit-route-grid warehouse-visual-related-grid is-two">${cards.map(renderCockpitRouteCard).join("")}</div>
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
        target: "warehouse-console-worklist/movement-visibility",
      },
      {
        key: "transfer_visibility",
        kicker: "Transfer posture",
        title: "Transfer Visibility",
        note: "Visibility across warehouses from submitted movement records.",
        action: "Open transfer visibility",
        actionAttr: "data-warehouse-open-transfer",
        variant: "is-movement",
        target: "warehouse-console-worklist/transfer-visibility",
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
      <section class="sales-console-card sales-console-section warehouse-cockpit-route-section" data-warehouse-cockpit-movement>
        <div class="sales-console-section-head warehouse-cockpit-section-head">
          <h2 class="sales-console-section-title warehouse-cockpit-section-title">Movement To Understand</h2>
          <div class="sales-console-section-note warehouse-cockpit-section-note">Review what already changed without leaving this read-only workspace.</div>
        </div>
        <div class="sales-console-queue-grid warehouse-cockpit-route-grid warehouse-visual-related-grid">${cards.map(renderCockpitRouteCard).join("")}</div>
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
      <div class="warehouse-console-inbound-card warehouse-visual-summary-card" data-warehouse-inbound-card="${escapeHtml(card.key || "")}">
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
      <div class="warehouse-console-inbound-card warehouse-visual-summary-card" data-warehouse-outbound-card="${escapeHtml(card.key || "")}">
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
    const dueToday = countFrom(payload, "due_today");
    const overdue = countFrom(payload, "overdue");
    const count = dueToday + overdue;
    const sideValue = count ? String(count) : "Open";
    const sideLabel = count ? "Needs Review" : "Queue";
    return `
      <button class="sales-console-queue-card regular warehouse-console-inbound-panel warehouse-cockpit-work-card" type="button" data-warehouse-section="inbound_priority" data-warehouse-open-inbound data-warehouse-cockpit-route-target="warehouse-console-worklist/inbound-receiving">
        <div class="sales-console-queue-main">
          <div class="sales-console-queue-title">Inbound Receiving</div>
          <div class="sales-console-queue-meta">Supplier stock due for read-only receiving review.</div>
        </div>
        <div class="sales-console-queue-side">
          <div class="sales-console-queue-count">${escapeHtml(sideValue)}</div>
          <div class="sales-console-queue-side-label">${escapeHtml(sideLabel)}</div>
        </div>
      </button>
    `;
  }

  function renderOutboundOverviewPanel(outbound) {
    const payload = outbound || {};
    const dueToday = countFrom(payload, "due_today");
    const overdue = countFrom(payload, "overdue");
    const shortStock = countFrom(payload, "short_stock");
    const count = dueToday + overdue + shortStock;
    const sideValue = count ? String(count) : "Open";
    const sideLabel = count ? "Needs Review" : "Queue";
    return `
      <button class="sales-console-queue-card regular warehouse-console-inbound-panel warehouse-console-outbound-panel warehouse-cockpit-work-card" type="button" data-warehouse-section="outbound_priority" data-warehouse-open-outbound data-warehouse-cockpit-route-target="warehouse-console-worklist/outbound-picking">
        <div class="sales-console-queue-main">
          <div class="sales-console-queue-title">Outbound Picking</div>
          <div class="sales-console-queue-meta">Customer demand waiting for warehouse readiness review.</div>
        </div>
        <div class="sales-console-queue-side">
          <div class="sales-console-queue-count">${escapeHtml(sideValue)}</div>
          <div class="sales-console-queue-side-label">${escapeHtml(sideLabel)}</div>
        </div>
      </button>
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
        <div class="warehouse-console-inbound-cards warehouse-visual-summary-grid">${cards.map(renderStockExceptionCard).join("")}</div>
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
  function renderSupplierReturnCandidateShell() {
    const statuses = [
      "Candidate Source",
      "Physical Evidence",
      "Manager Review",
      "Procurement Review",
      "Finance/Admin Review",
      "Supplier Handoff Request",
    ];
    const userPreview = [
      "Identify supplier-return goods",
      "Count candidate quantity",
      "Record condition",
      "Add evidence reference",
      "Send to manager review",
    ];
    const managerPreview = [
      "Request reinspection",
      "Mark quarantine review",
      "Mark supplier-return candidate",
      "Escalate to Procurement",
      "Escalate to Finance/Admin",
      "Reject supplier-return candidate",
    ];
    const evidence = [
      ["Supplier/source reference", "PO, receipt, quarantine, or Procurement instruction"],
      ["Item identity", "Item and unit posture"],
      ["Candidate quantity", "Physical count evidence"],
      ["Condition grade", "Damage, wrong item, quality, or quarantine posture"],
      ["Evidence reference", "Future attachment or note reference"],
      ["Manager event", "Supplier-return review trail"],
      ["Procurement marker", "Supplier-facing follow-up marker"],
    ];
    const ownership = [
      ["Warehouse", "Physical evidence and candidate posture"],
      ["Warehouse Manager", "Internal return recommendation"],
      ["Procurement", "Supplier communication, claim, and PO decision"],
      ["Finance/Admin", "Debit, payable, and document governance"],
    ];
    const policy = [
      ["Return Purchase Receipt", "Future policy only, blocked now"],
      ["Purchase Invoice return", "Future policy only, blocked now"],
      ["Stock Entry", "Future policy only, blocked now"],
      ["Stock Ledger / Stock Balance", "Future policy only, blocked now"],
      ["Supplier notification", "Procurement-owned, blocked now"],
      ["Reference handling", "Plain text/status only if later approved"],
    ];
    const plannedMarkup = (items) => items.map((item) => `
      <div class="warehouse-customer-return-planned" data-warehouse-supplier-return-planned-control aria-disabled="true">${escapeHtml(item)}</div>
    `).join("");
    const miniMarkup = (items) => items.map((item) => `
      <div class="warehouse-customer-return-mini">
        ${escapeHtml(item[0])}
        <span>${escapeHtml(item[1])}</span>
      </div>
    `).join("");
    return `
      <section class="sales-console-card sales-console-section warehouse-customer-return-shell warehouse-supplier-return-shell" data-warehouse-supplier-return-shell>
        <div class="warehouse-customer-return-head">
          <div class="warehouse-customer-return-copy">
            <h2 class="warehouse-customer-return-title">Supplier return candidate</h2>
            <div class="warehouse-customer-return-subtitle">Planned workflow shell for supplier-return evidence, manager recommendation, Procurement review, and Finance/Admin handoff.</div>
          </div>
          <span class="warehouse-customer-return-badge">Shell only</span>
        </div>
        <div class="warehouse-customer-return-guardrail" data-warehouse-supplier-return-guardrail>
          No supplier is notified, no stock is decreased, and no return Purchase Receipt, Purchase Invoice return, Stock Entry, Stock Ledger, or Stock Balance record is created from this shell.
        </div>
        <div class="warehouse-customer-return-status-strip">
          ${statuses.map((status) => `<div class="warehouse-customer-return-status-chip" data-warehouse-supplier-return-status>${escapeHtml(status)}</div>`).join("")}
        </div>
        <div class="warehouse-customer-return-grid">
          <section class="warehouse-customer-return-panel" data-warehouse-supplier-return-user-preview>
            <h3>Warehouse user preview</h3>
            <div class="warehouse-customer-return-items">${plannedMarkup(userPreview)}</div>
          </section>
          <section class="warehouse-customer-return-panel" data-warehouse-supplier-return-manager-preview>
            <h3>Manager preview</h3>
            <div class="warehouse-customer-return-items">${plannedMarkup(managerPreview)}</div>
          </section>
          <section class="warehouse-customer-return-panel" data-warehouse-supplier-return-evidence-preview>
            <h3>Evidence preview</h3>
            <div class="warehouse-customer-return-evidence-grid">${miniMarkup(evidence)}</div>
          </section>
          <section class="warehouse-customer-return-panel">
            <h3>Role ownership</h3>
            <div class="warehouse-customer-return-owner-grid">${miniMarkup(ownership)}</div>
          </section>
          <section class="warehouse-customer-return-panel warehouse-customer-return-policy-panel" data-warehouse-supplier-return-policy>
            <h3>Future document policy</h3>
            <div class="warehouse-customer-return-policy-grid">${miniMarkup(policy)}</div>
          </section>
        </div>
      </section>
    `;
  }



  function renderInternalTransferCandidateShell() {
    const statuses = [
      "Transfer Source",
      "Target Warehouse",
      "Physical Count",
      "Manager Review",
      "Inventory/Admin Review",
      "Document Policy",
    ];
    const userPreview = [
      "Start transfer check",
      "Count source quantity",
      "Record target warehouse",
      "Add evidence reference",
      "Send to manager review",
    ];
    const managerPreview = [
      "Request recount",
      "Mark transfer candidate",
      "Mark quarantine review",
      "Request Inventory/Admin review",
      "Reject transfer candidate",
      "Close transfer candidate",
    ];
    const evidence = [
      ["Source warehouse", "Where the stock is physically counted"],
      ["Target warehouse", "Requested internal destination"],
      ["Item identity", "Item and unit posture"],
      ["Requested quantity", "Transfer intent quantity"],
      ["Counted quantity", "Physical count evidence"],
      ["Evidence reference", "Future attachment or note reference"],
      ["Manager event", "Transfer candidate review trail"],
    ];
    const ownership = [
      ["Warehouse", "Physical count and transfer intent"],
      ["Warehouse Manager", "Internal transfer recommendation"],
      ["Inventory/Admin", "Stock document policy governance"],
      ["System/Admin", "Native-submit containment and policy"],
    ];
    const policy = [
      ["Stock Entry", "Future policy only, blocked now"],
      ["Stock Ledger / Stock Balance", "Future policy only, blocked now"],
      ["Stock Reconciliation", "Future policy only, blocked now"],
      ["Stock Reservation", "Future policy only, blocked now"],
      ["Stock movement", "Blocked now"],
      ["Reference handling", "Plain text/status only if later approved"],
    ];
    const plannedMarkup = (items) => items.map((item) => `
      <div class="warehouse-customer-return-planned" data-warehouse-internal-transfer-planned-control aria-disabled="true">${escapeHtml(item)}</div>
    `).join("");
    const miniMarkup = (items) => items.map((item) => `
      <div class="warehouse-customer-return-mini">
        ${escapeHtml(item[0])}
        <span>${escapeHtml(item[1])}</span>
      </div>
    `).join("");
    return `
      <section class="sales-console-card sales-console-section warehouse-customer-return-shell warehouse-internal-transfer-shell" data-warehouse-internal-transfer-shell>
        <div class="warehouse-customer-return-head">
          <div class="warehouse-customer-return-copy">
            <h2 class="warehouse-customer-return-title">Internal transfer candidate</h2>
            <div class="warehouse-customer-return-subtitle">Planned workflow shell for internal transfer intent, source count evidence, manager recommendation, and Inventory/Admin review.</div>
          </div>
          <span class="warehouse-customer-return-badge">Shell only</span>
        </div>
        <div class="warehouse-customer-return-guardrail" data-warehouse-internal-transfer-guardrail>
          No stock is moved, no Stock Entry is created or submitted, and no Stock Ledger or Stock Balance record is changed from this shell.
        </div>
        <div class="warehouse-customer-return-status-strip">
          ${statuses.map((status) => `<div class="warehouse-customer-return-status-chip" data-warehouse-internal-transfer-status>${escapeHtml(status)}</div>`).join("")}
        </div>
        <div class="warehouse-customer-return-grid">
          <section class="warehouse-customer-return-panel" data-warehouse-internal-transfer-user-preview>
            <h3>Warehouse user preview</h3>
            <div class="warehouse-customer-return-items">${plannedMarkup(userPreview)}</div>
          </section>
          <section class="warehouse-customer-return-panel" data-warehouse-internal-transfer-manager-preview>
            <h3>Manager preview</h3>
            <div class="warehouse-customer-return-items">${plannedMarkup(managerPreview)}</div>
          </section>
          <section class="warehouse-customer-return-panel" data-warehouse-internal-transfer-evidence-preview>
            <h3>Evidence preview</h3>
            <div class="warehouse-customer-return-evidence-grid">${miniMarkup(evidence)}</div>
          </section>
          <section class="warehouse-customer-return-panel">
            <h3>Role ownership</h3>
            <div class="warehouse-customer-return-owner-grid">${miniMarkup(ownership)}</div>
          </section>
          <section class="warehouse-customer-return-panel warehouse-customer-return-policy-panel" data-warehouse-internal-transfer-policy>
            <h3>Future document policy</h3>
            <div class="warehouse-customer-return-policy-grid">${miniMarkup(policy)}</div>
          </section>
        </div>
      </section>
    `;
  }


  function renderPlannedWorkflowShells() {
    const workflows = [
      {
        key: "customer-return",
        title: "Customer return intake",
        note: "Physical return intake evidence, inspection posture, and Sales or Finance handoff.",
        owner: "Sales / Finance",
        guardrail: "No stock increase, no Sales Return, no Credit Note.",
        detail: renderCustomerReturnIntakeShell(),
      },
      {
        key: "supplier-return",
        title: "Supplier return candidate",
        note: "Supplier-return evidence, manager recommendation, Procurement review, and Finance/Admin handoff.",
        owner: "Procurement / Finance",
        guardrail: "No supplier notification, no stock decrease, no return purchase document.",
        detail: renderSupplierReturnCandidateShell(),
      },
      {
        key: "internal-transfer",
        title: "Internal transfer candidate",
        note: "Internal transfer intent, source count evidence, manager recommendation, and Inventory/Admin review.",
        owner: "Inventory / Admin",
        guardrail: "No stock movement, no Stock Entry, no Stock Ledger or Balance change.",
        detail: renderInternalTransferCandidateShell(),
      },
    ];
    const cards = workflows.map((workflow) => `
      <article class="warehouse-planned-workflow-card" data-warehouse-planned-workflow-card="${escapeHtml(workflow.key)}">
        <div class="warehouse-planned-workflow-card-head">
          <div class="warehouse-planned-workflow-title">${escapeHtml(workflow.title)}</div>
          <span class="warehouse-planned-workflow-kicker">Shell only</span>
        </div>
        <div class="warehouse-planned-workflow-note">${escapeHtml(workflow.note)}</div>
        <div class="warehouse-planned-workflow-guardrail">${escapeHtml(workflow.guardrail)}</div>
        <div class="warehouse-planned-workflow-meta">
          <span>${escapeHtml(workflow.owner)}</span>
          <span>Request only</span>
          <span>No document created</span>
        </div>
        <button class="warehouse-planned-workflow-toggle" type="button" aria-expanded="false" data-warehouse-planned-workflow-toggle="${escapeHtml(workflow.key)}">View details</button>
      </article>
    `).join("");
    const details = workflows.map((workflow) => `
      <div class="warehouse-planned-workflow-detail" data-warehouse-planned-workflow-detail="${escapeHtml(workflow.key)}" hidden>
        ${workflow.detail}
      </div>
    `).join("");
    return `
      <section class="sales-console-card sales-console-section warehouse-planned-workflows" data-warehouse-planned-workflows>
        <div class="warehouse-planned-workflows-head">
          <div class="warehouse-planned-workflows-copy">
            <h2 class="warehouse-planned-workflows-title">Planned workflow shells</h2>
            <div class="warehouse-planned-workflows-subtitle">Future controlled workflow lanes stay compact here. Expand one lane to inspect guardrails and ownership; no ERP document or stock action starts from this section.</div>
          </div>
          <span class="warehouse-planned-workflows-mode">Planned only</span>
        </div>
        <div class="warehouse-planned-workflows-grid">${cards}</div>
        <div class="warehouse-planned-workflow-details">${details}</div>
      </section>
    `;
  }

  function renderOverview(page, payload) {
    ensureStyle();
    const kpis = Array.isArray(payload.kpis) ? payload.kpis.slice(0, 6) : [];
    const pulseCards = cockpitPulseCards(payload, kpis);
    const heroPulseCards = pulseCards.slice(0, 3);
    const contextPulseCards = pulseCards.slice(3);
    const $root = $(`
      <div class="sales-console-shell warehouse-console-shell warehouse-overview-shared warehouse-visual-foundation" data-erpw-workspace="warehouse" data-erpw-console-runtime="ready" data-erpw-console-bootstrap="ready" data-warehouse-cockpit="ready" data-warehouse-visual-foundation="overview-shared-ui">
        <section class="sales-console-card sales-console-header warehouse-console-header warehouse-visual-command" data-warehouse-cockpit-command>
          <div class="sales-console-header-row warehouse-cockpit-command-row">
            <div class="sales-console-header-copy">
              <h1 class="sales-console-title warehouse-console-title">Warehouse Console</h1>
              <div class="sales-console-header-note warehouse-console-note">Read-only review and planning workspace for inbound receiving, outbound picking, stock exceptions, posted movements, and transfer visibility.</div>
            </div>
          </div>
          <div class="sales-console-kpi-grid warehouse-console-kpi-grid warehouse-cockpit-pulse-grid" data-count="3" data-warehouse-cockpit-pulse>${heroPulseCards.map(renderPulseCard).join("")}</div>
        </section>
        <section class="sales-console-card sales-console-section warehouse-cockpit-pulse-section" data-warehouse-cockpit-pulse-context>
          <div class="sales-console-section-head">
            <h2 class="sales-console-section-title">Warehouse Pulse</h2>
            <div class="warehouse-cockpit-pulse-tools">
              <button class="warehouse-console-refresh" type="button" data-warehouse-refresh>Refresh</button>
            </div>
          </div>
          <div class="sales-console-queue-grid warehouse-cockpit-pulse-grid-secondary">${contextPulseCards.map(renderPulseContextCard).join("")}</div>
        </section>
        ${renderCockpitStart(payload, kpis)}
        ${renderCockpitActionCenter(payload.action_center || {})}
        ${renderPlannedWorkflowShells()}
      </div>
    `);
    $root.find("[data-warehouse-planned-workflow-toggle]").on("click", (event) => {
      event.preventDefault();
      const $toggle = $(event.currentTarget);
      const workflowKey = $toggle.attr("data-warehouse-planned-workflow-toggle") || "";
      const wasExpanded = $toggle.attr("aria-expanded") === "true";
      $root.find("[data-warehouse-planned-workflow-toggle]").attr("aria-expanded", "false").text("View details").closest("[data-warehouse-planned-workflow-card]").removeClass("is-expanded");
      $root.find("[data-warehouse-planned-workflow-detail]").prop("hidden", true);
      if (!wasExpanded && workflowKey) {
        $toggle.attr("aria-expanded", "true").text("Hide details").closest("[data-warehouse-planned-workflow-card]").addClass("is-expanded");
        $root.find(`[data-warehouse-planned-workflow-detail="${workflowKey}"]`).prop("hidden", false);
      }
    });
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
    $root.find("[data-warehouse-action-center-open]").on("click", (event) => {
      event.preventDefault();
      const card = event.currentTarget.closest("[data-warehouse-action-center-card]");
      const route = card ? card.getAttribute("data-warehouse-action-center-route") : "";
      const routePart = card ? card.getAttribute("data-warehouse-action-center-route-part") : "";
      if (route === WORKLIST_PAGE_KEY && isSupportedWorklistQueue(routePart)) {
        frappe.route_options = {};
        frappe.set_route(WORKLIST_PAGE_KEY, worklistViewName(routePart));
      }
    });
    replacePageBody(page, $root);
    cleanupWarehousePageHeads();
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

  function cleanupWarehousePageHeads() {
    if (!isWarehouseOwnedRouteKey(activeWarehouseRouteKey())) return;
    document.querySelectorAll(".page-head").forEach((head) => {
      if (head instanceof HTMLElement) head.remove();
    });
  }

  function replaceWarehouseRouteHost(viewState, $root) {
    if (!viewState || !viewState.$host) return;
    removeDuplicateWarehouseHosts(viewState.$host.get(0));
    viewState.$host.empty().append($root);
    cleanupWarehousePageHeads();
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

  function receivingLoadSignature(purchaseOrder) {
    return `${receivingRouteSignature()}::${String(purchaseOrder || "").trim()}`;
  }

  function hasRenderedReceivingShell(viewState, purchaseOrder) {
    const host = viewState && viewState.$host && viewState.$host.get ? viewState.$host.get(0) : null;
    if (!host || !document.documentElement.contains(host)) return false;
    const shell = host.querySelector('.warehouse-receiving-shell[data-warehouse-view="receiving-review"]');
    if (!shell) return false;
    return String(shell.getAttribute("data-warehouse-receiving-order") || "") === String(purchaseOrder || "").trim();
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
      <div class="warehouse-inbound-queue-card warehouse-visual-summary-card" data-warehouse-inbound-queue-card="${escapeHtml(card.key || "")}" data-warehouse-outbound-queue-card="${escapeHtml(card.key || "")}">
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
    if (row.purchase_order) {
      const postureKey = String(row.state_key || "review").replace(/[^a-z0-9_-]+/gi, "_").toLowerCase();
      return `
        <article class="warehouse-inbound-row warehouse-visual-row-card is-receiving" data-warehouse-inbound-row="${escapeHtml(rowKey)}" data-warehouse-outbound-row="${escapeHtml(rowKey)}" data-warehouse-inbound-posture="${escapeHtml(postureKey)}">
          <div class="warehouse-inbound-row-summary warehouse-visual-row-header">
            <div class="warehouse-inbound-row-identity">
              <div class="warehouse-inbound-order">${escapeHtml(rowKey)}</div>
              <div class="warehouse-inbound-meta">${escapeHtml(partner || "Supplier not visible")}</div>
            </div>
            <span class="warehouse-inbound-status-chip is-${escapeHtml(postureKey)}">${escapeHtml(row.state_label || row.status || "Review")}</span>
          </div>
          <div class="warehouse-inbound-row-facts warehouse-visual-row-facts">
            <div class="warehouse-inbound-row-fact" data-warehouse-inbound-row-fact="supplier"><span>Supplier</span><strong>${escapeHtml(partner || "Not visible")}</strong></div>
            <div class="warehouse-inbound-row-fact" data-warehouse-inbound-row-fact="warehouse"><span>Target warehouse</span><strong>${escapeHtml(row.target_warehouse || "Not visible")}</strong></div>
            <div class="warehouse-inbound-row-fact" data-warehouse-inbound-row-fact="expected"><span>Expected</span><strong>${escapeHtml(row.age_label || row.required_date || "Not visible")}</strong></div>
            <div class="warehouse-inbound-row-fact" data-warehouse-inbound-row-fact="open"><span>Open posture</span><strong>${escapeHtml(row.remaining_summary || "No open quantity summary")} - ${escapeHtml(progress)}</strong></div>
          </div>
          <div class="warehouse-inbound-row-actions warehouse-visual-action-strip">
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-row-toggle>View lines</button>
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-row-open-detail>Open receiving review</button>
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
    if (row.sales_order) {
      const postureKey = String(row.state_key || "review").replace(/[^a-z0-9_-]+/gi, "_").toLowerCase();
      return `
        <article class="warehouse-inbound-row warehouse-outbound-row warehouse-visual-row-card is-picking" data-warehouse-inbound-row="${escapeHtml(rowKey)}" data-warehouse-outbound-row="${escapeHtml(rowKey)}" data-warehouse-outbound-posture="${escapeHtml(postureKey)}">
          <div class="warehouse-inbound-row-summary warehouse-outbound-row-summary warehouse-visual-row-header">
            <div class="warehouse-inbound-row-identity">
              <div class="warehouse-inbound-order">${escapeHtml(rowKey)}</div>
              <div class="warehouse-inbound-meta">${escapeHtml(partner || "Customer not visible")}</div>
            </div>
            <span class="warehouse-inbound-status-chip warehouse-outbound-status-chip is-${escapeHtml(postureKey)}">${escapeHtml(row.state_label || row.status || "Review")}</span>
          </div>
          <div class="warehouse-inbound-row-facts warehouse-outbound-row-facts warehouse-visual-row-facts">
            <div class="warehouse-inbound-row-fact" data-warehouse-outbound-row-fact="customer"><span>Customer</span><strong>${escapeHtml(partner || "Not visible")}</strong></div>
            <div class="warehouse-inbound-row-fact" data-warehouse-outbound-row-fact="warehouse"><span>Warehouse</span><strong>${escapeHtml(row.target_warehouse || "Not visible")}</strong></div>
            <div class="warehouse-inbound-row-fact" data-warehouse-outbound-row-fact="due"><span>Delivery timing</span><strong>${escapeHtml(row.age_label || row.required_date || "Not visible")}</strong></div>
            <div class="warehouse-inbound-row-fact" data-warehouse-outbound-row-fact="open"><span>Picking posture</span><strong>${escapeHtml(row.remaining_summary || "No open quantity summary")} - ${escapeHtml(progress)}</strong></div>
          </div>
          <div class="warehouse-inbound-row-actions warehouse-outbound-row-actions warehouse-visual-action-strip">
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-row-toggle>View lines</button>
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-row-open-picking-detail>Open picking review</button>
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
    const detailButton = row.purchase_order
      ? '<button type="button" class="warehouse-inbound-queue-button" data-warehouse-row-open-detail>View details</button>'
      : row.sales_order
        ? '<button type="button" class="warehouse-inbound-queue-button" data-warehouse-row-open-picking-detail>View details</button>'
        : "";
    return `
      <article class="warehouse-inbound-row warehouse-visual-row-card" data-warehouse-inbound-row="${escapeHtml(rowKey)}" data-warehouse-outbound-row="${escapeHtml(rowKey)}">
        <div class="warehouse-inbound-row-main warehouse-visual-row-header">
          <div>
            <div class="warehouse-inbound-order">${escapeHtml(rowKey)}</div>
            <div class="warehouse-inbound-meta">${escapeHtml(partner)}</div>
          </div>
          <div class="warehouse-inbound-meta">${escapeHtml(row.target_warehouse || "")}</div>
          <div class="warehouse-inbound-meta">${escapeHtml(row.age_label || row.required_date || "")}</div>
          <div class="warehouse-inbound-meta">${escapeHtml(row.remaining_summary || "")} - ${escapeHtml(progress)}</div>
          <div class="warehouse-receiving-actions warehouse-visual-action-strip">
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

  function renderQueueGroup(group, queueKey) {
    const rows = Array.isArray(group.rows) ? group.rows : [];
    const groupKey = String(group.key || "");
    const inboundGroupKeys = ["overdue", "due_today", "partially_received", "expected_soon"];
    const emptyText = normalizeQueueKey(queueKey) === OUTBOUND_QUEUE_KEY
      ? "No outbound picking matches these filters."
      : inboundGroupKeys.includes(groupKey)
        ? "No receiving matches these filters."
        : "No work matches these filters.";
    return `
      <section class="warehouse-inbound-group is-${escapeHtml(groupKey)}" data-warehouse-inbound-group="${escapeHtml(groupKey)}" data-warehouse-outbound-group="${escapeHtml(groupKey)}">
        <div class="warehouse-inbound-group-head">
          <h2 class="warehouse-inbound-group-title">${escapeHtml(group.title || "")}</h2>
          <div class="warehouse-inbound-group-note">${escapeHtml(rows.length ? `${rows.length} shown` : group.summary || "")}</div>
        </div>
        <div class="warehouse-console-card-grid warehouse-visual-row-list">
          ${rows.length ? rows.map(renderQueueRow).join("") : `<div class="warehouse-inbound-row warehouse-visual-fallback" data-warehouse-inbound-empty data-warehouse-outbound-empty><span class="warehouse-inbound-meta">${escapeHtml(emptyText)}</span></div>`}
        </div>
      </section>
    `;
  }

  function renderStockExceptionCard(card) {
    return `
      <div class="warehouse-inbound-queue-card warehouse-visual-summary-card" data-warehouse-stock-exception-card="${escapeHtml(card.key || "")}">
        <div class="warehouse-inbound-queue-card-label">${escapeHtml(card.label || card.title || "")}</div>
        <div class="warehouse-inbound-queue-card-value">${escapeHtml(cardValue(card))}</div>
        <div class="warehouse-inbound-queue-card-note">${escapeHtml(card.note || "")}</div>
      </div>
    `;
  }

  function stockExceptionPostureKey(row) {
    return String(row.exception_key || row.state_key || "review").replace(/[^a-z0-9_-]+/gi, "_").toLowerCase();
  }

  function renderStockExceptionRow(row) {
    const targets = row.route_targets || {};
    const reviewTarget = targets.exception_review || {};
    const pickingTarget = targets.picking || {};
    const receivingTarget = targets.receiving || {};
    const postureTarget = targets.stock_posture || targets.posture || {};
    const reviewToken = reviewTarget.context_token || row.context_token || "";
    const postureToken = postureTarget.context_token || row.stock_posture_token || "";
    const postureKey = stockExceptionPostureKey(row);
    const reviewButton = reviewToken
      ? '<button type="button" class="warehouse-inbound-queue-button" data-warehouse-stock-exception-route-detail>Review exception</button>'
      : "";
    const postureButton = postureToken
      ? '<button type="button" class="warehouse-inbound-queue-button" data-warehouse-stock-exception-route-posture>Review stock posture</button>'
      : "";
    const pickingButton = pickingTarget.sales_order
      ? '<button type="button" class="warehouse-inbound-queue-button" data-warehouse-stock-exception-route-picking>View picking review</button>'
      : "";
    const receivingButton = receivingTarget.purchase_order
      ? '<button type="button" class="warehouse-inbound-queue-button" data-warehouse-stock-exception-route-receiving>View inbound review</button>'
      : "";
    return `
      <article class="warehouse-stock-exception-row warehouse-visual-row-card is-premium" data-warehouse-stock-exception-row="${escapeHtml(row.key || "")}" data-warehouse-stock-exception-token="${escapeHtml(reviewToken)}" data-warehouse-stock-exception-posture-token="${escapeHtml(postureToken)}" data-warehouse-stock-exception-sales-order="${escapeHtml(row.sales_order || "")}" data-warehouse-stock-exception-receiving-order="${escapeHtml(row.expected_inbound_order || "")}" data-warehouse-stock-exception-posture="${escapeHtml(postureKey)}">
        <div class="warehouse-stock-exception-row-summary warehouse-visual-row-header">
          <div class="warehouse-stock-exception-row-identity">
            <div class="warehouse-inbound-order">${escapeHtml(row.sales_order || "Demand not visible")}</div>
            <div class="warehouse-inbound-meta">${escapeHtml(row.customer || "Customer not visible")} · ${escapeHtml(row.item_code || "Item not visible")} ${escapeHtml(row.item_name || "")}</div>
          </div>
          <span class="warehouse-inbound-status-chip is-${escapeHtml(postureKey)}">${escapeHtml(row.exception_label || "Needs Review")}</span>
        </div>
        <div class="warehouse-stock-exception-facts warehouse-visual-row-facts" data-warehouse-stock-exception-row-facts>
          <div class="warehouse-stock-exception-fact" data-warehouse-stock-exception-row-fact="warehouse"><span>Warehouse</span><strong>${escapeHtml(row.source_warehouse || "Not visible")}</strong></div>
          <div class="warehouse-stock-exception-fact" data-warehouse-stock-exception-row-fact="timing"><span>Timing</span><strong>${escapeHtml(row.urgency_label || row.required_date || "Not visible")}</strong></div>
          <div class="warehouse-stock-exception-fact" data-warehouse-stock-exception-row-fact="open"><span>Open demand</span><strong>${escapeHtml(row.pending_qty || "0")} ${escapeHtml(row.uom || "")}</strong></div>
          <div class="warehouse-stock-exception-fact" data-warehouse-stock-exception-row-fact="available"><span>Available posture</span><strong>${escapeHtml(row.available_qty || "N/A")} available · ${escapeHtml(row.projected_qty || "N/A")} projected</strong></div>
          <div class="warehouse-stock-exception-fact" data-warehouse-stock-exception-row-fact="short"><span>Short posture</span><strong>${escapeHtml(row.short_qty || "0")} ${escapeHtml(row.uom || "")}</strong></div>
          <div class="warehouse-stock-exception-fact" data-warehouse-stock-exception-row-fact="inbound"><span>Inbound cover</span><strong>${escapeHtml(row.expected_inbound_qty || "0")} ${escapeHtml(row.expected_inbound_date || "")}</strong></div>
        </div>
        <div class="warehouse-stock-exception-actions warehouse-visual-action-strip" data-warehouse-stock-exception-actions>
          <button type="button" class="warehouse-inbound-queue-button" data-warehouse-stock-exception-toggle>View details</button>
          ${reviewButton}
          ${postureButton}
          ${pickingButton}
          ${receivingButton}
        </div>
        <div class="warehouse-stock-exception-details" data-warehouse-stock-exception-details>
          <div class="warehouse-stock-exception-detail">${escapeHtml(row.explanation || "No exception explanation visible.")}</div>
          <div class="warehouse-stock-exception-detail">Next review: open a custom Warehouse review route if one is visible for this row.</div>
        </div>
      </article>
    `;
  }

  function renderStockExceptionGroup(group) {
    const rows = Array.isArray(group.rows) ? group.rows : [];
    const groupKey = String(group.key || "");
    const emptyText = {
      needs_stock_review: "No shortage-risk rows match these filters.",
      inbound_cover_expected: "No inbound-cover rows match these filters.",
      urgent_aging: "No urgent or aging demand matches these filters.",
      warehouse_posture_missing: "No missing warehouse posture matches these filters.",
    }[groupKey] || "No stock exceptions match these filters.";
    return `
      <section class="warehouse-inbound-group" data-warehouse-stock-exception-group="${escapeHtml(groupKey)}">
        <div class="warehouse-inbound-group-head">
          <h2 class="warehouse-inbound-group-title">${escapeHtml(group.title || "")}</h2>
          <div class="warehouse-inbound-group-note">${escapeHtml(rows.length ? `${rows.length} shown` : group.summary || "")}</div>
        </div>
        <div class="warehouse-console-card-grid warehouse-visual-row-list">
          ${rows.length ? rows.map(renderStockExceptionRow).join("") : `<div class="warehouse-stock-exception-row warehouse-visual-fallback" data-warehouse-stock-exception-empty><span class="warehouse-inbound-meta">${escapeHtml(emptyText)}</span></div>`}
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
    const isLoadingState = statePayload.kind === "loading";
    const loadingCards = [
      { key: "loading_shortage", label: "Shortage risk", value: "--", note: "Checking open demand." },
      { key: "loading_cover", label: "Inbound cover", value: "--", note: "Checking expected supply." },
      { key: "loading_posture", label: "Missing posture", value: "--", note: "Checking warehouse posture." },
      { key: "loading_urgent", label: "Urgent review", value: "--", note: "Checking aging demand." },
    ];
    const visibleCards = cards.length ? cards : (isLoadingState ? loadingCards : cards);
    const loadingControls = `
      <div class="warehouse-inbound-loading-field"><span>Demand</span><i></i></div>
      <div class="warehouse-inbound-loading-field"><span>Item</span><i></i></div>
      <div class="warehouse-inbound-loading-field"><span>Warehouse</span><i></i></div>
      <div class="warehouse-inbound-loading-field"><span>Exception state</span><i></i></div>
      <div class="warehouse-inbound-loading-status">Checking stock exceptions...</div>
    `;
    const controlsMarkup = isLoadingState
      ? loadingControls
      : `
            ${fields.map(controlField).join("")}
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-apply>Apply</button>
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-reset>Reset</button>
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-refresh>Refresh</button>
        `;
    const $root = $(`
      <div class="sales-console-shell warehouse-inbound-shell warehouse-stock-exception-shell warehouse-stock-exception-premium-shell warehouse-visual-foundation" data-erpw-workspace="warehouse" data-warehouse-view="stock-exceptions" data-warehouse-queue-key="${STOCK_EXCEPTIONS_KEY}" data-warehouse-stock-exception-shell="true" data-warehouse-visual-foundation="stock-exceptions-premium" data-erpw-console-runtime="ready">
        <section class="warehouse-inbound-queue-header warehouse-visual-command" data-warehouse-stock-exception-command>
          <div class="warehouse-inbound-queue-head">
            <div class="warehouse-inbound-command">
              <h1 class="warehouse-inbound-queue-title">${escapeHtml(payload.summary && payload.summary.title || "Stock Exceptions")}</h1>
              <div class="warehouse-inbound-queue-note">${escapeHtml(payload.summary && payload.summary.subtitle || "Outbound blockers, inbound cover, and warehouse posture gaps.")}</div>
            </div>
          </div>
          <div class="warehouse-inbound-queue-cards warehouse-visual-summary-grid ${isLoadingState ? "is-loading" : ""}">${visibleCards.map(renderStockExceptionCard).join("")}</div>
          <div class="warehouse-inbound-controls warehouse-visual-filter-strip ${isLoadingState ? "is-loading" : ""}">
            ${controlsMarkup}
          </div>
        </section>
        <div class="warehouse-inbound-groups">
          ${statePayload.kind === "restricted" || statePayload.kind === "error"
            ? `<section class="warehouse-inbound-group warehouse-visual-fallback" data-warehouse-stock-exception-group="state"><h2 class="warehouse-inbound-group-title">${escapeHtml(statePayload.title || "Stock exceptions unavailable")}</h2><div class="warehouse-inbound-meta" data-warehouse-stock-exception-empty>${escapeHtml(statePayload.detail || "Stock exceptions could not be loaded. Refresh or contact an administrator.")}</div></section>`
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
    $root.find("[data-warehouse-stock-exception-route-posture]").on("click", function (event) {
      event.preventDefault();
      const token = String($(this).closest("[data-warehouse-stock-exception-posture-token]").attr("data-warehouse-stock-exception-posture-token") || "").trim();
      if (token) frappe.set_route(STOCK_POSTURE_PAGE_KEY, token);
    });
    $root.find("[data-warehouse-stock-exception-route-receiving]").on("click", function (event) {
      event.preventDefault();
      const purchaseOrder = String($(this).closest("[data-warehouse-stock-exception-receiving-order]").attr("data-warehouse-stock-exception-receiving-order") || "").trim();
      if (purchaseOrder) frappe.set_route(RECEIVING_PAGE_KEY, purchaseOrder);
    });
    $root.find("[data-warehouse-stock-exception-toggle]").on("click", function (event) {
      event.preventDefault();
      $(this).closest("[data-warehouse-stock-exception-row]").toggleClass("is-expanded");
    });
    replaceWarehouseRouteHost(viewState, $root);
  }

  function movementCardByKey(cards, keys) {
    const wanted = Array.isArray(keys) ? keys : [keys];
    return (Array.isArray(cards) ? cards : []).find((card) => wanted.includes(String(card && card.key || ""))) || {};
  }

  function movementCardDisplay(cards, keys, fallback) {
    const card = movementCardByKey(cards, keys);
    const value = card && Object.prototype.hasOwnProperty.call(card, "value") ? cardValue(card) : "";
    return value ? value : fallback;
  }

  function movementCommandChips(payload) {
    const summary = payload && payload.summary ? payload.summary : {};
    const chips = Array.isArray(summary.chips) ? summary.chips.map((chip) => chip && chip.label ? chip.label : chip).filter(Boolean) : [];
    return ["Read-only", "Warehouse movement", freshnessText(payload), ...chips.filter((chip) => !/^read-only$/i.test(String(chip)))].slice(0, 5);
  }

  function movementCommandFacts(payload, cards) {
    return [
      { key: "recent", label: "Recent movement", value: movementCardDisplay(cards, ["total_movements", "recent_movements"], "Not visible") },
      { key: "direct", label: "Direct posture", value: movementCardDisplay(cards, ["internal_transfers", "direct_transfers"], "Not visible") },
      { key: "receipts", label: "Inbound posture", value: movementCardDisplay(cards, ["receipts"], "Not visible") },
      { key: "needs_review", label: "Needs review", value: movementCardDisplay(cards, ["needs_review"], "0") },
    ];
  }

  function renderMovementCommandFact(fact) {
    return `
      <div class="warehouse-movement-command-fact warehouse-visual-fact" data-warehouse-movement-command-fact="${escapeHtml(fact.key || "")}">
        <span>${escapeHtml(fact.label || "")}</span>
        <strong>${escapeHtml(fact.value || "Not visible")}</strong>
      </div>
    `;
  }

  function renderMovementCard(card) {
    return `
      <div class="warehouse-inbound-queue-card warehouse-visual-summary-card" data-warehouse-movement-card="${escapeHtml(card.key || "")}">
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
      <article class="warehouse-inbound-row warehouse-stock-exception-row warehouse-movement-row warehouse-visual-row-card is-premium" data-warehouse-movement-row="${escapeHtml(row.movement_id || row.key || "")}">
        <div class="warehouse-movement-row-main warehouse-visual-row-header" data-warehouse-movement-row-main>
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
          <div class="warehouse-movement-actions warehouse-visual-action-strip">
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-row-toggle>View lines</button>
            ${reviewButton}
          </div>
        </div>
        <div class="warehouse-movement-row-facts warehouse-visual-row-facts" data-warehouse-movement-row-facts>
          <div class="warehouse-movement-row-fact" data-warehouse-movement-row-fact="posted"><span>Posted</span><strong>${escapeHtml(row.posting_date || "Date not visible")}</strong></div>
          <div class="warehouse-movement-row-fact" data-warehouse-movement-row-fact="purpose"><span>Purpose</span><strong>${escapeHtml(row.purpose || row.movement_type || "Movement posture")}</strong></div>
          <div class="warehouse-movement-row-fact" data-warehouse-movement-row-fact="direction"><span>Direction</span><strong>${escapeHtml(row.direction_label || "Warehouse posture needs review")}</strong></div>
          <div class="warehouse-movement-row-fact" data-warehouse-movement-row-fact="items"><span>Items</span><strong>${escapeHtml(row.item_count == null ? "0" : row.item_count)} shown</strong></div>
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
        <div class="warehouse-console-card-grid warehouse-visual-row-list">
          ${rows.length ? rows.map(renderMovementRow).join("") : `<div class="warehouse-stock-exception-row warehouse-visual-fallback" data-warehouse-movement-empty><span class="warehouse-inbound-meta">No movement records match these filters.</span></div>`}
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
    const isLoadingState = String(statePayload.kind || "") === "loading";
    const loadingCards = [
      { key: "loading_recent", label: "Recent Movement", value: "--", note: "Checking posted movement records." },
      { key: "loading_direct", label: "Direct Posture", value: "--", note: "Checking warehouse movement posture." },
      { key: "loading_inbound", label: "Inbound Posture", value: "--", note: "Checking receipt movement evidence." },
      { key: "loading_review", label: "Needs Review", value: "--", note: "Checking movement rows." },
    ];
    const visibleCards = cards.length ? cards : (isLoadingState ? loadingCards : cards);
    const loadingControls = `
      <div class="warehouse-inbound-loading-field"><span>Movement</span><i></i></div>
      <div class="warehouse-inbound-loading-field"><span>Warehouse</span><i></i></div>
      <div class="warehouse-inbound-loading-field"><span>Movement Type</span><i></i></div>
      <button type="button" class="warehouse-inbound-queue-button" disabled>Apply</button>
      <button type="button" class="warehouse-inbound-queue-button" disabled>Reset</button>
      <button type="button" class="warehouse-inbound-queue-button" disabled>Refresh</button>
      <div class="warehouse-inbound-loading-status">Checking movement visibility...</div>
    `;
    const $root = $(`
      <div class="sales-console-shell warehouse-inbound-shell warehouse-movement-shell warehouse-movement-premium-shell warehouse-visual-foundation" data-erpw-workspace="warehouse" data-warehouse-view="movement-visibility" data-warehouse-queue-key="${MOVEMENT_VISIBILITY_KEY}" data-warehouse-movement-shell="true" data-warehouse-visual-foundation="w13-movement-premium" data-erpw-console-runtime="ready">
        <section class="warehouse-inbound-queue-header warehouse-movement-command-header warehouse-visual-command" data-warehouse-movement-command>
          <div class="warehouse-inbound-queue-head">
            <div class="warehouse-movement-command">
              <h1 class="warehouse-inbound-queue-title">${escapeHtml(payload.summary && payload.summary.title || "Movement Visibility")}</h1>
              <div class="warehouse-inbound-queue-note">${escapeHtml(payload.summary && payload.summary.subtitle || "Recorded stock movement posture across warehouses.")}</div>
            </div>
          </div>
          <div class="warehouse-inbound-queue-cards warehouse-visual-summary-grid ${isLoadingState ? "is-loading" : ""}">${visibleCards.map(renderMovementCard).join("")}</div>
          <div class="warehouse-inbound-controls warehouse-visual-filter-strip ${isLoadingState ? "is-loading" : ""}">
            ${isLoadingState ? loadingControls : `
              ${fields.map(controlField).join("")}
              <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-apply>Apply</button>
              <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-reset>Reset</button>
              <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-refresh>Refresh</button>
            `}
          </div>
        </section>
        <div class="warehouse-inbound-groups">
          ${statePayload.kind === "restricted" || statePayload.kind === "error"
            ? `<section class="warehouse-inbound-group warehouse-visual-fallback" data-warehouse-movement-group="state"><h2 class="warehouse-inbound-group-title">${escapeHtml(statePayload.title || "Movement visibility unavailable")}</h2><div class="warehouse-inbound-meta" data-warehouse-movement-empty>${escapeHtml(statePayload.detail || "Movement visibility could not be loaded. Refresh or contact an administrator.")}</div></section>`
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
    replaceWarehouseRouteHost(viewState, $root);
  }

  function transferCardByKey(cards, keys) {
    const wanted = Array.isArray(keys) ? keys : [keys];
    return (Array.isArray(cards) ? cards : []).find((card) => wanted.includes(String(card && card.key || ""))) || {};
  }

  function transferCardDisplay(cards, keys, fallback) {
    const card = transferCardByKey(cards, keys);
    const value = card && Object.prototype.hasOwnProperty.call(card, "value") ? cardValue(card) : "";
    return value ? value : fallback;
  }

  function transferCommandChips(payload) {
    const summary = payload && payload.summary ? payload.summary : {};
    const chips = Array.isArray(summary.chips) ? summary.chips.map((chip) => chip && chip.label ? chip.label : chip).filter(Boolean) : [];
    return ["Read-only", "Transfer posture", freshnessText(payload), ...chips.filter((chip) => !/^read-only$/i.test(String(chip)))].slice(0, 5);
  }

  function transferFallbackCards(cards, statePayload, rows) {
    if (Array.isArray(cards) && cards.length) return cards;
    const rowCount = Array.isArray(rows) ? rows.length : 0;
    return [
      { key: "needs_review", label: "Needs Review", value: statePayload && statePayload.kind === "loading" ? "Checking" : "0", note: "Missing or mixed warehouse posture." },
      { key: "direct_transfers", label: "Direct Transfers", value: rowCount ? rowCount : "Not visible", note: "Clear source and target warehouse posture." },
      { key: "recently_posted", label: "Recently Posted", value: rowCount, note: "Submitted transfer records in this window." },
      { key: "transfer_quantity", label: "Transfer Quantity", value: "Not visible", note: "Operational quantity summary." },
    ];
  }

  function transferCommandFacts(payload, cards, rows) {
    return [
      { key: "needs_review", label: "Needs review", value: transferCardDisplay(cards, ["needs_review"], "0") },
      { key: "direct", label: "Direct transfers", value: transferCardDisplay(cards, ["direct_transfers"], "Not visible") },
      { key: "transit", label: "Transit related", value: transferCardDisplay(cards, ["transit_related"], "Not visible") },
      { key: "posted", label: "Recently posted", value: transferCardDisplay(cards, ["recently_posted", "total_transfers"], Array.isArray(rows) ? String(rows.length) : "Not visible") },
    ];
  }

  function renderTransferCommandFact(fact) {
    return `
      <div class="warehouse-transfer-command-fact warehouse-visual-fact" data-warehouse-transfer-command-fact="${escapeHtml(fact.key || "")}">
        <span>${escapeHtml(fact.label || "")}</span>
        <strong>${escapeHtml(fact.value || "Not visible")}</strong>
      </div>
    `;
  }

  function renderTransferCard(card) {
    const value = String(cardValue(card));
    const displayValue = String(card && card.key || "") === "transfer_quantity" && !/\d/.test(value) ? "--" : value;
    return `
      <div class="warehouse-inbound-queue-card warehouse-visual-summary-card" data-warehouse-transfer-card="${escapeHtml(card.key || "")}" data-warehouse-transfer-summary-card>
        <div class="warehouse-inbound-queue-card-label">${escapeHtml(card.label || card.title || "")}</div>
        <div class="warehouse-inbound-queue-card-value">${escapeHtml(displayValue)}</div>
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
      <article class="warehouse-inbound-row warehouse-stock-exception-row warehouse-transfer-row warehouse-visual-row-card is-premium" data-warehouse-transfer-row="${escapeHtml(row.transfer_id || row.key || "")}">
        <div class="warehouse-transfer-row-main warehouse-visual-row-header" data-warehouse-transfer-row-main>
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
          <div class="warehouse-transfer-actions warehouse-visual-action-strip" data-warehouse-transfer-actions>
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-row-toggle>View lines</button>
            ${reviewButton}
            ${postureButton}
          </div>
        </div>
        <div class="warehouse-transfer-row-facts warehouse-visual-row-facts" data-warehouse-transfer-row-facts>
          <div class="warehouse-transfer-row-fact" data-warehouse-transfer-row-fact="source"><span>Source</span><strong>${escapeHtml(row.source_warehouse || "Not visible")}</strong></div>
          <div class="warehouse-transfer-row-fact" data-warehouse-transfer-row-fact="target"><span>Target</span><strong>${escapeHtml(row.target_warehouse || "Not visible")}</strong></div>
          <div class="warehouse-transfer-row-fact" data-warehouse-transfer-row-fact="quantity"><span>Quantity</span><strong>${escapeHtml(row.quantity_summary || "Not visible")}</strong></div>
          <div class="warehouse-transfer-row-fact" data-warehouse-transfer-row-fact="state"><span>Review state</span><strong>${escapeHtml(row.posture || row.group_label || "Transfer posture")}</strong></div>
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
        <div class="warehouse-console-card-grid warehouse-visual-row-list">
          ${rows.length ? rows.map(renderTransferRow).join("") : `<div class="warehouse-stock-exception-row warehouse-visual-fallback" data-warehouse-transfer-empty><span class="warehouse-inbound-meta">${escapeHtml(transferGroupEmptyText(group))}</span></div>`}
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
    const rows = Array.isArray(payload.rows) ? payload.rows : [];
    const statePayload = payload.state || {};
    const isLoadingState = String(statePayload.kind || "") === "loading";
    const unavailable = ["restricted", "error", "unavailable"].includes(String(statePayload.kind || ""));
    const safeCards = transferFallbackCards(cards, statePayload, rows);
    const loadingCards = [
      { key: "loading_needs_review", label: "Needs Review", value: "--", note: "Checking transfer posture." },
      { key: "loading_direct", label: "Direct Transfers", value: "--", note: "Checking source and target warehouses." },
      { key: "loading_recent", label: "Recently Posted", value: "--", note: "Checking submitted transfer records." },
      { key: "loading_quantity", label: "Transfer Quantity", value: "--", note: "Checking quantity summary." },
    ];
    const visibleCards = cards.length ? safeCards : (isLoadingState ? loadingCards : safeCards);
    const loadingControls = `
      <div class="warehouse-inbound-loading-field"><span>Transfer</span><i></i></div>
      <div class="warehouse-inbound-loading-field"><span>Warehouse</span><i></i></div>
      <div class="warehouse-inbound-loading-field"><span>Transfer State</span><i></i></div>
      <button type="button" class="warehouse-inbound-queue-button" disabled>Apply</button>
      <button type="button" class="warehouse-inbound-queue-button" disabled>Reset</button>
      <button type="button" class="warehouse-inbound-queue-button" disabled>Refresh</button>
      <div class="warehouse-inbound-loading-status">Checking transfer visibility...</div>
    `;
    const $root = $(`
      <div class="sales-console-shell warehouse-inbound-shell warehouse-transfer-shell warehouse-transfer-premium-shell warehouse-visual-foundation" data-erpw-workspace="warehouse" data-warehouse-view="transfer-visibility" data-warehouse-queue-key="${TRANSFER_VISIBILITY_KEY}" data-warehouse-transfer-shell="true" data-warehouse-transfer-state="${escapeHtml(statePayload.kind || "ready")}" data-warehouse-visual-foundation="w13-transfer-premium" data-erpw-console-runtime="ready">
        <section class="warehouse-inbound-queue-header warehouse-transfer-command-header warehouse-visual-command" data-warehouse-transfer-command>
          <div class="warehouse-inbound-queue-head">
            <div class="warehouse-transfer-command">
              <h1 class="warehouse-inbound-queue-title">${escapeHtml(payload.summary && payload.summary.title || "Transfer Visibility")}</h1>
              <div class="warehouse-inbound-queue-note">${escapeHtml(payload.summary && payload.summary.subtitle || "Read-only warehouse-to-warehouse transfer posture.")}</div>
            </div>
          </div>
          <div class="warehouse-inbound-queue-cards warehouse-visual-summary-grid ${isLoadingState ? "is-loading" : ""}">${visibleCards.map(renderTransferCard).join("")}</div>
          <div class="warehouse-inbound-controls warehouse-visual-filter-strip ${isLoadingState ? "is-loading" : ""}">
            ${isLoadingState ? loadingControls : `
              ${fields.map(controlField).join("")}
              <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-apply>Apply</button>
              <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-reset>Reset</button>
              <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-refresh>Refresh</button>
            `}
          </div>
        </section>
        <div class="warehouse-inbound-groups">
          ${unavailable
            ? `<section class="warehouse-inbound-group warehouse-visual-fallback" data-warehouse-transfer-group="state"><h2 class="warehouse-inbound-group-title">${escapeHtml(statePayload.title || "Transfer visibility unavailable")}</h2><div class="warehouse-inbound-meta" data-warehouse-transfer-empty>${escapeHtml(statePayload.detail || "Transfer visibility could not be loaded. Refresh or contact an administrator.")}</div></section>`
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
    replaceWarehouseRouteHost(viewState, $root);
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
    const state = {
      page,
      $host,
      purchaseOrder: "",
      requestSerial: 0,
      loadingSignature: "",
      loadingPromise: null,
      loadedSignature: "",
      lastPayload: null,
    };
    wrapper.__erpwWarehouseReceivingReview = state;
    return state;
  }

  function receivingSummaryText(header) {
    const parts = [header.purchase_order, "Read-only receiving posture"].filter(Boolean);
    return parts.join(" · ");
  }

  function receivingNumber(value) {
    const match = String(value == null ? "" : value).replace(/,/g, "").match(/-?\d+(?:\.\d+)?/);
    return match ? Number(match[0]) : 0;
  }

  function receivingLinePosture(line) {
    const status = String(line && line.status ? line.status : "").toLowerCase();
    const warehouse = String(line && line.target_warehouse ? line.target_warehouse : "").toLowerCase();
    const remaining = receivingNumber(line && line.remaining_qty);
    const received = receivingNumber(line && line.received_qty);
    if (!line || !line.item_code) {
      return { key: "unavailable", tone: "unavailable", label: "Unavailable", note: "Line details are not visible for this order." };
    }
    if (remaining <= 0 || status.includes("arrived")) {
      return { key: "received", tone: "received", label: "Already Received", note: "No open quantity is visible on this line." };
    }
    if (!warehouse || warehouse.includes("not set") || warehouse.includes("missing")) {
      return { key: "blocked", tone: "blocked", label: "Needs Review", note: "Target warehouse is not clear." };
    }
    if (status.includes("overdue")) {
      return { key: "blocked", tone: "blocked", label: "Needs Review", note: "Past the expected date." };
    }
    if (received > 0) {
      return { key: "ready", tone: "ready", label: "Partially Open", note: "Some quantity has already arrived." };
    }
    return { key: "ready", tone: "ready", label: "Open For Review", note: "Open quantity is visible for warehouse review." };
  }

  function receivingReadinessSummary(lines, unavailable) {
    const counts = { ready: 0, blocked: 0, received: 0, unavailable: unavailable ? 1 : 0 };
    (Array.isArray(lines) ? lines : []).forEach((line) => {
      const posture = receivingLinePosture(line);
      if (posture.key === "ready") counts.ready += 1;
      else if (posture.key === "blocked") counts.blocked += 1;
      else if (posture.key === "received") counts.received += 1;
      else counts.unavailable += 1;
    });
    if (!unavailable && (!lines || !lines.length)) counts.unavailable += 1;
    return [
      { key: "ready", label: "Ready Later", value: counts.ready, note: "Open lines with clear warehouse posture." },
      { key: "blocked", label: "Needs Review", value: counts.blocked, note: "Overdue, missing, or unclear posture." },
      { key: "received", label: "Already Received", value: counts.received, note: "Lines with no open quantity visible." },
      { key: "unavailable", label: "Unavailable", value: counts.unavailable, note: "Details hidden or not available." },
    ];
  }

  function renderReceivingReadinessCard(card) {
    return `
      <div class="warehouse-receiving-readiness-card warehouse-visual-summary-card is-${escapeHtml(card.key || "")}" data-warehouse-receiving-readiness-card="${escapeHtml(card.key || "")}">
        <div class="warehouse-receiving-card-label">${escapeHtml(card.label || "")}</div>
        <div class="warehouse-receiving-card-value">${escapeHtml(card.value == null ? "0" : card.value)}</div>
        <div class="warehouse-receiving-card-note">${escapeHtml(card.note || "")}</div>
      </div>
    `;
  }

  function renderReceivingCard(card) {
    return `
      <div class="warehouse-receiving-card warehouse-visual-summary-card" data-warehouse-receiving-card="${escapeHtml(card.key || "")}">
        <div class="warehouse-receiving-card-label">${escapeHtml(card.label || "")}</div>
        <div class="warehouse-receiving-card-value">${escapeHtml(card.value == null ? "--" : card.value)}</div>
        <div class="warehouse-receiving-card-note">${escapeHtml(card.note || "")}</div>
      </div>
    `;
  }

  function receivingLineStatusDetail(line, posture) {
    const status = String(line && line.status ? line.status : "").trim();
    const fallback = String(posture && posture.note ? posture.note : "").trim();
    const label = String(posture && posture.label ? posture.label : "").trim();
    const detail = status || fallback;
    if (!detail) return "";
    const normalizedDetail = detail.toLowerCase();
    const normalizedLabel = label.toLowerCase();
    if (normalizedDetail === normalizedLabel) return "";
    if (posture && posture.key === "received" && /arriv|receiv/.test(normalizedDetail)) return "";
    return detail;
  }

  function normalizedReceivingDate(value) {
    return String(value == null ? "" : value).trim();
  }

  function receivingLineExpectedFact(line, headerExpectedDate) {
    const lineDate = normalizedReceivingDate(line && line.required_date);
    const headerDate = normalizedReceivingDate(headerExpectedDate);
    if (!lineDate || (headerDate && lineDate === headerDate)) return "";
    return `<div class="warehouse-receiving-line-fact warehouse-visual-fact"><span>Line expected</span><strong>${escapeHtml(lineDate)}</strong></div>`;
  }

  function renderReceivingLine(line, headerExpectedDate) {
    const posture = receivingLinePosture(line || {});
    const statusDetail = receivingLineStatusDetail(line || {}, posture);
    const uom = line.uom || "";
    const expectedFact = receivingLineExpectedFact(line || {}, headerExpectedDate);
    return `
      <div class="warehouse-receiving-line warehouse-visual-row-card is-${escapeHtml(posture.tone)}" data-warehouse-receiving-line="${escapeHtml(line.item_code || "")}">
        <div class="warehouse-receiving-line-main warehouse-visual-row-header">
          <div class="warehouse-receiving-line-identity">
            <div class="warehouse-receiving-strong">${escapeHtml(line.item_code || "Item not visible")}</div>
            <div class="warehouse-receiving-meta">${escapeHtml(line.item_name || "No item description visible")}</div>
          </div>
          <div class="warehouse-receiving-line-status warehouse-visual-chip is-${escapeHtml(posture.tone)}" data-warehouse-receiving-line-status="${escapeHtml(posture.key)}">
            <span>${escapeHtml(posture.label)}</span>
            ${statusDetail ? `<strong>${escapeHtml(statusDetail)}</strong>` : ""}
          </div>
        </div>
        <div class="warehouse-receiving-line-facts warehouse-visual-row-facts">
          <div class="warehouse-receiving-line-fact warehouse-visual-fact"><span>Ordered</span><strong>${escapeHtml(line.ordered_qty || "0")} ${escapeHtml(uom)}</strong></div>
          <div class="warehouse-receiving-line-fact warehouse-visual-fact"><span>Already arrived</span><strong>${escapeHtml(line.received_qty || "0")} ${escapeHtml(uom)}</strong></div>
          <div class="warehouse-receiving-line-fact warehouse-visual-fact"><span>Still open</span><strong>${escapeHtml(line.remaining_qty || "0")} ${escapeHtml(uom)}</strong></div>
          <div class="warehouse-receiving-line-fact warehouse-visual-fact"><span>Warehouse</span><strong>${escapeHtml(line.target_warehouse || "Not visible")}</strong></div>
          ${expectedFact}
        </div>
      </div>
    `;
  }

  function renderReceivingHistoryRow(row) {
    return `
      <div class="warehouse-receiving-history-row warehouse-visual-row-card" data-warehouse-receiving-history-row="${escapeHtml(row.receipt_id || "")}">
        <div>
          <div class="warehouse-receiving-strong">${escapeHtml(row.receipt_id || "Receipt not visible")}</div>
          <div class="warehouse-receiving-meta">${escapeHtml(row.posting_date || "Posting date not visible")}</div>
        </div>
        <div class="warehouse-receiving-history-pill warehouse-visual-chip">${escapeHtml(row.status || "Recorded")}</div>
        <div class="warehouse-receiving-meta">${escapeHtml(row.item_count == null ? "0" : row.item_count)} items</div>
        <div class="warehouse-receiving-meta">${escapeHtml(row.quantity_summary || "Recorded quantity")}</div>
      </div>
    `;
  }

  function renderReceivingWorkflowStatusStrip() {
    const statuses = [
      "Not Started",
      "In Progress",
      "Submitted For Review",
      "Manager Review",
      "Procurement Escalation",
      "Draft Prepared",
    ];
    return `
      <div class="warehouse-receiving-workflow-status" data-warehouse-receiving-workflow-status-strip>
        ${statuses.map((status) => `<div class="warehouse-receiving-workflow-status-step" data-warehouse-receiving-workflow-status="${escapeHtml(status)}">${escapeHtml(status)}</div>`).join("")}
      </div>
    `;
  }

  function renderReceivingPlannedControl(key, title, note) {
    return `
      <div class="warehouse-receiving-planned-control" aria-disabled="true" data-warehouse-receiving-workflow-control="${escapeHtml(key)}">
        <strong>${escapeHtml(title)}</strong>
        <span>${escapeHtml(note || "Planned control, not active yet.")}</span>
      </div>
    `;
  }

  function renderReceivingCountField(label, value) {
    return `
      <div class="warehouse-receiving-count-field">
        <span>${escapeHtml(label)}</span>
        <strong>${escapeHtml(value == null || value === "" ? "--" : value)}</strong>
      </div>
    `;
  }

  function renderReceivingCountEvidenceRow(line) {
    const uom = line && line.uom ? ` ${line.uom}` : "";
    const expected = line && (line.remaining_qty || line.ordered_qty) ? `${line.remaining_qty || line.ordered_qty}${uom}` : "--";
    return `
      <div class="warehouse-receiving-count-row" data-warehouse-receiving-count-row="${escapeHtml(line && line.item_code || "")}">
        <div class="warehouse-receiving-count-row-title">${escapeHtml(line && line.item_code || "Item not visible")}</div>
        <div class="warehouse-receiving-meta">${escapeHtml(line && line.item_name || "Count evidence model preview")}</div>
        <div class="warehouse-receiving-count-fields">
          ${renderReceivingCountField("Expected", expected)}
          ${renderReceivingCountField("Counted", "Not active")}
          ${renderReceivingCountField("Accepted", "Not active")}
          ${renderReceivingCountField("Damaged", "Not active")}
          ${renderReceivingCountField("Short", "Not active")}
          ${renderReceivingCountField("Over", "Not active")}
          ${renderReceivingCountField("Quarantine", "Not active")}
        </div>
      </div>
    `;
  }

  function renderReceivingDiscrepancyCard(key, title, note) {
    return `
      <div class="warehouse-receiving-discrepancy-card" data-warehouse-receiving-discrepancy-category="${escapeHtml(key)}">
        <strong>${escapeHtml(title)}</strong>
        <span>${escapeHtml(note)}</span>
      </div>
    `;
  }

  function renderReceivingManagerDecision(key, title, note) {
    return `
      <div class="warehouse-receiving-manager-card" aria-disabled="true" data-warehouse-receiving-manager-decision="${escapeHtml(key)}">
        <strong>${escapeHtml(title)}</strong>
        <span>${escapeHtml(note)}</span>
      </div>
    `;
  }

  function renderReceivingWorkflowShell(header, lines, statePayload) {
    const visibleLines = Array.isArray(lines) ? lines.filter((line) => line && line.item_code).slice(0, 4) : [];
    const moreLines = Array.isArray(lines) && lines.length > visibleLines.length ? lines.length - visibleLines.length : 0;
    const unavailable = ["restricted", "error", "unavailable"].includes(String(statePayload && statePayload.kind || ""));
    const countRows = visibleLines.length
      ? visibleLines.map(renderReceivingCountEvidenceRow).join("")
      : `<div class="warehouse-receiving-count-row warehouse-visual-fallback" data-warehouse-receiving-workflow-empty><div class="warehouse-receiving-count-row-title">No count preview visible</div><div class="warehouse-receiving-meta">${escapeHtml(unavailable ? "Receiving task evidence is not available for this order." : "Item lines will appear here when receiving evidence is enabled.")}</div></div>`;
    return `
      <section class="warehouse-receiving-workflow-shell" data-warehouse-receiving-workflow-shell data-warehouse-w15c2-shell="true">
        <div class="warehouse-receiving-workflow-head">
          <div>
            <h2 class="warehouse-receiving-workflow-title">Receiving workflow</h2>
            <div class="warehouse-receiving-workflow-subtitle">Controlled future workflow shell for arrival checks, count evidence, manager review, and Procurement escalation. This preview is display-only.</div>
          </div>
          <span class="warehouse-receiving-workflow-badge" data-warehouse-receiving-workflow-state>Shell only</span>
        </div>
        <div class="warehouse-receiving-workflow-guardrail" data-warehouse-receiving-workflow-guardrail>
          <strong>No stock is posted.</strong>
          <span>No Purchase Receipt is created or submitted from this shell. Draft preparation comes later through an approved workflow and remains unsubmitted.</span>
        </div>
        ${renderReceivingWorkflowStatusStrip()}
        <div class="warehouse-receiving-workflow-grid">
          <section class="warehouse-receiving-workflow-card" data-warehouse-receiving-user-work-panel>
            <div>
              <div class="warehouse-receiving-workflow-card-title">Warehouse User Work Panel</div>
              <div class="warehouse-receiving-workflow-card-note">Planned controls are visible for workflow shape only. They are inactive and do not change stock or receiving records.</div>
            </div>
            <div class="warehouse-receiving-planned-actions">
              ${renderReceivingPlannedControl("start_arrival_check", "Start arrival check", "Planned action for confirming goods physically arrived.")}
              ${renderReceivingPlannedControl("save_count_draft", "Save count draft", "Planned action for storing count evidence after workflow approval.")}
              ${renderReceivingPlannedControl("submit_for_review", "Send to manager review", "Planned handoff for manager review, not active now.")}
            </div>
          </section>
          <section class="warehouse-receiving-workflow-card" data-warehouse-receiving-discrepancy-panel>
            <div>
              <div class="warehouse-receiving-workflow-card-title">Discrepancy categories</div>
              <div class="warehouse-receiving-workflow-card-note">Future evidence-required categories for manager review and Procurement escalation.</div>
            </div>
            <div class="warehouse-receiving-discrepancy-grid">
              ${renderReceivingDiscrepancyCard("short", "Short", "Evidence required when received quantity is below expected quantity.")}
              ${renderReceivingDiscrepancyCard("over", "Over", "Procurement owns over-receipt policy and supplier follow-up.")}
              ${renderReceivingDiscrepancyCard("damaged", "Damaged", "Evidence required before quarantine or supplier claim.")}
              ${renderReceivingDiscrepancyCard("wrong_item", "Wrong item", "Procurement escalation required; do not accept as normal stock.")}
              ${renderReceivingDiscrepancyCard("quarantine", "Quarantine", "Hold posture for damaged, wrong, or unresolved goods.")}
              ${renderReceivingDiscrepancyCard("supplier_paperwork_mismatch", "Supplier paperwork mismatch", "Evidence required before Procurement follow-up.")}
              ${renderReceivingDiscrepancyCard("procurement_escalation", "Procurement escalation", "For PO correction, supplier dispute, or commercial decision.")}
            </div>
          </section>
        </div>
        <section class="warehouse-receiving-workflow-card" data-warehouse-receiving-count-evidence-preview>
          <div>
            <div class="warehouse-receiving-workflow-card-title">Count Evidence Preview</div>
            <div class="warehouse-receiving-workflow-card-note">Future count model based on visible receiving lines for ${escapeHtml(header && header.purchase_order || "this order")}. Values are display-only placeholders.${moreLines ? ` Showing first ${visibleLines.length} lines; ${moreLines} more remain in Item Lines.` : ""}</div>
          </div>
          <div class="warehouse-receiving-count-grid">${countRows}</div>
        </section>
        <div class="warehouse-receiving-workflow-grid">
          <section class="warehouse-receiving-workflow-card" data-warehouse-receiving-manager-preview>
            <div>
              <div class="warehouse-receiving-workflow-card-title">Manager Decision Preview</div>
              <div class="warehouse-receiving-workflow-card-note">Planned Warehouse Manager decisions are shown as non-active review cards.</div>
            </div>
            <div class="warehouse-receiving-manager-grid">
              ${renderReceivingManagerDecision("request_recount", "Request recount", "Ask Warehouse User to verify unclear counts.")}
              ${renderReceivingManagerDecision("approve_clean_receipt", "Approve clean receipt", "For counts that match visible PO receiving posture.")}
              ${renderReceivingManagerDecision("approve_shortage_within_tolerance", "Approve shortage within tolerance", "Allowed only after owner-approved tolerance policy.")}
              ${renderReceivingManagerDecision("mark_quarantine_review", "Mark quarantine review", "For damaged, wrong, or held goods.")}
              ${renderReceivingManagerDecision("escalate_to_procurement", "Escalate to Procurement", "Required for overage, wrong item, supplier return, PO correction, or supplier dispute.")}
            </div>
          </section>
          <section class="warehouse-receiving-workflow-card" data-warehouse-receiving-draft-policy>
            <div>
              <div class="warehouse-receiving-workflow-card-title">Draft Policy Preview</div>
              <div class="warehouse-receiving-workflow-card-note">Purchase Receipt draft preparation comes later, remains unsubmitted, and requires Procurement/Admin document review after approval.</div>
            </div>
            <div class="warehouse-receiving-discrepancy-grid">
              ${renderReceivingDiscrepancyCard("draft_later_only", "Draft comes later", "No draft is prepared from this preview.")}
              ${renderReceivingDiscrepancyCard("draft_unsubmitted", "Draft remains unsubmitted", "Stock posting stays outside this shell.")}
              ${renderReceivingDiscrepancyCard("document_owner_review", "Document owner review", "Procurement/Admin reviews the draft handoff after preparation.")}
              ${renderReceivingDiscrepancyCard("exclude_unresolved", "Exclude unresolved issues", "Damaged, wrong, quarantine, or unresolved overage must not become normal accepted draft lines.")}
            </div>
          </section>
        </div>
      </section>
    `;
  }

  function activateReceivingTab($root, tabKey) {
    const key = tabKey || "item_lines";
    $root.find("[data-warehouse-receiving-tab]").each(function () {
      const isActive = String(this.getAttribute("data-warehouse-receiving-tab")) === key;
      $(this).toggleClass("is-active", isActive).attr("aria-selected", isActive ? "true" : "false");
    });
    $root.find("[data-warehouse-receiving-panel]").each(function () {
      const isActive = String(this.getAttribute("data-warehouse-receiving-panel")) === key;
      $(this).toggleClass("is-active", isActive).attr("hidden", isActive ? null : "hidden");
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
    const readinessCards = receivingReadinessSummary(lines, unavailable);
    const shellOrder = header.purchase_order || viewState.purchaseOrder || "";
    const $root = $(`
      <div class="sales-console-shell warehouse-receiving-shell warehouse-visual-foundation" data-erpw-workspace="warehouse" data-warehouse-view="receiving-review" data-erpw-console-runtime="ready" data-warehouse-receiving-order="${escapeHtml(shellOrder)}" data-warehouse-visual-foundation="w13c2">
        <section class="warehouse-receiving-header warehouse-visual-command">
          <div class="warehouse-receiving-head">
            <div class="warehouse-receiving-command warehouse-visual-command-title">
              <div class="warehouse-receiving-eyebrow">Read-only receiving posture</div>
              <h1 class="warehouse-receiving-title">Receiving Review</h1>
              <div class="warehouse-receiving-subtitle">${escapeHtml(unavailable ? statePayload.detail || "Receiving work could not be loaded. Refresh or contact an administrator." : receivingSummaryText(header))}</div>
              <div class="warehouse-receiving-chip-row warehouse-visual-chip-row">
                <span class="warehouse-receiving-chip warehouse-visual-chip">${escapeHtml(shellOrder || "Order not visible")}</span>
                <span class="warehouse-receiving-chip warehouse-visual-chip">${escapeHtml(header.status || statePayload.title || "Review")}</span>
                <span class="warehouse-receiving-chip warehouse-visual-chip is-read-only">Read-only</span>
              </div>
            </div>
            <div class="warehouse-receiving-actions warehouse-visual-action-strip">
              <button type="button" class="warehouse-receiving-button" data-warehouse-receiving-back>Back to inbound receiving</button>
              <button type="button" class="warehouse-receiving-button" data-warehouse-receiving-refresh>Refresh</button>
            </div>
          </div>
          ${unavailable ? `<div class="warehouse-receiving-state-panel warehouse-visual-fallback" data-warehouse-receiving-empty><strong>${escapeHtml(statePayload.title || "Receiving review unavailable")}</strong><span>${escapeHtml(statePayload.detail || "Receiving work could not be loaded. Refresh or contact an administrator.")}</span></div>` : `
            <div class="warehouse-receiving-command-grid warehouse-visual-fact-strip">
              <div class="warehouse-receiving-command-fact warehouse-visual-fact"><span>Supplier</span><strong>${escapeHtml(header.supplier || "Not visible")}</strong></div>
              <div class="warehouse-receiving-command-fact warehouse-visual-fact"><span>Target warehouse</span><strong>${escapeHtml(header.target_warehouse || "Not visible")}</strong></div>
              <div class="warehouse-receiving-command-fact warehouse-visual-fact"><span>Expected</span><strong>${escapeHtml(header.required_date || "Not visible")}</strong></div>
              <div class="warehouse-receiving-command-fact warehouse-visual-fact"><span>Receiving state</span><strong>${escapeHtml(header.state_label || "Review")}</strong></div>
            </div>
            <section class="warehouse-receiving-posture-panel" data-warehouse-receiving-posture-panel>
              <div class="warehouse-receiving-posture-head">
                <div>
                  <h2 class="warehouse-receiving-posture-title">Receiving posture</h2>
                  <div class="warehouse-receiving-posture-note">${escapeHtml(header.age_label || "Receiving posture visible")} · ${escapeHtml(header.remaining_summary || "No open quantity summary visible")}</div>
                </div>
              </div>
              <div class="warehouse-receiving-posture-layout">
                <div class="warehouse-receiving-posture-block">
                  <div class="warehouse-receiving-posture-kicker">Line readiness</div>
                  <div class="warehouse-receiving-readiness warehouse-visual-summary-grid" data-warehouse-receiving-readiness>
                    ${readinessCards.map(renderReceivingReadinessCard).join("")}
                  </div>
                </div>
                <div class="warehouse-receiving-posture-block">
                  <div class="warehouse-receiving-posture-kicker">Receipt posture</div>
                  <div class="warehouse-receiving-cards warehouse-visual-summary-grid">${cards.map(renderReceivingCard).join("")}</div>
                </div>
              </div>
            </section>
          `}
        </section>
        <section class="warehouse-receiving-guardrail warehouse-visual-guardrail" data-warehouse-receiving-guardrail>
          <strong>Review only</strong>
          <span>No stock is posted and no Purchase Receipt is created from this screen. Use this page to understand receiving posture before any separate receiving process.</span>
        </section>
        ${renderReceivingWorkflowShell(header, lines, statePayload)}
        <section class="warehouse-receiving-detail">
          <div class="warehouse-receiving-detail-head">
            <div>
              <h2 class="warehouse-receiving-section-title">Receiving Lines</h2>
              <div class="warehouse-receiving-meta">Open quantity, arrived quantity, target warehouse, and expected date are shown for review only.</div>
            </div>
            <div class="warehouse-receiving-tabs warehouse-visual-tab-strip">
              ${tabs.map((tab) => `<button type="button" class="warehouse-receiving-tab warehouse-visual-tab" data-warehouse-receiving-tab="${escapeHtml(tab.key || "")}">${escapeHtml(tab.label || "")} ${escapeHtml(tab.count == null ? "" : `(${tab.count})`)}</button>`).join("")}
            </div>
          </div>
          <div class="warehouse-receiving-panel warehouse-visual-row-list is-active" data-warehouse-receiving-panel="item_lines">
            ${lines.length ? lines.map((line) => renderReceivingLine(line, header.required_date)).join("") : `<div class="warehouse-receiving-line warehouse-visual-fallback" data-warehouse-receiving-empty><span class="warehouse-receiving-meta">No item lines are visible for this order.</span></div>`}
          </div>
          <div class="warehouse-receiving-panel warehouse-visual-row-list" data-warehouse-receiving-panel="receipt_history">
            <div class="warehouse-receiving-history-note">Prior receipt records visible to your role are shown as bounded history. This panel does not open native receipt pages.</div>
            ${history.length ? history.map(renderReceivingHistoryRow).join("") : `<div class="warehouse-receiving-history-row warehouse-visual-fallback" data-warehouse-receiving-empty><span class="warehouse-receiving-meta">No receipt history is visible for this order.</span></div>`}
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
      loadReceivingReview(viewState, viewState.purchaseOrder, { force: true });
    });
    $root.find("[data-warehouse-receiving-tab]").on("click", function (event) {
      event.preventDefault();
      activateReceivingTab($root, String(this.getAttribute("data-warehouse-receiving-tab") || "item_lines"));
    });
    activateReceivingTab($root, "item_lines");
    replaceWarehouseRouteHost(viewState, $root);
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

  function loadReceivingReview(viewState, purchaseOrder, options) {
    const order = String(purchaseOrder || receivingPurchaseOrderFromRoute() || "").trim();
    const force = Boolean(options && options.force);
    const signature = receivingLoadSignature(order);
    if (!force && viewState.loadingPromise && viewState.loadingSignature === signature) {
      markWarehouseDiagnostic("receivingDuplicateLoadReused");
      return viewState.loadingPromise;
    }
    if (!force && viewState.loadedSignature === signature && hasRenderedReceivingShell(viewState, order)) {
      markWarehouseDiagnostic("receivingDuplicateRenderSkipped");
      return Promise.resolve(viewState.lastPayload || {});
    }

    markWarehouseDiagnostic("receivingServiceCallAttempted");
    viewState.purchaseOrder = order;
    const requestToken = (viewState.requestSerial || 0) + 1;
    viewState.requestSerial = requestToken;
    viewState.loadingSignature = signature;
    viewState.loadedSignature = "";
    renderReceivingLoading(viewState);

    const finishRequest = (payload) => {
      const currentOrder = receivingPurchaseOrderFromRoute();
      const shouldRender = (
        viewState.requestSerial === requestToken
        && viewState.loadingSignature === signature
        && isActiveReceivingRoute()
        && String(currentOrder || "").trim() === order
      );
      if (viewState.requestSerial === requestToken && viewState.loadingSignature === signature) {
        viewState.loadingPromise = null;
        viewState.loadingSignature = "";
      }
      if (!shouldRender) {
        markWarehouseDiagnostic("receivingStaleResponseIgnored");
        return payload;
      }
      viewState.loadedSignature = signature;
      viewState.lastPayload = payload;
      renderReceivingReviewPayload(viewState, payload);
      return payload;
    };

    const requestPromise = frappe.call({
      method: RECEIVING_METHOD,
      args: { purchase_order: viewState.purchaseOrder },
    }).then((response) => finishRequest(response && response.message ? response.message : {})).catch(() => finishRequest({
      state: { kind: "error", title: "Receiving review unavailable", detail: "Receiving work could not be loaded. Refresh or contact an administrator." },
      header: { purchase_order: viewState.purchaseOrder || "" },
      summary_cards: [],
      tabs: [
        { key: "item_lines", label: "Item Lines", count: 0 },
        { key: "receipt_history", label: "Receipt History", count: 0 },
      ],
      lines: [],
      receipt_history: [],
    }));
    viewState.loadingPromise = requestPromise;
    return requestPromise;
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
    const state = {
      page,
      $host,
      salesOrder: "",
      requestSerial: 0,
      loadingSignature: "",
      loadingPromise: null,
      loadedSignature: "",
      lastPayload: null,
    };
    wrapper.__erpwWarehousePickingReview = state;
    return state;
  }

  function pickingLoadSignature(salesOrder) {
    return `${pickingRouteSignature()}::${String(salesOrder || "").trim()}`;
  }

  function hasRenderedPickingShell(viewState, salesOrder) {
    const host = viewState && viewState.$host && viewState.$host.get ? viewState.$host.get(0) : null;
    if (!host || !document.documentElement.contains(host)) return false;
    const shell = host.querySelector('.warehouse-picking-shell[data-warehouse-view="picking-review"]');
    if (!shell) return false;
    return String(shell.getAttribute("data-warehouse-picking-order") || "") === String(salesOrder || "").trim();
  }

  function pickingSummaryText(header) {
    const parts = [header.sales_order, "Read-only picking posture"].filter(Boolean);
    return parts.join(" · ");
  }

  function pickingLinePosture(line) {
    const readiness = String(line.readiness || "").toLowerCase();
    const availability = String(line.availability || "").toLowerCase();
    if (readiness.includes("need") || readiness.includes("short") || availability.includes("short")) {
      return { key: "needs_review", tone: "blocked", label: "Needs Review", note: "Stock posture needs review" };
    }
    if (readiness.includes("ready") || availability.includes("available")) {
      return { key: "ready", tone: "ready", label: "Ready", note: "Available posture visible" };
    }
    if (readiness || availability) {
      return { key: "review", tone: "review", label: "Review", note: "Posture visible" };
    }
    return { key: "unavailable", tone: "unavailable", label: "Unavailable", note: "Stock posture not visible" };
  }

  function pickingReadinessSummary(lines, unavailable) {
    if (unavailable) {
      return [
        { key: "ready", label: "Ready Lines", value: "--", note: "Unavailable", tone: "unavailable" },
        { key: "review", label: "Needs Review", value: "--", note: "Unavailable", tone: "unavailable" },
        { key: "open", label: "Open Lines", value: "--", note: "Unavailable", tone: "unavailable" },
        { key: "availability", label: "Availability", value: "--", note: "Unavailable", tone: "unavailable" },
      ];
    }
    const total = lines.length;
    const ready = lines.filter((line) => pickingLinePosture(line).tone === "ready").length;
    const review = lines.filter((line) => pickingLinePosture(line).tone === "blocked").length;
    const visible = lines.filter((line) => String(line.availability || "").trim()).length;
    return [
      { key: "ready", label: "Ready Lines", value: ready, note: "Visible as ready for review", tone: "ready" },
      { key: "review", label: "Needs Review", value: review, note: "Line posture needs attention", tone: review ? "blocked" : "ready" },
      { key: "open", label: "Open Lines", value: total, note: "Lines still visible for review", tone: total ? "review" : "unavailable" },
      { key: "availability", label: "Availability", value: visible, note: "Lines with available posture", tone: visible ? "ready" : "unavailable" },
    ];
  }

  function pickingLineStatusDetail(line, posture) {
    const readiness = String(line && line.readiness ? line.readiness : "").trim();
    const label = String(posture && posture.label ? posture.label : "").trim();
    const fallback = String(posture && posture.note ? posture.note : "").trim();
    if (!readiness) return fallback;
    if (readiness.toLowerCase() === label.toLowerCase()) return "";
    return readiness;
  }

  function renderPickingReadinessCard(card) {
    return `
      <div class="warehouse-receiving-readiness-card warehouse-visual-summary-card is-${escapeHtml(card.tone || "review")}" data-warehouse-picking-readiness-card="${escapeHtml(card.key || "")}">
        <div class="warehouse-receiving-card-label">${escapeHtml(card.label || "")}</div>
        <div class="warehouse-receiving-card-value">${escapeHtml(card.value == null ? "--" : card.value)}</div>
        <div class="warehouse-receiving-card-note">${escapeHtml(card.note || "")}</div>
      </div>
    `;
  }

  function renderPickingCard(card) {
    return `
      <div class="warehouse-receiving-card warehouse-visual-summary-card" data-warehouse-picking-card="${escapeHtml(card.key || "")}">
        <div class="warehouse-receiving-card-label">${escapeHtml(card.label || "")}</div>
        <div class="warehouse-receiving-card-value">${escapeHtml(card.value == null ? "--" : card.value)}</div>
        <div class="warehouse-receiving-card-note">${escapeHtml(card.note || "")}</div>
      </div>
    `;
  }

  function renderPickingLine(line) {
    const posture = pickingLinePosture(line);
    const statusDetail = pickingLineStatusDetail(line, posture);
    const uom = line.uom || line.stock_uom || "";
    return `
      <div class="warehouse-receiving-line warehouse-picking-line warehouse-visual-row-card is-${escapeHtml(posture.tone)}" data-warehouse-picking-line="${escapeHtml(line.item_code || "")}" data-warehouse-picking-line-card>
        <div class="warehouse-receiving-line-main warehouse-visual-row-header">
          <div>
            <div class="warehouse-receiving-strong">${escapeHtml(line.item_code || "Item not visible")}</div>
            <div class="warehouse-receiving-meta">${escapeHtml(line.item_name || "Item name not visible")}</div>
          </div>
          <div class="warehouse-receiving-line-status warehouse-visual-chip is-${escapeHtml(posture.tone)}" data-warehouse-picking-line-status="${escapeHtml(posture.key)}">
            <span>${escapeHtml(posture.label)}</span>
            ${statusDetail ? `<strong>${escapeHtml(statusDetail)}</strong>` : ""}
          </div>
        </div>
        <div class="warehouse-receiving-line-facts warehouse-picking-line-facts warehouse-visual-row-facts">
          <div class="warehouse-receiving-line-fact warehouse-visual-fact" data-warehouse-picking-line-fact="ordered"><span>Ordered</span><strong>${escapeHtml(line.ordered_qty || "0")} ${escapeHtml(uom)}</strong></div>
          <div class="warehouse-receiving-line-fact warehouse-visual-fact" data-warehouse-picking-line-fact="delivered"><span>Delivered</span><strong>${escapeHtml(line.delivered_qty || "0")} ${escapeHtml(uom)}</strong></div>
          <div class="warehouse-receiving-line-fact warehouse-visual-fact" data-warehouse-picking-line-fact="open"><span>Still open</span><strong>${escapeHtml(line.pending_qty || "0")} ${escapeHtml(uom)}</strong></div>
          <div class="warehouse-receiving-line-fact warehouse-visual-fact" data-warehouse-picking-line-fact="warehouse"><span>Warehouse</span><strong>${escapeHtml(line.source_warehouse || "Not visible")}</strong></div>
          <div class="warehouse-receiving-line-fact warehouse-visual-fact" data-warehouse-picking-line-fact="available"><span>Available posture</span><strong>${escapeHtml(line.availability || "Not visible")}</strong></div>
        </div>
      </div>
    `;
  }

  function renderPickingReadinessRow(line) {
    const posture = pickingLinePosture(line);
    const statusDetail = pickingLineStatusDetail(line, posture);
    const uom = line.uom || line.stock_uom || "";
    return `
      <div class="warehouse-receiving-history-row warehouse-picking-readiness-row warehouse-visual-row-card is-${escapeHtml(posture.tone)}" data-warehouse-picking-readiness-row="${escapeHtml(line.item_code || "")}">
        <div>
          <div class="warehouse-receiving-strong">${escapeHtml(line.item_code || "")}</div>
          <div class="warehouse-receiving-meta">${escapeHtml(line.source_warehouse || "")}</div>
        </div>
        <div class="warehouse-receiving-meta">${escapeHtml(line.pending_qty || "0")} ${escapeHtml(uom)} open</div>
        <div class="warehouse-receiving-meta">${escapeHtml(line.availability || "Availability not visible")}</div>
        <div class="warehouse-receiving-line-status warehouse-visual-chip is-${escapeHtml(posture.tone)}" data-warehouse-picking-readiness-status="${escapeHtml(posture.key)}"><span>${escapeHtml(posture.label)}</span>${statusDetail ? `<strong>${escapeHtml(statusDetail)}</strong>` : ""}</div>
      </div>
    `;
  }

  function renderPickingWorkflowStatusStep(step) {
    return `
      <div class="warehouse-receiving-workflow-status-step" data-warehouse-picking-workflow-status="${escapeHtml(step.key || "")}">
        ${escapeHtml(step.label || "")}
      </div>
    `;
  }

  function renderPickingPlannedControl(control) {
    return `
      <div class="warehouse-receiving-planned-control" data-warehouse-picking-planned-control="${escapeHtml(control.key || "")}" aria-disabled="true">
        <strong>${escapeHtml(control.label || "")}</strong>
        <span>${escapeHtml(control.note || "")}</span>
      </div>
    `;
  }

  function renderPickingWorkflowField(label, value) {
    return `
      <div class="warehouse-receiving-count-field">
        <span>${escapeHtml(label || "")}</span>
        <strong>${escapeHtml(value == null || value === "" ? "Not active" : value)}</strong>
      </div>
    `;
  }

  function renderPickingEvidenceRow(line) {
    const uom = line.uom || line.stock_uom || "";
    const openQty = `${line.pending_qty || "0"} ${uom}`.trim();
    return `
      <div class="warehouse-receiving-count-row" data-warehouse-picking-evidence-row="${escapeHtml(line.item_code || "")}">
        <div class="warehouse-receiving-count-row-title">${escapeHtml(line.item_code || "Item not visible")}</div>
        <div class="warehouse-receiving-meta">${escapeHtml(line.item_name || line.source_warehouse || "Line detail not visible")}</div>
        <div class="warehouse-receiving-count-fields">
          ${renderPickingWorkflowField("Open", openQty)}
          ${renderPickingWorkflowField("Picked", "Not active")}
          ${renderPickingWorkflowField("Packed", "Not active")}
          ${renderPickingWorkflowField("Exception", "Not active")}
        </div>
      </div>
    `;
  }

  function renderPickingWorkflowCard(card, dataAttr) {
    return `
      <div class="warehouse-receiving-discrepancy-card" ${dataAttr}="${escapeHtml(card.key || "")}">
        <strong>${escapeHtml(card.label || "")}</strong>
        <span>${escapeHtml(card.note || "")}</span>
      </div>
    `;
  }

  function renderPickingWorkflowShell(header, lines, statePayload) {
    const statusSteps = [
      { key: "not_started", label: "Not Started" },
      { key: "in_progress", label: "In Progress" },
      { key: "submitted", label: "Sent For Review" },
      { key: "manager_review", label: "Manager Review" },
      { key: "pack_ready", label: "Pack Ready" },
      { key: "dispatch_handoff", label: "Dispatch Handoff" },
    ];
    const plannedControls = [
      { key: "start_pick_check", label: "Start pick check", note: "Planned warehouse user step for confirming physical pick work." },
      { key: "save_pick_draft", label: "Save pick draft", note: "Planned evidence capture for picked, short, damaged, or not-found lines." },
      { key: "send_manager_review", label: "Send to manager review", note: "Planned handoff for manager decision before dispatch readiness." },
    ];
    const exceptions = [
      { key: "shortage", label: "Shortage", note: "Open quantity cannot be fully picked from the visible warehouse posture." },
      { key: "damaged", label: "Damaged", note: "Picked goods need damage evidence before manager review." },
      { key: "not_found", label: "Not found", note: "Expected stock is not found and may need repick or recount." },
      { key: "substitution_blocked", label: "Substitution blocked", note: "Alternative items require Sales and customer approval before use." },
      { key: "partial_fulfillment", label: "Partial fulfillment", note: "Partial dispatch needs manager and Sales-facing decision policy." },
      { key: "sales_escalation", label: "Sales escalation", note: "Customer promise, shortage notification, and order changes remain Sales-owned." },
    ];
    const managerDecisions = [
      { key: "request_repick", label: "Request repick", note: "Ask the warehouse user to recheck or recount the pick." },
      { key: "approve_clean_pick", label: "Approve clean pick", note: "Approve picked lines only when no shortage or damage is present." },
      { key: "approve_partial_pick", label: "Approve partial pick", note: "Approve a partial pick only under the later owner-approved policy." },
      { key: "mark_shortage_review", label: "Mark shortage review", note: "Keep shortage evidence for resolution before any dispatch handoff." },
      { key: "escalate_sales", label: "Escalate to Sales", note: "Send customer-facing changes to Sales ownership." },
      { key: "mark_dispatch_handoff", label: "Mark dispatch handoff", note: "Planned dispatch readiness state after policy approval." },
    ];
    const previewLines = Array.isArray(lines) ? lines.slice(0, 4) : [];
    const stateTitle = statePayload && statePayload.title ? statePayload.title : "";
    return `
      <section class="warehouse-receiving-workflow-shell" data-warehouse-picking-workflow-shell data-warehouse-w15d2-shell="true">
        <div class="warehouse-receiving-workflow-head">
          <div>
            <h2 class="warehouse-receiving-workflow-title">Picking workflow</h2>
            <div class="warehouse-receiving-workflow-subtitle">Future workflow preview for pick evidence, pack readiness, manager review, Sales escalation, and dispatch handoff. This preview is display-only.</div>
          </div>
          <span class="warehouse-receiving-workflow-badge" data-warehouse-picking-workflow-badge>Shell only</span>
        </div>
        <div class="warehouse-receiving-workflow-guardrail" data-warehouse-picking-workflow-policy>
          <strong>No stock effect.</strong>
          <span>No stock is reserved, picked, packed, shipped, delivered, posted, or adjusted from this workflow preview. Delivery Note, Pick List, and Stock Reservation steps require a later approved policy.</span>
        </div>
        <div class="warehouse-receiving-workflow-status" data-warehouse-picking-workflow-status-strip>
          ${statusSteps.map(renderPickingWorkflowStatusStep).join("")}
        </div>
        <div class="warehouse-receiving-workflow-grid">
          <div class="warehouse-receiving-workflow-card" data-warehouse-picking-user-work-panel>
            <div>
              <div class="warehouse-receiving-workflow-card-title">Warehouse user work</div>
              <div class="warehouse-receiving-workflow-card-note">Planned physical pick, count, and exception evidence steps. These controls are not active.</div>
            </div>
            <div class="warehouse-receiving-planned-actions">
              ${plannedControls.map(renderPickingPlannedControl).join("")}
            </div>
          </div>
          <div class="warehouse-receiving-workflow-card" data-warehouse-picking-evidence-preview>
            <div>
              <div class="warehouse-receiving-workflow-card-title">Pick evidence preview</div>
              <div class="warehouse-receiving-workflow-card-note">${escapeHtml(stateTitle || header.state_label || "Visible item lines")} remain source evidence only until a later workflow is enabled.</div>
            </div>
            <div class="warehouse-receiving-count-grid">
              ${previewLines.length ? previewLines.map(renderPickingEvidenceRow).join("") : `<div class="warehouse-receiving-count-row" data-warehouse-picking-evidence-row="empty"><div class="warehouse-receiving-count-row-title">No visible pick lines</div><div class="warehouse-receiving-meta">No line evidence can be previewed for this order.</div></div>`}
            </div>
          </div>
          <div class="warehouse-receiving-workflow-card" data-warehouse-picking-exception-preview>
            <div>
              <div class="warehouse-receiving-workflow-card-title">Exception categories</div>
              <div class="warehouse-receiving-workflow-card-note">Outbound exceptions stay internal until manager and Sales ownership rules are approved.</div>
            </div>
            <div class="warehouse-receiving-discrepancy-grid">
              ${exceptions.map((card) => renderPickingWorkflowCard(card, "data-warehouse-picking-exception-category")).join("")}
            </div>
          </div>
          <div class="warehouse-receiving-workflow-card" data-warehouse-picking-manager-preview>
            <div>
              <div class="warehouse-receiving-workflow-card-title">Manager decision preview</div>
              <div class="warehouse-receiving-workflow-card-note">Future manager choices remain preview-only and do not create stock documents.</div>
            </div>
            <div class="warehouse-receiving-manager-grid">
              ${managerDecisions.map((card) => renderPickingWorkflowCard(card, "data-warehouse-picking-manager-decision")).join("")}
            </div>
          </div>
        </div>
        <div class="warehouse-receiving-workflow-card" data-warehouse-picking-delivery-policy>
          <div class="warehouse-receiving-workflow-card-title">Delivery policy preview</div>
          <div class="warehouse-receiving-workflow-card-note">Delivery Note draft, Pick List, Stock Reservation, and customer-facing dispatch steps are not available from this preview. Later phases must keep Sales/Admin ownership and native route restrictions explicit.</div>
        </div>
      </section>
    `;
  }

  function activatePickingTab($root, tabKey) {
    const key = tabKey || "item_lines";
    $root.find("[data-warehouse-picking-tab]").each(function () {
      const isActive = String(this.getAttribute("data-warehouse-picking-tab")) === key;
      $(this).toggleClass("is-active", isActive).attr("aria-selected", isActive ? "true" : "false");
    });
    $root.find("[data-warehouse-picking-panel]").each(function () {
      const isActive = String(this.getAttribute("data-warehouse-picking-panel")) === key;
      $(this).toggleClass("is-active", isActive).attr("hidden", isActive ? null : "hidden");
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
    const readinessCards = pickingReadinessSummary(lines, unavailable);
    const shellOrder = header.sales_order || viewState.salesOrder || "";
    const $root = $(`
      <div class="sales-console-shell warehouse-receiving-shell warehouse-picking-shell warehouse-visual-foundation" data-erpw-workspace="warehouse" data-warehouse-view="picking-review" data-erpw-console-runtime="ready" data-warehouse-picking-order="${escapeHtml(shellOrder)}" data-warehouse-visual-foundation="w13c2">
        <section class="warehouse-receiving-header warehouse-picking-header warehouse-visual-command" data-warehouse-picking-command>
          <div class="warehouse-receiving-head">
            <div class="warehouse-receiving-command warehouse-visual-command-title">
              <div class="warehouse-receiving-eyebrow">Read-only picking posture</div>
              <h1 class="warehouse-receiving-title">Picking Review</h1>
              <div class="warehouse-receiving-subtitle">${escapeHtml(unavailable ? statePayload.detail || "Picking work could not be loaded. Refresh or contact an administrator." : pickingSummaryText(header))}</div>
              <div class="warehouse-receiving-chip-row warehouse-visual-chip-row" data-warehouse-picking-identity-chips>
                <span class="warehouse-receiving-chip warehouse-visual-chip" data-warehouse-picking-identity-chip>${escapeHtml(shellOrder || "Order not visible")}</span>
                <span class="warehouse-receiving-chip warehouse-visual-chip" data-warehouse-picking-identity-chip>${escapeHtml(header.customer || "Customer not visible")}</span>
                <span class="warehouse-receiving-chip warehouse-visual-chip" data-warehouse-picking-identity-chip>${escapeHtml(header.age_label || header.required_date || "Delivery date not visible")}</span>
                <span class="warehouse-receiving-chip warehouse-visual-chip" data-warehouse-picking-identity-chip>${escapeHtml(header.target_warehouse || "Warehouse not visible")}</span>
                <span class="warehouse-receiving-chip warehouse-visual-chip" data-warehouse-picking-identity-chip>${escapeHtml(header.status || header.state_label || statePayload.title || "Review")}</span>
                <span class="warehouse-receiving-chip warehouse-visual-chip is-read-only" data-warehouse-picking-identity-chip>Read-only</span>
              </div>
            </div>
            <div class="warehouse-receiving-actions warehouse-visual-action-strip">
              <button type="button" class="warehouse-receiving-button" data-warehouse-picking-back>Back to outbound picking</button>
              <button type="button" class="warehouse-receiving-button" data-warehouse-picking-refresh>Refresh</button>
            </div>
          </div>
          ${unavailable ? `<div class="warehouse-receiving-state-panel warehouse-visual-fallback" data-warehouse-picking-empty><strong>${escapeHtml(statePayload.title || "Picking review unavailable")}</strong><span>${escapeHtml(statePayload.detail || "Picking work could not be loaded. Refresh or contact an administrator.")}</span></div>` : `
            <div class="warehouse-receiving-command-grid warehouse-picking-command-grid warehouse-visual-fact-strip">
              <div class="warehouse-receiving-command-fact warehouse-visual-fact" data-warehouse-picking-command-fact="customer"><span>Customer</span><strong>${escapeHtml(header.customer || "Not visible")}</strong></div>
              <div class="warehouse-receiving-command-fact warehouse-visual-fact" data-warehouse-picking-command-fact="warehouse"><span>Warehouse</span><strong>${escapeHtml(header.target_warehouse || "Not visible")}</strong></div>
              <div class="warehouse-receiving-command-fact warehouse-visual-fact" data-warehouse-picking-command-fact="delivery"><span>Delivery timing</span><strong>${escapeHtml(header.required_date || header.age_label || "Not visible")}</strong></div>
              <div class="warehouse-receiving-command-fact warehouse-visual-fact" data-warehouse-picking-command-fact="state"><span>Picking state</span><strong>${escapeHtml(header.state_label || header.status || "Review")}</strong></div>
            </div>
            <section class="warehouse-receiving-posture-panel warehouse-picking-posture-panel" data-warehouse-picking-posture-panel>
              <div class="warehouse-receiving-posture-head">
                <div>
                  <h2 class="warehouse-receiving-posture-title">Picking posture</h2>
                  <div class="warehouse-receiving-posture-note">${escapeHtml(header.age_label || "Picking posture visible")} · ${escapeHtml(header.remaining_summary || "No open quantity summary visible")}</div>
                </div>
              </div>
              <div class="warehouse-receiving-posture-layout">
                <div class="warehouse-receiving-posture-block">
                  <div class="warehouse-receiving-posture-kicker">Line readiness</div>
                  <div class="warehouse-receiving-readiness warehouse-picking-readiness warehouse-visual-summary-grid" data-warehouse-picking-readiness>
                    ${readinessCards.map(renderPickingReadinessCard).join("")}
                  </div>
                </div>
                <div class="warehouse-receiving-posture-block">
                  <div class="warehouse-receiving-posture-kicker">Fulfillment posture</div>
                  <div class="warehouse-receiving-cards warehouse-visual-summary-grid">${cards.map(renderPickingCard).join("")}</div>
                </div>
              </div>
            </section>
          `}
        </section>
        <section class="warehouse-receiving-guardrail warehouse-picking-guardrail warehouse-visual-guardrail" data-warehouse-picking-guardrail>
          <strong>Review only</strong>
          <span>No stock is reserved, picked, shipped, or delivered from this page. Use this page to understand picking posture before any separate outbound process.</span>
        </section>
        ${unavailable ? "" : renderPickingWorkflowShell(header, lines, statePayload)}
        <section class="warehouse-receiving-detail warehouse-picking-detail" data-warehouse-picking-detail>
          <div class="warehouse-receiving-detail-head" data-warehouse-picking-detail-head>
            <div>
              <h2 class="warehouse-receiving-section-title">Picking Lines</h2>
              <div class="warehouse-receiving-meta">Ordered quantity, delivered quantity, open quantity, available posture, and warehouse are shown for review only.</div>
            </div>
            <div class="warehouse-receiving-tabs warehouse-visual-tab-strip">
              ${tabs.map((tab) => `<button type="button" class="warehouse-receiving-tab warehouse-visual-tab" data-warehouse-picking-tab="${escapeHtml(tab.key || "")}">${escapeHtml(tab.label || "")} ${escapeHtml(tab.count == null ? "" : `(${tab.count})`)}</button>`).join("")}
            </div>
          </div>
          <div class="warehouse-receiving-panel warehouse-visual-row-list is-active" data-warehouse-picking-panel="item_lines">
            ${lines.length ? lines.map(renderPickingLine).join("") : `<div class="warehouse-receiving-line warehouse-visual-fallback" data-warehouse-picking-empty><span class="warehouse-receiving-meta">No item lines visible for this order.</span></div>`}
          </div>
          <div class="warehouse-receiving-panel warehouse-visual-row-list" data-warehouse-picking-panel="stock_readiness">
            <div class="warehouse-receiving-history-note">Line-level stock readiness is shown as bounded review posture. This panel does not open native stock pages.</div>
            ${lines.length ? lines.map(renderPickingReadinessRow).join("") : `<div class="warehouse-receiving-history-row warehouse-visual-fallback" data-warehouse-picking-empty><span class="warehouse-receiving-meta">No stock readiness visible for this order.</span></div>`}
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
      loadPickingReview(viewState, viewState.salesOrder, { force: true });
    });
    $root.find("[data-warehouse-picking-tab]").on("click", function (event) {
      event.preventDefault();
      activatePickingTab($root, String(this.getAttribute("data-warehouse-picking-tab") || "item_lines"));
    });
    activatePickingTab($root, "item_lines");
    replaceWarehouseRouteHost(viewState, $root);
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

  function loadPickingReview(viewState, salesOrder, options) {
    const order = String(salesOrder || pickingSalesOrderFromRoute() || "").trim();
    const force = Boolean(options && options.force);
    const signature = pickingLoadSignature(order);
    if (!force && viewState.loadingPromise && viewState.loadingSignature === signature) {
      markWarehouseDiagnostic("pickingDuplicateLoadReused");
      return viewState.loadingPromise;
    }
    if (!force && viewState.loadedSignature === signature && hasRenderedPickingShell(viewState, order)) {
      markWarehouseDiagnostic("pickingDuplicateRenderSkipped");
      return Promise.resolve(viewState.lastPayload || {});
    }

    markWarehouseDiagnostic("pickingServiceCallAttempted");
    viewState.salesOrder = order;
    const requestToken = (viewState.requestSerial || 0) + 1;
    viewState.requestSerial = requestToken;
    viewState.loadingSignature = signature;
    viewState.loadedSignature = "";
    renderPickingLoading(viewState);

    const finishRequest = (payload) => {
      const currentOrder = pickingSalesOrderFromRoute();
      const shouldRender = (
        viewState.requestSerial === requestToken
        && viewState.loadingSignature === signature
        && isActivePickingRoute()
        && String(currentOrder || "").trim() === order
      );
      if (viewState.requestSerial === requestToken && viewState.loadingSignature === signature) {
        viewState.loadingPromise = null;
        viewState.loadingSignature = "";
      }
      if (!shouldRender) {
        markWarehouseDiagnostic("pickingStaleResponseIgnored");
        return payload;
      }
      viewState.loadedSignature = signature;
      viewState.lastPayload = payload;
      renderPickingReviewPayload(viewState, payload);
      return payload;
    };

    const requestPromise = frappe.call({
      method: PICKING_METHOD,
      args: { sales_order: viewState.salesOrder },
    }).then((response) => finishRequest(response && response.message ? response.message : {})).catch(() => finishRequest({
      state: { kind: "error", title: "Picking review unavailable", detail: "Picking work could not be loaded. Refresh or contact an administrator." },
      header: { sales_order: viewState.salesOrder || "" },
      summary_cards: [],
      tabs: [
        { key: "item_lines", label: "Item Lines", count: 0 },
        { key: "stock_readiness", label: "Stock Readiness", count: 0 },
      ],
      lines: [],
    }));
    viewState.loadingPromise = requestPromise;
    return requestPromise;
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
    const state = {
      page,
      $host,
      contextToken: "",
      requestSerial: 0,
      loadingSignature: "",
      loadingPromise: null,
      loadedSignature: "",
      lastPayload: null,
    };
    wrapper.__erpwWarehouseStockExceptionReview = state;
    return state;
  }

  function stockExceptionReviewLoadSignature(contextToken) {
    return `${stockExceptionRouteSignature()}::${String(contextToken || "").trim()}`;
  }

  function hasRenderedStockExceptionReviewShell(viewState, contextToken) {
    const host = viewState && viewState.$host && viewState.$host.get ? viewState.$host.get(0) : null;
    if (!host || !document.documentElement.contains(host)) return false;
    const shell = host.querySelector('.warehouse-stock-exception-review-shell[data-warehouse-view="stock-exception-review"]');
    if (!shell) return false;
    return String(shell.getAttribute("data-warehouse-stock-exception-token") || "") === String(contextToken || "").trim();
  }

  function stockExceptionSummaryText(header) {
    const parts = [header.sales_order || header.item_code, "Read-only stock exception posture"].filter(Boolean);
    return parts.length ? parts.join(" · ") : "Read-only stock exception posture";
  }

  function stockExceptionIdentityChips(header) {
    return [
      { key: "mode", label: "Read-only" },
      { key: "exception", label: header.exception_label || header.title || "Stock exception" },
      { key: "order", label: header.sales_order || "Demand not visible" },
      { key: "item", label: header.item_code || "Item not visible" },
      { key: "warehouse", label: header.source_warehouse || "Warehouse not visible" },
      { key: "timing", label: header.urgency_label || header.required_date || "Review timing not visible" },
    ].slice(0, 6);
  }

  function stockExceptionCommandFacts(header) {
    return [
      { key: "demand", label: "Demand at risk", value: header.sales_order || header.customer || "Visible demand" },
      { key: "item", label: "Item", value: [header.item_code, header.item_name].filter(Boolean).join(" - ") || "Item posture" },
      { key: "warehouse", label: "Warehouse posture", value: header.source_warehouse || "Warehouse not shown" },
      { key: "timing", label: "Review timing", value: header.urgency_label || header.required_date || "Review timing not shown" },
    ];
  }

  function stockExceptionReviewCards(cards, statePayload) {
    if (cards.length) return cards;
    const stateTitle = statePayload && statePayload.title ? statePayload.title : "Review unavailable";
    return [
      { key: "review_state", label: "Review State", value: stateTitle, note: "Visible details are limited for this review." },
      { key: "demand_posture", label: "Demand Posture", value: "Not visible", note: "Demand context is not visible in this state." },
      { key: "stock_posture", label: "Stock Posture", value: "Not visible", note: "Warehouse posture is not visible in this state." },
      { key: "review_paths", label: "Review Paths", value: "Unavailable", note: "Custom review paths appear only when available." },
    ];
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
    const visibleItems = items.length ? items : [
      { label: "Review state", value: "Details not visible" },
      { label: "Visible summary", value: panel.summary || "No details visible for this section." },
      { label: "Workspace", value: "Warehouse Console" },
      { label: "Posture", value: "Read-only" },
    ];
    const target = panel.route_target || {};
    const postureToken = target.route === STOCK_POSTURE_PAGE_KEY ? String(target.context_token || "") : "";
    return `
      <section class="warehouse-stock-exception-review-panel" data-warehouse-stock-exception-${escapeHtml(panelKey)}-panel data-warehouse-stock-exception-review-panel>
        <div class="warehouse-inbound-group-head">
          <h2 class="warehouse-inbound-group-title">${escapeHtml(panel.title || "")}</h2>
          <div class="warehouse-inbound-group-note">${escapeHtml(panel.summary || "")}</div>
        </div>
        <div class="warehouse-stock-exception-review-facts">
          ${visibleItems.map((item) => `
            <div class="warehouse-stock-exception-review-fact" data-warehouse-stock-exception-review-fact>
              <span>${escapeHtml(item.label || "")}</span>
              <strong>${escapeHtml(item.value == null ? "" : item.value)}</strong>
            </div>
          `).join("")}
        </div>
        ${postureToken ? `<button type="button" class="warehouse-receiving-button" data-warehouse-stock-exception-open-posture data-warehouse-stock-exception-posture-token="${escapeHtml(postureToken)}">Review stock posture</button>` : ""}
      </section>
    `;
  }

  function renderNextReviewPanel(panel) {
    const items = Array.isArray(panel.items) ? panel.items : [];
    return `
      <section class="warehouse-stock-exception-review-panel" data-warehouse-stock-exception-next-panel data-warehouse-stock-exception-review-panel>
        <div class="warehouse-inbound-group-head">
          <h2 class="warehouse-inbound-group-title">${escapeHtml(panel.title || "Recommended Review")}</h2>
          <div class="warehouse-inbound-group-note">${escapeHtml(panel.summary || "")}</div>
        </div>
        <div class="warehouse-stock-exception-next-grid">
          ${items.length ? items.map((item) => {
            const target = item.target || {};
            const targetKind = target.context_token && target.route === STOCK_POSTURE_PAGE_KEY ? "stock_posture" : target.purchase_order ? "receiving" : target.sales_order ? "picking" : "stock";
            return `
              <button type="button" class="warehouse-stock-exception-next-card" data-warehouse-stock-exception-next-card data-warehouse-stock-exception-next-target="${escapeHtml(targetKind)}" data-warehouse-stock-exception-next-sales-order="${escapeHtml(target.sales_order || "")}" data-warehouse-stock-exception-next-purchase-order="${escapeHtml(target.purchase_order || "")}" data-warehouse-stock-exception-next-token="${escapeHtml(target.context_token || "")}">
                <span>${escapeHtml(item.label || "")}</span>
                <strong>${escapeHtml(item.value || "")}</strong>
              </button>
            `;
          }).join("") : `
            <div class="warehouse-stock-exception-next-card" data-warehouse-stock-exception-next-card data-warehouse-stock-exception-next-unavailable>
              <span>Review path unavailable</span>
              <strong>Custom Warehouse review paths appear here when visible for this exception.</strong>
            </div>
            <div class="warehouse-stock-exception-next-card" data-warehouse-stock-exception-next-card data-warehouse-stock-exception-next-unavailable>
              <span>Stay in stock exceptions</span>
              <strong>Use Back to stock exceptions or Refresh to review the latest visible posture.</strong>
            </div>
          `}
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
    const identityChips = stockExceptionIdentityChips(header);
    const commandFacts = stockExceptionCommandFacts(header);
    const visibleCards = stockExceptionReviewCards(cards, statePayload);
    const $root = $(`
      <div class="sales-console-shell warehouse-receiving-shell warehouse-stock-exception-review-shell" data-erpw-workspace="warehouse" data-warehouse-view="stock-exception-review" data-erpw-console-runtime="ready" data-warehouse-stock-exception-review-shell="true" data-warehouse-stock-exception-token="${escapeHtml(header.context_token || viewState.contextToken || "")}">
        <section class="warehouse-receiving-header warehouse-stock-exception-review-header" data-warehouse-stock-exception-review-command>
          <div class="warehouse-receiving-head">
            <div class="warehouse-stock-exception-review-command">
              <div class="warehouse-stock-exception-review-eyebrow">Read-only stock exception review</div>
              <h1 class="warehouse-receiving-title">Stock Exception Review</h1>
              <div class="warehouse-receiving-subtitle">${escapeHtml(unavailable ? statePayload.detail || "Stock exception review could not be loaded. Refresh or contact an administrator." : stockExceptionSummaryText(header))}</div>
              <div class="warehouse-stock-exception-review-chip-row">
                ${identityChips.map((chip) => `<span class="warehouse-inbound-chip ${chip.key === "mode" ? "is-read-only" : ""}" data-warehouse-stock-exception-review-identity-chip="${escapeHtml(chip.key)}">${escapeHtml(chip.label)}</span>`).join("")}
              </div>
            </div>
            <div class="warehouse-receiving-actions">
              <button type="button" class="warehouse-receiving-button" data-warehouse-stock-exception-back>Back to stock exceptions</button>
              <button type="button" class="warehouse-receiving-button" data-warehouse-stock-exception-refresh>Refresh</button>
            </div>
          </div>
          ${unavailable ? `<div class="warehouse-console-state-detail" data-warehouse-stock-exception-review-empty>${escapeHtml(statePayload.title || "Stock exception review unavailable")}</div>` : `
            <div class="warehouse-receiving-note"><span class="warehouse-inbound-badge">${escapeHtml(header.exception_label || "")}</span> ${escapeHtml(header.urgency_label || "")} · ${escapeHtml(header.explanation || "")}</div>
          `}
          <div class="warehouse-stock-exception-review-command-grid">
            ${commandFacts.map((fact) => `
              <div class="warehouse-stock-exception-review-command-fact" data-warehouse-stock-exception-review-command-fact="${escapeHtml(fact.key)}">
                <span>${escapeHtml(fact.label)}</span>
                <strong>${escapeHtml(fact.value)}</strong>
              </div>
            `).join("")}
          </div>
          <section class="warehouse-receiving-posture-panel warehouse-stock-exception-review-posture-panel" data-warehouse-stock-exception-review-posture-panel>
            <div class="warehouse-receiving-posture-head">
              <div>
                <h2 class="warehouse-receiving-posture-title">Exception posture</h2>
                <div class="warehouse-receiving-posture-note">${escapeHtml(header.explanation || header.urgency_label || "Demand risk, stock posture, and inbound cover are shown for review only.")}</div>
              </div>
            </div>
            <div class="warehouse-receiving-posture-layout">
              <div class="warehouse-receiving-posture-block warehouse-stock-exception-review-posture-block">
                <div class="warehouse-receiving-posture-kicker">Demand and stock posture</div>
                <div class="warehouse-receiving-cards">${visibleCards.map(renderStockExceptionReviewCard).join("")}</div>
              </div>
            </div>
          </section>
        </section>
        <section class="warehouse-inbound-queue-guardrail warehouse-stock-exception-review-guardrail" data-warehouse-stock-exception-review-guardrail>
          <strong>Review only</strong>
          <span>No stock is reserved, reconciled, transferred, picked, received, shipped, posted, or adjusted here. Use this page to understand demand risk, stock posture, and inbound cover before any separate warehouse process.</span>
        </section>
        <section class="warehouse-stock-exception-review-grid">
          ${renderStockExceptionPanel(panels.demand || {}, "demand")}
          ${renderStockExceptionPanel(panels.stock || {}, "stock")}
          ${renderStockExceptionPanel(panels.inbound || {}, "inbound")}
          ${renderNextReviewPanel(panels.next_reviews || {})}
        </section>
        <section class="warehouse-receiving-detail warehouse-stock-exception-review-related-panel" data-warehouse-stock-exception-related-panel>
          <div class="warehouse-inbound-group-head">
            <h2 class="warehouse-inbound-group-title">Related Reviews</h2>
            <div class="warehouse-inbound-group-note">Custom Warehouse review paths for this exception.</div>
          </div>
          <div class="warehouse-receiving-panel is-active">
            ${relatedRows.length ? relatedRows.map(renderStockExceptionRelatedRow).join("") : `<div class="warehouse-receiving-history-row" data-warehouse-stock-exception-related-row="unavailable" data-warehouse-stock-exception-review-empty><div><div class="warehouse-receiving-strong">Related review unavailable</div><div class="warehouse-receiving-meta">Custom Warehouse routes appear here when visible for this exception.</div></div><div class="warehouse-receiving-meta">Read-only</div></div>`}
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
      loadStockExceptionReview(viewState, viewState.contextToken, { force: true });
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
    replaceWarehouseRouteHost(viewState, $root);
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

  function loadStockExceptionReview(viewState, contextToken, options) {
    const token = String(contextToken || stockExceptionTokenFromRoute() || "").trim();
    const force = Boolean(options && options.force);
    const signature = stockExceptionReviewLoadSignature(token);
    if (!force && viewState.loadingPromise && viewState.loadingSignature === signature) {
      markWarehouseDiagnostic("stockExceptionReviewDuplicateLoadReused");
      return viewState.loadingPromise;
    }
    if (!force && viewState.loadedSignature === signature && hasRenderedStockExceptionReviewShell(viewState, token)) {
      markWarehouseDiagnostic("stockExceptionReviewDuplicateRenderSkipped");
      return Promise.resolve(viewState.lastPayload || {});
    }

    markWarehouseDiagnostic("stockExceptionReviewServiceCallAttempted");
    viewState.contextToken = token;
    const requestToken = (viewState.requestSerial || 0) + 1;
    viewState.requestSerial = requestToken;
    viewState.loadingSignature = signature;
    viewState.loadedSignature = "";
    renderStockExceptionReviewLoading(viewState);

    const finishRequest = (payload) => {
      const currentToken = stockExceptionTokenFromRoute();
      const shouldRender = (
        viewState.requestSerial === requestToken
        && viewState.loadingSignature === signature
        && isActiveStockExceptionRoute()
        && String(currentToken || "").trim() === token
      );
      if (viewState.requestSerial === requestToken && viewState.loadingSignature === signature) {
        viewState.loadingPromise = null;
        viewState.loadingSignature = "";
      }
      if (!shouldRender) {
        markWarehouseDiagnostic("stockExceptionReviewStaleResponseIgnored");
        return payload;
      }
      viewState.loadedSignature = signature;
      viewState.lastPayload = payload;
      renderStockExceptionReviewPayload(viewState, payload);
      return payload;
    };

    const requestPromise = frappe.call({
      method: STOCK_EXCEPTION_REVIEW_METHOD,
      args: { context_token: viewState.contextToken },
    }).then((response) => finishRequest(response && response.message ? response.message : {})).catch(() => finishRequest({
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
    }));
    viewState.loadingPromise = requestPromise;
    return requestPromise;
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
    const state = {
      page,
      $host,
      contextToken: "",
      requestSerial: 0,
      loadingSignature: "",
      loadingPromise: null,
      loadedSignature: "",
      lastPayload: null,
    };
    wrapper.__erpwWarehouseStockPostureReview = state;
    return state;
  }

  function hasReadyStockPostureReviewShellForToken(contextToken) {
    const token = String(contextToken || stockPostureTokenFromRoute() || "").trim();
    const shell = document.querySelector('.warehouse-stock-posture-shell[data-warehouse-view="stock-posture-review"]');
    if (!shell) return false;
    return !token || String(shell.getAttribute("data-warehouse-stock-posture-token") || "").trim() === token;
  }

  function stockPostureSummaryText(header) {
    const parts = [header.item_code, header.item_name, header.warehouse].filter(Boolean);
    return parts.length ? parts.join(" - ") : "Item and warehouse posture review.";
  }

  function stockPostureCardValue(cards, keys, fallback) {
    const wanted = Array.isArray(keys) ? keys : [keys];
    const match = cards.find((card) => wanted.includes(String(card.key || "")));
    return match && match.value != null ? match.value : fallback;
  }

  function stockPostureIdentityChips(header) {
    return [
      { key: "mode", label: "Read-only" },
      { key: "posture", label: header.posture_label || header.title || "Stock posture" },
      { key: "item", label: header.item_code || "Item not visible" },
      { key: "warehouse", label: header.warehouse || "Warehouse not visible" },
      { key: "context", label: header.context_token ? "Review context available" : "Review context not visible" },
      { key: "freshness", label: header.fetched_at ? `Freshness ${header.fetched_at}` : "Freshness not visible" },
    ].slice(0, 6);
  }

  function stockPostureCommandFacts(header, cards) {
    return [
      { key: "available", label: "Visible stock", value: stockPostureCardValue(cards, ["available", "actual_qty"], "Not visible") },
      { key: "projected", label: "Projected posture", value: stockPostureCardValue(cards, "projected", "Not visible") },
      { key: "open_demand", label: "Open demand", value: stockPostureCardValue(cards, "open_demand", "Not visible") },
      { key: "inbound_cover", label: "Inbound cover", value: stockPostureCardValue(cards, "inbound_cover", header.posture_label || "Not visible") },
    ];
  }

  function stockPostureReviewCards(cards, statePayload) {
    if (cards.length) return cards;
    const stateTitle = statePayload && statePayload.title ? statePayload.title : "Review unavailable";
    return [
      { key: "available", label: "Available", value: "Not visible", note: "Available stock is not visible in this state." },
      { key: "open_demand", label: "Open Demand", value: "Not visible", note: "Demand posture is not visible in this state." },
      { key: "inbound_cover", label: "Inbound Cover", value: "Not visible", note: "Inbound cover is not visible in this state." },
      { key: "review_state", label: "Review State", value: stateTitle, note: "Visible details are limited for this review." },
    ];
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
    const visibleItems = items.length ? items : [
      { label: "Review state", value: "Details not visible" },
      { label: "Visible summary", value: panel.summary || "No details visible for this section." },
      { label: "Workspace", value: "Warehouse Console" },
      { label: "Posture", value: "Read-only" },
    ];
    return `
      <section class="warehouse-stock-exception-review-panel" data-warehouse-stock-posture-panel="${escapeHtml(panelKey)}">
        <div class="warehouse-inbound-group-head">
          <h2 class="warehouse-inbound-group-title">${escapeHtml(panel.title || "")}</h2>
          <div class="warehouse-inbound-group-note">${escapeHtml(panel.summary || "")}</div>
        </div>
        <div class="warehouse-stock-exception-review-facts">
          ${visibleItems.map((item) => `
            <div class="warehouse-stock-exception-review-fact" data-warehouse-stock-posture-fact>
              <span>${escapeHtml(item.label || "")}</span>
              <strong>${escapeHtml(item.value == null ? "" : item.value)}</strong>
            </div>
          `).join("")}
        </div>
      </section>
    `;
  }

  function stockPostureRecommendedItems(actionTargets) {
    const items = [];
    const exceptionTarget = actionTargets.stock_exception || actionTargets.back || {};
    if (exceptionTarget.route === STOCK_EXCEPTION_PAGE_KEY && exceptionTarget.context_token) {
      items.push({ label: "Review exception", value: "Open the related stock exception review.", target: exceptionTarget });
    }
    if (actionTargets.picking && actionTargets.picking.route === PICKING_PAGE_KEY && actionTargets.picking.sales_order) {
      items.push({ label: "View picking review", value: "Review outbound demand inside Warehouse.", target: actionTargets.picking });
    }
    if (actionTargets.receiving && actionTargets.receiving.route === RECEIVING_PAGE_KEY && actionTargets.receiving.purchase_order) {
      items.push({ label: "View inbound review", value: "Review inbound cover inside Warehouse.", target: actionTargets.receiving });
    }
    return items;
  }

  function renderStockPostureRecommendedPanel(items) {
    return `
      <section class="warehouse-receiving-detail warehouse-stock-posture-recommended-panel" data-warehouse-stock-posture-recommended-panel>
        <div class="warehouse-inbound-group-head">
          <h2 class="warehouse-inbound-group-title">Recommended Review</h2>
          <div class="warehouse-inbound-group-note">Read-only Warehouse paths connected to this posture.</div>
        </div>
        <div class="warehouse-stock-posture-recommended-grid">
          ${items.length ? items.map((item) => {
            const target = item.target || {};
            const targetKind = stockPostureRouteKind(target);
            return `
              <button type="button" class="warehouse-stock-posture-recommended-card" data-warehouse-stock-posture-recommended-card data-warehouse-stock-posture-related-target="${escapeHtml(targetKind)}" data-warehouse-stock-posture-related-sales-order="${escapeHtml(target.sales_order || "")}" data-warehouse-stock-posture-related-purchase-order="${escapeHtml(target.purchase_order || "")}" data-warehouse-stock-posture-related-token="${escapeHtml(target.context_token || "")}" ${targetKind ? `data-warehouse-stock-posture-route-${escapeHtml(targetKind.replace("_", "-"))}` : ""}>
                <span>${escapeHtml(item.label || "")}</span>
                <strong>${escapeHtml(item.value || "")}</strong>
              </button>
            `;
          }).join("") : `
            <div class="warehouse-stock-posture-recommended-card" data-warehouse-stock-posture-recommended-card data-warehouse-stock-posture-recommended-unavailable>
              <span>Review path unavailable</span>
              <strong>Custom Warehouse review paths appear here when visible for this posture.</strong>
            </div>
            <div class="warehouse-stock-posture-recommended-card" data-warehouse-stock-posture-recommended-card data-warehouse-stock-posture-recommended-unavailable>
              <span>Stay in stock exceptions</span>
              <strong>Use Back to stock exceptions or Refresh to review the latest visible posture.</strong>
            </div>
          `}
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
    const identityChips = stockPostureIdentityChips(header);
    const visibleCards = stockPostureReviewCards(cards, statePayload);
    const commandFacts = stockPostureCommandFacts(header, visibleCards);
    const recommendedItems = stockPostureRecommendedItems(actionTargets);
    const postureSplit = Math.max(2, Math.ceil(visibleCards.length / 2));
    const stockPositionCards = visibleCards.slice(0, postureSplit);
    const demandCoverCards = visibleCards.slice(postureSplit);
    const $root = $(`
      <div class="sales-console-shell warehouse-receiving-shell warehouse-stock-posture-shell" data-erpw-workspace="warehouse" data-warehouse-view="stock-posture-review" data-erpw-console-runtime="ready" data-warehouse-stock-posture-shell="true" data-warehouse-stock-posture-token="${escapeHtml(header.context_token || viewState.contextToken || "")}">
        <section class="warehouse-receiving-header warehouse-stock-posture-header" data-warehouse-stock-posture-command>
          <div class="warehouse-receiving-head">
            <div class="warehouse-stock-posture-command">
              <div class="warehouse-stock-posture-eyebrow">Read-only stock posture review</div>
              <h1 class="warehouse-receiving-title">Stock Posture Review</h1>
              <div class="warehouse-receiving-subtitle">${escapeHtml(unavailable ? statePayload.detail || "Stock posture review could not be loaded. Refresh or contact an administrator." : stockPostureSummaryText(header))}</div>
              <div class="warehouse-stock-posture-chip-row">
                ${identityChips.map((chip) => `<span class="warehouse-inbound-chip ${chip.key === "mode" ? "is-read-only" : ""}" data-warehouse-stock-posture-identity-chip="${escapeHtml(chip.key)}">${escapeHtml(chip.label)}</span>`).join("")}
              </div>
            </div>
            <div class="warehouse-receiving-actions">
              <button type="button" class="warehouse-receiving-button" data-warehouse-stock-posture-back data-warehouse-stock-posture-back-route="${escapeHtml(backTarget.route || "")}" data-warehouse-stock-posture-back-sales-order="${escapeHtml(backTarget.sales_order || "")}" data-warehouse-stock-posture-back-purchase-order="${escapeHtml(backTarget.purchase_order || "")}" data-warehouse-stock-posture-back-token="${escapeHtml(backTarget.context_token || "")}">Back to stock exceptions</button>
              <button type="button" class="warehouse-receiving-button" data-warehouse-stock-posture-refresh>Refresh</button>
            </div>
          </div>
          ${unavailable ? `<div class="warehouse-console-state-detail" data-warehouse-stock-posture-empty>${escapeHtml(statePayload.title || "Stock posture review unavailable")}</div>` : `
            <div class="warehouse-receiving-note"><span class="warehouse-inbound-badge">${escapeHtml(header.posture_label || "")}</span> ${escapeHtml(header.explanation || "")}</div>
          `}
          <div class="warehouse-stock-posture-command-grid">
            ${commandFacts.map((fact) => `
              <div class="warehouse-stock-posture-command-fact" data-warehouse-stock-posture-command-fact="${escapeHtml(fact.key)}">
                <span>${escapeHtml(fact.label)}</span>
                <strong>${escapeHtml(fact.value)}</strong>
              </div>
            `).join("")}
          </div>
        </section>
        <section class="warehouse-receiving-posture-panel warehouse-stock-posture-review-posture-panel" data-warehouse-stock-posture-review-posture-panel>
          <div class="warehouse-receiving-posture-head">
            <h2 class="warehouse-receiving-posture-title">Stock posture</h2>
            <div class="warehouse-receiving-posture-note">${escapeHtml(header.explanation || statePayload.detail || "Visible stock, projected posture, demand, and inbound cover are shown for review only.")}</div>
          </div>
          <div class="warehouse-receiving-posture-layout">
            <div class="warehouse-receiving-posture-block warehouse-stock-posture-review-posture-block">
              <div class="warehouse-receiving-posture-kicker">Stock position</div>
              <div class="warehouse-receiving-cards">${stockPositionCards.map(renderStockPostureCard).join("")}</div>
            </div>
            <div class="warehouse-receiving-posture-block warehouse-stock-posture-review-posture-block">
              <div class="warehouse-receiving-posture-kicker">Demand and cover</div>
              <div class="warehouse-receiving-cards">${demandCoverCards.length ? demandCoverCards.map(renderStockPostureCard).join("") : stockPositionCards.slice(-1).map(renderStockPostureCard).join("")}</div>
            </div>
          </div>
        </section>
        <section class="warehouse-inbound-queue-guardrail warehouse-stock-posture-guardrail" data-warehouse-stock-posture-guardrail>
          <strong>Review only</strong>
          <span>No stock is reserved, reconciled, transferred, picked, received, shipped, posted, or adjusted here. Use this page to understand item posture, demand, and inbound cover before any separate warehouse process.</span>
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
        ${renderStockPostureRecommendedPanel(recommendedItems)}
        <section class="warehouse-receiving-detail" data-warehouse-stock-posture-related-panel>
          <div class="warehouse-inbound-group-head">
            <h2 class="warehouse-inbound-group-title">Related Exceptions</h2>
            <div class="warehouse-inbound-group-note">Custom Warehouse review paths for this item and warehouse.</div>
          </div>
          <div class="warehouse-receiving-panel is-active">
            ${relatedRows.length ? relatedRows.map(renderStockPostureRelatedRow).join("") : `<div class="warehouse-receiving-history-row" data-warehouse-stock-posture-related-row="unavailable" data-warehouse-stock-posture-empty><div><div class="warehouse-receiving-strong">Related exception unavailable</div><div class="warehouse-receiving-meta">Custom Warehouse exception paths appear here when visible for this posture.</div></div><div class="warehouse-receiving-meta">Read-only</div></div>`}
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
      loadStockPostureReview(viewState, viewState.contextToken, { force: true });
    });
    $root.find("[data-warehouse-stock-posture-related-target]").on("click", function (event) {
      event.preventDefault();
      routeStockPostureElement(this);
    });
    replaceWarehouseRouteHost(viewState, $root);
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

  function stockPostureReviewLoadSignature(contextToken) {
    return `stock-posture:${String(contextToken || "").trim()}`;
  }

  function hasRenderedStockPostureShell(viewState, contextToken) {
    if (!viewState || !viewState.$host || !viewState.$host.length) return false;
    const shell = viewState.$host.find('[data-warehouse-stock-posture-shell="true"][data-warehouse-view="stock-posture-review"]').get(0);
    if (!shell) return false;
    const token = String(contextToken || "").trim();
    return !token || String(shell.getAttribute("data-warehouse-stock-posture-token") || "").trim() === token;
  }

  function loadStockPostureReview(viewState, contextToken, options) {
    const token = String(contextToken || stockPostureTokenFromRoute() || "").trim();
    const force = Boolean(options && options.force);
    const signature = stockPostureReviewLoadSignature(token);
    if (!force && viewState.loadingPromise && viewState.loadingSignature === signature) {
      markWarehouseDiagnostic("stockPostureReviewDuplicateLoadReused");
      return viewState.loadingPromise;
    }
    if (!force && viewState.loadedSignature === signature && hasRenderedStockPostureShell(viewState, token)) {
      markWarehouseDiagnostic("stockPostureReviewDuplicateRenderSkipped");
      return Promise.resolve(viewState.lastPayload || {});
    }

    markWarehouseDiagnostic("stockPostureReviewServiceCallAttempted");
    viewState.contextToken = token;
    const requestToken = (viewState.requestSerial || 0) + 1;
    viewState.requestSerial = requestToken;
    viewState.loadingSignature = signature;
    viewState.loadedSignature = "";
    renderStockPostureReviewLoading(viewState);

    const finishRequest = (payload) => {
      const currentToken = stockPostureTokenFromRoute();
      const shouldRender = (
        viewState.requestSerial === requestToken
        && viewState.loadingSignature === signature
        && isActiveStockPostureRoute()
        && String(currentToken || "").trim() === token
      );
      if (viewState.requestSerial === requestToken && viewState.loadingSignature === signature) {
        viewState.loadingPromise = null;
        viewState.loadingSignature = "";
      }
      if (!shouldRender) {
        markWarehouseDiagnostic("stockPostureReviewStaleResponseIgnored");
        return payload;
      }
      viewState.loadedSignature = signature;
      viewState.lastPayload = payload;
      renderStockPostureReviewPayload(viewState, payload);
      return payload;
    };

    const requestPromise = frappe.call({
      method: STOCK_POSTURE_REVIEW_METHOD,
      args: { context_token: viewState.contextToken },
    }).then((response) => finishRequest(response && response.message ? response.message : {})).catch(() => finishRequest({
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
      }));
    viewState.loadingPromise = requestPromise;
    return requestPromise;
  }

  function renderStockPostureReview(wrapper, contextToken) {
    markWarehouseDiagnostic("renderStockPostureReviewEntered");
    const token = String(contextToken || stockPostureTokenFromRoute() || "").trim();
    if (isActiveStockPostureRoute() && hasReadyStockPostureReviewShellForToken(token)) {
      markWarehouseDiagnostic("stockPostureReviewDuplicateRenderSkipped");
      return;
    }
    const viewState = makeStockPosturePage(wrapper);
    if (window.erpWorkspaceConsoleSidebar && typeof window.erpWorkspaceConsoleSidebar.refresh === "function") {
      window.erpWorkspaceConsoleSidebar.refresh();
    }
    loadStockPostureReview(viewState, token);
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

  function movementReviewIdentityChips(header, payload, statePayload) {
    return [
      { key: "mode", label: "Read-only" },
      { key: "movement", label: header.movement_id || "Movement not visible" },
      { key: "posture", label: header.docstatus_label || statePayload.title || "Review posture" },
    ];
  }

  function movementReviewCardValue(card) {
    if (!card || card.value == null || card.value === "") return "Not visible";
    return String(card.value);
  }

  function movementReviewFallbackCards(header, cards, unavailable) {
    if (Array.isArray(cards) && cards.length) return cards;
    return [
      { key: "movement", label: "Movement", value: header.movement_id || "Not visible", note: unavailable ? "Details not visible" : "Movement identity" },
      { key: "posture", label: "Posture", value: header.docstatus_label || "Review", note: header.purpose || header.movement_type || "Movement posture" },
      { key: "timing", label: "Posted", value: [header.posting_date, header.posting_time].filter(Boolean).join(" ") || "Not visible", note: "Posted movement timing" },
      { key: "quantity", label: "Quantity", value: header.quantity_summary || "Not visible", note: `${header.item_count == null ? "0" : header.item_count} items shown` },
    ];
  }

  function movementReviewCommandFacts(header, cards, unavailable) {
    const safeCards = movementReviewFallbackCards(header, cards, unavailable);
    const byKey = (keys) => {
      const wanted = Array.isArray(keys) ? keys : [keys];
      return safeCards.find((card) => wanted.includes(String(card && card.key || ""))) || {};
    };
    return [
      { key: "reference", label: "Movement", value: header.movement_id || movementReviewCardValue(byKey("movement")) },
      { key: "type", label: "Movement type", value: header.purpose || header.movement_type || movementReviewCardValue(byKey("posture")) },
      { key: "posted", label: "Posted", value: [header.posting_date, header.posting_time].filter(Boolean).join(" ") || movementReviewCardValue(byKey("timing")) },
      { key: "direction", label: "Direction", value: header.direction_label || "Details not visible" },
    ];
  }

  function renderMovementReviewCommandFact(fact) {
    return `
      <div class="warehouse-movement-review-command-fact" data-warehouse-movement-review-command-fact="${escapeHtml(fact.key || "")}">
        <span>${escapeHtml(fact.label || "")}</span>
        <strong>${escapeHtml(fact.value || "Not visible")}</strong>
      </div>
    `;
  }

  function renderMovementReviewCard(card) {
    return `
      <div class="warehouse-receiving-card" data-warehouse-movement-review-card="${escapeHtml(card.key || "")}" data-warehouse-movement-review-summary-card>
        <div class="warehouse-receiving-card-label">${escapeHtml(card.label || "")}</div>
        <div class="warehouse-receiving-card-value">${escapeHtml(movementReviewCardValue(card))}</div>
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
            <div class="warehouse-stock-exception-panel-item" data-warehouse-movement-review-fact="${escapeHtml(panelKey || "")}">
              <span>${escapeHtml(item.label || "")}</span>
              <strong>${escapeHtml(item.value || "")}</strong>
            </div>
          `).join("") : `<div class="warehouse-inbound-meta" data-warehouse-movement-review-empty>Details not visible for this section.</div>`}
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
      <div class="warehouse-receiving-line warehouse-movement-review-line-card" data-warehouse-movement-review-line="${escapeHtml(line.item_code || "")}">
        <div class="warehouse-movement-review-line-main">
          <div>
            <div class="warehouse-receiving-strong">${escapeHtml(line.item_code || "Item not visible")}</div>
            <div class="warehouse-receiving-meta">${escapeHtml(line.item_name || "Item name not visible")}</div>
          </div>
          <div class="warehouse-receiving-meta">${escapeHtml(line.quantity || "0")} ${escapeHtml(line.stock_uom || "")}</div>
          <div class="warehouse-receiving-meta">${escapeHtml(line.direction_label || "Warehouse direction not visible")}</div>
          <div class="warehouse-receiving-actions">${postureButton}</div>
        </div>
        <div class="warehouse-movement-review-line-facts" data-warehouse-movement-review-line-facts>
          <div class="warehouse-movement-review-line-fact" data-warehouse-movement-review-line-fact="source"><span>Source</span><strong>${escapeHtml(line.source_warehouse || "Not visible")}</strong></div>
          <div class="warehouse-movement-review-line-fact" data-warehouse-movement-review-line-fact="target"><span>Target</span><strong>${escapeHtml(line.target_warehouse || "Not visible")}</strong></div>
          <div class="warehouse-movement-review-line-fact" data-warehouse-movement-review-line-fact="quantity"><span>Quantity</span><strong>${escapeHtml(line.quantity || "0")} ${escapeHtml(line.stock_uom || "")}</strong></div>
          <div class="warehouse-movement-review-line-fact" data-warehouse-movement-review-line-fact="state"><span>Review state</span><strong>${escapeHtml(line.line_note || "Details not visible")}</strong></div>
        </div>
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
    const rawPanels = payload.panels || {};
    const panels = Object.keys(rawPanels).length ? rawPanels : {
      direction: payload.direction_panel || {},
      related: payload.related_panel || {},
    };
    const lineGroups = Array.isArray(payload.line_groups) ? payload.line_groups : [];
    const relatedRoutes = Array.isArray(payload.related_routes) ? payload.related_routes : [];
    const statePayload = payload.state || {};
    const actionTargets = payload.action_targets || {};
    const backTarget = actionTargets.back || {};
    const backQueueKey = normalizeQueueKey(backTarget.queue_key || "");
    const backLabel = backQueueKey === TRANSFER_VISIBILITY_KEY ? "Back to transfer visibility" : "Back to movement visibility";
    const unavailable = ["restricted", "error", "unavailable"].includes(String(statePayload.kind || ""));
    const safeCards = movementReviewFallbackCards(header, cards, unavailable);
    const identityChips = movementReviewIdentityChips(header, payload, statePayload);
    const commandFacts = movementReviewCommandFacts(header, safeCards, unavailable);
    const movementSplit = Math.max(2, Math.ceil(safeCards.length / 2));
    const movementEvidenceCards = safeCards.slice(0, movementSplit);
    const movementContextCards = safeCards.slice(movementSplit);
    const $root = $(`
      <div class="sales-console-shell warehouse-receiving-shell warehouse-movement-review-shell" data-erpw-workspace="warehouse" data-warehouse-view="movement-review" data-erpw-console-runtime="ready" data-warehouse-movement-review-shell="true" data-warehouse-movement-review-state="${escapeHtml(statePayload.kind || "ready")}" data-warehouse-movement-review-token="${escapeHtml(header.context_token || viewState.contextToken || "")}">
        <section class="warehouse-receiving-header warehouse-movement-review-header" data-warehouse-movement-review-command>
          <div class="warehouse-receiving-head">
            <div class="warehouse-movement-review-command">
              <div class="warehouse-movement-review-eyebrow">Movement Review</div>
              <h1 class="warehouse-receiving-title">Movement Review</h1>
              <div class="warehouse-receiving-subtitle">${escapeHtml(unavailable ? statePayload.detail || "Movement review could not be loaded. Refresh or contact an administrator." : movementSummaryText(header) || "Read-only posted movement context.")}</div>
              <div class="warehouse-movement-review-chip-row">${identityChips.map((chip) => `<span class="warehouse-inbound-chip ${chip.key === "mode" ? "is-read-only" : ""}" data-warehouse-movement-review-identity-chip="${escapeHtml(chip.key)}">${escapeHtml(chip.label)}</span>`).join("")}</div>
            </div>
            <div class="warehouse-receiving-actions">
              <button type="button" class="warehouse-receiving-button" data-warehouse-movement-review-back data-warehouse-movement-review-back-route="${escapeHtml(backTarget.route || "")}" data-warehouse-movement-review-back-queue="${escapeHtml(backTarget.queue_key || "")}">${escapeHtml(backLabel)}</button>
              <button type="button" class="warehouse-receiving-button" data-warehouse-movement-review-refresh>Refresh</button>
            </div>
          </div>
          <div class="warehouse-movement-review-command-grid" data-warehouse-movement-review-command-grid>${commandFacts.map(renderMovementReviewCommandFact).join("")}</div>
          <div class="warehouse-receiving-note"><span class="warehouse-inbound-badge">${escapeHtml(header.docstatus_label || statePayload.title || "Review")}</span> ${escapeHtml(header.direction_label || (unavailable ? "Details not visible" : ""))}</div>
          ${unavailable ? `<div class="warehouse-console-state-detail" data-warehouse-movement-review-empty>${escapeHtml(statePayload.title || "Movement review unavailable")}</div>` : ""}
        </section>
        <section class="warehouse-receiving-posture-panel warehouse-movement-review-posture-panel" data-warehouse-movement-review-summary>
          <div class="warehouse-receiving-posture-head">
            <h2 class="warehouse-receiving-posture-title">Movement posture</h2>
            <div class="warehouse-receiving-posture-note">${escapeHtml(header.direction_label || movementSummaryText(header) || "Posted movement evidence and related stock posture are shown for review only.")}</div>
          </div>
          <div class="warehouse-receiving-posture-layout">
            <div class="warehouse-receiving-posture-block warehouse-movement-review-posture-block">
              <div class="warehouse-receiving-posture-kicker">Movement evidence</div>
              <div class="warehouse-receiving-cards">${movementEvidenceCards.map(renderMovementReviewCard).join("")}</div>
            </div>
            <div class="warehouse-receiving-posture-block warehouse-movement-review-posture-block">
              <div class="warehouse-receiving-posture-kicker">Review context</div>
              <div class="warehouse-receiving-cards">${movementContextCards.length ? movementContextCards.map(renderMovementReviewCard).join("") : movementEvidenceCards.slice(-1).map(renderMovementReviewCard).join("")}</div>
            </div>
          </div>
        </section>
        <section class="warehouse-receiving-guardrail warehouse-movement-review-guardrail" data-warehouse-movement-review-guardrail>
          <strong>Review only</strong>
          <span>No stock is transferred, reconciled, adjusted, posted, reserved, picked, received, shipped, or delivered from this page.</span>
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
      loadMovementReview(viewState, viewState.contextToken, { force: true });
    });
    $root.find("[data-warehouse-movement-review-route-stock-posture], [data-warehouse-movement-review-related-row]").on("click", function (event) {
      event.preventDefault();
      const token = String(this.getAttribute("data-warehouse-stock-posture-token") || this.getAttribute("data-warehouse-movement-review-route-stock-posture") || "").trim();
      if (token) frappe.set_route(STOCK_POSTURE_PAGE_KEY, token);
    });
    replaceWarehouseRouteHost(viewState, $root);
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

  function movementReviewLoadSignature(contextToken) {
    return `movement-review:${String(contextToken || "").trim()}`;
  }

  function hasRenderedMovementReviewShell(viewState, contextToken) {
    if (!viewState || !viewState.$host || !viewState.$host.length) return false;
    const shell = viewState.$host.find('[data-warehouse-movement-review-shell="true"][data-warehouse-view="movement-review"]').get(0);
    if (!shell) return false;
    const token = String(contextToken || "").trim();
    return !token || String(shell.getAttribute("data-warehouse-movement-review-token") || "").trim() === token;
  }

  function loadMovementReview(viewState, contextToken, options) {
    const token = String(contextToken || movementTokenFromRoute() || "").trim();
    const force = Boolean(options && options.force);
    const signature = movementReviewLoadSignature(token);
    if (!force && viewState.loadingPromise && viewState.loadingSignature === signature) {
      markWarehouseDiagnostic("movementReviewDuplicateLoadReused");
      return viewState.loadingPromise;
    }
    if (!force && viewState.loadedSignature === signature && hasRenderedMovementReviewShell(viewState, token)) {
      markWarehouseDiagnostic("movementReviewDuplicateRenderSkipped");
      return Promise.resolve(viewState.lastPayload || {});
    }

    markWarehouseDiagnostic("movementReviewServiceCallAttempted");
    viewState.contextToken = token;
    const requestToken = (viewState.requestSerial || 0) + 1;
    viewState.requestSerial = requestToken;
    viewState.loadingSignature = signature;
    viewState.loadedSignature = "";
    renderMovementReviewLoading(viewState);

    const finishRequest = (payload) => {
      const currentToken = movementTokenFromRoute();
      const shouldRender = (
        viewState.requestSerial === requestToken
        && viewState.loadingSignature === signature
        && isActiveMovementRoute()
        && String(currentToken || "").trim() === token
      );
      if (viewState.requestSerial === requestToken && viewState.loadingSignature === signature) {
        viewState.loadingPromise = null;
        viewState.loadingSignature = "";
      }
      if (!shouldRender) {
        markWarehouseDiagnostic("movementReviewStaleResponseIgnored");
        return payload;
      }
      viewState.loadedSignature = signature;
      viewState.lastPayload = payload;
      renderMovementReviewPayload(viewState, payload);
      return payload;
    };

    const requestPromise = frappe.call({
      method: MOVEMENT_REVIEW_METHOD,
      args: { context: viewState.contextToken },
    }).then((response) => finishRequest(response && response.message ? response.message : {})).catch(() => finishRequest({
        state: { kind: "error", title: "Movement review unavailable", detail: "Movement review could not be loaded. Refresh or contact an administrator." },
        header: { context_token: viewState.contextToken || "" },
        summary_cards: [],
        panels: {
          direction: { title: "Movement Direction", items: [] },
          related: { title: "Related Reviews", items: [] },
        },
        line_groups: [],
        related_routes: [],
      }));
    viewState.loadingPromise = requestPromise;
    return requestPromise;
  }

  function renderMovementReview(wrapper, contextToken) {
    markWarehouseDiagnostic("renderMovementReviewEntered");
    const token = String(contextToken || movementTokenFromRoute() || "").trim();
    if (isActiveMovementRoute() && hasReadyMovementReviewShell()) {
      markWarehouseDiagnostic("movementReviewDuplicateRenderSkipped");
      return;
    }
    const viewState = makeMovementPage(wrapper);
    if (window.erpWorkspaceConsoleSidebar && typeof window.erpWorkspaceConsoleSidebar.refresh === "function") {
      window.erpWorkspaceConsoleSidebar.refresh();
    }
    loadMovementReview(viewState, token);
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
    const isInboundQueue = queueKey === INBOUND_QUEUE_KEY;
    const isOutboundQueue = queueKey === OUTBOUND_QUEUE_KEY;
    const isPremiumQueue = isInboundQueue || isOutboundQueue;
    const isLoadingState = statePayload.kind === "loading";
    const rowCount = groups.reduce((total, group) => total + (Array.isArray(group.rows) ? group.rows.length : 0), 0);
    const summaryChips = isInboundQueue
      ? [
          "Read-only",
          "Supplier-side review",
          `${rowCount} ${rowCount === 1 ? "candidate" : "candidates"}`,
          payload.fetched_at ? `Fresh ${formatWarehouseFreshness(payload.fetched_at)}` : "",
        ].filter(Boolean)
      : isOutboundQueue
        ? []
      : [];
    const inboundLoadingCards = [
      { key: "loading_due_today", label: "Receiving due today", value: "--", note: "Checking expected receipts." },
      { key: "loading_overdue", label: "Overdue receiving", value: "--", note: "Checking late supplier stock." },
      { key: "loading_partial", label: "Partially received", value: "--", note: "Checking arrived quantities." },
      { key: "loading_expected", label: "Expected soon", value: "--", note: "Checking upcoming receipts." },
    ];
    const outboundLoadingCards = [
      { key: "loading_due_today", label: "Picking due today", value: "--", note: "Checking required picks." },
      { key: "loading_overdue", label: "Overdue picking", value: "--", note: "Checking past delivery dates." },
      { key: "loading_ready", label: "Ready to pick", value: "--", note: "Checking visible stock posture." },
      { key: "loading_stock_review", label: "Needs stock review", value: "--", note: "Checking warehouse readiness." },
    ];
    const visibleCards = cards.length
      ? cards
      : (isInboundQueue && isLoadingState ? inboundLoadingCards : (isOutboundQueue && isLoadingState ? outboundLoadingCards : cards));
    const inboundLoadingControls = `
      <div class="warehouse-inbound-loading-field"><span>Purchase order</span><i></i></div>
      <div class="warehouse-inbound-loading-field"><span>Supplier</span><i></i></div>
      <div class="warehouse-inbound-loading-field"><span>Warehouse</span><i></i></div>
      <div class="warehouse-inbound-loading-field"><span>Receiving state</span><i></i></div>
      <div class="warehouse-inbound-loading-status">Checking inbound work...</div>
    `;
    const outboundLoadingControls = `
      <div class="warehouse-inbound-loading-field"><span>Sales order</span><i></i></div>
      <div class="warehouse-inbound-loading-field"><span>Customer</span><i></i></div>
      <div class="warehouse-inbound-loading-field"><span>Warehouse</span><i></i></div>
      <div class="warehouse-inbound-loading-field"><span>Picking state</span><i></i></div>
      <div class="warehouse-inbound-loading-status">Checking outbound work...</div>
    `;
    const controlsMarkup = isLoadingState && (isInboundQueue || isOutboundQueue)
      ? (isOutboundQueue ? outboundLoadingControls : inboundLoadingControls)
      : `
            ${fields.map(controlField).join("")}
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-apply>Apply</button>
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-reset>Reset</button>
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-refresh>Refresh</button>
        `;
    const $root = $(`
      <div class="sales-console-shell warehouse-inbound-shell warehouse-visual-foundation ${isOutboundQueue ? "warehouse-outbound-shell warehouse-outbound-premium-shell" : ""} ${isInboundQueue ? "warehouse-inbound-premium-shell" : ""}" data-erpw-workspace="warehouse" data-warehouse-view="${escapeHtml(viewName)}" data-warehouse-queue-key="${escapeHtml(queueKey)}" data-warehouse-visual-foundation="w13c1" data-erpw-console-runtime="ready">
        <section class="warehouse-inbound-queue-header warehouse-visual-command">
          <div class="warehouse-inbound-queue-head">
            <div class="${isPremiumQueue ? "warehouse-inbound-command" : ""}">
              ${isInboundQueue ? "" : ""}
              ${isOutboundQueue ? "" : ""}
              <h1 class="warehouse-inbound-queue-title">${escapeHtml(payload.summary && payload.summary.title || "Inbound Receiving")}</h1>
              <div class="warehouse-inbound-queue-note">${escapeHtml(payload.summary && payload.summary.subtitle || "Expected supplier stock due into warehouse.")}</div>
              ${isInboundQueue ? "" : ""}
              ${isOutboundQueue ? "" : ""}
            </div>
            ${isInboundQueue ? "" : ""}
          </div>
          <div class="warehouse-inbound-queue-cards warehouse-visual-summary-grid ${isLoadingState && (isInboundQueue || isOutboundQueue) ? "is-loading" : ""}">${visibleCards.map(renderQueueCard).join("")}</div>
          <div class="warehouse-inbound-controls warehouse-visual-filter-strip ${isLoadingState && (isInboundQueue || isOutboundQueue) ? "is-loading" : ""}">
            ${controlsMarkup}
          </div>
          ${isInboundQueue ? "" : ""}
          ${isOutboundQueue ? "" : ""}
        </section>
        <div class="warehouse-inbound-groups">
          ${statePayload.kind === "restricted" || statePayload.kind === "error"
            ? `<section class="warehouse-inbound-group warehouse-visual-fallback" data-warehouse-inbound-group="state" data-warehouse-outbound-group="state"><h2 class="warehouse-inbound-group-title">${escapeHtml(statePayload.title || "Warehouse worklist unavailable")}</h2><div class="warehouse-inbound-meta" data-warehouse-inbound-empty data-warehouse-outbound-empty>${escapeHtml(statePayload.detail || "Warehouse work could not be loaded. Refresh or contact an administrator.")}</div></section>`
            : groups.map((group) => renderQueueGroup(group, queueKey)).join("")}
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
    replaceWarehouseRouteHost(viewState, $root);
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
    const explicitQueueKey = normalizeQueueKey(queueKey || "");
    const resolvedQueueKey = explicitQueueKey || activeWorklistQueueKey();
    if (!isSupportedWorklistQueue(resolvedQueueKey)) return;
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
