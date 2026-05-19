/* global frappe, $ */

(function () {
  const workspaceRegistry = window.erpWorkspaceUiWorkspaceRegistry || {};
  const procurementWorkspace = typeof workspaceRegistry.procurement === "function" ? workspaceRegistry.procurement() : null;
  const procurementRoutes = procurementWorkspace && procurementWorkspace.routes ? procurementWorkspace.routes : {};
  const procurementMethods = procurementWorkspace && procurementWorkspace.methods ? procurementWorkspace.methods : {};
  const PAGE_KEY = procurementRoutes.purchaseOrderForm || "procurement-console-purchase-order-form";
  const WORKLIST_ROUTE = procurementRoutes.worklist || "procurement-console-worklist";
  const CONTEXT_METHOD = procurementMethods.managedPurchaseOrderContext || "erp_workspace_ui.procurement_console.managed_purchase_order.get_managed_purchase_order_context";
  const SAVE_METHOD = procurementMethods.managedPurchaseOrderSave || "erp_workspace_ui.procurement_console.managed_purchase_order.save_managed_purchase_order";
  const ITEM_DEFAULTS_METHOD = procurementMethods.managedPurchaseOrderItemDefaults || "erp_workspace_ui.procurement_console.managed_purchase_order.get_managed_purchase_order_item_defaults";
  const OUTPUT_CONTEXT_METHOD = "erp_workspace_ui.procurement_console.document_output.get_document_output_context";
  const OUTPUT_PREVIEW_METHOD = "erp_workspace_ui.procurement_console.document_output.get_document_print_preview_context";
  const OUTPUT_PDF_METHOD = "erp_workspace_ui.procurement_console.document_output.download_document_pdf";
  const CHILD_PAGE_RUNTIME_URLS = [
    "/assets/erp_workspace_ui/js/runtime/child_page/child_page_helpers.js",
    "/assets/erp_workspace_ui/js/runtime/child_page/child_page_shell_content.js",
    "/assets/erp_workspace_ui/js/procurement_console/procurement_readiness_ui.js",
  ];
  let runtimePromise = null;

  function helpers() {
    return (window.erpWorkspaceUiChildPage && window.erpWorkspaceUiChildPage.helpers) || {};
  }

  function shellContent() {
    return (window.erpWorkspaceUiChildPage && window.erpWorkspaceUiChildPage.shellContent) || {};
  }

  function hasReadinessUi() {
    const readiness = window.erpWorkspaceUiProcurementReadiness || {};
    return typeof readiness.renderReadinessCard === "function" && typeof readiness.bindReadinessLinks === "function";
  }

  function hasRuntime() {
    return typeof shellContent().renderShellContent === "function" && hasReadinessUi();
  }

  function requireAsset(url) {
    return new Promise((resolve) => frappe.require(url, () => resolve()));
  }

  function ensureRuntime() {
    if (hasRuntime()) return Promise.resolve(shellContent());
    if (runtimePromise) return runtimePromise;
    runtimePromise = CHILD_PAGE_RUNTIME_URLS.reduce(
      (promise, url) => promise.then(() => (hasRuntime() ? null : requireAsset(url))),
      Promise.resolve()
    ).then(() => {
      if (!hasRuntime()) throw new Error("Shared child-page runtime is unavailable.");
      return shellContent();
    }).catch((error) => {
      runtimePromise = null;
      throw error;
    });
    return runtimePromise;
  }

  function escapeHtml(value) {
    const fn = helpers().escapeHtml;
    if (typeof fn === "function") return fn(value);
    return frappe.utils.escape_html(value == null ? "" : String(value));
  }

  function toNumber(value) {
    const numberValue = Number(value);
    return Number.isFinite(numberValue) ? numberValue : 0;
  }

  function calcAmount(row) {
    return toNumber(row && row.qty) * toNumber(row && row.rate);
  }

  function formatAmount(value) {
    const numberValue = toNumber(value);
    if (!numberValue) return "0.00";
    return numberValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function ensureStyles() {
    if (document.getElementById("erpw-managed-po-form-style")) return;
    const style = document.createElement("style");
    style.id = "erpw-managed-po-form-style";
    style.textContent = `
      .erpw-managed-po-page { padding-bottom: 24px; }
      .erpw-managed-po-shell { display: grid; gap: 10px; max-width: 1220px; margin: 0 auto; }
      .erpw-managed-po-shell .erpw-child-summary { min-height: 0; padding: 12px 16px; border-radius: 14px; border: 1px solid #dbe6f2; background: #ffffff; box-shadow: inset 0 1px 0 rgba(255,255,255,0.98), 0 8px 18px rgba(15,23,42,0.027); }
      .erpw-managed-po-shell .erpw-child-summary-copy { min-width: 0; background: transparent; }
      .erpw-managed-po-shell .erpw-child-summary-facts { display: none; padding: 0; border: 0; }
      .erpw-managed-po-shell .erpw-child-summary-top { align-items: center; gap: 12px; }
      .erpw-managed-po-shell .erpw-child-kicker { color: #0f766e; font-size: 10px; letter-spacing: 0.09em; }
      .erpw-managed-po-shell .erpw-child-title { font-size: 20px; line-height: 1.12; letter-spacing: 0; margin-top: 3px; }
      .erpw-managed-po-shell .erpw-child-subtitle { max-width: 620px; margin-top: 4px; font-size: 12.5px; line-height: 1.32; color: #334155; }
      .erpw-managed-po-shell .erpw-child-chip-row-header { align-self: center; }
      .erpw-managed-po-shell .erpw-child-chip { min-height: 25px; padding: 0.22rem 0.56rem; }
      .erpw-managed-po-shell .erpw-child-actions-toolbar { margin-top: -4px; padding: 0 2px; border: 0; background: transparent; box-shadow: none; }
      .erpw-managed-po-shell .erpw-child-toolbar-actions { justify-content: flex-start; flex-wrap: wrap; gap: 8px; }
      .erpw-managed-po-shell .erpw-child-toolbar-action { min-height: 34px; border-radius: 10px; }
      .erpw-managed-po-card { display: grid; gap: 12px; padding: 15px 18px 18px; overflow: visible; }
      .erpw-managed-po-output-card { display: grid; gap: 12px; padding: 15px 18px 18px; border: 1px solid #dbe6f2; border-radius: 14px; background: #ffffff; box-shadow: inset 0 1px 0 rgba(255,255,255,0.98), 0 7px 16px rgba(15,23,42,0.03); }
      .erpw-managed-po-output-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
      .erpw-managed-po-output-title { font-size: 15px; line-height: 1.25; font-weight: 790; color: #0f172a; }
      .erpw-managed-po-output-note { margin-top: 3px; color: #475569; font-size: 12.5px; line-height: 1.36; max-width: 700px; }
      .erpw-managed-po-output-badge { display: inline-flex; min-height: 26px; align-items: center; padding: 0 10px; border-radius: 999px; border: 1px solid #fed7aa; background: #fff7ed; color: #9a3412; font-size: 12px; font-weight: 760; white-space: nowrap; }
      .erpw-managed-po-output-actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
      .erpw-managed-po-output-button { min-height: 34px; border: 1px solid #d5e2ef; border-radius: 10px; background: #fff; color: #12365f; font-weight: 740; font-size: 12px; padding: 0 12px; }
      .erpw-managed-po-output-button:hover:not(:disabled) { border-color: #9db7d2; background: #f8fbff; }
      .erpw-managed-po-output-button:disabled { opacity: 0.58; cursor: not-allowed; }
      .erpw-managed-po-output-message { min-height: 18px; color: #64748b; font-size: 12.5px; line-height: 1.36; }
      .erpw-managed-po-output-message.error { color: #b42318; }
      .erpw-output-modal-backdrop { position: fixed; inset: 0; z-index: 1400; background: rgba(15,23,42,0.36); display: flex; align-items: center; justify-content: center; padding: 22px; }
      .erpw-output-modal { width: min(980px, 96vw); max-height: min(820px, 92vh); overflow: hidden; display: grid; grid-template-rows: auto 1fr; border-radius: 16px; background: #fff; box-shadow: 0 26px 70px rgba(15,23,42,0.28); border: 1px solid #dbe6f2; }
      .erpw-output-modal-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 12px 14px; border-bottom: 1px solid #e2e8f0; }
      .erpw-output-modal-title { font-weight: 800; color: #0f172a; }
      .erpw-output-modal-close { min-height: 32px; border: 1px solid #d5e2ef; border-radius: 9px; background: #fff; color: #12365f; font-weight: 740; padding: 0 10px; }
      .erpw-output-modal-body { overflow: auto; background: #f8fafc; padding: 16px; }
      .erpw-output-preview { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; }
      .erpw-output-preview-banner { padding: 9px 12px; background: #fefce8; color: #854d0e; font-size: 12px; font-weight: 800; border-bottom: 1px solid #fef3c7; }
      .erpw-output-preview-supplier { padding: 8px 12px; color: #334155; font-size: 12px; border-bottom: 1px solid #e2e8f0; }
      .erpw-output-preview-body { padding: 12px; overflow: auto; }
      .erpw-managed-po-section-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; }
      .erpw-managed-po-section-title { margin-top: 3px; font-size: 15.5px; line-height: 1.25; font-weight: 790; color: #0f172a; }
      .erpw-managed-po-section-note { margin-top: 3px; max-width: 620px; font-size: 12.5px; line-height: 1.38; color: #475569; }
      .erpw-managed-po-grid { display: grid; grid-template-columns: minmax(260px, 1.4fr) repeat(3, minmax(130px, 170px)); gap: 12px; align-items: end; }
      .erpw-managed-po-field { display: grid; gap: 6px; min-width: 0; }
      .erpw-managed-po-field label { font-size: 10.5px; line-height: 1.2; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; margin: 0; }
      .erpw-managed-po-input, .erpw-managed-po-table input { width: 100%; min-height: 37px; border: 1px solid #d5e2ef; border-radius: 11px; padding: 0 10px; font-size: 13px; color: #0f172a; background: #fff; box-shadow: inset 0 1px 0 rgba(255,255,255,0.95); box-sizing: border-box; }
      .erpw-managed-po-input:focus, .erpw-managed-po-table input:focus { outline: none; border-color: #8fb0d3; box-shadow: 0 0 0 3px rgba(18,54,95,0.08); }
      .erpw-managed-po-lines-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; padding-top: 2px; }
      .erpw-managed-po-lines-title { font-size: 14px; line-height: 1.25; font-weight: 790; color: #0f172a; }
      .erpw-managed-po-lines-note { margin-top: 3px; color: #64748b; font-size: 12.5px; line-height: 1.36; }
      .erpw-managed-po-table-wrap { overflow: visible; border: 0; border-radius: 0; background: transparent; }
      .erpw-managed-po-table, .erpw-managed-po-table tbody, .erpw-managed-po-table tr, .erpw-managed-po-table td { display: block; box-sizing: border-box; }
      .erpw-managed-po-table { width: 100%; min-width: 0; border-collapse: separate; border-spacing: 0; }
      .erpw-managed-po-table thead { display: block; margin: 0 0 6px; }
      .erpw-managed-po-table thead tr { display: grid; grid-template-columns: minmax(232px, 1.22fr) 74px minmax(128px, 0.48fr) minmax(168px, 0.82fr) 92px 78px 112px 64px; gap: 12px; align-items: end; padding: 0 12px; border: 0; background: transparent; box-shadow: none; }
      .erpw-managed-po-table th { display: block; min-width: 0; padding: 0; border: 0; color: #64748b; font-size: 10px; line-height: 1.15; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; text-align: left; white-space: nowrap; }
      .erpw-managed-po-table tbody { display: grid; gap: 10px; }
      .erpw-managed-po-table tbody tr { display: grid; grid-template-columns: minmax(232px, 1.22fr) 74px minmax(128px, 0.48fr) minmax(168px, 0.82fr) 92px 78px 112px 64px; gap: 12px; align-items: end; padding: 12px; border: 1px solid #dbe6f2; border-radius: 14px; background: #ffffff; box-shadow: inset 0 1px 0 rgba(255,255,255,0.98), 0 7px 16px rgba(15,23,42,0.03); }
      .erpw-managed-po-table td { min-width: 0; padding: 0; border: 0; display: grid; gap: 6px; vertical-align: top; }
      .erpw-managed-po-table td::before { content: ""; display: none; }
      .erpw-managed-po-table td.row-action { align-self: end; }
      .erpw-managed-po-table td.row-action::before { content: ""; display: none; }
      .erpw-managed-po-uom-value, .erpw-managed-po-amount-value { display: inline-flex; align-items: center; justify-content: center; min-width: 70px; min-height: 37px; max-width: 100%; border-radius: 999px; border: 1px solid #dbe6f2; background: #f8fafc; color: #334155; padding: 0 11px; font-size: 13px; line-height: 1; font-weight: 650; letter-spacing: 0; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; white-space: nowrap; overflow: visible; text-overflow: clip; box-sizing: border-box; }
      .erpw-managed-po-amount-value { justify-content: flex-end; min-width: 92px; border-radius: 11px; font-variant-numeric: tabular-nums; }
      .erpw-managed-po-row-button, .erpw-managed-po-add-line { min-height: 34px; border: 1px solid #d5e2ef; border-radius: 10px; background: #fff; color: #12365f; font-weight: 740; font-size: 12px; padding: 0 10px; }
      .erpw-managed-po-row-button { width: 100%; max-width: 62px; padding: 0 8px; color: #475569; }
      .erpw-managed-po-row-button:hover, .erpw-managed-po-add-line:hover { border-color: #9db7d2; background: #f8fbff; color: #12365f; }
      .erpw-managed-po-lines-footer { display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap; }
      .erpw-managed-po-add-line { justify-self: start; }
      .erpw-managed-po-message { min-height: 20px; font-size: 12.5px; color: #64748b; }
      .erpw-managed-po-message.error { color: #b42318; }
      .erpw-managed-po-suggestions { position: fixed; z-index: 1200; min-width: 0; max-height: 240px; overflow: auto; margin: 0; border: 1px solid #d5e2ef; border-radius: 12px; background: #fff; box-shadow: 0 18px 40px rgba(15,23,42,0.18); }
      .erpw-managed-po-suggestion { display: block; width: 100%; text-align: left; border: 0; background: transparent; padding: 9px 11px; font-size: 13px; color: #0f172a; }
      .erpw-managed-po-suggestion:hover, .erpw-managed-po-suggestion:focus-visible { background: #f1f5f9; outline: none; }
      .erpw-managed-po-link-cell { position: relative; }
      @media (max-width: 1280px) {
        .erpw-managed-po-grid { grid-template-columns: minmax(260px, 1fr) repeat(2, minmax(145px, 180px)); }
        .erpw-managed-po-table thead tr, .erpw-managed-po-table tbody tr { grid-template-columns: minmax(220px, 1fr) 72px 88px 70px 96px 62px; grid-template-areas: "item qty rate uom amount action" "date warehouse warehouse warehouse warehouse action"; gap: 8px; align-items: end; }
        .erpw-managed-po-table thead tr { padding: 0 10px; }
        .erpw-managed-po-table tbody tr { padding: 10px; }
        .erpw-managed-po-table th:nth-child(1) { grid-area: item; }
        .erpw-managed-po-table th.qty { grid-area: qty; }
        .erpw-managed-po-table th.date { grid-area: date; }
        .erpw-managed-po-table th.warehouse { grid-area: warehouse; }
        .erpw-managed-po-table th.rate { grid-area: rate; }
        .erpw-managed-po-table th.uom { grid-area: uom; }
        .erpw-managed-po-table th.amount { grid-area: amount; }
        .erpw-managed-po-table th.row-action { grid-area: action; }
        .erpw-managed-po-line-item { grid-area: item; }
        .erpw-managed-po-line-qty { grid-area: qty; }
        .erpw-managed-po-line-date { grid-area: date; max-width: 180px; }
        .erpw-managed-po-line-warehouse { grid-area: warehouse; }
        .erpw-managed-po-line-rate { grid-area: rate; }
        .erpw-managed-po-line-uom { grid-area: uom; }
        .erpw-managed-po-line-amount { grid-area: amount; max-width: none; }
        .erpw-managed-po-line-action { grid-area: action; }
        .erpw-managed-po-amount-value { min-width: 0; width: 100%; }
        .erpw-managed-po-row-button { max-width: 60px; padding: 0 6px; font-size: 11.5px; }
      }
      @media (max-width: 720px) {
        .erpw-managed-po-grid { grid-template-columns: 1fr; }
        .erpw-managed-po-shell .erpw-child-summary-top { display: grid; }
        .erpw-managed-po-table thead { display: none; }
        .erpw-managed-po-table tbody tr { grid-template-columns: 1fr 86px 74px; grid-template-areas: "item item item" "qty uom action" "date date date" "warehouse warehouse warehouse" "rate rate rate" "amount amount amount"; }
        .erpw-managed-po-table td::before { content: attr(data-label); display: block; font-size: 10px; line-height: 1.15; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; }
        .erpw-managed-po-line-amount { max-width: none; }
      }
    `;
    document.head.appendChild(style);
  }

  function routeParts() {
    const route = frappe.get_route ? frappe.get_route() : [];
    if (Array.isArray(route) && String(route[0] || "") === PAGE_KEY) return route;
    const path = String(window.location && window.location.pathname || "").replace(/^\/+/, "");
    const parts = path.split("/").filter(Boolean);
    const deskParts = parts[0] === "desk" || parts[0] === "app" ? parts.slice(1) : parts;
    return deskParts.map((part) => {
      try { return decodeURIComponent(part || ""); } catch (error) { return part || ""; }
    });
  }

  function resolveName() {
    const parts = routeParts();
    return parts.length > 1 ? String(parts[1] || "new") : "new";
  }

  function routeToWorklist(queueKey) {
    frappe.route_options = {};
    frappe.set_route(WORKLIST_ROUTE, String(queueKey || "purchase_order_directory").replace(/_/g, "-"));
  }

  function routeToPage(route, parts, options) {
    frappe.route_options = options || {};
    return frappe.set_route.apply(frappe, [route].concat(Array.isArray(parts) ? parts : []));
  }

  function cleanupManagedPageChrome(wrapper) {
    $(wrapper).find(".page-head").remove();
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

  function isAttached($node) {
    const node = $node && $node.get ? $node.get(0) : null;
    return Boolean(node && document.documentElement.contains(node));
  }

  function makePage(wrapper) {
    try {
      return frappe.ui.make_app_page({ parent: wrapper, title: "Purchase Order Form", single_column: true });
    } catch (error) {
      const $parent = $(wrapper);
      $parent.empty().append('<main class="layout-main-section erpw-direct-child-body"></main>');
      return { body: $parent.find(".erpw-direct-child-body").first(), set_title(title) { document.title = title || "Purchase Order Form"; } };
    }
  }

  function ensureHost(page, wrapper) {
    const $parent = page && page.body ? $(page.body) : $(wrapper);
    let $host = $parent.children(".erpw-managed-po-page").first();
    if (!$host.length) {
      $host = $('<section class="erpw-managed-po-page"></section>');
      $parent.empty().append($host);
    }
    let $shell = $host.children(".erpw-child-shell.erpw-child-detail-shell.erpw-managed-po-shell").first();
    if (!$shell.length) {
      $shell = $('<div class="erpw-child-shell erpw-child-detail-shell erpw-managed-po-shell"></div>');
      $host.append($shell);
    }
    return { $host, $shell };
  }

  function stateForm(payload) {
    const form = payload && payload.form ? payload.form : {};
    const header = form.header || {};
    const items = Array.isArray(form.items) && form.items.length ? form.items : [{ item_code: "", qty: 1, rate: "", schedule_date: header.schedule_date || "", warehouse: header.set_warehouse || "", uom: "", amount: "" }];
    return {
      name: form.name || "new",
      header: {
        supplier: header.supplier || "",
        transaction_date: header.transaction_date || "",
        schedule_date: header.schedule_date || header.default_required_by || "",
        set_warehouse: header.set_warehouse || "",
        buying_price_list: header.buying_price_list || "",
        company: header.company || "",
        currency: header.currency || "",
        conversion_rate: header.conversion_rate || 1,
      },
      items: items.map((row) => {
        const current = Object.assign({ item_code: "", qty: 1, rate: "", schedule_date: header.schedule_date || "", warehouse: header.set_warehouse || "", uom: "", amount: "" }, row || {});
        current._schedule_date_mode = current._schedule_date_mode || (current.schedule_date && current.schedule_date !== (header.schedule_date || "") ? "manual" : "inherited");
        current.amount = calcAmount(current);
        return current;
      }),
    };
  }

  function actionConfig(payload, viewState) {
    const actions = payload && payload.controls && Array.isArray(payload.controls.actions) ? payload.controls.actions : [];
    return actions.map((action) => Object.assign({}, action, {
      title: action.key === "reset_unsaved" ? "Reset" : action.title || action.label || action.key,
      variant: action.kind === "primary" ? "primary" : "secondary",
      icon: action.key === "save_purchase_order" ? "check" : action.key === "back_to_purchase_orders" ? "arrow-left" : "refresh",
      handler() {
        if (action.key === "save_purchase_order") return savePurchaseOrder(viewState);
        if (action.key === "reset_unsaved") return loadRoute(viewState, { force: true });
        const target = ((viewState.payload && viewState.payload.action_targets) || {})[action.key];
        if (target && target.kind === "worklist") return routeToWorklist(target.queue_key);
        if (target && target.kind === "page" && target.route) return routeToPage(target.route, target.route_parts, target.options);
      },
    }));
  }


  function isSavedForm(form) {
    return form && form.name && form.name !== "new";
  }

  function outputCardMarkup(form, outputContext) {
    if (!isSavedForm(form)) return "";
    const context = outputContext && outputContext.name === form.name ? outputContext : null;
    return `
      <section class="erpw-managed-po-output-card" data-managed-po-output-card data-document-name="${escapeHtml(form.name)}">
        <div class="erpw-managed-po-output-top">
          <div>
            <div class="erpw-managed-po-output-title">Document Output</div>
            <div class="erpw-managed-po-output-note">Preview and PDF are internal draft output only. Supplier send requires a governed purchase order release step.</div>
          </div>
          <span class="erpw-managed-po-output-badge">${escapeHtml(context ? context.warning || "Draft / Not for supplier" : "Draft / Not for supplier")}</span>
        </div>
        <div class="erpw-managed-po-output-actions">
          <button type="button" class="erpw-managed-po-output-button" data-po-output-preview ${context ? "" : "disabled"}>Preview Purchase Order</button>
          <button type="button" class="erpw-managed-po-output-button" data-po-output-download ${context ? "" : "disabled"}>Download PO PDF</button>
        </div>
        <div class="erpw-managed-po-output-message" data-po-output-message>${escapeHtml(context ? context.send_block_reason || "Supplier send is deferred." : "Loading output controls...")}</div>
      </section>
    `;
  }

  function outputPdfUrl(args) {
    const params = new URLSearchParams();
    Object.keys(args || {}).forEach((key) => {
      if (args[key] !== undefined && args[key] !== null && String(args[key]).trim() !== "") params.set(key, args[key]);
    });
    return `/api/method/${OUTPUT_PDF_METHOD}?${params.toString()}`;
  }

  function showOutputMessage($shell, message, tone) {
    $shell.find("[data-po-output-message]").text(message || "").toggleClass("error", tone === "error");
  }

  function showPreviewModal(title, html) {
    $(".erpw-output-modal-backdrop").remove();
    const $modal = $(
      `<div class="erpw-output-modal-backdrop" role="dialog" aria-modal="true">
        <section class="erpw-output-modal">
          <div class="erpw-output-modal-head"><div class="erpw-output-modal-title"></div><button type="button" class="erpw-output-modal-close">Close</button></div>
          <div class="erpw-output-modal-body"></div>
        </section>
      </div>`
    );
    $modal.find(".erpw-output-modal-title").text(title || "Document preview");
    $modal.find(".erpw-output-modal-body").html(html || "");
    $modal.find(".erpw-output-modal-close").on("click", () => $modal.remove());
    $modal.on("click", (event) => { if (event.target === $modal.get(0)) $modal.remove(); });
    $(document.body).append($modal);
  }

  function loadOutputContext(viewState) {
    const form = viewState.form || stateForm(viewState.payload);
    if (!isSavedForm(form)) return Promise.resolve(null);
    if (viewState.outputContext && viewState.outputContext.name === form.name) return Promise.resolve(viewState.outputContext);
    return frappe.call({ method: OUTPUT_CONTEXT_METHOD, args: { doctype: "Purchase Order", name: form.name } }).then((response) => {
      const context = response && response.message ? response.message : {};
      viewState.outputContext = context;
      renderPayload(viewState);
      return context;
    });
  }

  function bindOutputCard($shell, viewState) {
    const $card = $shell.find("[data-managed-po-output-card]");
    if (!$card.length) return;
    loadOutputContext(viewState);
    $card.find("[data-po-output-preview]").off("click.output").on("click.output", () => {
      const form = viewState.form || stateForm(viewState.payload);
      showOutputMessage($shell, "Rendering Purchase Order preview...", "");
      frappe.call({ method: OUTPUT_PREVIEW_METHOD, args: { doctype: "Purchase Order", name: form.name } }).then((response) => {
        const payload = response && response.message ? response.message : {};
        if (payload.state && payload.state.kind === "ready") {
          showPreviewModal("Purchase Order Preview", payload.html || "");
          showOutputMessage($shell, payload.filename || "Purchase Order preview ready.", "");
        } else {
          showOutputMessage($shell, payload.state && payload.state.detail ? payload.state.detail : "Purchase Order preview unavailable.", "error");
        }
      });
    });
    $card.find("[data-po-output-download]").off("click.output").on("click.output", () => {
      const form = viewState.form || stateForm(viewState.payload);
      showOutputMessage($shell, "Preparing Purchase Order PDF...", "");
      window.open(outputPdfUrl({ doctype: "Purchase Order", name: form.name }), "_blank", "noopener");
    });
  }

  function formMarkup(form) {
    const header = form.header || {};
    return `
      <section class="erpw-child-card erpw-managed-po-card" data-erpw-managed-po-form>
        <div class="erpw-managed-po-section-head">
          <div>
            <div class="erpw-managed-po-section-title">Order details</div>
            <div class="erpw-managed-po-section-note">New item lines use the default date unless changed.</div>
          </div>
        </div>
        <div class="erpw-managed-po-grid">
          <div class="erpw-managed-po-field erpw-managed-po-link-cell"><label>Supplier</label><input class="erpw-managed-po-input supplier-link" data-field="supplier" value="${escapeHtml(header.supplier || "")}" placeholder="Select supplier" autocomplete="off"></div>
          <div class="erpw-managed-po-field"><label>Transaction Date</label><input class="erpw-managed-po-input" data-field="transaction_date" type="date" value="${escapeHtml(header.transaction_date || "")}"></div>
          <div class="erpw-managed-po-field"><label>Default Required By</label><input class="erpw-managed-po-input" data-field="schedule_date" type="date" value="${escapeHtml(header.schedule_date || "")}"></div>
          <div class="erpw-managed-po-field"><label>Currency</label><input class="erpw-managed-po-input" data-field="currency" value="${escapeHtml(header.currency || "")}" placeholder="Currency"></div>
        </div>
        <div class="erpw-managed-po-lines-head">
          <div>
            <div class="erpw-managed-po-lines-title">Items</div>
            <div class="erpw-managed-po-lines-note">Select items, required dates, warehouse, quantities, and buyer-entered rates.</div>
          </div>
        </div>
        <div class="erpw-managed-po-table-wrap">
          <table class="erpw-managed-po-table">
            <thead><tr><th>Item</th><th class="qty">Qty</th><th class="date">Line Required By</th><th class="warehouse">Warehouse</th><th class="rate">Rate</th><th class="uom">UOM</th><th class="amount">Amount</th><th class="row-action">Action</th></tr></thead>
            <tbody>
              ${(form.items || []).map((row, index) => `
                <tr data-row-index="${index}">
                  <td class="erpw-managed-po-link-cell erpw-managed-po-line-item" data-label="Item"><input class="item-link" data-row-field="item_code" value="${escapeHtml(row.item_code || "")}" placeholder="Select item" autocomplete="off"></td>
                  <td class="erpw-managed-po-line-qty" data-label="Qty"><input data-row-field="qty" type="number" min="0" step="0.01" value="${escapeHtml(row.qty || "")}"></td>
                  <td class="erpw-managed-po-line-date" data-label="Line Required By"><input data-row-field="schedule_date" data-schedule-mode="${escapeHtml(row._schedule_date_mode || "inherited")}" type="date" value="${escapeHtml(row.schedule_date || header.schedule_date || "")}"></td>
                  <td class="erpw-managed-po-link-cell erpw-managed-po-line-warehouse" data-label="Warehouse"><input class="warehouse-link" data-row-field="warehouse" value="${escapeHtml(row.warehouse || "")}" placeholder="Optional warehouse" autocomplete="off"></td>
                  <td class="erpw-managed-po-line-rate" data-label="Rate"><input data-row-field="rate" type="number" min="0" step="0.01" value="${escapeHtml(row.rate || "")}"></td>
                  <td class="uom erpw-managed-po-line-uom" data-label="UOM"><span class="erpw-managed-po-uom-value" data-uom-display>${escapeHtml(row.uom || "Derived")}</span><input type="hidden" data-row-field="uom" value="${escapeHtml(row.uom || "")}"></td>
                  <td class="amount erpw-managed-po-line-amount" data-label="Amount"><span class="erpw-managed-po-amount-value" data-amount-display>${escapeHtml(formatAmount(row.amount || calcAmount(row)))}</span><input type="hidden" data-row-field="amount" value="${escapeHtml(row.amount || calcAmount(row))}"></td>
                  <td class="row-action erpw-managed-po-line-action"><button type="button" class="erpw-managed-po-row-button" data-remove-row="${index}">Remove</button></td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
        <div class="erpw-managed-po-lines-footer">
          <button type="button" class="erpw-managed-po-add-line" data-add-row>Add line</button>
          <div class="erpw-managed-po-message" data-managed-po-message></div>
        </div>
      </section>
    `;
  }

  function collectForm($shell, viewState) {
    const form = viewState.form || stateForm(viewState.payload);
    form.header.supplier = $shell.find('[data-field="supplier"]').val() || "";
    form.header.transaction_date = $shell.find('[data-field="transaction_date"]').val() || "";
    form.header.schedule_date = $shell.find('[data-field="schedule_date"]').val() || "";
    form.header.currency = $shell.find('[data-field="currency"]').val() || "";
    $shell.find("tbody tr[data-row-index]").each(function () {
      const index = Number($(this).attr("data-row-index"));
      const row = form.items[index] || {};
      $(this).find("[data-row-field]").each(function () {
        const key = $(this).attr("data-row-field");
        row[key] = $(this).val();
        if (key === "schedule_date") row._schedule_date_mode = $(this).attr("data-schedule-mode") || row._schedule_date_mode || "inherited";
      });
      row.amount = calcAmount(row);
      form.items[index] = row;
    });
    viewState.form = form;
    updateAmounts($shell, viewState);
    return form;
  }

  function setMessage($shell, message, tone) {
    $shell.find("[data-managed-po-message]").text(message || "").toggleClass("error", tone === "error");
  }

  function updateAmounts($shell, viewState) {
    const form = viewState.form || stateForm(viewState.payload);
    $shell.find("tr[data-row-index]").each(function () {
      const index = Number($(this).attr("data-row-index"));
      const row = form.items[index] || {};
      const amount = calcAmount(row);
      row.amount = amount;
      $(this).find("[data-amount-display]").text(formatAmount(amount));
      $(this).find('[data-row-field="amount"]').val(amount);
    });
  }

  function syncInheritedLineDates($shell, viewState, defaultDate, previousDefaultDate) {
    const form = viewState.form || stateForm(viewState.payload);
    form.header.schedule_date = defaultDate || "";
    $shell.find('tr[data-row-index]').each(function () {
      const index = Number($(this).attr("data-row-index"));
      const $date = $(this).find('[data-row-field="schedule_date"]');
      const mode = $date.attr("data-schedule-mode") || (form.items[index] && form.items[index]._schedule_date_mode) || "inherited";
      const currentDate = $date.val() || "";
      const stillDefaulted = currentDate === (previousDefaultDate || "");
      if (mode !== "manual" || stillDefaulted) {
        $date.val(defaultDate || "").attr("data-schedule-mode", "inherited");
        if (form.items[index]) {
          form.items[index].schedule_date = defaultDate || "";
          form.items[index]._schedule_date_mode = "inherited";
        }
      }
    });
    viewState.form = form;
  }

  function savePurchaseOrder(viewState) {
    const form = collectForm(viewState.$shell, viewState);
    setMessage(viewState.$shell, "Recording purchase order...", "");
    return frappe.call({ method: SAVE_METHOD, args: { payload: JSON.stringify(form) } }).then((response) => {
      const payload = response && response.message ? response.message : {};
      if (payload.state && payload.state.kind === "ready") {
        const nextName = payload.form && payload.form.name ? payload.form.name : form.name;
        viewState.payload = payload;
        viewState.form = stateForm(payload);
        if (nextName && nextName !== "new" && resolveName() !== nextName) {
          frappe.set_route(PAGE_KEY, nextName);
          return;
        }
        renderPayload(viewState);
        setMessage(viewState.$shell, payload.message || "Purchase Order recorded for operational review.", "");
        return;
      }
      renderPayload(viewState, payload);
    }).catch((error) => {
      setMessage(viewState.$shell, error && error.message ? error.message : "Purchase Order could not be saved.", "error");
    });
  }

  function bindForm($shell, viewState) {
    $shell.find("[data-field], [data-row-field]").off("input.poform change.poform");
    $shell.find('[data-field="schedule_date"]').on("input.poform change.poform", function () {
      const previousDefaultDate = (viewState.form && viewState.form.header && viewState.form.header.schedule_date) || "";
      collectForm($shell, viewState);
      syncInheritedLineDates($shell, viewState, $(this).val() || "", previousDefaultDate);
      collectForm($shell, viewState);
    });
    $shell.find('[data-row-field="schedule_date"]').on("input.poform change.poform", function () {
      $(this).attr("data-schedule-mode", "manual");
      collectForm($shell, viewState);
    });
    $shell.find('[data-field]:not([data-field="schedule_date"]), [data-row-field]:not([data-row-field="schedule_date"])').on("input.poform change.poform", () => collectForm($shell, viewState));
    $shell.find('[data-row-field="qty"], [data-row-field="rate"]').on("input.poform change.poform", () => {
      collectForm($shell, viewState);
      updateAmounts($shell, viewState);
    });
    $shell.find("[data-add-row]").off("click.poform").on("click.poform", () => {
      collectForm($shell, viewState);
      const headerDate = viewState.form.header.schedule_date || "";
      viewState.form.items.push({ item_code: "", qty: 1, rate: "", schedule_date: headerDate, warehouse: "", uom: "", amount: "", _schedule_date_mode: "inherited" });
      renderPayload(viewState);
    });
    $shell.find("[data-remove-row]").off("click.poform").on("click.poform", function () {
      collectForm($shell, viewState);
      const index = Number($(this).attr("data-remove-row"));
      viewState.form.items.splice(index, 1);
      if (!viewState.form.items.length) viewState.form.items.push({ item_code: "", qty: 1, rate: "", schedule_date: viewState.form.header.schedule_date || "", warehouse: "", uom: "", amount: "", _schedule_date_mode: "inherited" });
      renderPayload(viewState);
    });
    bindLinkField($shell, viewState, ".supplier-link", "Supplier");
    bindLinkField($shell, viewState, ".item-link", "Item");
    bindLinkField($shell, viewState, ".warehouse-link", "Warehouse");
  }

  function bindLinkField($shell, viewState, selector, doctype) {
    let timer = null;
    $shell.find(selector).off("input.link focus.link blur.link").on("input.link focus.link", function () {
      const input = this;
      clearTimeout(timer);
      timer = setTimeout(() => showSuggestions($shell, input, doctype, viewState), 180);
    }).on("blur.link", function () {
      const input = this;
      setTimeout(removeSuggestions, 180);
      if (doctype === "Item") updateItemDefaults($shell, input, viewState);
    });
  }

  function removeSuggestions() {
    $(window).off("resize.managedPoSuggest scroll.managedPoSuggest");
    $(document).off("scroll.managedPoSuggest");
    $(".erpw-managed-po-suggestions").remove();
  }

  function positionSuggestions($menu, input) {
    const rect = input.getBoundingClientRect();
    const viewportWidth = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
    const viewportHeight = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);
    const width = Math.min(Math.max(rect.width, 300), Math.max(220, viewportWidth - rect.left - 12));
    const desiredHeight = 240;
    const usefulBelowHeight = 128;
    const minPanelHeight = 56;
    const availableBelow = Math.max(0, viewportHeight - rect.bottom - 16);
    const availableAbove = Math.max(0, rect.top - 16);
    const protectedBottom = [".erpw-child-summary", ".erpw-child-actions-toolbar"].reduce((bottom, selector) => {
      const node = document.querySelector(selector);
      if (!node) return bottom;
      const box = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      if (box.width <= 0 || box.height <= 0 || style.display === "none" || style.visibility === "hidden") return bottom;
      return Math.max(bottom, box.bottom + 8);
    }, 12);
    const naturalHeight = Math.min(desiredHeight, Math.max(minPanelHeight, $menu.get(0) ? $menu.get(0).scrollHeight : minPanelHeight));
    const aboveHeight = Math.min(desiredHeight, availableAbove);
    const aboveTop = Math.max(12, rect.top - Math.min(naturalHeight, aboveHeight) - 6);
    const canUseBelow = availableBelow >= minPanelHeight;
    const belowIsUseful = availableBelow >= usefulBelowHeight;
    const aboveIsMateriallyBetter = aboveHeight >= usefulBelowHeight && aboveHeight > availableBelow + 80;
    const aboveAvoidsChrome = aboveTop >= protectedBottom;
    const placeAbove = !belowIsUseful && aboveIsMateriallyBetter && aboveAvoidsChrome;
    const maxHeight = Math.max(minPanelHeight, Math.min(desiredHeight, placeAbove ? availableAbove : Math.max(availableBelow, canUseBelow ? availableBelow : minPanelHeight)));
    const menuHeight = Math.min(naturalHeight, maxHeight);
    const top = placeAbove ? aboveTop : Math.min(rect.bottom + 6, Math.max(12, viewportHeight - menuHeight - 12));
    $menu.css({ left: `${Math.round(rect.left)}px`, top: `${Math.round(top)}px`, width: `${Math.round(width)}px`, maxHeight: `${Math.round(maxHeight)}px` });
  }

  function showSuggestions($shell, input, doctype, viewState) {
    const $input = $(input);
    const txt = String($input.val() || "").trim();
    if (txt.length < 1) {
      removeSuggestions();
      return;
    }
    frappe.call({ method: "frappe.desk.search.search_link", args: { doctype, txt, page_length: 8 } }).then((response) => {
      const rows = response && response.message && Array.isArray(response.message.results) ? response.message.results : Array.isArray(response.message) ? response.message : [];
      removeSuggestions();
      if (!rows.length || !document.body.contains(input)) return;
      const $menu = $('<div class="erpw-managed-po-suggestions" role="listbox"></div>');
      rows.slice(0, 8).forEach((row) => {
        const value = row.value || row.name || row.label || row;
        const label = row.label || row.description || value;
        $('<button type="button" class="erpw-managed-po-suggestion" role="option"></button>').text(label).on("mousedown", (event) => {
          event.preventDefault();
          $input.val(value);
          collectForm($shell, viewState);
          removeSuggestions();
          if (doctype === "Item") updateItemDefaults($shell, input, viewState);
        }).appendTo($menu);
      });
      $menu.appendTo(document.body);
      positionSuggestions($menu, input);
      $(window).off("resize.managedPoSuggest scroll.managedPoSuggest").on("resize.managedPoSuggest scroll.managedPoSuggest", () => positionSuggestions($menu, input));
      $(document).off("scroll.managedPoSuggest").on("scroll.managedPoSuggest", () => positionSuggestions($menu, input));
    });
  }

  function updateItemDefaults($shell, input, viewState) {
    const $input = $(input);
    const itemCode = String($input.val() || "").trim();
    if (!itemCode) return;
    const $row = $input.closest("tr[data-row-index]");
    const index = Number($row.attr("data-row-index"));
    frappe.call({ method: ITEM_DEFAULTS_METHOD, args: { item_code: itemCode } }).then((response) => {
      const payload = response && response.message ? response.message : {};
      const item = payload.item || {};
      if (!item.uom) return;
      $row.find('[data-row-field="uom"]').val(item.uom);
      $row.find("[data-uom-display]").text(item.uom || "Derived");
      collectForm($shell, viewState);
      if (viewState.form.items[index]) viewState.form.items[index].uom = item.uom;
    });
  }

  function loadingPayload() {
    return {
      state: { kind: "loading", title: "Loading Purchase Order form", detail: "Reading purchase order context." },
      summary: { kicker: "Purchase Order", title: "New Purchase Order", subtitle: "Record supplier order details before operational processing.", chips: [{ label: "New Purchase Order" }, { label: "Buying order" }] },
      controls: { actions: [] },
      form: { header: { supplier: "", transaction_date: "", schedule_date: "", company: "", currency: "", conversion_rate: 1 }, items: [{ item_code: "", qty: 1, rate: "", schedule_date: "", warehouse: "", uom: "", amount: "" }] },
      action_targets: {},
    };
  }

  function renderState(payload) {
    const state = payload && payload.state ? payload.state : {};
    return `
      <section class="erpw-child-card erpw-list-results">
        <div class="erpw-list-state ${escapeHtml(state.kind || "unavailable")}">
          <div class="erpw-list-state-title">${escapeHtml(state.title || "Purchase Order form unavailable")}</div>
          <div class="erpw-list-state-detail">${escapeHtml(state.detail || "This managed Purchase Order form cannot be loaded right now.")}</div>
        </div>
      </section>
    `;
  }


  function readinessUi() {
    return window.erpWorkspaceUiProcurementReadiness || {};
  }

  function readinessCardMarkup(payload) {
    const context = payload && payload.readiness_context ? payload.readiness_context : null;
    const ui = readinessUi();
    if (!context || typeof ui.renderReadinessCard !== "function") return "";
    return ui.renderReadinessCard(context, {
      title: "Readiness Review",
      note: "Read-only guidance for future governed procurement steps.",
    });
  }

  function bindReadinessCard($shell) {
    const ui = readinessUi();
    if (typeof ui.bindReadinessLinks === "function") ui.bindReadinessLinks($shell);
  }

  function renderPayload(viewState, overridePayload) {
    removeSuggestions();
    const payload = overridePayload || viewState.payload || loadingPayload();
    const form = overridePayload && payload.state && payload.state.kind !== "ready" ? viewState.form || stateForm(viewState.payload) : viewState.form || stateForm(payload);
    const output = outputCardMarkup(form, viewState.outputContext);
    const extra = payload.state && payload.state.kind && payload.state.kind !== "ready" && payload.state.kind !== "loading" ? renderState(payload) : formMarkup(form) + readinessCardMarkup(payload) + output;
    shellContent().renderShellContent(viewState.$shell, {
      summary: payload.summary || loadingPayload().summary,
      actions: actionConfig(payload, viewState),
      actionLayout: { mode: "toolbar" },
      extraSectionsHtml: extra,
    });
    viewState.$shell.attr("data-erpw-managed-po-state", payload.state && payload.state.kind ? payload.state.kind : "ready");
    if (payload.state && payload.state.kind === "ready") {
      bindForm(viewState.$shell, viewState);
      bindOutputCard(viewState.$shell, viewState);
      bindReadinessCard(viewState.$shell);
    }
  }

  function loadRoute(viewState) {
    const name = resolveName();
    viewState.form = null;
    renderPayload(viewState, loadingPayload());
    return frappe.call({ method: CONTEXT_METHOD, args: { name } }).then((response) => {
      const payload = response && response.message ? response.message : {};
      viewState.payload = payload;
      viewState.form = stateForm(payload);
      viewState.outputContext = null;
      renderPayload(viewState);
    }).catch((error) => {
      renderPayload(viewState, { state: { kind: "error", title: "Purchase Order form failed", detail: error && error.message ? error.message : "The managed form could not load." } });
    });
  }

  function render(wrapper) {
    cleanupRouteShells();
    ensureStyles();
    const page = makePage(wrapper);
    cleanupManagedPageChrome(wrapper);
    const host = ensureHost(page, wrapper);
    const viewState = { page, wrapper, $host: host.$host, $shell: host.$shell, payload: loadingPayload(), form: null };
    wrapper.__erpwManagedPurchaseOrderForm = viewState;
    pruneRouteShells(host.$host.get(0));
    ensureRuntime().then(() => loadRoute(viewState));
  }

  function show(wrapper) {
    const state = wrapper && wrapper.__erpwManagedPurchaseOrderForm;
    if (state && state.$shell && state.$shell.length && isAttached(state.$host) && isAttached(state.$shell)) {
      cleanupManagedPageChrome(wrapper);
      pruneRouteShells(state.$host.get(0));
      loadRoute(state);
      return;
    }
    render(wrapper);
  }

  window.erpWorkspaceUiProcurementPurchaseOrderForm = Object.assign(window.erpWorkspaceUiProcurementPurchaseOrderForm || {}, {
    render,
    show,
  });
})();
