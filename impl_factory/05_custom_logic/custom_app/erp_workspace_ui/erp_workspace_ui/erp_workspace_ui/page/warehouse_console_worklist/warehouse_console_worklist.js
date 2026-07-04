/* global frappe */

(function () {
  const workspaceRegistry = window.erpWorkspaceUiWorkspaceRegistry || {};
  const warehouseWorkspace = typeof workspaceRegistry.warehouse === "function" ? workspaceRegistry.warehouse() : null;
  const warehouseRoutes = warehouseWorkspace && warehouseWorkspace.routes ? warehouseWorkspace.routes : {};
  const PAGE_KEY = warehouseRoutes.worklist || "warehouse-console-worklist";
  const ASSET = "/assets/erp_workspace_ui/js/warehouse_console/warehouse_console_page.js";
  let renderSerial = 0;
  let routeGuardBound = false;

  const VIEW_TITLES = {
    "inbound-receiving": "Inbound Receiving",
    "outbound-picking": "Outbound Picking",
    "stock-exceptions": "Stock Exceptions",
    "movement-visibility": "Movement Visibility",
    "transfer-visibility": "Transfer Visibility",
    "returns-work-hub": "Returns",
    "internal-transfer-workflow": "Internal Transfer",
    "cycle-count-workflow": "Cycle Count",
    "unsupported-worklist": "Warehouse worklist",
  };

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
    if (key === "movement_visibility") return "movement-visibility";
    if (key === "transfer_visibility") return "transfer-visibility";
    if (key === "returns_work_hub") return "returns-work-hub";
    if (key === "internal_transfer_workflow") return "internal-transfer-workflow";
    if (key === "cycle_count_workflow") return "cycle-count-workflow";
    if (!key || key === "inbound_receiving") return "inbound-receiving";
    return "unsupported-worklist";
  }

  function isActiveWorklistRoute() {
    const pathRoute = routePartsFromPath();
    if (String(pathRoute[0] || "") === PAGE_KEY) return true;
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) && String(route[0] || "") === PAGE_KEY;
  }

  function currentWrapper(fallback) {
    return fallback || (frappe.container && frappe.container.page && frappe.container.page.wrapper) || document.getElementById("body");
  }

  function safeViewAttr(value) {
    return String(value || "warehouse").replace(/[^a-z0-9_-]+/gi, "-").toLowerCase();
  }

  function renderRouteLoadingShell(wrapper, viewName) {
    const target = currentWrapper(wrapper);
    if (!target || !target.querySelector) return;
    if (target === document.body || target.id === "body") return;
    const safeView = safeViewAttr(viewName);
    const finalShell = target.querySelector(`.sales-console-shell[data-erpw-workspace="warehouse"][data-warehouse-view="${safeView}"]`);
    if (finalShell) return;
    const existing = target.querySelector("[data-warehouse-route-loading]");
    if (existing && existing.getAttribute("data-warehouse-route-loading") === safeView) return;
    const title = VIEW_TITLES[safeView] || "Warehouse Console";
    target.innerHTML = `
      <section data-warehouse-route-loading="${safeView}" style="box-sizing:border-box;max-width:1120px;margin:0 auto;padding:26px 28px;">
        <div style="border:1px solid #dbe7ef;border-radius:22px;background:#fff;box-shadow:0 18px 48px rgba(15,38,64,.06);padding:24px 26px;">
          <div style="font-size:22px;font-weight:760;letter-spacing:-.03em;color:#061529;margin-bottom:8px;">${title}</div>
          <div style="font-size:13px;line-height:1.5;color:#48607a;">Loading Warehouse workspace...</div>
        </div>
      </section>
    `;
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
    const wrapperEl = currentWrapper(wrapper);
    renderRouteLoadingShell(wrapperEl, activeViewName());
    frappe.require([ASSET], () => {
      const attempt = () => {
        const shell = document.querySelector(`.sales-console-shell[data-erpw-workspace="warehouse"][data-warehouse-view="${activeViewName()}"]`);
        if (shell) return true;
        if (token !== renderSerial) return true;
        return invokeRenderer(wrapperEl);
      };
      attempt();
      if (window.requestAnimationFrame) window.requestAnimationFrame(attempt);
      window.setTimeout(attempt, 80);
      window.setTimeout(attempt, 220);
      window.setTimeout(attempt, 700);
      window.setTimeout(attempt, 1200);
    });
  }

  function scheduleActiveRender(wrapper) {
    if (!isActiveWorklistRoute()) return;
    ensureAndRender(currentWrapper(wrapper));
  }

  function bindRouteGuard() {
    if (routeGuardBound) return;
    routeGuardBound = true;
    const schedule = () => {
      window.setTimeout(() => scheduleActiveRender(currentWrapper()), 0);
      window.setTimeout(() => scheduleActiveRender(currentWrapper()), 180);
      window.setTimeout(() => scheduleActiveRender(currentWrapper()), 700);
    };
    if (frappe.router && typeof frappe.router.on === "function" && !frappe.router.erpwWarehouseWorklistPageGuardBound) {
      frappe.router.erpwWarehouseWorklistPageGuardBound = true;
      frappe.router.on("change", () => {
        if (frappe.after_ajax && typeof frappe.after_ajax === "function") {
          frappe.after_ajax(schedule);
          return;
        }
        schedule();
      });
    }
    window.addEventListener("hashchange", schedule);
    window.addEventListener("popstate", schedule);
  }

  const pageDef = frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  pageDef.__erpwWarehouseInboundPageWrapper = true;
  pageDef.on_page_load = ensureAndRender;
  pageDef.on_page_show = ensureAndRender;
  bindRouteGuard();

  window.setTimeout(() => {
    scheduleActiveRender(currentWrapper());
  }, 0);
  window.setTimeout(() => {
    scheduleActiveRender(currentWrapper());
  }, 180);
  window.setTimeout(() => {
    scheduleActiveRender(currentWrapper());
  }, 700);
})();
