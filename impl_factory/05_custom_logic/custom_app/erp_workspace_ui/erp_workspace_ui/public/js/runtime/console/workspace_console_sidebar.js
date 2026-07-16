/* global frappe */

(function () {
  const root = typeof window !== "undefined" ? window : globalThis;
  const consoleRuntime = root.erpWorkspaceConsoleRuntime || {};
  const sidebarRuntime = root.erpWorkspaceConsoleSidebar = root.erpWorkspaceConsoleSidebar || {};
  function currentWorkspaceRegistry() {
    return root.erpWorkspaceUiWorkspaceRegistry || {};
  }

  function workspaceFromRegistry(workspaceId) {
    const key = String(workspaceId || "").trim();
    if (!key) return null;
    const registry = currentWorkspaceRegistry();
    if (typeof registry.get === "function") {
      const workspace = registry.get(key);
      if (workspace) return workspace;
    }
    if (typeof registry[key] === "function") {
      const workspace = registry[key]();
      if (workspace) return workspace;
    }
    return null;
  }

  function workspaceFromRouteKey(routeKey) {
    const normalized = String(routeKey || "").trim();
    if (!normalized) return null;
    const registry = currentWorkspaceRegistry();
    if (typeof registry.getByRoute === "function") {
      const workspace = registry.getByRoute(normalized);
      if (workspace) return workspace;
    }
    return null;
  }

  function configuredWorkspaces() {
    return [workspaceFromRegistry("sales"), workspaceFromRegistry("procurement"), workspaceFromRegistry("warehouse"), workspaceFromRegistry("finance")].filter(Boolean);
  }

  function defaultWorkspaceForSidebar() {
    return workspaceFromRegistry("sales") || workspaceFromRegistry("procurement") || null;
  }

  const salesWorkspace = workspaceFromRegistry("sales");
  const salesRoutes = salesWorkspace && salesWorkspace.routes ? salesWorkspace.routes : {};
  const salesMethods = salesWorkspace && salesWorkspace.methods ? salesWorkspace.methods : {};
  const SIDEBAR_CONTEXT_SCHEMA_VERSION = "workspace-sidebar.v1";
  const MANAGED_SEARCH_SCHEMA_VERSION = "workspace-search.v1";
  const STYLE_ID = "erpw-sales-console-sidebar-style";
  const SIDEBAR_METHOD = salesMethods.sidebarContext || "erp_workspace_ui.sales_console.service.get_sales_console_sidebar_context";
  const SEARCH_METHOD = salesMethods.workspaceSearch || "erp_workspace_ui.sales_console.service.search_sales_console_workspace";
  const HOME_ROUTE = salesRoutes.home || "sales-console";
  const WORKLIST_ROUTE = salesRoutes.worklist || "sales-console-worklist";
  const REPORT_ROUTE = salesRoutes.report || "sales-console-report";
  const HOME_PATH = salesRoutes.homePath || `/desk/${HOME_ROUTE}`;
  const WORKSPACE_TITLE = (salesWorkspace && salesWorkspace.title) || "Sales Console";
  const WORKSPACE_MODE_LABEL = (salesWorkspace && salesWorkspace.modeLabel) || "Sales Workspace";
  const MANAGED_BODY_CLASS = "erpw-sales-console-sidebar-managed";
  const MANAGED_FORM_ACTIVE_KEYS = Object.assign({
    "Quotation": "quotation_directory",
    "Sales Order": "sales_order_directory",
    "Customer": "customer_directory",
    "Item": "item_directory",
    "Delivery Note": "sales_order_directory",
    "Sales Invoice": "sales_order_directory",
  }, (salesWorkspace && salesWorkspace.managedDoctypes) || {});
  const SALES_FORM_DOCTYPES = new Set(["Quotation", "Sales Order", "Customer", "Item", "Delivery Note", "Sales Invoice"]);
  const PROCUREMENT_FORM_DOCTYPES = new Set([
    "Supplier",
    "Supplier Group",
    "Item Supplier",
    "Item Price",
    "Material Request",
    "Request for Quotation",
    "Supplier Quotation",
    "Purchase Order",
    "Purchase Receipt",
    "Purchase Invoice",
  ]);
  const PROCUREMENT_SEARCH_LABELS = Object.freeze({
    "Supplier": { group: "Suppliers", badge: "Supplier" },
    "Item": { group: "Buying Items", badge: "Item" },
    "Material Request": { group: "Purchase Requests", badge: "Request" },
    "Request for Quotation": { group: "RFQs", badge: "RFQ" },
    "Supplier Quotation": { group: "Supplier Quotations", badge: "Quotation" },
    "Purchase Order": { group: "Purchase Orders", badge: "Order" },
    "Report": { group: "Reports", badge: "Report" },
    suppliers: { group: "Suppliers", badge: "Supplier" },
    buying_items: { group: "Buying Items", badge: "Item" },
    purchase_requests: { group: "Purchase Requests", badge: "Request" },
    rfqs: { group: "RFQs", badge: "RFQ" },
    supplier_quotations: { group: "Supplier Quotations", badge: "Quotation" },
    purchase_orders: { group: "Purchase Orders", badge: "Order" },
    reports: { group: "Reports", badge: "Report" },
  });
  const SLUG_FORM_DOCTYPES = {
    quotation: "Quotation",
    "sales-order": "Sales Order",
    sales_order: "Sales Order",
    customer: "Customer",
    item: "Item",
    "delivery-note": "Delivery Note",
    delivery_note: "Delivery Note",
    "sales-invoice": "Sales Invoice",
    sales_invoice: "Sales Invoice",
    supplier: "Supplier",
    "material-request": "Material Request",
    material_request: "Material Request",
    "request-for-quotation": "Request for Quotation",
    request_for_quotation: "Request for Quotation",
    "supplier-quotation": "Supplier Quotation",
    supplier_quotation: "Supplier Quotation",
    "purchase-order": "Purchase Order",
    purchase_order: "Purchase Order",
  };

  function workspaceId(workspace) {
    return String((workspace && (workspace.workspaceId || workspace.workspace_id)) || "sales");
  }

  function routeDoctype(route) {
    if (!Array.isArray(route) || !route.length) return "";
    const pageKey = String(route[0] || "");
    if (pageKey === "Form") return String(route[1] || "");
    return SLUG_FORM_DOCTYPES[pageKey] || "";
  }

  function inferredWorkspaceId(route) {
    const pageKey = Array.isArray(route) ? String(route[0] || "") : "";
    if (pageKey.indexOf("procurement-console") === 0) return "procurement";
    if (pageKey.indexOf("warehouse-console") === 0) return "warehouse";
    if (pageKey.indexOf("finance-control-desk") === 0) return "finance";
    if (pageKey.indexOf("sales-console") === 0) return "sales";
    const doctype = routeDoctype(route);
    if (PROCUREMENT_FORM_DOCTYPES.has(doctype)) return "procurement";
    if (SALES_FORM_DOCTYPES.has(doctype)) return "sales";
    return "";
  }

  function workspaceForRoute(route) {
    const pageKey = Array.isArray(route) ? String(route[0] || "") : "";
    const routedWorkspace = workspaceFromRouteKey(pageKey);
    if (routedWorkspace) return routedWorkspace;

    const inferredId = inferredWorkspaceId(route);
    if (inferredId) return workspaceFromRegistry(inferredId) || { workspaceId: inferredId };

    const doctype = routeDoctype(route);
    if (doctype) {
      const matched = configuredWorkspaces().find((workspace) => workspace && workspace.managedDoctypes && workspace.managedDoctypes[doctype]);
      if (matched) return matched;
    }
    return defaultWorkspaceForSidebar();
  }

  function procurementSearchLabel(item, config, type) {
    if (!config || config.workspaceId !== "procurement") return "";
    const groupKey = String((item && item.group_key) || "").trim();
    const doctype = String((item && item.doctype) || "").trim();
    const labels = PROCUREMENT_SEARCH_LABELS[groupKey] || PROCUREMENT_SEARCH_LABELS[doctype];
    return labels && labels[type] ? labels[type] : "";
  }

  function workspaceConfig(route) {
    const workspace = workspaceForRoute(route) || defaultWorkspaceForSidebar() || {};
    const routes = workspace.routes || {};
    const methods = workspace.methods || {};
    const sidebar = workspace.sidebar || {};
    const id = workspaceId(workspace);
    const fallbackTitle = id === "procurement" ? "Procurement Console" : id === "warehouse" ? "Warehouse Console" : id === "finance" ? "Finance Control Desk" : WORKSPACE_TITLE;
    const fallbackMode = id === "procurement" ? "Procurement Workspace" : id === "warehouse" ? "Warehouse Workspace" : id === "finance" ? "Finance & Accounting Workspace" : WORKSPACE_MODE_LABEL;
    const fallbackHome = id === "procurement" ? "procurement-console" : id === "warehouse" ? "warehouse-console" : id === "finance" ? "finance-control-desk" : HOME_ROUTE;
    return {
      workspace,
      workspaceId: id,
      title: workspace.title || fallbackTitle,
      modeLabel: workspace.modeLabel || fallbackMode,
      routes,
      sidebar,
      search: workspace.search || {},
      fallbackItems: Array.isArray(workspace.fallbackItems) ? workspace.fallbackItems : [],
      homeRoute: routes.home || fallbackHome,
      launcherRoute: routes.launcher || routes.home || (id === "procurement" ? "procurement-console-home" : id === "finance" ? "finance-control-desk" : salesRoutes.launcher || "sales-console-home"),
      worklistRoute: routes.worklist || (id === "procurement" ? "procurement-console-worklist" : id === "sales" ? WORKLIST_ROUTE : ""),
      reportRoute: routes.report || (id === "procurement" ? "procurement-console-report" : id === "sales" ? REPORT_ROUTE : ""),
      homePath: routes.homePath || routes.home_path || `/desk/${routes.home || fallbackHome}`,
      sidebarContextMethod: methods.sidebarContext || methods.sidebar_context || (id === "procurement" ? "erp_workspace_ui.procurement_console.service.get_procurement_console_sidebar_context" : id === "warehouse" ? "erp_workspace_ui.warehouse_console.service.get_warehouse_console_sidebar_context" : id === "finance" ? "erp_workspace_ui.finance_accounting.service.get_finance_control_desk_sidebar_context" : SIDEBAR_METHOD),
      searchMethod: methods.workspaceSearch || methods.workspace_search || (id === "procurement" ? "erp_workspace_ui.procurement_console.service.search_procurement_console_workspace" : id === "finance" ? "erp_workspace_ui.finance_accounting.service.search_finance_control_desk_workspace" : SEARCH_METHOD),
      managedFormActiveKeys: Object.assign({}, workspace.managedDoctypes || {}),
    };
  }

  function createWorkspaceContextCoordinator() {
    const states = new Map();
    let serial = 0;

    function stateFor(workspaceKey) {
      const key = String(workspaceKey || "").trim();
      if (!states.has(key)) states.set(key, { payload: null, promise: null, token: 0 });
      return states.get(key);
    }

    function prime(workspaceKey, payload) {
      const state = stateFor(workspaceKey);
      state.token = ++serial;
      state.payload = payload;
      state.promise = null;
      return payload;
    }

    function peek(workspaceKey) {
      return stateFor(workspaceKey).payload;
    }

    function clear(workspaceKey) {
      const key = String(workspaceKey || "").trim();
      const selected = key ? [states.get(key)].filter(Boolean) : Array.from(states.values());
      selected.forEach((state) => {
        state.token = ++serial;
        state.payload = null;
        state.promise = null;
      });
      if (key) states.delete(key);
      else states.clear();
    }

    function load(workspaceKey, requestFactory, fallbackFactory) {
      const state = stateFor(workspaceKey);
      if (state.payload) return Promise.resolve(state.payload);
      if (state.promise) return state.promise;
      const token = ++serial;
      state.token = token;
      const promise = Promise.resolve().then(requestFactory).then((payload) => {
        if (state.token !== token) return state.payload;
        state.payload = payload;
        return payload;
      }).catch(() => {
        if (state.token !== token) return state.payload;
        state.payload = fallbackFactory();
        return state.payload;
      }).finally(() => {
        if (state.token === token) state.promise = null;
      });
      state.promise = promise;
      return promise;
    }

    return Object.freeze({ clear, load, peek, prime });
  }

  const contextCoordinator = createWorkspaceContextCoordinator();
  let syncTimer = null;
  let mutationSyncTimer = null;
  let sidebarMutationObserver = null;
  let listenersBound = false;
  let searchDialog = null;
  let searchTimer = null;
  let searchRequestToken = 0;
  let searchNormalizedQuery = "";
  let searchResults = [];
  let activeSearchEnvelope = null;
  const searchGenerationCoordinator = createManagedSearchGenerationCoordinator();
  let searchActiveIndex = -1;
  let searchReturnFocus = null;
  let searchRestoreFocusOnClose = false;

  function escapeHtml(value) {
    if (typeof consoleRuntime.escapeHtml === "function") {
      return consoleRuntime.escapeHtml(value);
    }
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function sidebarIconMarkup(name) {
    const icons = {
      report: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M6 4.5h12v15H6z"></path>
          <path d="M9 9h6"></path>
          <path d="M9 12.5h6"></path>
          <path d="M9 16h3"></path>
        </svg>
      `,
      return: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M9 7H5v4"></path>
          <path d="M5 11a7 7 0 1 0 2.1-5"></path>
        </svg>
      `,
      stock: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M12 3l7 4-7 4-7-4 7-4z"></path>
          <path d="M5 7v6l7 4 7-4V7"></path>
          <path d="M8 17.5h8"></path>
          <path d="M16 15.5l2 2-2 2"></path>
        </svg>
      `,
    };
    return icons[name] || "";
  }

  function iconMarkup(name) {
    const localIcon = sidebarIconMarkup(name);
    if (localIcon) return localIcon;
    if (typeof consoleRuntime.iconMarkup === "function") {
      return consoleRuntime.iconMarkup(name);
    }
    return "";
  }

  function sidebarItemIconMarkup(item) {
    const key = String(item && item.key || "");
    const iconsByKey = {
      stock_exceptions: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M12 4.5l8 15H4z"></path>
          <path d="M12 9v4.3"></path>
          <path d="M12 17h.01"></path>
        </svg>
      `,
      returns_work_hub: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M9 7H5v4"></path>
          <path d="M5 11a7 7 0 1 0 2.1-5"></path>
        </svg>
      `,
      internal_transfer_workflow: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M7 7h10"></path>
          <path d="M14 4l3 3-3 3"></path>
          <path d="M17 17H7"></path>
          <path d="M10 14l-3 3 3 3"></path>
        </svg>
      `,
      cycle_count_workflow: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M18.5 8.5A7 7 0 1 0 20 13"></path>
          <path d="M18.5 4.5v4h-4"></path>
          <path d="M8.5 12.5l2.1 2.1 4.4-5"></path>
        </svg>
      `,
      movement_visibility: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M4 17c3.2-6.5 7.8 2.5 16-7"></path>
          <path d="M16 10h4v4"></path>
          <path d="M5 7h4"></path>
        </svg>
      `,
      transfer_visibility: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M6 8h12"></path>
          <path d="M15 5l3 3-3 3"></path>
          <path d="M18 16H6"></path>
          <path d="M9 13l-3 3 3 3"></path>
        </svg>
      `,
    };
    return iconsByKey[key] || iconMarkup(item && item.icon || "square");
  }

  function ensureStyles() {
    if (document.getElementById(STYLE_ID)) return;

    const style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = `
      .erpw-sales-console-sidebar-nav {
        margin-top: 8px;
      }
      .${MANAGED_BODY_CLASS} .body-sidebar {
        container-type: inline-size;
      }
      .${MANAGED_BODY_CLASS} .body-sidebar .item-anchor,
      .${MANAGED_BODY_CLASS} .body-sidebar .collapse-sidebar-link,
      .${MANAGED_BODY_CLASS} .body-sidebar button {
        cursor: pointer;
        user-select: none;
      }
      .${MANAGED_BODY_CLASS} .body-sidebar .erpw-sales-console-sidebar-header .drop-icon {
        display: none !important;
        pointer-events: none !important;
      }
      .${MANAGED_BODY_CLASS} .body-sidebar .navbar-search-bar {
        display: none !important;
      }
      .${MANAGED_BODY_CLASS} .body-sidebar .sidebar-notification {
        display: none !important;
      }
      .${MANAGED_BODY_CLASS} .body-sidebar .body-sidebar-top .sidebar-items > .sidebar-item-container:not([data-erpw-sales-console-nav='1']) {
        display: none !important;
      }
      .${MANAGED_BODY_CLASS} .body-sidebar .body-sidebar-top .edit-mode {
        display: none !important;
      }
      .${MANAGED_BODY_CLASS} .body-sidebar .sidebar-item-container:has(> .standard-sidebar-item > .item-anchor[href="${HOME_PATH}"]),
      .${MANAGED_BODY_CLASS} .body-sidebar .sidebar-item-container:has(> .standard-sidebar-item > .item-anchor[href$="${HOME_PATH}"]) {
        display: none !important;
      }
      .${MANAGED_BODY_CLASS} .body-sidebar .sidebar-item-container > .standard-sidebar-item.active-sidebar {
        min-height: 40px;
        border-radius: 12px;
        border: 1px solid rgba(230, 235, 242, 0.98);
        background: #ffffff;
        box-shadow:
          0 1px 2px rgba(15, 23, 42, 0.04),
          0 6px 16px rgba(15, 23, 42, 0.05);
      }
      .${MANAGED_BODY_CLASS} .body-sidebar .sidebar-item-container > .standard-sidebar-item.active-sidebar .item-anchor {
        min-height: 40px;
        height: 40px;
        gap: 10px;
        padding: 5px 9px;
      }
      .${MANAGED_BODY_CLASS} .body-sidebar .sidebar-item-container > .standard-sidebar-item.active-sidebar .sidebar-item-icon {
        padding: 7px;
      }
      .erpw-sales-console-sidebar-shell {
        display: grid;
        gap: 10px;
      }
      .erpw-sales-console-sidebar-utilities {
        display: grid;
        gap: 6px;
        margin-bottom: 2px;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(229, 235, 243, 0.88);
      }
      .erpw-sales-console-sidebar-utility {
        display: grid;
        grid-template-columns: 28px minmax(0, 1fr) auto;
        align-items: center;
        justify-items: start;
        gap: 8px;
        width: 100%;
        min-width: 0;
        max-width: 100%;
        box-sizing: border-box;
        min-height: 40px;
        padding: 5px 9px;
        border: 1px solid rgba(255, 255, 255, 0);
        border-radius: 12px;
        background: transparent;
        color: #334155;
        box-shadow: none;
        text-align: left;
        transition: background 120ms ease, border-color 120ms ease, box-shadow 120ms ease, color 120ms ease;
        outline: none;
      }
      .erpw-sales-console-sidebar-utility:hover {
        background: rgba(255, 255, 255, 0.92);
        border-color: rgba(229, 235, 243, 0.96);
        color: #0f172a;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
      }
      .erpw-sales-console-sidebar-utility-icon {
        width: 26px;
        height: 26px;
        display: inline-grid;
        place-items: center;
        border-radius: 9px;
        border: 1px solid rgba(226, 232, 240, 0.68);
        background: #ffffff;
        color: #64748b;
      }
      .erpw-sales-console-sidebar-utility-icon svg {
        width: 14px;
        height: 14px;
      }
      .erpw-sales-console-sidebar-utility-copy {
        min-width: 0;
        justify-self: start;
        text-align: left;
      }
      .erpw-sales-console-sidebar-utility-title {
        display: block;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-size: 13px;
        font-weight: 600;
        line-height: 1.35;
      }
      .erpw-sales-console-sidebar-utility-meta {
        font-size: 11px;
        line-height: 1.35;
        color: #94a3b8;
      }
      .erpw-sales-console-sidebar-utility-shortcut {
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.01em;
        color: #94a3b8;
        justify-self: end;
        white-space: nowrap;
      }
      .erpw-sales-console-sidebar-head {
        display: grid;
        gap: 4px;
        padding: 0 8px 4px;
      }
      .erpw-sales-console-sidebar-title {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #52627a;
      }
      .erpw-sales-console-sidebar-mode {
        font-size: 13px;
        font-weight: 600;
        color: #0f172a;
        line-height: 1.35;
      }
      .erpw-sales-console-sidebar-scope {
        font-size: 11.5px;
        line-height: 1.45;
        color: #64748b;
      }
      .erpw-sales-console-sidebar-section {
        display: grid;
        gap: 2px;
      }
      .erpw-sales-console-sidebar-section-label {
        padding: 0 8px 2px;
        font-size: 10.5px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #94a3b8;
      }
      .erpw-sales-console-sidebar-item .standard-sidebar-item {
        width: 100%;
      }
      .erpw-sales-console-sidebar-link {
        display: grid !important;
        grid-template-columns: 28px minmax(0, 1fr);
        align-items: center;
        justify-items: start;
        gap: 8px !important;
        width: 100%;
        min-width: 0;
        max-width: 100%;
        box-sizing: border-box;
        min-height: 40px;
        padding: 5px 9px;
        border: 1px solid rgba(255, 255, 255, 0);
        border-radius: 12px;
        background: transparent;
        color: #334155;
        box-shadow: none;
        text-align: left;
        transition: background 120ms ease, border-color 120ms ease, color 120ms ease, box-shadow 120ms ease;
        outline: none;
      }
      .erpw-sales-console-sidebar-link:hover {
        background: rgba(255, 255, 255, 0.92);
        border-color: rgba(229, 235, 243, 0.96);
        color: #0f172a;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
      }
      .erpw-sales-console-sidebar-link.is-active {
        background: #ffffff;
        border-color: rgba(230, 235, 242, 0.98);
        color: #0f172a;
        box-shadow:
          0 1px 2px rgba(15, 23, 42, 0.04),
          0 6px 16px rgba(15, 23, 42, 0.05);
      }
      .erpw-sales-console-sidebar-link:focus,
      .erpw-sales-console-sidebar-link:active {
        outline: none;
      }
      .${MANAGED_BODY_CLASS} .body-sidebar :is(a, button, [role="button"], .collapse-sidebar-link):focus-visible,
      .erpw-sales-console-sidebar-header:focus-visible,
      .erpw-sales-console-sidebar-utility:focus-visible,
      .erpw-sales-console-sidebar-link:focus-visible {
        outline: none;
        box-shadow: inset 0 0 0 3px #2563eb;
      }
      .erpw-sales-console-sidebar-icon {
        width: 26px;
        height: 26px;
        display: inline-grid;
        place-items: center;
        border-radius: 9px;
        border: 1px solid rgba(226, 232, 240, 0.68);
        background: #ffffff;
        color: #64748b;
        box-shadow: none;
      }
      .erpw-sales-console-sidebar-link.is-active .erpw-sales-console-sidebar-icon {
        border-color: rgba(203, 213, 225, 0.72);
        background: #ffffff;
        color: #334155;
      }
      .erpw-sales-console-sidebar-icon svg {
        width: 14px;
        height: 14px;
      }
      .erpw-sales-console-sidebar-copy {
        min-width: 0;
        justify-self: start;
        text-align: left;
      }
      .erpw-sales-console-sidebar-text {
        display: block;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-size: 13px;
        font-weight: 600;
        line-height: 1.35;
      }
      .erpw-sales-console-search-dialog .modal-dialog {
        max-width: 760px;
      }
      .erpw-sales-console-search-shell {
        display: grid;
        gap: 10px;
        padding-top: 0;
      }
      .erpw-sales-console-search-bar {
        display: grid;
        grid-template-columns: 34px minmax(0, 1fr) auto;
        align-items: center;
        gap: 9px;
        min-height: 48px;
        padding: 0 12px;
        border: 1px solid rgba(214, 223, 236, 0.94);
        border-radius: 14px;
        background: #ffffff;
        box-shadow:
          0 1px 2px rgba(15, 23, 42, 0.025),
          0 8px 18px rgba(15, 23, 42, 0.035);
      }
      .erpw-sales-console-search-bar-icon {
        width: 26px;
        height: 26px;
        display: inline-grid;
        place-items: center;
        border-radius: 9px;
        border: 1px solid rgba(228, 234, 242, 0.94);
        background: #ffffff;
        color: #64748b;
      }
      .erpw-sales-console-search-bar-icon svg {
        width: 15px;
        height: 15px;
      }
      .erpw-sales-console-search-input {
        width: 100%;
        border: none;
        background: transparent;
        font-size: 13px;
        font-weight: 500;
        color: #0f172a;
        outline: none;
        box-shadow: none;
      }
      .erpw-sales-console-search-input::placeholder {
        color: #a3afbf;
        font-weight: 500;
      }
      .erpw-sales-console-search-bar:has(.erpw-sales-console-search-input:focus-visible) {
        outline: 3px solid #2563eb;
        outline-offset: 2px;
      }
      .erpw-sales-console-search-status {
        font-size: 12px;
        line-height: 1.5;
        color: #64748b;
      }
      .erpw-sales-console-search-status[hidden] {
        display: none;
      }
      .erpw-sales-console-search-results {
        display: grid;
        gap: 12px;
        max-height: min(58vh, 560px);
        overflow: auto;
        padding-right: 2px;
      }
      .erpw-sales-console-search-results[hidden] {
        display: none;
      }
      .erpw-sales-console-search-group {
        display: grid;
        gap: 6px;
      }
      .erpw-sales-console-search-group-label {
        padding-left: 2px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #94a3b8;
      }
      .erpw-sales-console-search-result {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr);
        align-items: start;
        gap: 12px;
        width: 100%;
        padding: 12px 14px;
        border: 1px solid rgba(229, 235, 243, 0.96);
        border-radius: 14px;
        background: #ffffff;
        text-align: left;
        transition: border-color 120ms ease, box-shadow 120ms ease, transform 120ms ease;
      }
      .erpw-sales-console-search-result:hover,
      .erpw-sales-console-search-result.is-active {
        border-color: #2563eb;
        box-shadow:
          0 1px 2px rgba(15, 23, 42, 0.04),
          0 10px 20px rgba(15, 23, 42, 0.05);
      }
      .erpw-sales-console-search-result:focus-visible {
        outline: none;
        box-shadow:
          inset 0 0 0 3px #2563eb,
          0 1px 2px rgba(15, 23, 42, 0.04),
          0 10px 20px rgba(15, 23, 42, 0.05);
      }
      .erpw-sales-console-search-result-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 24px;
        padding: 0 8px;
        border-radius: 999px;
        border: 1px solid rgba(228, 234, 242, 0.98);
        background: #f8fafc;
        color: #52627a;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        white-space: nowrap;
      }
      .erpw-sales-console-search-result-copy {
        min-width: 0;
        display: grid;
        gap: 3px;
      }
      .erpw-sales-console-search-result-title {
        font-size: 13px;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.4;
      }
      .erpw-sales-console-search-result-meta {
        font-size: 12px;
        line-height: 1.5;
        color: #64748b;
      }
      @container (max-width: 80px) {
        .erpw-sales-console-sidebar-nav {
          margin-top: 8px;
        }
        .erpw-sales-console-sidebar-shell,
        .erpw-sales-console-sidebar-section {
          gap: 8px;
        }
        .erpw-sales-console-sidebar-utilities {
          gap: 8px;
          padding-bottom: 10px;
        }
        .erpw-sales-console-sidebar-section-label,
        .erpw-sales-console-sidebar-utility-copy,
        .erpw-sales-console-sidebar-utility-shortcut,
        .erpw-sales-console-sidebar-copy {
          display: none !important;
        }
        .erpw-sales-console-sidebar-utility,
        .erpw-sales-console-sidebar-link {
          display: inline-grid;
          grid-template-columns: 28px;
          justify-content: center;
          justify-items: center;
          width: 31px;
          min-width: 31px;
          max-width: 31px;
          min-height: 40px;
          padding: 5px 1px;
          gap: 0;
        }
        .erpw-sales-console-sidebar-item,
        .erpw-sales-console-sidebar-item .standard-sidebar-item {
          width: 31px;
          min-width: 31px;
          max-width: 31px;
        }
      }
    `;
    document.head.appendChild(style);
  }

  function decodeRoutePart(value) {
    try {
      return decodeURIComponent(String(value || ""));
    } catch (error) {
      return String(value || "");
    }
  }

  function routeFromLocation() {
    const pathname = String((root.location && root.location.pathname) || "");
    const parts = pathname
      .replace(/^\/+/, "")
      .split("/")
      .filter(Boolean)
      .map(decodeRoutePart);
    if (!parts.length) return [];

    const routeParts = parts[0] === "desk" || parts[0] === "app" ? parts.slice(1) : parts;
    if (!routeParts.length) return [];

    const pageKey = routeParts[0];
    if (SLUG_FORM_DOCTYPES[pageKey]) {
      return ["Form", SLUG_FORM_DOCTYPES[pageKey], routeParts[1] || ""];
    }
    return routeParts;
  }

  function getRoute() {
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) && route.length ? route : routeFromLocation();
  }

  function isWorkspaceHomeRoute(route) {
    const pageKey = Array.isArray(route) ? String(route[0] || "") : "";
    const config = workspaceConfig(route);
    return pageKey === config.homeRoute || pageKey === config.launcherRoute;
  }

  function isSalesConsoleHomeRoute(route) {
    return workspaceConfig(route).workspaceId === "sales" && isWorkspaceHomeRoute(route);
  }

  function getManagedFormDoctype(route) {
    const doctype = routeDoctype(route);
    if (!doctype) return "";
    const config = workspaceConfig(route);
    return config.managedFormActiveKeys[doctype] ? doctype : "";
  }

  function isManagedRoute(route) {
    if (!Array.isArray(route) || !route.length) return false;
    const pageKey = String(route[0] || "");
    const config = workspaceConfig(route);
    if (pageKey === config.homeRoute || pageKey === config.launcherRoute) return true;
    if (pageKey === config.worklistRoute || pageKey === config.reportRoute) return true;
    if (Object.keys(config.routes || {}).some((key) => !/_path$/i.test(key) && config.routes[key] === pageKey)) return true;
    if (getManagedFormDoctype(route)) return true;
    return false;
  }

  const MANAGED_DETAIL_ROUTE_ACTIVE_KEYS = Object.freeze({
    procurement: Object.freeze({
      poFollowUp: "purchase_order_directory",
      supplierDetail: "supplier_directory",
      itemDetail: "buying_item_directory",
      purchaseRequestReview: "purchase_request_directory",
      purchaseRequestForm: "purchase_request_directory",
      rfqForm: "rfq_directory",
      rfqReview: "rfq_directory",
      supplierQuotationForm: "supplier_quotation_directory",
      supplierQuotationReview: "supplier_quotation_directory",
      purchaseOrderForm: "purchase_order_directory",
    }),
    warehouse: Object.freeze({
      receiving: "inbound_receiving",
      picking: "outbound_picking",
      stockException: "stock_exceptions",
      stockPosture: "stock_exceptions",
      movement: "movement_visibility",
    }),
  });

  function managedDetailRouteActiveKey(config, pageKey) {
    const workspaceRoutes = config && config.routes ? config.routes : {};
    const routeMap = MANAGED_DETAIL_ROUTE_ACTIVE_KEYS[String(config && config.workspaceId || "")];
    if (!routeMap) return "";
    const routeName = Object.keys(routeMap).find((key) => workspaceRoutes[key] === pageKey);
    return routeName ? routeMap[routeName] : "";
  }

  function resolveActiveKey(route) {
    if (!Array.isArray(route) || !route.length) return "";
    const pageKey = String(route[0] || "");
    const config = workspaceConfig(route);
    const managedDoctype = getManagedFormDoctype(route);
    if (managedDoctype) return config.managedFormActiveKeys[managedDoctype] || "";
    if (pageKey === config.homeRoute || pageKey === config.launcherRoute) {
      return config.sidebar.homeKey || (config.workspaceId === "procurement" ? "procurement_console_home" : "sales_console_home");
    }
    if (pageKey === config.worklistRoute) {
      const worklistKey = String(route[1] || "").replace(/-/g, "_");
      if (config.workspaceId === "sales") {
        if (["quotation_directory", "quotations_waiting_action", "quotations_awaiting_approval", "expiring_quotations"].includes(worklistKey)) return "quotation_directory";
        if (["sales_order_directory", "open_orders", "sales_orders_pending_fulfillment", "orders_due_soon", "orders_blocked_by_approval", "partially_delivered_orders", "invoices_outstanding", "sales_returns_in_progress"].includes(worklistKey)) return "sales_order_directory";
        if (["customer_detail", "customer_editor"].includes(worklistKey)) return "customer_directory";
        if (worklistKey === "item_detail") return "item_directory";
        return worklistKey;
      }
      if (["requests_to_source"].includes(worklistKey)) return "purchase_request_directory";
      if (["purchase_orders_due_soon", "purchase_orders_overdue", "purchase_orders_late_or_unreceived", "purchase_orders_partially_received", "purchase_orders_not_billed_visibility", "purchase_orders_supplier_follow_up", "purchase_orders_open", "purchase_orders_pending_approval"].includes(worklistKey)) return "purchase_order_directory";
      if (["rfqs_awaiting_supplier_response", "rfqs_partially_quoted"].includes(worklistKey)) return "rfq_directory";
      if (["supplier_quotations_to_compare", "supplier_quotations_expiring"].includes(worklistKey)) return "supplier_quotation_directory";
      return worklistKey;
    }
    if (pageKey === config.reportRoute && config.workspaceId === "procurement") {
      const reportKey = String(route[1] || "").replace(/-/g, "_");
      if (!reportKey || reportKey === "index" || reportKey === "procurement_reports_index") return "procurement_reports";
      if (reportKey === "supplier_quotation_comparison") return "supplier_quotation_comparison";
      return "procurement_reports";
    }
    const managedDetailKey = managedDetailRouteActiveKey(config, pageKey);
    if (managedDetailKey) return managedDetailKey;
    if (pageKey === config.reportRoute) return "";
    return "";
  }

  function getSidebarHost() {
    const topHost = document.querySelector(".body-sidebar-top .sidebar-items");
    const bottomHost = document.querySelector(".body-sidebar-bottom");
    return {
      topHost,
      bottomHost,
      host: topHost || bottomHost,
    };
  }

  function ensureManagedSidebarHost() {
    let bodySidebar = document.querySelector(".body-sidebar");
    if (!bodySidebar) return getSidebarHost();

    let topSection = bodySidebar.querySelector(".body-sidebar-top");
    if (!topSection) {
      topSection = document.createElement("div");
      topSection.className = "body-sidebar-top";
      const bottomSection = bodySidebar.querySelector(".body-sidebar-bottom");
      bodySidebar.insertBefore(topSection, bottomSection || null);
    }

    let topHost = topSection.querySelector(".sidebar-items");
    if (!topHost) {
      topHost = document.createElement("div");
      topHost.className = "sidebar-items";
      topSection.insertBefore(topHost, topSection.firstChild);
    }

    return getSidebarHost();
  }

  function removeGuideItem() {
    document.querySelectorAll("[data-sales-console-guide='1']").forEach((node) => node.remove());
  }

  function removeSidebar() {
    document.querySelectorAll("[data-erpw-sales-console-nav='1']").forEach((node) => node.remove());
  }

  function clearSidebarArtifacts(route) {
    contextCoordinator.clear();
    setManagedBodyState(false);
    setManagedSidebarHeader(false);
    removeSidebar();
    if (searchDialog && !isManagedRoute(route)) {
      searchDialog.hide();
    }
    if (!isSalesConsoleHomeRoute(route)) {
      removeGuideItem();
    }
  }

  function hasVisibleNativeSidebarArtifacts() {
    return Array.from(document.querySelectorAll(
      ".body-sidebar .navbar-search-bar, .body-sidebar-top .sidebar-items > .sidebar-item-container:not([data-erpw-sales-console-nav='1'])"
    )).some((node) => {
      const style = root.getComputedStyle ? root.getComputedStyle(node) : null;
      const rect = typeof node.getBoundingClientRect === "function" ? node.getBoundingClientRect() : null;
      return (!style || (style.display !== "none" && style.visibility !== "hidden"))
        && (!rect || (rect.width > 0 && rect.height > 0));
    });
  }

  function setManagedBodyState(enabled) {
    if (!document.body) return;
    document.body.classList.toggle(MANAGED_BODY_CLASS, Boolean(enabled));
  }

  function getSidebarHeaderParts() {
    const header = document.querySelector(".body-sidebar .sidebar-header");
    if (!header) return null;
    return {
      header,
      icon: header.querySelector(".sidebar-item-icon .header-logo"),
      title: header.querySelector(".header-title"),
      subtitle: header.querySelector(".header-subtitle"),
    };
  }

  function createManagedSidebarHeader() {
    const bodySidebar = document.querySelector(".body-sidebar");
    if (!bodySidebar) return null;
    const config = workspaceConfig(getRoute());

    const header = document.createElement("a");
    header.className = "sidebar-header erpw-sales-console-sidebar-header";
    header.setAttribute("data-erpw-created-sales-console-header", "1");
    header.setAttribute("href", config.homePath);
    header.style.textDecoration = "none";
    header.style.width = "auto";
    header.style.cursor = "pointer";
    header.style.paddingLeft = "8px";
    header.style.paddingRight = "8px";
    header.innerHTML = `
      <div class="sidebar-item-icon" style="background-color: var();">
        <div class="header-logo">${managedHeaderIconMarkup()}</div>
      </div>
      <div class="title-container">
        <div class="sidebar-item-label header-title" data-name-style="">PrimeAxis</div>
        <div class="sidebar-item-label header-subtitle">${escapeHtml(config.title)}</div>
      </div>
      <button class="btn-reset drop-icon show-in-edit-mode">
        <svg class="icon icon-sm" style="display: block;margin:auto;" aria-hidden="true">
          <use class="" href="#icon-chevron-down"></use>
        </svg>
      </button>
    `;
    bodySidebar.insertBefore(header, bodySidebar.firstChild);
    return getSidebarHeaderParts();
  }

  function managedHeaderIconMarkup() {
    return `
      <div class="icon-container" style="background-color: rgb(123, 128, 138);">
        <svg fill="currentColor" class="desktop-alphabet icon text-ink-gray-7 icon-sm" stroke="none" style="color: var(--white);" aria-hidden="true">
          <use class="" href="#P"></use>
        </svg>
      </div>
    `;
  }

  function restoreNativeAttribute(node, name, wasPresent, value) {
    if (!node || !name) return;
    if (wasPresent) node.setAttribute(name, value || "");
    else node.removeAttribute(name);
  }

  function setManagedSidebarHeader(enabled) {
    let parts = getSidebarHeaderParts();
    if (!parts && enabled) {
      parts = createManagedSidebarHeader();
    }
    if (!parts) return;

    const { header, icon, title, subtitle } = parts;
    const config = workspaceConfig(getRoute());
    if (enabled) {
      if (!header.dataset.erpwNativeHeaderCaptured) {
        header.dataset.erpwNativeHeaderCaptured = "1";
        header.dataset.erpwNativeHeaderIcon = icon ? icon.innerHTML : "";
        header.dataset.erpwNativeHeaderTitle = title ? title.textContent : "";
        header.dataset.erpwNativeHeaderSubtitle = subtitle ? subtitle.textContent : "";
        header.dataset.erpwNativeHeaderHadHref = header.hasAttribute("href") ? "1" : "0";
        header.dataset.erpwNativeHeaderHref = header.getAttribute("href") || "";
        const nativeDropIcon = header.querySelector(".drop-icon");
        header.dataset.erpwNativeDropHadAriaHidden = nativeDropIcon && nativeDropIcon.hasAttribute("aria-hidden") ? "1" : "0";
        header.dataset.erpwNativeDropAriaHidden = nativeDropIcon ? nativeDropIcon.getAttribute("aria-hidden") || "" : "";
        header.dataset.erpwNativeDropHadTabindex = nativeDropIcon && nativeDropIcon.hasAttribute("tabindex") ? "1" : "0";
        header.dataset.erpwNativeDropTabindex = nativeDropIcon ? nativeDropIcon.getAttribute("tabindex") || "" : "";
      }
      header.classList.add("erpw-sales-console-sidebar-header");
      header.setAttribute("href", config.homePath);
      if (icon) icon.innerHTML = managedHeaderIconMarkup();
      if (title) title.textContent = "PrimeAxis";
      if (subtitle) subtitle.textContent = config.title;
      const dropIcon = header.querySelector(".drop-icon");
      if (dropIcon) {
        dropIcon.setAttribute("aria-hidden", "true");
        dropIcon.setAttribute("tabindex", "-1");
      }
      return;
    }

    if (header.getAttribute("data-erpw-created-sales-console-header") === "1") {
      header.remove();
      return;
    }

    if (!header.dataset.erpwNativeHeaderCaptured) return;
    header.classList.remove("erpw-sales-console-sidebar-header");
    if (icon) icon.innerHTML = header.dataset.erpwNativeHeaderIcon || "";
    if (title) title.textContent = header.dataset.erpwNativeHeaderTitle || "";
    if (subtitle) subtitle.textContent = header.dataset.erpwNativeHeaderSubtitle || "";
    restoreNativeAttribute(header, "href", header.dataset.erpwNativeHeaderHadHref === "1", header.dataset.erpwNativeHeaderHref);
    const dropIcon = header.querySelector(".drop-icon");
    if (dropIcon) {
      restoreNativeAttribute(dropIcon, "aria-hidden", header.dataset.erpwNativeDropHadAriaHidden === "1", header.dataset.erpwNativeDropAriaHidden);
      restoreNativeAttribute(dropIcon, "tabindex", header.dataset.erpwNativeDropHadTabindex === "1", header.dataset.erpwNativeDropTabindex);
    }
    delete header.dataset.erpwNativeHeaderCaptured;
    delete header.dataset.erpwNativeHeaderIcon;
    delete header.dataset.erpwNativeHeaderTitle;
    delete header.dataset.erpwNativeHeaderSubtitle;
    delete header.dataset.erpwNativeHeaderHadHref;
    delete header.dataset.erpwNativeHeaderHref;
    delete header.dataset.erpwNativeDropHadAriaHidden;
    delete header.dataset.erpwNativeDropAriaHidden;
    delete header.dataset.erpwNativeDropHadTabindex;
    delete header.dataset.erpwNativeDropTabindex;
  }

  function ensureSidebarWrapper() {
    const { topHost, bottomHost, host } = ensureManagedSidebarHost();
    if (!host) return null;

    let wrapper = document.querySelector("[data-erpw-sales-console-nav='1']");
    if (wrapper) return wrapper;

    wrapper = document.createElement("div");
    wrapper.className = "erpw-sales-console-sidebar-nav sidebar-item-container";
    wrapper.setAttribute("data-erpw-sales-console-nav", "1");

    if (topHost) {
      topHost.insertBefore(wrapper, topHost.firstChild);
      return wrapper;
    }

    const collapseLink = bottomHost ? bottomHost.querySelector(".collapse-sidebar-link") : null;
    if (collapseLink && bottomHost) {
      bottomHost.insertBefore(wrapper, collapseLink);
      return wrapper;
    }

    if (bottomHost) {
      bottomHost.appendChild(wrapper);
      return wrapper;
    }

    return null;
  }

  function fallbackContext(route) {
    const config = workspaceConfig(route || getRoute());
    const fallbackItems = config.fallbackItems.length
      ? config.fallbackItems
      : [
        { key: config.workspaceId === "procurement" ? "procurement_console_home" : "sales_console_home", label: "Overview", icon: "home", target: { kind: "page", route: config.homeRoute } },
      ];
    return {
      schema_version: SIDEBAR_CONTEXT_SCHEMA_VERSION,
      workspace: config.workspace,
      sidebar: {
        schema_version: SIDEBAR_CONTEXT_SCHEMA_VERSION,
        workspace_id: config.workspaceId,
        title: config.title,
        mode_label: config.modeLabel,
        scope_label: config.workspaceId === "finance" ? "Read-only overview" : "",
        items: fallbackItems,
        sections: [
          {
            key: config.sidebar.sectionKey || (config.workspaceId === "procurement" ? "workspace" : "browse"),
            label: config.sidebar.sectionLabel || (config.workspaceId === "procurement" ? "Workspace" : "Browse"),
            items: fallbackItems,
          },
        ],
      },
    };
  }

  function isWorkspaceSearchEnabled(config) {
    return !(config && config.search && config.search.enabled === false);
  }

  function shortcutLabel() {
    const isMac = typeof navigator !== "undefined" && /Mac|iPhone|iPad/.test(String(navigator.platform || ""));
    return isMac ? "⌘K" : "Ctrl+K";
  }

  function routeToPage(route) {
    if (!route) return;
    frappe.set_route(String(route));
  }

  function routeToList(doctype, filters) {
    frappe.route_options = filters && Object.keys(filters).length ? filters : {};
    frappe.set_route("List", doctype);
  }

  function routeToReport(reportName, filters) {
    frappe.route_options = filters && Object.keys(filters).length ? filters : {};
    frappe.set_route("query-report", reportName);
  }

  function encodeRoutePart(value) {
    return encodeURIComponent(String(value || "").trim());
  }

  function customerRouteValue(filters) {
    return filters && typeof filters === "object" ? String(filters.customer || "").trim() : "";
  }

  function itemRouteValue(filters) {
    return filters && typeof filters === "object" ? String(filters.item || filters.item_code || "").trim() : "";
  }


  function fallbackToProcurementManagedRoute(config, pageKey, slug, shellSelector) {
    if (!config || config.workspaceId !== "procurement") return;
    window.setTimeout(() => {
      const route = getRoute();
      const activePage = Array.isArray(route) ? String(route[0] || "") : "";
      const activeSlug = Array.isArray(route) ? String(route[1] || "") : "";
      if (activePage !== pageKey || activeSlug !== slug || document.querySelector(shellSelector)) return;
      window.location.href = `/desk/${pageKey}/${slug}`;
    }, 900);
  }

  function routeToWorklist(queueKey, filters) {
    const config = workspaceConfig(getRoute());
    if (!config.worklistRoute) return;
    const nextFilters = filters && Object.keys(filters).length ? filters : null;
    const normalizedQueueKey = String(queueKey || "").replace(/_/g, "-");
    const normalizedTargetKey = String(queueKey || "").replace(/-/g, "_");
    const routeCustomer = customerRouteValue(nextFilters);
    const routeItem = itemRouteValue(nextFilters);
    frappe.route_options = nextFilters || {};
    if (config.workspaceId === "sales" && ["customer_detail", "customer_editor"].includes(normalizedTargetKey) && routeCustomer) {
      frappe.set_route(config.worklistRoute, normalizedQueueKey, encodeRoutePart(routeCustomer));
      return;
    }
    if (config.workspaceId === "sales" && normalizedTargetKey === "item_detail" && routeItem) {
      frappe.set_route(config.worklistRoute, normalizedQueueKey, encodeRoutePart(routeItem));
      return;
    }
    frappe.set_route(config.worklistRoute, normalizedQueueKey);
    fallbackToProcurementManagedRoute(config, config.worklistRoute, normalizedQueueKey, ".erpw-list-shell");
  }

  function routeToReportPage(reportKey) {
    const config = workspaceConfig(getRoute());
    if (!config.reportRoute) return;
    const slug = String(reportKey || "").replace(/_/g, "-");
    frappe.set_route(config.reportRoute, slug);
    fallbackToProcurementManagedRoute(config, config.reportRoute, slug, ".erpw-report-shell");
  }

  function openNativeNotifications() {
    const dropdown = document.querySelector(".body-sidebar .dropdown-notifications");
    if (dropdown) {
      dropdown.classList.toggle("hidden");
      return true;
    }

    return false;
  }

  function warehouseTargetRoutePart(target, fallbackKey) {
    if (!target || typeof target !== "object") return "";
    const routeParts = Array.isArray(target.route_parts) ? target.route_parts : [];
    if (fallbackKey && target[fallbackKey]) return String(target[fallbackKey] || "").trim();
    return String(routeParts[0] || target.context_token || target.purchase_order || target.sales_order || "").trim();
  }

  function routeToWarehouseTarget(config, target) {
    if (!config || config.workspaceId !== "warehouse" || !target || target.kind !== "warehouse_page") return false;
    const route = String(target.route || "").trim();
    const routes = config.routes || {};
    const allowedRoutes = new Set([
      config.homeRoute,
      config.worklistRoute,
      routes.receiving,
      routes.picking,
      routes.stockException,
      routes.stockPosture,
      routes.movement,
    ].filter(Boolean));
    if (!allowedRoutes.has(route)) return false;
    if (route === config.worklistRoute) {
      const queueKey = String(target.queue_key || warehouseTargetRoutePart(target) || "").replace(/_/g, "-").trim();
      if (queueKey) frappe.set_route(route, queueKey);
      else frappe.set_route(route);
      return true;
    }
    const routePart = warehouseTargetRoutePart(target);
    if (routePart) frappe.set_route(route, routePart);
    else frappe.set_route(route);
    return true;
  }

  function sidebarTargetSignature(target) {
    if (!target || typeof target !== "object" || Array.isArray(target)) return "";
    const keys = Object.keys(target).sort();
    if (target.kind === "page" && keys.length === 2 && keys[0] === "kind" && keys[1] === "route") {
      if (typeof target.route !== "string" || !target.route || target.route !== target.route.trim()) return "";
      return `page:${target.route}`;
    }
    if (target.kind === "worklist" && keys.length === 2 && keys[0] === "kind" && keys[1] === "queue_key") {
      if (typeof target.queue_key !== "string" || !target.queue_key || target.queue_key !== target.queue_key.trim()) return "";
      return `worklist:${target.queue_key}`;
    }
    return "";
  }

  function sidebarTargetAllowed(workspace, target) {
    const signature = sidebarTargetSignature(target);
    if (!signature || !workspace) return false;
    const allowed = new Set(
      (Array.isArray(workspace.fallbackItems) ? workspace.fallbackItems : [])
        .map((item) => sidebarTargetSignature(item && item.target))
        .filter(Boolean)
    );
    return allowed.has(signature);
  }

  function isPlainSearchObject(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return false;
    const prototype = Object.getPrototypeOf(value);
    return prototype === Object.prototype || prototype === null;
  }

  function hasOnlySearchKeys(value, allowed, required) {
    if (!isPlainSearchObject(value)) return false;
    const allowedKeys = new Set(allowed || []);
    const requiredKeys = new Set(required || []);
    return Object.keys(value).every((key) => allowedKeys.has(key))
      && Array.from(requiredKeys).every((key) => Object.prototype.hasOwnProperty.call(value, key));
  }

  function managedSearchRouteIdentity(route) {
    if (!Array.isArray(route)) return "";
    return JSON.stringify(route.map((part) => String(part == null ? "" : part)));
  }

  function managedSearchTargetSignature(config, target) {
    if (!config || !target || !isPlainSearchObject(target)) return "";
    const keys = Object.keys(target).sort();
    if (target.kind === "worklist") {
      if (!["sales", "procurement"].includes(config.workspaceId)) return "";
      if (JSON.stringify(keys) !== JSON.stringify(["filters", "kind", "queue_key"])) return "";
      if (!isPlainSearchObject(target.filters) || Object.keys(target.filters).length !== 1
        || typeof target.filters.keyword !== "string" || !target.filters.keyword.trim()
        || target.filters.keyword !== target.filters.keyword.trim() || target.filters.keyword.length > 120) return "";
      const queueKey = typeof target.queue_key === "string" ? target.queue_key : "";
      if (!queueKey || queueKey !== queueKey.trim()) return "";
      const allowedQueues = new Set((config.fallbackItems || [])
        .map((item) => item && item.target)
        .filter((item) => item && item.kind === "worklist")
        .map((item) => item.queue_key));
      return allowedQueues.has(queueKey) ? `worklist:${queueKey}:${target.filters.keyword}` : "";
    }
    if (target.kind === "warehouse_page" && config.workspaceId === "warehouse") {
      const route = typeof target.route === "string" ? target.route : "";
      const routes = config.routes || {};
      const allowedRouteShapes = new Map([
        [routes.receiving, "route_parts"],
        [routes.picking, "route_parts"],
        [routes.stockException, "context_token"],
        [routes.stockPosture, "context_token"],
        [routes.movement, "context_token"],
      ].filter(([allowedRoute]) => typeof allowedRoute === "string" && allowedRoute));
      const expectedShape = allowedRouteShapes.get(route);
      if (!route || route !== route.trim() || !expectedShape) return "";
      const expectedKeys = expectedShape === "route_parts"
        ? ["kind", "route", "route_parts"]
        : ["context_token", "kind", "route"];
      if (JSON.stringify(keys) !== JSON.stringify(expectedKeys)) return "";
      if (expectedShape === "route_parts") {
        if (!Array.isArray(target.route_parts) || !target.route_parts.length || target.route_parts.length > 2
          || target.route_parts.some((part) => typeof part !== "string" || !part.trim() || part !== part.trim() || part.length > 180)) return "";
        return `warehouse_page:${route}:${target.route_parts.join("/")}`;
      }
      if (typeof target.context_token !== "string" || !target.context_token.trim()
        || target.context_token !== target.context_token.trim() || target.context_token.length > 512) return "";
      return `warehouse_page:${route}:${target.context_token}`;
    }
    return "";
  }

  function managedSearchTargetAllowed(config, target) {
    return Boolean(managedSearchTargetSignature(config, target));
  }

  function validateSearchPreview(config, preview, topLevelTarget) {
    if (!hasOnlySearchKeys(
      preview,
      ["title", "subtitle", "chips", "facts", "target", "primary_action_label", "boundary_note"],
      ["title", "subtitle", "chips", "facts", "target", "primary_action_label", "boundary_note"]
    )) return false;
    if (![preview.title, preview.subtitle, preview.primary_action_label, preview.boundary_note]
      .every((value) => typeof value === "string")) return false;
    if (!Array.isArray(preview.chips) || preview.chips.some((value) => typeof value !== "string")) return false;
    if (!Array.isArray(preview.facts) || preview.facts.some((fact) => !hasOnlySearchKeys(fact, ["label", "value"], ["label", "value"])
      || typeof fact.label !== "string" || typeof fact.value !== "string")) return false;
    const previewTarget = managedSearchTargetSignature(config, preview.target);
    return Boolean(previewTarget) && previewTarget === managedSearchTargetSignature(config, topLevelTarget);
  }

  function validateManagedSearchResult(config, item) {
    const allowedKeys = [
      "id", "result_type", "group_key", "group", "group_label", "doctype", "name", "label", "title",
      "subtitle", "meta", "badge_label", "result_label", "target", "preview", "primary_action_label",
    ];
    if (!hasOnlySearchKeys(item, allowedKeys, ["target"])) return false;
    if (!Object.entries(item).every(([key, value]) => key === "target" || key === "preview" || typeof value === "string")) return false;
    if (!managedSearchTargetAllowed(config, item.target)) return false;
    if (Object.prototype.hasOwnProperty.call(item, "preview") && !validateSearchPreview(config, item.preview, item.target)) return false;
    return true;
  }

  function validateManagedSearchPayload(config, payload) {
    const allowedKeys = ["state", "query", "message", "groups", "results", "no_effect"];
    if (!hasOnlySearchKeys(payload, allowedKeys, ["state", "query", "message", "results"])) return false;
    if (!["idle", "empty", "ready", "restricted", "unavailable"].includes(payload.state)
      || typeof payload.query !== "string" || typeof payload.message !== "string"
      || !Array.isArray(payload.results) || !payload.results.every((item) => validateManagedSearchResult(config, item))) return false;
    if (Object.prototype.hasOwnProperty.call(payload, "no_effect")
      && (!isPlainSearchObject(payload.no_effect) || !Object.values(payload.no_effect).every((value) => value === false))) return false;
    if (Object.prototype.hasOwnProperty.call(payload, "groups")) {
      if (!Array.isArray(payload.groups) || payload.groups.some((group) => !hasOnlySearchKeys(group, ["key", "label", "results"], ["key", "label", "results"])
        || typeof group.key !== "string" || typeof group.label !== "string" || !Array.isArray(group.results)
        || !group.results.every((item) => validateManagedSearchResult(config, item)))) return false;
    }
    return true;
  }

  function normalizedManagedSearchItem(config, item) {
    return Object.freeze({
      group_label: String(item.group_label || item.group || procurementSearchLabel(item, config, "group") || item.doctype || "Record"),
      badge_label: String(item.badge_label || item.result_label || procurementSearchLabel(item, config, "badge") || item.doctype || "Record"),
      label: String(item.label || item.title || item.name || "Unnamed record"),
      meta: String(item.meta || item.subtitle || ""),
      target: Object.freeze(Object.assign(
        {},
        item.target,
        item.target && item.target.filters ? { filters: Object.freeze(Object.assign({}, item.target.filters)) } : {},
        item.target && item.target.route_parts ? { route_parts: Object.freeze(item.target.route_parts.slice()) } : {}
      )),
    });
  }

  function normalizeManagedSearchQuery(query) {
    return String(query || "").trim();
  }

  function createManagedSearchGenerationCoordinator() {
    let generation = 0;
    let routeIdentity = "";
    let normalizedQuery = "";
    function begin(route, query) {
      generation += 1;
      routeIdentity = managedSearchRouteIdentity(route);
      normalizedQuery = normalizeManagedSearchQuery(query);
      return Object.freeze({ requestToken: generation, routeIdentity, normalizedQuery });
    }
    function current(route, requestToken, query) {
      return Number.isInteger(requestToken)
        && requestToken === generation
        && managedSearchRouteIdentity(route) === routeIdentity
        && normalizeManagedSearchQuery(query) === normalizedQuery;
    }
    function invalidate() {
      generation += 1;
      routeIdentity = "";
      normalizedQuery = "";
      return Object.freeze({ requestToken: generation, routeIdentity, normalizedQuery });
    }
    return Object.freeze({ begin, current, invalidate });
  }

  function createManagedSearchEnvelope(config, route, requestToken, normalizedQuery, payload) {
    const queryIdentity = normalizeManagedSearchQuery(normalizedQuery);
    if (!config || !queryIdentity || !validateManagedSearchPayload(config, payload)
      || normalizeManagedSearchQuery(payload.query) !== queryIdentity
      || !Number.isInteger(requestToken) || requestToken < 1) return null;
    const routeIdentity = managedSearchRouteIdentity(route);
    if (!routeIdentity) return null;
    return Object.freeze({
      schema_version: MANAGED_SEARCH_SCHEMA_VERSION,
      workspace_id: config.workspaceId,
      route_identity: routeIdentity,
      request_token: requestToken,
      normalized_query: queryIdentity,
      payload: Object.freeze({
        state: payload.state,
        query: queryIdentity,
        message: payload.message,
        results: Object.freeze(payload.results.map((item) => normalizedManagedSearchItem(config, item))),
      }),
    });
  }

  function managedSearchEnvelopeCurrent(envelope, config, route, requestToken, normalizedQuery) {
    const queryIdentity = normalizeManagedSearchQuery(normalizedQuery);
    return hasOnlySearchKeys(envelope, ["schema_version", "workspace_id", "route_identity", "request_token", "normalized_query", "payload"], ["schema_version", "workspace_id", "route_identity", "request_token", "normalized_query", "payload"])
      && envelope.schema_version === MANAGED_SEARCH_SCHEMA_VERSION
      && envelope.workspace_id === config.workspaceId
      && envelope.route_identity === managedSearchRouteIdentity(route)
      && envelope.request_token === requestToken
      && envelope.normalized_query === queryIdentity
      && envelope.payload
      && envelope.payload.query === queryIdentity;
  }

  function dispatchManagedSearchTarget(envelope, index, config, route, requestToken, normalizedQuery, executor) {
    if (!managedSearchEnvelopeCurrent(envelope, config, route, requestToken, normalizedQuery)) return false;
    const item = envelope.payload && envelope.payload.results ? envelope.payload.results[index] : null;
    if (!item || !managedSearchTargetAllowed(config, item.target) || typeof executor !== "function") return false;
    executor(item.target);
    return true;
  }

  function executeSidebarTarget(target) {
    const route = getRoute();
    if (!isManagedRoute(route)) return false;
    const config = workspaceConfig(route);
    if (!sidebarTargetAllowed(config.workspace, target)) return false;
    executeTarget(target);
    return true;
  }

  function executeTarget(target) {
    if (!target) return;
    const config = workspaceConfig(getRoute());
    if (target.notice) {
      frappe.show_alert({ message: __(target.notice), indicator: "blue" });
    }
    if (routeToWarehouseTarget(config, target)) return;
    const routeOwner = config.workspaceId === "sales" ? root.erpWorkspaceUiChildPage && root.erpWorkspaceUiChildPage.helpers : null;
    if (
      routeOwner
      && typeof routeOwner.routeToSalesConsoleTarget === "function"
      && routeOwner.routeToSalesConsoleTarget(target)
    ) {
      return;
    }
    if (target.kind === "page" && target.route) return routeToPage(target.route);
    if (target.kind === "worklist" && target.queue_key) {
      const route = getRoute();
      const config = workspaceConfig(route);
      const currentQueueKey = Array.isArray(route) && route[0] === config.worklistRoute
        ? String(route[1] || "").replace(/-/g, "_")
        : "";
	      const filters = target.filters && typeof target.filters === "object" ? target.filters : null;
	      const normalizedTargetKey = String(target.queue_key || "").replace(/-/g, "_");
	      if (config.workspaceId === "sales" && ["customer_detail", "customer_editor"].includes(normalizedTargetKey) && customerRouteValue(filters)) {
	        return routeToWorklist(target.queue_key, filters);
	      }
	      if (config.workspaceId === "sales" && normalizedTargetKey === "item_detail" && itemRouteValue(filters)) {
	        return routeToWorklist(target.queue_key, filters);
	      }
      const worklistRuntime = config.workspaceId === "sales" ? root.erpWorkspaceSalesConsoleWorklist : null;
      if (
        filters &&
        currentQueueKey === String(target.queue_key || "") &&
        worklistRuntime &&
        typeof worklistRuntime.applyFilters === "function"
      ) {
        if (worklistRuntime.applyFilters(target.queue_key, filters)) return;
      }
      return routeToWorklist(target.queue_key, filters);
    }
  }

  function resetSearchTimer() {
    if (searchTimer) {
      window.clearTimeout(searchTimer);
      searchTimer = null;
    }
  }

  function currentSearchElements() {
    if (!searchDialog || !searchDialog.fields_dict || !searchDialog.fields_dict.search_html) return null;
    const $root = searchDialog.fields_dict.search_html.$wrapper;
    return {
      $root,
      $input: $root.find("[data-erpw-sales-search-input]"),
      $status: $root.find("[data-erpw-sales-search-status]"),
      $results: $root.find("[data-erpw-sales-search-results]"),
    };
  }

  function resetWorkspaceSearch(message, normalizedQuery = "") {
    resetSearchTimer();
    const generation = searchGenerationCoordinator.begin(getRoute(), normalizedQuery);
    searchRequestToken = generation.requestToken;
    searchNormalizedQuery = generation.normalizedQuery;
    searchResults = [];
    activeSearchEnvelope = null;
    searchActiveIndex = -1;
    const elements = currentSearchElements();
    if (!elements) return searchRequestToken;
    if (message) {
      elements.$status.text(message).removeAttr("hidden");
    } else {
      elements.$status.text("").attr("hidden", true);
    }
    applyManagedSearchActiveState(elements.$results.get(0), elements.$input.get(0), -1);
    elements.$results.empty().attr("hidden", true);
    elements.$input.attr("aria-expanded", "false");
    return searchRequestToken;
  }

  function applyManagedSearchActiveState(resultRoot, input, index) {
    const items = resultRoot
      ? Array.from(resultRoot.querySelectorAll("[data-erpw-sales-search-index]"))
      : [];
    items.forEach((item) => {
      item.classList.remove("is-active");
      item.setAttribute("aria-selected", "false");
    });
    const active = Number.isInteger(index)
      ? items.find((item) => Number(item.getAttribute("data-erpw-sales-search-index")) === index)
      : null;
    if (!active) {
      if (input) input.removeAttribute("aria-activedescendant");
      return -1;
    }
    active.classList.add("is-active");
    active.setAttribute("aria-selected", "true");
    if (input && active.id) input.setAttribute("aria-activedescendant", active.id);
    if (typeof active.scrollIntoView === "function") active.scrollIntoView({ block: "nearest" });
    return index;
  }

  function bindManagedSearchResultFocus(resultRoot, activate) {
    if (!resultRoot || typeof resultRoot.addEventListener !== "function" || typeof activate !== "function") return false;
    if (resultRoot.__erpwManagedSearchFocusHandler) {
      resultRoot.removeEventListener("focusin", resultRoot.__erpwManagedSearchFocusHandler);
    }
    const handler = (event) => {
      const option = event.target && event.target.closest
        ? event.target.closest("[data-erpw-sales-search-index]")
        : null;
      if (!option || !resultRoot.contains(option)) return;
      activate(Number(option.getAttribute("data-erpw-sales-search-index")));
    };
    resultRoot.__erpwManagedSearchFocusHandler = handler;
    resultRoot.addEventListener("focusin", handler);
    return true;
  }

  function setWorkspaceSearchActive(index) {
    if (!searchResults.length) {
      searchActiveIndex = -1;
      return;
    }
    const boundedIndex = Math.max(0, Math.min(index, searchResults.length - 1));
    searchActiveIndex = boundedIndex;
    const elements = currentSearchElements();
    if (!elements) return;
    applyManagedSearchActiveState(elements.$results.get(0), elements.$input.get(0), boundedIndex);
  }

  function chooseWorkspaceSearchResult(index) {
    const item = searchResults[index];
    if (!item) return false;
    const route = getRoute();
    const config = workspaceConfig(route);
    const dispatched = dispatchManagedSearchTarget(
      activeSearchEnvelope, index, config, route, searchRequestToken, searchNormalizedQuery, executeTarget
    );
    if (dispatched && searchDialog) {
      searchRestoreFocusOnClose = false;
      searchDialog.hide();
    }
    return dispatched;
  }

  function managedSearchResultsMarkup(config, results, activeIndex) {
    const groupedResults = [];
    (Array.isArray(results) ? results : []).forEach((item, index) => {
      const groupLabel = item.group_label || procurementSearchLabel(item, config, "group");
      const groupKey = String(item.group_key || groupLabel || item.doctype || "Record");
      let group = groupedResults.find((entry) => entry.key === groupKey);
      if (!group) {
        group = { key: groupKey, label: groupLabel || groupKey, items: [] };
        groupedResults.push(group);
      }
      group.items.push(Object.assign({}, item, { _index: index }));
    });
    return groupedResults.map((group) => `
      <div class="erpw-sales-console-search-group">
        <div class="erpw-sales-console-search-group-label">${escapeHtml(group.label)}</div>
        ${group.items.map((item) => `
          <button
            type="button"
            class="erpw-sales-console-search-result${item._index === activeIndex ? " is-active" : ""}"
            data-erpw-sales-search-index="${item._index}"
            id="erpw-sales-console-search-option-${item._index}"
            role="option"
            aria-selected="${item._index === activeIndex ? "true" : "false"}"
          >
            <span class="erpw-sales-console-search-result-badge">${escapeHtml(item.badge_label || item.result_label || procurementSearchLabel(item, config, "badge") || item.doctype || "Record")}</span>
            <span class="erpw-sales-console-search-result-copy">
              <span class="erpw-sales-console-search-result-title">${escapeHtml(item.label || item.name || "Unnamed record")}</span>
              <span class="erpw-sales-console-search-result-meta">${escapeHtml(item.meta || "")}</span>
            </span>
          </button>
        `).join("")}
      </div>
    `).join("");
  }

  function renderWorkspaceSearchResults(envelope) {
    const elements = currentSearchElements();
    if (!elements) return;
    const route = getRoute();
    const config = workspaceConfig(route);
    if (!managedSearchEnvelopeCurrent(envelope, config, route, searchRequestToken, searchNormalizedQuery)) return false;
    const payload = envelope.payload;

    activeSearchEnvelope = envelope;
    searchResults = Array.isArray(payload.results) ? payload.results : [];
    searchActiveIndex = searchResults.length ? 0 : -1;

    if (!searchResults.length) {
      elements.$status.text((payload && payload.message) || `No ${config.title} records match this search yet.`).removeAttr("hidden");
      applyManagedSearchActiveState(elements.$results.get(0), elements.$input.get(0), -1);
      elements.$results.empty().attr("hidden", true);
      elements.$input.attr("aria-expanded", "false");
      return;
    }

    elements.$status.text((payload && payload.message) || `${searchResults.length} result(s) found.`).removeAttr("hidden");
    elements.$input.attr("aria-expanded", "true");

    elements.$results.html(
      managedSearchResultsMarkup(config, searchResults, searchActiveIndex)
    ).removeAttr("hidden");
    applyManagedSearchActiveState(elements.$results.get(0), elements.$input.get(0), searchActiveIndex);
    bindManagedSearchResultFocus(elements.$results.get(0), setWorkspaceSearchActive);

    elements.$results.find("[data-erpw-sales-search-index]").on("mouseenter", function () {
      setWorkspaceSearchActive(Number(this.getAttribute("data-erpw-sales-search-index")));
    });
    elements.$results.find("[data-erpw-sales-search-index]").on("mousedown", (event) => {
      event.preventDefault();
    });
    elements.$results.find("[data-erpw-sales-search-index]").on("click", function () {
      chooseWorkspaceSearchResult(Number(this.getAttribute("data-erpw-sales-search-index")));
    });
    return true;
  }

  function runWorkspaceSearch(query, generation = null) {
    const needle = normalizeManagedSearchQuery(query);
    const requestRoute = generation && Array.isArray(generation.route)
      ? generation.route.slice()
      : getRoute().slice();
    const requestToken = generation && Number.isInteger(generation.requestToken)
      ? generation.requestToken
      : resetWorkspaceSearch(null, needle);

    if (needle.length < 2 || requestToken !== searchRequestToken || needle !== searchNormalizedQuery
      || !searchGenerationCoordinator.current(requestRoute, requestToken, needle)) return;

    const config = workspaceConfig(requestRoute);
    const elements = currentSearchElements();
    if (elements) {
      elements.$status.text("Searching...").removeAttr("hidden");
    }

    Promise.resolve(frappe.call({
      method: config.searchMethod,
      args: { query: needle, limit: 12 },
    })).then((response) => {
      if (requestToken !== searchRequestToken || needle !== searchNormalizedQuery
        || !searchGenerationCoordinator.current(requestRoute, requestToken, needle)) return;
      const currentRoute = getRoute();
      const currentConfig = workspaceConfig(currentRoute);
      if (currentConfig.workspaceId !== config.workspaceId
        || managedSearchRouteIdentity(currentRoute) !== managedSearchRouteIdentity(requestRoute)) return;
      const envelope = createManagedSearchEnvelope(
        config, requestRoute, requestToken, needle, response && response.message ? response.message : {}
      );
      if (!envelope) {
        resetWorkspaceSearch(`${config.title} search is temporarily unavailable.`, needle);
        return;
      }
      renderWorkspaceSearchResults(envelope);
    }).catch(() => {
      if (requestToken !== searchRequestToken || needle !== searchNormalizedQuery
        || !searchGenerationCoordinator.current(requestRoute, requestToken, needle)
        || workspaceConfig(getRoute()).workspaceId !== config.workspaceId
        || managedSearchRouteIdentity(getRoute()) !== managedSearchRouteIdentity(requestRoute)) return;
      resetWorkspaceSearch(`${config.title} search is temporarily unavailable.`, needle);
    });
  }

  function scheduleWorkspaceSearch(query) {
    const needle = normalizeManagedSearchQuery(query);
    const requestRoute = getRoute().slice();
    const requestToken = resetWorkspaceSearch(null, needle);
    if (needle.length < 2) return;
    searchTimer = window.setTimeout(() => {
      runWorkspaceSearch(needle, { requestToken, route: requestRoute });
    }, 160);
  }

  function managedSearchShellMarkup(config) {
    const placeholder = (config.search && config.search.placeholder)
      || (config.workspaceId === "procurement"
        ? "Search suppliers, purchase requests, RFQs, quotations, or purchase orders"
        : "Search customers, items, quotations, or sales orders");
    return `
      <div class="erpw-sales-console-search-shell">
        <div class="erpw-sales-console-search-bar">
          <span class="erpw-sales-console-search-bar-icon" aria-hidden="true">${iconMarkup("search")}</span>
          <input
            type="text"
            class="erpw-sales-console-search-input"
            data-erpw-sales-search-input
            aria-label="Search ${escapeHtml(config.title)}"
            role="combobox"
            aria-autocomplete="list"
            aria-expanded="false"
            aria-controls="erpw-sales-console-search-results"
            placeholder="${escapeHtml(placeholder)}"
            autocomplete="off"
          />
          <span class="erpw-sales-console-sidebar-utility-shortcut">${escapeHtml(shortcutLabel())}</span>
        </div>
        <div
          class="erpw-sales-console-search-status"
          data-erpw-sales-search-status
          role="status"
          aria-live="polite"
          aria-atomic="true"
          hidden
        ></div>
        <div
          class="erpw-sales-console-search-results"
          data-erpw-sales-search-results
          id="erpw-sales-console-search-results"
          role="listbox"
          aria-label="${escapeHtml(config.title)} search results"
          hidden
        ></div>
      </div>
    `;
  }

  function managedDialogFocusableNodes(dialogRoot) {
    if (!dialogRoot || typeof dialogRoot.querySelectorAll !== "function") return [];
    return Array.from(dialogRoot.querySelectorAll(
      'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    )).filter((node) => {
      if (node.hidden || node.getAttribute("aria-hidden") === "true") return false;
      if (typeof node.getClientRects === "function" && node.getClientRects().length === 0) return false;
      return true;
    });
  }

  function containManagedDialogFocus(event, dialogRoot, activeElement) {
    if (!event || event.key !== "Tab") return false;
    const focusable = managedDialogFocusableNodes(dialogRoot);
    if (!focusable.length) return false;
    const current = activeElement || document.activeElement;
    const currentIndex = focusable.indexOf(current);
    const target = event.shiftKey
      ? (currentIndex <= 0 ? focusable[focusable.length - 1] : null)
      : (currentIndex < 0 || currentIndex === focusable.length - 1 ? focusable[0] : null);
    if (!target) return false;
    event.preventDefault();
    event.stopPropagation();
    target.focus();
    return true;
  }

  function restoreWorkspaceSearchFocus() {
    const target = searchRestoreFocusOnClose ? searchReturnFocus : null;
    searchReturnFocus = null;
    searchRestoreFocusOnClose = false;
    if (!target || target === document.body || !document.contains(target) || typeof target.focus !== "function") return false;
    window.setTimeout(() => {
      if (document.contains(target)) target.focus();
    }, 0);
    return true;
  }

  function bindWorkspaceSearchDialog(dialog) {
    if (!dialog || !dialog.fields_dict || !dialog.fields_dict.search_html) return;
    const config = workspaceConfig(getRoute());
    const $root = dialog.fields_dict.search_html.$wrapper;
    $root.html(managedSearchShellMarkup(config));
    const dialogRoot = dialog.$wrapper && typeof dialog.$wrapper.get === "function"
      ? dialog.$wrapper.get(0)
      : null;
    if (dialog.$wrapper && typeof dialog.$wrapper.off === "function") {
      dialog.$wrapper.off("keydown.erpWorkspaceSearchFocus").on("keydown.erpWorkspaceSearchFocus", (event) => {
        containManagedDialogFocus(event, dialogRoot);
      });
    }

    const $input = $root.find("[data-erpw-sales-search-input]");
    $input.on("input", function () {
      scheduleWorkspaceSearch(this.value);
    });
    $input.on("keydown", function (event) {
      if (event.key === "ArrowDown") {
        event.preventDefault();
        setWorkspaceSearchActive(searchActiveIndex + 1);
        return;
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        setWorkspaceSearchActive(searchActiveIndex - 1);
        return;
      }
      if (event.key === "Enter") {
        event.preventDefault();
        if (searchResults.length) {
          chooseWorkspaceSearchResult(searchActiveIndex >= 0 ? searchActiveIndex : 0);
        } else {
          runWorkspaceSearch(this.value);
        }
        return;
      }
      if (event.key === "Escape") {
        event.preventDefault();
        dialog.hide();
      }
    });
  }

  function ensureWorkspaceSearchDialog() {
    const config = workspaceConfig(getRoute());
    if (searchDialog) {
      if (typeof searchDialog.set_title === "function") searchDialog.set_title(__(`${config.title} Search`));
      bindWorkspaceSearchDialog(searchDialog);
      return searchDialog;
    }
    searchDialog = new frappe.ui.Dialog({
      title: __(`${config.title} Search`),
      size: "large",
      fields: [
        {
          fieldtype: "HTML",
          fieldname: "search_html",
        },
      ],
    });
    searchDialog.$wrapper.addClass("erpw-sales-console-search-dialog");
    bindWorkspaceSearchDialog(searchDialog);
    searchDialog.$wrapper.on("hidden.bs.modal", () => {
      resetWorkspaceSearch();
      restoreWorkspaceSearchFocus();
    });
    return searchDialog;
  }

  function openWorkspaceSearch(prefill) {
    const route = getRoute();
    const config = workspaceConfig(route);
    if (!isManagedRoute(route) || !isWorkspaceSearchEnabled(config)) return;
    searchReturnFocus = document.activeElement;
    searchRestoreFocusOnClose = true;
    const dialog = ensureWorkspaceSearchDialog();
    dialog.show();
    const elements = currentSearchElements();
    if (!elements) return;
    const value = String(prefill != null ? prefill : elements.$input.val() || "").trim();
    elements.$input.val(value);
    resetWorkspaceSearch();
    window.setTimeout(() => {
      elements.$input.trigger("focus").trigger("select");
      if (value.length >= 2) {
        scheduleWorkspaceSearch(value);
      }
    }, 30);
  }

  function workspaceIdentity(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return "";
    const hasCamel = Object.prototype.hasOwnProperty.call(value, "workspaceId");
    const hasSnake = Object.prototype.hasOwnProperty.call(value, "workspace_id");
    if (hasCamel && (typeof value.workspaceId !== "string" || !value.workspaceId || value.workspaceId !== value.workspaceId.trim())) return "";
    if (hasSnake && (typeof value.workspace_id !== "string" || !value.workspace_id || value.workspace_id !== value.workspace_id.trim())) return "";

    const camel = hasCamel ? value.workspaceId : "";
    const snake = hasSnake ? value.workspace_id : "";
    if (camel && snake && camel !== snake) return "";
    return camel || snake;
  }
  function sidebarItemsValid(items, workspace, seenKeys) {
    if (!Array.isArray(items)) return false;
    const itemKeys = seenKeys instanceof Set ? seenKeys : new Set();
    const registeredKeys = new Set(
      Array.isArray(workspace && workspace.fallbackItems)
        ? workspace.fallbackItems.map((item) => item && item.key).filter(Boolean)
        : []
    );
    return items.every((item) => {
      if (!item || typeof item !== "object" || Array.isArray(item)) return false;
      if (Object.keys(item).some((key) => !["key", "label", "icon", "target"].includes(key))) return false;
      if (typeof item.key !== "string" || !item.key || item.key !== item.key.trim()
        || !registeredKeys.has(item.key) || itemKeys.has(item.key)) return false;
      itemKeys.add(item.key);
      return typeof item.label === "string"
        && typeof item.icon === "string"
        && sidebarTargetAllowed(workspace, item.target);
    });
  }


  function sidebarSectionsValid(sidebar, workspace) {
    if (!sidebar || typeof sidebar !== "object" || Array.isArray(sidebar) || !Array.isArray(sidebar.sections)) return false;
    const sectionItemKeys = new Set();
    return sidebar.sections.every((section) => {
      if (!section || typeof section !== "object" || Array.isArray(section)) return false;
      if (Object.keys(section).some((key) => !["key", "label", "items"].includes(key))) return false;
      if (typeof section.key !== "string" || typeof section.label !== "string" || !Array.isArray(section.items)) return false;
      return sidebarItemsValid(section.items, workspace, sectionItemKeys);
    });
  }

  function financeSidebarCopyValid(sidebar, expectedWorkspaceId) {
    if (expectedWorkspaceId !== "finance") return true;
    const sections = Array.isArray(sidebar.sections) ? sidebar.sections : [];
    const rootItems = Array.isArray(sidebar.items) ? sidebar.items : [];
    const validItems = (items) => items.length === 1
      && items[0].key === "finance_control_desk_home"
      && items[0].label === "Overview"
      && items[0].icon === "home";
    return sidebar.title === "Finance Control Desk"
      && sidebar.mode_label === "Read-only aggregate posture"
      && ["Read-only overview", "Restricted"].includes(sidebar.scope_label)
      && sections.length === 1
      && sections[0].key === "workspace"
      && sections[0].label === "Workspace"
      && validItems(rootItems)
      && validItems(Array.isArray(sections[0].items) ? sections[0].items : []);
  }

  function sidebarPayloadMatchesWorkspace(payload, expectedWorkspaceId) {
    if (typeof expectedWorkspaceId !== "string" || !expectedWorkspaceId || expectedWorkspaceId !== expectedWorkspaceId.trim()) return false;
    const expected = expectedWorkspaceId;
    const topLevel = workspaceIdentity(payload && payload.workspace);
    const nested = workspaceIdentity(payload && payload.sidebar);
    const workspace = workspaceFromRegistry(expected);
    return Boolean(expected && payload && payload.sidebar && workspace)
      && payload.schema_version === SIDEBAR_CONTEXT_SCHEMA_VERSION
      && sidebarItemsValid(payload.sidebar.items, workspace)
      && payload.sidebar.schema_version === SIDEBAR_CONTEXT_SCHEMA_VERSION
      && topLevel === expected
      && nested === expected
      && sidebarSectionsValid(payload.sidebar, workspace)
      && financeSidebarCopyValid(payload.sidebar, expected);
  }

  function primePayload(payload) {
    const expectedKey = workspaceConfig(getRoute()).workspaceId;
    if (!sidebarPayloadMatchesWorkspace(payload, expectedKey)) return false;
    const workspace = payload.workspace || {};
    const key = workspaceId(workspace);
    contextCoordinator.prime(key, {
      schema_version: payload.schema_version,
      workspace,
      context: payload.context || {},
      scope: payload.scope || {},
      ui_profile: payload.ui_profile || {},
      sidebar: payload.sidebar || {},
      fetched_at: payload.fetched_at || null,
    });
    return true;
  }

  function loadSidebarContext(routeOverride) {
    const route = Array.isArray(routeOverride) ? routeOverride : getRoute();
    const config = workspaceConfig(route);
    const routeSignature = JSON.stringify(route || []);
    const routeIsCurrent = () => {
      const currentRoute = getRoute();
      return workspaceConfig(currentRoute).workspaceId === config.workspaceId
        && JSON.stringify(currentRoute || []) === routeSignature;
    };
    return contextCoordinator.load(
      config.workspaceId,
      () => Promise.resolve(frappe.call({ method: config.sidebarContextMethod })).then((response) => {
        if (!routeIsCurrent()) return null;
        const payload = response && response.message ? response.message : {};
        return sidebarPayloadMatchesWorkspace(payload, config.workspaceId) ? payload : fallbackContext(route);
      }),
      () => routeIsCurrent() ? fallbackContext(route) : null
    );
  }


  function buildSignature(sidebar, activeKey, config) {
    const searchConfig = config && config.search ? config.search : {};
    return JSON.stringify({
      activeKey: activeKey || "",
      workspace_id: sidebar && sidebar.workspace_id,
      title: sidebar && sidebar.title,
      mode_label: sidebar && sidebar.mode_label,
      scope_label: sidebar && sidebar.scope_label,
      sections: sidebar && sidebar.sections,
      search_enabled: isWorkspaceSearchEnabled(config),
      search_mode: searchConfig.mode || "",
      search_placement: searchConfig.placement || "",
    });
  }

  function renderSidebar(contextPayload, activeKey) {
    ensureStyles();
    const config = workspaceConfig(getRoute());
    if (!sidebarPayloadMatchesWorkspace(contextPayload, config.workspaceId)) {
      removeSidebar();
      return false;
    }
    const wrapper = ensureSidebarWrapper();
    if (!wrapper) return false;

    const fallbackPayload = fallbackContext(getRoute()) || {};
    const sidebar = contextPayload && contextPayload.sidebar ? contextPayload.sidebar : fallbackPayload.sidebar;
    if (!sidebar) {
      removeSidebar();
      return false;
    }
    const workspaceTitle = sidebar.title || config.title;
    const sections = Array.isArray(sidebar.sections) ? sidebar.sections.filter(Boolean) : [];
    if (!sections.length) {
      removeSidebar();
      return false;
    }

    const signature = buildSignature(sidebar, activeKey, config);
    const expectsSearchUtility = isWorkspaceSearchEnabled(config);
    const hasSearchUtility = Boolean(wrapper.querySelector("[data-erpw-sales-search-open]"));
    if (wrapper.getAttribute("data-erpw-sidebar-signature") === signature && (!expectsSearchUtility || hasSearchUtility)) {
      return true;
    }

    const searchUtilityMarkup = isWorkspaceSearchEnabled(config) ? `
        <button
          type="button"
          class="erpw-sales-console-sidebar-utility"
          data-erpw-sales-search-open="1"
          aria-label="Open ${escapeHtml(workspaceTitle)} search"
          title="Search"
        >
          <span class="erpw-sales-console-sidebar-utility-icon" aria-hidden="true">${iconMarkup("search")}</span>
          <span class="erpw-sales-console-sidebar-utility-copy">
            <span class="erpw-sales-console-sidebar-utility-title">Search</span>
          </span>
          <span class="erpw-sales-console-sidebar-utility-shortcut">${escapeHtml(shortcutLabel())}</span>
        </button>
    ` : "";
    const notificationUtilityMarkup = config.workspaceId === "warehouse" || config.workspaceId === "finance" ? "" : `
        <button
          type="button"
          class="erpw-sales-console-sidebar-utility"
          data-erpw-sales-notifications-open="1"
          aria-label="Open notifications"
          title="Notification"
        >
          <span class="erpw-sales-console-sidebar-utility-icon" aria-hidden="true">${iconMarkup("notification")}</span>
          <span class="erpw-sales-console-sidebar-utility-copy">
            <span class="erpw-sales-console-sidebar-utility-title">Notification</span>
          </span>
        </button>
    `;
    const utilitiesMarkup = `
      <div class="erpw-sales-console-sidebar-utilities">
        ${notificationUtilityMarkup}
        ${searchUtilityMarkup}
      </div>
    `;

    const itemIndex = new Map();
    const showSectionLabels = sections.length > 1;
    let currentIndex = 0;
    const sectionsMarkup = sections.map((section) => {
      const items = Array.isArray(section.items) ? section.items.filter(Boolean) : [];
      if (!items.length) return "";

      const itemsMarkup = items.map((item) => {
        currentIndex += 1;
        const indexKey = String(currentIndex);
        itemIndex.set(indexKey, item);
        const activeClass = item.key === activeKey ? " is-active" : "";
        const activeState = item.key === activeKey ? ' aria-current="page"' : "";
        const itemLabel = item.label || workspaceTitle;
        return `
          <div class="erpw-sales-console-sidebar-item">
            <div class="standard-sidebar-item">
              <button
                type="button"
                class="item-anchor erpw-sales-console-sidebar-link${activeClass}"
                data-erpw-sidebar-index="${escapeHtml(indexKey)}"
                aria-label="${escapeHtml(itemLabel)}"
                ${activeState}
                title="${escapeHtml(itemLabel)}"
              >
                <span class="erpw-sales-console-sidebar-icon" aria-hidden="true">${sidebarItemIconMarkup(item)}</span>
                <span class="erpw-sales-console-sidebar-copy">
                  <span class="erpw-sales-console-sidebar-text">${escapeHtml(itemLabel)}</span>
                </span>
              </button>
            </div>
          </div>
        `;
      }).join("");

      return `
        <section class="erpw-sales-console-sidebar-section" data-erpw-sidebar-section="${escapeHtml(section.key || "")}">
          ${showSectionLabels ? `<div class="erpw-sales-console-sidebar-section-label">${escapeHtml(section.label || "Section")}</div>` : ""}
          ${itemsMarkup}
        </section>
      `;
    }).join("");

    wrapper.innerHTML = `
      <div class="erpw-sales-console-sidebar-shell">
        ${utilitiesMarkup}
        ${sectionsMarkup}
      </div>
    `;
    wrapper._erpwSidebarItems = itemIndex;
    wrapper.setAttribute("data-erpw-sidebar-workspace", config.workspaceId);
    wrapper.setAttribute("data-erpw-sidebar-signature", signature);

    wrapper.querySelectorAll("[data-erpw-sales-search-open]").forEach((element) => {
      element.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        if (typeof event.stopImmediatePropagation === "function") event.stopImmediatePropagation();
        openWorkspaceSearch("");
      });
    });
    wrapper.querySelectorAll("[data-erpw-sales-notifications-open]").forEach((element) => {
      element.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        if (typeof event.stopImmediatePropagation === "function") event.stopImmediatePropagation();
        openNativeNotifications();
      });
    });
    wrapper.querySelectorAll("[data-erpw-sidebar-index]").forEach((element) => {
      element.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        if (typeof event.stopImmediatePropagation === "function") event.stopImmediatePropagation();
        const item = wrapper._erpwSidebarItems && wrapper._erpwSidebarItems.get(element.getAttribute("data-erpw-sidebar-index"));
        executeSidebarTarget(item && item.target ? item.target : null);
      });
    });

    return true;
  }

  function syncSidebarNow() {
    const route = getRoute();
    if (!isManagedRoute(route)) {
      clearSidebarArtifacts(route);
      return Promise.resolve(false);
    }

    setManagedBodyState(true);
    setManagedSidebarHeader(true);

    if (!isSalesConsoleHomeRoute(route)) {
      removeGuideItem();
    }

    const activeKey = resolveActiveKey(route);
    const config = workspaceConfig(route);
    const routeSignature = JSON.stringify(route || []);
    const initialContext = contextCoordinator.peek(config.workspaceId) || fallbackContext(route);
    renderSidebar(initialContext, activeKey);
    return loadSidebarContext(route).then((contextPayload) => {
      if (!contextPayload) return false;
      const currentRoute = getRoute();
      const currentConfig = workspaceConfig(currentRoute);
      if (currentConfig.workspaceId !== config.workspaceId || JSON.stringify(currentRoute || []) !== routeSignature) {
        return false;
      }
      return renderSidebar(contextPayload, resolveActiveKey(currentRoute));
    });
  }

  function scheduleSync(delayMs) {
    if (syncTimer) {
      window.clearTimeout(syncTimer);
    }

    let attempts = 0;
    const tick = () => {
      const route = getRoute();
      if (!isManagedRoute(route)) {
        clearSidebarArtifacts(route);
        return;
      }

      if (!ensureManagedSidebarHost().host && attempts < 12) {
        attempts += 1;
        syncTimer = window.setTimeout(tick, 280);
        return;
      }

      syncTimer = null;
      syncSidebarNow();
    };

    syncTimer = window.setTimeout(tick, Number.isFinite(delayMs) ? delayMs : 0);
  }

  function synchronizeSidebarRoute(route, managedSync, unmanagedClear) {
    if (isManagedRoute(route)) return managedSync();
    return unmanagedClear(route);
  }

  function scheduleSyncSeries() {
    [0, 40, 90, 160, 260, 420, 720].forEach((delay) => {
      window.setTimeout(() => {
        const route = getRoute();
        synchronizeSidebarRoute(route, syncSidebarNow, clearSidebarArtifacts);
      }, delay);
    });
  }

  function scheduleMutationSync() {
    if (mutationSyncTimer) return;
    mutationSyncTimer = window.setTimeout(() => {
      mutationSyncTimer = null;
      scheduleSync(0);
    }, 60);
  }

  function bindSidebarMutationObserver() {
    if (sidebarMutationObserver || typeof MutationObserver !== "function" || !document.body) return;
    sidebarMutationObserver = new MutationObserver(() => {
      const route = getRoute();
      if (!isManagedRoute(route)) return;
      if (!document.querySelector("[data-erpw-sales-console-nav='1']") || hasVisibleNativeSidebarArtifacts()) {
        scheduleMutationSync();
      }
    });
    sidebarMutationObserver.observe(document.body, { childList: true, subtree: true });
  }

  function handleWorkspaceSearchShortcut(event) {
    const route = getRoute();
    if (!isManagedRoute(route)) return;
    const isSearchShortcut = (event.ctrlKey || event.metaKey) && !event.shiftKey && !event.altKey && String(event.key || "").toLowerCase() === "k";
    if (!isSearchShortcut) return;
    event.preventDefault();
    event.stopPropagation();
    if (typeof event.stopImmediatePropagation === "function") {
      event.stopImmediatePropagation();
    }
    openWorkspaceSearch("");
  }

  function handleSidebarRouteChange(route, managedSchedule, unmanagedClear, deferManaged) {
    if (!isManagedRoute(route)) {
      contextCoordinator.clear();
    } else {
      contextCoordinator.clear(workspaceConfig(route).workspaceId);
    }
    if (!isManagedRoute(route)) {
      unmanagedClear(route);
      return false;
    }
    managedSchedule();
    if (typeof deferManaged === "function") deferManaged(managedSchedule);
    return true;
  }

  function handleCurrentRouteChange() {
    resetWorkspaceSearch();
    if (searchDialog && typeof searchDialog.hide === "function") {
      searchRestoreFocusOnClose = false;
      searchDialog.hide();
    }
    const route = getRoute();
    handleSidebarRouteChange(
      route,
      scheduleSyncSeries,
      clearSidebarArtifacts,
      (callback) => {
        if (typeof frappe.after_ajax === "function") frappe.after_ajax(callback);
      }
    );
  }

  function bindListeners() {
    if (listenersBound) return;
    listenersBound = true;
    if (frappe.router && typeof frappe.router.on === "function") {
      frappe.router.on("change", handleCurrentRouteChange);
    }
    window.addEventListener("hashchange", handleCurrentRouteChange);
    window.addEventListener("popstate", handleCurrentRouteChange);
    document.addEventListener("readystatechange", () => scheduleSync(10));
    if (document.body) {
      bindSidebarMutationObserver();
    } else {
      document.addEventListener("DOMContentLoaded", bindSidebarMutationObserver, { once: true });
    }
    window.addEventListener("keydown", handleWorkspaceSearchShortcut, true);
    document.addEventListener("keydown", handleWorkspaceSearchShortcut, true);
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = Object.freeze({
      SIDEBAR_CONTEXT_SCHEMA_VERSION,
      MANAGED_SEARCH_SCHEMA_VERSION,
      normalizeManagedSearchQuery,
      createManagedSearchGenerationCoordinator,
      managedSearchRouteIdentity,
      managedSearchTargetAllowed,
      createManagedSearchEnvelope,
      managedSearchEnvelopeCurrent,
      dispatchManagedSearchTarget,
      createWorkspaceContextCoordinator,
      MANAGED_DETAIL_ROUTE_ACTIVE_KEYS,
      managedDetailRouteActiveKey,
      applyManagedSearchActiveState,
      bindManagedSearchResultFocus,
      managedDialogFocusableNodes,
      containManagedDialogFocus,
      managedSearchResultsMarkup,
      managedSearchShellMarkup,
      handleSidebarRouteChange,
      sidebarPayloadMatchesWorkspace,
      financeSidebarCopyValid,
      isManagedRoute,
      resolveActiveKey,
      fallbackContext,
      ensureStyles,
      renderSidebar,
      sidebarTargetAllowed,
      synchronizeSidebarRoute,
      setManagedSidebarHeader,
      restoreNativeAttribute,
    });
    return;
  }

  bindListeners();
  scheduleSyncSeries();

  delete sidebarRuntime.executeTarget;
  root.erpWorkspaceConsoleSidebar = Object.assign(sidebarRuntime, {
    executeSidebarTarget,
    createManagedSearchGenerationCoordinator,
    primePayload,
    refresh() {
      contextCoordinator.clear(workspaceConfig(getRoute()).workspaceId);
      scheduleSyncSeries();
    },
    syncSidebarNow,
  });
})();
