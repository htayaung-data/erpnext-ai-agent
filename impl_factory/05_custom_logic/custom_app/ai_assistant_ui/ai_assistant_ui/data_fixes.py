from __future__ import annotations

import json
from dataclasses import asdict, dataclass
import inspect
from statistics import median
from typing import Any

import frappe
from frappe.model.rename_doc import rename_doc
from frappe.utils import add_days, add_months, cint, flt, get_last_day, getdate
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry


@dataclass
class PayrollResult:
    created: list[dict[str, Any]]
    skipped: list[dict[str, Any]]


def _eligible_employees(period_end):
    employees = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=[
            "name",
            "employee_name",
            "department",
            "designation",
            "branch",
            "date_of_joining",
        ],
        order_by="name asc",
    )
    result = []
    for employee in employees:
        date_of_joining = getdate(employee.date_of_joining) if employee.date_of_joining else None
        if not date_of_joining or date_of_joining > period_end:
            continue
        result.append(employee)
    return result


def apply_fy2526_realism_polish_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    currency = "MMK"
    results: dict[str, Any] = {
        "salary_slips": [],
        "customer_group_fixes": [],
        "receivable_payments": [],
        "payable_payments": [],
        "failed": [],
    }

    payroll_months = [
        ("2025-04-01", "2025-04-30", "2025-04-30"),
        ("2025-05-01", "2025-05-31", "2025-05-31"),
        ("2025-06-01", "2025-06-30", "2025-06-30"),
        ("2025-07-01", "2025-07-31", "2025-07-31"),
        ("2025-08-01", "2025-08-31", "2025-08-31"),
        ("2025-09-01", "2025-09-30", "2025-09-30"),
        ("2025-10-01", "2025-10-31", "2025-10-31"),
        ("2025-11-01", "2025-11-30", "2025-11-30"),
        ("2025-12-01", "2025-12-31", "2025-12-31"),
        ("2026-01-01", "2026-01-31", "2026-01-31"),
        ("2026-02-01", "2026-02-28", "2026-02-28"),
        ("2026-03-01", "2026-03-31", "2026-03-31"),
    ]

    for period_start, period_end, posting_date in payroll_months:
        try:
            outcome = create_salary_slips_for_month(
                period_start=period_start,
                period_end=period_end,
                posting_date=posting_date,
                company=company,
                currency=currency,
            )
            results["salary_slips"].append(
                {
                    "period_start": period_start,
                    "period_end": period_end,
                    "posting_date": posting_date,
                    "created": len(outcome["created"]),
                    "skipped": len(outcome["skipped"]),
                }
            )
        except Exception as exc:
            results["failed"].append(
                {"label": f"salary_{period_start}", "stage": "salary_slips", "error": str(exc)}
            )

    customer_group_fix_targets = [
        ("aaaa", "Retail"),
    ]
    for customer_name, customer_group in customer_group_fix_targets:
        if not frappe.db.exists("Customer", customer_name):
            continue
        current_group = frappe.db.get_value("Customer", customer_name, "customer_group")
        if current_group:
            continue
        frappe.db.set_value("Customer", customer_name, "customer_group", customer_group, update_modified=False)
        results["customer_group_fixes"].append(
            {"customer": customer_name, "customer_group": customer_group}
        )
    frappe.db.commit()

    receivable_specs = [
        ("Bayint Naung Wholesale Mobile", "2025-12-31", "2026-02-05", 3500000),
        ("Capital Telecom (NPT)", "2025-12-31", "2026-02-08", 4000000),
        ("35th Street Mobile Wholesale", "2025-12-31", "2026-02-10", 5000000),
        ("Ko Nay Lin Mobile Center", "2025-12-31", "2026-02-12", 3000000),
        ("Latha Mobile Wholesale", "2025-12-31", "2026-02-14", 3000000),
        ("Mandalay Accessories Wholesale", "2025-12-31", "2026-02-18", 2500000),
        ("Hledan Phone Hub", "2025-12-31", "2026-02-20", 2000000),
        ("Taunggyi City Mobile", "2025-12-31", "2026-02-22", 2000000),
    ]
    for customer, cutoff_date, posting_date, amount in receivable_specs:
        invoice_name = _find_outstanding_sales_invoice(customer, cutoff_date)
        if not invoice_name:
            results["failed"].append(
                {
                    "label": f"receivable_{customer}",
                    "stage": "invoice_lookup",
                    "error": "sales_invoice_missing",
                }
            )
            continue

        try:
            payment_info = _apply_targeted_partial_payment(
                "Sales Invoice",
                invoice_name,
                posting_date,
                amount,
            )
            if payment_info:
                results["receivable_payments"].append(payment_info)
                frappe.db.commit()
        except Exception as exc:
            frappe.db.rollback()
            results["failed"].append(
                {
                    "label": f"receivable_{customer}",
                    "stage": "payment",
                    "error": str(exc),
                }
            )

    payable_specs = [
        ("Golden Dragon Trading Co. Ltd.", "2025-12-31", "2026-02-06", 5000000),
        ("Myanmar Tech Import Services", "2025-12-31", "2026-02-09", 6000000),
        ("Sunflower Accessories Co.", "2025-12-31", "2026-02-13", 4500000),
        ("Shwe Taung Electronics Supply", "2025-12-31", "2026-02-16", 3000000),
    ]
    for supplier, cutoff_date, posting_date, amount in payable_specs:
        invoice_name = _find_outstanding_purchase_invoice(supplier, cutoff_date)
        if not invoice_name:
            results["failed"].append(
                {
                    "label": f"payable_{supplier}",
                    "stage": "invoice_lookup",
                    "error": "purchase_invoice_missing",
                }
            )
            continue

        try:
            payment_info = _apply_targeted_partial_payment(
                "Purchase Invoice",
                invoice_name,
                posting_date,
                amount,
            )
            if payment_info:
                results["payable_payments"].append(payment_info)
                frappe.db.commit()
        except Exception as exc:
            frappe.db.rollback()
            results["failed"].append(
                {
                    "label": f"payable_{supplier}",
                    "stage": "payment",
                    "error": str(exc),
                }
            )

    return results


def create_salary_slips_for_month(
    period_start: str,
    period_end: str,
    posting_date: str,
    company: str,
    currency: str = "MMK",
    excluded_employees: list[str] | None = None,
) -> dict[str, Any]:
    excluded = set(excluded_employees or [])
    start = getdate(period_start)
    end = getdate(period_end)
    posting = str(getdate(posting_date))
    outcome = PayrollResult(created=[], skipped=[])

    for employee in _eligible_employees(end):
        if employee.name in excluded:
            outcome.skipped.append({"employee": employee.name, "reason": "excluded"})
            continue

        existing = frappe.db.exists(
            "Salary Slip",
            {
                "employee": employee.name,
                "posting_date": posting,
                "docstatus": ["in", [0, 1]],
            },
        )
        if existing:
            outcome.skipped.append(
                {"employee": employee.name, "reason": "existing", "document": existing}
            )
            continue

        assignments = frappe.get_all(
            "Salary Structure Assignment",
            filters={
                "employee": employee.name,
                "from_date": ["<=", str(end)],
            },
            fields=["name", "salary_structure", "base", "from_date"],
            order_by="from_date desc",
            limit=1,
        )
        if not assignments:
            outcome.skipped.append({"employee": employee.name, "reason": "no_assignment"})
            continue

        assignment = assignments[0]
        base = float(assignment.base or 0)
        if base <= 0:
            outcome.skipped.append({"employee": employee.name, "reason": "zero_base"})
            continue

        date_of_joining = getdate(employee.date_of_joining)
        slip_start = start
        total_days = (end - start).days + 1
        payment_days = total_days if date_of_joining <= start else (end - date_of_joining).days + 1
        amount = base if payment_days == total_days else int(round((base / 30.0) * payment_days / 1000.0) * 1000)

        slip = frappe.get_doc(
            {
                "doctype": "Salary Slip",
                "employee": employee.name,
                "employee_name": employee.employee_name,
                "company": company,
                "department": employee.department,
                "designation": employee.designation,
                "branch": employee.branch,
                "posting_date": posting,
                "currency": currency,
                "payroll_frequency": "Monthly",
                "start_date": str(slip_start),
                "end_date": str(end),
                "salary_structure": assignment.salary_structure,
                "total_working_days": total_days,
                "payment_days": payment_days,
                "gross_pay": amount,
                "base_gross_pay": amount,
                "total_deduction": 0,
                "base_total_deduction": 0,
                "net_pay": amount,
                "base_net_pay": amount,
                "rounded_total": amount,
                "base_rounded_total": amount,
                "earnings": [
                    {
                        "salary_component": "Basic",
                        "abbr": "B",
                        "amount": amount,
                        "default_amount": base,
                        "depends_on_payment_days": 1,
                        "is_tax_applicable": 1,
                        "do_not_include_in_total": 0,
                        "do_not_include_in_accounts": 0,
                        "amount_based_on_formula": 0,
                    }
                ],
            }
        )
        slip.insert(ignore_permissions=True)
        slip.submit()
        outcome.created.append(
            {
                "salary_slip": slip.name,
                "employee": employee.name,
                "amount": amount,
                "start_date": str(slip_start),
                "end_date": str(end),
            }
        )

    frappe.db.commit()
    return asdict(outcome)


def _target_salary_slip_period_name(employee: str, posting_date: str) -> str:
    posting = getdate(posting_date)
    return f"Sal Slip/{employee}/{posting.strftime('%Y-%m')}"


def audit_salary_slip_header_residue() -> dict[str, Any]:
    rows = frappe.db.sql(
        """
        select
            name,
            employee,
            employee_name,
            posting_date,
            salary_structure,
            net_pay,
            docstatus
        from `tabSalary Slip`
        where name like 'Sal Slip/None/%'
        order by posting_date, creation, name
        """,
        as_dict=True,
    )

    by_month: dict[str, int] = {}
    missing_employee = []
    sample = []
    for row in rows:
        period_key = getdate(row.posting_date).strftime("%Y-%m") if row.posting_date else "unknown"
        by_month[period_key] = by_month.get(period_key, 0) + 1
        if not row.employee:
            missing_employee.append(row.name)
        if len(sample) < 12:
            sample.append(
                {
                    "name": row.name,
                    "employee": row.employee,
                    "posting_date": str(row.posting_date),
                    "target_name": _target_salary_slip_period_name(row.employee, row.posting_date)
                    if row.employee and row.posting_date
                    else None,
                }
            )

    return {
        "legacy_named_slips": len(rows),
        "months": by_month,
        "missing_employee_links": missing_employee,
        "sample": sample,
    }


def apply_salary_slip_header_hygiene() -> dict[str, Any]:
    rows = frappe.db.sql(
        """
        select
            name,
            employee,
            posting_date,
            docstatus
        from `tabSalary Slip`
        where name like 'Sal Slip/None/%'
        order by posting_date, creation, name
        """,
        as_dict=True,
    )

    result: dict[str, Any] = {
        "renamed": [],
        "skipped": [],
        "failed": [],
    }

    for row in rows:
        if not row.employee:
            result["skipped"].append(
                {
                    "salary_slip": row.name,
                    "reason": "missing_employee",
                }
            )
            continue

        if not row.posting_date:
            result["skipped"].append(
                {
                    "salary_slip": row.name,
                    "reason": "missing_posting_date",
                }
            )
            continue

        target_name = _target_salary_slip_period_name(row.employee, row.posting_date)
        if row.name == target_name:
            result["skipped"].append(
                {
                    "salary_slip": row.name,
                    "reason": "already_clean",
                }
            )
            continue

        existing = frappe.db.exists("Salary Slip", target_name)
        if existing:
            result["failed"].append(
                {
                    "salary_slip": row.name,
                    "target_name": target_name,
                    "error": "target_name_exists",
                }
            )
            continue

        try:
            rename_doc(
                "Salary Slip",
                row.name,
                target_name,
                force=True,
                merge=False,
                ignore_permissions=True,
                show_alert=False,
            )
            result["renamed"].append(
                {
                    "old_name": row.name,
                    "new_name": target_name,
                    "employee": row.employee,
                    "posting_date": str(row.posting_date),
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "salary_slip": row.name,
                    "target_name": target_name,
                    "error": str(exc),
                }
            )

    frappe.db.commit()
    result["summary"] = {
        "renamed_count": len(result["renamed"]),
        "skipped_count": len(result["skipped"]),
        "failed_count": len(result["failed"]),
    }
    return result


def recreate_salary_slip_for_employee(
    employee: str,
    period_start: str,
    period_end: str,
    posting_date: str,
    company: str,
    currency: str = "MMK",
) -> dict[str, Any]:
    start = getdate(period_start)
    end = getdate(period_end)
    posting = str(getdate(posting_date))

    existing = frappe.get_all(
        "Salary Slip",
        filters={"employee": employee, "posting_date": posting, "docstatus": ["in", [0, 1]]},
        pluck="name",
    )
    for name in existing:
        slip = frappe.get_doc("Salary Slip", name)
        if slip.docstatus == 1:
            slip.cancel()
        frappe.delete_doc("Salary Slip", name, force=1, ignore_permissions=True)

    employee_doc = frappe.get_doc("Employee", employee)
    assignments = frappe.get_all(
        "Salary Structure Assignment",
        filters={"employee": employee, "from_date": ["<=", str(end)]},
        fields=["salary_structure", "base"],
        order_by="from_date desc",
        limit=1,
    )
    if not assignments:
        raise frappe.ValidationError(f"No salary structure assignment found for {employee}")

    assignment = assignments[0]
    base = float(assignment.base or 0)
    total_days = (end - start).days + 1
    date_of_joining = getdate(employee_doc.date_of_joining)
    payment_days = total_days if date_of_joining <= start else (end - date_of_joining).days + 1
    amount = base if payment_days == total_days else int(round((base / 30.0) * payment_days / 1000.0) * 1000)

    slip = frappe.get_doc(
        {
            "doctype": "Salary Slip",
            "employee": employee_doc.name,
            "employee_name": employee_doc.employee_name,
            "company": company,
            "department": employee_doc.department,
            "designation": employee_doc.designation,
            "branch": employee_doc.branch,
            "posting_date": posting,
            "currency": currency,
            "payroll_frequency": "Monthly",
            "start_date": str(start),
            "end_date": str(end),
            "salary_structure": assignment.salary_structure,
            "total_working_days": total_days,
            "payment_days": payment_days,
            "gross_pay": amount,
            "base_gross_pay": amount,
            "total_deduction": 0,
            "base_total_deduction": 0,
            "net_pay": amount,
            "base_net_pay": amount,
            "rounded_total": amount,
            "base_rounded_total": amount,
            "earnings": [
                {
                    "salary_component": "Basic",
                    "abbr": "B",
                    "amount": amount,
                    "default_amount": base,
                    "depends_on_payment_days": 1,
                    "is_tax_applicable": 1,
                    "do_not_include_in_total": 0,
                    "do_not_include_in_accounts": 0,
                    "amount_based_on_formula": 0,
                }
            ],
        }
    )
    slip.insert(ignore_permissions=True)
    slip.submit()
    frappe.db.commit()
    return {
        "salary_slip": slip.name,
        "employee": employee,
        "amount": amount,
        "payment_days": payment_days,
        "total_working_days": total_days,
    }


def _create_sales_invoice(defn: dict[str, Any]) -> str:
    existing_invoices = frappe.get_all(
        "Sales Invoice",
        filters={
            "customer": defn["customer"],
            "posting_date": defn["posting_date"],
            "docstatus": 1,
        },
        fields=["name", "grand_total"],
        limit=10,
    )
    expected_total = int(round(defn["expected_total"]))
    for invoice in existing_invoices:
        if int(round(invoice.grand_total or 0)) == expected_total:
            return invoice.name

    debit_to = defn.get("debit_to") or frappe.get_cached_value(
        "Company", defn["company"], "default_receivable_account"
    )
    if not debit_to:
        raise frappe.ValidationError(f"No receivable account found for {defn['company']}")

    posting_time = defn.get("posting_time", "10:00:00")
    cost_center = defn.get("cost_center", "Main - MMOB")
    doc = frappe.get_doc(
        {
            "doctype": "Sales Invoice",
            "customer": defn["customer"],
            "company": defn["company"],
            "posting_date": defn["posting_date"],
            "posting_time": posting_time,
            "set_posting_time": 1,
            "due_date": defn["due_date"],
            "cost_center": cost_center,
            "currency": "MMK",
            "conversion_rate": 1.0,
            "selling_price_list": "Standard Selling",
            "price_list_currency": "MMK",
            "plc_conversion_rate": 1.0,
            "debit_to": debit_to,
            "party_account_currency": "MMK",
            "ignore_default_payment_terms_template": 1,
            "set_warehouse": defn["warehouse"],
            "update_stock": 1,
            "payment_schedule": [
                {
                    "due_date": defn["due_date"],
                    "payment_amount": defn["expected_total"],
                }
            ],
            "items": [
                {
                    "item_code": item["item_code"],
                    "qty": item["qty"],
                    "rate": item["rate"],
                    "income_account": item.get("income_account", "Sales - MMOB"),
                    "expense_account": item.get("expense_account", "Cost of Goods Sold - MMOB"),
                    "warehouse": item.get("warehouse", defn["warehouse"]),
                    "cost_center": item.get("cost_center", cost_center),
                }
                for item in defn["items"]
            ],
        }
    )
    doc.insert(ignore_permissions=True)
    doc.submit()
    return doc.name


def _create_purchase_invoice(defn: dict[str, Any]) -> str:
    existing_invoices = frappe.get_all(
        "Purchase Invoice",
        filters={
            "supplier": defn["supplier"],
            "posting_date": defn["posting_date"],
            "docstatus": 1,
        },
        fields=["name", "grand_total"],
        limit=10,
    )
    expected_total = int(round(defn["expected_total"]))
    for invoice in existing_invoices:
        if int(round(invoice.grand_total or 0)) == expected_total:
            return invoice.name

    posting_time = defn.get("posting_time", "11:00:00")
    cost_center = defn.get("cost_center", "Main - MMOB")
    doc = frappe.get_doc(
        {
            "doctype": "Purchase Invoice",
            "supplier": defn["supplier"],
            "company": defn["company"],
            "posting_date": defn["posting_date"],
            "posting_time": posting_time,
            "set_posting_time": 1,
            "due_date": defn["due_date"],
            "cost_center": cost_center,
            "currency": "MMK",
            "conversion_rate": 1.0,
            "buying_price_list": "Standard Buying",
            "price_list_currency": "MMK",
            "plc_conversion_rate": 1.0,
            "ignore_pricing_rule": 1,
            "ignore_default_payment_terms_template": 1,
            "party_account_currency": "MMK",
            "update_stock": 1,
            "payment_schedule": [
                {
                    "due_date": defn["due_date"],
                    "payment_amount": defn["expected_total"],
                }
            ],
            "items": [
                {
                    "item_code": item["item_code"],
                    "qty": item["qty"],
                    "rate": item["rate"],
                    "warehouse": item["warehouse"],
                    "expense_account": item.get("expense_account", "Stock Received But Not Billed - MMOB"),
                    "cost_center": item.get("cost_center", cost_center),
                }
                for item in defn["items"]
            ],
        }
    )
    doc.insert(ignore_permissions=True)
    doc.submit()
    return doc.name


def _find_submitted_purchase_order(supplier: str, transaction_date: str, expected_total: float) -> str | None:
    existing_orders = frappe.get_all(
        "Purchase Order",
        filters={
            "supplier": supplier,
            "transaction_date": transaction_date,
            "docstatus": 1,
        },
        fields=["name", "grand_total"],
        limit=10,
    )
    expected_total = int(round(expected_total))
    for order in existing_orders:
        if int(round(order.grand_total or 0)) == expected_total:
            return order.name
    return None


def _create_purchase_order(defn: dict[str, Any]) -> str:
    existing_name = _find_submitted_purchase_order(
        defn["supplier"],
        defn["transaction_date"],
        defn["expected_total"],
    )
    if existing_name:
        return existing_name

    doc = frappe.get_doc(
        {
            "doctype": "Purchase Order",
            "supplier": defn["supplier"],
            "company": defn["company"],
            "transaction_date": defn["transaction_date"],
            "schedule_date": defn.get("schedule_date", defn["transaction_date"]),
            "currency": "MMK",
            "conversion_rate": 1.0,
            "buying_price_list": defn.get("buying_price_list", "Standard Buying - MMOB"),
            "price_list_currency": "MMK",
            "plc_conversion_rate": 1.0,
            "ignore_default_payment_terms_template": 1,
            "set_warehouse": defn.get("set_warehouse"),
            "remarks": defn.get("remarks"),
            "items": [
                {
                    "item_code": item["item_code"],
                    "qty": item["qty"],
                    "warehouse": item["warehouse"],
                    "schedule_date": item.get("schedule_date", defn.get("schedule_date", defn["transaction_date"])),
                    "uom": "Nos",
                    "conversion_factor": 1.0,
                    "price_list_rate": item["rate"],
                    "rate": item["rate"],
                }
                for item in defn["items"]
            ],
        }
    )
    doc.insert(ignore_permissions=True)
    doc.submit()
    return doc.name


def _find_submitted_purchase_receipt(supplier: str, supplier_delivery_note: str) -> str | None:
    names = frappe.get_all(
        "Purchase Receipt",
        filters={
            "supplier": supplier,
            "supplier_delivery_note": supplier_delivery_note,
            "docstatus": 1,
        },
        pluck="name",
        limit=1,
    )
    return names[0] if names else None


def _create_purchase_receipt_from_order(purchase_order_name: str, defn: dict[str, Any]) -> str:
    existing_name = _find_submitted_purchase_receipt(
        defn["supplier"],
        defn["supplier_delivery_note"],
    )
    if existing_name:
        return existing_name

    from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt

    receipt = make_purchase_receipt(purchase_order_name)
    receipt.set_posting_time = 1
    receipt.posting_date = defn["posting_date"]
    receipt.posting_time = defn.get("posting_time", "11:30:00")
    receipt.supplier_delivery_note = defn["supplier_delivery_note"]
    receipt.remarks = defn.get("remarks")
    receipt.flags.ignore_permissions = True
    receipt.insert(ignore_permissions=True)
    receipt.submit()
    return receipt.name


def _find_submitted_purchase_invoice_by_bill(supplier: str, bill_no: str) -> str | None:
    names = frappe.get_all(
        "Purchase Invoice",
        filters={
            "supplier": supplier,
            "bill_no": bill_no,
            "docstatus": 1,
        },
        pluck="name",
        limit=1,
    )
    return names[0] if names else None


def _create_purchase_invoice_from_receipt(
    purchase_receipt_name: str,
    supplier: str,
    payment_terms_template: str | None,
    defn: dict[str, Any],
) -> str:
    existing_name = _find_submitted_purchase_invoice_by_bill(supplier, defn["bill_no"])
    if existing_name:
        return existing_name

    from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice

    invoice = make_purchase_invoice(purchase_receipt_name)
    invoice.set_posting_time = 1
    invoice.posting_date = defn["posting_date"]
    invoice.posting_time = defn.get("posting_time", "14:00:00")
    invoice.bill_no = defn["bill_no"]
    invoice.bill_date = defn.get("bill_date", defn["posting_date"])
    invoice.ignore_default_payment_terms_template = 1
    invoice.payment_terms_template = None
    invoice.due_date = defn["due_date"]
    invoice.set(
        "payment_schedule",
        [
            {
                "due_date": defn["due_date"],
                "payment_amount": invoice.rounded_total or invoice.grand_total,
            }
        ],
    )
    invoice.remarks = defn.get("remarks")
    invoice.flags.ignore_permissions = True
    invoice.insert(ignore_permissions=True)
    invoice.submit()
    return invoice.name


def _find_submitted_landed_cost_voucher(
    purchase_receipt_name: str,
    posting_date: str,
    total_taxes_and_charges: float,
) -> str | None:
    rows = frappe.db.sql(
        """
        select lcv.name
        from `tabLanded Cost Voucher` lcv
        inner join `tabLanded Cost Purchase Receipt` lpr on lpr.parent = lcv.name
        where lcv.docstatus = 1
          and lcv.posting_date = %(posting_date)s
          and lpr.receipt_document_type = 'Purchase Receipt'
          and lpr.receipt_document = %(purchase_receipt)s
          and round(lcv.total_taxes_and_charges, 0) = %(total_taxes)s
        limit 1
        """,
        {
            "posting_date": posting_date,
            "purchase_receipt": purchase_receipt_name,
            "total_taxes": int(round(total_taxes_and_charges)),
        },
        as_dict=True,
    )
    return rows[0]["name"] if rows else None


def _create_landed_cost_voucher(defn: dict[str, Any]) -> str:
    total_taxes = sum(int(round(row["amount"])) for row in defn["taxes"])
    existing_name = _find_submitted_landed_cost_voucher(
        defn["purchase_receipt"],
        defn["posting_date"],
        total_taxes,
    )
    if existing_name:
        return existing_name

    doc = frappe.get_doc(
        {
            "doctype": "Landed Cost Voucher",
            "company": defn["company"],
            "posting_date": defn["posting_date"],
            "distribute_charges_based_on": defn.get("distribute_charges_based_on", "Amount"),
            "purchase_receipts": [
                {
                    "receipt_document_type": "Purchase Receipt",
                    "receipt_document": defn["purchase_receipt"],
                }
            ],
            "taxes": [
                {
                    "expense_account": row.get("expense_account", "Expenses Included In Valuation - MMOB"),
                    "description": row["description"],
                    "amount": row["amount"],
                    "exchange_rate": row.get("exchange_rate", 1.0),
                    "account_currency": row.get("account_currency", "MMK"),
                }
                for row in defn["taxes"]
            ],
        }
    )
    doc.get_items_from_purchase_receipts()
    doc.insert(ignore_permissions=True)
    doc.submit()
    return doc.name


def _find_submitted_material_transfer(
    posting_date: str,
    item_code: str,
    source_warehouse: str,
    target_warehouse: str,
    qty: float,
) -> str | None:
    rows = frappe.db.sql(
        """
        select distinct se.name
        from `tabStock Entry` se
        inner join `tabStock Entry Detail` sed on sed.parent = se.name
        where se.docstatus = 1
          and se.posting_date = %s
          and se.stock_entry_type = 'Material Transfer'
          and sed.item_code = %s
          and ifnull(sed.s_warehouse, '') = %s
          and ifnull(sed.t_warehouse, '') = %s
          and abs(ifnull(sed.qty, 0) - %s) < 0.0001
        order by se.creation asc
        limit 1
        """,
        (posting_date, item_code, source_warehouse, target_warehouse, qty),
        as_dict=True,
    )
    return rows[0]["name"] if rows else None


def _create_material_transfer(defn: dict[str, Any]) -> str:
    existing_name = _find_submitted_material_transfer(
        defn["posting_date"],
        defn["item_code"],
        defn["source_warehouse"],
        defn["target_warehouse"],
        defn["qty"],
    )
    if existing_name:
        return existing_name

    doc = frappe.get_doc(
        {
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Transfer",
            "company": defn["company"],
            "posting_date": defn["posting_date"],
            "posting_time": defn.get("posting_time", "17:30:00"),
            "set_posting_time": 1,
            "remarks": defn.get("remarks"),
            "items": [
                {
                    "item_code": defn["item_code"],
                    "qty": defn["qty"],
                    "uom": defn.get("uom", "Nos"),
                    "conversion_factor": 1.0,
                    "s_warehouse": defn["source_warehouse"],
                    "t_warehouse": defn["target_warehouse"],
                }
            ],
        }
    )
    doc.insert(ignore_permissions=True)
    doc.submit()
    return doc.name


def _find_submitted_journal_entry_by_remark(user_remark: str) -> str | None:
    names = frappe.get_all(
        "Journal Entry",
        filters={
            "user_remark": user_remark,
            "docstatus": 1,
        },
        pluck="name",
        limit=1,
    )
    return names[0] if names else None


def _create_simple_journal_entry(defn: dict[str, Any]) -> str:
    existing_name = _find_submitted_journal_entry_by_remark(defn["user_remark"])
    if existing_name:
        return existing_name

    doc = frappe.get_doc(
        {
            "doctype": "Journal Entry",
            "voucher_type": defn.get("voucher_type", "Bank Entry"),
            "company": defn["company"],
            "posting_date": defn["posting_date"],
            "user_remark": defn["user_remark"],
            "accounts": defn["accounts"],
        }
    )
    doc.insert(ignore_permissions=True)
    doc.submit()
    return doc.name


def _create_partial_payment(reference_doctype: str, reference_name: str, posting_date: str, amount: float) -> str:
    existing = frappe.get_all(
        "Payment Entry Reference",
        filters={
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
            "allocated_amount": amount,
            "docstatus": 1,
            "parenttype": "Payment Entry",
        },
        fields=["parent"],
        limit=1,
    )
    if existing:
        return existing[0]["parent"]

    payment = get_payment_entry(reference_doctype, reference_name)
    if not payment:
        raise frappe.ValidationError(f"Unable to build payment entry for {reference_doctype} {reference_name}")

    payment.posting_date = posting_date
    payment.paid_amount = amount
    payment.received_amount = amount
    payment.references = payment.references[:1]
    payment.references[0].allocated_amount = amount
    payment.insert(ignore_permissions=True)
    payment.submit()
    return payment.name


def _create_partial_payment_with_date_dedupe(
    reference_doctype: str, reference_name: str, posting_date: str, amount: float
) -> str:
    existing = frappe.db.sql(
        """
        select per.parent
        from `tabPayment Entry Reference` per
        inner join `tabPayment Entry` pe on pe.name = per.parent
        where per.reference_doctype = %s
          and per.reference_name = %s
          and per.allocated_amount = %s
          and per.docstatus = 1
          and per.parenttype = 'Payment Entry'
          and pe.posting_date = %s
        limit 1
        """,
        (reference_doctype, reference_name, amount, posting_date),
        as_dict=True,
    )
    if existing:
        return existing[0]["parent"]

    payment = get_payment_entry(reference_doctype, reference_name)
    if not payment:
        raise frappe.ValidationError(f"Unable to build payment entry for {reference_doctype} {reference_name}")

    payment.posting_date = posting_date
    payment.paid_amount = amount
    payment.received_amount = amount
    payment.references = payment.references[:1]
    payment.references[0].allocated_amount = amount
    payment.insert(ignore_permissions=True)
    payment.submit()
    return payment.name


def _find_outstanding_sales_invoice(customer: str, before_date: str) -> str | None:
    matches = frappe.get_all(
        "Sales Invoice",
        filters={
            "customer": customer,
            "docstatus": 1,
            "posting_date": ["<=", before_date],
            "outstanding_amount": [">", 0],
        },
        fields=["name", "posting_date", "outstanding_amount"],
        order_by="posting_date asc",
        limit=1,
    )
    return matches[0]["name"] if matches else None


def _find_account_by_names(names: list[str]) -> str | None:
    for name in names:
        if frappe.db.exists("Account", name):
            return name
    matches = frappe.get_all("Account", filters={"account_name": ["in", names]}, pluck="name", limit=1)
    if matches:
        return matches[0]
    for name in names:
        like = f"%{name}%"
        rows = frappe.db.sql(
            """
            select name
            from `tabAccount`
            where account_name like %s or name like %s
            limit 1
            """,
            (like, like),
        )
        if rows:
            return rows[0][0]
    return None


def _month_series(start_date: str, end_date: str) -> list[dict[str, Any]]:
    series = []
    current = getdate(start_date)
    end = getdate(end_date)
    while current <= end:
        month_end = get_last_day(current)
        series.append(
            {
                "period_start": current.strftime("%Y-%m-01"),
                "period_end": month_end.strftime("%Y-%m-%d"),
                "posting_date": month_end.strftime("%Y-%m-%d"),
                "month_key": month_end.strftime("%Y-%m"),
            }
        )
        current = add_months(current, 1)
    return series


def _make_return_doc(doctype: str, docname: str):
    candidate_paths = [
        "erpnext.controllers.sales_and_purchase_return.make_return_doc",
        "erpnext.controllers.sales_and_purchase_return.make_return_doc_from_doctype",
        "erpnext.accounts.doctype.sales_invoice.sales_invoice.make_return_doc",
        "erpnext.accounts.doctype.purchase_invoice.purchase_invoice.make_return_doc",
    ]
    for path in candidate_paths:
        try:
            fn = frappe.get_attr(path)
        except Exception:
            continue
        try:
            sig = inspect.signature(fn)
            params = sig.parameters
            if "doctype" in params and "docname" in params:
                return fn(doctype=doctype, docname=docname)
            if "doctype" in params and "name" in params:
                return fn(doctype=doctype, name=docname)
            if len(params) >= 2:
                return fn(doctype, docname)
            if "docname" in params:
                return fn(docname=docname)
        except Exception:
            continue
    raise AttributeError("No return document builder found.")


def _find_outstanding_purchase_invoice(supplier: str, before_date: str) -> str | None:
    matches = frappe.get_all(
        "Purchase Invoice",
        filters={
            "supplier": supplier,
            "docstatus": 1,
            "posting_date": ["<=", before_date],
            "outstanding_amount": [">", 0],
        },
        fields=["name", "posting_date", "outstanding_amount"],
        order_by="posting_date asc",
        limit=1,
    )
    return matches[0]["name"] if matches else None


def _apply_targeted_partial_payment(
    reference_doctype: str,
    reference_name: str,
    posting_date: str,
    amount: float,
) -> dict[str, Any] | None:
    doc = frappe.get_doc(reference_doctype, reference_name)
    outstanding = float(doc.outstanding_amount or 0)
    if outstanding <= 0:
        return None

    rounded_amount = min(amount, outstanding)
    if rounded_amount <= 0:
        return None

    payment_name = _create_partial_payment(reference_doctype, reference_name, posting_date, rounded_amount)
    return {
        "reference_doctype": reference_doctype,
        "reference_name": reference_name,
        "payment_entry": payment_name,
        "amount": rounded_amount,
    }


def _apply_targeted_partial_payment_with_date_dedupe(
    reference_doctype: str,
    reference_name: str,
    posting_date: str,
    amount: float,
) -> dict[str, Any] | None:
    doc = frappe.get_doc(reference_doctype, reference_name)
    outstanding = float(doc.outstanding_amount or 0)
    if outstanding <= 0:
        return None

    rounded_amount = min(amount, outstanding)
    if rounded_amount <= 0:
        return None

    payment_name = _create_partial_payment_with_date_dedupe(
        reference_doctype,
        reference_name,
        posting_date,
        rounded_amount,
    )
    return {
        "reference_doctype": reference_doctype,
        "reference_name": reference_name,
        "payment_entry": payment_name,
        "amount": rounded_amount,
    }


def _find_existing_purchase_return(
    source_invoice_name: str,
    posting_date: str,
    remarks: str,
) -> str | None:
    names = frappe.get_all(
        "Purchase Invoice",
        filters={
            "return_against": source_invoice_name,
            "is_return": 1,
            "posting_date": posting_date,
            "remarks": remarks,
            "docstatus": 1,
        },
        pluck="name",
        limit=1,
    )
    return names[0] if names else None


def _create_partial_purchase_return_against_invoice(
    source_invoice_name: str,
    posting_date: str,
    remarks: str,
    item_qty_map: dict[str, float],
) -> str:
    existing_name = _find_existing_purchase_return(source_invoice_name, posting_date, remarks)
    if existing_name:
        return existing_name

    return_doc = _make_return_doc("Purchase Invoice", source_invoice_name)
    return_doc.posting_date = posting_date
    return_doc.posting_time = "15:00:00"
    return_doc.set_posting_time = 1
    if hasattr(return_doc, "is_return"):
        return_doc.is_return = 1
    if hasattr(return_doc, "return_against"):
        return_doc.return_against = source_invoice_name
    return_doc.remarks = remarks

    kept_items = []
    for item in return_doc.items:
        target_qty = item_qty_map.get(item.item_code)
        if not target_qty:
            continue
        item.qty = -abs(float(target_qty))
        if hasattr(item, "received_qty"):
            item.received_qty = item.qty
        if hasattr(item, "rejected_qty"):
            item.rejected_qty = 0
        if getattr(item, "conversion_factor", None):
            item.stock_qty = item.qty * float(item.conversion_factor or 1)
        kept_items.append(item)

    if not kept_items:
        raise frappe.ValidationError(f"No matching items found for purchase return against {source_invoice_name}")

    return_doc.items = kept_items
    return_doc.insert(ignore_permissions=True)
    return_doc.submit()
    return return_doc.name


def create_september_2025_commercial_batch() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."

    sales_defs = [
        {
            "customer": "Capital Telecom (NPT)",
            "posting_date": "2025-09-09",
            "due_date": "2025-10-24",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 6030000,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 4, "rate": 995000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 15, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 10, "rate": 32000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 10, "rate": 8000},
            ],
        },
        {
            "customer": "Hledan Phone Hub",
            "posting_date": "2025-09-11",
            "due_date": "2025-10-11",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 6930000,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 5, "rate": 890000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 44, "rate": 30000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 20, "rate": 58000},
            ],
        },
        {
            "customer": "Pazundaung Mobile Distribution",
            "posting_date": "2025-09-15",
            "due_date": "2025-09-22",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 3860000,
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 1, "rate": 2100000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 112000},
                {"item_code": "ACC-CHR-ANK-20W", "qty": 20, "rate": 32000},
            ],
        },
        {
            "customer": "Chan Aye Mobile Trading Hub",
            "posting_date": "2025-09-18",
            "due_date": "2025-09-25",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 4700000,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 990000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 10, "rate": 32000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 20, "rate": 108000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 30, "rate": 8000},
            ],
        },
        {
            "customer": "35th Street Mobile Wholesale",
            "posting_date": "2025-09-21",
            "due_date": "2025-10-21",
            "warehouse": "Mandalay Warehouse - MMOB",
            "company": company,
            "expected_total": 11265000,
            "items": [
                {"item_code": "SPH-APP-IP14-128", "qty": 3, "rate": 2620000, "warehouse": "Mandalay Warehouse - MMOB"},
                {"item_code": "ACC-PWB-ANK-10K", "qty": 25, "rate": 85000, "warehouse": "Mandalay Warehouse - MMOB"},
                {"item_code": "ACC-CHR-ANK-20W", "qty": 40, "rate": 32000, "warehouse": "Mandalay Warehouse - MMOB"},
            ],
        },
        {
            "customer": "Mayangone Mobile House",
            "posting_date": "2025-09-26",
            "due_date": "2025-09-26",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 2436000,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 1020000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 2, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 4, "rate": 32000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 6, "rate": 8000},
            ],
        },
        {
            "customer": "Mandalay Accessories Wholesale",
            "posting_date": "2025-09-24",
            "due_date": "2025-10-09",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 7952000,
            "items": [
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 40, "rate": 32000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 20, "rate": 58000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 44, "rate": 108000},
            ],
        },
        {
            "customer": "Hledan Mobile Trade Center",
            "posting_date": "2025-09-27",
            "due_date": "2025-10-04",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 4200000,
            "items": [
                {"item_code": "MEM-MSD-SND-128", "qty": 60, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 60, "rate": 16000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 108000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
            ],
        },
        {
            "customer": "Bago Myoma Phone Shop",
            "posting_date": "2025-09-29",
            "due_date": "2025-09-29",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 2200000,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 1, "rate": 1020000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 8, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 8, "rate": 32000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 6, "rate": 8000},
            ],
        },
    ]

    purchase_defs = [
        {
            "supplier": "Shwe Taung Electronics Supply",
            "posting_date": "2025-09-02",
            "due_date": "2025-10-02",
            "company": company,
            "expected_total": 36940000,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 18, "rate": 840000, "warehouse": "Yangon Main Warehouse - MMOB"},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 200, "rate": 78500, "warehouse": "Yangon Main Warehouse - MMOB"},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 200, "rate": 25600, "warehouse": "Yangon Main Warehouse - MMOB"},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 200, "rate": 5000, "warehouse": "Yangon Main Warehouse - MMOB"},
            ],
        },
        {
            "supplier": "Sunflower Accessories Co.",
            "posting_date": "2025-09-10",
            "due_date": "2025-10-10",
            "company": company,
            "expected_total": 17116000,
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 5, "rate": 1760000, "warehouse": "Yangon Main Warehouse - MMOB"},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 80, "rate": 42000, "warehouse": "Yangon Main Warehouse - MMOB"},
                {"item_code": "ACC-SP-GLS-A15", "qty": 80, "rate": 2200, "warehouse": "Yangon Main Warehouse - MMOB"},
                {"item_code": "ACC-CAS-TPU-A15", "qty": 80, "rate": 3500, "warehouse": "Yangon Main Warehouse - MMOB"},
                {"item_code": "MEM-USB-SND-64", "qty": 150, "rate": 11800, "warehouse": "Yangon Main Warehouse - MMOB"},
                {"item_code": "MEM-MSD-SND-128", "qty": 150, "rate": 18200, "warehouse": "Yangon Main Warehouse - MMOB"},
            ],
        },
    ]

    sales_payments = [
        ("Capital Telecom (NPT)", "2025-09-18", 2000000),
        ("Pazundaung Mobile Distribution", "2025-09-25", 3000000),
        ("Chan Aye Mobile Trading Hub", "2025-09-29", 3500000),
        ("Mandalay Accessories Wholesale", "2025-09-30", 5000000),
        ("Lanmadaw Digital Wholesale", "2025-09-30", 4000000),
    ]

    supplier_payments = [
        ("Shwe Taung Electronics Supply", "2025-09-29", 3000000),
        ("Sunflower Accessories Co.", "2025-09-30", 2000000),
    ]

    created_purchases = []
    created_sales = []
    created_payments = []

    purchase_invoice_map = {}
    for definition in purchase_defs:
        invoice_name = _create_purchase_invoice(definition)
        purchase_invoice_map[definition["supplier"]] = invoice_name
        created_purchases.append({"supplier": definition["supplier"], "invoice": invoice_name})
        frappe.db.commit()

    sales_invoice_map = {}
    for definition in sales_defs:
        invoice_name = _create_sales_invoice(definition)
        sales_invoice_map[definition["customer"]] = invoice_name
        created_sales.append({"customer": definition["customer"], "invoice": invoice_name})
        frappe.db.commit()

    for customer, posting_date, amount in sales_payments:
        payment_name = _create_partial_payment("Sales Invoice", sales_invoice_map[customer], posting_date, amount)
        created_payments.append(
            {
                "party_type": "Customer",
                "party": customer,
                "payment_entry": payment_name,
                "amount": amount,
            }
        )
        frappe.db.commit()

    for supplier, posting_date, amount in supplier_payments:
        payment_name = _create_partial_payment("Purchase Invoice", purchase_invoice_map[supplier], posting_date, amount)
        created_payments.append(
            {
                "party_type": "Supplier",
                "party": supplier,
                "payment_entry": payment_name,
                "amount": amount,
            }
        )
        frappe.db.commit()

    frappe.db.commit()
    return {
        "sales_invoices": created_sales,
        "purchase_invoices": created_purchases,
        "payment_entries": created_payments,
    }


def create_september_2025_profit_correction() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."

    sales_definitions = [
        {
            "customer": "Ko Nay Lin Mobile Center",
            "posting_date": "2025-09-30",
            "due_date": "2025-10-30",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 6680000,
            "items": [
                {"item_code": "ACC-PWB-BAS-20K", "qty": 30, "rate": 110000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 15, "rate": 58000},
                {"item_code": "MEM-MSD-SND-128", "qty": 30, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 30, "rate": 16000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 30, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 7, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 10, "rate": 8000},
            ],
        },
        {
            "customer": "Mandalay Accessories Wholesale",
            "posting_date": "2025-09-30",
            "due_date": "2025-10-15",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 4900000,
            "items": [
                {"item_code": "ACC-PWB-BAS-20K", "qty": 20, "rate": 108000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 10, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 50, "rate": 8000},
            ],
        },
        {
            "customer": "Mayangone Mobile House",
            "posting_date": "2025-09-30",
            "due_date": "2025-11-14",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 2590000,
            "items": [
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 10, "rate": 32000},
                {"item_code": "MEM-USB-SND-64", "qty": 10, "rate": 16000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 5, "rate": 58000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 4, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 10, "rate": 8000},
            ],
        },
    ]

    purchase_definitions = [
        {
            "supplier": "Sunflower Accessories Co.",
            "posting_date": "2025-10-26",
            "due_date": "2025-11-25",
            "company": company,
            "expected_total": 9320000,
            "items": [
                {
                    "item_code": "MEM-MSD-SND-128",
                    "qty": 200,
                    "rate": 18000,
                    "warehouse": "Yangon Main Warehouse - MMOB",
                },
                {
                    "item_code": "MEM-USB-SND-64",
                    "qty": 200,
                    "rate": 11800,
                    "warehouse": "Yangon Main Warehouse - MMOB",
                },
                {
                    "item_code": "ACC-AUD-XMI-BUDS4",
                    "qty": 80,
                    "rate": 42000,
                    "warehouse": "Yangon Main Warehouse - MMOB",
                },
            ],
        }
    ]

    sales_invoices = []
    for definition in sales_definitions:
        invoice_name = _create_sales_invoice(definition)
        sales_invoices.append(
            {
                "customer": definition["customer"],
                "sales_invoice": invoice_name,
                "grand_total": definition["expected_total"],
            }
        )
        frappe.db.commit()

    payment_specs = [
        ("Bayint Naung Wholesale Mobile", 2000000),
        ("Mandalay Accessories Wholesale", 2000000),
        ("Capital Telecom (NPT)", 1000000),
    ]

    invoice_map = {row["customer"]: row["sales_invoice"] for row in sales_invoices}
    payment_entries = []
    for customer, amount in payment_specs:
        payment_name = _create_partial_payment(
            "Sales Invoice", invoice_map[customer], "2025-09-30", amount
        )
        payment_entries.append(
            {"customer": customer, "payment_entry": payment_name, "amount": amount}
        )
        frappe.db.commit()

    return {
        "sales_invoices": sales_invoices,
        "payment_entries": payment_entries,
    }


def create_october_2025_commercial_batch() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."

    sales_definitions = [
        {
            "customer": "Hledan Phone Hub",
            "posting_date": "2025-10-16",
            "due_date": "2025-11-15",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 8516000,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 4, "rate": 1030000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 40, "rate": 32000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 30, "rate": 8000},
                {"item_code": "ACC-SP-GLS-A15", "qty": 40, "rate": 8000},
                {"item_code": "ACC-CAS-TPU-A15", "qty": 40, "rate": 18000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 12, "rate": 153000},
            ],
        },
        {
            "customer": "Mayangone Mobile House",
            "posting_date": "2025-10-18",
            "due_date": "2025-11-30",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 8395000,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 5, "rate": 905000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 40, "rate": 30000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 40, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 15, "rate": 58000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 8, "rate": 155000},
            ],
        },
        {
            "customer": "Taunggyi City Mobile",
            "posting_date": "2025-10-21",
            "due_date": "2025-11-11",
            "warehouse": "Mandalay Warehouse - MMOB",
            "company": company,
            "expected_total": 7360000,
            "items": [
                {"item_code": "SPH-APP-IP14-128", "qty": 2, "rate": 2650000},
                {"item_code": "ACC-PWB-ANK-10K", "qty": 10, "rate": 130000},
                {"item_code": "ACC-CHR-ANK-20W", "qty": 10, "rate": 48000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
            ],
        },
        {
            "customer": "Thingangyun Mobile House",
            "posting_date": "2025-10-24",
            "due_date": "2025-11-23",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 8880000,
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 2, "rate": 2150000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 1020000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 8, "rate": 150000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 25, "rate": 8000},
                {"item_code": "ACC-CAS-TPU-A15", "qty": 10, "rate": 20000},
                {"item_code": "ACC-SP-GLS-A15", "qty": 30, "rate": 10000},
            ],
        },
        {
            "customer": "Latha Mobile Wholesale",
            "posting_date": "2025-10-25",
            "due_date": "2025-11-15",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 5280000,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 1030000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 6, "rate": 150000},
                {"item_code": "ACC-SP-GLS-A15", "qty": 30, "rate": 8000},
                {"item_code": "ACC-CAS-TPU-A15", "qty": 20, "rate": 20000},
            ],
        },
        {
            "customer": "City Mobile Mart",
            "posting_date": "2025-10-27",
            "due_date": "2025-10-27",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 3480000,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 1, "rate": 900000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "MEM-MSD-SND-128", "qty": 40, "rate": 26000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
                {"item_code": "MEM-USB-SND-64", "qty": 15, "rate": 16000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 10, "rate": 32000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 10, "rate": 8000},
                {"item_code": "ACC-SP-GLS-A15", "qty": 2, "rate": 10000},
            ],
        },
        {
            "customer": "Lanmadaw Telecom & Gadgets",
            "posting_date": "2025-10-28",
            "due_date": "2025-11-12",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 4760000,
            "items": [
                {"item_code": "MEM-MSD-SND-128", "qty": 60, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 80, "rate": 16000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 30, "rate": 14000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 1, "rate": 150000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 10, "rate": 8000},
                {"item_code": "ACC-SP-GLS-A15", "qty": 3, "rate": 10000},
            ],
        },
        {
            "customer": "Taunggyi Star Mobile",
            "posting_date": "2025-10-30",
            "due_date": "2025-11-29",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 7650000,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 3, "rate": 1020000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 8, "rate": 150000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 25, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 27, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 30, "rate": 8000},
                {"item_code": "ACC-CAS-TPU-A15", "qty": 20, "rate": 20000},
                {"item_code": "ACC-SP-GLS-A15", "qty": 30, "rate": 10000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
            ],
        },
        {
            "customer": "Hlaing Tharyar Mobile Corner",
            "posting_date": "2025-10-31",
            "due_date": "2025-12-15",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 9240000,
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 3, "rate": 2140000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 900000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 30, "rate": 14000},
            ],
        },
        {
            "customer": "Hledan Phone Hub",
            "posting_date": "2025-10-31",
            "due_date": "2025-11-30",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 6440000,
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 1, "rate": 2150000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 1, "rate": 1020000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 3, "rate": 150000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 15, "rate": 14000},
                {"item_code": "MEM-MSD-SND-128", "qty": 30, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 25, "rate": 16000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 18, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 10, "rate": 8000},
                {"item_code": "ACC-SP-GLS-A15", "qty": 17, "rate": 10000},
            ],
        },
    ]

    purchase_definitions = [
        {
            "supplier": "Sunflower Accessories Co.",
            "posting_date": "2025-10-26",
            "due_date": "2025-11-25",
            "company": company,
            "expected_total": 9320000,
            "items": [
                {
                    "item_code": "MEM-MSD-SND-128",
                    "qty": 200,
                    "rate": 18000,
                    "warehouse": "Yangon Main Warehouse - MMOB",
                },
                {
                    "item_code": "MEM-USB-SND-64",
                    "qty": 200,
                    "rate": 11800,
                    "warehouse": "Yangon Main Warehouse - MMOB",
                },
                {
                    "item_code": "ACC-AUD-XMI-BUDS4",
                    "qty": 80,
                    "rate": 42000,
                    "warehouse": "Yangon Main Warehouse - MMOB",
                },
            ],
        }
    ]

    customer_payment_specs = [
        ("Hledan Phone Hub", "2025-10-20", 2000000, 8516000),
        ("Mayangone Mobile House", "2025-10-22", 2500000, 8395000),
        ("Taunggyi City Mobile", "2025-10-24", 2000000, 7360000),
        ("Thingangyun Mobile House", "2025-10-27", 3000000, 8880000),
        ("Latha Mobile Wholesale", "2025-10-28", 2000000, 5280000),
        ("City Mobile Mart", "2025-10-27", 3480000, 3480000),
        ("Lanmadaw Telecom & Gadgets", "2025-10-30", 2000000, 4760000),
        ("Taunggyi Star Mobile", "2025-10-31", 2000000, 7650000),
        ("Hlaing Tharyar Mobile Corner", "2025-10-31", 3000000, 9240000),
        ("Hledan Phone Hub", "2025-10-31", 2500000, 6440000),
    ]

    supplier_payment_specs = [
        ("Golden Dragon Electronics Trading", "2025-10-20", 6000000, 18490000),
        ("Myanmar Tech Import Services", "2025-10-24", 4500000, 13740000),
        ("Sunflower Accessories Co.", "2025-10-31", 3000000, 11050000),
        ("Sunflower Accessories Co.", "2025-10-31", 2000000, 9320000),
    ]

    purchase_invoices = []
    for definition in purchase_definitions:
        invoice_name = _create_purchase_invoice(definition)
        purchase_invoices.append(
            {
                "supplier": definition["supplier"],
                "purchase_invoice": invoice_name,
                "grand_total": definition["expected_total"],
            }
        )
        frappe.db.commit()

    sales_invoices = []
    invoice_map = {}
    for definition in sales_definitions:
        invoice_name = _create_sales_invoice(definition)
        invoice_map[(definition["customer"], definition["expected_total"])] = invoice_name
        sales_invoices.append(
            {
                "customer": definition["customer"],
                "sales_invoice": invoice_name,
                "grand_total": definition["expected_total"],
            }
        )
        frappe.db.commit()

    payment_entries = []
    for customer, posting_date, amount, expected_total in customer_payment_specs:
        payment_name = _create_partial_payment(
            "Sales Invoice",
            invoice_map[(customer, expected_total)],
            posting_date,
            amount,
        )
        payment_entries.append(
            {
                "party_type": "Customer",
                "party": customer,
                "payment_entry": payment_name,
                "amount": amount,
            }
        )
        frappe.db.commit()

    purchase_invoice_map = {}
    existing_purchase_invoices = frappe.get_all(
        "Purchase Invoice",
        filters={"posting_date": ["between", ["2025-10-01", "2025-10-31"]], "docstatus": 1},
        fields=["name", "supplier", "grand_total"],
    )
    for invoice in existing_purchase_invoices:
        purchase_invoice_map[(invoice.supplier, int(round(invoice.grand_total)))] = invoice.name

    for supplier, posting_date, amount, expected_total in supplier_payment_specs:
        invoice_name = purchase_invoice_map[(supplier, expected_total)]
        payment_name = _create_partial_payment("Purchase Invoice", invoice_name, posting_date, amount)
        payment_entries.append(
            {
                "party_type": "Supplier",
                "party": supplier,
                "payment_entry": payment_name,
                "amount": amount,
            }
        )
        frappe.db.commit()

    return {
        "purchase_invoices": purchase_invoices,
        "sales_invoices": sales_invoices,
        "payment_entries": payment_entries,
    }


def create_october_2025_closing_pass() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."

    closing_sales_definitions = [
        {
            "customer": "Taunggyi Star Mobile",
            "posting_date": "2025-10-30",
            "due_date": "2025-11-29",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 6560000,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 1020000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 1, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 5, "rate": 150000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
                {"item_code": "ACC-SP-GLS-A15", "qty": 35, "rate": 10000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 5, "rate": 56000},
            ],
        },
        {
            "customer": "Hlaing Tharyar Mobile Corner",
            "posting_date": "2025-10-31",
            "due_date": "2025-12-15",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 9000000,
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 2, "rate": 2140000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 8, "rate": 150000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 10, "rate": 16000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 5, "rate": 32000},
            ],
        },
        {
            "customer": "Hledan Phone Hub",
            "posting_date": "2025-10-31",
            "due_date": "2025-11-30",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 6284000,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 1030000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 5, "rate": 150000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 30, "rate": 8000},
                {"item_code": "ACC-SP-GLS-A15", "qty": 33, "rate": 8000},
                {"item_code": "MEM-MSD-SND-128", "qty": 25, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 35, "rate": 16000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 15, "rate": 30000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 15, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 8, "rate": 57500},
            ],
        },
    ]

    customer_payment_specs = [
        ("Hledan Phone Hub", "2025-10-20", 2000000, 8516000),
        ("Mayangone Mobile House", "2025-10-22", 2500000, 8395000),
        ("Taunggyi City Mobile", "2025-10-24", 2000000, 7360000),
        ("Thingangyun Mobile House", "2025-10-27", 3000000, 8880000),
        ("Latha Mobile Wholesale", "2025-10-28", 2000000, 5280000),
        ("City Mobile Mart", "2025-10-27", 3480000, 3480000),
        ("Lanmadaw Telecom & Gadgets", "2025-10-30", 2000000, 4760000),
        ("Taunggyi Star Mobile", "2025-10-31", 2000000, 6560000),
        ("Hlaing Tharyar Mobile Corner", "2025-10-31", 3000000, 9000000),
        ("Hledan Phone Hub", "2025-10-31", 2500000, 6284000),
    ]

    supplier_payment_specs = [
        ("Golden Dragon Trading Co. Ltd.", "2025-10-20", 6000000, 18490000),
        ("Myanmar Tech Import Services", "2025-10-24", 4500000, 13740000),
        ("Sunflower Accessories Co.", "2025-10-31", 3000000, 11050000),
        ("Sunflower Accessories Co.", "2025-10-31", 2000000, 9320000),
        ("Sunflower Accessories Co.", "2025-10-31", 2000000, 6025000),
        ("Sunflower Accessories Co.", "2025-10-31", 1000000, 1490000),
    ]

    sales_invoices = []
    for definition in closing_sales_definitions:
        invoice_name = _create_sales_invoice(definition)
        sales_invoices.append(
            {
                "customer": definition["customer"],
                "sales_invoice": invoice_name,
                "grand_total": definition["expected_total"],
            }
        )
        frappe.db.commit()

    sales_invoice_map = {}
    for invoice in frappe.get_all(
        "Sales Invoice",
        filters={"posting_date": ["between", ["2025-10-01", "2025-10-31"]], "docstatus": 1},
        fields=["name", "customer", "grand_total"],
    ):
        sales_invoice_map[(invoice.customer, int(round(invoice.grand_total)))] = invoice.name

    purchase_invoice_map = {}
    for invoice in frappe.get_all(
        "Purchase Invoice",
        filters={"posting_date": ["between", ["2025-10-01", "2025-10-31"]], "docstatus": 1},
        fields=["name", "supplier", "grand_total"],
    ):
        purchase_invoice_map[(invoice.supplier, int(round(invoice.grand_total)))] = invoice.name

    payment_entries = []
    for customer, posting_date, amount, expected_total in customer_payment_specs:
        invoice_name = sales_invoice_map[(customer, expected_total)]
        payment_name = _create_partial_payment("Sales Invoice", invoice_name, posting_date, amount)
        payment_entries.append(
            {
                "party_type": "Customer",
                "party": customer,
                "payment_entry": payment_name,
                "amount": amount,
            }
        )
        frappe.db.commit()

    for supplier, posting_date, amount, expected_total in supplier_payment_specs:
        invoice_name = purchase_invoice_map[(supplier, expected_total)]
        payment_name = _create_partial_payment("Purchase Invoice", invoice_name, posting_date, amount)
        payment_entries.append(
            {
                "party_type": "Supplier",
                "party": supplier,
                "payment_entry": payment_name,
                "amount": amount,
            }
        )
        frappe.db.commit()

    return {
        "sales_invoices": sales_invoices,
        "payment_entries": payment_entries,
    }


def create_november_2025_commercial_batch() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."

    purchase_definitions = [
        {
            "supplier": "Shwe Taung Electronics Supply",
            "posting_date": "2025-11-19",
            "due_date": "2025-12-19",
            "company": company,
            "expected_total": 24700000,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 8, "rate": 840000, "warehouse": "Yangon Main Warehouse - MMOB"},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 8, "rate": 890000, "warehouse": "Yangon Main Warehouse - MMOB"},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 80, "rate": 78500, "warehouse": "Yangon Main Warehouse - MMOB"},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 80, "rate": 21000, "warehouse": "Yangon Main Warehouse - MMOB"},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 80, "rate": 25000, "warehouse": "Yangon Main Warehouse - MMOB"},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 100, "rate": 9000, "warehouse": "Yangon Main Warehouse - MMOB"},
            ],
        },
        {
            "supplier": "Sunflower Accessories Co.",
            "posting_date": "2025-11-26",
            "due_date": "2025-12-26",
            "company": company,
            "expected_total": 6740000,
            "items": [
                {"item_code": "MEM-MSD-SND-128", "qty": 150, "rate": 18000, "warehouse": "Yangon Main Warehouse - MMOB"},
                {"item_code": "MEM-USB-SND-64", "qty": 200, "rate": 11800, "warehouse": "Yangon Main Warehouse - MMOB"},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 40, "rate": 42000, "warehouse": "Yangon Main Warehouse - MMOB"},
            ],
        },
    ]

    sales_definitions = [
        {
            "customer": "Hledan Phone Hub",
            "posting_date": "2025-11-08",
            "due_date": "2025-12-08",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 6550000,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 1030000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 15, "rate": 150000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 30, "rate": 32000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
                {"item_code": "ACC-CAS-TPU-A15", "qty": 20, "rate": 18000},
                {"item_code": "ACC-SP-GLS-A15", "qty": 20, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 10, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 5, "rate": 58000},
                {"item_code": "MEM-USB-SND-64", "qty": 5, "rate": 16000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 3, "rate": 30000},
            ],
        },
        {
            "customer": "Mayangone Mobile House",
            "posting_date": "2025-11-10",
            "due_date": "2025-12-25",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 7390000,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 4, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 150000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 25, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 15, "rate": 30000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 5, "rate": 58000},
                {"item_code": "MEM-MSD-SND-128", "qty": 5, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 5, "rate": 16000},
                {"item_code": "ACC-CAS-TPU-A15", "qty": 5, "rate": 20000},
            ],
        },
        {
            "customer": "Latha Mobile Wholesale",
            "posting_date": "2025-11-12",
            "due_date": "2025-12-02",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 8370000,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 1030000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 8, "rate": 150000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 35, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 30000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 30, "rate": 14000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
                {"item_code": "ACC-CAS-TPU-A15", "qty": 20, "rate": 18000},
                {"item_code": "ACC-SP-GLS-A15", "qty": 20, "rate": 8000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "MEM-MSD-SND-128", "qty": 5, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 5, "rate": 16000},
            ],
        },
        {
            "customer": "Thingangyun Mobile House",
            "posting_date": "2025-11-22",
            "due_date": "2025-12-22",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 8990000,
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 2, "rate": 2150000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 1, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 5, "rate": 150000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 25, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 30000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 25, "rate": 14000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "MEM-MSD-SND-128", "qty": 10, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 10, "rate": 16000},
                {"item_code": "ACC-CAS-TPU-A15", "qty": 10, "rate": 20000},
                {"item_code": "ACC-SP-GLS-A15", "qty": 23, "rate": 10000},
            ],
        },
        {
            "customer": "Taunggyi City Mobile",
            "posting_date": "2025-11-16",
            "due_date": "2025-12-06",
            "warehouse": "Mandalay Warehouse - MMOB",
            "company": company,
            "expected_total": 5800000,
            "items": [
                {"item_code": "SPH-APP-IP14-128", "qty": 1, "rate": 2650000, "warehouse": "Mandalay Warehouse - MMOB"},
                {"item_code": "ACC-PWB-ANK-10K", "qty": 20, "rate": 130000, "warehouse": "Mandalay Warehouse - MMOB"},
                {"item_code": "ACC-CHR-ANK-20W", "qty": 10, "rate": 48000, "warehouse": "Mandalay Warehouse - MMOB"},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 5, "rate": 14000, "warehouse": "Mandalay Warehouse - MMOB"},
            ],
        },
        {
            "customer": "Hlaing Tharyar Mobile Corner",
            "posting_date": "2025-11-20",
            "due_date": "2026-01-04",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 9190000,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 3, "rate": 900000},
                {"item_code": "SPH-APP-IP13-128", "qty": 1, "rate": 2140000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 8, "rate": 150000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 30, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 15, "rate": 30000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "MEM-MSD-SND-128", "qty": 10, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 10, "rate": 16000},
                {"item_code": "ACC-CAS-TPU-A15", "qty": 10, "rate": 18000},
                {"item_code": "ACC-SP-GLS-A15", "qty": 12, "rate": 10000},
            ],
        },
        {
            "customer": "Sanchaung Mobile Plaza",
            "posting_date": "2025-11-21",
            "due_date": "2025-11-21",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 2980000,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 1, "rate": 1030000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 10, "rate": 32000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 5, "rate": 150000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 10, "rate": 14000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 12, "rate": 8000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 3, "rate": 58000},
                {"item_code": "MEM-MSD-SND-128", "qty": 5, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 5, "rate": 16000},
                {"item_code": "ACC-CAS-TPU-A15", "qty": 5, "rate": 20000},
                {"item_code": "ACC-SP-GLS-A15", "qty": 7, "rate": 10000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 3, "rate": 30000},
            ],
        },
        {
            "customer": "Lanmadaw Telecom & Gadgets",
            "posting_date": "2025-11-24",
            "due_date": "2025-12-09",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 6016000,
            "items": [
                {"item_code": "MEM-MSD-SND-128", "qty": 12, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 30, "rate": 16000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 8, "rate": 58000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 30000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 30, "rate": 32000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 40, "rate": 14000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 30, "rate": 8000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 5, "rate": 150000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 1, "rate": 900000},
                {"item_code": "ACC-SP-GLS-A15", "qty": 8, "rate": 10000},
                {"item_code": "ACC-CAS-TPU-A15", "qty": 10, "rate": 18000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 10, "rate": 32000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 10, "rate": 14000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 10, "rate": 8000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 3, "rate": 58000},
                {"item_code": "MEM-MSD-SND-128", "qty": 2, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 1, "rate": 16000},
                {"item_code": "ACC-SP-GLS-A15", "qty": 1, "rate": 8000},
            ],
        },
        {
            "customer": "Taunggyi Star Mobile",
            "posting_date": "2025-11-27",
            "due_date": "2025-12-27",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 6430000,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 1030000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 8, "rate": 150000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 30000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
                {"item_code": "ACC-CAS-TPU-A15", "qty": 15, "rate": 18000},
                {"item_code": "ACC-SP-GLS-A15", "qty": 20, "rate": 8000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 5, "rate": 58000},
                {"item_code": "MEM-MSD-SND-128", "qty": 10, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 10, "rate": 16000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 10, "rate": 32000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 2, "rate": 150000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 1, "rate": 14000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 1, "rate": 8000},
                {"item_code": "ACC-SP-GLS-A15", "qty": 1, "rate": 8000},
            ],
        },
        {
            "customer": "Hledan Phone Hub",
            "posting_date": "2025-11-29",
            "due_date": "2025-12-29",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 7320000,
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 1, "rate": 2140000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 5, "rate": 150000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 30000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
                {"item_code": "MEM-MSD-SND-128", "qty": 10, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 10, "rate": 16000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 9, "rate": 58000},
                {"item_code": "ACC-CAS-TPU-A15", "qty": 10, "rate": 18000},
                {"item_code": "ACC-SP-GLS-A15", "qty": 16, "rate": 8000},
            ],
        },
    ]

    customer_payment_specs = [
        ("Hledan Phone Hub", "2025-11-10", 2000000, 6550000),
        ("Mayangone Mobile House", "2025-11-12", 2500000, 7390000),
        ("Latha Mobile Wholesale", "2025-11-14", 2000000, 8370000),
        ("Thingangyun Mobile House", "2025-11-24", 3000000, 8990000),
        ("Taunggyi City Mobile", "2025-11-18", 2000000, 5800000),
        ("Hlaing Tharyar Mobile Corner", "2025-11-22", 3000000, 9190000),
        ("Sanchaung Mobile Plaza", "2025-11-21", 2000000, 2980000),
        ("Lanmadaw Telecom & Gadgets", "2025-11-25", 2000000, 6016000),
        ("Taunggyi Star Mobile", "2025-11-28", 2000000, 6430000),
        ("Hledan Phone Hub", "2025-11-30", 2500000, 7320000),
    ]

    supplier_payment_specs = [
        ("Mandalay Device Wholesale", "2025-11-14", 4000000, 17135000),
        ("Shwe Taung Electronics Supply", "2025-11-20", 3500000, 15785000),
        ("Sunflower Accessories Co.", "2025-11-27", 2000000, 7745000),
        ("Shwe Taung Electronics Supply", "2025-11-28", 4000000, 24700000),
        ("Sunflower Accessories Co.", "2025-11-29", 2000000, 6740000),
    ]

    purchase_invoices = []
    for definition in purchase_definitions:
        invoice_name = _create_purchase_invoice(definition)
        purchase_invoices.append(
            {
                "supplier": definition["supplier"],
                "purchase_invoice": invoice_name,
                "grand_total": definition["expected_total"],
            }
        )
        frappe.db.commit()

    sales_invoices = []
    invoice_map = {}
    for definition in sales_definitions:
        invoice_name = _create_sales_invoice(definition)
        invoice_map[(definition["customer"], definition["expected_total"])] = invoice_name
        sales_invoices.append(
            {
                "customer": definition["customer"],
                "sales_invoice": invoice_name,
                "grand_total": definition["expected_total"],
            }
        )
        frappe.db.commit()

    payment_entries = []
    for customer, posting_date, amount, expected_total in customer_payment_specs:
        payment_name = _create_partial_payment(
            "Sales Invoice",
            invoice_map[(customer, expected_total)],
            posting_date,
            amount,
        )
        payment_entries.append(
            {
                "party_type": "Customer",
                "party": customer,
                "payment_entry": payment_name,
                "amount": amount,
            }
        )
        frappe.db.commit()

    purchase_invoice_map = {}
    for invoice in frappe.get_all(
        "Purchase Invoice",
        filters={"posting_date": ["between", ["2025-11-01", "2025-11-30"]], "docstatus": 1},
        fields=["name", "supplier", "grand_total"],
    ):
        purchase_invoice_map[(invoice.supplier, int(round(invoice.grand_total)))] = invoice.name

    for supplier, posting_date, amount, expected_total in supplier_payment_specs:
        payment_name = _create_partial_payment(
            "Purchase Invoice",
            purchase_invoice_map[(supplier, expected_total)],
            posting_date,
            amount,
        )
        payment_entries.append(
            {
                "party_type": "Supplier",
                "party": supplier,
                "payment_entry": payment_name,
                "amount": amount,
            }
        )
        frappe.db.commit()

    return {
        "purchase_invoices": purchase_invoices,
        "sales_invoices": sales_invoices,
        "payment_entries": payment_entries,
    }


def create_december_2025_commercial_batch() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."

    sales_definitions = [
        {
            "customer": "Hledan Phone Hub",
            "posting_date": "2025-12-10",
            "due_date": "2026-01-09",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 8750000,
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 1, "rate": 1765000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 1100000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 955000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 31000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 30, "rate": 14000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 1, "rate": 170000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 1, "rate": 215000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 4, "rate": 5000},
            ],
        },
        {
            "customer": "Hlaing Tharyar Mobile Corner",
            "posting_date": "2025-12-25",
            "due_date": "2026-01-24",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 10065000,
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 1, "rate": 1765000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 3, "rate": 1100000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 955000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 100000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 31000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 2, "rate": 170000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 10, "rate": 14000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 16, "rate": 5000},
            ],
        },
        {
            "customer": "Latha Mobile Wholesale",
            "posting_date": "2025-12-19",
            "due_date": "2026-01-08",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 8510000,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 955000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 1100000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 9, "rate": 100000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 30, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 31000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 2, "rate": 215000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 22, "rate": 5000},
            ],
        },
        {
            "customer": "Thingangyun Mobile House",
            "posting_date": "2025-12-26",
            "due_date": "2026-01-25",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 9470000,
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 2, "rate": 1765000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 1100000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 11, "rate": 100000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 31000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 3, "rate": 215000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
                {"item_code": "MEM-MSD-SND-128", "qty": 5, "rate": 26000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 11, "rate": 5000},
            ],
        },
        {
            "customer": "Taunggyi City Mobile",
            "posting_date": "2025-12-21",
            "due_date": "2026-01-10",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 7650000,
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 2, "rate": 1765000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 1, "rate": 1100000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 1, "rate": 955000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 100000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 31000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 23, "rate": 5000},
            ],
        },
        {
            "customer": "Mayangone Mobile House",
            "posting_date": "2025-12-27",
            "due_date": "2026-02-10",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 7095000,
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 1, "rate": 1765000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 1, "rate": 1100000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 11, "rate": 100000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 5, "rate": 215000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 30, "rate": 14000},
                {"item_code": "MEM-MSD-SND-128", "qty": 15, "rate": 26000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 5, "rate": 5000},
            ],
        },
        {
            "customer": "Lanmadaw Telecom & Gadgets",
            "posting_date": "2025-12-26",
            "due_date": "2026-01-10",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 9985000,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 3, "rate": 1100000},
                {"item_code": "SPH-APP-IP13-128", "qty": 1, "rate": 1765000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 17, "rate": 215000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 15, "rate": 32000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 30, "rate": 14000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 31000},
                {"item_code": "MEM-MSD-SND-128", "qty": 10, "rate": 26000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 11, "rate": 5000},
            ],
        },
        {
            "customer": "Mandalay Accessories Wholesale",
            "posting_date": "2025-12-27",
            "due_date": "2026-01-11",
            "warehouse": "Mandalay Warehouse - MMOB",
            "company": company,
            "expected_total": 8640000,
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 2, "rate": 1765000, "warehouse": "Mandalay Warehouse - MMOB"},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 1100000, "warehouse": "Mandalay Warehouse - MMOB"},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 30, "rate": 32000, "warehouse": "Mandalay Warehouse - MMOB"},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 31000, "warehouse": "Mandalay Warehouse - MMOB"},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 2, "rate": 215000, "warehouse": "Mandalay Warehouse - MMOB"},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 15, "rate": 14000, "warehouse": "Mandalay Warehouse - MMOB"},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 6, "rate": 100000, "warehouse": "Mandalay Warehouse - MMOB"},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 18, "rate": 5000, "warehouse": "Mandalay Warehouse - MMOB"},
            ],
        },
        {
            "customer": "Taunggyi Star Mobile",
            "posting_date": "2025-12-28",
            "due_date": "2026-01-27",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 7219000,
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 1, "rate": 1765000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 955000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 11, "rate": 100000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 21, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 31000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 2, "rate": 215000},
                {"item_code": "MEM-MSD-SND-128", "qty": 4, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 2, "rate": 14000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 2, "rate": 5000},
            ],
        },
        {
            "customer": "City Mobile Mart",
            "posting_date": "2025-12-29",
            "due_date": "2025-12-29",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 5530000,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 955000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 100000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 31000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 2, "rate": 215000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 5, "rate": 58000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 30, "rate": 14000},
                {"item_code": "MEM-USB-SND-64", "qty": 10, "rate": 14000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 16, "rate": 5000},
            ],
        },
        {
            "customer": "Hledan Mobile Trade Center",
            "posting_date": "2025-12-30",
            "due_date": "2026-01-06",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 3960000,
            "items": [
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 9, "rate": 215000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 30, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 31000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 10, "rate": 14000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 6, "rate": 100000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 3, "rate": 5000},
            ],
        },
    ]

    customer_payment_specs = [
        ("Hledan Phone Hub", "2025-12-21", 3000000, 8750000),
        ("Hlaing Tharyar Mobile Corner", "2025-12-27", 3500000, 10065000),
        ("Thingangyun Mobile House", "2025-12-29", 3000000, 9470000),
        ("Latha Mobile Wholesale", "2025-12-26", 2500000, 8510000),
        ("Taunggyi City Mobile", "2025-12-31", 2000000, 7650000),
        ("Taunggyi Star Mobile", "2025-12-31", 2000000, 7219000),
        ("Mayangone Mobile House", "2025-12-30", 2500000, 7095000),
        ("Lanmadaw Telecom & Gadgets", "2025-12-30", 2500000, 9985000),
        ("Mandalay Accessories Wholesale", "2025-12-31", 3000000, 8640000),
        ("City Mobile Mart", "2025-12-31", 2000000, 5530000),
        ("Hledan Mobile Trade Center", "2025-12-31", 1500000, 3960000),
    ]

    supplier_payment_specs = [
        ("Golden Dragon Trading Co. Ltd.", "2025-12-18", 5000000, 22500000),
        ("Myanmar Tech Import Services", "2025-12-27", 5000000, 22627000),
        ("Sunflower Accessories Co.", "2025-12-30", 5000000, 23210000),
    ]

    sales_invoices = []
    invoice_map = {}
    for definition in sales_definitions:
        invoice_name = _create_sales_invoice(definition)
        invoice_map[(definition["customer"], definition["expected_total"])] = invoice_name
        sales_invoices.append(
            {
                "customer": definition["customer"],
                "sales_invoice": invoice_name,
                "grand_total": definition["expected_total"],
            }
        )
        frappe.db.commit()

    payment_entries = []
    for customer, posting_date, amount, expected_total in customer_payment_specs:
        payment_name = _create_partial_payment(
            "Sales Invoice",
            invoice_map[(customer, expected_total)],
            posting_date,
            amount,
        )
        payment_entries.append(
            {
                "party_type": "Customer",
                "party": customer,
                "payment_entry": payment_name,
                "amount": amount,
            }
        )
        frappe.db.commit()

    purchase_invoice_map = {}
    for invoice in frappe.get_all(
        "Purchase Invoice",
        filters={"posting_date": ["between", ["2025-12-01", "2025-12-31"]], "docstatus": 1},
        fields=["name", "supplier", "grand_total"],
    ):
        purchase_invoice_map[(invoice.supplier, int(round(invoice.grand_total)))] = invoice.name

    for supplier, posting_date, amount, expected_total in supplier_payment_specs:
        payment_name = _create_partial_payment(
            "Purchase Invoice",
            purchase_invoice_map[(supplier, expected_total)],
            posting_date,
            amount,
        )
        payment_entries.append(
            {
                "party_type": "Supplier",
                "party": supplier,
                "payment_entry": payment_name,
                "amount": amount,
            }
        )
        frappe.db.commit()

    return {
        "sales_invoices": sales_invoices,
        "payment_entries": payment_entries,
    }


def create_december_2025_completion_batch() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."

    remaining_sales_definitions = [
        {
            "customer": "Lanmadaw Telecom & Gadgets",
            "posting_date": "2025-12-26",
            "due_date": "2026-01-10",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 9985000,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 3, "rate": 1100000},
                {"item_code": "SPH-APP-IP13-128", "qty": 1, "rate": 1765000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 17, "rate": 215000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 15, "rate": 32000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 30, "rate": 14000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 31000},
                {"item_code": "MEM-MSD-SND-128", "qty": 10, "rate": 26000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 11, "rate": 5000},
            ],
        },
        {
            "customer": "Mandalay Accessories Wholesale",
            "posting_date": "2025-12-27",
            "due_date": "2026-01-11",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 8640000,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 955000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 1100000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 14, "rate": 31000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 3, "rate": 215000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 19, "rate": 14000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 18, "rate": 100000},
                {"item_code": "MEM-MSD-SND-128", "qty": 3, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 23, "rate": 14000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 69, "rate": 5000},
            ],
        },
        {
            "customer": "Taunggyi Star Mobile",
            "posting_date": "2025-12-28",
            "due_date": "2026-01-27",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 7219000,
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 1, "rate": 1765000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 955000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 11, "rate": 100000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 21, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 31000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 6, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 2, "rate": 215000},
                {"item_code": "MEM-MSD-SND-128", "qty": 4, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 10, "rate": 14000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 26, "rate": 5000},
            ],
        },
        {
            "customer": "City Mobile Mart",
            "posting_date": "2025-12-29",
            "due_date": "2025-12-29",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 5530000,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 955000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 100000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 31000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 2, "rate": 215000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 5, "rate": 58000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 30, "rate": 14000},
                {"item_code": "MEM-USB-SND-64", "qty": 10, "rate": 14000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 16, "rate": 5000},
            ],
        },
        {
            "customer": "Hledan Mobile Trade Center",
            "posting_date": "2025-12-30",
            "due_date": "2026-01-06",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 3960000,
            "items": [
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 9, "rate": 215000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 30, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 31000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 10, "rate": 14000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 6, "rate": 100000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 3, "rate": 5000},
            ],
        },
    ]

    customer_payment_specs = [
        ("Hledan Phone Hub", "2025-12-21", 3000000, 8750000),
        ("Latha Mobile Wholesale", "2025-12-26", 2500000, 8510000),
        ("Taunggyi City Mobile", "2025-12-31", 2000000, 7650000),
        ("Hlaing Tharyar Mobile Corner", "2025-12-27", 3500000, 10065000),
        ("Thingangyun Mobile House", "2025-12-29", 3000000, 9470000),
        ("Mayangone Mobile House", "2025-12-30", 2500000, 7095000),
        ("Lanmadaw Telecom & Gadgets", "2025-12-30", 2500000, 9985000),
        ("Mandalay Accessories Wholesale", "2025-12-31", 3000000, 8640000),
        ("Taunggyi Star Mobile", "2025-12-31", 2000000, 7219000),
        ("City Mobile Mart", "2025-12-31", 2000000, 5530000),
        ("Hledan Mobile Trade Center", "2025-12-31", 1500000, 3960000),
    ]

    supplier_payment_specs = [
        ("Golden Dragon Trading Co. Ltd.", "2025-12-18", 5000000, 22500000),
        ("Myanmar Tech Import Services", "2025-12-27", 5000000, 22627000),
        ("Sunflower Accessories Co.", "2025-12-30", 5000000, 23210000),
    ]

    sales_invoices = []
    for definition in remaining_sales_definitions:
        invoice_name = _create_sales_invoice(definition)
        sales_invoices.append(
            {
                "customer": definition["customer"],
                "sales_invoice": invoice_name,
                "grand_total": definition["expected_total"],
            }
        )
        frappe.db.commit()

    invoice_map = {}
    for customer, _, _, expected_total in customer_payment_specs:
        matches = frappe.get_all(
            "Sales Invoice",
            filters={"customer": customer, "docstatus": 1},
            fields=["name", "grand_total"],
            limit=20,
        )
        for invoice in matches:
            if int(round(invoice.grand_total or 0)) == int(round(expected_total)):
                invoice_map[(customer, expected_total)] = invoice.name
                break

    payment_entries = []
    for customer, posting_date, amount, expected_total in customer_payment_specs:
        payment_name = _create_partial_payment(
            "Sales Invoice",
            invoice_map[(customer, expected_total)],
            posting_date,
            amount,
        )
        payment_entries.append(
            {
                "party_type": "Customer",
                "party": customer,
                "payment_entry": payment_name,
                "amount": amount,
            }
        )
        frappe.db.commit()

    purchase_invoice_map = {}
    for invoice in frappe.get_all(
        "Purchase Invoice",
        filters={"posting_date": ["between", ["2025-12-01", "2025-12-31"]], "docstatus": 1},
        fields=["name", "supplier", "grand_total"],
    ):
        purchase_invoice_map[(invoice.supplier, int(round(invoice.grand_total)))] = invoice.name

    for supplier, posting_date, amount, expected_total in supplier_payment_specs:
        payment_name = _create_partial_payment(
            "Purchase Invoice",
            purchase_invoice_map[(supplier, expected_total)],
            posting_date,
            amount,
        )
        payment_entries.append(
            {
                "party_type": "Supplier",
                "party": supplier,
                "payment_entry": payment_name,
                "amount": amount,
            }
        )
        frappe.db.commit()

    return {
        "sales_invoices": sales_invoices,
        "payment_entries": payment_entries,
    }


def _find_submitted_sales_invoice(
    customer: str,
    posting_date: str,
    expected_total: float | None = None,
) -> str | None:
    matches = frappe.get_all(
        "Sales Invoice",
        filters={
            "customer": customer,
            "posting_date": posting_date,
            "docstatus": 1,
        },
        fields=["name", "grand_total"],
        order_by="creation asc",
    )
    if expected_total is not None:
        for match in matches:
            if int(round(match.grand_total or 0)) == int(round(expected_total)):
                return match.name
    if len(matches) == 1:
        return matches[0].name
    return None


def _find_submitted_purchase_invoice(
    supplier: str,
    posting_date: str,
    expected_total: float | None = None,
) -> str | None:
    matches = frappe.get_all(
        "Purchase Invoice",
        filters={
            "supplier": supplier,
            "posting_date": posting_date,
            "docstatus": 1,
        },
        fields=["name", "grand_total"],
        order_by="creation asc",
    )
    if expected_total is not None:
        for match in matches:
            if int(round(match.grand_total or 0)) == int(round(expected_total)):
                return match.name
    if len(matches) == 1:
        return matches[0].name
    return None


def post_december_2025_remaining_sales_invoices() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    definitions = [
        {
            "customer": "Mandalay Accessories Wholesale",
            "posting_date": "2025-12-27",
            "due_date": "2026-01-11",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 8640000,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 955000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 1100000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 32, "rate": 31000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 2, "rate": 215000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 19, "rate": 14000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 17, "rate": 100000},
                {"item_code": "MEM-MSD-SND-128", "qty": 3, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 11, "rate": 14000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 54, "rate": 5000},
            ],
        },
        {
            "customer": "Taunggyi Star Mobile",
            "posting_date": "2025-12-28",
            "due_date": "2026-01-27",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 7219000,
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 1, "rate": 1765000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 955000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 13, "rate": 100000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 18, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 22, "rate": 31000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 1, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 2, "rate": 215000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 5, "rate": 14000},
                {"item_code": "MEM-MSD-SND-128", "qty": 4, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 11, "rate": 14000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 34, "rate": 5000},
            ],
        },
        {
            "customer": "City Mobile Mart",
            "posting_date": "2025-12-29",
            "due_date": "2025-12-29",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 5530000,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 955000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 100000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 31000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 2, "rate": 215000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 5, "rate": 58000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 30, "rate": 14000},
                {"item_code": "MEM-USB-SND-64", "qty": 10, "rate": 14000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 16, "rate": 5000},
            ],
        },
        {
            "customer": "Hledan Mobile Trade Center",
            "posting_date": "2025-12-30",
            "due_date": "2026-01-06",
            "warehouse": "Yangon Main Warehouse - MMOB",
            "company": company,
            "expected_total": 3960000,
            "items": [
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 9, "rate": 215000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 30, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 31000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 10, "rate": 14000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 6, "rate": 100000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 3, "rate": 5000},
            ],
        },
    ]

    created = []
    skipped = []
    failed = []

    for definition in definitions:
        existing_name = _find_submitted_sales_invoice(
            definition["customer"],
            definition["posting_date"],
            definition["expected_total"],
        )
        if existing_name:
            skipped.append(
                {
                    "customer": definition["customer"],
                    "sales_invoice": existing_name,
                    "reason": "existing",
                }
            )
            continue

        try:
            invoice_name = _create_sales_invoice(definition)
            frappe.db.commit()
            created.append(
                {
                    "customer": definition["customer"],
                    "sales_invoice": invoice_name,
                    "grand_total": definition["expected_total"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            failed.append(
                {
                    "customer": definition["customer"],
                    "expected_total": definition["expected_total"],
                    "error": str(exc),
                }
            )

    return {
        "created": created,
        "skipped": skipped,
        "failed": failed,
    }


def post_december_2025_supporting_replenishment_invoices() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    definitions = [
        {
            "supplier": "Myanmar Tech Import Services",
            "posting_date": "2025-12-27",
            "due_date": "2026-01-26",
            "company": company,
            "expected_total": 4650000,
            "items": [
                {
                    "item_code": "SPH-APP-IP13-128",
                    "qty": 3,
                    "rate": 1550000,
                    "warehouse": "Yangon Main Warehouse - MMOB",
                },
            ],
        },
        {
            "supplier": "Sunflower Accessories Co.",
            "posting_date": "2025-12-27",
            "due_date": "2026-01-26",
            "company": company,
            "expected_total": 420000,
            "items": [
                {
                    "item_code": "ACC-CHR-SAM-25W",
                    "qty": 20,
                    "rate": 21000,
                    "warehouse": "Yangon Main Warehouse - MMOB",
                },
            ],
        },
        {
            "supplier": "Sunflower Accessories Co.",
            "posting_date": "2025-12-28",
            "due_date": "2026-01-27",
            "company": company,
            "expected_total": 1030000,
            "items": [
                {
                    "item_code": "ACC-CHR-SAM-25W",
                    "qty": 30,
                    "rate": 21000,
                    "warehouse": "Yangon Main Warehouse - MMOB",
                },
                {
                    "item_code": "ACC-CHR-XMI-33W",
                    "qty": 20,
                    "rate": 20000,
                    "warehouse": "Yangon Main Warehouse - MMOB",
                },
            ],
        },
        {
            "supplier": "Sunflower Accessories Co.",
            "posting_date": "2025-12-29",
            "due_date": "2026-01-28",
            "company": company,
            "expected_total": 2100000,
            "items": [
                {
                    "item_code": "ACC-CHR-SAM-25W",
                    "qty": 100,
                    "rate": 21000,
                    "warehouse": "Yangon Main Warehouse - MMOB",
                },
            ],
        },
    ]

    created = []
    skipped = []
    failed = []

    for definition in definitions:
        existing_name = _find_submitted_purchase_invoice(
            definition["supplier"],
            definition["posting_date"],
            definition["expected_total"],
        )
        if existing_name:
            skipped.append(
                {
                    "supplier": definition["supplier"],
                    "purchase_invoice": existing_name,
                    "reason": "existing",
                }
            )
            continue

        try:
            invoice_name = _create_purchase_invoice(definition)
            frappe.db.commit()
            created.append(
                {
                    "supplier": definition["supplier"],
                    "purchase_invoice": invoice_name,
                    "grand_total": definition["expected_total"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            failed.append(
                {
                    "supplier": definition["supplier"],
                    "expected_total": definition["expected_total"],
                    "error": str(exc),
                }
            )

    return {
        "created": created,
        "skipped": skipped,
        "failed": failed,
    }


def post_december_2025_planned_payments() -> dict[str, Any]:
    customer_payment_specs = [
        ("Hledan Phone Hub", "2025-12-10", "2025-12-21", 3000000, 8750000),
        ("Latha Mobile Wholesale", "2025-12-19", "2025-12-26", 2500000, 8510000),
        ("Taunggyi City Mobile", "2025-12-21", "2025-12-31", 2000000, 7650000),
        ("Hlaing Tharyar Mobile Corner", "2025-12-25", "2025-12-27", 3500000, 10065000),
        ("Thingangyun Mobile House", "2025-12-26", "2025-12-29", 3000000, 9470000),
        ("Lanmadaw Telecom & Gadgets", "2025-12-26", "2025-12-30", 2500000, None),
        ("Mayangone Mobile House", "2025-12-27", "2025-12-30", 2500000, 7095000),
        ("Taunggyi Star Mobile", "2025-12-28", "2025-12-31", 2000000, 7219000),
        ("City Mobile Mart", "2025-12-29", "2025-12-31", 2000000, 5530000),
        ("Hledan Mobile Trade Center", "2025-12-30", "2025-12-31", 1500000, 3960000),
        ("Mandalay Accessories Wholesale", "2025-12-27", "2025-12-31", 3000000, 8640000),
    ]

    supplier_payment_specs = [
        ("Golden Dragon Trading Co. Ltd.", "2025-12-09", "2025-12-18", 5000000, 22500000),
        ("Myanmar Tech Import Services", "2025-12-17", "2025-12-27", 5000000, 22627000),
        ("Sunflower Accessories Co.", "2025-12-24", "2025-12-30", 5000000, 23210000),
    ]

    created = []
    skipped = []
    missing = []

    for customer, invoice_posting_date, payment_posting_date, amount, expected_total in customer_payment_specs:
        invoice_name = _find_submitted_sales_invoice(customer, invoice_posting_date, expected_total)
        if not invoice_name:
            missing.append(
                {
                    "party_type": "Customer",
                    "party": customer,
                    "posting_date": invoice_posting_date,
                    "amount": amount,
                    "reason": "invoice_missing",
                }
            )
            continue

        payment_name = _create_partial_payment(
            "Sales Invoice",
            invoice_name,
            payment_posting_date,
            amount,
        )
        if frappe.db.exists("Payment Entry", payment_name):
            frappe.db.commit()
        if frappe.get_all(
            "Payment Entry Reference",
            filters={
                "reference_doctype": "Sales Invoice",
                "reference_name": invoice_name,
                "allocated_amount": amount,
                "parent": payment_name,
                "docstatus": 1,
            },
            fields=["name"],
            limit=1,
        ):
            created.append(
                {
                    "party_type": "Customer",
                    "party": customer,
                    "payment_entry": payment_name,
                    "amount": amount,
                }
            )
        else:
            skipped.append(
                {
                    "party_type": "Customer",
                    "party": customer,
                    "payment_entry": payment_name,
                    "amount": amount,
                    "reason": "not_linked",
                }
            )

    for supplier, invoice_posting_date, payment_posting_date, amount, expected_total in supplier_payment_specs:
        invoice_name = _find_submitted_purchase_invoice(supplier, invoice_posting_date, expected_total)
        if not invoice_name:
            missing.append(
                {
                    "party_type": "Supplier",
                    "party": supplier,
                    "posting_date": invoice_posting_date,
                    "amount": amount,
                    "reason": "invoice_missing",
                }
            )
            continue

        payment_name = _create_partial_payment(
            "Purchase Invoice",
            invoice_name,
            payment_posting_date,
            amount,
        )
        if frappe.db.exists("Payment Entry", payment_name):
            frappe.db.commit()
        if frappe.get_all(
            "Payment Entry Reference",
            filters={
                "reference_doctype": "Purchase Invoice",
                "reference_name": invoice_name,
                "allocated_amount": amount,
                "parent": payment_name,
                "docstatus": 1,
            },
            fields=["name"],
            limit=1,
        ):
            created.append(
                {
                    "party_type": "Supplier",
                    "party": supplier,
                    "payment_entry": payment_name,
                    "amount": amount,
                }
            )
        else:
            skipped.append(
                {
                    "party_type": "Supplier",
                    "party": supplier,
                    "payment_entry": payment_name,
                    "amount": amount,
                    "reason": "not_linked",
                }
            )

    return {
        "created": created,
        "skipped": skipped,
        "missing": missing,
    }


def post_december_2025_mandalay_final_invoice() -> dict[str, Any]:
    definition = {
        "customer": "Mandalay Accessories Wholesale",
        "posting_date": "2025-12-27",
        "due_date": "2026-01-11",
        "warehouse": "Yangon Main Warehouse - MMOB",
        "company": "Mingalar Mobile Distribution Co., Ltd.",
        "expected_total": 8640000,
        "items": [
            {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 955000},
            {"item_code": "SPH-XMI-RN13-8/256", "qty": 4, "rate": 1100000},
            {"item_code": "ACC-PWB-BAS-20K", "qty": 16, "rate": 100000},
            {"item_code": "MEM-MSD-SND-128", "qty": 10, "rate": 26000},
            {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 14000},
            {"item_code": "ACC-CBL-BAS-TC1M", "qty": 38, "rate": 5000},
        ],
    }

    existing_name = _find_submitted_sales_invoice(
        definition["customer"],
        definition["posting_date"],
        definition["expected_total"],
    )
    if existing_name:
        return {"status": "existing", "sales_invoice": existing_name}

    invoice_name = _create_sales_invoice(definition)
    frappe.db.commit()
    return {
        "status": "created",
        "sales_invoice": invoice_name,
        "grand_total": definition["expected_total"],
    }


def apply_december_2025_credit_limit_closeout_adjustment() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    targets = {
        "Mandalay Accessories Wholesale": 30000000,
    }

    updated = []
    created = []

    for customer_name, credit_limit in targets.items():
        customer = frappe.get_doc("Customer", customer_name)
        row = None
        for credit_row in customer.credit_limits:
            if credit_row.company == company:
                row = credit_row
                break

        if row:
            row.credit_limit = credit_limit
            row.bypass_credit_limit_check = 0
            updated.append({"customer": customer_name, "credit_limit": credit_limit})
        else:
            customer.append(
                "credit_limits",
                {
                    "company": company,
                    "credit_limit": credit_limit,
                    "bypass_credit_limit_check": 0,
                },
            )
            created.append({"customer": customer_name, "credit_limit": credit_limit})

        customer.save(ignore_permissions=True)
        frappe.db.commit()

    return {
        "updated": updated,
        "created": created,
    }


def normalize_apr_dec_2025_historical_workflow() -> dict[str, Any]:
    expired_quotations = [
        "SAL-QTN-2026-00195",
        "SAL-QTN-2026-00196",
        "SAL-QTN-2026-00198",
        "SAL-QTN-2026-00201",
        "SAL-QTN-2026-00205",
        "SAL-QTN-2026-00207",
        "SAL-QTN-2026-00211",
        "SAL-QTN-2026-00212",
    ]
    lost_quotations = [
        "SAL-QTN-2026-00197",
        "SAL-QTN-2026-00199",
        "SAL-QTN-2026-00200",
        "SAL-QTN-2026-00202",
        "SAL-QTN-2026-00203",
        "SAL-QTN-2026-00204",
        "SAL-QTN-2026-00206",
        "SAL-QTN-2026-00208",
        "SAL-QTN-2026-00209",
        "SAL-QTN-2026-00210",
    ]

    completed_sales_orders = [
        "SAL-ORD-2026-00295",
        "SAL-ORD-2026-00296",
        "SAL-ORD-2026-00299",
        "SAL-ORD-2026-00300",
        "SAL-ORD-2026-00301",
        "SAL-ORD-2026-00302",
        "SAL-ORD-2026-00303",
        "SAL-ORD-2026-00305",
        "SAL-ORD-2026-00306",
    ]
    closed_sales_orders = [
        "SAL-ORD-2026-00297",
        "SAL-ORD-2026-00298",
        "SAL-ORD-2026-00304",
        "SAL-ORD-2026-00307",
        "SAL-ORD-2026-00308",
    ]
    completed_delivery_notes = [
        "MAT-DN-2026-00272",
        "MAT-DN-2026-00273",
        "MAT-DN-2026-00274",
        "MAT-DN-2026-00275",
        "MAT-DN-2026-00276",
        "MAT-DN-2026-00277",
    ]

    result = {
        "quotations_expired": [],
        "quotations_lost": [],
        "sales_orders_completed": [],
        "sales_orders_closed": [],
        "delivery_notes_completed": [],
    }

    for name in expired_quotations:
        if not frappe.db.exists("Quotation", name):
            continue
        frappe.db.set_value(
            "Quotation",
            name,
            {
                "status": "Expired",
                "order_lost_reason": None,
            },
            update_modified=False,
        )
        frappe.db.commit()
        result["quotations_expired"].append(name)

    for name in lost_quotations:
        if not frappe.db.exists("Quotation", name):
            continue
        status = frappe.db.get_value("Quotation", name, "status")
        if status == "Cancelled":
            continue
        frappe.db.set_value(
            "Quotation",
            name,
            {
                "status": "Lost",
                "order_lost_reason": "Historical non-conversion normalization: customer did not confirm order after pricing follow-up.",
            },
            update_modified=False,
        )
        frappe.db.commit()
        result["quotations_lost"].append(name)

    for name in completed_sales_orders:
        if not frappe.db.exists("Sales Order", name):
            continue
        frappe.db.set_value(
            "Sales Order",
            name,
            {
                "per_delivered": 100,
                "per_billed": 100,
                "status": "Completed",
            },
            update_modified=False,
        )
        result["sales_orders_completed"].append(name)

    if closed_sales_orders:
        from erpnext.selling.doctype.sales_order.sales_order import close_or_unclose_sales_orders

        close_or_unclose_sales_orders(json.dumps(closed_sales_orders), "Closed")
        result["sales_orders_closed"] = list(closed_sales_orders)

    delivery_note_meta = frappe.get_meta("Delivery Note")
    for name in completed_delivery_notes:
        if not frappe.db.exists("Delivery Note", name):
            continue
        values = {"status": "Completed"}
        if delivery_note_meta.has_field("per_billed"):
            values["per_billed"] = 100
        if delivery_note_meta.has_field("per_installed"):
            values["per_installed"] = 100
        frappe.db.set_value("Delivery Note", name, values, update_modified=False)
        result["delivery_notes_completed"].append(name)

    frappe.db.commit()
    return result


def _company_stock_adjustment_account(company: str) -> str | None:
    return frappe.db.get_value("Company", company, "stock_adjustment_account")


def _company_cost_center(company: str) -> str | None:
    return (
        frappe.db.get_value("Company", company, "cost_center")
        or frappe.db.get_value("Company", company, "default_cost_center")
    )


def _find_fiscal_year(target_date: str) -> str | None:
    rows = frappe.db.sql(
        """
        select name
        from `tabFiscal Year`
        where year_start_date <= %s and year_end_date >= %s
        order by year_start_date desc
        limit 1
        """,
        (target_date, target_date),
    )
    return rows[0][0] if rows else None


def _create_stock_reconciliation(
    company: str,
    item_code: str,
    warehouse: str,
    posting_date: str,
    qty: float,
    valuation_rate: float,
    posting_time: str = "18:00:00",
    remarks: str | None = None,
) -> str:
    existing = frappe.db.sql(
        """
        select sr.name
        from `tabStock Reconciliation` sr
        inner join `tabStock Reconciliation Item` sri on sri.parent = sr.name
        where sr.docstatus = 1
          and sr.posting_date = %s
          and sri.item_code = %s
          and sri.warehouse = %s
          and abs(ifnull(sri.qty, 0) - %s) < 0.01
          and abs(ifnull(sri.valuation_rate, 0) - %s) < 0.01
        limit 1
        """,
        (posting_date, item_code, warehouse, qty, valuation_rate),
    )
    if existing:
        return existing[0][0]

    stock_adjustment_account = _company_stock_adjustment_account(company)
    cost_center = _company_cost_center(company)
    if not stock_adjustment_account or not cost_center:
        raise ValueError("Missing stock adjustment account or cost center for stock reconciliation.")

    doc = frappe.get_doc(
        {
            "doctype": "Stock Reconciliation",
            "company": company,
            "posting_date": posting_date,
            "posting_time": posting_time,
            "set_posting_time": 1,
            "purpose": "Stock Reconciliation",
            "remarks": remarks or "FY25/26 stock valuation cleanup to remove negative balance artifacts.",
            "items": [
                {
                    "item_code": item_code,
                    "warehouse": warehouse,
                    "qty": qty,
                    "valuation_rate": valuation_rate,
                    "expense_account": stock_adjustment_account,
                    "cost_center": cost_center,
                }
            ],
        }
    )
    doc.insert(ignore_permissions=True)
    doc.submit()
    return doc.name


def apply_stock_negative_valuation_fix() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    results: dict[str, Any] = {"reconciliations": [], "skipped": [], "failed": []}

    warehouses = frappe.get_all("Warehouse", filters={"company": company}, pluck="name")
    if not warehouses:
        results["skipped"].append({"reason": "no_company_warehouses"})
        return results

    placeholders = ", ".join(["%s"] * len(warehouses))
    bins = frappe.db.sql(
        f"""
        select item_code, warehouse, actual_qty, stock_value, valuation_rate
        from `tabBin`
        where warehouse in ({placeholders})
          and (stock_value < 0 or valuation_rate < 0)
        order by stock_value asc
        limit 5
        """,
        tuple(warehouses),
        as_dict=True,
    )

    if not bins:
        results["skipped"].append({"reason": "no_negative_bins"})
        return results

    for row in bins:
        if row.actual_qty and row.actual_qty > 0:
            results["skipped"].append(
                {
                    "item_code": row.item_code,
                    "warehouse": row.warehouse,
                    "actual_qty": row.actual_qty,
                    "stock_value": row.stock_value,
                    "valuation_rate": row.valuation_rate,
                    "reason": "positive_qty_requires_manual_review",
                }
            )
            continue

        try:
            reconciliation_name = _create_stock_reconciliation(
                company=company,
                item_code=row.item_code,
                warehouse=row.warehouse,
                posting_date="2026-03-31",
                qty=0,
                valuation_rate=0,
            )
            frappe.db.commit()
            results["reconciliations"].append(
                {
                    "stock_reconciliation": reconciliation_name,
                    "item_code": row.item_code,
                    "warehouse": row.warehouse,
                    "actual_qty": row.actual_qty,
                    "stock_value": row.stock_value,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            results["failed"].append(
                {
                    "item_code": row.item_code,
                    "warehouse": row.warehouse,
                    "error": str(exc),
                }
            )

    return results


def run_financial_reports_smoke() -> dict[str, Any]:
    results: dict[str, Any] = {"reports": [], "failed": []}
    for report_name in ["Profit and Loss Statement", "Balance Sheet", "Cash Flow"]:
        try:
            payload = _execute_report_by_name(report_name, _fy2526_financial_report_filters("Monthly", 1))
            results["reports"].append(
                {"report": report_name, "rows": payload["row_count"], "method": "report_execute_module"}
            )
        except Exception as exc:
            results["failed"].append({"report": report_name, "error": str(exc)})

    return results


def debug_financial_report_filters() -> dict[str, Any]:
    report_names = ["Profit and Loss Statement", "Balance Sheet", "Cash Flow"]
    results: dict[str, Any] = {}
    for report_name in report_names:
        try:
            report_doc = frappe.get_doc("Report", report_name)
            filters_info = []
            for row in report_doc.filters or []:
                filters_info.append(
                    {
                        "fieldname": row.fieldname,
                        "label": row.label,
                        "fieldtype": row.fieldtype,
                        "mandatory": row.mandatory,
                    }
                )
            results[report_name] = filters_info
        except Exception as exc:
            results[report_name] = {"error": str(exc)}
    return results


def apply_financial_statement_report_filter_fix() -> dict[str, Any]:
    report_names = ["Profit and Loss Statement", "Balance Sheet", "Cash Flow"]
    results: dict[str, Any] = {"updated": [], "skipped": [], "failed": []}
    default_filters = [
        {"fieldname": "company", "label": "Company", "fieldtype": "Link", "options": "Company", "mandatory": 1},
        {
            "fieldname": "filter_based_on",
            "label": "Filter Based On",
            "fieldtype": "Select",
            "options": "Date Range\nFiscal Year",
            "default": "Date Range",
        },
        {"fieldname": "period_start_date", "label": "From Date", "fieldtype": "Date", "mandatory": 1},
        {"fieldname": "period_end_date", "label": "To Date", "fieldtype": "Date", "mandatory": 1},
        {"fieldname": "from_fiscal_year", "label": "From Fiscal Year", "fieldtype": "Link", "options": "Fiscal Year"},
        {"fieldname": "to_fiscal_year", "label": "To Fiscal Year", "fieldtype": "Link", "options": "Fiscal Year"},
        {
            "fieldname": "periodicity",
            "label": "Periodicity",
            "fieldtype": "Select",
            "options": "Monthly\nQuarterly\nYearly",
            "default": "Monthly",
        },
        {"fieldname": "accumulated_values", "label": "Accumulated Values", "fieldtype": "Check", "default": 1},
        {
            "fieldname": "presentation_currency",
            "label": "Currency",
            "fieldtype": "Link",
            "options": "Currency",
        },
        {
            "fieldname": "show_account_details",
            "label": "Show Account Details",
            "fieldtype": "Select",
            "options": "Summary\nAll",
            "default": "Summary",
        },
        {
            "fieldname": "include_default_book_entries",
            "label": "Include Default Book Entries",
            "fieldtype": "Check",
            "default": 1,
        },
    ]

    for report_name in report_names:
        try:
            report_doc = frappe.get_doc("Report", report_name)
            existing = report_doc.filters or []
            fieldnames = {row.fieldname for row in existing} if existing else set()
            if {"period_start_date", "period_end_date"} <= fieldnames:
                results["skipped"].append({"report": report_name, "reason": "filters_already_present"})
                continue
            report_doc.set("filters", default_filters)
            report_doc.save(ignore_permissions=True)
            results["updated"].append({"report": report_name, "filters": [row["fieldname"] for row in default_filters]})
            frappe.db.commit()
        except Exception as exc:
            frappe.db.rollback()
            results["failed"].append({"report": report_name, "error": str(exc)})

    return results


def debug_financial_report_execute_signatures() -> dict[str, Any]:
    import inspect

    report_paths = {
        "Profit and Loss Statement": "erpnext.accounts.report.profit_and_loss_statement.profit_and_loss_statement.execute",
        "Balance Sheet": "erpnext.accounts.report.balance_sheet.balance_sheet.execute",
        "Cash Flow": "erpnext.accounts.report.cash_flow.cash_flow.execute",
    }
    results: dict[str, Any] = {}
    for report_name, path in report_paths.items():
        try:
            fn = frappe.get_attr(path)
            signature = str(inspect.signature(fn))
            source = inspect.getsource(fn)
            results[report_name] = {
                "signature": signature,
                "source_head": source.splitlines()[:40],
            }
        except Exception as exc:
            results[report_name] = {"error": str(exc)}
    return results


def _fy2526_financial_report_filters(
    periodicity: str = "Monthly",
    accumulated_values: int | None = None,
) -> frappe._dict:
    company = "Mingalar Mobile Distribution Co., Ltd."
    fiscal_filters = {"from_date": "2025-04-01", "to_date": "2026-03-31"}
    fiscal_year = _find_fiscal_year("2025-04-01")

    if accumulated_values is None:
        accumulated_values = 1 if periodicity == "Monthly" else 0

    filters = frappe._dict(
        {
            "company": company,
            "filter_based_on": "Date Range",
            "period_start_date": fiscal_filters["from_date"],
            "period_end_date": fiscal_filters["to_date"],
            "periodicity": periodicity,
            "accumulated_values": accumulated_values,
            "include_default_book_entries": 1,
            "show_opening_and_closing_balance": 1,
            "show_account_details": "Summary",
        }
    )
    if fiscal_year:
        filters.from_fiscal_year = fiscal_year
        filters.to_fiscal_year = fiscal_year
    return filters


def _execute_report_by_name(report_name: str, filters: frappe._dict | dict[str, Any]) -> dict[str, Any]:
    report_doc = frappe.get_doc("Report", report_name)
    data = report_doc.execute_module(filters)

    columns: list[Any] = []
    rows: list[Any] = []
    extras: dict[str, Any] = {}

    if isinstance(data, tuple):
        if len(data) >= 1:
            columns = data[0] or []
        if len(data) >= 2:
            rows = data[1] or []
        if len(data) >= 3:
            extras["message"] = data[2]
        if len(data) >= 4:
            extras["chart"] = data[3]
        if len(data) >= 5:
            extras["summary"] = data[4]
        if len(data) >= 6:
            extras["primitive_summary"] = data[5]
    elif isinstance(data, dict):
        columns = data.get("columns") or []
        rows = data.get("result") or []
        extras = {key: value for key, value in data.items() if key not in {"columns", "result"}}

    return {
        "report": report_name,
        "filters": dict(filters),
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        **extras,
    }


def export_fy2526_financial_statements(
    periodicity: str = "Monthly",
    accumulated_values: int | None = None,
) -> dict[str, Any]:
    report_names = ["Profit and Loss Statement", "Balance Sheet", "Cash Flow"]

    results: dict[str, Any] = {"reports": [], "failed": []}
    for report_name in report_names:
        try:
            filters = _fy2526_financial_report_filters(periodicity, accumulated_values)
            results["reports"].append(_execute_report_by_name(report_name, filters))
        except Exception as exc:
            results["failed"].append({"report": report_name, "error": str(exc)})

    return results


def summarize_fy2526_financial_statements_yearly() -> dict[str, Any]:
    export = export_fy2526_financial_statements(periodicity="Yearly", accumulated_values=0)
    if export.get("failed"):
        return {"status": "failed", "errors": export["failed"]}

    def _amount_fields(columns: list[dict[str, Any]]) -> list[str]:
        return [
            col["fieldname"]
            for col in columns
            if isinstance(col, dict) and str(col.get("fieldname") or "").startswith("total_")
        ]

    def _pick_amount(row: dict[str, Any], fields: list[str]) -> float:
        for field in reversed(fields):
            if row.get(field) not in (None, ""):
                return float(row.get(field) or 0)
        return float(row.get("total") or 0)

    def _find_row(rows: list[dict[str, Any]], labels: list[str]) -> dict[str, Any] | None:
        targets = {label.strip() for label in labels}
        for row in rows:
            for key in ("account", "account_name", "label", "section_name"):
                value = str(row.get(key) or "").strip().strip("'")
                if value in targets:
                    return row
        return None

    report_map = {report["report"]: report for report in export["reports"]}

    pnl = report_map.get("Profit and Loss Statement") or {}
    pnl_fields = _amount_fields(pnl.get("columns") or [])
    pnl_rows = pnl.get("rows") or []
    sales_row = _find_row(pnl_rows, ["Sales - MMOB", "Sales", "Total Income"])
    cogs_row = _find_row(pnl_rows, ["Cost of Goods Sold - MMOB", "Cost of Goods Sold"])
    salary_row = _find_row(pnl_rows, ["Salary - MMOB"])
    rent_row = _find_row(pnl_rows, ["Office Rent - MMOB"])
    utilities_row = _find_row(pnl_rows, ["Utility Expenses - MMOB"])
    admin_row = _find_row(pnl_rows, ["Administrative Expenses - MMOB"])
    stock_adjustment_row = _find_row(pnl_rows, ["Stock Adjustment - MMOB"])
    net_profit_row = _find_row(pnl_rows, ["Net Profit / Loss", "Profit for the year"])

    bs = report_map.get("Balance Sheet") or {}
    bs_fields = _amount_fields(bs.get("columns") or [])
    bs_rows = bs.get("rows") or []
    debtors_row = _find_row(bs_rows, ["Debtors - MMOB"])
    stock_row = _find_row(bs_rows, ["Stock In Hand - MMOB"])
    creditors_row = _find_row(bs_rows, ["Creditors - MMOB"])
    overdraft_row = _find_row(bs_rows, ["Bank Overdraft Account - MMOB"])
    loan_row = _find_row(bs_rows, ["Bank Loan - KBZ - MMOB"])
    retained_row = _find_row(bs_rows, ["Retained Earnings - MMOB"])
    provisional_row = _find_row(bs_rows, ["Provisional Profit / Loss (Credit)"])
    total_asset_row = _find_row(bs_rows, ["Total Asset (Debit)", "Total (Debit)"])
    total_liability_row = _find_row(bs_rows, ["Total (Credit)"])

    cf = report_map.get("Cash Flow") or {}
    cf_fields = _amount_fields(cf.get("columns") or [])
    cf_rows = cf.get("rows") or []
    operations_row = _find_row(cf_rows, ["Net Cash from Operations"])
    investing_row = _find_row(cf_rows, ["Net Cash from Investing"])
    financing_row = _find_row(cf_rows, ["Net Cash from Financing"])
    net_cash_row = _find_row(cf_rows, ["Net Change in Cash"])

    bank_position_audit = audit_fy2526_bank_cash_positions()
    bank_total = sum(float(row.get("balance") or 0) for row in bank_position_audit.get("accounts") or [])

    total_assets = _pick_amount(total_asset_row or {}, bs_fields)
    total_liabilities_and_equity = _pick_amount(total_liability_row or {}, bs_fields)

    return {
        "status": "ok",
        "profit_and_loss": {
            "sales": _pick_amount(sales_row or {}, pnl_fields),
            "cogs": _pick_amount(cogs_row or {}, pnl_fields),
            "salary": _pick_amount(salary_row or {}, pnl_fields),
            "office_rent": _pick_amount(rent_row or {}, pnl_fields),
            "utilities": _pick_amount(utilities_row or {}, pnl_fields),
            "administrative": _pick_amount(admin_row or {}, pnl_fields),
            "stock_adjustment": _pick_amount(stock_adjustment_row or {}, pnl_fields),
            "net_profit": _pick_amount(net_profit_row or {}, pnl_fields),
        },
        "balance_sheet": {
            "debtors": _pick_amount(debtors_row or {}, bs_fields),
            "stock_in_hand": _pick_amount(stock_row or {}, bs_fields),
            "bank_and_cash": bank_total,
            "creditors": _pick_amount(creditors_row or {}, bs_fields),
            "bank_overdraft": _pick_amount(overdraft_row or {}, bs_fields),
            "bank_loan": _pick_amount(loan_row or {}, bs_fields),
            "retained_earnings": _pick_amount(retained_row or {}, bs_fields),
            "provisional_profit_loss": _pick_amount(provisional_row or {}, bs_fields),
            "total_assets": total_assets,
            "total_liabilities_and_equity": total_liabilities_and_equity,
            "balance_gap": round(total_assets - total_liabilities_and_equity, 2),
        },
        "cash_flow": {
            "operations": _pick_amount(operations_row or {}, cf_fields),
            "investing": _pick_amount(investing_row or {}, cf_fields),
            "financing": _pick_amount(financing_row or {}, cf_fields),
            "net_change_in_cash": _pick_amount(net_cash_row or {}, cf_fields),
        },
    }


def summarize_fy2526_financial_statements_enterprise_view() -> dict[str, Any]:
    yearly = summarize_fy2526_financial_statements_yearly()
    expense_mix = audit_fy2526_expense_account_mix()
    cash_flow = audit_fy2526_cash_flow_variance()

    if yearly.get("status") != "ok":
        return yearly

    pnl = yearly.get("profit_and_loss") or {}
    bs = yearly.get("balance_sheet") or {}
    cf = yearly.get("cash_flow") or {}
    expense_accounts = expense_mix.get("accounts") or []
    valuation_offsets = expense_mix.get("valuation_offsets") or []

    def _amount(account_name: str) -> float:
        for row in expense_accounts:
            if str(row.get("account") or "") == account_name:
                return float(row.get("amount") or 0)
        return 0.0

    sales = float(pnl.get("sales") or 0)
    cogs = float(pnl.get("cogs") or 0)
    gross_profit = sales - cogs
    gross_margin_pct = round((gross_profit / sales) * 100, 2) if sales else 0.0

    salary = float(pnl.get("salary") or 0)
    rent = float(pnl.get("office_rent") or 0)
    admin = float(pnl.get("administrative") or 0)
    utilities = float(pnl.get("utilities") or 0)
    depreciation = _amount("Depreciation - MMOB")
    interest = _amount("Interest Expense - Bank Loan - MMOB")
    tax_expense = _amount("Tax Expense - MMOB")
    marketing = _amount("Marketing Expenses - MMOB")
    logistics = _amount("Freight and Forwarding Charges - MMOB")
    telecom = _amount("Telephone Expenses - MMOB")
    sales_expense = _amount("Sales Expenses - MMOB")
    maintenance = _amount("Office Maintenance Expenses - MMOB")
    travel = _amount("Travel Expenses - MMOB")
    stationery = _amount("Print and Stationery - MMOB")
    bank_charges = _amount("Bank Charges - MMOB")
    stock_adjustment = _amount("Stock Adjustment - MMOB")

    operating_opex = (
        salary
        + rent
        + admin
        + utilities
        + marketing
        + logistics
        + telecom
        + sales_expense
        + maintenance
        + travel
        + stationery
        + bank_charges
        + stock_adjustment
    )
    ebitda = gross_profit - (operating_opex - stock_adjustment)
    ebit = gross_profit - operating_opex - depreciation
    profit_after_tax = float(pnl.get("net_profit") or 0)
    profit_before_tax = profit_after_tax + tax_expense
    effective_tax_rate = round((tax_expense / profit_before_tax) * 100, 2) if profit_before_tax else 0.0

    def _balance_upto_fy_end(account_name: str) -> float:
        rows = frappe.db.sql(
            """
            select round(sum(debit_in_account_currency - credit_in_account_currency), 2) as balance
            from `tabGL Entry`
            where company = %s
              and account = %s
              and posting_date <= %s
              and ifnull(is_cancelled, 0) = 0
            """,
            ("Mingalar Mobile Distribution Co., Ltd.", account_name, "2026-03-31"),
            as_dict=True,
        )
        return abs(float((rows[0]["balance"] or 0) if rows else 0))

    payroll_payable = _balance_upto_fy_end("Payroll Payable - MMOB")
    accrued_expenses = _balance_upto_fy_end("Accrued Expenses - MMOB")
    grni_balance = _balance_upto_fy_end("Stock Received But Not Billed - MMOB")
    tax_payable = _balance_upto_fy_end("Income Tax Payable - MMOB")
    unsecured_loans = _balance_upto_fy_end("Unsecured Loans - MMOB")
    secured_loans = _balance_upto_fy_end("Secured Loans - MMOB")
    other_current_liabilities = payroll_payable + accrued_expenses + grni_balance + tax_payable
    interest_bearing_debt = round(
        float(cash_flow.get("borrowing_balance_to_fy_end") or 0) + secured_loans,
        2,
    )

    current_assets = float(bs.get("debtors") or 0) + float(bs.get("stock_in_hand") or 0) + float(bs.get("bank_and_cash") or 0)
    current_liabilities = (
        float(bs.get("creditors") or 0)
        + float(bs.get("bank_overdraft") or 0)
        + other_current_liabilities
    )
    working_capital = round(current_assets - current_liabilities, 2)
    net_bank_position = round(float(bs.get("bank_and_cash") or 0) - float(bs.get("bank_overdraft") or 0), 2)

    equity_total = round(
        float(bs.get("total_liabilities_and_equity") or 0)
        - float(bs.get("creditors") or 0)
        - other_current_liabilities
        - interest_bearing_debt,
        2,
    )
    debt_to_equity = round((interest_bearing_debt / equity_total), 2) if equity_total else None

    return {
        "status": "ok",
        "profit_and_loss": {
            "sales": sales,
            "cogs": cogs,
            "gross_profit": round(gross_profit, 2),
            "gross_margin_pct": gross_margin_pct,
            "operating_opex": round(operating_opex, 2),
            "depreciation": round(depreciation, 2),
            "interest": round(interest, 2),
            "ebitda": round(ebitda, 2),
            "ebit": round(ebit, 2),
            "tax_expense": round(tax_expense, 2),
            "profit_before_tax": round(profit_before_tax, 2),
            "profit_after_tax": round(profit_after_tax, 2),
            "effective_tax_rate_pct": effective_tax_rate,
            "valuation_offsets": valuation_offsets,
        },
        "balance_sheet": {
            "current_assets": round(current_assets, 2),
            "current_liabilities": round(current_liabilities, 2),
            "other_current_liabilities": round(other_current_liabilities, 2),
            "working_capital": working_capital,
            "bank_and_cash": round(float(bs.get("bank_and_cash") or 0), 2),
            "bank_overdraft": round(float(bs.get("bank_overdraft") or 0), 2),
            "net_bank_position": net_bank_position,
            "interest_bearing_debt": interest_bearing_debt,
            "unsecured_loans": round(unsecured_loans, 2),
            "secured_loans": round(secured_loans, 2),
            "equity_total": equity_total,
            "debt_to_equity": debt_to_equity,
        },
        "cash_flow": {
            "operations": round(float(cf.get("operations") or 0), 2),
            "investing": round(float(cf.get("investing") or 0), 2),
            "financing": round(float(cf.get("financing") or 0), 2),
            "net_change_in_cash": round(float(cf.get("net_change_in_cash") or 0), 2),
            "borrowing_balance_to_fy_end": round(float(cash_flow.get("borrowing_balance_to_fy_end") or 0), 2),
        },
    }


def audit_fy2526_tax_posture() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."

    account_rows = frappe.db.sql(
        """
        select a.name,
               a.root_type,
               a.report_type,
               ifnull(a.account_type, '') as account_type,
               round(sum(ifnull(gl.debit_in_account_currency, 0) - ifnull(gl.credit_in_account_currency, 0)), 2) as fy_balance
        from `tabAccount` a
        left join `tabGL Entry` gl
          on gl.account = a.name
         and gl.company = a.company
         and gl.posting_date between '2025-04-01' and '2026-03-31'
        where a.company = %s
          and (
            lower(a.name) like '%%tax%%'
            or lower(a.name) like '%%vat%%'
            or lower(a.name) like '%%duties%%'
            or lower(a.name) like '%%withholding%%'
            or lower(a.name) like '%%commercial%%'
          )
        group by a.name, a.root_type, a.report_type, a.account_type
        order by a.name asc
        """,
        (company,),
        as_dict=True,
    )

    template_summary = []
    for doctype in ("Sales Taxes and Charges Template", "Purchase Taxes and Charges Template"):
        template_name = "Myanamar Tax - MMOB"
        if not frappe.db.exists(doctype, template_name):
            continue
        doc = frappe.get_doc(doctype, template_name)
        template_summary.append(
            {
                "doctype": doctype,
                "name": doc.name,
                "title": getattr(doc, "title", ""),
                "taxes": [
                    {
                        "charge_type": row.charge_type,
                        "account_head": row.account_head,
                        "rate": float(row.rate or 0),
                        "description": row.description,
                    }
                    for row in doc.taxes
                ],
            }
        )

    document_tax_totals = frappe.db.sql(
        """
        select 'Sales Invoice' as doctype, count(*) as doc_count, round(sum(base_total_taxes_and_charges), 2) as tax_amount
        from `tabSales Invoice`
        where docstatus = 1 and posting_date between '2025-04-01' and '2026-03-31'
        union all
        select 'Purchase Invoice' as doctype, count(*) as doc_count, round(sum(base_total_taxes_and_charges), 2) as tax_amount
        from `tabPurchase Invoice`
        where docstatus = 1 and posting_date between '2025-04-01' and '2026-03-31'
        union all
        select 'Sales Order' as doctype, count(*) as doc_count, round(sum(base_total_taxes_and_charges), 2) as tax_amount
        from `tabSales Order`
        where docstatus = 1 and transaction_date between '2025-04-01' and '2026-03-31'
        union all
        select 'Purchase Order' as doctype, count(*) as doc_count, round(sum(base_total_taxes_and_charges), 2) as tax_amount
        from `tabPurchase Order`
        where docstatus = 1 and transaction_date between '2025-04-01' and '2026-03-31'
        """,
        as_dict=True,
    )

    enterprise_view = summarize_fy2526_financial_statements_enterprise_view()
    pnl = enterprise_view.get("profit_and_loss") or {}
    findings = []

    template_rates = [
        float(tax.get("rate") or 0)
        for template in template_summary
        for tax in (template.get("taxes") or [])
    ]
    if any(abs(rate - 5.0) > 0.005 for rate in template_rates):
        findings.append("tax_templates_not_at_general_5_percent_commercial_tax_rate")

    if all(abs(float(row.get("tax_amount") or 0)) < 0.005 for row in document_tax_totals):
        findings.append("no_document_level_tax_recorded_in_fy2526")

    if abs(float(pnl.get("tax_expense") or 0)) < 0.005 and float(pnl.get("profit_before_tax") or 0) > 0:
        findings.append("no_income_tax_provision_recorded_despite_positive_profit_before_tax")

    return {
        "status": "ok",
        "findings": findings,
        "enterprise_tax_view": {
            "profit_before_tax": float(pnl.get("profit_before_tax") or 0),
            "tax_expense": float(pnl.get("tax_expense") or 0),
            "profit_after_tax": float(pnl.get("profit_after_tax") or 0),
            "effective_tax_rate_pct": float(pnl.get("effective_tax_rate_pct") or 0),
        },
        "tax_accounts": account_rows,
        "tax_templates": template_summary,
        "document_tax_totals": document_tax_totals,
    }


def audit_fy2526_industry_standard_statement_posture() -> dict[str, Any]:
    enterprise_view = summarize_fy2526_financial_statements_enterprise_view()
    tax_posture = audit_fy2526_tax_posture()

    pnl = enterprise_view.get("profit_and_loss") or {}
    bs = enterprise_view.get("balance_sheet") or {}
    cf = enterprise_view.get("cash_flow") or {}

    gaps = []
    if abs(float(pnl.get("gross_profit") or 0)) < 0.005:
        gaps.append("gross_profit_missing")
    if abs(float(pnl.get("ebitda") or 0)) < 0.005:
        gaps.append("ebitda_missing")
    if abs(float(pnl.get("ebit") or 0)) < 0.005:
        gaps.append("ebit_missing")
    if abs(float(pnl.get("tax_expense") or 0)) < 0.005 and float(pnl.get("profit_before_tax") or 0) > 0:
        gaps.append("tax_line_not_substantive")
    if abs(float(cf.get("borrowing_balance_to_fy_end") or 0)) > 0.005 and abs(float(cf.get("financing") or 0)) < 0.005:
        gaps.append("native_financing_cash_flow_understates_borrowing_story")
    if float(bs.get("debt_to_equity") or 0) <= 0:
        gaps.append("debt_to_equity_not_computed")

    return {
        "status": "ok",
        "gaps": gaps,
        "statement_view": enterprise_view,
        "tax_posture_findings": tax_posture.get("findings") or [],
    }


def normalize_myanmar_commercial_tax_templates() -> dict[str, Any]:
    result: dict[str, Any] = {"updated": [], "failed": []}
    template_name = "Myanamar Tax - MMOB"
    title_map = {
        "Sales Taxes and Charges Template": "Myanmar Commercial Tax 5% - MMOB",
        "Purchase Taxes and Charges Template": "Myanmar Commercial Tax 5% - MMOB",
    }

    for doctype in ("Sales Taxes and Charges Template", "Purchase Taxes and Charges Template"):
        if not frappe.db.exists(doctype, template_name):
            continue
        try:
            doc = frappe.get_doc(doctype, template_name)
            changed = False
            if getattr(doc, "title", "") != title_map[doctype]:
                doc.title = title_map[doctype]
                changed = True
            for row in doc.taxes:
                if abs(float(row.rate or 0) - 5.0) > 0.005:
                    row.rate = 5.0
                    changed = True
                description = f"Commercial Tax @ {float(row.rate or 0):.1f}%"
                if row.description != description:
                    row.description = description
                    changed = True
            if changed:
                doc.save()
                frappe.db.commit()
                result["updated"].append(
                    {
                        "doctype": doctype,
                        "name": doc.name,
                        "title": doc.title,
                        "rates": [float(row.rate or 0) for row in doc.taxes],
                    }
                )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"doctype": doctype, "name": template_name, "error": str(exc)})

    return result


def _ensure_leaf_account(
    account_name: str,
    company: str,
    parent_account: str,
    root_type: str,
    report_type: str,
    account_type: str = "",
) -> str:
    existing_name = _find_account_by_names([f"{account_name} - MMOB", account_name])
    if existing_name:
        return existing_name

    doc = frappe.get_doc(
        {
            "doctype": "Account",
            "account_name": account_name,
            "company": company,
            "parent_account": parent_account,
            "root_type": root_type,
            "report_type": report_type,
            "account_type": account_type,
            "is_group": 0,
        }
    )
    doc.insert()
    frappe.db.commit()
    return doc.name


def estimate_fy2526_income_tax_provision(rate_pct: float = 22.0) -> dict[str, Any]:
    enterprise_view = summarize_fy2526_financial_statements_enterprise_view()
    pnl = enterprise_view.get("profit_and_loss") or {}
    profit_before_tax = float(pnl.get("profit_before_tax") or 0)
    existing_tax_expense = float(pnl.get("tax_expense") or 0)

    estimated_tax_total = int(round((profit_before_tax * rate_pct / 100.0) / 1000.0) * 1000)
    incremental_tax_required = max(0, estimated_tax_total - int(round(existing_tax_expense)))
    profit_after_tax_if_booked = round(profit_before_tax - estimated_tax_total, 2)
    effective_tax_rate_if_booked = round((estimated_tax_total / profit_before_tax) * 100, 2) if profit_before_tax else 0.0

    return {
        "status": "ok",
        "assumption": {
            "rate_pct": rate_pct,
            "basis": "simplified_estimated_current_income_tax_on_accounting_profit_before_tax",
            "rounding_policy": "nearest_1000_mmk",
        },
        "current": {
            "profit_before_tax": round(profit_before_tax, 2),
            "existing_tax_expense": round(existing_tax_expense, 2),
            "existing_profit_after_tax": round(float(pnl.get("profit_after_tax") or 0), 2),
        },
        "estimate": {
            "estimated_tax_total": estimated_tax_total,
            "incremental_tax_required": incremental_tax_required,
            "profit_after_tax_if_booked": profit_after_tax_if_booked,
            "effective_tax_rate_pct_if_booked": effective_tax_rate_if_booked,
        },
    }


def apply_fy2526_estimated_income_tax_provision(
    rate_pct: float = 22.0,
    posting_date: str = "2026-03-31",
) -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    cost_center = _company_cost_center(company)
    estimate = estimate_fy2526_income_tax_provision(rate_pct=rate_pct)
    incremental_tax_required = int(estimate.get("estimate", {}).get("incremental_tax_required") or 0)

    result: dict[str, Any] = {"before": estimate, "journal_entry": None, "after": None}
    if incremental_tax_required <= 0:
        result["after"] = summarize_fy2526_financial_statements_enterprise_view()
        return result

    tax_expense_account = _find_account_by_names(["Tax Expense - MMOB", "Income Tax Expense - MMOB"])
    if not tax_expense_account:
        raise frappe.ValidationError("Missing Tax Expense account for FY2526 income tax provision.")

    tax_payable_account = _ensure_leaf_account(
        account_name="Income Tax Payable",
        company=company,
        parent_account="Duties and Taxes - MMOB",
        root_type="Liability",
        report_type="Balance Sheet",
        account_type="Tax",
    )

    journal_entry_name = _create_simple_journal_entry(
        {
            "company": company,
            "posting_date": posting_date,
            "voucher_type": "Journal Entry",
            "user_remark": (
                f"AI-FY2526-INCOME-TAX-PROVISION-{posting_date} | "
                f"Estimated current income tax provision at {float(rate_pct):.1f}% of FY2526 profit before tax"
            ),
            "accounts": [
                {
                    "account": tax_expense_account,
                    "debit_in_account_currency": incremental_tax_required,
                    "cost_center": cost_center,
                },
                {
                    "account": tax_payable_account,
                    "credit_in_account_currency": incremental_tax_required,
                    "cost_center": cost_center,
                },
            ],
        }
    )
    frappe.db.commit()

    result["journal_entry"] = {
        "journal_entry": journal_entry_name,
        "tax_expense_account": tax_expense_account,
        "tax_payable_account": tax_payable_account,
        "amount": incremental_tax_required,
        "posting_date": posting_date,
        "rate_pct": rate_pct,
    }
    result["after"] = {
        "enterprise_view": summarize_fy2526_financial_statements_enterprise_view(),
        "tax_posture": audit_fy2526_tax_posture(),
    }
    return result


def audit_apr2026_forward_tax_document_posture() -> dict[str, Any]:
    sales_docs = frappe.db.sql(
        """
        select 'Quotation' as doctype, name, transaction_date as posting_date, party_name as party,
               docstatus, status, grand_total, base_total_taxes_and_charges, taxes_and_charges
        from `tabQuotation`
        where transaction_date between '2026-04-01' and '2026-04-30'
        union all
        select 'Sales Order' as doctype, name, transaction_date as posting_date, customer as party,
               docstatus, status, grand_total, base_total_taxes_and_charges, taxes_and_charges
        from `tabSales Order`
        where transaction_date between '2026-04-01' and '2026-04-30'
        union all
        select 'Sales Invoice' as doctype, name, posting_date as posting_date, customer as party,
               docstatus, status, grand_total, base_total_taxes_and_charges, taxes_and_charges
        from `tabSales Invoice`
        where posting_date between '2026-04-01' and '2026-04-30'
        order by posting_date asc, doctype asc, name asc
        """,
        as_dict=True,
    )
    tax_rows = frappe.db.sql(
        """
        select parenttype, parent, account_head, charge_type, rate,
               round(base_tax_amount_after_discount_amount, 2) as tax_amount
        from `tabSales Taxes and Charges`
        where parenttype in ('Quotation', 'Sales Order', 'Sales Invoice')
          and parent in (
            select name from `tabQuotation` where transaction_date between '2026-04-01' and '2026-04-30'
            union select name from `tabSales Order` where transaction_date between '2026-04-01' and '2026-04-30'
            union select name from `tabSales Invoice` where posting_date between '2026-04-01' and '2026-04-30'
          )
        order by parenttype asc, parent asc
        """,
        as_dict=True,
    )

    malformed = [
        row
        for row in tax_rows
        if str(row.get("account_head") or "") != "VAT - MMOB"
        or abs(float(row.get("rate") or 0) - 5.0) > 0.005
    ]

    return {
        "status": "ok",
        "sales_docs": sales_docs,
        "tax_rows": tax_rows,
        "malformed_tax_rows": malformed,
        "summary": {
            "document_count": len(sales_docs),
            "documents_with_tax_amount": sum(
                1 for row in sales_docs if abs(float(row.get("base_total_taxes_and_charges") or 0)) > 0.005
            ),
            "malformed_tax_row_count": len(malformed),
        },
    }


def _rebuild_sales_tax_rows_from_template(doc, template_name: str | None) -> None:
    doc.set("taxes", [])
    doc.taxes_and_charges = template_name
    if template_name:
        doc.append_taxes_from_master("Sales Taxes and Charges Template")
    doc.calculate_taxes_and_totals()


def apply_apr2026_forward_commercial_tax_realism_wave() -> dict[str, Any]:
    result: dict[str, Any] = {"updated": [], "cleared": [], "failed": [], "after": None}
    template_name = "Myanamar Tax - MMOB"

    # Formal/documented tax-applied pipeline cases for the current live month.
    tax_target_docs = [
        ("Sales Order", "SAL-ORD-2026-00034"),
        ("Sales Order", "SAL-ORD-2026-00035"),
        ("Sales Order", "SAL-ORD-2026-00309"),
    ]
    # Remove malformed tax from the one informal draft quote so the mix stays realistic.
    clear_target_docs = [
        ("Quotation", "SAL-QTN-2026-00213"),
    ]

    for doctype, name in tax_target_docs:
        if not frappe.db.exists(doctype, name):
            continue
        try:
            doc = frappe.get_doc(doctype, name)
            if int(doc.docstatus or 0) != 0:
                result["failed"].append({"doctype": doctype, "name": name, "error": "not_draft"})
                continue
            _rebuild_sales_tax_rows_from_template(doc, template_name)
            doc.save()
            frappe.db.commit()
            result["updated"].append(
                {
                    "doctype": doctype,
                    "name": name,
                    "party": getattr(doc, "customer", None) or getattr(doc, "party_name", None),
                    "grand_total": float(doc.grand_total or 0),
                    "base_total_taxes_and_charges": float(doc.base_total_taxes_and_charges or 0),
                    "taxes_and_charges": doc.taxes_and_charges,
                    "tax_accounts": [row.account_head for row in doc.taxes],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"doctype": doctype, "name": name, "error": str(exc)})

    for doctype, name in clear_target_docs:
        if not frappe.db.exists(doctype, name):
            continue
        try:
            doc = frappe.get_doc(doctype, name)
            if int(doc.docstatus or 0) != 0:
                result["failed"].append({"doctype": doctype, "name": name, "error": "not_draft"})
                continue
            _rebuild_sales_tax_rows_from_template(doc, None)
            doc.save()
            frappe.db.commit()
            result["cleared"].append(
                {
                    "doctype": doctype,
                    "name": name,
                    "party": getattr(doc, "customer", None) or getattr(doc, "party_name", None),
                    "grand_total": float(doc.grand_total or 0),
                    "base_total_taxes_and_charges": float(doc.base_total_taxes_and_charges or 0),
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"doctype": doctype, "name": name, "error": str(exc)})

    result["after"] = audit_apr2026_forward_tax_document_posture()
    return result


def apply_forward_customer_tax_policy_layer() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    result: dict[str, Any] = {
        "tax_category": None,
        "tax_rule": None,
        "customers_updated": [],
        "quotes_updated": [],
        "failed": [],
        "after": None,
    }

    taxable_customer_names = [
        "Capital Telecom (NPT)",
        "Aung Aung Telecom",
        "Mandalay Accessories Wholesale",
        "Hledan Mobile Trade Center",
    ]
    tax_category_name = "Commercial Taxable - MMOB"
    tax_rule_name = "MMOB Sales Commercial Tax 5% - Formal Accounts"
    tax_template_name = "Myanamar Tax - MMOB"

    try:
        if not frappe.db.exists("Tax Category", tax_category_name):
            category_doc = frappe.get_doc(
                {
                    "doctype": "Tax Category",
                    "title": tax_category_name,
                    "disabled": 0,
                }
            )
            category_doc.insert()
            frappe.db.commit()
        result["tax_category"] = tax_category_name
    except Exception as exc:
        frappe.db.rollback()
        result["failed"].append({"stage": "ensure_tax_category", "error": str(exc)})
        return result

    try:
        if frappe.db.exists("Sales Taxes and Charges Template", tax_template_name):
            tax_template = frappe.get_doc("Sales Taxes and Charges Template", tax_template_name)
            changed = False
            if tax_template.tax_category != tax_category_name:
                tax_template.tax_category = tax_category_name
                changed = True
            if changed:
                tax_template.save()
                frappe.db.commit()
    except Exception as exc:
        frappe.db.rollback()
        result["failed"].append({"stage": "link_tax_template_to_category", "error": str(exc)})
        return result

    try:
        if not frappe.db.exists("Tax Rule", tax_rule_name):
            rule_doc = frappe.get_doc(
                {
                    "doctype": "Tax Rule",
                    "title": tax_rule_name,
                    "tax_type": "Sales",
                    "company": company,
                    "tax_category": tax_category_name,
                    "sales_tax_template": tax_template_name,
                    "from_date": "2026-04-01",
                    "priority": 10,
                }
            )
            rule_doc.insert()
            frappe.db.commit()
        result["tax_rule"] = tax_rule_name
    except Exception as exc:
        frappe.db.rollback()
        result["failed"].append({"stage": "ensure_tax_rule", "error": str(exc)})
        return result

    for customer_name in taxable_customer_names:
        if not frappe.db.exists("Customer", customer_name):
            result["failed"].append({"stage": "set_customer_tax_category", "customer": customer_name, "error": "missing_customer"})
            continue
        try:
            customer = frappe.get_doc("Customer", customer_name)
            if customer.tax_category != tax_category_name:
                customer.tax_category = tax_category_name
                customer.save()
                frappe.db.commit()
            result["customers_updated"].append(
                {
                    "customer": customer.name,
                    "customer_group": customer.customer_group,
                    "territory": customer.territory,
                    "tax_category": customer.tax_category,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"stage": "set_customer_tax_category", "customer": customer_name, "error": str(exc)})

    open_quote_rows = frappe.get_all(
        "Quotation",
        filters={
            "docstatus": 1,
            "status": "Open",
            "transaction_date": ["between", ["2026-04-01", "2026-04-30"]],
            "party_name": ["in", taxable_customer_names],
        },
        fields=["name", "party_name", "transaction_date", "grand_total", "base_total_taxes_and_charges"],
        order_by="transaction_date asc, name asc",
    )

    for row in open_quote_rows:
        try:
            doc = frappe.get_doc("Quotation", row.name)
            if int(doc.docstatus or 0) != 1:
                continue
            # Rebuild from the policy-linked template so the quote reflects formal-taxable treatment.
            doc.set("taxes", [])
            doc.taxes_and_charges = tax_template_name
            doc.append_taxes_from_master("Sales Taxes and Charges Template")
            doc.calculate_taxes_and_totals()
            doc.save()
            frappe.db.commit()
            result["quotes_updated"].append(
                {
                    "quotation": doc.name,
                    "customer": doc.party_name,
                    "grand_total": float(doc.grand_total or 0),
                    "base_total_taxes_and_charges": float(doc.base_total_taxes_and_charges or 0),
                    "taxes_and_charges": doc.taxes_and_charges,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"stage": "refresh_open_quotation_tax", "quotation": row.name, "error": str(exc)})

    result["after"] = {
        "forward_tax_posture": audit_apr2026_forward_tax_document_posture(),
        "tax_posture": audit_fy2526_tax_posture(),
    }
    return result


def _quotation_item_signature(items: list[Any]) -> list[tuple[str, float, float, str | None]]:
    signature: list[tuple[str, float, float, str | None]] = []
    for item in items:
        item_code = item.get("item_code") if isinstance(item, dict) else item.item_code
        qty = item.get("qty") if isinstance(item, dict) else item.qty
        rate = item.get("rate") if isinstance(item, dict) else item.rate
        warehouse = item.get("warehouse") if isinstance(item, dict) else item.warehouse
        signature.append(
            (
                item_code,
                float(qty or 0),
                float(rate or 0),
                warehouse or None,
            )
        )
    return sorted(signature)


def _find_existing_draft_quotation_revision(
    customer: str,
    company: str,
    transaction_date: str,
    taxes_and_charges: str,
    items: list[dict[str, Any]],
) -> str | None:
    candidate_rows = frappe.get_all(
        "Quotation",
        filters={
            "docstatus": 0,
            "party_name": customer,
            "company": company,
            "transaction_date": transaction_date,
            "taxes_and_charges": taxes_and_charges,
        },
        fields=["name"],
        order_by="creation asc",
    )
    target_signature = _quotation_item_signature(items)
    for row in candidate_rows:
        candidate = frappe.get_doc("Quotation", row.name)
        if _quotation_item_signature(candidate.items) == target_signature:
            return candidate.name
    return None


def _create_draft_quotation_tax_revision(
    source_quotation_name: str,
    transaction_date: str,
    valid_till: str | None = None,
    tax_template_name: str = "Myanamar Tax - MMOB",
) -> dict[str, Any]:
    if not frappe.db.exists("Quotation", source_quotation_name):
        raise frappe.DoesNotExistError(f"Quotation {source_quotation_name} not found")

    source = frappe.get_doc("Quotation", source_quotation_name)
    customer = frappe.get_doc("Customer", source.party_name)
    transaction_date = str(getdate(transaction_date))
    valid_till = str(getdate(valid_till or add_days(getdate(transaction_date), 7)))

    item_rows = [
        {
            "item_code": item.item_code,
            "qty": float(item.qty or 0),
            "rate": float(item.rate or 0),
            "warehouse": item.warehouse,
        }
        for item in source.items
    ]

    existing_name = _find_existing_draft_quotation_revision(
        customer=source.party_name,
        company=source.company,
        transaction_date=transaction_date,
        taxes_and_charges=tax_template_name,
        items=item_rows,
    )
    if existing_name:
        existing = frappe.get_doc("Quotation", existing_name)
        return {
            "change_type": "existing",
            "source_quotation": source.name,
            "revision_quotation": existing.name,
            "customer": existing.party_name,
            "transaction_date": str(existing.transaction_date),
            "valid_till": str(existing.valid_till),
            "workflow_state": existing.workflow_state,
            "grand_total": float(existing.grand_total or 0),
            "base_total_taxes_and_charges": float(existing.base_total_taxes_and_charges or 0),
            "taxes_and_charges": existing.taxes_and_charges,
        }

    revision = frappe.get_doc(
        {
            "doctype": "Quotation",
            "quotation_to": "Customer",
            "party_name": source.party_name,
            "company": source.company,
            "transaction_date": transaction_date,
            "valid_till": valid_till,
            "currency": source.currency or "MMK",
            "conversion_rate": float(source.conversion_rate or 1),
            "selling_price_list": source.selling_price_list or customer.default_price_list or "Standard Selling",
            "price_list_currency": source.price_list_currency or "MMK",
            "plc_conversion_rate": float(source.plc_conversion_rate or 1),
            "ignore_default_payment_terms_template": 1,
            "payment_terms_template": source.payment_terms_template or customer.payment_terms,
            "order_type": source.order_type or "Sales",
            "tax_category": customer.tax_category or source.tax_category,
            "taxes_and_charges": tax_template_name,
            "terms": (
                f"Commercial-tax revision of approved quotation {source.name}. "
                "Original submitted quotation retained unchanged for audit continuity."
            ),
            "items": [
                {
                    "item_code": item["item_code"],
                    "qty": item["qty"],
                    "warehouse": item["warehouse"],
                    "uom": "Nos",
                    "conversion_factor": 1.0,
                    "price_list_rate": item["rate"],
                    "rate": item["rate"],
                }
                for item in item_rows
            ],
        }
    )
    revision.insert(ignore_permissions=True)
    revision.set("taxes", [])
    revision.append_taxes_from_master("Sales Taxes and Charges Template")
    revision.calculate_taxes_and_totals()
    revision.save(ignore_permissions=True)
    revision.add_comment(
        "Comment",
        text=(
            f"Commercial-tax revision drafted from submitted quotation {source.name} because ERP "
            "does not allow changing the tax template after submission."
        ),
    )
    source.add_comment(
        "Comment",
        text=(
            f"Commercial-tax revision draft {revision.name} created to continue the live commercial "
            "pipeline without rewriting the submitted quotation."
        ),
    )
    frappe.db.commit()
    refreshed = frappe.get_doc("Quotation", revision.name)
    return {
        "change_type": "created",
        "source_quotation": source.name,
        "revision_quotation": refreshed.name,
        "customer": refreshed.party_name,
        "transaction_date": str(refreshed.transaction_date),
        "valid_till": str(refreshed.valid_till),
        "workflow_state": refreshed.workflow_state,
        "grand_total": float(refreshed.grand_total or 0),
        "base_total_taxes_and_charges": float(refreshed.base_total_taxes_and_charges or 0),
        "taxes_and_charges": refreshed.taxes_and_charges,
    }


def apply_apr2026_formal_quote_tax_revision_wave() -> dict[str, Any]:
    revision_specs = [
        {
            "source_quotation": "SAL-QTN-2026-00012",
            "transaction_date": "2026-04-16",
            "valid_till": "2026-04-22",
        },
        {
            "source_quotation": "SAL-QTN-2026-00013",
            "transaction_date": "2026-04-16",
            "valid_till": "2026-04-28",
        },
        {
            "source_quotation": "SAL-QTN-2026-00015",
            "transaction_date": "2026-04-17",
            "valid_till": "2026-04-23",
        },
    ]

    result: dict[str, Any] = {
        "revisions": [],
        "failed": [],
        "after": {},
    }

    for spec in revision_specs:
        try:
            result["revisions"].append(
                _create_draft_quotation_tax_revision(
                    source_quotation_name=spec["source_quotation"],
                    transaction_date=spec["transaction_date"],
                    valid_till=spec["valid_till"],
                )
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "source_quotation": spec["source_quotation"],
                    "stage": "create_revision",
                    "error": str(exc),
                }
            )

    result["after"] = {
        "forward_tax_posture": audit_apr2026_forward_tax_document_posture(),
        "affected_quotes": frappe.db.sql(
            """
            select
                name,
                party_name,
                transaction_date,
                valid_till,
                docstatus,
                status,
                workflow_state,
                taxes_and_charges,
                grand_total,
                base_total_taxes_and_charges
            from `tabQuotation`
            where party_name in ('Aung Aung Telecom', 'Capital Telecom (NPT)', 'Hledan Mobile Trade Center')
              and transaction_date between '2026-04-11' and '2026-04-30'
            order by transaction_date asc, docstatus desc, name asc
            """,
            as_dict=True,
        ),
    }
    return result


def _advance_quotation_workflow_to_state(
    quotation_name: str,
    workflow_actions: list[str] | tuple[str, ...],
    target_state: str,
) -> dict[str, Any]:
    from frappe.model.workflow import apply_workflow

    doc = frappe.get_doc("Quotation", quotation_name)
    if doc.workflow_state == target_state:
        return {
            "quotation": doc.name,
            "change_type": "existing",
            "workflow_state": doc.workflow_state,
            "status": doc.status,
            "docstatus": int(doc.docstatus or 0),
        }

    change_type = "updated"
    for action in workflow_actions:
        doc.reload()
        if doc.workflow_state == target_state:
            break
        doc.flags.ignore_permissions = True
        doc = apply_workflow(doc, action)
        doc.flags.ignore_permissions = True

    doc.reload()
    if doc.workflow_state != target_state:
        frappe.throw(
            f"Quotation {doc.name} ended in workflow state {doc.workflow_state}, expected {target_state}."
        )

    return {
        "quotation": doc.name,
        "change_type": change_type,
        "workflow_state": doc.workflow_state,
        "status": doc.status,
        "docstatus": int(doc.docstatus or 0),
    }


def _retire_superseded_quotation(
    source_quotation_name: str,
    revision_quotation_name: str,
    reason: str,
) -> dict[str, Any]:
    from frappe.model.workflow import apply_workflow

    doc = frappe.get_doc("Quotation", source_quotation_name)
    if doc.workflow_state == "Lost" and doc.status != "Lost":
        frappe.db.set_value(
            "Quotation",
            doc.name,
            {
                "status": "Lost",
                "order_lost_reason": doc.order_lost_reason or reason,
            },
            update_modified=False,
        )
        frappe.db.commit()
        doc.reload()

    if doc.status == "Lost" and doc.workflow_state == "Lost":
        return {
            "quotation": doc.name,
            "change_type": "existing",
            "workflow_state": doc.workflow_state,
            "status": doc.status,
            "order_lost_reason": doc.order_lost_reason,
        }

    frappe.db.set_value(
        "Quotation",
        doc.name,
        "order_lost_reason",
        reason,
        update_modified=False,
    )
    doc.reload()
    if doc.workflow_state == "Approved":
        doc.flags.ignore_permissions = True
        doc = apply_workflow(doc, "Mark Lost")
    else:
        frappe.db.set_value(
            "Quotation",
            doc.name,
            {
                "status": "Lost",
                "order_lost_reason": reason,
            },
            update_modified=False,
        )
        _sync_quotation_workflow_state(doc.name)
        doc = frappe.get_doc("Quotation", doc.name)
    doc.add_comment(
        "Comment",
        text=(
            f"Superseded by revised commercial-tax quotation {revision_quotation_name}. "
            "Original quotation closed to avoid duplicate active commercial promises."
        ),
    )
    if doc.status != "Lost":
        frappe.db.set_value(
            "Quotation",
            doc.name,
            {
                "status": "Lost",
                "order_lost_reason": doc.order_lost_reason or reason,
            },
            update_modified=False,
        )
    frappe.db.commit()
    doc.reload()
    return {
        "quotation": doc.name,
        "change_type": "updated",
        "workflow_state": doc.workflow_state,
        "status": doc.status,
        "order_lost_reason": doc.order_lost_reason,
    }


def apply_apr2026_formal_quote_pipeline_alignment() -> dict[str, Any]:
    alignment_specs = [
        {
            "source_quotation": "SAL-QTN-2026-00012",
            "revision_quotation": "SAL-QTN-2026-00263",
            "workflow_actions": ("Submit Quote", "Approve"),
            "target_workflow_state": "Approved",
            "supersede_reason": (
                "Superseded by revised commercial-tax quotation SAL-QTN-2026-00263 after formal policy alignment."
            ),
        },
        {
            "source_quotation": "SAL-QTN-2026-00013",
            "revision_quotation": "SAL-QTN-2026-00264",
            "workflow_actions": ("Submit Quote", "Escalate", "Approve"),
            "target_workflow_state": "Approved",
            "supersede_reason": (
                "Superseded by revised commercial-tax quotation SAL-QTN-2026-00264 after tax and approval-lane alignment."
            ),
        },
        {
            "source_quotation": "SAL-QTN-2026-00015",
            "revision_quotation": "SAL-QTN-2026-00265",
            "workflow_actions": ("Submit Quote",),
            "target_workflow_state": "Pending Sales Approval",
            "supersede_reason": (
                "Superseded by revised commercial-tax quotation SAL-QTN-2026-00265 now in the active approval queue."
            ),
        },
    ]

    result: dict[str, Any] = {
        "revisions_aligned": [],
        "source_quotes_retired": [],
        "failed": [],
        "after": {},
    }

    for spec in alignment_specs:
        try:
            aligned = _advance_quotation_workflow_to_state(
                quotation_name=spec["revision_quotation"],
                workflow_actions=spec["workflow_actions"],
                target_state=spec["target_workflow_state"],
            )
            result["revisions_aligned"].append(aligned)

            retired = _retire_superseded_quotation(
                source_quotation_name=spec["source_quotation"],
                revision_quotation_name=spec["revision_quotation"],
                reason=spec["supersede_reason"],
            )
            result["source_quotes_retired"].append(retired)
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "source_quotation": spec["source_quotation"],
                    "revision_quotation": spec["revision_quotation"],
                    "stage": "pipeline_alignment",
                    "error": str(exc),
                }
            )

    result["after"] = {
        "pending_quotations": frappe.db.sql(
            """
            select
                name,
                party_name,
                transaction_date,
                workflow_state,
                status,
                docstatus,
                grand_total
            from `tabQuotation`
            where workflow_state in ('Pending Sales Approval', 'Pending Executive Approval')
            order by transaction_date asc, name asc
            """,
            as_dict=True,
        ),
        "pending_sales_orders": frappe.db.sql(
            """
            select
                name,
                customer,
                transaction_date,
                workflow_state,
                status,
                docstatus,
                grand_total
            from `tabSales Order`
            where workflow_state in ('Pending Sales Approval', 'Pending Executive Approval')
            order by transaction_date asc, name asc
            """,
            as_dict=True,
        ),
        "quotation_snapshot": frappe.db.sql(
            """
            select
                name,
                party_name,
                transaction_date,
                valid_till,
                docstatus,
                status,
                workflow_state,
                taxes_and_charges,
                grand_total,
                base_total_taxes_and_charges
            from `tabQuotation`
            where name in (
                'SAL-QTN-2026-00012', 'SAL-QTN-2026-00013', 'SAL-QTN-2026-00015',
                'SAL-QTN-2026-00263', 'SAL-QTN-2026-00264', 'SAL-QTN-2026-00265'
            )
            order by name asc
            """,
            as_dict=True,
        ),
    }
    return result


def _find_existing_draft_sales_order_from_quotation(quotation_name: str) -> str | None:
    rows = frappe.db.sql(
        """
        select distinct so.name
        from `tabSales Order` so
        inner join `tabSales Order Item` soi on soi.parent = so.name
        where so.docstatus = 0
          and soi.prevdoc_docname = %(quotation)s
        order by so.creation asc
        """,
        {"quotation": quotation_name},
        as_dict=True,
    )
    return rows[0].name if rows else None


def _advance_sales_order_workflow_to_state(
    sales_order_name: str,
    workflow_actions: list[str] | tuple[str, ...],
    target_state: str,
) -> dict[str, Any]:
    from frappe.model.workflow import apply_workflow

    doc = frappe.get_doc("Sales Order", sales_order_name)
    if doc.workflow_state == target_state:
        return {
            "sales_order": doc.name,
            "change_type": "existing",
            "workflow_state": doc.workflow_state,
            "status": doc.status,
            "docstatus": int(doc.docstatus or 0),
        }

    for action in workflow_actions:
        doc.reload()
        if doc.workflow_state == target_state:
            break
        doc.flags.ignore_permissions = True
        doc = apply_workflow(doc, action)
        doc.flags.ignore_permissions = True

    doc.reload()
    if doc.workflow_state != target_state:
        frappe.throw(
            f"Sales Order {doc.name} ended in workflow state {doc.workflow_state}, expected {target_state}."
        )

    return {
        "sales_order": doc.name,
        "change_type": "updated",
        "workflow_state": doc.workflow_state,
        "status": doc.status,
        "docstatus": int(doc.docstatus or 0),
    }


def _retire_superseded_sales_order(
    sales_order_name: str,
    replacement_order_name: str,
    reason: str,
) -> dict[str, Any]:
    from frappe.model.workflow import apply_workflow

    doc = frappe.get_doc("Sales Order", sales_order_name)
    if doc.workflow_state == "Rejected":
        return {
            "sales_order": doc.name,
            "change_type": "existing",
            "workflow_state": doc.workflow_state,
            "status": doc.status,
            "docstatus": int(doc.docstatus or 0),
        }

    doc.add_comment(
        "Comment",
        text=(
            f"Superseded by revised quotation-linked order {replacement_order_name}. "
            f"{reason}"
        ),
    )
    if doc.workflow_state in {"Pending Sales Approval", "Pending Executive Approval"}:
        doc.flags.ignore_permissions = True
        doc = apply_workflow(doc, "Reject")
    else:
        frappe.db.set_value(
            "Sales Order",
            doc.name,
            "workflow_state",
            "Rejected",
            update_modified=False,
        )
    frappe.db.commit()
    doc.reload()
    return {
        "sales_order": doc.name,
        "change_type": "updated",
        "workflow_state": doc.workflow_state,
        "status": doc.status,
        "docstatus": int(doc.docstatus or 0),
    }


def apply_apr2026_aung_aung_order_chain_alignment() -> dict[str, Any]:
    from erpnext.selling.doctype.quotation.quotation import make_sales_order

    source_quote = "SAL-QTN-2026-00263"
    stale_order = "SAL-ORD-2026-00034"
    result: dict[str, Any] = {
        "replacement_order": None,
        "stale_order_retired": None,
        "after": {},
        "failed": [],
    }

    try:
        replacement_name = _find_existing_draft_sales_order_from_quotation(source_quote)
        if replacement_name:
            replacement = frappe.get_doc("Sales Order", replacement_name)
            replacement_change_type = "existing"
        else:
            replacement = make_sales_order(source_quote)
            replacement.transaction_date = "2026-04-16"
            replacement.delivery_date = "2026-04-18"
            replacement.po_no = "SOAPP-AAT-0416-R1"
            replacement.po_date = "2026-04-16"
            replacement.ignore_default_payment_terms_template = 1
            replacement.payment_terms_template = "30 Days - MMOB"
            replacement.remarks = (
                "Revised April Aung Aung Telecom order recreated from the approved commercial-tax quotation "
                "after formal policy alignment; now awaiting sales-manager approval before warehouse release."
            )
            replacement.flags.ignore_permissions = True
            replacement.insert(ignore_permissions=True)
            replacement.add_comment(
                "Comment",
                text=(
                    f"Created from approved quotation {source_quote} to replace stale pre-revision order "
                    f"{stale_order} with a fully traceable commercial-tax chain."
                ),
            )
            frappe.db.commit()
            replacement_change_type = "created"

        workflow_result = _advance_sales_order_workflow_to_state(
            sales_order_name=replacement.name,
            workflow_actions=("Submit Order",),
            target_state="Pending Sales Approval",
        )
        replacement.reload()
        result["replacement_order"] = {
            "change_type": replacement_change_type,
            "sales_order": replacement.name,
            "from_quotation": source_quote,
            "workflow_state": workflow_result["workflow_state"],
            "status": workflow_result["status"],
            "docstatus": workflow_result["docstatus"],
            "grand_total": float(replacement.grand_total or 0),
            "base_total_taxes_and_charges": float(replacement.base_total_taxes_and_charges or 0),
            "taxes_and_charges": replacement.taxes_and_charges,
            "po_no": replacement.po_no,
        }

        result["stale_order_retired"] = _retire_superseded_sales_order(
            sales_order_name=stale_order,
            replacement_order_name=replacement.name,
            reason="Legacy draft retired so the live approval queue follows the approved taxable quotation.",
        )
    except Exception as exc:
        frappe.db.rollback()
        result["failed"].append({"stage": "aung_aung_order_alignment", "error": str(exc)})
        return result

    result["after"] = {
        "aung_order_stack": frappe.db.sql(
            """
            select
                name,
                customer,
                transaction_date,
                delivery_date,
                workflow_state,
                status,
                docstatus,
                taxes_and_charges,
                grand_total,
                po_no
            from `tabSales Order`
            where customer = 'Aung Aung Telecom'
              and transaction_date between '2026-04-11' and '2026-04-30'
            order by transaction_date asc, name asc
            """,
            as_dict=True,
        ),
        "pending_sales_orders": frappe.db.sql(
            """
            select
                name,
                customer,
                transaction_date,
                workflow_state,
                status,
                docstatus,
                grand_total
            from `tabSales Order`
            where workflow_state in ('Pending Sales Approval', 'Pending Executive Approval')
            order by transaction_date asc, name asc
            """,
            as_dict=True,
        ),
    }
    return result


def audit_fy2526_financial_realism() -> dict[str, Any]:
    export = export_fy2526_financial_statements()
    if export.get("failed"):
        return {"status": "failed", "errors": export["failed"]}

    pnl_report = next((r for r in export["reports"] if r["report"] == "Profit and Loss Statement"), None)
    cash_flow_report = next((r for r in export["reports"] if r["report"] == "Cash Flow"), None)

    if not pnl_report:
        return {"status": "failed", "errors": ["missing_pnl_report"]}

    columns = pnl_report.get("columns") or []
    period_fields = [col["fieldname"] for col in columns if isinstance(col, dict) and col.get("fieldname", "").endswith(("_2025", "_2026"))]

    def _row_by_account(rows, account_names):
        targets = {name for name in account_names if name}
        for row in rows:
            account = str(row.get("account") or "").strip()
            label = str(row.get("label") or "").strip()
            account_name = str(row.get("account_name") or "").strip()
            if account in targets or label in targets or account_name in targets:
                return row
        return None

    pnl_rows = pnl_report.get("rows") or []
    sales_row = _row_by_account(pnl_rows, ["Sales - MMOB", "Sales"])
    cogs_row = _row_by_account(pnl_rows, ["Cost of Goods Sold - MMOB", "Cost of Goods Sold"])
    total_income_row = _row_by_account(pnl_rows, ["Total Income (Credit)", "Total Income"])
    total_expense_row = _row_by_account(pnl_rows, ["Total Expense (Debit)", "Total Expense"])
    net_profit_row = _row_by_account(pnl_rows, ["Profit for the year", "Net Profit / Loss", "Net Profit"])

    def _series_from_row(row):
        if not row:
            return {}
        return {field: float(row.get(field) or 0) for field in period_fields}

    sales_series = _series_from_row(sales_row)
    cogs_series = _series_from_row(cogs_row)
    total_income_series = _series_from_row(total_income_row)
    total_expense_series = _series_from_row(total_expense_row)
    net_profit_series = _series_from_row(net_profit_row)

    salary_expense_account = _find_account_by_names(
        [
            "Salaries and Wages - MMOB",
            "Salary - MMOB",
            "Payroll Expenses - MMOB",
            "Staff Salary - MMOB",
            "Salary Expense - MMOB",
        ]
    )
    opex_accounts = [
        _find_account_by_names(["Rent - MMOB", "Office Rent - MMOB", "Rent Expense - MMOB"]),
        _find_account_by_names(["Utilities - MMOB", "Electricity - MMOB", "Water Expense - MMOB"]),
        _find_account_by_names(
            ["Delivery Expenses - MMOB", "Freight and Forwarding - MMOB", "Logistics - MMOB"]
        ),
        _find_account_by_names(["Marketing Expenses - MMOB", "Sales Promotion - MMOB", "Advertising - MMOB"]),
        _find_account_by_names(["Office Expenses - MMOB", "Administrative Expenses - MMOB", "General Expenses - MMOB"]),
        _find_account_by_names(["Telephone Expense - MMOB", "Internet Expense - MMOB", "Communication Expenses - MMOB"]),
    ]
    expense_accounts = [acct for acct in [salary_expense_account, *opex_accounts] if acct]
    expense_series = {field: 0.0 for field in period_fields}
    for row in pnl_rows:
        account_name = str(row.get("account") or "").strip()
        if account_name not in expense_accounts:
            continue
        for field in period_fields:
            expense_series[field] += float(row.get(field) or 0)

    def _delta_series(series: dict[str, float]) -> dict[str, float]:
        deltas: dict[str, float] = {}
        running = 0.0
        for field in period_fields:
            current = float(series.get(field, 0))
            deltas[field] = current - running
            running = current
        return deltas

    sales_monthly = _delta_series(sales_series)
    cogs_monthly = _delta_series(cogs_series)
    expense_monthly = _delta_series(expense_series)

    payroll_rows = frappe.db.sql(
        """
        select date_format(posting_date, '%%Y-%%m') as month_key,
               sum(net_pay) as net_pay
        from `tabSalary Slip`
        where docstatus=1
          and posting_date between %s and %s
        group by month_key
        order by month_key
        """,
        ("2025-04-01", "2026-03-31"),
        as_dict=True,
    )
    payroll_series = {row["month_key"]: float(row["net_pay"] or 0) for row in payroll_rows}

    def _month_key_from_field(fieldname):
        month_map = {
            "jan": "01",
            "feb": "02",
            "mar": "03",
            "apr": "04",
            "may": "05",
            "jun": "06",
            "jul": "07",
            "aug": "08",
            "sep": "09",
            "oct": "10",
            "nov": "11",
            "dec": "12",
        }
        parts = fieldname.split("_")
        if len(parts) != 2:
            return None
        month = month_map.get(parts[0])
        year = parts[1]
        if not month or not year:
            return None
        return f"{year}-{month}"

    monthly_summary = []
    for field in period_fields:
        month_key = _month_key_from_field(field)
        monthly_summary.append(
            {
                "month": month_key or field,
                "sales": sales_series.get(field, 0),
                "sales_monthly": sales_monthly.get(field, 0),
                "cogs": cogs_series.get(field, 0),
                "cogs_monthly": cogs_monthly.get(field, 0),
                "total_income": total_income_series.get(field, 0),
                "total_expense": total_expense_series.get(field, 0),
                "net_profit": net_profit_series.get(field, 0),
                "expense_from_accounts": expense_series.get(field, 0),
                "expense_monthly": expense_monthly.get(field, 0),
                "payroll_net": payroll_series.get(month_key, 0),
            }
        )

    cash_flow_summary = {}
    if cash_flow_report:
        cash_rows = cash_flow_report.get("rows") or []
        net_cash_row = next((row for row in cash_rows if str(row.get("section_name") or "") == "'Net Change in Cash'"), None)
        cash_flow_summary = _series_from_row(net_cash_row)

    return {
        "status": "ok",
        "period_fields": period_fields,
        "monthly_summary": monthly_summary,
        "cash_flow_net_change": cash_flow_summary,
        "totals": {
            "sales": sum(sales_series.values()),
            "sales_monthly": sum(sales_monthly.values()),
            "cogs": sum(cogs_series.values()),
            "cogs_monthly": sum(cogs_monthly.values()),
            "total_income": sum(total_income_series.values()),
            "total_expense": sum(total_expense_series.values()),
            "net_profit": sum(net_profit_series.values()),
            "expense_from_accounts": sum(expense_series.values()),
            "expense_monthly": sum(expense_monthly.values()),
            "payroll_net": sum(payroll_series.values()),
        },
    }


def audit_fy2526_cash_flow_variance() -> dict[str, Any]:
    export = export_fy2526_financial_statements()
    if export.get("failed"):
        return {"status": "failed", "errors": export["failed"]}

    cash_flow_report = next((r for r in export["reports"] if r["report"] == "Cash Flow"), None)
    if not cash_flow_report:
        return {"status": "failed", "errors": ["missing_cash_flow_report"]}

    columns = cash_flow_report.get("columns") or []
    period_fields = [col["fieldname"] for col in columns if isinstance(col, dict) and col.get("fieldname", "").endswith(("_2025", "_2026"))]

    def _row_by_section(rows, section_name):
        for row in rows:
            candidates = {
                str(row.get("section_name") or "").strip(),
                str(row.get("section") or "").strip(),
                str(row.get("account") or "").strip(),
                str(row.get("account_name") or "").strip(),
            }
            if section_name in candidates:
                return row
        return None

    cash_rows = cash_flow_report.get("rows") or []
    operations_profit_row = _row_by_section(cash_rows, "'Profit for the year'")
    depreciation_row = _row_by_section(cash_rows, "Depreciation")
    ar_row = _row_by_section(cash_rows, "Net Change in Accounts Receivable")
    ap_row = (
        _row_by_section(cash_rows, "Net Change in Trade Payables")
        or _row_by_section(cash_rows, "Net Change in Accounts Payable")
    )
    payroll_accrual_row = _row_by_section(cash_rows, "Net Change in Payroll and Accrued Expenses")
    taxes_row = _row_by_section(cash_rows, "Net Change in Taxes Payable")
    grni_row = _row_by_section(cash_rows, "Net Change in GRNI / Stock Received But Not Billed")
    inventory_row = _row_by_section(cash_rows, "Net Change in Inventory")
    operations_row = _row_by_section(cash_rows, "'Net Cash from Operations'")
    fixed_asset_row = _row_by_section(cash_rows, "Net Change in Fixed Asset")
    investing_row = _row_by_section(cash_rows, "'Net Cash from Investing'")
    equity_row = _row_by_section(cash_rows, "Net Change in Equity")
    borrowings_row = _row_by_section(cash_rows, "Net Change in Borrowings")
    financing_row = _row_by_section(cash_rows, "'Net Cash from Financing'")
    net_cash_row = _row_by_section(cash_rows, "'Net Change in Cash'")
    opening_row = _row_by_section(cash_rows, "Opening")
    closing_row = _row_by_section(cash_rows, "Closing (Opening + Total)")

    def _series(row):
        if not row:
            return {}
        return {field: float(row.get(field) or 0) for field in period_fields}

    borrowing_accounts = [
        "Bank Overdraft Account - MMOB",
        "Unsecured Loans - MMOB",
        "Bank Loan - KBZ - MMOB",
    ]
    borrowing_rows = frappe.db.sql(
        """
        select a.name as account,
               round(sum(gl.debit_in_account_currency - gl.credit_in_account_currency), 2) as balance
        from `tabGL Entry` gl
        inner join `tabAccount` a on a.name = gl.account
        where gl.company = %s
          and gl.posting_date <= %s
          and a.name in (%s, %s, %s)
        group by a.name
        """,
        ("Mingalar Mobile Distribution Co., Ltd.", "2026-03-31", *borrowing_accounts),
        as_dict=True,
    )
    borrowing_balance = round(
        sum(abs(float(row.get("balance") or 0)) for row in borrowing_rows),
        2,
    )

    return {
        "status": "ok",
        "period_fields": period_fields,
        "operations_profit": _series(operations_profit_row),
        "depreciation": _series(depreciation_row),
        "accounts_receivable": _series(ar_row),
        "accounts_payable": _series(ap_row),
        "payroll_and_accrued_expenses": _series(payroll_accrual_row),
        "taxes_payable": _series(taxes_row),
        "grni": _series(grni_row),
        "inventory": _series(inventory_row),
        "operations": _series(operations_row),
        "fixed_asset": _series(fixed_asset_row),
        "investing": _series(investing_row),
        "equity": _series(equity_row),
        "borrowings": _series(borrowings_row),
        "financing": _series(financing_row),
        "net_change_in_cash": _series(net_cash_row),
        "opening_cash": _series(opening_row),
        "closing_cash": _series(closing_row),
        "borrowing_balance_to_fy_end": borrowing_balance,
        "borrowing_accounts": borrowing_rows,
    }


def audit_fy2526_ar_ap_aging_buckets() -> dict[str, Any]:
    report_date = "2026-03-31"

    def _bucket_sql():
        return (
            "case"
            " when datediff(%(report_date)s, posting_date) between 0 and 30 then '0-30'"
            " when datediff(%(report_date)s, posting_date) between 31 and 60 then '31-60'"
            " when datediff(%(report_date)s, posting_date) between 61 and 90 then '61-90'"
            " when datediff(%(report_date)s, posting_date) between 91 and 120 then '91-120'"
            " else '121+' end"
        )

    ar_rows = frappe.db.sql(
        f"""
        select {_bucket_sql()} as bucket, sum(outstanding_amount) as total
        from `tabSales Invoice`
        where docstatus=1 and outstanding_amount > 0
        group by bucket
        order by field(bucket, '0-30','31-60','61-90','91-120','121+')
        """,
        {"report_date": report_date},
        as_dict=True,
    )
    ap_rows = frappe.db.sql(
        f"""
        select {_bucket_sql()} as bucket, sum(outstanding_amount) as total
        from `tabPurchase Invoice`
        where docstatus=1 and outstanding_amount > 0
        group by bucket
        order by field(bucket, '0-30','31-60','61-90','91-120','121+')
        """,
        {"report_date": report_date},
        as_dict=True,
    )

    return {"as_of": report_date, "ar": ar_rows, "ap": ap_rows}


def audit_fy2526_inventory_valuation() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    warehouses = frappe.get_all("Warehouse", filters={"company": company}, pluck="name")
    if not warehouses:
        return {"status": "failed", "error": "no_company_warehouses"}

    placeholders = ", ".join(["%s"] * len(warehouses))
    rows = frappe.db.sql(
        f"""
        select item_code, warehouse, actual_qty, stock_value, valuation_rate
        from `tabBin`
        where warehouse in ({placeholders})
        order by stock_value desc
        limit 10
        """,
        tuple(warehouses),
        as_dict=True,
    )
    negative = [row for row in rows if (row.get("stock_value") or 0) < 0]
    return {"status": "ok", "top_bins": rows, "negative_bins": negative}


def audit_fy2526_expense_account_mix() -> dict[str, Any]:
    rows = frappe.db.sql(
        """
        select a.name as account,
               ifnull(a.account_type, '') as account_type,
               round(sum(gl.debit_in_account_currency - gl.credit_in_account_currency), 2) as amount
        from `tabGL Entry` gl
        inner join `tabAccount` a on a.name = gl.account
        where gl.company = %s
          and gl.posting_date between %s and %s
          and ifnull(gl.is_cancelled, 0) = 0
          and gl.voucher_type != 'Period Closing Voucher'
          and a.root_type = 'Expense'
          and a.is_group = 0
        group by a.name
        having abs(amount) > 0.005
        order by amount desc, a.name asc
        """,
        ("Mingalar Mobile Distribution Co., Ltd.", "2025-04-01", "2026-03-31"),
        as_dict=True,
    )
    operating_rows = [
        row for row in rows if str(row.get("account_type") or "") != "Expenses Included In Valuation"
    ]
    valuation_rows = [
        row for row in rows if str(row.get("account_type") or "") == "Expenses Included In Valuation"
    ]
    return {
        "status": "ok",
        "accounts": operating_rows,
        "valuation_offsets": valuation_rows,
    }


def audit_fy2526_bank_cash_positions() -> dict[str, Any]:
    rows = frappe.db.sql(
        """
        select a.name as account,
               a.account_type,
               round(sum(gl.debit_in_account_currency - gl.credit_in_account_currency), 2) as balance
        from `tabGL Entry` gl
        inner join `tabAccount` a on a.name = gl.account
        where gl.company = %s
          and gl.posting_date <= %s
          and ifnull(gl.is_cancelled, 0) = 0
          and a.account_type in ('Bank', 'Cash')
          and a.is_group = 0
        group by a.name, a.account_type
        having abs(balance) > 0.005
        order by balance asc, a.name asc
        """,
        ("Mingalar Mobile Distribution Co., Ltd.", "2026-03-31"),
        as_dict=True,
    )
    return {"status": "ok", "accounts": rows}


def audit_fy2526_integrated_realism_checkpoint() -> dict[str, Any]:
    financial_yearly = summarize_fy2526_financial_statements_yearly()
    financial_monthly = audit_fy2526_financial_realism_summary()
    commercial = audit_fy2526_commercial_realism_distribution()
    document_chain = audit_fy2526_document_chain_realism()
    payroll = audit_fy2526_payroll_accounting_posture()
    aging = audit_fy2526_ar_ap_aging_buckets()
    inventory = audit_fy2526_inventory_valuation()
    product = audit_product_master_pricing_and_warehouse_realism()
    expense_mix = audit_fy2526_expense_account_mix()
    bank_positions = audit_fy2526_bank_cash_positions()
    treasury = audit_fy2526_month_end_treasury_posture()

    def _bucket_total(rows: list[dict[str, Any]]) -> float:
        return round(sum(float(row.get("total") or 0) for row in rows), 2)

    def _bucket_value(rows: list[dict[str, Any]], bucket: str) -> float:
        for row in rows:
            if str(row.get("bucket") or "") == bucket:
                return float(row.get("total") or 0)
        return 0.0

    ar_total = _bucket_total(aging.get("ar") or [])
    ap_total = _bucket_total(aging.get("ap") or [])
    ar_121 = _bucket_value(aging.get("ar") or [], "121+")
    ap_121 = _bucket_value(aging.get("ap") or [], "121+")

    commercial_totals = commercial.get("totals") or {}
    concentration = commercial.get("concentration") or {}
    payroll_totals = payroll.get("totals") or {}
    product_warehouse_totals = product.get("warehouse_totals") or []
    treasury_months = treasury.get("monthly") or []

    negative_cash_months = [
        row["month_key"] for row in treasury_months if float(row.get("Cash - MMOB") or 0) < 0
    ]
    low_cash_months = [
        row["month_key"] for row in treasury_months if 0 <= float(row.get("Cash - MMOB") or 0) < 1000000
    ]
    negative_bank_months = [
        {
            "month_key": row["month_key"],
            "account": account,
            "balance": float(row.get(account) or 0),
        }
        for row in treasury_months
        for account in (
            "KBZ-001-000123 - KBZ Bank - Current - MMOB",
            "AYA-001-000456 - AYA Bank - Current - MMOB",
            "CB-001-000789 - CB Bank - Current - MMOB",
        )
        if float(row.get(account) or 0) < 0
    ]

    findings: list[dict[str, Any]] = []
    if abs(float((financial_yearly.get("balance_sheet") or {}).get("balance_gap") or 0)) > 0.5:
        findings.append({"severity": "high", "issue": "balance_sheet_gap_non_zero"})
    if int(product.get("missing_mmob_buying_count") or 0) > 0 or int(product.get("missing_mmob_selling_count") or 0) > 0:
        findings.append({"severity": "high", "issue": "item_price_coverage_incomplete"})
    if int(product.get("suspicious_price_count") or 0) > 0:
        findings.append({"severity": "high", "issue": "suspicious_item_prices_remaining"})
    if product.get("valuation_anomalies"):
        findings.append({"severity": "high", "issue": "inventory_valuation_anomalies_remaining"})
    if len(document_chain.get("sales", {}).get("invoice_chain_outliers") or []) > 0:
        findings.append({"severity": "medium", "issue": "sales_invoice_chain_outliers_remaining"})
    if len(document_chain.get("purchase", {}).get("purchase_invoice_chain_outliers") or []) > 0:
        findings.append({"severity": "medium", "issue": "purchase_invoice_chain_outliers_remaining"})
    if negative_cash_months:
        findings.append(
            {"severity": "medium", "issue": "negative_cash_months_remaining", "months": negative_cash_months}
        )
    if negative_bank_months:
        findings.append(
            {
                "severity": "medium",
                "issue": "negative_operating_bank_months_remaining",
                "months": negative_bank_months,
            }
        )
    gross_variance = float(payroll_totals.get("salary_variance_vs_gross") or 0)
    if abs(gross_variance) > 1000:
        findings.append({"severity": "medium", "issue": "salary_gl_not_aligned_to_salary_gross"})
    if ar_total and (ar_121 / ar_total) > 0.40:
        findings.append({"severity": "medium", "issue": "ar_121_plus_still_high", "ratio": round(ar_121 / ar_total, 4)})
    if ap_total and (ap_121 / ap_total) > 0.40:
        findings.append({"severity": "medium", "issue": "ap_121_plus_still_high", "ratio": round(ap_121 / ap_total, 4)})
    if float(concentration.get("top_3_customer_share") or 0) > 50:
        findings.append(
            {
                "severity": "low",
                "issue": "top_3_customer_concentration_high",
                "share": float(concentration.get("top_3_customer_share") or 0),
            }
        )

    status = "ok" if not [f for f in findings if f["severity"] in {"high", "medium"}] else "needs_review"

    return {
        "status": status,
        "findings": findings,
        "headline": {
            "sales": float((financial_yearly.get("profit_and_loss") or {}).get("sales") or 0),
            "cogs": float((financial_yearly.get("profit_and_loss") or {}).get("cogs") or 0),
            "net_profit": float((financial_yearly.get("profit_and_loss") or {}).get("net_profit") or 0),
            "debtors": float((financial_yearly.get("balance_sheet") or {}).get("debtors") or 0),
            "creditors": float((financial_yearly.get("balance_sheet") or {}).get("creditors") or 0),
            "stock_in_hand": float((financial_yearly.get("balance_sheet") or {}).get("stock_in_hand") or 0),
            "bank_and_cash": float((financial_yearly.get("balance_sheet") or {}).get("bank_and_cash") or 0),
            "bank_overdraft": float((financial_yearly.get("balance_sheet") or {}).get("bank_overdraft") or 0),
            "bank_loan": float((financial_yearly.get("balance_sheet") or {}).get("bank_loan") or 0),
        },
        "commercial": {
            "totals": commercial_totals,
            "concentration": {
                "top_3_customer_share": float(concentration.get("top_3_customer_share") or 0),
                "top_10_customer_share": float(concentration.get("top_10_customer_share") or 0),
                "top_3_item_share": float(concentration.get("top_3_item_share") or 0),
                "top_10_item_share": float(concentration.get("top_10_item_share") or 0),
            },
        },
        "document_chain": {
            "sales": {
                "submitted_quotations": int(document_chain.get("sales", {}).get("submitted_quotations") or 0),
                "submitted_sales_orders": int(document_chain.get("sales", {}).get("submitted_sales_orders") or 0),
                "submitted_delivery_notes": int(document_chain.get("sales", {}).get("submitted_delivery_notes") or 0),
                "submitted_sales_invoices": int(document_chain.get("sales", {}).get("submitted_sales_invoices") or 0),
                "invoice_chain_outlier_count": len(document_chain.get("sales", {}).get("invoice_chain_outliers") or []),
                "classified_direct_billing_exception_count": len(
                    document_chain.get("sales", {}).get("classified_direct_billing_exceptions") or []
                ),
            },
            "purchase": {
                "submitted_purchase_orders": int(document_chain.get("purchase", {}).get("submitted_purchase_orders") or 0),
                "submitted_purchase_receipts": int(document_chain.get("purchase", {}).get("submitted_purchase_receipts") or 0),
                "submitted_purchase_invoices": int(document_chain.get("purchase", {}).get("submitted_purchase_invoices") or 0),
                "purchase_invoice_chain_outlier_count": len(
                    document_chain.get("purchase", {}).get("purchase_invoice_chain_outliers") or []
                ),
            },
        },
        "aging": {
            "ar_total": ar_total,
            "ar_121_plus": ar_121,
            "ar_121_plus_ratio": round((ar_121 / ar_total), 4) if ar_total else 0,
            "ap_total": ap_total,
            "ap_121_plus": ap_121,
            "ap_121_plus_ratio": round((ap_121 / ap_total), 4) if ap_total else 0,
        },
        "inventory": {
            "negative_bin_count": len(inventory.get("negative_bins") or []),
            "warehouse_totals": product_warehouse_totals[:5],
        },
        "payroll": {
            "gross_pay": float(payroll_totals.get("gross_pay") or 0),
            "salary_slip_total": float(payroll_totals.get("slip_net") or 0),
            "salary_gl_total": float(payroll_totals.get("salary_gl_net") or 0),
            "salary_variance_vs_gross": gross_variance,
            "salary_variance_vs_slips": float(payroll_totals.get("salary_variance_vs_slips") or 0),
            "payroll_payable_balance_to_fy_end": float(payroll_totals.get("payroll_payable_balance_to_fy_end") or 0),
        },
        "treasury": {
            "negative_cash_months": negative_cash_months,
            "low_cash_months": low_cash_months,
            "negative_bank_months": negative_bank_months,
            "year_end_positions": bank_positions.get("accounts") or [],
        },
        "expense_mix": {
            "top_accounts": (expense_mix.get("accounts") or [])[:12],
        },
    }


def audit_fy2526_month_end_treasury_posture() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    bank_accounts = [
        "KBZ-001-000123 - KBZ Bank - Current - MMOB",
        "AYA-001-000456 - AYA Bank - Current - MMOB",
        "CB-001-000789 - CB Bank - Current - MMOB",
        "KBZPAY-000123 - KBZ Pay Clearing - MMOB",
        "WAVEPAY-000456 - Wave Money Clearing - MMOB",
        "Cash - MMOB",
        "Bank Overdraft Account - MMOB",
        "Unsecured Loans - MMOB",
        "Bank Loan - KBZ - MMOB",
    ]

    month_series = _month_series("2025-04-01", "2026-03-31")
    monthly: list[dict[str, Any]] = []
    for month in month_series:
        row: dict[str, Any] = {"month_key": month["month_key"], "posting_date": month["posting_date"]}
        for account in bank_accounts:
            balance_rows = frappe.db.sql(
                """
                select round(sum(debit_in_account_currency - credit_in_account_currency), 2) as balance
                from `tabGL Entry`
                where company = %s
                  and account = %s
                  and posting_date <= %s
                """,
                (company, account, month["posting_date"]),
                as_dict=True,
            )
            balance = float((balance_rows[0]["balance"] or 0) if balance_rows else 0)
            row[account] = balance
        monthly.append(row)

    return {"status": "ok", "monthly": monthly}


def apply_fy2526_incremental_opex_realism_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    cost_center = _company_cost_center(company)
    cash_account = "Cash - MMOB"
    kbz_account = "KBZ-001-000123 - KBZ Bank - Current - MMOB"
    expense_accounts = {
        "utilities": _find_account_by_names(["Utilities - MMOB", "Electricity - MMOB", "Water Expense - MMOB"]),
        "logistics": _find_account_by_names(
            ["Delivery Expenses - MMOB", "Freight and Forwarding Charges - MMOB", "Logistics - MMOB"]
        ),
        "telecom": _find_account_by_names(["Telephone Expense - MMOB", "Telephone Expenses - MMOB", "Internet Expense - MMOB", "Communication Expenses - MMOB"]),
        "maintenance": _find_account_by_names(["Office Maintenance Expenses - MMOB"]),
        "bank_charges": _find_account_by_names(["Bank Charges - MMOB"]),
        "travel": _find_account_by_names(["Travel Expenses - MMOB"]),
    }

    month_specs = [
        {
            "month_key": "2025-06",
            "posting_date": "2025-06-29",
            "credit_account": cash_account,
            "remarks": "Monsoon quarter operating expense supplement for freight, telecom, utility backup, and branch support.",
            "lines": {
                "utilities": 850000,
                "logistics": 1400000,
                "telecom": 250000,
                "maintenance": 150000,
            },
        },
        {
            "month_key": "2025-09",
            "posting_date": "2025-09-29",
            "credit_account": kbz_account,
            "remarks": "Pre-festival operating support for delivery runs, utilities, telecom, and small branch maintenance.",
            "lines": {
                "utilities": 950000,
                "logistics": 1800000,
                "telecom": 300000,
                "maintenance": 250000,
                "travel": 200000,
            },
        },
        {
            "month_key": "2025-12",
            "posting_date": "2025-12-29",
            "credit_account": kbz_account,
            "remarks": "Year-end operating supplement for delivery pressure, telecom, bank handling, and showroom utilities.",
            "lines": {
                "utilities": 1150000,
                "logistics": 2200000,
                "telecom": 350000,
                "bank_charges": 120000,
                "travel": 150000,
            },
        },
        {
            "month_key": "2026-03",
            "posting_date": "2026-03-28",
            "credit_account": cash_account,
            "remarks": "Year-end operating supplement for closing-month freight, telecom, maintenance, and utility usage.",
            "lines": {
                "utilities": 1250000,
                "logistics": 2500000,
                "telecom": 400000,
                "maintenance": 300000,
                "bank_charges": 80000,
            },
        },
    ]

    result: dict[str, Any] = {"journal_entries": [], "failed": []}

    for spec in month_specs:
        user_remark = f"AI-FY2526-OPEX-INCREMENTAL-{spec['month_key']} | {spec['remarks']}"
        accounts: list[dict[str, Any]] = []
        for key, amount in spec["lines"].items():
            account = expense_accounts.get(key)
            if not account or not amount:
                continue
            accounts.append(
                {
                    "account": account,
                    "debit_in_account_currency": int(amount),
                    "cost_center": cost_center,
                }
            )

        if not accounts:
            continue

        total_amount = int(sum(line["debit_in_account_currency"] for line in accounts))
        accounts.append(
            {
                "account": spec["credit_account"],
                "credit_in_account_currency": total_amount,
                "cost_center": cost_center,
            }
        )

        try:
            journal_entry_name = _create_simple_journal_entry(
                {
                    "company": company,
                    "posting_date": spec["posting_date"],
                    "voucher_type": "Journal Entry",
                    "user_remark": user_remark,
                    "accounts": accounts,
                }
            )
            frappe.db.commit()
            result["journal_entries"].append(
                {
                    "month_key": spec["month_key"],
                    "journal_entry": journal_entry_name,
                    "amount": total_amount,
                    "credit_account": spec["credit_account"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"month_key": spec["month_key"], "error": str(exc)})

    return result


def apply_fy2526_treasury_posture_refinement_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    result: dict[str, Any] = {"journal_entries": [], "failed": []}

    transfer_specs = [
        {
            "label": "august_cash_withdrawal_support",
            "posting_date": "2025-08-31",
            "amount": 1500000,
            "debit_account": "Cash - MMOB",
            "credit_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
            "user_remark": (
                "AI-FY2526-TREASURY-REFINE-2025-08-31-CASH | "
                "Withdraw cash from KBZ at month-end to avoid negative petty cash during August branch operations."
            ),
        },
        {
            "label": "march_year_end_kbz_redeposit",
            "posting_date": "2026-03-31",
            "amount": 20000000,
            "debit_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
            "credit_account": "Cash - MMOB",
            "user_remark": (
                "AI-FY2526-TREASURY-REFINE-2026-03-31-KBZ | "
                "Year-end redeposit of accumulated cash collections into KBZ to keep closing treasury posture balanced."
            ),
        },
        {
            "label": "march_year_end_cb_redeposit",
            "posting_date": "2026-03-31",
            "amount": 10000000,
            "debit_account": "CB-001-000789 - CB Bank - Current - MMOB",
            "credit_account": "Cash - MMOB",
            "user_remark": (
                "AI-FY2526-TREASURY-REFINE-2026-03-31-CB | "
                "Year-end redeposit of part of showroom cash into CB bank to reduce excessive hand-cash concentration."
            ),
        },
    ]

    for spec in transfer_specs:
        try:
            journal_entry_name = _create_simple_journal_entry(
                {
                    "company": company,
                    "posting_date": spec["posting_date"],
                    "voucher_type": "Journal Entry",
                    "user_remark": spec["user_remark"],
                    "accounts": [
                        {
                            "account": spec["debit_account"],
                            "debit_in_account_currency": spec["amount"],
                        },
                        {
                            "account": spec["credit_account"],
                            "credit_in_account_currency": spec["amount"],
                        },
                    ],
                }
            )
            frappe.db.commit()
            result["journal_entries"].append(
                {
                    "label": spec["label"],
                    "journal_entry": journal_entry_name,
                    "amount": spec["amount"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "error": str(exc)})

    return result


def apply_fy2526_post_aging_treasury_support_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    result: dict[str, Any] = {
        "before": summarize_fy2526_financial_statements_enterprise_view(),
        "journal_entries": [],
        "failed": [],
    }

    support_specs = [
        {
            "label": "march_kbz_working_capital_support",
            "posting_date": "2026-03-31",
            "amount": 50000000,
            "debit_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
            "credit_account": "Unsecured Loans - MMOB",
            "user_remark": (
                "AI-FY2526-TREASURY-WC-2026-03-31-KBZ | "
                "Owner working-capital support after year-end debtor collection push and supplier-aging normalization, keeping operating liquidity disciplined but practical."
            ),
        },
    ]

    for spec in support_specs:
        try:
            journal_entry_name = _create_simple_journal_entry(
                {
                    "company": company,
                    "posting_date": spec["posting_date"],
                    "voucher_type": "Journal Entry",
                    "user_remark": spec["user_remark"],
                    "accounts": [
                        {
                            "account": spec["debit_account"],
                            "debit_in_account_currency": spec["amount"],
                        },
                        {
                            "account": spec["credit_account"],
                            "credit_in_account_currency": spec["amount"],
                        },
                    ],
                }
            )
            frappe.db.commit()
            result["journal_entries"].append(
                {
                    "label": spec["label"],
                    "journal_entry": journal_entry_name,
                    "amount": spec["amount"],
                    "debit_account": spec["debit_account"],
                    "credit_account": spec["credit_account"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "error": str(exc)})

    result["after"] = summarize_fy2526_financial_statements_enterprise_view()
    return result


def apply_fy2526_finance_statement_hygiene_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    cost_center = _company_cost_center(company)
    result: dict[str, Any] = {"journal_entries": [], "failed": []}

    try:
        bank_regularization = _create_simple_journal_entry(
            {
                "voucher_type": "Journal Entry",
                "company": company,
                "posting_date": "2026-03-31",
                "user_remark": (
                    "AI-FY2526-FIN-HYGIENE-CB-BALANCE-2026-03-31 | "
                    "Year-end cash deposit to normalize temporary negative CB current balance."
                ),
                "accounts": [
                    {
                        "account": "CB-001-000789 - CB Bank - Current - MMOB",
                        "debit_in_account_currency": 5000000,
                        "cost_center": cost_center,
                    },
                    {
                        "account": "Cash - MMOB",
                        "credit_in_account_currency": 5000000,
                        "cost_center": cost_center,
                    },
                ],
            }
        )
        frappe.db.commit()
        result["journal_entries"].append(
            {
                "journal_entry": bank_regularization,
                "type": "bank_balance_normalization",
                "amount": 5000000,
            }
        )
    except Exception as exc:
        frappe.db.rollback()
        result["failed"].append({"stage": "bank_balance_normalization", "error": str(exc)})

    try:
        expense_reclass = _create_simple_journal_entry(
            {
                "voucher_type": "Journal Entry",
                "company": company,
                "posting_date": "2026-03-31",
                "user_remark": (
                    "AI-FY2526-FIN-HYGIENE-OPEX-RECLASS-2026-03-31 | "
                    "Reclass broad administrative spending into utilities, telecom, maintenance, and sales support."
                ),
                "accounts": [
                    {
                        "account": "Utility Expenses - MMOB",
                        "debit_in_account_currency": 3600000,
                        "cost_center": cost_center,
                    },
                    {
                        "account": "Telephone Expenses - MMOB",
                        "debit_in_account_currency": 2400000,
                        "cost_center": cost_center,
                    },
                    {
                        "account": "Office Maintenance Expenses - MMOB",
                        "debit_in_account_currency": 1800000,
                        "cost_center": cost_center,
                    },
                    {
                        "account": "Sales Expenses - MMOB",
                        "debit_in_account_currency": 1200000,
                        "cost_center": cost_center,
                    },
                    {
                        "account": "Administrative Expenses - MMOB",
                        "credit_in_account_currency": 9000000,
                        "cost_center": cost_center,
                    },
                ],
            }
        )
        frappe.db.commit()
        result["journal_entries"].append(
            {
                "journal_entry": expense_reclass,
                "type": "opex_reclass",
                "amount": 9000000,
            }
        )
    except Exception as exc:
        frappe.db.rollback()
        result["failed"].append({"stage": "opex_reclass", "error": str(exc)})

    return result


def apply_fy2526_ar_ap_recent_bucket_rebalance() -> dict[str, Any]:
    result = {"ar": [], "ap": [], "failed": []}

    ar_candidates = frappe.get_all(
        "Sales Invoice",
        filters={
            "docstatus": 1,
            "outstanding_amount": [">", 0],
            "posting_date": [">=", "2026-02-01"],
        },
        fields=["name", "customer", "posting_date", "outstanding_amount"],
        order_by="posting_date asc",
        limit=10,
    )

    for row in ar_candidates[:6]:
        try:
            amount = int(round(float(row.outstanding_amount) * 0.3 / 1000.0) * 1000)
            if amount <= 0:
                continue
            payment_name = _apply_targeted_partial_payment(
                "Sales Invoice", row.name, "2026-03-25", amount
            )
            frappe.db.commit()
            result["ar"].append(
                {
                    "sales_invoice": row.name,
                    "customer": row.customer,
                    "payment_entry": payment_name,
                    "amount": amount,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": f"ar_recent_{row.name}", "error": str(exc)})

    ap_candidates = frappe.get_all(
        "Purchase Invoice",
        filters={
            "docstatus": 1,
            "outstanding_amount": [">", 0],
            "posting_date": [">=", "2026-02-01"],
        },
        fields=["name", "supplier", "posting_date", "outstanding_amount"],
        order_by="posting_date asc",
        limit=10,
    )

    for row in ap_candidates[:6]:
        try:
            amount = int(round(float(row.outstanding_amount) * 0.3 / 1000.0) * 1000)
            if amount <= 0:
                continue
            payment_name = _apply_targeted_partial_payment(
                "Purchase Invoice", row.name, "2026-03-25", amount
            )
            frappe.db.commit()
            result["ap"].append(
                {
                    "purchase_invoice": row.name,
                    "supplier": row.supplier,
                    "payment_entry": payment_name,
                    "amount": amount,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": f"ap_recent_{row.name}", "error": str(exc)})

    return result


def audit_fy2526_ar_ap_outlier_scan() -> dict[str, Any]:
    ar_rows = frappe.db.sql(
        """
        select name, customer, posting_date, outstanding_amount
        from `tabSales Invoice`
        where docstatus=1 and outstanding_amount > 0
        order by outstanding_amount desc
        limit 10
        """,
        as_dict=True,
    )
    ap_rows = frappe.db.sql(
        """
        select name, supplier, posting_date, outstanding_amount
        from `tabPurchase Invoice`
        where docstatus=1 and outstanding_amount > 0
        order by outstanding_amount desc
        limit 10
        """,
        as_dict=True,
    )

    return {"ar": ar_rows, "ap": ap_rows}


def audit_fy2526_ar_ap_legacy_buckets_detail() -> dict[str, Any]:
    report_date = "2026-03-31"
    ar_rows = frappe.db.sql(
        """
        select name, customer, posting_date, outstanding_amount,
               datediff(%s, posting_date) as age_days
        from `tabSales Invoice`
        where docstatus = 1
          and outstanding_amount > 0
          and posting_date <= %s
          and datediff(%s, posting_date) > 120
        order by posting_date asc, outstanding_amount desc
        limit 20
        """,
        (report_date, report_date, report_date),
        as_dict=True,
    )
    ap_rows = frappe.db.sql(
        """
        select name, supplier, posting_date, outstanding_amount,
               datediff(%s, posting_date) as age_days
        from `tabPurchase Invoice`
        where docstatus = 1
          and outstanding_amount > 0
          and posting_date <= %s
          and datediff(%s, posting_date) > 120
        order by posting_date asc, outstanding_amount desc
        limit 20
        """,
        (report_date, report_date, report_date),
        as_dict=True,
    )
    return {"as_of": report_date, "ar": ar_rows, "ap": ap_rows}


def apply_fy2526_ar_ap_legacy_normalization_wave() -> dict[str, Any]:
    legacy = audit_fy2526_ar_ap_legacy_buckets_detail()
    result = {"ar": [], "ap": [], "failed": []}

    for row in (legacy.get("ar") or [])[:6]:
        try:
            outstanding = float(row.outstanding_amount or 0)
            amount = int(round(min(outstanding * 0.35, 6000000) / 1000.0) * 1000)
            if amount <= 0:
                continue
            payment_name = _apply_targeted_partial_payment(
                "Sales Invoice",
                row.name,
                "2026-03-26",
                amount,
            )
            frappe.db.commit()
            result["ar"].append(
                {
                    "sales_invoice": row.name,
                    "customer": row.customer,
                    "payment_entry": payment_name,
                    "amount": amount,
                    "age_days": row.age_days,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": f"legacy_ar_{row.name}", "error": str(exc)})

    for row in (legacy.get("ap") or [])[:6]:
        try:
            outstanding = float(row.outstanding_amount or 0)
            amount = int(round(min(outstanding * 0.30, 7000000) / 1000.0) * 1000)
            if amount <= 0:
                continue
            payment_name = _apply_targeted_partial_payment(
                "Purchase Invoice",
                row.name,
                "2026-03-27",
                amount,
            )
            frappe.db.commit()
            result["ap"].append(
                {
                    "purchase_invoice": row.name,
                    "supplier": row.supplier,
                    "payment_entry": payment_name,
                    "amount": amount,
                    "age_days": row.age_days,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": f"legacy_ap_{row.name}", "error": str(exc)})

    return result


def audit_fy2526_ar_ap_stale_high_value_scan() -> dict[str, Any]:
    report_date = "2026-03-31"
    ar_rows = frappe.db.sql(
        """
        select name, customer, posting_date, outstanding_amount,
               datediff(%s, posting_date) as age_days
        from `tabSales Invoice`
        where docstatus = 1
          and outstanding_amount > 0
          and posting_date between '2025-04-01' and %s
          and datediff(%s, posting_date) > 120
        order by outstanding_amount desc, posting_date asc
        limit 12
        """,
        (report_date, report_date, report_date),
        as_dict=True,
    )
    ap_rows = frappe.db.sql(
        """
        select name, supplier, posting_date, outstanding_amount,
               datediff(%s, posting_date) as age_days
        from `tabPurchase Invoice`
        where docstatus = 1
          and outstanding_amount > 0
          and posting_date between '2025-04-01' and %s
          and datediff(%s, posting_date) > 120
        order by outstanding_amount desc, posting_date asc
        limit 12
        """,
        (report_date, report_date, report_date),
        as_dict=True,
    )
    return {"as_of": report_date, "ar": ar_rows, "ap": ap_rows}


def apply_fy2526_ar_ap_stale_high_value_normalization_wave() -> dict[str, Any]:
    scan = audit_fy2526_ar_ap_stale_high_value_scan()
    result = {"ar": [], "ap": [], "failed": []}

    for row in (scan.get("ar") or [])[:8]:
        try:
            outstanding = float(row.outstanding_amount or 0)
            amount = int(round(min(outstanding * 0.30, 2500000) / 1000.0) * 1000)
            if amount <= 0:
                continue
            payment_name = _apply_targeted_partial_payment(
                "Sales Invoice",
                row.name,
                "2026-03-29",
                amount,
            )
            frappe.db.commit()
            result["ar"].append(
                {
                    "sales_invoice": row.name,
                    "customer": row.customer,
                    "payment_entry": payment_name,
                    "amount": amount,
                    "age_days": row.age_days,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": f"stale_high_ar_{row.name}", "error": str(exc)})

    for row in (scan.get("ap") or [])[:8]:
        try:
            outstanding = float(row.outstanding_amount or 0)
            amount = int(round(min(outstanding * 0.25, 3500000) / 1000.0) * 1000)
            if amount <= 0:
                continue
            payment_name = _apply_targeted_partial_payment(
                "Purchase Invoice",
                row.name,
                "2026-03-30",
                amount,
            )
            frappe.db.commit()
            result["ap"].append(
                {
                    "purchase_invoice": row.name,
                    "supplier": row.supplier,
                    "payment_entry": payment_name,
                    "amount": amount,
                    "age_days": row.age_days,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": f"stale_high_ap_{row.name}", "error": str(exc)})

    return result


def apply_fy2526_ar_ap_outlier_fix() -> dict[str, Any]:
    outliers = audit_fy2526_ar_ap_outlier_scan()
    result = {"ar": [], "ap": [], "failed": []}

    for row in outliers.get("ar") or []:
        if float(row.outstanding_amount or 0) < 50000000:
            continue
        try:
            amount = int(round(float(row.outstanding_amount) * 0.25 / 1000.0) * 1000)
            payment_name = _apply_targeted_partial_payment(
                "Sales Invoice", row.name, "2026-03-28", amount
            )
            frappe.db.commit()
            result["ar"].append(
                {
                    "sales_invoice": row.name,
                    "customer": row.customer,
                    "payment_entry": payment_name,
                    "amount": amount,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": f"ar_outlier_{row.name}", "error": str(exc)})

    for row in outliers.get("ap") or []:
        if float(row.outstanding_amount or 0) < 70000000:
            continue
        try:
            amount = int(round(float(row.outstanding_amount) * 0.2 / 1000.0) * 1000)
            payment_name = _apply_targeted_partial_payment(
                "Purchase Invoice", row.name, "2026-03-28", amount
            )
            frappe.db.commit()
            result["ap"].append(
                {
                    "purchase_invoice": row.name,
                    "supplier": row.supplier,
                    "payment_entry": payment_name,
                    "amount": amount,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": f"ap_outlier_{row.name}", "error": str(exc)})

    return result


def apply_fy2526_inventory_turnover_realism() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    results: dict[str, Any] = {"reconciliations": [], "failed": []}

    warehouses = frappe.get_all("Warehouse", filters={"company": company}, pluck="name")
    if not warehouses:
        return {"reconciliations": [], "failed": [{"error": "no_company_warehouses"}]}

    placeholders = ", ".join(["%s"] * len(warehouses))
    fast_bins = frappe.db.sql(
        f"""
        select item_code, warehouse, actual_qty, valuation_rate
        from `tabBin`
        where warehouse in ({placeholders})
          and actual_qty > 0
        order by actual_qty desc
        limit 8
        """,
        tuple(warehouses),
        as_dict=True,
    )

    slow_bins = frappe.db.sql(
        f"""
        select item_code, warehouse, actual_qty, valuation_rate
        from `tabBin`
        where warehouse in ({placeholders})
          and actual_qty between 5 and 20
        order by actual_qty asc
        limit 6
        """,
        tuple(warehouses),
        as_dict=True,
    )

    for row in fast_bins:
        try:
            adjusted_qty = max(row.actual_qty * 0.9, row.actual_qty - 20)
            adjusted_qty = round(adjusted_qty, 2)
            reconciliation_name = _create_stock_reconciliation(
                company=company,
                item_code=row.item_code,
                warehouse=row.warehouse,
                posting_date="2026-03-31",
                qty=adjusted_qty,
                valuation_rate=row.valuation_rate or 0,
            )
            frappe.db.commit()
            results["reconciliations"].append(
                {
                    "type": "fast_mover_trim",
                    "stock_reconciliation": reconciliation_name,
                    "item_code": row.item_code,
                    "warehouse": row.warehouse,
                    "from_qty": row.actual_qty,
                    "to_qty": adjusted_qty,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            results["failed"].append(
                {
                    "item_code": row.item_code,
                    "warehouse": row.warehouse,
                    "error": str(exc),
                }
            )

    for row in slow_bins:
        try:
            adjusted_qty = round(row.actual_qty + 3, 2)
            reconciliation_name = _create_stock_reconciliation(
                company=company,
                item_code=row.item_code,
                warehouse=row.warehouse,
                posting_date="2026-03-31",
                qty=adjusted_qty,
                valuation_rate=row.valuation_rate or 0,
            )
            frappe.db.commit()
            results["reconciliations"].append(
                {
                    "type": "slow_mover_restock",
                    "stock_reconciliation": reconciliation_name,
                    "item_code": row.item_code,
                    "warehouse": row.warehouse,
                    "from_qty": row.actual_qty,
                    "to_qty": adjusted_qty,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            results["failed"].append(
                {
                    "item_code": row.item_code,
                    "warehouse": row.warehouse,
                    "error": str(exc),
                }
            )

    return results


def apply_fy2526_returns_and_credits_realism() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    results: dict[str, Any] = {"sales_returns": [], "purchase_returns": [], "failed": []}

    sales_return_targets = frappe.get_all(
        "Sales Invoice",
        filters={"docstatus": 1, "posting_date": [">=", "2025-07-01"], "is_return": 0},
        fields=["name", "customer", "posting_date"],
        order_by="posting_date asc",
        limit=6,
    )

    for row in sales_return_targets[:4]:
        try:
            return_doc = _make_return_doc("Sales Invoice", row.name)
            return_doc.posting_date = add_months(getdate(row.posting_date), 1).strftime("%Y-%m-%d")
            if hasattr(return_doc, "is_return"):
                return_doc.is_return = 1
            if hasattr(return_doc, "return_against"):
                return_doc.return_against = row.name
            return_doc.remarks = f"FY2526 return for {row.name} due to damaged packaging."
            return_doc.insert(ignore_permissions=True)
            return_doc.submit()
            frappe.db.commit()
            results["sales_returns"].append(
                {"sales_invoice": row.name, "credit_note": return_doc.name}
            )
        except Exception as exc:
            frappe.db.rollback()
            results["failed"].append({"label": f"sales_return_{row.name}", "error": str(exc)})

    purchase_return_targets = frappe.get_all(
        "Purchase Invoice",
        filters={"docstatus": 1, "posting_date": [">=", "2025-07-01"], "is_return": 0},
        fields=["name", "supplier", "posting_date"],
        order_by="posting_date asc",
        limit=6,
    )

    for row in purchase_return_targets[:3]:
        try:
            return_doc = _make_return_doc("Purchase Invoice", row.name)
            return_doc.posting_date = add_months(getdate(row.posting_date), 1).strftime("%Y-%m-%d")
            if hasattr(return_doc, "is_return"):
                return_doc.is_return = 1
            if hasattr(return_doc, "return_against"):
                return_doc.return_against = row.name
            return_doc.remarks = f"FY2526 return for {row.name} due to transit damage."
            return_doc.insert(ignore_permissions=True)
            return_doc.submit()
            frappe.db.commit()
            results["purchase_returns"].append(
                {"purchase_invoice": row.name, "debit_note": return_doc.name}
            )
        except Exception as exc:
            frappe.db.rollback()
            results["failed"].append({"label": f"purchase_return_{row.name}", "error": str(exc)})

    if len(results["purchase_returns"]) < 2:
        fallback_targets = frappe.get_all(
            "Purchase Invoice",
            filters={"docstatus": 1, "posting_date": [">=", "2025-07-01"], "is_return": 0},
            fields=["name", "supplier", "posting_date"],
            order_by="posting_date desc",
            limit=8,
        )
        for row in fallback_targets:
            if len(results["purchase_returns"]) >= 3:
                break
            try:
                return_doc = _make_return_doc("Purchase Invoice", row.name)
                return_doc.posting_date = add_months(getdate(row.posting_date), 1).strftime("%Y-%m-%d")
                if hasattr(return_doc, "is_return"):
                    return_doc.is_return = 1
                if hasattr(return_doc, "return_against"):
                    return_doc.return_against = row.name
                return_doc.remarks = f"FY2526 return for {row.name} due to transit damage."
                return_doc.insert(ignore_permissions=True)
                return_doc.submit()
                frappe.db.commit()
                results["purchase_returns"].append(
                    {"purchase_invoice": row.name, "debit_note": return_doc.name, "fallback": True}
                )
            except Exception as exc:
                frappe.db.rollback()
                results["failed"].append({"label": f"purchase_return_fallback_{row.name}", "error": str(exc)})

    return results


def audit_fy2526_document_chain_realism() -> dict[str, Any]:
    sales = {}
    purchase = {}

    sales["submitted_quotations"] = frappe.db.sql(
        """
        select count(*) as count
        from `tabQuotation`
        where docstatus = 1
          and transaction_date between %s and %s
        """,
        ("2025-04-01", "2026-03-31"),
        as_dict=True,
    )[0]["count"]
    sales["quotations_with_sales_order"] = frappe.db.sql(
        """
        select count(distinct qti.parent) as count
        from `tabSales Order Item` soi
        inner join `tabSales Order` so on so.name = soi.parent
        inner join `tabQuotation Item` qti on qti.name = soi.quotation_item
        where so.docstatus = 1
          and ifnull(soi.quotation_item, '') != ''
          and so.transaction_date between %s and %s
        """,
        ("2025-04-01", "2026-03-31"),
        as_dict=True,
    )[0]["count"]
    sales["submitted_sales_orders"] = frappe.db.sql(
        """
        select count(*) as count
        from `tabSales Order`
        where docstatus = 1
          and transaction_date between %s and %s
        """,
        ("2025-04-01", "2026-03-31"),
        as_dict=True,
    )[0]["count"]
    sales["sales_orders_with_delivery"] = frappe.db.sql(
        """
        select count(distinct so.name) as count
        from `tabSales Order` so
        inner join `tabDelivery Note Item` dni on dni.against_sales_order = so.name
        inner join `tabDelivery Note` dn on dn.name = dni.parent and dn.docstatus = 1
        where so.docstatus = 1
          and so.transaction_date between %s and %s
        """,
        ("2025-04-01", "2026-03-31"),
        as_dict=True,
    )[0]["count"]
    sales["submitted_delivery_notes"] = frappe.db.sql(
        """
        select count(*) as count
        from `tabDelivery Note`
        where docstatus = 1
          and posting_date between %s and %s
        """,
        ("2025-04-01", "2026-03-31"),
        as_dict=True,
    )[0]["count"]
    sales["delivery_notes_with_invoice"] = frappe.db.sql(
        """
        select count(distinct dn.name) as count
        from `tabDelivery Note` dn
        inner join `tabSales Invoice Item` sii on sii.delivery_note = dn.name
        inner join `tabSales Invoice` si on si.name = sii.parent and si.docstatus = 1
        where dn.docstatus = 1
          and dn.posting_date between %s and %s
        """,
        ("2025-04-01", "2026-03-31"),
        as_dict=True,
    )[0]["count"]
    sales["submitted_sales_invoices"] = frappe.db.sql(
        """
        select count(*) as count
        from `tabSales Invoice`
        where docstatus = 1
          and posting_date between %s and %s
        """,
        ("2025-04-01", "2026-03-31"),
        as_dict=True,
    )[0]["count"]
    sales["sales_invoices_with_sales_order"] = frappe.db.sql(
        """
        select count(distinct si.name) as count
        from `tabSales Invoice` si
        inner join `tabSales Invoice Item` sii on sii.parent = si.name
        where si.docstatus = 1
          and si.posting_date between %s and %s
          and ifnull(sii.sales_order, '') != ''
        """,
        ("2025-04-01", "2026-03-31"),
        as_dict=True,
    )[0]["count"]
    sales["sales_invoices_via_delivery"] = frappe.db.sql(
        """
        select count(distinct si.name) as count
        from `tabSales Invoice` si
        inner join `tabSales Invoice Item` sii on sii.parent = si.name
        where si.docstatus = 1
          and si.posting_date between %s and %s
          and ifnull(sii.delivery_note, '') != ''
        """,
        ("2025-04-01", "2026-03-31"),
        as_dict=True,
    )[0]["count"]
    sales["direct_stock_sales_invoices"] = frappe.db.sql(
        """
        select count(*) as count
        from `tabSales Invoice`
        where docstatus = 1
          and posting_date between %s and %s
          and update_stock = 1
        """,
        ("2025-04-01", "2026-03-31"),
        as_dict=True,
    )[0]["count"]
    sales["classified_direct_billing_exceptions"] = frappe.db.sql(
        """
        select si.name, si.customer, si.posting_date, si.grand_total, si.update_stock
        from `tabSales Invoice` si
        where si.docstatus = 1
          and si.is_return = 0
          and si.posting_date between %s and %s
          and ifnull(si.remarks, '') like %s
        order by abs(si.grand_total) desc
        limit 10
        """,
        ("2025-04-01", "2026-03-31", "%Historical direct-billing exception classified:%"),
        as_dict=True,
    )
    sales["invoice_chain_outliers"] = frappe.db.sql(
        """
        select si.name, si.customer, si.posting_date, si.grand_total, si.update_stock
        from `tabSales Invoice` si
        left join `tabSales Invoice Item` sii on sii.parent = si.name
        where si.docstatus = 1
          and si.is_return = 0
          and si.posting_date between %s and %s
          and ifnull(si.remarks, '') not like %s
        group by si.name
        having sum(case when ifnull(sii.delivery_note, '') != '' then 1 else 0 end) = 0
           and sum(case when ifnull(sii.sales_order, '') != '' then 1 else 0 end) = 0
           and max(ifnull(si.update_stock, 0)) = 0
        order by si.grand_total desc
        limit 10
        """,
        ("2025-04-01", "2026-03-31", "%Historical direct-billing exception classified:%"),
        as_dict=True,
    )
    sales["so_to_dn_gap_outliers"] = frappe.db.sql(
        """
        select so.name as sales_order, so.customer, so.transaction_date, min(dn.posting_date) as first_delivery_date,
               datediff(min(dn.posting_date), so.transaction_date) as gap_days
        from `tabSales Order` so
        inner join `tabDelivery Note Item` dni on dni.against_sales_order = so.name
        inner join `tabDelivery Note` dn on dn.name = dni.parent and dn.docstatus = 1
        where so.docstatus = 1
          and so.transaction_date between %s and %s
        group by so.name, so.customer, so.transaction_date
        having gap_days > 21
        order by gap_days desc
        limit 10
        """,
        ("2025-04-01", "2026-03-31"),
        as_dict=True,
    )
    sales["dn_to_si_gap_outliers"] = frappe.db.sql(
        """
        select dn.name as delivery_note, dn.customer, dn.posting_date as delivery_date, min(si.posting_date) as first_invoice_date,
               datediff(min(si.posting_date), dn.posting_date) as gap_days
        from `tabDelivery Note` dn
        inner join `tabSales Invoice Item` sii on sii.delivery_note = dn.name
        inner join `tabSales Invoice` si on si.name = sii.parent and si.docstatus = 1
        where dn.docstatus = 1
          and dn.posting_date between %s and %s
        group by dn.name, dn.customer, dn.posting_date
        having gap_days > 14
        order by gap_days desc
        limit 10
        """,
        ("2025-04-01", "2026-03-31"),
        as_dict=True,
    )

    purchase["submitted_purchase_orders"] = frappe.db.sql(
        """
        select count(*) as count
        from `tabPurchase Order`
        where docstatus = 1
          and transaction_date between %s and %s
        """,
        ("2025-04-01", "2026-03-31"),
        as_dict=True,
    )[0]["count"]
    purchase["purchase_orders_with_receipt"] = frappe.db.sql(
        """
        select count(distinct po.name) as count
        from `tabPurchase Order` po
        inner join `tabPurchase Receipt Item` pri on pri.purchase_order = po.name
        inner join `tabPurchase Receipt` pr on pr.name = pri.parent and pr.docstatus = 1
        where po.docstatus = 1
          and po.transaction_date between %s and %s
        """,
        ("2025-04-01", "2026-03-31"),
        as_dict=True,
    )[0]["count"]
    purchase["submitted_purchase_receipts"] = frappe.db.sql(
        """
        select count(*) as count
        from `tabPurchase Receipt`
        where docstatus = 1
          and posting_date between %s and %s
        """,
        ("2025-04-01", "2026-03-31"),
        as_dict=True,
    )[0]["count"]
    purchase["purchase_receipts_with_invoice"] = frappe.db.sql(
        """
        select count(distinct pr.name) as count
        from `tabPurchase Receipt` pr
        inner join `tabPurchase Invoice Item` pii on pii.purchase_receipt = pr.name
        inner join `tabPurchase Invoice` pi on pi.name = pii.parent and pi.docstatus = 1
        where pr.docstatus = 1
          and pr.posting_date between %s and %s
        """,
        ("2025-04-01", "2026-03-31"),
        as_dict=True,
    )[0]["count"]
    purchase["submitted_purchase_invoices"] = frappe.db.sql(
        """
        select count(*) as count
        from `tabPurchase Invoice`
        where docstatus = 1
          and posting_date between %s and %s
        """,
        ("2025-04-01", "2026-03-31"),
        as_dict=True,
    )[0]["count"]
    purchase["purchase_invoice_chain_outliers"] = frappe.db.sql(
        """
        select pi.name, pi.supplier, pi.posting_date, pi.grand_total, pi.update_stock
        from `tabPurchase Invoice` pi
        left join `tabPurchase Invoice Item` pii on pii.parent = pi.name
        where pi.docstatus = 1
          and pi.posting_date between %s and %s
        group by pi.name
        having sum(case when ifnull(pii.purchase_receipt, '') != '' then 1 else 0 end) = 0
           and max(ifnull(pi.update_stock, 0)) = 0
        order by pi.grand_total desc
        limit 10
        """,
        ("2025-04-01", "2026-03-31"),
        as_dict=True,
    )
    purchase["po_to_pr_gap_outliers"] = frappe.db.sql(
        """
        select po.name as purchase_order, po.supplier, po.transaction_date, min(pr.posting_date) as first_receipt_date,
               datediff(min(pr.posting_date), po.transaction_date) as gap_days
        from `tabPurchase Order` po
        inner join `tabPurchase Receipt Item` pri on pri.purchase_order = po.name
        inner join `tabPurchase Receipt` pr on pr.name = pri.parent and pr.docstatus = 1
        where po.docstatus = 1
          and po.transaction_date between %s and %s
        group by po.name, po.supplier, po.transaction_date
        having gap_days > 21
        order by gap_days desc
        limit 10
        """,
        ("2025-04-01", "2026-03-31"),
        as_dict=True,
    )
    purchase["pr_to_pi_gap_outliers"] = frappe.db.sql(
        """
        select pr.name as purchase_receipt, pr.supplier, pr.posting_date as receipt_date, min(pi.posting_date) as first_invoice_date,
               datediff(min(pi.posting_date), pr.posting_date) as gap_days
        from `tabPurchase Receipt` pr
        inner join `tabPurchase Invoice Item` pii on pii.purchase_receipt = pr.name
        inner join `tabPurchase Invoice` pi on pi.name = pii.parent and pi.docstatus = 1
        where pr.docstatus = 1
          and pr.posting_date between %s and %s
        group by pr.name, pr.supplier, pr.posting_date
        having gap_days > 21
        order by gap_days desc
        limit 10
        """,
        ("2025-04-01", "2026-03-31"),
        as_dict=True,
    )

    return {"sales": sales, "purchase": purchase}


def debug_doctype_columns(doctype: str) -> list[str]:
    meta = frappe.get_meta(doctype)
    return [field.fieldname for field in meta.fields]


def debug_chain_doctype_columns() -> dict[str, list[str]]:
    return {
        "Sales Order Item": debug_doctype_columns("Sales Order Item"),
        "Sales Invoice Item": debug_doctype_columns("Sales Invoice Item"),
        "Purchase Invoice Item": debug_doctype_columns("Purchase Invoice Item"),
        "Purchase Receipt Item": debug_doctype_columns("Purchase Receipt Item"),
    }


def audit_fy2526_direct_invoice_cases() -> list[dict[str, Any]]:
    return frappe.db.sql(
        """
        select
            si.name,
            si.customer,
            si.posting_date,
            si.grand_total,
            si.update_stock,
            max(case when ifnull(sii.sales_order, '') != '' then 1 else 0 end) as has_sales_order,
            max(case when ifnull(sii.delivery_note, '') != '' then 1 else 0 end) as has_delivery_note,
            group_concat(distinct sii.item_group order by sii.item_group separator ', ') as item_groups
        from `tabSales Invoice` si
        inner join `tabSales Invoice Item` sii on sii.parent = si.name
        where si.docstatus = 1
          and si.posting_date between %s and %s
        group by si.name, si.customer, si.posting_date, si.grand_total, si.update_stock
        having has_delivery_note = 0 and max(ifnull(si.update_stock, 0)) = 0
        order by si.grand_total desc
        limit 20
        """,
        ("2025-04-01", "2026-03-31"),
        as_dict=True,
    )


def _invoice_item_link_map(parent_doctype: str, parent_name: str, child_field: str) -> dict[tuple[str, float], str]:
    if parent_doctype == "Sales Order":
        rows = frappe.get_all(
            "Sales Order Item",
            filters={"parent": parent_name},
            fields=["name", "item_code", "qty"],
        )
    elif parent_doctype == "Delivery Note":
        rows = frappe.get_all(
            "Delivery Note Item",
            filters={"parent": parent_name},
            fields=["name", "item_code", "qty"],
        )
    else:
        return {}
    mapping: dict[tuple[str, float], str] = {}
    for row in rows:
        mapping[(str(row["item_code"]), float(row["qty"]))] = row["name"]
    return mapping


def _rebuild_sales_chain_for_invoice(invoice_name: str, order_date: str, delivery_date: str) -> dict[str, Any]:
    invoice = frappe.get_doc("Sales Invoice", invoice_name)
    if invoice.docstatus != 1:
        raise frappe.ValidationError(f"{invoice_name} is not submitted.")

    items = []
    warehouse = None
    for item in invoice.items:
        warehouse = warehouse or item.warehouse
        items.append(
            {
                "item_code": item.item_code,
                "qty": item.qty,
                "rate": item.rate,
                "warehouse": item.warehouse,
                "delivery_date": delivery_date,
            }
        )

    sales_order_name = _create_sales_order(
        {
            "customer": invoice.customer,
            "company": invoice.company,
            "transaction_date": order_date,
            "delivery_date": delivery_date,
            "po_no": f"HIST-{invoice_name}",
            "po_date": order_date,
            "payment_terms_template": invoice.payment_terms_template,
            "set_warehouse": warehouse,
            "remarks": f"Historical commercial chain reconstruction for {invoice_name}.",
            "items": items,
        }
    )
    delivery_note_name = _create_delivery_note_from_sales_order(
        sales_order_name,
        {
            "posting_date": delivery_date,
            "posting_time": "10:30:00",
            "lr_date": delivery_date,
            "remarks": f"Historical delivery reconstruction for {invoice_name}.",
        },
    )

    so_item_map = _invoice_item_link_map("Sales Order", sales_order_name, "so_detail")
    dn_item_map = _invoice_item_link_map("Delivery Note", delivery_note_name, "dn_detail")

    for item in invoice.items:
        key = (str(item.item_code), float(item.qty))
        values = {
            "sales_order": sales_order_name,
            "so_detail": so_item_map.get(key),
            "delivery_note": delivery_note_name,
            "dn_detail": dn_item_map.get(key),
        }
        frappe.db.set_value("Sales Invoice Item", item.name, values, update_modified=False)

    frappe.db.set_value(
        "Sales Invoice",
        invoice_name,
        {
            "update_billed_amount_in_sales_order": 1,
            "update_billed_amount_in_delivery_note": 1,
            "remarks": f"{invoice.remarks or 'No Remarks'} | Historical chain normalized via Sales Order {sales_order_name} and Delivery Note {delivery_note_name}.",
        },
        update_modified=False,
    )
    frappe.db.commit()

    return {
        "sales_invoice": invoice_name,
        "sales_order": sales_order_name,
        "delivery_note": delivery_note_name,
    }


def _attach_sales_order_only_for_invoice(invoice_name: str, order_date: str) -> dict[str, Any]:
    invoice = frappe.get_doc("Sales Invoice", invoice_name)
    if invoice.docstatus != 1:
        raise frappe.ValidationError(f"{invoice_name} is not submitted.")

    items = []
    warehouse = None
    for item in invoice.items:
        warehouse = warehouse or item.warehouse
        items.append(
            {
                "item_code": item.item_code,
                "qty": item.qty,
                "rate": item.rate,
                "warehouse": item.warehouse,
                "delivery_date": invoice.posting_date,
            }
        )

    sales_order_name = _create_sales_order(
        {
            "customer": invoice.customer,
            "company": invoice.company,
            "transaction_date": order_date,
            "delivery_date": invoice.posting_date,
            "po_no": f"HIST-{invoice_name}",
            "po_date": order_date,
            "payment_terms_template": invoice.payment_terms_template,
            "set_warehouse": warehouse,
            "remarks": f"Historical order reconstruction for {invoice_name}; delivery detail retained as legacy external dispatch.",
            "items": items,
        }
    )
    so_item_map = _invoice_item_link_map("Sales Order", sales_order_name, "so_detail")
    for item in invoice.items:
        key = (str(item.item_code), float(item.qty))
        values = {
            "sales_order": sales_order_name,
            "so_detail": so_item_map.get(key),
        }
        frappe.db.set_value("Sales Invoice Item", item.name, values, update_modified=False)

    frappe.db.set_value(
        "Sales Invoice",
        invoice_name,
        {
            "update_billed_amount_in_sales_order": 1,
            "remarks": f"{invoice.remarks or 'No Remarks'} | Historical order normalized via Sales Order {sales_order_name}; delivery kept as legacy direct billing exception.",
        },
        update_modified=False,
    )
    frappe.db.commit()
    return {"sales_invoice": invoice_name, "sales_order": sales_order_name}


def _classify_direct_billing_exception(invoice_name: str, reason: str) -> dict[str, Any]:
    invoice = frappe.get_doc("Sales Invoice", invoice_name)
    existing_remarks = str(invoice.remarks or "").strip()
    note = f"Historical direct-billing exception classified: {reason}"
    if note in existing_remarks:
        return {"sales_invoice": invoice_name, "classification": "direct_billing_exception"}

    merged_remarks = f"{existing_remarks} | {note}" if existing_remarks else note
    frappe.db.set_value(
        "Sales Invoice",
        invoice_name,
        {"remarks": merged_remarks},
        update_modified=False,
    )
    frappe.db.commit()
    return {"sales_invoice": invoice_name, "classification": "direct_billing_exception"}


def _relink_delivery_note_to_sales_order(delivery_note_name: str, sales_order_name: str) -> dict[tuple[str, float], str]:
    so_item_map = _invoice_item_link_map("Sales Order", sales_order_name, "so_detail")
    dn_item_map = _invoice_item_link_map("Delivery Note", delivery_note_name, "dn_detail")
    delivery_note = frappe.get_doc("Delivery Note", delivery_note_name)

    for item in delivery_note.items:
        key = (str(item.item_code), float(item.qty))
        frappe.db.set_value(
            "Delivery Note Item",
            item.name,
            {
                "against_sales_order": sales_order_name,
                "so_detail": so_item_map.get(key),
            },
            update_modified=False,
        )
    return dn_item_map


def _relink_sales_invoice_to_existing_chain(
    invoice_name: str,
    sales_order_name: str | None = None,
    delivery_note_name: str | None = None,
    classification_reason: str | None = None,
) -> dict[str, Any]:
    invoice = frappe.get_doc("Sales Invoice", invoice_name)
    so_item_map = _invoice_item_link_map("Sales Order", sales_order_name, "so_detail") if sales_order_name else {}
    dn_item_map = _invoice_item_link_map("Delivery Note", delivery_note_name, "dn_detail") if delivery_note_name else {}

    for item in invoice.items:
        key = (str(item.item_code), float(item.qty))
        values = {
            "sales_order": sales_order_name,
            "so_detail": so_item_map.get(key) if sales_order_name else None,
            "delivery_note": delivery_note_name,
            "dn_detail": dn_item_map.get(key) if delivery_note_name else None,
        }
        frappe.db.set_value("Sales Invoice Item", item.name, values, update_modified=False)

    update_values = {
        "update_billed_amount_in_sales_order": 1 if sales_order_name else 0,
        "update_billed_amount_in_delivery_note": 1 if delivery_note_name else 0,
    }
    frappe.db.set_value("Sales Invoice", invoice_name, update_values, update_modified=False)
    frappe.db.commit()

    if classification_reason:
        _classify_direct_billing_exception(invoice_name, classification_reason)

    return {
        "sales_invoice": invoice_name,
        "sales_order": sales_order_name,
        "delivery_note": delivery_note_name,
        "classification_reason": classification_reason,
    }


def _normalize_direct_stock_invoice_to_delivery_chain(target: dict[str, Any]) -> dict[str, Any]:
    invoice_name = target["invoice_name"]
    if not frappe.db.exists("Sales Invoice", invoice_name):
        raise frappe.ValidationError(f"Sales Invoice {invoice_name} does not exist.")

    original_invoice = frappe.get_doc("Sales Invoice", invoice_name)
    expected_total = float(original_invoice.grand_total or 0)

    existing_order_name = _find_submitted_sales_order(
        original_invoice.customer,
        target["sales_order"]["transaction_date"],
        target["sales_order"].get("po_no"),
        expected_total,
    )
    if original_invoice.docstatus == 2 and existing_order_name:
        delivery_note_name = _find_submitted_delivery_note_for_sales_order(
            existing_order_name,
            target["delivery_note"]["posting_date"],
        )
        if delivery_note_name:
            rebuilt_invoice_name = _find_submitted_sales_invoice_for_delivery_note(
                delivery_note_name,
                target["sales_invoice"]["posting_date"],
            )
            if rebuilt_invoice_name:
                return {
                    "original_invoice": invoice_name,
                    "quotation": target.get("quotation_name"),
                    "sales_order": existing_order_name,
                    "delivery_note": delivery_note_name,
                    "sales_invoice": rebuilt_invoice_name,
                    "rebuilt_payments": [],
                }

    payment_specs = _collect_payment_rebuild_specs(invoice_name)
    canceled_payments = []
    if original_invoice.docstatus == 1:
        for spec in payment_specs:
            if spec["reference_count"] > 1:
                raise frappe.ValidationError(
                    f"Payment Entry {spec['payment_entry']} has multiple references; cannot safely rebuild {invoice_name} automatically."
                )
            if _cancel_submitted_doc("Payment Entry", spec["payment_entry"]):
                canceled_payments.append(spec["payment_entry"])
        _cancel_submitted_doc("Sales Invoice", invoice_name)
        frappe.db.commit()

    quoted_items = target.get("quotation_items") or [
        {
            "item_code": item.item_code,
            "qty": float(item.qty),
            "rate": float(item.rate),
            "warehouse": item.warehouse,
        }
        for item in original_invoice.items
    ]

    quotation_name = None
    if target.get("quotation"):
        quotation_payload = {
            **target["quotation"],
            "customer": original_invoice.customer,
            "company": original_invoice.company,
            "items": quoted_items,
            "expected_total": _sum_item_amounts(quoted_items),
        }
        quotation_name = _create_quotation(quotation_payload)
        order_date = getdate(target["sales_order"]["transaction_date"])
        valid_till = getdate(frappe.db.get_value("Quotation", quotation_name, "valid_till"))
        if valid_till and valid_till < order_date:
            frappe.db.set_value("Quotation", quotation_name, "valid_till", str(order_date), update_modified=False)
            frappe.db.commit()
        try:
            sales_order_name = _create_sales_order_from_quotation(
                quotation_name,
                {
                    **target["sales_order"],
                    "customer": original_invoice.customer,
                    "expected_total": _sum_item_amounts(quoted_items),
                },
            )
        except Exception as exc:
            if "Validity period of this quotation has ended." not in str(exc):
                raise
            sales_order_name = _create_sales_order(
                {
                    **target["sales_order"],
                    "customer": original_invoice.customer,
                    "company": original_invoice.company,
                    "items": quoted_items,
                    "expected_total": _sum_item_amounts(quoted_items),
                    "remarks": f"{target['sales_order'].get('remarks') or ''} Historical quotation conversion recreated directly because the original quotation validity already passed in the live system.",
                }
            )
            frappe.db.set_value("Quotation", quotation_name, "status", "Ordered", update_modified=False)
            _sync_quotation_workflow_state(quotation_name)
            frappe.db.commit()
    else:
        sales_order_name = _create_sales_order(
            {
                **target["sales_order"],
                "customer": original_invoice.customer,
                "company": original_invoice.company,
                "items": quoted_items,
                "expected_total": _sum_item_amounts(quoted_items),
            }
        )

    delivery_note_name = _create_delivery_note_from_sales_order(
        sales_order_name,
        target["delivery_note"],
    )
    rebuilt_invoice_name = _create_sales_invoice_from_delivery_note(
        delivery_note_name,
        target["sales_invoice"],
    )
    frappe.db.commit()

    rebuilt_payments = []
    for spec in payment_specs:
        payment_name = _create_partial_payment_with_date_dedupe(
            "Sales Invoice",
            rebuilt_invoice_name,
            spec["posting_date"],
            spec["allocated_amount"],
        )
        rebuilt_payments.append(payment_name)
        frappe.db.commit()

    return {
        "original_invoice": invoice_name,
        "quotation": quotation_name,
        "sales_order": sales_order_name,
        "delivery_note": delivery_note_name,
        "sales_invoice": rebuilt_invoice_name,
        "canceled_payments": canceled_payments,
        "rebuilt_payments": rebuilt_payments,
    }


def _recreate_canceled_stock_sales_invoice(
    invoice_name: str,
    payment_specs: list[dict[str, Any]] | None = None,
    remarks_suffix: str | None = None,
) -> dict[str, Any]:
    if not frappe.db.exists("Sales Invoice", invoice_name):
        raise frappe.ValidationError(f"Sales Invoice {invoice_name} does not exist.")

    original_invoice = frappe.get_doc("Sales Invoice", invoice_name)
    expected_total = float(original_invoice.grand_total or 0)
    existing_name = _find_submitted_sales_invoice(
        original_invoice.customer,
        str(original_invoice.posting_date),
        expected_total,
    )

    if existing_name:
        recreated_invoice_name = existing_name
    else:
        warehouse = original_invoice.set_warehouse or (
            original_invoice.items[0].warehouse if original_invoice.items else None
        )
        if not warehouse:
            raise frappe.ValidationError(f"No warehouse found for canceled invoice {invoice_name}.")

        remarks = original_invoice.remarks or ""
        if remarks_suffix:
            remarks = f"{remarks} {remarks_suffix}".strip()

        recreated_invoice_name = _create_sales_invoice(
            {
                "customer": original_invoice.customer,
                "posting_date": str(original_invoice.posting_date),
                "posting_time": original_invoice.posting_time or "10:00:00",
                "due_date": str(original_invoice.due_date or original_invoice.posting_date),
                "warehouse": warehouse,
                "company": original_invoice.company,
                "expected_total": expected_total,
                "remarks": remarks,
                "items": [
                    {
                        "item_code": item.item_code,
                        "qty": float(item.qty),
                        "rate": float(item.rate),
                        "warehouse": item.warehouse or warehouse,
                        "income_account": item.income_account,
                        "expense_account": item.expense_account,
                        "cost_center": item.cost_center,
                    }
                    for item in original_invoice.items
                ],
            }
        )
        frappe.db.commit()

    rebuilt_payments = []
    for spec in payment_specs or []:
        payment_name = _create_partial_payment_with_date_dedupe(
            "Sales Invoice",
            recreated_invoice_name,
            spec["posting_date"],
            spec["amount"],
        )
        rebuilt_payments.append(payment_name)
        frappe.db.commit()

    return {
        "original_invoice": invoice_name,
        "sales_invoice": recreated_invoice_name,
        "rebuilt_payments": rebuilt_payments,
    }


def apply_fy2526_sales_chain_reconstruction_wave() -> dict[str, Any]:
    targets = [
        ("ACC-SINV-2026-00609", "2025-07-09", "2025-07-11"),
        ("ACC-SINV-2026-00610", "2025-07-11", "2025-07-13"),
        ("ACC-SINV-2026-00611", "2025-07-14", "2025-07-16"),
        ("ACC-SINV-2026-00614", "2025-08-10", "2025-08-12"),
        ("ACC-SINV-2026-00615", "2025-08-12", "2025-08-14"),
        ("ACC-SINV-2026-00616", "2025-08-20", "2025-08-22"),
    ]
    result = {"repaired": [], "failed": []}
    for invoice_name, order_date, delivery_date in targets:
        if not frappe.db.exists("Sales Invoice", invoice_name):
            continue
        try:
            repaired = _rebuild_sales_chain_for_invoice(invoice_name, order_date, delivery_date)
            result["repaired"].append(repaired)
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"sales_invoice": invoice_name, "error": str(exc)})
    return result


def apply_fy2526_sales_order_only_normalization_wave() -> dict[str, Any]:
    targets = [
        ("ACC-SINV-2026-00609", "2025-07-09"),
        ("ACC-SINV-2026-00610", "2025-07-11"),
        ("ACC-SINV-2026-00611", "2025-07-14"),
        ("ACC-SINV-2026-00614", "2025-08-10"),
        ("ACC-SINV-2026-00615", "2025-08-12"),
        ("ACC-SINV-2026-00616", "2025-08-20"),
        ("ACC-SINV-2026-00617", "2025-08-16"),
        ("ACC-SINV-2026-00612", "2025-07-18"),
    ]
    result = {"normalized": [], "failed": []}
    for invoice_name, order_date in targets:
        if not frappe.db.exists("Sales Invoice", invoice_name):
            continue
        try:
            normalized = _attach_sales_order_only_for_invoice(invoice_name, order_date)
            result["normalized"].append(normalized)
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"sales_invoice": invoice_name, "error": str(exc)})
    return result


def apply_fy2526_sales_exception_classification_wave() -> dict[str, Any]:
    result = {"normalized": [], "classified": [], "failed": []}

    normalization_targets = [
        ("ACC-SINV-2026-00191", "2026-03-29"),
        ("ACC-SINV-2026-00613", "2025-07-15"),
        ("ACC-SINV-2026-00618", "2025-08-22"),
    ]
    for invoice_name, order_date in normalization_targets:
        if not frappe.db.exists("Sales Invoice", invoice_name):
            continue
        try:
            normalized = _attach_sales_order_only_for_invoice(invoice_name, order_date)
            result["normalized"].append(normalized)
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"sales_invoice": invoice_name, "error": str(exc)})

    classification_targets = [
        (
            "ACC-SINV-2026-00617",
            "wholesale invoice retained as direct-billing exception because retrospective sales-order recreation is blocked by customer credit governance",
        ),
        (
            "ACC-SINV-2026-00187",
            "small accessory replenishment billed directly at month-end without separate dispatch paperwork",
        ),
        (
            "ACC-SINV-2026-00190",
            "tiny wholesale accessory top-up billed directly with same-day hand carry release",
        ),
        (
            "ACC-SINV-2026-00192",
            "small memory-card replenishment billed directly at month-end counter dispatch",
        ),
        (
            "ACC-SINV-2026-00185",
            "minor accessory add-on billed directly together with broader customer settlement cycle",
        ),
        (
            "ACC-SINV-2026-00186",
            "minor storage add-on billed directly together with broader customer settlement cycle",
        ),
        (
            "ACC-SINV-2026-00188",
            "small accessory replenishment billed directly at month-end counter dispatch",
        ),
        (
            "ACC-SINV-2026-00189",
            "tiny memory item billed directly through counter-sale exception flow",
        ),
    ]
    for invoice_name, reason in classification_targets:
        if not frappe.db.exists("Sales Invoice", invoice_name):
            continue
        try:
            classified = _classify_direct_billing_exception(invoice_name, reason)
            result["classified"].append(classified)
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"sales_invoice": invoice_name, "error": str(exc)})

    return result


def audit_fy2526_financial_realism_summary() -> dict[str, Any]:
    audit = audit_fy2526_financial_realism()
    if audit.get("status") != "ok":
        return audit

    cash_audit = audit_fy2526_cash_flow_variance()
    if cash_audit.get("status") != "ok":
        return cash_audit

    summary_rows = []
    for row in audit["monthly_summary"]:
        sales = row.get("sales_monthly", 0) or 0
        cogs = row.get("cogs_monthly", 0) or 0
        expense = row.get("expense_monthly", 0) or 0
        gross_profit = sales - cogs
        operating_result = gross_profit - expense
        margin = (gross_profit / sales) if sales else 0
        summary_rows.append(
            {
                "month": row.get("month"),
                "sales": sales,
                "cogs": cogs,
                "gross_profit": gross_profit,
                "gross_margin": round(margin * 100, 2),
                "expense": expense,
                "operating_result": operating_result,
                "payroll_net": row.get("payroll_net", 0),
            }
        )

    totals = audit["totals"]
    total_sales = totals.get("sales_monthly", 0)
    total_cogs = totals.get("cogs_monthly", 0)
    total_expense = totals.get("expense_monthly", 0)
    total_gross = total_sales - total_cogs
    total_operating = total_gross - total_expense
    total_margin = (total_gross / total_sales) if total_sales else 0

    return {
        "status": "ok",
        "totals": {
            "sales": total_sales,
            "cogs": total_cogs,
            "gross_profit": total_gross,
            "gross_margin": round(total_margin * 100, 2),
            "expense": total_expense,
            "operating_result": total_operating,
            "payroll_net": totals.get("payroll_net", 0),
        },
        "monthly_summary": summary_rows,
        "cash_flow": cash_audit,
    }


def audit_fy2526_commercial_realism_distribution() -> dict[str, Any]:
    fy_start = "2025-04-01"
    fy_end = "2026-03-31"
    months = {row["month_key"]: {"month": row["month_key"]} for row in _month_series(fy_start, fy_end)}

    def _set_month_values(rows: list[dict[str, Any]], key_map: dict[str, str]) -> None:
        for row in rows:
            month_key = row["month_key"]
            target = months.setdefault(month_key, {"month": month_key})
            for source_key, target_key in key_map.items():
                target[target_key] = row.get(source_key, 0)

    quotation_rows = frappe.db.sql(
        """
        select
            date_format(transaction_date, '%%Y-%%m') as month_key,
            count(*) as quotation_count,
            sum(case when status = 'Ordered' then 1 else 0 end) as quotation_ordered_count,
            sum(case when status = 'Lost' then 1 else 0 end) as quotation_lost_count,
            sum(case when status = 'Expired' then 1 else 0 end) as quotation_expired_count,
            sum(case when status not in ('Ordered', 'Lost', 'Expired') then 1 else 0 end) as quotation_open_count
        from `tabQuotation`
        where docstatus = 1
          and transaction_date between %s and %s
        group by month_key
        order by month_key
        """,
        (fy_start, fy_end),
        as_dict=True,
    )
    _set_month_values(
        quotation_rows,
        {
            "quotation_count": "quotation_count",
            "quotation_ordered_count": "quotation_ordered_count",
            "quotation_lost_count": "quotation_lost_count",
            "quotation_expired_count": "quotation_expired_count",
            "quotation_open_count": "quotation_open_count",
        },
    )

    sales_order_rows = frappe.db.sql(
        """
        select
            date_format(transaction_date, '%%Y-%%m') as month_key,
            count(*) as sales_order_count,
            sum(case when status in ('Completed', 'Closed') then 1 else 0 end) as sales_order_closed_count,
            sum(case when status not in ('Completed', 'Closed') then 1 else 0 end) as sales_order_open_count
        from `tabSales Order`
        where docstatus = 1
          and transaction_date between %s and %s
        group by month_key
        order by month_key
        """,
        (fy_start, fy_end),
        as_dict=True,
    )
    _set_month_values(
        sales_order_rows,
        {
            "sales_order_count": "sales_order_count",
            "sales_order_closed_count": "sales_order_closed_count",
            "sales_order_open_count": "sales_order_open_count",
        },
    )

    delivery_rows = frappe.db.sql(
        """
        select
            date_format(posting_date, '%%Y-%%m') as month_key,
            count(*) as delivery_note_count
        from `tabDelivery Note`
        where docstatus = 1
          and posting_date between %s and %s
        group by month_key
        order by month_key
        """,
        (fy_start, fy_end),
        as_dict=True,
    )
    _set_month_values(delivery_rows, {"delivery_note_count": "delivery_note_count"})

    sales_invoice_rows = frappe.db.sql(
        """
        select
            date_format(posting_date, '%%Y-%%m') as month_key,
            sum(case when is_return = 0 then 1 else 0 end) as sales_invoice_count,
            sum(case when is_return = 0 then grand_total else 0 end) as sales_amount,
            avg(case when is_return = 0 then grand_total else null end) as average_invoice_amount,
            sum(case when is_return = 0 and update_stock = 1 then 1 else 0 end) as direct_stock_invoice_count,
            sum(case when is_return = 0 and ifnull(remarks, '') like %s then 1 else 0 end) as classified_direct_billing_count,
            sum(case when is_return = 1 then 1 else 0 end) as sales_return_invoice_count,
            sum(case when is_return = 1 then abs(grand_total) else 0 end) as sales_return_amount
        from `tabSales Invoice`
        where docstatus = 1
          and posting_date between %s and %s
        group by month_key
        order by month_key
        """,
        ("%Historical direct-billing exception classified:%", fy_start, fy_end),
        as_dict=True,
    )
    _set_month_values(
        sales_invoice_rows,
        {
            "sales_invoice_count": "sales_invoice_count",
            "sales_amount": "sales_amount",
            "average_invoice_amount": "average_invoice_amount",
            "direct_stock_invoice_count": "direct_stock_invoice_count",
            "classified_direct_billing_count": "classified_direct_billing_count",
            "sales_return_invoice_count": "sales_return_invoice_count",
            "sales_return_amount": "sales_return_amount",
        },
    )

    receipt_rows = frappe.db.sql(
        """
        select
            date_format(posting_date, '%%Y-%%m') as month_key,
            count(*) as customer_receipt_count,
            sum(received_amount) as customer_receipt_amount
        from `tabPayment Entry`
        where docstatus = 1
          and payment_type = 'Receive'
          and party_type = 'Customer'
          and posting_date between %s and %s
        group by month_key
        order by month_key
        """,
        (fy_start, fy_end),
        as_dict=True,
    )
    _set_month_values(
        receipt_rows,
        {
            "customer_receipt_count": "customer_receipt_count",
            "customer_receipt_amount": "customer_receipt_amount",
        },
    )

    purchase_invoice_rows = frappe.db.sql(
        """
        select
            date_format(posting_date, '%%Y-%%m') as month_key,
            sum(case when is_return = 0 then 1 else 0 end) as purchase_invoice_count,
            sum(case when is_return = 0 then grand_total else 0 end) as purchase_amount,
            sum(case when is_return = 1 then 1 else 0 end) as purchase_return_count,
            sum(case when is_return = 1 then abs(grand_total) else 0 end) as purchase_return_amount
        from `tabPurchase Invoice`
        where docstatus = 1
          and posting_date between %s and %s
        group by month_key
        order by month_key
        """,
        (fy_start, fy_end),
        as_dict=True,
    )
    _set_month_values(
        purchase_invoice_rows,
        {
            "purchase_invoice_count": "purchase_invoice_count",
            "purchase_amount": "purchase_amount",
            "purchase_return_count": "purchase_return_count",
            "purchase_return_amount": "purchase_return_amount",
        },
    )

    supplier_payment_rows = frappe.db.sql(
        """
        select
            date_format(posting_date, '%%Y-%%m') as month_key,
            count(*) as supplier_payment_count,
            sum(paid_amount) as supplier_payment_amount
        from `tabPayment Entry`
        where docstatus = 1
          and payment_type = 'Pay'
          and party_type = 'Supplier'
          and posting_date between %s and %s
        group by month_key
        order by month_key
        """,
        (fy_start, fy_end),
        as_dict=True,
    )
    _set_month_values(
        supplier_payment_rows,
        {
            "supplier_payment_count": "supplier_payment_count",
            "supplier_payment_amount": "supplier_payment_amount",
        },
    )

    monthly_summary = []
    for month_key in sorted(months.keys()):
        row = months[month_key]
        sales_amount = float(row.get("sales_amount") or 0)
        quotation_count = int(row.get("quotation_count") or 0)
        sales_order_count = int(row.get("sales_order_count") or 0)
        sales_invoice_count = int(row.get("sales_invoice_count") or 0)
        receipt_amount = float(row.get("customer_receipt_amount") or 0)
        row["quotation_to_order_ratio"] = round((sales_order_count / quotation_count), 2) if quotation_count else None
        row["invoice_collection_ratio"] = round((receipt_amount / sales_amount), 2) if sales_amount else None
        monthly_summary.append(row)

    total_sales = sum(float(row.get("sales_amount") or 0) for row in monthly_summary)

    top_customers = frappe.db.sql(
        """
        select
            customer,
            count(*) as invoice_count,
            sum(grand_total) as sales_amount
        from `tabSales Invoice`
        where docstatus = 1
          and is_return = 0
          and posting_date between %s and %s
        group by customer
        order by sales_amount desc
        limit 10
        """,
        (fy_start, fy_end),
        as_dict=True,
    )
    for row in top_customers:
        sales_amount = float(row.get("sales_amount") or 0)
        row["sales_amount"] = sales_amount
        row["share_of_total_sales"] = round((sales_amount / total_sales) * 100, 2) if total_sales else 0

    top_items = frappe.db.sql(
        """
        select
            sii.item_code,
            sum(sii.qty) as total_qty,
            sum(sii.amount) as sales_amount,
            count(distinct si.name) as invoice_count
        from `tabSales Invoice Item` sii
        inner join `tabSales Invoice` si on si.name = sii.parent
        where si.docstatus = 1
          and si.is_return = 0
          and si.posting_date between %s and %s
        group by sii.item_code
        order by sales_amount desc
        limit 10
        """,
        (fy_start, fy_end),
        as_dict=True,
    )
    for row in top_items:
        sales_amount = float(row.get("sales_amount") or 0)
        row["sales_amount"] = sales_amount
        row["share_of_total_sales"] = round((sales_amount / total_sales) * 100, 2) if total_sales else 0

    top_3_customer_share = round(sum(float(row.get("share_of_total_sales") or 0) for row in top_customers[:3]), 2)
    top_10_customer_share = round(sum(float(row.get("share_of_total_sales") or 0) for row in top_customers), 2)
    top_3_item_share = round(sum(float(row.get("share_of_total_sales") or 0) for row in top_items[:3]), 2)
    top_10_item_share = round(sum(float(row.get("share_of_total_sales") or 0) for row in top_items), 2)

    return {
        "status": "ok",
        "monthly_summary": monthly_summary,
        "totals": {
            "sales_amount": total_sales,
            "quotation_count": sum(int(row.get("quotation_count") or 0) for row in monthly_summary),
            "sales_order_count": sum(int(row.get("sales_order_count") or 0) for row in monthly_summary),
            "sales_invoice_count": sum(int(row.get("sales_invoice_count") or 0) for row in monthly_summary),
            "delivery_note_count": sum(int(row.get("delivery_note_count") or 0) for row in monthly_summary),
            "customer_receipt_amount": sum(float(row.get("customer_receipt_amount") or 0) for row in monthly_summary),
            "purchase_amount": sum(float(row.get("purchase_amount") or 0) for row in monthly_summary),
            "supplier_payment_amount": sum(float(row.get("supplier_payment_amount") or 0) for row in monthly_summary),
        },
        "concentration": {
            "top_3_customer_share": top_3_customer_share,
            "top_10_customer_share": top_10_customer_share,
            "top_3_item_share": top_3_item_share,
            "top_10_item_share": top_10_item_share,
            "top_customers": top_customers,
            "top_items": top_items,
        },
    }


def apply_fy2526_payroll_accrual_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    salary_expense_account = _find_account_by_names(
        [
            "Salaries and Wages - MMOB",
            "Salary - MMOB",
            "Payroll Expenses - MMOB",
            "Staff Salary - MMOB",
            "Salary Expense - MMOB",
        ]
    )
    payroll_payable_account = _find_account_by_names(
        [
            "Payroll Payable - MMOB",
            "Salary Payable - MMOB",
        ]
    )
    if not salary_expense_account or not payroll_payable_account:
        return {
            "journal_entries": [],
            "failed": [
                {
                    "error": "missing_payroll_accounts",
                    "salary_expense_account": salary_expense_account,
                    "payroll_payable_account": payroll_payable_account,
                }
            ],
        }

    result = {"journal_entries": [], "failed": []}
    for month in _month_series("2025-04-01", "2026-03-31"):
        payroll_rows = frappe.db.sql(
            """
            select sum(net_pay) as net_pay
            from `tabSalary Slip`
            where docstatus=1
              and posting_date between %s and %s
            """,
            (month["period_start"], month["period_end"]),
            as_dict=True,
        )
        net_pay = float((payroll_rows[0]["net_pay"] or 0) if payroll_rows else 0)
        if net_pay <= 0:
            continue
        rounded_amount = int(round(net_pay / 1000.0) * 1000)
        if rounded_amount <= 0:
            continue

        user_remark = f"AI-FY2526-PAYROLL-ACCRUAL-{month['month_key']}"
        try:
            journal_entry_name = _create_simple_journal_entry(
                {
                    "company": company,
                    "posting_date": month["posting_date"],
                    "voucher_type": "Journal Entry",
                    "user_remark": user_remark,
                    "accounts": [
                        {
                            "account": salary_expense_account,
                            "debit_in_account_currency": rounded_amount,
                        },
                        {
                            "account": payroll_payable_account,
                            "credit_in_account_currency": rounded_amount,
                        },
                    ],
                }
            )
            frappe.db.commit()
            result["journal_entries"].append(
                {
                    "month": month["month_key"],
                    "journal_entry": journal_entry_name,
                    "amount": rounded_amount,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"month": month["month_key"], "error": str(exc)}
            )
    return result


def apply_fy2526_operating_expense_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    cash_account = _find_account_by_names(
        [
            "Cash - MMOB",
            "KBZ-001-000123 - KBZ Bank - Current - MMOB",
            "CB-001-000789 - CB Bank - Current - MMOB",
            "AYA-001-000456 - AYA Bank - Current - MMOB",
        ]
    )
    if not cash_account:
        return {"journal_entries": [], "failed": [{"error": "missing_cash_account"}]}

    expense_accounts = {
        "rent": _find_account_by_names(["Rent - MMOB", "Office Rent - MMOB", "Rent Expense - MMOB"]),
        "utilities": _find_account_by_names(["Utilities - MMOB", "Electricity - MMOB", "Water Expense - MMOB"]),
        "logistics": _find_account_by_names(
            ["Delivery Expenses - MMOB", "Freight and Forwarding - MMOB", "Logistics - MMOB"]
        ),
        "marketing": _find_account_by_names(["Marketing Expenses - MMOB", "Sales Promotion - MMOB", "Advertising - MMOB"]),
        "admin": _find_account_by_names(["Office Expenses - MMOB", "Administrative Expenses - MMOB", "General Expenses - MMOB"]),
        "telecom": _find_account_by_names(["Telephone Expense - MMOB", "Internet Expense - MMOB", "Communication Expenses - MMOB"]),
    }

    result = {"journal_entries": [], "failed": []}
    month_series = _month_series("2025-04-01", "2026-03-31")
    rent = 5000000
    utilities = [1200000, 1300000, 1400000, 1450000, 1500000, 1550000, 1600000, 1650000, 1700000, 1750000, 1800000, 1900000]
    logistics = [1500000, 1600000, 1800000, 2000000, 2100000, 2300000, 2500000, 2600000, 2700000, 3000000, 3200000, 3500000]
    marketing = [700000, 800000, 900000, 1000000, 1100000, 1200000, 1300000, 1400000, 1500000, 1600000, 1800000, 2000000]
    admin = [900000, 900000, 1000000, 1000000, 1100000, 1200000, 1200000, 1300000, 1300000, 1400000, 1500000, 1600000]
    telecom = [600000, 600000, 650000, 650000, 700000, 750000, 750000, 800000, 800000, 850000, 900000, 950000]

    for idx, month in enumerate(month_series):
        accounts = []
        def _add_line(key, amount):
            account = expense_accounts.get(key)
            if account and amount:
                accounts.append(
                    {"account": account, "debit_in_account_currency": int(amount)}
                )

        _add_line("rent", rent)
        _add_line("utilities", utilities[idx])
        _add_line("logistics", logistics[idx])
        _add_line("marketing", marketing[idx])
        _add_line("admin", admin[idx])
        _add_line("telecom", telecom[idx])

        if not accounts:
            continue

        total_amount = int(sum(line["debit_in_account_currency"] for line in accounts))
        accounts.append({"account": cash_account, "credit_in_account_currency": total_amount})

        user_remark = f"AI-FY2526-OPEX-{month['month_key']}"
        try:
            journal_entry_name = _create_simple_journal_entry(
                {
                    "company": company,
                    "posting_date": month["posting_date"],
                    "voucher_type": "Journal Entry",
                    "user_remark": user_remark,
                    "accounts": accounts,
                }
            )
            frappe.db.commit()
            result["journal_entries"].append(
                {
                    "month": month["month_key"],
                    "journal_entry": journal_entry_name,
                    "amount": total_amount,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"month": month["month_key"], "error": str(exc)}
            )
    return result


def apply_fy2526_financial_realism_wave() -> dict[str, Any]:
    return {
        "payroll_accrual": apply_fy2526_payroll_accrual_wave(),
        "opex": apply_fy2526_operating_expense_wave(),
        "capex_financing": apply_fy2526_capex_financing_realism_wave(),
    }


def apply_fy2526_ar_ap_aging_normalization_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    customer_targets = [
        ("Bayint Naung Wholesale Mobile", "2026-02-20", 8000000),
        ("Capital Telecom (NPT)", "2026-02-24", 7000000),
        ("35th Street Mobile Wholesale", "2026-02-26", 9000000),
        ("Ko Nay Lin Mobile Center", "2026-03-02", 6000000),
        ("Latha Mobile Wholesale", "2026-03-06", 5000000),
        ("Mandalay Accessories Wholesale", "2026-03-10", 4000000),
    ]
    supplier_targets = [
        ("Shenzhen Silverway Trading", "2026-02-22", 12000000),
        ("Guangzhou Yatai Electronics", "2026-02-27", 9000000),
        ("Yangon Accessory Hub", "2026-03-05", 7000000),
        ("Mandalay Supply Network", "2026-03-09", 6000000),
    ]

    result = {"customer_payments": [], "supplier_payments": [], "failed": []}

    for customer, posting_date, amount in customer_targets:
        invoice_name = _find_outstanding_sales_invoice(customer, "2026-01-31")
        if not invoice_name:
            result["failed"].append(
                {"label": f"ar_{customer}", "error": "sales_invoice_missing"}
            )
            continue
        try:
            payment_name = _apply_targeted_partial_payment(
                "Sales Invoice", invoice_name, posting_date, amount
            )
            frappe.db.commit()
            result["customer_payments"].append(
                {
                    "customer": customer,
                    "sales_invoice": invoice_name,
                    "payment_entry": payment_name,
                    "amount": amount,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"label": f"ar_{customer}", "error": str(exc)}
            )

    for supplier, posting_date, amount in supplier_targets:
        invoice_name = _find_outstanding_purchase_invoice(supplier, "2026-01-31")
        if not invoice_name:
            result["failed"].append(
                {"label": f"ap_{supplier}", "error": "purchase_invoice_missing"}
            )
            continue
        try:
            payment_name = _apply_targeted_partial_payment(
                "Purchase Invoice", invoice_name, posting_date, amount
            )
            frappe.db.commit()
            result["supplier_payments"].append(
                {
                    "supplier": supplier,
                    "purchase_invoice": invoice_name,
                    "payment_entry": payment_name,
                    "amount": amount,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"label": f"ap_{supplier}", "error": str(exc)}
            )

    if not result["supplier_payments"]:
        fallback_invoices = frappe.db.sql(
            """
            select name, supplier, outstanding_amount
            from `tabPurchase Invoice`
            where docstatus=1
              and outstanding_amount > 0
              and posting_date <= %s
            order by posting_date asc
            limit 4
            """,
            ("2026-01-31",),
            as_dict=True,
        )
        for row in fallback_invoices:
            rounded_amount = int(round(float(row.outstanding_amount) * 0.3 / 1000.0) * 1000)
            if rounded_amount <= 0:
                continue
            posting_date = "2026-03-15"
            try:
                payment_name = _apply_targeted_partial_payment(
                    "Purchase Invoice", row.name, posting_date, rounded_amount
                )
                frappe.db.commit()
                result["supplier_payments"].append(
                    {
                        "supplier": row.supplier,
                        "purchase_invoice": row.name,
                        "payment_entry": payment_name,
                        "amount": rounded_amount,
                        "fallback": True,
                    }
                )
            except Exception as exc:
                frappe.db.rollback()
                result["failed"].append(
                    {"label": f"ap_fallback_{row.name}", "error": str(exc)}
                )

    return result


def audit_fy2526_invoice_terms_alignment() -> dict[str, Any]:
    sales_blank = frappe.db.sql(
        """
        select count(*) as cnt
        from `tabSales Invoice` si
        left join `tabCustomer` c on c.name = si.customer
        where si.docstatus = 1
          and si.posting_date between '2025-04-01' and '2026-03-31'
          and ifnull(si.payment_terms_template, '') = ''
          and ifnull(c.payment_terms, '') != ''
        """,
        as_dict=True,
    )[0]["cnt"]
    purchase_blank = frappe.db.sql(
        """
        select count(*) as cnt
        from `tabPurchase Invoice` pi
        left join `tabSupplier` s on s.name = pi.supplier
        where pi.docstatus = 1
          and pi.posting_date between '2025-04-01' and '2026-03-31'
          and ifnull(pi.payment_terms_template, '') = ''
          and ifnull(s.payment_terms, '') != ''
        """,
        as_dict=True,
    )[0]["cnt"]
    return {
        "sales_invoices_blank_with_master_terms": int(sales_blank or 0),
        "purchase_invoices_blank_with_master_terms": int(purchase_blank or 0),
    }


def apply_fy2526_invoice_terms_alignment_wave() -> dict[str, Any]:
    result: dict[str, Any] = {
        "before": audit_fy2526_invoice_terms_alignment(),
        "sales_updated": 0,
        "purchase_updated": 0,
        "sales_examples": [],
        "purchase_examples": [],
    }

    sales_rows = frappe.db.sql(
        """
        select si.name, si.customer, c.payment_terms
        from `tabSales Invoice` si
        inner join `tabCustomer` c on c.name = si.customer
        where si.docstatus = 1
          and si.posting_date between '2025-04-01' and '2026-03-31'
          and ifnull(si.payment_terms_template, '') = ''
          and ifnull(c.payment_terms, '') != ''
        order by si.posting_date asc, si.name asc
        """,
        as_dict=True,
    )
    for row in sales_rows:
        frappe.db.set_value(
            "Sales Invoice",
            row.name,
            "payment_terms_template",
            row.payment_terms,
            update_modified=False,
        )
        result["sales_updated"] += 1
        if len(result["sales_examples"]) < 15:
            result["sales_examples"].append(
                {
                    "sales_invoice": row.name,
                    "customer": row.customer,
                    "payment_terms_template": row.payment_terms,
                }
            )

    purchase_rows = frappe.db.sql(
        """
        select pi.name, pi.supplier, s.payment_terms
        from `tabPurchase Invoice` pi
        inner join `tabSupplier` s on s.name = pi.supplier
        where pi.docstatus = 1
          and pi.posting_date between '2025-04-01' and '2026-03-31'
          and ifnull(pi.payment_terms_template, '') = ''
          and ifnull(s.payment_terms, '') != ''
        order by pi.posting_date asc, pi.name asc
        """,
        as_dict=True,
    )
    for row in purchase_rows:
        frappe.db.set_value(
            "Purchase Invoice",
            row.name,
            "payment_terms_template",
            row.payment_terms,
            update_modified=False,
        )
        result["purchase_updated"] += 1
        if len(result["purchase_examples"]) < 15:
            result["purchase_examples"].append(
                {
                    "purchase_invoice": row.name,
                    "supplier": row.supplier,
                    "payment_terms_template": row.payment_terms,
                }
            )

    frappe.db.commit()
    result["after"] = audit_fy2526_invoice_terms_alignment()
    return result


def apply_fy2526_finance_control_normalization_wave() -> dict[str, Any]:
    ar_specs = [
        {"invoice": "ACC-SINV-2026-00745", "posting_date": "2026-03-18", "amount": 4800000},
        {"invoice": "ACC-SINV-2026-00614", "posting_date": "2026-03-18", "amount": 4800000},
        {"invoice": "ACC-SINV-2026-00734", "posting_date": "2026-03-19", "amount": 3000000},
        {"invoice": "ACC-SINV-2026-00615", "posting_date": "2026-03-19", "amount": 3500000},
        {"invoice": "ACC-SINV-2026-00737", "posting_date": "2026-03-20", "amount": 3500000},
        {"invoice": "ACC-SINV-2026-00732", "posting_date": "2026-03-20", "amount": 3000000},
        {"invoice": "ACC-SINV-2026-00741", "posting_date": "2026-03-21", "amount": 3300000},
        {"invoice": "ACC-SINV-2026-00633", "posting_date": "2026-03-21", "amount": 2700000},
        {"invoice": "ACC-SINV-2026-00736", "posting_date": "2026-03-22", "amount": 3200000},
        {"invoice": "ACC-SINV-2026-00763", "posting_date": "2026-03-22", "amount": 2500000},
        {"invoice": "ACC-SINV-2026-00650", "posting_date": "2026-03-24", "amount": 2800000},
        {"invoice": "ACC-SINV-2026-00731", "posting_date": "2026-03-24", "amount": 3000000},
        {"invoice": "ACC-SINV-2026-00643", "posting_date": "2026-03-25", "amount": 3200000},
        {"invoice": "ACC-SINV-2026-00759", "posting_date": "2026-03-25", "amount": 3000000},
        {"invoice": "ACC-SINV-2026-00738", "posting_date": "2026-03-26", "amount": 2500000},
        {"invoice": "ACC-SINV-2026-00743", "posting_date": "2026-03-26", "amount": 3000000},
        {"invoice": "ACC-SINV-2026-00642", "posting_date": "2026-03-27", "amount": 2500000},
    ]
    ap_specs = [
        {"invoice": "ACC-PINV-2026-00272", "posting_date": "2026-03-18", "amount": 8000000},
        {"invoice": "ACC-PINV-2026-00327", "posting_date": "2026-03-19", "amount": 8000000},
        {"invoice": "ACC-PINV-2026-00289", "posting_date": "2026-03-20", "amount": 6000000},
        {"invoice": "ACC-PINV-2026-00325", "posting_date": "2026-03-21", "amount": 6000000},
        {"invoice": "ACC-PINV-2026-00319", "posting_date": "2026-03-21", "amount": 5500000},
        {"invoice": "ACC-PINV-2026-00018", "posting_date": "2026-03-24", "amount": 5000000},
        {"invoice": "ACC-PINV-2026-00326", "posting_date": "2026-03-25", "amount": 4500000},
        {"invoice": "ACC-PINV-2026-00015", "posting_date": "2026-03-26", "amount": 3500000},
        {"invoice": "ACC-PINV-2026-00033", "posting_date": "2026-03-27", "amount": 3000000},
    ]
    result: dict[str, Any] = {
        "before_terms": audit_fy2526_invoice_terms_alignment(),
        "before_aging": audit_fy2526_ar_ap_aging_buckets(),
        "before_financials": summarize_fy2526_financial_statements_enterprise_view(),
        "customer_receipts": [],
        "supplier_payments": [],
        "failed": [],
    }

    terms_alignment = apply_fy2526_invoice_terms_alignment_wave()
    result["terms_alignment"] = {
        "sales_updated": terms_alignment.get("sales_updated", 0),
        "purchase_updated": terms_alignment.get("purchase_updated", 0),
        "after": terms_alignment.get("after", {}),
    }

    for spec in ar_specs:
        try:
            payment_info = _apply_targeted_partial_payment_with_date_dedupe(
                "Sales Invoice",
                spec["invoice"],
                spec["posting_date"],
                spec["amount"],
            )
            frappe.db.commit()
            if payment_info:
                result["customer_receipts"].append(payment_info)
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": f"ar_{spec['invoice']}", "error": str(exc)})

    for spec in ap_specs:
        try:
            payment_info = _apply_targeted_partial_payment_with_date_dedupe(
                "Purchase Invoice",
                spec["invoice"],
                spec["posting_date"],
                spec["amount"],
            )
            frappe.db.commit()
            if payment_info:
                result["supplier_payments"].append(payment_info)
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": f"ap_{spec['invoice']}", "error": str(exc)})

    result["customer_receipt_total"] = round(
        sum(float(row.get("amount") or 0) for row in result["customer_receipts"]),
        2,
    )
    result["supplier_payment_total"] = round(
        sum(float(row.get("amount") or 0) for row in result["supplier_payments"]),
        2,
    )
    result["after_aging"] = audit_fy2526_ar_ap_aging_buckets()
    result["after_financials"] = summarize_fy2526_financial_statements_enterprise_view()
    return result


def apply_fy2526_finance_control_residue_wave() -> dict[str, Any]:
    ar_specs = [
        {"invoice": "ACC-SINV-2026-00755", "posting_date": "2026-03-27", "amount": 2500000},
        {"invoice": "ACC-SINV-2026-00762", "posting_date": "2026-03-27", "amount": 2500000},
        {"invoice": "ACC-SINV-2026-00760", "posting_date": "2026-03-28", "amount": 2500000},
        {"invoice": "ACC-SINV-2026-00761", "posting_date": "2026-03-28", "amount": 2500000},
        {"invoice": "ACC-SINV-2026-00764", "posting_date": "2026-03-28", "amount": 2000000},
        {"invoice": "ACC-SINV-2026-00645", "posting_date": "2026-03-29", "amount": 2000000},
        {"invoice": "ACC-SINV-2026-00640", "posting_date": "2026-03-29", "amount": 2000000},
        {"invoice": "ACC-SINV-2026-00763", "posting_date": "2026-03-29", "amount": 1800000},
        {"invoice": "ACC-SINV-2026-00741", "posting_date": "2026-03-30", "amount": 2000000},
        {"invoice": "ACC-SINV-2026-00649", "posting_date": "2026-03-30", "amount": 2000000},
        {"invoice": "ACC-SINV-2026-00074", "posting_date": "2026-03-30", "amount": 2315000},
        {"invoice": "ACC-SINV-2026-00170", "posting_date": "2026-03-30", "amount": 1069000},
        {"invoice": "ACC-SINV-2026-00040", "posting_date": "2026-03-30", "amount": 1127000},
        {"invoice": "ACC-SINV-2026-00125", "posting_date": "2026-03-30", "amount": 1169000},
        {"invoice": "ACC-SINV-2026-00029", "posting_date": "2026-03-31", "amount": 428000},
        {"invoice": "ACC-SINV-2026-00137", "posting_date": "2026-03-31", "amount": 428000},
        {"invoice": "ACC-SINV-2026-00046", "posting_date": "2026-03-31", "amount": 946000},
        {"invoice": "ACC-SINV-2026-00159", "posting_date": "2026-03-31", "amount": 941000},
        {"invoice": "ACC-SINV-2026-00122", "posting_date": "2026-03-31", "amount": 957500},
        {"invoice": "ACC-SINV-2026-00143", "posting_date": "2026-03-31", "amount": 861500},
        {"invoice": "ACC-SINV-2026-00148", "posting_date": "2026-03-31", "amount": 229500},
        {"invoice": "ACC-SINV-2026-00048", "posting_date": "2026-03-31", "amount": 193000},
        {"invoice": "ACC-SINV-2026-00166", "posting_date": "2026-03-31", "amount": 939000},
        {"invoice": "ACC-SINV-2026-00126", "posting_date": "2026-03-31", "amount": 205000},
        {"invoice": "ACC-SINV-2026-00086", "posting_date": "2026-03-31", "amount": 2295000},
        {"invoice": "ACC-SINV-2026-00070", "posting_date": "2026-03-31", "amount": 971500},
        {"invoice": "ACC-SINV-2026-00127", "posting_date": "2026-03-31", "amount": 986000},
    ]
    ap_specs = [
        {"invoice": "ACC-PINV-2026-00011", "posting_date": "2026-03-28", "amount": 3000000},
        {"invoice": "ACC-PINV-2026-00017", "posting_date": "2026-03-28", "amount": 5000000},
        {"invoice": "ACC-PINV-2026-00324", "posting_date": "2026-03-29", "amount": 4000000},
        {"invoice": "ACC-PINV-2026-00318", "posting_date": "2026-03-29", "amount": 3000000},
        {"invoice": "ACC-PINV-2026-00273", "posting_date": "2026-03-29", "amount": 4000000},
        {"invoice": "ACC-PINV-2026-00325", "posting_date": "2026-03-30", "amount": 3000000},
        {"invoice": "ACC-PINV-2026-00319", "posting_date": "2026-03-30", "amount": 2500000},
        {"invoice": "ACC-PINV-2026-00272", "posting_date": "2026-03-30", "amount": 4000000},
        {"invoice": "ACC-PINV-2026-00035", "posting_date": "2026-03-31", "amount": 3000000},
        {"invoice": "ACC-PINV-2026-00320", "posting_date": "2026-03-31", "amount": 2000000},
        {"invoice": "ACC-PINV-2026-00018", "posting_date": "2026-03-31", "amount": 2000000},
        {"invoice": "ACC-PINV-2026-00015", "posting_date": "2026-03-31", "amount": 1500000},
    ]
    result: dict[str, Any] = {
        "before_aging": audit_fy2526_ar_ap_aging_buckets(),
        "before_financials": summarize_fy2526_financial_statements_enterprise_view(),
        "customer_receipts": [],
        "supplier_payments": [],
        "failed": [],
    }

    for spec in ar_specs:
        try:
            payment_info = _apply_targeted_partial_payment_with_date_dedupe(
                "Sales Invoice",
                spec["invoice"],
                spec["posting_date"],
                spec["amount"],
            )
            frappe.db.commit()
            if payment_info:
                result["customer_receipts"].append(payment_info)
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": f"ar_{spec['invoice']}", "error": str(exc)})

    for spec in ap_specs:
        try:
            payment_info = _apply_targeted_partial_payment_with_date_dedupe(
                "Purchase Invoice",
                spec["invoice"],
                spec["posting_date"],
                spec["amount"],
            )
            frappe.db.commit()
            if payment_info:
                result["supplier_payments"].append(payment_info)
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": f"ap_{spec['invoice']}", "error": str(exc)})

    result["customer_receipt_total"] = round(
        sum(float(row.get("amount") or 0) for row in result["customer_receipts"]),
        2,
    )
    result["supplier_payment_total"] = round(
        sum(float(row.get("amount") or 0) for row in result["supplier_payments"]),
        2,
    )
    result["after_aging"] = audit_fy2526_ar_ap_aging_buckets()
    result["after_financials"] = summarize_fy2526_financial_statements_enterprise_view()
    return result


def apply_fy2526_finance_control_convergence_wave(
    target_ratio: float = 0.175,
) -> dict[str, Any]:
    def _bucket_total(rows: list[dict[str, Any]]) -> float:
        return round(sum(float(row.get("total") or 0) for row in rows), 2)

    def _bucket_value(rows: list[dict[str, Any]], bucket: str) -> float:
        for row in rows:
            if str(row.get("bucket") or "") == bucket:
                return float(row.get("total") or 0)
        return 0.0

    def _ratio(rows: list[dict[str, Any]]) -> float:
        total = _bucket_total(rows)
        if total <= 0:
            return 0.0
        return round(_bucket_value(rows, "121+") / total, 4)

    def _ar_candidates() -> list[dict[str, Any]]:
        return frappe.db.sql(
            """
            select si.name, si.customer, si.posting_date, si.outstanding_amount,
                   datediff('2026-03-31', si.posting_date) as age_days,
                   ifnull(si.payment_terms_template, '') as payment_terms_template
            from `tabSales Invoice` si
            where si.docstatus = 1
              and si.outstanding_amount > 0
              and datediff('2026-03-31', si.posting_date) > 120
            order by
              case
                when ifnull(si.payment_terms_template, '') in (
                    'Immediate / Counter Cash - MMOB',
                    'Cash on Delivery - MMOB',
                    '7 Days - MMOB'
                ) then 0
                when ifnull(si.payment_terms_template, '') in (
                    '15 Days - MMOB',
                    '30 Days - MMOB',
                    '45 Days Approved - MMOB'
                ) then 1
                else 2
              end asc,
              datediff('2026-03-31', si.posting_date) desc,
              si.outstanding_amount desc,
              si.name asc
            """,
            as_dict=True,
        )

    def _ap_candidates() -> list[dict[str, Any]]:
        return frappe.db.sql(
            """
            select pi.name, pi.supplier, pi.posting_date, pi.outstanding_amount,
                   datediff('2026-03-31', pi.posting_date) as age_days,
                   ifnull(pi.payment_terms_template, '') as payment_terms_template
            from `tabPurchase Invoice` pi
            where pi.docstatus = 1
              and pi.outstanding_amount > 0
              and datediff('2026-03-31', pi.posting_date) > 120
            order by
              case
                when ifnull(pi.payment_terms_template, '') in (
                    'Cash on Delivery - MMOB',
                    '15 Days - MMOB'
                ) then 0
                when ifnull(pi.payment_terms_template, '') in (
                    '30 Days - MMOB',
                    '45 Days Approved - MMOB'
                ) then 1
                else 2
              end asc,
              datediff('2026-03-31', pi.posting_date) desc,
              pi.outstanding_amount desc,
              pi.name asc
            """,
            as_dict=True,
        )

    before_aging = audit_fy2526_ar_ap_aging_buckets()
    result: dict[str, Any] = {
        "target_ratio": target_ratio,
        "before_aging": before_aging,
        "before_financials": summarize_fy2526_financial_statements_enterprise_view(),
        "customer_receipts": [],
        "supplier_payments": [],
        "failed": [],
    }

    ar_rows = before_aging.get("ar") or []
    ap_rows = before_aging.get("ap") or []
    ar_ratio = _ratio(ar_rows)
    ap_ratio = _ratio(ap_rows)
    ar_posting_dates = ["2026-03-27", "2026-03-28", "2026-03-29", "2026-03-30", "2026-03-31"]
    ap_posting_dates = ["2026-03-28", "2026-03-29", "2026-03-30", "2026-03-31"]

    if ar_ratio > target_ratio:
        for index, row in enumerate(_ar_candidates()):
            current = audit_fy2526_ar_ap_aging_buckets()
            ar_ratio = _ratio((current.get("ar") or []))
            if ar_ratio <= target_ratio:
                break
            try:
                payment_info = _apply_targeted_partial_payment_with_date_dedupe(
                    "Sales Invoice",
                    row.name,
                    ar_posting_dates[index % len(ar_posting_dates)],
                    float(row.outstanding_amount or 0),
                )
                frappe.db.commit()
                if payment_info:
                    payment_info["customer"] = row.customer
                    payment_info["age_days"] = int(row.age_days or 0)
                    payment_info["payment_terms_template"] = row.payment_terms_template
                    result["customer_receipts"].append(payment_info)
            except Exception as exc:
                frappe.db.rollback()
                result["failed"].append({"label": f"ar_{row.name}", "error": str(exc)})

    if ap_ratio > target_ratio:
        for index, row in enumerate(_ap_candidates()):
            current = audit_fy2526_ar_ap_aging_buckets()
            ap_ratio = _ratio((current.get("ap") or []))
            if ap_ratio <= target_ratio:
                break
            try:
                payment_info = _apply_targeted_partial_payment_with_date_dedupe(
                    "Purchase Invoice",
                    row.name,
                    ap_posting_dates[index % len(ap_posting_dates)],
                    float(row.outstanding_amount or 0),
                )
                frappe.db.commit()
                if payment_info:
                    payment_info["supplier"] = row.supplier
                    payment_info["age_days"] = int(row.age_days or 0)
                    payment_info["payment_terms_template"] = row.payment_terms_template
                    result["supplier_payments"].append(payment_info)
            except Exception as exc:
                frappe.db.rollback()
                result["failed"].append({"label": f"ap_{row.name}", "error": str(exc)})

    result["customer_receipt_total"] = round(
        sum(float(row.get("amount") or 0) for row in result["customer_receipts"]),
        2,
    )
    result["supplier_payment_total"] = round(
        sum(float(row.get("amount") or 0) for row in result["supplier_payments"]),
        2,
    )
    result["after_aging"] = audit_fy2526_ar_ap_aging_buckets()
    result["after_financials"] = summarize_fy2526_financial_statements_enterprise_view()
    return result


def apply_fy2526_inventory_realism_sweep() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    results: dict[str, Any] = {"reconciliations": [], "skipped": [], "failed": []}

    warehouses = frappe.get_all("Warehouse", filters={"company": company}, pluck="name")
    if not warehouses:
        results["skipped"].append({"reason": "no_company_warehouses"})
        return results

    placeholders = ", ".join(["%s"] * len(warehouses))
    bins = frappe.db.sql(
        f"""
        select item_code, warehouse, actual_qty, valuation_rate
        from `tabBin`
        where warehouse in ({placeholders})
          and actual_qty > 0
        order by actual_qty desc
        limit 6
        """,
        tuple(warehouses),
        as_dict=True,
    )

    if not bins:
        results["skipped"].append({"reason": "no_bins"})
        return results

    for row in bins:
        try:
            adjusted_qty = max(row.actual_qty * 0.94, row.actual_qty - 12)
            adjusted_qty = round(adjusted_qty, 2)
            reconciliation_name = _create_stock_reconciliation(
                company=company,
                item_code=row.item_code,
                warehouse=row.warehouse,
                posting_date="2026-03-31",
                qty=adjusted_qty,
                valuation_rate=row.valuation_rate or 0,
            )
            frappe.db.commit()
            results["reconciliations"].append(
                {
                    "stock_reconciliation": reconciliation_name,
                    "item_code": row.item_code,
                    "warehouse": row.warehouse,
                    "from_qty": row.actual_qty,
                    "to_qty": adjusted_qty,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            results["failed"].append(
                {
                    "item_code": row.item_code,
                    "warehouse": row.warehouse,
                    "error": str(exc),
                }
            )

    return results


def apply_fy2526_ar_ap_inventory_realism_wave() -> dict[str, Any]:
    return {
        "ar_ap": apply_fy2526_ar_ap_aging_normalization_wave(),
        "inventory": apply_fy2526_inventory_realism_sweep(),
    }


def apply_fy2526_capex_financing_realism_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    cash_account = _find_account_by_names(
        [
            "KBZ-001-000123 - KBZ Bank - Current - MMOB",
            "CB-001-000789 - CB Bank - Current - MMOB",
            "AYA-001-000456 - AYA Bank - Current - MMOB",
            "Cash - MMOB",
        ]
    )
    if not cash_account:
        return {"journal_entries": [], "failed": [{"error": "missing_cash_account"}]}

    fixed_asset_account = _find_account_by_names(
        [
            "Capital Equipment - MMOB",
            "Electronic Equipment - MMOB",
            "Office Equipment - MMOB",
            "Furniture and Fixtures - MMOB",
            "Plants and Machineries - MMOB",
            "Software - MMOB",
        ]
    )
    equity_account = _find_account_by_names(
        [
            "Capital Stock - MMOB",
            "Share Capital - MMOB",
            "Owner's Equity - MMOB",
        ]
    )
    dividends_account = _find_account_by_names(
        [
            "Dividends Paid - MMOB",
            "Dividend - MMOB",
        ]
    )

    result = {"journal_entries": [], "failed": []}

    capex_specs = [
        {"posting_date": "2025-04-18", "amount": 20000000},
        {"posting_date": "2025-06-20", "amount": 45000000},
        {"posting_date": "2025-09-15", "amount": 60000000},
        {"posting_date": "2025-11-22", "amount": 35000000},
        {"posting_date": "2026-01-18", "amount": 80000000},
        {"posting_date": "2026-03-20", "amount": 50000000},
    ]

    for spec in capex_specs:
        if not fixed_asset_account:
            result["failed"].append({"error": "missing_fixed_asset_account"})
            break
        user_remark = f"AI-FY2526-CAPEX-{spec['posting_date']}"
        try:
            journal_entry_name = _create_simple_journal_entry(
                {
                    "company": company,
                    "posting_date": spec["posting_date"],
                    "voucher_type": "Journal Entry",
                    "user_remark": user_remark,
                    "accounts": [
                        {
                            "account": fixed_asset_account,
                            "debit_in_account_currency": spec["amount"],
                        },
                        {
                            "account": cash_account,
                            "credit_in_account_currency": spec["amount"],
                        },
                    ],
                }
            )
            frappe.db.commit()
            result["journal_entries"].append(
                {
                    "type": "capex",
                    "journal_entry": journal_entry_name,
                    "amount": spec["amount"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"type": "capex", "error": str(exc)})

    financing_specs = [
        {"posting_date": "2025-10-10", "amount": 120000000},
        {"posting_date": "2026-02-12", "amount": 60000000},
    ]
    for spec in financing_specs:
        if not equity_account:
            result["failed"].append({"error": "missing_equity_account"})
            break
        user_remark = f"AI-FY2526-EQUITY-IN-{spec['posting_date']}"
        try:
            journal_entry_name = _create_simple_journal_entry(
                {
                    "company": company,
                    "posting_date": spec["posting_date"],
                    "voucher_type": "Journal Entry",
                    "user_remark": user_remark,
                    "accounts": [
                        {
                            "account": cash_account,
                            "debit_in_account_currency": spec["amount"],
                        },
                        {
                            "account": equity_account,
                            "credit_in_account_currency": spec["amount"],
                        },
                    ],
                }
            )
            frappe.db.commit()
            result["journal_entries"].append(
                {
                    "type": "equity_injection",
                    "journal_entry": journal_entry_name,
                    "amount": spec["amount"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"type": "equity_injection", "error": str(exc)})

    if dividends_account:
        dividend_specs = [
            {"posting_date": "2025-12-28", "amount": 30000000},
        ]
        for spec in dividend_specs:
            user_remark = f"AI-FY2526-DIVIDEND-{spec['posting_date']}"
            try:
                journal_entry_name = _create_simple_journal_entry(
                    {
                        "company": company,
                        "posting_date": spec["posting_date"],
                        "voucher_type": "Journal Entry",
                        "user_remark": user_remark,
                        "accounts": [
                            {
                                "account": dividends_account,
                                "debit_in_account_currency": spec["amount"],
                            },
                            {
                                "account": cash_account,
                                "credit_in_account_currency": spec["amount"],
                            },
                        ],
                    }
                )
                frappe.db.commit()
                result["journal_entries"].append(
                    {
                        "type": "dividend",
                        "journal_entry": journal_entry_name,
                        "amount": spec["amount"],
                    }
                )
            except Exception as exc:
                frappe.db.rollback()
                result["failed"].append({"type": "dividend", "error": str(exc)})

    return result


def apply_apr_dec_2025_receipt_and_settlement_wave() -> dict[str, Any]:
    customer_receipts = [
        ("ACC-SINV-2026-00609", "2025-10-15", 8000000),
        ("ACC-SINV-2026-00610", "2025-10-20", 6000000),
        ("ACC-SINV-2026-00611", "2025-10-24", 5000000),
        ("ACC-SINV-2026-00617", "2025-10-28", 3000000),
        ("ACC-SINV-2026-00612", "2025-10-30", 2000000),
        ("ACC-SINV-2026-00613", "2025-10-31", 2000000),
        ("ACC-SINV-2026-00149", "2025-11-05", 1500000),
        ("ACC-SINV-2026-00154", "2025-11-07", 1500000),
        ("ACC-SINV-2026-00139", "2025-11-10", 1500000),
        ("ACC-SINV-2026-00141", "2025-11-12", 1500000),
        ("ACC-SINV-2026-00163", "2025-11-15", 1500000),
        ("ACC-SINV-2026-00156", "2025-11-18", 1500000),
        ("ACC-SINV-2026-00041", "2025-11-20", 2000000),
        ("ACC-SINV-2026-00167", "2025-11-22", 1000000),
        ("ACC-SINV-2026-00169", "2025-11-25", 1000000),
        ("ACC-SINV-2026-00155", "2025-11-28", 1000000),
        ("ACC-SINV-2026-00150", "2025-12-05", 1000000),
        ("ACC-SINV-2026-00151", "2025-12-08", 1000000),
        ("ACC-SINV-2026-00623", "2025-12-12", 4000000),
        ("ACC-SINV-2026-00624", "2025-12-14", 1500000),
        ("ACC-SINV-2026-00625", "2025-12-16", 2000000),
        ("ACC-SINV-2026-00626", "2025-12-18", 200000),
    ]

    supplier_settlements = [
        ("ACC-PINV-2026-00271", "2025-10-18", 8000000),
        ("ACC-PINV-2026-00027", "2025-10-25", 8000000),
        ("ACC-PINV-2026-00063", "2025-11-05", 7000000),
        ("ACC-PINV-2026-00020", "2025-11-20", 3000000),
        ("ACC-PINV-2026-00023", "2025-11-26", 3000000),
        ("ACC-PINV-2026-00021", "2025-12-05", 2000000),
        ("ACC-PINV-2026-00022", "2025-12-10", 2000000),
        ("ACC-PINV-2026-00026", "2025-12-12", 3000000),
        ("ACC-PINV-2026-00025", "2025-12-20", 1000000),
    ]

    result = {
        "customer_receipts": [],
        "supplier_payments": [],
    }

    for invoice_name, posting_date, amount in customer_receipts:
        if not frappe.db.exists("Sales Invoice", invoice_name):
            continue
        payment_name = _create_partial_payment("Sales Invoice", invoice_name, posting_date, amount)
        result["customer_receipts"].append(
            {
                "sales_invoice": invoice_name,
                "payment_entry": payment_name,
                "amount": amount,
            }
        )
        frappe.db.commit()

    for invoice_name, posting_date, amount in supplier_settlements:
        if not frappe.db.exists("Purchase Invoice", invoice_name):
            continue
        payment_name = _create_partial_payment("Purchase Invoice", invoice_name, posting_date, amount)
        result["supplier_payments"].append(
            {
                "purchase_invoice": invoice_name,
                "payment_entry": payment_name,
                "amount": amount,
            }
        )
        frappe.db.commit()

    return result


def apply_apr_dec_2025_procurement_control_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    procurement_lanes = [
        {
            "label": "october_sunflower_accessories_replenishment",
            "purchase_order": {
                "supplier": "Sunflower Accessories Co.",
                "company": company,
                "transaction_date": "2025-10-12",
                "schedule_date": "2025-10-15",
                "payment_terms_template": "15 Days - MMOB",
                "set_warehouse": "Yangon Main Warehouse - MMOB",
                "expected_total": 6580000,
                "remarks": "October Yangon accessories replenishment before Thadingyut wholesale push",
                "items": [
                    {
                        "item_code": "ACC-PWB-BAS-20K",
                        "qty": 40,
                        "rate": 72000,
                        "warehouse": "Yangon Main Warehouse - MMOB",
                    },
                    {
                        "item_code": "ACC-CHR-SAM-25W",
                        "qty": 100,
                        "rate": 22000,
                        "warehouse": "Yangon Main Warehouse - MMOB",
                    },
                    {
                        "item_code": "ACC-CHR-XMI-33W",
                        "qty": 75,
                        "rate": 20000,
                        "warehouse": "Yangon Main Warehouse - MMOB",
                    },
                ],
            },
            "purchase_receipt": {
                "supplier": "Sunflower Accessories Co.",
                "posting_date": "2025-10-15",
                "posting_time": "11:20:00",
                "supplier_delivery_note": "SFL-DN-251015-01",
                "remarks": "Sunflower October accessories arrival for fast-moving Yangon wholesale stock",
            },
            "purchase_invoice": {
                "posting_date": "2025-10-16",
                "posting_time": "14:10:00",
                "bill_no": "SFL-INV-2510-118",
                "bill_date": "2025-10-15",
                "due_date": "2025-10-30",
                "remarks": "Sunflower October replenishment invoice / 15-day supplier credit",
            },
        },
        {
            "label": "november_golden_dragon_importer_replenishment",
            "purchase_order": {
                "supplier": "Golden Dragon Trading Co. Ltd.",
                "company": company,
                "transaction_date": "2025-11-08",
                "schedule_date": "2025-11-12",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": "Yangon Main Warehouse - MMOB",
                "expected_total": 20980000,
                "remarks": "November importer replenishment for Yangon handset and charger demand",
                "items": [
                    {
                        "item_code": "SPH-SAM-A15-6/128",
                        "qty": 12,
                        "rate": 805000,
                        "warehouse": "Yangon Main Warehouse - MMOB",
                    },
                    {
                        "item_code": "SPH-XMI-RN13-8/256",
                        "qty": 14,
                        "rate": 710000,
                        "warehouse": "Yangon Main Warehouse - MMOB",
                    },
                    {
                        "item_code": "ACC-CHR-SAM-25W",
                        "qty": 60,
                        "rate": 23000,
                        "warehouse": "Yangon Main Warehouse - MMOB",
                    },
                ],
            },
            "purchase_receipt": {
                "supplier": "Golden Dragon Trading Co. Ltd.",
                "posting_date": "2025-11-12",
                "posting_time": "13:40:00",
                "supplier_delivery_note": "GD-DN-251112-02",
                "remarks": "Golden Dragon November consolidated import arrival for year-end handset demand",
            },
            "purchase_invoice": {
                "posting_date": "2025-11-14",
                "posting_time": "15:00:00",
                "bill_no": "GD-INV-2511-204",
                "bill_date": "2025-11-13",
                "due_date": "2025-12-12",
                "remarks": "Golden Dragon November import supplier invoice / 30-day credit",
            },
            "landed_cost_voucher": {
                "posting_date": "2025-11-15",
                "distribute_charges_based_on": "Amount",
                "taxes": [
                    {
                        "expense_account": "Expenses Included In Valuation - MMOB",
                        "description": "Customs clearance and import handling uplift",
                        "amount": 900000,
                    },
                    {
                        "expense_account": "Expenses Included In Valuation - MMOB",
                        "description": "Yangon inland freight from port consolidation",
                        "amount": 360000,
                    },
                ],
            },
        },
        {
            "label": "december_shwe_taung_branch_support_replenishment",
            "purchase_order": {
                "supplier": "Shwe Taung Electronics Supply",
                "company": company,
                "transaction_date": "2025-12-18",
                "schedule_date": "2025-12-22",
                "payment_terms_template": "30 Days - MMOB",
                "expected_total": 16800000,
                "remarks": "December mixed Yangon and Mandalay branch-support replenishment",
                "items": [
                    {
                        "item_code": "SPH-SAM-A15-6/128",
                        "qty": 8,
                        "rate": 840000,
                        "warehouse": "Mandalay Warehouse - MMOB",
                    },
                    {
                        "item_code": "SPH-APP-IP13-128",
                        "qty": 4,
                        "rate": 1735000,
                        "warehouse": "Yangon Main Warehouse - MMOB",
                    },
                    {
                        "item_code": "ACC-PWB-BAS-20K",
                        "qty": 40,
                        "rate": 78500,
                        "warehouse": "Mandalay Warehouse - MMOB",
                    },
                ],
            },
            "purchase_receipt": {
                "supplier": "Shwe Taung Electronics Supply",
                "posting_date": "2025-12-22",
                "posting_time": "11:50:00",
                "supplier_delivery_note": "STE-DN-251222-01",
                "remarks": "Shwe Taung December branch-support goods arrival for Mandalay and Yangon",
            },
            "purchase_invoice": {
                "posting_date": "2025-12-24",
                "posting_time": "16:10:00",
                "bill_no": "STE-INV-2512-087",
                "bill_date": "2025-12-23",
                "due_date": "2026-01-23",
                "remarks": "Shwe Taung December replenishment invoice / 30-day supplier credit",
            },
        },
    ]

    result = {
        "lanes": [],
        "failed": [],
    }

    for lane in procurement_lanes:
        try:
            po_name = _create_purchase_order(lane["purchase_order"])
            pr_name = _create_purchase_receipt_from_order(po_name, lane["purchase_receipt"])
            pi_name = _create_purchase_invoice_from_receipt(
                pr_name,
                lane["purchase_order"]["supplier"],
                lane["purchase_order"].get("payment_terms_template"),
                lane["purchase_invoice"],
            )

            lane_result = {
                "label": lane["label"],
                "purchase_order": po_name,
                "purchase_receipt": pr_name,
                "purchase_invoice": pi_name,
            }

            if lane.get("landed_cost_voucher"):
                lcv_spec = dict(lane["landed_cost_voucher"])
                lcv_spec["company"] = company
                lcv_spec["purchase_receipt"] = pr_name
                lane_result["landed_cost_voucher"] = _create_landed_cost_voucher(lcv_spec)

            frappe.db.commit()
            result["lanes"].append(lane_result)
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": lane["label"],
                    "error": str(exc),
                }
            )

    return result


def apply_apr_dec_2025_payroll_settlement_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    settlement_specs = [
        {
            "label": "april_payroll_settlement",
            "posting_date": "2025-05-06",
            "amount": 16150000,
            "bank_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
            "user_remark": "AI-HIST-JV-2025-FY2526-PAYROLL-B2 | AI-FY2526-PAYROLL-APR-REPAY | Replacement bank settlement of April payroll payable after earlier ledger cancellation",
        },
        {
            "label": "may_payroll_settlement",
            "posting_date": "2025-06-06",
            "amount": 16996000,
            "bank_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
            "user_remark": "AI-HIST-JV-2025-FY2526-PAYROLL-B2 | AI-FY2526-PAYROLL-MAY-REPAY | Replacement bank settlement of May payroll payable after earlier ledger cancellation",
        },
        {
            "label": "june_payroll_settlement",
            "posting_date": "2025-07-06",
            "amount": 17000000,
            "bank_account": "CB-001-000789 - CB Bank - Current - MMOB",
            "user_remark": "AI-HIST-JV-2025-FY2526-PAYROLL-B2 | AI-FY2526-PAYROLL-JUN-REPAY | Replacement bank settlement of June payroll payable after earlier ledger cancellation",
        },
        {
            "label": "july_payroll_settlement",
            "posting_date": "2025-08-06",
            "amount": 17000000,
            "bank_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
            "user_remark": "AI-HIST-JV-2025-FY2526-PAYROLL-B2 | AI-FY2526-PAYROLL-JUL-REPAY | Replacement bank settlement of July payroll payable after earlier ledger cancellation",
        },
        {
            "label": "august_payroll_settlement",
            "posting_date": "2025-09-05",
            "amount": 17625000,
            "bank_account": "AYA-001-000456 - AYA Bank - Current - MMOB",
            "user_remark": "AI-HIST-JV-2025-FY2526-PAYROLL-B2 | AI-FY2526-PAYROLL-AUG-SETTLE | Monthly bank settlement of August payroll payable",
        },
        {
            "label": "september_payroll_settlement",
            "posting_date": "2025-10-06",
            "amount": 18000000,
            "bank_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
            "user_remark": "AI-HIST-JV-2025-FY2526-PAYROLL-B2 | AI-FY2526-PAYROLL-SEP-SETTLE | Monthly bank settlement of September payroll payable",
        },
        {
            "label": "october_payroll_settlement",
            "posting_date": "2025-11-05",
            "amount": 19190000,
            "bank_account": "AYA-001-000456 - AYA Bank - Current - MMOB",
            "user_remark": "AI-HIST-JV-2025-FY2526-PAYROLL-B2 | AI-FY2526-PAYROLL-OCT-SETTLE | Monthly bank settlement of October payroll payable",
        },
        {
            "label": "november_payroll_settlement",
            "posting_date": "2025-12-06",
            "amount": 19150000,
            "bank_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
            "user_remark": "AI-HIST-JV-2025-FY2526-PAYROLL-B2 | AI-FY2526-PAYROLL-NOV-SETTLE | Monthly bank settlement of November payroll payable",
        },
    ]

    result = {
        "journal_entries": [],
        "failed": [],
    }

    for spec in settlement_specs:
        try:
            journal_entry_name = _create_simple_journal_entry(
                {
                    "company": company,
                    "posting_date": spec["posting_date"],
                    "voucher_type": "Journal Entry",
                    "user_remark": spec["user_remark"],
                    "accounts": [
                        {
                            "account": "Payroll Payable - MMOB",
                            "debit_in_account_currency": spec["amount"],
                        },
                        {
                            "account": spec["bank_account"],
                            "credit_in_account_currency": spec["amount"],
                        },
                    ],
                }
            )
            frappe.db.commit()
            result["journal_entries"].append(
                {
                    "label": spec["label"],
                    "journal_entry": journal_entry_name,
                    "amount": spec["amount"],
                    "bank_account": spec["bank_account"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": spec["label"],
                    "error": str(exc),
                }
            )

    return result


def _fy2526_payroll_settlement_specs() -> list[dict[str, Any]]:
    return [
        {
            "month_key": "2025-04",
            "posting_date": "2025-05-06",
            "bank_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
        },
        {
            "month_key": "2025-05",
            "posting_date": "2025-06-06",
            "bank_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
        },
        {
            "month_key": "2025-06",
            "posting_date": "2025-07-06",
            "bank_account": "CB-001-000789 - CB Bank - Current - MMOB",
        },
        {
            "month_key": "2025-07",
            "posting_date": "2025-08-06",
            "bank_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
        },
        {
            "month_key": "2025-08",
            "posting_date": "2025-09-05",
            "bank_account": "AYA-001-000456 - AYA Bank - Current - MMOB",
        },
        {
            "month_key": "2025-09",
            "posting_date": "2025-10-06",
            "bank_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
        },
        {
            "month_key": "2025-10",
            "posting_date": "2025-11-05",
            "bank_account": "AYA-001-000456 - AYA Bank - Current - MMOB",
        },
        {
            "month_key": "2025-11",
            "posting_date": "2025-12-06",
            "bank_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
        },
        {
            "month_key": "2025-12",
            "posting_date": "2026-01-06",
            "bank_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
        },
        {
            "month_key": "2026-01",
            "posting_date": "2026-02-06",
            "bank_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
        },
        {
            "month_key": "2026-02",
            "posting_date": "2026-03-06",
            "bank_account": "CB-001-000789 - CB Bank - Current - MMOB",
        },
    ]


def _list_stale_fy2526_payroll_journal_entries() -> list[dict[str, Any]]:
    return frappe.db.sql(
        """
        select name, posting_date, docstatus, user_remark
        from `tabJournal Entry`
        where docstatus = 1
          and (
            user_remark like 'AI-HIST-JV-2025-FY2526-PAYROLL-%'
            or user_remark = 'October 2025 payroll accrual top-up to align submitted salary slips with monthly salary expense baseline.'
            or user_remark = 'November 2025 payroll accrual top-up to align submitted salary slips with monthly salary expense baseline.'
            or user_remark = 'December 2025 payroll accrual top-up to align submitted salary slips with monthly salary expense baseline.'
          )
        order by posting_date, name
        """,
        as_dict=True,
    )


def _list_orphaned_payroll_cancellation_gl_entries() -> list[dict[str, Any]]:
    return frappe.db.sql(
        """
        select gle.voucher_no,
               gle.posting_date,
               gle.account,
               gle.name,
               gle.remarks,
               gle.is_cancelled,
               round(gle.debit_in_account_currency - gle.credit_in_account_currency, 2) as net
        from `tabGL Entry` gle
        left join `tabJournal Entry` je on je.name = gle.voucher_no
        where gle.company = 'Mingalar Mobile Distribution Co., Ltd.'
          and gle.voucher_type = 'Journal Entry'
          and gle.voucher_no in (
            'ACC-JV-2026-00114',
            'ACC-JV-2026-00116',
            'ACC-JV-2026-00118',
            'ACC-JV-2026-00120'
          )
          and ifnull(gle.is_cancelled, 0) = 1
          and je.name is null
        order by gle.posting_date, gle.voucher_no, gle.account, gle.name
        """,
        as_dict=True,
    )


def audit_fy2526_payroll_accounting_posture() -> dict[str, Any]:
    slip_rows = frappe.db.sql(
        """
        select date_format(posting_date, '%Y-%m') as month_key,
               round(sum(gross_pay), 2) as gross_pay,
               round(sum(net_pay), 2) as slip_net,
               count(*) as slip_count
        from `tabSalary Slip`
        where docstatus = 1
          and posting_date between '2025-04-01' and '2026-03-31'
        group by month_key
        order by month_key
        """,
        as_dict=True,
    )
    salary_rows = frappe.db.sql(
        """
        select date_format(posting_date, '%Y-%m') as month_key,
               round(sum(debit_in_account_currency - credit_in_account_currency), 2) as salary_gl_net
        from `tabGL Entry`
        where company = 'Mingalar Mobile Distribution Co., Ltd.'
          and account = 'Salary - MMOB'
          and posting_date between '2025-04-01' and '2026-03-31'
          and ifnull(is_cancelled, 0) = 0
          and voucher_type != 'Period Closing Voucher'
        group by month_key
        order by month_key
        """,
        as_dict=True,
    )
    payroll_payable_rows = frappe.db.sql(
        """
        select date_format(posting_date, '%Y-%m') as month_key,
               round(sum(debit_in_account_currency - credit_in_account_currency), 2) as payroll_payable_gl_net
        from `tabGL Entry`
        where company = 'Mingalar Mobile Distribution Co., Ltd.'
          and account = 'Payroll Payable - MMOB'
          and posting_date between '2025-04-01' and '2026-03-31'
          and ifnull(is_cancelled, 0) = 0
          and voucher_type != 'Period Closing Voucher'
        group by month_key
        order by month_key
        """,
        as_dict=True,
    )
    stale_rows = _list_stale_fy2526_payroll_journal_entries()
    orphaned_gl_rows = _list_orphaned_payroll_cancellation_gl_entries()
    payroll_payable_balance = frappe.db.sql(
        """
        select round(sum(debit_in_account_currency - credit_in_account_currency), 2) as balance
        from `tabGL Entry`
        where company = 'Mingalar Mobile Distribution Co., Ltd.'
          and account = 'Payroll Payable - MMOB'
          and posting_date <= '2026-03-31'
          and ifnull(is_cancelled, 0) = 0
        """,
        as_dict=True,
    )

    gross_map = {row["month_key"]: float(row.get("gross_pay") or 0) for row in slip_rows}
    slip_map = {row["month_key"]: float(row.get("slip_net") or 0) for row in slip_rows}
    count_map = {row["month_key"]: int(row.get("slip_count") or 0) for row in slip_rows}
    salary_map = {row["month_key"]: float(row.get("salary_gl_net") or 0) for row in salary_rows}
    payable_map = {
        row["month_key"]: float(row.get("payroll_payable_gl_net") or 0) for row in payroll_payable_rows
    }

    month_keys = sorted(set(slip_map) | set(gross_map) | set(salary_map) | set(payable_map))
    monthly_summary = []
    for month_key in month_keys:
        slip_net = slip_map.get(month_key, 0)
        gross_pay = gross_map.get(month_key, 0)
        salary_gl_net = salary_map.get(month_key, 0)
        monthly_summary.append(
            {
                "month_key": month_key,
                "slip_count": count_map.get(month_key, 0),
                "gross_pay": gross_pay,
                "slip_net": slip_net,
                "salary_gl_net": salary_gl_net,
                "payroll_payable_gl_net": payable_map.get(month_key, 0),
                "salary_variance_vs_gross": round(salary_gl_net - gross_pay, 2),
                "salary_variance_vs_slips": round(salary_gl_net - slip_net, 2),
            }
        )

    return {
        "status": "ok",
        "monthly_summary": monthly_summary,
        "totals": {
            "gross_pay": round(sum(gross_map.values()), 2),
            "slip_net": round(sum(slip_map.values()), 2),
            "salary_gl_net": round(sum(salary_map.values()), 2),
            "salary_variance_vs_gross": round(sum(salary_map.values()) - sum(gross_map.values()), 2),
            "salary_variance_vs_slips": round(sum(salary_map.values()) - sum(slip_map.values()), 2),
            "stale_payroll_journal_entry_count": len(stale_rows),
            "orphaned_payroll_gl_entry_count": len(orphaned_gl_rows),
            "payroll_payable_balance_to_fy_end": float((payroll_payable_balance[0]["balance"] or 0) if payroll_payable_balance else 0),
        },
        "stale_payroll_journal_entries": [
            {
                "name": row["name"],
                "posting_date": str(row["posting_date"]),
                "user_remark": row["user_remark"],
            }
            for row in stale_rows
        ],
        "orphaned_payroll_gl_entries": [
            {
                "name": row["name"],
                "voucher_no": row["voucher_no"],
                "posting_date": str(row["posting_date"]),
                "account": row["account"],
                "net": float(row.get("net") or 0),
                "remarks": row["remarks"],
            }
            for row in orphaned_gl_rows
        ],
    }


def audit_fy2526_salary_expense_sources() -> dict[str, Any]:
    rows = frappe.db.sql(
        """
        select
            gle.voucher_type,
            gle.voucher_no,
            gle.posting_date,
            round(sum(gle.debit_in_account_currency - gle.credit_in_account_currency), 2) as amount,
            max(ifnull(gle.remarks, '')) as remarks
        from `tabGL Entry` gle
        where gle.company = 'Mingalar Mobile Distribution Co., Ltd.'
          and gle.account = 'Salary - MMOB'
          and gle.posting_date between '2025-04-01' and '2026-03-31'
        group by gle.voucher_type, gle.voucher_no, gle.posting_date
        having abs(amount) > 0.005
        order by gle.posting_date asc, gle.voucher_no asc
        """,
        as_dict=True,
    )
    return {"status": "ok", "rows": rows}


def apply_fy2526_salary_misclassification_reclass_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    cost_center = _company_cost_center(company)
    target_account = _find_account_by_names(
        ["Administrative Expenses - MMOB", "Office Expenses - MMOB", "General Expenses - MMOB"]
    )
    if not target_account:
        return {"journal_entries": [], "failed": [{"error": "missing_administrative_expense_account"}]}

    sources = audit_fy2526_salary_expense_sources().get("rows") or []
    result: dict[str, Any] = {"journal_entries": [], "failed": []}

    for row in sources:
        voucher_no = str(row.get("voucher_no") or "")
        remarks = str(row.get("remarks") or "")
        if not voucher_no.startswith("ACC-JV-2026-000"):
            continue
        if "operating expenses" not in remarks.lower():
            continue
        amount = float(row.get("amount") or 0)
        if amount <= 0:
            continue

        user_remark = (
            f"AI-FY2526-SALARY-RECLASS-{voucher_no} | "
            f"Reclass operating-expense misposting from Salary to Administrative Expenses for {voucher_no}"
        )
        try:
            journal_entry_name = _create_simple_journal_entry(
                {
                    "company": company,
                    "posting_date": str(row.get("posting_date")),
                    "voucher_type": "Journal Entry",
                    "user_remark": user_remark,
                    "accounts": [
                        {
                            "account": target_account,
                            "debit_in_account_currency": amount,
                            "cost_center": cost_center,
                        },
                        {
                            "account": "Salary - MMOB",
                            "credit_in_account_currency": amount,
                            "cost_center": cost_center,
                        },
                    ],
                }
            )
            frappe.db.commit()
            result["journal_entries"].append(
                {
                    "source_voucher": voucher_no,
                    "journal_entry": journal_entry_name,
                    "amount": amount,
                    "posting_date": str(row.get("posting_date")),
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"source_voucher": voucher_no, "error": str(exc)})

    return result


def apply_fy2526_payroll_accounting_normalization() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    result: dict[str, Any] = {
        "cancelled_stale_entries": [],
        "created_settlements": [],
        "deleted_orphaned_gl_entries": [],
        "failed": [],
        "before": audit_fy2526_payroll_accounting_posture(),
        "after": None,
    }

    stale_rows = _list_stale_fy2526_payroll_journal_entries()
    for row in stale_rows:
        try:
            doc = frappe.get_doc("Journal Entry", row["name"])
            if doc.docstatus == 1:
                doc.cancel()
                frappe.db.commit()
            result["cancelled_stale_entries"].append(
                {
                    "name": row["name"],
                    "posting_date": str(row["posting_date"]),
                    "user_remark": row["user_remark"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "stage": "cancel_stale_payroll_entries",
                    "name": row["name"],
                    "error": str(exc),
                }
            )

    if result["failed"]:
        result["after"] = audit_fy2526_payroll_accounting_posture()
        return result

    for spec in _fy2526_payroll_settlement_specs():
        month_start = f"{spec['month_key']}-01"
        month_end = str(get_last_day(month_start))
        payroll_rows = frappe.db.sql(
            """
            select sum(net_pay) as net_pay
            from `tabSalary Slip`
            where docstatus = 1
              and posting_date between %s and %s
            """,
            (month_start, month_end),
            as_dict=True,
        )
        rounded_amount = int(round(float((payroll_rows[0]["net_pay"] or 0) if payroll_rows else 0) / 1000.0) * 1000)
        if rounded_amount <= 0:
            continue

        user_remark = (
            f"AI-FY2526-PAYROLL-SETTLEMENT-{spec['month_key']} | "
            f"Monthly bank settlement of {spec['month_key']} payroll payable"
        )
        try:
            journal_entry_name = _create_simple_journal_entry(
                {
                    "company": company,
                    "posting_date": spec["posting_date"],
                    "voucher_type": "Journal Entry",
                    "user_remark": user_remark,
                    "accounts": [
                        {
                            "account": "Payroll Payable - MMOB",
                            "debit_in_account_currency": rounded_amount,
                        },
                        {
                            "account": spec["bank_account"],
                            "credit_in_account_currency": rounded_amount,
                        },
                    ],
                }
            )
            frappe.db.commit()
            result["created_settlements"].append(
                {
                    "month_key": spec["month_key"],
                    "journal_entry": journal_entry_name,
                    "amount": rounded_amount,
                    "posting_date": spec["posting_date"],
                    "bank_account": spec["bank_account"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "stage": "create_clean_payroll_settlement_entries",
                    "month_key": spec["month_key"],
                    "error": str(exc),
                }
            )

    orphaned_gl_rows = _list_orphaned_payroll_cancellation_gl_entries()
    for row in orphaned_gl_rows:
        try:
            frappe.db.delete("GL Entry", {"name": row["name"]})
            frappe.db.commit()
            result["deleted_orphaned_gl_entries"].append(
                {
                    "name": row["name"],
                    "voucher_no": row["voucher_no"],
                    "posting_date": str(row["posting_date"]),
                    "account": row["account"],
                    "net": float(row.get("net") or 0),
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "stage": "delete_orphaned_payroll_gl_entries",
                    "name": row["name"],
                    "voucher_no": row["voucher_no"],
                    "error": str(exc),
                }
            )

    if result["failed"]:
        result["after"] = audit_fy2526_payroll_accounting_posture()
        return result

    result["after"] = audit_fy2526_payroll_accounting_posture()
    return result


def apply_apr_dec_2025_treasury_rebalancing_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    transfer_specs = [
        {
            "label": "cb_bank_cash_deposit_support",
            "posting_date": "2025-07-04",
            "amount": 6000000,
            "debit_account": "CB-001-000789 - CB Bank - Current - MMOB",
            "credit_account": "Cash - MMOB",
            "user_remark": "AI-HIST-JV-2025-FY2526-TREASURY-B1 | AI-FY2526-TREASURY-CB-DEPOSIT | Cash deposit into CB bank before payroll and supplier outflows",
        },
        {
            "label": "kbz_bank_cash_deposit_support",
            "posting_date": "2025-10-03",
            "amount": 12000000,
            "debit_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
            "credit_account": "Cash - MMOB",
            "user_remark": "AI-HIST-JV-2025-FY2526-TREASURY-B1 | AI-FY2526-TREASURY-KBZ-DEPOSIT | Cash deposit into KBZ bank after wholesale collections and before dense October payouts",
        },
    ]

    result = {
        "journal_entries": [],
        "failed": [],
    }

    for spec in transfer_specs:
        try:
            journal_entry_name = _create_simple_journal_entry(
                {
                    "company": company,
                    "posting_date": spec["posting_date"],
                    "voucher_type": "Journal Entry",
                    "user_remark": spec["user_remark"],
                    "accounts": [
                        {
                            "account": spec["debit_account"],
                            "debit_in_account_currency": spec["amount"],
                        },
                        {
                            "account": spec["credit_account"],
                            "credit_in_account_currency": spec["amount"],
                        },
                    ],
                }
            )
            frappe.db.commit()
            result["journal_entries"].append(
                {
                    "label": spec["label"],
                    "journal_entry": journal_entry_name,
                    "amount": spec["amount"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": spec["label"],
                    "error": str(exc),
                }
            )

    return result


def apply_fy2526_working_capital_support_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    support_specs = [
        {
            "label": "may_cash_working_capital_support",
            "posting_date": "2025-05-31",
            "amount": 2900000,
            "debit_account": "Cash - MMOB",
            "credit_account": "Unsecured Loans - MMOB",
            "user_remark": "AI-FY2526-TREASURY-WC-2025-05-31-CASH | Owner working-capital support to keep petty cash non-negative after early-year operating and supplier cash outflows",
        },
        {
            "label": "july_cash_working_capital_support",
            "posting_date": "2025-07-31",
            "amount": 10000000,
            "debit_account": "Cash - MMOB",
            "credit_account": "Unsecured Loans - MMOB",
            "user_remark": "AI-FY2526-TREASURY-WC-2025-07-31-CASH | Owner working-capital support to stabilize petty cash during monsoon-season treasury pressure",
        },
        {
            "label": "july_cb_working_capital_support",
            "posting_date": "2025-07-31",
            "amount": 10000000,
            "debit_account": "CB-001-000789 - CB Bank - Current - MMOB",
            "credit_account": "Unsecured Loans - MMOB",
            "user_remark": "AI-FY2526-TREASURY-WC-2025-07-31-CB | Short-term owner funding placed into CB account to avoid negative bank balance during payroll and supplier settlement window",
        },
        {
            "label": "august_cash_working_capital_support",
            "posting_date": "2025-08-31",
            "amount": 8000000,
            "debit_account": "Cash - MMOB",
            "credit_account": "Unsecured Loans - MMOB",
            "user_remark": "AI-FY2526-TREASURY-WC-2025-08-31-CASH | Additional owner working-capital support after dense August cash collections lag behind supplier and opex timing",
        },
        {
            "label": "october_cash_working_capital_support",
            "posting_date": "2025-10-31",
            "amount": 15000000,
            "debit_account": "Cash - MMOB",
            "credit_account": "Unsecured Loans - MMOB",
            "user_remark": "AI-FY2526-TREASURY-WC-2025-10-31-CASH | Additional owner working-capital support ahead of dense festival-season expenses and collections timing gap",
        },
        {
            "label": "october_cb_working_capital_support",
            "posting_date": "2025-10-31",
            "amount": 2000000,
            "debit_account": "CB-001-000789 - CB Bank - Current - MMOB",
            "credit_account": "Unsecured Loans - MMOB",
            "user_remark": "AI-FY2526-TREASURY-WC-2025-10-31-CB | Supplemental CB bank top-up to keep operating account slightly positive through month-end close",
        },
        {
            "label": "december_cb_working_capital_support",
            "posting_date": "2025-12-31",
            "amount": 1000000,
            "debit_account": "CB-001-000789 - CB Bank - Current - MMOB",
            "credit_account": "Unsecured Loans - MMOB",
            "user_remark": "AI-FY2526-TREASURY-WC-2025-12-31-CB | Small year-end CB bank top-up so short-term operating bank remains non-negative before January close",
        },
    ]

    result = {"journal_entries": [], "failed": []}

    for spec in support_specs:
        try:
            journal_entry_name = _create_simple_journal_entry(
                {
                    "company": company,
                    "posting_date": spec["posting_date"],
                    "voucher_type": "Journal Entry",
                    "user_remark": spec["user_remark"],
                    "accounts": [
                        {
                            "account": spec["debit_account"],
                            "debit_in_account_currency": spec["amount"],
                        },
                        {
                            "account": spec["credit_account"],
                            "credit_in_account_currency": spec["amount"],
                        },
                    ],
                }
            )
            frappe.db.commit()
            result["journal_entries"].append(
                {
                    "label": spec["label"],
                    "journal_entry": journal_entry_name,
                    "amount": spec["amount"],
                    "debit_account": spec["debit_account"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "error": str(exc)})

    return result


def rebuild_fy2526_kbz_overdraft_timeline() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    legacy_january_remark = (
        "AI-FY2526-TREASURY-2026-01-31-KBZ-OD | Recognize KBZ working-capital "
        "overdraft draw for January inventory and capex pressure"
    )

    result = {
        "cancelled_legacy": None,
        "journal_entries": [],
        "failed": [],
    }

    legacy_name = frappe.db.get_value(
        "Journal Entry",
        {"user_remark": legacy_january_remark},
        "name",
    )
    if legacy_name:
        legacy_docstatus = frappe.db.get_value("Journal Entry", legacy_name, "docstatus")
        if legacy_docstatus == 1:
            try:
                legacy_doc = frappe.get_doc("Journal Entry", legacy_name)
                legacy_doc.cancel()
                frappe.db.commit()
                result["cancelled_legacy"] = legacy_name
            except Exception as exc:
                frappe.db.rollback()
                result["failed"].append({"label": "cancel_legacy_january_kbz_od", "error": str(exc)})
                return result
        else:
            result["cancelled_legacy"] = legacy_name

    entry_specs = [
        {
            "label": "june_month_end_kbz_overdraft_draw",
            "posting_date": "2025-06-30",
            "amount": 50000000,
            "debit_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
            "credit_account": "Bank Overdraft Account - MMOB",
            "user_remark": "AI-FY2526-TREASURY-KBZ-OD-2025-06-30 | Month-end KBZ overdraft draw to cover June capex and payroll pressure while keeping operating bank slightly positive",
        },
        {
            "label": "july_month_end_kbz_overdraft_draw",
            "posting_date": "2025-07-31",
            "amount": 2000000,
            "debit_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
            "credit_account": "Bank Overdraft Account - MMOB",
            "user_remark": "AI-FY2526-TREASURY-KBZ-OD-2025-07-31 | Small additional month-end KBZ overdraft draw during monsoon-season collections slowdown",
        },
        {
            "label": "august_month_end_kbz_overdraft_draw",
            "posting_date": "2025-08-31",
            "amount": 35000000,
            "debit_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
            "credit_account": "Bank Overdraft Account - MMOB",
            "user_remark": "AI-FY2526-TREASURY-KBZ-OD-2025-08-31 | Month-end KBZ overdraft draw after August supplier settlements outpace wholesale collections",
        },
        {
            "label": "september_month_end_kbz_overdraft_draw",
            "posting_date": "2025-09-30",
            "amount": 56000000,
            "debit_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
            "credit_account": "Bank Overdraft Account - MMOB",
            "user_remark": "AI-FY2526-TREASURY-KBZ-OD-2025-09-30 | Month-end KBZ overdraft draw to bridge September inventory buildup and capex timing gap",
        },
        {
            "label": "october_month_end_kbz_overdraft_repayment",
            "posting_date": "2025-10-31",
            "amount": 112000000,
            "debit_account": "Bank Overdraft Account - MMOB",
            "credit_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
            "user_remark": "AI-FY2526-TREASURY-KBZ-OD-2025-10-31-REPAY | Partial KBZ overdraft repayment after stronger October collections and owner capital support",
        },
        {
            "label": "november_month_end_kbz_overdraft_draw",
            "posting_date": "2025-11-30",
            "amount": 33000000,
            "debit_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
            "credit_account": "Bank Overdraft Account - MMOB",
            "user_remark": "AI-FY2526-TREASURY-KBZ-OD-2025-11-30 | Month-end KBZ overdraft draw after renewed November stock and operating pressure",
        },
        {
            "label": "december_month_end_kbz_overdraft_draw",
            "posting_date": "2025-12-31",
            "amount": 47000000,
            "debit_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
            "credit_account": "Bank Overdraft Account - MMOB",
            "user_remark": "AI-FY2526-TREASURY-KBZ-OD-2025-12-31 | Year-end KBZ overdraft draw to keep the operating bank positive going into January trading and payroll cycle",
        },
        {
            "label": "january_month_end_kbz_overdraft_draw",
            "posting_date": "2026-01-31",
            "amount": 87000000,
            "debit_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
            "credit_account": "Bank Overdraft Account - MMOB",
            "user_remark": "AI-FY2526-TREASURY-KBZ-OD-2026-01-31 | Month-end KBZ overdraft draw to keep the operating bank marginally positive after January capex and supplier settlements",
        },
    ]

    for spec in entry_specs:
        try:
            journal_entry_name = _create_simple_journal_entry(
                {
                    "company": company,
                    "posting_date": spec["posting_date"],
                    "voucher_type": "Journal Entry",
                    "user_remark": spec["user_remark"],
                    "accounts": [
                        {
                            "account": spec["debit_account"],
                            "debit_in_account_currency": spec["amount"],
                        },
                        {
                            "account": spec["credit_account"],
                            "credit_in_account_currency": spec["amount"],
                        },
                    ],
                }
            )
            frappe.db.commit()
            result["journal_entries"].append(
                {
                    "label": spec["label"],
                    "journal_entry": journal_entry_name,
                    "amount": spec["amount"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "error": str(exc)})

    return result


def apply_feb_mar_2026_kbz_refinance_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    entry_specs = [
        {
            "label": "feb_term_loan_refinance_repayment",
            "posting_date": "2026-02-01",
            "amount": 100000000,
            "debit_account": "Bank Overdraft Account - MMOB",
            "credit_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
            "user_remark": "AI-FY2526-TREASURY-KBZ-REFI-2026-02-01 | Use KBZ term-loan proceeds to refinance a major portion of the short-term overdraft balance",
        },
        {
            "label": "feb_equity_support_overdraft_repayment",
            "posting_date": "2026-02-12",
            "amount": 20000000,
            "debit_account": "Bank Overdraft Account - MMOB",
            "credit_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
            "user_remark": "AI-FY2526-TREASURY-KBZ-REFI-2026-02-12 | Apply part of February owner capital support to reduce the remaining KBZ overdraft exposure",
        },
        {
            "label": "march_capex_overdraft_redraw",
            "posting_date": "2026-03-20",
            "amount": 40000000,
            "debit_account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
            "credit_account": "Bank Overdraft Account - MMOB",
            "user_remark": "AI-FY2526-TREASURY-KBZ-REFI-2026-03-20 | Draw back part of the KBZ overdraft facility after March capex and supplier settlements tighten cash",
        },
    ]

    result = {"journal_entries": [], "failed": []}

    for spec in entry_specs:
        try:
            journal_entry_name = _create_simple_journal_entry(
                {
                    "company": company,
                    "posting_date": spec["posting_date"],
                    "voucher_type": "Journal Entry",
                    "user_remark": spec["user_remark"],
                    "accounts": [
                        {
                            "account": spec["debit_account"],
                            "debit_in_account_currency": spec["amount"],
                        },
                        {
                            "account": spec["credit_account"],
                            "credit_in_account_currency": spec["amount"],
                        },
                    ],
                }
            )
            frappe.db.commit()
            result["journal_entries"].append(
                {
                    "label": spec["label"],
                    "journal_entry": journal_entry_name,
                    "amount": spec["amount"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "error": str(exc)})

    return result


def apply_fy2526_kbz_term_loan_realism_normalization() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    result: dict[str, Any] = {
        "before": summarize_fy2526_financial_statements_enterprise_view(),
        "cancelled_legacy": [],
        "journal_entries": [],
        "failed": [],
    }

    # Keep the original 100M disbursement, but normalize the later schedule so
    # the year-end principal lands on a clean MMK amount and interest is rounded.
    legacy_names = [
        "ACC-JV-2026-00008",
        "ACC-JV-2026-00007",
        "ACC-JV-2026-00006",
        "ACC-JV-2026-00005",
    ]
    for name in legacy_names:
        try:
            if _cancel_submitted_doc("Journal Entry", name):
                frappe.db.commit()
                result["cancelled_legacy"].append(name)
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"stage": "cancel_legacy", "journal_entry": name, "error": str(exc)})
            return result

    entry_specs = [
        {
            "label": "february_interest_accrual",
            "posting_date": "2026-02-28",
            "voucher_type": "Journal Entry",
            "user_remark": (
                "AI-FY2526-LOAN-KBZ-TERM-2026-02-28-ACCR | "
                "Monthly KBZ term-loan interest accrual rounded for MMK realism."
            ),
            "accounts": [
                {
                    "account": "Interest Expense - Bank Loan - MMOB",
                    "debit_in_account_currency": 1000000,
                },
                {
                    "account": "Interest Payable - Bank Loan - MMOB",
                    "credit_in_account_currency": 1000000,
                },
            ],
        },
        {
            "label": "february_loan_repayment",
            "posting_date": "2026-02-28",
            "voucher_type": "Journal Entry",
            "user_remark": (
                "AI-FY2526-LOAN-KBZ-TERM-2026-02-28-PAY | "
                "First rounded KBZ term-loan installment: 5M principal plus 1M interest settlement."
            ),
            "accounts": [
                {
                    "account": "Interest Payable - Bank Loan - MMOB",
                    "debit_in_account_currency": 1000000,
                },
                {
                    "account": "Bank Loan - KBZ - MMOB",
                    "debit_in_account_currency": 5000000,
                },
                {
                    "account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
                    "credit_in_account_currency": 6000000,
                },
            ],
        },
        {
            "label": "march_interest_accrual",
            "posting_date": "2026-03-31",
            "voucher_type": "Journal Entry",
            "user_remark": (
                "AI-FY2526-LOAN-KBZ-TERM-2026-03-31-ACCR | "
                "Month-end KBZ term-loan interest accrual rounded for MMK realism."
            ),
            "accounts": [
                {
                    "account": "Interest Expense - Bank Loan - MMOB",
                    "debit_in_account_currency": 900000,
                },
                {
                    "account": "Interest Payable - Bank Loan - MMOB",
                    "credit_in_account_currency": 900000,
                },
            ],
        },
        {
            "label": "march_loan_repayment",
            "posting_date": "2026-03-31",
            "voucher_type": "Journal Entry",
            "user_remark": (
                "AI-FY2526-LOAN-KBZ-TERM-2026-03-31-PAY | "
                "Second rounded KBZ term-loan installment: 5M principal plus 0.9M interest settlement."
            ),
            "accounts": [
                {
                    "account": "Interest Payable - Bank Loan - MMOB",
                    "debit_in_account_currency": 900000,
                },
                {
                    "account": "Bank Loan - KBZ - MMOB",
                    "debit_in_account_currency": 5000000,
                },
                {
                    "account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
                    "credit_in_account_currency": 5900000,
                },
            ],
        },
    ]

    for spec in entry_specs:
        try:
            journal_entry_name = _create_simple_journal_entry(
                {
                    "company": company,
                    "posting_date": spec["posting_date"],
                    "voucher_type": spec["voucher_type"],
                    "user_remark": spec["user_remark"],
                    "accounts": spec["accounts"],
                }
            )
            frappe.db.commit()
            result["journal_entries"].append(
                {
                    "label": spec["label"],
                    "journal_entry": journal_entry_name,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"stage": "create_normalized_entry", "label": spec["label"], "error": str(exc)})

    loan_rows = frappe.db.sql(
        """
        select round(sum(debit_in_account_currency - credit_in_account_currency), 2) as balance
        from `tabGL Entry`
        where company = %s
          and account = %s
          and posting_date <= %s
          and ifnull(is_cancelled, 0) = 0
        """,
        (company, "Bank Loan - KBZ - MMOB", "2026-03-31"),
        as_dict=True,
    )
    interest_rows = frappe.db.sql(
        """
        select round(sum(debit_in_account_currency - credit_in_account_currency), 2) as amount
        from `tabGL Entry`
        where company = %s
          and account = %s
          and posting_date between %s and %s
          and ifnull(is_cancelled, 0) = 0
        """,
        (company, "Interest Expense - Bank Loan - MMOB", "2025-04-01", "2026-03-31"),
        as_dict=True,
    )
    result["after"] = summarize_fy2526_financial_statements_enterprise_view()
    result["loan_balance_to_fy_end"] = abs(float((loan_rows[0]["balance"] or 0) if loan_rows else 0))
    result["interest_expense_fy"] = float((interest_rows[0]["amount"] or 0) if interest_rows else 0)
    return result


def apply_fy2526_period_close_to_retained_earnings() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    fiscal_year = "2025-2026"
    result: dict[str, Any] = {
        "before": summarize_fy2526_financial_statements_enterprise_view(),
        "existing_submitted": [],
        "drafts_found": [],
        "period_closing_voucher": None,
        "failed": [],
    }

    submitted = frappe.get_all(
        "Period Closing Voucher",
        filters={"company": company, "fiscal_year": fiscal_year, "docstatus": 1},
        fields=["name", "transaction_date", "gle_processing_status"],
        order_by="transaction_date desc, creation desc",
    )
    if submitted:
        result["existing_submitted"] = submitted
        result["after"] = summarize_fy2526_financial_statements_enterprise_view()
        return result

    drafts = frappe.get_all(
        "Period Closing Voucher",
        filters={"company": company, "fiscal_year": fiscal_year, "docstatus": 0},
        fields=["name", "transaction_date", "gle_processing_status"],
        order_by="transaction_date desc, creation desc",
    )
    result["drafts_found"] = drafts

    try:
        doc = frappe.get_doc(
            {
                "doctype": "Period Closing Voucher",
                "transaction_date": "2026-03-31",
                "company": company,
                "fiscal_year": fiscal_year,
                "period_start_date": "2025-04-01",
                "period_end_date": "2026-03-31",
                "closing_account_head": "Retained Earnings - MMOB",
                "remarks": (
                    "FY2025-2026 retained-earnings close to remove provisional "
                    "current-year profit from the balance-sheet presentation."
                ),
            }
        )
        doc.insert(ignore_permissions=True)
        doc.submit()
        frappe.db.commit()
        result["period_closing_voucher"] = {
            "name": doc.name,
            "transaction_date": str(doc.transaction_date),
            "gle_processing_status": doc.gle_processing_status,
        }
    except Exception as exc:
        frappe.db.rollback()
        result["failed"].append({"stage": "period_close_submit", "error": str(exc)})
        return result

    result["after"] = summarize_fy2526_financial_statements_enterprise_view()
    return result


def apply_fy2526_single_book_finance_book_normalization() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    result: dict[str, Any] = {
        "before": {
            "gl_default_count": frappe.db.sql(
                """
                select count(*)
                from `tabGL Entry`
                where company = %s
                  and ifnull(finance_book, '') = 'Default'
                """,
                (company,),
            )[0][0],
            "asset_finance_book_default_count": frappe.db.sql(
                """
                select count(*)
                from `tabAsset Finance Book`
                where ifnull(finance_book, '') = 'Default'
                """
            )[0][0],
            "asset_schedule_default_count": frappe.db.sql(
                """
                select count(*)
                from `tabAsset Depreciation Schedule`
                where ifnull(finance_book, '') = 'Default'
                """
            )[0][0],
        },
        "updated_assets": [],
        "updated_counts": {},
        "after": {},
    }

    asset_names = [
        row[0]
        for row in frappe.db.sql(
            """
            select parent
            from `tabAsset Finance Book`
            where ifnull(finance_book, '') = 'Default'
            order by parent
            """
        )
    ]
    result["updated_assets"] = asset_names

    if asset_names:
        frappe.db.sql(
            """
            update `tabAsset Finance Book`
            set finance_book = null
            where ifnull(finance_book, '') = 'Default'
            """
        )
        frappe.db.sql(
            """
            update `tabAsset Depreciation Schedule`
            set finance_book = null
            where ifnull(finance_book, '') = 'Default'
            """
        )

    frappe.db.sql(
        """
        update `tabGL Entry`
        set finance_book = null
        where company = %s
          and ifnull(finance_book, '') = 'Default'
        """,
        (company,),
    )
    frappe.db.commit()

    result["updated_counts"] = {
        "gl_default_count": frappe.db.sql(
            """
            select count(*)
            from `tabGL Entry`
            where company = %s
              and ifnull(finance_book, '') = 'Default'
            """,
            (company,),
        )[0][0],
        "asset_finance_book_default_count": frappe.db.sql(
            """
            select count(*)
            from `tabAsset Finance Book`
            where ifnull(finance_book, '') = 'Default'
            """
        )[0][0],
        "asset_schedule_default_count": frappe.db.sql(
            """
            select count(*)
            from `tabAsset Depreciation Schedule`
            where ifnull(finance_book, '') = 'Default'
            """
        )[0][0],
    }
    result["after"] = summarize_fy2526_financial_statements_enterprise_view()
    return result


def apply_feb_mar_2026_cb_stabilization_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    entry_specs = [
        {
            "label": "february_cb_cash_deposit_support",
            "posting_date": "2026-02-28",
            "amount": 5000000,
            "debit_account": "CB-001-000789 - CB Bank - Current - MMOB",
            "credit_account": "Cash - MMOB",
            "user_remark": "AI-FY2526-TREASURY-CB-2026-02-28 | Month-end cash deposit into CB account after supplier and market-support outflows exceed direct February receipts",
        },
        {
            "label": "march_cb_cash_deposit_support",
            "posting_date": "2026-03-31",
            "amount": 5000000,
            "debit_account": "CB-001-000789 - CB Bank - Current - MMOB",
            "credit_account": "Cash - MMOB",
            "user_remark": "AI-FY2526-TREASURY-CB-2026-03-31 | Month-end cash deposit into CB account so the operating bank closes slightly positive at fiscal year-end",
        },
    ]

    result = {"journal_entries": [], "failed": []}

    for spec in entry_specs:
        try:
            journal_entry_name = _create_simple_journal_entry(
                {
                    "company": company,
                    "posting_date": spec["posting_date"],
                    "voucher_type": "Journal Entry",
                    "user_remark": spec["user_remark"],
                    "accounts": [
                        {
                            "account": spec["debit_account"],
                            "debit_in_account_currency": spec["amount"],
                        },
                        {
                            "account": spec["credit_account"],
                            "credit_in_account_currency": spec["amount"],
                        },
                    ],
                }
            )
            frappe.db.commit()
            result["journal_entries"].append(
                {
                    "label": spec["label"],
                    "journal_entry": journal_entry_name,
                    "amount": spec["amount"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "error": str(exc)})

    return result


def apply_fy2526_final_realism_tightening_wave() -> dict[str, Any]:
    results: dict[str, Any] = {
        "receivable_payments": [],
        "payable_payments": [],
        "purchase_returns": [],
        "failed": [],
    }

    receivable_specs = [
        {"invoice": "ACC-SINV-2026-00745", "posting_date": "2026-02-18", "amount": 5000000},
        {"invoice": "ACC-SINV-2026-00747", "posting_date": "2026-02-20", "amount": 4000000},
        {"invoice": "ACC-SINV-2026-00753", "posting_date": "2026-03-12", "amount": 3500000},
        {"invoice": "ACC-SINV-2026-00736", "posting_date": "2026-03-15", "amount": 3000000},
        {"invoice": "ACC-SINV-2026-00754", "posting_date": "2026-03-18", "amount": 3000000},
        {"invoice": "ACC-SINV-2026-00758", "posting_date": "2026-03-22", "amount": 3000000},
    ]

    payable_specs = [
        {"invoice": "ACC-PINV-2026-00272", "posting_date": "2026-02-24", "amount": 8000000},
        {"invoice": "ACC-PINV-2026-00324", "posting_date": "2026-02-26", "amount": 7000000},
        {"invoice": "ACC-PINV-2026-00325", "posting_date": "2026-03-05", "amount": 5000000},
        {"invoice": "ACC-PINV-2026-00320", "posting_date": "2026-03-07", "amount": 4000000},
        {"invoice": "ACC-PINV-2026-00318", "posting_date": "2026-03-10", "amount": 4000000},
    ]

    purchase_return_specs = [
        {
            "source_invoice": "ACC-PINV-2026-00307",
            "posting_date": "2026-03-22",
            "remarks": "FY2526 realism partial purchase return for inbound quality variance and customer-pack mismatch.",
            "items": {
                "SPH-SAM-A15-6/128": 3,
                "SPH-XMI-RN13-8/256": 2,
                "ACC-PWB-BAS-20K": 10,
            },
        },
        {
            "source_invoice": "ACC-PINV-2026-00309",
            "posting_date": "2026-03-28",
            "remarks": "FY2526 realism partial purchase return for damaged accessory and memory-card packs discovered during put-away.",
            "items": {
                "ACC-AUD-XMI-BUDS4": 15,
                "MEM-MSD-SND-128": 20,
                "GAD-SPK-JBL-GO3": 2,
            },
        },
    ]

    for spec in receivable_specs:
        try:
            payment_info = _apply_targeted_partial_payment(
                "Sales Invoice",
                spec["invoice"],
                spec["posting_date"],
                spec["amount"],
            )
            if payment_info:
                results["receivable_payments"].append(payment_info)
                frappe.db.commit()
        except Exception as exc:
            frappe.db.rollback()
            results["failed"].append({"label": f"receivable_{spec['invoice']}", "error": str(exc)})

    for spec in payable_specs:
        try:
            payment_info = _apply_targeted_partial_payment(
                "Purchase Invoice",
                spec["invoice"],
                spec["posting_date"],
                spec["amount"],
            )
            if payment_info:
                results["payable_payments"].append(payment_info)
                frappe.db.commit()
        except Exception as exc:
            frappe.db.rollback()
            results["failed"].append({"label": f"payable_{spec['invoice']}", "error": str(exc)})

    for spec in purchase_return_specs:
        try:
            return_name = _create_partial_purchase_return_against_invoice(
                spec["source_invoice"],
                spec["posting_date"],
                spec["remarks"],
                spec["items"],
            )
            frappe.db.commit()
            results["purchase_returns"].append(
                {
                    "source_invoice": spec["source_invoice"],
                    "purchase_return": return_name,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            results["failed"].append({"label": f"purchase_return_{spec['source_invoice']}", "error": str(exc)})

    return results


def apply_mar_2026_procurement_control_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    procurement_lanes = [
        {
            "label": "march_golden_dragon_handset_topup",
            "purchase_order": {
                "supplier": "Golden Dragon Trading Co. Ltd.",
                "company": company,
                "transaction_date": "2026-03-22",
                "schedule_date": "2026-03-24",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": "Yangon Main Warehouse - MMOB",
                "expected_total": 18180000,
                "remarks": "Late-March handset top-up after stronger wholesale take-up ahead of new month turnover.",
                "items": [
                    {
                        "item_code": "SPH-XMI-RN13-8/256",
                        "qty": 12,
                        "rate": 710000,
                        "warehouse": "Yangon Main Warehouse - MMOB",
                    },
                    {
                        "item_code": "SPH-SAM-A15-6/128",
                        "qty": 10,
                        "rate": 790000,
                        "warehouse": "Yangon Main Warehouse - MMOB",
                    },
                    {
                        "item_code": "ACC-CHR-SAM-25W",
                        "qty": 80,
                        "rate": 22000,
                        "warehouse": "Yangon Main Warehouse - MMOB",
                    },
                ],
            },
            "purchase_receipt": {
                "supplier": "Golden Dragon Trading Co. Ltd.",
                "posting_date": "2026-03-24",
                "posting_time": "11:10:00",
                "supplier_delivery_note": "GD-DN-260324-01",
                "remarks": "Golden Dragon late-March replenishment received into Yangon main warehouse.",
            },
            "purchase_invoice": {
                "posting_date": "2026-03-25",
                "posting_time": "14:15:00",
                "bill_no": "GD-INV-2603-318",
                "bill_date": "2026-03-24",
                "due_date": "2026-04-24",
                "remarks": "Golden Dragon late-March handset replenishment invoice / 30-day supplier credit.",
            },
        },
        {
            "label": "march_sunflower_accessories_fast_mover_topup",
            "purchase_order": {
                "supplier": "Sunflower Accessories Co.",
                "company": company,
                "transaction_date": "2026-03-23",
                "schedule_date": "2026-03-26",
                "payment_terms_template": "15 Days - MMOB",
                "set_warehouse": "Yangon Main Warehouse - MMOB",
                "expected_total": 16115000,
                "remarks": "Late-March fast-mover accessories replenishment after strong charger and power-bank sell-through.",
                "items": [
                    {
                        "item_code": "ACC-PWB-BAS-20K",
                        "qty": 120,
                        "rate": 82000,
                        "warehouse": "Yangon Main Warehouse - MMOB",
                    },
                    {
                        "item_code": "ACC-CHR-XMI-33W",
                        "qty": 150,
                        "rate": 20500,
                        "warehouse": "Yangon Main Warehouse - MMOB",
                    },
                    {
                        "item_code": "ACC-AUD-XMI-BUDS4",
                        "qty": 80,
                        "rate": 40000,
                        "warehouse": "Yangon Main Warehouse - MMOB",
                    },
                ],
            },
            "purchase_receipt": {
                "supplier": "Sunflower Accessories Co.",
                "posting_date": "2026-03-26",
                "posting_time": "12:00:00",
                "supplier_delivery_note": "SFL-DN-260326-02",
                "remarks": "Sunflower accessories batch received for Yangon wholesale and counter demand.",
            },
            "purchase_invoice": {
                "posting_date": "2026-03-27",
                "posting_time": "15:10:00",
                "bill_no": "SFL-INV-2603-226",
                "bill_date": "2026-03-26",
                "due_date": "2026-04-10",
                "remarks": "Sunflower March fast-mover accessories invoice / 15-day supplier credit.",
            },
        },
        {
            "label": "march_shwe_taung_mixed_branch_support",
            "purchase_order": {
                "supplier": "Shwe Taung Electronics Supply",
                "company": company,
                "transaction_date": "2026-03-25",
                "schedule_date": "2026-03-29",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": "Mandalay Warehouse - MMOB",
                "expected_total": 12320000,
                "remarks": "Month-end mixed branch-support replenishment for Mandalay warehouse and Yangon spillover demand.",
                "items": [
                    {
                        "item_code": "SPH-OPP-A58-6/128",
                        "qty": 10,
                        "rate": 665000,
                        "warehouse": "Mandalay Warehouse - MMOB",
                    },
                    {
                        "item_code": "SPH-SAM-A05S-6/128",
                        "qty": 8,
                        "rate": 600000,
                        "warehouse": "Mandalay Warehouse - MMOB",
                    },
                    {
                        "item_code": "ACC-CHR-ANK-20W",
                        "qty": 40,
                        "rate": 21000,
                        "warehouse": "Yangon Main Warehouse - MMOB",
                    },
                ],
            },
            "purchase_receipt": {
                "supplier": "Shwe Taung Electronics Supply",
                "posting_date": "2026-03-29",
                "posting_time": "11:45:00",
                "supplier_delivery_note": "STE-DN-260329-01",
                "remarks": "Shwe Taung mixed handset and accessory support batch received for month-end coverage.",
            },
            "purchase_invoice": {
                "posting_date": "2026-03-30",
                "posting_time": "16:05:00",
                "bill_no": "STE-INV-2603-119",
                "bill_date": "2026-03-29",
                "due_date": "2026-04-28",
                "remarks": "Shwe Taung late-March mixed replenishment invoice / 30-day supplier credit.",
            },
        },
    ]

    result = {"lanes": [], "failed": []}

    for lane in procurement_lanes:
        try:
            po_name = _create_purchase_order(lane["purchase_order"])
            pr_name = _create_purchase_receipt_from_order(po_name, lane["purchase_receipt"])
            pi_name = _create_purchase_invoice_from_receipt(
                pr_name,
                lane["purchase_order"]["supplier"],
                lane["purchase_order"].get("payment_terms_template"),
                lane["purchase_invoice"],
            )

            lane_result = {
                "label": lane["label"],
                "purchase_order": po_name,
                "purchase_receipt": pr_name,
                "purchase_invoice": pi_name,
            }

            frappe.db.commit()
            result["lanes"].append(lane_result)
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": lane["label"], "error": str(exc)})

    return result


def _build_fy2526_depreciation_profile(asset_doc, finance_book_row, fy_start: str) -> dict[str, Any] | None:
    available_for_use_date = asset_doc.available_for_use_date or asset_doc.purchase_date
    if not available_for_use_date:
        return None

    frequency = cint(finance_book_row.frequency_of_depreciation or 0)
    total_depreciations = cint(finance_book_row.total_number_of_depreciations or 0)
    if frequency <= 0 or total_depreciations <= 0:
        return None

    first_schedule_date = get_last_day(add_months(getdate(available_for_use_date), frequency))
    schedule_dates = [
        get_last_day(add_months(first_schedule_date, frequency * idx))
        for idx in range(total_depreciations)
    ]
    fy_start_date = getdate(fy_start)
    opening_booked = sum(1 for schedule_date in schedule_dates if getdate(schedule_date) < fy_start_date)
    if opening_booked >= total_depreciations:
        return None

    precision = asset_doc.precision("net_purchase_amount")
    depreciable_amount = flt(
        flt(asset_doc.net_purchase_amount) - flt(finance_book_row.expected_value_after_useful_life or 0),
        precision,
    )
    opening_accumulated_depreciation = flt(
        (depreciable_amount * opening_booked) / total_depreciations,
        precision,
    )
    remaining_value = flt(flt(asset_doc.total_asset_cost or asset_doc.net_purchase_amount) - opening_accumulated_depreciation, precision)

    return {
        "available_for_use_date": str(getdate(available_for_use_date)),
        "first_schedule_date": str(first_schedule_date),
        "target_start_date": str(schedule_dates[opening_booked]),
        "opening_number_of_booked_depreciations": opening_booked,
        "opening_accumulated_depreciation": opening_accumulated_depreciation,
        "remaining_value_after_opening": remaining_value,
        "schedule_dates_in_fy": [
            str(schedule_date)
            for schedule_date in schedule_dates
            if fy_start_date <= getdate(schedule_date) <= getdate("2026-03-31")
        ],
    }


def apply_fy2526_depreciation_model_repair(
    asset_names: list[str] | str | None = None,
    company: str = "Mingalar Mobile Distribution Co., Ltd.",
    fy_start: str = "2025-04-01",
    fy_end: str = "2026-03-31",
    submit_draft_assets: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    from erpnext.assets.doctype.asset.depreciation import make_depreciation_entry
    from erpnext.assets.doctype.asset_depreciation_schedule.asset_depreciation_schedule import (
        get_asset_depr_schedule_doc,
        reschedule_depreciation,
    )

    if isinstance(asset_names, str):
        asset_names = [asset_names]

    asset_filters: dict[str, Any] = {
        "company": company,
        "calculate_depreciation": 1,
        "docstatus": ["in", [0, 1]],
    }
    if asset_names:
        asset_filters["name"] = ["in", asset_names]

    asset_rows = frappe.get_all(
        "Asset",
        filters=asset_filters,
        fields=["name", "purchase_date", "docstatus", "status"],
        order_by="purchase_date asc, name asc",
    )

    results: dict[str, Any] = {
        "processed": [],
        "skipped": [],
        "failed": [],
    }
    note = "FY2025-2026 depreciation model repair: reset opening base to 2025-04-01 and reschedule from realistic commissioning dates."

    for asset_row in asset_rows:
        try:
            asset_doc = frappe.get_doc("Asset", asset_row.name)
            if not asset_doc.get("finance_books"):
                results["skipped"].append(
                    {"asset": asset_doc.name, "reason": "missing_finance_book"}
                )
                continue

            finance_book_row = asset_doc.get("finance_books")[0]
            if finance_book_row.depreciation_method not in ("Straight Line", "", None):
                results["skipped"].append(
                    {
                        "asset": asset_doc.name,
                        "reason": "unsupported_depreciation_method",
                        "depreciation_method": finance_book_row.depreciation_method,
                    }
                )
                continue

            profile = _build_fy2526_depreciation_profile(asset_doc, finance_book_row, fy_start)
            if not profile:
                results["skipped"].append(
                    {
                        "asset": asset_doc.name,
                        "reason": "profile_not_applicable",
                    }
                )
                continue

            before_active_schedule = get_asset_depr_schedule_doc(asset_doc.name, "Active", finance_book_row.finance_book)
            before_draft_schedule = get_asset_depr_schedule_doc(asset_doc.name, "Draft", finance_book_row.finance_book)
            before_posted_entries = 0
            if before_active_schedule:
                before_posted_entries = len(
                    [row for row in before_active_schedule.get("depreciation_schedule") if row.journal_entry]
                )

            summary = {
                "asset": asset_doc.name,
                "asset_name": asset_doc.asset_name,
                "docstatus_before": asset_doc.docstatus,
                "status_before": asset_doc.status,
                "opening_booked_before": cint(asset_doc.opening_number_of_booked_depreciations or 0),
                "opening_booked_after": profile["opening_number_of_booked_depreciations"],
                "opening_accumulated_before": flt(asset_doc.opening_accumulated_depreciation or 0),
                "opening_accumulated_after": profile["opening_accumulated_depreciation"],
                "depreciation_start_before": str(finance_book_row.depreciation_start_date) if finance_book_row.depreciation_start_date else None,
                "depreciation_start_after": profile["target_start_date"],
                "fy_schedule_count": len(profile["schedule_dates_in_fy"]),
                "active_schedule_before": before_active_schedule.name if before_active_schedule else None,
                "draft_schedule_before": before_draft_schedule.name if before_draft_schedule else None,
                "posted_entries_before": before_posted_entries,
            }

            if dry_run:
                results["processed"].append(summary)
                continue

            if before_active_schedule and before_active_schedule.docstatus == 1:
                before_active_schedule.cancel()

            remaining_value = profile["remaining_value_after_opening"]
            asset_doc.db_set(
                "opening_number_of_booked_depreciations",
                profile["opening_number_of_booked_depreciations"],
                update_modified=False,
            )
            asset_doc.db_set(
                "opening_accumulated_depreciation",
                profile["opening_accumulated_depreciation"],
                update_modified=False,
            )
            asset_doc.db_set("next_depreciation_date", profile["target_start_date"], update_modified=False)
            asset_doc.db_set("value_after_depreciation", remaining_value, update_modified=False)
            finance_book_row.db_set("depreciation_start_date", profile["target_start_date"], update_modified=False)
            finance_book_row.db_set("value_after_depreciation", remaining_value, update_modified=False)
            finance_book_row.db_set(
                "total_number_of_booked_depreciations",
                profile["opening_number_of_booked_depreciations"],
                update_modified=False,
            )

            asset_doc.reload()
            if asset_doc.docstatus == 0:
                asset_doc.flags.ignore_validate_update_after_submit = True
                asset_doc.save(ignore_permissions=True)
                if submit_draft_assets:
                    asset_doc.submit()
            else:
                reschedule_depreciation(asset_doc, note)

            asset_doc.reload()
            active_schedule = get_asset_depr_schedule_doc(asset_doc.name, "Active", finance_book_row.finance_book)
            if submit_draft_assets and active_schedule:
                make_depreciation_entry(active_schedule.name, date=fy_end)

            asset_doc.reload()
            asset_doc.set_total_booked_depreciations()
            asset_doc.set_status()
            frappe.db.commit()

            active_schedule = get_asset_depr_schedule_doc(asset_doc.name, "Active", finance_book_row.finance_book)
            posted_entries_after = 0
            if active_schedule:
                posted_entries_after = len(
                    [row for row in active_schedule.get("depreciation_schedule") if row.journal_entry]
                )
            summary.update(
                {
                    "docstatus_after": asset_doc.docstatus,
                    "status_after": asset_doc.status,
                    "active_schedule_after": active_schedule.name if active_schedule else None,
                    "posted_entries_after": posted_entries_after,
                }
            )
            results["processed"].append(summary)
        except Exception as exc:
            frappe.db.rollback()
            results["failed"].append({"asset": asset_row.name, "error": str(exc)})

    return results


def apply_january_2026_treasury_overdraft_normalization_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    entry_specs = [
        {
            "label": "aya_cash_deposit_support",
            "posting_date": "2026-01-31",
            "voucher_type": "Journal Entry",
            "user_remark": "AI-FY2526-TREASURY-2026-01-31-AYA-DEPOSIT | Month-end cash deposit to clear small AYA operating deficit before financial close",
            "accounts": [
                {
                    "account": "AYA-001-000456 - AYA Bank - Current - MMOB",
                    "debit_in_account_currency": 3800000,
                },
                {
                    "account": "Cash - MMOB",
                    "credit_in_account_currency": 3800000,
                },
            ],
        },
        {
            "label": "cb_cash_deposit_support",
            "posting_date": "2026-01-31",
            "voucher_type": "Journal Entry",
            "user_remark": "AI-FY2526-TREASURY-2026-01-31-CB-DEPOSIT | Month-end cash deposit to clear small CB operating deficit before financial close",
            "accounts": [
                {
                    "account": "CB-001-000789 - CB Bank - Current - MMOB",
                    "debit_in_account_currency": 3200000,
                },
                {
                    "account": "Cash - MMOB",
                    "credit_in_account_currency": 3200000,
                },
            ],
        },
        {
            "label": "kbz_overdraft_draw_support",
            "posting_date": "2026-01-31",
            "voucher_type": "Journal Entry",
            "user_remark": "AI-FY2526-TREASURY-2026-01-31-KBZ-OD | Recognize KBZ working-capital overdraft draw for January inventory and capex pressure",
            "accounts": [
                {
                    "account": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
                    "debit_in_account_currency": 88700000,
                },
                {
                    "account": "Bank Overdraft Account - MMOB",
                    "credit_in_account_currency": 88700000,
                },
            ],
        },
    ]

    result = {"journal_entries": [], "failed": []}

    for spec in entry_specs:
        try:
            journal_entry_name = _create_simple_journal_entry(
                {
                    "company": company,
                    "posting_date": spec["posting_date"],
                    "voucher_type": spec["voucher_type"],
                    "user_remark": spec["user_remark"],
                    "accounts": spec["accounts"],
                }
            )
            frappe.db.commit()
            result["journal_entries"].append(
                {
                    "label": spec["label"],
                    "journal_entry": journal_entry_name,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "error": str(exc)})

    return result


def _sum_item_amounts(items: list[dict[str, Any]]) -> int:
    return int(round(sum(float(row["qty"]) * float(row["rate"]) for row in items)))


def _find_submitted_quotation(
    customer: str,
    transaction_date: str,
    expected_total: float | None = None,
) -> str | None:
    matches = frappe.get_all(
        "Quotation",
        filters={
            "party_name": customer,
            "transaction_date": transaction_date,
            "docstatus": 1,
        },
        fields=["name", "grand_total"],
        order_by="creation asc",
    )
    if expected_total is not None:
        for match in matches:
            if int(round(match.grand_total or 0)) == int(round(expected_total)):
                return match.name
    if len(matches) == 1:
        return matches[0].name
    return None


def _target_quotation_workflow_state(status: str | None, docstatus: int = 1) -> str | None:
    if docstatus != 1:
        return None
    if status == "Lost":
        return "Lost"
    if status == "Expired":
        return "Expired"
    return "Approved"


def _sync_quotation_workflow_state(quotation_name: str) -> str | None:
    row = frappe.db.get_value(
        "Quotation",
        quotation_name,
        ["docstatus", "status", "workflow_state"],
        as_dict=True,
    )
    if not row:
        return None

    target_state = _target_quotation_workflow_state(row.status, cint(row.docstatus or 0))
    if target_state and row.workflow_state != target_state:
        frappe.db.set_value(
            "Quotation",
            quotation_name,
            "workflow_state",
            target_state,
            update_modified=False,
        )
    return target_state


def _create_quotation(defn: dict[str, Any]) -> str:
    expected_total = defn.get("expected_total") or _sum_item_amounts(defn["items"])
    existing_name = _find_submitted_quotation(
        defn["customer"],
        defn["transaction_date"],
        expected_total,
    )
    if existing_name:
        return existing_name

    doc = frappe.get_doc(
        {
            "doctype": "Quotation",
            "quotation_to": "Customer",
            "party_name": defn["customer"],
            "company": defn["company"],
            "transaction_date": defn["transaction_date"],
            "valid_till": defn["valid_till"],
            "currency": "MMK",
            "conversion_rate": 1.0,
            "selling_price_list": defn.get("selling_price_list", "Standard Selling"),
            "price_list_currency": "MMK",
            "plc_conversion_rate": 1.0,
            "ignore_default_payment_terms_template": 1,
            "payment_terms_template": defn.get("payment_terms_template"),
            "order_type": defn.get("order_type", "Sales"),
            "set_warehouse": defn.get("set_warehouse"),
            "remarks": defn.get("remarks"),
            "items": [
                {
                    "item_code": item["item_code"],
                    "qty": item["qty"],
                    "warehouse": item.get("warehouse", defn.get("set_warehouse")),
                    "uom": "Nos",
                    "conversion_factor": 1.0,
                    "price_list_rate": item["rate"],
                    "rate": item["rate"],
                }
                for item in defn["items"]
            ],
        }
    )
    doc.insert(ignore_permissions=True)
    doc.submit()
    _sync_quotation_workflow_state(doc.name)
    return doc.name


def normalize_submitted_quotation_workflow_states(
    from_date: str | None = None,
    to_date: str | None = None,
) -> dict[str, Any]:
    filters: dict[str, Any] = {"docstatus": 1}
    if from_date and to_date:
        filters["transaction_date"] = ["between", [from_date, to_date]]
    elif from_date:
        filters["transaction_date"] = [">=", from_date]
    elif to_date:
        filters["transaction_date"] = ["<=", to_date]

    rows = frappe.get_all(
        "Quotation",
        filters=filters,
        fields=["name", "transaction_date", "party_name", "status", "workflow_state"],
        order_by="transaction_date asc, creation asc",
    )

    normalized: list[dict[str, Any]] = []
    unchanged: list[str] = []
    for row in rows:
        target_state = _target_quotation_workflow_state(row.status, 1)
        if not target_state or row.workflow_state == target_state:
            unchanged.append(row.name)
            continue
        frappe.db.set_value(
            "Quotation",
            row.name,
            "workflow_state",
            target_state,
            update_modified=False,
        )
        normalized.append(
            {
                "quotation": row.name,
                "transaction_date": row.transaction_date,
                "customer": row.party_name,
                "status": row.status,
                "from_workflow_state": row.workflow_state,
                "to_workflow_state": target_state,
            }
        )

    frappe.db.commit()
    return {
        "status": "ok",
        "scope": {"from_date": from_date, "to_date": to_date},
        "normalized_count": len(normalized),
        "unchanged_count": len(unchanged),
        "normalized": normalized,
    }


def _find_submitted_sales_order(
    customer: str,
    transaction_date: str,
    po_no: str | None = None,
    expected_total: float | None = None,
) -> str | None:
    filters = {
        "customer": customer,
        "transaction_date": transaction_date,
        "docstatus": 1,
    }
    if po_no:
        filters["po_no"] = po_no
    matches = frappe.get_all(
        "Sales Order",
        filters=filters,
        fields=["name", "grand_total"],
        order_by="creation asc",
    )
    if expected_total is not None:
        for match in matches:
            if int(round(match.grand_total or 0)) == int(round(expected_total)):
                return match.name
    if len(matches) == 1:
        return matches[0].name
    return None


def _create_sales_order(defn: dict[str, Any]) -> str:
    expected_total = defn.get("expected_total") or _sum_item_amounts(defn["items"])
    existing_name = _find_submitted_sales_order(
        defn["customer"],
        defn["transaction_date"],
        defn.get("po_no"),
        expected_total,
    )
    if existing_name:
        return existing_name

    doc = frappe.get_doc(
        {
            "doctype": "Sales Order",
            "customer": defn["customer"],
            "company": defn["company"],
            "transaction_date": defn["transaction_date"],
            "delivery_date": defn["delivery_date"],
            "po_no": defn.get("po_no"),
            "po_date": defn.get("po_date"),
            "currency": "MMK",
            "conversion_rate": 1.0,
            "selling_price_list": defn.get("selling_price_list", "Standard Selling"),
            "price_list_currency": "MMK",
            "plc_conversion_rate": 1.0,
            "ignore_default_payment_terms_template": 1,
            "payment_terms_template": defn.get("payment_terms_template"),
            "set_warehouse": defn.get("set_warehouse"),
            "remarks": defn.get("remarks"),
            "items": [
                {
                    "item_code": item["item_code"],
                    "qty": item["qty"],
                    "warehouse": item.get("warehouse", defn.get("set_warehouse")),
                    "delivery_date": item.get("delivery_date", defn["delivery_date"]),
                    "uom": "Nos",
                    "conversion_factor": 1.0,
                    "price_list_rate": item["rate"],
                    "rate": item["rate"],
                }
                for item in defn["items"]
            ],
        }
    )
    doc.insert(ignore_permissions=True)
    doc.submit()
    return doc.name


def _create_sales_order_from_quotation(quotation_name: str, defn: dict[str, Any]) -> str:
    existing_name = _find_submitted_sales_order(
        defn["customer"],
        defn["transaction_date"],
        defn.get("po_no"),
        defn.get("expected_total"),
    )
    if existing_name:
        return existing_name

    from erpnext.selling.doctype.quotation.quotation import make_sales_order

    order = make_sales_order(quotation_name)
    order.transaction_date = defn["transaction_date"]
    order.delivery_date = defn["delivery_date"]
    order.po_no = defn.get("po_no")
    order.po_date = defn.get("po_date")
    order.set_warehouse = defn.get("set_warehouse")
    order.ignore_default_payment_terms_template = 1
    order.payment_terms_template = defn.get("payment_terms_template")
    order.remarks = defn.get("remarks")
    order.flags.ignore_permissions = True
    order.insert(ignore_permissions=True)
    order.submit()
    return order.name


def _find_submitted_sales_invoice_for_sales_order(
    sales_order_name: str,
    posting_date: str | None = None,
) -> str | None:
    conditions = ["si.docstatus = 1", "sii.sales_order = %(sales_order)s"]
    params: dict[str, Any] = {"sales_order": sales_order_name}
    if posting_date:
        conditions.append("si.posting_date = %(posting_date)s")
        params["posting_date"] = posting_date

    rows = frappe.db.sql(
        f"""
        select distinct si.name, si.grand_total
        from `tabSales Invoice` si
        inner join `tabSales Invoice Item` sii on sii.parent = si.name
        where {" and ".join(conditions)}
        order by si.creation asc
        limit 1
        """,
        params,
        as_dict=True,
    )
    return rows[0]["name"] if rows else None


def _create_stock_sales_invoice_from_sales_order(sales_order_name: str, defn: dict[str, Any]) -> str:
    existing_name = _find_submitted_sales_invoice_for_sales_order(
        sales_order_name,
        defn.get("posting_date"),
    )
    if existing_name:
        return existing_name

    from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice

    sales_invoice = make_sales_invoice(sales_order_name)
    sales_invoice.set_posting_time = 1
    sales_invoice.posting_date = defn["posting_date"]
    sales_invoice.posting_time = defn.get("posting_time", "10:30:00")
    sales_invoice.due_date = defn.get("due_date", defn["posting_date"])
    sales_invoice.ignore_default_payment_terms_template = 1
    sales_invoice.payment_terms_template = defn.get("payment_terms_template")
    sales_invoice.update_stock = 1
    sales_invoice.remarks = defn.get("remarks")
    sales_invoice.flags.ignore_permissions = True
    sales_invoice.insert(ignore_permissions=True)
    sales_invoice.submit()
    return sales_invoice.name


def _find_submitted_delivery_note_for_sales_order(
    sales_order_name: str,
    posting_date: str | None = None,
) -> str | None:
    conditions = ["dn.docstatus = 1", "dni.against_sales_order = %(sales_order)s"]
    params: dict[str, Any] = {"sales_order": sales_order_name}
    if posting_date:
        conditions.append("dn.posting_date = %(posting_date)s")
        params["posting_date"] = posting_date

    rows = frappe.db.sql(
        f"""
        select distinct dn.name
        from `tabDelivery Note` dn
        inner join `tabDelivery Note Item` dni on dni.parent = dn.name
        where {" and ".join(conditions)}
        order by dn.creation asc
        limit 1
        """,
        params,
        as_dict=True,
    )
    return rows[0]["name"] if rows else None


def _create_delivery_note_from_sales_order(sales_order_name: str, defn: dict[str, Any]) -> str:
    existing_name = _find_submitted_delivery_note_for_sales_order(
        sales_order_name,
        defn.get("posting_date"),
    )
    if existing_name:
        return existing_name

    from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note

    delivery_note = make_delivery_note(sales_order_name)
    delivery_note.set_posting_time = 1
    delivery_note.posting_date = defn["posting_date"]
    delivery_note.posting_time = defn.get("posting_time", "10:30:00")
    delivery_note.lr_date = defn.get("lr_date", defn["posting_date"])
    delivery_note.remarks = defn.get("remarks")
    delivery_note.flags.ignore_permissions = True
    delivery_note.insert(ignore_permissions=True)
    delivery_note.submit()
    return delivery_note.name


def _find_submitted_sales_invoice_for_delivery_note(
    delivery_note_name: str,
    posting_date: str | None = None,
) -> str | None:
    conditions = ["si.docstatus = 1", "sii.delivery_note = %(delivery_note)s"]
    params: dict[str, Any] = {"delivery_note": delivery_note_name}
    if posting_date:
        conditions.append("si.posting_date = %(posting_date)s")
        params["posting_date"] = posting_date

    rows = frappe.db.sql(
        f"""
        select distinct si.name
        from `tabSales Invoice` si
        inner join `tabSales Invoice Item` sii on sii.parent = si.name
        where {" and ".join(conditions)}
        order by si.creation asc
        limit 1
        """,
        params,
        as_dict=True,
    )
    return rows[0]["name"] if rows else None


def _create_sales_invoice_from_delivery_note(delivery_note_name: str, defn: dict[str, Any]) -> str:
    existing_name = _find_submitted_sales_invoice_for_delivery_note(
        delivery_note_name,
        defn.get("posting_date"),
    )
    if existing_name:
        return existing_name

    from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice

    sales_invoice = make_sales_invoice(delivery_note_name)
    sales_invoice.set_posting_time = 1
    sales_invoice.posting_date = defn["posting_date"]
    sales_invoice.posting_time = defn.get("posting_time", "11:00:00")
    sales_invoice.due_date = defn["due_date"]
    sales_invoice.ignore_default_payment_terms_template = 1
    sales_invoice.payment_terms_template = defn.get("payment_terms_template")
    sales_invoice.set(
        "payment_schedule",
        [
            {
                "due_date": defn["due_date"],
                "payment_amount": sales_invoice.rounded_total or sales_invoice.grand_total,
            }
        ],
    )
    sales_invoice.remarks = defn.get("remarks")
    sales_invoice.flags.ignore_permissions = True
    sales_invoice.insert(ignore_permissions=True)
    sales_invoice.submit()
    return sales_invoice.name


def _cancel_submitted_doc(doctype: str, name: str) -> bool:
    if not name or not frappe.db.exists(doctype, name):
        return False
    docstatus = frappe.db.get_value(doctype, name, "docstatus")
    if int(docstatus or 0) != 1:
        return False
    doc = frappe.get_doc(doctype, name)
    doc.flags.ignore_permissions = True
    doc.cancel()
    return True


def _collect_payment_rebuild_specs(invoice_name: str) -> list[dict[str, Any]]:
    rows = frappe.db.sql(
        """
        select per.parent as payment_entry,
               pe.posting_date,
               per.allocated_amount
        from `tabPayment Entry Reference` per
        inner join `tabPayment Entry` pe on pe.name = per.parent
        where per.reference_doctype = 'Sales Invoice'
          and per.reference_name = %s
          and pe.docstatus = 1
        order by pe.posting_date asc, pe.creation asc
        """,
        (invoice_name,),
        as_dict=True,
    )
    specs = []
    for row in rows:
        ref_count = frappe.db.count(
            "Payment Entry Reference",
            filters={"parent": row["payment_entry"], "parenttype": "Payment Entry"},
        )
        specs.append(
            {
                "payment_entry": row["payment_entry"],
                "posting_date": str(row["posting_date"]),
                "allocated_amount": float(row["allocated_amount"] or 0),
                "reference_count": int(ref_count or 0),
            }
        )
    return specs


def _collect_linked_return_specs(invoice_name: str) -> list[dict[str, Any]]:
    rows = frappe.get_all(
        "Sales Invoice",
        filters={"return_against": invoice_name, "docstatus": 1, "is_return": 1},
        fields=["name", "posting_date", "posting_time", "due_date", "update_stock", "remarks"],
        order_by="posting_date asc, creation asc",
    )
    specs = []
    for row in rows:
        specs.append(
            {
                "name": row["name"],
                "posting_date": str(row["posting_date"]),
                "posting_time": row.get("posting_time") or "10:00:00",
                "due_date": str(row.get("due_date") or row["posting_date"]),
                "update_stock": int(row.get("update_stock") or 0),
                "remarks": row.get("remarks"),
            }
        )
    return specs


def _recreate_sales_return_against_invoice(invoice_name: str, defn: dict[str, Any]) -> str:
    base_invoice = frappe.get_doc("Sales Invoice", invoice_name)
    return_doc = _make_return_doc("Sales Invoice", invoice_name)
    return_doc.posting_date = defn["posting_date"]
    return_doc.posting_time = defn.get("posting_time", "10:00:00")
    return_doc.set_posting_time = 1
    return_doc.due_date = defn.get("due_date", defn["posting_date"])
    return_doc.update_stock = int(defn.get("update_stock") or 0)
    return_doc.ignore_default_payment_terms_template = 1
    return_doc.payment_terms_template = defn.get("payment_terms_template") or ""
    return_doc.return_against = invoice_name
    return_doc.remarks = defn.get("remarks")
    return_doc.flags.ignore_permissions = True

    # Preserve the original commercial values rather than recalculating from today's defaults.
    original_return = frappe.get_doc("Sales Invoice", defn["source_return_name"])
    rate_map = {}
    for item in original_return.items:
        rate_map[(item.item_code, float(abs(item.qty)))] = {
            "rate": float(abs(item.rate)),
            "warehouse": item.warehouse,
        }
    for item in return_doc.items:
        key = (item.item_code, float(abs(item.qty)))
        if key in rate_map:
            item.rate = rate_map[key]["rate"]
            item.warehouse = rate_map[key]["warehouse"]
        if not item.income_account:
            item.income_account = "Sales - MMOB"
        if not item.expense_account:
            item.expense_account = "Cost of Goods Sold - MMOB"

    return_doc.insert(ignore_permissions=True)
    return_doc.submit()
    return return_doc.name


def _normalize_sales_invoice_to_stock_sales_order_chain(defn: dict[str, Any]) -> dict[str, Any]:
    invoice = frappe.get_doc("Sales Invoice", defn["invoice_name"])
    if invoice.docstatus != 1:
        return {"status": "skipped", "invoice": invoice.name, "reason": f"docstatus_{invoice.docstatus}"}

    if int(invoice.update_stock or 0) == 1:
        return {"status": "already_stock_linked", "invoice": invoice.name}

    payment_specs = _collect_payment_rebuild_specs(invoice.name)
    return_specs = _collect_linked_return_specs(invoice.name)
    for payment in payment_specs:
        if payment["reference_count"] != 1:
            raise frappe.ValidationError(
                f"Payment Entry {payment['payment_entry']} has multiple references; manual review required."
            )

    invoice_item_defs = [
        {
            "item_code": item.item_code,
            "qty": float(item.qty),
            "rate": float(item.rate),
            "warehouse": item.warehouse,
            "delivery_date": defn["sales_order"]["delivery_date"],
        }
        for item in invoice.items
    ]

    expected_total = _sum_item_amounts(invoice_item_defs)

    for payment in payment_specs:
        _cancel_submitted_doc("Payment Entry", payment["payment_entry"])
    frappe.db.commit()

    for return_spec in reversed(return_specs):
        _cancel_submitted_doc("Sales Invoice", return_spec["name"])
    frappe.db.commit()

    _cancel_submitted_doc("Sales Invoice", invoice.name)
    if defn.get("delivery_note_name"):
        _cancel_submitted_doc("Delivery Note", defn["delivery_note_name"])
    if defn.get("normalized_sales_order_name"):
        _cancel_submitted_doc("Sales Order", defn["normalized_sales_order_name"])
    if defn.get("original_sales_order_name"):
        _cancel_submitted_doc("Sales Order", defn["original_sales_order_name"])
    frappe.db.commit()

    sales_order_name = _create_sales_order(
        {
            **defn["sales_order"],
            "customer": invoice.customer,
            "company": invoice.company,
            "payment_terms_template": invoice.payment_terms_template,
            "expected_total": expected_total,
            "items": invoice_item_defs,
        }
    )
    new_invoice_name = _create_stock_sales_invoice_from_sales_order(
        sales_order_name,
        {
            "posting_date": str(invoice.posting_date),
            "posting_time": invoice.posting_time or "10:30:00",
            "due_date": str(invoice.due_date),
            "payment_terms_template": invoice.payment_terms_template,
            "remarks": defn.get("invoice_remarks")
            or f"July 2025 normalization rebuild for historical invoice {invoice.name}.",
        },
    )
    frappe.db.commit()

    recreated_returns = []
    for return_spec in return_specs:
        recreated_return_name = _recreate_sales_return_against_invoice(
            new_invoice_name,
            {
                **return_spec,
                "source_return_name": return_spec["name"],
                "payment_terms_template": "",
            },
        )
        recreated_returns.append(recreated_return_name)
    frappe.db.commit()

    rebuilt_payments = []
    for payment in payment_specs:
        payment_name = _create_partial_payment_with_date_dedupe(
            "Sales Invoice",
            new_invoice_name,
            payment["posting_date"],
            payment["allocated_amount"],
        )
        rebuilt_payments.append(
            {
                "payment_entry": payment_name,
                "posting_date": payment["posting_date"],
                "allocated_amount": payment["allocated_amount"],
            }
        )
    frappe.db.commit()

    return {
        "status": "normalized",
        "old_invoice": invoice.name,
        "new_sales_order": sales_order_name,
        "new_sales_invoice": new_invoice_name,
        "recreated_returns": recreated_returns,
        "rebuilt_payments": rebuilt_payments,
    }


def apply_april_2025_commercial_rebalance_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    warehouse = "Yangon Main Warehouse - MMOB"

    credit_limit_targets = {
        "Bayint Naung Wholesale Mobile": 200000000,
        "35th Street Mobile Wholesale": 110000000,
        "Capital Telecom (NPT)": 150000000,
        "Taunggyi City Mobile": 60000000,
        "Bago Myoma Phone Shop": 10000000,
    }

    procurement_lanes = [
        {
            "label": "april_golden_dragon_handset_replenishment",
            "purchase_order": {
                "supplier": "Golden Dragon Trading Co. Ltd.",
                "company": company,
                "transaction_date": "2025-04-03",
                "schedule_date": "2025-04-05",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "April opening-month handset and charger replenishment for early wholesale trading rhythm.",
                "items": [
                    {"item_code": "SPH-SAM-A15-6/128", "qty": 18, "rate": 840000, "warehouse": warehouse},
                    {"item_code": "SPH-XMI-RN13-8/256", "qty": 16, "rate": 705000, "warehouse": warehouse},
                    {"item_code": "ACC-CHR-XMI-33W", "qty": 100, "rate": 20000, "warehouse": warehouse},
                ],
            },
            "purchase_receipt": {
                "supplier": "Golden Dragon Trading Co. Ltd.",
                "posting_date": "2025-04-05",
                "posting_time": "11:10:00",
                "supplier_delivery_note": "GD-DN-250405-01",
                "remarks": "Golden Dragon April opening-month goods arrival for handset-led wholesale demand.",
            },
            "purchase_invoice": {
                "posting_date": "2025-04-06",
                "posting_time": "15:20:00",
                "bill_no": "GD-INV-2504-041",
                "bill_date": "2025-04-05",
                "due_date": "2025-05-05",
                "remarks": "Golden Dragon April opening-month supplier invoice / normal 30-day credit.",
            },
        },
        {
            "label": "april_sunflower_accessory_replenishment",
            "purchase_order": {
                "supplier": "Sunflower Accessories Co.",
                "company": company,
                "transaction_date": "2025-04-09",
                "schedule_date": "2025-04-10",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "April accessory replenishment for ordinary wholesale bundle selling after opening-week demand.",
                "items": [
                    {"item_code": "SPH-APP-IP13-128", "qty": 6, "rate": 1735000, "warehouse": warehouse},
                    {"item_code": "ACC-PWB-BAS-20K", "qty": 80, "rate": 78000, "warehouse": warehouse},
                    {"item_code": "ACC-CHR-SAM-25W", "qty": 120, "rate": 25000, "warehouse": warehouse},
                    {"item_code": "ACC-CBL-BAS-TC1M", "qty": 150, "rate": 5000, "warehouse": warehouse},
                ],
            },
            "purchase_receipt": {
                "supplier": "Sunflower Accessories Co.",
                "posting_date": "2025-04-10",
                "posting_time": "12:00:00",
                "supplier_delivery_note": "SFL-DN-250410-01",
                "remarks": "Sunflower April accessory arrival supporting bundled handset sales in Yangon.",
            },
            "purchase_invoice": {
                "posting_date": "2025-04-11",
                "posting_time": "16:00:00",
                "bill_no": "SFL-INV-2504-028",
                "bill_date": "2025-04-10",
                "due_date": "2025-05-10",
                "remarks": "Sunflower April opening-month accessory invoice / 30-day supplier credit.",
            },
        },
        {
            "label": "april_handset_buffer_topup",
            "purchase_order": {
                "supplier": "Myanmar Tech Import Services",
                "company": company,
                "transaction_date": "2025-04-12",
                "schedule_date": "2025-04-14",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "April controlled handset top-up to keep Q2-Q3 sell-through from going negative on key smartphone SKUs.",
                "items": [
                    {"item_code": "SPH-XMI-RN13-8/256", "qty": 8, "rate": 705000, "warehouse": warehouse},
                    {"item_code": "SPH-APP-IP13-128", "qty": 4, "rate": 1735000, "warehouse": warehouse},
                ],
            },
            "purchase_receipt": {
                "supplier": "Myanmar Tech Import Services",
                "posting_date": "2025-04-14",
                "posting_time": "11:40:00",
                "supplier_delivery_note": "MTI-DN-250414-01",
                "remarks": "Myanmar Tech April top-up arrival to protect future handset continuity.",
            },
            "purchase_invoice": {
                "posting_date": "2025-04-15",
                "posting_time": "15:10:00",
                "bill_no": "MTI-INV-2504-019",
                "bill_date": "2025-04-14",
                "due_date": "2025-05-14",
                "remarks": "Myanmar Tech April handset top-up invoice / normal 30-day supplier credit.",
            },
        },
    ]

    quotation_specs = [
        {
            "label": "april_bayint_quote",
            "customer": "Bayint Naung Wholesale Mobile",
            "transaction_date": "2025-04-07",
            "valid_till": "2025-04-12",
            "payment_terms_template": "30 Days - MMOB",
            "set_warehouse": warehouse,
            "remarks": "April opening-month Bayint wholesale quotation for mixed handset and accessory replenishment.",
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 6, "rate": 1010000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 6, "rate": 890000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 20, "rate": 108000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 30, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 30, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 40, "rate": 8000},
            ],
        },
        {
            "label": "april_35th_quote",
            "customer": "35th Street Mobile Wholesale",
            "transaction_date": "2025-04-14",
            "valid_till": "2025-04-19",
            "payment_terms_template": "30 Days - MMOB",
            "set_warehouse": warehouse,
            "remarks": "April Mandalay-lane quotation for mixed handset and fast-moving accessory restock.",
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 3, "rate": 2120000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 4, "rate": 1010000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
            ],
        },
        {
            "label": "april_latha_lost_quote",
            "customer": "Latha Mobile Wholesale",
            "transaction_date": "2025-04-11",
            "valid_till": "2025-04-14",
            "payment_terms_template": "30 Days - MMOB",
            "set_warehouse": warehouse,
            "target_status": "Lost",
            "remarks": "April price-sensitive wholesale quotation that did not convert after competitor comparison and margin negotiation.",
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 5, "rate": 1020000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 30, "rate": 8000},
            ],
        },
        {
            "label": "april_hledan_expired_quote",
            "customer": "Hledan Phone Hub",
            "transaction_date": "2025-04-23",
            "valid_till": "2025-04-26",
            "payment_terms_template": "30 Days - MMOB",
            "set_warehouse": warehouse,
            "target_status": "Expired",
            "remarks": "April small wholesale quotation that expired after the customer delayed final confirmation.",
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 15, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
            ],
        },
    ]

    chain_specs = [
        {
            "label": "april_bayint_quote_to_order_chain",
            "customer": "Bayint Naung Wholesale Mobile",
            "quotation_label": "april_bayint_quote",
            "sales_order": {
                "transaction_date": "2025-04-09",
                "delivery_date": "2025-04-11",
                "po_no": "CPO-2025-04-101",
                "po_date": "2025-04-09",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "April Bayint wholesale order converted from approved opening-month quotation.",
            },
            "delivery_note": {
                "posting_date": "2025-04-11",
                "posting_time": "11:20:00",
                "remarks": "April Bayint wholesale dispatch after customer confirmation and stock picking.",
            },
            "sales_invoice": {
                "posting_date": "2025-04-11",
                "posting_time": "11:40:00",
                "due_date": "2025-05-11",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "April Bayint wholesale invoice converted from approved quotation and delivery.",
            },
        },
        {
            "label": "april_35th_quote_to_order_chain",
            "customer": "35th Street Mobile Wholesale",
            "quotation_label": "april_35th_quote",
            "sales_order": {
                "transaction_date": "2025-04-16",
                "delivery_date": "2025-04-18",
                "po_no": "CPO-2025-04-102",
                "po_date": "2025-04-16",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "April Mandalay-lane wholesale order converted from earlier mixed-product quotation.",
            },
            "delivery_note": {
                "posting_date": "2025-04-18",
                "posting_time": "14:00:00",
                "remarks": "April 35th Street mixed handset and accessory dispatch after quotation approval.",
            },
            "sales_invoice": {
                "posting_date": "2025-04-18",
                "posting_time": "14:20:00",
                "due_date": "2025-05-18",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "April 35th Street wholesale invoice converted from approved quotation and dispatch.",
            },
        },
        {
            "label": "april_capital_direct_order_chain",
            "customer": "Capital Telecom (NPT)",
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 2, "rate": 2150000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 4, "rate": 1020000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 15, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
            ],
            "sales_order": {
                "transaction_date": "2025-04-20",
                "delivery_date": "2025-04-22",
                "po_no": "CPO-2025-04-103",
                "po_date": "2025-04-20",
                "payment_terms_template": "45 Days Approved - MMOB",
                "set_warehouse": warehouse,
                "remarks": "April key-account direct wholesale order confirmed by phone and internal credit review.",
            },
            "delivery_note": {
                "posting_date": "2025-04-22",
                "posting_time": "13:10:00",
                "remarks": "April Capital Telecom mixed handset dispatch after internal release confirmation.",
            },
            "sales_invoice": {
                "posting_date": "2025-04-22",
                "posting_time": "13:30:00",
                "due_date": "2025-06-06",
                "payment_terms_template": "45 Days Approved - MMOB",
                "remarks": "April Capital Telecom invoice issued after direct-order dispatch and approval.",
            },
        },
        {
            "label": "april_taunggyi_direct_order_chain",
            "customer": "Taunggyi City Mobile",
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 2, "rate": 2150000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 1020000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 12, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
            ],
            "sales_order": {
                "transaction_date": "2025-04-24",
                "delivery_date": "2025-04-25",
                "po_no": "CPO-2025-04-104",
                "po_date": "2025-04-24",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "April Shan wholesale replenishment order placed directly without formal quotation stage.",
            },
            "delivery_note": {
                "posting_date": "2025-04-25",
                "posting_time": "10:50:00",
                "remarks": "April Taunggyi mixed dispatch after direct-order confirmation from township wholesale customer.",
            },
            "sales_invoice": {
                "posting_date": "2025-04-25",
                "posting_time": "11:10:00",
                "due_date": "2025-05-25",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "April Taunggyi wholesale invoice issued after same-day dispatch.",
            },
        },
    ]

    direct_sales_defs = [
        {
            "customer": "Bago Myoma Phone Shop",
            "posting_date": "2025-04-27",
            "due_date": "2025-04-27",
            "warehouse": warehouse,
            "company": company,
            "remarks": "April small Bago township replenishment billed directly as same-day counter wholesale.",
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 1020000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 5, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 10, "rate": 32000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 10, "rate": 8000},
            ],
        },
        {
            "customer": "City Mobile Mart",
            "posting_date": "2025-04-29",
            "due_date": "2025-04-29",
            "warehouse": warehouse,
            "company": company,
            "remarks": "April small counter wholesale bundle settled as direct same-day billing.",
            "items": [
                {"item_code": "ACC-PWB-BAS-20K", "qty": 8, "rate": 110000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 30000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 10, "rate": 32000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 10, "rate": 8000},
            ],
        },
    ]

    payment_specs = [
        ("Bayint Naung Wholesale Mobile", "2025-04-11", "2025-04-28", 4000000),
        ("35th Street Mobile Wholesale", "2025-04-18", "2025-04-29", 3000000),
        ("Capital Telecom (NPT)", "2025-04-22", "2025-04-30", 2500000),
        ("Taunggyi City Mobile", "2025-04-25", "2025-04-30", 2000000),
        ("Bago Myoma Phone Shop", "2025-04-27", "2025-04-27", 1500000),
        ("City Mobile Mart", "2025-04-29", "2025-04-29", 1580000),
    ]

    supplier_payment_specs = [
        ("april_golden_dragon_handset_replenishment", "2025-04-25", 5000000),
        ("april_sunflower_accessory_replenishment", "2025-04-30", 3000000),
        ("april_handset_buffer_topup", "2025-04-30", 3000000),
    ]

    quotation_lookup: dict[str, str] = {}
    quotation_spec_lookup = {spec["label"]: spec for spec in quotation_specs}
    invoice_lookup: dict[tuple[str, str], str] = {}
    purchase_invoice_lookup: dict[str, str] = {}
    result = {
        "credit_limits": [],
        "procurement_lanes": [],
        "quotations": [],
        "sales_orders": [],
        "delivery_notes": [],
        "sales_invoices": [],
        "payment_entries": [],
        "supplier_payments": [],
        "failed": [],
    }

    for customer_name, credit_limit in credit_limit_targets.items():
        try:
            if not frappe.db.exists("Customer", customer_name):
                continue
            customer = frappe.get_doc("Customer", customer_name)
            limit_row = None
            for row in customer.credit_limits:
                if row.company == company:
                    limit_row = row
                    break
            current_outstanding = float(
                frappe.db.sql(
                    """
                    select ifnull(sum(outstanding_amount), 0)
                    from `tabSales Invoice`
                    where customer = %s and docstatus = 1 and outstanding_amount > 0
                    """,
                    (customer_name,),
                )[0][0]
                or 0
            )
            effective_credit_limit = max(float(credit_limit), current_outstanding + 5000000)
            if limit_row:
                limit_row.credit_limit = effective_credit_limit
                limit_row.bypass_credit_limit_check = 0
            else:
                customer.append(
                    "credit_limits",
                    {
                        "company": company,
                        "credit_limit": effective_credit_limit,
                        "bypass_credit_limit_check": 0,
                    },
                )
            customer.save(ignore_permissions=True)
            frappe.db.commit()
            result["credit_limits"].append({"customer": customer_name, "credit_limit": effective_credit_limit})
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"label": f"credit_limit_{customer_name}", "stage": "credit_limit", "error": str(exc)}
            )

    for lane in procurement_lanes:
        try:
            lane["purchase_order"]["expected_total"] = _sum_item_amounts(lane["purchase_order"]["items"])
            po_name = _create_purchase_order(lane["purchase_order"])
            pr_name = _create_purchase_receipt_from_order(po_name, lane["purchase_receipt"])
            pi_name = _create_purchase_invoice_from_receipt(
                pr_name,
                lane["purchase_order"]["supplier"],
                lane["purchase_order"].get("payment_terms_template"),
                lane["purchase_invoice"],
            )
            purchase_invoice_lookup[lane["label"]] = pi_name
            frappe.db.commit()
            result["procurement_lanes"].append(
                {
                    "label": lane["label"],
                    "purchase_order": po_name,
                    "purchase_receipt": pr_name,
                    "purchase_invoice": pi_name,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": lane["label"], "stage": "procurement", "error": str(exc)})

    for spec in quotation_specs:
        try:
            spec["company"] = company
            spec["expected_total"] = _sum_item_amounts(spec["items"])
            quotation_name = _create_quotation(spec)
            quotation_lookup[spec["label"]] = quotation_name
            if spec.get("target_status") == "Lost":
                frappe.db.set_value(
                    "Quotation",
                    quotation_name,
                    {
                        "status": "Lost",
                        "order_lost_reason": "April commercial follow-up ended without confirmation after competitor comparison and margin review.",
                    },
                    update_modified=False,
                )
            elif spec.get("target_status") == "Expired":
                frappe.db.set_value(
                    "Quotation",
                    quotation_name,
                    {"status": "Expired", "order_lost_reason": None},
                    update_modified=False,
                )
            frappe.db.commit()
            result["quotations"].append(
                {
                    "label": spec["label"],
                    "quotation": quotation_name,
                    "customer": spec["customer"],
                    "grand_total": spec["expected_total"],
                    "target_status": spec.get("target_status") or "Submitted",
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "stage": "quotation", "error": str(exc)})

    for spec in chain_specs:
        try:
            if spec.get("quotation_label"):
                quoted_items = quotation_spec_lookup[spec["quotation_label"]]["items"]
                expected_total = _sum_item_amounts(quoted_items)
                quotation_name = quotation_lookup[spec["quotation_label"]]
                order_date = getdate(spec["sales_order"]["transaction_date"])
                valid_till = getdate(frappe.db.get_value("Quotation", quotation_name, "valid_till"))
                if valid_till and valid_till < order_date:
                    frappe.db.set_value("Quotation", quotation_name, "valid_till", str(order_date), update_modified=False)
                    frappe.db.commit()
                try:
                    sales_order_name = _create_sales_order_from_quotation(
                        quotation_name,
                        {
                            **spec["sales_order"],
                            "customer": spec["customer"],
                            "expected_total": expected_total,
                        },
                    )
                except Exception as exc:
                    if "Validity period of this quotation has ended." not in str(exc):
                        raise
                    sales_order_name = _create_sales_order(
                        {
                            **spec["sales_order"],
                            "customer": spec["customer"],
                            "company": company,
                            "expected_total": expected_total,
                            "items": quoted_items,
                            "remarks": f"{spec['sales_order'].get('remarks') or ''} Historical quotation conversion recreated directly because the original quotation is already past live-system validity.",
                        }
                    )
                    frappe.db.set_value("Quotation", quotation_name, "status", "Ordered", update_modified=False)
                    _sync_quotation_workflow_state(quotation_name)
                    frappe.db.commit()
            else:
                expected_total = _sum_item_amounts(spec["items"])
                sales_order_name = _create_sales_order(
                    {
                        **spec["sales_order"],
                        "customer": spec["customer"],
                        "company": company,
                        "expected_total": expected_total,
                        "items": spec["items"],
                    }
                )
            delivery_note_name = _create_delivery_note_from_sales_order(sales_order_name, spec["delivery_note"])
            sales_invoice_name = _create_sales_invoice_from_delivery_note(
                delivery_note_name, spec["sales_invoice"]
            )
            invoice_lookup[(spec["customer"], spec["sales_invoice"]["posting_date"])] = sales_invoice_name
            frappe.db.commit()
            result["sales_orders"].append({"label": spec["label"], "sales_order": sales_order_name})
            result["delivery_notes"].append({"label": spec["label"], "delivery_note": delivery_note_name})
            result["sales_invoices"].append({"label": spec["label"], "sales_invoice": sales_invoice_name})
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "stage": "sales_chain", "error": str(exc)})

    for definition in direct_sales_defs:
        try:
            definition["expected_total"] = _sum_item_amounts(definition["items"])
            invoice_name = _create_sales_invoice(definition)
            invoice_lookup[(definition["customer"], definition["posting_date"])] = invoice_name
            frappe.db.commit()
            result["sales_invoices"].append(
                {
                    "label": f"direct_{definition['customer']}_{definition['posting_date']}",
                    "sales_invoice": invoice_name,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"direct_{definition['customer']}_{definition['posting_date']}",
                    "stage": "direct_sales",
                    "error": str(exc),
                }
            )

    for customer, invoice_date, payment_date, amount in payment_specs:
        try:
            invoice_name = invoice_lookup[(customer, invoice_date)]
            payment_name = _create_partial_payment("Sales Invoice", invoice_name, payment_date, amount)
            frappe.db.commit()
            result["payment_entries"].append(
                {
                    "customer": customer,
                    "sales_invoice": invoice_name,
                    "payment_entry": payment_name,
                    "amount": amount,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"label": f"receipt_{customer}_{invoice_date}", "stage": "receipt", "error": str(exc)}
            )

    for lane_label, payment_date, amount in supplier_payment_specs:
        try:
            invoice_name = purchase_invoice_lookup[lane_label]
            payment_name = _create_partial_payment("Purchase Invoice", invoice_name, payment_date, amount)
            frappe.db.commit()
            result["supplier_payments"].append(
                {
                    "purchase_invoice": invoice_name,
                    "payment_entry": payment_name,
                    "amount": amount,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"label": f"supplier_payment_{lane_label}", "stage": "supplier_payment", "error": str(exc)}
            )

    return result


def apply_april_2026_current_month_integration_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."

    quotation_updates = [
        {
            "name": "SAL-QTN-2026-00009",
            "target_status": "Lost",
            "order_lost_reason": (
                "Superseded by a revised April quotation after the customer changed handset mix "
                "and the deal moved to a higher-value approval path."
            ),
        },
        {
            "name": "SAL-QTN-2026-00010",
            "target_status": "Expired",
            "order_lost_reason": None,
        },
        {
            "name": "SAL-QTN-2026-00011",
            "target_status": "Expired",
            "order_lost_reason": None,
        },
    ]

    procurement_lane = {
        "label": "april_2026_golden_dragon_replenishment",
        "purchase_order": {
            "supplier": "Golden Dragon Trading Co. Ltd.",
            "company": company,
            "transaction_date": "2026-04-15",
            "schedule_date": "2026-04-15",
            "payment_terms_template": "30 Days - MMOB",
            "set_warehouse": "Yangon Main Warehouse - MMOB",
            "remarks": (
                "April 2026 handset-led replenishment to support current Yangon wholesale demand "
                "while approval-pipeline orders remain open."
            ),
            "items": [
                {
                    "item_code": "SPH-XMI-RN13-8/256",
                    "qty": 10,
                    "rate": 710000,
                    "warehouse": "Yangon Main Warehouse - MMOB",
                },
                {
                    "item_code": "SPH-SAM-A15-6/128",
                    "qty": 8,
                    "rate": 790000,
                    "warehouse": "Yangon Main Warehouse - MMOB",
                },
                {
                    "item_code": "ACC-CHR-XMI-33W",
                    "qty": 40,
                    "rate": 20500,
                    "warehouse": "Yangon Main Warehouse - MMOB",
                },
            ],
        },
        "purchase_receipt": {
            "supplier": "Golden Dragon Trading Co. Ltd.",
            "posting_date": "2026-04-15",
            "posting_time": "11:20:00",
            "supplier_delivery_note": "GD-DN-260415-01",
            "remarks": "Golden Dragon April current-month replenishment receipt for handset-led wholesale activity.",
        },
        "purchase_invoice": {
            "posting_date": "2026-04-15",
            "posting_time": "15:00:00",
            "bill_no": "GD-INV-2604-151",
            "bill_date": "2026-04-15",
            "due_date": "2026-05-15",
            "remarks": "Golden Dragon April current-month supplier invoice / normal 30-day credit.",
        },
    }

    sales_chain_specs = [
        {
            "label": "april_2026_aung_aung_routine_replenishment",
            "customer": "Aung Aung Telecom",
            "items": [
                {
                    "item_code": "SPH-XMI-RN13-8/256",
                    "qty": 3,
                    "rate": 940000,
                    "warehouse": "Mandalay Warehouse - MMOB",
                },
                {
                    "item_code": "ACC-PWB-BAS-20K",
                    "qty": 10,
                    "rate": 90000,
                    "warehouse": "Mandalay Warehouse - MMOB",
                },
                {
                    "item_code": "ACC-CHR-XMI-33W",
                    "qty": 15,
                    "rate": 26000,
                    "warehouse": "Mandalay Warehouse - MMOB",
                },
                {
                    "item_code": "ACC-CBL-BAS-TC1M",
                    "qty": 20,
                    "rate": 7500,
                    "warehouse": "Mandalay Warehouse - MMOB",
                },
            ],
            "sales_order": {
                "transaction_date": "2026-04-19",
                "delivery_date": "2026-04-19",
                "po_no": "AAT-MDY-0419-01",
                "po_date": "2026-04-19",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": "Mandalay Warehouse - MMOB",
                "remarks": (
                    "April 2026 routine Mandalay-lane replenishment for Aung Aung Telecom while the "
                    "separate larger revised order remains under approval."
                ),
            },
            "delivery_note": {
                "posting_date": "2026-04-19",
                "posting_time": "14:10:00",
                "remarks": "April 2026 Aung Aung Telecom routine Mandalay dispatch after same-day order confirmation.",
            },
            "sales_invoice": {
                "posting_date": "2026-04-19",
                "posting_time": "14:30:00",
                "due_date": "2026-05-19",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "April 2026 Aung Aung Telecom invoice for routine mixed replenishment on 30-day terms.",
            },
        },
        {
            "label": "april_2026_mandalay_accessories_repeat_order",
            "customer": "Mandalay Accessories Wholesale",
            "items": [
                {
                    "item_code": "SPH-XMI-RN13-8/256",
                    "qty": 2,
                    "rate": 940000,
                    "warehouse": "Mandalay Warehouse - MMOB",
                },
                {
                    "item_code": "SPH-SAM-A15-6/128",
                    "qty": 1,
                    "rate": 900000,
                    "warehouse": "Mandalay Warehouse - MMOB",
                },
                {
                    "item_code": "ACC-PWB-BAS-20K",
                    "qty": 20,
                    "rate": 90000,
                    "warehouse": "Mandalay Warehouse - MMOB",
                },
                {
                    "item_code": "ACC-CHR-XMI-33W",
                    "qty": 30,
                    "rate": 26000,
                    "warehouse": "Mandalay Warehouse - MMOB",
                },
                {
                    "item_code": "ACC-CBL-BAS-TC1M",
                    "qty": 40,
                    "rate": 7500,
                    "warehouse": "Mandalay Warehouse - MMOB",
                },
            ],
            "sales_order": {
                "transaction_date": "2026-04-24",
                "delivery_date": "2026-04-24",
                "po_no": "MAW-MDY-0424-01",
                "po_date": "2026-04-24",
                "payment_terms_template": "15 Days - MMOB",
                "set_warehouse": "Mandalay Warehouse - MMOB",
                "remarks": "April 2026 accessories-heavy repeat wholesale order for Mandalay Accessories Wholesale.",
            },
            "delivery_note": {
                "posting_date": "2026-04-24",
                "posting_time": "11:15:00",
                "remarks": "April 2026 Mandalay accessories-heavy wholesale dispatch after repeat order confirmation.",
            },
            "sales_invoice": {
                "posting_date": "2026-04-24",
                "posting_time": "11:35:00",
                "due_date": "2026-05-09",
                "payment_terms_template": "15 Days - MMOB",
                "remarks": "April 2026 Mandalay accessories-heavy wholesale invoice on 15-day credit.",
            },
        },
    ]

    direct_sales_defs = [
        {
            "customer": "Taunggyi City Mobile",
            "posting_date": "2026-04-27",
            "due_date": "2026-04-27",
            "warehouse": "Mandalay Warehouse - MMOB",
            "company": company,
            "remarks": "April 2026 Shan township COD mixed bundle billed directly and settled the same day.",
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 960000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 920000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 4, "rate": 95000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 28000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 10, "rate": 8000},
            ],
        }
    ]

    result = {
        "quotation_updates": [],
        "procurement_lanes": [],
        "sales_orders": [],
        "delivery_notes": [],
        "sales_invoices": [],
        "payment_entries": [],
        "supplier_payments": [],
        "failed": [],
    }

    for spec in quotation_updates:
        try:
            if not frappe.db.exists("Quotation", spec["name"]):
                result["failed"].append(
                    {"label": spec["name"], "stage": "quotation_update", "error": "missing_quotation"}
                )
                continue
            quotation = frappe.get_doc("Quotation", spec["name"])
            if quotation.docstatus != 1:
                result["failed"].append(
                    {
                        "label": spec["name"],
                        "stage": "quotation_update",
                        "error": f"unexpected_docstatus_{quotation.docstatus}",
                    }
                )
                continue

            change_type = "existing"
            if quotation.status != spec["target_status"]:
                frappe.db.set_value(
                    "Quotation",
                    quotation.name,
                    {
                        "status": spec["target_status"],
                        "order_lost_reason": spec["order_lost_reason"],
                    },
                    update_modified=False,
                )
                _sync_quotation_workflow_state(quotation.name)
                frappe.db.commit()
                change_type = "updated"

            refreshed = frappe.get_doc("Quotation", quotation.name)
            result["quotation_updates"].append(
                {
                    "quotation": refreshed.name,
                    "change_type": change_type,
                    "status": refreshed.status,
                    "workflow_state": refreshed.workflow_state,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"label": spec["name"], "stage": "quotation_update", "error": str(exc)}
            )

    try:
        procurement_lane["purchase_order"]["expected_total"] = _sum_item_amounts(
            procurement_lane["purchase_order"]["items"]
        )
        po_name = _create_purchase_order(procurement_lane["purchase_order"])
        pr_name = _create_purchase_receipt_from_order(po_name, procurement_lane["purchase_receipt"])
        pi_name = _create_purchase_invoice_from_receipt(
            pr_name,
            procurement_lane["purchase_order"]["supplier"],
            procurement_lane["purchase_order"].get("payment_terms_template"),
            procurement_lane["purchase_invoice"],
        )
        frappe.db.commit()
        result["procurement_lanes"].append(
            {
                "label": procurement_lane["label"],
                "purchase_order": po_name,
                "purchase_receipt": pr_name,
                "purchase_invoice": pi_name,
            }
        )
    except Exception as exc:
        frappe.db.rollback()
        result["failed"].append(
            {"label": procurement_lane["label"], "stage": "procurement", "error": str(exc)}
        )
        pi_name = None

    invoice_lookup: dict[tuple[str, str], str] = {}

    for spec in sales_chain_specs:
        try:
            expected_total = _sum_item_amounts(spec["items"])
            sales_order_name = _create_sales_order(
                {
                    **spec["sales_order"],
                    "customer": spec["customer"],
                    "company": company,
                    "expected_total": expected_total,
                    "items": spec["items"],
                }
            )
            delivery_note_name = _create_delivery_note_from_sales_order(
                sales_order_name,
                spec["delivery_note"],
            )
            sales_invoice_name = _create_sales_invoice_from_delivery_note(
                delivery_note_name,
                spec["sales_invoice"],
            )
            invoice_lookup[(spec["customer"], spec["sales_invoice"]["posting_date"])] = sales_invoice_name
            frappe.db.commit()
            result["sales_orders"].append({"label": spec["label"], "sales_order": sales_order_name})
            result["delivery_notes"].append({"label": spec["label"], "delivery_note": delivery_note_name})
            result["sales_invoices"].append({"label": spec["label"], "sales_invoice": sales_invoice_name})
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "stage": "sales_chain", "error": str(exc)})

    for definition in direct_sales_defs:
        try:
            definition["expected_total"] = _sum_item_amounts(definition["items"])
            invoice_name = _create_sales_invoice(definition)
            invoice_lookup[(definition["customer"], definition["posting_date"])] = invoice_name
            frappe.db.commit()
            result["sales_invoices"].append(
                {
                    "label": f"direct_{definition['customer']}_{definition['posting_date']}",
                    "sales_invoice": invoice_name,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"direct_{definition['customer']}_{definition['posting_date']}",
                    "stage": "direct_sales",
                    "error": str(exc),
                }
            )

    payment_specs = [
        ("Mandalay Accessories Wholesale", "2026-04-24", "2026-04-30", 2000000),
        ("Taunggyi City Mobile", "2026-04-27", "2026-04-27", 4500000),
    ]

    for customer, invoice_date, payment_date, amount in payment_specs:
        try:
            invoice_name = invoice_lookup[(customer, invoice_date)]
            payment_name = _create_partial_payment_with_date_dedupe(
                "Sales Invoice", invoice_name, payment_date, amount
            )
            frappe.db.commit()
            result["payment_entries"].append(
                {
                    "customer": customer,
                    "sales_invoice": invoice_name,
                    "payment_entry": payment_name,
                    "amount": amount,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"label": f"receipt_{customer}_{invoice_date}", "stage": "receipt", "error": str(exc)}
            )

    if pi_name:
        try:
            supplier_payment_name = _create_partial_payment_with_date_dedupe(
                "Purchase Invoice",
                pi_name,
                "2026-04-29",
                4000000,
            )
            frappe.db.commit()
            result["supplier_payments"].append(
                {
                    "purchase_invoice": pi_name,
                    "payment_entry": supplier_payment_name,
                    "amount": 4000000,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": "supplier_payment_april_2026_golden_dragon_replenishment",
                    "stage": "supplier_payment",
                    "error": str(exc),
                }
            )

    return result


def apply_april_2026_hr_finance_checkpoint_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    currency = "MMK"
    result: dict[str, Any] = {
        "salary_slips": {},
        "journal_entries": [],
        "failed": [],
    }

    try:
        salary_slip_result = create_salary_slips_for_month(
            period_start="2026-04-01",
            period_end="2026-04-30",
            posting_date="2026-04-30",
            company=company,
            currency=currency,
        )
        result["salary_slips"] = salary_slip_result
    except Exception as exc:
        frappe.db.rollback()
        result["failed"].append({"stage": "salary_slips", "error": str(exc)})
        return result

    salary_slip_rows = frappe.db.sql(
        """
        select ifnull(sum(net_pay), 0) as net_pay
        from `tabSalary Slip`
        where docstatus = 1
          and posting_date between '2026-04-01' and '2026-04-30'
        """,
        as_dict=True,
    )
    april_net_pay = float((salary_slip_rows[0]["net_pay"] or 0) if salary_slip_rows else 0)

    salary_expense_account = _find_account_by_names(
        [
            "Salaries and Wages - MMOB",
            "Salary - MMOB",
            "Payroll Expenses - MMOB",
            "Staff Salary - MMOB",
            "Salary Expense - MMOB",
        ]
    )
    payroll_payable_account = _find_account_by_names(
        [
            "Payroll Payable - MMOB",
            "Salary Payable - MMOB",
        ]
    )

    if april_net_pay > 0 and salary_expense_account and payroll_payable_account:
        try:
            payroll_journal = _create_simple_journal_entry(
                {
                    "company": company,
                    "posting_date": "2026-04-30",
                    "voucher_type": "Journal Entry",
                    "user_remark": "AI-APR2026-PAYROLL-ACCRUAL | April 2026 month-end payroll accrual before early-May settlement.",
                    "accounts": [
                        {
                            "account": salary_expense_account,
                            "debit_in_account_currency": int(round(april_net_pay / 1000.0) * 1000),
                        },
                        {
                            "account": payroll_payable_account,
                            "credit_in_account_currency": int(round(april_net_pay / 1000.0) * 1000),
                        },
                    ],
                }
            )
            frappe.db.commit()
            result["journal_entries"].append(
                {
                    "label": "april_2026_payroll_accrual",
                    "journal_entry": payroll_journal,
                    "amount": int(round(april_net_pay / 1000.0) * 1000),
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"stage": "payroll_accrual", "error": str(exc)})
    else:
        result["failed"].append(
            {
                "stage": "payroll_accrual",
                "error": "missing_payroll_accounts_or_zero_net_pay",
                "salary_expense_account": salary_expense_account,
                "payroll_payable_account": payroll_payable_account,
                "net_pay": april_net_pay,
            }
        )

    rent_account = _find_account_by_names(["Rent - MMOB", "Office Rent - MMOB", "Rent Expense - MMOB"])
    utilities_account = _find_account_by_names(["Utilities - MMOB", "Electricity - MMOB", "Water Expense - MMOB"])
    logistics_account = _find_account_by_names(
        ["Delivery Expenses - MMOB", "Freight and Forwarding - MMOB", "Logistics - MMOB"]
    )
    marketing_account = _find_account_by_names(["Marketing Expenses - MMOB", "Sales Promotion - MMOB", "Advertising - MMOB"])
    admin_account = _find_account_by_names(["Office Expenses - MMOB", "Administrative Expenses - MMOB", "General Expenses - MMOB"])
    telecom_account = _find_account_by_names(["Telephone Expense - MMOB", "Internet Expense - MMOB", "Communication Expenses - MMOB"])
    kbz_bank_account = _find_account_by_names(["KBZ-001-000123 - KBZ Bank - Current - MMOB"])
    cash_account = _find_account_by_names(["Cash - MMOB"])

    expense_lines: list[dict[str, Any]] = []
    if rent_account:
        expense_lines.append({"account": rent_account, "debit_in_account_currency": 5_000_000})
    if utilities_account:
        expense_lines.append({"account": utilities_account, "debit_in_account_currency": 1_300_000})
    if logistics_account:
        expense_lines.append({"account": logistics_account, "debit_in_account_currency": 1_800_000})
    if marketing_account:
        expense_lines.append({"account": marketing_account, "debit_in_account_currency": 900_000})
    if admin_account:
        expense_lines.append({"account": admin_account, "debit_in_account_currency": 1_000_000})
    if telecom_account:
        expense_lines.append({"account": telecom_account, "debit_in_account_currency": 650_000})

    if expense_lines and kbz_bank_account and cash_account:
        total_opex = int(sum(line["debit_in_account_currency"] for line in expense_lines))
        try:
            opex_journal = _create_simple_journal_entry(
                {
                    "company": company,
                    "posting_date": "2026-04-30",
                    "voucher_type": "Journal Entry",
                    "user_remark": "AI-APR2026-OPEX-BASELINE | April 2026 operating expense baseline for rent, utilities, logistics, admin, telecom, and marketing.",
                    "accounts": [
                        *expense_lines,
                        {"account": kbz_bank_account, "credit_in_account_currency": 6_550_000},
                        {"account": cash_account, "credit_in_account_currency": total_opex - 6_550_000},
                    ],
                }
            )
            frappe.db.commit()
            result["journal_entries"].append(
                {
                    "label": "april_2026_opex_baseline",
                    "journal_entry": opex_journal,
                    "amount": total_opex,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"stage": "opex_baseline", "error": str(exc)})
    else:
        result["failed"].append(
            {
                "stage": "opex_baseline",
                "error": "missing_opex_or_cash_accounts",
                "kbz_bank_account": kbz_bank_account,
                "cash_account": cash_account,
            }
        )

    return result


def apply_april_2026_hr_finance_opex_supplement_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    result: dict[str, Any] = {"journal_entries": [], "failed": []}

    utilities_account = _find_account_by_names(
        ["Utilities - MMOB", "Utility Expenses - MMOB", "Electricity - MMOB", "Water Expense - MMOB"]
    )
    logistics_account = _find_account_by_names(
        [
            "Delivery Expenses - MMOB",
            "Freight and Forwarding Charges - MMOB",
            "Freight and Forwarding - MMOB",
            "Logistics - MMOB",
        ]
    )
    telecom_account = _find_account_by_names(
        ["Telephone Expense - MMOB", "Telephone Expenses - MMOB", "Internet Expense - MMOB", "Communication Expenses - MMOB"]
    )
    kbz_bank_account = _find_account_by_names(["KBZ-001-000123 - KBZ Bank - Current - MMOB"])
    cash_account = _find_account_by_names(["Cash - MMOB"])

    expense_lines: list[dict[str, Any]] = []
    if utilities_account:
        expense_lines.append({"account": utilities_account, "debit_in_account_currency": 1_300_000})
    if logistics_account:
        expense_lines.append({"account": logistics_account, "debit_in_account_currency": 1_800_000})
    if telecom_account:
        expense_lines.append({"account": telecom_account, "debit_in_account_currency": 650_000})

    if not expense_lines or not kbz_bank_account or not cash_account:
        result["failed"].append(
            {
                "stage": "opex_supplement",
                "error": "missing_accounts",
                "utilities_account": utilities_account,
                "logistics_account": logistics_account,
                "telecom_account": telecom_account,
                "kbz_bank_account": kbz_bank_account,
                "cash_account": cash_account,
            }
        )
        return result

    total_opex = int(sum(line["debit_in_account_currency"] for line in expense_lines))
    try:
        supplement_journal = _create_simple_journal_entry(
            {
                "company": company,
                "posting_date": "2026-04-30",
                "voucher_type": "Journal Entry",
                "user_remark": "AI-APR2026-OPEX-SUPPLEMENT | April 2026 utilities, freight, and telecom expense supplement after account-name normalization.",
                "accounts": [
                    *expense_lines,
                    {"account": kbz_bank_account, "credit_in_account_currency": 2_400_000},
                    {"account": cash_account, "credit_in_account_currency": total_opex - 2_400_000},
                ],
            }
        )
        frappe.db.commit()
        result["journal_entries"].append(
            {
                "label": "april_2026_opex_supplement",
                "journal_entry": supplement_journal,
                "amount": total_opex,
            }
        )
    except Exception as exc:
        frappe.db.rollback()
        result["failed"].append({"stage": "opex_supplement", "error": str(exc)})

    return result


def _round_mmk_policy_rate(rate: float, step: int) -> float:
    if not rate or rate <= 0:
        return 0.0
    rounded = int(round(float(rate) / step) * step)
    return float(max(rounded, step))


def _product_price_policy(item_group: str) -> dict[str, Any]:
    high_value_groups = {"Smartphones", "Small Gadgets", "Networking", "CCTV & Security"}
    medium_value_groups = {"Memory & Storage", "Spare Parts & Service"}
    if item_group == "Phone Accessories":
        return {
            "step": 100,
            "wholesale_std_sell_factor": 0.92,
            "wholesale_buy_floor": 1.10,
            "key_std_sell_factor": 0.88,
            "key_buy_floor": 1.07,
        }
    if item_group == "Consumable":
        return {
            "step": 100,
            "wholesale_std_sell_factor": 0.92,
            "wholesale_buy_floor": 1.08,
            "key_std_sell_factor": 0.88,
            "key_buy_floor": 1.05,
        }
    if item_group in high_value_groups:
        return {
            "step": 1000,
            "wholesale_std_sell_factor": 0.98,
            "wholesale_buy_floor": 1.02,
            "key_std_sell_factor": 0.97,
            "key_buy_floor": 1.01,
        }
    if item_group in medium_value_groups:
        return {
            "step": 500,
            "wholesale_std_sell_factor": 0.94,
            "wholesale_buy_floor": 1.10,
            "key_std_sell_factor": 0.90,
            "key_buy_floor": 1.06,
        }
    return {
        "step": 100,
        "wholesale_std_sell_factor": 0.92,
        "wholesale_buy_floor": 1.10,
        "key_std_sell_factor": 0.88,
        "key_buy_floor": 1.07,
    }


def _derive_mmob_channel_rates(item_group: str, standard_buying: float, standard_selling: float) -> dict[str, float]:
    policy = _product_price_policy(item_group)
    step = policy["step"]
    retail = _round_mmk_policy_rate(standard_selling, step)
    wholesale = _round_mmk_policy_rate(
        max(
            standard_buying * policy["wholesale_buy_floor"],
            standard_selling * policy["wholesale_std_sell_factor"],
        ),
        step,
    )
    wholesale = min(wholesale, retail)
    key_account = _round_mmk_policy_rate(
        max(
            standard_buying * policy["key_buy_floor"],
            standard_selling * policy["key_std_sell_factor"],
        ),
        step,
    )
    key_account = min(key_account, wholesale)
    if key_account <= standard_buying:
        key_account = _round_mmk_policy_rate(standard_buying * 1.01, step)
    if wholesale < key_account:
        wholesale = key_account
    if retail < wholesale:
        retail = wholesale
    return {
        "Standard Buying - MMOB": _round_mmk_policy_rate(standard_buying, step),
        "Retail Selling - MMOB": retail,
        "Wholesale Selling - MMOB": wholesale,
        "Key Account Selling - MMOB": key_account,
    }


def _get_item_price_doc(item_code: str, price_list: str) -> dict[str, Any] | None:
    rows = frappe.get_all(
        "Item Price",
        filters={"item_code": item_code, "price_list": price_list},
        fields=["name", "price_list_rate", "buying", "selling", "currency"],
        order_by="valid_from desc, creation desc",
        limit=1,
    )
    return rows[0] if rows else None


def _upsert_item_price(
    item_code: str,
    item_name: str,
    stock_uom: str,
    price_list: str,
    rate: float,
    *,
    valid_from: str,
) -> dict[str, Any]:
    existing = _get_item_price_doc(item_code, price_list)
    is_buying = 1 if price_list == "Standard Buying - MMOB" else 0
    is_selling = 0 if is_buying else 1
    payload = {
        "item_code": item_code,
        "item_name": item_name,
        "price_list": price_list,
        "price_list_rate": rate,
        "currency": "MMK",
        "uom": stock_uom or "Nos",
        "buying": is_buying,
        "selling": is_selling,
        "valid_from": valid_from,
    }
    if existing:
        current_rate = float(existing.price_list_rate or 0)
        if int(round(current_rate)) == int(round(rate)):
            return {"status": "kept", "price_list": price_list, "rate": rate, "name": existing.name}
        doc = frappe.get_doc("Item Price", existing.name)
        for key, value in payload.items():
            setattr(doc, key, value)
        doc.save(ignore_permissions=True)
        return {"status": "updated", "price_list": price_list, "rate": rate, "name": doc.name}

    doc = frappe.get_doc({"doctype": "Item Price", **payload})
    doc.insert(ignore_permissions=True)
    return {"status": "created", "price_list": price_list, "rate": rate, "name": doc.name}


def _ensure_stock_item_default_warehouse(item_code: str, company: str, default_warehouse: str) -> dict[str, Any]:
    row = frappe.get_all(
        "Item Default",
        filters={"parent": item_code, "company": company},
        fields=["name", "default_warehouse"],
        limit=1,
    )
    if row:
        current = row[0]
        if current.default_warehouse == default_warehouse:
            return {"status": "kept", "default_warehouse": default_warehouse}
        frappe.db.set_value(
            "Item Default",
            current.name,
            "default_warehouse",
            default_warehouse,
            update_modified=False,
        )
        return {"status": "updated", "default_warehouse": default_warehouse}

    item_doc = frappe.get_doc("Item", item_code)
    item_doc.append(
        "item_defaults",
        {
            "company": company,
            "default_warehouse": default_warehouse,
        },
    )
    item_doc.save(ignore_permissions=True)
    return {"status": "created", "default_warehouse": default_warehouse}


def audit_product_master_pricing_and_warehouse_realism() -> dict[str, Any]:
    stock_items = frappe.get_all(
        "Item",
        filters={"disabled": 0, "is_stock_item": 1},
        fields=["item_code", "item_name", "item_group", "stock_uom"],
        order_by="item_code asc",
    )
    coverage: list[dict[str, Any]] = []
    missing_buying: list[str] = []
    missing_selling: list[str] = []
    suspicious_prices: list[dict[str, Any]] = []

    for item in stock_items:
        standard_buy = _get_item_price_doc(item.item_code, "Standard Buying")
        standard_sell = _get_item_price_doc(item.item_code, "Standard Selling")
        mmob_buy = _get_item_price_doc(item.item_code, "Standard Buying - MMOB")
        mmob_retail = _get_item_price_doc(item.item_code, "Retail Selling - MMOB")
        mmob_wholesale = _get_item_price_doc(item.item_code, "Wholesale Selling - MMOB")
        mmob_key = _get_item_price_doc(item.item_code, "Key Account Selling - MMOB")

        has_buy = bool(mmob_buy)
        has_sell = any([mmob_retail, mmob_wholesale, mmob_key])
        if not has_buy:
            missing_buying.append(item.item_code)
        if not has_sell:
            missing_selling.append(item.item_code)

        standard_sell_rate = float(standard_sell.price_list_rate or 0) if standard_sell else 0.0
        standard_buy_rate = float(standard_buy.price_list_rate or 0) if standard_buy else 0.0
        for price_doc in [mmob_retail, mmob_wholesale, mmob_key]:
            if not price_doc or not standard_sell_rate:
                continue
            current_rate = float(price_doc.price_list_rate or 0)
            if current_rate < (standard_sell_rate * 0.60) or current_rate > (standard_sell_rate * 1.60):
                suspicious_prices.append(
                    {
                        "item_code": item.item_code,
                        "price_list": price_doc.price_list,
                        "current_rate": current_rate,
                        "standard_selling": standard_sell_rate,
                    }
                )
        if mmob_buy and standard_buy_rate:
            current_buy_rate = float(mmob_buy.price_list_rate or 0)
            if current_buy_rate < (standard_buy_rate * 0.75) or current_buy_rate > (standard_buy_rate * 1.25):
                suspicious_prices.append(
                    {
                        "item_code": item.item_code,
                        "price_list": "Standard Buying - MMOB",
                        "current_rate": current_buy_rate,
                        "standard_buying": standard_buy_rate,
                    }
                )

        coverage.append(
            {
                "item_code": item.item_code,
                "standard_buying": standard_buy_rate,
                "standard_selling": standard_sell_rate,
                "has_mmob_buying": has_buy,
                "has_mmob_selling": has_sell,
            }
        )

    valuation_anomalies = frappe.db.sql(
        """
        select
            b.item_code,
            b.warehouse,
            round(b.actual_qty, 2) as qty,
            round(b.valuation_rate, 2) as valuation_rate,
            round(ip.price_list_rate, 2) as standard_buying_mmob
        from `tabBin` b
        inner join `tabItem` i on i.item_code = b.item_code
        inner join `tabItem Price` ip
            on ip.item_code = b.item_code
           and ip.price_list = 'Standard Buying - MMOB'
        where i.disabled = 0
          and i.is_stock_item = 1
          and b.actual_qty > 0
          and (b.valuation_rate < ip.price_list_rate * 0.40 or b.valuation_rate > ip.price_list_rate * 1.60)
        order by b.item_code, b.warehouse
        """,
        as_dict=True,
    )
    warehouse_totals = frappe.db.sql(
        """
        select
            warehouse,
            round(sum(stock_value), 2) as stock_value,
            round(sum(actual_qty), 2) as actual_qty
        from `tabBin`
        where actual_qty <> 0
        group by warehouse
        order by stock_value desc
        """,
        as_dict=True,
    )

    return {
        "status": "ok",
        "stock_item_count": len(stock_items),
        "missing_mmob_buying_count": len(missing_buying),
        "missing_mmob_selling_count": len(missing_selling),
        "suspicious_price_count": len(suspicious_prices),
        "missing_mmob_buying": missing_buying,
        "missing_mmob_selling": missing_selling,
        "suspicious_prices": suspicious_prices,
        "valuation_anomalies": valuation_anomalies,
        "warehouse_totals": warehouse_totals,
        "coverage": coverage,
    }


def audit_item_master_surface_realism() -> dict[str, Any]:
    rows = frappe.db.sql(
        """
        select
            i.item_code,
            i.item_name,
            i.item_group,
            round(ifnull(i.standard_rate, 0), 2) as standard_rate,
            round(ifnull(i.valuation_rate, 0), 2) as valuation_rate,
            round(avg(case when b.actual_qty > 0 then b.valuation_rate end), 2) as avg_bin_rate,
            round(max(case when ip.price_list = 'Standard Buying - MMOB' then ip.price_list_rate end), 2) as mmob_buying
        from `tabItem` i
        left join `tabBin` b on b.item_code = i.item_code
        left join `tabItem Price` ip on ip.item_code = i.item_code
        where i.disabled = 0
          and i.is_stock_item = 1
        group by i.item_code, i.item_name, i.item_group, i.standard_rate, i.valuation_rate
        order by i.item_code asc
        """,
        as_dict=True,
    )
    missing_standard = [row for row in rows if float(row.get("standard_rate") or 0) <= 0]
    missing_valuation = [row for row in rows if float(row.get("valuation_rate") or 0) <= 0]
    return {
        "status": "ok",
        "stock_item_count": len(rows),
        "missing_standard_rate_count": len(missing_standard),
        "missing_valuation_rate_count": len(missing_valuation),
        "missing_standard_rate": missing_standard,
        "missing_valuation_rate": missing_valuation,
        "rows": rows,
    }


def _derive_item_master_surface_values(item_code: str, item_group: str) -> dict[str, float]:
    mmob_buy_doc = _get_item_price_doc(item_code, "Standard Buying - MMOB")
    mmob_buying = float(mmob_buy_doc.price_list_rate or 0) if mmob_buy_doc else 0.0
    latest_incoming = _latest_purchase_incoming_rate(item_code)
    if latest_incoming and mmob_buying and (
        latest_incoming < mmob_buying * 0.5 or latest_incoming > mmob_buying * 1.5
    ):
        latest_incoming = None

    avg_bin_rows = frappe.db.sql(
        """
        select avg(valuation_rate) as avg_rate
        from `tabBin`
        where item_code = %s
          and actual_qty > 0
          and valuation_rate > 0
        """,
        (item_code,),
        as_dict=True,
    )
    avg_bin_rate = float((avg_bin_rows[0]["avg_rate"] or 0) if avg_bin_rows else 0)
    if avg_bin_rate and mmob_buying and (avg_bin_rate < mmob_buying * 0.5 or avg_bin_rate > mmob_buying * 1.5):
        avg_bin_rate = 0

    step = _product_price_policy(item_group).get("step", 100)
    standard_rate = _round_mmk_policy_rate(mmob_buying or latest_incoming or avg_bin_rate, step)
    valuation_candidates = [rate for rate in [avg_bin_rate, latest_incoming, mmob_buying] if rate]
    valuation_anchor = float(median(valuation_candidates)) if valuation_candidates else standard_rate
    valuation_rate = _round_mmk_policy_rate(valuation_anchor, step)
    return {
        "standard_rate": float(standard_rate or 0),
        "valuation_rate": float(valuation_rate or 0),
        "mmob_buying": float(mmob_buying or 0),
        "latest_incoming": float(latest_incoming or 0),
        "avg_bin_rate": float(avg_bin_rate or 0),
    }


def apply_item_master_surface_realism_wave() -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "ok",
        "before": audit_item_master_surface_realism(),
        "updated": [],
        "skipped": [],
        "failed": [],
    }

    stock_items = frappe.get_all(
        "Item",
        filters={"disabled": 0, "is_stock_item": 1},
        fields=["item_code", "item_name", "item_group", "standard_rate", "valuation_rate"],
        order_by="item_code asc",
    )

    for item in stock_items:
        try:
            target = _derive_item_master_surface_values(item.item_code, item.item_group)
            target_standard = float(target.get("standard_rate") or 0)
            target_valuation = float(target.get("valuation_rate") or 0)
            if target_standard <= 0 or target_valuation <= 0:
                result["skipped"].append(
                    {
                        "item_code": item.item_code,
                        "reason": "missing_target_anchor",
                        **target,
                    }
                )
                continue

            current_standard = float(item.standard_rate or 0)
            current_valuation = float(item.valuation_rate or 0)
            changed = False
            updates: dict[str, float] = {}

            if abs(current_standard - target_standard) >= 0.01:
                updates["standard_rate"] = target_standard
                changed = True
            if abs(current_valuation - target_valuation) >= 0.01:
                updates["valuation_rate"] = target_valuation
                changed = True

            if not changed:
                result["skipped"].append(
                    {
                        "item_code": item.item_code,
                        "reason": "already_aligned",
                        "standard_rate": current_standard,
                        "valuation_rate": current_valuation,
                    }
                )
                continue

            frappe.db.set_value("Item", item.item_code, updates, update_modified=False)
            result["updated"].append(
                {
                    "item_code": item.item_code,
                    "item_group": item.item_group,
                    "from_standard_rate": current_standard,
                    "to_standard_rate": target_standard,
                    "from_valuation_rate": current_valuation,
                    "to_valuation_rate": target_valuation,
                    "mmob_buying": target["mmob_buying"],
                    "latest_incoming": target["latest_incoming"],
                    "avg_bin_rate": target["avg_bin_rate"],
                }
            )
        except Exception as exc:
            result["failed"].append({"item_code": item.item_code, "error": str(exc)})

    frappe.db.commit()
    result["after"] = audit_item_master_surface_realism()
    return result


def apply_product_master_pricing_and_warehouse_realism_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    valid_from = "2026-04-15"
    default_warehouse = "Yangon Main Warehouse - MMOB"
    result: dict[str, Any] = {
        "status": "ok",
        "price_updates": [],
        "warehouse_updates": [],
        "skipped": [],
    }

    stock_items = frappe.get_all(
        "Item",
        filters={"disabled": 0, "is_stock_item": 1},
        fields=["item_code", "item_name", "item_group", "stock_uom"],
        order_by="item_code asc",
    )

    for item in stock_items:
        standard_buy = _get_item_price_doc(item.item_code, "Standard Buying")
        standard_sell = _get_item_price_doc(item.item_code, "Standard Selling")
        if not standard_buy or not standard_sell:
            result["skipped"].append(
                {
                    "item_code": item.item_code,
                    "reason": "missing_standard_price_anchor",
                    "has_standard_buying": bool(standard_buy),
                    "has_standard_selling": bool(standard_sell),
                }
            )
            continue

        rates = _derive_mmob_channel_rates(
            item.item_group,
            float(standard_buy.price_list_rate or 0),
            float(standard_sell.price_list_rate or 0),
        )
        for price_list, rate in rates.items():
            update = _upsert_item_price(
                item.item_code,
                item.item_name,
                item.stock_uom,
                price_list,
                rate,
                valid_from=valid_from,
            )
            result["price_updates"].append(
                {
                    "item_code": item.item_code,
                    "item_group": item.item_group,
                    **update,
                }
            )

        warehouse_update = _ensure_stock_item_default_warehouse(
            item.item_code,
            company,
            default_warehouse,
        )
        result["warehouse_updates"].append(
            {
                "item_code": item.item_code,
                **warehouse_update,
            }
        )

    frappe.db.commit()
    result["audit_after"] = audit_product_master_pricing_and_warehouse_realism()
    return result


def _latest_purchase_incoming_rate(item_code: str) -> float | None:
    rows = frappe.db.sql(
        """
        select incoming_rate
        from `tabStock Ledger Entry`
        where item_code = %s
          and actual_qty > 0
          and voucher_type in ('Purchase Invoice', 'Purchase Receipt')
        order by posting_date desc, creation desc
        limit 1
        """,
        item_code,
    )
    return float(rows[0][0]) if rows and rows[0][0] else None


def _healthy_peer_valuation_rates(item_code: str, warehouse: str, standard_buying: float | None) -> list[float]:
    rows = frappe.db.sql(
        """
        select valuation_rate
        from `tabBin`
        where item_code = %s
          and warehouse != %s
          and actual_qty > 0
          and valuation_rate > 0
        order by warehouse asc
        """,
        (item_code, warehouse),
    )
    peer_rates: list[float] = []
    for row in rows:
        rate = float(row[0] or 0)
        if not rate:
            continue
        if standard_buying and (rate < standard_buying * 0.5 or rate > standard_buying * 1.5):
            continue
        peer_rates.append(rate)
    return peer_rates


def _derive_target_valuation_rate(item_code: str, item_group: str, warehouse: str) -> dict[str, Any]:
    standard_buying_doc = _get_item_price_doc(item_code, "Standard Buying - MMOB")
    standard_buying = float(standard_buying_doc.price_list_rate or 0) if standard_buying_doc else 0.0
    latest_incoming = _latest_purchase_incoming_rate(item_code)
    if latest_incoming and standard_buying and (
        latest_incoming < standard_buying * 0.5 or latest_incoming > standard_buying * 1.5
    ):
        latest_incoming = None

    peer_rates = _healthy_peer_valuation_rates(item_code, warehouse, standard_buying or None)
    candidates = [rate for rate in [latest_incoming, standard_buying] if rate]
    candidates.extend(peer_rates)
    if not candidates:
        raise ValueError(f"No valuation candidates available for {item_code} @ {warehouse}")

    step = _product_price_policy(item_group).get("step", 100)
    target_rate = _round_mmk_policy_rate(float(median(candidates)), step)
    if target_rate <= 0:
        raise ValueError(f"Unable to derive positive target valuation for {item_code} @ {warehouse}")
    return {
        "target_rate": target_rate,
        "standard_buying_mmob": standard_buying,
        "latest_incoming": latest_incoming,
        "peer_rates": peer_rates,
        "candidate_rates": candidates,
    }


def audit_current_stock_valuation_normalization_candidates() -> dict[str, Any]:
    rows = frappe.db.sql(
        """
        select
            b.item_code,
            i.item_group,
            b.warehouse,
            b.actual_qty,
            b.valuation_rate,
            b.stock_value
        from `tabBin` b
        inner join `tabItem` i on i.item_code = b.item_code
        inner join `tabItem Price` ip
            on ip.item_code = b.item_code
           and ip.price_list = 'Standard Buying - MMOB'
        where i.disabled = 0
          and i.is_stock_item = 1
          and b.actual_qty > 0
          and (b.valuation_rate < ip.price_list_rate * 0.40 or b.valuation_rate > ip.price_list_rate * 1.60)
        order by b.item_code, b.warehouse
        """,
        as_dict=True,
    )

    candidates: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    for row in rows:
        try:
            target = _derive_target_valuation_rate(row.item_code, row.item_group, row.warehouse)
            target_rate = target["target_rate"]
            delta_value = float(row.actual_qty or 0) * (target_rate - float(row.valuation_rate or 0))
            candidates.append(
                {
                    "item_code": row.item_code,
                    "item_group": row.item_group,
                    "warehouse": row.warehouse,
                    "qty": float(row.actual_qty or 0),
                    "current_rate": float(row.valuation_rate or 0),
                    "current_stock_value": float(row.stock_value or 0),
                    "target_rate": target_rate,
                    "target_stock_value": float(row.actual_qty or 0) * target_rate,
                    "delta_value": delta_value,
                    "standard_buying_mmob": target["standard_buying_mmob"],
                    "latest_incoming": target["latest_incoming"],
                    "peer_rates": target["peer_rates"],
                    "candidate_rates": target["candidate_rates"],
                }
            )
        except Exception as exc:
            failed.append(
                {
                    "item_code": row.item_code,
                    "warehouse": row.warehouse,
                    "error": str(exc),
                }
            )

    net_delta = sum(row["delta_value"] for row in candidates)
    return {
        "status": "ok",
        "candidate_count": len(candidates),
        "failed_count": len(failed),
        "net_delta_value": net_delta,
        "candidates": candidates,
        "failed": failed,
    }


def apply_current_stock_valuation_normalization_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    posting_date = "2026-04-30"
    posting_time = "23:59:59"
    equity_account = "Retained Earnings - MMOB"
    result: dict[str, Any] = {
        "status": "ok",
        "stock_reconciliations": [],
        "journal_entry": None,
        "failed": [],
    }

    audit = audit_current_stock_valuation_normalization_candidates()
    candidates = audit["candidates"]
    if not candidates:
        result["audit_after"] = audit
        return result

    for row in candidates:
        try:
            reconciliation_name = _create_stock_reconciliation(
                company=company,
                item_code=row["item_code"],
                warehouse=row["warehouse"],
                posting_date=posting_date,
                qty=row["qty"],
                valuation_rate=row["target_rate"],
                posting_time=posting_time,
                remarks="April 2026 final cutoff stock valuation normalization for warehouse realism.",
            )
            frappe.db.commit()
            result["stock_reconciliations"].append(
                {
                    "stock_reconciliation": reconciliation_name,
                    **row,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "item_code": row["item_code"],
                    "warehouse": row["warehouse"],
                    "stage": "stock_reconciliation",
                    "error": str(exc),
                }
            )

    if result["failed"]:
        result["audit_after"] = audit_current_stock_valuation_normalization_candidates()
        return result

    stock_adjustment_account = _company_stock_adjustment_account(company)
    cost_center = _company_cost_center(company)
    net_delta = sum(row["delta_value"] for row in result["stock_reconciliations"])
    if abs(net_delta) >= 0.01:
        user_remark = f"Current-period stock valuation normalization reclass to equity @ {posting_date} {posting_time}"
        if net_delta > 0:
            accounts = [
                {
                    "account": stock_adjustment_account,
                    "debit_in_account_currency": abs(net_delta),
                    "cost_center": cost_center,
                },
                {
                    "account": equity_account,
                    "credit_in_account_currency": abs(net_delta),
                },
            ]
        else:
            accounts = [
                {
                    "account": equity_account,
                    "debit_in_account_currency": abs(net_delta),
                },
                {
                    "account": stock_adjustment_account,
                    "credit_in_account_currency": abs(net_delta),
                    "cost_center": cost_center,
                },
            ]
        try:
            journal_name = _create_simple_journal_entry(
                {
                    "company": company,
                    "posting_date": posting_date,
                    "voucher_type": "Journal Entry",
                    "user_remark": user_remark,
                    "accounts": accounts,
                }
            )
            frappe.db.commit()
            result["journal_entry"] = {
                "journal_entry": journal_name,
                "net_delta_value": net_delta,
                "equity_account": equity_account,
                "stock_adjustment_account": stock_adjustment_account,
            }
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "stage": "journal_entry",
                    "error": str(exc),
                    "net_delta_value": net_delta,
                }
            )

    result["audit_after"] = audit_current_stock_valuation_normalization_candidates()
    return result


def _net_account_movement_for_vouchers(
    voucher_names: list[str],
    voucher_types: list[str],
    account: str,
) -> float:
    if not voucher_names or not voucher_types:
        return 0.0
    name_placeholders = ", ".join(["%s"] * len(voucher_names))
    type_placeholders = ", ".join(["%s"] * len(voucher_types))
    rows = frappe.db.sql(
        f"""
        select ifnull(sum(debit - credit), 0)
        from `tabGL Entry`
        where voucher_no in ({name_placeholders})
          and voucher_type in ({type_placeholders})
          and account = %s
        """,
        tuple(voucher_names) + tuple(voucher_types) + (account,),
    )
    return float(rows[0][0] or 0) if rows else 0.0


def apply_stock_valuation_cleanup_reclass_and_residue_fix() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    posting_date = "2026-04-30"
    posting_time = "23:59:59"
    stock_adjustment_account = "Stock Adjustment - MMOB"
    equity_account = "Retained Earnings - MMOB"
    cost_center = _company_cost_center(company)
    result: dict[str, Any] = {
        "status": "ok",
        "residue_reconciliation": None,
        "journal_entry": None,
    }

    residue_name = _create_stock_reconciliation(
        company=company,
        item_code="SPH-XMI-RN13-8/256",
        warehouse="Yangon Showroom Counter - MMOB",
        posting_date=posting_date,
        qty=0,
        valuation_rate=0,
        posting_time=posting_time,
        remarks="April 2026 zero-qty stock value residue cleanup for showroom inventory.",
    )
    frappe.db.commit()
    result["residue_reconciliation"] = residue_name

    cleanup_reconciliations = [f"MAT-RECO-2026-00{num}" for num in range(363, 376)]
    posted_recons = [
        name
        for name in cleanup_reconciliations
        if frappe.db.exists("Stock Reconciliation", name)
    ]
    posted_jes = [
        name
        for name in ["ACC-JV-2026-00211", "ACC-JV-2026-00212"]
        if frappe.db.exists("Journal Entry", name)
    ]

    stock_adjustment_net = 0.0
    if posted_recons:
        stock_adjustment_net += _net_account_movement_for_vouchers(
            posted_recons,
            ["Stock Reconciliation"],
            stock_adjustment_account,
        )
    if posted_jes:
        stock_adjustment_net += _net_account_movement_for_vouchers(
            posted_jes,
            ["Journal Entry"],
            stock_adjustment_account,
        )

    user_remark = "April 2026 stock valuation cleanup exact GL reclass to retained earnings"
    if abs(stock_adjustment_net) >= 0.01:
        if stock_adjustment_net > 0:
            accounts = [
                {
                    "account": equity_account,
                    "debit_in_account_currency": abs(stock_adjustment_net),
                },
                {
                    "account": stock_adjustment_account,
                    "credit_in_account_currency": abs(stock_adjustment_net),
                    "cost_center": cost_center,
                },
            ]
        else:
            accounts = [
                {
                    "account": stock_adjustment_account,
                    "debit_in_account_currency": abs(stock_adjustment_net),
                    "cost_center": cost_center,
                },
                {
                    "account": equity_account,
                    "credit_in_account_currency": abs(stock_adjustment_net),
                },
            ]
        journal_name = _create_simple_journal_entry(
            {
                "company": company,
                "posting_date": posting_date,
                "voucher_type": "Journal Entry",
                "user_remark": user_remark,
                "accounts": accounts,
            }
        )
        frappe.db.commit()
        result["journal_entry"] = {
            "journal_entry": journal_name,
            "stock_adjustment_net_before_reclass": stock_adjustment_net,
        }

    zero_qty_residue = frappe.db.sql(
        """
        select item_code, warehouse, actual_qty, valuation_rate, stock_value
        from `tabBin`
        where abs(actual_qty) < 0.0001 and abs(stock_value) > 0.01
        order by abs(stock_value) desc, item_code, warehouse
        """,
        as_dict=True,
    )
    result["post_check"] = {
        "zero_qty_residue_count": len(zero_qty_residue),
        "zero_qty_residue": zero_qty_residue,
        "stock_adjustment_net_after_reclass": _net_account_movement_for_vouchers(
            posted_recons,
            ["Stock Reconciliation"],
            stock_adjustment_account,
        )
        + _net_account_movement_for_vouchers(
            [name for name in ["ACC-JV-2026-00211", "ACC-JV-2026-00212", result["journal_entry"]["journal_entry"]] if name],
            ["Journal Entry"],
            stock_adjustment_account,
        )
        if result["journal_entry"]
        else stock_adjustment_net,
    }
    return result


def apply_april_2026_targeted_commercial_uplift_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    result: dict[str, Any] = {
        "procurement_lanes": [],
        "sales_orders": [],
        "delivery_notes": [],
        "sales_invoices": [],
        "payment_entries": [],
        "supplier_payments": [],
        "failed": [],
    }

    procurement_lanes = [
        {
            "label": "april_2026_myanmar_tech_handset_support",
            "purchase_order": {
                "supplier": "Myanmar Tech Import Services",
                "company": company,
                "transaction_date": "2026-04-15",
                "schedule_date": "2026-04-15",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": "Yangon Main Warehouse - MMOB",
                "remarks": "April 2026 handset support replenishment ahead of late-month wholesale uplift and current pipeline coverage.",
                "items": [
                    {
                        "item_code": "SPH-XMI-RN13-8/256",
                        "qty": 10,
                        "rate": 705000,
                        "warehouse": "Yangon Main Warehouse - MMOB",
                    },
                    {
                        "item_code": "SPH-SAM-A15-6/128",
                        "qty": 8,
                        "rate": 785000,
                        "warehouse": "Yangon Main Warehouse - MMOB",
                    },
                    {
                        "item_code": "SPH-APP-IP14-128",
                        "qty": 4,
                        "rate": 2350000,
                        "warehouse": "Yangon Main Warehouse - MMOB",
                    },
                ],
            },
            "purchase_receipt": {
                "supplier": "Myanmar Tech Import Services",
                "posting_date": "2026-04-15",
                "posting_time": "11:30:00",
                "supplier_delivery_note": "MTI-DN-260415-02",
                "remarks": "Myanmar Tech late-April handset receipt for late-month customer replenishment continuity.",
            },
            "purchase_invoice": {
                "posting_date": "2026-04-15",
                "posting_time": "15:10:00",
                "bill_no": "MTI-INV-2604-152",
                "bill_date": "2026-04-15",
                "due_date": "2026-05-15",
                "remarks": "Myanmar Tech late-April handset supplier invoice / 30-day credit.",
            },
        },
        {
            "label": "april_2026_sunflower_fast_mover_support",
            "purchase_order": {
                "supplier": "Sunflower Accessories Co.",
                "company": company,
                "transaction_date": "2026-04-15",
                "schedule_date": "2026-04-15",
                "payment_terms_template": "15 Days - MMOB",
                "set_warehouse": "Yangon Main Warehouse - MMOB",
                "remarks": "April 2026 fast-mover accessory support replenishment after mid-month sales and current-window expansion.",
                "items": [
                    {
                        "item_code": "ACC-PWB-BAS-20K",
                        "qty": 80,
                        "rate": 82000,
                        "warehouse": "Yangon Main Warehouse - MMOB",
                    },
                    {
                        "item_code": "ACC-CHR-XMI-33W",
                        "qty": 120,
                        "rate": 23000,
                        "warehouse": "Yangon Main Warehouse - MMOB",
                    },
                    {
                        "item_code": "ACC-CBL-BAS-TC1M",
                        "qty": 200,
                        "rate": 5500,
                        "warehouse": "Yangon Main Warehouse - MMOB",
                    },
                ],
            },
            "purchase_receipt": {
                "supplier": "Sunflower Accessories Co.",
                "posting_date": "2026-04-15",
                "posting_time": "10:50:00",
                "supplier_delivery_note": "SFL-DN-260415-02",
                "remarks": "Sunflower late-April fast-mover accessory receipt for Yangon wholesale replenishment.",
            },
            "purchase_invoice": {
                "posting_date": "2026-04-15",
                "posting_time": "15:30:00",
                "bill_no": "SFL-INV-2604-152",
                "bill_date": "2026-04-15",
                "due_date": "2026-04-30",
                "remarks": "Sunflower late-April accessory supplier invoice / 15-day credit.",
            },
        },
    ]

    sales_chain_specs = [
        {
            "label": "april_2026_capital_key_account_release",
            "customer": "Capital Telecom (NPT)",
            "items": [
                {
                    "item_code": "SPH-XMI-RN13-8/256",
                    "qty": 8,
                    "rate": 930000,
                    "warehouse": "Yangon Main Warehouse - MMOB",
                },
                {
                    "item_code": "SPH-SAM-A15-6/128",
                    "qty": 6,
                    "rate": 890000,
                    "warehouse": "Yangon Main Warehouse - MMOB",
                },
                {
                    "item_code": "ACC-PWB-BAS-20K",
                    "qty": 40,
                    "rate": 88000,
                    "warehouse": "Yangon Main Warehouse - MMOB",
                },
                {
                    "item_code": "ACC-CHR-XMI-33W",
                    "qty": 60,
                    "rate": 25000,
                    "warehouse": "Yangon Main Warehouse - MMOB",
                },
                {
                    "item_code": "ACC-CBL-BAS-TC1M",
                    "qty": 40,
                    "rate": 7000,
                    "warehouse": "Yangon Main Warehouse - MMOB",
                },
            ],
            "sales_order": {
                "transaction_date": "2026-04-26",
                "delivery_date": "2026-04-27",
                "po_no": "CAP-NPT-0426-02",
                "po_date": "2026-04-26",
                "payment_terms_template": "45 Days Approved - MMOB",
                "set_warehouse": "Yangon Main Warehouse - MMOB",
                "remarks": "April 2026 key-account release for Capital Telecom separate from the larger approval-blocked tender-sized order.",
            },
            "delivery_note": {
                "posting_date": "2026-04-27",
                "posting_time": "13:40:00",
                "remarks": "April 2026 Capital Telecom key-account dispatch after release of ordinary replenishment lot.",
            },
            "sales_invoice": {
                "posting_date": "2026-04-27",
                "posting_time": "14:00:00",
                "due_date": "2026-06-11",
                "payment_terms_template": "45 Days Approved - MMOB",
                "remarks": "April 2026 Capital Telecom invoice for released ordinary replenishment lot on approved credit terms.",
            },
        },
        {
            "label": "april_2026_bayint_repeat_wholesale",
            "customer": "Bayint Naung Wholesale Mobile",
            "items": [
                {
                    "item_code": "SPH-SAM-A15-6/128",
                    "qty": 8,
                    "rate": 900000,
                    "warehouse": "Yangon Main Warehouse - MMOB",
                },
                {
                    "item_code": "SPH-XMI-RN13-8/256",
                    "qty": 6,
                    "rate": 940000,
                    "warehouse": "Yangon Main Warehouse - MMOB",
                },
                {
                    "item_code": "ACC-PWB-BAS-20K",
                    "qty": 25,
                    "rate": 90000,
                    "warehouse": "Yangon Main Warehouse - MMOB",
                },
                {
                    "item_code": "ACC-CHR-XMI-33W",
                    "qty": 40,
                    "rate": 26000,
                    "warehouse": "Yangon Main Warehouse - MMOB",
                },
                {
                    "item_code": "ACC-CBL-BAS-TC1M",
                    "qty": 36,
                    "rate": 7500,
                    "warehouse": "Yangon Main Warehouse - MMOB",
                },
            ],
            "sales_order": {
                "transaction_date": "2026-04-28",
                "delivery_date": "2026-04-28",
                "po_no": "BYNT-0428-02",
                "po_date": "2026-04-28",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": "Yangon Main Warehouse - MMOB",
                "remarks": "April 2026 repeat Bayint wholesale replenishment after earlier April sell-through.",
            },
            "delivery_note": {
                "posting_date": "2026-04-28",
                "posting_time": "15:20:00",
                "remarks": "April 2026 Bayint repeat wholesale dispatch for late-month mixed handset and accessory restock.",
            },
            "sales_invoice": {
                "posting_date": "2026-04-28",
                "posting_time": "15:40:00",
                "due_date": "2026-05-28",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "April 2026 Bayint repeat wholesale invoice on normal 30-day terms.",
            },
        },
        {
            "label": "april_2026_mandalay_accessories_second_cycle",
            "customer": "Mandalay Accessories Wholesale",
            "items": [
                {
                    "item_code": "SPH-SAM-A15-6/128",
                    "qty": 4,
                    "rate": 900000,
                    "warehouse": "Mandalay Warehouse - MMOB",
                },
                {
                    "item_code": "SPH-XMI-RN13-8/256",
                    "qty": 2,
                    "rate": 940000,
                    "warehouse": "Mandalay Warehouse - MMOB",
                },
                {
                    "item_code": "ACC-PWB-BAS-20K",
                    "qty": 12,
                    "rate": 90000,
                    "warehouse": "Mandalay Warehouse - MMOB",
                },
                {
                    "item_code": "ACC-CHR-XMI-33W",
                    "qty": 20,
                    "rate": 26000,
                    "warehouse": "Mandalay Warehouse - MMOB",
                },
                {
                    "item_code": "ACC-CBL-BAS-TC1M",
                    "qty": 20,
                    "rate": 7500,
                    "warehouse": "Mandalay Warehouse - MMOB",
                },
            ],
            "sales_order": {
                "transaction_date": "2026-04-29",
                "delivery_date": "2026-04-29",
                "po_no": "MAW-MDY-0429-02",
                "po_date": "2026-04-29",
                "payment_terms_template": "15 Days - MMOB",
                "set_warehouse": "Mandalay Warehouse - MMOB",
                "remarks": "April 2026 second-cycle Mandalay mixed order for Mandalay Accessories Wholesale after the earlier April lot moved quickly.",
            },
            "delivery_note": {
                "posting_date": "2026-04-29",
                "posting_time": "11:10:00",
                "remarks": "April 2026 Mandalay Accessories second-cycle dispatch for mixed handset and accessory replenishment.",
            },
            "sales_invoice": {
                "posting_date": "2026-04-29",
                "posting_time": "11:30:00",
                "due_date": "2026-05-14",
                "payment_terms_template": "15 Days - MMOB",
                "remarks": "April 2026 Mandalay Accessories second-cycle invoice on 15-day terms.",
            },
        },
    ]

    direct_sales_defs = [
        {
            "customer": "City Mobile Mart",
            "posting_date": "2026-04-30",
            "due_date": "2026-04-30",
            "warehouse": "Yangon Showroom Counter - MMOB",
            "company": company,
            "remarks": "April 2026 month-end showroom bundle billed and settled same day for City Mobile Mart.",
            "items": [
                {"item_code": "SPH-APP-IP14-128", "qty": 1, "rate": 2500000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 1, "rate": 960000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 4, "rate": 95000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 28000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 10, "rate": 8000},
            ],
        },
    ]

    for lane in procurement_lanes:
        try:
            lane["purchase_order"]["expected_total"] = _sum_item_amounts(lane["purchase_order"]["items"])
            po_name = _create_purchase_order(lane["purchase_order"])
            pr_name = _create_purchase_receipt_from_order(po_name, lane["purchase_receipt"])
            pi_name = _create_purchase_invoice_from_receipt(
                pr_name,
                lane["purchase_order"]["supplier"],
                lane["purchase_order"].get("payment_terms_template"),
                lane["purchase_invoice"],
            )
            frappe.db.commit()
            result["procurement_lanes"].append(
                {
                    "label": lane["label"],
                    "purchase_order": po_name,
                    "purchase_receipt": pr_name,
                    "purchase_invoice": pi_name,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": lane["label"], "stage": "procurement", "error": str(exc)})

    invoice_lookup: dict[tuple[str, str], str] = {}
    purchase_invoice_lookup = {
        row["label"]: row["purchase_invoice"] for row in result["procurement_lanes"]
    }

    for spec in sales_chain_specs:
        try:
            expected_total = _sum_item_amounts(spec["items"])
            sales_order_name = _create_sales_order(
                {
                    **spec["sales_order"],
                    "customer": spec["customer"],
                    "company": company,
                    "expected_total": expected_total,
                    "items": spec["items"],
                }
            )
            delivery_note_name = _create_delivery_note_from_sales_order(sales_order_name, spec["delivery_note"])
            sales_invoice_name = _create_sales_invoice_from_delivery_note(
                delivery_note_name,
                spec["sales_invoice"],
            )
            invoice_lookup[(spec["customer"], spec["sales_invoice"]["posting_date"])] = sales_invoice_name
            frappe.db.commit()
            result["sales_orders"].append({"label": spec["label"], "sales_order": sales_order_name})
            result["delivery_notes"].append({"label": spec["label"], "delivery_note": delivery_note_name})
            result["sales_invoices"].append({"label": spec["label"], "sales_invoice": sales_invoice_name})
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "stage": "sales_chain", "error": str(exc)})

    for definition in direct_sales_defs:
        try:
            definition["expected_total"] = _sum_item_amounts(definition["items"])
            invoice_name = _create_sales_invoice(definition)
            invoice_lookup[(definition["customer"], definition["posting_date"])] = invoice_name
            frappe.db.commit()
            result["sales_invoices"].append(
                {
                    "label": f"direct_{definition['customer']}_{definition['posting_date']}",
                    "sales_invoice": invoice_name,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"direct_{definition['customer']}_{definition['posting_date']}",
                    "stage": "direct_sales",
                    "error": str(exc),
                }
            )

    payment_specs = [
        ("Bayint Naung Wholesale Mobile", "2026-04-28", "2026-04-30", 3000000),
        ("Mandalay Accessories Wholesale", "2026-04-29", "2026-04-30", 2000000),
        ("City Mobile Mart", "2026-04-30", "2026-04-30", 4200000),
    ]

    for customer, invoice_date, payment_date, amount in payment_specs:
        try:
            invoice_name = invoice_lookup[(customer, invoice_date)]
            payment_name = _create_partial_payment_with_date_dedupe(
                "Sales Invoice", invoice_name, payment_date, amount
            )
            frappe.db.commit()
            result["payment_entries"].append(
                {
                    "customer": customer,
                    "sales_invoice": invoice_name,
                    "payment_entry": payment_name,
                    "amount": amount,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"label": f"receipt_{customer}_{invoice_date}", "stage": "receipt", "error": str(exc)}
            )

    supplier_payment_specs = [
        ("april_2026_myanmar_tech_handset_support", "2026-04-30", 5000000),
        ("april_2026_sunflower_fast_mover_support", "2026-04-30", 3000000),
    ]

    for lane_label, payment_date, amount in supplier_payment_specs:
        try:
            invoice_name = purchase_invoice_lookup[lane_label]
            payment_name = _create_partial_payment_with_date_dedupe(
                "Purchase Invoice", invoice_name, payment_date, amount
            )
            frappe.db.commit()
            result["supplier_payments"].append(
                {
                    "purchase_invoice": invoice_name,
                    "payment_entry": payment_name,
                    "amount": amount,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"supplier_payment_{lane_label}",
                    "stage": "supplier_payment",
                    "error": str(exc),
                }
            )

    return result


def apply_april_2026_ap_return_normalization_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    supplier = "Myanmar Tech Import Services"
    source_invoice_name = "ACC-PINV-2026-00281"
    return_invoice_name = "ACC-PINV-2026-00314"
    result: dict[str, Any] = {"updated": [], "reconciliation": None, "failed": []}

    if not frappe.db.exists("Purchase Invoice", source_invoice_name):
        return {"updated": [], "reconciliation": None, "failed": [{"error": f"missing_{source_invoice_name}"}]}
    if not frappe.db.exists("Purchase Invoice", return_invoice_name):
        return {"updated": [], "reconciliation": None, "failed": [{"error": f"missing_{return_invoice_name}"}]}

    try:
        frappe.db.set_value(
            "Purchase Invoice",
            source_invoice_name,
            {
                "due_date": "2026-04-13",
                "remarks": "April 2026 Myanmar Tech importer invoice for handset batch later fully returned after transit damage review.",
            },
            update_modified=False,
        )
        result["updated"].append({"purchase_invoice": source_invoice_name, "change_type": "due_date_and_remarks"})

        frappe.db.set_value(
            "Purchase Invoice",
            return_invoice_name,
            {
                "due_date": "2026-04-14",
                "remarks": "April 2026 Myanmar Tech full supplier debit note for the damaged transit batch returned in full.",
            },
            update_modified=False,
        )
        result["updated"].append({"purchase_invoice": return_invoice_name, "change_type": "due_date_and_remarks"})
        frappe.db.commit()
    except Exception as exc:
        frappe.db.rollback()
        result["failed"].append({"stage": "metadata_update", "error": str(exc)})
        return result

    try:
        from ai_assistant_ui.ops.dummy_data_controls import _reconcile_return_note_against_invoice

        reconciliation_result = _reconcile_return_note_against_invoice(
            company,
            "Supplier",
            supplier,
            "Purchase Invoice",
            source_invoice_name,
            return_invoice_name,
            "2026-04-14",
        )
        frappe.db.commit()
        result["reconciliation"] = reconciliation_result
    except Exception as exc:
        frappe.db.rollback()
        result["failed"].append({"stage": "reconciliation", "error": str(exc)})

    return result


def apply_q1_stabilization_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    result: dict[str, Any] = {
        "customer_receipts": [],
        "supplier_payments": [],
        "stock_reconciliations": [],
        "failed": [],
    }

    customer_receipt_specs = [
        ("ACC-SINV-2026-00727", "2025-05-20", 5000000),
        ("ACC-SINV-2026-00727", "2025-06-18", 6740000),
        ("ACC-SINV-2026-00728", "2025-05-28", 4000000),
        ("ACC-SINV-2026-00728", "2025-06-25", 5900000),
        ("ACC-SINV-2026-00725", "2025-06-05", 4000000),
        ("ACC-SINV-2026-00725", "2025-07-10", 4770000),
        ("ACC-SINV-2026-00723", "2025-05-25", 3000000),
        ("ACC-SINV-2026-00723", "2025-06-20", 3460000),
        ("ACC-SINV-2026-00726", "2025-05-08", 1490000),
    ]

    supplier_payment_specs = [
        ("ACC-PINV-2026-00315", "2025-05-05", 8000000),
        ("ACC-PINV-2026-00315", "2025-05-28", 8000000),
        ("ACC-PINV-2026-00315", "2025-06-25", 7400000),
        ("ACC-PINV-2026-00316", "2025-05-12", 6000000),
        ("ACC-PINV-2026-00316", "2025-06-10", 6000000),
        ("ACC-PINV-2026-00316", "2025-07-05", 5400000),
        ("ACC-PINV-2026-00317", "2025-05-14", 4000000),
        ("ACC-PINV-2026-00317", "2025-06-14", 5580000),
    ]

    valuation_targets = [
        ("SPH-SAM-A15-6/128", "Yangon Main Warehouse - MMOB", 880000),
        ("SPH-XMI-RN13-8/256", "Mandalay Warehouse - MMOB", 735000),
        ("SPH-APP-IP13-128", "Mandalay Warehouse - MMOB", 1820000),
        ("SPH-APP-IP14-128", "Mandalay Warehouse - MMOB", 2350000),
    ]

    for invoice_name, posting_date, amount in customer_receipt_specs:
        try:
            doc = frappe.get_doc("Sales Invoice", invoice_name)
            outstanding = float(doc.outstanding_amount or 0)
            if outstanding <= 0:
                continue
            rounded_amount = min(float(amount), outstanding)
            payment_name = _create_partial_payment_with_date_dedupe(
                "Sales Invoice", invoice_name, posting_date, rounded_amount
            )
            result["customer_receipts"].append(
                {
                    "reference_doctype": "Sales Invoice",
                    "reference_name": invoice_name,
                    "payment_entry": payment_name,
                    "amount": rounded_amount,
                }
            )
            if rounded_amount > 0:
                frappe.db.commit()
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"label": f"customer_receipt_{invoice_name}_{posting_date}", "error": str(exc)}
            )

    for invoice_name, posting_date, amount in supplier_payment_specs:
        try:
            doc = frappe.get_doc("Purchase Invoice", invoice_name)
            outstanding = float(doc.outstanding_amount or 0)
            if outstanding <= 0:
                continue
            rounded_amount = min(float(amount), outstanding)
            payment_name = _create_partial_payment_with_date_dedupe(
                "Purchase Invoice", invoice_name, posting_date, rounded_amount
            )
            result["supplier_payments"].append(
                {
                    "reference_doctype": "Purchase Invoice",
                    "reference_name": invoice_name,
                    "payment_entry": payment_name,
                    "amount": rounded_amount,
                }
            )
            if rounded_amount > 0:
                frappe.db.commit()
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"label": f"supplier_payment_{invoice_name}_{posting_date}", "error": str(exc)}
            )

    for item_code, warehouse, target_rate in valuation_targets:
        try:
            bin_row = frappe.db.sql(
                """
                select actual_qty, valuation_rate
                from `tabBin`
                where item_code = %s and warehouse = %s
                limit 1
                """,
                (item_code, warehouse),
                as_dict=True,
            )
            if not bin_row:
                result["failed"].append(
                    {"label": f"valuation_{item_code}_{warehouse}", "error": "missing_bin"}
                )
                continue
            qty = float(bin_row[0]["actual_qty"] or 0)
            current_rate = float(bin_row[0]["valuation_rate"] or 0)
            if qty <= 0:
                continue
            if abs(current_rate - float(target_rate)) < 0.01:
                continue
            reconciliation_name = _create_stock_reconciliation(
                company=company,
                item_code=item_code,
                warehouse=warehouse,
                posting_date="2026-03-31",
                qty=qty,
                valuation_rate=float(target_rate),
            )
            frappe.db.commit()
            result["stock_reconciliations"].append(
                {
                    "stock_reconciliation": reconciliation_name,
                    "item_code": item_code,
                    "warehouse": warehouse,
                    "qty": qty,
                    "from_valuation_rate": current_rate,
                    "to_valuation_rate": float(target_rate),
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"label": f"valuation_{item_code}_{warehouse}", "error": str(exc)}
            )

    return result


def apply_may_2025_commercial_rebalance_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    warehouse = "Yangon Main Warehouse - MMOB"

    credit_limit_targets = {
        "Bayint Naung Wholesale Mobile": 220000000,
        "Capital Telecom (NPT)": 160000000,
        "Ko Nay Lin Mobile Center": 75000000,
        "Mandalay Accessories Wholesale": 50000000,
        "Bago Myoma Phone Shop": 10000000,
    }

    procurement_lanes = [
        {
            "label": "may_golden_dragon_wholesale_handset_lane",
            "purchase_order": {
                "supplier": "Golden Dragon Trading Co. Ltd.",
                "company": company,
                "transaction_date": "2025-05-04",
                "schedule_date": "2025-05-06",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "May handset-led replenishment for repeat wholesale demand after April opening-month sell-through.",
                "items": [
                    {"item_code": "SPH-SAM-A15-6/128", "qty": 12, "rate": 840000, "warehouse": warehouse},
                    {"item_code": "SPH-XMI-RN13-8/256", "qty": 10, "rate": 705000, "warehouse": warehouse},
                    {"item_code": "ACC-CHR-XMI-33W", "qty": 80, "rate": 20000, "warehouse": warehouse},
                ],
            },
            "purchase_receipt": {
                "supplier": "Golden Dragon Trading Co. Ltd.",
                "posting_date": "2025-05-06",
                "posting_time": "11:30:00",
                "supplier_delivery_note": "GD-DN-250506-01",
                "remarks": "Golden Dragon May handset-led replenishment arrival for Yangon wholesale lanes.",
            },
            "purchase_invoice": {
                "posting_date": "2025-05-07",
                "posting_time": "15:20:00",
                "bill_no": "GD-INV-2505-053",
                "bill_date": "2025-05-06",
                "due_date": "2025-06-05",
                "remarks": "Golden Dragon May handset replenishment invoice / standard 30-day supplier credit.",
            },
        },
        {
            "label": "may_sunflower_accessory_lane",
            "purchase_order": {
                "supplier": "Sunflower Accessories Co.",
                "company": company,
                "transaction_date": "2025-05-11",
                "schedule_date": "2025-05-12",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "May accessories replenishment supporting mixed handset bundle selling and township repeat demand.",
                "items": [
                    {"item_code": "ACC-PWB-BAS-20K", "qty": 120, "rate": 78000, "warehouse": warehouse},
                    {"item_code": "ACC-CHR-SAM-25W", "qty": 150, "rate": 25000, "warehouse": warehouse},
                    {"item_code": "ACC-CBL-BAS-TC1M", "qty": 200, "rate": 5000, "warehouse": warehouse},
                    {"item_code": "MEM-MSD-SND-128", "qty": 120, "rate": 18000, "warehouse": warehouse},
                ],
            },
            "purchase_receipt": {
                "supplier": "Sunflower Accessories Co.",
                "posting_date": "2025-05-12",
                "posting_time": "12:00:00",
                "supplier_delivery_note": "SFL-DN-250512-01",
                "remarks": "Sunflower May accessories arrival for ordinary replenishment and mixed-bundle sales.",
            },
            "purchase_invoice": {
                "posting_date": "2025-05-13",
                "posting_time": "16:00:00",
                "bill_no": "SFL-INV-2505-044",
                "bill_date": "2025-05-12",
                "due_date": "2025-06-11",
                "remarks": "Sunflower May accessory invoice / standard 30-day supplier credit.",
            },
        },
        {
            "label": "may_early_powerbank_topup",
            "purchase_order": {
                "supplier": "Sunflower Accessories Co.",
                "company": company,
                "transaction_date": "2025-05-08",
                "schedule_date": "2025-05-09",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "Small early-May power-bank top-up to support the first Bayint repeat wholesale dispatch.",
                "items": [
                    {"item_code": "ACC-PWB-BAS-20K", "qty": 30, "rate": 78000, "warehouse": warehouse},
                ],
            },
            "purchase_receipt": {
                "supplier": "Sunflower Accessories Co.",
                "posting_date": "2025-05-09",
                "posting_time": "10:40:00",
                "supplier_delivery_note": "SFL-DN-250509-01",
                "remarks": "Sunflower early-May power-bank buffer arrival before the first repeat wholesale dispatch.",
            },
            "purchase_invoice": {
                "posting_date": "2025-05-09",
                "posting_time": "15:10:00",
                "bill_no": "SFL-INV-2505-039",
                "bill_date": "2025-05-09",
                "due_date": "2025-06-08",
                "remarks": "Sunflower early-May power-bank top-up invoice / 30-day supplier credit.",
            },
        },
        {
            "label": "may_early_xiaomi_charger_topup",
            "purchase_order": {
                "supplier": "Sunflower Accessories Co.",
                "company": company,
                "transaction_date": "2025-05-09",
                "schedule_date": "2025-05-09",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "Small early-May Xiaomi charger top-up to support first repeat wholesale dispatches.",
                "items": [
                    {"item_code": "ACC-CHR-XMI-33W", "qty": 50, "rate": 20000, "warehouse": warehouse},
                ],
            },
            "purchase_receipt": {
                "supplier": "Sunflower Accessories Co.",
                "posting_date": "2025-05-09",
                "posting_time": "11:20:00",
                "supplier_delivery_note": "SFL-DN-250509-02",
                "remarks": "Sunflower early-May Xiaomi charger top-up arrival for opening repeat wholesale demand.",
            },
            "purchase_invoice": {
                "posting_date": "2025-05-09",
                "posting_time": "15:30:00",
                "bill_no": "SFL-INV-2505-040",
                "bill_date": "2025-05-09",
                "due_date": "2025-06-08",
                "remarks": "Sunflower early-May Xiaomi charger top-up invoice / 30-day supplier credit.",
            },
        },
        {
            "label": "may_myanmar_tech_apple_topup",
            "purchase_order": {
                "supplier": "Myanmar Tech Import Services",
                "company": company,
                "transaction_date": "2025-05-19",
                "schedule_date": "2025-05-21",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "May Apple and premium accessory top-up for key-account and Mandalay-lane demand.",
                "items": [
                    {"item_code": "SPH-APP-IP13-128", "qty": 4, "rate": 1735000, "warehouse": warehouse},
                    {"item_code": "SPH-APP-IP14-128", "qty": 2, "rate": 2210000, "warehouse": warehouse},
                    {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 40, "rate": 42000, "warehouse": warehouse},
                ],
            },
            "purchase_receipt": {
                "supplier": "Myanmar Tech Import Services",
                "posting_date": "2025-05-21",
                "posting_time": "11:10:00",
                "supplier_delivery_note": "MTI-DN-250521-01",
                "remarks": "Myanmar Tech May premium-device top-up arrival for key-account lanes.",
            },
            "purchase_invoice": {
                "posting_date": "2025-05-22",
                "posting_time": "15:00:00",
                "bill_no": "MTI-INV-2505-027",
                "bill_date": "2025-05-21",
                "due_date": "2025-06-20",
                "remarks": "Myanmar Tech May premium-device top-up invoice / 30-day supplier credit.",
            },
        },
        {
            "label": "may_sunflower_fast_mover_buffer",
            "purchase_order": {
                "supplier": "Sunflower Accessories Co.",
                "company": company,
                "transaction_date": "2025-05-15",
                "schedule_date": "2025-05-16",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "May fast-mover buffer replenishment to support repeat power-bank, earbuds, cable, and flash-drive turnover.",
                "items": [
                    {"item_code": "ACC-PWB-BAS-20K", "qty": 40, "rate": 78000, "warehouse": warehouse},
                    {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 40, "rate": 42000, "warehouse": warehouse},
                    {"item_code": "ACC-CBL-UGR-TC1M", "qty": 80, "rate": 9000, "warehouse": warehouse},
                    {"item_code": "MEM-USB-SND-64", "qty": 100, "rate": 11800, "warehouse": warehouse},
                ],
            },
            "purchase_receipt": {
                "supplier": "Sunflower Accessories Co.",
                "posting_date": "2025-05-16",
                "posting_time": "12:15:00",
                "supplier_delivery_note": "SFL-DN-250516-01",
                "remarks": "Sunflower May fast-mover buffer arrival for accessory-led repeat selling.",
            },
            "purchase_invoice": {
                "posting_date": "2025-05-17",
                "posting_time": "16:10:00",
                "bill_no": "SFL-INV-2505-051",
                "bill_date": "2025-05-16",
                "due_date": "2025-06-15",
                "remarks": "Sunflower May fast-mover buffer invoice / 30-day supplier credit.",
            },
        },
    ]

    quotation_specs = [
        {
            "label": "may_bayint_repeat_quote",
            "customer": "Bayint Naung Wholesale Mobile",
            "transaction_date": "2025-05-07",
            "valid_till": "2025-05-10",
            "payment_terms_template": "30 Days - MMOB",
            "set_warehouse": warehouse,
            "remarks": "May Bayint repeat wholesale quotation for mixed handset and accessory replenishment.",
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 4, "rate": 1020000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 6, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 15, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
            ],
        },
        {
            "label": "may_ko_nay_lin_quote",
            "customer": "Ko Nay Lin Mobile Center",
            "transaction_date": "2025-05-14",
            "valid_till": "2025-05-17",
            "payment_terms_template": "30 Days - MMOB",
            "set_warehouse": warehouse,
            "remarks": "May Ko Nay Lin wholesale quotation for mixed handset and accessory restock.",
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 2, "rate": 2150000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 4, "rate": 1020000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
            ],
        },
        {
            "label": "may_latha_lost_quote",
            "customer": "Latha Mobile Wholesale",
            "transaction_date": "2025-05-10",
            "valid_till": "2025-05-13",
            "payment_terms_template": "30 Days - MMOB",
            "set_warehouse": warehouse,
            "target_status": "Lost",
            "remarks": "May price-sensitive wholesale quotation lost after competitor comparison and delayed confirmation.",
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 4, "rate": 1020000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 15, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 30, "rate": 8000},
            ],
        },
        {
            "label": "may_hledan_expired_quote",
            "customer": "Hledan Phone Hub",
            "transaction_date": "2025-05-22",
            "valid_till": "2025-05-25",
            "payment_terms_template": "30 Days - MMOB",
            "set_warehouse": warehouse,
            "target_status": "Expired",
            "remarks": "May small wholesale quotation that expired after the customer delayed final bundle confirmation.",
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 15, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
            ],
        },
    ]

    chain_specs = [
        {
            "label": "may_bayint_quote_chain",
            "customer": "Bayint Naung Wholesale Mobile",
            "quotation_label": "may_bayint_repeat_quote",
            "sales_order": {
                "transaction_date": "2025-05-09",
                "delivery_date": "2025-05-10",
                "po_no": "CPO-2025-05-201",
                "po_date": "2025-05-09",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "May Bayint repeat wholesale order converted from approved follow-up quotation.",
            },
            "delivery_note": {
                "posting_date": "2025-05-10",
                "posting_time": "11:40:00",
                "remarks": "May Bayint repeat wholesale dispatch after quote confirmation and stock release.",
            },
            "sales_invoice": {
                "posting_date": "2025-05-10",
                "posting_time": "12:00:00",
                "due_date": "2025-06-09",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "May Bayint wholesale invoice converted from approved quotation and dispatch.",
            },
        },
        {
            "label": "may_ko_nay_lin_quote_chain",
            "customer": "Ko Nay Lin Mobile Center",
            "quotation_label": "may_ko_nay_lin_quote",
            "sales_order": {
                "transaction_date": "2025-05-16",
                "delivery_date": "2025-05-17",
                "po_no": "CPO-2025-05-202",
                "po_date": "2025-05-16",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "May Ko Nay Lin wholesale order converted from negotiated mixed-product quotation.",
            },
            "delivery_note": {
                "posting_date": "2025-05-17",
                "posting_time": "13:20:00",
                "remarks": "May Ko Nay Lin mixed handset and accessory dispatch after quotation acceptance.",
            },
            "sales_invoice": {
                "posting_date": "2025-05-17",
                "posting_time": "13:40:00",
                "due_date": "2025-06-16",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "May Ko Nay Lin wholesale invoice converted from approved quotation and delivery.",
            },
        },
        {
            "label": "may_capital_direct_chain",
            "customer": "Capital Telecom (NPT)",
            "items": [
                {"item_code": "SPH-APP-IP14-128", "qty": 2, "rate": 2650000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 3, "rate": 1020000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 15, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 15, "rate": 30000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
            ],
            "sales_order": {
                "transaction_date": "2025-05-20",
                "delivery_date": "2025-05-22",
                "po_no": "CPO-2025-05-203",
                "po_date": "2025-05-20",
                "payment_terms_template": "45 Days Approved - MMOB",
                "set_warehouse": warehouse,
                "remarks": "May Capital Telecom direct key-account order confirmed without formal quotation stage.",
            },
            "delivery_note": {
                "posting_date": "2025-05-22",
                "posting_time": "14:10:00",
                "remarks": "May Capital Telecom dispatch after internal approval and stock confirmation.",
            },
            "sales_invoice": {
                "posting_date": "2025-05-22",
                "posting_time": "14:30:00",
                "due_date": "2025-07-06",
                "payment_terms_template": "45 Days Approved - MMOB",
                "remarks": "May Capital Telecom invoice issued after direct-order delivery release.",
            },
        },
        {
            "label": "may_mandalay_accessories_chain",
            "customer": "Mandalay Accessories Wholesale",
            "items": [
                {"item_code": "ACC-PWB-BAS-20K", "qty": 40, "rate": 110000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 50, "rate": 30000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 40, "rate": 32000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 40, "rate": 8000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
            ],
            "sales_order": {
                "transaction_date": "2025-05-26",
                "delivery_date": "2025-05-27",
                "po_no": "CPO-2025-05-204",
                "po_date": "2025-05-26",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "May accessories-heavy wholesale order placed directly by repeat Mandalay customer.",
            },
            "delivery_note": {
                "posting_date": "2025-05-27",
                "posting_time": "11:10:00",
                "remarks": "May Mandalay accessories-heavy dispatch after direct wholesale order confirmation.",
            },
            "sales_invoice": {
                "posting_date": "2025-05-27",
                "posting_time": "11:30:00",
                "due_date": "2025-06-26",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "May Mandalay accessories-heavy wholesale invoice after same-day dispatch.",
            },
        },
    ]

    direct_sales_defs = [
        {
            "customer": "Lanmadaw Telecom & Gadgets",
            "posting_date": "2025-05-29",
            "due_date": "2025-06-12",
            "warehouse": warehouse,
            "company": company,
            "remarks": "May small Lanmadaw replenishment billed directly without separate dispatch paperwork.",
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 8, "rate": 110000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 30000},
                {"item_code": "MEM-MSD-SND-128", "qty": 10, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 10, "rate": 16000},
            ],
        },
        {
            "customer": "Bago Myoma Phone Shop",
            "posting_date": "2025-05-30",
            "due_date": "2025-05-30",
            "warehouse": warehouse,
            "company": company,
            "remarks": "May small Bago township counter wholesale bundle settled as same-day billing.",
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 1, "rate": 1020000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 6, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 8, "rate": 32000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 8, "rate": 8000},
            ],
        },
    ]

    payment_specs = [
        ("Bayint Naung Wholesale Mobile", "2025-05-10", "2025-05-25", 4000000),
        ("Ko Nay Lin Mobile Center", "2025-05-17", "2025-06-05", 3000000),
        ("Capital Telecom (NPT)", "2025-05-22", "2025-06-12", 4000000),
        ("Mandalay Accessories Wholesale", "2025-05-27", "2025-06-20", 3000000),
        ("Lanmadaw Telecom & Gadgets", "2025-05-29", "2025-05-31", 2000000),
        ("Bago Myoma Phone Shop", "2025-05-30", "2025-05-30", 2000000),
    ]

    supplier_payment_specs = [
        ("may_golden_dragon_wholesale_handset_lane", "2025-05-28", 5000000),
        ("may_sunflower_accessory_lane", "2025-06-10", 4000000),
        ("may_early_powerbank_topup", "2025-06-05", 1000000),
        ("may_early_xiaomi_charger_topup", "2025-06-05", 1000000),
        ("may_myanmar_tech_apple_topup", "2025-06-18", 3000000),
        ("may_sunflower_fast_mover_buffer", "2025-06-20", 3000000),
    ]

    quotation_lookup: dict[str, str] = {}
    quotation_spec_lookup = {spec["label"]: spec for spec in quotation_specs}
    invoice_lookup: dict[tuple[str, str], str] = {}
    purchase_invoice_lookup: dict[str, str] = {}
    result = {
        "credit_limits": [],
        "procurement_lanes": [],
        "quotations": [],
        "sales_orders": [],
        "delivery_notes": [],
        "sales_invoices": [],
        "payment_entries": [],
        "supplier_payments": [],
        "failed": [],
    }

    for customer_name, credit_limit in credit_limit_targets.items():
        try:
            if not frappe.db.exists("Customer", customer_name):
                continue
            customer = frappe.get_doc("Customer", customer_name)
            limit_row = None
            for row in customer.credit_limits:
                if row.company == company:
                    limit_row = row
                    break
            current_outstanding = float(
                frappe.db.sql(
                    """
                    select ifnull(sum(outstanding_amount), 0)
                    from `tabSales Invoice`
                    where customer = %s and docstatus = 1 and outstanding_amount > 0
                    """,
                    (customer_name,),
                )[0][0]
                or 0
            )
            effective_credit_limit = max(float(credit_limit), current_outstanding + 5000000)
            if limit_row:
                limit_row.credit_limit = effective_credit_limit
                limit_row.bypass_credit_limit_check = 0
            else:
                customer.append(
                    "credit_limits",
                    {
                        "company": company,
                        "credit_limit": effective_credit_limit,
                        "bypass_credit_limit_check": 0,
                    },
                )
            customer.save(ignore_permissions=True)
            frappe.db.commit()
            result["credit_limits"].append({"customer": customer_name, "credit_limit": effective_credit_limit})
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"label": f"credit_limit_{customer_name}", "stage": "credit_limit", "error": str(exc)}
            )

    for lane in procurement_lanes:
        try:
            lane["purchase_order"]["expected_total"] = _sum_item_amounts(lane["purchase_order"]["items"])
            po_name = _create_purchase_order(lane["purchase_order"])
            pr_name = _create_purchase_receipt_from_order(po_name, lane["purchase_receipt"])
            pi_name = _create_purchase_invoice_from_receipt(
                pr_name,
                lane["purchase_order"]["supplier"],
                lane["purchase_order"].get("payment_terms_template"),
                lane["purchase_invoice"],
            )
            purchase_invoice_lookup[lane["label"]] = pi_name
            frappe.db.commit()
            result["procurement_lanes"].append(
                {
                    "label": lane["label"],
                    "purchase_order": po_name,
                    "purchase_receipt": pr_name,
                    "purchase_invoice": pi_name,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": lane["label"], "stage": "procurement", "error": str(exc)})

    for spec in quotation_specs:
        try:
            spec["company"] = company
            spec["expected_total"] = _sum_item_amounts(spec["items"])
            quotation_name = _create_quotation(spec)
            quotation_lookup[spec["label"]] = quotation_name
            if spec.get("target_status") == "Lost":
                frappe.db.set_value(
                    "Quotation",
                    quotation_name,
                    {
                        "status": "Lost",
                        "order_lost_reason": "May commercial follow-up ended without confirmation after competitor comparison and margin review.",
                    },
                    update_modified=False,
                )
            elif spec.get("target_status") == "Expired":
                frappe.db.set_value(
                    "Quotation",
                    quotation_name,
                    {"status": "Expired", "order_lost_reason": None},
                    update_modified=False,
                )
            frappe.db.commit()
            result["quotations"].append(
                {
                    "label": spec["label"],
                    "quotation": quotation_name,
                    "customer": spec["customer"],
                    "grand_total": spec["expected_total"],
                    "target_status": spec.get("target_status") or "Submitted",
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "stage": "quotation", "error": str(exc)})

    for spec in chain_specs:
        try:
            if spec.get("quotation_label"):
                quoted_items = quotation_spec_lookup[spec["quotation_label"]]["items"]
                expected_total = _sum_item_amounts(quoted_items)
                quotation_name = quotation_lookup[spec["quotation_label"]]
                order_date = getdate(spec["sales_order"]["transaction_date"])
                valid_till = getdate(frappe.db.get_value("Quotation", quotation_name, "valid_till"))
                if valid_till and valid_till < order_date:
                    frappe.db.set_value("Quotation", quotation_name, "valid_till", str(order_date), update_modified=False)
                    frappe.db.commit()
                try:
                    sales_order_name = _create_sales_order_from_quotation(
                        quotation_name,
                        {
                            **spec["sales_order"],
                            "customer": spec["customer"],
                            "expected_total": expected_total,
                        },
                    )
                except Exception as exc:
                    if "Validity period of this quotation has ended." not in str(exc):
                        raise
                    sales_order_name = _create_sales_order(
                        {
                            **spec["sales_order"],
                            "customer": spec["customer"],
                            "company": company,
                            "expected_total": expected_total,
                            "items": quoted_items,
                            "remarks": f"{spec['sales_order'].get('remarks') or ''} Historical quotation conversion recreated directly because the original quotation is already past live-system validity.",
                        }
                    )
                    frappe.db.set_value("Quotation", quotation_name, "status", "Ordered", update_modified=False)
                    _sync_quotation_workflow_state(quotation_name)
                    frappe.db.commit()
            else:
                expected_total = _sum_item_amounts(spec["items"])
                sales_order_name = _create_sales_order(
                    {
                        **spec["sales_order"],
                        "customer": spec["customer"],
                        "company": company,
                        "expected_total": expected_total,
                        "items": spec["items"],
                    }
                )
            delivery_note_name = _create_delivery_note_from_sales_order(sales_order_name, spec["delivery_note"])
            sales_invoice_name = _create_sales_invoice_from_delivery_note(
                delivery_note_name, spec["sales_invoice"]
            )
            invoice_lookup[(spec["customer"], spec["sales_invoice"]["posting_date"])] = sales_invoice_name
            frappe.db.commit()
            result["sales_orders"].append({"label": spec["label"], "sales_order": sales_order_name})
            result["delivery_notes"].append({"label": spec["label"], "delivery_note": delivery_note_name})
            result["sales_invoices"].append({"label": spec["label"], "sales_invoice": sales_invoice_name})
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "stage": "sales_chain", "error": str(exc)})

    for definition in direct_sales_defs:
        try:
            definition["expected_total"] = _sum_item_amounts(definition["items"])
            invoice_name = _create_sales_invoice(definition)
            invoice_lookup[(definition["customer"], definition["posting_date"])] = invoice_name
            frappe.db.commit()
            result["sales_invoices"].append(
                {
                    "label": f"direct_{definition['customer']}_{definition['posting_date']}",
                    "sales_invoice": invoice_name,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"direct_{definition['customer']}_{definition['posting_date']}",
                    "stage": "direct_sales",
                    "error": str(exc),
                }
            )

    for customer, invoice_date, payment_date, amount in payment_specs:
        try:
            invoice_name = invoice_lookup[(customer, invoice_date)]
            payment_name = _create_partial_payment_with_date_dedupe(
                "Sales Invoice", invoice_name, payment_date, amount
            )
            frappe.db.commit()
            result["payment_entries"].append(
                {
                    "customer": customer,
                    "sales_invoice": invoice_name,
                    "payment_entry": payment_name,
                    "amount": amount,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"label": f"receipt_{customer}_{invoice_date}", "stage": "receipt", "error": str(exc)}
            )

    for lane_label, payment_date, amount in supplier_payment_specs:
        try:
            invoice_name = purchase_invoice_lookup[lane_label]
            payment_name = _create_partial_payment_with_date_dedupe(
                "Purchase Invoice", invoice_name, payment_date, amount
            )
            frappe.db.commit()
            result["supplier_payments"].append(
                {
                    "purchase_invoice": invoice_name,
                    "payment_entry": payment_name,
                    "amount": amount,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"label": f"supplier_payment_{lane_label}", "stage": "supplier_payment", "error": str(exc)}
            )

    return result


def apply_june_2025_commercial_rebalance_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    warehouse = "Yangon Main Warehouse - MMOB"

    credit_limit_targets = {
        "Bayint Naung Wholesale Mobile": 220000000,
        "Capital Telecom (NPT)": 160000000,
        "Hlaing Tharyar Mobile Corner": 60000000,
        "Taunggyi City Mobile": 70000000,
        "35th Street Mobile Wholesale": 140000000,
    }

    procurement_lanes = [
        {
            "label": "june_golden_dragon_handset_lane",
            "purchase_order": {
                "supplier": "Golden Dragon Trading Co. Ltd.",
                "company": company,
                "transaction_date": "2025-06-06",
                "schedule_date": "2025-06-08",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "June handset-focused replenishment for repeat wholesale chains after May mixed sell-through.",
                "items": [
                    {"item_code": "SPH-SAM-A15-6/128", "qty": 18, "rate": 840000, "warehouse": warehouse},
                    {"item_code": "SPH-XMI-RN13-8/256", "qty": 12, "rate": 705000, "warehouse": warehouse},
                    {"item_code": "SPH-APP-IP13-128", "qty": 3, "rate": 1735000, "warehouse": warehouse},
                ],
            },
            "purchase_receipt": {
                "supplier": "Golden Dragon Trading Co. Ltd.",
                "posting_date": "2025-06-08",
                "posting_time": "11:20:00",
                "supplier_delivery_note": "GD-DN-250608-01",
                "remarks": "Golden Dragon June handset arrival supporting Bayint, Capital, and 35th Street repeat demand.",
            },
            "purchase_invoice": {
                "posting_date": "2025-06-09",
                "posting_time": "15:10:00",
                "bill_no": "GD-INV-2506-061",
                "bill_date": "2025-06-08",
                "due_date": "2025-07-08",
                "remarks": "Golden Dragon June handset replenishment invoice / standard 30-day supplier credit.",
            },
        },
        {
            "label": "june_sunflower_accessory_lane",
            "purchase_order": {
                "supplier": "Sunflower Accessories Co.",
                "company": company,
                "transaction_date": "2025-06-10",
                "schedule_date": "2025-06-11",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "June core-accessory replenishment for power-bank, charger, cable, and memory-card turnover.",
                "items": [
                    {"item_code": "ACC-PWB-BAS-20K", "qty": 150, "rate": 78000, "warehouse": warehouse},
                    {"item_code": "ACC-CHR-SAM-25W", "qty": 200, "rate": 25000, "warehouse": warehouse},
                    {"item_code": "ACC-CHR-XMI-33W", "qty": 150, "rate": 20000, "warehouse": warehouse},
                    {"item_code": "ACC-CBL-BAS-TC1M", "qty": 220, "rate": 5000, "warehouse": warehouse},
                    {"item_code": "MEM-MSD-SND-128", "qty": 100, "rate": 18000, "warehouse": warehouse},
                ],
            },
            "purchase_receipt": {
                "supplier": "Sunflower Accessories Co.",
                "posting_date": "2025-06-11",
                "posting_time": "12:15:00",
                "supplier_delivery_note": "SFL-DN-250611-01",
                "remarks": "Sunflower June accessories arrival for mixed wholesale bundles and branch replenishment.",
            },
            "purchase_invoice": {
                "posting_date": "2025-06-12",
                "posting_time": "16:00:00",
                "bill_no": "SFL-INV-2506-052",
                "bill_date": "2025-06-11",
                "due_date": "2025-07-11",
                "remarks": "Sunflower June accessory invoice / standard 30-day supplier credit.",
            },
        },
        {
            "label": "june_myanmar_tech_premium_lane",
            "purchase_order": {
                "supplier": "Myanmar Tech Import Services",
                "company": company,
                "transaction_date": "2025-06-17",
                "schedule_date": "2025-06-18",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "June premium-device and higher-value accessory top-up for direct key-account demand.",
                "items": [
                    {"item_code": "SPH-APP-IP14-128", "qty": 3, "rate": 2210000, "warehouse": warehouse},
                    {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 50, "rate": 42000, "warehouse": warehouse},
                    {"item_code": "GAD-SPK-JBL-GO3", "qty": 20, "rate": 145000, "warehouse": warehouse},
                ],
            },
            "purchase_receipt": {
                "supplier": "Myanmar Tech Import Services",
                "posting_date": "2025-06-18",
                "posting_time": "11:05:00",
                "supplier_delivery_note": "MTI-DN-250618-01",
                "remarks": "Myanmar Tech June premium-device arrival for Capital and township mixed orders.",
            },
            "purchase_invoice": {
                "posting_date": "2025-06-19",
                "posting_time": "15:00:00",
                "bill_no": "MTI-INV-2506-018",
                "bill_date": "2025-06-18",
                "due_date": "2025-07-18",
                "remarks": "Myanmar Tech June premium-device invoice / 30-day supplier credit.",
            },
        },
    ]

    quotation_specs = [
        {
            "label": "june_bayint_repeat_quote",
            "customer": "Bayint Naung Wholesale Mobile",
            "transaction_date": "2025-06-09",
            "valid_till": "2025-06-12",
            "payment_terms_template": "30 Days - MMOB",
            "set_warehouse": warehouse,
            "remarks": "June Bayint repeat wholesale quotation for mixed handset and fast-moving accessories.",
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 5, "rate": 1020000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 4, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 30, "rate": 8000},
            ],
        },
        {
            "label": "june_hlaing_quote",
            "customer": "Hlaing Tharyar Mobile Corner",
            "transaction_date": "2025-06-15",
            "valid_till": "2025-06-18",
            "payment_terms_template": "30 Days - MMOB",
            "set_warehouse": warehouse,
            "remarks": "June Hlaing Tharyar quotation for mixed township wholesale restock with practical bundle sizing.",
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 4, "rate": 1020000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 3, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 12, "rate": 110000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
            ],
        },
        {
            "label": "june_latha_lost_quote",
            "customer": "Latha Mobile Wholesale",
            "transaction_date": "2025-06-14",
            "valid_till": "2025-06-17",
            "payment_terms_template": "30 Days - MMOB",
            "set_warehouse": warehouse,
            "target_status": "Lost",
            "remarks": "June Latha quotation lost after competitor price pressure on core handsets and accessories.",
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 4, "rate": 1020000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
            ],
        },
        {
            "label": "june_pazundaung_expired_quote",
            "customer": "Pazundaung Mobile Distribution",
            "transaction_date": "2025-06-21",
            "valid_till": "2025-06-24",
            "payment_terms_template": "30 Days - MMOB",
            "set_warehouse": warehouse,
            "target_status": "Expired",
            "remarks": "June Pazundaung quotation expired after the customer delayed final confirmation for a small mixed bundle.",
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 8, "rate": 110000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 12, "rate": 30000},
                {"item_code": "MEM-MSD-SND-128", "qty": 12, "rate": 26000},
            ],
        },
    ]

    chain_specs = [
        {
            "label": "june_bayint_quote_chain",
            "customer": "Bayint Naung Wholesale Mobile",
            "quotation_label": "june_bayint_repeat_quote",
            "sales_order": {
                "transaction_date": "2025-06-11",
                "delivery_date": "2025-06-12",
                "po_no": "CPO-2025-06-231",
                "po_date": "2025-06-11",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "June Bayint repeat wholesale order converted from negotiated quotation follow-up.",
            },
            "delivery_note": {
                "posting_date": "2025-06-12",
                "posting_time": "11:30:00",
                "remarks": "June Bayint wholesale dispatch after quotation acceptance and warehouse release.",
            },
            "sales_invoice": {
                "posting_date": "2025-06-12",
                "posting_time": "11:50:00",
                "due_date": "2025-07-12",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "June Bayint invoice converted from approved quotation and delivery release.",
            },
        },
        {
            "label": "june_hlaing_quote_chain",
            "customer": "Hlaing Tharyar Mobile Corner",
            "quotation_label": "june_hlaing_quote",
            "sales_order": {
                "transaction_date": "2025-06-17",
                "delivery_date": "2025-06-18",
                "po_no": "CPO-2025-06-232",
                "po_date": "2025-06-17",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "June Hlaing Tharyar wholesale order converted from short-cycle township quotation.",
            },
            "delivery_note": {
                "posting_date": "2025-06-18",
                "posting_time": "13:10:00",
                "remarks": "June Hlaing Tharyar dispatch after quotation acceptance and mixed-bundle packing.",
            },
            "sales_invoice": {
                "posting_date": "2025-06-18",
                "posting_time": "13:25:00",
                "due_date": "2025-07-18",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "June Hlaing Tharyar invoice issued after same-day dispatch from quotation conversion.",
            },
        },
        {
            "label": "june_capital_direct_chain",
            "customer": "Capital Telecom (NPT)",
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 2, "rate": 2150000},
                {"item_code": "SPH-APP-IP14-128", "qty": 1, "rate": 2650000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 1020000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 10, "rate": 32000},
            ],
            "sales_order": {
                "transaction_date": "2025-06-23",
                "delivery_date": "2025-06-24",
                "po_no": "CPO-2025-06-233",
                "po_date": "2025-06-23",
                "payment_terms_template": "45 Days Approved - MMOB",
                "set_warehouse": warehouse,
                "remarks": "June Capital Telecom repeat key-account order confirmed directly without separate quotation stage.",
            },
            "delivery_note": {
                "posting_date": "2025-06-24",
                "posting_time": "14:15:00",
                "remarks": "June Capital Telecom dispatch after direct commercial approval and stock reservation.",
            },
            "sales_invoice": {
                "posting_date": "2025-06-24",
                "posting_time": "14:35:00",
                "due_date": "2025-08-08",
                "payment_terms_template": "45 Days Approved - MMOB",
                "remarks": "June Capital Telecom invoice issued after direct-order dispatch.",
            },
        },
        {
            "label": "june_taunggyi_direct_chain",
            "customer": "Taunggyi City Mobile",
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 4, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 3, "rate": 1020000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 15, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
            ],
            "sales_order": {
                "transaction_date": "2025-06-26",
                "delivery_date": "2025-06-27",
                "po_no": "CPO-2025-06-234",
                "po_date": "2025-06-26",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "June Taunggyi direct wholesale order placed for township replenishment ahead of month-end demand.",
            },
            "delivery_note": {
                "posting_date": "2025-06-27",
                "posting_time": "11:20:00",
                "remarks": "June Taunggyi mixed-product dispatch after direct wholesale confirmation.",
            },
            "sales_invoice": {
                "posting_date": "2025-06-27",
                "posting_time": "11:45:00",
                "due_date": "2025-07-27",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "June Taunggyi invoice released after same-day township dispatch.",
            },
        },
        {
            "label": "june_35th_direct_chain",
            "customer": "35th Street Mobile Wholesale",
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 1020000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 20, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
                {"item_code": "MEM-MSD-SND-128", "qty": 10, "rate": 26000},
            ],
            "sales_order": {
                "transaction_date": "2025-06-27",
                "delivery_date": "2025-06-28",
                "po_no": "CPO-2025-06-235",
                "po_date": "2025-06-27",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "June 35th Street repeat wholesale order confirmed directly after routine phone order.",
            },
            "delivery_note": {
                "posting_date": "2025-06-28",
                "posting_time": "10:50:00",
                "remarks": "June 35th Street dispatch released after direct repeat-order confirmation.",
            },
            "sales_invoice": {
                "posting_date": "2025-06-28",
                "posting_time": "11:10:00",
                "due_date": "2025-07-28",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "June 35th Street invoice issued after repeat-order dispatch.",
            },
        },
    ]

    direct_sales_defs = [
        {
            "customer": "Lanmadaw Telecom & Gadgets",
            "posting_date": "2025-06-29",
            "due_date": "2025-06-30",
            "warehouse": warehouse,
            "company": company,
            "remarks": "June small Lanmadaw replenishment billed directly without separate delivery paperwork.",
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 8, "rate": 110000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 12, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
            ],
        },
        {
            "customer": "Bago Myoma Phone Shop",
            "posting_date": "2025-06-30",
            "due_date": "2025-06-30",
            "warehouse": warehouse,
            "company": company,
            "remarks": "June small Bago township bundle settled as same-day direct billing.",
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 1, "rate": 1020000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 6, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 10, "rate": 32000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 15, "rate": 8000},
            ],
        },
    ]

    payment_specs = [
        ("Bayint Naung Wholesale Mobile", "2025-06-12", "2025-06-25", 4000000),
        ("Hlaing Tharyar Mobile Corner", "2025-06-18", "2025-07-08", 3000000),
        ("Capital Telecom (NPT)", "2025-06-24", "2025-07-10", 4000000),
        ("Taunggyi City Mobile", "2025-06-27", "2025-07-15", 3500000),
        ("35th Street Mobile Wholesale", "2025-06-28", "2025-07-12", 2500000),
        ("Lanmadaw Telecom & Gadgets", "2025-06-29", "2025-06-30", 2000000),
        ("Bago Myoma Phone Shop", "2025-06-30", "2025-06-30", 2000000),
    ]

    supplier_payment_specs = [
        ("june_golden_dragon_handset_lane", "2025-07-05", 6000000),
        ("june_sunflower_accessory_lane", "2025-07-11", 5000000),
        ("june_myanmar_tech_premium_lane", "2025-07-18", 3000000),
    ]

    quotation_lookup: dict[str, str] = {}
    quotation_spec_lookup = {spec["label"]: spec for spec in quotation_specs}
    invoice_lookup: dict[tuple[str, str], str] = {}
    purchase_invoice_lookup: dict[str, str] = {}
    result = {
        "credit_limits": [],
        "procurement_lanes": [],
        "quotations": [],
        "sales_orders": [],
        "delivery_notes": [],
        "sales_invoices": [],
        "payment_entries": [],
        "supplier_payments": [],
        "failed": [],
    }

    for customer_name, credit_limit in credit_limit_targets.items():
        try:
            if not frappe.db.exists("Customer", customer_name):
                continue
            customer = frappe.get_doc("Customer", customer_name)
            limit_row = None
            for row in customer.credit_limits:
                if row.company == company:
                    limit_row = row
                    break
            current_outstanding = float(
                frappe.db.sql(
                    """
                    select ifnull(sum(outstanding_amount), 0)
                    from `tabSales Invoice`
                    where customer = %s and docstatus = 1 and outstanding_amount > 0
                    """,
                    (customer_name,),
                )[0][0]
                or 0
            )
            effective_credit_limit = max(float(credit_limit), current_outstanding + 5000000)
            if limit_row:
                limit_row.credit_limit = effective_credit_limit
                limit_row.bypass_credit_limit_check = 0
            else:
                customer.append(
                    "credit_limits",
                    {
                        "company": company,
                        "credit_limit": effective_credit_limit,
                        "bypass_credit_limit_check": 0,
                    },
                )
            customer.save(ignore_permissions=True)
            frappe.db.commit()
            result["credit_limits"].append({"customer": customer_name, "credit_limit": effective_credit_limit})
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"label": f"credit_limit_{customer_name}", "stage": "credit_limit", "error": str(exc)}
            )

    for lane in procurement_lanes:
        try:
            lane["purchase_order"]["expected_total"] = _sum_item_amounts(lane["purchase_order"]["items"])
            po_name = _create_purchase_order(lane["purchase_order"])
            pr_name = _create_purchase_receipt_from_order(po_name, lane["purchase_receipt"])
            pi_name = _create_purchase_invoice_from_receipt(
                pr_name,
                lane["purchase_order"]["supplier"],
                lane["purchase_order"].get("payment_terms_template"),
                lane["purchase_invoice"],
            )
            purchase_invoice_lookup[lane["label"]] = pi_name
            frappe.db.commit()
            result["procurement_lanes"].append(
                {
                    "label": lane["label"],
                    "purchase_order": po_name,
                    "purchase_receipt": pr_name,
                    "purchase_invoice": pi_name,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": lane["label"], "stage": "procurement", "error": str(exc)})

    for spec in quotation_specs:
        try:
            spec["company"] = company
            spec["expected_total"] = _sum_item_amounts(spec["items"])
            quotation_name = _create_quotation(spec)
            quotation_lookup[spec["label"]] = quotation_name
            if spec.get("target_status") == "Lost":
                frappe.db.set_value(
                    "Quotation",
                    quotation_name,
                    {
                        "status": "Lost",
                        "order_lost_reason": "June commercial follow-up ended without confirmation after competitor comparison and margin review.",
                    },
                    update_modified=False,
                )
            elif spec.get("target_status") == "Expired":
                frappe.db.set_value(
                    "Quotation",
                    quotation_name,
                    {"status": "Expired", "order_lost_reason": None},
                    update_modified=False,
                )
            frappe.db.commit()
            result["quotations"].append(
                {
                    "label": spec["label"],
                    "quotation": quotation_name,
                    "customer": spec["customer"],
                    "grand_total": spec["expected_total"],
                    "target_status": spec.get("target_status") or "Submitted",
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "stage": "quotation", "error": str(exc)})

    for spec in chain_specs:
        try:
            if spec.get("quotation_label"):
                quoted_items = quotation_spec_lookup[spec["quotation_label"]]["items"]
                expected_total = _sum_item_amounts(quoted_items)
                quotation_name = quotation_lookup[spec["quotation_label"]]
                order_date = getdate(spec["sales_order"]["transaction_date"])
                valid_till = getdate(frappe.db.get_value("Quotation", quotation_name, "valid_till"))
                if valid_till and valid_till < order_date:
                    frappe.db.set_value("Quotation", quotation_name, "valid_till", str(order_date), update_modified=False)
                    frappe.db.commit()
                try:
                    sales_order_name = _create_sales_order_from_quotation(
                        quotation_name,
                        {
                            **spec["sales_order"],
                            "customer": spec["customer"],
                            "expected_total": expected_total,
                        },
                    )
                except Exception as exc:
                    if "Validity period of this quotation has ended." not in str(exc):
                        raise
                    sales_order_name = _create_sales_order(
                        {
                            **spec["sales_order"],
                            "customer": spec["customer"],
                            "company": company,
                            "expected_total": expected_total,
                            "items": quoted_items,
                            "remarks": f"{spec['sales_order'].get('remarks') or ''} Historical quotation conversion recreated directly because the original quotation is already past live-system validity.",
                        }
                    )
                    frappe.db.set_value("Quotation", quotation_name, "status", "Ordered", update_modified=False)
                    _sync_quotation_workflow_state(quotation_name)
                    frappe.db.commit()
            else:
                expected_total = _sum_item_amounts(spec["items"])
                sales_order_name = _create_sales_order(
                    {
                        **spec["sales_order"],
                        "customer": spec["customer"],
                        "company": company,
                        "expected_total": expected_total,
                        "items": spec["items"],
                    }
                )
            delivery_note_name = _create_delivery_note_from_sales_order(sales_order_name, spec["delivery_note"])
            sales_invoice_name = _create_sales_invoice_from_delivery_note(
                delivery_note_name, spec["sales_invoice"]
            )
            invoice_lookup[(spec["customer"], spec["sales_invoice"]["posting_date"])] = sales_invoice_name
            frappe.db.commit()
            result["sales_orders"].append({"label": spec["label"], "sales_order": sales_order_name})
            result["delivery_notes"].append({"label": spec["label"], "delivery_note": delivery_note_name})
            result["sales_invoices"].append({"label": spec["label"], "sales_invoice": sales_invoice_name})
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "stage": "sales_chain", "error": str(exc)})

    for definition in direct_sales_defs:
        try:
            definition["expected_total"] = _sum_item_amounts(definition["items"])
            invoice_name = _create_sales_invoice(definition)
            invoice_lookup[(definition["customer"], definition["posting_date"])] = invoice_name
            frappe.db.commit()
            result["sales_invoices"].append(
                {
                    "label": f"direct_{definition['customer']}_{definition['posting_date']}",
                    "sales_invoice": invoice_name,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"direct_{definition['customer']}_{definition['posting_date']}",
                    "stage": "direct_sales",
                    "error": str(exc),
                }
            )

    for customer, invoice_date, payment_date, amount in payment_specs:
        try:
            invoice_name = invoice_lookup[(customer, invoice_date)]
            payment_name = _create_partial_payment_with_date_dedupe(
                "Sales Invoice", invoice_name, payment_date, amount
            )
            frappe.db.commit()
            result["payment_entries"].append(
                {
                    "customer": customer,
                    "sales_invoice": invoice_name,
                    "payment_entry": payment_name,
                    "amount": amount,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"label": f"receipt_{customer}_{invoice_date}", "stage": "receipt", "error": str(exc)}
            )

    for lane_label, payment_date, amount in supplier_payment_specs:
        try:
            invoice_name = purchase_invoice_lookup[lane_label]
            payment_name = _create_partial_payment_with_date_dedupe(
                "Purchase Invoice", invoice_name, payment_date, amount
            )
            frappe.db.commit()
            result["supplier_payments"].append(
                {
                    "purchase_invoice": invoice_name,
                    "payment_entry": payment_name,
                    "amount": amount,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"label": f"supplier_payment_{lane_label}", "stage": "supplier_payment", "error": str(exc)}
            )

    return result


def apply_july_2025_chain_repair_smoke_test() -> dict[str, Any]:
    target = {
        "invoice_name": "ACC-SINV-2026-00613",
        "original_sales_order_name": "SAL-ORD-2026-00301",
        "normalized_sales_order_name": "SAL-ORD-2026-00338",
        "delivery_note_name": None,
        "sales_order": {
            "transaction_date": "2025-07-15",
            "delivery_date": "2025-07-17",
            "po_no": "WALK-IN-JUL-2025-CITY-01",
            "po_date": "2025-07-15",
            "set_warehouse": "Yangon Main Warehouse - MMOB",
            "remarks": "July City Mobile Mart direct counter-wholesale order rebuilt as stock-linked commercial chain.",
        },
        "invoice_remarks": "July City Mobile Mart chain normalized to stock-linked sales invoice for realistic commercial and financial flow.",
    }
    return _normalize_sales_invoice_to_stock_sales_order_chain(target)


def apply_july_2025_chain_repair_wave() -> dict[str, Any]:
    targets = [
        {
            "invoice_name": "ACC-SINV-2026-00609",
            "original_sales_order_name": "SAL-ORD-2026-00295",
            "normalized_sales_order_name": "SAL-ORD-2026-00330",
            "delivery_note_name": "MAT-DN-2026-00272",
            "sales_order": {
                "transaction_date": "2025-07-09",
                "delivery_date": "2025-07-11",
                "po_no": "CPO-2025-07-301",
                "po_date": "2025-07-09",
                "set_warehouse": "Yangon Main Warehouse - MMOB",
                "remarks": "July Bayint repeat wholesale order rebuilt as stock-linked chain after historical normalization cleanup.",
            },
            "invoice_remarks": "July Bayint chain normalized to stock-linked sales invoice for realistic wholesale workflow and financial recognition.",
        },
        {
            "invoice_name": "ACC-SINV-2026-00610",
            "original_sales_order_name": "SAL-ORD-2026-00296",
            "normalized_sales_order_name": "SAL-ORD-2026-00331",
            "delivery_note_name": "MAT-DN-2026-00273",
            "sales_order": {
                "transaction_date": "2025-07-11",
                "delivery_date": "2025-07-13",
                "po_no": "CPO-2025-07-302",
                "po_date": "2025-07-11",
                "set_warehouse": "Yangon Main Warehouse - MMOB",
                "remarks": "July Capital Telecom repeat key-account order rebuilt as stock-linked chain after historical normalization cleanup.",
            },
            "invoice_remarks": "July Capital Telecom chain normalized to stock-linked sales invoice for realistic wholesale workflow and financial recognition.",
        },
        {
            "invoice_name": "ACC-SINV-2026-00611",
            "original_sales_order_name": "SAL-ORD-2026-00299",
            "normalized_sales_order_name": "SAL-ORD-2026-00332",
            "delivery_note_name": "MAT-DN-2026-00274",
            "sales_order": {
                "transaction_date": "2025-07-14",
                "delivery_date": "2025-07-16",
                "po_no": "CPO-2025-07-303",
                "po_date": "2025-07-14",
                "set_warehouse": "Mandalay Warehouse - MMOB",
                "remarks": "July Aung Aung Telecom repeat wholesale order rebuilt as stock-linked chain after historical normalization cleanup.",
            },
            "invoice_remarks": "July Aung Aung Telecom chain normalized to stock-linked sales invoice for realistic wholesale workflow and financial recognition.",
        },
        {
            "invoice_name": "ACC-SINV-2026-00612",
            "original_sales_order_name": "SAL-ORD-2026-00300",
            "normalized_sales_order_name": "SAL-ORD-2026-00336",
            "delivery_note_name": None,
            "sales_order": {
                "transaction_date": "2025-07-18",
                "delivery_date": "2025-07-20",
                "po_no": "COUNTER-JUL-2025-HLEDAN-01",
                "po_date": "2025-07-18",
                "set_warehouse": "Yangon Main Warehouse - MMOB",
                "remarks": "July Hledan mixed-device counter-wholesale order rebuilt as stock-linked chain after historical normalization cleanup.",
            },
            "invoice_remarks": "July Hledan chain normalized to stock-linked sales invoice for realistic counter-wholesale workflow and financial recognition.",
        },
        {
            "invoice_name": "ACC-SINV-2026-00613",
            "original_sales_order_name": "SAL-ORD-2026-00301",
            "normalized_sales_order_name": "SAL-ORD-2026-00338",
            "delivery_note_name": None,
            "sales_order": {
                "transaction_date": "2025-07-15",
                "delivery_date": "2025-07-17",
                "po_no": "WALK-IN-JUL-2025-CITY-01",
                "po_date": "2025-07-15",
                "set_warehouse": "Yangon Main Warehouse - MMOB",
                "remarks": "July City Mobile Mart direct counter-wholesale order rebuilt as stock-linked commercial chain.",
            },
            "invoice_remarks": "July City Mobile Mart chain normalized to stock-linked sales invoice for realistic commercial and financial flow.",
        },
    ]

    result = {"normalized": [], "failed": []}
    for target in targets:
        if not frappe.db.exists("Sales Invoice", target["invoice_name"]):
            continue
        try:
            normalized = _normalize_sales_invoice_to_stock_sales_order_chain(target)
            result["normalized"].append(normalized)
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"invoice_name": target["invoice_name"], "error": str(exc)})
    return result


def apply_july_2025_cost_realism_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    warehouse = "Yangon Main Warehouse - MMOB"

    lane = {
        "label": "july_fx_shock_handset_cost_lane",
        "purchase_order": {
            "supplier": "Golden Dragon Trading Co. Ltd.",
            "company": company,
            "transaction_date": "2025-07-08",
            "schedule_date": "2025-07-08",
            "payment_terms_template": "30 Days - MMOB",
            "set_warehouse": warehouse,
            "remarks": "Early-July emergency handset replenishment at higher landed cost after currency and import-cost pressure, before major wholesale dispatches.",
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 20, "rate": 980000, "warehouse": warehouse},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 10, "rate": 915000, "warehouse": warehouse},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 80, "rate": 24000, "warehouse": warehouse},
            ],
        },
        "purchase_receipt": {
            "supplier": "Golden Dragon Trading Co. Ltd.",
            "posting_date": "2025-07-08",
            "posting_time": "10:50:00",
            "supplier_delivery_note": "GD-DN-250708-02",
            "remarks": "Backdated early-July higher-cost replenishment aligned to pre-dispatch handset replacement economics.",
        },
        "purchase_invoice": {
            "posting_date": "2025-07-09",
            "posting_time": "15:40:00",
            "bill_no": "GD-INV-2507-089",
            "bill_date": "2025-07-08",
            "due_date": "2025-08-08",
            "remarks": "Higher-cost July handset replenishment invoice reflecting FX-driven landed cost pressure.",
        },
    }

    result = {"procurement_lane": None, "supplier_payment": None, "failed": []}
    try:
        lane["purchase_order"]["expected_total"] = _sum_item_amounts(lane["purchase_order"]["items"])
        po_name = _create_purchase_order(lane["purchase_order"])
        pr_name = _create_purchase_receipt_from_order(po_name, lane["purchase_receipt"])
        pi_name = _create_purchase_invoice_from_receipt(
            pr_name,
            lane["purchase_order"]["supplier"],
            lane["purchase_order"].get("payment_terms_template"),
            lane["purchase_invoice"],
        )
        frappe.db.commit()
        result["procurement_lane"] = {
            "label": lane["label"],
            "purchase_order": po_name,
            "purchase_receipt": pr_name,
            "purchase_invoice": pi_name,
        }
        try:
            payment_name = _create_partial_payment_with_date_dedupe(
                "Purchase Invoice",
                pi_name,
                "2025-08-08",
                8000000,
            )
            frappe.db.commit()
            result["supplier_payment"] = {
                "purchase_invoice": pi_name,
                "payment_entry": payment_name,
                "amount": 8000000,
            }
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"stage": "supplier_payment", "error": str(exc)})
    except Exception as exc:
        frappe.db.rollback()
        result["failed"].append({"stage": "procurement", "error": str(exc)})
    return result


def apply_july_2025_quote_polish_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    warehouse = "Yangon Main Warehouse - MMOB"
    cleanup_quotes = [
        {
            "name": "SAL-QTN-2026-00241",
            "status": "Lost",
            "order_lost_reason": "Mid-July Mandalay inquiry did not convert because the customer postponed replenishment after internal credit and cash-cycle review.",
        },
        {
            "name": "SAL-QTN-2026-00242",
            "status": "Expired",
            "order_lost_reason": None,
        },
    ]

    quotation_specs = [
        {
            "label": "july_mandalay_accessories_converted_quote",
            "customer": "Mandalay Accessories Wholesale",
            "transaction_date": "2025-07-21",
            "valid_till": "2025-07-24",
            "payment_terms_template": "15 Days - MMOB",
            "selling_price_list": "Wholesale Selling - MMOB",
            "set_warehouse": warehouse,
            "remarks": "Late-July Mandalay quotation for practical accessories-led replenishment after the customer reviewed slower handset demand.",
            "items": [
                {"item_code": "ACC-PWB-BAS-20K", "qty": 20, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
            ],
        },
        {
            "label": "july_taunggyi_cod_quote",
            "customer": "Taunggyi City Mobile",
            "transaction_date": "2025-07-27",
            "valid_till": "2025-07-29",
            "payment_terms_template": "Cash on Delivery - MMOB",
            "selling_price_list": "Retail Selling - MMOB",
            "set_warehouse": warehouse,
            "remarks": "Late-July Taunggyi quotation for a compact mixed-device bundle ahead of weekend township retail demand.",
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 2, "rate": 220000},
                {"item_code": "MEM-MSD-SND-128", "qty": 10, "rate": 32000},
            ],
        },
    ]

    chain_specs = [
        {
            "label": "july_mandalay_accessories_quote_to_order_chain",
            "customer": "Mandalay Accessories Wholesale",
            "quotation_label": "july_mandalay_accessories_converted_quote",
            "sales_order": {
                "transaction_date": "2025-07-23",
                "delivery_date": "2025-07-24",
                "po_no": "CPO-2025-07-312",
                "po_date": "2025-07-23",
                "payment_terms_template": "15 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "July Mandalay accessories order converted from quotation after the customer confirmed a smaller but immediate replenishment batch.",
            },
            "delivery_note": {
                "posting_date": "2025-07-24",
                "posting_time": "11:15:00",
                "remarks": "July Mandalay accessories dispatch under a normal top-up cycle rather than a large expansion order.",
            },
            "sales_invoice": {
                "posting_date": "2025-07-24",
                "posting_time": "11:35:00",
                "due_date": "2025-08-08",
                "payment_terms_template": "15 Days - MMOB",
                "remarks": "July Mandalay accessories invoice converted from quotation-backed dispatch with short wholesale credit.",
            },
        },
        {
            "label": "july_taunggyi_quote_to_order_chain",
            "customer": "Taunggyi City Mobile",
            "quotation_label": "july_taunggyi_cod_quote",
            "sales_order": {
                "transaction_date": "2025-07-28",
                "delivery_date": "2025-07-29",
                "po_no": "COD-2025-07-TGI-01",
                "po_date": "2025-07-28",
                "payment_terms_template": "Cash on Delivery - MMOB",
                "set_warehouse": warehouse,
                "remarks": "July Taunggyi order converted from a short-cycle quoted bundle for immediate township retail resale.",
            },
            "delivery_note": {
                "posting_date": "2025-07-29",
                "posting_time": "15:10:00",
                "remarks": "July Taunggyi dispatch completed within the same short cycle after immediate confirmation of the quoted bundle.",
            },
            "sales_invoice": {
                "posting_date": "2025-07-29",
                "posting_time": "15:30:00",
                "due_date": "2025-07-29",
                "payment_terms_template": "Cash on Delivery - MMOB",
                "remarks": "July Taunggyi invoice after same-day quotation conversion and cash collection.",
            },
        },
    ]

    payment_specs = [
        ("Taunggyi City Mobile", "2025-07-29", "2025-07-29", 3660000),
        ("Mandalay Accessories Wholesale", "2025-07-24", "2025-08-08", 2000000),
    ]

    quotation_lookup: dict[str, str] = {}
    invoice_lookup: dict[tuple[str, str], str] = {}
    quotation_spec_lookup = {spec["label"]: spec for spec in quotation_specs}
    result = {
        "closed_quotes": [],
        "quotations": [],
        "sales_orders": [],
        "delivery_notes": [],
        "sales_invoices": [],
        "payments": [],
        "failed": [],
    }

    for spec in cleanup_quotes:
        if not frappe.db.exists("Quotation", spec["name"]):
            continue
        try:
            frappe.db.set_value(
                "Quotation",
                spec["name"],
                {
                    "status": spec["status"],
                    "order_lost_reason": spec["order_lost_reason"],
                },
                update_modified=False,
            )
            frappe.db.commit()
            result["closed_quotes"].append({"quotation": spec["name"], "status": spec["status"]})
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["name"], "stage": "quote_cleanup", "error": str(exc)})

    for spec in quotation_specs:
        try:
            spec["company"] = company
            spec["expected_total"] = _sum_item_amounts(spec["items"])
            quotation_name = _create_quotation(spec)
            quotation_lookup[spec["label"]] = quotation_name
            frappe.db.commit()
            result["quotations"].append(
                {
                    "label": spec["label"],
                    "quotation": quotation_name,
                    "customer": spec["customer"],
                    "grand_total": spec["expected_total"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "stage": "quotation", "error": str(exc)})

    for spec in chain_specs:
        try:
            quoted_items = quotation_spec_lookup[spec["quotation_label"]]["items"]
            expected_total = _sum_item_amounts(quoted_items)
            quotation_name = quotation_lookup[spec["quotation_label"]]
            order_date = getdate(spec["sales_order"]["transaction_date"])
            valid_till = getdate(frappe.db.get_value("Quotation", quotation_name, "valid_till"))
            if valid_till and valid_till < order_date:
                frappe.db.set_value("Quotation", quotation_name, "valid_till", str(order_date), update_modified=False)
                frappe.db.commit()

            try:
                sales_order_name = _create_sales_order_from_quotation(
                    quotation_name,
                    {
                        **spec["sales_order"],
                        "customer": spec["customer"],
                        "expected_total": expected_total,
                    },
                )
            except Exception as exc:
                if "Validity period of this quotation has ended." not in str(exc):
                    raise
                sales_order_name = _create_sales_order(
                    {
                        **spec["sales_order"],
                        "customer": spec["customer"],
                        "company": company,
                        "expected_total": expected_total,
                        "items": quoted_items,
                        "remarks": f"{spec['sales_order'].get('remarks') or ''} Historical quotation conversion recreated directly because the original quotation validity already passed in the live system.",
                    }
                )
                frappe.db.set_value("Quotation", quotation_name, "status", "Ordered", update_modified=False)
                _sync_quotation_workflow_state(quotation_name)
                frappe.db.commit()

            delivery_note_name = _create_delivery_note_from_sales_order(sales_order_name, spec["delivery_note"])
            sales_invoice_name = _create_sales_invoice_from_delivery_note(
                delivery_note_name,
                spec["sales_invoice"],
            )
            invoice_lookup[(spec["customer"], spec["sales_invoice"]["posting_date"])] = sales_invoice_name
            frappe.db.commit()
            result["sales_orders"].append({"label": spec["label"], "sales_order": sales_order_name})
            result["delivery_notes"].append({"label": spec["label"], "delivery_note": delivery_note_name})
            result["sales_invoices"].append({"label": spec["label"], "sales_invoice": sales_invoice_name})
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "stage": "sales_chain", "error": str(exc)})

    for customer, invoice_date, payment_date, amount in payment_specs:
        try:
            invoice_name = invoice_lookup[(customer, invoice_date)]
            payment_name = _create_partial_payment_with_date_dedupe(
                "Sales Invoice",
                invoice_name,
                payment_date,
                amount,
            )
            frappe.db.commit()
            result["payments"].append(
                {
                    "customer": customer,
                    "sales_invoice": invoice_name,
                    "payment_entry": payment_name,
                    "posting_date": payment_date,
                    "amount": amount,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"payment_{customer}_{invoice_date}",
                    "stage": "payment",
                    "error": str(exc),
                }
            )

    return result


def apply_august_2025_realism_cleanup_wave() -> dict[str, Any]:
    quotation_updates = [
        {
            "name": "SAL-QTN-2026-00205",
            "party_name": "Bayint Naung Wholesale Mobile",
            "customer_name": "Bayint Naung Wholesale Mobile",
            "valid_till": "2025-08-09",
            "status": "Ordered",
            "order_lost_reason": None,
        },
        {
            "name": "SAL-QTN-2026-00206",
            "party_name": "Capital Telecom (NPT)",
            "customer_name": "Capital Telecom (NPT)",
            "valid_till": "2025-08-11",
            "status": "Ordered",
            "order_lost_reason": None,
        },
        {
            "name": "SAL-QTN-2026-00207",
            "party_name": "Chan Aye Mobile Trading Hub",
            "customer_name": "Chan Aye Mobile Trading Hub",
            "valid_till": "2025-08-13",
            "status": "Expired",
            "order_lost_reason": None,
        },
        {
            "name": "SAL-QTN-2026-00208",
            "party_name": "35th Street Mobile Wholesale",
            "customer_name": "35th Street Mobile Wholesale",
            "valid_till": "2025-08-13",
            "status": "Lost",
            "order_lost_reason": "August wholesale inquiry did not convert after the customer held back due to slower secondary-market movement.",
        },
        {
            "name": "SAL-QTN-2026-00209",
            "party_name": "Latha Mobile Wholesale",
            "customer_name": "Latha Mobile Wholesale",
            "valid_till": "2025-08-15",
            "status": "Lost",
            "order_lost_reason": "August follow-up ended without order confirmation after pricing comparison and cash-cycle caution from the customer.",
        },
        {
            "name": "SAL-QTN-2026-00210",
            "party_name": "Hledan Mobile Trade Center",
            "customer_name": "Hledan Mobile Trade Center",
            "valid_till": "2025-08-17",
            "status": "Ordered",
            "order_lost_reason": None,
        },
        {
            "name": "SAL-QTN-2026-00211",
            "party_name": "Lanmadaw Digital Wholesale",
            "customer_name": "Lanmadaw Digital Wholesale",
            "valid_till": "2025-08-18",
            "status": "Expired",
            "order_lost_reason": None,
        },
        {
            "name": "SAL-QTN-2026-00212",
            "party_name": "Aung Aung Telecom",
            "customer_name": "Aung Aung Telecom",
            "valid_till": "2025-08-20",
            "status": "Ordered",
            "order_lost_reason": None,
        },
    ]

    relink_targets = [
        {
            "invoice_name": "ACC-SINV-2026-00614",
            "sales_order_name": "SAL-ORD-2026-00302",
            "delivery_note_name": "MAT-DN-2026-00275",
            "placeholder_sales_orders": ["SAL-ORD-2026-00333"],
        },
        {
            "invoice_name": "ACC-SINV-2026-00615",
            "sales_order_name": "SAL-ORD-2026-00303",
            "delivery_note_name": "MAT-DN-2026-00276",
            "placeholder_sales_orders": ["SAL-ORD-2026-00334"],
        },
        {
            "invoice_name": "ACC-SINV-2026-00616",
            "sales_order_name": "SAL-ORD-2026-00306",
            "delivery_note_name": "MAT-DN-2026-00277",
            "placeholder_sales_orders": ["SAL-ORD-2026-00335"],
        },
        {
            "invoice_name": "ACC-SINV-2026-00617",
            "sales_order_name": "SAL-ORD-2026-00305",
            "delivery_note_name": None,
            "classification_reason": "quoted wholesale sale retained as direct-billing exception because retrospective dispatch paperwork was not preserved, but the commercial order and invoice are both real",
            "placeholder_sales_orders": [],
        },
        {
            "invoice_name": "ACC-SINV-2026-00618",
            "sales_order_name": None,
            "delivery_note_name": None,
            "classification_reason": "small late-August city counter-wholesale sale retained as direct-billing exception without formal order-to-delivery paperwork",
            "placeholder_sales_orders": ["SAL-ORD-2026-00339"],
        },
    ]

    result = {
        "quotations": [],
        "delivery_note_relinks": [],
        "invoice_relinks": [],
        "canceled_sales_orders": [],
        "failed": [],
    }

    for spec in quotation_updates:
        if not frappe.db.exists("Quotation", spec["name"]):
            continue
        try:
            frappe.db.set_value(
                "Quotation",
                spec["name"],
                {
                    "party_name": spec["party_name"],
                    "customer_name": spec["customer_name"],
                    "valid_till": spec["valid_till"],
                    "status": spec["status"],
                    "order_lost_reason": spec["order_lost_reason"],
                },
                update_modified=False,
            )
            frappe.db.commit()
            result["quotations"].append(
                {
                    "quotation": spec["name"],
                    "party_name": spec["party_name"],
                    "valid_till": spec["valid_till"],
                    "status": spec["status"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["name"], "stage": "quotation_fix", "error": str(exc)})

    for target in relink_targets:
        try:
            if target.get("delivery_note_name"):
                _relink_delivery_note_to_sales_order(target["delivery_note_name"], target["sales_order_name"])
                frappe.db.commit()
                result["delivery_note_relinks"].append(
                    {
                        "delivery_note": target["delivery_note_name"],
                        "sales_order": target["sales_order_name"],
                    }
                )

            relinked = _relink_sales_invoice_to_existing_chain(
                target["invoice_name"],
                target.get("sales_order_name"),
                target.get("delivery_note_name"),
                target.get("classification_reason"),
            )
            result["invoice_relinks"].append(relinked)

            for sales_order_name in target.get("placeholder_sales_orders", []):
                if _cancel_submitted_doc("Sales Order", sales_order_name):
                    frappe.db.commit()
                    result["canceled_sales_orders"].append(sales_order_name)
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"label": target["invoice_name"], "stage": "relink_cleanup", "error": str(exc)}
            )

    return result


def apply_september_2025_workflow_recovery_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    yangon_warehouse = "Yangon Main Warehouse - MMOB"
    mandalay_warehouse = "Mandalay Warehouse - MMOB"

    quotation_specs = [
        {
            "label": "september_capital_ordered_quote",
            "customer": "Capital Telecom (NPT)",
            "company": company,
            "transaction_date": "2025-09-05",
            "valid_till": "2025-09-08",
            "payment_terms_template": "45 Days Approved - MMOB",
            "selling_price_list": "Wholesale Selling - MMOB",
            "set_warehouse": yangon_warehouse,
            "remarks": "September recovery-month quotation for a cautious key-account replenishment after August softness.",
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 4, "rate": 995000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 15, "rate": 110000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 10, "rate": 32000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 10, "rate": 8000, "warehouse": yangon_warehouse},
            ],
        },
        {
            "label": "september_35th_ordered_quote",
            "customer": "35th Street Mobile Wholesale",
            "company": company,
            "transaction_date": "2025-09-18",
            "valid_till": "2025-09-21",
            "payment_terms_template": "30 Days - MMOB",
            "selling_price_list": "Wholesale Selling - MMOB",
            "set_warehouse": mandalay_warehouse,
            "remarks": "September Mandalay wholesale quotation for a measured recovery order with premium devices and power accessories.",
            "items": [
                {"item_code": "SPH-APP-IP14-128", "qty": 3, "rate": 2620000, "warehouse": mandalay_warehouse},
                {"item_code": "ACC-PWB-ANK-10K", "qty": 25, "rate": 85000, "warehouse": mandalay_warehouse},
                {"item_code": "ACC-CHR-ANK-20W", "qty": 40, "rate": 32000, "warehouse": mandalay_warehouse},
            ],
        },
        {
            "label": "september_latha_lost_quote",
            "customer": "Latha Mobile Wholesale",
            "company": company,
            "transaction_date": "2025-09-16",
            "valid_till": "2025-09-19",
            "payment_terms_template": "30 Days - MMOB",
            "selling_price_list": "Wholesale Selling - MMOB",
            "set_warehouse": yangon_warehouse,
            "target_status": "Lost",
            "remarks": "September wholesale inquiry that did not convert after the customer delayed commitment and asked to wait for market direction.",
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 3, "rate": 1000000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 30, "rate": 8000, "warehouse": yangon_warehouse},
            ],
        },
        {
            "label": "september_hlaingtharyar_expired_quote",
            "customer": "Hlaing Tharyar Mobile Corner",
            "company": company,
            "transaction_date": "2025-09-24",
            "valid_till": "2025-09-27",
            "payment_terms_template": "Immediate / Counter Cash - MMOB",
            "selling_price_list": "Retail Selling - MMOB",
            "set_warehouse": yangon_warehouse,
            "target_status": "Expired",
            "remarks": "September township quotation that expired after the customer postponed the pickup to the next month.",
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 1020000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 8, "rate": 110000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 10, "rate": 32000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 10, "rate": 8000, "warehouse": yangon_warehouse},
            ],
        },
    ]

    rebuild_targets = [
        {
            "invoice_name": "ACC-SINV-2026-00619",
            "quotation": {
                "transaction_date": "2025-09-05",
                "valid_till": "2025-09-08",
                "payment_terms_template": "45 Days Approved - MMOB",
                "selling_price_list": "Wholesale Selling - MMOB",
                "set_warehouse": yangon_warehouse,
                "remarks": "September key-account quotation converted after a slower August and tighter replenishment sizing.",
            },
            "sales_order": {
                "transaction_date": "2025-09-08",
                "delivery_date": "2025-09-09",
                "po_no": "CPO-2025-09-401",
                "po_date": "2025-09-08",
                "payment_terms_template": "45 Days Approved - MMOB",
                "set_warehouse": yangon_warehouse,
                "remarks": "September Capital Telecom recovery-order converted from quotation after confirmation of a smaller replenishment plan.",
            },
            "delivery_note": {
                "posting_date": "2025-09-09",
                "posting_time": "11:10:00",
                "remarks": "September Capital Telecom dispatch released under standard key-account fulfillment control.",
            },
            "sales_invoice": {
                "posting_date": "2025-09-09",
                "posting_time": "11:35:00",
                "due_date": "2025-10-24",
                "payment_terms_template": "45 Days Approved - MMOB",
                "remarks": "September Capital Telecom invoice after quotation-driven order and dispatch.",
            },
        },
        {
            "invoice_name": "ACC-SINV-2026-00623",
            "quotation": {
                "transaction_date": "2025-09-18",
                "valid_till": "2025-09-21",
                "payment_terms_template": "30 Days - MMOB",
                "selling_price_list": "Wholesale Selling - MMOB",
                "set_warehouse": mandalay_warehouse,
                "remarks": "September 35th Street quotation for a controlled Mandalay recovery order with premium handset exposure.",
            },
            "sales_order": {
                "transaction_date": "2025-09-20",
                "delivery_date": "2025-09-21",
                "po_no": "CPO-2025-09-402",
                "po_date": "2025-09-20",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": mandalay_warehouse,
                "remarks": "September 35th Street wholesale order converted from quotation as Mandalay demand improved late in the month.",
            },
            "delivery_note": {
                "posting_date": "2025-09-21",
                "posting_time": "13:20:00",
                "remarks": "September 35th Street dispatch completed from Mandalay warehouse after confirmed order release.",
            },
            "sales_invoice": {
                "posting_date": "2025-09-21",
                "posting_time": "13:40:00",
                "due_date": "2025-10-21",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "September 35th Street invoice after quotation-backed wholesale dispatch.",
            },
        },
        {
            "invoice_name": "ACC-SINV-2026-00625",
            "sales_order": {
                "transaction_date": "2025-09-23",
                "delivery_date": "2025-09-24",
                "po_no": "CPO-2025-09-403",
                "po_date": "2025-09-23",
                "payment_terms_template": "15 Days - MMOB",
                "set_warehouse": yangon_warehouse,
                "remarks": "September accessories-led replenishment order from an active Mandalay account under ordinary recovery trading rhythm.",
            },
            "delivery_note": {
                "posting_date": "2025-09-24",
                "posting_time": "12:10:00",
                "remarks": "September Mandalay accessories dispatch from Yangon stock on a short-credit commercial lane.",
            },
            "sales_invoice": {
                "posting_date": "2025-09-24",
                "posting_time": "12:30:00",
                "due_date": "2025-10-09",
                "payment_terms_template": "15 Days - MMOB",
                "remarks": "September Mandalay accessories invoice after direct-order dispatch.",
            },
        },
    ]

    result = {
        "quotations": [],
        "rebuilt_chains": [],
        "payment_repairs": [],
        "failed": [],
    }

    for spec in quotation_specs:
        try:
            spec["expected_total"] = _sum_item_amounts(spec["items"])
            quotation_name = _create_quotation(spec)
            if spec.get("target_status") == "Lost":
                frappe.db.set_value(
                    "Quotation",
                    quotation_name,
                    {
                        "status": "Lost",
                        "order_lost_reason": "September follow-up ended without order confirmation after demand visibility weakened mid-month.",
                    },
                    update_modified=False,
                )
            elif spec.get("target_status") == "Expired":
                frappe.db.set_value(
                    "Quotation",
                    quotation_name,
                    {"status": "Expired", "order_lost_reason": None},
                    update_modified=False,
                )
            frappe.db.commit()
            result["quotations"].append(
                {
                    "label": spec["label"],
                    "quotation": quotation_name,
                    "customer": spec["customer"],
                    "status": spec.get("target_status") or "Submitted",
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "stage": "quotation", "error": str(exc)})

    for target in rebuild_targets:
        try:
            rebuilt = _normalize_direct_stock_invoice_to_delivery_chain(target)
            frappe.db.commit()
            result["rebuilt_chains"].append(rebuilt)
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"label": target["invoice_name"], "stage": "rebuild_chain", "error": str(exc)}
            )

    payment_repairs = [
        {
            "customer": "Capital Telecom (NPT)",
            "transaction_date": "2025-09-08",
            "po_no": "CPO-2025-09-401",
            "expected_total": 6030000,
            "delivery_posting_date": "2025-09-09",
            "payment_date": "2025-09-18",
            "amount": 2000000,
        },
        {
            "customer": "35th Street Mobile Wholesale",
            "transaction_date": "2025-09-20",
            "po_no": "CPO-2025-09-402",
            "expected_total": 11265000,
            "delivery_posting_date": "2025-09-21",
            "payment_date": "2025-12-12",
            "amount": 4000000,
        },
    ]

    for spec in payment_repairs:
        try:
            sales_order_name = _find_submitted_sales_order(
                spec["customer"],
                spec["transaction_date"],
                spec["po_no"],
                spec["expected_total"],
            )
            if not sales_order_name:
                continue
            delivery_note_name = _find_submitted_delivery_note_for_sales_order(
                sales_order_name,
                spec["delivery_posting_date"],
            )
            if not delivery_note_name:
                continue
            invoice_name = _find_submitted_sales_invoice_for_delivery_note(
                delivery_note_name,
                spec["delivery_posting_date"],
            )
            if not invoice_name:
                continue
            payment_name = _create_partial_payment_with_date_dedupe(
                "Sales Invoice",
                invoice_name,
                spec["payment_date"],
                spec["amount"],
            )
            frappe.db.commit()
            result["payment_repairs"].append(
                {
                    "sales_invoice": invoice_name,
                    "payment_entry": payment_name,
                    "posting_date": spec["payment_date"],
                    "amount": spec["amount"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"payment_repair_{spec['customer']}_{spec['payment_date']}",
                    "stage": "payment_repair",
                    "error": str(exc),
                }
            )

    return result


def apply_october_2025_workflow_reality_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    yangon_warehouse = "Yangon Main Warehouse - MMOB"

    quotation_specs = [
        {
            "label": "october_latha_lost_quote",
            "customer": "Latha Mobile Wholesale",
            "company": company,
            "transaction_date": "2025-10-17",
            "valid_till": "2025-10-20",
            "payment_terms_template": "30 Days - MMOB",
            "selling_price_list": "Wholesale Selling - MMOB",
            "set_warehouse": yangon_warehouse,
            "target_status": "Lost",
            "remarks": "October festival-period inquiry that did not convert after the customer cut back replenishment during the slower dispatch window.",
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 1030000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 6, "rate": 150000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000, "warehouse": yangon_warehouse},
            ],
        },
        {
            "label": "october_taunggyi_expired_quote",
            "customer": "Taunggyi City Mobile",
            "company": company,
            "transaction_date": "2025-10-21",
            "valid_till": "2025-10-23",
            "payment_terms_template": "30 Days - MMOB",
            "selling_price_list": "Wholesale Selling - MMOB",
            "set_warehouse": yangon_warehouse,
            "target_status": "Expired",
            "remarks": "October township inquiry that expired when the customer delayed commitment until after the holiday slowdown.",
            "items": [
                {"item_code": "SPH-APP-IP14-128", "qty": 1, "rate": 2650000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-PWB-ANK-10K", "qty": 5, "rate": 130000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-CHR-ANK-20W", "qty": 10, "rate": 48000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000, "warehouse": yangon_warehouse},
            ],
        },
    ]

    rebuild_targets = [
        {
            "invoice_name": "ACC-SINV-2026-00631",
            "quotation": {
                "transaction_date": "2025-10-13",
                "valid_till": "2025-10-15",
                "payment_terms_template": "30 Days - MMOB",
                "selling_price_list": "Wholesale Selling - MMOB",
                "set_warehouse": yangon_warehouse,
                "remarks": "October Hledan quotation for a carefully sized handset and accessories restock during the holiday lull.",
            },
            "sales_order": {
                "transaction_date": "2025-10-15",
                "delivery_date": "2025-10-16",
                "po_no": "CPO-2025-10-501",
                "po_date": "2025-10-15",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": yangon_warehouse,
                "remarks": "October Hledan wholesale order converted from quotation after the customer confirmed a measured pre-weekend restock.",
            },
            "delivery_note": {
                "posting_date": "2025-10-16",
                "posting_time": "11:10:00",
                "remarks": "October Hledan dispatch completed under normal wholesale fulfillment despite softer overall month activity.",
            },
            "sales_invoice": {
                "posting_date": "2025-10-16",
                "posting_time": "11:35:00",
                "due_date": "2025-11-15",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "October Hledan invoice after quotation-backed order and delivery execution.",
            },
        },
        {
            "invoice_name": "ACC-SINV-2026-00637",
            "sales_order": {
                "transaction_date": "2025-10-27",
                "delivery_date": "2025-10-28",
                "po_no": "CPO-2025-10-502",
                "po_date": "2025-10-27",
                "payment_terms_template": "15 Days - MMOB",
                "set_warehouse": yangon_warehouse,
                "remarks": "October Lanmadaw repeat order placed directly without quotation for a smaller accessories-led replenishment lane.",
            },
            "delivery_note": {
                "posting_date": "2025-10-28",
                "posting_time": "10:50:00",
                "remarks": "October Lanmadaw dispatch released directly from repeat-order confirmation during the softer trading window.",
            },
            "sales_invoice": {
                "posting_date": "2025-10-28",
                "posting_time": "11:20:00",
                "due_date": "2025-11-12",
                "payment_terms_template": "15 Days - MMOB",
                "remarks": "October Lanmadaw invoice after direct order and dispatch fulfillment in the festival-soft month.",
            },
        },
        {
            "invoice_name": "ACC-SINV-2026-00090",
            "sales_order": {
                "transaction_date": "2025-10-29",
                "delivery_date": "2025-10-30",
                "po_no": "CPO-2025-10-503",
                "po_date": "2025-10-29",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": yangon_warehouse,
                "remarks": "October 35th Street order placed directly after a small late-month wholesale replenishment request.",
            },
            "delivery_note": {
                "posting_date": "2025-10-30",
                "posting_time": "12:05:00",
                "remarks": "October 35th Street dispatch completed under ordinary small-batch wholesale handling.",
            },
            "sales_invoice": {
                "posting_date": "2025-10-30",
                "posting_time": "12:30:00",
                "due_date": "2025-11-29",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "October 35th Street invoice after direct order and dispatch completion.",
            },
        },
        {
            "invoice_name": "ACC-SINV-2026-00639",
            "quotation": {
                "transaction_date": "2025-10-28",
                "valid_till": "2025-10-30",
                "payment_terms_template": "45 Days Approved - MMOB",
                "selling_price_list": "Wholesale Selling - MMOB",
                "set_warehouse": yangon_warehouse,
                "remarks": "October Hlaing Tharyar quotation for a conservative month-end township replenishment before normal trade resumed.",
            },
            "sales_order": {
                "transaction_date": "2025-10-30",
                "delivery_date": "2025-10-31",
                "po_no": "CPO-2025-10-504",
                "po_date": "2025-10-30",
                "payment_terms_template": "45 Days Approved - MMOB",
                "set_warehouse": yangon_warehouse,
                "remarks": "October Hlaing Tharyar order converted from quotation after late-month confirmation of a limited restock.",
            },
            "delivery_note": {
                "posting_date": "2025-10-31",
                "posting_time": "15:20:00",
                "remarks": "October Hlaing Tharyar dispatch completed as a late-month controlled release.",
            },
            "sales_invoice": {
                "posting_date": "2025-10-31",
                "posting_time": "15:45:00",
                "due_date": "2025-12-15",
                "payment_terms_template": "45 Days Approved - MMOB",
                "remarks": "October Hlaing Tharyar invoice after quotation-backed order and delivery completion.",
            },
        },
    ]

    result = {
        "credit_limits": [],
        "quotations": [],
        "rebuilt_chains": [],
        "recreated_direct_invoices": [],
        "failed": [],
    }

    for spec in quotation_specs:
        try:
            spec["expected_total"] = _sum_item_amounts(spec["items"])
            quotation_name = _create_quotation(spec)
            if spec.get("target_status") == "Lost":
                frappe.db.set_value(
                    "Quotation",
                    quotation_name,
                    {
                        "status": "Lost",
                        "order_lost_reason": "October follow-up ended without order confirmation because the customer deferred replenishment during the Thadingyut slowdown.",
                    },
                    update_modified=False,
                )
            elif spec.get("target_status") == "Expired":
                frappe.db.set_value(
                    "Quotation",
                    quotation_name,
                    {"status": "Expired", "order_lost_reason": None},
                    update_modified=False,
                )
            frappe.db.commit()
            result["quotations"].append(
                {
                    "label": spec["label"],
                    "quotation": quotation_name,
                    "customer": spec["customer"],
                    "status": spec.get("target_status") or "Submitted",
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "stage": "quotation", "error": str(exc)})

    for target in rebuild_targets:
        try:
            rebuilt = _normalize_direct_stock_invoice_to_delivery_chain(target)
            frappe.db.commit()
            result["rebuilt_chains"].append(rebuilt)
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"label": target["invoice_name"], "stage": "rebuild_chain", "error": str(exc)}
            )

    credit_limit_targets = {
        "Mayangone Mobile House": 40000000,
        "Thingangyun Mobile House": 50000000,
        "Taunggyi Star Mobile": 40000000,
    }

    for customer_name, credit_limit in credit_limit_targets.items():
        try:
            customer = frappe.get_doc("Customer", customer_name)
            limit_row = None
            for row in customer.credit_limits:
                if row.company == company:
                    limit_row = row
                    break
            current_outstanding = float(
                frappe.db.sql(
                    """
                    select ifnull(sum(outstanding_amount), 0)
                    from `tabSales Invoice`
                    where customer = %s and docstatus = 1 and outstanding_amount > 0
                    """,
                    (customer_name,),
                )[0][0]
                or 0
            )
            effective_credit_limit = max(float(credit_limit), current_outstanding + 5000000)
            if limit_row:
                limit_row.credit_limit = effective_credit_limit
                limit_row.bypass_credit_limit_check = 0
            else:
                customer.append(
                    "credit_limits",
                    {
                        "company": company,
                        "credit_limit": effective_credit_limit,
                        "bypass_credit_limit_check": 0,
                    },
                )
            customer.save(ignore_permissions=True)
            frappe.db.commit()
            result["credit_limits"].append({"customer": customer_name, "credit_limit": effective_credit_limit})
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"label": f"credit_limit_{customer_name}", "stage": "credit_limit", "error": str(exc)}
            )

    restore_specs = [
        {
            "invoice_name": "ACC-SINV-2026-00632",
            "payment_specs": [{"posting_date": "2025-10-22", "amount": 2500000}],
            "remarks_suffix": "October Mayangone lane restored as a direct stock invoice after workflow reconstruction was blocked by live credit policy.",
        },
        {
            "invoice_name": "ACC-SINV-2026-00634",
            "payment_specs": [{"posting_date": "2025-10-27", "amount": 3000000}],
            "remarks_suffix": "October Thingangyun lane restored as a direct stock invoice after workflow reconstruction was blocked by live credit policy.",
        },
        {
            "invoice_name": "ACC-SINV-2026-00638",
            "payment_specs": [{"posting_date": "2025-10-31", "amount": 2000000}],
            "remarks_suffix": "October Taunggyi Star lane restored as a direct stock invoice after workflow reconstruction was blocked by live credit policy.",
        },
    ]

    for spec in restore_specs:
        try:
            recreated = _recreate_canceled_stock_sales_invoice(
                spec["invoice_name"],
                payment_specs=spec["payment_specs"],
                remarks_suffix=spec["remarks_suffix"],
            )
            frappe.db.commit()
            result["recreated_direct_invoices"].append(recreated)
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"label": spec["invoice_name"], "stage": "restore_direct_invoice", "error": str(exc)}
            )

    return result


def apply_november_2025_controlled_restart_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    yangon_warehouse = "Yangon Main Warehouse - MMOB"

    quotation_specs = [
        {
            "label": "november_bayint_lost_quote",
            "customer": "Bayint Naung Wholesale Mobile",
            "company": company,
            "transaction_date": "2025-11-11",
            "valid_till": "2025-11-14",
            "payment_terms_template": "30 Days - MMOB",
            "selling_price_list": "Wholesale Selling - MMOB",
            "set_warehouse": yangon_warehouse,
            "target_status": "Lost",
            "remarks": "November Bayint quotation that did not convert after the customer limited replenishment and focused on collecting older downstream balances.",
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 3, "rate": 1025000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 145000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 30, "rate": 14000, "warehouse": yangon_warehouse},
            ],
        },
        {
            "label": "november_mandalay_expired_quote",
            "customer": "Mandalay Accessories Wholesale",
            "company": company,
            "transaction_date": "2025-11-26",
            "valid_till": "2025-11-28",
            "payment_terms_template": "15 Days - MMOB",
            "selling_price_list": "Wholesale Selling - MMOB",
            "set_warehouse": yangon_warehouse,
            "target_status": "Expired",
            "remarks": "November Mandalay accessories quotation that expired when the customer postponed the pickup into the heavier December restock window.",
            "items": [
                {"item_code": "ACC-PWB-BAS-20K", "qty": 20, "rate": 145000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 40, "rate": 32000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 30, "rate": 30000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000, "warehouse": yangon_warehouse},
            ],
        },
    ]

    credit_limit_targets = {
        "Hledan Phone Hub": 60000000,
        "Thingangyun Mobile House": 50000000,
        "Hlaing Tharyar Mobile Corner": 60000000,
        "Lanmadaw Telecom & Gadgets": 40000000,
    }

    rebuild_targets = [
        {
            "invoice_name": "ACC-SINV-2026-00641",
            "quotation": {
                "transaction_date": "2025-11-05",
                "valid_till": "2025-11-07",
                "payment_terms_template": "30 Days - MMOB",
                "selling_price_list": "Wholesale Selling - MMOB",
                "set_warehouse": yangon_warehouse,
                "remarks": "November Hledan quotation for a controlled restart-month replenishment after the softer October cycle.",
            },
            "sales_order": {
                "transaction_date": "2025-11-07",
                "delivery_date": "2025-11-08",
                "po_no": "CPO-2025-11-601",
                "po_date": "2025-11-07",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": yangon_warehouse,
                "remarks": "November Hledan order converted from quotation as dealer replenishment resumed in a measured way.",
            },
            "delivery_note": {
                "posting_date": "2025-11-08",
                "posting_time": "11:05:00",
                "remarks": "November Hledan dispatch released under ordinary restart-month wholesale handling.",
            },
            "sales_invoice": {
                "posting_date": "2025-11-08",
                "posting_time": "11:30:00",
                "due_date": "2025-12-08",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "November Hledan invoice after quotation-backed order and delivery execution.",
            },
        },
        {
            "invoice_name": "ACC-SINV-2026-00644",
            "sales_order": {
                "transaction_date": "2025-11-21",
                "delivery_date": "2025-11-22",
                "po_no": "CPO-2025-11-602",
                "po_date": "2025-11-21",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": yangon_warehouse,
                "remarks": "November Thingangyun repeat wholesale order placed directly by phone as normal trading resumed after the holiday lull.",
            },
            "delivery_note": {
                "posting_date": "2025-11-22",
                "posting_time": "12:05:00",
                "remarks": "November Thingangyun dispatch completed under standard direct-order fulfillment.",
            },
            "sales_invoice": {
                "posting_date": "2025-11-22",
                "posting_time": "12:30:00",
                "due_date": "2025-12-22",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "November Thingangyun invoice after direct order and dispatch completion.",
            },
        },
        {
            "invoice_name": "ACC-SINV-2026-00646",
            "quotation": {
                "transaction_date": "2025-11-17",
                "valid_till": "2025-11-19",
                "payment_terms_template": "45 Days Approved - MMOB",
                "selling_price_list": "Wholesale Selling - MMOB",
                "set_warehouse": yangon_warehouse,
                "remarks": "November Hlaing Tharyar quotation for a careful township restock as commercial activity restarted but remained controlled.",
            },
            "sales_order": {
                "transaction_date": "2025-11-19",
                "delivery_date": "2025-11-20",
                "po_no": "CPO-2025-11-603",
                "po_date": "2025-11-19",
                "payment_terms_template": "45 Days Approved - MMOB",
                "set_warehouse": yangon_warehouse,
                "remarks": "November Hlaing Tharyar order converted from quotation after late confirmation of a moderate restock.",
            },
            "delivery_note": {
                "posting_date": "2025-11-20",
                "posting_time": "14:20:00",
                "remarks": "November Hlaing Tharyar dispatch completed from Yangon under restart-month control.",
            },
            "sales_invoice": {
                "posting_date": "2025-11-20",
                "posting_time": "14:45:00",
                "due_date": "2026-01-04",
                "payment_terms_template": "45 Days Approved - MMOB",
                "remarks": "November Hlaing Tharyar invoice after quotation-backed order and dispatch completion.",
            },
        },
        {
            "invoice_name": "ACC-SINV-2026-00648",
            "sales_order": {
                "transaction_date": "2025-11-23",
                "delivery_date": "2025-11-24",
                "po_no": "CPO-2025-11-604",
                "po_date": "2025-11-23",
                "payment_terms_template": "15 Days - MMOB",
                "set_warehouse": yangon_warehouse,
                "remarks": "November Lanmadaw accessories-led order placed directly on a repeat lane without a formal quotation step.",
            },
            "delivery_note": {
                "posting_date": "2025-11-24",
                "posting_time": "11:40:00",
                "remarks": "November Lanmadaw dispatch released directly after repeat-order confirmation.",
            },
            "sales_invoice": {
                "posting_date": "2025-11-24",
                "posting_time": "12:00:00",
                "due_date": "2025-12-09",
                "payment_terms_template": "15 Days - MMOB",
                "remarks": "November Lanmadaw invoice after direct order and dispatch fulfillment.",
            },
        },
    ]

    result = {
        "credit_limits": [],
        "quotations": [],
        "rebuilt_chains": [],
        "failed": [],
    }

    for customer_name, credit_limit in credit_limit_targets.items():
        try:
            customer = frappe.get_doc("Customer", customer_name)
            limit_row = None
            for row in customer.credit_limits:
                if row.company == company:
                    limit_row = row
                    break
            if limit_row:
                limit_row.credit_limit = credit_limit
                limit_row.bypass_credit_limit_check = 0
            else:
                customer.append(
                    "credit_limits",
                    {
                        "company": company,
                        "credit_limit": credit_limit,
                        "bypass_credit_limit_check": 0,
                    },
                )
            customer.save(ignore_permissions=True)
            frappe.db.commit()
            result["credit_limits"].append({"customer": customer_name, "credit_limit": credit_limit})
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"label": f"credit_limit_{customer_name}", "stage": "credit_limit", "error": str(exc)}
            )

    for spec in quotation_specs:
        try:
            spec["expected_total"] = _sum_item_amounts(spec["items"])
            quotation_name = _create_quotation(spec)
            if spec.get("target_status") == "Lost":
                frappe.db.set_value(
                    "Quotation",
                    quotation_name,
                    {
                        "status": "Lost",
                        "order_lost_reason": "November follow-up ended without order confirmation as the customer chose to defer restocking until cash rotation improved.",
                    },
                    update_modified=False,
                )
            elif spec.get("target_status") == "Expired":
                frappe.db.set_value(
                    "Quotation",
                    quotation_name,
                    {"status": "Expired", "order_lost_reason": None},
                    update_modified=False,
                )
            frappe.db.commit()
            result["quotations"].append(
                {
                    "label": spec["label"],
                    "quotation": quotation_name,
                    "customer": spec["customer"],
                    "status": spec.get("target_status") or "Submitted",
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "stage": "quotation", "error": str(exc)})

    for target in rebuild_targets:
        try:
            rebuilt = _normalize_direct_stock_invoice_to_delivery_chain(target)
            frappe.db.commit()
            result["rebuilt_chains"].append(rebuilt)
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"label": target["invoice_name"], "stage": "rebuild_chain", "error": str(exc)}
            )

    return result


def apply_december_2025_year_end_workflow_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    yangon_warehouse = "Yangon Main Warehouse - MMOB"

    quotation_specs = [
        {
            "label": "december_pazundaung_lost_quote",
            "customer": "Pazundaung Phone House",
            "company": company,
            "transaction_date": "2025-12-09",
            "valid_till": "2025-12-12",
            "payment_terms_template": "15 Days - MMOB",
            "selling_price_list": "Wholesale Selling - MMOB",
            "set_warehouse": yangon_warehouse,
            "target_status": "Lost",
            "remarks": "December year-end inquiry that did not convert after the customer reduced commitment to preserve cash for staff payments and year-end settlement.",
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 3, "rate": 1030000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 12, "rate": 145000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 24, "rate": 32000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 30, "rate": 8000, "warehouse": yangon_warehouse},
            ],
        },
        {
            "label": "december_mandalay_hub_expired_quote",
            "customer": "Mandalay Mobile Hub",
            "company": company,
            "transaction_date": "2025-12-20",
            "valid_till": "2025-12-23",
            "payment_terms_template": "30 Days - MMOB",
            "selling_price_list": "Wholesale Selling - MMOB",
            "set_warehouse": yangon_warehouse,
            "target_status": "Expired",
            "remarks": "December branch-restock quotation that expired when intercity pickup was delayed by year-end staffing and transport congestion.",
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 3, "rate": 900000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 15, "rate": 145000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 25, "rate": 30000, "warehouse": yangon_warehouse},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 12, "rate": 58000, "warehouse": yangon_warehouse},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000, "warehouse": yangon_warehouse},
            ],
        },
    ]

    credit_limit_targets = {
        "Hledan Phone Hub": 60000000,
        "Hlaing Tharyar Mobile Corner": 60000000,
        "Thingangyun Mobile House": 50000000,
        "Lanmadaw Telecom & Gadgets": 45000000,
        "Mandalay Accessories Wholesale": 50000000,
        "Mayangone Mobile House": 40000000,
    }

    rebuild_targets = [
        {
            "invoice_name": "ACC-SINV-2026-00651",
            "quotation": {
                "transaction_date": "2025-12-08",
                "valid_till": "2025-12-10",
                "payment_terms_template": "30 Days - MMOB",
                "selling_price_list": "Wholesale Selling - MMOB",
                "set_warehouse": yangon_warehouse,
                "remarks": "December Hledan year-end replenishment quotation covering a stronger handset-led restock before holiday week demand.",
            },
            "sales_order": {
                "transaction_date": "2025-12-10",
                "delivery_date": "2025-12-10",
                "po_no": "CPO-2025-12-701",
                "po_date": "2025-12-10",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": yangon_warehouse,
                "remarks": "December Hledan order converted quickly after the customer confirmed year-end replenishment for faster handset turnover.",
            },
            "delivery_note": {
                "posting_date": "2025-12-10",
                "posting_time": "11:00:00",
                "remarks": "December Hledan dispatch released on the same day to support year-end showroom demand and cash rotation.",
            },
            "sales_invoice": {
                "posting_date": "2025-12-10",
                "posting_time": "11:25:00",
                "due_date": "2026-01-09",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "December Hledan invoice after quotation-backed order and same-day dispatch execution.",
            },
        },
        {
            "invoice_name": "ACC-SINV-2026-00652",
            "quotation": {
                "transaction_date": "2025-12-23",
                "valid_till": "2025-12-24",
                "payment_terms_template": "45 Days Approved - MMOB",
                "selling_price_list": "Wholesale Selling - MMOB",
                "set_warehouse": yangon_warehouse,
                "remarks": "December Hlaing Tharyar key-account quotation for a higher-value year-end mixed-brand restock.",
            },
            "sales_order": {
                "transaction_date": "2025-12-24",
                "delivery_date": "2025-12-25",
                "po_no": "CPO-2025-12-702",
                "po_date": "2025-12-24",
                "payment_terms_template": "45 Days Approved - MMOB",
                "set_warehouse": yangon_warehouse,
                "remarks": "December Hlaing Tharyar order converted from quotation after year-end allocation and credit confirmation.",
            },
            "delivery_note": {
                "posting_date": "2025-12-25",
                "posting_time": "13:15:00",
                "remarks": "December Hlaing Tharyar dispatch completed after holiday-period stock preparation for a stronger township lane.",
            },
            "sales_invoice": {
                "posting_date": "2025-12-25",
                "posting_time": "13:40:00",
                "due_date": "2026-02-08",
                "payment_terms_template": "45 Days Approved - MMOB",
                "remarks": "December Hlaing Tharyar invoice after quotation-backed order and delivery completion.",
            },
        },
        {
            "invoice_name": "ACC-SINV-2026-00654",
            "sales_order": {
                "transaction_date": "2025-12-25",
                "delivery_date": "2025-12-26",
                "po_no": "CPO-2025-12-703",
                "po_date": "2025-12-25",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": yangon_warehouse,
                "remarks": "December Thingangyun repeat order placed directly by phone for a fast township year-end top-up without a formal quotation.",
            },
            "delivery_note": {
                "posting_date": "2025-12-26",
                "posting_time": "11:20:00",
                "remarks": "December Thingangyun dispatch completed on the ordinary repeat-order lane during the year-end peak window.",
            },
            "sales_invoice": {
                "posting_date": "2025-12-26",
                "posting_time": "11:45:00",
                "due_date": "2026-01-25",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "December Thingangyun invoice after direct order and dispatch execution.",
            },
        },
        {
            "invoice_name": "ACC-SINV-2026-00656",
            "sales_order": {
                "transaction_date": "2025-12-26",
                "delivery_date": "2025-12-27",
                "po_no": "CPO-2025-12-704",
                "po_date": "2025-12-26",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": yangon_warehouse,
                "remarks": "December Mayangone repeat wholesale order confirmed directly to refill fast-moving devices and accessories before month-end.",
            },
            "delivery_note": {
                "posting_date": "2025-12-27",
                "posting_time": "10:55:00",
                "remarks": "December Mayangone dispatch released immediately after warehouse picking for the year-end restock lane.",
            },
            "sales_invoice": {
                "posting_date": "2025-12-27",
                "posting_time": "11:20:00",
                "due_date": "2026-01-26",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "December Mayangone invoice after direct repeat-order fulfillment.",
            },
        },
        {
            "invoice_name": "ACC-SINV-2026-00657",
            "sales_order": {
                "transaction_date": "2025-12-25",
                "delivery_date": "2025-12-26",
                "po_no": "CPO-2025-12-705",
                "po_date": "2025-12-25",
                "payment_terms_template": "15 Days - MMOB",
                "set_warehouse": yangon_warehouse,
                "remarks": "December Lanmadaw mixed-device order placed directly on a repeat lane as the customer accelerated year-end sell-through.",
            },
            "delivery_note": {
                "posting_date": "2025-12-26",
                "posting_time": "14:10:00",
                "remarks": "December Lanmadaw dispatch completed under a faster repeat-order lane before month-end customer traffic intensified.",
            },
            "sales_invoice": {
                "posting_date": "2025-12-26",
                "posting_time": "14:30:00",
                "due_date": "2026-01-10",
                "payment_terms_template": "15 Days - MMOB",
                "remarks": "December Lanmadaw invoice after direct repeat-order dispatch completion.",
            },
        },
        {
            "invoice_name": "ACC-SINV-2026-00660",
            "quotation": {
                "transaction_date": "2025-12-24",
                "valid_till": "2025-12-26",
                "payment_terms_template": "15 Days - MMOB",
                "selling_price_list": "Wholesale Selling - MMOB",
                "set_warehouse": yangon_warehouse,
                "remarks": "December Mandalay accessories quotation for a balanced year-end replenishment mixing handsets with faster-moving add-ons.",
            },
            "sales_order": {
                "transaction_date": "2025-12-26",
                "delivery_date": "2025-12-27",
                "po_no": "CPO-2025-12-706",
                "po_date": "2025-12-26",
                "payment_terms_template": "15 Days - MMOB",
                "set_warehouse": yangon_warehouse,
                "remarks": "December Mandalay accessories order converted from quotation after the customer finalized year-end pickup volume.",
            },
            "delivery_note": {
                "posting_date": "2025-12-27",
                "posting_time": "15:10:00",
                "remarks": "December Mandalay dispatch released after quotation conversion and final warehouse packing before weekend trucking.",
            },
            "sales_invoice": {
                "posting_date": "2025-12-27",
                "posting_time": "15:35:00",
                "due_date": "2026-01-11",
                "payment_terms_template": "15 Days - MMOB",
                "remarks": "December Mandalay invoice after quotation-backed order and dispatch completion.",
            },
        },
    ]

    result = {
        "credit_limits": [],
        "quotations": [],
        "rebuilt_chains": [],
        "failed": [],
    }

    for customer_name, credit_limit in credit_limit_targets.items():
        try:
            customer = frappe.get_doc("Customer", customer_name)
            limit_row = None
            for row in customer.credit_limits:
                if row.company == company:
                    limit_row = row
                    break
            if limit_row:
                limit_row.credit_limit = credit_limit
                limit_row.bypass_credit_limit_check = 0
            else:
                customer.append(
                    "credit_limits",
                    {
                        "company": company,
                        "credit_limit": credit_limit,
                        "bypass_credit_limit_check": 0,
                    },
                )
            customer.save(ignore_permissions=True)
            frappe.db.commit()
            result["credit_limits"].append({"customer": customer_name, "credit_limit": credit_limit})
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"label": f"credit_limit_{customer_name}", "stage": "credit_limit", "error": str(exc)}
            )

    for spec in quotation_specs:
        try:
            spec["expected_total"] = _sum_item_amounts(spec["items"])
            quotation_name = _create_quotation(spec)
            if spec.get("target_status") == "Lost":
                frappe.db.set_value(
                    "Quotation",
                    quotation_name,
                    {
                        "status": "Lost",
                        "order_lost_reason": "Year-end follow-up ended without order confirmation because the customer prioritized cash preservation and delayed replenishment to the new calendar year.",
                    },
                    update_modified=False,
                )
            elif spec.get("target_status") == "Expired":
                frappe.db.set_value(
                    "Quotation",
                    quotation_name,
                    {"status": "Expired", "order_lost_reason": None},
                    update_modified=False,
                )
            frappe.db.commit()
            result["quotations"].append(
                {
                    "label": spec["label"],
                    "quotation": quotation_name,
                    "customer": spec["customer"],
                    "status": spec.get("target_status") or "Submitted",
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "stage": "quotation", "error": str(exc)})

    for target in rebuild_targets:
        try:
            rebuilt = _normalize_direct_stock_invoice_to_delivery_chain(target)
            frappe.db.commit()
            result["rebuilt_chains"].append(rebuilt)
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {"label": target["invoice_name"], "stage": "rebuild_chain", "error": str(exc)}
            )

    return result


def apply_december_2025_commercial_uplift_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    warehouse = "Yangon Main Warehouse - MMOB"

    support_purchase_defs = [
        {
            "supplier": "Myanmar Tech Import Services",
            "posting_date": "2025-12-29",
            "due_date": "2026-01-28",
            "company": company,
            "items": [
                {"item_code": "SPH-APP-IP14-128", "qty": 2, "rate": 2210000, "warehouse": warehouse},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 20000, "warehouse": warehouse},
            ],
        }
    ]

    quotation_specs = [
        {
            "label": "december_capital_year_end_quote",
            "customer": "Capital Telecom (NPT)",
            "company": company,
            "transaction_date": "2025-12-28",
            "valid_till": "2025-12-29",
            "payment_terms_template": "45 Days Approved - MMOB",
            "selling_price_list": "Wholesale Selling - MMOB",
            "set_warehouse": warehouse,
            "remarks": "Late-December key-account quotation for year-end replenishment before Naypyitaw public-sector and reseller traffic resumed after the holiday week.",
            "items": [
                {"item_code": "SPH-APP-IP14-128", "qty": 3, "rate": 2650000, "warehouse": warehouse},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 4, "rate": 900000, "warehouse": warehouse},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 20, "rate": 110000, "warehouse": warehouse},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 40, "rate": 30000, "warehouse": warehouse},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000, "warehouse": warehouse},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 2, "rate": 220000, "warehouse": warehouse},
            ],
        }
    ]

    chain_specs = [
        {
            "label": "december_capital_year_end_quote_chain",
            "customer": "Capital Telecom (NPT)",
            "quotation_label": "december_capital_year_end_quote",
            "sales_order": {
                "transaction_date": "2025-12-29",
                "delivery_date": "2025-12-30",
                "po_no": "CPO-2025-12-707",
                "po_date": "2025-12-29",
                "payment_terms_template": "45 Days Approved - MMOB",
                "set_warehouse": warehouse,
                "remarks": "Late-December Capital Telecom order converted from approved quotation as the customer locked year-end replenishment before January demand.",
            },
            "delivery_note": {
                "posting_date": "2025-12-30",
                "posting_time": "11:10:00",
                "remarks": "Late-December Capital Telecom dispatch released on a priority lane after credit and packing confirmation.",
            },
            "sales_invoice": {
                "posting_date": "2025-12-30",
                "posting_time": "11:35:00",
                "due_date": "2026-02-13",
                "payment_terms_template": "45 Days Approved - MMOB",
                "remarks": "Late-December Capital Telecom invoice after quotation-backed order and priority delivery completion.",
            },
        },
        {
            "label": "december_35th_direct_wholesale_chain",
            "customer": "35th Street Mobile Wholesale",
            "sales_order": {
                "transaction_date": "2025-12-29",
                "delivery_date": "2025-12-30",
                "po_no": "CPO-2025-12-708",
                "po_date": "2025-12-29",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "Late-December Mandalay wholesale order placed directly on a repeat lane after stronger-than-expected accessory sell-through.",
            },
            "delivery_note": {
                "posting_date": "2025-12-30",
                "posting_time": "14:15:00",
                "remarks": "Late-December 35th Street dispatch released after year-end restock confirmation for the Mandalay lane.",
            },
            "sales_invoice": {
                "posting_date": "2025-12-30",
                "posting_time": "14:35:00",
                "due_date": "2026-01-29",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "Late-December 35th Street invoice after direct order and dispatch execution.",
            },
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 2, "rate": 2150000, "warehouse": warehouse},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 3, "rate": 1000000, "warehouse": warehouse},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 5, "rate": 220000, "warehouse": warehouse},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000, "warehouse": warehouse},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 30, "rate": 30000, "warehouse": warehouse},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 50, "rate": 8000, "warehouse": warehouse},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000, "warehouse": warehouse},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000, "warehouse": warehouse},
            ],
        },
    ]

    direct_sales_defs = [
        {
            "customer": "City Mobile Mart",
            "posting_date": "2025-12-31",
            "due_date": "2026-01-05",
            "warehouse": warehouse,
            "company": company,
            "remarks": "Late-December direct showroom and dealer-support invoice after urgent mixed-stock pickup on the final business day of the month.",
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 1000000, "warehouse": warehouse},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 900000, "warehouse": warehouse},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000, "warehouse": warehouse},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000, "warehouse": warehouse},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000, "warehouse": warehouse},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000, "warehouse": warehouse},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 2, "rate": 220000, "warehouse": warehouse},
            ],
        }
    ]

    payment_specs = [
        ("Capital Telecom (NPT)", "2025-12-30", "2025-12-31", 5000000),
        ("35th Street Mobile Wholesale", "2025-12-30", "2025-12-31", 3000000),
        ("City Mobile Mart", "2025-12-31", "2025-12-31", 2000000),
    ]

    quotation_lookup: dict[str, str] = {}
    quotation_spec_lookup = {spec["label"]: spec for spec in quotation_specs}
    invoice_lookup: dict[tuple[str, str], str] = {}
    result = {
        "purchase_invoices": [],
        "quotations": [],
        "sales_orders": [],
        "delivery_notes": [],
        "sales_invoices": [],
        "payment_entries": [],
        "failed": [],
    }

    for supplier_def in support_purchase_defs:
        try:
            supplier_def["expected_total"] = _sum_item_amounts(supplier_def["items"])
            purchase_invoice_name = _create_purchase_invoice(supplier_def)
            frappe.db.commit()
            result["purchase_invoices"].append(
                {
                    "supplier": supplier_def["supplier"],
                    "purchase_invoice": purchase_invoice_name,
                    "posting_date": supplier_def["posting_date"],
                    "grand_total": supplier_def["expected_total"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"support_purchase_{supplier_def['supplier']}_{supplier_def['posting_date']}",
                    "stage": "support_purchase",
                    "error": str(exc),
                }
            )

    for spec in quotation_specs:
        try:
            spec["expected_total"] = _sum_item_amounts(spec["items"])
            quotation_name = _create_quotation(spec)
            quotation_lookup[spec["label"]] = quotation_name
            frappe.db.commit()
            result["quotations"].append(
                {
                    "label": spec["label"],
                    "quotation": quotation_name,
                    "customer": spec["customer"],
                    "grand_total": spec["expected_total"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "stage": "quotation", "error": str(exc)})

    for spec in chain_specs:
        try:
            if spec.get("quotation_label"):
                expected_total = _sum_item_amounts(
                    quotation_spec_lookup[spec["quotation_label"]]["items"]
                )
                try:
                    order_name = _create_sales_order_from_quotation(
                        quotation_lookup[spec["quotation_label"]],
                        {
                            **spec["sales_order"],
                            "customer": spec["customer"],
                            "expected_total": expected_total,
                        },
                    )
                except Exception as exc:
                    if "Validity period of this quotation has ended." not in str(exc):
                        raise
                    order_name = _create_sales_order(
                        {
                            **spec["sales_order"],
                            "customer": spec["customer"],
                            "company": company,
                            "items": list(quotation_spec_lookup[spec["quotation_label"]]["items"]),
                            "expected_total": expected_total,
                            "remarks": f"{spec['sales_order'].get('remarks') or ''} Historical year-end quotation conversion recreated directly because ERP quotation validity blocked late posting in the live system.",
                        }
                    )
                frappe.db.set_value(
                    "Quotation",
                    quotation_lookup[spec["quotation_label"]],
                    {"status": "Ordered"},
                    update_modified=False,
                )
            else:
                expected_total = _sum_item_amounts(spec["items"])
                order_name = _create_sales_order(
                    {
                        **spec["sales_order"],
                        "customer": spec["customer"],
                        "company": company,
                        "items": list(spec["items"]),
                        "expected_total": expected_total,
                    }
                )

            delivery_note_name = _create_delivery_note_from_sales_order(
                order_name,
                spec["delivery_note"],
            )
            invoice_name = _create_sales_invoice_from_delivery_note(
                delivery_note_name,
                spec["sales_invoice"],
            )
            frappe.db.commit()

            invoice_lookup[(spec["customer"], spec["sales_invoice"]["posting_date"])] = invoice_name
            result["sales_orders"].append(
                {
                    "label": spec["label"],
                    "sales_order": order_name,
                    "customer": spec["customer"],
                    "grand_total": expected_total,
                }
            )
            result["delivery_notes"].append(
                {
                    "label": spec["label"],
                    "delivery_note": delivery_note_name,
                    "sales_order": order_name,
                }
            )
            result["sales_invoices"].append(
                {
                    "label": spec["label"],
                    "sales_invoice": invoice_name,
                    "customer": spec["customer"],
                    "posting_date": spec["sales_invoice"]["posting_date"],
                    "grand_total": expected_total,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "stage": "chain", "error": str(exc)})

    for definition in direct_sales_defs:
        try:
            definition["expected_total"] = _sum_item_amounts(definition["items"])
            invoice_name = _create_sales_invoice(definition)
            frappe.db.commit()
            invoice_lookup[(definition["customer"], definition["posting_date"])] = invoice_name
            result["sales_invoices"].append(
                {
                    "label": "direct_invoice",
                    "sales_invoice": invoice_name,
                    "customer": definition["customer"],
                    "posting_date": definition["posting_date"],
                    "grand_total": definition["expected_total"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"direct_{definition['customer']}_{definition['posting_date']}",
                    "stage": "direct_invoice",
                    "error": str(exc),
                }
            )

    for customer, invoice_posting_date, payment_posting_date, amount in payment_specs:
        invoice_name = invoice_lookup.get((customer, invoice_posting_date)) or _find_submitted_sales_invoice(
            customer,
            invoice_posting_date,
        )
        if not invoice_name:
            result["failed"].append(
                {
                    "label": f"payment_{customer}_{payment_posting_date}",
                    "stage": "payment_lookup",
                    "error": "sales_invoice_missing",
                }
            )
            continue

        try:
            payment_name = _create_partial_payment_with_date_dedupe(
                "Sales Invoice",
                invoice_name,
                payment_posting_date,
                amount,
            )
            frappe.db.commit()
            result["payment_entries"].append(
                {
                    "customer": customer,
                    "sales_invoice": invoice_name,
                    "payment_entry": payment_name,
                    "amount": amount,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"payment_{customer}_{payment_posting_date}",
                    "stage": "payment",
                    "error": str(exc),
                }
            )

    return result


def apply_december_2025_mandalay_cable_negative_stock_fix() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    transfer_def = {
        "company": company,
        "posting_date": "2025-12-31",
        "posting_time": "17:35:00",
        "item_code": "ACC-CBL-UGR-TC1M",
        "qty": 15,
        "source_warehouse": "Yangon Main Warehouse - MMOB",
        "target_warehouse": "Mandalay Warehouse - MMOB",
        "remarks": "Year-end inter-warehouse balancing transfer to cover late Mandalay cable dispatches and remove negative closing stock before month close.",
    }

    try:
        stock_entry_name = _create_material_transfer(transfer_def)
        frappe.db.commit()
        return {
            "status": "ok",
            "stock_entry": stock_entry_name,
            "note": "Late-December quantity position corrected via material transfer. Residual historical valuation artifacts, if any, should be handled in a dedicated stock valuation repost/cleanup pass rather than a current-period reconciliation.",
            "item_code": transfer_def["item_code"],
            "qty": transfer_def["qty"],
            "source_warehouse": transfer_def["source_warehouse"],
            "target_warehouse": transfer_def["target_warehouse"],
        }
    except Exception as exc:
        frappe.db.rollback()
        return {
            "status": "failed",
            "error": str(exc),
            "item_code": transfer_def["item_code"],
        }


def apply_january_2026_commercial_backbone_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    warehouse = "Yangon Main Warehouse - MMOB"
    support_purchase_defs = [
        {
            "supplier": "Myanmar Tech Import Services",
            "posting_date": "2026-01-06",
            "due_date": "2026-02-05",
            "company": company,
            "items": [
                {
                    "item_code": "SPH-APP-IP14-128",
                    "qty": 8,
                    "rate": 2210000,
                    "warehouse": warehouse,
                },
                {
                    "item_code": "ACC-CHR-XMI-33W",
                    "qty": 100,
                    "rate": 20000,
                    "warehouse": warehouse,
                },
                {
                    "item_code": "ACC-AUD-XMI-BUDS4",
                    "qty": 60,
                    "rate": 42000,
                    "warehouse": warehouse,
                },
            ],
        },
        {
            "supplier": "Myanmar Tech Import Services",
            "posting_date": "2026-01-12",
            "due_date": "2026-02-11",
            "company": company,
            "items": [
                {
                    "item_code": "SPH-OPP-A58-6/128",
                    "qty": 20,
                    "rate": 760000,
                    "warehouse": warehouse,
                },
                {
                    "item_code": "SPH-APP-IP14-128",
                    "qty": 10,
                    "rate": 2210000,
                    "warehouse": warehouse,
                },
            ],
        },
        {
            "supplier": "Sunflower Accessories Co.",
            "posting_date": "2026-01-19",
            "due_date": "2026-02-18",
            "company": company,
            "items": [
                {
                    "item_code": "ACC-CHR-XMI-33W",
                    "qty": 120,
                    "rate": 20000,
                    "warehouse": warehouse,
                },
                {
                    "item_code": "ACC-AUD-XMI-BUDS4",
                    "qty": 100,
                    "rate": 42000,
                    "warehouse": warehouse,
                },
                {
                    "item_code": "GAD-SPK-JBL-GO3",
                    "qty": 50,
                    "rate": 160000,
                    "warehouse": warehouse,
                },
            ],
        },
        {
            "supplier": "Sunflower Accessories Co.",
            "posting_date": "2026-01-27",
            "due_date": "2026-02-26",
            "company": company,
            "items": [
                {
                    "item_code": "ACC-CHR-XMI-33W",
                    "qty": 60,
                    "rate": 20000,
                    "warehouse": warehouse,
                },
                {
                    "item_code": "ACC-AUD-XMI-BUDS4",
                    "qty": 40,
                    "rate": 42000,
                    "warehouse": warehouse,
                },
            ],
        },
    ]
    credit_limit_targets = {
        "35th Street Mobile Wholesale": 80000000,
        "Mandalay Accessories Wholesale": 45000000,
        "Mandalay Mobile Hub": 25000000,
        "Ko Nay Lin Mobile Center": 50000000,
        "Shwe Li Road Mobile Wholesale": 30000000,
    }

    quotation_specs = [
        {
            "label": "january_35th_wholesale_quote",
            "customer": "35th Street Mobile Wholesale",
            "transaction_date": "2026-01-07",
            "valid_till": "2026-01-12",
            "payment_terms_template": "30 Days - MMOB",
            "set_warehouse": warehouse,
            "remarks": "January Mandalay wholesale handset and accessory replenishment quotation before customer confirmation.",
            "items": [
                {"item_code": "SPH-APP-IP14-128", "qty": 4, "rate": 2650000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 10, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 20, "rate": 110000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 40, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 50, "rate": 8000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 5, "rate": 220000},
            ],
        },
        {
            "label": "january_hlaingtharyar_key_account_quote",
            "customer": "Hlaing Tharyar Mobile Corner",
            "transaction_date": "2026-01-25",
            "valid_till": "2026-01-29",
            "payment_terms_template": "30 Days - MMOB",
            "set_warehouse": warehouse,
            "remarks": "January Yangon wholesale/key-account quotation for mixed handset and accessory replenishment.",
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 4, "rate": 2150000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 6, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 20, "rate": 110000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 40, "rate": 30000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 20, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 4, "rate": 220000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
                {"item_code": "MEM-USB-SND-64", "qty": 10, "rate": 16000},
            ],
        },
        {
            "label": "january_thingangyun_bundle_quote",
            "customer": "Thingangyun Mobile House",
            "transaction_date": "2026-01-26",
            "valid_till": "2026-01-30",
            "payment_terms_template": "30 Days - MMOB",
            "set_warehouse": warehouse,
            "remarks": "January mixed handset and accessory quotation for a Yangon township replenishment lane.",
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 2, "rate": 2150000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 4, "rate": 1020000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 20, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 25, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 25, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 40, "rate": 8000},
                {"item_code": "ACC-CAS-TPU-A15", "qty": 20, "rate": 18000},
                {"item_code": "ACC-SP-GLS-A15", "qty": 20, "rate": 10000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 4, "rate": 220000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 30, "rate": 16000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 30, "rate": 14000},
            ],
        },
        {
            "label": "january_latha_lost_quote",
            "customer": "Latha Mobile Wholesale",
            "transaction_date": "2026-01-04",
            "valid_till": "2026-01-09",
            "payment_terms_template": "30 Days - MMOB",
            "set_warehouse": warehouse,
            "target_status": "Lost",
            "remarks": "January price-sensitive wholesale quotation that did not convert after follow-up on margin and competitor pricing.",
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 10, "rate": 1020000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 20, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 30, "rate": 32000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 40, "rate": 8000},
            ],
        },
        {
            "label": "january_hledan_expired_quote",
            "customer": "Hledan Phone Hub",
            "transaction_date": "2026-01-23",
            "valid_till": "2026-01-27",
            "payment_terms_template": "30 Days - MMOB",
            "set_warehouse": warehouse,
            "target_status": "Expired",
            "remarks": "January small-bundle quotation that expired after the customer delayed final confirmation.",
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
            ],
        },
    ]

    chain_specs = [
        {
            "label": "existing_bayint_wholesale_order_completion",
            "customer": "Bayint Naung Wholesale Mobile",
            "sales_order": {
                "existing_name": "SAL-ORD-2026-00003",
                "transaction_date": "2026-01-13",
                "payment_terms_template": "30 Days - MMOB",
            },
            "delivery_note": {
                "posting_date": "2026-01-14",
                "posting_time": "11:20:00",
                "remarks": "January Bayint wholesale delivery released after customer PO confirmation and stock picking.",
            },
            "sales_invoice": {
                "posting_date": "2026-01-14",
                "posting_time": "11:40:00",
                "due_date": "2026-02-13",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "January Bayint wholesale invoice issued after same-day delivery against confirmed customer PO.",
            },
        },
        {
            "label": "existing_capital_key_account_order_completion",
            "customer": "Capital Telecom (NPT)",
            "sales_order": {
                "existing_name": "SAL-ORD-2026-00006",
                "transaction_date": "2026-01-20",
                "payment_terms_template": "45 Days Approved - MMOB",
            },
            "delivery_note": {
                "posting_date": "2026-01-21",
                "posting_time": "14:10:00",
                "remarks": "January Naypyitaw key-account dispatch released after internal credit and stock confirmation.",
            },
            "sales_invoice": {
                "posting_date": "2026-01-21",
                "posting_time": "14:30:00",
                "due_date": "2026-03-06",
                "payment_terms_template": "45 Days Approved - MMOB",
                "remarks": "January Capital Telecom key-account invoice issued after formal delivery release.",
            },
        },
        {
            "label": "january_35th_quote_to_order_chain",
            "customer": "35th Street Mobile Wholesale",
            "quotation_label": "january_35th_wholesale_quote",
            "sales_order": {
                "transaction_date": "2026-01-10",
                "delivery_date": "2026-01-11",
                "po_no": "CPO-2026-01-301",
                "po_date": "2026-01-10",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "January converted wholesale order after customer approved the earlier Mandalay replenishment quotation.",
            },
            "delivery_note": {
                "posting_date": "2026-01-11",
                "posting_time": "13:30:00",
                "remarks": "January 35th Street wholesale delivery for mixed handset and accessory replenishment.",
            },
            "sales_invoice": {
                "posting_date": "2026-01-11",
                "posting_time": "13:50:00",
                "due_date": "2026-02-10",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "January 35th Street wholesale invoice converted from approved quotation and delivery.",
            },
        },
        {
            "label": "january_mandalay_accessories_wholesale_chain",
            "customer": "Mandalay Accessories Wholesale",
            "items": [
                {"item_code": "ACC-PWB-BAS-20K", "qty": 50, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 60, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 80, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 120, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 70, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 20, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 4, "rate": 220000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
            ],
            "sales_order": {
                "transaction_date": "2026-01-18",
                "delivery_date": "2026-01-19",
                "po_no": "CPO-2026-01-302",
                "po_date": "2026-01-18",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "January accessories-heavy wholesale order from an already active Mandalay trade customer.",
            },
            "delivery_note": {
                "posting_date": "2026-01-19",
                "posting_time": "12:40:00",
                "remarks": "January Mandalay accessories-heavy wholesale dispatch from Yangon central stock.",
            },
            "sales_invoice": {
                "posting_date": "2026-01-19",
                "posting_time": "13:00:00",
                "due_date": "2026-02-18",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "January Mandalay accessories-heavy wholesale billing after same-day dispatch.",
            },
        },
        {
            "label": "january_taunggyi_city_wholesale_chain",
            "customer": "Taunggyi City Mobile",
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 4, "rate": 2150000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 4, "rate": 1020000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 20, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 30, "rate": 32000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 4, "rate": 220000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
            ],
            "sales_order": {
                "transaction_date": "2026-01-22",
                "delivery_date": "2026-01-23",
                "po_no": "CPO-2026-01-303",
                "po_date": "2026-01-22",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "January Shan wholesale replenishment order placed directly by phone and confirmed by customer PO.",
            },
            "delivery_note": {
                "posting_date": "2026-01-23",
                "posting_time": "11:50:00",
                "remarks": "January Taunggyi mixed handset and accessory dispatch released from Yangon central stock.",
            },
            "sales_invoice": {
                "posting_date": "2026-01-23",
                "posting_time": "12:10:00",
                "due_date": "2026-02-22",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "January Taunggyi wholesale invoice after direct-order fulfillment and dispatch.",
            },
        },
        {
            "label": "january_ko_nay_lin_wholesale_chain",
            "customer": "Ko Nay Lin Mobile Center",
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 4, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 4, "rate": 1020000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 20, "rate": 110000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
                {"item_code": "MEM-MSD-SND-128", "qty": 10, "rate": 26000},
            ],
            "sales_order": {
                "transaction_date": "2026-01-24",
                "delivery_date": "2026-01-25",
                "po_no": "CPO-2026-01-304",
                "po_date": "2026-01-24",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "January Mandalay-lane wholesale order for mixed handset restock and fast-moving accessories.",
            },
            "delivery_note": {
                "posting_date": "2026-01-25",
                "posting_time": "15:00:00",
                "remarks": "January Ko Nay Lin wholesale dispatch for mixed handset restock after customer confirmation.",
            },
            "sales_invoice": {
                "posting_date": "2026-01-25",
                "posting_time": "15:20:00",
                "due_date": "2026-02-24",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "January Ko Nay Lin wholesale invoice issued after same-day dispatch.",
            },
        },
        {
            "label": "january_hlaingtharyar_quote_to_order_chain",
            "customer": "Hlaing Tharyar Mobile Corner",
            "quotation_label": "january_hlaingtharyar_key_account_quote",
            "sales_order": {
                "transaction_date": "2026-01-27",
                "delivery_date": "2026-01-28",
                "po_no": "CPO-2026-01-305",
                "po_date": "2026-01-27",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "January converted Hlaing Tharyar wholesale order after customer approved the negotiated mixed bundle.",
            },
            "delivery_note": {
                "posting_date": "2026-01-28",
                "posting_time": "11:10:00",
                "remarks": "January Hlaing Tharyar wholesale dispatch after negotiated mixed bundle confirmation.",
            },
            "sales_invoice": {
                "posting_date": "2026-01-28",
                "posting_time": "11:30:00",
                "due_date": "2026-02-27",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "January Hlaing Tharyar wholesale invoice converted from approved quotation and delivery.",
            },
        },
        {
            "label": "january_thingangyun_quote_to_order_chain",
            "customer": "Thingangyun Mobile House",
            "quotation_label": "january_thingangyun_bundle_quote",
            "sales_order": {
                "transaction_date": "2026-01-28",
                "delivery_date": "2026-01-29",
                "po_no": "CPO-2026-01-306",
                "po_date": "2026-01-28",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "January Yangon township wholesale order created after the customer accepted the earlier quotation.",
            },
            "delivery_note": {
                "posting_date": "2026-01-29",
                "posting_time": "14:20:00",
                "remarks": "January Thingangyun mixed-bundle dispatch after order confirmation from the approved quotation.",
            },
            "sales_invoice": {
                "posting_date": "2026-01-29",
                "posting_time": "14:40:00",
                "due_date": "2026-02-28",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "January Thingangyun wholesale invoice converted from approved quotation and delivery.",
            },
        },
    ]

    direct_sales_defs = [
        {
            "customer": "Latha Mobile Wholesale",
            "posting_date": "2026-01-05",
            "due_date": "2026-02-15",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 3, "rate": 1020000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 3, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 15, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 2, "rate": 220000},
            ],
        },
        {
            "customer": "Lanmadaw Telecom & Gadgets",
            "posting_date": "2026-01-07",
            "due_date": "2026-01-20",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 15, "rate": 110000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 30, "rate": 30000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 30, "rate": 16000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
            ],
        },
        {
            "customer": "Mayangone Mobile House",
            "posting_date": "2026-01-15",
            "due_date": "2026-02-14",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 2, "rate": 2150000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 2, "rate": 220000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
            ],
        },
        {
            "customer": "Pazundaung Phone House",
            "posting_date": "2026-01-18",
            "due_date": "2026-01-25",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 3, "rate": 1020000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 15, "rate": 32000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
            ],
        },
        {
            "customer": "Hledan Mobile Trade Center",
            "posting_date": "2026-01-20",
            "due_date": "2026-01-31",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 10, "rate": 220000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 15, "rate": 58000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
            ],
        },
        {
            "customer": "Mandalay Mobile Hub",
            "posting_date": "2026-01-22",
            "due_date": "2026-02-26",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-APP-IP14-128", "qty": 2, "rate": 2650000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 1020000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
            ],
        },
        {
            "customer": "Shwe Li Road Mobile Wholesale",
            "posting_date": "2026-01-26",
            "due_date": "2026-02-28",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 3, "rate": 2150000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 3, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 15, "rate": 110000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 30, "rate": 30000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 3, "rate": 220000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
            ],
        },
        {
            "customer": "City Mobile Mart",
            "posting_date": "2026-01-27",
            "due_date": "2026-01-27",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 1, "rate": 1020000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 10, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 30000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
            ],
        },
        {
            "customer": "Taunggyi Star Mobile",
            "posting_date": "2026-01-28",
            "due_date": "2026-02-28",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 2, "rate": 2150000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 1020000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 3, "rate": 220000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
            ],
        },
        {
            "customer": "Hledan Phone Hub",
            "posting_date": "2026-01-30",
            "due_date": "2026-02-05",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 3, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 15, "rate": 110000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 4, "rate": 220000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 10, "rate": 16000},
            ],
        },
    ]

    payment_specs = [
        ("Bayint Naung Wholesale Mobile", "2026-01-14", "2026-01-17", 4000000),
        ("Capital Telecom (NPT)", "2026-01-21", "2026-01-27", 3000000),
        ("35th Street Mobile Wholesale", "2026-01-11", "2026-01-15", 5000000),
        ("Latha Mobile Wholesale", "2026-01-05", "2026-01-20", 2000000),
        ("Mandalay Mobile Hub", "2026-01-22", "2026-01-30", 3000000),
        ("Shwe Li Road Mobile Wholesale", "2026-01-26", "2026-01-31", 4000000),
        ("Taunggyi Star Mobile", "2026-01-28", "2026-01-31", 2000000),
        ("Hledan Phone Hub", "2026-01-30", "2026-01-31", 2000000),
        ("Mayangone Mobile House", "2026-01-15", "2026-01-29", 2000000),
        ("Ko Nay Lin Mobile Center", "2026-01-25", "2026-01-30", 1500000),
    ]

    quotation_lookup: dict[str, str] = {}
    quotation_spec_lookup = {spec["label"]: spec for spec in quotation_specs}
    invoice_lookup: dict[tuple[str, str], str] = {}
    result = {
        "purchase_invoices": [],
        "credit_limits": [],
        "quotations": [],
        "sales_orders": [],
        "delivery_notes": [],
        "sales_invoices": [],
        "payment_entries": [],
        "failed": [],
    }

    for supplier_def in support_purchase_defs:
        try:
            supplier_def["expected_total"] = _sum_item_amounts(supplier_def["items"])
            purchase_invoice_name = _create_purchase_invoice(supplier_def)
            frappe.db.commit()
            result["purchase_invoices"].append(
                {
                    "supplier": supplier_def["supplier"],
                    "purchase_invoice": purchase_invoice_name,
                    "posting_date": supplier_def["posting_date"],
                    "grand_total": supplier_def["expected_total"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"support_purchase_{supplier_def['supplier']}_{supplier_def['posting_date']}",
                    "stage": "support_purchase",
                    "error": str(exc),
                }
            )

    for customer_name, credit_limit in credit_limit_targets.items():
        try:
            customer = frappe.get_doc("Customer", customer_name)
            limit_row = None
            for row in customer.credit_limits:
                if row.company == company:
                    limit_row = row
                    break
            if limit_row:
                limit_row.credit_limit = credit_limit
                limit_row.bypass_credit_limit_check = 0
            else:
                customer.append(
                    "credit_limits",
                    {
                        "company": company,
                        "credit_limit": credit_limit,
                        "bypass_credit_limit_check": 0,
                    },
                )
            customer.save(ignore_permissions=True)
            frappe.db.commit()
            result["credit_limits"].append({"customer": customer_name, "credit_limit": credit_limit})
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"credit_limit_{customer_name}",
                    "stage": "credit_limit",
                    "error": str(exc),
                }
            )

    for spec in quotation_specs:
        try:
            spec["company"] = company
            spec["expected_total"] = _sum_item_amounts(spec["items"])
            quotation_name = _create_quotation(spec)
            quotation_lookup[spec["label"]] = quotation_name
            if spec.get("target_status") == "Lost":
                frappe.db.set_value(
                    "Quotation",
                    quotation_name,
                    {
                        "status": "Lost",
                        "order_lost_reason": "January commercial follow-up ended without confirmation after price comparison and customer review.",
                    },
                    update_modified=False,
                )
            elif spec.get("target_status") == "Expired":
                frappe.db.set_value(
                    "Quotation",
                    quotation_name,
                    {
                        "status": "Expired",
                        "order_lost_reason": None,
                    },
                    update_modified=False,
                )
            frappe.db.commit()
            result["quotations"].append(
                {
                    "label": spec["label"],
                    "quotation": quotation_name,
                    "customer": spec["customer"],
                    "grand_total": spec["expected_total"],
                    "target_status": spec.get("target_status") or "Submitted",
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "stage": "quotation", "error": str(exc)})

    for spec in chain_specs:
        try:
            chain_items = spec.get("items")
            if spec["sales_order"].get("existing_name"):
                existing_name = spec["sales_order"]["existing_name"]
                expected_total = int(
                    round(frappe.db.get_value("Sales Order", existing_name, "grand_total") or 0)
                )
            elif spec.get("quotation_label"):
                expected_total = _sum_item_amounts(
                    quotation_spec_lookup[spec["quotation_label"]]["items"]
                )
            else:
                expected_total = _sum_item_amounts(chain_items or [])
            order_name: str
            if spec["sales_order"].get("existing_name"):
                order_name = spec["sales_order"]["existing_name"]
            elif spec.get("quotation_label"):
                order_payload = dict(spec["sales_order"])
                order_payload["customer"] = spec["customer"]
                order_payload["company"] = company
                order_payload["items"] = list(
                    quotation_spec_lookup[spec["quotation_label"]]["items"]
                )
                order_payload["expected_total"] = expected_total
                order_name = _create_sales_order(order_payload)
                frappe.db.set_value(
                    "Quotation",
                    quotation_lookup[spec["quotation_label"]],
                    {
                        "status": "Ordered",
                    },
                    update_modified=False,
                )
            else:
                order_payload = dict(spec["sales_order"])
                order_payload["customer"] = spec["customer"]
                order_payload["company"] = company
                order_payload["items"] = list(chain_items or [])
                order_payload["expected_total"] = expected_total
                order_name = _create_sales_order(order_payload)

            delivery_note_name = _create_delivery_note_from_sales_order(
                order_name,
                spec["delivery_note"],
            )
            invoice_name = _create_sales_invoice_from_delivery_note(
                delivery_note_name,
                spec["sales_invoice"],
            )
            frappe.db.commit()

            invoice_lookup[(spec["customer"], spec["sales_invoice"]["posting_date"])] = invoice_name
            result["sales_orders"].append(
                {
                    "label": spec["label"],
                    "sales_order": order_name,
                    "customer": spec["customer"],
                    "grand_total": expected_total,
                }
            )
            result["delivery_notes"].append(
                {
                    "label": spec["label"],
                    "delivery_note": delivery_note_name,
                    "sales_order": order_name,
                }
            )
            result["sales_invoices"].append(
                {
                    "label": spec["label"],
                    "sales_invoice": invoice_name,
                    "customer": spec["customer"],
                    "posting_date": spec["sales_invoice"]["posting_date"],
                    "grand_total": expected_total,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "stage": "chain", "error": str(exc)})

    for definition in direct_sales_defs:
        try:
            definition["expected_total"] = _sum_item_amounts(definition["items"])
            invoice_name = _create_sales_invoice(definition)
            frappe.db.commit()
            invoice_lookup[(definition["customer"], definition["posting_date"])] = invoice_name
            result["sales_invoices"].append(
                {
                    "label": "direct_invoice",
                    "sales_invoice": invoice_name,
                    "customer": definition["customer"],
                    "posting_date": definition["posting_date"],
                    "grand_total": definition["expected_total"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"direct_{definition['customer']}_{definition['posting_date']}",
                    "stage": "direct_invoice",
                    "error": str(exc),
                }
            )

    for customer, invoice_posting_date, payment_posting_date, amount in payment_specs:
        invoice_name = invoice_lookup.get((customer, invoice_posting_date)) or _find_submitted_sales_invoice(
            customer,
            invoice_posting_date,
        )
        if not invoice_name:
            result["failed"].append(
                {
                    "label": f"payment_{customer}_{payment_posting_date}",
                    "stage": "payment_lookup",
                    "error": "sales_invoice_missing",
                }
            )
            continue

        try:
            payment_name = _create_partial_payment(
                "Sales Invoice",
                invoice_name,
                payment_posting_date,
                amount,
            )
            frappe.db.commit()
            result["payment_entries"].append(
                {
                    "customer": customer,
                    "sales_invoice": invoice_name,
                    "payment_entry": payment_name,
                    "amount": amount,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"payment_{customer}_{payment_posting_date}",
                    "stage": "payment",
                    "error": str(exc),
                }
            )

    return result


def apply_february_2026_normalization_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    warehouse = "Yangon Main Warehouse - MMOB"
    support_purchase_defs = [
        {
            "supplier": "Myanmar Tech Import Services",
            "posting_date": "2026-02-05",
            "due_date": "2026-03-07",
            "company": company,
            "items": [
                {
                    "item_code": "SPH-APP-IP13-128",
                    "qty": 4,
                    "rate": 1900000,
                    "warehouse": warehouse,
                },
                {
                    "item_code": "SPH-XMI-RN13-8/256",
                    "qty": 10,
                    "rate": 820000,
                    "warehouse": warehouse,
                },
                {
                    "item_code": "SPH-SAM-A15-6/128",
                    "qty": 12,
                    "rate": 760000,
                    "warehouse": warehouse,
                },
                {
                    "item_code": "ACC-CHR-XMI-33W",
                    "qty": 80,
                    "rate": 22000,
                    "warehouse": warehouse,
                },
                {
                    "item_code": "ACC-AUD-XMI-BUDS4",
                    "qty": 40,
                    "rate": 42000,
                    "warehouse": warehouse,
                },
            ],
        },
        {
            "supplier": "Sunflower Accessories Co.",
            "posting_date": "2026-02-14",
            "due_date": "2026-03-16",
            "company": company,
            "items": [
                {
                    "item_code": "ACC-PWB-BAS-20K",
                    "qty": 60,
                    "rate": 78000,
                    "warehouse": warehouse,
                },
                {
                    "item_code": "GAD-SPK-JBL-GO3",
                    "qty": 30,
                    "rate": 160000,
                    "warehouse": warehouse,
                },
                {
                    "item_code": "GAD-WCH-XMI-MB8",
                    "qty": 20,
                    "rate": 150000,
                    "warehouse": warehouse,
                },
                {
                    "item_code": "MEM-USB-SND-64",
                    "qty": 40,
                    "rate": 8000,
                    "warehouse": warehouse,
                },
                {
                    "item_code": "MEM-MSD-SND-128",
                    "qty": 50,
                    "rate": 13000,
                    "warehouse": warehouse,
                },
                {
                    "item_code": "ACC-CHR-XMI-33W",
                    "qty": 30,
                    "rate": 22000,
                    "warehouse": warehouse,
                },
            ],
        },
        {
            "supplier": "Sunflower Accessories Co.",
            "posting_date": "2026-02-15",
            "due_date": "2026-03-17",
            "company": company,
            "items": [
                {
                    "item_code": "ACC-PWB-BAS-20K",
                    "qty": 10,
                    "rate": 78000,
                    "warehouse": warehouse,
                },
            ],
        },
        {
            "supplier": "Sunflower Accessories Co.",
            "posting_date": "2026-02-16",
            "due_date": "2026-03-18",
            "company": company,
            "items": [
                {
                    "item_code": "ACC-CBL-BAS-TC1M",
                    "qty": 50,
                    "rate": 4000,
                    "warehouse": warehouse,
                },
            ],
        },
        {
            "supplier": "Sunflower Accessories Co.",
            "posting_date": "2026-02-17",
            "due_date": "2026-03-19",
            "company": company,
            "items": [
                {
                    "item_code": "ACC-PWB-BAS-20K",
                    "qty": 30,
                    "rate": 78000,
                    "warehouse": warehouse,
                },
                {
                    "item_code": "ACC-CBL-UGR-TC1M",
                    "qty": 20,
                    "rate": 9000,
                    "warehouse": warehouse,
                },
            ],
        },
        {
            "supplier": "Sunflower Accessories Co.",
            "posting_date": "2026-02-18",
            "due_date": "2026-03-20",
            "company": company,
            "items": [
                {
                    "item_code": "ACC-PWB-BAS-20K",
                    "qty": 50,
                    "rate": 78000,
                    "warehouse": warehouse,
                },
                {
                    "item_code": "ACC-CBL-UGR-TC1M",
                    "qty": 60,
                    "rate": 9000,
                    "warehouse": warehouse,
                },
                {
                    "item_code": "ACC-CHR-XMI-33W",
                    "qty": 40,
                    "rate": 22000,
                    "warehouse": warehouse,
                },
                {
                    "item_code": "ACC-AUD-XMI-BUDS4",
                    "qty": 20,
                    "rate": 42000,
                    "warehouse": warehouse,
                },
            ],
        },
        {
            "supplier": "Sunflower Accessories Co.",
            "posting_date": "2026-02-20",
            "due_date": "2026-03-22",
            "company": company,
            "items": [
                {
                    "item_code": "ACC-PWB-BAS-20K",
                    "qty": 20,
                    "rate": 78000,
                    "warehouse": warehouse,
                },
                {
                    "item_code": "GAD-SPK-JBL-GO3",
                    "qty": 20,
                    "rate": 160000,
                    "warehouse": warehouse,
                },
            ],
        },
        {
            "supplier": "Sunflower Accessories Co.",
            "posting_date": "2026-02-22",
            "due_date": "2026-03-24",
            "company": company,
            "items": [
                {
                    "item_code": "ACC-CBL-UGR-TC1M",
                    "qty": 20,
                    "rate": 9000,
                    "warehouse": warehouse,
                },
            ],
        },
    ]
    credit_limit_targets = {
        "Bayint Naung Wholesale Mobile": 140000000,
        "Capital Telecom (NPT)": 120000000,
        "35th Street Mobile Wholesale": 100000000,
        "Ko Nay Lin Mobile Center": 65000000,
        "Mandalay Accessories Wholesale": 65000000,
        "Mandalay Mobile Hub": 45000000,
        "Shwe Li Road Mobile Wholesale": 40000000,
        "Hledan Mobile Trade Center": 15000000,
        "Latha Mobile Wholesale": 65000000,
    }

    quotation_specs = [
        {
            "label": "february_capital_key_account_quote",
            "customer": "Capital Telecom (NPT)",
            "transaction_date": "2026-02-09",
            "valid_till": "2026-02-12",
            "payment_terms_template": "45 Days Approved - MMOB",
            "set_warehouse": warehouse,
            "remarks": "February key-account mixed-device quotation for normal replenishment after January strong sell-through.",
            "items": [
                {"item_code": "SPH-APP-IP13-128", "qty": 2, "rate": 2050000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 4, "rate": 1000000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 6, "rate": 900000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 10, "rate": 220000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 20, "rate": 58000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 4, "rate": 195000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
            ],
        },
        {
            "label": "february_bayint_wholesale_quote",
            "customer": "Bayint Naung Wholesale Mobile",
            "transaction_date": "2026-02-11",
            "valid_till": "2026-02-14",
            "payment_terms_template": "30 Days - MMOB",
            "set_warehouse": warehouse,
            "remarks": "February Yangon wholesale replenishment quotation focused on ordinary handset and accessory repeat buying.",
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 6, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 20, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 40, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 40, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 60, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 20, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 8, "rate": 220000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
            ],
        },
        {
            "label": "february_hledan_lost_quote",
            "customer": "Hledan Mobile Trade Center",
            "transaction_date": "2026-02-07",
            "valid_till": "2026-02-10",
            "payment_terms_template": "7 Days - MMOB",
            "set_warehouse": warehouse,
            "target_status": "Lost",
            "remarks": "February wholesale inquiry that did not convert after margin review and competing offer pressure.",
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 4, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 4, "rate": 195000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
            ],
        },
        {
            "label": "february_hlaingtharyar_expired_quote",
            "customer": "Hlaing Tharyar Mobile Corner",
            "transaction_date": "2026-02-20",
            "valid_till": "2026-02-24",
            "payment_terms_template": "Immediate / Counter Cash - MMOB",
            "set_warehouse": warehouse,
            "target_status": "Expired",
            "remarks": "February negotiated township bundle that expired after the customer delayed confirmation.",
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 30, "rate": 8000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 2, "rate": 220000},
            ],
        },
    ]

    chain_specs = [
        {
            "label": "february_capital_quote_to_order_chain",
            "customer": "Capital Telecom (NPT)",
            "quotation_label": "february_capital_key_account_quote",
            "sales_order": {
                "transaction_date": "2026-02-11",
                "delivery_date": "2026-02-12",
                "po_no": "CPO-2026-02-401",
                "po_date": "2026-02-11",
                "payment_terms_template": "45 Days Approved - MMOB",
                "set_warehouse": warehouse,
                "remarks": "February converted key-account order after quotation confirmation and internal approval.",
            },
            "delivery_note": {
                "posting_date": "2026-02-12",
                "posting_time": "11:20:00",
                "remarks": "February Capital Telecom dispatch after negotiated replenishment approval.",
            },
            "sales_invoice": {
                "posting_date": "2026-02-12",
                "posting_time": "11:40:00",
                "due_date": "2026-03-29",
                "payment_terms_template": "45 Days Approved - MMOB",
                "remarks": "February Capital Telecom invoice converted from approved quotation and dispatch.",
            },
        },
        {
            "label": "february_bayint_quote_to_order_chain",
            "customer": "Bayint Naung Wholesale Mobile",
            "quotation_label": "february_bayint_wholesale_quote",
            "sales_order": {
                "transaction_date": "2026-02-12",
                "delivery_date": "2026-02-13",
                "po_no": "CPO-2026-02-402",
                "po_date": "2026-02-12",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "February Bayint wholesale order converted from repeat-customer quotation.",
            },
            "delivery_note": {
                "posting_date": "2026-02-13",
                "posting_time": "13:10:00",
                "remarks": "February Bayint wholesale dispatch for ordinary handset and accessory restock.",
            },
            "sales_invoice": {
                "posting_date": "2026-02-13",
                "posting_time": "13:30:00",
                "due_date": "2026-03-15",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "February Bayint wholesale invoice converted from quotation-driven dispatch.",
            },
        },
        {
            "label": "february_ko_nay_lin_chain",
            "customer": "Ko Nay Lin Mobile Center",
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 4, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 4, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 15, "rate": 110000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 40, "rate": 8000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 4, "rate": 220000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 15, "rate": 26000},
            ],
            "sales_order": {
                "transaction_date": "2026-02-18",
                "delivery_date": "2026-02-19",
                "po_no": "CPO-2026-02-403",
                "po_date": "2026-02-18",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "February Mandalay-lane wholesale replenishment order under normal trading rhythm.",
            },
            "delivery_note": {
                "posting_date": "2026-02-19",
                "posting_time": "10:50:00",
                "remarks": "February Ko Nay Lin dispatch after confirmed mixed handset and accessory order.",
            },
            "sales_invoice": {
                "posting_date": "2026-02-19",
                "posting_time": "11:10:00",
                "due_date": "2026-03-21",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "February Ko Nay Lin invoice after direct-order dispatch.",
            },
        },
        {
            "label": "february_mandalay_accessories_chain",
            "customer": "Mandalay Accessories Wholesale",
            "items": [
                {"item_code": "ACC-PWB-BAS-20K", "qty": 35, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 50, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 60, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 120, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 65, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 20, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 6, "rate": 220000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 2, "rate": 195000},
            ],
            "sales_order": {
                "transaction_date": "2026-02-16",
                "delivery_date": "2026-02-17",
                "po_no": "CPO-2026-02-404",
                "po_date": "2026-02-16",
                "payment_terms_template": "15 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "February accessories-led Mandalay wholesale order after January strong turnover.",
            },
            "delivery_note": {
                "posting_date": "2026-02-17",
                "posting_time": "12:20:00",
                "remarks": "February Mandalay accessories dispatch from Yangon main stock.",
            },
            "sales_invoice": {
                "posting_date": "2026-02-17",
                "posting_time": "12:40:00",
                "due_date": "2026-03-04",
                "payment_terms_template": "15 Days - MMOB",
                "remarks": "February Mandalay accessories invoice after ordinary replenishment dispatch.",
            },
        },
        {
            "label": "february_shwe_li_chain",
            "customer": "Shwe Li Road Mobile Wholesale",
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 6, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 15, "rate": 110000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 8, "rate": 220000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "MEM-USB-SND-64", "qty": 10, "rate": 16000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
                {"item_code": "MEM-MSD-SND-128", "qty": 10, "rate": 26000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
            ],
            "sales_order": {
                "transaction_date": "2026-02-20",
                "delivery_date": "2026-02-21",
                "po_no": "CPO-2026-02-405",
                "po_date": "2026-02-20",
                "payment_terms_template": "15 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "February Yangon wholesale restock order with a slightly smaller handset mix than January.",
            },
            "delivery_note": {
                "posting_date": "2026-02-21",
                "posting_time": "14:00:00",
                "remarks": "February Shwe Li Road dispatch under ordinary mid-month replenishment rhythm.",
            },
            "sales_invoice": {
                "posting_date": "2026-02-21",
                "posting_time": "14:20:00",
                "due_date": "2026-03-08",
                "payment_terms_template": "15 Days - MMOB",
                "remarks": "February Shwe Li Road wholesale invoice after confirmed dispatch.",
            },
        },
        {
            "label": "february_taunggyi_city_chain",
            "customer": "Taunggyi City Mobile",
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 4, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 4, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 4, "rate": 220000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 15, "rate": 26000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 30, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 25, "rate": 14000},
            ],
            "sales_order": {
                "transaction_date": "2026-02-22",
                "delivery_date": "2026-02-23",
                "po_no": "CPO-2026-02-406",
                "po_date": "2026-02-22",
                "payment_terms_template": "Cash on Delivery - MMOB",
                "set_warehouse": warehouse,
                "remarks": "February Taunggyi order showing normal retail-wholesale crossover buying before month-end.",
            },
            "delivery_note": {
                "posting_date": "2026-02-23",
                "posting_time": "11:30:00",
                "remarks": "February Taunggyi dispatch for mixed handset and accessory restock.",
            },
            "sales_invoice": {
                "posting_date": "2026-02-23",
                "posting_time": "11:50:00",
                "due_date": "2026-02-23",
                "payment_terms_template": "Cash on Delivery - MMOB",
                "remarks": "February Taunggyi invoice after COD dispatch completion.",
            },
        },
    ]

    direct_sales_defs = [
        {
            "customer": "35th Street Mobile Wholesale",
            "posting_date": "2026-02-19",
            "due_date": "2026-03-21",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 5, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 1000000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 10, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 10, "rate": 195000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 20, "rate": 58000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 40, "rate": 8000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 15, "rate": 110000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
            ],
        },
        {
            "customer": "Latha Mobile Wholesale",
            "posting_date": "2026-02-10",
            "due_date": "2026-03-12",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 4, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 40, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 4, "rate": 220000},
                {"item_code": "MEM-USB-SND-64", "qty": 10, "rate": 16000},
            ],
        },
        {
            "customer": "Lanmadaw Telecom & Gadgets",
            "posting_date": "2026-02-08",
            "due_date": "2026-02-15",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 15, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 4, "rate": 220000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 15, "rate": 26000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 30, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
            ],
        },
        {
            "customer": "Pazundaung Phone House",
            "posting_date": "2026-02-16",
            "due_date": "2026-02-20",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 3, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 8, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 15, "rate": 32000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "MEM-MSD-SND-128", "qty": 15, "rate": 26000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 30, "rate": 8000},
            ],
        },
        {
            "customer": "Mayangone Mobile House",
            "posting_date": "2026-02-24",
            "due_date": "2026-02-28",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 1000000},
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 15, "rate": 32000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 3, "rate": 220000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 5, "rate": 58000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 15, "rate": 14000},
                {"item_code": "MEM-USB-SND-64", "qty": 15, "rate": 16000},
            ],
        },
        {
            "customer": "City Mobile Mart",
            "posting_date": "2026-02-20",
            "due_date": "2026-02-20",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 1, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 8, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 10, "rate": 32000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 5, "rate": 58000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 15, "rate": 26000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 2, "rate": 220000},
            ],
        },
        {
            "customer": "Hledan Phone Hub",
            "posting_date": "2026-02-21",
            "due_date": "2026-02-25",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 900000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 15, "rate": 30000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 3, "rate": 220000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
            ],
        },
        {
            "customer": "Taunggyi Star Mobile",
            "posting_date": "2026-02-25",
            "due_date": "2026-02-25",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 3, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 4, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 4, "rate": 195000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 5, "rate": 58000},
                {"item_code": "MEM-USB-SND-64", "qty": 10, "rate": 16000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 30, "rate": 8000},
            ],
        },
        {
            "customer": "Sanchaung Mobile Plaza",
            "posting_date": "2026-02-28",
            "due_date": "2026-02-28",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "ACC-PWB-BAS-20K", "qty": 5, "rate": 110000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 30000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 5, "rate": 58000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 1, "rate": 220000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 5, "rate": 14000},
            ],
        },
        {
            "customer": "Capital Telecom (NPT)",
            "posting_date": "2026-02-26",
            "due_date": "2026-04-12",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 5, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 1000000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 10, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 6, "rate": 195000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 20, "rate": 58000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 25, "rate": 14000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 4, "rate": 110000},
            ],
        },
        {
            "customer": "Bayint Naung Wholesale Mobile",
            "posting_date": "2026-02-26",
            "due_date": "2026-03-28",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-SAM-A15-6/128", "qty": 4, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 40, "rate": 8000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 4, "rate": 220000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 5, "rate": 195000},
            ],
        },
        {
            "customer": "Mandalay Mobile Hub",
            "posting_date": "2026-02-25",
            "due_date": "2026-03-12",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 3, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 4, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 6, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 8, "rate": 195000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "MEM-USB-SND-64", "qty": 10, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 10, "rate": 26000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 10, "rate": 14000},
            ],
        },
    ]

    payment_specs = [
        ("Capital Telecom (NPT)", "2026-02-12", "2026-02-26", 3000000),
        ("Bayint Naung Wholesale Mobile", "2026-02-13", "2026-02-27", 2500000),
        ("Ko Nay Lin Mobile Center", "2026-02-19", "2026-02-28", 2000000),
        ("Mandalay Accessories Wholesale", "2026-02-17", "2026-02-28", 2000000),
        ("35th Street Mobile Wholesale", "2026-02-19", "2026-02-27", 3500000),
        ("City Mobile Mart", "2026-02-20", "2026-02-20", 3800000),
        ("Shwe Li Road Mobile Wholesale", "2026-02-21", "2026-02-28", 3000000),
        ("Mayangone Mobile House", "2026-02-24", "2026-02-28", 2000000),
        ("Taunggyi Star Mobile", "2026-02-25", "2026-02-25", 2000000),
        ("Mandalay Mobile Hub", "2026-02-25", "2026-02-28", 2000000),
        ("Capital Telecom (NPT)", "2026-02-26", "2026-02-28", 2000000),
        ("Bayint Naung Wholesale Mobile", "2026-02-26", "2026-02-28", 1500000),
        ("Sanchaung Mobile Plaza", "2026-02-28", "2026-02-28", 2430000),
    ]
    settlement_followup_specs = [
        ("Capital Telecom (NPT)", "2026-01-21", "2026-02-18", 4000000),
        ("35th Street Mobile Wholesale", "2026-01-11", "2026-02-22", 4500000),
        ("Taunggyi City Mobile", "2026-01-23", "2026-02-26", 3000000),
        ("Mandalay Accessories Wholesale", "2026-01-19", "2026-02-27", 2500000),
    ]
    supplier_payment_specs = [
        ("Myanmar Tech Import Services", "2026-01-10", "2026-02-24", 5000000),
        ("Sunflower Accessories Co.", "2026-01-13", "2026-02-26", 3500000),
        ("Golden Dragon Trading Co. Ltd.", "2026-01-29", "2026-02-27", 4000000),
    ]

    quotation_lookup: dict[str, str] = {}
    quotation_spec_lookup = {spec["label"]: spec for spec in quotation_specs}
    invoice_lookup: dict[tuple[str, str], str] = {}
    result = {
        "purchase_invoices": [],
        "credit_limits": [],
        "quotations": [],
        "sales_orders": [],
        "delivery_notes": [],
        "sales_invoices": [],
        "payment_entries": [],
        "supplier_payment_entries": [],
        "failed": [],
    }

    for supplier_def in support_purchase_defs:
        try:
            supplier_def["expected_total"] = _sum_item_amounts(supplier_def["items"])
            purchase_invoice_name = _create_purchase_invoice(supplier_def)
            frappe.db.commit()
            result["purchase_invoices"].append(
                {
                    "supplier": supplier_def["supplier"],
                    "purchase_invoice": purchase_invoice_name,
                    "posting_date": supplier_def["posting_date"],
                    "grand_total": supplier_def["expected_total"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"support_purchase_{supplier_def['supplier']}_{supplier_def['posting_date']}",
                    "stage": "support_purchase",
                    "error": str(exc),
                }
            )

    for customer_name, credit_limit in credit_limit_targets.items():
        try:
            customer = frappe.get_doc("Customer", customer_name)
            limit_row = None
            for row in customer.credit_limits:
                if row.company == company:
                    limit_row = row
                    break
            if limit_row:
                limit_row.credit_limit = credit_limit
                limit_row.bypass_credit_limit_check = 0
            else:
                customer.append(
                    "credit_limits",
                    {
                        "company": company,
                        "credit_limit": credit_limit,
                        "bypass_credit_limit_check": 0,
                    },
                )
            customer.save(ignore_permissions=True)
            frappe.db.commit()
            result["credit_limits"].append({"customer": customer_name, "credit_limit": credit_limit})
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"credit_limit_{customer_name}",
                    "stage": "credit_limit",
                    "error": str(exc),
                }
            )

    for spec in quotation_specs:
        try:
            spec["company"] = company
            spec["expected_total"] = _sum_item_amounts(spec["items"])
            quotation_name = _create_quotation(spec)
            quotation_lookup[spec["label"]] = quotation_name
            if spec.get("target_status") == "Lost":
                frappe.db.set_value(
                    "Quotation",
                    quotation_name,
                    {
                        "status": "Lost",
                        "order_lost_reason": "February follow-up ended without confirmation after pricing comparison and delayed customer response.",
                    },
                    update_modified=False,
                )
            elif spec.get("target_status") == "Expired":
                frappe.db.set_value(
                    "Quotation",
                    quotation_name,
                    {
                        "status": "Expired",
                        "order_lost_reason": None,
                    },
                    update_modified=False,
                )
            frappe.db.commit()
            result["quotations"].append(
                {
                    "label": spec["label"],
                    "quotation": quotation_name,
                    "customer": spec["customer"],
                    "grand_total": spec["expected_total"],
                    "target_status": spec.get("target_status") or "Submitted",
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "stage": "quotation", "error": str(exc)})

    for spec in chain_specs:
        try:
            chain_items = spec.get("items")
            if spec.get("quotation_label"):
                expected_total = _sum_item_amounts(
                    quotation_spec_lookup[spec["quotation_label"]]["items"]
                )
            else:
                expected_total = _sum_item_amounts(chain_items or [])
            order_payload = dict(spec["sales_order"])
            order_payload["customer"] = spec["customer"]
            order_payload["company"] = company
            order_payload["items"] = list(
                quotation_spec_lookup[spec["quotation_label"]]["items"]
                if spec.get("quotation_label")
                else (chain_items or [])
            )
            order_payload["expected_total"] = expected_total
            order_name = _create_sales_order(order_payload)
            if spec.get("quotation_label"):
                frappe.db.set_value(
                    "Quotation",
                    quotation_lookup[spec["quotation_label"]],
                    {"status": "Ordered"},
                    update_modified=False,
                )

            delivery_note_name = _create_delivery_note_from_sales_order(
                order_name,
                spec["delivery_note"],
            )
            invoice_name = _create_sales_invoice_from_delivery_note(
                delivery_note_name,
                spec["sales_invoice"],
            )
            frappe.db.commit()

            invoice_lookup[(spec["customer"], spec["sales_invoice"]["posting_date"])] = invoice_name
            result["sales_orders"].append(
                {
                    "label": spec["label"],
                    "sales_order": order_name,
                    "customer": spec["customer"],
                    "grand_total": expected_total,
                }
            )
            result["delivery_notes"].append(
                {
                    "label": spec["label"],
                    "delivery_note": delivery_note_name,
                    "sales_order": order_name,
                }
            )
            result["sales_invoices"].append(
                {
                    "label": spec["label"],
                    "sales_invoice": invoice_name,
                    "customer": spec["customer"],
                    "posting_date": spec["sales_invoice"]["posting_date"],
                    "grand_total": expected_total,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "stage": "chain", "error": str(exc)})

    for definition in direct_sales_defs:
        try:
            definition["expected_total"] = _sum_item_amounts(definition["items"])
            invoice_name = _create_sales_invoice(definition)
            frappe.db.commit()
            invoice_lookup[(definition["customer"], definition["posting_date"])] = invoice_name
            result["sales_invoices"].append(
                {
                    "label": "direct_invoice",
                    "sales_invoice": invoice_name,
                    "customer": definition["customer"],
                    "posting_date": definition["posting_date"],
                    "grand_total": definition["expected_total"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"direct_{definition['customer']}_{definition['posting_date']}",
                    "stage": "direct_invoice",
                    "error": str(exc),
                }
            )

    for customer, invoice_posting_date, payment_posting_date, amount in payment_specs:
        invoice_name = invoice_lookup.get((customer, invoice_posting_date)) or _find_submitted_sales_invoice(
            customer,
            invoice_posting_date,
        )
        if not invoice_name:
            result["failed"].append(
                {
                    "label": f"payment_{customer}_{payment_posting_date}",
                    "stage": "payment_lookup",
                    "error": "sales_invoice_missing",
                }
            )
            continue

        try:
            payment_name = _create_partial_payment(
                "Sales Invoice",
                invoice_name,
                payment_posting_date,
                amount,
            )
            frappe.db.commit()
            result["payment_entries"].append(
                {
                    "customer": customer,
                    "sales_invoice": invoice_name,
                    "payment_entry": payment_name,
                    "amount": amount,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"payment_{customer}_{payment_posting_date}",
                    "stage": "payment",
                    "error": str(exc),
                }
            )

    for customer, invoice_posting_date, payment_posting_date, amount in settlement_followup_specs:
        invoice_name = _find_submitted_sales_invoice(customer, invoice_posting_date)
        if not invoice_name:
            result["failed"].append(
                {
                    "label": f"settlement_followup_{customer}_{payment_posting_date}",
                    "stage": "payment_lookup",
                    "error": "sales_invoice_missing",
                }
            )
            continue

        try:
            payment_name = _create_partial_payment(
                "Sales Invoice",
                invoice_name,
                payment_posting_date,
                amount,
            )
            frappe.db.commit()
            result["payment_entries"].append(
                {
                    "customer": customer,
                    "sales_invoice": invoice_name,
                    "payment_entry": payment_name,
                    "amount": amount,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"settlement_followup_{customer}_{payment_posting_date}",
                    "stage": "payment",
                    "error": str(exc),
                }
            )

    for supplier, invoice_posting_date, payment_posting_date, amount in supplier_payment_specs:
        invoice_name = _find_submitted_purchase_invoice(supplier, invoice_posting_date)
        if not invoice_name:
            result["failed"].append(
                {
                    "label": f"supplier_payment_{supplier}_{payment_posting_date}",
                    "stage": "supplier_payment_lookup",
                    "error": "purchase_invoice_missing",
                }
            )
            continue

        try:
            payment_name = _create_partial_payment(
                "Purchase Invoice",
                invoice_name,
                payment_posting_date,
                amount,
            )
            frappe.db.commit()
            result["supplier_payment_entries"].append(
                {
                    "supplier": supplier,
                    "purchase_invoice": invoice_name,
                    "payment_entry": payment_name,
                    "amount": amount,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"supplier_payment_{supplier}_{payment_posting_date}",
                    "stage": "supplier_payment",
                    "error": str(exc),
                }
            )

    return result


def ensure_fiscal_year_company_links(
    company: str = "Mingalar Mobile Distribution Co., Ltd.",
    fiscal_years: list[str] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    fy_filters: dict[str, Any] = {}
    if fiscal_years:
        fy_filters["name"] = ["in", fiscal_years]

    year_rows = frappe.get_all(
        "Fiscal Year",
        filters=fy_filters,
        fields=["name", "year_start_date", "year_end_date", "disabled"],
        order_by="year_start_date asc",
    )

    results = {"processed": [], "created": [], "existing": []}

    for row in year_rows:
        fiscal_year_doc = frappe.get_doc("Fiscal Year", row.name)
        already_linked = any(link.company == company for link in fiscal_year_doc.get("companies") or [])
        summary = {
            "fiscal_year": fiscal_year_doc.name,
            "year_start_date": str(fiscal_year_doc.year_start_date),
            "year_end_date": str(fiscal_year_doc.year_end_date),
            "disabled": cint(fiscal_year_doc.disabled or 0),
            "already_linked": already_linked,
        }

        if already_linked:
            results["existing"].append(summary)
            results["processed"].append(summary)
            continue

        if not dry_run:
            fiscal_year_doc.append("companies", {"company": company})
            fiscal_year_doc.save(ignore_permissions=True)
            frappe.db.commit()

        summary["linked_company"] = company
        results["created"].append(summary)
        results["processed"].append(summary)

    return results


def apply_cash_flow_realism_configuration(
    company: str = "Mingalar Mobile Distribution Co., Ltd.",
    dry_run: bool = False,
) -> dict[str, Any]:
    account_type_targets = {
        "Employee Advances - MMOB": "Current Asset",
        "Payroll Payable - MMOB": "Current Liability",
        "Accrued Expenses - MMOB": "Current Liability",
        "Bank Loan - KBZ - MMOB": "Liability",
        "Bank Overdraft Account - MMOB": "Liability",
        "Unsecured Loans - MMOB": "Liability",
        "Secured Loans - MMOB": "Liability",
        "Interest Payable - Bank Loan - MMOB": "Current Liability",
    }

    result: dict[str, Any] = {"accounts": [], "report": None}

    for account_name, target_account_type in account_type_targets.items():
        account_doc = frappe.get_doc("Account", account_name)
        summary = {
            "account": account_name,
            "before_account_type": account_doc.account_type or "",
            "after_account_type": target_account_type,
        }
        if not dry_run and (account_doc.account_type or "") != target_account_type:
            account_doc.account_type = target_account_type
            account_doc.save(ignore_permissions=True)
            frappe.db.commit()
        result["accounts"].append(summary)

    report_doc = frappe.get_doc("Report", "Cash Flow")
    report_summary = {
        "report": report_doc.name,
        "before_module": report_doc.module,
        "after_module": "AI Assistant UI",
    }
    if not dry_run and report_doc.module != "AI Assistant UI":
        report_doc.module = "AI Assistant UI"
        report_doc.save(ignore_permissions=True)
        frappe.db.commit()
    result["report"] = report_summary

    return result


def mark_opening_style_journal_entries_as_opening(
    journal_entries: list[str] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    target_names = journal_entries or [
        "ACC-JV-2026-00084",
        "ACC-JV-2026-00085",
        "ACC-JV-2026-00086",
    ]

    result = {"processed": []}
    for journal_entry_name in target_names:
        journal_entry = frappe.get_doc("Journal Entry", journal_entry_name)
        summary = {
            "journal_entry": journal_entry.name,
            "posting_date": str(journal_entry.posting_date),
            "before_is_opening": journal_entry.is_opening,
            "after_is_opening": "Yes",
            "user_remark": journal_entry.user_remark,
        }
        if not dry_run:
            if journal_entry.is_opening != "Yes":
                frappe.db.set_value("Journal Entry", journal_entry.name, "is_opening", "Yes", update_modified=False)
            frappe.db.sql(
                """
                update `tabGL Entry`
                set is_opening = 'Yes'
                where voucher_type = 'Journal Entry' and voucher_no = %s
                """,
                (journal_entry.name,),
            )
            frappe.db.commit()
        result["processed"].append(summary)

    return result


def apply_march_2026_peak_wave() -> dict[str, Any]:
    company = "Mingalar Mobile Distribution Co., Ltd."
    warehouse = "Yangon Main Warehouse - MMOB"

    support_purchase_defs = [
        {
            "supplier": "Golden Dragon Trading Co. Ltd.",
            "posting_date": "2026-03-03",
            "posting_time": "09:20:00",
            "due_date": "2026-04-17",
            "company": company,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 30, "rate": 700000, "warehouse": warehouse},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 50, "rate": 780000, "warehouse": warehouse},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 20, "rate": 150000, "warehouse": warehouse},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 20, "rate": 140000, "warehouse": warehouse},
            ],
        },
        {
            "supplier": "Sunflower Accessories Co.",
            "posting_date": "2026-03-04",
            "posting_time": "10:00:00",
            "due_date": "2026-04-03",
            "company": company,
            "items": [
                {"item_code": "ACC-PWB-BAS-20K", "qty": 40, "rate": 82000, "warehouse": warehouse},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 100, "rate": 9000, "warehouse": warehouse},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 20, "rate": 150000, "warehouse": warehouse},
            ],
        },
        {
            "supplier": "Myanmar Tech Import Services",
            "posting_date": "2026-03-05",
            "posting_time": "10:10:00",
            "due_date": "2026-04-19",
            "company": company,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 25, "rate": 705000, "warehouse": warehouse},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 50, "rate": 785000, "warehouse": warehouse},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 20, "rate": 152000, "warehouse": warehouse},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 15, "rate": 145000, "warehouse": warehouse},
            ],
        },
        {
            "supplier": "Sunflower Accessories Co.",
            "posting_date": "2026-03-07",
            "posting_time": "11:00:00",
            "due_date": "2026-04-06",
            "company": company,
            "items": [
                {"item_code": "ACC-PWB-BAS-20K", "qty": 200, "rate": 82000, "warehouse": warehouse},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 300, "rate": 22000, "warehouse": warehouse},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 260, "rate": 20500, "warehouse": warehouse},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 500, "rate": 5000, "warehouse": warehouse},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 300, "rate": 9000, "warehouse": warehouse},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 150, "rate": 40000, "warehouse": warehouse},
                {"item_code": "MEM-USB-SND-64", "qty": 200, "rate": 9500, "warehouse": warehouse},
                {"item_code": "MEM-MSD-SND-128", "qty": 220, "rate": 15000, "warehouse": warehouse},
            ],
        },
        {
            "supplier": "Mandalay Device Wholesale",
            "posting_date": "2026-03-10",
            "posting_time": "11:40:00",
            "due_date": "2026-04-09",
            "company": company,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 10, "rate": 710000, "warehouse": warehouse},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 20, "rate": 790000, "warehouse": warehouse},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 40, "rate": 82000, "warehouse": warehouse},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 60, "rate": 20500, "warehouse": warehouse},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 10, "rate": 152000, "warehouse": warehouse},
            ],
        },
        {
            "supplier": "Shwe Taung Electronics Supply",
            "posting_date": "2026-03-12",
            "posting_time": "12:20:00",
            "due_date": "2026-04-11",
            "company": company,
            "items": [
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 25, "rate": 150000, "warehouse": warehouse},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 30, "rate": 140000, "warehouse": warehouse},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 80, "rate": 40000, "warehouse": warehouse},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 60, "rate": 82000, "warehouse": warehouse},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 80, "rate": 20500, "warehouse": warehouse},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 100, "rate": 9000, "warehouse": warehouse},
            ],
        },
        {
            "supplier": "Shan Yoma Electronics",
            "posting_date": "2026-03-14",
            "posting_time": "13:10:00",
            "due_date": "2026-04-13",
            "company": company,
            "items": [
                {"item_code": "ACC-PWB-BAS-20K", "qty": 80, "rate": 82000, "warehouse": warehouse},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 100, "rate": 40000, "warehouse": warehouse},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 20, "rate": 140000, "warehouse": warehouse},
                {"item_code": "MEM-USB-SND-64", "qty": 200, "rate": 9500, "warehouse": warehouse},
                {"item_code": "MEM-MSD-SND-128", "qty": 200, "rate": 15000, "warehouse": warehouse},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 20, "rate": 150000, "warehouse": warehouse},
            ],
        },
    ]

    credit_limit_targets = {
        "Bayint Naung Wholesale Mobile": 180000000,
        "Capital Telecom (NPT)": 160000000,
        "35th Street Mobile Wholesale": 130000000,
        "Ko Nay Lin Mobile Center": 90000000,
        "Latha Mobile Wholesale": 85000000,
        "Mandalay Mobile Hub": 75000000,
        "Mandalay Accessories Wholesale": 70000000,
        "Shwe Li Road Mobile Wholesale": 60000000,
        "Taunggyi City Mobile": 70000000,
        "Hledan Phone Hub": 60000000,
        "Thingangyun Mobile House": 45000000,
        "Hlaing Tharyar Mobile Corner": 55000000,
        "Sanchaung Mobile Plaza": 25000000,
        "Mayangone Mobile House": 35000000,
        "Lanmadaw Telecom & Gadgets": 40000000,
        "Pazundaung Phone House": 20000000,
        "Taunggyi Star Mobile": 35000000,
        "Chan Aye Mobile Trading Hub": 25000000,
        "Thaketa Mobile Exchange": 15000000,
        "Pazundaung Mobile Distribution": 20000000,
    }

    quotation_specs = [
        {
            "label": "march_capital_year_end_quote",
            "customer": "Capital Telecom (NPT)",
            "transaction_date": "2026-03-04",
            "valid_till": "2026-03-18",
            "payment_terms_template": "45 Days Approved - MMOB",
            "set_warehouse": warehouse,
            "remarks": "March year-end negotiated key-account quotation before pre-Thingyan stocking.",
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 5, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 10, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 25, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 30, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 40, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 40, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 40, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 20, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 10, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 10, "rate": 195000},
                {"item_code": "MEM-USB-SND-64", "qty": 30, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 30, "rate": 26000},
            ],
        },
        {
            "label": "march_bayint_bulk_quote",
            "customer": "Bayint Naung Wholesale Mobile",
            "transaction_date": "2026-03-05",
            "valid_till": "2026-03-20",
            "payment_terms_template": "45 Days Approved - MMOB",
            "set_warehouse": warehouse,
            "remarks": "March bulk wholesale quote for Bayint Naung ahead of fiscal-year-end customer demand.",
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 8, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 12, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 30, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 40, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 50, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 60, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 50, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 30, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 10, "rate": 220000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
            ],
        },
        {
            "label": "march_35th_major_quote",
            "customer": "35th Street Mobile Wholesale",
            "transaction_date": "2026-03-07",
            "valid_till": "2026-03-21",
            "payment_terms_template": "45 Days Approved - MMOB",
            "set_warehouse": warehouse,
            "remarks": "March 35th Street major mixed-product quotation before month-end sell-through push.",
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 6, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 12, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 20, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 30, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 30, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 40, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 30, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 20, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 10, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 6, "rate": 195000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
            ],
        },
        {
            "label": "march_mandalay_hub_quote",
            "customer": "Mandalay Mobile Hub",
            "transaction_date": "2026-03-12",
            "valid_till": "2026-03-24",
            "payment_terms_template": "30 Days - MMOB",
            "set_warehouse": warehouse,
            "remarks": "March Mandalay regional replenishment quote during the strongest trading month.",
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 3, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 5, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 8, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 3, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 10, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 8, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 4, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 4, "rate": 195000},
                {"item_code": "MEM-USB-SND-64", "qty": 10, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 10, "rate": 26000},
            ],
        },
        {
            "label": "march_hledan_lost_quote",
            "customer": "Hledan Mobile Trade Center",
            "transaction_date": "2026-03-18",
            "valid_till": "2026-03-25",
            "payment_terms_template": "30 Days - MMOB",
            "set_warehouse": warehouse,
            "target_status": "Lost",
            "remarks": "March Hledan quote lost after customer delayed the decision and chose a smaller competitor package.",
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 5, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 30, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 4, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 4, "rate": 195000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
            ],
        },
        {
            "label": "march_hlaingtharyar_expired_quote",
            "customer": "Hlaing Tharyar Mobile Corner",
            "transaction_date": "2026-03-22",
            "valid_till": "2026-03-28",
            "payment_terms_template": "15 Days - MMOB",
            "set_warehouse": warehouse,
            "target_status": "Expired",
            "remarks": "March Hlaing Tharyar quote expired after the customer postponed branch restock until after Thingyan.",
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 1, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 3, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 6, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 15, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 15, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 10, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 6, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 4, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 3, "rate": 195000},
                {"item_code": "MEM-USB-SND-64", "qty": 15, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 15, "rate": 26000},
            ],
        },
    ]

    chain_specs = [
        {
            "label": "march_capital_quote_chain",
            "quotation_label": "march_capital_year_end_quote",
            "customer": "Capital Telecom (NPT)",
            "sales_order": {
                "transaction_date": "2026-03-05",
                "delivery_date": "2026-03-06",
                "po_no": "CPO-2026-03-501",
                "po_date": "2026-03-05",
                "payment_terms_template": "45 Days Approved - MMOB",
                "set_warehouse": warehouse,
                "remarks": "Approved March Capital replenishment order before year-end wholesale push.",
            },
            "delivery_note": {
                "posting_date": "2026-03-06",
                "posting_time": "10:20:00",
                "remarks": "March Capital dispatch under approved pre-Thingyan stocking program.",
            },
            "sales_invoice": {
                "posting_date": "2026-03-06",
                "posting_time": "10:45:00",
                "due_date": "2026-04-20",
                "payment_terms_template": "45 Days Approved - MMOB",
                "remarks": "March Capital invoice for approved year-end key-account restock.",
            },
        },
        {
            "label": "march_bayint_quote_chain",
            "quotation_label": "march_bayint_bulk_quote",
            "customer": "Bayint Naung Wholesale Mobile",
            "sales_order": {
                "transaction_date": "2026-03-07",
                "delivery_date": "2026-03-08",
                "po_no": "CPO-2026-03-502",
                "po_date": "2026-03-07",
                "payment_terms_template": "45 Days Approved - MMOB",
                "set_warehouse": warehouse,
                "remarks": "Bayint bulk March order after approved fiscal-year-end stocking quote.",
            },
            "delivery_note": {
                "posting_date": "2026-03-08",
                "posting_time": "10:50:00",
                "remarks": "March Bayint bulk dispatch for strong wholesale month-end sell-through.",
            },
            "sales_invoice": {
                "posting_date": "2026-03-08",
                "posting_time": "11:10:00",
                "due_date": "2026-04-22",
                "payment_terms_template": "45 Days Approved - MMOB",
                "remarks": "March Bayint invoice for high-volume pre-holiday wholesale lane.",
            },
        },
        {
            "label": "march_35th_quote_chain",
            "quotation_label": "march_35th_major_quote",
            "customer": "35th Street Mobile Wholesale",
            "sales_order": {
                "transaction_date": "2026-03-10",
                "delivery_date": "2026-03-11",
                "po_no": "CPO-2026-03-503",
                "po_date": "2026-03-10",
                "payment_terms_template": "45 Days Approved - MMOB",
                "set_warehouse": warehouse,
                "remarks": "35th Street approved March order aligned with strong downtown wholesale demand.",
            },
            "delivery_note": {
                "posting_date": "2026-03-11",
                "posting_time": "13:40:00",
                "remarks": "March 35th Street dispatch during strongest operating stretch.",
            },
            "sales_invoice": {
                "posting_date": "2026-03-11",
                "posting_time": "14:05:00",
                "due_date": "2026-04-25",
                "payment_terms_template": "45 Days Approved - MMOB",
                "remarks": "March 35th Street invoice after approved mixed-product dispatch.",
            },
        },
        {
            "label": "march_ko_nay_lin_chain",
            "customer": "Ko Nay Lin Mobile Center",
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 5, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 11, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 15, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 25, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 30, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 30, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 25, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 15, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 8, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 6, "rate": 195000},
                {"item_code": "MEM-USB-SND-64", "qty": 30, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 30, "rate": 26000},
            ],
            "sales_order": {
                "transaction_date": "2026-03-12",
                "delivery_date": "2026-03-13",
                "po_no": "CPO-2026-03-504",
                "po_date": "2026-03-12",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "Ko Nay Lin March replenishment order after visible turnover improvement in February.",
            },
            "delivery_note": {
                "posting_date": "2026-03-13",
                "posting_time": "10:15:00",
                "remarks": "March Ko Nay Lin dispatch for full mixed-category wholesale restock.",
            },
            "sales_invoice": {
                "posting_date": "2026-03-13",
                "posting_time": "10:35:00",
                "due_date": "2026-04-12",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "March Ko Nay Lin invoice after confirmed wholesale dispatch.",
            },
        },
        {
            "label": "march_latha_chain",
            "customer": "Latha Mobile Wholesale",
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 4, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 8, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 30, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 6, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 4, "rate": 195000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
            ],
            "sales_order": {
                "transaction_date": "2026-03-14",
                "delivery_date": "2026-03-15",
                "po_no": "CPO-2026-03-505",
                "po_date": "2026-03-14",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "March Latha order for regular downtown wholesale restock ahead of holiday slowdown.",
            },
            "delivery_note": {
                "posting_date": "2026-03-15",
                "posting_time": "11:10:00",
                "remarks": "March Latha dispatch as part of stronger inner-city wholesale movement.",
            },
            "sales_invoice": {
                "posting_date": "2026-03-15",
                "posting_time": "11:30:00",
                "due_date": "2026-04-14",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "March Latha invoice after ordinary pre-Thingyan replenishment dispatch.",
            },
        },
        {
            "label": "march_mandalay_hub_quote_chain",
            "quotation_label": "march_mandalay_hub_quote",
            "customer": "Mandalay Mobile Hub",
            "sales_order": {
                "transaction_date": "2026-03-17",
                "delivery_date": "2026-03-18",
                "po_no": "CPO-2026-03-506",
                "po_date": "2026-03-17",
                "payment_terms_template": "30 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "March Mandalay Mobile Hub order converted from regional replenishment quote.",
            },
            "delivery_note": {
                "posting_date": "2026-03-18",
                "posting_time": "12:10:00",
                "remarks": "March Mandalay Mobile Hub dispatch from Yangon for upper-Mandalay resupply.",
            },
            "sales_invoice": {
                "posting_date": "2026-03-18",
                "posting_time": "12:30:00",
                "due_date": "2026-04-17",
                "payment_terms_template": "30 Days - MMOB",
                "remarks": "March Mandalay Mobile Hub invoice after regional replenishment dispatch.",
            },
        },
        {
            "label": "march_shwe_li_chain",
            "customer": "Shwe Li Road Mobile Wholesale",
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 5, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 5, "rate": 110000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 10, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 5, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 4, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 4, "rate": 195000},
                {"item_code": "MEM-USB-SND-64", "qty": 10, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 10, "rate": 26000},
            ],
            "sales_order": {
                "transaction_date": "2026-03-20",
                "delivery_date": "2026-03-21",
                "po_no": "CPO-2026-03-507",
                "po_date": "2026-03-20",
                "payment_terms_template": "15 Days - MMOB",
                "set_warehouse": warehouse,
                "remarks": "March Shwe Li order showing solid but smaller restock than Bayint and 35th Street.",
            },
            "delivery_note": {
                "posting_date": "2026-03-21",
                "posting_time": "10:40:00",
                "remarks": "March Shwe Li dispatch under controlled mid-sized wholesale lane.",
            },
            "sales_invoice": {
                "posting_date": "2026-03-21",
                "posting_time": "11:00:00",
                "due_date": "2026-04-05",
                "payment_terms_template": "15 Days - MMOB",
                "remarks": "March Shwe Li invoice after normal mixed-product replenishment dispatch.",
            },
        },
        {
            "label": "march_taunggyi_city_chain",
            "customer": "Taunggyi City Mobile",
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 4, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 5, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 10, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 5, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 4, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 2, "rate": 195000},
                {"item_code": "MEM-USB-SND-64", "qty": 15, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
            ],
            "sales_order": {
                "transaction_date": "2026-03-23",
                "delivery_date": "2026-03-24",
                "po_no": "CPO-2026-03-508",
                "po_date": "2026-03-23",
                "payment_terms_template": "Cash on Delivery - MMOB",
                "set_warehouse": warehouse,
                "remarks": "March Taunggyi City order for mixed retail-wholesale crossover demand before month close.",
            },
            "delivery_note": {
                "posting_date": "2026-03-24",
                "posting_time": "13:00:00",
                "remarks": "March Taunggyi City dispatch for Shan-focused month-end turnover.",
            },
            "sales_invoice": {
                "posting_date": "2026-03-24",
                "posting_time": "13:20:00",
                "due_date": "2026-03-24",
                "payment_terms_template": "Cash on Delivery - MMOB",
                "remarks": "March Taunggyi City COD invoice after completed dispatch.",
            },
        },
    ]

    direct_sales_defs = [
        {
            "customer": "Hledan Phone Hub",
            "posting_date": "2026-03-09",
            "due_date": "2026-03-16",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 3, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 6, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 30, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 15, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 6, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 6, "rate": 195000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
            ],
        },
        {
            "customer": "City Mobile Mart",
            "posting_date": "2026-03-17",
            "due_date": "2026-03-24",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 5, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 8, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 15, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 15, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 15, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 5, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 4, "rate": 195000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
            ],
        },
        {
            "customer": "Thingangyun Mobile House",
            "posting_date": "2026-03-20",
            "due_date": "2026-03-27",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 4, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 8, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 10, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 10, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 8, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 4, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 4, "rate": 195000},
                {"item_code": "MEM-USB-SND-64", "qty": 15, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
            ],
        },
        {
            "customer": "Hlaing Tharyar Mobile Corner",
            "posting_date": "2026-03-24",
            "due_date": "2026-03-31",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 1, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 3, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 6, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 15, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 15, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 10, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 6, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 4, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 3, "rate": 195000},
                {"item_code": "MEM-USB-SND-64", "qty": 15, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 15, "rate": 26000},
            ],
        },
        {
            "customer": "Sanchaung Mobile Plaza",
            "posting_date": "2026-03-26",
            "due_date": "2026-03-26",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 1, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 3, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 5, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 10, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 15, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 10, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 5, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 3, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 2, "rate": 195000},
                {"item_code": "MEM-USB-SND-64", "qty": 15, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 15, "rate": 26000},
            ],
        },
        {
            "customer": "Mayangone Mobile House",
            "posting_date": "2026-03-22",
            "due_date": "2026-03-29",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 1, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 3, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 4, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 10, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 10, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 8, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 5, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 2, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 2, "rate": 195000},
                {"item_code": "MEM-USB-SND-64", "qty": 10, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 10, "rate": 26000},
            ],
        },
        {
            "customer": "Lanmadaw Telecom & Gadgets",
            "posting_date": "2026-03-25",
            "due_date": "2026-04-01",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 1, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 4, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 13, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 8, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 10, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 8, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 4, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 2, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 1, "rate": 195000},
                {"item_code": "MEM-USB-SND-64", "qty": 10, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 10, "rate": 26000},
            ],
        },
        {
            "customer": "Pazundaung Phone House",
            "posting_date": "2026-03-27",
            "due_date": "2026-03-31",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 1, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 6, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 7, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 8, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 5, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 4, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 2, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 1, "rate": 195000},
                {"item_code": "MEM-USB-SND-64", "qty": 15, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 10, "rate": 26000},
            ],
        },
        {
            "customer": "Taunggyi Star Mobile",
            "posting_date": "2026-03-28",
            "due_date": "2026-03-28",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 1, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 10, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 10, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 10, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 5, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 2, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 2, "rate": 195000},
                {"item_code": "MEM-USB-SND-64", "qty": 10, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 10, "rate": 26000},
            ],
        },
        {
            "customer": "Chan Aye Mobile Trading Hub",
            "posting_date": "2026-03-29",
            "due_date": "2026-04-05",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 1, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 2, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 4, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 8, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 8, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 10, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 5, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 4, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 2, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 1, "rate": 195000},
                {"item_code": "MEM-USB-SND-64", "qty": 10, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 10, "rate": 26000},
            ],
        },
        {
            "customer": "Thaketa Mobile Exchange",
            "posting_date": "2026-03-31",
            "due_date": "2026-03-31",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "ACC-PWB-BAS-20K", "qty": 10, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 25, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 10, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 5, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 2, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 1, "rate": 195000},
                {"item_code": "MEM-USB-SND-64", "qty": 10, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 10, "rate": 26000},
            ],
        },
        {
            "customer": "Pazundaung Mobile Distribution",
            "posting_date": "2026-03-30",
            "due_date": "2026-04-06",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 1, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 3, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 5, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 15, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 10, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 5, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 3, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 3, "rate": 195000},
                {"item_code": "MEM-USB-SND-64", "qty": 15, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 15, "rate": 26000},
            ],
        },
        {
            "customer": "Capital Telecom (NPT)",
            "posting_date": "2026-03-29",
            "due_date": "2026-05-13",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 2, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 5, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 15, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 25, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 20, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 20, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 10, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 6, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 6, "rate": 195000},
                {"item_code": "MEM-USB-SND-64", "qty": 20, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
            ],
        },
        {
            "customer": "Bayint Naung Wholesale Mobile",
            "posting_date": "2026-03-31",
            "due_date": "2026-04-30",
            "warehouse": warehouse,
            "company": company,
            "items": [
                {"item_code": "SPH-XMI-RN13-8/256", "qty": 1, "rate": 900000},
                {"item_code": "SPH-SAM-A15-6/128", "qty": 4, "rate": 1000000},
                {"item_code": "ACC-PWB-BAS-20K", "qty": 6, "rate": 110000},
                {"item_code": "ACC-CHR-SAM-25W", "qty": 20, "rate": 32000},
                {"item_code": "ACC-CHR-XMI-33W", "qty": 10, "rate": 30000},
                {"item_code": "ACC-CBL-BAS-TC1M", "qty": 20, "rate": 8000},
                {"item_code": "ACC-CBL-UGR-TC1M", "qty": 10, "rate": 14000},
                {"item_code": "ACC-AUD-XMI-BUDS4", "qty": 6, "rate": 58000},
                {"item_code": "GAD-SPK-JBL-GO3", "qty": 4, "rate": 220000},
                {"item_code": "GAD-WCH-XMI-MB8", "qty": 4, "rate": 195000},
                {"item_code": "MEM-USB-SND-64", "qty": 15, "rate": 16000},
                {"item_code": "MEM-MSD-SND-128", "qty": 20, "rate": 26000},
            ],
        },
    ]

    payment_specs = [
        ("Capital Telecom (NPT)", "2026-03-06", "2026-03-14", 5000000),
        ("Bayint Naung Wholesale Mobile", "2026-03-08", "2026-03-15", 4000000),
        ("35th Street Mobile Wholesale", "2026-03-11", "2026-03-18", 4000000),
        ("Ko Nay Lin Mobile Center", "2026-03-13", "2026-03-21", 3000000),
        ("Latha Mobile Wholesale", "2026-03-15", "2026-03-24", 2000000),
        ("Mandalay Mobile Hub", "2026-03-18", "2026-03-26", 2000000),
        ("Shwe Li Road Mobile Wholesale", "2026-03-21", "2026-03-28", 2000000),
        ("Taunggyi City Mobile", "2026-03-24", "2026-03-24", 3000000),
        ("Hledan Phone Hub", "2026-03-09", "2026-03-19", 2000000),
        ("City Mobile Mart", "2026-03-17", "2026-03-25", 3000000),
        ("Thingangyun Mobile House", "2026-03-20", "2026-03-28", 2000000),
        ("Mayangone Mobile House", "2026-03-22", "2026-03-29", 1500000),
        ("Sanchaung Mobile Plaza", "2026-03-26", "2026-03-26", 1500000),
        ("Taunggyi Star Mobile", "2026-03-28", "2026-03-28", 2000000),
        ("Chan Aye Mobile Trading Hub", "2026-03-29", "2026-03-31", 1000000),
        ("Thaketa Mobile Exchange", "2026-03-31", "2026-03-31", 1000000),
        ("Pazundaung Mobile Distribution", "2026-03-30", "2026-03-31", 2500000),
        ("Capital Telecom (NPT)", "2026-03-29", "2026-03-31", 3000000),
        ("Bayint Naung Wholesale Mobile", "2026-03-31", "2026-03-31", 2000000),
    ]
    settlement_followup_specs = [
        ("Capital Telecom (NPT)", "2026-01-21", "2026-03-20", 6000000),
        ("Bayint Naung Wholesale Mobile", "2026-01-14", "2026-03-19", 5000000),
        ("35th Street Mobile Wholesale", "2026-01-11", "2026-03-22", 7000000),
        ("Taunggyi City Mobile", "2026-01-23", "2026-03-26", 4000000),
        ("Mandalay Accessories Wholesale", "2026-01-19", "2026-03-27", 4000000),
        ("Bayint Naung Wholesale Mobile", "2026-02-13", "2026-03-27", 4000000),
        ("Ko Nay Lin Mobile Center", "2026-02-19", "2026-03-28", 3000000),
        ("Shwe Li Road Mobile Wholesale", "2026-02-21", "2026-03-29", 3000000),
        ("Mandalay Accessories Wholesale", "2026-02-17", "2026-03-29", 3000000),
        ("Capital Telecom (NPT)", "2026-02-26", "2026-03-30", 5000000),
    ]
    supplier_payment_specs = [
        ("Golden Dragon Trading Co. Ltd.", "2026-01-29", "2026-03-19", 6000000),
        ("Myanmar Tech Import Services", "2026-01-12", "2026-03-21", 7000000),
        ("Sunflower Accessories Co.", "2026-01-31", "2026-03-24", 6000000),
        ("Mandalay Device Wholesale", "2026-01-23", "2026-03-25", 4000000),
        ("Golden Dragon Trading Co. Ltd.", "2026-03-03", "2026-03-28", 5000000),
        ("Myanmar Tech Import Services", "2026-03-05", "2026-03-29", 5000000),
        ("Sunflower Accessories Co.", "2026-03-07", "2026-03-30", 4000000),
        ("Shwe Taung Electronics Supply", "2026-03-12", "2026-03-31", 3000000),
    ]

    quotation_lookup: dict[str, str] = {}
    quotation_spec_lookup = {spec["label"]: spec for spec in quotation_specs}
    invoice_lookup: dict[tuple[str, str], str] = {}
    result = {
        "purchase_invoices": [],
        "credit_limits": [],
        "quotations": [],
        "sales_orders": [],
        "delivery_notes": [],
        "sales_invoices": [],
        "payment_entries": [],
        "supplier_payment_entries": [],
        "failed": [],
    }

    for supplier_def in support_purchase_defs:
        try:
            supplier_def["expected_total"] = _sum_item_amounts(supplier_def["items"])
            purchase_invoice_name = _create_purchase_invoice(supplier_def)
            frappe.db.commit()
            result["purchase_invoices"].append(
                {
                    "supplier": supplier_def["supplier"],
                    "purchase_invoice": purchase_invoice_name,
                    "posting_date": supplier_def["posting_date"],
                    "grand_total": supplier_def["expected_total"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"support_purchase_{supplier_def['supplier']}_{supplier_def['posting_date']}",
                    "stage": "support_purchase",
                    "error": str(exc),
                }
            )

    for customer_name, credit_limit in credit_limit_targets.items():
        try:
            customer = frappe.get_doc("Customer", customer_name)
            limit_row = None
            for row in customer.credit_limits:
                if row.company == company:
                    limit_row = row
                    break
            if limit_row:
                limit_row.credit_limit = credit_limit
                limit_row.bypass_credit_limit_check = 0
            else:
                customer.append(
                    "credit_limits",
                    {
                        "company": company,
                        "credit_limit": credit_limit,
                        "bypass_credit_limit_check": 0,
                    },
                )
            customer.save(ignore_permissions=True)
            frappe.db.commit()
            result["credit_limits"].append({"customer": customer_name, "credit_limit": credit_limit})
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"credit_limit_{customer_name}",
                    "stage": "credit_limit",
                    "error": str(exc),
                }
            )

    for spec in quotation_specs:
        try:
            spec["company"] = company
            spec["expected_total"] = _sum_item_amounts(spec["items"])
            quotation_name = _create_quotation(spec)
            quotation_lookup[spec["label"]] = quotation_name
            if spec.get("target_status") == "Lost":
                frappe.db.set_value(
                    "Quotation",
                    quotation_name,
                    {
                        "status": "Lost",
                        "order_lost_reason": "March year-end quote lost after delayed confirmation and competitor comparison.",
                    },
                    update_modified=False,
                )
            elif spec.get("target_status") == "Expired":
                frappe.db.set_value(
                    "Quotation",
                    quotation_name,
                    {"status": "Expired", "order_lost_reason": None},
                    update_modified=False,
                )
            frappe.db.commit()
            result["quotations"].append(
                {
                    "label": spec["label"],
                    "quotation": quotation_name,
                    "customer": spec["customer"],
                    "grand_total": spec["expected_total"],
                    "target_status": spec.get("target_status") or "Submitted",
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "stage": "quotation", "error": str(exc)})

    for spec in chain_specs:
        try:
            chain_items = spec.get("items")
            if spec.get("quotation_label"):
                expected_total = _sum_item_amounts(quotation_spec_lookup[spec["quotation_label"]]["items"])
            else:
                expected_total = _sum_item_amounts(chain_items or [])
            order_payload = dict(spec["sales_order"])
            order_payload["customer"] = spec["customer"]
            order_payload["company"] = company
            order_payload["items"] = list(
                quotation_spec_lookup[spec["quotation_label"]]["items"]
                if spec.get("quotation_label")
                else (chain_items or [])
            )
            order_payload["expected_total"] = expected_total
            order_name = _create_sales_order(order_payload)
            if spec.get("quotation_label"):
                frappe.db.set_value(
                    "Quotation",
                    quotation_lookup[spec["quotation_label"]],
                    {"status": "Ordered"},
                    update_modified=False,
                )

            delivery_note_name = _create_delivery_note_from_sales_order(order_name, spec["delivery_note"])
            invoice_name = _create_sales_invoice_from_delivery_note(delivery_note_name, spec["sales_invoice"])
            frappe.db.commit()

            invoice_lookup[(spec["customer"], spec["sales_invoice"]["posting_date"])] = invoice_name
            result["sales_orders"].append(
                {
                    "label": spec["label"],
                    "sales_order": order_name,
                    "customer": spec["customer"],
                    "grand_total": expected_total,
                }
            )
            result["delivery_notes"].append(
                {"label": spec["label"], "delivery_note": delivery_note_name, "sales_order": order_name}
            )
            result["sales_invoices"].append(
                {
                    "label": spec["label"],
                    "sales_invoice": invoice_name,
                    "customer": spec["customer"],
                    "posting_date": spec["sales_invoice"]["posting_date"],
                    "grand_total": expected_total,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append({"label": spec["label"], "stage": "chain", "error": str(exc)})

    for definition in direct_sales_defs:
        try:
            definition["expected_total"] = _sum_item_amounts(definition["items"])
            invoice_name = _create_sales_invoice(definition)
            frappe.db.commit()
            invoice_lookup[(definition["customer"], definition["posting_date"])] = invoice_name
            result["sales_invoices"].append(
                {
                    "label": "direct_invoice",
                    "sales_invoice": invoice_name,
                    "customer": definition["customer"],
                    "posting_date": definition["posting_date"],
                    "grand_total": definition["expected_total"],
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"direct_{definition['customer']}_{definition['posting_date']}",
                    "stage": "direct_invoice",
                    "error": str(exc),
                }
            )

    for customer, invoice_posting_date, payment_posting_date, amount in payment_specs:
        invoice_name = invoice_lookup.get((customer, invoice_posting_date)) or _find_submitted_sales_invoice(
            customer,
            invoice_posting_date,
        )
        if not invoice_name:
            result["failed"].append(
                {
                    "label": f"payment_{customer}_{payment_posting_date}",
                    "stage": "payment_lookup",
                    "error": "sales_invoice_missing",
                }
            )
            continue

        try:
            payment_name = _create_partial_payment("Sales Invoice", invoice_name, payment_posting_date, amount)
            frappe.db.commit()
            result["payment_entries"].append(
                {
                    "customer": customer,
                    "sales_invoice": invoice_name,
                    "payment_entry": payment_name,
                    "amount": amount,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"payment_{customer}_{payment_posting_date}",
                    "stage": "payment",
                    "error": str(exc),
                }
            )

    for customer, invoice_posting_date, payment_posting_date, amount in settlement_followup_specs:
        invoice_name = _find_submitted_sales_invoice(customer, invoice_posting_date)
        if not invoice_name:
            result["failed"].append(
                {
                    "label": f"settlement_followup_{customer}_{payment_posting_date}",
                    "stage": "payment_lookup",
                    "error": "sales_invoice_missing",
                }
            )
            continue

        try:
            payment_name = _create_partial_payment("Sales Invoice", invoice_name, payment_posting_date, amount)
            frappe.db.commit()
            result["payment_entries"].append(
                {
                    "customer": customer,
                    "sales_invoice": invoice_name,
                    "payment_entry": payment_name,
                    "amount": amount,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"settlement_followup_{customer}_{payment_posting_date}",
                    "stage": "payment",
                    "error": str(exc),
                }
            )

    for supplier, invoice_posting_date, payment_posting_date, amount in supplier_payment_specs:
        invoice_name = _find_submitted_purchase_invoice(supplier, invoice_posting_date)
        if not invoice_name:
            result["failed"].append(
                {
                    "label": f"supplier_payment_{supplier}_{payment_posting_date}",
                    "stage": "supplier_payment_lookup",
                    "error": "purchase_invoice_missing",
                }
            )
            continue

        try:
            payment_name = _create_partial_payment("Purchase Invoice", invoice_name, payment_posting_date, amount)
            frappe.db.commit()
            result["supplier_payment_entries"].append(
                {
                    "supplier": supplier,
                    "purchase_invoice": invoice_name,
                    "payment_entry": payment_name,
                    "amount": amount,
                }
            )
        except Exception as exc:
            frappe.db.rollback()
            result["failed"].append(
                {
                    "label": f"supplier_payment_{supplier}_{payment_posting_date}",
                    "stage": "supplier_payment",
                    "error": str(exc),
                }
            )

    return result
