/* global frappe */

(function () {
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

  frappe.require([ASSET], () => {
    scheduleProcurementConsoleRender();
    window.setTimeout(scheduleProcurementConsoleRender, 80);
    window.setTimeout(scheduleProcurementConsoleRender, 220);
  });
})();
