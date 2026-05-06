const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const TIMEOUT = Number(process.env.ERPW_PROCUREMENT_SMOKE_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_PROCUREMENT_ARTIFACT_DIR || path.join(__dirname, "artifacts", "procurement-phase3-assurance");
fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

const USERS = [
  {
    key: "manager",
    label: "Manager",
    username: process.env.ERPW_MANAGER_USERNAME,
    password: process.env.ERPW_MANAGER_PASSWORD,
  },
  {
    key: "user",
    label: "User",
    username: process.env.ERPW_USER_USERNAME,
    password: process.env.ERPW_USER_PASSWORD,
  },
].filter((user) => user.username && user.password);

const WORKLISTS = [
  { key: "purchase_orders_due_soon", route: "/desk/procurement-console-worklist/purchase-orders-due-soon" },
  { key: "purchase_orders_overdue", route: "/desk/procurement-console-worklist/purchase-orders-overdue" },
  { key: "purchase_orders_late_or_unreceived", route: "/desk/procurement-console-worklist/purchase-orders-late-or-unreceived" },
  { key: "purchase_orders_partially_received", route: "/desk/procurement-console-worklist/purchase-orders-partially-received" },
  { key: "purchase_orders_not_billed_visibility", route: "/desk/procurement-console-worklist/purchase-orders-not-billed-visibility" },
  { key: "purchase_orders_supplier_follow_up", route: "/desk/procurement-console-worklist/purchase-orders-supplier-follow-up" },
];

const FORBIDDEN_ACTION_RE = /(approve|reject|submit|cancel|amend|close|unclose|receive|receipt|bill|invoice|pay|payment|item_price|default_supplier|set_default_supplier|supplier_ack|acknowledg)/i;

function assert(condition, message, details = {}) {
  if (!condition) {
    const error = new Error(message);
    error.details = details;
    throw error;
  }
}

function normalizeText(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function routeUrl(route) {
  return new URL(route, BASE_URL).toString();
}

function safeFileName(value) {
  return String(value || "shot").replace(/[^a-z0-9_-]+/gi, "-").replace(/^-+|-+$/g, "").toLowerCase();
}

async function captureSmokeScreenshot(page, name) {
  const file = path.join(ARTIFACT_DIR, `${safeFileName(name)}.png`);
  await page.screenshot({ path: file, fullPage: true });
  return file;
}

function valuesFromContainer(value) {
  if (Array.isArray(value)) return value;
  if (value && typeof value === "object") return Object.values(value);
  return [];
}

function pushAction(actions, action) {
  if (!action) return;
  if (typeof action === "string") {
    actions.push({ key: action, label: action });
    return;
  }
  if (typeof action === "object") actions.push(action);
}

function stateKind(payload) {
  return payload && payload.results && payload.results.state ? payload.results.state.kind : payload && payload.state ? payload.state.kind : "missing";
}

function collectActions(payload) {
  const actions = [];
  const controls = payload && payload.controls ? payload.controls : {};
  valuesFromContainer(controls.actions).forEach((action) => pushAction(actions, action));
  ((payload && payload.results && payload.results.rows) || []).forEach((row) => {
    valuesFromContainer(row.actions).forEach((action) => pushAction(actions, action));
    valuesFromContainer(row.cells).forEach((cell) => {
      if (cell && typeof cell === "object" && cell.actionKey) pushAction(actions, { key: cell.actionKey, label: cell.actionKey });
    });
  });
  Object.values((payload && payload.action_targets) || {}).forEach((target) => pushAction(actions, target));
  return actions;
}

function assertNoForbiddenActions(payload, label) {
  const offenders = collectActions(payload)
    .map((action) => `${action.key || ""} ${action.label || ""} ${action.kind || ""} ${action.route || ""} ${action.doctype || ""}`)
    .filter((value) => FORBIDDEN_ACTION_RE.test(value));
  assert(offenders.length === 0, `${label}: forbidden mutation action exposed`, { offenders });
}

function assertNoNativePurchaseOrderFormTargets(payload, label) {
  const targets = Object.values((payload && payload.action_targets) || {});
  const offenders = targets.filter((target) => target && target.kind === "form" && target.doctype === "Purchase Order");
  assert(offenders.length === 0, `${label}: native Purchase Order form target exposed`, { offenders });
}

async function login(page, user) {
  await page.goto(routeUrl("/login"), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  const userField = page.locator("#login_email, input[name='usr'], input[name='login_email'], input[type='email'], input[type='text']").first();
  const passwordField = page.locator("#login_password, input[name='pwd'], input[name='login_password'], input[type='password']").first();
  const loginButton = page.locator("button:has-text('Login'), button.btn-login, .btn-login").first();
  await userField.waitFor({ state: "visible", timeout: TIMEOUT });
  await userField.fill(user.username);
  await passwordField.fill(user.password);
  await Promise.all([
    page.waitForURL(/\/(?:app|desk)(?:[/?#]|$)/, { waitUntil: "domcontentloaded", timeout: TIMEOUT }),
    loginButton.click(),
  ]);
}

async function openDeskRoute(page, route) {
  await suppressUnsavedFormGuard(page);
  await dismissFrappeModals(page);
  const targetUrl = routeUrl(route);
  const targetPath = new URL(targetUrl).pathname;
  const canUseDeskRouter = await page.evaluate(() => Boolean(window.frappe && typeof frappe.set_route === "function")).catch(() => false);
  if (canUseDeskRouter && /^\/desk\//.test(targetPath)) {
    const routeParts = targetPath.replace(/^\/desk\/?/, "").split("/").filter(Boolean).map((part) => {
      try {
        return decodeURIComponent(part);
      } catch (error) {
        return part;
      }
    });
    await page.evaluate((parts) => {
      frappe.set_route.apply(frappe, parts);
    }, routeParts);
    await page.waitForURL((url) => url.pathname === targetPath, { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  } else {
    await page.goto(targetUrl, { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  }
  if (/\/login(?:[/?#]|$)/.test(page.url())) throw new Error(`Route ${route} redirected to login`);
  await page.waitForFunction(() => Boolean(window.frappe), null, { timeout: TIMEOUT });
  if (/\/desk\/procurement-console/.test(route)) {
    await page.waitForFunction(() => {
      const boot = window.erpWorkspaceUiBoot || {};
      return typeof boot.scheduleProcurementDirectPage === "function" || typeof boot.ensureProcurementDirectPage === "function";
    }, null, { timeout: TIMEOUT }).catch(() => {});
    await page.evaluate(() => {
      const boot = window.erpWorkspaceUiBoot || {};
      if (typeof boot.scheduleProcurementDirectPage === "function") {
        boot.scheduleProcurementDirectPage();
      } else if (typeof boot.ensureProcurementDirectPage === "function") {
        boot.ensureProcurementDirectPage();
      }
    }).catch(() => {});
  }
}

async function callMethod(page, method, args = {}) {
  return page.evaluate(
    async ({ method, args, timeout }) => {
      const body = new URLSearchParams();
      for (const [key, value] of Object.entries(args || {})) {
        body.set(key, typeof value === "string" ? value : JSON.stringify(value));
      }
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), timeout);
      try {
        const response = await fetch(`/api/method/${method}`, {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Frappe-CSRF-Token": (window.frappe && window.frappe.csrf_token) || "",
          },
          body,
          signal: controller.signal,
        });
        const raw = await response.text();
        let data = null;
        try {
          data = raw ? JSON.parse(raw) : null;
        } catch (error) {
          data = { raw };
        }
        return { ok: response.ok, status: response.status, data };
      } catch (error) {
        return { ok: false, status: 0, data: { error: error && error.name === "AbortError" ? `Timed out calling ${method}` : String((error && error.message) || error), method } };
      } finally {
        clearTimeout(timer);
      }
    },
    { method, args, timeout: TIMEOUT }
  );
}

async function checkWorklist(page, item, user) {
  const response = await callMethod(page, "erp_workspace_ui.procurement_console.worklist.get_procurement_console_worklist_context", {
    queue_key: item.key,
  });
  assert(response.ok, `${item.key}: worklist API failed`, response);
  const payload = response.data.message || {};
  const state = stateKind(payload);
  assert(["ready", "empty", "restricted", "unavailable"].includes(state), `${item.key}: invalid state`, { state, payload });
  assertNoForbiddenActions(payload, item.key);
  assertNoNativePurchaseOrderFormTargets(payload, item.key);
  if (user.key === "manager") {
    assert(state === "ready" || state === "empty", `${item.key}: manager did not receive Phase 3 queue`, { state });
  }

  await openDeskRoute(page, item.route);
  await page.locator(".erpw-list-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  if (state === "ready" || state === "empty") {
    await page.locator('[data-erpw-list-action-key="apply_filters"]').first().waitFor({ state: "visible", timeout: TIMEOUT });
    await page.locator('[data-erpw-list-action-key="reset_filters"]').first().waitFor({ state: "visible", timeout: TIMEOUT });
    await page.locator('[data-erpw-list-action-key="refresh"]').first().waitFor({ state: "visible", timeout: TIMEOUT });
  }
  const actionKeys = await page.locator("[data-erpw-list-action-key]").evaluateAll((nodes) =>
    nodes.map((node) => node.getAttribute("data-erpw-list-action-key"))
  );
  const forbidden = actionKeys.filter((key) => FORBIDDEN_ACTION_RE.test(key || ""));
  assert(forbidden.length === 0, `${item.key}: forbidden UI action exposed`, { forbidden });
  if (state === "ready" || state === "empty") {
    assert(actionKeys.slice(0, 3).join(",") === "apply_filters,reset_filters,refresh", `${item.key}: UI action order mismatch`, { actionKeys });
  }
  return { apiState: state, actionKeys: actionKeys.slice(0, 3), firstRow: ((payload.results || {}).rows || [])[0] || null };
}

async function checkDefaultLanding(page, user) {
  await page.waitForFunction(() => Boolean(window.frappe), null, { timeout: TIMEOUT });
  try {
    await page.waitForURL(/\/(?:app|desk)\/procurement-console(?:-home)?(?:[/?#]|$)/, { waitUntil: "domcontentloaded", timeout: 20000 });
  } catch (error) {
    assert(/\/(?:app|desk)\/procurement-console(?:-home)?(?:[/?#]|$)/.test(page.url()), `${user.label}: did not land on Procurement Console after login`, { url: page.url() });
  }
  return page.url();
}

async function checkOverviewStyling(page) {
  await openDeskRoute(page, "/desk/procurement-console");
  await page.locator(".sales-console-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  await page.locator(".sales-console-kpi-card").first().waitFor({ state: "visible", timeout: TIMEOUT });
  const styles = await page.evaluate(() => {
    function px(value) {
      return Number.parseFloat(String(value || "0").replace("px", "")) || 0;
    }
    function compact(style) {
      return {
        display: style.display,
        gridTemplateColumns: style.gridTemplateColumns,
        paddingTop: px(style.paddingTop),
        borderRadius: px(style.borderTopLeftRadius),
        borderTopWidth: px(style.borderTopWidth),
        boxShadow: style.boxShadow,
        backgroundColor: style.backgroundColor,
        backgroundImage: style.backgroundImage,
      };
    }
    const shell = document.querySelector(".sales-console-shell");
    const card = document.querySelector(".sales-console-card.sales-console-header") || document.querySelector(".sales-console-card");
    const kpiGrid = document.querySelector(".sales-console-kpi-grid");
    const kpi = document.querySelector(".sales-console-kpi-card");
    const queueGrid = document.querySelector(".sales-console-queue-grid");
    const pipelineGrid = document.querySelector('[data-section-grid="buying-pipeline"]');
    const priorityGrid = document.querySelector('[data-section-grid="priority-work"]');
    const pipelineFirst = pipelineGrid ? pipelineGrid.querySelector(".sales-console-queue-card") : null;
    const sectionHead = document.querySelector(".sales-console-section-head");
    return {
      shell: compact(getComputedStyle(shell)),
      card: compact(getComputedStyle(card)),
      kpiGrid: compact(getComputedStyle(kpiGrid)),
      kpi: compact(getComputedStyle(kpi)),
      kpiLabels: Array.from(document.querySelectorAll(".sales-console-kpi-label")).map((node) => (node.textContent || "").trim()),
      priorityLabels: priorityGrid ? Array.from(priorityGrid.querySelectorAll(".sales-console-queue-title")).map((node) => (node.textContent || "").trim()) : [],
      queueGrid: compact(getComputedStyle(queueGrid)),
      priorityGrid: priorityGrid ? compact(getComputedStyle(priorityGrid)) : null,
      pipelineGrid: compact(getComputedStyle(pipelineGrid)),
      pipelineStep: pipelineFirst ? getComputedStyle(pipelineFirst, "::before").content : "",
      sectionHead: compact(getComputedStyle(sectionHead)),
    };
  });
  assert(styles.shell.display === "grid", "Overview shell is not using shared grid layout", styles);
  assert(styles.card.paddingTop > 0, "Overview card has no shared padding", styles);
  assert(styles.card.borderRadius > 0, "Overview card has no shared radius", styles);
  assert(styles.card.borderTopWidth > 0 || styles.card.boxShadow !== "none", "Overview card has no border or shadow", styles);
  assert(styles.kpi.display === "grid", "KPI cards look like unstyled browser buttons", styles);
  assert(styles.kpi.paddingTop > 8, "KPI cards have default button padding", styles);
  assert(styles.kpiGrid.display === "grid", "KPI grid is not styled", styles);
  assert(styles.queueGrid.display === "grid", "Queue sections are not styled as grids", styles);
  assert(styles.priorityGrid && styles.priorityGrid.display === "grid", "Priority Work strip is not styled as a grid", styles);
  assert(styles.pipelineGrid.display === "grid", "Buying pipeline is not styled as a process grid", styles);
  assert(styles.pipelineStep && styles.pipelineStep !== "none", "Buying pipeline does not expose visible step markers", styles);
  assert(styles.kpiLabels.slice(0, 3).join("|") === "Overdue POs|Supplier Follow-up|Due Soon", "Hero priority signals should stay focused on three PO follow-up risks", styles);
  assert(styles.priorityLabels.join("|") === "Requests To Source|Expiring Supplier Quotations", "Priority Work strip did not move demand and quotation validity out of the hero", styles);
  assert(["flex", "grid"].includes(styles.sectionHead.display), "Section header layout is not styled", styles);
  return styles;
}

async function checkOverviewDirectLoadStability(page) {
  const states = [];
  for (let index = 0; index < 10; index += 1) {
    await page.goto(routeUrl("/desk/procurement-console"), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
    let elapsed = 0;
    const marks = [];
    for (const mark of [500, 1500]) {
      await page.waitForTimeout(Math.max(0, mark - elapsed));
      elapsed = mark;
      const snapshot = await page.evaluate((mark) => {
        const visible = (node) => {
          if (!node) return false;
          const style = getComputedStyle(node);
          const rect = node.getBoundingClientRect();
          return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
        };
        const shell = document.querySelector('.sales-console-shell[data-erpw-workspace="procurement"]');
        const text = (document.body.innerText || "").replace(/\s+/g, " ").trim();
        return {
          mark,
          url: window.location.href,
          shellVisible: visible(shell),
          shellRuntime: shell ? shell.getAttribute("data-erpw-console-runtime") : "",
          shellBootstrap: shell ? shell.getAttribute("data-erpw-console-bootstrap") : "",
          hasTitle: /Procurement Console/i.test(text),
          hasWorkbench: /Start Buying Work|Priority Work|Buying Pipeline/i.test(text),
          textSample: text.slice(0, 500),
        };
      }, mark);
      marks.push(snapshot);
    }
    const early = marks.find((mark) => mark.mark === 500) || {};
    const ready = marks.find((mark) => mark.mark === 1500) || {};
    assert(early.shellVisible && early.hasTitle, "Procurement Overview showed sidebar-only blank content at 500ms", { index: index + 1, marks });
    assert(ready.shellVisible && ready.hasWorkbench, "Procurement Overview did not render buyer workbench content by 1500ms", { index: index + 1, marks });
    states.push({ iteration: index + 1, marks });
  }
  return states;
}


async function visibleElementCount(page, selector) {
  return page.locator(selector).evaluateAll((nodes) => nodes.filter((node) => {
    const style = window.getComputedStyle(node);
    const rect = node.getBoundingClientRect();
    return style.display !== "none" && style.visibility !== "hidden" && Number(style.opacity || "1") !== 0 && rect.width > 0 && rect.height > 0;
  }).length);
}

async function measureProcurementLayout(page) {
  return page.evaluate(() => {
    const main = document.querySelector(".layout-main-section, .page-container, main") || document.body;
    const filter = document.querySelector(".erpw-list-controls-strip, .erpw-report-controls, .erpw-list-control-form, .erpw-report-control-grid");
    const mainRect = main.getBoundingClientRect();
    const filterRect = filter ? filter.getBoundingClientRect() : { width: 0, height: 0 };
    return {
      clientWidth: document.documentElement.clientWidth,
      bodyScrollWidth: document.body.scrollWidth,
      mainWidth: mainRect.width,
      filterWidth: filterRect.width,
      filterHeight: filterRect.height,
    };
  });
}

function maxLayoutDelta(before, states) {
  return states.reduce((maxDelta, state) => Math.max(
    maxDelta,
    Math.abs(state.clientWidth - before.clientWidth),
    Math.abs(state.bodyScrollWidth - before.bodyScrollWidth),
    Math.abs(state.mainWidth - before.mainWidth),
    Math.abs(state.filterWidth - before.filterWidth)
  ), 0);
}

async function procurementShellState(page) {
  const state = {
    overview: await visibleElementCount(page, ".sales-console-shell[data-erpw-workspace=\"procurement\"]"),
    worklist: await visibleElementCount(page, ".erpw-list-shell"),
    report: await visibleElementCount(page, ".erpw-report-shell"),
    poDetail: await visibleElementCount(page, ".erpw-procurement-po-follow-up-shell"),
    supplierDetail: await visibleElementCount(page, ".erpw-procurement-supplier-detail-shell"),
    itemDetail: await visibleElementCount(page, ".erpw-procurement-item-detail-shell"),
    purchaseRequestReview: await visibleElementCount(page, ".erpw-procurement-purchase-request-review-shell"),
    rfqReview: await visibleElementCount(page, ".erpw-procurement-rfq-review-shell"),
    supplierQuotationReview: await visibleElementCount(page, ".erpw-procurement-supplier-quotation-review-shell"),
  };
  state.total = state.overview + state.worklist + state.report + state.poDetail + state.supplierDetail + state.itemDetail + state.purchaseRequestReview + state.rfqReview + state.supplierQuotationReview;
  state.url = page.url();
  return state;
}

async function procurementChromeSnapshot(page, label) {
  await page.waitForTimeout(800);
  return page.evaluate((label) => {
    function visible(node) {
      if (!(node instanceof HTMLElement)) return false;
      const style = window.getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return style.display !== "none" && style.visibility !== "hidden" && Number(style.opacity || "1") !== 0 && rect.width > 0 && rect.height > 0;
    }
    function textOf(node) {
      return String((node && node.textContent) || "").replace(/\s+/g, " ").trim();
    }
    const pageHeads = Array.from(document.querySelectorAll(".page-head")).filter(visible);
    const managedChromeHeads = pageHeads.filter((node) => node.getAttribute("data-erpw-procurement-managed-chrome") === "1");
    const visiblePageHeadIcons = pageHeads.flatMap((node) => {
      return Array.from(node.querySelectorAll(".page-icon, .indicator-pill, .title-area > .icon, .title-area > svg")).filter(visible);
    });
    const visibleManagedChromeIcons = managedChromeHeads.flatMap((node) => {
      return Array.from(node.querySelectorAll(".page-icon, .indicator-pill, .title-area > .icon, .title-area > svg")).filter(visible);
    });
    const breadcrumbRows = Array.from(document.querySelectorAll(".navbar-breadcrumbs, .breadcrumb, .breadcrumbs, .page-breadcrumbs, .breadcrumb-container, .page-title")).filter(visible);
    const headerRows = pageHeads.map((node) => ({
      text: textOf(node),
      links: Array.from(node.querySelectorAll("a")).map((link) => ({
        text: textOf(link),
        href: link.href || "",
        route: link.getAttribute("data-route") || "",
      })),
    }));
    const breadcrumbDetails = breadcrumbRows.map((node) => ({
      text: textOf(node),
      links: Array.from(node.querySelectorAll("a")).map((link) => ({
        text: textOf(link),
        href: link.href || "",
        route: link.getAttribute("data-route") || "",
      })),
    })).filter((row) => row.text || row.links.length);
    const nativeParentWords = /^(Stock|Buying|Material Request|Request for Quotation|Supplier Quotation|Purchase Order|Supplier|Item)$/i;
    const parentLinkLeaks = breadcrumbDetails.flatMap((row) => row.links).filter((link) => {
      const label = String(link.text || "").replace(/\s+/g, " ").trim();
      const href = String(link.href || "");
      const route = String(link.route || "");
      return nativeParentWords.test(label) && !/procurement-console/i.test(href + " " + route);
    });
    const parentTextLeaks = headerRows.filter((row) => /^(Stock|Buying)(Material Request|Request for Quotation|Supplier Quotation|Purchase Order|Supplier|Item)/i.test(row.text));
    const overviewVisible = Array.from(document.querySelectorAll(".sales-console-title, .sales-console-header-note")).some((node) => visible(node) && /Procurement Console|Buyer workbench/i.test(textOf(node)));
    return {
      label,
      url: window.location.href,
      route: window.frappe && typeof frappe.get_route === "function" ? frappe.get_route() : [],
      pageHeadCount: pageHeads.length,
      managedChromeHeadCount: managedChromeHeads.length,
      visiblePageHeadIconCount: visiblePageHeadIcons.length,
      visibleManagedChromeIconCount: visibleManagedChromeIcons.length,
      breadcrumbRowCount: breadcrumbDetails.length,
      headerRows,
      breadcrumbRows: breadcrumbDetails,
      parentLinkLeaks,
      parentTextLeaks: parentTextLeaks.map((row) => row.text),
      overviewVisible,
      procurementShellState: {
        overview: document.querySelectorAll('.sales-console-shell[data-erpw-workspace="procurement"]').length,
        worklist: document.querySelectorAll(".erpw-procurement-console-worklist-page").length,
        report: document.querySelectorAll(".erpw-procurement-console-report-page").length,
        poDetail: document.querySelectorAll(".erpw-procurement-po-follow-up-page").length,
        supplierDetail: document.querySelectorAll(".erpw-procurement-supplier-detail-page").length,
        itemDetail: document.querySelectorAll(".erpw-procurement-item-detail-page").length,
      },
    };
  }, label);
}

async function suppressUnsavedFormGuard(page) {
  await page.evaluate(() => {
    window.onbeforeunload = null;
    if (window.cur_frm) {
      try {
        if (cur_frm.doc) cur_frm.doc.__unsaved = 0;
        cur_frm.dirty = () => false;
        cur_frm.is_dirty = () => false;
      } catch (error) {
        // Smoke-only navigation guard cleanup.
      }
    }
  }).catch(() => {});
}

async function dismissFrappeModals(page) {
  await page.keyboard.press("Escape").catch(() => {});
  await page.evaluate(() => {
    const modals = Array.from(document.querySelectorAll(".modal.show, .modal.fade.show"));
    for (const modal of modals) {
      try {
        if (window.jQuery && typeof window.jQuery(modal).modal === "function") {
          window.jQuery(modal).modal("hide");
        }
      } catch (error) {
        // Smoke-only modal cleanup.
      }
      modal.classList.remove("show");
      modal.setAttribute("aria-hidden", "true");
      modal.style.display = "none";
    }
    document.querySelectorAll(".modal-backdrop").forEach((node) => node.remove());
    document.body.classList.remove("modal-open");
    document.body.style.removeProperty("padding-right");
  }).catch(() => {});
  await page.waitForFunction(() => !document.querySelector(".modal.show, .modal.fade.show"), null, { timeout: 3000 }).catch(() => {});
}

async function firstVisibleRowName(page, queueKey) {
  const response = await callMethod(page, "erp_workspace_ui.procurement_console.worklist.get_procurement_console_worklist_context", { queue_key: queueKey });
  if (!response.ok) return "";
  const rows = (((response.data || {}).message || {}).results || {}).rows || [];
  const row = rows[0] || {};
  return row.name || row.key || "";
}

async function clickProcurementCreateAction(page, actionKey, expectedPathPattern) {
  await suppressUnsavedFormGuard(page);
  await openDeskRoute(page, "/desk/procurement-console");
  await page.locator('[data-erpw-console-bootstrap="ready"]').first().waitFor({ state: "attached", timeout: TIMEOUT });
  await dismissFrappeModals(page);
  await page.locator(`[data-erpw-procurement-create-action="${actionKey}"]`).first().click();
  await page.waitForURL((url) => expectedPathPattern.test(url.pathname), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
}

async function checkProcurementNativeChromeLifecycle(page, user) {
  if (user.key !== "manager") return { skipped: "native create chrome is checked with manager permissions" };
  const snapshots = [];
  const createRoutes = [
    { key: "new_purchase_request", label: "New Purchase Request", path: /\/desk\/material-request\// },
    { key: "new_rfq", label: "New RFQ", path: /\/desk\/request-for-quotation\// },
    { key: "new_supplier_quotation", label: "New Supplier Quotation", path: /\/desk\/supplier-quotation\// },
    { key: "new_purchase_order", label: "New Purchase Order", path: /\/desk\/purchase-order\// },
  ];
  await openDeskRoute(page, "/desk/procurement-console");
  snapshots.push(await procurementChromeSnapshot(page, "Procurement Overview"));
  for (const item of createRoutes) {
    await clickProcurementCreateAction(page, item.key, item.path);
    snapshots.push(await procurementChromeSnapshot(page, item.label));
    const parentCrumb = page.locator('[data-erpw-procurement-native-kind="parent"]').first();
    await parentCrumb.waitFor({ state: "visible", timeout: TIMEOUT });
    await suppressUnsavedFormGuard(page);
    await dismissFrappeModals(page);
    await parentCrumb.click();
    await page.waitForURL(/\/desk\/procurement-console-worklist\//, { waitUntil: "domcontentloaded", timeout: TIMEOUT });
    assert(!/\/desk\/(stock|buying|material-request|request-for-quotation|supplier-quotation|purchase-order)(?:[/?#]|$)/i.test(page.url()), `${item.label}: parent breadcrumb leaked to native ERP route`, { url: page.url() });
  }

  await openDeskRoute(page, "/desk/procurement-console-report/supplier-quotation-comparison");
  await page.locator(".erpw-report-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  snapshots.push(await procurementChromeSnapshot(page, "Quote Comparison"));

  const supplierName = await firstVisibleRowName(page, "supplier_directory");
  if (supplierName) {
    await openDeskRoute(page, `/desk/procurement-console-supplier/${encodeURIComponent(supplierName)}`);
    await page.locator(".erpw-procurement-supplier-detail-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
    snapshots.push(await procurementChromeSnapshot(page, "Supplier Detail"));
  }
  const itemName = await firstVisibleRowName(page, "buying_item_directory");
  if (itemName) {
    await openDeskRoute(page, `/desk/procurement-console-item/${encodeURIComponent(itemName)}`);
    await page.locator(".erpw-procurement-item-detail-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
    snapshots.push(await procurementChromeSnapshot(page, "Item Detail"));
  }
  const purchaseOrder = await firstVisibleRowName(page, "purchase_orders_due_soon") || await firstVisibleRowName(page, "purchase_orders_overdue");
  if (purchaseOrder) {
    await openDeskRoute(page, `/desk/procurement-console-po-follow-up/${encodeURIComponent(purchaseOrder)}`);
    await page.locator(".erpw-procurement-po-follow-up-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
    snapshots.push(await procurementChromeSnapshot(page, "PO Follow-up Detail"));
  }

  const defects = snapshots.filter((snapshot) => {
    const duplicateHeader = snapshot.pageHeadCount > 1;
    const parentLeak = (snapshot.parentLinkLeaks || []).length > 0 || (snapshot.parentTextLeaks || []).length > 0;
    const oldOverview = snapshot.label !== "Procurement Overview" && snapshot.overviewVisible;
    return duplicateHeader || parentLeak || oldOverview;
  });
  assert(defects.length === 0, "Procurement native chrome has duplicate headers or ERPNext parent breadcrumb leaks", { defects, snapshots });
  return { snapshots };
}

async function checkQuoteComparisonHeaderLifecycle(page) {
  const snapshots = [];
  for (let index = 0; index < 5; index += 1) {
    await openDeskRoute(page, "/desk/procurement-console-report/supplier-quotation-comparison");
    await page.locator(".erpw-report-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
    const snapshot = await procurementChromeSnapshot(page, `Quote Comparison repeat ${index + 1}`);
    snapshots.push(snapshot);
    assert(snapshot.pageHeadCount <= 1, "Quote Comparison repeated open created duplicate page headers", snapshot);
    assert(snapshot.procurementShellState.report === 1, "Quote Comparison repeated open created duplicate report shells", snapshot);
  }
  return { snapshots };
}

async function checkDetailActionStyling(page, selector, label) {
  const shell = page.locator(selector).first();
  await shell.waitFor({ state: "visible", timeout: TIMEOUT });
  const largeCardActionCount = await visibleElementCount(page, `${selector} .erpw-child-action`);
  const actions = await shell.locator(".erpw-child-toolbar-action").evaluateAll((nodes) => nodes.map((node) => {
    const style = getComputedStyle(node);
    const rect = node.getBoundingClientRect();
    return {
      text: (node.textContent || "").replace(/\s+/g, " ").trim(),
      padding: style.padding,
      borderRadius: style.borderRadius,
      border: style.border,
      display: style.display,
      height: rect.height,
      width: rect.width,
      iconSvgCount: node.querySelectorAll(".erpw-child-toolbar-action-icon svg").length,
    };
  }));
  assert(largeCardActionCount === 0, `${label}: simple detail controls still use large action-card buttons`, { largeCardActionCount });
  assert(actions.length > 0, `${label}: no compact shared toolbar buttons rendered`, { actions });
  assert(actions[0].text.match(/Back/i), `${label}: Back action should be first`, { actions });
  assert(actions.some((action) => /Refresh/i.test(action.text)), `${label}: Refresh action missing`, { actions });
  assert(actions.every((action) => action.display === "inline-flex" || action.display === "flex"), `${label}: toolbar buttons are not using compact shared styling`, { actions });
  assert(actions.every((action) => action.height <= 44 && action.width < 260), `${label}: toolbar button still looks like a large card`, { actions });
  assert(actions.every((action) => !/^0px/.test(action.borderRadius) && !/ 0px /.test(action.padding)), `${label}: toolbar button styling looks unstyled`, { actions });
  assert(actions.every((action) => action.iconSvgCount > 0), `${label}: compact toolbar buttons are missing shared icons`, { actions });
  return actions;
}

async function exerciseDetailRefresh(page, selector, shellKey, label) {
  const refresh = page.locator(`${selector} .erpw-child-toolbar-action`, { hasText: "Refresh" }).first();
  await refresh.waitFor({ state: "visible", timeout: TIMEOUT });
  await refresh.click();
  await page.waitForTimeout(900);
  return assertSingleProcurementShell(page, shellKey, `${label}: after Refresh`);
}

async function exerciseDetailBack(page, selector, expectedPath, shellKey, label) {
  const back = page.locator(`${selector} .erpw-child-toolbar-action`, { hasText: /Back/i }).first();
  await back.waitFor({ state: "visible", timeout: TIMEOUT });
  await back.click();
  await page.waitForURL((url) => url.pathname === expectedPath, { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  return assertSingleProcurementShell(page, shellKey, `${label}: after Back`);
}


async function checkCompactDetailHeader(page, selector, label) {
  const shell = page.locator(selector).first();
  await shell.waitFor({ state: "visible", timeout: TIMEOUT });
  await captureSmokeScreenshot(page, `${label}-detail-page`);
  const styles = await shell.locator(".erpw-child-summary").first().evaluate((node) => {
    const style = getComputedStyle(node);
    const rect = node.getBoundingClientRect();
    const title = node.querySelector(".erpw-child-title");
    const titleStyle = title ? getComputedStyle(title) : null;
    return {
      height: rect.height,
      paddingTop: Number.parseFloat(style.paddingTop) || 0,
      paddingLeft: Number.parseFloat(style.paddingLeft) || 0,
      borderRadius: Number.parseFloat(style.borderTopLeftRadius) || 0,
      borderTopWidth: Number.parseFloat(style.borderTopWidth) || 0,
      boxShadow: style.boxShadow,
      backgroundColor: style.backgroundColor,
      backgroundImage: style.backgroundImage,
      color: style.color,
      titleColor: titleStyle ? titleStyle.color : "",
      overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    };
  });
  assert(styles.paddingTop > 0 && styles.paddingLeft > 0, `${label}: detail header has no shared compact padding`, styles);
  assert(styles.borderRadius > 0, `${label}: detail header has no premium radius`, styles);
  assert(styles.borderTopWidth > 0 || styles.boxShadow !== "none", `${label}: detail header has no border or elevation`, styles);
  assert(!/gradient/i.test(styles.backgroundImage || ""), `${label}: detail header still uses Overview-style dark hero gradient`, styles);
  assert(!/rgb\(15, 23, 42\)|rgb\(17, 24, 39\)|rgb\(30, 41, 59\)/i.test(styles.backgroundColor || ""), `${label}: detail header still uses dark Overview hero background`, styles);
  assert(styles.height <= 320, `${label}: detail header is too tall for compact detail treatment`, styles);
  assert(styles.overflowX <= 1, `${label}: detail page introduced horizontal overflow`, styles);
  return styles;
}

async function checkProcurementTargetAudit(page, user) {
  const audit = [];
  const expectations = [
    { queue: "supplier_directory", label: "Supplier Directory", actionKey: "open_record", actionLabel: "Open", classification: "productized Procurement page", route: "procurement-console-supplier", shellKey: "supplierDetail", shellSelector: ".erpw-procurement-supplier-detail-shell" },
    { queue: "buying_item_directory", label: "Buying Item Directory", actionKey: "open_record", actionLabel: "Open", classification: "productized Procurement page", route: "procurement-console-item", shellKey: "itemDetail", shellSelector: ".erpw-procurement-item-detail-shell" },
    { queue: "purchase_order_directory", label: "Purchase Order Directory", actionKey: "open_record", actionLabel: "Open", classification: "productized Procurement PO Follow-up Detail", route: "procurement-console-po-follow-up", shellKey: "poDetail", shellSelector: ".erpw-procurement-po-follow-up-shell" },
    { queue: "purchase_request_directory", label: "Purchase Request Directory", actionKey: "open_record", actionLabel: "Review Request", classification: "productized Procurement Purchase Request Review", route: "procurement-console-purchase-request-review", shellKey: "purchaseRequestReview", shellSelector: ".erpw-procurement-purchase-request-review-shell" },
    { queue: "requests_to_source", label: "Requests To Source", actionKey: "open_record", actionLabel: "Review Request", classification: "productized Procurement Purchase Request Review", route: "procurement-console-purchase-request-review", shellKey: "purchaseRequestReview", shellSelector: ".erpw-procurement-purchase-request-review-shell" },
    { queue: "rfq_directory", label: "RFQ Directory", actionKey: "open_record", actionLabel: "Review RFQ", classification: "productized Procurement RFQ Review", route: "procurement-console-rfq-review", shellKey: "rfqReview", shellSelector: ".erpw-procurement-rfq-review-shell" },
    { queue: "rfqs_awaiting_supplier_response", label: "RFQs Awaiting Supplier Response", actionKey: "open_record", actionLabel: "Review RFQ", classification: "productized Procurement RFQ Review", route: "procurement-console-rfq-review", shellKey: "rfqReview", shellSelector: ".erpw-procurement-rfq-review-shell" },
    { queue: "supplier_quotation_directory", label: "Supplier Quotation Directory", actionKey: "open_record", actionLabel: "Review Quote", classification: "productized Procurement Supplier Quotation Review", route: "procurement-console-supplier-quotation-review", shellKey: "supplierQuotationReview", shellSelector: ".erpw-procurement-supplier-quotation-review-shell" },
    { queue: "supplier_quotations_to_compare", label: "Supplier Quotations To Compare", actionKey: "open_record", actionLabel: "Review Quote", classification: "productized Procurement Supplier Quotation Review", route: "procurement-console-supplier-quotation-review", shellKey: "supplierQuotationReview", shellSelector: ".erpw-procurement-supplier-quotation-review-shell" },
    { queue: "supplier_quotations_expiring", label: "Supplier Quotations Expiring", actionKey: "open_record", actionLabel: "Review Quote", classification: "productized Procurement Supplier Quotation Review", route: "procurement-console-supplier-quotation-review", shellKey: "supplierQuotationReview", shellSelector: ".erpw-procurement-supplier-quotation-review-shell" },
  ];
  for (const item of expectations) {
    const payload = await worklistPayload(page, item.queue);
    const firstRow = ((payload.results || {}).rows || [])[0] || {};
    const state = stateKind(payload);
    const result = { queue: item.queue, classification: item.classification, state, skipped: !firstRow.key };
    assertNoForbiddenActions(payload, `${item.queue}_worklist`);
    if (firstRow.key) {
      const actions = Array.isArray(firstRow.actions) ? firstRow.actions : [];
      const target = (payload.action_targets || {})[`row:${firstRow.key}:${item.actionKey}`] || {};
      result.actionKey = item.actionKey;
      result.targetKind = target.kind;
      result.targetRoute = target.route || "";
      result.targetDoctype = target.doctype || "";
      assert(actions.some((action) => action.key === item.actionKey && action.label === item.actionLabel), `${item.label}: expected business row action missing`, { actions, item });
      assert(!actions.some((action) => /Open ERP Form/i.test(action.label || "")), `${item.label}: productized worklist still exposes generic Open ERP Form row action`, { actions });
      assert(target.kind === "page" && target.route === item.route, `${item.label}: productized target mismatch`, { target, item });
      assert(!Object.values(payload.action_targets || {}).some((candidate) => candidate && candidate.kind === "form" && /Material Request|Request for Quotation|Supplier Quotation/.test(candidate.doctype || "")), `${item.label}: productized worklist still exposes native form row target`, { targets: payload.action_targets });
    }
    audit.push(result);
  }

  const clickChecks = expectations.filter((item) => item.route && item.queue !== "supplier_directory" && item.queue !== "buying_item_directory" && item.queue !== "purchase_order_directory");
  for (const item of clickChecks) {
    const payload = await worklistPayload(page, item.queue);
    const firstRow = ((payload.results || {}).rows || [])[0] || {};
    if (!firstRow.key) continue;
    await openDeskRoute(page, `/desk/procurement-console-worklist/${item.queue.replace(/_/g, "-")}`);
    const beforeText = normalizeText(await page.locator(".erpw-list-shell").first().innerText({ timeout: TIMEOUT }));
    assert(!/Open ERP Form/i.test(beforeText), `${item.label}: visible worklist still shows Open ERP Form`, { beforeText });
    await page.waitForFunction(
      ({ actionKey, rowKey }) => Array.from(document.querySelectorAll("[data-erpw-list-action-key]")).some((node) =>
        node.getAttribute("data-erpw-list-action-key") === actionKey && node.getAttribute("data-erpw-row-key") === rowKey
      ),
      { actionKey: item.actionKey, rowKey: firstRow.key },
      { timeout: TIMEOUT }
    );
    await page.evaluate(({ actionKey, rowKey }) => {
      const node = Array.from(document.querySelectorAll("[data-erpw-list-action-key]")).find((candidate) =>
        candidate.getAttribute("data-erpw-list-action-key") === actionKey && candidate.getAttribute("data-erpw-row-key") === rowKey
      );
      if (!node) throw new Error(`Missing row action ${actionKey} for ${rowKey}`);
      node.click();
    }, { actionKey: item.actionKey, rowKey: firstRow.key });
    await page.waitForURL((url) => url.pathname === `/desk/${item.route}/${encodeURIComponent(firstRow.key)}`, { waitUntil: "domcontentloaded", timeout: TIMEOUT });
    await page.locator(item.shellSelector).first().waitFor({ state: "visible", timeout: TIMEOUT });
    await assertSingleProcurementShell(page, item.shellKey, `${item.label}: productized review route`);
    const reviewText = normalizeText(await page.locator(item.shellSelector).first().innerText({ timeout: TIMEOUT }));
    assert(reviewText.includes(firstRow.key), `${item.label}: productized review did not show selected document`, { firstRow, reviewText });
    assert(/Read-only|review/i.test(reviewText), `${item.label}: productized review lacks read-only buyer review context`, { reviewText });
    const forbiddenReviewActions = await page.locator(`${item.shellSelector} button, ${item.shellSelector} a`).evaluateAll((nodes) =>
      nodes.map((node) => (node.textContent || "").replace(/\s+/g, " ").trim()).filter((label) =>
        /^(Approve|Reject|Submit|Cancel|Amend|Close|Unclose|Receive|Bill|Pay|Set Default Supplier|Update Item Price|Item Price)$/i.test(label)
      )
    );
    assert(forbiddenReviewActions.length === 0, `${item.label}: productized review exposes forbidden mutation action`, { forbiddenReviewActions, reviewText });
  }
  return audit;
}

async function waitForProcurementShell(page, shellKey, label = "Procurement shell") {
  const selectors = {
    overview: ".sales-console-shell[data-erpw-workspace=\"procurement\"]",
    worklist: ".erpw-list-shell",
    report: ".erpw-report-shell",
    poDetail: ".erpw-procurement-po-follow-up-shell",
    supplierDetail: ".erpw-procurement-supplier-detail-shell",
    itemDetail: ".erpw-procurement-item-detail-shell",
    purchaseRequestReview: ".erpw-procurement-purchase-request-review-shell",
    rfqReview: ".erpw-procurement-rfq-review-shell",
    supplierQuotationReview: ".erpw-procurement-supplier-quotation-review-shell",
  };
  const selector = selectors[shellKey];
  assert(selector, `Unknown procurement shell key ${shellKey}`);
  try {
    await page.locator(selector).first().waitFor({ state: "visible", timeout: TIMEOUT });
  } catch (error) {
    const state = await procurementShellState(page).catch(() => ({}));
    throw Object.assign(new Error(`${label}: expected ${shellKey} shell did not become visible`), {
      cause: error,
      details: { url: page.url(), state, selector },
    });
  }
}

async function assertSingleProcurementShell(page, expectedShell, label) {
  await waitForProcurementShell(page, expectedShell, label);
  await page.waitForFunction((shellKey) => {
    function visibleCount(selector) {
      return Array.from(document.querySelectorAll(selector)).filter((node) => {
        const style = window.getComputedStyle(node);
        const rect = node.getBoundingClientRect();
        return style.display !== "none" && style.visibility !== "hidden" && Number(style.opacity || "1") !== 0 && rect.width > 0 && rect.height > 0;
      }).length;
    }
    const counts = {
      overview: visibleCount('.sales-console-shell[data-erpw-workspace="procurement"]'),
      worklist: visibleCount(".erpw-list-shell"),
      report: visibleCount(".erpw-report-shell"),
      poDetail: visibleCount(".erpw-procurement-po-follow-up-shell"),
      supplierDetail: visibleCount(".erpw-procurement-supplier-detail-shell"),
      itemDetail: visibleCount(".erpw-procurement-item-detail-shell"),
      purchaseRequestReview: visibleCount(".erpw-procurement-purchase-request-review-shell"),
      rfqReview: visibleCount(".erpw-procurement-rfq-review-shell"),
      supplierQuotationReview: visibleCount(".erpw-procurement-supplier-quotation-review-shell"),
    };
    const total = counts.overview + counts.worklist + counts.report + counts.poDetail + counts.supplierDetail + counts.itemDetail + counts.purchaseRequestReview + counts.rfqReview + counts.supplierQuotationReview;
    return counts[shellKey] === 1 && total === 1;
  }, expectedShell, { timeout: TIMEOUT });
  const state = await procurementShellState(page);
  assert(state[expectedShell] === 1, `${label}: expected ${expectedShell} shell to be visible once`, state);
  assert(state.total === 1, `${label}: multiple Procurement shells are visible`, state);
  if (expectedShell !== "overview") {
    assert(state.overview === 0, `${label}: old Procurement Overview remains visible on child route`, state);
  }
  return state;
}

async function clickOverviewTarget(page, target) {
  await openDeskRoute(page, "/desk/procurement-console");
  await assertSingleProcurementShell(page, "overview", `${target.label}: before overview card click`);
  const shellSelector = '.sales-console-shell[data-erpw-workspace="procurement"]';
  const selector = target.insightKey
    ? `${shellSelector} [data-insight-key="${target.insightKey}"]`
    : target.sectionKey
      ? `${shellSelector} [data-section-key="${target.sectionKey}"] [data-queue-key="${target.queueKey}"]`
      : `${shellSelector} [data-queue-key="${target.queueKey}"]`;
  const card = page.locator(selector).first();
  await card.waitFor({ state: "visible", timeout: TIMEOUT });
  await dismissFrappeModals(page);
  await card.click({ noWaitAfter: true });
  await page.waitForURL((url) => url.pathname === target.expectedPath, { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  return assertSingleProcurementShell(page, target.expectedShell, `${target.label}: after overview card click`);
}

async function checkProcurementOverviewNavigationLifecycle(page) {
  const targets = [
    { label: "Overdue POs", insightKey: "purchase_orders_overdue", expectedPath: "/desk/procurement-console-worklist/purchase-orders-overdue", expectedShell: "worklist" },
    { label: "Supplier Follow-up", insightKey: "purchase_orders_supplier_follow_up", expectedPath: "/desk/procurement-console-worklist/purchase-orders-supplier-follow-up", expectedShell: "worklist" },
    { label: "Due Soon", insightKey: "purchase_orders_due_soon", expectedPath: "/desk/procurement-console-worklist/purchase-orders-due-soon", expectedShell: "worklist" },
    { label: "Requests To Source", sectionKey: "priority-work", queueKey: "requests_to_source", expectedPath: "/desk/procurement-console-worklist/requests-to-source", expectedShell: "worklist" },
    { label: "Priority Expiring Supplier Quotations", sectionKey: "priority-work", queueKey: "supplier_quotations_expiring", expectedPath: "/desk/procurement-console-worklist/supplier-quotations-expiring", expectedShell: "worklist" },
    { label: "Pipeline Purchase Request", sectionKey: "buying-pipeline", queueKey: "requests_to_source", expectedPath: "/desk/procurement-console-worklist/requests-to-source", expectedShell: "worklist" },
    { label: "Pipeline RFQ", sectionKey: "buying-pipeline", queueKey: "rfqs_awaiting_supplier_response", expectedPath: "/desk/procurement-console-worklist/rfqs-awaiting-supplier-response", expectedShell: "worklist" },
    { label: "Pipeline Supplier Quotation", sectionKey: "buying-pipeline", queueKey: "supplier_quotations_to_compare", expectedPath: "/desk/procurement-console-worklist/supplier-quotations-to-compare", expectedShell: "worklist" },
    { label: "Pipeline Purchase Order", sectionKey: "buying-pipeline", queueKey: "purchase_order_directory", expectedPath: "/desk/procurement-console-worklist/purchase-order-directory", expectedShell: "worklist" },
    { label: "Pipeline Receipt Visibility", sectionKey: "buying-pipeline", queueKey: "purchase_orders_partially_received", expectedPath: "/desk/procurement-console-worklist/purchase-orders-partially-received", expectedShell: "worklist" },
    { label: "Pipeline Billing Visibility", sectionKey: "buying-pipeline", queueKey: "purchase_orders_not_billed_visibility", expectedPath: "/desk/procurement-console-worklist/purchase-orders-not-billed-visibility", expectedShell: "worklist" },
    { label: "Overdue Purchase Orders", sectionKey: "order-follow-up", queueKey: "purchase_orders_overdue", expectedPath: "/desk/procurement-console-worklist/purchase-orders-overdue", expectedShell: "worklist" },
    { label: "Purchase Orders Due Soon", sectionKey: "order-follow-up", queueKey: "purchase_orders_due_soon", expectedPath: "/desk/procurement-console-worklist/purchase-orders-due-soon", expectedShell: "worklist" },
    { label: "Partially Received Purchase Orders", sectionKey: "order-follow-up", queueKey: "purchase_orders_partially_received", expectedPath: "/desk/procurement-console-worklist/purchase-orders-partially-received", expectedShell: "worklist" },
    { label: "Received Not Fully Billed", sectionKey: "order-follow-up", queueKey: "purchase_orders_not_billed_visibility", expectedPath: "/desk/procurement-console-worklist/purchase-orders-not-billed-visibility", expectedShell: "worklist" },
    { label: "RFQs Awaiting Supplier Response", sectionKey: "sourcing", queueKey: "rfqs_awaiting_supplier_response", expectedPath: "/desk/procurement-console-worklist/rfqs-awaiting-supplier-response", expectedShell: "worklist" },
    { label: "Supplier Quotations To Compare", sectionKey: "sourcing", queueKey: "supplier_quotations_to_compare", expectedPath: "/desk/procurement-console-worklist/supplier-quotations-to-compare", expectedShell: "worklist" },
    { label: "Sourcing Expiring Supplier Quotations", sectionKey: "sourcing", queueKey: "supplier_quotations_expiring", expectedPath: "/desk/procurement-console-worklist/supplier-quotations-expiring", expectedShell: "worklist" },
    { label: "Quote Comparison", sectionKey: "sourcing", queueKey: "supplier_quotation_comparison", expectedPath: "/desk/procurement-console-report/supplier-quotation-comparison", expectedShell: "report" },
    { label: "Suppliers", sectionKey: "directories", queueKey: "supplier_directory", expectedPath: "/desk/procurement-console-worklist/supplier-directory", expectedShell: "worklist" },
    { label: "Purchase Requests", sectionKey: "directories", queueKey: "purchase_request_directory", expectedPath: "/desk/procurement-console-worklist/purchase-request-directory", expectedShell: "worklist" },
    { label: "Purchase Orders", sectionKey: "directories", queueKey: "purchase_order_directory", expectedPath: "/desk/procurement-console-worklist/purchase-order-directory", expectedShell: "worklist" },
    { label: "RFQs", sectionKey: "directories", queueKey: "rfq_directory", expectedPath: "/desk/procurement-console-worklist/rfq-directory", expectedShell: "worklist" },
    { label: "Supplier Quotations", sectionKey: "directories", queueKey: "supplier_quotation_directory", expectedPath: "/desk/procurement-console-worklist/supplier-quotation-directory", expectedShell: "worklist" },
    { label: "Buying Items", sectionKey: "directories", queueKey: "buying_item_directory", expectedPath: "/desk/procurement-console-worklist/buying-item-directory", expectedShell: "worklist" },
  ];
  const results = [];
  for (const target of targets) {
    results.push(await clickOverviewTarget(page, target));
  }
  return results;
}


async function checkProcurementBackForwardLifecycle(page) {
  await openDeskRoute(page, "/desk/procurement-console");
  await assertSingleProcurementShell(page, "overview", "Back/forward: overview start");
  await clickOverviewTarget(page, { label: "Back/forward Purchase Orders", sectionKey: "directories", queueKey: "purchase_order_directory", expectedPath: "/desk/procurement-console-worklist/purchase-order-directory", expectedShell: "worklist" });
  await openDeskRoute(page, "/desk/procurement-console");
  await assertSingleProcurementShell(page, "overview", "Back/forward: overview middle");
  await clickOverviewTarget(page, { label: "Back/forward Quote Comparison", sectionKey: "sourcing", queueKey: "supplier_quotation_comparison", expectedPath: "/desk/procurement-console-report/supplier-quotation-comparison", expectedShell: "report" });
  await page.goBack({ waitUntil: "domcontentloaded", timeout: TIMEOUT });
  await page.waitForURL((url) => url.pathname === "/desk/procurement-console", { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  await assertSingleProcurementShell(page, "overview", "Back/forward: after browser back");
  await page.goForward({ waitUntil: "domcontentloaded", timeout: TIMEOUT });
  await page.waitForURL((url) => url.pathname === "/desk/procurement-console-report/supplier-quotation-comparison", { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  await assertSingleProcurementShell(page, "report", "Back/forward: after browser forward");
  for (let index = 0; index < 5; index += 1) {
    await openDeskRoute(page, "/desk/procurement-console");
    await assertSingleProcurementShell(page, "overview", `Repeated navigation ${index + 1}: overview`);
    await clickOverviewTarget(page, { label: `Repeated navigation ${index + 1} Suppliers`, sectionKey: "directories", queueKey: "supplier_directory", expectedPath: "/desk/procurement-console-worklist/supplier-directory", expectedShell: "worklist" });
  }
  return { ok: true };
}

async function checkProcurementSidebar(page) {
  await openDeskRoute(page, "/desk/procurement-console");
  const expected = ["Overview", "Suppliers", "Purchase Requests", "Purchase Orders", "RFQs", "Supplier Quotations", "Buying Items", "Quote Comparison"];
  const sidebarText = page.locator(".erpw-sales-console-sidebar-text");
  await sidebarText.first().waitFor({ state: "visible", timeout: TIMEOUT });
  const labels = (await sidebarText.evaluateAll((nodes) => nodes.map((node) => (node.textContent || "").trim()).filter(Boolean))).slice(0, expected.length);
  assert(expected.every((label, index) => labels[index] === label), "Procurement sidebar labels/order mismatch", { labels, expected });
  const headerSubtitle = await page.locator(".body-sidebar .header-subtitle").first().textContent({ timeout: TIMEOUT }).catch(() => "");
  assert(/Procurement Console/i.test(headerSubtitle || ""), "Procurement sidebar header did not use Procurement Console", { headerSubtitle });

  const routeChecks = [
    { label: "Suppliers", expectedPath: "/desk/procurement-console-worklist/supplier-directory" },
    { label: "Purchase Requests", expectedPath: "/desk/procurement-console-worklist/purchase-request-directory" },
    { label: "Purchase Orders", expectedPath: "/desk/procurement-console-worklist/purchase-order-directory" },
    { label: "RFQs", expectedPath: "/desk/procurement-console-worklist/rfq-directory" },
    { label: "Supplier Quotations", expectedPath: "/desk/procurement-console-worklist/supplier-quotation-directory" },
    { label: "Buying Items", expectedPath: "/desk/procurement-console-worklist/buying-item-directory" },
  ];
  const clickedRoutes = [];
  for (const check of routeChecks) {
    const link = page.locator(".erpw-sales-console-sidebar-link", { hasText: check.label }).first();
    await link.waitFor({ state: "visible", timeout: TIMEOUT });
    await link.click();
    await page.waitForURL((url) => url.pathname === check.expectedPath, { waitUntil: "domcontentloaded", timeout: TIMEOUT });
    assert(!/\/desk\/sales-console-worklist\//.test(new URL(page.url()).pathname), `${check.label}: routed to Sales Console worklist`, { url: page.url() });
    await assertSingleProcurementShell(page, "worklist", `${check.label}: after sidebar click`);
    clickedRoutes.push(page.url());
  }

  const quoteLink = page.locator(".erpw-sales-console-sidebar-link", { hasText: "Quote Comparison" }).first();
  await quoteLink.waitFor({ state: "visible", timeout: TIMEOUT });
  await quoteLink.click();
  await page.waitForURL((url) => url.pathname === "/desk/procurement-console-report/supplier-quotation-comparison", { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  await assertSingleProcurementShell(page, "report", "Quote Comparison: after sidebar click");
  clickedRoutes.push(page.url());

  return { labels, clickedRoutes };
}

function fieldByKey(payload, key) {
  return (((payload && payload.controls) || {}).fields || []).find((field) => field && field.key === key) || null;
}

function assertLinkField(payload, key, doctype, label, placeholder) {
  const field = fieldByKey(payload, key);
  assert(field && field.type === "link" && field.linkDoctype === doctype, `${label}: link filter metadata mismatch`, { key, doctype, field });
  if (placeholder) {
    assert(field.placeholder === placeholder, `${label}: link filter placeholder mismatch`, { key, expected: placeholder, field });
  }
}

function assertTextSearchField(payload, key, label, expectedLabel) {
  const field = fieldByKey(payload, key);
  assert(field && field.type === "text" && field.label === expectedLabel, `${label}: text search filter label mismatch`, { key, expectedLabel, field });
}

function assertNoCompanyField(payload, label) {
  assert(!fieldByKey(payload, "company"), `${label}: company filter should be hidden in single-company context`, payload && payload.controls);
}

function firstRowName(payload) {
  const row = (((payload || {}).results || {}).rows || [])[0] || {};
  return row.name || row.key || "";
}

function queryFromSeed(seed) {
  const value = normalizeText(seed);
  if (!value) return "";
  return value.slice(0, Math.max(2, Math.min(6, value.length)));
}

async function worklistPayload(page, queueKey) {
  const response = await callMethod(page, "erp_workspace_ui.procurement_console.worklist.get_procurement_console_worklist_context", {
    queue_key: queueKey,
  });
  assert(response.ok, `${queueKey}: worklist API failed for autocomplete setup`, response);
  return response.data.message || {};
}

async function fetchLinkSeed(page, doctype, fallbackTxt = "") {
  const response = await callMethod(page, "frappe.desk.search.search_link", {
    doctype,
    txt: fallbackTxt,
    page_length: 1,
  });
  const rows = response.ok && Array.isArray(response.data.message) ? response.data.message : [];
  const row = rows[0];
  if (!row) return "";
  if (typeof row === "string") return row;
  return row.value || row.name || row.label || "";
}

async function exerciseListLinkAutocomplete(page, route, key, doctype, seed, label) {
  const query = queryFromSeed(seed) || queryFromSeed(await fetchLinkSeed(page, doctype, ""));
  if (!query) return { label, skipped: true, reason: `No ${doctype} seed available` };
  await openDeskRoute(page, route);
  await page.locator(".erpw-list-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  const input = page.locator(`[data-erpw-list-field-key="${key}"][data-erpw-list-link-doctype="${doctype}"]`).first();
  await input.waitFor({ state: "visible", timeout: TIMEOUT });
  await input.fill(query);
  const suggestions = page.locator(".erpw-list-link-suggestions:not([hidden])").first();
  await suggestions.waitFor({ state: "visible", timeout: TIMEOUT });
  const option = suggestions.locator("[data-erpw-list-link-option]").first();
  await option.waitFor({ state: "visible", timeout: TIMEOUT });
  await option.click();
  const selected = await input.inputValue();
  assert(selected.length > 0, `${label}: autocomplete did not select a value`, { query, selected });
  return { label, query, selected };
}

async function exerciseReportLinkAutocomplete(page, route, key, doctype, seed, label) {
  const query = queryFromSeed(seed) || queryFromSeed(await fetchLinkSeed(page, doctype, ""));
  if (!query) return { label, skipped: true, reason: `No ${doctype} seed available` };
  await openDeskRoute(page, route);
  await page.locator(".erpw-report-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  const input = page.locator(`[data-erpw-control-key="${key}"][data-erpw-link-doctype="${doctype}"]`).first();
  await input.waitFor({ state: "visible", timeout: TIMEOUT });
  await input.fill(query);
  const suggestions = page.locator(".erpw-report-link-suggestions:not([hidden])").first();
  await suggestions.waitFor({ state: "visible", timeout: TIMEOUT });
  const option = suggestions.locator("[data-erpw-report-link-option]").first();
  await option.waitFor({ state: "visible", timeout: TIMEOUT });
  await option.click();
  const selected = await input.inputValue();
  assert(selected.length > 0, `${label}: report autocomplete did not select a value`, { query, selected });
  return { label, query, selected };
}

async function checkSupplierAutocomplete(page) {
  const supplierPayload = await worklistPayload(page, "supplier_directory");
  const requestPayload = await worklistPayload(page, "purchase_request_directory");
  const orderPayload = await worklistPayload(page, "purchase_order_directory");
  const followUpPayload = await worklistPayload(page, "purchase_orders_overdue");
  const rfqPayload = await worklistPayload(page, "rfq_directory");
  const quotationPayload = await worklistPayload(page, "supplier_quotation_directory");
  const itemPayload = await worklistPayload(page, "buying_item_directory");
  const comparisonResponse = await callMethod(page, "erp_workspace_ui.procurement_console.report.get_procurement_console_report_context", {
    report_key: "supplier_quotation_comparison",
  });
  assert(comparisonResponse.ok, "Quote comparison API failed for autocomplete setup", comparisonResponse);
  const comparisonPayload = comparisonResponse.data.message || {};

  assertLinkField(supplierPayload, "supplier", "Supplier", "Supplier Directory", "Select supplier");
  assertLinkField(supplierPayload, "supplier_group", "Supplier Group", "Supplier Directory", "Select supplier group");
  assertTextSearchField(supplierPayload, "keyword", "Supplier Directory", "Search supplier text");
  assertLinkField(requestPayload, "material_request", "Material Request", "Purchase Requests", "Select purchase request");
  assertTextSearchField(requestPayload, "keyword", "Purchase Requests", "Search request text");
  assertNoCompanyField(requestPayload, "Purchase Requests");
  assertLinkField(orderPayload, "purchase_order", "Purchase Order", "Purchase Orders", "Select purchase order");
  assertLinkField(orderPayload, "supplier", "Supplier", "Purchase Orders", "Select supplier");
  assertTextSearchField(orderPayload, "keyword", "Purchase Orders", "Search order ID or supplier");
  assertNoCompanyField(orderPayload, "Purchase Orders");
  assertLinkField(followUpPayload, "purchase_order", "Purchase Order", "PO Follow-up", "Select purchase order");
  assertLinkField(followUpPayload, "supplier", "Supplier", "PO Follow-up", "Select supplier");
  assertTextSearchField(followUpPayload, "keyword", "PO Follow-up", "Search order ID or supplier");
  assertNoCompanyField(followUpPayload, "PO Follow-up");
  assertLinkField(rfqPayload, "request_for_quotation", "Request for Quotation", "RFQs", "Select RFQ");
  assertTextSearchField(rfqPayload, "keyword", "RFQs", "Search RFQ text");
  assertNoCompanyField(rfqPayload, "RFQs");
  assertLinkField(quotationPayload, "supplier_quotation", "Supplier Quotation", "Supplier Quotations", "Select supplier quotation");
  assertLinkField(quotationPayload, "supplier", "Supplier", "Supplier Quotations", "Select supplier");
  assertTextSearchField(quotationPayload, "keyword", "Supplier Quotations", "Search quotation text");
  assertNoCompanyField(quotationPayload, "Supplier Quotations");
  assertLinkField(itemPayload, "item", "Item", "Buying Items", "Select item");
  assertTextSearchField(itemPayload, "keyword", "Buying Items", "Search item text");
  assertLinkField(itemPayload, "item_group", "Item Group", "Buying Items", "Select item group");
  assertLinkField(comparisonPayload, "item_code", "Item", "Quote Comparison", "Select item");
  assertLinkField(comparisonPayload, "supplier", "Supplier", "Quote Comparison", "Select supplier");
  assertLinkField(comparisonPayload, "supplier_quotation", "Supplier Quotation", "Quote Comparison", "Select supplier quotation");
  assertLinkField(comparisonPayload, "request_for_quotation", "Request for Quotation", "Quote Comparison", "Select RFQ");
  assertNoCompanyField(comparisonPayload, "Quote Comparison");

  const supplierSeed = firstRowName(supplierPayload) || await fetchLinkSeed(page, "Supplier", "S");
  const requestSeed = firstRowName(requestPayload);
  const orderSeed = firstRowName(orderPayload) || firstRowName(followUpPayload);
  const rfqSeed = firstRowName(rfqPayload);
  const quotationSeed = firstRowName(quotationPayload);
  const itemSeed = firstRowName(itemPayload) || await fetchLinkSeed(page, "Item", "A");
  const results = [];
  results.push(await exerciseListLinkAutocomplete(page, "/desk/procurement-console-worklist/purchase-order-directory", "supplier", "Supplier", supplierSeed, "Supplier on Purchase Orders"));
  results.push(await exerciseListLinkAutocomplete(page, "/desk/procurement-console-worklist/purchase-request-directory", "material_request", "Material Request", requestSeed, "Purchase Request"));
  results.push(await exerciseListLinkAutocomplete(page, "/desk/procurement-console-worklist/purchase-orders-overdue", "purchase_order", "Purchase Order", orderSeed, "Purchase Order follow-up"));
  results.push(await exerciseListLinkAutocomplete(page, "/desk/procurement-console-worklist/rfq-directory", "request_for_quotation", "Request for Quotation", rfqSeed, "RFQ"));
  results.push(await exerciseListLinkAutocomplete(page, "/desk/procurement-console-worklist/supplier-quotation-directory", "supplier_quotation", "Supplier Quotation", quotationSeed, "Supplier Quotation"));
  results.push(await exerciseListLinkAutocomplete(page, "/desk/procurement-console-worklist/buying-item-directory", "item", "Item", itemSeed, "Buying Item"));
  results.push(await exerciseReportLinkAutocomplete(page, "/desk/procurement-console-report/supplier-quotation-comparison", "item_code", "Item", itemSeed, "Quote Comparison Item"));

  await openDeskRoute(page, "/desk/procurement-console-worklist/purchase-order-directory");
  await page.locator(".erpw-list-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  const urlBefore = page.url();
  await page.evaluate(() => { window.__erpwProcurementSmokeMarker = String(Date.now()); });
  await page.locator('[data-erpw-list-action-key="apply_filters"]').first().click();
  await page.waitForFunction(() => document.querySelector(".erpw-list-shell") && document.querySelector(".erpw-list-shell").getAttribute("aria-busy") !== "true", null, { timeout: TIMEOUT });
  assert(await page.evaluate(() => Boolean(window.__erpwProcurementSmokeMarker)), "Apply reloaded the full page unexpectedly");
  assert(page.url() === urlBefore, "Apply changed route unexpectedly", { before: urlBefore, after: page.url() });
  await page.locator('[data-erpw-list-action-key="reset_filters"]').first().click();
  await page.waitForFunction(() => document.querySelector(".erpw-list-shell") && document.querySelector(".erpw-list-shell").getAttribute("aria-busy") !== "true", null, { timeout: TIMEOUT });
  assert(await page.evaluate(() => Boolean(window.__erpwProcurementSmokeMarker)), "Reset reloaded the full page unexpectedly");
  await page.locator('[data-erpw-list-action-key="refresh"]').first().click();
  await page.waitForFunction(() => document.querySelector(".erpw-list-shell") && document.querySelector(".erpw-list-shell").getAttribute("aria-busy") !== "true", null, { timeout: TIMEOUT });
  assert(await page.evaluate(() => Boolean(window.__erpwProcurementSmokeMarker)), "Refresh reloaded the full page unexpectedly");
  return { results };
}

async function assertDatePairSameRow(page, route, label) {
  await openDeskRoute(page, route);
  await page.locator(".erpw-list-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  const pair = await page.evaluate(() => {
    const start = document.querySelector('[data-erpw-list-field-shell-key="date_start"]');
    const end = document.querySelector('[data-erpw-list-field-shell-key="date_end"]');
    const startRect = start ? start.getBoundingClientRect() : null;
    const endRect = end ? end.getBoundingClientRect() : null;
    return {
      hasStart: !!start,
      hasEnd: !!end,
      startTop: startRect ? Math.round(startRect.top) : null,
      endTop: endRect ? Math.round(endRect.top) : null,
      startLeft: startRect ? Math.round(startRect.left) : null,
      endLeft: endRect ? Math.round(endRect.left) : null,
      viewportWidth: window.innerWidth,
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    };
  });
  assert(pair.hasStart && pair.hasEnd, `${label}: date-window controls are missing`, pair);
  assert(Math.abs(pair.startTop - pair.endTop) <= 4, `${label}: Date From and Date To are not aligned in the same row`, pair);
  assert(pair.endLeft > pair.startLeft, `${label}: Date To is not positioned after Date From`, pair);
  assert(pair.overflow <= 1, `${label}: date-pair layout introduced horizontal overflow`, pair);
  return { label, route, pair };
}

async function checkDatePairLayout(page) {
  return [
    await assertDatePairSameRow(page, "/desk/procurement-console-worklist/purchase-request-directory", "Purchase Request Directory"),
    await assertDatePairSameRow(page, "/desk/procurement-console-worklist/purchase-orders-overdue", "Overdue Purchase Orders"),
  ];
}

async function assertEnterpriseListFilterLayout(page, route, label) {
  await openDeskRoute(page, route);
  await page.locator(".erpw-list-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  const layout = await page.evaluate(() => {
    const visible = (node) => {
      if (!node) return false;
      const style = window.getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
    };
    const shell = document.querySelector(".erpw-list-shell");
    const deck = shell && shell.querySelector(".erpw-list-filter-deck");
    const main = deck && deck.querySelector(".erpw-list-filter-main-row");
    const dateGroup = deck && deck.querySelector(".erpw-list-date-window-group");
    const actionCell = deck && deck.querySelector(".erpw-list-command-action-cell");
    const actionToolbar = actionCell && actionCell.querySelector(".erpw-list-toolbar-actions");
    const summary = shell && shell.querySelector(".erpw-list-summary-card");
    const facts = summary && summary.querySelector(".erpw-list-summary-facts");
    const factItems = facts ? Array.from(facts.querySelectorAll(".erpw-list-summary-fact")) : [];
    const summaryMetrics = summary && summary.querySelector(".erpw-list-summary-metrics");
    const detachedMetricCount = shell
      ? Array.from(shell.children).filter((child) => child.classList && child.classList.contains("erpw-list-metrics") && !child.classList.contains("erpw-list-summary-metrics")).length
      : 0;
    const field = (key) => deck && deck.querySelector(`[data-erpw-list-field-shell-key="${key}"]`);
    const firstIdentity = deck && deck.querySelector('[data-erpw-list-field-role="identity"]');
    const search = field("keyword") || (deck && deck.querySelector('[data-erpw-list-field-role="search"]'));
    const start = field("date_start");
    const end = field("date_end");
    const firstIdentityInput = firstIdentity && firstIdentity.querySelector('[data-erpw-list-field-key]');
    const searchInput = search && search.querySelector('[data-erpw-list-field-key]');
    const startInput = start && start.querySelector('[data-erpw-list-field-key]');
    const endInput = end && end.querySelector('[data-erpw-list-field-key]');
    const rect = (node) => {
      if (!node) return null;
      const box = node.getBoundingClientRect();
      return { top: Math.round(box.top), left: Math.round(box.left), right: Math.round(box.right), bottom: Math.round(box.bottom), width: Math.round(box.width), height: Math.round(box.height) };
    };
    const controlFields = deck
      ? Array.from(deck.querySelectorAll("[data-erpw-list-field-role]"))
          .filter(visible)
          .map((node) => Object.assign(rect(node), {
            key: node.getAttribute("data-erpw-list-field-shell-key") || "",
            role: node.getAttribute("data-erpw-list-field-role") || "",
            row: node.closest(".erpw-list-filter-secondary-row") ? "secondary" : "main",
          }))
      : [];
    return {
      hasDeck: visible(deck),
      hasMain: visible(main),
      hasDateGroup: visible(dateGroup),
      hasActions: visible(actionCell),
      filter: rect(shell && shell.querySelector(".erpw-list-controls-strip")),
      deck: rect(deck),
      main: rect(main),
      firstIdentity: rect(firstIdentity),
      firstIdentityInput: rect(firstIdentityInput),
      search: rect(search),
      searchInput: rect(searchInput),
      actionCell: rect(actionCell),
      actionToolbar: rect(actionToolbar),
      start: rect(start),
      startInput: rect(startInput),
      end: rect(end),
      endInput: rect(endInput),
      facts: rect(facts),
      factCount: factItems.length,
      factText: facts ? String(facts.textContent || "").replace(/\s+/g, " ").trim() : "",
      hasSummaryMetricCards: !!summaryMetrics,
      detachedMetricCount,
      controlFields,
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    };
  });
  assert(layout.hasDeck && layout.hasMain, `${label}: shared filter deck is not rendered`, layout);
  assert(layout.filter && layout.filter.height <= 210, `${label}: filter deck is too tall for enterprise worklist layout`, layout);
  if (layout.firstIdentity && layout.search) {
    assert(Math.abs(layout.firstIdentity.top - layout.search.top) <= 4, `${label}: primary record link and keyword search should share the main row`, layout);
  }
  if (layout.start && layout.end) {
    assert(layout.hasDateGroup, `${label}: date fields should render inside the shared date-window group`, layout);
    assert(Math.abs(layout.start.top - layout.end.top) <= 4, `${label}: date fields are not paired`, layout);
    assert(layout.end.left > layout.start.left, `${label}: Date To should appear after Date From`, layout);
  }
  if (layout.actionToolbar && layout.startInput && layout.endInput) {
    const dateInputCenter = (Math.min(layout.startInput.top, layout.endInput.top) + Math.max(layout.startInput.bottom, layout.endInput.bottom)) / 2;
    const actionCenter = (layout.actionToolbar.top + layout.actionToolbar.bottom) / 2;
    assert(Math.abs(actionCenter - dateInputCenter) <= 8, `${label}: filter action buttons should align to the center of the date-window inputs`, layout);
  } else if (layout.actionToolbar && layout.main) {
    const visibleFields = [layout.firstIdentityInput, layout.searchInput].filter(Boolean);
    const fieldCenter = visibleFields.length
      ? (Math.min(...visibleFields.map((field) => field.top)) + Math.max(...visibleFields.map((field) => field.bottom))) / 2
      : (layout.main.top + layout.main.bottom) / 2;
    const actionCenter = (layout.actionToolbar.top + layout.actionToolbar.bottom) / 2;
    assert(Math.abs(actionCenter - fieldCenter) <= 8, `${label}: filter action buttons should align to the center of the active filter inputs`, layout);
  }
  const fixedFields = (layout.controlFields || []).filter((field) => field && field.role !== "search");
  const searchFields = (layout.controlFields || []).filter((field) => field && field.role === "search");
  if (fixedFields.length >= 2) {
    const fixedWidths = fixedFields.map((field) => field.width);
    const fixedWidthSpread = Math.max(...fixedWidths) - Math.min(...fixedWidths);
    assert(fixedWidthSpread <= 12, `${label}: non-search filter controls should use one shared fixed width`, { layout, fixedFields, fixedWidthSpread });
  }
  if (fixedFields.length && searchFields.length) {
    const widestFixed = Math.max(...fixedFields.map((field) => field.width));
    searchFields.forEach((field) => {
      assert(field.width >= widestFixed - 8, `${label}: keyword search should receive remaining width without becoming narrower than fixed filters`, { layout, field, widestFixed });
    });
  }
  assert(layout.detachedMetricCount === 0, `${label}: detached one-card metric summaries should not render below filters`, layout);
  assert(layout.facts && layout.factCount >= 1, `${label}: header metrics should render as flat inline facts`, layout);
  assert(!layout.hasSummaryMetricCards, `${label}: header metrics should not render as nested metric cards`, layout);
  assert(/in view/i.test(layout.factText), `${label}: header facts should include the visible record count`, layout);
  assert(layout.overflow <= 1, `${label}: enterprise filter layout introduced horizontal overflow`, layout);
  return { label, route, layout };
}

async function assertEnterpriseReportFilterLayout(page, route, label) {
  await openDeskRoute(page, route);
  await page.locator(".erpw-report-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  const layout = await page.evaluate(() => {
    const visible = (node) => {
      if (!node) return false;
      const style = window.getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
    };
    const rect = (node) => {
      if (!node) return null;
      const box = node.getBoundingClientRect();
      return { top: Math.round(box.top), left: Math.round(box.left), right: Math.round(box.right), bottom: Math.round(box.bottom), width: Math.round(box.width), height: Math.round(box.height) };
    };
    const shell = document.querySelector(".erpw-report-shell");
    const summary = shell && shell.querySelector(".erpw-report-summary");
    const controls = shell && shell.querySelector(".erpw-report-controls");
    const actionCell = controls && controls.querySelector(".erpw-report-command-actions");
    const rows = controls ? Array.from(controls.querySelectorAll(".erpw-report-command-row")).filter(visible) : [];
    const lastRow = rows.length ? rows[rows.length - 1] : null;
    const title = summary ? String(summary.textContent || "").replace(/\s+/g, " ").trim() : "";
    const fieldRect = (key) => {
      const input = controls && controls.querySelector(`[data-erpw-control-key="${key}"]`);
      const field = input && input.closest(".erpw-report-control-field");
      const box = rect(field);
      return box ? Object.assign(box, { key }) : null;
    };
    const firstRowFields = ["from_date", "to_date", "categorize_by", "include_expired"].map(fieldRect);
    const secondRowFields = ["item_code", "supplier", "supplier_quotation", "request_for_quotation"].map(fieldRect);
    return {
      hasProcurementMode: !!(shell && shell.classList.contains("is-procurement-report")),
      summary: rect(summary),
      controls: rect(controls),
      actionCell: rect(actionCell),
      lastRow: rect(lastRow),
      hasActionsOnlyRow: !!(actionCell && actionCell.closest(".erpw-report-command-row.actions-only")),
      actionLabels: actionCell ? Array.from(actionCell.querySelectorAll("button")).map((button) => String(button.textContent || "").replace(/\s+/g, " ").trim()) : [],
      firstRowFields,
      secondRowFields,
      title,
      rowCount: rows.length,
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    };
  });
  assert(layout.hasProcurementMode, `${label}: report shell did not opt into Procurement enterprise mode`, layout);
  assert(layout.summary && layout.summary.height <= 120, `${label}: report header is too tall`, layout);
  assert(layout.controls && layout.controls.height <= 320, `${label}: report filter panel is too tall`, layout);
  assert(layout.rowCount >= 3, `${label}: report filters should use two field rows plus a command row`, layout);
  assert(layout.hasActionsOnlyRow, `${label}: report actions should sit in a separate command row`, layout);
  assert(!layout.actionLabels.some((labelText) => /Back to Procurement Console/i.test(labelText)), `${label}: report should not carry a one-off Back to Procurement Console action`, layout);
  assert(layout.firstRowFields.every(Boolean), `${label}: first report filter row is missing a required field`, layout);
  assert(layout.secondRowFields.every(Boolean), `${label}: second report filter row is missing a required field`, layout);
  const firstTop = layout.firstRowFields[0].top;
  const secondTop = layout.secondRowFields[0].top;
  layout.firstRowFields.forEach((field) => {
    assert(Math.abs(field.top - firstTop) <= 4, `${label}: first-row report filters are not aligned`, layout);
    assert(Math.abs(field.width - layout.firstRowFields[0].width) <= 8, `${label}: first-row report filter widths are inconsistent`, layout);
  });
  layout.secondRowFields.forEach((field) => {
    assert(Math.abs(field.top - secondTop) <= 4, `${label}: second-row report filters are not aligned`, layout);
    assert(Math.abs(field.width - layout.secondRowFields[0].width) <= 8, `${label}: second-row report filter widths are inconsistent`, layout);
  });
  assert(layout.actionCell && layout.actionCell.top > Math.max(...layout.secondRowFields.map((field) => field.bottom)), `${label}: report actions should appear after filter rows`, layout);
  assert(/Quote Comparison/i.test(layout.title), `${label}: report header should use business-facing page title`, layout);
  assert(!/native report|mutation tools/i.test(layout.title), `${label}: report copy exposes implementation language`, layout);
  assert(layout.overflow <= 1, `${label}: report filter layout introduced horizontal overflow`, layout);
  return { label, route, layout };
}

async function checkEnterpriseListFilterLayouts(page) {
  const worklists = [
    ["/desk/procurement-console-worklist/supplier-directory", "Supplier Directory"],
    ["/desk/procurement-console-worklist/purchase-request-directory", "Purchase Request Directory"],
    ["/desk/procurement-console-worklist/requests-to-source", "Requests To Source"],
    ["/desk/procurement-console-worklist/purchase-order-directory", "Purchase Order Directory"],
    ["/desk/procurement-console-worklist/purchase-orders-open", "Open Purchase Orders"],
    ["/desk/procurement-console-worklist/purchase-orders-due-soon", "Purchase Orders Due Soon"],
    ["/desk/procurement-console-worklist/purchase-orders-overdue", "Overdue Purchase Orders"],
    ["/desk/procurement-console-worklist/purchase-orders-partially-received", "Partially Received Purchase Orders"],
    ["/desk/procurement-console-worklist/purchase-orders-not-billed-visibility", "Received Not Fully Billed"],
    ["/desk/procurement-console-worklist/purchase-orders-supplier-follow-up", "Supplier Follow-up"],
    ["/desk/procurement-console-worklist/rfq-directory", "RFQ Directory"],
    ["/desk/procurement-console-worklist/rfqs-awaiting-supplier-response", "RFQs Awaiting Supplier Response"],
    ["/desk/procurement-console-worklist/supplier-quotation-directory", "Supplier Quotation Directory"],
    ["/desk/procurement-console-worklist/supplier-quotations-to-compare", "Supplier Quotations To Compare"],
    ["/desk/procurement-console-worklist/supplier-quotations-expiring", "Expiring Supplier Quotations"],
    ["/desk/procurement-console-worklist/buying-item-directory", "Buying Item Directory"],
  ];
  const results = [];
  for (const [route, label] of worklists) {
    results.push(await assertEnterpriseListFilterLayout(page, route, label));
  }
  results.push(await assertEnterpriseReportFilterLayout(page, "/desk/procurement-console-report/supplier-quotation-comparison", "Quote Comparison"));
  return results;
}

async function exerciseFocusStability(page, scenario) {
  await openDeskRoute(page, scenario.route);
  await page.locator(scenario.shell).first().waitFor({ state: "visible", timeout: TIMEOUT });
  const input = page.locator(scenario.selector).first();
  await input.waitFor({ state: "visible", timeout: TIMEOUT });
  await captureSmokeScreenshot(page, `${scenario.key}-before-focus`);
  const before = await measureProcurementLayout(page);
  await input.focus();
  await page.waitForTimeout(350);
  await captureSmokeScreenshot(page, `${scenario.key}-after-focus`);
  const focused = await measureProcurementLayout(page);
  await input.fill(scenario.query);
  await page.waitForTimeout(900);
  await captureSmokeScreenshot(page, `${scenario.key}-after-typing`);
  const typed = await measureProcurementLayout(page);
  if (scenario.suggestionSelector) {
    await page.locator(scenario.suggestionSelector).first().waitFor({ state: "visible", timeout: TIMEOUT });
  }
  await input.blur();
  await page.waitForTimeout(350);
  await captureSmokeScreenshot(page, `${scenario.key}-after-blur`);
  const blurred = await measureProcurementLayout(page);
  const maxDelta = maxLayoutDelta(before, [focused, typed, blurred]);
  assert(maxDelta <= 2, `${scenario.label}: filter focus caused layout width shift`, { scenario, before, focused, typed, blurred, maxDelta });
  return { label: scenario.label, before, focused, typed, blurred, maxDelta };
}

async function checkFocusStability(page) {
  const scenarios = [
    { key: "supplier-link", label: "Supplier Link", route: "/desk/procurement-console-worklist/supplier-directory", shell: ".erpw-list-shell", selector: '[data-erpw-list-field-key="supplier"]', query: "Golden", suggestionSelector: ".erpw-list-link-suggestions:not([hidden])" },
    { key: "po-supplier-link", label: "PO Supplier Link", route: "/desk/procurement-console-worklist/purchase-order-directory", shell: ".erpw-list-shell", selector: '[data-erpw-list-field-key="supplier"]', query: "Myanmar", suggestionSelector: ".erpw-list-link-suggestions:not([hidden])" },
    { key: "item-link", label: "Item Link", route: "/desk/procurement-console-worklist/buying-item-directory", shell: ".erpw-list-shell", selector: '[data-erpw-list-field-key="item"]', query: "Samsung", suggestionSelector: ".erpw-list-link-suggestions:not([hidden])" },
    { key: "item-group-link", label: "Item Group Link", route: "/desk/procurement-console-worklist/buying-item-directory", shell: ".erpw-list-shell", selector: '[data-erpw-list-field-key="item_group"]', query: "Phone", suggestionSelector: ".erpw-list-link-suggestions:not([hidden])" },
    { key: "quote-supplier-link", label: "Quote Comparison Supplier Link", route: "/desk/procurement-console-report/supplier-quotation-comparison", shell: ".erpw-report-shell", selector: '[data-erpw-control-key="supplier"]', query: "Golden", suggestionSelector: ".erpw-report-link-suggestions:not([hidden])" },
  ];
  const viewports = [
    { key: "desktop", width: 1366, height: 900 },
    { key: "mobile", width: 390, height: 820 },
  ];
  const results = [];
  for (const viewport of viewports) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    for (const scenario of scenarios) {
      results.push(Object.assign({ viewport: viewport.key }, await exerciseFocusStability(page, Object.assign({}, scenario, { key: `${viewport.key}-${scenario.key}` }))));
    }
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  return results;
}

async function checkTopChrome(page) {
  const pages = [
    { route: "/desk/procurement-console-worklist/supplier-directory", shell: ".erpw-list-shell", title: "Suppliers" },
    { route: "/desk/procurement-console-worklist/purchase-order-directory", shell: ".erpw-list-shell", title: "Purchase Orders" },
    { route: "/desk/procurement-console-worklist/purchase-orders-overdue", shell: ".erpw-list-shell", title: "Overdue Purchase Orders" },
    { route: "/desk/procurement-console-worklist/buying-item-directory", shell: ".erpw-list-shell", title: "Buying Items" },
    { route: "/desk/procurement-console-worklist/supplier-quotation-directory", shell: ".erpw-list-shell", title: "Supplier Quotations" },
    { route: "/desk/procurement-console-report/supplier-quotation-comparison", shell: ".erpw-report-shell", title: "Quote Comparison" },
  ];
  const results = [];
  for (const item of pages) {
    await openDeskRoute(page, item.route);
    await page.locator(item.shell).first().waitFor({ state: "visible", timeout: TIMEOUT });
    const snapshot = await procurementChromeSnapshot(page, item.title);
    const headerText = normalizeText((snapshot.pageHeads || []).map((row) => row.text).join(" ") + " " + (snapshot.breadcrumbRows || []).map((row) => row.text).join(" "));
    assert(headerText.includes("Procurement Console") && headerText.includes(item.title), `${item.title}: top chrome did not show workspace and page context`, { headerText, snapshot });
    assert(!/Procurement Console Worklist|Procurement Console Report/i.test(headerText), `${item.title}: top chrome still exposes generic route title`, { headerText, snapshot });
    assert(snapshot.pageHeadCount <= 1, `${item.title}: duplicate Procurement page-head rows are visible`, snapshot);
    assert(snapshot.managedChromeHeadCount >= 1, `${item.title}: Procurement page head was not marked as managed chrome`, snapshot);
    assert(snapshot.visiblePageHeadIconCount === 0, `${item.title}: Procurement top chrome still shows orphan route icon`, snapshot);
    assert(snapshot.visibleManagedChromeIconCount === 0, `${item.title}: managed Procurement chrome still shows orphan route icon`, snapshot);
    const parent = page.locator('[data-erpw-procurement-home="1"]').first();
    await parent.waitFor({ state: "visible", timeout: TIMEOUT });
    await parent.click();
    await page.waitForURL(/\/desk\/procurement-console(?:[/?#]|$)/, { waitUntil: "domcontentloaded", timeout: TIMEOUT });
    await assertSingleProcurementShell(page, "overview", `${item.title}: parent breadcrumb to overview`);
    results.push({ title: item.title, headerText });
  }
  return results;
}

async function checkQuoteComparisonFromSidebar(page) {
  await openDeskRoute(page, "/desk/procurement-console");
  const quoteLink = page.locator(".erpw-sales-console-sidebar-link", { hasText: "Quote Comparison" }).first();
  await quoteLink.waitFor({ state: "visible", timeout: TIMEOUT });
  await quoteLink.click();
  await page.waitForURL(/\/desk\/procurement-console-report\/supplier-quotation-comparison(?:[/?#]|$)/, { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  await page.locator(".erpw-report-shell, .erpw-report-results, .erpw-report-summary").first().waitFor({ state: "visible", timeout: TIMEOUT });
  await assertSingleProcurementShell(page, "report", "Quote Comparison direct route");
  return page.url();
}

async function checkDetail(page, purchaseOrderName, options = {}) {
  const route = purchaseOrderName
    ? `/desk/procurement-console-po-follow-up/${encodeURIComponent(purchaseOrderName)}`
    : "/desk/procurement-console-po-follow-up";
  await openDeskRoute(page, route);
  await page.locator(".erpw-procurement-po-follow-up-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  await assertSingleProcurementShell(page, "poDetail", "PO Follow-up Detail direct route");
  const text = normalizeText(await page.locator(".erpw-procurement-po-follow-up-shell").first().innerText({ timeout: TIMEOUT }));
  assert(!/Detail runtime unavailable/i.test(text), "Detail page fell back to missing runtime state", { text, route });
  assert(/Purchase Order|follow-up|required|Item lines|unavailable/i.test(text), "Detail page did not render expected read-only shell", { text });
  if (options.requireReadyShell) {
    assert(/Item lines/i.test(text), "Direct PO detail route did not render item line section", { text, route });
    assert(/Receipt posture/i.test(text) && /Billing posture/i.test(text), "Direct PO detail route did not render downstream posture", { text, route });
  }
  const actionStyles = await checkDetailActionStyling(page, ".erpw-procurement-po-follow-up-shell", "PO Follow-up Detail");
  const compactHeader = await checkCompactDetailHeader(page, ".erpw-procurement-po-follow-up-shell", "PO Follow-up Detail");
  const detailResponse = await callMethod(page, "erp_workspace_ui.procurement_console.purchase_order_detail.get_purchase_order_follow_up_detail_context", {
    purchase_order: purchaseOrderName || "",
  });
  assert(detailResponse.ok, "Detail API failed", detailResponse);
  const payload = detailResponse.data.message || {};
  assert(["ready", "restricted", "unavailable", "empty"].includes((payload.detail && payload.detail.state && payload.detail.state.kind) || "missing"), "Detail API invalid state", payload);
  assertNoForbiddenActions(payload, "po_follow_up_detail");
  let toolbarExercise = null;
  if (options.exerciseToolbar) {
    await exerciseDetailRefresh(page, ".erpw-procurement-po-follow-up-shell", "poDetail", "PO Follow-up Detail");
    await exerciseDetailBack(page, ".erpw-procurement-po-follow-up-shell", "/desk/procurement-console-worklist/purchase-orders-supplier-follow-up", "worklist", "PO Follow-up Detail");
    toolbarExercise = { refresh: true, back: true };
  }
  return { route, state: payload.detail && payload.detail.state ? payload.detail.state.kind : "missing", actionStyles, compactHeader, toolbarExercise };
}

async function checkSupplierDetail(page, user) {
  const directoryResponse = await callMethod(page, "erp_workspace_ui.procurement_console.worklist.get_procurement_console_worklist_context", {
    queue_key: "supplier_directory",
  });
  assert(directoryResponse.ok, "Supplier Directory API failed", directoryResponse);
  const directoryPayload = directoryResponse.data.message || {};
  assertNoForbiddenActions(directoryPayload, "supplier_directory");
  const firstSupplier = ((directoryPayload.results || {}).rows || [])[0] || {};
  const supplierName = firstSupplier.name || firstSupplier.key;
  const supplierTarget = ((directoryPayload.action_targets || {})[`row:${firstSupplier.key}:open_record`]) || {};
  assert(supplierTarget.kind === "page" && supplierTarget.route === "procurement-console-supplier", "Supplier Directory must route to productized Supplier Detail", { supplierTarget });
  if (!supplierName) return { state: stateKind(directoryPayload), skipped: "no visible supplier" };

  await openDeskRoute(page, `/desk/procurement-console-supplier/${encodeURIComponent(supplierName)}`);
  await page.locator(".erpw-procurement-supplier-detail-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  await assertSingleProcurementShell(page, "supplierDetail", "Supplier Detail direct route");
  const text = normalizeText(await page.locator(".erpw-procurement-supplier-detail-shell").first().innerText({ timeout: TIMEOUT }));
  assert(/Supplier buying profile|Supplier Detail/i.test(text), "Supplier Detail shell did not render supplier summary", { text });
  assert(/Open or overdue purchase orders/i.test(text), "Supplier Detail did not render PO posture", { text });
  assert(/RFQs/i.test(text) && /Supplier quotations/i.test(text), "Supplier Detail did not render sourcing context", { text });
  assert(!/Detail runtime unavailable/i.test(text), "Supplier Detail fell back to missing runtime state", { text });
  const actionStyles = await checkDetailActionStyling(page, ".erpw-procurement-supplier-detail-shell", "Supplier Detail");
  const compactHeader = await checkCompactDetailHeader(page, ".erpw-procurement-supplier-detail-shell", "Supplier Detail");

  const detailResponse = await callMethod(page, "erp_workspace_ui.procurement_console.supplier_detail.get_supplier_detail_context", {
    supplier: supplierName,
  });
  assert(detailResponse.ok, "Supplier Detail API failed", detailResponse);
  const payload = detailResponse.data.message || {};
  const state = payload.detail && payload.detail.state ? payload.detail.state.kind : "missing";
  assert(["ready", "restricted", "unavailable", "empty"].includes(state), "Supplier Detail API invalid state", payload);
  assertNoForbiddenActions(payload, "supplier_detail");
  const supplierPurchaseRows = [
    ...((((payload.detail || {}).open_purchase_orders || {}).rows) || []),
    ...((((payload.detail || {}).recent_purchase_orders || {}).rows) || []),
  ];
  let purchaseOrderNavigation = { skipped: "no visible supplier purchase orders" };
  if (supplierPurchaseRows.length) {
    const firstPurchaseOrder = supplierPurchaseRows[0];
    const purchaseOrderCell = ((firstPurchaseOrder.cells || {}).purchase_order || {});
    const purchaseOrderName = purchaseOrderCell.value || firstPurchaseOrder.key || "";
    assert(purchaseOrderCell.route === "procurement-console-po-follow-up", "Supplier Detail purchase order cell must use Procurement PO Follow-up route", { purchaseOrderCell });
    const poButton = page.locator('.erpw-procurement-supplier-detail-shell [data-erpw-procurement-detail-route="procurement-console-po-follow-up"]').first();
    await poButton.waitFor({ state: "visible", timeout: TIMEOUT });
    const poButtonClass = await poButton.getAttribute("class");
    assert(!/erpw-procurement-table-link/.test(poButtonClass || ""), "Supplier Detail PO link still uses Procurement-specific pill styling", { poButtonClass });
    const poIconText = normalizeText(await poButton.locator(".erpw-list-inline-open-icon").first().innerText({ timeout: TIMEOUT }));
    assert(poIconText && poIconText !== "?", "Supplier Detail PO link must use shared row-action arrow affordance", { poIconText });
    await poButton.click();
    await page.waitForURL((url) => url.pathname === `/desk/procurement-console-po-follow-up/${encodeURIComponent(purchaseOrderName)}`, { waitUntil: "domcontentloaded", timeout: TIMEOUT });
    await assertSingleProcurementShell(page, "poDetail", "Supplier Detail purchase order navigation");
    const poText = normalizeText(await page.locator(".erpw-procurement-po-follow-up-shell").first().innerText({ timeout: TIMEOUT }));
    assert(poText.includes(purchaseOrderName), "Supplier Detail PO navigation did not load the selected Procurement PO detail", { purchaseOrderName, poText });
    assert(!/Supplier Detail|Supplier buying profile/i.test(poText), "PO Detail retained stale Supplier Detail context after supplier row navigation", { purchaseOrderName, poText });
    await page.goBack({ waitUntil: "domcontentloaded", timeout: TIMEOUT });
    await assertSingleProcurementShell(page, "supplierDetail", "Supplier Detail after browser back from PO detail");
    purchaseOrderNavigation = { purchaseOrderName };
  }
  const hasNativeFormAction = Boolean((payload.action_targets || {}).open_supplier_form);
  if (user.key !== "manager") {
    assert(!hasNativeFormAction, "Non-manager user should not see governed native Supplier form action", payload.action_targets || {});
  }
  await exerciseDetailRefresh(page, ".erpw-procurement-supplier-detail-shell", "supplierDetail", "Supplier Detail");
  await exerciseDetailBack(page, ".erpw-procurement-supplier-detail-shell", "/desk/procurement-console-worklist/supplier-directory", "worklist", "Supplier Detail");
  return { supplierName, state, hasNativeFormAction, actionStyles, compactHeader, purchaseOrderNavigation, toolbarExercise: { refresh: true, back: true } };
}

async function checkItemDetail(page, user) {
  const directoryResponse = await callMethod(page, "erp_workspace_ui.procurement_console.worklist.get_procurement_console_worklist_context", {
    queue_key: "buying_item_directory",
  });
  assert(directoryResponse.ok, "Buying Items API failed", directoryResponse);
  const directoryPayload = directoryResponse.data.message || {};
  assertNoForbiddenActions(directoryPayload, "buying_item_directory");
  const firstItem = ((directoryPayload.results || {}).rows || [])[0] || {};
  const itemCode = firstItem.name || firstItem.key;
  const itemTarget = ((directoryPayload.action_targets || {})[`row:${firstItem.key}:open_record`]) || {};
  assert(itemTarget.kind === "page" && itemTarget.route === "procurement-console-item", "Buying Items must route to productized Item Detail", { itemTarget });
  if (!itemCode) return { state: stateKind(directoryPayload), skipped: "no visible item" };

  await openDeskRoute(page, `/desk/procurement-console-item/${encodeURIComponent(itemCode)}`);
  await page.locator(".erpw-procurement-item-detail-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  await assertSingleProcurementShell(page, "itemDetail", "Buying Item Detail direct route");
  const text = normalizeText(await page.locator(".erpw-procurement-item-detail-shell").first().innerText({ timeout: TIMEOUT }));
  assert(/Buying item profile|Buying Item Detail/i.test(text), "Item Detail shell did not render item summary", { text });
  assert(/Approved suppliers|Supplier price review/i.test(text), "Item Detail did not render supplier or price context", { text });
  assert(/Recent supplier quotations|Open purchase orders/i.test(text), "Item Detail did not render buying movement context", { text });
  assert(!/Detail runtime unavailable/i.test(text), "Item Detail fell back to missing runtime state", { text });
  const actionStyles = await checkDetailActionStyling(page, ".erpw-procurement-item-detail-shell", "Item Detail");
  const compactHeader = await checkCompactDetailHeader(page, ".erpw-procurement-item-detail-shell", "Item Detail");

  const detailResponse = await callMethod(page, "erp_workspace_ui.procurement_console.items.get_item_detail_context", {
    item: itemCode,
  });
  assert(detailResponse.ok, "Item Detail API failed", detailResponse);
  const payload = detailResponse.data.message || {};
  const state = payload.detail && payload.detail.state ? payload.detail.state.kind : "missing";
  assert(["ready", "restricted", "unavailable", "empty"].includes(state), "Item Detail API invalid state", payload);
  assertNoForbiddenActions(payload, "buying_item_detail");
  const hasNativeFormAction = Boolean((payload.action_targets || {}).open_item_form);
  if (user.key !== "manager") {
    assert(!hasNativeFormAction, "Non-manager user should not see governed native Item form action", payload.action_targets || {});
  }
  const purchaseRows = (((payload.detail || {}).purchase_orders || {}).rows || []);
  let purchaseOrderNavigation = { skipped: "no visible open purchase orders" };
  if (purchaseRows.length) {
    const firstPurchaseOrder = purchaseRows[0];
    const purchaseOrderCell = ((firstPurchaseOrder.cells || {}).purchase_order || {});
    const purchaseOrderName = purchaseOrderCell.value || firstPurchaseOrder.key || "";
    assert(purchaseOrderCell.route === "procurement-console-po-follow-up", "Item Detail purchase order cell must use Procurement PO Follow-up route", { purchaseOrderCell });
    const poButton = page.locator('.erpw-procurement-item-detail-shell [data-erpw-procurement-detail-route="procurement-console-po-follow-up"]').first();
    await poButton.waitFor({ state: "visible", timeout: TIMEOUT });
    const poButtonClass = await poButton.getAttribute("class");
    assert(!/erpw-procurement-table-link/.test(poButtonClass || ""), "Item Detail PO link still uses Procurement-specific pill styling", { poButtonClass });
    const poIconText = normalizeText(await poButton.locator(".erpw-list-inline-open-icon").first().innerText({ timeout: TIMEOUT }));
    assert(poIconText && poIconText !== "?", "Item Detail PO link must use shared row-action arrow affordance", { poIconText });
    await poButton.click();
    await page.waitForURL((url) => url.pathname === `/desk/procurement-console-po-follow-up/${encodeURIComponent(purchaseOrderName)}`, { waitUntil: "domcontentloaded", timeout: TIMEOUT });
    await assertSingleProcurementShell(page, "poDetail", "Item Detail purchase order navigation");
    const poText = normalizeText(await page.locator(".erpw-procurement-po-follow-up-shell").first().innerText({ timeout: TIMEOUT }));
    assert(poText.includes(purchaseOrderName), "Item Detail PO navigation did not load the selected Procurement PO detail", { purchaseOrderName, poText });
    assert(!/Buying Item Detail|Buying item profile/i.test(poText), "PO Detail retained stale Buying Item Detail context after Item row navigation", { purchaseOrderName, poText });
    await page.goBack({ waitUntil: "domcontentloaded", timeout: TIMEOUT });
    await assertSingleProcurementShell(page, "itemDetail", "Item Detail after browser back from PO detail");
    purchaseOrderNavigation = { purchaseOrderName };
  }
  await exerciseDetailRefresh(page, ".erpw-procurement-item-detail-shell", "itemDetail", "Item Detail");
  await exerciseDetailBack(page, ".erpw-procurement-item-detail-shell", "/desk/procurement-console-worklist/buying-item-directory", "worklist", "Item Detail");
  return { itemCode, state, hasNativeFormAction, actionStyles, compactHeader, purchaseOrderNavigation, toolbarExercise: { refresh: true, back: true } };
}

async function checkCreateActions(page, user, bootstrapPayload) {
  const actions = Array.isArray(bootstrapPayload && bootstrapPayload.create_actions) ? bootstrapPayload.create_actions : [];
  const targets = (bootstrapPayload && bootstrapPayload.action_targets) || {};
  const keys = actions.map((action) => action.key).filter(Boolean);
  keys.forEach((key) => {
    assert(targets[key] && targets[key].kind === "new_doc" && targets[key].doctype, `Create action ${key} has no governed new-doc target`, { target: targets[key] });
  });
  if (user.key !== "manager") {
    assert(!keys.includes("new_supplier"), "Non-manager user should not see New Supplier in Procurement create actions", { keys });
  }
  await openDeskRoute(page, "/desk/procurement-console");
  await page.locator('[data-erpw-console-bootstrap="ready"], [data-procurement-console-state="restricted"]').first().waitFor({ state: "attached", timeout: TIMEOUT });
  const visibleKeys = await page.locator("[data-erpw-procurement-create-action]").evaluateAll((nodes) =>
    nodes.map((node) => node.getAttribute("data-erpw-procurement-create-action")).filter(Boolean)
  );
  assert(visibleKeys.join("|") === keys.join("|"), "Overview create action UI does not match backend visibility", { keys, visibleKeys });
  const labels = await page.locator("[data-erpw-procurement-create-action]").evaluateAll((nodes) =>
    nodes.map((node) => (node.textContent || "").replace(/\s+/g, " ").trim())
  );
  const variants = actions.reduce((result, action) => {
    if (action && action.key) result[action.key] = action.variant || "";
    return result;
  }, {});
  ["new_purchase_request", "new_rfq", "new_supplier_quotation", "new_purchase_order"].forEach((key) => {
    if (keys.includes(key)) assert(variants[key] === "primary", `${key} should be a primary Procurement create action`, { variants });
  });
  ["new_supplier", "new_item"].forEach((key) => {
    if (keys.includes(key)) assert(variants[key] === "secondary", `${key} should remain a secondary governed master-data action`, { variants });
  });
  const actionCardCount = await visibleElementCount(page, ".sales-console-action[data-erpw-procurement-create-action]");
  const childActionCount = await visibleElementCount(page, ".erpw-child-action[data-erpw-procurement-create-action]");
  const primaryLayout = await page.locator('[data-section-key="create-actions"] .sales-console-action-strip.primary').first().evaluate((node) => {
    const style = getComputedStyle(node);
    return {
      columns: style.gridTemplateColumns,
      actionCount: node.querySelectorAll('.sales-console-action[data-erpw-procurement-create-variant="primary"]').length,
      declaredColumns: node.getAttribute("data-erpw-action-columns") || "",
    };
  });
  assert(actionCardCount === keys.length, "Procurement create actions do not use shared Sales Console action cards", { keys, actionCardCount, childActionCount });
  assert(childActionCount === 0, "Procurement create actions still use child-page action styling", { childActionCount });
  if (["new_purchase_request", "new_rfq", "new_supplier_quotation", "new_purchase_order"].every((key) => keys.includes(key))) {
    assert(primaryLayout.actionCount === 4 && primaryLayout.declaredColumns === "2", "Core Procurement create actions should render as a balanced 2x2 primary grid", primaryLayout);
  }
  let createRoute = null;
  if (keys.includes("new_purchase_request")) {
    await page.locator('[data-erpw-procurement-create-action="new_purchase_request"]').first().click();
    await page.waitForFunction(() => {
      const route = window.frappe && typeof frappe.get_route === "function" ? frappe.get_route() : [];
      const routeText = Array.isArray(route) ? route.join("|") : String(route || "");
      return /Material Request|material-request/i.test(routeText) || /material-request/i.test(window.location.pathname || "");
    }, null, { timeout: TIMEOUT });
    createRoute = { url: page.url(), route: await page.evaluate(() => (window.frappe && typeof frappe.get_route === "function" ? frappe.get_route() : [])) };
    const nativeState = await procurementShellState(page);
    assert(nativeState.total === 0, "Create action left Procurement shell visible on native form route", nativeState);
    await openDeskRoute(page, "/desk/procurement-console");
    await assertSingleProcurementShell(page, "overview", "After create action return to Procurement Overview");
  }
  return { keys, labels, createRoute };
}

async function runUser(browser, user) {
  const context = await browser.newContext({
    baseURL: BASE_URL,
    ignoreHTTPSErrors: true,
    viewport: { width: 1440, height: 1000 },
  });
  const page = await context.newPage();
  const pageErrors = [];
  page.on("dialog", (dialog) => dialog.accept().catch(() => {}));
  page.on("pageerror", (error) => pageErrors.push(error.message));
  const report = { user: user.key };
  try {
    await login(page, user);
    report.overviewDirectLoadStability = await checkOverviewDirectLoadStability(page);
    report.defaultLandingUrl = await checkDefaultLanding(page, user);
    report.overviewStyles = await checkOverviewStyling(page);
    report.nativeChromeLifecycle = await checkProcurementNativeChromeLifecycle(page, user);
    report.reportHeaderLifecycle = await checkQuoteComparisonHeaderLifecycle(page);
    report.targetAudit = await checkProcurementTargetAudit(page, user);
    report.overviewNavigationLifecycle = await checkProcurementOverviewNavigationLifecycle(page);
    report.backForwardLifecycle = await checkProcurementBackForwardLifecycle(page);
    report.sidebarLabels = await checkProcurementSidebar(page);
    await openDeskRoute(page, "/desk/procurement-console");
    const bootstrap = await callMethod(page, "erp_workspace_ui.procurement_console.service.get_procurement_console_bootstrap");
    assert(bootstrap.ok, `${user.label}: bootstrap failed`, bootstrap);
    const bootstrapPayload = bootstrap.data && bootstrap.data.message ? bootstrap.data.message : {};
    const state = bootstrapPayload && bootstrapPayload.state ? bootstrapPayload.state.kind : "missing";
    report.bootstrapState = state;
    if (state === "ready") {
      if (user.key === "manager") {
        report.topChrome = await checkTopChrome(page);
        report.focusStability = await checkFocusStability(page);
        report.datePairLayout = await checkDatePairLayout(page);
        report.enterpriseListFilterLayouts = await checkEnterpriseListFilterLayouts(page);
      }
      report.createActions = await checkCreateActions(page, user, bootstrapPayload);
      report.worklists = {};
      let firstPoName = process.env.ERPW_PROCUREMENT_PO_NAME || "";
      for (const item of WORKLISTS) {
        const result = await checkWorklist(page, item, user);
        report.worklists[item.key] = result;
        if (!firstPoName && result.firstRow && result.firstRow.name) firstPoName = result.firstRow.name;
      }
      if (!firstPoName) {
        const purchaseOrderPayload = await worklistPayload(page, "purchase_order_directory");
        firstPoName = firstRowName(purchaseOrderPayload);
      }
      const directPoName = process.env.ERPW_PROCUREMENT_DIRECT_PO_NAME || firstPoName || "PUR-ORD-2026-00010";
      report.directDetail = await checkDetail(page, directPoName, { requireReadyShell: true, exerciseToolbar: true });
      report.supplierAutocomplete = await checkSupplierAutocomplete(page);
      report.supplierDetail = await checkSupplierDetail(page, user);
      report.itemDetail = await checkItemDetail(page, user);
      report.quoteComparisonUrl = await checkQuoteComparisonFromSidebar(page);
      report.detail = await checkDetail(page, firstPoName);
    } else {
      assert(state === "restricted", `${user.label}: unexpected bootstrap state`, { state });
      await openDeskRoute(page, "/desk/procurement-console-worklist/purchase-orders-overdue");
      await page.locator(".erpw-list-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
      report.restrictedRoute = true;
    }
    assert(pageErrors.length === 0, `${user.label}: page JS error`, { pageErrors });
    return report;
  } finally {
    await context.close();
  }
}

(async () => {
  assert(USERS.length > 0, "No smoke users are available in environment variables");
  const browser = await chromium.launch({ headless: true });
  try {
    const reports = [];
    for (const user of USERS) {
      reports.push(await runUser(browser, user));
    }
    console.log(JSON.stringify({ ok: true, baseUrl: BASE_URL, reports }, null, 2));
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error.stack || error.message);
  if (error.details) console.error(JSON.stringify(error.details, null, 2));
  process.exit(1);
});
