/* global frappe, $ */

(function () {
  const workspaceRegistry = window.erpWorkspaceUiWorkspaceRegistry || {};
  const procurementWorkspace = typeof workspaceRegistry.procurement === "function" ? workspaceRegistry.procurement() : null;
  const procurementRoutes = procurementWorkspace && procurementWorkspace.routes ? procurementWorkspace.routes : {};
  const procurementMethods = procurementWorkspace && procurementWorkspace.methods ? procurementWorkspace.methods : {};
  const WORKLIST_ROUTE = procurementRoutes.worklist || "procurement-console-worklist";
  const REPORT_ROUTE = procurementRoutes.report || "procurement-console-report";
  const PAGE_DEFINITIONS = {
    [procurementRoutes.purchaseRequestReview || "procurement-console-purchase-request-review"]: {
      title: "Purchase Request Review",
      defaultQueue: "purchase_request_directory",
      argName: "material_request",
      stateTitle: "Purchase request review unavailable",
      loadingTitle: "Loading purchase request",
      loadingDetail: "Reading purchase demand context.",
      contextMethod: procurementMethods.purchaseRequestReviewContext || "erp_workspace_ui.procurement_console.document_reviews.get_purchase_request_review_context",
      hostClass: "erpw-procurement-purchase-request-review-page",
      shellClass: "erpw-procurement-purchase-request-review-shell",
    },
    [procurementRoutes.rfqReview || "procurement-console-rfq-review"]: {
      title: "RFQ Review",
      defaultQueue: "rfq_directory",
      argName: "request_for_quotation",
      stateTitle: "RFQ review unavailable",
      loadingTitle: "Loading RFQ",
      loadingDetail: "Reading sourcing response context.",
      contextMethod: procurementMethods.rfqReviewContext || "erp_workspace_ui.procurement_console.document_reviews.get_rfq_review_context",
      hostClass: "erpw-procurement-rfq-review-page",
      shellClass: "erpw-procurement-rfq-review-shell",
    },
    [procurementRoutes.supplierQuotationReview || "procurement-console-supplier-quotation-review"]: {
      title: "Supplier Quotation Review",
      defaultQueue: "supplier_quotation_directory",
      argName: "supplier_quotation",
      stateTitle: "Supplier quotation review unavailable",
      loadingTitle: "Loading supplier quotation",
      loadingDetail: "Reading supplier offer context.",
      contextMethod: procurementMethods.supplierQuotationReviewContext || "erp_workspace_ui.procurement_console.document_reviews.get_supplier_quotation_review_context",
      hostClass: "erpw-procurement-supplier-quotation-review-page",
      shellClass: "erpw-procurement-supplier-quotation-review-shell",
    },
  };
  const CHILD_PAGE_RUNTIME_URLS = [
    "/assets/erp_workspace_ui/js/runtime/child_page/child_page_helpers.js",
    "/assets/erp_workspace_ui/js/runtime/child_page/child_page_shell_content.js",
  ];
  let runtimePromise = null;

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
      frappe.require(url, () => resolve());
    });
  }

  function ensureDetailRuntime() {
    if (hasShellRuntime()) return Promise.resolve(shellContent());
    if (runtimePromise) return runtimePromise;
    runtimePromise = CHILD_PAGE_RUNTIME_URLS.reduce(
      (promise, url) => promise.then(() => (hasShellRuntime() ? null : requireRuntimeAsset(url))),
      Promise.resolve()
    ).then(() => {
      if (!hasShellRuntime()) throw new Error("Shared child-page detail runtime is unavailable.");
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

  function resolveName(route) {
    return Array.isArray(route) && route.length > 1 ? String(route[1] || "") : "";
  }

  function routeToWorklist(queueKey, filters) {
    frappe.route_options = filters && Object.keys(filters).length ? filters : {};
    frappe.set_route(WORKLIST_ROUTE, String(queueKey || "").replace(/_/g, "-"));
  }

  function routeToReportPage(reportKey, filters) {
    frappe.route_options = filters && Object.keys(filters).length ? filters : {};
    frappe.set_route(REPORT_ROUTE, String(reportKey || "").replace(/_/g, "-"));
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
    $(wrapper).find(".page-head").remove();
  }

  function ensureHost(page, wrapper, definition) {
    const $parent = page && page.body ? $(page.body) : $(wrapper);
    let $host = $parent.children(`.${definition.hostClass}`).first();
    if (!$host.length) {
      $host = $(`<section class="erpw-procurement-review-page ${definition.hostClass}"></section>`);
      $parent.empty().append($host);
    }
    let $shell = $host.children(`.erpw-child-shell.erpw-child-detail-shell.${definition.shellClass}`).first();
    if (!$shell.length) {
      $shell = $(`<div class="erpw-child-shell erpw-child-detail-shell erpw-procurement-review-shell ${definition.shellClass}"></div>`);
      $host.append($shell);
    }
    return { $host, $shell };
  }

  function isAttached($node) {
    const node = $node && $node.get ? $node.get(0) : null;
    return Boolean(node && document.documentElement.contains(node));
  }

  function makeFallbackPage(wrapper, definition) {
    const $parent = $(wrapper);
    $parent.empty().append(`
      <div class="erpw-direct-child-page">
        <div class="erpw-direct-child-titlebar">
          <div class="erpw-direct-child-title">${escapeHtml(definition.title)}</div>
        </div>
        <main class="layout-main-section erpw-direct-child-body"></main>
      </div>
    `);
    const $body = $parent.find(".erpw-direct-child-body").first();
    return {
      body: $body,
      set_title(title) {
        const nextTitle = title || definition.title;
        $parent.find(".erpw-direct-child-title").first().text(nextTitle);
        document.title = nextTitle;
      },
    };
  }

  function makeDetailPage(wrapper, definition) {
    try {
      return frappe.ui.make_app_page({ parent: wrapper, title: definition.title, single_column: true });
    } catch (error) {
      return makeFallbackPage(wrapper, definition);
    }
  }

  function normalizeActions(payload, viewState) {
    const actions = payload && payload.controls && Array.isArray(payload.controls.actions) ? payload.controls.actions : [];
    return actions.map((action) => Object.assign({}, action, {
      title: action.title || action.label || action.key,
      handler() {
        if (action.key === "refresh") return loadRoute(viewState);
        const target = ((payload && payload.action_targets) || {})[action.key];
        if (target && target.kind === "worklist" && target.queue_key) return routeToWorklist(target.queue_key, target.filters || null);
        if (target && target.kind === "report_page" && target.report_key) return routeToReportPage(target.report_key, target.filters || null);
        if (target && target.kind === "form" && target.doctype && target.name) {
          rememberNativeChromeTarget(target);
          cleanupForNativeRoute();
          return frappe.set_route("Form", target.doctype, target.name);
        }
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
          <thead><tr>${columns.map((column) => `<th>${escapeHtml(column.label || column.key)}</th>`).join("")}</tr></thead>
          <tbody>
            ${rows.map((row) => `
              <tr>
                ${columns.map((column) => {
                  const cell = row.cells && row.cells[column.key] !== undefined ? row.cells[column.key] : "";
                  const value = cell && typeof cell === "object" ? cell.value : cell;
                  const meta = cell && typeof cell === "object" ? cell.meta : "";
                  return `<td><span class="erpw-list-cell-value">${escapeHtml(value || "-")}</span>${meta ? `<span class="erpw-list-cell-meta">${escapeHtml(meta)}</span>` : ""}</td>`;
                }).join("")}
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;
  }

  function renderSection(section) {
    return `
      <section class="erpw-child-card erpw-list-results">
        <div class="erpw-child-section-header">
          <div class="erpw-child-section-header-copy">
            <div class="erpw-child-section-header-title">${escapeHtml(section.title || "Review section")}</div>
            <div class="erpw-child-section-header-note">${escapeHtml(section.note || "Read-only procurement review context.")}</div>
          </div>
          <div class="erpw-child-section-header-status">${escapeHtml(section.status || "Read-only")}</div>
        </div>
        ${renderTable(section.table || {})}
      </section>
    `;
  }

  function extraSections(payload, definition) {
    const detail = (payload && payload.detail) || {};
    const state = detail.state || {};
    if (state.kind && state.kind !== "ready") {
      return `
        <section class="erpw-child-card erpw-list-results">
          <div class="erpw-list-state ${escapeHtml(state.kind)}">
            <div class="erpw-list-state-title">${escapeHtml(state.title || definition.stateTitle)}</div>
            <div class="erpw-list-state-detail">${escapeHtml(state.detail || "This Procurement review page is not available.")}</div>
          </div>
        </section>
      `;
    }
    const sections = Array.isArray(detail.sections) ? detail.sections : [];
    return sections.map(renderSection).join("");
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
        extraSectionsHtml: extraSections(payload, viewState.definition),
        guidance: {},
      });
    }).catch((error) => {
      if (viewState.routeSignature !== routeSignature) return;
      viewState.$shell.html(`
        <section class="erpw-child-card">
          <div class="erpw-list-state error">
            <div class="erpw-list-state-title">${escapeHtml(viewState.definition.title)} could not be loaded</div>
            <div class="erpw-list-state-detail">${escapeHtml(error && error.message ? error.message : "The shared detail runtime could not be loaded.")}</div>
          </div>
        </section>
      `);
    });
  }

  function loadingPayload(name, definition) {
    return {
      page: { title: definition.title },
      summary: {
        kicker: "Procurement review",
        title: name || definition.title,
        subtitle: definition.loadingDetail,
        chips: [{ label: "Loading", tone: "pending" }],
        facts: [],
      },
      controls: { actions: [] },
      detail: { state: { kind: "loading", title: definition.loadingTitle, detail: definition.loadingDetail } },
    };
  }

  function loadRoute(viewState) {
    const route = frappe.get_route ? frappe.get_route() : [];
    const name = resolveName(route);
    const routeSignature = Array.isArray(route) ? route.join("|") : "";
    const routeOptions = frappe.route_options && typeof frappe.route_options === "object" ? Object.assign({}, frappe.route_options) : {};
    frappe.route_options = {};
    viewState.routeSignature = routeSignature;
    mountPayload(viewState, loadingPayload(name, viewState.definition));
    const args = { name, return_queue: routeOptions.return_queue || viewState.definition.defaultQueue };
    args[viewState.definition.argName] = name;
    frappe.call({ method: viewState.definition.contextMethod, args }).then((response) => {
      if (viewState.routeSignature !== routeSignature) return;
      mountPayload(viewState, response && response.message ? response.message : {});
    }).catch((error) => {
      if (viewState.routeSignature !== routeSignature) return;
      mountPayload(viewState, {
        page: { title: viewState.definition.title },
        summary: {
          kicker: "Procurement review",
          title: viewState.definition.stateTitle,
          subtitle: error && error.message ? error.message : "The review page could not be loaded.",
          chips: [{ label: "error", tone: "blocker" }],
          facts: [],
        },
        detail: { state: { kind: "error", title: viewState.definition.stateTitle, detail: error && error.message ? error.message : "The page could not load." } },
      });
    });
  }

  function cleanupRouteShells(pageKey) {
    if (window.erpWorkspaceUiBoot && typeof window.erpWorkspaceUiBoot.cleanupProcurementRouteShells === "function") {
      window.erpWorkspaceUiBoot.cleanupProcurementRouteShells(pageKey, { removeActive: true });
    }
  }

  function pruneRouteShells(pageKey, keepNode) {
    if (window.erpWorkspaceUiBoot && typeof window.erpWorkspaceUiBoot.pruneProcurementRouteShells === "function") {
      window.erpWorkspaceUiBoot.pruneProcurementRouteShells(pageKey, keepNode);
      setTimeout(() => window.erpWorkspaceUiBoot.pruneProcurementRouteShells(pageKey, keepNode), 0);
      setTimeout(() => window.erpWorkspaceUiBoot.pruneProcurementRouteShells(pageKey, keepNode), 80);
    }
  }

  function render(wrapper, pageKey) {
    const definition = PAGE_DEFINITIONS[pageKey];
    cleanupRouteShells(pageKey);
    const page = makeDetailPage(wrapper, definition);
    cleanupManagedPageChrome(wrapper);
    const hosts = ensureHost(page, wrapper, definition);
    const viewState = { page, definition, $host: hosts.$host, $shell: hosts.$shell };
    wrapper.__erpwProcurementReviewDetail = viewState;
    pruneRouteShells(pageKey, hosts.$host.get(0));
    loadRoute(viewState);
  }

  function show(wrapper, pageKey) {
    if (window.erpWorkspaceConsoleSidebar && typeof window.erpWorkspaceConsoleSidebar.refresh === "function") {
      window.erpWorkspaceConsoleSidebar.refresh();
    }
    const existing = wrapper && wrapper.__erpwProcurementReviewDetail;
    if (existing && existing.definition === PAGE_DEFINITIONS[pageKey] && isAttached(existing.$host) && isAttached(existing.$shell)) {
      cleanupManagedPageChrome(wrapper);
      loadRoute(existing);
      return;
    }
    render(wrapper, pageKey);
  }

  window.erpWorkspaceUiProcurementReviewPage = {
    render,
    show,
  };
})();
