(function () {
  let footerPatched = false;
  let sidebarPatched = false;
  let formRenderSidebarGuardPatched = false;
  let routeChromeBound = false;
  let gridActionLabelsBound = false;
  let gridActionLabelsObserver = null;
  let gridActionLabelNormalizeFrame = null;
  let draftLookupBound = false;
  let activeDraftLookupInput = null;
  let draftLookupPositionFrame = null;
  let draftLookupMirror = null;
  let draftLookupMirrorNativeOptions = [];
  let activeDraftLookupMeta = null;
  let draftLookupRequestToken = 0;
  let draftLookupResultCache = Object.create(null);
  let draftLookupPendingCache = Object.create(null);

  function salesWorkspaceDefinition() {
    const registry = window.erpWorkspaceUiWorkspaceRegistry || {};
    return typeof registry.sales === "function" ? registry.sales() : null;
  }

  function salesWorkspaceRoutes() {
    const workspace = salesWorkspaceDefinition();
    return workspace && workspace.routes ? workspace.routes : {};
  }

  function salesWorkspaceTitle() {
    const workspace = salesWorkspaceDefinition();
    return (workspace && workspace.title) || "Sales Console";
  }

  function resolveLifecycleElement(value) {
    if (!value) return null;
    if (value instanceof HTMLElement) return value;
    if (value.jquery && value.length) return value.get(0);
    if (value[0] instanceof HTMLElement) return value[0];
    return null;
  }

  function lifecycleReturn(node) {
    if (!node) return window.jQuery ? window.jQuery() : null;
    return window.jQuery ? window.jQuery(node) : node;
  }

  function resolveManagedPageBody(page, wrapper) {
    const pageBody = page && page.body ? resolveLifecycleElement(page.body) : null;
    if (pageBody) return pageBody;
    const wrapperNode = resolveLifecycleElement(wrapper);
    if (!wrapperNode) return null;
    return wrapperNode.querySelector(".layout-main-section, .page-body, .page-content") || wrapperNode;
  }

  function markManagedRouteNode(node, settings) {
    if (!(node instanceof HTMLElement)) return;
    node.setAttribute("data-erpw-managed-route-host", "true");
    if (settings && settings.routeGroup) {
      node.setAttribute("data-erpw-route-group", String(settings.routeGroup));
    }
    if (settings && settings.routeKind) {
      node.setAttribute("data-erpw-route-kind", String(settings.routeKind));
    }
  }

  function clearManagedPageBody(parent, keepNode) {
    if (!(parent instanceof HTMLElement)) return;
    Array.from(parent.children).forEach((child) => {
      if (child !== keepNode && child.parentNode === parent) {
        child.remove();
      }
    });
  }

  function ensureManagedHost(options) {
    const settings = options && typeof options === "object" ? options : {};
    const parent = resolveManagedPageBody(settings.page, settings.wrapper);
    if (!parent) return lifecycleReturn(null);
    const hostClass = String(settings.hostClass || "").replace(/^\./, "").trim();
    let host = null;
    if (hostClass) {
      host = Array.from(parent.children).find((child) => child.classList && child.classList.contains(hostClass)) || null;
    }
    if (!host) {
      host = document.createElement(settings.tagName || "section");
      if (hostClass) host.className = hostClass;
    }
    markManagedRouteNode(host, settings);
    clearManagedPageBody(parent, host);
    if (host.parentNode !== parent) parent.appendChild(host);
    return lifecycleReturn(host);
  }

  function replaceManagedContent(options) {
    const settings = options && typeof options === "object" ? options : {};
    const parent = resolveManagedPageBody(settings.page, settings.wrapper);
    const content = resolveLifecycleElement(settings.content);
    if (!parent || !content) return lifecycleReturn(null);
    markManagedRouteNode(content, settings);
    parent.textContent = "";
    parent.appendChild(content);
    return lifecycleReturn(content);
  }

  window.erpWorkspaceUiRouteLifecycle = Object.assign(window.erpWorkspaceUiRouteLifecycle || {}, {
    ensureManagedHost,
    replaceManagedContent,
  });

  function escapeRegExp(value) {
    return String(value || "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function salesWorkspaceRoute(routeKind, fallback) {
    const routes = salesWorkspaceRoutes();
    return routes[String(routeKind || "")] || fallback || "";
  }

  function salesWorkspaceDeskPath(routeKind, fallback) {
    const route = salesWorkspaceRoute(routeKind, fallback);
    return route ? `/desk/${route}` : "";
  }

  function isSalesWorkspacePath(path, routeKind, fallback) {
    const route = salesWorkspaceRoute(routeKind, fallback);
    if (!route) return false;
    return new RegExp(`^/(?:desk|app)/${escapeRegExp(route)}(?:/|$)`).test(String(path || ""));
  }

  function isSalesWorkspaceLauncherPath(path) {
    return isSalesWorkspacePath(path, "launcher", "sales-console-home");
  }

  function normalizeFrappeRouteOptions() {
    if (!window.frappe) return null;
    const current = frappe.route_options;
    if (!current || typeof current !== "object") {
      frappe.route_options = {};
      return frappe.route_options;
    }
    return current;
  }

  function wrapRouteOptionsMethod(owner, methodName) {
    if (!owner || typeof owner[methodName] !== "function" || owner[methodName].__erpwRouteOptionsGuardPatched) {
      return false;
    }
    const original = owner[methodName];
    const wrapped = function () {
      normalizeFrappeRouteOptions();
      const result = original.apply(this, arguments);
      normalizeFrappeRouteOptions();
      return result;
    };
    wrapped.__erpwRouteOptionsGuardPatched = true;
    wrapped.__erpwOriginal = original;
    owner[methodName] = wrapped;
    return true;
  }

  function patchRouteOptionsNullSafety() {
    if (!window.frappe) return false;
    normalizeFrappeRouteOptions();
    let patched = wrapRouteOptionsMethod(frappe, "set_route");
    if (frappe.router) {
      patched = wrapRouteOptionsMethod(frappe.router, "trigger") || patched;
      patched = wrapRouteOptionsMethod(frappe.router, "set_route") || patched;
    }
    return patched;
  }

  function routeSalesLauncherToOverview() {
    const path = window.location && window.location.pathname ? window.location.pathname : "";
    if (!isSalesWorkspaceLauncherPath(path)) return false;
    if (!window.frappe || typeof frappe.set_route !== "function") return false;
    const targetRoute = salesWorkspaceRoute("home", "sales-console");
    if (!targetRoute) return false;
    const currentRoute = safeCurrentRouteString();
    if (currentRoute === targetRoute) return true;
    normalizeFrappeRouteOptions();
    frappe.set_route(targetRoute);
    return true;
  }

  function scheduleSalesLauncherHandoff() {
    routeSalesLauncherToOverview();
    window.setTimeout(routeSalesLauncherToOverview, 0);
    window.setTimeout(routeSalesLauncherToOverview, 80);
    window.setTimeout(routeSalesLauncherToOverview, 240);
    window.setTimeout(routeSalesLauncherToOverview, 700);
  }

  function matchesChildExecutionPath(slug) {
    const path = window.location.pathname || "";
    return new RegExp(`^/(?:desk|app)/${slug}/[^/]+(?:/|$)`).test(path);
  }

  function isSalesOrderRoute() {
    return matchesChildExecutionPath("sales-order");
  }

  function isQuotationRoute() {
    return matchesChildExecutionPath("quotation");
  }

  function isDeliveryNoteRoute() {
    return matchesChildExecutionPath("delivery-note");
  }

  function isSalesInvoiceRoute() {
    return matchesChildExecutionPath("sales-invoice");
  }

  function isChildExecutionRoute() {
    return isSalesOrderRoute() || isQuotationRoute() || isDeliveryNoteRoute() || isSalesInvoiceRoute();
  }

	  function isChildExecutionDocType(doctype) {
	    return doctype === "Sales Order" || doctype === "Quotation" || doctype === "Delivery Note" || doctype === "Sales Invoice";
	  }

	  function managedSalesConsoleDirectoryTarget(label) {
	    const normalized = String(label || "").replace(/\s+/g, " ").trim().toLowerCase();
	    const targets = {
	      quotation: { doctype: "Quotation", queue_key: "quotation_directory" },
	      quotations: { doctype: "Quotation", queue_key: "quotation_directory" },
	      "sales order": { doctype: "Sales Order", queue_key: "sales_order_directory" },
	      "sales orders": { doctype: "Sales Order", queue_key: "sales_order_directory" },
	      "delivery note": { doctype: "Delivery Note", queue_key: "sales_order_directory" },
	      "delivery notes": { doctype: "Delivery Note", queue_key: "sales_order_directory" },
	      "sales invoice": { doctype: "Sales Invoice", queue_key: "sales_order_directory" },
	      "sales invoices": { doctype: "Sales Invoice", queue_key: "sales_order_directory" },
	      customer: { doctype: "Customer", queue_key: "customer_directory" },
	      customers: { doctype: "Customer", queue_key: "customer_directory" },
	      "customer detail": { doctype: "Customer", queue_key: "customer_directory" },
	      "customer details": { doctype: "Customer", queue_key: "customer_directory" },
	      item: { doctype: "Item", queue_key: "item_directory" },
	      items: { doctype: "Item", queue_key: "item_directory" },
	      "item detail": { doctype: "Item", queue_key: "item_directory" },
	      "item details": { doctype: "Item", queue_key: "item_directory" },
	    };
	    return targets[normalized] || null;
	  }

	  function managedSalesConsoleHomeTarget(label, href) {
	    const normalized = String(label || "").replace(/\s+/g, " ").trim().toLowerCase();
	    const homeLabels = new Set([
	      "accounts",
	      "erpnext",
	      "sales console",
	      "sales console report",
	      "sales console worklist",
	      "selling",
	      "stock",
	    ]);
	    if (homeLabels.has(normalized)) {
	      return { kind: "home" };
	    }

	    const rawHref = String(href || "").trim();
	    if (!rawHref || rawHref === "#") return null;

	    let path = rawHref;
	    try {
	      path = new URL(rawHref, window.location.origin).pathname || rawHref;
	    } catch (error) {
	      path = rawHref.split(/[?#]/)[0] || rawHref;
	    }
	    const normalizedPath = String(path || "").replace(/\/+$/, "").toLowerCase();
	    const workspaceHomeRoutes = [
	      "accounts",
	      "selling",
	      "stock",
	      salesWorkspaceRoute("launcher", "sales-console-home"),
	      salesWorkspaceRoute("home", "sales-console"),
	      salesWorkspaceRoute("worklist", "sales-console-worklist"),
	      salesWorkspaceRoute("report", "sales-console-report"),
	    ].filter(Boolean);
	    if (workspaceHomeRoutes.some((route) => new RegExp(`^/(?:desk|app)/${escapeRegExp(route)}$`).test(normalizedPath))) {
	      return { kind: "home" };
	    }
	    return null;
	  }

	  function isManagedSalesConsoleRoute() {
	    const path = window.location.pathname || "";
	    return isChildExecutionRoute()
	      || isSalesWorkspaceLauncherPath(path)
	      || isSalesWorkspacePath(path, "home", "sales-console")
	      || isSalesWorkspacePath(path, "worklist", "sales-console-worklist")
	      || isSalesWorkspacePath(path, "report", "sales-console-report");
	  }

	  function routeToManagedDirectory(target) {
	    if (!target || !target.queue_key) return false;
	    const routes = salesWorkspaceRoutes();
	    const helpers = window.erpWorkspaceUiChildPage && window.erpWorkspaceUiChildPage.helpers;
	    if (
	      helpers
	      && typeof helpers.routeToSalesConsoleTarget === "function"
	      && helpers.routeToSalesConsoleTarget({ kind: "worklist", queue_key: target.queue_key })
	    ) {
	      return true;
	    }
	    frappe.set_route(routes.worklist || "sales-console-worklist", String(target.queue_key).replace(/_/g, "-"));
	    return true;
	  }

	  function routeToManagedBreadcrumbTarget(target) {
	    if (!target) return false;
	    const routes = salesWorkspaceRoutes();
	    if (target.kind === "home") {
	      frappe.set_route(routes.home || "sales-console");
	      return true;
	    }
	    return routeToManagedDirectory(target);
	  }

	  function managedDirectoryTargetFromQueue(queueKey) {
	    const targets = {
	      quotation_directory: { doctype: "Quotation", queue_key: "quotation_directory" },
	      sales_order_directory: { doctype: "Sales Order", queue_key: "sales_order_directory" },
	      customer_directory: { doctype: "Customer", queue_key: "customer_directory" },
	      item_directory: { doctype: "Item", queue_key: "item_directory" },
	    };
	    return targets[String(queueKey || "")] || null;
	  }

	  function normalizeBreadcrumbLabel(link) {
	    if (!(link instanceof HTMLElement)) return "";
	    return String(link.textContent || "")
	      .replace(/\s+/g, " ")
	      .replace(/^\/+/, "")
	      .trim();
	  }

	  function breadcrumbTargetFromLink(link) {
	    if (!(link instanceof HTMLElement)) return null;
	    const label = normalizeBreadcrumbLabel(link);
	    return managedSalesConsoleDirectoryTarget(label)
	      || managedSalesConsoleHomeTarget(label, link.getAttribute("href") || "");
	  }

	  function breadcrumbTargetFromDataset(link) {
	    if (!(link instanceof HTMLElement)) return null;
	    const kind = String(link.getAttribute("data-erpw-sales-owned-route-kind") || "").trim();
	    if (kind === "home") return { kind: "home" };
	    return managedDirectoryTargetFromQueue(link.getAttribute("data-erpw-sales-owned-route"));
	  }

	  function isSalesConsoleCustomChromeRoute() {
	    if (isChildExecutionRoute()) return false;
	    const path = window.location.pathname || "";
	    return isSalesWorkspaceLauncherPath(path)
	      || isSalesWorkspacePath(path, "home", "sales-console")
	      || isSalesWorkspacePath(path, "worklist", "sales-console-worklist")
	      || isSalesWorkspacePath(path, "report", "sales-console-report");
	  }

	  function routeSegmentsFromPath() {
	    const path = String(window.location.pathname || "").replace(/^\/(?:desk|app)\//, "");
	    return path.split("/").map((part) => {
	      try {
	        return decodeURIComponent(part || "");
	      } catch (error) {
	        return part || "";
	      }
	    }).filter(Boolean);
	  }

	  function normalizeRouteKey(value) {
	    return String(value || "").trim().replace(/-/g, "_");
	  }

	  function humanizeRouteKey(value) {
	    return String(value || "")
	      .replace(/[-_]+/g, " ")
	      .replace(/\s+/g, " ")
	      .trim()
	      .replace(/\b\w/g, (letter) => letter.toUpperCase()) || "Workspace";
	  }

	  function currentSalesConsoleChromeContext(options) {
	    const routes = salesWorkspaceRoutes();
	    const settings = options && typeof options === "object" ? options : {};
	    const segments = routeSegmentsFromPath();
	    const pageKey = segments[0] || "";
	    const queueLabels = {
	      quotation_directory: "Quotations",
	      sales_order_directory: "Sales Orders",
	      customer_directory: "Customers",
	      item_directory: "Items",
	      customer_detail: "Customer Detail",
	      customer_editor: "Customer Profile",
	      item_detail: "Item Detail",
	      open_orders: "Open Sales Orders",
	      sales_orders_pending_fulfillment: "Orders Pending Fulfillment",
	      partially_delivered_orders: "Partially Delivered Orders",
	      orders_due_soon: "Orders Due Soon",
	      quotations_waiting_action: "Quotations Waiting for Action",
	      expiring_quotations: "Quotations Nearing Expiry",
	      orders_blocked_by_approval: "Orders Blocked by Approval",
	      quotations_awaiting_approval: "Quotations Awaiting Approval",
	      customer_follow_up_tasks: "Customer Follow-Up Tasks",
	      invoices_outstanding: "Invoices Outstanding",
	      sales_returns_in_progress: "Sales Returns in Progress",
	    };
	    const reportLabels = {
	      sales_analytics: "Sales Analytics",
	      sales_order_analysis: "Sales Order Analysis",
	      trend_analysis: "Trend Analysis",
	      quotation_trends: "Trend Analysis",
	      collections_status: "Collections Status",
	      payment_terms_status_sales_order: "Collections Status",
	      item_wise_sales_history: "Item-wise Sales History",
	      lost_quotations: "Lost Quotations",
	    };

	    const queueKey = pageKey === (routes.worklist || "sales-console-worklist") ? normalizeRouteKey(segments[1] || "") : "";
	    let leafLabel = settings.title || settings.leafLabel || "";
	    if (!leafLabel && pageKey === (routes.worklist || "sales-console-worklist")) {
	      leafLabel = queueLabels[queueKey] || humanizeRouteKey(queueKey || "worklist");
	    }
	    if (!leafLabel && pageKey === (routes.report || "sales-console-report")) {
	      const reportKey = normalizeRouteKey(segments[1] || "");
	      leafLabel = reportLabels[reportKey] || humanizeRouteKey(reportKey || "report");
	    }
	    if (!leafLabel) {
	      leafLabel = "Overview";
	    }

	    const detailParents = {
	      customer_detail: {
	        label: "Customers",
	        route: `${salesWorkspaceDeskPath("worklist", "sales-console-worklist")}/customer-directory`,
	        queue_key: "customer_directory",
	      },
	      item_detail: {
	        label: "Items",
	        route: `${salesWorkspaceDeskPath("worklist", "sales-console-worklist")}/item-directory`,
	        queue_key: "item_directory",
	      },
	    };
	    const crumbs = [
	      {
	        label: salesWorkspaceTitle(),
	        route: routes.homePath || salesWorkspaceDeskPath("home", "sales-console"),
	        kind: "home",
	      },
	    ];
	    const detailParent = segments[2] ? detailParents[queueKey] : null;
	    if (detailParent && leafLabel !== detailParent.label) {
	      crumbs.push(detailParent);
	    }
	    crumbs.push({
	      label: leafLabel,
	      route: "",
	      current: true,
	    });

	    return {
	      documentTitle: settings.documentTitle || leafLabel,
	      crumbs,
	    };
	  }

	  function safeCurrentRouteString() {
	    try {
	      if (!window.frappe) return "";
	      const route = frappe.get_route ? frappe.get_route() : null;
	      if (Array.isArray(route) && route.length && frappe.get_route_str) {
	        return frappe.get_route_str(route);
	      }
	      return "";
	    } catch (error) {
	      return "";
	    }
	  }

	  function resolveSalesConsoleChromeRoots(page) {
	    const roots = [];
	    const pageWrapper = page && page.wrapper
	      ? (page.wrapper.jquery ? page.wrapper.get(0) : page.wrapper)
	      : null;
	    if (pageWrapper instanceof HTMLElement) {
	      roots.push(pageWrapper);
	    }

	    const routeStr = safeCurrentRouteString();
	    const routePage = routeStr && window.frappe && frappe.ui && frappe.ui.pages
	      ? frappe.ui.pages[routeStr]
	      : null;
	    const routeWrapper = routePage && routePage.wrapper
	      ? (routePage.wrapper.jquery ? routePage.wrapper.get(0) : routePage.wrapper)
	      : null;
	    if (routeWrapper instanceof HTMLElement && !roots.includes(routeWrapper)) {
	      roots.push(routeWrapper);
	    }

	    if (!roots.length) {
	      Array.from(document.querySelectorAll(".page-head")).forEach((head) => {
	        if (!(head instanceof HTMLElement)) return;
	        const rect = head.getBoundingClientRect();
	        const style = window.getComputedStyle(head);
	        if (rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden") {
	          roots.push(head);
	        }
	      });
	    }
	    return roots;
	  }

	  function syncSalesConsoleNativeChrome(options) {
	    if (!isSalesConsoleCustomChromeRoute()) return false;
	    const settings = options && typeof options === "object" ? options : {};
	    const context = currentSalesConsoleChromeContext(settings);
	    const roots = resolveSalesConsoleChromeRoots(settings.page);
	    let synced = false;

	    roots.forEach((rootNode) => {
	      const breadcrumbLists = rootNode instanceof HTMLElement && rootNode.matches(".page-head")
	        ? Array.from(rootNode.querySelectorAll(".navbar-breadcrumbs"))
	        : Array.from(rootNode.querySelectorAll(".page-head .navbar-breadcrumbs"));
	      breadcrumbLists.forEach((list) => {
	        if (!(list instanceof HTMLElement)) return;
	        list.textContent = "";
	        list.setAttribute("data-erpw-sales-console-breadcrumbs", "1");
	        context.crumbs.forEach((crumb, index) => {
	          const item = document.createElement("li");
	          const link = document.createElement("a");
	          const isCurrent = Boolean(crumb.current || index === context.crumbs.length - 1);
	          link.textContent = crumb.label;
	          if (crumb.route && !isCurrent) {
	            link.setAttribute("href", crumb.route);
	          } else {
	            link.setAttribute("href", "");
	            link.setAttribute("aria-current", "page");
	          }
	          if (crumb.kind === "home") {
	            link.setAttribute("data-erpw-sales-owned-route-kind", "home");
	          }
	          if (crumb.queue_key) {
	            link.setAttribute("data-erpw-sales-owned-route-kind", "directory");
	            link.setAttribute("data-erpw-sales-owned-route", crumb.queue_key);
	          }
	          if (isCurrent) {
	            link.classList.add("title-text");
	            link.setAttribute("data-erpw-sales-current-crumb", "1");
	          }
	          item.appendChild(link);
	          list.appendChild(item);
	        });
	        synced = true;
	      });

	      const titleNodes = rootNode instanceof HTMLElement && rootNode.matches(".page-head")
	        ? Array.from(rootNode.querySelectorAll(".page-title .title-text, .title-area .title-text"))
	        : Array.from(rootNode.querySelectorAll(".page-head .page-title .title-text, .page-head .title-area .title-text"));
	      titleNodes.forEach((node) => {
	        if (!(node instanceof HTMLElement)) return;
	        if (node.closest(".navbar-breadcrumbs")) return;
	        node.textContent = context.documentTitle || salesWorkspaceTitle();
	        node.setAttribute("data-erpw-sales-console-title", "1");
	        synced = true;
	      });
	    });

	    if (synced) {
	      if (document.body) {
	        document.body.classList.remove("no-breadcrumbs");
	      }
	      if (window.frappe && frappe.utils && typeof frappe.utils.set_title === "function") {
	        frappe.utils.set_title(context.documentTitle || salesWorkspaceTitle());
	      }
	    }
	    return synced;
	  }

	  function syncSalesConsoleBreadcrumbLinks() {
	    if (!isManagedSalesConsoleRoute()) return;
	    document.querySelectorAll(".breadcrumb a, .breadcrumbs a, .page-title a").forEach((link) => {
	      if (!(link instanceof HTMLElement)) return;
	      const target = breadcrumbTargetFromLink(link);
	      if (!target) return;
	      if (target.kind === "home") {
	        link.setAttribute("data-erpw-sales-owned-route-kind", "home");
	        link.removeAttribute("data-erpw-sales-owned-route");
	        link.setAttribute("href", salesWorkspaceRoutes().homePath || salesWorkspaceDeskPath("home", "sales-console"));
	        return;
	      }
	      link.setAttribute("data-erpw-sales-owned-route-kind", "directory");
	      link.setAttribute("data-erpw-sales-owned-route", target.queue_key);
	      link.setAttribute("href", `${salesWorkspaceDeskPath("worklist", "sales-console-worklist")}/${String(target.queue_key).replace(/_/g, "-")}`);
	    });
	  }

	  function bindSalesConsoleBreadcrumbOwnership() {
	    if (document.__erpwSalesBreadcrumbOwnershipBound) return;
	    document.__erpwSalesBreadcrumbOwnershipBound = true;
	    document.addEventListener("click", (event) => {
	      if (!isManagedSalesConsoleRoute()) return;
	      const link = event.target && event.target.closest
	        ? event.target.closest(".breadcrumb a, .breadcrumbs a, .page-title a")
	        : null;
	      if (!(link instanceof HTMLElement)) return;
	      const target = breadcrumbTargetFromDataset(link) || breadcrumbTargetFromLink(link);
	      if (!target) return;
	      event.preventDefault();
	      event.stopPropagation();
	      routeToManagedBreadcrumbTarget(target);
	    }, true);
	  }

	  window.erpWorkspaceUiSalesConsoleChrome = Object.assign(window.erpWorkspaceUiSalesConsoleChrome || {}, {
	    sync: syncSalesConsoleNativeChrome,
	  });


  function applySalesOrderRouteChrome() {
    const isSalesOrder = isChildExecutionRoute();
    if (!isSalesOrder) {
      lastChildExecutionScrollPath = null;
    }
    const root = document.documentElement;
    const body = document.body;
    const sidebar = document.querySelector(".body-sidebar");
    const sidebarContainer = document.querySelector(".body-sidebar-container");

    [root, body, sidebar, sidebarContainer].forEach((node) => {
      if (!node) return;
      node.classList.toggle("erpw-route-sales-order-ready", isSalesOrder);
      node.classList.remove("erpw-route-sales-order-prep");
      node.classList.remove("erpw-so-left-sidebar-compact");
    });

  }

  const childPageBootstrapRegistry = {};
  let childPageBootstrapWatcherToken = 0;
  let lastChildExecutionScrollPath = null;
  let childExecutionScrollToken = 0;

  function elementHasMeaningfulVisibleContent(node) {
    if (!(node instanceof HTMLElement)) return false;

    const visibleDescendants = Array.from(node.querySelectorAll('*')).filter((child) => {
      if (!(child instanceof HTMLElement)) return false;
      const style = window.getComputedStyle(child);
      return style.display !== 'none' && style.visibility !== 'hidden' && !child.hidden;
    });

    const visibleText = visibleDescendants
      .map((child) => String(child.textContent || '').replace(/\s+/g, ' ').trim())
      .join(' ')
      .replace(/\s+/g, ' ')
      .trim();
    if (visibleText) return true;

    return visibleDescendants.some((child) => child.matches('button, a[href], input:not([type="hidden"]), select, textarea, .btn, .indicator-pill, .chart-wrapper, .widget, .number-widget'));
  }

  function collapseEmptyChildTopChrome() {
    if (!isChildExecutionRoute()) return;

    const candidates = document.querySelectorAll(
      '.layout-main-section .form-dashboard,'
      + '.layout-main-section .form-dashboard-section,'
      + '.layout-main-section .form-message-container,'
      + '.form-page .form-dashboard,'
      + '.form-page .form-dashboard-section,'
      + '.form-page .form-message-container'
    );

    candidates.forEach((node) => {
      if (!(node instanceof HTMLElement)) return;
      const meaningful = elementHasMeaningfulVisibleContent(node);
      node.classList.toggle('erpw-child-empty-top-strip', !meaningful);
    });
  }

  function forceChildExecutionHeaderTop() {
    try {
      const mainSection = document.querySelector(".main-section");
      const layoutMainSection = document.querySelector(".layout-main-section");
      const scrollingElement = document.scrollingElement || document.documentElement || document.body;

      if (mainSection) {
        mainSection.scrollTop = 0;
      }
      if (layoutMainSection) {
        layoutMainSection.scrollTop = 0;
      }
      if (scrollingElement) {
        scrollingElement.scrollTop = 0;
      }
      if (document.body) {
        document.body.scrollTop = 0;
      }
      if (document.documentElement) {
        document.documentElement.scrollTop = 0;
      }
      window.scrollTo(0, 0);
    } catch (error) {
      // Ignore scroll reset failures and keep route flow usable.
    }
  }

  function scrollChildExecutionRouteTop() {
    const path = window.location.pathname || "";
    if (!path || lastChildExecutionScrollPath === path) return;
    lastChildExecutionScrollPath = path;
    const scrollToken = ++childExecutionScrollToken;
    [0, 90, 220, 460, 900].forEach((delay) => {
      window.setTimeout(() => {
        if (scrollToken !== childExecutionScrollToken) return;
        if (!isChildExecutionRoute()) return;
        if ((window.location.pathname || "") !== path) return;
        forceChildExecutionHeaderTop();
      }, delay);
    });
  }

  function hasRenderedChildShell(frm) {
    const rootNode = frm && (
      frm.page && frm.page.main
        ? frm.page.main
        : frm.layout && frm.layout.wrapper
          ? frm.layout.wrapper
          : frm.wrapper || frm.$wrapper || null
    );
    const rootElement = rootNode && rootNode.jquery ? rootNode.get(0) : rootNode;
    const scopedRoot = rootElement instanceof HTMLElement
      ? (rootElement.closest(".layout-main-section, .form-page, .page-content") || rootElement)
      : null;
    const shell = scopedRoot
      ? scopedRoot.querySelector(".erpw-child-shell")
      : document.querySelector(".erpw-child-shell");

    if (!(shell instanceof HTMLElement)) return false;
    if (!shell.children.length) return false;
    return !shell.querySelector(".erpw-so-shell-skeleton");
  }

  function runActiveChildPageBootstrap() {
    const frm = window.cur_frm;
    if (!frm || !frm.doctype || !isChildExecutionDocType(frm.doctype)) {
      return false;
    }

    if (frm.__erpwContextRenderedName === (frm.doc && frm.doc.name) && hasRenderedChildShell(frm)) {
      return true;
    }

    const bootstrap = childPageBootstrapRegistry[frm.doctype];
    if (typeof bootstrap !== "function") {
      return false;
    }

    try {
      const booted = bootstrap() === true;
      if (booted) {
        scrollChildExecutionRouteTop();
      }
      return booted;
    } catch (error) {
      return false;
    }
  }

  function ensureActiveChildPageBootstrap(options) {
    const settings = Object.assign({
      maxAttempts: 18,
    }, options || {});

    const watcherToken = ++childPageBootstrapWatcherToken;
    let attempts = 0;

    const tick = () => {
      if (watcherToken !== childPageBootstrapWatcherToken) return;
      if (!isChildExecutionRoute()) return;
      if (runActiveChildPageBootstrap()) return;

      attempts += 1;
      if (attempts >= settings.maxAttempts) return;

      const delay = attempts < 6 ? 120 : attempts < 12 ? 260 : 420;
      window.setTimeout(tick, delay);
    };

    tick();
  }

  function scheduleActiveChildPageBootstrap() {
    [0, 140, 360, 720].forEach((delay) => {
      window.setTimeout(runActiveChildPageBootstrap, delay);
    });
    ensureActiveChildPageBootstrap({ maxAttempts: 20 });
  }

  function bindRouteChrome() {
    if (routeChromeBound) return;
    routeChromeBound = true;

	    const syncSoon = () => {
	      window.requestAnimationFrame(() => {
	        applySalesOrderRouteChrome();
	        collapseEmptyChildTopChrome();
	        bindSalesConsoleBreadcrumbOwnership();
		        syncSalesConsoleNativeChrome();
	        syncSalesConsoleBreadcrumbLinks();
		        ensureChildGridActionLabels();
	        bindDraftLookupSurface();
        prewarmDraftLookupDefaults();
        scheduleDraftLookupPositioning();
        ensureActiveChildPageBootstrap({ maxAttempts: 20 });
      });
    };

    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;

    history.pushState = function () {
      const result = originalPushState.apply(this, arguments);
      syncSoon();
      return result;
    };

    history.replaceState = function () {
      const result = originalReplaceState.apply(this, arguments);
      syncSoon();
      return result;
    };

    window.addEventListener("popstate", syncSoon);
    window.addEventListener("hashchange", syncSoon);
    window.addEventListener("resize", syncSoon);
    document.addEventListener("readystatechange", syncSoon);

    syncSoon();
    setTimeout(syncSoon, 0);
    setTimeout(syncSoon, 120);
    setTimeout(syncSoon, 320);
  }

  function ensureSupportHeadMarkup($wrapper) {
    if (!$wrapper || !$wrapper.length) return;

    let $head = $wrapper.find(".erpw-so-support-head").first();
    if (!$head.length) {
      $head = $(`
        <div class="erpw-so-support-head">
          <div class="erpw-so-support-copy">
            <div class="erpw-so-support-title">Activity & Comments</div>
            <div class="erpw-so-support-note">Comments stay available. Expand activity only when you need deeper audit history.</div>
          </div>
          <button type="button" class="erpw-so-support-toggle" aria-expanded="false">
            <span class="erpw-so-support-toggle-text">Show Full Activity</span>
            <span class="erpw-so-support-toggle-icon" aria-hidden="true"></span>
          </button>
        </div>
      `);
      $wrapper.prepend($head);
      return;
    }

    if (!$head.find(".erpw-so-support-copy").length) {
      $head.prepend(`
        <div class="erpw-so-support-copy">
          <div class="erpw-so-support-title">Activity & Comments</div>
          <div class="erpw-so-support-note">Comments stay available. Expand activity only when you need deeper audit history.</div>
        </div>
      `);
    }

    if (!$head.find(".erpw-so-support-toggle").length) {
      $head.append(`
        <button type="button" class="erpw-so-support-toggle" aria-expanded="false">
          <span class="erpw-so-support-toggle-text">Show Full Activity</span>
          <span class="erpw-so-support-toggle-icon" aria-hidden="true"></span>
        </button>
      `);
    }
  }

  function countSelectedGridRows(section) {
    if (!(section instanceof Element)) return 0;

    const selectors = [
      '.grid-row-check:checked',
      '.grid-row-check.checked',
      '.grid-body input[type="checkbox"]:checked',
      '.grid-static-col input[type="checkbox"]:checked',
      '.rows input[type="checkbox"]:checked',
      '.grid-row input[type="checkbox"]:checked',
    ];

    const nodes = new Set();
    selectors.forEach((selector) => {
      section.querySelectorAll(selector).forEach((node) => nodes.add(node));
    });
    return nodes.size;
  }

  function resetGridActionLabel(button) {
    if (!(button instanceof HTMLElement)) return;
    button.querySelectorAll('.erpw-grid-action-label').forEach((node) => node.remove());
    button.classList.remove('erpw-grid-action-labeled', 'erpw-grid-action-force-label');
    button.removeAttribute('data-erpw-action-label');
  }

  function syncNativeDeleteButton(button, selectedRows) {
    if (!(button instanceof HTMLElement)) return;

    resetGridActionLabel(button);
    button.setAttribute('aria-label', 'Delete row');
    button.setAttribute('title', 'Delete row');
    button.removeAttribute('data-erpw-action-label');
    button.style.removeProperty('display');
    button.style.setProperty('background-color', 'rgb(255, 255, 255)', 'important');
    button.style.setProperty('border-color', 'rgba(226, 232, 240, 0.82)', 'important');
    button.style.setProperty('color', 'rgb(56, 56, 56)', 'important');
    button.style.setProperty('-webkit-text-fill-color', 'rgb(56, 56, 56)', 'important');

    const currentText = String(button.textContent || '').replace(/\s+/g, ' ').trim();
    if (selectedRows > 0 && !currentText) {
      button.textContent = 'Delete row';
    }
  }

  function normalizeGridActionLabels(scope) {
    if (!isChildExecutionRoute()) return;

    collapseEmptyChildTopChrome();

    const rootNode = scope && typeof scope.querySelectorAll === 'function'
      ? scope
      : document;
    const footers = rootNode.querySelectorAll(
      '.erpw-so-form-enhanced .form-section.erpw-so-section-items .grid-footer,'
      + '.erpw-so-form-enhanced .form-section.erpw-so-section-taxes .grid-footer,'
      + '.erpw-so-terms-section-payment .grid-footer'
    );

    footers.forEach((footer) => {
      const section = footer && typeof footer.closest === 'function'
        ? footer.closest('.form-section, .grid-field, .frappe-control')
        : null;
      const selectedRows = countSelectedGridRows(section);
      const nativeDeleteButton = footer.querySelector('.grid-buttons .grid-remove-rows');
      const deleteAllButton = footer.querySelector('.grid-buttons .grid-remove-all-rows');

      if (nativeDeleteButton instanceof HTMLElement) {
        syncNativeDeleteButton(nativeDeleteButton, selectedRows);
      }

      if (deleteAllButton instanceof HTMLElement) {
        resetGridActionLabel(deleteAllButton);
        deleteAllButton.style.removeProperty('display');
      }

      footer.querySelectorAll('.grid-bulk-actions .btn, .grid-bulk-actions button').forEach((button) => {
        if (!(button instanceof HTMLElement)) return;
        resetGridActionLabel(button);
        button.style.removeProperty('display');
      });
    });
  }

  function scheduleGridActionLabelNormalization(scope) {
    if (gridActionLabelNormalizeFrame) {
      window.cancelAnimationFrame(gridActionLabelNormalizeFrame);
    }
    gridActionLabelNormalizeFrame = window.requestAnimationFrame(() => {
      gridActionLabelNormalizeFrame = null;
      normalizeGridActionLabels(scope);
    });
    [120, 320, 720].forEach((delay) => {
      window.setTimeout(() => normalizeGridActionLabels(scope), delay);
    });
  }

  function isManagedDraftForm(frm) {
    return !!(
      frm
      && (frm.doctype === 'Sales Order' || frm.doctype === 'Quotation')
      && typeof frm.is_new === 'function'
      && frm.is_new()
      && isChildExecutionRoute()
    );
  }

  function getManagedDraftLookupInput(target) {
    if (!isManagedDraftForm(window.cur_frm)) return null;
    const input = target instanceof HTMLInputElement
      ? target
      : target && typeof target.closest === 'function'
        ? target.closest('input')
        : null;
    if (!(input instanceof HTMLInputElement)) return null;
    if (!input.closest('.erpw-so-form-enhanced')) return null;
    return input;
  }

  function getManagedDraftLookupAnchorFromInput(input) {
    if (!(input instanceof HTMLInputElement)) return null;
    const candidates = [
      input.closest('.awesomplete'),
      input.closest('.link-field'),
      input.closest('.control-input-wrapper'),
      input.parentElement,
    ];
    const anchor = candidates.find((candidate) => candidate instanceof HTMLElement && candidate.closest('.erpw-so-form-enhanced'));
    return anchor instanceof HTMLElement ? anchor : null;
  }

  function resetDraftLookupAnchors() {
    Array.from(document.querySelectorAll('.erpw-managed-draft-lookup-anchor')).forEach((anchor) => {
      if (!(anchor instanceof HTMLElement)) return;
      anchor.classList.remove('erpw-managed-draft-lookup-anchor');
      [
        'position', 'overflow', 'display', 'width', 'max-width', 'min-height', 'height', 'max-height', 'z-index'
      ].forEach((property) => anchor.style.removeProperty(property));
    });
  }

  let managedDraftLookupStylesInjected = false;

  function ensureManagedDraftLookupStyles() {
    if (managedDraftLookupStylesInjected || !document.head) return;
    managedDraftLookupStylesInjected = true;

    const style = document.createElement('style');
    style.id = 'erpw-managed-draft-lookup-styles';
    style.textContent = `
      .erpw-so-form-enhanced [data-erpw-draft-column="quotation-price-list"],
      .erpw-so-form-enhanced [data-erpw-draft-column="sales-order-price-list"] {
        display: block;
        clear: left;
        float: left;
        width: 33.33333333%;
      }

      .erpw-so-form-enhanced .erpw-so-draft-price-list-field,
      .erpw-so-form-enhanced .erpw-so-draft-price-list-field .frappe-control,
      .erpw-so-form-enhanced .erpw-so-draft-price-list-field .control-input-wrapper,
      .erpw-so-form-enhanced .erpw-so-draft-price-list-field .link-field,
      .erpw-so-form-enhanced .erpw-so-draft-price-list-field .awesomplete,
      .erpw-so-form-enhanced .erpw-so-draft-price-list-field input {
        width: 100% !important;
        max-width: 100% !important;
      }

      .erpw-so-form-enhanced .erpw-so-draft-price-list-field {
        margin-left: 0 !important;
        margin-right: 0 !important;
      }

      .erpw-so-form-enhanced .erpw-draft-tax-context {
        margin: 0 24px 18px;
        padding: 12px 18px 14px;
        border: 1px solid rgba(214, 224, 238, 0.95);
        border-radius: 18px;
        background: #ffffff;
      }

      .erpw-so-form-enhanced .erpw-draft-tax-context-meta {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 8px;
      }

      .erpw-so-form-enhanced .erpw-draft-tax-context-status {
        flex: 0 0 auto;
        padding: 0;
        border: 0;
        border-radius: 0;
        background: transparent;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: #7b8ea6;
      }

      .erpw-so-form-enhanced .erpw-draft-tax-grid {
        display: grid;
        gap: 10px 16px;
      }

      .erpw-so-form-enhanced .erpw-draft-tax-grid-main {
        grid-template-columns: minmax(0, 1fr);
      }

      .erpw-so-form-enhanced .erpw-draft-tax-field {
        margin: 0 !important;
        width: min(640px, 100%) !important;
        max-width: 640px !important;
      }

      .erpw-so-form-enhanced .erpw-draft-tax-field .form-group,
      .erpw-so-form-enhanced .erpw-draft-tax-field .frappe-control,
      .erpw-so-form-enhanced .erpw-draft-tax-field .control-input-wrapper,
      .erpw-so-form-enhanced .erpw-draft-tax-field .link-field,
      .erpw-so-form-enhanced .erpw-draft-tax-field .awesomplete,
      .erpw-so-form-enhanced .erpw-draft-tax-field .input-with-feedback,
      .erpw-so-form-enhanced .erpw-draft-tax-field .control-value,
      .erpw-so-form-enhanced .erpw-draft-tax-field input,
      .erpw-so-form-enhanced .erpw-draft-tax-field select {
        width: 100% !important;
        max-width: 100% !important;
      }

      .erpw-so-form-enhanced .erpw-draft-tax-field .control-input-wrapper,
      .erpw-so-form-enhanced .erpw-draft-tax-field .link-field,
      .erpw-so-form-enhanced .erpw-draft-tax-field .awesomplete,
      .erpw-so-form-enhanced .erpw-draft-tax-field .input-with-feedback,
      .erpw-so-form-enhanced .erpw-draft-tax-field .control-value,
      .erpw-so-form-enhanced .erpw-draft-tax-field input,
      .erpw-so-form-enhanced .erpw-draft-tax-field select {
        background: #f3f6fa !important;
        border-color: #dfe7f1 !important;
        border-radius: 12px !important;
      }

      @media (max-width: 991px) {
        .erpw-so-form-enhanced .erpw-draft-tax-grid-main {
          grid-template-columns: 1fr;
        }

        .erpw-so-form-enhanced .erpw-draft-tax-context {
          margin-left: 16px;
          margin-right: 16px;
        }
      }

      .erpw-hide-line-delivery-date .grid-heading-row [data-fieldname="delivery_date"],
      .erpw-hide-line-delivery-date .grid-body [data-fieldname="delivery_date"],
      .erpw-hide-line-delivery-date .rows [data-fieldname="delivery_date"],
      .erpw-hide-line-delivery-date .grid-static-col[data-fieldname="delivery_date"] {
        display: none !important;
      }
    `;
    document.head.appendChild(style);
  }

  function normalizeDraftLookupAnchor(input) {
    const anchor = getManagedDraftLookupAnchorFromInput(input);
    if (!(anchor instanceof HTMLElement)) return null;

    const inputRect = input.getBoundingClientRect();
    const inputHeight = Math.max(34, Math.ceil(inputRect.height || input.offsetHeight || 36));
    const inputWidth = Math.max(180, Math.ceil(inputRect.width || input.offsetWidth || anchor.offsetWidth || 0));

    anchor.classList.add('erpw-managed-draft-lookup-anchor');
    anchor.style.setProperty('position', 'relative', 'important');
    anchor.style.setProperty('overflow', 'visible', 'important');
    anchor.style.setProperty('z-index', '1400', 'important');
    anchor.style.setProperty('min-height', `${inputHeight}px`, 'important');
    anchor.style.setProperty('height', `${inputHeight}px`, 'important');
    anchor.style.setProperty('max-height', `${inputHeight}px`, 'important');

    if (
      anchor.classList.contains('awesomplete')
      || anchor.classList.contains('link-field')
      || anchor.classList.contains('control-input-wrapper')
    ) {
      anchor.style.setProperty('display', 'block', 'important');
      anchor.style.setProperty('width', `${inputWidth}px`, 'important');
      anchor.style.setProperty('max-width', '100%', 'important');
    }
    return anchor;
  }

  function getManagedDraftLookupMeta(target) {
    const frm = window.cur_frm;
    if (!isManagedDraftForm(frm)) return null;
    const input = getManagedDraftLookupInput(target);
    if (!(input instanceof HTMLInputElement)) return null;

    const explicitFieldHost = input.closest('[data-fieldname], .frappe-control[data-fieldname], .grid-static-col[data-fieldname], .grid-field[data-fieldname]');
    const explicitOptionsHost = input.closest('[data-options], .frappe-control[data-options], [data-fieldtype="Link"][data-options]');

    let fieldname = explicitFieldHost && typeof explicitFieldHost.getAttribute === 'function'
      ? String(explicitFieldHost.getAttribute('data-fieldname') || '').trim()
      : '';
    let optionsDoctype = explicitOptionsHost && typeof explicitOptionsHost.getAttribute === 'function'
      ? String(explicitOptionsHost.getAttribute('data-options') || '').trim()
      : '';

    let node = input;
    while (node && node !== document.body) {
      if (typeof node.getAttribute === 'function') {
        fieldname = fieldname || String(node.getAttribute('data-fieldname') || '').trim();
        optionsDoctype = optionsDoctype || String(node.getAttribute('data-options') || '').trim();
      }
      node = node.parentElement;
    }

    const quotationPartyDoctype = frm && frm.doctype === 'Quotation'
      ? String((frm.doc && frm.doc.quotation_to) || 'Customer').trim() || 'Customer'
      : 'Customer';
    const fieldDoctypeMap = {
      item_code: 'Item',
      customer: 'Customer',
      party_name: quotationPartyDoctype,
      customer_address: 'Address',
      shipping_address_name: 'Address',
      contact_person: 'Contact',
      territory: 'Territory',
      taxes_and_charges: 'Sales Taxes and Charges Template',
      tax_category: 'Tax Category',
      shipping_rule: 'Shipping Rule',
      incoterm: 'Incoterm',
      selling_price_list: 'Price List',
    };

    const resolvedOptionsDoctype = (
      optionsDoctype
      && optionsDoctype !== 'quotation_to'
      && /^[A-Z]/.test(optionsDoctype)
    ) ? optionsDoctype : '';
    const doctype = fieldname === 'party_name'
      ? quotationPartyDoctype
      : resolvedOptionsDoctype || fieldDoctypeMap[fieldname] || '';
    const managedFields = new Set(['item_code', 'customer', 'party_name', 'selling_price_list', 'taxes_and_charges']);
    if (!managedFields.has(fieldname)) return null;
    if (!(doctype === 'Customer' || doctype === 'Item' || doctype === 'Price List' || doctype === 'Sales Taxes and Charges Template')) return null;

    return {
      doctype,
      fieldname,
      input,
    };
  }

  function getDraftLookupCacheKey(meta, frm) {
    const activeForm = frm || window.cur_frm;
    if (!activeForm || !meta || !meta.doctype) return '';
    const routeKey = String(activeForm.doctype || '').trim();
    const fieldKey = String(meta.fieldname || meta.doctype || '').trim();
    const doctypeKey = String(meta.doctype || '').trim();
    const partyKey = String(activeForm.doc && activeForm.doc.quotation_to || '').trim();
    return [routeKey, fieldKey, doctypeKey, partyKey].filter(Boolean).join('::');
  }

  function setDraftLookupCachedResults(meta, results, frm) {
    const cacheKey = getDraftLookupCacheKey(meta, frm);
    if (!cacheKey) return [];
    draftLookupResultCache[cacheKey] = Array.isArray(results) ? results.slice() : [];
    return draftLookupResultCache[cacheKey];
  }

  function mergeDraftLookupFilters(baseFilters, extraFilters) {
    const additions = extraFilters && typeof extraFilters === 'object' ? extraFilters : {};
    if (!Object.keys(additions).length) return baseFilters;
    if (!baseFilters) return additions;

    if (typeof baseFilters === 'string') {
      try {
        const parsed = JSON.parse(baseFilters);
        return Object.assign({}, parsed || {}, additions);
      } catch (error) {
        return additions;
      }
    }

    if (Array.isArray(baseFilters)) {
      return baseFilters.concat(Object.entries(additions));
    }

    if (typeof baseFilters === 'object') {
      return Object.assign({}, baseFilters, additions);
    }

    return additions;
  }

  function applyManagedDraftLookupFieldFilters(meta, args) {
    if (!meta || !args || typeof args !== 'object') return args;

    if (meta.fieldname === 'selling_price_list') {
      args.filters = mergeDraftLookupFilters(args.filters, {
        selling: 1,
        enabled: 1,
      });
    }

    if (meta.fieldname === 'taxes_and_charges') {
      args.filters = mergeDraftLookupFilters(args.filters, {
        disabled: 0,
      });
    }

    return args;
  }

  function getDraftLookupCachedResults(meta, frm) {
    const cacheKey = getDraftLookupCacheKey(meta, frm);
    if (!cacheKey) return [];
    return Array.isArray(draftLookupResultCache[cacheKey]) ? draftLookupResultCache[cacheKey].slice() : [];
  }

  function fetchDraftLookupDataset(meta, frm) {
    const activeForm = frm || window.cur_frm;
    if (!activeForm || !meta || !meta.doctype) return Promise.resolve([]);
    if (!window.frappe || typeof frappe.call !== 'function') return Promise.resolve([]);

    const cacheKey = getDraftLookupCacheKey(meta, activeForm);
    if (!cacheKey) return Promise.resolve([]);

    const cachedResults = getDraftLookupCachedResults(meta, activeForm);
    if (cachedResults.length) return Promise.resolve(cachedResults);
    if (draftLookupPendingCache[cacheKey]) return draftLookupPendingCache[cacheKey];

    draftLookupPendingCache[cacheKey] = new Promise((resolve) => {
      try {
        const args = applyManagedDraftLookupFieldFilters(meta, {
          doctype: meta.doctype,
          txt: '',
          page_length: 500,
          reference_doctype: activeForm.doctype,
          link_fieldname: meta.fieldname || undefined,
        });

        frappe.call({
          method: 'frappe.desk.search.search_link',
          args,
          callback: (response) => {
            const results = normalizeDraftLookupResults(response && response.message);
            setDraftLookupCachedResults(meta, results, activeForm);
            delete draftLookupPendingCache[cacheKey];
            resolve(results);
          },
          error: () => {
            delete draftLookupPendingCache[cacheKey];
            resolve([]);
          },
        });
      } catch (error) {
        delete draftLookupPendingCache[cacheKey];
        resolve([]);
      }
    });

    return draftLookupPendingCache[cacheKey];
  }

  function filterDraftLookupResults(results, query) {
    if (!Array.isArray(results) || !results.length) return [];
    const normalizedQuery = String(query || '').trim().toLowerCase();
    if (!normalizedQuery) return results.slice();

    const scored = results
      .map((result, index) => {
        const value = String(result && result.value || '').trim();
        const label = String(result && result.label || value).trim();
        const description = String(result && result.description || '').trim();
        const primary = `${value} ${label}`.toLowerCase();
        const secondary = description.toLowerCase();

        let score = -1;
        if (value.toLowerCase() === normalizedQuery || label.toLowerCase() === normalizedQuery) {
          score = 0;
        } else if (value.toLowerCase().startsWith(normalizedQuery) || label.toLowerCase().startsWith(normalizedQuery)) {
          score = 1;
        } else if (primary.includes(normalizedQuery)) {
          score = 2;
        } else if (secondary.includes(normalizedQuery)) {
          score = 3;
        }

        if (score < 0) return null;
        return { result, score, index };
      })
      .filter(Boolean)
      .sort((left, right) => {
        if (left.score !== right.score) return left.score - right.score;
        return left.index - right.index;
      })
      .map((entry) => entry.result);

    return scored;
  }

  function prewarmDraftLookup(meta) {
    const frm = window.cur_frm;
    if (!isManagedDraftForm(frm) || !frm) return;
    if (!meta || !meta.doctype) return;

    frm.__erpwDraftLookupWarmed = frm.__erpwDraftLookupWarmed || {};
    const warmKey = getDraftLookupCacheKey(meta, frm);
    if (!warmKey || frm.__erpwDraftLookupWarmed[warmKey]) return;

    frm.__erpwDraftLookupWarmed[warmKey] = true;
    fetchDraftLookupDataset(meta, frm);
  }

  function prewarmDraftLookupDefaults(frmOverride) {
    const frm = frmOverride || window.cur_frm;
    if (!isManagedDraftForm(frm)) return;
    if (frm.doctype === 'Quotation') {
      prewarmDraftLookup({
        doctype: String((frm.doc && frm.doc.quotation_to) || 'Customer').trim() || 'Customer',
        fieldname: 'party_name',
      });
    } else {
      prewarmDraftLookup({ doctype: 'Customer', fieldname: 'customer' });
    }
    prewarmDraftLookup({ doctype: 'Item', fieldname: 'item_code' });
    prewarmDraftLookup({ doctype: 'Price List', fieldname: 'selling_price_list' });
    prewarmDraftLookup({ doctype: 'Sales Taxes and Charges Template', fieldname: 'taxes_and_charges' });
  }

  function primeManagedDraftLookups(frm) {
    const activeForm = frm || window.cur_frm;
    if (!isManagedDraftForm(activeForm)) return;
    prewarmDraftLookupDefaults(activeForm);
  }

  function getVisibleDraftLookupPopups() {
    const selectors = [
      '.awesomplete > ul:not([hidden])',
      '.ui-autocomplete',
      '.autocomplete-suggestions',
      '.link-field .awesomplete > ul:not([hidden])',
      '[role="listbox"]',
      '.ui-menu',
    ];

    const seen = new Set();
    return selectors
      .flatMap((selector) => Array.from(document.querySelectorAll(selector)))
      .filter((popup) => {
        if (!(popup instanceof HTMLElement)) return false;
        if (seen.has(popup)) return false;
        seen.add(popup);
        const style = window.getComputedStyle(popup);
        if (style.display === 'none' || style.visibility === 'hidden' || popup.hidden) return false;
        return popup.getClientRects().length > 0;
      });
  }

  function hideNativeDraftLookupPopups(popups) {
    popups.forEach((popup) => {
      if (!(popup instanceof HTMLElement)) return;
      popup.classList.add('erpw-native-draft-lookup-hidden');
    });
  }

  function clearNativeDraftLookupPopupHiding() {
    getVisibleDraftLookupPopups().forEach((popup) => {
      if (!(popup instanceof HTMLElement)) return;
      popup.classList.remove('erpw-native-draft-lookup-hidden');
    });
  }

  function getManagedDraftLookupGridRow(input) {
    const frm = window.cur_frm;
    if (!frm || !(input instanceof HTMLElement)) return null;
    const rowNode = input.closest('.grid-row');
    if (!(rowNode instanceof HTMLElement)) return null;
    const rowName = String(rowNode.getAttribute('data-name') || rowNode.getAttribute('data-docname') || rowNode.dataset.name || '').trim();
    if (!rowName) return null;

    const fieldEntries = Object.values(frm.fields_dict || {});
    for (const field of fieldEntries) {
      const grid = field && field.grid;
      if (!grid || !grid.grid_rows_by_docname) continue;
      if (grid.grid_rows_by_docname[rowName]) {
        return grid.grid_rows_by_docname[rowName];
      }
    }
    return null;
  }

  function escapeDraftLookupHtml(value) {
    const text = String(value == null ? '' : value);
    if (window.frappe && frappe.utils && typeof frappe.utils.escape_html === 'function') {
      return frappe.utils.escape_html(text);
    }
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function normalizeDraftLookupResults(message) {
    if (!Array.isArray(message)) return [];
    return message
      .map((row) => {
        if (!row) return null;
        if (typeof row === 'string') {
          return { value: row, label: row, description: '' };
        }
        if (Array.isArray(row)) {
          return {
            value: String(row[0] || '').trim(),
            label: String(row[0] || '').trim(),
            description: String(row[1] || '').trim(),
          };
        }
        const value = String(row.value || row.name || '').trim();
        if (!value) return null;
        return {
          value,
          label: String(row.label || row.value || row.name || '').trim() || value,
          description: String(row.description || '').trim(),
        };
      })
      .filter((row) => row && row.value);
  }

  function ensureDraftLookupMirror() {
    if (draftLookupMirror instanceof HTMLElement && document.body.contains(draftLookupMirror)) return draftLookupMirror;

    const mirror = document.createElement('div');
    mirror.className = 'erpw-draft-lookup-mirror';
    mirror.setAttribute('aria-hidden', 'true');
    mirror.addEventListener('mousedown', (event) => {
      if (event.target.closest('.erpw-draft-lookup-option')) {
        event.preventDefault();
      }
    });
    mirror.addEventListener('click', (event) => {
      const optionNode = event.target.closest('.erpw-draft-lookup-option');
      if (!(optionNode instanceof HTMLElement)) return;
      event.preventDefault();
      const index = Number(optionNode.getAttribute('data-lookup-index') || '-1');
      const result = draftLookupMirrorNativeOptions[index];
      if (!result) return;
      applyDraftLookupSelection(result);
    });
    document.body.appendChild(mirror);
    draftLookupMirror = mirror;
    return draftLookupMirror;
  }

  function hideDraftLookupMirror() {
    if (!(draftLookupMirror instanceof HTMLElement)) return;
    draftLookupMirror.classList.remove('visible');
    draftLookupMirror.setAttribute('aria-hidden', 'true');
    draftLookupMirror.innerHTML = '';
    draftLookupMirrorNativeOptions = [];
  }

  function renderDraftLookupMirrorMessage(input, title, note) {
    const mirror = ensureDraftLookupMirror();
    draftLookupMirrorNativeOptions = [];
    mirror.innerHTML = `
      <div class="erpw-draft-lookup-empty">
        <span class="erpw-draft-lookup-empty-title">${escapeDraftLookupHtml(title || '')}</span>
        ${note ? `<span class="erpw-draft-lookup-empty-note">${escapeDraftLookupHtml(note)}</span>` : ''}
      </div>
    `;
    mirror.classList.add('visible');
    mirror.setAttribute('aria-hidden', 'false');
    positionDraftLookupMirror(input);
  }

  function positionDraftLookupMirror(input) {
    if (!(draftLookupMirror instanceof HTMLElement) || !draftLookupMirror.classList.contains('visible')) return;
    if (!(input instanceof HTMLElement)) return;
    const rect = input.getBoundingClientRect();
    if (!rect.width && !rect.height) return;

    const viewportPadding = 12;
    const width = Math.min(Math.max(Math.ceil(rect.width + 18), 260), 340, window.innerWidth - (viewportPadding * 2));
    const mirrorHeight = Math.min(Math.max(draftLookupMirror.scrollHeight || draftLookupMirror.offsetHeight || 180, 120), 280);
    const roomBelow = window.innerHeight - rect.bottom - viewportPadding;
    const top = roomBelow >= Math.min(180, mirrorHeight)
      ? rect.bottom + 2
      : Math.max(viewportPadding, rect.top - mirrorHeight - 2);
    const left = Math.min(
      Math.max(viewportPadding, rect.left),
      window.innerWidth - width - viewportPadding
    );

    draftLookupMirror.style.setProperty('top', `${top}px`, 'important');
    draftLookupMirror.style.setProperty('left', `${left}px`, 'important');
    draftLookupMirror.style.setProperty('width', `${width}px`, 'important');
    draftLookupMirror.style.setProperty('max-height', '280px', 'important');
  }

  function renderDraftLookupMirror(results, input) {
    const mirror = ensureDraftLookupMirror();
    if (!Array.isArray(results) || !results.length) {
      hideDraftLookupMirror();
      return;
    }

    draftLookupMirrorNativeOptions = results;
    mirror.innerHTML = results.map((result, index) => `
      <button type="button" class="erpw-draft-lookup-option" data-lookup-index="${index}">
        <span class="erpw-draft-lookup-title">${escapeDraftLookupHtml(result.label || result.value)}</span>
        ${result.description ? `<span class="erpw-draft-lookup-meta">${escapeDraftLookupHtml(result.description)}</span>` : ''}
      </button>
    `).join('');
    mirror.classList.add('visible');
    mirror.setAttribute('aria-hidden', 'false');
    positionDraftLookupMirror(input);
  }

  function applyDraftLookupSelection(result) {
    const frm = window.cur_frm;
    const meta = activeDraftLookupMeta;
    const input = activeDraftLookupInput;
    if (!frm || !meta || !(input instanceof HTMLInputElement) || !result || !result.value) {
      resetDraftLookupPopups();
      return;
    }

    input.value = result.value;

    if (meta.fieldname === 'item_code') {
      const gridRow = getManagedDraftLookupGridRow(input);
      if (gridRow && gridRow.doc && window.frappe && frappe.model && typeof frappe.model.set_value === 'function') {
        frappe.model.set_value(gridRow.doc.doctype, gridRow.doc.name, meta.fieldname, result.value);
      } else {
        input.dispatchEvent(new Event('change', { bubbles: true }));
      }
    } else if (typeof frm.set_value === 'function') {
      frm.set_value(meta.fieldname, result.value);
    } else {
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }

    window.setTimeout(() => {
      resetDraftLookupPopups();
      if (input && typeof input.focus === 'function') {
        input.focus();
      }
    }, 0);
  }

  function fetchManagedDraftLookup(meta, input, options) {
    const frm = meta && meta.frm ? meta.frm : window.cur_frm;
    if (!isManagedDraftForm(frm) || !meta || !meta.doctype || !(input instanceof HTMLInputElement)) {
      resetDraftLookupPopups();
      return;
    }

    const settings = Object.assign({
      showAll: false,
    }, options || {});
    const query = settings.showAll ? '' : String(input.value || '').trim();
    const requestToken = ++draftLookupRequestToken;
    activeDraftLookupInput = input;
    activeDraftLookupMeta = meta;
    normalizeDraftLookupAnchor(input);

    const renderFiltered = (results) => {
      const filteredResults = filterDraftLookupResults(results, query);
      hideNativeDraftLookupPopups(getVisibleDraftLookupPopups());
      if (filteredResults.length) {
        renderDraftLookupMirror(filteredResults, input);
        return;
      }
      renderDraftLookupMirrorMessage(
        input,
        query ? `No matches for "${query}"` : 'No options available',
        query ? 'Try a broader term or clear the field.' : 'No records are available for this field.'
      );
    };

    hideNativeDraftLookupPopups(getVisibleDraftLookupPopups());
    renderDraftLookupMirrorMessage(input, 'Loading options...', 'Fetching the latest records.');

    let args = null;
    if (meta.control && typeof meta.control.get_search_args === 'function') {
      args = meta.control.get_search_args(query);
    }
    if (!args) {
      args = {
        txt: query,
        doctype: meta.doctype,
        reference_doctype: frm.doctype,
        link_fieldname: meta.fieldname,
      };
    }

    args.txt = query;
    args.doctype = meta.doctype;
    args.reference_doctype = frm.doctype;
    args.link_fieldname = meta.fieldname || args.link_fieldname;
    args.page_length = query ? 200 : (meta.doctype === 'Price List' ? 500 : 120);
    applyManagedDraftLookupFieldFilters(meta, args);

    try {
      frappe.call({
        type: query ? 'POST' : 'GET',
        method: 'frappe.desk.search.search_link',
        no_spinner: true,
        cache: !query,
        args,
        callback: (response) => {
          if (requestToken !== draftLookupRequestToken) return;
          if (activeDraftLookupInput !== input) return;
          const results = normalizeDraftLookupResults(response && response.message);
          renderFiltered(results);
        },
        error: () => {
          if (requestToken !== draftLookupRequestToken) return;
          renderDraftLookupMirrorMessage(input, 'Unable to load options', 'Try again in a moment.');
        },
      });
    } catch (error) {
      if (requestToken !== draftLookupRequestToken) return;
      renderDraftLookupMirrorMessage(input, 'Unable to load options', 'Try again in a moment.');
    }
  }

  function scheduleManagedDraftLookupFetch(meta, input, options) {
    if (!meta || !meta.doctype || !(input instanceof HTMLInputElement)) {
      resetDraftLookupPopups();
      return;
    }

    activeDraftLookupMeta = meta;
    activeDraftLookupInput = input;
    normalizeDraftLookupAnchor(input);
    fetchManagedDraftLookup(meta, input, options);
  }

  function resetDraftLookupPopups() {
    draftLookupRequestToken += 1;
    clearNativeDraftLookupPopupHiding();
    resetDraftLookupAnchors();
    hideDraftLookupMirror();
  }

  function positionDraftLookupPopups() {
    if (!isManagedDraftForm(window.cur_frm)) {
      resetDraftLookupPopups();
      return;
    }
    if (!(activeDraftLookupInput instanceof HTMLElement) || !document.body.contains(activeDraftLookupInput)) {
      resetDraftLookupPopups();
      return;
    }
    positionDraftLookupMirror(activeDraftLookupInput);
    hideNativeDraftLookupPopups(getVisibleDraftLookupPopups());
  }

  function scheduleDraftLookupPositioning() {
    if (draftLookupPositionFrame) {
      window.cancelAnimationFrame(draftLookupPositionFrame);
    }
    draftLookupPositionFrame = window.requestAnimationFrame(() => {
      draftLookupPositionFrame = null;
      positionDraftLookupPopups();
    });
  }

  function bindDraftLookupSurface() {
    if (draftLookupBound || !document.body) return;
    draftLookupBound = true;
    ensureManagedDraftLookupStyles();

    const isLookupEventInside = (target) => {
      if (!(target instanceof Element)) return false;
      if (target.closest('.erpw-draft-lookup-mirror')) return true;
      return !!getManagedDraftLookupMeta(target);
    };

    document.body.addEventListener('mousedown', (event) => {
      if (isLookupEventInside(event.target)) return;
      resetDraftLookupPopups();
    }, true);

    document.body.addEventListener('focusin', (event) => {
      const meta = getManagedDraftLookupMeta(event.target);
      if (!meta) return;
      scheduleManagedDraftLookupFetch(meta, meta.input, { showAll: true });
    }, true);

    document.body.addEventListener('input', (event) => {
      const meta = getManagedDraftLookupMeta(event.target);
      if (!meta) return;
      scheduleManagedDraftLookupFetch(meta, meta.input);
    }, true);

    document.body.addEventListener('keydown', (event) => {
      if (event.key !== 'Escape') return;
      if (!isLookupEventInside(event.target)) return;
      resetDraftLookupPopups();
    }, true);

    window.addEventListener('resize', scheduleDraftLookupPositioning, true);
    window.addEventListener('scroll', () => {
      if (activeDraftLookupInput instanceof HTMLElement && document.body.contains(activeDraftLookupInput)) {
        scheduleDraftLookupPositioning();
        return;
      }
      resetDraftLookupPopups();
    }, true);
  }


  function ensureChildGridActionLabels() {
    if (!document.body) return;

    if (!gridActionLabelsBound) {
      gridActionLabelsBound = true;

      if (window.MutationObserver) {
        gridActionLabelsObserver = new MutationObserver((mutations) => {
          if (!isChildExecutionRoute()) return;
          const hasRelevantChange = mutations.some((mutation) => {
            if (mutation.addedNodes && mutation.addedNodes.length) return true;
            if (mutation.type === 'attributes' && ['class', 'checked', 'title', 'aria-label'].includes(mutation.attributeName || '')) {
              return true;
            }
            return false;
          });
          if (!hasRelevantChange) return;
          scheduleGridActionLabelNormalization(document);
        });
        gridActionLabelsObserver.observe(document.body, {
          childList: true,
          subtree: true,
          attributes: true,
          attributeFilter: ['class', 'checked', 'title', 'aria-label'],
        });
      }

      const scheduleGridLabels = () => {
        if (!isChildExecutionRoute()) return;
        scheduleGridActionLabelNormalization(document);
      };

      document.body.addEventListener('click', scheduleGridLabels, true);
      document.body.addEventListener('change', scheduleGridLabels, true);
    }

    scheduleGridActionLabelNormalization(document);
  }

  function getManagedNativeDraftForm(control) {
    if (!control) return null;
    const frm = control.frm
      || (control.grid && control.grid.frm)
      || (control.layout && control.layout.frm)
      || window.cur_frm;
    return isManagedDraftForm(frm) ? frm : null;
  }

  function getManagedNativeDraftLookupMeta(control) {
    const frm = getManagedNativeDraftForm(control);
    if (!frm || !control || !control.df) return null;

    const fieldname = String(control.df.fieldname || '').trim();
    if (!(fieldname === 'customer' || fieldname === 'party_name' || fieldname === 'item_code' || fieldname === 'selling_price_list' || fieldname === 'taxes_and_charges')) {
      return null;
    }

    const input = control.$input && typeof control.$input.get === 'function'
      ? control.$input.get(0)
      : control.input;
    if (!(input instanceof HTMLInputElement)) return null;

    const doctype = fieldname === 'item_code'
      ? 'Item'
      : fieldname === 'selling_price_list'
        ? 'Price List'
      : fieldname === 'taxes_and_charges'
        ? String(control.df.options || 'Sales Taxes and Charges Template').trim() || 'Sales Taxes and Charges Template'
      : frm.doctype === 'Quotation'
        ? String((frm.doc && frm.doc.quotation_to) || control.df.options || 'Customer').trim() || 'Customer'
        : 'Customer';

    return {
      frm,
      control,
      fieldname,
      doctype,
      input,
    };
  }

  function isManagedNativeDraftLink(control) {
    return !!getManagedNativeDraftLookupMeta(control);
  }

  function patchNativeDraftLinkLookup() {
    if (!window.frappe || !frappe.ui || !frappe.ui.form || !frappe.ui.form.ControlLink) {
      return;
    }
    const proto = frappe.ui.form.ControlLink.prototype;
    if (!proto || proto.__erpwNativeDraftLookupPatched) return;

    const originalGetSearchArgs = proto.get_search_args;
    const originalSetupAwesomplete = proto.setup_awesomeplete;
    const originalOnInput = proto.on_input;

    proto.get_search_args = function () {
      const args = originalGetSearchArgs.apply(this, arguments);
      if (args && isManagedNativeDraftLink(this)) {
        args.page_length = 200;
      }
      return args;
    };

    proto.setup_awesomeplete = function () {
      const result = originalSetupAwesomplete.apply(this, arguments);
      if (!isManagedNativeDraftLink(this)) return result;
      if (!this.awesomplete || !this.$input) return result;

      this.awesomplete.maxItems = 200;
      if (!this.__erpwManagedDraftInputBound) {
        if (this._debounced_input_handler) {
          this.$input.off('input', this._debounced_input_handler);
        }
        this._debounced_input_handler = frappe.utils.debounce(this.on_input.bind(this), 120);
        this.$input.on('input', this._debounced_input_handler);
        this.__erpwManagedDraftInputBound = true;
      }
      return result;
    };

    proto.on_input = function () {
      const meta = getManagedNativeDraftLookupMeta(this);
      if (!meta) {
        return originalOnInput.apply(this, arguments);
      }
      if (this.awesomplete && typeof this.awesomplete.close === 'function') {
        this.awesomplete.close();
      }
      return;
    };

    window.addEventListener('scroll', () => {
      document.querySelectorAll('.awesomplete').forEach((node) => {
        if (!(node instanceof HTMLElement)) return;
        const input = node.querySelector('input');
        if (!(input instanceof HTMLInputElement)) return;
        const control = input._control || input.control;
        if (control && isManagedNativeDraftLink(control) && control.awesomplete && typeof control.awesomplete.close === 'function') {
          control.awesomplete.close();
        }
      });
    }, true);

    proto.__erpwNativeDraftLookupPatched = true;
  }

  function patchFooter() {
    if (
      footerPatched ||
      !window.frappe ||
      !frappe.ui ||
      !frappe.ui.form ||
      !frappe.ui.form.Footer
    ) {
      return;
    }

    const proto = frappe.ui.form.Footer.prototype;
    if (!proto || typeof proto.make !== "function") return;

    const originalMake = proto.make;
    proto.make = function () {
      const result = originalMake.apply(this, arguments);
      if (this.frm && isChildExecutionDocType(this.frm.doctype) && this.wrapper) {
        this.wrapper.addClass("erpw-so-support-shell");
        this.wrapper.find(".comment-box").addClass("erpw-so-comment-block");
        this.wrapper.find(".timeline, .new-timeline").addClass("erpw-so-timeline-block");
        ensureSupportHeadMarkup(this.wrapper);
      }
      return result;
    };

    footerPatched = true;
  }

  function patchSidebar() {
    if (
      sidebarPatched ||
      !window.frappe ||
      !frappe.ui ||
      !frappe.ui.form ||
      !frappe.ui.form.Sidebar
    ) {
      return;
    }

    const proto = frappe.ui.form.Sidebar.prototype;
    if (!proto || typeof proto.make !== "function") return;

    const originalMake = proto.make;
    proto.make = function () {
      if (!this || !this.page || !this.page.sidebar) {
        return this;
      }
      const result = originalMake.apply(this, arguments);
      if (this.frm && isChildExecutionDocType(this.frm.doctype) && this.sidebar) {
        this.sidebar.addClass("erpw-so-sidebar-shell");
        this.sidebar.find(".sidebar-section.text-muted.border-top.pt-3").addClass("erpw-so-sidebar-meta-hidden").hide();
      }
      return result;
    };

    sidebarPatched = true;
  }



  function noopSidebarHost() {
    if (window.jQuery) return window.jQuery();
    const noop = {
      addClass() { return noop; },
      empty() { return noop; },
      hide() { return noop; },
      removeClass() { return noop; },
    };
    return noop;
  }

  function patchFormRenderSidebarGuard() {
    if (
      formRenderSidebarGuardPatched ||
      !window.frappe ||
      !frappe.ui ||
      !frappe.ui.form ||
      !frappe.ui.form.Form
    ) {
      return;
    }

    const proto = frappe.ui.form.Form.prototype;
    if (!proto || typeof proto.render_form !== "function") return;

    const originalRenderForm = proto.render_form;
    proto.render_form = function () {
      if (!this || !this.page) {
        return undefined;
      }
      if (!this.page.sidebar) {
        this.page.sidebar = noopSidebarHost();
      }
      return originalRenderForm.apply(this, arguments);
    };

    formRenderSidebarGuardPatched = true;
  }

  const PROCUREMENT_DIRECT_PAGE_ASSETS = {
    "procurement-console": "/assets/erp_workspace_ui/js/procurement_console/procurement_console_page.js",
    "procurement-console-po-follow-up": "/assets/erp_workspace_ui/js/procurement_console/procurement_console_po_follow_up_page.js",
    "procurement-console-supplier": "/assets/erp_workspace_ui/js/procurement_console/procurement_console_supplier_page.js",
    "procurement-console-item": "/assets/erp_workspace_ui/js/procurement_console/procurement_console_item_page.js",
  };
  const PROCUREMENT_DIRECT_PAGE_STATE_KEYS = {
    "procurement-console": "__erpwProcurementConsole",
    "procurement-console-po-follow-up": "__erpwProcurementPoFollowUp",
    "procurement-console-supplier": "__erpwProcurementSupplierDetail",
    "procurement-console-item": "__erpwProcurementItemDetail",
  };
  const PROCUREMENT_ROUTE_SHELLS = {
    "procurement-console": ['.sales-console-shell[data-erpw-workspace="procurement"]'],
    "procurement-console-worklist": [".erpw-procurement-console-worklist-page"],
    "procurement-console-report": [".erpw-procurement-console-report-page"],
    "procurement-console-po-follow-up": [".erpw-procurement-po-follow-up-page"],
    "procurement-console-supplier": [".erpw-procurement-supplier-detail-page"],
    "procurement-console-item": [".erpw-procurement-item-detail-page"],
  };
  const procurementDirectPageLoads = Object.create(null);

  function isProcurementConsoleRoute(pageKey) {
    return Object.prototype.hasOwnProperty.call(PROCUREMENT_ROUTE_SHELLS, pageKey || "");
  }

  function procurementRouteShellCount(pageKey) {
    if (!isProcurementConsoleRoute(pageKey) || !document || !document.querySelectorAll) return 0;
    return PROCUREMENT_ROUTE_SHELLS[pageKey].reduce((count, selector) => count + document.querySelectorAll(selector).length, 0);
  }

  function cleanupProcurementRouteShells(activePageKey, options) {
    if (!document || !document.querySelectorAll) return;
    const settings = options && typeof options === "object" ? options : {};
    const hasActiveProcurementRoute = isProcurementConsoleRoute(activePageKey);
    Object.keys(PROCUREMENT_ROUTE_SHELLS).forEach((pageKey) => {
      if (!settings.removeActive && hasActiveProcurementRoute && pageKey === activePageKey) return;
      PROCUREMENT_ROUTE_SHELLS[pageKey].forEach((selector) => {
        document.querySelectorAll(selector).forEach((node) => {
          if (node && node.parentNode) node.parentNode.removeChild(node);
        });
      });
    });
  }

  function pruneProcurementRouteShells(activePageKey, keepNode) {
    cleanupProcurementRouteShells(activePageKey);
    if (!isProcurementConsoleRoute(activePageKey) || !keepNode || !document || !document.querySelectorAll) return;
    PROCUREMENT_ROUTE_SHELLS[activePageKey].forEach((selector) => {
      document.querySelectorAll(selector).forEach((node) => {
        if (node === keepNode || node.contains(keepNode) || keepNode.contains(node)) return;
        if (node.parentNode) node.parentNode.removeChild(node);
      });
    });
  }

  function routePartsFromLocationPath() {
    const path = String(window.location && window.location.pathname || "").replace(/^\/+/, "");
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

  function currentRouteParts() {
    const pathRouteParts = routePartsFromLocationPath();
    const pathPageKey = String(pathRouteParts[0] || "");
    if (isProcurementConsoleRoute(pathPageKey)) return pathRouteParts;
    if (pathRouteParts.length && pathPageKey) return pathRouteParts;
    if (window.frappe && typeof frappe.get_route === "function") {
      const route = frappe.get_route();
      if (Array.isArray(route) && route.length) return route;
    }
    return pathRouteParts;
  }

  function procurementDirectPageWrapper(pageKey, pageDef) {
    if (pageDef && (pageDef.page_name === pageKey || pageDef.jquery || pageDef[0] || pageDef.nodeType)) {
      return pageDef;
    }
    const deskBody = document.getElementById("body");
    if (deskBody) return deskBody;
    if (window.frappe && frappe.container) {
      const page = frappe.container.page || null;
      if (page && page.wrapper) return page.wrapper;
    }
    return null;
  }

  function renderProcurementOverviewFirstPaint(pageKey) {
    if (pageKey !== "procurement-console" || !document || !document.querySelector) return false;
    const existing = document.querySelector('.sales-console-shell[data-erpw-workspace="procurement"]');
    if (existing) return true;
    const deskBody = document.getElementById("body");
    if (!deskBody) return false;
    cleanupProcurementRouteShells(pageKey, { removeActive: true });
    const shell = document.createElement("div");
    shell.className = "sales-console-shell";
    shell.setAttribute("data-erpw-workspace", "procurement");
    shell.setAttribute("data-erpw-console-runtime", "loading");
    shell.setAttribute("data-erpw-console-bootstrap", "loading");
    shell.setAttribute("data-erpw-direct-first-paint", "procurement-console");
    shell.setAttribute("aria-busy", "true");
    shell.innerHTML = [
      '<section class="sales-console-card sales-console-header">',
      '  <div class="sales-console-header-row">',
      '    <div class="sales-console-header-copy">',
      '      <h1 class="sales-console-title">Procurement Console</h1>',
      '      <div class="sales-console-header-note">Loading the buyer workbench.</div>',
      '    </div>',
      '  </div>',
      '</section>',
      '<section class="sales-console-card sales-console-section" data-section-key="create-actions">',
      '  <div class="sales-console-section-head">',
      '    <h2 class="sales-console-section-title">Start Buying Work</h2>',
      '    <div class="sales-console-section-note">Preparing your available buying actions</div>',
      '  </div>',
      '</section>',
      '<section class="sales-console-card sales-console-section" data-section-key="priority-work">',
      '  <div class="sales-console-section-head">',
      '    <h2 class="sales-console-section-title">Priority Work</h2>',
      '    <div class="sales-console-section-note">Demand and supplier follow-up</div>',
      '  </div>',
      '</section>',
      '<section class="sales-console-card sales-console-section" data-section-key="buying-pipeline">',
      '  <div class="sales-console-section-head">',
      '    <h2 class="sales-console-section-title">Buying Pipeline</h2>',
      '    <div class="sales-console-section-note">Purchase Request to Billing Visibility</div>',
      '  </div>',
      '</section>',
    ].join("");
    deskBody.appendChild(shell);
    return true;
  }

  function renderProcurementDirectPage(pageKey) {
    const route = currentRouteParts();
    if (String(route[0] || "") !== pageKey) return false;
    const pageDef = window.frappe && frappe.pages ? frappe.pages[pageKey] : null;
    const wrapper = procurementDirectPageWrapper(pageKey, pageDef);
    if (!pageDef || !wrapper) return false;
    const routeSignature = route.join("|");
    const stateKey = PROCUREMENT_DIRECT_PAGE_STATE_KEYS[pageKey] || "";
    const existing = stateKey ? wrapper[stateKey] : null;
    const activeShell = document.querySelector('.sales-console-shell[data-erpw-workspace="procurement"]');
    const activeShellIsLoading = activeShell && (
      activeShell.getAttribute("data-erpw-direct-first-paint") === "procurement-console"
      || activeShell.getAttribute("data-erpw-console-runtime") === "loading"
    );
    if (activeShell && procurementRouteShellCount(pageKey) === 1 && !activeShellIsLoading) {
      cleanupProcurementRouteShells(pageKey);
      return true;
    }
    if (existing && existing.routeSignature === routeSignature && procurementRouteShellCount(pageKey) === 1 && !activeShellIsLoading) {
      cleanupProcurementRouteShells(pageKey);
      return true;
    }
    cleanupProcurementRouteShells(pageKey, { removeActive: true });
    if (typeof pageDef.on_page_show === "function") {
      pageDef.on_page_show(wrapper);
      return true;
    }
    if (typeof pageDef.on_page_load === "function") {
      pageDef.on_page_load(wrapper);
      return true;
    }
    return false;
  }

  function loadProcurementDirectPageAsset(pageKey, asset, callback) {
    const scriptId = `erpw-direct-page-${pageKey}`;
    const existing = document.getElementById(scriptId);
    if (existing) {
      existing.addEventListener("load", callback, { once: true });
      setTimeout(callback, 160);
      return;
    }
    const script = document.createElement("script");
    script.id = scriptId;
    script.src = asset;
    script.async = true;
    script.onload = callback;
    script.onerror = () => {
      procurementDirectPageLoads[pageKey] = false;
    };
    document.head.appendChild(script);
  }

  function ensureProcurementDirectPage() {
    const route = currentRouteParts();
    const pageKey = String(route[0] || "");
    const asset = PROCUREMENT_DIRECT_PAGE_ASSETS[pageKey];
    if (!asset) {
      cleanupProcurementRouteShells(pageKey);
      return false;
    }
    renderProcurementOverviewFirstPaint(pageKey);
    if (!window.frappe || !frappe.pages) return false;
    if (renderProcurementDirectPage(pageKey)) return true;
    if (procurementDirectPageLoads[pageKey]) {
      setTimeout(() => {
        if (String(currentRouteParts()[0] || "") === pageKey && procurementRouteShellCount(pageKey) === 0) {
          renderProcurementDirectPage(pageKey);
        }
      }, 120);
      return false;
    }
    procurementDirectPageLoads[pageKey] = true;
    loadProcurementDirectPageAsset(pageKey, asset, () => {
      if (String(currentRouteParts()[0] || "") !== pageKey) return;
      renderProcurementDirectPage(pageKey);
    });
    return true;
  }

  function scheduleProcurementDirectPage() {
    ensureProcurementDirectPage();
    setTimeout(ensureProcurementDirectPage, 80);
    setTimeout(ensureProcurementDirectPage, 220);
  }

  let procurementDirectRouteWatchBound = false;
  let lastProcurementDirectRouteSignature = "";

  function bindProcurementDirectRouteWatch() {
    if (procurementDirectRouteWatchBound || !window || typeof window.setInterval !== "function") return;
    procurementDirectRouteWatchBound = true;
    window.setInterval(() => {
      const route = currentRouteParts();
      const pageKey = String(route[0] || "");
      if (!isProcurementConsoleRoute(pageKey)) {
        lastProcurementDirectRouteSignature = "";
        return;
      }
      const routeSignature = route.join("|");
      const missingShell = procurementRouteShellCount(pageKey) === 0;
      if (routeSignature !== lastProcurementDirectRouteSignature || missingShell) {
        lastProcurementDirectRouteSignature = routeSignature;
        scheduleProcurementDirectPage();
      }
    }, 320);
  }

  let roleHomeRedirectDone = false;

  function currentBootRoles() {
    const boot = window.frappe && frappe.boot ? frappe.boot : {};
    const candidates = [
      boot.user && boot.user.roles,
      boot.user_roles,
      boot.roles,
    ];
    for (let index = 0; index < candidates.length; index += 1) {
      if (Array.isArray(candidates[index])) return candidates[index].map((role) => String(role || ""));
    }
    return [];
  }

  function hasAnyBootRole(roleNames) {
    const roleSet = new Set(currentBootRoles());
    return roleNames.some((role) => roleSet.has(role));
  }

  function isPlainDeskPath() {
    const path = String(window.location && window.location.pathname || "").replace(/\/+$/, "");
    return path === "/desk" || path === "/app";
  }

  function hasWarehouseOperationalHomeRole() {
    return hasAnyBootRole(["Warehouse Manager", "Warehouse User", "Stock Manager", "Stock User"]);
  }

  function hasWarehouseDeskBypassRole() {
    return hasAnyBootRole([
      "System Manager",
      "Sales Manager",
      "Sales User",
      "Sales Master Manager",
      "Sales Executive",
      "Key Account Sales",
      "Purchase User",
      "Purchase Manager",
      "Purchase Master Manager",
      "Accounts Manager",
      "Accounts User",
      "Finance Manager",
      "Finance User",
      "HR Manager",
      "HR User",
      "Manufacturing Manager",
      "Manufacturing User",
      "Projects Manager",
      "Projects User",
      "Report Manager",
      "Workspace Manager",
    ]);
  }

  function routeToRoleHome() {
    if (!isPlainDeskPath()) {
      roleHomeRedirectDone = false;
      return;
    }
    if (roleHomeRedirectDone || !window.frappe || typeof frappe.set_route !== "function") return;

    const user = String((frappe.session && frappe.session.user) || (frappe.boot && frappe.boot.user && frappe.boot.user.name) || "");
    if (!user || user === "Guest" || user === "Administrator") return;
    if (hasAnyBootRole(["Sales Manager", "Sales User", "Sales Master Manager", "Sales Executive", "Key Account Sales"])) {
      roleHomeRedirectDone = true;
      frappe.set_route(salesWorkspaceRoute("launcher", "sales-console-home"));
      return;
    }
    if (hasAnyBootRole(["Purchase User", "Purchase Manager", "Purchase Master Manager"])) {
      roleHomeRedirectDone = true;
      frappe.set_route("procurement-console-home");
      return;
    }
    if (hasAnyBootRole(["Accounts Manager", "Accounts User"])) {
      roleHomeRedirectDone = true;
      frappe.set_route("finance-control-desk");
      return;
    }
    if (hasWarehouseOperationalHomeRole() && !hasWarehouseDeskBypassRole()) {
      roleHomeRedirectDone = true;
      frappe.set_route("warehouse-console");
    }
  }

  function scheduleRoleHomeRedirect() {
    routeToRoleHome();
    setTimeout(routeToRoleHome, 80);
    setTimeout(routeToRoleHome, 240);
    setTimeout(routeToRoleHome, 700);
  }

  window.erpWorkspaceUiBoot = Object.assign(window.erpWorkspaceUiBoot || {}, {
    registerChildPageBootstrap(doctype, bootstrap) {
      if (!doctype || typeof bootstrap !== "function") return;
      childPageBootstrapRegistry[doctype] = bootstrap;
      scheduleActiveChildPageBootstrap();
    },
    runActiveChildPageBootstrap,
    ensureActiveChildPageBootstrap,
    scheduleActiveChildPageBootstrap,
    cleanupProcurementRouteShells,
    pruneProcurementRouteShells,
    ensureProcurementDirectPage,
    scheduleProcurementDirectPage,
    primeManagedDraftLookups,
    setSalesOrderPrep() {
      // First-paint prep takeover has been intentionally disabled.
      // Sales Order enhancement should never be allowed to blank the route.
    },
  });

  patchRouteOptionsNullSafety();
  scheduleSalesLauncherHandoff();
  scheduleRoleHomeRedirect();
  scheduleProcurementDirectPage();
  bindProcurementDirectRouteWatch();
  patchFooter();
  patchSidebar();
  patchFormRenderSidebarGuard();
  patchNativeDraftLinkLookup();
  bindRouteChrome();
  scheduleProcurementDirectPage();
  ensureChildGridActionLabels();
  bindDraftLookupSurface();
  setTimeout(patchFooter, 0);
  setTimeout(patchFooter, 80);
  setTimeout(patchFooter, 220);
  setTimeout(patchSidebar, 0);
  setTimeout(patchSidebar, 80);
  setTimeout(patchSidebar, 220);
  setTimeout(patchFormRenderSidebarGuard, 0);
  setTimeout(patchFormRenderSidebarGuard, 80);
  setTimeout(patchFormRenderSidebarGuard, 220);
  setTimeout(patchNativeDraftLinkLookup, 0);
  setTimeout(patchNativeDraftLinkLookup, 120);
  setTimeout(patchNativeDraftLinkLookup, 320);
  setTimeout(bindRouteChrome, 80);
  setTimeout(bindRouteChrome, 220);
  setTimeout(scheduleProcurementDirectPage, 80);
  setTimeout(scheduleProcurementDirectPage, 260);
  setTimeout(scheduleProcurementDirectPage, 700);
  setTimeout(scheduleProcurementDirectPage, 1400);
  setTimeout(scheduleProcurementDirectPage, 2600);
  setTimeout(patchRouteOptionsNullSafety, 0);
  setTimeout(patchRouteOptionsNullSafety, 80);
  setTimeout(patchRouteOptionsNullSafety, 220);
  setTimeout(patchRouteOptionsNullSafety, 700);
  setTimeout(scheduleSalesLauncherHandoff, 80);
  setTimeout(scheduleSalesLauncherHandoff, 400);
  setTimeout(scheduleRoleHomeRedirect, 80);
  setTimeout(scheduleRoleHomeRedirect, 400);
  setTimeout(ensureChildGridActionLabels, 0);
  setTimeout(ensureChildGridActionLabels, 140);
  setTimeout(ensureChildGridActionLabels, 360);
  if (window.frappe && frappe.router && typeof frappe.router.on === "function" && !frappe.router.erpwProcurementDirectPageRouteBound) {
    frappe.router.on("change", normalizeFrappeRouteOptions);
    frappe.router.on("change", scheduleSalesLauncherHandoff);
    frappe.router.on("change", scheduleProcurementDirectPage);
    frappe.router.on("change", scheduleRoleHomeRedirect);
    frappe.router.erpwProcurementDirectPageRouteBound = true;
  }
  setTimeout(scheduleDraftLookupPositioning, 0);
  setTimeout(scheduleDraftLookupPositioning, 180);
})();
