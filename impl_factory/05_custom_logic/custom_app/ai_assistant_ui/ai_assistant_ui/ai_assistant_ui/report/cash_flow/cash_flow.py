# Copyright (c) 2026, MEET
# License: MIT

from copy import deepcopy
from datetime import timedelta

import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.utils import cstr, flt
from pypika import Order

from erpnext.accounts.report.financial_statements import (
    get_columns,
    get_cost_centers_with_children,
    get_data,
    get_filtered_list_for_consolidated_report,
    get_period_list,
    set_gl_entries_by_account,
)
from erpnext.accounts.report.profit_and_loss_statement.profit_and_loss_statement import (
    get_net_profit_loss,
)
from erpnext.accounts.utils import get_fiscal_year


def execute(filters=None):
    period_list = get_period_list(
        filters.from_fiscal_year,
        filters.to_fiscal_year,
        filters.period_start_date,
        filters.period_end_date,
        filters.filter_based_on,
        filters.periodicity,
        company=filters.company,
    )

    income = get_data(
        filters.company,
        "Income",
        "Credit",
        period_list,
        filters=filters,
        accumulated_values=filters.accumulated_values,
        ignore_closing_entries=True,
        ignore_accumulated_values_for_fy=True,
    )
    expense = get_data(
        filters.company,
        "Expense",
        "Debit",
        period_list,
        filters=filters,
        accumulated_values=filters.accumulated_values,
        ignore_closing_entries=True,
        ignore_accumulated_values_for_fy=True,
    )
    net_profit_loss = get_net_profit_loss(income, expense, period_list, filters.company)

    data = []
    summary_data = {}
    company_currency = filters.presentation_currency or frappe.get_cached_value(
        "Company", filters.company, "default_currency"
    )

    for section in get_cash_flow_sections():
        section_data = []
        data.append(
            {
                "section_name": "'" + section["section_header"] + "'",
                "parent_section": None,
                "indent": 0.0,
                "section": section["section_header"],
            }
        )

        if len(data) == 1 and net_profit_loss:
            net_profit_loss.update(
                {
                    "indent": 1,
                    "parent_section": section["section_header"],
                    "section": net_profit_loss["account"],
                }
            )
            data.append(net_profit_loss)
            section_data.append(net_profit_loss)

        for row in section["rows"]:
            row_data = get_row_data(filters.company, row, period_list, filters.accumulated_values, filters)
            row_data.update(
                {
                    "section_name": row["label"],
                    "section": row["label"],
                    "indent": 1,
                    "accounts": resolve_row_accounts(filters.company, row),
                    "parent_section": section["section_header"],
                    "currency": company_currency,
                }
            )
            data.append(row_data)
            section_data.append(row_data)

        add_total_row_account(
            data,
            section_data,
            section["section_footer"],
            period_list,
            company_currency,
            summary_data,
            filters,
        )

    net_change_in_cash = add_total_row_account(
        data, data, _("Net Change in Cash"), period_list, company_currency, summary_data, filters
    )

    if filters.show_opening_and_closing_balance:
        show_opening_and_closing_balance(data, period_list, company_currency, net_change_in_cash, filters)

    columns = get_columns(
        filters.periodicity,
        period_list,
        filters.accumulated_values,
        filters.company,
        True,
    )
    chart = get_chart_data(columns, data, company_currency)
    report_summary = get_report_summary(summary_data, company_currency)

    return columns, data, None, chart, report_summary


def get_cash_flow_sections():
    return [
        {
            "section_name": "Operations",
            "section_header": _("Cash Flow from Operations"),
            "section_footer": _("Net Cash from Operations"),
            "rows": [
                {"label": _("Depreciation"), "account_types": ["Depreciation"], "flip_sign": True},
                {"label": _("Net Change in Accounts Receivable"), "account_types": ["Receivable"]},
                {"label": _("Net Change in Trade Payables"), "account_names": ["Creditors - MMOB"]},
                {
                    "label": _("Net Change in Payroll and Accrued Expenses"),
                    "account_names": ["Payroll Payable - MMOB", "Accrued Expenses - MMOB"],
                },
                {"label": _("Net Change in Taxes Payable"), "account_names": ["Income Tax Payable - MMOB"]},
                {
                    "label": _("Net Change in GRNI / Stock Received But Not Billed"),
                    "account_names": ["Stock Received But Not Billed - MMOB"],
                },
                {"label": _("Net Change in Inventory"), "account_types": ["Stock"]},
            ],
        },
        {
            "section_name": "Investing",
            "section_header": _("Cash Flow from Investing"),
            "section_footer": _("Net Cash from Investing"),
            "rows": [
                {"label": _("Net Change in Fixed Asset"), "account_types": ["Fixed Asset"]},
            ],
        },
        {
            "section_name": "Financing",
            "section_header": _("Cash Flow from Financing"),
            "section_footer": _("Net Cash from Financing"),
            "rows": [
                {"label": _("Net Change in Equity"), "account_types": ["Equity"]},
                {
                    "label": _("Net Change in Borrowings"),
                    "account_names": [
                        "Bank Overdraft Account - MMOB",
                        "Bank Loan - KBZ - MMOB",
                        "Unsecured Loans - MMOB",
                        "Secured Loans - MMOB",
                    ],
                },
            ],
        },
    ]


def resolve_row_accounts(company, row):
    if row.get("account_names"):
        return row["account_names"]

    account_types = row.get("account_types") or []
    if not account_types:
        return []

    return frappe.get_all(
        "Account",
        filters={
            "company": company,
            "account_type": ["in", account_types],
            "is_group": 0,
        },
        pluck="name",
    )


def get_row_data(company, row, period_list, accumulated_values, filters):
    data = {}
    total = 0

    for period in period_list:
        start_date = get_start_date(period, accumulated_values, company)
        local_filters = deepcopy(filters)
        local_filters.start_date = start_date
        local_filters.end_date = period["to_date"]

        amount = get_balance_change(
            company,
            local_filters,
            account_types=row.get("account_types"),
            account_names=row.get("account_names"),
        )
        if row.get("flip_sign"):
            amount *= -1

        total += amount
        data.setdefault(period["key"], amount)

    data["total"] = total
    return data


def get_balance_change(company, filters=None, account_types=None, account_names=None):
    filters = frappe._dict(filters or {})
    params = {
        "company": company,
        "start_date": filters.start_date,
        "end_date": filters.end_date,
    }

    cond = ""
    if filters.include_default_book_entries:
        company_fb = frappe.get_cached_value("Company", company, "default_finance_book")
        cond = """ and (gle.finance_book in ({}, {}, '') or gle.finance_book is null)
        """.format(
            frappe.db.escape(filters.finance_book),
            frappe.db.escape(company_fb),
        )
    else:
        cond = " and (gle.finance_book in (%s, '') or gle.finance_book is null)" % (
            frappe.db.escape(cstr(filters.finance_book))
        )

    if filters.get("cost_center"):
        params["cost_center"] = tuple(get_cost_centers_with_children(filters.cost_center))
        cond += " and gle.cost_center in %(cost_center)s"

    account_conditions = []
    if account_types:
        params["account_types"] = tuple(account_types)
        account_conditions.append("acc.account_type in %(account_types)s")
    if account_names:
        params["account_names"] = tuple(account_names)
        account_conditions.append("acc.name in %(account_names)s")

    if not account_conditions:
        return 0

    gl_sum = frappe.db.sql_list(
        f"""
        select sum(gle.credit) - sum(gle.debit)
        from `tabGL Entry` gle
        inner join `tabAccount` acc on acc.name = gle.account
        where gle.company = %(company)s
          and gle.posting_date >= %(start_date)s
          and gle.posting_date <= %(end_date)s
          and ifnull(gle.is_opening, 'No') = 'No'
          and gle.voucher_type != 'Period Closing Voucher'
          and ({' or '.join(account_conditions)})
          {cond}
        """,
        params,
    )

    return gl_sum[0] if gl_sum and gl_sum[0] else 0


def get_start_date(period, accumulated_values, company):
    if not accumulated_values and period.get("from_date"):
        return period["from_date"]

    start_date = period["year_start_date"]
    if accumulated_values:
        start_date = get_fiscal_year(period.to_date, company=company)[1]

    return start_date


def add_total_row_account(out, data, label, period_list, currency, summary_data, filters, consolidated=False):
    total_row = {
        "section_name": "'" + _("{0}").format(label) + "'",
        "section": "'" + _("{0}").format(label) + "'",
        "currency": currency,
    }

    summary_data[label] = 0

    if filters.get("accumulated_values"):
        period_list = [period_list[-1]]

    if filters.get("accumulated_in_group_company"):
        period_list = get_filtered_list_for_consolidated_report(filters, period_list)

    for row in data:
        if row.get("parent_section"):
            for period in period_list:
                key = period if consolidated else period["key"]
                total_row.setdefault(key, 0.0)
                total_row[key] += row.get(key, 0.0)
                summary_data[label] += row.get(key)

            total_row.setdefault("total", 0.0)
            total_row["total"] += row["total"]

    out.append(total_row)
    out.append({})
    return total_row


def show_opening_and_closing_balance(out, period_list, currency, net_change_in_cash, filters):
    opening_balance = {"section_name": "Opening", "section": "Opening", "currency": currency}
    closing_balance = {
        "section_name": "Closing (Opening + Total)",
        "section": "Closing (Opening + Total)",
        "currency": currency,
    }

    opening_amount = get_opening_balance(filters.company, period_list, filters) or 0.0
    running_total = opening_amount

    for i, period in enumerate(period_list):
        key = period["key"]
        change = net_change_in_cash.get(key, 0.0)
        opening_balance[key] = opening_amount if i == 0 else running_total
        running_total += change
        closing_balance[key] = running_total

    opening_balance["total"] = opening_balance[period_list[0]["key"]]
    closing_balance["total"] = closing_balance[period_list[-1]["key"]]

    out.extend([opening_balance, net_change_in_cash, closing_balance, {}])


def get_opening_balance(company, period_list, filters):
    _, previous_day = get_opening_range_using_fiscal_year(company, period_list)
    opening_rows = frappe.db.sql_list(
        """
        select sum(gle.debit) - sum(gle.credit)
        from `tabGL Entry` gle
        inner join `tabAccount` acc on acc.name = gle.account
        where gle.company = %s
          and gle.posting_date <= %s
          and acc.account_type in ('Bank', 'Cash')
        """,
        (company, previous_day),
    )
    return opening_rows[0] if opening_rows and opening_rows[0] else 0


def get_net_income(company, period_list, filters):
    gl_entries_by_account_for_income, gl_entries_by_account_for_expense = {}, {}
    income, expense = 0.0, 0.0
    from_date, to_date = get_opening_range_using_fiscal_year(company, period_list)

    for root_type in ["Income", "Expense"]:
        for root in frappe.db.sql(
            """select lft, rgt from tabAccount
               where root_type=%s and ifnull(parent_account, '') = ''""",
            root_type,
            as_dict=1,
        ):
            set_gl_entries_by_account(
                company,
                from_date,
                to_date,
                filters,
                gl_entries_by_account_for_income if root_type == "Income" else gl_entries_by_account_for_expense,
                root.lft,
                root.rgt,
                root_type=root_type,
                ignore_closing_entries=True,
            )

    for entries in gl_entries_by_account_for_income.values():
        for entry in entries:
            if entry.posting_date <= to_date:
                income = flt(income + ((entry.debit - entry.credit) * -1), 2)

    for entries in gl_entries_by_account_for_expense.values():
        for entry in entries:
            if entry.posting_date <= to_date:
                expense = flt(expense + (entry.debit - entry.credit), 2)

    return income - expense


def get_opening_range_using_fiscal_year(company, period_list):
    first_from_date = period_list[0]["from_date"]
    previous_day = first_from_date - timedelta(days=1)

    fiscal_year = DocType("Fiscal Year")
    fiscal_year_company = DocType("Fiscal Year Company")

    earliest_fy = (
        frappe.qb.from_(fiscal_year)
        .join(fiscal_year_company)
        .on(fiscal_year_company.parent == fiscal_year.name)
        .select(fiscal_year.year_start_date)
        .where(fiscal_year_company.company == company)
        .orderby(fiscal_year.year_start_date, order=Order.asc)
        .limit(1)
    ).run(as_dict=True)

    if not earliest_fy:
        frappe.throw(_("Not able to find the earliest Fiscal Year for the given company."))

    company_start_date = earliest_fy[0]["year_start_date"]
    return company_start_date, previous_day


def get_report_summary(summary_data, currency):
    report_summary = []
    for label, value in summary_data.items():
        report_summary.append(
            {"value": value, "label": label, "datatype": "Currency", "currency": currency}
        )
    return report_summary


def get_chart_data(columns, data, currency):
    labels = [d.get("label") for d in columns[2:]]
    datasets = [
        {
            "name": section.get("section").replace("'", ""),
            "values": [section.get(d.get("fieldname")) for d in columns[2:]],
        }
        for section in data
        if section.get("parent_section") is None and section.get("currency")
    ]
    datasets = datasets[:-2]

    chart = {"data": {"labels": labels, "datasets": datasets}, "type": "bar"}
    chart["fieldtype"] = "Currency"
    chart["options"] = "currency"
    chart["currency"] = currency
    return chart
