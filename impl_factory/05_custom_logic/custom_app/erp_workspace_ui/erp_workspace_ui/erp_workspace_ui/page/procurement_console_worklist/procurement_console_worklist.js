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

  function consumeRouteFilters() {
    const options = frappe.route_options && typeof frappe.route_options === "object"
      ? Object.assign({}, frappe.route_options)
      : null;
    frappe.route_options = {};
    return options;
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
    if (target.kind === "form" && target.doctype && target.name) return frappe.set_route("Form", target.doctype, target.name);
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

  function mountPayload(viewState, payload, options) {
    const runtime = window.erpWorkspaceUiListPage && window.erpWorkspaceUiListPage.shell;
    if (!runtime || typeof runtime.mountWorklist !== "function") {
      viewState.$host.html('<div class="erpw-list-shell"><section class="erpw-child-card erpw-list-results"><div class="erpw-list-state error"><div class="erpw-list-state-title">List runtime unavailable</div><div class="erpw-list-state-detail">Shared worklist runtime is not loaded on this page.</div></div></section></div>');
      return;
    }
    const config = Object.assign({}, payload || {}, {
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
    const requestToken = (viewState.requestToken || 0) + 1;
    viewState.requestToken = requestToken;
    const routedFilters = nextFilters === undefined ? consumeRouteFilters() : null;
    viewState.activeFilters = nextFilters !== undefined ? Object.assign({}, nextFilters || {}) : Object.assign({}, routedFilters || viewState.activeFilters || {});

    if (!queueKey) {
      mountPayload(viewState, routeMissingConfig());
      return;
    }

    const partialDataRefresh = Boolean(settings.partialDataRefresh && viewState.$host && viewState.$host.find(".erpw-list-shell").length);
    if (partialDataRefresh) {
      setDataRefreshing(viewState, true);
    } else {
      mountPayload(viewState, loadingConfig(queueKey));
    }

    frappe.call({
      method: CONTEXT_METHOD,
      args: {
        queue_key: queueKey,
        filters: viewState.activeFilters || {},
      },
    }).then((response) => {
      if (viewState.routeSignature !== routeSignature || viewState.requestToken !== requestToken) return;
      const payload = response && response.message ? response.message : {};
      if (viewState.page && typeof viewState.page.set_title === "function" && payload.page && payload.page.title) {
        viewState.page.set_title(payload.page.title);
      }
      mountPayload(viewState, payload, { partialDataRefresh, refreshControls: Boolean(settings.refreshControls) });
    }).catch((error) => {
      if (viewState.routeSignature !== routeSignature || viewState.requestToken !== requestToken) return;
      setDataRefreshing(viewState, false);
      mountPayload(viewState, {
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
      });
    });
  }

  function cleanupRouteShells() {
    if (window.erpWorkspaceUiBoot && typeof window.erpWorkspaceUiBoot.cleanupProcurementRouteShells === "function") {
      window.erpWorkspaceUiBoot.cleanupProcurementRouteShells(PAGE_KEY);
    }
  }

  function render(wrapper) {
    cleanupRouteShells();
    const page = frappe.ui.make_app_page({
      parent: wrapper,
      title: "Procurement Console Worklist",
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
    loadRoute(viewState);
  }

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) { render(wrapper); };
  frappe.pages[PAGE_KEY].on_page_show = function (wrapper) {
    if (wrapper && wrapper.__erpwProcurementConsoleWorklist) {
      activeViewState = wrapper.__erpwProcurementConsoleWorklist;
      loadRoute(wrapper.__erpwProcurementConsoleWorklist);
      return;
    }
    render(wrapper);
  };
})();
