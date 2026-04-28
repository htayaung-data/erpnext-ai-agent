const { test, expect } = require("@playwright/test");
const { DIAGNOSTIC_TIMEOUT, openRuntimePage } = require("./helpers/runtime_page");

test("Sales Console runtime loads with shared shell and inquiry controls", async ({ page }) => {
  const route = process.env.ERPW_SALES_CONSOLE_ROUTE || "/desk/sales-console";

  await openRuntimePage(page, route);

  const $shell = page.locator(".sales-console-shell").first();
  await expect($shell).toBeVisible({ timeout: DIAGNOSTIC_TIMEOUT });

  await expect($shell).toHaveAttribute("data-erpw-console-runtime", "ready");
  await expect
    .poll(async () => $shell.getAttribute("data-erpw-console-bootstrap"), {
      timeout: DIAGNOSTIC_TIMEOUT,
      message: "Expected Sales Console bootstrap to settle successfully",
    })
    .toBe("ready");

  await expect(page.locator(".sales-console-title")).toHaveText("Sales Console");
  await expect(page.locator("[data-header-roleline]")).toBeVisible();
  await expect(page.locator("[data-inquiry-input]")).toBeVisible();
  await expect
    .poll(async () => page.locator(".sales-console-action:visible").count(), {
      timeout: DIAGNOSTIC_TIMEOUT,
      message: "Expected Sales Console to expose at least one visible action card",
    })
    .toBeGreaterThan(0);
  await expect(page.locator(".sales-console-queue-card").first()).toBeVisible();
});
