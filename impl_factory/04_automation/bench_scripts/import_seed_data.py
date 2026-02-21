import os, csv
import frappe
from frappe.utils import now_datetime, getdate

COMPANY = "Mingalar Mobile Distribution Co., Ltd."
BASE = "/tmp/seed_data"
LOG  = "/tmp/seed_import.log"

VALID_EMP_STATUS = {"Active", "Inactive", "Suspended", "Left"}

def split_first_name(fullname: str) -> str:
    fullname = (fullname or '').strip()
    if not fullname:
        return 'Employee'
    # Myanmar honorifics are part of the name; keep them in first_name
    return fullname.split()[0]

def guess_dob(dept: str, designation: str) -> str:
    # deterministic + plausible DOBs (dummy data)
    key = ((dept or '') + '|' + (designation or '')).lower()
    # senior roles
    if 'general manager' in key or 'manager' in key:
        return '1982-06-15'
    # accountant/admin
    if 'account' in key or 'hr' in key or 'admin' in key:
        return '1991-09-20'
    # supervisors
    if 'supervisor' in key:
        return '1989-03-10'
    # default staff
    return '1996-01-05'

def log(msg: str):
    ts = now_datetime().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def read_csv(filename: str):
    path = os.path.join(BASE, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        for row in r:
            clean = {(k or "").strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
            if all((not v) for v in clean.values()):
                continue
            yield clean

def to_int(v):
    if v is None: return 0
    s = str(v).strip()
    if s == "": return 0
    try: return int(float(s))
    except: return 0

def to_float(v):
    if v is None: return 0.0
    s = str(v).strip()
    if s == "": return 0.0
    try: return float(s)
    except: return 0.0

def safe_parent(v):
    # Root nodes should have blank parent, never fallback to "All ..."
    s = (v or "").strip()
    return s or ""

def safe_date(v):
    s = (v or "").strip()
    if not s:
        return None
    try:
        return getdate(s)  # handles YYYY-MM-DD and many common formats
    except Exception:
        return None

def insert_if_missing(doctype: str, filters: dict, docfields: dict):
    existing = frappe.db.exists(doctype, filters)
    if existing:
        return False, existing
    doc = frappe.get_doc({"doctype": doctype, **docfields})
    doc.insert(ignore_permissions=False)
    return True, doc.name

def run():
    frappe.set_user("Administrator")
    frappe.flags.in_import = True

    if not frappe.db.exists("Company", COMPANY):
        raise Exception(f"Company not found: {COMPANY}. Create Company first via Setup Wizard.")

    # reset log
    try:
        if os.path.exists(LOG):
            os.remove(LOG)
    except Exception:
        pass

    log("=== Seed Import START ===")
    log(f"Company: {COMPANY}")
    log(f"CSV Base: {BASE}")

    summary = []

    # 1) Branch
    created = 0
    for r in read_csv("branches.csv"):
        name = r.get("Branch")
        if not name: continue
        ok, _ = insert_if_missing("Branch", {"branch": name}, {"branch": name})
        created += 1 if ok else 0
    frappe.db.commit(); summary.append(("Branch", created))

    # 2) Brand
    created = 0
    for r in read_csv("brands.csv"):
        name = r.get("Brand")
        if not name: continue
        ok, _ = insert_if_missing("Brand", {"brand": name}, {"brand": name})
        created += 1 if ok else 0
    frappe.db.commit(); summary.append(("Brand", created))

    # 3) UOM
    created = 0
    for r in read_csv("uom.csv"):
        name = r.get("UOM Name")
        if not name: continue
        ok, _ = insert_if_missing("UOM", {"uom_name": name}, {"uom_name": name})
        created += 1 if ok else 0
    frappe.db.commit(); summary.append(("UOM", created))

    # 4) Item Group (tree)
    created = 0
    for r in read_csv("item_groups.csv"):
        name = r.get("Item Group Name")
        if not name: continue
        fields = {
            "item_group_name": name,
            "parent_item_group": (r.get("Parent Item Group") or "All Item Groups"),
            "is_group": to_int(r.get("Is Group")),
        }
        ok, _ = insert_if_missing("Item Group", {"item_group_name": name}, fields)
        created += 1 if ok else 0
    frappe.db.commit(); summary.append(("Item Group", created))

    # 5) Price List
    created = 0
    for r in read_csv("price_lists.csv"):
        name = r.get("Price List Name")
        if not name: continue
        fields = {
            "price_list_name": name,
            "enabled": to_int(r.get("Enabled") or 1),
            "currency": r.get("Currency") or "MMK",
            "selling": to_int(r.get("Selling")),
            "buying": to_int(r.get("Buying")),
        }
        ok, _ = insert_if_missing("Price List", {"price_list_name": name}, fields)
        created += 1 if ok else 0
    frappe.db.commit(); summary.append(("Price List", created))

    # 6) Territory (tree)
    created = 0
    for r in read_csv("territories.csv"):
        name = r.get("Territory Name")
        if not name: continue
        fields = {
            "territory_name": name,
            "parent_territory": (r.get("Parent Territory") or "All Territories"),
            "is_group": to_int(r.get("Is Group")),
        }
        ok, _ = insert_if_missing("Territory", {"territory_name": name}, fields)
        created += 1 if ok else 0
    frappe.db.commit(); summary.append(("Territory", created))

    # 7) Customer Group (tree)
    created = 0
    for r in read_csv("customer_groups.csv"):
        name = r.get("Customer Group Name")
        if not name: continue
        fields = {
            "customer_group_name": name,
            "parent_customer_group": (r.get("Parent Customer Group") or "All Customer Groups"),
            "is_group": to_int(r.get("Is Group")),
        }
        ok, _ = insert_if_missing("Customer Group", {"customer_group_name": name}, fields)
        created += 1 if ok else 0
    frappe.db.commit(); summary.append(("Customer Group", created))

    # 8) Supplier
    created = 0
    for r in read_csv("suppliers.csv"):
        name = r.get("Supplier Name")
        if not name: continue
        fields = {
            "supplier_name": name,
            "supplier_type": r.get("Supplier Type") or "Company",
            "country": r.get("Country") or "Myanmar",
            "mobile_no": r.get("Mobile No"),
            "city": r.get("City"),
        }
        ok, _ = insert_if_missing("Supplier", {"supplier_name": name}, fields)
        created += 1 if ok else 0
    frappe.db.commit(); summary.append(("Supplier", created))

    # 9) Customer
    created = 0
    for r in read_csv("customers.csv"):
        name = r.get("Customer Name")
        if not name: continue
        fields = {
            "customer_name": name,
            "customer_type": r.get("Customer Type") or "Company",
            "customer_group": r.get("Customer Group") or "Retail",
            "territory": r.get("Territory") or "Other",
            "mobile_no": r.get("Mobile No"),
            "city": r.get("City"),
        }
        ok, _ = insert_if_missing("Customer", {"customer_name": name}, fields)
        created += 1 if ok else 0
    frappe.db.commit(); summary.append(("Customer", created))

    # 10) Sales Person (tree) - root parent must be blank
    created = 0
    for r in read_csv("sales_persons.csv"):
        name = r.get("Sales Person Name")
        if not name: continue
        fields = {
            "sales_person_name": name,
            "parent_sales_person": safe_parent(r.get("Parent Sales Person")),
            "is_group": to_int(r.get("Is Group")),
            "enabled": to_int(r.get("Enabled") or 1),
        }
        ok, _ = insert_if_missing("Sales Person", {"sales_person_name": name}, fields)
        created += 1 if ok else 0
    frappe.db.commit(); summary.append(("Sales Person", created))

    # 11) Department (company mandatory in your build)
    created = 0
    for r in read_csv("departments.csv"):
        name = r.get("Department Name")
        if not name: continue
        fields = {"department_name": name, "company": COMPANY}
        ok, _ = insert_if_missing("Department", {"department_name": name, "company": COMPANY}, fields)
        created += 1 if ok else 0
    frappe.db.commit(); summary.append(("Department", created))

    # 12) Designation (field is designation_name in your build)
    created = 0
    for r in read_csv("designations.csv"):
        name = r.get("Designation")
        if not name: continue
        fields = {"designation_name": name}
        ok, _ = insert_if_missing("Designation", {"designation_name": name}, fields)
        created += 1 if ok else 0
    frappe.db.commit(); summary.append(("Designation", created))

    # 13) Employee (status must be valid)
    created = 0
    for r in read_csv("employees.csv"):
        emp = r.get("Employee Name")
        if not emp: continue

        status = (r.get("Status") or "Active").strip()
        if status not in VALID_EMP_STATUS:
            status = "Active"

        doj = safe_date(r.get("Date of Joining")) or safe_date("2026-02-01")

        filters = {"employee_name": emp, "company": COMPANY}
        fields = {
            "employee_name": emp,
            "first_name": split_first_name(emp),
            "date_of_birth": safe_date(r.get("Date of Birth")) or safe_date(guess_dob(r.get("Department"), r.get("Designation"))),
            "status": status,
            "gender": r.get("Gender"),
            "department": r.get("Department"),
            "designation": r.get("Designation"),
            "employment_type": r.get("Employment Type") or "Full-time",
            "company": COMPANY,
            "date_of_joining": doj,
            "cell_number": r.get("Cell Number"),
            "branch": r.get("Branch"),
        }
        ok, _ = insert_if_missing("Employee", filters, fields)
        created += 1 if ok else 0
    frappe.db.commit(); summary.append(("Employee", created))

    # 14) Warehouse (company-specific)
    created = 0
    for r in read_csv("warehouses.csv"):
        w = r.get("Warehouse Name")
        if not w: continue
        company = r.get("Company") or COMPANY
        fields = {
            "warehouse_name": w,
            "parent_warehouse": r.get("Parent Warehouse") or "All Warehouses",
            "is_group": to_int(r.get("Is Group")),
            "company": company,
        }
        ok, _ = insert_if_missing("Warehouse", {"warehouse_name": w, "company": company}, fields)
        created += 1 if ok else 0
    frappe.db.commit(); summary.append(("Warehouse", created))

    # 15) Cost Center (company-specific)
    created = 0
    for r in read_csv("cost_centers.csv"):
        cc = r.get("Cost Center Name")
        if not cc: continue
        company = r.get("Company") or COMPANY
        fields = {
            "cost_center_name": cc,
            "parent_cost_center": r.get("Parent Cost Center") or "All Cost Centers",
            "is_group": to_int(r.get("Is Group")),
            "company": company,
        }
        ok, _ = insert_if_missing("Cost Center", {"cost_center_name": cc, "company": company}, fields)
        created += 1 if ok else 0
    frappe.db.commit(); summary.append(("Cost Center", created))

    # 16) Mode of Payment
    created = 0
    for r in read_csv("modes_of_payment.csv"):
        mop = r.get("Mode of Payment")
        if not mop: continue
        fields = {"mode_of_payment": mop, "type": r.get("Type") or "Cash"}
        ok, _ = insert_if_missing("Mode of Payment", {"mode_of_payment": mop}, fields)
        created += 1 if ok else 0
    frappe.db.commit(); summary.append(("Mode of Payment", created))

    # 17) Item
    created = 0
    for r in read_csv("items.csv"):
        code = r.get("Item Code")
        if not code: continue
        fields = {
            "item_code": code,
            "item_name": r.get("Item Name") or code,
            "item_group": r.get("Item Group"),
            "brand": r.get("Brand"),
            "stock_uom": r.get("Stock UOM") or "Nos",
            "is_stock_item": to_int(r.get("Is Stock Item")),
            "has_serial_no": to_int(r.get("Has Serial No")),
        }
        ok, _ = insert_if_missing("Item", {"item_code": code}, fields)
        created += 1 if ok else 0
    frappe.db.commit(); summary.append(("Item", created))

    # 18) Item Price
    created = 0
    for r in read_csv("item_prices.csv"):
        code = r.get("Item Code")
        pl = r.get("Price List")
        if not code or not pl: continue
        fields = {
            "item_code": code,
            "price_list": pl,
            "price_list_rate": to_float(r.get("Price List Rate")),
            "currency": r.get("Currency") or "MMK",
        }
        ok, _ = insert_if_missing("Item Price", {"item_code": code, "price_list": pl}, fields)
        created += 1 if ok else 0
    frappe.db.commit(); summary.append(("Item Price", created))

    log("=== Summary (created records) ===")
    for dt, n in summary:
        log(f"{dt}: {n}")
    log("=== Seed Import DONE ===")

if __name__ == "__main__":
    run()
