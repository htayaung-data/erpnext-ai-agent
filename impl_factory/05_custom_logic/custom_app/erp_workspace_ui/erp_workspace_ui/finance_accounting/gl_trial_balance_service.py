"""Internal canonical response boundary for permissioned GL / Trial Balance reads.

This module deliberately has no Frappe import, default runtime, production
policy, HTTP exposure, mutation, or accounting-execution authority.  The
permission adapter and its injected runtime remain the sole owners of source
authorization and accounting-result construction.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from .gl_trial_balance_adapter import (
    GLTrialBalanceReadRequest,
    PermissionedSnapshotRuntime,
    read_gl_trial_balance,
)
from .gl_trial_balance_core import (
    AccountingAmounts,
    TrialBalanceLine,
    TrialBalanceResult,
    TrialBalanceScope,
)


__all__ = [
    "GLTrialBalanceServiceError",
    "GLTrialBalanceServicePolicy",
    "GLTrialBalanceServiceRequest",
    "build_canonical_gl_trial_balance_response",
]


_GENERIC_ERROR = "finance_read_unavailable"
_SCHEMA_VERSION = "finance-gl-trial-balance.internal.v2"
_NAMED_FINANCE_BOOK_SCOPE = (
    "company_default",
    "blank_unbooked",
    "null_unbooked",
)
_UNBOOKED_FINANCE_BOOK_SCOPE = (
    "blank_unbooked",
    "null_unbooked",
)
_ROOT_TYPES = frozenset({"Asset", "Liability", "Equity", "Income", "Expense"})


class GLTrialBalanceServiceError(RuntimeError):
    """One stable, non-identifying failure for the internal service boundary."""

    code = _GENERIC_ERROR

    def __init__(self) -> None:
        super().__init__(_GENERIC_ERROR)


@dataclass(frozen=True, slots=True)
class GLTrialBalanceServiceRequest:
    """Business scope only; callers cannot provide resource or numeric policy."""

    company: str
    fiscal_year: str
    from_date: date
    to_date: date


@dataclass(frozen=True, slots=True)
class GLTrialBalanceServicePolicy:
    """Required trusted policy with no production defaults."""

    currency_precision: int
    max_accounts: int
    max_gl_entries: int
    max_metadata_bytes: int
    max_response_bytes: int


def _fail() -> None:
    raise ValueError(_GENERIC_ERROR)


def _strict_text(value: object) -> str:
    if (
        type(value) is not str
        or not value
        or value != value.strip()
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        _fail()
    return value


def _positive_integer(value: object) -> int:
    if type(value) is not int or value <= 0:
        _fail()
    return value


def _validate_request(value: object) -> GLTrialBalanceServiceRequest:
    if type(value) is not GLTrialBalanceServiceRequest:
        _fail()
    _strict_text(value.company)
    _strict_text(value.fiscal_year)
    if type(value.from_date) is not date or type(value.to_date) is not date:
        _fail()
    if value.from_date > value.to_date:
        _fail()
    return value


def _validate_policy(value: object) -> GLTrialBalanceServicePolicy:
    if type(value) is not GLTrialBalanceServicePolicy:
        _fail()
    if type(value.currency_precision) is not int or value.currency_precision < 0:
        _fail()
    _positive_integer(value.max_accounts)
    _positive_integer(value.max_gl_entries)
    _positive_integer(value.max_metadata_bytes)
    _positive_integer(value.max_response_bytes)
    if value.max_metadata_bytes > value.max_response_bytes:
        _fail()
    # Structural containment only.  Exact production values remain injected.
    if value.currency_precision + 4 > value.max_response_bytes:
        _fail()
    return value


def _fixed_decimal(value: object, precision: int, response_cap: int) -> str:
    if type(value) is not Decimal or not value.is_finite() or value.is_signed():
        _fail()
    _, digits, exponent = value.as_tuple()
    if len(digits) > response_cap:
        _fail()
    integer_digits = 1
    if not value.is_zero():
        integer_digits = max(len(digits) + exponent, 1)
    rendered_size = integer_digits + (precision + 1 if precision else 0)
    if rendered_size > response_cap:
        _fail()
    rendered = format(value, f".{precision}f")
    if "e" in rendered.lower() or Decimal(rendered) != value:
        _fail()
    if len(rendered.encode("ascii")) > response_cap:
        _fail()
    return rendered


def _amounts_payload(
    value: object, *, precision: int, response_cap: int
) -> dict[str, str]:
    if type(value) is not AccountingAmounts:
        _fail()
    return {
        "closing_credit": _fixed_decimal(
            value.closing_credit, precision, response_cap
        ),
        "closing_debit": _fixed_decimal(value.closing_debit, precision, response_cap),
        "movement_credit": _fixed_decimal(
            value.movement_credit, precision, response_cap
        ),
        "movement_debit": _fixed_decimal(
            value.movement_debit, precision, response_cap
        ),
        "opening_credit": _fixed_decimal(
            value.opening_credit, precision, response_cap
        ),
        "opening_debit": _fixed_decimal(value.opening_debit, precision, response_cap),
    }


def _validate_scope(
    value: object,
    *,
    request: GLTrialBalanceServiceRequest,
    policy: GLTrialBalanceServicePolicy,
) -> TrialBalanceScope:
    if type(value) is not TrialBalanceScope:
        _fail()
    _strict_text(value.company)
    _strict_text(value.base_currency)
    if value.default_finance_book is None:
        if value.finance_book_cohort != _UNBOOKED_FINANCE_BOOK_SCOPE:
            _fail()
    else:
        _strict_text(value.default_finance_book)
        if value.finance_book_cohort != _NAMED_FINANCE_BOOK_SCOPE:
            _fail()
    if value.company != request.company or value.precision != policy.currency_precision:
        _fail()
    if type(value.precision) is not int or value.precision < 0:
        _fail()
    boundaries = (
        value.fiscal_year_start,
        value.fiscal_year_end,
        value.from_date,
        value.to_date,
    )
    if any(type(boundary) is not date for boundary in boundaries):
        _fail()
    if not (
        value.fiscal_year_start
        <= value.from_date
        <= value.to_date
        <= value.fiscal_year_end
    ):
        _fail()
    if value.from_date != request.from_date or value.to_date != request.to_date:
        _fail()
    if type(value.active_dimensions) is not int or value.active_dimensions != 0:
        _fail()
    return value


def _line_payloads(
    value: object,
    *,
    precision: int,
    max_accounts: int,
    response_cap: int,
) -> list[dict[str, object]]:
    if type(value) is not tuple or not value or len(value) > max_accounts:
        _fail()
    payloads: list[dict[str, object]] = []
    prior_lines: dict[str, TrialBalanceLine] = {}
    parent_ids: set[str] = set()
    for line in value:
        if type(line) is not TrialBalanceLine:
            _fail()
        account_id = _strict_text(line.account_id)
        if account_id in prior_lines:
            _fail()
        if line.parent_account_id is not None:
            parent_id = _strict_text(line.parent_account_id)
            parent = prior_lines.get(parent_id)
            if (
                parent is None
                or line.depth != parent.depth + 1
                or line.root_type != parent.root_type
            ):
                _fail()
            parent_ids.add(parent_id)
        elif line.depth != 0:
            _fail()
        if type(line.is_group) is not bool:
            _fail()
        if line.root_type not in _ROOT_TYPES:
            _fail()
        if type(line.depth) is not int or line.depth < 0:
            _fail()
        payloads.append(
            {
                "account_id": account_id,
                "amounts": _amounts_payload(
                    line.amounts, precision=precision, response_cap=response_cap
                ),
                "depth": line.depth,
                "is_group": line.is_group,
                "parent_account_id": line.parent_account_id,
                "root_type": line.root_type,
            }
        )
        prior_lines[account_id] = line
    for account_id, line in prior_lines.items():
        if line.is_group != (account_id in parent_ids):
            _fail()
    return payloads


def _canonical_json_bytes(value: object, *, terminal_lf: bool) -> bytes:
    encoded = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return encoded + (b"\n" if terminal_lf else b"")


def _validate_request_envelope(
    request: GLTrialBalanceServiceRequest,
    *,
    metadata_cap: int,
) -> None:
    envelope = {
        "company": request.company,
        "fiscal_year": request.fiscal_year,
        "from_date": request.from_date.isoformat(),
        "to_date": request.to_date.isoformat(),
    }
    if len(_canonical_json_bytes(envelope, terminal_lf=False)) > metadata_cap:
        _fail()


def _build_response(
    *,
    result: object,
    request: GLTrialBalanceServiceRequest,
    policy: GLTrialBalanceServicePolicy,
) -> bytes:
    if type(result) is not TrialBalanceResult:
        _fail()
    scope = _validate_scope(result.scope, request=request, policy=policy)
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
        "active_dimensions": scope.active_dimensions,
        "base_currency": scope.base_currency,
        "company": scope.company,
        "currency_precision": scope.precision,
        "default_finance_book": scope.default_finance_book,
        "finance_book_scope": list(scope.finance_book_cohort),
        "fiscal_year": request.fiscal_year,
        "fiscal_year_end": scope.fiscal_year_end.isoformat(),
        "fiscal_year_start": scope.fiscal_year_start.isoformat(),
        "from_date": scope.from_date.isoformat(),
        "to_date": scope.to_date.isoformat(),
    }
    metadata = {
        "boundary": boundary,
        "schema_version": _SCHEMA_VERSION,
        "scope": scope_payload,
        "state": "ready",
    }
    if len(_canonical_json_bytes(metadata, terminal_lf=False)) > policy.max_metadata_bytes:
        _fail()
    response = {
        **metadata,
        "lines": _line_payloads(
            result.lines,
            precision=scope.precision,
            max_accounts=policy.max_accounts,
            response_cap=policy.max_response_bytes,
        ),
        "totals": {
            "gross": _amounts_payload(
                result.gross_totals,
                precision=scope.precision,
                response_cap=policy.max_response_bytes,
            ),
            "presentation": _amounts_payload(
                result.presentation_totals,
                precision=scope.precision,
                response_cap=policy.max_response_bytes,
            ),
        },
    }
    encoded = _canonical_json_bytes(response, terminal_lf=True)
    if len(encoded) > policy.max_response_bytes:
        _fail()
    return encoded


def build_canonical_gl_trial_balance_response(
    *,
    request: GLTrialBalanceServiceRequest,
    runtime: PermissionedSnapshotRuntime,
    policy: GLTrialBalanceServicePolicy,
) -> bytes:
    """Return one complete canonical internal payload or one generic failure.

    The adapter remains the sole owner of user, role, Company User Permission,
    document-permission, manifest, snapshot, cancellation, and Finance Book
    enforcement.  This service adds only trusted-policy construction and a
    closed deterministic serialization boundary.
    """

    response: bytes | None = None
    failed = False
    try:
        validated_policy = _validate_policy(policy)
        validated_request = _validate_request(request)
        _validate_request_envelope(
            validated_request,
            metadata_cap=validated_policy.max_metadata_bytes,
        )
        if runtime is None:
            _fail()
        adapter_request = GLTrialBalanceReadRequest(
            company=validated_request.company,
            fiscal_year=validated_request.fiscal_year,
            from_date=validated_request.from_date,
            to_date=validated_request.to_date,
            currency_precision=validated_policy.currency_precision,
            max_accounts=validated_policy.max_accounts,
            max_gl_entries=validated_policy.max_gl_entries,
        )
        result = read_gl_trial_balance(request=adapter_request, runtime=runtime)
        response = _build_response(
            result=result,
            request=validated_request,
            policy=validated_policy,
        )
    except Exception:
        failed = True
    if failed or response is None:
        # Raised outside the handler so source exceptions are not retained as
        # ``__context__`` and no result fragment can escape.
        raise GLTrialBalanceServiceError()
    return response
