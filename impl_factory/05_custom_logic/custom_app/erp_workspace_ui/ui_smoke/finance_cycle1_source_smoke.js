"use strict";

const assert = require("assert");
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const appRoot = path.resolve(process.env.ERPW_APP_ROOT || path.join(__dirname, ".."));
const financePath = path.join(appRoot, "erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js");
const sidebarPath = path.join(appRoot, "erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js");
const browserRegistryPath = path.join(appRoot, "erp_workspace_ui/public/js/runtime/console/workspace_registry.js");
global.window = global.window || {};
const salesPagePath = path.join(appRoot, "erp_workspace_ui/erp_workspace_ui/page/sales_console/sales_console.js");
const procurementPagePath = path.join(appRoot, "erp_workspace_ui/public/js/procurement_console/procurement_console_page.js");
require(browserRegistryPath);
const finance = require(financePath);
const sidebar = require(sidebarPath);
const browserWorkspaceRegistry = global.window.erpWorkspaceUiWorkspaceRegistry;

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

async function financeRequestLifecycle() {
  let preDispatchCalls = 0;
  const preDispatchCoordinator = finance.createOverviewRequestCoordinator(() => {
    preDispatchCalls += 1;
    return Promise.resolve({ state: "must-not-dispatch" });
  });
  const preDispatchDeparture = preDispatchCoordinator.load();
  preDispatchCoordinator.invalidate();
  const preDispatchResult = await preDispatchDeparture;
  assert.strictEqual(preDispatchCalls, 0, "same-turn invalidation must stop an obsolete Finance RPC before dispatch");
  assert.strictEqual(preDispatchResult.stale, true);

  const pending = [];
  const rendered = [];
  const errors = [];
  const settled = [];
  const coordinator = finance.createOverviewRequestCoordinator(() => {
    const request = deferred();
    pending.push(request);
    return request.promise;
  });

  const initial = coordinator.load({
    onPayload: (payload) => rendered.push(payload.state),
    onSettled: () => settled.push("initial"),
  });
  const duplicate = coordinator.load({ onPayload: () => rendered.push("duplicate") });
  assert.strictEqual(initial, duplicate, "equivalent concurrent Finance loads must deduplicate");
  await Promise.resolve();
  assert.strictEqual(pending.length, 1);

  const refresh = coordinator.load({
    force: true,
    onPayload: (payload) => rendered.push(payload.state),
    onSettled: () => settled.push("refresh"),
  });
  await Promise.resolve();
  assert.strictEqual(pending.length, 2);
  pending[1].resolve({ state: "unavailable" });
  await refresh;
  pending[0].resolve({ state: "ready" });
  const initialResult = await initial;
  assert.strictEqual(initialResult.stale, true, "older ready response must become non-authoritative");
  assert.deepStrictEqual(rendered, ["unavailable"]);
  assert.deepStrictEqual(settled, ["refresh"], "only the authoritative request may announce or restore focus");

  const oldUnavailable = coordinator.load({ force: true, onError: () => errors.push("old") });
  await Promise.resolve();
  const newReady = coordinator.load({ force: true, onPayload: (payload) => rendered.push(payload.state) });
  await Promise.resolve();
  pending[3].resolve({ state: "ready-latest" });
  await newReady;
  pending[2].reject(new Error("stale unavailable"));
  const oldUnavailableResult = await oldUnavailable;
  assert.strictEqual(oldUnavailableResult.stale, true, "older unavailable response must not replace newer ready state");
  assert.deepStrictEqual(errors, []);
  assert.deepStrictEqual(rendered, ["unavailable", "ready-latest"]);

  global.document = global.document || { body: {} };
  const target = {
    setAttribute() {},
    querySelector() { return null; },
    __financeControlDeskRequestCoordinator: coordinator,
    __financeControlDeskOverviewPayload: { state: "older" },
  };
  const pageWrapper = {
    querySelector(selector) {
      return selector === ".layout-main-section" ? target : null;
    },
  };
  let hideHandler = null;
  assert.strictEqual(finance.bindFinancePageHide(pageWrapper, target, (node, handler) => {
    assert.strictEqual(node, pageWrapper, "hide must bind to the actual outer Frappe page wrapper");
    hideHandler = handler;
    return true;
  }), true);
  assert.strictEqual(typeof hideHandler, "function");

  const routeDeparture = coordinator.load({ force: true, onPayload: () => rendered.push("left-route") });
  await Promise.resolve();
  hideHandler();
  pending[4].resolve({ state: "ready-after-route-leave" });
  const routeDepartureResult = await routeDeparture;
  assert.strictEqual(routeDepartureResult.stale, true, "wrapper hide must invalidate its in-flight Finance response");
  assert.strictEqual(target.__financeControlDeskOverviewPayload, null);
  assert(!rendered.includes("left-route"));

  const routeError = coordinator.load({ force: true, onError: () => errors.push("left-route-error") });
  await Promise.resolve();
  hideHandler();
  pending[5].reject(new Error("late route error"));
  const routeErrorResult = await routeError;
  assert.strictEqual(routeErrorResult.stale, true);
  assert(!errors.includes("left-route-error"));

  const returnToFinance = coordinator.load({ onPayload: (payload) => rendered.push(payload.state) });
  await Promise.resolve();
  pending[6].resolve({ state: "ready-after-return" });
  await returnToFinance;
  assert(rendered.includes("ready-after-return"));
}

async function financeFinancialDomAuthority() {
  const originalDocument = global.document;
  const attributes = {};
  const renderHost = {
    innerHTML: "Current: 7; overdue: 3; 125000.00 MMK",
    setAttribute(name, value) { attributes[name] = value; },
  };
  const liveStatus = { textContent: "125000.00 MMK stale announcement" };
  let target = null;
  const presentationShell = {
    get parentElement() { return target; },
    querySelector(selector) {
      if (selector === "[data-finance-render-host]") return renderHost;
      if (selector === "[data-finance-live-status]") return liveStatus;
      return null;
    },
  };
  global.document = {
    body: {},
    head: { appendChild() {} },
    getElementById() { return { id: "finance-control-desk-shell-style" }; },
    createElement() { return {}; },
  };
  const pending = [];
  target = {
    innerHTML: "",
    __financeControlDeskOverviewPayload: { manager: "stale-financial-posture" },
    setAttribute(name, value) { attributes[name] = value; },
    querySelector(selector) {
      if (selector === "[data-finance-presentation-shell]") return presentationShell;
      if (selector === "[data-finance-render-host]") return renderHost;
      if (selector === "[data-finance-live-status]") return liveStatus;
      return null;
    },
  };
  target.__financeControlDeskRequestCoordinator = finance.createOverviewRequestCoordinator(() => {
    const request = deferred();
    pending.push(request);
    return request.promise;
  });

  const first = finance.loadOverviewContext(target, { force: true, userInitiated: true });
  assert.strictEqual(pending.length, 0, "stale Finance DOM must clear before RPC dispatch begins");
  assert.strictEqual(target.__financeControlDeskOverviewPayload, null, "Refresh must invalidate cached Finance posture synchronously");
  assert(!renderHost.innerHTML.includes("125000.00 MMK"), "Refresh must remove stale MMK values synchronously");
  assert(!renderHost.innerHTML.includes("Current: 7"), "Refresh must remove stale counts synchronously");
  assert.strictEqual(liveStatus.textContent, "", "Refresh must clear stale assistive-technology announcements synchronously");
  assert(renderHost.innerHTML.includes('data-finance-cycle1-overview="loading"'), "pending Finance must use a neutral loading state");
  await Promise.resolve();
  assert.strictEqual(pending.length, 1);
  assert.strictEqual(attributes["aria-busy"], "true");

  const second = finance.loadOverviewContext(target, { force: true, userInitiated: true });
  await Promise.resolve();
  pending[1].reject(new Error("new authoritative transport failure"));
  await second;
  assert(renderHost.innerHTML.includes("Controlled unavailable state"), "authoritative failure must remain controlled");
  assert(!renderHost.innerHTML.includes("125000.00 MMK"));
  assert.strictEqual(target.__financeControlDeskOverviewPayload, null);

  pending[0].resolve({ state: { kind: "ready" }, financial: "stale-late-success" });
  const staleFirst = await first;
  assert.strictEqual(staleFirst.stale, true);
  assert(!renderHost.innerHTML.includes("stale-late-success"), "stale success must not restore removed Finance data");
  assert.strictEqual(target.__financeControlDeskOverviewPayload, null);

  renderHost.innerHTML = "Overdue: 9; 99000.00 MMK";
  liveStatus.textContent = "99000.00 MMK stale announcement";
  target.__financeControlDeskOverviewPayload = { manager: "stale-before-hide" };
  finance.invalidateTarget(target);
  assert.strictEqual(target.__financeControlDeskOverviewPayload, null);
  assert(!renderHost.innerHTML.includes("99000.00 MMK"), "route invalidation must clear retained financial markup");
  assert(!renderHost.innerHTML.includes("Overdue: 9"));
  assert.strictEqual(liveStatus.textContent, "");
  assert(renderHost.innerHTML.includes('data-finance-cycle1-overview="loading"'));
  assert.strictEqual(attributes["aria-busy"], "false");

  global.document = originalDocument;
}

async function financeAccessibilityPresentation() {
  const mutations = [];
  let liveText = "";
  const liveStatus = {};
  Object.defineProperty(liveStatus, "textContent", {
    get() { return liveText; },
    set(value) { liveText = String(value); mutations.push(liveText); },
  });
  const focusCalls = [];
  const listeners = new Set();
  const focusDocument = {
    activeElement: null,
    addEventListener(type, handler) { if (type === "focusin") listeners.add(handler); },
    removeEventListener(type, handler) { if (type === "focusin") listeners.delete(handler); },
  };
  const refresh = {
    disabled: true,
    ownerDocument: focusDocument,
    focus(options) { focusCalls.push(options || null); focusDocument.activeElement = this; },
  };
  focusDocument.activeElement = refresh;
  const attributes = {};
  const target = {
    setAttribute(name, value) { attributes[name] = value; },
    querySelector(selector) {
      if (selector === "[data-finance-refresh]") return refresh;
      if (selector === "[data-finance-live-status]") return liveStatus;
      return null;
    },
  };

  const refreshIntent = finance.createFinanceRefreshFocusIntent(target, refresh, { document: focusDocument });
  finance.completeFinanceRequest(target, {
    refreshFocusIntent: refreshIntent,
    statusMessage: finance.completionAnnouncement({ state: { kind: "ready" } }, "payload", true),
  });
  await Promise.resolve();
  assert.strictEqual(attributes["aria-busy"], "false");
  assert.strictEqual(refresh.disabled, false);
  assert.strictEqual(focusCalls.length, 1, "authoritative Refresh completion must restore logical focus once");
  assert.deepStrictEqual(focusCalls[0], { preventScroll: true });
  assert.strictEqual(liveStatus.textContent, "Finance overview refreshed.");
  assert.strictEqual(listeners.size, 0, "settled Refresh intent must release its focus listener");

  assert.strictEqual(
    finance.completionAnnouncement({ state: { kind: "unavailable" } }, "payload", true),
    "Finance overview refreshed. Current posture is unavailable."
  );
  assert.strictEqual(
    finance.completionAnnouncement(null, "error", true),
    "Finance overview could not be refreshed. No financial posture was shown."
  );
  assert.strictEqual(
    finance.completionAnnouncement({ state: { kind: "ready" } }, "payload", false),
    "Finance overview loaded.",
    "initial load must not claim that the user refreshed the page"
  );
  assert.strictEqual(
    finance.visiblePostureValue({ key: "receivables_posture", state: "unavailable", value: "No counts" }),
    "Unavailable"
  );
  assert.strictEqual(
    finance.visiblePostureValue({ key: "payables_posture", state: "ready", value: "Aggregate counts only" }),
    "Aggregate counts only"
  );

  mutations.length = 0;
  liveStatus.textContent = "previous";
  finance.announceFinanceStatus(target, "source_permission_denied");
  await Promise.resolve();
  assert.strictEqual(liveStatus.textContent, "Finance overview updated.", "raw reason codes must not be announced");
  assert.deepStrictEqual(mutations.slice(-2), ["", "Finance overview updated."]);

  mutations.length = 0;
  finance.announceFinanceStatus(target, "Finance overview refreshed.");
  await Promise.resolve();
  finance.announceFinanceStatus(target, "Finance overview refreshed.");
  await Promise.resolve();
  assert.deepStrictEqual(
    mutations,
    ["", "Finance overview refreshed.", "", "Finance overview refreshed."],
    "identical authoritative outcomes must each clear and repopulate the persistent polite status"
  );

  const movedFocusCalls = [];
  const movedListeners = new Set();
  const movedDocument = {
    activeElement: null,
    addEventListener(type, handler) { if (type === "focusin") movedListeners.add(handler); },
    removeEventListener(type, handler) { if (type === "focusin") movedListeners.delete(handler); },
  };
  const movedRefresh = {
    disabled: true,
    ownerDocument: movedDocument,
    focus() { movedFocusCalls.push("refresh"); },
  };
  movedDocument.activeElement = movedRefresh;
  const movedTarget = {
    setAttribute() {},
    querySelector(selector) {
      if (selector === "[data-finance-refresh]") return movedRefresh;
      if (selector === "[data-finance-live-status]") return { textContent: "" };
      return null;
    },
  };
  const movedIntent = finance.createFinanceRefreshFocusIntent(movedTarget, movedRefresh, { document: movedDocument });
  const sidebarControl = { id: "persistent-sidebar-control" };
  movedDocument.activeElement = sidebarControl;
  movedListeners.forEach((handler) => handler({ target: sidebarControl }));
  finance.completeFinanceRequest(movedTarget, {
    refreshFocusIntent: movedIntent,
    statusMessage: "Finance overview refreshed.",
  });
  await Promise.resolve();
  assert.deepStrictEqual(movedFocusCalls, [], "Refresh must not steal focus after the user moves elsewhere");
  assert.strictEqual(movedListeners.size, 0);

  movedDocument.activeElement = movedRefresh;
  const departedIntent = finance.createFinanceRefreshFocusIntent(movedTarget, movedRefresh, { document: movedDocument });
  departedIntent.invalidate();
  assert.strictEqual(departedIntent.shouldRestore(), false, "route departure must cancel Refresh focus authority");
  assert.strictEqual(movedListeners.size, 0);

  const presentationNodes = {};
  const presentationTarget = {
    _innerHTML: "",
    set innerHTML(value) {
      this._innerHTML = value;
      if (value.includes('data-finance-presentation-shell="1"')) {
        presentationNodes.presentationShell = presentationNodes.presentationShell || {
          parentElement: presentationTarget,
          querySelector(selector) {
            if (selector === "[data-finance-render-host]") return presentationNodes.renderHost || null;
            if (selector === "[data-finance-live-status]") return presentationNodes.liveStatus || null;
            return null;
          },
        };
        presentationNodes.renderHost = presentationNodes.renderHost || {
          innerHTML: "",
          parentElement: presentationNodes.presentationShell,
          setAttribute() {},
        };
        presentationNodes.liveStatus = presentationNodes.liveStatus || {
          textContent: "",
          parentElement: presentationNodes.presentationShell,
          offsetParent: presentationNodes.presentationShell,
        };
      }
    },
    get innerHTML() { return this._innerHTML; },
    querySelector(selector) {
      if (selector === "[data-finance-presentation-shell]") return presentationNodes.presentationShell || null;
      return null;
    },
  };
  finance.setHtml(presentationTarget, "first Finance state");
  const persistentShell = presentationNodes.presentationShell;
  const persistentStatus = presentationNodes.liveStatus;
  finance.setHtml(presentationTarget, "second Finance state");
  assert.strictEqual(presentationNodes.presentationShell, persistentShell, "Finance presentation-shell identity must survive rerender");
  assert.strictEqual(presentationNodes.liveStatus, persistentStatus, "Finance live-region identity must survive rerender");
  assert.strictEqual(presentationNodes.presentationShell.parentElement, presentationTarget, "Finance presentation shell must be owned by the Page body");
  assert.strictEqual(presentationNodes.liveStatus.offsetParent, presentationNodes.presentationShell, "Finance live region must use the owned presentation shell as its positioning context");
  assert.strictEqual(presentationNodes.renderHost.innerHTML, "second Finance state");
}

async function normalPageInitialization() {
  const originalDocument = global.document;
  const originalWindow = global.window;
  const originalFrappe = global.frappe;
  const calls = [];
  const eventHandlers = new Map();
  let pageCreations = 0;
  let pendingRequest = null;
  const target = {
    id: "finance-main",
    nodeType: 1,
    innerHTML: "",
    classList: { contains(value) { return value === "layout-main-section"; } },
    setAttribute() {},
    querySelector() { return null; },
  };
  const pageWrapper = {
    page: null,
    contains(node) { return node === target; },
    querySelector() { return null; },
  };
  global.document = {
    body: {},
    head: { appendChild() {} },
    getElementById() { return { id: "finance-control-desk-shell-style" }; },
    createElement() { return {}; },
  };
  const jquery = (node) => {
    assert.strictEqual(node, pageWrapper);
    return {
      off(eventName) { eventHandlers.delete(eventName); return this; },
      on(eventName, handler) { eventHandlers.set(eventName, handler); return this; },
      trigger(eventName) {
        for (const [registeredName, handler] of eventHandlers.entries()) {
          if (registeredName === eventName || registeredName.startsWith(`${eventName}.`)) handler.call(node);
        }
        return this;
      },
    };
  };
  global.window = {
    jQuery: jquery,
    $: jquery,
  };
  global.frappe = {
    ui: {
      make_app_page(options) {
        assert.strictEqual(options.parent, pageWrapper);
        assert.strictEqual(options.single_column, true);
        pageCreations += 1;
        pageWrapper.page = { parent: pageWrapper, body: { 0: target, jquery: "fixture" } };
        return pageWrapper.page;
      },
    },
    call(options) {
      calls.push(options.method);
      pendingRequest = options;
      return { fail() { return this; } };
    },
  };
  const initialLoad = finance.render(pageWrapper);
  const immediateShow = finance.render(pageWrapper);
  await Promise.resolve();
  assert.strictEqual(pageCreations, 1, "initial load and immediate show must create one owned Frappe Page");
  assert.strictEqual(finance.resolveTarget(pageWrapper), target, "Finance must resolve the owned wrapper.page.body");
  assert.strictEqual(calls.length, 1, "normal initialization must call Finance context exactly once");
  assert(eventHandlers.has("hide.financeControlDesk"), "normal initialization must bind the real wrapper hide event");
  jquery(pageWrapper).trigger("hide");
  pendingRequest.callback({ message: { state: { kind: "ready" } } });
  await Promise.all([initialLoad, immediateShow]);
  assert.strictEqual(target.__financeControlDeskOverviewPayload, null);

  const returnLoad = finance.render(pageWrapper);
  await Promise.resolve();
  assert.strictEqual(pageCreations, 1, "return must reuse the same owned Frappe Page");
  assert.strictEqual(calls.length, 2, "return must load a fresh authoritative Finance context");
  pendingRequest.error(new Error("controlled source smoke failure"));
  await returnLoad;
  assert(target.innerHTML.includes("temporarily unavailable"), "return failure must render a controlled nonblank state");
  global.document = originalDocument;
  global.window = originalWindow;
  global.frappe = originalFrappe;
}

async function replacedPageBodyAuthority() {
  const originalDocument = global.document;
  const originalWindow = global.window;
  const originalFrappe = global.frappe;
  const requests = [];
  const handlers = new Map();
  const makeBody = (id) => ({
    id,
    nodeType: 1,
    innerHTML: "",
    classList: { contains(value) { return value === "layout-main-section"; } },
    setAttribute() {},
    querySelector() { return null; },
  });
  const firstBody = makeBody("finance-body-one");
  const secondBody = makeBody("finance-body-two");
  let currentBody = firstBody;
  const pageWrapper = {
    page: null,
    contains(node) { return node === currentBody; },
    querySelector() { return null; },
  };
  pageWrapper.page = { parent: pageWrapper, body: { 0: firstBody, jquery: "fixture" } };
  const jquery = () => ({
    off(eventName) { handlers.delete(eventName); return this; },
    on(eventName, handler) { handlers.set(eventName, handler); return this; },
  });
  global.document = {
    body: {},
    head: { appendChild() {} },
    getElementById() { return { id: "finance-control-desk-shell-style" }; },
    createElement() { return {}; },
  };
  global.window = { jQuery: jquery, $: jquery };
  global.frappe = {
    ui: { make_app_page() { throw new Error("replacement must reuse the supplied Frappe Page"); } },
    call(options) {
      requests.push(options);
      return { fail() { return this; } };
    },
  };

  const oldLoad = finance.render(pageWrapper);
  await Promise.resolve();
  assert.strictEqual(requests.length, 1);
  firstBody.innerHTML = "Current: 8; 88000.00 MMK";
  firstBody.__financeControlDeskOverviewPayload = { manager: "stale-replaced-body" };

  currentBody = secondBody;
  pageWrapper.page.body = { 0: secondBody, jquery: "fixture" };
  const replacementLoad = finance.render(pageWrapper);
  assert.strictEqual(firstBody.__financeControlDeskOverviewPayload, null, "replacement must revoke the old body cache synchronously");
  assert(!firstBody.innerHTML.includes("88000.00 MMK"), "replacement must clear old body financial markup synchronously");
  await Promise.resolve();
  assert.strictEqual(requests.length, 2);

  requests[0].callback({ message: { state: { kind: "ready" }, financial: "late-replaced-body" } });
  const oldResult = await oldLoad;
  assert.strictEqual(oldResult.stale, true, "the replaced body request token must become stale");
  assert(!firstBody.innerHTML.includes("late-replaced-body"));
  assert.strictEqual(firstBody.__financeControlDeskOverviewPayload, null);

  requests[1].error(new Error("controlled replacement-body failure"));
  await replacementLoad;
  assert(secondBody.innerHTML.includes("temporarily unavailable"));

  global.document = originalDocument;
  global.window = originalWindow;
  global.frappe = originalFrappe;
}

async function strictPageOwnershipFailures() {
  const originalDocument = global.document;
  const originalWindow = global.window;
  const originalFrappe = global.frappe;
  let calls = 0;
  let pageCreations = 0;
  const unrelatedBody = {
    nodeType: 1,
    innerHTML: "other-workspace",
    classList: { contains(value) { return value === "layout-main-section"; } },
  };
  const globalWrapper = {
    page: { parent: null, body: { 0: unrelatedBody, jquery: "fixture" } },
    contains(node) { return node === unrelatedBody; },
    querySelector() { return unrelatedBody; },
  };
  globalWrapper.page.parent = globalWrapper;
  const candidateBody = {
    nodeType: 1,
    innerHTML: "candidate-workspace",
    classList: { contains(value) { return value === "layout-main-section"; } },
  };
  const candidateWrapper = {
    page: null,
    contains(node) { return node === candidateBody; },
    querySelector() { return candidateBody; },
  };
  global.document = { body: {}, getElementById() { return null; } };
  global.window = {};
  global.frappe = {
    container: { page: globalWrapper },
    call() { calls += 1; throw new Error("ownership failure must stop before RPC"); },
  };

  await finance.render(null);
  await finance.render(candidateWrapper);
  candidateWrapper.page = { parent: candidateWrapper, body: null };
  global.frappe.ui = { make_app_page() { pageCreations += 1; } };
  await finance.render(candidateWrapper);
  candidateWrapper.page = { parent: globalWrapper, body: { 0: candidateBody, jquery: "fixture" } };
  await finance.render(candidateWrapper);

  assert.strictEqual(calls, 0, "missing ownership must not call the Finance overview RPC");
  assert.strictEqual(pageCreations, 0, "an invalid existing Page must not be replaced implicitly");
  assert.strictEqual(unrelatedBody.innerHTML, "other-workspace", "global Page fallback must not alter another workspace");
  assert.strictEqual(candidateBody.innerHTML, "candidate-workspace", "descendant fallback must not alter an unowned container");
  assert.strictEqual(candidateBody.__financeControlDeskInitialized, undefined);
  assert.strictEqual(candidateBody.__financeControlDeskOverviewPayload, undefined);
  assert.strictEqual(candidateBody.__financeControlDeskRequestCoordinator, undefined);
  assert.strictEqual(candidateBody.__financeRefreshFocusIntent, undefined);
  assert.strictEqual(candidateBody.__financeLiveStatusGeneration, undefined);

  global.document = originalDocument;
  global.window = originalWindow;
  global.frappe = originalFrappe;
}

async function overviewTransportSettlement() {
  let timeoutHandler = null;
  let timeoutCallOptions = null;
  let timeoutFailHandler = null;
  const cancelled = [];
  const timedOut = finance.createOverviewContextRequest((options) => {
    timeoutCallOptions = options;
    return {
      fail(handler) {
        timeoutFailHandler = handler;
        return this;
      },
    };
  }, {
    timeoutMs: 25,
    scheduleTimeout(handler, delay) {
      assert.strictEqual(delay, 25);
      timeoutHandler = handler;
      return 17;
    },
    cancelTimeout(timerId) { cancelled.push(timerId); },
  });
  assert.strictEqual(typeof timeoutHandler, "function");
  assert.strictEqual(typeof timeoutFailHandler, "function");
  timeoutHandler();
  await assert.rejects(timedOut, /timed out/);
  assert.deepStrictEqual(cancelled, [17]);
  timeoutCallOptions.callback({ message: { state: "late-ready" } });
  timeoutFailHandler(new Error("late transport failure"));

  let bypassErrorHandler = null;
  const bypassedError = finance.createOverviewContextRequest(() => ({
    fail(handler) {
      bypassErrorHandler = handler;
      return this;
    },
  }), {
    scheduleTimeout() { return 23; },
    cancelTimeout(timerId) { assert.strictEqual(timerId, 23); },
  });
  bypassErrorHandler(new Error("callback-bypassing Frappe failure"));
  await assert.rejects(bypassedError, /callback-bypassing/);

  let successOptions = null;
  let lateFail = null;
  const successful = finance.createOverviewContextRequest((options) => {
    successOptions = options;
    return { fail(handler) { lateFail = handler; return this; } };
  }, {
    scheduleTimeout() { return 31; },
    cancelTimeout(timerId) { assert.strictEqual(timerId, 31); },
  });
  successOptions.callback({ message: { state: "ready" } });
  lateFail(new Error("must not replace success"));
  assert.deepStrictEqual(await successful, { state: "ready" });
}

function validSidebarPayload(workspaceId) {
  const workspace = browserWorkspaceRegistry.get(workspaceId);
  const items = workspace.fallbackItems.map((item) => ({
    key: item.key,
    label: item.label,
    icon: item.icon,
    target: { ...item.target },
  }));
  return {
    schema_version: sidebar.SIDEBAR_CONTEXT_SCHEMA_VERSION,
    workspace: { workspace_id: workspaceId, title: workspace.title },
    sidebar: {
      schema_version: sidebar.SIDEBAR_CONTEXT_SCHEMA_VERSION,
      workspace_id: workspaceId,
      title: workspace.title,
      mode_label: workspace.modeLabel,
      scope_label: workspaceId === "finance" ? "Read-only overview" : "Representative permission scope",
      active_key: workspaceId === "finance" ? "finance_control_desk_home" : workspace.home,
      home_key: workspaceId === "finance" ? "finance_control_desk_home" : workspace.home,
      items,
      sections: [{ key: workspaceId === "finance" ? "workspace" : "primary", label: "Workspace", items: items.map((item) => ({ ...item, target: { ...item.target } })) }],
    },
  };
}

async function sidebarWorkspaceIsolation() {
  const coordinator = sidebar.createWorkspaceContextCoordinator();
  const financeRequest = deferred();
  const salesRequest = deferred();
  const financeLoad = coordinator.load("finance", () => financeRequest.promise, () => ({ workspace: "finance-fallback" }));
  const financeDuplicate = coordinator.load("finance", () => Promise.reject(new Error("duplicate")), () => ({}));
  assert.strictEqual(financeLoad, financeDuplicate, "same-workspace sidebar loads must deduplicate");
  const salesLoad = coordinator.load("sales", () => salesRequest.promise, () => ({ workspace: "sales-fallback" }));
  salesRequest.resolve({ workspace: "sales" });
  assert.deepStrictEqual(await salesLoad, { workspace: "sales" });
  financeRequest.resolve({ workspace: "finance" });
  assert.deepStrictEqual(await financeLoad, { workspace: "finance" });
  assert.deepStrictEqual(coordinator.peek("sales"), { workspace: "sales" });
  assert.deepStrictEqual(coordinator.peek("finance"), { workspace: "finance" });

  const warehouseRequest = deferred();
  const staleWarehouse = coordinator.load("warehouse", () => warehouseRequest.promise, () => ({ workspace: "warehouse-fallback" }));
  coordinator.prime("warehouse", { workspace: "warehouse-new" });
  warehouseRequest.resolve({ workspace: "warehouse-stale" });
  await staleWarehouse;
  assert.deepStrictEqual(coordinator.peek("warehouse"), { workspace: "warehouse-new" }, "primed route state must supersede an older request");

  const lateFinanceRequest = deferred();
  const lateFinance = coordinator.load("finance-late", () => lateFinanceRequest.promise, () => ({ workspace: "finance-fallback" }));
  coordinator.clear();
  lateFinanceRequest.resolve({ workspace: "finance-stale" });
  await lateFinance;
  assert.strictEqual(coordinator.peek("finance-late"), null, "cleared workspace state must not be repopulated by a late response");

  const isolated = sidebar.createWorkspaceContextCoordinator();
  isolated.prime("finance", { workspace: "finance-current" });
  isolated.prime("sales", { workspace: "sales-current" });
  isolated.clear("sales");
  assert.deepStrictEqual(isolated.peek("finance"), { workspace: "finance-current" }, "Sales refresh must not invalidate Finance state");
  assert.strictEqual(isolated.peek("sales"), null);

  let managedCalls = 0;
  let unmanagedCalls = 0;
  sidebar.synchronizeSidebarRoute(["finance-control-desk"], () => { managedCalls += 1; }, () => { unmanagedCalls += 1; });
  sidebar.synchronizeSidebarRoute(["Form", "User", "Administrator"], () => { managedCalls += 1; }, () => { unmanagedCalls += 1; });
  assert.strictEqual(managedCalls, 1);
  assert.strictEqual(unmanagedCalls, 1);

  let immediateManaged = 0;
  let immediateUnmanaged = 0;
  let deferredManaged = 0;
  sidebar.handleSidebarRouteChange(
    ["finance-control-desk"],
    () => { immediateManaged += 1; },
    () => { immediateUnmanaged += 1; },
    (callback) => { deferredManaged += 1; callback(); }
  );
  assert.strictEqual(immediateManaged, 2, "managed route must synchronize immediately and after AJAX");
  assert.strictEqual(deferredManaged, 1);
  sidebar.handleSidebarRouteChange(
    ["Form", "User", "Administrator"],
    () => { immediateManaged += 1; },
    () => { immediateUnmanaged += 1; },
    () => { throw new Error("unmanaged cleanup must not wait for AJAX"); }
  );
  assert.strictEqual(immediateUnmanaged, 1, "unmanaged route cleanup must run synchronously");
}

function managedSearchIsolation() {
  const salesConfig = {
    workspaceId: "sales",
    routes: browserWorkspaceRegistry.get("sales").routes,
    fallbackItems: browserWorkspaceRegistry.get("sales").fallbackItems,
  };
  const procurementConfig = {
    workspaceId: "procurement",
    routes: browserWorkspaceRegistry.get("procurement").routes,
    fallbackItems: browserWorkspaceRegistry.get("procurement").fallbackItems,
  };
  const financeConfig = {
    workspaceId: "finance",
    routes: browserWorkspaceRegistry.get("finance").routes,
    fallbackItems: browserWorkspaceRegistry.get("finance").fallbackItems,
  };
  const salesRoute = ["sales-console"];
  const safePayload = {
    state: "ready",
    query: "alpha",
    message: "One result found.",
    results: [{
      doctype: "Customer",
      name: "CUST-001",
      label: "Alpha Store",
      meta: "Visible customer",
      target: { kind: "worklist", queue_key: "customer_directory", filters: { keyword: "CUST-001" } },
    }],
  };
  const envelope = sidebar.createManagedSearchEnvelope(salesConfig, salesRoute, 7, "alpha", safePayload);
  assert(envelope, "approved managed search result must create a versioned envelope");
  assert.strictEqual(envelope.schema_version, sidebar.MANAGED_SEARCH_SCHEMA_VERSION);
  assert.strictEqual(envelope.workspace_id, "sales");
  assert.strictEqual(envelope.route_identity, JSON.stringify(salesRoute));
  assert.strictEqual(envelope.request_token, 7);

  let dispatched = 0;
  assert(sidebar.dispatchManagedSearchTarget(envelope, 0, salesConfig, salesRoute, 7, "alpha", () => { dispatched += 1; }));
  assert.strictEqual(dispatched, 1, "approved same-route result must dispatch once");
  assert(!sidebar.dispatchManagedSearchTarget(envelope, 0, financeConfig, ["finance-control-desk"], 7, "alpha", () => { dispatched += 1; }), "delayed Sales result must not dispatch in Finance");
  assert(!sidebar.dispatchManagedSearchTarget(envelope, 0, procurementConfig, ["procurement-console"], 7, "alpha", () => { dispatched += 1; }), "delayed Sales result must not dispatch in Procurement");
  assert(!sidebar.dispatchManagedSearchTarget(envelope, 0, salesConfig, ["Form", "User", "Administrator"], 7, "alpha", () => { dispatched += 1; }), "managed result must not dispatch after native route departure");
  assert(!sidebar.dispatchManagedSearchTarget(envelope, 0, salesConfig, salesRoute, 8, "alpha", () => { dispatched += 1; }), "stale request token must not dispatch");
  assert.strictEqual(dispatched, 1);
  assert(!sidebar.dispatchManagedSearchTarget(envelope, 0, salesConfig, salesRoute, 7, "beta", () => { dispatched += 1; }), "same-route result must not dispatch after query change");

  const generations = sidebar.createManagedSearchGenerationCoordinator();
  const queryA = generations.begin(salesRoute, " alpha ");
  assert.strictEqual(queryA.normalizedQuery, "alpha");
  assert(generations.current(salesRoute, queryA.requestToken, "alpha"));
  const queryB = generations.begin(salesRoute, "beta");
  assert(!generations.current(salesRoute, queryA.requestToken, "alpha"), "input change before debounce must invalidate prior authority");
  const queryC = generations.begin(salesRoute, "gamma");
  assert(!generations.current(salesRoute, queryB.requestToken, "beta"), "rapid A to B to C must invalidate B");
  assert(generations.current(salesRoute, queryC.requestToken, " gamma "));
  assert(!generations.current(["procurement-console"], queryC.requestToken, "gamma"), "route change while pending must invalidate authority");
  const equivalentA = generations.begin(salesRoute, "alpha");
  const equivalentB = generations.begin(salesRoute, " alpha ");
  assert(!generations.current(salesRoute, equivalentA.requestToken, "alpha"), "normalized-equivalent input still starts a fresh generation");
  assert(generations.current(salesRoute, equivalentB.requestToken, "alpha"));
  generations.invalidate();
  assert(!generations.current(salesRoute, equivalentB.requestToken, "alpha"), "invalidated results cannot render or dispatch");

  const unsafeTargets = [
    { kind: "new_doc", doctype: "Sales Invoice" },
    { kind: "form", doctype: "Customer", name: "CUST-001" },
    { kind: "list", doctype: "Sales Invoice" },
    { kind: "report", route: "Accounts Receivable" },
    { kind: "export", doctype: "Sales Invoice" },
    { kind: "print", doctype: "Sales Invoice" },
    { kind: "execution", action: "submit" },
    { kind: "page", route: "sales-console" },
    { kind: "worklist", queue_key: "customer_directory", filters: { keyword: " CUST-001 " } },
    { kind: "worklist", queue_key: "unknown_queue", filters: { keyword: "CUST-001" } },
  ];
  unsafeTargets.forEach((target) => {
    assert(!sidebar.managedSearchTargetAllowed(salesConfig, target), `unsafe target must be denied: ${target.kind}`);
    const payload = JSON.parse(JSON.stringify(safePayload));
    payload.results[0].target = target;
    assert.strictEqual(sidebar.createManagedSearchEnvelope(salesConfig, salesRoute, 7, "alpha", payload), null);
  });

  const mismatchedWorkspaceEnvelope = { ...envelope, workspace_id: "finance" };
  assert(!sidebar.managedSearchEnvelopeCurrent(mismatchedWorkspaceEnvelope, salesConfig, salesRoute, 7, "alpha"));
  const mismatchedRouteEnvelope = { ...envelope, route_identity: JSON.stringify(["procurement-console"]) };
  assert(!sidebar.managedSearchEnvelopeCurrent(mismatchedRouteEnvelope, salesConfig, salesRoute, 7, "alpha"));
  const mismatchedQueryEnvelope = { ...envelope, normalized_query: "beta" };
  assert(!sidebar.managedSearchEnvelopeCurrent(mismatchedQueryEnvelope, salesConfig, salesRoute, 7, "alpha"));
  const mismatchedPayloadQueryEnvelope = { ...envelope, payload: { ...envelope.payload, query: "beta" } };
  assert(!sidebar.managedSearchEnvelopeCurrent(mismatchedPayloadQueryEnvelope, salesConfig, salesRoute, 7, "alpha"));
  assert.strictEqual(sidebar.createManagedSearchEnvelope(salesConfig, salesRoute, 7, "beta", safePayload), null);

  const warehouseWorkspace = browserWorkspaceRegistry.get("warehouse");
  const warehouseConfig = {
    workspaceId: "warehouse",
    routes: warehouseWorkspace.routes,
    fallbackItems: warehouseWorkspace.fallbackItems,
  };
  const warehouseRoute = [warehouseWorkspace.routes.home];
  const warehouseTarget = {
    kind: "warehouse_page",
    route: warehouseWorkspace.routes.receiving,
    route_parts: ["PO-0001"],
  };
  const warehousePayload = {
    state: "ready", query: "PO", message: "One result found.",
    results: [{
      id: "receiving:PO-0001", result_type: "receiving", group_key: "receiving", group: "Receiving",
      doctype: "Purchase Order", name: "PO-0001", label: "PO-0001", title: "PO-0001",
      subtitle: "Supplier receiving review", meta: "Custom review only", target: warehouseTarget,
      primary_action_label: "Open receiving review",
      preview: { title: "PO-0001", subtitle: "Supplier receiving review", chips: ["Open"], facts: [],
        target: warehouseTarget, primary_action_label: "Open receiving review", boundary_note: "Custom review only" },
    }],
  };
  const warehouseEnvelope = sidebar.createManagedSearchEnvelope(warehouseConfig, warehouseRoute, 9, "PO", warehousePayload);
  assert(warehouseEnvelope, "exact Warehouse custom route target must be accepted");
  assert(Object.isFrozen(warehouseEnvelope.payload.results[0].target.route_parts));
  const unsafeWarehousePayload = JSON.parse(JSON.stringify(warehousePayload));
  unsafeWarehousePayload.results[0].target = { kind: "warehouse_page", route: warehouseWorkspace.routes.worklist, route_parts: ["arbitrary-queue"] };
  unsafeWarehousePayload.results[0].preview.target = unsafeWarehousePayload.results[0].target;
  assert.strictEqual(sidebar.createManagedSearchEnvelope(warehouseConfig, warehouseRoute, 9, "PO", unsafeWarehousePayload), null);
  assert(!sidebar.managedSearchTargetAllowed(warehouseConfig, {
    kind: "worklist", queue_key: "inbound_receiving", filters: { keyword: "PO-0001" },
  }), "Warehouse search must not dispatch generic worklist targets");

  const createOption = (index) => {
    const attributes = new Map([
      ["data-erpw-sales-search-index", String(index)],
      ["aria-selected", index === 0 ? "true" : "false"],
    ]);
    const classes = new Set(index === 0 ? ["is-active"] : []);
    const option = {
      id: `erpw-sales-console-search-option-${index}`,
      classList: {
        add(value) { classes.add(value); },
        remove(value) { classes.delete(value); },
        contains(value) { return classes.has(value); },
      },
      getAttribute(name) { return attributes.has(name) ? attributes.get(name) : null; },
      setAttribute(name, value) { attributes.set(name, String(value)); },
      closest(selector) { return selector === "[data-erpw-sales-search-index]" ? option : null; },
      scrollIntoView() {},
    };
    return option;
  };
  const options = [createOption(0), createOption(1), createOption(2)];
  const inputAttributes = new Map([["aria-activedescendant", options[0].id]]);
  const input = {
    setAttribute(name, value) { inputAttributes.set(name, String(value)); },
    removeAttribute(name) { inputAttributes.delete(name); },
    getAttribute(name) { return inputAttributes.has(name) ? inputAttributes.get(name) : null; },
  };
  let focusHandler = null;
  const resultRoot = {
    querySelectorAll() { return options; },
    addEventListener(type, handler) { if (type === "focusin") focusHandler = handler; },
    removeEventListener() {},
    contains(option) { return options.includes(option); },
  };
  let activeIndex = 0;
  assert(sidebar.bindManagedSearchResultFocus(resultRoot, (index) => {
    activeIndex = index;
    sidebar.applyManagedSearchActiveState(resultRoot, input, index);
  }));
  focusHandler({ target: options[2] });
  assert.strictEqual(activeIndex, 2, "direct governed-option focus must synchronize the active index");
  assert.strictEqual(options.filter((option) => option.getAttribute("aria-selected") === "true").length, 1);
  assert.strictEqual(options[2].getAttribute("aria-selected"), "true");
  assert.strictEqual(input.getAttribute("aria-activedescendant"), options[2].id);
  assert.strictEqual(sidebar.applyManagedSearchActiveState(resultRoot, input, -1), -1);
  assert.strictEqual(options.filter((option) => option.getAttribute("aria-selected") === "true").length, 0);
  assert.strictEqual(input.getAttribute("aria-activedescendant"), null, "query/route invalidation must clear active descendant state");

  let focusedNode = null;
  const dialogFocusables = ["first", "middle", "last"].map((name) => ({
    name,
    hidden: false,
    getAttribute() { return null; },
    getClientRects() { return [{}]; },
    focus() { focusedNode = this; },
  }));
  const dialogRoot = { querySelectorAll() { return dialogFocusables; } };
  const forwardEvent = { key: "Tab", shiftKey: false, preventDefault() {}, stopPropagation() {} };
  assert(sidebar.containManagedDialogFocus(forwardEvent, dialogRoot, dialogFocusables[2]));
  assert.strictEqual(focusedNode, dialogFocusables[0], "Tab from the final managed-dialog control must wrap to the first control");
  const backwardEvent = { key: "Tab", shiftKey: true, preventDefault() {}, stopPropagation() {} };
  assert(sidebar.containManagedDialogFocus(backwardEvent, dialogRoot, dialogFocusables[0]));
  assert.strictEqual(focusedNode, dialogFocusables[2], "Shift+Tab from the first managed-dialog control must wrap to the final control");
}

function managedDetailRouteActiveStates() {
  const expected = {
    procurement: {
      poFollowUp: "purchase_order_directory",
      supplierDetail: "supplier_directory",
      itemDetail: "buying_item_directory",
      purchaseRequestReview: "purchase_request_directory",
      purchaseRequestForm: "purchase_request_directory",
      rfqForm: "rfq_directory",
      rfqReview: "rfq_directory",
      supplierQuotationForm: "supplier_quotation_directory",
      supplierQuotationReview: "supplier_quotation_directory",
      purchaseOrderForm: "purchase_order_directory",
    },
    warehouse: {
      receiving: "inbound_receiving",
      picking: "outbound_picking",
      stockException: "stock_exceptions",
      stockPosture: "stock_exceptions",
      movement: "movement_visibility",
    },
  };
  Object.entries(expected).forEach(([workspaceId, routeMap]) => {
    const workspace = browserWorkspaceRegistry.get(workspaceId);
    Object.entries(routeMap).forEach(([routeName, activeKey]) => {
      const routeKey = workspace.routes[routeName];
      assert(routeKey, `${workspaceId}.${routeName} must exist in the browser registry`);
      assert.strictEqual(sidebar.resolveActiveKey([routeKey, "governed-review-context"]), activeKey);
      assert(workspace.fallbackItems.some((item) => item.key === activeKey), `${routeKey} owner must exist in fallback navigation`);
    });
  });
}

function salesInquiryIsolation() {
  const originalFrappe = global.frappe;
  global.frappe = global.frappe || {};
  delete require.cache[require.resolve(salesPagePath)];
  const salesPage = require(salesPagePath);
  let route = ["sales-console"];
  const authority = salesPage.createSalesInquiryAuthority({ getRoute: () => route.slice() });

  const searchA = authority.begin("Alpha", "search");
  const suggestA = authority.begin(" Alpha ", "suggest");
  assert(authority.isCurrent(searchA, "Alpha", "search"), "same-query focus/suggestions must not cancel Search");
  assert(authority.isCurrent(suggestA, "Alpha", "suggest"));
  const suggestB = authority.begin("Beta", "suggest");
  assert(!authority.isCurrent(suggestA, "Alpha", "suggest"));
  assert(authority.isCurrent(searchA, "Alpha", "search"), "per-channel generation must preserve active Search");
  assert(authority.isCurrent(suggestB, " Beta ", "suggest"));

  const searchB = authority.begin("request two", "search");
  const searchC = authority.begin("request three", "search");
  assert(!authority.isCurrent(searchA, "Alpha", "search"));
  assert(!authority.isCurrent(searchB, "request two", "search"));
  assert(authority.isCurrent(searchC, " request   three ", "search"));

  const assist = authority.begin("request three", "assist");
  authority.invalidate("suggest");
  assert(authority.isCurrent(assist, "request three", "assist"), "suggestion cancellation must not strand AI state");
  route = ["procurement-console"];
  assert(!authority.isCurrent(searchC, "request three", "search"));
  route = ["sales-console"];
  assert(authority.isCurrent(searchC, "request three", "search"), "route return still requires hide invalidation");
  authority.invalidate();
  assert(!authority.isCurrent(searchC, "request three", "search"));
  assert(!authority.isCurrent(assist, "request three", "assist"));
  global.frappe = originalFrappe;
}

function procurementQuickFindIsolation() {
  const procurementPage = require(procurementPagePath);
  let routeIdentity = "procurement-console";
  let active = true;
  const authority = procurementPage.createProcurementQuickFindAuthority({
    getRouteIdentity: () => routeIdentity,
    isActive: () => active,
  });

  const queryA = authority.begin(" Alpha ");
  const resultA = { id: "supplier:alpha" };
  const stateA = { authority: queryA, selected: resultA };
  assert(procurementPage.quickFindSelectionCurrent(queryA, "Alpha", true, authority));
  assert(procurementPage.quickFindOpenCurrent(stateA, resultA, queryA, "Alpha", true, authority), "current same-route Open must remain usable");
  assert(!procurementPage.quickFindOpenCurrent(stateA, { id: "other" }, queryA, "Alpha", true, authority), "Open must be bound to the selected result object");
  assert(authority.isCurrent(queryA, "Alpha"));
  const queryB = authority.begin("Beta");
  assert(!authority.isCurrent(queryA, "Alpha"), "Procurement input change must invalidate authority before debounce");
  assert(!procurementPage.quickFindOpenCurrent(stateA, resultA, queryA, "Alpha", true, authority), "prior selection Open must be stale after input generation changes");
  const queryC = authority.begin(" Gamma ");
  assert(!authority.isCurrent(queryB, "Beta"));
  assert(authority.isCurrent(queryC, "Gamma"), "latest Procurement query must remain authoritative");
  assert(!authority.isCurrent(queryC, "Delta"), "same-route prior-query response must be stale");
  routeIdentity = "finance-control-desk";
  assert(!authority.isCurrent(queryC, "Gamma"), "Procurement response must be stale after route departure");
  assert(!procurementPage.quickFindSelectionCurrent(queryC, "Gamma", true, authority), "retained stale option must not store or preview after departure");
  routeIdentity = "procurement-console";
  active = false;
  assert(!authority.isCurrent(queryC, "Gamma"), "inactive Procurement workspace must not accept results");
  active = true;
  authority.invalidate();
  assert(!authority.isCurrent(queryC, "Gamma"), "Clear/workspace switch must invalidate stored Procurement targets");

  const equivalentA = authority.begin("alpha   beta");
  const equivalentB = authority.begin(" alpha beta ");
  assert(!authority.isCurrent(equivalentA, "alpha beta"), "normalized-equivalent input still establishes a fresh generation");
  assert(authority.isCurrent(equivalentB, "alpha beta"));
}

function salesGuideIsolation() {
  const originalFrappe = global.frappe;
  const originalDocument = global.document;
  global.frappe = global.frappe || {};
  global.document = global.document || {};
  delete require.cache[require.resolve(salesPagePath)];
  const salesPage = require(salesPagePath);
  let route = ["sales-console"];
  const callbacks = [];
  const cancelled = [];
  let inserted = 0;
  let removed = 0;
  const scheduler = salesPage.createSalesGuideScheduler({
    getRoute: () => route.slice(),
    ensureGuide: () => { inserted += 1; return true; },
    removeGuide: () => { removed += 1; },
    scheduleInterval(callback) { callbacks.push(callback); return callbacks.length; },
    cancelInterval(timerId) { cancelled.push(timerId); },
  });

  assert(scheduler.schedule(() => {}), "Sales guide must schedule while Sales remains active");
  callbacks[0]();
  assert.strictEqual(inserted, 1, "Sales guide must remain available on the active Sales route");

  assert(scheduler.schedule(() => {}));
  route = ["finance-control-desk"];
  callbacks[1]();
  assert.strictEqual(inserted, 1, "a delayed Sales timer must not insert after navigation to Finance");
  assert(removed >= 1, "route departure must remove stale Sales guide state");

  route = ["sales-console"];
  assert(scheduler.schedule(() => {}));
  const staleReturnCallback = callbacks[2];
  scheduler.cancel();
  assert(scheduler.schedule(() => {}));
  staleReturnCallback();
  assert.strictEqual(inserted, 1, "a pre-departure generation must not insert after rapid return to Sales");
  callbacks[3]();
  assert.strictEqual(inserted, 2, "the fresh Sales generation must preserve approved guide behavior");
  scheduler.cancel();
  assert(cancelled.length >= 4);
  global.frappe = originalFrappe;
  global.document = originalDocument;
}

function salesBootstrapIsolation() {
  const originalFrappe = global.frappe;
  global.frappe = global.frappe || {};
  delete require.cache[require.resolve(salesPagePath)];
  const salesPage = require(salesPagePath);
  let route = ["sales-console"];
  const authority = salesPage.createSalesBootstrapAuthority({ getRoute: () => route.slice() });
  const first = authority.begin();
  assert(authority.isCurrent(first));
  route = ["finance-control-desk"];
  assert(!authority.isCurrent(first), "late Sales bootstrap must be non-authoritative after Finance navigation");
  route = ["sales-console"];
  assert(authority.isCurrent(first), "route identity alone remains stable until wrapper-hide invalidation");
  authority.invalidate();
  assert(!authority.isCurrent(first), "wrapper hide must invalidate the pre-departure bootstrap generation");
  const returned = authority.begin();
  assert(authority.isCurrent(returned), "rapid return must establish a fresh Sales bootstrap generation");

  const calls = { bind: 0, guide: 0, bootstrap: 0 };
  const pageState = { bootstrapState: "invalidated", bootstrapAuthority: authority };
  const wrapper = {
    __salesConsolePageState: pageState,
    __salesConsoleOpenGuide() {},
    __salesConsoleRoot: { id: "cached-sales-root" },
  };
  assert(salesPage.resumeCachedSalesPage(wrapper, true, {
    bindLifecycle(node, state) { assert.strictEqual(node, wrapper); assert.strictEqual(state, pageState); calls.bind += 1; },
    scheduleGuide(callback) { assert.strictEqual(callback, wrapper.__salesConsoleOpenGuide); calls.guide += 1; },
    reloadBootstrap(root, state) { assert.strictEqual(root, wrapper.__salesConsoleRoot); assert.strictEqual(state, pageState); calls.bootstrap += 1; state.bootstrapState = "loading"; },
  }));
  assert.deepStrictEqual(calls, { bind: 1, guide: 1, bootstrap: 1 }, "cached return must restore Guide and restart invalidated bootstrap");
  assert(!salesPage.shouldReloadSalesBootstrap(pageState), "replacement request must prevent duplicate cached reloads");
  salesPage.resumeCachedSalesPage(wrapper, true, {
    bindLifecycle() { calls.bind += 1; },
    scheduleGuide() { calls.guide += 1; },
    reloadBootstrap() { calls.bootstrap += 1; },
  });
  assert.deepStrictEqual(calls, { bind: 2, guide: 2, bootstrap: 1 }, "loading cached bootstrap must deduplicate while preserving Guide");
  pageState.bootstrapState = "ready";
  assert(!salesPage.shouldReloadSalesBootstrap(pageState));
  assert.strictEqual(salesPage.resumeCachedSalesPage(wrapper, false, {}), false, "non-cached route must use normal render path");
  global.frappe = originalFrappe;
}

function nativeHeaderAttributeRestoration() {
  const attributes = new Map([["href", "/desk/home"], ["aria-hidden", "false"], ["tabindex", "0"]]);
  const node = {
    setAttribute(name, value) { attributes.set(name, String(value)); },
    removeAttribute(name) { attributes.delete(name); },
  };
  sidebar.restoreNativeAttribute(node, "href", true, "/desk/home");
  sidebar.restoreNativeAttribute(node, "aria-hidden", true, "false");

  sidebar.restoreNativeAttribute(node, "tabindex", true, "0");
  assert.strictEqual(attributes.get("href"), "/desk/home");
  assert.strictEqual(attributes.get("aria-hidden"), "false");
  assert.strictEqual(attributes.get("tabindex"), "0");
  sidebar.restoreNativeAttribute(node, "href", false, "");
  sidebar.restoreNativeAttribute(node, "aria-hidden", false, "");
  sidebar.restoreNativeAttribute(node, "tabindex", false, "");
  assert.strictEqual(attributes.size, 0, "attributes absent before management must be removed during native cleanup");
}

function sourceContracts() {
  const financeSource = fs.readFileSync(financePath, "utf8");
  const sidebarSource = fs.readFileSync(sidebarPath, "utf8");
  const bootSource = fs.readFileSync(path.join(appRoot, "erp_workspace_ui/boot.py"), "utf8");
  const registrySource = fs.readFileSync(path.join(appRoot, "erp_workspace_ui/public/js/runtime/console/workspace_registry.js"), "utf8");
  const browserBootSource = fs.readFileSync(path.join(appRoot, "erp_workspace_ui/public/js/erp_workspace_ui_boot.js"), "utf8");
  const procurementSource = fs.readFileSync(path.join(appRoot, "erp_workspace_ui/public/js/procurement_console/procurement_console_page.js"), "utf8");
  const childActionsSource = fs.readFileSync(path.join(appRoot, "erp_workspace_ui/public/js/runtime/child_page/child_page_operating_actions.js"), "utf8");
  const childHelpersSource = fs.readFileSync(path.join(appRoot, "erp_workspace_ui/public/js/runtime/child_page/child_page_helpers.js"), "utf8");
  const salesWorklistSource = fs.readFileSync(path.join(appRoot, "erp_workspace_ui/erp_workspace_ui/page/sales_console_worklist/sales_console_worklist.js"), "utf8");
  const salesReportSource = fs.readFileSync(path.join(appRoot, "erp_workspace_ui/erp_workspace_ui/page/sales_console_report/sales_console_report.js"), "utf8");
  const procurementWorklistSource = fs.readFileSync(path.join(appRoot, "erp_workspace_ui/erp_workspace_ui/page/procurement_console_worklist/procurement_console_worklist.js"), "utf8");
  const procurementReportSource = fs.readFileSync(path.join(appRoot, "erp_workspace_ui/erp_workspace_ui/page/procurement_console_report/procurement_console_report.js"), "utf8");
  const pageMetadata = JSON.parse(fs.readFileSync(path.join(appRoot, "erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.json"), "utf8"));
  assert(financeSource.includes('data-finance-cycle1-overview="ready"'));
  assert(financeSource.includes("validateFinanceOverviewPayload(payload)"));
  assert(financeSource.indexOf("validateFinanceOverviewPayload(payload)") < financeSource.indexOf("setHtml(target, renderPayload(payload));"));
  assert(!financeSource.includes("target.__financeControlDeskOverviewPayload = payload;"), "validated raw Finance payloads must not be cached on DOM nodes");
  assert(financeSource.includes("@media (max-width: 860px)"), "Finance layout must retain narrow-screen behavior");
  assert(financeSource.includes('aria-live="polite"'));
  assert(sidebarSource.includes("box-shadow: inset 0 0 0 3px #2563eb;"), "all managed workspaces must share a contained visible keyboard focus ring");
  assert(sidebarSource.includes(':is(a, button, [role="button"], .collapse-sidebar-link):focus-visible'));
  assert(sidebarSource.includes(".erpw-sales-console-sidebar-header:focus-visible"));
  assert(sidebarSource.includes(".erpw-sales-console-sidebar-utility:focus-visible"));
  assert(sidebarSource.includes(".erpw-sales-console-sidebar-link:focus-visible"));
  assert(sidebarSource.includes(".erpw-sales-console-search-result:focus-visible"));
  assert(sidebarSource.includes("inset 0 0 0 3px #2563eb"), "governed search focus must remain inside its overflow container");
  assert(sidebarSource.includes(".erpw-sales-console-search-bar:has(.erpw-sales-console-search-input:focus-visible)"));
  assert(sidebarSource.includes('role="status"'));
  assert(sidebarSource.includes('aria-live="polite"'));
  assert(sidebarSource.includes('aria-atomic="true"'));
  assert(sidebarSource.includes("aria-current=\"page\""), "active managed sidebar item must expose current-page semantics");
  assert(sidebarSource.includes("if (!contextPayload) return false;"), "invalidated sidebar responses must not render fallback");
  assert(sidebarSource.includes("currentConfig.workspaceId !== config.workspaceId"));
  assert(sidebarSource.includes("JSON.stringify(currentRoute || []) !== routeSignature"));
  const browserExports = sidebarSource.slice(sidebarSource.indexOf("root.erpWorkspaceConsoleSidebar = Object.assign"));
  assert(!browserExports.includes("\n    executeTarget,"), "raw target executor must not be browser-global");
  assert(browserExports.includes("\n    executeSidebarTarget,"), "browser exposure must use the governed sidebar dispatcher");
  assert(sidebarSource.includes("delete sidebarRuntime.executeTarget;"), "legacy global executor must be removed during script re-evaluation");
  assert(!sidebar.isManagedRoute(["Form", "User", "Administrator"]), "unmanaged native routes must not own custom sidebar dispatch");
  assert(sidebar.isManagedRoute([browserWorkspaceRegistry.get("finance").routes.home]), "Finance route must remain managed");
  assert(!sidebarSource.includes('target.kind === "new_doc" && target.doctype'), "custom sidebar dispatcher must not retain native new-document navigation");
  assert(!sidebarSource.includes('target.kind === "form" && target.doctype'), "custom sidebar dispatcher must not retain native form navigation");
  assert(!sidebarSource.includes('target.kind === "list" && target.doctype'), "custom sidebar dispatcher must not retain native list navigation");
  assert(!sidebarSource.includes('target.kind === "report" && target.report_name'), "custom sidebar dispatcher must not retain native report navigation");
  assert(childActionsSource.includes("sidebar.executeSidebarTarget"));
  assert(!childActionsSource.includes("sidebar.executeTarget"));
  assert(childHelpersSource.includes("if (!salesTargetAllowed(target)) return false;"));
  assert(childHelpersSource.includes("function isSalesOwnedRoute()"));
  const childHelperExports = childHelpersSource.slice(childHelpersSource.indexOf("childPageRuntime.helpers = Object.assign"));
  assert(!childHelperExports.includes("routeToDoc,"), "arbitrary native Form helper must not remain browser-global");
  assert(!childHelperExports.includes("routeToList,"), "arbitrary native List helper must not remain browser-global");
  assert(!childHelperExports.includes("routeToWorklist,"), "unguarded worklist helper must not remain browser-global");
  const retainedHelper = () => true;
  const childWindow = {
    erpWorkspaceUiChildPage: {
      helpers: {
        routeToDoc: () => false,
        routeToList: () => false,
        routeToWorklist: () => false,
        retainedHelper,
      },
    },
    erpWorkspaceUiWorkspaceRegistry: {
      sales: () => ({ routes: { home: "sales-console", worklist: "sales-console-worklist" } }),
    },
  };
  vm.runInNewContext(childHelpersSource, { window: childWindow, console, setTimeout, clearTimeout });
  assert.strictEqual(childWindow.erpWorkspaceUiChildPage.helpers.routeToDoc, undefined, "re-evaluation must delete stale native Form helper");
  assert.strictEqual(childWindow.erpWorkspaceUiChildPage.helpers.routeToList, undefined, "re-evaluation must delete stale native List helper");
  assert.strictEqual(childWindow.erpWorkspaceUiChildPage.helpers.routeToWorklist, undefined, "re-evaluation must delete stale ungoverned worklist helper");
  assert.strictEqual(childWindow.erpWorkspaceUiChildPage.helpers.retainedHelper, retainedHelper, "unrelated approved helper state must survive re-evaluation");
  assert(childHelpersSource.includes("SALES_OWNED_PAGE_ROUTES.has(pageKey)"), "Sales helper authority must use exact registry routes");
  assert(!childHelpersSource.includes('pageKey.indexOf("sales-console") === 0'), "Sales helper authority must not use a route prefix");
  [salesWorklistSource, salesReportSource, procurementWorklistSource, procurementReportSource].forEach((pageSource) => {
    assert(!pageSource.includes('target.kind === "new_doc"'), "page-local target dispatch must not accept raw new-document targets");
    assert(!pageSource.includes('target.kind === "form"'), "page-local target dispatch must not accept raw native form targets");
    assert(!pageSource.includes('target.kind === "list"'), "page-local target dispatch must not accept raw native list targets");
    assert(!pageSource.includes('target.kind === "report" && target.report_name'), "page-local target dispatch must not accept raw native report targets");
  });
  assert(procurementWorklistSource.includes("const allowedRoutes = new Set"));
  assert(procurementReportSource.includes("const allowedRoutes = new Set"));
  assert(!financeSource.includes("pageDef.on_page_hide = hide"), "unsupported Frappe on_page_hide callback must not be used");
  assert(financeSource.includes('off("hide.financeControlDesk").on("hide.financeControlDesk", handler)'));
  assert(financeSource.includes("createFinanceRefreshFocusIntent"));
  assert(financeSource.includes("event.target !== refresh"), "user focus movement must cancel Refresh restoration authority");
  assert(financeSource.includes("target.__financeLiveStatusGeneration !== generation"));
  assert(financeSource.includes("currentStatus.textContent = safeMessage"));
  ["sales", "procurement", "warehouse", "finance"].forEach((workspaceId) => {
    const serverPayload = validSidebarPayload(workspaceId);
    assert(sidebar.sidebarPayloadMatchesWorkspace(serverPayload, workspaceId), `${workspaceId} server payload must satisfy the shared versioned contract`);
    const browserFallback = JSON.parse(JSON.stringify(serverPayload));
    browserFallback.workspace = { workspaceId };
    assert(sidebar.sidebarPayloadMatchesWorkspace(browserFallback, workspaceId), `${workspaceId} browser fallback must satisfy the shared versioned contract`);
    const runtimeFallback = sidebar.fallbackContext([browserWorkspaceRegistry.get(workspaceId).routes.home]);
    assert(sidebar.sidebarPayloadMatchesWorkspace(runtimeFallback, workspaceId), `${workspaceId} runtime fallback must satisfy its own contract`);
  });
  const unsafeFinanceCopy = validSidebarPayload("finance");
  unsafeFinanceCopy.sidebar.sections[0].items[0].label = "CUST-0001";
  assert(!sidebar.sidebarPayloadMatchesWorkspace(unsafeFinanceCopy, "finance"), "Finance sidebar must reject identity-bearing display text");
  const unapprovedFinanceCopy = validSidebarPayload("finance");
  unapprovedFinanceCopy.sidebar.sections[0].items[0].label = "Quarterly summary";
  assert(!sidebar.sidebarPayloadMatchesWorkspace(unapprovedFinanceCopy, "finance"), "Finance sidebar must accept only exact approved labels");
  const mismatch = validSidebarPayload("finance");
  mismatch.sidebar.workspace_id = "sales";
  assert(!sidebar.sidebarPayloadMatchesWorkspace(mismatch, "finance"));
  const conflictingAlias = validSidebarPayload("finance");
  conflictingAlias.workspace.workspace_id = "sales";
  assert(!sidebar.sidebarPayloadMatchesWorkspace(conflictingAlias, "finance"));
  const unsafeTopLevelTarget = validSidebarPayload("finance");
  unsafeTopLevelTarget.sidebar.items[0].target = { kind: "new_doc", doctype: "Payment Entry" };
  assert(!sidebar.sidebarPayloadMatchesWorkspace(unsafeTopLevelTarget, "finance"));
  assert.strictEqual(unsafeTopLevelTarget.sidebar.sections[0].items[0].target.kind, "page", "top-level target test must leave section target valid");
  const unsafeTarget = validSidebarPayload("finance");
  unsafeTarget.sidebar.sections[0].items[0].target = { kind: "report", route: "Accounts Receivable" };
  assert(!sidebar.sidebarPayloadMatchesWorkspace(unsafeTarget, "finance"));
  assert(!sidebar.sidebarTargetAllowed(browserWorkspaceRegistry.get("finance"), { kind: "new_doc", doctype: "Payment Entry" }));
  assert(!sidebar.sidebarTargetAllowed(browserWorkspaceRegistry.get("finance"), { kind: "page", route: "sales-console" }));
  assert(!sidebar.sidebarTargetAllowed(browserWorkspaceRegistry.get("sales"), { kind: "report", route: "Sales Analytics" }));
  const paddedIdentity = validSidebarPayload("finance");
  paddedIdentity.workspace.workspace_id = " finance ";
  assert(!sidebar.sidebarPayloadMatchesWorkspace(paddedIdentity, "finance"));
  const arrayIdentity = validSidebarPayload("finance");
  arrayIdentity.workspace.workspace_id = ["finance"];
  assert(!sidebar.sidebarPayloadMatchesWorkspace(arrayIdentity, "finance"));
  const paddedRoute = validSidebarPayload("finance");
  paddedRoute.sidebar.sections[0].items[0].target.route = ` ${paddedRoute.sidebar.sections[0].items[0].target.route} `;
  assert(!sidebar.sidebarPayloadMatchesWorkspace(paddedRoute, "finance"));
  const duplicateTopLevelKey = validSidebarPayload("procurement");
  duplicateTopLevelKey.sidebar.items[1].key = duplicateTopLevelKey.sidebar.items[0].key;
  assert(!sidebar.sidebarPayloadMatchesWorkspace(duplicateTopLevelKey, "procurement"), "duplicate top-level sidebar keys must fail the shared payload contract");
  const duplicateSectionKey = validSidebarPayload("warehouse");
  duplicateSectionKey.sidebar.sections[0].items[1].key = duplicateSectionKey.sidebar.sections[0].items[0].key;
  assert(!sidebar.sidebarPayloadMatchesWorkspace(duplicateSectionKey, "warehouse"), "duplicate section sidebar keys must fail the shared payload contract");
  const duplicateAcrossSections = validSidebarPayload("procurement");
  duplicateAcrossSections.sidebar.sections.push({
    key: "secondary",
    label: "Secondary",
    items: [{ ...duplicateAcrossSections.sidebar.sections[0].items[0], target: { ...duplicateAcrossSections.sidebar.sections[0].items[0].target } }],
  });
  assert(!sidebar.sidebarPayloadMatchesWorkspace(duplicateAcrossSections, "procurement"), "duplicate keys across sections must fail the shared payload contract");
  const unregisteredItemKey = validSidebarPayload("procurement");
  unregisteredItemKey.sidebar.items[0].key = "unregistered_workspace_item";
  assert(!sidebar.sidebarPayloadMatchesWorkspace(unregisteredItemKey, "procurement"), "unregistered sidebar keys must fail the shared payload contract");
  const salesPageSource = fs.readFileSync(salesPagePath, "utf8");
  assert(salesPageSource.includes("const primed = sidebarRuntime.primePayload(payload);"));
  assert(salesPageSource.includes("if (primed && typeof sidebarRuntime.syncSidebarNow"));
  assert(!salesPageSource.includes("sidebarRuntime.refresh();"), "a delayed Sales bootstrap must not clear the current workspace");
  assert(salesPageSource.includes("if (!authority.isCurrent(requestToken)) return;"));
  assert(salesPageSource.includes("wrapper.__salesConsoleOpenGuide = openGuide;"));
  assert(salesPageSource.includes("resumeCachedSalesPage(wrapper"));
  assert(salesPageSource.includes('pageState.bootstrapState = "invalidated";'));
  assert(salesPageSource.includes("createSalesInquiryAuthority"));
  assert(salesPageSource.includes("pageState.inquiryAuthority.invalidate();"));
  assert(salesPageSource.includes("pageState.inquiryAuthority.isCurrent(authority"));
  assert(procurementSource.includes("beginQuickFindRequest(query)"));
  assert(procurementSource.includes("invalidateQuickFindRequests();"));
  assert(procurementSource.includes("quickFindRequestCurrent(authority"));
  assert(procurementSource.includes("procurementTargetAllowed(target)"));
  assert(procurementSource.includes("quickFindOpenCurrent(state, result, authority, currentQuery"));
  assert(procurementSource.includes("renderQuickFindPreview($section, state, result, authority)"));
  assert(!procurementSource.includes("requestSerial"));

  const salesHome = browserBootSource.indexOf('salesWorkspaceRoute("launcher", "sales-console-home")');
  const procurementHome = browserBootSource.indexOf('frappe.set_route("procurement-console-home")');
  const financeHome = browserBootSource.indexOf('frappe.set_route("finance-control-desk")');
  const warehouseHome = browserBootSource.indexOf('frappe.set_route("warehouse-console")');
  assert(salesHome >= 0 && procurementHome > salesHome && financeHome > procurementHome && warehouseHome > financeHome,
    "browser landing fallback must preserve Sales > Procurement > Finance > Warehouse priority");

  assert(!financeSource.includes("low_count_policy_not_ready"));
  assert(bootSource.includes('"Accounts Manager"') && bootSource.includes('"Accounts User"'));
  assert(bootSource.includes('"finance-control-desk"'));
  assert(registrySource.includes('home: "finance-control-desk"'));
  assert(registrySource.includes('label: "Overview"'));
  assert.deepStrictEqual(pageMetadata.roles.map((item) => item.role).sort(), ["Accounts Manager", "Accounts User"]);
}

(async () => {
  await financeRequestLifecycle();
  await financeFinancialDomAuthority();
  await financeAccessibilityPresentation();
  await normalPageInitialization();
  await replacedPageBodyAuthority();
  await strictPageOwnershipFailures();
  await overviewTransportSettlement();
  await sidebarWorkspaceIsolation();
  managedSearchIsolation();
  managedDetailRouteActiveStates();
  salesInquiryIsolation();
  procurementQuickFindIsolation();
  salesGuideIsolation();
  salesBootstrapIsolation();
  nativeHeaderAttributeRestoration();
  sourceContracts();
  process.stdout.write("Finance Cycle 1 source smoke passed.\n");
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
