/* global frappe */

(function () {
  const PAGE_KEY = "warehouse-console";
  const ASSET = "/assets/erp_workspace_ui/js/warehouse_console/warehouse_console_page.js";

  function invokeRenderer(wrapper) {
    const pageDef = frappe.pages && frappe.pages[PAGE_KEY] ? frappe.pages[PAGE_KEY] : null;
    if (pageDef && pageDef.__erpwWarehouseConsoleRenderer && typeof pageDef.on_page_show === "function") {
      pageDef.on_page_show(wrapper);
      return true;
    }
    return false;
  }

  function ensureAndRender(wrapper) {
    frappe.require([ASSET], () => {
      invokeRenderer(wrapper);
      window.setTimeout(() => invokeRenderer(wrapper), 80);
      window.setTimeout(() => invokeRenderer(wrapper), 220);
    });
  }

  const pageDef = frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  if (!pageDef.__erpwWarehouseConsoleRenderer) {
    pageDef.on_page_load = ensureAndRender;
    pageDef.on_page_show = ensureAndRender;
  }
})();
