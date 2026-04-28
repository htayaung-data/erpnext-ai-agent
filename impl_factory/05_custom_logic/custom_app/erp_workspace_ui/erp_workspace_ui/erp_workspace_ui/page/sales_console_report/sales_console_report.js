/* global frappe, $ */

(function () {
  const PAGE_KEY = "sales-console-report";
  const CONTEXT_METHOD = "erp_workspace_ui.sales_console.report.get_sales_console_report_context";
  const REPORT_SHELL_URL = "/assets/erp_workspace_ui/js/runtime/report_page/report_page_shell.js?v=2026-04-21-report-table-fit";
  const REPORT_SHELL_VERSION = "2026-04-21-report-table-fit";

  function routeToList(doctype, filters) {
    frappe.route_options = filters && Object.keys(filters).length ? filters : null;
    frappe.set_route("List", doctype);
  }

  function routeToReport(reportName, filters) {
    frappe.route_options = filters && Object.keys(filters).length ? filters : null;
    frappe.set_route("query-report", reportName);
  }

  function routeToWorklist(queueKey) {
    frappe.set_route("sales-console-worklist", String(queueKey || "").replace(/_/g, "-"));
  }

  function executeTarget(target) {
    if (!target) return;
    if (target.notice) {
      frappe.show_alert({ message: __(target.notice), indicator: "blue" });
    }
    const routeOwner = window.erpWorkspaceUiChildPage && window.erpWorkspaceUiChildPage.helpers;
    if (
      routeOwner
      && typeof routeOwner.routeToSalesConsoleTarget === "function"
      && routeOwner.routeToSalesConsoleTarget(target)
    ) {
      return;
    }
    if (target.kind === "new_doc" && target.doctype) return frappe.new_doc(target.doctype);
    if (target.kind === "form" && target.doctype && target.name) return frappe.set_route("Form", target.doctype, target.name);
    if (target.kind === "list" && target.doctype) return routeToList(target.doctype, target.filters || null);
    if (target.kind === "report" && target.report_name) return routeToReport(target.report_name, target.filters || null);
    if (target.kind === "worklist" && target.queue_key) return routeToWorklist(target.queue_key);
  }

  function loadingConfig(reportKey) {
    const labelMap = {
      sales_analytics: "Sales Analytics",
      sales_order_analysis: "Sales Order Analysis",
      quotation_trends: "Quotation Trends",
      collections_status: "Collections Status",
      payment_terms_status_sales_order: "Collections Status",
      item_wise_sales_history: "Item-wise Sales History",
      lost_quotations: "Lost Quotations",
    };
    const label = labelMap[reportKey] || "Sales Console Report";
    return {
      reportKey,
      page: { title: label },
      summary: {
        kicker: "Sales Console report",
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
      page: { title: "Sales Console Report" },
      summary: {
        kicker: "Sales Console report",
        title: "Report unavailable",
        subtitle: "This route could not be resolved into a supported Sales Console report.",
      },
      controls: {
        actions: [
          { key: "back_to_console", label: "Back to Sales Console" },
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
    let $host = $parent.children(".erpw-sales-console-report-page").first();
    if (!$host.length) {
      $host = $('<section class="erpw-sales-console-report-page"></section>');
      $parent.empty().append($host);
    }
    return $host;
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
        reject(new Error("Shared Sales Console report runtime is not loaded on this page."));
      });
    });
  }

  function mountPayload(viewState, payload) {
    return ensureReportRuntime().then((runtime) => {
      runtime.mountReport(viewState.$host, Object.assign({}, payload || {}, {
        reportKey: viewState.reportKey || "",
        onAction(details) {
          if (!details) return;
          if (details.key === "refresh") return loadRoute(viewState);
          if (details.key === "back_to_console") return frappe.set_route("sales-console");
          executeTarget(((payload && payload.action_targets) || {})[details.key] || null);
        },
        onControlSubmit(details) {
          if (!details) return;
          if (details.mode === "reset") {
            viewState.filterOverrides = null;
          } else {
            viewState.filterOverrides = details.values && Object.keys(details.values).length ? details.values : null;
          }
          loadRoute(viewState);
        },
      }));
    }).catch(() => {
      viewState.$host.html('<section class="erpw-report-shell"><section class="erpw-report-card erpw-report-results"><div class="erpw-report-state error"><div class="erpw-report-state-title">Report runtime unavailable</div><div class="erpw-report-state-detail">Shared Sales Console report runtime is not loaded on this page.</div></div></section></section>');
    });
  }

  function loadRoute(viewState) {
    const route = frappe.get_route ? frappe.get_route() : [];
    const reportKey = Array.isArray(route) && route.length > 1 ? String(route[1] || "").replace(/-/g, "_") : "";
    const routeSignature = Array.isArray(route) ? route.join("|") : "";

    if (viewState.reportKey && viewState.reportKey !== reportKey) {
      viewState.filterOverrides = null;
    }
    viewState.reportKey = reportKey;
    viewState.routeSignature = routeSignature;

    if (!reportKey) {
      mountPayload(viewState, errorConfig("Open this page from a Sales Console report card so the report key is passed through."));
      return;
    }

    mountPayload(viewState, loadingConfig(reportKey));

    const args = { report_key: reportKey };
    if (viewState.filterOverrides && Object.keys(viewState.filterOverrides).length) {
      args.filter_overrides = viewState.filterOverrides;
    }

    frappe.call({ method: CONTEXT_METHOD, args }).then((response) => {
      if (viewState.routeSignature !== routeSignature) return;
      const payload = response && response.message ? response.message : {};
      if (viewState.page && typeof viewState.page.set_title === "function" && payload.page && payload.page.title) {
        viewState.page.set_title(payload.page.title);
      }
      mountPayload(viewState, payload);
    }).catch((error) => {
      if (viewState.routeSignature !== routeSignature) return;
      mountPayload(viewState, errorConfig(error && error.message ? error.message : "The report could not be loaded."));
    });
  }

  function render(wrapper) {
    const page = frappe.ui.make_app_page({
      parent: wrapper,
      title: "Sales Console Report",
      single_column: true,
    });
    const viewState = {
      page,
      $host: ensureHost(page, wrapper),
      routeSignature: "",
      reportKey: "",
      filterOverrides: null,
    };
    wrapper.__erpwSalesConsoleReport = viewState;
    loadRoute(viewState);
  }

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) { render(wrapper); };
  frappe.pages[PAGE_KEY].on_page_show = function (wrapper) {
    if (wrapper && wrapper.__erpwSalesConsoleReport) loadRoute(wrapper.__erpwSalesConsoleReport);
  };
})();
