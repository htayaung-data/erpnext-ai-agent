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
    utils_stub.now_datetime = lambda: datetime(2026, 7, 4, 0, 0, 0)

    sys.modules["frappe"] = frappe_stub
    sys.modules["frappe.utils"] = utils_stub


_install_frappe_stub()

from erp_workspace_ui.finance_accounting import service


_SOURCE_ROOT = Path(__file__).resolve().parents[1]
_SERVICE_SOURCE = _SOURCE_ROOT / "finance_accounting/service.py"
_FRONTEND_SOURCE = _SOURCE_ROOT / "erp_workspace_ui/page/finance_control_desk/finance_control_desk.js"
_COMPANY_SCOPE = {
    "name": "Mingalar Mobile Distribution Co., Ltd.",
    "label": "Mingalar Mobile Distribution Co., Ltd.",
    "currency": "MMK",
}
_ALLOWED_TOP_LEVEL_KEYS = {
    "phase",
    "state",
    "source_state",
    "company_scope",
    "as_of_date",
    "bucket_labels",
    "bucket_counts",
    "policy",
    "no_effect",
}
_ALLOWED_POLICY_KEYS = {
    "source",
    "reason",
    "resolver_state",
    "resolver_source",
    "role_category",
    "source_permission_checked",
    "source_permission_verified",
    "source_read_policy_ready",
    "runtime_count_enabled",
    "manager_only",
    "accounts_user_counts_enabled",
    "aggregate_counts_only",
    "due_date_basis_only",
    "posting_date_fallback_enabled",
    "due_soon_enabled",
    "payment_terms_supported",
    "payment_schedule_supported",
    "payment_schedule_presence_gate_required",
    "payment_schedule_rows_returned",
    "on_hold_supported",
    "returns_supported",
    "identifiers_enabled",
    "monetary_values_enabled",
    "native_navigation_enabled",
    "external_output_enabled",
    "execution_enabled",
}
_RECORDS = [
    {"company": _COMPANY_SCOPE["name"], "docstatus": 1, "outstanding_amount": 100, "status": "Unpaid", "is_return": 0, "return_against": "", "due_date": date(2026, 7, 9), "payment_terms_template": "", "on_hold": 0},
    {"company": _COMPANY_SCOPE["name"], "docstatus": 1, "outstanding_amount": 100, "status": "Partly Paid", "is_return": 0, "return_against": None, "due_date": date(2026, 7, 10), "payment_terms_template": "", "on_hold": 0},
    {"company": _COMPANY_SCOPE["name"], "docstatus": 1, "outstanding_amount": 100, "status": "Overdue", "is_return": 0, "return_against": "", "due_date": date(2026, 7, 8), "payment_terms_template": "", "on_hold": 0},
    {"company": _COMPANY_SCOPE["name"], "docstatus": 1, "outstanding_amount": 100, "status": "Overdue", "is_return": 0, "return_against": "", "due_date": date(2026, 6, 9), "payment_terms_template": "", "on_hold": 0},
    {"company": _COMPANY_SCOPE["name"], "docstatus": 1, "outstanding_amount": 100, "status": "Overdue", "is_return": 0, "return_against": "", "due_date": date(2026, 6, 8), "payment_terms_template": "", "on_hold": 0},
    {"company": _COMPANY_SCOPE["name"], "docstatus": 1, "outstanding_amount": 100, "status": "Overdue", "is_return": 0, "return_against": "", "due_date": date(2026, 5, 10), "payment_terms_template": "", "on_hold": 0},
    {"company": _COMPANY_SCOPE["name"], "docstatus": 1, "outstanding_amount": 100, "status": "Overdue", "is_return": 0, "return_against": "", "due_date": date(2026, 5, 9), "payment_terms_template": "", "on_hold": 0},
    {"company": _COMPANY_SCOPE["name"], "docstatus": 1, "outstanding_amount": 100, "status": "Overdue", "is_return": 0, "return_against": "", "due_date": date(2026, 4, 10), "payment_terms_template": "", "on_hold": 0},
    {"company": _COMPANY_SCOPE["name"], "docstatus": 1, "outstanding_amount": 100, "status": "Overdue", "is_return": 0, "return_against": "", "due_date": date(2026, 4, 9), "payment_terms_template": "", "on_hold": 0},
    {"company": _COMPANY_SCOPE["name"], "docstatus": 1, "outstanding_amount": 0, "status": "Paid", "is_return": 0, "return_against": "", "due_date": date(2026, 7, 8), "payment_terms_template": "", "on_hold": 0},
    {"company": _COMPANY_SCOPE["name"], "docstatus": 0, "outstanding_amount": 100, "status": "Draft", "is_return": 0, "return_against": "", "due_date": date(2026, 7, 8), "payment_terms_template": "", "on_hold": 0},
    {"company": _COMPANY_SCOPE["name"], "docstatus": 2, "outstanding_amount": 100, "status": "Cancelled", "is_return": 0, "return_against": "", "due_date": date(2026, 7, 8), "payment_terms_template": "", "on_hold": 0},
    {"company": "Other Company", "docstatus": 1, "outstanding_amount": 100, "status": "Overdue", "is_return": 0, "return_against": "", "due_date": date(2026, 7, 8), "payment_terms_template": "", "on_hold": 0},
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
    return {"user": "finance.lead@meet.com", "roles": ["Accounts Manager"] if roles is None else roles}


def _permission_checker(allowed=True, calls=None):
    def checker(doctype, **kwargs):
        if calls is not None:
            calls.append((doctype, kwargs))
        return allowed

    return checker


def _normalize_date(value):
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    return value


def _matches_filter(record, item):
    if len(item) == 4:
        doctype, field, operator, value = item
        if doctype != "Payment Schedule":
            raise AssertionError(f"Unexpected child filter: {item!r}")
        schedule_count = record.get("_payment_schedule_count", 0)
        if not schedule_count:
            current = None
        elif field == "parent":
            current = "synthetic-parent"
        elif field == "parenttype":
            current = record.get("_payment_schedule_parenttype", "Purchase Invoice")
        elif field == "parentfield":
            current = record.get("_payment_schedule_parentfield", "payment_schedule")
        else:
            raise AssertionError(f"Unexpected child filter: {item!r}")
    else:
        field, operator, value = item
        current = record.get(field)
    if operator == "=":
        return current == value
    if operator == ">":
        if current in (None, ""):
            return False
        if field in {"posting_date", "due_date"}:
            return _normalize_date(current) > _normalize_date(value)
        return current > value
    if operator == "in":
        return current in value
    if operator == ">=":
        return _normalize_date(current) >= _normalize_date(value)
    if operator == "<=":
        return _normalize_date(current) <= _normalize_date(value)
    if operator == "between":
        start, end = [_normalize_date(part) for part in value]
        return start <= _normalize_date(current) <= end
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
        child_join = any(len(item) == 4 and item[0] == "Payment Schedule" for item in filters)
        count = sum(
            int(record.get("_payment_schedule_count", 1)) if child_join else 1
            for record in source_records
            if all(_matches_filter(record, item) for item in filters)
        )
        return [{"count": count}]

    return getter


def _raising_getter(*args, **kwargs):
    raise AssertionError("Purchase Invoice count query should not run")


def _static_count_response_getter(response, calls=None):
    def getter(doctype, **kwargs):
        if calls is not None:
            calls.append((doctype, kwargs))
        return response

    return getter


class TestFinancePayablesCountPosture(unittest.TestCase):
    def assert_safe_payables_response(self, payload):
        self.assertEqual(set(payload), _ALLOWED_TOP_LEVEL_KEYS)
        self.assertEqual(set(payload["policy"]), _ALLOWED_POLICY_KEYS)
        for blocked_key in ("rows", "documents", "records", "invoices", "suppliers", "routes", "actions", "amounts", "currency"):
            self.assertNotIn(blocked_key, payload)
        for collection in (payload["bucket_counts"], payload["company_scope"] or {}):
            text = repr(collection).lower()
            for blocked in (
                "supplier", "purchase_invoice", "bill_no", "bill_date", "voucher", "payment_ledger",
                "gl_entry", "route", "report", "export", "download", "print", "action", "amount", "currency",
            ):
                self.assertNotIn(blocked, text)
        self.assertTrue(all(value is False for value in payload["no_effect"].values()))
        self.assertEqual(payload["policy"]["identifiers_enabled"], False)
        self.assertEqual(payload["policy"]["monetary_values_enabled"], False)
        self.assertEqual(payload["policy"]["native_navigation_enabled"], False)
        self.assertEqual(payload["policy"]["external_output_enabled"], False)
        self.assertEqual(payload["policy"]["execution_enabled"], False)

    def test_accounts_manager_scoped_with_permission_gets_aggregate_bucket_counts_only(self):
        calls = []
        permission_calls = []
        payload = service.build_payables_count_posture(
            context=_context(),
            resolver=_resolver(),
            as_of_date="2026-07-09",
            permission_checker=_permission_checker(True, permission_calls),
            list_getter=_counting_getter(calls),
        )

        self.assert_safe_payables_response(payload)
        self.assertEqual(payload["phase"], service.FINANCE_PAYABLES_COUNT_PHASE)
        self.assertEqual(payload["state"], "ready")
        self.assertEqual(payload["source_state"], "ready")
        self.assertEqual(payload["company_scope"], {"name": _COMPANY_SCOPE["name"], "label": _COMPANY_SCOPE["label"]})
        self.assertEqual(payload["as_of_date"], "2026-07-09")
        self.assertEqual(payload["bucket_counts"], {
            "not_due": 2,
            "overdue_1_30": 2,
            "overdue_31_60": 2,
            "overdue_61_90": 2,
            "overdue_over_90": 1,
        })
        self.assertEqual([item["key"] for item in payload["bucket_labels"]], [
            "not_due",
            "overdue_1_30",
            "overdue_31_60",
            "overdue_61_90",
            "overdue_over_90",
        ])
        self.assertEqual(payload["policy"]["manager_only"], True)
        self.assertEqual(payload["policy"]["accounts_user_counts_enabled"], False)
        self.assertEqual(payload["policy"]["runtime_count_enabled"], True)
        self.assertEqual(payload["policy"]["reason"], "payables_count_posture_ready")
        self.assertEqual(permission_calls, [("Purchase Invoice", {"ptype": "read", "user": "finance.lead@meet.com"})])
        self.assertEqual(len(calls), 15)

    def test_query_contract_uses_selected_company_and_required_filters(self):
        calls = []
        service.build_payables_count_posture(
            context=_context(),
            resolver=_resolver(),
            as_of_date="2026-07-09",
            permission_checker=_permission_checker(True),
            list_getter=_counting_getter(calls),
        )

        self.assertEqual(service.PAYABLES_COUNT_QUERY_FIELD, {"COUNT": "name", "as": "count"})
        for doctype, kwargs in calls:
            self.assertEqual(doctype, "Purchase Invoice")
            self.assertEqual(kwargs["fields"], [service.PAYABLES_COUNT_QUERY_FIELD])
            self.assertEqual(kwargs["limit_page_length"], 1)
            self.assertNotIn("ignore_permissions", kwargs)
            self.assertNotIn("order_by", kwargs)
            filters = kwargs["filters"]
            self.assertIn(["company", "=", _COMPANY_SCOPE["name"]], filters)
            self.assertIn(["docstatus", "=", 1], filters)
        self.assertNotIn(["status", "in", list(service.PAYABLES_OPEN_STATUSES)], calls[0][1]["filters"])
        self.assertIn(["status", "in", list(service.PAYABLES_OPEN_STATUSES)], calls[1][1]["filters"])
        self.assertIn([service.PAYABLES_SCHEDULE_CHILD_SOURCE, "parent", "is", "set"], calls[2][1]["filters"])
        self.assertIn([service.PAYABLES_SCHEDULE_CHILD_SOURCE, "parenttype", "=", "Purchase Invoice"], calls[2][1]["filters"])
        self.assertIn([service.PAYABLES_SCHEDULE_CHILD_SOURCE, "parentfield", "=", "payment_schedule"], calls[2][1]["filters"])
        self.assertEqual(calls[2][1]["fields"], [{"COUNT": "name", "as": "count"}])
        bucket_filters = [kwargs["filters"][-1] for _doctype, kwargs in calls[-5:]]
        self.assertEqual(bucket_filters, [
            ["due_date", ">=", "2026-07-09"],
            ["due_date", "between", ["2026-06-09", "2026-07-08"]],
            ["due_date", "between", ["2026-05-10", "2026-06-08"]],
            ["due_date", "between", ["2026-04-10", "2026-05-09"]],
            ["due_date", "<=", "2026-04-09"],
        ])
        for _doctype, kwargs in calls[-5:]:
            filters = kwargs["filters"]
            self.assertIn(["outstanding_amount", ">", 0], filters)
            self.assertIn(["status", "in", list(service.PAYABLES_OPEN_STATUSES)], filters)
            self.assertIn(["is_return", "=", 0], filters)
            self.assertIn(["return_against", "is", "not set"], filters)

    def test_accounts_user_and_non_finance_do_not_call_permission_or_adapter(self):
        cases = [
            (_context(["Accounts User"]), _resolver(role_category="normal_finance"), "accounts_manager_required"),
            (_context(["Auditor"]), _resolver(role_category="auditor"), "accounts_manager_required"),
            (_context(["System Manager"]), _resolver(role_category="admin_only"), "accounts_manager_required"),
            (_context(["Executive Approver"]), _resolver(state="restricted", role_category="restricted", selected_company=None, reason="finance_role_required"), "finance_role_required"),
            (_context(["Finance Lead Approver"]), _resolver(role_category="review_only"), "accounts_manager_required"),
            (_context(["Sales User"]), _resolver(state="restricted", role_category="restricted", selected_company=None, reason="finance_role_required"), "finance_role_required"),
            (_context(["Purchase User"]), _resolver(state="restricted", role_category="restricted", selected_company=None, reason="finance_role_required"), "finance_role_required"),
            (_context(["Warehouse User"]), _resolver(state="restricted", role_category="restricted", selected_company=None, reason="finance_role_required"), "finance_role_required"),
            (_context([]), _resolver(state="restricted", role_category="restricted", selected_company=None, reason="finance_role_required"), "finance_role_required"),
        ]
        for context, resolver, reason in cases:
            with self.subTest(reason=reason):
                permission_calls = []
                payload = service.build_payables_count_posture(
                    context=context,
                    resolver=resolver,
                    as_of_date="2026-07-09",
                    permission_checker=_permission_checker(True, permission_calls),
                    list_getter=_raising_getter,
                )
                self.assert_safe_payables_response(payload)
                self.assertEqual(payload["state"], "unavailable")
                self.assertEqual(payload["bucket_counts"], {})
                self.assertIsNone(payload["company_scope"])
                self.assertEqual(payload["policy"]["reason"], reason)
                self.assertEqual(permission_calls, [])
                self.assertEqual(payload["policy"]["runtime_count_enabled"], False)

    def test_wrong_or_missing_company_fails_closed_before_adapter(self):
        cases = [
            _resolver(selected_company={"name": "Other Company", "label": "Other Company", "currency": "MMK"}),
            _resolver(selected_company={"name": _COMPANY_SCOPE["name"], "label": _COMPANY_SCOPE["label"], "currency": "USD"}),
            _resolver(state="unavailable", selected_company=None, reason="no_enabled_company"),
        ]
        for resolver in cases:
            with self.subTest(reason=resolver.get("reason")):
                payload = service.build_payables_count_posture(
                    context=_context(),
                    resolver=resolver,
                    as_of_date="2026-07-09",
                    permission_checker=_permission_checker(True),
                    list_getter=_raising_getter,
                )
                self.assert_safe_payables_response(payload)
                self.assertEqual(payload["state"], "unavailable")
                self.assertEqual(payload["bucket_counts"], {})

    def test_browser_filters_fail_closed_before_permission_or_adapter(self):
        permission_calls = []
        payload = service.build_payables_count_posture(
            context=_context(),
            resolver=_resolver(),
            as_of_date="2026-07-09",
            permission_checker=_permission_checker(True, permission_calls),
            list_getter=_raising_getter,
            browser_filters={"supplier": "blocked"},
        )

        self.assert_safe_payables_response(payload)
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["policy"]["reason"], "browser_filters_not_allowed")
        self.assertEqual(permission_calls, [])

    def test_any_selected_company_payment_schedule_presence_fails_closed_before_aging(self):
        scenarios = (
            ("one_default_row", 1, "Unpaid"),
            ("multiple_rows", 2, "Unpaid"),
            ("missing_child_due_date", 1, "Unpaid"),
            ("malformed_child", 1, "Unpaid"),
            ("schedule_total_mismatch", 2, "Unpaid"),
            ("partly_paid_with_schedule", 1, "Partly Paid"),
        )
        for label, schedule_count, status in scenarios:
            with self.subTest(label=label):
                records = list(_RECORDS) + [{
                    "company": _COMPANY_SCOPE["name"],
                    "docstatus": 1,
                    "outstanding_amount": 100,
                    "status": status,
                    "is_return": 0,
                    "return_against": "",
                    "due_date": date(2026, 7, 8),
                    "payment_terms_template": "",
                    "on_hold": 0,
                    "_payment_schedule_count": schedule_count,
                }]
                calls = []
                payload = service.build_payables_count_posture(
                    context=_context(),
                    resolver=_resolver(),
                    as_of_date="2026-07-09",
                    permission_checker=_permission_checker(True),
                    list_getter=_counting_getter(calls, records=records),
                )

                self.assert_safe_payables_response(payload)
                self.assertEqual(payload["state"], "unavailable")
                self.assertEqual(payload["policy"]["reason"], "payment_schedule_not_supported")
                self.assertEqual(payload["bucket_counts"], {})
                self.assertIsNone(payload["company_scope"])
                self.assertEqual(len(calls), 3)

    def test_missing_or_unsupported_status_fails_closed_before_schedule_and_aging(self):
        for status in ("Submitted", "Internal Transfer", None, ""):
            with self.subTest(status=status):
                records = list(_RECORDS) + [{
                    "company": _COMPANY_SCOPE["name"],
                    "docstatus": 1,
                    "outstanding_amount": 100,
                    "status": status,
                    "is_return": 0,
                    "return_against": "",
                    "due_date": date(2026, 7, 8),
                    "payment_terms_template": "",
                    "on_hold": 0,
                    "_payment_schedule_count": 1,
                }]
                calls = []
                payload = service.build_payables_count_posture(
                    context=_context(),
                    resolver=_resolver(),
                    as_of_date="2026-07-09",
                    permission_checker=_permission_checker(True),
                    list_getter=_counting_getter(calls, records=records),
                )

                self.assert_safe_payables_response(payload)
                self.assertEqual(payload["state"], "unavailable")
                self.assertEqual(payload["policy"]["reason"], "purchase_invoice_status_not_supported")
                self.assertEqual(payload["bucket_counts"], {})
                self.assertIsNone(payload["company_scope"])
                self.assertEqual(len(calls), 2)

    def test_wrong_company_schedule_does_not_trip_selected_company_gate(self):
        records = [
            {**record, "_payment_schedule_count": 2} if record.get("company") == "Other Company" else dict(record)
            for record in _RECORDS
        ]
        payload = service.build_payables_count_posture(
            context=_context(),
            resolver=_resolver(),
            as_of_date="2026-07-09",
            permission_checker=_permission_checker(True),
            list_getter=_counting_getter([], records=records),
        )

        self.assert_safe_payables_response(payload)
        self.assertEqual(payload["state"], "ready")

    def test_wrong_parenttype_or_parentfield_schedule_does_not_join(self):
        cases = (
            {"_payment_schedule_parenttype": "Sales Invoice"},
            {"_payment_schedule_parentfield": "other_schedule"},
        )
        for relationship_override in cases:
            with self.subTest(relationship_override=relationship_override):
                records = [dict(record) for record in _RECORDS]
                records[0].update({"_payment_schedule_count": 1, **relationship_override})
                payload = service.build_payables_count_posture(
                    context=_context(),
                    resolver=_resolver(),
                    as_of_date="2026-07-09",
                    permission_checker=_permission_checker(True),
                    list_getter=_counting_getter([], records=records),
                )

                self.assert_safe_payables_response(payload)
                self.assertEqual(payload["state"], "ready")
                self.assertEqual(payload["policy"]["reason"], "payables_count_posture_ready")

    def test_fail_closed_complexity_gates(self):
        scenarios = [
            ("missing_due_date_policy_not_ready", {"due_date": None}),
            ("future_posting_date_not_supported", {"posting_date": date(2026, 7, 10)}),
            ("payment_terms_not_supported", {"payment_terms_template": "Net 30"}),
            ("advances_not_supported", {"total_advance": 1}),
            ("on_hold_not_supported", {"on_hold": 1}),
            ("returns_debit_notes_not_supported", {"is_return": 1}),
            ("returns_debit_notes_not_supported", {"return_against": "PINV-0001"}),
        ]
        for reason, override in scenarios:
            with self.subTest(reason=reason):
                records = list(_RECORDS) + [{
                    "company": _COMPANY_SCOPE["name"],
                    "docstatus": 1,
                    "outstanding_amount": 100,
                    "status": "Unpaid",
                    "is_return": 0,
                    "return_against": "",
                    "due_date": date(2026, 7, 8),
                    "payment_terms_template": "",
                    "on_hold": 0,
                    **override,
                }]
                calls = []
                payload = service.build_payables_count_posture(
                    context=_context(),
                    resolver=_resolver(),
                    as_of_date="2026-07-09",
                    permission_checker=_permission_checker(True),
                    list_getter=_counting_getter(calls, records=records),
                )
                self.assert_safe_payables_response(payload)
                self.assertEqual(payload["state"], "unavailable")
                self.assertEqual(payload["policy"]["reason"], reason)
                self.assertEqual(payload["bucket_counts"], {})
                self.assertIsNone(payload["company_scope"])

    def test_permission_denied_or_error_returns_unavailable_without_adapter(self):
        for checker in (_permission_checker(False), lambda *args, **kwargs: (_ for _ in ()).throw(service.frappe.PermissionError("denied"))):
            payload = service.build_payables_count_posture(
                context=_context(),
                resolver=_resolver(),
                as_of_date="2026-07-09",
                permission_checker=checker,
                list_getter=_raising_getter,
            )
            self.assert_safe_payables_response(payload)
            self.assertEqual(payload["state"], "unavailable")
            self.assertEqual(payload["policy"]["reason"], "source_permission_denied")
            self.assertEqual(payload["bucket_counts"], {})

    def test_malformed_count_outputs_fail_closed(self):
        cases = (
            None,
            [],
            [{"COUNT(name)": 0}],
            [{"total": 0}],
            [{"count": None}],
            [{"count": "not-a-number"}],
            [{"count": -1}],
            [{"count": 1}, {"count": 2}],
            [{"count": 0, "extra": 0}],
        )
        for response in cases:
            with self.subTest(response=response):
                calls = []
                payload = service.build_payables_count_posture(
                    context=_context(),
                    resolver=_resolver(),
                    as_of_date="2026-07-09",
                    permission_checker=_permission_checker(True),
                    list_getter=_static_count_response_getter(response, calls=calls),
                )
                self.assert_safe_payables_response(payload)
                self.assertEqual(payload["state"], "unavailable")
                self.assertEqual(payload["policy"]["reason"], service.PAYABLES_COUNT_SOURCE_INVALID_REASON)
                self.assertEqual(payload["bucket_counts"], {})
                self.assertEqual(len(calls), 1)

    def test_overview_payables_copy_hides_raw_policy_reasons(self):
        posture = service.build_payables_count_posture(
            context=_context(['Accounts User']),
            resolver=_resolver(role_category='normal_finance'),
            as_of_date='2026-07-09',
            permission_checker=_permission_checker(True),
            list_getter=_raising_getter,
        )
        cards = service._overview_cards(
            {'state': 'scoped', 'detail': 'Company scoped', 'company': _COMPANY_SCOPE['name']},
            {'state': 'unavailable', 'detail': 'Period deferred'},
            payables_count_posture=posture,
        )
        payables_card = next(card for card in cards if card['key'] == 'payables_posture')

        self.assertIn('Manager-only payables posture', payables_card['detail'])
        self.assertIn('available only to Accounts Manager', payables_card['detail'])
        self.assertNotIn('accounts_manager_required', payables_card['detail'])
        self.assertNotIn('policy gate', payables_card['detail'])

    def test_overview_payment_schedule_unavailable_copy_is_business_facing(self):
        records = [{**record, "_payment_schedule_count": 1} for record in _RECORDS]
        posture = service.build_payables_count_posture(
            context=_context(),
            resolver=_resolver(),
            as_of_date='2026-07-09',
            permission_checker=_permission_checker(True),
            list_getter=_counting_getter([], records=records),
        )
        cards = service._overview_cards(
            {'state': 'scoped', 'detail': 'Company scoped', 'company': _COMPANY_SCOPE['name']},
            {'state': 'unavailable', 'detail': 'Period deferred'},
            payables_count_posture=posture,
        )
        payables_card = next(card for card in cards if card['key'] == 'payables_posture')

        self.assertEqual(payables_card['state'], 'unavailable')
        self.assertEqual(payables_card['value'], 'Unavailable')
        self.assertIn('supplier invoices use payment schedules', payables_card['detail'])
        self.assertIn('does not approve or initiate payments', payables_card['detail'])
        self.assertNotIn('payment_schedule_not_supported', payables_card['detail'])

    def test_static_payables_readiness_copy_is_fail_closed_not_ready(self):
        source = _FRONTEND_SOURCE.read_text(encoding="utf-8")
        self.assertIn("Payables stays count-only and fail-closed", source)
        self.assertNotIn("Payables remains count-only where approved", source)

    def test_overview_payables_ready_copy_defines_current_not_overdue(self):
        payload = service.build_payables_count_posture(
            context=_context(),
            resolver=_resolver(),
            as_of_date='2026-07-09',
            permission_checker=_permission_checker(True),
            list_getter=_counting_getter([]),
        )
        cards = service._overview_cards(
            {'state': 'scoped', 'detail': 'Company scoped', 'company': _COMPANY_SCOPE['name']},
            {'state': 'unavailable', 'detail': 'Period deferred'},
            payables_count_posture=payload,
        )
        payables_card = next(card for card in cards if card['key'] == 'payables_posture')

        self.assertIn('Current / not overdue includes invoices due today or later', payables_card['detail'])
        self.assertNotIn('AP balance', payables_card['detail'])
        self.assertNotIn('cash requirement', payables_card['detail'])
        self.assertNotIn('payment approval', payables_card['detail'])

    def test_static_source_keeps_payables_count_boundary(self):
        source = _SERVICE_SOURCE.read_text(encoding="utf-8")
        forbidden_patterns = [
            r"frappe\.get_all",
            r"frappe\.db\.sql",
            r"frappe\.db\.count",
            r"ignore_permissions",
            r"query-report",
            r"/app",
            r"/desk/Form",
            r"/desk/List",
            r"/desk/Report",
            r"Purchase Invoice Item",
            r"frappe\.db\.count",
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
        self.assertIn('PAYABLES_COUNT_SOURCE = "Purchase Invoice"', source)
        self.assertIn('PAYABLES_SCHEDULE_CHILD_SOURCE = "Payment Schedule"', source)
        self.assertIn('PAYABLES_COUNT_QUERY_FIELD = {"COUNT": "name", "as": "count"}', source)

    def test_frontend_guard_contains_ap_specific_forbidden_keys(self):
        source = _FRONTEND_SOURCE.read_text(encoding="utf-8")
        for expected in (
            "supplier_rows",
            "purchase_invoice_rows",
            "payment_entry_rows",
            "supplier_name",
            "supplier_id",
            "purchase_invoice",
            "bill_no",
            "bill_date",
            "payable_account",
            "party_name",
            "supplier_group",
            "payment_order",
            "supplier_bank_account",
            "supplier_contact",
            "supplier_tax_id",
            "supplier_statement",
            "supplier_payment_communication",
            "payment_order_created",
            "payment_run_performed",
            "purchase_invoice_lifecycle_performed",
            "payables_count_posture",
        ):
            self.assertIn(expected, source)


if __name__ == "__main__":
    unittest.main()
