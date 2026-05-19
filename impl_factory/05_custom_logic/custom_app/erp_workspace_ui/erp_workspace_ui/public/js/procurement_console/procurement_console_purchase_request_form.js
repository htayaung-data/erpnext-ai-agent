/* global frappe, $ */

(function () {
  const workspaceRegistry = window.erpWorkspaceUiWorkspaceRegistry || {};
  const procurementWorkspace = typeof workspaceRegistry.procurement === "function" ? workspaceRegistry.procurement() : null;
  const procurementRoutes = procurementWorkspace && procurementWorkspace.routes ? procurementWorkspace.routes : {};
  const procurementMethods = procurementWorkspace && procurementWorkspace.methods ? procurementWorkspace.methods : {};
  const PAGE_KEY = procurementRoutes.purchaseRequestForm || "procurement-console-purchase-request-form";
  const WORKLIST_ROUTE = procurementRoutes.worklist || "procurement-console-worklist";
  const CONTEXT_METHOD = procurementMethods.managedPurchaseRequestContext || "erp_workspace_ui.procurement_console.managed_purchase_request.get_managed_purchase_request_context";
  const SAVE_METHOD = procurementMethods.managedPurchaseRequestSave || "erp_workspace_ui.procurement_console.managed_purchase_request.save_managed_purchase_request_draft";
  const ITEM_DEFAULTS_METHOD = procurementMethods.managedPurchaseRequestItemDefaults || "erp_workspace_ui.procurement_console.managed_purchase_request.get_managed_purchase_request_item_defaults";
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

  function ensureStyles() {
    if (document.getElementById("erpw-managed-pr-form-style")) return;
    const style = document.createElement("style");
    style.id = "erpw-managed-pr-form-style";
    style.textContent = `
      .erpw-managed-pr-page { padding-bottom: 24px; }
      .erpw-managed-pr-shell { display: grid; gap: 10px; max-width: 1220px; margin: 0 auto; }
      .erpw-managed-pr-shell .erpw-child-summary { min-height: 0; padding: 12px 16px; border-radius: 14px; border: 1px solid #dbe6f2; background: #ffffff; box-shadow: inset 0 1px 0 rgba(255,255,255,0.98), 0 8px 18px rgba(15,23,42,0.027); }
      .erpw-managed-pr-shell .erpw-child-summary-copy { min-width: 0; background: transparent; }
      .erpw-managed-pr-shell .erpw-child-summary-facts { display: none; padding: 0; border: 0; }
      .erpw-managed-pr-shell .erpw-child-summary-top { align-items: center; gap: 12px; }
      .erpw-managed-pr-shell .erpw-child-kicker { color: #0f766e; font-size: 10px; letter-spacing: 0.09em; }
      .erpw-managed-pr-shell .erpw-child-title { font-size: 20px; line-height: 1.12; letter-spacing: 0; margin-top: 3px; }
      .erpw-managed-pr-shell .erpw-child-subtitle { max-width: 620px; margin-top: 4px; font-size: 12.5px; line-height: 1.32; color: #334155; }
      .erpw-managed-pr-shell .erpw-child-chip-row-header { align-self: center; }
      .erpw-managed-pr-shell .erpw-child-chip { min-height: 25px; padding: 0.22rem 0.56rem; }
      .erpw-managed-pr-shell .erpw-child-actions-toolbar { margin-top: -4px; padding: 0 2px; border: 0; background: transparent; box-shadow: none; }
      .erpw-managed-pr-shell .erpw-child-toolbar-actions { justify-content: flex-start; flex-wrap: wrap; gap: 8px; }
      .erpw-managed-pr-shell .erpw-child-toolbar-action { min-height: 34px; border-radius: 10px; }
      .erpw-managed-pr-card { display: grid; gap: 12px; padding: 15px 18px 18px; overflow: visible; }
      .erpw-managed-pr-section-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; }
      .erpw-managed-pr-section-kicker { font-size: 10.5px; line-height: 1.2; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; }
      .erpw-managed-pr-section-title { margin-top: 3px; font-size: 15.5px; line-height: 1.25; font-weight: 790; color: #0f172a; }
      .erpw-managed-pr-section-note { margin-top: 3px; max-width: 620px; font-size: 12.5px; line-height: 1.38; color: #475569; }
      .erpw-managed-pr-grid { display: grid; grid-template-columns: repeat(2, minmax(170px, 220px)); gap: 12px; align-items: end; }
      .erpw-managed-pr-field { display: grid; gap: 6px; min-width: 0; }
      .erpw-managed-pr-field label { font-size: 10.5px; line-height: 1.2; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; margin: 0; }
      .erpw-managed-pr-input, .erpw-managed-pr-table input { width: 100%; min-height: 37px; border: 1px solid #d5e2ef; border-radius: 11px; padding: 0 10px; font-size: 13px; color: #0f172a; background: #fff; box-shadow: inset 0 1px 0 rgba(255,255,255,0.95); box-sizing: border-box; }
      .erpw-managed-pr-input:focus, .erpw-managed-pr-table input:focus { outline: none; border-color: #8fb0d3; box-shadow: 0 0 0 3px rgba(18,54,95,0.08); }
      .erpw-managed-pr-lines-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; padding-top: 2px; }
      .erpw-managed-pr-lines-title { font-size: 14px; line-height: 1.25; font-weight: 790; color: #0f172a; }
      .erpw-managed-pr-lines-note { margin-top: 3px; color: #64748b; font-size: 12.5px; line-height: 1.36; }
      .erpw-managed-pr-table-wrap { overflow: visible; border: 0; border-radius: 0; background: transparent; }
      .erpw-managed-pr-table, .erpw-managed-pr-table tbody, .erpw-managed-pr-table tr, .erpw-managed-pr-table td { display: block; box-sizing: border-box; }
      .erpw-managed-pr-table { width: 100%; min-width: 0; border-collapse: separate; border-spacing: 0; }
      .erpw-managed-pr-table thead { display: block; margin: 0 0 6px; }
      .erpw-managed-pr-table thead tr { display: grid; grid-template-columns: minmax(240px, 1.35fr) 78px 128px minmax(180px, 1fr) 76px 66px; gap: 10px; align-items: end; padding: 0 12px; border: 0; background: transparent; box-shadow: none; }
      .erpw-managed-pr-table th { display: block; min-width: 0; padding: 0; border: 0; color: #64748b; font-size: 10px; line-height: 1.15; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; text-align: left; white-space: nowrap; }
      .erpw-managed-pr-table tbody { display: grid; gap: 10px; }
      .erpw-managed-pr-table tbody tr { display: grid; grid-template-columns: minmax(240px, 1.35fr) 78px 128px minmax(180px, 1fr) 76px 66px; gap: 10px; align-items: end; padding: 12px; border: 1px solid #dbe6f2; border-radius: 14px; background: #ffffff; box-shadow: inset 0 1px 0 rgba(255,255,255,0.98), 0 7px 16px rgba(15,23,42,0.03); }
      .erpw-managed-pr-table td { min-width: 0; padding: 0; border: 0; display: grid; gap: 6px; vertical-align: top; }
      .erpw-managed-pr-table td::before { content: ""; display: none; }
      .erpw-managed-pr-table td.row-action { align-self: end; }
      .erpw-managed-pr-table td.row-action::before { content: ""; display: none; }
      .erpw-managed-pr-uom-value { display: inline-flex; align-items: center; justify-content: center; min-width: 70px; min-height: 37px; max-width: 100%; border-radius: 999px; border: 1px solid #dbe6f2; background: #f8fafc; color: #334155; padding: 0 11px; font-size: 13px; line-height: 1; font-weight: 650; letter-spacing: 0; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; white-space: nowrap; overflow: visible; text-overflow: clip; box-sizing: border-box; }
      .erpw-managed-pr-row-button, .erpw-managed-pr-add-line { min-height: 34px; border: 1px solid #d5e2ef; border-radius: 10px; background: #fff; color: #12365f; font-weight: 740; font-size: 12px; padding: 0 10px; }
      .erpw-managed-pr-row-button { width: 100%; max-width: 62px; padding: 0 8px; color: #475569; }
      .erpw-managed-pr-row-button:hover, .erpw-managed-pr-add-line:hover { border-color: #9db7d2; background: #f8fbff; color: #12365f; }
      .erpw-managed-pr-lines-footer { display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap; }
      .erpw-managed-pr-add-line { justify-self: start; }
      .erpw-managed-pr-message { min-height: 20px; font-size: 12.5px; color: #64748b; }
      .erpw-managed-pr-message.error { color: #b42318; }
      .erpw-managed-pr-suggestions { position: fixed; z-index: 1200; min-width: 0; max-height: 240px; overflow: auto; margin: 0; border: 1px solid #d5e2ef; border-radius: 12px; background: #fff; box-shadow: 0 18px 40px rgba(15,23,42,0.18); }
      .erpw-managed-pr-suggestion { display: block; width: 100%; text-align: left; border: 0; background: transparent; padding: 9px 11px; font-size: 13px; color: #0f172a; }
      .erpw-managed-pr-suggestion:hover, .erpw-managed-pr-suggestion:focus-visible { background: #f1f5f9; outline: none; }
      .erpw-managed-pr-link-cell { position: relative; }
      @media (max-width: 1180px) {
        .erpw-managed-pr-table thead tr, .erpw-managed-pr-table tbody tr { grid-template-columns: minmax(250px, 1fr) 78px 76px 62px; grid-template-areas: "item qty uom action" "date warehouse warehouse warehouse"; align-items: end; }
        .erpw-managed-pr-table th:nth-child(1) { grid-area: item; }
        .erpw-managed-pr-table th.qty { grid-area: qty; }
        .erpw-managed-pr-table th.date { grid-area: date; }
        .erpw-managed-pr-table th:nth-child(4) { grid-area: warehouse; }
        .erpw-managed-pr-table th.uom { grid-area: uom; }
        .erpw-managed-pr-table th.row-action { grid-area: action; }
        .erpw-managed-pr-line-item { grid-area: item; }
        .erpw-managed-pr-line-qty { grid-area: qty; }
        .erpw-managed-pr-line-date { grid-area: date; max-width: 180px; }
        .erpw-managed-pr-line-warehouse { grid-area: warehouse; }
        .erpw-managed-pr-line-uom { grid-area: uom; }
        .erpw-managed-pr-line-action { grid-area: action; }
      }
      @media (max-width: 720px) {
        .erpw-managed-pr-grid { grid-template-columns: 1fr; }
        .erpw-managed-pr-shell .erpw-child-summary-top { display: grid; }
        .erpw-managed-pr-table thead { display: none; }
        .erpw-managed-pr-table tbody tr { grid-template-columns: 1fr 86px 74px; grid-template-areas: "item item item" "qty uom action" "date date date" "warehouse warehouse warehouse"; }
        .erpw-managed-pr-table td::before { content: attr(data-label); display: block; font-size: 10px; line-height: 1.15; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; }
        .erpw-managed-pr-line-date { max-width: none; }
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
    frappe.set_route(WORKLIST_ROUTE, String(queueKey || "purchase_request_directory").replace(/_/g, "-"));
  }

  function routeToPage(route, parts, options) {
    frappe.route_options = options || {};
    return frappe.set_route.apply(frappe, [route].concat(Array.isArray(parts) ? parts : []));
  }

  function makePage(wrapper) {
    try {
      return frappe.ui.make_app_page({ parent: wrapper, title: "Purchase Request Form", single_column: true });
    } catch (error) {
      const $parent = $(wrapper);
      $parent.empty().append('<main class="layout-main-section erpw-direct-child-body"></main>');
      return { body: $parent.find(".erpw-direct-child-body").first(), set_title(title) { document.title = title || "Purchase Request Form"; } };
    }
  }

  function ensureHost(page, wrapper) {
    const $parent = page && page.body ? $(page.body) : $(wrapper);
    let $host = $parent.children(".erpw-managed-pr-page").first();
    if (!$host.length) {
      $host = $('<section class="erpw-managed-pr-page"></section>');
      $parent.empty().append($host);
    }
    let $shell = $host.children(".erpw-child-shell.erpw-child-detail-shell.erpw-managed-pr-shell").first();
    if (!$shell.length) {
      $shell = $('<div class="erpw-child-shell erpw-child-detail-shell erpw-managed-pr-shell"></div>');
      $host.append($shell);
    }
    return { $host, $shell };
  }

  function stateForm(payload) {
    const form = payload && payload.form ? payload.form : {};
    const header = form.header || {};
    const items = Array.isArray(form.items) && form.items.length ? form.items : [{ item_code: "", qty: 1, schedule_date: header.schedule_date || "", warehouse: "", uom: "" }];
    return {
      name: form.name || "new",
      header: {
        transaction_date: header.transaction_date || "",
        schedule_date: header.schedule_date || "",
        company: header.company || "",
        material_request_type: "Purchase",
      },
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
      icon: action.key === "save_draft" ? "check" : action.key === "back_to_purchase_requests" ? "arrow-left" : "refresh",
      handler() {
        if (action.key === "save_draft") return saveDraft(viewState);
        if (action.key === "reset_unsaved") return loadRoute(viewState, { force: true });
        const target = ((viewState.payload && viewState.payload.action_targets) || {})[action.key];
        if (target && target.kind === "worklist") return routeToWorklist(target.queue_key);
        if (target && target.kind === "page" && target.route) return routeToPage(target.route, target.route_parts, target.options);
      },
    }));
  }

  function formMarkup(form) {
    const header = form.header || {};
    return `
      <section class="erpw-child-card erpw-managed-pr-card" data-erpw-managed-pr-form>
        <div class="erpw-managed-pr-section-head">
          <div>
            <div class="erpw-managed-pr-section-title">Request details</div>
            <div class="erpw-managed-pr-section-note">New item lines use the default date unless changed.</div>
          </div>
        </div>
        <div class="erpw-managed-pr-grid">
          <div class="erpw-managed-pr-field"><label>Transaction Date</label><input class="erpw-managed-pr-input" data-field="transaction_date" type="date" value="${escapeHtml(header.transaction_date || "")}"></div>
          <div class="erpw-managed-pr-field"><label>Default Required By</label><input class="erpw-managed-pr-input" data-field="schedule_date" type="date" value="${escapeHtml(header.schedule_date || "")}"></div>
        </div>
        <div class="erpw-managed-pr-lines-head">
          <div>
            <div class="erpw-managed-pr-lines-title">Items</div>
            <div class="erpw-managed-pr-lines-note">Select items, quantities, line dates, and optional warehouse.</div>
          </div>
        </div>
        <div class="erpw-managed-pr-table-wrap">
          <table class="erpw-managed-pr-table">
            <thead><tr><th>Item</th><th class="qty">Qty</th><th class="date">Line Required By</th><th>Warehouse</th><th class="uom">UOM</th><th class="row-action">Action</th></tr></thead>
            <tbody>
              ${(form.items || []).map((row, index) => `
                <tr data-row-index="${index}">
                  <td class="erpw-managed-pr-link-cell erpw-managed-pr-line-item" data-label="Item"><input class="item-link" data-row-field="item_code" value="${escapeHtml(row.item_code || "")}" placeholder="Select item" autocomplete="off"></td>
                  <td class="erpw-managed-pr-line-qty" data-label="Qty"><input data-row-field="qty" type="number" min="0" step="0.01" value="${escapeHtml(row.qty || "")}"></td>
                  <td class="erpw-managed-pr-line-date" data-label="Line Required By"><input data-row-field="schedule_date" data-schedule-mode="${escapeHtml(row._schedule_date_mode || "inherited")}" type="date" value="${escapeHtml(row.schedule_date || header.schedule_date || "")}"></td>
                  <td class="erpw-managed-pr-link-cell erpw-managed-pr-line-warehouse" data-label="Warehouse"><input class="warehouse-link" data-row-field="warehouse" value="${escapeHtml(row.warehouse || "")}" placeholder="Optional warehouse" autocomplete="off"></td>
                  <td class="uom erpw-managed-pr-line-uom" data-label="UOM"><span class="erpw-managed-pr-uom-value" data-uom-display>${escapeHtml(row.uom || "Derived")}</span><input type="hidden" data-row-field="uom" value="${escapeHtml(row.uom || "")}"></td>
                  <td class="row-action erpw-managed-pr-line-action"><button type="button" class="erpw-managed-pr-row-button" data-remove-row="${index}">Remove</button></td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
        <div class="erpw-managed-pr-lines-footer">
          <button type="button" class="erpw-managed-pr-add-line" data-add-row>Add line</button>
          <div class="erpw-managed-pr-message" data-managed-pr-message></div>
        </div>
      </section>
    `;
  }

  function collectForm($shell, viewState) {
    const form = viewState.form || stateForm(viewState.payload);
    form.header.transaction_date = $shell.find('[data-field="transaction_date"]').val() || "";
    form.header.schedule_date = $shell.find('[data-field="schedule_date"]').val() || "";
    form.header.company = $shell.find('[data-field="company"]').val() || form.header.company || "";
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
    $shell.find("[data-managed-pr-message]").text(message || "").toggleClass("error", tone === "error");
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

  function saveDraft(viewState) {
    const form = collectForm(viewState.$shell, viewState);
    setMessage(viewState.$shell, "Recording request...", "");
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
        setMessage(viewState.$shell, payload.message || "Request recorded for procurement review.", "");
        return;
      }
      renderPayload(viewState, payload);
    }).catch((error) => {
      setMessage(viewState.$shell, error && error.message ? error.message : "Draft could not be saved.", "error");
    });
  }

  function bindForm($shell, viewState) {
    $shell.find("[data-field], [data-row-field]").off("input.prform change.prform");
    $shell.find('[data-field="schedule_date"]').on("input.prform change.prform", function () {
      const previousDefaultDate = (viewState.form && viewState.form.header && viewState.form.header.schedule_date) || "";
      collectForm($shell, viewState);
      syncInheritedLineDates($shell, viewState, $(this).val() || "", previousDefaultDate);
      collectForm($shell, viewState);
    });
    $shell.find('[data-row-field="schedule_date"]').on("input.prform change.prform", function () {
      $(this).attr("data-schedule-mode", "manual");
      collectForm($shell, viewState);
    });
    $shell.find('[data-field]:not([data-field="schedule_date"]), [data-row-field]:not([data-row-field="schedule_date"])').on("input.prform change.prform", () => collectForm($shell, viewState));
    $shell.find("[data-add-row]").off("click.prform").on("click.prform", () => {
      collectForm($shell, viewState);
      const headerDate = viewState.form.header.schedule_date || "";
      viewState.form.items.push({ item_code: "", qty: 1, schedule_date: headerDate, warehouse: "", uom: "", _schedule_date_mode: "inherited" });
      renderPayload(viewState);
    });
    $shell.find("[data-remove-row]").off("click.prform").on("click.prform", function () {
      collectForm($shell, viewState);
      const index = Number($(this).attr("data-remove-row"));
      viewState.form.items.splice(index, 1);
      if (!viewState.form.items.length) viewState.form.items.push({ item_code: "", qty: 1, schedule_date: viewState.form.header.schedule_date || "", warehouse: "", uom: "", _schedule_date_mode: "inherited" });
      renderPayload(viewState);
    });
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
    $(window).off("resize.managedPrSuggest scroll.managedPrSuggest");
    $(document).off("scroll.managedPrSuggest");
    $(".erpw-managed-pr-suggestions").remove();
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
    const placeAbove = !canUseBelow && aboveIsMateriallyBetter && aboveAvoidsChrome;
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
      const $menu = $('<div class="erpw-managed-pr-suggestions" role="listbox"></div>');
      rows.slice(0, 8).forEach((row) => {
        const value = row.value || row.name || row.label || row;
        const label = row.label || row.description || value;
        $('<button type="button" class="erpw-managed-pr-suggestion" role="option"></button>').text(label).on("mousedown", (event) => {
          event.preventDefault();
          $input.val(value);
          collectForm($shell, viewState);
          removeSuggestions();
          if (doctype === "Item") updateItemDefaults($shell, input, viewState);
        }).appendTo($menu);
      });
      $menu.appendTo(document.body);
      positionSuggestions($menu, input);
      $(window).off("resize.managedPrSuggest scroll.managedPrSuggest").on("resize.managedPrSuggest scroll.managedPrSuggest", () => positionSuggestions($menu, input));
      $(document).off("scroll.managedPrSuggest").on("scroll.managedPrSuggest", () => positionSuggestions($menu, input));
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
      state: { kind: "loading", title: "Loading Purchase Request form", detail: "Reading draft context." },
      summary: { kicker: "Purchase Request", title: "New Purchase Request", subtitle: "Capture internal purchase demand before sourcing.", chips: [{ label: "New Request" }, { label: "Purchase only" }] },
      controls: { actions: [] },
      form: { header: { transaction_date: "", schedule_date: "", company: "", material_request_type: "Purchase" }, items: [{ item_code: "", qty: 1, schedule_date: "", warehouse: "", uom: "" }] },
      action_targets: {},
    };
  }

  function renderState($shell, payload) {
    const state = payload && payload.state ? payload.state : {};
    return `
      <section class="erpw-child-card erpw-list-results">
        <div class="erpw-list-state ${escapeHtml(state.kind || "unavailable")}">
          <div class="erpw-list-state-title">${escapeHtml(state.title || "Purchase Request form unavailable")}</div>
          <div class="erpw-list-state-detail">${escapeHtml(state.detail || "This managed form cannot be loaded right now.")}</div>
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
    const form = overridePayload && overridePayload.state && overridePayload.state.kind !== "ready" ? viewState.form || stateForm(viewState.payload) : viewState.form || stateForm(payload);
    const extra = payload.state && payload.state.kind && payload.state.kind !== "ready" && payload.state.kind !== "loading" ? renderState(viewState.$shell, payload) : formMarkup(form) + readinessCardMarkup(payload);
    shellContent().renderShellContent(viewState.$shell, {
      summary: payload.summary || loadingPayload().summary,
      actions: actionConfig(payload, viewState),
      actionLayout: { mode: "toolbar" },
      extraSectionsHtml: extra,
    });
    viewState.$shell.attr("data-erpw-managed-pr-state", payload.state && payload.state.kind ? payload.state.kind : "ready");
    if (payload.state && payload.state.kind === "ready") {
      bindForm(viewState.$shell, viewState);
      bindReadinessCard(viewState.$shell);
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
      renderPayload(viewState);
    }).catch((error) => {
      renderPayload(viewState, { state: { kind: "error", title: "Purchase Request form failed", detail: error && error.message ? error.message : "The managed form could not load." } });
    });
  }

  function render(wrapper) {
    ensureStyles();
    const page = makePage(wrapper);
    const host = ensureHost(page, wrapper);
    const viewState = { page, wrapper, $host: host.$host, $shell: host.$shell, payload: loadingPayload(), form: null };
    wrapper.__erpwManagedPurchaseRequestForm = viewState;
    ensureRuntime().then(() => loadRoute(viewState));
  }

  function show(wrapper) {
    const state = wrapper && wrapper.__erpwManagedPurchaseRequestForm;
    if (state && state.$shell && state.$shell.length) {
      loadRoute(state);
      return;
    }
    render(wrapper);
  }

  window.erpWorkspaceUiProcurementPurchaseRequestForm = Object.assign(window.erpWorkspaceUiProcurementPurchaseRequestForm || {}, {
    render,
    show,
  });
})();
