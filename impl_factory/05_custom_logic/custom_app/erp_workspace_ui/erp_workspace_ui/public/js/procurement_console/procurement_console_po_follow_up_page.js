/* global frappe, $ */

(function () {
  const workspaceRegistry = window.erpWorkspaceUiWorkspaceRegistry || {};
  const procurementWorkspace = typeof workspaceRegistry.procurement === "function" ? workspaceRegistry.procurement() : null;
  const procurementRoutes = procurementWorkspace && procurementWorkspace.routes ? procurementWorkspace.routes : {};
  const procurementMethods = procurementWorkspace && procurementWorkspace.methods ? procurementWorkspace.methods : {};
  const PAGE_KEY = procurementRoutes.poFollowUp || "procurement-console-po-follow-up";
  const WORKLIST_ROUTE = procurementRoutes.worklist || "procurement-console-worklist";
  const CONTEXT_METHOD = procurementMethods.poFollowUpDetailContext || "erp_workspace_ui.procurement_console.purchase_order_detail.get_purchase_order_follow_up_detail_context";
  const CHILD_PAGE_RUNTIME_URLS = [
    "/assets/erp_workspace_ui/js/runtime/child_page/child_page_helpers.js?v=procurement-po-follow-up-v1",
    "/assets/erp_workspace_ui/js/runtime/child_page/child_page_shell_content.js?v=procurement-po-follow-up-v1",
  ];
  let activeViewState = null;
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

  function routeToWorklist(queueKey) {
    frappe.set_route(WORKLIST_ROUTE, String(queueKey || "purchase_orders_supplier_follow_up").replace(/_/g, "-"));
  }

  function resolvePurchaseOrder(route) {
    return Array.isArray(route) && route.length > 1 ? String(route[1] || "") : "";
  }

  function consumeRouteOptions() {
    const options = frappe.route_options && typeof frappe.route_options === "object"
      ? Object.assign({}, frappe.route_options)
      : {};
    frappe.route_options = {};
    return options;
  }

  function ensureHost(page, wrapper) {
    const $parent = page && page.body ? $(page.body) : $(wrapper);
    let $host = $parent.children(".erpw-procurement-po-follow-up-page").first();
    if (!$host.length) {
      $host = $('<section class="erpw-procurement-po-follow-up-page"></section>');
      $parent.empty().append($host);
    }
    let $shell = $host.children(".erpw-child-shell.erpw-procurement-po-follow-up-shell").first();
    if (!$shell.length) {
      $shell = $('<div class="erpw-child-shell erpw-procurement-po-follow-up-shell"></div>');
      $host.append($shell);
    }
    return { $host, $shell };
  }

  function makeFallbackPage(wrapper) {
    const $parent = $(wrapper);
    $parent.empty().append(`
      <div class="erpw-direct-child-page">
        <div class="erpw-direct-child-titlebar">
          <div class="erpw-direct-child-title">Purchase Order Follow-up</div>
        </div>
        <main class="layout-main-section erpw-direct-child-body"></main>
      </div>
    `);
    const $body = $parent.find(".erpw-direct-child-body").first();
    return {
      body: $body,
      set_title(title) {
        const nextTitle = title || "Purchase Order Follow-up";
        $parent.find(".erpw-direct-child-title").first().text(nextTitle);
        document.title = nextTitle;
      },
    };
  }

  function makeDetailPage(wrapper) {
    try {
      return frappe.ui.make_app_page({
        parent: wrapper,
        title: "Purchase Order Follow-up",
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
                  return `<td><span class="erpw-list-cell-value">${escapeHtml(value || "-")}</span>${meta ? `<span class="erpw-list-cell-meta">${escapeHtml(meta)}</span>` : ""}</td>`;
                }).join("")}
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;
  }

  function renderDownstreamCard(title, payload) {
    const state = payload && payload.state ? payload.state : {};
    return `
      <article class="erpw-child-guidance-card erpw-child-guidance-card-secondary">
        <div class="erpw-child-guidance-copy">
          <div class="erpw-child-guidance-title">${escapeHtml(title)}</div>
          <div class="erpw-child-guidance-chip ${escapeHtml(state.kind || "neutral")}">${escapeHtml(state.kind || "visibility")}</div>
        </div>
        <div class="erpw-child-guidance-text">${escapeHtml(payload && payload.metric || "--")}</div>
        <div class="erpw-child-section-header-note">${escapeHtml(payload && payload.detail || state.detail || "")}</div>
      </article>
    `;
  }

  function extraSections(payload) {
    const detail = (payload && payload.detail) || {};
    const state = detail.state || {};
    if (state.kind && state.kind !== "ready") {
      return `
        <section class="erpw-child-card erpw-list-results">
          <div class="erpw-list-state ${escapeHtml(state.kind)}">
            <div class="erpw-list-state-title">${escapeHtml(state.title || "Purchase Order follow-up unavailable")}</div>
            <div class="erpw-list-state-detail">${escapeHtml(state.detail || "This read-only follow-up page is not available.")}</div>
          </div>
        </section>
      `;
    }
    const downstream = detail.downstream || {};
    return `
      <section class="erpw-child-card erpw-list-results">
        <div class="erpw-child-section-header">
          <div class="erpw-child-section-header-copy">
            <div class="erpw-child-section-header-title">Item lines</div>
            <div class="erpw-child-section-header-note">Line-level quantity, receipt posture, warehouse, required date, and source references.</div>
          </div>
          <div class="erpw-child-section-header-status">Visibility only</div>
        </div>
        ${renderTable(detail.items || {})}
      </section>
      <section class="erpw-child-card erpw-child-context erpw-child-context-compact">
        <div class="erpw-child-section-heading erpw-child-section-heading-compact">
          <div class="erpw-child-section-title">Downstream visibility</div>
        </div>
        <div class="erpw-child-guidance-grid">
          ${renderDownstreamCard("Receipt posture", downstream.receipts || {})}
          ${renderDownstreamCard("Billing posture", downstream.billing || {})}
        </div>
      </section>
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
        actionLayout: { sparseSecondaryThreshold: 2 },
        extraSectionsHtml: extraSections(payload),
        guidance: {},
      });
    }).catch((error) => {
      if (viewState.routeSignature !== routeSignature) return;
      viewState.$shell.html(`
        <section class="erpw-child-card">
          <div class="erpw-list-state error">
            <div class="erpw-list-state-title">Purchase Order detail could not be loaded</div>
            <div class="erpw-list-state-detail">${escapeHtml(error && error.message ? error.message : "The shared detail runtime could not be loaded.")}</div>
          </div>
        </section>
      `);
    });
  }

  function loadingPayload(poName) {
    return {
      page: { title: "Purchase Order Follow-up" },
      summary: {
        kicker: "Procurement Console",
        title: poName || "Purchase Order Follow-up",
        subtitle: "Loading read-only purchase order follow-up context.",
        chips: [{ label: "Loading", tone: "pending" }],
        facts: [],
      },
      controls: { actions: [] },
      detail: {
        state: { kind: "loading", title: "Loading follow-up", detail: "Reading purchase order context." },
      },
    };
  }

  function loadRoute(viewState) {
    const route = frappe.get_route ? frappe.get_route() : [];
    const poName = resolvePurchaseOrder(route);
    const routeSignature = Array.isArray(route) ? route.join("|") : "";
    viewState.routeSignature = routeSignature;
    if (!viewState.routeOptionsConsumed) {
      viewState.routeOptions = consumeRouteOptions();
      viewState.routeOptionsConsumed = true;
    }
    mountPayload(viewState, loadingPayload(poName));
    frappe.call({
      method: CONTEXT_METHOD,
      args: {
        purchase_order: poName,
        return_queue: (viewState.routeOptions && viewState.routeOptions.return_queue) || "",
      },
    }).then((response) => {
      if (viewState.routeSignature !== routeSignature) return;
      mountPayload(viewState, response && response.message ? response.message : {});
    }).catch((error) => {
      if (viewState.routeSignature !== routeSignature) return;
      mountPayload(viewState, {
        page: { title: "Purchase Order Follow-up" },
        summary: {
          kicker: "Procurement Console",
          title: "Purchase Order follow-up unavailable",
          subtitle: error && error.message ? error.message : "The read-only follow-up page could not be loaded.",
          chips: [{ label: "error", tone: "blocker" }],
          facts: [],
        },
        detail: {
          state: { kind: "error", title: "Follow-up failed", detail: error && error.message ? error.message : "The page could not load." },
        },
      });
    });
  }

  function render(wrapper) {
    const page = makeDetailPage(wrapper);
    const hosts = ensureHost(page, wrapper);
    const viewState = {
      page,
      $host: hosts.$host,
      $shell: hosts.$shell,
      routeOptions: {},
      routeOptionsConsumed: false,
    };
    wrapper.__erpwProcurementPoFollowUp = viewState;
    activeViewState = viewState;
    loadRoute(viewState);
  }

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) { render(wrapper); };
  frappe.pages[PAGE_KEY].on_page_show = function (wrapper) {
    if (window.erpWorkspaceConsoleSidebar && typeof window.erpWorkspaceConsoleSidebar.refresh === "function") {
      window.erpWorkspaceConsoleSidebar.refresh();
    }
    const existing = wrapper && wrapper.__erpwProcurementPoFollowUp;
    if (existing) {
      activeViewState = existing;
      existing.routeOptionsConsumed = false;
      loadRoute(existing);
      return;
    }
    render(wrapper);
  };
})();
