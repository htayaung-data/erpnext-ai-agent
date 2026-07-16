"use strict";

const assert = require("assert");
const childProcess = require("child_process");
const fs = require("fs");
const path = require("path");

const appRoot = path.resolve(process.env.ERPW_APP_ROOT || path.join(__dirname, ".."));
const financePath = path.join(appRoot, "erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js");
const sidebarPath = path.join(appRoot, "erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js");
const registryPath = path.join(appRoot, "erp_workspace_ui/public/js/runtime/console/workspace_registry.js");
const source = fs.readFileSync(financePath, "utf8");
const sidebarSource = fs.readFileSync(sidebarPath, "utf8");
const registrySource = fs.readFileSync(registryPath, "utf8");
const styleMatch = source.match(/style\.textContent = `([\s\S]*?)`;\n\s*document\.head\.appendChild/);
assert(styleMatch, "Finance source CSS must be extractable for responsive smoke");
const sidebarStyleMatch = sidebarSource.match(/style\.textContent = `([\s\S]*?)`;\n\s*document\.head\.appendChild/);
assert(sidebarStyleMatch, "Shared sidebar CSS must be extractable for accessibility smoke");
const sidebarCss = sidebarStyleMatch[1].replace(/\$\{MANAGED_BODY_CLASS\}/g, "erpw-sales-console-sidebar-managed");

const HERO_SURFACE_COLORS = [
  "#172033", "#24434a", "#19322e",
  "#29313f", "#3b4654",
  "#263241", "#435160",
];

const EXPECTED_MANAGED_DETAIL_ACTIVE_KEYS = Object.freeze({
  procurement: Object.freeze({
    "procurement-console-po-follow-up": "purchase_order_directory",
    "procurement-console-supplier": "supplier_directory",
    "procurement-console-item": "buying_item_directory",
    "procurement-console-purchase-request-review": "purchase_request_directory",
    "procurement-console-purchase-request-form": "purchase_request_directory",
    "procurement-console-rfq-form": "rfq_directory",
    "procurement-console-rfq-review": "rfq_directory",
    "procurement-console-supplier-quotation-form": "supplier_quotation_directory",
    "procurement-console-purchase-order-form": "purchase_order_directory",
    "procurement-console-supplier-quotation-review": "supplier_quotation_directory",
  }),
  warehouse: Object.freeze({
    "warehouse-console-receiving": "inbound_receiving",
    "warehouse-console-picking": "outbound_picking",
    "warehouse-console-stock-exception": "stock_exceptions",
    "warehouse-console-stock-posture": "stock_exceptions",
    "warehouse-console-movement": "movement_visibility",
  }),
});

function hexToRgb(value) {
  const match = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(value);
  assert(match, `Expected a full hexadecimal color, received ${value}`);
  return match.slice(1).map((channel) => parseInt(channel, 16));
}

function cssRgb(value) {
  const match = /^rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$/i.exec(value);
  assert(match, `Expected a computed RGB color, received ${value}`);
  return match.slice(1).map(Number);
}

function relativeLuminance(rgb) {
  const channels = rgb.map((channel) => {
    const normalized = channel / 255;
    return normalized <= 0.04045
      ? normalized / 12.92
      : ((normalized + 0.055) / 1.055) ** 2.4;
  });
  return (0.2126 * channels[0]) + (0.7152 * channels[1]) + (0.0722 * channels[2]);
}

function contrastRatio(foreground, background) {
  const foregroundLuminance = relativeLuminance(foreground);
  const backgroundLuminance = relativeLuminance(background);
  return (Math.max(foregroundLuminance, backgroundLuminance) + 0.05)
    / (Math.min(foregroundLuminance, backgroundLuminance) + 0.05);
}

const titleRuleMatch = styleMatch[1].match(/\.finance-control-title\s*\{([\s\S]*?)\}/);
assert(titleRuleMatch, "Finance title rule must be present");
const titleColorMatch = titleRuleMatch[1].match(/color:\s*(#[0-9a-f]{6})\s*;/i);
assert(titleColorMatch, "Finance title must explicitly override Frappe's heading color");
const sourceTitleColor = hexToRgb(titleColorMatch[1]);
const sourceMinimumContrast = Math.min(...HERO_SURFACE_COLORS.map((color) => contrastRatio(sourceTitleColor, hexToRgb(color))));
assert(
  sourceMinimumContrast >= 4.5,
  `Finance source title contrast ${sourceMinimumContrast.toFixed(2)}:1 is below WCAG AA`,
);
const sidebarFocusColorMatch = sidebarCss.match(/\.erpw-sales-console-sidebar-header:focus-visible,[\s\S]*?box-shadow:\s*inset\s+0\s+0\s+0\s+3px\s+(#[0-9a-f]{6})\s*;/i);
assert(sidebarFocusColorMatch, "Shared sidebar focus indicator must be an explicit contained three-pixel treatment");
const sourceFocusContrast = contrastRatio(hexToRgb(sidebarFocusColorMatch[1]), hexToRgb("#ffffff"));
assert(sourceFocusContrast >= 3, `Shared sidebar focus contrast ${sourceFocusContrast.toFixed(2)}:1 is below WCAG non-text contrast`);
const searchInsetFocusMatch = sidebarCss.match(/\.erpw-sales-console-search-result:focus-visible\s*\{[\s\S]*?inset\s+0\s+0\s+0\s+3px\s+(#[0-9a-f]{6})/i);
assert(searchInsetFocusMatch, "Governed search result must use a contained three-pixel inset focus treatment");
const searchInsetContrast = contrastRatio(hexToRgb(searchInsetFocusMatch[1]), hexToRgb("#ffffff"));
assert(searchInsetContrast >= 3, `Governed search focus contrast ${searchInsetContrast.toFixed(2)}:1 is below WCAG non-text contrast`);

const card = (title, detail, value) => `
  <article class="finance-control-panel">
    <h2 class="finance-control-panel-title">${title}</h2>
    <p class="finance-control-panel-copy">${detail}</p>
    <div class="finance-control-chip-row"><span class="finance-control-chip">${value}</span></div>
  </article>`;

function shell(state) {
  const restricted = state === "restricted";
  const unavailable = state === "unavailable";
  const cards = (restricted || unavailable) ? "" : [
    card("Workspace readiness", "Finance Control Desk is active for read-only overview posture.", "Read-only"),
    card("Company scope", "Company-scoped read-only aggregate posture.", "Mingalar Mobile Distribution Co., Ltd."),
    card("Fiscal period posture", "Fiscal period posture remains deferred.", "Deferred"),
    card("Receivables posture", "Sales Invoice aggregate count buckets and manager-only Payment Ledger MMK amount buckets remain separate signals. No row-level identity is shown.", "Aggregate counts + MMK buckets"),
    card("Payables posture", "Payables counts remain unavailable when payment schedules cannot be interpreted safely.", "Unavailable"),
    card("Ledger posture", "Account balances and ledger rows remain blocked.", "Blocked"),
  ].join("");
  return `<!doctype html><html><head><meta charset="utf-8"><style>h1 { color: #171717; }</style><style>${styleMatch[1]}</style><style>${sidebarCss}</style></head><body class="erpw-sales-console-sidebar-managed">
    <aside class="body-sidebar" aria-label="Managed workspace navigation">
      <a class="erpw-sales-console-sidebar-header" href="#managed-home">PrimeAxis</a>
      <div class="erpw-sales-console-sidebar-shell">
        <button class="erpw-sales-console-sidebar-utility">Search</button>
        <button class="erpw-sales-console-sidebar-link is-active" aria-current="page">Overview</button>
      </div>
      <button class="collapse-sidebar-link">Collapse</button>
    </aside>
    <div class="erpw-sales-console-search-dialog">
      <div class="erpw-sales-console-search-bar"><input class="erpw-sales-console-search-input" aria-label="Workspace search"></div>
      <div class="erpw-sales-console-search-results">
        <div class="erpw-sales-console-search-group">
          <button class="erpw-sales-console-search-result is-active">Approved result</button>
        </div>
      </div>
    </div>
    <main class="finance-control-shell" data-finance-cycle1-overview="${state}">
      <section class="finance-control-hero ${restricted ? "is-restricted" : unavailable ? "is-unavailable" : ""}">
        <div class="finance-control-hero-top">
          <div><p class="finance-control-eyebrow">Finance &amp; Accounting</p><h1 class="finance-control-title">Finance Control Desk</h1>
          <p class="finance-control-summary">${restricted ? "Manager-only Finance posture is not shown for this role." : unavailable ? "The Finance overview is temporarily unavailable." : "Company-scoped aggregate posture only; no rows, reports, exports, or execution."}</p>
          <p class="finance-control-freshness">As of 2026-07-13 | Refreshed 2026-07-13 12:00:00</p></div>
          <div class="finance-control-actions"><span class="finance-control-status">${restricted ? "Restricted" : unavailable ? "Unavailable" : "Read-only overview"}</span><button class="finance-control-refresh">Refresh</button></div>
        </div>
        <div class="finance-control-chip-row"><span class="finance-control-chip">No row-level data shown</span><span class="finance-control-chip">Execution disabled</span></div>
      </section>
      <section class="finance-control-grid">${cards || card(unavailable ? "Controlled unavailable state" : "Finance access restricted", "No row-level financial data, metrics, reports, exports, or execution routes are returned or shown.", unavailable ? "Unavailable" : "Restricted")}</section>
    </main>
  </body></html>`;
}

async function verify(page, viewport, state) {
  await page.goto("about:blank");
  await page.setViewportSize(viewport);
  await page.setContent(shell(state), { waitUntil: "domcontentloaded" });
  const result = await page.evaluate(() => {
    const root = document.documentElement;
    const panels = Array.from(document.querySelectorAll(".finance-control-panel")).map((node) => node.getBoundingClientRect());
    const horizontalOverflow = root.scrollWidth - root.clientWidth;
    const outOfBounds = panels.some((box) => box.left < -0.5 || box.right > root.clientWidth + 0.5);
    const overlap = panels.some((box, index) => panels.slice(index + 1).some((other) => {
      const horizontal = box.left < other.right && box.right > other.left;
      const vertical = box.top < other.bottom && box.bottom > other.top;
      return horizontal && vertical;
    }));
    const title = document.querySelector(".finance-control-title");
    const titleColor = title ? window.getComputedStyle(title).color : "";
    return {
      horizontalOverflow, outOfBounds, overlap, panelCount: panels.length, titleColor,
    };
  });
  assert(result.panelCount > 0);
  assert(result.horizontalOverflow <= 1, `${state} layout overflowed by ${result.horizontalOverflow}px at ${viewport.width}px`);
  assert.strictEqual(result.outOfBounds, false, `${state} panel escaped viewport at ${viewport.width}px`);
  assert.strictEqual(result.overlap, false, `${state} panels overlapped at ${viewport.width}px`);
  const titleColor = cssRgb(result.titleColor);
  const minimumContrast = Math.min(...HERO_SURFACE_COLORS.map((color) => contrastRatio(titleColor, hexToRgb(color))));
  assert(
    minimumContrast >= 4.5,
    `${state} Finance title contrast ${minimumContrast.toFixed(2)}:1 is below WCAG AA at ${viewport.width}px`,
  );
  const focusTargets = [
    [".erpw-sales-console-sidebar-header", ".erpw-sales-console-sidebar-header"],
    [".erpw-sales-console-sidebar-utility", ".erpw-sales-console-sidebar-utility"],
    [".erpw-sales-console-sidebar-link", ".erpw-sales-console-sidebar-link"],
    [".collapse-sidebar-link", ".collapse-sidebar-link"],
    [".erpw-sales-console-search-input", ".erpw-sales-console-search-bar"],
    [".erpw-sales-console-search-result", ".erpw-sales-console-search-result"],
  ];
  for (const [focusSelector, indicatorSelector] of focusTargets) {
    await page.locator(focusSelector).focus();
    await page.waitForTimeout(180);
    const indicator = await page.locator(indicatorSelector).evaluate((node) => {
      const computed = window.getComputedStyle(node);
      const container = node.closest(".erpw-sales-console-search-results");
      const box = node.getBoundingClientRect();
      const containerBox = container ? container.getBoundingClientRect() : null;
      return {
        color: computed.outlineColor,
        style: computed.outlineStyle,
        width: computed.outlineWidth,
        boxShadow: computed.boxShadow,
        contained: !containerBox || (box.left >= containerBox.left && box.right <= containerBox.right),
      };
    });
    if (focusSelector === ".erpw-sales-console-search-result"
      || focusSelector === ".erpw-sales-console-sidebar-header"
      || focusSelector === ".erpw-sales-console-sidebar-utility"
      || focusSelector === ".erpw-sales-console-sidebar-link"
      || focusSelector === ".collapse-sidebar-link") {
      assert(indicator.boxShadow.includes("inset"), "governed result focus must be painted inside the result box");
      assert(
        indicator.boxShadow.includes("rgb(37, 99, 235)"),
        `${focusSelector} must use the shared focus color: ${indicator.boxShadow}`,
      );
      assert.strictEqual(indicator.contained, true, `${focusSelector} must remain inside its real overflow container`);
      continue;
    }
    assert.strictEqual(indicator.style, "solid", `${focusSelector} must expose a solid focus indicator`);
    assert.strictEqual(indicator.width, "3px", `${focusSelector} must expose a three-pixel focus indicator`);
    const focusContrast = contrastRatio(cssRgb(indicator.color), hexToRgb("#ffffff"));
    assert(focusContrast >= 3, `${focusSelector} focus contrast ${focusContrast.toFixed(2)}:1 is below 3:1 at ${viewport.width}px`);
  }
}

function loadFinanceFixtures() {
  const testsPath = path.join(appRoot, "erp_workspace_ui/tests").replace(/\\/g, "/");
  const script = `
import json, sys
from unittest.mock import patch
sys.path.insert(0, ${JSON.stringify(testsPath)})
import test_finance_accounting_shell as fixtures
from erp_workspace_ui.workspace_governance_manifest import ROUTE_MANIFEST
unavailable = fixtures._frontend_guard_payload({"state": "unavailable", "policy": {"reason": "accounts_manager_required"}})
with patch.object(fixtures.service.frappe, "get_roles", return_value=["Sales User"]):
    restricted = fixtures.service.get_finance_control_desk_overview_context()
with patch.object(fixtures.service.frappe, "get_roles", return_value=["Accounts Manager"]), patch.object(
    fixtures.service,
    "resolve_finance_role_company_scope",
    return_value=fixtures._resolver(
        state="unavailable",
        selected_company=None,
        reason="company_scope_temporarily_unavailable",
    ),
):
    overview_unavailable = fixtures.service.get_finance_control_desk_overview_context()
ready_zero = fixtures._frontend_guard_payload({"state": "ready"})
manager_ready = fixtures._frontend_coherent_receivables_amount_payload()
managed_detail_routes = [
    {"workspace_id": row["workspace_id"], "route_key": row["route_key"], "page_kind": row["page_kind"]}
    for row in ROUTE_MANIFEST
    if row["workspace_id"] in {"procurement", "warehouse"}
    and row["classification"] in {"productized_detail", "managed_create_edit"}
]
print(json.dumps({"unavailable": unavailable, "overview_unavailable": overview_unavailable, "restricted": restricted, "ready_zero": ready_zero, "manager_ready": manager_ready, "managed_detail_routes": managed_detail_routes}, separators=(",", ":")))
`;
  return JSON.parse(childProcess.execFileSync(process.env.PYTHON || "python3", ["-c", script], {
    cwd: appRoot,
    env: Object.assign({}, process.env, { PYTHONPATH: appRoot }),
    encoding: "utf8",
  }));
}

async function verifyActualSidebarRenderer(page, viewport, workspaceId, collapsed) {
  await page.goto("about:blank");
  await page.setViewportSize(viewport);
  const sidebarWidth = collapsed ? 72 : 260;
  const initialSidebarWidth = collapsed ? 260 : 72;
  await page.setContent(`<!doctype html><html><head><style>html,body{margin:0;max-width:100%}.body-sidebar{width:${sidebarWidth}px;max-width:100%;overflow:hidden}</style></head><body>
    <aside class="body-sidebar" aria-label="Managed workspace navigation" style="width:${initialSidebarWidth}px">
      <div class="body-sidebar-top"><div class="sidebar-items"></div></div>
      <div class="body-sidebar-bottom"><button class="collapse-sidebar-link">Collapse</button></div>
    </aside>
    <section id="actual-search-render"></section>
  </body></html>`, { waitUntil: "domcontentloaded" });
  await page.evaluate(() => {
    window.__managedRoute = [];
    window.__managedNavigations = [];
    window.frappe = {
      get_route() { return window.__managedRoute.slice(); },
      set_route(...parts) { window.__managedNavigations.push(parts.map(String)); },
      router: { on() {} },
      after_ajax(callback) { callback(); },
      call() { return Promise.resolve({ message: {} }); },
    };
    const sidebar = document.querySelector(".body-sidebar");
    const collapse = document.querySelector(".collapse-sidebar-link");
    collapse.addEventListener("click", () => {
      const isCollapsed = sidebar.getBoundingClientRect().width <= 80;
      sidebar.style.width = isCollapsed ? "260px" : "72px";
      collapse.setAttribute("aria-expanded", isCollapsed ? "true" : "false");
    });
  });
  await page.addScriptTag({ content: registrySource });
  await page.evaluate((id) => {
    window.__managedRoute = [window.erpWorkspaceUiWorkspaceRegistry.get(id).routes.home];
  }, workspaceId);
  await page.addScriptTag({ content: sidebarSource });
  await page.waitForFunction(() => document.body.classList.contains("erpw-sales-console-sidebar-managed")
    && window.erpWorkspaceConsoleSidebar && typeof window.erpWorkspaceConsoleSidebar.syncSidebarNow === "function");
  const toggledSidebar = await page.evaluate(() => {
    document.querySelector(".collapse-sidebar-link").click();
    const sidebar = document.querySelector(".body-sidebar");
    return {
      width: Math.round(sidebar.getBoundingClientRect().width),
      inlineWidth: sidebar.style.width,
    };
  });
  assert.strictEqual(
    toggledSidebar.width,
    sidebarWidth,
    `production sidebar collapse fixture resolved ${JSON.stringify(toggledSidebar)} instead of ${sidebarWidth}px`,
  );
  await page.evaluate(() => { window.module = { exports: {} }; });
  await page.addScriptTag({ content: sidebarSource });
  await page.evaluate(() => {
    window.__sidebarRenderer = window.module.exports;
    delete window.module;
  });
  const rendered = await page.evaluate(async (id) => {
    const workspace = window.erpWorkspaceUiWorkspaceRegistry.get(id);
    window.__managedRoute = [workspace.routes.home];
    document.body.classList.add("erpw-sales-console-sidebar-managed");
    const items = workspace.fallbackItems.map((item) => ({
      key: item.key,
      label: item.label,
      icon: item.icon,
      target: Object.assign({}, item.target),
    }));
    const payload = {
      schema_version: window.__sidebarRenderer.SIDEBAR_CONTEXT_SCHEMA_VERSION,
      workspace: { workspace_id: id, title: workspace.title },
      sidebar: {
        schema_version: window.__sidebarRenderer.SIDEBAR_CONTEXT_SCHEMA_VERSION,
        workspace_id: id,
        title: workspace.title,
        mode_label: workspace.modeLabel,
        scope_label: id === "finance" ? "Read-only overview" : "Representative permission scope",
        active_key: items[0].key,
        home_key: items[0].key,
        items,
        sections: [{ key: id === "finance" ? "workspace" : "primary", label: "Workspace", items }],
      },
    };
    const primed = window.erpWorkspaceConsoleSidebar.primePayload(payload);
    const sidebarReady = primed && await window.erpWorkspaceConsoleSidebar.syncSidebarNow();
    const nonHomeItem = items.slice(1).find((item) => item && item.target);
    let nonHomeRoute = null;
    let nonHomeActiveKey = "";
    if (nonHomeItem) {
      if (nonHomeItem.target.kind === "page") {
        nonHomeRoute = [nonHomeItem.target.route];
      } else if (nonHomeItem.target.kind === "worklist" && workspace.routes.worklist) {
        nonHomeRoute = [workspace.routes.worklist, String(nonHomeItem.target.queue_key || "").replace(/_/g, "-")];
      } else if (nonHomeItem.target.kind === "warehouse_page") {
        nonHomeRoute = [nonHomeItem.target.route].concat(nonHomeItem.target.route_parts || []);
      }
      if (nonHomeRoute && window.__sidebarRenderer.isManagedRoute(nonHomeRoute)) {
        window.__managedRoute = nonHomeRoute.slice();
        nonHomeActiveKey = window.__sidebarRenderer.resolveActiveKey(nonHomeRoute);
        await window.erpWorkspaceConsoleSidebar.syncSidebarNow();
      }
    }
    const searchHost = document.getElementById("actual-search-render");
    const config = Object.assign({}, workspace, { workspaceId: id });
    const searchEnabled = !(workspace.search && workspace.search.enabled === false);
    let resultNested = false;
    if (searchEnabled) {
      searchHost.innerHTML = window.__sidebarRenderer.managedSearchShellMarkup(config);
      const resultHost = searchHost.querySelector("[data-erpw-sales-search-results]");
      const governedResults = Array.from({ length: 18 }, (_value, index) => ({
        group_label: "Approved workspace results",
        badge_label: "Approved",
        label: `Governed result ${index + 1}`,
        meta: "Custom workspace destination",
      }));
      resultHost.innerHTML = window.__sidebarRenderer.managedSearchResultsMarkup(config, governedResults, 0);
      resultHost.hidden = false;
      const input = searchHost.querySelector("[data-erpw-sales-search-input]");
      window.__managedSearchActiveIndex = 0;
      window.__sidebarRenderer.applyManagedSearchActiveState(resultHost, input, 0);
      window.__sidebarRenderer.bindManagedSearchResultFocus(resultHost, (index) => {
        window.__managedSearchActiveIndex = index;
        window.__sidebarRenderer.applyManagedSearchActiveState(resultHost, input, index);
      });
      resultNested = Boolean(resultHost.querySelector(":scope .erpw-sales-console-search-group > .erpw-sales-console-search-result"));
    }
    const activeNode = document.querySelector('.erpw-sales-console-sidebar-link[aria-current="page"]');
    const nonHomeActiveItem = nonHomeActiveKey
      ? items.find((item) => item.key === nonHomeActiveKey)
      : null;
    return {
      sidebarReady,
      activeCount: document.querySelectorAll('.erpw-sales-console-sidebar-link[aria-current="page"]').length,
      activeLabel: activeNode ? activeNode.getAttribute("aria-label") || "" : "",
      compactSidebar: document.querySelector(".body-sidebar").getBoundingClientRect().width <= 80,
      nonHomeExpectedLabel: nonHomeActiveItem ? nonHomeActiveItem.label || "" : "",
      searchEnabled,
      resultNested,
    };
  }, workspaceId);
  assert.strictEqual(rendered.sidebarReady, true, `${workspaceId} actual sidebar renderer must accept its governed payload`);
  assert.strictEqual(rendered.activeCount, 1, `${workspaceId} actual sidebar must retain one current item`);
  if (rendered.nonHomeExpectedLabel) {
    assert.strictEqual(rendered.activeLabel, rendered.nonHomeExpectedLabel, `${workspaceId} non-home route must resolve its governed active item`);
  }
  assert.strictEqual(rendered.compactSidebar, collapsed, `${workspaceId} compact container state must match the explicit ${collapsed ? "collapsed" : "expanded"} fixture at ${viewport.width}px`);
  if (rendered.searchEnabled) {
    assert.strictEqual(rendered.resultNested, true, `${workspaceId} governed result must use the actual overflow-container nesting`);
  } else {
    assert.strictEqual(rendered.resultNested, false, `${workspaceId} must not synthesize governed search where registry policy disables it`);
  }

  const sidebarGeometry = await page.evaluate((isCollapsed) => {
    const sidebarNode = document.querySelector(".body-sidebar");
    const sidebarBox = sidebarNode.getBoundingClientRect();
    const visible = (node) => {
      const style = getComputedStyle(node);
      const box = node.getBoundingClientRect();
      return style.display !== "none" && style.visibility !== "hidden" && box.width > 0 && box.height > 0;
    };
    const layoutSelectors = [
      ".erpw-sales-console-sidebar-shell",
      ".erpw-sales-console-sidebar-utilities",
      ".erpw-sales-console-sidebar-section",
      ".erpw-sales-console-sidebar-item",
      ".erpw-sales-console-sidebar-item .standard-sidebar-item",
      ".erpw-sales-console-sidebar-utility",
      ".erpw-sales-console-sidebar-link",
    ];
    const layoutNodes = layoutSelectors.flatMap((selector) => Array.from(sidebarNode.querySelectorAll(selector)));
    const outOfBounds = Array.from(sidebarNode.querySelectorAll("*")).filter((node) => node instanceof HTMLElement).filter(visible).filter((node) => {
      const box = node.getBoundingClientRect();
      return box.left < sidebarBox.left - 1 || box.right > sidebarBox.right + 1;
    }).map((node) => String(node.className || node.tagName));
    const scrollOverflow = layoutNodes.filter(visible).filter((node) => node.scrollWidth > node.clientWidth + 1)
      .map((node) => String(node.className || node.tagName));
    const compactCopies = Array.from(sidebarNode.querySelectorAll(
      ".erpw-sales-console-sidebar-section-label, .erpw-sales-console-sidebar-utility-copy, .erpw-sales-console-sidebar-utility-shortcut, .erpw-sales-console-sidebar-copy"
    ));
    const focusTargets = [
      sidebarNode.querySelector(".erpw-sales-console-sidebar-header"),
      sidebarNode.querySelector(".erpw-sales-console-sidebar-utility"),
      sidebarNode.querySelector('.erpw-sales-console-sidebar-link[aria-current="page"]'),
      sidebarNode.querySelector(".collapse-sidebar-link"),
    ].filter(Boolean);
    return {
      outOfBounds,
      scrollOverflow,
      compactCopyCount: compactCopies.length,
      visibleCompactCopyCount: compactCopies.filter(visible).length,
      focusTargetCount: focusTargets.length,
      isCollapsed,
    };
  }, collapsed);
  assert.deepStrictEqual(sidebarGeometry.outOfBounds, [], `${workspaceId} sidebar descendants escaped the overflow container at ${viewport.width}px`);
  assert.deepStrictEqual(sidebarGeometry.scrollOverflow, [], `${workspaceId} sidebar layout containers overflowed at ${viewport.width}px`);
  assert(sidebarGeometry.compactCopyCount > 0, `${workspaceId} must render production compact/expanded copy`);
  assert.strictEqual(
    sidebarGeometry.visibleCompactCopyCount === 0,
    collapsed,
    `${workspaceId} compact copy visibility must follow the production container state at ${viewport.width}px`,
  );
  assert(sidebarGeometry.focusTargetCount >= 3, `${workspaceId} must render governed header, utility/navigation, and collapse focus targets`);

  const activeLink = page.locator('.erpw-sales-console-sidebar-link[aria-current="page"]');
  await activeLink.focus();
  await page.waitForTimeout(180);
  const activeFocus = await activeLink.evaluate((node) => {
    const computed = getComputedStyle(node);
    return { outline: computed.outlineWidth, boxShadow: computed.boxShadow, current: node.getAttribute("aria-current") };
  });
  assert(activeFocus.boxShadow.includes("rgb(37, 99, 235)"), `${workspaceId} active navigation focus must use the contained 3px treatment`);
  assert.strictEqual(activeFocus.current, "page");

  for (const selector of [
    ".erpw-sales-console-sidebar-header",
    ".erpw-sales-console-sidebar-utility",
    ".collapse-sidebar-link",
  ]) {
    const target = page.locator(selector).first();
    if (!await target.count()) continue;
    await target.focus();
    await page.waitForTimeout(180);
    const focusStyle = await target.evaluate((node) => {
      const style = getComputedStyle(node);
      const box = node.getBoundingClientRect();
      const sidebarBox = node.closest(".body-sidebar").getBoundingClientRect();
      return {
        boxShadow: style.boxShadow,
        contained: box.left >= sidebarBox.left - 1 && box.right <= sidebarBox.right + 1,
      };
    });
    assert(focusStyle.boxShadow.includes("rgb(37, 99, 235)"), `${workspaceId} ${selector} must use the shared contained focus treatment`);
    assert.strictEqual(focusStyle.contained, true, `${workspaceId} ${selector} must remain inside the production overflow container`);
  }
  await page.locator(".erpw-sales-console-sidebar-link").first().click();
  const navigation = await page.evaluate(() => window.__managedNavigations.at(-1) || []);
  assert(navigation.length > 0, `${workspaceId} governed sidebar click must dispatch a custom workspace route`);
  assert(!["Form", "List", "query-report"].includes(navigation[0]), `${workspaceId} sidebar click must not dispatch a native ERP surface`);

  if (!rendered.searchEnabled) return;
  const results = page.locator(".erpw-sales-console-search-result");
  assert.strictEqual(await results.count(), 18);
  for (const position of [0, 17]) {
    const result = results.nth(position);
    if (position === 0) {
      await page.locator("[data-erpw-sales-search-input]").focus();
    } else {
      await results.nth(position - 1).focus();
    }
    await page.keyboard.press("Tab");
    await page.waitForTimeout(180);
    const searchFocus = await result.evaluate((node) => {
      const container = node.closest(".erpw-sales-console-search-results");
      const input = document.querySelector("[data-erpw-sales-search-input]");
      const box = node.getBoundingClientRect();
      const containerBox = container.getBoundingClientRect();
      const computed = getComputedStyle(node);
      return {
        boxShadow: computed.boxShadow,
        leftContained: box.left >= containerBox.left - 1,
        rightContained: box.right <= containerBox.right + 1,
        topContained: box.top >= containerBox.top - 1,
        bottomContained: box.bottom <= containerBox.bottom + 1,
        overflow: getComputedStyle(container).overflowY,
        verticallyScrollable: container.scrollHeight > container.clientHeight,
        scrollTop: container.scrollTop,
        selectedCount: container.querySelectorAll('[role="option"][aria-selected="true"]').length,
        selected: node.getAttribute("aria-selected"),
        activeDescendant: input ? input.getAttribute("aria-activedescendant") : "",
        activeIndex: window.__managedSearchActiveIndex,
        focused: document.activeElement === node,
      };
    });
    assert(searchFocus.boxShadow.includes("inset"));
    assert(searchFocus.boxShadow.includes("rgb(37, 99, 235)"), `${workspaceId} result ${position} focus color was ${searchFocus.boxShadow}`);
    assert.strictEqual(searchFocus.leftContained, true);
    assert.strictEqual(searchFocus.rightContained, true);
    assert.strictEqual(searchFocus.topContained, true);
    assert.strictEqual(searchFocus.bottomContained, true);
    assert.strictEqual(searchFocus.verticallyScrollable, true, "actual governed-result list must overflow vertically");
    assert(["auto", "scroll"].includes(searchFocus.overflow));
    assert.strictEqual(searchFocus.selectedCount, 1, "direct option focus must retain exactly one selected governed result");
    assert.strictEqual(searchFocus.selected, "true", "directly focused governed result must become selected");
    assert.strictEqual(searchFocus.activeDescendant, `erpw-sales-console-search-option-${position}`);
    assert.strictEqual(searchFocus.activeIndex, position, "direct option focus must synchronize the managed active index");
    assert.strictEqual(searchFocus.focused, true, "governed option must receive direct keyboard focus");
    if (position === 17) assert(searchFocus.scrollTop > 0, "last governed result must be scrolled into the real overflow viewport");
  }
  const clearedSearchState = await page.evaluate(() => {
    const resultRoot = document.querySelector("[data-erpw-sales-search-results]");
    const input = document.querySelector("[data-erpw-sales-search-input]");
    window.__managedSearchActiveIndex = window.__sidebarRenderer.applyManagedSearchActiveState(resultRoot, input, -1);
    return {
      activeIndex: window.__managedSearchActiveIndex,
      selectedCount: resultRoot.querySelectorAll('[role="option"][aria-selected="true"]').length,
      activeDescendant: input.getAttribute("aria-activedescendant"),
    };
  });
  assert.strictEqual(clearedSearchState.activeIndex, -1);
  assert.strictEqual(clearedSearchState.selectedCount, 0, "clearing governed results must remove selected option state");
  assert.strictEqual(clearedSearchState.activeDescendant, null, "clearing governed results must remove aria-activedescendant");
}

async function verifyManagedDetailRouteActiveStates(page, managedDetailRoutes) {
  const expectedRoutes = Object.entries(EXPECTED_MANAGED_DETAIL_ACTIVE_KEYS).flatMap(([workspaceId, routes]) => (
    Object.entries(routes).map(([routeKey, activeKey]) => ({ workspace_id: workspaceId, route_key: routeKey, active_key: activeKey }))
  ));
  const discoveredRoutes = managedDetailRoutes
    .map((entry) => `${entry.workspace_id}:${entry.route_key}`)
    .sort();
  const expectedRouteIds = expectedRoutes
    .map((entry) => `${entry.workspace_id}:${entry.route_key}`)
    .sort();
  assert.deepStrictEqual(discoveredRoutes, expectedRouteIds, "managed detail/review route coverage must match the governance manifest exactly");

  await page.goto("about:blank");
  await page.setViewportSize({ width: 1366, height: 900 });
  await page.setContent(`<!doctype html><html><body>
    <aside class="body-sidebar" aria-label="Managed workspace navigation" style="width:260px">
      <div class="body-sidebar-top"><div class="sidebar-items"></div></div>
      <div class="body-sidebar-bottom"><button class="collapse-sidebar-link">Collapse</button></div>
    </aside>
  </body></html>`, { waitUntil: "domcontentloaded" });
  await page.evaluate(() => {
    window.__managedRoute = ["procurement-console"];
    window.frappe = {
      get_route() { return window.__managedRoute.slice(); },
      set_route() {},
      router: { on() {} },
      after_ajax(callback) { callback(); },
      call() { return Promise.resolve({ message: {} }); },
    };
  });
  await page.addScriptTag({ content: registrySource });
  await page.addScriptTag({ content: sidebarSource });
  await page.waitForFunction(() => document.body.classList.contains("erpw-sales-console-sidebar-managed")
    && window.erpWorkspaceConsoleSidebar && typeof window.erpWorkspaceConsoleSidebar.syncSidebarNow === "function");
  await page.evaluate(() => { window.module = { exports: {} }; });
  await page.addScriptTag({ content: sidebarSource });
  await page.evaluate(() => {
    window.__sidebarRenderer = window.module.exports;
    delete window.module;
  });
  const browserDiscoveredRoutes = await page.evaluate(() => ["procurement", "warehouse"].flatMap((workspaceId) => {
    const workspace = window.erpWorkspaceUiWorkspaceRegistry.get(workspaceId);
    const shellRouteNames = new Set(["launcher", "home", "worklist", "report"]);
    return Object.entries(workspace.routes)
      .filter(([routeName, routeKey]) => !/Path$/.test(routeName)
        && !shellRouteNames.has(routeName)
        && typeof routeKey === "string"
        && routeKey.startsWith(`${workspaceId === "procurement" ? "procurement" : "warehouse"}-console-`))
      .map(([, routeKey]) => `${workspaceId}:${routeKey}`);
  }));
  assert.deepStrictEqual(
    browserDiscoveredRoutes.sort(),
    expectedRouteIds,
    "browser registry detail/review routes must match the governance manifest independently",
  );

  for (const routeCase of expectedRoutes) {
    const result = await page.evaluate(async (entry) => {
      const workspace = window.erpWorkspaceUiWorkspaceRegistry.get(entry.workspace_id);
      const items = workspace.fallbackItems.map((item) => ({
        key: item.key,
        label: item.label,
        icon: item.icon,
        target: Object.assign({}, item.target),
      }));
      const payload = {
        schema_version: window.__sidebarRenderer.SIDEBAR_CONTEXT_SCHEMA_VERSION,
        workspace: { workspace_id: entry.workspace_id, title: workspace.title },
        sidebar: {
          schema_version: window.__sidebarRenderer.SIDEBAR_CONTEXT_SCHEMA_VERSION,
          workspace_id: entry.workspace_id,
          title: workspace.title,
          mode_label: workspace.modeLabel,
          scope_label: "Governed route contract",
          active_key: entry.active_key,
          home_key: items[0].key,
          items,
          sections: [{ key: "primary", label: "Workspace", items }],
        },
      };
      window.__managedRoute = [entry.route_key, "governed-review-context"];
      const resolved = window.__sidebarRenderer.resolveActiveKey(window.__managedRoute);
      const primed = window.erpWorkspaceConsoleSidebar.primePayload(payload);
      const rendered = primed && await window.erpWorkspaceConsoleSidebar.syncSidebarNow();
      const current = Array.from(document.querySelectorAll('.erpw-sales-console-sidebar-link[aria-current="page"]'));
      const expectedItem = items.find((item) => item.key === entry.active_key);
      return {
        rendered,
        resolved,
        currentCount: current.length,
        currentLabel: current[0] ? current[0].getAttribute("aria-label") : "",
        expectedLabel: expectedItem ? expectedItem.label : "",
      };
    }, routeCase);
    assert.strictEqual(result.rendered, true, `${routeCase.route_key} must render through the real shared sidebar`);
    assert.strictEqual(result.resolved, routeCase.active_key, `${routeCase.route_key} must resolve the governed owner item`);
    assert.strictEqual(result.currentCount, 1, `${routeCase.route_key} must expose exactly one current sidebar item`);
    assert(result.expectedLabel, `${routeCase.route_key} active key must exist in the actual registry fallback items`);
    assert.strictEqual(result.currentLabel, result.expectedLabel, `${routeCase.route_key} current item must match its governed registry owner`);
  }
}

async function verifyActualFinanceRendererGeometry(page, viewport, payload, expectedState, collapsed) {
  const sidebarWidth = collapsed ? 72 : 260;
  const initialSidebarWidth = collapsed ? 260 : 72;
  await page.goto("about:blank");
  await page.setViewportSize(viewport);
  await page.setContent(`<!doctype html><html><head><style>
    html,body{margin:0;max-width:100%}
    html,body,#workspace-frame{height:100%}
    #workspace-frame{display:grid;grid-template-columns:${initialSidebarWidth}px minmax(0,1fr);align-items:start;max-width:100vw}
    .body-sidebar{width:${sidebarWidth}px;height:100vh;max-width:100%;min-width:0;overflow:hidden}
    .body-sidebar-top{max-height:calc(100vh - 48px);overflow-y:auto}
    .main-section{box-sizing:border-box;width:100%;height:100vh;min-width:0;overflow-x:hidden;overflow-y:auto}
    #page-wrapper,.page-body,.layout-main,.layout-main-section-wrapper,.layout-main-section{box-sizing:border-box;min-width:0;max-width:100%}
    .page-head{height:56px}
    .page-body{width:100%;padding:0}
    .layout-main{display:flex;width:100%}
    .layout-main-section-wrapper{flex:1 0 100%;width:100%}
    .layout-footer.hide{display:none}
  </style></head><body>
    <div id="workspace-frame">
      <aside class="body-sidebar" aria-label="Managed workspace navigation" style="width:${initialSidebarWidth}px">
        <div class="body-sidebar-top"><div class="sidebar-items"></div></div>
        <div class="body-sidebar-bottom"><button class="collapse-sidebar-link">Collapse</button></div>
      </aside>
      <section class="main-section">
        <div id="page-wrapper" class="content page-container"></div>
      </section>
    </div>
  </body></html>`, { waitUntil: "domcontentloaded" });
  await page.evaluate(() => {
    delete window.module;
    window.__managedRoute = ["finance-control-desk"];
    window.__financeRequests = [];
    window.__financePageCreations = 0;
    const wrapper = document.getElementById("page-wrapper");
    window.__financeEventHandlers = new Map();
    const jquery = (node) => {
      if (node !== wrapper) throw new Error("Finance geometry lifecycle events must use the owned route wrapper");
      return {
        off(eventName) { window.__financeEventHandlers.delete(eventName); return this; },
        on(eventName, handler) { window.__financeEventHandlers.set(eventName, handler); return this; },
      };
    };
    window.jQuery = jquery;
    window.$ = jquery;
    window.frappe = {
      pages: {},
      container: { page: wrapper },
      ui: {
        make_app_page(options) {
          if (!options || options.parent !== wrapper || options.single_column !== true) {
            throw new Error("Finance must create one standard single-column Frappe Page");
          }
          window.__financePageCreations += 1;
          wrapper.innerHTML = `
            <header class="page-head"><div class="page-head-content"><span class="title-text"></span></div></header>
            <div class="page-body">
              <div class="layout-main">
                <div class="layout-main-section-wrapper">
                  <main class="layout-main-section"></main>
                  <div class="layout-footer hide"></div>
                </div>
              </div>
            </div>`;
          const body = wrapper.querySelector(".layout-main-section");
          wrapper.page = { body: { 0: body, jquery: "fixture" }, parent: wrapper };
          return wrapper.page;
        },
      },
      get_route() { return window.__managedRoute.slice(); },
      set_route() {},
      router: { on() {} },
      after_ajax(callback) { callback(); },
      call(options) {
        if (!options || !String(options.method || "").includes("get_finance_control_desk_overview_context")) {
          return Promise.resolve({ message: {} });
        }
        const request = { options, failHandler: null };
        window.__financeRequests.push(request);
        return {
          fail(handler) {
            request.failHandler = handler;
            return this;
          },
        };
      },
    };
  });
  await page.addScriptTag({ content: registrySource });
  await page.addScriptTag({ content: sidebarSource });
  await page.waitForFunction(() => document.body.classList.contains("erpw-sales-console-sidebar-managed")
    && window.erpWorkspaceConsoleSidebar && typeof window.erpWorkspaceConsoleSidebar.syncSidebarNow === "function");
  await page.evaluate(() => {
    const sidebar = document.querySelector(".body-sidebar");
    const collapse = document.querySelector(".collapse-sidebar-link");
    collapse.addEventListener("click", () => {
      const isCollapsed = sidebar.getBoundingClientRect().width <= 80;
      sidebar.style.width = isCollapsed ? "260px" : "72px";
      document.getElementById("workspace-frame").style.gridTemplateColumns = `${isCollapsed ? 260 : 72}px minmax(0,1fr)`;
      collapse.setAttribute("aria-expanded", isCollapsed ? "true" : "false");
    }, { once: true });
  });
  const toggledFinanceSidebar = await page.evaluate(() => {
    document.querySelector(".collapse-sidebar-link").click();
    const sidebar = document.querySelector(".body-sidebar");
    return {
      width: Math.round(sidebar.getBoundingClientRect().width),
      inlineWidth: sidebar.style.width,
      gridColumns: document.getElementById("workspace-frame").style.gridTemplateColumns,
    };
  });
  assert.strictEqual(
    toggledFinanceSidebar.width,
    sidebarWidth,
    `production Finance sidebar collapse fixture resolved ${JSON.stringify(toggledFinanceSidebar)} instead of ${sidebarWidth}px`,
  );
  await page.evaluate(async () => {
    const workspace = window.erpWorkspaceUiWorkspaceRegistry.get("finance");
    const items = workspace.fallbackItems.map((item) => ({
      key: item.key,
      label: item.label,
      icon: item.icon,
      target: Object.assign({}, item.target),
    }));
    const schemaVersion = "workspace-sidebar.v1";
    const payload = {
      schema_version: schemaVersion,
      workspace: { workspace_id: "finance", title: workspace.title },
      sidebar: {
        schema_version: schemaVersion,
        workspace_id: "finance",
        title: workspace.title,
        mode_label: workspace.modeLabel,
        scope_label: "Read-only overview",
        active_key: items[0].key,
        home_key: items[0].key,
        items,
        sections: [{ key: "workspace", label: "Workspace", items }],
      },
    };
    window.erpWorkspaceConsoleSidebar.primePayload(payload);
    await window.erpWorkspaceConsoleSidebar.syncSidebarNow();
  });
  await page.addScriptTag({ content: source });
  await page.evaluate(() => {
    const pageDefinition = window.frappe.pages["finance-control-desk"];
    if (!pageDefinition || typeof pageDefinition.on_page_load !== "function") {
      throw new Error("Finance production page registration is unavailable");
    }
    const wrapper = document.getElementById("page-wrapper");
    pageDefinition.on_page_load(wrapper);
    if (typeof pageDefinition.on_page_show !== "function") throw new Error("Finance page-show lifecycle is unavailable");
    pageDefinition.on_page_show(wrapper);
  });
  await page.waitForFunction(() => window.__financeRequests.length === 1);
  if (payload === null) {
    await page.evaluate(() => {
      window.__financeRequests[0].options.error(new Error("controlled source fixture failure"));
    });
  } else {
    await page.evaluate((financePayload) => {
      window.__financeRequests[0].options.callback({ message: financePayload });
    }, payload);
  }
  await page.waitForFunction(() => {
    const host = document.querySelector("[data-finance-render-host]");
    return host && host.getAttribute("aria-busy") === "false";
  });
  const actualState = await page.locator("[data-finance-cycle1-overview]").getAttribute("data-finance-cycle1-overview");
  assert.strictEqual(actualState, expectedState, `actual Finance renderer state must match the ${expectedState} fixture`);

  const geometry = await page.evaluate(() => {
    const root = document.documentElement;
    const frame = document.getElementById("workspace-frame").getBoundingClientRect();
    const scrollHost = document.querySelector(".main-section");
    const scrollHostBox = scrollHost.getBoundingClientRect();
    const sidebar = document.querySelector(".body-sidebar").getBoundingClientRect();
    const mainNode = document.querySelector(".layout-main-section");
    const main = mainNode.getBoundingClientRect();
    const pageBody = document.querySelector(".page-body");
    const presentationShell = document.querySelector("[data-finance-presentation-shell]");
    const presentationShellBox = presentationShell && presentationShell.getBoundingClientRect();
    const shellNode = document.querySelector(".finance-control-shell");
    const renderHost = shellNode.parentElement;
    const shell = shellNode.getBoundingClientRect();
    const lastShellChild = shellNode.lastElementChild;
    const lastShellChildBox = lastShellChild ? lastShellChild.getBoundingClientRect() : null;
    const hero = document.querySelector(".finance-control-hero").getBoundingClientRect();
    const heroTopChildren = Array.from(document.querySelectorAll(".finance-control-hero-top > *")).map((node) => node.getBoundingClientRect());
    const panels = Array.from(document.querySelectorAll(".finance-control-panel")).map((node) => node.getBoundingClientRect());
    const refresh = document.querySelector("[data-finance-refresh]");
    const refreshBox = refresh.getBoundingClientRect();
    const liveStatus = document.querySelector("[data-finance-live-status]");
    const liveStatusBox = liveStatus && liveStatus.getBoundingClientRect();
    const overlaps = (first, second) => (
      first.left < second.right - 0.5 && first.right > second.left + 0.5
      && first.top < second.bottom - 0.5 && first.bottom > second.top + 0.5
    );
    const horizontallyClipped = (node) => {
      const box = node.getBoundingClientRect();
      if (box.width <= 0 || box.height <= 0) return true;
      let ancestor = node.parentElement;
      while (ancestor) {
        const style = getComputedStyle(ancestor);
        if (["hidden", "clip", "auto", "scroll"].includes(style.overflowX)) {
          const ancestorBox = ancestor.getBoundingClientRect();
          if (box.left < ancestorBox.left - 1 || box.right > ancestorBox.right + 1) return true;
        }
        ancestor = ancestor.parentElement;
      }
      return box.left < -1 || box.right > root.clientWidth + 1;
    };
    const focusables = Array.from(document.querySelectorAll(
      '.body-sidebar button, .body-sidebar a, [data-finance-refresh]'
    )).filter((node) => getComputedStyle(node).display !== "none" && getComputedStyle(node).visibility !== "hidden");
    const overflowingElements = Array.from(document.querySelectorAll("body *")).filter((node) => {
      const style = getComputedStyle(node);
      const box = node.getBoundingClientRect();
      return style.display !== "none" && box.width > 0 && (box.left < -1 || box.right > root.clientWidth + 1);
    }).slice(0, 12).map((node) => ({
      tag: node.tagName.toLowerCase(),
      className: String(node.className || ""),
      left: Math.round(node.getBoundingClientRect().left),
      right: Math.round(node.getBoundingClientRect().right),
    }));
    const liveStyle = liveStatus ? getComputedStyle(liveStatus) : null;
    const clippedContent = Array.from(document.querySelectorAll(
      '.finance-control-title, .finance-control-summary, .finance-control-freshness, .finance-control-chip, .finance-control-panel-title, .finance-control-panel-copy, .finance-control-state-label, .finance-control-state-text'
    )).filter((node) => node.scrollWidth > node.clientWidth + 1).map((node) => String(node.className || node.tagName));
    const stateBoxes = [".finance-control-panel", ".finance-control-list", ".finance-control-state-row", ".finance-control-state-label", ".finance-control-state-text"].map((selector) => {
      const node = document.querySelector(selector);
      if (!node) return { selector, missing: true };
      const box = node.getBoundingClientRect();
      const style = getComputedStyle(node);
      return {
        selector,
        left: Math.round(box.left),
        right: Math.round(box.right),
        width: Math.round(box.width),
        clientWidth: node.clientWidth,
        scrollWidth: node.scrollWidth,
        boxSizing: style.boxSizing,
        cssWidth: style.width,
        maxWidth: style.maxWidth,
        gridTemplateColumns: style.gridTemplateColumns,
      };
    });
    const mainStyle = getComputedStyle(mainNode);
    const pageBodyStyle = getComputedStyle(pageBody);
    return {
      horizontalOverflow: root.scrollWidth - root.clientWidth,
      overflowingElements,
      frameContained: frame.left >= -0.5 && frame.right <= root.clientWidth + 0.5,
      sidebarMainOverlap: overlaps(sidebar, main),
      heroSidebarOverlap: overlaps(hero, sidebar),
      heroContentOverlap: heroTopChildren.some((box, index) => heroTopChildren.slice(index + 1).some((other) => overlaps(box, other))),
      heroContained: hero.left >= main.left - 0.5 && hero.right <= main.right + 0.5,
      panelOutOfBounds: panels.some((box) => box.left < main.left - 0.5 || box.right > main.right + 0.5),
      panelOverlap: panels.some((box, index) => panels.slice(index + 1).some((other) => overlaps(box, other))),
      panelCount: panels.length,
      clippedFocusableCount: focusables.filter(horizontallyClipped).length,
      clippedContent,
      financePageCreations: window.__financePageCreations,
      standardPageBodyPresent: Boolean(pageBody),
      shellMountedInPageBody: renderHost.hasAttribute("data-finance-render-host")
        && renderHost.parentElement === presentationShell
        && presentationShell.parentElement === mainNode && pageBody.contains(mainNode),
      presentationStructureOwned: renderHost.children.length === 1 && renderHost.firstElementChild === shellNode
        && mainNode.children.length === 1 && mainNode.firstElementChild === presentationShell
        && presentationShell.children.length === 2
        && presentationShell.firstElementChild === renderHost
        && presentationShell.lastElementChild === liveStatus,
      liveStatusOffsetParentOwned: Boolean(liveStatus && liveStatus.offsetParent === presentationShell),
      liveStatusContained: Boolean(liveStatusBox && presentationShellBox
        && liveStatusBox.left >= presentationShellBox.left - 0.5
        && liveStatusBox.right <= presentationShellBox.right + 0.5
        && liveStatusBox.top >= presentationShellBox.top - 0.5
        && liveStatusBox.bottom <= presentationShellBox.bottom + 0.5),
      mainTrailingSpace: Math.max(0, mainNode.scrollHeight - shellNode.offsetTop - shellNode.offsetHeight),
      shellBottomSpace: lastShellChildBox ? Math.max(0, shell.bottom - lastShellChildBox.bottom) : null,
      mainOverflowY: mainStyle.overflowY,
      pageBodyOverflowY: pageBodyStyle.overflowY,
      scrollHostOverflowY: getComputedStyle(scrollHost).overflowY,
      scrollHostClientHeight: scrollHost.clientHeight,
      scrollHostTrailingSpace: Math.max(0, scrollHost.scrollHeight - Math.max(scrollHost.clientHeight, shell.bottom - scrollHostBox.top)),
      documentScrollRange: document.scrollingElement.scrollHeight - document.scrollingElement.clientHeight,
      documentScrollY: window.scrollY,
      stateBoxes,
      refreshVisible: refreshBox.width > 0 && refreshBox.height > 0 && !horizontallyClipped(refresh),
      refreshEnabled: !refresh.disabled,
      liveStatusPresent: Boolean(liveStatus),
      liveStatusAccessible: Boolean(liveStatus && liveStatus.textContent.trim()
        && liveStatus.getAttribute("aria-live") === "polite"
        && liveStatus.getAttribute("role") === "status"
        && liveStatus.getAttribute("aria-atomic") === "true"
        && liveStyle.display !== "none" && liveStyle.visibility !== "hidden"
        && liveStatus.getAttribute("aria-hidden") !== "true"),
      requestCount: window.__financeRequests.length,
    };
  });
  const label = `${expectedState} ${collapsed ? "collapsed" : "expanded"} at ${viewport.width}px`;
  assert(
    geometry.horizontalOverflow <= 1,
    `actual Finance renderer overflowed by ${geometry.horizontalOverflow}px for ${label}: ${JSON.stringify({ overflowingElements: geometry.overflowingElements, stateBoxes: geometry.stateBoxes })}`,
  );
  assert.strictEqual(geometry.frameContained, true, `workspace frame escaped the viewport for ${label}`);
  assert.strictEqual(geometry.sidebarMainOverlap, false, `sidebar overlapped Finance content for ${label}`);
  assert.strictEqual(geometry.heroSidebarOverlap, false, `Finance hero overlapped the sidebar for ${label}`);
  assert.strictEqual(geometry.heroContentOverlap, false, `Finance hero content overlapped for ${label}`);
  assert.strictEqual(geometry.heroContained, true, `Finance hero escaped its real main container for ${label}`);
  assert.strictEqual(geometry.panelOutOfBounds, false, `Finance card escaped its real main container for ${label}`);
  assert.strictEqual(geometry.panelOverlap, false, `Finance cards overlapped for ${label}`);
  assert.strictEqual(geometry.financePageCreations, 1, `Finance must create exactly one Frappe Page for ${label}`);
  assert.strictEqual(geometry.standardPageBodyPresent, true, `Finance must retain the standard Frappe page body for ${label}`);
  assert.strictEqual(geometry.shellMountedInPageBody, true, `Finance must mount inside the Frappe page body for ${label}`);
  assert.strictEqual(geometry.presentationStructureOwned, true, `Finance Page body must contain exactly one owned presentation shell for ${label}`);
  assert.strictEqual(geometry.liveStatusOffsetParentOwned, true, `Finance live status escaped its owned positioning context for ${label}`);
  assert.strictEqual(geometry.liveStatusContained, true, `Finance live status escaped the owned presentation-shell rectangle for ${label}`);
  assert(geometry.mainTrailingSpace <= 1, `Finance page host added ${geometry.mainTrailingSpace}px of artificial trailing scroll for ${label}`);
  assert(geometry.shellBottomSpace <= 34, `Finance shell exceeded its normal bottom padding for ${label}: ${geometry.shellBottomSpace}px`);
  assert(!["hidden", "clip"].includes(geometry.mainOverflowY), `Finance main content disabled natural scrolling for ${label}`);
  assert(!["hidden", "clip"].includes(geometry.pageBodyOverflowY), `Frappe page body disabled natural scrolling for ${label}`);
  assert.strictEqual(geometry.scrollHostOverflowY, "auto", `Frappe main section must own Finance scrolling for ${label}`);
  assert(Math.abs(geometry.scrollHostClientHeight - viewport.height) <= 1, `Frappe scroll host height drifted for ${label}`);
  assert(geometry.scrollHostTrailingSpace <= 1, `Frappe scroll host added ${geometry.scrollHostTrailingSpace}px of blank tail for ${label}`);
  assert(geometry.documentScrollRange <= 1, `document retained a competing ${geometry.documentScrollRange}px Finance scroll range for ${label}`);
  assert.strictEqual(geometry.documentScrollY, 0, `document became a competing Finance scroll owner for ${label}`);
  assert(geometry.panelCount > 0, `actual Finance renderer must produce posture content for ${label}`);
  assert.strictEqual(geometry.clippedFocusableCount, 0, `focusable controls were horizontally clipped for ${label}`);
  assert.deepStrictEqual(geometry.clippedContent, [], `Finance copy or chips were clipped for ${label}`);
  assert.strictEqual(geometry.refreshVisible, true, `Refresh must remain visible for ${label}`);
  assert.strictEqual(geometry.refreshEnabled, true, `Refresh must be enabled after authoritative settlement for ${label}`);
  assert.strictEqual(geometry.liveStatusPresent, true, `persistent live status must exist for ${label}`);
  assert.strictEqual(geometry.liveStatusAccessible, true, `persistent live status must remain accessible for ${label}`);
  assert.strictEqual(geometry.requestCount, 1, `actual Finance registration must issue one aggregate request for ${label}`);

  const longContentGeometry = await page.evaluate((minimumHeight) => {
    const root = document.documentElement;
    const shell = document.querySelector(".finance-control-shell");
    const scrollHost = document.querySelector(".main-section");
    const sidebarScrollHost = document.querySelector(".body-sidebar-top");
    const marker = document.createElement("section");
    marker.className = "finance-control-panel";
    marker.setAttribute("data-finance-long-content-fixture", "true");
    marker.style.minHeight = `${minimumHeight}px`;
    marker.textContent = "Long Finance posture fixture";
    shell.appendChild(marker);
    const horizontalOverflow = root.scrollWidth - root.clientWidth;
    const contentScrollable = scrollHost.scrollHeight > scrollHost.clientHeight + 1;
    const sidebarScrollBefore = sidebarScrollHost.scrollTop;
    scrollHost.scrollTop = scrollHost.scrollHeight;
    const contentScrollAtEnd = scrollHost.scrollTop;
    const expectedContentScrollEnd = scrollHost.scrollHeight - scrollHost.clientHeight;
    const scrollHostBox = scrollHost.getBoundingClientRect();
    const markerBox = marker.getBoundingClientRect();
    const sidebarScrollAfterContent = sidebarScrollHost.scrollTop;
    const sidebarFixture = document.createElement("div");
    sidebarFixture.style.height = `${minimumHeight}px`;
    sidebarFixture.setAttribute("data-sidebar-long-content-fixture", "true");
    sidebarScrollHost.appendChild(sidebarFixture);
    const contentScrollBeforeSidebar = scrollHost.scrollTop;
    sidebarScrollHost.scrollTop = sidebarScrollHost.scrollHeight;
    return {
      horizontalOverflow,
      contentScrollable,
      contentReachedEnd: Math.abs(contentScrollAtEnd - expectedContentScrollEnd) <= 1,
      finalContentReachable: markerBox.bottom <= scrollHostBox.bottom + 1,
      sidebarUnaffectedByContentScroll: sidebarScrollAfterContent === sidebarScrollBefore,
      contentUnaffectedBySidebarScroll: scrollHost.scrollTop === contentScrollBeforeSidebar,
      documentScrollRange: document.scrollingElement.scrollHeight - document.scrollingElement.clientHeight,
      documentScrollY: window.scrollY,
      mainTrailingSpace: Math.max(0, shell.parentElement.scrollHeight - shell.offsetTop - shell.offsetHeight),
    };
  }, viewport.height + 320);
  assert.strictEqual(longContentGeometry.contentScrollable, true, `long Finance content must remain naturally scrollable for ${label}`);
  assert.strictEqual(longContentGeometry.contentReachedEnd, true, `long Finance content did not reach the Frappe scroll boundary for ${label}`);
  assert.strictEqual(longContentGeometry.finalContentReachable, true, `long Finance content could not reach the viewport bottom for ${label}`);
  assert.strictEqual(longContentGeometry.sidebarUnaffectedByContentScroll, true, `Finance scrolling moved the sidebar for ${label}`);
  assert.strictEqual(longContentGeometry.contentUnaffectedBySidebarScroll, true, `sidebar scrolling moved Finance content for ${label}`);
  assert(longContentGeometry.documentScrollRange <= 1, `long Finance content created a competing ${longContentGeometry.documentScrollRange}px document range for ${label}`);
  assert.strictEqual(longContentGeometry.documentScrollY, 0, `long Finance content moved the document scroll owner for ${label}`);
  assert(longContentGeometry.horizontalOverflow <= 1, `long Finance content created horizontal overflow for ${label}`);
  assert(longContentGeometry.mainTrailingSpace <= 1, `long Finance content created an artificial host tail for ${label}`);
}

async function verifyActualFinanceLifecycle(page, fixtures) {
  await page.goto("about:blank");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.setContent(`<!doctype html><html><body>
    <button id="persistent-sidebar-control">Persistent sidebar control</button>
    <div id="page-wrapper" class="content page-container"></div>
  </body></html>`, { waitUntil: "domcontentloaded" });
  await page.evaluate(() => {
    window.__financeRequests = [];
    window.__financePageCreations = 0;
    window.__financeEventHandlers = new Map();
    const wrapper = document.getElementById("page-wrapper");
    const jquery = (node) => {
      if (node !== wrapper) throw new Error("Finance lifecycle events must use the owned route wrapper");
      return {
        off(eventName) { window.__financeEventHandlers.delete(eventName); return this; },
        on(eventName, handler) { window.__financeEventHandlers.set(eventName, handler); return this; },
        trigger(eventName) {
          for (const [registeredName, handler] of window.__financeEventHandlers.entries()) {
            if (registeredName === eventName || registeredName.startsWith(`${eventName}.`)) handler.call(node);
          }
          return this;
        },
      };
    };
    window.jQuery = jquery;
    window.$ = jquery;
    window.frappe = {
      pages: {},
      container: { page: wrapper },
      ui: {
        make_app_page(options) {
          if (!options || options.parent !== wrapper || options.single_column !== true) {
            throw new Error("Finance lifecycle must create a standard owned Frappe Page");
          }
          window.__financePageCreations += 1;
          wrapper.innerHTML = `
            <header class="page-head"></header>
            <div class="page-body">
              <div class="layout-main">
                <div class="layout-main-section-wrapper">
                  <main class="layout-main-section"></main>
                  <div class="layout-footer hide"></div>
                </div>
              </div>
            </div>`;
          const body = wrapper.querySelector(".layout-main-section");
          wrapper.page = { parent: wrapper, body: { 0: body, jquery: "fixture" } };
          return wrapper.page;
        },
      },
      call(options) {
        const request = { options, failHandler: null };
        window.__financeRequests.push(request);
        return {
          fail(handler) {
            request.failHandler = handler;
            return this;
          },
        };
      },
    };
    window.module = { exports: {} };
  });
  await page.addScriptTag({ content: source });
  await page.evaluate(() => {
    window.__financeRenderer = window.module.exports;
    delete window.module;
    const wrapper = document.getElementById("page-wrapper");
    window.__financeRenderer.render(wrapper);
    window.__financeRenderer.render(wrapper);
  });
  await page.waitForFunction(() => window.__financeRequests.length === 1);
  const ownedLifecycle = await page.evaluate(() => {
    const wrapper = document.getElementById("page-wrapper");
    const body = wrapper.querySelector(".layout-main-section");
    return {
      creations: window.__financePageCreations,
      targetOwned: window.__financeRenderer.resolveTarget(wrapper) === body,
      hideBound: window.__financeEventHandlers.has("hide.financeControlDesk"),
    };
  });
  assert.deepStrictEqual(ownedLifecycle, { creations: 1, targetOwned: true, hideBound: true });
  await page.evaluate((payload) => {
    window.__financeRequests[0].options.callback({ message: payload });
  }, fixtures.manager_ready);
  await page.waitForFunction(() => {
    const refresh = document.querySelector("[data-finance-refresh]");
    const host = document.querySelector("[data-finance-render-host]");
    return refresh && !refresh.disabled && host && host.getAttribute("aria-busy") === "false";
  });
  assert.strictEqual(await page.locator("[data-finance-cycle1-overview='ready']").count(), 1);
  assert(!(await page.locator(".layout-main-section").innerText()).includes("CUST-"));
  assert.strictEqual(await page.locator("[data-finance-live-status]").textContent(), "Finance overview loaded.");

  await page.evaluate(() => {
    const liveStatus = document.querySelector("[data-finance-live-status]");
    liveStatus.dataset.persistenceMarker = "original";
    window.__financeLiveMutations = [];
    window.__financeLiveObserver = new MutationObserver(() => {
      window.__financeLiveMutations.push(liveStatus.textContent);
    });
    window.__financeLiveObserver.observe(liveStatus, { childList: true, characterData: true, subtree: true });
  });
  await page.locator("[data-finance-refresh]").focus();
  await page.locator("[data-finance-refresh]").click();
  await page.waitForFunction(() => window.__financeRequests.length === 2);
  await page.evaluate((payload) => {
    window.__financeRequests[1].options.callback({ message: payload });
  }, fixtures.manager_ready);
  await page.waitForFunction(() => {
    const refresh = document.querySelector("[data-finance-refresh]");
    const host = document.querySelector("[data-finance-render-host]");
    return refresh && document.activeElement === refresh
      && host && host.getAttribute("aria-busy") === "false"
      && document.querySelector("[data-finance-live-status]").textContent === "Finance overview refreshed.";
  });

  await page.locator("[data-finance-refresh]").click();
  await page.waitForFunction(() => window.__financeRequests.length === 3);
  await page.evaluate((payload) => {
    window.__financeRequests[2].options.callback({ message: payload });
  }, fixtures.manager_ready);
  await page.waitForFunction(() => window.__financeLiveMutations.filter((value) => value === "Finance overview refreshed.").length >= 2);

  const result = await page.evaluate(() => {
    const liveStatus = document.querySelector("[data-finance-live-status]");
    const visibleText = document.querySelector(".layout-main-section").innerText;
    return {
      callCount: window.__financeRequests.length,
      liveMarker: liveStatus && liveStatus.dataset.persistenceMarker,
      liveText: liveStatus && liveStatus.textContent,
      liveMutations: window.__financeLiveMutations.slice(),
      visibleText,
      refreshFocused: document.activeElement === document.querySelector("[data-finance-refresh]"),
    };
  });
  assert.strictEqual(result.callCount, 3, "each Refresh must issue exactly one additional Finance request");
  assert.strictEqual(result.liveMarker, "original", "Refresh must preserve the established live-region node");
  assert.strictEqual(result.refreshFocused, true, "Refresh must regain focus after the authoritative refresh settles");
  assert.strictEqual(result.liveText, "Finance overview refreshed.");
  assert(result.liveMutations.filter((value) => value === "").length >= 2, "each identical completion must clear the live region first");
  assert(result.liveMutations.filter((value) => value === "Finance overview refreshed.").length >= 2, "each identical completion must repopulate the live region");

  await page.locator("[data-finance-refresh]").click();
  await page.waitForFunction(() => window.__financeRequests.length === 4);
  await page.locator("#persistent-sidebar-control").focus();
  await page.evaluate((payload) => {
    window.__financeRequests[3].options.callback({ message: payload });
  }, fixtures.manager_ready);
  await page.waitForFunction(() => {
    const host = document.querySelector("[data-finance-render-host]");
    return host && host.getAttribute("aria-busy") === "false";
  });
  assert.strictEqual(
    await page.evaluate(() => document.activeElement && document.activeElement.id),
    "persistent-sidebar-control",
    "authoritative completion must not steal focus after the user moves to another persistent control",
  );

  const staleReadyStart = await page.evaluate(() => {
    const target = document.querySelector(".layout-main-section");
    window.__financeRenderer.loadOverviewContext(target, { force: true });
    return window.__financeRequests.length;
  });
  await page.waitForFunction((count) => window.__financeRequests.length === count + 1, staleReadyStart);
  const staleReadyFirst = await page.evaluate(() => window.__financeRequests.length - 1);
  const newerUnavailableStart = await page.evaluate(() => {
    window.__financeRenderer.loadOverviewContext(document.querySelector(".layout-main-section"), { force: true });
    return window.__financeRequests.length;
  });
  await page.waitForFunction((count) => window.__financeRequests.length === count + 1, newerUnavailableStart);
  const staleReadyIndexes = [staleReadyFirst, await page.evaluate(() => window.__financeRequests.length - 1)];
  await page.evaluate(({ indexes }) => {
    window.__financeRequests[indexes[1]].options.error(new Error("newer controlled failure"));
  }, { indexes: staleReadyIndexes });
  await page.waitForFunction(() => document.querySelector("[data-finance-cycle1-overview='unavailable']"));
  const authoritativeUnavailable = await page.locator("[data-finance-render-host]").innerHTML();
  await page.evaluate(({ indexes, payload }) => {
    window.__financeRequests[indexes[0]].options.callback({ message: payload });
  }, { indexes: staleReadyIndexes, payload: fixtures.manager_ready });
  await page.waitForTimeout(0);
  assert.strictEqual(await page.locator("[data-finance-render-host]").innerHTML(), authoritativeUnavailable, "stale success must not replace a newer unavailable state");

  const staleErrorStart = await page.evaluate(() => {
    const target = document.querySelector(".layout-main-section");
    window.__financeRenderer.loadOverviewContext(target, { force: true });
    return window.__financeRequests.length;
  });
  await page.waitForFunction((count) => window.__financeRequests.length === count + 1, staleErrorStart);
  const staleErrorFirst = await page.evaluate(() => window.__financeRequests.length - 1);
  const newerReadyStart = await page.evaluate(() => {
    window.__financeRenderer.loadOverviewContext(document.querySelector(".layout-main-section"), { force: true });
    return window.__financeRequests.length;
  });
  await page.waitForFunction((count) => window.__financeRequests.length === count + 1, newerReadyStart);
  const staleErrorIndexes = [staleErrorFirst, await page.evaluate(() => window.__financeRequests.length - 1)];
  await page.evaluate(({ indexes, payload }) => {
    window.__financeRequests[indexes[1]].options.callback({ message: payload });
  }, { indexes: staleErrorIndexes, payload: fixtures.ready_zero });
  await page.waitForFunction(() => document.body.innerText.includes("Current / not overdue: 0"));
  const authoritativeReady = await page.locator("[data-finance-render-host]").innerHTML();
  await page.evaluate(({ indexes }) => {
    window.__financeRequests[indexes[0]].options.error(new Error("stale technical failure"));
  }, { indexes: staleErrorIndexes });
  await page.waitForTimeout(0);
  assert.strictEqual(await page.locator("[data-finance-render-host]").innerHTML(), authoritativeReady, "stale error must not replace a newer ready-zero state");
  const readyZeroText = await page.locator("[data-finance-render-host]").innerText();
  assert(readyZeroText.includes("Current / not overdue: 0"));
  assert(readyZeroText.includes("Aggregate counts only"));
  assert(!readyZeroText.includes("No counts"));

  const preDispatchDepartureStart = await page.evaluate(() => {
    const wrapper = document.getElementById("page-wrapper");
    const target = document.querySelector(".layout-main-section");
    const before = window.__financeRequests.length;
    window.__financeRenderer.loadOverviewContext(target, { force: true });
    window.jQuery(wrapper).trigger("hide");
    return before;
  });
  await page.waitForTimeout(0);
  assert.strictEqual(
    await page.evaluate(() => window.__financeRequests.length),
    preDispatchDepartureStart,
    "same-turn route departure must invalidate before the obsolete Finance RPC dispatches",
  );

  const dispatchedDepartureStart = await page.evaluate(() => {
    window.__financeRenderer.loadOverviewContext(document.querySelector(".layout-main-section"), { force: true });
    return window.__financeRequests.length;
  });
  await page.waitForFunction((count) => window.__financeRequests.length === count + 1, dispatchedDepartureStart);
  const departureIndex = await page.evaluate(() => {
    window.jQuery(document.getElementById("page-wrapper")).trigger("hide");
    return window.__financeRequests.length - 1;
  });
  await page.evaluate(({ index, payload }) => {
    window.__financeRequests[index].options.callback({ message: payload });
  }, { index: departureIndex, payload: fixtures.manager_ready });
  await page.waitForTimeout(0);
  assert.strictEqual(await page.evaluate(() => document.querySelector(".layout-main-section").__financeControlDeskOverviewPayload), null);
  const returnStart = await page.evaluate(() => {
    window.__financeRenderer.render(document.getElementById("page-wrapper"));
    return window.__financeRequests.length;
  });
  await page.waitForFunction((count) => window.__financeRequests.length === count + 1, returnStart);
  assert.strictEqual(await page.evaluate(() => window.__financePageCreations), 1, "Finance return must reuse the owned Page");
  await page.evaluate((payload) => {
    window.__financeRequests[window.__financeRequests.length - 1].options.callback({ message: payload });
  }, fixtures.unavailable);
  await page.waitForFunction(() => document.body.innerText.includes("Manager-only payables posture"));
  const unavailableText = await page.locator("[data-finance-render-host]").innerText();
  assert(unavailableText.includes("Unavailable"));
  assert(!unavailableText.includes("No counts"));
  assert(!unavailableText.includes("accounts_manager_required"));

  const failureStart = await page.evaluate(() => {
    const target = document.querySelector(".layout-main-section");
    window.__financeRenderer.loadOverviewContext(target, { force: true, userInitiated: true });
    return window.__financeRequests.length;
  });
  await page.waitForFunction((count) => window.__financeRequests.length === count + 1, failureStart);
  await page.evaluate(() => {
    window.__financeRequests[window.__financeRequests.length - 1].options.error(new Error("technical transport detail must stay hidden"));
  });
  await page.waitForFunction(() => document.querySelector("[data-finance-live-status]").textContent.includes("could not be refreshed"));
  const failureText = await page.locator(".layout-main-section").innerText();
  assert(!failureText.includes("technical transport detail"));
  assert(!failureText.includes("source_permission_denied"));
}

async function verifyActualFinanceTimeout(page) {
  await page.goto("about:blank");
  await page.setContent(`<!doctype html><html><body><div id="page-wrapper" class="content page-container"></div></body></html>`);
  await page.evaluate(() => {
    window.__financeTimeout = null;
    window.__nativeSetTimeout = window.setTimeout.bind(window);
    window.setTimeout = (callback, delay) => {
      if (delay === 30000) {
        window.__financeTimeout = callback;
        return 30000;
      }
      return window.__nativeSetTimeout(callback, delay);
    };
    const wrapper = document.getElementById("page-wrapper");
    window.__financeTimeoutEventHandlers = new Map();
    const jquery = (node) => {
      if (node !== wrapper) throw new Error("Finance timeout lifecycle events must use the owned route wrapper");
      return {
        off(eventName) { window.__financeTimeoutEventHandlers.delete(eventName); return this; },
        on(eventName, handler) { window.__financeTimeoutEventHandlers.set(eventName, handler); return this; },
      };
    };
    window.jQuery = jquery;
    window.$ = jquery;
    window.frappe = {
      pages: {},
      ui: {
        make_app_page(options) {
          if (!options || options.parent !== wrapper || options.single_column !== true) {
            throw new Error("Finance timeout must use an owned Frappe Page");
          }
          wrapper.innerHTML = `<div class="page-body"><div class="layout-main"><div class="layout-main-section-wrapper"><main class="layout-main-section"></main></div></div></div>`;
          const body = wrapper.querySelector(".layout-main-section");
          wrapper.page = { parent: wrapper, body: { 0: body, jquery: "fixture" } };
          return wrapper.page;
        },
      },
      call() { return { fail() { return this; } }; },
    };
    window.module = { exports: {} };
  });
  await page.addScriptTag({ content: source });
  await page.evaluate(() => {
    window.__financeRenderer = window.module.exports;
    delete window.module;
    window.__financeRenderer.render(document.getElementById("page-wrapper"));
  });
  await page.waitForFunction(() => typeof window.__financeTimeout === "function");
  await page.evaluate(() => {
    const timeout = window.__financeTimeout;
    window.setTimeout = window.__nativeSetTimeout;
    timeout();
  });
  await page.waitForFunction(() => document.querySelector("[data-finance-cycle1-overview='unavailable']"));
  const text = await page.locator(".layout-main-section").innerText();
  assert(text.includes("temporarily unavailable"));
  assert(!text.includes("timed out"));
}

async function main() {
  if (process.argv.includes("--contrast-only")) {
    process.stdout.write(`Finance title ${sourceMinimumContrast.toFixed(2)}:1 and sidebar focus ${sourceFocusContrast.toFixed(2)}:1 contrast passed.\n`);
    return;
  }
  const { chromium } = require("@playwright/test");
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    const financeFixtures = loadFinanceFixtures();
    for (const viewport of [
      { width: 1366, height: 900 },
      { width: 390, height: 844 },
      { width: 320, height: 844 },
    ]) {
      for (const state of ["ready", "restricted", "unavailable"]) {
        await verify(page, viewport, state);
      }
      for (const workspaceId of ["sales", "procurement", "warehouse", "finance"]) {
        for (const collapsed of [false, true]) {
          await verifyActualSidebarRenderer(page, viewport, workspaceId, collapsed);
        }
      }
      const actualStates = [
        ["ready", financeFixtures.manager_ready],
        ["ready", financeFixtures.unavailable],
        ["restricted", financeFixtures.restricted],
        ["unavailable", financeFixtures.overview_unavailable],
        ["unavailable", null],
      ];
      const financeSidebarStates = viewport.width > 390 ? [false, true] : [true];
      for (const [state, payload] of actualStates) {
        for (const collapsed of financeSidebarStates) {
          await verifyActualFinanceRendererGeometry(page, viewport, payload, state, collapsed);
        }
      }
    }
    await verifyManagedDetailRouteActiveStates(page, financeFixtures.managed_detail_routes);
    await verifyActualFinanceLifecycle(page, financeFixtures);
    await verifyActualFinanceTimeout(page);
  } finally {
    await browser.close();
  }
  process.stdout.write("Finance Cycle 1 responsive smoke passed.\n");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
