/* global frappe, $ */

(function () {
  const workspaceRegistry = window.erpWorkspaceUiWorkspaceRegistry || {};
  const procurementWorkspace = typeof workspaceRegistry.procurement === "function" ? workspaceRegistry.procurement() : null;
  const procurementRoutes = procurementWorkspace && procurementWorkspace.routes ? procurementWorkspace.routes : {};
  const procurementMethods = procurementWorkspace && procurementWorkspace.methods ? procurementWorkspace.methods : {};
  const PAGE_KEY = procurementRoutes.worklist || "procurement-console-worklist";
  const HOME_ROUTE = procurementRoutes.home || "procurement-console";
  const CONTEXT_METHOD = procurementMethods.worklistContext || "erp_workspace_ui.procurement_console.worklist.get_procurement_console_worklist_context";
  let activeViewState = null;
  const SAME_ROUTE_CACHE_TTL_MS = 5000;
  const contextLoadCache = Object.create(null);

  function ensureProcurementChromeStyle() {
    if (document.getElementById("erpw-procurement-managed-chrome-style")) return;
    const style = document.createElement("style");
    style.id = "erpw-procurement-managed-chrome-style";
    style.textContent = [
      '.page-head[data-erpw-procurement-managed-chrome="1"] .page-icon,',
      '.page-head[data-erpw-procurement-managed-chrome="1"] .indicator-pill,',
      '.page-head[data-erpw-procurement-managed-chrome="1"] .title-area > .icon,',
      '.page-head[data-erpw-procurement-managed-chrome="1"] .title-area > svg { display: none !important; }',
    ].join("\n");
    document.head.appendChild(style);
  }

  function titleFromQueueKey(queueKey) {
    return String(queueKey || "")
      .replace(/[_-]+/g, " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase()) || "Procurement Queue";
  }

  function routeToWorklist(queueKey, filters) {
    frappe.route_options = filters && Object.keys(filters).length ? filters : {};
    frappe.set_route(PAGE_KEY, String(queueKey || "").replace(/_/g, "-"));
  }

  function routeToList(doctype, filters) {
    frappe.route_options = filters && Object.keys(filters).length ? filters : {};
    frappe.set_route("List", doctype);
  }

  function routeToReport(reportName, filters) {
    frappe.route_options = filters && Object.keys(filters).length ? filters : {};
    frappe.set_route("query-report", reportName);
  }

  function resolveQueueKey(route) {
    return Array.isArray(route) && route.length > 1 ? String(route[1] || "").replace(/-/g, "_") : "";
  }

  function pathRouteSignature() {
    const path = String(window.location && window.location.pathname || "").replace(/^\/+/, "");
    const parts = path.split("/").filter(Boolean);
    const routeParts = parts[0] === "desk" || parts[0] === "app" ? parts.slice(1) : parts;
    return routeParts.map((part) => {
      try {
        return decodeURIComponent(part || "");
      } catch (error) {
        return part || "";
      }
    }).join("|");
  }

  function isCurrentWorklistRoute(routeSignature) {
    const pathSignature = pathRouteSignature();
    if (pathSignature === routeSignature) return true;
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) && String(route[0] || "") === PAGE_KEY && route.join("|") === routeSignature;
  }

  function consumeRouteFilters() {
    const options = frappe.route_options && typeof frappe.route_options === "object"
      ? Object.assign({}, frappe.route_options)
      : null;
    frappe.route_options = {};
    return options;
  }

  function stableStringify(value) {
    if (!value || typeof value !== "object") return "{}";
    const keys = Object.keys(value).sort();
    const normalized = {};
    keys.forEach((key) => {
      const current = value[key];
      if (current !== undefined && current !== null && String(current) !== "") normalized[key] = current;
    });
    return JSON.stringify(normalized);
  }


  function ensureHost(page, wrapper) {
    const $parent = page && page.body ? $(page.body) : $(wrapper);
    let $host = $parent.children(".erpw-procurement-console-worklist-page").first();
    if (!$host.length) {
      $host = $('<section class="erpw-procurement-console-worklist-page"></section>');
      $parent.empty().append($host);
    }
    return $host;
  }

  function isAttached($node) {
    const node = $node && $node.get ? $node.get(0) : null;
    return Boolean(node && document.documentElement.contains(node));
  }

  function collectFilterValues($host) {
    const values = {};
    if (!$host || !$host.length) return values;
    $host.find("[data-erpw-list-field-key]").each(function () {
      const $field = $(this);
      const key = ($field.attr("data-erpw-list-field-key") || "").trim();
      if (!key) return;
      const value = ($field.val() || "").toString().trim();
      if (value) values[key] = value;
    });
    return values;
  }

  function collectHiddenFilterValues($host) {
    const values = {};
    if (!$host || !$host.length) return values;
    $host.find('[data-erpw-list-field-type="hidden"][data-erpw-list-field-key]').each(function () {
      const $field = $(this);
      const key = ($field.attr("data-erpw-list-field-key") || "").trim();
      if (!key) return;
      const value = ($field.val() || "").toString().trim();
      if (value) values[key] = value;
    });
    return values;
  }

  function resetVisibleFilterFields($host) {
    if (!$host || !$host.length) return;
    $host.find('[data-erpw-list-field-key]').each(function () {
      const $field = $(this);
      if (($field.attr("data-erpw-list-field-type") || "") === "hidden") return;
      $field.val("");
    });
  }

  function resolveActionTarget(payload, details) {
    const targets = (payload && payload.action_targets) || {};
    if (details.scope === "row") {
      return targets["row:" + details.rowKey + ":" + details.key] || null;
    }
    return targets[details.scope + ":" + details.key] || targets[details.key] || null;
  }

  function executeTarget(target) {
    if (!target) return;
    if (target.kind === "page" && target.route) {
      const routeParts = Array.isArray(target.route_parts) ? target.route_parts : [];
      frappe.route_options = target.options && typeof target.options === "object" ? Object.assign({}, target.options) : {};
      return frappe.set_route.apply(frappe, [target.route].concat(routeParts));
    }
    if (target.kind === "list" && target.doctype) return routeToList(target.doctype, target.filters || null);
    if (target.kind === "report" && target.report_name) return routeToReport(target.report_name, target.filters || null);
    if (target.kind === "worklist" && target.queue_key) return routeToWorklist(target.queue_key, target.filters || null);
  }

  function loadingConfig(queueKey) {
    return {
      summary: {
        title: "Loading Procurement Queue",
        subtitle: "Reading live ERP records for " + String(queueKey || "this queue").replace(/_/g, " ") + ".",
      },
      results: {
        title: "Preparing queue",
        state: {
          kind: "loading",
          title: "Loading queue",
          detail: "Pulling live records and permission scope.",
        },
      },
    };
  }

  function routeMissingConfig() {
    return {
      summary: {
        title: "Procurement queue unavailable",
        subtitle: "Open this page from a Procurement Console card so the queue key is passed through.",
      },
      controls: { actions: [{ key: "refresh", label: "Refresh" }] },
      results: {
        title: "Queue state",
        state: {
          kind: "unavailable",
          title: "Queue unavailable",
          detail: "The requested Procurement Console queue is not available from this route.",
        },
      },
    };
  }

  function setDataRefreshing(viewState, enabled) {
    const runtime = window.erpWorkspaceUiListPage && window.erpWorkspaceUiListPage.shell;
    if (!runtime || typeof runtime.setDataRefreshing !== "function") return;
    runtime.setDataRefreshing(viewState && viewState.$host, enabled);
  }

  function cleanupDuplicateWorklistChrome($wrapper, title) {
    const wrapper = $wrapper && $wrapper.jquery ? $wrapper : $($wrapper || []);
    const heads = wrapper.find(".page-head").toArray();
    if (!heads.length) return null;
    const expectedTitle = String(title || "").replace(/\s+/g, " ").trim();
    const keep = heads.find((head) => {
      const text = String((head && head.textContent) || "").replace(/\s+/g, " ").trim();
      return expectedTitle && text.indexOf(expectedTitle) !== -1;
    }) || heads[0];
    heads.forEach((head) => {
      if (head !== keep && head.parentNode) head.parentNode.removeChild(head);
    });
    const $keep = $(keep);
    $keep.attr("data-erpw-procurement-managed-chrome", "1");
    $keep.find(".page-icon, .indicator-pill, .title-area > .icon, .title-area > svg").remove();
    return $keep;
  }

  function syncWorklistChromeTitle(viewState, payload) {
    if (!viewState || !viewState.page) return;
    ensureProcurementChromeStyle();
    const route = frappe.get_route ? frappe.get_route() : [];
    const fallbackTitle = titleFromQueueKey(resolveQueueKey(route));
    const title = payload && payload.page && payload.page.title ? payload.page.title : fallbackTitle;
    if (typeof viewState.page.set_title === "function") viewState.page.set_title(title);
    const $wrapper = viewState.page.wrapper ? $(viewState.page.wrapper) : $();
    cleanupDuplicateWorklistChrome($wrapper, title);
    $wrapper.find(".page-title .title-text, .title-area .title-text").first().text(title);
    const $breadcrumbs = $wrapper.find(".navbar-breadcrumbs").first();
    if ($breadcrumbs.length) {
      $breadcrumbs.html([
        '<li><a href="/desk/' + HOME_ROUTE + '" data-erpw-procurement-home="1">Procurement Console</a></li>',
        '<li><a class="title-text" aria-current="page">' + frappe.utils.escape_html(title) + '</a></li>',
      ].join(""));
    }
    cleanupDuplicateWorklistChrome($wrapper, title);
    setTimeout(() => cleanupDuplicateWorklistChrome($wrapper, title), 0);
    setTimeout(() => cleanupDuplicateWorklistChrome($wrapper, title), 120);
    $wrapper.off("click.erpWProcurementWorklistChrome").on("click.erpWProcurementWorklistChrome", "[data-erpw-procurement-home]", function (event) {
      event.preventDefault();
      frappe.set_route(HOME_ROUTE);
    });
  }

  function mountPayload(viewState, payload, options) {
    if (viewState && viewState.routeSignature && !isCurrentWorklistRoute(viewState.routeSignature)) return;
    const runtime = window.erpWorkspaceUiListPage && window.erpWorkspaceUiListPage.shell;
    if (!runtime || typeof runtime.mountWorklist !== "function") {
      viewState.$host.html('<div class="erpw-list-shell"><section class="erpw-child-card erpw-list-results"><div class="erpw-list-state error"><div class="erpw-list-state-title">List runtime unavailable</div><div class="erpw-list-state-detail">Shared worklist runtime is not loaded on this page.</div></div></section></div>');
      return;
    }
    const config = Object.assign({}, payload || {}, {
      workspace: "procurement",
      page: Object.assign({ workspace: "procurement" }, payload && payload.page ? payload.page : {}),
      onAction(details) {
        if (!details) return;
        if (details.key === "refresh") return loadRoute(viewState, viewState.activeFilters || {}, { partialDataRefresh: true });
        if (details.key === "back_to_console") return frappe.set_route(HOME_ROUTE);
        if (details.key === "apply_filters") return loadRoute(viewState, collectFilterValues(viewState.$host), { partialDataRefresh: true });
        if (details.key === "reset_filters") {
          const resetFilters = collectHiddenFilterValues(viewState.$host);
          resetVisibleFilterFields(viewState.$host);
          return loadRoute(viewState, resetFilters, { partialDataRefresh: true, refreshControls: true });
        }
        executeTarget(resolveActionTarget(payload, details));
      },
    });

    if (options && options.partialDataRefresh && typeof runtime.refreshWorklistData === "function") {
      runtime.refreshWorklistData(viewState.$host, config, { refreshControls: Boolean(options.refreshControls) });
    } else {
      runtime.mountWorklist(viewState.$host, config);
    }
  }

  function loadRoute(viewState, nextFilters, options) {
    const settings = options && typeof options === "object" ? options : {};
    const route = frappe.get_route ? frappe.get_route() : [];
    const queueKey = resolveQueueKey(route);
    const routeSignature = Array.isArray(route) ? route.join("|") : "";
    viewState.routeSignature = routeSignature;
    const routedFilters = nextFilters === undefined ? consumeRouteFilters() : null;
    viewState.activeFilters = nextFilters !== undefined ? Object.assign({}, nextFilters || {}) : Object.assign({}, routedFilters || viewState.activeFilters || {});
    const loadKey = routeSignature + "|" + stableStringify(viewState.activeFilters || {});

    if (!queueKey) {
      mountPayload(viewState, routeMissingConfig());
      return Promise.resolve();
    }

    if (!settings.partialDataRefresh && !settings.refresh && viewState.currentLoadKey === loadKey) {
      if (viewState.inFlightRequest) return viewState.inFlightRequest;
      if (viewState.lastPayload && viewState.lastLoadedAt && Date.now() - viewState.lastLoadedAt < SAME_ROUTE_CACHE_TTL_MS) {
        return Promise.resolve(viewState.lastPayload);
      }
    }

    if (!settings.partialDataRefresh && !settings.refresh) {
      const cachedLoad = contextLoadCache[loadKey];
      if (cachedLoad && cachedLoad.request) {
        if (viewState.loadingLoadKey !== loadKey && viewState.mountedPayloadLoadKey !== loadKey) {
          viewState.loadingLoadKey = loadKey;
          mountPayload(viewState, loadingConfig(queueKey));
        }
        const joinedRequest = cachedLoad.request.then((payload) => {
          if (viewState.routeSignature !== routeSignature || !isCurrentWorklistRoute(routeSignature)) return payload;
          viewState.lastPayload = payload;
          viewState.lastLoadedAt = Date.now();
          viewState.loadingLoadKey = "";
          viewState.mountedPayloadLoadKey = loadKey;
          syncWorklistChromeTitle(viewState, payload || {});
          mountPayload(viewState, payload || {}, { refreshControls: Boolean(settings.refreshControls) });
          return payload;
        });
        viewState.currentLoadKey = loadKey;
        viewState.inFlightRequest = joinedRequest;
        joinedRequest.then(() => {
          if (viewState.inFlightRequest === joinedRequest) viewState.inFlightRequest = null;
        });
        return joinedRequest;
      }
      if (cachedLoad && cachedLoad.payload && cachedLoad.loadedAt && Date.now() - cachedLoad.loadedAt < SAME_ROUTE_CACHE_TTL_MS) {
        viewState.currentLoadKey = loadKey;
        viewState.lastPayload = cachedLoad.payload;
        viewState.lastLoadedAt = cachedLoad.loadedAt;
        viewState.loadingLoadKey = "";
        if (viewState.mountedPayloadLoadKey !== loadKey) {
          viewState.mountedPayloadLoadKey = loadKey;
          syncWorklistChromeTitle(viewState, cachedLoad.payload || {});
          mountPayload(viewState, cachedLoad.payload || {}, { refreshControls: Boolean(settings.refreshControls) });
        }
        return Promise.resolve(cachedLoad.payload);
      }
    }

    viewState.currentLoadKey = loadKey;
    const requestToken = (viewState.requestToken || 0) + 1;
    viewState.requestToken = requestToken;
    const partialDataRefresh = Boolean(settings.partialDataRefresh && viewState.$host && viewState.$host.find(".erpw-list-shell").length);
    if (partialDataRefresh) {
      setDataRefreshing(viewState, true);
    } else if (viewState.loadingLoadKey !== loadKey) {
      viewState.loadingLoadKey = loadKey;
      mountPayload(viewState, loadingConfig(queueKey));
    }

    const request = frappe.call({
      method: CONTEXT_METHOD,
      args: {
        queue_key: queueKey,
        filters: viewState.activeFilters || {},
      },
    }).then((response) => {
      if (viewState.routeSignature !== routeSignature || viewState.requestToken !== requestToken || !isCurrentWorklistRoute(routeSignature)) return null;
      const payload = response && response.message ? response.message : {};
      viewState.lastPayload = payload;
      viewState.lastLoadedAt = Date.now();
      viewState.loadingLoadKey = "";
      viewState.mountedPayloadLoadKey = loadKey;
      contextLoadCache[loadKey] = { payload, loadedAt: viewState.lastLoadedAt, request: null };
      syncWorklistChromeTitle(viewState, payload);
      mountPayload(viewState, payload, { partialDataRefresh, refreshControls: Boolean(settings.refreshControls) });
      return payload;
    }).catch((error) => {
      if (viewState.routeSignature !== routeSignature || viewState.requestToken !== requestToken || !isCurrentWorklistRoute(routeSignature)) return null;
      setDataRefreshing(viewState, false);
      const payload = {
        summary: {
          title: "Procurement queue unavailable",
          subtitle: "The queue could not be loaded right now.",
        },
        controls: { actions: [{ key: "refresh", label: "Refresh" }] },
        results: {
          title: "Queue state",
          state: {
            kind: "error",
            title: "Queue context failed",
            detail: error && error.message ? error.message : "The operational queue could not be loaded.",
          },
        },
      };
      viewState.lastPayload = payload;
      viewState.lastLoadedAt = Date.now();
      viewState.loadingLoadKey = "";
      viewState.mountedPayloadLoadKey = loadKey;
      contextLoadCache[loadKey] = { payload, loadedAt: viewState.lastLoadedAt, request: null };
      mountPayload(viewState, payload);
      return payload;
    });
    viewState.inFlightRequest = request;
    if (!settings.partialDataRefresh && !settings.refresh) {
      contextLoadCache[loadKey] = { request, payload: null, loadedAt: 0 };
    }
    request.then(() => {
      if (viewState.inFlightRequest === request) viewState.inFlightRequest = null;
      const cachedLoad = contextLoadCache[loadKey];
      if (cachedLoad && cachedLoad.request === request) cachedLoad.request = null;
    });
    return request;
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
    const page = frappe.ui.make_app_page({
      parent: wrapper,
      title: "Procurement Console",
      single_column: true,
    });
    const viewState = {
      page,
      $host: ensureHost(page, wrapper),
      routeSignature: "",
      activeFilters: {},
    };
    wrapper.__erpwProcurementConsoleWorklist = viewState;
    activeViewState = viewState;
    syncWorklistChromeTitle(viewState);
    pruneRouteShells(viewState.$host.get(0));
    loadRoute(viewState);
  }

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) { render(wrapper); };
  frappe.pages[PAGE_KEY].on_page_show = function (wrapper) {
    const existing = wrapper && wrapper.__erpwProcurementConsoleWorklist;
    if (existing && isAttached(existing.$host)) {
      activeViewState = existing;
      loadRoute(existing);
      return;
    }
    render(wrapper);
  };
})();
