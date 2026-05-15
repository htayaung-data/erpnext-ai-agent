/* global frappe, $ */

(function () {
  const workspaceRegistry = window.erpWorkspaceUiWorkspaceRegistry || {};
  const procurementWorkspace = typeof workspaceRegistry.procurement === "function" ? workspaceRegistry.procurement() : null;
  const procurementRoutes = procurementWorkspace && procurementWorkspace.routes ? procurementWorkspace.routes : {};
  const procurementMethods = procurementWorkspace && procurementWorkspace.methods ? procurementWorkspace.methods : {};
  const PAGE_KEY = procurementRoutes.rfqForm || "procurement-console-rfq-form";
  const WORKLIST_ROUTE = procurementRoutes.worklist || "procurement-console-worklist";
  const CONTEXT_METHOD = procurementMethods.managedRfqContext || "erp_workspace_ui.procurement_console.managed_rfq.get_managed_rfq_context";
  const SAVE_METHOD = procurementMethods.managedRfqSave || "erp_workspace_ui.procurement_console.managed_rfq.save_managed_rfq_draft";
  const ITEM_DEFAULTS_METHOD = procurementMethods.managedRfqItemDefaults || "erp_workspace_ui.procurement_console.managed_rfq.get_managed_rfq_item_defaults";
  const OUTPUT_CONTEXT_METHOD = "erp_workspace_ui.procurement_console.document_output.get_document_output_context";
  const OUTPUT_PREVIEW_METHOD = "erp_workspace_ui.procurement_console.document_output.get_document_print_preview_context";
  const OUTPUT_PDF_METHOD = "erp_workspace_ui.procurement_console.document_output.download_document_pdf";
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

  function hasRuntime() {
    return typeof shellContent().renderShellContent === "function";
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

  function ensureStyles() {
    if (document.getElementById("erpw-managed-rfq-form-style")) return;
    const style = document.createElement("style");
    style.id = "erpw-managed-rfq-form-style";
    style.textContent = `
      .erpw-managed-rfq-page { padding-bottom: 24px; }
      .erpw-managed-rfq-shell { display: grid; gap: 10px; max-width: 1220px; margin: 0 auto; }
      .erpw-managed-rfq-shell .erpw-child-summary { min-height: 0; padding: 12px 16px; border-radius: 14px; border: 1px solid #dbe6f2; background: #ffffff; box-shadow: inset 0 1px 0 rgba(255,255,255,0.98), 0 8px 18px rgba(15,23,42,0.027); }
      .erpw-managed-rfq-shell .erpw-child-summary-copy { min-width: 0; background: transparent; }
      .erpw-managed-rfq-shell .erpw-child-summary-facts { display: none; padding: 0; border: 0; }
      .erpw-managed-rfq-shell .erpw-child-summary-top { align-items: center; gap: 12px; }
      .erpw-managed-rfq-shell .erpw-child-kicker { color: #0f766e; font-size: 10px; letter-spacing: 0.09em; }
      .erpw-managed-rfq-shell .erpw-child-title { font-size: 20px; line-height: 1.12; letter-spacing: 0; margin-top: 3px; }
      .erpw-managed-rfq-shell .erpw-child-subtitle { max-width: 620px; margin-top: 4px; font-size: 12.5px; line-height: 1.32; color: #334155; }
      .erpw-managed-rfq-shell .erpw-child-chip-row-header { align-self: center; }
      .erpw-managed-rfq-shell .erpw-child-chip { min-height: 25px; padding: 0.22rem 0.56rem; }
      .erpw-managed-rfq-shell .erpw-child-actions-toolbar { margin-top: -4px; padding: 0 2px; border: 0; background: transparent; box-shadow: none; }
      .erpw-managed-rfq-shell .erpw-child-toolbar-actions { justify-content: flex-start; flex-wrap: wrap; gap: 8px; }
      .erpw-managed-rfq-shell .erpw-child-toolbar-action { min-height: 34px; border-radius: 10px; }
      .erpw-managed-rfq-card { display: grid; gap: 12px; padding: 15px 18px 18px; overflow: visible; }
      .erpw-managed-rfq-output-card { display: grid; gap: 12px; padding: 15px 18px 18px; border: 1px solid #dbe6f2; border-radius: 14px; background: #ffffff; box-shadow: inset 0 1px 0 rgba(255,255,255,0.98), 0 7px 16px rgba(15,23,42,0.03); }
      .erpw-managed-rfq-output-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
      .erpw-managed-rfq-output-title { font-size: 15px; line-height: 1.25; font-weight: 790; color: #0f172a; }
      .erpw-managed-rfq-output-note { margin-top: 3px; color: #475569; font-size: 12.5px; line-height: 1.36; max-width: 680px; }
      .erpw-managed-rfq-output-badge { display: inline-flex; min-height: 26px; align-items: center; padding: 0 10px; border-radius: 999px; border: 1px solid #d9eadf; background: #f3faf6; color: #166534; font-size: 12px; font-weight: 760; white-space: nowrap; }
      .erpw-managed-rfq-output-grid { display: grid; grid-template-columns: minmax(240px, 360px) minmax(0, 1fr); gap: 12px; align-items: end; }
      .erpw-managed-rfq-output-field { display: grid; gap: 6px; min-width: 0; }
      .erpw-managed-rfq-output-field label { font-size: 10.5px; line-height: 1.2; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; margin: 0; }
      .erpw-managed-rfq-output-field select { width: 100%; min-height: 37px; border: 1px solid #d5e2ef; border-radius: 11px; padding: 0 10px; background: #fff; color: #0f172a; font-size: 13px; box-sizing: border-box; }
      .erpw-managed-rfq-output-actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
      .erpw-managed-rfq-output-button { min-height: 34px; border: 1px solid #d5e2ef; border-radius: 10px; background: #fff; color: #12365f; font-weight: 740; font-size: 12px; padding: 0 12px; }
      .erpw-managed-rfq-output-button:hover:not(:disabled) { border-color: #9db7d2; background: #f8fbff; }
      .erpw-managed-rfq-output-button:disabled { opacity: 0.58; cursor: not-allowed; }
      .erpw-managed-rfq-output-message { min-height: 18px; color: #64748b; font-size: 12.5px; line-height: 1.36; }
      .erpw-managed-rfq-output-message.error { color: #b42318; }
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
      .erpw-managed-rfq-section-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; }
      .erpw-managed-rfq-section-kicker { font-size: 10.5px; line-height: 1.2; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; }
      .erpw-managed-rfq-section-title { margin-top: 3px; font-size: 15.5px; line-height: 1.25; font-weight: 790; color: #0f172a; }
      .erpw-managed-rfq-section-note { margin-top: 3px; max-width: 620px; font-size: 12.5px; line-height: 1.38; color: #475569; }
      .erpw-managed-rfq-grid { display: grid; grid-template-columns: repeat(2, minmax(170px, 220px)); gap: 12px; align-items: end; }
      .erpw-managed-rfq-field { display: grid; gap: 6px; min-width: 0; }
      .erpw-managed-rfq-field label { font-size: 10.5px; line-height: 1.2; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; margin: 0; }
      .erpw-managed-rfq-input, .erpw-managed-rfq-table input, .erpw-managed-rfq-supplier-table input { width: 100%; min-height: 37px; border: 1px solid #d5e2ef; border-radius: 11px; padding: 0 10px; font-size: 13px; color: #0f172a; background: #fff; box-shadow: inset 0 1px 0 rgba(255,255,255,0.95); box-sizing: border-box; }
      .erpw-managed-rfq-input:focus, .erpw-managed-rfq-table input:focus, .erpw-managed-rfq-supplier-table input:focus { outline: none; border-color: #8fb0d3; box-shadow: 0 0 0 3px rgba(18,54,95,0.08); }
      .erpw-managed-rfq-lines-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; padding-top: 2px; }
      .erpw-managed-rfq-lines-title { font-size: 14px; line-height: 1.25; font-weight: 790; color: #0f172a; }
      .erpw-managed-rfq-lines-note { margin-top: 3px; color: #64748b; font-size: 12.5px; line-height: 1.36; }
      .erpw-managed-rfq-table-wrap { overflow: visible; border: 0; border-radius: 0; background: transparent; }
      .erpw-managed-rfq-table, .erpw-managed-rfq-table tbody, .erpw-managed-rfq-table tr, .erpw-managed-rfq-table td, .erpw-managed-rfq-supplier-table, .erpw-managed-rfq-supplier-table tbody, .erpw-managed-rfq-supplier-table tr, .erpw-managed-rfq-supplier-table td { display: block; box-sizing: border-box; }
      .erpw-managed-rfq-table, .erpw-managed-rfq-supplier-table { width: 100%; min-width: 0; border-collapse: separate; border-spacing: 0; }
      .erpw-managed-rfq-supplier-table thead { display: none; }
      .erpw-managed-rfq-table thead { display: block; margin: 0 0 6px; }
      .erpw-managed-rfq-table thead tr { display: grid; grid-template-columns: minmax(240px, 1.35fr) 78px 128px minmax(180px, 1fr) 76px 66px; gap: 10px; align-items: end; padding: 0 12px; border: 0; background: transparent; box-shadow: none; }
      .erpw-managed-rfq-table th { display: block; min-width: 0; padding: 0; border: 0; color: #64748b; font-size: 10px; line-height: 1.15; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; text-align: left; white-space: nowrap; }
      .erpw-managed-rfq-table tbody, .erpw-managed-rfq-supplier-table tbody { display: grid; gap: 10px; }
      .erpw-managed-rfq-supplier-table tr { display: grid; grid-template-columns: minmax(280px, 520px) 76px; gap: 10px; align-items: end; padding: 12px; border: 1px solid #dbe6f2; border-radius: 14px; background: #ffffff; box-shadow: inset 0 1px 0 rgba(255,255,255,0.98), 0 7px 16px rgba(15,23,42,0.03); }
      .erpw-managed-rfq-table tbody tr { display: grid; grid-template-columns: minmax(240px, 1.35fr) 78px 128px minmax(180px, 1fr) 76px 66px; gap: 10px; align-items: end; padding: 12px; border: 1px solid #dbe6f2; border-radius: 14px; background: #ffffff; box-shadow: inset 0 1px 0 rgba(255,255,255,0.98), 0 7px 16px rgba(15,23,42,0.03); }
      .erpw-managed-rfq-table td, .erpw-managed-rfq-supplier-table td { min-width: 0; padding: 0; border: 0; display: grid; gap: 6px; vertical-align: top; }
      .erpw-managed-rfq-table td::before { content: ""; display: none; }
      .erpw-managed-rfq-supplier-table td::before { content: attr(data-label); font-size: 10px; line-height: 1.15; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; }
      .erpw-managed-rfq-table td.row-action, .erpw-managed-rfq-supplier-table td.row-action { align-self: end; }
      .erpw-managed-rfq-table td.row-action::before, .erpw-managed-rfq-supplier-table td.row-action::before { content: ""; display: none; }
      .erpw-managed-rfq-uom-value { display: inline-flex; align-items: center; justify-content: center; min-width: 70px; min-height: 37px; max-width: 100%; border-radius: 999px; border: 1px solid #dbe6f2; background: #f8fafc; color: #334155; padding: 0 11px; font-size: 13px; line-height: 1; font-weight: 650; letter-spacing: 0; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; white-space: nowrap; overflow: visible; text-overflow: clip; box-sizing: border-box; }
      .erpw-managed-rfq-row-button, .erpw-managed-rfq-add-line { min-height: 34px; border: 1px solid #d5e2ef; border-radius: 10px; background: #fff; color: #12365f; font-weight: 740; font-size: 12px; padding: 0 10px; }
      .erpw-managed-rfq-row-button { width: 100%; max-width: 62px; padding: 0 8px; color: #475569; }
      .erpw-managed-rfq-row-button:hover, .erpw-managed-rfq-add-line:hover { border-color: #9db7d2; background: #f8fbff; color: #12365f; }
      .erpw-managed-rfq-lines-footer { display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap; }
      .erpw-managed-rfq-add-line { justify-self: start; }
      .erpw-managed-rfq-message { min-height: 20px; font-size: 12.5px; color: #64748b; }
      .erpw-managed-rfq-message.error { color: #b42318; }
      .erpw-managed-rfq-suggestions { position: fixed; z-index: 1200; min-width: 0; max-height: 240px; overflow: auto; margin: 0; border: 1px solid #d5e2ef; border-radius: 12px; background: #fff; box-shadow: 0 18px 40px rgba(15,23,42,0.18); }
      .erpw-managed-rfq-suggestion { display: block; width: 100%; text-align: left; border: 0; background: transparent; padding: 9px 11px; font-size: 13px; color: #0f172a; }
      .erpw-managed-rfq-suggestion:hover, .erpw-managed-rfq-suggestion:focus-visible { background: #f1f5f9; outline: none; }
      .erpw-managed-rfq-link-cell { position: relative; }
      @media (max-width: 1180px) {
        .erpw-managed-rfq-table thead tr, .erpw-managed-rfq-table tbody tr { grid-template-columns: minmax(250px, 1fr) 78px 76px 62px; grid-template-areas: "item qty uom action" "date warehouse warehouse warehouse"; align-items: end; }
        .erpw-managed-rfq-table th:nth-child(1) { grid-area: item; }
        .erpw-managed-rfq-table th.qty { grid-area: qty; }
        .erpw-managed-rfq-table th.date { grid-area: date; }
        .erpw-managed-rfq-table th:nth-child(4) { grid-area: warehouse; }
        .erpw-managed-rfq-table th.uom { grid-area: uom; }
        .erpw-managed-rfq-table th.row-action { grid-area: action; }
        .erpw-managed-rfq-line-item { grid-area: item; }
        .erpw-managed-rfq-line-qty { grid-area: qty; }
        .erpw-managed-rfq-line-date { grid-area: date; max-width: 180px; }
        .erpw-managed-rfq-line-warehouse { grid-area: warehouse; }
        .erpw-managed-rfq-line-uom { grid-area: uom; }
        .erpw-managed-rfq-line-action { grid-area: action; }
      }
      @media (max-width: 720px) {
        .erpw-managed-rfq-grid, .erpw-managed-rfq-output-grid { grid-template-columns: 1fr; }
        .erpw-managed-rfq-supplier-table tr { grid-template-columns: 1fr 66px; }
        .erpw-managed-rfq-shell .erpw-child-summary-top { display: grid; }
        .erpw-managed-rfq-table thead { display: none; }
        .erpw-managed-rfq-table tbody tr { grid-template-columns: 1fr 86px 74px; grid-template-areas: "item item item" "qty uom action" "date date date" "warehouse warehouse warehouse"; }
        .erpw-managed-rfq-table td::before { content: attr(data-label); display: block; font-size: 10px; line-height: 1.15; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; }
        .erpw-managed-rfq-line-date { max-width: none; }
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
    frappe.set_route(WORKLIST_ROUTE, String(queueKey || "rfq_directory").replace(/_/g, "-"));
  }

  function routeToPage(route, parts, options) {
    frappe.route_options = options || {};
    return frappe.set_route.apply(frappe, [route].concat(Array.isArray(parts) ? parts : []));
  }

  function cleanupForNativeRoute() {
    if (window.erpWorkspaceUiBoot && typeof window.erpWorkspaceUiBoot.cleanupProcurementRouteShells === "function") {
      window.erpWorkspaceUiBoot.cleanupProcurementRouteShells("", { removeActive: true });
      setTimeout(() => window.erpWorkspaceUiBoot.cleanupProcurementRouteShells("", { removeActive: true }), 0);
      setTimeout(() => window.erpWorkspaceUiBoot.cleanupProcurementRouteShells("", { removeActive: true }), 80);
    }
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

  function rememberNativeChromeTarget(target) {
    const context = target && target.native_chrome && typeof target.native_chrome === "object" ? Object.assign({}, target.native_chrome) : null;
    if (!context) return;
    context.createdAt = Date.now();
    const nativeChrome = window.erpWorkspaceUiProcurementNativeChrome || {};
    if (typeof nativeChrome.remember === "function") return nativeChrome.remember(context);
    try { window.sessionStorage.setItem("erpwProcurementNativeChromeContext", JSON.stringify(context)); } catch (error) { window.__erpwProcurementNativeChromeContext = context; }
  }

  function makePage(wrapper) {
    try {
      return frappe.ui.make_app_page({ parent: wrapper, title: "RFQ Form", single_column: true });
    } catch (error) {
      const $parent = $(wrapper);
      $parent.empty().append('<main class="layout-main-section erpw-direct-child-body"></main>');
      return { body: $parent.find(".erpw-direct-child-body").first(), set_title(title) { document.title = title || "RFQ Form"; } };
    }
  }

  function ensureHost(page, wrapper) {
    const $parent = page && page.body ? $(page.body) : $(wrapper);
    let $host = $parent.children(".erpw-managed-rfq-page").first();
    if (!$host.length) {
      $host = $('<section class="erpw-managed-rfq-page"></section>');
      $parent.empty().append($host);
    }
    let $shell = $host.children(".erpw-child-shell.erpw-child-detail-shell.erpw-managed-rfq-shell").first();
    if (!$shell.length) {
      $shell = $('<div class="erpw-child-shell erpw-child-detail-shell erpw-managed-rfq-shell"></div>');
      $host.append($shell);
    }
    return { $host, $shell };
  }

  function stateForm(payload) {
    const form = payload && payload.form ? payload.form : {};
    const header = form.header || {};
    const suppliers = Array.isArray(form.suppliers) && form.suppliers.length ? form.suppliers : [{ supplier: "" }];
    const items = Array.isArray(form.items) && form.items.length ? form.items : [{ item_code: "", qty: 1, schedule_date: header.schedule_date || "", warehouse: "", uom: "" }];
    return {
      name: form.name || "new",
      header: {
        transaction_date: header.transaction_date || "",
        schedule_date: header.schedule_date || "",
        company: header.company || "",
        subject: header.subject || "Request for Quotation",
        message_for_supplier: header.message_for_supplier || "Please supply the specified items at the best possible rates",
      },
      suppliers: suppliers.map((row) => Object.assign({ supplier: "" }, row || {})),
      items: items.map((row) => {
        const current = Object.assign({ item_code: "", qty: 1, schedule_date: header.schedule_date || "", warehouse: "", uom: "" }, row || {});
        current._schedule_date_mode = current._schedule_date_mode || (current.schedule_date && current.schedule_date !== (header.schedule_date || "") ? "manual" : "inherited");
        return current;
      }),
    };
  }

  function actionConfig(payload, viewState) {
    const actions = payload && payload.controls && Array.isArray(payload.controls.actions) ? payload.controls.actions : [];
    return actions.map((action) => Object.assign({}, action, {
      title: action.key === "reset_unsaved" ? "Reset" : action.title || action.label || action.key,
      variant: action.kind === "primary" ? "primary" : "secondary",
      icon: action.key === "save_rfq" ? "check" : action.key === "open_erp_form" ? "external" : action.key === "back_to_rfqs" ? "arrow-left" : "refresh",
      handler() {
        if (action.key === "save_rfq") return saveRfq(viewState);
        if (action.key === "reset_unsaved") return loadRoute(viewState, { force: true });
        const target = ((viewState.payload && viewState.payload.action_targets) || {})[action.key];
        if (target && target.kind === "worklist") return routeToWorklist(target.queue_key);
        if (target && target.kind === "page" && target.route) return routeToPage(target.route, target.route_parts, target.options);
        if (target && target.kind === "form" && target.doctype && target.name) {
          rememberNativeChromeTarget(target);
          cleanupForNativeRoute();
          return frappe.set_route("Form", target.doctype, target.name);
        }
      },
    }));
  }


  function isSavedForm(form) {
    return form && form.name && form.name !== "new";
  }

  function outputCardMarkup(form, outputContext) {
    if (!isSavedForm(form)) return "";
    const context = outputContext && outputContext.name === form.name ? outputContext : null;
    const suppliers = context && Array.isArray(context.suppliers) ? context.suppliers : [];
    const selected = context && context.selected_supplier ? context.selected_supplier : (suppliers.length === 1 ? suppliers[0].supplier : "");
    return `
      <section class="erpw-managed-rfq-output-card" data-managed-rfq-output-card data-document-name="${escapeHtml(form.name)}">
        <div class="erpw-managed-rfq-output-top">
          <div>
            <div class="erpw-managed-rfq-output-title">Supplier Communication</div>
            <div class="erpw-managed-rfq-output-note">Preview and PDF output are supplier-specific. Email send is deferred until a governed RFQ send step exists.</div>
          </div>
          <span class="erpw-managed-rfq-output-badge">${escapeHtml(context ? context.warning || "Draft / Not sent" : "Draft / Not sent")}</span>
        </div>
        <div class="erpw-managed-rfq-output-grid">
          <div class="erpw-managed-rfq-output-field">
            <label>Supplier context</label>
            <select data-rfq-output-supplier ${context ? "" : "disabled"}>
              <option value="">Select supplier</option>
              ${suppliers.map((row) => `<option value="${escapeHtml(row.supplier)}" ${row.supplier === selected ? "selected" : ""}>${escapeHtml(row.supplier_name || row.supplier)}</option>`).join("")}
            </select>
          </div>
          <div class="erpw-managed-rfq-output-actions">
            <button type="button" class="erpw-managed-rfq-output-button" data-rfq-output-preview ${context ? "" : "disabled"}>Preview RFQ</button>
            <button type="button" class="erpw-managed-rfq-output-button" data-rfq-output-download ${context ? "" : "disabled"}>Download RFQ PDF</button>
          </div>
        </div>
        <div class="erpw-managed-rfq-output-message" data-rfq-output-message>${escapeHtml(context ? context.send_block_reason || "Email send is deferred." : "Loading output controls...")}</div>
      </section>
    `;
  }

  function selectedOutputSupplier($shell) {
    return String($shell.find("[data-rfq-output-supplier]").val() || "").trim();
  }

  function outputPdfUrl(args) {
    const params = new URLSearchParams();
    Object.keys(args || {}).forEach((key) => {
      if (args[key] !== undefined && args[key] !== null && String(args[key]).trim() !== "") params.set(key, args[key]);
    });
    return `/api/method/${OUTPUT_PDF_METHOD}?${params.toString()}`;
  }

  function showOutputMessage($shell, message, tone) {
    $shell.find("[data-rfq-output-message]").text(message || "").toggleClass("error", tone === "error");
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
    return frappe.call({ method: OUTPUT_CONTEXT_METHOD, args: { doctype: "Request for Quotation", name: form.name } }).then((response) => {
      const context = response && response.message ? response.message : {};
      viewState.outputContext = context;
      renderPayload(viewState);
      return context;
    });
  }

  function bindOutputCard($shell, viewState) {
    const $card = $shell.find("[data-managed-rfq-output-card]");
    if (!$card.length) return;
    loadOutputContext(viewState);
    $card.find("[data-rfq-output-preview]").off("click.output").on("click.output", () => {
      const form = viewState.form || stateForm(viewState.payload);
      const supplier = selectedOutputSupplier($shell);
      if (!supplier) {
        showOutputMessage($shell, "Select one supplier before previewing RFQ output.", "error");
        return;
      }
      showOutputMessage($shell, "Rendering RFQ preview...", "");
      frappe.call({ method: OUTPUT_PREVIEW_METHOD, args: { doctype: "Request for Quotation", name: form.name, supplier } }).then((response) => {
        const payload = response && response.message ? response.message : {};
        if (payload.state && payload.state.kind === "ready") {
          showPreviewModal(`RFQ Preview - ${supplier}`, payload.html || "");
          showOutputMessage($shell, payload.filename || "RFQ preview ready.", "");
        } else {
          showOutputMessage($shell, payload.state && payload.state.detail ? payload.state.detail : "RFQ preview unavailable.", "error");
        }
      });
    });
    $card.find("[data-rfq-output-download]").off("click.output").on("click.output", () => {
      const form = viewState.form || stateForm(viewState.payload);
      const supplier = selectedOutputSupplier($shell);
      if (!supplier) {
        showOutputMessage($shell, "Select one supplier before downloading RFQ PDF.", "error");
        return;
      }
      showOutputMessage($shell, "Preparing RFQ PDF...", "");
      window.open(outputPdfUrl({ doctype: "Request for Quotation", name: form.name, supplier }), "_blank", "noopener");
    });
  }

  function formMarkup(form) {
    const header = form.header || {};
    return `
      <section class="erpw-child-card erpw-managed-rfq-card" data-erpw-managed-rfq-form>
        <div class="erpw-managed-rfq-section-head">
          <div>
            <div class="erpw-managed-rfq-section-title">RFQ details</div>
            <div class="erpw-managed-rfq-section-note">New item lines use the default date unless changed.</div>
          </div>
        </div>
        <div class="erpw-managed-rfq-grid">
          <div class="erpw-managed-rfq-field"><label>Transaction Date</label><input class="erpw-managed-rfq-input" data-field="transaction_date" type="date" value="${escapeHtml(header.transaction_date || "")}"></div>
          <div class="erpw-managed-rfq-field"><label>Default Required By</label><input class="erpw-managed-rfq-input" data-field="schedule_date" type="date" value="${escapeHtml(header.schedule_date || "")}"></div>
        </div>
        <div class="erpw-managed-rfq-lines-head">
          <div>
            <div class="erpw-managed-rfq-lines-title">Suppliers</div>
            <div class="erpw-managed-rfq-lines-note">Select suppliers for sourcing review.</div>
          </div>
        </div>
        <div class="erpw-managed-rfq-table-wrap">
          <table class="erpw-managed-rfq-supplier-table">
            <thead><tr><th>Supplier</th><th class="row-action"></th></tr></thead>
            <tbody>
              ${(form.suppliers || []).map((row, index) => `
                <tr data-supplier-row-index="${index}">
                  <td class="erpw-managed-rfq-link-cell" data-label="Supplier"><input class="supplier-link" data-supplier-field="supplier" value="${escapeHtml(row.supplier || "")}" placeholder="Select supplier" autocomplete="off"></td>
                  <td class="row-action"><button type="button" class="erpw-managed-rfq-row-button" data-remove-supplier-row="${index}">Remove</button></td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
        <div class="erpw-managed-rfq-lines-footer">
          <button type="button" class="erpw-managed-rfq-add-line" data-add-supplier-row>Add supplier</button>
        </div>
        <div class="erpw-managed-rfq-lines-head">
          <div>
            <div class="erpw-managed-rfq-lines-title">Items</div>
            <div class="erpw-managed-rfq-lines-note">Select items, quantities, line dates, and optional warehouse.</div>
          </div>
        </div>
        <div class="erpw-managed-rfq-table-wrap">
          <table class="erpw-managed-rfq-table">
            <thead><tr><th>Item</th><th class="qty">Qty</th><th class="date">Line Required By</th><th>Warehouse</th><th class="uom">UOM</th><th class="row-action">Action</th></tr></thead>
            <tbody>
              ${(form.items || []).map((row, index) => `
                <tr data-row-index="${index}">
                  <td class="erpw-managed-rfq-link-cell erpw-managed-rfq-line-item" data-label="Item"><input class="item-link" data-row-field="item_code" value="${escapeHtml(row.item_code || "")}" placeholder="Select item" autocomplete="off"></td>
                  <td class="erpw-managed-rfq-line-qty" data-label="Qty"><input data-row-field="qty" type="number" min="0" step="0.01" value="${escapeHtml(row.qty || "")}"></td>
                  <td class="erpw-managed-rfq-line-date" data-label="Line Required By"><input data-row-field="schedule_date" data-schedule-mode="${escapeHtml(row._schedule_date_mode || "inherited")}" type="date" value="${escapeHtml(row.schedule_date || header.schedule_date || "")}"></td>
                  <td class="erpw-managed-rfq-link-cell erpw-managed-rfq-line-warehouse" data-label="Warehouse"><input class="warehouse-link" data-row-field="warehouse" value="${escapeHtml(row.warehouse || "")}" placeholder="Optional warehouse" autocomplete="off"></td>
                  <td class="uom erpw-managed-rfq-line-uom" data-label="UOM"><span class="erpw-managed-rfq-uom-value" data-uom-display>${escapeHtml(row.uom || "Derived")}</span><input type="hidden" data-row-field="uom" value="${escapeHtml(row.uom || "")}"></td>
                  <td class="row-action erpw-managed-rfq-line-action"><button type="button" class="erpw-managed-rfq-row-button" data-remove-row="${index}">Remove</button></td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
        <div class="erpw-managed-rfq-lines-footer">
          <button type="button" class="erpw-managed-rfq-add-line" data-add-row>Add line</button>
          <div class="erpw-managed-rfq-message" data-managed-rfq-message></div>
        </div>
      </section>
    `;
  }

  function collectForm($shell, viewState) {
    const form = viewState.form || stateForm(viewState.payload);
    form.header.transaction_date = $shell.find('[data-field="transaction_date"]').val() || "";
    form.header.schedule_date = $shell.find('[data-field="schedule_date"]').val() || "";
    $shell.find("tbody tr[data-supplier-row-index]").each(function () {
      const index = Number($(this).attr("data-supplier-row-index"));
      const row = form.suppliers[index] || {};
      $(this).find("[data-supplier-field]").each(function () {
        row[$(this).attr("data-supplier-field")] = $(this).val();
      });
      form.suppliers[index] = row;
    });
    $shell.find("tbody tr[data-row-index]").each(function () {
      const index = Number($(this).attr("data-row-index"));
      const row = form.items[index] || {};
      $(this).find("[data-row-field]").each(function () {
        const key = $(this).attr("data-row-field");
        row[key] = $(this).val();
        if (key === "schedule_date") row._schedule_date_mode = $(this).attr("data-schedule-mode") || row._schedule_date_mode || "inherited";
      });
      form.items[index] = row;
    });
    viewState.form = form;
    return form;
  }

  function setMessage($shell, message, tone) {
    $shell.find("[data-managed-rfq-message]").text(message || "").toggleClass("error", tone === "error");
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

  function saveRfq(viewState) {
    const form = collectForm(viewState.$shell, viewState);
    setMessage(viewState.$shell, "Recording RFQ...", "");
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
        setMessage(viewState.$shell, payload.message || "RFQ recorded for sourcing review.", "");
        return;
      }
      renderPayload(viewState, payload);
    }).catch((error) => {
      setMessage(viewState.$shell, error && error.message ? error.message : "RFQ could not be saved.", "error");
    });
  }

  function bindForm($shell, viewState) {
    $shell.find("[data-field], [data-row-field], [data-supplier-field]").off("input.rfqform change.rfqform");
    $shell.find('[data-field="schedule_date"]').on("input.rfqform change.rfqform", function () {
      const previousDefaultDate = (viewState.form && viewState.form.header && viewState.form.header.schedule_date) || "";
      collectForm($shell, viewState);
      syncInheritedLineDates($shell, viewState, $(this).val() || "", previousDefaultDate);
      collectForm($shell, viewState);
    });
    $shell.find('[data-row-field="schedule_date"]').on("input.rfqform change.rfqform", function () {
      $(this).attr("data-schedule-mode", "manual");
      collectForm($shell, viewState);
    });
    $shell.find('[data-field]:not([data-field="schedule_date"]), [data-row-field]:not([data-row-field="schedule_date"]), [data-supplier-field]').on("input.rfqform change.rfqform", () => collectForm($shell, viewState));
    $shell.find("[data-add-supplier-row]").off("click.rfqform").on("click.rfqform", () => {
      collectForm($shell, viewState);
      viewState.form.suppliers.push({ supplier: "" });
      renderPayload(viewState);
    });
    $shell.find("[data-remove-supplier-row]").off("click.rfqform").on("click.rfqform", function () {
      collectForm($shell, viewState);
      const index = Number($(this).attr("data-remove-supplier-row"));
      viewState.form.suppliers.splice(index, 1);
      if (!viewState.form.suppliers.length) viewState.form.suppliers.push({ supplier: "" });
      renderPayload(viewState);
    });
    $shell.find("[data-add-row]").off("click.rfqform").on("click.rfqform", () => {
      collectForm($shell, viewState);
      const headerDate = viewState.form.header.schedule_date || "";
      viewState.form.items.push({ item_code: "", qty: 1, schedule_date: headerDate, warehouse: "", uom: "", _schedule_date_mode: "inherited" });
      renderPayload(viewState);
    });
    $shell.find("[data-remove-row]").off("click.rfqform").on("click.rfqform", function () {
      collectForm($shell, viewState);
      const index = Number($(this).attr("data-remove-row"));
      viewState.form.items.splice(index, 1);
      if (!viewState.form.items.length) viewState.form.items.push({ item_code: "", qty: 1, schedule_date: viewState.form.header.schedule_date || "", warehouse: "", uom: "", _schedule_date_mode: "inherited" });
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
    $(window).off("resize.managedRfqSuggest scroll.managedRfqSuggest");
    $(document).off("scroll.managedRfqSuggest");
    $(".erpw-managed-rfq-suggestions").remove();
  }

  function positionSuggestions($menu, input) {
    const rect = input.getBoundingClientRect();
    const viewportWidth = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
    const viewportHeight = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);
    const width = Math.min(Math.max(rect.width, 300), Math.max(220, viewportWidth - rect.left - 12));
    const availableBelow = Math.max(40, viewportHeight - rect.bottom - 16);
    const availableAbove = Math.max(40, rect.top - 16);
    const naturalHeight = Math.min(240, Math.max(40, $menu.get(0) ? $menu.get(0).scrollHeight : 40));
    const placeAbove = naturalHeight + 6 > availableBelow && availableAbove > availableBelow;
    const maxHeight = Math.min(240, placeAbove ? availableAbove : availableBelow);
    const menuHeight = Math.min(naturalHeight, maxHeight);
    const top = placeAbove ? Math.max(12, rect.top - menuHeight - 6) : rect.bottom + 6;
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
      const $menu = $('<div class="erpw-managed-rfq-suggestions" role="listbox"></div>');
      rows.slice(0, 8).forEach((row) => {
        const value = row.value || row.name || row.label || row;
        const label = row.label || row.description || value;
        $('<button type="button" class="erpw-managed-rfq-suggestion" role="option"></button>').text(label).on("mousedown", (event) => {
          event.preventDefault();
          $input.val(value);
          collectForm($shell, viewState);
          removeSuggestions();
          if (doctype === "Item") updateItemDefaults($shell, input, viewState);
        }).appendTo($menu);
      });
      $menu.appendTo(document.body);
      positionSuggestions($menu, input);
      $(window).off("resize.managedRfqSuggest scroll.managedRfqSuggest").on("resize.managedRfqSuggest scroll.managedRfqSuggest", () => positionSuggestions($menu, input));
      $(document).off("scroll.managedRfqSuggest").on("scroll.managedRfqSuggest", () => positionSuggestions($menu, input));
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
      state: { kind: "loading", title: "Loading RFQ form", detail: "Reading sourcing context." },
      summary: { kicker: "Request for Quotation", title: "New RFQ", subtitle: "Prepare supplier sourcing request before sending.", chips: [{ label: "New RFQ" }, { label: "Sourcing" }] },
      controls: { actions: [] },
      form: { header: { transaction_date: "", schedule_date: "", company: "", subject: "Request for Quotation", message_for_supplier: "Please supply the specified items at the best possible rates" }, suppliers: [{ supplier: "" }], items: [{ item_code: "", qty: 1, schedule_date: "", warehouse: "", uom: "" }] },
      action_targets: {},
    };
  }

  function renderState($shell, payload) {
    const state = payload && payload.state ? payload.state : {};
    return `
      <section class="erpw-child-card erpw-list-results">
        <div class="erpw-list-state ${escapeHtml(state.kind || "unavailable")}">
          <div class="erpw-list-state-title">${escapeHtml(state.title || "RFQ form unavailable")}</div>
          <div class="erpw-list-state-detail">${escapeHtml(state.detail || "This managed RFQ form cannot be loaded right now.")}</div>
        </div>
      </section>
    `;
  }

  function renderPayload(viewState, overridePayload) {
    removeSuggestions();
    const payload = overridePayload || viewState.payload || loadingPayload();
    const form = overridePayload && overridePayload.state && overridePayload.state.kind !== "ready" ? viewState.form || stateForm(viewState.payload) : viewState.form || stateForm(payload);
    const output = outputCardMarkup(form, viewState.outputContext);
    const extra = payload.state && payload.state.kind && payload.state.kind !== "ready" && payload.state.kind !== "loading" ? renderState(viewState.$shell, payload) : formMarkup(form) + output;
    shellContent().renderShellContent(viewState.$shell, {
      summary: payload.summary || loadingPayload().summary,
      actions: actionConfig(payload, viewState),
      actionLayout: { mode: "toolbar" },
      extraSectionsHtml: extra,
    });
    viewState.$shell.attr("data-erpw-managed-rfq-state", payload.state && payload.state.kind ? payload.state.kind : "ready");
    if (payload.state && payload.state.kind === "ready") {
      bindForm(viewState.$shell, viewState);
      bindOutputCard(viewState.$shell, viewState);
    }
  }

  function loadRoute(viewState, options) {
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
      renderPayload(viewState, { state: { kind: "error", title: "RFQ form failed", detail: error && error.message ? error.message : "The managed form could not load." } });
    });
  }

  function render(wrapper) {
    cleanupRouteShells();
    ensureStyles();
    const page = makePage(wrapper);
    cleanupManagedPageChrome(wrapper);
    const host = ensureHost(page, wrapper);
    const viewState = { page, wrapper, $host: host.$host, $shell: host.$shell, payload: loadingPayload(), form: null };
    wrapper.__erpwManagedRfqForm = viewState;
    pruneRouteShells(host.$host.get(0));
    ensureRuntime().then(() => loadRoute(viewState));
  }

  function show(wrapper) {
    const state = wrapper && wrapper.__erpwManagedRfqForm;
    if (state && state.$shell && state.$shell.length && isAttached(state.$host) && isAttached(state.$shell)) {
      cleanupManagedPageChrome(wrapper);
      pruneRouteShells(state.$host.get(0));
      loadRoute(state);
      return;
    }
    render(wrapper);
  }

  window.erpWorkspaceUiProcurementRfqForm = Object.assign(window.erpWorkspaceUiProcurementRfqForm || {}, {
    render,
    show,
  });
})();
