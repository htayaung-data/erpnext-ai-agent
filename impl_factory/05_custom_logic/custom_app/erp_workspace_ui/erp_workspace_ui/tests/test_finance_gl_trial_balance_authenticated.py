"""Isolated tests for the authenticated internal GL/TB bridge."""

from __future__ import annotations

import builtins
import hashlib
import inspect
import sys
import types
import unittest
from dataclasses import replace
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from erp_workspace_ui.finance_accounting import gl_trial_balance_authenticated as bridge
from erp_workspace_ui.finance_accounting.gl_trial_balance_authenticated import (
    GLTrialBalanceAuthenticationError,
    read_authenticated_gl_trial_balance,
)
from erp_workspace_ui.finance_accounting.gl_trial_balance_core import (
    AccountingAmounts,
    TrialBalanceLine,
    TrialBalanceResult,
    TrialBalanceScope,
)
from erp_workspace_ui.finance_accounting.gl_trial_balance_frappe_runtime import (
    FrappeGLTrialBalanceRuntime,
    GLTrialBalanceRuntimePolicy,
)
from erp_workspace_ui.finance_accounting.gl_trial_balance_service import (
    GLTrialBalanceServicePolicy,
    GLTrialBalanceServiceRequest,
)


USER = "accounts.manager@example.test"
COMPANY = "COMPANY_A"
CANONICAL = b'{"schema_version":"finance-gl-trial-balance.internal.v2"}\n'
_UNSET = object()


def _company_rule(
    company: str,
    *,
    applicable_for: object = None,
    is_default: object = 1,
    hide_descendants: object = 0,
) -> dict[str, object]:
    return {
        "doc": company,
        "applicable_for": applicable_for,
        "is_default": is_default,
        "hide_descendants": hide_descendants,
    }


class _Frappe:
    def __init__(self) -> None:
        self.local = types.SimpleNamespace(
            session={"user": USER},
            message_log=[],
        )
        self.roles: object = ["Accounts Manager"]
        self.role_calls: list[str] = []

    def get_roles(self, user: str) -> object:
        self.role_calls.append(user)
        value = self.roles(user) if callable(self.roles) else self.roles
        if isinstance(value, Exception):
            raise value
        return value


class _Permissions:
    def __init__(self) -> None:
        self.value: object = {"Company": [_company_rule(COMPANY)]}
        self.calls: list[str] = []

    def get_user_permissions(self, user: str) -> object:
        self.calls.append(user)
        value = self.value(user) if callable(self.value) else self.value
        if isinstance(value, Exception):
            raise value
        return value


def _zero_amounts() -> AccountingAmounts:
    zero = Decimal("0.00")
    return AccountingAmounts(zero, zero, zero, zero, zero, zero)


def _canonical_result(*, unbooked_only: bool = False) -> TrialBalanceResult:
    scope = TrialBalanceScope(
        company=COMPANY,
        base_currency="MMK",
        precision=2,
        fiscal_year_start=date(2026, 1, 1),
        fiscal_year_end=date(2026, 12, 31),
        from_date=date(2026, 1, 1),
        to_date=date(2026, 12, 31),
        default_finance_book=None if unbooked_only else "DEFAULT_BOOK",
        finance_book_cohort=(
            ("blank_unbooked", "null_unbooked")
            if unbooked_only
            else (
                "company_default",
                "blank_unbooked",
                "null_unbooked",
            )
        ),
        active_dimensions=0,
    )
    zero = _zero_amounts()
    lines = (
        TrialBalanceLine("1000 - Assets", None, True, "Asset", 0, zero),
        TrialBalanceLine(
            "1110 - Cash", "1000 - Assets", False, "Asset", 1, zero
        ),
        TrialBalanceLine(
            "2000 - Liabilities", None, True, "Liability", 0, zero
        ),
        TrialBalanceLine(
            "2110 - Payables",
            "2000 - Liabilities",
            False,
            "Liability",
            1,
            zero,
        ),
    )
    return TrialBalanceResult(
        scope=scope,
        lines=lines,
        gross_totals=zero,
        presentation_totals=zero,
    )


def _request(company: str = COMPANY) -> GLTrialBalanceServiceRequest:
    return GLTrialBalanceServiceRequest(
        company=company,
        fiscal_year="FY-2026",
        from_date=date(2026, 1, 1),
        to_date=date(2026, 12, 31),
    )


def _runtime_policy(**changes: object) -> GLTrialBalanceRuntimePolicy:
    values: dict[str, object] = {
        "expected_driver": "pymysql",
        "expected_driver_version": "1.1.2",
        "expected_server_version": "10.11.18-MariaDB-test",
    }
    values.update(changes)
    return GLTrialBalanceRuntimePolicy(**values)  # type: ignore[arg-type]


def _service_policy(**changes: object) -> GLTrialBalanceServicePolicy:
    values: dict[str, object] = {
        "currency_precision": 2,
        "max_accounts": 100,
        "max_gl_entries": 1000,
        "max_metadata_bytes": 4096,
        "max_response_bytes": 65536,
    }
    values.update(changes)
    return GLTrialBalanceServicePolicy(**values)  # type: ignore[arg-type]


def _runtime(
    frappe: _Frappe,
    permissions: _Permissions,
    policy: GLTrialBalanceRuntimePolicy,
) -> FrappeGLTrialBalanceRuntime:
    return FrappeGLTrialBalanceRuntime(
        frappe_module=frappe,
        permissions_module=permissions,
        policy=policy,
        distribution_version=lambda _: "1.1.2",
    )


class AuthenticatedGLTrialBalanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.frappe = _Frappe()
        self.permissions = _Permissions()
        self.runtime_policy = _runtime_policy()
        self.service_policy = _service_policy()
        self.runtime = _runtime(
            self.frappe,
            self.permissions,
            self.runtime_policy,
        )

    def _read(
        self,
        *,
        request: object = _UNSET,
        frappe_module: object = _UNSET,
        permissions_module: object = _UNSET,
        runtime: object = _UNSET,
        runtime_policy: object = _UNSET,
        service_policy: object = _UNSET,
    ) -> bytes:
        request = _request() if request is _UNSET else request
        frappe_module = self.frappe if frappe_module is _UNSET else frappe_module
        permissions_module = (
            self.permissions
            if permissions_module is _UNSET
            else permissions_module
        )
        runtime = self.runtime if runtime is _UNSET else runtime
        runtime_policy = (
            self.runtime_policy if runtime_policy is _UNSET else runtime_policy
        )
        service_policy = (
            self.service_policy if service_policy is _UNSET else service_policy
        )
        return read_authenticated_gl_trial_balance(
            request=request,
            frappe_module=frappe_module,
            permissions_module=permissions_module,
            runtime=runtime,
            runtime_policy=runtime_policy,
            service_policy=service_policy,
        )

    def _call(
        self,
        *,
        request: object = _UNSET,
        frappe_module: object = _UNSET,
        permissions_module: object = _UNSET,
        runtime: object = _UNSET,
        runtime_policy: object = _UNSET,
        service_policy: object = _UNSET,
    ) -> tuple[bytes, object]:
        with patch.object(
            bridge,
            "build_canonical_gl_trial_balance_response",
            return_value=CANONICAL,
        ) as canonical:
            response = self._read(
                request=request,
                frappe_module=frappe_module,
                permissions_module=permissions_module,
                runtime=runtime,
                runtime_policy=runtime_policy,
                service_policy=service_policy,
            )
        return response, canonical

    def _assert_generic(self, function) -> GLTrialBalanceAuthenticationError:
        with self.assertRaises(GLTrialBalanceAuthenticationError) as captured:
            function()
        error = captured.exception
        self.assertEqual(str(error), "finance_read_unavailable")
        self.assertEqual(error.code, "finance_read_unavailable")
        self.assertIsNone(error.__cause__)
        self.assertIsNone(error.__context__)
        return error

    def _assert_denied_before_canonical(self, **kwargs: object) -> None:
        with patch.object(
            bridge, "build_canonical_gl_trial_balance_response"
        ) as canonical:
            self._assert_generic(lambda: self._read(**kwargs))
        canonical.assert_not_called()

    def test_authenticated_manager_invokes_canonical_service_exactly_once(self) -> None:
        response, canonical = self._call()
        self.assertEqual(response, CANONICAL)
        canonical.assert_called_once_with(
            request=_request(),
            runtime=self.runtime,
            policy=self.service_policy,
        )
        self.assertEqual(self.frappe.role_calls, [USER, USER])
        self.assertEqual(self.permissions.calls, [USER, USER])
        self.assertEqual(self.frappe.local.message_log, [])

    def test_real_canonical_service_composition_has_frozen_output(self) -> None:
        with patch(
            "erp_workspace_ui.finance_accounting.gl_trial_balance_service."
            "read_gl_trial_balance",
            return_value=_canonical_result(),
        ) as adapter:
            response = self._read()
        adapter.assert_called_once()
        self.assertTrue(response.endswith(b"\n"))
        self.assertEqual(
            hashlib.sha256(
                response.replace(
                    b"finance-gl-trial-balance.internal.v2",
                    b"finance-gl-trial-balance.internal.v1",
                )
            ).hexdigest(),
            "6d324fdaf19e1c1fb3d8c4178cd8529e422b7bcaa73df633650edeb6052a112a",
        )
        self.assertIn(
            b'"schema_version":"finance-gl-trial-balance.internal.v2"', response
        )

    def test_real_service_accepts_unbooked_v2_and_rejects_cross_mode_scope(self) -> None:
        with patch(
            "erp_workspace_ui.finance_accounting.gl_trial_balance_service."
            "read_gl_trial_balance",
            return_value=_canonical_result(unbooked_only=True),
        ):
            response = self._read()
        self.assertIn(b'"default_finance_book":null', response)
        self.assertIn(
            b'"finance_book_scope":["blank_unbooked","null_unbooked"]',
            response,
        )
        self.assertNotIn(b"company_default", response)

        malformed_scope = replace(
            _canonical_result(unbooked_only=True).scope,
            finance_book_cohort=(
                "company_default",
                "blank_unbooked",
                "null_unbooked",
            ),
        )
        with patch(
            "erp_workspace_ui.finance_accounting.gl_trial_balance_service."
            "read_gl_trial_balance",
            return_value=replace(
                _canonical_result(unbooked_only=True), scope=malformed_scope
            ),
        ):
            self._assert_generic(lambda: self._read())

    def test_active_session_is_the_only_user_authority(self) -> None:
        signature = inspect.signature(read_authenticated_gl_trial_balance)
        self.assertNotIn("user", signature.parameters)
        self.assertEqual(
            set(signature.parameters),
            {
                "request",
                "frappe_module",
                "permissions_module",
                "runtime",
                "runtime_policy",
                "service_policy",
            },
        )
        for parameter in signature.parameters.values():
            self.assertEqual(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
            self.assertIs(parameter.default, inspect.Parameter.empty)
        self._call()
        self.assertEqual(set(self.frappe.role_calls), {USER})
        self.assertEqual(set(self.permissions.calls), {USER})

    def test_guest_and_administrator_are_denied_before_canonical_service(self) -> None:
        for user in ("Guest", "Administrator"):
            with self.subTest(user=user):
                self.setUp()
                self.frappe.local.session["user"] = user
                with patch.object(
                    bridge, "build_canonical_gl_trial_balance_response"
                ) as canonical:
                    self._assert_generic(
                        lambda: read_authenticated_gl_trial_balance(
                            request=_request(),
                            frappe_module=self.frappe,
                            permissions_module=self.permissions,
                            runtime=self.runtime,
                            runtime_policy=self.runtime_policy,
                            service_policy=self.service_policy,
                        )
                    )
                canonical.assert_not_called()

    def test_wrong_role_and_privileged_mixtures_are_denied(self) -> None:
        invalid_roles = (
            [],
            ["Accounts User"],
            ["Auditor"],
            ["Accounts Manager", "System Manager"],
            ["Accounts Manager", "Administrator"],
            ["Accounts Manager", "Bypass Finance Scope"],
            ["Accounts Manager", "Accounts Manager"],
        )
        for roles in invalid_roles:
            with self.subTest(roles=roles):
                self.setUp()
                self.frappe.roles = roles
                with patch.object(
                    bridge, "build_canonical_gl_trial_balance_response"
                ) as canonical:
                    self._assert_generic(
                        lambda: read_authenticated_gl_trial_balance(
                            request=_request(),
                            frappe_module=self.frappe,
                            permissions_module=self.permissions,
                            runtime=self.runtime,
                            runtime_policy=self.runtime_policy,
                            service_policy=self.service_policy,
                        )
                    )
                canonical.assert_not_called()

    def test_selected_company_mismatch_and_absent_permission_are_denied(self) -> None:
        invalid = (
            {},
            {"Company": []},
            {"Company": [_company_rule("COMPANY_B")]},
        )
        for permissions in invalid:
            with self.subTest(permissions=permissions):
                self.setUp()
                self.permissions.value = permissions
                with patch.object(
                    bridge, "build_canonical_gl_trial_balance_response"
                ) as canonical:
                    self._assert_generic(
                        lambda: read_authenticated_gl_trial_balance(
                            request=_request(),
                            frappe_module=self.frappe,
                            permissions_module=self.permissions,
                            runtime=self.runtime,
                            runtime_policy=self.runtime_policy,
                            service_policy=self.service_policy,
                        )
                    )
                canonical.assert_not_called()

    def test_multiple_company_permissions_require_exact_selected_membership(self) -> None:
        self.permissions.value = {
            "Company": [_company_rule(COMPANY), _company_rule("COMPANY_B")]
        }
        response, _ = self._call()
        self.assertEqual(response, CANONICAL)
        self.setUp()
        self.permissions.value = {
            "Company": [_company_rule(COMPANY), _company_rule("COMPANY_B")]
        }
        with patch.object(
            bridge, "build_canonical_gl_trial_balance_response"
        ) as canonical:
            self._assert_generic(
                lambda: read_authenticated_gl_trial_balance(
                    request=_request("COMPANY_C"),
                    frappe_module=self.frappe,
                    permissions_module=self.permissions,
                    runtime=self.runtime,
                    runtime_policy=self.runtime_policy,
                    service_policy=self.service_policy,
                )
            )
        canonical.assert_not_called()

    def test_restrictive_company_and_relevant_user_permissions_are_denied(self) -> None:
        invalid = (
            {"Company": [_company_rule(COMPANY, applicable_for="Account")]},
            {"Company": [_company_rule(COMPANY, hide_descendants=1)]},
            {
                "Company": [_company_rule(COMPANY)],
                "Account": [_company_rule("ACC-SECRET")],
            },
            {
                "Company": [_company_rule(COMPANY)],
                "Customer": [_company_rule("CUST", applicable_for="GL Entry")],
            },
            {
                "Company": [_company_rule(COMPANY), _company_rule(COMPANY)]
            },
        )
        for permissions in invalid:
            with self.subTest(permissions=permissions):
                self.setUp()
                self.permissions.value = permissions
                self._assert_denied_before_canonical()

    def test_unrelated_nonrestrictive_user_permissions_do_not_expand_authority(self) -> None:
        self.permissions.value = {
            "Company": [_company_rule(COMPANY)],
            "Customer": [_company_rule("CUSTOMER_A")],
        }
        self.assertEqual(self._call()[0], CANONICAL)

    def test_malformed_authentication_role_and_permission_shapes_fail_closed(self) -> None:
        malformed_roles = ("Accounts Manager", [""], [1], None)
        for roles in malformed_roles:
            with self.subTest(roles=roles):
                self.setUp()
                self.frappe.roles = roles
                self._assert_denied_before_canonical()
        malformed_permissions = (
            None,
            [],
            {"Company": "COMPANY_A"},
            {"Company": [{}]},
            {"Company": [_company_rule(COMPANY, is_default=True)]},
            {"Company": [_company_rule(COMPANY, applicable_for=1)]},
        )
        for permissions in malformed_permissions:
            with self.subTest(permissions=permissions):
                self.setUp()
                self.permissions.value = permissions
                self._assert_denied_before_canonical()

    def test_session_role_and_permission_drift_discard_canonical_response(self) -> None:
        mutations = (
            lambda: self.frappe.local.session.__setitem__(
                "user", "other.manager@example.test"
            ),
            lambda: setattr(self.frappe, "roles", ["Accounts User"]),
            lambda: setattr(
                self.permissions,
                "value",
                {"Company": [_company_rule("COMPANY_B")]},
            ),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.setUp()
                with patch.object(
                    bridge,
                    "build_canonical_gl_trial_balance_response",
                    side_effect=lambda **_: (mutation(), CANONICAL)[1],
                ) as canonical:
                    self._assert_generic(
                        lambda: read_authenticated_gl_trial_balance(
                            request=_request(),
                            frappe_module=self.frappe,
                            permissions_module=self.permissions,
                            runtime=self.runtime,
                            runtime_policy=self.runtime_policy,
                            service_policy=self.service_policy,
                        )
                    )
                canonical.assert_called_once()

    def test_runtime_session_user_drift_is_denied(self) -> None:
        with patch.object(
            self.runtime,
            "current_user",
            side_effect=[USER, "other.manager@example.test"],
        ), patch.object(
            bridge,
            "build_canonical_gl_trial_balance_response",
            return_value=CANONICAL,
        ) as canonical:
            self._assert_generic(
                lambda: read_authenticated_gl_trial_balance(
                    request=_request(),
                    frappe_module=self.frappe,
                    permissions_module=self.permissions,
                    runtime=self.runtime,
                    runtime_policy=self.runtime_policy,
                    service_policy=self.service_policy,
                )
            )
        canonical.assert_called_once()

    def test_runtime_binding_policy_and_context_mismatch_fail_before_authentication(self) -> None:
        other_frappe = _Frappe()
        other_permissions = _Permissions()
        mismatched_policy = replace(
            self.runtime_policy,
            expected_server_version="10.11.19-MariaDB-other",
        )
        cases = (
            {"runtime": object()},
            {"runtime": None},
            {"runtime_policy": None},
            {"runtime_policy": mismatched_policy},
            {"frappe_module": other_frappe},
            {"permissions_module": other_permissions},
        )
        for case in cases:
            with self.subTest(case=case):
                self.setUp()
                self._assert_denied_before_canonical(**case)
        self.setUp()
        self.runtime._context = object()  # type: ignore[assignment]
        self._assert_denied_before_canonical()

    def test_request_and_service_policy_absence_or_malformed_values_fail_closed(self) -> None:
        cases = (
            {"request": object()},
            {"service_policy": object()},
            {"service_policy": None},
        )
        for case in cases:
            with self.subTest(case=case):
                self.setUp()
                self._assert_denied_before_canonical(**case)

    def test_canonical_failure_or_malformed_output_is_generic_without_partial(self) -> None:
        outcomes = (
            RuntimeError("SECRET COMPANY_A GL-ENTRY-9"),
            None,
            "not-bytes",
            b"",
        )
        for outcome in outcomes:
            with self.subTest(outcome=outcome):
                self.setUp()
                kwargs = (
                    {"side_effect": outcome}
                    if isinstance(outcome, Exception)
                    else {"return_value": outcome}
                )
                with patch.object(
                    bridge,
                    "build_canonical_gl_trial_balance_response",
                    **kwargs,
                ) as canonical:
                    error = self._assert_generic(
                        lambda: read_authenticated_gl_trial_balance(
                            request=_request(),
                            frappe_module=self.frappe,
                            permissions_module=self.permissions,
                            runtime=self.runtime,
                            runtime_policy=self.runtime_policy,
                            service_policy=self.service_policy,
                        )
                    )
                canonical.assert_called_once()
                self.assertNotIn("SECRET", str(error))
                self.assertNotIn("COMPANY_A", str(error))

    def test_authentication_and_canonical_message_leakage_is_restored(self) -> None:
        def leaking_roles(_: str) -> object:
            self.frappe.local.message_log.append("SECRET ROLE COMPANY_A")
            raise RuntimeError("SECRET")

        self.frappe.roles = leaking_roles
        self._assert_denied_before_canonical()
        self.assertEqual(self.frappe.local.message_log, [])

        self.setUp()

        def leaking_canonical(**_: object) -> bytes:
            self.frappe.local.message_log.append("SECRET GL-ENTRY-9")
            return CANONICAL

        with patch.object(
            bridge,
            "build_canonical_gl_trial_balance_response",
            side_effect=leaking_canonical,
        ):
            self._assert_generic(
                lambda: read_authenticated_gl_trial_balance(
                    request=_request(),
                    frappe_module=self.frappe,
                    permissions_module=self.permissions,
                    runtime=self.runtime,
                    runtime_policy=self.runtime_policy,
                    service_policy=self.service_policy,
                )
            )
        self.assertEqual(self.frappe.local.message_log, [])

    def test_nonempty_mutable_message_log_is_rejected_before_canonical_mutation(self) -> None:
        marker = {"detail": "safe"}
        self.frappe.local.message_log = [marker]

        def mutate_existing_message(**_: object) -> bytes:
            marker["detail"] = "SECRET GL-ENTRY-9"
            return CANONICAL

        with patch.object(
            bridge,
            "build_canonical_gl_trial_balance_response",
            side_effect=mutate_existing_message,
        ) as canonical:
            self._assert_generic(lambda: self._read())
        canonical.assert_not_called()
        self.assertEqual(marker, {"detail": "safe"})
        self.assertIs(self.frappe.local.message_log[0], marker)

    def test_message_log_replacement_is_rejected_and_original_reference_restored(self) -> None:
        original = self.frappe.local.message_log

        def replace_log(**_: object) -> bytes:
            self.frappe.local.message_log = ["SECRET REPLACEMENT"]
            return CANONICAL

        with patch.object(
            bridge,
            "build_canonical_gl_trial_balance_response",
            side_effect=replace_log,
        ):
            self._assert_generic(
                lambda: read_authenticated_gl_trial_balance(
                    request=_request(),
                    frappe_module=self.frappe,
                    permissions_module=self.permissions,
                    runtime=self.runtime,
                    runtime_policy=self.runtime_policy,
                    service_policy=self.service_policy,
                )
            )
        self.assertIs(self.frappe.local.message_log, original)
        self.assertEqual(original, [])

    def test_fresh_source_execution_has_no_frappe_or_external_activation(self) -> None:
        source = inspect.getsource(bridge)
        code = compile(source, "<gl_tb_authenticated_inertness>", "exec")
        module_name = "erp_workspace_ui.finance_accounting._gl_tb_auth_inertness"
        candidate = types.ModuleType(module_name)
        candidate.__package__ = "erp_workspace_ui.finance_accounting"
        real_import = builtins.__import__
        forbidden = {
            "MySQLdb",
            "frappe",
            "os",
            "pathlib",
            "pymysql",
            "requests",
            "socket",
            "subprocess",
            "urllib",
        }

        def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name.partition(".")[0] in forbidden:
                raise AssertionError("activation_import_forbidden")
            return real_import(name, globals, locals, fromlist, level)

        sys.modules[module_name] = candidate
        try:
            with patch.object(builtins, "__import__", side_effect=guarded_import), patch.object(
                builtins, "open", side_effect=AssertionError("filesystem_forbidden")
            ):
                exec(code, candidate.__dict__)
        finally:
            sys.modules.pop(module_name, None)
        self.assertIn("read_authenticated_gl_trial_balance", candidate.__dict__)

    def test_source_has_no_whitelist_http_default_runtime_or_execution_authority(self) -> None:
        source = inspect.getsource(bridge)
        for forbidden in (
            "import frappe",
            "@frappe.whitelist",
            "frappe.db",
            "get_all(",
            "ignore_permissions",
            "requests",
            "socket",
            "open(",
            "insert(",
            "save(",
            "submit(",
            "cancel(",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
