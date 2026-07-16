from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, ROUND_HALF_UP
from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, now_datetime

from erp_workspace_ui.workspace_registry import (
    WORKSPACE_SIDEBAR_SCHEMA_VERSION,
    get_finance_workspace_definition,
)


FINANCE_SHELL_ROLES = frozenset({"Accounts User", "Accounts Manager", "Auditor", "System Manager"})
FINANCE_OVERVIEW_ROLES = frozenset({"Accounts User", "Accounts Manager", "Auditor"})
FINANCE_MANAGER_ROLES = frozenset({"Accounts Manager"})
FINANCE_NORMAL_USER_ROLES = frozenset({"Accounts User"})
FINANCE_AUDIT_ROLES = frozenset({"Auditor"})
FINANCE_ADMIN_ONLY_ROLES = frozenset({"System Manager"})
FINANCE_REVIEW_ONLY_ROLES = frozenset({"Finance Lead Approver"})
FINANCE_EXECUTIVE_ONLY_ROLES = frozenset({"Executive Approver"})
FINANCE_OVERVIEW_PHASE = "finance_cycle_1_aggregate_posture"
FINANCE_RESOLVER_PHASE = "f4b_role_company_resolver"
FINANCE_RECEIVABLES_SOURCE_POLICY_PHASE = "f4c_receivables_source_read_policy"
FINANCE_RECEIVABLES_COUNT_PHASE = "f4d_receivables_count_posture"
FINANCE_RECEIVABLES_AMOUNT_PHASE = "f4h_payment_ledger_amount_summary"
FINANCE_PAYABLES_COUNT_PHASE = "f5c_payables_count_posture"
FINANCE_APPROVED_COMPANY_NAME = "Mingalar Mobile Distribution Co., Ltd."
FINANCE_APPROVED_COMPANY_CURRENCY = "MMK"
RECEIVABLES_COUNT_SOURCE = "Sales Invoice"
RECEIVABLES_SCHEDULE_CHILD_SOURCE = "Payment Schedule"
RECEIVABLES_COUNT_QUERY_FIELD = {"COUNT": "name", "as": "count"}
RECEIVABLES_COUNT_SOURCE_INVALID_REASON = "sales_invoice_count_source_invalid"
RECEIVABLES_SCHEDULE_CANDIDATE_MAX_ROWS = 2000
RECEIVABLES_SCHEDULE_INTEGRITY_MAX_ROWS = 2
RECEIVABLES_SCHEDULE_INTEGRITY_INVALID_REASON = "payment_schedule_integrity_unavailable"
PAYABLES_COUNT_SOURCE = "Purchase Invoice"
PAYABLES_SCHEDULE_CHILD_SOURCE = "Payment Schedule"
PAYABLES_FUTURE_ACTIVITY_SOURCE = "Payment Ledger Entry"
PAYABLES_COUNT_QUERY_FIELD = {"COUNT": "name", "as": "count"}
PAYABLES_COUNT_SOURCE_INVALID_REASON = "purchase_invoice_count_source_invalid"
PAYABLES_FUTURE_ACTIVITY_SOURCE_INVALID_REASON = "payment_ledger_future_activity_source_invalid"
PAYABLES_COUNT_BUCKETS = (
    {"key": "not_due", "label": "Current / not overdue", "from_days": None, "to_days": 0},
    {"key": "overdue_1_30", "label": "1-30 overdue", "from_days": 1, "to_days": 30},
    {"key": "overdue_31_60", "label": "31-60 overdue", "from_days": 31, "to_days": 60},
    {"key": "overdue_61_90", "label": "61-90 overdue", "from_days": 61, "to_days": 90},
    {"key": "overdue_over_90", "label": ">90 overdue", "from_days": 91, "to_days": None},
)
PAYABLES_OPEN_STATUSES = ("Unpaid", "Overdue", "Partly Paid")
RECEIVABLES_AMOUNT_SOURCE = "Payment Ledger Entry"
RECEIVABLES_AMOUNT_MIN_BUCKET_VOUCHER_COUNT = 3
RECEIVABLES_AMOUNT_MIN_BUCKET_DIVERSITY_COUNT = 3
RECEIVABLES_AMOUNT_SOURCE_PAGE_SIZE = 500
RECEIVABLES_AMOUNT_SOURCE_MAX_ROWS = 5000
RECEIVABLES_IDENTITY_SOURCE_PAGE_SIZE = 500
RECEIVABLES_IDENTITY_SOURCE_MAX_ROWS = 5000
RECEIVABLES_AMOUNT_SOURCE_TOO_LARGE_REASON = "payment_ledger_source_too_large"
RECEIVABLES_AMOUNT_SOURCE_INVALID_REASON = "payment_ledger_source_invalid"
RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON = "receivables_voucher_reconciliation_unavailable"
RECEIVABLES_AMOUNT_CURRENCY_CONTRACT_INVALID_REASON = "currency_precision_contract_unavailable"
FINANCE_OVERVIEW_SCHEMA_VERSION = "finance-overview.v1"
FINANCE_COMPANY_SCOPE_MAX_ROWS = 20
FINANCE_COMPANY_PERMISSION_MAX_ROWS = 50
RECEIVABLES_AMOUNT_SOURCE_FIELDS = (
    "name",
    "company",
    "account",
    "account_type",
    "party_type",
    "party",
    "voucher_type",
    "voucher_no",
    "voucher_detail_no",
    "against_voucher_type",
    "against_voucher_no",
    "posting_date",
    "due_date",
    "amount",
    "amount_in_account_currency",
    "account_currency",
    "delinked",
)
RECEIVABLES_IDENTITY_SOURCE_FIELDS = (
    "name",
    "company",
    "customer",
    "debit_to",
    "posting_date",
    "due_date",
    "docstatus",
    "is_return",
    "return_against",
)
RECEIVABLES_BLOCKED_SOURCES = frozenset(
    {
        "Accounts Receivable",
        "Accounts Payable",
        "Customer",
        "GL Entry",
        "General Ledger",
        "Journal Entry",
        "Payment Entry",
        "Purchase Invoice",
        "Bank Transaction",
    }
)
RECEIVABLES_ALLOWED_INTERNAL_FIELDS = frozenset(
    {
        "company",
        "docstatus",
        "due_date",
        "is_return",
        "outstanding_amount",
        "posting_date",
        "return_against",
        "status",
    }
)
RECEIVABLES_BLOCKED_BROWSER_FIELDS = frozenset(
    {
        "name",
        "customer",
        "currency",
        "due_date",
        "invoice_identifier",
        "outstanding_amount",
        "payment_schedule",
        "posting_date",
        "route",
        "status",
    }
)
RECEIVABLES_COUNT_RESPONSE_KEYS = frozenset(
    {
        "as_of_date",
        "bucket_counts",
        "bucket_labels",
        "company_scope",
        "no_effect",
        "policy",
    }
)
RECEIVABLES_BLOCKED_EMPTY_PLACEHOLDER_KEYS = frozenset({"rows", "amounts", "documents", "metrics"})
RECEIVABLES_COUNT_BUCKETS = (
    {"key": "current", "label": "Current / not due", "from_days": None, "to_days": 0},
    {"key": "overdue_1_30", "label": "1-30 overdue", "from_days": 1, "to_days": 30},
    {"key": "overdue_31_60", "label": "31-60 overdue", "from_days": 31, "to_days": 60},
    {"key": "overdue_61_90", "label": "61-90 overdue", "from_days": 61, "to_days": 90},
    {"key": "overdue_over_90", "label": ">90 overdue", "from_days": 91, "to_days": None},
)
_COMPANY_SCOPE_UNSET = object()


def ensure_authenticated() -> None:
    if getattr(frappe.session, "user", None) == "Guest":
        frappe.throw(_("Authentication required"), frappe.PermissionError)


def current_user_roles(user: str | None = None) -> set[str]:
    try:
        return set(frappe.get_roles(user or getattr(frappe.session, "user", None)))
    except Exception:
        return set()


def has_finance_shell_access(context: dict[str, object] | None = None) -> bool:
    roles = set(context.get("roles") or []) if context and "roles" in context else current_user_roles()
    return bool(roles.intersection(FINANCE_SHELL_ROLES))


def has_finance_overview_access(context: dict[str, object] | None = None) -> bool:
    roles = set(context.get("roles") or []) if context and "roles" in context else current_user_roles()
    return bool(roles.intersection(FINANCE_OVERVIEW_ROLES))


def _role_variant(roles: list[str]) -> str:
    role_set = set(roles)
    if "Accounts Manager" in role_set:
        return "accounts_manager"
    if "Accounts User" in role_set:
        return "accounts_user"
    if "Auditor" in role_set:
        return "auditor"
    if "System Manager" in role_set:
        return "system_manager"
    return "restricted"


def _clean_roles(roles: object) -> set[str]:
    if not roles:
        return set()
    return {cstr(role).strip() for role in roles if cstr(role).strip()}


def classify_finance_role_scope(roles: object) -> dict[str, object]:
    role_set = _clean_roles(roles)
    category = "restricted"
    primary_role = ""
    if role_set.intersection(FINANCE_MANAGER_ROLES):
        category = "manager"
        primary_role = "Accounts Manager"
    elif role_set.intersection(FINANCE_NORMAL_USER_ROLES):
        category = "normal_finance"
        primary_role = "Accounts User"
    elif role_set.intersection(FINANCE_AUDIT_ROLES):
        category = "audit_candidate"
        primary_role = "Auditor"
    elif role_set.intersection(FINANCE_ADMIN_ONLY_ROLES):
        category = "system_admin_only"
        primary_role = "System Manager"
    elif role_set.intersection(FINANCE_EXECUTIVE_ONLY_ROLES):
        category = "executive_only"
        primary_role = "Executive Approver"
    elif role_set.intersection(FINANCE_REVIEW_ONLY_ROLES):
        category = "review_only"
        primary_role = "Finance Lead Approver"

    manager_candidate = category == "manager"
    normal_candidate = category == "normal_finance"
    audit_candidate = category == "audit_candidate"
    finance_scope_candidate = manager_candidate or normal_candidate
    return {
        "role_category": category,
        "primary_role": primary_role,
        "roles": sorted(role_set),
        "manager_visibility_candidate": manager_candidate,
        "normal_finance_candidate": normal_candidate,
        "audit_candidate": audit_candidate,
        "finance_scope_candidate": finance_scope_candidate,
        "amount_visibility_candidate": manager_candidate,
        "limited_posture_candidate": finance_scope_candidate,
        "system_manager_only": category == "system_admin_only",
        "executive_only": category == "executive_only",
        "review_only": category == "review_only",
    }


def _permission_preserving_list_call(getter: object, doctype: str, **kwargs: object) -> object:
    message_log = getattr(getattr(frappe, "local", None), "message_log", None)
    message_count = len(message_log) if isinstance(message_log, list) else None
    try:
        return getter(doctype, **kwargs)
    except Exception:
        if message_count is not None and isinstance(message_log, list):
            del message_log[message_count:]
        raise


def _safe_config_list(doctype: str, max_rows: int, **kwargs: object) -> list[dict[str, object]] | None:
    getter = getattr(frappe, "get_list", None)
    if not callable(getter) or not isinstance(max_rows, int) or isinstance(max_rows, bool) or max_rows <= 0:
        return None
    try:
        records = _permission_preserving_list_call(
            getter,
            doctype,
            **kwargs,
            limit_start=0,
            limit_page_length=max_rows + 1,
        ) or []
    except Exception:
        return None
    if not isinstance(records, list) or len(records) > max_rows:
        return None
    normalized: list[dict[str, object]] = []
    for record in records:
        if not isinstance(record, dict):
            return None
        normalized.append(record)
    return normalized


def _load_enabled_company_records() -> list[dict[str, object]] | None:
    # Company.disabled is intentionally not requested. Field-level denial must
    # return a controlled scope state rather than a modal exception.
    return _safe_config_list(
        "Company",
        FINANCE_COMPANY_SCOPE_MAX_ROWS,
        fields=["name", "company_name", "default_currency"],
        order_by="name asc",
    )


def _load_company_user_permission_values(user: str | None) -> list[str] | None:
    if not user:
        return []
    records = _safe_config_list(
        "User Permission",
        FINANCE_COMPANY_PERMISSION_MAX_ROWS,
        filters={"user": user, "allow": "Company"},
        fields=["for_value"],
        order_by="for_value asc",
    )
    if records is None:
        return None
    values: list[str] = []
    for record in records:
        if set(record) != {"for_value"}:
            return None
        value = cstr(record.get("for_value") or "").strip()
        if not value or value in values:
            return None
        values.append(value)
    return values


def _can_read_company_user_permissions(user: str | None) -> bool:
    """Check configuration authority without triggering a permission exception."""
    checker = getattr(frappe, "has_permission", None)
    if not user or not callable(checker):
        return False
    try:
        return bool(
            checker(
                "User Permission",
                ptype="read",
                user=user,
                throw=False,
            )
        )
    except Exception:
        return False


def _company_record(record: object) -> dict[str, object]:
    if not isinstance(record, dict) or set(record) != {"name", "company_name", "default_currency"}:
        return {
            "name": "",
            "label": "",
            "currency": "",
            "enabled": False,
        }
    name = cstr(record.get("name") or "").strip()
    label = cstr(record.get("company_name") or "").strip()
    currency = cstr(record.get("default_currency") or "").strip()
    return {
        "name": name,
        "label": label,
        "currency": currency,
        "enabled": bool(name),
    }


def _normalize_enabled_companies(records: object) -> list[dict[str, object]]:
    if not records:
        return []
    companies = [_company_record(record) for record in records]
    return [company for company in companies if company.get("enabled")]


def _scope_payload(
    state_value: str,
    source: str,
    role_scope: dict[str, object],
    reason: str,
    company: dict[str, object] | None = None,
    available_company_count: int = 0,
) -> dict[str, object]:
    selected = None
    if company:
        selected = {
            "name": company.get("name"),
            "label": company.get("label"),
            "currency": company.get("currency"),
        }
    return {
        "phase": FINANCE_RESOLVER_PHASE,
        "state": state_value,
        "source": source,
        "reason": reason,
        "role_category": role_scope.get("role_category"),
        "primary_role": role_scope.get("primary_role"),
        "selected_company": selected,
        "available_company_count": available_company_count,
        "selection_required": source == "selection_required",
        "source_read_policy_ready": False,
        "ar_runtime_data_enabled": False,
        "ap_runtime_data_enabled": False,
        "cash_runtime_data_enabled": False,
        "amount_visibility_enabled": False,
        "amount_visibility_candidate": bool(role_scope.get("amount_visibility_candidate")),
        "limited_posture_candidate": bool(role_scope.get("limited_posture_candidate")),
        "execution_enabled": False,
        "rows": [],
        "metrics": [],
        "amounts": [],
        "documents": [],
    }


def resolve_finance_role_company_scope(
    context: dict[str, object] | None = None,
    requested_company: str | None = None,
    enabled_companies: object = _COMPANY_SCOPE_UNSET,
    company_user_permissions: object = _COMPANY_SCOPE_UNSET,
    site_enabled_company_count: object = _COMPANY_SCOPE_UNSET,
    audit_scope_approved: bool = False,
) -> dict[str, object]:
    active_context = context or build_context()
    user = cstr(active_context.get("user") or getattr(frappe.session, "user", None) or "").strip()
    role_scope = classify_finance_role_scope(active_context.get("roles") or [])
    if role_scope.get("audit_candidate") and audit_scope_approved:
        role_scope = dict(role_scope)
        role_scope["finance_scope_candidate"] = True
        role_scope["limited_posture_candidate"] = True
    if not role_scope.get("finance_scope_candidate"):
        return _scope_payload("restricted", "restricted", role_scope, "finance_role_required")

    if enabled_companies is _COMPANY_SCOPE_UNSET:
        enabled_records = _load_enabled_company_records()
        if enabled_records is None:
            return _scope_payload("unavailable", "unavailable", role_scope, "company_lookup_unavailable")
    else:
        enabled_records = enabled_companies
    companies = _normalize_enabled_companies(enabled_records)
    if len(companies) != len(enabled_records or []):
        return _scope_payload("unavailable", "unavailable", role_scope, "company_lookup_malformed")
    company_by_name = {cstr(company.get("name")): company for company in companies}
    if len(company_by_name) != len(companies) or any(
        not cstr(company.get("name")).strip()
        or not cstr(company.get("label")).strip()
        or not cstr(company.get("currency")).strip()
        for company in companies
    ):
        return _scope_payload("unavailable", "unavailable", role_scope, "company_lookup_malformed")
    requested = cstr(requested_company or "").strip()

    injected_company_count = None
    if site_enabled_company_count is not _COMPANY_SCOPE_UNSET:
        try:
            injected_company_count = int(site_enabled_company_count)
        except (TypeError, ValueError):
            return _scope_payload("unavailable", "unavailable", role_scope, "company_count_input_invalid")
        if injected_company_count < 0:
            return _scope_payload("unavailable", "unavailable", role_scope, "company_count_input_invalid")

    if not companies or injected_company_count == 0:
        return _scope_payload("unavailable", "unavailable", role_scope, "no_enabled_company")

    single_visible_company = len(companies) == 1 and injected_company_count in (None, 1)
    if company_user_permissions is _COMPANY_SCOPE_UNSET and single_visible_company:
        if requested and requested != companies[0].get("name"):
            return _scope_payload(
                "restricted",
                "restricted",
                role_scope,
                "requested_company_outside_scope",
                available_company_count=1,
            )
        return _scope_payload(
            "scoped",
            "single_company_site_fallback",
            role_scope,
            "single_permission_visible_company_without_user_permission_read",
            companies[0],
            1,
        )

    if company_user_permissions is _COMPANY_SCOPE_UNSET:
        # Frappe get_list can queue a browser-visible permission message before
        # raising. Never attempt this read unless the non-throwing authority
        # check proves it is safe for the current user.
        permission_values = (
            _load_company_user_permission_values(user)
            if _can_read_company_user_permissions(user)
            else None
        )
    else:
        raw_permission_values = list(company_user_permissions or [])
        permission_values = [cstr(value).strip() for value in raw_permission_values if cstr(value).strip()]
        if len(permission_values) != len(raw_permission_values) or len(set(permission_values)) != len(permission_values):
            return _scope_payload("unavailable", "unavailable", role_scope, "company_permission_lookup_malformed")

    if permission_values:
        allowed = [company_by_name[value] for value in permission_values if value in company_by_name]
        if requested:
            if requested not in {cstr(company.get("name")) for company in allowed}:
                return _scope_payload(
                    "restricted",
                    "restricted",
                    role_scope,
                    "requested_company_outside_scope",
                    available_company_count=len(allowed),
                )
            return _scope_payload(
                "scoped",
                "company_user_permission",
                role_scope,
                "requested_company_allowed",
                company_by_name[requested],
                len(allowed),
            )
        if len(allowed) == 1:
            return _scope_payload(
                "scoped",
                "company_user_permission",
                role_scope,
                "single_company_permission",
                allowed[0],
                1,
            )
        if len(allowed) > 1:
            return _scope_payload(
                "selection_required",
                "selection_required",
                role_scope,
                "multiple_company_permissions_require_selection",
                available_company_count=len(allowed),
            )
        return _scope_payload("unavailable", "unavailable", role_scope, "company_permission_not_enabled")

    # Explicitly injected policy inputs retain the pure resolver contract used
    # by source tests; runtime one-company fallback has already returned above.
    if single_visible_company:
        if requested and requested != companies[0].get("name"):
            return _scope_payload(
                "restricted",
                "restricted",
                role_scope,
                "requested_company_outside_scope",
                available_company_count=1,
            )
        return _scope_payload(
            "scoped",
            "single_company_site_fallback",
            role_scope,
            "single_permission_visible_company"
            if permission_values is not None
            else "single_permission_visible_company_without_user_permission_read",
            companies[0],
            1,
        )

    if permission_values is None:
        return _scope_payload("unavailable", "unavailable", role_scope, "company_permission_lookup_unavailable")

    if requested:
        return _scope_payload(
            "restricted",
            "restricted",
            role_scope,
            "company_user_permission_required_for_multi_company",
        )
    return _scope_payload(
        "unavailable",
        "unavailable",
        role_scope,
        "company_user_permission_required_for_multi_company",
    )


def receivables_aging_bucket_contract() -> list[dict[str, object]]:
    return [dict(bucket) for bucket in RECEIVABLES_COUNT_BUCKETS]


def receivables_source_read_contract() -> dict[str, object]:
    return {
        "phase": FINANCE_RECEIVABLES_SOURCE_POLICY_PHASE,
        "allowed_future_source": RECEIVABLES_COUNT_SOURCE,
        "allowed_internal_fields": sorted(RECEIVABLES_ALLOWED_INTERNAL_FIELDS),
        "blocked_browser_fields": sorted(RECEIVABLES_BLOCKED_BROWSER_FIELDS),
        "blocked_sources": sorted(RECEIVABLES_BLOCKED_SOURCES),
        "required_filters": {
            "company": "selected_allowed_company_from_f4b_resolver",
            "docstatus": 1,
            "outstanding_amount": "> 0",
            "is_return": "exclude_first_cycle",
            "return_against": "exclude_first_cycle",
        },
        "aging_basis": {
            "as_of_date_source": "backend_defined_request_date",
            "date_field": "due_date_internal_only",
            "payment_schedule_basis": "deferred_until_explicit_policy",
            "timezone_policy": "backend_site_timezone_required_before_runtime",
        },
        "aging_buckets": receivables_aging_bucket_contract(),
        "invoice_semantics": {
            "submitted_only": True,
            "cancelled_excluded": True,
            "amended_or_reversed_records_excluded": True,
            "positive_outstanding_only": True,
            "returns_excluded_first_cycle": True,
            "credit_notes_excluded_first_cycle": True,
            "missing_due_date_policy": "fail_closed_before_bucket_counts",
            "payment_schedule_policy": "deferred_until_explicit_policy",
        },
        "low_count_policy": {
            "manager": "allow_bucket_counts_without_customer_or_invoice_identifiers",
            "normal_finance": "suppress_or_coarsen_low_counts_before_runtime_enablement",
            "audit_candidate": "future_read_only_only_after_audit_scope_approval",
            "runtime_threshold_ready": False,
        },
        "f4d_runtime_prerequisites": [
            "server_side_resolver_dependency",
            "no_client_supplied_company_scope_trust",
            "count_fixture_bucket_boundary_tests",
            "submitted_only_and_positive_outstanding_tests",
            "return_and_credit_note_exclusion_tests",
            "low_count_suppression_tests",
            "narrow_permission_preserving_get_list_spy_if_query_is_added",
        ],
        "report_passthrough_enabled": False,
        "runtime_query_enabled": False,
        "count_runtime_enabled": False,
        "source_permission_probe_enabled": False,
        "source_permission_verified": False,
        "amount_visibility_enabled": False,
    }


def build_receivables_source_read_policy(
    resolver: dict[str, object] | None,
    source: str = RECEIVABLES_COUNT_SOURCE,
) -> dict[str, object]:
    contract = receivables_source_read_contract()
    source_name = cstr(source or "").strip()
    resolver_state = cstr((resolver or {}).get("state") or "").strip()
    role_category = cstr((resolver or {}).get("role_category") or "").strip()
    selected_company = (resolver or {}).get("selected_company") if isinstance(resolver, dict) else None

    reason = "resolver_scope_required"
    source_allowed = False
    policy_contract_accepted = False
    resolver_scoped = resolver_state == "scoped" and bool(selected_company)
    role_eligible = role_category == "manager"
    source_permission_verified = False
    if source_name in RECEIVABLES_BLOCKED_SOURCES:
        reason = "source_blocked_for_f4c"
    elif source_name != RECEIVABLES_COUNT_SOURCE:
        reason = "source_not_allowed_for_f4c"
    elif not resolver_scoped:
        reason = "resolver_not_scoped"
    elif role_category == "normal_finance":
        reason = "low_count_policy_not_ready"
        source_allowed = True
    elif role_category != "manager":
        reason = "role_not_approved_for_f4c_counts"
    else:
        reason = "source_permission_not_verified"
        source_allowed = True
        policy_contract_accepted = True

    return {
        "phase": FINANCE_RECEIVABLES_SOURCE_POLICY_PHASE,
        "state": "policy_contract_accepted" if policy_contract_accepted else "not_ready",
        "reason": reason,
        "source": source_name,
        "source_allowed": source_allowed,
        "policy_contract_accepted": policy_contract_accepted,
        "policy_preconditions_ready": policy_contract_accepted,
        "resolver_scoped": resolver_scoped,
        "role_eligible_for_count_policy": role_eligible,
        "source_permission_verified": source_permission_verified,
        "source_permission_probe_enabled": False,
        "source_read_policy_ready": False,
        "runtime_count_enabled": False,
        "resolver_state": resolver_state or "missing",
        "role_category": role_category or "missing",
        "selected_company": selected_company if policy_contract_accepted else None,
        "contract": contract,
        "response_contract": {
            "allowed_response_keys": sorted(RECEIVABLES_COUNT_RESPONSE_KEYS),
            "blocked_empty_placeholder_keys": sorted(RECEIVABLES_BLOCKED_EMPTY_PLACEHOLDER_KEYS),
            "rows": [],
            "metrics": [],
            "amounts": [],
            "documents": [],
            "customer_identifiers_enabled": False,
            "invoice_identifiers_enabled": False,
            "native_route_enabled": False,
            "report_enabled": False,
            "export_enabled": False,
            "execution_enabled": False,
        },
        "rows": [],
        "metrics": [],
        "amounts": [],
        "documents": [],
        "no_effect": no_effect_flags(),
        "ar_runtime_data_enabled": False,
        "amount_visibility_enabled": False,
        "count_runtime_enabled": False,
    }

def _normalize_as_of_date(value: object = None) -> date:
    if isinstance(value, datetime):
        raise TypeError("financial as-of date must not include time or timezone")
    if isinstance(value, date):
        return value
    if value is not None:
        if not isinstance(value, str):
            raise TypeError("financial as-of date must be a string or date object")
        text = value
        if len(text) != 10 or text[4] != "-" or text[7] != "-" or not (text[:4] + text[5:7] + text[8:]).isdigit():
            raise ValueError("financial as-of date must be an exact ISO calendar date")
        parsed = date.fromisoformat(text)
        if parsed.isoformat() != text:
            raise ValueError("financial as-of date must be an exact ISO calendar date")
        return parsed

    current = now_datetime()
    if isinstance(current, datetime):
        return current.date()
    if isinstance(current, date):
        return current
    raise ValueError("server financial as-of date is unavailable")


def _bucket_labels() -> list[dict[str, str]]:
    return [{"key": cstr(bucket.get("key")), "label": cstr(bucket.get("label"))} for bucket in RECEIVABLES_COUNT_BUCKETS]


def _receivables_base_count_filters(company_name: str, as_of: date | None = None) -> list[list[object]]:
    filters = [
        ["company", "=", company_name],
        ["docstatus", "=", 1],
        ["outstanding_amount", ">", 0],
        ["is_return", "=", 0],
        ["return_against", "is", "not set"],
    ]
    if as_of:
        filters.append(["posting_date", "<=", as_of.isoformat()])
    return filters


def _receivables_bucket_filters(company_name: str, bucket_key: str, as_of: date) -> list[list[object]]:
    filters = _receivables_base_count_filters(company_name, as_of)
    if bucket_key == "current":
        filters.append(["due_date", ">=", as_of.isoformat()])
    elif bucket_key == "overdue_1_30":
        filters.append(["due_date", "between", [(as_of - timedelta(days=30)).isoformat(), (as_of - timedelta(days=1)).isoformat()]])
    elif bucket_key == "overdue_31_60":
        filters.append(["due_date", "between", [(as_of - timedelta(days=60)).isoformat(), (as_of - timedelta(days=31)).isoformat()]])
    elif bucket_key == "overdue_61_90":
        filters.append(["due_date", "between", [(as_of - timedelta(days=90)).isoformat(), (as_of - timedelta(days=61)).isoformat()]])
    elif bucket_key == "overdue_over_90":
        filters.append(["due_date", "<=", (as_of - timedelta(days=91)).isoformat()])
    else:
        filters.append(["due_date", "is", "set"])
    return filters


def _receivables_missing_due_date_filters(company_name: str, as_of: date) -> list[list[object]]:
    filters = _receivables_base_count_filters(company_name, as_of)
    filters.append(["due_date", "is", "not set"])
    return filters


def _receivables_count_with_extra_filter(
    company_name: str,
    as_of: date,
    extra_filter: list[object],
    list_getter: object = None,
    include_future_posting: bool = False,
) -> int:
    filters = _receivables_base_count_filters(company_name, None if include_future_posting else as_of)
    filters.append(extra_filter)
    return _permission_preserving_receivables_count(filters, list_getter=list_getter)


def _permission_preserving_receivables_schedule_presence_count(
    company_name: str,
    as_of: date,
    list_getter: object = None,
) -> int:
    # The future Payment Ledger gate runs first. With later activity excluded,
    # only currently positive-outstanding invoices are schedule candidates.
    filters = [
        ["company", "=", company_name],
        ["docstatus", "=", 1],
        ["posting_date", "<=", as_of.isoformat()],
        ["outstanding_amount", ">", 0],
        ["is_return", "=", 0],
        ["return_against", "is", "not set"],
    ]
    filters.extend(
        (
            [RECEIVABLES_SCHEDULE_CHILD_SOURCE, "parent", "is", "set"],
            [RECEIVABLES_SCHEDULE_CHILD_SOURCE, "parenttype", "=", RECEIVABLES_COUNT_SOURCE],
            [RECEIVABLES_SCHEDULE_CHILD_SOURCE, "parentfield", "=", "payment_schedule"],
        )
    )
    return _permission_preserving_receivables_count(filters, list_getter=list_getter)


def _permission_preserving_receivables_schedule_integrity_gate(
    company_name: str,
    as_of: date,
    list_getter: object = None,
) -> int:
    """Detect schedule relationships that can affect selected-company candidates."""
    getter = list_getter or getattr(frappe, "get_list", None)
    if not callable(getter):
        raise _ReceivablesCountUnavailable(RECEIVABLES_SCHEDULE_INTEGRITY_INVALID_REASON)

    candidate_limit = int(RECEIVABLES_SCHEDULE_CANDIDATE_MAX_ROWS)
    integrity_limit = int(RECEIVABLES_SCHEDULE_INTEGRITY_MAX_ROWS)
    if candidate_limit <= 0 or integrity_limit <= 1:
        raise _ReceivablesCountUnavailable(RECEIVABLES_SCHEDULE_INTEGRITY_INVALID_REASON)

    try:
        candidates = _permission_preserving_list_call(
            getter,
            RECEIVABLES_COUNT_SOURCE,
            filters=_receivables_base_count_filters(company_name, as_of),
            fields=["name"],
            order_by="name asc",
            limit_start=0,
            limit_page_length=candidate_limit + 1,
        )
    except Exception:
        raise _ReceivablesCountUnavailable(RECEIVABLES_SCHEDULE_INTEGRITY_INVALID_REASON)
    if not isinstance(candidates, list) or len(candidates) > candidate_limit:
        raise _ReceivablesCountUnavailable(RECEIVABLES_SCHEDULE_INTEGRITY_INVALID_REASON)

    candidate_names: list[str] = []
    for row in candidates:
        if not isinstance(row, dict) or set(row) != {"name"}:
            raise _ReceivablesCountUnavailable(RECEIVABLES_SCHEDULE_INTEGRITY_INVALID_REASON)
        name = cstr(row.get("name") or "").strip()
        if not name or name in candidate_names:
            raise _ReceivablesCountUnavailable(RECEIVABLES_SCHEDULE_INTEGRITY_INVALID_REASON)
        candidate_names.append(name)

    if not candidate_names:
        return 0
    try:
        relationships = _permission_preserving_list_call(
            getter,
            RECEIVABLES_SCHEDULE_CHILD_SOURCE,
            filters=[["parent", "in", candidate_names]],
            fields=["parent", "parenttype", "parentfield"],
            parent_doctype=RECEIVABLES_COUNT_SOURCE,
            order_by="parent asc",
            limit_start=0,
            limit_page_length=integrity_limit,
        )
    except Exception:
        raise _ReceivablesCountUnavailable(RECEIVABLES_SCHEDULE_INTEGRITY_INVALID_REASON)
    if not isinstance(relationships, list) or len(relationships) >= integrity_limit:
        raise _ReceivablesCountUnavailable(RECEIVABLES_SCHEDULE_INTEGRITY_INVALID_REASON)

    candidate_set = set(candidate_names)
    for row in relationships:
        if not isinstance(row, dict) or set(row) != {"parent", "parenttype", "parentfield"}:
            raise _ReceivablesCountUnavailable(RECEIVABLES_SCHEDULE_INTEGRITY_INVALID_REASON)
        parent = cstr(row.get("parent") or "").strip()
        parenttype = cstr(row.get("parenttype") or "").strip()
        parentfield = cstr(row.get("parentfield") or "").strip()
        if not parent or parent not in candidate_set:
            raise _ReceivablesCountUnavailable(RECEIVABLES_SCHEDULE_INTEGRITY_INVALID_REASON)
        if parenttype != RECEIVABLES_COUNT_SOURCE or parentfield != "payment_schedule":
            raise _ReceivablesCountUnavailable(RECEIVABLES_SCHEDULE_INTEGRITY_INVALID_REASON)

    return len(relationships)


class _ReceivablesCountUnavailable(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def _extract_count(records: object, invalid_reason: str = RECEIVABLES_COUNT_SOURCE_INVALID_REASON) -> int:
    if not isinstance(records, list) or len(records) != 1:
        raise _ReceivablesCountUnavailable(invalid_reason)
    first = records[0]
    if not isinstance(first, dict) or set(first) != {"count"}:
        raise _ReceivablesCountUnavailable(invalid_reason)
    value = first.get("count")
    if isinstance(value, bool) or value in (None, ""):
        raise _ReceivablesCountUnavailable(invalid_reason)
    try:
        count = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise _ReceivablesCountUnavailable(invalid_reason)
    if count < 0 or count != count.to_integral_value():
        raise _ReceivablesCountUnavailable(invalid_reason)
    return int(count)


def verify_receivables_source_permission(
    context: dict[str, object] | None = None,
    permission_checker: object = None,
) -> dict[str, object]:
    checker = permission_checker or getattr(frappe, "has_permission", None)
    user = cstr((context or {}).get("user") or getattr(frappe.session, "user", None) or "").strip()
    if not callable(checker):
        return {
            "source": RECEIVABLES_COUNT_SOURCE,
            "source_permission_checked": False,
            "source_permission_verified": False,
            "reason": "source_permission_checker_unavailable",
        }
    try:
        allowed = bool(checker(RECEIVABLES_COUNT_SOURCE, ptype="read", user=user or None))
    except TypeError:
        try:
            allowed = bool(checker(RECEIVABLES_COUNT_SOURCE, "read"))
        except Exception:
            allowed = False
    except Exception:
        allowed = False
    return {
        "source": RECEIVABLES_COUNT_SOURCE,
        "source_permission_checked": True,
        "source_permission_verified": allowed,
        "reason": "source_permission_allowed" if allowed else "source_permission_denied",
    }


def _permission_preserving_receivables_count(filters: list[list[object]], list_getter: object = None) -> int:
    getter = list_getter or getattr(frappe, "get_list", None)
    if not callable(getter):
        raise RuntimeError("permission_preserving_count_reader_unavailable")
    records = _permission_preserving_list_call(
        getter,
        RECEIVABLES_COUNT_SOURCE,
        filters=filters,
        fields=[RECEIVABLES_COUNT_QUERY_FIELD],
        limit_page_length=1,
    )
    return _extract_count(records or [])


def _permission_preserving_receivables_future_activity_count(
    company_name: str,
    as_of: date,
    list_getter: object = None,
) -> int:
    getter = list_getter or getattr(frappe, "get_list", None)
    if not callable(getter):
        raise _ReceivablesCountUnavailable("future_payment_ledger_activity_gate_unavailable")
    try:
        records = _permission_preserving_list_call(
            getter,
            RECEIVABLES_AMOUNT_SOURCE,
            filters=[
                ["company", "=", company_name],
                ["account_type", "=", "Receivable"],
                ["party_type", "=", "Customer"],
                ["delinked", "=", 0],
                ["posting_date", ">", as_of.isoformat()],
            ],
            fields=[RECEIVABLES_COUNT_QUERY_FIELD],
            limit_page_length=1,
        )
        return _extract_count(records or [], "future_payment_ledger_activity_gate_invalid")
    except _ReceivablesCountUnavailable:
        raise
    except Exception:
        raise _ReceivablesCountUnavailable("future_payment_ledger_activity_gate_unavailable")


def _safe_count_policy(
    resolver: dict[str, object],
    policy: dict[str, object],
    permission: dict[str, object],
    reason: str,
    runtime_enabled: bool = False,
) -> dict[str, object]:
    return {
        "source": RECEIVABLES_COUNT_SOURCE,
        "reason": reason,
        "resolver_state": resolver.get("state"),
        "resolver_source": resolver.get("source"),
        "role_category": resolver.get("role_category"),
        "policy_contract_accepted": bool(policy.get("policy_contract_accepted")),
        "resolver_scoped": bool(policy.get("resolver_scoped")),
        "role_eligible_for_count_policy": bool(policy.get("role_eligible_for_count_policy")),
        "source_permission_checked": bool(permission.get("source_permission_checked")),
        "source_permission_verified": bool(permission.get("source_permission_verified")),
        "future_activity_source_permission_checked": bool(permission.get("future_activity_source_permission_checked")),
        "future_activity_source_permission_verified": bool(permission.get("future_activity_source_permission_verified")),
        "source_read_policy_ready": runtime_enabled,
        "runtime_count_enabled": runtime_enabled,
        "low_count_suppression_ready": False,
        "manager_aggregate_counts_only": True,
        "count_source": RECEIVABLES_COUNT_SOURCE,
        "semantic_guard_sources": [RECEIVABLES_SCHEDULE_CHILD_SOURCE, RECEIVABLES_AMOUNT_SOURCE],
        "payment_schedule_supported": False,
        "payment_schedule_presence_gate_required": True,
        "future_posting_supported": False,
        "future_payment_ledger_activity_supported": False,
        "accounts_user_raw_counts_enabled": False,
        "identifiers_enabled": False,
        "monetary_values_enabled": False,
        "native_navigation_enabled": False,
        "external_output_enabled": False,
        "execution_enabled": False,
    }


def _receivables_count_payload(
    state_value: str,
    reason: str,
    resolver: dict[str, object],
    policy: dict[str, object],
    permission: dict[str, object],
    as_of: date,
    bucket_counts: dict[str, int] | None = None,
) -> dict[str, object]:
    runtime_enabled = state_value == "ready"
    selected_company = resolver.get("selected_company") if isinstance(resolver, dict) else None
    return {
        "phase": FINANCE_RECEIVABLES_COUNT_PHASE,
        "state": state_value,
        "company_scope": selected_company if runtime_enabled else None,
        "as_of_date": as_of.isoformat(),
        "bucket_labels": _bucket_labels(),
        "bucket_counts": dict(bucket_counts or {}),
        "policy": _safe_count_policy(resolver, policy, permission, reason, runtime_enabled=runtime_enabled),
        "no_effect": no_effect_flags(),
        "rows_returned": False,
        "amounts_returned": False,
        "documents_returned": False,
        "runtime_count_enabled": runtime_enabled,
    }


def build_receivables_count_posture(
    context: dict[str, object] | None = None,
    requested_company: str | None = None,
    resolver: dict[str, object] | None = None,
    as_of_date: object = None,
    permission_checker: object = None,
    list_getter: object = None,
) -> dict[str, object]:
    active_context = context or build_context()
    active_resolver = resolver or resolve_finance_role_company_scope(
        context=active_context,
        requested_company=requested_company,
    )
    invalid_as_of = False
    try:
        as_of = _normalize_as_of_date(as_of_date)
    except (TypeError, ValueError):
        as_of = _normalize_as_of_date()
        invalid_as_of = True
    policy = build_receivables_source_read_policy(active_resolver)
    empty_permission = {
        "source": RECEIVABLES_COUNT_SOURCE,
        "source_permission_checked": False,
        "source_permission_verified": False,
        "reason": "source_permission_not_checked",
    }
    if invalid_as_of:
        return _receivables_count_payload("unavailable", "invalid_as_of_date", active_resolver, policy, empty_permission, as_of)
    if not policy.get("policy_contract_accepted"):
        reason = cstr(policy.get("reason") or "receivables_count_policy_not_ready")
        if active_resolver.get("state") != "scoped":
            reason = cstr(active_resolver.get("reason") or reason)
        return _receivables_count_payload("unavailable", reason, active_resolver, policy, empty_permission, as_of)

    permission = verify_receivables_source_permission(active_context, permission_checker=permission_checker)
    if not permission.get("source_permission_verified"):
        return _receivables_count_payload("unavailable", "source_permission_denied", active_resolver, policy, permission, as_of)

    future_activity_permission = verify_receivables_amount_source_permission(active_context, permission_checker=permission_checker)
    permission = dict(permission)
    permission["future_activity_source_permission_checked"] = bool(future_activity_permission.get("source_permission_checked"))
    permission["future_activity_source_permission_verified"] = bool(future_activity_permission.get("source_permission_verified"))
    if not future_activity_permission.get("source_permission_verified"):
        return _receivables_count_payload(
            "unavailable",
            "future_payment_ledger_activity_permission_unavailable",
            active_resolver,
            policy,
            permission,
            as_of,
        )

    selected_company = active_resolver.get("selected_company") if isinstance(active_resolver, dict) else None
    company_name = cstr((selected_company or {}).get("name") if isinstance(selected_company, dict) else "").strip()
    if not company_name:
        return _receivables_count_payload("unavailable", "selected_company_required", active_resolver, policy, permission, as_of)

    try:
        future_activity_count = _permission_preserving_receivables_future_activity_count(
            company_name,
            as_of,
            list_getter=list_getter,
        )
        if future_activity_count > 0:
            return _receivables_count_payload(
                "unavailable",
                "future_payment_ledger_activity_not_supported",
                active_resolver,
                policy,
                permission,
                as_of,
            )
        future_posted_count = _receivables_count_with_extra_filter(
            company_name,
            as_of,
            ["posting_date", ">", as_of.isoformat()],
            list_getter=list_getter,
            include_future_posting=True,
        )
        if future_posted_count > 0:
            return _receivables_count_payload("unavailable", "future_posting_date_not_supported", active_resolver, policy, permission, as_of)
        payment_terms_count = _receivables_count_with_extra_filter(
            company_name,
            as_of,
            ["payment_terms_template", "is", "set"],
            list_getter=list_getter,
        )
        if payment_terms_count > 0:
            return _receivables_count_payload("unavailable", "payment_terms_not_supported", active_resolver, policy, permission, as_of)
        if _permission_preserving_receivables_schedule_presence_count(company_name, as_of, list_getter=list_getter) > 0:
            return _receivables_count_payload("unavailable", "payment_schedule_not_supported", active_resolver, policy, permission, as_of)
        if _permission_preserving_receivables_schedule_integrity_gate(
            company_name,
            as_of,
            list_getter=list_getter,
        ) > 0:
            return _receivables_count_payload("unavailable", "payment_schedule_not_supported", active_resolver, policy, permission, as_of)
        missing_due_date_count = _permission_preserving_receivables_count(
            _receivables_missing_due_date_filters(company_name, as_of),
            list_getter=list_getter,
        )
        if missing_due_date_count > 0:
            return _receivables_count_payload("unavailable", "missing_due_date_policy_not_ready", active_resolver, policy, permission, as_of)
        bucket_counts = {
            cstr(bucket.get("key")): _permission_preserving_receivables_count(
                _receivables_bucket_filters(company_name, cstr(bucket.get("key")), as_of),
                list_getter=list_getter,
            )
            for bucket in RECEIVABLES_COUNT_BUCKETS
        }
    except _ReceivablesCountUnavailable as exc:
        return _receivables_count_payload("unavailable", exc.reason, active_resolver, policy, permission, as_of)
    except Exception:
        return _receivables_count_payload("unavailable", "permission_preserving_count_unavailable", active_resolver, policy, permission, as_of)

    return _receivables_count_payload("ready", "receivables_count_posture_ready", active_resolver, policy, permission, as_of, bucket_counts)




def _payables_bucket_labels() -> list[dict[str, str]]:
    return [{"key": cstr(bucket.get("key")), "label": cstr(bucket.get("label"))} for bucket in PAYABLES_COUNT_BUCKETS]


def _payables_candidate_count_filters(company_name: str) -> list[list[object]]:
    return [
        ["company", "=", company_name],
        ["docstatus", "=", 1],
        ["outstanding_amount", ">", 0],
        ["is_return", "=", 0],
        ["return_against", "is", "not set"],
    ]


def _payables_open_count_filters(company_name: str) -> list[list[object]]:
    filters = _payables_candidate_count_filters(company_name)
    filters.append(["status", "in", list(PAYABLES_OPEN_STATUSES)])
    return filters


def _payables_submitted_company_filters(company_name: str) -> list[list[object]]:
    return [["company", "=", company_name], ["docstatus", "=", 1]]


def _payables_bucket_filters(company_name: str, bucket_key: str, as_of: date) -> list[list[object]]:
    filters = _payables_open_count_filters(company_name)
    if bucket_key == "not_due":
        filters.append(["due_date", ">=", as_of.isoformat()])
    elif bucket_key == "overdue_1_30":
        filters.append(["due_date", "between", [(as_of - timedelta(days=30)).isoformat(), (as_of - timedelta(days=1)).isoformat()]])
    elif bucket_key == "overdue_31_60":
        filters.append(["due_date", "between", [(as_of - timedelta(days=60)).isoformat(), (as_of - timedelta(days=31)).isoformat()]])
    elif bucket_key == "overdue_61_90":
        filters.append(["due_date", "between", [(as_of - timedelta(days=90)).isoformat(), (as_of - timedelta(days=61)).isoformat()]])
    elif bucket_key == "overdue_over_90":
        filters.append(["due_date", "<=", (as_of - timedelta(days=91)).isoformat()])
    else:
        filters.append(["due_date", "is", "set"])
    return filters


class _PayablesCountUnavailable(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def _extract_payables_count(records: object, invalid_reason: str = PAYABLES_COUNT_SOURCE_INVALID_REASON) -> int:
    try:
        return _extract_count(records, invalid_reason)
    except _ReceivablesCountUnavailable as exc:
        raise _PayablesCountUnavailable(exc.reason)


def verify_payables_source_permission(
    context: dict[str, object] | None = None,
    permission_checker: object = None,
) -> dict[str, object]:
    checker = permission_checker or getattr(frappe, "has_permission", None)
    user = cstr((context or {}).get("user") or getattr(frappe.session, "user", None) or "").strip()
    if not callable(checker):
        return {
            "source": PAYABLES_COUNT_SOURCE,
            "source_permission_checked": False,
            "source_permission_verified": False,
            "reason": "source_permission_checker_unavailable",
        }
    try:
        allowed = bool(checker(PAYABLES_COUNT_SOURCE, ptype="read", user=user or None))
    except TypeError:
        try:
            allowed = bool(checker(PAYABLES_COUNT_SOURCE, "read"))
        except Exception:
            allowed = False
    except Exception:
        allowed = False
    return {
        "source": PAYABLES_COUNT_SOURCE,
        "source_permission_checked": True,
        "source_permission_verified": allowed,
        "reason": "source_permission_allowed" if allowed else "source_permission_denied",
    }


def _permission_preserving_payables_count(filters: list[list[object]], list_getter: object = None) -> int:
    getter = list_getter or getattr(frappe, "get_list", None)
    if not callable(getter):
        raise _PayablesCountUnavailable("permission_preserving_payables_count_reader_unavailable")
    try:
        records = _permission_preserving_list_call(
            getter,
            PAYABLES_COUNT_SOURCE,
            filters=filters,
            fields=[PAYABLES_COUNT_QUERY_FIELD],
            limit_page_length=1,
        )
    except Exception:
        raise _PayablesCountUnavailable("permission_preserving_payables_count_unavailable")
    return _extract_payables_count(records)


def verify_payables_future_activity_source_permission(
    context: dict[str, object] | None = None,
    permission_checker: object = None,
) -> dict[str, object]:
    checker = permission_checker or getattr(frappe, "has_permission", None)
    user = cstr((context or {}).get("user") or getattr(frappe.session, "user", None) or "").strip()
    if not callable(checker):
        return {
            "future_activity_source_permission_checked": False,
            "future_activity_source_permission_verified": False,
            "reason": "future_activity_source_permission_checker_unavailable",
        }
    try:
        allowed = bool(checker(PAYABLES_FUTURE_ACTIVITY_SOURCE, ptype="read", user=user or None))
    except TypeError:
        try:
            allowed = bool(checker(PAYABLES_FUTURE_ACTIVITY_SOURCE, "read"))
        except Exception:
            allowed = False
    except Exception:
        allowed = False
    return {
        "future_activity_source_permission_checked": True,
        "future_activity_source_permission_verified": allowed,
        "reason": "future_activity_source_permission_allowed" if allowed else "future_activity_source_permission_denied",
    }


def _permission_preserving_payables_future_activity_count(
    company_name: str,
    as_of: date,
    list_getter: object = None,
) -> int:
    getter = list_getter or getattr(frappe, "get_list", None)
    if not callable(getter):
        raise _PayablesCountUnavailable("permission_preserving_payables_future_activity_reader_unavailable")
    try:
        records = _permission_preserving_list_call(
            getter,
            PAYABLES_FUTURE_ACTIVITY_SOURCE,
            filters=[
                ["company", "=", company_name],
                ["party_type", "=", "Supplier"],
                ["delinked", "=", 0],
                ["posting_date", ">", as_of.isoformat()],
            ],
            fields=[PAYABLES_COUNT_QUERY_FIELD],
            limit_page_length=1,
        )
    except Exception:
        raise _PayablesCountUnavailable("permission_preserving_payables_future_activity_unavailable")
    return _extract_payables_count(records, PAYABLES_FUTURE_ACTIVITY_SOURCE_INVALID_REASON)


def _payables_count_with_extra_filter(company_name: str, extra_filter: list[object], list_getter: object = None, base: str = "open") -> int:
    filters = _payables_open_count_filters(company_name) if base == "open" else _payables_submitted_company_filters(company_name)
    filters.append(extra_filter)
    return _permission_preserving_payables_count(filters, list_getter=list_getter)


def _permission_preserving_payables_schedule_presence_count(company_name: str, list_getter: object = None) -> int:
    filters = _payables_open_count_filters(company_name)
    filters.extend(
        (
            [PAYABLES_SCHEDULE_CHILD_SOURCE, "parent", "is", "set"],
            [PAYABLES_SCHEDULE_CHILD_SOURCE, "parenttype", "=", PAYABLES_COUNT_SOURCE],
            [PAYABLES_SCHEDULE_CHILD_SOURCE, "parentfield", "=", "payment_schedule"],
        )
    )
    return _permission_preserving_payables_count(filters, list_getter=list_getter)


def _safe_payables_policy(
    resolver: dict[str, object],
    permission: dict[str, object],
    reason: str,
    runtime_enabled: bool = False,
) -> dict[str, object]:
    return {
        "source": PAYABLES_COUNT_SOURCE,
        "reason": reason,
        "resolver_state": resolver.get("state"),
        "resolver_source": resolver.get("source"),
        "role_category": resolver.get("role_category"),
        "source_permission_checked": bool(permission.get("source_permission_checked")),
        "source_permission_verified": bool(permission.get("source_permission_verified")),
        "future_activity_source": PAYABLES_FUTURE_ACTIVITY_SOURCE,
        "future_activity_source_permission_checked": bool(permission.get("future_activity_source_permission_checked")),
        "future_activity_source_permission_verified": bool(permission.get("future_activity_source_permission_verified")),
        "future_activity_gate_required": True,
        "future_payment_ledger_activity_supported": False,
        "source_read_policy_ready": runtime_enabled,
        "runtime_count_enabled": runtime_enabled,
        "manager_only": True,
        "accounts_user_counts_enabled": False,
        "aggregate_counts_only": True,
        "due_date_basis_only": True,
        "posting_date_fallback_enabled": False,
        "due_soon_enabled": False,
        "payment_terms_supported": False,
        "payment_schedule_supported": False,
        "payment_schedule_presence_gate_required": True,
        "payment_schedule_rows_returned": False,
        "on_hold_supported": False,
        "returns_supported": False,
        "identifiers_enabled": False,
        "monetary_values_enabled": False,
        "native_navigation_enabled": False,
        "external_output_enabled": False,
        "execution_enabled": False,
    }


def _payables_company_scope(selected_company: object, runtime_enabled: bool) -> dict[str, object] | None:
    if not runtime_enabled or not isinstance(selected_company, dict):
        return None
    return {
        "name": selected_company.get("name"),
        "label": selected_company.get("label") or selected_company.get("name"),
    }


def _payables_count_payload(
    state_value: str,
    reason: str,
    resolver: dict[str, object],
    permission: dict[str, object],
    as_of: date,
    bucket_counts: dict[str, int] | None = None,
) -> dict[str, object]:
    runtime_enabled = state_value == "ready"
    selected_company = resolver.get("selected_company") if isinstance(resolver, dict) else None
    return {
        "phase": FINANCE_PAYABLES_COUNT_PHASE,
        "state": state_value,
        "source_state": state_value,
        "company_scope": _payables_company_scope(selected_company, runtime_enabled),
        "as_of_date": as_of.isoformat(),
        "bucket_labels": _payables_bucket_labels(),
        "bucket_counts": dict(bucket_counts or {}),
        "policy": _safe_payables_policy(resolver, permission, reason, runtime_enabled=runtime_enabled),
        "no_effect": no_effect_flags(),
    }


def build_payables_count_posture(
    context: dict[str, object] | None = None,
    requested_company: str | None = None,
    resolver: dict[str, object] | None = None,
    as_of_date: object = None,
    permission_checker: object = None,
    list_getter: object = None,
    browser_filters: dict[str, object] | None = None,
) -> dict[str, object]:
    active_context = context or build_context()
    active_resolver = resolver or resolve_finance_role_company_scope(
        context=active_context,
        requested_company=requested_company,
    )
    invalid_as_of = False
    try:
        as_of = _normalize_as_of_date(as_of_date)
    except (TypeError, ValueError):
        as_of = _normalize_as_of_date()
        invalid_as_of = True
    empty_permission = {
        "source": PAYABLES_COUNT_SOURCE,
        "source_permission_checked": False,
        "source_permission_verified": False,
        "future_activity_source_permission_checked": False,
        "future_activity_source_permission_verified": False,
        "reason": "source_permission_not_checked",
    }
    if invalid_as_of:
        return _payables_count_payload("unavailable", "invalid_as_of_date", active_resolver, empty_permission, as_of)
    if browser_filters:
        return _payables_count_payload("unavailable", "browser_filters_not_allowed", active_resolver, empty_permission, as_of)
    if active_resolver.get("state") != "scoped":
        return _payables_count_payload(
            "unavailable",
            cstr(active_resolver.get("reason") or "resolver_not_scoped"),
            active_resolver,
            empty_permission,
            as_of,
        )
    if active_resolver.get("role_category") != "manager":
        return _payables_count_payload("unavailable", "accounts_manager_required", active_resolver, empty_permission, as_of)

    selected_company = active_resolver.get("selected_company") if isinstance(active_resolver, dict) else None
    company_name = cstr((selected_company or {}).get("name") if isinstance(selected_company, dict) else "").strip()
    company_currency = cstr((selected_company or {}).get("currency") if isinstance(selected_company, dict) else "").strip()
    if company_name != FINANCE_APPROVED_COMPANY_NAME or company_currency != FINANCE_APPROVED_COMPANY_CURRENCY:
        return _payables_count_payload("unavailable", "approved_company_scope_required", active_resolver, empty_permission, as_of)

    permission = verify_payables_source_permission(active_context, permission_checker=permission_checker)
    if not permission.get("source_permission_verified"):
        return _payables_count_payload("unavailable", "source_permission_denied", active_resolver, permission, as_of)
    permission.update(
        verify_payables_future_activity_source_permission(
            active_context,
            permission_checker=permission_checker,
        )
    )
    if not permission.get("future_activity_source_permission_verified"):
        return _payables_count_payload(
            "unavailable",
            "future_activity_source_permission_denied",
            active_resolver,
            permission,
            as_of,
        )

    try:
        candidate_count = _permission_preserving_payables_count(
            _payables_candidate_count_filters(company_name),
            list_getter=list_getter,
        )
        approved_status_count = _permission_preserving_payables_count(
            _payables_open_count_filters(company_name),
            list_getter=list_getter,
        )
        if candidate_count != approved_status_count:
            return _payables_count_payload(
                "unavailable",
                "purchase_invoice_status_not_supported",
                active_resolver,
                permission,
                as_of,
            )
        if _permission_preserving_payables_schedule_presence_count(company_name, list_getter=list_getter) > 0:
            return _payables_count_payload("unavailable", "payment_schedule_not_supported", active_resolver, permission, as_of)
        complexity_checks = (
            ("missing_due_date_policy_not_ready", ["due_date", "is", "not set"], "open"),
            ("future_posting_date_not_supported", ["posting_date", ">", as_of.isoformat()], "open"),
            ("payment_terms_not_supported", ["payment_terms_template", "is", "set"], "open"),
            ("advances_not_supported", ["total_advance", ">", 0], "open"),
            ("on_hold_not_supported", ["on_hold", "=", 1], "open"),
            ("returns_debit_notes_not_supported", ["is_return", "=", 1], "submitted"),
            ("returns_debit_notes_not_supported", ["return_against", "is", "set"], "submitted"),
        )
        for reason, extra_filter, base in complexity_checks:
            if _payables_count_with_extra_filter(company_name, extra_filter, list_getter=list_getter, base=base) > 0:
                return _payables_count_payload("unavailable", reason, active_resolver, permission, as_of)
        if _permission_preserving_payables_future_activity_count(company_name, as_of, list_getter=list_getter) > 0:
            return _payables_count_payload(
                "unavailable",
                "future_payment_ledger_activity_not_supported",
                active_resolver,
                permission,
                as_of,
            )
        bucket_counts = {
            cstr(bucket.get("key")): _permission_preserving_payables_count(
                _payables_bucket_filters(company_name, cstr(bucket.get("key")), as_of),
                list_getter=list_getter,
            )
            for bucket in PAYABLES_COUNT_BUCKETS
        }
    except _PayablesCountUnavailable as exc:
        return _payables_count_payload("unavailable", exc.reason, active_resolver, permission, as_of)
    except Exception:
        return _payables_count_payload("unavailable", "payables_count_posture_unavailable", active_resolver, permission, as_of)

    return _payables_count_payload("ready", "payables_count_posture_ready", active_resolver, permission, as_of, bucket_counts)


class _ReceivablesAmountUnavailable(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def verify_receivables_amount_source_permission(
    context: dict[str, object] | None = None,
    permission_checker: object = None,
) -> dict[str, object]:
    checker = permission_checker or getattr(frappe, "has_permission", None)
    user = cstr((context or {}).get("user") or getattr(frappe.session, "user", None) or "").strip()
    if not callable(checker):
        return {
            "source": RECEIVABLES_AMOUNT_SOURCE,
            "source_permission_checked": False,
            "source_permission_verified": False,
            "reason": "source_permission_checker_unavailable",
        }
    try:
        allowed = bool(checker(RECEIVABLES_AMOUNT_SOURCE, ptype="read", user=user or None))
    except TypeError:
        try:
            allowed = bool(checker(RECEIVABLES_AMOUNT_SOURCE, "read"))
        except Exception:
            allowed = False
    except Exception:
        allowed = False
    return {
        "source": RECEIVABLES_AMOUNT_SOURCE,
        "source_permission_checked": True,
        "source_permission_verified": allowed,
        "reason": "source_permission_allowed" if allowed else "source_permission_denied",
    }


def _metadata_field_options(meta: object, fieldname: str) -> str:
    getter = getattr(meta, "get_field", None)
    field = getter(fieldname) if callable(getter) else None
    if isinstance(field, dict):
        return cstr(field.get("options") or "")
    if field is not None:
        return cstr(getattr(field, "options", "") or "")
    for candidate in getattr(meta, "fields", []) or []:
        if isinstance(candidate, dict) and candidate.get("fieldname") == fieldname:
            return cstr(candidate.get("options") or "")
        if getattr(candidate, "fieldname", None) == fieldname:
            return cstr(getattr(candidate, "options", "") or "")
    return ""


def verify_receivables_amount_source_metadata(metadata_provider: object = None) -> dict[str, object]:
    provider = metadata_provider or getattr(frappe, "get_meta", None)
    if not callable(provider):
        return {
            "source": RECEIVABLES_AMOUNT_SOURCE,
            "source_metadata_checked": False,
            "source_metadata_verified": False,
            "reason": "source_metadata_provider_unavailable",
        }
    try:
        meta = provider(RECEIVABLES_AMOUNT_SOURCE)
    except Exception:
        return {
            "source": RECEIVABLES_AMOUNT_SOURCE,
            "source_metadata_checked": True,
            "source_metadata_verified": False,
            "reason": "source_metadata_unavailable",
        }
    amount_options = _metadata_field_options(meta, "amount")
    account_amount_options = _metadata_field_options(meta, "amount_in_account_currency")
    verified = amount_options == "Company:company:default_currency" and account_amount_options == "account_currency"
    return {
        "source": RECEIVABLES_AMOUNT_SOURCE,
        "source_metadata_checked": True,
        "source_metadata_verified": verified,
        "reason": "source_metadata_verified" if verified else "source_metadata_drift",
        "company_currency_amount_field": verified,
    }


def _strict_decimal_amount(value: object) -> Decimal:
    if value in (None, ""):
        raise _ReceivablesAmountUnavailable(RECEIVABLES_AMOUNT_SOURCE_INVALID_REASON)
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise _ReceivablesAmountUnavailable(RECEIVABLES_AMOUNT_SOURCE_INVALID_REASON)
    if not amount.is_finite():
        raise _ReceivablesAmountUnavailable(RECEIVABLES_AMOUNT_SOURCE_INVALID_REASON)
    return amount


def _currency_precision_contract(
    currency: str,
    precision_provider: object = None,
    rounding_method_getter: object = None,
) -> dict[str, object]:
    rounding_getter = rounding_method_getter or getattr(frappe, "get_system_settings", None)
    if currency != FINANCE_APPROVED_COMPANY_CURRENCY or not callable(rounding_getter):
        raise _ReceivablesAmountUnavailable(RECEIVABLES_AMOUNT_CURRENCY_CONTRACT_INVALID_REASON)
    try:
        if callable(precision_provider):
            raw_precision = precision_provider()
        else:
            from erpnext.accounts.utils import get_currency_precision

            raw_precision = get_currency_precision()
        if isinstance(raw_precision, bool):
            raise ValueError("boolean precision is invalid")
        precision_decimal = Decimal(str(raw_precision))
        if precision_decimal != precision_decimal.to_integral_value():
            raise ValueError("fractional precision is invalid")
        precision = int(precision_decimal)
        rounding_method = cstr(rounding_getter("rounding_method") or "").strip()
    except Exception:
        raise _ReceivablesAmountUnavailable(RECEIVABLES_AMOUNT_CURRENCY_CONTRACT_INVALID_REASON)
    rounding_modes = {
        "Banker's Rounding": ROUND_HALF_EVEN,
        "Commercial Rounding": ROUND_HALF_UP,
    }
    if precision < 0 or precision > 8 or rounding_method not in rounding_modes:
        raise _ReceivablesAmountUnavailable(RECEIVABLES_AMOUNT_CURRENCY_CONTRACT_INVALID_REASON)
    return {
        "currency": currency,
        "precision": precision,
        "precision_source": "erpnext.accounts.utils.get_currency_precision",
        "rounding_method": rounding_method,
        "rounding_mode": rounding_modes[rounding_method],
        "decimal_serialization": "fixed_string",
        "verified": True,
    }


def _currency_decimal_value(value: Decimal, currency_contract: dict[str, object]) -> Decimal:
    try:
        precision = int(currency_contract.get("precision"))
        rounding_mode = currency_contract.get("rounding_mode")
        quantum = Decimal(1).scaleb(-precision)
        return value.quantize(quantum, rounding=rounding_mode)
    except Exception:
        raise _ReceivablesAmountUnavailable(RECEIVABLES_AMOUNT_CURRENCY_CONTRACT_INVALID_REASON)


def _currency_decimal_string(value: Decimal, currency_contract: dict[str, object]) -> str:
    precision = int(currency_contract.get("precision"))
    rounded = _currency_decimal_value(value, currency_contract)
    return format(rounded, f".{precision}f")


def _coerce_source_date(value: object) -> date | None:
    if isinstance(value, datetime):
        return None
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    text = value
    if not text:
        return None
    if len(text) != 10 or text[4] != "-" or text[7] != "-" or not (text[:4] + text[5:7] + text[8:]).isdigit():
        return None
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.isoformat() == text else None


def _strict_source_date(value: object) -> date:
    coerced = _coerce_source_date(value)
    if not coerced:
        raise _ReceivablesAmountUnavailable(RECEIVABLES_AMOUNT_SOURCE_INVALID_REASON)
    return coerced


def _required_text(value: object) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise _ReceivablesAmountUnavailable(RECEIVABLES_AMOUNT_SOURCE_INVALID_REASON)
    return value


def _strict_checked(value: object) -> bool:
    if type(value) is bool:
        return value
    if type(value) is int and value in (0, 1):
        return bool(value)
    if type(value) is str:
        if value in ("1", "true", "True", "yes", "Yes"):
            return True
        if value in ("0", "false", "False", "no", "No"):
            return False
    raise _ReceivablesAmountUnavailable(RECEIVABLES_AMOUNT_SOURCE_INVALID_REASON)


def _payment_ledger_filters(company_name: str, as_of: date) -> list[list[object]]:
    return [
        ["company", "=", company_name],
        ["account_type", "=", "Receivable"],
        ["party_type", "=", "Customer"],
        ["delinked", "=", 0],
        ["posting_date", "<=", as_of.isoformat()],
    ]


def _payment_ledger_reference_filters(invoice_names: list[str]) -> list[list[object]]:
    return [
        ["against_voucher_no", "in", invoice_names],
        ["voucher_no", "in", invoice_names],
    ]


def _permission_preserving_payment_ledger_rows(
    company_name: str,
    as_of: date,
    invoice_names: list[str],
    list_getter: object = None,
) -> list[dict[str, object]]:
    getter = list_getter or getattr(frappe, "get_list", None)
    if not callable(getter):
        raise _ReceivablesAmountUnavailable("permission_preserving_payment_ledger_reader_unavailable")
    try:
        page_size = int(RECEIVABLES_AMOUNT_SOURCE_PAGE_SIZE)
        max_rows = int(RECEIVABLES_AMOUNT_SOURCE_MAX_ROWS)
    except (TypeError, ValueError):
        raise _ReceivablesAmountUnavailable("payment_ledger_source_limit_invalid")
    if page_size <= 0 or max_rows <= 0:
        raise _ReceivablesAmountUnavailable("payment_ledger_source_limit_invalid")
    if any(not isinstance(name, str) or not name or name != name.strip() for name in invoice_names):
        raise _ReceivablesAmountUnavailable(RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
    if len(invoice_names) > RECEIVABLES_IDENTITY_SOURCE_MAX_ROWS:
        raise _ReceivablesAmountUnavailable(RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)

    fields = list(RECEIVABLES_AMOUNT_SOURCE_FIELDS)

    def read_pages(filters: list[list[object]], or_filters: list[list[object]] | None = None) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        seen_page_row_names: set[str] = set()
        total_seen = 0
        limit_start = 0
        while True:
            remaining_probe = max_rows + 1 - total_seen
            current_page_size = min(page_size, remaining_probe)
            options: dict[str, object] = {
                "filters": filters,
                "fields": fields,
                "order_by": "name asc",
                "limit_start": limit_start,
                "limit_page_length": current_page_size,
            }
            if or_filters is not None:
                options["or_filters"] = or_filters
            records = _permission_preserving_list_call(getter, RECEIVABLES_AMOUNT_SOURCE, **options)
            if not isinstance(records, list):
                raise _ReceivablesAmountUnavailable(RECEIVABLES_AMOUNT_SOURCE_INVALID_REASON)
            page = records
            if not page:
                break
            total_seen += len(page)
            if total_seen > max_rows:
                raise _ReceivablesAmountUnavailable(RECEIVABLES_AMOUNT_SOURCE_TOO_LARGE_REASON)
            for record in page:
                if not isinstance(record, dict):
                    raise _ReceivablesAmountUnavailable(RECEIVABLES_AMOUNT_SOURCE_INVALID_REASON)
                row_name = record.get("name")
                if not isinstance(row_name, str) or not row_name or row_name != row_name.strip():
                    raise _ReceivablesAmountUnavailable(RECEIVABLES_AMOUNT_SOURCE_INVALID_REASON)
                if row_name in seen_page_row_names:
                    raise _ReceivablesAmountUnavailable(RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
                seen_page_row_names.add(row_name)
                rows.append(record)
            if len(page) < current_page_size:
                break
            limit_start += len(page)
        return rows

    primary_rows = read_pages(_payment_ledger_filters(company_name, as_of))
    anomaly_rows = read_pages(
        [],
        _payment_ledger_reference_filters(sorted(set(invoice_names))),
    ) if invoice_names else []

    rows_by_name: dict[str, dict[str, object]] = {}
    for record in primary_rows + anomaly_rows:
        row_name = record.get("name")
        if not isinstance(row_name, str) or not row_name or row_name != row_name.strip():
            raise _ReceivablesAmountUnavailable(RECEIVABLES_AMOUNT_SOURCE_INVALID_REASON)
        existing = rows_by_name.get(row_name)
        if existing is not None and existing != record:
            raise _ReceivablesAmountUnavailable(RECEIVABLES_AMOUNT_SOURCE_INVALID_REASON)
        rows_by_name[row_name] = record
        if len(rows_by_name) > max_rows:
            raise _ReceivablesAmountUnavailable(RECEIVABLES_AMOUNT_SOURCE_TOO_LARGE_REASON)
    return [rows_by_name[name] for name in sorted(rows_by_name)]


def _receivables_identity_filters(company_name: str, as_of: date) -> list[list[object]]:
    return _receivables_base_count_filters(company_name, as_of)


def _permission_preserving_receivables_invoice_identity_sets(
    company_name: str,
    as_of: date,
    list_getter: object = None,
) -> dict[str, frozenset[tuple[str, str, str, str, str]]]:
    """Read only bounded composite invoice identities for internal set reconciliation."""
    getter = list_getter or getattr(frappe, "get_list", None)
    if not callable(getter):
        raise _ReceivablesAmountUnavailable(RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
    try:
        page_size = int(RECEIVABLES_IDENTITY_SOURCE_PAGE_SIZE)
        max_rows = int(RECEIVABLES_IDENTITY_SOURCE_MAX_ROWS)
    except (TypeError, ValueError):
        raise _ReceivablesAmountUnavailable(RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
    if page_size <= 0 or max_rows <= 0:
        raise _ReceivablesAmountUnavailable(RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)

    try:
        return_records = _permission_preserving_list_call(
            getter,
            RECEIVABLES_COUNT_SOURCE,
            filters=[
                ["company", "=", company_name],
                ["docstatus", "=", 1],
                ["is_return", "=", 1],
                ["posting_date", "<=", as_of.isoformat()],
            ],
            fields=[RECEIVABLES_COUNT_QUERY_FIELD],
            limit_page_length=1,
        )
        return_count = _extract_count(return_records, RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
    except Exception:
        raise _ReceivablesAmountUnavailable(RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
    if return_count > 0:
        raise _ReceivablesAmountUnavailable("credit_returns_not_supported")

    bucket_sets: dict[str, set[tuple[str, str, str, str, str]]] = {
        cstr(bucket.get("key")): set() for bucket in RECEIVABLES_COUNT_BUCKETS
    }
    seen_names: set[str] = set()
    total_seen = 0
    limit_start = 0
    expected_fields = set(RECEIVABLES_IDENTITY_SOURCE_FIELDS)
    while True:
        current_page_size = min(page_size, max_rows + 1 - total_seen)
        try:
            records = _permission_preserving_list_call(
                getter,
                RECEIVABLES_COUNT_SOURCE,
                filters=_receivables_identity_filters(company_name, as_of),
                fields=list(RECEIVABLES_IDENTITY_SOURCE_FIELDS),
                order_by="name asc",
                limit_start=limit_start,
                limit_page_length=current_page_size,
            )
        except Exception:
            raise _ReceivablesAmountUnavailable(RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
        if not isinstance(records, list):
            raise _ReceivablesAmountUnavailable(RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
        if not records:
            break
        total_seen += len(records)
        if total_seen > max_rows:
            raise _ReceivablesAmountUnavailable(RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
        for row in records:
            if not isinstance(row, dict) or set(row) != expected_fields:
                raise _ReceivablesAmountUnavailable(RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
            invoice_name = _required_text(row.get("name"))
            if invoice_name in seen_names:
                raise _ReceivablesAmountUnavailable(RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
            seen_names.add(invoice_name)
            if _required_text(row.get("company")) != company_name:
                raise _ReceivablesAmountUnavailable(RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
            if row.get("docstatus") not in (1, "1"):
                raise _ReceivablesAmountUnavailable(RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
            if _strict_checked(row.get("is_return")) or cstr(row.get("return_against") or "").strip():
                raise _ReceivablesAmountUnavailable(RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
            posting_date = _strict_source_date(row.get("posting_date"))
            if row.get("due_date") in (None, ""):
                raise _ReceivablesAmountUnavailable("missing_due_date_policy_not_ready")
            due_date = _strict_source_date(row.get("due_date"))
            if posting_date > as_of:
                raise _ReceivablesAmountUnavailable(RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
            identity = (
                _required_text(row.get("debit_to")),
                RECEIVABLES_COUNT_SOURCE,
                invoice_name,
                "Customer",
                _required_text(row.get("customer")),
            )
            bucket_sets[_voucher_bucket(due_date, as_of)].add(identity)
        if len(records) < current_page_size:
            break
        limit_start += len(records)

    return {key: frozenset(values) for key, values in bucket_sets.items()}


def _payment_ledger_identity_sets(
    vouchers: list[dict[str, object]],
) -> dict[str, frozenset[tuple[str, str, str, str, str]]]:
    bucket_sets: dict[str, set[tuple[str, str, str, str, str]]] = {
        cstr(bucket.get("key")): set() for bucket in RECEIVABLES_COUNT_BUCKETS
    }
    for voucher in vouchers:
        bucket_key = cstr(voucher.get("bucket") or "")
        identity = voucher.get("identity")
        if bucket_key not in bucket_sets or not isinstance(identity, tuple) or len(identity) != 5:
            raise _ReceivablesAmountUnavailable(RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
        if any(not isinstance(part, str) or not part for part in identity):
            raise _ReceivablesAmountUnavailable(RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
        if identity in bucket_sets[bucket_key]:
            raise _ReceivablesAmountUnavailable(RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
        bucket_sets[bucket_key].add(identity)
    return {key: frozenset(values) for key, values in bucket_sets.items()}


def _receivables_voucher_identity_sets_match(
    invoice_sets: dict[str, frozenset[tuple[str, str, str, str, str]]],
    payment_ledger_sets: dict[str, frozenset[tuple[str, str, str, str, str]]],
) -> bool:
    expected_keys = {cstr(bucket.get("key")) for bucket in RECEIVABLES_COUNT_BUCKETS}
    if set(invoice_sets) != expected_keys or set(payment_ledger_sets) != expected_keys:
        return False
    return all(invoice_sets.get(key) == payment_ledger_sets.get(key) for key in expected_keys)


def _voucher_bucket(entry_date: date, as_of: date) -> str:
    if entry_date >= as_of:
        return "current"
    age = (as_of - entry_date).days
    if age <= 30:
        return "overdue_1_30"
    if age <= 60:
        return "overdue_31_60"
    if age <= 90:
        return "overdue_61_90"
    return "overdue_over_90"


def _payment_ledger_voucher_outstandings(
    records: list[dict[str, object]],
    as_of: date,
    company_name: str,
    currency_contract: dict[str, object],
) -> list[dict[str, object]]:
    voucher_basis: dict[tuple[str, str, str, str, str], dict[str, object]] = {}
    outstanding_by_key: dict[tuple[str, str, str, str, str], Decimal] = {}
    outstanding_account_by_key: dict[tuple[str, str, str, str, str], Decimal] = {}
    seen_row_names: set[str] = set()
    seen_activity_identities: dict[tuple[object, ...], date | None] = {}

    for row in records:
        if not isinstance(row, dict):
            raise _ReceivablesAmountUnavailable(RECEIVABLES_AMOUNT_SOURCE_INVALID_REASON)
        row_name = _required_text(row.get("name"))
        if row_name in seen_row_names:
            raise _ReceivablesAmountUnavailable(RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
        seen_row_names.add(row_name)
        row_company = _required_text(row.get("company"))
        if row_company != company_name:
            raise _ReceivablesAmountUnavailable(RECEIVABLES_AMOUNT_SOURCE_INVALID_REASON)
        if _strict_checked(row.get("delinked")):
            continue
        account_type = _required_text(row.get("account_type"))
        party_type = _required_text(row.get("party_type"))
        if account_type != "Receivable" or party_type != "Customer":
            raise _ReceivablesAmountUnavailable(RECEIVABLES_AMOUNT_SOURCE_INVALID_REASON)
        posting_date = _strict_source_date(row.get("posting_date"))
        if posting_date > as_of:
            raise _ReceivablesAmountUnavailable("future_payment_ledger_activity_not_supported")
        account = _required_text(row.get("account"))
        party = _required_text(row.get("party"))
        voucher_type = _required_text(row.get("voucher_type"))
        voucher_no = _required_text(row.get("voucher_no"))
        voucher_detail_value = row.get("voucher_detail_no")
        voucher_detail_no = "" if voucher_detail_value in (None, "") else _required_text(voucher_detail_value)
        against_type = _required_text(row.get("against_voucher_type"))
        against_no = _required_text(row.get("against_voucher_no"))
        _required_text(row.get("account_currency"))
        if against_type != RECEIVABLES_COUNT_SOURCE:
            raise _ReceivablesAmountUnavailable(RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
        if voucher_type not in {RECEIVABLES_COUNT_SOURCE, "Payment Entry", "Journal Entry"}:
            raise _ReceivablesAmountUnavailable(RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
        if voucher_type == RECEIVABLES_COUNT_SOURCE and voucher_no != against_no:
            raise _ReceivablesAmountUnavailable(RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)

        amount = _strict_decimal_amount(row.get("amount"))
        account_amount = _strict_decimal_amount(row.get("amount_in_account_currency"))
        due_date = _coerce_source_date(row.get("due_date"))
        if row.get("due_date") not in (None, "") and not due_date:
            raise _ReceivablesAmountUnavailable(RECEIVABLES_AMOUNT_SOURCE_INVALID_REASON)
        activity_identity = (
            row_company,
            account,
            party_type,
            party,
            voucher_type,
            voucher_no,
            voucher_detail_no,
            against_type,
            against_no,
        )
        if activity_identity in seen_activity_identities:
            if voucher_type == RECEIVABLES_COUNT_SOURCE and seen_activity_identities[activity_identity] != due_date:
                raise _ReceivablesAmountUnavailable("payment_terms_not_supported")
            raise _ReceivablesAmountUnavailable(RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
        seen_activity_identities[activity_identity] = due_date
        voucher_key = (account, voucher_type, voucher_no, party_type, party)
        basis = voucher_basis.setdefault(
            voucher_key,
            {
                "amount": Decimal("0"),
                "party": party,
                "voucher_type": voucher_type,
                "posting_dates": set(),
                "due_dates": set(),
            },
        )
        basis["amount"] = basis.get("amount", Decimal("0")) + amount
        if posting_date:
            basis["posting_dates"].add(posting_date)
        if due_date:
            basis["due_dates"].add(due_date)

        outstanding_key = (account, against_type, against_no, party_type, party)
        outstanding_by_key[outstanding_key] = outstanding_by_key.get(outstanding_key, Decimal("0")) + amount
        outstanding_account_by_key[outstanding_key] = outstanding_account_by_key.get(outstanding_key, Decimal("0")) + account_amount

    vouchers: list[dict[str, object]] = []
    correlations_by_invoice: dict[str, set[tuple[str, str, str]]] = {}
    for key, basis in voucher_basis.items():
        account, voucher_type, voucher_no, party_type, party = key
        if voucher_type == RECEIVABLES_COUNT_SOURCE:
            correlations_by_invoice.setdefault(voucher_no, set()).add((account, party_type, party))
    for key in outstanding_by_key:
        account, against_type, against_no, party_type, party = key
        if against_type == RECEIVABLES_COUNT_SOURCE:
            correlations_by_invoice.setdefault(against_no, set()).add((account, party_type, party))
    if any(len(correlations) > 1 for correlations in correlations_by_invoice.values()):
        raise _ReceivablesAmountUnavailable("split_receivable_account_not_supported")

    invoice_basis_keys = {
        key
        for key, basis in voucher_basis.items()
        if basis.get("voucher_type") == RECEIVABLES_COUNT_SOURCE
    }
    if any(key not in invoice_basis_keys for key in outstanding_by_key):
        raise _ReceivablesAmountUnavailable(
            RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON
        )

    for key, basis in voucher_basis.items():
        _account, voucher_type, _voucher_no, _party_type, party = key
        if voucher_type != "Sales Invoice":
            continue
        outstanding = _currency_decimal_value(
            outstanding_by_key.get(key, Decimal("0")),
            currency_contract,
        )
        outstanding_in_account_currency = _currency_decimal_value(
            outstanding_account_by_key.get(key, Decimal("0")),
            currency_contract,
        )
        company_balance_is_positive = outstanding > 0
        account_balance_is_positive = outstanding_in_account_currency > 0
        if company_balance_is_positive != account_balance_is_positive:
            raise _ReceivablesAmountUnavailable(RECEIVABLES_AMOUNT_SOURCE_INVALID_REASON)
        if not company_balance_is_positive:
            continue
        due_dates = basis.get("due_dates") or set()
        if len(due_dates) > 1:
            raise _ReceivablesAmountUnavailable("payment_terms_not_supported")
        if not due_dates:
            raise _ReceivablesAmountUnavailable("missing_due_date_policy_not_ready")
        entry_date = next(iter(due_dates))
        vouchers.append(
            {
                "bucket": _voucher_bucket(entry_date, as_of),
                "amount": outstanding,
                "party": party,
                "identity": (key[0], RECEIVABLES_COUNT_SOURCE, key[2], "Customer", party),
            }
        )
    return vouchers


def _aggregate_payment_ledger_buckets(
    vouchers: list[dict[str, object]],
    currency_contract: dict[str, object],
) -> dict[str, object]:
    bucket_state: dict[str, dict[str, object]] = {
        cstr(bucket.get("key")): {"count": 0, "amount": Decimal("0"), "parties": set()}
        for bucket in RECEIVABLES_COUNT_BUCKETS
    }
    for voucher in vouchers:
        bucket_key = cstr(voucher.get("bucket") or "")
        if bucket_key not in bucket_state:
            continue
        bucket_state[bucket_key]["count"] += 1
        bucket_state[bucket_key]["amount"] += voucher.get("amount") or Decimal("0")
        party = cstr(voucher.get("party") or "").strip()
        if party:
            bucket_state[bucket_key]["parties"].add(party)

    bucket_counts: dict[str, int] = {}
    bucket_amounts: dict[str, str] = {}
    suppressed_buckets: dict[str, dict[str, object]] = {}
    grand_total = Decimal("0")
    for bucket in RECEIVABLES_COUNT_BUCKETS:
        bucket_key = cstr(bucket.get("key"))
        state = bucket_state[bucket_key]
        count = int(state["count"])
        bucket_counts[bucket_key] = count
        if count == 0:
            bucket_amounts[bucket_key] = _currency_decimal_string(Decimal("0"), currency_contract)
            continue
        if count < RECEIVABLES_AMOUNT_MIN_BUCKET_VOUCHER_COUNT or len(state["parties"]) < RECEIVABLES_AMOUNT_MIN_BUCKET_DIVERSITY_COUNT:
            suppressed_buckets[bucket_key] = {"suppressed": True, "reason": "suppressed_low_population"}
            continue
        amount = state["amount"]
        bucket_amounts[bucket_key] = _currency_decimal_string(amount, currency_contract)
        grand_total += amount

    return {
        "bucket_counts": bucket_counts,
        "bucket_amounts": bucket_amounts,
        "suppressed_buckets": suppressed_buckets,
        "grand_total": None if suppressed_buckets else _currency_decimal_string(grand_total, currency_contract),
    }


def _safe_amount_policy(
    resolver: dict[str, object],
    permission: dict[str, object],
    metadata: dict[str, object],
    currency_contract: dict[str, object],
    reason: str,
    runtime_enabled: bool = False,
) -> dict[str, object]:
    return {
        "source": RECEIVABLES_AMOUNT_SOURCE,
        "reason": reason,
        "resolver_state": resolver.get("state"),
        "resolver_source": resolver.get("source"),
        "role_category": resolver.get("role_category"),
        "source_permission_checked": bool(permission.get("source_permission_checked")),
        "source_permission_verified": bool(permission.get("source_permission_verified")),
        "source_metadata_checked": bool(metadata.get("source_metadata_checked")),
        "source_metadata_verified": bool(metadata.get("source_metadata_verified")),
        "runtime_amount_summary_enabled": runtime_enabled,
        "manager_only": True,
        "company_currency": FINANCE_APPROVED_COMPANY_CURRENCY,
        "currency_precision_verified": bool(currency_contract.get("verified")),
        "currency_precision": currency_contract.get("precision") if currency_contract.get("verified") else None,
        "currency_precision_source": currency_contract.get("precision_source") if currency_contract.get("verified") else None,
        "currency_rounding_method": currency_contract.get("rounding_method") if currency_contract.get("verified") else None,
        "amount_serialization": "fixed_decimal_string" if runtime_enabled and currency_contract.get("verified") else "unavailable",
        "payment_terms_supported": False,
        "payment_terms_detection": "sales_invoice_schedule_gate_and_payment_ledger_due_date_consistency",
        "payment_schedule_rows_read": False,
        "split_payment_terms_fail_closed": True,
        "aging_date_basis": "due_date_only",
        "posting_date_fallback_enabled": False,
        "split_receivable_accounts_supported": False,
        "voucher_set_reconciliation": "account_voucher_type_voucher_party",
        "voucher_set_reconciliation_verified": runtime_enabled,
        "voucher_identities_returned": False,
        "credit_returns_supported": False,
        "minimum_voucher_population": RECEIVABLES_AMOUNT_MIN_BUCKET_VOUCHER_COUNT,
        "minimum_diversity_population": RECEIVABLES_AMOUNT_MIN_BUCKET_DIVERSITY_COUNT,
        "identifiers_enabled": False,
        "native_navigation_enabled": False,
        "external_output_enabled": False,
        "execution_enabled": False,
    }


def _receivables_amount_payload(
    state_value: str,
    reason: str,
    resolver: dict[str, object],
    permission: dict[str, object],
    metadata: dict[str, object],
    currency_contract: dict[str, object],
    as_of: date,
    aggregate: dict[str, object] | None = None,
) -> dict[str, object]:
    runtime_enabled = state_value == "ready"
    selected_company = resolver.get("selected_company") if isinstance(resolver, dict) else None
    aggregate = aggregate or {}
    payload: dict[str, object] = {
        "phase": FINANCE_RECEIVABLES_AMOUNT_PHASE,
        "state": state_value,
        "company_scope": selected_company if runtime_enabled else None,
        "as_of_date": as_of.isoformat(),
        "currency": FINANCE_APPROVED_COMPANY_CURRENCY if runtime_enabled else "",
        "bucket_labels": _bucket_labels(),
        "bucket_counts": aggregate.get("bucket_counts") if runtime_enabled else {},
        "bucket_amounts": aggregate.get("bucket_amounts") if runtime_enabled else {},
        "suppressed_buckets": aggregate.get("suppressed_buckets") if runtime_enabled else {},
        "policy": _safe_amount_policy(resolver, permission, metadata, currency_contract, reason, runtime_enabled=runtime_enabled),
        "no_effect": no_effect_flags(),
        "rows_returned": False,
        "amounts_are_aggregate": runtime_enabled,
        "documents_returned": False,
        "runtime_payment_ledger_amount_summary_enabled": runtime_enabled,
    }
    if runtime_enabled and aggregate.get("grand_total") is not None:
        payload["grand_total"] = aggregate.get("grand_total")
    return payload

def _receivables_count_amount_buckets_match(
    count_payload: dict[str, object],
    amount_payload: dict[str, object],
) -> bool:
    if count_payload.get("state") != "ready" or amount_payload.get("state") != "ready":
        return False
    expected_keys = [cstr(bucket.get("key")) for bucket in RECEIVABLES_COUNT_BUCKETS]
    count_buckets = count_payload.get("bucket_counts")
    amount_buckets = amount_payload.get("bucket_counts")
    if not isinstance(count_buckets, dict) or not isinstance(amount_buckets, dict):
        return False
    if set(count_buckets) != set(expected_keys) or set(amount_buckets) != set(expected_keys):
        return False
    return all(
        isinstance(count_buckets.get(key), int)
        and not isinstance(count_buckets.get(key), bool)
        and isinstance(amount_buckets.get(key), int)
        and not isinstance(amount_buckets.get(key), bool)
        and count_buckets.get(key) == amount_buckets.get(key)
        for key in expected_keys
    )


def _fail_closed_receivables_amount_payload(payload: dict[str, object], reason: str) -> dict[str, object]:
    safe_payload = dict(payload)
    policy = dict(safe_payload.get("policy") if isinstance(safe_payload.get("policy"), dict) else {})
    policy.update({
        "reason": reason,
        "runtime_amount_summary_enabled": False,
        "amount_serialization": "unavailable",
        "voucher_set_reconciliation_verified": False,
    })
    safe_payload.update({
        "state": "unavailable", "company_scope": None, "currency": "", "bucket_counts": {},
        "bucket_amounts": {}, "suppressed_buckets": {}, "policy": policy,
        "amounts_are_aggregate": False, "runtime_payment_ledger_amount_summary_enabled": False,
    })
    safe_payload.pop("grand_total", None)
    return safe_payload


def build_receivables_payment_ledger_amount_summary(
    context: dict[str, object] | None = None,
    requested_company: str | None = None,
    resolver: dict[str, object] | None = None,
    as_of_date: object = None,
    permission_checker: object = None,
    metadata_provider: object = None,
    list_getter: object = None,
    invoice_identity_list_getter: object = None,
    future_activity_list_getter: object = None,
    currency_contract_provider: object = None,
    browser_filters: dict[str, object] | None = None,
    payment_terms_required: bool = False,
) -> dict[str, object]:
    active_context = context or build_context()
    active_resolver = resolver or resolve_finance_role_company_scope(
        context=active_context,
        requested_company=requested_company,
    )
    invalid_as_of = False
    try:
        as_of = _normalize_as_of_date(as_of_date)
    except (TypeError, ValueError):
        as_of = _normalize_as_of_date()
        invalid_as_of = True
    empty_permission = {
        "source": RECEIVABLES_AMOUNT_SOURCE,
        "source_permission_checked": False,
        "source_permission_verified": False,
        "reason": "source_permission_not_checked",
    }
    empty_metadata = {
        "source": RECEIVABLES_AMOUNT_SOURCE,
        "source_metadata_checked": False,
        "source_metadata_verified": False,
        "reason": "source_metadata_not_checked",
    }
    empty_currency_contract: dict[str, object] = {"verified": False}
    if invalid_as_of:
        return _receivables_amount_payload("unavailable", "invalid_as_of_date", active_resolver, empty_permission, empty_metadata, empty_currency_contract, as_of)
    if browser_filters:
        return _receivables_amount_payload("unavailable", "browser_filters_not_allowed", active_resolver, empty_permission, empty_metadata, empty_currency_contract, as_of)
    if active_resolver.get("state") != "scoped":
        return _receivables_amount_payload(
            "unavailable",
            cstr(active_resolver.get("reason") or "resolver_not_scoped"),
            active_resolver,
            empty_permission,
            empty_metadata,
            empty_currency_contract,
            as_of,
        )
    if active_resolver.get("role_category") != "manager":
        return _receivables_amount_payload("unavailable", "accounts_manager_required", active_resolver, empty_permission, empty_metadata, empty_currency_contract, as_of)

    selected_company = active_resolver.get("selected_company") if isinstance(active_resolver, dict) else None
    company_name = cstr((selected_company or {}).get("name") if isinstance(selected_company, dict) else "").strip()
    company_currency = cstr((selected_company or {}).get("currency") if isinstance(selected_company, dict) else "").strip()
    if company_name != FINANCE_APPROVED_COMPANY_NAME or company_currency != FINANCE_APPROVED_COMPANY_CURRENCY:
        return _receivables_amount_payload("unavailable", "approved_company_currency_required", active_resolver, empty_permission, empty_metadata, empty_currency_contract, as_of)
    if payment_terms_required:
        return _receivables_amount_payload("unavailable", "payment_terms_not_supported", active_resolver, empty_permission, empty_metadata, empty_currency_contract, as_of)

    permission = verify_receivables_amount_source_permission(active_context, permission_checker=permission_checker)
    if not permission.get("source_permission_verified"):
        return _receivables_amount_payload("unavailable", "source_permission_denied", active_resolver, permission, empty_metadata, empty_currency_contract, as_of)

    metadata = verify_receivables_amount_source_metadata(metadata_provider=metadata_provider)
    if not metadata.get("source_metadata_verified"):
        return _receivables_amount_payload("unavailable", cstr(metadata.get("reason") or "source_metadata_drift"), active_resolver, permission, metadata, empty_currency_contract, as_of)

    try:
        future_activity_count = _permission_preserving_receivables_future_activity_count(
            company_name,
            as_of,
            list_getter=future_activity_list_getter,
        )
    except _ReceivablesCountUnavailable as exc:
        return _receivables_amount_payload("unavailable", exc.reason, active_resolver, permission, metadata, empty_currency_contract, as_of)
    if future_activity_count > 0:
        return _receivables_amount_payload(
            "unavailable",
            "future_payment_ledger_activity_not_supported",
            active_resolver,
            permission,
            metadata,
            empty_currency_contract,
            as_of,
        )

    try:
        if callable(currency_contract_provider):
            currency_contract = currency_contract_provider(company_currency)
        else:
            currency_contract = _currency_precision_contract(company_currency)
        if not isinstance(currency_contract, dict) or not currency_contract.get("verified"):
            raise _ReceivablesAmountUnavailable(RECEIVABLES_AMOUNT_CURRENCY_CONTRACT_INVALID_REASON)
    except _ReceivablesAmountUnavailable as exc:
        return _receivables_amount_payload("unavailable", exc.reason, active_resolver, permission, metadata, empty_currency_contract, as_of)
    except Exception:
        return _receivables_amount_payload("unavailable", RECEIVABLES_AMOUNT_CURRENCY_CONTRACT_INVALID_REASON, active_resolver, permission, metadata, empty_currency_contract, as_of)

    try:
        invoice_identity_sets = _permission_preserving_receivables_invoice_identity_sets(
            company_name,
            as_of,
            list_getter=invoice_identity_list_getter,
        )
        invoice_names = sorted({
            identity[2]
            for bucket_identities in invoice_identity_sets.values()
            for identity in bucket_identities
        })
        rows = _permission_preserving_payment_ledger_rows(
            company_name,
            as_of,
            invoice_names,
            list_getter=list_getter,
        )
        vouchers = _payment_ledger_voucher_outstandings(
            rows,
            as_of,
            company_name,
            currency_contract,
        )
        payment_ledger_identity_sets = _payment_ledger_identity_sets(vouchers)
        if not _receivables_voucher_identity_sets_match(invoice_identity_sets, payment_ledger_identity_sets):
            raise _ReceivablesAmountUnavailable(RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
        aggregate = _aggregate_payment_ledger_buckets(vouchers, currency_contract)
    except _ReceivablesAmountUnavailable as exc:
        return _receivables_amount_payload("unavailable", exc.reason, active_resolver, permission, metadata, currency_contract, as_of)
    except Exception:
        return _receivables_amount_payload("unavailable", "payment_ledger_amount_summary_unavailable", active_resolver, permission, metadata, currency_contract, as_of)

    return _receivables_amount_payload("ready", "payment_ledger_amount_summary_ready", active_resolver, permission, metadata, currency_contract, as_of, aggregate)


def build_context() -> dict[str, object]:
    roles = sorted(current_user_roles())
    return {
        "user": getattr(frappe.session, "user", None),
        "roles": roles,
        "role_family": "Finance & Accounting",
        "role_variant": _role_variant(roles),
        "has_finance_shell_access": bool(set(roles).intersection(FINANCE_SHELL_ROLES)),
        "has_finance_overview_access": bool(set(roles).intersection(FINANCE_OVERVIEW_ROLES)),
    }


def public_context(context: dict[str, object]) -> dict[str, object]:
    return {
        "role_family": context.get("role_family") or "Finance & Accounting",
        "role_variant": context.get("role_variant") or "restricted",
        "has_finance_shell_access": bool(context.get("has_finance_shell_access")),
        "has_finance_overview_access": bool(context.get("has_finance_overview_access")),
    }


def state(kind: str, title: str, detail: str) -> dict[str, str]:
    return {
        "kind": kind,
        "title": title,
        "detail": detail,
    }


def ready_state() -> dict[str, str]:
    return state(
        "ready",
        "Finance Control Desk is ready",
        "Approved Finance roles can review company-scoped aggregate posture. No row-level financial data is returned, shown, linked, exported, or actionable.",
    )


def overview_ready_state() -> dict[str, str]:
    return state(
        "ready",
        "Read-only accounting overview is ready",
        "Scoped posture shows aggregate data only: no document rows, reports, exports, or execution routes.",
    )


def overview_unavailable_state() -> dict[str, str]:
    return state(
        "unavailable",
        "Company scope is required",
        "Finance posture requires an approved company scope. Personal defaults do not grant financial visibility.",
    )


def restricted_state() -> dict[str, str]:
    return state(
        "restricted",
        "Finance Control Desk is restricted",
        "This shell is limited to approved accounting, audit, or system roles.",
    )


def finance_workspace_public_context() -> dict[str, object]:
    workspace = get_finance_workspace_definition()
    return {
        "workspace_id": workspace.get("workspace_id"),
        "status": workspace.get("status"),
        "title": workspace.get("title"),
        "workspace_family": workspace.get("workspace_family"),
        "mode_label": workspace.get("mode_label"),
        "role_family": workspace.get("role_family"),
        "routes": workspace.get("routes"),
        "methods": workspace.get("methods"),
        "sidebar": workspace.get("sidebar"),
        "search": workspace.get("search"),
    }


def no_effect_flags() -> dict[str, bool]:
    return {
        "erp_document_created": False,
        "erp_document_updated": False,
        "gl_entry_created": False,
        "journal_entry_created": False,
        "payment_entry_created": False,
        "reconciliation_performed": False,
        "tax_filing_performed": False,
        "period_close_performed": False,
        "notification_sent": False,
        "export_generated": False,
        "row_level_financial_data_returned": False,
        "native_route_opened": False,
        "report_run": False,
        "email_sent": False,
        "portal_action_performed": False,
        "supplier_notification_sent": False,
        "supplier_statement_sent": False,
        "supplier_payment_communication_sent": False,
        "payment_request_created": False,
        "payment_order_created": False,
        "payment_run_performed": False,
        "supplier_bank_or_contact_exposed": False,
        "purchase_invoice_lifecycle_performed": False,
        "user_or_role_mutated": False,
    }


def build_sidebar(context: dict[str, object] | None = None) -> dict[str, object]:
    workspace = get_finance_workspace_definition()
    sidebar = workspace.get("sidebar") or {}
    items = list(workspace.get("fallback_items") or [])
    allowed = has_finance_shell_access(context)
    sidebar_state = ready_state() if allowed else restricted_state()
    return {
        "schema_version": WORKSPACE_SIDEBAR_SCHEMA_VERSION,
        "workspace_id": workspace.get("workspace_id"),
        "title": workspace.get("title"),
        "mode_label": workspace.get("mode_label"),
        "scope_label": "Read-only overview" if allowed else "Restricted",
        "active_key": sidebar.get("home_key") or "finance_control_desk_home",
        "home_key": sidebar.get("home_key") or "finance_control_desk_home",
        "items": items,
        "sections": [
            {
                "key": sidebar.get("section_key") or "workspace",
                "label": sidebar.get("section_label") or "Workspace",
                "items": items,
            }
        ],
        "state": sidebar_state,
    }


def _shell_lanes() -> list[dict[str, Any]]:
    return [
        {
            "key": "accounting_overview",
            "title": "Accounting overview",
            "state": "ready",
            "detail": "Scoped posture uses approved aggregate visibility only; rows, reports, exports, and execution remain blocked.",
            "rows": [],
        },
        {
            "key": "receivables",
            "title": "Receivables posture",
            "state": "ready",
            "detail": "Accounts Manager may see aggregate Sales Invoice count buckets and Payment Ledger MMK amount buckets only when every semantic and permission gate passes.",
            "rows": [],
        },
        {
            "key": "payables",
            "title": "Payables posture",
            "state": "unavailable",
            "detail": "Accounts Manager may see aggregate Purchase Invoice count buckets only when schedule, date, company, status, and permission gates pass.",
            "rows": [],
        },
        {
            "key": "security_hardening",
            "title": "Security and owner verification",
            "state": "empty",
            "detail": "Cycle 1 remains read-only and aggregate-only while final source, browser, and owner verification is completed.",
            "rows": [],
        },
    ]


def _base_payload(context: dict[str, object], payload_state: dict[str, str]) -> dict[str, object]:
    allowed = has_finance_shell_access(context)
    return {
        "workspace": finance_workspace_public_context(),
        "context": public_context(context),
        "scope": {
            "scope_mode": "finance_accounting_shell" if allowed else "restricted",
            "default_routing_enabled": False,
            "financial_data_enabled": False,
            "execution_enabled": False,
        },
        "state": payload_state,
        "sidebar": build_sidebar(context),
        "navigation": {"items": list(get_finance_workspace_definition().get("fallback_items") or [])},
        "lanes": _shell_lanes() if allowed else [],
        "rows": [],
        "no_effect": no_effect_flags(),
        "fetched_at": cstr(now_datetime()),
    }


def _company_scope(context: dict[str, object], resolver: dict[str, object] | None = None) -> dict[str, object]:
    if not has_finance_overview_access(context):
        return {
            "state": "restricted",
            "source": "role_gate",
            "company": None,
            "company_label": None,
            "currency": None,
            "title": "Company scope restricted",
            "detail": "Finance overview requires an approved accounting or audit role.",
        }

    active_resolver = resolver or resolve_finance_role_company_scope(context=context)
    resolver_state = cstr(active_resolver.get("state") or "unavailable")
    resolver_source = cstr(active_resolver.get("source") or resolver_state)
    selected_company = active_resolver.get("selected_company") if isinstance(active_resolver, dict) else None
    if resolver_state == "scoped" and isinstance(selected_company, dict) and selected_company.get("name"):
        company_name = cstr(selected_company.get("name"))
        company_label = cstr(selected_company.get("label") or company_name)
        return {
            "state": "scoped",
            "source": resolver_source,
            "company": company_name,
            "company_label": company_label,
            "currency": cstr(selected_company.get("currency") or ""),
            "title": "Company scope active",
            "detail": "Finance posture is limited to the approved company shown here.",
        }
    if resolver_state == "selection_required":
        return {
            "state": "selection_required",
            "source": resolver_source,
            "company": None,
            "company_label": None,
            "currency": None,
            "title": "Company selection required",
            "detail": "Multiple allowed companies require an approved server-side selection before Finance posture loads.",
        }
    if resolver_state == "restricted":
        return {
            "state": "restricted",
            "source": resolver_source,
            "company": None,
            "company_label": None,
            "currency": None,
            "title": "Company scope restricted",
            "detail": "Your Finance role does not provide an approved company scope.",
        }
    return {
        "state": "unavailable",
        "source": resolver_source or "unavailable",
        "company": None,
        "company_label": None,
        "currency": None,
        "title": "Company scope unavailable",
        "detail": "Finance posture is unavailable until an approved company scope is available.",
    }

def _period_scope(company_scope: dict[str, object]) -> dict[str, object]:
    if company_scope.get("state") != "scoped":
        return {
            "state": "unavailable",
            "title": "Period posture unavailable",
            "detail": "Fiscal and period posture waits for an approved company scope.",
        }
    return {
        "state": "unavailable",
        "title": "Fiscal period posture deferred",
        "detail": "Fiscal calendars and close records remain deferred until the owner approves the period policy.",
    }


def _overview_cards(
    company_scope: dict[str, object],
    period_scope: dict[str, object],
    receivables_posture: dict[str, object] | None = None,
    receivables_amount_summary: dict[str, object] | None = None,
    payables_count_posture: dict[str, object] | None = None,
) -> list[dict[str, object]]:
    company_state = "ready" if company_scope.get("state") == "scoped" else "unavailable"
    receivables_ready = bool(receivables_posture and receivables_posture.get("state") == "ready")
    receivables_counts = receivables_posture.get("bucket_counts") if receivables_ready else {}
    receivables_amount_ready = bool(receivables_amount_summary and receivables_amount_summary.get("state") == "ready")
    payables_ready = bool(payables_count_posture and payables_count_posture.get("state") == "ready")
    label_by_key = {item["key"]: item["label"] for item in _bucket_labels()}
    payables_label_by_key = {item["key"]: item["label"] for item in _payables_bucket_labels()}

    def amount_bucket_parts() -> list[str]:
        amount_summary = receivables_amount_summary.get("bucket_amounts") if receivables_amount_ready else {}
        suppressed = receivables_amount_summary.get("suppressed_buckets") if receivables_amount_ready else {}
        parts = []
        for key in ("current", "overdue_1_30", "overdue_31_60", "overdue_61_90", "overdue_over_90"):
            if key in (amount_summary or {}):
                parts.append(f"{label_by_key.get(key, key)}: {amount_summary.get(key, 0)} MMK")
            elif key in (suppressed or {}):
                parts.append(f"{label_by_key.get(key, key)}: suppressed")
        return parts

    no_row_level_exposure = "No row-level customer, invoice, voucher, account, Payment Ledger, route, report, export, or action detail is returned, shown, linked, exported, or actionable."
    receivables_policy = (receivables_posture or {}).get("policy") or {}
    receivables_role_category = cstr(receivables_policy.get("role_category") or "")
    receivables_manager_only_copy = "Manager-only receivables posture. Aggregate receivables counts and amount posture are available only to Accounts Manager in this phase. No customer, invoice, voucher, account, report, export, or action data is shown."
    receivables_unavailable_copy = "Receivables posture is unavailable. Aggregate receivables counts and manager-only amount posture are not shown. No customer, invoice, voucher, account, report, export, or action data is shown."
    receivables_detail = receivables_unavailable_copy
    receivables_value = "No counts"
    receivables_state = "unavailable"
    if receivables_ready:
        receivables_detail = "; ".join(
            f"{label_by_key.get(key, key)}: {receivables_counts.get(key, 0)}"
            for key in ("current", "overdue_1_30", "overdue_31_60", "overdue_61_90", "overdue_over_90")
        )
        if receivables_amount_ready:
            receivables_detail = f"Sales Invoice aggregate count buckets and manager-only Payment Ledger MMK amount buckets. {receivables_detail}. {'; '.join(amount_bucket_parts())}. {no_row_level_exposure}"
            receivables_value = "Aggregate counts + MMK buckets"
        else:
            receivables_detail = f"Sales Invoice aggregate count buckets only. {receivables_detail}. No row-level customer, invoice, amount, route, report, export, or action detail is returned, shown, linked, exported, or actionable."
            receivables_value = "Aggregate counts only"
        receivables_state = "ready"
    elif receivables_posture:
        if receivables_role_category == "normal_finance":
            receivables_detail = receivables_manager_only_copy
        else:
            receivables_detail = receivables_unavailable_copy

    payables_detail = "Payables aggregate count posture is unavailable. No supplier detail, invoice detail, amounts, native reports, exports, or payment actions are returned or shown."
    payables_value = "No counts"
    payables_state = "unavailable"
    if payables_ready:
        payables_counts = payables_count_posture.get("bucket_counts") or {}
        payables_detail = "; ".join(
            f"{payables_label_by_key.get(key, key)}: {payables_counts.get(key, 0)}"
            for key in ("not_due", "overdue_1_30", "overdue_31_60", "overdue_61_90", "overdue_over_90")
        )
        payables_detail = f"Purchase Invoice aggregate count buckets only. Current / not overdue includes invoices due today or later. {payables_detail}. No supplier names, invoice IDs, amounts, currency totals, native reports, exports, or payment actions are returned, shown, linked, exported, or actionable."
        payables_value = "Aggregate counts only"
        payables_state = "ready"
    elif payables_count_posture:
        reason = cstr((payables_count_posture.get('policy') or {}).get('reason') or 'policy gate not ready')
        if reason in {'payment_schedule_not_supported', 'payment_terms_not_supported'}:
            payables_detail = 'Payables counts are unavailable because some supplier invoices use payment schedules that this overview does not interpret. No supplier detail, invoice detail, amounts, native reports, exports, or payment actions are returned or shown. This overview does not approve or initiate payments.'
            payables_value = 'Unavailable'
        elif reason == 'accounts_manager_required':
            payables_detail = 'Manager-only payables posture. AP count posture is available only to Accounts Manager in this phase. No supplier detail, invoice detail, amounts, native reports, exports, or payment actions are returned or shown.'
        else:
            payables_detail = 'Payables aggregate count posture is unavailable until the approved role, company, source, and permission gates pass. No supplier detail, invoice detail, amounts, native reports, exports, or payment actions are returned or shown.'

    return [
        {
            "key": "workspace_readiness",
            "title": "Workspace readiness",
            "state": "ready",
            "detail": "Finance Control Desk is active for read-only overview posture.",
            "value": "Read-only",
            "rows": [],
        },
        {
            "key": "company_scope",
            "title": "Company scope",
            "state": company_state,
            "detail": company_scope.get("detail"),
            "value": company_scope.get("company") or "Not set",
            "rows": [],
        },
        {
            "key": "period_scope",
            "title": "Fiscal period posture",
            "state": period_scope.get("state"),
            "detail": period_scope.get("detail"),
            "value": "Deferred",
            "rows": [],
        },
        {
            "key": "receivables_posture",
            "title": "Receivables posture",
            "state": receivables_state,
            "detail": receivables_detail,
            "value": receivables_value,
            "rows": [],
        },
        {
            "key": "payables_posture",
            "title": "Payables posture",
            "state": payables_state,
            "detail": payables_detail,
            "value": payables_value,
            "rows": [],
        },
        {
            "key": "ledger_posture",
            "title": "Ledger posture",
            "state": "unavailable",
            "detail": "Account balances, ledger rows, statements, and trial-balance figures remain blocked in this read-only posture.",
            "value": "Blocked",
            "rows": [],
        },
    ]


def _overview_lanes(cards: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "key": cstr(card.get("key")),
            "title": cstr(card.get("title")),
            "state": cstr(card.get("state")),
            "detail": cstr(card.get("detail")),
            "value": cstr(card.get("value")),
            "rows": [],
        }
        for card in cards
    ]


def _overview_payload(context: dict[str, object]) -> dict[str, object]:
    allowed = has_finance_overview_access(context)
    as_of = _normalize_as_of_date()
    company_resolver = resolve_finance_role_company_scope(context=context) if allowed else None
    company_scope = _company_scope(context, company_resolver)
    period_scope = _period_scope(company_scope)
    receivables_posture = build_receivables_count_posture(
        context=context,
        resolver=company_resolver,
        as_of_date=as_of,
    ) if allowed else None
    receivables_amount_summary = None
    if allowed and receivables_posture and receivables_posture.get("state") == "ready":
        receivables_amount_summary = build_receivables_payment_ledger_amount_summary(
            context=context,
            resolver=company_resolver,
            as_of_date=as_of,
        )
        if receivables_amount_summary.get("state") == "ready" and not _receivables_count_amount_buckets_match(
            receivables_posture,
            receivables_amount_summary,
        ):
            receivables_amount_summary = _fail_closed_receivables_amount_payload(
                receivables_amount_summary, "receivables_count_amount_bucket_mismatch"
            )
    elif allowed:
        receivables_amount_summary = _receivables_amount_payload(
            "unavailable",
            "receivables_count_semantics_required",
            company_resolver or {},
            {
                "source": RECEIVABLES_AMOUNT_SOURCE,
                "source_permission_checked": False,
                "source_permission_verified": False,
            },
            {
                "source": RECEIVABLES_AMOUNT_SOURCE,
                "source_metadata_checked": False,
                "source_metadata_verified": False,
            },
            {"verified": False},
            as_of,
        )
    payables_count_posture = build_payables_count_posture(
        context=context,
        resolver=company_resolver,
        as_of_date=as_of,
    ) if allowed else None
    cards = _overview_cards(company_scope, period_scope, receivables_posture, receivables_amount_summary, payables_count_posture) if allowed else []
    payload_state = restricted_state()
    if allowed:
        payload_state = overview_ready_state() if company_scope.get("state") == "scoped" else overview_unavailable_state()

    return {
        "schema_version": FINANCE_OVERVIEW_SCHEMA_VERSION,
        "workspace": {
            "workspace_id": "finance",
            "status": "cycle_1_f6_quality_gate_pending",
            "title": "Finance Control Desk",
            "workspace_family": "Finance & Accounting",
            "mode_label": "Read-only aggregate posture",
        },
        "scope": {
            "scope_mode": FINANCE_OVERVIEW_PHASE if allowed else "restricted",
            "phase": FINANCE_OVERVIEW_PHASE,
            "default_routing_enabled": False,
            "accounting_overview_enabled": bool(allowed and company_scope.get("state") == "scoped"),
            "receivables_count_posture_enabled": bool(receivables_posture and receivables_posture.get("state") == "ready"),
            "receivables_amount_summary_enabled": bool(receivables_amount_summary and receivables_amount_summary.get("state") == "ready"),
            "payables_count_posture_enabled": bool(payables_count_posture and payables_count_posture.get("state") == "ready"),
            "company_scope_required": True,
            "financial_data_enabled": False,
            "financial_rows_enabled": False,
            "monetary_values_enabled": bool(receivables_amount_summary and receivables_amount_summary.get("state") == "ready"),
            "execution_enabled": False,
        },
        "state": payload_state,
        "overview": {
            "phase": FINANCE_OVERVIEW_PHASE,
            "title": "Read-only accounting posture",
            "detail": "Company-scoped posture only. Receivables and Payables signals are aggregate-only when their gates pass; row-level data, reports, exports, and execution remain blocked.",
        },
        "receivables_posture": receivables_posture or {},
        "receivables_amount_summary": receivables_amount_summary or {},
        "payables_count_posture": payables_count_posture or {},
        "company_scope": company_scope,
        "period_scope": period_scope,
        "posture_cards": cards,
        "lanes": _overview_lanes(cards) if allowed else [],
        "metrics": [],
        "amounts": [],
        "documents": [],
        "rows": [],
        "no_effect": no_effect_flags(),
        "fetched_at": cstr(now_datetime()),
    }


@frappe.whitelist()
def get_finance_control_desk_shell_context() -> dict[str, object]:
    ensure_authenticated()
    context = build_context()
    payload_state = ready_state() if has_finance_shell_access(context) else restricted_state()
    return _base_payload(context, payload_state)


@frappe.whitelist()
def get_finance_control_desk_overview_context() -> dict[str, object]:
    ensure_authenticated()
    context = build_context()
    return _overview_payload(context)


@frappe.whitelist()
def get_finance_role_company_resolver_context(requested_company: str | None = None) -> dict[str, object]:
    ensure_authenticated()
    context = build_context()
    resolver = resolve_finance_role_company_scope(context=context, requested_company=requested_company)
    return {
        "workspace": finance_workspace_public_context(),
        "context": public_context(context),
        "phase": FINANCE_RESOLVER_PHASE,
        "resolver": resolver,
        "scope": {
            "scope_mode": FINANCE_RESOLVER_PHASE,
            "default_routing_enabled": False,
            "financial_data_enabled": False,
            "financial_rows_enabled": False,
            "monetary_values_enabled": False,
            "execution_enabled": False,
            "source_read_policy_ready": False,
            "ar_runtime_data_enabled": False,
            "amount_visibility_enabled": False,
        },
        "metrics": [],
        "amounts": [],
        "documents": [],
        "rows": [],
        "no_effect": no_effect_flags(),
        "fetched_at": cstr(now_datetime()),
    }


@frappe.whitelist()
def get_finance_control_desk_sidebar_context() -> dict[str, object]:
    ensure_authenticated()
    context = build_context()
    payload_state = ready_state() if has_finance_shell_access(context) else restricted_state()
    return {
        "schema_version": WORKSPACE_SIDEBAR_SCHEMA_VERSION,
        "workspace": finance_workspace_public_context(),
        "context": public_context(context),
        "scope": {
            "scope_mode": "finance_accounting_shell" if has_finance_shell_access(context) else "restricted",
            "default_routing_enabled": False,
            "financial_data_enabled": False,
            "execution_enabled": False,
        },
        "state": payload_state,
        "sidebar": build_sidebar(context),
        "no_effect": no_effect_flags(),
        "fetched_at": cstr(now_datetime()),
    }


@frappe.whitelist()
def search_finance_control_desk_workspace(query: str = "", limit: int = 0) -> dict[str, object]:
    ensure_authenticated()
    context = build_context()
    needle = cstr(query).strip()
    if not has_finance_shell_access(context):
        return {
            "state": "restricted",
            "query": needle,
            "message": "Finance search is restricted.",
            "groups": [],
            "results": [],
            "no_effect": no_effect_flags(),
        }
    return {
        "state": "unavailable",
        "query": needle,
        "message": "Finance search is not active for row-level financial data in this read-only posture.",
        "groups": [],
        "results": [],
        "no_effect": no_effect_flags(),
    }
