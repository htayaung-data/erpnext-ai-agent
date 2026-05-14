/* global frappe */

(function () {
  const PAGE_KEY = "procurement-console-rfq-form";
  const FORM_PAGE_ASSET = "/assets/erp_workspace_ui/js/procurement_console/procurement_console_rfq_form.js";

  function withFormRuntime(wrapper, methodName) {
    frappe.require(FORM_PAGE_ASSET, () => {
      const runtime = window.erpWorkspaceUiProcurementRfqForm || {};
      const method = runtime[methodName];
      if (typeof method === "function") method(wrapper, PAGE_KEY);
    });
  }

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) { withFormRuntime(wrapper, "render"); };
  frappe.pages[PAGE_KEY].on_page_show = function (wrapper) { withFormRuntime(wrapper, "show"); };
})();
