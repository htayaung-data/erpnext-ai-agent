from __future__ import annotations

import copy
import unittest
from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal

from erp_workspace_ui.finance_accounting.gl_trial_balance_core import (
    AccountNode,
    GLTrialBalanceInputError,
    NormalizedGLEntry,
    TrialBalanceContext,
    build_trial_balance,
)


COMPANY = "COMPANY_A"
CURRENCY = "MMK"
DEFAULT_BOOK = "BOOK_DEFAULT"


def _context(**changes: object) -> TrialBalanceContext:
    value = TrialBalanceContext(
        company=COMPANY,
        base_currency=CURRENCY,
        precision=2,
        fiscal_year_start=date(2026, 1, 1),
        fiscal_year_end=date(2026, 12, 31),
        from_date=date(2026, 4, 1),
        to_date=date(2026, 6, 30),
        default_finance_book=DEFAULT_BOOK,
        finance_book_cohort=(DEFAULT_BOOK, "", None),
        active_dimensions=0,
    )
    return replace(value, **changes)


def _account(
    account_id: str,
    parent: str | None,
    is_group: bool,
    root_type: str,
    sort_order: int,
    **changes: object,
) -> AccountNode:
    value = AccountNode(
        account_id=account_id,
        company=COMPANY,
        parent_account_id=parent,
        is_group=is_group,
        root_type=root_type,
        account_currency=CURRENCY,
        sort_order=sort_order,
    )
    return replace(value, **changes)


ACCOUNTS = (
    _account("ASSET_ROOT", None, True, "Asset", 10),
    _account("CURRENT_ASSETS", "ASSET_ROOT", True, "Asset", 10),
    _account("CASH", "CURRENT_ASSETS", False, "Asset", 10),
    _account("RECEIVABLE", "CURRENT_ASSETS", False, "Asset", 20),
    _account("ZERO_ASSET", "CURRENT_ASSETS", False, "Asset", 30),
    _account("LIABILITY_ROOT", None, True, "Liability", 20),
    _account("PAYABLE", "LIABILITY_ROOT", False, "Liability", 10),
    _account("EQUITY_ROOT", None, True, "Equity", 30),
    _account("EQUITY", "EQUITY_ROOT", False, "Equity", 10),
    _account("INCOME_ROOT", None, True, "Income", 40),
    _account("REVENUE", "INCOME_ROOT", False, "Income", 10),
    _account("EXPENSE_ROOT", None, True, "Expense", 50),
    _account("EXPENSE", "EXPENSE_ROOT", False, "Expense", 10),
)
EXPECTED_ACCOUNT_IDS = tuple(account.account_id for account in ACCOUNTS)
EXPECTED_ROOT_IDS = (
    "ASSET_ROOT",
    "LIABILITY_ROOT",
    "EQUITY_ROOT",
    "INCOME_ROOT",
    "EXPENSE_ROOT",
)


def _entry(
    entry_id: str,
    account_id: str,
    posting_date: date,
    debit: str,
    credit: str,
    *,
    finance_book: str | None = DEFAULT_BOOK,
    is_opening: bool = False,
    **changes: object,
) -> NormalizedGLEntry:
    value = NormalizedGLEntry(
        entry_id=entry_id,
        company=COMPANY,
        account_id=account_id,
        posting_date=posting_date,
        debit=Decimal(debit),
        credit=Decimal(credit),
        currency=CURRENCY,
        finance_book=finance_book,
        is_opening=is_opening,
    )
    return replace(value, **changes)


ENTRIES = (
    _entry("OPEN_CASH", "CASH", date(2026, 1, 1), "100.00", "0", is_opening=True),
    _entry("OPEN_EQUITY", "EQUITY", date(2026, 1, 1), "0", "100.00", is_opening=True),
    _entry("MOVE_AR", "RECEIVABLE", date(2026, 4, 1), "60.00", "0"),
    _entry("MOVE_REVENUE", "REVENUE", date(2026, 4, 1), "0", "60.00"),
    _entry("MOVE_CASH_UNBOOKED", "CASH", date(2026, 6, 30), "40.00", "0", finance_book=""),
    _entry("MOVE_AR_UNBOOKED", "RECEIVABLE", date(2026, 6, 30), "0", "40.00", finance_book=None),
)


def _build(
    *,
    context: TrialBalanceContext | None = None,
    accounts: object = ACCOUNTS,
    entries: object = ENTRIES,
    expected_account_ids: object = EXPECTED_ACCOUNT_IDS,
    expected_root_ids: object = EXPECTED_ROOT_IDS,
):
    return build_trial_balance(
        context=context or _context(),
        expected_account_ids=expected_account_ids,
        expected_root_account_ids=expected_root_ids,
        accounts=accounts,
        entries=entries,
    )


def _lines(result) -> dict[str, object]:
    return {line.account_id: line for line in result.lines}


class TestFinanceGLTrialBalanceCore(unittest.TestCase):
    def test_balanced_opening_movement_closing_and_hierarchy_rollup(self):
        result = _build()
        lines = _lines(result)

        self.assertEqual(result.gross_totals.opening_debit, Decimal("100.00"))
        self.assertEqual(result.gross_totals.opening_credit, Decimal("100.00"))
        self.assertEqual(result.gross_totals.movement_debit, Decimal("100.00"))
        self.assertEqual(result.gross_totals.movement_credit, Decimal("100.00"))
        self.assertEqual(result.gross_totals.closing_debit, Decimal("200.00"))
        self.assertEqual(result.gross_totals.closing_credit, Decimal("200.00"))
        self.assertEqual(result.presentation_totals.closing_debit, Decimal("160.00"))
        self.assertEqual(result.presentation_totals.closing_credit, Decimal("160.00"))
        self.assertEqual(lines["CASH"].amounts.closing_debit, Decimal("140.00"))
        self.assertEqual(lines["RECEIVABLE"].amounts.closing_debit, Decimal("20.00"))
        self.assertEqual(lines["CURRENT_ASSETS"].amounts.closing_debit, Decimal("160.00"))
        self.assertEqual(lines["ASSET_ROOT"].amounts.closing_debit, Decimal("160.00"))
        for amounts in (line.amounts for line in result.lines):
            self.assertEqual(
                amounts.opening_debit
                - amounts.opening_credit
                + amounts.movement_debit
                - amounts.movement_credit,
                amounts.closing_debit - amounts.closing_credit,
            )

    def test_deterministic_order_and_equivalent_reordered_input(self):
        forward = _build()
        reversed_result = _build(
            context=_context(finance_book_cohort=(None, "", DEFAULT_BOOK)),
            accounts=tuple(reversed(ACCOUNTS)),
            entries=tuple(reversed(ENTRIES)),
            expected_account_ids=tuple(reversed(EXPECTED_ACCOUNT_IDS)),
            expected_root_ids=tuple(reversed(EXPECTED_ROOT_IDS)),
        )

        self.assertEqual(forward, reversed_result)
        self.assertEqual(
            tuple(line.account_id for line in forward.lines),
            (
                "ASSET_ROOT",
                "CURRENT_ASSETS",
                "CASH",
                "RECEIVABLE",
                "ZERO_ASSET",
                "LIABILITY_ROOT",
                "PAYABLE",
                "EQUITY_ROOT",
                "EQUITY",
                "INCOME_ROOT",
                "REVENUE",
                "EXPENSE_ROOT",
                "EXPENSE",
            ),
        )

    def test_zero_activity_accounts_are_retained_by_complete_chart(self):
        result = _build()
        zero = _lines(result)["ZERO_ASSET"]
        self.assertEqual(zero.amounts.opening_debit, Decimal("0.00"))
        self.assertEqual(zero.amounts.movement_debit, Decimal("0.00"))
        self.assertEqual(zero.amounts.closing_debit, Decimal("0.00"))
        self.assertEqual(len(result.lines), len(EXPECTED_ACCOUNT_IDS))

    def test_fiscal_and_requested_date_boundaries_are_inclusive(self):
        entries = (
            _entry("PNL_OPEN_D", "EXPENSE", date(2026, 1, 1), "20", "0"),
            _entry("PNL_OPEN_C", "REVENUE", date(2026, 1, 1), "0", "20"),
            _entry("FROM_D", "EXPENSE", date(2026, 4, 1), "10", "0"),
            _entry("FROM_C", "REVENUE", date(2026, 4, 1), "0", "10"),
            _entry("TO_D", "EXPENSE", date(2026, 6, 30), "5", "0"),
            _entry("TO_C", "REVENUE", date(2026, 6, 30), "0", "5"),
        )
        result = _build(entries=entries)
        lines = _lines(result)

        self.assertEqual(lines["EXPENSE"].amounts.opening_debit, Decimal("20.00"))
        self.assertEqual(lines["EXPENSE"].amounts.movement_debit, Decimal("15.00"))
        self.assertEqual(lines["REVENUE"].amounts.closing_credit, Decimal("35.00"))
        full_year = _build(context=_context(from_date=date(2026, 1, 1), to_date=date(2026, 12, 31)))
        self.assertEqual(full_year.scope.from_date, date(2026, 1, 1))
        self.assertEqual(full_year.scope.to_date, date(2026, 12, 31))

    def test_profit_and_loss_invalid_opening_inputs_fail_closed(self):
        cases = (
            (
                _entry(
                    "PNL_MARKER_D",
                    "EXPENSE",
                    date(2026, 1, 1),
                    "1",
                    "0",
                    is_opening=True,
                ),
                _entry(
                    "PNL_MARKER_C",
                    "REVENUE",
                    date(2026, 1, 1),
                    "0",
                    "1",
                    is_opening=True,
                ),
            ),
            (
                _entry("PNL_PRIOR_D", "EXPENSE", date(2025, 12, 31), "1", "0"),
                _entry("PNL_PRIOR_C", "REVENUE", date(2025, 12, 31), "0", "1"),
            ),
        )
        for entries in cases:
            with self.subTest(entries=entries):
                with self.assertRaises(GLTrialBalanceInputError) as raised:
                    _build(entries=entries)
                self.assertEqual(raised.exception.code, "profit_and_loss_opening_invalid")

    def test_malformed_and_out_of_range_dates_fail_closed(self):
        contexts = (
            (_context(fiscal_year_start="2026-01-01"), "date_invalid"),
            (_context(from_date=datetime(2026, 4, 1)), "date_invalid"),
            (_context(from_date=date(2025, 12, 31)), "date_range_invalid"),
            (
                _context(from_date=date(2026, 7, 1), to_date=date(2026, 6, 30)),
                "date_range_invalid",
            ),
            (_context(to_date=date(2027, 1, 1)), "date_range_invalid"),
        )
        for context, expected_code in contexts:
            with self.subTest(context=context):
                with self.assertRaises(GLTrialBalanceInputError) as raised:
                    _build(context=context)
                self.assertEqual(raised.exception.code, expected_code)
        invalid_entries = (
            (
                (
                    replace(ENTRIES[0], posting_date="2026-01-01"),
                    replace(ENTRIES[1], posting_date="2026-01-01"),
                ),
                "posting_date_invalid",
            ),
            (
                (
                    replace(ENTRIES[0], posting_date=datetime(2026, 1, 1)),
                    replace(ENTRIES[1], posting_date=datetime(2026, 1, 1)),
                ),
                "posting_date_invalid",
            ),
            (
                (
                    replace(ENTRIES[0], posting_date=date(2026, 7, 1)),
                    replace(ENTRIES[1], posting_date=date(2026, 7, 1)),
                ),
                "posting_date_out_of_scope",
            ),
        )
        for entries, expected_code in invalid_entries:
            with self.subTest(entries=entries):
                with self.assertRaises(GLTrialBalanceInputError) as raised:
                    _build(entries=entries)
                self.assertEqual(raised.exception.code, expected_code)

    def test_default_blank_and_null_finance_book_cohort_is_exact(self):
        result = _build()
        self.assertEqual(
            result.scope.finance_book_cohort,
            ("company_default", "blank_unbooked", "null_unbooked"),
        )
        invalid_contexts = (
            _context(finance_book_cohort=(DEFAULT_BOOK, None)),
            _context(finance_book_cohort=(DEFAULT_BOOK, "", None, "BOOK_OTHER")),
            _context(finance_book_cohort=(DEFAULT_BOOK, "", "")),
        )
        for context in invalid_contexts:
            with self.subTest(context=context):
                with self.assertRaises(GLTrialBalanceInputError) as raised:
                    _build(context=context)
                self.assertEqual(raised.exception.code, "finance_book_cohort_invalid")
        with self.assertRaises(GLTrialBalanceInputError) as raised:
            _build(entries=(replace(ENTRIES[0], finance_book="BOOK_OTHER"),))
        self.assertEqual(raised.exception.code, "finance_book_cohort_invalid")

    def test_finance_book_cohorts_must_balance_independently(self):
        aggregate_balanced_but_cohorts_unbalanced = (
            _entry("DEFAULT_DEBIT", "CASH", date(2026, 5, 1), "10.00", "0"),
            _entry(
                "UNBOOKED_CREDIT",
                "EQUITY",
                date(2026, 5, 1),
                "0",
                "10.00",
                finance_book="",
            ),
        )
        with self.assertRaises(GLTrialBalanceInputError) as raised:
            _build(entries=aggregate_balanced_but_cohorts_unbalanced)
        self.assertEqual(raised.exception.code, "trial_balance_imbalance")

    def test_balance_sheet_opening_marker_inside_requested_period_is_opening(self):
        entries = (
            _entry(
                "OPEN_IN_PERIOD_DEBIT",
                "CASH",
                date(2026, 5, 1),
                "25.00",
                "0",
                is_opening=True,
            ),
            _entry(
                "OPEN_IN_PERIOD_CREDIT",
                "EQUITY",
                date(2026, 5, 1),
                "0",
                "25.00",
                is_opening=True,
            ),
        )
        result = _build(entries=entries)
        self.assertEqual(result.gross_totals.opening_debit, Decimal("25.00"))
        self.assertEqual(result.gross_totals.opening_credit, Decimal("25.00"))
        self.assertEqual(result.gross_totals.movement_debit, Decimal("0.00"))
        self.assertEqual(result.gross_totals.movement_credit, Decimal("0.00"))

    def test_wrong_company_or_currency_fails_closed(self):
        cases = (
            (
                {
                    "entries": (
                        replace(ENTRIES[0], company="COMPANY_B"),
                        replace(ENTRIES[1], company="COMPANY_B"),
                    )
                },
                "company_mismatch",
            ),
            (
                {
                    "entries": (
                        replace(ENTRIES[0], currency="USD"),
                        replace(ENTRIES[1], currency="USD"),
                    )
                },
                "currency_mismatch",
            ),
            (
                {"accounts": (replace(ACCOUNTS[0], company="COMPANY_B"),) + ACCOUNTS[1:]},
                "company_mismatch",
            ),
            (
                {
                    "accounts": (replace(ACCOUNTS[0], account_currency="USD"),)
                    + ACCOUNTS[1:]
                },
                "currency_mismatch",
            ),
        )
        for case, expected_code in cases:
            with self.subTest(case=case):
                with self.assertRaises(GLTrialBalanceInputError) as raised:
                    _build(**case)
                self.assertEqual(raised.exception.code, expected_code)

    def test_active_or_entry_dimensions_fail_closed(self):
        with self.assertRaises(GLTrialBalanceInputError) as raised:
            _build(context=_context(active_dimensions=1))
        self.assertEqual(raised.exception.code, "active_dimensions_not_supported")
        entries = (
            replace(ENTRIES[0], dimension_values=(("cost_center", "CC-1"),)),
            replace(ENTRIES[1], dimension_values=(("cost_center", "CC-1"),)),
        )
        with self.assertRaises(GLTrialBalanceInputError) as raised:
            _build(entries=entries)
        self.assertEqual(raised.exception.code, "dimensions_not_supported")

    def test_missing_parent_fails_closed(self):
        accounts = tuple(
            replace(account, parent_account_id="MISSING")
            if account.account_id == "CASH"
            else account
            for account in ACCOUNTS
        )
        with self.assertRaisesRegex(GLTrialBalanceInputError, "missing_parent"):
            _build(accounts=accounts)

    def test_orphan_account_fails_closed(self):
        orphan = _account("ORPHAN", None, False, "Asset", 99)
        with self.assertRaisesRegex(GLTrialBalanceInputError, "orphan_account"):
            _build(
                accounts=ACCOUNTS + (orphan,),
                expected_account_ids=EXPECTED_ACCOUNT_IDS + ("ORPHAN",),
            )

    def test_hierarchy_cycle_fails_closed(self):
        accounts = tuple(
            replace(account, parent_account_id="CASH")
            if account.account_id == "CURRENT_ASSETS"
            else account
            for account in ACCOUNTS
        )
        with self.assertRaisesRegex(GLTrialBalanceInputError, "hierarchy_cycle"):
            _build(accounts=accounts)

    def test_duplicate_account_fails_closed(self):
        with self.assertRaisesRegex(GLTrialBalanceInputError, "duplicate_account"):
            _build(accounts=ACCOUNTS + (ACCOUNTS[-1],))

    def test_inconsistent_group_and_leaf_structure_fails_closed(self):
        cases = (
            (
                tuple(
                    replace(account, is_group=True)
                    if account.account_id == "CASH"
                    else account
                    for account in ACCOUNTS
                ),
                "group_without_children",
            ),
            (
                tuple(
                    replace(account, is_group=False)
                    if account.account_id == "CURRENT_ASSETS"
                    else account
                    for account in ACCOUNTS
                ),
                "leaf_with_children",
            ),
        )
        for accounts, expected_code in cases:
            with self.subTest(accounts=accounts):
                with self.assertRaises(GLTrialBalanceInputError) as raised:
                    _build(accounts=accounts)
                self.assertEqual(raised.exception.code, expected_code)

    def test_incomplete_chart_fails_closed(self):
        with self.assertRaisesRegex(GLTrialBalanceInputError, "incomplete_chart"):
            _build(accounts=ACCOUNTS[:-1])
        with self.assertRaisesRegex(GLTrialBalanceInputError, "incomplete_chart"):
            _build(expected_account_ids=EXPECTED_ACCOUNT_IDS[:-1])

    def test_invalid_sign_and_precision_fail_closed(self):
        invalid_debits = (
            (Decimal("-1.00"), "amount_invalid"),
            (Decimal("-0.00"), "amount_invalid"),
            (Decimal("1.001"), "amount_precision_invalid"),
        )
        for value, expected_code in invalid_debits:
            entries = (
                replace(ENTRIES[0], debit=value),
                replace(ENTRIES[1], credit=value),
            )
            with self.subTest(value=value):
                with self.assertRaises(GLTrialBalanceInputError) as raised:
                    _build(entries=entries)
                self.assertEqual(raised.exception.code, expected_code)
        for precision in (-1, "2"):
            with self.subTest(precision=precision):
                with self.assertRaises(GLTrialBalanceInputError) as raised:
                    _build(context=_context(precision=precision))
                self.assertEqual(raised.exception.code, "precision_invalid")

    def test_boolean_integer_and_float_confusion_fails_closed(self):
        cases = (
            ({"context": _context(precision=True)}, "precision_invalid"),
            (
                {"accounts": (replace(ACCOUNTS[0], is_group=1),) + ACCOUNTS[1:]},
                "account_kind_invalid",
            ),
            (
                {"accounts": (replace(ACCOUNTS[0], sort_order=True),) + ACCOUNTS[1:]},
                "sort_order_invalid",
            ),
            (
                {
                    "entries": (
                        replace(ENTRIES[0], debit=True),
                        replace(ENTRIES[1], credit=True),
                    )
                },
                "amount_invalid",
            ),
            (
                {
                    "entries": (
                        replace(ENTRIES[0], debit=1),
                        replace(ENTRIES[1], credit=1),
                    )
                },
                "amount_invalid",
            ),
            (
                {
                    "entries": (
                        replace(ENTRIES[0], debit=1.0),
                        replace(ENTRIES[1], credit=1.0),
                    )
                },
                "amount_invalid",
            ),
            (
                {
                    "entries": (
                        replace(ENTRIES[0], is_opening=1),
                        replace(ENTRIES[1], is_opening=1),
                    )
                },
                "opening_marker_invalid",
            ),
        )
        for case, expected_code in cases:
            with self.subTest(case=case):
                with self.assertRaises(GLTrialBalanceInputError) as raised:
                    _build(**case)
                self.assertEqual(raised.exception.code, expected_code)

    def test_non_finite_decimal_values_fail_closed(self):
        for value in (Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")):
            entries = (
                replace(ENTRIES[0], debit=value),
                replace(ENTRIES[1], credit=value),
            )
            with self.subTest(value=value):
                with self.assertRaises(GLTrialBalanceInputError) as raised:
                    _build(entries=entries)
                self.assertEqual(raised.exception.code, "amount_invalid")

    def test_zero_or_double_sided_entry_fails_closed(self):
        cases = (
            replace(ENTRIES[0], debit=Decimal("0"), credit=Decimal("0")),
            replace(ENTRIES[0], debit=Decimal("1"), credit=Decimal("1")),
        )
        for entry in cases:
            with self.subTest(entry=entry):
                with self.assertRaises(GLTrialBalanceInputError) as raised:
                    _build(entries=(entry,))
                self.assertEqual(raised.exception.code, "entry_sides_invalid")

    def test_imbalance_fails_closed(self):
        unpaired = _entry("UNPAIRED", "CASH", date(2026, 5, 1), "1", "0")
        with self.assertRaisesRegex(GLTrialBalanceInputError, "trial_balance_imbalance"):
            _build(entries=ENTRIES + (unpaired,))

    def test_failure_returns_no_partial_result_or_identifying_error(self):
        result_marker = object()
        result = result_marker
        invalid = replace(ENTRIES[-1], entry_id="LATE_SECRET_ID", currency="USD")
        with self.assertRaises(GLTrialBalanceInputError) as raised:
            result = _build(entries=ENTRIES + (invalid,))
        self.assertIs(result, result_marker)
        self.assertEqual(str(raised.exception), raised.exception.code)
        self.assertNotIn("LATE_SECRET_ID", str(raised.exception))
        self.assertNotIn("RECEIVABLE", str(raised.exception))

    def test_inputs_remain_immutable(self):
        accounts = list(ACCOUNTS)
        entries = list(ENTRIES)
        expected_accounts = list(EXPECTED_ACCOUNT_IDS)
        expected_roots = list(EXPECTED_ROOT_IDS)
        before = copy.deepcopy((accounts, entries, expected_accounts, expected_roots))

        _build(
            accounts=accounts,
            entries=entries,
            expected_account_ids=expected_accounts,
            expected_root_ids=expected_roots,
        )

        self.assertEqual((accounts, entries, expected_accounts, expected_roots), before)

    def test_duplicate_unknown_and_group_entries_fail_closed(self):
        cases = (
            (ENTRIES + (replace(ENTRIES[0]),), "duplicate_entry"),
            (
                (
                    replace(ENTRIES[0], account_id="UNKNOWN"),
                    replace(ENTRIES[1], account_id="UNKNOWN"),
                ),
                "entry_account_missing",
            ),
            (
                (
                    replace(ENTRIES[0], account_id="ASSET_ROOT"),
                    replace(ENTRIES[1], account_id="EQUITY_ROOT"),
                ),
                "group_entry_not_allowed",
            ),
        )
        for entries, expected_code in cases:
            with self.subTest(entries=entries):
                with self.assertRaises(GLTrialBalanceInputError) as raised:
                    _build(entries=entries)
                self.assertEqual(raised.exception.code, expected_code)

    def test_root_type_and_sort_contracts_fail_closed(self):
        cases = (
            (
                tuple(
                    replace(account, root_type="Liability")
                    if account.account_id == "CASH"
                    else account
                    for account in ACCOUNTS
                ),
                "root_type_mismatch",
            ),
            (
                (replace(ACCOUNTS[0], root_type="Unknown"),) + ACCOUNTS[1:],
                "root_type_invalid",
            ),
            (
                (replace(ACCOUNTS[0], sort_order=-1),) + ACCOUNTS[1:],
                "sort_order_invalid",
            ),
        )
        for accounts, expected_code in cases:
            with self.subTest(accounts=accounts):
                with self.assertRaises(GLTrialBalanceInputError) as raised:
                    _build(accounts=accounts)
                self.assertEqual(raised.exception.code, expected_code)
