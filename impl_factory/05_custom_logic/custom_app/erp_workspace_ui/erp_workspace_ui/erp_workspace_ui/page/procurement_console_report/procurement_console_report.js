/* global frappe, $ */

(function () {
  const workspaceRegistry = window.erpWorkspaceUiWorkspaceRegistry || {};
  const procurementWorkspace = typeof workspaceRegistry.procurement === "function" ? workspaceRegistry.procurement() : null;
  const procurementRoutes = procurementWorkspace && procurementWorkspace.routes ? procurementWorkspace.routes : {};
  const procurementMethods = procurementWorkspace && procurementWorkspace.methods ? procurementWorkspace.methods : {};
  const PAGE_KEY = procurementRoutes.report || "procurement-console-report";
  const HOME_ROUTE = procurementRoutes.home || "procurement-console";
  const WORKLIST_ROUTE = procurementRoutes.worklist || "procurement-console-worklist";
  const CONTEXT_METHOD = procurementMethods.reportContext || "erp_workspace_ui.procurement_console.report.get_procurement_console_report_context";
  const REPORT_CHROME_TITLE = "Procurement Console Report";
  const REPORT_SHELL_URL = "/assets/erp_workspace_ui/js/runtime/report_page/report_page_shell.js?v=2026-05-02-report-link-suggest-v1";
  const REPORT_SHELL_VERSION = "2026-05-02-report-link-suggest-v1";

  function routeToWorklist(queueKey, filters) {
    frappe.route_options = filters && Object.keys(filters).length ? filters : null;
    frappe.set_route(WORKLIST_ROUTE, String(queueKey || "").replace(/_/g, "-"));
  }

  function routeToReport(reportName, filters) {
    frappe.route_options = filters && Object.keys(filters).length ? filters : null;
    frappe.set_route("query-report", reportName);
  }

  function executeTarget(target) {
    if (!target) return;
    if (target.kind === "form" && target.doctype && target.name) return frappe.set_route("Form", target.doctype, target.name);
    if (target.kind === "worklist" && target.queue_key) return routeToWorklist(target.queue_key, target.filters || null);
    if (target.kind === "report" && target.report_name) return routeToReport(target.report_name, target.filters || null);
  }

  function resolveReportKey(route) {
    return Array.isArray(route) && route.length > 1 ? String(route[1] || "").replace(/-/g, "_") : "";
  }

  function loadingConfig(reportKey) {
    const labelMap = {
      supplier_quotation_comparison: "Supplier Quotation Comparison",
    };
    const label = labelMap[reportKey] || REPORT_CHROME_TITLE;
    return {
      reportKey,
      page: { title: REPORT_CHROME_TITLE },
      summary: {
        kicker: "Procurement Console report",
        title: label,
        subtitle: "Loading live ERP report context.",
      },
      results: {
        title: "Report state",
        state: {
          kind: "loading",
          title: "Loading report",
          detail: "Reading live report output and shaping the productized review surface.",
        },
      },
      action_targets: {},
    };
  }

  function errorConfig(message) {
    return {
      reportKey: "",
      page: { title: REPORT_CHROME_TITLE },
      summary: {
        kicker: "Procurement Console report",
        title: "Report unavailable",
        subtitle: "This route could not be resolved into a supported Procurement Console report.",
      },
      controls: {
        actions: [
          { key: "back_to_console", label: "Back to Procurement Console" },
          { key: "refresh", label: "Refresh" },
        ],
      },
      results: {
        title: "Report state",
        state: {
          kind: "error",
          title: "Report context failed",
          detail: message || "Live report context could not be loaded right now.",
        },
      },
      action_targets: {},
    };
  }

  function ensureHost(page, wrapper) {
    const $parent = page && page.body ? $(page.body) : $(wrapper);
    let $host = $parent.children(".erpw-procurement-console-report-page").first();
    if (!$host.length) {
      $host = $('<section class="erpw-procurement-console-report-page"></section>');
      $parent.empty().append($host);
    }
    return $host;
  }

  function syncReportChromeTitle(viewState, payload) {
    if (!viewState || !viewState.page) return;
    const payloadTitle = payload && payload.page && payload.page.title ? payload.page.title : "";
    const chromeTitle = payloadTitle || REPORT_CHROME_TITLE;
    if (typeof viewState.page.set_title === "function") {
      viewState.page.set_title(chromeTitle);
    }
    const $wrapper = viewState.page.wrapper ? $(viewState.page.wrapper) : $();
    $wrapper.find(".page-title .title-text, .title-area .title-text").first().text(chromeTitle);
  }

  function ensureReportRuntime() {
    const runtime = window.erpWorkspaceUiReportPage && window.erpWorkspaceUiReportPage.shell;
    if (runtime && typeof runtime.mountReport === "function" && runtime.version === REPORT_SHELL_VERSION) {
      return Promise.resolve(runtime);
    }
    return new Promise((resolve, reject) => {
      frappe.require(REPORT_SHELL_URL, () => {
        const refreshed = window.erpWorkspaceUiReportPage && window.erpWorkspaceUiReportPage.shell;
        if (refreshed && typeof refreshed.mountReport === "function") {
          resolve(refreshed);
          return;
        }
        reject(new Error("Shared report runtime is not loaded on this page."));
      });
    });
  }

  function setDataRefreshing(viewState, enabled) {
    const runtime = window.erpWorkspaceUiReportPage && window.erpWorkspaceUiReportPage.shell;
    if (!runtime || typeof runtime.setDataRefreshing !== "function") return;
    runtime.setDataRefreshing(viewState && viewState.$host, enabled);
  }

  function setControlFieldValue(field, value) {
    if (!field) return;
    const nextValue = value == null ? "" : String(value);
    if (String(field.tagName || "").toLowerCase() === "select") {
      const hasExactOption = Array.from(field.options || []).some((option) => String(option.value) === nextValue);
      if (hasExactOption) {
        field.value = nextValue;
      } else {
        field.selectedIndex = 0;
      }
      return;
    }
    field.value = nextValue;
  }

  function resetControlFields(viewState) {
    const host = viewState && viewState.$host && viewState.$host.get ? viewState.$host.get(0) : null;
    if (!host) return;
    host.querySelectorAll("[data-erpw-control-key]").forEach((field) => {
      setControlFieldValue(field, "");
    });
  }

  function syncControlFieldValues(viewState, controls) {
    const host = viewState && viewState.$host && viewState.$host.get ? viewState.$host.get(0) : null;
    if (!host || !controls || typeof controls !== "object") return;
    const fields = Array.isArray(controls.fields) ? controls.fields : [];
    fields.forEach((field) => {
      if (!field || !field.key) return;
      const node = Array.from(host.querySelectorAll("[data-erpw-control-key]")).find((input) => {
        return String(input.getAttribute("data-erpw-control-key") || "") === String(field.key);
      });
      setControlFieldValue(node, field.value);
    });
  }

  function mountPayload(viewState, payload, options) {
    syncReportChromeTitle(viewState, payload);
    return ensureReportRuntime().then((runtime) => {
      const config = Object.assign({}, payload || {}, {
        reportKey: viewState.reportKey || "",
        onAction(details) {
          if (!details) return;
          if (details.key === "refresh") return loadRoute(viewState, { partialDataRefresh: true });
          if (details.key === "back_to_console") return frappe.set_route(HOME_ROUTE);
          executeTarget(((payload && payload.action_targets) || {})[details.key] || null);
        },
        onControlSubmit(details) {
          if (!details) return;
          if (details.mode === "reset") {
            viewState.filterOverrides = null;
            resetControlFields(viewState);
            loadRoute(viewState, { partialDataRefresh: true, refreshControls: true });
            return;
          }
          viewState.filterOverrides = details.values && Object.keys(details.values).length ? details.values : null;
          loadRoute(viewState, { partialDataRefresh: true });
        },
      });

      if (options && options.partialDataRefresh && typeof runtime.refreshReportData === "function") {
        runtime.refreshReportData(viewState.$host, config, { refreshControls: Boolean(options.refreshControls) });
        if (options.refreshControls) {
          syncControlFieldValues(viewState, payload && payload.controls);
        }
      } else {
        runtime.mountReport(viewState.$host, config);
      }
    }).catch(() => {
      viewState.$host.html('<section class="erpw-report-shell"><section class="erpw-report-card erpw-report-results"><div class="erpw-report-state error"><div class="erpw-report-state-title">Report runtime unavailable</div><div class="erpw-report-state-detail">Shared report runtime is not loaded on this page.</div></div></section></section>');
    });
  }

  function loadRoute(viewState, options) {
    const settings = options && typeof options === "object" ? options : {};
    syncReportChromeTitle(viewState);
    const route = frappe.get_route ? frappe.get_route() : [];
    const reportKey = resolveReportKey(route);
    const routeSignature = Array.isArray(route) ? route.join("|") : "";
    const requestToken = (viewState.requestToken || 0) + 1;
    viewState.requestToken = requestToken;

    if (viewState.reportKey && viewState.reportKey !== reportKey) {
      viewState.filterOverrides = null;
    }
    viewState.reportKey = reportKey;
    viewState.routeSignature = routeSignature;

    if (!reportKey) {
      mountPayload(viewState, errorConfig("Open this page from a Procurement Console report card so the report key is passed through."));
      return;
    }

    const partialDataRefresh = Boolean(settings.partialDataRefresh && viewState.$host && viewState.$host.find(".erpw-report-shell").length);
    if (partialDataRefresh) {
      setDataRefreshing(viewState, true);
    } else {
      mountPayload(viewState, loadingConfig(reportKey));
    }

    const args = { report_key: reportKey };
    if (viewState.filterOverrides && Object.keys(viewState.filterOverrides).length) {
      args.filter_overrides = viewState.filterOverrides;
    }

    frappe.call({ method: CONTEXT_METHOD, args }).then((response) => {
      if (viewState.routeSignature !== routeSignature || viewState.requestToken !== requestToken) return;
      const payload = response && response.message ? response.message : {};
      syncReportChromeTitle(viewState, payload);
      mountPayload(viewState, payload, { partialDataRefresh, refreshControls: Boolean(settings.refreshControls) });
    }).catch((error) => {
      if (viewState.routeSignature !== routeSignature || viewState.requestToken !== requestToken) return;
      setDataRefreshing(viewState, false);
      mountPayload(viewState, errorConfig(error && error.message ? error.message : "The report could not be loaded."));
    });
  }

  function render(wrapper) {
    const page = frappe.ui.make_app_page({
      parent: wrapper,
      title: REPORT_CHROME_TITLE,
      single_column: true,
    });
    syncReportChromeTitle({ page });
    const viewState = {
      page,
      $host: ensureHost(page, wrapper),
      routeSignature: "",
      reportKey: "",
      filterOverrides: null,
    };
    wrapper.__erpwProcurementConsoleReport = viewState;
    loadRoute(viewState);
  }

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) { render(wrapper); };
  frappe.pages[PAGE_KEY].on_page_show = function (wrapper) {
    if (wrapper && wrapper.__erpwProcurementConsoleReport) {
      loadRoute(wrapper.__erpwProcurementConsoleReport);
      return;
    }
    render(wrapper);
  };
})();
