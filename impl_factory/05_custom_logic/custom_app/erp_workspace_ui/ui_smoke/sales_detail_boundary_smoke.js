const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const OUT_DIR = process.env.ERPW_SALES_DETAIL_OUT || path.join(process.cwd(), "artifacts", "sales-detail-boundary-smoke");
const TIMEOUT = Number(process.env.ERPW_SALES_DETAIL_TIMEOUT || 70000);
const WORKLIST_METHOD_PATH = "/api/method/erp_workspace_ui.sales_console.worklist.get_sales_console_worklist_context";

const USER = {
  label: "Sales Manager",
  username: process.env.ERPW_MANAGER_USERNAME || process.env.ERPW_USERNAME,
  password: process.env.ERPW_MANAGER_PASSWORD || process.env.ERPW_PASSWORD,
};

const FORBIDDEN_MUTATION_LABELS = new Set([
  "Submit",
  "Cancel",
  "Amend",
  "Close",
  "Unclose",
  "Approve",
  "Reject",
  "Receive",
  "Bill",
  "Pay",
  "Set Default Supplier",
  "Update Item Price",
  "Delete",
]);

function requireValue(value, name) {
  if (!value) throw new Error(`Missing ${name}`);
  return value;
}

function routeUrl(route) {
  return new URL(route, BASE_URL).toString();
}

function normalizeText(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function safeFileKey(value) {
  return String(value || "detail").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "detail";
}

function assert(condition, message, details = {}) {
  if (!condition) {
    const error = new Error(message);
    error.details = details;
    throw error;
  }
}

async function login(page) {
  await page.goto(routeUrl("/login"), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  const userField = page.locator("#login_email, input[name='usr'], input[name='login_email'], input[type='email'], input[type='text']").first();
  const passwordField = page.locator("#login_password, input[name='pwd'], input[name='login_password'], input[type='password']").first();
  const loginButton = page.locator("button:has-text('Login'), button.btn-login, .btn-login").first();
  await userField.waitFor({ state: "visible", timeout: TIMEOUT });
  await userField.fill(USER.username);
  await passwordField.fill(USER.password);
  await Promise.all([
    page.waitForURL(/\/(?:app|desk)(?:[/?#]|$)/, { waitUntil: "domcontentloaded", timeout: TIMEOUT }),
    loginButton.click(),
  ]);
  await page.waitForFunction(() => Boolean(window.frappe), null, { timeout: TIMEOUT });
}

async function waitForWorklistApi(page) {
  return page.waitForResponse(
    (response) => response.url().includes(WORKLIST_METHOD_PATH) && response.request().method() === "POST",
    { timeout: TIMEOUT }
  );
}

async function waitForListShell(page, expectedPattern) {
  await page.locator(".erpw-list-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  await page.waitForFunction(() => {
    const shell = document.querySelector(".erpw-list-shell");
    return shell && shell.getAttribute("aria-busy") !== "true";
  }, null, { timeout: TIMEOUT });
  if (expectedPattern) {
    await page.waitForFunction((pattern) => new RegExp(pattern).test(window.location.pathname), expectedPattern, { timeout: TIMEOUT });
  }
}

async function openWorklist(page, route, title) {
  const responsePromise = waitForWorklistApi(page).catch(() => null);
  await page.goto(routeUrl(route), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  if (/\/login(?:[/?#]|$)/.test(page.url())) throw new Error(`${title}: redirected to login`);
  await responsePromise;
  await waitForListShell(page);
}

async function visibleCounts(page) {
  return page.evaluate(() => {
    const visible = (node) => {
      if (!node) return false;
      const style = window.getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
    };
    const count = (selector) => Array.from(document.querySelectorAll(selector)).filter(visible).length;
    return {
      listShell: count(".erpw-list-shell"),
      childShell: count(".erpw-child-shell"),
      pageHead: count(".page-head"),
      nativeForm: count(".form-layout, .form-page"),
    };
  });
}

async function assertNoDuplicateShellOrHeader(page, label) {
  const counts = await visibleCounts(page);
  assert(counts.listShell + counts.childShell <= 1, `${label}: duplicate managed shells found`, counts);
  assert(counts.pageHead <= 1, `${label}: duplicate page headers found`, counts);
  return counts;
}

async function scanForbiddenMutations(page, label) {
  const matches = await page.evaluate((labels) => {
    const forbidden = new Set(labels);
    const visible = (node) => {
      const style = window.getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
    };
    return Array.from(document.querySelectorAll("button, a, [role='button']"))
      .filter(visible)
      .map((node) => ({
        tag: node.tagName.toLowerCase(),
        text: (node.textContent || "").replace(/\s+/g, " ").trim(),
        actionKey: node.getAttribute("data-erpw-list-action-key") || "",
        href: node.getAttribute("href") || "",
      }))
      .filter((item) => forbidden.has(item.text));
  }, Array.from(FORBIDDEN_MUTATION_LABELS));
  assert(matches.length === 0, `${label}: forbidden mutation actions visible on productized page`, { matches });
  return matches;
}

async function assertNoGenericNativeOpen(page, label) {
  const leaks = await page.evaluate(() => {
    const visible = (node) => {
      const style = window.getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
    };
    return Array.from(document.querySelectorAll("button, a, [role='button']"))
      .filter(visible)
      .map((node) => ({
        text: (node.textContent || "").replace(/\s+/g, " ").trim(),
        actionKey: node.getAttribute("data-erpw-list-action-key") || "",
        href: node.getAttribute("href") || "",
      }))
      .filter((item) => /Open ERP Form/i.test(item.text) || /\/(?:app|desk)\/Form\//i.test(item.href));
  });
  assert(leaks.length === 0, `${label}: generic native open leakage visible`, { leaks });
  return leaks;
}

async function clickFirstInlineOpen(page, label) {
  const button = page.locator(".erpw-list-inline-open:visible").first();
  await button.waitFor({ state: "visible", timeout: TIMEOUT });
  const text = normalizeText(await button.innerText());
  const responsePromise = waitForWorklistApi(page).catch(() => null);
  await button.click();
  await responsePromise;
  return text || label;
}

async function openFirstDetailFromDirectory(page, directoryRoute, routePattern, label, report) {
  await openWorklist(page, directoryRoute, label);
  const sourceText = await clickFirstInlineOpen(page, label);
  await waitForListShell(page, routePattern);
  const route = await page.evaluate(() => (window.frappe && typeof window.frappe.get_route === "function" ? window.frappe.get_route() : []));
  const counts = await assertNoDuplicateShellOrHeader(page, `${label} detail`);
  await assertNoGenericNativeOpen(page, `${label} detail`);
  await scanForbiddenMutations(page, `${label} detail`);
  const toolbar = await page.locator(".erpw-list-action-button:visible").evaluateAll((nodes) =>
    nodes.map((node) => ({
      key: node.getAttribute("data-erpw-list-action-key"),
      scope: node.getAttribute("data-erpw-list-action-scope"),
      className: node.className,
      text: node.textContent.replace(/\s+/g, " ").trim(),
    }))
  );
  assert(toolbar.some((item) => /^back_to_/.test(item.key || "")), `${label} detail: missing shared compact back action`, { toolbar });
  assert(toolbar.every((item) => /\berpw-list-action-button\b/.test(item.className)), `${label} detail: toolbar action missing shared class`, { toolbar });
  const screenshot = path.join(OUT_DIR, `${safeFileKey(label)}-detail.png`);
  await page.screenshot({ path: screenshot, fullPage: true });
  report.details[label] = { sourceText, route, url: page.url(), counts, toolbar, screenshot };
}

async function assertItemDetailPremiumLayout(page, label, report) {
  await waitForListShell(page, "/sales-console-worklist/item-detail/");
  const state = await page.evaluate(() => {
    const visible = (node) => {
      if (!node) return false;
      const style = window.getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
    };
    const shell = document.querySelector(".erpw-list-shell");
    const summary = document.querySelector(".erpw-list-summary-card");
    const metricNodes = Array.from(document.querySelectorAll(".erpw-list-summary-card .erpw-list-summary-metric")).filter(visible);
    const metricRects = metricNodes.map((node) => {
      const rect = node.getBoundingClientRect();
      return {
        label: (node.querySelector(".erpw-list-metric-label") || {}).textContent || "",
        value: (node.querySelector(".erpw-list-metric-value") || {}).textContent || "",
        left: Math.round(rect.left),
        top: Math.round(rect.top),
        width: Math.round(rect.width),
        height: Math.round(rect.height),
      };
    });
    const toolbarActions = Array.from(document.querySelectorAll(".erpw-list-summary-toolbar [data-erpw-list-action-key]")).filter(visible).map((node) => ({
      key: node.getAttribute("data-erpw-list-action-key"),
      text: node.textContent.replace(/\s+/g, " ").trim(),
      className: node.className,
    }));
    return {
      hasDetailHeader: Boolean(summary && summary.classList.contains("is-detail-header")),
      title: (document.querySelector(".erpw-list-title") || {}).textContent || "",
      subtitle: (document.querySelector(".erpw-list-subtitle") || {}).textContent || "",
      toolbarActions,
      metricRects,
      metricRows: Array.from(new Set(metricRects.map((rect) => rect.top))).length,
      shellOverflow: shell ? Math.round(shell.scrollWidth - shell.clientWidth) : 0,
      duplicateHeaders: Array.from(document.querySelectorAll(".page-head")).filter(visible).length,
    };
  });
  assert(state.hasDetailHeader, `${label}: item detail header is not using the shared detail variant`, state);
  assert(state.toolbarActions.some((action) => action.key === "back_to_items"), `${label}: Back to Items is missing from compact toolbar`, state);
  assert(state.toolbarActions.some((action) => action.key === "refresh"), `${label}: Refresh is missing from compact toolbar`, state);
  assert(state.metricRects.length >= 4, `${label}: item KPI cards missing`, state);
  assert(state.metricRows === 1, `${label}: item KPI cards wrapped awkwardly at desktop width`, state);
  assert(state.shellOverflow <= 2, `${label}: item detail has horizontal overflow`, state);
  assert(state.duplicateHeaders <= 1, `${label}: duplicate header/chrome visible`, state);
  const screenshot = path.join(OUT_DIR, `${safeFileKey(label)}-premium-layout.png`);
  await page.screenshot({ path: screenshot, fullPage: true });
  report.itemDetailPremium = report.itemDetailPremium || {};
  report.itemDetailPremium[safeFileKey(label)] = Object.assign({ screenshot }, state);
}

async function openSpecificItemDetail(page, itemCode, report) {
  const responsePromise = waitForWorklistApi(page).catch(() => null);
  await page.goto(routeUrl(`/desk/sales-console-worklist/item-detail/${encodeURIComponent(itemCode)}`), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  await responsePromise;
  await assertItemDetailPremiumLayout(page, `Item Detail ${itemCode}`, report);
}

async function openCustomerEditorIfAvailable(page, report) {
  const editButton = page.locator('[data-erpw-list-action-key="edit_customer"]:visible').first();
  if ((await editButton.count()) === 0) {
    report.customerEditor = { status: "skipped", reason: "Edit Customer action is not visible for this account/record." };
    return;
  }
  const responsePromise = waitForWorklistApi(page).catch(() => null);
  await editButton.click();
  await responsePromise;
  await waitForListShell(page, "/sales-console-worklist/customer-editor/");
  const route = await page.evaluate(() => (window.frappe && typeof window.frappe.get_route === "function" ? window.frappe.get_route() : []));
  const hasFormPanel = await page.locator(".erpw-list-controls-strip.is-form-panel:visible").count();
  assert(hasFormPanel > 0, "Customer editor: productized form panel shell missing");
  await scanForbiddenMutations(page, "Customer editor");
  const screenshot = path.join(OUT_DIR, "customer-editor.png");
  await page.screenshot({ path: screenshot, fullPage: true });
  report.customerEditor = { status: "checked", route, url: page.url(), screenshot };
}

async function openManagedSalesOrderForm(page, route, label, report) {
  await page.goto(routeUrl(route), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  if (/\/login(?:[/?#]|$)/.test(page.url())) throw new Error(`${label}: redirected to login`);
  await page.waitForFunction(() => {
    const route = window.frappe && typeof window.frappe.get_route === "function" ? window.frappe.get_route() : [];
    return Array.isArray(route) && route[0] === "Form" && route[1] === "Sales Order";
  }, null, { timeout: TIMEOUT });
  await page.locator(".erpw-child-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  await page.waitForFunction(() => {
    const shell = document.querySelector(".erpw-child-shell");
    const skeleton = document.querySelector(".erpw-so-shell-skeleton");
    if (!shell) return false;
    const rect = shell.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0 && !skeleton;
  }, null, { timeout: TIMEOUT });
  const state = await page.evaluate(() => {
    const visible = (node) => {
      if (!node) return false;
      const style = window.getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
    };
    const route = window.frappe && typeof window.frappe.get_route === "function" ? window.frappe.get_route() : [];
    return {
      route,
      url: window.location.href,
      childShellCount: Array.from(document.querySelectorAll(".erpw-child-shell")).filter(visible).length,
      skeletonCount: Array.from(document.querySelectorAll(".erpw-so-shell-skeleton")).filter(visible).length,
      actionRects: Array.from(document.querySelectorAll(".erpw-child-action")).filter(visible).map((node) => {
        const rect = node.getBoundingClientRect();
        return { left: Math.round(rect.left), top: Math.round(rect.top), width: Math.round(rect.width), height: Math.round(rect.height) };
      }),
      shellOverflow: (() => {
        const shell = document.querySelector(".erpw-child-shell");
        return shell ? Math.round(shell.scrollWidth - shell.clientWidth) : 0;
      })(),
      title: (document.querySelector(".page-title .title-text, .title-area .title-text") || {}).textContent || "",
    };
  });
  state.actionCardCount = state.actionRects.length;
  state.actionColumns = Array.from(new Set(state.actionRects.map((rect) => rect.left))).length;
  assert(state.childShellCount === 1, `${label}: managed Sales Order shell missing or duplicated`, state);
  assert(state.skeletonCount === 0, `${label}: persistent Sales Order skeleton visible`, state);
  if (state.actionCardCount >= 4) {
    assert(state.actionColumns >= 2, `${label}: Sales Order action cards collapsed into one desktop column`, state);
  }
  assert(state.shellOverflow <= 2, `${label}: managed Sales Order shell has horizontal overflow`, state);
  const counts = await assertNoDuplicateShellOrHeader(page, label);
  const screenshot = path.join(OUT_DIR, `${safeFileKey(label)}.png`);
  await page.screenshot({ path: screenshot, fullPage: true });
  report.salesOrders = report.salesOrders || {};
  report.salesOrders[safeFileKey(label)] = Object.assign({ counts, screenshot }, state);
}

async function openManagedDocumentForm(page, report) {
  await openWorklist(page, "/desk/sales-console-worklist/quotation-directory", "Quotation Directory");
  const rowButton = page.locator(".erpw-list-inline-open:visible").first();
  let openedFrom = "quotation_directory_row";
  if ((await rowButton.count()) > 0) {
    await rowButton.click();
  } else {
    const newButton = page.locator('[data-erpw-list-action-key="new_quotation"]:visible').first();
    await newButton.waitFor({ state: "visible", timeout: TIMEOUT });
    openedFrom = "quotation_directory_new_quotation";
    await newButton.click();
  }
  await page.waitForFunction(() => {
    const route = window.frappe && typeof window.frappe.get_route === "function" ? window.frappe.get_route() : [];
    return Array.isArray(route) && route[0] === "Form" && ["Quotation", "Sales Order"].includes(route[1]);
  }, null, { timeout: TIMEOUT });
  await page.waitForFunction(() => {
    const shell = document.querySelector(".erpw-child-shell");
    const skeleton = document.querySelector(".erpw-so-shell-skeleton");
    return shell && shell.getBoundingClientRect().height > 0 && !skeleton;
  }, null, { timeout: TIMEOUT }).catch(() => {});
  const state = await page.evaluate(() => {
    const route = window.frappe && typeof window.frappe.get_route === "function" ? window.frappe.get_route() : [];
    const title = document.querySelector(".page-title .title-text, .title-area .title-text");
    return {
      route,
      url: window.location.href,
      childShellCount: Array.from(document.querySelectorAll(".erpw-child-shell")).filter((node) => {
        const rect = node.getBoundingClientRect();
        const style = window.getComputedStyle(node);
        return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
      }).length,
      toolbarCount: document.querySelectorAll(".erpw-child-toolbar-action").length,
      title: title ? title.textContent.replace(/\s+/g, " ").trim() : "",
    };
  });
  assert(["Quotation", "Sales Order"].includes(state.route[1]), "Managed Sales document form did not open", state);
  assert(state.childShellCount <= 1, "Managed Sales document form stacked child shells", state);
  const counts = await assertNoDuplicateShellOrHeader(page, "Managed Sales document form");
  const screenshot = path.join(OUT_DIR, "managed-sales-document-form.png");
  await page.screenshot({ path: screenshot, fullPage: true });
  report.managedForm = Object.assign({ openedFrom, counts, screenshot }, state);
}

(async () => {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  requireValue(USER.username, "Sales Manager username");
  requireValue(USER.password, "Sales Manager password");

  const browser = await chromium.launch({ headless: process.env.ERPW_HEADLESS !== "0" });
  const context = await browser.newContext({
    baseURL: BASE_URL,
    ignoreHTTPSErrors: true,
    viewport: { width: 1440, height: 1200 },
  });
  const page = await context.newPage();
  const consoleMessages = [];
  const pageErrors = [];
  page.on("console", (message) => {
    if (["error", "warning"].includes(message.type())) consoleMessages.push({ type: message.type(), text: message.text() });
  });
  page.on("pageerror", (error) => pageErrors.push(error.message || String(error)));

  const report = {
    role: USER.label,
    username: USER.username,
    details: {},
    customerEditor: null,
    managedForm: null,
    salesOrders: {},
    itemDetailPremium: {},
    consoleMessages,
    pageErrors,
  };

  try {
    await login(page);
    await openFirstDetailFromDirectory(page, "/desk/sales-console-worklist/customer-directory", "/sales-console-worklist/customer-detail/", "Customer", report);
    await openCustomerEditorIfAvailable(page, report);
    await openFirstDetailFromDirectory(page, "/desk/sales-console-worklist/item-directory", "/sales-console-worklist/item-detail/", "Item", report);
    await assertItemDetailPremiumLayout(page, "Item Detail", report);
    await openSpecificItemDetail(page, "CCTV-NVR-4CH", report);
    await openManagedDocumentForm(page, report);
    await openManagedSalesOrderForm(page, "/desk/sales-order/SAL-ORD-2026-00037", "Existing Sales Order", report);
    await openManagedSalesOrderForm(page, "/desk/sales-order/new-sales-order", "New Sales Order", report);
    const hardErrors = consoleMessages.filter((message) => message.type === "error");
    assert(hardErrors.length === 0, "Console errors detected during Sales detail/form boundary smoke", { hardErrors });
    assert(pageErrors.length === 0, "Page errors detected during Sales detail/form boundary smoke", { pageErrors });
    report.status = "passed";
    console.log("[pass] Sales detail and managed form boundary");
  } catch (error) {
    report.status = "failed";
    report.error = error.message;
    report.details = error.details || null;
    await page.screenshot({ path: path.join(OUT_DIR, "failure.png"), fullPage: true }).catch(() => {});
    console.error(`[fail] ${error.message}`);
    if (error.details) console.error(JSON.stringify(error.details, null, 2));
    process.exitCode = 1;
  } finally {
    await context.close();
    await browser.close();
    fs.writeFileSync(path.join(OUT_DIR, "sales-detail-boundary-report.json"), `${JSON.stringify(report, null, 2)}\n`, "utf8");
    console.log(`report=${path.join(OUT_DIR, "sales-detail-boundary-report.json")}`);
  }
})();
