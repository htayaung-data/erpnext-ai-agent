from __future__ import annotations

import re
import sys
import types
import unittest
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
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
    frappe_stub.get_system_settings = lambda key: "Banker's Rounding"
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



def _currency_contract(precision=2, rounding_method="Banker's Rounding"):
    return {
        "currency": "MMK",
        "precision": precision,
        "precision_source": "erpnext.accounts.utils.get_currency_precision",
        "number_format": "#,###.##" if precision == 2 else "#,###.###",
        "rounding_method": rounding_method,
        "rounding_mode": service.ROUND_HALF_EVEN if rounding_method == "Banker's Rounding" else service.ROUND_HALF_UP,
        "decimal_serialization": "fixed_string",
        "verified": True,
    }

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


def _future_activity_getter(records, response=None):
    def getter(doctype, **kwargs):
        if doctype != service.RECEIVABLES_AMOUNT_SOURCE:
            raise AssertionError(f"Unexpected future activity source: {doctype!r}")
        if kwargs.get("fields") != [service.RECEIVABLES_COUNT_QUERY_FIELD]:
            raise AssertionError("Future activity gate must use aggregate count syntax")
        if response is not None:
            return response
        future_count = 0
        for record in records:
            if not isinstance(record, dict):
                continue
            try:
                posting_date = _as_date(record.get("posting_date"))
            except (TypeError, ValueError):
                continue
            if posting_date is not None and posting_date > date.fromisoformat("2026-07-06"):
                future_count += 1
        return [{"count": future_count}]

    return getter


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
        self_order = kwargs.get("order_by")
        if self_order != "name asc":
            raise AssertionError("Payment Ledger pagination requires unique name ordering")
        for forbidden in ("ignore_permissions", "as_list", "pluck"):
            if forbidden in kwargs:
                raise AssertionError(f"Forbidden Payment Ledger query option: {forbidden}")
        filters = kwargs.get("filters")
        or_filters = kwargs.get("or_filters")
        if or_filters is None:
            expected_filters = [
                ["company", "=", _COMPANY_SCOPE["name"]],
                ["account_type", "=", "Receivable"],
                ["party_type", "=", "Customer"],
                ["delinked", "=", 0],
            ]
            if any(expected not in (filters or []) for expected in expected_filters):
                raise AssertionError("Primary Payment Ledger read is not selected-company Receivable/Customer scoped")
            if not any(item[:2] == ["posting_date", "<="] for item in (filters or [])):
                raise AssertionError("Primary Payment Ledger read is not as-of scoped")
            matched = [dict(record) for record in records if all(_matches_filter(record, item) for item in filters)]
        else:
            if filters not in ([], None) or len(or_filters) != 2:
                raise AssertionError("Payment Ledger anomaly probe shape drifted")
            invoice_names = list(or_filters[0][2])
            expected_or_filters = [
                ["against_voucher_no", "in", invoice_names],
                ["voucher_no", "in", invoice_names],
            ]
            if or_filters != expected_or_filters:
                raise AssertionError("Payment Ledger anomaly probe must bind reference and basis identities")
            matched = [
                dict(record)
                for record in records
                if record.get("voucher_no") in invoice_names or record.get("against_voucher_no") in invoice_names
            ]
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
    voucher_detail_no=None,
    row_name=None,
):
    resolved_against_no = against_voucher_no if against_voucher_no is not None else voucher_no
    generated_name = f"PLE|{voucher_type}|{voucher_no}|{resolved_against_no}|{posting_date}|{due_date}|{amount}|{account}|{voucher_detail_no}"
    return {
        "name": row_name or generated_name,
        "company": company or _COMPANY_SCOPE["name"],
        "account": account,
        "account_type": account_type,
        "party_type": party_type,
        "party": party,
        "voucher_type": voucher_type,
        "voucher_no": voucher_no,
        "voucher_detail_no": voucher_detail_no,
        "against_voucher_type": against_voucher_type,
        "against_voucher_no": resolved_against_no,
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
    row = _ple(
        voucher_type="Sales Invoice",
        voucher_no=name,
        party=party,
        amount=-abs(amount),
        posting_date=posting_date,
        due_date=posting_date,
        against_voucher_type="Sales Invoice",
        against_voucher_no=name,
    )
    row["_test_is_return"] = True
    row["_test_return_against"] = against_invoice
    return row


def _sales_invoice_identity_rows(records):
    outstanding = {}
    basis = {}
    for row in records:
        if not isinstance(row, dict):
            continue
        try:
            key = (
                str(row["account"]),
                str(row["against_voucher_type"]),
                str(row["against_voucher_no"]),
                str(row["party_type"]),
                str(row["party"]),
            )
            outstanding[key] = outstanding.get(key, Decimal("0")) + Decimal(str(row["amount"]))
            if (
                row.get("voucher_type") == "Sales Invoice"
                and row.get("voucher_no") == row.get("against_voucher_no")
                and Decimal(str(row.get("amount"))) > 0
            ):
                basis.setdefault(key, dict(row))
        except (KeyError, InvalidOperation, TypeError, ValueError):
            continue

    result = []
    seen_names = set()
    for key, row in basis.items():
        if outstanding.get(key, Decimal("0")) <= 0:
            continue
        invoice_name = str(row.get("voucher_no") or "")
        if not invoice_name or invoice_name in seen_names:
            continue
        seen_names.add(invoice_name)
        result.append({
            "name": invoice_name,
            "company": row.get("company"),
            "customer": row.get("party"),
            "debit_to": row.get("account"),
            "posting_date": row.get("posting_date"),
            "due_date": row.get("due_date"),
            "docstatus": 1,
            "is_return": 0,
            "return_against": None,
        })
    return sorted(result, key=lambda row: row["name"])


def _sales_invoice_identity_getter(records, calls=None):
    source_rows = _sales_invoice_identity_rows(records)

    def getter(doctype, **kwargs):
        if calls is not None:
            calls.append((doctype, kwargs))
        if doctype != service.RECEIVABLES_COUNT_SOURCE:
            raise AssertionError(f"Unexpected identity source: {doctype!r}")
        if kwargs.get("fields") == [service.RECEIVABLES_COUNT_QUERY_FIELD]:
            filters = kwargs.get("filters") or []
            for expected in (
                ["company", "=", _COMPANY_SCOPE["name"]],
                ["docstatus", "=", 1],
                ["is_return", "=", 1],
            ):
                if expected not in filters:
                    raise AssertionError(f"Missing Sales Invoice return filter: {expected!r}")
            if not any(item[:2] == ["posting_date", "<="] for item in filters):
                raise AssertionError("Missing return as-of filter")
            return_count = sum(
                1 for row in records
                if isinstance(row, dict)
                and row.get("voucher_type") == "Sales Invoice"
                and row.get("_test_is_return") is True
                and Decimal(str(row.get("amount") or 0)) < 0
            )
            return [{"count": return_count}]
        if kwargs.get("fields") != list(service.RECEIVABLES_IDENTITY_SOURCE_FIELDS):
            raise AssertionError("Sales Invoice identity fields drifted")
        if kwargs.get("order_by") != "name asc":
            raise AssertionError("Sales Invoice identity pagination requires name ordering")
        page_size = kwargs.get("limit_page_length")
        limit_start = kwargs.get("limit_start")
        if not isinstance(page_size, int) or page_size <= 0 or page_size > service.RECEIVABLES_IDENTITY_SOURCE_PAGE_SIZE:
            raise AssertionError("Sales Invoice identity read must be bounded")
        if not isinstance(limit_start, int) or limit_start < 0:
            raise AssertionError("Sales Invoice identity read must paginate")
        for forbidden in ("ignore_permissions", "as_list", "pluck"):
            if forbidden in kwargs:
                raise AssertionError(f"Forbidden Sales Invoice identity option: {forbidden}")
        filters = kwargs.get("filters") or []
        for expected in (
            ["company", "=", _COMPANY_SCOPE["name"]],
            ["docstatus", "=", 1],
            ["outstanding_amount", ">", 0],
            ["is_return", "=", 0],
            ["return_against", "is", "not set"],
        ):
            if expected not in filters:
                raise AssertionError(f"Missing Sales Invoice identity filter: {expected!r}")
        return [dict(row) for row in source_rows[limit_start : limit_start + page_size]]

    return getter


def _safe_summary(records, **kwargs):
    calls = kwargs.pop("calls", None)
    invoice_identity_list_getter = kwargs.pop(
        "invoice_identity_list_getter", _sales_invoice_identity_getter(records)
    )
    return service.build_receivables_payment_ledger_amount_summary(
        context=_context(),
        resolver=_resolver(),
        as_of_date="2026-07-06",
        permission_checker=_permission_checker(True),
        metadata_provider=_metadata_provider(),
        currency_contract_provider=lambda currency: _currency_contract(),
        future_activity_list_getter=_future_activity_getter(records),
        list_getter=_payment_ledger_getter(records, calls=calls),
        invoice_identity_list_getter=invoice_identity_list_getter,
        **kwargs,
    )


def _direct_summary(records):
    return service.build_receivables_payment_ledger_amount_summary(
        context=_context(),
        resolver=_resolver(),
        as_of_date="2026-07-06",
        permission_checker=_permission_checker(True),
        metadata_provider=_metadata_provider(),
        currency_contract_provider=lambda currency: _currency_contract(),
        future_activity_list_getter=_future_activity_getter(records),
        list_getter=lambda doctype, **kwargs: records,
        invoice_identity_list_getter=_sales_invoice_identity_getter(records),
    )


def _overview_count_stub(filters, list_getter=None):
    if any(len(item) == 4 for item in filters):
        return 0
    terminal = filters[-1]
    if terminal[0:2] == ["due_date", ">="]:
        return 3
    if terminal[0:2] in (["due_date", "between"], ["due_date", "<="], ["due_date", "<"]):
        return 0
    if terminal[0:2] in (["posting_date", ">"], ["payment_terms_template", "is"], ["due_date", "is"]):
        return 0
    return 3


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
        self.assertEqual(payload["policy"]["payment_terms_detection"], "sales_invoice_schedule_gate_and_payment_ledger_due_date_consistency")
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
            "current": "600.00",
            "overdue_1_30": "60.00",
            "overdue_31_60": "0.00",
            "overdue_61_90": "0.00",
            "overdue_over_90": "0.00",
        })
        self.assertEqual(payload["suppressed_buckets"], {})
        self.assertEqual(payload["grand_total"], "660.00")
        self.assertEqual(payload["amounts_are_aggregate"], True)
        self.assertEqual(payload["runtime_payment_ledger_amount_summary_enabled"], True)
        self.assertEqual(len(calls), 2)
        doctype, kwargs = calls[0]
        self.assertEqual(doctype, service.RECEIVABLES_AMOUNT_SOURCE)
        self.assertEqual(kwargs["limit_start"], 0)
        self.assertEqual(kwargs["limit_page_length"], service.RECEIVABLES_AMOUNT_SOURCE_PAGE_SIZE)
        self.assertNotEqual(kwargs["limit_page_length"], 0)
        self.assertNotIn("ignore_permissions", kwargs)

    def test_each_voucher_is_rounded_before_bucket_aggregation(self):
        cases = (
            ("100.004", "300.00"),
            ("100.006", "300.03"),
        )
        for raw_amount, expected_total in cases:
            with self.subTest(raw_amount=raw_amount):
                records = [
                    _invoice(f"SINV-ROUND-{index}", f"CUST-{index:03d}", raw_amount, date(2026, 7, 6))
                    for index in range(1, 4)
                ]
                payload = _safe_summary(records)

                self.assert_safe_amount_response(payload)
                self.assertEqual(payload["state"], "ready")
                self.assertEqual(payload["bucket_counts"]["current"], 3)
                self.assertEqual(payload["bucket_amounts"]["current"], expected_total)
                self.assertEqual(payload["grand_total"], expected_total)

    def test_sub_precision_partial_payments_round_each_voucher_before_total(self):
        records = []
        for index in range(1, 4):
            invoice_name = f"SINV-PARTIAL-ROUND-{index}"
            party = f"CUST-{index:03d}"
            records.extend(
                (
                    _invoice(invoice_name, party, "200.004", date(2026, 7, 6)),
                    _payment(
                        f"PE-PARTIAL-ROUND-{index}",
                        invoice_name,
                        party,
                        service.Decimal("100.000"),
                        date(2026, 7, 6),
                    ),
                )
            )

        payload = _safe_summary(records)

        self.assert_safe_amount_response(payload)
        self.assertEqual(payload["state"], "ready")
        self.assertEqual(payload["bucket_counts"]["current"], 3)
        self.assertEqual(payload["bucket_amounts"]["current"], "300.00")
        self.assertEqual(payload["grand_total"], "300.00")

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
        self.assertEqual(payload["bucket_amounts"]["current"], "210.00")
        self.assertEqual(payload["grand_total"], "210.00")
        self.assertEqual([kwargs["limit_start"] for _doctype, kwargs in calls], [0, 2, 4, 6, 0, 2, 4, 6])
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
        self.assertEqual(payload["bucket_amounts"]["current"], "60.00")
        self.assertEqual(payload["grand_total"], "60.00")
        self.assertEqual([kwargs["limit_start"] for _doctype, kwargs in calls], [0, 2, 0, 2])

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
            currency_contract_provider=lambda currency: _currency_contract(),
            future_activity_list_getter=_future_activity_getter([]),
            list_getter=invalid_getter,
            invoice_identity_list_getter=lambda doctype, **kwargs: [{"count": 0}]
            if kwargs.get("fields") == [service.RECEIVABLES_COUNT_QUERY_FIELD] else [],
        )

        self.assert_invalid_source_response(payload)
        self.assertEqual(payload["policy"]["currency_precision_verified"], True)
        self.assertEqual(payload["policy"]["amount_serialization"], "unavailable")
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

    def test_non_finite_payment_ledger_amounts_fail_closed_without_partial_amounts(self):
        for value in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(value=value):
                records = [
                    _invoice("SINV-FINITE-1", "CUST-001", 100, date(2026, 7, 6)),
                    _invoice("SINV-FINITE-2", "CUST-002", value, date(2026, 7, 6)),
                    _invoice("SINV-FINITE-3", "CUST-003", 300, date(2026, 7, 6)),
                ]
                payload = _direct_summary(records)

                self.assert_invalid_source_response(payload)
                self.assertEqual(payload["bucket_amounts"], {})
                self.assertNotIn("grand_total", payload)
                self.assertNotIn("SINV-FINITE", repr(payload))
                self.assertNotIn("CUST-", repr(payload))

    def test_positive_company_balance_with_zero_or_negative_account_balance_fails_closed(self):
        for account_balance in (0, -25):
            with self.subTest(account_balance=account_balance):
                records = [
                    _invoice("SINV-SIGN-1", "CUST-001", 100, date(2026, 7, 6)),
                    _invoice("SINV-SIGN-2", "CUST-002", 200, date(2026, 7, 6)),
                    _invoice("SINV-SIGN-3", "CUST-003", 300, date(2026, 7, 6)),
                ]
                records[0]["amount_in_account_currency"] = account_balance
                payload = _direct_summary(records)

                self.assert_invalid_source_response(payload)
                self.assertNotIn("SINV-SIGN", repr(payload))
                self.assertNotIn("CUST-", repr(payload))

    def test_account_positive_with_non_positive_company_balance_fails_closed(self):
        records = [
            _invoice("SINV-SIGN-REVERSE", "CUST-001", -10, date(2026, 7, 6)),
            _invoice("SINV-SIGN-2", "CUST-002", 200, date(2026, 7, 6)),
            _invoice("SINV-SIGN-3", "CUST-003", 300, date(2026, 7, 6)),
        ]
        records[0]["amount_in_account_currency"] = 10
        payload = _direct_summary(records)

        self.assert_invalid_source_response(payload)
        self.assertNotIn("SINV-SIGN", repr(payload))
        self.assertNotIn("CUST-", repr(payload))

    def test_cross_currency_partial_allocation_with_consistent_signs_remains_decimal_safe(self):
        records = [
            _invoice("SINV-FX-1", "CUST-001", 100, date(2026, 7, 6), posting_date=date(2026, 7, 5)),
            _invoice("SINV-FX-2", "CUST-002", 200, date(2026, 7, 6), posting_date=date(2026, 7, 5)),
            _invoice("SINV-FX-3", "CUST-003", 300, date(2026, 7, 6), posting_date=date(2026, 7, 5)),
            _payment("PE-FX-1", "SINV-FX-1", "CUST-001", 25, date(2026, 7, 6)),
        ]
        records[0]["amount_in_account_currency"] = "2.50"
        records[0]["account_currency"] = "USD"
        records[3]["amount_in_account_currency"] = "-0.625"
        records[3]["account_currency"] = "USD"
        payload = _safe_summary(records)

        self.assert_safe_amount_response(payload)
        self.assertEqual(payload["state"], "ready")
        self.assertEqual(payload["bucket_amounts"]["current"], "575.00")
        self.assertEqual(payload["grand_total"], "575.00")
        self.assertNotIn("USD", repr(payload))
        self.assertNotIn("SINV-FX", repr(payload))

    def test_strict_financial_dates_reject_prefixes_and_malformed_values(self):
        for invalid_value in ("2026-07-06T23:59:59", "2026-07-06 trailing", "06-07-2026", "2026-02-30"):
            with self.subTest(invalid_value=invalid_value):
                with self.assertRaises(ValueError):
                    service._normalize_as_of_date(invalid_value)
                self.assertIsNone(service._coerce_source_date(invalid_value))

        for invalid_type in (b"2026-07-06", 20260706, object()):
            with self.subTest(invalid_type=type(invalid_type).__name__):
                with self.assertRaises(TypeError):
                    service._normalize_as_of_date(invalid_type)
                self.assertIsNone(service._coerce_source_date(invalid_type))

        payload = _safe_summary([
            _invoice("SINV-DATE-1", "CUST-001", 100, "2026-07-06T12:00:00"),
            _invoice("SINV-DATE-2", "CUST-002", 200, date(2026, 7, 6)),
            _invoice("SINV-DATE-3", "CUST-003", 300, date(2026, 7, 6)),
        ])
        self.assert_invalid_source_response(payload)

    def test_count_amount_bucket_mismatch_suppresses_entire_amount_posture(self):
        records = [
            _invoice("SINV-MATCH-1", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-MATCH-2", "CUST-002", 200, date(2026, 7, 6)),
            _invoice("SINV-MATCH-3", "CUST-003", 300, date(2026, 7, 6)),
        ]
        amount_payload = _safe_summary(records)
        count_payload = {
            "state": "ready",
            "bucket_counts": dict(amount_payload["bucket_counts"], overdue_1_30=1),
        }

        self.assertFalse(service._receivables_count_amount_buckets_match(count_payload, amount_payload))
        payload = service._fail_closed_receivables_amount_payload(
            amount_payload,
            "receivables_count_amount_bucket_mismatch",
        )

        self.assert_safe_amount_response(payload)
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["bucket_counts"], {})
        self.assertEqual(payload["bucket_amounts"], {})
        self.assertEqual(payload["suppressed_buckets"], {})
        self.assertNotIn("grand_total", payload)
        self.assertFalse(payload["amounts_are_aggregate"])
        self.assertFalse(payload["runtime_payment_ledger_amount_summary_enabled"])
        self.assertIsNone(payload["company_scope"])
        self.assertNotIn("SINV-MATCH", repr(payload))
        self.assertNotIn("CUST-", repr(payload))

    def test_mismatched_payment_ledger_company_fails_closed_without_partial_amounts(self):
        records = [
            _invoice("SINV-COMPANY-1", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-COMPANY-2", "CUST-002", 200, date(2026, 7, 6), company="Other Company"),
            _invoice("SINV-COMPANY-3", "CUST-003", 300, date(2026, 7, 6)),
        ]
        payload = _direct_summary(records)

        self.assert_safe_amount_response(payload)
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["bucket_amounts"], {})
        self.assertNotIn("grand_total", payload)
        self.assertNotIn("SINV-COMPANY", repr(payload))
        self.assertNotIn("CUST-", repr(payload))
        self.assertNotIn("Other Company", repr(payload))

    def test_reference_anomaly_probe_catches_wrong_company_activity_filtered_from_primary_read(self):
        records = [
            _invoice("SINV-PROBE-1", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-PROBE-2", "CUST-002", 200, date(2026, 7, 6)),
            _invoice("SINV-PROBE-3", "CUST-003", 300, date(2026, 7, 6)),
            _ple(
                voucher_type="Payment Entry", voucher_no="PE-WRONG-COMPANY", party="CUST-001",
                amount=-10, posting_date=date(2026, 7, 6), against_voucher_no="SINV-PROBE-1",
                company="Other Company",
            ),
        ]

        payload = _safe_summary(records)

        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["bucket_amounts"], {})
        self.assertNotIn("grand_total", payload)
        self.assertNotIn("SINV-", repr(payload))
        self.assertNotIn("PE-", repr(payload))
        self.assertNotIn("Other Company", repr(payload))

    def test_mismatched_delinked_payment_ledger_company_fails_closed_before_skip(self):
        records = [
            _invoice("SINV-DELINK-1", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-DELINK-2", "CUST-002", 200, date(2026, 7, 6), company="Other Company"),
            _invoice("SINV-DELINK-3", "CUST-003", 300, date(2026, 7, 6)),
        ]
        records[1]["delinked"] = 1
        payload = _direct_summary(records)

        self.assert_safe_amount_response(payload)
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["bucket_amounts"], {})
        self.assertNotIn("grand_total", payload)
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

    def test_payment_and_journal_allocations_reduce_voucher_outstanding(self):
        records = [
            _invoice("SINV-PE", "CUST-001", 1000, date(2026, 7, 6)),
            _payment("PE-001", "SINV-PE", "CUST-001", 250, date(2026, 7, 6)),
            _invoice("SINV-JE", "CUST-002", 500, date(2026, 7, 6)),
            _journal("JE-001", "SINV-JE", "CUST-002", 100, date(2026, 7, 6)),
            _invoice("SINV-OPEN", "CUST-003", 600, date(2026, 7, 6)),
        ]
        payload = _safe_summary(records)

        self.assert_safe_amount_response(payload)
        self.assertEqual(payload["state"], "ready")
        self.assertEqual(payload["bucket_counts"]["current"], 3)
        self.assertEqual(payload["bucket_amounts"]["current"], "1750.00")
        self.assertEqual(payload["grand_total"], "1750.00")

    def test_supported_activity_without_self_originating_invoice_basis_fails_closed(self):
        base = [
            _invoice("SINV-VALID-1", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-VALID-2", "CUST-002", 200, date(2026, 7, 6)),
            _invoice("SINV-VALID-3", "CUST-003", 300, date(2026, 7, 6)),
        ]
        orphan_rows = (
            _payment("PE-ORPHAN", "SINV-ABSENT", "CUST-004", 25, date(2026, 7, 6)),
            _journal("JE-ORPHAN", "SINV-ABSENT", "CUST-004", 25, date(2026, 7, 6)),
        )
        for orphan_row in orphan_rows:
            with self.subTest(voucher_type=orphan_row["voucher_type"]):
                payload = _safe_summary(base + [orphan_row])

                self.assert_safe_amount_response(payload)
                self.assertEqual(payload["state"], "unavailable")
                self.assertEqual(
                    payload["policy"]["reason"],
                    service.RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON,
                )
                self.assertEqual(payload["bucket_counts"], {})
                self.assertEqual(payload["bucket_amounts"], {})
                self.assertNotIn("grand_total", payload)
                self.assertNotIn("SINV-", repr(payload))
                self.assertNotIn("PE-", repr(payload))
                self.assertNotIn("JE-", repr(payload))
                self.assertNotIn("CUST-", repr(payload))

    def test_misdirected_sales_invoice_basis_fails_closed_without_partial_amounts(self):
        records = [
            _invoice("SINV-DIRECT-1", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-DIRECT-2", "CUST-002", 200, date(2026, 7, 6)),
            _invoice("SINV-DIRECT-3", "CUST-003", 300, date(2026, 7, 6)),
        ]
        records[0]["against_voucher_no"] = "SINV-DIRECT-2"
        payload = _safe_summary(records)

        self.assert_safe_amount_response(payload)
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(
            payload["policy"]["reason"],
            service.RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON,
        )
        self.assertEqual(payload["bucket_amounts"], {})
        self.assertNotIn("grand_total", payload)
        self.assertNotIn("SINV-", repr(payload))
        self.assertNotIn("CUST-", repr(payload))

    def test_credit_or_return_activity_fails_amount_posture_closed(self):
        records = [
            _invoice("SINV-CR", "CUST-001", 600, date(2026, 7, 6)),
            _invoice("SINV-CR-2", "CUST-002", 200, date(2026, 7, 6)),
            _invoice("SINV-CR-3", "CUST-003", 300, date(2026, 7, 6)),
            _credit_invoice("SINV-CREDIT-001", "SINV-CR", "CUST-001", 50, date(2026, 7, 6)),
        ]
        payload = _safe_summary(records)

        self.assert_safe_amount_response(payload)
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["policy"]["reason"], "credit_returns_not_supported")
        self.assertFalse(payload["policy"]["credit_returns_supported"])
        self.assertEqual(payload["bucket_counts"], {})
        self.assertEqual(payload["bucket_amounts"], {})
        self.assertNotIn("grand_total", payload)
        self.assertNotIn("SINV-", repr(payload))
        self.assertNotIn("CUST-", repr(payload))

    def test_malformed_return_activity_aggregate_fails_closed(self):
        records = [
            _invoice("SINV-RET-1", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-RET-2", "CUST-002", 200, date(2026, 7, 6)),
            _invoice("SINV-RET-3", "CUST-003", 300, date(2026, 7, 6)),
        ]
        valid_getter = _sales_invoice_identity_getter(records)

        def malformed_return_getter(doctype, **kwargs):
            if kwargs.get("fields") == [service.RECEIVABLES_COUNT_QUERY_FIELD]:
                return [{"total": 0}]
            return valid_getter(doctype, **kwargs)

        payload = _safe_summary(records, invoice_identity_list_getter=malformed_return_getter)

        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["policy"]["reason"], service.RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
        self.assertEqual(payload["bucket_counts"], {})
        self.assertEqual(payload["bucket_amounts"], {})
        self.assertNotIn("grand_total", payload)

    def test_future_dated_allocations_fail_closed_without_partial_amounts(self):
        records = [
            _invoice("SINV-FUT-1", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-FUT-2", "CUST-002", 100, date(2026, 7, 6)),
            _invoice("SINV-FUT-3", "CUST-003", 100, date(2026, 7, 6)),
            _payment("PE-FUTURE", "SINV-FUT-1", "CUST-001", 100, date(2026, 7, 7)),
        ]
        payload = _safe_summary(records)

        self.assert_safe_amount_response(payload)
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["policy"]["reason"], "future_payment_ledger_activity_not_supported")
        self.assertEqual(payload["bucket_counts"], {})
        self.assertEqual(payload["bucket_amounts"], {})
        self.assertNotIn("grand_total", payload)

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
        self.assertEqual(payload["bucket_amounts"]["current"], "180.00")
        self.assertEqual(payload["grand_total"], "180.00")

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
        self.assertEqual(payload["policy"]["payment_terms_detection"], "sales_invoice_schedule_gate_and_payment_ledger_due_date_consistency")
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
        with patch.object(service, "now_datetime", return_value=datetime(2026, 7, 6, 12, 0, 0)), patch.object(
            service.frappe, "get_roles", return_value=["Accounts Manager"]
        ), patch.object(
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
            "_permission_preserving_receivables_schedule_integrity_gate",
            return_value=0,
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
            "_permission_preserving_receivables_future_activity_count",
            return_value=0,
        ), patch.object(
            service,
            "_currency_precision_contract",
            return_value=_currency_contract(),
        ), patch.object(
            service,
            "_permission_preserving_payment_ledger_rows",
            return_value=records,
        ), patch.object(
            service,
            "_permission_preserving_receivables_invoice_identity_sets",
            return_value={
                "current": frozenset({
                    ("Debtors - MMD", "Sales Invoice", "SINV-OV-1", "Customer", "CUST-001"),
                    ("Debtors - MMD", "Sales Invoice", "SINV-OV-2", "Customer", "CUST-002"),
                    ("Debtors - MMD", "Sales Invoice", "SINV-OV-3", "Customer", "CUST-003"),
                }),
                "overdue_1_30": frozenset(),
                "overdue_31_60": frozenset(),
                "overdue_61_90": frozenset(),
                "overdue_over_90": frozenset(),
            },
        ):
            payload = service.get_finance_control_desk_overview_context()
            with patch.object(service, "_receivables_count_amount_buckets_match", return_value=False):
                mismatched_payload = service.get_finance_control_desk_overview_context()

        self.assertEqual(payload["scope"]["receivables_amount_summary_enabled"], True, {
            "count": payload["receivables_posture"].get("bucket_counts"),
            "amount": payload["receivables_amount_summary"].get("bucket_counts"),
            "reason": payload["receivables_amount_summary"].get("policy", {}).get("reason"),
        })
        self.assertEqual(payload["scope"]["monetary_values_enabled"], True)
        self.assertEqual(payload["receivables_amount_summary"]["policy"]["aging_date_basis"], "due_date_only")
        self.assertEqual(payload["receivables_amount_summary"]["policy"]["posting_date_fallback_enabled"], False)
        self.assertEqual(payload["receivables_amount_summary"]["state"], "ready")
        self.assertEqual(payload["receivables_amount_summary"]["bucket_amounts"]["current"], "600.00")
        self.assertEqual(payload["amounts"], [])
        self.assertEqual(payload["rows"], [])
        self.assertEqual(payload["documents"], [])
        self.assertTrue(all(card["rows"] == [] for card in payload["posture_cards"]))
        receivables_card = next(card for card in payload["posture_cards"] if card["key"] == "receivables_posture")
        self.assertIn("Sales Invoice aggregate count buckets", receivables_card["detail"])
        self.assertIn("manager-only Payment Ledger MMK amount buckets", receivables_card["detail"])
        self.assertIn("No row-level customer, invoice, voucher, account, Payment Ledger, route, report, export, or action detail is returned, shown, linked, exported, or actionable.", receivables_card["detail"])
        self.assertIn("Current / not due: 600.00 MMK", receivables_card["detail"])
        self.assertNotIn("SINV-", repr(payload["receivables_amount_summary"]))
        self.assertNotIn("CUST-", repr(payload["receivables_amount_summary"]))
        mismatch = mismatched_payload["receivables_amount_summary"]
        self.assertEqual(mismatch["state"], "unavailable")
        self.assertEqual(mismatch["bucket_counts"], {})
        self.assertEqual(mismatch["bucket_amounts"], {})
        self.assertEqual(mismatch["suppressed_buckets"], {})
        self.assertNotIn("grand_total", mismatch)
        self.assertFalse(mismatched_payload["scope"]["receivables_amount_summary_enabled"])
        self.assertFalse(mismatched_payload["scope"]["monetary_values_enabled"])
        self.assertFalse(mismatch["policy"]["voucher_set_reconciliation_verified"])
        self.assertNotIn("SINV-", repr(mismatch))
        self.assertNotIn("CUST-", repr(mismatch))

    def test_overview_count_semantic_failure_suppresses_amount_adapter_and_values(self):
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
            "build_receivables_payment_ledger_amount_summary",
            side_effect=AssertionError("amount builder must not run after count semantic failure"),
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
            "_permission_preserving_receivables_future_activity_count",
            return_value=0,
        ), patch.object(
            service,
            "_currency_precision_contract",
            return_value=_currency_contract(),
        ), patch.object(
            service,
            "_permission_preserving_payment_ledger_rows",
            return_value=records,
        ):
            payload = service.get_finance_control_desk_overview_context()

        self.assertEqual(payload["scope"]["receivables_count_posture_enabled"], False)
        self.assertEqual(payload["scope"]["receivables_amount_summary_enabled"], False)
        self.assertEqual(payload["scope"]["monetary_values_enabled"], False)
        self.assertEqual(payload["receivables_amount_summary"]["state"], "unavailable")
        self.assertEqual(payload["receivables_amount_summary"]["policy"]["reason"], "receivables_count_semantics_required")
        self.assertEqual(payload["receivables_amount_summary"]["bucket_amounts"], {})
        self.assertNotIn("grand_total", payload["receivables_amount_summary"])
        receivables_card = next(card for card in payload["posture_cards"] if card["key"] == "receivables_posture")
        self.assertIn("Receivables posture is unavailable", receivables_card["detail"])
        self.assertNotIn("MMK buckets only", receivables_card["value"])
        self.assertNotIn("600.00 MMK", receivables_card["detail"])
        self.assertEqual(payload["rows"], [])
        self.assertEqual(payload["documents"], [])

    def test_currency_precision_contract_uses_erpnext_global_precision_and_decimal_strings(self):
        contract = service._currency_precision_contract(
            "MMK",
            precision_provider=lambda: 3,
            rounding_method_getter=lambda key: "Banker's Rounding",
        )
        self.assertEqual(contract["precision"], 3)
        self.assertEqual(contract["precision_source"], "erpnext.accounts.utils.get_currency_precision")
        self.assertEqual(service._currency_decimal_string(service.Decimal("9007199254740993.1255"), contract), "9007199254740993.126")
        self.assertNotIn("number_format", contract)

    def test_currency_precision_contract_uses_system_rounding_not_user_defaults(self):
        user_default_getter = getattr(frappe.defaults, "get_global_default", None)
        frappe.defaults.get_global_default = lambda key: "Commercial Rounding"
        try:
            with patch.object(
                frappe,
                "get_system_settings",
                return_value="Banker's Rounding",
                create=True,
            ) as system_settings:
                contract = service._currency_precision_contract(
                    "MMK",
                    precision_provider=lambda: 2,
                )
        finally:
            if user_default_getter is None:
                delattr(frappe.defaults, "get_global_default")
            else:
                frappe.defaults.get_global_default = user_default_getter

        system_settings.assert_called_once_with("rounding_method")
        self.assertEqual(contract["rounding_method"], "Banker's Rounding")
        self.assertEqual(
            service._currency_decimal_string(service.Decimal("100.005"), contract),
            "100.00",
        )

    def test_currency_precision_contract_fails_closed_on_uncertain_global_precision(self):
        for value in (None, True, -1, 9, "2.5"):
            with self.subTest(value=value):
                with self.assertRaises(service._ReceivablesAmountUnavailable):
                    service._currency_precision_contract(
                        "MMK",
                        precision_provider=lambda value=value: value,
                        rounding_method_getter=lambda key: "Banker's Rounding",
                    )

    def test_invalid_currency_precision_contract_fails_closed_before_ledger_adapter(self):
        payload = service.build_receivables_payment_ledger_amount_summary(
            context=_context(),
            resolver=_resolver(),
            as_of_date="2026-07-06",
            permission_checker=_permission_checker(True),
            metadata_provider=_metadata_provider(),
            currency_contract_provider=lambda currency: {"verified": False},
            future_activity_list_getter=_future_activity_getter([]),
            list_getter=_raising_getter,
        )
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["policy"]["reason"], service.RECEIVABLES_AMOUNT_CURRENCY_CONTRACT_INVALID_REASON)
        self.assertEqual(payload["bucket_amounts"], {})
        self.assertNotIn("grand_total", payload)

    def test_exact_voucher_sets_are_required_even_when_bucket_counts_match(self):
        amount_records = [
            _invoice("SINV-SET-1", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-SET-2", "CUST-002", 200, date(2026, 7, 6)),
            _invoice("SINV-SET-3", "CUST-003", 300, date(2026, 7, 6)),
        ]
        different_invoice_records = [
            _invoice("SINV-SET-1", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-SET-2", "CUST-002", 200, date(2026, 7, 6)),
            _invoice("SINV-DIFFERENT", "CUST-004", 300, date(2026, 7, 6)),
        ]
        payload = _safe_summary(
            amount_records,
            invoice_identity_list_getter=_sales_invoice_identity_getter(different_invoice_records),
        )

        self.assert_safe_amount_response(payload)
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["policy"]["reason"], service.RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
        self.assertEqual(payload["bucket_counts"], {})
        self.assertEqual(payload["bucket_amounts"], {})
        self.assertNotIn("grand_total", payload)
        self.assertNotIn("SINV-", repr(payload))
        self.assertNotIn("CUST-", repr(payload))

    def test_exact_voucher_set_reconciliation_accepts_matching_composite_keys(self):
        records = [
            _invoice("SINV-EXACT-1", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-EXACT-2", "CUST-002", 200, date(2026, 7, 6)),
            _invoice("SINV-EXACT-3", "CUST-003", 300, date(2026, 7, 6)),
            _payment("PE-EXACT", "SINV-EXACT-1", "CUST-001", 10, date(2026, 7, 6)),
        ]
        payload = _safe_summary(records)

        self.assertEqual(payload["state"], "ready")
        self.assertTrue(payload["policy"]["voucher_set_reconciliation_verified"])
        self.assertEqual(payload["policy"]["voucher_set_reconciliation"], "account_voucher_type_voucher_party")
        self.assertFalse(payload["policy"]["voucher_identities_returned"])
        self.assertEqual(payload["bucket_amounts"]["current"], "590.00")
        self.assertNotIn("SINV-", repr(payload))
        self.assertNotIn("CUST-", repr(payload))

    def test_missing_or_extra_voucher_on_either_side_fails_closed(self):
        amount_records = [
            _invoice("SINV-SIDE-1", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-SIDE-2", "CUST-002", 200, date(2026, 7, 6)),
            _invoice("SINV-SIDE-3", "CUST-003", 300, date(2026, 7, 6)),
        ]
        cases = [
            amount_records[:2],
            amount_records + [_invoice("SINV-SIDE-4", "CUST-004", 400, date(2026, 7, 6))],
        ]
        for invoice_records in cases:
            with self.subTest(invoice_count=len(invoice_records)):
                payload = _safe_summary(
                    amount_records,
                    invoice_identity_list_getter=_sales_invoice_identity_getter(invoice_records),
                )
                self.assertEqual(payload["state"], "unavailable")
                self.assertEqual(payload["policy"]["reason"], service.RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
                self.assertEqual(payload["bucket_amounts"], {})
                self.assertNotIn("grand_total", payload)

    def test_duplicate_payment_ledger_row_identity_fails_closed(self):
        records = [
            _invoice("SINV-DUP-1", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-DUP-2", "CUST-002", 200, date(2026, 7, 6)),
            _invoice("SINV-DUP-3", "CUST-003", 300, date(2026, 7, 6)),
        ]
        records.append(dict(records[0]))
        payload = _safe_summary(records)

        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["policy"]["reason"], service.RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
        self.assertEqual(payload["bucket_amounts"], {})
        self.assertNotIn("grand_total", payload)


    def test_distinct_row_names_cannot_replay_the_same_ledger_activity(self):
        records = [
            _invoice("SINV-REPLAY-1", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-REPLAY-2", "CUST-002", 200, date(2026, 7, 6)),
            _invoice("SINV-REPLAY-3", "CUST-003", 300, date(2026, 7, 6)),
            _payment("PE-REPLAY", "SINV-REPLAY-1", "CUST-001", 10, date(2026, 7, 6)),
        ]
        replay = dict(records[-1])
        replay["name"] = "PLE-DIFFERENT-ROW-NAME"
        records.append(replay)

        payload = _safe_summary(records)

        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["policy"]["reason"], service.RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
        self.assertEqual(payload["bucket_amounts"], {})
        self.assertNotIn("grand_total", payload)
        self.assertNotIn("SINV-", repr(payload))
        self.assertNotIn("PE-", repr(payload))

    def test_distinct_voucher_detail_rows_are_not_false_duplicates(self):
        records = [
            _invoice("SINV-DETAIL-1", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-DETAIL-2", "CUST-002", 200, date(2026, 7, 6)),
            _invoice("SINV-DETAIL-3", "CUST-003", 300, date(2026, 7, 6)),
            _ple(
                voucher_type="Journal Entry", voucher_no="JV-DETAIL", voucher_detail_no="JV-LINE-1",
                row_name="PLE-JV-DETAIL-1", party="CUST-001", amount=-5,
                posting_date=date(2026, 7, 6), against_voucher_no="SINV-DETAIL-1",
            ),
            _ple(
                voucher_type="Journal Entry", voucher_no="JV-DETAIL", voucher_detail_no="JV-LINE-2",
                row_name="PLE-JV-DETAIL-2", party="CUST-001", amount=-5,
                posting_date=date(2026, 7, 6), against_voucher_no="SINV-DETAIL-1",
            ),
        ]

        payload = _safe_summary(records)

        self.assertEqual(payload["state"], "ready")
        self.assertEqual(payload["bucket_amounts"]["current"], "590.00")

    def test_malformed_checkbox_values_fail_closed(self):
        base = [
            _invoice("SINV-FLAG-1", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-FLAG-2", "CUST-002", 200, date(2026, 7, 6)),
            _invoice("SINV-FLAG-3", "CUST-003", 300, date(2026, 7, 6)),
        ]
        for field, value in (("delinked", 2), ("delinked", 1.0), ("delinked", "maybe")):
            with self.subTest(field=field, value=value):
                records = [dict(row) for row in base]
                records[0][field] = value
                payload = _safe_summary(records)
                self.assertEqual(payload["state"], "unavailable")
                self.assertEqual(payload["bucket_amounts"], {})
                self.assertNotIn("grand_total", payload)

    def test_identity_components_require_exact_unpadded_strings(self):
        base = [
            _invoice("SINV-STRICT-1", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-STRICT-2", "CUST-002", 200, date(2026, 7, 6)),
            _invoice("SINV-STRICT-3", "CUST-003", 300, date(2026, 7, 6)),
        ]
        cases = [
            ("padded_invoice", 0, "voucher_no", " SINV-STRICT-1"),
            ("numeric_customer", 0, "party", 101),
            ("padded_account", 0, "account", " Debtors - MMD"),
            ("padded_company", 0, "company", f" {_COMPANY_SCOPE['name']}"),
            ("container_link", 0, "against_voucher_no", {"name": "SINV-STRICT-1"}),
        ]
        for label, index, field, value in cases:
            with self.subTest(label=label):
                records = [dict(row) for row in base]
                records[index][field] = value
                payload = _safe_summary(records)
                self.assertEqual(payload["state"], "unavailable")
                self.assertEqual(payload["bucket_amounts"], {})
                self.assertNotIn("grand_total", payload)
                self.assertNotIn("SINV-", repr(payload))
                self.assertNotIn("CUST-", repr(payload))

    def test_unknown_or_uncorrelatable_payment_ledger_voucher_fails_closed(self):
        base = [
            _invoice("SINV-TYPE-1", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-TYPE-2", "CUST-002", 200, date(2026, 7, 6)),
            _invoice("SINV-TYPE-3", "CUST-003", 300, date(2026, 7, 6)),
        ]
        cases = [
            _ple(
                voucher_type="Stock Entry", voucher_no="STE-001", party="CUST-001", amount=-1,
                posting_date=date(2026, 7, 6), against_voucher_no="SINV-TYPE-1",
            ),
            _ple(
                voucher_type="Payment Entry", voucher_no="PE-ADV", party="CUST-001", amount=10,
                posting_date=date(2026, 7, 6), against_voucher_type="Payment Entry",
                against_voucher_no="PE-ADV",
            ),
        ]
        for bad_row in cases:
            with self.subTest(voucher_type=bad_row["voucher_type"], against_type=bad_row["against_voucher_type"]):
                payload = _safe_summary(base + [bad_row])
                self.assertEqual(payload["state"], "unavailable")
                self.assertEqual(payload["policy"]["reason"], service.RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
                self.assertEqual(payload["bucket_amounts"], {})
                self.assertNotIn("grand_total", payload)

    def test_bucket_identity_disagreement_fails_closed(self):
        amount_records = [
            _invoice("SINV-BUCKET-1", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-BUCKET-2", "CUST-002", 200, date(2026, 7, 6)),
            _invoice("SINV-BUCKET-3", "CUST-003", 300, date(2026, 7, 6)),
        ]
        invoice_records = [dict(row) for row in amount_records]
        invoice_records[2]["due_date"] = date(2026, 6, 20)
        payload = _safe_summary(
            amount_records,
            invoice_identity_list_getter=_sales_invoice_identity_getter(invoice_records),
        )

        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["policy"]["reason"], service.RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
        self.assertEqual(payload["bucket_amounts"], {})
        self.assertNotIn("grand_total", payload)

    def test_invoice_identity_permission_uncertainty_and_cap_fail_closed_before_output(self):
        records = [
            _invoice("SINV-ID-1", "CUST-001", 100, date(2026, 7, 6)),
            _invoice("SINV-ID-2", "CUST-002", 200, date(2026, 7, 6)),
            _invoice("SINV-ID-3", "CUST-003", 300, date(2026, 7, 6)),
        ]
        denied = _safe_summary(
            records,
            invoice_identity_list_getter=lambda *args, **kwargs: (_ for _ in ()).throw(_FrappePermissionError()),
        )
        self.assertEqual(denied["state"], "unavailable")
        self.assertEqual(denied["policy"]["reason"], service.RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
        self.assertEqual(denied["bucket_amounts"], {})

        with patch.object(service, "RECEIVABLES_IDENTITY_SOURCE_MAX_ROWS", 2), patch.object(
            service, "RECEIVABLES_IDENTITY_SOURCE_PAGE_SIZE", 2
        ):
            capped = _safe_summary(records)
        self.assertEqual(capped["state"], "unavailable")
        self.assertEqual(capped["policy"]["reason"], service.RECEIVABLES_IDENTITY_SOURCE_INVALID_REASON)
        self.assertEqual(capped["bucket_amounts"], {})
        self.assertNotIn("grand_total", capped)

    def test_strict_financial_date_policy_rejects_padding_and_datetime_objects(self):
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
                with self.assertRaises((TypeError, ValueError)):
                    service._normalize_as_of_date(invalid_value)
                self.assertIsNone(service._coerce_source_date(invalid_value))

        self.assertEqual(service._normalize_as_of_date(date(2026, 7, 6)), date(2026, 7, 6))
        self.assertEqual(service._normalize_as_of_date("2026-07-06"), date(2026, 7, 6))

    def test_explicit_empty_as_of_date_fails_closed_before_amount_gates(self):
        payload = service.build_receivables_payment_ledger_amount_summary(
            context=_context(),
            resolver=_resolver(),
            as_of_date="",
            permission_checker=_raising_permission,
            metadata_provider=_raising_metadata,
            list_getter=_raising_getter,
            invoice_identity_list_getter=_raising_getter,
            future_activity_list_getter=_raising_getter,
            currency_contract_provider=lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("currency contract must not run for invalid date")
            ),
        )

        self.assert_safe_amount_response(payload)
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["policy"]["reason"], "invalid_as_of_date")
        self.assertEqual(payload["bucket_counts"], {})
        self.assertEqual(payload["bucket_amounts"], {})
        self.assertNotIn("grand_total", payload)

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
