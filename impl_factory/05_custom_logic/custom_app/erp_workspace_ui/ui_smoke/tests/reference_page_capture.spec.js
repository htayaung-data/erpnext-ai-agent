const { test, expect } = require("@playwright/test");
const {
  DIAGNOSTIC_TIMEOUT,
  buildDocRoute,
  openRuntimePage,
  waitForDiagnosticAttr,
  waitForFeatureAttempt,
  waitForFeatureReady,
} = require("./helpers/runtime_page");
const {
  CAPTURE_ENABLED,
  CAPTURE_ROOT,
  VIEWPORTS,
  applyViewport,
  captureFullPage,
  captureLocator,
  clickTabByName,
  listVisibleTabs,
  resetCaptureDir,
  writeCaptureJson,
} = require("./helpers/reference_capture");

test.describe.configure({ mode: "serial" });

test.describe("PrimeAxis reference screenshot capture", () => {
  test.skip(!CAPTURE_ENABLED, "Set ERPW_CAPTURE_REFERENCE=1 to enable reference screenshot capture.");

  async function settleSalesConsole(page) {
    const shell = page.locator(".sales-console-shell").first();
    await expect(shell).toBeVisible({ timeout: DIAGNOSTIC_TIMEOUT });
    await expect
      .poll(async () => shell.getAttribute("data-erpw-console-bootstrap"), {
        timeout: DIAGNOSTIC_TIMEOUT,
        message: "Expected Sales Console bootstrap to settle successfully",
      })
      .toBe("ready");
    await expect(page.locator(".sales-console-action:visible").first()).toBeVisible({ timeout: DIAGNOSTIC_TIMEOUT });
    await expect(page.locator(".sales-console-queue-card").first()).toBeVisible({ timeout: DIAGNOSTIC_TIMEOUT });
  }

  async function settleSalesOrder(page) {
    await waitForDiagnosticAttr(page, "data-erpw-diag-shell-mount", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-shell-skeleton", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-shell-prepare", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-shell-release", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-support-shell", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-sidebar-cleanup", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-workflow-banner", ["ready", "missing"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-connection-workspace", ["ready"]);
    await waitForFeatureReady(page, "context_load");
    await waitForFeatureReady(page, "shell_prepare");
    await waitForFeatureReady(page, "shell_release");
    await waitForFeatureReady(page, "connection_workspace");
    await waitForFeatureAttempt(page, "workflow_banner");
  }

  async function settleQuotation(page) {
    await waitForDiagnosticAttr(page, "data-erpw-diag-shell-mount", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-shell-skeleton", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-shell-prepare", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-support-shell", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-sidebar-cleanup", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-workflow-banner", ["ready", "missing"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-connection-workspace", ["ready"]);
    await waitForFeatureReady(page, "context_load");
    await waitForFeatureReady(page, "shell_prepare");
    await waitForFeatureReady(page, "connection_workspace");
    await waitForFeatureAttempt(page, "workflow_banner");
  }

  async function settleDeliveryNote(page) {
    await waitForDiagnosticAttr(page, "data-erpw-diag-shell-mount", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-shell-skeleton", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-shell-prepare", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-support-shell", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-sidebar-cleanup", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-workflow-banner", ["ready", "missing"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-connection-workspace", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-address-contact-tab", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-terms-output-tab", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-items-execution-zone", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-commercial-posture", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-more-info-tab", ["ready"]);
    await waitForFeatureReady(page, "context_load");
    await waitForFeatureReady(page, "shell_prepare");
    await waitForFeatureReady(page, "connection_workspace");
    await waitForFeatureReady(page, "address_contact_tab");
    await waitForFeatureReady(page, "terms_output_tab");
    await waitForFeatureReady(page, "items_execution_zone");
    await waitForFeatureReady(page, "commercial_posture");
    await waitForFeatureReady(page, "more_info_tab");
    await waitForFeatureAttempt(page, "workflow_banner");
  }

  async function settleSalesInvoice(page) {
    await waitForDiagnosticAttr(page, "data-erpw-diag-shell-mount", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-shell-skeleton", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-shell-prepare", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-support-shell", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-sidebar-cleanup", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-workflow-banner", ["ready", "missing"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-connection-workspace", ["ready"]);
    await waitForDiagnosticAttr(page, "data-erpw-diag-payment-entry-access", ["ready", "missing"]);
    await waitForFeatureReady(page, "context_load");
    await waitForFeatureReady(page, "shell_prepare");
    await waitForFeatureReady(page, "connection_workspace");
    await waitForFeatureAttempt(page, "payment_entry_access");
    await waitForFeatureAttempt(page, "workflow_banner");
  }

  async function captureConsoleReference(page, viewport) {
    const route = process.env.ERPW_SALES_CONSOLE_ROUTE || "/desk/sales-console";
    const pageKey = "sales_console";

    await applyViewport(page, viewport);
    resetCaptureDir(pageKey, viewport.key);
    await openRuntimePage(page, route);
    await settleSalesConsole(page);

    const commandShellCaptured = await captureLocator(page.locator(".sales-console-header").first(), pageKey, viewport.key, "02_command_shell");
    const actionLayerCaptured = await captureLocator(page.locator('[data-section-key="actions"]').first(), pageKey, viewport.key, "03_action_layer");
    const secondaryWorkspaceCaptured = await captureLocator(page.locator('[data-section-key="inquiry"]').first(), pageKey, viewport.key, "04_secondary_workspace");
    const supportSurfaceCaptured = await captureLocator(page.locator('[data-section-key="work"]').first(), pageKey, viewport.key, "05_support_surface");

    await captureFullPage(page, pageKey, viewport.key, "01_full_page");
    writeCaptureJson(pageKey, viewport.key, "00_inventory", {
      page_type: "workspace_console",
      page_key: pageKey,
      viewport: viewport.key,
      route,
      elements: {
        full_page: true,
        command_shell: commandShellCaptured,
        action_layer: actionLayerCaptured,
        secondary_workspace: secondaryWorkspaceCaptured,
        support_surface: supportSurfaceCaptured,
      },
      tabs: [],
    });
  }

  async function captureChildPageReference(page, viewport, options) {
    await applyViewport(page, viewport);
    resetCaptureDir(options.pageKey, viewport.key);
    await openRuntimePage(page, options.route);
    await options.settle(page);

    const commandShellCaptured = await captureLocator(page.locator(".erpw-child-summary").first(), options.pageKey, viewport.key, "02_command_shell");
    const actionLayerCaptured = await captureLocator(page.locator(".erpw-child-actions").first(), options.pageKey, viewport.key, "03_action_layer");
    const guidanceLayerCaptured = await captureLocator(page.locator(".erpw-child-context").first(), options.pageKey, viewport.key, "04_guidance_layer");

    await captureFullPage(page, options.pageKey, viewport.key, "01_full_page");

    const tabs = await listVisibleTabs(page);
    writeCaptureJson(options.pageKey, viewport.key, "00_inventory", {
      page_type: "child_page",
      page_key: options.pageKey,
      viewport: viewport.key,
      route: options.route,
      elements: {
        full_page: true,
        command_shell: commandShellCaptured,
        action_layer: actionLayerCaptured,
        guidance_layer: guidanceLayerCaptured,
        visible_tablist: tabs.length > 0,
      },
      tabs,
    });

    for (let index = 0; index < tabs.length; index += 1) {
      const tab = tabs[index];
      if (!(await clickTabByName(page, tab.name))) {
        continue;
      }
      const sequence = String(index + 5).padStart(2, "0");
      await captureFullPage(page, options.pageKey, viewport.key, `${sequence}_tab_${tab.normalized}`);
    }
  }

  for (const viewport of VIEWPORTS) {
    test(`Sales Console reference capture (${viewport.key})`, async ({ page }) => {
      await captureConsoleReference(page, viewport);
    });

    test(`Sales Order reference capture (${viewport.key})`, async ({ page }) => {
      await captureChildPageReference(page, viewport, {
        pageKey: "sales_order",
        route: buildDocRoute({
          routeEnv: "ERPW_SALES_ORDER_ROUTE",
          nameEnv: "ERPW_SALES_ORDER_NAME",
          slug: "sales-order",
        }),
        settle: settleSalesOrder,
      });
    });

    test(`Quotation reference capture (${viewport.key})`, async ({ page }) => {
      await captureChildPageReference(page, viewport, {
        pageKey: "quotation",
        route: buildDocRoute({
          routeEnv: "ERPW_QUOTATION_ROUTE",
          nameEnv: "ERPW_QUOTATION_NAME",
          slug: "quotation",
        }),
        settle: settleQuotation,
      });
    });

    test(`Delivery Note reference capture (${viewport.key})`, async ({ page }) => {
      await captureChildPageReference(page, viewport, {
        pageKey: "delivery_note",
        route: buildDocRoute({
          routeEnv: "ERPW_DELIVERY_NOTE_ROUTE",
          nameEnv: "ERPW_DELIVERY_NOTE_NAME",
          slug: "delivery-note",
        }),
        settle: settleDeliveryNote,
      });
    });

    test(`Sales Invoice reference capture (${viewport.key})`, async ({ page }) => {
      await captureChildPageReference(page, viewport, {
        pageKey: "sales_invoice",
        route: buildDocRoute({
          routeEnv: "ERPW_SALES_INVOICE_ROUTE",
          nameEnv: "ERPW_SALES_INVOICE_NAME",
          slug: "sales-invoice",
        }),
        settle: settleSalesInvoice,
      });
    });
  }

  test.afterAll(async () => {
    console.log(`Reference screenshots are available under: ${CAPTURE_ROOT}`);
  });
});
