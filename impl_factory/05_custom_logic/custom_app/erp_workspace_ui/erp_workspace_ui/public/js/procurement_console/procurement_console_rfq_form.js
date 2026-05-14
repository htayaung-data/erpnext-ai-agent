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
      .erpw-managed-rfq-table thead, .erpw-managed-rfq-supplier-table thead { display: none; }
      .erpw-managed-rfq-table tbody, .erpw-managed-rfq-supplier-table tbody { display: grid; gap: 10px; }
      .erpw-managed-rfq-supplier-table tr { display: grid; grid-template-columns: minmax(280px, 520px) 76px; gap: 10px; align-items: end; padding: 12px; border: 1px solid #dbe6f2; border-radius: 14px; background: #ffffff; box-shadow: inset 0 1px 0 rgba(255,255,255,0.98), 0 7px 16px rgba(15,23,42,0.03); }
      .erpw-managed-rfq-table tr { display: grid; grid-template-columns: minmax(240px, 1.35fr) 78px 128px minmax(180px, 1fr) 76px 66px; gap: 10px; align-items: end; padding: 12px; border: 1px solid #dbe6f2; border-radius: 14px; background: #ffffff; box-shadow: inset 0 1px 0 rgba(255,255,255,0.98), 0 7px 16px rgba(15,23,42,0.03); }
      .erpw-managed-rfq-table td, .erpw-managed-rfq-supplier-table td { min-width: 0; padding: 0; border: 0; display: grid; gap: 6px; vertical-align: top; }
      .erpw-managed-rfq-table td::before, .erpw-managed-rfq-supplier-table td::before { content: attr(data-label); font-size: 10px; line-height: 1.15; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; }
      .erpw-managed-rfq-table td.row-action, .erpw-managed-rfq-supplier-table td.row-action { align-self: end; }
      .erpw-managed-rfq-table td.row-action::before, .erpw-managed-rfq-supplier-table td.row-action::before { content: ""; display: none; }
      .erpw-managed-rfq-uom-value { display: inline-flex; align-items: center; justify-content: center; min-height: 37px; max-width: 100%; border-radius: 999px; border: 1px solid #dbe6f2; background: #f8fafc; color: #334155; padding: 0 9px; font-size: 12px; font-weight: 760; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
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
        .erpw-managed-rfq-table tr { grid-template-columns: minmax(250px, 1fr) 78px 76px 62px; grid-template-areas: "item qty uom action" "date warehouse warehouse warehouse"; align-items: end; }
        .erpw-managed-rfq-line-item { grid-area: item; }
        .erpw-managed-rfq-line-qty { grid-area: qty; }
        .erpw-managed-rfq-line-date { grid-area: date; max-width: 180px; }
        .erpw-managed-rfq-line-warehouse { grid-area: warehouse; }
        .erpw-managed-rfq-line-uom { grid-area: uom; }
        .erpw-managed-rfq-line-action { grid-area: action; }
      }
      @media (max-width: 720px) {
        .erpw-managed-rfq-grid { grid-template-columns: 1fr; }
        .erpw-managed-rfq-supplier-table tr { grid-template-columns: 1fr 66px; }
        .erpw-managed-rfq-shell .erpw-child-summary-top { display: grid; }
        .erpw-managed-rfq-table tr { grid-template-columns: 1fr 86px 74px; grid-template-areas: "item item item" "qty uom action" "date date date" "warehouse warehouse warehouse"; }
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
      items: items.map((row) => Object.assign({ item_code: "", qty: 1, schedule_date: header.schedule_date || "", warehouse: "", uom: "" }, row || {})),
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

  function formMarkup(form) {
    const header = form.header || {};
    return `
      <section class="erpw-child-card erpw-managed-rfq-card" data-erpw-managed-rfq-form>
        <div class="erpw-managed-rfq-section-head">
          <div>
            <div class="erpw-managed-rfq-section-title">RFQ details</div>
            <div class="erpw-managed-rfq-section-note">Set sourcing dates and request lines before supplier communication.</div>
          </div>
        </div>
        <div class="erpw-managed-rfq-grid">
          <div class="erpw-managed-rfq-field"><label>Transaction Date</label><input class="erpw-managed-rfq-input" data-field="transaction_date" type="date" value="${escapeHtml(header.transaction_date || "")}"></div>
          <div class="erpw-managed-rfq-field"><label>Required By</label><input class="erpw-managed-rfq-input" data-field="schedule_date" type="date" value="${escapeHtml(header.schedule_date || "")}"></div>
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
            <div class="erpw-managed-rfq-lines-note">Select items, quantities, required dates, and optional warehouse.</div>
          </div>
        </div>
        <div class="erpw-managed-rfq-table-wrap">
          <table class="erpw-managed-rfq-table">
            <thead><tr><th>Item</th><th class="qty">Qty</th><th class="date">Required By</th><th>Warehouse</th><th class="uom">UOM</th><th class="row-action"></th></tr></thead>
            <tbody>
              ${(form.items || []).map((row, index) => `
                <tr data-row-index="${index}">
                  <td class="erpw-managed-rfq-link-cell erpw-managed-rfq-line-item" data-label="Item"><input class="item-link" data-row-field="item_code" value="${escapeHtml(row.item_code || "")}" placeholder="Select item" autocomplete="off"></td>
                  <td class="erpw-managed-rfq-line-qty" data-label="Qty"><input data-row-field="qty" type="number" min="0" step="0.01" value="${escapeHtml(row.qty || "")}"></td>
                  <td class="erpw-managed-rfq-line-date" data-label="Required By"><input data-row-field="schedule_date" type="date" value="${escapeHtml(row.schedule_date || header.schedule_date || "")}"></td>
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
        row[$(this).attr("data-row-field")] = $(this).val();
      });
      form.items[index] = row;
    });
    viewState.form = form;
    return form;
  }

  function setMessage($shell, message, tone) {
    $shell.find("[data-managed-rfq-message]").text(message || "").toggleClass("error", tone === "error");
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
    $shell.find("[data-field], [data-row-field], [data-supplier-field]").off("input.rfqform change.rfqform").on("input.rfqform change.rfqform", () => collectForm($shell, viewState));
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
      viewState.form.items.push({ item_code: "", qty: 1, schedule_date: headerDate, warehouse: "", uom: "" });
      renderPayload(viewState);
    });
    $shell.find("[data-remove-row]").off("click.rfqform").on("click.rfqform", function () {
      collectForm($shell, viewState);
      const index = Number($(this).attr("data-remove-row"));
      viewState.form.items.splice(index, 1);
      if (!viewState.form.items.length) viewState.form.items.push({ item_code: "", qty: 1, schedule_date: viewState.form.header.schedule_date || "", warehouse: "", uom: "" });
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
    const maxHeight = Math.min(240, Math.max(120, viewportHeight - rect.bottom - 16));
    $menu.css({ left: `${Math.round(rect.left)}px`, top: `${Math.round(rect.bottom + 6)}px`, width: `${Math.round(width)}px`, maxHeight: `${Math.round(maxHeight)}px` });
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
    const extra = payload.state && payload.state.kind && payload.state.kind !== "ready" && payload.state.kind !== "loading" ? renderState(viewState.$shell, payload) : formMarkup(form);
    shellContent().renderShellContent(viewState.$shell, {
      summary: payload.summary || loadingPayload().summary,
      actions: actionConfig(payload, viewState),
      actionLayout: { mode: "toolbar" },
      extraSectionsHtml: extra,
    });
    viewState.$shell.attr("data-erpw-managed-rfq-state", payload.state && payload.state.kind ? payload.state.kind : "ready");
    if (payload.state && payload.state.kind === "ready") bindForm(viewState.$shell, viewState);
  }

  function loadRoute(viewState, options) {
    const name = resolveName();
    viewState.form = null;
    renderPayload(viewState, loadingPayload());
    return frappe.call({ method: CONTEXT_METHOD, args: { name } }).then((response) => {
      const payload = response && response.message ? response.message : {};
      viewState.payload = payload;
      viewState.form = stateForm(payload);
      renderPayload(viewState);
    }).catch((error) => {
      renderPayload(viewState, { state: { kind: "error", title: "RFQ form failed", detail: error && error.message ? error.message : "The managed form could not load." } });
    });
  }

  function render(wrapper) {
    ensureStyles();
    const page = makePage(wrapper);
    const host = ensureHost(page, wrapper);
    const viewState = { page, wrapper, $host: host.$host, $shell: host.$shell, payload: loadingPayload(), form: null };
    wrapper.__erpwManagedRfqForm = viewState;
    ensureRuntime().then(() => loadRoute(viewState));
  }

  function show(wrapper) {
    const state = wrapper && wrapper.__erpwManagedRfqForm;
    if (state && state.$shell && state.$shell.length) {
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
