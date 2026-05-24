/* global frappe, $ */

(function () {
  const workspaceRegistry = window.erpWorkspaceUiWorkspaceRegistry || {};
  const procurementWorkspace = typeof workspaceRegistry.procurement === "function" ? workspaceRegistry.procurement() : null;
  const procurementRoutes = procurementWorkspace && procurementWorkspace.routes ? procurementWorkspace.routes : {};
  const procurementMethods = procurementWorkspace && procurementWorkspace.methods ? procurementWorkspace.methods : {};
  const PAGE_KEY = procurementRoutes.home || "procurement-console";
  const WORKLIST_ROUTE = procurementRoutes.worklist || "procurement-console-worklist";
  const REPORT_ROUTE = procurementRoutes.report || "procurement-console-report";
  const BOOTSTRAP_METHOD = procurementMethods.bootstrap || "erp_workspace_ui.procurement_console.service.get_procurement_console_bootstrap";
  const READINESS_METHOD = procurementMethods.manager_readiness || "erp_workspace_ui.procurement_console.readiness.get_procurement_manager_readiness";
  const QUICK_FIND_METHOD = procurementMethods.quickFind || procurementMethods.quick_find || "erp_workspace_ui.procurement_console.service.get_procurement_quick_find_suggestions";
  const QUICK_FIND_DEBOUNCE_MS = 240;
  const CONSOLE_RUNTIME_URL = "/assets/erp_workspace_ui/js/runtime/console/workspace_console_runtime.js";
  const READINESS_UI_URL = "/assets/erp_workspace_ui/js/procurement_console/procurement_readiness_ui.js";
  const BOOTSTRAP_RETRY_DELAYS = [350, 900, 1800];
  let consoleRuntimePromise = null;
  let activeOverviewGuardBound = false;
  let overviewRenderSerial = 0;
  let activeOverviewRenderState = null;
  function consoleRuntime() {
    return window.erpWorkspaceConsoleRuntime || {};
  }

  function runtimeMethod(name) {
    const method = consoleRuntime()[name];
    if (typeof method === "function") return method;
    throw new Error("Procurement Console runtime is missing method: " + name);
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

  function hasReadinessUi() {
    const readiness = window.erpWorkspaceUiProcurementReadiness || {};
    return typeof readiness.renderManagerReadiness === "function" && typeof readiness.bindReadinessLinks === "function";
  }

  function hasConsoleRuntime() {
    const runtime = consoleRuntime();
    return Boolean(runtime && typeof runtime.makeInsightCard === "function" && typeof runtime.makeAction === "function" && typeof runtime.makeQueueItem === "function" && hasReadinessUi());
  }

  function ensureConsoleRuntime() {
    if (hasConsoleRuntime()) return Promise.resolve(consoleRuntime());
    if (consoleRuntimePromise) return consoleRuntimePromise;
    consoleRuntimePromise = new Promise((resolve, reject) => {
      frappe.require(CONSOLE_RUNTIME_URL, () => {
        frappe.require(READINESS_UI_URL, () => {
          if (hasConsoleRuntime()) {
            resolve(consoleRuntime());
            return;
          }
          reject(new Error("Shared console runtime is not loaded on this page."));
        });
      });
    }).catch((error) => {
      consoleRuntimePromise = null;
      throw error;
    });
    return consoleRuntimePromise;
  }

  function fallbackToManagedRoute(pageKey, slug, shellSelector) {
    setTimeout(() => {
      const route = frappe.get_route ? frappe.get_route() : [];
      const activePage = Array.isArray(route) ? String(route[0] || "") : "";
      const activeSlug = Array.isArray(route) ? String(route[1] || "") : "";
      if (activePage !== pageKey || activeSlug !== slug || document.querySelector(shellSelector)) return;
      window.location.href = `/desk/${pageKey}/${slug}`;
    }, 900);
  }

  function routeToWorklist(queueKey, filters) {
    const slug = String(queueKey || "").replace(/_/g, "-");
    frappe.route_options = filters && Object.keys(filters).length ? filters : {};
    frappe.set_route(WORKLIST_ROUTE, slug);
    fallbackToManagedRoute(WORKLIST_ROUTE, slug, ".erpw-list-shell");
  }

  function routeToReport(reportKey, filters) {
    const slug = String(reportKey || "").replace(/_/g, "-");
    frappe.route_options = filters && Object.keys(filters).length ? filters : {};
    frappe.set_route(REPORT_ROUTE, slug);
    fallbackToManagedRoute(REPORT_ROUTE, slug, ".erpw-report-shell");
  }

  function pathRouteParts() {
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

  function overviewRouteSignature() {
    const pathRoute = pathRouteParts();
    if (Array.isArray(pathRoute) && String(pathRoute[0] || "") === PAGE_KEY) return pathRoute.join("|");
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) ? route.join("|") : "";
  }

  function isActiveProcurementRoute() {
    const pathRoute = pathRouteParts();
    if (String(pathRoute[0] || "") === PAGE_KEY) return true;
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) && String(route[0] || "") === PAGE_KEY;
  }

  function executeTarget(target) {
    if (!target) return;
    if (target.kind === "worklist" && target.queue_key) return routeToWorklist(target.queue_key, target.filters || null);
    if (target.kind === "report_page" && target.report_key) return routeToReport(target.report_key, target.filters || null);
    if (target.kind === "page" && target.route) {
      frappe.route_options = target.options || {};
      const parts = [target.route].concat(Array.isArray(target.route_parts) ? target.route_parts : []);
      return frappe.set_route.apply(frappe, parts);
    }
  }

  function makeInsightCard(config) {
    return runtimeMethod("makeInsightCard")(config);
  }

  function makeAction(config) {
    return runtimeMethod("makeAction")(config);
  }

  function makeQueueItem(config) {
    return runtimeMethod("makeQueueItem")(config);
  }

  function applyMetric($root, key, metric) {
    runtimeMethod("applyQueueMetric")($root, key, metric);
    runtimeMethod("applyInsightMetric")($root, key, metric);
  }

  function renderState(page, state) {
    const payloadState = state || {};
    const $root = $(`
      <div class="sales-console-shell" data-erpw-workspace="procurement" data-procurement-console-state="${escapeHtml(payloadState.kind || "unavailable")}">
        <section class="sales-console-card sales-console-section">
          <div class="sales-console-section-head">
            <h2 class="sales-console-section-title">${escapeHtml(payloadState.title || "Procurement Console unavailable")}</h2>
            <div class="sales-console-section-note">Workspace state</div>
          </div>
          <div class="sales-console-inquiry-placeholder">${escapeHtml(payloadState.detail || "This workspace is not available right now.")}</div>
        </section>
      </div>
    `);
    replacePageBody(page, $root);
  }

  function pageBodyElement(page) {
    if (page && page.body) {
      if (page.body.nodeType) return page.body;
      if (page.body.jquery && page.body[0]) return page.body[0];
    }
    return document.querySelector(".erpw-direct-console-body");
  }

  function replacePageBody(page, $content) {
    const body = pageBodyElement(page);
    if (!body) return;
    body.innerHTML = "";
    $content.each((index, node) => {
      body.appendChild(node);
    });
  }

  function renderLoadingState(page) {
    if (!isActiveProcurementRoute()) return;
    const $root = $(`
      <div class="sales-console-shell" data-erpw-workspace="procurement" data-erpw-console-runtime="loading" data-erpw-console-bootstrap="loading" data-erpw-overview-route-signature="${escapeHtml(overviewRouteSignature())}">
        <section class="sales-console-card sales-console-header">
          <div class="sales-console-header-row">
            <div class="sales-console-header-copy">
              <h1 class="sales-console-title">Procurement Console</h1>
              <div class="sales-console-header-note">Loading the buyer workbench.</div>
            </div>
          </div>
        </section>
      </div>
    `);
    replacePageBody(page, $root);
    pruneRouteShells($root.get(0));
    cleanupOverviewPageHeads();
  }

  function makeFallbackPage(wrapper) {
    const $parent = $(wrapper);
    if (wrapper && wrapper.id === "body") {
      let $host = $parent.find('.erpw-direct-console-page[data-erpw-page-key="procurement-console"]').first();
      if (!$host.length) {
        $host = $('<div class="erpw-direct-console-page" data-erpw-page-key="procurement-console"></div>').appendTo($parent);
      }
      if (!$host.find(".erpw-direct-console-body").length) {
        $host.append('<main class="layout-main-section erpw-direct-console-body"></main>');
      }
      return {
        body: $host.find(".erpw-direct-console-body").first().get(0),
        set_title(title) {
          document.title = title || "Procurement Console";
        },
      };
    }
    $parent.empty().append(`
      <div class="erpw-direct-console-page">
        <main class="layout-main-section erpw-direct-console-body"></main>
      </div>
    `);
    return {
      body: $parent.find(".erpw-direct-console-body").first().get(0),
      set_title(title) {
        document.title = title || "Procurement Console";
      },
    };
  }

  function makeConsolePage(wrapper) {
    if (wrapper && wrapper.id === "body") return makeFallbackPage(wrapper);
    try {
      return frappe.ui.make_app_page({
        parent: wrapper,
        title: "Procurement Console",
        single_column: true,
      });
    } catch (error) {
      return makeFallbackPage(wrapper);
    }
  }

  function readinessUi() {
    return window.erpWorkspaceUiProcurementReadiness || {};
  }

  function canSeeManagerReadiness(payload) {
    const context = (payload && payload.context) || {};
    const variant = String(context.role_variant || "");
    const roles = Array.isArray(context.roles) ? context.roles : [];
    return variant === "purchase_manager" || variant === "purchase_master_manager" || roles.indexOf("Purchase Manager") !== -1 || roles.indexOf("Purchase Master Manager") !== -1;
  }

  function isCurrentOverviewRoot($root, token) {
    return token === overviewRenderSerial && isActiveProcurementRoute() && $root && $root.length && document.body.contains($root.get(0));
  }

  function insertManagerReadinessSection($root, $section) {
    $root.find("[data-procurement-manager-readiness]").remove();
    if (!$section || !$section.length) return;
    let $anchor = $root.find('[data-procurement-quick-find]').first();
    if (!$anchor.length) {
      $anchor = $root.find('[data-section-key="create-actions"]').first();
    }
    if ($anchor.length) {
      $anchor.after($section);
    } else {
      $root.append($section);
    }
    const ui = readinessUi();
    if (typeof ui.bindReadinessLinks === "function") ui.bindReadinessLinks($section);
  }

  function renderManagerReadinessLoading($root) {
    const ui = readinessUi();
    if (typeof ui.renderManagerReadinessLoading !== "function") return;
    insertManagerReadinessSection($root, $(ui.renderManagerReadinessLoading()));
  }

  function renderManagerReadinessError($root, error) {
    const ui = readinessUi();
    if (typeof ui.renderManagerReadinessError !== "function") return;
    const message = error && error.message ? error.message : "Readiness review could not be loaded right now.";
    insertManagerReadinessSection($root, $(ui.renderManagerReadinessError(message)));
  }

  function renderManagerReadinessPayload($root, readiness) {
    const ui = readinessUi();
    if (typeof ui.renderManagerReadiness !== "function") return;
    const html = ui.renderManagerReadiness(readiness);
    if (!html) {
      $root.find("[data-procurement-manager-readiness]").remove();
      return;
    }
    insertManagerReadinessSection($root, $(html));
  }

  function loadManagerReadiness($root, payload, token) {
    if (!canSeeManagerReadiness(payload)) {
      $root.find("[data-procurement-manager-readiness]").remove();
      return;
    }
    renderManagerReadinessLoading($root);
    const startedAt = Date.now();
    frappe.call({ method: READINESS_METHOD }).then((response) => {
      if (!isCurrentOverviewRoot($root, token)) return;
      const readiness = response && response.message ? response.message : {};
      renderManagerReadinessPayload($root, readiness);
      const $section = $root.find("[data-procurement-manager-readiness]").first();
      if ($section.length) {
        $section.attr("data-procurement-manager-readiness-fetch-ms", String(Date.now() - startedAt));
      }
    }).catch((error) => {
      if (!isCurrentOverviewRoot($root, token)) return;
      renderManagerReadinessError($root, error);
    });
  }


  function renderQuickFindSection() {
    const $section = $(`
      <section class="sales-console-card sales-console-section erpw-procurement-quick-find" data-procurement-quick-find>
        <div class="sales-console-section-head erpw-procurement-quick-find-head">
          <div>
            <h2 class="sales-console-section-title">Quick Find</h2>
            <div class="erpw-procurement-quick-find-subtitle">Locate a visible procurement record, preview it, then open the productized page.</div>
          </div>
          <div class="sales-console-section-note">Preview before opening</div>
        </div>
        <div class="erpw-procurement-quick-find-body">
          <div class="erpw-procurement-quick-find-search">
            <label class="sr-only" for="erpw-procurement-quick-find-input">Find supplier, item, request, RFQ, quotation, order, or report</label>
            <input id="erpw-procurement-quick-find-input" class="erpw-procurement-quick-find-input" data-procurement-quick-find-input type="search" autocomplete="off" spellcheck="false" placeholder="Find supplier, item, request, RFQ, quotation, order, or report" aria-controls="erpw-procurement-quick-find-suggestions" aria-expanded="false" />
            <button type="button" class="erpw-procurement-quick-find-clear" data-procurement-quick-find-clear hidden>Clear</button>
          </div>
          <div id="erpw-procurement-quick-find-suggestions" class="erpw-procurement-quick-find-suggestions" data-procurement-quick-find-suggestions role="listbox" hidden></div>
          <div class="erpw-procurement-quick-find-status" data-procurement-quick-find-status>Type at least 2 characters to search visible Procurement records.</div>
          <div class="erpw-procurement-quick-find-preview" data-procurement-quick-find-preview hidden></div>
        </div>
      </section>
    `);
    bindQuickFind($section);
    return $section;
  }

  function bindQuickFind($section) {
    const $input = $section.find("[data-procurement-quick-find-input]").first();
    const $clear = $section.find("[data-procurement-quick-find-clear]").first();
    let timer = null;
    let requestSerial = 0;
    const state = { results: [], selected: null };

    function resetPreview() {
      state.selected = null;
      $section.data("erpwQuickFindSelected", null);
      $section.find("[data-procurement-quick-find-preview]").attr("hidden", "hidden").empty();
    }

    function closeSuggestions() {
      $section.find("[data-procurement-quick-find-suggestions]").attr("hidden", "hidden").empty();
      $input.attr("aria-expanded", "false");
    }

    function setStatus(message, mode) {
      $section.find("[data-procurement-quick-find-status]").attr("data-state", mode || "idle").text(message || "");
    }

    function renderSuggestions(payload) {
      const groups = Array.isArray(payload && payload.groups) ? payload.groups : [];
      const $panel = $section.find("[data-procurement-quick-find-suggestions]").first();
      $panel.empty();
      state.results = [];
      groups.forEach((group) => {
        const results = Array.isArray(group.results) ? group.results : [];
        if (!results.length) return;
        state.results = state.results.concat(results);
        const $group = $(`<div class="erpw-procurement-quick-find-group" data-procurement-quick-find-group="${escapeHtml(group.key || "")}"></div>`);
        $group.append(`<div class="erpw-procurement-quick-find-group-label">${escapeHtml(group.label || group.key || "Results")}</div>`);
        results.forEach((result) => {
          const $option = $(`
            <button type="button" class="erpw-procurement-quick-find-option" role="option" data-procurement-quick-find-option data-result-id="${escapeHtml(result.id || "")}" data-result-type="${escapeHtml(result.result_type || "")}">
              <span class="erpw-procurement-quick-find-option-type">${escapeHtml(result.group || result.result_type || "Result")}</span>
              <span class="erpw-procurement-quick-find-option-main">${escapeHtml(result.title || result.label || result.name || "Untitled")}</span>
              <span class="erpw-procurement-quick-find-option-meta">${escapeHtml(result.subtitle || result.meta || "Productized Procurement result")}</span>
            </button>
          `);
          $option.on("click", () => selectQuickFindResult($section, state, result));
          $group.append($option);
        });
        $panel.append($group);
      });
      if (state.results.length) {
        $panel.removeAttr("hidden");
        $input.attr("aria-expanded", "true");
      } else {
        closeSuggestions();
      }
    }

    function runSearch() {
      const query = String($input.val() || "").trim();
      $clear.prop("hidden", !query);
      resetPreview();
      if (query.length < 2) {
        state.results = [];
        closeSuggestions();
        setStatus("Type at least 2 characters to search visible Procurement records.", "idle");
        return;
      }
      const serial = ++requestSerial;
      setStatus("Searching visible Procurement records...", "loading");
      frappe.call({ method: QUICK_FIND_METHOD, args: { query, limit: 12 } }).then((response) => {
        if (serial !== requestSerial || !$section.get(0).isConnected || !isActiveProcurementRoute()) return;
        const payload = response && response.message ? response.message : {};
        if (payload.state === "ready") {
          setStatus(payload.message || "Results ready. Select a result to preview before opening.", "ready");
          renderSuggestions(payload);
        } else {
          state.results = [];
          closeSuggestions();
          setStatus(payload.message || "No visible Procurement records match this search.", payload.state || "empty");
        }
      }).catch((error) => {
        if (serial !== requestSerial || !$section.get(0).isConnected) return;
        state.results = [];
        closeSuggestions();
        setStatus(error && error.message ? error.message : "Quick Find could not search right now.", "error");
      });
    }

    $input.on("input", () => {
      if (timer) window.clearTimeout(timer);
      timer = window.setTimeout(runSearch, QUICK_FIND_DEBOUNCE_MS);
    });
    $input.on("keydown", (event) => {
      if (event.key === "Escape") {
        closeSuggestions();
        event.preventDefault();
      }
      if (event.key === "Enter") {
        event.preventDefault();
      }
    });
    $clear.on("click", () => {
      $input.val("");
      $clear.prop("hidden", true);
      state.results = [];
      closeSuggestions();
      resetPreview();
      setStatus("Type at least 2 characters to search visible Procurement records.", "idle");
      $input.trigger("focus");
    });
  }

  function selectQuickFindResult($section, state, result) {
    state.selected = result;
    $section.data("erpwQuickFindSelected", result);
    $section.find("[data-procurement-quick-find-suggestions]").attr("hidden", "hidden");
    $section.find("[data-procurement-quick-find-input]").attr("aria-expanded", "false");
    renderQuickFindPreview($section, result);
  }

  function renderQuickFindPreview($section, result) {
    const preview = (result && result.preview) || {};
    const facts = Array.isArray(preview.facts) ? preview.facts : [];
    const chips = Array.isArray(preview.chips) ? preview.chips : [];
    const actionLabel = preview.primary_action_label || result.primary_action_label || "Open";
    const $preview = $section.find("[data-procurement-quick-find-preview]").first();
    $preview.empty().removeAttr("hidden");
    const $facts = facts.length ? $("<dl class=\"erpw-procurement-quick-find-facts\"></dl>") : $("<div></div>");
    facts.forEach((fact) => {
      $facts.append(`<div><dt>${escapeHtml(fact.label || "Fact")}</dt><dd>${escapeHtml(fact.value || "-")}</dd></div>`);
    });
    const chipHtml = chips.map((chip) => `<span class="erpw-procurement-quick-find-chip">${escapeHtml(chip)}</span>`).join("");
    $preview.append(`
      <div class="erpw-procurement-quick-find-preview-copy">
        <div class="erpw-procurement-quick-find-preview-kicker">${escapeHtml(result.group || "Procurement result")}</div>
        <h3 class="erpw-procurement-quick-find-preview-title">${escapeHtml(preview.title || result.title || result.label || result.name || "Selected result")}</h3>
        <div class="erpw-procurement-quick-find-preview-subtitle">${escapeHtml(preview.subtitle || result.subtitle || "Productized Procurement destination")}</div>
        <div class="erpw-procurement-quick-find-chip-row">${chipHtml}</div>
      </div>
    `);
    $preview.append($facts);
    $preview.append(`
      <div class="erpw-procurement-quick-find-preview-action">
        <div class="erpw-procurement-quick-find-boundary">${escapeHtml(preview.boundary_note || "Productized Procurement route only.")}</div>
        <button type="button" class="erpw-procurement-quick-find-open" data-procurement-quick-find-open>${escapeHtml(actionLabel)}</button>
      </div>
    `);
    $preview.find("[data-procurement-quick-find-open]").on("click", () => {
      const selected = $section.data("erpwQuickFindSelected") || result;
      executeTarget((selected.preview && selected.preview.target) || selected.target);
    });
    $section.find("[data-procurement-quick-find-status]").attr("data-state", "preview").text("Preview selected. Use Open to navigate.");
  }

  function applyPayload($root, payload) {
    const work = (payload && payload.work) || {};
    const directories = (payload && payload.directories) || {};
    const insights = (payload && payload.insights) || {};
    Object.keys(work).forEach((key) => applyMetric($root, key, work[key]));
    Object.keys(directories).forEach((key) => applyMetric($root, key, directories[key]));
    Object.keys(insights).forEach((key) => applyMetric($root, key, insights[key]));
    renderCreateActions($root, payload);
  }

  function renderCreateActions($root, payload) {
    const actions = Array.isArray(payload && payload.create_actions) ? payload.create_actions : [];
    const targets = (payload && payload.action_targets) || {};
    const $section = $root.find('[data-section-key="create-actions"]').first();
    const $grid = $section.find('[data-section-grid="create-actions"]').first();
    $grid.empty().append(`
      <div class="sales-console-action-strip primary"></div>
      <div class="sales-console-action-strip secondary" hidden></div>
    `);
    if (!actions.length) {
      $section.attr("hidden", "hidden");
      return;
    }
    $section.removeAttr("hidden");
    const $primary = $grid.find(".sales-console-action-strip.primary").first();
    const $secondary = $grid.find(".sales-console-action-strip.secondary").first();
    actions.forEach((action) => {
      const variant = action.variant === "primary" ? "primary" : "secondary";
      const isPrimary = variant === "primary";
      const $button = makeAction({
        key: action.key || "",
        title: action.title || action.label || action.key,
        meta: action.note || "Open the governed ERPNext form.",
        icon: "square",
        primary: isPrimary,
        tier: variant,
        onClick: () => executeTarget(targets[action.key]),
      });
      $button.attr("data-erpw-procurement-create-action", action.key || "");
      $button.attr("data-erpw-procurement-create-variant", variant);
      (isPrimary ? $primary : $secondary).append($button);
    });
    if (typeof runtimeMethod("rebalanceActionStrips") === "function") {
      const primaryCount = actions.filter((action) => action.variant === "primary").length;
      runtimeMethod("rebalanceActionStrips")($section, {
        maxPrimaryActions: 4,
        primaryColumns: primaryCount === 4 ? 2 : 0,
      });
    }
  }

  function fetchBootstrapWithRetry($root, attempt) {
    return frappe.call({ method: BOOTSTRAP_METHOD }).catch((error) => {
      const nextDelay = BOOTSTRAP_RETRY_DELAYS[attempt || 0];
      if (!isActiveProcurementRoute() || nextDelay == null) throw error;
      if ($root && $root.length) {
        $root.attr("data-erpw-console-bootstrap", "retrying");
      }
      return new Promise((resolve) => {
        setTimeout(resolve, nextDelay);
      }).then(() => fetchBootstrapWithRetry($root, (attempt || 0) + 1));
    });
  }

  function renderWorkbench(page, routeSignature) {
    const pageState = { payload: {} };
    const renderToken = ++overviewRenderSerial;
    const signature = routeSignature || overviewRouteSignature();
    const $root = $('<div class="sales-console-shell" data-erpw-workspace="procurement" data-erpw-console-runtime="ready" data-erpw-console-bootstrap="loading"></div>');
    $root.attr("data-erpw-overview-render-token", String(renderToken));
    $root.attr("data-erpw-overview-route-signature", signature);

    const $header = $(`
      <section class="sales-console-card sales-console-header">
        <div class="sales-console-header-row">
          <div class="sales-console-header-copy">
            <h1 class="sales-console-title">Procurement Console</h1>
            <div class="sales-console-header-note">Buyer workbench for purchase demand, supplier coordination, and purchase order follow-up.</div>
          </div>
        </div>
        <div class="sales-console-kpi-grid"></div>
      </section>
    `);

    const $kpiGrid = $header.find(".sales-console-kpi-grid");
    $kpiGrid.attr("data-count", "3");
    $kpiGrid.append(
      makeInsightCard({ key: "purchase_orders_overdue", label: "Overdue POs", meta: "Open item lines past required date." })
        .on("click", () => routeToWorklist("purchase_orders_overdue")),
      makeInsightCard({ key: "purchase_orders_supplier_follow_up", label: "Supplier Follow-up", meta: "Orders needing buyer coordination." })
        .on("click", () => routeToWorklist("purchase_orders_supplier_follow_up")),
      makeInsightCard({ key: "purchase_orders_due_soon", label: "Due Soon", meta: "Open item lines due in the next seven days." })
        .on("click", () => routeToWorklist("purchase_orders_due_soon"))
    );

    const $quickFind = renderQuickFindSection();

    const $priorityWork = $(`
      <section class="sales-console-card sales-console-section" data-section-key="priority-work">
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">Priority Work</h2>
          <div class="sales-console-section-note">Demand and quote validity</div>
        </div>
        <div class="sales-console-queue-grid" data-section-grid="priority-work"></div>
      </section>
    `);
    $priorityWork.find(".sales-console-queue-grid").append(
      makeQueueItem({
        key: "requests_to_source",
        title: "Requests To Source",
        meta: "Purchase demand needing buying action.",
        badgeClass: "attention",
        sideLabel: "Source",
        priority: true,
        onClick: () => routeToWorklist("requests_to_source"),
      }),
      makeQueueItem({
        key: "supplier_quotations_expiring",
        title: "Expiring Supplier Quotations",
        meta: "Quoted offers nearing validity end.",
        badgeClass: "blocker",
        sideLabel: "Review",
        priority: true,
        onClick: () => routeToWorklist("supplier_quotations_expiring"),
      })
    );

    const $createActions = $(`
      <section class="sales-console-card sales-console-section" data-section-key="create-actions" hidden>
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">Start Buying Work</h2>
          <div class="sales-console-section-note">Only actions available to your role</div>
        </div>
        <div class="sales-console-action-groups" data-section-grid="create-actions">
          <div class="sales-console-action-strip primary"></div>
          <div class="sales-console-action-strip secondary" hidden></div>
        </div>
      </section>
    `);

    const $pipeline = $(`
      <section class="sales-console-card sales-console-section" data-section-key="buying-pipeline">
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">Buying Pipeline</h2>
          <div class="sales-console-section-note">Demand to downstream visibility</div>
        </div>
        <div class="sales-console-queue-grid" data-section-grid="buying-pipeline"></div>
      </section>
    `);
    $pipeline.find(".sales-console-queue-grid").append(
      makeQueueItem({
        key: "requests_to_source",
        title: "Purchase Request",
        meta: "Submitted purchase demand waiting for sourcing or ordering.",
        badgeClass: "attention",
        sideLabel: "Source",
        onClick: () => routeToWorklist("requests_to_source"),
      }),
      makeQueueItem({
        key: "rfqs_awaiting_supplier_response",
        title: "RFQ",
        meta: "Supplier response posture for active requests.",
        badgeClass: "attention",
        sideLabel: "Response",
        onClick: () => routeToWorklist("rfqs_awaiting_supplier_response"),
      }),
      makeQueueItem({
        key: "supplier_quotations_to_compare",
        title: "Supplier Quotation",
        meta: "Quoted offers ready for buyer comparison.",
        badgeClass: "attention",
        sideLabel: "Compare",
        onClick: () => routeToWorklist("supplier_quotations_to_compare"),
      }),
      makeQueueItem({
        key: "purchase_order_directory",
        title: "Purchase Order",
        meta: "Orders visible for buyer follow-up and supplier coordination.",
        badgeClass: "review",
        sideLabel: "Orders",
        onClick: () => routeToWorklist("purchase_order_directory"),
      }),
      makeQueueItem({
        key: "purchase_orders_partially_received",
        title: "Receipt Visibility",
        meta: "Receiving posture only; warehouse teams own execution.",
        badgeClass: "review",
        sideLabel: "Receipt",
        onClick: () => routeToWorklist("purchase_orders_partially_received"),
      }),
      makeQueueItem({
        key: "purchase_orders_not_billed_visibility",
        title: "Billing Visibility",
        meta: "Billing posture only; Finance owns invoice and payment work.",
        badgeClass: "review",
        sideLabel: "Billing",
        onClick: () => routeToWorklist("purchase_orders_not_billed_visibility"),
      })
    );

    const $orderFollowUp = $(`
      <section class="sales-console-card sales-console-section" data-section-key="order-follow-up">
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">Order Follow-up</h2>
          <div class="sales-console-section-note">Buyer coordination queues</div>
        </div>
        <div class="sales-console-queue-grid" data-section-grid="order-follow-up"></div>
      </section>
    `);
    $orderFollowUp.find(".sales-console-queue-grid").append(
      makeQueueItem({
        key: "purchase_orders_overdue",
        title: "Overdue Purchase Orders",
        meta: "Open item lines past required date.",
        badgeClass: "blocker",
        sideLabel: "Overdue",
        onClick: () => routeToWorklist("purchase_orders_overdue"),
      }),
      makeQueueItem({
        key: "purchase_orders_due_soon",
        title: "Purchase Orders Due Soon",
        meta: "Open item lines due in the next seven days.",
        badgeClass: "attention",
        sideLabel: "Due Soon",
        onClick: () => routeToWorklist("purchase_orders_due_soon"),
      }),
      makeQueueItem({
        key: "purchase_orders_partially_received",
        title: "Partially Received Purchase Orders",
        meta: "Some receipt posted but fulfillment is not complete.",
        badgeClass: "attention",
        sideLabel: "Partial",
        onClick: () => routeToWorklist("purchase_orders_partially_received"),
      }),
      makeQueueItem({
        key: "purchase_orders_not_billed_visibility",
        title: "Received Not Fully Billed",
        meta: "Downstream billing posture only; Finance owns invoice and payment work.",
        badgeClass: "review",
        sideLabel: "Visibility",
        onClick: () => routeToWorklist("purchase_orders_not_billed_visibility"),
      })
    );

    const $directories = $(`
      <section class="sales-console-card sales-console-section" data-section-key="directories">
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">Directories</h2>
          <div class="sales-console-section-note">Compact record access</div>
        </div>
        <div class="sales-console-queue-grid" data-section-grid="directories"></div>
      </section>
    `);
    $directories.find(".sales-console-queue-grid").append(
      makeQueueItem({
        key: "supplier_directory",
        title: "Suppliers",
        meta: "Supplier records for buying coordination.",
        badgeClass: "review",
        sideLabel: "Browse",
        onClick: () => routeToWorklist("supplier_directory"),
      }),
      makeQueueItem({
        key: "purchase_request_directory",
        title: "Purchase Requests",
        meta: "Purchase Material Requests only.",
        badgeClass: "review",
        sideLabel: "Browse",
        onClick: () => routeToWorklist("purchase_request_directory"),
      }),
      makeQueueItem({
        key: "purchase_order_directory",
        title: "Purchase Orders",
        meta: "Visible purchase orders for buyer follow-up.",
        badgeClass: "review",
        sideLabel: "Browse",
        onClick: () => routeToWorklist("purchase_order_directory"),
      }),
      makeQueueItem({
        key: "rfq_directory",
        title: "RFQs",
        meta: "Request for Quotation records visible to this user.",
        badgeClass: "review",
        sideLabel: "Browse",
        onClick: () => routeToWorklist("rfq_directory"),
      }),
      makeQueueItem({
        key: "supplier_quotation_directory",
        title: "Supplier Quotations",
        meta: "Supplier quotation records visible to this user.",
        badgeClass: "review",
        sideLabel: "Browse",
        onClick: () => routeToWorklist("supplier_quotation_directory"),
      }),
      makeQueueItem({
        key: "buying_item_directory",
        title: "Buying Items",
        meta: "Purchase-enabled item and catalog context.",
        badgeClass: "review",
        sideLabel: "Browse",
        onClick: () => routeToWorklist("buying_item_directory"),
      })
    );

    const $sourcing = $(`
      <section class="sales-console-card sales-console-section" data-section-key="sourcing">
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">Sourcing Desk</h2>
          <div class="sales-console-section-note">RFQ and quotation decisions</div>
        </div>
        <div class="sales-console-queue-grid" data-section-grid="sourcing"></div>
      </section>
    `);
    $sourcing.find(".sales-console-queue-grid").append(
      makeQueueItem({
        key: "rfqs_awaiting_supplier_response",
        title: "RFQs Awaiting Supplier Response",
        meta: "Submitted RFQs with pending supplier responses.",
        badgeClass: "attention",
        sideLabel: "Pending",
        onClick: () => routeToWorklist("rfqs_awaiting_supplier_response"),
      }),
      makeQueueItem({
        key: "supplier_quotations_to_compare",
        title: "Supplier Quotations To Compare",
        meta: "Submitted quotations available for price and validity review.",
        badgeClass: "attention",
        sideLabel: "Compare",
        onClick: () => routeToWorklist("supplier_quotations_to_compare"),
      }),
      makeQueueItem({
        key: "supplier_quotations_expiring",
        title: "Expiring Supplier Quotations",
        meta: "Quotation validity ending within seven days.",
        badgeClass: "blocker",
        sideLabel: "Review",
        onClick: () => routeToWorklist("supplier_quotations_expiring"),
      }),
      makeQueueItem({
        key: "supplier_quotation_comparison",
        title: "Quote Comparison",
        meta: "Compare quoted prices, validity, supplier, item, and RFQ reference.",
        badgeClass: "review",
        sideLabel: "Report",
        onClick: () => routeToReport("supplier_quotation_comparison"),
      })
    );

    $root.append($header, $createActions, $quickFind, $priorityWork, $pipeline, $orderFollowUp, $sourcing, $directories);
    replacePageBody(page, $root);
    pruneRouteShells($root.get(0));
    cleanupOverviewPageHeads();
    setTimeout(cleanupOverviewPageHeads, 0);
    setTimeout(cleanupOverviewPageHeads, 120);

    const bootstrapRequest = fetchBootstrapWithRetry($root, 0);
    activeOverviewRenderState = { routeSignature: signature, phase: "bootstrap", token: renderToken, root: $root.get(0), request: bootstrapRequest };
    bootstrapRequest.then((response) => {
      if (!isCurrentOverviewRoot($root, renderToken)) return;
      const payload = response && response.message ? response.message : {};
      pageState.payload = payload;
      if (activeOverviewRenderState && activeOverviewRenderState.token === renderToken) activeOverviewRenderState.phase = "ready";
      if (payload.state && payload.state.kind === "restricted") {
        renderState(page, payload.state);
        return;
      }
      applyPayload($root, payload);
      $root.attr("data-erpw-console-bootstrap", "ready");
      loadManagerReadiness($root, payload, renderToken);
    }).catch((error) => {
      if (!isCurrentOverviewRoot($root, renderToken)) return;
      renderState(page, {
        kind: "error",
        title: "Procurement Console could not be loaded",
        detail: error && error.message ? error.message : "The buyer workbench could not be loaded right now.",
      });
    });
  }

  function cleanupRouteShells() {
    if (window.erpWorkspaceUiBoot && typeof window.erpWorkspaceUiBoot.cleanupProcurementRouteShells === "function") {
      window.erpWorkspaceUiBoot.cleanupProcurementRouteShells(PAGE_KEY, { removeActive: true });
    }
  }

  function pruneRouteShells(keepNode) {
    if (window.erpWorkspaceUiBoot && typeof window.erpWorkspaceUiBoot.pruneProcurementRouteShells === "function") {
      const prune = () => {
        if (!keepNode || !keepNode.isConnected) return;
        window.erpWorkspaceUiBoot.pruneProcurementRouteShells(PAGE_KEY, keepNode);
      };
      prune();
      setTimeout(prune, 0);
      setTimeout(prune, 80);
    }
  }


  function cleanupOverviewPageHeads() {
    const route = frappe.get_route ? frappe.get_route() : [];
    const routeKey = Array.isArray(route) ? String(route[0] || "") : "";
    if (routeKey !== PAGE_KEY) return;
    document.querySelectorAll(".page-head").forEach((head) => {
      if (!(head instanceof HTMLElement)) return;
      const text = String(head.textContent || "").replace(/\s+/g, " ").trim();
      const hasManagedTitle = /Procurement Console/i.test(text);
      if (!hasManagedTitle && (!text || text === "Actions")) {
        head.remove();
      }
    });
  }

  function hasReadyOverviewShell() {
    const shell = document.querySelector('.sales-console-shell[data-erpw-workspace="procurement"]');
    return Boolean(shell && shell.getAttribute("data-erpw-console-runtime") === "ready" && document.querySelector(".sales-console-kpi-card"));
  }

  function render(wrapper) {
    if (!isActiveProcurementRoute()) return;
    if (hasReadyOverviewShell()) return;
    const routeSignature = overviewRouteSignature();
    const active = activeOverviewRenderState;
    if (active && active.routeSignature === routeSignature && active.phase !== "error" && active.root && document.body.contains(active.root)) return;
    cleanupRouteShells();
    cleanupOverviewPageHeads();
    const page = makeConsolePage(wrapper);
    renderLoadingState(page);
    activeOverviewRenderState = { routeSignature, phase: "runtime", root: pageBodyElement(page) };
    if (wrapper) {
      wrapper.__erpwProcurementConsole = { routeSignature };
    }
    ensureConsoleRuntime().then(() => {
      if (!isActiveProcurementRoute() || overviewRouteSignature() !== routeSignature) return;
      renderWorkbench(page, routeSignature);
    }).catch((error) => {
      if (activeOverviewRenderState && activeOverviewRenderState.routeSignature === routeSignature) activeOverviewRenderState.phase = "error";
      renderState(page, {
        kind: "error",
        title: "Procurement Console could not be loaded",
        detail: error && error.message ? error.message : "The shared console runtime could not be loaded.",
      });
    });
  }

  function directRenderWrapper() {
    return document.getElementById("body") || (frappe.container && frappe.container.page && frappe.container.page.wrapper);
  }

  function shouldSelfRenderOverview() {
    if (!isActiveProcurementRoute()) return false;
    const shell = document.querySelector('.sales-console-shell[data-erpw-workspace="procurement"]');
    if (!shell) return true;
    if (shell.getAttribute("data-erpw-direct-first-paint") === "procurement-console") return true;
    const runtimeState = shell.getAttribute("data-erpw-console-runtime") || "";
    const bootstrapState = shell.getAttribute("data-erpw-console-bootstrap") || "";
    if (runtimeState === "loading" || bootstrapState === "loading" || bootstrapState === "retrying") return false;
    return !document.querySelector(".sales-console-kpi-card");
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
    setTimeout(renderActiveOverviewRoute, 1400);
  }

  function bindActiveOverviewGuard() {
    if (activeOverviewGuardBound || !window || typeof window.setInterval !== "function") return;
    activeOverviewGuardBound = true;
    window.setInterval(() => {
      if (shouldSelfRenderOverview()) renderActiveOverviewRoute();
    }, 160);
  }

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].__erpwProcurementConsoleRenderer = true;
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) { render(wrapper); };
  frappe.pages[PAGE_KEY].on_page_show = function (wrapper) {
    if (window.erpWorkspaceConsoleSidebar && typeof window.erpWorkspaceConsoleSidebar.refresh === "function") {
      window.erpWorkspaceConsoleSidebar.refresh();
    }
    const host = wrapper && wrapper.page && wrapper.page.body ? wrapper.page.body : wrapper;
    let $existingShell = $(host || []).find(".sales-console-shell").first();
    if (!$existingShell.length) {
      $existingShell = $('.sales-console-shell[data-erpw-workspace="procurement"]').first();
    }
    const isFirstPaintShell = $existingShell.attr("data-erpw-direct-first-paint") === "procurement-console";
    const isLoadingShell = $existingShell.attr("data-erpw-console-runtime") === "loading";
    if ($existingShell.length && !isFirstPaintShell && !isLoadingShell) {
      pruneRouteShells($existingShell.get(0));
      cleanupOverviewPageHeads();
      setTimeout(cleanupOverviewPageHeads, 0);
      setTimeout(cleanupOverviewPageHeads, 120);
      return;
    }
    render(wrapper);
  };
  scheduleActiveOverviewRender();
  bindActiveOverviewGuard();
})();
