/* global frappe, $ */

(function () {
  const workspaceRegistry = window.erpWorkspaceUiWorkspaceRegistry || {};
  const warehouseWorkspace = typeof workspaceRegistry.warehouse === "function" ? workspaceRegistry.warehouse() : null;
  const warehouseRoutes = warehouseWorkspace && warehouseWorkspace.routes ? warehouseWorkspace.routes : {};
  const warehouseMethods = warehouseWorkspace && warehouseWorkspace.methods ? warehouseWorkspace.methods : {};
  const PAGE_KEY = warehouseRoutes.home || "warehouse-console";
  const OVERVIEW_METHOD = warehouseMethods.overview || "erp_workspace_ui.warehouse_console.service.get_warehouse_console_overview";
  const CONSOLE_RUNTIME_URL = "/assets/erp_workspace_ui/js/runtime/console/workspace_console_runtime.js";
  const BOOTSTRAP_RETRY_DELAYS = [350, 900, 1800];
  let consoleRuntimePromise = null;
  let overviewRenderSerial = 0;
  let activeOverviewRenderState = null;
  let activeOverviewGuardBound = false;

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
      }
      @media (max-width: 900px) {
        .warehouse-console-header-row,
        .warehouse-console-grid {
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

  function replacePageBody(page, $content) {
    const body = pageBodyElement(page);
    if (!body) return;
    body.innerHTML = "";
    $content.each((index, node) => body.appendChild(node));
  }

  function makeConsolePage(wrapper) {
    const $parent = $(wrapper);
    if (wrapper && wrapper.id === "body") {
      let $host = $parent.find('.erpw-direct-warehouse-page[data-erpw-page-key="warehouse-console"]').first();
      if (!$host.length) {
        $host = $('<div class="erpw-direct-warehouse-page" data-erpw-page-key="warehouse-console"></div>').appendTo($parent);
      }
      if (!$host.find(".erpw-direct-warehouse-body").length) {
        $host.append('<main class="layout-main-section erpw-direct-warehouse-body"></main>');
      }
      return {
        body: $host.find(".erpw-direct-warehouse-body").first().get(0),
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

  function hasReadyOverviewShell() {
    const shell = document.querySelector('.sales-console-shell[data-erpw-workspace="warehouse"]');
    return Boolean(shell && shell.getAttribute("data-erpw-console-runtime") === "ready" && document.querySelector(".warehouse-console-kpi-card"));
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
      const payload = response && response.message ? response.message : {};
      if (payload.state && payload.state.kind === "restricted") {
        renderState(page, payload.state);
        return;
      }
      renderOverview(page, payload);
    }).catch((error) => {
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

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].__erpwWarehouseConsoleRenderer = true;
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) { render(wrapper); };
  frappe.pages[PAGE_KEY].on_page_show = function (wrapper) {
    if (window.erpWorkspaceConsoleSidebar && typeof window.erpWorkspaceConsoleSidebar.refresh === "function") {
      window.erpWorkspaceConsoleSidebar.refresh();
    }
    render(wrapper);
  };
  scheduleActiveOverviewRender();
  bindActiveOverviewGuard();
})();
