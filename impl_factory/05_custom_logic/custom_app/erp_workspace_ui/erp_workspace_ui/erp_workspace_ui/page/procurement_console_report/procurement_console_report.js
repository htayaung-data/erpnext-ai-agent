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
  const REPORT_INDEX_KEY = "procurement_reports_index";
  const REPORT_CHROME_TITLE = "Procurement Report";
  const REPORT_CHROME_LABELS = {
    procurement_reports_index: "Procurement Reports",
    supplier_quotation_comparison: "Quote Comparison",
  };
  const REPORT_SHELL_URL = "/assets/erp_workspace_ui/js/runtime/report_page/report_page_shell.js?v=2026-05-02-report-link-suggest-v1";
  const REPORT_SHELL_VERSION = "2026-05-02-report-link-suggest-v1";

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

  function ensureProcurementReportCatalogStyle() {
    if (document.getElementById("erpw-procurement-report-catalog-style")) return;
    const style = document.createElement("style");
    style.id = "erpw-procurement-report-catalog-style";
    style.textContent = [
      '.erpw-procurement-report-catalog { display:grid; gap:16px; }',
      '.erpw-procurement-report-catalog .erpw-report-section-head { max-width:760px; }',
      '.erpw-procurement-report-catalog-grid { display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:14px; align-items:stretch; }',
      '.erpw-procurement-report-card { min-height:188px; padding:16px; border-radius:16px; border:1px solid #dbe6f2; background:linear-gradient(180deg,#ffffff 0%,#f8fbff 100%); display:flex; flex-direction:column; gap:10px; text-align:left; color:#0f172a; box-shadow:0 10px 24px rgba(15,23,42,0.045); transition:border-color 140ms ease, box-shadow 140ms ease, transform 140ms ease; }',
      '.erpw-procurement-report-card.is-ready { cursor:pointer; border-color:#b8cbe2; }',
      '.erpw-procurement-report-card.is-ready:hover { border-color:#8fb0d3; box-shadow:0 14px 30px rgba(15,23,42,0.075); transform:translateY(-1px); }',
      '.erpw-procurement-report-card.is-planned { cursor:not-allowed; opacity:0.74; background:#f8fafc; }',
      '.erpw-procurement-report-card-top { display:flex; align-items:center; justify-content:space-between; gap:10px; }',
      '.erpw-procurement-report-card-category { font-size:10.5px; font-weight:750; letter-spacing:0.08em; text-transform:uppercase; color:#64748b; }',
      '.erpw-procurement-report-card-status { display:inline-flex; align-items:center; justify-content:center; min-height:22px; padding:0 9px; border-radius:999px; border:1px solid #d8e3ef; background:#f8fbff; color:#475569; font-size:10.5px; font-weight:750; letter-spacing:0.06em; text-transform:uppercase; white-space:nowrap; }',
      '.erpw-procurement-report-card.is-ready .erpw-procurement-report-card-status { border-color:#9fc4d8; background:#eef9fb; color:#0f5f6d; }',
      '.erpw-procurement-report-card-title { font-size:16px; line-height:1.25; font-weight:760; color:#0f172a; }',
      '.erpw-procurement-report-card-purpose { font-size:12.5px; line-height:1.48; color:#475569; }',
      '.erpw-procurement-report-card-boundary { margin-top:auto; padding-top:10px; border-top:1px solid rgba(219,230,242,0.82); font-size:11.5px; line-height:1.45; color:#64748b; }',
      '.erpw-procurement-report-card-action { margin-top:2px; font-size:12px; font-weight:750; color:#12365f; }',
      '@media (max-width:1180px) { .erpw-procurement-report-catalog-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }',
      '@media (max-width:720px) { .erpw-procurement-report-catalog-grid { grid-template-columns:1fr; } .erpw-procurement-report-card { min-height:0; } }',
    ].join("\n");
    document.head.appendChild(style);
  }

  function routeToWorklist(queueKey, filters) {
    frappe.route_options = filters && Object.keys(filters).length ? filters : {};
    frappe.set_route(WORKLIST_ROUTE, String(queueKey || "").replace(/_/g, "-"));
  }

  function routeToReport(reportName, filters) {
    frappe.route_options = filters && Object.keys(filters).length ? filters : {};
    frappe.set_route("query-report", reportName);
  }

  function routeToReportPage(reportKey, filters) {
    frappe.route_options = filters && Object.keys(filters).length ? filters : {};
    const slug = String(reportKey || "").replace(/_/g, "-");
    if (slug && slug !== REPORT_INDEX_KEY.replace(/_/g, "-")) {
      return frappe.set_route(PAGE_KEY, slug);
    }
    return frappe.set_route(PAGE_KEY);
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

  function executeTarget(target) {
    if (!target) return;
    if (target.kind === "form" && target.doctype && target.name) {
      rememberNativeChromeTarget(target);
      cleanupForNativeRoute();
      return frappe.set_route("Form", target.doctype, target.name);
    }
    if (target.kind === "worklist" && target.queue_key) return routeToWorklist(target.queue_key, target.filters || null);
    if (target.kind === "report" && target.report_name) return routeToReport(target.report_name, target.filters || null);
    if (target.kind === "report_page") return routeToReportPage(target.report_key || REPORT_INDEX_KEY, target.filters || null);
    if (target.kind === "page" && target.route) {
      frappe.route_options = target.options || {};
      const parts = [target.route].concat(Array.isArray(target.route_parts) ? target.route_parts : []);
      return frappe.set_route.apply(frappe, parts);
    }
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

  function isCurrentReportRoute(routeSignature) {
    const pathSignature = pathRouteSignature();
    if (pathSignature === routeSignature) return true;
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) && String(route[0] || "") === PAGE_KEY && route.join("|") === routeSignature;
  }

  function resolveReportKey(route) {
    return Array.isArray(route) && route.length > 1 ? String(route[1] || "").replace(/-/g, "_") : REPORT_INDEX_KEY;
  }

  function loadingConfig(reportKey) {
    const labelMap = {
      procurement_reports_index: "Procurement Reports",
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

  function isAttached($node) {
    const node = $node && $node.get ? $node.get(0) : null;
    return Boolean(node && document.documentElement.contains(node));
  }

  function syncReportChromeTitle(viewState, payload) {
    if (!viewState || !viewState.page) return;
    ensureProcurementChromeStyle();
    const payloadTitle = payload && payload.page && payload.page.title ? payload.page.title : "";
    const reportKey = viewState.reportKey || payload && payload.page && payload.page.key || "";
    const chromeTitle = REPORT_CHROME_LABELS[reportKey] || payloadTitle || REPORT_CHROME_TITLE;
    if (typeof viewState.page.set_title === "function") {
      viewState.page.set_title(chromeTitle);
    }
    const $wrapper = viewState.page.wrapper ? $(viewState.page.wrapper) : $();
    cleanupDuplicateReportChrome($wrapper, chromeTitle);
    $wrapper.find(".page-title .title-text, .title-area .title-text").first().text(chromeTitle);
    const $breadcrumbs = $wrapper.find(".navbar-breadcrumbs").first();
    if ($breadcrumbs.length) {
      $breadcrumbs.html([
        '<li><a href="/desk/' + HOME_ROUTE + '" data-erpw-procurement-home="1">Procurement Console</a></li>',
        '<li><a class="title-text" aria-current="page">' + frappe.utils.escape_html(chromeTitle) + '</a></li>',
      ].join(""));
    }
    $wrapper.off("click.erpWProcurementReportChrome").on("click.erpWProcurementReportChrome", "[data-erpw-procurement-home]", function (event) {
      event.preventDefault();
      frappe.set_route(HOME_ROUTE);
    });
    cleanupDuplicateReportChrome($wrapper, chromeTitle);
    setTimeout(() => cleanupDuplicateReportChrome($wrapper, chromeTitle), 0);
    setTimeout(() => cleanupDuplicateReportChrome($wrapper, chromeTitle), 120);
  }

  function cleanupDuplicateReportChrome($wrapper, title) {
    const wrapper = $wrapper && $wrapper.jquery ? $wrapper : $($wrapper || []);
    const heads = wrapper.find(".page-head").toArray();
    if (!heads.length) return null;
    const expectedTitle = String(title || "").replace(/\s+/g, " ").trim();
    const keep = heads.find((head) => {
      const text = String((head && head.textContent) || "").replace(/\s+/g, " ").trim();
      return expectedTitle && text.indexOf(expectedTitle) !== -1;
    }) || heads.find((head) => {
      const text = String((head && head.textContent) || "").replace(/\s+/g, " ").trim();
      return !/Procurement Console Report/i.test(text);
    }) || heads[0];
    heads.forEach((head) => {
      if (head !== keep && head.parentNode) head.parentNode.removeChild(head);
    });
    const $keep = $(keep);
    $keep.attr("data-erpw-procurement-managed-chrome", "1");
    $keep.find(".page-icon, .indicator-pill, .title-area > .icon, .title-area > svg").remove();
    return $keep;
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


  function escapeHtml(value) {
    return frappe.utils.escape_html(String(value == null ? "" : value));
  }

  function renderCatalogCard(entry) {
    const card = entry && entry.card ? entry.card : {};
    const section = entry && entry.section ? entry.section : {};
    const status = String(card.status || "planned").toLowerCase();
    const isReady = status === "ready" && card.action_key;
    const attrs = isReady
      ? ' data-erpw-report-action-key="' + escapeHtml(card.action_key) + '"'
      : ' disabled aria-disabled="true"';
    const statusLabel = card.status_label ? card.status_label : (isReady ? "Ready" : "Planned");
    return [
      '<button type="button" class="erpw-procurement-report-card ', isReady ? 'is-ready' : 'is-planned', '"', attrs, ' data-erpw-procurement-report-card="', escapeHtml(card.key || ''), '">',
        '<div class="erpw-procurement-report-card-top">',
          '<div class="erpw-procurement-report-card-category">' + escapeHtml(section.title || '') + '</div>',
          '<div class="erpw-procurement-report-card-status">' + escapeHtml(statusLabel) + '</div>',
        '</div>',
        '<div class="erpw-procurement-report-card-title">' + escapeHtml(card.title || '') + '</div>',
        '<div class="erpw-procurement-report-card-purpose">' + escapeHtml(card.purpose || '') + '</div>',
        card.boundary ? '<div class="erpw-procurement-report-card-boundary">' + escapeHtml(card.boundary) + '</div>' : '',
        isReady ? '<div class="erpw-procurement-report-card-action">Open report</div>' : '',
      '</button>'
    ].join("");
  }

  function renderReportCatalog(catalog) {
    ensureProcurementReportCatalogStyle();
    const sections = Array.isArray(catalog && catalog.sections) ? catalog.sections : [];
    const entries = [];
    sections.forEach((section) => {
      const cards = Array.isArray(section && section.cards) ? section.cards : [];
      cards.forEach((card) => entries.push({ section, card }));
    });
    if (!entries.length) return '';
    return [
      '<section class="erpw-report-card erpw-report-secondary erpw-procurement-report-catalog">',
        '<div class="erpw-report-section-head">',
          '<div class="erpw-report-section-title">Approved report surfaces</div>',
          '<div class="erpw-report-section-subtitle">Use ready reports for buyer review. Planned reports remain visible as roadmap markers but are not active yet.</div>',
        '</div>',
        '<div class="erpw-procurement-report-catalog-grid">',
          entries.map(renderCatalogCard).join(''),
        '</div>',
      '</section>'
    ].join('');
  }

  function mountReportIndex(viewState, runtime, config, payload) {
    const indexConfig = Object.assign({}, config, { metrics: [], secondary: null, results: null });
    runtime.mountReport(viewState.$host, indexConfig);
    const $shell = viewState.$host.children('.erpw-report-shell').first();
    $shell.append(renderReportCatalog(payload && payload.catalog));
    if (typeof runtime.setDataRefreshing === "function") {
      runtime.setDataRefreshing(viewState.$host, false);
    }
  }

  function mountPayload(viewState, payload, options) {
    if (viewState && viewState.routeSignature && !isCurrentReportRoute(viewState.routeSignature)) return;
    syncReportChromeTitle(viewState, payload);
    return ensureReportRuntime().then((runtime) => {
      const config = Object.assign({}, payload || {}, {
        workspace: "procurement",
        page: Object.assign({ workspace: "procurement" }, payload && payload.page ? payload.page : {}),
        reportKey: viewState.reportKey || "",
        onAction(details) {
          if (!details) return;
          if (details.key === "refresh") return loadRoute(viewState, { partialDataRefresh: true });
          if (details.key === "back_to_console") return frappe.set_route(HOME_ROUTE);
          if (details.key === "back_to_reports") return frappe.set_route(PAGE_KEY);
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

      if (payload && payload.catalog) {
        mountReportIndex(viewState, runtime, config, payload);
        return;
      }
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
      if (viewState.routeSignature !== routeSignature || viewState.requestToken !== requestToken || !isCurrentReportRoute(routeSignature)) return;
      const payload = response && response.message ? response.message : {};
      syncReportChromeTitle(viewState, payload);
      mountPayload(viewState, payload, { partialDataRefresh, refreshControls: Boolean(settings.refreshControls) });
    }).catch((error) => {
      if (viewState.routeSignature !== routeSignature || viewState.requestToken !== requestToken || !isCurrentReportRoute(routeSignature)) return;
      setDataRefreshing(viewState, false);
      mountPayload(viewState, errorConfig(error && error.message ? error.message : "The report could not be loaded."));
    });
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
    cleanupDuplicateReportChrome($(wrapper), REPORT_CHROME_TITLE);
    const page = frappe.ui.make_app_page({
      parent: wrapper,
      title: "Procurement Console",
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
    pruneRouteShells(viewState.$host.get(0));
    loadRoute(viewState);
  }

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) { render(wrapper); };
  frappe.pages[PAGE_KEY].on_page_show = function (wrapper) {
    const existing = wrapper && wrapper.__erpwProcurementConsoleReport;
    if (existing && isAttached(existing.$host)) {
      pruneRouteShells(existing.$host.get(0));
      syncReportChromeTitle(existing);
      cleanupDuplicateReportChrome($(wrapper), REPORT_CHROME_TITLE);
      loadRoute(existing);
      return;
    }
    render(wrapper);
  };
})();
