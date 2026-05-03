/* global frappe */

(function () {
  const PAGE_KEY = "procurement-console-home";
  const TARGET_ROUTE = "procurement-console";

  function handoff() {
    if (frappe.get_route_str && frappe.get_route_str() === TARGET_ROUTE) return;
    window.setTimeout(() => {
      frappe.set_route(TARGET_ROUTE);
    }, 0);
  }

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
      parent: wrapper,
      title: "Procurement Console",
      single_column: true,
    });
    const host = page && page.body ? page.body : wrapper;
    if (host) {
      host.innerHTML = '<div style="padding: 28px; color: #64748b; font-size: 13px;">Opening Procurement Console</div>';
    }
    handoff();
  };
  frappe.pages[PAGE_KEY].on_page_show = handoff;
})();
