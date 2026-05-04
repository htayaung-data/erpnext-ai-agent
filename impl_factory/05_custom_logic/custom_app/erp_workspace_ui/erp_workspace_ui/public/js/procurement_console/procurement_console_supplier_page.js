/* global frappe, $ */

(function () {
  const workspaceRegistry = window.erpWorkspaceUiWorkspaceRegistry || {};
  const procurementWorkspace = typeof workspaceRegistry.procurement === "function" ? workspaceRegistry.procurement() : null;
  const procurementRoutes = procurementWorkspace && procurementWorkspace.routes ? procurementWorkspace.routes : {};
  const procurementMethods = procurementWorkspace && procurementWorkspace.methods ? procurementWorkspace.methods : {};
  const PAGE_KEY = procurementRoutes.supplierDetail || "procurement-console-supplier";
  const WORKLIST_ROUTE = procurementRoutes.worklist || "procurement-console-worklist";
  const CONTEXT_METHOD = procurementMethods.supplierDetailContext || "erp_workspace_ui.procurement_console.supplier_detail.get_supplier_detail_context";
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

  function resolveSupplier(route) {
    return Array.isArray(route) && route.length > 1 ? String(route[1] || "") : "";
  }

  function routeToWorklist(queueKey) {
    frappe.set_route(WORKLIST_ROUTE, String(queueKey || "supplier_directory").replace(/_/g, "-"));
  }

  function ensureHost(page, wrapper) {
    const $parent = page && page.body ? $(page.body) : $(wrapper);
    let $host = $parent.children(".erpw-procurement-supplier-detail-page").first();
    if (!$host.length) {
      $host = $('<section class="erpw-procurement-supplier-detail-page"></section>');
      $parent.empty().append($host);
    }
    let $shell = $host.children(".erpw-child-shell.erpw-procurement-supplier-detail-shell").first();
    if (!$shell.length) {
      $shell = $('<div class="erpw-child-shell erpw-procurement-supplier-detail-shell"></div>');
      $host.append($shell);
    }
    return { $host, $shell };
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
        if (action.key === "refresh") return loadRoute(viewState);
        const target = ((payload && payload.action_targets) || {})[action.key];
        if (target && target.kind === "worklist" && target.queue_key) return routeToWorklist(target.queue_key);
        if (target && target.kind === "form" && target.doctype && target.name) return frappe.set_route("Form", target.doctype, target.name);
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
                  return `<td><span class="erpw-list-cell-value">${escapeHtml(value || "-")}</span>${meta ? `<span class="erpw-list-cell-meta">${escapeHtml(meta)}</span>` : ""}</td>`;
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
        actionLayout: { sparseSecondaryThreshold: 3 },
        extraSectionsHtml: extraSections(payload),
        guidance: {},
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

  function loadRoute(viewState) {
    const route = frappe.get_route ? frappe.get_route() : [];
    const supplierName = resolveSupplier(route);
    const routeSignature = Array.isArray(route) ? route.join("|") : "";
    viewState.routeSignature = routeSignature;
    mountPayload(viewState, loadingPayload(supplierName));
    frappe.call({
      method: CONTEXT_METHOD,
      args: {
        supplier: supplierName,
      },
    }).then((response) => {
      if (viewState.routeSignature !== routeSignature) return;
      mountPayload(viewState, response && response.message ? response.message : {});
    }).catch((error) => {
      if (viewState.routeSignature !== routeSignature) return;
      mountPayload(viewState, {
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
      });
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
    const page = makeDetailPage(wrapper);
    const hosts = ensureHost(page, wrapper);
    const viewState = {
      page,
      $host: hosts.$host,
      $shell: hosts.$shell,
    };
    wrapper.__erpwProcurementSupplierDetail = viewState;
    loadRoute(viewState);
  }

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) { render(wrapper); };
  frappe.pages[PAGE_KEY].on_page_show = function (wrapper) {
    if (window.erpWorkspaceConsoleSidebar && typeof window.erpWorkspaceConsoleSidebar.refresh === "function") {
      window.erpWorkspaceConsoleSidebar.refresh();
    }
    const existing = wrapper && wrapper.__erpwProcurementSupplierDetail;
    if (existing) {
      loadRoute(existing);
      return;
    }
    render(wrapper);
  };
})();
