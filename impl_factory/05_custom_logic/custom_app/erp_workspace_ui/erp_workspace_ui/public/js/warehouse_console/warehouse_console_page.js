/* global frappe, $ */

(function () {
  const workspaceRegistry = window.erpWorkspaceUiWorkspaceRegistry || {};
  const warehouseWorkspace = typeof workspaceRegistry.warehouse === "function" ? workspaceRegistry.warehouse() : null;
  const warehouseRoutes = warehouseWorkspace && warehouseWorkspace.routes ? warehouseWorkspace.routes : {};
  const warehouseMethods = warehouseWorkspace && warehouseWorkspace.methods ? warehouseWorkspace.methods : {};
  const PAGE_KEY = warehouseRoutes.home || "warehouse-console";
  const WORKLIST_PAGE_KEY = warehouseRoutes.worklist || "warehouse-console-worklist";
  const INBOUND_QUEUE_KEY = "inbound_receiving";
  const OVERVIEW_METHOD = warehouseMethods.overview || "erp_workspace_ui.warehouse_console.service.get_warehouse_console_overview";
  const INBOUND_METHOD = warehouseMethods.inboundQueue || warehouseMethods.inbound_queue || "erp_workspace_ui.warehouse_console.service.get_warehouse_inbound_receiving_queue";
  const CONSOLE_RUNTIME_URL = "/assets/erp_workspace_ui/js/runtime/console/workspace_console_runtime.js";
  const BOOTSTRAP_RETRY_DELAYS = [350, 900, 1800];
  let consoleRuntimePromise = null;
  let overviewRenderSerial = 0;
  let activeOverviewRenderState = null;
  let activeOverviewGuardBound = false;
  let inboundRouteGuardBound = false;
  let inboundRouteRenderSerial = 0;

  function consoleRuntime() {
    return window.erpWorkspaceConsoleRuntime || {};
  }

  function hasConsoleRuntime() {
    const runtime = consoleRuntime();
    return Boolean(runtime && typeof runtime.escapeHtml === "function");
  }

  function ensureConsoleRuntime() {
    if (hasConsoleRuntime()) return Promise.resolve(consoleRuntime());
    if (consoleRuntimePromise) return consoleRuntimePromise;
    consoleRuntimePromise = new Promise((resolve, reject) => {
      frappe.require(CONSOLE_RUNTIME_URL, () => {
        if (hasConsoleRuntime()) {
          resolve(consoleRuntime());
          return;
        }
        reject(new Error("Shared console runtime is not loaded on this page."));
      });
    }).catch((error) => {
      consoleRuntimePromise = null;
      throw error;
    });
    return consoleRuntimePromise;
  }

  function escapeHtml(value) {
    const method = consoleRuntime().escapeHtml;
    if (typeof method === "function") return method(value);
    if (frappe.utils && typeof frappe.utils.escape_html === "function") {
      return frappe.utils.escape_html(value == null ? "" : String(value));
    }
    return String(value == null ? "" : value).replace(/[&<>"']/g, (character) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "\"": "&quot;",
      "'": "&#39;",
    }[character] || character));
  }

  function pathRouteParts() {
    const path = String((window.location && window.location.pathname) || "").replace(/^\/+/, "");
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

  function overviewRouteSignature() {
    const pathRoute = pathRouteParts();
    if (Array.isArray(pathRoute) && String(pathRoute[0] || "") === PAGE_KEY) return pathRoute.join("|");
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) ? route.join("|") : "";
  }

  function isActiveWarehouseRoute() {
    const pathRoute = pathRouteParts();
    if (String(pathRoute[0] || "") === PAGE_KEY) return true;
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) && String(route[0] || "") === PAGE_KEY;
  }

  function inboundRouteSignature() {
    const pathRoute = pathRouteParts();
    if (String(pathRoute[0] || "") === WORKLIST_PAGE_KEY) return pathRoute.join("|");
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) ? route.join("|") : "";
  }

  function isActiveInboundRoute() {
    const pathRoute = pathRouteParts();
    if (String(pathRoute[0] || "") === WORKLIST_PAGE_KEY) {
      const queue = String(pathRoute[1] || "").replace(/-/g, "_");
      return !queue || queue === INBOUND_QUEUE_KEY;
    }
    const route = frappe.get_route ? frappe.get_route() : [];
    if (!Array.isArray(route) || String(route[0] || "") !== WORKLIST_PAGE_KEY) return false;
    const queue = String(route[1] || "").replace(/-/g, "_");
    return !queue || queue === INBOUND_QUEUE_KEY;
  }

  function warehouseConsoleDiagnostics() {
    const api = window.erpWorkspaceWarehouseConsole = window.erpWorkspaceWarehouseConsole || {};
    api.diagnostics = api.diagnostics || {};
    return api.diagnostics;
  }

  function markWarehouseDiagnostic(key) {
    const diagnostics = warehouseConsoleDiagnostics();
    diagnostics[key] = (diagnostics[key] || 0) + 1;
    diagnostics.lastEvent = key;
    diagnostics.lastEventAt = Date.now();
  }

  function ensureStyle() {
    if (document.getElementById("warehouse-console-shell-style")) return;
    const style = document.createElement("style");
    style.id = "warehouse-console-shell-style";
    style.textContent = `
      .warehouse-console-shell {
        width: min(1180px, calc(100% - 24px));
        min-width: 0;
      }
      .warehouse-console-header {
        display: grid;
        gap: 18px;
        padding: 22px;
        overflow: hidden;
        background: linear-gradient(135deg, #ffffff 0%, #f8fbfa 54%, #eef7f2 100%);
        border: 1px solid rgba(210, 225, 218, 0.92);
      }
      .warehouse-console-header-row {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 16px;
        align-items: start;
      }
      .warehouse-console-title {
        margin: 0;
        color: #17231f;
        font-size: 30px;
        line-height: 1.05;
        font-weight: 720;
        letter-spacing: 0;
      }
      .warehouse-console-note {
        margin-top: 6px;
        max-width: 760px;
        color: #52655d;
        font-size: 13px;
        line-height: 1.55;
      }
      .warehouse-console-refresh {
        min-height: 34px;
        padding: 0 14px;
        border: 1px solid rgba(177, 199, 189, 0.95);
        border-radius: 8px;
        background: #ffffff;
        color: #1f3b31;
        font-size: 12px;
        font-weight: 700;
      }
      .warehouse-console-kpi-grid {
        display: grid;
        grid-template-columns: repeat(6, minmax(0, 1fr));
        gap: 8px;
        min-width: 0;
      }
      .warehouse-console-kpi-card {
        min-width: 0;
        display: grid;
        gap: 7px;
        padding: 14px 14px 13px;
        border: 1px solid rgba(214, 228, 221, 0.96);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.9);
      }
      .warehouse-console-kpi-label {
        overflow-wrap: anywhere;
        color: #5f7169;
        font-size: 10.5px;
        font-weight: 760;
        letter-spacing: 0.05em;
        line-height: 1.25;
        text-transform: uppercase;
      }
      .warehouse-console-kpi-value {
        color: #17231f;
        font-size: 27px;
        font-weight: 760;
        line-height: 1;
      }
      .warehouse-console-kpi-meta {
        color: #667a71;
        font-size: 11.5px;
        line-height: 1.4;
      }
      .warehouse-console-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 14px;
      }
      .warehouse-console-section {
        min-width: 0;
        padding: 18px 18px 17px;
      }
      .warehouse-console-section-head {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 14px;
      }
      .warehouse-console-section-title {
        margin: 0;
        color: #1f2b27;
        font-size: 15px;
        font-weight: 760;
        line-height: 1.3;
      }
      .warehouse-console-section-note {
        color: #6a7b73;
        font-size: 12px;
        line-height: 1.4;
        text-align: right;
      }
      .warehouse-console-card-grid {
        display: grid;
        gap: 8px;
      }
      .warehouse-console-status-card {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: center;
        gap: 12px;
        min-width: 0;
        padding: 11px 12px;
        border: 1px solid rgba(224, 233, 229, 0.96);
        border-radius: 8px;
        background: #ffffff;
      }
      .warehouse-console-status-title {
        color: #263530;
        font-size: 13px;
        font-weight: 720;
        line-height: 1.35;
      }
      .warehouse-console-status-note {
        margin-top: 2px;
        color: #708178;
        font-size: 11.5px;
        line-height: 1.4;
      }
      .warehouse-console-status-value {
        min-width: 42px;
        text-align: right;
        color: #1f3b31;
        font-size: 20px;
        font-weight: 760;
        line-height: 1;
      }
      .warehouse-console-inbound-panel {
        display: grid;
        gap: 13px;
        min-width: 0;
        padding: 16px;
        border: 1px solid rgba(210, 225, 218, 0.92);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.76);
      }
      .warehouse-console-inbound-head,
      .warehouse-inbound-queue-head {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: start;
        gap: 14px;
      }
      .warehouse-console-inbound-title,
      .warehouse-inbound-queue-title {
        margin: 0;
        color: #1f2b27;
        font-size: 16px;
        font-weight: 760;
        line-height: 1.3;
      }
      .warehouse-console-inbound-note,
      .warehouse-inbound-queue-note {
        margin-top: 3px;
        color: #64766e;
        font-size: 12.5px;
        line-height: 1.45;
      }
      .warehouse-console-inbound-open,
      .warehouse-inbound-queue-button {
        min-height: 34px;
        padding: 0 12px;
        border: 1px solid rgba(177, 199, 189, 0.95);
        border-radius: 8px;
        background: #ffffff;
        color: #1f3b31;
        font-size: 12px;
        font-weight: 720;
      }
      .warehouse-console-inbound-cards,
      .warehouse-inbound-queue-cards {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 8px;
      }
      .warehouse-console-inbound-card,
      .warehouse-inbound-queue-card {
        min-width: 0;
        padding: 12px;
        border: 1px solid rgba(219, 231, 225, 0.96);
        border-radius: 8px;
        background: #ffffff;
      }
      .warehouse-console-inbound-card-label,
      .warehouse-inbound-queue-card-label {
        color: #667a71;
        font-size: 10.5px;
        font-weight: 760;
        letter-spacing: 0.05em;
        line-height: 1.25;
        text-transform: uppercase;
      }
      .warehouse-console-inbound-card-value,
      .warehouse-inbound-queue-card-value {
        margin-top: 7px;
        color: #17231f;
        font-size: 24px;
        font-weight: 760;
        line-height: 1;
      }
      .warehouse-console-inbound-card-note,
      .warehouse-inbound-queue-card-note {
        margin-top: 6px;
        color: #708178;
        font-size: 11.5px;
        line-height: 1.35;
      }
      .warehouse-console-inbound-preview {
        display: grid;
        gap: 7px;
      }
      .warehouse-console-inbound-row {
        display: grid;
        grid-template-columns: minmax(0, 1.15fr) minmax(0, 0.9fr) minmax(0, 0.75fr) auto;
        gap: 10px;
        align-items: center;
        min-width: 0;
        padding: 10px 11px;
        border: 1px solid rgba(224, 233, 229, 0.96);
        border-radius: 8px;
        background: #ffffff;
      }
      .warehouse-console-inbound-row strong,
      .warehouse-inbound-order {
        color: #263530;
        font-size: 13px;
        font-weight: 740;
        line-height: 1.3;
      }
      .warehouse-console-inbound-row span,
      .warehouse-inbound-meta {
        min-width: 0;
        color: #66786f;
        font-size: 12px;
        line-height: 1.35;
        overflow-wrap: anywhere;
      }
      .warehouse-inbound-shell {
        width: min(1180px, calc(100% - 24px));
        min-width: 0;
      }
      .warehouse-inbound-queue-header {
        display: grid;
        gap: 16px;
        padding: 22px;
        border: 1px solid rgba(210, 225, 218, 0.92);
        border-radius: 8px;
        background: linear-gradient(135deg, #ffffff 0%, #f8fbfa 58%, #eef7f2 100%);
      }
      .warehouse-inbound-controls {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr)) auto auto auto;
        gap: 8px;
        align-items: end;
        padding: 12px;
        border: 1px solid rgba(219, 231, 225, 0.96);
        border-radius: 8px;
        background: #ffffff;
      }
      .warehouse-inbound-field {
        display: grid;
        gap: 5px;
        min-width: 0;
      }
      .warehouse-inbound-field label {
        color: #64766e;
        font-size: 10.5px;
        font-weight: 760;
        letter-spacing: 0.05em;
        text-transform: uppercase;
      }
      .warehouse-inbound-field input,
      .warehouse-inbound-field select {
        width: 100%;
        min-width: 0;
        height: 34px;
        border: 1px solid rgba(205, 220, 213, 0.98);
        border-radius: 8px;
        background: #ffffff;
        color: #23352f;
        font-size: 12.5px;
        padding: 0 10px;
      }
      .warehouse-inbound-groups {
        display: grid;
        gap: 12px;
        margin-top: 14px;
      }
      .warehouse-inbound-group {
        min-width: 0;
        padding: 16px;
        border: 1px solid rgba(219, 231, 225, 0.96);
        border-radius: 8px;
        background: #ffffff;
      }
      .warehouse-inbound-group-head {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 10px;
      }
      .warehouse-inbound-group-title {
        margin: 0;
        color: #1f2b27;
        font-size: 14px;
        font-weight: 760;
      }
      .warehouse-inbound-group-note {
        color: #72837b;
        font-size: 12px;
      }
      .warehouse-inbound-row {
        display: grid;
        gap: 8px;
        min-width: 0;
        padding: 12px;
        border: 1px solid rgba(228, 236, 232, 0.98);
        border-radius: 8px;
        background: #fbfdfc;
      }
      .warehouse-inbound-row-main {
        display: grid;
        grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.85fr) minmax(0, 0.9fr) minmax(0, 0.75fr) auto;
        gap: 10px;
        align-items: center;
      }
      .warehouse-inbound-badge {
        display: inline-flex;
        align-items: center;
        width: fit-content;
        min-height: 22px;
        padding: 0 8px;
        border: 1px solid rgba(197, 217, 207, 0.9);
        border-radius: 999px;
        background: #f4faf7;
        color: #264239;
        font-size: 10.5px;
        font-weight: 760;
        text-transform: uppercase;
      }
      .warehouse-inbound-lines {
        display: none;
        gap: 6px;
        padding-top: 7px;
        border-top: 1px solid rgba(224, 233, 229, 0.96);
      }
      .warehouse-inbound-row.is-expanded .warehouse-inbound-lines {
        display: grid;
      }
      .warehouse-inbound-line {
        display: grid;
        grid-template-columns: minmax(0, 1fr) minmax(0, 0.5fr) minmax(0, 0.8fr);
        gap: 8px;
        color: #51645c;
        font-size: 12px;
        line-height: 1.35;
      }
      .warehouse-console-state {
        padding: 20px;
      }
      .warehouse-console-state-title {
        margin: 0 0 8px;
        color: #1f2b27;
        font-size: 18px;
        font-weight: 740;
      }
      .warehouse-console-state-detail {
        color: #64746d;
        font-size: 13px;
        line-height: 1.55;
      }
      @media (max-width: 1240px) {
        .warehouse-console-kpi-grid {
          grid-template-columns: repeat(3, minmax(0, 1fr));
        }
        .warehouse-console-inbound-cards,
        .warehouse-inbound-queue-cards {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .warehouse-inbound-controls {
          grid-template-columns: repeat(4, minmax(0, 1fr));
        }
      }
      @media (max-width: 900px) {
        .warehouse-console-header-row,
        .warehouse-console-grid,
        .warehouse-console-inbound-head,
        .warehouse-inbound-queue-head,
        .warehouse-console-inbound-row,
        .warehouse-inbound-row-main {
          grid-template-columns: minmax(0, 1fr);
        }
        .warehouse-console-section-note {
          text-align: left;
        }
      }
      @media (max-width: 680px) {
        .warehouse-console-kpi-grid {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
      }
    `;
    document.head.appendChild(style);
  }

  function pageBodyElement(page) {
    if (page && page.body) {
      if (page.body.nodeType) return page.body;
      if (page.body.jquery && page.body[0]) return page.body[0];
    }
    return document.querySelector(".erpw-direct-warehouse-body");
  }

  function currentWarehouseHost() {
    return document.querySelector('.erpw-direct-warehouse-page[data-erpw-page-key="warehouse-console"]');
  }

  function ensureWarehouseBody(host) {
    if (!host) return null;
    let body = host.querySelector(".erpw-direct-warehouse-body");
    if (!body) {
      body = document.createElement("main");
      body.className = "layout-main-section erpw-direct-warehouse-body";
      host.appendChild(body);
    }
    return body;
  }

  function removeDuplicateWarehouseHosts(keepBody) {
    const keepHost = keepBody ? keepBody.closest('.erpw-direct-warehouse-page[data-erpw-page-key="warehouse-console"]') : null;
    document.querySelectorAll('.sales-console-shell[data-erpw-workspace="warehouse"]').forEach((shell) => {
      if (!keepBody || !keepBody.contains(shell)) shell.remove();
    });
    document.querySelectorAll('.erpw-direct-warehouse-page[data-erpw-page-key="warehouse-console"]').forEach((host) => {
      if (host !== keepHost) host.remove();
    });
  }

  function replacePageBody(page, $content) {
    const body = pageBodyElement(page);
    if (!body) return;
    removeDuplicateWarehouseHosts(body);
    body.innerHTML = "";
    $content.each((index, node) => body.appendChild(node));
  }

  function makeConsolePage(wrapper) {
    const existingHost = currentWarehouseHost();
    if (existingHost && document.body.contains(existingHost)) {
      return {
        body: ensureWarehouseBody(existingHost),
        set_title(title) {
          document.title = title || "Warehouse Console";
        },
      };
    }

    const $parent = $(wrapper);
    if (wrapper && wrapper.id === "body") {
      let $host = $parent.find('.erpw-direct-warehouse-page[data-erpw-page-key="warehouse-console"]').first();
      if (!$host.length) {
        $host = $('<div class="erpw-direct-warehouse-page" data-erpw-page-key="warehouse-console"></div>').appendTo($parent);
      }
      return {
        body: ensureWarehouseBody($host.get(0)),
        set_title(title) {
          document.title = title || "Warehouse Console";
        },
      };
    }
    $parent.empty().append(`
      <div class="erpw-direct-warehouse-page" data-erpw-page-key="warehouse-console">
        <main class="layout-main-section erpw-direct-warehouse-body"></main>
      </div>
    `);
    return {
      body: $parent.find(".erpw-direct-warehouse-body").first().get(0),
      set_title(title) {
        document.title = title || "Warehouse Console";
      },
    };
  }

  function renderState(page, state) {
    ensureStyle();
    const payloadState = state || {};
    const $root = $(`
      <div class="sales-console-shell warehouse-console-shell" data-erpw-workspace="warehouse" data-warehouse-console-state="${escapeHtml(payloadState.kind || "unavailable")}">
        <section class="warehouse-console-state">
          <h1 class="warehouse-console-state-title">${escapeHtml(payloadState.title || "Warehouse Console unavailable")}</h1>
          <div class="warehouse-console-state-detail">${escapeHtml(payloadState.detail || "Warehouse information could not be loaded. Refresh or try again.")}</div>
        </section>
      </div>
    `);
    replacePageBody(page, $root);
    cleanupOverviewPageHeads();
  }

  function renderLoadingState(page) {
    if (!isActiveWarehouseRoute()) return;
    ensureStyle();
    const $root = $(`
      <div class="sales-console-shell warehouse-console-shell" data-erpw-workspace="warehouse" data-erpw-console-runtime="loading" data-erpw-console-bootstrap="loading" data-erpw-overview-route-signature="${escapeHtml(overviewRouteSignature())}">
        <section class="warehouse-console-header">
          <div class="warehouse-console-header-row">
            <div>
              <h1 class="warehouse-console-title">Warehouse Console</h1>
              <div class="warehouse-console-note">Loading stock visibility and warehouse posture.</div>
            </div>
          </div>
        </section>
      </div>
    `);
    replacePageBody(page, $root);
    cleanupOverviewPageHeads();
  }

  function metricText(metric) {
    if (!metric) return "--";
    if (metric.state === "unavailable" || metric.value == null) return "N/A";
    return String(metric.value);
  }

  function metricNote(metric) {
    if (!metric) return "";
    return metric.note || metric.meta || "";
  }

  function renderKpi(metric) {
    return `
      <div class="warehouse-console-kpi-card" data-warehouse-kpi="${escapeHtml(metric.key || "")}">
        <div class="warehouse-console-kpi-label">${escapeHtml(metric.label || "")}</div>
        <div class="warehouse-console-kpi-value">${escapeHtml(metricText(metric))}</div>
        <div class="warehouse-console-kpi-meta">${escapeHtml(metricNote(metric))}</div>
      </div>
    `;
  }

  function cardValue(card) {
    if (!card) return "--";
    if (card.state === "unavailable" || card.value == null) return "N/A";
    return String(card.value);
  }

  function renderInboundCard(card) {
    return `
      <div class="warehouse-console-inbound-card" data-warehouse-inbound-card="${escapeHtml(card.key || "")}">
        <div class="warehouse-console-inbound-card-label">${escapeHtml(card.label || card.title || "")}</div>
        <div class="warehouse-console-inbound-card-value">${escapeHtml(cardValue(card))}</div>
        <div class="warehouse-console-inbound-card-note">${escapeHtml(card.note || "")}</div>
      </div>
    `;
  }

  function renderInboundPreviewRow(row) {
    return `
      <div class="warehouse-console-inbound-row" data-warehouse-inbound-preview-row="${escapeHtml(row.key || "")}">
        <div>
          <strong>${escapeHtml(row.purchase_order || row.name || "")}</strong>
          <span>${escapeHtml(row.supplier || "")}</span>
        </div>
        <span>${escapeHtml(row.target_warehouse || "")}</span>
        <span>${escapeHtml(row.age_label || row.required_date || "")}</span>
        <span>${escapeHtml(row.received_percent || "0%")}</span>
      </div>
    `;
  }

  function renderInboundOverviewPanel(inbound) {
    const payload = inbound || {};
    const cards = Array.isArray(payload.cards) ? payload.cards.slice(0, 4) : [];
    const rows = Array.isArray(payload.preview_rows) ? payload.preview_rows.slice(0, 6) : [];
    const emptyMessage = payload.state && payload.state.kind === "empty" ? payload.state.detail : "No inbound receiving needs attention.";
    return `
      <section class="warehouse-console-inbound-panel" data-warehouse-section="inbound_priority">
        <div class="warehouse-console-inbound-head">
          <div>
            <h2 class="warehouse-console-inbound-title">Inbound Work</h2>
            <div class="warehouse-console-inbound-note">Expected supplier stock due into warehouse.</div>
          </div>
          <button class="warehouse-console-inbound-open" type="button" data-warehouse-open-inbound>Open inbound receiving</button>
        </div>
        <div class="warehouse-console-inbound-cards">${cards.map(renderInboundCard).join("")}</div>
        <div class="warehouse-console-inbound-preview">
          ${rows.length ? rows.map(renderInboundPreviewRow).join("") : `<div class="warehouse-console-inbound-row"><span>${escapeHtml(emptyMessage)}</span></div>`}
        </div>
      </section>
    `;
  }

  function renderSection(section) {
    const cards = Array.isArray(section.cards) ? section.cards.slice(0, 4) : [];
    const cardMarkup = cards.length ? cards.map((card) => `
      <div class="warehouse-console-status-card" data-warehouse-card="${escapeHtml(card.key || "")}">
        <div>
          <div class="warehouse-console-status-title">${escapeHtml(card.title || "")}</div>
          <div class="warehouse-console-status-note">${escapeHtml(card.note || card.empty_message || "")}</div>
        </div>
        <div class="warehouse-console-status-value">${escapeHtml(cardValue(card))}</div>
      </div>
    `).join("") : `
      <div class="warehouse-console-status-card">
        <div>
          <div class="warehouse-console-status-title">${escapeHtml(section.empty_message || "No warehouse work needs attention right now.")}</div>
        </div>
        <div class="warehouse-console-status-value">0</div>
      </div>
    `;
    return `
      <section class="warehouse-console-section" data-warehouse-section="${escapeHtml(section.key || "")}">
        <div class="warehouse-console-section-head">
          <h2 class="warehouse-console-section-title">${escapeHtml(section.title || "")}</h2>
          <div class="warehouse-console-section-note">${escapeHtml(section.summary || "")}</div>
        </div>
        <div class="warehouse-console-card-grid">${cardMarkup}</div>
      </section>
    `;
  }

  function renderOverview(page, payload) {
    ensureStyle();
    const kpis = Array.isArray(payload.kpis) ? payload.kpis.slice(0, 6) : [];
    const sections = Array.isArray(payload.sections) ? payload.sections.slice(0, 5) : [];
    const $root = $(`
      <div class="sales-console-shell warehouse-console-shell" data-erpw-workspace="warehouse" data-erpw-console-runtime="ready" data-erpw-console-bootstrap="ready">
        <section class="warehouse-console-header">
          <div class="warehouse-console-header-row">
            <div>
              <h1 class="warehouse-console-title">Warehouse Console</h1>
              <div class="warehouse-console-note">Stock visibility, receiving posture, movement watch, and warehouse exceptions.</div>
            </div>
            <button class="warehouse-console-refresh" type="button" data-warehouse-refresh>Refresh</button>
          </div>
          <div class="warehouse-console-kpi-grid">${kpis.map(renderKpi).join("")}</div>
          ${renderInboundOverviewPanel(payload.inbound || {})}
        </section>
        <div class="warehouse-console-grid">${sections.map(renderSection).join("")}</div>
      </div>
    `);
    $root.find("[data-warehouse-refresh]").on("click", (event) => {
      event.preventDefault();
      activeOverviewRenderState = null;
      $root.remove();
      render(directRenderWrapper());
    });
    $root.find("[data-warehouse-open-inbound]").on("click", (event) => {
      event.preventDefault();
      frappe.route_options = {};
      frappe.set_route(WORKLIST_PAGE_KEY, "inbound-receiving");
    });
    replacePageBody(page, $root);
    cleanupOverviewPageHeads();
  }

  function fetchOverviewWithRetry(attempt) {
    return frappe.call({ method: OVERVIEW_METHOD }).catch((error) => {
      const nextDelay = BOOTSTRAP_RETRY_DELAYS[attempt || 0];
      if (!isActiveWarehouseRoute() || nextDelay == null) throw error;
      return new Promise((resolve) => {
        setTimeout(resolve, nextDelay);
      }).then(() => fetchOverviewWithRetry((attempt || 0) + 1));
    });
  }

  function cleanupOverviewPageHeads() {
    const route = frappe.get_route ? frappe.get_route() : [];
    const routeKey = Array.isArray(route) ? String(route[0] || "") : "";
    if (routeKey !== PAGE_KEY) return;
    document.querySelectorAll(".page-head").forEach((head) => {
      if (!(head instanceof HTMLElement)) return;
      const text = String(head.textContent || "").replace(/\s+/g, " ").trim();
      const hasManagedTitle = /Warehouse Console/i.test(text);
      if (!hasManagedTitle && (!text || text === "Actions")) {
        head.remove();
      }
    });
  }

  function rootHasWarehouseShell(root) {
    return Boolean(root && root.querySelector && root.querySelector('.sales-console-shell[data-erpw-workspace="warehouse"]'));
  }

  function cleanupDuplicateReadyShells() {
    const shells = Array.from(document.querySelectorAll('.sales-console-shell[data-erpw-workspace="warehouse"]'));
    if (shells.length <= 1) return shells[0] || null;
    shells.slice(1).forEach((shell) => shell.remove());
    removeDuplicateWarehouseHosts(shells[0] && shells[0].parentElement ? shells[0].parentElement : null);
    return shells[0] || null;
  }

  function hasReadyOverviewShell() {
    const shell = cleanupDuplicateReadyShells();
    return Boolean(shell && shell.getAttribute("data-erpw-console-runtime") === "ready" && shell.querySelector(".warehouse-console-kpi-card"));
  }

  function render(wrapper) {
    if (!isActiveWarehouseRoute()) return;
    if (hasReadyOverviewShell()) return;
    const routeSignature = overviewRouteSignature();
    const active = activeOverviewRenderState;
    if (active && active.routeSignature === routeSignature && active.root && document.body.contains(active.root)) {
      if (rootHasWarehouseShell(active.root)) return;
      activeOverviewRenderState = null;
    }
    const page = makeConsolePage(wrapper);
    renderLoadingState(page);
    const renderToken = ++overviewRenderSerial;
    activeOverviewRenderState = { routeSignature, token: renderToken, root: pageBodyElement(page) };
    ensureConsoleRuntime().then(() => fetchOverviewWithRetry(0)).then((response) => {
      if (!isActiveWarehouseRoute() || overviewRouteSignature() !== routeSignature) return;
      if (!activeOverviewRenderState || activeOverviewRenderState.token !== renderToken) return;
      const payload = response && response.message ? response.message : {};
      if (payload.state && payload.state.kind === "restricted") {
        renderState(page, payload.state);
        return;
      }
      renderOverview(page, payload);
    }).catch((error) => {
      if (!activeOverviewRenderState || activeOverviewRenderState.token !== renderToken) return;
      renderState(page, {
        kind: "error",
        title: "Warehouse Console could not be loaded",
        detail: error && error.message ? error.message : "Warehouse information could not be loaded. Refresh or try again.",
      });
    });
  }

  function directRenderWrapper() {
    return document.getElementById("body") || (frappe.container && frappe.container.page && frappe.container.page.wrapper);
  }

  function directInboundRenderWrapper() {
    const pageDef = frappe.pages && frappe.pages[WORKLIST_PAGE_KEY] ? frappe.pages[WORKLIST_PAGE_KEY] : null;
    if (pageDef && pageDef.wrapper) return pageDef.wrapper;
    return (frappe.container && frappe.container.page && frappe.container.page.wrapper) || document.getElementById("body");
  }

  function hasReadyInboundShell() {
    return Boolean(document.querySelector('.warehouse-inbound-shell[data-warehouse-view="inbound-receiving"]'));
  }

  function shouldSelfRenderInbound() {
    return isActiveInboundRoute() && !hasReadyInboundShell();
  }

  function renderActiveInboundRoute() {
    if (!shouldSelfRenderInbound()) return;
    const signature = inboundRouteSignature();
    const token = ++inboundRouteRenderSerial;
    markWarehouseDiagnostic("activeRouteGuardFired");
    const wrapper = directInboundRenderWrapper();
    if (!wrapper) return;
    window.setTimeout(() => {
      if (token !== inboundRouteRenderSerial || !shouldSelfRenderInbound() || inboundRouteSignature() !== signature) return;
      renderInboundQueue(wrapper);
    }, 0);
  }

  function scheduleActiveInboundRender() {
    renderActiveInboundRoute();
    setTimeout(renderActiveInboundRoute, 80);
    setTimeout(renderActiveInboundRoute, 220);
    setTimeout(renderActiveInboundRoute, 700);
  }

  function bindActiveInboundGuard() {
    if (inboundRouteGuardBound || !window || typeof window.setInterval !== "function") return;
    inboundRouteGuardBound = true;
    window.setInterval(() => {
      if (shouldSelfRenderInbound()) renderActiveInboundRoute();
    }, 220);
  }

  function shouldSelfRenderOverview() {
    if (!isActiveWarehouseRoute()) return false;
    const shell = document.querySelector('.sales-console-shell[data-erpw-workspace="warehouse"]');
    if (!shell) return true;
    const runtimeState = shell.getAttribute("data-erpw-console-runtime") || "";
    const bootstrapState = shell.getAttribute("data-erpw-console-bootstrap") || "";
    if (runtimeState === "loading" || bootstrapState === "loading") return false;
    return !document.querySelector(".warehouse-console-kpi-card");
  }

  function renderActiveOverviewRoute() {
    if (!shouldSelfRenderOverview()) return;
    const wrapper = directRenderWrapper();
    if (!wrapper) return;
    render(wrapper);
  }

  function scheduleActiveOverviewRender() {
    renderActiveOverviewRoute();
    setTimeout(renderActiveOverviewRoute, 80);
    setTimeout(renderActiveOverviewRoute, 220);
    setTimeout(renderActiveOverviewRoute, 700);
  }

  function bindActiveOverviewGuard() {
    if (activeOverviewGuardBound || !window || typeof window.setInterval !== "function") return;
    activeOverviewGuardBound = true;
    window.setInterval(() => {
      if (shouldSelfRenderOverview()) renderActiveOverviewRoute();
    }, 220);
  }

  function collectInboundFilters($host) {
    const values = {};
    $host.find("[data-warehouse-filter-key]").each(function () {
      const key = String(this.getAttribute("data-warehouse-filter-key") || "").trim();
      const value = String($(this).val() || "").trim();
      if (key && value) values[key] = value;
    });
    return values;
  }

  function controlField(field) {
    const value = escapeHtml(field.value || "");
    if (field.type === "select") {
      const options = Array.isArray(field.options) ? field.options : [];
      return `
        <div class="warehouse-inbound-field" data-warehouse-inbound-filter-field="${escapeHtml(field.key || "")}">
          <label>${escapeHtml(field.label || "")}</label>
          <select data-warehouse-filter-key="${escapeHtml(field.key || "")}">
            ${options.map((option) => `<option value="${escapeHtml(option.value || "")}"${String(option.value || "") === String(field.value || "") ? " selected" : ""}>${escapeHtml(option.label || "")}</option>`).join("")}
          </select>
        </div>
      `;
    }
    return `
      <div class="warehouse-inbound-field" data-warehouse-inbound-filter-field="${escapeHtml(field.key || "")}">
        <label>${escapeHtml(field.label || "")}</label>
        <input type="text" value="${value}" placeholder="${escapeHtml(field.placeholder || "")}" data-warehouse-filter-key="${escapeHtml(field.key || "")}" />
      </div>
    `;
  }

  function renderQueueCard(card) {
    return `
      <div class="warehouse-inbound-queue-card" data-warehouse-inbound-queue-card="${escapeHtml(card.key || "")}">
        <div class="warehouse-inbound-queue-card-label">${escapeHtml(card.label || card.title || "")}</div>
        <div class="warehouse-inbound-queue-card-value">${escapeHtml(cardValue(card))}</div>
        <div class="warehouse-inbound-queue-card-note">${escapeHtml(card.note || "")}</div>
      </div>
    `;
  }

  function renderQueueRow(row) {
    const lines = Array.isArray(row.lines) ? row.lines : [];
    return `
      <article class="warehouse-inbound-row" data-warehouse-inbound-row="${escapeHtml(row.key || "")}">
        <div class="warehouse-inbound-row-main">
          <div>
            <div class="warehouse-inbound-order">${escapeHtml(row.purchase_order || row.name || "")}</div>
            <div class="warehouse-inbound-meta">${escapeHtml(row.supplier || "")}</div>
          </div>
          <div class="warehouse-inbound-meta">${escapeHtml(row.target_warehouse || "")}</div>
          <div class="warehouse-inbound-meta">${escapeHtml(row.age_label || row.required_date || "")}</div>
          <div class="warehouse-inbound-meta">${escapeHtml(row.remaining_summary || "")} · ${escapeHtml(row.received_percent || "0%")}</div>
          <button type="button" class="warehouse-inbound-queue-button" data-warehouse-row-toggle>View lines</button>
        </div>
        <div class="warehouse-inbound-lines">
          ${lines.length ? lines.map((line) => `
            <div class="warehouse-inbound-line">
              <span>${escapeHtml(line.item_code || "")} ${escapeHtml(line.item_name || "")}</span>
              <span>${escapeHtml(line.remaining_qty || "")} ${escapeHtml(line.uom || "")}</span>
              <span>${escapeHtml(line.target_warehouse || "")}</span>
            </div>
          `).join("") : `<div class="warehouse-inbound-line"><span>No item line details available.</span></div>`}
        </div>
      </article>
    `;
  }

  function renderQueueGroup(group) {
    const rows = Array.isArray(group.rows) ? group.rows : [];
    return `
      <section class="warehouse-inbound-group" data-warehouse-inbound-group="${escapeHtml(group.key || "")}">
        <div class="warehouse-inbound-group-head">
          <h2 class="warehouse-inbound-group-title">${escapeHtml(group.title || "")}</h2>
          <div class="warehouse-inbound-group-note">${escapeHtml(rows.length ? `${rows.length} shown` : group.summary || "")}</div>
        </div>
        <div class="warehouse-console-card-grid">
          ${rows.length ? rows.map(renderQueueRow).join("") : `<div class="warehouse-inbound-row" data-warehouse-inbound-empty><span class="warehouse-inbound-meta">No receiving matches these filters.</span></div>`}
        </div>
      </section>
    `;
  }

  function makeInboundPage(wrapper) {
    const existing = wrapper && wrapper.__erpwWarehouseInboundQueue;
    if (existing && existing.page && existing.$host && document.documentElement.contains(existing.$host.get(0))) {
      return existing;
    }
    const page = frappe.ui.make_app_page({
      parent: wrapper,
      title: "Inbound Receiving",
      single_column: true,
    });
    const $parent = page && page.body ? $(page.body) : $(wrapper);
    const $host = $('<section class="warehouse-inbound-route"></section>');
    $parent.empty().append($host);
    const state = { page, $host, activeFilters: {} };
    wrapper.__erpwWarehouseInboundQueue = state;
    return state;
  }

  function renderInboundQueuePayload(viewState, payload) {
    ensureStyle();
    const controls = payload.controls || {};
    const fields = Array.isArray(controls.fields) ? controls.fields : [];
    const cards = Array.isArray(payload.cards) ? payload.cards : [];
    const groups = Array.isArray(payload.groups) ? payload.groups : [];
    const statePayload = payload.state || {};
    const $root = $(`
      <div class="sales-console-shell warehouse-inbound-shell" data-erpw-workspace="warehouse" data-warehouse-view="inbound-receiving" data-erpw-console-runtime="ready">
        <section class="warehouse-inbound-queue-header">
          <div class="warehouse-inbound-queue-head">
            <div>
              <h1 class="warehouse-inbound-queue-title">${escapeHtml(payload.summary && payload.summary.title || "Inbound Receiving")}</h1>
              <div class="warehouse-inbound-queue-note">${escapeHtml(payload.summary && payload.summary.subtitle || "Expected supplier stock due into warehouse.")}</div>
            </div>
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-back-overview>Open Warehouse page</button>
          </div>
          <div class="warehouse-inbound-queue-cards">${cards.map(renderQueueCard).join("")}</div>
          <div class="warehouse-inbound-controls">
            ${fields.map(controlField).join("")}
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-apply>Apply</button>
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-reset>Reset</button>
            <button type="button" class="warehouse-inbound-queue-button" data-warehouse-filter-refresh>Refresh</button>
          </div>
        </section>
        <div class="warehouse-inbound-groups">
          ${statePayload.kind === "restricted" || statePayload.kind === "error"
            ? `<section class="warehouse-inbound-group" data-warehouse-inbound-group="state"><h2 class="warehouse-inbound-group-title">${escapeHtml(statePayload.title || "Inbound receiving unavailable")}</h2><div class="warehouse-inbound-meta" data-warehouse-inbound-empty>${escapeHtml(statePayload.detail || "Receiving work could not be loaded. Refresh or contact an administrator.")}</div></section>`
            : groups.map(renderQueueGroup).join("")}
        </div>
      </div>
    `);
    $root.find("[data-warehouse-back-overview]").on("click", (event) => {
      event.preventDefault();
      frappe.set_route(PAGE_KEY);
    });
    $root.find("[data-warehouse-filter-apply]").on("click", (event) => {
      event.preventDefault();
      viewState.activeFilters = collectInboundFilters($root);
      loadInboundQueue(viewState);
    });
    $root.find("[data-warehouse-filter-reset]").on("click", (event) => {
      event.preventDefault();
      viewState.activeFilters = {};
      loadInboundQueue(viewState);
    });
    $root.find("[data-warehouse-filter-refresh]").on("click", (event) => {
      event.preventDefault();
      loadInboundQueue(viewState);
    });
    $root.find("[data-warehouse-row-toggle]").on("click", function (event) {
      event.preventDefault();
      $(this).closest("[data-warehouse-inbound-row]").toggleClass("is-expanded");
    });
    removeDuplicateWarehouseHosts(viewState.$host.get(0));
    viewState.$host.empty().append($root);
  }

  function renderInboundLoading(viewState) {
    renderInboundQueuePayload(viewState, {
      summary: { title: "Inbound Receiving", subtitle: "Checking inbound work..." },
      controls: { fields: [], actions: [] },
      cards: [],
      groups: [],
      state: { kind: "loading", title: "Checking inbound work", detail: "Checking inbound work..." },
    });
  }

  function loadInboundQueue(viewState) {
    markWarehouseDiagnostic("queueServiceCallAttempted");
    renderInboundLoading(viewState);
    return frappe.call({
      method: INBOUND_METHOD,
      args: { queue_key: INBOUND_QUEUE_KEY, filters: viewState.activeFilters || {} },
    }).then((response) => {
      renderInboundQueuePayload(viewState, response && response.message ? response.message : {});
    }).catch(() => {
      renderInboundQueuePayload(viewState, {
        summary: { title: "Inbound Receiving", subtitle: "Receiving work could not be loaded. Refresh or contact an administrator." },
        controls: { fields: [], actions: [{ key: "refresh", label: "Refresh" }] },
        cards: [],
        groups: [],
        state: { kind: "error", title: "Inbound receiving unavailable", detail: "Receiving work could not be loaded. Refresh or contact an administrator." },
      });
    });
  }

  function renderInboundQueue(wrapper) {
    markWarehouseDiagnostic("renderInboundQueueEntered");
    const viewState = makeInboundPage(wrapper);
    if (window.erpWorkspaceConsoleSidebar && typeof window.erpWorkspaceConsoleSidebar.refresh === "function") {
      window.erpWorkspaceConsoleSidebar.refresh();
    }
    loadInboundQueue(viewState);
  }

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].__erpwWarehouseConsoleRenderer = true;
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) { render(wrapper); };
  frappe.pages[PAGE_KEY].on_page_show = function (wrapper) {
    if (window.erpWorkspaceConsoleSidebar && typeof window.erpWorkspaceConsoleSidebar.refresh === "function") {
      window.erpWorkspaceConsoleSidebar.refresh();
    }
    render(wrapper);
  };
  const warehouseConsoleApi = window.erpWorkspaceWarehouseConsole = window.erpWorkspaceWarehouseConsole || {};
  warehouseConsoleApi.renderInboundQueue = renderInboundQueue;
  warehouseConsoleApi.renderOverview = render;
  warehouseConsoleApi.diagnostics = warehouseConsoleApi.diagnostics || {};
  warehouseConsoleApi.diagnostics.exportedRendererReady = true;

  frappe.pages[WORKLIST_PAGE_KEY] = frappe.pages[WORKLIST_PAGE_KEY] || {};
  frappe.pages[WORKLIST_PAGE_KEY].__erpwWarehouseInboundRenderer = true;
  frappe.pages[WORKLIST_PAGE_KEY].__erpwRenderWarehouseInboundQueue = renderInboundQueue;
  frappe.pages[WORKLIST_PAGE_KEY].on_page_load = function (wrapper) { renderInboundQueue(wrapper); };
  frappe.pages[WORKLIST_PAGE_KEY].on_page_show = function (wrapper) { renderInboundQueue(wrapper); };
  scheduleActiveOverviewRender();
  bindActiveOverviewGuard();
  scheduleActiveInboundRender();
  bindActiveInboundGuard();
})();
