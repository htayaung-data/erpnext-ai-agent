/* global frappe */

(function () {
  const PAGE_KEY = "finance-control-desk";
  const OVERVIEW_CONTEXT_METHOD = "erp_workspace_ui.finance_accounting.service.get_finance_control_desk_overview_context";

  function ensureStyle() {
    if (document.getElementById("finance-control-desk-shell-style")) return;

    const style = document.createElement("style");
    style.id = "finance-control-desk-shell-style";
    style.textContent = `
      .finance-control-shell {
        box-sizing: border-box;
        width: min(1120px, calc(100% - 24px));
        margin: 0 auto;
        padding: 8px 0 30px;
        display: grid;
        gap: 16px;
        color: #172033;
      }
      .finance-control-hero {
        border-radius: 18px;
        background: linear-gradient(135deg, #172033 0%, #24434a 60%, #19322e 100%);
        color: #f8fafc;
        padding: 26px 28px 24px;
        box-shadow: 0 22px 50px rgba(20, 35, 54, 0.16);
      }
      .finance-control-hero.is-restricted {
        background: linear-gradient(135deg, #29313f 0%, #3b4654 100%);
      }
      .finance-control-hero.is-unavailable {
        background: linear-gradient(135deg, #263241 0%, #435160 100%);
      }
      .finance-control-hero-top {
        display: flex;
        flex-wrap: wrap;
        align-items: flex-start;
        justify-content: space-between;
        gap: 16px;
      }
      .finance-control-eyebrow {
        margin: 0 0 8px;
        font-size: 11px;
        line-height: 1.3;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #a7f3d0;
      }
      .finance-control-title {
        margin: 0;
        font-size: 30px;
        line-height: 1.08;
        font-weight: 760;
        letter-spacing: 0;
      }
      .finance-control-summary {
        max-width: 760px;
        margin: 10px 0 0;
        font-size: 13px;
        line-height: 1.62;
        color: #dce8ed;
      }
      .finance-control-actions {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
        justify-content: flex-end;
      }
      .finance-control-status,
      .finance-control-refresh {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 30px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 750;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        white-space: nowrap;
      }
      .finance-control-status {
        padding: 0 12px;
        border: 1px solid rgba(167, 243, 208, 0.28);
        background: rgba(167, 243, 208, 0.11);
        color: #dcfce7;
      }
      .finance-control-refresh {
        padding: 0 11px;
        border: 1px solid rgba(226, 232, 240, 0.42);
        background: rgba(255, 255, 255, 0.1);
        color: #f8fafc;
        cursor: pointer;
      }
      .finance-control-refresh:focus-visible {
        outline: 2px solid rgba(167, 243, 208, 0.72);
        outline-offset: 2px;
      }
      .finance-control-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
      }
      .finance-control-panel {
        min-width: 0;
        border: 1px solid rgba(142, 154, 174, 0.24);
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.98);
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
        padding: 17px 18px 16px;
      }
      .finance-control-panel-title {
        margin: 0 0 7px;
        font-size: 14px;
        line-height: 1.3;
        font-weight: 740;
        color: #172033;
      }
      .finance-control-panel-copy {
        margin: 0;
        font-size: 12.5px;
        line-height: 1.55;
        color: #526072;
      }
      .finance-control-chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 14px;
      }
      .finance-control-chip {
        display: inline-flex;
        align-items: center;
        max-width: 100%;
        min-height: 26px;
        padding: 0 10px;
        border-radius: 999px;
        background: #eef8f0;
        color: #1f6f4a;
        font-size: 11px;
        font-weight: 700;
        line-height: 1.35;
      }
      .finance-control-chip.is-muted {
        background: #f4f6f8;
        color: #5d6878;
      }
      .finance-control-list {
        display: grid;
        gap: 10px;
      }
      .finance-control-state-row {
        display: grid;
        grid-template-columns: minmax(140px, 0.32fr) minmax(0, 1fr);
        gap: 12px;
        align-items: start;
        padding: 12px 0;
        border-top: 1px solid #edf0f4;
      }
      .finance-control-state-row:first-child {
        border-top: 0;
        padding-top: 0;
      }
      .finance-control-state-label {
        display: inline-flex;
        width: max-content;
        max-width: 100%;
        min-height: 24px;
        align-items: center;
        border-radius: 999px;
        padding: 0 9px;
        background: #fff7ed;
        color: #9a4f12;
        font-size: 11px;
        font-weight: 750;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }
      .finance-control-state-label.is-ready {
        background: #ecfdf3;
        color: #177245;
      }
      .finance-control-state-label.is-restricted {
        background: #f1f5f9;
        color: #475569;
      }
      .finance-control-state-text {
        min-width: 0;
      }
      .finance-control-state-text strong {
        display: block;
        margin-bottom: 3px;
        font-size: 13px;
        color: #202b3d;
      }
      .finance-control-state-text span {
        display: block;
        font-size: 12.25px;
        line-height: 1.55;
        color: #5d6878;
      }
      .finance-control-boundary {
        border-left: 3px solid #22c55e;
      }
      .finance-control-empty {
        border: 1px dashed #cdd5df;
        border-radius: 10px;
        padding: 14px 15px;
        background: #fbfcfd;
        color: #5a6575;
        font-size: 12.5px;
        line-height: 1.55;
      }
      .finance-control-loading {
        min-height: 180px;
        display: grid;
        align-content: center;
      }
      @media (max-width: 860px) {
        .finance-control-grid {
          grid-template-columns: 1fr;
        }
        .finance-control-state-row {
          grid-template-columns: 1fr;
        }
        .finance-control-actions {
          justify-content: flex-start;
        }
      }
    `;
    document.head.appendChild(style);
  }

  function escapeHtml(value) {
    return String(value === undefined || value === null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function resolveTarget(wrapper) {
    const candidate = wrapper && wrapper.jquery ? wrapper[0] : wrapper;
    if (candidate && candidate.querySelector) {
      return candidate.querySelector(".layout-main-section") || candidate;
    }
    const pageWrapper = frappe.container && frappe.container.page && frappe.container.page.wrapper;
    if (pageWrapper && pageWrapper.querySelector) {
      return pageWrapper.querySelector(".layout-main-section") || pageWrapper;
    }
    return document.getElementById("body");
  }

  function normalizePayload(payload) {
    const safePayload = payload && typeof payload === "object" ? payload : {};
    const state = safePayload.state && typeof safePayload.state === "object" ? safePayload.state : {};
    const scope = safePayload.scope && typeof safePayload.scope === "object" ? safePayload.scope : {};
    const workspace = safePayload.workspace && typeof safePayload.workspace === "object" ? safePayload.workspace : {};
    const noEffect = safePayload.no_effect && typeof safePayload.no_effect === "object" ? safePayload.no_effect : {};
    const overview = safePayload.overview && typeof safePayload.overview === "object" ? safePayload.overview : {};
    const companyScope = safePayload.company_scope && typeof safePayload.company_scope === "object" ? safePayload.company_scope : {};
    const postureCards = Array.isArray(safePayload.posture_cards) ? safePayload.posture_cards : [];
    const lanes = Array.isArray(safePayload.lanes) ? safePayload.lanes : [];
    const rows = Array.isArray(safePayload.rows) ? safePayload.rows : [];

    return {
      workspace,
      state: {
        kind: state.kind || "unavailable",
        title: state.title || "Finance Control Desk is unavailable",
        detail: state.detail || "The Finance overview context could not be loaded.",
      },
      scope,
      overview,
      company_scope: companyScope,
      posture_cards: postureCards,
      lanes,
      rows,
      no_effect: noEffect,
    };
  }

  const FORBIDDEN_COLLECTION_KEYS = new Set([
    "rows",
    "records",
    "documents",
    "metrics",
    "customer_rows",
    "customers",
    "invoice_rows",
    "invoices",
    "voucher_rows",
    "vouchers",
    "account_rows",
    "accounts",
    "payment_ledger_rows",
    "gl_rows",
  ]);

  const FORBIDDEN_IDENTITY_KEYS = new Set([
    "customer",
    "customer_id",
    "customer_name",
    "invoice",
    "invoice_id",
    "invoice_name",
    "voucher",
    "voucher_id",
    "voucher_no",
    "account",
    "account_id",
    "account_name",
    "payment_ledger_entry",
    "payment_ledger_entry_name",
    "gl_entry",
    "gl_entry_name",
    "doctype",
    "docname",
  ]);

  const FORBIDDEN_SURFACE_KEYS = new Set([
    "route",
    "route_options",
    "report",
    "report_name",
    "export",
    "export_url",
    "download",
    "download_url",
    "print",
    "print_url",
    "action",
    "actions",
    "button",
    "buttons",
    "link",
    "links",
    "email",
    "email_sent",
    "email_queue",
    "sendmail",
    "notification",
    "notification_sent",
    "portal",
    "portal_action",
    "portal_action_performed",
    "dunning",
    "payment_request",
    "customer_statement",
    "customer_reminder",
    "customer_action",
    "supplier_action",
    "communication",
    "save",
    "submit",
    "cancel",
    "delete",
    "insert",
    "set_value",
    "enqueue",
    "posting",
    "payment",
    "payment_entry",
    "payment_entry_created",
    "journal_entry",
    "journal_entry_created",
    "gl_entry_created",
    "reconciliation",
    "reconciliation_performed",
    "payment_reconciliation",
    "bank_reconciliation",
    "write_off",
    "tax",
    "tax_filing",
    "tax_filing_performed",
    "close",
    "period_close",
    "period_close_performed",
    "erp_document_created",
    "erp_document_updated",
    "native_route_opened",
    "report_run",
    "row_level_financial_data_returned",
  ]);

  function normalizeKey(key) {
    return String(key || "").replace(/[^a-z0-9]+/gi, "_").replace(/^_+|_+$/g, "").toLowerCase();
  }

  function isEmptyBoundaryValue(value) {
    if (value === undefined || value === null || value === false || value === "") {
      return true;
    }
    if (Array.isArray(value)) {
      return value.length === 0;
    }
    if (value && typeof value === "object") {
      return Object.keys(value).length === 0;
    }
    return false;
  }

  function hasForbiddenFinancePayloadShape(value) {
    if (!value || typeof value !== "object") {
      return false;
    }
    if (Array.isArray(value)) {
      return value.some((item) => hasForbiddenFinancePayloadShape(item));
    }
    return Object.entries(value).some(([key, nested]) => {
      const normalizedKey = normalizeKey(key);
      if (FORBIDDEN_COLLECTION_KEYS.has(normalizedKey)) {
        return !isEmptyBoundaryValue(nested);
      }
      if (FORBIDDEN_IDENTITY_KEYS.has(normalizedKey) || FORBIDDEN_SURFACE_KEYS.has(normalizedKey)) {
        return !isEmptyBoundaryValue(nested);
      }
      return hasForbiddenFinancePayloadShape(nested);
    });
  }

  function financeDataBoundaryPayload(payload) {
    const safePayload = payload && typeof payload === "object" ? payload : {};
    return {
      overview: safePayload.overview,
      receivables_posture: safePayload.receivables_posture,
      receivables_amount_summary: safePayload.receivables_amount_summary,
      company_scope: safePayload.company_scope,
      period_scope: safePayload.period_scope,
      posture_cards: safePayload.posture_cards,
      lanes: safePayload.lanes,
      rows: safePayload.rows,
      metrics: safePayload.metrics,
      amounts: safePayload.amounts,
      documents: safePayload.documents,
      no_effect: safePayload.no_effect,
    };
  }

  function hasFinancialRows(payload) {
    return hasForbiddenFinancePayloadShape(payload);
  }

  function allNoEffectFlagsFalse(noEffect) {
    return Object.keys(noEffect || {}).every((key) => noEffect[key] === false);
  }

  function boundaryChips(payload) {
    const chips = [
      "No row-level data shown",
      "Aggregate source reads only",
      "No report calls",
      "No native execution routes",
    ];
    if (payload.scope && payload.scope.execution_enabled === false) {
      chips.push("Execution disabled");
    }
    if (payload.no_effect && payload.no_effect.export_generated === false) {
      chips.push("Exports blocked");
    }
    return chips.map((chip, index) => `<span class="finance-control-chip${index > 3 ? " is-muted" : ""}">${escapeHtml(chip)}</span>`).join("");
  }

  function renderHero(payload, variant, summary, statusLabel) {
    const workspace = payload.workspace || {};
    const title = workspace.title || "Finance Control Desk";
    const family = workspace.workspace_family || "Finance & Accounting";
    const safeVariant = variant ? ` ${variant}` : "";
    return `
      <section class="finance-control-hero${safeVariant}" aria-label="Finance Control Desk foundation">
        <div class="finance-control-hero-top">
          <div>
            <p class="finance-control-eyebrow">${escapeHtml(family)}</p>
            <h1 class="finance-control-title">${escapeHtml(title)}</h1>
            <p class="finance-control-summary">${escapeHtml(summary)}</p>
          </div>
          <div class="finance-control-actions">
            <span class="finance-control-status">${escapeHtml(statusLabel)}</span>
            <button class="finance-control-refresh" type="button" data-finance-refresh="1" aria-label="Refresh Finance overview context">Refresh</button>
          </div>
        </div>
        <div class="finance-control-chip-row" aria-label="Finance boundary summary">
          ${boundaryChips(payload)}
        </div>
      </section>
    `;
  }

  function renderReady(payload) {
    const lanes = (payload.posture_cards.length ? payload.posture_cards : payload.lanes).slice(0, 6);
    const laneCards = lanes.map((lane) => `
      <article class="finance-control-panel" data-finance-posture-key="${escapeHtml(lane.key || "posture")}">
        <h2 class="finance-control-panel-title">${escapeHtml(lane.title || "Finance posture")}</h2>
        <p class="finance-control-panel-copy">${escapeHtml(lane.detail || "This posture is not active for this read-only phase.")}</p>
        <div class="finance-control-chip-row" aria-label="${escapeHtml(lane.title || "Posture")} state">
          <span class="finance-control-chip${lane.state === "ready" ? "" : " is-muted"}">${escapeHtml(lane.value || lane.state || "Unavailable")}</span>
        </div>
      </article>
    `).join("");
    const noRowsCopy = hasFinancialRows(payload)
      ? "Policy violation: row-level financial data was returned to this page. The page blocks rendering, linking, export, and action surfaces for that response, and this response must not be accepted for manual review."
      : "Finance overview shows scoped aggregate posture only. The backend may perform bounded aggregate source reads, but row-level accounting data is not returned, shown, linked, exported, or actionable. Approved managers may see aggregate receivables count buckets and MMK amount buckets when all gates pass.";
    const noEffectCopy = allNoEffectFlagsFalse(payload.no_effect)
      ? "The backend context reports no document, ledger, payment, reconciliation, tax, notification, or export effect."
      : "The shell treats this response as display-only and does not expose execution controls.";
    const overviewCopy = payload.overview && payload.overview.detail
      ? payload.overview.detail
      : "Company-scoped posture only. Approved managers may see aggregate receivables count buckets and MMK amount buckets when all gates pass; row-level data, reports, exports, and execution remain blocked.";

    return `
      <main class="finance-control-shell" data-erpw-workspace="finance" data-finance-f3-overview="ready">
        ${renderHero(
          payload,
          "",
          overviewCopy,
          "Read-only overview"
        )}

        <section class="finance-control-grid" aria-label="Finance accounting overview posture">
          ${laneCards || `
            <article class="finance-control-panel">
              <h2 class="finance-control-panel-title">Overview posture unavailable</h2>
              <p class="finance-control-panel-copy">The overview context returned no posture lanes for this phase.</p>
            </article>
          `}
        </section>

        <section class="finance-control-panel" aria-label="Accounting overview posture">
          <h2 class="finance-control-panel-title">Overview posture</h2>
          <div class="finance-control-list">
            <div class="finance-control-state-row">
              <div class="finance-control-state-label is-ready">${escapeHtml(payload.state.title || "Shell registered")}</div>
              <div class="finance-control-state-text">
                <strong>Read-only overview ready</strong>
                <span>${escapeHtml(payload.state.detail || "The Finance & Accounting route renders scoped aggregate posture without returning, showing, linking, exporting, or making row-level accounting data actionable.")}</span>
              </div>
            </div>
            <div class="finance-control-state-row">
              <div class="finance-control-state-label">Unavailable</div>
              <div class="finance-control-state-text">
                <strong>Payables, cash, and ledger rows are not active</strong>
                <span>Those lanes reopen only after field allowlists, company scope rules, and role visibility are approved. Receivables is limited to aggregate count buckets and manager-only MMK amount buckets when all gates pass.</span>
              </div>
            </div>
            <div class="finance-control-state-row">
              <div class="finance-control-state-label">No effect</div>
              <div class="finance-control-state-text">
                <strong>Overview context only</strong>
                <span>${escapeHtml(noEffectCopy)}</span>
              </div>
            </div>
          </div>
        </section>

        <section class="finance-control-panel finance-control-boundary" aria-label="No row-level financial data shown">
          <h2 class="finance-control-panel-title">Finance overview shows no row-level financial data</h2>
          <div class="finance-control-empty">${escapeHtml(noRowsCopy)}</div>
        </section>
      </main>
    `;
  }

  function renderPolicyViolation(payload) {
    const violationPayload = normalizePayload({
      workspace: payload.workspace,
      state: {
        kind: "unavailable",
        title: "Finance response blocked",
        detail: "The Finance overview response contained row-level, identity, route, report, export, print, download, or action-shaped data. The page blocked ready rendering for this response.",
      },
      scope: { financial_data_enabled: false, execution_enabled: false },
      no_effect: payload.no_effect,
      rows: [],
      lanes: [],
    });
    return `
      <main class="finance-control-shell" data-erpw-workspace="finance" data-finance-f3-overview="unavailable">
        ${renderHero(violationPayload, "is-unavailable", violationPayload.state.detail, "Blocked")}
        <section class="finance-control-panel finance-control-boundary" aria-label="Finance response blocked">
          <h2 class="finance-control-panel-title">Policy violation blocked</h2>
          <p class="finance-control-panel-copy">No row-level data, identities, native routes, reports, exports, downloads, print surfaces, or action controls are rendered from this response.</p>
        </section>
      </main>
    `;
  }

  function renderRestricted(payload) {
    return `
      <main class="finance-control-shell" data-erpw-workspace="finance" data-finance-f3-overview="restricted">
        ${renderHero(
          payload,
          "is-restricted",
          payload.state.detail || "This shell is limited to approved accounting, audit, or system roles.",
          "Restricted"
        )}
        <section class="finance-control-panel finance-control-boundary" aria-label="Finance access restricted">
          <h2 class="finance-control-panel-title">${escapeHtml(payload.state.title || "Finance Control Desk is restricted")}</h2>
          <p class="finance-control-panel-copy">The Finance overview is not shown for this role. No row-level financial data, metrics, reports, exports, or execution routes are returned or shown.</p>
        </section>
      </main>
    `;
  }

  function renderLoading() {
    const payload = normalizePayload({
      workspace: { title: "Finance Control Desk", workspace_family: "Finance & Accounting" },
      state: { kind: "loading", title: "Loading Finance overview", detail: "Loading the role-aware Finance overview context." },
      scope: { financial_data_enabled: false, execution_enabled: false },
      no_effect: { row_level_financial_data_returned: false, export_generated: false },
      rows: [],
      lanes: [],
    });
    return `
      <main class="finance-control-shell finance-control-loading" data-erpw-workspace="finance" data-finance-f3-overview="loading">
        ${renderHero(payload, "is-unavailable", payload.state.detail, "Loading")}
      </main>
    `;
  }

  function renderUnavailable(message) {
    const payload = normalizePayload({
      workspace: { title: "Finance Control Desk", workspace_family: "Finance & Accounting" },
      state: {
        kind: "unavailable",
        title: "Finance Control Desk is unavailable",
        detail: message || "The Finance overview context could not be reached. No row-level financial data or execution controls are available.",
      },
      scope: { financial_data_enabled: false, execution_enabled: false },
      no_effect: { row_level_financial_data_returned: false, export_generated: false },
      rows: [],
      lanes: [],
    });
    return `
      <main class="finance-control-shell" data-erpw-workspace="finance" data-finance-f3-overview="unavailable">
        ${renderHero(payload, "is-unavailable", payload.state.detail, "Unavailable")}
        <section class="finance-control-panel finance-control-boundary" aria-label="Finance overview unavailable">
          <h2 class="finance-control-panel-title">Controlled unavailable state</h2>
          <p class="finance-control-panel-copy">Refresh reloads only the overview context. It does not call accounting reports, return row-level financial data, export files, or open native execution routes.</p>
        </section>
      </main>
    `;
  }

  function renderPayload(payload) {
    const rawPayloadHasFinancialRows = hasFinancialRows(financeDataBoundaryPayload(payload));
    const normalized = normalizePayload(payload);
    if (rawPayloadHasFinancialRows || hasFinancialRows(normalized)) {
      return renderPolicyViolation(normalized);
    }
    if (normalized.state.kind === "restricted") {
      return renderRestricted(normalized);
    }
    if (normalized.state.kind !== "ready") {
      return renderUnavailable(normalized.state.detail);
    }
    return renderReady(normalized);
  }

  function callOverviewContext() {
    return new Promise((resolve, reject) => {
      if (!frappe || typeof frappe.call !== "function") {
        reject(new Error("Frappe call API unavailable"));
        return;
      }
      frappe.call({
        method: OVERVIEW_CONTEXT_METHOD,
        callback(response) {
          resolve(response && response.message ? response.message : {});
        },
        error(error) {
          reject(error || new Error("Finance overview context failed"));
        },
      });
    });
  }

  function bindRefresh(target) {
    const refresh = target.querySelector("[data-finance-refresh]");
    if (!refresh) return;
    refresh.addEventListener("click", () => loadOverviewContext(target, { forceLoading: true }));
  }

  function setHtml(target, html) {
    if (!target || target === document.body || target.id === "body") return;
    target.innerHTML = html;
    bindRefresh(target);
  }

  function loadOverviewContext(target, options) {
    ensureStyle();
    const opts = options || {};
    if (!target || target === document.body || target.id === "body") return;
    if (opts.forceLoading || !target.__financeControlDeskOverviewPayload) {
      setHtml(target, renderLoading());
    }
    callOverviewContext()
      .then((payload) => {
        target.__financeControlDeskOverviewPayload = payload;
        setHtml(target, renderPayload(payload));
      })
      .catch(() => {
        target.__financeControlDeskOverviewPayload = null;
        setHtml(target, renderUnavailable());
      });
  }

  function render(wrapper) {
    const target = resolveTarget(wrapper);
    if (!target || target === document.body || target.id === "body") return;
    if (target.__financeControlDeskInitialized && target.__financeControlDeskOverviewPayload) {
      setHtml(target, renderPayload(target.__financeControlDeskOverviewPayload));
      return;
    }
    target.__financeControlDeskInitialized = true;
    loadOverviewContext(target);
  }

  const pageDef = frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  pageDef.on_page_load = render;
  pageDef.on_page_show = render;
})();