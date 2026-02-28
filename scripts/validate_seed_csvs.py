import csv, json, sys
from pathlib import Path

META = Path("impl_factory/04_automation/logs/doctype_meta.json")
SEED = Path("impl_factory/02_seed_data")

DOCTYPES = [
  ("branches.csv", "Branch"),
  ("brands.csv", "Brand"),
  ("uom.csv", "UOM"),
  ("item_groups.csv", "Item Group"),
  ("price_lists.csv", "Price List"),
  ("customer_groups.csv", "Customer Group"),
  ("territories.csv", "Territory"),
  ("departments.csv", "Department"),
  ("designations.csv", "Designation"),
  ("employees.csv", "Employee"),
  ("sales_persons.csv", "Sales Person"),
  ("suppliers.csv", "Supplier"),
  ("customers.csv", "Customer"),
  ("warehouses.csv", "Warehouse"),
  ("cost_centers.csv", "Cost Center"),
  ("modes_of_payment.csv", "Mode of Payment"),
  ("items.csv", "Item"),
  ("item_prices.csv", "Item Price"),
]

def selopts(s):
    return [x.strip() for x in (s or "").split("\n") if x.strip()]

def main():
    meta = json.loads(META.read_text(encoding="utf-8"))
    bad = 0

    for fname, dt in DOCTYPES:
        fpath = SEED / fname
        if not fpath.exists():
            print(f"[MISS] {fname} not found")
            bad += 1
            continue

        fields = meta[dt]["fields"]
        req = [f["fieldname"] for f in fields if f.get("reqd") and f.get("fieldname")]
        selects = {f["fieldname"]: selopts(f.get("options",""))
                   for f in fields if f.get("fieldtype")=="Select" and f.get("fieldname")}

        with fpath.open(newline="", encoding="utf-8") as fp:
            reader = csv.DictReader(fp)
            headers = reader.fieldnames or []
            # check required fields exist in header
            for r in req:
                if r not in headers:
                    print(f"[{dt}] missing REQUIRED column in header: {r}")
                    bad += 1

            # row checks
            for i, row in enumerate(reader, start=2):
                for r in req:
                    if r in headers and not (row.get(r) or "").strip():
                        print(f"[{dt}] row {i}: required field empty: {r}")
                        bad += 1
                for sf, opts in selects.items():
                    v = (row.get(sf) or "").strip()
                    if v and opts and v not in opts:
                        print(f"[{dt}] row {i}: invalid select '{sf}'='{v}' (allowed: {opts})")
                        bad += 1

    if bad:
        print(f"\nFAILED: {bad} issue(s) found.")
        sys.exit(1)
    print("OK: CSVs look consistent with DocType meta (required/select checks passed).")

if __name__ == "__main__":
    main()
