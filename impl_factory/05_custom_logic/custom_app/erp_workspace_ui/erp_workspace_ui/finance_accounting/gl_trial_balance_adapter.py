"""Internal permissioned source adapter for the pure GL / Trial Balance core.

The adapter deliberately has no Frappe import and no default runtime.  A later
Finance service integration must provide the Frappe permission, User
Permission, complete-chart, and coherent-snapshot implementation described by
``PermissionedSnapshotRuntime``.  Missing or incomplete authority fails closed.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol

from .gl_trial_balance_core import (
    AccountNode,
    GLTrialBalanceInputError,
    NormalizedGLEntry,
    TrialBalanceContext,
    TrialBalanceResult,
    build_trial_balance,
)


__all__ = [
    "CompleteAccountManifest",
    "CompleteFiscalYearApplicability",
    "EffectivePermissionEvidence",
    "GLTrialBalanceAdapterError",
    "GLTrialBalanceReadRequest",
    "PermissionedSnapshotRuntime",
    "ReadSnapshotEvidence",
    "UserPermissionRule",
    "read_gl_trial_balance",
]


_GENERIC_ERROR = "finance_read_unavailable"
_PRIVILEGED_ROLES = frozenset(
    {"System Manager", "Administrator", "Bypass Finance Scope"}
)
_RELEVANT_PERMISSION_DOCTYPES = frozenset(
    {
        "Company",
        "Account",
        "Cost Center",
        "Project",
        "Finance Book",
        "Accounting Dimension",
    }
)
_ROOT_TYPES = frozenset({"Asset", "Liability", "Equity", "Income", "Expense"})
_PROFIT_AND_LOSS_ROOTS = frozenset({"Income", "Expense"})
_FISCAL_APPLICABILITY_STATES = frozenset(
    {"selected_company", "global", "excluded"}
)

_COMPANY_FIELDS = ("name", "default_currency", "default_finance_book")
_FISCAL_YEAR_FIELDS = ("name", "year_start_date", "year_end_date", "disabled")
_FISCAL_YEAR_COMPANY_FIELDS = ("parent", "company")
_FINANCE_BOOK_FIELDS = ("name", "finance_book_name")
_DIMENSION_FIELDS = ("name", "document_type", "fieldname", "disabled")
_ACCOUNT_FIELDS = (
    "name",
    "company",
    "parent_account",
    "is_group",
    "root_type",
    "lft",
    "rgt",
    "account_currency",
    "disabled",
)
_GL_ENTRY_FIELDS = (
    "name",
    "company",
    "posting_date",
    "account",
    "debit",
    "credit",
    "is_cancelled",
    "is_opening",
    "finance_book",
)
_PERMISSION_REQUIREMENTS = (
    ("Company", "read"),
    ("Fiscal Year", "read"),
    ("Fiscal Year Company", "read"),
    ("Finance Book", "read"),
    ("Accounting Dimension", "read"),
    ("Account", "read"),
    ("Account", "report"),
    ("GL Entry", "read"),
    ("GL Entry", "report"),
)


class GLTrialBalanceAdapterError(RuntimeError):
    """One stable, non-identifying failure for every adapter rejection."""

    code = _GENERIC_ERROR

    def __init__(self) -> None:
        super().__init__(_GENERIC_ERROR)


@dataclass(frozen=True, slots=True)
class GLTrialBalanceReadRequest:
    company: str
    fiscal_year: str
    from_date: date
    to_date: date
    currency_precision: int
    max_accounts: int
    max_gl_entries: int


@dataclass(frozen=True, slots=True)
class UserPermissionRule:
    allow: str
    for_value: str
    applicable_for: str | None
    apply_to_all_doctypes: int
    hide_descendants: int


@dataclass(frozen=True, slots=True)
class ReadSnapshotEvidence:
    token: str
    user: str
    company: str
    primary_connection: bool
    replica_denied: bool
    transaction_isolation: str
    transaction_read_only: bool
    transaction_active: bool
    consistent_snapshot: bool
    reconnect_denied: bool
    same_connection: bool
    stable: bool


@dataclass(frozen=True, slots=True)
class EffectivePermissionEvidence:
    snapshot_token: str
    user: str
    company: str
    roles: tuple[str, ...]
    user_permissions: tuple[UserPermissionRule, ...]
    complete: bool
    permission_equivalent: bool
    unresolved_relevant_hooks: bool
    custom_docperm_drift: bool
    property_setter_drift: bool
    owner_only_drift: bool
    elevated_permlevel_drift: bool
    field_mask_drift: bool
    share_drift: bool
    custom_report_role_drift: bool


@dataclass(frozen=True, slots=True)
class CompleteAccountManifest:
    snapshot_token: str
    company: str
    account_ids: tuple[str, ...]
    root_account_ids: tuple[str, ...]
    complete: bool
    permission_equivalent: bool


@dataclass(frozen=True, slots=True)
class CompleteFiscalYearApplicability:
    snapshot_token: str
    company: str
    fiscal_year_applicability: tuple[tuple[str, str], ...]
    complete: bool
    permission_equivalent: bool


class PermissionedSnapshotRuntime(Protocol):
    """Frappe-owned integration boundary supplied by a later service gate.

    ``get_list`` must preserve Frappe permissions and must never use
    ``get_all``, raw SQL, ``ignore_permissions``, a native report, or a Query
    Report passthrough.  The runtime owns primary-connection and transaction
    setup, reconnect denial, permission-message containment, and cleanup.
    """

    def current_user(self) -> object: ...

    def begin_read_snapshot(self, user: str, company: str) -> object: ...

    def effective_permission_evidence(
        self, snapshot: ReadSnapshotEvidence
    ) -> object: ...

    def has_permission(
        self,
        snapshot: ReadSnapshotEvidence,
        user: str,
        doctype: str,
        permission_type: str,
    ) -> object: ...

    def get_list(
        self,
        snapshot: ReadSnapshotEvidence,
        doctype: str,
        fields: tuple[str, ...],
        filters: tuple[tuple[str, str, object], ...],
        or_filters: tuple[tuple[str, str, object], ...],
        order_by: str,
        limit: int,
    ) -> object: ...

    def complete_account_manifest(
        self,
        snapshot: ReadSnapshotEvidence,
        company: str,
        max_accounts: int,
    ) -> object: ...

    def complete_fiscal_year_applicability(
        self,
        snapshot: ReadSnapshotEvidence,
        company: str,
        max_fiscal_years: int,
    ) -> object: ...

    def final_snapshot_evidence(self, snapshot: ReadSnapshotEvidence) -> object: ...

    def close_read_snapshot(self, snapshot: ReadSnapshotEvidence) -> None: ...


def _fail() -> None:
    raise GLTrialBalanceAdapterError()


def _strict_text(value: object) -> str:
    if type(value) is not str or not value or value != value.strip():
        _fail()
    return value


def _strict_positive_int(value: object) -> int:
    if type(value) is not int or value <= 0:
        _fail()
    return value


def _strict_flag(value: object, allowed: tuple[int, ...]) -> int:
    if type(value) is not int or value not in allowed:
        _fail()
    return value


def _strict_identifier_tuple(value: object, *, allow_empty: bool = False) -> tuple[str, ...]:
    if type(value) is not tuple or (not value and not allow_empty):
        _fail()
    result = tuple(_strict_text(item) for item in value)
    if len(set(result)) != len(result):
        _fail()
    return result


def _validate_request(value: object) -> GLTrialBalanceReadRequest:
    if type(value) is not GLTrialBalanceReadRequest:
        _fail()
    _strict_text(value.company)
    _strict_text(value.fiscal_year)
    if type(value.from_date) is not date or type(value.to_date) is not date:
        _fail()
    if value.from_date > value.to_date:
        _fail()
    if type(value.currency_precision) is not int or value.currency_precision < 0:
        _fail()
    _strict_positive_int(value.max_accounts)
    _strict_positive_int(value.max_gl_entries)
    return value


def _validate_snapshot(
    value: object, *, user: str, company: str
) -> ReadSnapshotEvidence:
    if type(value) is not ReadSnapshotEvidence:
        _fail()
    _strict_text(value.token)
    if value.user != user or value.company != company:
        _fail()
    if (
        type(value.primary_connection) is not bool
        or not value.primary_connection
        or type(value.replica_denied) is not bool
        or not value.replica_denied
        or value.transaction_isolation != "REPEATABLE READ"
        or type(value.transaction_read_only) is not bool
        or not value.transaction_read_only
        or type(value.transaction_active) is not bool
        or not value.transaction_active
        or type(value.consistent_snapshot) is not bool
        or not value.consistent_snapshot
        or type(value.reconnect_denied) is not bool
        or not value.reconnect_denied
        or type(value.same_connection) is not bool
        or not value.same_connection
        or type(value.stable) is not bool
        or not value.stable
    ):
        _fail()
    return value


def _validate_effective_permissions(
    value: object,
    *,
    snapshot: ReadSnapshotEvidence,
    user: str,
    company: str,
) -> None:
    if type(value) is not EffectivePermissionEvidence:
        _fail()
    if (
        value.snapshot_token != snapshot.token
        or value.user != user
        or value.company != company
        or type(value.complete) is not bool
        or not value.complete
        or type(value.permission_equivalent) is not bool
        or not value.permission_equivalent
    ):
        _fail()
    roles = _strict_identifier_tuple(value.roles)
    if "Accounts Manager" not in roles or set(roles) & _PRIVILEGED_ROLES:
        _fail()
    drift_flags = (
        value.unresolved_relevant_hooks,
        value.custom_docperm_drift,
        value.property_setter_drift,
        value.owner_only_drift,
        value.elevated_permlevel_drift,
        value.field_mask_drift,
        value.share_drift,
        value.custom_report_role_drift,
    )
    if any(type(flag) is not bool or flag for flag in drift_flags):
        _fail()
    if type(value.user_permissions) is not tuple:
        _fail()
    company_rules: list[UserPermissionRule] = []
    for rule in value.user_permissions:
        if type(rule) is not UserPermissionRule:
            _fail()
        allow = _strict_text(rule.allow)
        _strict_text(rule.for_value)
        if rule.applicable_for is not None and type(rule.applicable_for) is not str:
            _fail()
        if type(rule.applicable_for) is str and rule.applicable_for != rule.applicable_for.strip():
            _fail()
        _strict_flag(rule.apply_to_all_doctypes, (0, 1))
        _strict_flag(rule.hide_descendants, (0, 1))
        if allow == "Company":
            company_rules.append(rule)
        elif allow in _RELEVANT_PERMISSION_DOCTYPES or rule.applicable_for in {
            "Account",
            "GL Entry",
        }:
            _fail()
    if not company_rules:
        _fail()
    allowed_companies: set[str] = set()
    for company_rule in company_rules:
        permitted_company = _strict_text(company_rule.for_value)
        if (
            permitted_company in allowed_companies
            or company_rule.apply_to_all_doctypes != 1
            or company_rule.applicable_for not in (None, "")
            or company_rule.hide_descendants != 0
        ):
            _fail()
        allowed_companies.add(permitted_company)
    if company not in allowed_companies:
        _fail()


def _validate_permissions(
    runtime: PermissionedSnapshotRuntime,
    snapshot: ReadSnapshotEvidence,
    user: str,
) -> None:
    for doctype, permission_type in _PERMISSION_REQUIREMENTS:
        if runtime.has_permission(
            snapshot, user, doctype, permission_type
        ) is not True:
            _fail()


def _owned_rows(value: object, *, maximum: int) -> tuple[dict[str, object], ...]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        _fail()
    if len(value) > maximum:
        _fail()
    rows: list[dict[str, object]] = []
    for row in value:
        if not isinstance(row, Mapping):
            _fail()
        rows.append(dict(row))
    return tuple(rows)


def _read_rows(
    runtime: PermissionedSnapshotRuntime,
    snapshot: ReadSnapshotEvidence,
    *,
    doctype: str,
    fields: tuple[str, ...],
    filters: tuple[tuple[str, str, object], ...] = (),
    or_filters: tuple[tuple[str, str, object], ...] = (),
    order_by: str,
    maximum: int,
) -> tuple[dict[str, object], ...]:
    value = runtime.get_list(
        snapshot,
        doctype,
        fields,
        filters,
        or_filters,
        order_by,
        maximum + 1,
    )
    return _owned_rows(value, maximum=maximum)


def _require_keys(row: Mapping[str, object], fields: tuple[str, ...]) -> None:
    if frozenset(row) != frozenset(fields):
        _fail()


def _load_company(
    runtime: PermissionedSnapshotRuntime,
    snapshot: ReadSnapshotEvidence,
    request: GLTrialBalanceReadRequest,
) -> tuple[str, str]:
    rows = _read_rows(
        runtime,
        snapshot,
        doctype="Company",
        fields=_COMPANY_FIELDS,
        filters=(("name", "=", request.company),),
        order_by="name asc",
        maximum=request.max_accounts,
    )
    if len(rows) != 1:
        _fail()
    row = rows[0]
    _require_keys(row, _COMPANY_FIELDS)
    if _strict_text(row["name"]) != request.company:
        _fail()
    return _strict_text(row["default_currency"]), _strict_text(
        row["default_finance_book"]
    )


def _load_fiscal_year(
    runtime: PermissionedSnapshotRuntime,
    snapshot: ReadSnapshotEvidence,
    request: GLTrialBalanceReadRequest,
    *,
    applicability: Mapping[str, str],
) -> tuple[date, date]:
    years = _read_rows(
        runtime,
        snapshot,
        doctype="Fiscal Year",
        fields=_FISCAL_YEAR_FIELDS,
        filters=(("disabled", "=", 0),),
        order_by="year_start_date asc, name asc",
        maximum=request.max_accounts,
    )
    if not years:
        _fail()
    parsed: dict[str, tuple[date, date]] = {}
    for row in years:
        _require_keys(row, _FISCAL_YEAR_FIELDS)
        name = _strict_text(row["name"])
        start = row["year_start_date"]
        end = row["year_end_date"]
        if (
            name in parsed
            or type(start) is not date
            or type(end) is not date
            or start > end
            or _strict_flag(row["disabled"], (0, 1)) != 0
        ):
            _fail()
        parsed[name] = (start, end)
    if frozenset(parsed) != frozenset(applicability):
        _fail()
    company_rows = _read_rows(
        runtime,
        snapshot,
        doctype="Fiscal Year Company",
        fields=_FISCAL_YEAR_COMPANY_FIELDS,
        filters=(
            ("parent", "in", tuple(sorted(parsed))),
            ("company", "=", request.company),
        ),
        order_by="parent asc, company asc",
        maximum=request.max_accounts,
    )
    selected_links: set[str] = set()
    for row in company_rows:
        _require_keys(row, _FISCAL_YEAR_COMPANY_FIELDS)
        parent = _strict_text(row["parent"])
        company = _strict_text(row["company"])
        if (
            parent not in parsed
            or company != request.company
            or parent in selected_links
        ):
            _fail()
        selected_links.add(parent)
    for name, state in applicability.items():
        if (state == "selected_company") != (name in selected_links):
            _fail()
    applicable: list[tuple[str, date, date]] = []
    for name, (start, end) in parsed.items():
        if applicability[name] == "excluded":
            continue
        if start <= request.from_date <= request.to_date <= end:
            applicable.append((name, start, end))
    if len(applicable) != 1 or applicable[0][0] != request.fiscal_year:
        _fail()
    return applicable[0][1], applicable[0][2]


def _validate_finance_book(
    runtime: PermissionedSnapshotRuntime,
    snapshot: ReadSnapshotEvidence,
    request: GLTrialBalanceReadRequest,
    default_finance_book: str,
) -> None:
    rows = _read_rows(
        runtime,
        snapshot,
        doctype="Finance Book",
        fields=_FINANCE_BOOK_FIELDS,
        filters=(("name", "=", default_finance_book),),
        order_by="name asc",
        maximum=request.max_accounts,
    )
    if len(rows) != 1:
        _fail()
    row = rows[0]
    _require_keys(row, _FINANCE_BOOK_FIELDS)
    if _strict_text(row["name"]) != default_finance_book:
        _fail()
    _strict_text(row["finance_book_name"])


def _reject_active_dimensions(
    runtime: PermissionedSnapshotRuntime,
    snapshot: ReadSnapshotEvidence,
    request: GLTrialBalanceReadRequest,
) -> None:
    rows = _read_rows(
        runtime,
        snapshot,
        doctype="Accounting Dimension",
        fields=_DIMENSION_FIELDS,
        filters=(("disabled", "=", 0),),
        order_by="name asc",
        maximum=request.max_accounts,
    )
    if rows:
        for row in rows:
            _require_keys(row, _DIMENSION_FIELDS)
        _fail()


def _validate_manifest(
    value: object,
    *,
    snapshot: ReadSnapshotEvidence,
    request: GLTrialBalanceReadRequest,
) -> CompleteAccountManifest:
    if type(value) is not CompleteAccountManifest:
        _fail()
    if (
        value.snapshot_token != snapshot.token
        or value.company != request.company
        or type(value.complete) is not bool
        or not value.complete
        or type(value.permission_equivalent) is not bool
        or not value.permission_equivalent
    ):
        _fail()
    account_ids = _strict_identifier_tuple(value.account_ids)
    root_ids = _strict_identifier_tuple(value.root_account_ids)
    if (
        len(account_ids) > request.max_accounts
        or len(root_ids) > request.max_accounts
        or not set(root_ids).issubset(account_ids)
    ):
        _fail()
    return value


def _validate_fiscal_applicability(
    value: object,
    *,
    snapshot: ReadSnapshotEvidence,
    request: GLTrialBalanceReadRequest,
) -> tuple[CompleteFiscalYearApplicability, dict[str, str]]:
    if type(value) is not CompleteFiscalYearApplicability:
        _fail()
    if (
        value.snapshot_token != snapshot.token
        or value.company != request.company
        or type(value.complete) is not bool
        or not value.complete
        or type(value.permission_equivalent) is not bool
        or not value.permission_equivalent
    ):
        _fail()
    entries = value.fiscal_year_applicability
    if (
        type(entries) is not tuple
        or not entries
        or len(entries) > request.max_accounts
    ):
        _fail()
    applicability_by_year: dict[str, str] = {}
    for item in entries:
        if type(item) is not tuple or len(item) != 2:
            _fail()
        fiscal_year = _strict_text(item[0])
        state = _strict_text(item[1])
        if (
            fiscal_year in applicability_by_year
            or state not in _FISCAL_APPLICABILITY_STATES
        ):
            _fail()
        applicability_by_year[fiscal_year] = state
    return value, applicability_by_year


def _load_accounts(
    runtime: PermissionedSnapshotRuntime,
    snapshot: ReadSnapshotEvidence,
    request: GLTrialBalanceReadRequest,
    *,
    base_currency: str,
    manifest: CompleteAccountManifest,
) -> tuple[tuple[AccountNode, ...], dict[str, AccountNode]]:
    rows = _read_rows(
        runtime,
        snapshot,
        doctype="Account",
        fields=_ACCOUNT_FIELDS,
        filters=(("company", "=", request.company),),
        order_by="lft asc, name asc",
        maximum=request.max_accounts,
    )
    accounts: list[AccountNode] = []
    intervals: dict[str, tuple[int, int]] = {}
    endpoints: set[int] = set()
    for row in rows:
        _require_keys(row, _ACCOUNT_FIELDS)
        name = _strict_text(row["name"])
        company = _strict_text(row["company"])
        parent_value = row["parent_account"]
        parent = None if parent_value is None else _strict_text(parent_value)
        is_group = _strict_flag(row["is_group"], (0, 1))
        root_type = _strict_text(row["root_type"])
        lft = row["lft"]
        rgt = row["rgt"]
        currency = _strict_text(row["account_currency"])
        _strict_flag(row["disabled"], (0, 1))
        if (
            company != request.company
            or currency != base_currency
            or root_type not in _ROOT_TYPES
            or type(lft) is not int
            or type(rgt) is not int
            or lft <= 0
            or rgt <= lft
            or lft in endpoints
            or rgt in endpoints
            or name in intervals
        ):
            _fail()
        endpoints.update((lft, rgt))
        intervals[name] = (lft, rgt)
        accounts.append(
            AccountNode(
                account_id=name,
                company=company,
                parent_account_id=parent,
                is_group=bool(is_group),
                root_type=root_type,
                account_currency=currency,
                sort_order=lft,
            )
        )
    by_id = {account.account_id: account for account in accounts}
    if len(by_id) != len(accounts) or frozenset(by_id) != frozenset(manifest.account_ids):
        _fail()
    for account in accounts:
        parent_id = account.parent_account_id
        if parent_id is None:
            continue
        parent = by_id.get(parent_id)
        if parent is None or parent.root_type != account.root_type:
            _fail()
        parent_lft, parent_rgt = intervals[parent_id]
        child_lft, child_rgt = intervals[account.account_id]
        if not (parent_lft < child_lft < child_rgt < parent_rgt):
            _fail()
    ordered = tuple(sorted(accounts, key=lambda item: (item.sort_order, item.account_id)))
    return ordered, by_id


def _load_entries(
    runtime: PermissionedSnapshotRuntime,
    snapshot: ReadSnapshotEvidence,
    request: GLTrialBalanceReadRequest,
    *,
    base_currency: str,
    default_finance_book: str,
    fiscal_year_start: date,
    accounts_by_id: Mapping[str, AccountNode],
) -> tuple[NormalizedGLEntry, ...]:
    rows = _read_rows(
        runtime,
        snapshot,
        doctype="GL Entry",
        fields=_GL_ENTRY_FIELDS,
        filters=(
            ("company", "=", request.company),
            ("posting_date", "<=", request.to_date),
            ("is_cancelled", "=", 0),
        ),
        or_filters=(
            ("finance_book", "=", default_finance_book),
            ("finance_book", "=", ""),
            ("finance_book", "is", "not set"),
        ),
        order_by="posting_date asc, name asc",
        maximum=request.max_gl_entries,
    )
    entries: list[NormalizedGLEntry] = []
    seen_names: set[str] = set()
    for row in rows:
        _require_keys(row, _GL_ENTRY_FIELDS)
        name = _strict_text(row["name"])
        company = _strict_text(row["company"])
        account_id = _strict_text(row["account"])
        posting_date = row["posting_date"]
        debit = row["debit"]
        credit = row["credit"]
        is_cancelled = row["is_cancelled"]
        is_opening = row["is_opening"]
        finance_book = row["finance_book"]
        if (
            name in seen_names
            or company != request.company
            or type(posting_date) is not date
            or posting_date > request.to_date
            or type(debit) is not Decimal
            or type(credit) is not Decimal
            or _strict_flag(is_cancelled, (0, 1)) != 0
            or is_opening not in ("Yes", "No")
            or finance_book not in (default_finance_book, "", None)
        ):
            _fail()
        seen_names.add(name)
        account = accounts_by_id.get(account_id)
        if account is None or account.is_group:
            _fail()
        if account.root_type in _PROFIT_AND_LOSS_ROOTS:
            if is_opening == "Yes":
                _fail()
            if posting_date < fiscal_year_start:
                continue
        entries.append(
            NormalizedGLEntry(
                entry_id=name,
                company=company,
                account_id=account_id,
                posting_date=posting_date,
                debit=debit,
                credit=credit,
                currency=base_currency,
                finance_book=finance_book,
                is_opening=is_opening == "Yes",
                dimension_values=(),
            )
        )
    return tuple(entries)


def _read_with_snapshot(
    request: GLTrialBalanceReadRequest,
    runtime: PermissionedSnapshotRuntime,
    snapshot: ReadSnapshotEvidence,
    user: str,
) -> TrialBalanceResult:
    effective = runtime.effective_permission_evidence(snapshot)
    _validate_effective_permissions(
        effective, snapshot=snapshot, user=user, company=request.company
    )
    _validate_permissions(runtime, snapshot, user)
    fiscal_manifest, fiscal_applicability = _validate_fiscal_applicability(
        runtime.complete_fiscal_year_applicability(
            snapshot, request.company, request.max_accounts
        ),
        snapshot=snapshot,
        request=request,
    )
    base_currency, default_finance_book = _load_company(runtime, snapshot, request)
    fiscal_year_start, fiscal_year_end = _load_fiscal_year(
        runtime,
        snapshot,
        request,
        applicability=fiscal_applicability,
    )
    _validate_finance_book(
        runtime, snapshot, request, default_finance_book
    )
    _reject_active_dimensions(runtime, snapshot, request)
    manifest = _validate_manifest(
        runtime.complete_account_manifest(
            snapshot, request.company, request.max_accounts
        ),
        snapshot=snapshot,
        request=request,
    )
    accounts, accounts_by_id = _load_accounts(
        runtime,
        snapshot,
        request,
        base_currency=base_currency,
        manifest=manifest,
    )
    entries = _load_entries(
        runtime,
        snapshot,
        request,
        base_currency=base_currency,
        default_finance_book=default_finance_book,
        fiscal_year_start=fiscal_year_start,
        accounts_by_id=accounts_by_id,
    )
    result = build_trial_balance(
        context=TrialBalanceContext(
            company=request.company,
            base_currency=base_currency,
            precision=request.currency_precision,
            fiscal_year_start=fiscal_year_start,
            fiscal_year_end=fiscal_year_end,
            from_date=request.from_date,
            to_date=request.to_date,
            default_finance_book=default_finance_book,
            finance_book_cohort=(default_finance_book, "", None),
            active_dimensions=0,
        ),
        expected_account_ids=manifest.account_ids,
        expected_root_account_ids=manifest.root_account_ids,
        accounts=accounts,
        entries=entries,
    )
    final_manifest = _validate_manifest(
        runtime.complete_account_manifest(
            snapshot, request.company, request.max_accounts
        ),
        snapshot=snapshot,
        request=request,
    )
    final_fiscal_manifest, _ = _validate_fiscal_applicability(
        runtime.complete_fiscal_year_applicability(
            snapshot, request.company, request.max_accounts
        ),
        snapshot=snapshot,
        request=request,
    )
    final_snapshot = _validate_snapshot(
        runtime.final_snapshot_evidence(snapshot),
        user=user,
        company=request.company,
    )
    final_effective = runtime.effective_permission_evidence(snapshot)
    _validate_effective_permissions(
        final_effective,
        snapshot=snapshot,
        user=user,
        company=request.company,
    )
    _validate_permissions(runtime, snapshot, user)
    if (
        final_manifest != manifest
        or final_fiscal_manifest != fiscal_manifest
        or final_snapshot != snapshot
        or final_effective != effective
    ):
        _fail()
    return result


def read_gl_trial_balance(
    *,
    request: GLTrialBalanceReadRequest,
    runtime: PermissionedSnapshotRuntime,
) -> TrialBalanceResult:
    """Return one complete internal result or one generic unavailable error.

    The function has no HTTP, UI, AI, mutation, close/reopen, cancellation,
    audit, persistence, or accounting-execution authority.
    """

    snapshot: ReadSnapshotEvidence | None = None
    result: TrialBalanceResult | None = None
    failed = False
    try:
        validated_request = _validate_request(request)
        user = _strict_text(runtime.current_user())
        if user in {"Guest", "Administrator"}:
            _fail()
        snapshot_candidate = runtime.begin_read_snapshot(
            user, validated_request.company
        )
        if type(snapshot_candidate) is ReadSnapshotEvidence:
            snapshot = snapshot_candidate
        snapshot = _validate_snapshot(
            snapshot_candidate,
            user=user,
            company=validated_request.company,
        )
        result = _read_with_snapshot(validated_request, runtime, snapshot, user)
        closing_snapshot = snapshot
        snapshot = None
        runtime.close_read_snapshot(closing_snapshot)
    except Exception:
        failed = True
        if snapshot is not None:
            closing_snapshot = snapshot
            snapshot = None
            try:
                runtime.close_read_snapshot(closing_snapshot)
            except Exception:
                pass
    if failed or result is None:
        # Raise outside the active exception handler so even ``__context__``
        # cannot expose a source, permission, snapshot, or database exception.
        raise GLTrialBalanceAdapterError()
    return result
