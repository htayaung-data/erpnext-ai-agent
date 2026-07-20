"""Internal-only synthetic proof harness for Finance GL / Trial Balance.

This file is experimental evidence code, not production runtime architecture.  It
has no route, endpoint, report registration, background task, or accounting
execution surface.  It is intentionally inert unless the separately approved
synthetic gate environment is present.  The harness reconstructs aggregate
trial-balance controls from raw GL Entry and a complete Account chart; it never
uses native General Ledger, native Trial Balance, Query Report, Account Closing
Balance, or Process Period Closing Voucher as a candidate source.

The future disposable runner owns site/container creation and teardown.  This
harness owns only deterministic run-namespaced fixture writes and the
harness-produced evidence files declared below.  It does not create or claim
runner JUnit, topology, provenance, review, teardown, or final-manifest evidence.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import resource
import stat
import threading
import time
import tracemalloc
import unittest
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import frappe
from frappe.database.mariadb.database import MariaDBDatabase


CANDIDATE = "gl_reconstructed"
SYNTHETIC_GATE_VALUE = "finance_gl_tb_internal_v1"
RUN_ID_PATTERN = re.compile(r"^[0-9a-f]{12}$")
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9 _-]+$")
MAX_ACTIVE_DIMENSIONS = 0
CANDIDATE_FORBIDDEN_READS = {"acb": 0, "pcv": 0}

ACCOUNTING_IDS = tuple(f"A{index:02d}" for index in range(1, 23))
PERMISSION_IDS = tuple(f"P{index:02d}" for index in range(1, 29))
SNAPSHOT_IDS = tuple(f"S{index:02d}" for index in range(1, 9))
RECONNECT_BOUNDARIES = (
    "context",
    "authority",
    "fiscal",
    "chart",
    "opening",
    "movement",
    "hierarchy",
    "validation",
    "serialization",
)

PUBLIC_SUCCESS_KEYS = (
    "status",
    "source_mode",
    "context",
    "opening",
    "period",
    "closing",
    "gross_balance_exact",
    "presentation_balance_exact",
    "integrity_status",
)
PUBLIC_CONTEXT_KEYS = (
    "company_scope",
    "currency_scope",
    "period_scope",
    "finance_book_scope",
    "dimension_scope",
)
PUBLIC_AMOUNT_KEYS = ("debit", "credit")
PUBLIC_FAILURE = {
    "status": "unavailable",
    "reason": "finance_context_unavailable",
    "correlation_id": "opaque-synthetic-id",
}

FORBIDDEN_PUBLIC_KEYS = frozenset(
    {
        "account",
        "account_name",
        "account_number",
        "parent_account",
        "root_type",
        "party",
        "party_type",
        "customer",
        "supplier",
        "employee",
        "voucher",
        "voucher_no",
        "against_voucher",
        "reference",
        "remarks",
        "title",
        "owner",
        "modified_by",
        "user",
        "roles",
        "permission",
        "email",
        "phone",
        "address",
        "bank",
        "tax",
        "payroll",
        "cost_center",
        "project",
        "dimension",
        "company",
        "currency",
        "finance_book",
        "row",
        "rows",
        "source_record",
        "route",
        "action",
        "report",
        "export",
        "download",
        "print",
        "sql",
        "traceback",
    }
)

HARNESS_EVIDENCE_BASENAMES = frozenset(
    {
        "fixture-manifest.json",
        "accounting-results.jsonl",
        "permission-results.jsonl",
        "snapshot-results.jsonl",
        "workload-results.jsonl",
        "leakage-results.jsonl",
        "expected-actual-diff.jsonl",
        "mutation-sentinel.json",
    }
)

EXTERNAL_EVIDENCE_BASENAMES = frozenset(
    {
        "provenance.json",
        "topology.json",
        "site-apps.json",
        "junit.xml",
        "evidence-manifest.sha256",
        "review-disposition.json",
        "teardown-receipt.json",
    }
)

FIXTURE_RECORD_KEYS = (
    "fixture_id",
    "family",
    "candidate",
    "input_manifest_sha256",
    "authority_vector_sha256",
    "expected_decision",
    "expected_sha256",
    "actual_decision",
    "actual_sha256",
    "accessor_calls",
    "connection_ids_sha256",
    "canary_matches",
    "exact_diff",
    "result",
)

LOG_KEYS = (
    "event_id",
    "fixture_id",
    "result_class",
    "duration_class",
    "correlation_id",
)

REQUIRED_WORKLOAD_KEYS = (
    "request_latency_ms",
    "statement_duration_ms",
    "process_memory_bytes",
    "examined_database_rows",
    "internal_chart_accounts",
    "internal_gl_rows",
    "serialized_utf8_bytes",
    "concurrent_readers",
    "setup_fixture_ms",
    "reconnect_retries",
)

WORKLOAD_SAFETY_KEYS = (
    "candidate_points",
    "accounts",
    "chart_depth",
    "period_days",
    "gl_rows",
    "concurrent_readers",
    "fault_delay_ms",
)

WORKLOAD_POINT_KEYS = (
    "series_code",
    "step",
    "variant_code",
    "accounts",
    "chart_depth",
    "period_days",
    "eligible_gl_rows",
    "poison_gl_rows",
    "concurrent_readers",
    "response_bytes",
    "active_dimensions",
    "cache_state_code",
)

WORKLOAD_SERIES_AXIS_FIELDS = {
    1: "accounts",
    2: "period_days",
    3: "eligible_gl_rows",
    4: "eligible_gl_rows",
    5: "eligible_gl_rows",
}
WORKLOAD_SERIES_CAPS = {
    1: "MAX_ACCOUNTS",
    2: "MAX_PERIOD_DAYS",
    3: "MAX_RESPONSE_BYTES",
    4: "STATEMENT_TIMEOUT_MS",
    5: "REQUEST_TIMEOUT_MS",
}
WORKLOAD_SERIES_TARGET_BUDGETS = {
    1: "internal_chart_accounts",
    3: "serialized_utf8_bytes",
    4: "statement_duration_ms",
    5: "request_latency_ms",
}
WORKLOAD_VARIANT_CODES = frozenset({0, 1, 2})

DERIVED_CAP_NAMES = (
    "MAX_ACCOUNTS",
    "MAX_PERIOD_DAYS",
    "MAX_OUTPUT_ROWS",
    "MAX_RESPONSE_BYTES",
    "STATEMENT_TIMEOUT_MS",
    "REQUEST_TIMEOUT_MS",
    "MAX_RETRIES",
)

REQUIRED_SOURCE_TABLES = {
    "tabCompany": ("name", "default_currency", "default_finance_book"),
    "tabCurrency": ("name", "fraction_units", "smallest_currency_fraction_value"),
    "tabFinance Book": ("name", "finance_book_name"),
    "tabFiscal Year": ("name", "year_start_date", "year_end_date", "disabled"),
    "tabFiscal Year Company": ("parent", "company"),
    "tabAccount": (
        "name",
        "company",
        "parent_account",
        "is_group",
        "root_type",
        "lft",
        "rgt",
        "account_currency",
        "disabled",
    ),
    "tabGL Entry": (
        "name",
        "company",
        "posting_date",
        "account",
        "debit",
        "credit",
        "is_cancelled",
        "is_opening",
        "finance_book",
    ),
    "tabUser": ("name", "enabled", "user_type"),
    "tabHas Role": ("name", "parent", "parenttype", "role"),
    "tabUser Permission": (
        "name",
        "user",
        "allow",
        "for_value",
        "apply_to_all_doctypes",
        "applicable_for",
        "hide_descendants",
    ),
    "tabDocPerm": ("parent", "role", "permlevel", "read", "report", "if_owner", "mask"),
    "tabCustom DocPerm": (
        "name",
        "parent",
        "role",
        "permlevel",
        "read",
        "report",
        "if_owner",
        "mask",
    ),
    "tabDocField": ("parent", "fieldname", "permlevel"),
    "tabCustom Field": ("dt", "fieldname", "permlevel"),
    "tabDocShare": ("name", "user", "share_doctype", "share_name", "read", "everyone"),
    "tabCustom Role": ("name", "report", "ref_doctype"),
    "tabProperty Setter": ("name", "doc_type", "field_name", "property", "value"),
    "tabSingles": ("doctype", "field", "value"),
    "tabAccounting Dimension": ("name", "document_type", "fieldname", "disabled"),
}

FIXTURE_MUTATION_TABLES = frozenset(
    {
        "tabCompany",
        "tabFinance Book",
        "tabFiscal Year",
        "tabFiscal Year Company",
        "tabAccount",
        "tabGL Entry",
        "tabUser",
        "tabHas Role",
        "tabUser Permission",
        "tabCustom DocPerm",
        "tabDocShare",
        "tabCustom Role",
        "tabProperty Setter",
        "tabAccounting Dimension",
        "tabAccount Closing Balance",
        "tabProcess Period Closing Voucher",
    }
)

REQUIRED_ACCOUNT_FIELDS = frozenset(
    {
        "name",
        "company",
        "parent_account",
        "is_group",
        "root_type",
        "lft",
        "rgt",
        "account_currency",
        "disabled",
    }
)
REQUIRED_GL_FIELDS = frozenset(
    {
        "company",
        "posting_date",
        "account",
        "debit",
        "credit",
        "is_cancelled",
        "is_opening",
        "finance_book",
    }
)

CANARY_TEMPLATES = {
    "account_name": "ZXQ_{run}_ACCOUNT_NAME",
    "account_number": "ZXQ_{run}_ACCOUNT_NUMBER",
    "parent_root": "ZXQ_{run}_PARENT_ROOT",
    "party": "ZXQ_{run}_PARTY_CUSTOMER_SUPPLIER_EMPLOYEE",
    "voucher_reference": "ZXQ_{run}_VOUCHER_REFERENCE",
    "free_text": "ZXQ_{run}_REMARKS_TITLE_TEXT",
    "actor_contact": "ZXQ_{run}_OWNER_USER_ROLE_EMAIL_PHONE_ADDRESS",
    "sensitive": "ZXQ_{run}_BANK_TAX_PAYROLL_INTERCOMPANY",
    "dimension": "ZXQ_{run}_COST_CENTER_PROJECT_DIMENSION",
    "poison_scope": "ZXQ_{run}_COMPANY_B_CANCELLED_OUTSIDE_ALTBOOK",
}


class ProofUnavailable(Exception):
    """Fail-closed internal signal.  Its text is never serialized or logged."""


class StatementTimeoutProof(ProofUnavailable):
    """Internal MariaDB ER_STATEMENT_TIMEOUT signal; never serialized or logged."""


def _fail() -> None:
    raise ProofUnavailable


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=False).encode("utf-8")
        + b"\n"
    )


def _canonical_json_inline(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=False).encode("utf-8")


def _strict_iso_date(value: str) -> date:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        _fail()
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        _fail()
    if parsed.isoformat() != value:
        _fail()
    return parsed


def _strict_positive_int(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        _fail()
    return value


def _strict_nonnegative_int(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        _fail()
    return value


def _elapsed_ms_ceil(elapsed_ns: int) -> int:
    if isinstance(elapsed_ns, bool) or not isinstance(elapsed_ns, int) or elapsed_ns < 0:
        _fail()
    return (elapsed_ns + 999_999) // 1_000_000


def _validate_money(value: Decimal, precision: int) -> Decimal:
    if type(value) is not Decimal or not value.is_finite() or value.is_signed():
        _fail()
    normalized = value.normalize()
    if normalized != 0 and normalized.as_tuple().exponent < -precision:
        _fail()
    return value


def _major_to_minor(value: Decimal, precision: int) -> int:
    _validate_money(value, precision)
    shifted = value.scaleb(precision)
    if shifted.as_tuple().exponent < 0:
        _fail()
    return int(shifted)


def _minor_to_major(value: int, precision: int) -> str:
    if isinstance(value, bool) or not isinstance(value, int):
        _fail()
    sign = "-" if value < 0 else ""
    digits = str(abs(value))
    if precision == 0:
        return f"{sign}{digits}"
    padded = digits.rjust(precision + 1, "0")
    return f"{sign}{padded[:-precision]}.{padded[-precision:]}"


def _strict_decimal_from_db(value: Any, precision: int) -> Decimal:
    if not isinstance(value, str) or not re.fullmatch(r"-?\d+(?:\.\d+)?", value):
        _fail()
    parsed = Decimal(value)
    return _validate_money(parsed, precision)


def _ordered(mapping: Mapping[str, Any], keys: Sequence[str]) -> dict[str, Any]:
    if set(mapping) != set(keys):
        _fail()
    return {key: mapping[key] for key in keys}


def _generic_failure() -> dict[str, str]:
    return dict(PUBLIC_FAILURE)


def _normalize_failure_bytes(value: Mapping[str, Any]) -> bytes:
    normalized = dict(value)
    if set(normalized) != set(PUBLIC_FAILURE):
        _fail()
    normalized["correlation_id"] = "opaque-synthetic-id"
    return _canonical_json_inline(_ordered(normalized, tuple(PUBLIC_FAILURE)))


def _walk_keys(value: Any) -> Iterable[str]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _walk_keys(child)


def _assert_public_key_containment(value: Mapping[str, Any]) -> None:
    if tuple(value) != PUBLIC_SUCCESS_KEYS:
        _fail()
    if tuple(value["context"]) != PUBLIC_CONTEXT_KEYS:
        _fail()
    for bucket in ("opening", "period", "closing"):
        if tuple(value[bucket]) != PUBLIC_AMOUNT_KEYS:
            _fail()
    lowered = {key.casefold() for key in _walk_keys(value)}
    if lowered & FORBIDDEN_PUBLIC_KEYS:
        _fail()


@dataclass(frozen=True)
class ProofContext:
    company: str
    currency: str
    precision: int
    from_date: date
    to_date: date
    default_books: tuple[str, ...]
    active_dimensions: int
    dimension_filters: tuple[tuple[str, str], ...] = ()
    account_filter: str | None = None
    selected_finance_book: str | None = None
    consolidation: bool = False


@dataclass(frozen=True)
class FiscalYearSpec:
    key: str
    start: date
    end: date
    companies: tuple[str, ...]
    disabled: int = 0


@dataclass(frozen=True)
class AccountSpec:
    key: str
    company: str
    parent: str | None
    is_group: int
    root_type: str
    lft: int
    rgt: int
    account_currency: str
    disabled: int = 0


@dataclass(frozen=True)
class GLEntrySpec:
    key: str
    company: str
    posting_date: date
    account: str
    debit: Decimal
    credit: Decimal
    is_cancelled: int
    is_opening: str
    finance_book: str | None
    source_class: str = "ordinary_raw_gl"
    dimension_values: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class SixAmounts:
    opening_debit: int = 0
    opening_credit: int = 0
    period_debit: int = 0
    period_credit: int = 0

    @property
    def closing_debit(self) -> int:
        return self.opening_debit + self.period_debit

    @property
    def closing_credit(self) -> int:
        return self.opening_credit + self.period_credit

    @property
    def closing_net(self) -> int:
        return self.closing_debit - self.closing_credit

    def add_opening(self, debit: int, credit: int) -> "SixAmounts":
        return replace(
            self,
            opening_debit=self.opening_debit + debit,
            opening_credit=self.opening_credit + credit,
        )

    def add_period(self, debit: int, credit: int) -> "SixAmounts":
        return replace(
            self,
            period_debit=self.period_debit + debit,
            period_credit=self.period_credit + credit,
        )

    def add(self, other: "SixAmounts") -> "SixAmounts":
        return SixAmounts(
            opening_debit=self.opening_debit + other.opening_debit,
            opening_credit=self.opening_credit + other.opening_credit,
            period_debit=self.period_debit + other.period_debit,
            period_credit=self.period_credit + other.period_credit,
        )


@dataclass(frozen=True)
class ReconstructionResult:
    fiscal_year: FiscalYearSpec
    leaves: Mapping[str, SixAmounts]
    hierarchy: Mapping[str, SixAmounts]
    gross_totals: SixAmounts
    presentation_opening_debit: int
    presentation_opening_credit: int
    presentation_period_debit: int
    presentation_period_credit: int
    presentation_closing_debit: int
    presentation_closing_credit: int
    account_accessor_calls: int
    gl_accessor_calls: int
    acb_accessor_calls: int
    pcv_accessor_calls: int


class AccessLedger:
    def __init__(self) -> None:
        self.account = 0
        self.gl = 0
        self.acb = 0
        self.pcv = 0

    def read_account(self) -> None:
        self.account += 1

    def read_gl(self) -> None:
        self.gl += 1

    def read_acb(self) -> None:
        self.acb += 1
        CANDIDATE_FORBIDDEN_READS["acb"] += 1
        _fail()

    def read_pcv(self) -> None:
        self.pcv += 1
        CANDIDATE_FORBIDDEN_READS["pcv"] += 1
        _fail()


ROOT_TYPES = frozenset({"Asset", "Liability", "Income", "Expense", "Equity"})
BALANCE_SHEET_ROOTS = frozenset({"Asset", "Liability", "Equity"})
PROFIT_AND_LOSS_ROOTS = frozenset({"Income", "Expense"})


def _resolve_context(context: ProofContext, fiscal_years: Sequence[FiscalYearSpec]) -> tuple[FiscalYearSpec, str]:
    if not context.company or not context.currency:
        _fail()
    if isinstance(context.precision, bool) or not isinstance(context.precision, int) or context.precision < 0:
        _fail()
    if context.from_date > context.to_date:
        _fail()
    if context.active_dimensions != MAX_ACTIVE_DIMENSIONS:
        _fail()
    if context.dimension_filters or context.account_filter or context.selected_finance_book or context.consolidation:
        _fail()
    if len(context.default_books) != 1:
        _fail()
    default_book = context.default_books[0]
    if not isinstance(default_book, str) or not default_book or default_book != default_book.strip():
        _fail()

    applicable = [
        item
        for item in fiscal_years
        if item.disabled == 0 and (not item.companies or context.company in item.companies)
    ]
    for item in applicable:
        if item.start > item.end:
            _fail()
    ordered = sorted(applicable, key=lambda item: (item.start, item.end, item.key))
    for left, right in zip(ordered, ordered[1:]):
        if right.start <= left.end:
            _fail()
    containing = [
        item for item in applicable if item.start <= context.from_date and context.to_date <= item.end
    ]
    if len(containing) != 1:
        _fail()
    return containing[0], default_book


def _validate_chart(context: ProofContext, accounts: Sequence[AccountSpec]) -> tuple[dict[str, AccountSpec], dict[str, list[str]]]:
    if not accounts:
        _fail()
    chart: dict[str, AccountSpec] = {}
    endpoints: set[int] = set()
    children: dict[str, list[str]] = defaultdict(list)
    for account in accounts:
        if account.key in chart:
            _fail()
        if account.company != context.company or account.root_type not in ROOT_TYPES:
            _fail()
        if account.is_group not in (0, 1) or account.disabled not in (0, 1):
            _fail()
        if account.account_currency != context.currency:
            _fail()
        if (
            isinstance(account.lft, bool)
            or isinstance(account.rgt, bool)
            or not isinstance(account.lft, int)
            or not isinstance(account.rgt, int)
            or account.lft <= 0
            or account.rgt <= account.lft
            or account.lft in endpoints
            or account.rgt in endpoints
        ):
            _fail()
        endpoints.update((account.lft, account.rgt))
        chart[account.key] = account

    roots: list[str] = []
    for account in accounts:
        if account.parent:
            parent = chart.get(account.parent)
            if parent is None or parent.company != context.company or parent.is_group != 1:
                _fail()
            if not (parent.lft < account.lft < account.rgt < parent.rgt):
                _fail()
            if parent.root_type != account.root_type:
                _fail()
            children[parent.key].append(account.key)
        else:
            roots.append(account.key)
    if not roots:
        _fail()
    for account in accounts:
        has_children = bool(children.get(account.key))
        if account.is_group == 0 and has_children:
            _fail()
        if account.is_group == 1 and not has_children:
            _fail()

    visited: set[str] = set()
    active: set[str] = set()

    def visit(key: str) -> None:
        if key in active:
            _fail()
        if key in visited:
            return
        active.add(key)
        for child in children.get(key, ()):
            visit(child)
        active.remove(key)
        visited.add(key)

    for root in roots:
        visit(root)
    if visited != set(chart):
        _fail()

    ancestors: dict[str, set[str]] = {}
    for key in chart:
        chain: set[str] = set()
        parent_key = chart[key].parent
        while parent_key:
            if parent_key in chain or parent_key not in chart:
                _fail()
            chain.add(parent_key)
            parent_key = chart[parent_key].parent
        ancestors[key] = chain
    keys = list(chart)
    for index, left_key in enumerate(keys):
        left = chart[left_key]
        for right_key in keys[index + 1 :]:
            right = chart[right_key]
            intervals_overlap = not (left.rgt < right.lft or right.rgt < left.lft)
            if not intervals_overlap:
                continue
            if left_key in ancestors[right_key]:
                if not (left.lft < right.lft < right.rgt < left.rgt):
                    _fail()
            elif right_key in ancestors[left_key]:
                if not (right.lft < left.lft < left.rgt < right.rgt):
                    _fail()
            else:
                _fail()
    return chart, children


def _book_is_in_cohort(value: str | None, default_book: str) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        _fail()
    return value == "" or value == default_book


def _assert_book_cohort_equality(opening_keys: Iterable[str], movement_keys: Iterable[str]) -> None:
    if set(opening_keys) != set(movement_keys):
        _fail()


def _trial_balance_totals(values: Iterable[SixAmounts]) -> tuple[int, int, int, int, int, int]:
    """Return net-sided opening/closing and gross period debit/credit.

    ERPNext Trial Balance period columns represent total debits and credits
    posted during the selected period.  Only balance columns are net-sided.
    """

    opening_debit = opening_credit = 0
    period_debit = period_credit = 0
    closing_debit = closing_credit = 0
    for item in values:
        opening_net = item.opening_debit - item.opening_credit
        closing_net = item.closing_net
        if opening_net >= 0:
            opening_debit += opening_net
        else:
            opening_credit += -opening_net
        period_debit += item.period_debit
        period_credit += item.period_credit
        if closing_net >= 0:
            closing_debit += closing_net
        else:
            closing_credit += -closing_net
    return (
        opening_debit,
        opening_credit,
        period_debit,
        period_credit,
        closing_debit,
        closing_credit,
    )


def _finish_reconstruction(
    context: ProofContext,
    fiscal_year: FiscalYearSpec,
    chart: Mapping[str, AccountSpec],
    children: Mapping[str, Sequence[str]],
    leaves: Mapping[str, SixAmounts],
    access: AccessLedger,
) -> ReconstructionResult:
    leaf_values = [leaves[key] for key, account in chart.items() if account.is_group == 0]
    gross = SixAmounts()
    for value in leaf_values:
        gross = gross.add(value)
        if (
            value.opening_debit - value.opening_credit
            + value.period_debit
            - value.period_credit
            != value.closing_net
        ):
            _fail()
    if (
        gross.opening_debit != gross.opening_credit
        or gross.period_debit != gross.period_credit
        or gross.closing_debit != gross.closing_credit
    ):
        _fail()

    hierarchy: dict[str, SixAmounts] = {}

    def rollup(key: str) -> SixAmounts:
        account = chart[key]
        if account.is_group == 0:
            value = leaves[key]
        else:
            value = SixAmounts()
            for child in children.get(key, ()):
                value = value.add(rollup(child))
        hierarchy[key] = value
        return value

    for key, account in chart.items():
        if not account.parent:
            rollup(key)
    if set(hierarchy) != set(chart):
        _fail()

    presentation = _trial_balance_totals(leaf_values)
    if presentation[0] != presentation[1] or presentation[2] != presentation[3] or presentation[4] != presentation[5]:
        _fail()
    return ReconstructionResult(
        fiscal_year=fiscal_year,
        leaves=dict(leaves),
        hierarchy=hierarchy,
        gross_totals=gross,
        presentation_opening_debit=presentation[0],
        presentation_opening_credit=presentation[1],
        presentation_period_debit=presentation[2],
        presentation_period_credit=presentation[3],
        presentation_closing_debit=presentation[4],
        presentation_closing_credit=presentation[5],
        account_accessor_calls=access.account,
        gl_accessor_calls=access.gl,
        acb_accessor_calls=access.acb,
        pcv_accessor_calls=access.pcv,
    )


def reconstruct_raw_gl(
    context: ProofContext,
    fiscal_years: Sequence[FiscalYearSpec],
    accounts: Sequence[AccountSpec],
    rows: Sequence[GLEntrySpec],
    access: AccessLedger | None = None,
) -> ReconstructionResult:
    access = access or AccessLedger()
    fiscal_year, default_book = _resolve_context(context, fiscal_years)
    access.read_account()
    chart, children = _validate_chart(context, accounts)
    leaves: dict[str, SixAmounts] = {
        key: SixAmounts() for key, account in chart.items() if account.is_group == 0
    }
    access.read_gl()
    for row in rows:
        if type(row.posting_date) is not date:
            _fail()
        if row.is_cancelled not in (0, 1) or row.is_opening not in ("Yes", "No"):
            _fail()
        if row.company != context.company:
            continue
        if row.is_cancelled == 1 or row.posting_date > context.to_date:
            continue
        if not _book_is_in_cohort(row.finance_book, default_book):
            continue
        account = chart.get(row.account)
        if account is None or account.company != context.company or account.is_group != 0:
            _fail()
        if row.dimension_values and context.active_dimensions == MAX_ACTIVE_DIMENSIONS:
            _fail()
        debit = _major_to_minor(row.debit, context.precision)
        credit = _major_to_minor(row.credit, context.precision)
        current = leaves[account.key]
        if account.root_type in PROFIT_AND_LOSS_ROOTS and row.is_opening == "Yes":
            _fail()
        if account.root_type in BALANCE_SHEET_ROOTS:
            is_opening = row.posting_date < context.from_date or row.is_opening == "Yes"
        else:
            is_opening = (
                fiscal_year.start <= row.posting_date < context.from_date
                and row.is_opening != "Yes"
            )
        is_movement = (
            context.from_date <= row.posting_date <= context.to_date
            and row.is_opening != "Yes"
        )
        if is_opening:
            current = current.add_opening(debit, credit)
        if is_movement:
            current = current.add_period(debit, credit)
        leaves[account.key] = current
    return _finish_reconstruction(context, fiscal_year, chart, children, leaves, access)


def serialize_public_success(result: ReconstructionResult, context: ProofContext) -> dict[str, Any]:
    if result.acb_accessor_calls != 0 or result.pcv_accessor_calls != 0:
        _fail()
    value = {
        "status": "ready",
        "source_mode": CANDIDATE,
        "context": {
            "company_scope": "single_authorized",
            "currency_scope": "company_base",
            "period_scope": "single_fiscal_year_inclusive",
            "finance_book_scope": "company_default_plus_unbooked",
            "dimension_scope": "none",
        },
        "opening": {
            "debit": _minor_to_major(result.presentation_opening_debit, context.precision),
            "credit": _minor_to_major(result.presentation_opening_credit, context.precision),
        },
        "period": {
            "debit": _minor_to_major(result.presentation_period_debit, context.precision),
            "credit": _minor_to_major(result.presentation_period_credit, context.precision),
        },
        "closing": {
            "debit": _minor_to_major(result.presentation_closing_debit, context.precision),
            "credit": _minor_to_major(result.presentation_closing_credit, context.precision),
        },
        "gross_balance_exact": (
            result.gross_totals.opening_debit == result.gross_totals.opening_credit
            and result.gross_totals.period_debit == result.gross_totals.period_credit
            and result.gross_totals.closing_debit == result.gross_totals.closing_credit
        ),
        "presentation_balance_exact": (
            result.presentation_opening_debit == result.presentation_opening_credit
            and result.presentation_period_debit == result.presentation_period_credit
            and result.presentation_closing_debit == result.presentation_closing_credit
        ),
        "integrity_status": "exact",
    }
    _assert_public_key_containment(value)
    return value


@dataclass(frozen=True)
class UserPermissionSpec:
    allow: str
    for_value: str
    apply_to_all_doctypes: int = 1
    applicable_for: str | None = None
    hide_descendants: int = 0


@dataclass(frozen=True)
class AuthorityVector:
    authenticated: bool
    actor: str
    roles: frozenset[str]
    requested_company: str | None
    company_permissions: tuple[str, ...]
    user_permissions: tuple[UserPermissionSpec, ...]
    account_read: bool = True
    account_report: bool = True
    gl_read: bool = True
    gl_report: bool = True
    required_account_fields: frozenset[str] = REQUIRED_ACCOUNT_FIELDS
    required_gl_fields: frozenset[str] = REQUIRED_GL_FIELDS
    custom_docperm_override: bool = False
    property_setter_override: bool = False
    owner_only: bool = False
    elevated_permlevel: bool = False
    masked_field: bool = False
    relevant_share: bool = False
    irrelevant_share: bool = False
    custom_report_role_drift: bool = False
    native_report_roles: frozenset[str] = frozenset()
    permission_hooks_resolved: bool = True
    active_dimensions: int = MAX_ACTIVE_DIMENSIONS
    dimension_filter: bool = False
    unsupported_context: bool = False
    externally_supplied_caps_valid: bool = True
    snapshot_valid: bool = True
    complete_chart_valid: bool = True
    exact_balance_valid: bool = True
    public_schema_valid: bool = True
    strict_user_permissions: bool = True


@dataclass(frozen=True)
class AuthorityDecision:
    allowed: bool
    public: Mapping[str, str] | None
    accounting_accessor_calls: int


PRIVILEGED_ROLES = frozenset({"System Manager", "Administrator", "Bypass Finance Scope"})
RELEVANT_PERMISSION_DOCTYPES = frozenset(
    {"Company", "Account", "Cost Center", "Project", "Finance Book", "Accounting Dimension"}
)


def authorize_internal(vector: AuthorityVector) -> AuthorityDecision:
    """Evaluate authority without touching accounting data.

    Native report roles and shares never grant the candidate.  The return value
    deliberately contains no internal denial reason because all denials must be
    byte-equivalent after correlation normalization.
    """

    deny = AuthorityDecision(False, _generic_failure(), 0)
    if not vector.authenticated or not vector.actor or vector.actor == "Guest":
        return deny
    if vector.actor == "Administrator" or vector.roles & PRIVILEGED_ROLES:
        return deny
    if "Accounts Manager" not in vector.roles:
        return deny
    if vector.requested_company is None:
        return deny
    if len(vector.company_permissions) != 1:
        return deny
    if vector.company_permissions[0] != vector.requested_company:
        return deny
    if not (vector.account_read and vector.account_report and vector.gl_read and vector.gl_report):
        return deny
    if vector.required_account_fields != REQUIRED_ACCOUNT_FIELDS:
        return deny
    if vector.required_gl_fields != REQUIRED_GL_FIELDS:
        return deny
    if (
        vector.custom_docperm_override
        or vector.property_setter_override
        or vector.owner_only
        or vector.elevated_permlevel
        or vector.masked_field
    ):
        return deny
    if vector.relevant_share or vector.custom_report_role_drift:
        return deny
    if not vector.permission_hooks_resolved:
        return deny

    company_rows = [item for item in vector.user_permissions if item.allow == "Company"]
    if len(company_rows) != 1:
        return deny
    company_row = company_rows[0]
    if (
        company_row.for_value != vector.requested_company
        or company_row.apply_to_all_doctypes != 1
        or company_row.applicable_for not in (None, "")
        or company_row.hide_descendants != 0
    ):
        return deny
    for item in vector.user_permissions:
        if item is company_row:
            continue
        if item.allow in RELEVANT_PERMISSION_DOCTYPES or item.applicable_for in {"Account", "GL Entry"}:
            return deny
    if vector.active_dimensions != MAX_ACTIVE_DIMENSIONS or vector.dimension_filter:
        return deny
    if vector.unsupported_context or not vector.externally_supplied_caps_valid:
        return deny
    if not vector.snapshot_valid:
        return deny
    if not vector.complete_chart_valid or not vector.exact_balance_valid or not vector.public_schema_valid:
        return deny
    return AuthorityDecision(True, None, 0)


class CanaryRegistry:
    def __init__(self, run_id: str) -> None:
        if not RUN_ID_PATTERN.fullmatch(run_id):
            _fail()
        self._by_family = {
            family: template.format(run=run_id) for family, template in CANARY_TEMPLATES.items()
        }
        self._values = tuple(self._by_family.values())
        self.hashes = tuple(sorted(_sha256_bytes(value.encode("utf-8")) for value in self._values))

    def value(self, family: str) -> str:
        if family not in self._by_family:
            _fail()
        return self._by_family[family]

    def scan_bytes(self, payload: bytes) -> int:
        return sum(payload.count(value.encode("utf-8")) for value in self._values)

    def scan_value(self, value: Any) -> int:
        return self.scan_bytes(_canonical_json_inline(value))


class SyntheticLogCapture:
    def __init__(self, canaries: CanaryRegistry) -> None:
        self._canaries = canaries
        self.records: list[dict[str, str]] = []

    def emit(
        self,
        *,
        fixture_id: str,
        result_class: str,
        duration_class: str,
        correlation_id: str = "opaque-synthetic-id",
    ) -> None:
        record = {
            "event_id": "finance_gl_tb_synthetic_proof",
            "fixture_id": fixture_id,
            "result_class": result_class,
            "duration_class": duration_class,
            "correlation_id": correlation_id,
        }
        if tuple(record) != LOG_KEYS or self._canaries.scan_value(record):
            _fail()
        self.records.append(record)


class EvidenceWriter:
    """Canonical writer restricted to harness-owned evidence basenames."""

    def __init__(self, root: Path, canaries: CanaryRegistry) -> None:
        expected = Path("/evidence")
        if root != expected or root.is_symlink() or not root.is_dir():
            _fail()
        self.root = root
        self.canaries = canaries
        self.written: set[str] = set()
        self.finalized = False
        self._dir_fd = os.open(
            str(root), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        )

    def _target(self, basename: str) -> Path:
        if basename not in HARNESS_EVIDENCE_BASENAMES or Path(basename).name != basename:
            _fail()
        return self.root / basename

    def _temporary_basename(self, basename: str) -> str:
        self._target(basename)
        return f".{basename}.partial"

    def _open(self, basename: str, flags: int) -> int:
        if self.finalized:
            _fail()
        temporary = self._temporary_basename(basename)
        descriptor = os.open(
            temporary,
            flags | os.O_NOFOLLOW,
            0o600,
            dir_fd=self._dir_fd,
        )
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            os.close(descriptor)
            _fail()
        return descriptor

    def write_json(self, basename: str, value: Mapping[str, Any]) -> None:
        payload = _canonical_json_bytes(value)
        if self.canaries.scan_bytes(payload):
            _fail()
        descriptor = self._open(
            basename, os.O_WRONLY | os.O_CREAT | os.O_EXCL
        )
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        self.written.add(basename)

    def append_jsonl(self, basename: str, value: Mapping[str, Any]) -> None:
        payload = _canonical_json_bytes(value)
        if self.canaries.scan_bytes(payload):
            _fail()
        flags = os.O_WRONLY | os.O_APPEND
        if basename not in self.written:
            flags |= os.O_CREAT | os.O_EXCL
        descriptor = self._open(
            basename, flags
        )
        with os.fdopen(descriptor, "ab", closefd=True) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        self.written.add(basename)

    def scan_harness_owned(self) -> dict[str, int]:
        result: dict[str, int] = {}
        for basename in sorted(self.written):
            descriptor = self._open(basename, os.O_RDONLY)
            with os.fdopen(descriptor, "rb", closefd=True) as stream:
                result[basename] = self.canaries.scan_bytes(stream.read())
        return result

    def finalize(self) -> None:
        if self.finalized:
            _fail()
        for basename in sorted(self.written):
            target = self._target(basename)
            if target.exists() or target.is_symlink():
                _fail()
            os.replace(
                self._temporary_basename(basename),
                basename,
                src_dir_fd=self._dir_fd,
                dst_dir_fd=self._dir_fd,
            )
        os.fsync(self._dir_fd)
        self.finalized = True

    def close(self) -> None:
        if getattr(self, "_dir_fd", -1) >= 0:
            os.close(self._dir_fd)
            self._dir_fd = -1


def _fixture_record(
    *,
    fixture_id: str,
    family: str,
    input_manifest: Mapping[str, Any],
    authority_vector: Mapping[str, Any] | None,
    expected_decision: str,
    expected: Mapping[str, Any],
    actual_decision: str,
    actual: Mapping[str, Any] | None,
    accessor_calls: int | None,
    connection_ids: Sequence[int] | None,
    canary_matches: int | None,
) -> dict[str, Any]:
    expected_bytes = _canonical_json_inline(expected)
    actual_bytes = _canonical_json_inline(actual) if actual is not None else None
    record = {
        "fixture_id": fixture_id,
        "family": family,
        "candidate": CANDIDATE,
        "input_manifest_sha256": _sha256_bytes(_canonical_json_inline(input_manifest)),
        "authority_vector_sha256": (
            _sha256_bytes(_canonical_json_inline(authority_vector)) if authority_vector is not None else None
        ),
        "expected_decision": expected_decision,
        "expected_sha256": _sha256_bytes(expected_bytes),
        "actual_decision": actual_decision,
        "actual_sha256": _sha256_bytes(actual_bytes) if actual_bytes is not None else None,
        "accessor_calls": accessor_calls,
        "connection_ids_sha256": (
            _sha256_bytes(_canonical_json_inline(list(connection_ids)))
            if connection_ids is not None
            else None
        ),
        "canary_matches": canary_matches,
        "exact_diff": "none" if expected_bytes == actual_bytes else "mismatch",
        "result": (
            "pass" if expected_decision == actual_decision and expected_bytes == actual_bytes else "fail"
        ),
    }
    if tuple(record) != FIXTURE_RECORD_KEYS:
        _fail()
    return record


@dataclass(frozen=True)
class WorkloadPlan:
    budgets: Mapping[str, int]
    candidate_points: tuple[Mapping[str, int], ...]
    safety_envelope: Mapping[str, int]

    @classmethod
    def from_environment(cls) -> "WorkloadPlan":
        raw = os.environ.get("SYNTH_WORKLOAD_PLAN_JSON")
        if not raw:
            _fail()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            _fail()
        if not isinstance(parsed, dict) or set(parsed) != {
            "budgets",
            "candidate_points",
            "safety_envelope",
        }:
            _fail()
        budgets = parsed["budgets"]
        points = parsed["candidate_points"]
        safety = parsed["safety_envelope"]
        if not isinstance(budgets, dict) or set(budgets) != set(REQUIRED_WORKLOAD_KEYS):
            _fail()
        checked_budgets = {key: _strict_positive_int(budgets[key]) for key in REQUIRED_WORKLOAD_KEYS}
        if not isinstance(points, list) or not points:
            _fail()
        checked_points: list[dict[str, int]] = []
        for point in points:
            if not isinstance(point, dict) or set(point) != set(WORKLOAD_POINT_KEYS):
                _fail()
            checked_points.append(
                {key: _strict_nonnegative_int(point[key]) for key in WORKLOAD_POINT_KEYS}
            )
        if not isinstance(safety, dict) or set(safety) != set(WORKLOAD_SAFETY_KEYS):
            _fail()
        checked_safety = {
            key: _strict_positive_int(safety[key]) for key in WORKLOAD_SAFETY_KEYS
        }
        if len(checked_points) > checked_safety["candidate_points"]:
            _fail()
        for point in checked_points:
            if (
                point["accounts"] > checked_safety["accounts"]
                or point["chart_depth"] > checked_safety["chart_depth"]
                or point["period_days"] > checked_safety["period_days"]
                or point["eligible_gl_rows"] + point["poison_gl_rows"]
                > checked_safety["gl_rows"]
                or point["concurrent_readers"]
                > checked_safety["concurrent_readers"]
            ):
                _fail()
        if any(
            point["poison_gl_rows"] < 4 or point["poison_gl_rows"] % 4 != 0
            for point in checked_points
        ):
            _fail()
        grouped: dict[tuple[int, int], list[dict[str, int]]] = defaultdict(list)
        for point in checked_points:
            if (
                point["series_code"] not in WORKLOAD_SERIES_AXIS_FIELDS
                or point["active_dimensions"] != MAX_ACTIVE_DIMENSIONS
            ):
                _fail()
            grouped[(point["series_code"], point["step"])].append(point)
        if {key[0] for key in grouped} != set(WORKLOAD_SERIES_AXIS_FIELDS):
            _fail()
        ignored_variant_fields = {"variant_code", "cache_state_code", "concurrent_readers"}
        for (_series_code, _step), variants in grouped.items():
            if {point["variant_code"] for point in variants} != WORKLOAD_VARIANT_CODES:
                _fail()
            by_variant = {point["variant_code"]: point for point in variants}
            if len(by_variant) != len(variants):
                _fail()
            if (
                by_variant[0]["cache_state_code"] != 0
                or by_variant[0]["concurrent_readers"] != 1
                or by_variant[1]["cache_state_code"] != 1
                or by_variant[1]["concurrent_readers"] != 1
                or by_variant[2]["cache_state_code"] != 1
                or by_variant[2]["concurrent_readers"] <= 1
            ):
                _fail()
            signatures = {
                tuple(
                    (key, point[key])
                    for key in WORKLOAD_POINT_KEYS
                    if key not in ignored_variant_fields
                )
                for point in variants
            }
            if len(signatures) != 1:
                _fail()
        for series_code, axis_field in WORKLOAD_SERIES_AXIS_FIELDS.items():
            steps = sorted(step for series, step in grouped if series == series_code)
            if len(steps) < 3 or steps != list(range(len(steps))):
                _fail()
            representatives = [
                next(
                    point
                    for point in grouped[(series_code, step)]
                    if point["variant_code"] == 0
                )
                for step in steps
            ]
            axis_values = [point[axis_field] for point in representatives]
            if any(left >= right for left, right in zip(axis_values, axis_values[1:])):
                _fail()
            allowed_to_change = {"step", axis_field}
            if axis_field == "eligible_gl_rows":
                allowed_to_change.add("response_bytes")
            for key in WORKLOAD_POINT_KEYS:
                if key in ignored_variant_fields | allowed_to_change | {"series_code"}:
                    continue
                if len({point[key] for point in representatives}) != 1:
                    _fail()
        return cls(
            checked_budgets,
            tuple(checked_points),
            checked_safety,
        )


def _classify_workload_observation(observation: Mapping[str, int], plan: WorkloadPlan) -> str:
    if set(observation) != set(REQUIRED_WORKLOAD_KEYS):
        _fail()
    for key in REQUIRED_WORKLOAD_KEYS:
        value = _strict_nonnegative_int(observation[key])
        if value > plan.budgets[key]:
            return "observed_over_budget"
    return "observed_within_budget"


def _workload_exceeded_keys(
    observation: Mapping[str, int], plan: WorkloadPlan
) -> tuple[str, ...]:
    if set(observation) != set(REQUIRED_WORKLOAD_KEYS):
        _fail()
    return tuple(
        key
        for key in REQUIRED_WORKLOAD_KEYS
        if _strict_nonnegative_int(observation[key]) > plan.budgets[key]
    )


@dataclass(frozen=True)
class SyntheticEnvironment:
    run_id: str
    expected_site: str
    db_name: str
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_root_password: str
    currency: str
    precision: int
    fiscal_start: date
    fiscal_end: date
    from_date: date
    to_date: date
    evidence_root: Path
    expected_harness_sha256: str

    @classmethod
    def load(cls) -> "SyntheticEnvironment":
        run_id = os.environ.get("SYNTH_RUN_ID", "")
        if not RUN_ID_PATTERN.fullmatch(run_id):
            _fail()
        expected_site = os.environ.get("SYNTH_EXPECTED_SITE", "")
        if expected_site != f"test_finance_gl_tb_{run_id}.local" or frappe.local.site != expected_site:
            _fail()
        if frappe.conf.get("db_type") != "mariadb":
            _fail()
        db_host = str(frappe.conf.get("db_host") or "")
        if db_host != "db-primary" or frappe.conf.get("db_socket"):
            _fail()
        for key in (
            "read_from_replica",
            "db_replica_host",
            "replica_host",
            "db_read_only_host",
            "db_failover_host",
            "db_proxy_host",
        ):
            if frappe.conf.get(key):
                _fail()
        db_name = str(frappe.conf.get("db_name") or "")
        db_user = str(frappe.conf.get("db_user") or db_name)
        db_password = str(frappe.conf.get("db_password") or "")
        db_root_password = os.environ.get("SYNTH_DB_ROOT_PASSWORD", "")
        if (
            db_name != f"test_finance_gl_tb_{run_id}"
            or not db_user
            or not db_password
            or not db_root_password
        ):
            _fail()
        db_port = int(frappe.conf.get("db_port") or 3306)
        currency = os.environ.get("SYNTH_CURRENCY_CODE", "")
        precision_raw = os.environ.get("SYNTH_CURRENCY_PRECISION", "")
        if not currency or not re.fullmatch(r"\d+", precision_raw):
            _fail()
        precision = int(precision_raw)
        if precision < 0:
            _fail()
        fiscal_start = _strict_iso_date(os.environ.get("SYNTH_FY_START", ""))
        fiscal_end = _strict_iso_date(os.environ.get("SYNTH_FY_END", ""))
        from_date = _strict_iso_date(os.environ.get("SYNTH_FROM_DATE", ""))
        to_date = _strict_iso_date(os.environ.get("SYNTH_TO_DATE", ""))
        if not (fiscal_start <= from_date <= to_date <= fiscal_end):
            _fail()
        evidence_root = Path(os.environ.get("SYNTH_EVIDENCE_DIR", ""))
        if evidence_root != Path("/evidence"):
            _fail()
        expected_hash = os.environ.get("SYNTH_EXPECTED_HARNESS_SHA256", "")
        source_hash = _sha256_bytes(Path(__file__).read_bytes())
        if not re.fullmatch(r"[0-9a-f]{64}", expected_hash) or source_hash != expected_hash:
            _fail()
        return cls(
            run_id=run_id,
            expected_site=expected_site,
            db_name=db_name,
            db_host=db_host,
            db_port=db_port,
            db_user=db_user,
            db_password=db_password,
            db_root_password=db_root_password,
            currency=currency,
            precision=precision,
            fiscal_start=fiscal_start,
            fiscal_end=fiscal_end,
            from_date=from_date,
            to_date=to_date,
            evidence_root=evidence_root,
            expected_harness_sha256=expected_hash,
        )


class StrictMariaDBConnection:
    """Dedicated pinned-primary connection with adapter reconnect disabled.

    The pinned Frappe MariaDB adapter is used only to construct the connection.
    All statements use its raw parameterized cursor.  Financial DECIMAL values
    are always cast to character data in SQL before exact parsing.
    """

    def __init__(
        self,
        env: SyntheticEnvironment,
        *,
        topology: bool = False,
        statement_timeout_ms: int | None = None,
    ) -> None:
        user = "root" if topology else env.db_user
        password = env.db_root_password if topology else env.db_password
        self.env = env
        self.topology = topology
        self._database = MariaDBDatabase(
            socket=None,
            host=env.db_host,
            user=user,
            password=password,
            port=env.db_port,
            cur_db_name=env.db_name,
        )
        self._connection: Any = None
        self._cursor: Any = None
        self.snapshot_connection_id: int | None = None
        self.connection_ids: list[int] = []
        self.statement_count = 0
        self.statement_duration_ns = 0
        self.max_statement_duration_ns = 0
        self.rows_fetched = 0
        self.statement_timeout_count = 0
        self.closed = False
        try:
            self._database.connect()
            self._connection = self._database._conn
            if not hasattr(self._connection, "auto_reconnect"):
                _fail()
            self._connection.auto_reconnect = False
            if self._connection.auto_reconnect is not False:
                _fail()
            self._cursor = self._connection.cursor()
            if statement_timeout_ms is not None:
                timeout_ms = _strict_positive_int(statement_timeout_ms)
                timeout_seconds = Decimal(timeout_ms) / Decimal(1000)
                self._rows(
                    "SET SESSION max_statement_time = %s",
                    (format(timeout_seconds, "f"),),
                )
        except Exception:
            if self._connection is None:
                self._connection = getattr(self._database, "_conn", None)
            self.close()
            raise ProofUnavailable from None

    def _rows(self, query: str, values: Sequence[Any] = ()) -> list[dict[str, Any]]:
        if self.closed:
            _fail()
        started = time.perf_counter_ns()
        try:
            self._cursor.execute(query, tuple(values))
            self.statement_count += 1
            description = self._cursor.description
            if description is None:
                return []
            columns = [item[0] for item in description]
            rows = [dict(zip(columns, row)) for row in self._cursor.fetchall()]
            self.rows_fetched += len(rows)
            return rows
        except ProofUnavailable:
            raise
        except Exception as exc:
            error_code = (
                exc.args[0]
                if getattr(exc, "args", ())
                and isinstance(exc.args[0], int)
                and not isinstance(exc.args[0], bool)
                else None
            )
            if error_code == 1969:
                self.statement_timeout_count += 1
                raise StatementTimeoutProof from None
            raise ProofUnavailable from None
        finally:
            elapsed_ns = time.perf_counter_ns() - started
            self.statement_duration_ns += elapsed_ns
            self.max_statement_duration_ns = max(
                self.max_statement_duration_ns, elapsed_ns
            )

    def session_rows_read(self) -> int:
        rows = self._rows("SHOW SESSION STATUS LIKE 'Rows_read'")
        if len(rows) != 1:
            _fail()
        value = rows[0].get("Value")
        return _strict_nonnegative_int(int(str(value)))

    def _connection_id(self) -> int:
        rows = self._rows("SELECT CONNECTION_ID() AS connection_id")
        if len(rows) != 1:
            _fail()
        value = rows[0]["connection_id"]
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            _fail()
        return value

    def assert_same_connection(self) -> int:
        current = self._connection_id()
        self.connection_ids.append(current)
        if self.snapshot_connection_id is not None and current != self.snapshot_connection_id:
            _fail()
        return current

    def execute(
        self,
        query: str,
        values: Sequence[Any] = (),
        *,
        verify_connection: bool = True,
    ) -> list[dict[str, Any]]:
        if self.snapshot_connection_id is not None and verify_connection:
            self.assert_same_connection()
        rows = self._rows(query, values)
        if self.snapshot_connection_id is not None and verify_connection:
            self.assert_same_connection()
        return rows

    def begin_read_snapshot(self) -> None:
        if self.topology or self.snapshot_connection_id is not None:
            _fail()
        self._rows("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        self._rows("START TRANSACTION READ ONLY, WITH CONSISTENT SNAPSHOT")
        self.snapshot_connection_id = self._connection_id()
        self.connection_ids.append(self.snapshot_connection_id)
        state = self.execute(
            """
            SELECT DATABASE() AS database_name,
                   @@hostname AS server_hostname,
                   @@port AS server_port,
                   @@server_id AS server_id,
                   @@in_transaction AS in_transaction
            """
        )
        if len(state) != 1:
            _fail()
        row = state[0]
        if (
            row["database_name"] != self.env.db_name
            or not row["server_hostname"]
            or int(row["server_port"]) != self.env.db_port
            or int(row["in_transaction"]) != 1
        ):
            _fail()

    def verify_innodb_transaction(self) -> None:
        self.execute("SELECT name FROM `tabAccount` ORDER BY name LIMIT 1")
        rows = self.execute(
            """
            SELECT TRX_MYSQL_THREAD_ID AS thread_id,
                   TRX_ISOLATION_LEVEL AS isolation_level,
                   TRX_IS_READ_ONLY AS is_read_only
            FROM INFORMATION_SCHEMA.INNODB_TRX
            WHERE TRX_MYSQL_THREAD_ID = CONNECTION_ID()
            """
        )
        if len(rows) != 1:
            _fail()
        row = rows[0]
        if (
            int(row["thread_id"]) != self.snapshot_connection_id
            or str(row["isolation_level"]).replace("-", " ").upper() != "REPEATABLE READ"
            or int(row["is_read_only"]) != 1
        ):
            _fail()

    def commit_fixture(self) -> None:
        if self.topology or self.snapshot_connection_id is not None:
            _fail()
        self._connection.commit()

    def rollback(self) -> None:
        if self.closed:
            return
        try:
            self._connection.rollback()
        except Exception:
            pass
        self.snapshot_connection_id = None

    def close(self) -> None:
        if getattr(self, "closed", False):
            return
        try:
            self._cursor.close()
        except Exception:
            pass
        try:
            self._connection.close()
        except Exception:
            pass
        self.closed = True


FORBIDDEN_IMPORT_ROOTS = frozenset(
    {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "smtplib",
    }
)
FORBIDDEN_FRAPPE_CALLS = frozenset(
    {
        "whitelist",
        "enqueue",
        "sendmail",
        "publish_realtime",
        "get_doc",
        "new_doc",
        "delete_doc",
    }
)
FORBIDDEN_DIRECT_CALLS = frozenset({"eval", "exec", "compile", "__import__"})
NATIVE_REPORT_CALLS = frozenset(
    {
        "execute_report",
        "get_attr",
        "get_cached_doc",
        "get_prepared_report_result",
        "get_report_result",
        "run_report",
    }
)
CANDIDATE_CACHE_CALLS = frozenset({"cache", "get_cached_doc", "get_cached_value"})


@dataclass(frozen=True)
class StaticContainmentAudit:
    source_sha256: str
    forbidden_import_count: int
    forbidden_frappe_call_count: int
    forbidden_direct_call_count: int
    whitelist_decorator_count: int
    unscoped_file_write_call_count: int
    native_report_surface_count: int
    candidate_cache_surface_count: int

    @classmethod
    def inspect(cls, source: Path) -> "StaticContainmentAudit":
        payload = source.read_bytes()
        try:
            tree = ast.parse(payload.decode("utf-8"), filename=source.name)
        except (UnicodeDecodeError, SyntaxError):
            _fail()
        forbidden_imports = 0
        forbidden_frappe_calls = 0
        forbidden_direct_calls = 0
        whitelist_decorators = 0
        native_report_surfaces = 0
        candidate_cache_surfaces = 0
        evidence_write_call_ids: set[int] = set()
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == "EvidenceWriter":
                evidence_write_call_ids.update(
                    id(child) for child in ast.walk(node) if isinstance(child, ast.Call)
                )
        unscoped_file_writes = 0

        def is_file_write_call(call: ast.Call) -> bool:
            if isinstance(call.func, ast.Name):
                return call.func.id == "open"
            if not isinstance(call.func, ast.Attribute):
                return False
            if call.func.attr in {
                "write",
                "writelines",
                "write_bytes",
                "write_text",
                "rename",
                "unlink",
            }:
                return True
            if call.func.attr == "replace":
                receiver = call.func.value
                return not (
                    isinstance(receiver, ast.Call)
                    and isinstance(receiver.func, ast.Name)
                    and receiver.func.id == "str"
                )
            return (
                call.func.attr in {"open", "remove"}
                and isinstance(call.func.value, ast.Name)
                and call.func.value.id == "os"
            )

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                forbidden_imports += sum(
                    alias.name.split(".", 1)[0] in FORBIDDEN_IMPORT_ROOTS
                    for alias in node.names
                )
                native_report_surfaces += sum(
                    ".desk.query_report" in alias.name
                    or ".accounts.report." in alias.name
                    for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom):
                forbidden_imports += int(
                    bool(node.module)
                    and str(node.module).split(".", 1)[0] in FORBIDDEN_IMPORT_ROOTS
                )
                native_report_surfaces += int(
                    bool(node.module)
                    and (
                        ".desk.query_report" in str(node.module)
                        or ".accounts.report." in str(node.module)
                    )
                )
            elif isinstance(node, ast.Call):
                if is_file_write_call(node) and id(node) not in evidence_write_call_ids:
                    unscoped_file_writes += 1
                if isinstance(node.func, ast.Name):
                    forbidden_direct_calls += int(
                        node.func.id in FORBIDDEN_DIRECT_CALLS
                    )
                elif (
                    isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "frappe"
                ):
                    forbidden_frappe_calls += int(
                        node.func.attr in FORBIDDEN_FRAPPE_CALLS
                    )
                if isinstance(node.func, ast.Attribute):
                    native_report_surfaces += int(
                        node.func.attr in NATIVE_REPORT_CALLS
                        or (
                            isinstance(node.func.value, ast.Attribute)
                            and node.func.value.attr == "query_report"
                        )
                    )
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "frappe"
            ):
                candidate_cache_surfaces += int(
                    node.attr in CANDIDATE_CACHE_CALLS
                )
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for decorator in node.decorator_list:
                    if (
                        isinstance(decorator, ast.Attribute)
                        and isinstance(decorator.value, ast.Name)
                        and decorator.value.id == "frappe"
                        and decorator.attr == "whitelist"
                    ):
                        whitelist_decorators += 1
        result = cls(
            source_sha256=_sha256_bytes(payload),
            forbidden_import_count=forbidden_imports,
            forbidden_frappe_call_count=forbidden_frappe_calls,
            forbidden_direct_call_count=forbidden_direct_calls,
            whitelist_decorator_count=whitelist_decorators,
            unscoped_file_write_call_count=unscoped_file_writes,
            native_report_surface_count=native_report_surfaces,
            candidate_cache_surface_count=candidate_cache_surfaces,
        )
        if any(
            (
                result.forbidden_import_count,
                result.forbidden_frappe_call_count,
                result.forbidden_direct_call_count,
                result.whitelist_decorator_count,
                result.unscoped_file_write_call_count,
                result.native_report_surface_count,
                result.candidate_cache_surface_count,
            )
        ):
            _fail()
        return result

    def evidence(self) -> dict[str, Any]:
        return {
            "source_sha256": self.source_sha256,
            "forbidden_import_count": self.forbidden_import_count,
            "forbidden_frappe_call_count": self.forbidden_frappe_call_count,
            "forbidden_direct_call_count": self.forbidden_direct_call_count,
            "whitelist_decorator_count": self.whitelist_decorator_count,
            "unscoped_file_write_call_count": self.unscoped_file_write_call_count,
            "native_report_surface_count": self.native_report_surface_count,
            "candidate_cache_surface_count": self.candidate_cache_surface_count,
        }


class FixtureMutationGate:
    def __init__(self, connection: StrictMariaDBConnection, run_id: str) -> None:
        if connection.topology or not RUN_ID_PATTERN.fullmatch(run_id):
            _fail()
        self.connection = connection
        self.prefix = f"SYNTH_{run_id}_"
        self.operations: dict[str, int] = defaultdict(int)
        self.commits = 0
        self.rollbacks = 0
        self._column_cache: dict[str, frozenset[str]] = {}

    def _columns(self, table: str) -> frozenset[str]:
        if table not in FIXTURE_MUTATION_TABLES or not IDENTIFIER_PATTERN.fullmatch(table):
            _fail()
        if table not in self._column_cache:
            rows = self.connection.execute(
                """
                SELECT COLUMN_NAME AS column_name
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s
                  AND BINARY TABLE_NAME = BINARY %s
                  AND OCTET_LENGTH(TABLE_NAME) = OCTET_LENGTH(%s)
                ORDER BY ORDINAL_POSITION
                """,
                (self.connection.env.db_name, table, table),
                verify_connection=False,
            )
            columns = frozenset(str(row["column_name"]) for row in rows)
            if not columns:
                _fail()
            self._column_cache[table] = columns
        return self._column_cache[table]

    def insert(self, table: str, row: Mapping[str, Any]) -> None:
        columns = self._columns(table)
        if not row or not set(row).issubset(columns):
            _fail()
        name = row.get("name")
        if not isinstance(name, str) or not name.startswith(self.prefix):
            _fail()
        for field in ("parent", "company", "user"):
            value = row.get(field)
            if value not in (None, "") and field != "company":
                fixed_parent = (
                    table == "tabCustom DocPerm"
                    and field == "parent"
                    and value in {"Account", "GL Entry"}
                )
                if (
                    not fixed_parent
                    and (not isinstance(value, str) or not value.startswith(self.prefix))
                ):
                    _fail()
            if field == "company" and value not in (None, ""):
                if not isinstance(value, str) or not value.startswith(self.prefix):
                    _fail()
        ordered_columns = tuple(row)
        if any(not IDENTIFIER_PATTERN.fullmatch(column) for column in ordered_columns):
            _fail()
        identifiers = ", ".join(f"`{column}`" for column in ordered_columns)
        placeholders = ", ".join(["%s"] * len(ordered_columns))
        self.connection.execute(
            f"INSERT INTO `{table}` ({identifiers}) VALUES ({placeholders})",
            tuple(row[column] for column in ordered_columns),
            verify_connection=False,
        )
        self.operations[f"insert:{table}"] += 1

    def update_by_name(self, table: str, name: str, changes: Mapping[str, Any]) -> None:
        columns = self._columns(table)
        if (
            not isinstance(name, str)
            or not name.startswith(self.prefix)
            or not changes
            or "name" in changes
            or not set(changes).issubset(columns)
        ):
            _fail()
        ordered_columns = tuple(changes)
        if any(not IDENTIFIER_PATTERN.fullmatch(column) for column in ordered_columns):
            _fail()
        assignments = ", ".join(f"`{column}` = %s" for column in ordered_columns)
        self.connection.execute(
            f"""
            UPDATE `{table}` SET {assignments}
            WHERE BINARY name = BINARY %s AND OCTET_LENGTH(name) = OCTET_LENGTH(%s)
            """,
            tuple(changes[column] for column in ordered_columns) + (name, name),
            verify_connection=False,
        )
        if self.connection._cursor.rowcount != 1:
            _fail()
        self.operations[f"update:{table}"] += 1

    def insert_minimal(self, table: str, name: str, *, company: str | None = None) -> None:
        columns = self._columns(table)
        row = {key: value for key, value in _base_row(name).items() if key in columns}
        if company is not None and "company" in columns:
            row["company"] = company
        self.insert(table, row)

    def commit(self) -> None:
        self.connection.commit_fixture()
        self.commits += 1

    def rollback(self) -> None:
        self.connection.rollback()
        self.rollbacks += 1

    def sentinel_summary(
        self,
        containment: StaticContainmentAudit,
        forbidden_reads: Mapping[str, int],
    ) -> dict[str, Any]:
        if set(forbidden_reads) != {"acb", "pcv"} or any(
            _strict_nonnegative_int(value) != 0 for value in forbidden_reads.values()
        ):
            _fail()
        table_counts = {
            _sha256_bytes(key.encode("utf-8")): self.operations[key] for key in sorted(self.operations)
        }
        return {
            "candidate": CANDIDATE,
            "namespace_rule": "run_prefixed_rows_only",
            "mutation_classes_sha256_to_count": table_counts,
            "fixture_commits": self.commits,
            "fixture_rollbacks": self.rollbacks,
            "static_containment": containment.evidence(),
            "source_repository_write_surface_count": containment.unscoped_file_write_call_count,
            "native_report_surface_count": containment.native_report_surface_count,
            "candidate_cache_surface_count": containment.candidate_cache_surface_count,
            "acb_candidate_read_calls": forbidden_reads["acb"],
            "pcv_candidate_read_calls": forbidden_reads["pcv"],
            "forbidden_runtime_surface_count": sum(
                (
                    containment.forbidden_import_count,
                    containment.forbidden_frappe_call_count,
                    containment.forbidden_direct_call_count,
                    containment.whitelist_decorator_count,
                    containment.unscoped_file_write_call_count,
                    containment.native_report_surface_count,
                    containment.candidate_cache_surface_count,
                )
            ),
            "host_topology_proof": "external_pending",
            "final_junit_scan": "runner_owned_pending",
            "final_teardown_scan": "environment_owner_pending",
        }


def _base_row(name: str) -> dict[str, Any]:
    stamp = datetime(2000, 1, 1)
    return {
        "name": name,
        "owner": "Administrator",
        "creation": stamp,
        "modified": stamp,
        "modified_by": "Administrator",
        "docstatus": 0,
        "idx": 0,
    }


def _exact_predicate(column: str) -> str:
    if not IDENTIFIER_PATTERN.fullmatch(column):
        _fail()
    return f"BINARY `{column}` = BINARY %s AND OCTET_LENGTH(`{column}`) = OCTET_LENGTH(%s)"


def _sanitize_query_plan(value: Any) -> tuple[Mapping[str, Any], ...]:
    """Retain plan shape without predicates, literals, names, or row contents."""

    records: list[dict[str, Any]] = []

    def walk(node: Any) -> None:
        if isinstance(node, Mapping):
            table = node.get("table")
            if isinstance(table, Mapping):
                table_name = table.get("table_name")
                access_type = table.get("access_type")
                key = table.get("key")
                possible_keys = table.get("possible_keys")
                rows = table.get("rows")
                if (
                    not isinstance(table_name, str)
                    or table_name not in {"account", "gle"}
                    or not isinstance(access_type, str)
                    or key is not None
                    and not isinstance(key, str)
                    or possible_keys is not None
                    and (
                        not isinstance(possible_keys, list)
                        or not all(isinstance(item, str) for item in possible_keys)
                    )
                    or rows is not None
                    and (isinstance(rows, bool) or not isinstance(rows, int) or rows < 0)
                ):
                    _fail()
                records.append(
                    {
                        "table_alias": table_name,
                        "access_type": access_type,
                        "selected_key_sha256": (
                            _sha256_bytes(key.encode("utf-8")) if key is not None else None
                        ),
                        "possible_key_count": len(possible_keys or []),
                        "estimated_rows": rows,
                    }
                )
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(value)
    if not records or {record["table_alias"] for record in records} != {"account", "gle"}:
        _fail()
    return tuple(
        sorted(
            records,
            key=lambda record: (
                str(record["table_alias"]),
                str(record["access_type"]),
                str(record["selected_key_sha256"]),
            ),
        )
    )


@dataclass(frozen=True)
class PermissionHookSnapshot:
    fingerprint: str
    relevant_unresolved: bool


FROZEN_PERMISSION_HOOK_SNAPSHOT: PermissionHookSnapshot | None = None


def _capture_permission_hook_snapshot() -> PermissionHookSnapshot:
    """Capture relevant hooks on the main Frappe context before worker threads."""

    payload: dict[str, dict[str, list[str]]] = {}
    relevant_unresolved = False
    for hook_name in ("permission_query_conditions", "has_permission"):
        hook_map = frappe.get_hooks(hook_name) or {}
        if not isinstance(hook_map, Mapping):
            _fail()
        relevant: dict[str, list[str]] = {}
        for doctype in ("*", "Account", "GL Entry"):
            if doctype not in hook_map:
                continue
            relevant_unresolved = True
            raw = hook_map[doctype]
            if isinstance(raw, str):
                values = [raw]
            elif isinstance(raw, (list, tuple)) and all(
                isinstance(item, str) for item in raw
            ):
                values = list(raw)
            elif raw in (None, False):
                values = []
            else:
                _fail()
            relevant[doctype] = sorted(values)
        payload[hook_name] = relevant
    return PermissionHookSnapshot(
        fingerprint=_sha256_bytes(_canonical_json_inline(payload)),
        relevant_unresolved=relevant_unresolved,
    )


def _frozen_permission_hook_snapshot() -> PermissionHookSnapshot:
    snapshot = FROZEN_PERMISSION_HOOK_SNAPSHOT
    if snapshot is None:
        _fail()
    return snapshot


class DatabaseProofReader:
    def __init__(
        self,
        env: SyntheticEnvironment,
        *,
        company: str,
        actor: str,
        boundary_hook: Callable[[str, int], None] | None = None,
        request_from_date: date | None = None,
        request_to_date: date | None = None,
        candidate_limits: Mapping[str, int] | None = None,
        capture_query_plan: bool = False,
        statement_delay_ms: int | None = None,
    ) -> None:
        self.env = env
        self.company = company
        self.actor = actor
        self.boundary_hook = boundary_hook
        self.request_from_date = request_from_date or env.from_date
        self.request_to_date = request_to_date or env.to_date
        if type(self.request_from_date) is not date or type(self.request_to_date) is not date:
            _fail()
        if candidate_limits is not None and set(candidate_limits) != set(DERIVED_CAP_NAMES):
            _fail()
        self.candidate_limits = (
            {key: _strict_nonnegative_int(candidate_limits[key]) for key in DERIVED_CAP_NAMES}
            if candidate_limits is not None
            else None
        )
        self.capture_query_plan = capture_query_plan
        self.statement_delay_ms = (
            _strict_positive_int(statement_delay_ms)
            if statement_delay_ms is not None
            else None
        )
        self.permission_hook_snapshot = _frozen_permission_hook_snapshot()
        self.connection: StrictMariaDBConnection | None = None
        self.access = AccessLedger()
        self.serialized_bytes: bytes | None = None
        self.candidate_serialized_size: int | None = None
        self.query_plan_sha256: str | None = None
        self.query_plan_estimated_rows: int | None = None
        self.query_plan_structure: tuple[Mapping[str, Any], ...] | None = None
        self.source_scope_rows = 0
        self.metrics: dict[str, int] = {}
        self._request_started_ns: int | None = None
        self.connection_attempts = 0
        self.connection_hosts_attempted: list[str] = []

    def _assert_request_deadline(self) -> None:
        if self.candidate_limits is None or self._request_started_ns is None:
            return
        elapsed_ns = time.perf_counter_ns() - self._request_started_ns
        if elapsed_ns > self.candidate_limits["REQUEST_TIMEOUT_MS"] * 1_000_000:
            _fail()

    def _boundary(self, name: str) -> None:
        if self.connection is None:
            _fail()
        self._assert_request_deadline()
        connection_id = self.connection.assert_same_connection()
        if self.boundary_hook is not None:
            self.boundary_hook(name, connection_id)
        self._assert_request_deadline()
        self.connection.assert_same_connection()

    def _load_context(self) -> ProofContext:
        assert self.connection is not None
        rows = self.connection.execute(
            f"""
            SELECT default_currency, default_finance_book
            FROM `tabCompany`
            WHERE {_exact_predicate('name')}
            """,
            (self.company, self.company),
        )
        if len(rows) != 1:
            _fail()
        currency = rows[0]["default_currency"]
        default_book = rows[0]["default_finance_book"]
        if currency != self.env.currency or not isinstance(default_book, str):
            _fail()
        currency_rows = self.connection.execute(
            f"""
            SELECT fraction_units,
                   CAST(smallest_currency_fraction_value AS CHAR) AS smallest_fraction
            FROM `tabCurrency`
            WHERE {_exact_predicate('name')}
            """,
            (currency, currency),
        )
        if len(currency_rows) != 1:
            _fail()
        expected_fraction_units = 10 ** self.env.precision
        expected_smallest = Decimal(1).scaleb(-self.env.precision)
        if (
            int(currency_rows[0]["fraction_units"]) != expected_fraction_units
            or _strict_decimal_from_db(currency_rows[0]["smallest_fraction"], self.env.precision)
            != expected_smallest
        ):
            _fail()
        book_rows = self.connection.execute(
            f"SELECT name FROM `tabFinance Book` WHERE {_exact_predicate('name')}",
            (default_book, default_book),
        )
        if len(book_rows) != 1 or book_rows[0]["name"] != default_book:
            _fail()
        return ProofContext(
            company=self.company,
            currency=currency,
            precision=self.env.precision,
            from_date=self.request_from_date,
            to_date=self.request_to_date,
            default_books=(default_book,),
            active_dimensions=MAX_ACTIVE_DIMENSIONS,
        )

    def _load_authority(self, requested_company: str) -> AuthorityVector:
        assert self.connection is not None
        if not isinstance(requested_company, str) or not requested_company:
            _fail()
        user_rows = self.connection.execute(
            f"SELECT enabled, user_type FROM `tabUser` WHERE {_exact_predicate('name')}",
            (self.actor, self.actor),
        )
        authenticated = (
            len(user_rows) == 1
            and int(user_rows[0]["enabled"]) == 1
            and user_rows[0]["user_type"] == "System User"
        )
        role_rows = self.connection.execute(
            f"""
            SELECT role FROM `tabHas Role`
            WHERE {_exact_predicate('parent')} AND parenttype = 'User'
            ORDER BY role
            """,
            (self.actor, self.actor),
        )
        effective_roles = {str(row["role"]) for row in role_rows}
        if authenticated:
            effective_roles.add("All")
            effective_roles.add("Guest")
            effective_roles.add("Desk User")
        roles = frozenset(effective_roles)
        permission_rows = self.connection.execute(
            f"""
            SELECT allow, for_value, apply_to_all_doctypes, applicable_for, hide_descendants
            FROM `tabUser Permission`
            WHERE {_exact_predicate('user')}
            ORDER BY name
            """,
            (self.actor, self.actor),
        )
        permissions = tuple(
            UserPermissionSpec(
                allow=str(row["allow"]),
                for_value=str(row["for_value"]),
                apply_to_all_doctypes=int(row["apply_to_all_doctypes"] or 0),
                applicable_for=row["applicable_for"],
                hide_descendants=int(row["hide_descendants"] or 0),
            )
            for row in permission_rows
        )
        company_permissions = tuple(
            item.for_value for item in permissions if item.allow == "Company"
        )
        custom_rows = self.connection.execute(
            """
            SELECT parent, role, permlevel, `read`, report, if_owner, mask
            FROM `tabCustom DocPerm`
            WHERE parent IN ('Account', 'GL Entry')
            """
        )
        actor_custom_rows = [row for row in custom_rows if str(row["role"]) in roles]
        standard_rows = self.connection.execute(
            """
            SELECT parent, permlevel, `read`, report, if_owner, mask
            FROM `tabDocPerm`
            WHERE parent IN ('Account', 'GL Entry') AND role = 'Accounts Manager'
            ORDER BY parent, permlevel
            """
        )
        standard_ok: dict[str, bool] = {"Account": False, "GL Entry": False}
        owner_only = masked = elevated = False
        for row in standard_rows:
            parent = str(row["parent"])
            permlevel = int(row["permlevel"] or 0)
            if permlevel == 0 and int(row["read"] or 0) == 1 and int(row["report"] or 0) == 1:
                standard_ok[parent] = True
            owner_only = owner_only or int(row["if_owner"] or 0) == 1
            masked = masked or int(row["mask"] or 0) == 1
            elevated = elevated or permlevel != 0
        for row in actor_custom_rows:
            owner_only = owner_only or int(row["if_owner"] or 0) == 1
            masked = masked or int(row["mask"] or 0) == 1
            elevated = elevated or int(row["permlevel"] or 0) != 0
        field_rows = self.connection.execute(
            """
            SELECT parent, fieldname, COALESCE(permlevel, 0) AS permlevel
            FROM `tabDocField`
            WHERE parent IN ('Account', 'GL Entry')
            UNION ALL
            SELECT dt AS parent, fieldname, COALESCE(permlevel, 0) AS permlevel
            FROM `tabCustom Field`
            WHERE dt IN ('Account', 'GL Entry')
            """
        )
        account_fields = {
            str(row["fieldname"])
            for row in field_rows
            if row["parent"] == "Account" and int(row["permlevel"] or 0) == 0
        }
        gl_fields = {
            str(row["fieldname"])
            for row in field_rows
            if row["parent"] == "GL Entry" and int(row["permlevel"] or 0) == 0
        }
        account_fields.add("name")
        elevated = elevated or any(
            int(row["permlevel"] or 0) != 0
            and (
                (row["parent"] == "Account" and row["fieldname"] in REQUIRED_ACCOUNT_FIELDS)
                or (row["parent"] == "GL Entry" and row["fieldname"] in REQUIRED_GL_FIELDS)
            )
            for row in field_rows
        )
        share_rows = self.connection.execute(
            f"""
            SELECT name FROM `tabDocShare`
            WHERE share_doctype IN ('Account', 'GL Entry')
              AND (`everyone` = 1 OR ({_exact_predicate('user')}))
              AND `read` = 1
            """,
            (self.actor, self.actor),
        )
        drift_rows = self.connection.execute(
            """
            SELECT custom_role.name, assigned.role
            FROM `tabCustom Role` AS custom_role
            INNER JOIN `tabHas Role` AS assigned
                    ON assigned.parent = custom_role.name
                   AND assigned.parenttype = 'Custom Role'
            WHERE custom_role.report IN ('General Ledger', 'Trial Balance')
               OR custom_role.ref_doctype IN ('Account', 'GL Entry')
            """
        )
        relevant_custom_role = any(str(row["role"]) in roles for row in drift_rows)
        property_rows = self.connection.execute(
            """
            SELECT doc_type, field_name, property, value
            FROM `tabProperty Setter`
            WHERE doc_type IN ('Account', 'GL Entry')
              AND property IN ('permlevel', 'mask')
            """
        )
        relevant_property_rows = [
            row
            for row in property_rows
            if (
                row["doc_type"] == "Account"
                and row["field_name"] in REQUIRED_ACCOUNT_FIELDS
            )
            or (
                row["doc_type"] == "GL Entry"
                and row["field_name"] in REQUIRED_GL_FIELDS
            )
        ]
        for row in relevant_property_rows:
            if row["property"] == "permlevel":
                try:
                    elevated = elevated or int(str(row["value"] or "0")) != 0
                except ValueError:
                    _fail()
            elif row["property"] == "mask":
                masked = masked or str(row["value"] or "0") not in {"", "0"}
        strict_rows = self.connection.execute(
            """
            SELECT value FROM `tabSingles`
            WHERE doctype = 'System Settings'
              AND field = 'apply_strict_user_permissions'
            """
        )
        if len(strict_rows) > 1 or (
            strict_rows and str(strict_rows[0]["value"] or "0") not in {"0", "1"}
        ):
            _fail()
        strict_user_permissions = bool(
            strict_rows and str(strict_rows[0]["value"] or "0") == "1"
        )
        dimension_rows = self.connection.execute(
            "SELECT name FROM `tabAccounting Dimension` WHERE disabled = 0"
        )
        hooks_resolved = not self.permission_hook_snapshot.relevant_unresolved
        return AuthorityVector(
            authenticated=authenticated,
            actor=self.actor,
            roles=roles,
            requested_company=requested_company,
            company_permissions=company_permissions,
            user_permissions=permissions,
            account_read=standard_ok["Account"],
            account_report=standard_ok["Account"],
            gl_read=standard_ok["GL Entry"],
            gl_report=standard_ok["GL Entry"],
            required_account_fields=frozenset(account_fields & REQUIRED_ACCOUNT_FIELDS),
            required_gl_fields=frozenset(gl_fields & REQUIRED_GL_FIELDS),
            custom_docperm_override=bool(custom_rows),
            property_setter_override=bool(relevant_property_rows),
            owner_only=owner_only,
            elevated_permlevel=elevated,
            masked_field=masked,
            relevant_share=bool(share_rows),
            custom_report_role_drift=relevant_custom_role,
            permission_hooks_resolved=hooks_resolved,
            active_dimensions=len(dimension_rows),
            strict_user_permissions=strict_user_permissions,
        )

    def _load_fiscal_years(self, context: ProofContext) -> list[FiscalYearSpec]:
        assert self.connection is not None
        rows = self.connection.execute(
            """
            SELECT fy.name,
                   CAST(fy.year_start_date AS CHAR) AS start_date,
                   CAST(fy.year_end_date AS CHAR) AS end_date,
                   fy.disabled,
                   fyc.company
            FROM `tabFiscal Year` AS fy
            LEFT JOIN `tabFiscal Year Company` AS fyc ON fyc.parent = fy.name
            WHERE fyc.company IS NULL OR (
                BINARY fyc.company = BINARY %s
                AND OCTET_LENGTH(fyc.company) = OCTET_LENGTH(%s)
            )
            ORDER BY fy.name, fyc.company
            """,
            (context.company, context.company),
        )
        grouped: dict[str, dict[str, Any]] = {}
        for row in rows:
            key = str(row["name"])
            item = grouped.setdefault(
                key,
                {
                    "start": _strict_iso_date(str(row["start_date"])),
                    "end": _strict_iso_date(str(row["end_date"])),
                    "disabled": int(row["disabled"] or 0),
                    "companies": [],
                },
            )
            if row["company"]:
                item["companies"].append(str(row["company"]))
        result = [
            FiscalYearSpec(
                key=key,
                start=value["start"],
                end=value["end"],
                companies=tuple(value["companies"]),
                disabled=value["disabled"],
            )
            for key, value in grouped.items()
        ]
        _resolve_context(context, result)
        return result

    def _load_chart(self, context: ProofContext) -> list[AccountSpec]:
        assert self.connection is not None
        self.access.read_account()
        rows = self.connection.execute(
            f"""
            SELECT name, company, parent_account, is_group, root_type, lft, rgt,
                   account_currency, disabled
            FROM `tabAccount`
            WHERE {_exact_predicate('company')}
            ORDER BY lft, name
            """,
            (context.company, context.company),
        )
        return [
            AccountSpec(
                key=str(row["name"]),
                company=str(row["company"]),
                parent=str(row["parent_account"]) if row["parent_account"] else None,
                is_group=int(row["is_group"] or 0),
                root_type=str(row["root_type"]),
                lft=int(row["lft"]),
                rgt=int(row["rgt"]),
                account_currency=str(row["account_currency"]),
                disabled=int(row["disabled"] or 0),
            )
            for row in rows
        ]

    def _load_aggregates(
        self,
        context: ProofContext,
        fiscal_year: FiscalYearSpec,
        chart: Mapping[str, AccountSpec],
    ) -> dict[str, SixAmounts]:
        assert self.connection is not None
        default_book = context.default_books[0]
        company_exact = (
            "BINARY gle.company = BINARY %s "
            "AND OCTET_LENGTH(gle.company) = OCTET_LENGTH(%s)"
        )
        book_exact = (
            "(gle.finance_book IS NULL OR OCTET_LENGTH(gle.finance_book) = 0 OR "
            "(BINARY gle.finance_book = BINARY %s "
            "AND OCTET_LENGTH(gle.finance_book) = OCTET_LENGTH(%s)))"
        )
        account_join = (
            "BINARY gle.account = BINARY account.name "
            "AND OCTET_LENGTH(gle.account) = OCTET_LENGTH(account.name)"
        )
        validation = self.connection.execute(
            f"""
            SELECT
              COUNT(*) AS source_rows,
              SUM(CASE WHEN gle.posting_date IS NULL THEN 1 ELSE 0 END)
                AS bad_posting_date,
              SUM(CASE WHEN gle.debit IS NULL OR gle.credit IS NULL THEN 1 ELSE 0 END)
                AS bad_amount_null,
              SUM(CASE WHEN gle.is_cancelled NOT IN (0, 1) OR gle.is_cancelled IS NULL THEN 1 ELSE 0 END)
                AS bad_cancelled,
              SUM(CASE WHEN gle.is_opening NOT IN ('Yes', 'No') OR gle.is_opening IS NULL THEN 1 ELSE 0 END)
                AS bad_opening,
              SUM(CASE WHEN gle.debit < 0 OR gle.credit < 0 THEN 1 ELSE 0 END)
                AS bad_negative,
              SUM(CASE WHEN gle.debit <> TRUNCATE(gle.debit, %s)
                            OR gle.credit <> TRUNCATE(gle.credit, %s) THEN 1 ELSE 0 END)
                AS bad_scale,
              SUM(CASE WHEN account.name IS NULL THEN 1 ELSE 0 END)
                AS bad_account,
              SUM(CASE WHEN account.name IS NOT NULL
                            AND (account.is_group = 1
                                 OR BINARY account.company <> BINARY gle.company
                                 OR OCTET_LENGTH(account.company) <> OCTET_LENGTH(gle.company))
                       THEN 1 ELSE 0 END)
                AS bad_account_scope,
              SUM(CASE WHEN account.root_type IN ('Income', 'Expense')
                            AND gle.is_opening = 'Yes' THEN 1 ELSE 0 END)
                AS bad_pnl_opening
            FROM `tabGL Entry` AS gle
            LEFT JOIN `tabAccount` AS account ON {account_join}
            WHERE {company_exact}
              AND (gle.posting_date IS NULL OR gle.posting_date <= %s)
              AND {book_exact}
            """,
            (
                context.precision,
                context.precision,
                context.company,
                context.company,
                context.to_date.isoformat(),
                default_book,
                default_book,
            ),
        )
        if len(validation) != 1:
            _fail()
        self.source_scope_rows = int(validation[0]["source_rows"] or 0)
        if any(
            int(value or 0) != 0
            for key, value in validation[0].items()
            if key.startswith("bad_")
        ):
            _fail()

        self.access.read_gl()
        self._boundary("opening")
        aggregate_sql = f"""
            SELECT gle.account,
              CAST(COALESCE(SUM(CASE
                WHEN account.root_type IN ('Asset', 'Liability', 'Equity')
                 AND (gle.posting_date < %s OR gle.is_opening = 'Yes')
                THEN gle.debit
                WHEN account.root_type IN ('Income', 'Expense')
                 AND gle.posting_date >= %s AND gle.posting_date < %s
                 AND gle.is_opening <> 'Yes'
                THEN gle.debit ELSE 0 END), 0) AS CHAR) AS opening_debit,
              CAST(COALESCE(SUM(CASE
                WHEN account.root_type IN ('Asset', 'Liability', 'Equity')
                 AND (gle.posting_date < %s OR gle.is_opening = 'Yes')
                THEN gle.credit
                WHEN account.root_type IN ('Income', 'Expense')
                 AND gle.posting_date >= %s AND gle.posting_date < %s
                 AND gle.is_opening <> 'Yes'
                THEN gle.credit ELSE 0 END), 0) AS CHAR) AS opening_credit,
              CAST(COALESCE(SUM(CASE
                WHEN gle.posting_date >= %s AND gle.posting_date <= %s
                 AND gle.is_opening <> 'Yes'
                THEN gle.debit ELSE 0 END), 0) AS CHAR) AS period_debit,
              CAST(COALESCE(SUM(CASE
                WHEN gle.posting_date >= %s AND gle.posting_date <= %s
                 AND gle.is_opening <> 'Yes'
                THEN gle.credit ELSE 0 END), 0) AS CHAR) AS period_credit
            FROM `tabGL Entry` AS gle
            INNER JOIN `tabAccount` AS account ON {account_join}
            WHERE {company_exact}
              AND gle.is_cancelled = 0
              AND gle.posting_date <= %s
              AND {book_exact}
            GROUP BY gle.account
            ORDER BY gle.account
            """
        aggregate_values = (
            context.from_date.isoformat(),
            fiscal_year.start.isoformat(),
            context.from_date.isoformat(),
            context.from_date.isoformat(),
            fiscal_year.start.isoformat(),
            context.from_date.isoformat(),
            context.from_date.isoformat(),
            context.to_date.isoformat(),
            context.from_date.isoformat(),
            context.to_date.isoformat(),
            context.company,
            context.company,
            context.to_date.isoformat(),
            default_book,
            default_book,
        )
        if self.capture_query_plan:
            plan_rows = self.connection.execute(
                f"EXPLAIN FORMAT=JSON {aggregate_sql}", aggregate_values
            )
            if len(plan_rows) != 1 or len(plan_rows[0]) != 1:
                _fail()
            raw_plan = next(iter(plan_rows[0].values()))
            if not isinstance(raw_plan, str):
                _fail()
            try:
                parsed_plan = json.loads(raw_plan)
            except json.JSONDecodeError:
                _fail()

            def estimated_rows(value: Any) -> int:
                if isinstance(value, dict):
                    subtotal = 0
                    for key, item in value.items():
                        if key == "rows" and isinstance(item, int) and not isinstance(item, bool):
                            subtotal += item
                        else:
                            subtotal += estimated_rows(item)
                    return subtotal
                if isinstance(value, list):
                    return sum(estimated_rows(item) for item in value)
                return 0

            self.query_plan_sha256 = _sha256_bytes(raw_plan.encode("utf-8"))
            self.query_plan_estimated_rows = estimated_rows(parsed_plan)
            self.query_plan_structure = _sanitize_query_plan(parsed_plan)
        aggregate_rows = self.connection.execute(aggregate_sql, aggregate_values)
        self._boundary("movement")
        aggregates: dict[str, SixAmounts] = {
            key: SixAmounts() for key, account in chart.items() if account.is_group == 0
        }
        for row in aggregate_rows:
            key = str(row["account"])
            account = chart.get(key)
            if account is None or account.is_group != 0 or key not in aggregates:
                _fail()
            aggregates[key] = SixAmounts(
                opening_debit=_major_to_minor(
                    _strict_decimal_from_db(row["opening_debit"], context.precision),
                    context.precision,
                ),
                opening_credit=_major_to_minor(
                    _strict_decimal_from_db(row["opening_credit"], context.precision),
                    context.precision,
                ),
                period_debit=_major_to_minor(
                    _strict_decimal_from_db(row["period_debit"], context.precision),
                    context.precision,
                ),
                period_credit=_major_to_minor(
                    _strict_decimal_from_db(row["period_credit"], context.precision),
                    context.precision,
                ),
            )
        return aggregates

    def run(self) -> tuple[dict[str, Any], ReconstructionResult | None, tuple[int, ...]]:
        self._request_started_ns = time.perf_counter_ns()
        period_days = (self.request_to_date - self.request_from_date).days + 1
        if self.candidate_limits is not None:
            if (
                period_days <= 0
                or period_days > self.candidate_limits["MAX_PERIOD_DAYS"]
                or 3 > self.candidate_limits["MAX_OUTPUT_ROWS"]
                or 0 > self.candidate_limits["MAX_RETRIES"]
            ):
                return _generic_failure(), None, ()
        rows_read_before = 0
        try:
            self.connection_attempts += 1
            self.connection_hosts_attempted.append(self.env.db_host)
            self.connection = StrictMariaDBConnection(
                self.env,
                statement_timeout_ms=(
                    self.candidate_limits["STATEMENT_TIMEOUT_MS"]
                    if self.candidate_limits is not None
                    else None
                ),
            )
            pre_hook_hash = self.permission_hook_snapshot.fingerprint
            self.connection.begin_read_snapshot()
            self.connection.verify_innodb_transaction()
            if self.statement_delay_ms is not None:
                self.connection.execute(
                    "SELECT SLEEP(%s) AS completed",
                    (
                        format(
                            Decimal(self.statement_delay_ms) / Decimal(1000),
                            "f",
                        ),
                    ),
                )
            rows_read_before = self.connection.session_rows_read()
            authority = self._load_authority(self.company)
            decision = authorize_internal(authority)
            self._boundary("authority")
            if not decision.allowed:
                _fail()
            context = self._load_context()
            self._boundary("context")
            fiscal_years = self._load_fiscal_years(context)
            fiscal_year, _ = _resolve_context(context, fiscal_years)
            self._boundary("fiscal")
            accounts = self._load_chart(context)
            chart, children = _validate_chart(context, accounts)
            if (
                self.candidate_limits is not None
                and len(chart) > self.candidate_limits["MAX_ACCOUNTS"]
            ):
                _fail()
            self._boundary("chart")
            aggregates = self._load_aggregates(context, fiscal_year, chart)
            self._boundary("hierarchy")
            result = _finish_reconstruction(
                context,
                fiscal_year,
                chart,
                children,
                aggregates,
                self.access,
            )
            self._boundary("validation")
            public = serialize_public_success(result, context)
            serialized = _canonical_json_inline(public)
            self.candidate_serialized_size = len(serialized)
            if (
                self.candidate_limits is not None
                and len(serialized) > self.candidate_limits["MAX_RESPONSE_BYTES"]
            ):
                _fail()
            self._boundary("serialization")
            post_hook_hash = self.permission_hook_snapshot.fingerprint
            if pre_hook_hash != post_hook_hash:
                _fail()
            self.connection.assert_same_connection()
            self._assert_request_deadline()
            self.serialized_bytes = serialized
            return public, result, tuple(self.connection.connection_ids)
        except Exception:
            self.serialized_bytes = None
            ids = tuple(self.connection.connection_ids) if self.connection else ()
            return _generic_failure(), None, ids
        finally:
            if self.connection is not None:
                try:
                    rows_read_after = self.connection.session_rows_read()
                except Exception:
                    rows_read_after = rows_read_before
                request_ms = (
                    _elapsed_ms_ceil(time.perf_counter_ns() - self._request_started_ns)
                    if self._request_started_ns is not None
                    else 0
                )
                self.metrics = {
                    "request_latency_ms": request_ms,
                    "statement_duration_ms": _elapsed_ms_ceil(
                        self.connection.max_statement_duration_ns
                    ),
                    "statement_total_duration_ms": _elapsed_ms_ceil(
                        self.connection.statement_duration_ns
                    ),
                    "examined_database_rows": max(rows_read_after - rows_read_before, 0),
                    "statement_count": self.connection.statement_count,
                    "rows_fetched": self.connection.rows_fetched,
                    "source_scope_rows": self.source_scope_rows,
                    "reconnect_retries": max(self.connection_attempts - 1, 0),
                    "statement_timeouts": self.connection.statement_timeout_count,
                    "fallback_host_attempts": sum(
                        host != self.env.db_host
                        for host in self.connection_hosts_attempted
                    ),
                }
                try:
                    self.connection.rollback()
                except Exception:
                    pass
                self.connection.close()
            else:
                self.metrics = {
                    "request_latency_ms": (
                        _elapsed_ms_ceil(time.perf_counter_ns() - self._request_started_ns)
                        if self._request_started_ns is not None
                        else 0
                    ),
                    "statement_duration_ms": 0,
                    "statement_total_duration_ms": 0,
                    "examined_database_rows": 0,
                    "statement_count": 0,
                    "rows_fetched": 0,
                    "source_scope_rows": 0,
                    "reconnect_retries": max(self.connection_attempts - 1, 0),
                    "statement_timeouts": 0,
                    "fallback_host_attempts": sum(
                        host != self.env.db_host
                        for host in self.connection_hosts_attempted
                    ),
                }


def _verify_topology_and_schema(env: SyntheticEnvironment) -> dict[str, Any]:
    connection = StrictMariaDBConnection(env, topology=True)
    try:
        state = connection.execute(
            """
            SELECT DATABASE() AS database_name,
                   @@GLOBAL.read_only AS global_read_only,
                   @@hostname AS server_hostname,
                   @@port AS server_port,
                   @@server_id AS server_id
            """,
            verify_connection=False,
        )
        if (
            len(state) != 1
            or state[0]["database_name"] != env.db_name
            or int(state[0]["global_read_only"]) != 0
            or int(state[0]["server_port"]) != env.db_port
        ):
            _fail()
        replica_rows = connection.execute("SHOW ALL REPLICAS STATUS", verify_connection=False)
        if replica_rows:
            _fail()
        table_names = tuple(REQUIRED_SOURCE_TABLES)
        placeholders = ", ".join(["%s"] * len(table_names))
        engine_rows = connection.execute(
            f"""
            SELECT TABLE_NAME AS table_name, ENGINE AS engine
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME IN ({placeholders})
            """,
            (env.db_name, *table_names),
            verify_connection=False,
        )
        engines = {str(row["table_name"]): str(row["engine"]).upper() for row in engine_rows}
        if set(engines) != set(table_names) or any(engine != "INNODB" for engine in engines.values()):
            _fail()
        for table, required_columns in REQUIRED_SOURCE_TABLES.items():
            rows = connection.execute(
                """
                SELECT COLUMN_NAME AS column_name
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s
                  AND BINARY TABLE_NAME = BINARY %s
                  AND OCTET_LENGTH(TABLE_NAME) = OCTET_LENGTH(%s)
                """,
                (env.db_name, table, table),
                verify_connection=False,
            )
            columns = {str(row["column_name"]) for row in rows}
            if not set(required_columns).issubset(columns):
                _fail()
        return {
            "database_identity_sha256": _sha256_bytes(env.db_name.encode("utf-8")),
            "server_identity_sha256": _sha256_bytes(
                f"{state[0]['server_hostname']}:{state[0]['server_port']}:{state[0]['server_id']}".encode(
                    "utf-8"
                )
            ),
            "primary_read_only": False,
            "replica_rows": 0,
            "source_table_count": len(REQUIRED_SOURCE_TABLES),
            "all_source_tables_innodb": True,
        }
    finally:
        connection.rollback()
        connection.close()


def _kill_synthetic_reader(env: SyntheticEnvironment, connection_id: int) -> None:
    if isinstance(connection_id, bool) or not isinstance(connection_id, int) or connection_id <= 0:
        _fail()
    topology = StrictMariaDBConnection(env, topology=True)
    try:
        rows = topology.execute(
            """
            SELECT ID AS connection_id, DB AS database_name, USER AS database_user,
                   HOST AS client_host
            FROM INFORMATION_SCHEMA.PROCESSLIST
            WHERE ID = %s
            """,
            (connection_id,),
            verify_connection=False,
        )
        if (
            len(rows) != 1
            or rows[0]["database_name"] != env.db_name
            or rows[0]["database_user"] != env.db_user
            or not rows[0]["client_host"]
        ):
            _fail()
        topology.execute(f"KILL CONNECTION {connection_id}", verify_connection=False)
    finally:
        topology.close()


def _base_chart(company: str, currency: str) -> list[AccountSpec]:
    return [
        AccountSpec("ASSET_ROOT", company, None, 1, "Asset", 1, 10, currency),
        AccountSpec("CURRENT_ASSETS", company, "ASSET_ROOT", 1, "Asset", 2, 9, currency),
        AccountSpec("CASH", company, "CURRENT_ASSETS", 0, "Asset", 3, 4, currency),
        AccountSpec("RECEIVABLE", company, "CURRENT_ASSETS", 0, "Asset", 5, 6, currency),
        AccountSpec("ZERO_ASSET", company, "CURRENT_ASSETS", 0, "Asset", 7, 8, currency),
        AccountSpec("EQUITY_ROOT", company, None, 1, "Equity", 11, 14, currency),
        AccountSpec("EQUITY", company, "EQUITY_ROOT", 0, "Equity", 12, 13, currency),
        AccountSpec("INCOME_ROOT", company, None, 1, "Income", 15, 18, currency),
        AccountSpec("REVENUE", company, "INCOME_ROOT", 0, "Income", 16, 17, currency),
        AccountSpec("EXPENSE_ROOT", company, None, 1, "Expense", 19, 22, currency),
        AccountSpec("EXPENSE", company, "EXPENSE_ROOT", 0, "Expense", 20, 21, currency),
        AccountSpec("LIABILITY_ROOT", company, None, 1, "Liability", 23, 26, currency),
        AccountSpec("PAYABLE", company, "LIABILITY_ROOT", 0, "Liability", 24, 25, currency),
    ]


def _base_context(env: SyntheticEnvironment, company: str, default_book: str) -> ProofContext:
    return ProofContext(
        company=company,
        currency=env.currency,
        precision=env.precision,
        from_date=env.from_date,
        to_date=env.to_date,
        default_books=(default_book,),
        active_dimensions=MAX_ACTIVE_DIMENSIONS,
    )


def _base_fiscal_year(env: SyntheticEnvironment, company: str) -> list[FiscalYearSpec]:
    return [
        FiscalYearSpec(
            key="FY_CURRENT",
            start=env.fiscal_start,
            end=env.fiscal_end,
            companies=(company,),
        )
    ]


def _base_rows(context: ProofContext) -> list[GLEntrySpec]:
    opening_date = context.from_date - timedelta(days=1)
    return [
        GLEntrySpec(
            "OPEN_CASH",
            context.company,
            opening_date,
            "CASH",
            Decimal("100"),
            Decimal("0"),
            0,
            "No",
            context.default_books[0],
        ),
        GLEntrySpec(
            "OPEN_EQUITY",
            context.company,
            opening_date,
            "EQUITY",
            Decimal("0"),
            Decimal("100"),
            0,
            "No",
            context.default_books[0],
        ),
        GLEntrySpec(
            "MOVE_AR",
            context.company,
            context.from_date,
            "RECEIVABLE",
            Decimal("60"),
            Decimal("0"),
            0,
            "No",
            context.default_books[0],
        ),
        GLEntrySpec(
            "MOVE_REVENUE",
            context.company,
            context.from_date,
            "REVENUE",
            Decimal("0"),
            Decimal("60"),
            0,
            "No",
            context.default_books[0],
        ),
        GLEntrySpec(
            "MOVE_CASH",
            context.company,
            context.to_date,
            "CASH",
            Decimal("40"),
            Decimal("0"),
            0,
            "No",
            context.default_books[0],
        ),
        GLEntrySpec(
            "MOVE_AR_SETTLE",
            context.company,
            context.to_date,
            "RECEIVABLE",
            Decimal("0"),
            Decimal("40"),
            0,
            "No",
            context.default_books[0],
        ),
    ]


def _expected_public(
    context: ProofContext,
    *,
    opening: Decimal,
    period: Decimal,
    closing: Decimal,
) -> dict[str, Any]:
    def text(value: Decimal) -> str:
        return _minor_to_major(_major_to_minor(value, context.precision), context.precision)

    value = {
        "status": "ready",
        "source_mode": CANDIDATE,
        "context": {
            "company_scope": "single_authorized",
            "currency_scope": "company_base",
            "period_scope": "single_fiscal_year_inclusive",
            "finance_book_scope": "company_default_plus_unbooked",
            "dimension_scope": "none",
        },
        "opening": {"debit": text(opening), "credit": text(opening)},
        "period": {"debit": text(period), "credit": text(period)},
        "closing": {"debit": text(closing), "credit": text(closing)},
        "gross_balance_exact": True,
        "presentation_balance_exact": True,
        "integrity_status": "exact",
    }
    _assert_public_key_containment(value)
    return value


def _attempt_reconstruction(
    context: ProofContext,
    fiscal_years: Sequence[FiscalYearSpec],
    accounts: Sequence[AccountSpec],
    rows: Sequence[GLEntrySpec],
) -> tuple[str, dict[str, Any], ReconstructionResult | None]:
    try:
        result = reconstruct_raw_gl(context, fiscal_years, accounts, rows)
        public = serialize_public_success(result, context)
        return "ready", public, result
    except ProofUnavailable:
        return "deny", _generic_failure(), None


@dataclass(frozen=True)
class FixtureNames:
    scope: str
    company_a: str
    company_b: str
    book_default: str
    book_alternate: str
    fiscal_year: str
    actor: str
    accounts: Mapping[str, str]


def _fixture_names(env: SyntheticEnvironment, scope: str) -> FixtureNames:
    if not re.fullmatch(r"[A-Z0-9_]+", scope):
        _fail()
    prefix = f"SYNTH_{env.run_id}_{scope}_"
    accounts = {key: f"{prefix}{key}" for key in (
        "ASSET_ROOT",
        "CURRENT_ASSETS",
        "CASH",
        "RECEIVABLE",
        "ZERO_ASSET",
        "EQUITY_ROOT",
        "EQUITY",
        "INCOME_ROOT",
        "REVENUE",
        "EXPENSE_ROOT",
        "EXPENSE",
        "LIABILITY_ROOT",
        "PAYABLE",
    )}
    return FixtureNames(
        scope=scope,
        company_a=f"{prefix}COMPANY_A",
        company_b=f"{prefix}COMPANY_B",
        book_default=f"{prefix}BOOK_DEFAULT",
        book_alternate=f"{prefix}BOOK_ALTERNATE",
        fiscal_year=f"{prefix}FY",
        actor=f"{prefix}ACCOUNTS_MANAGER@invalid.example",
        accounts=accounts,
    )


def _map_account(account: AccountSpec, names: FixtureNames) -> AccountSpec:
    return replace(
        account,
        key=names.accounts[account.key],
        company=names.company_a,
        parent=names.accounts[account.parent] if account.parent else None,
    )


def _map_row(row: GLEntrySpec, names: FixtureNames, index: int) -> GLEntrySpec:
    return replace(
        row,
        key=f"SYNTH_{names.scope}_{index:04d}",
        company=names.company_a,
        account=names.accounts[row.account],
        finance_book=names.book_default if row.finance_book else row.finance_book,
    )


def _seed_database_scope(
    env: SyntheticEnvironment,
    gate: FixtureMutationGate,
    names: FixtureNames,
    canaries: CanaryRegistry,
) -> None:
    company = _base_row(names.company_a)
    company.update(
        {
            "company_name": names.company_a,
            "abbr": f"A{env.run_id[:5]}{names.scope[:3]}",
            "default_currency": env.currency,
            "default_finance_book": names.book_default,
            "is_group": 0,
        }
    )
    gate.insert("tabCompany", company)
    company_b = _base_row(names.company_b)
    company_b.update(
        {
            "company_name": names.company_b,
            "abbr": f"B{env.run_id[:5]}{names.scope[:3]}",
            "default_currency": env.currency,
            "default_finance_book": names.book_default,
            "is_group": 0,
        }
    )
    gate.insert("tabCompany", company_b)
    for book_name in (names.book_default, names.book_alternate):
        row = _base_row(book_name)
        row["finance_book_name"] = book_name
        gate.insert("tabFinance Book", row)
    fiscal = _base_row(names.fiscal_year)
    fiscal.update(
        {
            "year": names.fiscal_year,
            "disabled": 0,
            "is_short_year": 0,
            "year_start_date": env.fiscal_start.isoformat(),
            "year_end_date": env.fiscal_end.isoformat(),
            "auto_created": 0,
        }
    )
    gate.insert("tabFiscal Year", fiscal)
    fiscal_company_name = f"SYNTH_{env.run_id}_{names.scope}_FY_COMPANY"
    fiscal_company = _base_row(fiscal_company_name)
    fiscal_company.update(
        {
            "parent": names.fiscal_year,
            "parenttype": "Fiscal Year",
            "parentfield": "companies",
            "company": names.company_a,
        }
    )
    gate.insert("tabFiscal Year Company", fiscal_company)
    chart = [_map_account(item, names) for item in _base_chart(names.company_a, env.currency)]
    canary_values = list(CANARY_TEMPLATES)
    for index, account in enumerate(chart):
        row = _base_row(account.key)
        row.update(
            {
                "account_name": f"{canaries.value(canary_values[index % len(canary_values)])}_{index:03d}",
                "account_number": f"{canaries.value('account_number')}_{index:03d}",
                "is_group": account.is_group,
                "company": account.company,
                "root_type": account.root_type,
                "report_type": (
                    "Balance Sheet" if account.root_type in BALANCE_SHEET_ROOTS else "Profit and Loss"
                ),
                "account_currency": account.account_currency,
                "parent_account": account.parent or "",
                "lft": account.lft,
                "rgt": account.rgt,
                "disabled": account.disabled,
            }
        )
        gate.insert("tabAccount", row)
    user = _base_row(names.actor)
    user.update(
        {
            "email": names.actor,
            "first_name": "Synthetic",
            "enabled": 1,
            "user_type": "System User",
            "send_welcome_email": 0,
        }
    )
    gate.insert("tabUser", user)
    role = _base_row(f"SYNTH_{env.run_id}_{names.scope}_HAS_ROLE")
    role.update(
        {
            "parent": names.actor,
            "parenttype": "User",
            "parentfield": "roles",
            "role": "Accounts Manager",
        }
    )
    gate.insert("tabHas Role", role)
    permission = _base_row(f"SYNTH_{env.run_id}_{names.scope}_COMPANY_PERMISSION")
    permission.update(
        {
            "user": names.actor,
            "allow": "Company",
            "for_value": names.company_a,
            "is_default": 1,
            "apply_to_all_doctypes": 1,
            "applicable_for": "",
            "hide_descendants": 0,
        }
    )
    gate.insert("tabUser Permission", permission)
    context = _base_context(env, names.company_a, names.book_default)
    rows = [_map_row(item, names, index) for index, item in enumerate(_base_rows(context))]
    for index, entry in enumerate(rows):
        row = _base_row(f"SYNTH_{env.run_id}_{names.scope}_GL_{index:04d}")
        row.update(
            {
                "posting_date": entry.posting_date.isoformat(),
                "account": entry.account,
                "debit": entry.debit,
                "credit": entry.credit,
                "account_currency": env.currency,
                "debit_in_account_currency": entry.debit,
                "credit_in_account_currency": entry.credit,
                "voucher_type": "",
                "company": entry.company,
                "finance_book": entry.finance_book,
                "is_opening": entry.is_opening,
                "is_cancelled": entry.is_cancelled,
                "party_type": "Customer",
                "party": canaries.value("party"),
                "voucher_no": canaries.value("voucher_reference"),
                "against_voucher": canaries.value("voucher_reference"),
                "remarks": (
                    canaries.value("poison_scope")
                    if entry.key.startswith("W_POISON_")
                    else canaries.value("free_text")
                ),
                "owner": canaries.value("actor_contact"),
                "modified_by": canaries.value("actor_contact"),
                "cost_center": canaries.value("dimension"),
                "project": canaries.value("dimension"),
            }
        )
        gate.insert("tabGL Entry", row)
    gate.commit()


def _insert_gl_entry(
    env: SyntheticEnvironment,
    gate: FixtureMutationGate,
    names: FixtureNames,
    *,
    suffix: str,
    account_key: str,
    debit: Decimal,
    credit: Decimal,
    posting_date: date,
    finance_book: str | None = None,
    is_cancelled: int = 0,
    is_opening: str = "No",
    voucher_type: str = "",
    voucher_no: str = "",
) -> None:
    row = _base_row(f"SYNTH_{env.run_id}_{names.scope}_GL_{suffix}")
    row.update(
        {
            "posting_date": posting_date.isoformat(),
            "account": names.accounts[account_key],
            "debit": debit,
            "credit": credit,
            "account_currency": env.currency,
            "debit_in_account_currency": debit,
            "credit_in_account_currency": credit,
            "voucher_type": voucher_type,
            "voucher_no": voucher_no,
            "company": names.company_a,
            "finance_book": names.book_default if finance_book is None else finance_book,
            "is_opening": is_opening,
            "is_cancelled": is_cancelled,
            "remarks": "",
        }
    )
    gate.insert("tabGL Entry", row)


def _insert_balanced_pair(
    env: SyntheticEnvironment,
    gate: FixtureMutationGate,
    names: FixtureNames,
    *,
    suffix: str,
    amount: Decimal,
    posting_date: date,
) -> None:
    _insert_gl_entry(
        env,
        gate,
        names,
        suffix=f"{suffix}_DEBIT",
        account_key="CASH",
        debit=amount,
        credit=Decimal("0"),
        posting_date=posting_date,
    )
    _insert_gl_entry(
        env,
        gate,
        names,
        suffix=f"{suffix}_CREDIT",
        account_key="EQUITY",
        debit=Decimal("0"),
        credit=amount,
        posting_date=posting_date,
    )


def _generate_workload_fixture(
    env: SyntheticEnvironment,
    point: Mapping[str, int],
) -> tuple[ProofContext, list[FiscalYearSpec], list[AccountSpec], list[GLEntrySpec], dict[str, Any]]:
    if set(point) != set(WORKLOAD_POINT_KEYS):
        _fail()
    account_count = point["accounts"]
    depth = point["chart_depth"]
    period_days = point["period_days"]
    eligible_rows = point["eligible_gl_rows"]
    poison_rows = point["poison_gl_rows"]
    if (
        account_count < depth + 2
        or depth < 1
        or period_days < 1
        or eligible_rows < 2
        or eligible_rows % 2 != 0
        or point["concurrent_readers"] < 1
        or point["cache_state_code"] not in (0, 1)
    ):
        _fail()
    to_date = env.from_date + timedelta(days=period_days - 1)
    if to_date > env.fiscal_end:
        _fail()
    company = "WORKLOAD_COMPANY_A"
    book = "WORKLOAD_BOOK_DEFAULT"
    context = ProofContext(
        company=company,
        currency=env.currency,
        precision=env.precision,
        from_date=env.from_date,
        to_date=to_date,
        default_books=(book,),
        active_dimensions=point["active_dimensions"],
    )
    fiscal_years = [
        FiscalYearSpec("WORKLOAD_FY", env.fiscal_start, env.fiscal_end, (company,))
    ]

    group_keys = [f"W_GROUP_{index}" for index in range(depth)]
    leaf_count = account_count - depth
    leaf_keys = [f"W_LEAF_{index}" for index in range(leaf_count)]
    children: dict[str, list[str]] = defaultdict(list)
    for index in range(1, len(group_keys)):
        children[group_keys[index - 1]].append(group_keys[index])
    children[group_keys[-1]].extend(leaf_keys)
    endpoints: dict[str, tuple[int, int]] = {}
    counter = 1

    def assign(key: str) -> None:
        nonlocal counter
        left = counter
        counter += 1
        for child in children.get(key, ()):
            assign(child)
        right = counter
        counter += 1
        endpoints[key] = (left, right)

    assign(group_keys[0])
    accounts: list[AccountSpec] = []
    for index, key in enumerate(group_keys):
        left, right = endpoints[key]
        accounts.append(
            AccountSpec(
                key,
                company,
                group_keys[index - 1] if index else None,
                1,
                "Asset",
                left,
                right,
                env.currency,
            )
        )
    for key in leaf_keys:
        left, right = endpoints[key]
        accounts.append(
            AccountSpec(
                key,
                company,
                group_keys[-1],
                0,
                "Asset",
                left,
                right,
                env.currency,
            )
        )
    rows: list[GLEntrySpec] = []
    pair_count = eligible_rows // 2
    for index in range(pair_count):
        posting = env.from_date + timedelta(days=index % period_days)
        rows.append(
            GLEntrySpec(
                f"W_ELIGIBLE_D_{index}",
                company,
                posting,
                leaf_keys[0],
                Decimal("1"),
                Decimal("0"),
                0,
                "No",
                book,
            )
        )
        rows.append(
            GLEntrySpec(
                f"W_ELIGIBLE_C_{index}",
                company,
                posting,
                leaf_keys[1],
                Decimal("0"),
                Decimal("1"),
                0,
                "No",
                book,
            )
        )
    for index in range(poison_rows):
        poison_class = index % 4
        rows.append(
            GLEntrySpec(
                f"W_POISON_{index}",
                "WORKLOAD_COMPANY_B" if poison_class == 0 else company,
                to_date + timedelta(days=1) if poison_class == 2 else env.from_date,
                leaf_keys[0] if poison_class != 0 else "WORKLOAD_COMPANY_B_ACCOUNT",
                Decimal("777"),
                Decimal("0"),
                1 if poison_class == 1 else 0,
                "No",
                "WORKLOAD_BOOK_ALTERNATE" if poison_class == 3 else book,
            )
        )
    expected_amount = Decimal(pair_count)
    expected = _expected_public(
        context,
        opening=Decimal("0"),
        period=expected_amount,
        closing=expected_amount,
    )
    manifest = {
        "series_code": point["series_code"],
        "step": point["step"],
        "variant_code": point["variant_code"],
        "accounts": account_count,
        "chart_depth": depth,
        "period_days": period_days,
        "eligible_gl_rows": eligible_rows,
        "poison_gl_rows": poison_rows,
        "concurrent_readers": point["concurrent_readers"],
        "declared_response_bytes": point["response_bytes"],
        "active_dimensions": point["active_dimensions"],
        "cache_state": (
            "first_candidate_read_fresh_scope_no_candidate_cache"
            if point["cache_state_code"] == 0
            else "repeat_candidate_read_no_candidate_cache"
        ),
        "expected_public_sha256": _sha256_bytes(_canonical_json_inline(expected)),
    }
    return context, fiscal_years, accounts, rows, manifest


def _seed_workload_database_scope(
    env: SyntheticEnvironment,
    gate: FixtureMutationGate,
    *,
    scope: str,
    point: Mapping[str, int],
    canaries: CanaryRegistry,
) -> tuple[FixtureNames, ProofContext, Mapping[str, Any], Mapping[str, Any], int]:
    """Materialize one externally bounded workload point in the disposable DB."""

    started = time.perf_counter_ns()
    context, _years, chart, rows, manifest = _generate_workload_fixture(env, point)
    if context.active_dimensions != 0:
        _fail()
    base_names = _fixture_names(env, scope)
    prefix = f"SYNTH_{env.run_id}_{scope}_"
    account_names = {account.key: f"{prefix}{account.key}" for account in chart}
    names = replace(base_names, accounts=account_names)

    default_book = _base_row(names.book_default)
    default_book.update({"finance_book_name": names.book_default})
    alternate_book = _base_row(names.book_alternate)
    alternate_book.update({"finance_book_name": names.book_alternate})
    gate.insert("tabFinance Book", default_book)
    gate.insert("tabFinance Book", alternate_book)

    company = _base_row(names.company_a)
    company.update(
        {
            "company_name": names.company_a,
            "abbr": f"W{scope[-6:]}",
            "default_currency": env.currency,
            "default_finance_book": names.book_default,
            "country": "United States",
            "is_group": 0,
        }
    )
    gate.insert("tabCompany", company)
    fiscal = _base_row(names.fiscal_year)
    fiscal.update(
        {
            "year": names.fiscal_year,
            "disabled": 0,
            "is_short_year": 0,
            "year_start_date": env.fiscal_start.isoformat(),
            "year_end_date": env.fiscal_end.isoformat(),
            "auto_created": 0,
        }
    )
    gate.insert("tabFiscal Year", fiscal)
    fiscal_company = _base_row(f"{prefix}FY_COMPANY")
    fiscal_company.update(
        {
            "parent": names.fiscal_year,
            "parenttype": "Fiscal Year",
            "parentfield": "companies",
            "company": names.company_a,
        }
    )
    gate.insert("tabFiscal Year Company", fiscal_company)

    for index, account in enumerate(chart):
        row = _base_row(account_names[account.key])
        row.update(
            {
                "account_name": f"{canaries.value('account_name')}_{index:06d}",
                "account_number": f"{canaries.value('account_number')}_{index:06d}",
                "is_group": account.is_group,
                "company": names.company_a,
                "root_type": account.root_type,
                "report_type": "Balance Sheet",
                "account_currency": env.currency,
                "parent_account": account_names[account.parent] if account.parent else "",
                "lft": account.lft,
                "rgt": account.rgt,
                "disabled": account.disabled,
            }
        )
        gate.insert("tabAccount", row)

    user = _base_row(names.actor)
    user.update(
        {
            "email": names.actor,
            "first_name": "Synthetic Workload",
            "enabled": 1,
            "user_type": "System User",
            "send_welcome_email": 0,
        }
    )
    gate.insert("tabUser", user)
    role = _base_row(f"{prefix}HAS_ROLE")
    role.update(
        {
            "parent": names.actor,
            "parenttype": "User",
            "parentfield": "roles",
            "role": "Accounts Manager",
        }
    )
    gate.insert("tabHas Role", role)
    permission = _base_row(f"{prefix}COMPANY_PERMISSION")
    permission.update(
        {
            "user": names.actor,
            "allow": "Company",
            "for_value": names.company_a,
            "is_default": 1,
            "apply_to_all_doctypes": 1,
            "applicable_for": "",
            "hide_descendants": 0,
        }
    )
    gate.insert("tabUser Permission", permission)

    mapped_context = replace(
        context,
        company=names.company_a,
        default_books=(names.book_default,),
    )
    for index, entry in enumerate(rows):
        if entry.company == "WORKLOAD_COMPANY_B":
            mapped_company = names.company_b
            mapped_account = f"{prefix}COMPANY_B_ACCOUNT"
        else:
            mapped_company = names.company_a
            mapped_account = account_names[entry.account]
        if entry.finance_book == "WORKLOAD_BOOK_ALTERNATE":
            mapped_book: str | None = names.book_alternate
        elif entry.finance_book == "WORKLOAD_BOOK_DEFAULT":
            mapped_book = names.book_default
        else:
            mapped_book = entry.finance_book
        row = _base_row(f"{prefix}GL_{index:08d}")
        row.update(
            {
                "posting_date": entry.posting_date.isoformat(),
                "account": mapped_account,
                "debit": entry.debit,
                "credit": entry.credit,
                "account_currency": env.currency,
                "debit_in_account_currency": entry.debit,
                "credit_in_account_currency": entry.credit,
                "voucher_type": "",
                "voucher_no": canaries.value("voucher_reference"),
                "company": mapped_company,
                "finance_book": mapped_book,
                "is_opening": entry.is_opening,
                "is_cancelled": entry.is_cancelled,
                "party_type": "Customer",
                "party": canaries.value("party"),
                "against_voucher": canaries.value("voucher_reference"),
                "remarks": (
                    canaries.value("poison_scope")
                    if entry.key.startswith("W_POISON_")
                    else canaries.value("free_text")
                ),
                "owner": canaries.value("actor_contact"),
                "modified_by": canaries.value("actor_contact"),
                "cost_center": canaries.value("dimension"),
                "project": canaries.value("dimension"),
            }
        )
        gate.insert("tabGL Entry", row)
    gate.commit()
    expected = _expected_public(
        mapped_context,
        opening=Decimal("0"),
        period=Decimal(point["eligible_gl_rows"] // 2),
        closing=Decimal(point["eligible_gl_rows"] // 2),
    )
    setup_ms = _elapsed_ms_ceil(time.perf_counter_ns() - started)
    return names, mapped_context, expected, manifest, setup_ms


def _positive_authority(company: str = "COMPANY_A") -> AuthorityVector:
    return AuthorityVector(
        authenticated=True,
        actor="SYNTHETIC_ACCOUNTS_MANAGER",
        roles=frozenset({"Accounts Manager"}),
        requested_company=company,
        company_permissions=(company,),
        user_permissions=(UserPermissionSpec("Company", company),),
    )


def _authority_manifest(vector: AuthorityVector) -> dict[str, Any]:
    return {
        "authenticated": vector.authenticated,
        "actor_sha256": _sha256_bytes(vector.actor.encode("utf-8")),
        "role_set_sha256": _sha256_bytes(
            _canonical_json_inline(sorted(vector.roles))
        ),
        "requested_company_sha256": (
            _sha256_bytes(vector.requested_company.encode("utf-8"))
            if vector.requested_company is not None
            else None
        ),
        "company_authority_count": len(vector.company_permissions),
        "user_permission_count": len(vector.user_permissions),
        "account_read": vector.account_read,
        "account_report": vector.account_report,
        "gl_read": vector.gl_read,
        "gl_report": vector.gl_report,
        "account_field_count": len(vector.required_account_fields),
        "gl_field_count": len(vector.required_gl_fields),
        "custom_docperm_override": vector.custom_docperm_override,
        "property_setter_override": vector.property_setter_override,
        "owner_only": vector.owner_only,
        "elevated_permlevel": vector.elevated_permlevel,
        "masked_field": vector.masked_field,
        "relevant_share": vector.relevant_share,
        "custom_report_role_drift": vector.custom_report_role_drift,
        "permission_hooks_resolved": vector.permission_hooks_resolved,
        "active_dimensions": vector.active_dimensions,
        "dimension_filter": vector.dimension_filter,
        "unsupported_context": vector.unsupported_context,
        "caps_valid": vector.externally_supplied_caps_valid,
        "snapshot_valid": vector.snapshot_valid,
        "complete_chart_valid": vector.complete_chart_valid,
        "exact_balance_valid": vector.exact_balance_valid,
        "public_schema_valid": vector.public_schema_valid,
        "strict_user_permissions": vector.strict_user_permissions,
    }


@unittest.skipUnless(
    os.environ.get("SYNTH_GL_TB_GATE") == SYNTHETIC_GATE_VALUE,
    "internal disposable Finance GL/TB synthetic gate is not active",
)
class TestFinanceGLTrialBalanceSourceProof(unittest.TestCase):
    """One internal synthetic module; execution requires a later Owner gate."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        global FROZEN_PERMISSION_HOOK_SNAPSHOT
        cls.env = SyntheticEnvironment.load()
        if not (cls.env.fiscal_start < cls.env.from_date < cls.env.to_date <= cls.env.fiscal_end):
            _fail()
        cls.workload_plan = WorkloadPlan.from_environment()
        CANDIDATE_FORBIDDEN_READS.update({"acb": 0, "pcv": 0})
        cls.canaries = CanaryRegistry(cls.env.run_id)
        cls.evidence = EvidenceWriter(cls.env.evidence_root, cls.canaries)
        cls.logs = SyntheticLogCapture(cls.canaries)
        cls.containment = StaticContainmentAudit.inspect(Path(__file__))
        cls.permission_hook_snapshot = _capture_permission_hook_snapshot()
        FROZEN_PERMISSION_HOOK_SNAPSHOT = cls.permission_hook_snapshot
        allowed_existing = HARNESS_EVIDENCE_BASENAMES | EXTERNAL_EVIDENCE_BASENAMES
        for child in cls.env.evidence_root.iterdir():
            if child.name not in allowed_existing or child.is_symlink() or not child.is_file():
                _fail()
            if child.name in HARNESS_EVIDENCE_BASENAMES:
                _fail()
        cls.topology_summary = _verify_topology_and_schema(cls.env)
        cls.source_hash_before = _sha256_bytes(Path(__file__).read_bytes())
        cls.mutation_connection = StrictMariaDBConnection(cls.env)
        cls.mutations = FixtureMutationGate(cls.mutation_connection, cls.env.run_id)
        cls.base_names = _fixture_names(cls.env, "BASE")
        _seed_database_scope(cls.env, cls.mutations, cls.base_names, cls.canaries)
        cls.evidence.write_json(
            "fixture-manifest.json",
            {
                "candidate": CANDIDATE,
                "run_id_sha256": _sha256_bytes(cls.env.run_id.encode("utf-8")),
                "harness_sha256": cls.source_hash_before,
                "accounting_fixture_ids": list(ACCOUNTING_IDS),
                "permission_fixture_ids": list(PERMISSION_IDS),
                "snapshot_fixture_ids": list(SNAPSHOT_IDS),
                "canary_hashes": list(cls.canaries.hashes),
                "workload_plan_sha256": _sha256_bytes(
                    os.environ["SYNTH_WORKLOAD_PLAN_JSON"].encode("utf-8")
                ),
                "topology_summary_sha256": _sha256_bytes(
                    _canonical_json_inline(cls.topology_summary)
                ),
            },
        )

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            if hasattr(cls, "source_hash_before"):
                source_hash_after = _sha256_bytes(Path(__file__).read_bytes())
                if source_hash_after != cls.source_hash_before:
                    _fail()
            if hasattr(cls, "mutations") and hasattr(cls, "evidence"):
                current_hooks = _capture_permission_hook_snapshot()
                if current_hooks != cls.permission_hook_snapshot:
                    _fail()
                sentinel = cls.mutations.sentinel_summary(
                    cls.containment, CANDIDATE_FORBIDDEN_READS
                )
                sentinel["harness_source_unchanged"] = True
                sentinel["harness_owned_evidence_only"] = True
                cls.evidence.write_json("mutation-sentinel.json", sentinel)
                log_matches = sum(cls.canaries.scan_value(record) for record in cls.logs.records)
                if log_matches:
                    _fail()
                scan = cls.evidence.scan_harness_owned()
                cls.evidence.append_jsonl(
                    "leakage-results.jsonl",
                    {
                        "fixture_id": "LEAKAGE_FINAL_HARNESS_OWNED",
                        "candidate": CANDIDATE,
                        "artifact_match_counts": scan,
                        "captured_log_match_count": log_matches,
                        "all_zero": all(value == 0 for value in scan.values()),
                        "runner_junit": "external_pending",
                        "environment_teardown": "external_pending",
                    },
                )
                if any(scan.values()):
                    _fail()
                cls.evidence.finalize()
        finally:
            if hasattr(cls, "mutation_connection"):
                cls.mutation_connection.close()
            if hasattr(cls, "evidence"):
                cls.evidence.close()
            super().tearDownClass()

    def _record_case(
        self,
        *,
        fixture_id: str,
        variant: str,
        family: str,
        expected_decision: str,
        expected: Mapping[str, Any],
        actual_decision: str,
        actual: Mapping[str, Any],
        accessor_calls: int | None,
        authority_vector: Mapping[str, Any] | None = None,
        connection_ids: Sequence[int] | None = None,
    ) -> None:
        canary_matches = self.canaries.scan_value(actual)
        record = _fixture_record(
            fixture_id=fixture_id,
            family=family,
            input_manifest={"fixture_id": fixture_id, "variant": variant},
            authority_vector=authority_vector,
            expected_decision=expected_decision,
            expected=expected,
            actual_decision=actual_decision,
            actual=actual,
            accessor_calls=accessor_calls,
            connection_ids=connection_ids,
            canary_matches=canary_matches,
        )
        target = {
            "accounting": "accounting-results.jsonl",
            "permission": "permission-results.jsonl",
            "snapshot": "snapshot-results.jsonl",
            "workload": "workload-results.jsonl",
        }[family]
        self.evidence.append_jsonl(target, record)
        self.evidence.append_jsonl(
            "expected-actual-diff.jsonl",
            {
                "fixture_id": fixture_id,
                "variant": variant,
                "expected_sha256": record["expected_sha256"],
                "actual_sha256": record["actual_sha256"],
                "expected": dict(expected),
                "actual": dict(actual),
                "equal": record["exact_diff"] == "none",
            },
        )
        self.logs.emit(
            fixture_id=fixture_id,
            result_class="pass" if record["result"] == "pass" else "fail",
            duration_class="bounded",
        )
        self.assertEqual(0, canary_matches)
        self.assertEqual("pass", record["result"])

    def _require_public_equivalence(
        self, expected: Mapping[str, Any], actual: Mapping[str, Any]
    ) -> None:
        """Compare without allowing an unexpected payload into JUnit failure text."""

        try:
            if self.canaries.scan_value(actual):
                _fail()
            if _canonical_json_inline(expected) != _canonical_json_inline(actual):
                _fail()
        except ProofUnavailable:
            raise
        except Exception:
            _fail()

    def _record_accounting_attempt(
        self,
        *,
        fixture_id: str,
        variant: str,
        context: ProofContext,
        fiscal_years: Sequence[FiscalYearSpec],
        accounts: Sequence[AccountSpec],
        rows: Sequence[GLEntrySpec],
        expected_decision: str,
        expected: Mapping[str, Any],
    ) -> ReconstructionResult | None:
        actual_decision, actual, result = _attempt_reconstruction(
            context, fiscal_years, accounts, rows
        )
        calls = (
            result.account_accessor_calls + result.gl_accessor_calls if result is not None else 0
        )
        self._record_case(
            fixture_id=fixture_id,
            variant=variant,
            family="accounting",
            expected_decision=expected_decision,
            expected=expected,
            actual_decision=actual_decision,
            actual=actual,
            accessor_calls=calls,
        )
        return result

    def test_20_permission_company_and_leakage_catalog(self) -> None:
        positive = _positive_authority()
        cases: list[tuple[str, str, AuthorityVector, str]] = []
        cases.append(("P01", "guest", replace(positive, authenticated=False, actor="Guest"), "deny"))
        for role in (
            "Accounts User",
            "Auditor",
            "Sales User",
            "Purchase User",
            "Stock User",
            "Executive",
            "AI User",
            "Roleless",
        ):
            roles = frozenset() if role == "Roleless" else frozenset({role})
            cases.append(("P02", role, replace(positive, roles=roles), "deny"))
        cases.extend(
            [
                ("P03", "administrator", replace(positive, actor="Administrator"), "deny"),
                (
                    "P04",
                    "mixed_privilege",
                    replace(positive, roles=frozenset({"Accounts Manager", "System Manager"})),
                    "deny",
                ),
                ("P05", "missing_selected_company", replace(positive, requested_company=None), "deny"),
                ("P06", "zero_companies", replace(positive, company_permissions=()), "deny"),
                (
                    "P06",
                    "multiple_companies",
                    replace(positive, company_permissions=("COMPANY_A", "COMPANY_B")),
                    "deny",
                ),
                ("P07", "company_mismatch", replace(positive, requested_company="COMPANY_B"), "deny"),
                (
                    "P08",
                    "leaf_account_permission",
                    replace(
                        positive,
                        user_permissions=positive.user_permissions
                        + (UserPermissionSpec("Account", "LEAF"),),
                    ),
                    "deny",
                ),
                (
                    "P09",
                    "parent_descendants_visible",
                    replace(
                        positive,
                        user_permissions=positive.user_permissions
                        + (UserPermissionSpec("Account", "PARENT", hide_descendants=0),),
                    ),
                    "deny",
                ),
                (
                    "P10",
                    "parent_descendants_hidden",
                    replace(
                        positive,
                        user_permissions=positive.user_permissions
                        + (UserPermissionSpec("Account", "PARENT", hide_descendants=1),),
                    ),
                    "deny",
                ),
                (
                    "P11",
                    "applicable_for",
                    replace(
                        positive,
                        user_permissions=positive.user_permissions
                        + (
                            UserPermissionSpec(
                                "Warehouse",
                                "IRRELEVANT_VALUE",
                                apply_to_all_doctypes=0,
                                applicable_for="GL Entry",
                            ),
                        ),
                    ),
                    "deny",
                ),
                (
                    "P12",
                    "cost_center_permission",
                    replace(
                        positive,
                        user_permissions=positive.user_permissions
                        + (UserPermissionSpec("Cost Center", "CC"),),
                    ),
                    "deny",
                ),
                (
                    "P13",
                    "project_permission",
                    replace(
                        positive,
                        user_permissions=positive.user_permissions
                        + (UserPermissionSpec("Project", "PROJECT"),),
                    ),
                    "deny",
                ),
                ("P14", "active_dimension", replace(positive, active_dimensions=1), "deny"),
                ("P15", "dimension_filter", replace(positive, dimension_filter=True), "deny"),
                (
                    "P16",
                    "custom_docperm",
                    replace(positive, custom_docperm_override=True),
                    "deny",
                ),
                ("P17", "owner_only", replace(positive, owner_only=True), "deny"),
                (
                    "P18",
                    "field_permlevel",
                    replace(
                        positive,
                        elevated_permlevel=True,
                        required_gl_fields=frozenset(REQUIRED_GL_FIELDS - {"debit"}),
                    ),
                    "deny",
                ),
                ("P19", "mask", replace(positive, masked_field=True), "deny"),
                ("P20", "share_only", replace(positive, relevant_share=True), "deny"),
                (
                    "P21",
                    "wrong_role_share",
                    replace(
                        positive,
                        roles=frozenset({"Accounts User"}),
                        relevant_share=True,
                    ),
                    "deny",
                ),
                (
                    "P22",
                    "custom_report_role",
                    replace(
                        positive,
                        roles=frozenset({"Accounts User"}),
                        custom_report_role_drift=True,
                    ),
                    "deny",
                ),
                (
                    "P23",
                    "native_report_role_removed",
                    replace(positive, native_report_roles=frozenset()),
                    "allow",
                ),
                (
                    "P24",
                    "unresolved_permission_hook",
                    replace(positive, permission_hooks_resolved=False),
                    "deny",
                ),
                (
                    "P25",
                    "required_field_omitted",
                    replace(
                        positive,
                        required_account_fields=frozenset(REQUIRED_ACCOUNT_FIELDS - {"root_type"}),
                    ),
                    "deny",
                ),
                (
                    "P26",
                    "unsupported_context",
                    replace(positive, unsupported_context=True),
                    "deny",
                ),
            ]
        )
        seen: set[str] = set()
        denial_bytes: list[bytes] = []
        for fixture_id, variant, vector, expected_decision in cases:
            with self.subTest(fixture_id=fixture_id, variant=variant):
                seen.add(fixture_id)
                decision = authorize_internal(vector)
                actual_decision = "allow" if decision.allowed else "deny"
                actual = (
                    {"authorization": "allow", "accounting_accessor_calls": 0}
                    if decision.allowed
                    else dict(decision.public or {})
                )
                expected = (
                    {"authorization": "allow", "accounting_accessor_calls": 0}
                    if expected_decision == "allow"
                    else _generic_failure()
                )
                if not decision.allowed:
                    denial_bytes.append(_normalize_failure_bytes(actual))
                self.assertEqual(0, decision.accounting_accessor_calls)
                self._record_case(
                    fixture_id=fixture_id,
                    variant=variant,
                    family="permission",
                    expected_decision=expected_decision,
                    expected=expected,
                    actual_decision=actual_decision,
                    actual=actual,
                    accessor_calls=decision.accounting_accessor_calls,
                    authority_vector=_authority_manifest(vector),
                )
        self.assertEqual(set(PERMISSION_IDS[:26]), seen)
        self.assertTrue(denial_bytes)
        self.assertEqual(1, len(set(denial_bytes)))

        controls = [
            positive,
            replace(
                positive,
                user_permissions=positive.user_permissions
                + (UserPermissionSpec("Warehouse", "IRRELEVANT"),),
            ),
            replace(positive, irrelevant_share=True),
            replace(positive, strict_user_permissions=False),
            replace(positive, native_report_roles=frozenset({"Some Other Report Role"})),
            _positive_authority("COMPANY_B"),
        ]
        for vector in controls:
            self.assertTrue(authorize_internal(vector).allowed)

    def test_25_installed_permission_extraction_controls(self) -> None:
        """Exercise material authority states through the pinned database reader."""

        def seed(scope: str) -> FixtureNames:
            names = _fixture_names(self.env, scope)
            _seed_database_scope(self.env, self.mutations, names, self.canaries)
            return names

        def record_reader(
            *,
            fixture_id: str,
            variant: str,
            names: FixtureNames,
            expected_decision: str,
            actor: str | None = None,
            company: str | None = None,
        ) -> tuple[dict[str, Any], ReconstructionResult | None]:
            requested_company = names.company_a if company is None else company
            reader = DatabaseProofReader(
                self.env,
                company=requested_company,
                actor=actor or names.actor,
            )
            public, result, connection_ids = reader.run()
            actual_decision = "allow" if result is not None else "deny"
            expected = (
                _expected_public(
                    _base_context(self.env, requested_company, names.book_default),
                    opening=Decimal("100"),
                    period=Decimal("100"),
                    closing=Decimal("160"),
                )
                if expected_decision == "allow"
                else _generic_failure()
            )
            self._record_case(
                fixture_id=fixture_id,
                variant=f"installed_{variant}",
                family="permission",
                expected_decision=expected_decision,
                expected=expected,
                actual_decision=actual_decision,
                actual=public,
                accessor_calls=reader.access.account + reader.access.gl,
                connection_ids=connection_ids,
            )
            if expected_decision == "deny":
                self.assertEqual(0, reader.access.account + reader.access.gl)
            return public, result

        base = seed("PDB_BASE")
        record_reader(
            fixture_id="P01",
            variant="guest",
            names=base,
            actor="Guest",
            expected_decision="deny",
        )
        record_reader(
            fixture_id="P03",
            variant="administrator",
            names=base,
            actor="Administrator",
            expected_decision="deny",
        )
        record_reader(
            fixture_id="P05",
            variant="missing_selected_company",
            names=base,
            company="",
            expected_decision="deny",
        )

        wrong_role = seed("PDB_ROLE")
        role_row = f"SYNTH_{self.env.run_id}_{wrong_role.scope}_HAS_ROLE"
        self.mutations.update_by_name(
            "tabHas Role", role_row, {"role": "Accounts User"}
        )
        self.mutations.commit()
        record_reader(
            fixture_id="P02",
            variant="wrong_role",
            names=wrong_role,
            expected_decision="deny",
        )

        mixed = seed("PDB_MIXED")
        mixed_role = _base_row(
            f"SYNTH_{self.env.run_id}_{mixed.scope}_SYSTEM_MANAGER_ROLE"
        )
        mixed_role.update(
            {
                "parent": mixed.actor,
                "parenttype": "User",
                "parentfield": "roles",
                "role": "System Manager",
            }
        )
        self.mutations.insert("tabHas Role", mixed_role)
        self.mutations.commit()
        record_reader(
            fixture_id="P04",
            variant="mixed_privilege",
            names=mixed,
            expected_decision="deny",
        )

        multiple = seed("PDB_MULTI")
        second_company_permission = _base_row(
            f"SYNTH_{self.env.run_id}_{multiple.scope}_SECOND_COMPANY_PERMISSION"
        )
        second_company_permission.update(
            {
                "user": multiple.actor,
                "allow": "Company",
                "for_value": multiple.company_b,
                "is_default": 0,
                "apply_to_all_doctypes": 1,
                "applicable_for": "",
                "hide_descendants": 0,
            }
        )
        self.mutations.insert("tabUser Permission", second_company_permission)
        self.mutations.commit()
        record_reader(
            fixture_id="P06",
            variant="multiple_companies",
            names=multiple,
            expected_decision="deny",
        )

        actor_scope = seed("PDB_ACTOR_A")
        other_scope = seed("PDB_COMPANY_B")
        record_reader(
            fixture_id="P07",
            variant="company_mismatch",
            names=other_scope,
            actor=actor_scope.actor,
            company=other_scope.company_a,
            expected_decision="deny",
        )

        account_limited = seed("PDB_ACCOUNT_PERMISSION")
        account_permission = _base_row(
            f"SYNTH_{self.env.run_id}_{account_limited.scope}_ACCOUNT_PERMISSION"
        )
        account_permission.update(
            {
                "user": account_limited.actor,
                "allow": "Account",
                "for_value": account_limited.accounts["CASH"],
                "is_default": 0,
                "apply_to_all_doctypes": 1,
                "applicable_for": "",
                "hide_descendants": 0,
            }
        )
        self.mutations.insert("tabUser Permission", account_permission)
        self.mutations.commit()
        record_reader(
            fixture_id="P08",
            variant="account_user_permission",
            names=account_limited,
            expected_decision="deny",
        )
        self.mutations.update_by_name(
            "tabUser Permission",
            account_permission["name"],
            {
                "for_value": account_limited.accounts["CURRENT_ASSETS"],
                "hide_descendants": 0,
            },
        )
        self.mutations.commit()
        record_reader(
            fixture_id="P09",
            variant="parent_permission_descendants_visible",
            names=account_limited,
            expected_decision="deny",
        )
        self.mutations.update_by_name(
            "tabUser Permission",
            account_permission["name"],
            {"hide_descendants": 1},
        )
        self.mutations.commit()
        record_reader(
            fixture_id="P10",
            variant="parent_permission_descendants_hidden",
            names=account_limited,
            expected_decision="deny",
        )
        self.mutations.update_by_name(
            "tabUser Permission",
            account_permission["name"],
            {
                "allow": "Warehouse",
                "for_value": f"SYNTH_{self.env.run_id}_{account_limited.scope}_IRRELEVANT",
                "applicable_for": "GL Entry",
                "hide_descendants": 0,
            },
        )
        self.mutations.commit()
        record_reader(
            fixture_id="P11",
            variant="applicable_for_gl_entry",
            names=account_limited,
            expected_decision="deny",
        )
        self.mutations.update_by_name(
            "tabUser Permission",
            account_permission["name"],
            {"allow": "Cost Center", "applicable_for": ""},
        )
        self.mutations.commit()
        record_reader(
            fixture_id="P12",
            variant="cost_center_permission",
            names=account_limited,
            expected_decision="deny",
        )
        self.mutations.update_by_name(
            "tabUser Permission", account_permission["name"], {"allow": "Project"}
        )
        self.mutations.commit()
        record_reader(
            fixture_id="P13",
            variant="project_permission",
            names=account_limited,
            expected_decision="deny",
        )

        dimension_scope = seed("PDB_DIMENSION")
        dimension_name = f"SYNTH_{self.env.run_id}_{dimension_scope.scope}_DIMENSION"
        dimension = _base_row(dimension_name)
        dimension.update(
            {
                "label": "Synthetic Dimension",
                "document_type": "Cost Center",
                "fieldname": f"synth_{self.env.run_id}_dimension",
                "disabled": 0,
            }
        )
        self.mutations.insert("tabAccounting Dimension", dimension)
        self.mutations.commit()
        record_reader(
            fixture_id="P14",
            variant="active_dimension",
            names=dimension_scope,
            expected_decision="deny",
        )
        self.mutations.update_by_name(
            "tabAccounting Dimension", dimension_name, {"disabled": 1}
        )
        self.mutations.commit()

        custom_scope = seed("PDB_CUSTOM_DOCPERM")
        custom_name = f"SYNTH_{self.env.run_id}_{custom_scope.scope}_CUSTOM_DOCPERM"
        custom = _base_row(custom_name)
        custom.update(
            {
                "parent": "GL Entry",
                "parenttype": "DocType",
                "parentfield": "permissions",
                "role": "Accounts Manager",
                "permlevel": 0,
                "read": 0,
                "report": 0,
                "if_owner": 0,
                "mask": 0,
            }
        )
        self.mutations.insert("tabCustom DocPerm", custom)
        self.mutations.commit()
        record_reader(
            fixture_id="P16",
            variant="custom_docperm",
            names=custom_scope,
            expected_decision="deny",
        )
        self.mutations.update_by_name(
            "tabCustom DocPerm",
            custom_name,
            {"read": 1, "report": 1, "if_owner": 1},
        )
        self.mutations.commit()
        record_reader(
            fixture_id="P17",
            variant="custom_docperm_owner_only",
            names=custom_scope,
            expected_decision="deny",
        )
        self.mutations.update_by_name(
            "tabCustom DocPerm",
            custom_name,
            {"role": "Synthetic Irrelevant Role"},
        )
        self.mutations.commit()
        record_reader(
            fixture_id="P17_GLOBAL_REPLACEMENT",
            variant="custom_docperm_unrelated_role_still_replaces_standard_permissions",
            names=custom_scope,
            expected_decision="deny",
        )
        self.mutations.update_by_name(
            "tabCustom DocPerm",
            custom_name,
            {
                "parent": f"SYNTH_{self.env.run_id}_{custom_scope.scope}_IRRELEVANT_DOCTYPE"
            },
        )
        self.mutations.commit()

        property_scope = seed("PDB_PROPERTY")
        property_name = f"SYNTH_{self.env.run_id}_{property_scope.scope}_PROPERTY"
        property_row = _base_row(property_name)
        property_row.update(
            {
                "doctype_or_field": "DocField",
                "doc_type": "GL Entry",
                "field_name": "debit",
                "property": "permlevel",
                "value": "1",
                "property_type": "Int",
            }
        )
        self.mutations.insert("tabProperty Setter", property_row)
        self.mutations.commit()
        record_reader(
            fixture_id="P18",
            variant="property_setter_permlevel",
            names=property_scope,
            expected_decision="deny",
        )
        self.mutations.update_by_name(
            "tabProperty Setter",
            property_name,
            {"property": "mask", "value": "1", "property_type": "Check"},
        )
        self.mutations.commit()
        record_reader(
            fixture_id="P19",
            variant="property_setter_mask",
            names=property_scope,
            expected_decision="deny",
        )
        self.mutations.update_by_name(
            "tabProperty Setter", property_name, {"field_name": "unrelated_field"}
        )
        self.mutations.commit()

        share_scope = seed("PDB_SHARE")
        share_name = f"SYNTH_{self.env.run_id}_{share_scope.scope}_SHARE"
        share = _base_row(share_name)
        share.update(
            {
                "user": share_scope.actor,
                "share_doctype": "Account",
                "share_name": share_scope.accounts["CASH"],
                "read": 1,
                "write": 0,
                "share": 0,
                "submit": 0,
                "everyone": 0,
            }
        )
        self.mutations.insert("tabDocShare", share)
        self.mutations.commit()
        record_reader(
            fixture_id="P20",
            variant="relevant_share",
            names=share_scope,
            expected_decision="deny",
        )
        self.mutations.update_by_name(
            "tabHas Role",
            f"SYNTH_{self.env.run_id}_{share_scope.scope}_HAS_ROLE",
            {"role": "Accounts User"},
        )
        self.mutations.commit()
        record_reader(
            fixture_id="P21",
            variant="wrong_role_relevant_share",
            names=share_scope,
            expected_decision="deny",
        )
        self.mutations.update_by_name("tabDocShare", share_name, {"read": 0})
        self.mutations.commit()

        custom_role_scope = seed("PDB_CUSTOM_ROLE")
        custom_role_name = f"SYNTH_{self.env.run_id}_{custom_role_scope.scope}_CUSTOM_ROLE"
        custom_role = _base_row(custom_role_name)
        custom_role.update(
            {"report": "Trial Balance", "ref_doctype": "GL Entry"}
        )
        self.mutations.insert("tabCustom Role", custom_role)
        assignment_name = (
            f"SYNTH_{self.env.run_id}_{custom_role_scope.scope}_CUSTOM_ROLE_ASSIGNMENT"
        )
        assignment = _base_row(assignment_name)
        assignment.update(
            {
                "parent": custom_role_name,
                "parenttype": "Custom Role",
                "parentfield": "roles",
                "role": "Accounts User",
            }
        )
        self.mutations.insert("tabHas Role", assignment)
        self.mutations.commit()
        record_reader(
            fixture_id="P23",
            variant="custom_report_role_excludes_actor",
            names=custom_role_scope,
            expected_decision="allow",
        )
        self.mutations.update_by_name(
            "tabHas Role", assignment_name, {"role": "Accounts Manager"}
        )
        self.mutations.commit()
        record_reader(
            fixture_id="P22",
            variant="custom_report_role_drift",
            names=custom_role_scope,
            expected_decision="deny",
        )
        self.mutations.update_by_name(
            "tabHas Role", assignment_name, {"role": "Synthetic Irrelevant Role"}
        )
        self.mutations.commit()

    def test_10_accounting_fixture_catalog(self) -> None:
        context = _base_context(self.env, "COMPANY_A", "BOOK_DEFAULT")
        years = _base_fiscal_year(self.env, context.company)
        chart = _base_chart(context.company, context.currency)
        rows = _base_rows(context)
        seen: set[str] = set()

        def run_case(
            fixture_id: str,
            variant: str,
            case_context: ProofContext,
            case_years: Sequence[FiscalYearSpec],
            case_chart: Sequence[AccountSpec],
            case_rows: Sequence[GLEntrySpec],
            expected_decision: str,
            expected: Mapping[str, Any],
        ) -> ReconstructionResult | None:
            seen.add(fixture_id)
            with self.subTest(fixture_id=fixture_id, variant=variant):
                return self._record_accounting_attempt(
                    fixture_id=fixture_id,
                    variant=variant,
                    context=case_context,
                    fiscal_years=case_years,
                    accounts=case_chart,
                    rows=case_rows,
                    expected_decision=expected_decision,
                    expected=expected,
                )

        base_expected = _expected_public(
            context,
            opening=Decimal("100"),
            period=Decimal("100"),
            closing=Decimal("160"),
        )
        a01 = run_case("A01", "core", context, years, chart, rows, "ready", base_expected)
        assert a01 is not None
        self.assertEqual(
            _major_to_minor(Decimal("200"), context.precision),
            a01.gross_totals.closing_debit,
        )
        self.assertEqual(
            _major_to_minor(Decimal("200"), context.precision),
            a01.gross_totals.closing_credit,
        )
        receivable = a01.leaves["RECEIVABLE"]
        self.assertEqual(
            _major_to_minor(Decimal("60"), context.precision), receivable.closing_debit
        )
        self.assertEqual(
            _major_to_minor(Decimal("40"), context.precision), receivable.closing_credit
        )
        self.assertEqual(
            _major_to_minor(Decimal("20"), context.precision), receivable.closing_net
        )

        a02_rows = rows + [
            GLEntrySpec(
                "A02_PRIOR_CASH",
                context.company,
                self.env.fiscal_start - timedelta(days=1),
                "CASH",
                Decimal("50"),
                Decimal("0"),
                0,
                "No",
                context.default_books[0],
            ),
            GLEntrySpec(
                "A02_PRIOR_EQUITY",
                context.company,
                self.env.fiscal_start - timedelta(days=1),
                "EQUITY",
                Decimal("0"),
                Decimal("50"),
                0,
                "No",
                context.default_books[0],
            ),
        ]
        a02_expected = _expected_public(
            context,
            opening=Decimal("150"),
            period=Decimal("100"),
            closing=Decimal("210"),
        )
        a02 = run_case("A02", "prior_balance_sheet", context, years, chart, a02_rows, "ready", a02_expected)
        assert a02 is not None
        self.assertEqual(
            _major_to_minor(Decimal("250"), context.precision),
            a02.gross_totals.closing_debit,
        )

        a03_rows = rows + [
            GLEntrySpec(
                "A03_PRIOR_EXPENSE",
                context.company,
                self.env.fiscal_start - timedelta(days=1),
                "EXPENSE",
                Decimal("30"),
                Decimal("0"),
                0,
                "No",
                context.default_books[0],
            ),
            GLEntrySpec(
                "A03_PRIOR_REVENUE",
                context.company,
                self.env.fiscal_start - timedelta(days=1),
                "REVENUE",
                Decimal("0"),
                Decimal("30"),
                0,
                "No",
                context.default_books[0],
            ),
            GLEntrySpec(
                "A03_CURRENT_EXPENSE",
                context.company,
                context.from_date - timedelta(days=1),
                "EXPENSE",
                Decimal("10"),
                Decimal("0"),
                0,
                "No",
                context.default_books[0],
            ),
            GLEntrySpec(
                "A03_CURRENT_REVENUE",
                context.company,
                context.from_date - timedelta(days=1),
                "REVENUE",
                Decimal("0"),
                Decimal("10"),
                0,
                "No",
                context.default_books[0],
            ),
        ]
        a03_expected = _expected_public(
            context,
            opening=Decimal("110"),
            period=Decimal("100"),
            closing=Decimal("170"),
        )
        a03 = run_case("A03", "pnl_fiscal_reset", context, years, chart, a03_rows, "ready", a03_expected)
        assert a03 is not None
        self.assertEqual(
            _major_to_minor(Decimal("10"), context.precision),
            a03.leaves["EXPENSE"].opening_debit,
        )

        a04_rows = rows + [
            GLEntrySpec(
                "A04_PRE_EXPENSE",
                context.company,
                context.from_date - timedelta(days=1),
                "EXPENSE",
                Decimal("5"),
                Decimal("0"),
                0,
                "No",
                context.default_books[0],
            ),
            GLEntrySpec(
                "A04_PRE_REVENUE",
                context.company,
                context.from_date - timedelta(days=1),
                "REVENUE",
                Decimal("0"),
                Decimal("5"),
                0,
                "No",
                context.default_books[0],
            ),
            GLEntrySpec(
                "A04_FROM_CASH",
                context.company,
                context.from_date,
                "CASH",
                Decimal("7"),
                Decimal("0"),
                0,
                "No",
                context.default_books[0],
            ),
            GLEntrySpec(
                "A04_FROM_EQUITY",
                context.company,
                context.from_date,
                "EQUITY",
                Decimal("0"),
                Decimal("7"),
                0,
                "No",
                context.default_books[0],
            ),
            GLEntrySpec(
                "A04_TO_CASH",
                context.company,
                context.to_date,
                "CASH",
                Decimal("9"),
                Decimal("0"),
                0,
                "No",
                context.default_books[0],
            ),
            GLEntrySpec(
                "A04_TO_EQUITY",
                context.company,
                context.to_date,
                "EQUITY",
                Decimal("0"),
                Decimal("9"),
                0,
                "No",
                context.default_books[0],
            ),
            GLEntrySpec(
                "A04_AFTER_CASH",
                context.company,
                context.to_date + timedelta(days=1),
                "CASH",
                Decimal("888"),
                Decimal("0"),
                0,
                "No",
                context.default_books[0],
            ),
            GLEntrySpec(
                "A04_AFTER_EQUITY",
                context.company,
                context.to_date + timedelta(days=1),
                "EQUITY",
                Decimal("0"),
                Decimal("888"),
                0,
                "No",
                context.default_books[0],
            ),
        ]
        a04_expected = _expected_public(
            context,
            opening=Decimal("105"),
            period=Decimal("116"),
            closing=Decimal("181"),
        )
        a04 = run_case("A04", "inclusive_boundaries", context, years, chart, a04_rows, "ready", a04_expected)
        assert a04 is not None
        self.assertEqual(
            _major_to_minor(Decimal("5"), context.precision),
            a04.leaves["EXPENSE"].opening_debit,
        )

        a05_rows = rows + [
            GLEntrySpec(
                "A05_CASH",
                context.company,
                context.from_date,
                "CASH",
                Decimal("12"),
                Decimal("0"),
                0,
                "Yes",
                context.default_books[0],
            ),
            GLEntrySpec(
                "A05_EQUITY",
                context.company,
                context.from_date,
                "EQUITY",
                Decimal("0"),
                Decimal("12"),
                0,
                "Yes",
                context.default_books[0],
            ),
        ]
        a05_expected = _expected_public(
            context,
            opening=Decimal("112"),
            period=Decimal("100"),
            closing=Decimal("172"),
        )
        a05 = run_case("A05", "balance_sheet_opening_marker", context, years, chart, a05_rows, "ready", a05_expected)
        assert a05 is not None
        self.assertEqual(
            _major_to_minor(Decimal("0"), context.precision),
            a05.leaves["CASH"].period_credit,
        )

        a06_rows = rows + [
            GLEntrySpec(
                "A06_EXPENSE",
                context.company,
                context.from_date,
                "EXPENSE",
                Decimal("1"),
                Decimal("0"),
                0,
                "Yes",
                context.default_books[0],
            )
        ]
        run_case("A06", "pnl_opening_marker", context, years, chart, a06_rows, "deny", _generic_failure())

        a07 = run_case("A07", "hierarchy_and_zero_accounts", context, years, chart, rows, "ready", base_expected)
        assert a07 is not None
        self.assertIn("ZERO_ASSET", a07.leaves)
        self.assertEqual(SixAmounts(), a07.leaves["ZERO_ASSET"])
        self.assertEqual(a07.hierarchy["ASSET_ROOT"], a07.hierarchy["CURRENT_ASSETS"])

        a08_variants: list[tuple[str, list[AccountSpec], list[GLEntrySpec]]] = [
            (
                "orphan",
                [replace(item, parent="MISSING_PARENT") if item.key == "RECEIVABLE" else item for item in chart],
                list(rows),
            ),
            (
                "cycle",
                [replace(item, parent="CURRENT_ASSETS") if item.key == "ASSET_ROOT" else item for item in chart],
                list(rows),
            ),
            ("duplicate", list(chart) + [chart[-1]], list(rows)),
            (
                "cross_company_parent",
                [replace(item, company="COMPANY_B") if item.key == "CURRENT_ASSETS" else item for item in chart],
                list(rows),
            ),
            (
                "group_account_gl",
                list(chart),
                list(rows)
                + [
                    GLEntrySpec(
                        "A08_GROUP",
                        context.company,
                        context.from_date,
                        "CURRENT_ASSETS",
                        Decimal("1"),
                        Decimal("0"),
                        0,
                        "No",
                        context.default_books[0],
                    )
                ],
            ),
        ]
        for variant, case_chart, case_rows in a08_variants:
            run_case("A08", variant, context, years, case_chart, case_rows, "deny", _generic_failure())

        duplicate_pair = [
            GLEntrySpec(
                "A09_CASH_DUP",
                context.company,
                context.from_date,
                "CASH",
                Decimal("3"),
                Decimal("0"),
                0,
                "No",
                context.default_books[0],
            ),
            GLEntrySpec(
                "A09_EQUITY_DUP",
                context.company,
                context.from_date,
                "EQUITY",
                Decimal("0"),
                Decimal("3"),
                0,
                "No",
                context.default_books[0],
            ),
        ]
        a09_expected = _expected_public(
            context,
            opening=Decimal("100"),
            period=Decimal("106"),
            closing=Decimal("166"),
        )
        a09 = run_case(
            "A09",
            "duplicate_rows_additive",
            context,
            years,
            chart,
            rows + duplicate_pair + duplicate_pair,
            "ready",
            a09_expected,
        )
        assert a09 is not None
        self.assertEqual(
            _major_to_minor(Decimal("106"), context.precision),
            a09.gross_totals.period_debit,
        )

        a10_rows = rows + [
            GLEntrySpec(
                "A10_CANCELLED_CASH",
                context.company,
                context.from_date,
                "CASH",
                Decimal("777"),
                Decimal("0"),
                1,
                "No",
                context.default_books[0],
            ),
            GLEntrySpec(
                "A10_CANCELLED_EQUITY",
                context.company,
                context.from_date,
                "EQUITY",
                Decimal("0"),
                Decimal("777"),
                1,
                "No",
                context.default_books[0],
            ),
            GLEntrySpec(
                "A10_CANCELLED_SWAPPED_CASH",
                context.company,
                context.to_date,
                "CASH",
                Decimal("0"),
                Decimal("777"),
                1,
                "No",
                context.default_books[0],
            ),
            GLEntrySpec(
                "A10_CANCELLED_SWAPPED_EQUITY",
                context.company,
                context.to_date,
                "EQUITY",
                Decimal("777"),
                Decimal("0"),
                1,
                "No",
                context.default_books[0],
            ),
        ]
        run_case("A10", "cancelled_poison_excluded", context, years, chart, a10_rows, "ready", base_expected)

        a11_rows = rows + [
            GLEntrySpec(
                "A11_ORIGINAL_CASH",
                context.company,
                context.from_date,
                "CASH",
                Decimal("25"),
                Decimal("0"),
                0,
                "No",
                context.default_books[0],
            ),
            GLEntrySpec(
                "A11_ORIGINAL_EQUITY",
                context.company,
                context.from_date,
                "EQUITY",
                Decimal("0"),
                Decimal("25"),
                0,
                "No",
                context.default_books[0],
            ),
            GLEntrySpec(
                "A11_REVERSAL_CASH",
                context.company,
                context.to_date,
                "CASH",
                Decimal("0"),
                Decimal("25"),
                0,
                "No",
                context.default_books[0],
            ),
            GLEntrySpec(
                "A11_REVERSAL_EQUITY",
                context.company,
                context.to_date,
                "EQUITY",
                Decimal("25"),
                Decimal("0"),
                0,
                "No",
                context.default_books[0],
            ),
        ]
        a11_expected = _expected_public(
            context,
            opening=Decimal("100"),
            period=Decimal("150"),
            closing=Decimal("160"),
        )
        a11 = run_case(
            "A11",
            "active_immutable_reversal",
            context,
            years,
            chart,
            a11_rows,
            "ready",
            a11_expected,
        )
        assert a11 is not None
        self.assertEqual(
            _major_to_minor(Decimal("150"), context.precision),
            a11.gross_totals.period_debit,
        )

        a12_rows = rows + [
            GLEntrySpec(
                "A12_COMPANY_B_DEBIT",
                "COMPANY_B",
                context.from_date,
                "COMPANY_B_ACCOUNT",
                Decimal("999"),
                Decimal("0"),
                0,
                "No",
                context.default_books[0],
            ),
            GLEntrySpec(
                "A12_COMPANY_B_CREDIT",
                "COMPANY_B",
                context.from_date,
                "COMPANY_B_EQUITY",
                Decimal("0"),
                Decimal("999"),
                0,
                "No",
                context.default_books[0],
            ),
        ]
        run_case("A12", "company_b_poison", context, years, chart, a12_rows, "ready", base_expected)

        a13_rows = rows + [
            GLEntrySpec(
                "A13_OUTSIDE_CASH",
                context.company,
                context.to_date + timedelta(days=1),
                "CASH",
                Decimal("888"),
                Decimal("0"),
                0,
                "No",
                context.default_books[0],
            ),
            GLEntrySpec(
                "A13_OUTSIDE_EQUITY",
                context.company,
                context.to_date + timedelta(days=1),
                "EQUITY",
                Decimal("0"),
                Decimal("888"),
                0,
                "No",
                context.default_books[0],
            ),
        ]
        run_case("A13", "out_of_period_poison", context, years, chart, a13_rows, "ready", base_expected)

        a14_rows = list(rows)
        for suffix, book in (
            ("NULL", None),
            ("BLANK", ""),
            ("DEFAULT", context.default_books[0]),
        ):
            a14_rows.extend(
                [
                    GLEntrySpec(
                        f"A14_{suffix}_CASH",
                        context.company,
                        context.from_date,
                        "CASH",
                        Decimal("2"),
                        Decimal("0"),
                        0,
                        "No",
                        book,
                    ),
                    GLEntrySpec(
                        f"A14_{suffix}_EQUITY",
                        context.company,
                        context.from_date,
                        "EQUITY",
                        Decimal("0"),
                        Decimal("2"),
                        0,
                        "No",
                        book,
                    ),
                ]
            )
        for suffix, book in (("ALTERNATE", "BOOK_ALTERNATE"), ("WHITESPACE", " ")):
            a14_rows.extend(
                [
                    GLEntrySpec(
                        f"A14_{suffix}_CASH",
                        context.company,
                        context.from_date,
                        "CASH",
                        Decimal("777"),
                        Decimal("0"),
                        0,
                        "No",
                        book,
                    ),
                    GLEntrySpec(
                        f"A14_{suffix}_EQUITY",
                        context.company,
                        context.from_date,
                        "EQUITY",
                        Decimal("0"),
                        Decimal("777"),
                        0,
                        "No",
                        book,
                    ),
                ]
            )
        a14_expected = _expected_public(
            context,
            opening=Decimal("100"),
            period=Decimal("106"),
            closing=Decimal("166"),
        )
        run_case("A14", "default_null_blank_exact", context, years, chart, a14_rows, "ready", a14_expected)

        run_case(
            "A15",
            "missing_default",
            replace(context, default_books=()),
            years,
            chart,
            rows,
            "deny",
            _generic_failure(),
        )
        run_case(
            "A15",
            "ambiguous_default",
            replace(context, default_books=("BOOK_DEFAULT", "BOOK_OTHER")),
            years,
            chart,
            rows,
            "deny",
            _generic_failure(),
        )
        try:
            _assert_book_cohort_equality({"ROW_NULL", "ROW_DEFAULT"}, {"ROW_DEFAULT"})
            divergence_decision, divergence_actual = "ready", {"cohort": "equal"}
        except ProofUnavailable:
            divergence_decision, divergence_actual = "deny", _generic_failure()
        seen.add("A15")
        self._record_case(
            fixture_id="A15",
            variant="opening_movement_cohort_divergence",
            family="accounting",
            expected_decision="deny",
            expected=_generic_failure(),
            actual_decision=divergence_decision,
            actual=divergence_actual,
            accessor_calls=0,
        )

        short_context = replace(
            context,
            from_date=self.env.fiscal_start,
            to_date=self.env.fiscal_end,
        )
        short_rows = [
            GLEntrySpec(
                "A16_SHORT_CASH",
                context.company,
                self.env.fiscal_start,
                "CASH",
                Decimal("10"),
                Decimal("0"),
                0,
                "No",
                context.default_books[0],
            ),
            GLEntrySpec(
                "A16_SHORT_EQUITY",
                context.company,
                self.env.fiscal_start,
                "EQUITY",
                Decimal("0"),
                Decimal("10"),
                0,
                "No",
                context.default_books[0],
            ),
        ]
        a16_expected = _expected_public(
            short_context,
            opening=Decimal("0"),
            period=Decimal("10"),
            closing=Decimal("10"),
        )
        run_case("A16", "short_year_exact_boundaries", short_context, years, chart, short_rows, "ready", a16_expected)
        overlapping_years = list(years) + [replace(years[0], key="FY_OVERLAP")]
        run_case("A16", "overlapping_years", context, overlapping_years, chart, rows, "deny", _generic_failure())
        run_case(
            "A16",
            "cross_year",
            replace(context, to_date=self.env.fiscal_end + timedelta(days=1)),
            years,
            chart,
            rows,
            "deny",
            _generic_failure(),
        )
        run_case(
            "A16",
            "inverted",
            replace(context, from_date=context.to_date, to_date=context.from_date),
            years,
            chart,
            rows,
            "deny",
            _generic_failure(),
        )

        one_minor = Decimal(1).scaleb(-context.precision)
        a17_rows = rows + [
            GLEntrySpec(
                "A17_ONE_MINOR",
                context.company,
                context.from_date,
                "CASH",
                one_minor,
                Decimal("0"),
                0,
                "No",
                context.default_books[0],
            )
        ]
        run_case("A17", "one_minor_imbalance", context, years, chart, a17_rows, "deny", _generic_failure())

        malformed_date_row = GLEntrySpec(
            "A18_BAD_DATE",
            context.company,
            "not-a-date",  # type: ignore[arg-type]
            "CASH",
            Decimal("1"),
            Decimal("0"),
            0,
            "No",
            context.default_books[0],
        )
        a18_variants = [
            (
                "negative",
                GLEntrySpec(
                    "A18_NEGATIVE",
                    context.company,
                    context.from_date,
                    "CASH",
                    Decimal("-1"),
                    Decimal("0"),
                    0,
                    "No",
                    context.default_books[0],
                ),
            ),
            (
                "non_finite",
                GLEntrySpec(
                    "A18_NAN",
                    context.company,
                    context.from_date,
                    "CASH",
                    Decimal("NaN"),
                    Decimal("0"),
                    0,
                    "No",
                    context.default_books[0],
                ),
            ),
            (
                "excess_scale",
                GLEntrySpec(
                    "A18_SCALE",
                    context.company,
                    context.from_date,
                    "CASH",
                    Decimal(1).scaleb(-(context.precision + 1)),
                    Decimal("0"),
                    0,
                    "No",
                    context.default_books[0],
                ),
            ),
            ("malformed_date", malformed_date_row),
            (
                "missing_account",
                GLEntrySpec(
                    "A18_MISSING_ACCOUNT",
                    context.company,
                    context.from_date,
                    "MISSING_ACCOUNT",
                    Decimal("1"),
                    Decimal("0"),
                    0,
                    "No",
                    context.default_books[0],
                ),
            ),
            (
                "wrong_company_account",
                GLEntrySpec(
                    "A18_WRONG_COMPANY_ACCOUNT",
                    context.company,
                    context.from_date,
                    "COMPANY_B_ACCOUNT",
                    Decimal("1"),
                    Decimal("0"),
                    0,
                    "No",
                    context.default_books[0],
                ),
            ),
        ]
        for variant, bad_row in a18_variants:
            run_case("A18", variant, context, years, chart, rows + [bad_row], "deny", _generic_failure())

        a19_rows = rows + [
            GLEntrySpec(
                "A19_PCV_REVENUE",
                context.company,
                context.from_date,
                "REVENUE",
                Decimal("4"),
                Decimal("0"),
                0,
                "No",
                context.default_books[0],
                source_class="period_closing_voucher_raw_gl",
            ),
            GLEntrySpec(
                "A19_PCV_EQUITY",
                context.company,
                context.from_date,
                "EQUITY",
                Decimal("0"),
                Decimal("4"),
                0,
                "No",
                context.default_books[0],
                source_class="period_closing_voucher_raw_gl",
            ),
        ]
        a19_expected = _expected_public(
            context,
            opening=Decimal("100"),
            period=Decimal("104"),
            closing=Decimal("160"),
        )
        a19 = run_case("A19", "active_pcv_raw_gl", context, years, chart, a19_rows, "ready", a19_expected)
        assert a19 is not None
        self.assertEqual(0, a19.acb_accessor_calls)
        self.assertEqual(0, a19.pcv_accessor_calls)

        poison_state = {
            "account_closing_balance_generation": "poison",
            "process_period_closing_voucher_generation": "poison",
        }
        self.assertNotIn("state", CANDIDATE)
        self.assertTrue(poison_state)
        a20 = run_case("A20", "acb_pcv_state_no_effect", context, years, chart, rows, "ready", base_expected)
        assert a20 is not None
        self.assertEqual(0, a20.acb_accessor_calls)
        self.assertEqual(0, a20.pcv_accessor_calls)

        a21_rows = list(rows) + [
            GLEntrySpec(
                "A21_PRIOR_CASH",
                context.company,
                context.from_date - timedelta(days=1),
                "CASH",
                Decimal("11"),
                Decimal("0"),
                0,
                "No",
                context.default_books[0],
            ),
            GLEntrySpec(
                "A21_PRIOR_PAYABLE",
                context.company,
                context.from_date - timedelta(days=1),
                "PAYABLE",
                Decimal("0"),
                Decimal("11"),
                0,
                "No",
                context.default_books[0],
            ),
            GLEntrySpec(
                "A21_MOVE_CASH",
                context.company,
                context.from_date,
                "CASH",
                Decimal("7"),
                Decimal("0"),
                0,
                "No",
                context.default_books[0],
            ),
            GLEntrySpec(
                "A21_MOVE_PAYABLE",
                context.company,
                context.from_date,
                "PAYABLE",
                Decimal("0"),
                Decimal("7"),
                0,
                "No",
                context.default_books[0],
            ),
        ]
        a21_expected = _expected_public(
            context,
            opening=Decimal("111"),
            period=Decimal("107"),
            closing=Decimal("178"),
        )
        a21 = run_case(
            "A21",
            "leaf_root_liability_signed_equations",
            context,
            years,
            chart,
            a21_rows,
            "ready",
            a21_expected,
        )
        assert a21 is not None
        gross = a21.gross_totals
        self.assertEqual(gross.opening_debit, gross.opening_credit)
        self.assertEqual(gross.period_debit, gross.period_credit)
        self.assertEqual(gross.closing_debit, gross.closing_credit)
        self.assertEqual(
            gross.opening_debit - gross.opening_credit + gross.period_debit - gross.period_credit,
            gross.closing_net,
        )
        self.assertEqual(
            _major_to_minor(Decimal("18"), context.precision),
            a21.leaves["PAYABLE"].closing_credit,
        )
        self.assertEqual(
            a21.hierarchy["PAYABLE"], a21.hierarchy["LIABILITY_ROOT"]
        )

        a22 = run_case("A22", "aggregate_only_serialization", context, years, chart, rows, "ready", base_expected)
        assert a22 is not None
        public = serialize_public_success(a22, context)
        self.assertEqual(0, self.canaries.scan_value(public))
        poisoned_public = dict(public)
        poisoned_public["account"] = "IDENTITY"
        with self.assertRaises(ProofUnavailable):
            _assert_public_key_containment(poisoned_public)

        self.assertEqual(set(ACCOUNTING_IDS), seen)

    def test_30_primary_snapshot_concurrency_and_reconnect_catalog(self) -> None:
        base_context = _base_context(
            self.env, self.base_names.company_a, self.base_names.book_default
        )
        base_expected = _expected_public(
            base_context,
            opening=Decimal("100"),
            period=Decimal("100"),
            closing=Decimal("160"),
        )
        baseline_reader = DatabaseProofReader(
            self.env,
            company=self.base_names.company_a,
            actor=self.base_names.actor,
        )
        baseline_public, baseline_result, baseline_ids = baseline_reader.run()
        self.assertIsNotNone(baseline_result)
        self._record_case(
            fixture_id="A01",
            variant="database_primary_snapshot",
            family="accounting",
            expected_decision="ready",
            expected=base_expected,
            actual_decision="ready" if baseline_result is not None else "deny",
            actual=baseline_public,
            accessor_calls=(
                baseline_result.account_accessor_calls + baseline_result.gl_accessor_calls
                if baseline_result is not None
                else 0
            ),
            connection_ids=baseline_ids,
        )

        def seed(scope: str) -> FixtureNames:
            names = _fixture_names(self.env, scope)
            _seed_database_scope(self.env, self.mutations, names, self.canaries)
            return names

        pcv_names = seed("A19_DB")
        _insert_gl_entry(
            self.env,
            self.mutations,
            pcv_names,
            suffix="A19_PCV_REVENUE",
            account_key="REVENUE",
            debit=Decimal("4"),
            credit=Decimal("0"),
            posting_date=self.env.from_date,
            voucher_type="Period Closing Voucher",
            voucher_no=f"SYNTH_{self.env.run_id}_{pcv_names.scope}_PCV",
        )
        _insert_gl_entry(
            self.env,
            self.mutations,
            pcv_names,
            suffix="A19_PCV_EQUITY",
            account_key="EQUITY",
            debit=Decimal("0"),
            credit=Decimal("4"),
            posting_date=self.env.from_date,
            voucher_type="Period Closing Voucher",
            voucher_no=f"SYNTH_{self.env.run_id}_{pcv_names.scope}_PCV",
        )
        self.mutations.commit()
        pcv_context = _base_context(
            self.env, pcv_names.company_a, pcv_names.book_default
        )
        pcv_expected = _expected_public(
            pcv_context,
            opening=Decimal("100"),
            period=Decimal("104"),
            closing=Decimal("160"),
        )
        pcv_reader = DatabaseProofReader(
            self.env, company=pcv_names.company_a, actor=pcv_names.actor
        )
        pcv_public, pcv_result, pcv_ids = pcv_reader.run()
        self.assertIsNotNone(pcv_result)
        self._record_case(
            fixture_id="A19",
            variant="database_pcv_origin_raw_gl",
            family="accounting",
            expected_decision="ready",
            expected=pcv_expected,
            actual_decision="ready" if pcv_result is not None else "deny",
            actual=pcv_public,
            accessor_calls=(
                pcv_result.account_accessor_calls + pcv_result.gl_accessor_calls
                if pcv_result is not None
                else 0
            ),
            connection_ids=pcv_ids,
        )

        cases: list[
            tuple[
                str,
                str,
                str,
                Callable[[FixtureNames], None],
                Mapping[str, Any],
                Callable[[ReconstructionResult | None], Mapping[str, Any]],
            ]
        ] = []

        def s01_action(names: FixtureNames) -> None:
            _insert_balanced_pair(
                self.env,
                self.mutations,
                names,
                suffix="S01_NEW",
                amount=Decimal("5"),
                posting_date=self.env.from_date,
            )
            self.mutations.commit()

        s01_fresh = _expected_public(
            base_context,
            opening=Decimal("100"),
            period=Decimal("105"),
            closing=Decimal("165"),
        )
        cases.append(
            (
                "S01",
                "balanced_gl_writer",
                "authority",
                s01_action,
                s01_fresh,
                lambda result: {
                    "fresh_leaf_count": len(result.leaves) if result is not None else None,
                    "fresh_gross_period": (
                        _minor_to_major(result.gross_totals.period_debit, self.env.precision)
                        if result is not None
                        else None
                    ),
                },
            )
        )

        def s02_action(names: FixtureNames) -> None:
            group_name = f"SYNTH_{self.env.run_id}_{names.scope}_NEW_ROOT"
            leaf_name = f"SYNTH_{self.env.run_id}_{names.scope}_NEW_LEAF"
            group = _base_row(group_name)
            group.update(
                {
                    "account_name": self.canaries.value("parent_root"),
                    "account_number": self.canaries.value("account_number"),
                    "is_group": 1,
                    "company": names.company_a,
                    "root_type": "Asset",
                    "report_type": "Balance Sheet",
                    "account_currency": self.env.currency,
                    "parent_account": "",
                    "lft": 27,
                    "rgt": 30,
                    "disabled": 0,
                }
            )
            self.mutations.insert("tabAccount", group)
            leaf = _base_row(leaf_name)
            leaf.update(
                {
                    "account_name": self.canaries.value("account_name"),
                    "account_number": self.canaries.value("account_number"),
                    "is_group": 0,
                    "company": names.company_a,
                    "root_type": "Asset",
                    "report_type": "Balance Sheet",
                    "account_currency": self.env.currency,
                    "parent_account": group_name,
                    "lft": 28,
                    "rgt": 29,
                    "disabled": 0,
                }
            )
            self.mutations.insert("tabAccount", leaf)
            self.mutations.commit()

        cases.append(
            (
                "S02",
                "account_tree_writer",
                "authority",
                s02_action,
                base_expected,
                lambda result: {
                    "fresh_leaf_count": len(result.leaves) if result is not None else None,
                    "fresh_gross_period": (
                        _minor_to_major(result.gross_totals.period_debit, self.env.precision)
                        if result is not None
                        else None
                    ),
                },
            )
        )

        def s03_action(names: FixtureNames) -> None:
            row = _base_row(f"SYNTH_{self.env.run_id}_{names.scope}_ACCOUNT_PERMISSION")
            row.update(
                {
                    "user": names.actor,
                    "allow": "Account",
                    "for_value": names.accounts["CASH"],
                    "is_default": 0,
                    "apply_to_all_doctypes": 1,
                    "applicable_for": "",
                    "hide_descendants": 0,
                }
            )
            self.mutations.insert("tabUser Permission", row)
            self.mutations.commit()

        cases.append(
            (
                "S03",
                "authority_writer",
                "authority",
                s03_action,
                _generic_failure(),
                lambda result: {
                    "fresh_leaf_count": len(result.leaves) if result is not None else None,
                    "fresh_gross_period": None,
                },
            )
        )

        def s04_action(names: FixtureNames) -> None:
            self.mutations.update_by_name(
                "tabCompany",
                names.company_a,
                {"default_finance_book": names.book_alternate},
            )
            self.mutations.commit()

        zero_expected = _expected_public(
            base_context,
            opening=Decimal("0"),
            period=Decimal("0"),
            closing=Decimal("0"),
        )
        cases.append(
            (
                "S04",
                "default_book_writer",
                "context",
                s04_action,
                zero_expected,
                lambda result: {
                    "fresh_leaf_count": len(result.leaves) if result is not None else None,
                    "fresh_gross_period": (
                        _minor_to_major(result.gross_totals.period_debit, self.env.precision)
                        if result is not None
                        else None
                    ),
                },
            )
        )

        def s05_action(names: FixtureNames) -> None:
            fiscal_name = f"SYNTH_{self.env.run_id}_{names.scope}_FY_OVERLAP"
            fiscal = _base_row(fiscal_name)
            fiscal.update(
                {
                    "year": fiscal_name,
                    "disabled": 0,
                    "is_short_year": 0,
                    "year_start_date": self.env.fiscal_start.isoformat(),
                    "year_end_date": self.env.fiscal_end.isoformat(),
                    "auto_created": 0,
                }
            )
            self.mutations.insert("tabFiscal Year", fiscal)
            child = _base_row(f"SYNTH_{self.env.run_id}_{names.scope}_FY_OVERLAP_COMPANY")
            child.update(
                {
                    "parent": fiscal_name,
                    "parenttype": "Fiscal Year",
                    "parentfield": "companies",
                    "company": names.company_a,
                }
            )
            self.mutations.insert("tabFiscal Year Company", child)
            self.mutations.commit()

        cases.append(
            (
                "S05",
                "fiscal_writer",
                "fiscal",
                s05_action,
                _generic_failure(),
                lambda result: {
                    "fresh_leaf_count": len(result.leaves) if result is not None else None,
                    "fresh_gross_period": None,
                },
            )
        )

        def s06_action(names: FixtureNames) -> None:
            _insert_balanced_pair(
                self.env,
                self.mutations,
                names,
                suffix="S06_ORIGINAL",
                amount=Decimal("5"),
                posting_date=self.env.from_date,
            )
            _insert_gl_entry(
                self.env,
                self.mutations,
                names,
                suffix="S06_REVERSAL_CASH",
                account_key="CASH",
                debit=Decimal("0"),
                credit=Decimal("5"),
                posting_date=self.env.to_date,
            )
            _insert_gl_entry(
                self.env,
                self.mutations,
                names,
                suffix="S06_REVERSAL_EQUITY",
                account_key="EQUITY",
                debit=Decimal("5"),
                credit=Decimal("0"),
                posting_date=self.env.to_date,
            )
            self.mutations.commit()

        s06_fresh = _expected_public(
            base_context,
            opening=Decimal("100"),
            period=Decimal("110"),
            closing=Decimal("160"),
        )
        cases.append(
            (
                "S06",
                "immutable_reversal_writer",
                "chart",
                s06_action,
                s06_fresh,
                lambda result: {
                    "fresh_leaf_count": len(result.leaves) if result is not None else None,
                    "fresh_gross_period": (
                        _minor_to_major(result.gross_totals.period_debit, self.env.precision)
                        if result is not None
                        else None
                    ),
                },
            )
        )

        def s07_action(names: FixtureNames) -> None:
            self.mutations.insert_minimal(
                "tabAccount Closing Balance",
                f"SYNTH_{self.env.run_id}_{names.scope}_ACB_POISON",
                company=names.company_a,
            )
            self.mutations.insert_minimal(
                "tabProcess Period Closing Voucher",
                f"SYNTH_{self.env.run_id}_{names.scope}_PCV_POISON",
                company=names.company_a,
            )
            self.mutations.commit()

        cases.append(
            (
                "S07",
                "acb_pcv_state_writer",
                "context",
                s07_action,
                base_expected,
                lambda result: {
                    "fresh_leaf_count": len(result.leaves) if result is not None else None,
                    "fresh_gross_period": (
                        _minor_to_major(result.gross_totals.period_debit, self.env.precision)
                        if result is not None
                        else None
                    ),
                },
            )
        )

        def s08_action(names: FixtureNames) -> None:
            _insert_balanced_pair(
                self.env,
                self.mutations,
                names,
                suffix="S08_ROLLBACK",
                amount=Decimal("5"),
                posting_date=self.env.from_date,
            )
            self.mutations.rollback()

        cases.append(
            (
                "S08",
                "writer_rollback",
                "authority",
                s08_action,
                base_expected,
                lambda result: {
                    "fresh_leaf_count": len(result.leaves) if result is not None else None,
                    "fresh_gross_period": (
                        _minor_to_major(result.gross_totals.period_debit, self.env.precision)
                        if result is not None
                        else None
                    ),
                },
            )
        )

        seen: set[str] = set()
        for fixture_id, variant, boundary, action, fresh_expected, fresh_probe in cases:
            with self.subTest(fixture_id=fixture_id):
                seen.add(fixture_id)
                names = seed(fixture_id)
                fired = False

                def hook(name: str, _connection_id: int) -> None:
                    nonlocal fired
                    if name == boundary and not fired:
                        fired = True
                        action(names)

                reader = DatabaseProofReader(
                    self.env,
                    company=names.company_a,
                    actor=names.actor,
                    boundary_hook=hook,
                )
                old_public, old_result, old_ids = reader.run()
                self.assertTrue(fired)
                fresh_reader = DatabaseProofReader(
                    self.env,
                    company=names.company_a,
                    actor=names.actor,
                )
                fresh_public, fresh_result, fresh_ids = fresh_reader.run()
                expected_summary = {
                    "reader_state": "old",
                    "reader_public_sha256": _sha256_bytes(_canonical_json_inline(base_expected)),
                    "fresh_public_sha256": _sha256_bytes(_canonical_json_inline(fresh_expected)),
                    "fresh_probe": (
                        {"fresh_leaf_count": 8, "fresh_gross_period": "100" + ("." + "0" * self.env.precision if self.env.precision else "")}
                        if fixture_id == "S02"
                        else {
                            "fresh_leaf_count": 7 if fixture_id not in {"S03", "S05"} else None,
                            "fresh_gross_period": (
                                None
                                if fixture_id in {"S03", "S05"}
                                else _minor_to_major(
                                    _major_to_minor(
                                        Decimal("105")
                                        if fixture_id == "S01"
                                        else Decimal("110")
                                        if fixture_id == "S06"
                                        else Decimal("0")
                                        if fixture_id == "S04"
                                        else Decimal("100"),
                                        self.env.precision,
                                    ),
                                    self.env.precision,
                                )
                            ),
                        }
                    ),
                    "hybrid": False,
                }
                actual_summary = {
                    "reader_state": "old" if old_public == base_expected and old_result is not None else "other",
                    "reader_public_sha256": _sha256_bytes(_canonical_json_inline(old_public)),
                    "fresh_public_sha256": _sha256_bytes(_canonical_json_inline(fresh_public)),
                    "fresh_probe": dict(fresh_probe(fresh_result)),
                    "hybrid": False,
                }
                self._record_case(
                    fixture_id=fixture_id,
                    variant=variant,
                    family="snapshot",
                    expected_decision="pass",
                    expected=expected_summary,
                    actual_decision="pass",
                    actual=actual_summary,
                    accessor_calls=(
                        (old_result.account_accessor_calls + old_result.gl_accessor_calls)
                        if old_result is not None
                        else 0
                    )
                    + (
                        (fresh_result.account_accessor_calls + fresh_result.gl_accessor_calls)
                        if fresh_result is not None
                        else 0
                    ),
                    connection_ids=(*old_ids, *fresh_ids),
                )
                if fixture_id == "S03":
                    self._record_case(
                        fixture_id="P28",
                        variant="database_authority_generation_snapshot",
                        family="permission",
                        expected_decision="pass",
                        expected=expected_summary,
                        actual_decision="pass",
                        actual=actual_summary,
                        accessor_calls=(
                            (old_result.account_accessor_calls + old_result.gl_accessor_calls)
                            if old_result is not None
                            else 0
                        ),
                        connection_ids=(*old_ids, *fresh_ids),
                    )
                if fixture_id == "S07" and fresh_result is not None:
                    self.assertEqual(0, fresh_result.acb_accessor_calls)
                    self.assertEqual(0, fresh_result.pcv_accessor_calls)
        self.assertEqual(set(SNAPSHOT_IDS), seen)

        p27_names = seed("P27")
        injected = False

        def integrity_failure_hook(name: str, _connection_id: int) -> None:
            nonlocal injected
            if name == "validation" and not injected:
                injected = True
                _fail()

        p27_reader = DatabaseProofReader(
            self.env,
            company=p27_names.company_a,
            actor=p27_names.actor,
            boundary_hook=integrity_failure_hook,
        )
        p27_public, p27_result, p27_ids = p27_reader.run()
        self.assertTrue(injected)
        if p27_result is not None or p27_reader.serialized_bytes is not None:
            _fail()
        self._require_public_equivalence(_generic_failure(), p27_public)
        self._record_case(
            fixture_id="P27",
            variant="database_post_read_integrity_failure",
            family="permission",
            expected_decision="deny",
            expected=_generic_failure(),
            actual_decision="deny",
            actual=p27_public,
            accessor_calls=p27_reader.access.account + p27_reader.access.gl,
            connection_ids=p27_ids,
        )

        reconnect_retry_observations: list[int] = []
        reconnect_fallback_observations: list[int] = []
        for index, boundary in enumerate(RECONNECT_BOUNDARIES, start=1):
            with self.subTest(reconnect_boundary=boundary):
                names = seed(f"R{index:02d}")
                fired = False

                def kill_hook(name: str, connection_id: int) -> None:
                    nonlocal fired
                    if name == boundary and not fired:
                        fired = True
                        _kill_synthetic_reader(self.env, connection_id)

                reader = DatabaseProofReader(
                    self.env,
                    company=names.company_a,
                    actor=names.actor,
                    boundary_hook=kill_hook,
                )
                public, result, connection_ids = reader.run()
                reconnect_retry_observations.append(
                    reader.metrics.get("reconnect_retries", -1)
                )
                reconnect_fallback_observations.append(
                    reader.metrics.get("fallback_host_attempts", -1)
                )
                self.assertTrue(fired)
                if result is not None or reader.serialized_bytes is not None:
                    _fail()
                self._require_public_equivalence(_generic_failure(), public)
                self._record_case(
                    fixture_id=f"R{index:02d}",
                    variant=f"connection_killed_after_{boundary}",
                    family="snapshot",
                    expected_decision="deny",
                    expected=_generic_failure(),
                    actual_decision="deny",
                    actual=public,
                    accessor_calls=0,
                    connection_ids=connection_ids,
                )
        if any(value < 0 for value in reconnect_retry_observations):
            _fail()
        if any(value < 0 for value in reconnect_fallback_observations):
            _fail()
        self.__class__.reconnect_retry_observations = tuple(
            reconnect_retry_observations
        )
        self.__class__.reconnect_fallback_observations = tuple(
            reconnect_fallback_observations
        )

    def test_40_workload_caps_timeouts_and_no_partial_contract(self) -> None:
        if {point["cache_state_code"] for point in self.workload_plan.candidate_points} != {0, 1}:
            _fail()
        if self.containment.candidate_cache_surface_count != 0:
            _fail()

        benchmark_records: list[dict[str, Any]] = []
        for index, point in enumerate(self.workload_plan.candidate_points, start=1):
            with self.subTest(workload_point=index):
                if point["active_dimensions"] != 0:
                    _fail()
                names, context, expected_success, manifest, setup_ms = (
                    _seed_workload_database_scope(
                        self.env,
                        self.mutations,
                        scope=f"W{index:04d}",
                        point=point,
                        canaries=self.canaries,
                    )
                )
                expected_bytes = len(_canonical_json_inline(expected_success))
                if point["response_bytes"] != expected_bytes:
                    _fail()

                def make_reader(
                    *,
                    capture_plan: bool,
                    candidate_limits: Mapping[str, int] | None = None,
                ) -> DatabaseProofReader:
                    return DatabaseProofReader(
                        self.env,
                        company=names.company_a,
                        actor=names.actor,
                        request_from_date=context.from_date,
                        request_to_date=context.to_date,
                        candidate_limits=candidate_limits,
                        capture_query_plan=capture_plan,
                    )

                if point["cache_state_code"] == 1:
                    warm_reader = make_reader(capture_plan=False)
                    warm_public, warm_result, _warm_ids = warm_reader.run()
                    self.assertIsNotNone(warm_result)
                    self._require_public_equivalence(expected_success, warm_public)

                readers: list[DatabaseProofReader] = []
                barrier = threading.Barrier(point["concurrent_readers"])

                def read_one(reader_index: int) -> tuple[
                    DatabaseProofReader,
                    dict[str, Any],
                    ReconstructionResult | None,
                    tuple[int, ...],
                ]:
                    reader = make_reader(capture_plan=reader_index == 0)
                    barrier.wait()
                    public, result, ids = reader.run()
                    return reader, public, result, ids

                tracemalloc.start()
                try:
                    with ThreadPoolExecutor(
                        max_workers=point["concurrent_readers"]
                    ) as executor:
                        futures = [
                            executor.submit(read_one, reader_index)
                            for reader_index in range(point["concurrent_readers"])
                        ]
                        completed = [future.result() for future in futures]
                    current_bytes, peak_bytes = tracemalloc.get_traced_memory()
                finally:
                    tracemalloc.stop()

                all_connection_ids: list[int] = []
                for reader, public, result, connection_ids in completed:
                    readers.append(reader)
                    all_connection_ids.extend(connection_ids)
                    self.assertIsNotNone(result)
                    self._require_public_equivalence(expected_success, public)
                    self.assertEqual(expected_bytes, reader.candidate_serialized_size)
                    self.assertIsNotNone(reader.serialized_bytes)

                first_reader, first_public, first_result, _first_ids = completed[0]
                self._record_case(
                    fixture_id=f"W{index:02d}",
                    variant=(
                        "database_first_candidate_read_fresh_scope"
                        if point["cache_state_code"] == 0
                        else "database_repeat_candidate_read_same_scope"
                    ),
                    family="workload",
                    expected_decision="ready",
                    expected=expected_success,
                    actual_decision="ready" if first_result is not None else "deny",
                    actual=first_public,
                    accessor_calls=sum(
                        reader.access.account + reader.access.gl for reader in readers
                    ),
                    connection_ids=all_connection_ids,
                )
                process_bytes = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
                observation = {
                    "request_latency_ms": max(
                        reader.metrics.get("request_latency_ms", 0) for reader in readers
                    ),
                    "statement_duration_ms": max(
                        reader.metrics.get("statement_duration_ms", 0) for reader in readers
                    ),
                    "process_memory_bytes": max(process_bytes, peak_bytes),
                    "examined_database_rows": max(
                        reader.metrics.get("examined_database_rows", 0) for reader in readers
                    ),
                    "internal_chart_accounts": point["accounts"],
                    "internal_gl_rows": point["eligible_gl_rows"] + point["poison_gl_rows"],
                    "serialized_utf8_bytes": max(
                        reader.candidate_serialized_size or 0 for reader in readers
                    ),
                    "concurrent_readers": len(readers),
                    "setup_fixture_ms": setup_ms,
                    "reconnect_retries": max(
                        reader.metrics.get("reconnect_retries", 0) for reader in readers
                    ),
                }
                classification = _classify_workload_observation(
                    observation, self.workload_plan
                )
                exceeded_keys = _workload_exceeded_keys(
                    observation, self.workload_plan
                )
                if (classification == "observed_within_budget") != (not exceeded_keys):
                    _fail()
                benchmark_records.append(
                    {
                        "point": dict(point),
                        "names": names,
                        "context": context,
                        "expected": expected_success,
                        "expected_bytes": expected_bytes,
                        "observation": observation,
                        "classification": classification,
                        "exceeded_budget_keys": exceeded_keys,
                    }
                )
                self.evidence.append_jsonl(
                    "workload-results.jsonl",
                    {
                        "record_type": "database_benchmark_observation",
                        "fixture_id": f"W{index:02d}",
                        "candidate": CANDIDATE,
                        "cache_state": (
                            "first_candidate_read_fresh_scope_no_candidate_cache"
                            if point["cache_state_code"] == 0
                            else "repeat_candidate_read_no_candidate_cache"
                        ),
                        "candidate_cache_surface_count": self.containment.candidate_cache_surface_count,
                        "input_manifest_sha256": _sha256_bytes(
                            _canonical_json_inline(manifest)
                        ),
                        "query_plan_sha256": first_reader.query_plan_sha256,
                        "query_plan_estimated_rows": first_reader.query_plan_estimated_rows,
                        "query_plan_structure": (
                            list(first_reader.query_plan_structure)
                            if first_reader.query_plan_structure is not None
                            else None
                        ),
                        "statement_count": max(
                            reader.metrics.get("statement_count", 0) for reader in readers
                        ),
                        "observation": observation,
                        "budget_classification": classification,
                        "exceeded_budget_keys": list(exceeded_keys),
                        "current_traced_bytes": current_bytes,
                        "candidate_limits_sha256": None,
                        "numeric_caps_approved": False,
                    },
                )

        public_output_rows = len(
            [key for key in ("opening", "period", "closing") if key in _expected_public(
                _base_context(self.env, "SCOPE", "BOOK"),
                opening=Decimal("0"),
                period=Decimal("0"),
                closing=Decimal("0"),
            )]
        )
        passing = [
            record
            for record in benchmark_records
            if record["classification"] == "observed_within_budget"
        ]
        failing = [
            record
            for record in benchmark_records
            if record["classification"] == "observed_over_budget"
        ]
        if not passing or not failing:
            _fail()

        grouped_records: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
        for record in benchmark_records:
            grouped_records[
                (record["point"]["series_code"], record["point"]["step"])
            ].append(record)

        selected_envelopes: dict[str, list[dict[str, Any]]] = {}
        first_failing_envelopes: dict[str, list[dict[str, Any]]] = {}
        for series_code, cap_name in WORKLOAD_SERIES_CAPS.items():
            steps = sorted(step for series, step in grouped_records if series == series_code)
            envelopes = [grouped_records[(series_code, step)] for step in steps]
            for envelope in envelopes:
                if {record["point"]["variant_code"] for record in envelope} != WORKLOAD_VARIANT_CODES:
                    _fail()
            statuses = [
                all(
                    record["classification"] == "observed_within_budget"
                    for record in envelope
                )
                for envelope in envelopes
            ]
            try:
                first_failure_index = statuses.index(False)
            except ValueError:
                _fail()
            if first_failure_index == 0 or any(statuses[first_failure_index:]):
                _fail()
            selected_envelopes[cap_name] = envelopes[first_failure_index - 1]
            first_failing_envelopes[cap_name] = envelopes[first_failure_index]
            target_budget = WORKLOAD_SERIES_TARGET_BUDGETS.get(series_code)
            if target_budget is not None and not any(
                target_budget in record["exceeded_budget_keys"]
                for record in envelopes[first_failure_index]
            ):
                _fail()

        def envelope_value(cap_name: str, envelope: Sequence[Mapping[str, Any]]) -> int:
            if cap_name == "MAX_ACCOUNTS":
                return max(record["point"]["accounts"] for record in envelope)
            if cap_name == "MAX_PERIOD_DAYS":
                return max(record["point"]["period_days"] for record in envelope)
            if cap_name == "MAX_RESPONSE_BYTES":
                return max(record["expected_bytes"] for record in envelope)
            if cap_name == "STATEMENT_TIMEOUT_MS":
                return max(
                    record["observation"]["statement_duration_ms"]
                    for record in envelope
                )
            if cap_name == "REQUEST_TIMEOUT_MS":
                return max(
                    record["observation"]["request_latency_ms"]
                    for record in envelope
                )
            _fail()

        for cap_name in WORKLOAD_SERIES_CAPS.values():
            if envelope_value(
                cap_name, selected_envelopes[cap_name]
            ) >= envelope_value(cap_name, first_failing_envelopes[cap_name]):
                _fail()

        selected_records = [
            record
            for cap_name in WORKLOAD_SERIES_CAPS.values()
            for record in selected_envelopes[cap_name]
        ]
        limits = {
            "MAX_ACCOUNTS": envelope_value(
                "MAX_ACCOUNTS", selected_envelopes["MAX_ACCOUNTS"]
            ),
            "MAX_PERIOD_DAYS": envelope_value(
                "MAX_PERIOD_DAYS", selected_envelopes["MAX_PERIOD_DAYS"]
            ),
            "MAX_OUTPUT_ROWS": public_output_rows,
            "MAX_RESPONSE_BYTES": envelope_value(
                "MAX_RESPONSE_BYTES", selected_envelopes["MAX_RESPONSE_BYTES"]
            ),
            "STATEMENT_TIMEOUT_MS": envelope_value(
                "STATEMENT_TIMEOUT_MS", selected_envelopes["STATEMENT_TIMEOUT_MS"]
            ),
            "REQUEST_TIMEOUT_MS": envelope_value(
                "REQUEST_TIMEOUT_MS", selected_envelopes["REQUEST_TIMEOUT_MS"]
            ),
            "MAX_RETRIES": max(
                record["observation"]["reconnect_retries"]
                for record in selected_records
            ),
        }
        if set(limits) != set(DERIVED_CAP_NAMES):
            _fail()
        if any(
            limits[key] <= 0 for key in DERIVED_CAP_NAMES if key != "MAX_RETRIES"
        ) or limits["MAX_RETRIES"] != 0:
            _fail()
        if (
            limits["MAX_ACCOUNTS"] + 1
            > self.workload_plan.safety_envelope["accounts"]
            or limits["MAX_PERIOD_DAYS"] + 1
            > self.workload_plan.safety_envelope["period_days"]
            or self.workload_plan.safety_envelope["fault_delay_ms"]
            <= max(limits["STATEMENT_TIMEOUT_MS"], limits["REQUEST_TIMEOUT_MS"])
        ):
            _fail()
        self.evidence.append_jsonl(
            "workload-results.jsonl",
            {
                "record_type": "benchmark_derived_candidate_limits",
                "candidate": CANDIDATE,
                "derivation": "last_all_variant_pass_before_first_nonpassing_monotonic_envelope",
                "limits": limits,
                "selected_first_repeat_concurrent_point_hashes": [
                    _sha256_bytes(_canonical_json_inline(record["point"]))
                    for record in selected_records
                ],
                "first_failing_envelope_hashes": {
                    cap_name: [
                        _sha256_bytes(_canonical_json_inline(record["point"]))
                        for record in first_failing_envelopes[cap_name]
                    ]
                    for cap_name in WORKLOAD_SERIES_CAPS.values()
                },
                "numeric_caps_approved": False,
            },
        )

        axis_fields = {
            "MAX_ACCOUNTS": "accounts",
            "MAX_PERIOD_DAYS": "period_days",
        }
        for cap_name, point_field in axis_fields.items():
            for label, target, expected_ready in (
                ("limit_minus_one", limits[cap_name] - 1, True),
                ("exact_limit", limits[cap_name], True),
                ("limit_plus_one", limits[cap_name] + 1, False),
            ):
                candidates = [
                    record
                    for record in benchmark_records
                    if record["point"]["series_code"]
                    == next(
                        series
                        for series, mapped_cap in WORKLOAD_SERIES_CAPS.items()
                        if mapped_cap == cap_name
                    )
                    and record["point"][point_field] == target
                    and record["point"]["variant_code"] == 1
                    and (
                        cap_name == "MAX_ACCOUNTS"
                        or record["point"]["accounts"] <= limits["MAX_ACCOUNTS"]
                    )
                    and (
                        cap_name == "MAX_PERIOD_DAYS"
                        or record["point"]["period_days"] <= limits["MAX_PERIOD_DAYS"]
                    )
                    and (
                        cap_name == "MAX_RESPONSE_BYTES"
                        or record["expected_bytes"] <= limits["MAX_RESPONSE_BYTES"]
                    )
                ]
                if not candidates:
                    _fail()
                selected = candidates[0]
                reader = DatabaseProofReader(
                    self.env,
                    company=selected["names"].company_a,
                    actor=selected["names"].actor,
                    request_from_date=selected["context"].from_date,
                    request_to_date=selected["context"].to_date,
                    candidate_limits=limits,
                )
                public, result, connection_ids = reader.run()
                self.assertEqual(expected_ready, result is not None)
                self._require_public_equivalence(
                    selected["expected"] if expected_ready else _generic_failure(),
                    public,
                )
                if not expected_ready and reader.serialized_bytes is not None:
                    _fail()
                self._record_case(
                    fixture_id=f"WB_{cap_name}",
                    variant=label,
                    family="workload",
                    expected_decision="ready" if expected_ready else "deny",
                    expected=(
                        selected["expected"] if expected_ready else _generic_failure()
                    ),
                    actual_decision="ready" if result is not None else "deny",
                    actual=public,
                    accessor_calls=reader.access.account + reader.access.gl,
                    connection_ids=connection_ids,
                )

        output_scope = next(
            record
            for record in passing
            if record["point"]["accounts"] <= limits["MAX_ACCOUNTS"]
            and record["point"]["period_days"] <= limits["MAX_PERIOD_DAYS"]
            and record["expected_bytes"] <= limits["MAX_RESPONSE_BYTES"]
        )
        for label, output_limit, expected_ready in (
            ("actual_limit_plus_one", public_output_rows - 1, False),
            ("exact_limit", public_output_rows, True),
            ("actual_limit_minus_one", public_output_rows + 1, True),
        ):
            output_limits = dict(limits)
            output_limits["MAX_OUTPUT_ROWS"] = output_limit
            reader = DatabaseProofReader(
                self.env,
                company=output_scope["names"].company_a,
                actor=output_scope["names"].actor,
                request_from_date=output_scope["context"].from_date,
                request_to_date=output_scope["context"].to_date,
                candidate_limits=output_limits,
            )
            public, result, connection_ids = reader.run()
            self.assertEqual(expected_ready, result is not None)
            self._require_public_equivalence(
                output_scope["expected"] if expected_ready else _generic_failure(),
                public,
            )
            self._record_case(
                fixture_id="WB_MAX_OUTPUT_ROWS",
                variant=label,
                family="workload",
                expected_decision="ready" if expected_ready else "deny",
                expected=(
                    output_scope["expected"] if expected_ready else _generic_failure()
                ),
                actual_decision="ready" if result is not None else "deny",
                actual=public,
                accessor_calls=reader.access.account + reader.access.gl,
                connection_ids=connection_ids,
            )

        fault_names = output_scope["names"]
        fault_context = output_scope["context"]
        fault_expected = output_scope["expected"]
        expected_size = len(_canonical_json_inline(fault_expected))
        for label, response_cap, expected_ready in (
            ("response_cap_limit_minus_one", expected_size - 1, False),
            ("response_cap_exact_limit", expected_size, True),
            ("response_cap_limit_plus_one", expected_size + 1, True),
        ):
            response_limits = dict(limits)
            response_limits["MAX_RESPONSE_BYTES"] = response_cap
            response_reader = DatabaseProofReader(
                self.env,
                company=fault_names.company_a,
                actor=fault_names.actor,
                request_from_date=fault_context.from_date,
                request_to_date=fault_context.to_date,
                candidate_limits=response_limits,
            )
            response_public, response_result, response_ids = response_reader.run()
            self.assertEqual(expected_ready, response_result is not None)
            self.assertEqual(expected_size, response_reader.candidate_serialized_size)
            self._require_public_equivalence(
                fault_expected if expected_ready else _generic_failure(),
                response_public,
            )
            if not expected_ready and response_reader.serialized_bytes is not None:
                _fail()
            self._record_case(
                fixture_id="WB_MAX_RESPONSE_BYTES",
                variant=label,
                family="workload",
                expected_decision="ready" if expected_ready else "deny",
                expected=fault_expected if expected_ready else _generic_failure(),
                actual_decision="ready" if response_result is not None else "deny",
                actual=response_public,
                accessor_calls=response_reader.access.account + response_reader.access.gl,
                connection_ids=response_ids,
            )

        delay_ms = self.workload_plan.safety_envelope["fault_delay_ms"]
        timeout_reader = DatabaseProofReader(
            self.env,
            company=fault_names.company_a,
            actor=fault_names.actor,
            request_from_date=fault_context.from_date,
            request_to_date=fault_context.to_date,
            candidate_limits=limits,
            statement_delay_ms=delay_ms,
        )
        timeout_public, timeout_result, timeout_ids = timeout_reader.run()
        if timeout_result is not None or timeout_reader.serialized_bytes is not None:
            _fail()
        if timeout_reader.metrics.get("statement_timeouts") != 1:
            _fail()
        self._require_public_equivalence(_generic_failure(), timeout_public)
        self._record_case(
            fixture_id="WF01",
            variant="database_statement_timeout",
            family="workload",
            expected_decision="deny",
            expected=_generic_failure(),
            actual_decision="deny",
            actual=timeout_public,
            accessor_calls=timeout_reader.access.account + timeout_reader.access.gl,
            connection_ids=timeout_ids,
        )

        request_delay_fired = False

        def request_timeout_hook(name: str, _connection_id: int) -> None:
            nonlocal request_delay_fired
            if name == "context" and not request_delay_fired:
                request_delay_fired = True
                time.sleep(delay_ms / 1000)

        request_reader = DatabaseProofReader(
            self.env,
            company=fault_names.company_a,
            actor=fault_names.actor,
            request_from_date=fault_context.from_date,
            request_to_date=fault_context.to_date,
            candidate_limits=limits,
            boundary_hook=request_timeout_hook,
        )
        request_public, request_result, request_ids = request_reader.run()
        self.assertTrue(request_delay_fired)
        if request_result is not None or request_reader.serialized_bytes is not None:
            _fail()
        self._require_public_equivalence(_generic_failure(), request_public)
        self._record_case(
            fixture_id="WF01",
            variant="database_request_timeout",
            family="workload",
            expected_decision="deny",
            expected=_generic_failure(),
            actual_decision="deny",
            actual=request_public,
            accessor_calls=request_reader.access.account + request_reader.access.gl,
            connection_ids=request_ids,
        )

        for variant, boundary in (
            ("query_stage_failure", "opening"),
            ("rollup_stage_failure", "hierarchy"),
            ("invariant_stage_failure", "validation"),
            ("serialization_stage_failure", "serialization"),
        ):
            injected = False

            def failure_hook(name: str, _connection_id: int) -> None:
                nonlocal injected
                if name == boundary and not injected:
                    injected = True
                    _fail()

            reader = DatabaseProofReader(
                self.env,
                company=fault_names.company_a,
                actor=fault_names.actor,
                request_from_date=fault_context.from_date,
                request_to_date=fault_context.to_date,
                candidate_limits=limits,
                boundary_hook=failure_hook,
            )
            public, result, connection_ids = reader.run()
            self.assertTrue(injected)
            if result is not None or reader.serialized_bytes is not None:
                _fail()
            self._require_public_equivalence(_generic_failure(), public)
            self._record_case(
                fixture_id="WF01",
                variant=variant,
                family="workload",
                expected_decision="deny",
                expected=_generic_failure(),
                actual_decision="deny",
                actual=public,
                accessor_calls=reader.access.account + reader.access.gl,
                connection_ids=connection_ids,
            )

        self.assertEqual(0, limits["MAX_RETRIES"])
        if not hasattr(self.__class__, "reconnect_retry_observations"):
            _fail()
        observed_kill_retries = tuple(self.__class__.reconnect_retry_observations)
        observed_kill_fallbacks = tuple(self.__class__.reconnect_fallback_observations)
        if (
            len(observed_kill_retries) != len(RECONNECT_BOUNDARIES)
            or len(observed_kill_fallbacks) != len(RECONNECT_BOUNDARIES)
            or max(observed_kill_retries) != limits["MAX_RETRIES"]
            or any(observed_kill_fallbacks)
        ):
            _fail()
        self.evidence.append_jsonl(
            "workload-results.jsonl",
            {
                "record_type": "reconnect_cap_derivation",
                "candidate": CANDIDATE,
                "derived_max_retries": limits["MAX_RETRIES"],
                "killed_material_boundary_count": len(RECONNECT_BOUNDARIES),
                "reconnect_retries_observed": list(observed_kill_retries),
                "fallback_host_attempts_observed": list(observed_kill_fallbacks),
                "numeric_caps_approved": False,
            },
        )
        self.assertEqual(0, MAX_ACTIVE_DIMENSIONS)
        positive_dimension_context = replace(
            _base_context(self.env, "COMPANY_A", "BOOK_DEFAULT"),
            active_dimensions=1,
        )
        decision, public, result = _attempt_reconstruction(
            positive_dimension_context,
            _base_fiscal_year(self.env, "COMPANY_A"),
            _base_chart("COMPANY_A", self.env.currency),
            _base_rows(positive_dimension_context),
        )
        self.assertEqual("deny", decision)
        self.assertIsNone(result)
        self._require_public_equivalence(_generic_failure(), public)
