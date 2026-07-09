from __future__ import annotations

import re
import sys
import types
import unittest
from datetime import date, datetime
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

_COMPANY_SCOPE = {
    "name": "Mingalar Mobile Distribution Co., Ltd.",
    "label": "Mingalar Mobile Distribution Co., Ltd.",
    "currency": "MMK",
}

_BASE_AMOUNT_KEYS = {
    "phase",
    "state",
    "company_scope",
    "as_of_date",
    "currency",
    "bucket_labels",
    "bucket_counts",
    "bucket_amounts",
    "suppressed_buckets",
    "policy",
    "no_effect",
    "rows_returned",
    "amounts_are_aggregate",
    "documents_returned",
    "runtime_payment_ledger_amount_summary_enabled",
}
_READY_WITH_TOTAL_KEYS = _BASE_AMOUNT_KEYS | {"grand_total"}


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


class _Meta:
    def __init__(self, amount_options="Company:company:default_currency", account_amount_options="account_currency"):
        self.amount_options = amount_options
        self.account_amount_options = account_amount_options

    def get_field(self, fieldname):
        if fieldname == "amount":
            return types.SimpleNamespace(options=self.amount_options)
        if fieldname == "amount_in_account_currency":
            return types.SimpleNamespace(options=self.account_amount_options)
        return None


def _metadata_provider(amount_options="Company:company:default_currency", account_amount_options="account_currency", calls=None):
    def provider(doctype):
        if calls is not None:
            calls.append(doctype)
        if doctype != service.RECEIVABLES_AMOUNT_SOURCE:
            raise AssertionError(f"Unexpected metadata source: {doctype!r}")
        return _Meta(amount_options=amount_options, account_amount_options=account_amount_options)

    return provider


def _raising_getter(*args, **kwargs):
    raise AssertionError("Payment Ledger Entry adapter should not run")


def _raising_permission(*args, **kwargs):
    raise AssertionError("Payment Ledger Entry permission check should not run")


def _raising_metadata(*args, **kwargs):
    raise AssertionError("Payment Ledger Entry metadata check should not run")


def _as_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value in (None, ""):
        return None
    return date.fromisoformat(str(value)[:10])


def _matches_filter(record, item):
    field, operator, value = item
    current = record.get(field)
    if operator == "=":
        return current == value
    if operator == "<=":
        current_date = _as_date(current)
        return current_date is not None and current_date <= date.fromisoformat(value)
    raise AssertionError(f"Unexpected Payment Ledger filter: {item!r}")


def _payment_ledger_getter(records, calls=None):
    def getter(doctype, **kwargs):
        if calls is not None:
            calls.append((doctype, kwargs))
        if doctype != service.RECEIVABLES_AMOUNT_SOURCE:
            raise AssertionError(f"Unexpected source: {doctype!r}")
        if kwargs.get("fields") != list(service.RECEIVABLES_AMOUNT_SOURCE_FIELDS):
            raise AssertionError("Payment Ledger fields drifted")
        page_size = kwargs.get("limit_page_length")
        limit_start = kwargs.get("limit_start")
        if not isinstance(page_size, int) or page_size <= 0:
            raise AssertionError("Payment Ledger read must use a positive bounded page size")
        if page_size > service.RECEIVABLES_AMOUNT_SOURCE_PAGE_SIZE:
            raise AssertionError("Payment Ledger page size exceeds configured cap")
        if not isinstance(limit_start, int) or limit_start < 0:
            raise AssertionError("Payment Ledger read must use explicit pagination")
        for forbidden in ("ignore_permissions", "order_by", "as_list", "pluck"):
            if forbidden in kwargs:
                raise AssertionError(f"Forbidden Payment Ledger query option: {forbidden}")
        filters = kwargs.get("filters") or []
        expected_filters = [
            ["company", "=", _COMPANY_SCOPE["name"]],
            ["account_type", "=", "Receivable"],
            ["party_type", "=", "Customer"],
            ["delinked", "=", 0],
        ]
        for expected in expected_filters:
            if expected not in filters:
                raise AssertionError(f"Missing required Payment Ledger filter: {expected!r}")
        if not any(item[:2] == ["posting_date", "<="] for item in filters):
            raise AssertionError("Missing as-of posting date filter")
        matched = [dict(record) for record in records if all(_matches_filter(record, item) for item in filters)]
        return matched[limit_start : limit_start + page_size]

    return getter


def _ple(
    *,
    voucher_type,
    voucher_no,
    party,
    amount,
    posting_date,
    due_date=None,
    against_voucher_type="Sales Invoice",
    against_voucher_no=None,
    account="Debtors - MMD",
    company=None,
    account_type="Receivable",
    party_type="Customer",
    account_currency="MMK",
    delinked=0,
):
    return {
        "company": company or _COMPANY_SCOPE["name"],
        "account": account,
        "account_type": account_type,
        "party_type": party_type,
        "party": party,
        "voucher_type": voucher_type,
        "voucher_no": voucher_no,
        "against_voucher_type": against_voucher_type,
        "against_voucher_no": against_voucher_no if against_voucher_no is not None else voucher_no,
        "posting_date": posting_date,
        "due_date": due_date,
        "amount": amount,
        "amount_in_account_currency": amount,
        "account_currency": account_currency,
        "delinked": delinked,
    }


def _invoice(name, party, amount, due_date, posting_date=None, account="Debtors - MMD", company=None):
    return _ple(
        voucher_type="Sales Invoice",
        voucher_no=name,
        party=party,
        amount=amount,
        posting_date=posting_date or due_date,
        due_date=due_date,
        against_voucher_type="Sales Invoice",
        against_voucher_no=name,
        account=account,
        company=company,
    )


def _payment(name, against_invoice, party, amount, posting_date, account="Debtors - MMD"):
    return _ple(
        voucher_type="Payment Entry",
        voucher_no=name,
        party=party,
        amount=-abs(amount),
        posting_date=posting_date,
        due_date=None,
        against_voucher_type="Sales Invoice",
        against_voucher_no=against_invoice,
        account=account,
    )


def _journal(name, against_invoice, party, amount, posting_date):
    return _ple(
        voucher_type="Journal Entry",
        voucher_no=name,
        party=party,
        amount=-abs(amount),
        posting_date=posting_date,
        due_date=None,
        against_voucher_type="Sales Invoice",
        against_voucher_no=against_invoice,
    )


def _credit_invoice(name, against_invoice, party, amount, posting_date):
    return _ple(
        voucher_type="Sales Invoice",
        voucher_no=name,
        party=party,
        amount=-abs(amount),
        posting_date=posting_date,
        due_date=posting_date,
        against_voucher_type="Sales Invoice",
        against_voucher_no=against_invoice,
    )


def _safe_summary(records, **kwargs):
    calls = kwargs.pop("calls", None)
    return service.build_receivables_payment_ledger_amount_summary(
        context=_context(),
        resolver=_resolver(),
        as_of_date="2026-07-06",
        permission_checker=_permission_checker(True),
        metadata_provider=_metadata_provider(),
        list_getter=_payment_ledger_getter(records, calls=calls),
        **kwargs,
    )


def _direct_summary(records):
    return service.build_receivables_payment_ledger_amount_summary(
        context=_context(),
        resolver=_resolver(),
        as_of_date="2026-07-06",
        permission_checker=_permission_checker(True),
        metadata_provider=_metadata_provider(),
        list_getter=lambda doctype, **kwargs: records,
    )


def _overview_count_stub(filters, list_getter=None):
    return 0 if filters[-1] == ["due_date", "is", "not set"] else 3


class TestFinanceReceivablesPaymentLedgerAmountSummary(unittest.TestCase):
    def assert_safe_amount_response(self, payload):
        allowed = _READY_WITH_TOTAL_KEYS if "grand_total" in payload else _BASE_AMOUNT_KEYS
        self.assertEqual(set(payload), allowed)
        self.assertEqual(payload["phase"], service.FINANCE_RECEIVABLES_AMOUNT_PHASE)
        self.assertEqual(payload["rows_returned"], False)
        self.assertEqual(payload["documents_returned"], False)
        self.assertTrue(all(value is False for value in payload["no_effect"].values()))
        self.assertFalse(payload["policy"]["identifiers_enabled"])
        self.assertFalse(payload["policy"]["native_navigation_enabled"])
        self.assertFalse(payload["policy"]["external_output_enabled"])
        self.assertFalse(payload["policy"]["execution_enabled"])
        self.assertFalse(payload["policy"]["payment_terms_supported"])
        self.assertEqual(payload["policy"]["payment_terms_detection"], "payment_ledger_multiple_due_dates_only")
        self.assertEqual(payload["policy"]["payment_schedule_rows_read"], False)
        self.assertEqual(payload["policy"]["aging_date_basis"], "due_date_only")
        self.assertEqual(payload["policy"]["posting_date_fallback_enabled"], False)
        self.assertEqual(payload["policy"]["split_receivable_accounts_supported"], False)
        self.assertNotIn("rows", payload)
        self.assertNotIn("documents", payload)
        self.assertNotIn("metrics", payload)
        for leaked in ("SINV-", "CUST-", "Debtors -", "PE-", "JE-"):
            self.assertNotIn(leaked, repr(payload), leaked)

    def assert_invalid_source_response(self, payload):
        self.assert_safe_amount_response(payload)
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["policy"]["reason"], service.RECEIVABLES_AMOUNT_SOURCE_INVALID_REASON)
        self.assertEqual(payload["bucket_counts"], {})
        self.assertEqual(payload["bucket_amounts"], {})
        self.assertEqual(payload["suppressed_buckets"], {})
        self.assertNotIn("grand_total", payload)
        self.assertFalse(payload["amounts_are_aggregate"])
        self.assertFalse(payload["runtime_payment_ledger_amount_summary_enabled"])
        self.assertIsNone(payload["company_scope"])

    def test_manager_ready_returns_aggregate_mmk_bucket_amounts_only(self):
        records = [
            _invoice("SINV-CUR-1", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-CUR-2", "CUST-002", 200, date(2026, 7, 7), posting_date=date(2026, 7, 6)),
            _invoice("SINV-CUR-3", "CUST-003", 300, date(2026, 7, 8), posting_date=date(2026, 7, 6)),
            _invoice("SINV-30-1", "CUST-004", 10, date(2026, 6, 20)),
            _invoice("SINV-30-2", "CUST-005", 20, date(2026, 6, 21)),
            _invoice("SINV-30-3", "CUST-006", 30, date(2026, 6, 22)),
        ]
        calls = []
        payload = _safe_summary(records, calls=calls)

        self.assert_safe_amount_response(payload)
        self.assertEqual(payload["state"], "ready")
        self.assertEqual(payload["currency"], "MMK")
        self.assertEqual(payload["company_scope"], _COMPANY_SCOPE)
        self.assertEqual(payload["bucket_counts"], {
            "current": 3,
            "overdue_1_30": 3,
            "overdue_31_60": 0,
            "overdue_61_90": 0,
            "overdue_over_90": 0,
        })
        self.assertEqual(payload["bucket_amounts"], {
            "current": 600.0,
            "overdue_1_30": 60.0,
            "overdue_31_60": 0.0,
            "overdue_61_90": 0.0,
            "overdue_over_90": 0.0,
        })
        self.assertEqual(payload["suppressed_buckets"], {})
        self.assertEqual(payload["grand_total"], 660.0)
        self.assertEqual(payload["amounts_are_aggregate"], True)
        self.assertEqual(payload["runtime_payment_ledger_amount_summary_enabled"], True)
        self.assertEqual(len(calls), 1)
        doctype, kwargs = calls[0]
        self.assertEqual(doctype, service.RECEIVABLES_AMOUNT_SOURCE)
        self.assertEqual(kwargs["limit_start"], 0)
        self.assertEqual(kwargs["limit_page_length"], service.RECEIVABLES_AMOUNT_SOURCE_PAGE_SIZE)
        self.assertNotEqual(kwargs["limit_page_length"], 0)
        self.assertNotIn("ignore_permissions", kwargs)

    def test_multi_page_source_read_works_below_cap(self):
        records = [
            _invoice("SINV-PAGE-1", "CUST-001", 10, date(2026, 7, 6)),
            _invoice("SINV-PAGE-2", "CUST-002", 20, date(2026, 7, 6)),
            _invoice("SINV-PAGE-3", "CUST-003", 30, date(2026, 7, 6)),
            _invoice("SINV-PAGE-4", "CUST-004", 40, date(2026, 7, 6)),
            _invoice("SINV-PAGE-5", "CUST-005", 50, date(2026, 7, 6)),
            _invoice("SINV-PAGE-6", "CUST-006", 60, date(2026, 7, 6)),
        ]
        calls = []
        with patch.object(service, "RECEIVABLES_AMOUNT_SOURCE_PAGE_SIZE", 2), patch.object(
            service,
            "RECEIVABLES_AMOUNT_SOURCE_MAX_ROWS",
            10,
        ):
            payload = _safe_summary(records, calls=calls)

        self.assert_safe_amount_response(payload)
        self.assertEqual(payload["state"], "ready")
        self.assertEqual(payload["bucket_counts"]["current"], 6)
        self.assertEqual(payload["bucket_amounts"]["current"], 210.0)
        self.assertEqual(payload["grand_total"], 210.0)
        self.assertEqual([kwargs["limit_start"] for _doctype, kwargs in calls], [0, 2, 4, 6])
        self.assertTrue(all(kwargs["limit_page_length"] == 2 for _doctype, kwargs in calls))

    def test_exact_source_cap_succeeds_without_suppression_or_partial_failure(self):
        records = [
            _invoice("SINV-EXACT-1", "CUST-001", 10, date(2026, 7, 6)),
            _invoice("SINV-EXACT-2", "CUST-002", 20, date(2026, 7, 6)),
            _invoice("SINV-EXACT-3", "CUST-003", 30, date(2026, 7, 6)),
        ]
        calls = []
        with patch.object(service, "RECEIVABLES_AMOUNT_SOURCE_PAGE_SIZE", 2), patch.object(
            service,
            "RECEIVABLES_AMOUNT_SOURCE_MAX_ROWS",
            3,
        ):
            payload = _safe_summary(records, calls=calls)

        self.assert_safe_amount_response(payload)
        self.assertEqual(payload["state"], "ready")
        self.assertEqual(payload["bucket_counts"]["current"], 3)
        self.assertEqual(payload["bucket_amounts"]["current"], 60.0)
        self.assertEqual(payload["grand_total"], 60.0)
        self.assertEqual([kwargs["limit_start"] for _doctype, kwargs in calls], [0, 2])

    def test_source_exceeding_max_rows_fails_closed_without_partial_amounts(self):
        records = [
            _invoice("SINV-CAP-1", "CUST-001", 10, date(2026, 7, 6)),
            _invoice("SINV-CAP-2", "CUST-002", 20, date(2026, 7, 6)),
            _invoice("SINV-CAP-3", "CUST-003", 30, date(2026, 7, 6)),
            _invoice("SINV-CAP-4", "CUST-004", 40, date(2026, 7, 6)),
        ]
        calls = []
        with patch.object(service, "RECEIVABLES_AMOUNT_SOURCE_PAGE_SIZE", 2), patch.object(
            service,
            "RECEIVABLES_AMOUNT_SOURCE_MAX_ROWS",
            3,
        ):
            payload = _safe_summary(records, calls=calls)

        self.assert_safe_amount_response(payload)
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["policy"]["reason"], service.RECEIVABLES_AMOUNT_SOURCE_TOO_LARGE_REASON)
        self.assertEqual(payload["bucket_counts"], {})
        self.assertEqual(payload["bucket_amounts"], {})
        self.assertEqual(payload["suppressed_buckets"], {})
        self.assertNotIn("grand_total", payload)
        self.assertFalse(payload["amounts_are_aggregate"])
        self.assertFalse(payload["runtime_payment_ledger_amount_summary_enabled"])
        self.assertIsNone(payload["company_scope"])
        self.assertEqual([kwargs["limit_start"] for _doctype, kwargs in calls], [0, 2])
        self.assertNotIn("SINV-CAP", repr(payload))
        self.assertNotIn("CUST-", repr(payload))

    def test_non_mapping_payment_ledger_source_row_fails_closed_without_partial_amounts(self):
        def invalid_getter(doctype, **kwargs):
            return ["invalid-payment-ledger-row"]

        payload = service.build_receivables_payment_ledger_amount_summary(
            context=_context(),
            resolver=_resolver(),
            as_of_date="2026-07-06",
            permission_checker=_permission_checker(True),
            metadata_provider=_metadata_provider(),
            list_getter=invalid_getter,
        )

        self.assert_invalid_source_response(payload)
        self.assertNotIn("invalid-payment-ledger-row", repr(payload))

    def test_missing_required_payment_ledger_fields_fail_closed_without_partial_amounts(self):
        required_field_mutations = {
            "company": "",
            "account": "",
            "account_type": "",
            "party_type": "",
            "party": "",
            "voucher_type": "",
            "voucher_no": "",
            "amount": None,
            "amount_in_account_currency": "not-a-number",
            "posting_date": "not-a-date",
            "account_currency": "",
            "delinked": None,
        }
        for field, value in required_field_mutations.items():
            with self.subTest(field=field):
                records = [
                    _invoice("SINV-BAD-1", "CUST-001", 100, date(2026, 7, 6)),
                    _invoice("SINV-BAD-2", "CUST-002", 200, date(2026, 7, 6)),
                    _invoice("SINV-BAD-3", "CUST-003", 300, date(2026, 7, 6)),
                ]
                records[1][field] = value
                payload = _direct_summary(records)

                self.assert_invalid_source_response(payload)
                self.assertNotIn("SINV-BAD", repr(payload))
                self.assertNotIn("CUST-", repr(payload))

    def test_mismatched_payment_ledger_company_fails_closed_without_partial_amounts(self):
        records = [
            _invoice("SINV-COMPANY-1", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-COMPANY-2", "CUST-002", 200, date(2026, 7, 6), company="Other Company"),
            _invoice("SINV-COMPANY-3", "CUST-003", 300, date(2026, 7, 6)),
        ]
        payload = _direct_summary(records)

        self.assert_invalid_source_response(payload)
        self.assertNotIn("SINV-COMPANY", repr(payload))
        self.assertNotIn("CUST-", repr(payload))
        self.assertNotIn("Other Company", repr(payload))

    def test_mismatched_delinked_payment_ledger_company_fails_closed_before_skip(self):
        records = [
            _invoice("SINV-DELINK-1", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-DELINK-2", "CUST-002", 200, date(2026, 7, 6), company="Other Company"),
            _invoice("SINV-DELINK-3", "CUST-003", 300, date(2026, 7, 6)),
        ]
        records[1]["delinked"] = 1
        payload = _direct_summary(records)

        self.assert_invalid_source_response(payload)
        self.assertNotIn("SINV-DELINK", repr(payload))
        self.assertNotIn("CUST-", repr(payload))
        self.assertNotIn("Other Company", repr(payload))

    def test_absent_required_payment_ledger_fields_fail_closed_without_partial_amounts(self):
        required_fields = (
            "company",
            "account",
            "account_type",
            "party_type",
            "party",
            "voucher_type",
            "voucher_no",
            "amount",
            "amount_in_account_currency",
            "posting_date",
            "account_currency",
            "delinked",
        )
        for field in required_fields:
            with self.subTest(field=field):
                records = [
                    _invoice("SINV-ABSENT-1", "CUST-001", 100, date(2026, 7, 6)),
                    _invoice("SINV-ABSENT-2", "CUST-002", 200, date(2026, 7, 6)),
                    _invoice("SINV-ABSENT-3", "CUST-003", 300, date(2026, 7, 6)),
                ]
                records[1].pop(field)
                payload = _direct_summary(records)

                self.assert_invalid_source_response(payload)
                self.assertNotIn("SINV-ABSENT", repr(payload))
                self.assertNotIn("CUST-", repr(payload))

    def test_missing_against_voucher_linkage_fields_fail_closed_without_partial_amounts(self):
        cases = [
            ("invoice", "against_voucher_type"),
            ("invoice", "against_voucher_no"),
            ("allocation", "against_voucher_type"),
            ("allocation", "against_voucher_no"),
        ]
        for row_kind, field in cases:
            with self.subTest(row_kind=row_kind, field=field):
                records = [
                    _invoice("SINV-LINK-1", "CUST-001", 100, date(2026, 7, 6)),
                    _invoice("SINV-LINK-2", "CUST-002", 200, date(2026, 7, 6)),
                    _invoice("SINV-LINK-3", "CUST-003", 300, date(2026, 7, 6)),
                ]
                if row_kind == "allocation":
                    records.append(_payment("PE-LINK", "SINV-LINK-1", "CUST-001", 10, date(2026, 7, 6)))
                    records[-1][field] = ""
                else:
                    records[0][field] = ""
                payload = _direct_summary(records)

                self.assert_invalid_source_response(payload)
                self.assertNotIn("SINV-LINK", repr(payload))
                self.assertNotIn("PE-LINK", repr(payload))
                self.assertNotIn("CUST-", repr(payload))

    def test_allocations_and_credit_rows_reduce_voucher_outstanding(self):
        records = [
            _invoice("SINV-PE", "CUST-001", 1000, date(2026, 7, 6)),
            _payment("PE-001", "SINV-PE", "CUST-001", 250, date(2026, 7, 6)),
            _invoice("SINV-JE", "CUST-002", 500, date(2026, 7, 6)),
            _journal("JE-001", "SINV-JE", "CUST-002", 100, date(2026, 7, 6)),
            _invoice("SINV-CR", "CUST-003", 600, date(2026, 7, 6)),
            _credit_invoice("SINV-CREDIT-001", "SINV-CR", "CUST-003", 50, date(2026, 7, 6)),
        ]
        payload = _safe_summary(records)

        self.assert_safe_amount_response(payload)
        self.assertEqual(payload["state"], "ready")
        self.assertEqual(payload["bucket_counts"]["current"], 3)
        self.assertEqual(payload["bucket_amounts"]["current"], 1700.0)
        self.assertEqual(payload["grand_total"], 1700.0)

    def test_future_dated_allocations_are_ignored_until_as_of_date(self):
        records = [
            _invoice("SINV-FUT-1", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-FUT-2", "CUST-002", 100, date(2026, 7, 6)),
            _invoice("SINV-FUT-3", "CUST-003", 100, date(2026, 7, 6)),
            _payment("PE-FUTURE", "SINV-FUT-1", "CUST-001", 100, date(2026, 7, 7)),
        ]
        payload = _safe_summary(records)

        self.assert_safe_amount_response(payload)
        self.assertEqual(payload["bucket_counts"]["current"], 3)
        self.assertEqual(payload["bucket_amounts"]["current"], 300.0)

    def test_zero_and_negative_outstanding_vouchers_are_excluded(self):
        records = [
            _invoice("SINV-ZERO", "CUST-001", 100, date(2026, 7, 6)),
            _payment("PE-ZERO", "SINV-ZERO", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-NEG", "CUST-002", 200, date(2026, 7, 6)),
            _payment("PE-NEG", "SINV-NEG", "CUST-002", 250, date(2026, 7, 6)),
            _invoice("SINV-POS-1", "CUST-003", 50, date(2026, 7, 6)),
            _invoice("SINV-POS-2", "CUST-004", 60, date(2026, 7, 6)),
            _invoice("SINV-POS-3", "CUST-005", 70, date(2026, 7, 6)),
        ]
        payload = _safe_summary(records)

        self.assert_safe_amount_response(payload)
        self.assertEqual(payload["bucket_counts"]["current"], 3)
        self.assertEqual(payload["bucket_amounts"]["current"], 180.0)
        self.assertEqual(payload["grand_total"], 180.0)

    def test_missing_due_date_returns_unavailable_without_posting_date_fallback(self):
        records = [
            _invoice("SINV-NODUE-1", "CUST-001", 10, None, posting_date=date(2026, 5, 1)),
            _invoice("SINV-NODUE-2", "CUST-002", 20, None, posting_date=date(2026, 5, 1)),
            _invoice("SINV-NODUE-3", "CUST-003", 30, None, posting_date=date(2026, 5, 1)),
        ]
        payload = _safe_summary(records)

        self.assert_safe_amount_response(payload)
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["policy"]["reason"], "missing_due_date_policy_not_ready")
        self.assertEqual(payload["bucket_counts"], {})
        self.assertEqual(payload["bucket_amounts"], {})
        self.assertNotIn("grand_total", payload)
        self.assertFalse(payload["runtime_payment_ledger_amount_summary_enabled"])
        self.assertNotIn("SINV-NODUE", repr(payload))
        self.assertNotIn("CUST-", repr(payload))

    def test_multiple_due_dates_for_same_voucher_returns_unavailable(self):
        records = [
            _invoice("SINV-TERMS", "CUST-001", 50, date(2026, 7, 1)),
            _invoice("SINV-TERMS", "CUST-001", 50, date(2026, 7, 2)),
        ]
        payload = _safe_summary(records)

        self.assert_safe_amount_response(payload)
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["policy"]["reason"], "payment_terms_not_supported")
        self.assertEqual(payload["bucket_amounts"], {})
        self.assertNotIn("grand_total", payload)

    def test_same_sales_invoice_across_receivable_accounts_fails_closed_without_account_leakage(self):
        records = [
            _invoice("SINV-SPLIT-1", "CUST-001", 100, date(2026, 7, 6), account="Debtors - MMD"),
            _invoice("SINV-SPLIT-1", "CUST-001", 200, date(2026, 7, 6), account="Installment Debtors - MMD"),
        ]
        payload = _safe_summary(records)

        self.assert_safe_amount_response(payload)
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["policy"]["reason"], "split_receivable_account_not_supported")
        self.assertEqual(payload["bucket_counts"], {})
        self.assertEqual(payload["bucket_amounts"], {})
        self.assertNotIn("grand_total", payload)
        self.assertNotIn("Debtors", repr(payload))
        self.assertNotIn("SINV-SPLIT", repr(payload))
        self.assertNotIn("CUST-", repr(payload))

    def test_allocation_across_receivable_accounts_fails_closed_without_account_leakage(self):
        records = [
            _invoice("SINV-ALLOC-SPLIT", "CUST-001", 300, date(2026, 7, 6), account="Debtors - MMD"),
            _payment(
                "PE-ALLOC-SPLIT",
                "SINV-ALLOC-SPLIT",
                "CUST-001",
                100,
                date(2026, 7, 6),
                account="Installment Debtors - MMD",
            ),
        ]
        payload = _safe_summary(records)

        self.assert_safe_amount_response(payload)
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["policy"]["reason"], "split_receivable_account_not_supported")
        self.assertEqual(payload["bucket_counts"], {})
        self.assertEqual(payload["bucket_amounts"], {})
        self.assertNotIn("grand_total", payload)
        self.assertNotIn("Debtors", repr(payload))
        self.assertNotIn("SINV-ALLOC", repr(payload))
        self.assertNotIn("PE-ALLOC", repr(payload))
        self.assertNotIn("CUST-", repr(payload))

    def test_payment_terms_required_stops_before_adapter(self):
        payload = service.build_receivables_payment_ledger_amount_summary(
            context=_context(),
            resolver=_resolver(),
            as_of_date="2026-07-06",
            permission_checker=_raising_permission,
            metadata_provider=_raising_metadata,
            list_getter=_raising_getter,
            payment_terms_required=True,
        )

        self.assert_safe_amount_response(payload)
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["policy"]["reason"], "payment_terms_not_supported")
        self.assertEqual(payload["runtime_payment_ledger_amount_summary_enabled"], False)
        self.assertEqual(payload["policy"]["payment_terms_detection"], "payment_ledger_multiple_due_dates_only")
        self.assertEqual(payload["policy"]["payment_schedule_rows_read"], False)

    def test_low_voucher_count_suppresses_amount_and_omits_grand_total(self):
        records = [
            _invoice("SINV-LOW-1", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-LOW-2", "CUST-002", 100, date(2026, 7, 6)),
        ]
        payload = _safe_summary(records)

        self.assert_safe_amount_response(payload)
        self.assertEqual(payload["state"], "ready")
        self.assertEqual(payload["bucket_counts"]["current"], 2)
        self.assertNotIn("current", payload["bucket_amounts"])
        self.assertEqual(payload["suppressed_buckets"]["current"], {"suppressed": True, "reason": "suppressed_low_population"})
        self.assertNotIn("grand_total", payload)

    def test_low_distinct_customer_count_suppresses_amount_and_omits_grand_total(self):
        records = [
            _invoice("SINV-DIV-1", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-DIV-2", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-DIV-3", "CUST-001", 100, date(2026, 7, 6)),
        ]
        payload = _safe_summary(records)

        self.assert_safe_amount_response(payload)
        self.assertEqual(payload["state"], "ready")
        self.assertEqual(payload["bucket_counts"]["current"], 3)
        self.assertNotIn("current", payload["bucket_amounts"])
        self.assertEqual(payload["suppressed_buckets"]["current"]["reason"], "suppressed_low_population")
        self.assertNotIn("grand_total", payload)

    def test_denied_roles_and_unscoped_resolvers_do_not_call_permission_or_adapter(self):
        cases = [
            (_resolver(role_category="normal_finance"), "accounts_manager_required"),
            (_resolver(role_category="audit_candidate"), "accounts_manager_required"),
            (_resolver(role_category="system_admin_only"), "accounts_manager_required"),
            (_resolver(state="restricted", selected_company=None, reason="finance_role_required"), "finance_role_required"),
            (_resolver(state="selection_required", selected_company=None, reason="multiple_company_permissions_require_selection"), "multiple_company_permissions_require_selection"),
        ]
        for resolver, reason in cases:
            with self.subTest(reason=reason):
                payload = service.build_receivables_payment_ledger_amount_summary(
                    context=_context(),
                    resolver=resolver,
                    as_of_date="2026-07-06",
                    permission_checker=_raising_permission,
                    metadata_provider=_raising_metadata,
                    list_getter=_raising_getter,
                )
                self.assert_safe_amount_response(payload)
                self.assertEqual(payload["state"], "unavailable")
                self.assertEqual(payload["policy"]["reason"], reason)
                self.assertEqual(payload["bucket_counts"], {})
                self.assertEqual(payload["bucket_amounts"], {})

    def test_company_currency_browser_and_source_gates_stop_before_adapter(self):
        wrong_company = {"name": _COMPANY_SCOPE["name"], "label": _COMPANY_SCOPE["label"], "currency": "USD"}
        cases = [
            {
                "resolver": _resolver(),
                "browser_filters": {"company": _COMPANY_SCOPE["name"]},
                "permission_checker": _raising_permission,
                "metadata_provider": _raising_metadata,
                "reason": "browser_filters_not_allowed",
            },
            {
                "resolver": _resolver(selected_company=wrong_company),
                "permission_checker": _raising_permission,
                "metadata_provider": _raising_metadata,
                "reason": "approved_company_currency_required",
            },
            {
                "resolver": _resolver(),
                "permission_checker": _permission_checker(False),
                "metadata_provider": _raising_metadata,
                "reason": "source_permission_denied",
            },
            {
                "resolver": _resolver(),
                "permission_checker": _permission_checker(True),
                "metadata_provider": _metadata_provider(amount_options="Currency"),
                "reason": "source_metadata_drift",
            },
        ]
        for case in cases:
            with self.subTest(reason=case["reason"]):
                payload = service.build_receivables_payment_ledger_amount_summary(
                    context=_context(),
                    resolver=case["resolver"],
                    as_of_date="2026-07-06",
                    permission_checker=case["permission_checker"],
                    metadata_provider=case["metadata_provider"],
                    list_getter=_raising_getter,
                    browser_filters=case.get("browser_filters"),
                )
                self.assert_safe_amount_response(payload)
                self.assertEqual(payload["state"], "unavailable")
                self.assertEqual(payload["policy"]["reason"], case["reason"])

    def test_overview_integrates_ready_amount_summary_without_rows(self):
        records = [
            _invoice("SINV-OV-1", "CUST-001", 100, date(2026, 7, 6), posting_date=date(2026, 7, 4)),
            _invoice("SINV-OV-2", "CUST-002", 200, date(2026, 7, 6), posting_date=date(2026, 7, 4)),
            _invoice("SINV-OV-3", "CUST-003", 300, date(2026, 7, 6), posting_date=date(2026, 7, 4)),
        ]
        with patch.object(service.frappe, "get_roles", return_value=["Accounts Manager"]), patch.object(
            service,
            "resolve_finance_role_company_scope",
            return_value=_resolver(),
        ), patch.object(
            service,
            "verify_receivables_source_permission",
            return_value={
                "source": service.RECEIVABLES_COUNT_SOURCE,
                "source_permission_checked": True,
                "source_permission_verified": True,
                "reason": "source_permission_allowed",
            },
        ), patch.object(
            service,
            "_permission_preserving_receivables_count",
            side_effect=_overview_count_stub,
        ), patch.object(
            service,
            "verify_receivables_amount_source_permission",
            return_value={
                "source": service.RECEIVABLES_AMOUNT_SOURCE,
                "source_permission_checked": True,
                "source_permission_verified": True,
                "reason": "source_permission_allowed",
            },
        ), patch.object(
            service,
            "verify_receivables_amount_source_metadata",
            return_value={
                "source": service.RECEIVABLES_AMOUNT_SOURCE,
                "source_metadata_checked": True,
                "source_metadata_verified": True,
                "reason": "source_metadata_verified",
                "company_currency_amount_field": True,
            },
        ), patch.object(
            service,
            "_permission_preserving_payment_ledger_rows",
            return_value=records,
        ):
            payload = service.get_finance_control_desk_overview_context()

        self.assertEqual(payload["scope"]["receivables_amount_summary_enabled"], True)
        self.assertEqual(payload["scope"]["monetary_values_enabled"], True)
        self.assertEqual(payload["receivables_amount_summary"]["policy"]["aging_date_basis"], "due_date_only")
        self.assertEqual(payload["receivables_amount_summary"]["policy"]["posting_date_fallback_enabled"], False)
        self.assertEqual(payload["receivables_amount_summary"]["state"], "ready")
        self.assertEqual(payload["receivables_amount_summary"]["bucket_amounts"]["current"], 600.0)
        self.assertEqual(payload["amounts"], [])
        self.assertEqual(payload["rows"], [])
        self.assertEqual(payload["documents"], [])
        self.assertTrue(all(card["rows"] == [] for card in payload["posture_cards"]))
        receivables_card = next(card for card in payload["posture_cards"] if card["key"] == "receivables_posture")
        self.assertIn("Sales Invoice aggregate count buckets", receivables_card["detail"])
        self.assertIn("manager-only Payment Ledger MMK amount buckets", receivables_card["detail"])
        self.assertIn("No row-level customer, invoice, voucher, account, Payment Ledger, route, report, export, or action detail is returned, shown, linked, exported, or actionable.", receivables_card["detail"])
        self.assertIn("Current / not due: 600.0 MMK", receivables_card["detail"])
        self.assertNotIn("SINV-", repr(payload["receivables_amount_summary"]))
        self.assertNotIn("CUST-", repr(payload["receivables_amount_summary"]))

    def test_overview_amount_ready_count_unavailable_copy_does_not_deny_amounts(self):
        records = [
            _invoice("SINV-AMT-1", "CUST-001", 100, date(2026, 7, 6), posting_date=date(2026, 7, 4)),
            _invoice("SINV-AMT-2", "CUST-002", 200, date(2026, 7, 6), posting_date=date(2026, 7, 4)),
            _invoice("SINV-AMT-3", "CUST-003", 300, date(2026, 7, 6), posting_date=date(2026, 7, 4)),
        ]
        with patch.object(service.frappe, "get_roles", return_value=["Accounts Manager"]), patch.object(
            service,
            "resolve_finance_role_company_scope",
            return_value=_resolver(),
        ), patch.object(
            service,
            "verify_receivables_source_permission",
            return_value={
                "source": service.RECEIVABLES_COUNT_SOURCE,
                "source_permission_checked": True,
                "source_permission_verified": False,
                "reason": "source_permission_denied",
            },
        ), patch.object(
            service,
            "_permission_preserving_receivables_count",
            side_effect=AssertionError("count query should not run"),
        ), patch.object(
            service,
            "verify_receivables_amount_source_permission",
            return_value={
                "source": service.RECEIVABLES_AMOUNT_SOURCE,
                "source_permission_checked": True,
                "source_permission_verified": True,
                "reason": "source_permission_allowed",
            },
        ), patch.object(
            service,
            "verify_receivables_amount_source_metadata",
            return_value={
                "source": service.RECEIVABLES_AMOUNT_SOURCE,
                "source_metadata_checked": True,
                "source_metadata_verified": True,
                "reason": "source_metadata_verified",
                "company_currency_amount_field": True,
            },
        ), patch.object(
            service,
            "_permission_preserving_payment_ledger_rows",
            return_value=records,
        ):
            payload = service.get_finance_control_desk_overview_context()

        self.assertEqual(payload["scope"]["receivables_count_posture_enabled"], False)
        self.assertEqual(payload["scope"]["receivables_amount_summary_enabled"], True)
        receivables_card = next(card for card in payload["posture_cards"] if card["key"] == "receivables_posture")
        self.assertIn("Sales Invoice count buckets are unavailable", receivables_card["detail"])
        self.assertIn("Manager-only Payment Ledger MMK amount buckets are available", receivables_card["detail"])
        self.assertIn("No row-level customer, invoice, voucher, account, Payment Ledger, route, report, export, or action detail is returned, shown, linked, exported, or actionable.", receivables_card["detail"])
        self.assertIn("Current / not due: 600.0 MMK", receivables_card["detail"])
        self.assertNotIn("No rows or amounts are loaded", receivables_card["detail"])
        self.assertEqual(receivables_card["value"], "MMK buckets only")
        self.assertEqual(payload["rows"], [])
        self.assertEqual(payload["documents"], [])
        self.assertNotIn("SINV-AMT", repr(payload["receivables_amount_summary"]))
        self.assertNotIn("CUST-", repr(payload["receivables_amount_summary"]))

    def test_service_source_uses_safe_payment_ledger_adapter_contract(self):
        source = _SERVICE_SOURCE.read_text(encoding="utf-8")

        self.assertIn('getattr(frappe, "get_list", None)', source)
        self.assertIn('getattr(frappe, "has_permission", None)', source)
        self.assertIn('getattr(frappe, "get_meta", None)', source)
        self.assertIn("RECEIVABLES_AMOUNT_SOURCE_PAGE_SIZE", source)
        self.assertIn("RECEIVABLES_AMOUNT_SOURCE_MAX_ROWS", source)
        self.assertIn("RECEIVABLES_AMOUNT_SOURCE_TOO_LARGE_REASON", source)
        self.assertIn("RECEIVABLES_AMOUNT_SOURCE_INVALID_REASON", source)
        self.assertIn("row_company != company_name", source)
        self.assertIn("limit_start=limit_start", source)
        self.assertIn('"aging_date_basis": "due_date_only"', source)
        self.assertIn('"posting_date_fallback_enabled": False', source)
        self.assertIn('"split_receivable_accounts_supported": False', source)
        self.assertNotIn("limit_page_length=0", source)
        self.assertNotIn("min(posting_dates)", source)
        forbidden_patterns = [
            r"frappe\.get_all",
            r"frappe\.get_list\s*\(",
            r"frappe\.db\.sql",
            r"frappe\.get_doc\s*\(",
            r"ignore_permissions",
            r"query-report",
            r"/app/",
            r"/desk/Form",
            r"/desk/List",
            r"/desk/Report",
            r"\.save\(",
            r"\.submit\(",
            r"\.cancel\(",
            r"delete_doc",
            r"set_value",
            r"enqueue",
            r"sendmail",
            r"download\(",
            r"export_data",
        ]
        for pattern in forbidden_patterns:
            self.assertIsNone(re.search(pattern, source), pattern)


if __name__ == "__main__":
    unittest.main()
