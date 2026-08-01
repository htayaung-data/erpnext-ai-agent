from __future__ import annotations

import re
import sys
import types
import unittest
from datetime import date, datetime, timezone
from pathlib import Path


class _FrappePermissionError(Exception):
    pass


_TEST_DOCS = {}


def _install_frappe_stub() -> None:
    if "frappe" in sys.modules:
        return

    frappe_stub = types.ModuleType("frappe")
    frappe_stub.PermissionError = _FrappePermissionError
    frappe_stub.session = types.SimpleNamespace(user=None)
    frappe_stub.get_roles = lambda user=None: []
    frappe_stub.defaults = types.SimpleNamespace(get_user_default=lambda key: None)
    frappe_stub.local = types.SimpleNamespace(message_log=[])
    frappe_stub.flags = types.SimpleNamespace()
    frappe_stub.get_doc = lambda doctype, name: _TEST_DOCS[name]
    frappe_stub._ = lambda value: value
    frappe_stub.whitelist = lambda *args, **kwargs: (lambda fn: fn) if not args else args[0]

    def throw(message, exc=None):
        raise (exc or Exception)(message)

    frappe_stub.throw = throw

    utils_stub = types.ModuleType("frappe.utils")
    utils_stub.cstr = lambda value="": "" if value is None else str(value)
    utils_stub.now_datetime = lambda: datetime(2026, 7, 4, 0, 0, 0)
    utils_stub.flt = lambda value, precision=None: round(float(str(value).replace(",", "")), precision) if precision is not None else float(value)

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
    "future_activity_source",
    "future_activity_source_permission_checked",
    "future_activity_source_permission_verified",
    "future_activity_gate_required",
    "future_payment_ledger_activity_supported",
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
for _record_index, _record in enumerate(_RECORDS, 1):
    _record.setdefault("name", f"PINV-{_record_index:04d}")


class _SyntheticDocument:
    def __init__(self, **values):
        self.__dict__.update(values)
        self._permission = values.get("_permission", True)
        self._precision_map = values.get("_precision_map", {})
        self._field_permissions_applied = False

    def has_permission(self, permtype, *, user=None):
        return self._permission

    def apply_fieldlevel_read_permissions(self):
        self._field_permissions_applied = True

    def precision(self, fieldname):
        return self._precision_map.get(fieldname, 2)


def _schedule_row(
    *,
    name="PS-0001",
    idx=1,
    parent="PINV-SCHEDULED",
    due_date=date(2026, 7, 9),
    payment_term="",
    invoice_portion=100,
    payment_amount="100.00",
    **overrides,
):
    values = {
        "doctype": "Payment Schedule",
        "name": name,
        "idx": idx,
        "parent": parent,
        "parenttype": "Purchase Invoice",
        "parentfield": "payment_schedule",
        "due_date": due_date,
        "payment_term": payment_term,
        "invoice_portion": invoice_portion,
        "payment_amount": payment_amount,
        "base_payment_amount": payment_amount,
        "outstanding": payment_amount,
        "base_outstanding": payment_amount,
        "paid_amount": 0,
        "base_paid_amount": 0,
        "discounted_amount": 0,
        "discount": 0,
        "_precision_map": {
            "invoice_portion": 2,
            "payment_amount": 2,
            "base_payment_amount": 2,
            "outstanding": 2,
            "base_outstanding": 2,
        },
    }
    values.update(overrides)
    return _SyntheticDocument(**values)


def _document_from_record(record):
    schedule = list(record.get("_payment_schedule") or [])
    total = sum(float(getattr(row, "payment_amount", 0) or 0) for row in schedule) if schedule else 100.0
    due_date = record.get("due_date")
    values = {
        "doctype": "Purchase Invoice",
        "name": record["name"],
        "company": record.get("company"),
        "docstatus": record.get("docstatus"),
        "status": record.get("status"),
        "is_return": record.get("is_return", 0),
        "return_against": record.get("return_against"),
        "on_hold": record.get("on_hold", 0),
        "amended_from": record.get("amended_from"),
        "is_paid": record.get("is_paid", 0),
        "is_opening": record.get("is_opening", "No"),
        "posting_date": record.get("posting_date", date(2026, 7, 1)),
        "due_date": due_date,
        "outstanding_amount": record.get("outstanding_amount"),
        "total_advance": record.get("total_advance", 0),
        "write_off_amount": record.get("write_off_amount", 0),
        "base_write_off_amount": record.get("base_write_off_amount", 0),
        "payment_terms_template": record.get("payment_terms_template", ""),
        "payment_schedule": schedule,
        "currency": record.get("currency", "MMK"),
        "company_currency": record.get("company_currency", "MMK"),
        "party_account_currency": record.get("party_account_currency", "MMK"),
        "conversion_rate": record.get("conversion_rate", 1),
        "rounded_total": record.get("rounded_total", total),
        "grand_total": record.get("grand_total", total),
        "base_rounded_total": record.get("base_rounded_total", total),
        "base_grand_total": record.get("base_grand_total", total),
        "_permission": record.get("_document_permission", True),
        "_precision_map": record.get("_precision_map", {
            "grand_total": 2,
            "base_grand_total": 2,
            "outstanding_amount": 2,
        }),
    }
    values.update(record.get("_document_overrides") or {})
    return _SyntheticDocument(**values)


def _scheduled_record(*, name="PINV-SCHEDULED", rows=None, **overrides):
    active_rows = list(rows or [_schedule_row(parent=name)])
    record = {
        **_RECORDS[0],
        "name": name,
        "due_date": max(getattr(row, "due_date") for row in active_rows),
        "outstanding_amount": 100.0,
        "rounded_total": "100.00",
        "grand_total": "100.00",
        "base_rounded_total": "100.00",
        "base_grand_total": "100.00",
        "_payment_schedule": active_rows,
    }
    record.update(overrides)
    return record


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


def _counting_getter(calls, records=None, future_activity_records=None):
    source_records = [dict(record) for record in (_RECORDS if records is None else records)]
    for index, record in enumerate(source_records, 1):
        record.setdefault("name", f"PINV-CUSTOM-{index:04d}")
    _TEST_DOCS.clear()
    _TEST_DOCS.update({record["name"]: _document_from_record(record) for record in source_records})
    future_records = list(future_activity_records or [])

    def getter(doctype, **kwargs):
        calls.append((doctype, kwargs))
        filters = kwargs.get("filters") or []
        if doctype == service.PAYABLES_FUTURE_ACTIVITY_SOURCE:
            count = sum(
                1
                for record in future_records
                if all(_matches_filter(record, item) for item in filters)
            )
            return [{"count": count}]
        if doctype != service.PAYABLES_COUNT_SOURCE:
            raise AssertionError(f"Unexpected Payables source: {doctype!r}")
        if kwargs.get("fields") == ["name"]:
            return [
                {"name": record["name"]}
                for record in sorted(source_records, key=lambda item: item["name"])
                if all(_matches_filter(record, item) for item in filters)
            ]
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
        self.assertEqual(payload["policy"]["future_activity_source"], "Payment Ledger Entry")
        self.assertEqual(payload["policy"]["future_activity_gate_required"], True)
        self.assertEqual(payload["policy"]["future_payment_ledger_activity_supported"], False)
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
        self.assertEqual(permission_calls[:2], [
            ("Purchase Invoice", {"ptype": "read", "user": "finance.lead@meet.com"}),
            ("Payment Ledger Entry", {"ptype": "read", "user": "finance.lead@meet.com"}),
        ])
        record_checks = permission_calls[2:]
        self.assertEqual(len(record_checks), 18)
        self.assertTrue(all(doctype == "Purchase Invoice" for doctype, _kwargs in record_checks))
        self.assertTrue(
            all(
                kwargs["ptype"] == "read"
                and kwargs["throw"] is False
                and "print_logs" not in kwargs
                for _doctype, kwargs in record_checks
            )
        )
        self.assertEqual(len(calls), 11)

    def test_record_permission_call_matches_pinned_frappe_signature(self):
        calls = []

        def pinned_has_permission(
            doctype=None,
            ptype="read",
            doc=None,
            user=None,
            throw=False,
            *,
            parent_doctype=None,
            debug=False,
            ignore_share_permissions=False,
        ):
            calls.append((doctype, ptype, doc, user, throw, parent_doctype, debug, ignore_share_permissions))
            return True

        self.assertTrue(
            service._payables_record_permission(
                pinned_has_permission,
                "PINV-PINNED-SIGNATURE",
                "finance.manager@example.invalid",
            )
        )
        self.assertEqual(
            calls,
            [
                (
                    "Purchase Invoice",
                    "read",
                    "PINV-PINNED-SIGNATURE",
                    "finance.manager@example.invalid",
                    False,
                    None,
                    False,
                    False,
                )
            ],
        )

    def test_invalid_supplied_as_of_values_fail_closed_before_source_reads(self):
        invalid_values = (
            "",
            " 2026-07-06",
            "2026-07-06 ",
            "2026-07-06T00:00:00",
            datetime(2026, 7, 6, 0, 0, 0),
            datetime(2026, 7, 6, 0, 0, 0, tzinfo=timezone.utc),
        )
        for invalid_value in invalid_values:
            with self.subTest(value=repr(invalid_value)):
                payload = service.build_payables_count_posture(
                    context=_context(),
                    resolver=_resolver(),
                    as_of_date=invalid_value,
                    permission_checker=lambda *args, **kwargs: (_ for _ in ()).throw(
                        AssertionError("permission gate must not run for invalid date")
                    ),
                    list_getter=lambda *args, **kwargs: (_ for _ in ()).throw(
                        AssertionError("source adapter must not run for invalid date")
                    ),
                )
                self.assert_safe_payables_response(payload)
                self.assertEqual(payload["state"], "unavailable")
                self.assertEqual(payload["policy"]["reason"], "invalid_as_of_date")
                self.assertEqual(payload["bucket_counts"], {})

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
        purchase_calls = [(doctype, kwargs) for doctype, kwargs in calls if doctype == "Purchase Invoice"]
        future_calls = [(doctype, kwargs) for doctype, kwargs in calls if doctype == "Payment Ledger Entry"]
        count_calls = [(doctype, kwargs) for doctype, kwargs in purchase_calls if kwargs["fields"] == [service.PAYABLES_COUNT_QUERY_FIELD]]
        manifest_calls = [(doctype, kwargs) for doctype, kwargs in purchase_calls if kwargs["fields"] == ["name"]]
        for doctype, kwargs in count_calls:
            self.assertEqual(doctype, "Purchase Invoice")
            self.assertEqual(kwargs["fields"], [service.PAYABLES_COUNT_QUERY_FIELD])
            self.assertEqual(kwargs["limit_page_length"], 1)
            self.assertNotIn("ignore_permissions", kwargs)
            self.assertNotIn("order_by", kwargs)
            filters = kwargs["filters"]
            self.assertIn(["company", "=", _COMPANY_SCOPE["name"]], filters)
            self.assertIn(["docstatus", "=", 1], filters)
        self.assertEqual(len(future_calls), 1)
        future_filters = future_calls[0][1]["filters"]
        self.assertEqual(future_calls[0][1]["fields"], [service.PAYABLES_COUNT_QUERY_FIELD])
        self.assertEqual(future_calls[0][1]["limit_page_length"], 1)
        self.assertNotIn("ignore_permissions", future_calls[0][1])
        self.assertEqual(future_filters, [
            ["company", "=", _COMPANY_SCOPE["name"]],
            ["party_type", "=", "Supplier"],
            ["delinked", "=", 0],
            ["posting_date", ">", "2026-07-09"],
        ])
        self.assertNotIn(["status", "in", list(service.PAYABLES_OPEN_STATUSES)], count_calls[0][1]["filters"])
        self.assertIn(["status", "in", list(service.PAYABLES_OPEN_STATUSES)], count_calls[1][1]["filters"])
        self.assertEqual(len(manifest_calls), 2)
        for _doctype, kwargs in manifest_calls:
            self.assertEqual(kwargs["order_by"], "name asc")
            self.assertEqual(kwargs["limit_start"], 0)
            self.assertEqual(kwargs["limit_page_length"], service.PAYABLES_SCHEDULE_CANDIDATE_MAX_ROWS + 1)
            self.assertNotIn("parent_doctype", kwargs)
            self.assertNotIn("ignore_permissions", kwargs)
            filters = kwargs["filters"]
            self.assertIn(["outstanding_amount", ">", 0], filters)
            self.assertIn(["status", "in", list(service.PAYABLES_OPEN_STATUSES)], filters)
            self.assertIn(["is_return", "=", 0], filters)
            self.assertIn(["return_against", "is", "not set"], filters)
        self.assertFalse(any(doctype == "Payment Schedule" for doctype, _kwargs in calls))

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

    def test_template_and_template_less_schedules_count_open_obligations_by_child_due_date(self):
        template_less = {
            **_RECORDS[0],
            "name": "PINV-TEMPLATE-LESS",
            "due_date": date(2026, 7, 9),
            "_payment_schedule": [_schedule_row(parent="PINV-TEMPLATE-LESS")],
        }
        template_rows = [
            _schedule_row(
                name="PS-TEMPLATE-1",
                idx=1,
                parent="PINV-TEMPLATE",
                due_date=date(2026, 7, 8),
                payment_term="Term 1",
                invoice_portion=50,
                payment_amount="50.00",
            ),
            _schedule_row(
                name="PS-TEMPLATE-2",
                idx=2,
                parent="PINV-TEMPLATE",
                due_date=date(2026, 5, 9),
                payment_term="Term 2",
                invoice_portion=50,
                payment_amount="50.00",
            ),
        ]
        templated = {
            **_RECORDS[0],
            "name": "PINV-TEMPLATE",
            "due_date": date(2026, 7, 8),
            "payment_terms_template": "Net split",
            "_payment_schedule": template_rows,
        }
        payload = service.build_payables_count_posture(
            context=_context(),
            resolver=_resolver(),
            as_of_date="2026-07-09",
            permission_checker=_permission_checker(True),
            list_getter=_counting_getter([], records=[template_less, templated]),
        )

        self.assert_safe_payables_response(payload)
        self.assertEqual(payload["state"], "ready")
        self.assertEqual(payload["bucket_counts"], {
            "not_due": 1,
            "overdue_1_30": 1,
            "overdue_31_60": 0,
            "overdue_61_90": 1,
            "overdue_over_90": 0,
        })
        self.assertTrue(payload["policy"]["payment_terms_supported"])
        self.assertTrue(payload["policy"]["payment_schedule_supported"])
        self.assertFalse(payload["policy"]["payment_schedule_presence_gate_required"])
        self.assertFalse(payload["policy"]["payment_schedule_rows_returned"])

    def test_schedule_boundaries_and_permitted_total_residual_are_deterministic(self):
        dates = (
            date(2026, 7, 9),
            date(2026, 7, 8),
            date(2026, 6, 9),
            date(2026, 6, 8),
            date(2026, 5, 10),
            date(2026, 5, 9),
            date(2026, 4, 10),
            date(2026, 4, 9),
        )
        portions = ("12.50",) * 8
        amounts = ("12.51", "12.50", "12.50", "12.50", "12.50", "12.50", "12.50", "12.50")
        rows = [
            _schedule_row(
                name=f"PS-BOUNDARY-{index}",
                idx=index,
                parent="PINV-BOUNDARY",
                due_date=due,
                payment_term=f"Term {index}",
                invoice_portion=portions[index - 1],
                payment_amount=amounts[index - 1],
            )
            for index, due in enumerate(dates, 1)
        ]
        record = {
            **_RECORDS[0],
            "name": "PINV-BOUNDARY",
            "due_date": max(dates),
            "outstanding_amount": 100.0,
            "rounded_total": "100.00",
            "grand_total": "100.00",
            "base_rounded_total": "100.00",
            "base_grand_total": "100.00",
            "_payment_schedule": rows,
        }
        payload = service.build_payables_count_posture(
            context=_context(), resolver=_resolver(), as_of_date="2026-07-09",
            permission_checker=_permission_checker(True), list_getter=_counting_getter([], records=[record]),
        )

        self.assertEqual(payload["state"], "ready")
        self.assertEqual(payload["bucket_counts"], {
            "not_due": 1,
            "overdue_1_30": 2,
            "overdue_31_60": 2,
            "overdue_61_90": 2,
            "overdue_over_90": 1,
        })

    def test_scheduleless_invoices_preserve_existing_parent_due_date_cohort(self):
        records = [
            {
                **_RECORDS[0],
                "name": "PINV-SCHEDULELESS-OPENING",
                "is_opening": "Yes",
            },
            {
                **_RECORDS[0],
                "name": "PINV-SCHEDULELESS-AMENDED",
                "amended_from": "PINV-SCHEDULELESS-OLD",
            },
            {
                **_RECORDS[0],
                "name": "PINV-SCHEDULELESS-WRITEOFF",
                "status": "Partly Paid",
                "outstanding_amount": 75,
                "write_off_amount": 25,
                "base_write_off_amount": 25,
            },
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
        self.assertEqual(payload["bucket_counts"], {
            "not_due": 3,
            "overdue_1_30": 0,
            "overdue_31_60": 0,
            "overdue_61_90": 0,
            "overdue_over_90": 0,
        })

    def test_scheduleless_template_without_rows_fails_closed_as_stale(self):
        record = {
            **_RECORDS[0],
            "name": "PINV-SCHEDULELESS-STALE-TEMPLATE",
            "payment_terms_template": "Net split",
        }
        payload = service.build_payables_count_posture(
            context=_context(),
            resolver=_resolver(),
            as_of_date="2026-07-09",
            permission_checker=_permission_checker(True),
            list_getter=_counting_getter([], records=[record]),
        )

        self.assert_safe_payables_response(payload)
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["policy"]["reason"], service.PAYABLES_SCHEDULE_INVALID_REASON)
        self.assertEqual(payload["bucket_counts"], {})

    def test_malformed_schedule_totals_dates_precision_currency_and_allocations_fail_closed(self):
        cases = []
        cases.append(("missing_due_date", _scheduled_record(rows=[_schedule_row(due_date=None)], due_date=date(2026, 7, 9))))
        cases.append(("invalid_due_date", _scheduled_record(rows=[_schedule_row(due_date="2026-02-30")], due_date=date(2026, 7, 9))))
        cases.append(("total_mismatch", _scheduled_record(rows=[_schedule_row(payment_amount="99.89", outstanding="99.89", base_payment_amount="99.89", base_outstanding="99.89")])))
        cases.append(("malformed_amount", _scheduled_record(rows=[_schedule_row(payment_amount="NaN")])))
        cases.append(("bad_precision", _scheduled_record(rows=[_schedule_row(_precision_map={"invoice_portion": 2, "payment_amount": 9, "base_payment_amount": 2, "outstanding": 2, "base_outstanding": 2})])))
        cases.append(("transaction_currency", _scheduled_record(currency="USD")))
        cases.append(("party_currency", _scheduled_record(party_account_currency="USD")))
        cases.append(("conversion_rate", _scheduled_record(conversion_rate="0.5")))
        cases.append(("partial_paid", _scheduled_record(rows=[_schedule_row(paid_amount="10.00", outstanding="90.00")], outstanding_amount=90.0, status="Partly Paid")))
        cases.append(("base_partial_paid", _scheduled_record(rows=[_schedule_row(base_paid_amount="10.00", base_outstanding="90.00")])))
        cases.append(("discounted", _scheduled_record(rows=[_schedule_row(discounted_amount="1.00")])))
        cases.append(("discount_offer", _scheduled_record(rows=[_schedule_row(discount="2.00")])))
        cases.append(("child_outstanding", _scheduled_record(rows=[_schedule_row(outstanding="99.00")])))
        cases.append(("parent_outstanding", _scheduled_record(outstanding_amount=99.0)))
        cases.append(("parent_due_date", _scheduled_record(due_date=date(2026, 7, 10))))
        cases.append(("portion_total", _scheduled_record(rows=[_schedule_row(invoice_portion="99.00")])))
        cases.append(("amended", _scheduled_record(amended_from="PINV-OLD")))
        cases.append(("opening", _scheduled_record(is_opening="Yes")))
        cases.append(("paid_flag", _scheduled_record(is_paid=1)))
        cases.append(("write_off", _scheduled_record(write_off_amount="1.00")))
        cases.append(("base_write_off", _scheduled_record(base_write_off_amount="1.00")))

        for label, record in cases:
            with self.subTest(label=label):
                payload = service.build_payables_count_posture(
                    context=_context(), resolver=_resolver(), as_of_date="2026-07-09",
                    permission_checker=_permission_checker(True),
                    list_getter=_counting_getter([], records=[record]),
                )
                self.assert_safe_payables_response(payload)
                self.assertEqual(payload["state"], "unavailable")
                self.assertEqual(payload["policy"]["reason"], service.PAYABLES_SCHEDULE_INVALID_REASON)
                self.assertEqual(payload["bucket_counts"], {})
                self.assertIsNone(payload["company_scope"])
                self.assertNotIn("'NaN'", repr(payload))

    def test_duplicate_or_ambiguous_schedule_rows_fail_closed_without_partial_buckets(self):
        first = _schedule_row(
            name="PS-DUP-1", idx=1, parent="PINV-DUP", due_date=date(2026, 7, 8),
            payment_term="Term 1", invoice_portion=50, payment_amount="50.00",
        )
        valid_second = dict(
            name="PS-DUP-2", idx=2, parent="PINV-DUP", due_date=date(2026, 8, 8),
            payment_term="Term 2", invoice_portion=50, payment_amount="50.00",
        )
        cases = (
            ("name", _schedule_row(**{**valid_second, "name": "PS-DUP-1"})),
            ("index", _schedule_row(**{**valid_second, "idx": 1})),
            ("date", _schedule_row(**{**valid_second, "due_date": date(2026, 7, 8)})),
            ("term", _schedule_row(**{**valid_second, "payment_term": "Term 1"})),
            ("blank_term", _schedule_row(**{**valid_second, "payment_term": ""})),
        )
        for label, second in cases:
            with self.subTest(label=label):
                record = _scheduled_record(name="PINV-DUP", rows=[first, second])
                payload = service.build_payables_count_posture(
                    context=_context(), resolver=_resolver(), as_of_date="2026-07-09",
                    permission_checker=_permission_checker(True),
                    list_getter=_counting_getter([], records=[record]),
                )
                self.assertEqual(payload["state"], "unavailable")
                self.assertEqual(payload["bucket_counts"], {})
                self.assertEqual(payload["policy"]["reason"], service.PAYABLES_SCHEDULE_INVALID_REASON)

    def test_record_permission_ambiguity_document_denial_and_manifest_drift_are_all_or_nothing(self):
        records = [
            _scheduled_record(name="PINV-A", rows=[_schedule_row(name="PS-A", parent="PINV-A")]),
            _scheduled_record(name="PINV-B", rows=[_schedule_row(name="PS-B", parent="PINV-B")]),
        ]

        def ambiguous_checker(doctype, **kwargs):
            if "doc" in kwargs:
                service.frappe.local.message_log.append("SECRET-PINV-A")
                service.frappe.flags.error_message = "SECRET-PINV-A"
                return {"allowed": True}
            return True

        service.frappe.local.message_log[:] = ["existing"]
        service.frappe.flags.error_message = "existing-error"
        payload = service.build_payables_count_posture(
            context=_context(), resolver=_resolver(), as_of_date="2026-07-09",
            permission_checker=ambiguous_checker,
            list_getter=_counting_getter([], records=records),
        )
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["bucket_counts"], {})
        self.assertEqual(service.frappe.local.message_log, ["existing"])
        self.assertEqual(service.frappe.flags.error_message, "existing-error")
        self.assertNotIn("secret", repr(payload).lower())

        denied = [dict(records[0], _document_permission=False)]
        denied_payload = service.build_payables_count_posture(
            context=_context(), resolver=_resolver(), as_of_date="2026-07-09",
            permission_checker=_permission_checker(True),
            list_getter=_counting_getter([], records=denied),
        )
        self.assertEqual(denied_payload["state"], "unavailable")
        self.assertEqual(denied_payload["bucket_counts"], {})

        calls = []
        base_getter = _counting_getter(calls, records=records)
        manifest_reads = 0

        def drifting_getter(doctype, **kwargs):
            nonlocal manifest_reads
            result = base_getter(doctype, **kwargs)
            if doctype == "Purchase Invoice" and kwargs.get("fields") == ["name"]:
                manifest_reads += 1
                if manifest_reads == 2:
                    return list(reversed(result))
            return result

        drift_payload = service.build_payables_count_posture(
            context=_context(), resolver=_resolver(), as_of_date="2026-07-09",
            permission_checker=_permission_checker(True), list_getter=drifting_getter,
        )
        self.assertEqual(drift_payload["state"], "unavailable")
        self.assertEqual(drift_payload["bucket_counts"], {})

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

    def test_wrong_company_schedule_is_not_loaded_or_counted(self):
        records = [
            {
                **record,
                "_payment_schedule": [_schedule_row(parent=record["name"])],
            } if record.get("company") == "Other Company" else dict(record)
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

    def test_wrong_parenttype_parentfield_or_parent_fails_entire_posture(self):
        cases = (
            {"parenttype": "Sales Invoice"},
            {"parentfield": "other_schedule"},
            {"parent": "PINV-OTHER"},
        )
        for relationship_override in cases:
            with self.subTest(relationship_override=relationship_override):
                records = [{
                    **_RECORDS[0],
                    "name": "PINV-RELATION",
                    "due_date": date(2026, 7, 9),
                    "_payment_schedule": [_schedule_row(**{"parent": "PINV-RELATION", **relationship_override})],
                }]
                payload = service.build_payables_count_posture(
                    context=_context(),
                    resolver=_resolver(),
                    as_of_date="2026-07-09",
                    permission_checker=_permission_checker(True),
                    list_getter=_counting_getter([], records=records),
                )

                self.assert_safe_payables_response(payload)
                self.assertEqual(payload["state"], "unavailable")
                self.assertEqual(payload["policy"]["reason"], service.PAYABLES_SCHEDULE_INVALID_REASON)
                self.assertEqual(payload["bucket_counts"], {})

    def test_fail_closed_complexity_gates(self):
        scenarios = [
            ("missing_due_date_policy_not_ready", {"due_date": None}),
            ("future_posting_date_not_supported", {"posting_date": date(2026, 7, 10)}),
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

    def test_future_payment_ledger_activity_suppresses_all_ap_counts(self):
        future_activity = [{
            "company": _COMPANY_SCOPE["name"],
            "account_type": "Payable",
            "party_type": "Supplier",
            "delinked": 0,
            "posting_date": date(2026, 7, 10),
        }]
        calls = []
        payload = service.build_payables_count_posture(
            context=_context(),
            resolver=_resolver(),
            as_of_date="2026-07-09",
            permission_checker=_permission_checker(True),
            list_getter=_counting_getter(calls, future_activity_records=future_activity),
        )

        self.assert_safe_payables_response(payload)
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["policy"]["reason"], "future_payment_ledger_activity_not_supported")
        self.assertEqual(payload["bucket_counts"], {})
        self.assertIsNone(payload["company_scope"])
        self.assertEqual(sum(doctype == "Payment Ledger Entry" for doctype, _kwargs in calls), 1)
        self.assertFalse(any(
            kwargs["filters"][-1][0] == "due_date" and kwargs["filters"][-1][1] in {">=", "between", "<="}
            for doctype, kwargs in calls
            if doctype == "Purchase Invoice"
        ))

    def test_future_supplier_activity_cannot_evade_gate_through_account_type(self):
        payload = service.build_payables_count_posture(
            context=_context(),
            resolver=_resolver(),
            as_of_date="2026-07-09",
            permission_checker=_permission_checker(True),
            list_getter=_counting_getter([], future_activity_records=[{
                "company": _COMPANY_SCOPE["name"],
                "account_type": "Unexpected",
                "party_type": "Supplier",
                "delinked": 0,
                "posting_date": date(2026, 7, 10),
            }]),
        )

        self.assert_safe_payables_response(payload)
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["policy"]["reason"], "future_payment_ledger_activity_not_supported")
        self.assertEqual(payload["bucket_counts"], {})
        self.assertIsNone(payload["company_scope"])

    def test_future_activity_in_another_company_does_not_affect_selected_company(self):
        payload = service.build_payables_count_posture(
            context=_context(),
            resolver=_resolver(),
            as_of_date="2026-07-09",
            permission_checker=_permission_checker(True),
            list_getter=_counting_getter([], future_activity_records=[{
                "company": "Other Company",
                "account_type": "Payable",
                "party_type": "Supplier",
                "delinked": 0,
                "posting_date": date(2026, 7, 10),
            }]),
        )

        self.assert_safe_payables_response(payload)
        self.assertEqual(payload["state"], "ready")

    def test_future_activity_permission_denial_fails_before_any_source_adapter(self):
        permission_calls = []

        def checker(doctype, **kwargs):
            permission_calls.append((doctype, kwargs))
            return doctype == "Purchase Invoice"

        payload = service.build_payables_count_posture(
            context=_context(),
            resolver=_resolver(),
            as_of_date="2026-07-09",
            permission_checker=checker,
            list_getter=_raising_getter,
        )

        self.assert_safe_payables_response(payload)
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["policy"]["reason"], "future_activity_source_permission_denied")
        self.assertEqual(payload["bucket_counts"], {})
        self.assertEqual(permission_calls, [
            ("Purchase Invoice", {"ptype": "read", "user": "finance.lead@meet.com"}),
            ("Payment Ledger Entry", {"ptype": "read", "user": "finance.lead@meet.com"}),
        ])

    def test_future_activity_probe_permission_error_malformed_or_ambiguous_output_fails_closed(self):
        cases = (
            ("permission_error", service.frappe.PermissionError("denied"), "permission_preserving_payables_future_activity_unavailable"),
            ("none", None, service.PAYABLES_FUTURE_ACTIVITY_SOURCE_INVALID_REASON),
            ("false", False, service.PAYABLES_FUTURE_ACTIVITY_SOURCE_INVALID_REASON),
            ("zero", 0, service.PAYABLES_FUTURE_ACTIVITY_SOURCE_INVALID_REASON),
            ("empty_string", "", service.PAYABLES_FUTURE_ACTIVITY_SOURCE_INVALID_REASON),
            ("mapping", {"count": 0}, service.PAYABLES_FUTURE_ACTIVITY_SOURCE_INVALID_REASON),
            ("tuple", ({"count": 0},), service.PAYABLES_FUTURE_ACTIVITY_SOURCE_INVALID_REASON),
            ("unexpected_alias", [{"total": 0}], service.PAYABLES_FUTURE_ACTIVITY_SOURCE_INVALID_REASON),
            ("ambiguous_multiple_rows", [{"count": 0}, {"count": 0}], service.PAYABLES_FUTURE_ACTIVITY_SOURCE_INVALID_REASON),
            ("negative", [{"count": -1}], service.PAYABLES_FUTURE_ACTIVITY_SOURCE_INVALID_REASON),
        )
        for label, response, expected_reason in cases:
            with self.subTest(label=label):
                calls = []
                purchase_getter = _counting_getter(calls)

                def getter(doctype, **kwargs):
                    if doctype == "Payment Ledger Entry":
                        calls.append((doctype, kwargs))
                        if isinstance(response, Exception):
                            raise response
                        return response
                    return purchase_getter(doctype, **kwargs)

                payload = service.build_payables_count_posture(
                    context=_context(),
                    resolver=_resolver(),
                    as_of_date="2026-07-09",
                    permission_checker=_permission_checker(True),
                    list_getter=getter,
                )

                self.assert_safe_payables_response(payload)
                self.assertEqual(payload["state"], "unavailable")
                self.assertEqual(payload["policy"]["reason"], expected_reason)
                self.assertEqual(payload["bucket_counts"], {})
                self.assertIsNone(payload["company_scope"])
                self.assertNotIn("grand_total", payload)

    def test_future_activity_read_failure_discards_only_new_frappe_messages(self):
        calls = []
        purchase_getter = _counting_getter(calls)
        prior_local = getattr(service.frappe, "local", None)
        service.frappe.local = types.SimpleNamespace(message_log=["existing-message"])

        def getter(doctype, **kwargs):
            if doctype == "Payment Ledger Entry":
                calls.append((doctype, kwargs))
                service.frappe.local.message_log.append("permission-denied-message")
                raise service.frappe.PermissionError("denied")
            return purchase_getter(doctype, **kwargs)

        try:
            payload = service.build_payables_count_posture(
                context=_context(),
                resolver=_resolver(),
                as_of_date="2026-07-09",
                permission_checker=_permission_checker(True),
                list_getter=getter,
            )
        finally:
            message_log = list(service.frappe.local.message_log)
            if prior_local is None:
                delattr(service.frappe, "local")
            else:
                service.frappe.local = prior_local

        self.assert_safe_payables_response(payload)
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["bucket_counts"], {})
        self.assertEqual(message_log, ["existing-message"])

    def test_future_activity_gate_response_contains_no_identity_amount_or_date_fields(self):
        payload = service.build_payables_count_posture(
            context=_context(),
            resolver=_resolver(),
            as_of_date="2026-07-09",
            permission_checker=_permission_checker(True),
            list_getter=_counting_getter([], future_activity_records=[{
                "company": _COMPANY_SCOPE["name"],
                "account_type": "Payable",
                "party_type": "Supplier",
                "delinked": 0,
                "posting_date": date(2026, 7, 10),
                "party": "SUPPLIER-SECRET",
                "voucher_no": "PINV-SECRET",
                "name": "PLE-SECRET",
                "amount": "999.00",
            }]),
        )
        serialized = repr(payload).lower()
        for forbidden in ("supplier-secret", "pinv-secret", "ple-secret", "999.00", "2026-07-10"):
            self.assertNotIn(forbidden, serialized)

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
        records = [_scheduled_record(rows=[_schedule_row(outstanding="99.00")])]
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
        self.assertIn('complete payable-obligation schedule could not be proven', payables_card['detail'])
        self.assertIn('does not approve or initiate payments', payables_card['detail'])
        self.assertNotIn(service.PAYABLES_SCHEDULE_INVALID_REASON, payables_card['detail'])

    def test_static_payables_readiness_copy_is_fail_closed_not_ready(self):
        source = _FRONTEND_SOURCE.read_text(encoding="utf-8")
        self.assertIn("Payables stays count-only and fail-closed", source)
        self.assertIn("supported installment schedules", source)
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

        self.assertIn('Open payable obligation count buckets only', payables_card['detail'])
        self.assertIn('Current / not overdue includes obligations due today or later', payables_card['detail'])
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
        self.assertIn('getattr(frappe, "get_doc", None)', source)
        self.assertIn('apply_fieldlevel_read_permissions', source)
        self.assertIn('PAYABLES_COUNT_SOURCE = "Purchase Invoice"', source)
        self.assertIn('PAYABLES_SCHEDULE_CHILD_SOURCE = "Payment Schedule"', source)
        self.assertIn('PAYABLES_FUTURE_ACTIVITY_SOURCE = "Payment Ledger Entry"', source)
        self.assertIn('PAYABLES_COUNT_QUERY_FIELD = {"COUNT": "name", "as": "count"}', source)
        self.assertNotIn('getter(\n            PAYABLES_SCHEDULE_CHILD_SOURCE', source)

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
