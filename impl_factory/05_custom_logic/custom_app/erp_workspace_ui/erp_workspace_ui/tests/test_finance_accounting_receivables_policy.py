from __future__ import annotations

import re
import sys
import types
import unittest
from datetime import datetime
from pathlib import Path


class _FrappePermissionError(Exception):
    pass


def _install_frappe_stub() -> None:
    if "frappe" in sys.modules:
        return

    frappe_stub = types.ModuleType("frappe")
    frappe_stub.PermissionError = _FrappePermissionError
    frappe_stub.session = types.SimpleNamespace(user=None)
    frappe_stub.get_roles = lambda user=None: []
    frappe_stub.defaults = types.SimpleNamespace(get_user_default=lambda key: None)
    frappe_stub._ = lambda value: value
    frappe_stub.whitelist = lambda *args, **kwargs: (lambda fn: fn) if not args else args[0]

    def throw(message, exc=None):
        raise (exc or Exception)(message)

    frappe_stub.throw = throw

    utils_stub = types.ModuleType("frappe.utils")
    utils_stub.cstr = lambda value="": "" if value is None else str(value)
    utils_stub.now_datetime = lambda: datetime(2026, 7, 6, 0, 0, 0)

    sys.modules["frappe"] = frappe_stub
    sys.modules["frappe.utils"] = utils_stub


_install_frappe_stub()

from erp_workspace_ui.finance_accounting import service


_SOURCE_ROOT = Path(__file__).resolve().parents[1]
_SERVICE_SOURCE = _SOURCE_ROOT / "finance_accounting/service.py"

_COMPANY_SCOPE = {
    "name": "Mingalar Mobile Distribution Co., Ltd.",
    "label": "Mingalar Mobile Distribution Co., Ltd.",
    "currency": "MMK",
}


def _resolver(state="scoped", role_category="manager", selected_company=None):
    return {
        "state": state,
        "source": "single_company_site_fallback",
        "role_category": role_category,
        "selected_company": _COMPANY_SCOPE if selected_company is None else selected_company,
        "rows": [],
        "metrics": [],
        "amounts": [],
        "documents": [],
    }


class TestFinanceReceivablesSourceReadPolicy(unittest.TestCase):
    def assert_no_runtime_payload(self, payload):
        for key in ("rows", "metrics", "amounts", "documents"):
            self.assertEqual(payload[key], [], key)
        self.assertEqual(payload["ar_runtime_data_enabled"], False)
        self.assertEqual(payload["amount_visibility_enabled"], False)
        self.assertEqual(payload["count_runtime_enabled"], False)
        self.assertEqual(payload["runtime_count_enabled"], False)
        self.assertEqual(payload["source_permission_verified"], False)
        self.assertEqual(payload["source_permission_probe_enabled"], False)
        self.assertEqual(payload["source_read_policy_ready"], False)
        self.assertTrue(all(value is False for value in payload["no_effect"].values()))
        response = payload["response_contract"]
        self.assertEqual(response["rows"], [])
        self.assertEqual(response["metrics"], [])
        self.assertEqual(response["amounts"], [])
        self.assertEqual(response["documents"], [])
        self.assertEqual(response["customer_identifiers_enabled"], False)
        self.assertEqual(response["invoice_identifiers_enabled"], False)
        self.assertEqual(response["native_route_enabled"], False)
        self.assertEqual(response["report_enabled"], False)
        self.assertEqual(response["export_enabled"], False)
        self.assertEqual(response["execution_enabled"], False)

    def test_policy_returns_not_ready_without_scoped_resolver(self):
        for state in ("restricted", "unavailable", "selection_required", ""):
            with self.subTest(state=state):
                payload = service.build_receivables_source_read_policy(_resolver(state=state))
                self.assertEqual(payload["state"], "not_ready")
                self.assertEqual(payload["source_read_policy_ready"], False)
                self.assertEqual(payload["policy_contract_accepted"], False)
                self.assertEqual(payload["policy_preconditions_ready"], False)
                self.assertEqual(payload["source_permission_verified"], False)
                self.assertIn(payload["reason"], {"resolver_not_scoped"})
                self.assertIsNone(payload["selected_company"])
                self.assert_no_runtime_payload(payload)

    def test_policy_rejects_non_finance_or_unapproved_roles(self):
        for role_category in ("restricted", "system_admin_only", "executive_only", "review_only", "audit_candidate"):
            with self.subTest(role_category=role_category):
                payload = service.build_receivables_source_read_policy(_resolver(role_category=role_category))
                self.assertEqual(payload["state"], "not_ready")
                self.assertEqual(payload["reason"], "role_not_approved_for_f4c_counts")
                self.assertEqual(payload["source_read_policy_ready"], False)
                self.assertEqual(payload["policy_contract_accepted"], False)
                self.assertEqual(payload["policy_preconditions_ready"], False)
                self.assertEqual(payload["source_permission_verified"], False)
                self.assert_no_runtime_payload(payload)

    def test_policy_accepts_sales_invoice_contract_for_manager_without_runtime_permission(self):
        payload = service.build_receivables_source_read_policy(_resolver(role_category="manager"))

        self.assertEqual(payload["state"], "policy_contract_accepted")
        self.assertEqual(payload["reason"], "source_permission_not_verified")
        self.assertEqual(payload["source"], service.RECEIVABLES_COUNT_SOURCE)
        self.assertEqual(payload["source_allowed"], True)
        self.assertEqual(payload["policy_contract_accepted"], True)
        self.assertEqual(payload["policy_preconditions_ready"], True)
        self.assertEqual(payload["resolver_scoped"], True)
        self.assertEqual(payload["role_eligible_for_count_policy"], True)
        self.assertEqual(payload["source_permission_verified"], False)
        self.assertEqual(payload["source_read_policy_ready"], False)
        self.assertEqual(payload["runtime_count_enabled"], False)
        self.assertEqual(payload["selected_company"], _COMPANY_SCOPE)
        self.assert_no_runtime_payload(payload)

    def test_accounts_user_is_not_ready_until_low_count_policy_exists(self):
        payload = service.build_receivables_source_read_policy(_resolver(role_category="normal_finance"))

        self.assertEqual(payload["state"], "not_ready")
        self.assertEqual(payload["reason"], "low_count_policy_not_ready")
        self.assertEqual(payload["source_allowed"], True)
        self.assertEqual(payload["policy_contract_accepted"], False)
        self.assertEqual(payload["role_eligible_for_count_policy"], False)
        self.assertEqual(payload["source_read_policy_ready"], False)
        self.assertEqual(payload["source_permission_verified"], False)
        self.assertEqual(payload["amount_visibility_enabled"], False)
        self.assert_no_runtime_payload(payload)

    def test_policy_blocks_every_non_sales_invoice_source_in_contract(self):
        blocked = sorted(service.RECEIVABLES_BLOCKED_SOURCES)
        self.assertEqual(
            set(blocked),
            {
                "Accounts Payable",
                "Accounts Receivable",
                "Bank Transaction",
                "Customer",
                "GL Entry",
                "General Ledger",
                "Journal Entry",
                "Payment Entry",
                "Purchase Invoice",
            },
        )
        for source in blocked:
            with self.subTest(source=source):
                payload = service.build_receivables_source_read_policy(_resolver(), source=source)
                self.assertEqual(payload["state"], "not_ready")
                self.assertEqual(payload["reason"], "source_blocked_for_f4c")
                self.assertEqual(payload["source_allowed"], False)
                self.assertEqual(payload["policy_contract_accepted"], False)
                self.assertEqual(payload["policy_preconditions_ready"], False)
                self.assertEqual(payload["source_permission_verified"], False)
                self.assert_no_runtime_payload(payload)

    def test_policy_rejects_unknown_source(self):
        payload = service.build_receivables_source_read_policy(_resolver(), source="Unknown Source")

        self.assertEqual(payload["state"], "not_ready")
        self.assertEqual(payload["reason"], "source_not_allowed_for_f4c")
        self.assertEqual(payload["source_allowed"], False)
        self.assertEqual(payload["policy_contract_accepted"], False)
        self.assertEqual(payload["policy_preconditions_ready"], False)
        self.assertEqual(payload["source_permission_verified"], False)
        self.assert_no_runtime_payload(payload)

    def test_contract_documents_required_filters_and_field_allowlists(self):
        contract = service.receivables_source_read_contract()

        self.assertEqual(contract["allowed_future_source"], "Sales Invoice")
        self.assertEqual(contract["required_filters"]["company"], "selected_allowed_company_from_f4b_resolver")
        self.assertEqual(contract["required_filters"]["docstatus"], 1)
        self.assertEqual(contract["required_filters"]["outstanding_amount"], "> 0")
        self.assertEqual(contract["required_filters"]["is_return"], "exclude_first_cycle")
        self.assertEqual(contract["required_filters"]["return_against"], "exclude_first_cycle")
        self.assertIn("due_date", contract["allowed_internal_fields"])
        self.assertIn("outstanding_amount", contract["allowed_internal_fields"])
        for blocked_field in ("name", "customer", "currency", "invoice_identifier", "route"):
            self.assertIn(blocked_field, contract["blocked_browser_fields"])
        self.assertEqual(contract["report_passthrough_enabled"], False)
        self.assertEqual(contract["runtime_query_enabled"], False)
        self.assertEqual(contract["source_permission_probe_enabled"], False)
        self.assertEqual(contract["source_permission_verified"], False)
        semantics = contract["invoice_semantics"]
        self.assertEqual(semantics["submitted_only"], True)
        self.assertEqual(semantics["cancelled_excluded"], True)
        self.assertEqual(semantics["positive_outstanding_only"], True)
        self.assertEqual(semantics["returns_excluded_first_cycle"], True)
        self.assertEqual(semantics["credit_notes_excluded_first_cycle"], True)
        self.assertEqual(semantics["payment_schedule_policy"], "deferred_until_explicit_policy")

    def test_aging_bucket_contract_is_accounting_friendly_and_backend_dated(self):
        contract = service.receivables_source_read_contract()
        buckets = contract["aging_buckets"]

        self.assertEqual([bucket["key"] for bucket in buckets], [
            "current",
            "overdue_1_30",
            "overdue_31_60",
            "overdue_61_90",
            "overdue_over_90",
        ])
        self.assertEqual(contract["aging_basis"]["as_of_date_source"], "backend_defined_request_date")
        self.assertEqual(contract["aging_basis"]["payment_schedule_basis"], "deferred_until_explicit_policy")
        self.assertEqual(contract["aging_basis"]["timezone_policy"], "backend_site_timezone_required_before_runtime")
        self.assertEqual(contract["low_count_policy"]["runtime_threshold_ready"], False)
        self.assertIn("low_count_suppression_tests", contract["f4d_runtime_prerequisites"])
        self.assertIn("server_side_resolver_dependency", contract["f4d_runtime_prerequisites"])

    def test_response_contract_excludes_customer_invoice_route_and_amount_fields(self):
        payload = service.build_receivables_source_read_policy(_resolver())
        response = payload["response_contract"]
        allowed_keys = set(response["allowed_response_keys"])

        self.assertEqual(
            allowed_keys,
            {
                "as_of_date",
                "bucket_counts",
                "bucket_labels",
                "company_scope",
                "no_effect",
                "policy",
            },
        )
        self.assertEqual(
            set(response["blocked_empty_placeholder_keys"]),
            {"amounts", "documents", "metrics", "rows"},
        )
        self.assertIn("bucket_counts", allowed_keys)
        self.assertIn("bucket_labels", allowed_keys)
        self.assertNotIn("customer", allowed_keys)
        self.assertNotIn("invoice", allowed_keys)
        self.assertNotIn("route", allowed_keys)
        self.assertNotIn("amount_total", allowed_keys)
        self.assertNotIn("rows", allowed_keys)
        self.assertNotIn("amounts", allowed_keys)
        self.assertNotIn("documents", allowed_keys)
        self.assert_no_runtime_payload(payload)

    def test_backend_source_has_no_f4c_query_or_mutation_apis(self):
        source = _SERVICE_SOURCE.read_text(encoding="utf-8")
        forbidden_patterns = [
            r"frappe\.get_all",
            r"frappe\.get_list\s*\(",
            r"frappe\.db\.sql",
            r"ignore_permissions",
            r"frappe\.get_doc",
            r"#Form/",
            r"frappe\.set_route",
            r"/app",
            r"/desk/Form",
            r"/desk/List",
            r"/desk/Report",
            r"query-report",
            r"\.save\(",
            r"\.submit\(",
            r"\.cancel\(",
            r"delete_doc",
            r"set_value",
            r"enqueue",
            r"sendmail",
        ]
        for pattern in forbidden_patterns:
            self.assertIsNone(re.search(pattern, source), pattern)

        allowed_config_reads = set(re.findall(r'_safe_config_list\(\s*"([^"]+)"', source))
        self.assertEqual(allowed_config_reads, {"Company", "User Permission"})
        self.assertNotIn('getattr(frappe, "get_list", None)(', source)


if __name__ == "__main__":
    unittest.main()
