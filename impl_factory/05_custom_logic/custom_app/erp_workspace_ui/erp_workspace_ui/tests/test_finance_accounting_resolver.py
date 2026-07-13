from __future__ import annotations

import re
import sys
import types
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch


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

import frappe  # noqa: E402

from erp_workspace_ui.finance_accounting import service


_SOURCE_ROOT = Path(__file__).resolve().parents[1]
_SERVICE_SOURCE = _SOURCE_ROOT / "finance_accounting/service.py"

_COMPANY = {
    "name": "Mingalar Mobile Distribution Co., Ltd.",
    "company_name": "Mingalar Mobile Distribution Co., Ltd.",
    "default_currency": "MMK",
}
_OTHER_COMPANY = {
    "name": "Second Company",
    "company_name": "Second Company",
    "default_currency": "MMK",
}


def _context(roles, user="finance.lead@meet.com"):
    return {
        "user": user,
        "roles": roles,
    }


def _resolve(
    roles,
    companies=None,
    permissions=None,
    requested_company=None,
    user="finance.lead@meet.com",
    site_company_count=None,
):
    company_records = [] if companies is None else companies
    return service.resolve_finance_role_company_scope(
        context=_context(roles, user=user),
        requested_company=requested_company,
        enabled_companies=company_records,
        company_user_permissions=[] if permissions is None else permissions,
        site_enabled_company_count=len(company_records) if site_company_count is None else site_company_count,
    )


class TestFinanceRoleCompanyResolver(unittest.TestCase):
    def setUp(self):
        self.previous_user = getattr(frappe.session, "user", None)
        frappe.session.user = "finance.lead@meet.com"

    def tearDown(self):
        frappe.session.user = self.previous_user

    def assert_no_business_payload(self, payload):
        for key in ("rows", "metrics", "amounts", "documents"):
            self.assertEqual(payload[key], [], key)
        self.assertEqual(payload["source_read_policy_ready"], False)
        self.assertEqual(payload["ar_runtime_data_enabled"], False)
        self.assertEqual(payload["ap_runtime_data_enabled"], False)
        self.assertEqual(payload["cash_runtime_data_enabled"], False)
        self.assertEqual(payload["amount_visibility_enabled"], False)
        self.assertEqual(payload["execution_enabled"], False)

    def test_accounts_manager_single_company_fallback_is_allowed_without_data(self):
        payload = _resolve(["Accounts Manager"], companies=[_COMPANY])

        self.assertEqual(payload["state"], "scoped")
        self.assertEqual(payload["source"], "single_company_site_fallback")
        self.assertEqual(payload["role_category"], "manager")
        self.assertEqual(payload["selected_company"]["label"], _COMPANY["company_name"])
        self.assertEqual(payload["selected_company"]["currency"], "MMK")
        self.assertEqual(payload["amount_visibility_candidate"], True)
        self.assert_no_business_payload(payload)

    def test_accounts_user_single_company_fallback_is_limited_posture_only(self):
        payload = _resolve(["Accounts User"], companies=[_COMPANY], user="accounts.ygn.01@meet.com")

        self.assertEqual(payload["state"], "scoped")
        self.assertEqual(payload["source"], "single_company_site_fallback")
        self.assertEqual(payload["role_category"], "normal_finance")
        self.assertEqual(payload["limited_posture_candidate"], True)
        self.assertEqual(payload["amount_visibility_candidate"], False)
        self.assert_no_business_payload(payload)

    def test_accounts_manager_company_user_permission_is_used_when_present(self):
        payload = _resolve(
            ["Accounts Manager"],
            companies=[_COMPANY, _OTHER_COMPANY],
            permissions=[_COMPANY["name"]],
        )

        self.assertEqual(payload["state"], "scoped")
        self.assertEqual(payload["source"], "company_user_permission")
        self.assertEqual(payload["reason"], "single_company_permission")
        self.assertEqual(payload["selected_company"]["name"], _COMPANY["name"])
        self.assert_no_business_payload(payload)

    def test_requested_company_outside_permission_is_rejected(self):
        payload = _resolve(
            ["Accounts Manager"],
            companies=[_COMPANY, _OTHER_COMPANY],
            permissions=[_COMPANY["name"]],
            requested_company=_OTHER_COMPANY["name"],
        )

        self.assertEqual(payload["state"], "restricted")
        self.assertEqual(payload["source"], "restricted")
        self.assertEqual(payload["reason"], "requested_company_outside_scope")
        self.assertIsNone(payload["selected_company"])
        self.assert_no_business_payload(payload)

    def test_multiple_company_permissions_without_selected_company_requires_selection(self):
        payload = _resolve(
            ["Accounts Manager"],
            companies=[_COMPANY, _OTHER_COMPANY],
            permissions=[_COMPANY["name"], _OTHER_COMPANY["name"]],
        )

        self.assertEqual(payload["state"], "selection_required")
        self.assertEqual(payload["source"], "selection_required")
        self.assertEqual(payload["available_company_count"], 2)
        self.assertIsNone(payload["selected_company"])
        self.assert_no_business_payload(payload)

    def test_multi_company_site_without_company_permission_is_unavailable(self):
        payload = _resolve(["Accounts Manager"], companies=[_COMPANY, _OTHER_COMPANY])

        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["source"], "unavailable")
        self.assertEqual(payload["reason"], "company_user_permission_required_for_multi_company")
        self.assertEqual(payload["available_company_count"], 0)
        self.assertIsNone(payload["selected_company"])
        self.assert_no_business_payload(payload)

    def test_visible_single_company_does_not_trigger_fallback_when_site_has_multiple_companies(self):
        payload = _resolve(["Accounts Manager"], companies=[_COMPANY], site_company_count=2)

        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["source"], "unavailable")
        self.assertEqual(payload["reason"], "company_user_permission_required_for_multi_company")
        self.assertIsNone(payload["selected_company"])
        self.assert_no_business_payload(payload)

    def test_no_company_is_unavailable(self):
        payload = _resolve(["Accounts Manager"], companies=[])

        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["source"], "unavailable")
        self.assertEqual(payload["reason"], "no_enabled_company")
        self.assert_no_business_payload(payload)

    def test_system_manager_only_has_no_finance_company_scope(self):
        payload = _resolve(["System Manager"], companies=[_COMPANY])

        self.assertEqual(payload["state"], "restricted")
        self.assertEqual(payload["source"], "restricted")
        self.assertEqual(payload["role_category"], "system_admin_only")
        self.assertIsNone(payload["selected_company"])
        self.assert_no_business_payload(payload)

    def test_executive_approver_only_has_no_finance_company_scope(self):
        payload = _resolve(["Executive Approver"], companies=[_COMPANY], user="general.manager@meet.com")

        self.assertEqual(payload["state"], "restricted")
        self.assertEqual(payload["role_category"], "executive_only")
        self.assertIsNone(payload["selected_company"])
        self.assert_no_business_payload(payload)

    def test_finance_lead_approver_only_has_no_amount_visibility(self):
        payload = _resolve(["Finance Lead Approver"], companies=[_COMPANY])

        self.assertEqual(payload["state"], "restricted")
        self.assertEqual(payload["role_category"], "review_only")
        self.assertEqual(payload["amount_visibility_candidate"], False)
        self.assert_no_business_payload(payload)

    def test_system_manager_with_accounts_manager_uses_finance_role(self):
        payload = _resolve(["System Manager", "Accounts Manager"], companies=[_COMPANY])

        self.assertEqual(payload["state"], "scoped")
        self.assertEqual(payload["role_category"], "manager")
        self.assertEqual(payload["source"], "single_company_site_fallback")
        self.assertEqual(payload["amount_visibility_candidate"], True)
        self.assert_no_business_payload(payload)

    def test_non_finance_roles_are_restricted(self):
        for roles in (["Stock Manager"], ["Sales Manager"], ["Purchase Manager"], ["Delivery Manager"]):
            with self.subTest(roles=roles):
                payload = _resolve(roles, companies=[_COMPANY], user="warehouse.manager@meet.com")
                self.assertEqual(payload["state"], "restricted")
                self.assertEqual(payload["source"], "restricted")
                self.assertEqual(payload["role_category"], "restricted")
                self.assertIsNone(payload["selected_company"])
                self.assert_no_business_payload(payload)

    def test_role_classification_matrix_matches_f4a3_policy(self):
        cases = [
            (["Accounts Manager"], "manager", True, True),
            (["Accounts User"], "normal_finance", True, False),
            (["Auditor"], "audit_candidate", False, False),
            (["System Manager"], "system_admin_only", False, False),
            (["Executive Approver"], "executive_only", False, False),
            (["Finance Lead Approver"], "review_only", False, False),
            (["Sales Manager", "Stock Manager"], "restricted", False, False),
            (["System Manager", "Accounts Manager"], "manager", True, True),
            (["Executive Approver", "Accounts Manager"], "manager", True, True),
        ]
        for roles, category, limited_candidate, amount_candidate in cases:
            with self.subTest(roles=roles):
                payload = service.classify_finance_role_scope(roles)
                self.assertEqual(payload["role_category"], category)
                self.assertEqual(payload["limited_posture_candidate"], limited_candidate)
                self.assertEqual(payload["amount_visibility_candidate"], amount_candidate)

    def test_auditor_has_no_company_scope_without_explicit_audit_approval(self):
        denied = service.resolve_finance_role_company_scope(
            context=_context(["Auditor"], user="auditor@example.test"),
            enabled_companies=[_COMPANY],
            company_user_permissions=[],
            site_enabled_company_count=1,
            audit_scope_approved=False,
        )
        allowed = service.resolve_finance_role_company_scope(
            context=_context(["Auditor"], user="auditor@example.test"),
            enabled_companies=[_COMPANY],
            company_user_permissions=[],
            site_enabled_company_count=1,
            audit_scope_approved=True,
        )

        self.assertEqual(denied["state"], "restricted")
        self.assertEqual(denied["role_category"], "audit_candidate")
        self.assertEqual(allowed["state"], "scoped")
        self.assertEqual(allowed["source"], "single_company_site_fallback")
        self.assertEqual(allowed["amount_visibility_candidate"], False)
        self.assert_no_business_payload(denied)
        self.assert_no_business_payload(allowed)

    def test_source_read_policy_remains_disabled_for_role_eligible_users(self):
        payload = _resolve(["Accounts Manager"], companies=[_COMPANY])

        self.assertEqual(payload["state"], "scoped")
        self.assertEqual(payload["source_read_policy_ready"], False)
        self.assertEqual(payload["ar_runtime_data_enabled"], False)
        self.assertEqual(payload["amount_visibility_enabled"], False)
        self.assert_no_business_payload(payload)

    def test_runtime_company_lookup_does_not_request_disabled_field(self):
        calls = []

        def fake_get_list(doctype, **kwargs):
            calls.append((doctype, kwargs))
            return [_COMPANY]

        with patch.object(service.frappe, "get_list", side_effect=fake_get_list, create=True):
            records = service._load_enabled_company_records()

        self.assertEqual(records, [_COMPANY])
        self.assertEqual(calls[0][0], "Company")
        self.assertNotIn("filters", calls[0][1])
        self.assertEqual(calls[0][1]["order_by"], "name asc")
        self.assertEqual(calls[0][1]["limit_start"], 0)
        self.assertEqual(
            calls[0][1]["limit_page_length"],
            service.FINANCE_COMPANY_SCOPE_MAX_ROWS + 1,
        )
        self.assertNotIn("disabled", repr(calls[0][1]))

    def test_runtime_company_lookup_fails_closed_above_explicit_cap(self):
        def fake_get_list(doctype, **kwargs):
            self.assertEqual(doctype, "Company")
            self.assertEqual(kwargs["limit_start"], 0)
            self.assertEqual(kwargs["limit_page_length"], service.FINANCE_COMPANY_SCOPE_MAX_ROWS + 1)
            return [dict(_COMPANY, name=f"Company {index}") for index in range(service.FINANCE_COMPANY_SCOPE_MAX_ROWS + 1)]

        with patch.object(service.frappe, "get_list", side_effect=fake_get_list, create=True):
            records = service._load_enabled_company_records()

        self.assertIsNone(records)

    def test_company_field_permission_error_returns_controlled_unavailable_state(self):
        def denied_get_list(doctype, **kwargs):
            if doctype == "Company":
                raise _FrappePermissionError("You do not have permission to access field: Company.disabled")
            return []

        with patch.object(service.frappe, "get_roles", return_value=["Accounts Manager"]), patch.object(
            service.frappe,
            "get_list",
            side_effect=denied_get_list,
            create=True,
        ):
            payload = service.get_finance_role_company_resolver_context()

        self.assertEqual(payload["resolver"]["state"], "unavailable")
        self.assertEqual(payload["resolver"]["reason"], "company_lookup_unavailable")
        self.assertEqual(payload["rows"], [])
        self.assertEqual(payload["amounts"], [])
        self.assertTrue(all(value is False for value in payload["no_effect"].values()))

    def test_accounts_manager_single_visible_company_falls_back_when_user_permission_read_is_denied(self):
        calls = []

        def guarded_get_list(doctype, **kwargs):
            calls.append((doctype, kwargs))
            if doctype == "Company":
                return [_COMPANY]
            if doctype == "User Permission":
                raise _FrappePermissionError("Insufficient Permission for User Permission")
            return []

        with patch.object(service.frappe, "get_roles", return_value=["Accounts Manager"]), patch.object(
            service.frappe,
            "get_list",
            side_effect=guarded_get_list,
            create=True,
        ):
            payload = service.get_finance_role_company_resolver_context()

        self.assertEqual(payload["resolver"]["state"], "scoped")
        self.assertEqual(payload["resolver"]["source"], "single_company_site_fallback")
        self.assertEqual(payload["resolver"]["reason"], "single_permission_visible_company_without_user_permission_read")
        self.assertIn("User Permission", [doctype for doctype, _kwargs in calls])
        self.assertEqual(payload["rows"], [])
        self.assertEqual(payload["amounts"], [])
        self.assertTrue(all(value is False for value in payload["no_effect"].values()))

    def test_accounts_user_single_visible_company_falls_back_when_user_permission_read_is_denied(self):
        calls = []

        def guarded_get_list(doctype, **kwargs):
            calls.append((doctype, kwargs))
            if doctype == "Company":
                return [_COMPANY]
            if doctype == "User Permission":
                raise _FrappePermissionError("Insufficient Permission for User Permission")
            return []

        with patch.object(service.frappe, "get_roles", return_value=["Accounts User"]), patch.object(
            service.frappe,
            "get_list",
            side_effect=guarded_get_list,
            create=True,
        ):
            payload = service.get_finance_role_company_resolver_context()

        self.assertEqual(payload["resolver"]["state"], "scoped")
        self.assertEqual(payload["resolver"]["source"], "single_company_site_fallback")
        self.assertEqual(payload["resolver"]["amount_visibility_candidate"], False)
        self.assertIn("User Permission", [doctype for doctype, _kwargs in calls])
        self.assertEqual(payload["rows"], [])
        self.assertEqual(payload["amounts"], [])
        self.assertTrue(all(value is False for value in payload["no_effect"].values()))

    def test_non_finance_role_stops_before_user_permission_lookup(self):
        calls = []

        def guarded_get_list(doctype, **kwargs):
            calls.append((doctype, kwargs))
            raise AssertionError("non-finance users must not reach resolver data lookups")

        with patch.object(service.frappe, "get_roles", return_value=["Sales Manager"]), patch.object(
            service.frappe,
            "get_list",
            side_effect=guarded_get_list,
            create=True,
        ):
            payload = service.get_finance_role_company_resolver_context()

        self.assertEqual(payload["resolver"]["state"], "restricted")
        self.assertEqual(payload["resolver"]["source"], "restricted")
        self.assertEqual(calls, [])
        self.assertEqual(payload["rows"], [])
        self.assertEqual(payload["amounts"], [])
        self.assertTrue(all(value is False for value in payload["no_effect"].values()))

    def test_multi_company_user_permission_denial_is_controlled_unavailable(self):
        def guarded_get_list(doctype, **kwargs):
            if doctype == "Company":
                return [_COMPANY, _OTHER_COMPANY]
            if doctype == "User Permission":
                raise _FrappePermissionError("Insufficient Permission for User Permission")
            return []

        with patch.object(service.frappe, "get_roles", return_value=["Accounts Manager"]), patch.object(
            service.frappe,
            "get_list",
            side_effect=guarded_get_list,
            create=True,
        ):
            payload = service.get_finance_role_company_resolver_context()

        self.assertEqual(payload["resolver"]["state"], "unavailable")
        self.assertEqual(payload["resolver"]["reason"], "company_permission_lookup_unavailable")
        self.assertEqual(payload["rows"], [])
        self.assertEqual(payload["amounts"], [])
        self.assertTrue(all(value is False for value in payload["no_effect"].values()))

    def test_malformed_permission_visible_company_records_fail_closed_before_permission_lookup(self):
        malformed_records = (
            {"name": _COMPANY["name"], "company_name": _COMPANY["name"], "default_currency": ""},
            {"company": _COMPANY["name"], "label": _COMPANY["name"], "currency": "MMK"},
            {**_COMPANY, "unexpected": "value"},
        )
        for record in malformed_records:
            calls = []

            def guarded_get_list(doctype, **kwargs):
                calls.append(doctype)
                if doctype == "Company":
                    return [record]
                raise AssertionError("malformed company scope must stop before User Permission lookup")

            with self.subTest(record=record), patch.object(
                service.frappe, "get_roles", return_value=["Accounts Manager"]
            ), patch.object(service.frappe, "get_list", side_effect=guarded_get_list, create=True):
                payload = service.get_finance_role_company_resolver_context()

            self.assertEqual(payload["resolver"]["state"], "unavailable")
            self.assertEqual(payload["resolver"]["reason"], "company_lookup_malformed")
            self.assertEqual(calls, ["Company"])

    def test_user_permission_lookup_is_bounded_and_deterministic(self):
        calls = []

        def fake_get_list(doctype, **kwargs):
            calls.append((doctype, kwargs))
            return [{"for_value": _COMPANY["name"]}]

        with patch.object(service.frappe, "get_list", side_effect=fake_get_list, create=True):
            values = service._load_company_user_permission_values("finance.lead@meet.com")

        self.assertEqual(values, [_COMPANY["name"]])
        self.assertEqual(calls[0][0], "User Permission")
        self.assertEqual(calls[0][1]["order_by"], "for_value asc")
        self.assertEqual(calls[0][1]["limit_start"], 0)
        self.assertEqual(
            calls[0][1]["limit_page_length"],
            service.FINANCE_COMPANY_PERMISSION_MAX_ROWS + 1,
        )

    def test_user_permission_over_cap_and_malformed_records_fail_closed(self):
        over_cap = [
            {"for_value": f"Company {index}"}
            for index in range(service.FINANCE_COMPANY_PERMISSION_MAX_ROWS + 1)
        ]
        cases = (
            over_cap,
            [{"for_value": _COMPANY["name"], "unexpected": "value"}],
            [{"for_value": ""}],
            [{"for_value": _COMPANY["name"]}, {"for_value": _COMPANY["name"]}],
        )
        for records in cases:
            with self.subTest(records=records[:2]), patch.object(
                service.frappe, "get_list", return_value=records, create=True
            ):
                self.assertIsNone(service._load_company_user_permission_values("finance.lead@meet.com"))

    def test_resolver_context_returns_only_metadata_and_no_effect_flags(self):
        with patch.object(service.frappe, "get_roles", return_value=["Accounts Manager"]), patch.object(
            service,
            "_load_enabled_company_records",
            return_value=[_COMPANY],
        ), patch.object(service, "_load_company_user_permission_values", return_value=[]):
            payload = service.get_finance_role_company_resolver_context()

        self.assertEqual(payload["phase"], service.FINANCE_RESOLVER_PHASE)
        self.assertEqual(payload["resolver"]["state"], "scoped")
        self.assertEqual(payload["scope"]["financial_data_enabled"], False)
        self.assertEqual(payload["scope"]["financial_rows_enabled"], False)
        self.assertEqual(payload["scope"]["monetary_values_enabled"], False)
        self.assertEqual(payload["scope"]["source_read_policy_ready"], False)
        for key in ("rows", "metrics", "amounts", "documents"):
            self.assertEqual(payload[key], [])
        self.assertTrue(all(value is False for value in payload["no_effect"].values()))

    def test_backend_source_has_no_business_doctype_reads_or_mutations(self):
        source = _SERVICE_SOURCE.read_text(encoding="utf-8")
        forbidden_patterns = [
            r"frappe\.get_all",
            r"frappe\.db\.sql",
            r"frappe\.db\.count",
            r"ignore_permissions",
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
        self.assertIn('getattr(frappe, "get_list", None)', source)
        self.assertNotIn('filters={"disabled": 0}', source)
        self.assertNotIn('counter("Company", {"disabled": 0})', source)
        self.assertNotIn('record.get("disabled")', source)
        self.assertNotIn("_count_enabled_companies", source)
        self.assertNotIn('count(name) as count', source)


if __name__ == "__main__":
    unittest.main()
