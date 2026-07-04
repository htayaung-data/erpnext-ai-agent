/* global frappe */

(function () {
  const workspaceRegistry = window.erpWorkspaceUiWorkspaceRegistry || {};
  const warehouseWorkspace = typeof workspaceRegistry.warehouse === "function" ? workspaceRegistry.warehouse() : null;
  const warehouseRoutes = warehouseWorkspace && warehouseWorkspace.routes ? warehouseWorkspace.routes : {};
  const PAGE_KEY = warehouseRoutes.receiving || "warehouse-console-receiving";
  const ASSET = "/assets/erp_workspace_ui/js/warehouse_console/warehouse_console_page.js";
  const THEME_PATCH_ASSET = "/assets/erp_workspace_ui/js/warehouse_console/warehouse_console_theme_patch.js";
  let renderSerial = 0;

  function routePartsFromPath() {
    const path = String((window.location && window.location.pathname) || "").replace(/^\/+/, "");
    const parts = path.split("/").filter(Boolean);
    return parts[0] === "desk" || parts[0] === "app" ? parts.slice(1) : parts;
  }

  function isActiveReceivingRoute() {
    const pathRoute = routePartsFromPath();
    if (String(pathRoute[0] || "") === PAGE_KEY) return true;
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) && String(route[0] || "") === PAGE_KEY;
  }

  function currentPurchaseOrder() {
    const pathRoute = routePartsFromPath();
    if (String(pathRoute[0] || "") === PAGE_KEY) return String(pathRoute[1] || "");
    const route = frappe.get_route ? frappe.get_route() : [];
    if (Array.isArray(route) && String(route[0] || "") === PAGE_KEY) return String(route[1] || "");
    return "";
  }

  function currentWrapper(fallback) {
    return fallback || (frappe.container && frappe.container.page && frappe.container.page.wrapper) || document.getElementById("body");
  }

  function renderRouteLoadingShell(wrapper) {
    const target = currentWrapper(wrapper);
    if (!target || !target.querySelector) return;
    if (target === document.body || target.id === "body") return;
    if (target.querySelector('.warehouse-receiving-shell[data-warehouse-view="receiving-review"]')) return;
    if (target.querySelector('[data-warehouse-route-loading="receiving-review"]')) return;
    const recordId = String(currentPurchaseOrder() || "").trim();
    const recordLine = recordId ? `Checking ${recordId}...` : "Loading Warehouse workflow...";
    target.innerHTML = `
      <section data-warehouse-route-loading="receiving-review" style="box-sizing:border-box;max-width:1120px;margin:0 auto;padding:26px 28px;">
        <div style="border:1px solid #dbe7ef;border-radius:22px;background:#fff;box-shadow:0 18px 48px rgba(15,38,64,.06);padding:24px 26px;">
          <div style="font-size:22px;font-weight:760;letter-spacing:-.03em;color:#061529;margin-bottom:8px;">Receiving Review</div>
          <div style="font-size:13px;line-height:1.5;color:#48607a;">${recordLine}</div>
        </div>
      </section>
    `;
  }

  function resolveRenderer() {
    const pageDef = frappe.pages && frappe.pages[PAGE_KEY] ? frappe.pages[PAGE_KEY] : null;
    if (pageDef && typeof pageDef.__erpwRenderWarehouseReceivingReview === "function") {
      return pageDef.__erpwRenderWarehouseReceivingReview;
    }
    const api = window.erpWorkspaceWarehouseConsole || {};
    if (typeof api.renderReceivingReview === "function") return api.renderReceivingReview;
    return null;
  }

  function invokeRenderer(wrapper) {
    const renderReceivingReview = resolveRenderer();
    if (typeof renderReceivingReview !== "function") return false;
    renderReceivingReview(currentWrapper(wrapper), currentPurchaseOrder());
    return true;
  }

  function ensureAndRender(wrapper) {
    const token = ++renderSerial;
    const wrapperEl = currentWrapper(wrapper);
    renderRouteLoadingShell(wrapperEl);
    frappe.require([ASSET], () => {
      const attempt = () => {
        const shell = document.querySelector('.warehouse-receiving-shell[data-warehouse-view="receiving-review"]');
        if (token !== renderSerial && shell) return true;
        return invokeRenderer(wrapperEl);
      };
      attempt();
      frappe.require([THEME_PATCH_ASSET], () => {
        if (window.erpWorkspaceWarehouseConsoleThemePatch) window.erpWorkspaceWarehouseConsoleThemePatch();
      });
      window.setTimeout(() => {
        attempt();
        if (window.erpWorkspaceWarehouseConsoleThemePatch) window.erpWorkspaceWarehouseConsoleThemePatch();
      }, 80);
      window.setTimeout(() => {
        attempt();
        if (window.erpWorkspaceWarehouseConsoleThemePatch) window.erpWorkspaceWarehouseConsoleThemePatch();
      }, 220);
    });
  }

  const pageDef = frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  pageDef.__erpwWarehouseReceivingPageWrapper = true;
  pageDef.on_page_load = ensureAndRender;
  pageDef.on_page_show = ensureAndRender;

  window.setTimeout(() => {
    if (isActiveReceivingRoute()) ensureAndRender(currentWrapper());
  }, 0);
  window.setTimeout(() => {
    if (isActiveReceivingRoute()) ensureAndRender(currentWrapper());
  }, 180);
})();
