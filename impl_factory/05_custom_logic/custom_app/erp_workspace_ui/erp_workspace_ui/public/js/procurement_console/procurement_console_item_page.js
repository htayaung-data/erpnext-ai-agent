/* global frappe, $ */

(function () {
  const workspaceRegistry = window.erpWorkspaceUiWorkspaceRegistry || {};
  const procurementWorkspace = typeof workspaceRegistry.procurement === "function" ? workspaceRegistry.procurement() : null;
  const procurementRoutes = procurementWorkspace && procurementWorkspace.routes ? procurementWorkspace.routes : {};
  const procurementMethods = procurementWorkspace && procurementWorkspace.methods ? procurementWorkspace.methods : {};
  const PAGE_KEY = procurementRoutes.itemDetail || "procurement-console-item";
  const WORKLIST_ROUTE = procurementRoutes.worklist || "procurement-console-worklist";
  const CONTEXT_METHOD = procurementMethods.itemDetailContext || "erp_workspace_ui.procurement_console.items.get_item_detail_context";
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

  function resolveItem(route) {
    return Array.isArray(route) && route.length > 1 ? String(route[1] || "") : "";
  }

  function routeToWorklist(queueKey) {
    frappe.set_route(WORKLIST_ROUTE, String(queueKey || "buying_item_directory").replace(/_/g, "-"));
  }

  function ensureHost(page, wrapper) {
    const $parent = page && page.body ? $(page.body) : $(wrapper);
    let $host = $parent.children(".erpw-procurement-item-detail-page").first();
    if (!$host.length) {
      $host = $('<section class="erpw-procurement-item-detail-page"></section>');
      $parent.empty().append($host);
    }
    let $shell = $host.children(".erpw-child-shell.erpw-procurement-item-detail-shell").first();
    if (!$shell.length) {
      $shell = $('<div class="erpw-child-shell erpw-procurement-item-detail-shell"></div>');
      $host.append($shell);
    }
    return { $host, $shell };
  }

  function makeFallbackPage(wrapper) {
    const $parent = $(wrapper);
    $parent.empty().append(`
      <div class="erpw-direct-child-page">
        <div class="erpw-direct-child-titlebar">
          <div class="erpw-direct-child-title">Buying Item Detail</div>
        </div>
        <main class="layout-main-section erpw-direct-child-body"></main>
      </div>
    `);
    const $body = $parent.find(".erpw-direct-child-body").first();
    return {
      body: $body,
      set_title(title) {
        const nextTitle = title || "Buying Item Detail";
        $parent.find(".erpw-direct-child-title").first().text(nextTitle);
        document.title = nextTitle;
      },
    };
  }

  function makeDetailPage(wrapper) {
    try {
      return frappe.ui.make_app_page({ parent: wrapper, title: "Buying Item Detail", single_column: true });
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
            <div class="erpw-list-state-title">${escapeHtml(state.title || "Buying item unavailable")}</div>
            <div class="erpw-list-state-detail">${escapeHtml(state.detail || "This buying item page is not available.")}</div>
          </div>
        </section>
      `;
    }
    return `
      ${renderSection("Approved suppliers", "Supplier relationships configured on the item master.", detail.item_suppliers)}
      ${renderSection("Supplier price review", "Read-only buying Item Price context. No price updates are exposed.", detail.item_prices)}
      ${renderSection("Recent supplier quotations", "Recent quotation context linked to this item.", detail.supplier_quotations)}
      ${renderSection("Open purchase orders", "Purchase order posture for buyer follow-up. Warehouse and Finance retain downstream ownership.", detail.purchase_orders)}
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
            <div class="erpw-list-state-title">Buying item detail could not be loaded</div>
            <div class="erpw-list-state-detail">${escapeHtml(error && error.message ? error.message : "The shared detail runtime could not be loaded.")}</div>
          </div>
        </section>
      `);
    });
  }

  function loadingPayload(itemCode) {
    return {
      page: { title: "Buying Item Detail" },
      summary: {
        kicker: "Procurement item",
        title: itemCode || "Buying Item Detail",
        subtitle: "Loading read-only item buying context.",
        chips: [{ label: "Loading", tone: "pending" }],
        facts: [],
      },
      controls: { actions: [] },
      detail: {
        state: { kind: "loading", title: "Loading item", detail: "Reading item buying context." },
      },
    };
  }

  function loadRoute(viewState) {
    const route = frappe.get_route ? frappe.get_route() : [];
    const itemCode = resolveItem(route);
    const routeSignature = Array.isArray(route) ? route.join("|") : "";
    viewState.routeSignature = routeSignature;
    mountPayload(viewState, loadingPayload(itemCode));
    frappe.call({
      method: CONTEXT_METHOD,
      args: { item: itemCode },
    }).then((response) => {
      if (viewState.routeSignature !== routeSignature) return;
      mountPayload(viewState, response && response.message ? response.message : {});
    }).catch((error) => {
      if (viewState.routeSignature !== routeSignature) return;
      mountPayload(viewState, {
        page: { title: "Buying Item Detail" },
        summary: {
          kicker: "Procurement item",
          title: "Buying item unavailable",
          subtitle: error && error.message ? error.message : "The item page could not be loaded.",
          chips: [{ label: "error", tone: "blocker" }],
          facts: [],
        },
        detail: {
          state: { kind: "error", title: "Buying item failed", detail: error && error.message ? error.message : "The page could not load." },
        },
      });
    });
  }

  function render(wrapper) {
    const page = makeDetailPage(wrapper);
    const hosts = ensureHost(page, wrapper);
    const viewState = { page, $host: hosts.$host, $shell: hosts.$shell };
    wrapper.__erpwProcurementItemDetail = viewState;
    loadRoute(viewState);
  }

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) { render(wrapper); };
  frappe.pages[PAGE_KEY].on_page_show = function (wrapper) {
    if (window.erpWorkspaceConsoleSidebar && typeof window.erpWorkspaceConsoleSidebar.refresh === "function") {
      window.erpWorkspaceConsoleSidebar.refresh();
    }
    const existing = wrapper && wrapper.__erpwProcurementItemDetail;
    if (existing) {
      loadRoute(existing);
      return;
    }
    render(wrapper);
  };
})();
