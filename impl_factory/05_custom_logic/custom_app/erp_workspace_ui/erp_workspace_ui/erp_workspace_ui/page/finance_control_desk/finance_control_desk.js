/* global frappe */

(function () {
  const PAGE_KEY = "finance-control-desk";
  const OVERVIEW_CONTEXT_METHOD = "erp_workspace_ui.finance_accounting.service.get_finance_control_desk_overview_context";
  const OVERVIEW_CONTEXT_TIMEOUT_MS = 30000;

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
      .finance-control-freshness {
        margin: 8px 0 0;
        font-size: 11.5px;
        line-height: 1.45;
        color: #b9cbd2;
        font-variant-numeric: tabular-nums;
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

  function resolvePageWrapper(wrapper) {
    const candidate = wrapper && wrapper.jquery ? wrapper[0] : wrapper;
    if (candidate && candidate.querySelector) return candidate;
    const pageWrapper = frappe && frappe.container && frappe.container.page;
    if (pageWrapper && pageWrapper.querySelector) return pageWrapper;
    return null;
  }

  function resolveTarget(wrapper) {
    const pageWrapper = resolvePageWrapper(wrapper);
    if (pageWrapper) return pageWrapper.querySelector(".layout-main-section") || pageWrapper;
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
    const postureDates = [
      safePayload.receivables_posture && safePayload.receivables_posture.as_of_date,
      safePayload.receivables_amount_summary && safePayload.receivables_amount_summary.as_of_date,
      safePayload.payables_count_posture && safePayload.payables_count_posture.as_of_date,
    ].filter((value) => typeof value === "string" && value);
    const asOfDate = postureDates.length ? postureDates[0] : "";
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
      as_of_date: asOfDate,
      fetched_at: typeof safePayload.fetched_at === "string" ? safePayload.fetched_at : "",
    };
  }

  const RECEIVABLES_UNAVAILABLE_FALLBACK = "Receivables posture is unavailable. Aggregate receivables counts and manager-only amount posture are not shown. No customer, invoice, voucher, account, report, export, or action data is shown.";
  const FINANCE_UNAVAILABLE_FALLBACK = "This read-only Finance posture is unavailable. No row-level data, native reports, exports, or execution actions are shown.";

  const FORBIDDEN_RENDERED_VALUE_PATTERNS = Object.freeze([
    /(?:^|[^A-Za-z0-9])(?:CUST|SINV|PINV|PLE|GLE|PE|JV|ACC|SUPP)-[A-Za-z0-9-]+(?:$|[^A-Za-z0-9])/i,
    /(?:\/(?:app|desk)\/|query[-_]report|https?:\/\/|frappe\.)/i,
    /^\s*(?:submit|cancel|reconcile|write\s*off|export|download|print|create|new\s+document)\b/i,
  ]);

  function isBusinessSafeText(value) {
    if (typeof value !== "string" || FORBIDDEN_RENDERED_VALUE_PATTERNS.some((pattern) => pattern.test(value))) return false;
    return !value.split(/[^A-Za-z0-9_]+/).filter(Boolean).some((token) => (
      token.includes("_")
      || /[a-z0-9][A-Z]/.test(token)
      || /^[A-Z]{2,}[A-Z][a-z]/.test(token)
    ));
  }

  function businessSafeText(value, fallback) {
    const text = typeof value === "string" ? value.trim() : "";
    return text && isBusinessSafeText(text) ? text : fallback;
  }

  function visibleLaneDetail(lane) {
    const safeLane = lane && typeof lane === "object" ? lane : {};
    const detail = String(safeLane.detail || "");
    if (!isBusinessSafeText(detail)) {
      if (safeLane.key === "receivables_posture") return RECEIVABLES_UNAVAILABLE_FALLBACK;
      if (safeLane.key === "payables_posture") {
        return "Payables aggregate count posture is unavailable until the approved manager, company, source, and permission gates pass. No supplier, invoice, payment, bank, report, export, or action data is shown.";
      }
      return FINANCE_UNAVAILABLE_FALLBACK;
    }
    return detail || "This posture is not active for this read-only phase.";
  }

  function visibleUnavailableMessage() {
    return "The Finance overview is temporarily unavailable. No row-level financial data, native reports, exports, or execution controls are shown.";
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
    "supplier_rows",
    "suppliers",
    "purchase_invoice_rows",
    "purchase_invoices",
    "payment_entry_rows",
    "payment_entries",
    "payment_schedule_rows",
    "payment_schedules",
    "bank_account_rows",
    "bank_accounts",
    "bank_transaction_rows",
    "bank_transactions",
    "bank_reference_rows",
    "bank_references",
    "bank_detail_rows",
    "bank_details",
    "bank_rows",
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
    "payment_schedule",
    "payment_schedule_id",
    "payment_schedule_name",
    "payment_schedule_parent",
    "payment_schedule_parent_name",
    "supplier",
    "supplier_id",
    "supplier_name",
    "supplier_group",
    "supplier_bank_account",
    "supplier_bank_details",
    "supplier_contact",
    "supplier_tax_id",
    "bank",
    "bank_id",
    "bank_name",
    "bank_account",
    "bank_account_id",
    "bank_account_name",
    "bank_account_no",
    "bank_account_number",
    "bank_account_details",
    "bank_party_account",
    "bank_party_account_id",
    "bank_party_account_number",
    "bank_transaction",
    "bank_transaction_id",
    "bank_transaction_name",
    "bank_transaction_reference",
    "bank_transaction_reference_number",
    "bank_reference",
    "bank_reference_id",
    "bank_reference_no",
    "bank_reference_number",
    "transaction_id",
    "transaction_name",
    "reference",
    "reference_id",
    "reference_no",
    "reference_number",
    "bank_detail",
    "bank_details",
    "iban",
    "iban_number",
    "swift",
    "swift_code",
    "swift_number",
    "swift_bic",
    "bank_swift",
    "bank_swift_code",
    "bic",
    "bic_code",
    "routing_number",
    "branch_code",
    "purchase_invoice",
    "purchase_invoice_id",
    "purchase_invoice_name",
    "bill_no",
    "bill_date",
    "payable_account",
    "party",
    "party_id",
    "party_name",
    "remarks",
    "payment_order",
    "payment_order_id",
    "doctype",
    "docname",
    "customer_code",
    "invoice_number",
    "ple_name",
    "ple_rows",
    "gl_name",
  ]);

  const FORBIDDEN_PAYABLES_VALUE_KEYS = new Set([
    "amount",
    "amounts",
    "bucket_amounts",
    "grand_total",
    "outstanding_amount",
    "payment_amount",
    "base_amount",
    "currency",
    "currencies",
    "account_currency",
    "party_currency",
    "supplier_balance",
    "ap_balance",
    "cash_requirement",
  ]);

  const FORBIDDEN_PAYABLES_VALUE_KEY_TOKENS = new Set([
    "amount",
    "amounts",
    "balance",
    "balances",
    "currency",
    "currencies",
    "outstanding",
    "rate",
    "rates",
    "total",
    "totals",
    "value",
    "values",
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
    "routes",
    "reports",
    "exports",
    "downloads",
    "execution",
    "executions",
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
    "supplier_notification",
    "supplier_statement",
    "supplier_payment_communication",
    "payment_order_created",
    "payment_request",
    "payment_request_created",
    "payment_run",
    "payment_run_performed",
    "purchase_invoice_lifecycle_performed",
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
    "native_url",
    "execute_action",
    "erp_document_created",
    "erp_document_updated",
    "native_route_opened",
    "report_run",
    "row_level_financial_data_returned",
  ]);

  const FORBIDDEN_FINANCIAL_KEY_PATTERNS = Object.freeze([
    /^(?:gl|ple|ap|ar)(?:_?\d+)?_(?:rows?|entries?|balance|balances|amount|amounts|identity|identities)$/,
    /^(?:customer|supplier|invoice|voucher|account)(?:_?\d+)?_(?:rows?|identity|identities)$/,
  ]);

  function normalizeKey(key) {
    return String(key || "")
      .replace(/([A-Z]+)([A-Z][a-z])/g, "$1_$2")
      .replace(/([a-z0-9])([A-Z])/g, "$1_$2")
      .replace(/[^a-z0-9]+/gi, "_")
      .replace(/^_+|_+$/g, "")
      .toLowerCase();
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
      const forbiddenPattern = FORBIDDEN_FINANCIAL_KEY_PATTERNS.some((pattern) => pattern.test(normalizedKey));
      if (
        FORBIDDEN_COLLECTION_KEYS.has(normalizedKey)
        || FORBIDDEN_IDENTITY_KEYS.has(normalizedKey)
        || FORBIDDEN_SURFACE_KEYS.has(normalizedKey)
        || forbiddenPattern
      ) {
        return !isEmptyBoundaryValue(nested);
      }
      return hasForbiddenFinancePayloadShape(nested);
    });
  }

  function isForbiddenPayablesValueKey(key) {
    const normalizedKey = normalizeKey(key);
    return FORBIDDEN_PAYABLES_VALUE_KEYS.has(normalizedKey)
      || normalizedKey.split("_").some((token) => FORBIDDEN_PAYABLES_VALUE_KEY_TOKENS.has(token));
  }

  function hasForbiddenPayablesPayloadShape(value) {
    if (!value || typeof value !== "object") {
      return false;
    }
    if (Array.isArray(value)) {
      return value.some((item) => hasForbiddenPayablesPayloadShape(item));
    }
    return Object.entries(value).some(([key, nested]) => {
      if (isForbiddenPayablesValueKey(key)) {
        return !isEmptyBoundaryValue(nested);
      }
      return hasForbiddenPayablesPayloadShape(nested);
    });
  }

  function financeDataBoundaryPayload(payload) {
    const safePayload = payload && typeof payload === "object" ? payload : {};
    return {
      overview: safePayload.overview,
      receivables_posture: safePayload.receivables_posture,
      receivables_amount_summary: safePayload.receivables_amount_summary,
      payables_count_posture: safePayload.payables_count_posture,
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

  function hasForbiddenRawFinancePayload(payload) {
    const safePayload = payload && typeof payload === "object" ? payload : {};
    return hasForbiddenFinancePayloadShape(safePayload)
      || hasForbiddenPayablesPayloadShape(safePayload.payables_count_posture);
  }

  const FINANCE_OVERVIEW_SCHEMA_VERSION = "finance-overview.v1";
  const FINANCE_BUCKET_KEYS = Object.freeze(["current", "overdue_1_30", "overdue_31_60", "overdue_61_90", "overdue_over_90"]);
  const PAYABLES_BUCKET_KEYS = Object.freeze(["not_due", "overdue_1_30", "overdue_31_60", "overdue_61_90", "overdue_over_90"]);
  const FINANCE_BUCKET_LABELS = Object.freeze({
    current: "Current / not due",
    overdue_1_30: "1-30 overdue",
    overdue_31_60: "31-60 overdue",
    overdue_61_90: "61-90 overdue",
    overdue_over_90: ">90 overdue",
  });
  const PAYABLES_BUCKET_LABELS = Object.freeze({
    not_due: "Current / not overdue",
    overdue_1_30: "1-30 overdue",
    overdue_31_60: "31-60 overdue",
    overdue_61_90: "61-90 overdue",
    overdue_over_90: ">90 overdue",
  });
  const TOP_LEVEL_KEYS = Object.freeze([
    "schema_version", "workspace", "scope", "state", "overview", "receivables_posture",
    "receivables_amount_summary", "payables_count_posture", "company_scope", "period_scope",
    "posture_cards", "lanes", "metrics", "amounts", "documents", "rows", "no_effect", "fetched_at",
  ]);
  const NO_EFFECT_KEYS = Object.freeze([
    "erp_document_created", "erp_document_updated", "gl_entry_created", "journal_entry_created",
    "payment_entry_created", "reconciliation_performed", "tax_filing_performed", "period_close_performed",
    "notification_sent", "export_generated", "row_level_financial_data_returned", "native_route_opened",
    "report_run", "email_sent", "portal_action_performed", "supplier_notification_sent",
    "supplier_statement_sent", "supplier_payment_communication_sent", "payment_request_created",
    "payment_order_created", "payment_run_performed", "supplier_bank_or_contact_exposed",
    "purchase_invoice_lifecycle_performed", "user_or_role_mutated",
  ]);
  const COUNT_POLICY_KEYS = Object.freeze([
    "source", "reason", "resolver_state", "resolver_source", "role_category", "policy_contract_accepted",
    "resolver_scoped", "role_eligible_for_count_policy", "source_permission_checked", "source_permission_verified",
    "future_activity_source_permission_checked", "future_activity_source_permission_verified", "source_read_policy_ready",
    "runtime_count_enabled", "low_count_suppression_ready", "manager_aggregate_counts_only", "count_source",
    "semantic_guard_sources", "payment_schedule_supported", "payment_schedule_presence_gate_required",
    "future_posting_supported", "future_payment_ledger_activity_supported", "accounts_user_raw_counts_enabled",
    "identifiers_enabled", "monetary_values_enabled", "native_navigation_enabled", "external_output_enabled", "execution_enabled",
  ]);
  const AMOUNT_POLICY_KEYS = Object.freeze([
    "source", "reason", "resolver_state", "resolver_source", "role_category", "source_permission_checked",
    "source_permission_verified", "source_metadata_checked", "source_metadata_verified", "runtime_amount_summary_enabled",
    "manager_only", "company_currency", "currency_precision_verified", "currency_precision", "currency_precision_source",
    "currency_rounding_method", "amount_serialization", "payment_terms_supported", "payment_terms_detection",
    "payment_schedule_rows_read", "split_payment_terms_fail_closed", "aging_date_basis", "posting_date_fallback_enabled",
    "split_receivable_accounts_supported", "voucher_set_reconciliation", "voucher_set_reconciliation_verified",
    "voucher_identities_returned", "credit_returns_supported", "minimum_voucher_population", "minimum_diversity_population",
    "identifiers_enabled", "native_navigation_enabled", "external_output_enabled", "execution_enabled",
  ]);
  const PAYABLES_POLICY_KEYS = Object.freeze([
    "source", "reason", "resolver_state", "resolver_source", "role_category", "source_permission_checked",
    "source_permission_verified", "source_read_policy_ready", "runtime_count_enabled", "manager_only",
    "accounts_user_counts_enabled", "aggregate_counts_only", "due_date_basis_only", "posting_date_fallback_enabled",
    "due_soon_enabled", "payment_terms_supported", "payment_schedule_supported", "payment_schedule_presence_gate_required",
    "payment_schedule_rows_returned", "on_hold_supported", "returns_supported", "identifiers_enabled",
    "monetary_values_enabled", "native_navigation_enabled", "external_output_enabled", "execution_enabled",
  ]);
  const POLICY_STRING_KEYS = new Set([
    "source", "reason", "resolver_state", "resolver_source", "role_category", "count_source",
    "company_currency", "amount_serialization",
    "payment_terms_detection", "aging_date_basis", "voucher_set_reconciliation",
  ]);
  const POLICY_STRING_OR_NULL_KEYS = new Set([
    "currency_precision_source", "currency_rounding_method",
  ]);
  const POLICY_INTEGER_OR_NULL_KEYS = new Set([
    "currency_precision", "minimum_voucher_population", "minimum_diversity_population",
  ]);

  function isPlainObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
  }

  function hasExactKeys(value, expectedKeys, optionalKeys) {
    if (!isPlainObject(value)) return false;
    const required = new Set(expectedKeys || []);
    const optional = new Set(optionalKeys || []);
    const keys = Object.keys(value);
    return Array.from(required).every((key) => Object.prototype.hasOwnProperty.call(value, key))
      && keys.every((key) => required.has(key) || optional.has(key));
  }

  function isEmptyArray(value) {
    return Array.isArray(value) && value.length === 0;
  }

  function validateNoEffect(value) {
    return hasExactKeys(value, NO_EFFECT_KEYS)
      && NO_EFFECT_KEYS.every((key) => value[key] === false);
  }

  function validateBucketLabels(value, expectedKeys) {
    const expectedLabels = expectedKeys === FINANCE_BUCKET_KEYS ? FINANCE_BUCKET_LABELS : PAYABLES_BUCKET_LABELS;
    return Array.isArray(value)
      && value.length === expectedKeys.length
      && value.every((item, index) => hasExactKeys(item, ["key", "label"])
        && item.key === expectedKeys[index]
        && item.label === expectedLabels[item.key]);
  }

  function validateBucketCounts(value, expectedKeys, ready) {
    if (!isPlainObject(value)) return false;
    if (!ready) return Object.keys(value).length === 0;
    return hasExactKeys(value, expectedKeys)
      && expectedKeys.every((key) => Number.isInteger(value[key]) && value[key] >= 0);
  }

  function validatePolicy(value, keys) {
    if (!hasExactKeys(value, keys) || typeof value.reason !== "string") return false;
    const valuesValid = Object.entries(value).every(([key, item]) => {
      if (key === "semantic_guard_sources") {
        return Array.isArray(item)
          && item.length > 0
          && item.every((source) => typeof source === "string" && source.length > 0);
      }
      if (POLICY_STRING_KEYS.has(key)) return typeof item === "string";
      if (POLICY_STRING_OR_NULL_KEYS.has(key)) return item === null || typeof item === "string";
      if (POLICY_INTEGER_OR_NULL_KEYS.has(key)) {
        return item === null || (typeof item === "number" && Number.isInteger(item) && Number.isFinite(item));
      }
      return typeof item === "boolean";
    });
    return valuesValid
      && value.identifiers_enabled === false
      && value.native_navigation_enabled === false
      && value.external_output_enabled === false
      && value.execution_enabled === false;
  }
  function validateReceivablesCountPolicyTruth(value) {
    return value.source === "Sales Invoice"
      && value.count_source === "Sales Invoice"
      && JSON.stringify(value.semantic_guard_sources) === JSON.stringify(["Payment Schedule", "Payment Ledger Entry"])
      && value.low_count_suppression_ready === false
      && value.manager_aggregate_counts_only === true
      && value.payment_schedule_supported === false
      && value.payment_schedule_presence_gate_required === true
      && value.future_posting_supported === false
      && value.future_payment_ledger_activity_supported === false
      && value.accounts_user_raw_counts_enabled === false
      && value.monetary_values_enabled === false;
  }

  function validateReceivablesAmountPolicyTruth(value) {
    return value.source === "Payment Ledger Entry"
      && value.manager_only === true
      && value.company_currency === "MMK"
      && value.payment_terms_supported === false
      && value.payment_terms_detection === "sales_invoice_schedule_gate_and_payment_ledger_due_date_consistency"
      && value.payment_schedule_rows_read === false
      && value.split_payment_terms_fail_closed === true
      && value.aging_date_basis === "due_date_only"
      && value.posting_date_fallback_enabled === false
      && value.split_receivable_accounts_supported === false
      && value.voucher_set_reconciliation === "account_voucher_type_voucher_party"
      && value.voucher_set_reconciliation_verified === value.runtime_amount_summary_enabled
      && value.voucher_identities_returned === false
      && value.credit_returns_supported === false
      && value.minimum_voucher_population === 3
      && value.minimum_diversity_population === 3;
  }

  function validatePayablesPolicyTruth(value) {
    return value.source === "Purchase Invoice"
      && value.manager_only === true
      && value.accounts_user_counts_enabled === false
      && value.aggregate_counts_only === true
      && value.due_date_basis_only === true
      && value.posting_date_fallback_enabled === false
      && value.due_soon_enabled === false
      && value.payment_terms_supported === false
      && value.payment_schedule_supported === false
      && value.payment_schedule_presence_gate_required === true
      && value.payment_schedule_rows_returned === false
      && value.on_hold_supported === false
      && value.returns_supported === false
      && value.monetary_values_enabled === false;
  }

  function isValidCalendarDate(value) {
    if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
    const [year, month, day] = value.split("-").map(Number);
    const parsed = new Date(Date.UTC(year, month - 1, day));
    return year >= 1000 && parsed.getUTCFullYear() === year && parsed.getUTCMonth() === month - 1 && parsed.getUTCDate() === day;
  }

  function isValidTimestamp(value) {
    if (typeof value !== "string") return false;
    const match = value.match(/^(\d{4}-\d{2}-\d{2})[ T](\d{2}):(\d{2}):(\d{2})(?:\.\d{1,6})?$/);
    return Boolean(match) && isValidCalendarDate(match[1])
      && Number(match[2]) <= 23 && Number(match[3]) <= 59 && Number(match[4]) <= 59;
  }


  function validateStringFields(value, keys, options) {
    if (!hasExactKeys(value, keys)) return false;
    const opts = options || {};
    return keys.every((key) => {
      if (opts.booleanKeys && opts.booleanKeys.includes(key)) return typeof value[key] === "boolean";
      return typeof value[key] === "string";
    });
  }

  const WORKSPACE_COPY_CONTRACT = Object.freeze({
    workspace_id: "finance",
    status: "cycle_1_f6_quality_gate_pending",
    title: "Finance Control Desk",
    workspace_family: "Finance & Accounting",
    mode_label: "Read-only aggregate posture",
  });
  const OVERVIEW_STATE_COPY_CONTRACT = Object.freeze({
    ready: Object.freeze({
      title: "Read-only accounting overview is ready",
      detail: "Scoped posture shows aggregate data only: no document rows, reports, exports, or execution routes.",
    }),
    unavailable: Object.freeze({
      title: "Company scope is required",
      detail: "Finance posture requires an approved company scope. Personal defaults do not grant financial visibility.",
    }),
    restricted: Object.freeze({
      title: "Finance Control Desk is restricted",
      detail: "This shell is limited to approved accounting, audit, or system roles.",
    }),
  });
  const OVERVIEW_COPY_CONTRACT = Object.freeze({
    phase: "finance_cycle_1_aggregate_posture",
    title: "Read-only accounting posture",
    detail: "Company-scoped posture only. Receivables and Payables signals are aggregate-only when their gates pass; row-level data, reports, exports, and execution remain blocked.",
  });
  const COMPANY_SCOPE_COPY_CONTRACT = Object.freeze({
    scoped: Object.freeze([Object.freeze({
      title: "Company scope active",
      detail: "Finance posture is limited to the approved company shown here.",
    })]),
    selection_required: Object.freeze([Object.freeze({
      title: "Company selection required",
      detail: "Multiple allowed companies require an approved server-side selection before Finance posture loads.",
    })]),
    restricted: Object.freeze([
      Object.freeze({
        title: "Company scope restricted",
        detail: "Finance overview requires an approved accounting or audit role.",
      }),
      Object.freeze({
        title: "Company scope restricted",
        detail: "Your Finance role does not provide an approved company scope.",
      }),
    ]),
    unavailable: Object.freeze([Object.freeze({
      title: "Company scope unavailable",
      detail: "Finance posture is unavailable until an approved company scope is available.",
    })]),
  });
  const PERIOD_SCOPE_COPY_CONTRACT = Object.freeze([
    Object.freeze({
      state: "unavailable",
      title: "Period posture unavailable",
      detail: "Fiscal and period posture waits for an approved company scope.",
    }),
    Object.freeze({
      state: "unavailable",
      title: "Fiscal period posture deferred",
      detail: "Fiscal calendars and close records remain deferred until the owner approves the period policy.",
    }),
  ]);

  function exactCopyMatch(value, expected, keys) {
    return keys.every((key) => value[key] === expected[key]);
  }

  function validateWorkspace(value) {
    const keys = ["workspace_id", "status", "title", "workspace_family", "mode_label"];
    return validateStringFields(value, keys)
      && exactCopyMatch(value, WORKSPACE_COPY_CONTRACT, keys);
  }

  function validateOverviewState(value) {
    if (!validateStringFields(value, ["kind", "title", "detail"])) return false;
    const expected = OVERVIEW_STATE_COPY_CONTRACT[value.kind];
    return !!expected && exactCopyMatch(value, expected, ["title", "detail"]);
  }

  function validateOverviewCopy(value) {
    const keys = ["phase", "title", "detail"];
    return validateStringFields(value, keys)
      && exactCopyMatch(value, OVERVIEW_COPY_CONTRACT, keys);
  }

  function validateCompanyScope(value) {
    const keys = ["state", "source", "company", "company_label", "currency", "title", "detail"];
    if (!hasExactKeys(value, keys)) return false;
    const copyOptions = COMPANY_SCOPE_COPY_CONTRACT[value.state];
    return Array.isArray(copyOptions)
      && ["state", "source", "title", "detail"].every((key) => typeof value[key] === "string")
      && ["company", "company_label", "currency"].every((key) => value[key] === null || typeof value[key] === "string")
      && (value.state !== "scoped" || ["company", "company_label", "currency"].every((key) => typeof value[key] === "string" && value[key].length > 0))
      && copyOptions.some((expected) => exactCopyMatch(value, expected, ["title", "detail"]));
  }

  function validatePeriodScope(value) {
    return validateStringFields(value, ["state", "title", "detail"])
      && PERIOD_SCOPE_COPY_CONTRACT.some((expected) => exactCopyMatch(value, expected, ["state", "title", "detail"]));
  }

  function validateScope(value) {
    const keys = ["scope_mode", "phase", "default_routing_enabled", "accounting_overview_enabled", "receivables_count_posture_enabled", "receivables_amount_summary_enabled", "payables_count_posture_enabled", "company_scope_required", "financial_data_enabled", "financial_rows_enabled", "monetary_values_enabled", "execution_enabled"];
    const booleanKeys = keys.filter((key) => !["scope_mode", "phase"].includes(key));
    return validateStringFields(value, keys, { booleanKeys })
      && value.default_routing_enabled === false
      && value.financial_rows_enabled === false
      && value.execution_enabled === false;
  }

  function validateCompanyReference(value, includeCurrency) {
    if (value === null) return true;
    const keys = includeCurrency ? ["name", "label", "currency"] : ["name", "label"];
    return hasExactKeys(value, keys) && keys.every((key) => typeof value[key] === "string" && value[key].length > 0);
  }

  function validateReceivablesPosture(value) {
    if (isPlainObject(value) && Object.keys(value).length === 0) return true;
    const keys = ["phase", "state", "company_scope", "as_of_date", "bucket_labels", "bucket_counts", "policy", "no_effect", "rows_returned", "amounts_returned", "documents_returned", "runtime_count_enabled"];
    if (!hasExactKeys(value, keys) || !["ready", "unavailable"].includes(value.state)
      || value.phase !== "f4d_receivables_count_posture") return false;
    const ready = value.state === "ready";
    return validateCompanyReference(value.company_scope, true)
      && (!ready || value.company_scope !== null)
      && (!ready || (value.policy.source === "Sales Invoice"
        && value.policy.role_category === "manager"
        && value.policy.resolver_state === "scoped"
        && value.policy.resolver_scoped === true
        && value.policy.policy_contract_accepted === true
        && value.policy.source_read_policy_ready === true
        && value.policy.source_permission_checked === true
        && value.policy.source_permission_verified === true
        && value.policy.future_activity_source_permission_checked === true
        && value.policy.future_activity_source_permission_verified === true))
      && isValidCalendarDate(value.as_of_date)
      && validateBucketLabels(value.bucket_labels, FINANCE_BUCKET_KEYS)
      && validateReceivablesCountPolicyTruth(value.policy)
      && validateBucketCounts(value.bucket_counts, FINANCE_BUCKET_KEYS, ready)
      && validatePolicy(value.policy, COUNT_POLICY_KEYS)
      && value.policy.runtime_count_enabled === ready
      && validateNoEffect(value.no_effect)
      && value.rows_returned === false
      && value.amounts_returned === false
      && value.documents_returned === false
      && value.runtime_count_enabled === ready;
  }

  function isFixedScaleDecimal(value, precision) {
    if (typeof value !== "string" || !Number.isInteger(precision) || precision < 0 || precision > 8) return false;
    const pattern = precision === 0
      ? /^-?\d+$/
      : new RegExp(`^-?\\d+\\.\\d{${precision}}$`);
    return pattern.test(value);
  }

  function validateReceivablesAmount(value) {
    if (isPlainObject(value) && Object.keys(value).length === 0) return true;
    const keys = ["phase", "state", "company_scope", "as_of_date", "currency", "bucket_labels", "bucket_counts", "bucket_amounts", "suppressed_buckets", "policy", "no_effect", "rows_returned", "amounts_are_aggregate", "documents_returned", "runtime_payment_ledger_amount_summary_enabled"];
    if (!hasExactKeys(value, keys, ["grand_total"]) || !["ready", "unavailable"].includes(value.state)
      || value.phase !== "f4h_payment_ledger_amount_summary") return false;
    const ready = value.state === "ready";
    const amounts = value.bucket_amounts;
    const suppressed = value.suppressed_buckets;
    if (!isPlainObject(amounts) || !isPlainObject(suppressed)) return false;
    if (!ready && (Object.keys(amounts).length > 0
      || Object.keys(suppressed).length > 0
      || Object.prototype.hasOwnProperty.call(value, "grand_total"))) return false;
    const precision = value.policy.currency_precision;
    if (!Object.keys(amounts).every((key) => FINANCE_BUCKET_KEYS.includes(key)
      && isFixedScaleDecimal(amounts[key], precision))) return false;
    if (!Object.keys(suppressed).every((key) => FINANCE_BUCKET_KEYS.includes(key)
      && hasExactKeys(suppressed[key], ["suppressed", "reason"])
      && suppressed[key].suppressed === true
      && suppressed[key].reason === "suppressed_low_population")) return false;
    const amountKeys = Object.keys(amounts);
    const suppressedKeys = Object.keys(suppressed);
    if (amountKeys.some((key) => suppressedKeys.includes(key))) return false;
    if (ready && new Set([...amountKeys, ...suppressedKeys]).size !== FINANCE_BUCKET_KEYS.length) return false;
    const hasGrandTotal = Object.prototype.hasOwnProperty.call(value, "grand_total");
    if (suppressedKeys.length > 0 && hasGrandTotal) return false;
    if (ready && suppressedKeys.length === 0 && !hasGrandTotal) return false;
    if (hasGrandTotal && !isFixedScaleDecimal(value.grand_total, precision)) return false;
    return validateCompanyReference(value.company_scope, true)
      && (!ready || value.company_scope !== null)
      && (!ready || (value.policy.source === "Payment Ledger Entry"
        && value.policy.role_category === "manager"
        && value.policy.resolver_state === "scoped"
        && value.policy.runtime_amount_summary_enabled === true
        && value.policy.source_permission_checked === true
        && value.policy.source_permission_verified === true
        && value.policy.source_metadata_checked === true
        && value.policy.source_metadata_verified === true
        && value.policy.currency_precision_verified === true
        && Number.isInteger(value.policy.currency_precision)
        && value.policy.currency_precision >= 0
        && value.policy.currency_precision <= 8
        && value.policy.currency_precision_source === "erpnext.accounts.utils.get_currency_precision"
        && ["Banker's Rounding", "Commercial Rounding"].includes(value.policy.currency_rounding_method)
        && value.policy.amount_serialization === "fixed_decimal_string"
        && value.policy.company_currency === "MMK"
        && value.currency === "MMK"))
      && isValidCalendarDate(value.as_of_date)
      && validateBucketLabels(value.bucket_labels, FINANCE_BUCKET_KEYS)
      && validateBucketCounts(value.bucket_counts, FINANCE_BUCKET_KEYS, ready)
      && validateReceivablesAmountPolicyTruth(value.policy)
      && validatePolicy(value.policy, AMOUNT_POLICY_KEYS)
      && value.policy.runtime_amount_summary_enabled === ready
      && value.policy.amount_serialization === (ready ? "fixed_decimal_string" : "unavailable")
      && validateNoEffect(value.no_effect)
      && value.rows_returned === false
      && value.documents_returned === false
      && value.amounts_are_aggregate === ready
      && value.runtime_payment_ledger_amount_summary_enabled === ready;
  }

  function validatePayablesPosture(value) {
    if (isPlainObject(value) && Object.keys(value).length === 0) return true;
    const keys = ["phase", "state", "source_state", "company_scope", "as_of_date", "bucket_labels", "bucket_counts", "policy", "no_effect"];
    if (!hasExactKeys(value, keys) || !["ready", "unavailable"].includes(value.state)
      || value.phase !== "f5c_payables_count_posture") return false;
    const ready = value.state === "ready";
    return value.source_state === value.state
      && validateCompanyReference(value.company_scope, false)
      && (!ready || value.company_scope !== null)
      && (!ready || (value.policy.source === "Purchase Invoice"
        && value.policy.role_category === "manager"
        && value.policy.resolver_state === "scoped"
        && value.policy.source_read_policy_ready === true
        && value.policy.source_permission_checked === true
        && value.policy.source_permission_verified === true))
      && isValidCalendarDate(value.as_of_date)
      && validateBucketLabels(value.bucket_labels, PAYABLES_BUCKET_KEYS)
      && validateBucketCounts(value.bucket_counts, PAYABLES_BUCKET_KEYS, ready)
      && validatePolicy(value.policy, PAYABLES_POLICY_KEYS)
      && validatePayablesPolicyTruth(value.policy)
      && value.policy.runtime_count_enabled === ready
      && value.policy.monetary_values_enabled === false
      && validateNoEffect(value.no_effect);
  }

  const POSTURE_CARD_CONTRACT = Object.freeze({
    workspace_readiness: Object.freeze({ title: "Workspace readiness", values: ["Read-only"] }),
    company_scope: Object.freeze({ title: "Company scope", values: ["Not set"] }),
    period_scope: Object.freeze({ title: "Fiscal period posture", values: ["Deferred"] }),
    receivables_posture: Object.freeze({
      title: "Receivables posture",
      values: ["No counts", "Aggregate counts only", "Aggregate counts + MMK buckets"],
    }),
    payables_posture: Object.freeze({
      title: "Payables posture",
      values: ["No counts", "Unavailable", "Aggregate counts only"],
    }),
    ledger_posture: Object.freeze({ title: "Ledger posture", values: ["Blocked"] }),
  });

  const RECEIVABLES_MANAGER_ONLY_DETAIL = "Manager-only receivables posture. Aggregate receivables counts and amount posture are available only to Accounts Manager in this phase. No customer, invoice, voucher, account, report, export, or action data is shown.";
  const RECEIVABLES_CARD_UNAVAILABLE_DETAIL = "Receivables posture is unavailable. Aggregate receivables counts and manager-only amount posture are not shown. No customer, invoice, voucher, account, report, export, or action data is shown.";
  const RECEIVABLES_NO_ROW_DETAIL = "No row-level customer, invoice, voucher, account, Payment Ledger, route, report, export, or action detail is returned, shown, linked, exported, or actionable.";
  const PAYABLES_NO_ROW_DETAIL = "No supplier detail, invoice detail, amounts, native reports, exports, or payment actions are returned or shown.";

  function bucketCountParts(posture, keys, labels) {
    const counts = posture && posture.bucket_counts;
    return keys.map((key) => `${labels[key]}: ${counts[key]}`).join("; ");
  }

  function expectedReceivablesCardDetail(payload) {
    const posture = payload.receivables_posture || {};
    if (posture.state !== "ready") {
      return posture.policy && posture.policy.role_category === "normal_finance"
        ? RECEIVABLES_MANAGER_ONLY_DETAIL
        : RECEIVABLES_CARD_UNAVAILABLE_DETAIL;
    }
    const countParts = bucketCountParts(posture, FINANCE_BUCKET_KEYS, FINANCE_BUCKET_LABELS);
    const amountSummary = payload.receivables_amount_summary || {};
    if (amountSummary.state !== "ready") {
      return `Sales Invoice aggregate count buckets only. ${countParts}. No row-level customer, invoice, amount, route, report, export, or action detail is returned, shown, linked, exported, or actionable.`;
    }
    const amountParts = FINANCE_BUCKET_KEYS.map((key) => {
      if (Object.prototype.hasOwnProperty.call(amountSummary.bucket_amounts, key)) {
        return `${FINANCE_BUCKET_LABELS[key]}: ${amountSummary.bucket_amounts[key]} MMK`;
      }
      return `${FINANCE_BUCKET_LABELS[key]}: suppressed`;
    }).join("; ");
    return `Sales Invoice aggregate count buckets and manager-only Payment Ledger MMK amount buckets. ${countParts}. ${amountParts}. ${RECEIVABLES_NO_ROW_DETAIL}`;
  }

  function expectedPayablesCardDetail(payload) {
    const posture = payload.payables_count_posture || {};
    if (posture.state === "ready") {
      const countParts = bucketCountParts(posture, PAYABLES_BUCKET_KEYS, PAYABLES_BUCKET_LABELS);
      return `Purchase Invoice aggregate count buckets only. Current / not overdue includes invoices due today or later. ${countParts}. No supplier names, invoice IDs, amounts, currency totals, native reports, exports, or payment actions are returned, shown, linked, exported, or actionable.`;
    }
    const reason = posture.policy && posture.policy.reason;
    if (["payment_schedule_not_supported", "payment_terms_not_supported"].includes(reason)) {
      return `Payables counts are unavailable because some supplier invoices use payment schedules that this overview does not interpret. ${PAYABLES_NO_ROW_DETAIL} This overview does not approve or initiate payments.`;
    }
    if (reason === "accounts_manager_required") {
      return `Manager-only payables posture. AP count posture is available only to Accounts Manager in this phase. ${PAYABLES_NO_ROW_DETAIL}`;
    }
    return `Payables aggregate count posture is unavailable until the approved role, company, source, and permission gates pass. ${PAYABLES_NO_ROW_DETAIL}`;
  }

  function expectedPostureCardDetail(item, payload) {
    if (item.key === "workspace_readiness") return "Finance Control Desk is active for read-only overview posture.";
    if (item.key === "company_scope") {
      const allowed = {
        scoped: "Finance posture is limited to the approved company shown here.",
        selection_required: "Multiple allowed companies require an approved server-side selection before Finance posture loads.",
        unavailable: "Finance posture is unavailable until an approved company scope is available.",
      };
      if (payload.company_scope.state === "restricted") {
        return [
          "Finance overview requires an approved accounting or audit role.",
          "Your Finance role does not provide an approved company scope.",
        ].includes(item.detail) ? item.detail : null;
      }
      return allowed[payload.company_scope.state] || null;
    }
    if (item.key === "period_scope") {
      return payload.company_scope.state === "scoped"
        ? "Fiscal calendars and close records remain deferred until the owner approves the period policy."
        : "Fiscal and period posture waits for an approved company scope.";
    }
    if (item.key === "receivables_posture") return expectedReceivablesCardDetail(payload);
    if (item.key === "payables_posture") return expectedPayablesCardDetail(payload);
    if (item.key === "ledger_posture") {
      return "Account balances, ledger rows, statements, and trial-balance figures remain blocked in this read-only posture.";
    }
    return null;
  }

  function validatePostureCards(value, payload) {
    if (!Array.isArray(value)) return false;
    if (value.length === 0) return true;
    if (value.length > Object.keys(POSTURE_CARD_CONTRACT).length) return false;
    const seen = new Set();
    return value.every((item) => {
      if (!hasExactKeys(item, ["key", "title", "state", "detail", "value", "rows"])
        || ![item.key, item.title, item.detail, item.value].every((field) => typeof field === "string")
        || !isEmptyArray(item.rows) || !["ready", "unavailable", "restricted"].includes(item.state)) return false;
      const contract = POSTURE_CARD_CONTRACT[item.key];
      if (!contract || seen.has(item.key) || item.title !== contract.title) return false;
      seen.add(item.key);
      if (item.key === "company_scope") {
        const companyName = payload.company_scope && typeof payload.company_scope.company === "string" ? payload.company_scope.company : "";
        if (!(item.value === "Not set" || (!!companyName && item.value === companyName))) return false;
      } else if (!contract.values.includes(item.value)) {
        return false;
      }
      return item.detail === expectedPostureCardDetail(item, payload);
    });
  }

  function postureCollectionsMatch(cards, lanes) {
    return Array.isArray(cards) && Array.isArray(lanes)
      && cards.length === lanes.length
      && cards.every((card, index) => JSON.stringify(card) === JSON.stringify(lanes[index]));
  }

  function validateBusinessFacingCopy(payload) {
    const directValues = [
      payload.workspace.title, payload.workspace.workspace_family, payload.workspace.mode_label,
      payload.state.title, payload.state.detail,
      payload.overview.title, payload.overview.detail,
      payload.company_scope.title, payload.company_scope.detail,
      payload.period_scope.title, payload.period_scope.detail,
    ];
    const cardValues = [...payload.posture_cards, ...payload.lanes].flatMap((item) => [
      item.title,
      item.detail,
      item.value,
    ]);
    return [...directValues, ...cardValues].every((value) => isBusinessSafeText(value));
  }

  function validateFinanceOverviewPayload(payload) {
    if (!hasExactKeys(payload, TOP_LEVEL_KEYS) || hasForbiddenRawFinancePayload(payload)) return false;
    if (payload.schema_version !== FINANCE_OVERVIEW_SCHEMA_VERSION) return false;
    if (!validateWorkspace(payload.workspace)
      || !validateOverviewState(payload.state)
      || !validateScope(payload.scope)
      || !validateOverviewCopy(payload.overview)
      || !validateCompanyScope(payload.company_scope)
      || !validatePeriodScope(payload.period_scope)) return false;
    if (!validateReceivablesPosture(payload.receivables_posture)
      || !validateReceivablesAmount(payload.receivables_amount_summary)
      || !validatePayablesPosture(payload.payables_count_posture)) return false;
    if (!validatePostureCards(payload.posture_cards, payload)
      || !validatePostureCards(payload.lanes, payload)
      || !postureCollectionsMatch(payload.posture_cards, payload.lanes)) return false;
    if (!validateBusinessFacingCopy(payload)) return false;
    if (![payload.metrics, payload.amounts, payload.documents, payload.rows].every(isEmptyArray)) return false;
    if (!validateNoEffect(payload.no_effect)) return false;
    const postureDates = [payload.receivables_posture, payload.receivables_amount_summary, payload.payables_count_posture]
      .filter((posture) => isPlainObject(posture) && Object.keys(posture).length > 0)
      .map((posture) => posture.as_of_date);
    if (postureDates.length && new Set(postureDates).size !== 1) return false;
    if (!isValidTimestamp(payload.fetched_at)) return false;
    if (payload.state.kind === "ready") {
      if ([payload.receivables_posture, payload.receivables_amount_summary, payload.payables_count_posture]
        .some((posture) => !isPlainObject(posture) || Object.keys(posture).length === 0)) return false;
      if (payload.scope.accounting_overview_enabled !== true
        || payload.scope.financial_data_enabled !== false
        || payload.company_scope.state !== "scoped") return false;
      const countReady = payload.receivables_posture.state === "ready";
      const amountReady = payload.receivables_amount_summary.state === "ready";
      const payablesReady = payload.payables_count_posture.state === "ready";
      if (amountReady && !countReady) return false;
      if (payload.scope.receivables_count_posture_enabled !== countReady) return false;
      if (payload.scope.receivables_amount_summary_enabled !== amountReady) return false;
      if (payload.scope.payables_count_posture_enabled !== payablesReady) return false;
      if (payload.scope.monetary_values_enabled !== amountReady) return false;
      const companyName = payload.company_scope.company;
      const companyCurrency = payload.company_scope.currency;
      if (amountReady && companyCurrency !== "MMK") return false;
      if (countReady && (payload.receivables_posture.company_scope.name !== companyName
        || payload.receivables_posture.company_scope.currency !== companyCurrency)) return false;
      if (amountReady && (payload.receivables_amount_summary.company_scope.name !== companyName
        || payload.receivables_amount_summary.company_scope.currency !== companyCurrency)) return false;
      if (payablesReady && payload.payables_count_posture.company_scope.name !== companyName) return false;
      const countDate = payload.receivables_posture.as_of_date;
      const amountDate = payload.receivables_amount_summary.as_of_date;
      if (countDate && amountDate && countDate !== amountDate) return false;
    } else {
      const nestedReady = [payload.receivables_posture, payload.receivables_amount_summary, payload.payables_count_posture]
        .some((posture) => isPlainObject(posture) && posture.state === "ready");
      if (nestedReady
        || payload.scope.accounting_overview_enabled !== false
        || payload.scope.receivables_count_posture_enabled !== false
        || payload.scope.receivables_amount_summary_enabled !== false
        || payload.scope.payables_count_posture_enabled !== false
        || payload.scope.monetary_values_enabled !== false) return false;
    }
    return true;
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

  function freshnessCopy(payload) {
    const asOf = String((payload && payload.as_of_date) || "").trim();
    const fetched = String((payload && payload.fetched_at) || "").trim().slice(0, 19).replace("T", " ");
    const parts = [];
    if (asOf) parts.push(`As of ${asOf}`);
    if (fetched) parts.push(`Refreshed ${fetched}`);
    return parts.join(" | ");
  }

  function renderHero(payload, variant, summary, statusLabel) {
    const workspace = payload.workspace || {};
    const title = businessSafeText(workspace.title, "Finance Control Desk");
    const family = businessSafeText(workspace.workspace_family, "Finance & Accounting");
    const safeVariant = variant ? ` ${variant}` : "";
    return `
      <section class="finance-control-hero${safeVariant}" aria-label="Finance Control Desk overview">
        <div class="finance-control-hero-top">
          <div>
            <p class="finance-control-eyebrow">${escapeHtml(family)}</p>
            <h1 class="finance-control-title">${escapeHtml(title)}</h1>
            <p class="finance-control-summary">${escapeHtml(businessSafeText(summary, visibleUnavailableMessage()))}</p>
            ${freshnessCopy(payload) ? `<p class="finance-control-freshness">${escapeHtml(freshnessCopy(payload))}</p>` : ""}
          </div>
          <div class="finance-control-actions">
            <span class="finance-control-status">${escapeHtml(businessSafeText(statusLabel, "Unavailable"))}</span>
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
        <h2 class="finance-control-panel-title">${escapeHtml(businessSafeText(lane.title, "Finance posture unavailable"))}</h2>
        <p class="finance-control-panel-copy">${escapeHtml(visibleLaneDetail(lane))}</p>
        <div class="finance-control-chip-row" aria-label="${escapeHtml(businessSafeText(lane.title, "Finance posture"))} state">
          <span class="finance-control-chip${lane.state === "ready" ? "" : " is-muted"}">${escapeHtml(businessSafeText(lane.value, "Unavailable"))}</span>
        </div>
      </article>
    `).join("");
    const noRowsCopy = hasFinancialRows(payload)
      ? "Policy violation: row-level financial data was returned to this page. The page blocks rendering, linking, export, and action surfaces for that response, and this response must not be accepted for manual review."
      : "Finance overview shows scoped aggregate posture only. The backend may perform bounded aggregate source reads, but row-level accounting data is not returned, shown, linked, exported, or actionable. Approved managers may see aggregate receivables buckets and count-only Payables buckets when all gates pass.";
    const noEffectCopy = allNoEffectFlagsFalse(payload.no_effect)
      ? "The backend context reports no document, ledger, payment, reconciliation, tax, notification, or export effect."
      : "The shell treats this response as display-only and does not expose execution controls.";
    const overviewCopy = payload.overview && payload.overview.detail
      ? payload.overview.detail
      : "Company-scoped posture only. Approved managers may see aggregate receivables buckets and count-only Payables buckets when all gates pass; row-level data, reports, exports, and execution remain blocked.";

    return `
      <main class="finance-control-shell" data-erpw-workspace="finance" data-finance-cycle1-overview="ready">
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
              <div class="finance-control-state-label is-ready">${escapeHtml(businessSafeText(payload.state.title, "Read-only Finance overview"))}</div>
              <div class="finance-control-state-text">
                <strong>Read-only overview ready</strong>
                <span>${escapeHtml(businessSafeText(payload.state.detail, FINANCE_UNAVAILABLE_FALLBACK))}</span>
              </div>
            </div>
            <div class="finance-control-state-row">
              <div class="finance-control-state-label">Read-only</div>
              <div class="finance-control-state-text">
                <strong>Payables stays count-only and fail-closed</strong>
                <span>Counts appear only when Finance can prove that candidate invoices do not use payment schedules. Otherwise Payables remains unavailable. AP amounts, supplier/invoice rows, cash truth, ledger rows, reports, exports, and payment actions remain blocked.</span>
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

  function renderPolicyViolation() {
    const violationPayload = normalizePayload({
      workspace: { title: "Finance Control Desk", workspace_family: "Finance & Accounting" },
      state: {
        kind: "unavailable",
        title: "Finance overview is unavailable",
        detail: "This Finance overview could not be shown safely. No row-level data, reports, exports, or action controls are displayed.",
      },
      scope: { financial_data_enabled: false, execution_enabled: false },
      no_effect: {},
      rows: [],
      lanes: [],
    });
    return `
      <main class="finance-control-shell" data-erpw-workspace="finance" data-finance-cycle1-overview="unavailable" data-finance-payload-rejected="1">
        ${renderHero(violationPayload, "is-unavailable", violationPayload.state.detail, "Unavailable")}
        <section class="finance-control-panel finance-control-boundary" aria-label="Finance overview unavailable">
          <h2 class="finance-control-panel-title">Controlled unavailable state</h2>
          <p class="finance-control-panel-copy">No row-level data, identities, native routes, reports, exports, downloads, print surfaces, or action controls are rendered from this response.</p>
        </section>
      </main>
    `;
  }

  function renderRestricted(payload) {
    return `
      <main class="finance-control-shell" data-erpw-workspace="finance" data-finance-cycle1-overview="restricted">
        ${renderHero(
          payload,
          "is-restricted",
          businessSafeText(payload.state.detail, "This shell is limited to approved accounting, audit, or system roles."),
          "Restricted"
        )}
        <section class="finance-control-panel finance-control-boundary" aria-label="Finance access restricted">
          <h2 class="finance-control-panel-title">${escapeHtml(businessSafeText(payload.state.title, "Finance Control Desk is restricted"))}</h2>
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
      <main class="finance-control-shell finance-control-loading" data-erpw-workspace="finance" data-finance-cycle1-overview="loading">
        ${renderHero(payload, "is-unavailable", payload.state.detail, "Loading")}
      </main>
    `;
  }

  function renderUnavailable(message, sourcePayload) {
    const source = sourcePayload || {};
    const payload = normalizePayload({
      workspace: { title: "Finance Control Desk", workspace_family: "Finance & Accounting" },
      state: {
        kind: "unavailable",
        title: "Finance Control Desk is unavailable",
        detail: visibleUnavailableMessage(message),
      },
      scope: { financial_data_enabled: false, execution_enabled: false },
      no_effect: { row_level_financial_data_returned: false, export_generated: false },
      rows: [],
      lanes: [],
    });
    payload.as_of_date = source.as_of_date || "";
    payload.fetched_at = source.fetched_at || "";
    return `
      <main class="finance-control-shell" data-erpw-workspace="finance" data-finance-cycle1-overview="unavailable">
        ${renderHero(payload, "is-unavailable", payload.state.detail, "Unavailable")}
        <section class="finance-control-panel finance-control-boundary" aria-label="Finance overview unavailable">
          <h2 class="finance-control-panel-title">Controlled unavailable state</h2>
          <p class="finance-control-panel-copy">Refresh reloads only the overview context. It does not call accounting reports, return row-level financial data, export files, or open native execution routes.</p>
        </section>
      </main>
    `;
  }

  function renderPayload(payload) {
    const contractValid = validateFinanceOverviewPayload(payload);
    const normalized = normalizePayload(payload);
    if (!contractValid || hasFinancialRows(normalized)) {
      return renderPolicyViolation();
    }
    if (normalized.state.kind === "restricted") {
      return renderRestricted(normalized);
    }
    if (normalized.state.kind !== "ready") {
      return renderUnavailable(normalized.state.detail, normalized);
    }
    return renderReady(normalized);
  }

  function createOverviewContextRequest(callApi, options) {
    const opts = options || {};
    const timeoutMs = Number.isFinite(opts.timeoutMs) && opts.timeoutMs > 0
      ? opts.timeoutMs
      : OVERVIEW_CONTEXT_TIMEOUT_MS;
    const scheduleTimeout = opts.scheduleTimeout || setTimeout;
    const cancelTimeout = opts.cancelTimeout || clearTimeout;
    return new Promise((resolve, reject) => {
      let settled = false;
      let timer = null;
      const finish = (callback, value) => {
        if (settled) return;
        settled = true;
        if (timer !== null) cancelTimeout(timer);
        callback(value);
      };
      const resolveOnce = (response) => finish(
        resolve,
        response && response.message ? response.message : {}
      );
      const rejectOnce = (error) => finish(
        reject,
        error instanceof Error ? error : new Error("Finance overview context failed")
      );
      timer = scheduleTimeout(
        () => rejectOnce(new Error("Finance overview context timed out")),
        timeoutMs
      );

      let request;
      try {
        request = callApi({
          method: OVERVIEW_CONTEXT_METHOD,
          callback: resolveOnce,
          error: rejectOnce,
        });
      } catch (error) {
        rejectOnce(error);
        return;
      }
      if (request && typeof request.fail === "function") {
        request.fail(rejectOnce);
      } else if (request && typeof request.catch === "function") {
        request.catch(rejectOnce);
      }
    });
  }

  function callOverviewContext() {
    if (!frappe || typeof frappe.call !== "function") {
      return Promise.reject(new Error("Frappe call API unavailable"));
    }
    const browser = typeof window !== "undefined" ? window : globalThis;
    return createOverviewContextRequest(
      (options) => frappe.call(options),
      {
        scheduleTimeout: typeof browser.setTimeout === "function" ? browser.setTimeout.bind(browser) : setTimeout,
        cancelTimeout: typeof browser.clearTimeout === "function" ? browser.clearTimeout.bind(browser) : clearTimeout,
      }
    );
  }

  function createOverviewRequestCoordinator(callContext) {
    let requestSerial = 0;
    let inFlight = null;

    function invalidate() {
      requestSerial += 1;
      inFlight = null;
    }

    function load(options) {
      const opts = options || {};
      if (!opts.force && inFlight) return inFlight.promise;
      const token = ++requestSerial;
      const request = Promise.resolve().then(() => callContext());
      const settled = request.then((payload) => {
        if (token !== requestSerial) return { stale: true, payload: null };
        if (typeof opts.onPayload === "function") opts.onPayload(payload);
        return { stale: false, payload };
      }).catch((error) => {
        if (token !== requestSerial) return { stale: true, error };
        if (typeof opts.onError === "function") opts.onError(error);
        return { stale: false, error };
      }).finally(() => {
        if (inFlight && inFlight.token === token) inFlight = null;
        if (token === requestSerial && typeof opts.onSettled === "function") opts.onSettled();
      });
      inFlight = { token, promise: settled };
      return settled;
    }

    return Object.freeze({ invalidate, load });
  }

  function bindRefresh(target) {
    const refresh = target.querySelector("[data-finance-refresh]");
    if (!refresh) return;
    refresh.addEventListener("click", () => loadOverviewContext(target, { force: true }));
  }

  function setHtml(target, html) {
    if (!target || target === document.body || target.id === "body") return;
    target.innerHTML = html;
    bindRefresh(target);
  }

  function setRequestBusy(target, busy) {
    if (!target) return;
    target.setAttribute("aria-busy", busy ? "true" : "false");
    const refresh = target.querySelector("[data-finance-refresh]");
    if (refresh) refresh.disabled = Boolean(busy);
  }

  function coordinatorFor(target) {
    if (!target.__financeControlDeskRequestCoordinator) {
      target.__financeControlDeskRequestCoordinator = createOverviewRequestCoordinator(callOverviewContext);
    }
    return target.__financeControlDeskRequestCoordinator;
  }

  function loadOverviewContext(target, options) {
    ensureStyle();
    const opts = options || {};
    if (!target || target === document.body || target.id === "body") return Promise.resolve({ stale: true });
    if (!target.__financeControlDeskOverviewPayload) setHtml(target, renderLoading());
    setRequestBusy(target, true);
    return coordinatorFor(target).load({
      force: Boolean(opts.force),
      onPayload(payload) {
        if (!validateFinanceOverviewPayload(payload)) {
          target.__financeControlDeskOverviewPayload = null;
          setHtml(target, renderPolicyViolation());
          return;
        }
        target.__financeControlDeskOverviewPayload = payload;
        setHtml(target, renderPayload(payload));
      },
      onError() {
        target.__financeControlDeskOverviewPayload = null;
        setHtml(target, renderUnavailable());
      },
      onSettled() {
        setRequestBusy(target, false);
      },
    });
  }

  function bindFinancePageHide(pageWrapper, target, binder) {
    if (!pageWrapper || !target || pageWrapper.__financeControlDeskHideBound) return false;
    const activeBinder = binder || ((node, handler) => {
      const browser = typeof window !== "undefined" ? window : globalThis;
      const jquery = browser.jQuery || browser.$;
      if (typeof jquery !== "function") return false;
      jquery(node).off("hide.financeControlDesk").on("hide.financeControlDesk", handler);
      return true;
    });
    if (activeBinder(pageWrapper, () => invalidateTarget(target)) === false) return false;
    pageWrapper.__financeControlDeskHideBound = true;
    return true;
  }

  function render(wrapper) {
    const pageWrapper = resolvePageWrapper(wrapper);
    const target = resolveTarget(pageWrapper);
    if (!target || target === document.body || target.id === "body") return;
    bindFinancePageHide(pageWrapper, target);
    if (target.__financeControlDeskOverviewPayload) {
      setHtml(target, renderPayload(target.__financeControlDeskOverviewPayload));
    }
    target.__financeControlDeskInitialized = true;
    return loadOverviewContext(target, { force: false });
  }

  function invalidateTarget(target) {
    if (!target || target === document.body || target.id === "body") return;
    if (target.__financeControlDeskRequestCoordinator) {
      target.__financeControlDeskRequestCoordinator.invalidate();
    }
    target.__financeControlDeskOverviewPayload = null;
    setRequestBusy(target, false);
  }

  function hide(wrapper) {
    invalidateTarget(resolveTarget(wrapper));
  }


  if (typeof module !== "undefined" && module.exports) {
    module.exports = Object.freeze({
      financeDataBoundaryPayload,
      hasForbiddenFinancePayloadShape,
      hasForbiddenPayablesPayloadShape,
      hasForbiddenRawFinancePayload,
      isForbiddenPayablesValueKey,
      visibleLaneDetail,
      isBusinessSafeText,
      businessSafeText,
      normalizePayload,
      validateFinanceOverviewPayload,
      createOverviewContextRequest,
      createOverviewRequestCoordinator,
      bindFinancePageHide,
      resolvePageWrapper,
      resolveTarget,
      render,
      hide,
      renderPayload,
    });
    return;
  }

  const pageDef = frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  pageDef.on_page_load = render;
  pageDef.on_page_show = render;
})();