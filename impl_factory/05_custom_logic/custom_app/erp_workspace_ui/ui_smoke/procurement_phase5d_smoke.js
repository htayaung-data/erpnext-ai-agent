const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.ERPW_BASE_URL || "https://meet.erpbosai.com";
const TIMEOUT = Number(process.env.ERPW_PROCUREMENT_SMOKE_TIMEOUT || 60000);
const ARTIFACT_DIR = process.env.ERPW_PROCUREMENT_PHASE5D_ARTIFACT_DIR || path.join(__dirname, "artifacts", "procurement-phase5d");
fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

const USERS = [
  { key: "manager", label: "Purchase Manager", username: process.env.ERPW_MANAGER_USERNAME, password: process.env.ERPW_MANAGER_PASSWORD },
  { key: "user", label: "Purchase User", username: process.env.ERPW_USER_USERNAME, password: process.env.ERPW_USER_PASSWORD },
].filter((user) => user.username && user.password);

const FORBIDDEN_ACTION_RE = /(submit|approve|reject|purchase receipt|create receipt|purchase invoice|create invoice|item price|default supplier|set default supplier|receive|bill|pay|payment|invoice|cancel|stop|phase 5d)/i;

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

async function waitForManagedPo(page) {
  await page.waitForSelector(".erpw-managed-po-page .erpw-managed-po-card", { state: "visible", timeout: TIMEOUT });
}

async function openFreshManagedPo(page) {
  await page.goto(routeUrl("/desk/procurement-console-purchase-order-form/new"), { waitUntil: "domcontentloaded", timeout: TIMEOUT });
  if (/\/login(?:[/?#]|$)/.test(page.url())) throw new Error("Managed Purchase Order new route redirected to login");
  await page.waitForFunction(() => Boolean(window.frappe), null, { timeout: TIMEOUT });
  await waitForManagedPo(page);
  const rowCount = await page.locator(".erpw-managed-po-table tbody tr[data-row-index]").count();
  assert(rowCount === 1, "Fresh managed Purchase Order form did not reset to one item row", { rowCount, url: page.url() });
}

async function stablePoSnapshot(page, label) {
  await waitForManagedPo(page);
  const state = await page.evaluate((snapshotLabel) => {
    const visible = (node) => {
      if (!node) return false;
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
    };
    const shells = Array.from(document.querySelectorAll(".erpw-managed-po-page")).filter(visible);
    const shell = shells[0] || null;
    const actionDetails = shell ? Array.from(shell.querySelectorAll(".erpw-child-toolbar-action")).filter(visible).map((button) => ({
      text: (button.textContent || "").replace(/\s+/g, " ").trim(),
      className: button.className || "",
    })) : [];
    const buttons = actionDetails.map((button) => button.text);
    const summary = shell ? shell.querySelector(".erpw-child-summary") : null;
    const card = shell ? shell.querySelector(".erpw-managed-po-card") : null;
    const summaryStyle = summary ? window.getComputedStyle(summary) : null;
    const cardStyle = card ? window.getComputedStyle(card) : null;
    const bodyWidth = Math.ceil(Math.max(document.body.scrollWidth, document.documentElement.scrollWidth));
    const viewportWidth = Math.ceil(window.innerWidth);
    const itemHeaderRows = shell ? Array.from(shell.querySelectorAll(".erpw-managed-po-table thead tr")).filter(visible) : [];
    const headerCells = shell ? Array.from(shell.querySelectorAll(".erpw-managed-po-table thead th")).filter(visible).map((node) => {
      const rect = node.getBoundingClientRect();
      return {
        text: (node.textContent || "").replace(/\s+/g, " ").trim(),
        top: Math.round(rect.top),
        left: Math.round(rect.left),
        right: Math.round(rect.right),
        width: Math.round(rect.width),
      };
    }) : [];
    const headerPairs = [];
    for (let index = 1; index < headerCells.length; index += 1) {
      const previous = headerCells[index - 1];
      const current = headerCells[index];
      if (Math.abs((current.top || 0) - (previous.top || 0)) > 2) continue;
      headerPairs.push({
        leftText: previous.text,
        rightText: current.text,
        gap: current.left - previous.right,
      });
    }
    const repeatedRowLabels = shell ? Array.from(shell.querySelectorAll(".erpw-managed-po-table td[data-label]")).filter((node) => {
      const before = window.getComputedStyle(node, "::before");
      const content = String(before.content || "").replace(/^"|"$/g, "");
      return content && content !== "none";
    }).length : 0;
    const uomDisplays = shell ? Array.from(shell.querySelectorAll("[data-uom-display]")).map((node) => {
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return {
        text: (node.textContent || "").trim(),
        visible: visible(node),
        width: Math.round(rect.width),
        right: Math.round(rect.right),
        scrollWidth: node.scrollWidth,
        clientWidth: node.clientWidth,
        whiteSpace: style.whiteSpace,
        overflow: style.overflow,
        textOverflow: style.textOverflow,
      };
    }) : [];
    const amountDisplays = shell ? Array.from(shell.querySelectorAll("[data-amount-display]")).map((node) => (node.textContent || "").trim()) : [];
    const removeRects = shell ? Array.from(shell.querySelectorAll(".erpw-managed-po-row-button")).map((button) => {
      const rect = button.getBoundingClientRect();
      return { text: button.textContent.trim(), right: Math.round(rect.right), visible: visible(button) };
    }) : [];
    const pageHeadTexts = Array.from(document.querySelectorAll(".page-head")).filter(visible).map((node) => (node.textContent || "").replace(/\s+/g, " ").trim());
    return {
      label: snapshotLabel,
      url: location.pathname,
      text: shell ? shell.innerText : document.body.innerText,
      visibleShellCount: shells.length,
      shellCount: document.querySelectorAll(".erpw-managed-po-page").length,
      pageHeadTexts,
      buttons,
      actionDetails,
      bodyWidth,
      viewportWidth,
      summaryBackgroundImage: summaryStyle ? summaryStyle.backgroundImage : "",
      cardBackgroundImage: cardStyle ? cardStyle.backgroundImage : "",
      itemHeaderCount: itemHeaderRows.length,
      headerCells,
      headerPairs,
      repeatedRowLabels,
      rowCount: shell ? shell.querySelectorAll(".erpw-managed-po-table tbody tr[data-row-index]").length : 0,
      hasCompanyField: shell ? Array.from(shell.querySelectorAll("label")).some((labelNode) => /company/i.test(labelNode.textContent || "")) : false,
      uomDisplays,
      amountDisplays,
      removeRects,
    };
  }, label);
  assert(state.visibleShellCount === 1 && state.shellCount === 1, `${label}: managed Purchase Order shell stacked`, state);
  assert(!state.pageHeadTexts.some((value) => /Purchase Order Form/i.test(value)), `${label}: duplicate Purchase Order Form page header is visible`, state);
  assert(state.bodyWidth <= state.viewportWidth + 2, `${label}: horizontal overflow`, state);
  assert(state.buttons.includes("Save Purchase Order"), `${label}: Save Purchase Order action missing`, state);
  const saveAction = state.actionDetails.find((button) => button.text === "Save Purchase Order");
  const secondaryPrimaryActions = state.actionDetails.filter((button) => button.text !== "Save Purchase Order" && /\bprimary\b/.test(button.className || ""));
  assert(saveAction && /\bprimary\b/.test(saveAction.className || ""), `${label}: Save Purchase Order does not use shared primary action style`, state);
  assert(!secondaryPrimaryActions.length, `${label}: secondary actions are styled as primary`, { secondaryPrimaryActions, state });
  assert(!/gradient/i.test(state.summaryBackgroundImage || "") && !/gradient/i.test(state.cardBackgroundImage || ""), `${label}: managed Purchase Order header/card uses a non-standard gradient`, state);
  assert(!state.buttons.some((button) => /Open ERP Form/i.test(button)) || !/\/new$/.test(state.url), `${label}: Open ERP Form appeared before save`, state);
  assert(!state.hasCompanyField, `${label}: company field should not render in managed Purchase Order UI`, state);
  assert(!/\bDraft\b|Phase 5D/i.test(state.text || ""), `${label}: technical draft or phase text visible`, state);
  assert(!FORBIDDEN_ACTION_RE.test(state.buttons.join(" ")), `${label}: forbidden Purchase Order action visible`, state);
  assert(state.removeRects.every((rect) => !rect.visible || rect.right <= state.viewportWidth + 1), `${label}: remove action clips past viewport`, state);
  assert(state.itemHeaderCount === 1, `${label}: item lines should have one desktop/tablet header row`, state);
  assert(state.headerPairs.every((pair) => pair.gap >= 8), `${label}: item-line header labels collide or are too close`, state);
  assert(state.repeatedRowLabels === 0, `${label}: item row labels repeat at desktop/tablet width`, state);
  assert(state.uomDisplays.some((display) => display.visible && display.text === "Derived"), `${label}: Derived UOM placeholder missing`, state);
  assert(state.uomDisplays.every((display) => !display.visible || (display.right <= state.viewportWidth + 1 && display.width >= 62 && display.scrollWidth <= display.clientWidth + 1 && display.whiteSpace === "nowrap" && display.overflow === "visible" && display.textOverflow === "clip")), `${label}: Derived UOM display is clipped or wrapping`, state);
  assert(!/\/desk\/(?:purchase-order|Form\/Purchase%20Order|Form\/Purchase Order)\//i.test(page.url()), `${label}: native Purchase Order route leaked`, state);
  return state;
}

async function getFixtureValues(page) {
  const values = await page.evaluate(async () => {
    const supplierResult = await frappe.call({ method: "frappe.client.get_list", args: { doctype: "Supplier", fields: ["name", "supplier_name"], limit_page_length: 1 } });
    const itemResult = await frappe.call({ method: "frappe.client.get_list", args: { doctype: "Item", filters: { is_purchase_item: 1, disabled: 0 }, fields: ["name", "item_name", "stock_uom"], limit_page_length: 1 } });
    const warehouseResult = await frappe.call({ method: "frappe.client.get_list", args: { doctype: "Warehouse", fields: ["name", "warehouse_name"], limit_page_length: 1 } });
    return { supplier: (supplierResult.message || [])[0] || null, item: (itemResult.message || [])[0] || null, warehouse: (warehouseResult.message || [])[0] || null };
  });
  assert(values.supplier && values.supplier.name, "No supplier available for managed Purchase Order smoke", values);
  assert(values.item && values.item.name, "No purchase item available for managed Purchase Order smoke", values);
  assert(values.warehouse && values.warehouse.name, "No warehouse available for managed Purchase Order smoke", values);
  return values;
}

async function chooseAutocomplete(page, selector, value, screenshotName) {
  const input = page.locator(selector).first();
  const bodyWidthBefore = await page.evaluate(() => Math.ceil(Math.max(document.body.scrollWidth, document.documentElement.scrollWidth)));
  await input.fill("");
  await input.type(String(value).slice(0, Math.min(6, String(value).length)));
  const suggestion = page.locator(".erpw-managed-po-suggestion").first();
  await suggestion.waitFor({ state: "visible", timeout: TIMEOUT });
  if (screenshotName) {
    const overlay = await suggestion.evaluate((node) => {
      const menu = node.closest(".erpw-managed-po-suggestions") || node;
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
        inputBottom: inputRect ? Math.round(inputRect.bottom) : null,
        verticalGap: inputRect ? Math.round(rect.top - inputRect.bottom) : null,
        leftDelta: inputRect ? Math.round(rect.left - inputRect.left) : null,
        nearestField: fieldRects.sort((a, b) => a.distance - b.distance)[0] || null,
        visible: rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden",
      };
    });
    const bodyWidthAfter = await page.evaluate(() => Math.ceil(Math.max(document.body.scrollWidth, document.documentElement.scrollWidth)));
    const expectedField = selector.includes("supplier") ? "supplier" : selector.includes("warehouse") ? "warehouse" : "item";
    assert(overlay.visible, `${screenshotName}: autocomplete overlay hidden`, overlay);
    assert(overlay.left >= 0 && overlay.right <= overlay.viewportWidth + 2, `${screenshotName}: autocomplete overlay clipped horizontally`, overlay);
    assert(overlay.top >= 0 && overlay.bottom <= overlay.viewportHeight + 2, `${screenshotName}: autocomplete overlay clipped vertically`, overlay);
    assert(overlay.parentIsBody && overlay.position === "fixed" && overlay.zIndex >= 1000, `${screenshotName}: autocomplete overlay trapped inside form layer`, overlay);
    assert(Math.abs(overlay.leftDelta) <= 2 && overlay.verticalGap >= 4 && overlay.verticalGap <= 12, `${screenshotName}: autocomplete overlay is detached from active input`, overlay);
    assert(overlay.nearestField && overlay.nearestField.key === expectedField, `${screenshotName}: autocomplete overlay is closer to another field`, { expectedField, overlay });
    assert(Math.abs(bodyWidthAfter - bodyWidthBefore) <= 1, `${screenshotName}: autocomplete changed body width`, { bodyWidthBefore, bodyWidthAfter, overlay });
    await capture(page, screenshotName);
  }
  await suggestion.click();
}

async function verifyOverviewAction(page, user) {
  await openDeskRoute(page, "/desk/procurement-console");
  await page.waitForSelector('[data-section-key="create-actions"]', { state: "visible", timeout: TIMEOUT });
  await page.locator('[data-erpw-procurement-create-action="new_purchase_order"]').first().click();
  await page.waitForURL(/procurement-console-purchase-order-form\/new$/, { timeout: TIMEOUT });
  await stablePoSnapshot(page, `${user.label} overview New Purchase Order`);
  await capture(page, `${user.key}-managed-po-new-overview`);
  return page.url().replace(/[#?].*$/, "");
}

async function verifyDirectoryAction(page, user, expectedUrl) {
  for (let attempt = 1; attempt <= 2; attempt += 1) {
    await openDeskRoute(page, "/desk/procurement-console-worklist/purchase-order-directory");
    await page.waitForSelector(".erpw-list-shell", { state: "visible", timeout: TIMEOUT });
    await page.locator("button:has-text('New Purchase Order')").first().click();
    await page.waitForURL(/procurement-console-purchase-order-form\/new$/, { timeout: TIMEOUT });
    await stablePoSnapshot(page, `${user.label} Purchase Order Directory New Purchase Order repeat ${attempt}`);
    await capture(page, `${user.key}-managed-po-directory-repeat-${attempt}`);
    const actualUrl = page.url().replace(/[#?].*$/, "");
    assert(actualUrl === expectedUrl, "Overview and Purchase Orders Directory must route to the same managed Purchase Order form", { expectedUrl, actualUrl, attempt });
    await page.locator("button:has-text('Back to Purchase Orders')").first().click();
    await page.waitForURL(/procurement-console-worklist\/purchase-order-directory$/, { timeout: TIMEOUT });
  }
}

async function verifyNewLayout(page, userKey, width, height) {
  await page.setViewportSize({ width, height });
  await openFreshManagedPo(page);
  const state = await stablePoSnapshot(page, `managed Purchase Order ${width}x${height}`);
  await capture(page, `${userKey}-managed-po-new-${width}x${height}`);
  if (width === 1136 || width === 1440) {
    await page.locator("[data-add-row]").click();
    await page.locator("[data-add-row]").click();
    const multiState = await stablePoSnapshot(page, `managed Purchase Order ${width}x${height} three lines`);
    assert(multiState.rowCount >= 3, "Managed Purchase Order three-line layout did not render at least three rows", multiState);
    await capture(page, `${userKey}-managed-po-three-lines-${width}x${height}`);
  }
  return state;
}

async function verifyAutocompleteGeometry(page, userKey, width, height) {
  await page.setViewportSize({ width, height });
  await openFreshManagedPo(page);
  const { supplier, item, warehouse } = await getFixtureValues(page);
  await page.locator('[data-field="transaction_date"]').fill("2026-05-15");
  await page.locator('[data-field="schedule_date"]').fill("2026-06-15");
  await chooseAutocomplete(page, ".supplier-link", supplier.name, `${userKey}-supplier-autocomplete-${width}x${height}`);
  await chooseAutocomplete(page, ".item-link", item.name, `${userKey}-item-autocomplete-${width}x${height}`);
  await chooseAutocomplete(page, ".warehouse-link", warehouse.name, `${userKey}-warehouse-autocomplete-${width}x${height}`);
}

async function verifyDateInheritance(page, userKey) {
  await openFreshManagedPo(page);
  const firstDate = page.locator('[data-row-field="schedule_date"]').nth(0);
  await page.locator('[data-field="schedule_date"]').fill("2026-06-01");
  await firstDate.waitFor({ state: "visible", timeout: TIMEOUT });
  assert(await firstDate.inputValue() === "2026-06-01", "First inherited PO line did not adopt default required date", { value: await firstDate.inputValue() });
  await page.locator("[data-add-row]").click();
  const secondDate = page.locator('[data-row-field="schedule_date"]').nth(1);
  assert(await secondDate.inputValue() === "2026-06-01", "New PO line did not inherit current default required date", { value: await secondDate.inputValue() });
  await secondDate.fill("2026-06-05");
  await page.locator('[data-field="schedule_date"]').fill("2026-06-10");
  assert(await firstDate.inputValue() === "2026-06-10", "Inherited PO line did not update when default required date changed", { value: await firstDate.inputValue() });
  assert(await secondDate.inputValue() === "2026-06-05", "Manual PO line date was overwritten by default required date change", { value: await secondDate.inputValue() });
  await page.locator("[data-add-row]").click();
  const thirdDate = page.locator('[data-row-field="schedule_date"]').nth(2);
  assert(await thirdDate.inputValue() === "2026-06-10", "New PO line did not inherit updated default required date", { value: await thirdDate.inputValue() });
  const state = await stablePoSnapshot(page, `${userKey} Purchase Order date inheritance`);
  assert(state.rowCount >= 3, "Managed Purchase Order date inheritance should leave at least three lines", state);
  await capture(page, `${userKey}-managed-po-date-inheritance`);
}

async function fillAndSavePo(page, userKey) {
  const { supplier, item, warehouse } = await getFixtureValues(page);
  await openFreshManagedPo(page);
  await page.locator('[data-field="transaction_date"]').fill("2026-05-15");
  await page.locator('[data-field="schedule_date"]').fill("2026-06-15");
  await chooseAutocomplete(page, ".supplier-link", supplier.name, `${userKey}-supplier-autocomplete-save`);
  await page.locator("[data-add-row]").click();
  await page.locator("[data-add-row]").click();
  await capture(page, `${userKey}-managed-po-three-lines-before-save`);
  await page.locator('[data-remove-row="2"]').click();
  await page.locator('[data-remove-row="1"]').click();
  await chooseAutocomplete(page, ".item-link", item.name, `${userKey}-item-autocomplete-save`);
  await chooseAutocomplete(page, ".warehouse-link", warehouse.name, `${userKey}-warehouse-autocomplete-save`);
  await page.locator('[data-row-field="qty"]').first().fill("2");
  await page.locator('[data-row-field="rate"]').first().fill("100");
  const amount = await page.locator("[data-amount-display]").first().innerText();
  assert(/200\.00|200/.test(amount), "Purchase Order amount did not update from qty and rate", { amount });
  const uomText = await page.locator("[data-uom-display]").first().innerText();
  assert(uomText.trim() && uomText.trim() !== "Derived", "Purchase Order UOM did not update after item selection", { uomText });
  await page.locator("button:has-text('Save Purchase Order')").click();
  await page.waitForFunction(() => /procurement-console-purchase-order-form\/(?!new$)[^/]+$/.test(location.pathname), null, { timeout: TIMEOUT });
  await waitForManagedPo(page);
  await capture(page, `${userKey}-managed-po-saved`);
  const saved = await page.evaluate(() => {
    const shell = document.querySelector(".erpw-managed-po-page");
    const actionDetails = Array.from(shell ? shell.querySelectorAll(".erpw-child-toolbar-action") : []).map((button) => ({ text: button.textContent.trim(), className: button.className || "" }));
    return { url: location.pathname, text: shell ? shell.innerText : document.body.innerText, actions: actionDetails.map((button) => button.text), actionDetails };
  });
  assert(/Purchase Order Recorded/.test(saved.text || ""), "Purchase Order Recorded status missing after save", saved);
  assert(saved.actions.some((label) => /Open ERP Form/i.test(label)), "Open ERP Form should appear only after saved Purchase Order", saved);
  assert(saved.actions.some((label) => /Review Purchase Order/i.test(label)), "Review Purchase Order action missing after save", saved);
  assert(saved.actionDetails.every((button) => !/Open ERP Form|Review Purchase Order|Back to Purchase Orders|Reset/i.test(button.text) || !/\bprimary\b/.test(button.className || "")), "Saved managed Purchase Order secondary actions must not use primary style", saved);
  assert(!/Submit|Approve|Reject|Purchase Receipt|Create Receipt|Purchase Invoice|Create Invoice|Update Item Price|Set Default Supplier|Receive|Bill|Pay|Payment|Cancel|Stop/i.test(saved.text || ""), "Forbidden Purchase Order action text visible after save", saved);
  return saved;
}

async function runUser(browser, user) {
  const context = await browser.newContext({ baseURL: BASE_URL, ignoreHTTPSErrors: true, viewport: { width: 1136, height: 768 } });
  const page = await context.newPage();
  const errors = [];
  page.on("dialog", (dialog) => dialog.accept().catch(() => {}));
  page.on("pageerror", (error) => errors.push(error.message));
  try {
    await login(page, user);
    const overviewUrl = await verifyOverviewAction(page, user);
    await verifyDirectoryAction(page, user, overviewUrl);
    for (const [width, height] of [[1136, 768], [1240, 768], [1440, 900]]) {
      await verifyNewLayout(page, user.key, width, height);
      await verifyAutocompleteGeometry(page, user.key, width, height);
    }
    await page.setViewportSize({ width: 1136, height: 768 });
    await verifyDateInheritance(page, user.key);
    await page.setViewportSize({ width: 1136, height: 768 });
    const saved = await fillAndSavePo(page, user.key);
    assert(errors.length === 0, `${user.label}: page JS error`, { errors });
    return { user: user.key, saved };
  } finally {
    await context.close();
  }
}

(async () => {
  assert(USERS.length > 0, "No smoke users are available in environment variables");
  const browser = await chromium.launch({ headless: true });
  try {
    const results = [];
    for (const user of USERS) {
      results.push(await runUser(browser, user));
    }
    const summaryPath = path.join(ARTIFACT_DIR, "summary.json");
    fs.writeFileSync(summaryPath, JSON.stringify({ ok: true, results, artifactDir: ARTIFACT_DIR }, null, 2));
    console.log(JSON.stringify({ ok: true, artifactDir: ARTIFACT_DIR, summaryPath }, null, 2));
  } catch (error) {
    const summaryPath = path.join(ARTIFACT_DIR, "summary.json");
    fs.writeFileSync(summaryPath, JSON.stringify({ ok: false, message: error.message, details: error.details || {}, artifactDir: ARTIFACT_DIR }, null, 2));
    console.error(error);
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
})();
