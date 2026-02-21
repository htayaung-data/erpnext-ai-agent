import json, os
from pathlib import Path

META = Path("impl_factory/04_automation/logs/doctype_meta.json")
OUT_DIR = Path("impl_factory/02_seed_data/_templates")

# These are the doctypes we want templates for (same list you dumped)
DOCTYPES = [
    "Branch","Brand","UOM","Item Group","Price List","Territory","Customer Group",
    "Supplier","Customer","Sales Person","Department","Designation","Employee",
    "Warehouse","Cost Center","Mode of Payment","Item","Item Price"
]

# Prefer these fields early if present (nice UX)
PREFERRED_ORDER = [
    "company", "branch", "department", "designation",
    "warehouse_name", "cost_center_name",
    "customer_name", "customer_group", "territory",
    "supplier_name", "supplier_type",
    "item_code", "item_name", "item_group", "brand", "stock_uom",
    "price_list", "price_list_rate", "currency",
    "sales_person_name", "parent_sales_person", "is_group", "enabled",
]

def main():
    meta = json.loads(META.read_text(encoding="utf-8"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for dt in DOCTYPES:
        m = meta[dt]
        fields = m["fields"]

        # Filter out noisy/internal fields
        skip_types = {"Section Break", "Column Break", "Tab Break", "HTML", "Button", "Fold"}
        usable = [
            f for f in fields
            if f.get("fieldname")
            and f.get("fieldtype") not in skip_types
            and not f["fieldname"].startswith("_")
        ]

        # Put mandatory fields first (keeps it safe)
        mandatory = {f["fieldname"] for f in m.get("mandatory_fields", [])}

        def key(f):
            fn = f["fieldname"]
            pref = PREFERRED_ORDER.index(fn) if fn in PREFERRED_ORDER else 999
            mand = 0 if fn in mandatory else 1
            return (mand, pref, fn)

        cols = [f["fieldname"] for f in sorted(usable, key=key)]

        # Write CSV header
        out = OUT_DIR / f"{dt.replace(' ', '_').lower()}_template.csv"
        out.write_text(",".join(cols) + "\n", encoding="utf-8")
        print(f"Wrote template: {out} ({len(cols)} cols)")

if __name__ == "__main__":
    main()
