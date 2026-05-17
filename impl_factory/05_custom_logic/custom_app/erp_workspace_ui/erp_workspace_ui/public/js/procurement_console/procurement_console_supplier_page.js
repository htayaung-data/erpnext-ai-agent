/* global frappe, $ */

(function () {
  const workspaceRegistry = window.erpWorkspaceUiWorkspaceRegistry || {};
  const procurementWorkspace = typeof workspaceRegistry.procurement === "function" ? workspaceRegistry.procurement() : null;
  const procurementRoutes = procurementWorkspace && procurementWorkspace.routes ? procurementWorkspace.routes : {};
  const procurementMethods = procurementWorkspace && procurementWorkspace.methods ? procurementWorkspace.methods : {};
  const PAGE_KEY = procurementRoutes.supplierDetail || "procurement-console-supplier";
  const WORKLIST_ROUTE = procurementRoutes.worklist || "procurement-console-worklist";
  const PO_DETAIL_ROUTE = procurementRoutes.poFollowUpDetail || "procurement-console-po-follow-up";
  const CONTEXT_METHOD = procurementMethods.supplierDetailContext || "erp_workspace_ui.procurement_console.supplier_detail.get_supplier_detail_context";
  const CHILD_PAGE_RUNTIME_URLS = [
    "/assets/erp_workspace_ui/js/runtime/child_page/child_page_helpers.js",
    "/assets/erp_workspace_ui/js/runtime/child_page/child_page_shell_content.js",
  ];
  let runtimePromise = null;
  const SAME_ROUTE_CACHE_TTL_MS = 5000;
  const globalContextRequestCache = window.__erpwProcurementDetailContextCache = window.__erpwProcurementDetailContextCache || Object.create(null);
  const contextRequestCache = globalContextRequestCache[PAGE_KEY] = globalContextRequestCache[PAGE_KEY] || Object.create(null);

  function helpers() {
    return (window.erpWorkspaceUiChildPage && window.erpWorkspaceUiChildPage.helpers) || {};
  }

  function shellContent() {
    return (window.erpWorkspaceUiChildPage && window.erpWorkspaceUiChildPage.shellContent) || {};
  }

  function hasShellRuntime() {
    return typeof shellContent().renderShellContent === "function";
  }

  function requireRuntimeAsset(url) {
    return new Promise((resolve) => {
      frappe.require(url, () => {
        resolve();
      });
    });
  }

  function ensureDetailRuntime() {
    if (hasShellRuntime()) return Promise.resolve(shellContent());
    if (runtimePromise) return runtimePromise;
    runtimePromise = CHILD_PAGE_RUNTIME_URLS.reduce(
      (promise, url) => promise.then(() => (hasShellRuntime() ? null : requireRuntimeAsset(url))),
      Promise.resolve()
    ).then(() => {
      if (!hasShellRuntime()) {
        throw new Error("Shared child-page detail runtime is unavailable.");
      }
      return shellContent();
    }).catch((error) => {
      runtimePromise = null;
      throw error;
    });
    return runtimePromise;
  }

  function escapeHtml(value) {
    const helperEscape = helpers().escapeHtml;
    if (typeof helperEscape === "function") return helperEscape(value);
    return frappe.utils.escape_html(value == null ? "" : String(value));
  }

  function traceDetailLoad(event) {
    const target = window.__erpwProcurementDetailPerfTrace;
    if (!Array.isArray(target)) return;
    target.push(Object.assign({ pageKey: PAGE_KEY, at: Date.now() }, event || {}));
  }

  function resolveSupplier(route) {
    return Array.isArray(route) && route.length > 1 ? String(route[1] || "") : "";
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
    const route = frappe.get_route ? frappe.get_route() : [];
    const pathRoute = routePartsFromLocationPath();
    if (Array.isArray(pathRoute) && pathRoute[0] === PAGE_KEY && pathRoute.length > (Array.isArray(route) ? route.length : 0)) {
      return pathRoute;
    }
    return Array.isArray(route) ? route : pathRoute;
  }

  function routeToWorklist(queueKey) {
    frappe.set_route(WORKLIST_ROUTE, String(queueKey || "supplier_directory").replace(/_/g, "-"));
  }

  function cleanupBeforeProductizedRoute(nextPageKey) {
    const boot = window.erpWorkspaceUiBoot || {};
    if (typeof boot.cleanupProcurementRouteShells === "function") {
      boot.cleanupProcurementRouteShells("", { removeActive: true });
      setTimeout(() => boot.cleanupProcurementRouteShells(nextPageKey || "", { removeActive: false }), 0);
      setTimeout(() => boot.cleanupProcurementRouteShells(nextPageKey || "", { removeActive: false }), 80);
    }
  }

  function routeToPurchaseOrderFollowUp(purchaseOrder) {
    const name = String(purchaseOrder || "").trim();
    if (!name) return;
    cleanupBeforeProductizedRoute(PO_DETAIL_ROUTE);
    frappe.set_route(PO_DETAIL_ROUTE, name);
  }

  function cleanupForNativeRoute() {
    if (window.erpWorkspaceUiBoot && typeof window.erpWorkspaceUiBoot.cleanupProcurementRouteShells === "function") {
      window.erpWorkspaceUiBoot.cleanupProcurementRouteShells("", { removeActive: true });
      setTimeout(() => window.erpWorkspaceUiBoot.cleanupProcurementRouteShells("", { removeActive: true }), 0);
      setTimeout(() => window.erpWorkspaceUiBoot.cleanupProcurementRouteShells("", { removeActive: true }), 80);
    }
  }

  function rememberNativeChromeTarget(target) {
    const context = target && target.native_chrome && typeof target.native_chrome === "object" ? Object.assign({}, target.native_chrome) : null;
    if (!context) return;
    context.createdAt = Date.now();
    const nativeChrome = window.erpWorkspaceUiProcurementNativeChrome || {};
    if (typeof nativeChrome.remember === "function") {
      nativeChrome.remember(context);
      return;
    }
    try {
      window.sessionStorage.setItem("erpwProcurementNativeChromeContext", JSON.stringify(context));
    } catch (error) {
      window.__erpwProcurementNativeChromeContext = context;
    }
  }

  function cleanupManagedPageChrome(wrapper) {
    const $wrapper = $(wrapper);
    $wrapper.find(".page-head").remove();
  }

  function ensureHost(page, wrapper) {
    const $parent = page && page.body ? $(page.body) : $(wrapper);
    let $host = $parent.children(".erpw-procurement-supplier-detail-page").first();
    if (!$host.length) {
      $host = $('<section class="erpw-procurement-supplier-detail-page"></section>');
      $parent.empty().append($host);
    }
    let $shell = $host.children(".erpw-child-shell.erpw-child-detail-shell.erpw-procurement-supplier-detail-shell").first();
    if (!$shell.length) {
      $shell = $('<div class="erpw-child-shell erpw-child-detail-shell erpw-procurement-supplier-detail-shell"></div>');
      $host.append($shell);
    }
    return { $host, $shell };
  }

  function isAttached($node) {
    const node = $node && $node.get ? $node.get(0) : null;
    return Boolean(node && document.documentElement.contains(node));
  }

  function makeFallbackPage(wrapper) {
    const $parent = $(wrapper);
    $parent.empty().append(`
      <div class="erpw-direct-child-page">
        <div class="erpw-direct-child-titlebar">
          <div class="erpw-direct-child-title">Supplier Detail</div>
        </div>
        <main class="layout-main-section erpw-direct-child-body"></main>
      </div>
    `);
    const $body = $parent.find(".erpw-direct-child-body").first();
    return {
      body: $body,
      set_title(title) {
        const nextTitle = title || "Supplier Detail";
        $parent.find(".erpw-direct-child-title").first().text(nextTitle);
        document.title = nextTitle;
      },
    };
  }

  function makeDetailPage(wrapper) {
    try {
      return frappe.ui.make_app_page({
        parent: wrapper,
        title: "Supplier Detail",
        single_column: true,
      });
    } catch (error) {
      return makeFallbackPage(wrapper);
    }
  }

  function normalizeActions(payload, viewState) {
    const actions = payload && payload.controls && Array.isArray(payload.controls.actions) ? payload.controls.actions : [];
    return actions.map((action) => Object.assign({}, action, {
      title: action.title || action.label || action.key,
      handler() {
        if (action.key === "refresh") return loadRoute(viewState, { refresh: true });
        const target = ((payload && payload.action_targets) || {})[action.key];
        if (target && target.kind === "worklist" && target.queue_key) return routeToWorklist(target.queue_key);
      },
    }));
  }

  function renderTable(table) {
    const columns = Array.isArray(table && table.columns) ? table.columns : [];
    const rows = Array.isArray(table && table.rows) ? table.rows : [];
    const state = table && table.state ? table.state : null;
    if (!rows.length) {
      return `
        <div class="erpw-list-state ${escapeHtml(state && state.kind || "empty")}">
          <div class="erpw-list-state-title">${escapeHtml(state && state.title || "No visible rows")}</div>
          <div class="erpw-list-state-detail">${escapeHtml(state && state.detail || "No rows are available for this section.")}</div>
        </div>
      `;
    }
    return `
      <div class="erpw-list-table-wrap">
        <table class="erpw-list-table">
          <thead>
            <tr>${columns.map((column) => `<th>${escapeHtml(column.label || column.key)}</th>`).join("")}</tr>
          </thead>
          <tbody>
            ${rows.map((row) => `
              <tr>
                ${columns.map((column) => {
                  const cell = row.cells && row.cells[column.key] !== undefined ? row.cells[column.key] : "";
                  const value = cell && typeof cell === "object" ? cell.value : cell;
                  const meta = cell && typeof cell === "object" ? cell.meta : "";
                  const route = cell && typeof cell === "object" ? String(cell.route || "") : "";
                  const routeParts = cell && typeof cell === "object" && Array.isArray(cell.route_parts) ? cell.route_parts : [];
                  const routeName = routeParts.length ? routeParts[0] : value;
                  const valueMarkup = route
                    ? `<button type="button" class="erpw-list-inline-open" data-erpw-procurement-detail-route="${escapeHtml(route)}" data-erpw-procurement-detail-name="${escapeHtml(routeName || "")}"><span class="erpw-list-inline-open-label">${escapeHtml(value || "-")}</span><span class="erpw-list-inline-open-icon" aria-hidden="true">&rarr;</span></button>`
                    : `<span class="erpw-list-cell-value">${escapeHtml(value || "-")}</span>`;
                  return `<td>${valueMarkup}${meta ? `<span class="erpw-list-cell-meta">${escapeHtml(meta)}</span>` : ""}</td>`;
                }).join("")}
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;
  }

  function renderSection(title, note, table) {
    return `
      <section class="erpw-child-card erpw-list-results">
        <div class="erpw-child-section-header">
          <div class="erpw-child-section-header-copy">
            <div class="erpw-child-section-header-title">${escapeHtml(title)}</div>
            <div class="erpw-child-section-header-note">${escapeHtml(note)}</div>
          </div>
          <div class="erpw-child-section-header-status">Visibility only</div>
        </div>
        ${renderTable(table || {})}
      </section>
    `;
  }

  function extraSections(payload) {
    const detail = (payload && payload.detail) || {};
    const state = detail.state || {};
    if (state.kind && state.kind !== "ready") {
      return `
        <section class="erpw-child-card erpw-list-results">
          <div class="erpw-list-state ${escapeHtml(state.kind)}">
            <div class="erpw-list-state-title">${escapeHtml(state.title || "Supplier detail unavailable")}</div>
            <div class="erpw-list-state-detail">${escapeHtml(state.detail || "This supplier page is not available.")}</div>
          </div>
        </section>
      `;
    }
    return `
      ${renderSection("Open or overdue purchase orders", "Buyer follow-up posture for visible purchase orders.", detail.open_purchase_orders)}
      ${renderSection("Recent purchase orders", "Recent buying activity for this supplier.", detail.recent_purchase_orders)}
      ${renderSection("RFQs", "Visible RFQ invitations and response posture for this supplier.", detail.rfqs)}
      ${renderSection("Supplier quotations", "Recent visible supplier quotation context.", detail.supplier_quotations)}
      ${renderSection("Buying contacts", "Visible contact records linked to this supplier.", detail.contacts)}
    `;
  }

  function mountPayload(viewState, payload) {
    if (viewState.page && typeof viewState.page.set_title === "function" && payload.page && payload.page.title) {
      viewState.page.set_title(payload.page.title);
    }
    const routeSignature = viewState.routeSignature || "";
    ensureDetailRuntime().then((runtime) => {
      if (viewState.routeSignature !== routeSignature) return;
      runtime.renderShellContent(viewState.$shell, {
        summary: payload.summary || {},
        actions: normalizeActions(payload, viewState),
        actionLayout: { mode: "toolbar", sparseSecondaryThreshold: 3 },
        extraSectionsHtml: extraSections(payload),
        guidance: {},
      });
      viewState.$shell.off("click.erpWProcurementSupplierDetailRoute").on("click.erpWProcurementSupplierDetailRoute", "[data-erpw-procurement-detail-route]", function (event) {
        event.preventDefault();
        const route = String($(this).attr("data-erpw-procurement-detail-route") || "");
        const name = String($(this).attr("data-erpw-procurement-detail-name") || "");
        if (route === PO_DETAIL_ROUTE) routeToPurchaseOrderFollowUp(name);
      });
    }).catch((error) => {
      if (viewState.routeSignature !== routeSignature) return;
      viewState.$shell.html(`
        <section class="erpw-child-card">
          <div class="erpw-list-state error">
            <div class="erpw-list-state-title">Supplier detail could not be loaded</div>
            <div class="erpw-list-state-detail">${escapeHtml(error && error.message ? error.message : "The shared detail runtime could not be loaded.")}</div>
          </div>
        </section>
      `);
    });
  }

  function loadingPayload(supplierName) {
    return {
      page: { title: "Supplier Detail" },
      summary: {
        kicker: "Procurement supplier",
        title: supplierName || "Supplier Detail",
        subtitle: "Loading read-only supplier buying context.",
        chips: [{ label: "Loading", tone: "pending" }],
        facts: [],
      },
      controls: { actions: [] },
      detail: {
        state: { kind: "loading", title: "Loading supplier", detail: "Reading supplier buying context." },
      },
    };
  }

  function unavailablePayload(error) {
    return {
      page: { title: "Supplier Detail" },
      summary: {
        kicker: "Procurement supplier",
        title: "Supplier detail unavailable",
        subtitle: error && error.message ? error.message : "The supplier page could not be loaded.",
        chips: [{ label: "error", tone: "blocker" }],
        facts: [],
      },
      detail: {
        state: { kind: "error", title: "Supplier detail failed", detail: error && error.message ? error.message : "The page could not load." },
      },
    };
  }

  function loadRoute(viewState, options) {
    const settings = options && typeof options === "object" ? options : {};
    const route = currentRouteParts();
    const supplierName = resolveSupplier(route);
    const routeSignature = Array.isArray(route) ? route.join("|") : "";
    const cacheKey = routeSignature || supplierName || "supplier-detail";
    const cached = contextRequestCache[cacheKey];
    viewState.routeSignature = routeSignature;
    traceDetailLoad({ type: "loadRoute", routeSignature, cacheKey, refresh: Boolean(settings.refresh), name: supplierName, hasCachedRequest: Boolean(cached && cached.request), hasCachedPayload: Boolean(cached && cached.payload), cachedAgeMs: cached && cached.loadedAt ? Date.now() - cached.loadedAt : null });

    if (!settings.refresh && cached && cached.request) {
      traceDetailLoad({ type: "cache-request-reuse", routeSignature, cacheKey, name: supplierName, mount: cached.payload ? "cached-payload" : "loading" });
      mountPayload(viewState, cached.payload || loadingPayload(supplierName));
      cached.request.then((payload) => {
        traceDetailLoad({ type: "cache-request-resolved", routeSignature, cacheKey, name: supplierName, routeStillActive: viewState.routeSignature === routeSignature });
        if (viewState.routeSignature === routeSignature) mountPayload(viewState, payload || {});
      });
      return cached.request;
    }

    if (!settings.refresh && cached && cached.payload && Date.now() - cached.loadedAt < SAME_ROUTE_CACHE_TTL_MS) {
      traceDetailLoad({ type: "cache-payload-reuse", routeSignature, cacheKey, name: supplierName, cachedAgeMs: Date.now() - cached.loadedAt });
      mountPayload(viewState, cached.payload);
      return Promise.resolve(cached.payload);
    }

    traceDetailLoad({ type: "request-start", routeSignature, cacheKey, name: supplierName });
    mountPayload(viewState, loadingPayload(supplierName));
    const entry = { request: null, payload: null, loadedAt: 0 };
    contextRequestCache[cacheKey] = entry;
    entry.request = frappe.call({
      method: CONTEXT_METHOD,
      args: {
        supplier: supplierName,
      },
    }).then((response) => {
      const payload = response && response.message ? response.message : {};
      entry.payload = payload;
      entry.loadedAt = Date.now();
      traceDetailLoad({ type: "request-success", routeSignature, cacheKey, name: supplierName, routeStillActive: viewState.routeSignature === routeSignature });
      if (viewState.routeSignature === routeSignature) mountPayload(viewState, payload);
      return payload;
    }).catch((error) => {
      const payload = unavailablePayload(error);
      entry.payload = payload;
      entry.loadedAt = Date.now();
      traceDetailLoad({ type: "request-error", routeSignature, cacheKey, name: supplierName, routeStillActive: viewState.routeSignature === routeSignature, message: error && error.message ? error.message : String(error || "") });
      if (viewState.routeSignature === routeSignature) mountPayload(viewState, payload);
      return payload;
    });
    entry.request.then(() => {
      if (contextRequestCache[cacheKey] === entry) entry.request = null;
    });
    return entry.request;
  }

  function cleanupRouteShells() {
    if (window.erpWorkspaceUiBoot && typeof window.erpWorkspaceUiBoot.cleanupProcurementRouteShells === "function") {
      window.erpWorkspaceUiBoot.cleanupProcurementRouteShells(PAGE_KEY, { removeActive: true });
    }
  }

  function pruneRouteShells(keepNode) {
    if (window.erpWorkspaceUiBoot && typeof window.erpWorkspaceUiBoot.pruneProcurementRouteShells === "function") {
      window.erpWorkspaceUiBoot.pruneProcurementRouteShells(PAGE_KEY, keepNode);
      setTimeout(() => window.erpWorkspaceUiBoot.pruneProcurementRouteShells(PAGE_KEY, keepNode), 0);
      setTimeout(() => window.erpWorkspaceUiBoot.pruneProcurementRouteShells(PAGE_KEY, keepNode), 80);
    }
  }

  function render(wrapper) {
    cleanupRouteShells();
    const page = makeDetailPage(wrapper);
    cleanupManagedPageChrome(wrapper);
    const hosts = ensureHost(page, wrapper);
    const viewState = {
      page,
      $host: hosts.$host,
      $shell: hosts.$shell,
    };
    wrapper.__erpwProcurementSupplierDetail = viewState;
    pruneRouteShells(hosts.$host.get(0));
    loadRoute(viewState);
  }

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) { render(wrapper); };
  frappe.pages[PAGE_KEY].on_page_show = function (wrapper) {
    if (window.erpWorkspaceConsoleSidebar && typeof window.erpWorkspaceConsoleSidebar.refresh === "function") {
      window.erpWorkspaceConsoleSidebar.refresh();
    }
    const existing = wrapper && wrapper.__erpwProcurementSupplierDetail;
    if (existing && isAttached(existing.$host) && isAttached(existing.$shell)) {
      cleanupManagedPageChrome(wrapper);
      loadRoute(existing);
      return;
    }
    render(wrapper);
  };
})();
