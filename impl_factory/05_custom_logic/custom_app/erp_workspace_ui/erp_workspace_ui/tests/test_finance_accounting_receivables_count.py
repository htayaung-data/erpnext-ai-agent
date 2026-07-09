from __future__ import annotations

import re
import sys
import types
import unittest
from datetime import date, datetime
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

_ALLOWED_TOP_LEVEL_KEYS = {
    "phase",
    "state",
    "company_scope",
    "as_of_date",
    "bucket_labels",
    "bucket_counts",
    "policy",
    "no_effect",
    "rows_returned",
    "amounts_returned",
    "documents_returned",
    "runtime_count_enabled",
}

_RECORDS = [
    {"company": _COMPANY_SCOPE["name"], "docstatus": 1, "outstanding_amount": 100, "is_return": 0, "return_against": "", "due_date": date(2026, 7, 6)},
    {"company": _COMPANY_SCOPE["name"], "docstatus": 1, "outstanding_amount": 100, "is_return": 0, "return_against": None, "due_date": date(2026, 7, 7)},
    {"company": _COMPANY_SCOPE["name"], "docstatus": 1, "outstanding_amount": 100, "is_return": 0, "return_against": "", "due_date": date(2026, 7, 5)},
    {"company": _COMPANY_SCOPE["name"], "docstatus": 1, "outstanding_amount": 100, "is_return": 0, "return_against": "", "due_date": date(2026, 6, 6)},
    {"company": _COMPANY_SCOPE["name"], "docstatus": 1, "outstanding_amount": 100, "is_return": 0, "return_against": "", "due_date": date(2026, 6, 5)},
    {"company": _COMPANY_SCOPE["name"], "docstatus": 1, "outstanding_amount": 100, "is_return": 0, "return_against": "", "due_date": date(2026, 5, 7)},
    {"company": _COMPANY_SCOPE["name"], "docstatus": 1, "outstanding_amount": 100, "is_return": 0, "return_against": "", "due_date": date(2026, 5, 6)},
    {"company": _COMPANY_SCOPE["name"], "docstatus": 1, "outstanding_amount": 100, "is_return": 0, "return_against": "", "due_date": date(2026, 4, 7)},
    {"company": _COMPANY_SCOPE["name"], "docstatus": 1, "outstanding_amount": 100, "is_return": 0, "return_against": "", "due_date": date(2026, 4, 6)},
    {"company": _COMPANY_SCOPE["name"], "docstatus": 0, "outstanding_amount": 100, "is_return": 0, "return_against": "", "due_date": date(2026, 7, 6)},
    {"company": _COMPANY_SCOPE["name"], "docstatus": 2, "outstanding_amount": 100, "is_return": 0, "return_against": "", "due_date": date(2026, 7, 5)},
    {"company": _COMPANY_SCOPE["name"], "docstatus": 1, "outstanding_amount": 0, "is_return": 0, "return_against": "", "due_date": date(2026, 7, 5)},
    {"company": _COMPANY_SCOPE["name"], "docstatus": 1, "outstanding_amount": 100, "is_return": 1, "return_against": "SINV-0001", "due_date": date(2026, 7, 5)},
    {"company": _COMPANY_SCOPE["name"], "docstatus": 1, "outstanding_amount": 100, "is_return": 0, "return_against": "SINV-0001", "due_date": date(2026, 7, 5)},
    {"company": "Other Company", "docstatus": 1, "outstanding_amount": 100, "is_return": 0, "return_against": "", "due_date": date(2026, 7, 5)},
]


def _resolver(state="scoped", role_category="manager", selected_company=None, reason="single_enabled_company_without_company_permission"):
    return {
        "state": state,
        "source": "single_company_site_fallback" if state == "scoped" else state,
        "reason": reason,
        "role_category": role_category,
        "selected_company": _COMPANY_SCOPE if selected_company is None and state == "scoped" else selected_company,
        "rows": [],
        "metrics": [],
        "amounts": [],
        "documents": [],
    }


def _context(roles=None):
    return {
        "user": "finance.lead@meet.com",
        "roles": ["Accounts Manager"] if roles is None else roles,
    }


def _permission_checker(allowed=True, calls=None):
    def checker(doctype, **kwargs):
        if calls is not None:
            calls.append((doctype, kwargs))
        return allowed

    return checker


def _matches_filter(record, item):
    field, operator, value = item
    current = record.get(field)
    if operator == "=":
        return current == value
    if operator == ">":
        return current > value
    if operator == ">=":
        return current >= date.fromisoformat(value)
    if operator == "<=":
        return current <= date.fromisoformat(value)
    if operator == "between":
        start, end = [date.fromisoformat(part) for part in value]
        return start <= current <= end
    if operator == "is" and value == "not set":
        return current in (None, "")
    if operator == "is" and value == "set":
        return current not in (None, "")
    raise AssertionError(f"Unexpected filter: {item!r}")


def _counting_getter(calls, records=None):
    source_records = list(_RECORDS if records is None else records)

    def getter(doctype, **kwargs):
        calls.append((doctype, kwargs))
        filters = kwargs.get("filters") or []
        count = sum(1 for record in source_records if all(_matches_filter(record, item) for item in filters))
        return [{"count": count}]

    return getter


def _raising_getter(*args, **kwargs):
    raise AssertionError("Sales Invoice count query should not run")


def _static_count_response_getter(response, calls=None):
    def getter(doctype, **kwargs):
        if calls is not None:
            calls.append((doctype, kwargs))
        return response

    return getter


class TestFinanceReceivablesCountPosture(unittest.TestCase):
    def assert_safe_count_response(self, payload):
        self.assertEqual(set(payload), _ALLOWED_TOP_LEVEL_KEYS)
        for blocked in ("rows", "amounts", "documents", "metrics", "customer", "invoice", "route", "report", "export", "print", "download", "action"):
            self.assertNotIn(blocked, payload)
        self.assertEqual(payload["rows_returned"], False)
        self.assertEqual(payload["amounts_returned"], False)
        self.assertEqual(payload["documents_returned"], False)
        self.assertTrue(all(value is False for value in payload["no_effect"].values()))
        policy = payload["policy"]
        for blocked in ("customer", "invoice", "route", "report", "export", "print", "download", "action"):
            self.assertTrue(all(blocked not in key for key in policy), blocked)
        self.assertEqual(policy["identifiers_enabled"], False)
        self.assertEqual(policy["monetary_values_enabled"], False)
        self.assertEqual(policy["native_navigation_enabled"], False)
        self.assertEqual(policy["external_output_enabled"], False)
        self.assertEqual(policy["execution_enabled"], False)

    def test_accounts_manager_scoped_with_permission_gets_aggregate_bucket_counts_only(self):
        calls = []
        permission_calls = []
        payload = service.build_receivables_count_posture(
            context=_context(),
            resolver=_resolver(),
            as_of_date="2026-07-06",
            permission_checker=_permission_checker(True, permission_calls),
            list_getter=_counting_getter(calls),
        )

        self.assert_safe_count_response(payload)
        self.assertEqual(payload["phase"], service.FINANCE_RECEIVABLES_COUNT_PHASE)
        self.assertEqual(payload["state"], "ready")
        self.assertEqual(payload["company_scope"], _COMPANY_SCOPE)
        self.assertEqual(payload["as_of_date"], "2026-07-06")
        self.assertEqual(
            payload["bucket_counts"],
            {
                "current": 2,
                "overdue_1_30": 2,
                "overdue_31_60": 2,
                "overdue_61_90": 2,
                "overdue_over_90": 1,
            },
        )
        self.assertEqual([item["key"] for item in payload["bucket_labels"]], [
            "current",
            "overdue_1_30",
            "overdue_31_60",
            "overdue_61_90",
            "overdue_over_90",
        ])
        self.assertEqual(payload["runtime_count_enabled"], True)
        self.assertEqual(payload["policy"]["role_category"], "manager")
        self.assertEqual(payload["policy"]["source"], service.RECEIVABLES_COUNT_SOURCE)
        self.assertEqual(payload["policy"]["source_permission_checked"], True)
        self.assertEqual(payload["policy"]["source_permission_verified"], True)
        self.assertEqual(payload["policy"]["source_read_policy_ready"], True)
        self.assertEqual(payload["policy"]["runtime_count_enabled"], True)
        self.assertEqual(payload["policy"]["reason"], "receivables_count_posture_ready")
        self.assertEqual(len(calls), 6)
        self.assertEqual(permission_calls, [("Sales Invoice", {"ptype": "read", "user": "finance.lead@meet.com"})])

    def test_query_contract_uses_selected_company_and_required_filters(self):
        calls = []
        service.build_receivables_count_posture(
            context=_context(),
            resolver=_resolver(),
            as_of_date="2026-07-06",
            permission_checker=_permission_checker(True),
            list_getter=_counting_getter(calls),
        )

        self.assertEqual(len(calls), 6)
        due_filters = []
        self.assertEqual(service.RECEIVABLES_COUNT_QUERY_FIELD, {"COUNT": "name", "as": "count"})
        for doctype, kwargs in calls:
            self.assertEqual(doctype, "Sales Invoice")
            self.assertEqual(kwargs["fields"], [service.RECEIVABLES_COUNT_QUERY_FIELD])
            self.assertNotIn("count(name) as count", repr(kwargs["fields"]))
            self.assertEqual(kwargs["limit_page_length"], 1)
            self.assertNotIn("ignore_permissions", kwargs)
            self.assertNotIn("order_by", kwargs)
            filters = kwargs["filters"]
            self.assertIn(["company", "=", _COMPANY_SCOPE["name"]], filters)
            self.assertIn(["docstatus", "=", 1], filters)
            self.assertIn(["outstanding_amount", ">", 0], filters)
            self.assertIn(["is_return", "=", 0], filters)
            self.assertIn(["return_against", "is", "not set"], filters)
            due_filters.append(filters[-1])
        self.assertEqual(due_filters, [
            ["due_date", "is", "not set"],
            ["due_date", ">=", "2026-07-06"],
            ["due_date", "between", ["2026-06-06", "2026-07-05"]],
            ["due_date", "between", ["2026-05-07", "2026-06-05"]],
            ["due_date", "between", ["2026-04-07", "2026-05-06"]],
            ["due_date", "<=", "2026-04-06"],
        ])

    def test_missing_sales_invoice_due_date_fails_closed_without_partial_counts(self):
        records = list(_RECORDS) + [
            {
                "company": _COMPANY_SCOPE["name"],
                "docstatus": 1,
                "outstanding_amount": 100,
                "is_return": 0,
                "return_against": "",
                "due_date": None,
            }
        ]
        calls = []
        payload = service.build_receivables_count_posture(
            context=_context(),
            resolver=_resolver(),
            as_of_date="2026-07-06",
            permission_checker=_permission_checker(True),
            list_getter=_counting_getter(calls, records=records),
        )

        self.assert_safe_count_response(payload)
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["policy"]["reason"], "missing_due_date_policy_not_ready")
        self.assertEqual(payload["bucket_counts"], {})
        self.assertEqual(payload["runtime_count_enabled"], False)
        self.assertIsNone(payload["company_scope"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1]["filters"][-1], ["due_date", "is", "not set"])

    def test_malformed_aggregate_count_responses_fail_closed_without_zero_counts(self):
        cases = (
            (None, "missing_response"),
            ([], "empty_response"),
            ([{"COUNT(name)": 0}], "unexpected_count_alias"),
            ([{"count(name)": 0}], "legacy_count_alias"),
            ([{"total": 0}], "missing_count_key"),
            ([{"count": None}], "none_count"),
            ([{"count": "not-a-number"}], "non_numeric_count"),
            ([{"count": -1}], "negative_count"),
            ([{"count": 1}, {"count": 2}], "multiple_aggregate_rows"),
            ([{"count": 0, "extra": 0}], "ambiguous_extra_key"),
        )
        for response, label in cases:
            with self.subTest(label=label):
                calls = []
                payload = service.build_receivables_count_posture(
                    context=_context(),
                    resolver=_resolver(),
                    as_of_date="2026-07-06",
                    permission_checker=_permission_checker(True),
                    list_getter=_static_count_response_getter(response, calls=calls),
                )

                self.assert_safe_count_response(payload)
                self.assertEqual(payload["state"], "unavailable")
                self.assertEqual(payload["policy"]["reason"], service.RECEIVABLES_COUNT_SOURCE_INVALID_REASON)
                self.assertEqual(payload["bucket_counts"], {})
                self.assertEqual(payload["runtime_count_enabled"], False)
                self.assertIsNone(payload["company_scope"])
                self.assertEqual(len(calls), 1)

    def test_permission_denied_returns_no_counts_and_does_not_query(self):
        payload = service.build_receivables_count_posture(
            context=_context(),
            resolver=_resolver(),
            as_of_date="2026-07-06",
            permission_checker=_permission_checker(False),
            list_getter=_raising_getter,
        )

        self.assert_safe_count_response(payload)
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["bucket_counts"], {})
        self.assertIsNone(payload["company_scope"])
        self.assertEqual(payload["runtime_count_enabled"], False)
        self.assertEqual(payload["policy"]["reason"], "source_permission_denied")
        self.assertEqual(payload["policy"]["source_permission_verified"], False)
        self.assertEqual(payload["policy"]["runtime_count_enabled"], False)

    def test_accounts_user_remains_not_ready_until_low_count_policy_exists(self):
        payload = service.build_receivables_count_posture(
            context=_context(["Accounts User"]),
            resolver=_resolver(role_category="normal_finance"),
            as_of_date="2026-07-06",
            permission_checker=_permission_checker(True),
            list_getter=_raising_getter,
        )

        self.assert_safe_count_response(payload)
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["bucket_counts"], {})
        self.assertEqual(payload["policy"]["role_category"], "normal_finance")
        self.assertEqual(payload["policy"]["reason"], "low_count_policy_not_ready")
        self.assertEqual(payload["policy"]["source_permission_checked"], False)
        self.assertEqual(payload["policy"]["runtime_count_enabled"], False)
        self.assertEqual(payload["policy"]["accounts_user_raw_counts_enabled"], False)

    def test_unscoped_and_restricted_resolver_states_do_not_query(self):
        cases = [
            _resolver(state="restricted", role_category="restricted", selected_company=None, reason="finance_role_required"),
            _resolver(state="restricted", role_category="manager", selected_company=None, reason="requested_company_outside_scope"),
            _resolver(state="unavailable", role_category="manager", selected_company=None, reason="company_user_permission_required_for_multi_company"),
            _resolver(state="unavailable", role_category="manager", selected_company=None, reason="no_enabled_company"),
            _resolver(state="selection_required", role_category="manager", selected_company=None, reason="multiple_company_permissions_require_selection"),
        ]
        for resolver in cases:
            with self.subTest(reason=resolver["reason"]):
                payload = service.build_receivables_count_posture(
                    context=_context(),
                    resolver=resolver,
                    as_of_date="2026-07-06",
                    permission_checker=_permission_checker(True),
                    list_getter=_raising_getter,
                )
                self.assert_safe_count_response(payload)
                self.assertEqual(payload["state"], "unavailable")
                self.assertEqual(payload["bucket_counts"], {})
                self.assertEqual(payload["runtime_count_enabled"], False)
                self.assertEqual(payload["policy"]["runtime_count_enabled"], False)
                self.assertIn(payload["policy"]["reason"], {
                    "finance_role_required",
                    "requested_company_outside_scope",
                    "company_user_permission_required_for_multi_company",
                    "no_enabled_company",
                    "multiple_company_permissions_require_selection",
                })

    def test_permission_helper_checks_doctype_read_without_row_probe(self):
        calls = []
        payload = service.verify_receivables_source_permission(
            _context(),
            permission_checker=_permission_checker(True, calls),
        )

        self.assertEqual(payload["source_permission_checked"], True)
        self.assertEqual(payload["source_permission_verified"], True)
        self.assertEqual(calls, [("Sales Invoice", {"ptype": "read", "user": "finance.lead@meet.com"})])

    def test_service_source_for_f4d_has_only_narrow_permission_preserving_count_read(self):
        source = _SERVICE_SOURCE.read_text(encoding="utf-8")
        forbidden_patterns = [
            r"frappe\.get_all",
            r"frappe\.get_list\s*\(",
            r"frappe\.db\.sql",
            r"ignore_permissions",
            r"frappe\.get_doc",
            r"frappe\.db\.count",
            r"frappe\.db\.get_list",
            r"frappe\.db\.get_value",
            r"frappe\.client",
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
        self.assertIn('getattr(frappe, "get_list", None)', source)
        self.assertIn('getattr(frappe, "has_permission", None)', source)
        allowed_config_reads = set(re.findall(r'_safe_config_list\(\s*"([^"]+)"', source))
        self.assertEqual(allowed_config_reads, {"Company", "User Permission"})


if __name__ == "__main__":
    unittest.main()
