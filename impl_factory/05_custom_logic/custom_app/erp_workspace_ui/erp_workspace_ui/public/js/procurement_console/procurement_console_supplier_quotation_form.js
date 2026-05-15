/* global frappe, $ */

(function () {
  const workspaceRegistry = window.erpWorkspaceUiWorkspaceRegistry || {};
  const procurementWorkspace = typeof workspaceRegistry.procurement === "function" ? workspaceRegistry.procurement() : null;
  const procurementRoutes = procurementWorkspace && procurementWorkspace.routes ? procurementWorkspace.routes : {};
  const procurementMethods = procurementWorkspace && procurementWorkspace.methods ? procurementWorkspace.methods : {};
  const PAGE_KEY = procurementRoutes.supplierQuotationForm || "procurement-console-supplier-quotation-form";
  const WORKLIST_ROUTE = procurementRoutes.worklist || "procurement-console-worklist";
  const CONTEXT_METHOD = procurementMethods.managedSupplierQuotationContext || "erp_workspace_ui.procurement_console.managed_supplier_quotation.get_managed_supplier_quotation_context";
  const SAVE_METHOD = procurementMethods.managedSupplierQuotationSave || "erp_workspace_ui.procurement_console.managed_supplier_quotation.save_managed_supplier_quotation_draft";
  const ITEM_DEFAULTS_METHOD = procurementMethods.managedSupplierQuotationItemDefaults || "erp_workspace_ui.procurement_console.managed_supplier_quotation.get_managed_supplier_quotation_item_defaults";
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
    if (document.getElementById("erpw-managed-sq-form-style")) return;
    const style = document.createElement("style");
    style.id = "erpw-managed-sq-form-style";
    style.textContent = `
      .erpw-managed-sq-page { padding-bottom: 24px; }
      .erpw-managed-sq-shell { display: grid; gap: 10px; max-width: 1220px; margin: 0 auto; }
      .erpw-managed-sq-shell .erpw-child-summary { min-height: 0; padding: 12px 16px; border-radius: 14px; border: 1px solid #dbe6f2; background: #ffffff; box-shadow: inset 0 1px 0 rgba(255,255,255,0.98), 0 8px 18px rgba(15,23,42,0.027); }
      .erpw-managed-sq-shell .erpw-child-summary-copy { min-width: 0; background: transparent; }
      .erpw-managed-sq-shell .erpw-child-summary-facts { display: none; padding: 0; border: 0; }
      .erpw-managed-sq-shell .erpw-child-summary-top { align-items: center; gap: 12px; }
      .erpw-managed-sq-shell .erpw-child-kicker { color: #0f766e; font-size: 10px; letter-spacing: 0.09em; }
      .erpw-managed-sq-shell .erpw-child-title { font-size: 20px; line-height: 1.12; letter-spacing: 0; margin-top: 3px; }
      .erpw-managed-sq-shell .erpw-child-subtitle { max-width: 620px; margin-top: 4px; font-size: 12.5px; line-height: 1.32; color: #334155; }
      .erpw-managed-sq-shell .erpw-child-chip-row-header { align-self: center; }
      .erpw-managed-sq-shell .erpw-child-chip { min-height: 25px; padding: 0.22rem 0.56rem; }
      .erpw-managed-sq-shell .erpw-child-actions-toolbar { margin-top: -4px; padding: 0 2px; border: 0; background: transparent; box-shadow: none; }
      .erpw-managed-sq-shell .erpw-child-toolbar-actions { justify-content: flex-start; flex-wrap: wrap; gap: 8px; }
      .erpw-managed-sq-shell .erpw-child-toolbar-action { min-height: 34px; border-radius: 10px; }
      .erpw-managed-sq-card { display: grid; gap: 12px; padding: 15px 18px 18px; overflow: visible; }
      .erpw-managed-sq-section-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; }
      .erpw-managed-sq-section-title { margin-top: 3px; font-size: 15.5px; line-height: 1.25; font-weight: 790; color: #0f172a; }
      .erpw-managed-sq-section-note { margin-top: 3px; max-width: 620px; font-size: 12.5px; line-height: 1.38; color: #475569; }
      .erpw-managed-sq-grid { display: grid; grid-template-columns: minmax(260px, 380px) repeat(2, minmax(160px, 190px)); gap: 12px; align-items: end; }
      .erpw-managed-sq-field { display: grid; gap: 6px; min-width: 0; }
      .erpw-managed-sq-field label { font-size: 10.5px; line-height: 1.2; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; margin: 0; }
      .erpw-managed-sq-input, .erpw-managed-sq-table input { width: 100%; min-height: 37px; border: 1px solid #d5e2ef; border-radius: 11px; padding: 0 10px; font-size: 13px; color: #0f172a; background: #fff; box-shadow: inset 0 1px 0 rgba(255,255,255,0.95); box-sizing: border-box; }
      .erpw-managed-sq-input:focus, .erpw-managed-sq-table input:focus { outline: none; border-color: #8fb0d3; box-shadow: 0 0 0 3px rgba(18,54,95,0.08); }
      .erpw-managed-sq-lines-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; padding-top: 2px; }
      .erpw-managed-sq-lines-title { font-size: 14px; line-height: 1.25; font-weight: 790; color: #0f172a; }
      .erpw-managed-sq-lines-note { margin-top: 3px; color: #64748b; font-size: 12.5px; line-height: 1.36; }
      .erpw-managed-sq-table-wrap { overflow: visible; border: 0; border-radius: 0; background: transparent; }
      .erpw-managed-sq-table, .erpw-managed-sq-table tbody, .erpw-managed-sq-table tr, .erpw-managed-sq-table td { display: block; box-sizing: border-box; }
      .erpw-managed-sq-table { width: 100%; min-width: 0; border-collapse: separate; border-spacing: 0; }
      .erpw-managed-sq-table thead { display: block; margin: 0 0 6px; }
      .erpw-managed-sq-table thead tr { display: grid; grid-template-columns: minmax(260px, 1.4fr) 82px 112px 76px 118px 66px; gap: 10px; align-items: end; padding: 0 12px; border: 0; background: transparent; box-shadow: none; }
      .erpw-managed-sq-table th { display: block; min-width: 0; padding: 0; border: 0; color: #64748b; font-size: 10px; line-height: 1.15; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; text-align: left; white-space: nowrap; }
      .erpw-managed-sq-table tbody { display: grid; gap: 10px; }
      .erpw-managed-sq-table tbody tr { display: grid; grid-template-columns: minmax(260px, 1.4fr) 82px 112px 76px 118px 66px; gap: 10px; align-items: end; padding: 12px; border: 1px solid #dbe6f2; border-radius: 14px; background: #ffffff; box-shadow: inset 0 1px 0 rgba(255,255,255,0.98), 0 7px 16px rgba(15,23,42,0.03); }
      .erpw-managed-sq-table td { min-width: 0; padding: 0; border: 0; display: grid; gap: 6px; vertical-align: top; }
      .erpw-managed-sq-table td::before { content: ""; display: none; }
      .erpw-managed-sq-table td.row-action { align-self: end; }
      .erpw-managed-sq-table td.row-action::before { content: ""; display: none; }
      .erpw-managed-sq-uom-value, .erpw-managed-sq-amount-value { display: inline-flex; align-items: center; justify-content: center; min-width: 70px; min-height: 37px; max-width: 100%; border-radius: 999px; border: 1px solid #dbe6f2; background: #f8fafc; color: #334155; padding: 0 11px; font-size: 13px; line-height: 1; font-weight: 650; letter-spacing: 0; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; white-space: nowrap; overflow: visible; text-overflow: clip; box-sizing: border-box; }
      .erpw-managed-sq-amount-value { justify-content: flex-end; min-width: 92px; border-radius: 11px; font-variant-numeric: tabular-nums; }
      .erpw-managed-sq-row-button, .erpw-managed-sq-add-line { min-height: 34px; border: 1px solid #d5e2ef; border-radius: 10px; background: #fff; color: #12365f; font-weight: 740; font-size: 12px; padding: 0 10px; }
      .erpw-managed-sq-row-button { width: 100%; max-width: 62px; padding: 0 8px; color: #475569; }
      .erpw-managed-sq-row-button:hover, .erpw-managed-sq-add-line:hover { border-color: #9db7d2; background: #f8fbff; color: #12365f; }
      .erpw-managed-sq-lines-footer { display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap; }
      .erpw-managed-sq-add-line { justify-self: start; }
      .erpw-managed-sq-message { min-height: 20px; font-size: 12.5px; color: #64748b; }
      .erpw-managed-sq-message.error { color: #b42318; }
      .erpw-managed-sq-suggestions { position: fixed; z-index: 1200; min-width: 0; max-height: 240px; overflow: auto; margin: 0; border: 1px solid #d5e2ef; border-radius: 12px; background: #fff; box-shadow: 0 18px 40px rgba(15,23,42,0.18); }
      .erpw-managed-sq-suggestion { display: block; width: 100%; text-align: left; border: 0; background: transparent; padding: 9px 11px; font-size: 13px; color: #0f172a; }
      .erpw-managed-sq-suggestion:hover, .erpw-managed-sq-suggestion:focus-visible { background: #f1f5f9; outline: none; }
      .erpw-managed-sq-link-cell { position: relative; }
      @media (max-width: 1180px) {
        .erpw-managed-sq-grid { grid-template-columns: minmax(260px, 1fr) repeat(2, minmax(150px, 180px)); }
        .erpw-managed-sq-table thead tr, .erpw-managed-sq-table tbody tr { grid-template-columns: minmax(230px, 1fr) 76px 96px 74px 104px 62px; grid-template-areas: "item qty rate uom amount action"; gap: 8px; align-items: end; }
        .erpw-managed-sq-table thead tr { padding: 0 10px; }
        .erpw-managed-sq-table tbody tr { padding: 10px; }
        .erpw-managed-sq-table th:nth-child(1) { grid-area: item; }
        .erpw-managed-sq-table th.qty { grid-area: qty; }
        .erpw-managed-sq-table th.rate { grid-area: rate; }
        .erpw-managed-sq-table th.uom { grid-area: uom; }
        .erpw-managed-sq-table th.amount { grid-area: amount; }
        .erpw-managed-sq-table th.row-action { grid-area: action; }
        .erpw-managed-sq-line-item { grid-area: item; }
        .erpw-managed-sq-line-qty { grid-area: qty; }
        .erpw-managed-sq-line-rate { grid-area: rate; }
        .erpw-managed-sq-line-uom { grid-area: uom; }
        .erpw-managed-sq-line-amount { grid-area: amount; max-width: none; }
        .erpw-managed-sq-line-action { grid-area: action; }
        .erpw-managed-sq-amount-value { min-width: 0; width: 100%; }
        .erpw-managed-sq-row-button { max-width: 60px; padding: 0 6px; font-size: 11.5px; }
      }
      @media (max-width: 720px) {
        .erpw-managed-sq-grid { grid-template-columns: 1fr; }
        .erpw-managed-sq-shell .erpw-child-summary-top { display: grid; }
        .erpw-managed-sq-table thead { display: none; }
        .erpw-managed-sq-table tbody tr { grid-template-columns: 1fr 86px 74px; grid-template-areas: "item item item" "qty uom action" "rate rate rate" "amount amount amount"; }
        .erpw-managed-sq-table td::before { content: attr(data-label); display: block; font-size: 10px; line-height: 1.15; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; }
        .erpw-managed-sq-line-amount { max-width: none; }
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
    frappe.set_route(WORKLIST_ROUTE, String(queueKey || "supplier_quotation_directory").replace(/_/g, "-"));
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
      return frappe.ui.make_app_page({ parent: wrapper, title: "Supplier Quotation Form", single_column: true });
    } catch (error) {
      const $parent = $(wrapper);
      $parent.empty().append('<main class="layout-main-section erpw-direct-child-body"></main>');
      return { body: $parent.find(".erpw-direct-child-body").first(), set_title(title) { document.title = title || "Supplier Quotation Form"; } };
    }
  }

  function ensureHost(page, wrapper) {
    const $parent = page && page.body ? $(page.body) : $(wrapper);
    let $host = $parent.children(".erpw-managed-sq-page").first();
    if (!$host.length) {
      $host = $('<section class="erpw-managed-sq-page"></section>');
      $parent.empty().append($host);
    }
    let $shell = $host.children(".erpw-child-shell.erpw-child-detail-shell.erpw-managed-sq-shell").first();
    if (!$shell.length) {
      $shell = $('<div class="erpw-child-shell erpw-child-detail-shell erpw-managed-sq-shell"></div>');
      $host.append($shell);
    }
    return { $host, $shell };
  }

  function stateForm(payload) {
    const form = payload && payload.form ? payload.form : {};
    const header = form.header || {};
    const items = Array.isArray(form.items) && form.items.length ? form.items : [{ item_code: "", qty: 1, rate: "", uom: "", amount: "" }];
    return {
      name: form.name || "new",
      header: {
        supplier: header.supplier || "",
        transaction_date: header.transaction_date || "",
        valid_till: header.valid_till || "",
        company: header.company || "",
        currency: header.currency || "",
        conversion_rate: header.conversion_rate || 1,
      },
      items: items.map((row) => {
        const current = Object.assign({ item_code: "", qty: 1, rate: "", uom: "", amount: "" }, row || {});
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
      icon: action.key === "save_supplier_quotation" ? "check" : action.key === "open_erp_form" ? "external" : action.key === "back_to_supplier_quotations" ? "arrow-left" : "refresh",
      handler() {
        if (action.key === "save_supplier_quotation") return saveSupplierQuotation(viewState);
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

  function formMarkup(form) {
    const header = form.header || {};
    return `
      <section class="erpw-child-card erpw-managed-sq-card" data-erpw-managed-sq-form>
        <div class="erpw-managed-sq-section-head">
          <div>
            <div class="erpw-managed-sq-section-title">Quotation details</div>
            <div class="erpw-managed-sq-section-note">Capture supplier, validity, and quoted rates for comparison.</div>
          </div>
        </div>
        <div class="erpw-managed-sq-grid">
          <div class="erpw-managed-sq-field erpw-managed-sq-link-cell"><label>Supplier</label><input class="erpw-managed-sq-input supplier-link" data-field="supplier" value="${escapeHtml(header.supplier || "")}" placeholder="Select supplier" autocomplete="off"></div>
          <div class="erpw-managed-sq-field"><label>Transaction Date</label><input class="erpw-managed-sq-input" data-field="transaction_date" type="date" value="${escapeHtml(header.transaction_date || "")}"></div>
          <div class="erpw-managed-sq-field"><label>Valid Till</label><input class="erpw-managed-sq-input" data-field="valid_till" type="date" value="${escapeHtml(header.valid_till || "")}"></div>
        </div>
        <div class="erpw-managed-sq-lines-head">
          <div>
            <div class="erpw-managed-sq-lines-title">Items</div>
            <div class="erpw-managed-sq-lines-note">Enter quoted quantities and buyer-recorded rates.</div>
          </div>
        </div>
        <div class="erpw-managed-sq-table-wrap">
          <table class="erpw-managed-sq-table">
            <thead><tr><th>Item</th><th class="qty">Qty</th><th class="rate">Rate</th><th class="uom">UOM</th><th class="amount">Amount</th><th class="row-action">Action</th></tr></thead>
            <tbody>
              ${(form.items || []).map((row, index) => `
                <tr data-row-index="${index}">
                  <td class="erpw-managed-sq-link-cell erpw-managed-sq-line-item" data-label="Item"><input class="item-link" data-row-field="item_code" value="${escapeHtml(row.item_code || "")}" placeholder="Select item" autocomplete="off"></td>
                  <td class="erpw-managed-sq-line-qty" data-label="Qty"><input data-row-field="qty" type="number" min="0" step="0.01" value="${escapeHtml(row.qty || "")}"></td>
                  <td class="erpw-managed-sq-line-rate" data-label="Rate"><input data-row-field="rate" type="number" min="0" step="0.01" value="${escapeHtml(row.rate || "")}"></td>
                  <td class="uom erpw-managed-sq-line-uom" data-label="UOM"><span class="erpw-managed-sq-uom-value" data-uom-display>${escapeHtml(row.uom || "Derived")}</span><input type="hidden" data-row-field="uom" value="${escapeHtml(row.uom || "")}"></td>
                  <td class="amount erpw-managed-sq-line-amount" data-label="Amount"><span class="erpw-managed-sq-amount-value" data-amount-display>${escapeHtml(formatAmount(row.amount || calcAmount(row)))}</span><input type="hidden" data-row-field="amount" value="${escapeHtml(row.amount || calcAmount(row))}"></td>
                  <td class="row-action erpw-managed-sq-line-action"><button type="button" class="erpw-managed-sq-row-button" data-remove-row="${index}">Remove</button></td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
        <div class="erpw-managed-sq-lines-footer">
          <button type="button" class="erpw-managed-sq-add-line" data-add-row>Add line</button>
          <div class="erpw-managed-sq-message" data-managed-sq-message></div>
        </div>
      </section>
    `;
  }

  function collectForm($shell, viewState) {
    const form = viewState.form || stateForm(viewState.payload);
    form.header.supplier = $shell.find('[data-field="supplier"]').val() || "";
    form.header.transaction_date = $shell.find('[data-field="transaction_date"]').val() || "";
    form.header.valid_till = $shell.find('[data-field="valid_till"]').val() || "";
    $shell.find("tbody tr[data-row-index]").each(function () {
      const index = Number($(this).attr("data-row-index"));
      const row = form.items[index] || {};
      $(this).find("[data-row-field]").each(function () {
        row[$(this).attr("data-row-field")] = $(this).val();
      });
      row.amount = calcAmount(row);
      form.items[index] = row;
    });
    viewState.form = form;
    updateAmounts($shell, viewState);
    return form;
  }

  function setMessage($shell, message, tone) {
    $shell.find("[data-managed-sq-message]").text(message || "").toggleClass("error", tone === "error");
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

  function saveSupplierQuotation(viewState) {
    const form = collectForm(viewState.$shell, viewState);
    setMessage(viewState.$shell, "Recording quotation...", "");
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
        setMessage(viewState.$shell, payload.message || "Quotation recorded for buyer comparison.", "");
        return;
      }
      renderPayload(viewState, payload);
    }).catch((error) => {
      setMessage(viewState.$shell, error && error.message ? error.message : "Supplier Quotation could not be saved.", "error");
    });
  }

  function bindForm($shell, viewState) {
    $shell.find("[data-field], [data-row-field]").off("input.sqform change.sqform");
    $shell.find("[data-field], [data-row-field]").on("input.sqform change.sqform", () => collectForm($shell, viewState));
    $shell.find('[data-row-field="qty"], [data-row-field="rate"]').on("input.sqform change.sqform", () => {
      collectForm($shell, viewState);
      updateAmounts($shell, viewState);
    });
    $shell.find("[data-add-row]").off("click.sqform").on("click.sqform", () => {
      collectForm($shell, viewState);
      viewState.form.items.push({ item_code: "", qty: 1, rate: "", uom: "", amount: "" });
      renderPayload(viewState);
    });
    $shell.find("[data-remove-row]").off("click.sqform").on("click.sqform", function () {
      collectForm($shell, viewState);
      const index = Number($(this).attr("data-remove-row"));
      viewState.form.items.splice(index, 1);
      if (!viewState.form.items.length) viewState.form.items.push({ item_code: "", qty: 1, rate: "", uom: "", amount: "" });
      renderPayload(viewState);
    });
    bindLinkField($shell, viewState, ".supplier-link", "Supplier");
    bindLinkField($shell, viewState, ".item-link", "Item");
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
    $(window).off("resize.managedSqSuggest scroll.managedSqSuggest");
    $(document).off("scroll.managedSqSuggest");
    $(".erpw-managed-sq-suggestions").remove();
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
      const $menu = $('<div class="erpw-managed-sq-suggestions" role="listbox"></div>');
      rows.slice(0, 8).forEach((row) => {
        const value = row.value || row.name || row.label || row;
        const label = row.label || row.description || value;
        $('<button type="button" class="erpw-managed-sq-suggestion" role="option"></button>').text(label).on("mousedown", (event) => {
          event.preventDefault();
          $input.val(value);
          collectForm($shell, viewState);
          removeSuggestions();
          if (doctype === "Item") updateItemDefaults($shell, input, viewState);
        }).appendTo($menu);
      });
      $menu.appendTo(document.body);
      positionSuggestions($menu, input);
      $(window).off("resize.managedSqSuggest scroll.managedSqSuggest").on("resize.managedSqSuggest scroll.managedSqSuggest", () => positionSuggestions($menu, input));
      $(document).off("scroll.managedSqSuggest").on("scroll.managedSqSuggest", () => positionSuggestions($menu, input));
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
      state: { kind: "loading", title: "Loading Supplier Quotation form", detail: "Reading quotation context." },
      summary: { kicker: "Supplier Quotation", title: "New Supplier Quotation", subtitle: "Record supplier offer details for buyer comparison.", chips: [{ label: "New Quotation" }, { label: "Buying offer" }] },
      controls: { actions: [] },
      form: { header: { supplier: "", transaction_date: "", valid_till: "", company: "", currency: "", conversion_rate: 1 }, items: [{ item_code: "", qty: 1, rate: "", uom: "", amount: "" }] },
      action_targets: {},
    };
  }

  function renderState(payload) {
    const state = payload && payload.state ? payload.state : {};
    return `
      <section class="erpw-child-card erpw-list-results">
        <div class="erpw-list-state ${escapeHtml(state.kind || "unavailable")}">
          <div class="erpw-list-state-title">${escapeHtml(state.title || "Supplier Quotation form unavailable")}</div>
          <div class="erpw-list-state-detail">${escapeHtml(state.detail || "This managed Supplier Quotation form cannot be loaded right now.")}</div>
        </div>
      </section>
    `;
  }

  function renderPayload(viewState, overridePayload) {
    removeSuggestions();
    const payload = overridePayload || viewState.payload || loadingPayload();
    const form = overridePayload && payload.state && payload.state.kind !== "ready" ? viewState.form || stateForm(viewState.payload) : viewState.form || stateForm(payload);
    const extra = payload.state && payload.state.kind && payload.state.kind !== "ready" && payload.state.kind !== "loading" ? renderState(payload) : formMarkup(form);
    shellContent().renderShellContent(viewState.$shell, {
      summary: payload.summary || loadingPayload().summary,
      actions: actionConfig(payload, viewState),
      actionLayout: { mode: "toolbar" },
      extraSectionsHtml: extra,
    });
    viewState.$shell.attr("data-erpw-managed-sq-state", payload.state && payload.state.kind ? payload.state.kind : "ready");
    if (payload.state && payload.state.kind === "ready") bindForm(viewState.$shell, viewState);
  }

  function loadRoute(viewState) {
    const name = resolveName();
    viewState.form = null;
    renderPayload(viewState, loadingPayload());
    return frappe.call({ method: CONTEXT_METHOD, args: { name } }).then((response) => {
      const payload = response && response.message ? response.message : {};
      viewState.payload = payload;
      viewState.form = stateForm(payload);
      renderPayload(viewState);
    }).catch((error) => {
      renderPayload(viewState, { state: { kind: "error", title: "Supplier Quotation form failed", detail: error && error.message ? error.message : "The managed form could not load." } });
    });
  }

  function render(wrapper) {
    cleanupRouteShells();
    ensureStyles();
    const page = makePage(wrapper);
    cleanupManagedPageChrome(wrapper);
    const host = ensureHost(page, wrapper);
    const viewState = { page, wrapper, $host: host.$host, $shell: host.$shell, payload: loadingPayload(), form: null };
    wrapper.__erpwManagedSupplierQuotationForm = viewState;
    pruneRouteShells(host.$host.get(0));
    ensureRuntime().then(() => loadRoute(viewState));
  }

  function show(wrapper) {
    const state = wrapper && wrapper.__erpwManagedSupplierQuotationForm;
    if (state && state.$shell && state.$shell.length && isAttached(state.$host) && isAttached(state.$shell)) {
      cleanupManagedPageChrome(wrapper);
      pruneRouteShells(state.$host.get(0));
      loadRoute(state);
      return;
    }
    render(wrapper);
  }

  window.erpWorkspaceUiProcurementSupplierQuotationForm = Object.assign(window.erpWorkspaceUiProcurementSupplierQuotationForm || {}, {
    render,
    show,
  });
})();
