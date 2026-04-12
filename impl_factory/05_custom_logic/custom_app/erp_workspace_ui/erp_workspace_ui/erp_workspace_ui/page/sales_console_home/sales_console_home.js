/* global frappe */

(function () {
  const PAGE_KEY = "sales-console-home";
  const TARGET_ROUTE = "sales-console";

  function handoff() {
    if (frappe.get_route_str && frappe.get_route_str() === TARGET_ROUTE) return;
    window.setTimeout(() => {
      frappe.set_route(TARGET_ROUTE);
    }, 0);
  }

  function render(wrapper) {
    const page = frappe.ui.make_app_page({
      parent: wrapper,
      title: "Sales Console",
      single_column: true,
    });

    const host = page && page.body ? page.body : wrapper;
    if (!host) {
      handoff();
      return;
    }

    host.innerHTML = `
      <div style="padding: 32px 0 24px; display: grid; place-items: center;">
        <div style="
          display: inline-flex;
          align-items: center;
          gap: 10px;
          padding: 14px 18px;
          border-radius: 16px;
          border: 1px solid rgba(203, 213, 225, 0.8);
          background: rgba(255, 255, 255, 0.96);
          color: #0f172a;
          font-size: 13px;
          font-weight: 600;
          box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
        ">
          <span style="
            width: 12px;
            height: 12px;
            border-radius: 999px;
            border: 2px solid rgba(15, 23, 42, 0.16);
            border-top-color: #0f172a;
            display: inline-block;
            animation: sales-console-home-spin 0.8s linear infinite;
          "></span>
          Opening Sales Console
        </div>
      </div>
    `;

    if (!document.getElementById("sales-console-home-style")) {
      const style = document.createElement("style");
      style.id = "sales-console-home-style";
      style.textContent = "@keyframes sales-console-home-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }";
      document.head.appendChild(style);
    }

    handoff();
  }

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) {
    render(wrapper);
  };
  frappe.pages[PAGE_KEY].on_page_show = function () {
    handoff();
  };
})();
