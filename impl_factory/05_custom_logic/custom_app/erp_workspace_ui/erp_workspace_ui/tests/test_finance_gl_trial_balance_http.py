"""Isolated tests for the authenticated GL / Trial Balance HTTP boundary."""

from __future__ import annotations

import ast
import inspect
import json
import sys
import types
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import Mock, patch


USER = "accounts.manager@example.test"
COMPANY = "COMPANY_A"
METHOD = (
    "erp_workspace_ui.finance_accounting.gl_trial_balance_http."
    "get_gl_trial_balance"
)


def _install_frappe_stub() -> tuple[types.ModuleType, types.ModuleType]:
    frappe = types.ModuleType("frappe")
    frappe.__path__ = []  # type: ignore[attr-defined]
    permissions = types.ModuleType("frappe.permissions")

    def whitelist(*, allow_guest=False, methods=None):
        def decorate(function):
            function.__allow_guest__ = allow_guest
            function.__http_methods__ = tuple(methods or ())
            return function

        return decorate

    frappe.whitelist = whitelist
    frappe.permissions = permissions
    frappe.local = types.SimpleNamespace()
    frappe.form_dict = {}
    sys.modules["frappe"] = frappe
    sys.modules["frappe.permissions"] = permissions
    return frappe, permissions


frappe, frappe_permissions = _install_frappe_stub()

from erp_workspace_ui.finance_accounting import gl_trial_balance_http as endpoint  # noqa: E402
from erp_workspace_ui.finance_accounting.gl_trial_balance_frappe_runtime import (  # noqa: E402
    GLTrialBalanceRuntimePolicy,
)
from erp_workspace_ui.finance_accounting.gl_trial_balance_http import (  # noqa: E402
    GLTrialBalanceHTTPError,
    get_gl_trial_balance,
)
from erp_workspace_ui.finance_accounting.gl_trial_balance_service import (  # noqa: E402
    GLTrialBalanceServicePolicy,
    GLTrialBalanceServiceRequest,
)


_SOURCE = Path(endpoint.__file__).read_text(encoding="utf-8")


def _policy() -> dict[str, object]:
    return {
        "runtime": {
            "expected_driver": "pymysql",
            "expected_driver_version": "1.1.2",
            "expected_server_version": "10.11.18-MariaDB-synthetic",
        },
        "service": {
            "currency_precision": 2,
            "max_accounts": 20,
            "max_gl_entries": 200,
            "max_metadata_bytes": 4096,
            "max_response_bytes": 32768,
        },
    }


def _amounts() -> dict[str, str]:
    return {
        "closing_credit": "0.00",
        "closing_debit": "0.00",
        "movement_credit": "0.00",
        "movement_debit": "0.00",
        "opening_credit": "0.00",
        "opening_debit": "0.00",
    }


def _document() -> dict[str, object]:
    return {
        "boundary": {
            "accounting_execution_enabled": False,
            "cancellation_control_claimed": False,
            "mutation_enabled": False,
            "party_identifiers_returned": False,
            "period_close_control_claimed": False,
            "read_only": True,
            "source_gl_entries_returned": False,
            "voucher_identifiers_returned": False,
        },
        "lines": [
            {
                "account_id": "1000 - Assets",
                "amounts": _amounts(),
                "depth": 0,
                "is_group": True,
                "parent_account_id": None,
                "root_type": "Asset",
            },
            {
                "account_id": "1110 - Cash",
                "amounts": _amounts(),
                "depth": 1,
                "is_group": False,
                "parent_account_id": "1000 - Assets",
                "root_type": "Asset",
            },
        ],
        "schema_version": "finance-gl-trial-balance.internal.v1",
        "scope": {
            "active_dimensions": 0,
            "base_currency": "MMK",
            "company": COMPANY,
            "currency_precision": 2,
            "default_finance_book": "DEFAULT_BOOK",
            "finance_book_scope": [
                "company_default",
                "blank_unbooked",
                "null_unbooked",
            ],
            "fiscal_year": "FY-2026",
            "fiscal_year_end": "2026-12-31",
            "fiscal_year_start": "2026-01-01",
            "from_date": "2026-01-01",
            "to_date": "2026-12-31",
        },
        "state": "ready",
        "totals": {"gross": _amounts(), "presentation": _amounts()},
    }


def _canonical(document: object | None = None) -> bytes:
    value = _document() if document is None else document
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


class GLTrialBalanceHTTPTests(unittest.TestCase):
    def setUp(self) -> None:
        frappe.local = types.SimpleNamespace(
            request=types.SimpleNamespace(method="POST"),
            session={"user": USER},
            conf={"finance_gl_trial_balance_policy": _policy()},
        )
        frappe.form_dict = {
            "cmd": METHOD,
            "company": COMPANY,
            "fiscal_year": "FY-2026",
            "from_date": "2026-01-01",
            "to_date": "2026-12-31",
        }

    def _assert_generic(self, callback, *leakage_canaries: str) -> GLTrialBalanceHTTPError:
        with self.assertRaises(GLTrialBalanceHTTPError) as captured:
            callback()
        error = captured.exception
        self.assertEqual(str(error), "finance_read_unavailable")
        self.assertEqual(error.code, "finance_read_unavailable")
        self.assertIsNone(error.__cause__)
        self.assertIsNone(error.__context__)
        for canary in leakage_canaries:
            self.assertNotIn(canary, str(error))
        return error

    def _invoke(self, **changes: object) -> object:
        values: dict[str, object] = {
            "company": COMPANY,
            "fiscal_year": "FY-2026",
            "from_date": "2026-01-01",
            "to_date": "2026-12-31",
        }
        values.update(changes)
        return get_gl_trial_balance(**values)

    def _successful_call(self) -> tuple[object, Mock, Mock]:
        runtime = object()
        with patch.object(
            endpoint, "FrappeGLTrialBalanceRuntime", return_value=runtime
        ) as runtime_factory, patch.object(
            endpoint,
            "read_authenticated_gl_trial_balance",
            return_value=_canonical(),
        ) as bridge:
            response = self._invoke()
        return response, runtime_factory, bridge

    def test_whitelist_is_authenticated_and_post_only(self) -> None:
        self.assertIs(get_gl_trial_balance.__allow_guest__, False)
        self.assertEqual(get_gl_trial_balance.__http_methods__, ("POST",))
        self.assertEqual(
            tuple(inspect.signature(get_gl_trial_balance).parameters),
            ("company", "fiscal_year", "from_date", "to_date"),
        )

    def test_success_constructs_fresh_policies_runtime_and_bridge_call(self) -> None:
        response, runtime_factory, bridge = self._successful_call()
        self.assertEqual(response, _document())
        runtime_factory.assert_called_once()
        runtime_kwargs = runtime_factory.call_args.kwargs
        self.assertIs(runtime_kwargs["frappe_module"], frappe)
        self.assertIs(runtime_kwargs["permissions_module"], frappe_permissions)
        self.assertEqual(
            runtime_kwargs["policy"],
            GLTrialBalanceRuntimePolicy(
                expected_driver="pymysql",
                expected_driver_version="1.1.2",
                expected_server_version="10.11.18-MariaDB-synthetic",
            ),
        )
        bridge.assert_called_once()
        bridge_kwargs = bridge.call_args.kwargs
        self.assertEqual(
            bridge_kwargs["request"],
            GLTrialBalanceServiceRequest(
                company=COMPANY,
                fiscal_year="FY-2026",
                from_date=endpoint.date(2026, 1, 1),
                to_date=endpoint.date(2026, 12, 31),
            ),
        )
        self.assertIs(bridge_kwargs["frappe_module"], frappe)
        self.assertIs(bridge_kwargs["permissions_module"], frappe_permissions)
        self.assertIs(bridge_kwargs["runtime"], runtime_factory.return_value)
        self.assertEqual(
            bridge_kwargs["service_policy"],
            GLTrialBalanceServicePolicy(2, 20, 200, 4096, 32768),
        )

    def test_each_call_constructs_a_new_runtime(self) -> None:
        with patch.object(
            endpoint, "FrappeGLTrialBalanceRuntime", side_effect=(object(), object())
        ) as runtime_factory, patch.object(
            endpoint,
            "read_authenticated_gl_trial_balance",
            return_value=_canonical(),
        ):
            self._invoke()
            self._invoke()
        self.assertEqual(runtime_factory.call_count, 2)

    def test_guest_and_administrator_are_rejected_before_policy_or_runtime(self) -> None:
        for user in ("Guest", "Administrator"):
            with self.subTest(user=user), patch.object(
                endpoint, "FrappeGLTrialBalanceRuntime"
            ) as runtime_factory:
                frappe.local.session = {"user": user}
                self._assert_generic(self._invoke)
                runtime_factory.assert_not_called()
        frappe.local.session = {"user": USER}

    def test_non_post_methods_are_rejected_before_policy_or_runtime(self) -> None:
        for method in ("GET", "PUT", "DELETE", "PATCH"):
            with self.subTest(method=method), patch.object(
                endpoint, "FrappeGLTrialBalanceRuntime"
            ) as runtime_factory:
                frappe.local.request.method = method
                self._assert_generic(self._invoke)
                runtime_factory.assert_not_called()
        frappe.local.request.method = "POST"

    def test_input_schema_rejects_missing_unknown_user_and_wrong_command(self) -> None:
        mutations = []
        missing = dict(frappe.form_dict)
        missing.pop("company")
        mutations.append(missing)
        unknown = dict(frappe.form_dict)
        unknown["report_name"] = "Trial Balance"
        mutations.append(unknown)
        user_supplied = dict(frappe.form_dict)
        user_supplied["user"] = "Administrator"
        mutations.append(user_supplied)
        wrong_command = dict(frappe.form_dict)
        wrong_command["cmd"] = "frappe.desk.query_report.run"
        mutations.append(wrong_command)
        for form_dict in mutations:
            with self.subTest(keys=tuple(sorted(form_dict))):
                frappe.form_dict = form_dict
                self._assert_generic(self._invoke, "Administrator", "Trial Balance")

    def test_input_schema_rejects_argument_form_mismatch(self) -> None:
        self._assert_generic(lambda: self._invoke(company="OTHER_COMPANY"), "OTHER_COMPANY")

    def test_business_inputs_are_strict_and_dates_are_ordered(self) -> None:
        cases = (
            {"company": ""},
            {"company": " COMPANY_A"},
            {"company": "COMPANY\nA"},
            {"fiscal_year": ""},
            {"from_date": "20260101"},
            {"from_date": "2026-02-30"},
            {"from_date": "2026-12-31", "to_date": "2026-01-01"},
            {"to_date": None},
        )
        for changes in cases:
            with self.subTest(changes=changes):
                frappe.form_dict.update(changes)
                self._assert_generic(lambda changes=changes: self._invoke(**changes))
                self.setUp()

    def test_policy_is_mandatory_closed_and_has_no_coercion(self) -> None:
        cases: list[object] = [
            None,
            {},
            {"runtime": _policy()["runtime"]},
            {**_policy(), "extra": {}},
        ]
        unknown_runtime = _policy()
        unknown_runtime["runtime"] = {
            **unknown_runtime["runtime"],  # type: ignore[dict-item]
            "fallback": "forbidden",
        }
        cases.append(unknown_runtime)
        unknown_service = _policy()
        unknown_service["service"] = {
            **unknown_service["service"],  # type: ignore[dict-item]
            "max_export_rows": 1,
        }
        cases.append(unknown_service)
        string_number = _policy()
        string_number["service"] = {
            **string_number["service"],  # type: ignore[dict-item]
            "max_accounts": "20",
        }
        cases.append(string_number)
        for value in cases:
            with self.subTest(value=value), patch.object(
                endpoint, "FrappeGLTrialBalanceRuntime"
            ) as runtime_factory:
                frappe.local.conf = {"finance_gl_trial_balance_policy": value}
                self._assert_generic(self._invoke, "fallback", "max_export_rows")
                runtime_factory.assert_not_called()

    def test_policy_bounds_fail_closed_before_runtime(self) -> None:
        cases = (
            {"currency_precision": -1},
            {"max_accounts": 0},
            {"max_gl_entries": True},
            {"max_metadata_bytes": 40000, "max_response_bytes": 32000},
            {"currency_precision": 40000, "max_response_bytes": 32000},
        )
        for changes in cases:
            with self.subTest(changes=changes), patch.object(
                endpoint, "FrappeGLTrialBalanceRuntime"
            ) as runtime_factory:
                policy = _policy()
                policy["service"] = {
                    **policy["service"],  # type: ignore[dict-item]
                    **changes,
                }
                frappe.local.conf = {"finance_gl_trial_balance_policy": policy}
                self._assert_generic(self._invoke)
                runtime_factory.assert_not_called()

    def test_bridge_permission_company_and_runtime_failures_are_generic(self) -> None:
        canaries = (
            "OTHER_COMPANY",
            "GL-ENTRY-SECRET",
            "CONNECTION-991",
            "SELECT COUNT(*)",
        )
        for canary in canaries:
            with self.subTest(canary=canary), patch.object(
                endpoint, "FrappeGLTrialBalanceRuntime", return_value=object()
            ), patch.object(
                endpoint,
                "read_authenticated_gl_trial_balance",
                side_effect=RuntimeError(canary),
            ):
                self._assert_generic(self._invoke, canary)

    def test_canonical_response_requires_bytes_strict_json_and_terminal_lf(self) -> None:
        payloads = (
            _canonical().decode("utf-8"),
            b"",
            b"\xef\xbb\xbf" + _canonical(),
            _canonical()[:-1],
            b"{malformed}\n",
            b'{"schema_version":"x","schema_version":"y"}\n',
            b'{"value":NaN}\n',
            b'{"value":1.5}\n',
        )
        for payload in payloads:
            with self.subTest(payload=payload), patch.object(
                endpoint, "FrappeGLTrialBalanceRuntime", return_value=object()
            ), patch.object(
                endpoint, "read_authenticated_gl_trial_balance", return_value=payload
            ):
                self._assert_generic(self._invoke)

    def test_response_rejects_schema_scope_boundary_and_nested_drift(self) -> None:
        documents = []
        top_level = _document()
        top_level["voucher_rows"] = []
        documents.append(top_level)
        schema = _document()
        schema["schema_version"] = "native-report"
        documents.append(schema)
        company = _document()
        company["scope"]["company"] = "OTHER_COMPANY"  # type: ignore[index]
        documents.append(company)
        boundary = _document()
        boundary["boundary"]["mutation_enabled"] = True  # type: ignore[index]
        documents.append(boundary)
        line = _document()
        line["lines"][0]["voucher_no"] = "GL-SECRET"  # type: ignore[index]
        documents.append(line)
        totals = _document()
        totals["totals"]["gross"]["sql"] = "SELECT secret"  # type: ignore[index]
        documents.append(totals)
        for document in documents:
            with self.subTest(keys=tuple(document)), patch.object(
                endpoint, "FrappeGLTrialBalanceRuntime", return_value=object()
            ), patch.object(
                endpoint,
                "read_authenticated_gl_trial_balance",
                return_value=_canonical(document),
            ):
                self._assert_generic(
                    self._invoke,
                    "OTHER_COMPANY",
                    "GL-SECRET",
                    "SELECT secret",
                )

    def test_response_rejects_boolean_substitution_and_noncanonical_amounts(self) -> None:
        documents = []
        active_dimensions = _document()
        active_dimensions["scope"]["active_dimensions"] = False  # type: ignore[index]
        documents.append(active_dimensions)
        precision = _document()
        precision["scope"]["currency_precision"] = False  # type: ignore[index]
        documents.append(precision)
        boundary = _document()
        boundary["boundary"]["mutation_enabled"] = 0  # type: ignore[index]
        documents.append(boundary)
        for amount in ("not-an-amount", "00.00", "-1.00", "1", "1.0", "1e2"):
            document = _document()
            document["lines"][0]["amounts"]["opening_debit"] = amount  # type: ignore[index]
            documents.append(document)
        for document in documents:
            with self.subTest(document=document), patch.object(
                endpoint, "FrappeGLTrialBalanceRuntime", return_value=object()
            ), patch.object(
                endpoint,
                "read_authenticated_gl_trial_balance",
                return_value=_canonical(document),
            ):
                self._assert_generic(self._invoke, "not-an-amount")

    def test_response_size_uses_injected_policy_without_endpoint_default(self) -> None:
        policy = _policy()
        policy["service"] = {
            **policy["service"],  # type: ignore[dict-item]
            "max_response_bytes": len(_canonical()) - 1,
        }
        frappe.local.conf = {"finance_gl_trial_balance_policy": policy}
        with patch.object(
            endpoint, "FrappeGLTrialBalanceRuntime", return_value=object()
        ), patch.object(
            endpoint,
            "read_authenticated_gl_trial_balance",
            return_value=_canonical(),
        ):
            self._assert_generic(self._invoke)

    def test_source_contains_no_accounting_query_mutation_or_external_output_path(self) -> None:
        for forbidden in (
            "frappe.db",
            ".get_all(",
            "ignore_permissions",
            "query_report",
            "run_report",
            "sendmail",
            ".insert(",
            ".save(",
            "download",
            "export",
            "print",
            "allow_cors",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, _SOURCE)
        self.assertEqual(_SOURCE.count("read_authenticated_gl_trial_balance("), 1)
        self.assertNotIn("allow_guest=True", _SOURCE)

    def test_source_has_no_default_policy_runtime_or_import_time_effect(self) -> None:
        tree = ast.parse(_SOURCE)
        forbidden_top_level_calls = {
            "FrappeGLTrialBalanceRuntime",
            "GLTrialBalanceRuntimePolicy",
            "GLTrialBalanceServicePolicy",
            "open",
        }
        for node in tree.body:
            if isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
            ):
                continue
            for child in ast.walk(node):
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                    self.assertNotIn(child.func.id, forbidden_top_level_calls)
        self.assertNotIn("requests.", _SOURCE)
        self.assertNotIn("subprocess", _SOURCE)
        self.assertIn('methods=["POST"]', _SOURCE)
        self.assertIn('"finance_gl_trial_balance_policy"', _SOURCE)

    def test_form_document_is_not_mutated_on_success_or_failure(self) -> None:
        before = deepcopy(frappe.form_dict)
        self._successful_call()
        self.assertEqual(frappe.form_dict, before)
        with patch.object(
            endpoint,
            "FrappeGLTrialBalanceRuntime",
            side_effect=RuntimeError("private"),
        ):
            self._assert_generic(self._invoke, "private")
        self.assertEqual(frappe.form_dict, before)


if __name__ == "__main__":
    unittest.main()
