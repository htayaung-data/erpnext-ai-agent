/* global frappe, $ */

(function () {
  const workspaceRegistry = window.erpWorkspaceUiWorkspaceRegistry || {};
  const procurementWorkspace = typeof workspaceRegistry.procurement === "function" ? workspaceRegistry.procurement() : null;
  const procurementRoutes = procurementWorkspace && procurementWorkspace.routes ? procurementWorkspace.routes : {};
  const procurementMethods = procurementWorkspace && procurementWorkspace.methods ? procurementWorkspace.methods : {};
  const PAGE_KEY = procurementRoutes.home || "procurement-console";
  const WORKLIST_ROUTE = procurementRoutes.worklist || "procurement-console-worklist";
  const REPORT_ROUTE = procurementRoutes.report || "procurement-console-report";
  const BOOTSTRAP_METHOD = procurementMethods.bootstrap || "erp_workspace_ui.procurement_console.service.get_procurement_console_bootstrap";
  function consoleRuntime() {
    return window.erpWorkspaceConsoleRuntime || {};
  }

  function runtimeMethod(name) {
    const method = consoleRuntime()[name];
    if (typeof method === "function") return method;
    throw new Error("Procurement Console runtime is missing method: " + name);
  }

  function escapeHtml(value) {
    return runtimeMethod("escapeHtml")(value);
  }

  function routeToWorklist(queueKey, filters) {
    frappe.route_options = filters && Object.keys(filters).length ? filters : {};
    frappe.set_route(WORKLIST_ROUTE, String(queueKey || "").replace(/_/g, "-"));
  }

  function routeToReport(reportKey, filters) {
    frappe.route_options = filters && Object.keys(filters).length ? filters : {};
    frappe.set_route(REPORT_ROUTE, String(reportKey || "").replace(/_/g, "-"));
  }

  function executeTarget(target) {
    if (!target) return;
    if (target.kind === "new_doc" && target.doctype) {
      frappe.route_options = target.defaults && typeof target.defaults === "object" ? Object.assign({}, target.defaults) : {};
      if (typeof frappe.new_doc === "function") {
        return frappe.new_doc(target.doctype);
      }
      return frappe.set_route("Form", target.doctype, "new-" + String(target.doctype).toLowerCase().replace(/\s+/g, "-"));
    }
    if (target.kind === "worklist" && target.queue_key) return routeToWorklist(target.queue_key, target.filters || null);
    if (target.kind === "report_page" && target.report_key) return routeToReport(target.report_key, target.filters || null);
  }

  function makeInsightCard(config) {
    return runtimeMethod("makeInsightCard")(config);
  }

  function makeAction(config) {
    return runtimeMethod("makeAction")(config);
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
      <div class="sales-console-shell" data-erpw-workspace="procurement" data-procurement-console-state="${escapeHtml(payloadState.kind || "unavailable")}">
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

  function makeFallbackPage(wrapper) {
    const $parent = $(wrapper);
    $parent.empty().append(`
      <div class="erpw-direct-console-page">
        <main class="layout-main-section erpw-direct-console-body"></main>
      </div>
    `);
    return {
      body: $parent.find(".erpw-direct-console-body").first(),
      set_title(title) {
        document.title = title || "Procurement Console";
      },
    };
  }

  function makeConsolePage(wrapper) {
    try {
      return frappe.ui.make_app_page({
        parent: wrapper,
        title: "Procurement Console",
        single_column: true,
      });
    } catch (error) {
      return makeFallbackPage(wrapper);
    }
  }

  function applyPayload($root, payload) {
    const work = (payload && payload.work) || {};
    const directories = (payload && payload.directories) || {};
    const insights = (payload && payload.insights) || {};
    Object.keys(work).forEach((key) => applyMetric($root, key, work[key]));
    Object.keys(directories).forEach((key) => applyMetric($root, key, directories[key]));
    Object.keys(insights).forEach((key) => applyMetric($root, key, insights[key]));
    renderCreateActions($root, payload);
  }

  function renderCreateActions($root, payload) {
    const actions = Array.isArray(payload && payload.create_actions) ? payload.create_actions : [];
    const targets = (payload && payload.action_targets) || {};
    const $section = $root.find('[data-section-key="create-actions"]').first();
    const $grid = $section.find('[data-section-grid="create-actions"]').first();
    $grid.empty().append(`
      <div class="sales-console-action-strip primary"></div>
      <div class="sales-console-action-strip secondary" hidden></div>
    `);
    if (!actions.length) {
      $section.attr("hidden", "hidden");
      return;
    }
    $section.removeAttr("hidden");
    const $primary = $grid.find(".sales-console-action-strip.primary").first();
    const $secondary = $grid.find(".sales-console-action-strip.secondary").first();
    actions.forEach((action, index) => {
      const isPrimary = index < 3;
      const $button = makeAction({
        key: action.key || "",
        title: action.title || action.label || action.key,
        meta: action.note || "Open the governed ERPNext form.",
        icon: "square",
        primary: isPrimary,
        tier: isPrimary ? "primary" : "secondary",
        onClick: () => executeTarget(targets[action.key]),
      });
      $button.attr("data-erpw-procurement-create-action", action.key || "");
      (isPrimary ? $primary : $secondary).append($button);
    });
    if (typeof runtimeMethod("rebalanceActionStrips") === "function") {
      runtimeMethod("rebalanceActionStrips")($section);
    }
  }

  function renderWorkbench(page) {
    const pageState = { payload: {} };
    const $root = $('<div class="sales-console-shell" data-erpw-workspace="procurement" data-erpw-console-runtime="ready" data-erpw-console-bootstrap="loading"></div>');

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
      makeInsightCard({ key: "purchase_orders_overdue", label: "Overdue POs", meta: "Open item lines past required date." })
        .on("click", () => routeToWorklist("purchase_orders_overdue")),
      makeInsightCard({ key: "purchase_orders_supplier_follow_up", label: "Supplier Follow-up", meta: "Orders needing buyer coordination." })
        .on("click", () => routeToWorklist("purchase_orders_supplier_follow_up")),
      makeInsightCard({ key: "purchase_orders_due_soon", label: "Due Soon", meta: "Open item lines due in the next seven days." })
        .on("click", () => routeToWorklist("purchase_orders_due_soon"))
    );

    const $priorityWork = $(`
      <section class="sales-console-card sales-console-section" data-section-key="priority-work">
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">Priority Work</h2>
          <div class="sales-console-section-note">Demand and quote validity</div>
        </div>
        <div class="sales-console-queue-grid" data-section-grid="priority-work"></div>
      </section>
    `);
    $priorityWork.find(".sales-console-queue-grid").append(
      makeQueueItem({
        key: "requests_to_source",
        title: "Requests To Source",
        meta: "Purchase demand needing buying action.",
        badgeClass: "attention",
        sideLabel: "Source",
        priority: true,
        onClick: () => routeToWorklist("requests_to_source"),
      }),
      makeQueueItem({
        key: "supplier_quotations_expiring",
        title: "Expiring Supplier Quotations",
        meta: "Quoted offers nearing validity end.",
        badgeClass: "blocker",
        sideLabel: "Review",
        priority: true,
        onClick: () => routeToWorklist("supplier_quotations_expiring"),
      })
    );

    const $createActions = $(`
      <section class="sales-console-card sales-console-section" data-section-key="create-actions" hidden>
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">Start Buying Work</h2>
          <div class="sales-console-section-note">Only actions available to your role</div>
        </div>
        <div class="sales-console-action-groups" data-section-grid="create-actions">
          <div class="sales-console-action-strip primary"></div>
          <div class="sales-console-action-strip secondary" hidden></div>
        </div>
      </section>
    `);

    const $pipeline = $(`
      <section class="sales-console-card sales-console-section" data-section-key="buying-pipeline">
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">Buying Pipeline</h2>
          <div class="sales-console-section-note">Demand to downstream visibility</div>
        </div>
        <div class="sales-console-queue-grid" data-section-grid="buying-pipeline"></div>
      </section>
    `);
    $pipeline.find(".sales-console-queue-grid").append(
      makeQueueItem({
        key: "requests_to_source",
        title: "Purchase Request",
        meta: "Submitted purchase demand waiting for sourcing or ordering.",
        badgeClass: "attention",
        sideLabel: "Source",
        onClick: () => routeToWorklist("requests_to_source"),
      }),
      makeQueueItem({
        key: "rfqs_awaiting_supplier_response",
        title: "RFQ",
        meta: "Supplier response posture for active requests.",
        badgeClass: "attention",
        sideLabel: "Response",
        onClick: () => routeToWorklist("rfqs_awaiting_supplier_response"),
      }),
      makeQueueItem({
        key: "supplier_quotations_to_compare",
        title: "Supplier Quotation",
        meta: "Quoted offers ready for buyer comparison.",
        badgeClass: "attention",
        sideLabel: "Compare",
        onClick: () => routeToWorklist("supplier_quotations_to_compare"),
      }),
      makeQueueItem({
        key: "purchase_order_directory",
        title: "Purchase Order",
        meta: "Orders visible for buyer follow-up and supplier coordination.",
        badgeClass: "review",
        sideLabel: "Orders",
        onClick: () => routeToWorklist("purchase_order_directory"),
      }),
      makeQueueItem({
        key: "purchase_orders_partially_received",
        title: "Receipt Visibility",
        meta: "Receiving posture only; warehouse teams own execution.",
        badgeClass: "review",
        sideLabel: "Receipt",
        onClick: () => routeToWorklist("purchase_orders_partially_received"),
      }),
      makeQueueItem({
        key: "purchase_orders_not_billed_visibility",
        title: "Billing Visibility",
        meta: "Billing posture only; Finance owns invoice and payment work.",
        badgeClass: "review",
        sideLabel: "Billing",
        onClick: () => routeToWorklist("purchase_orders_not_billed_visibility"),
      })
    );

    const $orderFollowUp = $(`
      <section class="sales-console-card sales-console-section" data-section-key="order-follow-up">
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">Order Follow-up</h2>
          <div class="sales-console-section-note">Buyer coordination queues</div>
        </div>
        <div class="sales-console-queue-grid" data-section-grid="order-follow-up"></div>
      </section>
    `);
    $orderFollowUp.find(".sales-console-queue-grid").append(
      makeQueueItem({
        key: "purchase_orders_overdue",
        title: "Overdue Purchase Orders",
        meta: "Open item lines past required date.",
        badgeClass: "blocker",
        sideLabel: "Overdue",
        onClick: () => routeToWorklist("purchase_orders_overdue"),
      }),
      makeQueueItem({
        key: "purchase_orders_due_soon",
        title: "Purchase Orders Due Soon",
        meta: "Open item lines due in the next seven days.",
        badgeClass: "attention",
        sideLabel: "Due Soon",
        onClick: () => routeToWorklist("purchase_orders_due_soon"),
      }),
      makeQueueItem({
        key: "purchase_orders_partially_received",
        title: "Partially Received Purchase Orders",
        meta: "Some receipt posted but fulfillment is not complete.",
        badgeClass: "attention",
        sideLabel: "Partial",
        onClick: () => routeToWorklist("purchase_orders_partially_received"),
      }),
      makeQueueItem({
        key: "purchase_orders_not_billed_visibility",
        title: "Received Not Fully Billed",
        meta: "Downstream billing posture only; Finance owns invoice and payment work.",
        badgeClass: "review",
        sideLabel: "Visibility",
        onClick: () => routeToWorklist("purchase_orders_not_billed_visibility"),
      })
    );

    const $directories = $(`
      <section class="sales-console-card sales-console-section" data-section-key="directories">
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">Directories</h2>
          <div class="sales-console-section-note">Compact record access</div>
        </div>
        <div class="sales-console-queue-grid" data-section-grid="directories"></div>
      </section>
    `);
    $directories.find(".sales-console-queue-grid").append(
      makeQueueItem({
        key: "supplier_directory",
        title: "Suppliers",
        meta: "Supplier records for buying coordination.",
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
      }),
      makeQueueItem({
        key: "rfq_directory",
        title: "RFQs",
        meta: "Request for Quotation records visible to this user.",
        badgeClass: "review",
        sideLabel: "Browse",
        onClick: () => routeToWorklist("rfq_directory"),
      }),
      makeQueueItem({
        key: "supplier_quotation_directory",
        title: "Supplier Quotations",
        meta: "Supplier quotation records visible to this user.",
        badgeClass: "review",
        sideLabel: "Browse",
        onClick: () => routeToWorklist("supplier_quotation_directory"),
      }),
      makeQueueItem({
        key: "buying_item_directory",
        title: "Buying Items",
        meta: "Purchase-enabled item and catalog context.",
        badgeClass: "review",
        sideLabel: "Browse",
        onClick: () => routeToWorklist("buying_item_directory"),
      })
    );

    const $sourcing = $(`
      <section class="sales-console-card sales-console-section" data-section-key="sourcing">
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">Sourcing Desk</h2>
          <div class="sales-console-section-note">RFQ and quotation decisions</div>
        </div>
        <div class="sales-console-queue-grid" data-section-grid="sourcing"></div>
      </section>
    `);
    $sourcing.find(".sales-console-queue-grid").append(
      makeQueueItem({
        key: "rfqs_awaiting_supplier_response",
        title: "RFQs Awaiting Supplier Response",
        meta: "Submitted RFQs with pending supplier responses.",
        badgeClass: "attention",
        sideLabel: "Pending",
        onClick: () => routeToWorklist("rfqs_awaiting_supplier_response"),
      }),
      makeQueueItem({
        key: "supplier_quotations_to_compare",
        title: "Supplier Quotations To Compare",
        meta: "Submitted quotations available for price and validity review.",
        badgeClass: "attention",
        sideLabel: "Compare",
        onClick: () => routeToWorklist("supplier_quotations_to_compare"),
      }),
      makeQueueItem({
        key: "supplier_quotations_expiring",
        title: "Expiring Supplier Quotations",
        meta: "Quotation validity ending within seven days.",
        badgeClass: "blocker",
        sideLabel: "Review",
        onClick: () => routeToWorklist("supplier_quotations_expiring"),
      }),
      makeQueueItem({
        key: "supplier_quotation_comparison",
        title: "Quote Comparison",
        meta: "Compare quoted prices, validity, supplier, item, and RFQ reference.",
        badgeClass: "review",
        sideLabel: "Report",
        onClick: () => routeToReport("supplier_quotation_comparison"),
      })
    );

    $root.append($header, $createActions, $priorityWork, $pipeline, $orderFollowUp, $sourcing, $directories);
    $(page.body).empty().append($root);
    pruneRouteShells($root.get(0));

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
    const page = makeConsolePage(wrapper);
    if (wrapper) {
      const route = frappe.get_route ? frappe.get_route() : [];
      wrapper.__erpwProcurementConsole = {
        routeSignature: Array.isArray(route) ? route.join("|") : "",
      };
    }
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
