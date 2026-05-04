/* global frappe */

(function () {
  const PAGE_KEY = "procurement-console";
  const ASSET = "/assets/erp_workspace_ui/js/procurement_console/procurement_console_page.js";

  function scheduleProcurementConsoleRender() {
    const boot = window.erpWorkspaceUiBoot || {};
    if (typeof boot.scheduleProcurementDirectPage === "function") {
      boot.scheduleProcurementDirectPage();
      return;
    }
    if (typeof boot.ensureProcurementDirectPage === "function") {
      boot.ensureProcurementDirectPage();
    }
  }

  function invokeRenderer(wrapper) {
    const pageDef = frappe.pages && frappe.pages[PAGE_KEY] ? frappe.pages[PAGE_KEY] : null;
    if (pageDef && pageDef.__erpwProcurementConsoleRenderer && typeof pageDef.on_page_show === "function") {
      pageDef.on_page_show(wrapper);
      return true;
    }
    return false;
  }

  function ensureAndRender(wrapper) {
    frappe.require([ASSET], () => {
      if (!invokeRenderer(wrapper)) scheduleProcurementConsoleRender();
      window.setTimeout(() => {
        if (!invokeRenderer(wrapper)) scheduleProcurementConsoleRender();
      }, 80);
      window.setTimeout(() => {
        if (!invokeRenderer(wrapper)) scheduleProcurementConsoleRender();
      }, 220);
    });
  }

  const pageDef = frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  if (!pageDef.__erpwProcurementConsoleRenderer) {
    pageDef.on_page_load = ensureAndRender;
    pageDef.on_page_show = ensureAndRender;
  } else {
    scheduleProcurementConsoleRender();
  }
})();
