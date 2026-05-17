const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const TIMEOUT = Number(process.env.ERPW_PROCUREMENT_SMOKE_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_PROCUREMENT_PHASE5B_ARTIFACT_DIR || path.join(__dirname, "artifacts", "procurement-phase5b");
fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

const USERS = [
  { key: "manager", label: "Purchase Manager", username: process.env.ERPW_MANAGER_USERNAME, password: process.env.ERPW_MANAGER_PASSWORD },
  { key: "user", label: "Purchase User", username: process.env.ERPW_USER_USERNAME, password: process.env.ERPW_USER_PASSWORD },
].filter((user) => user.username && user.password);

const FORBIDDEN_ACTION_RE = /(submit|send email|email supplier|supplier portal|create supplier quotation|create purchase order|purchase order|supplier quotation|item price|default supplier|set default supplier|receive|bill|pay|payment|invoice|phase 5b)/i;

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

async function waitForManagedRfq(page) {
  await page.waitForSelector(".erpw-managed-rfq-page .erpw-managed-rfq-card", { state: "visible", timeout: TIMEOUT });
}

async function stableRfqSnapshot(page, label) {
  await waitForManagedRfq(page);
  const state = await page.evaluate(() => {
    const visible = (node) => {
      if (!node) return false;
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
    };
    const shells = Array.from(document.querySelectorAll(".erpw-managed-rfq-page")).filter(visible);
    const shell = shells[0] || null;
    const actionDetails = shell ? Array.from(shell.querySelectorAll(".erpw-child-toolbar-action")).filter(visible).map((button) => {
      const style = window.getComputedStyle(button);
      return {
        text: button.textContent.trim(),
        className: button.className || "",
        backgroundImage: style.backgroundImage,
        borderColor: style.borderColor,
        color: style.color,
      };
    }) : [];
    const buttons = actionDetails.map((button) => button.text);
    const removeRects = shell ? Array.from(shell.querySelectorAll(".erpw-managed-rfq-row-button")).map((button) => {
      const rect = button.getBoundingClientRect();
      return { text: button.textContent.trim(), right: Math.round(rect.right), visible: visible(button) };
    }) : [];
    const uomDisplays = shell ? Array.from(shell.querySelectorAll("[data-uom-display]")).map((node) => {
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return {
        text: node.textContent.trim(),
        width: Math.round(rect.width),
        right: Math.round(rect.right),
        scrollWidth: node.scrollWidth,
        clientWidth: node.clientWidth,
        visible: visible(node),
        whiteSpace: style.whiteSpace,
        overflow: style.overflow,
        textOverflow: style.textOverflow,
      };
    }) : [];
    const summary = shell ? shell.querySelector(".erpw-child-summary") : null;
    const card = shell ? shell.querySelector(".erpw-managed-rfq-card") : null;
    const summaryStyle = summary ? window.getComputedStyle(summary) : null;
    const cardStyle = card ? window.getComputedStyle(card) : null;
    const formLabels = shell ? Array.from(shell.querySelectorAll(".erpw-managed-rfq-field label")).map((node) => node.textContent.trim()) : [];
    const rowLabels = shell ? Array.from(shell.querySelectorAll(".erpw-managed-rfq-table td[data-label]")).map((node) => node.getAttribute("data-label") || "") : [];
    const helperCount = shell ? (shell.innerText.match(/New item lines use the default date unless changed\./g) || []).length : 0;
    const itemHeaderRows = shell ? Array.from(shell.querySelectorAll(".erpw-managed-rfq-table thead tr")).filter((node) => {
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
    }) : [];
    const repeatedRowLabels = shell ? Array.from(shell.querySelectorAll(".erpw-managed-rfq-table td[data-label]")).filter((node) => {
      const before = window.getComputedStyle(node, "::before");
      const content = String(before.content || "").replace(/^"|"$/g, "");
      return before.display !== "none" && content.trim().length > 0;
    }).length : 0;
    const rowCount = shell ? shell.querySelectorAll(".erpw-managed-rfq-table tbody tr[data-row-index]").length : 0;
    const bodyWidth = Math.ceil(Math.max(document.body.scrollWidth, document.documentElement.scrollWidth));
    const viewportWidth = Math.ceil(window.innerWidth);
    const text = shell ? shell.innerText : document.body.innerText;
    const shellRect = shell ? shell.getBoundingClientRect() : null;
    const pageHeadTexts = Array.from(document.querySelectorAll(".page-head")).filter(visible).map((node) => (node.innerText || "").replace(/\s+/g, " ").trim());
    const rfqFormTextHits = [];
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      const value = String(walker.currentNode.nodeValue || "").replace(/\s+/g, " ").trim();
      if (!/RFQ Form/i.test(value)) continue;
      const parent = walker.currentNode.parentElement;
      if (!visible(parent)) continue;
      const rect = parent.getBoundingClientRect();
      rfqFormTextHits.push({
        text: value,
        top: Math.round(rect.top),
        left: Math.round(rect.left),
        insideShell: shell ? shell.contains(parent) : false,
        belowShell: shellRect ? rect.top > shellRect.bottom + 2 : false,
      });
    }
    return {
      url: location.pathname,
      shellCount: document.querySelectorAll(".erpw-managed-rfq-page").length,
      visibleShellCount: shells.length,
      pageHeadTexts,
      rfqFormTextHits,
      bodyWidth,
      viewportWidth,
      buttons,
      actionDetails,
      formLabels,
      rowLabels,
      helperCount,
      summaryBackgroundImage: summaryStyle ? summaryStyle.backgroundImage : "",
      cardBackgroundImage: cardStyle ? cardStyle.backgroundImage : "",
      removeRects,
      itemHeaderCount: itemHeaderRows.length,
      repeatedRowLabels,
      rowCount,
      uomDisplays,
      hasCompanyField: Boolean(shell && shell.querySelector('[data-field="company"]')),
      text,
    };
  });
  assert(state.visibleShellCount === 1 && state.shellCount === 1, `${label}: managed RFQ shell stacked`, state);
  assert(!state.pageHeadTexts.some((value) => /RFQ Form/i.test(value)), `${label}: duplicate RFQ Form page header is visible`, state);
  assert(!state.rfqFormTextHits.some((hit) => !hit.insideShell || hit.belowShell), `${label}: stale RFQ Form chrome visible outside managed form`, state);
  assert(state.bodyWidth <= state.viewportWidth + 2, `${label}: horizontal overflow`, state);
  assert(state.buttons.includes("Save RFQ"), `${label}: Save RFQ action missing`, state);
  const saveAction = state.actionDetails.find((button) => button.text === "Save RFQ");
  const secondaryPrimaryActions = state.actionDetails.filter((button) => button.text !== "Save RFQ" && /\bprimary\b/.test(button.className || ""));
  assert(saveAction && /\bprimary\b/.test(saveAction.className || ""), `${label}: Save RFQ does not use the shared primary action style`, state);
  assert(!secondaryPrimaryActions.length, `${label}: secondary actions are styled as primary`, { secondaryPrimaryActions, state });
  assert(state.formLabels.includes("Default Required By"), `${label}: Default Required By header label missing`, state);
  assert(state.rowLabels.includes("Line Required By"), `${label}: Line Required By row label missing`, state);
  assert(state.helperCount === 1, `${label}: default-date helper copy must appear once`, state);
  assert(!/gradient/i.test(state.summaryBackgroundImage || "") && !/gradient/i.test(state.cardBackgroundImage || ""), `${label}: managed RFQ header/card uses a non-standard gradient`, state);
  assert(!state.buttons.some((label) => /Open ERP Form/i.test(label)) || !/\/new$/.test(state.url), `${label}: Open ERP Form appeared before save`, state);
  assert(!state.hasCompanyField, `${label}: company field should not render in managed RFQ UI`, state);
  assert(!/\bDraft\b|Phase 5B/i.test(state.text || ""), `${label}: technical draft or phase text visible`, state);
  assert(!FORBIDDEN_ACTION_RE.test(state.buttons.join(" ")), `${label}: forbidden RFQ action visible`, state);
  assert(state.removeRects.every((rect) => !rect.visible || rect.right <= state.viewportWidth + 1), `${label}: remove action clips past viewport`, state);
  assert(state.itemHeaderCount === 1, `${label}: item lines should have one desktop header row`, state);
  assert(state.repeatedRowLabels === 0, `${label}: item row labels repeat at desktop/tablet width`, state);
  assert(state.uomDisplays.some((display) => display.visible && display.text === "Derived"), `${label}: Derived UOM placeholder missing`, state);
  assert(state.uomDisplays.every((display) => !display.visible || (display.right <= state.viewportWidth + 1 && display.width >= 62 && display.scrollWidth <= display.clientWidth + 1 && display.whiteSpace === "nowrap" && display.overflow === "visible" && display.textOverflow === "clip")), `${label}: Derived UOM display is clipped or wrapping`, state);
  assert(!/\/desk\/(?:request-for-quotation|Form\/Request%20for%20Quotation|Form\/Request for Quotation)\//i.test(page.url()), `${label}: native RFQ route leaked`, state);
  return state;
}

async function assertFocusStable(page, label) {
  const before = await page.evaluate(() => Math.ceil(Math.max(document.body.scrollWidth, document.documentElement.scrollWidth)));
  await page.locator(".erpw-managed-rfq-page .supplier-link").first().focus();
  await page.waitForTimeout(125);
  const after = await page.evaluate(() => Math.ceil(Math.max(document.body.scrollWidth, document.documentElement.scrollWidth)));
  assert(Math.abs(after - before) <= 1, `${label}: focus changed body width`, { before, after });
}

async function getFixtureValues(page) {
  const values = await page.evaluate(async () => {
    const supplierResult = await frappe.call({ method: "frappe.client.get_list", args: { doctype: "Supplier", fields: ["name", "supplier_name"], limit_page_length: 1 } });
    const itemResult = await frappe.call({ method: "frappe.client.get_list", args: { doctype: "Item", filters: { is_purchase_item: 1, disabled: 0 }, fields: ["name", "item_name", "stock_uom"], limit_page_length: 1 } });
    const warehouseResult = await frappe.call({ method: "frappe.client.get_list", args: { doctype: "Warehouse", filters: { disabled: 0 }, fields: ["name"], limit_page_length: 1 } }).catch(() => ({ message: [] }));
    return { supplier: (supplierResult.message || [])[0] || null, item: (itemResult.message || [])[0] || null, warehouse: (warehouseResult.message || [])[0] || null };
  });
  assert(values.supplier && values.supplier.name, "No supplier available for managed RFQ smoke", values);
  assert(values.item && values.item.name, "No purchase item available for managed RFQ smoke", values);
  return values;
}

async function chooseAutocomplete(page, selector, value, screenshotName) {
  const input = page.locator(selector).first();
  const bodyWidthBefore = await page.evaluate(() => Math.ceil(Math.max(document.body.scrollWidth, document.documentElement.scrollWidth)));
  await input.fill("");
  await input.type(String(value).slice(0, Math.min(6, String(value).length)));
  const suggestion = page.locator(".erpw-managed-rfq-suggestion").first();
  await suggestion.waitFor({ state: "visible", timeout: TIMEOUT });
  if (screenshotName) {
    const overlay = await suggestion.evaluate((node) => {
      const menu = node.closest(".erpw-managed-rfq-suggestions") || node;
      const rect = menu.getBoundingClientRect();
      const style = window.getComputedStyle(menu);
      const inputRect = document.activeElement ? document.activeElement.getBoundingClientRect() : null;
      const fieldRects = ["supplier-link", "item-link", "warehouse-link"].map((className) => {
        const field = document.querySelector(`.${className}`);
        if (!field) return null;
        const fieldRect = field.getBoundingClientRect();
        const centerX = fieldRect.left + fieldRect.width / 2;
        const centerY = fieldRect.top + fieldRect.height / 2;
        const overlayCenterX = rect.left + rect.width / 2;
        const overlayCenterY = rect.top + rect.height / 2;
        return {
          key: className.replace("-link", ""),
          top: Math.round(fieldRect.top),
          left: Math.round(fieldRect.left),
          right: Math.round(fieldRect.right),
          bottom: Math.round(fieldRect.bottom),
          width: Math.round(fieldRect.width),
          distance: Math.round(Math.sqrt(Math.pow(overlayCenterX - centerX, 2) + Math.pow(overlayCenterY - centerY, 2))),
        };
      }).filter(Boolean);
      return {
        top: Math.round(rect.top),
        left: Math.round(rect.left),
        right: Math.round(rect.right),
        bottom: Math.round(rect.bottom),
        width: Math.round(rect.width),
        zIndex: Number(style.zIndex) || 0,
        position: style.position,
        viewportWidth: Math.ceil(window.innerWidth),
        viewportHeight: Math.ceil(window.innerHeight),
        parentIsBody: menu.parentElement === document.body,
        inputTop: inputRect ? Math.round(inputRect.top) : null,
        inputLeft: inputRect ? Math.round(inputRect.left) : null,
        inputRight: inputRect ? Math.round(inputRect.right) : null,
        inputBottom: inputRect ? Math.round(inputRect.bottom) : null,
        verticalGap: inputRect ? Math.round(rect.top - inputRect.bottom) : null,
        leftDelta: inputRect ? Math.round(rect.left - inputRect.left) : null,
        nearestField: fieldRects.sort((a, b) => a.distance - b.distance)[0] || null,
        visible: rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden",
      };
    });
    const bodyWidthAfter = await page.evaluate(() => Math.ceil(Math.max(document.body.scrollWidth, document.documentElement.scrollWidth)));
    assert(overlay.visible, `${screenshotName}: autocomplete overlay hidden`, overlay);
    assert(overlay.left >= 0 && overlay.right <= overlay.viewportWidth + 2, `${screenshotName}: autocomplete overlay clipped horizontally`, overlay);
    assert(overlay.top >= 0 && overlay.bottom <= overlay.viewportHeight + 2, `${screenshotName}: autocomplete overlay clipped vertically`, overlay);
    const expectedField = selector.includes("supplier") ? "supplier" : selector.includes("warehouse") ? "warehouse" : "item";
    assert(overlay.parentIsBody && overlay.position === "fixed" && overlay.zIndex >= 1000, `${screenshotName}: autocomplete overlay trapped inside form layer`, overlay);
    assert(Math.abs(overlay.leftDelta) <= 2 && overlay.verticalGap >= 4 && overlay.verticalGap <= 12, `${screenshotName}: autocomplete overlay is detached from active input`, overlay);
    assert(overlay.nearestField && overlay.nearestField.key === expectedField, `${screenshotName}: autocomplete overlay is closer to another field`, { expectedField, overlay });
    assert(Math.abs(bodyWidthAfter - bodyWidthBefore) <= 1, `${screenshotName}: autocomplete changed body width`, { bodyWidthBefore, bodyWidthAfter, overlay });
    await capture(page, screenshotName);
  }
  await suggestion.click();
}

async function verifyAutocompleteGeometry(page, userKey, width, height) {
  await page.setViewportSize({ width, height });
  await openDeskRoute(page, "/desk/procurement-console-rfq-form/new");
  await waitForManagedRfq(page);
  const { supplier, item, warehouse } = await getFixtureValues(page);
  await page.locator('[data-field="transaction_date"]').fill("2026-05-14");
  await page.locator('[data-field="schedule_date"]').fill("2026-05-21");
  await chooseAutocomplete(page, ".supplier-link", supplier.name, `${userKey}-supplier-autocomplete-${width}x${height}`);
  await chooseAutocomplete(page, ".item-link", item.name, `${userKey}-item-autocomplete-${width}x${height}`);
  await page.locator('[data-row-field="qty"]').first().fill("1");
  await page.locator('[data-row-field="schedule_date"]').first().fill("2026-05-21");
  if (warehouse && warehouse.name) await chooseAutocomplete(page, ".warehouse-link", warehouse.name, `${userKey}-warehouse-autocomplete-${width}x${height}`);
}

async function fillAndSaveRfq(page, userKey) {
  const { supplier, item, warehouse } = await getFixtureValues(page);
  const defaultDate = "2026-05-21";
  const changedDefaultDate = "2026-05-25";
  const manualLineDate = "2026-05-23";
  await page.locator('[data-field="transaction_date"]').fill("2026-05-14");
  await page.locator('[data-field="schedule_date"]').fill(defaultDate);
  let dateState = await page.evaluate(() => Array.from(document.querySelectorAll('.erpw-managed-rfq-page [data-row-field="schedule_date"]')).map((input) => input.value));
  assert(dateState[0] === defaultDate, "Managed RFQ first inherited line did not update from Default Required By", { dateState, defaultDate });
  await chooseAutocomplete(page, ".supplier-link", supplier.name, `${userKey}-supplier-autocomplete-1136`);
  await page.locator('[data-add-row]').click();
  dateState = await page.evaluate(() => Array.from(document.querySelectorAll('.erpw-managed-rfq-page [data-row-field="schedule_date"]')).map((input) => input.value));
  assert(dateState[0] === defaultDate && dateState[1] === defaultDate, "Managed RFQ new line did not inherit the current default date", { dateState, defaultDate });
  await page.locator('.erpw-managed-rfq-page [data-row-field="schedule_date"]').nth(1).fill(manualLineDate);
  await page.locator('[data-field="schedule_date"]').fill(changedDefaultDate);
  dateState = await page.evaluate(() => Array.from(document.querySelectorAll('.erpw-managed-rfq-page [data-row-field="schedule_date"]')).map((input) => input.value));
  assert(dateState[0] === changedDefaultDate && dateState[1] === manualLineDate, "Managed RFQ default date update did not preserve manual line date", { dateState, changedDefaultDate, manualLineDate });
  await page.locator('[data-add-row]').click();
  dateState = await page.evaluate(() => Array.from(document.querySelectorAll('.erpw-managed-rfq-page [data-row-field="schedule_date"]')).map((input) => input.value));
  assert(dateState[0] === changedDefaultDate && dateState[1] === manualLineDate && dateState[2] === changedDefaultDate, "Managed RFQ third line did not inherit changed default date", { dateState, changedDefaultDate, manualLineDate });
  await capture(page, `${userKey}-managed-rfq-three-lines-1136x768`);
  await page.locator('[data-remove-row="2"]').click();
  await page.locator('[data-remove-row="1"]').click();
  await chooseAutocomplete(page, ".item-link", item.name, `${userKey}-item-autocomplete-1136`);
  await page.locator('[data-row-field="qty"]').first().fill("1");
  if (warehouse && warehouse.name) await chooseAutocomplete(page, ".warehouse-link", warehouse.name, `${userKey}-warehouse-autocomplete-1136`);
  await page.locator("button:has-text('Save RFQ')").click();
  await page.waitForFunction(() => /procurement-console-rfq-form\/(?!new$)[^/]+$/.test(location.pathname), null, { timeout: TIMEOUT });
  await waitForManagedRfq(page);
  await capture(page, `${userKey}-managed-rfq-saved`);
  const saved = await page.evaluate(() => {
    const shell = document.querySelector(".erpw-managed-rfq-page");
    const actionDetails = Array.from(shell ? shell.querySelectorAll(".erpw-child-toolbar-action") : []).map((button) => ({ text: button.textContent.trim(), className: button.className || "" }));
    return { url: location.pathname, text: shell ? shell.innerText : document.body.innerText, actions: actionDetails.map((button) => button.text), actionDetails };
  });
  assert(/RFQ Recorded/.test(saved.text || ""), "RFQ Recorded status missing after save", saved);
  assert(!saved.actions.some((label) => /Open ERP Form/i.test(label)), "Open ERP Form must not appear after a managed RFQ is saved", saved);
  assert(saved.actions.some((label) => /Review RFQ/i.test(label)), "Review RFQ action missing after save", saved);
  assert(saved.actionDetails.every((button) => !/Review RFQ|Back to RFQs|Reset/i.test(button.text) || !/\bprimary\b/.test(button.className || "")), "Saved managed RFQ secondary actions must not use primary style", saved);
  assert(!/Submit|Send Email|Supplier Portal|Create Supplier Quotation|Create Purchase Order/i.test(saved.text || ""), "Forbidden RFQ action text visible after save", saved);
}

async function verifyOverviewAction(page, user) {
  await openDeskRoute(page, "/desk/procurement-console");
  await page.waitForSelector('[data-section-key="create-actions"]', { state: "visible", timeout: TIMEOUT });
  await page.locator('[data-erpw-procurement-create-action="new_rfq"]').click();
  await page.waitForURL(/procurement-console-rfq-form\/new$/, { timeout: TIMEOUT });
  await stableRfqSnapshot(page, `${user.label} overview New RFQ`);
  await capture(page, `${user.key}-managed-rfq-new-overview`);
  return page.url().replace(/[#?].*$/, "");
}

async function verifyDirectoryAction(page, user, expectedUrl) {
  await openDeskRoute(page, "/desk/procurement-console-worklist/rfq-directory");
  await page.waitForSelector(".erpw-list-shell", { state: "visible", timeout: TIMEOUT });
  await capture(page, `${user.key}-rfq-directory-new-rfq`);
  for (let attempt = 1; attempt <= 2; attempt += 1) {
    await page.locator("button:has-text('New RFQ')").first().click();
    await page.waitForURL(/procurement-console-rfq-form\/new$/, { timeout: TIMEOUT });
    await stableRfqSnapshot(page, `${user.label} RFQ Directory New RFQ repeat ${attempt}`);
    await capture(page, `${user.key}-managed-rfq-directory-repeat-${attempt}`);
    const actualUrl = page.url().replace(/[#?].*$/, "");
    assert(actualUrl === expectedUrl, "Overview and RFQ Directory must route to the same managed RFQ form", { expectedUrl, actualUrl, attempt });
    await page.locator("button:has-text('Back to RFQs')").first().click();
    await page.waitForURL(/procurement-console-worklist\/rfq-directory$/, { timeout: TIMEOUT });
    await page.waitForSelector(".erpw-list-shell", { state: "visible", timeout: TIMEOUT });
  }
  await page.locator("button:has-text('New RFQ')").first().click();
  await page.waitForURL(/procurement-console-rfq-form\/new$/, { timeout: TIMEOUT });
  await stableRfqSnapshot(page, `${user.label} RFQ Directory New RFQ final`);
}

async function verifyNoPrConversion(page, user) {
  const reviewName = process.env.ERPW_PROCUREMENT_DIRECT_PR_NAME || "MAT-MR-2026-00021";
  await openDeskRoute(page, `/desk/procurement-console-purchase-request-review/${encodeURIComponent(reviewName)}`);
  await page.waitForTimeout(600);
  const text = await page.evaluate(() => document.body.innerText || "");
  assert(!/\bCreate RFQ\b/i.test(text), `${user.label}: draft/internal Purchase Request exposed active Create RFQ`, { reviewName, text: text.slice(0, 1000) });
}

async function runForViewport(page, user, width, height) {
  await page.setViewportSize({ width, height });
  await openDeskRoute(page, "/desk/procurement-console-rfq-form/new");
  const state = await stableRfqSnapshot(page, `${user.label} managed RFQ ${width}x${height}`);
  await assertFocusStable(page, `${user.label} managed RFQ ${width}x${height}`);
  await capture(page, `${user.key}-managed-rfq-new-${width}x${height}`);
  if (width === 1136 || width === 1440) {
    await page.locator('[data-add-row]').click();
    await page.locator('[data-add-row]').click();
    const multiState = await stableRfqSnapshot(page, `${user.label} managed RFQ ${width}x${height} three item lines`);
    assert(multiState.rowCount >= 3, `${user.label}: managed RFQ three-line layout did not render at least three rows`, multiState);
    await capture(page, `${user.key}-managed-rfq-three-lines-${width}x${height}`);
  }
  return state;
}

async function runUser(browser, user) {
  const context = await browser.newContext({ baseURL: BASE_URL, ignoreHTTPSErrors: true, viewport: { width: 1136, height: 768 } });
  const page = await context.newPage();
  const errors = [];
  page.on("dialog", (dialog) => dialog.accept().catch(() => {}));
  page.on("pageerror", (error) => errors.push(error.message));
  try {
    await login(page, user);
    const report = { user: user.key, layouts: [] };
    for (const [width, height] of [[1136, 768], [1240, 768], [1440, 900]]) {
      report.layouts.push(await runForViewport(page, user, width, height));
    }
    await page.setViewportSize({ width: 1136, height: 768 });
    const overviewUrl = await verifyOverviewAction(page, user);
    await verifyDirectoryAction(page, user, overviewUrl);
    for (const [width, height] of [[1136, 768], [1240, 768], [1440, 900]]) {
      await verifyAutocompleteGeometry(page, user.key, width, height);
    }
    await page.setViewportSize({ width: 1136, height: 768 });
    await openDeskRoute(page, "/desk/procurement-console-rfq-form/new");
    await fillAndSaveRfq(page, user.key);
    await verifyNoPrConversion(page, user);
    assert(errors.length === 0, `${user.label}: page JS error`, { errors });
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
    for (const user of USERS) reports.push(await runUser(browser, user));
    console.log(JSON.stringify({ ok: true, baseUrl: BASE_URL, artifactDir: ARTIFACT_DIR, reports }, null, 2));
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error.stack || error.message);
  if (error.details) console.error(JSON.stringify(error.details, null, 2));
  process.exit(1);
});
