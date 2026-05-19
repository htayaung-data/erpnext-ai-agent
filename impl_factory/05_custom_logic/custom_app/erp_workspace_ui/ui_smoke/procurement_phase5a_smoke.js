const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const TIMEOUT = Number(process.env.ERPW_PROCUREMENT_SMOKE_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_PROCUREMENT_PHASE5A_ARTIFACT_DIR || path.join(__dirname, "artifacts", "procurement-phase5a");
fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

const USERS = [
  { key: "manager", label: "Purchase Manager", username: process.env.ERPW_MANAGER_USERNAME, password: process.env.ERPW_MANAGER_PASSWORD },
  { key: "user", label: "Purchase User", username: process.env.ERPW_USER_USERNAME, password: process.env.ERPW_USER_PASSWORD },
].filter((user) => user.username && user.password);

const FORBIDDEN_ACTION_RE = /(submit|cancel|amend|stop|close|receive|bill|pay|payment|invoice|create purchase order|new rfq|new supplier quotation|item price|default supplier|set default supplier)/i;

function assert(condition, message, details = {}) {
  if (!condition) {
    const error = new Error(message);
    error.details = details;
    throw error;
  }
}

function routeUrl(route) {
  return new URL(route, BASE_URL).toString();
}

function safeFileName(value) {
  return String(value || "shot").replace(/[^a-z0-9_-]+/gi, "-").replace(/^-+|-+$/g, "").toLowerCase();
}

async function capture(page, name) {
  const file = path.join(ARTIFACT_DIR, `${safeFileName(name)}.png`);
  await page.screenshot({ path: file, fullPage: true });
  return file;
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
  const url = routeUrl(route);
  const pathName = new URL(url).pathname;
  const canRoute = await page.evaluate(() => Boolean(window.frappe && typeof frappe.set_route === "function")).catch(() => false);
  if (canRoute && pathName.startsWith("/desk/")) {
    const parts = pathName.replace(/^\/desk\/?/, "").split("/").filter(Boolean).map((part) => decodeURIComponent(part));
    await page.evaluate((routeParts) => frappe.set_route.apply(frappe, routeParts), parts);
    await page.waitForURL((current) => current.pathname === pathName, { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  } else {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  }
  if (/\/login(?:[/?#]|$)/.test(page.url())) throw new Error(`Route ${route} redirected to login`);
  await page.waitForFunction(() => Boolean(window.frappe), null, { timeout: TIMEOUT });
}

async function waitForManagedForm(page) {
  await page.waitForSelector(".erpw-managed-pr-page .erpw-managed-pr-card", { state: "visible", timeout: TIMEOUT });
}

async function assertStableManagedForm(page, label) {
  await waitForManagedForm(page);
  const state = await page.evaluate(() => {
    const visiblePages = Array.from(document.querySelectorAll(".erpw-managed-pr-page")).filter((node) => {
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
    });
    const pageEl = visiblePages[0] || null;
    const shell = pageEl ? pageEl.querySelector(".erpw-managed-pr-shell") : null;
    const actionDetails = pageEl ? Array.from(pageEl.querySelectorAll(".erpw-child-toolbar-action")).map((button) => {
      const rect = button.getBoundingClientRect();
      const style = window.getComputedStyle(button);
      return {
        text: button.textContent.trim(),
        className: button.className || "",
        backgroundImage: style.backgroundImage,
        borderColor: style.borderColor,
        color: style.color,
        visible: rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden",
      };
    }) : [];
    const actionButtons = actionDetails.map((button) => button.text);
    const removeRects = pageEl ? Array.from(pageEl.querySelectorAll(".erpw-managed-pr-row-button")).map((button) => {
      const rect = button.getBoundingClientRect();
      const style = window.getComputedStyle(button);
      return {
        text: button.textContent.trim(),
        left: Math.round(rect.left),
        right: Math.round(rect.right),
        width: Math.round(rect.width),
        visible: rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden",
      };
    }) : [];
    const uomDisplays = pageEl ? Array.from(pageEl.querySelectorAll("[data-uom-display]")).map((node) => {
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return {
        text: node.textContent.trim(),
        width: Math.round(rect.width),
        right: Math.round(rect.right),
        scrollWidth: node.scrollWidth,
        clientWidth: node.clientWidth,
        visible: rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden",
        whiteSpace: style.whiteSpace,
        letterSpacing: style.letterSpacing,
        overflow: style.overflow,
        textOverflow: style.textOverflow,
      };
    }) : [];
    const itemHeaderRows = pageEl ? Array.from(pageEl.querySelectorAll(".erpw-managed-pr-table thead tr")).filter((node) => {
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
    }) : [];
    const repeatedRowLabels = pageEl ? Array.from(pageEl.querySelectorAll(".erpw-managed-pr-table td[data-label]")).filter((node) => {
      const before = window.getComputedStyle(node, "::before");
      const content = String(before.content || "").replace(/^"|"$/g, "");
      return before.display !== "none" && content.trim().length > 0;
    }).length : 0;
    const rowCount = pageEl ? pageEl.querySelectorAll(".erpw-managed-pr-table tbody tr[data-row-index]").length : 0;
    const tableWrap = pageEl ? pageEl.querySelector(".erpw-managed-pr-table-wrap") : null;
    const tableWrapRect = tableWrap ? tableWrap.getBoundingClientRect() : null;
    const summary = pageEl ? pageEl.querySelector(".erpw-child-summary") : null;
    const summaryRect = summary ? summary.getBoundingClientRect() : null;
    const companyInput = pageEl ? pageEl.querySelector('[data-field="company"]') : null;
    const companyInputRect = companyInput ? companyInput.getBoundingClientRect() : null;
    const companyInputStyle = companyInput ? window.getComputedStyle(companyInput) : null;
    const companyContext = pageEl ? pageEl.querySelector(".erpw-managed-pr-context-card") : null;
    const companyContextRect = companyContext ? companyContext.getBoundingClientRect() : null;
    const summaryFacts = pageEl ? pageEl.querySelector(".erpw-child-summary-facts") : null;
    const summaryFactsRect = summaryFacts ? summaryFacts.getBoundingClientRect() : null;
    const card = pageEl ? pageEl.querySelector(".erpw-managed-pr-card") : null;
    const summaryStyle = summary ? window.getComputedStyle(summary) : null;
    const cardStyle = card ? window.getComputedStyle(card) : null;
    const formLabels = pageEl ? Array.from(pageEl.querySelectorAll(".erpw-managed-pr-field label")).map((node) => node.textContent.trim()) : [];
    const rowLabels = pageEl ? Array.from(pageEl.querySelectorAll(".erpw-managed-pr-table td[data-label]")).map((node) => node.getAttribute("data-label") || "") : [];
    const helperCount = pageEl ? (pageEl.innerText.match(/New item lines use the default date unless changed\./g) || []).length : 0;
    const bodyWidth = Math.ceil(Math.max(document.body.scrollWidth, document.documentElement.scrollWidth));
    const viewportWidth = Math.ceil(window.innerWidth);
    return {
      url: location.pathname,
      shellCount: document.querySelectorAll(".erpw-managed-pr-page").length,
      visibleShellCount: visiblePages.length,
      duplicateHeads: document.querySelectorAll(".page-head").length,
      hasForm: Boolean(shell && pageEl && pageEl.querySelector(".erpw-managed-pr-card")),
      actionButtons,
      actionDetails,
      formLabels,
      rowLabels,
      helperCount,
      summaryBackgroundImage: summaryStyle ? summaryStyle.backgroundImage : "",
      cardBackgroundImage: cardStyle ? cardStyle.backgroundImage : "",
      bodyWidth,
      viewportWidth,
      documentWidth: Math.ceil(document.documentElement.scrollWidth),
      summaryHeight: summaryRect ? Math.round(summaryRect.height) : null,
      tableWrapRight: tableWrapRect ? Math.round(tableWrapRect.right) : null,
      tableWrapWidth: tableWrapRect ? Math.round(tableWrapRect.width) : null,
      removeRects,
      uomDisplays,
      itemHeaderCount: itemHeaderRows.length,
      repeatedRowLabels,
      rowCount,
      companyContextVisible: Boolean(companyContextRect && companyContextRect.width > 0 && companyContextRect.height > 0),
      companyInputVisible: Boolean(companyInputRect && companyInputRect.width > 0 && companyInputRect.height > 0 && companyInputStyle && companyInputStyle.display !== "none" && companyInputStyle.visibility !== "hidden"),
      summaryFactsVisible: Boolean(summaryFactsRect && summaryFactsRect.width > 0 && summaryFactsRect.height > 0 && summaryFacts && summaryFacts.children.length === 0),
      duplicateDraftHeadings: pageEl ? (pageEl.innerText.match(/Purchase Request Draft/g) || []).length : 0,
      phase5aTextCount: pageEl ? (pageEl.innerText.match(/Phase 5A/g) || []).length : 0,
      companyTextCount: pageEl ? (pageEl.innerText.match(/\bCompany\b|Mingalar Mobile Distribution Co\., Ltd\./g) || []).length : 0,
      openErpBeforeSave: actionButtons.filter((label) => /Open ERP Form/i.test(label)).length,
      saveDraftTextCount: pageEl ? (pageEl.innerText.match(/Save Draft/g) || []).length : 0,
      draftWordCount: pageEl ? (pageEl.innerText.match(/\bDraft\b/g) || []).length : 0,
      newRequestCount: pageEl ? (pageEl.innerText.match(/New Request/g) || []).length : 0,
      text: pageEl ? pageEl.innerText : document.body.innerText,
    };
  });
  assert(state.hasForm, `${label}: managed PR form did not render`, state);
  assert(state.shellCount === 1 && state.visibleShellCount === 1, `${label}: managed PR form shell stacked`, state);
  assert(state.bodyWidth <= state.viewportWidth + 2, `${label}: horizontal body overflow`, state);
  assert((state.summaryHeight || 0) > 0 && state.summaryHeight <= 95, `${label}: managed PR header still has an oversized empty band`, state);
  assert(!state.summaryFactsVisible, `${label}: empty summary fact band is visible`, state);
  assert(state.duplicateDraftHeadings === 0, `${label}: duplicate Purchase Request Draft copy visible`, state);
  assert(state.phase5aTextCount === 0, `${label}: Phase 5A implementation copy is visible`, state);
  assert(state.companyTextCount === 0, `${label}: company context still consumes visible form space`, state);
  assert(state.saveDraftTextCount === 0, `${label}: Save Draft wording is still visible`, state);
  assert(state.draftWordCount === 0, `${label}: Draft wording is still visible in the productized managed PR flow`, state);
  assert(state.newRequestCount > 0, `${label}: New Request status is not visible`, state);
  assert(state.actionButtons.includes("Save Request"), `${label}: Save Request action missing`, state);
  const saveAction = state.actionDetails.find((button) => button.text === "Save Request");
  const secondaryPrimaryActions = state.actionDetails.filter((button) => button.text !== "Save Request" && /\bprimary\b/.test(button.className || ""));
  assert(saveAction && /\bprimary\b/.test(saveAction.className || ""), `${label}: Save Request does not use the shared primary action style`, state);
  assert(!secondaryPrimaryActions.length, `${label}: secondary actions are styled as primary`, { secondaryPrimaryActions, state });
  assert(state.formLabels.includes("Default Required By"), `${label}: Default Required By header label missing`, state);
  assert(state.rowLabels.includes("Line Required By"), `${label}: Line Required By row label missing`, state);
  assert(state.helperCount === 1, `${label}: default-date helper copy must appear once`, state);
  assert(!/gradient/i.test(state.summaryBackgroundImage || "") && !/gradient/i.test(state.cardBackgroundImage || ""), `${label}: managed PR header/card uses a non-standard gradient`, state);
  assert(!state.companyContextVisible, `${label}: company context metadata should be omitted from the main form`, state);
  assert(!state.companyInputVisible, `${label}: company still renders as editable-looking form input`, state);
  assert(state.openErpBeforeSave === 0, `${label}: Open ERP Form must not appear before a managed Purchase Request draft is saved`, state);
  assert(state.removeRects.some((rect) => rect.visible && /Remove/i.test(rect.text)), `${label}: Remove line action is not visible`, state);
  assert(state.removeRects.every((rect) => !rect.visible || rect.right <= state.viewportWidth + 1), `${label}: Remove line action clips past viewport`, state);
  assert(state.itemHeaderCount === 1, `${label}: item lines should have one desktop header row`, state);
  assert(state.repeatedRowLabels === 0, `${label}: item row labels repeat at desktop/tablet width`, state);
  assert(state.uomDisplays.some((display) => display.visible && display.text === "Derived"), `${label}: Derived UOM placeholder missing`, state);
  assert(state.uomDisplays.every((display) => !display.visible || (display.scrollWidth <= display.clientWidth + 1 && display.whiteSpace === "nowrap" && display.letterSpacing === "normal" && display.overflow === "visible" && display.textOverflow === "clip" && !/Derl|Derlv|Derive\s+d/i.test(display.text || ""))), `${label}: Derived UOM display is clipped, wrapped, or awkwardly spaced`, state);
  assert(!state.tableWrapRight || state.tableWrapRight <= state.viewportWidth + 1, `${label}: line-entry area clips past viewport`, state);
  assert(!FORBIDDEN_ACTION_RE.test(state.actionButtons.join(" ")), `${label}: forbidden action visible`, state);
  assert(!/\/desk\/Form\/Material Request\/new/i.test(page.url()), `${label}: native Material Request create route opened`, state);
  return state;
}

async function assertManagedFormFocusStable(page, label) {
  const before = await page.evaluate(() => {
    const shell = document.querySelector(".erpw-managed-pr-page .erpw-managed-pr-shell");
    return {
      bodyWidth: Math.ceil(Math.max(document.body.scrollWidth, document.documentElement.scrollWidth)),
      shellWidth: shell ? Math.round(shell.getBoundingClientRect().width) : 0,
    };
  });
  await page.locator(".erpw-managed-pr-page .item-link").first().focus();
  await page.waitForTimeout(125);
  const after = await page.evaluate(() => {
    const shell = document.querySelector(".erpw-managed-pr-page .erpw-managed-pr-shell");
    return {
      bodyWidth: Math.ceil(Math.max(document.body.scrollWidth, document.documentElement.scrollWidth)),
      shellWidth: shell ? Math.round(shell.getBoundingClientRect().width) : 0,
    };
  });
  assert(Math.abs(after.bodyWidth - before.bodyWidth) <= 1 && Math.abs(after.shellWidth - before.shellWidth) <= 1, `${label}: focus changed managed PR layout width`, { before, after });
}

async function getFixtureValues(page) {
  const values = await page.evaluate(async () => {
    const itemResult = await frappe.call({ method: "frappe.client.get_list", args: { doctype: "Item", filters: { is_purchase_item: 1, disabled: 0 }, fields: ["name", "item_name", "stock_uom"], limit_page_length: 1 } });
    const warehouseResult = await frappe.call({ method: "frappe.client.get_list", args: { doctype: "Warehouse", filters: { disabled: 0 }, fields: ["name"], limit_page_length: 1 } }).catch(() => ({ message: [] }));
    const item = (itemResult.message || [])[0] || null;
    const warehouse = (warehouseResult.message || [])[0] || null;
    return { item, warehouse };
  });
  assert(values.item && values.item.name, "No purchase item available for managed PR smoke", values);
  return values;
}

async function chooseAutocomplete(page, selector, value) {
  const input = page.locator(selector).first();
  await input.fill("");
  await input.type(String(value).slice(0, Math.min(6, String(value).length)));
  const suggestion = page.locator(".erpw-managed-pr-suggestion").first();
  await suggestion.waitFor({ state: "visible", timeout: TIMEOUT });
  await suggestion.click();
}

async function fillAndSaveDraft(page, userKey) {
  const { item, warehouse } = await getFixtureValues(page);
  const defaultDate = "2026-05-20";
  const changedDefaultDate = "2026-05-24";
  const manualLineDate = "2026-05-22";
  await page.locator('[data-field="transaction_date"]').fill("2026-05-13");
  await page.locator('[data-field="schedule_date"]').fill(defaultDate);
  let dateState = await page.evaluate(() => Array.from(document.querySelectorAll('.erpw-managed-pr-page [data-row-field="schedule_date"]')).map((input) => input.value));
  assert(dateState[0] === defaultDate, "Managed PR first inherited line did not update from Default Required By", { dateState, defaultDate });
  await page.locator('[data-add-row]').click();
  dateState = await page.evaluate(() => Array.from(document.querySelectorAll('.erpw-managed-pr-page [data-row-field="schedule_date"]')).map((input) => input.value));
  assert(dateState[0] === defaultDate && dateState[1] === defaultDate, "Managed PR new line did not inherit the current default date", { dateState, defaultDate });
  await page.locator('.erpw-managed-pr-page [data-row-field="schedule_date"]').nth(1).fill(manualLineDate);
  await page.locator('[data-field="schedule_date"]').fill(changedDefaultDate);
  dateState = await page.evaluate(() => Array.from(document.querySelectorAll('.erpw-managed-pr-page [data-row-field="schedule_date"]')).map((input) => input.value));
  assert(dateState[0] === changedDefaultDate && dateState[1] === manualLineDate, "Managed PR default date update did not preserve manual line date", { dateState, changedDefaultDate, manualLineDate });
  await page.locator('[data-add-row]').click();
  dateState = await page.evaluate(() => Array.from(document.querySelectorAll('.erpw-managed-pr-page [data-row-field="schedule_date"]')).map((input) => input.value));
  assert(dateState[0] === changedDefaultDate && dateState[1] === manualLineDate && dateState[2] === changedDefaultDate, "Managed PR third line did not inherit changed default date", { dateState, changedDefaultDate, manualLineDate });
  await capture(page, `${userKey}-managed-pr-three-lines-1136x768`);
  await page.locator('[data-remove-row="2"]').click();
  await page.locator('[data-remove-row="1"]').click();
  await chooseAutocomplete(page, ".item-link", item.name);
  await page.locator('[data-row-field="qty"]').first().fill("1");
  if (warehouse && warehouse.name) {
    await chooseAutocomplete(page, ".warehouse-link", warehouse.name);
  }
  await page.waitForFunction(() => {
    const uom = document.querySelector('[data-row-field="uom"]');
    return uom && String(uom.value || "").trim().length > 0;
  }, null, { timeout: TIMEOUT }).catch(() => {});
  await page.locator("button:has-text('Save Request')").click();
  await page.waitForFunction(() => /procurement-console-purchase-request-form\/(?!new$)[^/]+$/.test(location.pathname), null, { timeout: TIMEOUT });
  await waitForManagedForm(page);
  await capture(page, `${userKey}-managed-pr-saved`);
  const state = await page.evaluate(() => {
    const shell = document.querySelector(".erpw-managed-pr-page");
    const actionDetails = Array.from(shell ? shell.querySelectorAll(".erpw-child-toolbar-action") : document.querySelectorAll(".erpw-child-toolbar-action")).map((button) => ({ text: button.textContent.trim(), className: button.className || "" }));
    return {
      url: location.pathname,
      actions: actionDetails.map((button) => button.text),
      actionDetails,
      message: document.querySelector("[data-managed-pr-message]") ? document.querySelector("[data-managed-pr-message]").textContent.trim() : "",
      text: shell ? shell.innerText : document.body.innerText,
    };
  });
  assert(/procurement-console-purchase-request-form\/(?!new$)/.test(state.url), "Save Request did not move to a saved managed PR route", state);
  assert(/Request Recorded/.test(state.text || ""), "Request Recorded status missing after save", state);
  assert(!/Save Draft|Saved Draft|\bDraft\b/.test(state.text || ""), "Draft wording visible after save", state);
  assert(!state.actions.some((label) => /Open ERP Form/i.test(label)), "Open ERP Form must not appear after a managed Purchase Request draft is saved", state);
  assert(state.actions.some((label) => /Review Request/i.test(label)), "Review Request action missing after save", state);
  assert(state.actionDetails.every((button) => !/Review Request|Back to Purchase Requests|Reset/i.test(button.text) || !/\bprimary\b/.test(button.className || "")), "Saved managed PR secondary actions must not use primary style", state);
}

async function verifyOverviewAction(page, user) {
  await openDeskRoute(page, "/desk/procurement-console");
  await page.waitForSelector('[data-section-key="create-actions"]', { state: "visible", timeout: TIMEOUT });
  await capture(page, `${user.key}-overview-before-new-pr`);
  await page.locator('[data-erpw-procurement-create-action="new_purchase_request"]').click();
  await page.waitForURL(/procurement-console-purchase-request-form\/new$/, { timeout: TIMEOUT });
  await assertStableManagedForm(page, `${user.label} overview New Purchase Request`);
  await capture(page, `${user.key}-managed-pr-new-overview`);
}

async function verifyDirectoryAction(page, user) {
  await openDeskRoute(page, "/desk/procurement-console-worklist/purchase-request-directory");
  await page.waitForSelector(".erpw-list-shell", { state: "visible", timeout: TIMEOUT });
  await capture(page, `${user.key}-purchase-requests-before-new-pr`);
  const createButton = page.locator("button:has-text('New Purchase Request')").first();
  await createButton.waitFor({ state: "visible", timeout: TIMEOUT });
  const createClass = await createButton.evaluate((button) => button.className || "");
  assert(/\bcreate\b/.test(createClass), `${user.label}: New Purchase Request does not use the shared create action style`, { createClass });
  assert(!/\bnavigation\b/.test(createClass), `${user.label}: New Purchase Request is styled as secondary navigation instead of create action`, { createClass });
  await createButton.click();
  await page.waitForURL(/procurement-console-purchase-request-form\/new$/, { timeout: TIMEOUT });
  await assertStableManagedForm(page, `${user.label} directory New Purchase Request`);
  await capture(page, `${user.key}-managed-pr-new-directory`);
}


async function verifyAutocompleteOverlay(page, user) {
  await page.setViewportSize({ width: 1136, height: 768 });
  await openDeskRoute(page, "/desk/procurement-console-purchase-request-form/new");
  await assertStableManagedForm(page, `${user.label} autocomplete base`);
  const before = await page.evaluate(() => ({
    bodyWidth: Math.ceil(Math.max(document.body.scrollWidth, document.documentElement.scrollWidth)),
    shellHeight: Math.round(document.querySelector(".erpw-managed-pr-shell").getBoundingClientRect().height),
  }));
  const input = page.locator(".erpw-managed-pr-page .item-link").first();
  await input.fill("");
  await input.type("a");
  await page.locator(".erpw-managed-pr-suggestion").first().waitFor({ state: "visible", timeout: TIMEOUT });
  await page.waitForTimeout(150);
  await capture(page, `${user.key}-managed-pr-item-autocomplete-1136x768`);
  const state = await page.evaluate(() => {
    const rect = (el) => {
      if (!el) return null;
      const r = el.getBoundingClientRect();
      const style = getComputedStyle(el);
      return {
        left: Math.round(r.left),
        top: Math.round(r.top),
        right: Math.round(r.right),
        bottom: Math.round(r.bottom),
        width: Math.round(r.width),
        height: Math.round(r.height),
        position: style.position,
        zIndex: style.zIndex,
        display: style.display,
        visibility: style.visibility,
      };
    };
    const menu = document.querySelector(".erpw-managed-pr-suggestions");
    const itemInput = document.querySelector(".erpw-managed-pr-page .item-link");
    const shell = document.querySelector(".erpw-managed-pr-shell");
    const toolbar = document.querySelector(".erpw-child-actions-toolbar");
    const header = document.querySelector(".erpw-child-summary");
    const menuRect = menu ? menu.getBoundingClientRect() : null;
    const inputRect = itemInput ? itemInput.getBoundingClientRect() : null;
    const toolbarRect = toolbar ? toolbar.getBoundingClientRect() : null;
    const headerRect = header ? header.getBoundingClientRect() : null;
    const overlaps = (a, b) => Boolean(a && b && a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top);
    const menuStyle = menu ? getComputedStyle(menu) : null;
    return {
      bodyWidth: Math.ceil(Math.max(document.body.scrollWidth, document.documentElement.scrollWidth)),
      viewportWidth: window.innerWidth,
      viewportHeight: window.innerHeight,
      shellHeight: shell ? Math.round(shell.getBoundingClientRect().height) : 0,
      menu: rect(menu),
      input: rect(itemInput),
      belowSpace: inputRect ? Math.round(window.innerHeight - inputRect.bottom - 16) : null,
      maxHeight: menuStyle ? menuStyle.maxHeight : null,
      overflowY: menuStyle ? menuStyle.overflowY : null,
      overlapsToolbar: overlaps(menuRect, toolbarRect),
      overlapsHeader: overlaps(menuRect, headerRect),
      suggestionCount: document.querySelectorAll(".erpw-managed-pr-suggestion").length,
      menuParent: menu && menu.parentElement ? menu.parentElement.tagName : null,
      topElementClass: menu ? (document.elementFromPoint(menu.getBoundingClientRect().left + 12, menu.getBoundingClientRect().top + 12) || {}).className || "" : "",
    };
  });
  assert(state.suggestionCount > 0, `${user.label}: item autocomplete returned no suggestions`, state);
  assert(state.menu && state.menu.position === "fixed", `${user.label}: item autocomplete is not using a floating overlay`, state);
  assert(Number(state.menu.zIndex || 0) >= 1000, `${user.label}: item autocomplete z-index is too low`, state);
  assert(state.menuParent === "BODY", `${user.label}: item autocomplete is still trapped inside the form DOM`, state);
  assert(state.menu.left >= state.input.left - 2 && ((state.menu.top >= state.input.bottom && state.belowSpace >= 56) || state.belowSpace < 56), `${user.label}: item autocomplete should prefer below-field placement when usable space exists`, state);
  assert(state.menu.width >= state.input.width, `${user.label}: item autocomplete is narrower than input`, state);
  assert(!state.overlapsToolbar && !state.overlapsHeader, `${user.label}: item autocomplete overlaps header or action toolbar`, state);
  assert(state.suggestionCount < 5 || (/auto|scroll/i.test(state.overflowY || "") && parseFloat(state.maxHeight) <= 240), `${user.label}: item autocomplete is not capped and scrollable`, state);
  assert(state.menu.right <= state.viewportWidth + 1 && state.menu.bottom <= state.viewportHeight + 1, `${user.label}: item autocomplete clips outside viewport`, state);
  assert(state.bodyWidth <= state.viewportWidth + 2, `${user.label}: item autocomplete caused horizontal overflow`, state);
  assert(Math.abs(state.bodyWidth - before.bodyWidth) <= 1 && Math.abs(state.shellHeight - before.shellHeight) <= 1, `${user.label}: item autocomplete caused layout shift`, { before, state });
  await page.locator(".erpw-managed-pr-suggestion").first().click();
}

async function verifyResponsive(page, user) {
  const sizes = [
    { width: 1136, height: 768 },
    { width: 1240, height: 768 },
    { width: 1440, height: 900 },
  ];
  for (const size of sizes) {
    await page.setViewportSize(size);
    await openDeskRoute(page, "/desk/procurement-console-purchase-request-form/new");
    const state = await assertStableManagedForm(page, `${user.label} ${size.width}x${size.height}`);
    await capture(page, `${user.key}-managed-pr-${size.width}x${size.height}`);
    assert(state.actionButtons.includes("Save Request"), "Save Request action missing at responsive size", state);
    await assertManagedFormFocusStable(page, `${user.label} ${size.width}x${size.height}`);
    if (size.width === 1136 || size.width === 1440) {
      await page.locator('[data-add-row]').click();
      await page.locator('[data-add-row]').click();
      const multiState = await assertStableManagedForm(page, `${user.label} ${size.width}x${size.height} three item lines`);
      assert(multiState.rowCount >= 3, `${user.label}: managed PR three-line layout did not render at least three rows`, multiState);
      await capture(page, `${user.key}-managed-pr-three-lines-${size.width}x${size.height}`);
    }
    if (size.width === 1136) await verifyAutocompleteOverlay(page, user);
  }
}

async function runForUser(user) {
  const browser = await chromium.launch({ headless: process.env.ERPW_HEADLESS !== "0" });
  const page = await browser.newPage({ viewport: { width: 1240, height: 768 } });
  const errors = [];
  const failedResponses = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("response", (response) => {
    if (response.status() >= 400) failedResponses.push({ url: response.url(), status: response.status() });
  });
  try {
    await login(page, user);
    await verifyOverviewAction(page, user);
    await verifyDirectoryAction(page, user);
    await fillAndSaveDraft(page, user.key);
    await verifyResponsive(page, user);
    assert(!errors.length, `${user.label}: page JS errors`, { errors });
    assert(!failedResponses.filter((item) => !/socket.io|hot-update/.test(item.url)).length, `${user.label}: failed network responses`, { failedResponses });
  } finally {
    await browser.close();
  }
}

(async () => {
  assert(USERS.length > 0, "No Purchase Manager/User credentials were provided through env vars");
  for (const user of USERS) {
    await runForUser(user);
  }
  console.log(JSON.stringify({ status: "passed", users: USERS.map((user) => user.key), artifactDir: ARTIFACT_DIR }, null, 2));
})().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  if (error && error.details) console.error(JSON.stringify(error.details, null, 2));
  process.exit(1);
});
