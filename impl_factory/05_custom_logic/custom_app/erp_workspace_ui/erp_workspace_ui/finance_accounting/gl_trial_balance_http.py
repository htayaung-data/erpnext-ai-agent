"""Authenticated same-origin HTTP boundary for canonical GL / Trial Balance reads.

The endpoint is intentionally inactive until an exact deployment policy is
present in ``frappe.local.conf``.  It delegates all permission, company,
snapshot, and accounting authority to the committed authenticated bridge.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import date

import frappe
import frappe.permissions as frappe_permissions

from .gl_trial_balance_authenticated import read_authenticated_gl_trial_balance
from .gl_trial_balance_frappe_runtime import (
    FrappeGLTrialBalanceRuntime,
    GLTrialBalanceRuntimePolicy,
)
from .gl_trial_balance_service import (
    GLTrialBalanceServicePolicy,
    GLTrialBalanceServiceRequest,
)


__all__ = ["GLTrialBalanceHTTPError", "get_gl_trial_balance"]


_GENERIC_ERROR = "finance_read_unavailable"
_METHOD_PATH = (
    "erp_workspace_ui.finance_accounting.gl_trial_balance_http."
    "get_gl_trial_balance"
)
_POLICY_CONF_KEY = "finance_gl_trial_balance_policy"
_INPUT_KEYS = frozenset({"company", "fiscal_year", "from_date", "to_date"})
_RUNTIME_POLICY_KEYS = frozenset(
    {"expected_driver", "expected_driver_version", "expected_server_version"}
)
_SERVICE_POLICY_KEYS = frozenset(
    {
        "currency_precision",
        "max_accounts",
        "max_gl_entries",
        "max_metadata_bytes",
        "max_response_bytes",
    }
)
_TOP_LEVEL_KEYS = frozenset(
    {"boundary", "lines", "schema_version", "scope", "state", "totals"}
)
_BOUNDARY = {
    "accounting_execution_enabled": False,
    "cancellation_control_claimed": False,
    "mutation_enabled": False,
    "party_identifiers_returned": False,
    "period_close_control_claimed": False,
    "read_only": True,
    "source_gl_entries_returned": False,
    "voucher_identifiers_returned": False,
}
_SCOPE_KEYS = frozenset(
    {
        "active_dimensions",
        "base_currency",
        "company",
        "currency_precision",
        "default_finance_book",
        "finance_book_scope",
        "fiscal_year",
        "fiscal_year_end",
        "fiscal_year_start",
        "from_date",
        "to_date",
    }
)
_LINE_KEYS = frozenset(
    {
        "account_id",
        "amounts",
        "depth",
        "is_group",
        "parent_account_id",
        "root_type",
    }
)
_AMOUNT_KEYS = frozenset(
    {
        "closing_credit",
        "closing_debit",
        "movement_credit",
        "movement_debit",
        "opening_credit",
        "opening_debit",
    }
)
_ROOT_TYPES = frozenset({"Asset", "Liability", "Equity", "Income", "Expense"})
_NAMED_FINANCE_BOOK_SCOPE = ["company_default", "blank_unbooked", "null_unbooked"]
_UNBOOKED_FINANCE_BOOK_SCOPE = ["blank_unbooked", "null_unbooked"]


class GLTrialBalanceHTTPError(RuntimeError):
    """One stable non-identifying endpoint failure."""

    code = _GENERIC_ERROR

    def __init__(self) -> None:
        super().__init__(_GENERIC_ERROR)


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


def _mapping_value(value: object, key: str) -> object:
    if isinstance(value, Mapping):
        if key not in value:
            _fail()
        return value[key]
    try:
        return getattr(value, key)
    except Exception:
        _fail()


def _closed_mapping(value: object, keys: frozenset[str]) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or frozenset(value) != keys:
        _fail()
    if any(type(key) is not str for key in value):
        _fail()
    return value


def _session_user() -> str:
    local = getattr(frappe, "local")
    user = _strict_text(_mapping_value(getattr(local, "session"), "user"))
    if user in {"Guest", "Administrator"}:
        _fail()
    return user


def _validate_http_request(
    *, company: object, fiscal_year: object, from_date: object, to_date: object
) -> None:
    local = getattr(frappe, "local")
    request = getattr(local, "request")
    if _strict_text(getattr(request, "method")) != "POST":
        _fail()

    form_dict = getattr(frappe, "form_dict")
    if not isinstance(form_dict, Mapping) or any(
        type(key) is not str for key in form_dict
    ):
        _fail()
    keys = frozenset(form_dict)
    if not _INPUT_KEYS.issubset(keys) or not keys.issubset(_INPUT_KEYS | {"cmd"}):
        _fail()
    if "cmd" in form_dict and form_dict["cmd"] != _METHOD_PATH:
        _fail()
    values = {
        "company": company,
        "fiscal_year": fiscal_year,
        "from_date": from_date,
        "to_date": to_date,
    }
    if any(form_dict[key] != value for key, value in values.items()):
        _fail()


def _parse_date(value: object) -> date:
    text = _strict_text(value)
    if (
        len(text) != 10
        or text[4] != "-"
        or text[7] != "-"
        or not (text[:4] + text[5:7] + text[8:]).isdigit()
    ):
        _fail()
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        _fail()
    if parsed.isoformat() != text:
        _fail()
    return parsed


def _request(
    *, company: object, fiscal_year: object, from_date: object, to_date: object
) -> GLTrialBalanceServiceRequest:
    company_text = _strict_text(company)
    fiscal_year_text = _strict_text(fiscal_year)
    start = _parse_date(from_date)
    end = _parse_date(to_date)
    if start > end:
        _fail()
    return GLTrialBalanceServiceRequest(
        company=company_text,
        fiscal_year=fiscal_year_text,
        from_date=start,
        to_date=end,
    )


def _policy_document() -> tuple[GLTrialBalanceRuntimePolicy, GLTrialBalanceServicePolicy]:
    local = getattr(frappe, "local")
    conf = getattr(local, "conf")
    if isinstance(conf, Mapping):
        document = conf.get(_POLICY_CONF_KEY)
    else:
        getter = getattr(conf, "get", None)
        if not callable(getter):
            _fail()
        document = getter(_POLICY_CONF_KEY)
    policy = _closed_mapping(document, frozenset({"runtime", "service"}))
    runtime_raw = _closed_mapping(policy["runtime"], _RUNTIME_POLICY_KEYS)
    service_raw = _closed_mapping(policy["service"], _SERVICE_POLICY_KEYS)

    runtime_policy = GLTrialBalanceRuntimePolicy(
        expected_driver=_strict_text(runtime_raw["expected_driver"]),
        expected_driver_version=_strict_text(runtime_raw["expected_driver_version"]),
        expected_server_version=_strict_text(runtime_raw["expected_server_version"]),
    )
    currency_precision = service_raw["currency_precision"]
    if type(currency_precision) is not int or currency_precision < 0:
        _fail()
    service_policy = GLTrialBalanceServicePolicy(
        currency_precision=currency_precision,
        max_accounts=_positive_integer(service_raw["max_accounts"]),
        max_gl_entries=_positive_integer(service_raw["max_gl_entries"]),
        max_metadata_bytes=_positive_integer(service_raw["max_metadata_bytes"]),
        max_response_bytes=_positive_integer(service_raw["max_response_bytes"]),
    )
    if (
        service_policy.max_metadata_bytes > service_policy.max_response_bytes
        or service_policy.currency_precision + 4 > service_policy.max_response_bytes
    ):
        _fail()
    return runtime_policy, service_policy


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _fail()
        result[key] = value
    return result


def _reject_number(_value: str) -> object:
    _fail()


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return (
            json.dumps(
                value,
                allow_nan=False,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8", errors="strict")
            + b"\n"
        )
    except (TypeError, UnicodeEncodeError, ValueError):
        _fail()


def _fixed_amount(value: object, precision: int) -> None:
    if type(value) is not str:
        _fail()
    parts = value.split(".")
    if precision == 0:
        if len(parts) != 1:
            _fail()
    elif len(parts) != 2 or len(parts[1]) != precision:
        _fail()
    whole = parts[0]
    if (
        not whole
        or (len(whole) > 1 and whole.startswith("0"))
        or not whole.isascii()
        or not whole.isdigit()
    ):
        _fail()
    if precision and (not parts[1].isascii() or not parts[1].isdigit()):
        _fail()


def _amounts(value: object, precision: int) -> None:
    amounts = _closed_mapping(value, _AMOUNT_KEYS)
    for item in amounts.values():
        _fixed_amount(item, precision)


def _validate_document(
    document: object,
    *,
    request: GLTrialBalanceServiceRequest,
    policy: GLTrialBalanceServicePolicy,
) -> dict[str, object]:
    response = _closed_mapping(document, _TOP_LEVEL_KEYS)
    boundary = _closed_mapping(response["boundary"], frozenset(_BOUNDARY))
    if (
        response["schema_version"] != "finance-gl-trial-balance.internal.v2"
        or response["state"] != "ready"
        or boundary != _BOUNDARY
        or any(type(item) is not bool for item in boundary.values())
    ):
        _fail()

    scope = _closed_mapping(response["scope"], _SCOPE_KEYS)
    if (
        scope["company"] != request.company
        or scope["fiscal_year"] != request.fiscal_year
        or scope["from_date"] != request.from_date.isoformat()
        or scope["to_date"] != request.to_date.isoformat()
        or scope["currency_precision"] != policy.currency_precision
        or type(scope["currency_precision"]) is not int
        or scope["active_dimensions"] != 0
        or type(scope["active_dimensions"]) is not int
    ):
        _fail()
    if scope["default_finance_book"] is None:
        if scope["finance_book_scope"] != _UNBOOKED_FINANCE_BOOK_SCOPE:
            _fail()
    else:
        _strict_text(scope["default_finance_book"])
        if scope["finance_book_scope"] != _NAMED_FINANCE_BOOK_SCOPE:
            _fail()
    for key in (
        "base_currency",
        "fiscal_year_start",
        "fiscal_year_end",
    ):
        _strict_text(scope[key])

    lines = response["lines"]
    if type(lines) is not list or not lines:
        _fail()
    for raw_line in lines:
        line = _closed_mapping(raw_line, _LINE_KEYS)
        _strict_text(line["account_id"])
        parent = line["parent_account_id"]
        if parent is not None:
            _strict_text(parent)
        if type(line["depth"]) is not int or line["depth"] < 0:
            _fail()
        if type(line["is_group"]) is not bool or line["root_type"] not in _ROOT_TYPES:
            _fail()
        _amounts(line["amounts"], policy.currency_precision)

    totals = _closed_mapping(response["totals"], frozenset({"gross", "presentation"}))
    _amounts(totals["gross"], policy.currency_precision)
    _amounts(totals["presentation"], policy.currency_precision)
    return dict(response)


def _canonical_document(
    payload: object,
    *,
    request: GLTrialBalanceServiceRequest,
    policy: GLTrialBalanceServicePolicy,
) -> dict[str, object]:
    if type(payload) is not bytes or not payload or len(payload) > policy.max_response_bytes:
        _fail()
    if payload.startswith(b"\xef\xbb\xbf") or not payload.endswith(b"\n"):
        _fail()
    try:
        document = json.loads(
            payload.decode("utf-8", errors="strict"),
            object_pairs_hook=_unique_object,
            parse_float=_reject_number,
            parse_constant=_reject_number,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError):
        _fail()
    response = _validate_document(document, request=request, policy=policy)
    if _canonical_json_bytes(response) != payload:
        _fail()
    return response


@frappe.whitelist(allow_guest=False, methods=["POST"])
def get_gl_trial_balance(company=None, fiscal_year=None, from_date=None, to_date=None):
    """Return one permissioned canonical GL/TB response for the active session."""

    response: dict[str, object] | None = None
    failed = False
    try:
        _validate_http_request(
            company=company,
            fiscal_year=fiscal_year,
            from_date=from_date,
            to_date=to_date,
        )
        _session_user()
        service_request = _request(
            company=company,
            fiscal_year=fiscal_year,
            from_date=from_date,
            to_date=to_date,
        )
        runtime_policy, service_policy = _policy_document()
        runtime = FrappeGLTrialBalanceRuntime(
            frappe_module=frappe,
            permissions_module=frappe_permissions,
            policy=runtime_policy,
        )
        payload = read_authenticated_gl_trial_balance(
            request=service_request,
            frappe_module=frappe,
            permissions_module=frappe_permissions,
            runtime=runtime,
            runtime_policy=runtime_policy,
            service_policy=service_policy,
        )
        response = _canonical_document(
            payload,
            request=service_request,
            policy=service_policy,
        )
    except Exception:
        failed = True
    if failed or response is None:
        raise GLTrialBalanceHTTPError()
    return response
