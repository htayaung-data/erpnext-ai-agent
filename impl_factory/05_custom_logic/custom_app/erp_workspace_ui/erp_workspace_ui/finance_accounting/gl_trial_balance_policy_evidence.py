"""Dormant authenticated production-policy evidence boundary for Finance GL/TB.

The module is evidence-only. It has no enabled default, production policy,
mutation, report passthrough, UI, AI, or accounting-execution authority.
"""

from __future__ import annotations

import json
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Final

import frappe
from frappe import permissions as frappe_permissions

from .gl_trial_balance_adapter import (
    CompleteAccountManifest,
    GLTrialBalanceReadRequest,
    ReadSnapshotEvidence,
    _COMPANY_FIELDS,
    _FISCAL_YEAR_FIELDS,
    _PERMISSION_REQUIREMENTS,
    _read_rows,
    _read_with_snapshot,
    _validate_effective_permissions,
    _validate_fiscal_applicability,
    _validate_manifest,
    _validate_permissions,
    _validate_snapshot,
)
from .gl_trial_balance_frappe_runtime import (
    FrappeGLTrialBalanceRuntime,
    GLTrialBalanceRuntimePolicy,
)
from .gl_trial_balance_service import (
    GLTrialBalanceServicePolicy,
    GLTrialBalanceServiceRequest,
    _SCHEMA_VERSION as _PRODUCT_SCHEMA_VERSION,
    _amounts_payload,
    _build_response,
    _canonical_json_bytes,
    _line_payloads,
)

__all__ = [
    "GLTrialBalancePolicyEvidenceError",
    "collect_gl_trial_balance_policy_evidence",
    "diagnose_gl_trial_balance_policy_evidence_failure_phase",
]

_GENERIC_ERROR: Final = "finance_read_unavailable"
_METHOD_PATH: Final = (
    "erp_workspace_ui.finance_accounting.gl_trial_balance_policy_evidence."
    "collect_gl_trial_balance_policy_evidence"
)
_DIAGNOSTIC_METHOD_PATH: Final = (
    "erp_workspace_ui.finance_accounting.gl_trial_balance_policy_evidence."
    "diagnose_gl_trial_balance_policy_evidence_failure_phase"
)
_CONFIG_KEY: Final = "finance_gl_trial_balance_policy_evidence"
_DIAGNOSTIC_CONFIG_KEY: Final = (
    "finance_gl_trial_balance_policy_evidence_diagnostic"
)
_EVIDENCE_SCHEMA_VERSION: Final = "finance-gl-trial-balance.policy-evidence.v1"
_CONFIG_KEYS: Final = frozenset(
    {
        "enabled",
        "expected_driver",
        "expected_driver_version",
        "expected_server_version",
    }
)
_DIAGNOSTIC_CONFIG_KEYS: Final = frozenset({"enabled"})
_DIAGNOSTIC_PHASES: Final = frozenset(
    {
        "snapshot_runtime_construct",
        "snapshot_wrapper_bind",
        "snapshot_raw_connection",
        "snapshot_driver_identity",
        "snapshot_preflight_query",
        "snapshot_server_identity",
        "snapshot_connection_identity",
        "snapshot_transaction_idle",
        "snapshot_set_isolation",
        "snapshot_start",
        "snapshot_state",
        "snapshot_evidence_build",
        "snapshot_validate",
        "complete",
    }
)
_PRIVILEGED_ROLES: Final = frozenset(
    {"System Manager", "Administrator", "Bypass Finance Scope"}
)
_RESTRICTIVE_DOCTYPES: Final = frozenset(
    {
        "Account",
        "GL Entry",
        "Finance Book",
        "Cost Center",
        "Project",
        "Accounting Dimension",
    }
)
_USER_PERMISSION_KEYS: Final = frozenset(
    {"doc", "applicable_for", "is_default", "hide_descendants"}
)
_REQUEST_CEILING_MICROSECONDS: Final = 120_000_000
_ROUNDING_METHODS: Final = frozenset(
    {"Banker's Rounding", "Commercial Rounding"}
)
_CHARSET_WIDTHS: Final = {
    "ascii": 1,
    "latin1": 1,
    "utf8": 3,
    "utf8mb3": 3,
    "utf8mb4": 4,
}
_SOURCE_GROUPS: Final = (
    "company_rows",
    "active_fiscal_year_rows",
    "fiscal_year_company_rows",
    "finance_book_rows",
    "active_dimension_rows",
    "fiscal_applicability_rows",
    "account_manifest_ids",
    "root_manifest_ids",
    "account_rows",
    "final_manifest_ids",
    "final_root_ids",
    "final_fiscal_applicability_rows",
)

_COUNT_COMPANY_SQL: Final = (
    "SELECT COUNT(DISTINCT name) FROM tabCompany WHERE name = %(company)s"
)
_COUNT_ACTIVE_FISCAL_YEARS_SQL: Final = (
    "SELECT COUNT(DISTINCT name) FROM `tabFiscal Year` WHERE disabled = 0"
)
_COUNT_FISCAL_YEAR_COMPANY_SQL: Final = (
    "SELECT COUNT(*) FROM `tabFiscal Year Company` AS link "
    "INNER JOIN `tabFiscal Year` AS fy ON fy.name = link.parent "
    "WHERE fy.disabled = 0 AND link.parenttype = 'Fiscal Year' "
    "AND link.parentfield = 'companies' AND link.company = %(company)s"
)
_COUNT_FINANCE_BOOK_SQL: Final = (
    "SELECT COUNT(DISTINCT name) FROM `tabFinance Book` "
    "WHERE name = %(finance_book)s"
)
_COUNT_ACTIVE_DIMENSIONS_SQL: Final = (
    "SELECT COUNT(DISTINCT name) FROM `tabAccounting Dimension` "
    "WHERE disabled = 0"
)
_STATEMENT_CEILING_SQL: Final = (
    "SELECT @@GLOBAL.max_statement_time, @@SESSION.max_statement_time"
)
_NUMERIC_SHAPE_SQL: Final = (
    "SELECT COUNT(*), MIN(NUMERIC_PRECISION), MAX(NUMERIC_PRECISION), "
    "MIN(NUMERIC_SCALE), MAX(NUMERIC_SCALE) "
    "FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() "
    "AND TABLE_NAME = 'tabGL Entry' AND COLUMN_NAME IN ('debit', 'credit')"
)
_CURRENCY_METADATA_SQL: Final = (
    "SELECT COUNT(*), MIN(fraction_units), MAX(fraction_units), "
    "MIN(smallest_currency_fraction_value), "
    "MAX(smallest_currency_fraction_value) "
    "FROM tabCurrency WHERE name = %(currency)s"
)
_IDENTIFIER_ENVELOPE_SQL: Final = (
    "SELECT "
    "MAX(CASE WHEN TABLE_NAME = 'tabAccount' THEN CHARACTER_MAXIMUM_LENGTH END), "
    "MAX(CASE WHEN TABLE_NAME = 'tabAccount' THEN CHARACTER_SET_NAME END), "
    "MAX(CASE WHEN TABLE_NAME = 'tabCompany' THEN CHARACTER_MAXIMUM_LENGTH END), "
    "MAX(CASE WHEN TABLE_NAME = 'tabCompany' THEN CHARACTER_SET_NAME END), "
    "MAX(CASE WHEN TABLE_NAME = 'tabFiscal Year' THEN CHARACTER_MAXIMUM_LENGTH END), "
    "MAX(CASE WHEN TABLE_NAME = 'tabFiscal Year' THEN CHARACTER_SET_NAME END), "
    "MAX(CASE WHEN TABLE_NAME = 'tabCurrency' THEN CHARACTER_MAXIMUM_LENGTH END), "
    "MAX(CASE WHEN TABLE_NAME = 'tabCurrency' THEN CHARACTER_SET_NAME END), "
    "MAX(CASE WHEN TABLE_NAME = 'tabFinance Book' THEN CHARACTER_MAXIMUM_LENGTH END), "
    "MAX(CASE WHEN TABLE_NAME = 'tabFinance Book' THEN CHARACTER_SET_NAME END) "
    "FROM information_schema.COLUMNS "
    "WHERE TABLE_SCHEMA = DATABASE() AND COLUMN_NAME = 'name' "
    "AND TABLE_NAME IN "
    "('tabAccount', 'tabCompany', 'tabFiscal Year', 'tabCurrency', 'tabFinance Book')"
)


class GLTrialBalancePolicyEvidenceError(RuntimeError):
    """One stable, non-identifying evidence-boundary failure."""

    code = _GENERIC_ERROR

    def __init__(self) -> None:
        super().__init__(_GENERIC_ERROR)


@dataclass(slots=True)
class _PhaseRecorder:
    phase: str = "internal"

    def enter(self, phase: str) -> None:
        self.phase = phase if phase in _DIAGNOSTIC_PHASES else "internal"


@dataclass(frozen=True, slots=True)
class _AuthorityEvidence:
    user: str
    roles: tuple[str, ...]
    user_permissions: tuple[tuple[object, ...], ...]
    companies: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _CompanyMeasurement:
    source_floors: Mapping[str, int]
    max_gl_entries: int
    fiscal_endpoints: int
    minimum_fiscal_start: date
    maximum_fiscal_end: date
    maximum_fiscal_span_days: int
    precision: int
    statement_ceiling: Mapping[str, object]
    database_shape: Mapping[str, int]
    identifier_envelopes: Mapping[str, Mapping[str, int]]
    byte_evidence: Mapping[str, object]
    elapsed_microseconds: int


def _fail() -> None:
    raise ValueError(_GENERIC_ERROR)


def _enter_phase(
    recorder: _PhaseRecorder | None,
    phase: str,
) -> None:
    if recorder is not None:
        recorder.enter(phase)


def _strict_text(value: object, *, allow_empty: bool = False) -> str:
    if type(value) is not str or value != value.strip():
        _fail()
    if not allow_empty and not value:
        _fail()
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        _fail()
    return value


def _strict_flag(value: object) -> int:
    if type(value) is not int or value not in (0, 1):
        _fail()
    return value


def _nonnegative_int(value: object) -> int:
    if type(value) is not int or value < 0:
        _fail()
    return value


def _positive_int(value: object) -> int:
    result = _nonnegative_int(value)
    if result == 0:
        _fail()
    return result


def _closed_mapping(value: object, keys: frozenset[str]) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or frozenset(value) != keys:
        _fail()
    if any(type(key) is not str for key in value):
        _fail()
    return value


def _mapping_value(value: object, key: str) -> object:
    if isinstance(value, Mapping):
        if key not in value:
            _fail()
        return value[key]
    try:
        return getattr(value, key)
    except Exception:
        _fail()


def _exact_integer(value: object) -> int:
    if isinstance(value, bool):
        _fail()
    try:
        converted = Decimal(str(value))
    except (InvalidOperation, ValueError):
        _fail()
    if not converted.is_finite() or converted != converted.to_integral_value():
        _fail()
    result = int(converted)
    if result < 0:
        _fail()
    return result


def _elapsed_microseconds(started_ns: int) -> int:
    value = (time.monotonic_ns() - started_ns) // 1_000
    return _nonnegative_int(value)


def _request_shape(method_path: str) -> None:
    local = getattr(frappe, "local")
    request = getattr(local, "request")
    if _strict_text(getattr(request, "method")) != "POST":
        _fail()
    form_dict = getattr(frappe, "form_dict")
    if not isinstance(form_dict, Mapping):
        _fail()
    if any(type(key) is not str for key in form_dict):
        _fail()
    keys = frozenset(form_dict)
    if keys not in (frozenset(), frozenset({"cmd"})):
        _fail()
    if "cmd" in form_dict and _strict_text(form_dict["cmd"]) != method_path:
        _fail()


def _request_policy(
    *,
    method_path: str = _METHOD_PATH,
) -> GLTrialBalanceRuntimePolicy:
    _request_shape(method_path)

    local = getattr(frappe, "local")
    conf = getattr(local, "conf")
    if isinstance(conf, Mapping):
        raw = conf.get(_CONFIG_KEY)
    else:
        getter = getattr(conf, "get", None)
        if not callable(getter):
            _fail()
        raw = getter(_CONFIG_KEY)
    document = _closed_mapping(raw, _CONFIG_KEYS)
    if type(document["enabled"]) is not bool or document["enabled"] is not True:
        _fail()
    return GLTrialBalanceRuntimePolicy(
        expected_driver=_strict_text(document["expected_driver"]),
        expected_driver_version=_strict_text(document["expected_driver_version"]),
        expected_server_version=_strict_text(document["expected_server_version"]),
    )


def _diagnostic_enabled() -> None:
    _request_shape(_DIAGNOSTIC_METHOD_PATH)
    local = getattr(frappe, "local")
    conf = getattr(local, "conf")
    if isinstance(conf, Mapping):
        raw = conf.get(_DIAGNOSTIC_CONFIG_KEY)
    else:
        getter = getattr(conf, "get", None)
        if not callable(getter):
            _fail()
        raw = getter(_DIAGNOSTIC_CONFIG_KEY)
    document = _closed_mapping(raw, _DIAGNOSTIC_CONFIG_KEYS)
    if type(document["enabled"]) is not bool or document["enabled"] is not True:
        _fail()


def _diagnostic_caller_authorized() -> None:
    local = getattr(frappe, "local")
    session = getattr(local, "session")
    user = _strict_text(_mapping_value(session, "user"))
    if user in {"Guest", "Administrator"}:
        _fail()
    roles_value = getattr(frappe, "get_roles")(user)
    if isinstance(roles_value, (str, bytes, bytearray)) or not isinstance(
        roles_value, Sequence
    ):
        _fail()
    roles = tuple(_strict_text(role) for role in roles_value)
    role_set = set(roles)
    if (
        len(role_set) != len(roles)
        or "Accounts Manager" not in role_set
        or role_set & _PRIVILEGED_ROLES
    ):
        _fail()


def _authority_snapshot() -> _AuthorityEvidence:
    local = getattr(frappe, "local")
    session = getattr(local, "session")
    user = _strict_text(_mapping_value(session, "user"))
    if user in {"Guest", "Administrator"}:
        _fail()

    roles_value = getattr(frappe, "get_roles")(user)
    if isinstance(roles_value, (str, bytes, bytearray)) or not isinstance(
        roles_value, Sequence
    ):
        _fail()
    roles = tuple(_strict_text(role) for role in roles_value)
    if len(set(roles)) != len(roles):
        _fail()
    role_set = set(roles)
    if "Accounts Manager" not in role_set or role_set & _PRIVILEGED_ROLES:
        _fail()

    raw_permissions = getattr(
        frappe_permissions, "get_user_permissions"
    )(user)
    if not isinstance(raw_permissions, Mapping):
        _fail()
    normalized: list[tuple[object, ...]] = []
    companies: list[str] = []
    seen: set[tuple[object, ...]] = set()
    for raw_allow, entries in raw_permissions.items():
        allow = _strict_text(raw_allow)
        if isinstance(entries, (str, bytes, bytearray)) or not isinstance(
            entries, Sequence
        ):
            _fail()
        for entry in entries:
            if not isinstance(entry, Mapping) or frozenset(entry) != _USER_PERMISSION_KEYS:
                _fail()
            for_value = _strict_text(entry["doc"])
            applicable_for = entry["applicable_for"]
            if applicable_for is not None:
                applicable_for = _strict_text(applicable_for, allow_empty=True)
            _strict_flag(entry["is_default"])
            hide_descendants = _strict_flag(entry["hide_descendants"])
            apply_to_all = 1 if applicable_for in (None, "") else 0
            identity = (
                allow,
                for_value,
                applicable_for,
                apply_to_all,
                hide_descendants,
            )
            if identity in seen:
                _fail()
            seen.add(identity)
            if allow == "Company":
                if (
                    apply_to_all != 1
                    or hide_descendants != 0
                    or for_value in companies
                ):
                    _fail()
                companies.append(for_value)
            elif (
                allow in _RESTRICTIVE_DOCTYPES
                or applicable_for in {"Account", "GL Entry"}
            ):
                _fail()
            normalized.append(identity)
    if not companies:
        _fail()
    return _AuthorityEvidence(
        user=user,
        roles=tuple(sorted(roles)),
        user_permissions=tuple(sorted(normalized, key=repr)),
        companies=tuple(sorted(companies)),
    )


def _message_log() -> tuple[object, list[object], tuple[object, ...]]:
    local = getattr(frappe, "local")
    message_log = getattr(local, "message_log")
    if type(message_log) is not list or message_log:
        _fail()
    return local, message_log, tuple(message_log)


def _restore_message_log(
    local: object,
    message_log: list[object],
    original: tuple[object, ...],
) -> bool:
    try:
        message_log[:] = original
        if getattr(local, "message_log", None) is not message_log:
            setattr(local, "message_log", message_log)
        return (
            getattr(local, "message_log", None) is message_log
            and tuple(message_log) == original
        )
    except Exception:
        return False


def _checkpoint(
    runtime: FrappeGLTrialBalanceRuntime,
    snapshot: ReadSnapshotEvidence,
    user: str,
    company: str,
) -> None:
    if runtime.current_user() != user:
        _fail()
    if _validate_snapshot(
        runtime.final_snapshot_evidence(snapshot),
        user=user,
        company=company,
    ) != snapshot:
        _fail()


def _duration_microseconds(value: object) -> int:
    if isinstance(value, bool):
        _fail()
    try:
        seconds = Decimal(str(value))
        microseconds = seconds * Decimal(1_000_000)
    except (InvalidOperation, ValueError):
        _fail()
    if (
        not seconds.is_finite()
        or seconds < 0
        or microseconds != microseconds.to_integral_value()
    ):
        _fail()
    return _nonnegative_int(int(microseconds))


class _EvidenceRuntime(FrappeGLTrialBalanceRuntime):
    """Sealed evidence extensions over the committed snapshot owner."""

    def _evidence_row(
        self,
        snapshot: ReadSnapshotEvidence,
        statement: str,
        parameters: Mapping[str, object] | None = None,
    ) -> tuple[object, ...]:
        allowed = {
            _COUNT_COMPANY_SQL,
            _COUNT_ACTIVE_FISCAL_YEARS_SQL,
            _COUNT_FISCAL_YEAR_COMPANY_SQL,
            _COUNT_FINANCE_BOOK_SQL,
            _COUNT_ACTIVE_DIMENSIONS_SQL,
            _STATEMENT_CEILING_SQL,
            _NUMERIC_SHAPE_SQL,
            _CURRENCY_METADATA_SQL,
            _IDENTIFIER_ENVELOPE_SQL,
        }
        if statement not in allowed:
            _fail()
        return self._aggregate_one(snapshot, statement, parameters or {})

    def _evidence_count(
        self,
        snapshot: ReadSnapshotEvidence,
        statement: str,
        parameters: Mapping[str, object] | None = None,
    ) -> int:
        row = self._evidence_row(snapshot, statement, parameters)
        if len(row) != 1:
            _fail()
        return _nonnegative_int(row[0])

    def count_company(
        self, snapshot: ReadSnapshotEvidence, company: str
    ) -> int:
        return self._evidence_count(
            snapshot, _COUNT_COMPANY_SQL, {"company": company}
        )

    def count_active_fiscal_years(
        self, snapshot: ReadSnapshotEvidence
    ) -> int:
        return self._evidence_count(
            snapshot, _COUNT_ACTIVE_FISCAL_YEARS_SQL
        )

    def count_fiscal_year_company(
        self, snapshot: ReadSnapshotEvidence, company: str
    ) -> int:
        return self._evidence_count(
            snapshot,
            _COUNT_FISCAL_YEAR_COMPANY_SQL,
            {"company": company},
        )

    def count_finance_book(
        self,
        snapshot: ReadSnapshotEvidence,
        finance_book: str,
    ) -> int:
        return self._evidence_count(
            snapshot,
            _COUNT_FINANCE_BOOK_SQL,
            {"finance_book": finance_book},
        )

    def count_active_dimensions(
        self, snapshot: ReadSnapshotEvidence
    ) -> int:
        return self._evidence_count(
            snapshot, _COUNT_ACTIVE_DIMENSIONS_SQL
        )

    def count_accounts(
        self, snapshot: ReadSnapshotEvidence, company: str
    ) -> int:
        return self._count_accounts(snapshot, company)

    def count_gl_entries(
        self,
        snapshot: ReadSnapshotEvidence,
        company: str,
        to_date: date,
        finance_book: str,
    ) -> int:
        return self._count_gl_entries(
            snapshot, company, to_date, finance_book
        )

    def statement_ceiling(
        self, snapshot: ReadSnapshotEvidence
    ) -> Mapping[str, object]:
        row = self._evidence_row(snapshot, _STATEMENT_CEILING_SQL)
        if len(row) != 2:
            _fail()
        global_value = _duration_microseconds(row[0])
        session_value = _duration_microseconds(row[1])
        return {
            "global_state": "enabled" if global_value else "disabled",
            "global_microseconds": global_value,
            "session_state": "enabled" if session_value else "disabled",
            "session_microseconds": session_value,
        }

    def numeric_shape(
        self, snapshot: ReadSnapshotEvidence
    ) -> Mapping[str, int]:
        row = self._evidence_row(snapshot, _NUMERIC_SHAPE_SQL)
        if len(row) != 5 or row[0] != 2:
            _fail()
        precision_min = _positive_int(row[1])
        precision_max = _positive_int(row[2])
        scale_min = _nonnegative_int(row[3])
        scale_max = _nonnegative_int(row[4])
        if precision_min != precision_max or scale_min != scale_max:
            _fail()
        if scale_min > precision_min:
            _fail()
        return {
            "numeric_precision": precision_min,
            "numeric_scale": scale_min,
        }

    def currency_metadata(
        self,
        snapshot: ReadSnapshotEvidence,
        currency: str,
    ) -> tuple[int, Decimal]:
        row = self._evidence_row(
            snapshot,
            _CURRENCY_METADATA_SQL,
            {"currency": currency},
        )
        if len(row) != 5 or row[0] != 1 or row[1] != row[2] or row[3] != row[4]:
            _fail()
        fraction_units = _positive_int(row[1])
        try:
            smallest = Decimal(str(row[3]))
        except (InvalidOperation, ValueError):
            _fail()
        if not smallest.is_finite() or smallest <= 0:
            _fail()
        return fraction_units, smallest

    def identifier_envelopes(
        self, snapshot: ReadSnapshotEvidence
    ) -> Mapping[str, Mapping[str, int]]:
        row = self._evidence_row(snapshot, _IDENTIFIER_ENVELOPE_SQL)
        if len(row) != 10:
            _fail()
        names = (
            "account",
            "company",
            "fiscal_year",
            "currency",
            "finance_book",
        )
        result: dict[str, Mapping[str, int]] = {}
        for index, name in enumerate(names):
            characters = _positive_int(row[index * 2])
            charset = _strict_text(row[index * 2 + 1])
            width = _CHARSET_WIDTHS.get(charset)
            if width is None:
                _fail()
            utf8_bytes = characters * width
            result[name] = {
                "characters": characters,
                "utf8_bytes": utf8_bytes,
                "json_string_bytes": 2 + characters * max(width, 2),
            }
        return result


def _precision_evidence(
    runtime: _EvidenceRuntime,
    snapshot: ReadSnapshotEvidence,
    *,
    user: str,
    company: str,
    base_currency: str,
) -> Mapping[str, object]:
    from erpnext.accounts.utils import get_currency_precision
    from frappe.model.meta import get_field_precision

    database = getattr(frappe, "db")
    get_single_value = getattr(database, "get_single_value")
    system_database_value = get_single_value(
        "System Settings", "currency_precision"
    )
    _checkpoint(runtime, snapshot, user, company)

    settings_getter = getattr(frappe, "get_system_settings")
    system_api_value = settings_getter("currency_precision")
    rounding_method = _strict_text(
        settings_getter("rounding_method")
    )
    _checkpoint(runtime, snapshot, user, company)

    global_value = get_currency_precision()
    _checkpoint(runtime, snapshot, user, company)

    meta = getattr(frappe, "get_meta")("GL Entry")
    get_field = getattr(meta, "get_field")
    debit_field = get_field("debit")
    credit_field = get_field("credit")
    if debit_field is None or credit_field is None:
        _fail()
    debit_value = get_field_precision(
        debit_field, currency=base_currency
    )
    credit_value = get_field_precision(
        credit_field, currency=base_currency
    )
    _checkpoint(runtime, snapshot, user, company)

    values = tuple(
        _exact_integer(value)
        for value in (
            system_database_value,
            system_api_value,
            global_value,
            debit_value,
            credit_value,
        )
    )
    if len(set(values)) != 1:
        _fail()
    precision = values[0]
    if precision > 8 or rounding_method not in _ROUNDING_METHODS:
        _fail()

    fraction_units, smallest_fraction = runtime.currency_metadata(
        snapshot, base_currency
    )
    quantum = Decimal(1).scaleb(-precision)
    multiple = smallest_fraction / quantum
    if (
        multiple != multiple.to_integral_value()
        or Decimal(fraction_units) * smallest_fraction != Decimal(1)
    ):
        _fail()
    return {
        "precision": precision,
        "system_settings_agreement": True,
        "effective_debit_agreement": True,
        "effective_credit_agreement": True,
        "currency_rounding_agreement": True,
        "rounding_method_recognized": True,
    }


def _active_fiscal_rows(
    runtime: _EvidenceRuntime,
    snapshot: ReadSnapshotEvidence,
    count: int,
) -> tuple[tuple[str, date, date], ...]:
    rows = _read_rows(
        runtime,
        snapshot,
        doctype="Fiscal Year",
        fields=_FISCAL_YEAR_FIELDS,
        filters=(("disabled", "=", 0),),
        order_by="year_start_date asc, name asc",
        maximum=count,
    )
    if len(rows) != count or not rows:
        _fail()
    parsed: list[tuple[str, date, date]] = []
    seen: set[str] = set()
    for row in rows:
        if frozenset(row) != frozenset(_FISCAL_YEAR_FIELDS):
            _fail()
        name = _strict_text(row["name"])
        start = row["year_start_date"]
        end = row["year_end_date"]
        if (
            name in seen
            or type(start) is not date
            or type(end) is not date
            or start > end
            or _strict_flag(row["disabled"]) != 0
        ):
            _fail()
        seen.add(name)
        parsed.append((name, start, end))
    return tuple(parsed)


def _response_measurement(
    *,
    result: object,
    request: GLTrialBalanceServiceRequest,
    max_accounts: int,
    max_gl_entries: int,
    numeric_precision: int,
    numeric_scale: int,
) -> Mapping[str, object]:
    scope = getattr(result, "scope")
    precision = _nonnegative_int(getattr(scope, "precision"))
    gl_count = _nonnegative_int(max_gl_entries)
    growth = 0 if gl_count <= 1 else len(str(gl_count - 1))
    integer_digits = max(
        1, numeric_precision - numeric_scale + growth
    )
    fixed_decimal_width = integer_digits + (
        precision + 1 if precision > 0 else 0
    )

    lines = getattr(result, "lines")
    line_payloads = _line_payloads(
        lines,
        precision=precision,
        max_accounts=max_accounts,
        response_cap=fixed_decimal_width,
    )
    gross_payload = _amounts_payload(
        getattr(result, "gross_totals"),
        precision=precision,
        response_cap=fixed_decimal_width,
    )
    presentation_payload = _amounts_payload(
        getattr(result, "presentation_totals"),
        precision=precision,
        response_cap=fixed_decimal_width,
    )
    boundary = {
        "accounting_execution_enabled": False,
        "cancellation_control_claimed": False,
        "mutation_enabled": False,
        "party_identifiers_returned": False,
        "period_close_control_claimed": False,
        "read_only": True,
        "source_gl_entries_returned": False,
        "voucher_identifiers_returned": False,
    }
    scope_payload = {
        "active_dimensions": getattr(scope, "active_dimensions"),
        "base_currency": getattr(scope, "base_currency"),
        "company": getattr(scope, "company"),
        "currency_precision": precision,
        "default_finance_book": getattr(
            scope, "default_finance_book"
        ),
        "finance_book_scope": list(
            getattr(scope, "finance_book_cohort")
        ),
        "fiscal_year": request.fiscal_year,
        "fiscal_year_end": getattr(
            scope, "fiscal_year_end"
        ).isoformat(),
        "fiscal_year_start": getattr(
            scope, "fiscal_year_start"
        ).isoformat(),
        "from_date": getattr(scope, "from_date").isoformat(),
        "to_date": getattr(scope, "to_date").isoformat(),
    }
    metadata = {
        "boundary": boundary,
        "schema_version": _PRODUCT_SCHEMA_VERSION,
        "scope": scope_payload,
        "state": "ready",
    }
    envelope = {
        "company": request.company,
        "fiscal_year": request.fiscal_year,
        "from_date": request.from_date.isoformat(),
        "to_date": request.to_date.isoformat(),
    }
    request_bytes = len(
        _canonical_json_bytes(envelope, terminal_lf=False)
    )
    metadata_bytes = len(
        _canonical_json_bytes(metadata, terminal_lf=False)
    )
    response = {
        **metadata,
        "lines": line_payloads,
        "totals": {
            "gross": gross_payload,
            "presentation": presentation_payload,
        },
    }
    encoded = _canonical_json_bytes(response, terminal_lf=True)
    policy = GLTrialBalanceServicePolicy(
        currency_precision=precision,
        max_accounts=max_accounts,
        max_gl_entries=max(max_gl_entries, 1),
        max_metadata_bytes=max(request_bytes, metadata_bytes),
        max_response_bytes=len(encoded),
    )
    if _build_response(
        result=result, request=request, policy=policy
    ) != encoded:
        _fail()

    identifiers = [
        request.company,
        request.fiscal_year,
        scope_payload["base_currency"],
        scope_payload["default_finance_book"],
    ]
    parents: list[str] = []
    max_depth = 0
    fixed_values: list[str] = []
    for payload in line_payloads:
        identifiers.append(payload["account_id"])
        parent = payload["parent_account_id"]
        if parent is not None:
            identifiers.append(parent)
            parents.append(parent)
        max_depth = max(max_depth, payload["depth"])
        fixed_values.extend(payload["amounts"].values())
    fixed_values.extend(gross_payload.values())
    fixed_values.extend(presentation_payload.values())
    observed_identifier_bytes = max(
        len(_strict_text(value).encode("utf-8"))
        for value in identifiers
    )
    observed_escape_extra = max(
        len(_canonical_json_bytes(value, terminal_lf=False))
        - len(value.encode("utf-8"))
        - 2
        for value in identifiers
    )
    observed_parent_bytes = max(
        (len(value.encode("utf-8")) for value in parents),
        default=0,
    )
    observed_decimal_bytes = max(
        len(_strict_text(value).encode("ascii"))
        for value in fixed_values
    )
    if observed_decimal_bytes > fixed_decimal_width:
        _fail()
    return {
        "request_envelope_bytes": request_bytes,
        "response_metadata_bytes": metadata_bytes,
        "response_bytes": len(encoded),
        "line_count": len(line_payloads),
        "max_observed_depth": max_depth,
        "max_observed_depth_width": len(str(max_depth)),
        "max_identifier_utf8_bytes_observed": observed_identifier_bytes,
        "max_identifier_escape_extra_bytes_observed": observed_escape_extra,
        "max_parent_identifier_utf8_bytes_observed": observed_parent_bytes,
        "max_fixed_decimal_bytes_observed": observed_decimal_bytes,
        "aggregation_digit_growth": growth,
        "fixed_decimal_width_bound": fixed_decimal_width,
    }


def _aggregate_response_measurements(
    values: Sequence[Mapping[str, object]],
) -> Mapping[str, object]:
    if not values:
        _fail()
    for value in values:
        required = frozenset(
            {
                "request_envelope_bytes",
                "response_metadata_bytes",
                "response_bytes",
                "line_count",
                "max_observed_depth",
                "max_observed_depth_width",
                "max_identifier_utf8_bytes_observed",
                "max_identifier_escape_extra_bytes_observed",
                "max_parent_identifier_utf8_bytes_observed",
                "max_fixed_decimal_bytes_observed",
                "aggregation_digit_growth",
                "fixed_decimal_width_bound",
            }
        )
        if not isinstance(value, Mapping) or frozenset(value) != required:
            _fail()
        for item in value.values():
            _nonnegative_int(item)
    winner = max(
        values,
        key=lambda item: (
            item["response_bytes"],
            item["line_count"],
        ),
    )
    request_max = max(
        item["request_envelope_bytes"] for item in values
    )
    metadata_max = max(
        item["response_metadata_bytes"] for item in values
    )
    return {
        "request_envelope_max_bytes": request_max,
        "response_metadata_max_bytes": metadata_max,
        "current_metadata_floor_bytes": max(
            request_max, metadata_max
        ),
        "current_response_floor_bytes": winner["response_bytes"],
        "current_response_floor_line_count": winner["line_count"],
        "max_observed_depth": max(
            item["max_observed_depth"] for item in values
        ),
        "max_observed_depth_width": max(
            item["max_observed_depth_width"] for item in values
        ),
        "max_identifier_utf8_bytes_observed": max(
            item["max_identifier_utf8_bytes_observed"]
            for item in values
        ),
        "max_identifier_escape_extra_bytes_observed": max(
            item["max_identifier_escape_extra_bytes_observed"]
            for item in values
        ),
        "max_parent_identifier_utf8_bytes_observed": max(
            item["max_parent_identifier_utf8_bytes_observed"]
            for item in values
        ),
        "max_fixed_decimal_bytes_observed": max(
            item["max_fixed_decimal_bytes_observed"]
            for item in values
        ),
        "aggregation_digit_growth": max(
            item["aggregation_digit_growth"] for item in values
        ),
        "fixed_decimal_width_bound": max(
            item["fixed_decimal_width_bound"] for item in values
        ),
    }


def _collect_company(
    *,
    authority: _AuthorityEvidence,
    company: str,
    runtime_policy: GLTrialBalanceRuntimePolicy,
    phase_recorder: _PhaseRecorder | None = None,
) -> _CompanyMeasurement:
    started_ns = time.monotonic_ns()
    runtime = _EvidenceRuntime(
        frappe_module=frappe,
        permissions_module=frappe_permissions,
        policy=runtime_policy,
        snapshot_phase_hook=(
            phase_recorder.enter
            if phase_recorder is not None
            else None
        ),
    )
    snapshot: ReadSnapshotEvidence | None = None
    result: _CompanyMeasurement | None = None
    failed = False
    failure_phase: str | None = None
    try:
        _enter_phase(phase_recorder, "permission_initial")
        if company not in authority.companies:
            _fail()
        snapshot_candidate = runtime.begin_read_snapshot(
            authority.user, company
        )
        _enter_phase(phase_recorder, "snapshot_validate")
        snapshot = _validate_snapshot(
            snapshot_candidate,
            user=authority.user,
            company=company,
        )
        _enter_phase(phase_recorder, "complete")
        _enter_phase(phase_recorder, "permission_initial")
        if _authority_snapshot() != authority:
            _fail()
        _checkpoint(runtime, snapshot, authority.user, company)
        effective = runtime.effective_permission_evidence(snapshot)
        _validate_effective_permissions(
            effective,
            snapshot=snapshot,
            user=authority.user,
            company=company,
        )
        _validate_permissions(runtime, snapshot, authority.user)

        _enter_phase(phase_recorder, "company_scope")
        company_count = runtime.count_company(snapshot, company)
        if company_count != 1:
            _fail()
        company_rows = _read_rows(
            runtime,
            snapshot,
            doctype="Company",
            fields=_COMPANY_FIELDS,
            filters=(("name", "=", company),),
            order_by="name asc",
            maximum=company_count,
        )
        if (
            len(company_rows) != 1
            or frozenset(company_rows[0])
            != frozenset(_COMPANY_FIELDS)
            or _strict_text(company_rows[0]["name"]) != company
        ):
            _fail()
        base_currency = _strict_text(
            company_rows[0]["default_currency"]
        )
        default_finance_book = _strict_text(
            company_rows[0]["default_finance_book"]
        )

        _enter_phase(phase_recorder, "fiscal_scope")
        active_fiscal_count = runtime.count_active_fiscal_years(
            snapshot
        )
        fiscal_rows = _active_fiscal_rows(
            runtime, snapshot, _positive_int(active_fiscal_count)
        )
        first_name, first_start, first_end = fiscal_rows[0]
        _enter_phase(phase_recorder, "precision")
        precision_evidence = _precision_evidence(
            runtime,
            snapshot,
            user=authority.user,
            company=company,
            base_currency=base_currency,
        )
        precision = _nonnegative_int(
            precision_evidence["precision"]
        )
        provisional = GLTrialBalanceReadRequest(
            company=company,
            fiscal_year=first_name,
            from_date=first_start,
            to_date=first_end,
            currency_precision=precision,
            max_accounts=max(1, active_fiscal_count),
            max_gl_entries=1,
        )
        _enter_phase(phase_recorder, "fiscal_scope")
        fiscal_manifest, applicability = _validate_fiscal_applicability(
            runtime.complete_fiscal_year_applicability(
                snapshot, company, active_fiscal_count
            ),
            snapshot=snapshot,
            request=provisional,
        )
        if frozenset(applicability) != frozenset(
            item[0] for item in fiscal_rows
        ):
            _fail()
        if any(
            state not in {"global", "selected_company"}
            for state in applicability.values()
        ):
            _fail()

        _enter_phase(phase_recorder, "company_scope")
        selected_link_count = runtime.count_fiscal_year_company(
            snapshot, company
        )
        finance_book_count = runtime.count_finance_book(
            snapshot, default_finance_book
        )
        if finance_book_count != 1:
            _fail()
        active_dimension_count = runtime.count_active_dimensions(
            snapshot
        )
        if active_dimension_count != 0:
            _fail()
        _enter_phase(phase_recorder, "account_manifest")
        account_count = _positive_int(
            runtime.count_accounts(snapshot, company)
        )

        preliminary_floor = max(
            company_count,
            active_fiscal_count,
            selected_link_count,
            finance_book_count,
            active_dimension_count,
            len(fiscal_manifest.fiscal_year_applicability),
            account_count,
        )
        manifest_request = GLTrialBalanceReadRequest(
            company=company,
            fiscal_year=first_name,
            from_date=first_start,
            to_date=first_end,
            currency_precision=precision,
            max_accounts=preliminary_floor,
            max_gl_entries=1,
        )
        manifest = _validate_manifest(
            runtime.complete_account_manifest(
                snapshot, company, account_count
            ),
            snapshot=snapshot,
            request=manifest_request,
        )
        if len(manifest.account_ids) != account_count:
            _fail()
        root_count = _positive_int(len(manifest.root_account_ids))
        source_floors = {
            "company_rows": company_count,
            "active_fiscal_year_rows": active_fiscal_count,
            "fiscal_year_company_rows": selected_link_count,
            "finance_book_rows": finance_book_count,
            "active_dimension_rows": active_dimension_count,
            "fiscal_applicability_rows": len(
                fiscal_manifest.fiscal_year_applicability
            ),
            "account_manifest_ids": len(manifest.account_ids),
            "root_manifest_ids": root_count,
            "account_rows": account_count,
            "final_manifest_ids": len(manifest.account_ids),
            "final_root_ids": root_count,
            "final_fiscal_applicability_rows": len(
                fiscal_manifest.fiscal_year_applicability
            ),
        }
        if tuple(source_floors) != _SOURCE_GROUPS:
            _fail()
        max_accounts = max(source_floors.values())

        _enter_phase(phase_recorder, "gl_cohort")
        gl_counts = [
            runtime.count_gl_entries(
                snapshot,
                company,
                fiscal_end,
                default_finance_book,
            )
            for _name, _start, fiscal_end in fiscal_rows
        ]
        max_gl_entries = max(gl_counts)
        _enter_phase(phase_recorder, "statement_schema")
        statement_ceiling = runtime.statement_ceiling(snapshot)
        database_shape = runtime.numeric_shape(snapshot)
        identifier_envelopes = runtime.identifier_envelopes(
            snapshot
        )

        response_measurements: list[Mapping[str, object]] = []
        for fiscal_name, fiscal_start, fiscal_end in fiscal_rows:
            adapter_request = GLTrialBalanceReadRequest(
                company=company,
                fiscal_year=fiscal_name,
                from_date=fiscal_start,
                to_date=fiscal_end,
                currency_precision=precision,
                max_accounts=max_accounts,
                max_gl_entries=max(max_gl_entries, 1),
            )
            _enter_phase(phase_recorder, "accounting_read")
            trial_balance = _read_with_snapshot(
                adapter_request,
                runtime,
                snapshot,
                authority.user,
            )
            _enter_phase(phase_recorder, "canonical_size")
            response_measurements.append(
                _response_measurement(
                    result=trial_balance,
                    request=GLTrialBalanceServiceRequest(
                        company=company,
                        fiscal_year=fiscal_name,
                        from_date=fiscal_start,
                        to_date=fiscal_end,
                    ),
                    max_accounts=max_accounts,
                    max_gl_entries=max_gl_entries,
                    numeric_precision=database_shape[
                        "numeric_precision"
                    ],
                    numeric_scale=database_shape[
                        "numeric_scale"
                    ],
                )
            )

        _enter_phase(phase_recorder, "permission_final")
        final_effective = runtime.effective_permission_evidence(
            snapshot
        )
        _validate_effective_permissions(
            final_effective,
            snapshot=snapshot,
            user=authority.user,
            company=company,
        )
        _validate_permissions(runtime, snapshot, authority.user)
        _checkpoint(runtime, snapshot, authority.user, company)
        if (
            final_effective != effective
            or _authority_snapshot() != authority
        ):
            _fail()

        result = _CompanyMeasurement(
            source_floors=source_floors,
            max_gl_entries=max_gl_entries,
            fiscal_endpoints=len(fiscal_rows),
            minimum_fiscal_start=min(
                item[1] for item in fiscal_rows
            ),
            maximum_fiscal_end=max(
                item[2] for item in fiscal_rows
            ),
            maximum_fiscal_span_days=max(
                (item[2] - item[1]).days + 1
                for item in fiscal_rows
            ),
            precision=precision,
            statement_ceiling=statement_ceiling,
            database_shape=database_shape,
            identifier_envelopes=identifier_envelopes,
            byte_evidence=_aggregate_response_measurements(
                response_measurements
            ),
            elapsed_microseconds=0,
        )
    except Exception:
        failed = True
        if phase_recorder is not None:
            failure_phase = phase_recorder.phase
    if snapshot is not None:
        try:
            _enter_phase(phase_recorder, "snapshot_finalize")
            runtime.close_read_snapshot(snapshot)
            runtime.close_read_snapshot(snapshot)
        except Exception:
            failed = True
            if failure_phase is None:
                failure_phase = "snapshot_finalize"
    if failed or result is None:
        if phase_recorder is not None:
            phase_recorder.enter(failure_phase or "internal")
        _fail()
    _enter_phase(phase_recorder, "canonical_size")
    return _CompanyMeasurement(
        source_floors=result.source_floors,
        max_gl_entries=result.max_gl_entries,
        fiscal_endpoints=result.fiscal_endpoints,
        minimum_fiscal_start=result.minimum_fiscal_start,
        maximum_fiscal_end=result.maximum_fiscal_end,
        maximum_fiscal_span_days=result.maximum_fiscal_span_days,
        precision=result.precision,
        statement_ceiling=result.statement_ceiling,
        database_shape=result.database_shape,
        identifier_envelopes=result.identifier_envelopes,
        byte_evidence=result.byte_evidence,
        elapsed_microseconds=_elapsed_microseconds(started_ns),
    )


def _result_document(
    *,
    authority: _AuthorityEvidence,
    runtime_policy: GLTrialBalanceRuntimePolicy,
    measurements: Sequence[_CompanyMeasurement],
    started_ns: int,
) -> dict[str, object]:
    if not measurements or len(measurements) != len(
        authority.companies
    ):
        _fail()
    precisions = {item.precision for item in measurements}
    statement_states = {
        tuple(sorted(item.statement_ceiling.items()))
        for item in measurements
    }
    database_shapes = {
        tuple(sorted(item.database_shape.items()))
        for item in measurements
    }
    identifier_shapes = {
        json.dumps(
            item.identifier_envelopes,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        for item in measurements
    }
    if (
        len(precisions) != 1
        or len(statement_states) != 1
        or len(database_shapes) != 1
        or len(identifier_shapes) != 1
    ):
        _fail()

    source_floors = {
        key: max(
            _nonnegative_int(item.source_floors[key])
            for item in measurements
        )
        for key in _SOURCE_GROUPS
    }
    byte_values = [
        item.byte_evidence for item in measurements
    ]
    byte_evidence = _aggregate_response_measurements(
        [
            {
                "request_envelope_bytes": item[
                    "request_envelope_max_bytes"
                ],
                "response_metadata_bytes": item[
                    "response_metadata_max_bytes"
                ],
                "response_bytes": item[
                    "current_response_floor_bytes"
                ],
                "line_count": item[
                    "current_response_floor_line_count"
                ],
                "max_observed_depth": item[
                    "max_observed_depth"
                ],
                "max_observed_depth_width": item[
                    "max_observed_depth_width"
                ],
                "max_identifier_utf8_bytes_observed": item[
                    "max_identifier_utf8_bytes_observed"
                ],
                "max_identifier_escape_extra_bytes_observed": item[
                    "max_identifier_escape_extra_bytes_observed"
                ],
                "max_parent_identifier_utf8_bytes_observed": item[
                    "max_parent_identifier_utf8_bytes_observed"
                ],
                "max_fixed_decimal_bytes_observed": item[
                    "max_fixed_decimal_bytes_observed"
                ],
                "aggregation_digit_growth": item[
                    "aggregation_digit_growth"
                ],
                "fixed_decimal_width_bound": item[
                    "fixed_decimal_width_bound"
                ],
            }
            for item in byte_values
        ]
    )
    database_shape = dict(measurements[0].database_shape)
    statement = dict(measurements[0].statement_ceiling)
    document = {
        "schema_version": _EVIDENCE_SCHEMA_VERSION,
        "state": "evidence_ready",
        "boundary": {
            "read_only": True,
            "evidence_only": True,
            "production_limit_policy_selected": False,
            "production_limit_policy_injected": False,
            "environment_compatibility_policy_required": True,
            "accounting_execution_enabled": False,
            "identities_returned": False,
        },
        "authority": {
            "session_stable": True,
            "accounts_manager": True,
            "privileged_roles_absent": True,
            "explicit_company_permissions": True,
            "restrictive_permissions_absent": True,
            "nine_permissions": True,
            "permission_scope_stable": True,
            "permitted_company_count": len(authority.companies),
        },
        "environment": {
            "driver": runtime_policy.expected_driver,
            "driver_policy_match": True,
            "driver_version_policy_match": True,
            "server_version_policy_match": True,
            **statement,
        },
        "precision": {
            "resulting_currency_precision": next(
                iter(precisions)
            ),
            "system_settings_agreement": True,
            "effective_debit_agreement": True,
            "effective_credit_agreement": True,
            "currency_rounding_agreement": True,
            "all_company_agreement": True,
            "base_currency_present_all": True,
        },
        "accounting_shape": {
            "default_finance_book_present_all": True,
            "applicable_fiscal_state_valid": True,
            "active_dimensions_zero": True,
            "complete_hierarchy": True,
            "all_gl_accounts_in_manifest": True,
            "eligible_cohort_nonzero_cancelled_rows": 0,
            "finance_book_cohort_exact": True,
            "opening_history_available": True,
        },
        "current_floors": {
            **source_floors,
            "max_accounts": max(source_floors.values()),
            "max_gl_entries": max(
                item.max_gl_entries for item in measurements
            ),
            "companies_measured": len(measurements),
            "fiscal_endpoints_measured": sum(
                item.fiscal_endpoints for item in measurements
            ),
        },
        "date_scope": {
            "minimum_supported_fiscal_start": min(
                item.minimum_fiscal_start for item in measurements
            ).isoformat(),
            "maximum_supported_fiscal_end": max(
                item.maximum_fiscal_end for item in measurements
            ).isoformat(),
            "maximum_inclusive_fiscal_span_days": max(
                item.maximum_fiscal_span_days
                for item in measurements
            ),
            "from_lte_to": True,
            "opening_history_available": True,
        },
        "byte_evidence": {
            "canonical_sorted_compact_json": True,
            "ensure_ascii_false": True,
            "utf8": True,
            "metadata_terminal_lf": False,
            "response_terminal_lf_count": 1,
            "hierarchy_in_metadata": False,
            **byte_evidence,
            **database_shape,
            "identifier_envelopes": dict(
                measurements[0].identifier_envelopes
            ),
            "current_response_basis": (
                "full_fiscal_year_each_applicable_endpoint"
            ),
            "structural_maximum_state": "unproven",
            "structural_maximum_bytes": None,
        },
    }
    collector_elapsed = _elapsed_microseconds(started_ns)
    document["timing"] = {
        "unit": "microseconds",
        "collector_elapsed": collector_elapsed,
        "per_company": [
            {
                "ordinal": index,
                "elapsed": item.elapsed_microseconds,
            }
            for index, item in enumerate(
                measurements, start=1
            )
        ],
        "known_request_ceiling": _REQUEST_CEILING_MICROSECONDS,
        "collector_below_known_request_ceiling": (
            collector_elapsed < _REQUEST_CEILING_MICROSECONDS
        ),
        "full_request_completion_state": "unproven",
    }
    return document


def _execute_policy_evidence(
    *,
    method_path: str,
    phase_recorder: _PhaseRecorder | None,
    require_diagnostic_authority: bool,
) -> tuple[dict[str, object] | None, str | None, bool, bool]:
    started_ns = 0
    local: object | None = None
    message_log: list[object] | None = None
    original_messages: tuple[object, ...] = ()
    response: dict[str, object] | None = None
    failed = False
    failure_phase: str | None = None
    phase_visible = not require_diagnostic_authority
    try:
        _enter_phase(phase_recorder, "request_boundary")
        started_ns = time.monotonic_ns()
        local, message_log, original_messages = _message_log()
        if require_diagnostic_authority:
            _diagnostic_caller_authorized()
            phase_visible = True
            _enter_phase(phase_recorder, "message_log_integrity")
            if (
                getattr(local, "message_log", None) is not message_log
                or tuple(message_log) != original_messages
            ):
                _fail()
        _enter_phase(phase_recorder, "environment_policy")
        runtime_policy = _request_policy(method_path=method_path)
        _enter_phase(phase_recorder, "authority_initial")
        authority = _authority_snapshot()
        measurements = [
            _collect_company(
                authority=authority,
                company=company,
                runtime_policy=runtime_policy,
                phase_recorder=phase_recorder,
            )
            for company in authority.companies
        ]
        _enter_phase(phase_recorder, "authority_final")
        if _authority_snapshot() != authority:
            _fail()
        _enter_phase(phase_recorder, "message_log_integrity")
        if (
            getattr(local, "message_log", None) is not message_log
            or tuple(message_log) != original_messages
        ):
            _fail()
        _enter_phase(phase_recorder, "result_build")
        response = _result_document(
            authority=authority,
            runtime_policy=runtime_policy,
            measurements=measurements,
            started_ns=started_ns,
        )
    except Exception:
        failed = True
        if phase_recorder is not None:
            failure_phase = phase_recorder.phase
    if failed or response is None:
        cleanup_safe = local is not None and message_log is not None
        if local is not None and message_log is not None:
            cleanup_safe = _restore_message_log(
                local, message_log, original_messages
            )
        if (
            not cleanup_safe
            and phase_recorder is not None
            and failure_phase is None
        ):
            phase_recorder.enter("cleanup")
            failure_phase = phase_recorder.phase
        return response, failure_phase, cleanup_safe, phase_visible
    return response, None, True, phase_visible


@frappe.whitelist(allow_guest=False, methods=["POST"])
def collect_gl_trial_balance_policy_evidence():
    """Return sanitized current-floor evidence from the active session."""

    response, _phase, _cleanup_safe, _phase_visible = _execute_policy_evidence(
        method_path=_METHOD_PATH,
        phase_recorder=None,
        require_diagnostic_authority=False,
    )
    if response is None:
        raise GLTrialBalancePolicyEvidenceError()
    return response


@frappe.whitelist(allow_guest=False, methods=["POST"])
def diagnose_gl_trial_balance_policy_evidence_failure_phase():
    """Return one closed, non-identifying collector phase only."""

    enabled = False
    try:
        _diagnostic_enabled()
        enabled = True
    except Exception:
        pass
    if not enabled:
        raise GLTrialBalancePolicyEvidenceError()

    recorder = _PhaseRecorder()
    response, failure_phase, cleanup_safe, phase_visible = (
        _execute_policy_evidence(
            method_path=_DIAGNOSTIC_METHOD_PATH,
            phase_recorder=recorder,
            require_diagnostic_authority=True,
        )
    )
    if not cleanup_safe or not phase_visible:
        raise GLTrialBalancePolicyEvidenceError()
    if response is not None:
        return {"code": "diagnostic_complete", "phase": "complete"}
    if (
        failure_phase not in _DIAGNOSTIC_PHASES
        or failure_phase == "complete"
    ):
        raise GLTrialBalancePolicyEvidenceError()
    return {"code": _GENERIC_ERROR, "phase": failure_phase}
