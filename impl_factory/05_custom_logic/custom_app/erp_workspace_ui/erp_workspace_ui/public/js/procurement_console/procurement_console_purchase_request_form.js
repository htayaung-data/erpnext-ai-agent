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
    if (document.getElementById("erpw-managed-pr-form-style")) return;
    const style = document.createElement("style");
    style.id = "erpw-managed-pr-form-style";
    style.textContent = `
      .erpw-managed-pr-page { padding-bottom: 24px; }
      .erpw-managed-pr-shell { display: grid; gap: 10px; max-width: 1220px; margin: 0 auto; }
      .erpw-managed-pr-shell .erpw-child-summary { min-height: 0; padding: 12px 16px; border-radius: 14px; border: 1px solid #dbe6f2; background: linear-gradient(135deg, #ffffff 0%, #f8fbff 62%, #edf6fb 100%); box-shadow: inset 0 1px 0 rgba(255,255,255,0.98), 0 8px 18px rgba(15,23,42,0.027); }
      .erpw-managed-pr-shell .erpw-child-summary-copy { min-width: 0; }
      .erpw-managed-pr-shell .erpw-child-summary-top { align-items: center; gap: 12px; }
      .erpw-managed-pr-shell .erpw-child-kicker { color: #0f766e; font-size: 10px; letter-spacing: 0.09em; }
      .erpw-managed-pr-shell .erpw-child-title { font-size: 20px; line-height: 1.12; letter-spacing: 0; margin-top: 3px; }
      .erpw-managed-pr-shell .erpw-child-subtitle { max-width: 640px; margin-top: 4px; font-size: 12.5px; line-height: 1.32; color: #334155; }
      .erpw-managed-pr-shell .erpw-child-chip-row-header { align-self: flex-start; }
      .erpw-managed-pr-shell .erpw-child-actions-toolbar { margin-top: -2px; padding: 0 2px; border: 0; background: transparent; box-shadow: none; }
      .erpw-managed-pr-shell .erpw-child-toolbar-actions { justify-content: flex-start; flex-wrap: wrap; gap: 8px; }
      .erpw-managed-pr-shell .erpw-child-toolbar-action { min-height: 34px; border-radius: 10px; }
      .erpw-managed-pr-card { display: grid; gap: 14px; padding: 16px 18px 18px; overflow: hidden; }
      .erpw-managed-pr-section-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; }
      .erpw-managed-pr-section-kicker { font-size: 10.5px; line-height: 1.2; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; }
      .erpw-managed-pr-section-title { margin-top: 4px; font-size: 16px; line-height: 1.25; font-weight: 790; color: #0f172a; }
      .erpw-managed-pr-section-note { margin-top: 4px; max-width: 680px; font-size: 12.5px; line-height: 1.45; color: #475569; }
      .erpw-managed-pr-draft-note { flex: 0 0 auto; align-self: center; max-width: 260px; border: 1px solid #cde5df; background: #f2fbf8; color: #0f766e; border-radius: 999px; padding: 6px 10px; font-size: 11.5px; line-height: 1.2; font-weight: 760; }
      .erpw-managed-pr-grid { display: grid; grid-template-columns: minmax(160px, 220px) minmax(160px, 220px) minmax(220px, 1fr); gap: 12px; align-items: stretch; }
      .erpw-managed-pr-field { display: grid; gap: 6px; min-width: 0; }
      .erpw-managed-pr-field label { font-size: 10.5px; line-height: 1.2; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; margin: 0; }
      .erpw-managed-pr-input, .erpw-managed-pr-table input { width: 100%; min-height: 38px; border: 1px solid #d5e2ef; border-radius: 11px; padding: 0 10px; font-size: 13px; color: #0f172a; background: #fff; box-shadow: inset 0 1px 0 rgba(255,255,255,0.95); box-sizing: border-box; }
      .erpw-managed-pr-input:focus, .erpw-managed-pr-table input:focus { outline: none; border-color: #8fb0d3; box-shadow: 0 0 0 3px rgba(18,54,95,0.08); }
      .erpw-managed-pr-context-card { min-width: 0; border: 1px solid #dbe6f2; border-radius: 12px; background: #f8fafc; padding: 9px 11px; display: grid; gap: 2px; }
      .erpw-managed-pr-context-label { font-size: 10.5px; line-height: 1.2; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; }
      .erpw-managed-pr-context-value { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #0f172a; font-size: 13px; font-weight: 740; }
      .erpw-managed-pr-context-meta { color: #64748b; font-size: 11.5px; line-height: 1.25; }
      .erpw-managed-pr-lines-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; padding-top: 2px; }
      .erpw-managed-pr-lines-title { font-size: 14px; line-height: 1.25; font-weight: 790; color: #0f172a; }
      .erpw-managed-pr-lines-note { margin-top: 3px; color: #64748b; font-size: 12.5px; line-height: 1.4; }
      .erpw-managed-pr-table-wrap { overflow-x: visible; border: 1px solid #dbe6f2; border-radius: 14px; background: #fff; }
      .erpw-managed-pr-table { width: 100%; min-width: 0; border-collapse: collapse; table-layout: fixed; }
      .erpw-managed-pr-table th { padding: 10px 9px; font-size: 10px; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; text-align: left; background: #f8fafc; border-bottom: 1px solid #e5edf5; }
      .erpw-managed-pr-table td { padding: 9px; vertical-align: top; border-bottom: 1px solid #eef3f8; }
      .erpw-managed-pr-table tr:last-child td { border-bottom: 0; }
      .erpw-managed-pr-table .qty { width: 86px; }
      .erpw-managed-pr-table .date { width: 136px; }
      .erpw-managed-pr-table .uom { width: 82px; }
      .erpw-managed-pr-table .row-action { width: 78px; text-align: right; }
      .erpw-managed-pr-uom-value { display: inline-flex; align-items: center; min-height: 38px; max-width: 100%; border-radius: 999px; border: 1px solid #dbe6f2; background: #f8fafc; color: #334155; padding: 0 10px; font-size: 12.5px; font-weight: 760; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .erpw-managed-pr-row-button, .erpw-managed-pr-add-line { min-height: 34px; border: 1px solid #d5e2ef; border-radius: 10px; background: #fff; color: #12365f; font-weight: 740; font-size: 12px; padding: 0 10px; }
      .erpw-managed-pr-row-button { width: 100%; max-width: 64px; padding: 0 8px; }
      .erpw-managed-pr-row-button:hover, .erpw-managed-pr-add-line:hover { border-color: #9db7d2; background: #f8fbff; }
      .erpw-managed-pr-lines-footer { display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap; }
      .erpw-managed-pr-add-line { justify-self: start; }
      .erpw-managed-pr-message { min-height: 20px; font-size: 12.5px; color: #64748b; }
      .erpw-managed-pr-message.error { color: #b42318; }
      .erpw-managed-pr-suggestions { position: absolute; z-index: 20; min-width: min(320px, 90vw); max-height: 220px; overflow: auto; margin-top: 4px; border: 1px solid #d5e2ef; border-radius: 12px; background: #fff; box-shadow: 0 14px 32px rgba(15,23,42,0.14); }
      .erpw-managed-pr-suggestion { display: block; width: 100%; text-align: left; border: 0; background: transparent; padding: 9px 11px; font-size: 13px; color: #0f172a; }
      .erpw-managed-pr-suggestion:hover, .erpw-managed-pr-suggestion:focus-visible { background: #f1f5f9; outline: none; }
      .erpw-managed-pr-link-cell { position: relative; }
      @media (max-width: 980px) {
        .erpw-managed-pr-grid { grid-template-columns: 1fr 1fr; }
        .erpw-managed-pr-context-card { grid-column: 1 / -1; }
        .erpw-managed-pr-section-head, .erpw-managed-pr-lines-head { display: grid; gap: 8px; }
        .erpw-managed-pr-draft-note { justify-self: start; }
        .erpw-managed-pr-table-wrap { overflow-x: auto; }
        .erpw-managed-pr-table { min-width: 760px; }
      }
      @media (max-width: 720px) {
        .erpw-managed-pr-grid { grid-template-columns: 1fr; }
        .erpw-managed-pr-shell .erpw-child-summary-top { display: grid; }
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
      items: items.map((row) => Object.assign({ item_code: "", qty: 1, schedule_date: header.schedule_date || "", warehouse: "", uom: "" }, row || {})),
    };
  }

  function actionConfig(payload, viewState) {
    const actions = payload && payload.controls && Array.isArray(payload.controls.actions) ? payload.controls.actions : [];
    return actions.map((action) => Object.assign({}, action, {
      title: action.key === "reset_unsaved" ? "Reset" : action.title || action.label || action.key,
      variant: action.kind === "primary" ? "primary" : "secondary",
      icon: action.key === "save_draft" ? "check" : action.key === "open_erp_form" ? "external" : action.key === "back_to_purchase_requests" ? "arrow-left" : "refresh",
      handler() {
        if (action.key === "save_draft") return saveDraft(viewState);
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
      <section class="erpw-child-card erpw-managed-pr-card" data-erpw-managed-pr-form>
        <div class="erpw-managed-pr-section-head">
          <div>
            <div class="erpw-managed-pr-section-kicker">Request details</div>
            <div class="erpw-managed-pr-section-title">Draft basics</div>
            <div class="erpw-managed-pr-section-note">Set request dates and add purchase items before saving the draft.</div>
          </div>
          <div class="erpw-managed-pr-draft-note">Draft only. Review and sourcing steps follow after save.</div>
        </div>
        <div class="erpw-managed-pr-grid">
          <div class="erpw-managed-pr-field"><label>Transaction Date</label><input class="erpw-managed-pr-input" data-field="transaction_date" type="date" value="${escapeHtml(header.transaction_date || "")}"></div>
          <div class="erpw-managed-pr-field"><label>Required By</label><input class="erpw-managed-pr-input" data-field="schedule_date" type="date" value="${escapeHtml(header.schedule_date || "")}"></div>
          <div class="erpw-managed-pr-context-card" aria-label="Company context">
            <span class="erpw-managed-pr-context-label">Company</span>
            <span class="erpw-managed-pr-context-value" title="${escapeHtml(header.company || "")}">${escapeHtml(header.company || "Single company")}</span>
            <span class="erpw-managed-pr-context-meta">Locked context</span>
          </div>
        </div>
        <div class="erpw-managed-pr-lines-head">
          <div>
            <div class="erpw-managed-pr-lines-title">Item lines</div>
            <div class="erpw-managed-pr-lines-note">Item, quantity, required date, and optional warehouse for this purchase request.</div>
          </div>
        </div>
        <div class="erpw-managed-pr-table-wrap">
          <table class="erpw-managed-pr-table">
            <thead><tr><th>Item</th><th class="qty">Qty</th><th class="date">Required By</th><th>Warehouse</th><th class="uom">UOM</th><th class="row-action"></th></tr></thead>
            <tbody>
              ${(form.items || []).map((row, index) => `
                <tr data-row-index="${index}">
                  <td class="erpw-managed-pr-link-cell"><input class="item-link" data-row-field="item_code" value="${escapeHtml(row.item_code || "")}" placeholder="Select item" autocomplete="off"></td>
                  <td><input data-row-field="qty" type="number" min="0" step="0.01" value="${escapeHtml(row.qty || "")}"></td>
                  <td><input data-row-field="schedule_date" type="date" value="${escapeHtml(row.schedule_date || header.schedule_date || "")}"></td>
                  <td class="erpw-managed-pr-link-cell"><input class="warehouse-link" data-row-field="warehouse" value="${escapeHtml(row.warehouse || "")}" placeholder="Optional warehouse" autocomplete="off"></td>
                  <td class="uom"><span class="erpw-managed-pr-uom-value" data-uom-display>${escapeHtml(row.uom || "Derived")}</span><input type="hidden" data-row-field="uom" value="${escapeHtml(row.uom || "")}"></td>
                  <td class="row-action"><button type="button" class="erpw-managed-pr-row-button" data-remove-row="${index}">Remove</button></td>
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
        row[$(this).attr("data-row-field")] = $(this).val();
      });
      form.items[index] = row;
    });
    viewState.form = form;
    return form;
  }

  function setMessage($shell, message, tone) {
    $shell.find("[data-managed-pr-message]").text(message || "").toggleClass("error", tone === "error");
  }

  function saveDraft(viewState) {
    const form = collectForm(viewState.$shell, viewState);
    setMessage(viewState.$shell, "Saving draft...", "");
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
        setMessage(viewState.$shell, payload.message || "Draft saved.", "");
        return;
      }
      renderPayload(viewState, payload);
    }).catch((error) => {
      setMessage(viewState.$shell, error && error.message ? error.message : "Draft could not be saved.", "error");
    });
  }

  function bindForm($shell, viewState) {
    $shell.find("[data-field], [data-row-field]").off("input.prform change.prform").on("input.prform change.prform", () => collectForm($shell, viewState));
    $shell.find("[data-add-row]").off("click.prform").on("click.prform", () => {
      collectForm($shell, viewState);
      const headerDate = viewState.form.header.schedule_date || "";
      viewState.form.items.push({ item_code: "", qty: 1, schedule_date: headerDate, warehouse: "", uom: "" });
      renderPayload(viewState);
    });
    $shell.find("[data-remove-row]").off("click.prform").on("click.prform", function () {
      collectForm($shell, viewState);
      const index = Number($(this).attr("data-remove-row"));
      viewState.form.items.splice(index, 1);
      if (!viewState.form.items.length) viewState.form.items.push({ item_code: "", qty: 1, schedule_date: viewState.form.header.schedule_date || "", warehouse: "", uom: "" });
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
      setTimeout(() => $(input).siblings(".erpw-managed-pr-suggestions").remove(), 180);
      if (doctype === "Item") updateItemDefaults($shell, input, viewState);
    });
  }

  function showSuggestions($shell, input, doctype, viewState) {
    const $input = $(input);
    const txt = String($input.val() || "").trim();
    if (txt.length < 1) return;
    frappe.call({ method: "frappe.desk.search.search_link", args: { doctype, txt, page_length: 8 } }).then((response) => {
      const rows = response && response.message && Array.isArray(response.message.results) ? response.message.results : Array.isArray(response.message) ? response.message : [];
      $input.siblings(".erpw-managed-pr-suggestions").remove();
      if (!rows.length) return;
      const $menu = $('<div class="erpw-managed-pr-suggestions"></div>');
      rows.slice(0, 8).forEach((row) => {
        const value = row.value || row.name || row.label || row;
        const label = row.label || row.description || value;
        $('<button type="button" class="erpw-managed-pr-suggestion"></button>').text(label).on("mousedown", (event) => {
          event.preventDefault();
          $input.val(value);
          collectForm($shell, viewState);
          $menu.remove();
          if (doctype === "Item") updateItemDefaults($shell, input, viewState);
        }).appendTo($menu);
      });
      $input.after($menu);
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
      summary: { kicker: "Purchase Request", title: "New Purchase Request", subtitle: "Loading draft form.", chips: [{ label: "Draft" }, { label: "Purchase only" }] },
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

  function renderPayload(viewState, overridePayload) {
    const payload = overridePayload || viewState.payload || loadingPayload();
    const form = overridePayload && overridePayload.state && overridePayload.state.kind !== "ready" ? viewState.form || stateForm(viewState.payload) : viewState.form || stateForm(payload);
    const extra = payload.state && payload.state.kind && payload.state.kind !== "ready" && payload.state.kind !== "loading" ? renderState(viewState.$shell, payload) : formMarkup(form);
    shellContent().renderShellContent(viewState.$shell, {
      summary: payload.summary || loadingPayload().summary,
      actions: actionConfig(payload, viewState),
      actionLayout: { mode: "toolbar" },
      extraSectionsHtml: extra,
    });
    viewState.$shell.attr("data-erpw-managed-pr-state", payload.state && payload.state.kind ? payload.state.kind : "ready");
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
