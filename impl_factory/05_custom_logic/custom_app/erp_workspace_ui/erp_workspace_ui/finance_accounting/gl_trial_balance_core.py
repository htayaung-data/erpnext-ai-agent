"""Deterministic, database-independent GL / Trial Balance accounting core.

Callers own authorization, source reads, cancellation policy, snapshot
consistency, and every database or runtime concern. This module validates and
transforms only already-authorized normalized accounting inputs.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


__all__ = [
    "AccountNode",
    "AccountingAmounts",
    "GLTrialBalanceInputError",
    "NormalizedGLEntry",
    "TrialBalanceContext",
    "TrialBalanceLine",
    "TrialBalanceResult",
    "TrialBalanceScope",
    "build_trial_balance",
]


_ROOT_TYPE_ORDER = {
    "Asset": 0,
    "Liability": 1,
    "Equity": 2,
    "Income": 3,
    "Expense": 4,
}
_BALANCE_SHEET_ROOTS = frozenset({"Asset", "Liability", "Equity"})
_PROFIT_AND_LOSS_ROOTS = frozenset({"Income", "Expense"})
_NAMED_FINANCE_BOOK_SCOPE = (
    "company_default",
    "blank_unbooked",
    "null_unbooked",
)
_UNBOOKED_FINANCE_BOOK_SCOPE = (
    "blank_unbooked",
    "null_unbooked",
)


class GLTrialBalanceInputError(ValueError):
    """Fail-closed validation error with a stable non-identifying code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class TrialBalanceContext:
    company: str
    base_currency: str
    precision: int
    fiscal_year_start: date
    fiscal_year_end: date
    from_date: date
    to_date: date
    default_finance_book: str | None
    finance_book_cohort: tuple[str | None, ...]
    active_dimensions: int = 0


@dataclass(frozen=True, slots=True)
class AccountNode:
    account_id: str
    company: str
    parent_account_id: str | None
    is_group: bool
    root_type: str
    account_currency: str
    sort_order: int


@dataclass(frozen=True, slots=True)
class NormalizedGLEntry:
    entry_id: str
    company: str
    account_id: str
    posting_date: date
    debit: Decimal
    credit: Decimal
    currency: str
    finance_book: str | None
    is_opening: bool
    dimension_values: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class AccountingAmounts:
    opening_debit: Decimal
    opening_credit: Decimal
    movement_debit: Decimal
    movement_credit: Decimal
    closing_debit: Decimal
    closing_credit: Decimal


@dataclass(frozen=True, slots=True)
class TrialBalanceScope:
    company: str
    base_currency: str
    precision: int
    fiscal_year_start: date
    fiscal_year_end: date
    from_date: date
    to_date: date
    default_finance_book: str | None
    finance_book_cohort: tuple[str, ...]
    active_dimensions: int


@dataclass(frozen=True, slots=True)
class TrialBalanceLine:
    account_id: str
    parent_account_id: str | None
    is_group: bool
    root_type: str
    depth: int
    amounts: AccountingAmounts


@dataclass(frozen=True, slots=True)
class TrialBalanceResult:
    scope: TrialBalanceScope
    lines: tuple[TrialBalanceLine, ...]
    gross_totals: AccountingAmounts
    presentation_totals: AccountingAmounts


@dataclass(frozen=True, slots=True)
class _MinorAmounts:
    opening_debit: int = 0
    opening_credit: int = 0
    movement_debit: int = 0
    movement_credit: int = 0

    @property
    def closing_debit(self) -> int:
        return self.opening_debit + self.movement_debit

    @property
    def closing_credit(self) -> int:
        return self.opening_credit + self.movement_credit

    def add(self, other: _MinorAmounts) -> _MinorAmounts:
        return _MinorAmounts(
            opening_debit=self.opening_debit + other.opening_debit,
            opening_credit=self.opening_credit + other.opening_credit,
            movement_debit=self.movement_debit + other.movement_debit,
            movement_credit=self.movement_credit + other.movement_credit,
        )


def _reject(code: str) -> None:
    raise GLTrialBalanceInputError(code)


def _strict_text(value: object, code: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        _reject(code)
    return value


def _strict_sequence(value: object, code: str) -> tuple[object, ...]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        _reject(code)
    return tuple(value)


def _strict_identifier_tuple(value: object, code: str) -> tuple[str, ...]:
    items = _strict_sequence(value, code)
    if not items:
        _reject(code)
    identifiers = tuple(_strict_text(item, code) for item in items)
    if len(set(identifiers)) != len(identifiers):
        _reject(code)
    return identifiers


def _decimal_to_minor(value: object, precision: int) -> int:
    if type(value) is not Decimal or not value.is_finite() or value.is_signed():
        _reject("amount_invalid")
    sign, digits, exponent = value.as_tuple()
    if sign:
        _reject("amount_invalid")
    coefficient = 0
    for digit in digits:
        coefficient = coefficient * 10 + digit
    if coefficient == 0:
        return 0
    scaled_exponent = exponent + precision
    if scaled_exponent >= 0:
        return coefficient * (10**scaled_exponent)
    removed_places = -scaled_exponent
    if removed_places > len(digits):
        _reject("amount_precision_invalid")
    divisor = 10**removed_places
    if coefficient % divisor:
        _reject("amount_precision_invalid")
    return coefficient // divisor


def _minor_to_decimal(value: int, precision: int) -> Decimal:
    sign = 1 if value < 0 else 0
    digits = tuple(int(character) for character in str(abs(value))) if value else (0,)
    return Decimal((sign, digits, -precision))


def _to_gross_amounts(value: _MinorAmounts, precision: int) -> AccountingAmounts:
    return AccountingAmounts(
        opening_debit=_minor_to_decimal(value.opening_debit, precision),
        opening_credit=_minor_to_decimal(value.opening_credit, precision),
        movement_debit=_minor_to_decimal(value.movement_debit, precision),
        movement_credit=_minor_to_decimal(value.movement_credit, precision),
        closing_debit=_minor_to_decimal(value.closing_debit, precision),
        closing_credit=_minor_to_decimal(value.closing_credit, precision),
    )


def _to_presentation_amounts(value: _MinorAmounts, precision: int) -> AccountingAmounts:
    opening_net = value.opening_debit - value.opening_credit
    closing_net = value.closing_debit - value.closing_credit
    return AccountingAmounts(
        opening_debit=_minor_to_decimal(max(opening_net, 0), precision),
        opening_credit=_minor_to_decimal(max(-opening_net, 0), precision),
        movement_debit=_minor_to_decimal(value.movement_debit, precision),
        movement_credit=_minor_to_decimal(value.movement_credit, precision),
        closing_debit=_minor_to_decimal(max(closing_net, 0), precision),
        closing_credit=_minor_to_decimal(max(-closing_net, 0), precision),
    )


def _validate_context(context: object) -> TrialBalanceContext:
    if type(context) is not TrialBalanceContext:
        _reject("context_invalid")
    _strict_text(context.company, "company_invalid")
    _strict_text(context.base_currency, "currency_invalid")
    if context.default_finance_book is not None:
        _strict_text(context.default_finance_book, "finance_book_invalid")
    if type(context.precision) is not int or context.precision < 0:
        _reject("precision_invalid")
    if type(context.active_dimensions) is not int or context.active_dimensions != 0:
        _reject("active_dimensions_not_supported")
    boundaries = (
        context.fiscal_year_start,
        context.fiscal_year_end,
        context.from_date,
        context.to_date,
    )
    if any(type(value) is not date for value in boundaries):
        _reject("date_invalid")
    if not (
        context.fiscal_year_start
        <= context.from_date
        <= context.to_date
        <= context.fiscal_year_end
    ):
        _reject("date_range_invalid")
    cohort = _strict_sequence(context.finance_book_cohort, "finance_book_cohort_invalid")
    if context.default_finance_book is None:
        if (
            len(cohort) != 2
            or sum(type(value) is str and value == "" for value in cohort) != 1
            or sum(value is None for value in cohort) != 1
            or any(value is not None and value != "" for value in cohort)
        ):
            _reject("finance_book_cohort_invalid")
    elif (
        len(cohort) != 3
        or sum(value == context.default_finance_book for value in cohort) != 1
        or sum(type(value) is str and value == "" for value in cohort) != 1
        or sum(value is None for value in cohort) != 1
        or any(
            value is not None and value not in ("", context.default_finance_book)
            for value in cohort
        )
    ):
        _reject("finance_book_cohort_invalid")
    return context


def _validate_chart(
    context: TrialBalanceContext,
    accounts_value: object,
    expected_account_ids_value: object,
    expected_root_account_ids_value: object,
) -> tuple[
    dict[str, AccountNode],
    dict[str, tuple[str, ...]],
    dict[str, int],
    tuple[str, ...],
]:
    accounts = _strict_sequence(accounts_value, "chart_invalid")
    if not accounts:
        _reject("chart_invalid")
    expected_account_ids = _strict_identifier_tuple(
        expected_account_ids_value, "expected_accounts_invalid"
    )
    expected_root_ids = _strict_identifier_tuple(
        expected_root_account_ids_value, "expected_roots_invalid"
    )
    chart: dict[str, AccountNode] = {}
    for account in accounts:
        if type(account) is not AccountNode:
            _reject("account_invalid")
        account_id = _strict_text(account.account_id, "account_invalid")
        _strict_text(account.company, "account_invalid")
        _strict_text(account.account_currency, "account_invalid")
        if account.parent_account_id is not None:
            _strict_text(account.parent_account_id, "account_invalid")
        if type(account.is_group) is not bool:
            _reject("account_kind_invalid")
        if type(account.sort_order) is not int or account.sort_order < 0:
            _reject("sort_order_invalid")
        if account.root_type not in _ROOT_TYPE_ORDER:
            _reject("root_type_invalid")
        if account.company != context.company:
            _reject("company_mismatch")
        if account.account_currency != context.base_currency:
            _reject("currency_mismatch")
        if account_id in chart:
            _reject("duplicate_account")
        chart[account_id] = account

    if frozenset(chart) != frozenset(expected_account_ids):
        _reject("incomplete_chart")

    children_lists: dict[str, list[str]] = {account_id: [] for account_id in chart}
    for account_id, account in chart.items():
        parent_id = account.parent_account_id
        if parent_id is None:
            continue
        parent = chart.get(parent_id)
        if parent is None:
            _reject("missing_parent")
        if parent.root_type != account.root_type:
            _reject("root_type_mismatch")
        children_lists[parent_id].append(account_id)

    for start in sorted(chart):
        active: set[str] = set()
        cursor: str | None = start
        while cursor is not None:
            if cursor in active:
                _reject("hierarchy_cycle")
            active.add(cursor)
            cursor = chart[cursor].parent_account_id

    actual_roots = frozenset(
        account_id
        for account_id, account in chart.items()
        if account.parent_account_id is None
    )
    expected_roots = frozenset(expected_root_ids)
    if actual_roots != expected_roots:
        if actual_roots - expected_roots:
            _reject("orphan_account")
        _reject("expected_root_missing")

    children: dict[str, tuple[str, ...]] = {}
    for account_id, account in chart.items():
        account_children = tuple(
            sorted(
                children_lists[account_id],
                key=lambda child_id: (chart[child_id].sort_order, child_id),
            )
        )
        if account.is_group and not account_children:
            _reject("group_without_children")
        if not account.is_group and account_children:
            _reject("leaf_with_children")
        children[account_id] = account_children

    roots = sorted(
        actual_roots,
        key=lambda root_id: (
            _ROOT_TYPE_ORDER[chart[root_id].root_type],
            chart[root_id].sort_order,
            root_id,
        ),
    )
    depths: dict[str, int] = {}
    ordered_ids: list[str] = []
    stack = [(root_id, 0) for root_id in reversed(roots)]
    while stack:
        account_id, depth = stack.pop()
        if account_id in depths:
            _reject("hierarchy_cycle")
        depths[account_id] = depth
        ordered_ids.append(account_id)
        stack.extend((child_id, depth + 1) for child_id in reversed(children[account_id]))
    if frozenset(ordered_ids) != frozenset(chart):
        _reject("orphan_account")
    return chart, children, depths, tuple(ordered_ids)


def _book_tag(value: object, default_finance_book: str | None) -> str:
    if value is None:
        return "unbooked"
    if type(value) is not str:
        _reject("finance_book_cohort_invalid")
    if value == "":
        return "unbooked"
    if default_finance_book is not None and value == default_finance_book:
        return "company_default"
    _reject("finance_book_cohort_invalid")


def _validate_entry_amounts(entry: NormalizedGLEntry, precision: int) -> tuple[int, int]:
    debit = _decimal_to_minor(entry.debit, precision)
    credit = _decimal_to_minor(entry.credit, precision)
    if (debit == 0 and credit == 0) or (debit > 0 and credit > 0):
        _reject("entry_sides_invalid")
    return debit, credit


def _classify_entry(
    context: TrialBalanceContext,
    account: AccountNode,
    entry: NormalizedGLEntry,
) -> str:
    if type(entry.posting_date) is not date:
        _reject("posting_date_invalid")
    if type(entry.is_opening) is not bool:
        _reject("opening_marker_invalid")
    if entry.posting_date > context.to_date:
        _reject("posting_date_out_of_scope")
    if account.root_type in _PROFIT_AND_LOSS_ROOTS:
        if entry.is_opening or entry.posting_date < context.fiscal_year_start:
            _reject("profit_and_loss_opening_invalid")
        if entry.posting_date < context.from_date:
            return "opening"
        return "movement"
    if account.root_type not in _BALANCE_SHEET_ROOTS:
        _reject("root_type_invalid")
    if entry.is_opening or entry.posting_date < context.from_date:
        return "opening"
    return "movement"


def _load_entries(
    context: TrialBalanceContext,
    chart: dict[str, AccountNode],
    entries_value: object,
) -> tuple[dict[str, _MinorAmounts], dict[str, _MinorAmounts]]:
    entries = _strict_sequence(entries_value, "entries_invalid")
    leaf_amounts = {
        account_id: _MinorAmounts()
        for account_id, account in chart.items()
        if not account.is_group
    }
    cohort_totals = {"unbooked": _MinorAmounts()}
    if context.default_finance_book is not None:
        cohort_totals["company_default"] = _MinorAmounts()
    seen_entry_ids: set[str] = set()
    for entry in entries:
        if type(entry) is not NormalizedGLEntry:
            _reject("entry_invalid")
        entry_id = _strict_text(entry.entry_id, "entry_invalid")
        _strict_text(entry.company, "entry_invalid")
        account_id = _strict_text(entry.account_id, "entry_invalid")
        _strict_text(entry.currency, "entry_invalid")
        if entry_id in seen_entry_ids:
            _reject("duplicate_entry")
        seen_entry_ids.add(entry_id)
        account = chart.get(account_id)
        if account is None:
            _reject("entry_account_missing")
        if account.is_group:
            _reject("group_entry_not_allowed")
        if entry.company != context.company:
            _reject("company_mismatch")
        if entry.currency != context.base_currency:
            _reject("currency_mismatch")
        if type(entry.dimension_values) is not tuple or entry.dimension_values:
            _reject("dimensions_not_supported")
        book_tag = _book_tag(entry.finance_book, context.default_finance_book)
        debit, credit = _validate_entry_amounts(entry, context.precision)
        classification = _classify_entry(context, account, entry)
        if classification == "opening":
            amount = _MinorAmounts(opening_debit=debit, opening_credit=credit)
        else:
            amount = _MinorAmounts(movement_debit=debit, movement_credit=credit)
        leaf_amounts[account_id] = leaf_amounts[account_id].add(amount)
        cohort_totals[book_tag] = cohort_totals[book_tag].add(amount)
    return leaf_amounts, cohort_totals


def _assert_balanced(value: _MinorAmounts) -> None:
    if (
        value.opening_debit != value.opening_credit
        or value.movement_debit != value.movement_credit
        or value.closing_debit != value.closing_credit
    ):
        _reject("trial_balance_imbalance")


def _presentation_totals(
    values: Sequence[_MinorAmounts], precision: int
) -> AccountingAmounts:
    opening_debit = opening_credit = 0
    movement_debit = movement_credit = 0
    closing_debit = closing_credit = 0
    for value in values:
        opening_net = value.opening_debit - value.opening_credit
        closing_net = value.closing_debit - value.closing_credit
        opening_debit += max(opening_net, 0)
        opening_credit += max(-opening_net, 0)
        movement_debit += value.movement_debit
        movement_credit += value.movement_credit
        closing_debit += max(closing_net, 0)
        closing_credit += max(-closing_net, 0)
    if (
        opening_debit != opening_credit
        or movement_debit != movement_credit
        or closing_debit != closing_credit
    ):
        _reject("trial_balance_imbalance")
    return AccountingAmounts(
        opening_debit=_minor_to_decimal(opening_debit, precision),
        opening_credit=_minor_to_decimal(opening_credit, precision),
        movement_debit=_minor_to_decimal(movement_debit, precision),
        movement_credit=_minor_to_decimal(movement_credit, precision),
        closing_debit=_minor_to_decimal(closing_debit, precision),
        closing_credit=_minor_to_decimal(closing_credit, precision),
    )


def build_trial_balance(
    *,
    context: TrialBalanceContext,
    expected_account_ids: Sequence[str],
    expected_root_account_ids: Sequence[str],
    accounts: Sequence[AccountNode],
    entries: Sequence[NormalizedGLEntry],
) -> TrialBalanceResult:
    """Return one complete deterministic result or fail without partial output.

    This function has no permission, source-read, cancellation, snapshot,
    close, audit, execution, persistence, HTTP, or user-interface authority.
    """

    validated_context = _validate_context(context)
    chart, children, depths, ordered_ids = _validate_chart(
        validated_context,
        accounts,
        expected_account_ids,
        expected_root_account_ids,
    )
    leaf_amounts, cohort_totals = _load_entries(validated_context, chart, entries)

    for cohort_total in cohort_totals.values():
        _assert_balanced(cohort_total)
    leaf_values = tuple(leaf_amounts[account_id] for account_id in sorted(leaf_amounts))
    gross = _MinorAmounts()
    for value in leaf_values:
        gross = gross.add(value)
    _assert_balanced(gross)

    rollups: dict[str, _MinorAmounts] = {
        account_id: leaf_amounts.get(account_id, _MinorAmounts())
        for account_id in chart
    }
    for account_id in reversed(ordered_ids):
        parent_id = chart[account_id].parent_account_id
        if parent_id is not None:
            rollups[parent_id] = rollups[parent_id].add(rollups[account_id])

    lines = tuple(
        TrialBalanceLine(
            account_id=account_id,
            parent_account_id=chart[account_id].parent_account_id,
            is_group=chart[account_id].is_group,
            root_type=chart[account_id].root_type,
            depth=depths[account_id],
            amounts=_to_presentation_amounts(
                rollups[account_id], validated_context.precision
            ),
        )
        for account_id in ordered_ids
    )
    if len(lines) != len(chart) or {line.account_id for line in lines} != set(chart):
        _reject("incomplete_chart")

    scope = TrialBalanceScope(
        company=validated_context.company,
        base_currency=validated_context.base_currency,
        precision=validated_context.precision,
        fiscal_year_start=validated_context.fiscal_year_start,
        fiscal_year_end=validated_context.fiscal_year_end,
        from_date=validated_context.from_date,
        to_date=validated_context.to_date,
        default_finance_book=validated_context.default_finance_book,
        finance_book_cohort=(
            _UNBOOKED_FINANCE_BOOK_SCOPE
            if validated_context.default_finance_book is None
            else _NAMED_FINANCE_BOOK_SCOPE
        ),
        active_dimensions=0,
    )
    return TrialBalanceResult(
        scope=scope,
        lines=lines,
        gross_totals=_to_gross_amounts(gross, validated_context.precision),
        presentation_totals=_presentation_totals(
            leaf_values, validated_context.precision
        ),
    )
