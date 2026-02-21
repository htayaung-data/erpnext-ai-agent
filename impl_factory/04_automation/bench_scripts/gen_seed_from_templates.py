import csv
from pathlib import Path
from datetime import date

BASE = Path("impl_factory")
TEMPL_DIR = BASE / "02_seed_data" / "_templates"
OUT_DIR = BASE / "02_seed_data"

COMPANY = "Mingalar Mobile Distribution Co., Ltd."
CURRENCY = "MMK"

def read_headers(template_name: str):
    p = TEMPL_DIR / template_name
    h = p.read_text(encoding="utf-8-sig").splitlines()[0]
    return [c.strip() for c in h.split(",")]

def write_csv(filename: str, headers, rows):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    p = OUT_DIR / filename
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            out = {h: (r.get(h, "") if r.get(h, "") is not None else "") for h in headers}
            w.writerow(out)
    print("Wrote:", p)

def yn(v: bool): return 1 if v else 0

# -----------------------------
# Seed content (realistic + safe)
# -----------------------------

def branches():
    h = read_headers("branch_template.csv")
    rows = [
        {"branch": "Yangon"},
        {"branch": "Mandalay"},
    ]
    write_csv("branches.csv", h, rows)

def brands():
    h = read_headers("brand_template.csv")
    brand_list = ["Xiaomi","OPPO","Samsung","realme","Baseus","UGREEN","Anker","JBL","TP-Link","Kingston","SanDisk","No Brand"]
    rows = [{"brand": b, "description": ""} for b in brand_list]
    write_csv("brands.csv", h, rows)

def uoms():
    h = read_headers("uom_template.csv")
    rows = [
        {"uom_name":"Nos","enabled":1,"must_be_whole_number":1},
        {"uom_name":"Box","enabled":1,"must_be_whole_number":1},
        {"uom_name":"Pack","enabled":1,"must_be_whole_number":1},
    ]
    write_csv("uom.csv", h, rows)

def item_groups():
    h = read_headers("item_group_template.csv")
    # Keep hierarchy simple but realistic
    rows = [
        {"item_group_name":"All Item Groups","is_group":1,"parent_item_group":""},
        {"item_group_name":"Smartphones","is_group":0,"parent_item_group":"All Item Groups"},
        {"item_group_name":"Routers","is_group":0,"parent_item_group":"All Item Groups"},
        {"item_group_name":"Accessories","is_group":1,"parent_item_group":"All Item Groups"},
        {"item_group_name":"Chargers","is_group":0,"parent_item_group":"Accessories"},
        {"item_group_name":"Cables","is_group":0,"parent_item_group":"Accessories"},
        {"item_group_name":"Earbuds","is_group":0,"parent_item_group":"Accessories"},
        {"item_group_name":"Speakers","is_group":0,"parent_item_group":"Accessories"},
        {"item_group_name":"Power Banks","is_group":0,"parent_item_group":"Accessories"},
        {"item_group_name":"Memory","is_group":1,"parent_item_group":"Accessories"},
        {"item_group_name":"Memory Cards","is_group":0,"parent_item_group":"Memory"},
        {"item_group_name":"USB Flash","is_group":0,"parent_item_group":"Memory"},
        {"item_group_name":"Phone Cases","is_group":0,"parent_item_group":"Accessories"},
        {"item_group_name":"Spare Parts","is_group":1,"parent_item_group":"All Item Groups"},
        {"item_group_name":"Battery","is_group":0,"parent_item_group":"Spare Parts"},
        {"item_group_name":"LCD","is_group":0,"parent_item_group":"Spare Parts"},
    ]
    write_csv("item_groups.csv", h, rows)

def price_lists():
    h = read_headers("price_list_template.csv")
    rows = [
        {"price_list_name":"Retail","currency":CURRENCY,"enabled":1,"selling":1,"buying":0,"price_not_uom_dependent":1},
        {"price_list_name":"Wholesale","currency":CURRENCY,"enabled":1,"selling":1,"buying":0,"price_not_uom_dependent":1},
        {"price_list_name":"Buying","currency":CURRENCY,"enabled":1,"selling":0,"buying":1,"price_not_uom_dependent":1},
    ]
    write_csv("price_lists.csv", h, rows)

def territories():
    h = read_headers("territory_template.csv")
    rows = [
        {"territory_name":"Myanmar","is_group":1,"parent_territory":""},
        {"territory_name":"Yangon","is_group":0,"parent_territory":"Myanmar"},
        {"territory_name":"Mandalay","is_group":0,"parent_territory":"Myanmar"},
        {"territory_name":"Bago","is_group":0,"parent_territory":"Myanmar"},
        {"territory_name":"Taunggyi","is_group":0,"parent_territory":"Myanmar"},
    ]
    write_csv("territories.csv", h, rows)

def customer_groups():
    h = read_headers("customer_group_template.csv")
    rows = [
        {"customer_group_name":"All Customer Groups","is_group":1,"parent_customer_group":""},
        {"customer_group_name":"Wholesale","is_group":0,"parent_customer_group":"All Customer Groups","default_price_list":"Wholesale"},
        {"customer_group_name":"Retail","is_group":0,"parent_customer_group":"All Customer Groups","default_price_list":"Retail"},
    ]
    write_csv("customer_groups.csv", h, rows)

def suppliers():
    h = read_headers("supplier_template.csv")
    rows = [
        {"supplier_name":"Golden Dragon Trading Co Ltd","supplier_type":"Company","country":"Myanmar","mobile_no":"09421004567","default_currency":CURRENCY},
        {"supplier_name":"Shwe Taung Electronics Supply","supplier_type":"Company","country":"Myanmar","mobile_no":"09447001123","default_currency":CURRENCY},
        {"supplier_name":"Myanmar Tech Import Services","supplier_type":"Company","country":"Myanmar","mobile_no":"09425009988","default_currency":CURRENCY},
        {"supplier_name":"Mandalay Device Wholesale","supplier_type":"Company","country":"Myanmar","mobile_no":"09444488012","default_currency":CURRENCY},
        {"supplier_name":"Asia Connect Logistics And Customs","supplier_type":"Company","country":"Myanmar","mobile_no":"09431120456","default_currency":CURRENCY},
        {"supplier_name":"Sunrise Mobile Accessories Co Ltd","supplier_type":"Company","country":"Myanmar","mobile_no":"09426677110","default_currency":CURRENCY},
        {"supplier_name":"Royal Gadget Importers","supplier_type":"Company","country":"Myanmar","mobile_no":"09450911662","default_currency":CURRENCY},
        {"supplier_name":"Maha Aung Myay Spare Parts Hub","supplier_type":"Company","country":"Myanmar","mobile_no":"09444412090","default_currency":CURRENCY},
    ]
    write_csv("suppliers.csv", h, rows)

def sales_persons():
    h = read_headers("sales_person_template.csv")
    # Root + groups + reps (realistic)
    rows = [
        {"sales_person_name":"Mingalar Mobile Sales Team","is_group":1,"enabled":1,"parent_sales_person":"","department":"Sales"},
        {"sales_person_name":"Yangon Sales","is_group":1,"enabled":1,"parent_sales_person":"Mingalar Mobile Sales Team","department":"Sales"},
        {"sales_person_name":"Mandalay Sales","is_group":1,"enabled":1,"parent_sales_person":"Mingalar Mobile Sales Team","department":"Sales"},
        {"sales_person_name":"YGN-SP-01 Aung Ko Ko","is_group":0,"enabled":1,"parent_sales_person":"Yangon Sales","department":"Sales"},
        {"sales_person_name":"YGN-SP-02 Htet Naing","is_group":0,"enabled":1,"parent_sales_person":"Yangon Sales","department":"Sales"},
        {"sales_person_name":"YGN-SP-03 Thura Win","is_group":0,"enabled":1,"parent_sales_person":"Yangon Sales","department":"Sales"},
        {"sales_person_name":"YGN-SP-04 May Myint","is_group":0,"enabled":1,"parent_sales_person":"Yangon Sales","department":"Sales"},
        {"sales_person_name":"MDY-SP-01 Su Su Win","is_group":0,"enabled":1,"parent_sales_person":"Mandalay Sales","department":"Sales"},
        {"sales_person_name":"MDY-SP-02 Nay Lin","is_group":0,"enabled":1,"parent_sales_person":"Mandalay Sales","department":"Sales"},
        {"sales_person_name":"MDY-SP-03 Hnin Ei","is_group":0,"enabled":1,"parent_sales_person":"Mandalay Sales","department":"Sales"},
    ]
    write_csv("sales_persons.csv", h, rows)

def departments():
    h = read_headers("department_template.csv")
    rows = [
        {"company":COMPANY, "department_name":"Sales","is_group":0,"disabled":0},
        {"company":COMPANY, "department_name":"Warehouse","is_group":0,"disabled":0},
        {"company":COMPANY, "department_name":"Purchasing","is_group":0,"disabled":0},
        {"company":COMPANY, "department_name":"Accounts","is_group":0,"disabled":0},
        {"company":COMPANY, "department_name":"HR/Admin","is_group":0,"disabled":0},
        {"company":COMPANY, "department_name":"Delivery/Logistics","is_group":0,"disabled":0},
        {"company":COMPANY, "department_name":"IT","is_group":0,"disabled":0},
    ]
    write_csv("departments.csv", h, rows)

def designations():
    h = read_headers("designation_template.csv")
    rows = [{"designation_name": n} for n in [
        "General Manager","Sales Supervisor","Sales Executive",
        "Warehouse Supervisor","Storekeeper","Purchasing Officer",
        "Accountant","Cashier","HR/Admin Officer","Delivery Driver","IT Officer"
    ]]
    write_csv("designations.csv", h, rows)

def warehouses():
    h = read_headers("warehouse_template.csv")
    rows = [
        {"company":COMPANY,"warehouse_name":"YGN-Main Warehouse","is_group":0,"city":"Yangon","parent_warehouse":""},
        {"company":COMPANY,"warehouse_name":"YGN-Showroom Counter","is_group":0,"city":"Yangon","parent_warehouse":""},
        {"company":COMPANY,"warehouse_name":"MDY-Branch Warehouse","is_group":0,"city":"Mandalay","parent_warehouse":""},
        {"company":COMPANY,"warehouse_name":"In-Transit Warehouse","is_group":0,"city":"Yangon","parent_warehouse":"","default_in_transit_warehouse":""},
        {"company":COMPANY,"warehouse_name":"Returns And Damaged Warehouse","is_group":0,"city":"Yangon","parent_warehouse":"","is_rejected_warehouse":1},
    ]
    write_csv("warehouses.csv", h, rows)

def cost_centers():
    h = read_headers("cost_center_template.csv")
    # Parent CC must exist and is required by template/meta
    rows = [
        {"company":COMPANY,"cost_center_name":"Mingalar Mobile","parent_cost_center":"All Cost Centers","is_group":1,"disabled":0},
        {"company":COMPANY,"cost_center_name":"Yangon","parent_cost_center":"Mingalar Mobile","is_group":0,"disabled":0},
        {"company":COMPANY,"cost_center_name":"Mandalay","parent_cost_center":"Mingalar Mobile","is_group":0,"disabled":0},
    ]
    write_csv("cost_centers.csv", h, rows)

def modes_of_payment():
    h = read_headers("mode_of_payment_template.csv")
    rows = [
        {"mode_of_payment":"Cash","enabled":1,"type":"Cash"},
        {"mode_of_payment":"Bank Transfer","enabled":1,"type":"Bank"},
        {"mode_of_payment":"KBZPay","enabled":1,"type":"Phone"},
        {"mode_of_payment":"WavePay","enabled":1,"type":"Phone"},
    ]
    write_csv("modes_of_payment.csv", h, rows)

def customers():
    h = read_headers("customer_template.csv")
    # 18 B2B + 2 walk-in (Retail)
    rows = [
        {"customer_name":"Shwe Pyi Mobile And Accessories","customer_type":"Company","customer_group":"Wholesale","territory":"Yangon","mobile_no":"09420173456","default_price_list":"Wholesale"},
        {"customer_name":"Ko Nay Lin Mobile Center","customer_type":"Company","customer_group":"Wholesale","territory":"Mandalay","mobile_no":"09450988211","default_price_list":"Wholesale"},
        {"customer_name":"Thiri Mingalar Phone Shop","customer_type":"Company","customer_group":"Wholesale","territory":"Bago","mobile_no":"09444123987","default_price_list":"Wholesale"},
        {"customer_name":"Taunggyi Star Mobile","customer_type":"Company","customer_group":"Wholesale","territory":"Taunggyi","mobile_no":"09425977120","default_price_list":"Wholesale"},
        {"customer_name":"Aung Yadanar Mobile","customer_type":"Company","customer_group":"Wholesale","territory":"Yangon","mobile_no":"09420011002","default_price_list":"Wholesale"},
        {"customer_name":"Hledan Mobile Hub","customer_type":"Company","customer_group":"Wholesale","territory":"Yangon","mobile_no":"09420011003","default_price_list":"Wholesale"},
        {"customer_name":"Maha Bandoola Phone Shop","customer_type":"Company","customer_group":"Wholesale","territory":"Yangon","mobile_no":"09420011004","default_price_list":"Wholesale"},
        {"customer_name":"Chan Mya Tharzi Mobile","customer_type":"Company","customer_group":"Wholesale","territory":"Mandalay","mobile_no":"09444477001","default_price_list":"Wholesale"},
        {"customer_name":"Pyigyitagon Accessories","customer_type":"Company","customer_group":"Wholesale","territory":"Mandalay","mobile_no":"09444477002","default_price_list":"Wholesale"},
        {"customer_name":"Bago Central Mobile","customer_type":"Company","customer_group":"Wholesale","territory":"Bago","mobile_no":"09450022001","default_price_list":"Wholesale"},
        {"customer_name":"Hpa An Mobile Market","customer_type":"Company","customer_group":"Wholesale","territory":"Myanmar","mobile_no":"09450022002","default_price_list":"Wholesale"},
        {"customer_name":"North Okkalapa Phone Shop","customer_type":"Company","customer_group":"Wholesale","territory":"Yangon","mobile_no":"09450022003","default_price_list":"Wholesale"},
        {"customer_name":"South Dagon Mobile","customer_type":"Company","customer_group":"Wholesale","territory":"Yangon","mobile_no":"09450022004","default_price_list":"Wholesale"},
        {"customer_name":"Mingaladon Mobile Center","customer_type":"Company","customer_group":"Wholesale","territory":"Yangon","mobile_no":"09450022005","default_price_list":"Wholesale"},
        {"customer_name":"Amarapura Phone Shop","customer_type":"Company","customer_group":"Wholesale","territory":"Mandalay","mobile_no":"09444477003","default_price_list":"Wholesale"},
        {"customer_name":"Meiktila Mobile Shop","customer_type":"Company","customer_group":"Wholesale","territory":"Myanmar","mobile_no":"09444477004","default_price_list":"Wholesale"},
        {"customer_name":"Kyaukse Phone Accessories","customer_type":"Company","customer_group":"Wholesale","territory":"Myanmar","mobile_no":"09444477005","default_price_list":"Wholesale"},
        {"customer_name":"Daw Hnin Ei Walk In","customer_type":"Individual","customer_group":"Retail","territory":"Yangon","mobile_no":"09430066215","default_price_list":"Retail"},
        {"customer_name":"Walk In Customer","customer_type":"Individual","customer_group":"Retail","territory":"Yangon","mobile_no":"","default_price_list":"Retail"},
    ]
    write_csv("customers.csv", h, rows)

def employees():
    h = read_headers("employee_template.csv")
    # ERP requires DOB + DOJ + status + company + first_name + gender + naming_series
    # Use realistic DOB/DOJ (no sensitive real persons - just plausible Burmese names)
    rows = [
        {"company":COMPANY,"naming_series":"HR-EMP-","first_name":"Kyaw Min Oo","gender":"Male","date_of_birth":"1987-06-12","date_of_joining":"2022-04-01","status":"Active","branch":"Yangon","department":"Sales","designation":"General Manager"},
        {"company":COMPANY,"naming_series":"HR-EMP-","first_name":"Thandar Hlaing","gender":"Female","date_of_birth":"1992-02-18","date_of_joining":"2021-08-01","status":"Active","branch":"Yangon","department":"Accounts","designation":"Accountant"},
        {"company":COMPANY,"naming_series":"HR-EMP-","first_name":"Aung Ko Ko","gender":"Male","date_of_birth":"1990-10-05","date_of_joining":"2020-06-15","status":"Active","branch":"Yangon","department":"Sales","designation":"Sales Supervisor"},
        {"company":COMPANY,"naming_series":"HR-EMP-","first_name":"Su Su Win","gender":"Female","date_of_birth":"1997-03-11","date_of_joining":"2023-01-10","status":"Active","branch":"Mandalay","department":"Sales","designation":"Sales Executive"},
        {"company":COMPANY,"naming_series":"HR-EMP-","first_name":"Zaw Lin","gender":"Male","date_of_birth":"1991-12-22","date_of_joining":"2020-09-01","status":"Active","branch":"Yangon","department":"Warehouse","designation":"Warehouse Supervisor"},
        {"company":COMPANY,"naming_series":"HR-EMP-","first_name":"Min Thu","gender":"Male","date_of_birth":"1998-08-09","date_of_joining":"2023-05-01","status":"Active","branch":"Mandalay","department":"Warehouse","designation":"Storekeeper"},
        {"company":COMPANY,"naming_series":"HR-EMP-","first_name":"Hnin Pwint","gender":"Female","date_of_birth":"1995-05-27","date_of_joining":"2022-11-01","status":"Active","branch":"Yangon","department":"Purchasing","designation":"Purchasing Officer"},
        {"company":COMPANY,"naming_series":"HR-EMP-","first_name":"Ye Htut Naing","gender":"Male","date_of_birth":"1999-01-19","date_of_joining":"2023-07-01","status":"Active","branch":"Yangon","department":"Delivery/Logistics","designation":"Delivery Driver"},

        # Add more realistic headcount coverage
        {"company":COMPANY,"naming_series":"HR-EMP-","first_name":"Htet Naing","gender":"Male","date_of_birth":"1996-09-14","date_of_joining":"2022-02-01","status":"Active","branch":"Yangon","department":"Sales","designation":"Sales Executive"},
        {"company":COMPANY,"naming_series":"HR-EMP-","first_name":"Thura Win","gender":"Male","date_of_birth":"1994-04-03","date_of_joining":"2021-12-01","status":"Active","branch":"Yangon","department":"Sales","designation":"Sales Executive"},
        {"company":COMPANY,"naming_series":"HR-EMP-","first_name":"May Myint","gender":"Female","date_of_birth":"1998-11-08","date_of_joining":"2023-02-15","status":"Active","branch":"Yangon","department":"Sales","designation":"Sales Executive"},
        {"company":COMPANY,"naming_series":"HR-EMP-","first_name":"Nay Lin","gender":"Male","date_of_birth":"1993-07-30","date_of_joining":"2021-03-01","status":"Active","branch":"Mandalay","department":"Sales","designation":"Sales Executive"},
        {"company":COMPANY,"naming_series":"HR-EMP-","first_name":"Hnin Ei","gender":"Female","date_of_birth":"1997-12-02","date_of_joining":"2022-09-01","status":"Active","branch":"Mandalay","department":"Sales","designation":"Sales Executive"},
        {"company":COMPANY,"naming_series":"HR-EMP-","first_name":"Aye Chan","gender":"Male","date_of_birth":"1990-05-10","date_of_joining":"2020-01-05","status":"Active","branch":"Yangon","department":"Accounts","designation":"Cashier"},
        {"company":COMPANY,"naming_series":"HR-EMP-","first_name":"Ei Mon","gender":"Female","date_of_birth":"1996-02-25","date_of_joining":"2022-06-01","status":"Active","branch":"Yangon","department":"HR/Admin","designation":"HR/Admin Officer"},
        {"company":COMPANY,"naming_series":"HR-EMP-","first_name":"Ko Ko Lin","gender":"Male","date_of_birth":"1995-10-21","date_of_joining":"2021-05-01","status":"Active","branch":"Yangon","department":"IT","designation":"IT Officer"},
    ]
    write_csv("employees.csv", h, rows)

def items_and_prices():
    item_h = read_headers("item_template.csv")
    price_h = read_headers("item_price_template.csv")

    # Core items (your provided 15) + 8 more realistic fast movers
    items = [
        ("PH-XMI-RN13-8-256","Smartphones","Nos","Xiaomi Redmi Note 13 8GB 256GB","Xiaomi",1),
        ("PH-OPP-A58-6-128","Smartphones","Nos","OPPO A58 6GB 128GB","OPPO",1),
        ("PH-SSG-A15-6-128","Smartphones","Nos","Samsung Galaxy A15 6GB 128GB","Samsung",1),
        ("PH-RLM-C55-8-256","Smartphones","Nos","realme C55 8GB 256GB","realme",1),
        ("ACC-CHR-20W-USBC","Chargers","Nos","20W USB-C Fast Charger","Baseus",0),
        ("ACC-CBL-UGR-TC1M","Cables","Nos","Type-C Cable 1m Fast Charge","UGREEN",0),
        ("ACC-PWB-ANK-10K","Power Banks","Nos","Power Bank 10000mAh","Anker",0),
        ("ACC-EAR-RDM-BUDS4","Earbuds","Nos","Redmi Buds TWS Earbuds","Xiaomi",0),
        ("ACC-SPK-JBL-GO3","Speakers","Nos","Bluetooth Speaker GO3","JBL",0),
        ("NET-RTR-TPA-C6","Routers","Nos","Wi-Fi Router Archer C6","TP-Link",1),
        ("MEM-MSD-KNG-64","Memory Cards","Nos","MicroSD Card 64GB","Kingston",0),
        ("MEM-USB-SND-64","USB Flash","Nos","USB Flash Drive 64GB","SanDisk",0),
        ("ACC-CAS-TPU-RN13","Phone Cases","Nos","TPU Case Redmi Note 13","No Brand",0),
        ("SP-BAT-IP11","Battery","Nos","Replacement Battery iPhone 11","No Brand",0),
        ("SP-LCD-RN13","LCD","Nos","LCD Screen Redmi Note 13","No Brand",0),

        ("ACC-SCR-GLS-6D","Accessories","Nos","6D Screen Protector Glass","No Brand",0),
        ("ACC-CHR-33W-USBC","Chargers","Nos","33W Fast Charger USB-C","Baseus",0),
        ("ACC-CBL-LTG-1M","Cables","Nos","Lightning Cable 1m","No Brand",0),
        ("ACC-HDP-3P5","Accessories","Nos","3.5mm Headphone Adapter","No Brand",0),
        ("SP-BAT-RN13","Battery","Nos","Replacement Battery Redmi Note 13","No Brand",0),
        ("SP-LCD-IP11","LCD","Nos","LCD Screen iPhone 11","No Brand",0),
        ("ACC-PWB-20K","Power Banks","Nos","Power Bank 20000mAh","Anker",0),
        ("NET-RTR-4G","Routers","Nos","4G LTE Router","TP-Link",1),
    ]

    # Prices (Retail selling, Buying, Wholesale selling)
    retail = {
        "PH-XMI-RN13-8-256": 865000,
        "PH-OPP-A58-6-128": 795000,
        "PH-SSG-A15-6-128": 920000,
        "PH-RLM-C55-8-256": 835000,
        "ACC-CHR-20W-USBC": 22000,
        "ACC-CBL-UGR-TC1M": 9000,
        "ACC-PWB-ANK-10K": 78000,
        "ACC-EAR-RDM-BUDS4": 52000,
        "ACC-SPK-JBL-GO3": 118000,
        "NET-RTR-TPA-C6": 98000,
        "MEM-MSD-KNG-64": 13500,
        "MEM-USB-SND-64": 16000,
        "ACC-CAS-TPU-RN13": 6000,
        "SP-BAT-IP11": 42000,
        "SP-LCD-RN13": 165000,

        "ACC-SCR-GLS-6D": 4500,
        "ACC-CHR-33W-USBC": 32000,
        "ACC-CBL-LTG-1M": 9500,
        "ACC-HDP-3P5": 8500,
        "SP-BAT-RN13": 38000,
        "SP-LCD-IP11": 175000,
        "ACC-PWB-20K": 125000,
        "NET-RTR-4G": 135000,
    }
    buying = {
        "PH-XMI-RN13-8-256": 820000,
        "PH-OPP-A58-6-128": 755000,
        "PH-SSG-A15-6-128": 875000,
        "PH-RLM-C55-8-256": 790000,
        "ACC-CHR-20W-USBC": 17500,
        "ACC-CBL-UGR-TC1M": 6500,
        "ACC-PWB-ANK-10K": 68000,
        "ACC-EAR-RDM-BUDS4": 44500,
        "ACC-SPK-JBL-GO3": 103000,
        "NET-RTR-TPA-C6": 86000,
        "MEM-MSD-KNG-64": 10500,
        "MEM-USB-SND-64": 13000,
        "ACC-CAS-TPU-RN13": 3500,
        "SP-BAT-IP11": 32000,
        "SP-LCD-RN13": 145000,

        "ACC-SCR-GLS-6D": 2800,
        "ACC-CHR-33W-USBC": 25000,
        "ACC-CBL-LTG-1M": 6800,
        "ACC-HDP-3P5": 6000,
        "SP-BAT-RN13": 28000,
        "SP-LCD-IP11": 155000,
        "ACC-PWB-20K": 108000,
        "NET-RTR-4G": 118000,
    }

    def wholesale_price(code):
        r = retail[code]
        # phones/routers: small spread, accessories/spares: larger
        if code.startswith("PH-") or code.startswith("NET-"):
            return int(round(r * 0.97))
        return int(round(r * 0.92))

    # Items CSV
    item_rows = []
    for code, grp, uom, name, brand, serial in items:
        item_rows.append({
            "item_code": code,
            "item_group": grp,
            "stock_uom": uom,
            "item_name": name,
            "brand": brand,
            "is_sales_item": 1,
            "is_purchase_item": 1,
            "is_stock_item": 1,
            "has_serial_no": 1 if serial else 0,
            "valuation_method": "Moving Average",
        })
    write_csv("items.csv", item_h, item_rows)

    # Item Price CSV: 3 price lists per item (Retail/Wholesale/Buying)
    price_rows = []
    for code, grp, uom, name, brand, serial in items:
        price_rows.append({"item_code": code, "uom": uom, "price_list": "Retail", "price_list_rate": retail[code], "currency": CURRENCY, "brand": brand, "selling": 1})
        price_rows.append({"item_code": code, "uom": uom, "price_list": "Wholesale", "price_list_rate": wholesale_price(code), "currency": CURRENCY, "brand": brand, "selling": 1})
        price_rows.append({"item_code": code, "uom": uom, "price_list": "Buying", "price_list_rate": buying[code], "currency": CURRENCY, "buying": 1})
    write_csv("item_prices.csv", price_h, price_rows)

def main():
    # Ensure output dir exists
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    branches()
    brands()
    uoms()
    item_groups()
    price_lists()
    territories()
    customer_groups()
    suppliers()

    # NOTE: Sales Person links to Department -> create Department before Sales Person if using scripted inserts.
    departments()
    designations()

    # Warehouses/Cost Centers require Company; still generate CSV now, import after company exists.
    warehouses()
    cost_centers()

    modes_of_payment()
    customers()
    employees()
    sales_persons()
    items_and_prices()

    print("\nDONE: Seed CSVs regenerated 100% aligned with templates.")

if __name__ == "__main__":
    main()
