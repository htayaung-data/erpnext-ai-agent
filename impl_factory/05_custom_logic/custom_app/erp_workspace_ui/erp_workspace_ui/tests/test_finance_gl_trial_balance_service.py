"""Isolated source tests for the internal GL / Trial Balance service boundary."""

from __future__ import annotations

import builtins
import hashlib
import inspect
import json
import sys
import types
import unittest
from dataclasses import MISSING, fields, replace
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch

from erp_workspace_ui.finance_accounting import gl_trial_balance_service as service
from erp_workspace_ui.finance_accounting.gl_trial_balance_adapter import (
    GLTrialBalanceAdapterError,
    GLTrialBalanceReadRequest,
)
from erp_workspace_ui.finance_accounting.gl_trial_balance_core import (
    AccountingAmounts,
    TrialBalanceLine,
    TrialBalanceResult,
    TrialBalanceScope,
)
from erp_workspace_ui.finance_accounting.gl_trial_balance_service import (
    GLTrialBalanceServiceError,
    GLTrialBalanceServicePolicy,
    GLTrialBalanceServiceRequest,
    build_canonical_gl_trial_balance_response,
)


_CANONICAL_V1_RESPONSE_SHA256 = (
    "32fbb7a70bf3d5f669861e125cfba8772dd0ed992373a334aee00d544974520c"
)


def _amounts(
    *, debit: str = "0.00", credit: str = "0.00"
) -> AccountingAmounts:
    opening_debit = Decimal(debit)
    opening_credit = Decimal(credit)
    movement_debit = Decimal("2.30") if opening_debit else Decimal("0.00")
    movement_credit = Decimal("2.30") if opening_credit else Decimal("0.00")
    return AccountingAmounts(
        opening_debit=opening_debit,
        opening_credit=opening_credit,
        movement_debit=movement_debit,
        movement_credit=movement_credit,
        closing_debit=opening_debit + movement_debit,
        closing_credit=opening_credit + movement_credit,
    )


def _balanced_totals() -> AccountingAmounts:
    return AccountingAmounts(
        opening_debit=Decimal("1.20"),
        opening_credit=Decimal("1.20"),
        movement_debit=Decimal("2.30"),
        movement_credit=Decimal("2.30"),
        closing_debit=Decimal("3.50"),
        closing_credit=Decimal("3.50"),
    )


def _request(**changes: object) -> GLTrialBalanceServiceRequest:
    values: dict[str, object] = {
        "company": "Example Company",
        "fiscal_year": "FY-2026",
        "from_date": date(2026, 1, 1),
        "to_date": date(2026, 12, 31),
    }
    values.update(changes)
    return GLTrialBalanceServiceRequest(**values)  # type: ignore[arg-type]


def _policy(**changes: object) -> GLTrialBalanceServicePolicy:
    values: dict[str, object] = {
        "currency_precision": 2,
        "max_accounts": 10,
        "max_gl_entries": 100,
        "max_metadata_bytes": 4096,
        "max_response_bytes": 16384,
    }
    values.update(changes)
    return GLTrialBalanceServicePolicy(**values)  # type: ignore[arg-type]


def _result(**scope_changes: object) -> TrialBalanceResult:
    scope = TrialBalanceScope(
        company="Example Company",
        base_currency="USD",
        precision=2,
        fiscal_year_start=date(2026, 1, 1),
        fiscal_year_end=date(2026, 12, 31),
        from_date=date(2026, 1, 1),
        to_date=date(2026, 12, 31),
        default_finance_book="Default Book",
        finance_book_cohort=(
            "company_default",
            "blank_unbooked",
            "null_unbooked",
        ),
        active_dimensions=0,
    )
    if scope_changes:
        scope = replace(scope, **scope_changes)
    debit = _amounts(debit="1.20")
    credit = _amounts(credit="1.20")
    lines = (
        TrialBalanceLine("1000 - Assets", None, True, "Asset", 0, debit),
        TrialBalanceLine("1110 - Cash", "1000 - Assets", False, "Asset", 1, debit),
        TrialBalanceLine(
            "2000 - Liabilities", None, True, "Liability", 0, credit
        ),
        TrialBalanceLine(
            "2110 - Payables",
            "2000 - Liabilities",
            False,
            "Liability",
            1,
            credit,
        ),
    )
    totals = _balanced_totals()
    return TrialBalanceResult(scope, lines, totals, totals)


def _invoke(
    *,
    result: object | None = None,
    request: object | None = None,
    runtime: object | None = None,
    policy: object | None = None,
) -> tuple[bytes, object]:
    result = _result() if result is None else result
    request = _request() if request is None else request
    runtime = object() if runtime is None else runtime
    policy = _policy() if policy is None else policy
    with patch.object(service, "read_gl_trial_balance", return_value=result) as reader:
        payload = build_canonical_gl_trial_balance_response(
            request=request, runtime=runtime, policy=policy
        )
    return payload, reader


class GLTrialBalanceServiceTests(unittest.TestCase):
    def _assert_generic(self, function) -> GLTrialBalanceServiceError:
        with self.assertRaises(GLTrialBalanceServiceError) as captured:
            function()
        error = captured.exception
        self.assertEqual(str(error), "finance_read_unavailable")
        self.assertEqual(error.code, "finance_read_unavailable")
        self.assertIsNone(error.__cause__)
        self.assertIsNone(error.__context__)
        return error

    def test_valid_response_is_deterministic_and_hash_frozen(self) -> None:
        first, first_reader = _invoke()
        second, second_reader = _invoke()
        self.assertEqual(first, second)
        self.assertTrue(first.endswith(b"\n"))
        self.assertEqual(first.count(b"finance-gl-trial-balance.internal.v2"), 1)
        prior_schema_projection = first.replace(
            b"finance-gl-trial-balance.internal.v2",
            b"finance-gl-trial-balance.internal.v1",
        )
        self.assertEqual(
            hashlib.sha256(prior_schema_projection).hexdigest(),
            _CANONICAL_V1_RESPONSE_SHA256,
        )
        self.assertEqual(first_reader.call_count, 1)
        self.assertEqual(second_reader.call_count, 1)

    def test_canonical_shape_and_read_only_boundary(self) -> None:
        payload, _ = _invoke()
        decoded = json.loads(payload)
        self.assertEqual(
            set(decoded),
            {"boundary", "lines", "schema_version", "scope", "state", "totals"},
        )
        self.assertEqual(
            decoded["schema_version"], "finance-gl-trial-balance.internal.v2"
        )
        self.assertEqual(decoded["state"], "ready")
        self.assertEqual(
            decoded["boundary"],
            {
                "accounting_execution_enabled": False,
                "cancellation_control_claimed": False,
                "mutation_enabled": False,
                "party_identifiers_returned": False,
                "period_close_control_claimed": False,
                "read_only": True,
                "source_gl_entries_returned": False,
                "voucher_identifiers_returned": False,
            },
        )
        self.assertEqual(
            [line["account_id"] for line in decoded["lines"]],
            [
                "1000 - Assets",
                "1110 - Cash",
                "2000 - Liabilities",
                "2110 - Payables",
            ],
        )

    def test_scope_preserves_company_fiscal_date_currency_and_finance_book(self) -> None:
        decoded = json.loads(_invoke()[0])
        self.assertEqual(
            decoded["scope"],
            {
                "active_dimensions": 0,
                "base_currency": "USD",
                "company": "Example Company",
                "currency_precision": 2,
                "default_finance_book": "Default Book",
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
        )

    def test_unbooked_only_scope_serializes_as_closed_v2_variant(self) -> None:
        payload, _ = _invoke(
            result=_result(
                default_finance_book=None,
                finance_book_cohort=("blank_unbooked", "null_unbooked"),
            )
        )
        decoded = json.loads(payload)

        self.assertEqual(
            decoded["schema_version"], "finance-gl-trial-balance.internal.v2"
        )
        self.assertIsNone(decoded["scope"]["default_finance_book"])
        self.assertEqual(
            decoded["scope"]["finance_book_scope"],
            ["blank_unbooked", "null_unbooked"],
        )
        self.assertNotIn("company_default", decoded["scope"]["finance_book_scope"])

    def test_financial_values_are_fixed_strings_without_float_or_exponent(self) -> None:
        payload, _ = _invoke()
        decoded = json.loads(payload)
        amounts = decoded["totals"]["gross"]
        self.assertEqual(amounts["opening_debit"], "1.20")
        self.assertEqual(amounts["movement_credit"], "2.30")
        self.assertEqual(amounts["closing_debit"], "3.50")
        for section in (
            decoded["totals"]["gross"],
            decoded["totals"]["presentation"],
            *(line["amounts"] for line in decoded["lines"]),
        ):
            for value in section.values():
                self.assertIs(type(value), str)
                self.assertNotIn("e", value.lower())

    def test_adapter_receives_only_injected_policy_and_exact_business_scope(self) -> None:
        runtime = object()
        policy = _policy(
            currency_precision=3,
            max_accounts=17,
            max_gl_entries=211,
            max_metadata_bytes=5000,
            max_response_bytes=20000,
        )
        result = _result(precision=3)
        zero = Decimal("0.000")
        result = replace(
            result,
            lines=tuple(
                replace(
                    line,
                    amounts=AccountingAmounts(zero, zero, zero, zero, zero, zero),
                )
                for line in result.lines
            ),
            gross_totals=AccountingAmounts(zero, zero, zero, zero, zero, zero),
            presentation_totals=AccountingAmounts(
                zero, zero, zero, zero, zero, zero
            ),
        )
        with patch.object(service, "read_gl_trial_balance", return_value=result) as reader:
            build_canonical_gl_trial_balance_response(
                request=_request(), runtime=runtime, policy=policy
            )
        reader.assert_called_once_with(
            request=GLTrialBalanceReadRequest(
                company="Example Company",
                fiscal_year="FY-2026",
                from_date=date(2026, 1, 1),
                to_date=date(2026, 12, 31),
                currency_precision=3,
                max_accounts=17,
                max_gl_entries=211,
            ),
            runtime=runtime,
        )

    def test_service_requires_all_injected_arguments_and_has_no_defaults(self) -> None:
        signature = inspect.signature(build_canonical_gl_trial_balance_response)
        self.assertEqual(set(signature.parameters), {"request", "runtime", "policy"})
        for parameter in signature.parameters.values():
            self.assertIs(parameter.default, inspect.Parameter.empty)
            self.assertEqual(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
        for policy_field in fields(GLTrialBalanceServicePolicy):
            self.assertIs(policy_field.default, MISSING)
            self.assertIs(policy_field.default_factory, MISSING)

    def test_request_envelope_cap_precedes_adapter_and_handles_unicode(self) -> None:
        requests = (_request(), _request(company="示例公司"))
        for request in requests:
            envelope = {
                "company": request.company,
                "fiscal_year": request.fiscal_year,
                "from_date": request.from_date.isoformat(),
                "to_date": request.to_date.isoformat(),
            }
            exact_size = len(
                json.dumps(
                    envelope,
                    allow_nan=False,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ).encode("utf-8")
            )
            with self.subTest(company=request.company, boundary="exact"):
                with patch.object(
                    service,
                    "read_gl_trial_balance",
                    side_effect=GLTrialBalanceAdapterError(),
                ) as reader:
                    self._assert_generic(
                        lambda: build_canonical_gl_trial_balance_response(
                            request=request,
                            runtime=object(),
                            policy=_policy(max_metadata_bytes=exact_size),
                        )
                    )
                reader.assert_called_once()
            with self.subTest(company=request.company, boundary="plus_one"):
                with patch.object(service, "read_gl_trial_balance") as reader:
                    self._assert_generic(
                        lambda: build_canonical_gl_trial_balance_response(
                            request=request,
                            runtime=object(),
                            policy=_policy(max_metadata_bytes=exact_size - 1),
                        )
                    )
                reader.assert_not_called()

        with patch.object(service, "read_gl_trial_balance") as reader:
            self._assert_generic(
                lambda: build_canonical_gl_trial_balance_response(
                    request=_request(company="\ud800"),
                    runtime=object(),
                    policy=_policy(),
                )
            )
        reader.assert_not_called()

    def test_invalid_requests_fail_before_adapter_call(self) -> None:
        invalid = (
            object(),
            _request(company=""),
            _request(company=" Example Company"),
            _request(company="Example\nCompany"),
            _request(fiscal_year=""),
            _request(from_date=datetime(2026, 1, 1)),
            _request(to_date=datetime(2026, 12, 31)),
            _request(from_date=date(2026, 2, 1), to_date=date(2026, 1, 1)),
        )
        for candidate in invalid:
            with self.subTest(candidate=candidate):
                with patch.object(service, "read_gl_trial_balance") as reader:
                    self._assert_generic(
                        lambda: build_canonical_gl_trial_balance_response(
                            request=candidate, runtime=object(), policy=_policy()
                        )
                    )
                reader.assert_not_called()

    def test_invalid_policies_fail_before_adapter_call(self) -> None:
        invalid = (
            object(),
            _policy(currency_precision=True),
            _policy(currency_precision=-1),
            _policy(max_accounts=True),
            _policy(max_accounts=0),
            _policy(max_gl_entries=0),
            _policy(max_metadata_bytes=0),
            _policy(max_response_bytes=0),
            _policy(max_metadata_bytes=101, max_response_bytes=100),
            _policy(currency_precision=100, max_metadata_bytes=103, max_response_bytes=103),
        )
        for candidate in invalid:
            with self.subTest(candidate=candidate):
                with patch.object(service, "read_gl_trial_balance") as reader:
                    self._assert_generic(
                        lambda: build_canonical_gl_trial_balance_response(
                            request=_request(), runtime=object(), policy=candidate
                        )
                    )
                reader.assert_not_called()

    def test_missing_runtime_fails_before_adapter_call(self) -> None:
        with patch.object(service, "read_gl_trial_balance") as reader:
            self._assert_generic(
                lambda: build_canonical_gl_trial_balance_response(
                    request=_request(), runtime=None, policy=_policy()
                )
            )
        reader.assert_not_called()

    def test_company_result_mismatch_is_rejected(self) -> None:
        self._assert_generic(lambda: _invoke(result=_result(company="Other Company")))

    def test_scope_drift_is_rejected(self) -> None:
        invalid = (
            _result(precision=3),
            _result(from_date=date(2026, 1, 2)),
            _result(to_date=date(2026, 12, 30)),
            _result(fiscal_year_start=date(2026, 2, 1)),
            _result(finance_book_cohort=("company_default", "blank_unbooked", "other")),
            _result(finance_book_cohort=("blank_unbooked", "null_unbooked")),
            _result(
                default_finance_book=None,
                finance_book_cohort=(
                    "company_default",
                    "blank_unbooked",
                    "null_unbooked",
                ),
            ),
            _result(
                default_finance_book=None,
                finance_book_cohort=("null_unbooked", "blank_unbooked"),
            ),
            _result(active_dimensions=1),
            _result(base_currency=""),
            _result(default_finance_book=""),
            _result(default_finance_book=" "),
        )
        for candidate in invalid:
            with self.subTest(scope=candidate.scope):
                self._assert_generic(lambda candidate=candidate: _invoke(result=candidate))

    def test_permission_role_manifest_and_runtime_failures_are_generic(self) -> None:
        failures = (
            GLTrialBalanceAdapterError(),
            RuntimeError("Administrator secret-company"),
            RuntimeError("hidden-account ACC-SECRET"),
            RuntimeError("manifest drift voucher GL-ENTRY-9"),
            RuntimeError("connection 777 driver mysqlclient"),
        )
        for failure in failures:
            with self.subTest(failure=str(failure)):
                with patch.object(
                    service, "read_gl_trial_balance", side_effect=failure
                ) as reader:
                    error = self._assert_generic(
                        lambda: build_canonical_gl_trial_balance_response(
                            request=_request(), runtime=object(), policy=_policy()
                        )
                    )
                reader.assert_called_once()
                self.assertNotIn("secret", str(error))
                self.assertNotIn("voucher", str(error))
                self.assertNotIn("connection", str(error))

    def test_malformed_result_is_rejected_without_partial_output(self) -> None:
        invalid = (
            object(),
            replace(_result(), scope=object()),
            replace(_result(), lines=()),
            replace(_result(), lines=list(_result().lines)),
            replace(_result(), gross_totals=object()),
            replace(_result(), presentation_totals=object()),
        )
        for candidate in invalid:
            with self.subTest(candidate=type(candidate)):
                self._assert_generic(lambda candidate=candidate: _invoke(result=candidate))

    def test_line_cap_exact_pass_and_plus_one_rejection(self) -> None:
        payload, _ = _invoke(policy=_policy(max_accounts=4))
        self.assertTrue(payload)
        self._assert_generic(lambda: _invoke(policy=_policy(max_accounts=3)))

    def test_response_size_exact_pass_and_plus_one_rejection(self) -> None:
        payload, _ = _invoke()
        exact = len(payload)
        decoded = json.loads(payload)
        metadata = {
            key: decoded[key]
            for key in ("boundary", "schema_version", "scope", "state")
        }
        metadata_size = len(
            json.dumps(
                metadata,
                allow_nan=False,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        )
        exact_payload, _ = _invoke(
            policy=_policy(
                max_metadata_bytes=metadata_size, max_response_bytes=exact
            )
        )
        self.assertEqual(exact_payload, payload)
        self._assert_generic(
            lambda: _invoke(
                policy=_policy(
                    max_metadata_bytes=metadata_size,
                    max_response_bytes=exact - 1,
                )
            )
        )

    def test_metadata_size_exact_pass_and_plus_one_rejection(self) -> None:
        payload, _ = _invoke()
        decoded = json.loads(payload)
        metadata = {
            key: decoded[key]
            for key in ("boundary", "schema_version", "scope", "state")
        }
        metadata_size = len(
            json.dumps(
                metadata,
                allow_nan=False,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        )
        self.assertTrue(
            _invoke(policy=_policy(max_metadata_bytes=metadata_size))[0]
        )
        self._assert_generic(
            lambda: _invoke(policy=_policy(max_metadata_bytes=metadata_size - 1))
        )

    def test_overprecision_nonfinite_and_signed_values_are_rejected(self) -> None:
        for invalid_amount in (
            Decimal("1.201"),
            Decimal("NaN"),
            Decimal("Infinity"),
            Decimal("-0.00"),
            Decimal("1E+20000"),
        ):
            amounts = replace(_balanced_totals(), opening_debit=invalid_amount)
            candidate = replace(_result(), gross_totals=amounts)
            with self.subTest(value=invalid_amount):
                self._assert_generic(lambda candidate=candidate: _invoke(result=candidate))

    def test_duplicate_or_malformed_line_hierarchy_is_rejected(self) -> None:
        result = _result()
        duplicate = replace(
            result.lines[1], account_id=result.lines[0].account_id
        )
        wrong_depth = replace(result.lines[1], depth=2)
        wrong_root = replace(result.lines[1], root_type="Liability")
        invalid_sets = (
            (result.lines[0], duplicate, *result.lines[2:]),
            (result.lines[0], wrong_depth, *result.lines[2:]),
            (result.lines[0], wrong_root, *result.lines[2:]),
            (result.lines[1], result.lines[0], *result.lines[2:]),
            (replace(result.lines[0], is_group=False), *result.lines[1:]),
        )
        for lines in invalid_sets:
            with self.subTest(lines=lines):
                self._assert_generic(
                    lambda lines=lines: _invoke(result=replace(result, lines=lines))
                )

    def test_serialization_failure_is_generic_and_returns_no_partial_bytes(self) -> None:
        with patch.object(service.json, "dumps", side_effect=RuntimeError("secret")):
            error = self._assert_generic(lambda: _invoke())
        self.assertEqual(str(error), "finance_read_unavailable")

    def test_response_excludes_forbidden_source_and_runtime_identity_fields(self) -> None:
        decoded = json.loads(_invoke()[0])
        forbidden = {
            "entry_id",
            "gl_entry",
            "voucher",
            "party",
            "source_document",
            "connection_id",
            "driver",
            "server_version",
            "user",
            "roles",
        }

        def keys(value: object) -> set[str]:
            if type(value) is dict:
                found = set(value)
                for child in value.values():
                    found.update(keys(child))
                return found
            if type(value) is list:
                found: set[str] = set()
                for child in value:
                    found.update(keys(child))
                return found
            return set()

        self.assertFalse(keys(decoded) & forbidden)

    def test_fresh_source_execution_has_no_activation_side_effect(self) -> None:
        source = inspect.getsource(service)
        code = compile(source, "<gl_trial_balance_service_inertness>", "exec")
        module_name = (
            "erp_workspace_ui.finance_accounting._gl_trial_balance_service_inertness"
        )
        candidate = types.ModuleType(module_name)
        candidate.__package__ = "erp_workspace_ui.finance_accounting"
        real_import = builtins.__import__
        forbidden_roots = {
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
            if name.partition(".")[0] in forbidden_roots:
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
        self.assertIn("build_canonical_gl_trial_balance_response", candidate.__dict__)

    def test_source_has_no_http_frappe_database_filesystem_or_network_activation(self) -> None:
        source = inspect.getsource(service)
        for forbidden in (
            "import frappe",
            "@frappe.whitelist",
            "frappe.db",
            "get_all(",
            "ignore_permissions",
            "import socket",
            "import requests",
            "urllib",
            "open(",
            "Path(",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":  # pragma: no cover - direct developer convenience only
    unittest.main()
