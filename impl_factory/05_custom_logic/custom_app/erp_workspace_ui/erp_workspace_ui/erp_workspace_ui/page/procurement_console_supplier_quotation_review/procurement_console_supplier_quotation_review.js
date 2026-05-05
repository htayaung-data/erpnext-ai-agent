/* global frappe */

(function () {
  const PAGE_KEY = "procurement-console-supplier-quotation-review";
  const REVIEW_PAGE_ASSET = "/assets/erp_workspace_ui/js/procurement_console/procurement_console_review_page.js";

  function withReviewRuntime(wrapper, methodName) {
    frappe.require(REVIEW_PAGE_ASSET, () => {
      const runtime = window.erpWorkspaceUiProcurementReviewPage || {};
      const method = runtime[methodName];
      if (typeof method === "function") {
        method(wrapper, PAGE_KEY);
      }
    });
  }

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) { withReviewRuntime(wrapper, "render"); };
  frappe.pages[PAGE_KEY].on_page_show = function (wrapper) { withReviewRuntime(wrapper, "show"); };
})();
