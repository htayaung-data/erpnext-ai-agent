import json
import frappe

DOCTYPES = [
    "Branch","Brand","UOM","Item Group","Price List","Territory","Customer Group",
    "Supplier","Customer","Sales Person","Department","Designation","Employee",
    "Warehouse","Cost Center","Mode of Payment","Item","Item Price"
]
OUT = "/tmp/doctype_meta.json"

def field_info(df):
    return {
        "fieldname": df.fieldname,
        "label": df.label,
        "fieldtype": df.fieldtype,
        "reqd": int(df.reqd or 0),
        "options": df.options,
        "default": df.default,
    }

def run():
    out = {}
    for dt in DOCTYPES:
        m = frappe.get_meta(dt)
        fields = [field_info(df) for df in m.fields]
        out[dt] = {
            "autoname": m.autoname,
            "title_field": m.title_field,
            "mandatory_fields": [f for f in fields if f["reqd"]],
            "link_fields": [f for f in fields if f["fieldtype"] == "Link"],
            "select_fields": [f for f in fields if f["fieldtype"] == "Select"],
            "fields": fields,
        }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print("Wrote:", OUT)

if __name__ == "__main__":
    run()
