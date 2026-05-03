/* global frappe */

(function () {
  const PAGE_KEY = "procurement-console";
  const METHOD = "erp_workspace_ui.procurement_console.service.get_procurement_console_bootstrap";

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function stateFromPayload(payload, fallbackKind) {
    if (payload && payload.state && payload.state.kind) return payload.state;
    return {
      kind: fallbackKind || "unavailable",
      title: "Procurement Console is not available yet",
      detail: "The buyer workbench is not enabled yet.",
    };
  }

  function renderState(page, payload, fallbackKind) {
    const state = stateFromPayload(payload, fallbackKind);
    const host = page && page.body ? page.body : null;
    if (!host) return;
    host.innerHTML = `
      <section class="procurement-console-placeholder ${escapeHtml(state.kind)}">
        <div class="procurement-console-placeholder-card">
          <p class="procurement-console-kicker">Procurement Console</p>
          <h2>${escapeHtml(state.title)}</h2>
          <p>${escapeHtml(state.detail)}</p>
        </div>
      </section>
    `;
  }

  function ensureStyle() {
    if (document.getElementById("procurement-console-placeholder-style")) return;
    const style = document.createElement("style");
    style.id = "procurement-console-placeholder-style";
    style.textContent = `
      .procurement-console-placeholder {
        min-height: 360px;
        display: grid;
        place-items: center;
        padding: 32px 16px;
      }
      .procurement-console-placeholder-card {
        width: min(720px, 100%);
        border: 1px solid #d8e4f2;
        border-radius: 12px;
        background: #ffffff;
        box-shadow: 0 16px 38px rgba(15, 23, 42, 0.08);
        padding: 24px;
      }
      .procurement-console-placeholder-card h2 {
        margin: 0 0 8px;
        font-size: 22px;
        line-height: 1.2;
        color: #0f172a;
      }
      .procurement-console-placeholder-card p {
        margin: 0;
        color: #64748b;
        font-size: 13px;
        line-height: 1.55;
      }
      .procurement-console-kicker {
        margin: 0 0 10px !important;
        color: #475569 !important;
        font-size: 11px !important;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
      .procurement-console-placeholder.restricted .procurement-console-placeholder-card {
        border-color: #f1d7a8;
      }
    `;
    document.head.appendChild(style);
  }

  function load(page) {
    renderState(page, {
      state: {
        kind: "loading",
        title: "Opening Procurement Console",
        detail: "Checking workspace access.",
      },
    }, "loading");
    frappe.call({
      method: METHOD,
      callback(response) {
        renderState(page, response && response.message, "unavailable");
      },
      error() {
        renderState(page, {
          state: {
            kind: "error",
            title: "Procurement Console could not be opened",
            detail: "The workspace context could not be loaded right now.",
          },
        }, "error");
      },
    });
  }

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) {
    ensureStyle();
    const page = frappe.ui.make_app_page({
      parent: wrapper,
      title: "Procurement Console",
      single_column: true,
    });
    load(page);
  };
  frappe.pages[PAGE_KEY].on_page_show = function (wrapper) {
    ensureStyle();
    const page = frappe.ui.make_app_page({
      parent: wrapper,
      title: "Procurement Console",
      single_column: true,
    });
    load(page);
  };
})();
