/* global frappe */

(function () {
  const workspaceRegistry = window.erpWorkspaceUiWorkspaceRegistry || {};
  const warehouseWorkspace = typeof workspaceRegistry.warehouse === "function" ? workspaceRegistry.warehouse() : null;
  const warehouseRoutes = warehouseWorkspace && warehouseWorkspace.routes ? warehouseWorkspace.routes : {};
  const PAGE_KEY = warehouseRoutes.stockException || warehouseRoutes.stock_exception || "warehouse-console-stock-exception";
  const ASSET = "/assets/erp_workspace_ui/js/warehouse_console/warehouse_console_page.js";
  let renderSerial = 0;

  function routePartsFromPath() {
    const path = String((window.location && window.location.pathname) || "").replace(/^\/+/, "");
    const parts = path.split("/").filter(Boolean);
    return parts[0] === "desk" || parts[0] === "app" ? parts.slice(1) : parts;
  }

  function isActiveStockExceptionRoute() {
    const pathRoute = routePartsFromPath();
    if (String(pathRoute[0] || "") === PAGE_KEY) return true;
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) && String(route[0] || "") === PAGE_KEY;
  }

  function currentContextToken() {
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
    if (pageDef && typeof pageDef.__erpwRenderWarehouseStockExceptionReview === "function") {
      return pageDef.__erpwRenderWarehouseStockExceptionReview;
    }
    const api = window.erpWorkspaceWarehouseConsole || {};
    if (typeof api.renderStockExceptionReview === "function") return api.renderStockExceptionReview;
    return null;
  }

  function invokeRenderer(wrapper) {
    const renderStockExceptionReview = resolveRenderer();
    if (typeof renderStockExceptionReview !== "function") return false;
    renderStockExceptionReview(currentWrapper(wrapper), currentContextToken());
    return true;
  }

  function ensureAndRender(wrapper) {
    const token = ++renderSerial;
    frappe.require([ASSET], () => {
      const attempt = () => {
        const shell = document.querySelector('.warehouse-stock-exception-review-shell[data-warehouse-view="stock-exception-review"]');
        if (token !== renderSerial && shell) return true;
        return invokeRenderer(wrapper);
      };
      attempt();
      window.setTimeout(attempt, 80);
      window.setTimeout(attempt, 220);
    });
  }

  const pageDef = frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  pageDef.__erpwWarehouseStockExceptionPageWrapper = true;
  pageDef.on_page_load = ensureAndRender;
  pageDef.on_page_show = ensureAndRender;

  window.setTimeout(() => {
    if (isActiveStockExceptionRoute()) ensureAndRender(currentWrapper());
  }, 0);
  window.setTimeout(() => {
    if (isActiveStockExceptionRoute()) ensureAndRender(currentWrapper());
  }, 180);
})();
