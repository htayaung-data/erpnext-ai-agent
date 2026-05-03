/* global frappe */

(function () {
  const PAGE_KEY = "procurement-console-report";
  const METHOD = "erp_workspace_ui.procurement_console.report.get_procurement_console_report_context";

  function reportKey() {
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) && route.length > 1 ? String(route[1] || "").replace(/-/g, "_") : "";
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function render(wrapper, state) {
    wrapper.innerHTML = `
      <section style="padding: 28px;">
        <div style="border: 1px solid #d8e4f2; border-radius: 12px; background: #fff; padding: 22px; max-width: 720px;">
          <div style="font-size: 11px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: #475569; margin-bottom: 10px;">Procurement Console report</div>
          <h2 style="margin: 0 0 8px; font-size: 22px; color: #0f172a;">${escapeHtml(state.title || "Report unavailable")}</h2>
          <p style="margin: 0; color: #64748b; font-size: 13px; line-height: 1.55;">${escapeHtml(state.detail || "This report is not available yet.")}</p>
        </div>
      </section>
    `;
  }

  function load(wrapper) {
    render(wrapper, { title: "Opening report", detail: "Checking workspace access." });
    frappe.call({
      method: METHOD,
      args: { report_key: reportKey() },
      callback(response) {
        const payload = response && response.message ? response.message : {};
        const state = payload.results && payload.results.state ? payload.results.state : {};
        render(wrapper, state);
      },
      error() {
        render(wrapper, {
          title: "Report could not be opened",
          detail: "The report context could not be loaded right now.",
        });
      },
    });
  }

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
      parent: wrapper,
      title: "Procurement Console Report",
      single_column: true,
    });
    load(page && page.body ? page.body : wrapper);
  };
  frappe.pages[PAGE_KEY].on_page_show = function (wrapper) {
    const page = frappe.ui.make_app_page({
      parent: wrapper,
      title: "Procurement Console Report",
      single_column: true,
    });
    load(page && page.body ? page.body : wrapper);
  };
})();
