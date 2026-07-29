"""Isolated tests for the dormant GL/TB production-policy evidence boundary."""

from __future__ import annotations

import ast
import inspect
import json
import sys
import types
import unittest
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch


USER = "accounts.manager@example.test"
COMPANY_A = "COMPANY_ALPHA_CANARY"
COMPANY_B = "COMPANY_BETA_CANARY"
UNICODE_CANARY = "\u1004\u103d\u1031"
METHOD = (
    "erp_workspace_ui.finance_accounting.gl_trial_balance_policy_evidence."
    "collect_gl_trial_balance_policy_evidence"
)
DIAGNOSTIC_METHOD = (
    "erp_workspace_ui.finance_accounting.gl_trial_balance_policy_evidence."
    "diagnose_gl_trial_balance_policy_evidence_failure_phase"
)
IMPORT_EVENTS: list[tuple[object, ...]] = []


def _install_frappe_stub() -> tuple[types.ModuleType, types.ModuleType]:
    frappe = types.ModuleType("frappe")
    frappe.__path__ = []  # type: ignore[attr-defined]
    permissions = types.ModuleType("frappe.permissions")

    def whitelist(*, allow_guest=False, methods=None):
        IMPORT_EVENTS.append(
            ("whitelist", allow_guest, tuple(methods or ()))
        )

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

from erp_workspace_ui.finance_accounting import (  # noqa: E402
    gl_trial_balance_frappe_runtime as runtime_source,
)
from erp_workspace_ui.finance_accounting import (  # noqa: E402
    gl_trial_balance_policy_evidence as endpoint,
)
from erp_workspace_ui.finance_accounting.gl_trial_balance_adapter import (  # noqa: E402
    ReadSnapshotEvidence,
    UserPermissionRule,
)
from erp_workspace_ui.finance_accounting.gl_trial_balance_core import (  # noqa: E402
    AccountingAmounts,
    TrialBalanceLine,
    TrialBalanceResult,
    TrialBalanceScope,
)
from erp_workspace_ui.finance_accounting.gl_trial_balance_policy_evidence import (  # noqa: E402
    GLTrialBalancePolicyEvidenceError,
    collect_gl_trial_balance_policy_evidence,
    diagnose_gl_trial_balance_policy_evidence_failure_phase,
)
from erp_workspace_ui.finance_accounting.gl_trial_balance_service import (  # noqa: E402
    GLTrialBalanceServiceRequest,
)
from erp_workspace_ui.tests.test_finance_gl_trial_balance_adapter import (  # noqa: E402
    FISCAL_YEAR as ADAPTER_FISCAL_YEAR,
    _fiscal_manifest as _adapter_fiscal_manifest,
    _runtime_for_company as _adapter_runtime_for_company,
)


_SOURCE = Path(endpoint.__file__).read_text(encoding="utf-8")
_RUNTIME_SOURCE = Path(runtime_source.__file__).read_text(
    encoding="utf-8"
)


def _policy() -> dict[str, object]:
    return {
        "enabled": True,
        "expected_driver": "mysqlclient",
        "expected_driver_version": "2.2.7",
        "expected_server_version": "10.6.25-MariaDB-synthetic",
    }


def _permission_entry(
    value: str,
    *,
    applicable_for: str | None = None,
    hide_descendants: int = 0,
) -> dict[str, object]:
    return {
        "doc": value,
        "applicable_for": applicable_for,
        "is_default": 0,
        "hide_descendants": hide_descendants,
    }


def _permissions(
    companies: tuple[str, ...] = (COMPANY_A,),
) -> dict[str, object]:
    return {
        "Company": [
            _permission_entry(company) for company in companies
        ]
    }


def _source_floors(**changes: int) -> dict[str, int]:
    values = {
        "company_rows": 1,
        "active_fiscal_year_rows": 2,
        "fiscal_year_company_rows": 1,
        "finance_book_rows": 1,
        "active_dimension_rows": 0,
        "fiscal_applicability_rows": 2,
        "account_manifest_ids": 4,
        "root_manifest_ids": 1,
        "account_rows": 4,
        "final_manifest_ids": 4,
        "final_root_ids": 1,
        "final_fiscal_applicability_rows": 2,
    }
    values.update(changes)
    return values


def _byte_evidence(**changes: object) -> dict[str, object]:
    values: dict[str, object] = {
        "request_envelope_max_bytes": 120,
        "response_metadata_max_bytes": 700,
        "current_metadata_floor_bytes": 700,
        "current_response_floor_bytes": 4_096,
        "current_response_floor_line_count": 4,
        "max_observed_depth": 2,
        "max_observed_depth_width": 1,
        "max_identifier_utf8_bytes_observed": 32,
        "max_identifier_escape_extra_bytes_observed": 2,
        "max_parent_identifier_utf8_bytes_observed": 24,
        "max_fixed_decimal_bytes_observed": 12,
        "aggregation_digit_growth": 2,
        "fixed_decimal_width_bound": 18,
    }
    values.update(changes)
    return values


def _measurement(
    *,
    floors: dict[str, int] | None = None,
    max_gl_entries: int = 120,
    precision: int = 2,
    response_bytes: int = 4_096,
    elapsed: int = 1_000,
) -> endpoint._CompanyMeasurement:
    return endpoint._CompanyMeasurement(
        source_floors=floors or _source_floors(),
        max_gl_entries=max_gl_entries,
        fiscal_endpoints=2,
        minimum_fiscal_start=date(2025, 1, 1),
        maximum_fiscal_end=date(2026, 12, 31),
        maximum_fiscal_span_days=365,
        precision=precision,
        statement_ceiling={
            "global_state": "disabled",
            "global_microseconds": 0,
            "session_state": "enabled",
            "session_microseconds": 90_000_000,
        },
        database_shape={
            "numeric_precision": 21,
            "numeric_scale": 9,
        },
        identifier_envelopes={
            name: {
                "characters": 140,
                "utf8_bytes": 560,
                "json_string_bytes": 562,
            }
            for name in (
                "account",
                "company",
                "fiscal_year",
                "currency",
                "finance_book",
            )
        },
        byte_evidence=_byte_evidence(
            current_response_floor_bytes=response_bytes
        ),
        elapsed_microseconds=elapsed,
    )


def _amounts(value: str = "0.00") -> AccountingAmounts:
    amount = Decimal(value)
    return AccountingAmounts(
        opening_debit=amount,
        opening_credit=amount,
        movement_debit=amount,
        movement_credit=amount,
        closing_debit=amount,
        closing_credit=amount,
    )


def _result(
    *,
    child_name: str = '1110 - Cash "Main"',
    child_parent: str = "1000 - Assets",
) -> TrialBalanceResult:
    scope = TrialBalanceScope(
        company=COMPANY_A,
        base_currency="MMK",
        precision=2,
        fiscal_year_start=date(2026, 1, 1),
        fiscal_year_end=date(2026, 12, 31),
        from_date=date(2026, 1, 1),
        to_date=date(2026, 12, 31),
        default_finance_book="DEFAULT_BOOK",
        finance_book_cohort=(
            "company_default",
            "blank_unbooked",
            "null_unbooked",
        ),
        active_dimensions=0,
    )
    return TrialBalanceResult(
        scope=scope,
        lines=(
            TrialBalanceLine(
                account_id=child_parent,
                parent_account_id=None,
                is_group=True,
                root_type="Asset",
                depth=0,
                amounts=_amounts(),
            ),
            TrialBalanceLine(
                account_id=child_name,
                parent_account_id=child_parent,
                is_group=False,
                root_type="Asset",
                depth=1,
                amounts=_amounts("12.34"),
            ),
        ),
        gross_totals=_amounts("12.34"),
        presentation_totals=_amounts("12.34"),
    )


def _snapshot() -> ReadSnapshotEvidence:
    return ReadSnapshotEvidence(
        token="snapshot-token",
        user=USER,
        company=COMPANY_A,
        primary_connection=True,
        replica_denied=True,
        transaction_isolation="REPEATABLE READ",
        transaction_read_only=True,
        transaction_active=True,
        consistent_snapshot=True,
        reconnect_denied=True,
        same_connection=True,
        stable=True,
    )


class EndpointBoundaryAndAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        frappe.local = types.SimpleNamespace(
            request=types.SimpleNamespace(method="POST"),
            session={"user": USER},
            conf={endpoint._CONFIG_KEY: _policy()},
            message_log=[],
        )
        frappe.form_dict = {"cmd": METHOD}
        frappe.get_roles = lambda user: [
            "Accounts Manager",
            "Accounts User",
        ]
        frappe_permissions.get_user_permissions = (
            lambda user: _permissions()
        )

    def _assert_generic(
        self, callback, *canaries: str
    ) -> GLTrialBalancePolicyEvidenceError:
        with self.assertRaises(
            GLTrialBalancePolicyEvidenceError
        ) as captured:
            callback()
        error = captured.exception
        self.assertEqual(str(error), "finance_read_unavailable")
        self.assertEqual(error.code, "finance_read_unavailable")
        self.assertIsNone(error.__cause__)
        self.assertIsNone(error.__context__)
        for canary in canaries:
            self.assertNotIn(canary, str(error))
        return error

    def test_import_is_inert_and_endpoint_is_zero_argument_post_only(
        self,
    ) -> None:
        self.assertEqual(
            IMPORT_EVENTS,
            [
                ("whitelist", False, ("POST",)),
                ("whitelist", False, ("POST",)),
            ],
        )
        self.assertIs(
            collect_gl_trial_balance_policy_evidence.__allow_guest__,
            False,
        )
        self.assertEqual(
            collect_gl_trial_balance_policy_evidence.__http_methods__,
            ("POST",),
        )
        self.assertEqual(
            tuple(
                inspect.signature(
                    collect_gl_trial_balance_policy_evidence
                ).parameters
            ),
            (),
        )
        self.assertIs(
            diagnose_gl_trial_balance_policy_evidence_failure_phase.__allow_guest__,
            False,
        )
        self.assertEqual(
            diagnose_gl_trial_balance_policy_evidence_failure_phase.__http_methods__,
            ("POST",),
        )
        self.assertEqual(
            tuple(
                inspect.signature(
                    diagnose_gl_trial_balance_policy_evidence_failure_phase
                ).parameters
            ),
            (),
        )

    def test_feature_flag_has_no_enabled_default(self) -> None:
        for document in (
            None,
            {},
            {**_policy(), "enabled": False},
            {**_policy(), "enabled": 1},
            {**_policy(), "unknown": True},
        ):
            with self.subTest(document=document):
                frappe.local.conf = (
                    {}
                    if document is None
                    else {endpoint._CONFIG_KEY: document}
                )
                self._assert_generic(
                    collect_gl_trial_balance_policy_evidence
                )

    def test_feature_config_is_closed_and_contains_no_caps(self) -> None:
        policy = endpoint._request_policy()
        self.assertEqual(
            policy.expected_driver, "mysqlclient"
        )
        self.assertEqual(
            frozenset(_policy()),
            frozenset(
                {
                    "enabled",
                    "expected_driver",
                    "expected_driver_version",
                    "expected_server_version",
                }
            ),
        )
        forbidden = {
            "currency_precision",
            "max_accounts",
            "max_gl_entries",
            "max_metadata_bytes",
            "max_response_bytes",
            "timeout",
            "company",
        }
        self.assertFalse(forbidden & frozenset(_policy()))

    def test_guest_get_and_form_overrides_are_rejected(self) -> None:
        cases = (
            ("GET", USER, {"cmd": METHOD}),
            ("POST", "Guest", {"cmd": METHOD}),
            ("POST", "Administrator", {"cmd": METHOD}),
            ("POST", USER, {"cmd": "wrong.method"}),
            ("POST", USER, {"cmd": METHOD, "user": USER}),
            ("POST", USER, {"company": COMPANY_A}),
        )
        for method, user, form_dict in cases:
            with self.subTest(
                method=method, user=user, form_dict=form_dict
            ):
                frappe.local.request.method = method
                frappe.local.session = {"user": user}
                frappe.form_dict = form_dict
                self._assert_generic(
                    collect_gl_trial_balance_policy_evidence,
                    user,
                    COMPANY_A,
                )
                frappe.local.request.method = "POST"
                frappe.local.session = {"user": USER}
                frappe.form_dict = {"cmd": METHOD}

    def test_authority_uses_active_session_and_exact_role_boundary(
        self,
    ) -> None:
        authority = endpoint._authority_snapshot()
        self.assertEqual(authority.user, USER)
        self.assertEqual(authority.companies, (COMPANY_A,))
        self.assertIn("Accounts Manager", authority.roles)
        for roles in (
            ["Accounts User"],
            ["Accounts Manager", "System Manager"],
            ["Accounts Manager", "Administrator"],
            ["Accounts Manager", "Bypass Finance Scope"],
            ["Accounts Manager", "Accounts Manager"],
        ):
            with self.subTest(roles=roles):
                frappe.get_roles = lambda user, value=roles: value
                with self.assertRaises(ValueError):
                    endpoint._authority_snapshot()

    def test_every_relevant_restrictive_permission_is_rejected(
        self,
    ) -> None:
        for doctype in (
            "Account",
            "GL Entry",
            "Finance Book",
            "Cost Center",
            "Project",
            "Accounting Dimension",
        ):
            with self.subTest(doctype=doctype):
                frappe_permissions.get_user_permissions = (
                    lambda user, value=doctype: {
                        **_permissions(),
                        value: [_permission_entry("RESTRICTED")],
                    }
                )
                with self.assertRaises(ValueError):
                    endpoint._authority_snapshot()
        for applicable_for in ("Account", "GL Entry"):
            with self.subTest(applicable_for=applicable_for):
                frappe_permissions.get_user_permissions = (
                    lambda user, value=applicable_for: {
                        **_permissions(),
                        "Region": [
                            _permission_entry(
                                "REGION",
                                applicable_for=value,
                            )
                        ],
                    }
                )
                with self.assertRaises(ValueError):
                    endpoint._authority_snapshot()

    def test_company_permissions_must_be_explicit_unique_and_global(
        self,
    ) -> None:
        invalid = (
            {},
            {
                "Company": [
                    _permission_entry(
                        COMPANY_A, applicable_for="Account"
                    )
                ]
            },
            {
                "Company": [
                    _permission_entry(
                        COMPANY_A, hide_descendants=1
                    )
                ]
            },
            {
                "Company": [
                    _permission_entry(COMPANY_A),
                    _permission_entry(COMPANY_A),
                ]
            },
        )
        for permissions in invalid:
            with self.subTest(permissions=permissions):
                frappe_permissions.get_user_permissions = (
                    lambda user, value=permissions: value
                )
                with self.assertRaises(ValueError):
                    endpoint._authority_snapshot()

    def test_nine_permission_calls_are_exact(self) -> None:
        runtime = Mock()
        runtime.has_permission.return_value = True
        endpoint._validate_permissions(
            runtime, _snapshot(), USER
        )
        self.assertEqual(runtime.has_permission.call_count, 9)
        self.assertEqual(
            [call.args[2:] for call in runtime.has_permission.call_args_list],
            list(endpoint._PERMISSION_REQUIREMENTS),
        )
        self.assertEqual(
            endpoint._PERMISSION_REQUIREMENTS,
            (
                ("Company", "read"),
                ("Fiscal Year", "read"),
                ("Fiscal Year Company", "read"),
                ("Finance Book", "read"),
                ("Accounting Dimension", "read"),
                ("Account", "read"),
                ("Account", "report"),
                ("GL Entry", "read"),
                ("GL Entry", "report"),
            ),
        )

    def test_fiscal_year_company_parent_contract_is_frozen(self) -> None:
        tree = ast.parse(_RUNTIME_SOURCE)
        self.assertIsInstance(tree, ast.Module)
        self.assertIn(
            'parent = "Fiscal Year" if doctype == '
            '"Fiscal Year Company" else None',
            _RUNTIME_SOURCE,
        )
        self.assertIn("parent_doctype=parent", _RUNTIME_SOURCE)
        self.assertIn("ignore_permissions=False", _RUNTIME_SOURCE)

    def test_multiple_companies_select_aggregate_maxima_only(self) -> None:
        frappe_permissions.get_user_permissions = (
            lambda user: _permissions((COMPANY_A, COMPANY_B))
        )
        first = _measurement(
            floors=_source_floors(account_rows=8),
            max_gl_entries=100,
            response_bytes=5_000,
            elapsed=1_500,
        )
        second = _measurement(
            floors=_source_floors(
                account_manifest_ids=12,
                account_rows=12,
                final_manifest_ids=12,
            ),
            max_gl_entries=300,
            response_bytes=9_000,
            elapsed=2_500,
        )
        with patch.object(
            endpoint,
            "_collect_company",
            side_effect=(first, second),
        ) as collector, patch.object(
            endpoint.time,
            "monotonic_ns",
            side_effect=(0, 5_000_000),
        ):
            result = collect_gl_trial_balance_policy_evidence()
        self.assertEqual(collector.call_count, 2)
        self.assertEqual(
            [
                call.kwargs["company"]
                for call in collector.call_args_list
            ],
            [COMPANY_A, COMPANY_B],
        )
        self.assertEqual(
            result["authority"]["permitted_company_count"], 2
        )
        self.assertEqual(
            result["current_floors"]["max_accounts"], 12
        )
        self.assertEqual(
            result["current_floors"]["max_gl_entries"], 300
        )
        self.assertEqual(
            result["byte_evidence"][
                "current_response_floor_bytes"
            ],
            9_000,
        )
        self.assertEqual(
            result["timing"]["per_company"],
            [
                {"ordinal": 1, "elapsed": 1_500},
                {"ordinal": 2, "elapsed": 2_500},
            ],
        )
        encoded = json.dumps(result, sort_keys=True)
        self.assertNotIn(USER, encoded)
        self.assertNotIn(COMPANY_A, encoded)
        self.assertNotIn(COMPANY_B, encoded)

    def test_session_or_permission_drift_discards_all_evidence(
        self,
    ) -> None:
        authorities = [
            endpoint._AuthorityEvidence(
                user=USER,
                roles=("Accounts Manager",),
                user_permissions=(
                    (
                        "Company",
                        COMPANY_A,
                        None,
                        1,
                        0,
                    ),
                ),
                companies=(COMPANY_A,),
            ),
            endpoint._AuthorityEvidence(
                user="drift@example.test",
                roles=("Accounts Manager",),
                user_permissions=(),
                companies=(COMPANY_A,),
            ),
        ]
        with patch.object(
            endpoint,
            "_authority_snapshot",
            side_effect=authorities,
        ), patch.object(
            endpoint,
            "_collect_company",
            return_value=_measurement(),
        ):
            self._assert_generic(
                collect_gl_trial_balance_policy_evidence,
                USER,
                COMPANY_A,
                "drift@example.test",
            )

    def test_generic_failure_restores_message_log_without_leakage(
        self,
    ) -> None:
        original = frappe.local.message_log
        with patch.object(
            endpoint,
            "_collect_company",
            side_effect=RuntimeError(
                "SELECT * FROM tabGL Entry "
                + COMPANY_A
                + " voucher-canary"
            ),
        ):
            self._assert_generic(
                collect_gl_trial_balance_policy_evidence,
                COMPANY_A,
                "tabGL Entry",
                "voucher-canary",
            )
        self.assertIs(frappe.local.message_log, original)
        self.assertEqual(frappe.local.message_log, [])

    def test_source_forbids_identity_and_permission_bypasses(self) -> None:
        forbidden = (
            "frappe.set_user",
            ".set_user(",
            "ignore_permissions=True",
            "get_all(",
            "allow_guest=True",
            "frappe.db.sql",
            "logger(",
            "log_error",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, _SOURCE)
        self.assertNotIn("max_accounts", json.dumps(_policy()))
        self.assertNotIn("currency_precision", json.dumps(_policy()))

class DiagnosticBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        frappe.local = types.SimpleNamespace(
            request=types.SimpleNamespace(method="POST"),
            session={"user": USER},
            conf={
                endpoint._CONFIG_KEY: _policy(),
                endpoint._DIAGNOSTIC_CONFIG_KEY: {"enabled": True},
            },
            message_log=[],
        )
        frappe.form_dict = {"cmd": DIAGNOSTIC_METHOD}
        frappe.get_roles = lambda user: [
            "Accounts Manager",
            "Accounts User",
        ]
        frappe_permissions.get_user_permissions = (
            lambda user: _permissions()
        )

    def _assert_generic(self) -> None:
        with self.assertRaises(
            GLTrialBalancePolicyEvidenceError
        ) as captured:
            diagnose_gl_trial_balance_policy_evidence_failure_phase()
        self.assertEqual(
            str(captured.exception), "finance_read_unavailable"
        )
        self.assertIsNone(captured.exception.__cause__)
        self.assertIsNone(captured.exception.__context__)

    def test_diagnostic_is_absent_by_default_closed_and_post_only(
        self,
    ) -> None:
        invalid_documents = (
            None,
            {},
            {"enabled": False},
            {"enabled": 1},
            {"enabled": True, "unknown": True},
        )
        for document in invalid_documents:
            with self.subTest(document=document), patch.object(
                endpoint, "_execute_policy_evidence"
            ) as execute:
                frappe.local.conf = {endpoint._CONFIG_KEY: _policy()}
                if document is not None:
                    frappe.local.conf[
                        endpoint._DIAGNOSTIC_CONFIG_KEY
                    ] = document
                self._assert_generic()
                execute.assert_not_called()

        frappe.local.conf[
            endpoint._DIAGNOSTIC_CONFIG_KEY
        ] = {"enabled": True}
        for method, form_dict in (
            ("GET", {"cmd": DIAGNOSTIC_METHOD}),
            ("POST", {"cmd": METHOD}),
            ("POST", {"cmd": DIAGNOSTIC_METHOD, "extra": 1}),
        ):
            with self.subTest(method=method, form_dict=form_dict):
                frappe.local.request.method = method
                frappe.form_dict = form_dict
                self._assert_generic()
        frappe.local.request.method = "POST"
        frappe.form_dict = {"cmd": DIAGNOSTIC_METHOD}

    def test_non_snapshot_failures_return_no_phase_document(
        self,
    ) -> None:
        frappe.local.conf.pop(endpoint._CONFIG_KEY)
        self._assert_generic()

        frappe.local.conf[endpoint._CONFIG_KEY] = _policy()
        frappe_permissions.get_user_permissions = lambda user: {}
        self._assert_generic()

    def test_ineligible_callers_receive_no_phase_document(self) -> None:
        for user, roles in (
            ("Guest", ["Accounts Manager"]),
            ("Administrator", ["Accounts Manager"]),
            (USER, ["Accounts User"]),
            (USER, ["Accounts Manager", "System Manager"]),
        ):
            with self.subTest(user=user, roles=roles):
                frappe.local.session = {"user": user}
                frappe.get_roles = lambda _user, value=roles: value
                self._assert_generic()

    def test_role_preflight_messages_are_contained_and_restored(
        self,
    ) -> None:
        canary = "identity-canary " + USER

        def failing_roles(_user):
            frappe.local.message_log.append(canary)
            raise RuntimeError(canary)

        frappe.get_roles = failing_roles
        self._assert_generic()
        self.assertEqual(frappe.local.message_log, [])

        def noisy_roles(_user):
            frappe.local.message_log.append(canary)
            return ["Accounts Manager"]

        frappe.get_roles = noisy_roles
        self._assert_generic()
        self.assertEqual(frappe.local.message_log, [])

    def test_only_closed_phase_documents_can_leave_the_boundary(
        self,
    ) -> None:
        observable_phases = endpoint._DIAGNOSTIC_FAILURE_PHASES
        for phase in observable_phases:
            with self.subTest(phase=phase), patch.object(
                endpoint,
                "_execute_policy_evidence",
                return_value=(None, phase, True, True),
            ):
                result = (
                    diagnose_gl_trial_balance_policy_evidence_failure_phase()
                )
                self.assertEqual(
                    result,
                    {
                        "code": "finance_read_unavailable",
                        "phase": phase,
                    },
                )
                self.assertEqual(tuple(result), ("code", "phase"))
        for invalid_phase in ("complete", "internal", "identity-canary"):
            with self.subTest(invalid_phase=invalid_phase), patch.object(
                endpoint,
                "_execute_policy_evidence",
                return_value=(None, invalid_phase, True, True),
            ):
                self._assert_generic()

    def test_success_discards_the_full_evidence_document(self) -> None:
        with patch.object(
            endpoint,
            "_execute_policy_evidence",
            return_value=(
                {
                    "state": "evidence_ready",
                    "identity-canary": COMPANY_A,
                },
                None,
                True,
                True,
            ),
        ):
            self.assertEqual(
                diagnose_gl_trial_balance_policy_evidence_failure_phase(),
                {"code": "diagnostic_complete", "phase": "complete"},
            )

    def test_partial_company_and_message_data_are_discarded(self) -> None:
        frappe_permissions.get_user_permissions = (
            lambda user: _permissions((COMPANY_A, COMPANY_B))
        )
        calls = 0

        def collect(*, phase_recorder, **_kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                return _measurement()
            phase_recorder.enter("gl_cohort")
            frappe.local.message_log.append(
                "identity-canary " + COMPANY_B
            )
            raise RuntimeError("SELECT voucher-canary")

        with patch.object(endpoint, "_collect_company", collect):
            self._assert_generic()
        self.assertEqual(frappe.local.message_log, [])
        encoded = json.dumps(frappe.local.message_log, sort_keys=True)
        for canary in (
            USER,
            COMPANY_A,
            COMPANY_B,
            "SELECT",
            "voucher-canary",
        ):
            self.assertNotIn(canary, encoded)

    def test_uncertain_message_cleanup_returns_only_generic_error(
        self,
    ) -> None:
        def collect(*, phase_recorder, **_kwargs):
            phase_recorder.enter("snapshot_subphase_complete")
            raise RuntimeError("identity-canary " + COMPANY_A)

        recorder = endpoint._PhaseRecorder()
        with patch.object(
            endpoint, "_collect_company", collect
        ), patch.object(
            endpoint, "_restore_message_log", return_value=False
        ):
            result = endpoint._execute_policy_evidence(
                method_path=DIAGNOSTIC_METHOD,
                phase_recorder=recorder,
                require_diagnostic_authority=True,
            )
        self.assertIsNone(result[0])
        self.assertEqual(result[1], "snapshot_subphase_complete")
        self.assertFalse(result[2])
        self.assertTrue(result[3])
        with patch.object(
            endpoint, "_execute_policy_evidence", return_value=result
        ):
            self._assert_generic()

    def test_phase_recorder_rejects_dynamic_values(self) -> None:
        recorder = endpoint._PhaseRecorder()
        recorder.enter("snapshot_state")
        self.assertEqual(recorder.phase, "snapshot_state")
        recorder.enter("snapshot_state:" + COMPANY_A)
        self.assertEqual(recorder.phase, "internal")
        recorder.enter("snapshot_validate")
        self.assertEqual(recorder.phase, "internal")
        recorder.reset()
        recorder.enter("snapshot_state")
        recorder.enter(["snapshot_state"])
        self.assertEqual(recorder.phase, "internal")
        recorder.enter("snapshot_validate")
        self.assertEqual(recorder.phase, "internal")

    def test_known_collector_markers_preserve_snapshot_phase(self) -> None:
        recorder = endpoint._PhaseRecorder()
        recorder.enter("snapshot_state")
        for phase in endpoint._NON_SNAPSHOT_COLLECTOR_PHASES:
            with self.subTest(phase=phase):
                endpoint._enter_phase(recorder, phase)
                self.assertEqual(recorder.phase, "snapshot_state")
        endpoint._enter_phase(recorder, "dynamic:" + COMPANY_A)
        self.assertEqual(recorder.phase, "internal")

    def test_snapshot_phase_allowlist_is_exact(self) -> None:
        self.assertEqual(
            endpoint._DIAGNOSTIC_FAILURE_PHASES,
            frozenset(
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
                    "snapshot_subphase_complete",
                }
            ),
        )
        self.assertEqual(endpoint._DIAGNOSTIC_SUCCESS_PHASE, "complete")
        self.assertNotIn(
            endpoint._DIAGNOSTIC_SUCCESS_PHASE,
            endpoint._DIAGNOSTIC_FAILURE_PHASES,
        )

    def test_snapshot_phase_order_and_validation_boundary(
        self,
    ) -> None:
        expected = [
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
        ]
        observed: list[str] = []

        class ProbeRuntime:
            def __init__(self, *, snapshot_phase_hook, **_kwargs):
                self.hook = snapshot_phase_hook
                self.closed = 0
                self._snapshot_phase("snapshot_runtime_construct")

            def _snapshot_phase(self, phase):
                observed.append(phase)
                if self.hook is not None:
                    self.hook(phase)

            def begin_read_snapshot(self, _user, _company):
                for phase in expected[1:12]:
                    self._snapshot_phase(phase)
                return _snapshot()

            def close_read_snapshot(self, _snapshot_value):
                self.closed += 1
                raise RuntimeError("cleanup identity-canary")

        recorder = endpoint._PhaseRecorder()
        authority = endpoint._AuthorityEvidence(
            user=USER,
            roles=("Accounts Manager",),
            user_permissions=(),
            companies=(COMPANY_A,),
        )
        with patch.object(
            endpoint, "_EvidenceRuntime", ProbeRuntime
        ), patch.object(
            endpoint,
            "_validate_snapshot",
            side_effect=RuntimeError("validation identity-canary"),
        ):
            with self.assertRaisesRegex(
                ValueError, "finance_read_unavailable"
            ):
                endpoint._collect_company(
                    authority=authority,
                    company=COMPANY_A,
                    runtime_policy=endpoint.GLTrialBalanceRuntimePolicy(
                        "pymysql", "1.1.2", "server"
                    ),
                    phase_recorder=recorder,
                )
        self.assertEqual(observed, expected[:12])
        self.assertEqual(recorder.phase, "snapshot_validate")
        self.assertEqual(observed + [recorder.phase], expected[:13])

    def test_company_collection_resets_phase_before_any_work(self) -> None:
        recorder = endpoint._PhaseRecorder()
        recorder.enter("snapshot_state")
        authority = endpoint._AuthorityEvidence(
            user=USER,
            roles=("Accounts Manager",),
            user_permissions=(),
            companies=(COMPANY_A,),
        )
        with patch.object(
            endpoint.time,
            "monotonic_ns",
            side_effect=RuntimeError("identity-canary"),
        ):
            with self.assertRaises(RuntimeError):
                endpoint._collect_company(
                    authority=authority,
                    company=COMPANY_A,
                    runtime_policy=endpoint.GLTrialBalanceRuntimePolicy(
                        "pymysql", "1.1.2", "server"
                    ),
                    phase_recorder=recorder,
                )
        self.assertEqual(recorder.phase, "internal")

    def test_normal_collection_passes_no_snapshot_hook(self) -> None:
        hooks = []

        class InertProbeRuntime:
            def __init__(self, *, snapshot_phase_hook, **_kwargs):
                hooks.append(snapshot_phase_hook)

            def begin_read_snapshot(self, _user, _company):
                raise RuntimeError("stop")

        authority = endpoint._AuthorityEvidence(
            user=USER,
            roles=("Accounts Manager",),
            user_permissions=(),
            companies=(COMPANY_A,),
        )
        with patch.object(endpoint, "_EvidenceRuntime", InertProbeRuntime):
            with self.assertRaisesRegex(
                ValueError, "finance_read_unavailable"
            ):
                endpoint._collect_company(
                    authority=authority,
                    company=COMPANY_A,
                    runtime_policy=endpoint.GLTrialBalanceRuntimePolicy(
                        "pymysql", "1.1.2", "server"
                    ),
                    phase_recorder=None,
                )
        self.assertEqual(hooks, [None])


class EvidenceRuntimeQueryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot = _snapshot()
        self.runtime = object.__new__(endpoint._EvidenceRuntime)
        self.runtime._aggregate_one = Mock()

    def test_all_evidence_count_queries_are_literal_and_parameterized(
        self,
    ) -> None:
        cases = (
            (
                self.runtime.count_company,
                (self.snapshot, COMPANY_A),
                endpoint._COUNT_COMPANY_SQL,
                {"company": COMPANY_A},
            ),
            (
                self.runtime.count_active_fiscal_years,
                (self.snapshot,),
                endpoint._COUNT_ACTIVE_FISCAL_YEARS_SQL,
                {},
            ),
            (
                self.runtime.count_fiscal_year_company,
                (self.snapshot, COMPANY_A),
                endpoint._COUNT_FISCAL_YEAR_COMPANY_SQL,
                {"company": COMPANY_A},
            ),
            (
                self.runtime.count_finance_book,
                (self.snapshot, "DEFAULT_BOOK"),
                endpoint._COUNT_FINANCE_BOOK_SQL,
                {"finance_book": "DEFAULT_BOOK"},
            ),
            (
                self.runtime.count_active_dimensions,
                (self.snapshot,),
                endpoint._COUNT_ACTIVE_DIMENSIONS_SQL,
                {},
            ),
        )
        for callback, arguments, statement, parameters in cases:
            with self.subTest(statement=statement):
                self.runtime._aggregate_one.reset_mock()
                self.runtime._aggregate_one.return_value = (7,)
                self.assertEqual(callback(*arguments), 7)
                self.runtime._aggregate_one.assert_called_once_with(
                    self.snapshot, statement, parameters
                )

    def test_unknown_statement_and_malformed_counts_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "finance_read_unavailable"):
            self.runtime._evidence_row(
                self.snapshot, "SELECT identity_canary", {}
            )
        for row in ((-1,), (True,), (1, 2), ("company-canary",)):
            with self.subTest(row=row):
                self.runtime._aggregate_one.return_value = row
                with self.assertRaisesRegex(
                    ValueError, "finance_read_unavailable"
                ):
                    self.runtime.count_company(
                        self.snapshot, COMPANY_A
                    )

    def test_statement_ceiling_enabled_disabled_and_malformed_states(
        self,
    ) -> None:
        cases = (
            (
                (Decimal("0"), Decimal("90")),
                {
                    "global_state": "disabled",
                    "global_microseconds": 0,
                    "session_state": "enabled",
                    "session_microseconds": 90_000_000,
                },
            ),
            (
                (Decimal("120"), Decimal("0")),
                {
                    "global_state": "enabled",
                    "global_microseconds": 120_000_000,
                    "session_state": "disabled",
                    "session_microseconds": 0,
                },
            ),
        )
        for row, expected in cases:
            with self.subTest(row=row):
                self.runtime._aggregate_one.return_value = row
                self.assertEqual(
                    self.runtime.statement_ceiling(self.snapshot),
                    expected,
                )
        for row in (
            (Decimal("1.0000001"), Decimal("1")),
            (Decimal("-1"), Decimal("1")),
            (Decimal("NaN"), Decimal("1")),
            (Decimal("1"),),
        ):
            with self.subTest(row=row):
                self.runtime._aggregate_one.return_value = row
                with self.assertRaises(ValueError):
                    self.runtime.statement_ceiling(self.snapshot)

    def test_numeric_currency_and_identifier_shapes_are_exact(self) -> None:
        self.runtime._aggregate_one.return_value = (2, 21, 21, 9, 9)
        self.assertEqual(
            self.runtime.numeric_shape(self.snapshot),
            {"numeric_precision": 21, "numeric_scale": 9},
        )
        self.runtime._aggregate_one.return_value = (
            1,
            100,
            100,
            Decimal("0.01"),
            Decimal("0.01"),
        )
        self.assertEqual(
            self.runtime.currency_metadata(self.snapshot, "MMK"),
            (100, Decimal("0.01")),
        )
        self.runtime._aggregate_one.return_value = (
            140,
            "utf8mb4",
            140,
            "utf8mb4",
            140,
            "utf8mb4",
            3,
            "ascii",
            140,
            "utf8mb4",
        )
        envelopes = self.runtime.identifier_envelopes(self.snapshot)
        self.assertEqual(
            frozenset(envelopes),
            frozenset(
                {
                    "account",
                    "company",
                    "fiscal_year",
                    "currency",
                    "finance_book",
                }
            ),
        )
        self.assertEqual(
            envelopes["account"],
            {
                "characters": 140,
                "utf8_bytes": 560,
                "json_string_bytes": 562,
            },
        )
        self.assertEqual(
            envelopes["currency"],
            {
                "characters": 3,
                "utf8_bytes": 3,
                "json_string_bytes": 8,
            },
        )

    def test_malformed_database_shapes_fail_closed(self) -> None:
        malformed_numeric = (
            (1, 21, 21, 9, 9),
            (2, 21, 22, 9, 9),
            (2, 8, 8, 9, 9),
            (2, True, True, 0, 0),
        )
        for row in malformed_numeric:
            with self.subTest(row=row):
                self.runtime._aggregate_one.return_value = row
                with self.assertRaises(ValueError):
                    self.runtime.numeric_shape(self.snapshot)
        malformed_currency = (
            (0, None, None, None, None),
            (1, 100, 99, Decimal("0.01"), Decimal("0.01")),
            (1, 100, 100, Decimal("0"), Decimal("0")),
        )
        for row in malformed_currency:
            with self.subTest(row=row):
                self.runtime._aggregate_one.return_value = row
                with self.assertRaises(ValueError):
                    self.runtime.currency_metadata(
                        self.snapshot, "MMK"
                    )
        self.runtime._aggregate_one.return_value = (
            140,
            "unproved-charset",
        ) * 5
        with self.assertRaises(ValueError):
            self.runtime.identifier_envelopes(self.snapshot)

    def test_account_and_gl_counts_reuse_committed_exact_cohort(self) -> None:
        self.runtime._count_accounts = Mock(return_value=13)
        self.runtime._count_gl_entries = Mock(return_value=144)
        self.assertEqual(
            self.runtime.count_accounts(self.snapshot, COMPANY_A), 13
        )
        self.assertEqual(
            self.runtime.count_gl_entries(
                self.snapshot,
                COMPANY_A,
                date(2026, 12, 31),
                "DEFAULT_BOOK",
            ),
            144,
        )
        self.assertIn(
            "`posting_date` <= %(to_date)s AND `is_cancelled` = 0",
            runtime_source._GL_COUNT_SQL,
        )
        self.assertNotIn("from_date", runtime_source._GL_COUNT_SQL)
        self.assertIn(
            "`finance_book` = %(finance_book)s OR `finance_book` = '' "
            "OR `finance_book` IS NULL",
            runtime_source._GL_COUNT_SQL,
        )


class PrecisionAndSizingTests(unittest.TestCase):
    def _precision_evidence(
        self,
        *,
        database_value: object = 2,
        settings_value: object = 2,
        global_value: object = 2,
        debit_value: object = 2,
        credit_value: object = 2,
        rounding_method: object = "Commercial Rounding",
        currency_metadata: tuple[int, Decimal] = (
            100,
            Decimal("0.01"),
        ),
    ) -> dict[str, object]:
        erpnext_module = types.ModuleType("erpnext")
        erpnext_module.__path__ = []  # type: ignore[attr-defined]
        accounts_module = types.ModuleType("erpnext.accounts")
        accounts_module.__path__ = []  # type: ignore[attr-defined]
        utils_module = types.ModuleType("erpnext.accounts.utils")
        utils_module.get_currency_precision = Mock(
            return_value=global_value
        )
        model_module = types.ModuleType("frappe.model")
        model_module.__path__ = []  # type: ignore[attr-defined]
        meta_module = types.ModuleType("frappe.model.meta")
        meta_module.get_field_precision = Mock(
            side_effect=(debit_value, credit_value)
        )
        modules = {
            "erpnext": erpnext_module,
            "erpnext.accounts": accounts_module,
            "erpnext.accounts.utils": utils_module,
            "frappe.model": model_module,
            "frappe.model.meta": meta_module,
        }
        runtime = Mock()
        runtime.currency_metadata.return_value = currency_metadata
        database = types.SimpleNamespace(
            get_single_value=Mock(return_value=database_value)
        )
        settings = {
            "currency_precision": settings_value,
            "rounding_method": rounding_method,
        }
        meta = types.SimpleNamespace(
            get_field=Mock(side_effect=(object(), object()))
        )
        with patch.dict(sys.modules, modules), patch.object(
            frappe, "db", database, create=True
        ), patch.object(
            frappe,
            "get_system_settings",
            Mock(side_effect=lambda key: settings[key]),
            create=True,
        ), patch.object(
            frappe, "get_meta", Mock(return_value=meta), create=True
        ), patch.object(endpoint, "_checkpoint", Mock()):
            return dict(
                endpoint._precision_evidence(
                    runtime,
                    _snapshot(),
                    user=USER,
                    company=COMPANY_A,
                    base_currency="MMK",
                )
            )

    def test_precision_requires_exact_five_way_and_rounding_agreement(
        self,
    ) -> None:
        self.assertEqual(
            self._precision_evidence(),
            {
                "precision": 2,
                "system_settings_agreement": True,
                "effective_debit_agreement": True,
                "effective_credit_agreement": True,
                "currency_rounding_agreement": True,
                "rounding_method_recognized": True,
            },
        )
        cases = (
            {"database_value": 3},
            {"settings_value": 3},
            {"global_value": 3},
            {"debit_value": 3},
            {"credit_value": 3},
            {"rounding_method": "identity-canary"},
            {
                "currency_metadata": (
                    3,
                    Decimal("0.33"),
                )
            },
            {"global_value": 9},
        )
        for changes in cases:
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    self._precision_evidence(**changes)

    def test_canonical_response_measurement_matches_service_contract(
        self,
    ) -> None:
        request = GLTrialBalanceServiceRequest(
            company=COMPANY_A,
            fiscal_year="FY-2026",
            from_date=date(2026, 1, 1),
            to_date=date(2026, 12, 31),
        )
        result = _result(
            child_name='1110 - ' + UNICODE_CANARY + ' "Main" \\Cash'
        )
        measurement = endpoint._response_measurement(
            result=result,
            request=request,
            max_accounts=2,
            max_gl_entries=120,
            numeric_precision=21,
            numeric_scale=9,
        )
        envelope = {
            "company": COMPANY_A,
            "fiscal_year": "FY-2026",
            "from_date": "2026-01-01",
            "to_date": "2026-12-31",
        }
        expected_envelope = json.dumps(
            envelope,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        self.assertEqual(
            measurement["request_envelope_bytes"],
            len(expected_envelope),
        )
        self.assertEqual(measurement["line_count"], 2)
        self.assertEqual(measurement["aggregation_digit_growth"], 3)
        self.assertEqual(measurement["fixed_decimal_width_bound"], 18)
        self.assertGreater(
            measurement["response_bytes"],
            measurement["response_metadata_bytes"],
        )
        policy = endpoint.GLTrialBalanceServicePolicy(
            currency_precision=2,
            max_accounts=2,
            max_gl_entries=120,
            max_metadata_bytes=100_000,
            max_response_bytes=100_000,
        )
        encoded = endpoint._build_response(
            result=result, request=request, policy=policy
        )
        self.assertEqual(len(encoded), measurement["response_bytes"])
        self.assertTrue(encoded.endswith(b"\n"))
        self.assertFalse(encoded.endswith(b"\n\n"))
        self.assertIn(UNICODE_CANARY.encode("utf-8"), encoded)
        self.assertIn(b'\\"Main\\"', encoded)
        self.assertIn(b"\\\\Cash", encoded)

    def test_metadata_excludes_hierarchy_and_current_floor_is_not_maximum(
        self,
    ) -> None:
        request = GLTrialBalanceServiceRequest(
            company=COMPANY_A,
            fiscal_year="FY-2026",
            from_date=date(2026, 1, 1),
            to_date=date(2026, 12, 31),
        )
        first = endpoint._response_measurement(
            result=_result(child_name="SHORT"),
            request=request,
            max_accounts=2,
            max_gl_entries=10,
            numeric_precision=21,
            numeric_scale=9,
        )
        second = endpoint._response_measurement(
            result=_result(child_name="LONG-HIERARCHY-NAME-\"-\\-?"),
            request=request,
            max_accounts=2,
            max_gl_entries=10,
            numeric_precision=21,
            numeric_scale=9,
        )
        self.assertEqual(
            first["response_metadata_bytes"],
            second["response_metadata_bytes"],
        )
        self.assertNotEqual(
            first["response_bytes"], second["response_bytes"]
        )
        authority = endpoint._AuthorityEvidence(
            user=USER,
            roles=("Accounts Manager",),
            user_permissions=(),
            companies=(COMPANY_A,),
        )
        document = endpoint._result_document(
            authority=authority,
            runtime_policy=endpoint.GLTrialBalanceRuntimePolicy(
                expected_driver="mysqlclient",
                expected_driver_version="2.2.7",
                expected_server_version="server",
            ),
            measurements=(_measurement(),),
            started_ns=endpoint.time.monotonic_ns(),
        )
        self.assertFalse(
            document["byte_evidence"]["hierarchy_in_metadata"]
        )
        self.assertEqual(
            document["byte_evidence"]["structural_maximum_state"],
            "unproven",
        )
        self.assertIsNone(
            document["byte_evidence"]["structural_maximum_bytes"]
        )
        self.assertEqual(
            document["byte_evidence"]["current_response_basis"],
            "full_fiscal_year_each_applicable_endpoint",
        )

    def test_metadata_floor_is_maximum_of_request_and_response_metadata(
        self,
    ) -> None:
        values = (
            {
                "request_envelope_bytes": 900,
                "response_metadata_bytes": 700,
                "response_bytes": 4_000,
                "line_count": 4,
                "max_observed_depth": 2,
                "max_observed_depth_width": 1,
                "max_identifier_utf8_bytes_observed": 30,
                "max_identifier_escape_extra_bytes_observed": 3,
                "max_parent_identifier_utf8_bytes_observed": 20,
                "max_fixed_decimal_bytes_observed": 10,
                "aggregation_digit_growth": 1,
                "fixed_decimal_width_bound": 18,
            },
            {
                "request_envelope_bytes": 100,
                "response_metadata_bytes": 1_100,
                "response_bytes": 8_000,
                "line_count": 8,
                "max_observed_depth": 3,
                "max_observed_depth_width": 1,
                "max_identifier_utf8_bytes_observed": 40,
                "max_identifier_escape_extra_bytes_observed": 4,
                "max_parent_identifier_utf8_bytes_observed": 25,
                "max_fixed_decimal_bytes_observed": 12,
                "aggregation_digit_growth": 2,
                "fixed_decimal_width_bound": 19,
            },
        )
        aggregate = endpoint._aggregate_response_measurements(values)
        self.assertEqual(aggregate["request_envelope_max_bytes"], 900)
        self.assertEqual(aggregate["response_metadata_max_bytes"], 1_100)
        self.assertEqual(aggregate["current_metadata_floor_bytes"], 1_100)
        self.assertEqual(aggregate["current_response_floor_bytes"], 8_000)
        self.assertEqual(aggregate["current_response_floor_line_count"], 8)

class ResultSchemaAndContainmentTests(unittest.TestCase):
    def setUp(self) -> None:
        frappe.local = types.SimpleNamespace(
            request=types.SimpleNamespace(method="POST"),
            session={"user": USER},
            conf={endpoint._CONFIG_KEY: _policy()},
            message_log=[],
        )
        frappe.form_dict = {"cmd": METHOD}
        frappe.get_roles = lambda user: [
            "Accounts Manager",
            "Accounts User",
        ]
        frappe_permissions.get_user_permissions = (
            lambda user: _permissions((COMPANY_A, COMPANY_B))
        )
        self.authority = endpoint._AuthorityEvidence(
            user=USER,
            roles=("Accounts Manager",),
            user_permissions=(),
            companies=(COMPANY_A,),
        )
        self.runtime_policy = endpoint.GLTrialBalanceRuntimePolicy(
            expected_driver="mysqlclient",
            expected_driver_version="2.2.7",
            expected_server_version="10.6.25-MariaDB-synthetic",
        )

    def _document(
        self, *measurements: endpoint._CompanyMeasurement
    ) -> dict[str, object]:
        with patch.object(
            endpoint.time, "monotonic_ns", return_value=4_000_000
        ):
            return endpoint._result_document(
                authority=self.authority,
                runtime_policy=self.runtime_policy,
                measurements=measurements or (_measurement(),),
                started_ns=0,
            )

    def test_every_max_accounts_source_group_can_set_the_floor(self) -> None:
        self.assertEqual(tuple(_source_floors()), endpoint._SOURCE_GROUPS)
        for source_group in endpoint._SOURCE_GROUPS:
            floors = _source_floors()
            floors[source_group] = 101
            with self.subTest(source_group=source_group):
                result = self._document(
                    _measurement(floors=floors)
                )
                self.assertEqual(
                    result["current_floors"][source_group], 101
                )
                self.assertEqual(
                    result["current_floors"]["max_accounts"], 101
                )

    def test_output_schema_is_closed_aggregate_only_and_identity_free(
        self,
    ) -> None:
        result = self._document()
        self.assertEqual(
            tuple(result),
            (
                "schema_version",
                "state",
                "boundary",
                "authority",
                "environment",
                "precision",
                "accounting_shape",
                "current_floors",
                "date_scope",
                "byte_evidence",
                "timing",
            ),
        )
        self.assertEqual(result["state"], "evidence_ready")
        self.assertEqual(
            result["boundary"],
            {
                "read_only": True,
                "evidence_only": True,
                "production_limit_policy_selected": False,
                "production_limit_policy_injected": False,
                "environment_compatibility_policy_required": True,
                "accounting_execution_enabled": False,
                "identities_returned": False,
            },
        )
        encoded = json.dumps(result, sort_keys=True)
        for canary in (
            USER,
            COMPANY_A,
            COMPANY_B,
            "voucher-canary",
            "party-canary",
            "connection-canary",
        ):
            self.assertNotIn(canary, encoded)
        self.assertEqual(
            result["timing"]["per_company"],
            [{"ordinal": 1, "elapsed": 1_000}],
        )
        self.assertEqual(
            result["timing"]["known_request_ceiling"],
            120_000_000,
        )
        self.assertEqual(
            result["timing"]["collector_elapsed"], 4_000
        )
        self.assertTrue(
            result["timing"][
                "collector_below_known_request_ceiling"
            ]
        )
        self.assertEqual(
            result["timing"]["full_request_completion_state"],
            "unproven",
        )

    def test_result_rejects_cross_company_shape_or_policy_drift(self) -> None:
        self.authority = endpoint._AuthorityEvidence(
            user=USER,
            roles=("Accounts Manager",),
            user_permissions=(),
            companies=(COMPANY_A, COMPANY_B),
        )
        cases = (
            (
                _measurement(),
                _measurement(precision=3),
            ),
            (
                _measurement(),
                replace(
                    _measurement(),
                    database_shape={
                        "numeric_precision": 18,
                        "numeric_scale": 6,
                    },
                ),
            ),
        )
        for measurements in cases:
            with self.subTest(measurements=measurements):
                with self.assertRaises(ValueError):
                    self._document(*measurements)

    def test_partial_multi_company_failure_returns_only_generic_error(
        self,
    ) -> None:
        with patch.object(
            endpoint,
            "_collect_company",
            side_effect=(
                _measurement(),
                RuntimeError(
                    "SELECT identity-canary FROM tabGL Entry "
                    + COMPANY_B
                ),
            ),
        ):
            with self.assertRaises(
                GLTrialBalancePolicyEvidenceError
            ) as captured:
                collect_gl_trial_balance_policy_evidence()
        self.assertEqual(
            str(captured.exception), "finance_read_unavailable"
        )
        self.assertIsNone(captured.exception.__cause__)
        self.assertIsNone(captured.exception.__context__)
        self.assertEqual(frappe.local.message_log, [])

    def test_accounting_and_permission_boundaries_are_pinned(self) -> None:
        collector_source = inspect.getsource(endpoint._collect_company)
        for required in (
            "_validate_effective_permissions",
            "_validate_permissions",
            "_validate_fiscal_applicability",
            "_validate_manifest",
            "_read_with_snapshot",
            "final_effective != effective",
            'state not in {"global", "selected_company"}',
            "active_dimension_count != 0",
            "finance_book_count != 1",
            "runtime.count_gl_entries",
            "runtime.close_read_snapshot(snapshot)",
        ):
            with self.subTest(required=required):
                self.assertIn(required, collector_source)
        self.assertIn(
            '"eligible_cohort_nonzero_cancelled_rows": 0', _SOURCE
        )
        self.assertIn(
            '"finance_book_cohort_exact": True', _SOURCE
        )
        self.assertIn(
            '"opening_history_available": True', _SOURCE
        )

    def test_committed_transaction_and_reconnect_contract_is_reused(
        self,
    ) -> None:
        for statement in (
            "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ",
            "START TRANSACTION READ ONLY, WITH CONSISTENT SNAPSHOT",
            "ROLLBACK AND NO CHAIN",
            "SELECT VERSION(), CONNECTION_ID(), @@in_transaction",
        ):
            self.assertIn(statement, _RUNTIME_SOURCE)
        for continuity in (
            "same_connection=True",
            "reconnect_denied=True",
            "self._validate_binding(context, wrapper, raw)",
            "self._state(context)",
            "getattr(context.raw_connection, \"close\")()",
        ):
            self.assertIn(continuity, _RUNTIME_SOURCE)
        self.assertIn(
            "runtime.final_snapshot_evidence(snapshot)", _SOURCE
        )
        self.assertEqual(
            _SOURCE.count("runtime.close_read_snapshot(snapshot)"), 2
        )

    def test_endpoint_import_surface_has_no_external_side_effect_provider(
        self,
    ) -> None:
        tree = ast.parse(_SOURCE)
        imported_roots = {
            alias.name.split(".")[0]
            for node in tree.body
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported_roots.update(
            node.module.split(".")[0]
            for node in tree.body
            if isinstance(node, ast.ImportFrom)
            and node.module is not None
        )
        self.assertFalse(
            imported_roots
            & {
                "os",
                "pathlib",
                "socket",
                "subprocess",
                "requests",
                "redis",
                "docker",
            }
        )
        forbidden_calls = (
            "open(",
            "connect(",
            "requests.",
            "socket.",
            "subprocess.",
            "redis.",
            "docker.",
        )
        for token in forbidden_calls:
            self.assertNotIn(token, _SOURCE)
        self.assertEqual(
            _SOURCE.count("@frappe.whitelist("), 2
        )

    def test_existing_runtime_not_modified_by_evidence_subclass(self) -> None:
        self.assertIs(
            endpoint._EvidenceRuntime.begin_read_snapshot,
            runtime_source.FrappeGLTrialBalanceRuntime.begin_read_snapshot,
        )
        self.assertIs(
            endpoint._EvidenceRuntime.close_read_snapshot,
            runtime_source.FrappeGLTrialBalanceRuntime.close_read_snapshot,
        )
        self.assertIs(
            endpoint._EvidenceRuntime.final_snapshot_evidence,
            runtime_source.FrappeGLTrialBalanceRuntime.final_snapshot_evidence,
        )

class CollectorOrchestrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.authority = endpoint._AuthorityEvidence(
            user=USER,
            roles=("Accounts Manager",),
            user_permissions=(
                ("Company", COMPANY_A, None, 1, 0),
            ),
            companies=(COMPANY_A,),
        )
        self.policy = endpoint.GLTrialBalanceRuntimePolicy(
            expected_driver="mysqlclient",
            expected_driver_version="2.2.7",
            expected_server_version="10.6.25-MariaDB-synthetic",
        )

    def _runtime(self, state: str = "selected_company"):
        rule = UserPermissionRule(
            allow="Company",
            for_value=COMPANY_A,
            applicable_for=None,
            apply_to_all_doctypes=1,
            hide_descendants=0,
        )
        runtime = _adapter_runtime_for_company(
            COMPANY_A, (rule,)
        )
        fiscal_manifest = _adapter_fiscal_manifest(
            company=COMPANY_A,
            fiscal_year_applicability=(
                (ADAPTER_FISCAL_YEAR, state),
            ),
        )
        runtime.fiscal_manifests = [
            fiscal_manifest,
            fiscal_manifest,
        ]
        if state == "global":
            runtime.rows["Fiscal Year Company"] = []
        runtime.count_company = Mock(return_value=1)
        runtime.count_active_fiscal_years = Mock(return_value=1)
        runtime.count_fiscal_year_company = Mock(
            return_value=0 if state == "global" else 1
        )
        runtime.count_finance_book = Mock(return_value=1)
        runtime.count_active_dimensions = Mock(return_value=0)
        runtime.count_accounts = Mock(
            return_value=len(runtime.rows["Account"])
        )
        runtime.count_gl_entries = Mock(
            return_value=len(runtime.rows["GL Entry"])
        )
        runtime.statement_ceiling = Mock(
            return_value={
                "global_state": "disabled",
                "global_microseconds": 0,
                "session_state": "enabled",
                "session_microseconds": 90_000_000,
            }
        )
        runtime.numeric_shape = Mock(
            return_value={
                "numeric_precision": 21,
                "numeric_scale": 9,
            }
        )
        runtime.identifier_envelopes = Mock(
            return_value=_measurement().identifier_envelopes
        )
        return runtime

    def _collect(self, runtime, phase_recorder=None):
        precision = {
            "precision": 2,
            "system_settings_agreement": True,
            "effective_debit_agreement": True,
            "effective_credit_agreement": True,
            "currency_rounding_agreement": True,
            "rounding_method_recognized": True,
        }
        with patch.object(
            endpoint, "_EvidenceRuntime", return_value=runtime
        ), patch.object(
            endpoint, "_precision_evidence", return_value=precision
        ), patch.object(
            endpoint,
            "_authority_snapshot",
            return_value=self.authority,
        ), patch.object(
            endpoint.time,
            "monotonic_ns",
            side_effect=(0, 2_000_000),
        ):
            return endpoint._collect_company(
                authority=self.authority,
                company=COMPANY_A,
                runtime_policy=self.policy,
                phase_recorder=phase_recorder,
            )

    def test_selected_and_global_fiscal_states_execute_complete_glue(
        self,
    ) -> None:
        for state in ("selected_company", "global"):
            runtime = self._runtime(state)
            with self.subTest(state=state):
                measurement = self._collect(runtime)
                self.assertEqual(
                    tuple(measurement.source_floors),
                    endpoint._SOURCE_GROUPS,
                )
                self.assertEqual(
                    measurement.source_floors["company_rows"], 1
                )
                self.assertEqual(
                    measurement.source_floors[
                        "active_fiscal_year_rows"
                    ],
                    1,
                )
                self.assertEqual(
                    measurement.source_floors[
                        "fiscal_year_company_rows"
                    ],
                    0 if state == "global" else 1,
                )
                self.assertEqual(
                    measurement.source_floors["account_rows"], 10
                )
                self.assertEqual(
                    measurement.source_floors[
                        "final_manifest_ids"
                    ],
                    10,
                )
                self.assertEqual(measurement.max_gl_entries, 10)
                self.assertEqual(measurement.fiscal_endpoints, 1)
                self.assertGreater(
                    measurement.byte_evidence[
                        "current_response_floor_bytes"
                    ],
                    0,
                )
                self.assertEqual(len(runtime.closed), 2)
                runtime.count_gl_entries.assert_called_once_with(
                    runtime.snapshot,
                    COMPANY_A,
                    date(2026, 12, 31),
                    "BOOK_DEFAULT",
                )
                gl_calls = [
                    call
                    for call in runtime.calls
                    if call[0] == "get_list"
                    and call[2] == "GL Entry"
                ]
                self.assertEqual(len(gl_calls), 1)
                self.assertEqual(
                    gl_calls[0][4],
                    (
                        ("company", "=", COMPANY_A),
                        (
                            "posting_date",
                            "<=",
                            date(2026, 12, 31),
                        ),
                        ("is_cancelled", "=", 0),
                    ),
                )
                self.assertEqual(
                    gl_calls[0][5],
                    (
                        (
                            "finance_book",
                            "=",
                            "BOOK_DEFAULT",
                        ),
                        ("finance_book", "=", ""),
                        ("finance_book", "is", "not set"),
                    ),
                )

    def test_orchestration_failure_matrix_discards_and_closes(
        self,
    ) -> None:
        def excluded(runtime):
            manifest = _adapter_fiscal_manifest(
                company=COMPANY_A,
                fiscal_year_applicability=(
                    (ADAPTER_FISCAL_YEAR, "excluded"),
                ),
            )
            runtime.fiscal_manifests = [manifest, manifest]

        def hidden_account(runtime):
            runtime.rows["Account"].pop()

        def hidden_gl(runtime):
            runtime.rows["GL Entry"].pop()

        def cancelled(runtime):
            runtime.rows["GL Entry"][0]["is_cancelled"] = 1

        def wrong_finance_book(runtime):
            runtime.rows["GL Entry"][0]["finance_book"] = (
                "OTHER_BOOK_CANARY"
            )

        def permission_drift(runtime):
            runtime.final_permission_evidence = replace(
                runtime.permission_evidence,
                roles=("Accounts User",),
            )

        def continuity_loss(runtime):
            runtime.final_snapshot = replace(
                runtime.snapshot, stable=False
            )

        cases = (
            ("excluded_fiscal", excluded),
            (
                "nonzero_dimensions",
                lambda runtime: setattr(
                    runtime.count_active_dimensions,
                    "return_value",
                    1,
                ),
            ),
            (
                "missing_finance_book",
                lambda runtime: setattr(
                    runtime.count_finance_book,
                    "return_value",
                    0,
                ),
            ),
            ("hidden_account", hidden_account),
            ("hidden_gl", hidden_gl),
            ("cancelled", cancelled),
            ("wrong_finance_book", wrong_finance_book),
            ("permission_drift", permission_drift),
            ("continuity_loss", continuity_loss),
            (
                "session_drift",
                lambda runtime: setattr(
                    runtime, "user", "session-drift-canary"
                ),
            ),
            (
                "close_failure",
                lambda runtime: setattr(
                    runtime, "close_failure", True
                ),
            ),
        )
        for name, mutate in cases:
            runtime = self._runtime()
            mutate(runtime)
            with self.subTest(name=name):
                with self.assertRaisesRegex(
                    ValueError, "finance_read_unavailable"
                ) as captured:
                    self._collect(runtime)
                error = captured.exception
                self.assertNotIn(COMPANY_A, str(error))
                self.assertNotIn("OTHER_BOOK_CANARY", str(error))
                self.assertNotIn("session-drift-canary", str(error))
                self.assertGreaterEqual(len(runtime.closed), 1)

    def test_downstream_and_cleanup_failures_preserve_snapshot_phase(
        self,
    ) -> None:
        def downstream_and_cleanup(runtime):
            runtime.count_finance_book.return_value = 0
            runtime.close_failure = True

        def missing_finance_book(runtime):
            runtime.count_finance_book.return_value = 0

        def missing_accounts(runtime):
            runtime.count_accounts.return_value = 0

        def gl_count_failure(runtime):
            runtime.count_gl_entries.side_effect = RuntimeError(
                "SELECT identity-canary"
            )

        def statement_failure(runtime):
            runtime.statement_ceiling.side_effect = RuntimeError(
                "connection-canary"
            )

        def cancelled(runtime):
            runtime.rows["GL Entry"][0]["is_cancelled"] = 1

        cases = (
            ("company_scope", missing_finance_book),
            ("account_manifest", missing_accounts),
            ("gl_cohort", gl_count_failure),
            ("statement_schema", statement_failure),
            ("accounting_read", cancelled),
            (
                "snapshot_finalize",
                lambda runtime: setattr(
                    runtime, "close_failure", True
                ),
            ),
            ("downstream_and_cleanup", downstream_and_cleanup),
        )
        for former_phase, mutate in cases:
            runtime = self._runtime()
            mutate(runtime)
            recorder = endpoint._PhaseRecorder()
            with self.subTest(former_phase=former_phase):
                with self.assertRaisesRegex(
                    ValueError, "finance_read_unavailable"
                ):
                    self._collect(runtime, recorder)
                self.assertEqual(
                    recorder.phase, "snapshot_subphase_complete"
                )
