const { test, expect } = require("@playwright/test");
const {
  buildDocRoute,
  openRuntimePage,
  waitForDiagnosticAttr,
  waitForFeatureReady,
  waitForFeatureAttempt,
} = require("./helpers/runtime_page");

test.describe.configure({ mode: "serial" });

test("Sales Order child-page runtime diagnostics settle", async ({ page }) => {
  const route = buildDocRoute({
    routeEnv: "ERPW_SALES_ORDER_ROUTE",
    nameEnv: "ERPW_SALES_ORDER_NAME",
    slug: "sales-order",
  });

  await openRuntimePage(page, route);

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
});

test("Quotation child-page runtime diagnostics settle", async ({ page }) => {
  const route = buildDocRoute({
    routeEnv: "ERPW_QUOTATION_ROUTE",
    nameEnv: "ERPW_QUOTATION_NAME",
    slug: "quotation",
  });

  await openRuntimePage(page, route);

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
});

test("Delivery Note child-page runtime diagnostics settle", async ({ page }) => {
  const route = buildDocRoute({
    routeEnv: "ERPW_DELIVERY_NOTE_ROUTE",
    nameEnv: "ERPW_DELIVERY_NOTE_NAME",
    slug: "delivery-note",
  });

  await openRuntimePage(page, route);

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
});


test("Sales Invoice child-page runtime diagnostics settle", async ({ page }) => {
  const route = buildDocRoute({
    routeEnv: "ERPW_SALES_INVOICE_ROUTE",
    nameEnv: "ERPW_SALES_INVOICE_NAME",
    slug: "sales-invoice",
  });

  await openRuntimePage(page, route);

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
});
