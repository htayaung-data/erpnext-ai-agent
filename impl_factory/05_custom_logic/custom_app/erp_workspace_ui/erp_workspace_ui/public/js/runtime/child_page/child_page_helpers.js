(function () {
  const root = window;
  const childPageRuntime = root.erpWorkspaceUiChildPage = root.erpWorkspaceUiChildPage || {};
  let draftBodyGateStylesInjected = false;
  const draftPerformanceState = childPageRuntime.draftPerformanceState = childPageRuntime.draftPerformanceState || {
    sessions: Object.create(null),
    history: [],
    latest: null,
  };

  function getPerfNow() {
    try {
      if (root.performance && typeof root.performance.now === "function") {
        return root.performance.now();
      }
    } catch (error) {
      // Fall through to Date.now when Performance API is unavailable.
    }
    return Date.now();
  }

  function isDraftForm(frm) {
    return !!(frm && typeof frm.is_new === "function" && frm.is_new());
  }

  const BUSINESS_NOTE_INTENTS = Object.freeze([
    "action",
    "blocked",
    "decision",
    "empty",
    "exception",
    "missing",
    "readonly",
    "risk",
    "warning",
  ]);

  function normalizeBusinessNoteIntent(intent) {
    return String(intent || "").trim().toLowerCase();
  }

  function noteHasBusinessSignal(text) {
    return /\b(add|blocked|cannot|confirm|due|empty|expired|failed|fix|link|missing|needed|not configured|not linked|overdue|readonly|required|review-only|select|short|unlock|warning|zero)\b/i
      .test(String(text || ""));
  }

  function resolveBusinessNote(note, options) {
    const text = note == null ? "" : String(note).trim();
    if (!text) return "";

    const settings = options || {};
    if (settings.force === true) return text;

    const intent = normalizeBusinessNoteIntent(settings.intent || settings.noteIntent || settings.copyIntent);
    if (BUSINESS_NOTE_INTENTS.includes(intent)) return text;

    const tone = String(settings.statusTone || settings.tone || "").trim().toLowerCase();
    if (["attention", "blocker", "danger", "error", "warning"].includes(tone) && noteHasBusinessSignal(text)) {
      return text;
    }

    return "";
  }

  function getDraftPerformanceSessionKey(frm) {
    const routePath = root.location && root.location.pathname ? root.location.pathname : "";
    const identity = isDraftForm(frm)
      ? (routePath || `${frm && frm.doctype ? frm.doctype : "Form"}|draft`)
      : (frm && frm.doc && frm.doc.name ? frm.doc.name : "__draft__");

    return [
      frm && frm.doctype ? frm.doctype : "",
      isDraftForm(frm) ? "draft" : "saved",
      identity,
    ].join("|");
  }

  function sanitizePerformanceMeta(meta) {
    if (!meta || typeof meta !== "object") return meta == null ? null : String(meta);
    const output = {};
    Object.keys(meta).slice(0, 10).forEach((key) => {
      const value = meta[key];
      if (value == null) {
        output[key] = value;
      } else if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
        output[key] = value;
      } else if (Array.isArray(value)) {
        output[key] = value.slice(0, 5).map((entry) => (
          entry == null || typeof entry === "string" || typeof entry === "number" || typeof entry === "boolean"
            ? entry
            : String(entry)
        ));
      } else {
        output[key] = String(value);
      }
    });
    return output;
  }

  function ensureDraftPerformanceSession(frm) {
    if (!frm) return null;
    const key = getDraftPerformanceSessionKey(frm);
    if (!key) return null;

    let session = draftPerformanceState.sessions[key];
    if (!session) {
      session = {
        key,
        doctype: frm.doctype || "",
        name: (frm.doc && frm.doc.name) || "__draft__",
        mode: isDraftForm(frm) ? "draft" : "saved",
        route: root.location && root.location.pathname ? root.location.pathname : "",
        startedAt: getPerfNow(),
        timeline: [],
        events: Object.create(null),
        finalizedSignature: "",
      };
      draftPerformanceState.sessions[key] = session;
    }
    return session;
  }

  function resetDraftPerformanceSession(frm, meta) {
    if (!frm) return null;
    const key = getDraftPerformanceSessionKey(frm);
    if (!key) return null;

    delete draftPerformanceState.sessions[key];
    const session = ensureDraftPerformanceSession(frm);
    if (!session) return null;

    const eventMeta = sanitizePerformanceMeta(meta);
    session.timeline.push({
      name: "session_reset",
      ts: session.startedAt,
      meta: eventMeta,
    });
    session.events.session_reset = {
      ts: session.startedAt,
      count: 1,
      meta: eventMeta,
    };
    return session;
  }

  function seedDraftPerformanceSession(frm, snapshot) {
    const session = ensureDraftPerformanceSession(frm);
    if (!session || !snapshot || typeof snapshot !== "object") return null;

    const meta = Object.assign({
      seeded: true,
      source: "state",
    }, sanitizePerformanceMeta(snapshot) || {});

    if (snapshot.shellPrepared && !session.events.shell_prepare_ready) {
      recordDraftPerformanceEvent(frm, "shell_prepare_ready", meta);
    }
    if (snapshot.contextReady && !session.events.context_load_ready) {
      recordDraftPerformanceEvent(frm, "context_load_ready", meta);
    }
    if (snapshot.pendingActive && !session.events.draft_body_pending_start) {
      recordDraftPerformanceEvent(frm, "draft_body_pending_start", meta);
    }

    return session;
  }

  function recordDraftPerformanceEvent(frm, name, meta) {
    const session = ensureDraftPerformanceSession(frm);
    if (!session || !name) return null;

    const eventMeta = sanitizePerformanceMeta(meta);
    const timestamp = getPerfNow();
    const existing = session.events[name];
    session.events[name] = {
      ts: timestamp,
      count: existing ? existing.count + 1 : 1,
      meta: eventMeta,
    };
    session.timeline.push({
      name,
      ts: timestamp,
      meta: eventMeta,
    });
    if (session.timeline.length > 60) {
      session.timeline.splice(0, session.timeline.length - 60);
    }
    return session;
  }

  function buildDraftPerformanceSummary(session) {
    if (!session) return null;
    const t0 = session.startedAt || 0;
    const events = session.events || {};
    const getOffset = (name) => {
      const event = events[name];
      return event ? Math.max(0, Math.round(event.ts - t0)) : null;
    };
    const getDuration = (startName, endName) => {
      const start = events[startName];
      const end = events[endName];
      return start && end ? Math.max(0, Math.round(end.ts - start.ts)) : null;
    };

    return {
      key: session.key,
      doctype: session.doctype,
      name: session.name,
      mode: session.mode,
      route: session.route,
      msToShellPrepare: getOffset("shell_prepare_ready"),
      msToShellMount: getOffset("shell_mount_ready"),
      msToContextReady: getOffset("context_load_ready"),
      msToDraftPending: getOffset("draft_body_pending_start"),
      msToDraftReveal: getOffset("draft_body_pending_end"),
      msToDraftStable: getOffset("draft_body_stable"),
      draftGateVisibleMs: getDuration("draft_body_pending_start", "draft_body_pending_end"),
      readinessCheckMs: getDuration("draft_body_watch_start", "draft_body_stable"),
      draftRegressions: events.draft_body_regressed ? events.draft_body_regressed.count : 0,
      timeline: session.timeline.slice(-24),
    };
  }

  function publishDraftPerformanceSummary(frm, reason) {
    const session = ensureDraftPerformanceSession(frm);
    if (!session || session.mode !== "draft") return false;

    const summary = buildDraftPerformanceSummary(session);
    if (!summary) return false;
    if (summary.msToDraftReveal == null && summary.msToDraftStable == null) return false;

    const signature = JSON.stringify([
      summary.msToShellPrepare,
      summary.msToContextReady,
      summary.msToDraftReveal,
      summary.msToDraftStable,
      reason || "",
    ]);
    if (signature === session.finalizedSignature) {
      return true;
    }

    session.finalizedSignature = signature;
    summary.reason = reason || "update";
    draftPerformanceState.latest = summary;
    draftPerformanceState.history.unshift(summary);
    if (draftPerformanceState.history.length > 20) {
      draftPerformanceState.history.length = 20;
    }
    root.__erpwLatestDraftPerformance = summary;
    if (root.__erpwDraftPerformanceDebug === true && root.console && typeof root.console.debug === "function") {
      root.console.debug("[erpw:draft-performance]", summary);
    }
    try {
      root.dispatchEvent(new CustomEvent("erpw:draft-performance", {
        detail: summary,
      }));
    } catch (error) {
      // Ignore event dispatch failures.
    }
    return true;
  }

  function formatMoney(value, currency) {
    if (value == null) return "--";
    try {
      return format_currency(value, currency || frappe.defaults.get_default("currency"));
    } catch (e) {
      return `${currency || ""} ${value}`;
    }
  }

  function escapeHtml(value) {
    return frappe.utils.escape_html(value == null ? "" : String(value));
  }

  const SALES_CONSOLE_DIRECTORY_BY_DOCTYPE = {
    Customer: "customer_directory",
    Item: "item_directory",
    Quotation: "quotation_directory",
    "Sales Order": "sales_order_directory",
    ToDo: "customer_follow_up_tasks",
  };

  const SALES_CONSOLE_ENHANCED_FORM_DOCTYPES = new Set([
    "Delivery Note",
    "Quotation",
    "Sales Invoice",
    "Sales Order",
  ]);

  const SALES_CONSOLE_FORM_ONLY_DOCTYPES = new Set([
    "Delivery Note",
    "Sales Invoice",
  ]);

  const SALES_CONSOLE_DEFERRED_DOCTYPES = new Set([
    "Delivery Trip",
    "Driver",
    "Opportunity",
    "Payment Entry",
    "Supplier",
    "ToDo",
    "Warehouse",
  ]);

  const SALES_CONSOLE_LINKED_DOCUMENT_ACTION_CATEGORIES = new Set([
    "linked_document",
    "reference_document",
    "supporting_navigation",
  ]);

  function normalizeDoctype(value) {
    return String(value || "").trim();
  }

  function getDirectoryQueueForDoctype(doctype) {
    return SALES_CONSOLE_DIRECTORY_BY_DOCTYPE[normalizeDoctype(doctype)] || "";
  }

  function applySalesConsoleDocumentActionPolicy(actions, options) {
    const settings = Object.assign({
      includePassiveFollowUp: false,
      maxTopActions: 2,
    }, options || {});
    const maxTopActions = Math.max(0, Number(settings.maxTopActions || 0));
    const allowed = [];

    (Array.isArray(actions) ? actions : []).forEach((action) => {
      if (!action) return;
      const category = String(action.category || "").trim();
      const family = String(action.family || "").trim();

      if (family === "commit" || action.forceTopAction) {
        allowed.push(action);
        return;
      }

      if (SALES_CONSOLE_LINKED_DOCUMENT_ACTION_CATEGORIES.has(category)) {
        return;
      }

      if (category === "follow_up") {
        if (action.attention || settings.includePassiveFollowUp) {
          allowed.push(action);
        }
        return;
      }

      if (category === "primary_business_action" || category === "business_next_step") {
        allowed.push(action);
      }
    });

    return maxTopActions ? allowed.slice(0, maxTopActions) : allowed;
  }

  function applySalesConsoleGuidancePolicy(cards, options) {
    const settings = Object.assign({
      includeFallback: false,
      maxCards: 2,
    }, options || {});
    const normalized = (Array.isArray(cards) ? cards : []).filter(Boolean);
    const priorityCards = normalized.filter((card) => !!(card.attention || card.priority));
    const selected = priorityCards.length
      ? priorityCards
      : (settings.includeFallback ? normalized : []);
    return selected.slice(0, Math.max(0, Number(settings.maxCards || 0)));
  }

  function getKeywordFilter(name, filters) {
    if (filters && typeof filters === "object" && Object.keys(filters).length) {
      return Object.assign({}, filters);
    }
    const keyword = String(name || "").trim();
    return keyword ? { keyword } : {};
  }

  function showDeferredRouteNotice(doctype) {
    frappe.show_alert({
      message: __(`${doctype} is visible here, but its Sales Console page is not available yet.`),
      indicator: "orange",
    });
    return true;
  }

  function encodeRoutePart(value) {
    return encodeURIComponent(String(value || "").trim());
  }

  function customerRouteValue(filters) {
    return filters && typeof filters === "object" ? String(filters.customer || "").trim() : "";
  }

  function itemRouteValue(filters) {
    return filters && typeof filters === "object" ? String(filters.item || filters.item_code || "").trim() : "";
  }

  function routeToWorklist(queueKey, filters) {
    if (!queueKey) return false;
    const normalizedQueueKey = String(queueKey || "").replace(/_/g, "-");
    const nextFilters = filters && typeof filters === "object" && Object.keys(filters).length ? filters : null;
    const normalizedTargetKey = String(queueKey || "").replace(/-/g, "_");
    const routeCustomer = customerRouteValue(nextFilters);
    const routeItem = itemRouteValue(nextFilters);
    if (["customer_detail", "customer_editor"].includes(normalizedTargetKey) && routeCustomer) {
      frappe.route_options = nextFilters;
      frappe.set_route("sales-console-worklist", normalizedQueueKey, encodeRoutePart(routeCustomer));
      return true;
    }
    if (normalizedTargetKey === "item_detail" && routeItem) {
      frappe.route_options = nextFilters;
      frappe.set_route("sales-console-worklist", normalizedQueueKey, encodeRoutePart(routeItem));
      return true;
    }

    const route = frappe.get_route ? frappe.get_route() : [];
    const currentQueueKey = Array.isArray(route) && route[0] === "sales-console-worklist"
      ? String(route[1] || "").replace(/-/g, "_")
      : "";
    const worklistRuntime = root.erpWorkspaceSalesConsoleWorklist || {};

    if (
      currentQueueKey === String(queueKey || "").replace(/-/g, "_")
      && nextFilters
      && typeof worklistRuntime.applyFilters === "function"
      && worklistRuntime.applyFilters(String(queueKey || "").replace(/-/g, "_"), nextFilters)
    ) {
      return true;
    }

    frappe.route_options = nextFilters;
    frappe.set_route("sales-console-worklist", normalizedQueueKey);
    return true;
  }

  function routeToSalesConsoleTarget(target) {
    if (!target || typeof target !== "object") return false;
    if (target.notice) {
      frappe.show_alert({ message: __(target.notice), indicator: "blue" });
    }

    if (target.kind === "worklist" && target.queue_key) {
      return routeToWorklist(target.queue_key, target.filters || null);
    }

    if (target.kind === "form" && target.doctype && target.name) {
      const doctype = normalizeDoctype(target.doctype);
      if (doctype === "ToDo") {
        return routeToWorklist("customer_follow_up_tasks", Object.assign({}, target.filters || {}, {
          todo_name: target.name,
        }));
      }
      if (doctype === "Customer") {
        return routeToWorklist("customer_detail", Object.assign({}, target.filters || {}, {
          customer: target.name,
        }));
      }
      if (doctype === "Item") {
        return routeToWorklist("item_detail", Object.assign({}, target.filters || {}, {
          item: target.name,
        }));
      }
      if (SALES_CONSOLE_ENHANCED_FORM_DOCTYPES.has(doctype)) {
        frappe.set_route("Form", doctype, target.name);
        return true;
      }

      const queueKey = getDirectoryQueueForDoctype(doctype);
      if (queueKey) {
        return routeToWorklist(queueKey, getKeywordFilter(target.name, target.filters));
      }
      if (SALES_CONSOLE_DEFERRED_DOCTYPES.has(doctype)) {
        return showDeferredRouteNotice(doctype);
      }
    }

    if (target.kind === "list" && target.doctype) {
      const doctype = normalizeDoctype(target.doctype);
      const queueKey = getDirectoryQueueForDoctype(doctype);
      if (queueKey) {
        return routeToWorklist(queueKey, target.filters || null);
      }
      if (SALES_CONSOLE_FORM_ONLY_DOCTYPES.has(doctype)) {
        frappe.show_alert({
          message: __(`${doctype} directory is not available in Sales Console yet. Open a single linked document from Connections.`),
          indicator: "orange",
        });
        return true;
      }
      if (SALES_CONSOLE_DEFERRED_DOCTYPES.has(doctype)) {
        return showDeferredRouteNotice(doctype);
      }
    }

    return false;
  }

  function routeToDoc(doctype, name) {
    if (!doctype || !name) return;
    if (routeToSalesConsoleTarget({ kind: "form", doctype, name })) return;
    frappe.set_route("Form", doctype, name);
  }

  function routeToList(doctype, filters) {
    if (routeToSalesConsoleTarget({ kind: "list", doctype, filters })) return;
    frappe.route_options = filters && Object.keys(filters).length ? filters : null;
    frappe.set_route("List", doctype);
  }


  function scrollViewportTop() {
    try {
      const scrollingElement = document.scrollingElement || document.documentElement || document.body;
      if (scrollingElement) {
        scrollingElement.scrollTop = 0;
      }
      if (document.body) {
        document.body.scrollTop = 0;
      }
      if (document.documentElement) {
        document.documentElement.scrollTop = 0;
      }
      const mainSection = document.querySelector(".main-section");
      if (mainSection) {
        mainSection.scrollTop = 0;
      }
      const layoutMainSection = document.querySelector(".layout-main-section");
      if (layoutMainSection) {
        layoutMainSection.scrollTop = 0;
      }
      window.scrollTo(0, 0);
    } catch (error) {
      // Ignore scroll reset failures and keep route flow usable.
    }
  }

  function getFormTaskState(frm) {
    if (!frm) return { timers: {} };
    if (!frm.__erpwTaskState) {
      frm.__erpwTaskState = { timers: {} };
    }
    return frm.__erpwTaskState;
  }

  function scheduleFormTask(frm, key, delay, fn) {
    if (!frm || typeof fn !== "function") return;
    const state = getFormTaskState(frm);
    if (state.timers[key]) {
      clearTimeout(state.timers[key]);
    }
    state.timers[key] = setTimeout(() => {
      delete state.timers[key];
      if (!frm.doc) return;
      fn();
    }, Math.max(0, Number(delay || 0)));
  }

  function getLayoutWrapper(frm) {
    return $(frm && frm.layout && frm.layout.wrapper ? frm.layout.wrapper : []);
  }

  function getFormRoot(frm) {
    const $layout = getLayoutWrapper(frm);
    if ($layout.length) {
      const $mainSection = $layout.closest(".layout-main-section");
      if ($mainSection.length) return $mainSection;

      const $formPage = $layout.closest(".form-page");
      if ($formPage.length) return $formPage;

      const $parent = $layout.parent();
      if ($parent.length) return $parent;

      return $layout;
    }

    const $wrapper = $(frm && frm.wrapper ? frm.wrapper : frm && frm.$wrapper ? frm.$wrapper : []);
    if ($wrapper.length) {
      const $mainSection = $wrapper.closest(".layout-main-section");
      if ($mainSection.length) return $mainSection;

      const $formPage = $wrapper.closest(".form-page");
      if ($formPage.length) return $formPage;

      return $wrapper;
    }

    return $(frm && frm.page && frm.page.main ? frm.page.main : []);
  }

  function getPageContentRoot(frm) {
    const $layout = getLayoutWrapper(frm);
    if ($layout.length) {
      const $pageContent = $layout.closest(".page-content");
      if ($pageContent.length) return $pageContent;
    }

    const $root = getFormRoot(frm);
    if ($root.length) {
      const $pageContent = $root.closest(".page-content");
      if ($pageContent.length) return $pageContent;
    }

    return $(".page-content").first();
  }

  function getPageContainerRoot(frm) {
    const $pageContent = getPageContentRoot(frm);
    if ($pageContent.length) {
      const $pageContainer = $pageContent.closest(".page-container");
      if ($pageContainer.length) return $pageContainer;
    }

    const $root = getFormRoot(frm);
    if ($root.length) {
      const $pageContainer = $root.closest(".page-container");
      if ($pageContainer.length) return $pageContainer;
    }

    return $(".page-container").first();
  }

  function ensureChildPageHostSlot(frm) {
    const $layout = getLayoutWrapper(frm);
    const $formRoot = getFormRoot(frm);
    const $mainSection = $layout.length
      ? $layout.closest(".layout-main-section")
      : $formRoot.closest(".layout-main-section").length
        ? $formRoot.closest(".layout-main-section")
        : $formRoot.hasClass("layout-main-section")
          ? $formRoot
          : $();

    if ($mainSection.length) {
      const $pageContent = getPageContentRoot(frm);
      const $pageContainer = getPageContainerRoot(frm);
      let $slot = $mainSection.find(".erpw-child-page-host").first();
      if (!$slot.length && $pageContent.length) {
        $slot = $pageContent.find(".erpw-child-page-host").first();
      }
      if (!$slot.length && $pageContainer.length) {
        $slot = $pageContainer.find(".erpw-child-page-host").first();
      }
      if (!$slot.length) {
        $slot = $('<div class="erpw-child-page-host" data-erpw-child-page-host="1"></div>');
      }

      const $nativeAnchor = getNativeLayoutAnchor(frm);
      const $hiddenPageForm = $mainSection.children(".page-form").first();
      let $target = $nativeAnchor;
      let $desiredParent = $nativeAnchor.length ? $nativeAnchor.parent() : $mainSection;

      if (!$target.length) {
        const $formPage = $mainSection.children(".form-page").first();
        if ($formPage.length) {
          $target = $formPage;
          $desiredParent = $mainSection;
        }
      }

      const hostParent = $slot.parent();
      if (!hostParent.length || hostParent.get(0) !== $desiredParent.get(0)) {
        $slot.detach();
      }

      if ($target.length) {
        if ($slot.parent().get(0) !== $desiredParent.get(0) || $slot.next().get(0) !== $target.get(0)) {
          $slot.insertBefore($target);
        }
      } else if ($hiddenPageForm.length) {
        if ($slot.parent().get(0) !== $mainSection.get(0) || $slot.prev().get(0) !== $hiddenPageForm.get(0)) {
          $slot.insertAfter($hiddenPageForm);
        }
      } else if (!$slot.parent().length || $slot.parent().get(0) !== $mainSection.get(0)) {
        $mainSection.prepend($slot);
      }

      return $slot;
    }

    const $pageContent = getPageContentRoot(frm);
    if (!$pageContent.length) return $();

    let $slot = $pageContent.children(".erpw-child-page-host").first();
    if ($slot.length) return $slot;

    $slot = $('<div class="erpw-child-page-host" data-erpw-child-page-host="1"></div>');
    const $layoutMain = $pageContent.children(".layout-main").first();
    if ($layoutMain.length) {
      $slot.insertBefore($layoutMain);
    } else {
      $pageContent.prepend($slot);
    }
    return $slot;
  }

  function getNativeLayoutAnchor(frm) {
    const $root = getFormRoot(frm);
    if ($root.length) {
      const $stdFormLayout = $root.find(".std-form-layout").first();
      if ($stdFormLayout.length) return $stdFormLayout;

      const $formLayout = $root.find(".form-layout").first();
      if ($formLayout.length) return $formLayout;
    }

    const $layout = getLayoutWrapper(frm);
    if ($layout.length) return $layout;

    if (!$root.length) return $();

    return $root.find(".layout-main-section").first().length
      ? $root.find(".layout-main-section").first()
      : $root.find(".form-page").first().length
        ? $root.find(".form-page").first()
        : $();
  }

  function ensureDraftBodyGateStyles() {
    if (draftBodyGateStylesInjected) return;
    draftBodyGateStylesInjected = true;

    const style = document.createElement("style");
    style.id = "erpw-draft-body-gate-styles";
    style.textContent = `
      .erpw-child-draft-body-placeholder {
        display: none;
      }

      .erpw-child-draft-body-pending .erpw-child-draft-body-placeholder {
        display: block;
        margin: 0 0 18px;
        padding: 22px 24px;
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 22px;
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.98));
        box-shadow: 0 18px 44px rgba(15, 23, 42, 0.06);
      }

      .erpw-child-draft-body-placeholder-head {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        margin-bottom: 12px;
      }

      .erpw-child-draft-body-placeholder-pulse {
        width: 9px;
        height: 9px;
        border-radius: 999px;
        background: #0f766e;
        box-shadow: 0 0 0 0 rgba(15, 118, 110, 0.2);
        animation: erpwDraftPulse 1.4s ease-in-out infinite;
        flex: 0 0 auto;
      }

      .erpw-child-draft-body-placeholder-rows {
        display: grid;
        gap: 12px;
      }

      .erpw-child-draft-body-placeholder-row {
        display: grid;
        grid-template-columns: 1.15fr 1fr 0.9fr;
        gap: 12px;
      }

      .erpw-child-draft-body-placeholder-block {
        height: 44px;
        border-radius: 14px;
        background: linear-gradient(90deg, rgba(226, 232, 240, 0.88), rgba(241, 245, 249, 0.98), rgba(226, 232, 240, 0.88));
        background-size: 220% 100%;
        animation: erpwDraftShimmer 1.6s linear infinite;
      }

      .erpw-child-draft-body-placeholder-block.is-wide {
        grid-column: span 2;
      }

      .erpw-child-draft-body-pending .erpw-child-draft-tab-panels {
        opacity: 0 !important;
        pointer-events: none !important;
        max-height: 0 !important;
        min-height: 0 !important;
        overflow: hidden !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        border-width: 0 !important;
      }

      .erpw-child-draft-body-pending .erpw-child-draft-tab-panels > * {
        visibility: hidden !important;
      }

      .erpw-child-draft-body-pending .erpw-child-draft-support-hidden {
        display: none !important;
      }

      @keyframes erpwDraftShimmer {
        0% {
          background-position: 200% 0;
        }
        100% {
          background-position: -20% 0;
        }
      }

      @keyframes erpwDraftPulse {
        0% {
          box-shadow: 0 0 0 0 rgba(15, 118, 110, 0.24);
          opacity: 1;
        }
        70% {
          box-shadow: 0 0 0 10px rgba(15, 118, 110, 0);
          opacity: 0.7;
        }
        100% {
          box-shadow: 0 0 0 0 rgba(15, 118, 110, 0);
          opacity: 1;
        }
      }
    `;
    document.head.appendChild(style);
  }

  function escapeSelectorValue(value) {
    return String(value || "").replace(/([ #;?%&,.+*~\\':"!^$[\]()=>|/@])/g, "\\$1");
  }

  function getDraftBodyPanels(frm) {
    const $root = getFormRoot(frm);
    if (!$root.length) return $();

    const panels = [];
    const seen = new Set();
    $root.find(".form-tabs .nav-link, .form-tabs-list .nav-link, .nav-tabs .nav-link").each(function () {
      const panelId = String(this.getAttribute("aria-controls") || "").trim();
      if (!panelId) return;
      const $panel = $root.find(`#${escapeSelectorValue(panelId)}`).first();
      if (!$panel.length) return;
      const node = $panel.get(0);
      if (!node || seen.has(node)) return;
      seen.add(node);
      panels.push(node);
    });

    if (panels.length) {
      return $(panels);
    }

    const $fallback = $root.find(".tab-content, .form-tab-content, .form-tabs-content").first();
    return $fallback.length ? $fallback : $();
  }

  function isDraftBodyPanelVisible(node) {
    if (!(node instanceof HTMLElement)) return false;
    if (node.hidden) return false;
    const style = window.getComputedStyle(node);
    if (style.display === "none" || style.visibility === "hidden") return false;
    if (node.classList.contains("active") || node.classList.contains("show")) return true;
    return node.offsetParent !== null;
  }

  function getDraftBodyWatchTargets(frm) {
    const $root = getFormRoot(frm);
    const $panels = getDraftBodyPanels(frm);
    if (!$panels.length) {
      return $root;
    }

    const activePanels = [];
    $panels.each(function () {
      if (isDraftBodyPanelVisible(this)) {
        activePanels.push(this);
      }
    });

    if (activePanels.length) {
      return $(activePanels);
    }

    const $firstPanel = $panels.first();
    return $firstPanel.length ? $firstPanel : $root;
  }

  function ensureDraftBodyPlaceholder(frm) {
    const $root = getFormRoot(frm);
    const $panels = getDraftBodyPanels(frm);
    if (!$root.length || !$panels.length) return $();

    let $placeholder = $root.find(".erpw-child-draft-body-placeholder").first();
    if (!$placeholder.length) {
      $placeholder = $(`
        <div class="erpw-child-draft-body-placeholder" aria-live="polite" aria-busy="true">
          <div class="erpw-child-draft-body-placeholder-head">
            <span class="erpw-child-draft-body-placeholder-pulse" aria-hidden="true"></span>
          </div>
          <div class="erpw-child-draft-body-placeholder-rows">
            <div class="erpw-child-draft-body-placeholder-row">
              <div class="erpw-child-draft-body-placeholder-block"></div>
              <div class="erpw-child-draft-body-placeholder-block"></div>
              <div class="erpw-child-draft-body-placeholder-block"></div>
            </div>
            <div class="erpw-child-draft-body-placeholder-row">
              <div class="erpw-child-draft-body-placeholder-block is-wide"></div>
              <div class="erpw-child-draft-body-placeholder-block"></div>
            </div>
            <div class="erpw-child-draft-body-placeholder-row">
              <div class="erpw-child-draft-body-placeholder-block"></div>
              <div class="erpw-child-draft-body-placeholder-block"></div>
              <div class="erpw-child-draft-body-placeholder-block"></div>
            </div>
          </div>
        </div>
      `);
    }

    const $firstPanel = $panels.first();
    if (!$placeholder.parent().length || $placeholder.next().get(0) !== $firstPanel.get(0)) {
      $placeholder.detach();
      $placeholder.insertBefore($firstPanel);
    }

    return $placeholder;
  }

  function getDraftSupportSurfaces(frm) {
    const $root = getFormRoot(frm);
    const $wrapper = $(frm && (frm.wrapper || frm.$wrapper) ? (frm.wrapper || frm.$wrapper) : []);
    const surfaces = [];
    const seen = new Set();

    [
      ".form-footer",
      ".form-message-container",
      ".form-dashboard-section",
      ".comments-section",
    ].forEach((selector) => {
      [$root, $wrapper].forEach(($source) => {
        if (!$source || !$source.length) return;
        $source.find(selector).each(function () {
          if (seen.has(this)) return;
          seen.add(this);
          surfaces.push(this);
        });
      });
    });

    return $(surfaces);
  }

  function stopDraftBodyStabilityWatch(frm) {
    const state = frm && frm.__erpwDraftBodyWatchState;
    if (!state) return false;

    if (state.timer) {
      clearTimeout(state.timer);
    }
    if (state.observer) {
      state.observer.disconnect();
    }

    delete frm.__erpwDraftBodyWatchState;
    return true;
  }

  function markFeatureStatus(frm, feature, status, meta) {
    if (!frm || !feature || !status) return false;
    recordDraftPerformanceEvent(frm, `${feature}_${status}`, meta);
    if ((status === "loading" || status === "inflight" || status === "waiting") && !isDraftForm(frm)) {
      publishDraftPerformanceSummary(frm, `${feature}_${status}`);
    }
    return true;
  }

  function markFeatureReady(frm, feature, meta) {
    if (!frm || !feature) return false;
    recordDraftPerformanceEvent(frm, `${feature}_ready`, meta);
    if (feature === "context_load" || feature === "shell_release") {
      publishDraftPerformanceSummary(frm, `${feature}_ready`);
    }
    return true;
  }

  function markFeatureMissing(frm, feature, meta) {
    if (!frm || !feature) return false;
    recordDraftPerformanceEvent(frm, `${feature}_missing`, meta);
    publishDraftPerformanceSummary(frm, `${feature}_missing`);
    return true;
  }

  function watchDraftBodyStability(frm, options) {
    const $root = getFormRoot(frm);
    if (!$root.length) return false;

    const settings = Object.assign({
      isReady: null,
      key: "",
      maxWaitMs: 2200,
      pollMs: 45,
      quietMs: 140,
      onStable: null,
    }, options || {});

    const existing = frm && frm.__erpwDraftBodyWatchState;
    if (existing && existing.key === settings.key) {
      return true;
    }

    stopDraftBodyStabilityWatch(frm);
    ensureDraftBodyGateStyles();
    setDraftBodyPending(frm, true);
    recordDraftPerformanceEvent(frm, "draft_body_watch_start", {
      key: settings.key || "",
      maxWaitMs: settings.maxWaitMs,
      quietMs: settings.quietMs,
      pollMs: settings.pollMs,
    });

    const $targets = getDraftBodyWatchTargets(frm);
    const targets = $targets.length ? $targets.toArray() : [$root.get(0)];
    if (!targets.length) return false;

    const startedAt = Date.now();
    let lastMutationAt = startedAt;

    const state = {
      key: settings.key || "",
      observer: new MutationObserver((mutations) => {
        if (!Array.isArray(mutations) || !mutations.length) return;
        lastMutationAt = Date.now();
      }),
      timer: null,
    };

    frm.__erpwDraftBodyWatchState = state;

    targets.forEach((target) => {
      if (!target) return;
      state.observer.observe(target, {
        subtree: true,
        childList: true,
        characterData: true,
        attributes: true,
        attributeFilter: ["class", "style", "aria-hidden", "data-fieldname", "data-fieldtype"],
      });
    });

    const tick = () => {
      if (frm.__erpwDraftBodyWatchState !== state) return;

      const now = Date.now();
      let ready = true;
      if (typeof settings.isReady === "function") {
        try {
          ready = settings.isReady(frm) !== false;
        } catch (error) {
          ready = false;
        }
      }

      const quiet = now - lastMutationAt >= Math.max(0, Number(settings.quietMs || 0));
      const expired = now - startedAt >= Math.max(0, Number(settings.maxWaitMs || 0));
      if ((ready && quiet) || expired) {
        stopDraftBodyStabilityWatch(frm);
        recordDraftPerformanceEvent(frm, "draft_body_stable", {
          ready,
          quiet,
          expired,
          waitedMs: Math.max(0, Math.round(now - startedAt)),
        });
        if (typeof settings.onStable === "function") {
          settings.onStable(frm, { forced: expired && !(ready && quiet) });
        }
        publishDraftPerformanceSummary(frm, expired ? "draft_body_expired" : "draft_body_stable");
        return;
      }

      state.timer = setTimeout(tick, Math.max(30, Number(settings.pollMs || 60)));
    };

    state.timer = setTimeout(tick, Math.max(30, Number(settings.pollMs || 60)));
    return true;
  }

  function setDraftBodyPending(frm, pending) {
    const $root = getFormRoot(frm);
    if (!$root.length) return false;

    ensureDraftBodyGateStyles();
    const $panels = getDraftBodyPanels(frm);
    const $placeholder = ensureDraftBodyPlaceholder(frm);
    const $supportSurfaces = getDraftSupportSurfaces(frm);
    const keepDraftSupportHidden = !!(frm && typeof frm.is_new === "function" && frm.is_new());
    const wasPending = !!(frm && frm.__erpwDraftBodyPending);

    if (pending) {
      const session = ensureDraftPerformanceSession(frm);
      const alreadyRevealed = !!(session && session.events && (session.events.draft_body_pending_end || session.events.draft_body_stable));
      if (alreadyRevealed && !wasPending) {
        recordDraftPerformanceEvent(frm, "draft_body_regressed_blocked", {
          supportHidden: keepDraftSupportHidden,
        });
        return false;
      }
      if (!wasPending) {
        recordDraftPerformanceEvent(frm, "draft_body_pending_start", {
          supportHidden: keepDraftSupportHidden,
        });
      }
      $root.addClass("erpw-child-draft-body-pending");
      if ($panels.length) {
        $panels
          .addClass("erpw-child-draft-tab-panels")
          .attr("aria-hidden", "true");
      }
      if ($placeholder.length) {
        $placeholder.attr("aria-hidden", "false");
      }
      if ($supportSurfaces.length) {
        $supportSurfaces.addClass("erpw-child-draft-support-hidden").attr("aria-hidden", "true");
      }
      frm.__erpwDraftBodyPending = true;
      return true;
    }

    stopDraftBodyStabilityWatch(frm);
    $root.removeClass("erpw-child-draft-body-pending");
    if ($panels.length) {
      $panels
        .removeClass("erpw-child-draft-tab-panels")
        .removeAttr("aria-hidden");
    }
    if ($placeholder.length) {
      $placeholder.attr("aria-hidden", "true");
    }
    if ($supportSurfaces.length) {
      if (keepDraftSupportHidden) {
        $supportSurfaces.addClass("erpw-child-draft-support-hidden").attr("aria-hidden", "true");
      } else {
        $supportSurfaces.removeClass("erpw-child-draft-support-hidden").removeAttr("aria-hidden");
      }
    }
    if (wasPending) {
      recordDraftPerformanceEvent(frm, "draft_body_pending_end", {
        supportHidden: keepDraftSupportHidden,
      });
    }
    frm.__erpwDraftBodyPending = false;
    publishDraftPerformanceSummary(frm, "draft_body_revealed");
    return true;
  }

  childPageRuntime.observability = Object.assign({}, childPageRuntime.observability || {}, {
    buildDraftPerformanceSummary,
    getLatestDraftPerformance() {
      return draftPerformanceState.latest;
    },
    getDraftPerformanceHistory() {
      return draftPerformanceState.history.slice();
    },
    markFeatureStatus,
    markFeatureReady,
    markFeatureMissing,
    publishDraftPerformanceSummary,
    resetDraftPerformanceSession,
    seedDraftPerformanceSession,
  });

  childPageRuntime.helpers = Object.assign({}, childPageRuntime.helpers || {}, {
    ensureChildPageHostSlot,
    escapeHtml,
    formatMoney,
    resolveBusinessNote,
    getDraftPerformanceSessionKey,
    getDraftSupportSurfaces,
    getDraftBodyPanels,
    getPageContainerRoot,
    getFormRoot,
    getFormTaskState,
    getLayoutWrapper,
    getNativeLayoutAnchor,
    getPageContentRoot,
    applySalesConsoleDocumentActionPolicy,
    applySalesConsoleGuidancePolicy,
    routeToSalesConsoleTarget,
    routeToWorklist,
    routeToDoc,
    routeToList,
    scheduleFormTask,
    ensureDraftBodyPlaceholder,
    publishDraftPerformanceSummary,
    resetDraftPerformanceSession,
    seedDraftPerformanceSession,
    setDraftBodyPending,
    stopDraftBodyStabilityWatch,
    scrollViewportTop,
    watchDraftBodyStability,
  });
})();
