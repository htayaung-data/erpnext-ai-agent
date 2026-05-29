/* global frappe */

(function () {
  const workspaceRegistry = window.erpWorkspaceUiWorkspaceRegistry || {};
  const warehouseWorkspace = typeof workspaceRegistry.warehouse === "function" ? workspaceRegistry.warehouse() : null;
  const warehouseRoutes = warehouseWorkspace && warehouseWorkspace.routes ? warehouseWorkspace.routes : {};
  const PAGE_KEY = warehouseRoutes.picking || "warehouse-console-picking";
  const ASSET = "/assets/erp_workspace_ui/js/warehouse_console/warehouse_console_page.js";
  let renderSerial = 0;

  function routePartsFromPath() {
    const path = String((window.location && window.location.pathname) || "").replace(/^\/+/, "");
    const parts = path.split("/").filter(Boolean);
    return parts[0] === "desk" || parts[0] === "app" ? parts.slice(1) : parts;
  }

  function isActivePickingRoute() {
    const pathRoute = routePartsFromPath();
    if (String(pathRoute[0] || "") === PAGE_KEY) return true;
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) && String(route[0] || "") === PAGE_KEY;
  }

  function currentSalesOrder() {
    const pathRoute = routePartsFromPath();
    if (String(pathRoute[0] || "") === PAGE_KEY) return String(pathRoute[1] || "");
    const route = frappe.get_route ? frappe.get_route() : [];
    if (Array.isArray(route) && String(route[0] || "") === PAGE_KEY) return String(route[1] || "");
    return "";
  }

  function currentWrapper(fallback) {
    return fallback || document.getElementById("body") || (frappe.container && frappe.container.page && frappe.container.page.wrapper);
  }

  function resolveRenderer() {
    const pageDef = frappe.pages && frappe.pages[PAGE_KEY] ? frappe.pages[PAGE_KEY] : null;
    if (pageDef && typeof pageDef.__erpwRenderWarehousePickingReview === "function") {
      return pageDef.__erpwRenderWarehousePickingReview;
    }
    const api = window.erpWorkspaceWarehouseConsole || {};
    if (typeof api.renderPickingReview === "function") return api.renderPickingReview;
    return null;
  }

  function invokeRenderer(wrapper) {
    const renderPickingReview = resolveRenderer();
    if (typeof renderPickingReview !== "function") return false;
    renderPickingReview(currentWrapper(wrapper), currentSalesOrder());
    return true;
  }

  function ensureAndRender(wrapper) {
    const token = ++renderSerial;
    frappe.require([ASSET], () => {
      const attempt = () => {
        const shell = document.querySelector('.warehouse-picking-shell[data-warehouse-view="picking-review"]');
        if (token !== renderSerial && shell) return true;
        return invokeRenderer(wrapper);
      };
      attempt();
      window.setTimeout(attempt, 80);
      window.setTimeout(attempt, 220);
    });
  }

  const pageDef = frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  pageDef.__erpwWarehousePickingPageWrapper = true;
  pageDef.on_page_load = ensureAndRender;
  pageDef.on_page_show = ensureAndRender;

  window.setTimeout(() => {
    if (isActivePickingRoute()) ensureAndRender(currentWrapper());
  }, 0);
  window.setTimeout(() => {
    if (isActivePickingRoute()) ensureAndRender(currentWrapper());
  }, 180);
})();
