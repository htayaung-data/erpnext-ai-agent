const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const OUT_DIR = process.env.ERPW_ROLE_SMOKE_OUT || path.join(process.env.TEMP || process.cwd(), "erpw-role-smoke");
const TIMEOUT = Number(process.env.ERPW_ROLE_SMOKE_TIMEOUT || 45000);

const USERS = [
  {
    key: "manager",
    label: "Sales Manager",
    username: process.env.ERPW_MANAGER_USERNAME,
    password: process.env.ERPW_MANAGER_PASSWORD,
    expectedVariant: "sales_manager",
  },
  {
    key: "user",
    label: "Sales User",
    username: process.env.ERPW_USER_USERNAME,
    password: process.env.ERPW_USER_PASSWORD,
    expectedVariant: "sales_executive",
  },
];

function requireValue(value, name) {
  if (!value) throw new Error(`Missing ${name}`);
  return value;
}

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

async function login(page, user) {
  await page.goto(routeUrl("/login"), { waitUntil: "domcontentloaded", timeout: TIMEOUT });

  const userField = page.locator("#login_email, input[name='usr'], input[name='login_email'], input[type='email'], input[type='text']").first();
  const passwordField = page.locator("#login_password, input[name='pwd'], input[name='login_password'], input[type='password']").first();
  const loginButton = page.locator("button:has-text('Login'), button.btn-login, .btn-login").first();

  await userField.waitFor({ state: "visible", timeout: TIMEOUT });
  await userField.fill(user.username);
  await passwordField.fill(user.password);
  await Promise.all([
    page.waitForURL(/\/(?:app|desk)(?:[/?#]|$)/, { timeout: TIMEOUT }),
    loginButton.click(),
  ]);
}

async function openDeskRoute(page, route) {
  await page.goto(routeUrl(route), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  if (/\/login(?:[/?#]|$)/.test(page.url())) {
    throw new Error(`Route ${route} redirected to login`);
  }
  await page.waitForFunction(() => Boolean(window.frappe), null, { timeout: TIMEOUT });
}

async function callMethod(page, method, args = {}) {
  return page.evaluate(
    async ({ method, args }) => {
      const body = new URLSearchParams();
      for (const [key, value] of Object.entries(args || {})) {
        body.set(key, typeof value === "string" ? value : JSON.stringify(value));
      }
      const response = await fetch(`/api/method/${method}`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
          "X-Frappe-CSRF-Token": (window.frappe && window.frappe.csrf_token) || "",
        },
        body,
      });
      let data = null;
      try {
        data = await response.json();
      } catch (error) {
        data = { raw: await response.text() };
      }
      return { ok: response.ok, status: response.status, data };
    },
    { method, args }
  );
}

async function visibleTexts(page, selector) {
  return page.locator(selector).evaluateAll((nodes) =>
    nodes
      .filter((node) => {
        const style = window.getComputedStyle(node);
        const rect = node.getBoundingClientRect();
        return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
      })
      .map((node) => node.textContent.replace(/\s+/g, " ").trim())
      .filter(Boolean)
  );
}

async function checkHome(page, user, report) {
  await openDeskRoute(page, "/desk/sales-console");
  const shell = page.locator(".sales-console-shell").first();
  await shell.waitFor({ state: "visible", timeout: TIMEOUT });
  await page.waitForFunction(() => {
    const element = document.querySelector(".sales-console-shell");
    return element && element.getAttribute("data-erpw-console-runtime") === "ready";
  }, null, { timeout: TIMEOUT });
  await page.waitForFunction(() => {
    const element = document.querySelector(".sales-console-shell");
    return element && element.getAttribute("data-erpw-console-bootstrap") === "ready";
  }, null, { timeout: TIMEOUT });

  const title = normalizeText(await page.locator(".sales-console-title").first().innerText({ timeout: TIMEOUT }));
  assert(title === "Sales Console", `${user.label}: home title mismatch`, { title });

  const sidebarLabels = await visibleTexts(page, ".erpw-sales-console-sidebar-text");
  const expectedSidebar = ["Overview", "Quotations", "Sales Orders", "Customers", "Items"];
  assert(
    expectedSidebar.every((label, index) => sidebarLabels[index] === label),
    `${user.label}: sidebar labels/order mismatch`,
    { sidebarLabels, expectedSidebar }
  );

  const actionCount = await page.locator(".sales-console-action:visible").count();
  assert(actionCount > 0, `${user.label}: no visible Sales Console action cards`);

  const roleLine = await page.locator("[data-header-roleline]").first().innerText({ timeout: TIMEOUT }).catch(() => "");
  report.home = {
    url: page.url(),
    title,
    sidebarLabels,
    actionCount,
    roleLine: normalizeText(roleLine),
  };
}

async function checkWorklists(page, user, report) {
  const routes = [
    { key: "quotation_directory", route: "/desk/sales-console-worklist/quotation-directory", title: "Quotations" },
    { key: "sales_order_directory", route: "/desk/sales-console-worklist/sales-order-directory", title: "Sales Orders" },
    { key: "customer_directory", route: "/desk/sales-console-worklist/customer-directory", title: "Customers" },
    { key: "item_directory", route: "/desk/sales-console-worklist/item-directory", title: "Items" },
  ];

  report.worklists = {};
  for (const item of routes) {
    await openDeskRoute(page, item.route);
    await page.locator(".erpw-list-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
    await page.waitForFunction(
      (expectedTitle) => {
        const title = document.querySelector(".erpw-list-title");
        const stateTitle = document.querySelector(".erpw-list-state-title");
        const normalizedTitle = title ? title.textContent.replace(/\s+/g, " ").trim() : "";
        const normalizedState = stateTitle ? stateTitle.textContent.replace(/\s+/g, " ").trim() : "";
        return normalizedTitle === expectedTitle || /failed|unavailable|restricted/i.test(normalizedState);
      },
      item.title,
      { timeout: TIMEOUT }
    );
    const title = normalizeText(await page.locator(".erpw-list-title").first().innerText({ timeout: TIMEOUT }));
    const actions = await page.locator("[data-erpw-list-action-key]").evaluateAll((nodes) =>
      nodes.map((node) => ({
        key: node.getAttribute("data-erpw-list-action-key"),
        text: node.textContent.replace(/\s+/g, " ").trim(),
      }))
    );
    assert(title === item.title, `${user.label}: ${item.key} title mismatch`, { title, expected: item.title });
    report.worklists[item.key] = { url: page.url(), title, actions };
  }

  const customerActions = report.worklists.customer_directory.actions.map((action) => action.key);
  if (user.expectedVariant === "sales_manager") {
    assert(customerActions.includes("create_customer"), `${user.label}: missing Create Customer action`, { customerActions });
  } else {
    assert(!customerActions.includes("create_customer"), `${user.label}: restricted Create Customer action is visible`, { customerActions });
  }
}

async function checkCustomerEditor(page, user, report) {
  await openDeskRoute(page, "/desk/sales-console-worklist/customer-editor");
  await page.locator(".erpw-list-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  await page.waitForFunction(
    () => {
      const shell = document.querySelector(".erpw-list-shell");
      const text = shell ? shell.textContent.replace(/\s+/g, " ").trim() : "";
      return text.includes("Create Customer") || text.includes("Customer management restricted");
    },
    null,
    { timeout: TIMEOUT }
  );
  const pageText = normalizeText(await page.locator(".erpw-list-shell").first().innerText({ timeout: TIMEOUT }));
  const saveVisible = await page.locator("[data-erpw-list-action-key='save_customer_profile']:visible").count();

  if (user.expectedVariant === "sales_manager") {
    assert(saveVisible === 1, `${user.label}: Save Customer should be visible on customer create route`, { pageText });
    assert(pageText.includes("Create Customer"), `${user.label}: customer editor create title missing`, { pageText });
  } else {
    assert(saveVisible === 0, `${user.label}: Save Customer is visible for restricted user`, { pageText });
    assert(pageText.includes("Customer management restricted"), `${user.label}: restricted customer editor state missing`, { pageText });
  }

  report.customerEditor = { url: page.url(), saveVisible, textExcerpt: pageText.slice(0, 300) };
}

async function checkReport(page, user, report) {
  await openDeskRoute(page, "/desk/sales-console-report/sales-analytics");
  await page.locator(".erpw-report-shell").first().waitFor({ state: "visible", timeout: TIMEOUT });
  await page.locator("[data-erpw-report-action-key='refresh']").first().waitFor({ state: "visible", timeout: TIMEOUT });
  const actions = await page.locator("[data-erpw-report-action-key]").evaluateAll((nodes) =>
    nodes
      .filter((node) => {
        const style = window.getComputedStyle(node);
        const rect = node.getBoundingClientRect();
        return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
      })
      .map((node) => ({
        key: node.getAttribute("data-erpw-report-action-key"),
        text: node.textContent.replace(/\s+/g, " ").trim(),
      }))
  );
  const firstKeys = actions.map((action) => action.key).slice(0, 2);
  assert(
    firstKeys[0] === "refresh" && firstKeys[1] === "back_to_console",
    `${user.label}: report action order mismatch`,
    { actions }
  );
  report.report = { url: page.url(), actions };
}

async function checkApiContracts(page, user, report) {
  const sidebar = await callMethod(page, "erp_workspace_ui.sales_console.service.get_sales_console_sidebar_context");
  assert(sidebar.ok, `${user.label}: sidebar API failed`, sidebar);
  const context = sidebar.data.message.context || {};
  assert(context.role_variant === user.expectedVariant, `${user.label}: role variant mismatch`, context);

  const sidebarLabels = (sidebar.data.message.sidebar.sections || [])
    .flatMap((section) => section.items || [])
    .map((item) => item.label);
  assert(sidebarLabels[0] === "Overview", `${user.label}: sidebar API did not return Overview first`, { sidebarLabels });

  const customerDirectory = await callMethod(page, "erp_workspace_ui.sales_console.worklist.get_sales_console_worklist_context", {
    queue_key: "customer_directory",
  });
  assert(customerDirectory.ok, `${user.label}: customer directory API failed`, customerDirectory);
  const customerActionKeys = ((customerDirectory.data.message.controls || {}).actions || []).map((action) => action.key);

  const customerEditor = await callMethod(page, "erp_workspace_ui.sales_console.worklist.get_sales_console_worklist_context", {
    queue_key: "customer_editor",
    filters: { mode: "new" },
  });
  assert(customerEditor.ok, `${user.label}: customer editor API failed`, customerEditor);
  const customerEditorMessage = customerEditor.data.message || {};

  const reportContext = await callMethod(page, "erp_workspace_ui.sales_console.report.get_sales_console_report_context", {
    report_key: "sales_analytics",
  });
  assert(reportContext.ok, `${user.label}: report API failed`, reportContext);
  const reportActionKeys = ((reportContext.data.message.controls || {}).actions || []).map((action) => action.key);
  assert(
    reportActionKeys[0] === "refresh" && reportActionKeys[1] === "back_to_console",
    `${user.label}: report API action order mismatch`,
    { reportActionKeys }
  );

  let restrictedSaveProbe = null;
  if (user.expectedVariant !== "sales_manager") {
    restrictedSaveProbe = await callMethod(page, "erp_workspace_ui.sales_console.worklist.save_sales_console_customer_profile", {
      payload: { mode: "new" },
    });
    const serverMessages = JSON.stringify(restrictedSaveProbe.data || {});
    assert(
      restrictedSaveProbe.status === 403 || serverMessages.includes("Only Sales Managers"),
      `${user.label}: restricted save probe did not hit Sales Manager permission gate`,
      { status: restrictedSaveProbe.status, serverMessages }
    );
  }

  if (user.expectedVariant === "sales_manager") {
    assert(customerActionKeys.includes("create_customer"), `${user.label}: create_customer missing from API`, { customerActionKeys });
    const editorActions = ((customerEditorMessage.controls || {}).actions || []).map((action) => action.key);
    assert(editorActions.includes("save_customer_profile"), `${user.label}: manager editor API missing save action`, { editorActions });
  } else {
    assert(!customerActionKeys.includes("create_customer"), `${user.label}: create_customer leaked in API`, { customerActionKeys });
    const stateTitle = ((customerEditorMessage.results || {}).state || {}).title || "";
    assert(stateTitle === "Customer management restricted", `${user.label}: restricted API state mismatch`, { stateTitle });
  }

  report.api = {
    roleVariant: context.role_variant,
    sidebarLabels,
    customerActionKeys,
    customerEditorState: ((customerEditorMessage.results || {}).state || {}).title || "",
    reportActionKeys,
    restrictedSaveProbe: restrictedSaveProbe
      ? { status: restrictedSaveProbe.status, message: JSON.stringify(restrictedSaveProbe.data || {}).slice(0, 300) }
      : null,
  };
}

async function runRole(browser, user) {
  requireValue(user.username, `${user.key} username`);
  requireValue(user.password, `${user.key} password`);

  const context = await browser.newContext({
    baseURL: BASE_URL,
    ignoreHTTPSErrors: true,
    viewport: { width: 1440, height: 1200 },
  });
  const page = await context.newPage();
  const report = { role: user.label, username: user.username };

  try {
    await login(page, user);
    await checkHome(page, user, report);
    await checkWorklists(page, user, report);
    await checkCustomerEditor(page, user, report);
    await checkReport(page, user, report);
    await checkApiContracts(page, user, report);
    await page.screenshot({ path: path.join(OUT_DIR, `${user.key}-final.png`), fullPage: true });
    report.status = "passed";
    return report;
  } catch (error) {
    await page.screenshot({ path: path.join(OUT_DIR, `${user.key}-failure.png`), fullPage: true }).catch(() => {});
    report.status = "failed";
    report.error = error.message;
    report.details = error.details || null;
    throw Object.assign(error, { roleReport: report });
  } finally {
    await context.close();
  }
}

(async () => {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const browser = await chromium.launch({ headless: process.env.ERPW_HEADLESS !== "0" });
  const reports = [];
  try {
    for (const user of USERS) {
      const roleReport = await runRole(browser, user);
      reports.push(roleReport);
      console.log(`[pass] ${user.label}`);
    }
  } catch (error) {
    if (error.roleReport) reports.push(error.roleReport);
    console.error(`[fail] ${error.message}`);
    if (error.details) console.error(JSON.stringify(error.details, null, 2));
    process.exitCode = 1;
  } finally {
    await browser.close();
    fs.writeFileSync(path.join(OUT_DIR, "role-permission-report.json"), `${JSON.stringify(reports, null, 2)}\n`, "utf8");
    console.log(`report=${path.join(OUT_DIR, "role-permission-report.json")}`);
  }
})();
