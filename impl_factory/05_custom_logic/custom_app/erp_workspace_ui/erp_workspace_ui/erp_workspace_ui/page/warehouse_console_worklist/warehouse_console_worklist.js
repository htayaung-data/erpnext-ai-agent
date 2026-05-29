/* global frappe */

(function () {
  const workspaceRegistry = window.erpWorkspaceUiWorkspaceRegistry || {};
  const warehouseWorkspace = typeof workspaceRegistry.warehouse === "function" ? workspaceRegistry.warehouse() : null;
  const warehouseRoutes = warehouseWorkspace && warehouseWorkspace.routes ? warehouseWorkspace.routes : {};
  const PAGE_KEY = warehouseRoutes.worklist || "warehouse-console-worklist";
  const ASSET = "/assets/erp_workspace_ui/js/warehouse_console/warehouse_console_page.js";
  let renderSerial = 0;

  function routePartsFromPath() {
    const path = String((window.location && window.location.pathname) || "").replace(/^\/+/, "");
    const parts = path.split("/").filter(Boolean);
    return parts[0] === "desk" || parts[0] === "app" ? parts.slice(1) : parts;
  }

  function normalizeQueueKey(value) {
    return String(value || "").trim().replace(/-/g, "_");
  }

  function activeQueueKey() {
    const pathRoute = routePartsFromPath();
    if (String(pathRoute[0] || "") === PAGE_KEY) return normalizeQueueKey(pathRoute[1] || "inbound_receiving");
    const route = frappe.get_route ? frappe.get_route() : [];
    if (Array.isArray(route) && String(route[0] || "") === PAGE_KEY) return normalizeQueueKey(route[1] || "inbound_receiving");
    return "inbound_receiving";
  }

  function activeViewName() {
    const key = activeQueueKey();
    if (key === "outbound_picking") return "outbound-picking";
    if (key === "stock_exceptions") return "stock-exceptions";
    return "inbound-receiving";
  }

  function isActiveWorklistRoute() {
    const pathRoute = routePartsFromPath();
    if (String(pathRoute[0] || "") === PAGE_KEY) return true;
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) && String(route[0] || "") === PAGE_KEY;
  }

  function currentWrapper(fallback) {
    return fallback || document.getElementById("body") || (frappe.container && frappe.container.page && frappe.container.page.wrapper);
  }

  function resolveRenderer() {
    const pageDef = frappe.pages && frappe.pages[PAGE_KEY] ? frappe.pages[PAGE_KEY] : null;
    if (pageDef && typeof pageDef.__erpwRenderWarehouseWorklist === "function") {
      return pageDef.__erpwRenderWarehouseWorklist;
    }
    if (pageDef && typeof pageDef.__erpwRenderWarehouseInboundQueue === "function") {
      return pageDef.__erpwRenderWarehouseInboundQueue;
    }
    const api = window.erpWorkspaceWarehouseConsole || {};
    if (typeof api.renderWarehouseWorklist === "function") return api.renderWarehouseWorklist;
    if (typeof api.renderInboundQueue === "function") return api.renderInboundQueue;
    return null;
  }

  function invokeRenderer(wrapper) {
    const renderInboundQueue = resolveRenderer();
    if (typeof renderInboundQueue !== "function") return false;
    renderInboundQueue(currentWrapper(wrapper));
    return true;
  }

  function ensureAndRender(wrapper) {
    const token = ++renderSerial;
    frappe.require([ASSET], () => {
      const attempt = () => {
        const shell = document.querySelector(`.sales-console-shell[data-erpw-workspace="warehouse"][data-warehouse-view="${activeViewName()}"]`);
        if (token !== renderSerial && shell) return true;
        return invokeRenderer(wrapper);
      };
      attempt();
      window.setTimeout(attempt, 80);
      window.setTimeout(attempt, 220);
    });
  }

  const pageDef = frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  pageDef.__erpwWarehouseInboundPageWrapper = true;
  pageDef.on_page_load = ensureAndRender;
  pageDef.on_page_show = ensureAndRender;

  window.setTimeout(() => {
    if (isActiveWorklistRoute()) ensureAndRender(currentWrapper());
  }, 0);
  window.setTimeout(() => {
    if (isActiveWorklistRoute()) ensureAndRender(currentWrapper());
  }, 180);
})();
