/* global frappe, $ */

(function () {
  const workspaceRegistry = window.erpWorkspaceUiWorkspaceRegistry || {};
  const procurementWorkspace = typeof workspaceRegistry.procurement === "function" ? workspaceRegistry.procurement() : null;
  const procurementRoutes = procurementWorkspace && procurementWorkspace.routes ? procurementWorkspace.routes : {};
  const procurementMethods = procurementWorkspace && procurementWorkspace.methods ? procurementWorkspace.methods : {};
  const PAGE_KEY = procurementRoutes.itemDetail || "procurement-console-item";
  const WORKLIST_ROUTE = procurementRoutes.worklist || "procurement-console-worklist";
  const PO_DETAIL_ROUTE = procurementRoutes.poFollowUpDetail || "procurement-console-po-follow-up";
  const CONTEXT_METHOD = procurementMethods.itemDetailContext || "erp_workspace_ui.procurement_console.items.get_item_detail_context";
  const BUYING_PROFILE_SAVE_METHOD = "erp_workspace_ui.procurement_console.item_buying_profile.save_item_buying_profile";
  const CHILD_PAGE_RUNTIME_URLS = [
    "/assets/erp_workspace_ui/js/runtime/child_page/child_page_helpers.js",
    "/assets/erp_workspace_ui/js/runtime/child_page/child_page_shell_content.js",
    "/assets/erp_workspace_ui/js/procurement_console/procurement_readiness_ui.js",
  ];
  let runtimePromise = null;
  const SAME_ROUTE_CACHE_TTL_MS = 5000;
  const DETAIL_ROW_LIMIT = 5;
  const DETAIL_EXPANDED_ROW_LIMIT = 12;
  const globalContextRequestCache = window.__erpwProcurementDetailContextCache = window.__erpwProcurementDetailContextCache || Object.create(null);
  const contextRequestCache = globalContextRequestCache[PAGE_KEY] = globalContextRequestCache[PAGE_KEY] || Object.create(null);

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

  function hasShellRuntime() {
    return typeof shellContent().renderShellContent === "function" && hasReadinessUi();
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


  function ensureBuyingProfileStyles() {
    if (document.getElementById("erpw-item-buying-profile-styles")) return;
    const style = document.createElement("style");
    style.id = "erpw-item-buying-profile-styles";
    style.textContent = `
      .erpw-item-buying-profile-card { overflow: visible; margin-top: 10px; padding: 15px 18px 18px; box-sizing: border-box; }
      .erpw-item-buying-profile-top { display: flex; gap: 14px; align-items: center; justify-content: space-between; flex-wrap: wrap; padding-bottom: 12px; border-bottom: 1px solid #e6edf5; }
      .erpw-item-buying-profile-heading { min-width: 260px; flex: 1 1 420px; }
      .erpw-item-buying-profile-title { font-size: 16px; font-weight: 760; color: #0f172a; line-height: 1.25; }
      .erpw-item-buying-profile-note { margin-top: 4px; color: #52637a; font-size: 12.5px; line-height: 1.42; }
      .erpw-item-buying-profile-chip,
      .erpw-item-table-chip { display: inline-flex; align-items: center; justify-content: center; min-height: 26px; border-radius: 999px; padding: 0 10px; font-size: 12px; font-weight: 740; border: 1px solid #d5e2ef; background: #f8fafc; color: #334155; white-space: nowrap; line-height: 1; }
      .erpw-item-table-chip { min-height: 24px; padding: 0 9px; }
      .erpw-item-buying-profile-chip.good, .erpw-item-table-chip.good { border-color: #b7e4ca; background: #f0fbf5; color: #166534; }
      .erpw-item-buying-profile-chip.warning, .erpw-item-table-chip.warning { border-color: #f3d48b; background: #fff8e6; color: #854d0e; }
      .erpw-item-buying-profile-chip.danger, .erpw-item-table-chip.danger { border-color: #f1b7b7; background: #fff1f2; color: #991b1b; }
      .erpw-item-buying-profile-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin-top: 14px; }
      .erpw-item-buying-profile-field { min-width: 0; min-height: 78px; border: 1px solid #dce7f2; border-radius: 8px; padding: 11px 12px; background: #fff; box-shadow: 0 1px 0 rgba(15, 23, 42, .02); }
      .erpw-item-buying-profile-field.is-wide { grid-column: span 1; }
      .erpw-item-buying-profile-label { color: #5b6b80; font-size: 11px; font-weight: 760; text-transform: uppercase; letter-spacing: 0; }
      .erpw-item-buying-profile-value { color: #0f172a; font-size: 13.5px; font-weight: 700; margin-top: 5px; overflow-wrap: anywhere; }
      .erpw-item-buying-profile-meta { color: #64748b; font-size: 12px; margin-top: 4px; line-height: 1.35; overflow-wrap: anywhere; }
      .erpw-item-buying-profile-actions { display: flex; gap: 9px; align-items: center; justify-content: flex-end; flex-wrap: wrap; }
      .erpw-item-buying-profile-button { min-height: 34px; border-radius: 10px; border: 1px solid #d5e2ef; background: #fff; color: #12365f; padding: 0 12px; font-size: 12px; font-weight: 740; box-shadow: 0 1px 1px rgba(15, 23, 42, .03); }
      .erpw-item-buying-profile-button:hover:not(:disabled) { border-color: #9db7d2; background: #f8fbff; }
      .erpw-item-buying-profile-button.primary { border-color: #12365f; background: #12365f; color: #fff; }
      .erpw-item-buying-profile-button.primary:hover:not(:disabled) { border-color: #0f2f52; background: #0f2f52; }
      .erpw-item-buying-profile-button[disabled] { opacity: .6; cursor: not-allowed; }
      .erpw-item-buying-profile-form { margin-top: 14px; border-top: 1px solid #e6edf5; padding-top: 14px; }
      .erpw-item-buying-profile-form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
      .erpw-item-buying-profile-control { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
      .erpw-item-buying-profile-control.wide { grid-column: 1 / -1; }
      .erpw-item-buying-profile-control label { color: #334155; font-size: 12px; font-weight: 740; }
      .erpw-item-buying-profile-control input,
      .erpw-item-buying-profile-control select,
      .erpw-item-buying-profile-control textarea { min-height: 36px; border: 1px solid #cbd8e6; border-radius: 9px; padding: 8px 10px; color: #0f172a; background: #fff; font-size: 13px; width: 100%; }
      .erpw-item-buying-profile-control textarea { min-height: 74px; resize: vertical; }
      .erpw-item-buying-profile-message { margin-top: 10px; font-size: 12px; color: #64748b; }
      .erpw-item-buying-profile-message.error { color: #b91c1c; }
      .erpw-item-buying-profile-message.ready { color: #047857; }
      .erpw-object-profile { margin-top: 12px; display: flex; flex-direction: column; gap: 12px; }
      .erpw-object-profile-brief { border: 1px solid #dbe7f3; border-radius: 8px; background: #f9fbfd; padding: 13px 15px; display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
      .erpw-object-profile-brief-copy { min-width: 240px; flex: 1 1 420px; }
      .erpw-object-profile-brief-title { color: #0f172a; font-size: 14px; line-height: 1.25; font-weight: 780; }
      .erpw-object-profile-brief-note { color: #52637a; font-size: 12.5px; line-height: 1.42; margin-top: 4px; }
      .erpw-object-profile-brief-chips { display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
      .erpw-object-profile-chip { display: inline-flex; align-items: center; min-height: 26px; border-radius: 999px; border: 1px solid #d5e2ef; background: #fff; color: #334155; padding: 0 10px; font-size: 12px; font-weight: 720; white-space: nowrap; }
      .erpw-object-tab-shell { border: 1px solid #dbe7f3; border-radius: 8px; background: #fff; overflow: hidden; }
      .erpw-object-tabs { display: flex; gap: 4px; align-items: center; overflow-x: auto; padding: 8px; border-bottom: 1px solid #e6edf5; background: #f8fafc; }
      .erpw-object-tab { border: 1px solid transparent; background: transparent; color: #42526a; min-height: 34px; border-radius: 8px; padding: 0 12px; font-size: 12.5px; font-weight: 740; white-space: nowrap; }
      .erpw-object-tab:hover { border-color: #c8d7e8; background: #fff; color: #12365f; }
      .erpw-object-tab.is-active { border-color: #12365f; background: #12365f; color: #fff; box-shadow: 0 6px 16px rgba(18, 54, 95, .14); }
      .erpw-object-tab-panels { padding: 12px; display: flex; flex-direction: column; gap: 12px; }
      .erpw-object-tab-panel { display: flex; flex-direction: column; gap: 12px; min-width: 0; }
      .erpw-object-tab-panel[hidden] { display: none !important; }
      .erpw-object-panel-empty { border: 1px dashed #cbd8e6; border-radius: 8px; padding: 16px; color: #64748b; font-size: 13px; background: #fbfdff; }
      .erpw-list-row-reveal { margin-top: 10px; display: flex; justify-content: flex-end; }
      .erpw-list-row-reveal-button { min-height: 32px; border-radius: 8px; border: 1px solid #d5e2ef; background: #fff; color: #12365f; padding: 0 12px; font-size: 12px; font-weight: 740; }
      .erpw-list-row-reveal-button:hover { border-color: #9db7d2; background: #f8fbff; }
      @media (max-width: 1180px) {
        .erpw-item-buying-profile-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .erpw-object-tab-panels { padding: 10px; }
      }
      @media (max-width: 760px) {
        .erpw-item-buying-profile-grid,
        .erpw-item-buying-profile-form-grid { grid-template-columns: 1fr; }
      }
    `;
    document.head.appendChild(style);
  }

  function traceDetailLoad(event) {
    const target = window.__erpwProcurementDetailPerfTrace;
    if (!Array.isArray(target)) return;
    target.push(Object.assign({ pageKey: PAGE_KEY, at: Date.now() }, event || {}));
  }

  function resolveItem(route) {
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
    frappe.set_route(WORKLIST_ROUTE, String(queueKey || "buying_item_directory").replace(/_/g, "-"));
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
    let $host = $parent.children(".erpw-procurement-item-detail-page").first();
    if (!$host.length) {
      $host = $('<section class="erpw-procurement-item-detail-page"></section>');
      $parent.empty().append($host);
    }
    let $shell = $host.children(".erpw-child-shell.erpw-child-detail-shell.erpw-procurement-item-detail-shell").first();
    if (!$shell.length) {
      $shell = $('<div class="erpw-child-shell erpw-child-detail-shell erpw-procurement-item-detail-shell"></div>');
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
          <div class="erpw-direct-child-title">Buying Item Detail</div>
        </div>
        <main class="layout-main-section erpw-direct-child-body"></main>
      </div>
    `);
    const $body = $parent.find(".erpw-direct-child-body").first();
    return {
      body: $body,
      set_title(title) {
        const nextTitle = title || "Buying Item Detail";
        $parent.find(".erpw-direct-child-title").first().text(nextTitle);
        document.title = nextTitle;
      },
    };
  }

  function makeDetailPage(wrapper) {
    try {
      return frappe.ui.make_app_page({ parent: wrapper, title: "Buying Item Detail", single_column: true });
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

  function tableRows(table) {
    return Array.isArray(table && table.rows) ? table.rows : [];
  }

  function rowCountLabel(table, singular, plural) {
    const count = tableRows(table).length;
    const label = count === 1 ? singular : plural;
    return `${count} ${label}`;
  }

  function renderTable(table, options) {
    const settings = options && typeof options === "object" ? options : {};
    const columns = Array.isArray(table && table.columns) ? table.columns : [];
    const rows = tableRows(table);
    const state = table && table.state ? table.state : null;
    const rowLimit = Number.isFinite(settings.rowLimit) ? settings.rowLimit : rows.length;
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
            ${rows.map((row, index) => `
              <tr ${index >= rowLimit ? "hidden data-erpw-extra-row" : ""}>
                ${columns.map((column) => {
                  const cell = row.cells && row.cells[column.key] !== undefined ? row.cells[column.key] : "";
                  const value = cell && typeof cell === "object" ? cell.value : cell;
                  const meta = cell && typeof cell === "object" ? cell.meta : "";
                  const route = cell && typeof cell === "object" ? String(cell.route || "") : "";
                  const routeParts = cell && typeof cell === "object" && Array.isArray(cell.route_parts) ? cell.route_parts : [];
                  const routeName = routeParts.length ? routeParts[0] : value;
                  const tone = cell && typeof cell === "object" ? String(cell.tone || "") : "";
                  const chipColumn = ["readiness", "status"].includes(String(column.key || ""));
                  const valueMarkup = route
                    ? `<button type="button" class="erpw-list-inline-open" data-erpw-procurement-detail-route="${escapeHtml(route)}" data-erpw-procurement-detail-name="${escapeHtml(routeName || "")}"><span class="erpw-list-inline-open-label">${escapeHtml(value || "-")}</span><span class="erpw-list-inline-open-icon" aria-hidden="true">&rarr;</span></button>`
                    : chipColumn && tone
                      ? `<span class="erpw-item-table-chip ${escapeHtml(normalizeToneClass(tone))}">${escapeHtml(value || "-")}</span>`
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

  function renderSection(title, note, table, statusLabel, options) {
    const settings = options && typeof options === "object" ? options : {};
    const rows = tableRows(table);
    const rowLimit = Number.isFinite(settings.rowLimit) ? settings.rowLimit : DETAIL_ROW_LIMIT;
    const revealLimit = Math.min(rows.length, DETAIL_EXPANDED_ROW_LIMIT);
    const revealLabel = rows.length > rowLimit ? `Show ${revealLimit} recent` : "";
    return `
      <section class="erpw-child-card erpw-list-results" data-erpw-object-section="${escapeHtml(settings.key || title || "")}">
        <div class="erpw-child-section-header">
          <div class="erpw-child-section-header-copy">
            <div class="erpw-child-section-header-title">${escapeHtml(title)}</div>
            <div class="erpw-child-section-header-note">${escapeHtml(note)}</div>
          </div>
          <div class="erpw-child-section-header-status">${escapeHtml(statusLabel || "Reference")}</div>
        </div>
        ${renderTable(table || {}, { rowLimit })}
        ${revealLabel ? `<div class="erpw-list-row-reveal"><button type="button" class="erpw-list-row-reveal-button" data-erpw-show-recent data-erpw-row-limit="${escapeHtml(String(revealLimit))}">${escapeHtml(revealLabel)}</button></div>` : ""}
      </section>
    `;
  }

  function renderObjectBrief(detail) {
    const profile = detail.buying_profile || {};
    const readinessLabel = profile.readiness_label || profile.buying_readiness_status || "Readiness review";
    return `
      <section class="erpw-object-profile-brief" data-erpw-object-profile-brief>
        <div class="erpw-object-profile-brief-copy">
          <div class="erpw-object-profile-brief-title">Item buying context</div>
          <div class="erpw-object-profile-brief-note">Supplier relationships, price references, demand, and readiness are grouped for buying review.</div>
        </div>
        <div class="erpw-object-profile-brief-chips" aria-label="Buying item detail summary">
          <span class="erpw-object-profile-chip">${escapeHtml(readinessLabel)}</span>
          <span class="erpw-object-profile-chip">${escapeHtml(rowCountLabel(detail.item_suppliers, "supplier", "suppliers"))}</span>
          <span class="erpw-object-profile-chip">${escapeHtml(rowCountLabel(detail.item_prices, "price reference", "price references"))}</span>
        </div>
      </section>
    `;
  }

  function renderTabButton(tab, isActive) {
    return `<button type="button" class="erpw-object-tab ${isActive ? "is-active" : ""}" role="tab" aria-selected="${isActive ? "true" : "false"}" data-erpw-object-tab="${escapeHtml(tab.key)}">${escapeHtml(tab.label)}</button>`;
  }

  function renderTabPanel(tab, isActive) {
    return `<div class="erpw-object-tab-panel" role="tabpanel" data-erpw-object-tab-panel="${escapeHtml(tab.key)}" ${isActive ? "" : "hidden"}>${tab.content || `<div class="erpw-object-panel-empty">No content is available for this tab.</div>`}</div>`;
  }

  function renderObjectTabs(tabs, defaultKey) {
    const activeKey = defaultKey || (tabs[0] && tabs[0].key) || "";
    return `
      <section class="erpw-object-tab-shell" data-erpw-object-tabs>
        <div class="erpw-object-tabs" role="tablist" aria-label="Buying item detail sections">
          ${tabs.map((tab) => renderTabButton(tab, tab.key === activeKey)).join("")}
        </div>
        <div class="erpw-object-tab-panels">
          ${tabs.map((tab) => renderTabPanel(tab, tab.key === activeKey)).join("")}
        </div>
      </section>
    `;
  }

  function bindObjectTabs(viewState) {
    viewState.$shell.off("click.erpWObjectTabs").on("click.erpWObjectTabs", "[data-erpw-object-tab]", function () {
      const key = String(this.getAttribute("data-erpw-object-tab") || "");
      const $tabs = $(this).closest("[data-erpw-object-tabs]");
      $tabs.find("[data-erpw-object-tab]").removeClass("is-active").attr("aria-selected", "false");
      $(this).addClass("is-active").attr("aria-selected", "true");
      $tabs.find("[data-erpw-object-tab-panel]").prop("hidden", true);
      $tabs.find(`[data-erpw-object-tab-panel="${key}"]`).prop("hidden", false);
    });
    viewState.$shell.off("click.erpWObjectReveal").on("click.erpWObjectReveal", "[data-erpw-show-recent]", function () {
      const $button = $(this);
      const limit = Number($button.attr("data-erpw-row-limit") || DETAIL_EXPANDED_ROW_LIMIT);
      const $section = $button.closest("[data-erpw-object-section]");
      $section.find("[data-erpw-extra-row]").each(function (index) {
        if (index + DETAIL_ROW_LIMIT < limit) $(this).prop("hidden", false);
      });
      $button.closest(".erpw-list-row-reveal").remove();
    });
  }


  function normalizeToneClass(tone) {
    const value = String(tone || "neutral").trim().toLowerCase();
    if (["good", "positive", "success", "ready"].includes(value)) return "good";
    if (["warning", "pending", "review"].includes(value)) return "warning";
    if (["danger", "blocker", "blocked", "hold", "error"].includes(value)) return "danger";
    return "neutral";
  }

  function readinessToneClass(profile) {
    return normalizeToneClass(profile && profile.readiness_tone);
  }

  function formatBusinessTimestamp(value) {
    const raw = String(value || "").trim();
    if (!raw) return "";
    const match = raw.match(/^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::\d{2}(?:\.\d+)?)?)?/);
    if (!match) return raw.replace(/\.\d+$/, "");
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const day = String(Number(match[3]));
    const month = months[Number(match[2]) - 1] || match[2];
    const dateLabel = `${day} ${month} ${match[1]}`;
    if (match[4] && match[5]) return `${dateLabel}, ${match[4]}:${match[5]}`;
    return dateLabel;
  }

  function formatNumberValue(value, suffix) {
    const raw = String(value == null ? "" : value).trim();
    if (!raw) return "-";
    const number = Number(raw);
    if (!Number.isFinite(number)) return raw;
    const text = Number.isInteger(number) ? String(number) : String(number).replace(/\.0+$/, "");
    return suffix ? `${text} ${suffix}` : text;
  }

  function renderProfileField(label, value, meta) {
    return `
      <div class="erpw-item-buying-profile-field">
        <div class="erpw-item-buying-profile-label">${escapeHtml(label)}</div>
        <div class="erpw-item-buying-profile-value">${escapeHtml(value || "-")}</div>
        ${meta ? `<div class="erpw-item-buying-profile-meta">${escapeHtml(meta)}</div>` : ""}
      </div>
    `;
  }

  function renderBuyingProfileForm(profile) {
    if (!profile || !profile.can_edit) return "";
    const status = String(profile.buying_readiness_status || "Not reviewed");
    const statuses = Array.isArray(profile.status_options) ? profile.status_options : [];
    const suppliers = Array.isArray(profile.supplier_options) ? profile.supplier_options : [];
    const preferred = String(profile.preferred_existing_supplier || "");
    return `
      <form class="erpw-item-buying-profile-form" data-erpw-item-buying-profile-form hidden>
        <div class="erpw-item-buying-profile-form-grid">
          <div class="erpw-item-buying-profile-control">
            <label for="erpw-item-buying-status">Buying readiness</label>
            <select id="erpw-item-buying-status" data-erpw-item-profile-field="buying_readiness_status">
              ${statuses.map((option) => {
                const value = String(option.value || option.label || "");
                return `<option value="${escapeHtml(value)}" ${value === status ? "selected" : ""}>${escapeHtml(option.label || value)}</option>`;
              }).join("")}
            </select>
          </div>
          <div class="erpw-item-buying-profile-control">
            <label for="erpw-item-buying-supplier">Preferred supplier</label>
            <input id="erpw-item-buying-supplier" list="erpw-item-buying-supplier-options" data-erpw-item-profile-field="preferred_existing_supplier" value="${escapeHtml(preferred)}" placeholder="Existing Supplier ID">
            <datalist id="erpw-item-buying-supplier-options">
              ${suppliers.map((supplier) => `<option value="${escapeHtml(supplier.supplier || "")}">${escapeHtml(supplier.label || supplier.supplier || "")}</option>`).join("")}
            </datalist>
          </div>
          <div class="erpw-item-buying-profile-control">
            <label for="erpw-item-buying-part-no">Supplier part reference</label>
            <input id="erpw-item-buying-part-no" data-erpw-item-profile-field="supplier_part_no_context" value="${escapeHtml(profile.supplier_part_no_context || "")}" maxlength="140">
          </div>
          <div class="erpw-item-buying-profile-control">
            <label for="erpw-item-buying-lead-time">Lead time days</label>
            <input id="erpw-item-buying-lead-time" type="number" min="0" max="365" data-erpw-item-profile-field="procurement_lead_time_days" value="${escapeHtml(profile.procurement_lead_time_days || "")}">
          </div>
          <div class="erpw-item-buying-profile-control">
            <label for="erpw-item-buying-moq">Minimum order quantity</label>
            <input id="erpw-item-buying-moq" type="number" min="0.000001" max="1000000" step="any" data-erpw-item-profile-field="minimum_order_qty_context" value="${escapeHtml(profile.minimum_order_qty_context || "")}">
          </div>
          <div class="erpw-item-buying-profile-control wide">
            <label for="erpw-item-buying-note">Buying note</label>
            <textarea id="erpw-item-buying-note" data-erpw-item-profile-field="buying_note" maxlength="1000" placeholder="Internal buying context for this item">${escapeHtml(profile.buying_note || "")}</textarea>
          </div>
          <div class="erpw-item-buying-profile-control wide">
            <label for="erpw-item-readiness-note">Readiness note</label>
            <textarea id="erpw-item-readiness-note" data-erpw-item-profile-field="readiness_note" maxlength="1000" placeholder="Short reason or follow-up note">${escapeHtml(profile.readiness_note || "")}</textarea>
          </div>
        </div>
        <div class="erpw-item-buying-profile-actions" style="margin-top: 12px;">
          <button type="button" class="erpw-item-buying-profile-button" data-erpw-item-profile-cancel>Cancel</button>
          <button type="submit" class="erpw-item-buying-profile-button primary" data-erpw-item-profile-save>Save Context</button>
        </div>
        <div class="erpw-item-buying-profile-message" data-erpw-item-profile-message></div>
      </form>
    `;
  }

  function readinessUi() {
    return window.erpWorkspaceUiProcurementReadiness || {};
  }

  function readinessCardMarkup(context) {
    const ui = readinessUi();
    if (!context || typeof ui.renderReadinessCard !== "function") return "";
    return ui.renderReadinessCard(context, {
      title: "Readiness Review",
      note: "Item buying guidance only. Use Item Buying Context for controlled updates.",
    }).replace(/Buying Procurement Context/g, "Item Buying Context");
  }

  function renderBuyingProfile(profile) {
    const data = profile || {};
    const canEdit = Boolean(data.can_edit);
    const supplierLabel = data.preferred_supplier_name || data.preferred_existing_supplier || "Not selected";
    const updated = formatBusinessTimestamp(data.last_context_update_at || data.modified) || "Not saved";
    const leadTime = formatNumberValue(data.procurement_lead_time_days, "days");
    const moq = formatNumberValue(data.minimum_order_qty_context, "");
    return `
      <section class="erpw-child-card erpw-item-buying-profile-card" data-erpw-item-buying-profile-card data-erpw-item-code="${escapeHtml(data.item_code || "")}">
        <div class="erpw-item-buying-profile-top">
          <div class="erpw-item-buying-profile-heading">
            <div class="erpw-item-buying-profile-title">Item Buying Context</div>
            <div class="erpw-item-buying-profile-note">${escapeHtml(canEdit ? "Controlled item buying context for procurement planning." : "Read-only item buying context for procurement planning.")}</div>
          </div>
          <div class="erpw-item-buying-profile-actions">
            <span class="erpw-item-buying-profile-chip ${escapeHtml(readinessToneClass(data))}">${escapeHtml(data.readiness_label || data.buying_readiness_status || "Not reviewed")}</span>
            ${canEdit ? `<button type="button" class="erpw-item-buying-profile-button" data-erpw-item-profile-edit>Edit Context</button>` : ""}
          </div>
        </div>
        <div class="erpw-item-buying-profile-grid">
          ${renderProfileField("Preferred supplier", supplierLabel, data.preferred_existing_supplier ? "Context only; Default Supplier unchanged" : "No controlled supplier selected")}
          ${renderProfileField("Supplier part reference", data.supplier_part_no_context || "-", data.supplier_part_no_context ? "Context only; Item Supplier unchanged" : "No supplier part context")}
          ${renderProfileField("Lead time", leadTime, "Buying context only")}
          ${renderProfileField("Minimum order qty", moq, "Buying context only")}
          ${renderProfileField("Last updated", updated, data.last_context_update_by || data.modified_by || "")}
          ${renderProfileField("Permission", canEdit ? "Editable by Purchase Manager" : "Read-only", data.read_only_reason || "")}
          ${renderProfileField("Buying note", data.buying_note || "-", "")}
          ${renderProfileField("Readiness note", data.readiness_note || "-", "")}
        </div>
        ${renderBuyingProfileForm(data)}
      </section>
    `;
  }

  function itemProfileFormPayload($form) {
    const payload = {};
    $form.find("[data-erpw-item-profile-field]").each(function () {
      const $field = $(this);
      payload[String($field.attr("data-erpw-item-profile-field") || "")] = String($field.val() || "").trim();
    });
    return payload;
  }

  function setItemProfileMessage($card, kind, message) {
    const $message = $card.find("[data-erpw-item-profile-message]").first();
    $message.removeClass("ready error").addClass(kind || "").text(message || "");
  }

  function bindBuyingProfile(viewState) {
    const $card = viewState.$shell.find("[data-erpw-item-buying-profile-card]").first();
    if (!$card.length) return;
    $card.off("click.erpWItemProfileEdit").on("click.erpWItemProfileEdit", "[data-erpw-item-profile-edit]", function () {
      $card.find("[data-erpw-item-buying-profile-form]").prop("hidden", false);
      setItemProfileMessage($card, "", "");
    });
    $card.off("click.erpWItemProfileCancel").on("click.erpWItemProfileCancel", "[data-erpw-item-profile-cancel]", function () {
      $card.find("[data-erpw-item-buying-profile-form]").prop("hidden", true);
      setItemProfileMessage($card, "", "");
    });
    $card.off("submit.erpWItemProfileSave").on("submit.erpWItemProfileSave", "[data-erpw-item-buying-profile-form]", function (event) {
      event.preventDefault();
      const $form = $(this);
      const $button = $form.find("[data-erpw-item-profile-save]").first();
      const itemCode = String($card.attr("data-erpw-item-code") || "").trim();
      if (!itemCode) {
        setItemProfileMessage($card, "error", "Item buying context could not identify the item.");
        return;
      }
      $button.prop("disabled", true).text("Saving...");
      setItemProfileMessage($card, "", "Saving context.");
      frappe.call({
        method: BUYING_PROFILE_SAVE_METHOD,
        args: {
          item_code: itemCode,
          payload: JSON.stringify(itemProfileFormPayload($form)),
        },
      }).then((response) => {
        const message = response && response.message ? response.message : {};
        const state = message.state || {};
        if (state.kind && state.kind !== "ready") {
          setItemProfileMessage($card, "error", state.detail || state.title || "Item buying context was not saved.");
          return;
        }
        setItemProfileMessage($card, "ready", "Item buying context saved.");
        Object.keys(contextRequestCache).forEach((key) => { delete contextRequestCache[key]; });
        loadRoute(viewState, { refresh: true });
      }).catch((error) => {
        setItemProfileMessage($card, "error", error && error.message ? error.message : "Item buying context was not saved.");
      }).finally(() => {
        $button.prop("disabled", false).text("Save Context");
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
            <div class="erpw-list-state-title">${escapeHtml(state.title || "Buying item unavailable")}</div>
            <div class="erpw-list-state-detail">${escapeHtml(state.detail || "This buying item page is not available.")}</div>
          </div>
        </section>
      `;
    }
    const tabs = [
      {
        key: "profile",
        label: "Profile",
        content: `
          ${renderBuyingProfile(detail.buying_profile || {})}
          ${readinessCardMarkup(detail.readiness_context) || `<div class="erpw-object-panel-empty">No readiness guidance is available for this item.</div>`}
        `,
      },
      {
        key: "suppliers-prices",
        label: "Suppliers & Prices",
        content: `
          ${renderSection("Approved suppliers", "Supplier relationships configured on the item master.", detail.item_suppliers, "Supplier reference", { key: "suppliers" })}
          ${renderSection("Supplier price review", "Read-only buying Item Price context. No price updates are exposed.", detail.item_prices, "Price reference", { key: "prices" })}
        `,
      },
      {
        key: "orders",
        label: "Orders",
        content: renderSection("Open purchase orders", "Purchase order posture for buyer follow-up. Warehouse and Finance retain downstream ownership.", detail.purchase_orders, "Buyer follow-up", { key: "orders" }),
      },
      {
        key: "quotation-history",
        label: "Quotation History",
        content: renderSection("Recent supplier quotations", "Recent quotation context linked to this item.", detail.supplier_quotations, "Supplier reference", { key: "quotations" }),
      },
    ];
    return `
      <div class="erpw-object-profile" data-erpw-object-profile="buying-item">
        ${renderObjectTabs(tabs, "profile")}
      </div>
    `;
  }

  function mountPayload(viewState, payload) {
    if (viewState.page && typeof viewState.page.set_title === "function" && payload.page && payload.page.title) {
      viewState.page.set_title(payload.page.title);
    }
    const routeSignature = viewState.routeSignature || "";
    ensureDetailRuntime().then((runtime) => {
      if (viewState.routeSignature !== routeSignature) return;
      ensureBuyingProfileStyles();
      runtime.renderShellContent(viewState.$shell, {
        summary: payload.summary || {},
        actions: normalizeActions(payload, viewState),
        actionLayout: { mode: "toolbar", sparseSecondaryThreshold: 3 },
        extraSectionsHtml: extraSections(payload),
        guidance: {},
      });
      viewState.$shell.off("click.erpWProcurementItemDetailRoute").on("click.erpWProcurementItemDetailRoute", "[data-erpw-procurement-detail-route]", function (event) {
        event.preventDefault();
        const route = String(this.getAttribute("data-erpw-procurement-detail-route") || "");
        const name = String(this.getAttribute("data-erpw-procurement-detail-name") || "");
        if (route === PO_DETAIL_ROUTE) routeToPurchaseOrderFollowUp(name);
      });
      bindObjectTabs(viewState);
      bindBuyingProfile(viewState);
      if (typeof readinessUi().bindReadinessLinks === "function") readinessUi().bindReadinessLinks(viewState.$shell);
    }).catch((error) => {
      if (viewState.routeSignature !== routeSignature) return;
      viewState.$shell.html(`
        <section class="erpw-child-card">
          <div class="erpw-list-state error">
            <div class="erpw-list-state-title">Buying item detail could not be loaded</div>
            <div class="erpw-list-state-detail">${escapeHtml(error && error.message ? error.message : "The shared detail runtime could not be loaded.")}</div>
          </div>
        </section>
      `);
    });
  }

  function loadingPayload(itemCode) {
    return {
      page: { title: "Buying Item Detail" },
      summary: {
        kicker: "Procurement item",
        title: itemCode || "Buying Item Detail",
        subtitle: "Loading read-only item buying context.",
        chips: [{ label: "Loading", tone: "pending" }],
        facts: [],
      },
      controls: { actions: [] },
      detail: {
        state: { kind: "loading", title: "Loading item", detail: "Reading item buying context." },
      },
    };
  }

  function unavailablePayload(error) {
    return {
      page: { title: "Buying Item Detail" },
      summary: {
        kicker: "Procurement item",
        title: "Buying item unavailable",
        subtitle: error && error.message ? error.message : "The item page could not be loaded.",
        chips: [{ label: "error", tone: "blocker" }],
        facts: [],
      },
      detail: {
        state: { kind: "error", title: "Buying item failed", detail: error && error.message ? error.message : "The page could not load." },
      },
    };
  }

  function loadRoute(viewState, options) {
    const settings = options && typeof options === "object" ? options : {};
    const route = currentRouteParts();
    const itemCode = resolveItem(route);
    const routeSignature = Array.isArray(route) ? route.join("|") : "";
    const cacheKey = routeSignature || itemCode || "buying-item-detail";
    const cached = contextRequestCache[cacheKey];
    viewState.routeSignature = routeSignature;
    traceDetailLoad({ type: "loadRoute", routeSignature, cacheKey, refresh: Boolean(settings.refresh), name: itemCode, hasCachedRequest: Boolean(cached && cached.request), hasCachedPayload: Boolean(cached && cached.payload), cachedAgeMs: cached && cached.loadedAt ? Date.now() - cached.loadedAt : null });

    if (!settings.refresh && cached && cached.request) {
      traceDetailLoad({ type: "cache-request-reuse", routeSignature, cacheKey, name: itemCode, mount: cached.payload ? "cached-payload" : "loading" });
      mountPayload(viewState, cached.payload || loadingPayload(itemCode));
      cached.request.then((payload) => {
        traceDetailLoad({ type: "cache-request-resolved", routeSignature, cacheKey, name: itemCode, routeStillActive: viewState.routeSignature === routeSignature });
        if (viewState.routeSignature === routeSignature) mountPayload(viewState, payload || {});
      });
      return cached.request;
    }

    if (!settings.refresh && cached && cached.payload && Date.now() - cached.loadedAt < SAME_ROUTE_CACHE_TTL_MS) {
      traceDetailLoad({ type: "cache-payload-reuse", routeSignature, cacheKey, name: itemCode, cachedAgeMs: Date.now() - cached.loadedAt });
      mountPayload(viewState, cached.payload);
      return Promise.resolve(cached.payload);
    }

    traceDetailLoad({ type: "request-start", routeSignature, cacheKey, name: itemCode });
    mountPayload(viewState, loadingPayload(itemCode));
    const entry = { request: null, payload: null, loadedAt: 0 };
    contextRequestCache[cacheKey] = entry;
    entry.request = frappe.call({
      method: CONTEXT_METHOD,
      args: { item: itemCode },
    }).then((response) => {
      const payload = response && response.message ? response.message : {};
      entry.payload = payload;
      entry.loadedAt = Date.now();
      traceDetailLoad({ type: "request-success", routeSignature, cacheKey, name: itemCode, routeStillActive: viewState.routeSignature === routeSignature });
      if (viewState.routeSignature === routeSignature) mountPayload(viewState, payload);
      return payload;
    }).catch((error) => {
      const payload = unavailablePayload(error);
      entry.payload = payload;
      entry.loadedAt = Date.now();
      traceDetailLoad({ type: "request-error", routeSignature, cacheKey, name: itemCode, routeStillActive: viewState.routeSignature === routeSignature, message: error && error.message ? error.message : String(error || "") });
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
    const viewState = { page, $host: hosts.$host, $shell: hosts.$shell };
    wrapper.__erpwProcurementItemDetail = viewState;
    pruneRouteShells(hosts.$host.get(0));
    loadRoute(viewState);
  }

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) { render(wrapper); };
  frappe.pages[PAGE_KEY].on_page_show = function (wrapper) {
    if (window.erpWorkspaceConsoleSidebar && typeof window.erpWorkspaceConsoleSidebar.refresh === "function") {
      window.erpWorkspaceConsoleSidebar.refresh();
    }
    const existing = wrapper && wrapper.__erpwProcurementItemDetail;
    if (existing && isAttached(existing.$host) && isAttached(existing.$shell)) {
      cleanupManagedPageChrome(wrapper);
      loadRoute(existing);
      return;
    }
    render(wrapper);
  };
})();
