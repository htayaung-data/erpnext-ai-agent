/* global frappe, $ */

(function () {
  const workspaceRegistry = window.erpWorkspaceUiWorkspaceRegistry || {};
  const procurementWorkspace = typeof workspaceRegistry.procurement === "function" ? workspaceRegistry.procurement() : null;
  const procurementRoutes = procurementWorkspace && procurementWorkspace.routes ? procurementWorkspace.routes : {};
  const procurementMethods = procurementWorkspace && procurementWorkspace.methods ? procurementWorkspace.methods : {};
  const PAGE_KEY = procurementRoutes.home || "procurement-console";
  const WORKLIST_ROUTE = procurementRoutes.worklist || "procurement-console-worklist";
  const BOOTSTRAP_METHOD = procurementMethods.bootstrap || "erp_workspace_ui.procurement_console.service.get_procurement_console_bootstrap";
  const consoleRuntime = window.erpWorkspaceConsoleRuntime || {};

  function runtimeMethod(name) {
    const method = consoleRuntime[name];
    if (typeof method === "function") return method;
    throw new Error("Procurement Console runtime is missing method: " + name);
  }

  function escapeHtml(value) {
    return runtimeMethod("escapeHtml")(value);
  }

  function routeToWorklist(queueKey, filters) {
    frappe.route_options = filters && Object.keys(filters).length ? filters : null;
    frappe.set_route(WORKLIST_ROUTE, String(queueKey || "").replace(/_/g, "-"));
  }

  function makeInsightCard(config) {
    return runtimeMethod("makeInsightCard")(config);
  }

  function makeQueueItem(config) {
    return runtimeMethod("makeQueueItem")(config);
  }

  function applyMetric($root, key, metric) {
    runtimeMethod("applyQueueMetric")($root, key, metric);
    runtimeMethod("applyInsightMetric")($root, key, metric);
  }

  function renderState(page, state) {
    const payloadState = state || {};
    const $root = $(`
      <div class="sales-console-shell" data-procurement-console-state="${escapeHtml(payloadState.kind || "unavailable")}">
        <section class="sales-console-card sales-console-section">
          <div class="sales-console-section-head">
            <h2 class="sales-console-section-title">${escapeHtml(payloadState.title || "Procurement Console unavailable")}</h2>
            <div class="sales-console-section-note">Workspace state</div>
          </div>
          <div class="sales-console-inquiry-placeholder">${escapeHtml(payloadState.detail || "This workspace is not available right now.")}</div>
        </section>
      </div>
    `);
    $(page.body).empty().append($root);
  }

  function applyPayload($root, payload) {
    const work = (payload && payload.work) || {};
    const directories = (payload && payload.directories) || {};
    const insights = (payload && payload.insights) || {};
    Object.keys(work).forEach((key) => applyMetric($root, key, work[key]));
    Object.keys(directories).forEach((key) => applyMetric($root, key, directories[key]));
    Object.keys(insights).forEach((key) => applyMetric($root, key, insights[key]));
  }

  function renderWorkbench(page) {
    const pageState = { payload: {} };
    const $root = $('<div class="sales-console-shell" data-erpw-console-runtime="ready" data-erpw-console-bootstrap="loading"></div>');

    const $header = $(`
      <section class="sales-console-card sales-console-header">
        <div class="sales-console-header-row">
          <div class="sales-console-header-copy">
            <h1 class="sales-console-title">Procurement Console</h1>
            <div class="sales-console-header-note">Buyer workbench for purchase demand, supplier coordination, and purchase order follow-up.</div>
          </div>
        </div>
        <div class="sales-console-kpi-grid"></div>
      </section>
    `);

    const $kpiGrid = $header.find(".sales-console-kpi-grid");
    $kpiGrid.append(
      makeInsightCard({ key: "requests_to_source", label: "Requests To Source", meta: "Purchase requests needing buying action." })
        .on("click", () => routeToWorklist("requests_to_source")),
      makeInsightCard({ key: "purchase_orders_pending_approval", label: "Pending Approval", meta: "Purchase Orders waiting on purchase approval." })
        .on("click", () => routeToWorklist("purchase_orders_pending_approval")),
      makeInsightCard({ key: "purchase_orders_late_or_unreceived", label: "Late / Unreceived", meta: "Open orders past required date." })
        .on("click", () => routeToWorklist("purchase_orders_late_or_unreceived"))
    );

    const $priority = $(`
      <section class="sales-console-card sales-console-section" data-section-key="work">
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">Priority Work</h2>
          <div class="sales-console-section-note">Buyer queues</div>
        </div>
        <div class="sales-console-queue-grid" data-section-grid="work"></div>
      </section>
    `);
    $priority.find(".sales-console-queue-grid").append(
      makeQueueItem({
        key: "requests_to_source",
        title: "Requests To Source",
        meta: "Submitted purchase requests that are not fully ordered.",
        badgeClass: "attention",
        sideLabel: "Open",
        onClick: () => routeToWorklist("requests_to_source"),
      }),
      makeQueueItem({
        key: "purchase_orders_pending_approval",
        title: "Purchase Orders Pending Approval",
        meta: "Visibility only; approval actions are not enabled in Phase 1.",
        badgeClass: "blocker",
        sideLabel: "Pending",
        onClick: () => routeToWorklist("purchase_orders_pending_approval"),
      }),
      makeQueueItem({
        key: "purchase_orders_late_or_unreceived",
        title: "Late Or Unreceived Purchase Orders",
        meta: "Open orders past required date and not fully received.",
        badgeClass: "attention",
        sideLabel: "Follow Up",
        onClick: () => routeToWorklist("purchase_orders_late_or_unreceived"),
      }),
      makeQueueItem({
        key: "purchase_orders_open",
        title: "Open Purchase Orders",
        meta: "Submitted orders still active for buyer awareness.",
        badgeClass: "review",
        sideLabel: "Open",
        onClick: () => routeToWorklist("purchase_orders_open"),
      })
    );

    const $directories = $(`
      <section class="sales-console-card sales-console-section" data-section-key="directories">
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">Directories</h2>
          <div class="sales-console-section-note">Read and review</div>
        </div>
        <div class="sales-console-queue-grid" data-section-grid="directories"></div>
      </section>
    `);
    $directories.find(".sales-console-queue-grid").append(
      makeQueueItem({
        key: "supplier_directory",
        title: "Suppliers",
        meta: "Read-only supplier directory.",
        badgeClass: "review",
        sideLabel: "Browse",
        onClick: () => routeToWorklist("supplier_directory"),
      }),
      makeQueueItem({
        key: "purchase_request_directory",
        title: "Purchase Requests",
        meta: "Purchase Material Requests only.",
        badgeClass: "review",
        sideLabel: "Browse",
        onClick: () => routeToWorklist("purchase_request_directory"),
      }),
      makeQueueItem({
        key: "purchase_order_directory",
        title: "Purchase Orders",
        meta: "Visible purchase orders for buyer follow-up.",
        badgeClass: "review",
        sideLabel: "Browse",
        onClick: () => routeToWorklist("purchase_order_directory"),
      })
    );

    $root.append($header, $priority, $directories);
    $(page.body).empty().append($root);

    frappe.call({ method: BOOTSTRAP_METHOD }).then((response) => {
      const payload = response && response.message ? response.message : {};
      pageState.payload = payload;
      if (payload.state && payload.state.kind === "restricted") {
        renderState(page, payload.state);
        return;
      }
      applyPayload($root, payload);
      $root.attr("data-erpw-console-bootstrap", "ready");
    }).catch((error) => {
      renderState(page, {
        kind: "error",
        title: "Procurement Console could not be loaded",
        detail: error && error.message ? error.message : "The buyer workbench could not be loaded right now.",
      });
    });
  }

  function render(wrapper) {
    const page = frappe.ui.make_app_page({
      parent: wrapper,
      title: "Procurement Console",
      single_column: true,
    });
    renderWorkbench(page);
  }

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) { render(wrapper); };
  frappe.pages[PAGE_KEY].on_page_show = function (wrapper) {
    if (window.erpWorkspaceConsoleSidebar && typeof window.erpWorkspaceConsoleSidebar.refresh === "function") {
      window.erpWorkspaceConsoleSidebar.refresh();
    }
    const host = wrapper && wrapper.page && wrapper.page.body ? wrapper.page.body : wrapper;
    if ($(host || []).find(".sales-console-shell").length) return;
    render(wrapper);
  };
})();
