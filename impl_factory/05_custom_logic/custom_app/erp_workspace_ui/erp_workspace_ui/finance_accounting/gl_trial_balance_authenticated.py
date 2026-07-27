"""Authenticated internal bridge for canonical GL / Trial Balance reads.

The bridge binds one active Frappe session, its public role and User Permission
authorities, one already-constructed concrete GL/TB runtime, and injected
runtime/service policies.  It has no HTTP, whitelist, UI, mutation, execution,
or import-time Frappe/database authority.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .gl_trial_balance_frappe_runtime import (
    FrappeGLTrialBalanceRuntime,
    GLTrialBalanceRuntimePolicy,
)
from .gl_trial_balance_service import (
    GLTrialBalanceServicePolicy,
    GLTrialBalanceServiceRequest,
    build_canonical_gl_trial_balance_response,
)


__all__ = [
    "GLTrialBalanceAuthenticationError",
    "read_authenticated_gl_trial_balance",
]


_GENERIC_ERROR = "finance_read_unavailable"
_PRIVILEGED_ROLES = frozenset(
    {"System Manager", "Administrator", "Bypass Finance Scope"}
)
_RELEVANT_RESTRICTIVE_DOCTYPES = frozenset(
    {
        "Account",
        "Cost Center",
        "Project",
        "Finance Book",
        "Accounting Dimension",
    }
)
_USER_PERMISSION_KEYS = frozenset(
    {"doc", "applicable_for", "is_default", "hide_descendants"}
)


class GLTrialBalanceAuthenticationError(RuntimeError):
    """One stable, non-identifying authenticated-integration failure."""

    code = _GENERIC_ERROR

    def __init__(self) -> None:
        super().__init__(_GENERIC_ERROR)


@dataclass(frozen=True, slots=True)
class _AuthenticationEvidence:
    user: str
    roles: tuple[str, ...]
    company_permissions: tuple[str, ...]


def _fail() -> None:
    raise ValueError(_GENERIC_ERROR)


def _strict_text(value: object, *, allow_empty: bool = False) -> str:
    if type(value) is not str or value != value.strip():
        _fail()
    if not allow_empty and not value:
        _fail()
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        _fail()
    return value


def _flag(value: object) -> int:
    if type(value) is not int or value not in (0, 1):
        _fail()
    return value


def _mapping_or_attribute(value: object, key: str) -> object:
    if isinstance(value, Mapping):
        if key not in value:
            _fail()
        return value[key]
    try:
        return getattr(value, key)
    except Exception:
        _fail()


def _roles(frappe_module: object, user: str) -> tuple[str, ...]:
    getter = getattr(frappe_module, "get_roles")
    if not callable(getter):
        _fail()
    value = getter(user)
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        _fail()
    roles = tuple(_strict_text(role) for role in value)
    if len(set(roles)) != len(roles):
        _fail()
    role_set = set(roles)
    if "Accounts Manager" not in role_set or role_set & _PRIVILEGED_ROLES:
        _fail()
    return tuple(sorted(roles))


def _company_permissions(
    permissions_module: object,
    user: str,
    selected_company: str,
) -> tuple[str, ...]:
    getter = getattr(permissions_module, "get_user_permissions")
    if not callable(getter):
        _fail()
    value = getter(user)
    if not isinstance(value, Mapping):
        _fail()
    company_values: list[str] = []
    seen_rules: set[tuple[object, ...]] = set()
    for raw_allow, raw_entries in value.items():
        allow = _strict_text(raw_allow)
        if isinstance(raw_entries, (str, bytes, bytearray)) or not isinstance(
            raw_entries, Sequence
        ):
            _fail()
        for raw_entry in raw_entries:
            if not isinstance(raw_entry, Mapping) or frozenset(raw_entry) != _USER_PERMISSION_KEYS:
                _fail()
            for_value = _strict_text(raw_entry["doc"])
            applicable_for = raw_entry["applicable_for"]
            if applicable_for is not None:
                applicable_for = _strict_text(applicable_for, allow_empty=True)
            _flag(raw_entry["is_default"])
            hide_descendants = _flag(raw_entry["hide_descendants"])
            applies_to_all = 1 if applicable_for in (None, "") else 0
            identity = (
                allow,
                for_value,
                applicable_for,
                applies_to_all,
                hide_descendants,
            )
            if identity in seen_rules:
                _fail()
            seen_rules.add(identity)
            if allow == "Company":
                if applies_to_all != 1 or hide_descendants != 0:
                    _fail()
                if for_value in company_values:
                    _fail()
                company_values.append(for_value)
            elif (
                allow in _RELEVANT_RESTRICTIVE_DOCTYPES
                or applicable_for in {"Account", "GL Entry"}
            ):
                _fail()
    if not company_values or selected_company not in company_values:
        _fail()
    return tuple(sorted(company_values))


def _authentication_evidence(
    *,
    frappe_module: object,
    permissions_module: object,
    selected_company: str,
) -> _AuthenticationEvidence:
    local = getattr(frappe_module, "local")
    session = getattr(local, "session")
    user = _strict_text(_mapping_or_attribute(session, "user"))
    if user in {"Guest", "Administrator"}:
        _fail()
    return _AuthenticationEvidence(
        user=user,
        roles=_roles(frappe_module, user),
        company_permissions=_company_permissions(
            permissions_module,
            user,
            selected_company,
        ),
    )


def _message_log(frappe_module: object) -> tuple[object, list[object], tuple[object, ...]]:
    local = getattr(frappe_module, "local")
    message_log = getattr(local, "message_log")
    if type(message_log) is not list or message_log:
        _fail()
    return local, message_log, tuple(message_log)


def _restore_message_log(
    local: object,
    message_log: list[object],
    original: tuple[object, ...],
) -> None:
    try:
        message_log[:] = original
        if getattr(local, "message_log", None) is not message_log:
            setattr(local, "message_log", message_log)
    except Exception:
        pass


def _validate_runtime_binding(
    *,
    runtime: object,
    runtime_policy: object,
    frappe_module: object,
    permissions_module: object,
) -> FrappeGLTrialBalanceRuntime:
    if (
        type(runtime) is not FrappeGLTrialBalanceRuntime
        or type(runtime_policy) is not GLTrialBalanceRuntimePolicy
        or getattr(runtime, "_frappe", None) is not frappe_module
        or getattr(runtime, "_permissions", None) is not permissions_module
        or getattr(runtime, "_policy", None) != runtime_policy
        or getattr(runtime, "_context", None) is not None
    ):
        _fail()
    return runtime


def read_authenticated_gl_trial_balance(
    *,
    request: GLTrialBalanceServiceRequest,
    frappe_module: object,
    permissions_module: object,
    runtime: FrappeGLTrialBalanceRuntime,
    runtime_policy: GLTrialBalanceRuntimePolicy,
    service_policy: GLTrialBalanceServicePolicy,
) -> bytes:
    """Return one authenticated canonical response or one generic failure.

    User identity is derived only from the active Frappe session.  The bridge
    performs a strict pre/post authentication check, while the committed
    adapter/runtime remain the final role, Company User Permission, DocType
    permission, snapshot, and accounting authorities.
    """

    local: object | None = None
    message_log: list[object] | None = None
    original_messages: tuple[object, ...] = ()
    response: bytes | None = None
    failed = False
    try:
        if type(request) is not GLTrialBalanceServiceRequest:
            _fail()
        if type(service_policy) is not GLTrialBalanceServicePolicy:
            _fail()
        bound_runtime = _validate_runtime_binding(
            runtime=runtime,
            runtime_policy=runtime_policy,
            frappe_module=frappe_module,
            permissions_module=permissions_module,
        )
        local, message_log, original_messages = _message_log(frappe_module)
        before = _authentication_evidence(
            frappe_module=frappe_module,
            permissions_module=permissions_module,
            selected_company=request.company,
        )
        if _strict_text(bound_runtime.current_user()) != before.user:
            _fail()
        response_candidate = build_canonical_gl_trial_balance_response(
            request=request,
            runtime=bound_runtime,
            policy=service_policy,
        )
        if type(response_candidate) is not bytes or not response_candidate:
            _fail()
        if getattr(bound_runtime, "_context", None) is not None:
            _fail()
        if _strict_text(bound_runtime.current_user()) != before.user:
            _fail()
        after = _authentication_evidence(
            frappe_module=frappe_module,
            permissions_module=permissions_module,
            selected_company=request.company,
        )
        if after != before:
            _fail()
        if getattr(local, "message_log", None) is not message_log:
            _fail()
        if tuple(message_log) != original_messages:
            _fail()
        response = response_candidate
    except Exception:
        failed = True
    if failed or response is None:
        if local is not None and message_log is not None:
            _restore_message_log(local, message_log, original_messages)
        # Raise outside the active handler: no Frappe, permission, runtime,
        # policy, company, or canonical-service exception remains chained.
        raise GLTrialBalanceAuthenticationError()
    return response
