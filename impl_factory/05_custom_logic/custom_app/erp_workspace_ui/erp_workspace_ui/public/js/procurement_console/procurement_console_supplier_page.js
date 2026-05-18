/* global frappe, $ */

(function () {
  const workspaceRegistry = window.erpWorkspaceUiWorkspaceRegistry || {};
  const procurementWorkspace = typeof workspaceRegistry.procurement === "function" ? workspaceRegistry.procurement() : null;
  const procurementRoutes = procurementWorkspace && procurementWorkspace.routes ? procurementWorkspace.routes : {};
  const procurementMethods = procurementWorkspace && procurementWorkspace.methods ? procurementWorkspace.methods : {};
  const PAGE_KEY = procurementRoutes.supplierDetail || "procurement-console-supplier";
  const WORKLIST_ROUTE = procurementRoutes.worklist || "procurement-console-worklist";
  const PO_DETAIL_ROUTE = procurementRoutes.poFollowUpDetail || "procurement-console-po-follow-up";
  const CONTEXT_METHOD = procurementMethods.supplierDetailContext || "erp_workspace_ui.procurement_console.supplier_detail.get_supplier_detail_context";
  const READINESS_SAVE_METHOD = "erp_workspace_ui.procurement_console.supplier_readiness.save_supplier_readiness_profile";
  const CHILD_PAGE_RUNTIME_URLS = [
    "/assets/erp_workspace_ui/js/runtime/child_page/child_page_helpers.js",
    "/assets/erp_workspace_ui/js/runtime/child_page/child_page_shell_content.js",
  ];
  let runtimePromise = null;
  const SAME_ROUTE_CACHE_TTL_MS = 5000;
  const globalContextRequestCache = window.__erpwProcurementDetailContextCache = window.__erpwProcurementDetailContextCache || Object.create(null);
  const contextRequestCache = globalContextRequestCache[PAGE_KEY] = globalContextRequestCache[PAGE_KEY] || Object.create(null);

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

  function ensureReadinessStyles() {
    if (document.getElementById("erpw-supplier-readiness-styles")) return;
    const style = document.createElement("style");
    style.id = "erpw-supplier-readiness-styles";
    style.textContent = `
      .erpw-supplier-readiness-card { overflow: visible; }
      .erpw-supplier-readiness-top { display: flex; gap: 12px; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; }
      .erpw-supplier-readiness-title { font-size: 15px; font-weight: 650; color: #111827; }
      .erpw-supplier-readiness-note { margin-top: 3px; color: #6b7280; font-size: 12px; line-height: 1.4; }
      .erpw-supplier-readiness-chip { display: inline-flex; align-items: center; min-height: 26px; border-radius: 999px; padding: 0 10px; font-size: 12px; font-weight: 650; border: 1px solid #d1d5db; background: #f9fafb; color: #374151; white-space: nowrap; }
      .erpw-supplier-readiness-chip.good { border-color: #a7f3d0; background: #ecfdf5; color: #047857; }
      .erpw-supplier-readiness-chip.warning { border-color: #fde68a; background: #fffbeb; color: #92400e; }
      .erpw-supplier-readiness-chip.danger { border-color: #fecaca; background: #fef2f2; color: #b91c1c; }
      .erpw-supplier-readiness-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-top: 14px; }
      .erpw-supplier-readiness-field { min-width: 0; border: 1px solid #e5e7eb; border-radius: 8px; padding: 10px 12px; background: #fff; }
      .erpw-supplier-readiness-label { color: #6b7280; font-size: 11px; font-weight: 650; text-transform: uppercase; letter-spacing: 0; }
      .erpw-supplier-readiness-value { color: #111827; font-size: 13px; font-weight: 600; margin-top: 4px; overflow-wrap: anywhere; }
      .erpw-supplier-readiness-meta { color: #6b7280; font-size: 12px; margin-top: 3px; overflow-wrap: anywhere; }
      .erpw-supplier-readiness-actions { display: flex; gap: 8px; align-items: center; justify-content: flex-end; flex-wrap: wrap; }
      .erpw-supplier-readiness-button { min-height: 32px; border-radius: 7px; border: 1px solid #d1d5db; background: #fff; color: #111827; padding: 0 12px; font-weight: 650; }
      .erpw-supplier-readiness-button.primary { border-color: #2563eb; background: #2563eb; color: #fff; }
      .erpw-supplier-readiness-button[disabled] { opacity: .6; cursor: not-allowed; }
      .erpw-supplier-readiness-form { margin-top: 14px; border-top: 1px solid #e5e7eb; padding-top: 14px; }
      .erpw-supplier-readiness-form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
      .erpw-supplier-readiness-control { display: flex; flex-direction: column; gap: 5px; min-width: 0; }
      .erpw-supplier-readiness-control.wide { grid-column: 1 / -1; }
      .erpw-supplier-readiness-control label { color: #374151; font-size: 12px; font-weight: 650; }
      .erpw-supplier-readiness-control input,
      .erpw-supplier-readiness-control select,
      .erpw-supplier-readiness-control textarea { min-height: 34px; border: 1px solid #d1d5db; border-radius: 7px; padding: 7px 9px; color: #111827; background: #fff; font-size: 13px; width: 100%; }
      .erpw-supplier-readiness-control textarea { min-height: 70px; resize: vertical; }
      .erpw-supplier-readiness-message { margin-top: 10px; font-size: 12px; color: #6b7280; }
      .erpw-supplier-readiness-message.error { color: #b91c1c; }
      .erpw-supplier-readiness-message.ready { color: #047857; }
      @media (max-width: 1180px) {
        .erpw-supplier-readiness-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      }
      @media (max-width: 760px) {
        .erpw-supplier-readiness-grid,
        .erpw-supplier-readiness-form-grid { grid-template-columns: 1fr; }
      }
    `;
    document.head.appendChild(style);
  }

  function traceDetailLoad(event) {
    const target = window.__erpwProcurementDetailPerfTrace;
    if (!Array.isArray(target)) return;
    target.push(Object.assign({ pageKey: PAGE_KEY, at: Date.now() }, event || {}));
  }

  function resolveSupplier(route) {
    return Array.isArray(route) && route.length > 1 ? String(route[1] || "") : "";
  }


  function routePartsFromLocationPath() {
    const path = String(window.location && window.location.pathname || "").replace(/^\/+/, "");
    const parts = path.split("/").filter(Boolean);
    const routeParts = parts[0] === "desk" || parts[0] === "app" ? parts.slice(1) : parts;
    return routeParts.map((part) => {
      try {
        return decodeURIComponent(part || "");
      } catch (error) {
        return part || "";
      }
    });
  }

  function currentRouteParts() {
    const route = frappe.get_route ? frappe.get_route() : [];
    const pathRoute = routePartsFromLocationPath();
    if (Array.isArray(pathRoute) && pathRoute[0] === PAGE_KEY && pathRoute.length > (Array.isArray(route) ? route.length : 0)) {
      return pathRoute;
    }
    return Array.isArray(route) ? route : pathRoute;
  }

  function routeToWorklist(queueKey) {
    frappe.set_route(WORKLIST_ROUTE, String(queueKey || "supplier_directory").replace(/_/g, "-"));
  }

  function cleanupBeforeProductizedRoute(nextPageKey) {
    const boot = window.erpWorkspaceUiBoot || {};
    if (typeof boot.cleanupProcurementRouteShells === "function") {
      boot.cleanupProcurementRouteShells("", { removeActive: true });
      setTimeout(() => boot.cleanupProcurementRouteShells(nextPageKey || "", { removeActive: false }), 0);
      setTimeout(() => boot.cleanupProcurementRouteShells(nextPageKey || "", { removeActive: false }), 80);
    }
  }

  function routeToPurchaseOrderFollowUp(purchaseOrder) {
    const name = String(purchaseOrder || "").trim();
    if (!name) return;
    cleanupBeforeProductizedRoute(PO_DETAIL_ROUTE);
    frappe.set_route(PO_DETAIL_ROUTE, name);
  }

  function cleanupManagedPageChrome(wrapper) {
    const $wrapper = $(wrapper);
    $wrapper.find(".page-head").remove();
  }

  function ensureHost(page, wrapper) {
    const $parent = page && page.body ? $(page.body) : $(wrapper);
    let $host = $parent.children(".erpw-procurement-supplier-detail-page").first();
    if (!$host.length) {
      $host = $('<section class="erpw-procurement-supplier-detail-page"></section>');
      $parent.empty().append($host);
    }
    let $shell = $host.children(".erpw-child-shell.erpw-child-detail-shell.erpw-procurement-supplier-detail-shell").first();
    if (!$shell.length) {
      $shell = $('<div class="erpw-child-shell erpw-child-detail-shell erpw-procurement-supplier-detail-shell"></div>');
      $host.append($shell);
    }
    return { $host, $shell };
  }

  function isAttached($node) {
    const node = $node && $node.get ? $node.get(0) : null;
    return Boolean(node && document.documentElement.contains(node));
  }

  function makeFallbackPage(wrapper) {
    const $parent = $(wrapper);
    $parent.empty().append(`
      <div class="erpw-direct-child-page">
        <div class="erpw-direct-child-titlebar">
          <div class="erpw-direct-child-title">Supplier Detail</div>
        </div>
        <main class="layout-main-section erpw-direct-child-body"></main>
      </div>
    `);
    const $body = $parent.find(".erpw-direct-child-body").first();
    return {
      body: $body,
      set_title(title) {
        const nextTitle = title || "Supplier Detail";
        $parent.find(".erpw-direct-child-title").first().text(nextTitle);
        document.title = nextTitle;
      },
    };
  }

  function makeDetailPage(wrapper) {
    try {
      return frappe.ui.make_app_page({
        parent: wrapper,
        title: "Supplier Detail",
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
                  const route = cell && typeof cell === "object" ? String(cell.route || "") : "";
                  const routeParts = cell && typeof cell === "object" && Array.isArray(cell.route_parts) ? cell.route_parts : [];
                  const routeName = routeParts.length ? routeParts[0] : value;
                  const valueMarkup = route
                    ? `<button type="button" class="erpw-list-inline-open" data-erpw-procurement-detail-route="${escapeHtml(route)}" data-erpw-procurement-detail-name="${escapeHtml(routeName || "")}"><span class="erpw-list-inline-open-label">${escapeHtml(value || "-")}</span><span class="erpw-list-inline-open-icon" aria-hidden="true">&rarr;</span></button>`
                    : `<span class="erpw-list-cell-value">${escapeHtml(value || "-")}</span>`;
                  return `<td>${valueMarkup}${meta ? `<span class="erpw-list-cell-meta">${escapeHtml(meta)}</span>` : ""}</td>`;
                }).join("")}
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;
  }

  function renderSection(title, note, table) {
    return `
      <section class="erpw-child-card erpw-list-results">
        <div class="erpw-child-section-header">
          <div class="erpw-child-section-header-copy">
            <div class="erpw-child-section-header-title">${escapeHtml(title)}</div>
            <div class="erpw-child-section-header-note">${escapeHtml(note)}</div>
          </div>
          <div class="erpw-child-section-header-status">Visibility only</div>
        </div>
        ${renderTable(table || {})}
      </section>
    `;
  }

  function readinessToneClass(profile) {
    const tone = String(profile && profile.readiness_tone || "neutral").trim();
    if (["good", "warning", "danger"].includes(tone)) return tone;
    return "neutral";
  }

  function renderReadinessField(label, value, meta) {
    return `
      <div class="erpw-supplier-readiness-field">
        <div class="erpw-supplier-readiness-label">${escapeHtml(label)}</div>
        <div class="erpw-supplier-readiness-value">${escapeHtml(value || "-")}</div>
        ${meta ? `<div class="erpw-supplier-readiness-meta">${escapeHtml(meta)}</div>` : ""}
      </div>
    `;
  }

  function renderReadinessForm(profile) {
    if (!profile || !profile.can_edit) return "";
    const status = String(profile.buying_readiness_status || "Ready");
    const statuses = Array.isArray(profile.status_options) ? profile.status_options : [];
    const contacts = Array.isArray(profile.contact_options) ? profile.contact_options : [];
    return `
      <form class="erpw-supplier-readiness-form" data-erpw-supplier-readiness-form>
        <div class="erpw-supplier-readiness-form-grid">
          <div class="erpw-supplier-readiness-control">
            <label for="erpw-supplier-readiness-status">Readiness status</label>
            <select id="erpw-supplier-readiness-status" data-erpw-readiness-field="buying_readiness_status">
              ${statuses.map((option) => {
                const value = String(option.value || option.label || "");
                return `<option value="${escapeHtml(value)}" ${value === status ? "selected" : ""}>${escapeHtml(option.label || value)}</option>`;
              }).join("")}
            </select>
          </div>
          <div class="erpw-supplier-readiness-control">
            <label for="erpw-supplier-readiness-contact">Preferred RFQ contact</label>
            <select id="erpw-supplier-readiness-contact" data-erpw-readiness-field="preferred_rfq_contact">
              <option value="">No controlled contact selected</option>
              ${contacts.map((contact) => {
                const value = String(contact.contact || "");
                const label = `${contact.contact_name || value}${contact.email ? ` - ${contact.email}` : ""}`;
                return `<option value="${escapeHtml(value)}" ${value && value === String(profile.preferred_rfq_contact || "") ? "selected" : ""}>${escapeHtml(label)}</option>`;
              }).join("")}
            </select>
          </div>
          <div class="erpw-supplier-readiness-control wide">
            <label for="erpw-supplier-readiness-email">RFQ recipient email override</label>
            <input id="erpw-supplier-readiness-email" type="email" data-erpw-readiness-field="rfq_recipient_email_override" value="${escapeHtml(profile.rfq_recipient_email_override || "")}" placeholder="Optional controlled recipient email">
          </div>
          <div class="erpw-supplier-readiness-control wide">
            <label for="erpw-supplier-readiness-buying-note">Buying note</label>
            <textarea id="erpw-supplier-readiness-buying-note" data-erpw-readiness-field="buying_note" placeholder="Short buying context for this supplier">${escapeHtml(profile.buying_note || "")}</textarea>
          </div>
          <div class="erpw-supplier-readiness-control wide">
            <label for="erpw-supplier-readiness-note">Readiness note</label>
            <textarea id="erpw-supplier-readiness-note" data-erpw-readiness-field="readiness_note" placeholder="Required for non-ready readiness states">${escapeHtml(profile.readiness_note || "")}</textarea>
          </div>
        </div>
        <div class="erpw-supplier-readiness-actions" style="margin-top: 12px;">
          <button type="button" class="erpw-supplier-readiness-button" data-erpw-readiness-cancel>Cancel</button>
          <button type="submit" class="erpw-supplier-readiness-button primary" data-erpw-readiness-save>Save Readiness</button>
        </div>
        <div class="erpw-supplier-readiness-message" data-erpw-readiness-message></div>
      </form>
    `;
  }

  function renderBuyingProfile(profile) {
    const data = profile || {};
    const recipient = data.recipient || {};
    const recipientEmail = recipient.email || "";
    const recipientMeta = recipientEmail
      ? (recipient.source_label || "Controlled readiness recipient")
      : "No controlled recipient email";
    const contactName = data.preferred_contact_name || data.preferred_rfq_contact || "";
    const canEdit = Boolean(data.can_edit);
    return `
      <section class="erpw-child-card erpw-supplier-readiness-card" data-erpw-supplier-readiness-card data-erpw-supplier="${escapeHtml(data.supplier || "")}">
        <div class="erpw-supplier-readiness-top">
          <div>
            <div class="erpw-supplier-readiness-title">Supplier Buying Profile</div>
            <div class="erpw-supplier-readiness-note">${escapeHtml(canEdit ? "Controlled buying readiness for RFQ preparation." : "Read-only buying readiness for RFQ preparation.")}</div>
          </div>
          <div class="erpw-supplier-readiness-actions">
            <span class="erpw-supplier-readiness-chip ${escapeHtml(readinessToneClass(data))}">${escapeHtml(data.readiness_label || data.buying_readiness_status || "No profile")}</span>
            ${canEdit ? `<button type="button" class="erpw-supplier-readiness-button" data-erpw-readiness-edit>Edit</button>` : ""}
          </div>
        </div>
        <div class="erpw-supplier-readiness-grid">
          ${renderReadinessField("Preferred RFQ contact", contactName || "Not selected", data.preferred_contact_email || "")}
          ${renderReadinessField("Recipient email", recipientEmail || "Not set", recipientMeta)}
          ${renderReadinessField("Last updated", data.modified || "Not saved", data.modified_by || "")}
          ${renderReadinessField("Buying note", data.buying_note || "-", "")}
          ${renderReadinessField("Readiness note", data.readiness_note || "-", "")}
          ${renderReadinessField("Editing", canEdit ? "Purchase Manager" : "Read-only", data.read_only_reason || "")}
        </div>
        ${renderReadinessForm(Object.assign({}, data, { editing: false })).replace('class="erpw-supplier-readiness-form"', 'class="erpw-supplier-readiness-form" hidden')}
      </section>
    `;
  }

  function readinessFormPayload($form) {
    const payload = {};
    $form.find("[data-erpw-readiness-field]").each(function () {
      const $field = $(this);
      payload[String($field.attr("data-erpw-readiness-field") || "")] = String($field.val() || "").trim();
    });
    return payload;
  }

  function setReadinessMessage($card, kind, message) {
    const $message = $card.find("[data-erpw-readiness-message]").first();
    $message.removeClass("ready error").addClass(kind || "").text(message || "");
  }

  function bindReadinessProfile(viewState) {
    const $card = viewState.$shell.find("[data-erpw-supplier-readiness-card]").first();
    if (!$card.length) return;
    $card.off("click.erpWReadinessEdit").on("click.erpWReadinessEdit", "[data-erpw-readiness-edit]", function () {
      $card.find("[data-erpw-supplier-readiness-form]").prop("hidden", false);
      setReadinessMessage($card, "", "");
    });
    $card.off("click.erpWReadinessCancel").on("click.erpWReadinessCancel", "[data-erpw-readiness-cancel]", function () {
      $card.find("[data-erpw-supplier-readiness-form]").prop("hidden", true);
      setReadinessMessage($card, "", "");
    });
    $card.off("submit.erpWReadinessSave").on("submit.erpWReadinessSave", "[data-erpw-supplier-readiness-form]", function (event) {
      event.preventDefault();
      const $form = $(this);
      const $button = $form.find("[data-erpw-readiness-save]").first();
      const supplier = String($card.attr("data-erpw-supplier") || "").trim();
      if (!supplier) {
        setReadinessMessage($card, "error", "Supplier readiness could not identify the supplier.");
        return;
      }
      $button.prop("disabled", true).text("Saving...");
      setReadinessMessage($card, "", "Saving readiness.");
      frappe.call({
        method: READINESS_SAVE_METHOD,
        args: {
          supplier,
          payload: JSON.stringify(readinessFormPayload($form)),
        },
      }).then((response) => {
        const message = response && response.message ? response.message : {};
        const state = message.state || {};
        if (state.kind && state.kind !== "ready") {
          setReadinessMessage($card, "error", state.detail || state.title || "Supplier readiness was not saved.");
          return;
        }
        setReadinessMessage($card, "ready", "Supplier readiness saved.");
        Object.keys(contextRequestCache).forEach((key) => {
          delete contextRequestCache[key];
        });
        loadRoute(viewState, { refresh: true });
      }).catch((error) => {
        setReadinessMessage($card, "error", error && error.message ? error.message : "Supplier readiness was not saved.");
      }).finally(() => {
        $button.prop("disabled", false).text("Save Readiness");
      });
    });
  }

  function extraSections(payload) {
    const detail = (payload && payload.detail) || {};
    const state = detail.state || {};
    if (state.kind && state.kind !== "ready") {
      return `
        <section class="erpw-child-card erpw-list-results">
          <div class="erpw-list-state ${escapeHtml(state.kind)}">
            <div class="erpw-list-state-title">${escapeHtml(state.title || "Supplier detail unavailable")}</div>
            <div class="erpw-list-state-detail">${escapeHtml(state.detail || "This supplier page is not available.")}</div>
          </div>
        </section>
      `;
    }
    return `
      ${renderBuyingProfile(detail.buying_profile || {})}
      ${renderSection("Open or overdue purchase orders", "Buyer follow-up posture for visible purchase orders.", detail.open_purchase_orders)}
      ${renderSection("Recent purchase orders", "Recent buying activity for this supplier.", detail.recent_purchase_orders)}
      ${renderSection("RFQs", "Visible RFQ invitations and response posture for this supplier.", detail.rfqs)}
      ${renderSection("Supplier quotations", "Recent visible supplier quotation context.", detail.supplier_quotations)}
      ${renderSection("Buying contacts", "Visible contact records linked to this supplier.", detail.contacts)}
    `;
  }

  function mountPayload(viewState, payload) {
    if (viewState.page && typeof viewState.page.set_title === "function" && payload.page && payload.page.title) {
      viewState.page.set_title(payload.page.title);
    }
    const routeSignature = viewState.routeSignature || "";
    ensureDetailRuntime().then((runtime) => {
      if (viewState.routeSignature !== routeSignature) return;
      ensureReadinessStyles();
      runtime.renderShellContent(viewState.$shell, {
        summary: payload.summary || {},
        actions: normalizeActions(payload, viewState),
        actionLayout: { mode: "toolbar", sparseSecondaryThreshold: 3 },
        extraSectionsHtml: extraSections(payload),
        guidance: {},
      });
      viewState.$shell.off("click.erpWProcurementSupplierDetailRoute").on("click.erpWProcurementSupplierDetailRoute", "[data-erpw-procurement-detail-route]", function (event) {
        event.preventDefault();
        const route = String($(this).attr("data-erpw-procurement-detail-route") || "");
        const name = String($(this).attr("data-erpw-procurement-detail-name") || "");
          if (route === PO_DETAIL_ROUTE) routeToPurchaseOrderFollowUp(name);
      });
      bindReadinessProfile(viewState);
    }).catch((error) => {
      if (viewState.routeSignature !== routeSignature) return;
      viewState.$shell.html(`
        <section class="erpw-child-card">
          <div class="erpw-list-state error">
            <div class="erpw-list-state-title">Supplier detail could not be loaded</div>
            <div class="erpw-list-state-detail">${escapeHtml(error && error.message ? error.message : "The shared detail runtime could not be loaded.")}</div>
          </div>
        </section>
      `);
    });
  }

  function loadingPayload(supplierName) {
    return {
      page: { title: "Supplier Detail" },
      summary: {
        kicker: "Procurement supplier",
        title: supplierName || "Supplier Detail",
        subtitle: "Loading read-only supplier buying context.",
        chips: [{ label: "Loading", tone: "pending" }],
        facts: [],
      },
      controls: { actions: [] },
      detail: {
        state: { kind: "loading", title: "Loading supplier", detail: "Reading supplier buying context." },
      },
    };
  }

  function unavailablePayload(error) {
    return {
      page: { title: "Supplier Detail" },
      summary: {
        kicker: "Procurement supplier",
        title: "Supplier detail unavailable",
        subtitle: error && error.message ? error.message : "The supplier page could not be loaded.",
        chips: [{ label: "error", tone: "blocker" }],
        facts: [],
      },
      detail: {
        state: { kind: "error", title: "Supplier detail failed", detail: error && error.message ? error.message : "The page could not load." },
      },
    };
  }

  function loadRoute(viewState, options) {
    const settings = options && typeof options === "object" ? options : {};
    const route = currentRouteParts();
    const supplierName = resolveSupplier(route);
    const routeSignature = Array.isArray(route) ? route.join("|") : "";
    const cacheKey = routeSignature || supplierName || "supplier-detail";
    const cached = contextRequestCache[cacheKey];
    viewState.routeSignature = routeSignature;
    traceDetailLoad({ type: "loadRoute", routeSignature, cacheKey, refresh: Boolean(settings.refresh), name: supplierName, hasCachedRequest: Boolean(cached && cached.request), hasCachedPayload: Boolean(cached && cached.payload), cachedAgeMs: cached && cached.loadedAt ? Date.now() - cached.loadedAt : null });

    if (!settings.refresh && cached && cached.request) {
      traceDetailLoad({ type: "cache-request-reuse", routeSignature, cacheKey, name: supplierName, mount: cached.payload ? "cached-payload" : "loading" });
      mountPayload(viewState, cached.payload || loadingPayload(supplierName));
      cached.request.then((payload) => {
        traceDetailLoad({ type: "cache-request-resolved", routeSignature, cacheKey, name: supplierName, routeStillActive: viewState.routeSignature === routeSignature });
        if (viewState.routeSignature === routeSignature) mountPayload(viewState, payload || {});
      });
      return cached.request;
    }

    if (!settings.refresh && cached && cached.payload && Date.now() - cached.loadedAt < SAME_ROUTE_CACHE_TTL_MS) {
      traceDetailLoad({ type: "cache-payload-reuse", routeSignature, cacheKey, name: supplierName, cachedAgeMs: Date.now() - cached.loadedAt });
      mountPayload(viewState, cached.payload);
      return Promise.resolve(cached.payload);
    }

    traceDetailLoad({ type: "request-start", routeSignature, cacheKey, name: supplierName });
    mountPayload(viewState, loadingPayload(supplierName));
    const entry = { request: null, payload: null, loadedAt: 0 };
    contextRequestCache[cacheKey] = entry;
    entry.request = frappe.call({
      method: CONTEXT_METHOD,
      args: {
        supplier: supplierName,
      },
    }).then((response) => {
      const payload = response && response.message ? response.message : {};
      entry.payload = payload;
      entry.loadedAt = Date.now();
      traceDetailLoad({ type: "request-success", routeSignature, cacheKey, name: supplierName, routeStillActive: viewState.routeSignature === routeSignature });
      if (viewState.routeSignature === routeSignature) mountPayload(viewState, payload);
      return payload;
    }).catch((error) => {
      const payload = unavailablePayload(error);
      entry.payload = payload;
      entry.loadedAt = Date.now();
      traceDetailLoad({ type: "request-error", routeSignature, cacheKey, name: supplierName, routeStillActive: viewState.routeSignature === routeSignature, message: error && error.message ? error.message : String(error || "") });
      if (viewState.routeSignature === routeSignature) mountPayload(viewState, payload);
      return payload;
    });
    entry.request.then(() => {
      if (contextRequestCache[cacheKey] === entry) entry.request = null;
    });
    return entry.request;
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
    const page = makeDetailPage(wrapper);
    cleanupManagedPageChrome(wrapper);
    const hosts = ensureHost(page, wrapper);
    const viewState = {
      page,
      $host: hosts.$host,
      $shell: hosts.$shell,
    };
    wrapper.__erpwProcurementSupplierDetail = viewState;
    pruneRouteShells(hosts.$host.get(0));
    loadRoute(viewState);
  }

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) { render(wrapper); };
  frappe.pages[PAGE_KEY].on_page_show = function (wrapper) {
    if (window.erpWorkspaceConsoleSidebar && typeof window.erpWorkspaceConsoleSidebar.refresh === "function") {
      window.erpWorkspaceConsoleSidebar.refresh();
    }
    const existing = wrapper && wrapper.__erpwProcurementSupplierDetail;
    if (existing && isAttached(existing.$host) && isAttached(existing.$shell)) {
      cleanupManagedPageChrome(wrapper);
      loadRoute(existing);
      return;
    }
    render(wrapper);
  };
})();
