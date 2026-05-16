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
  const OUTPUT_PREVIEW_METHOD = "erp_workspace_ui.procurement_console.document_output.get_document_print_preview_context";
  const OUTPUT_PDF_METHOD = "erp_workspace_ui.procurement_console.document_output.download_document_pdf";
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

  function ensureReviewOutputStyles() {
    if (document.getElementById("erpw-procurement-review-output-styles")) return;
    const style = document.createElement("style");
    style.id = "erpw-procurement-review-output-styles";
    style.textContent = `
      .erpw-review-output-card { display: grid; gap: 12px; padding: 15px 18px 18px; border: 1px solid #dbe6f2; border-radius: 14px; background: #fff; box-shadow: inset 0 1px 0 rgba(255,255,255,0.98), 0 7px 16px rgba(15,23,42,0.03); }
      .erpw-review-output-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
      .erpw-review-output-title { font-size: 15px; line-height: 1.25; font-weight: 790; color: #0f172a; }
      .erpw-review-output-note { margin-top: 3px; color: #475569; font-size: 12.5px; line-height: 1.36; max-width: 680px; }
      .erpw-review-output-badge { display: inline-flex; min-height: 26px; align-items: center; padding: 0 10px; border-radius: 999px; border: 1px solid #d9eadf; background: #f3faf6; color: #166534; font-size: 12px; font-weight: 760; white-space: nowrap; }
      .erpw-review-output-grid { display: grid; grid-template-columns: minmax(240px, 360px) minmax(0, 1fr); gap: 12px; align-items: end; }
      .erpw-review-output-field { display: grid; gap: 6px; min-width: 0; }
      .erpw-review-output-field label { font-size: 10.5px; line-height: 1.2; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; margin: 0; }
      .erpw-review-output-field select { width: 100%; min-height: 37px; border: 1px solid #d5e2ef; border-radius: 11px; padding: 0 10px; background: #fff; color: #0f172a; font-size: 13px; box-sizing: border-box; }
      .erpw-review-output-actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
      .erpw-review-output-button { min-height: 34px; border: 1px solid #d5e2ef; border-radius: 10px; background: #fff; color: #12365f; font-weight: 740; font-size: 12px; padding: 0 12px; }
      .erpw-review-output-button:hover:not(:disabled) { border-color: #9db7d2; background: #f8fbff; }
      .erpw-review-output-button:disabled { opacity: 0.58; cursor: not-allowed; }
      .erpw-review-output-message { min-height: 18px; color: #64748b; font-size: 12.5px; line-height: 1.36; }
      .erpw-review-output-message.error { color: #b42318; }
      .erpw-review-readiness { display: grid; gap: 10px; padding-top: 2px; }
      .erpw-review-readiness-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
      .erpw-review-readiness-title { font-size: 13.5px; line-height: 1.25; font-weight: 790; color: #0f172a; }
      .erpw-review-readiness-note { margin-top: 2px; max-width: 690px; color: #475569; font-size: 12.3px; line-height: 1.36; }
      .erpw-review-readiness-pill { display: inline-flex; min-height: 25px; align-items: center; padding: 0 9px; border-radius: 999px; border: 1px solid #dbe6f2; background: #f8fafc; color: #334155; font-size: 11.5px; font-weight: 760; white-space: nowrap; }
      .erpw-review-readiness-pill.ready { border-color: #d9eadf; background: #f3faf6; color: #166534; }
      .erpw-review-readiness-pill.missing, .erpw-review-readiness-pill.blocked { border-color: #fde2b8; background: #fff8ed; color: #9a5b13; }
      .erpw-review-readiness-pill.unavailable { border-color: #e7eaf0; background: #f8fafc; color: #475569; }
      .erpw-review-recipient-list { display: grid; gap: 8px; }
      .erpw-review-recipient-row { display: grid; grid-template-columns: minmax(180px, 1.2fr) minmax(150px, 0.9fr) minmax(190px, 1.1fr) auto; gap: 10px; align-items: center; border: 1px solid #edf2f7; border-radius: 12px; padding: 9px 10px; background: #fbfdff; }
      .erpw-review-recipient-cell { min-width: 0; }
      .erpw-review-recipient-label { font-size: 10px; font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase; color: #64748b; }
      .erpw-review-recipient-value { margin-top: 2px; color: #0f172a; font-size: 12.5px; line-height: 1.25; overflow-wrap: anywhere; }
      .erpw-review-send-block { display: flex; align-items: center; justify-content: space-between; gap: 12px; border-top: 1px solid #edf2f7; padding-top: 10px; }
      .erpw-review-send-block-copy { color: #475569; font-size: 12.4px; line-height: 1.35; }
      .erpw-review-send-disabled { min-height: 34px; border: 1px solid #d5e2ef; border-radius: 10px; background: #f8fafc; color: #64748b; font-weight: 750; padding: 0 12px; cursor: not-allowed; white-space: nowrap; }
      .erpw-output-modal-backdrop { position: fixed; inset: 0; z-index: 1400; background: rgba(15,23,42,0.36); display: flex; align-items: center; justify-content: center; padding: 22px; }
      .erpw-output-modal { width: min(980px, 96vw); max-height: min(820px, 92vh); overflow: hidden; display: grid; grid-template-rows: auto 1fr; border-radius: 16px; background: #fff; box-shadow: 0 26px 70px rgba(15,23,42,0.28); border: 1px solid #dbe6f2; }
      .erpw-output-modal-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 12px 14px; border-bottom: 1px solid #e2e8f0; }
      .erpw-output-modal-title { font-weight: 800; color: #0f172a; }
      .erpw-output-modal-close { min-height: 32px; border: 1px solid #d5e2ef; border-radius: 9px; background: #fff; color: #12365f; font-weight: 740; padding: 0 10px; }
      .erpw-output-modal-body { overflow: auto; background: #f8fafc; padding: 16px; }
      @media (max-width: 760px) { .erpw-review-output-grid, .erpw-review-recipient-row { grid-template-columns: 1fr; } .erpw-review-send-block { align-items: flex-start; flex-direction: column; } }
    `;
    document.head.appendChild(style);
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

  function reviewOutputStateClass(status) {
    const value = String(status || "").toLowerCase();
    if (value === "ready") return "ready";
    if (value === "missing_email" || value === "invalid_email") return "missing";
    if (value === "email_unavailable" || value === "unavailable") return "unavailable";
    return "blocked";
  }

  function reviewReadinessRowsMarkup(readiness) {
    const suppliers = readiness && Array.isArray(readiness.suppliers) ? readiness.suppliers : [];
    if (!suppliers.length) return '<div class="erpw-review-output-message">No supplier recipients are available on this RFQ yet.</div>';
    return suppliers.map((row) => `
      <div class="erpw-review-recipient-row" data-rfq-recipient-row data-rfq-recipient-supplier="${escapeHtml(row.supplier || "")}" data-rfq-readiness-status="${escapeHtml(row.readiness_status || "")}">
        <div class="erpw-review-recipient-cell"><div class="erpw-review-recipient-label">Supplier</div><div class="erpw-review-recipient-value">${escapeHtml(row.supplier_name || row.supplier || "Supplier")}</div></div>
        <div class="erpw-review-recipient-cell"><div class="erpw-review-recipient-label">Contact</div><div class="erpw-review-recipient-value">${escapeHtml(row.contact_name || row.contact || "Not selected")}</div></div>
        <div class="erpw-review-recipient-cell"><div class="erpw-review-recipient-label">Email</div><div class="erpw-review-recipient-value">${escapeHtml(row.email || "Missing email")}</div></div>
        <span class="erpw-review-readiness-pill ${reviewOutputStateClass(row.readiness_status)}">${escapeHtml(row.readiness_label || "Send blocked")}</span>
      </div>
    `).join("");
  }

  function reviewReadinessPanelMarkup(context) {
    const readiness = context && context.send_readiness ? context.send_readiness : null;
    const outgoing = readiness && readiness.outgoing_email ? readiness.outgoing_email : {};
    const outgoingAvailable = Boolean(outgoing.available);
    const outgoingLabel = outgoingAvailable ? "Outgoing email ready" : "Email unavailable";
    const outgoingClass = outgoingAvailable ? "ready" : "unavailable";
    const blockReason = readiness && readiness.send_block_reason ? readiness.send_block_reason : "RFQ email send is not enabled yet.";
    const outgoingReason = outgoing.reason || "Supplier recipients and email setup are shown for readiness review.";
    return `
      <div class="erpw-review-readiness" data-rfq-readiness-panel>
        <div class="erpw-review-readiness-top">
          <div>
            <div class="erpw-review-readiness-title">Recipient readiness</div>
            <div class="erpw-review-readiness-note">RFQ email send is not enabled yet. Supplier recipients and email setup are shown for readiness review.</div>
          </div>
          <span class="erpw-review-readiness-pill ${outgoingClass}" data-rfq-outgoing-email-state="${outgoingAvailable ? "available" : "unavailable"}">${escapeHtml(outgoingLabel)}</span>
        </div>
        <div class="erpw-review-recipient-list">${reviewReadinessRowsMarkup(readiness)}</div>
        <div class="erpw-review-send-block">
          <div class="erpw-review-send-block-copy" data-rfq-send-block-reason>${escapeHtml(outgoingReason)} ${escapeHtml(blockReason)}</div>
          <button type="button" class="erpw-review-send-disabled" data-rfq-send-disabled disabled>Send RFQ</button>
        </div>
      </div>
    `;
  }

  function rfqReviewOutputCardMarkup(payload) {
    const page = payload && payload.page ? payload.page : {};
    if (page.key !== "rfq_review" || !page.name) return "";
    const context = payload.output_context || {};
    if (!context || context.state && context.state.kind && context.state.kind !== "ready") {
      const detail = context && context.state && context.state.detail ? context.state.detail : "Supplier communication controls are unavailable for this RFQ.";
      return `<section class="erpw-review-output-card" data-rfq-review-output-card><div class="erpw-review-output-title">Supplier Communication</div><div class="erpw-review-output-message error">${escapeHtml(detail)}</div></section>`;
    }
    const suppliers = Array.isArray(context.suppliers) ? context.suppliers : [];
    const selected = context.selected_supplier || (suppliers.length === 1 ? suppliers[0].supplier : "");
    return `
      <section class="erpw-review-output-card" data-rfq-review-output-card data-managed-rfq-output-card data-document-name="${escapeHtml(page.name)}">
        <div class="erpw-review-output-top">
          <div>
            <div class="erpw-review-output-title">Supplier Communication</div>
            <div class="erpw-review-output-note">Preview and PDF output are supplier-specific. Email send is deferred until a governed RFQ send step exists.</div>
          </div>
          <span class="erpw-review-output-badge">${escapeHtml(context.warning || "Draft / Not sent")}</span>
        </div>
        <div class="erpw-review-output-grid">
          <div class="erpw-review-output-field">
            <label>Supplier context</label>
            <select data-rfq-output-supplier>
              <option value="">Select supplier</option>
              ${suppliers.map((row) => `<option value="${escapeHtml(row.supplier)}" ${row.supplier === selected ? "selected" : ""}>${escapeHtml(row.supplier_name || row.supplier)}</option>`).join("")}
            </select>
          </div>
          <div class="erpw-review-output-actions">
            <button type="button" class="erpw-review-output-button" data-rfq-output-preview>Preview RFQ</button>
            <button type="button" class="erpw-review-output-button" data-rfq-output-download>Download RFQ PDF</button>
          </div>
        </div>
        <div class="erpw-review-output-message" data-rfq-output-message>${escapeHtml(context.send_block_reason || "Email send is deferred.")}</div>
        ${reviewReadinessPanelMarkup(context)}
      </section>
    `;
  }

  function selectedReviewOutputSupplier($shell) {
    return String($shell.find("[data-rfq-output-supplier]").val() || "").trim();
  }

  function outputPdfUrl(args) {
    const params = new URLSearchParams();
    Object.keys(args || {}).forEach((key) => {
      if (args[key] !== undefined && args[key] !== null && String(args[key]).trim() !== "") params.set(key, args[key]);
    });
    return `/api/method/${OUTPUT_PDF_METHOD}?${params.toString()}`;
  }

  function showReviewOutputMessage($shell, message, tone) {
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

  function bindRfqReviewOutputCard(viewState, payload) {
    const page = payload && payload.page ? payload.page : {};
    if (page.key !== "rfq_review" || !page.name) return;
    const $card = viewState.$shell.find("[data-rfq-review-output-card]");
    if (!$card.length) return;
    $card.find("[data-rfq-output-preview]").off("click.output").on("click.output", () => {
      const supplier = selectedReviewOutputSupplier(viewState.$shell);
      if (!supplier) {
        showReviewOutputMessage(viewState.$shell, "Select one supplier before previewing RFQ output.", "error");
        return;
      }
      showReviewOutputMessage(viewState.$shell, "Rendering RFQ preview...", "");
      frappe.call({ method: OUTPUT_PREVIEW_METHOD, args: { doctype: "Request for Quotation", name: page.name, supplier } }).then((response) => {
        const result = response && response.message ? response.message : {};
        if (result.state && result.state.kind === "ready") {
          showPreviewModal(`RFQ Preview - ${supplier}`, result.html || "");
          showReviewOutputMessage(viewState.$shell, result.filename || "RFQ preview ready.", "");
        } else {
          showReviewOutputMessage(viewState.$shell, result.state && result.state.detail ? result.state.detail : "RFQ preview unavailable.", "error");
        }
      });
    });
    $card.find("[data-rfq-output-download]").off("click.output").on("click.output", () => {
      const supplier = selectedReviewOutputSupplier(viewState.$shell);
      if (!supplier) {
        showReviewOutputMessage(viewState.$shell, "Select one supplier before downloading RFQ PDF.", "error");
        return;
      }
      showReviewOutputMessage(viewState.$shell, "Preparing RFQ PDF...", "");
      window.open(outputPdfUrl({ doctype: "Request for Quotation", name: page.name, supplier }), "_blank", "noopener");
    });
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
    return sections.map(renderSection).join("") + rfqReviewOutputCardMarkup(payload);
  }

  function mountPayload(viewState, payload) {
    viewState.payload = payload || {};
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
      bindRfqReviewOutputCard(viewState, payload);
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
    ensureReviewOutputStyles();
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
