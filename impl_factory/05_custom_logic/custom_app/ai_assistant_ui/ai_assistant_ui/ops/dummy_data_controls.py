from __future__ import annotations

import math
from typing import Any

import frappe
from erpnext.selling.doctype.customer.customer import get_customer_outstanding


COMPANY_NAME = "Mingalar Mobile Distribution Co., Ltd."
MMK_CREDIT_ROUNDING_UNIT = 5_000_000
PILOT_PRICE_REFERENCE = "Mini-Phase 1D Pilot Price"
MINIPHASE_1E_RETAIL_SALE_LABEL = "Mini-Phase 1E Pilot Retail Counter Sale"
MINIPHASE_1E_WHOLESALE_CREDIT_SALE_LABEL = "Mini-Phase 1E Pilot Wholesale Credit Sale"
MINIPHASE_1E_ACCESSORIES_PURCHASE_LABEL = "Mini-Phase 1E Pilot Accessories Purchase"
MINIPHASE_1F_SUPPLIER_PAYMENT_LABEL = "Mini-Phase 1F Pilot Partial Supplier Payment"
MINIPHASE_1F_CUSTOMER_COLLECTION_LABEL = "Mini-Phase 1F Pilot Partial Customer Collection"
MINIPHASE_1F_SALES_RETURN_LABEL = "Mini-Phase 1F Pilot Wholesale Accessory Sales Return"
MINIPHASE_2A_ADDITIONAL_WHOLESALE_SALE_LABEL = "Mini-Phase 2A Mandalay Wholesale Top-Up Sale"
MINIPHASE_2B_BRANCH_TRANSFER_LABEL = "Mini-Phase 2B Transit To Mandalay Router Release"
MINIPHASE_2C_AGED_COLLECTION_LABEL = "Mini-Phase 2C 35th Street Aged AR Collection"
MINIPHASE_2D_IMPORTER_AP_PAYMENT_LABEL = "Mini-Phase 2D Myanmar Tech Importer AP Payment"
MINIPHASE_2E_PURCHASE_RETURN_LABEL = "Mini-Phase 2E Sunflower Power Bank Purchase Return"
MINIPHASE_2F_REPLACEMENT_RECEIPT_LABEL = "Mini-Phase 2F Sunflower Power Bank Replacement Receipt"
MINIPHASE_3A_SHOWROOM_TOPUP_LABEL = "Mini-Phase 3A Yangon Showroom Xiaomi Top-Up"
MINIPHASE_3B_SHOWROOM_SALE_LABEL = "Mini-Phase 3B Hledan Showroom Xiaomi KBZ Pay Sale"
MINIPHASE_3C_STALE_SHOWROOM_ORDER_CANCEL_LABEL = "Mini-Phase 3C Hledan Stale Showroom Order Release"
MINIPHASE_3D_STALE_SHOWROOM_ORDER_CANCEL_LABEL = "Mini-Phase 3D City Mobile Mart Stale Showroom Order Release"
MINIPHASE_3E_STALE_SHOWROOM_ORDER_CANCEL_LABEL = "Mini-Phase 3E Pazundaung Expired Showroom Order Release"
MINIPHASE_3F_STALE_SHOWROOM_ORDER_CANCEL_LABEL = "Mini-Phase 3F Lanmadaw Legacy Showroom Order Release"
MINIPHASE_4B_CAPITAL_NPT_AGED_COLLECTION_LABEL = "Mini-Phase 4B Capital Telecom Aged AR Collection"
MINIPHASE_4C_GOLDEN_DRAGON_AGED_AP_PAYMENT_LABEL = "Mini-Phase 4C Golden Dragon Aged AP Payment"
MINIPHASE_4E_TRANSIT_ROUTER_CONTINUITY_RELEASE_LABEL = "Mini-Phase 4E Transit Router Continuity Release"
MINIPHASE_4E_LEGACY_KINGSTON_MEMORY_RELEASE_LABEL = "Mini-Phase 4E Legacy Kingston Memory Transit Release"
MINIPHASE_4F_DEFECTIVE_EARBUDS_QUARANTINE_LABEL = "Mini-Phase 4F Defective Earbuds Quarantine Transfer"
MINIPHASE_4G_CAPITAL_KEY_ACCOUNT_SALE_LABEL = "Mini-Phase 4G Capital Telecom Late-April Replenishment"
MINIPHASE_4G_BAYINT_MONTH_END_COLLECTION_LABEL = "Mini-Phase 4G Bayint Month-End Collection"
MINIPHASE_4G_MYANMAR_TECH_REALME_PO_LABEL = "Mini-Phase 4G Myanmar Tech Realme Replenishment PO"
MINIPHASE_5A_HLEDAN_CATCHUP_BILLING_LABEL = "Mini-Phase 5A Hledan Delivered Power Bank Catch-Up Billing"
MINIPHASE_5B_HLEDAN_MICROSD_CATCHUP_BILLING_LABEL = "Mini-Phase 5B Hledan Delivered MicroSD Catch-Up Billing"
MINIPHASE_6A_KO_NAY_LIN_AGED_COLLECTION_LABEL = "Mini-Phase 6A Ko Nay Lin Aged AR Collection"
MINIPHASE_6B_MYANMAR_TECH_FOLLOWON_AP_PAYMENT_LABEL = "Mini-Phase 6B Myanmar Tech Follow-On AP Payment"
MINIPHASE_6C_MANDALAY_DEVICE_FOLLOWON_AP_PAYMENT_LABEL = "Mini-Phase 6C Mandalay Device Follow-On AP Payment"
MINIPHASE_6E_35TH_STREET_FOLLOWON_COLLECTION_LABEL = "Mini-Phase 6E 35th Street Follow-On AR Collection"
MINIPHASE_6G_ASIA_CONNECT_FOLLOWON_AP_PAYMENT_LABEL = "Mini-Phase 6G Asia Connect Follow-On AP Payment"
MINIPHASE_6I_SHWE_TAUNG_FOLLOWON_AP_PAYMENT_LABEL = "Mini-Phase 6I Shwe Taung Follow-On AP Payment"
MINIPHASE_6K_CAPITAL_FOLLOWON_COLLECTION_LABEL = "Mini-Phase 6K Capital Telecom Follow-On AR Collection"
MINIPHASE_6M_GOLDEN_DRAGON_FOLLOWON_AP_PAYMENT_LABEL = "Mini-Phase 6M Golden Dragon Follow-On AP Payment"
MINIPHASE_7F_CHAN_AYE_FOLLOWON_COLLECTION_LABEL = "Mini-Phase 7F Chan Aye Follow-On Collection"
MINIPHASE_7G_HLEDAN_FOLLOWON_COLLECTION_LABEL = "Mini-Phase 7G Hledan Follow-On Collection"
MINIPHASE_7I_KO_NAY_LIN_MANDALAY_TOPUP_LABEL = "Mini-Phase 7I Ko Nay Lin Mandalay Wholesale Top-Up"
PARALLEL_SALES_CONSOLE_QUOTATION_APPROVAL_DEMO_LABEL = "Parallel Sales Console Quotation Approval Demo Rollout"
PARALLEL_SALES_CONSOLE_SALES_ORDER_APPROVAL_DEMO_LABEL = "Parallel Sales Console Sales Order Approval Demo Rollout"
MINIPHASE_6O_SUPPLIER_POLICY_DEFAULTS_LABEL = "Mini-Phase 6O Supplier Policy Defaults Rollout"
MINIPHASE_6Q_PARTIAL_TRANSIT_GADGET_RELEASE_LABEL = "Mini-Phase 6Q Partial Transit Small Gadget Release"
MINIPHASE_6T_MYANMAR_TECH_BALANCE_RECEIPT_LABEL = "Mini-Phase 6T Myanmar Tech Balance Import Receipt"
MINIPHASE_4D_STALE_WHOLESALE_ORDER_CANCEL_LABEL = "Mini-Phase 4D Shwe Li Stale Wholesale Order Release"
MINIPHASE_4D_MANDALAY_STALE_WHOLESALE_ORDER_CANCEL_LABEL = "Mini-Phase 4D Mandalay Mobile Hub Stale Wholesale Order Release"
MINIPHASE_4D_LATHA_STALE_WHOLESALE_ORDER_CANCEL_LABEL = "Mini-Phase 4D Latha Stale Wholesale Order Release"
MINIPHASE_4D_AMARAPURA_STALE_RETAIL_ORDER_CANCEL_LABEL = "Mini-Phase 4D Amarapura Stale Retail Order Release"
MINIPHASE_4D_MANDALAY_ACCESSORIES_STALE_WHOLESALE_ORDER_CANCEL_LABEL = "Mini-Phase 4D Mandalay Accessories Stale Wholesale Order Release"
MINIPHASE_4D_ZEGYO_MARKET_STALE_RETAIL_ORDER_CANCEL_LABEL = "Mini-Phase 4D Zegyo Market Stale Retail Order Release"
WHOLESALE_CUSTOMER_CREDIT_LIMIT_ROLLOUT_LABEL = "Parallel Wholesale Customer Credit Limit Rollout"
WHOLESALE_CUSTOMER_POLICY_DEFAULTS_LABEL = "Parallel Wholesale Customer Policy Defaults Rollout"
MINIPHASE_7J_ACTIVE_RETAIL_POLICY_DEFAULTS_LABEL = "Mini-Phase 7J Active Retail Customer Policy Defaults Rollout"

MINIPHASE_1C_PILOT_CREDIT_LIMITS = (
	{
		"customer": "35th Street Mobile Wholesale",
		"target_credit_limit": 45_000_000,
		"bypass_credit_limit_check": 0,
	},
	{
		"customer": "Bayint Naung Wholesale Mobile",
		"target_credit_limit": 40_000_000,
		"bypass_credit_limit_check": 0,
	},
	{
		"customer": "Capital Telecom (NPT)",
		"target_credit_limit": 35_000_000,
		"bypass_credit_limit_check": 0,
	},
)

MINIPHASE_1D_PILOT_ITEM_PRICES = (
	{
		"item_code": "SPH-APP-IP14-128",
		"uom": "Nos",
		"prices": {
			"Standard Buying - MMOB": 2_350_000,
			"Retail Selling - MMOB": 2_500_000,
			"Wholesale Selling - MMOB": 2_460_000,
			"Key Account Selling - MMOB": 2_420_000,
		},
	},
	{
		"item_code": "SPH-XMI-RN13-8/256",
		"uom": "Nos",
		"prices": {
			"Standard Buying - MMOB": 820_000,
			"Retail Selling - MMOB": 960_000,
			"Wholesale Selling - MMOB": 940_000,
			"Key Account Selling - MMOB": 930_000,
		},
	},
	{
		"item_code": "SPH-SAM-A15-6/128",
		"uom": "Nos",
		"prices": {
			"Standard Buying - MMOB": 875_000,
			"Retail Selling - MMOB": 920_000,
			"Wholesale Selling - MMOB": 900_000,
			"Key Account Selling - MMOB": 890_000,
		},
	},
	{
		"item_code": "ACC-PWB-BAS-20K",
		"uom": "Nos",
		"prices": {
			"Standard Buying - MMOB": 82_000,
			"Retail Selling - MMOB": 95_000,
			"Wholesale Selling - MMOB": 90_000,
			"Key Account Selling - MMOB": 88_000,
		},
	},
	{
		"item_code": "ACC-CBL-BAS-TC1M",
		"uom": "Nos",
		"prices": {
			"Standard Buying - MMOB": 5_500,
			"Retail Selling - MMOB": 8_000,
			"Wholesale Selling - MMOB": 7_500,
			"Key Account Selling - MMOB": 7_000,
		},
	},
	{
		"item_code": "ACC-CHR-XMI-33W",
		"uom": "Nos",
		"prices": {
			"Standard Buying - MMOB": 23_000,
			"Retail Selling - MMOB": 28_000,
			"Wholesale Selling - MMOB": 26_000,
			"Key Account Selling - MMOB": 25_000,
		},
	},
	{
		"item_code": "NET-RTR-TPL-C54",
		"uom": "Nos",
		"prices": {
			"Standard Buying - MMOB": 62_000,
			"Retail Selling - MMOB": 72_000,
			"Wholesale Selling - MMOB": 68_000,
			"Key Account Selling - MMOB": 66_000,
		},
	},
)

MINIPHASE_1E_RETAIL_COUNTER_SALE = {
	"sales_order": {
		"naming_series": "SAL-ORD-.YYYY.-",
		"customer": "City Mobile Mart",
		"company": COMPANY_NAME,
		"transaction_date": "2026-04-05",
		"delivery_date": "2026-04-05",
		"po_no": "PILOT-CTR-0405-01",
		"po_date": "2026-04-05",
		"currency": "MMK",
		"conversion_rate": 1.0,
		"selling_price_list": "Retail Selling - MMOB",
		"price_list_currency": "MMK",
		"plc_conversion_rate": 1.0,
		"payment_terms_template": "Immediate / Counter Cash - MMOB",
		"set_warehouse": "Yangon Showroom Counter - MMOB",
		"items": (
			{
				"item_code": "SPH-APP-IP14-128",
				"qty": 1,
				"warehouse": "Yangon Showroom Counter - MMOB",
				"delivery_date": "2026-04-05",
			},
			{
				"item_code": "ACC-PWB-BAS-20K",
				"qty": 1,
				"warehouse": "Yangon Showroom Counter - MMOB",
				"delivery_date": "2026-04-05",
			},
			{
				"item_code": "ACC-CBL-BAS-TC1M",
				"qty": 1,
				"warehouse": "Yangon Showroom Counter - MMOB",
				"delivery_date": "2026-04-05",
			},
		),
	},
	"delivery_note": {
		"posting_date": "2026-04-05",
		"posting_time": "10:15:00",
		"remarks": "Mini-Phase 1E pilot retail counter delivery / Yangon showroom",
	},
	"sales_invoice": {
		"posting_date": "2026-04-05",
		"posting_time": "10:30:00",
		"due_date": "2026-04-05",
		"remarks": "Mini-Phase 1E pilot retail counter invoice / same-day settlement",
	},
	"payment_entry": {
		"posting_date": "2026-04-05",
		"mode_of_payment": "Cash",
		"bank_account": "Cash - MMOB",
		"reference_no": "CNT-SLIP-0405-01",
		"reference_date": "2026-04-05",
		"remarks": "Mini-Phase 1E pilot retail counter cash settlement",
	},
}

MINIPHASE_1E_WHOLESALE_CREDIT_SALE = {
	"sales_order": {
		"naming_series": "SAL-ORD-.YYYY.-",
		"customer": "Bayint Naung Wholesale Mobile",
		"company": COMPANY_NAME,
		"transaction_date": "2026-04-06",
		"delivery_date": "2026-04-06",
		"po_no": "PILOT-WS-0406-01",
		"po_date": "2026-04-06",
		"currency": "MMK",
		"conversion_rate": 1.0,
		"selling_price_list": "Wholesale Selling - MMOB",
		"price_list_currency": "MMK",
		"plc_conversion_rate": 1.0,
		"payment_terms_template": "30 Days - MMOB",
		"set_warehouse": "Yangon Main Warehouse - MMOB",
		"items": (
			{
				"item_code": "SPH-XMI-RN13-8/256",
				"qty": 4,
				"warehouse": "Yangon Main Warehouse - MMOB",
				"delivery_date": "2026-04-06",
			},
			{
				"item_code": "ACC-CHR-XMI-33W",
				"qty": 20,
				"warehouse": "Yangon Main Warehouse - MMOB",
				"delivery_date": "2026-04-06",
			},
			{
				"item_code": "ACC-CBL-BAS-TC1M",
				"qty": 20,
				"warehouse": "Yangon Main Warehouse - MMOB",
				"delivery_date": "2026-04-06",
			},
		),
	},
	"delivery_note": {
		"posting_date": "2026-04-06",
		"posting_time": "14:15:00",
		"remarks": "Mini-Phase 1E pilot wholesale credit delivery / Yangon main warehouse",
	},
	"sales_invoice": {
		"posting_date": "2026-04-06",
		"posting_time": "14:30:00",
		"due_date": "2026-05-06",
		"remarks": "Mini-Phase 1E pilot wholesale credit invoice / 30-day terms",
	},
}

MINIPHASE_1E_ACCESSORIES_PURCHASE = {
	"purchase_order": {
		"naming_series": "PUR-ORD-.YYYY.-",
		"supplier": "Sunflower Accessories Co.",
		"company": COMPANY_NAME,
		"transaction_date": "2026-04-07",
		"schedule_date": "2026-04-07",
		"currency": "MMK",
		"conversion_rate": 1.0,
		"buying_price_list": "Standard Buying - MMOB",
		"price_list_currency": "MMK",
		"plc_conversion_rate": 1.0,
		"payment_terms_template": "15 Days - MMOB",
		"set_warehouse": "Yangon Main Warehouse - MMOB",
		"items": (
			{
				"item_code": "ACC-PWB-BAS-20K",
				"qty": 50,
				"warehouse": "Yangon Main Warehouse - MMOB",
				"schedule_date": "2026-04-07",
			},
			{
				"item_code": "ACC-CBL-BAS-TC1M",
				"qty": 100,
				"warehouse": "Yangon Main Warehouse - MMOB",
				"schedule_date": "2026-04-07",
			},
			{
				"item_code": "ACC-CHR-XMI-33W",
				"qty": 50,
				"warehouse": "Yangon Main Warehouse - MMOB",
				"schedule_date": "2026-04-07",
			},
		),
	},
	"purchase_receipt": {
		"posting_date": "2026-04-07",
		"posting_time": "16:10:00",
		"supplier_delivery_note": "SFL-DN-0407-01",
		"remarks": "Mini-Phase 1E pilot accessories receipt / Yangon main warehouse replenishment",
	},
	"purchase_invoice": {
		"posting_date": "2026-04-07",
		"posting_time": "16:25:00",
		"bill_no": "SFL-APR-0407-01",
		"bill_date": "2026-04-07",
		"due_date": "2026-04-22",
		"remarks": "Mini-Phase 1E pilot accessories supplier invoice / 15-day credit",
	},
}

MINIPHASE_1F_PARTIAL_SUPPLIER_PAYMENT = {
	"purchase_invoice": "ACC-PINV-2026-00071",
	"posting_date": "2026-04-15",
	"paid_amount": 2_000_000,
	"paid_from": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
	"reference_no": "KBZ-AP-0415-01",
	"reference_date": "2026-04-15",
	"remarks": "Mini-Phase 1F pilot partial supplier payment against accessories purchase invoice",
}

MINIPHASE_1F_PARTIAL_CUSTOMER_COLLECTION = {
	"sales_invoice": "ACC-SINV-2026-00201",
	"posting_date": "2026-04-20",
	"received_amount": 1_500_000,
	"paid_to": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
	"mode_of_payment": "Bank Transfer",
	"reference_no": "KBZ-AR-0420-01",
	"reference_date": "2026-04-20",
	"remarks": "Mini-Phase 1F pilot partial customer collection against wholesale credit invoice",
}

MINIPHASE_1F_WHOLESALE_ACCESSORY_RETURN = {
	"delivery_note": "MAT-DN-2026-00018",
	"sales_invoice": "ACC-SINV-2026-00201",
	"posting_date": "2026-04-21",
	"posting_time": "11:20:00",
	"item_code": "ACC-CHR-XMI-33W",
	"qty": 5,
	"warehouse": "Yangon Main Warehouse - MMOB",
	"remarks_delivery": "Mini-Phase 1F pilot wholesale accessory return / 5 Xiaomi chargers received back into Yangon main warehouse",
	"remarks_invoice": "Mini-Phase 1F pilot wholesale credit note / 5 Xiaomi chargers returned by customer after delivery",
}

MINIPHASE_2A_ADDITIONAL_WHOLESALE_SALE = {
	"sales_order": {
		"naming_series": "SAL-ORD-.YYYY.-",
		"customer": "35th Street Mobile Wholesale",
		"company": COMPANY_NAME,
		"transaction_date": "2026-04-23",
		"delivery_date": "2026-04-23",
		"po_no": "MDY-TOPUP-0423-01",
		"po_date": "2026-04-23",
		"currency": "MMK",
		"conversion_rate": 1.0,
		"selling_price_list": "Wholesale Selling - MMOB",
		"price_list_currency": "MMK",
		"plc_conversion_rate": 1.0,
		"payment_terms_template": "30 Days - MMOB",
		"set_warehouse": "Mandalay Warehouse - MMOB",
		"items": (
			{
				"item_code": "NET-RTR-TPL-C54",
				"qty": 5,
				"warehouse": "Mandalay Warehouse - MMOB",
				"delivery_date": "2026-04-23",
			},
			{
				"item_code": "ACC-CHR-XMI-33W",
				"qty": 10,
				"warehouse": "Mandalay Warehouse - MMOB",
				"delivery_date": "2026-04-23",
			},
		),
	},
	"delivery_note": {
		"posting_date": "2026-04-23",
		"posting_time": "13:40:00",
		"remarks": "Mini-Phase 2A Mandalay wholesale top-up delivery / 35th Street Mobile Wholesale",
	},
	"sales_invoice": {
		"posting_date": "2026-04-23",
		"posting_time": "14:00:00",
		"due_date": "2026-05-23",
		"remarks": "Mini-Phase 2A Mandalay wholesale top-up invoice / 30-day terms",
	},
}

MINIPHASE_2B_BRANCH_TRANSFER = {
	"stock_entry": {
		"naming_series": "MAT-STE-.YYYY.-",
		"company": COMPANY_NAME,
		"posting_date": "2026-04-24",
		"posting_time": "09:20:00",
		"stock_entry_type": "Material Transfer",
		"purpose": "Material Transfer",
		"from_warehouse": "Transit Warehouse - MMOB",
		"to_warehouse": "Mandalay Warehouse - MMOB",
		"remarks": "Mini-Phase 2B router release from transit warehouse to Mandalay after April 23 sell-through",
		"items": (
			{
				"item_code": "NET-RTR-TPL-C54",
				"qty": 5,
				"s_warehouse": "Transit Warehouse - MMOB",
				"t_warehouse": "Mandalay Warehouse - MMOB",
			},
		),
	},
}

MINIPHASE_2C_AGED_COLLECTION = {
	"sales_invoice": "ACC-SINV-2026-00119",
	"posting_date": "2026-04-25",
	"received_amount": 2_000_000,
	"paid_to": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
	"mode_of_payment": "Bank Transfer",
	"reference_no": "KBZ-35ST-0425-01",
	"reference_date": "2026-04-25",
	"remarks": "Mini-Phase 2C aged customer collection against March Mandalay wholesale invoice for 35th Street Mobile Wholesale",
}

MINIPHASE_2D_IMPORTER_AP_PAYMENT = {
	"purchase_invoice": "ACC-PINV-2026-00048",
	"posting_date": "2026-04-28",
	"paid_amount": 3_000_000,
	"paid_from": "CB-001-000789 - CB Bank - Current - MMOB",
	"mode_of_payment": "Bank Transfer",
	"reference_no": "CB-AP-0428-01",
	"reference_date": "2026-04-28",
	"remarks": "Mini-Phase 2D staged importer payment against February Myanmar Tech replenishment invoice",
}

MINIPHASE_2E_PURCHASE_RETURN = {
	"purchase_receipt": "MAT-PRE-2026-00012",
	"purchase_invoice": "ACC-PINV-2026-00071",
	"posting_date": "2026-04-09",
	"posting_time": "17:10:00",
	"item_code": "ACC-PWB-BAS-20K",
	"qty": 5,
	"warehouse": "Yangon Main Warehouse - MMOB",
	"remarks_receipt": "Mini-Phase 2E supplier return / 5 defective power banks sent back to Sunflower Accessories Co.",
	"remarks_invoice": "Mini-Phase 2E supplier debit note / 5 defective power banks returned after receipt quality review",
}

MINIPHASE_2F_REPLACEMENT_RECEIPT = {
	"purchase_order": "PUR-ORD-2026-00009",
	"source_return_receipt": "MAT-PRE-2026-00013",
	"source_return_invoice": "ACC-PINV-2026-00072",
	"posting_date": "2026-04-09",
	"posting_time": "18:00:00",
	"supplier_delivery_note": "SFL-RPL-0409-01",
	"item_code": "ACC-PWB-BAS-20K",
	"qty": 5,
	"warehouse": "Yangon Main Warehouse - MMOB",
	"remarks": "Mini-Phase 2F supplier replacement receipt / 5 quality-approved power banks re-delivered after the April supplier return without new supplier billing",
}

MINIPHASE_3A_SHOWROOM_TOPUP = {
	"stock_entry": {
		"naming_series": "MAT-STE-.YYYY.-",
		"company": COMPANY_NAME,
		"posting_date": "2026-04-09",
		"posting_time": "18:30:00",
		"stock_entry_type": "Material Transfer",
		"purpose": "Material Transfer",
		"from_warehouse": "Yangon Main Warehouse - MMOB",
		"to_warehouse": "Yangon Showroom Counter - MMOB",
		"remarks": "Mini-Phase 3A evening showroom top-up for Xiaomi Redmi Note 13 after live counter stock pressure review",
		"items": (
			{
				"item_code": "SPH-XMI-RN13-8/256",
				"qty": 3,
				"s_warehouse": "Yangon Main Warehouse - MMOB",
				"t_warehouse": "Yangon Showroom Counter - MMOB",
			},
		),
	}
}

MINIPHASE_4E_TRANSIT_ROUTER_CONTINUITY_RELEASE = {
	"stock_entry": {
		"naming_series": "MAT-STE-.YYYY.-",
		"company": COMPANY_NAME,
		"posting_date": "2026-04-25",
		"posting_time": "10:45:00",
		"stock_entry_type": "Material Transfer",
		"purpose": "Material Transfer",
		"from_warehouse": "Transit Warehouse - MMOB",
		"to_warehouse": "Yangon Main Warehouse - MMOB",
		"remarks": "Mini-Phase 4E continuity release of old transit router stock into Yangon Main after the April 24 Mandalay transit release",
		"items": (
			{
				"item_code": "NET-RTR-TPL-C54",
				"qty": 19,
				"s_warehouse": "Transit Warehouse - MMOB",
				"t_warehouse": "Yangon Main Warehouse - MMOB",
			},
			{
				"item_code": "NET-RTR-TPL-C6",
				"qty": 20,
				"s_warehouse": "Transit Warehouse - MMOB",
				"t_warehouse": "Yangon Main Warehouse - MMOB",
			},
		),
	}
}

MINIPHASE_4E_LEGACY_KINGSTON_MEMORY_RELEASE = {
	"stock_entry": {
		"naming_series": "MAT-STE-.YYYY.-",
		"company": COMPANY_NAME,
		"posting_date": "2026-04-26",
		"posting_time": "11:30:00",
		"stock_entry_type": "Material Transfer",
		"purpose": "Material Transfer",
		"from_warehouse": "Transit Warehouse - MMOB",
		"to_warehouse": "Yangon Main Warehouse - MMOB",
		"remarks": "Mini-Phase 4E release of legacy pre-window Kingston memory stock from transit into Yangon Main after warehouse continuity review",
		"items": (
			{
				"item_code": "MEM-MSD-KNG-64",
				"qty": 140,
				"s_warehouse": "Transit Warehouse - MMOB",
				"t_warehouse": "Yangon Main Warehouse - MMOB",
			},
			{
				"item_code": "MEM-USB-KNG-64",
				"qty": 120,
				"s_warehouse": "Transit Warehouse - MMOB",
				"t_warehouse": "Yangon Main Warehouse - MMOB",
			},
		),
	}
}

MINIPHASE_6Q_PARTIAL_TRANSIT_GADGET_RELEASE = {
	"stock_entry": {
		"naming_series": "MAT-STE-.YYYY.-",
		"company": COMPANY_NAME,
		"posting_date": "2026-04-30",
		"posting_time": "16:40:00",
		"stock_entry_type": "Material Transfer",
		"purpose": "Material Transfer",
		"from_warehouse": "Transit Warehouse - MMOB",
		"to_warehouse": "Yangon Main Warehouse - MMOB",
		"remarks": "Mini-Phase 6Q partial customs-cleared release of fast-moving gadget buffer from transit into Yangon Main after procurement-operational review",
		"items": (
			{
				"item_code": "GAD-WCH-XMI-MB8",
				"qty": 20,
				"s_warehouse": "Transit Warehouse - MMOB",
				"t_warehouse": "Yangon Main Warehouse - MMOB",
			},
			{
				"item_code": "GAD-SPK-JBL-GO3",
				"qty": 10,
				"s_warehouse": "Transit Warehouse - MMOB",
				"t_warehouse": "Yangon Main Warehouse - MMOB",
			},
		),
	}
}

MINIPHASE_6T_MYANMAR_TECH_BALANCE_RECEIPT = {
	"purchase_order": "PUR-ORD-2026-00002",
	"supplier": "Myanmar Tech Import Services",
	"company": COMPANY_NAME,
	"posting_date": "2026-01-16",
	"posting_time": "15:20:00",
	"supplier_delivery_note": "MTI-2026-0116-BAL",
	"remarks": (
		"Mini-Phase 6T second-tranche balance receipt completing the remaining Jan 2026 Myanmar Tech "
		"import quantities after receipt-model realism review"
	),
	"expected_remaining_items": {
		"SPH-SAM-A05-4/64": 2.0,
		"SPH-APP-IP13-128": 2.0,
		"SPH-SAM-A15-6/128": 2.0,
		"SPH-RLM-C55-8/256": 2.0,
		"ACC-CBL-BAS-TC1M": 40.0,
		"ACC-CBL-UGR-TC1M": 40.0,
		"MEM-USB-SND-64": 20.0,
	},
}

MINIPHASE_4F_DEFECTIVE_EARBUDS_QUARANTINE = {
	"stock_entry": {
		"naming_series": "MAT-STE-.YYYY.-",
		"company": COMPANY_NAME,
		"posting_date": "2026-04-27",
		"posting_time": "10:15:00",
		"stock_entry_type": "Material Transfer",
		"purpose": "Material Transfer",
		"from_warehouse": "Yangon Main Warehouse - MMOB",
		"to_warehouse": "Returns and Damaged - MMOB",
		"remarks": "Mini-Phase 4F quarantine transfer of one defective Redmi TWS Earbuds unit tied to the 2025-06-24 Ma Ei Phyo retail return after warehouse exception review",
		"reference_return_invoice": "ACC-SINV-RET-2026-00001",
		"items": (
			{
				"item_code": "ACC-AUD-XMI-BUDS4",
				"qty": 1,
				"s_warehouse": "Yangon Main Warehouse - MMOB",
				"t_warehouse": "Returns and Damaged - MMOB",
			},
		),
	}
}

MINIPHASE_4G_CAPITAL_KEY_ACCOUNT_SALE = {
	"sales_order": {
		"naming_series": "SAL-ORD-.YYYY.-",
		"customer": "Capital Telecom (NPT)",
		"company": COMPANY_NAME,
		"transaction_date": "2026-04-30",
		"delivery_date": "2026-04-30",
		"po_no": "CAP-NPT-0430-01",
		"po_date": "2026-04-30",
		"currency": "MMK",
		"conversion_rate": 1.0,
		"selling_price_list": "Key Account Selling - MMOB",
		"price_list_currency": "MMK",
		"plc_conversion_rate": 1.0,
		"payment_terms_template": "45 Days Approved - MMOB",
		"set_warehouse": "Yangon Main Warehouse - MMOB",
		"items": (
			{
				"item_code": "SPH-XMI-RN13-8/256",
				"qty": 3,
				"warehouse": "Yangon Main Warehouse - MMOB",
				"delivery_date": "2026-04-30",
			},
			{
				"item_code": "SPH-SAM-A15-6/128",
				"qty": 1,
				"warehouse": "Yangon Main Warehouse - MMOB",
				"delivery_date": "2026-04-30",
			},
			{
				"item_code": "ACC-CHR-XMI-33W",
				"qty": 25,
				"warehouse": "Yangon Main Warehouse - MMOB",
				"delivery_date": "2026-04-30",
			},
			{
				"item_code": "ACC-CBL-BAS-TC1M",
				"qty": 10,
				"warehouse": "Yangon Main Warehouse - MMOB",
				"delivery_date": "2026-04-30",
			},
		),
	},
	"delivery_note": {
		"posting_date": "2026-04-30",
		"posting_time": "15:20:00",
		"remarks": "Mini-Phase 4G late-April Naypyitaw key-account delivery / mixed handset and accessory replenishment from Yangon Main",
	},
	"sales_invoice": {
		"posting_date": "2026-04-30",
		"posting_time": "15:35:00",
		"due_date": "2026-06-14",
		"remarks": "Mini-Phase 4G late-April Naypyitaw key-account invoice / 45-day approved terms",
	},
}

MINIPHASE_4G_BAYINT_MONTH_END_COLLECTION = {
	"sales_invoice": "ACC-SINV-2026-00201",
	"posting_date": "2026-04-30",
	"received_amount": 1_000_000,
	"paid_to": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
	"mode_of_payment": "Bank Transfer",
	"reference_no": "KBZ-BYNT-0430-01",
	"reference_date": "2026-04-30",
	"remarks": "Mini-Phase 4G month-end partial collection against the April Bayint wholesale invoice ahead of the early-May due date",
}

MINIPHASE_4G_MYANMAR_TECH_REALME_PO = {
	"purchase_order": {
		"naming_series": "PUR-ORD-.YYYY.-",
		"supplier": "Myanmar Tech Import Services",
		"company": COMPANY_NAME,
		"transaction_date": "2026-04-30",
		"schedule_date": "2026-05-05",
		"currency": "MMK",
		"conversion_rate": 1.0,
		"buying_price_list": "Standard Buying - MMOB",
		"price_list_currency": "MMK",
		"plc_conversion_rate": 1.0,
		"payment_terms_template": "Cash on Delivery - MMOB",
		"set_warehouse": "Yangon Main Warehouse - MMOB",
		"remarks": "Mini-Phase 4G month-end importer replenishment signal for Realme C55 after low projected Yangon Main position and preserved active wholesale demand",
		"expected_bin": {
			"item_code": "SPH-RLM-C55-8/256",
			"warehouse": "Yangon Main Warehouse - MMOB",
			"actual_qty": 14.0,
			"reserved_qty": 14.0,
			"ordered_qty": 2.0,
			"projected_qty": 2.0,
		},
		"items": (
			{
				"item_code": "SPH-RLM-C55-8/256",
				"qty": 10,
				"warehouse": "Yangon Main Warehouse - MMOB",
				"schedule_date": "2026-05-05",
				"rate": 790000.0,
			},
		),
	},
}

MINIPHASE_5A_HLEDAN_CATCHUP_BILLING = {
	"delivery_note": "MAT-DN-2026-00013",
	"expected_sales_order": "SAL-ORD-2026-00018",
	"expected_customer": "Hledan Mobile Trade Center",
	"expected_grand_total": 475_000,
	"posting_date": "2026-03-30",
	"posting_time": "17:45:00",
	"due_date": "2026-04-06",
	"payment_terms_template": "7 Days - MMOB",
	"remarks": "Mini-Phase 5A catch-up billing for the already-delivered Hledan power-bank lane after late-March operational-chain review",
}

MINIPHASE_5B_HLEDAN_MICROSD_CATCHUP_BILLING = {
	"delivery_note": "MAT-DN-2026-00010",
	"expected_sales_order": "SAL-ORD-2026-00021",
	"expected_customer": "Hledan Mobile Trade Center",
	"expected_grand_total": 50_000,
	"posting_date": "2026-03-30",
	"posting_time": "18:10:00",
	"due_date": "2026-04-06",
	"payment_terms_template": "7 Days - MMOB",
	"remarks": "Mini-Phase 5B catch-up billing for the already-delivered Hledan MicroSD lane after late-March operational-chain review",
}

MINIPHASE_3B_SHOWROOM_SALE = {
	"sales_order": {
		"naming_series": "SAL-ORD-.YYYY.-",
		"customer": "Hledan Phone Hub",
		"company": COMPANY_NAME,
		"transaction_date": "2026-04-09",
		"delivery_date": "2026-04-09",
		"po_no": "HLD-KBZ-0409-01",
		"po_date": "2026-04-09",
		"currency": "MMK",
		"conversion_rate": 1.0,
		"selling_price_list": "Retail Selling - MMOB",
		"price_list_currency": "MMK",
		"plc_conversion_rate": 1.0,
		"payment_terms_template": "Immediate / Counter Cash - MMOB",
		"set_warehouse": "Yangon Showroom Counter - MMOB",
		"items": (
			{
				"item_code": "SPH-XMI-RN13-8/256",
				"qty": 1,
				"warehouse": "Yangon Showroom Counter - MMOB",
				"delivery_date": "2026-04-09",
			},
			{
				"item_code": "ACC-CHR-XMI-33W",
				"qty": 1,
				"warehouse": "Yangon Showroom Counter - MMOB",
				"delivery_date": "2026-04-09",
			},
			{
				"item_code": "ACC-CBL-BAS-TC1M",
				"qty": 1,
				"warehouse": "Yangon Showroom Counter - MMOB",
				"delivery_date": "2026-04-09",
			},
		),
	},
	"delivery_note": {
		"posting_date": "2026-04-09",
		"posting_time": "19:00:00",
		"remarks": "Mini-Phase 3B same-day Yangon showroom delivery for Hledan Phone Hub after Mini-Phase 3A handset top-up",
	},
	"sales_invoice": {
		"posting_date": "2026-04-09",
		"posting_time": "19:10:00",
		"due_date": "2026-04-09",
		"remarks": "Mini-Phase 3B Yangon showroom invoice for Xiaomi handset bundle settled by KBZ Pay",
	},
	"payment_entry": {
		"posting_date": "2026-04-09",
		"mode_of_payment": "KBZ Pay",
		"bank_account": "KBZPAY-000123 - KBZ Pay Clearing - MMOB",
		"reference_no": "KBZ-HLD-0409-01",
		"reference_date": "2026-04-09",
		"remarks": "Mini-Phase 3B KBZ Pay counter settlement for Hledan Phone Hub showroom Xiaomi bundle",
	},
}

MINIPHASE_3C_STALE_SHOWROOM_ORDER_CANCEL = {
	"sales_order": "SAL-ORD-2026-00009",
	"expected_customer": "Hledan Phone Hub",
	"expected_po_no": "CPO-2026-01-103",
	"replacement_sales_order": "SAL-ORD-2026-00031",
}

MINIPHASE_3D_STALE_SHOWROOM_ORDER_CANCEL = {
	"sales_order": "SAL-ORD-2026-00008",
	"expected_customer": "City Mobile Mart",
	"expected_po_no": "CPO-2026-01-102",
	"replacement_sales_order": "SAL-ORD-2026-00028",
}

MINIPHASE_3E_STALE_SHOWROOM_ORDER_CANCEL = {
	"sales_order": "SAL-ORD-2026-00010",
	"expected_customer": "Pazundaung Phone House",
	"expected_po_no": "CPO-2026-01-104",
}

MINIPHASE_3F_STALE_SHOWROOM_ORDER_CANCEL = {
	"sales_order": "SAL-ORD-2026-00007",
	"expected_customer": "Lanmadaw Telecom & Gadgets",
	"expected_po_no": "CPO-2026-01-101",
}

MINIPHASE_4B_CAPITAL_NPT_AGED_COLLECTION = {
	"sales_invoice": "ACC-SINV-2026-00104",
	"posting_date": "2026-04-29",
	"received_amount": 2_000_000,
	"paid_to": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
	"mode_of_payment": "Bank Transfer",
	"reference_no": "KBZ-NPT-0429-01",
	"reference_date": "2026-04-29",
	"remarks": "Mini-Phase 4B aged customer collection against January Naypyitaw wholesale Xiaomi and charger replenishment invoice for Capital Telecom (NPT)",
}

MINIPHASE_6A_KO_NAY_LIN_AGED_COLLECTION = {
	"sales_invoice": "ACC-SINV-2026-00111",
	"posting_date": "2026-04-09",
	"received_amount": 1_500_000,
	"paid_to": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
	"mode_of_payment": "Bank Transfer",
	"reference_no": "KBZ-KNL-0409-01",
	"reference_date": "2026-04-09",
	"remarks": "Mini-Phase 6A aged customer collection against February Mandalay wholesale power bank and storage invoice for Ko Nay Lin Mobile Center",
}

MINIPHASE_6B_MYANMAR_TECH_FOLLOWON_AP_PAYMENT = {
	"purchase_invoice": "ACC-PINV-2026-00048",
	"posting_date": "2026-04-30",
	"paid_amount": 2_000_000,
	"paid_from": "CB-001-000789 - CB Bank - Current - MMOB",
	"mode_of_payment": "Bank Transfer",
	"reference_no": "CB-AP-0430-02",
	"reference_date": "2026-04-30",
	"remarks": "Mini-Phase 6B follow-on staged importer payment against February Myanmar Tech replenishment invoice after April planning and replenishment review",
}

MINIPHASE_6C_MANDALAY_DEVICE_FOLLOWON_AP_PAYMENT = {
	"purchase_invoice": "ACC-PINV-2026-00050",
	"posting_date": "2026-04-29",
	"paid_amount": 2_500_000,
	"paid_from": "AYA-001-000456 - AYA Bank - Current - MMOB",
	"mode_of_payment": "Bank Transfer",
	"reference_no": "AYA-MDW-0429-01",
	"reference_date": "2026-04-29",
	"remarks": "Mini-Phase 6C follow-on staged local-supplier payment against February Mandalay Device handset and charger replenishment invoice after late-April payables review",
}

MINIPHASE_6E_35TH_STREET_FOLLOWON_COLLECTION = {
	"sales_invoice": "ACC-SINV-2026-00112",
	"posting_date": "2026-04-30",
	"received_amount": 2_000_000,
	"paid_to": "AYA-001-000456 - AYA Bank - Current - MMOB",
	"mode_of_payment": "Bank Transfer",
	"reference_no": "AYA-35ST-0430-01",
	"reference_date": "2026-04-30",
	"remarks": "Mini-Phase 6E follow-on staged customer collection against the February 35th Street premium mixed wholesale invoice after Mini-Phase 6D cross-domain signal review",
}

MINIPHASE_6G_ASIA_CONNECT_FOLLOWON_AP_PAYMENT = {
	"purchase_invoice": "ACC-PINV-2026-00029",
	"posting_date": "2026-04-30",
	"paid_amount": 2_500_000,
	"paid_from": "CB-001-000789 - CB Bank - Current - MMOB",
	"mode_of_payment": "Bank Transfer",
	"reference_no": "CB-ACL-0430-01",
	"reference_date": "2026-04-30",
	"remarks": "Mini-Phase 6G follow-on staged logistics-and-customs supplier payment against the August Asia Connect transit import invoice after Mini-Phase 6F cross-domain signal review",
}

MINIPHASE_6I_SHWE_TAUNG_FOLLOWON_AP_PAYMENT = {
	"purchase_invoice": "ACC-PINV-2026-00054",
	"posting_date": "2026-04-30",
	"paid_amount": 3_000_000,
	"paid_from": "AYA-001-000456 - AYA Bank - Current - MMOB",
	"mode_of_payment": "Bank Transfer",
	"reference_no": "AYA-STE-0430-01",
	"reference_date": "2026-04-30",
	"remarks": "Mini-Phase 6I follow-on staged supplier payment against the January Shwe Taung mixed handset and accessory replenishment invoice after Mini-Phase 6H cross-domain signal review",
}

MINIPHASE_6K_CAPITAL_FOLLOWON_COLLECTION = {
	"sales_invoice": "ACC-SINV-2026-00117",
	"posting_date": "2026-04-30",
	"received_amount": 1_500_000,
	"paid_to": "CB-001-000789 - CB Bank - Current - MMOB",
	"mode_of_payment": "Bank Transfer",
	"reference_no": "CB-NPT-0430-02",
	"reference_date": "2026-04-30",
	"remarks": "Mini-Phase 6K follow-on staged key-account collection against the March Capital Telecom Naypyitaw replenishment invoice after Mini-Phase 6J cross-domain signal review",
}

MINIPHASE_6M_GOLDEN_DRAGON_FOLLOWON_AP_PAYMENT = {
	"purchase_invoice": "ACC-PINV-2026-00059",
	"posting_date": "2026-04-30",
	"paid_amount": 4_000_000,
	"paid_from": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
	"mode_of_payment": "Bank Transfer",
	"reference_no": "KBZ-GD-0430-02",
	"reference_date": "2026-04-30",
	"remarks": "Mini-Phase 6M follow-on staged importer payment against the late-January Golden Dragon mixed handset replenishment invoice after Mini-Phase 6L cross-domain signal review",
}

MINIPHASE_7F_CHAN_AYE_FOLLOWON_COLLECTION = {
	"sales_invoice": "ACC-SINV-2026-00189",
	"posting_date": "2026-04-08",
	"received_amount": 160_000,
	"paid_to": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
	"mode_of_payment": "Bank Transfer",
	"reference_no": "KBZ-CHAN-0408-01",
	"reference_date": "2026-04-08",
	"remarks": "Mini-Phase 7F small follow-on collection against the overdue Chan Aye wholesale memory invoice after customer-lane invoice and settlement coherence review",
}

MINIPHASE_7G_HLEDAN_FOLLOWON_COLLECTION = {
	"sales_invoice": "ACC-SINV-2026-00206",
	"posting_date": "2026-04-10",
	"received_amount": 200_000,
	"paid_to": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
	"mode_of_payment": "Bank Transfer",
	"reference_no": "KBZ-HLD-0410-01",
	"reference_date": "2026-04-10",
	"remarks": "Mini-Phase 7G follow-on bank-transfer collection against the overdue Hledan mixed-history wholesale power-bank invoice after customer-lane settlement review",
}

MINIPHASE_7I_KO_NAY_LIN_MANDALAY_TOPUP = {
	"sales_order": {
		"naming_series": "SAL-ORD-.YYYY.-",
		"customer": "Ko Nay Lin Mobile Center",
		"company": COMPANY_NAME,
		"transaction_date": "2026-04-10",
		"delivery_date": "2026-04-10",
		"po_no": "KNL-MDY-0410-01",
		"po_date": "2026-04-10",
		"currency": "MMK",
		"conversion_rate": 1.0,
		"selling_price_list": "Wholesale Selling - MMOB",
		"price_list_currency": "MMK",
		"plc_conversion_rate": 1.0,
		"payment_terms_template": "30 Days - MMOB",
		"set_warehouse": "Mandalay Warehouse - MMOB",
		"items": (
			{
				"item_code": "SPH-XMI-RN13-8/256",
				"qty": 2,
				"warehouse": "Mandalay Warehouse - MMOB",
				"delivery_date": "2026-04-10",
			},
			{
				"item_code": "ACC-PWB-BAS-20K",
				"qty": 8,
				"warehouse": "Mandalay Warehouse - MMOB",
				"delivery_date": "2026-04-10",
			},
		),
	},
	"delivery_note": {
		"posting_date": "2026-04-10",
		"posting_time": "14:20:00",
		"remarks": (
			"Mini-Phase 7I same-day Mandalay wholesale top-up delivery for Ko Nay Lin Mobile Center "
			"after the Phase 7 midpoint pivot toward current-period branch selling realism"
		),
	},
	"sales_invoice": {
		"posting_date": "2026-04-10",
		"posting_time": "14:35:00",
		"due_date": "2026-05-10",
		"remarks": (
			"Mini-Phase 7I Mandalay wholesale top-up invoice on governed 30-day terms for Ko Nay Lin "
			"Mobile Center after the Phase 7 midpoint pivot"
		),
	},
}

SALES_CONSOLE_APPROVAL_DEMO_QUOTATIONS = (
	{
		"demo_key": "manager_wholesale",
		"customer": "Aung Aung Telecom",
		"company": COMPANY_NAME,
		"transaction_date": "2026-04-10",
		"valid_till": "2026-04-17",
		"selling_price_list": "Wholesale Selling - MMOB",
		"payment_terms_template": "30 Days - MMOB",
		"set_warehouse": "Mandalay Warehouse - MMOB",
		"order_type": "Sales",
		"terms": "Sales Console demo / manager approval / Aung Aung Telecom / Mandalay wholesale replenishment",
		"approval_note": (
			"Sales Console demo quotation requiring manager approval for an April Mandalay wholesale "
			"replenishment lane with rounded handset and accessory value."
		),
		"target_workflow_state": "Pending Sales Approval",
		"workflow_actions": ("Submit Quote",),
		"items": (
			{"item_code": "SPH-XMI-RN13-8/256", "qty": 8},
			{"item_code": "ACC-PWB-BAS-20K", "qty": 20},
			{"item_code": "ACC-CHR-XMI-33W", "qty": 30},
		),
	},
	{
		"demo_key": "manager_hledan_restock",
		"customer": "Hledan Mobile Trade Center",
		"company": COMPANY_NAME,
		"transaction_date": "2026-04-11",
		"valid_till": "2026-04-18",
		"selling_price_list": "Wholesale Selling - MMOB",
		"payment_terms_template": "7 Days - MMOB",
		"set_warehouse": "Yangon Main Warehouse - MMOB",
		"order_type": "Sales",
		"terms": "Sales Console demo / manager approval / Hledan / mixed handset accessory restock",
		"approval_note": (
			"Sales Console demo quotation requiring manager approval for a realistic April Hledan "
			"mixed handset and accessory restock that has not yet converted to order."
		),
		"target_workflow_state": "Pending Sales Approval",
		"workflow_actions": ("Submit Quote",),
		"items": (
			{"item_code": "SPH-XMI-RN13-8/256", "qty": 10},
			{"item_code": "ACC-PWB-BAS-20K", "qty": 6},
			{"item_code": "ACC-CHR-XMI-33W", "qty": 15},
		),
	},
	{
		"demo_key": "gm_value_key_account",
		"customer": "Capital Telecom (NPT)",
		"company": COMPANY_NAME,
		"transaction_date": "2026-04-10",
		"valid_till": "2026-04-22",
		"selling_price_list": "Key Account Selling - MMOB",
		"payment_terms_template": "45 Days Approved - MMOB",
		"set_warehouse": "Yangon Main Warehouse - MMOB",
		"order_type": "Sales",
		"terms": "Sales Console demo / executive approval / Capital Telecom / high-value key-account replenishment",
		"approval_note": (
			"Sales Console demo quotation escalated to executive approval for a large Naypyitaw key-"
			"account replenishment request above the managed approval band."
		),
		"target_workflow_state": "Pending Executive Approval",
		"workflow_actions": ("Submit Quote", "Escalate"),
		"items": (
			{"item_code": "SPH-XMI-RN13-8/256", "qty": 20},
			{"item_code": "SPH-SAM-A15-6/128", "qty": 10},
			{"item_code": "ACC-PWB-BAS-20K", "qty": 30},
		),
	},
	{
		"demo_key": "gm_discount_wholesale",
		"customer": "Bayint Naung Wholesale Mobile",
		"company": COMPANY_NAME,
		"transaction_date": "2026-04-10",
		"valid_till": "2026-04-15",
		"selling_price_list": "Wholesale Selling - MMOB",
		"payment_terms_template": "30 Days - MMOB",
		"set_warehouse": "Yangon Main Warehouse - MMOB",
		"order_type": "Sales",
		"terms": "Sales Console demo / executive approval / Bayint / wholesale discount request",
		"apply_discount_on": "Grand Total",
		"additional_discount_percentage": 12.0,
		"approval_note": (
			"Sales Console demo quotation escalated to executive approval for a wholesale discount "
			"request on a Yangon April bundle ahead of Thingyan promotions."
		),
		"target_workflow_state": "Pending Executive Approval",
		"workflow_actions": ("Submit Quote", "Escalate"),
		"items": (
			{"item_code": "SPH-SAM-A15-6/128", "qty": 12},
			{"item_code": "ACC-PWB-BAS-20K", "qty": 25},
			{"item_code": "ACC-CHR-XMI-33W", "qty": 50},
			{"item_code": "ACC-CBL-BAS-TC1M", "qty": 30},
		),
	},
)

SALES_CONSOLE_ORDER_APPROVAL_DEMO_CHAINS = (
	{
		"demo_key": "manager_order_wholesale",
		"customer": "Aung Aung Telecom",
		"company": COMPANY_NAME,
		"quotation": {
			"transaction_date": "2026-04-11",
			"valid_till": "2026-04-18",
			"selling_price_list": "Wholesale Selling - MMOB",
			"payment_terms_template": "30 Days - MMOB",
			"set_warehouse": "Mandalay Warehouse - MMOB",
			"order_type": "Sales",
			"terms": "Sales Console demo / approved quotation / Aung Aung Telecom / order blocker chain",
			"approval_note": (
				"Sales Console demo upstream quotation approved before order submission for a Mandalay "
				"wholesale handset and accessory replenishment lane."
			),
			"workflow_actions": ("Submit Quote", "Approve"),
			"target_workflow_state": "Approved",
		},
		"sales_order": {
			"delivery_date": "2026-04-14",
			"po_no": "SOAPP-AAT-0411-01",
			"po_date": "2026-04-11",
			"payment_terms_template": "30 Days - MMOB",
			"set_warehouse": "Mandalay Warehouse - MMOB",
			"remarks": (
				"Sales Console demo sales order waiting for manager approval after customer confirmation "
				"of the approved Aung Aung wholesale quotation."
			),
			"workflow_actions": ("Submit Order",),
			"target_workflow_state": "Pending Sales Approval",
		},
		"items": (
			{"item_code": "SPH-XMI-RN13-8/256", "qty": 10},
			{"item_code": "ACC-PWB-BAS-20K", "qty": 18},
			{"item_code": "ACC-CHR-XMI-33W", "qty": 24},
		),
	},
	{
		"demo_key": "executive_order_value_key_account",
		"customer": "Capital Telecom (NPT)",
		"company": COMPANY_NAME,
		"quotation": {
			"transaction_date": "2026-04-11",
			"valid_till": "2026-04-25",
			"selling_price_list": "Key Account Selling - MMOB",
			"payment_terms_template": "45 Days Approved - MMOB",
			"set_warehouse": "Yangon Main Warehouse - MMOB",
			"order_type": "Sales",
			"terms": "Sales Console demo / approved quotation / Capital Telecom / executive order blocker chain",
			"approval_note": (
				"Sales Console demo upstream quotation fully approved for a large Naypyitaw key-account "
				"replenishment before the final sales order enters executive approval."
			),
			"workflow_actions": ("Submit Quote", "Escalate", "Approve"),
			"target_workflow_state": "Approved",
		},
		"sales_order": {
			"delivery_date": "2026-04-16",
			"po_no": "SOAPP-CAP-0411-01",
			"po_date": "2026-04-11",
			"payment_terms_template": "45 Days Approved - MMOB",
			"set_warehouse": "Yangon Main Warehouse - MMOB",
			"remarks": (
				"Sales Console demo sales order escalated for executive approval after the quotation was "
				"already approved on a large Naypyitaw key-account commitment."
			),
			"workflow_actions": ("Submit Order", "Escalate"),
			"target_workflow_state": "Pending Executive Approval",
		},
		"items": (
			{"item_code": "SPH-XMI-RN13-8/256", "qty": 18},
			{"item_code": "SPH-SAM-A15-6/128", "qty": 8},
			{"item_code": "ACC-PWB-BAS-20K", "qty": 28},
		),
	},
	{
		"demo_key": "executive_order_discount_wholesale",
		"customer": "Bayint Naung Wholesale Mobile",
		"company": COMPANY_NAME,
		"quotation": {
			"transaction_date": "2026-04-11",
			"valid_till": "2026-04-17",
			"selling_price_list": "Wholesale Selling - MMOB",
			"payment_terms_template": "30 Days - MMOB",
			"set_warehouse": "Yangon Main Warehouse - MMOB",
			"order_type": "Sales",
			"terms": "Sales Console demo / approved quotation / Bayint / executive discount order blocker chain",
			"approval_note": (
				"Sales Console demo upstream quotation approved for a Yangon wholesale discount case "
				"before the final customer order is escalated for executive approval."
			),
			"apply_discount_on": "Grand Total",
			"additional_discount_percentage": 12.0,
			"workflow_actions": ("Submit Quote", "Escalate", "Approve"),
			"target_workflow_state": "Approved",
		},
		"sales_order": {
			"delivery_date": "2026-04-15",
			"po_no": "SOAPP-BNT-0411-01",
			"po_date": "2026-04-11",
			"payment_terms_template": "30 Days - MMOB",
			"set_warehouse": "Yangon Main Warehouse - MMOB",
			"remarks": (
				"Sales Console demo sales order waiting for executive approval because the final Bayint "
				"wholesale order still carries a managed promotional discount."
			),
			"apply_discount_on": "Grand Total",
			"additional_discount_percentage": 12.0,
			"workflow_actions": ("Submit Order", "Escalate"),
			"target_workflow_state": "Pending Executive Approval",
		},
		"items": (
			{"item_code": "SPH-SAM-A15-6/128", "qty": 12},
			{"item_code": "ACC-PWB-BAS-20K", "qty": 25},
			{"item_code": "ACC-CHR-XMI-33W", "qty": 50},
			{"item_code": "ACC-CBL-BAS-TC1M", "qty": 30},
		),
	},
)

MINIPHASE_6O_SUPPLIER_POLICY_DEFAULTS = (
	{
		"supplier": "Asia Connect Logistics & Customs",
		"default_price_list": "Standard Buying - MMOB",
		"payment_terms": "30 Days - MMOB",
	},
	{
		"supplier": "Golden Dragon Trading Co. Ltd.",
		"default_price_list": "Standard Buying - MMOB",
		"payment_terms": "30 Days - MMOB",
	},
	{
		"supplier": "Mandalay Device Wholesale",
		"default_price_list": "Standard Buying - MMOB",
		"payment_terms": "30 Days - MMOB",
	},
	{
		"supplier": "Shan Yoma Electronics",
		"default_price_list": "Standard Buying - MMOB",
		"payment_terms": "30 Days - MMOB",
	},
	{
		"supplier": "Shwe Taung Electronics Supply",
		"default_price_list": "Standard Buying - MMOB",
		"payment_terms": "30 Days - MMOB",
	},
)

MINIPHASE_4C_GOLDEN_DRAGON_AGED_AP_PAYMENT = {
	"purchase_invoice": "ACC-PINV-2026-00056",
	"posting_date": "2026-04-30",
	"paid_amount": 5_000_000,
	"paid_from": "CB-001-000789 - CB Bank - Current - MMOB",
	"mode_of_payment": "Bank Transfer",
	"reference_no": "CB-GD-0430-01",
	"reference_date": "2026-04-30",
	"remarks": "Mini-Phase 4C aged supplier payment against January Golden Dragon handset replenishment invoice after concentrated January import build-up",
}

MINIPHASE_4D_STALE_WHOLESALE_ORDER_CANCEL = {
	"sales_order": "SAL-ORD-2026-00002",
	"expected_customer": "Shwe Li Road Mobile Wholesale",
	"expected_po_no": "CPO-2026-01-002",
}

MINIPHASE_4D_MANDALAY_STALE_WHOLESALE_ORDER_CANCEL = {
	"sales_order": "SAL-ORD-2026-00004",
	"expected_customer": "Mandalay Mobile Hub",
	"expected_po_no": "CPO-2026-01-004",
}

MINIPHASE_4D_LATHA_STALE_WHOLESALE_ORDER_CANCEL = {
	"sales_order": "SAL-ORD-2026-00001",
	"expected_customer": "Latha Mobile Wholesale",
	"expected_po_no": "CPO-2026-01-001",
}

MINIPHASE_4D_AMARAPURA_STALE_RETAIL_ORDER_CANCEL = {
	"sales_order": "SAL-ORD-2026-00011",
	"expected_customer": "Amarapura Phone Corner",
	"expected_po_no": "CPO-2026-01-201",
}

MINIPHASE_4D_MANDALAY_ACCESSORIES_STALE_WHOLESALE_ORDER_CANCEL = {
	"sales_order": "SAL-ORD-2026-00005",
	"expected_customer": "Mandalay Accessories Wholesale",
	"expected_po_no": "CPO-2026-01-005",
}

MINIPHASE_4D_ZEGYO_MARKET_STALE_RETAIL_ORDER_CANCEL = {
	"sales_order": "SAL-ORD-2026-00012",
	"expected_customer": "Zegyo Market Mobile Shop",
	"expected_po_no": "CPO-2026-01-202",
}

WHOLESALE_CUSTOMER_CREDIT_LIMITS = (
	{
		"customer": "35th Street Mobile Wholesale",
		"target_credit_limit": 45_000_000,
		"bypass_credit_limit_check": 0,
	},
	{
		"customer": "Bayint Naung Wholesale Mobile",
		"target_credit_limit": 60_000_000,
		"bypass_credit_limit_check": 0,
	},
	{
		"customer": "Capital Telecom (NPT)",
		"target_credit_limit": 50_000_000,
		"bypass_credit_limit_check": 0,
	},
	{
		"customer": "Ko Nay Lin Mobile Center",
		"target_credit_limit": 30_000_000,
		"bypass_credit_limit_check": 0,
	},
	{
		"customer": "Aung Aung Telecom",
		"target_credit_limit": 25_000_000,
		"bypass_credit_limit_check": 0,
	},
	{
		"customer": "Latha Mobile Wholesale",
		"target_credit_limit": 20_000_000,
		"bypass_credit_limit_check": 0,
	},
	{
		"customer": "Mandalay Accessories Wholesale",
		"target_credit_limit": 15_000_000,
		"bypass_credit_limit_check": 0,
	},
	{
		"customer": "Mandalay Mobile Hub",
		"target_credit_limit": 15_000_000,
		"bypass_credit_limit_check": 0,
	},
	{
		"customer": "Shwe Li Road Mobile Wholesale",
		"target_credit_limit": 15_000_000,
		"bypass_credit_limit_check": 0,
	},
	{
		"customer": "Shwe Pyi Mobile & Accessories",
		"target_credit_limit": 15_000_000,
		"bypass_credit_limit_check": 0,
	},
	{
		"customer": "Zegyo Mobile Supply House",
		"target_credit_limit": 10_000_000,
		"bypass_credit_limit_check": 0,
	},
	{
		"customer": "Chan Aye Mobile Trading Hub",
		"target_credit_limit": 5_000_000,
		"bypass_credit_limit_check": 0,
	},
	{
		"customer": "Hledan Mobile Trade Center",
		"target_credit_limit": 5_000_000,
		"bypass_credit_limit_check": 0,
	},
	{
		"customer": "Lanmadaw Digital Wholesale",
		"target_credit_limit": 5_000_000,
		"bypass_credit_limit_check": 0,
	},
	{
		"customer": "Pazundaung Mobile Distribution",
		"target_credit_limit": 5_000_000,
		"bypass_credit_limit_check": 0,
	},
	{
		"customer": "Thaketa Mobile Exchange",
		"target_credit_limit": 5_000_000,
		"bypass_credit_limit_check": 0,
	},
	{
		"customer": "Maha Bandula Mobile Wholesale",
		"target_credit_limit": 5_000_000,
		"bypass_credit_limit_check": 0,
	},
	{
		"customer": "Theingyi Telecom Distribution",
		"target_credit_limit": 5_000_000,
		"bypass_credit_limit_check": 0,
	},
)

WHOLESALE_CUSTOMER_POLICY_DEFAULTS = (
	{
		"customer": "35th Street Mobile Wholesale",
		"default_price_list": "Wholesale Selling - MMOB",
		"payment_terms": "30 Days - MMOB",
	},
	{
		"customer": "Bayint Naung Wholesale Mobile",
		"default_price_list": "Wholesale Selling - MMOB",
		"payment_terms": "30 Days - MMOB",
	},
	{
		"customer": "Capital Telecom (NPT)",
		"default_price_list": "Key Account Selling - MMOB",
		"payment_terms": "45 Days Approved - MMOB",
	},
	{
		"customer": "Aung Aung Telecom",
		"default_price_list": "Wholesale Selling - MMOB",
		"payment_terms": "30 Days - MMOB",
	},
	{
		"customer": "Ko Nay Lin Mobile Center",
		"default_price_list": "Wholesale Selling - MMOB",
		"payment_terms": "30 Days - MMOB",
	},
	{
		"customer": "Latha Mobile Wholesale",
		"default_price_list": "Wholesale Selling - MMOB",
		"payment_terms": "30 Days - MMOB",
	},
	{
		"customer": "Mandalay Accessories Wholesale",
		"default_price_list": "Wholesale Selling - MMOB",
		"payment_terms": "15 Days - MMOB",
	},
	{
		"customer": "Mandalay Mobile Hub",
		"default_price_list": "Wholesale Selling - MMOB",
		"payment_terms": "15 Days - MMOB",
	},
	{
		"customer": "Shwe Li Road Mobile Wholesale",
		"default_price_list": "Wholesale Selling - MMOB",
		"payment_terms": "15 Days - MMOB",
	},
	{
		"customer": "Shwe Pyi Mobile & Accessories",
		"default_price_list": "Wholesale Selling - MMOB",
		"payment_terms": "15 Days - MMOB",
	},
	{
		"customer": "Zegyo Mobile Supply House",
		"default_price_list": "Wholesale Selling - MMOB",
		"payment_terms": "15 Days - MMOB",
	},
	{
		"customer": "Chan Aye Mobile Trading Hub",
		"default_price_list": "Wholesale Selling - MMOB",
		"payment_terms": "7 Days - MMOB",
	},
	{
		"customer": "Hledan Mobile Trade Center",
		"default_price_list": "Wholesale Selling - MMOB",
		"payment_terms": "7 Days - MMOB",
	},
	{
		"customer": "Lanmadaw Digital Wholesale",
		"default_price_list": "Wholesale Selling - MMOB",
		"payment_terms": "7 Days - MMOB",
	},
	{
		"customer": "Pazundaung Mobile Distribution",
		"default_price_list": "Wholesale Selling - MMOB",
		"payment_terms": "7 Days - MMOB",
	},
	{
		"customer": "Thaketa Mobile Exchange",
		"default_price_list": "Wholesale Selling - MMOB",
		"payment_terms": "7 Days - MMOB",
	},
	{
		"customer": "Maha Bandula Mobile Wholesale",
		"default_price_list": "Wholesale Selling - MMOB",
		"payment_terms": "7 Days - MMOB",
	},
	{
		"customer": "Theingyi Telecom Distribution",
		"default_price_list": "Wholesale Selling - MMOB",
		"payment_terms": "7 Days - MMOB",
	},
)

MINIPHASE_7J_ACTIVE_RETAIL_POLICY_DEFAULTS = (
	{
		"customer": "Hledan Phone Hub",
		"default_price_list": "Retail Selling - MMOB",
		"payment_terms": "Immediate / Counter Cash - MMOB",
	},
	{
		"customer": "Sanchaung Mobile Plaza",
		"default_price_list": "Retail Selling - MMOB",
		"payment_terms": "Immediate / Counter Cash - MMOB",
	},
	{
		"customer": "Taunggyi City Mobile",
		"default_price_list": "Retail Selling - MMOB",
		"payment_terms": "Cash on Delivery - MMOB",
	},
)


def _normalize_truthy(value: Any) -> bool:
	if isinstance(value, bool):
		return value
	if value is None:
		return False
	return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _round_up_mmk(value: float, unit: int = MMK_CREDIT_ROUNDING_UNIT) -> int:
	if value <= 0:
		return 0
	return int(math.ceil(float(value) / float(unit)) * unit)


def _summarize_doc(doc: Any) -> dict[str, Any]:
	item_rows = []
	for row in getattr(doc, "items", []) or []:
		item_rows.append(
			{
				"item_code": getattr(row, "item_code", None),
				"qty": getattr(row, "qty", None),
				"warehouse": getattr(row, "warehouse", None),
				"rate": getattr(row, "rate", None),
				"amount": getattr(row, "amount", None),
			}
		)

	return {
		"doctype": doc.doctype,
		"name": doc.name,
		"docstatus": doc.docstatus,
		"status": getattr(doc, "status", None),
		"posting_date": getattr(doc, "posting_date", None),
		"grand_total": getattr(doc, "grand_total", None),
		"outstanding_amount": getattr(doc, "outstanding_amount", None),
		"customer": getattr(doc, "customer", None),
		"supplier": getattr(doc, "supplier", None),
		"po_no": getattr(doc, "po_no", None),
		"remarks": getattr(doc, "remarks", None),
		"items": item_rows,
	}


def _summarize_payment_entry(doc: Any) -> dict[str, Any]:
	return {
		"doctype": doc.doctype,
		"name": doc.name,
		"docstatus": doc.docstatus,
		"status": getattr(doc, "status", None),
		"posting_date": getattr(doc, "posting_date", None),
		"mode_of_payment": getattr(doc, "mode_of_payment", None),
		"paid_from": getattr(doc, "paid_from", None),
		"paid_to": getattr(doc, "paid_to", None),
		"paid_amount": getattr(doc, "paid_amount", None),
		"received_amount": getattr(doc, "received_amount", None),
		"reference_no": getattr(doc, "reference_no", None),
		"party_type": getattr(doc, "party_type", None),
		"party": getattr(doc, "party", None),
		"references": [
			{
				"reference_doctype": row.reference_doctype,
				"reference_name": row.reference_name,
				"allocated_amount": row.allocated_amount,
			}
			for row in getattr(doc, "references", []) or []
		],
	}


def _get_pilot_price_rate(item_code: str, price_list: str) -> float:
	for item_spec in MINIPHASE_1D_PILOT_ITEM_PRICES:
		if item_spec["item_code"] == item_code:
			if price_list not in item_spec["prices"]:
				break
			return float(item_spec["prices"][price_list])

	frappe.throw(f"No pilot price configured for item {item_code} in price list {price_list}.")


def _get_live_item_price_rate(item_code: str, price_list: str, uom: str = "Nos") -> float:
	row = frappe.get_all(
		"Item Price",
		filters={"item_code": item_code, "price_list": price_list, "uom": uom},
		fields=["price_list_rate"],
		limit=1,
	)
	if row:
		return float(row[0]["price_list_rate"])
	return _get_pilot_price_rate(item_code, price_list)


def _get_pilot_purchase_rate(item_code: str) -> float:
	return _get_pilot_price_rate(item_code, "Standard Buying - MMOB")


def _apply_customer_credit_limit_specs(
	specs: tuple[dict[str, Any], ...],
	label: str,
	dry_run: bool = False,
) -> dict[str, Any]:
	"""Upsert rounded MMK credit limits for a controlled customer slice."""

	dry_run = _normalize_truthy(dry_run)
	results: list[dict[str, Any]] = []

	for spec in specs:
		customer = frappe.get_doc("Customer", spec["customer"])
		outstanding = get_customer_outstanding(
			customer.name,
			COMPANY_NAME,
			ignore_outstanding_sales_order=spec["bypass_credit_limit_check"],
		)
		effective_credit_limit = _round_up_mmk(max(spec["target_credit_limit"], outstanding))
		limit_row = next((row for row in customer.credit_limits if row.company == COMPANY_NAME), None)

		if limit_row:
			change_type = "update"
			before = {
				"credit_limit": limit_row.credit_limit,
				"bypass_credit_limit_check": limit_row.bypass_credit_limit_check,
			}
			if not dry_run:
				limit_row.credit_limit = effective_credit_limit
				limit_row.bypass_credit_limit_check = spec["bypass_credit_limit_check"]
		else:
			change_type = "insert"
			before = None
			if not dry_run:
				customer.append(
					"credit_limits",
					{
						"company": COMPANY_NAME,
						"credit_limit": effective_credit_limit,
						"bypass_credit_limit_check": spec["bypass_credit_limit_check"],
					},
				)

		if not dry_run:
			customer.save(ignore_permissions=True)

		results.append(
			{
				"customer": customer.name,
				"change_type": change_type,
				"before": before,
				"current_outstanding": outstanding,
				"after": {
					"company": COMPANY_NAME,
					"target_credit_limit": spec["target_credit_limit"],
					"effective_credit_limit": effective_credit_limit,
					"bypass_credit_limit_check": spec["bypass_credit_limit_check"],
				},
			}
		)

	if not dry_run:
		frappe.db.commit()

	return {
		"ok": True,
		"dry_run": dry_run,
		"label": label,
		"company": COMPANY_NAME,
		"count": len(results),
		"results": results,
	}


def apply_miniphase_1c_pilot_customer_credit_limits(dry_run: bool = False) -> dict[str, Any]:
	"""Upsert rounded MMK credit limits for the approved pilot-customer slice.

	These are transitional limits, not final policy targets. They are kept above
	current live exposure so ERP validation can accept the records while AR
	cleanup is still pending.
	"""

	return _apply_customer_credit_limit_specs(
		MINIPHASE_1C_PILOT_CREDIT_LIMITS,
		"Mini-Phase 1C Pilot Customer Credit Limits",
		dry_run=dry_run,
	)


def apply_wholesale_customer_credit_limits(dry_run: bool = False) -> dict[str, Any]:
	"""Upsert rounded MMK credit limits for the real wholesale customer layer.

	This rollout intentionally covers wholesale accounts only. Retail customers
	remain without formal credit limits unless a later scenario explicitly
	requires managed retail credit.
	"""

	return _apply_customer_credit_limit_specs(
		WHOLESALE_CUSTOMER_CREDIT_LIMITS,
		WHOLESALE_CUSTOMER_CREDIT_LIMIT_ROLLOUT_LABEL,
		dry_run=dry_run,
	)


def apply_wholesale_customer_policy_defaults(dry_run: bool = False) -> dict[str, Any]:
	"""Assign realistic default price lists and payment terms to wholesale customers."""

	return _apply_customer_policy_defaults_specs(
		WHOLESALE_CUSTOMER_POLICY_DEFAULTS,
		WHOLESALE_CUSTOMER_POLICY_DEFAULTS_LABEL,
		dry_run=dry_run,
	)


def _apply_customer_policy_defaults_specs(
	specs: tuple[dict[str, Any], ...],
	label: str,
	dry_run: bool = False,
) -> dict[str, Any]:
	"""Assign default price lists and payment terms to a bounded customer slice."""

	dry_run = _normalize_truthy(dry_run)
	results: list[dict[str, Any]] = []

	for spec in specs:
		customer = frappe.get_doc("Customer", spec["customer"])
		before = {
			"default_price_list": customer.default_price_list,
			"payment_terms": customer.payment_terms,
		}
		changed = (
			str(customer.default_price_list or "") != str(spec["default_price_list"])
			or str(customer.payment_terms or "") != str(spec["payment_terms"])
		)

		if changed and not dry_run:
			customer.default_price_list = spec["default_price_list"]
			customer.payment_terms = spec["payment_terms"]
			customer.save(ignore_permissions=True)

		results.append(
			{
				"customer": customer.name,
				"change_type": "update" if changed else "noop",
				"before": before,
				"after": {
					"default_price_list": spec["default_price_list"],
					"payment_terms": spec["payment_terms"],
				},
			}
		)

	if not dry_run:
		frappe.db.commit()

	return {
		"ok": True,
		"dry_run": dry_run,
		"label": label,
		"count": len(results),
		"results": results,
	}


def apply_miniphase_7j_active_retail_policy_defaults(dry_run: bool = False) -> dict[str, Any]:
	"""Assign retail defaults only to the active 2026 retail customer slice missing control posture."""

	return _apply_customer_policy_defaults_specs(
		MINIPHASE_7J_ACTIVE_RETAIL_POLICY_DEFAULTS,
		MINIPHASE_7J_ACTIVE_RETAIL_POLICY_DEFAULTS_LABEL,
		dry_run=dry_run,
	)


def apply_miniphase_1d_pilot_item_prices(dry_run: bool = False) -> dict[str, Any]:
	"""Upsert pilot item-price rows for the new MMOB commercial price lists."""

	dry_run = _normalize_truthy(dry_run)
	results: list[dict[str, Any]] = []

	for item_spec in MINIPHASE_1D_PILOT_ITEM_PRICES:
		for price_list, rate in item_spec["prices"].items():
			existing = frappe.get_all(
				"Item Price",
				filters={
					"item_code": item_spec["item_code"],
					"price_list": price_list,
					"uom": item_spec["uom"],
				},
				fields=["name", "price_list_rate"],
				limit=1,
			)

			if existing:
				change_type = "update"
				before = existing[0]["price_list_rate"]
				if not dry_run:
					doc = frappe.get_doc("Item Price", existing[0]["name"])
					doc.price_list_rate = rate
					doc.reference = PILOT_PRICE_REFERENCE
					doc.save(ignore_permissions=True)
			else:
				change_type = "insert"
				before = None
				if not dry_run:
					doc = frappe.get_doc(
						{
							"doctype": "Item Price",
							"item_code": item_spec["item_code"],
							"uom": item_spec["uom"],
							"price_list": price_list,
							"price_list_rate": rate,
							"reference": PILOT_PRICE_REFERENCE,
						}
					)
					doc.insert(ignore_permissions=True)

			results.append(
				{
					"item_code": item_spec["item_code"],
					"price_list": price_list,
					"change_type": change_type,
					"before": before,
					"after": rate,
				}
			)

	if not dry_run:
		frappe.db.commit()

	return {
		"ok": True,
		"dry_run": dry_run,
		"reference": PILOT_PRICE_REFERENCE,
		"count": len(results),
		"results": results,
	}


def create_miniphase_1e_retail_counter_sales_order(dry_run: bool = False) -> dict[str, Any]:
	"""Create the approved retail counter Sales Order with explicit pilot price rates."""

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_1E_RETAIL_COUNTER_SALE["sales_order"]
	item_rows = []

	for row in spec["items"]:
		rate = _get_pilot_price_rate(row["item_code"], spec["selling_price_list"])
		item_rows.append(
			{
				"item_code": row["item_code"],
				"qty": row["qty"],
				"warehouse": row["warehouse"],
				"delivery_date": row["delivery_date"],
				"uom": "Nos",
				"conversion_factor": 1.0,
				"price_list_rate": rate,
				"rate": rate,
			}
		)

	doc = frappe.get_doc(
		{
			"doctype": "Sales Order",
			"naming_series": spec["naming_series"],
			"customer": spec["customer"],
			"company": spec["company"],
			"transaction_date": spec["transaction_date"],
			"delivery_date": spec["delivery_date"],
			"po_no": spec["po_no"],
			"po_date": spec["po_date"],
			"currency": spec["currency"],
			"conversion_rate": spec["conversion_rate"],
			"selling_price_list": spec["selling_price_list"],
			"price_list_currency": spec["price_list_currency"],
			"plc_conversion_rate": spec["plc_conversion_rate"],
			"payment_terms_template": spec["payment_terms_template"],
			"set_warehouse": spec["set_warehouse"],
			"items": item_rows,
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	doc.submit()

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_1E_RETAIL_SALE_LABEL,
		"sales_order": _summarize_doc(doc),
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def complete_miniphase_1e_retail_counter_sale_from_sales_order(
	sales_order_name: str, dry_run: bool = False
) -> dict[str, Any]:
	"""Map a submitted pilot Sales Order through delivery, invoice, and cash receipt.

	This uses ERPNext's native mapping functions so downstream links remain intact.
	The helper is intentionally narrow: one approved pilot scenario only.
	"""

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
	from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
	from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_1E_RETAIL_COUNTER_SALE

	sales_order = frappe.get_doc("Sales Order", sales_order_name)
	if sales_order.docstatus != 1:
		frappe.throw(f"Sales Order {sales_order_name} must be submitted before downstream mapping.")
	if sales_order.customer != spec["sales_order"]["customer"]:
		frappe.throw(
			f"Sales Order {sales_order_name} belongs to {sales_order.customer}, expected {spec['sales_order']['customer']}."
		)
	if sales_order.company != COMPANY_NAME:
		frappe.throw(f"Sales Order {sales_order_name} does not belong to {COMPANY_NAME}.")
	if float(sales_order.per_delivered or 0) > 0 or float(sales_order.per_billed or 0) > 0:
		frappe.throw(
			f"Sales Order {sales_order_name} already has downstream activity "
			f"(delivered={sales_order.per_delivered}, billed={sales_order.per_billed})."
		)

	delivery_note = make_delivery_note(sales_order.name)
	delivery_note.set_posting_time = 1
	delivery_note.posting_date = spec["delivery_note"]["posting_date"]
	delivery_note.posting_time = spec["delivery_note"]["posting_time"]
	delivery_note.lr_date = spec["delivery_note"]["posting_date"]
	delivery_note.remarks = spec["delivery_note"]["remarks"]
	delivery_note.flags.ignore_permissions = True
	delivery_note.insert(ignore_permissions=True)
	delivery_note.submit()

	sales_invoice = make_sales_invoice(delivery_note.name)
	sales_invoice.set_posting_time = 1
	sales_invoice.posting_date = spec["sales_invoice"]["posting_date"]
	sales_invoice.posting_time = spec["sales_invoice"]["posting_time"]
	sales_invoice.due_date = spec["sales_invoice"]["due_date"]
	sales_invoice.payment_terms_template = sales_order.payment_terms_template
	sales_invoice.remarks = spec["sales_invoice"]["remarks"]
	sales_invoice.flags.ignore_permissions = True
	sales_invoice.insert(ignore_permissions=True)
	sales_invoice.submit()

	payment_entry = get_payment_entry(
		"Sales Invoice",
		sales_invoice.name,
		bank_account=spec["payment_entry"]["bank_account"],
		reference_date=spec["payment_entry"]["reference_date"],
	)
	payment_entry.posting_date = spec["payment_entry"]["posting_date"]
	payment_entry.mode_of_payment = spec["payment_entry"]["mode_of_payment"]
	if payment_entry.mode_of_payment == "Cash":
		payment_entry.bank_account = None
	payment_entry.reference_no = spec["payment_entry"]["reference_no"]
	payment_entry.reference_date = spec["payment_entry"]["reference_date"]
	payment_entry.remarks = (
		f"{spec['payment_entry']['remarks']}\n"
		f"Amount MMK {payment_entry.received_amount} received against Sales Invoice {sales_invoice.name}"
	)
	payment_entry.flags.ignore_permissions = True
	payment_entry.insert(ignore_permissions=True)
	payment_entry.submit()

	sales_order = frappe.get_doc("Sales Order", sales_order_name)
	delivery_note = frappe.get_doc("Delivery Note", delivery_note.name)
	sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice.name)
	payment_entry = frappe.get_doc("Payment Entry", payment_entry.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_1E_RETAIL_SALE_LABEL,
		"sales_order": _summarize_doc(sales_order),
		"delivery_note": _summarize_doc(delivery_note),
		"sales_invoice": _summarize_doc(sales_invoice),
		"payment_entry": {
			"doctype": payment_entry.doctype,
			"name": payment_entry.name,
			"docstatus": payment_entry.docstatus,
			"status": getattr(payment_entry, "status", None),
			"posting_date": payment_entry.posting_date,
			"mode_of_payment": payment_entry.mode_of_payment,
			"paid_from": payment_entry.paid_from,
			"paid_to": payment_entry.paid_to,
			"paid_amount": payment_entry.paid_amount,
			"received_amount": payment_entry.received_amount,
			"reference_no": payment_entry.reference_no,
			"references": [
				{
					"reference_doctype": row.reference_doctype,
					"reference_name": row.reference_name,
					"allocated_amount": row.allocated_amount,
				}
				for row in payment_entry.references
			],
		},
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_1e_wholesale_credit_sales_order(dry_run: bool = False) -> dict[str, Any]:
	"""Create the approved wholesale credit Sales Order with explicit pilot price rates."""

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_1E_WHOLESALE_CREDIT_SALE["sales_order"]
	item_rows = []

	for row in spec["items"]:
		rate = _get_pilot_price_rate(row["item_code"], spec["selling_price_list"])
		item_rows.append(
			{
				"item_code": row["item_code"],
				"qty": row["qty"],
				"warehouse": row["warehouse"],
				"delivery_date": row["delivery_date"],
				"uom": "Nos",
				"conversion_factor": 1.0,
				"price_list_rate": rate,
				"rate": rate,
			}
		)

	doc = frappe.get_doc(
		{
			"doctype": "Sales Order",
			"naming_series": spec["naming_series"],
			"customer": spec["customer"],
			"company": spec["company"],
			"transaction_date": spec["transaction_date"],
			"delivery_date": spec["delivery_date"],
			"po_no": spec["po_no"],
			"po_date": spec["po_date"],
			"currency": spec["currency"],
			"conversion_rate": spec["conversion_rate"],
			"selling_price_list": spec["selling_price_list"],
			"price_list_currency": spec["price_list_currency"],
			"plc_conversion_rate": spec["plc_conversion_rate"],
			"payment_terms_template": spec["payment_terms_template"],
			"set_warehouse": spec["set_warehouse"],
			"items": item_rows,
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	doc.submit()

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_1E_WHOLESALE_CREDIT_SALE_LABEL,
		"sales_order": _summarize_doc(doc),
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def complete_miniphase_1e_wholesale_credit_sale_from_sales_order(
	sales_order_name: str, dry_run: bool = False
) -> dict[str, Any]:
	"""Map a submitted pilot wholesale credit Sales Order through delivery and invoice."""

	from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
	from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_1E_WHOLESALE_CREDIT_SALE

	sales_order = frappe.get_doc("Sales Order", sales_order_name)
	if sales_order.docstatus != 1:
		frappe.throw(f"Sales Order {sales_order_name} must be submitted before downstream mapping.")
	if sales_order.customer != spec["sales_order"]["customer"]:
		frappe.throw(
			f"Sales Order {sales_order_name} belongs to {sales_order.customer}, expected {spec['sales_order']['customer']}."
		)
	if sales_order.company != COMPANY_NAME:
		frappe.throw(f"Sales Order {sales_order_name} does not belong to {COMPANY_NAME}.")
	if float(sales_order.per_delivered or 0) > 0 or float(sales_order.per_billed or 0) > 0:
		frappe.throw(
			f"Sales Order {sales_order_name} already has downstream activity "
			f"(delivered={sales_order.per_delivered}, billed={sales_order.per_billed})."
		)

	delivery_note = make_delivery_note(sales_order.name)
	delivery_note.set_posting_time = 1
	delivery_note.posting_date = spec["delivery_note"]["posting_date"]
	delivery_note.posting_time = spec["delivery_note"]["posting_time"]
	delivery_note.lr_date = spec["delivery_note"]["posting_date"]
	delivery_note.remarks = spec["delivery_note"]["remarks"]
	delivery_note.flags.ignore_permissions = True
	delivery_note.insert(ignore_permissions=True)
	delivery_note.submit()

	sales_invoice = make_sales_invoice(delivery_note.name)
	sales_invoice.set_posting_time = 1
	sales_invoice.posting_date = spec["sales_invoice"]["posting_date"]
	sales_invoice.posting_time = spec["sales_invoice"]["posting_time"]
	sales_invoice.due_date = spec["sales_invoice"]["due_date"]
	sales_invoice.payment_terms_template = sales_order.payment_terms_template
	sales_invoice.remarks = spec["sales_invoice"]["remarks"]
	sales_invoice.flags.ignore_permissions = True
	sales_invoice.insert(ignore_permissions=True)
	sales_invoice.submit()

	sales_order = frappe.get_doc("Sales Order", sales_order_name)
	delivery_note = frappe.get_doc("Delivery Note", delivery_note.name)
	sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_1E_WHOLESALE_CREDIT_SALE_LABEL,
		"sales_order": _summarize_doc(sales_order),
		"delivery_note": _summarize_doc(delivery_note),
		"sales_invoice": _summarize_doc(sales_invoice),
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_1e_accessories_purchase_order(dry_run: bool = False) -> dict[str, Any]:
	"""Create the approved accessories Purchase Order with explicit pilot buying rates."""

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_1E_ACCESSORIES_PURCHASE["purchase_order"]
	item_rows = []

	for row in spec["items"]:
		rate = _get_pilot_purchase_rate(row["item_code"])
		item_rows.append(
			{
				"item_code": row["item_code"],
				"qty": row["qty"],
				"warehouse": row["warehouse"],
				"schedule_date": row["schedule_date"],
				"uom": "Nos",
				"conversion_factor": 1.0,
				"price_list_rate": rate,
				"rate": rate,
			}
		)

	doc = frappe.get_doc(
		{
			"doctype": "Purchase Order",
			"naming_series": spec["naming_series"],
			"supplier": spec["supplier"],
			"company": spec["company"],
			"transaction_date": spec["transaction_date"],
			"schedule_date": spec["schedule_date"],
			"currency": spec["currency"],
			"conversion_rate": spec["conversion_rate"],
			"buying_price_list": spec["buying_price_list"],
			"price_list_currency": spec["price_list_currency"],
			"plc_conversion_rate": spec["plc_conversion_rate"],
			"payment_terms_template": spec["payment_terms_template"],
			"set_warehouse": spec["set_warehouse"],
			"items": item_rows,
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	doc.submit()

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_1E_ACCESSORIES_PURCHASE_LABEL,
		"purchase_order": _summarize_doc(doc),
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def complete_miniphase_1e_accessories_purchase_from_order(
	purchase_order_name: str, dry_run: bool = False
) -> dict[str, Any]:
	"""Map a submitted pilot accessories Purchase Order through receipt and invoice."""

	from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt
	from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_1E_ACCESSORIES_PURCHASE

	purchase_order = frappe.get_doc("Purchase Order", purchase_order_name)
	if purchase_order.docstatus != 1:
		frappe.throw(f"Purchase Order {purchase_order_name} must be submitted before downstream mapping.")
	if purchase_order.supplier != spec["purchase_order"]["supplier"]:
		frappe.throw(
			f"Purchase Order {purchase_order_name} belongs to {purchase_order.supplier}, expected {spec['purchase_order']['supplier']}."
		)
	if purchase_order.company != COMPANY_NAME:
		frappe.throw(f"Purchase Order {purchase_order_name} does not belong to {COMPANY_NAME}.")
	if float(purchase_order.per_received or 0) > 0 or float(purchase_order.per_billed or 0) > 0:
		frappe.throw(
			f"Purchase Order {purchase_order_name} already has downstream activity "
			f"(received={purchase_order.per_received}, billed={purchase_order.per_billed})."
		)

	purchase_receipt = make_purchase_receipt(purchase_order.name)
	purchase_receipt.set_posting_time = 1
	purchase_receipt.posting_date = spec["purchase_receipt"]["posting_date"]
	purchase_receipt.posting_time = spec["purchase_receipt"]["posting_time"]
	purchase_receipt.supplier_delivery_note = spec["purchase_receipt"]["supplier_delivery_note"]
	purchase_receipt.remarks = spec["purchase_receipt"]["remarks"]
	purchase_receipt.flags.ignore_permissions = True
	purchase_receipt.insert(ignore_permissions=True)
	purchase_receipt.submit()

	purchase_invoice = make_purchase_invoice(purchase_receipt.name)
	purchase_invoice.set_posting_time = 1
	purchase_invoice.posting_date = spec["purchase_invoice"]["posting_date"]
	purchase_invoice.posting_time = spec["purchase_invoice"]["posting_time"]
	purchase_invoice.bill_no = spec["purchase_invoice"]["bill_no"]
	purchase_invoice.bill_date = spec["purchase_invoice"]["bill_date"]
	purchase_invoice.payment_terms_template = purchase_order.payment_terms_template
	purchase_invoice.due_date = spec["purchase_invoice"]["due_date"]
	for row in purchase_invoice.payment_schedule or []:
		row.due_date = spec["purchase_invoice"]["due_date"]
	purchase_invoice.remarks = spec["purchase_invoice"]["remarks"]
	purchase_invoice.flags.ignore_permissions = True
	purchase_invoice.insert(ignore_permissions=True)
	purchase_invoice.submit()

	purchase_order = frappe.get_doc("Purchase Order", purchase_order_name)
	purchase_receipt = frappe.get_doc("Purchase Receipt", purchase_receipt.name)
	purchase_invoice = frappe.get_doc("Purchase Invoice", purchase_invoice.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_1E_ACCESSORIES_PURCHASE_LABEL,
		"purchase_order": _summarize_doc(purchase_order),
		"purchase_receipt": _summarize_doc(purchase_receipt),
		"purchase_invoice": _summarize_doc(purchase_invoice),
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def preview_miniphase_1e_accessories_purchase_invoice_mapping(
	purchase_order_name: str, dry_run: bool = True
) -> dict[str, Any]:
	"""Preview the mapped purchase invoice fields before insert for debugging."""

	from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt
	from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_1E_ACCESSORIES_PURCHASE
	purchase_order = frappe.get_doc("Purchase Order", purchase_order_name)

	purchase_receipt = make_purchase_receipt(purchase_order.name)
	purchase_receipt.set_posting_time = 1
	purchase_receipt.posting_date = spec["purchase_receipt"]["posting_date"]
	purchase_receipt.posting_time = spec["purchase_receipt"]["posting_time"]
	purchase_receipt.supplier_delivery_note = spec["purchase_receipt"]["supplier_delivery_note"]
	purchase_receipt.remarks = spec["purchase_receipt"]["remarks"]
	purchase_receipt.flags.ignore_permissions = True
	purchase_receipt.insert(ignore_permissions=True)
	purchase_receipt.submit()

	purchase_invoice = make_purchase_invoice(purchase_receipt.name)
	purchase_invoice.set_posting_time = 1
	purchase_invoice.posting_date = spec["purchase_invoice"]["posting_date"]
	purchase_invoice.posting_time = spec["purchase_invoice"]["posting_time"]
	purchase_invoice.bill_no = spec["purchase_invoice"]["bill_no"]
	purchase_invoice.bill_date = spec["purchase_invoice"]["bill_date"]
	purchase_invoice.payment_terms_template = purchase_order.payment_terms_template
	purchase_invoice.due_date = spec["purchase_invoice"]["due_date"]
	for row in purchase_invoice.payment_schedule or []:
		row.due_date = spec["purchase_invoice"]["due_date"]
	purchase_invoice.remarks = spec["purchase_invoice"]["remarks"]

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_1E_ACCESSORIES_PURCHASE_LABEL,
		"purchase_order": purchase_order.name,
		"purchase_receipt_preview": {
			"name": purchase_receipt.name,
			"posting_date": purchase_receipt.posting_date,
			"grand_total": purchase_receipt.grand_total,
		},
		"purchase_invoice_preview": {
			"posting_date": purchase_invoice.posting_date,
			"bill_date": purchase_invoice.bill_date,
			"due_date": purchase_invoice.due_date,
			"payment_terms_template": purchase_invoice.payment_terms_template,
			"payment_schedule": [
				{
					"payment_term": row.payment_term,
					"due_date": row.due_date,
					"invoice_portion": row.invoice_portion,
					"payment_amount": row.payment_amount,
				}
				for row in purchase_invoice.payment_schedule
			],
		},
	}

	if dry_run:
		frappe.db.rollback()

	return result


def create_miniphase_1f_partial_supplier_payment(dry_run: bool = False) -> dict[str, Any]:
	"""Create a partial supplier payment against the pilot accessories invoice."""

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_1F_PARTIAL_SUPPLIER_PAYMENT
	purchase_invoice = frappe.get_doc("Purchase Invoice", spec["purchase_invoice"])

	if purchase_invoice.docstatus != 1:
		frappe.throw(f"Purchase Invoice {purchase_invoice.name} must be submitted before payment.")
	if float(purchase_invoice.outstanding_amount or 0) <= 0:
		frappe.throw(f"Purchase Invoice {purchase_invoice.name} has no outstanding amount left.")

	payment_entry = get_payment_entry("Purchase Invoice", purchase_invoice.name)
	partial_amount = float(spec["paid_amount"])
	if partial_amount > float(purchase_invoice.outstanding_amount):
		frappe.throw(
			f"Configured partial payment {partial_amount} exceeds outstanding {purchase_invoice.outstanding_amount} "
			f"for {purchase_invoice.name}."
		)

	payment_entry.posting_date = spec["posting_date"]
	payment_entry.paid_from = spec["paid_from"]
	payment_entry.reference_no = spec["reference_no"]
	payment_entry.reference_date = spec["reference_date"]
	payment_entry.paid_amount = partial_amount
	payment_entry.received_amount = partial_amount
	payment_entry.source_exchange_rate = 1.0
	payment_entry.target_exchange_rate = 1.0
	payment_entry.remarks = (
		f"{spec['remarks']}\n"
		f"Amount MMK {partial_amount} paid against Purchase Invoice {purchase_invoice.name}"
	)
	if payment_entry.references:
		payment_entry.references[0].allocated_amount = partial_amount

	payment_entry.flags.ignore_permissions = True
	payment_entry.insert(ignore_permissions=True)
	payment_entry.submit()

	purchase_invoice = frappe.get_doc("Purchase Invoice", purchase_invoice.name)
	payment_entry = frappe.get_doc("Payment Entry", payment_entry.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_1F_SUPPLIER_PAYMENT_LABEL,
		"purchase_invoice": _summarize_doc(purchase_invoice),
		"payment_entry": {
			"doctype": payment_entry.doctype,
			"name": payment_entry.name,
			"docstatus": payment_entry.docstatus,
			"status": getattr(payment_entry, "status", None),
			"posting_date": payment_entry.posting_date,
			"mode_of_payment": payment_entry.mode_of_payment,
			"paid_from": payment_entry.paid_from,
			"paid_to": payment_entry.paid_to,
			"paid_amount": payment_entry.paid_amount,
			"received_amount": payment_entry.received_amount,
			"reference_no": payment_entry.reference_no,
			"references": [
				{
					"reference_doctype": row.reference_doctype,
					"reference_name": row.reference_name,
					"allocated_amount": row.allocated_amount,
				}
				for row in payment_entry.references
			],
		},
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_1f_partial_customer_collection(dry_run: bool = False) -> dict[str, Any]:
	"""Create a partial customer collection against the pilot wholesale invoice."""

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_1F_PARTIAL_CUSTOMER_COLLECTION
	sales_invoice = frappe.get_doc("Sales Invoice", spec["sales_invoice"])

	if sales_invoice.docstatus != 1:
		frappe.throw(f"Sales Invoice {sales_invoice.name} must be submitted before collection.")
	if float(sales_invoice.outstanding_amount or 0) <= 0:
		frappe.throw(f"Sales Invoice {sales_invoice.name} has no outstanding amount left.")

	payment_entry = get_payment_entry(
		"Sales Invoice",
		sales_invoice.name,
		bank_account=spec["paid_to"],
		reference_date=spec["reference_date"],
	)
	partial_amount = float(spec["received_amount"])
	if partial_amount > float(sales_invoice.outstanding_amount):
		frappe.throw(
			f"Configured partial collection {partial_amount} exceeds outstanding {sales_invoice.outstanding_amount} "
			f"for {sales_invoice.name}."
		)

	payment_entry.posting_date = spec["posting_date"]
	payment_entry.paid_to = spec["paid_to"]
	payment_entry.mode_of_payment = spec["mode_of_payment"]
	payment_entry.reference_no = spec["reference_no"]
	payment_entry.reference_date = spec["reference_date"]
	payment_entry.paid_amount = partial_amount
	payment_entry.received_amount = partial_amount
	payment_entry.source_exchange_rate = 1.0
	payment_entry.target_exchange_rate = 1.0
	payment_entry.remarks = (
		f"{spec['remarks']}\n"
		f"Amount MMK {partial_amount} received against Sales Invoice {sales_invoice.name}"
	)
	if payment_entry.references:
		payment_entry.references[0].allocated_amount = partial_amount

	payment_entry.flags.ignore_permissions = True
	payment_entry.insert(ignore_permissions=True)
	payment_entry.submit()

	sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice.name)
	payment_entry = frappe.get_doc("Payment Entry", payment_entry.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_1F_CUSTOMER_COLLECTION_LABEL,
		"sales_invoice": _summarize_doc(sales_invoice),
		"payment_entry": {
			"doctype": payment_entry.doctype,
			"name": payment_entry.name,
			"docstatus": payment_entry.docstatus,
			"status": getattr(payment_entry, "status", None),
			"posting_date": payment_entry.posting_date,
			"mode_of_payment": payment_entry.mode_of_payment,
			"paid_from": payment_entry.paid_from,
			"paid_to": payment_entry.paid_to,
			"paid_amount": payment_entry.paid_amount,
			"received_amount": payment_entry.received_amount,
			"reference_no": payment_entry.reference_no,
			"references": [
				{
					"reference_doctype": row.reference_doctype,
					"reference_name": row.reference_name,
					"allocated_amount": row.allocated_amount,
				}
				for row in payment_entry.references
			],
		},
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_1f_wholesale_accessory_sales_return(dry_run: bool = False) -> dict[str, Any]:
	"""Create a controlled wholesale sales return and matching credit note for the pilot invoice."""

	from erpnext.controllers.sales_and_purchase_return import make_return_doc

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_1F_WHOLESALE_ACCESSORY_RETURN
	delivery_note = frappe.get_doc("Delivery Note", spec["delivery_note"])
	sales_invoice = frappe.get_doc("Sales Invoice", spec["sales_invoice"])

	if delivery_note.docstatus != 1:
		frappe.throw(f"Delivery Note {delivery_note.name} must be submitted before return.")
	if sales_invoice.docstatus != 1:
		frappe.throw(f"Sales Invoice {sales_invoice.name} must be submitted before return.")
	if delivery_note.customer != sales_invoice.customer:
		frappe.throw(
			f"Delivery Note {delivery_note.name} customer {delivery_note.customer} does not match "
			f"Sales Invoice {sales_invoice.name} customer {sales_invoice.customer}."
		)

	return_qty = float(spec["qty"])
	if return_qty <= 0:
		frappe.throw("Return quantity must be positive.")

	delivery_return = make_return_doc("Delivery Note", delivery_note.name)
	_sales_return_trimmed = False
	for row in list(delivery_return.items):
		if row.item_code != spec["item_code"]:
			delivery_return.remove(row)
			continue
		row.qty = -1 * return_qty
		row.stock_qty = -1 * return_qty * float(row.conversion_factor or 1.0)
		row.warehouse = spec["warehouse"]
		_sales_return_trimmed = True

	if not _sales_return_trimmed or not delivery_return.items:
		frappe.throw(
			f"Item {spec['item_code']} not found on Delivery Note {delivery_note.name} for return mapping."
		)

	delivery_return.set_posting_time = 1
	delivery_return.posting_date = spec["posting_date"]
	delivery_return.posting_time = spec["posting_time"]
	delivery_return.lr_date = spec["posting_date"]
	delivery_return.remarks = spec["remarks_delivery"]
	delivery_return.run_method("calculate_taxes_and_totals")
	delivery_return.flags.ignore_permissions = True
	delivery_return.insert(ignore_permissions=True)
	delivery_return.submit()

	sales_return = make_return_doc("Sales Invoice", sales_invoice.name)
	_invoice_return_trimmed = False
	for row in list(sales_return.items):
		if row.item_code != spec["item_code"]:
			sales_return.remove(row)
			continue
		row.qty = -1 * return_qty
		row.stock_qty = -1 * return_qty * float(row.conversion_factor or 1.0)
		row.warehouse = spec["warehouse"]
		_invoice_return_trimmed = True

	if not _invoice_return_trimmed or not sales_return.items:
		frappe.throw(
			f"Item {spec['item_code']} not found on Sales Invoice {sales_invoice.name} for return mapping."
		)

	sales_return.set_posting_time = 1
	sales_return.posting_date = spec["posting_date"]
	sales_return.posting_time = spec["posting_time"]
	sales_return.due_date = spec["posting_date"]
	sales_return.payment_terms_template = ""
	sales_return.set("payment_schedule", [])
	sales_return.remarks = spec["remarks_invoice"]
	sales_return.run_method("calculate_taxes_and_totals")
	sales_return.flags.ignore_permissions = True
	sales_return.insert(ignore_permissions=True)
	sales_return.submit()

	delivery_return = frappe.get_doc("Delivery Note", delivery_return.name)
	sales_return = frappe.get_doc("Sales Invoice", sales_return.name)
	sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_1F_SALES_RETURN_LABEL,
		"delivery_return": _summarize_doc(delivery_return),
		"sales_return": _summarize_doc(sales_return),
		"source_sales_invoice": _summarize_doc(sales_invoice),
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_2a_additional_wholesale_sales_order(dry_run: bool = False) -> dict[str, Any]:
	"""Create the first post-pilot additional wholesale Sales Order with explicit MMOB rates."""

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_2A_ADDITIONAL_WHOLESALE_SALE["sales_order"]
	item_rows = []

	for row in spec["items"]:
		rate = _get_pilot_price_rate(row["item_code"], spec["selling_price_list"])
		item_rows.append(
			{
				"item_code": row["item_code"],
				"qty": row["qty"],
				"warehouse": row["warehouse"],
				"delivery_date": row["delivery_date"],
				"uom": "Nos",
				"conversion_factor": 1.0,
				"price_list_rate": rate,
				"rate": rate,
			}
		)

	doc = frappe.get_doc(
		{
			"doctype": "Sales Order",
			"naming_series": spec["naming_series"],
			"customer": spec["customer"],
			"company": spec["company"],
			"transaction_date": spec["transaction_date"],
			"delivery_date": spec["delivery_date"],
			"po_no": spec["po_no"],
			"po_date": spec["po_date"],
			"currency": spec["currency"],
			"conversion_rate": spec["conversion_rate"],
			"selling_price_list": spec["selling_price_list"],
			"price_list_currency": spec["price_list_currency"],
			"plc_conversion_rate": spec["plc_conversion_rate"],
			"payment_terms_template": spec["payment_terms_template"],
			"set_warehouse": spec["set_warehouse"],
			"items": item_rows,
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	doc.submit()

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_2A_ADDITIONAL_WHOLESALE_SALE_LABEL,
		"sales_order": _summarize_doc(doc),
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def complete_miniphase_2a_additional_wholesale_sale_from_sales_order(
	sales_order_name: str, dry_run: bool = False
) -> dict[str, Any]:
	"""Map a submitted additional wholesale Sales Order through delivery and invoice."""

	from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
	from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_2A_ADDITIONAL_WHOLESALE_SALE

	sales_order = frappe.get_doc("Sales Order", sales_order_name)
	if sales_order.docstatus != 1:
		frappe.throw(f"Sales Order {sales_order_name} must be submitted before downstream mapping.")
	if sales_order.customer != spec["sales_order"]["customer"]:
		frappe.throw(
			f"Sales Order {sales_order_name} belongs to {sales_order.customer}, expected {spec['sales_order']['customer']}."
		)
	if sales_order.company != COMPANY_NAME:
		frappe.throw(f"Sales Order {sales_order_name} does not belong to {COMPANY_NAME}.")
	if float(sales_order.per_delivered or 0) > 0 or float(sales_order.per_billed or 0) > 0:
		frappe.throw(
			f"Sales Order {sales_order_name} already has downstream activity "
			f"(delivered={sales_order.per_delivered}, billed={sales_order.per_billed})."
		)

	delivery_note = make_delivery_note(sales_order.name)
	delivery_note.set_posting_time = 1
	delivery_note.posting_date = spec["delivery_note"]["posting_date"]
	delivery_note.posting_time = spec["delivery_note"]["posting_time"]
	delivery_note.lr_date = spec["delivery_note"]["posting_date"]
	delivery_note.remarks = spec["delivery_note"]["remarks"]
	delivery_note.flags.ignore_permissions = True
	delivery_note.insert(ignore_permissions=True)
	delivery_note.submit()

	sales_invoice = make_sales_invoice(delivery_note.name)
	sales_invoice.set_posting_time = 1
	sales_invoice.posting_date = spec["sales_invoice"]["posting_date"]
	sales_invoice.posting_time = spec["sales_invoice"]["posting_time"]
	sales_invoice.due_date = spec["sales_invoice"]["due_date"]
	sales_invoice.payment_terms_template = sales_order.payment_terms_template
	sales_invoice.remarks = spec["sales_invoice"]["remarks"]
	sales_invoice.flags.ignore_permissions = True
	sales_invoice.insert(ignore_permissions=True)
	sales_invoice.submit()

	sales_order = frappe.get_doc("Sales Order", sales_order_name)
	delivery_note = frappe.get_doc("Delivery Note", delivery_note.name)
	sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_2A_ADDITIONAL_WHOLESALE_SALE_LABEL,
		"sales_order": _summarize_doc(sales_order),
		"delivery_note": _summarize_doc(delivery_note),
		"sales_invoice": _summarize_doc(sales_invoice),
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_2b_branch_transfer(dry_run: bool = False) -> dict[str, Any]:
	"""Create the first bounded router release into Mandalay after stockout."""

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_2B_BRANCH_TRANSFER["stock_entry"]
	item_rows = []

	for row in spec["items"]:
		item_rows.append(
			{
				"item_code": row["item_code"],
				"qty": row["qty"],
				"s_warehouse": row["s_warehouse"],
				"t_warehouse": row["t_warehouse"],
				"uom": "Nos",
				"stock_uom": "Nos",
				"conversion_factor": 1.0,
			}
		)

	doc = frappe.get_doc(
		{
			"doctype": "Stock Entry",
			"naming_series": spec["naming_series"],
			"company": spec["company"],
			"posting_date": spec["posting_date"],
			"posting_time": spec["posting_time"],
			"set_posting_time": 1,
			"stock_entry_type": spec["stock_entry_type"],
			"purpose": spec["purpose"],
			"from_warehouse": spec["from_warehouse"],
			"to_warehouse": spec["to_warehouse"],
			"remarks": spec["remarks"],
			"items": item_rows,
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	doc.submit()

	doc = frappe.get_doc("Stock Entry", doc.name)
	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_2B_BRANCH_TRANSFER_LABEL,
		"stock_entry": {
			**_summarize_doc(doc),
			"stock_entry_type": doc.stock_entry_type,
			"purpose": doc.purpose,
			"from_warehouse": doc.from_warehouse,
			"to_warehouse": doc.to_warehouse,
		},
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_2c_aged_customer_collection(dry_run: bool = False) -> dict[str, Any]:
	"""Create a rounded aged AR collection for the 35th Street wholesale account."""

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_2C_AGED_COLLECTION
	sales_invoice = frappe.get_doc("Sales Invoice", spec["sales_invoice"])

	if sales_invoice.docstatus != 1:
		frappe.throw(f"Sales Invoice {sales_invoice.name} must be submitted before collection.")
	if float(sales_invoice.outstanding_amount or 0) <= 0:
		frappe.throw(f"Sales Invoice {sales_invoice.name} has no outstanding amount left.")

	payment_entry = get_payment_entry(
		"Sales Invoice",
		sales_invoice.name,
		bank_account=spec["paid_to"],
		reference_date=spec["reference_date"],
	)
	partial_amount = float(spec["received_amount"])
	if partial_amount > float(sales_invoice.outstanding_amount):
		frappe.throw(
			f"Configured partial collection {partial_amount} exceeds outstanding {sales_invoice.outstanding_amount} "
			f"for {sales_invoice.name}."
		)

	payment_entry.posting_date = spec["posting_date"]
	payment_entry.paid_to = spec["paid_to"]
	payment_entry.mode_of_payment = spec["mode_of_payment"]
	payment_entry.reference_no = spec["reference_no"]
	payment_entry.reference_date = spec["reference_date"]
	payment_entry.paid_amount = partial_amount
	payment_entry.received_amount = partial_amount
	payment_entry.source_exchange_rate = 1.0
	payment_entry.target_exchange_rate = 1.0
	payment_entry.remarks = (
		f"{spec['remarks']}\n"
		f"Amount MMK {partial_amount} received against Sales Invoice {sales_invoice.name}"
	)
	if payment_entry.references:
		payment_entry.references[0].allocated_amount = partial_amount

	payment_entry.flags.ignore_permissions = True
	payment_entry.insert(ignore_permissions=True)
	payment_entry.submit()

	sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice.name)
	payment_entry = frappe.get_doc("Payment Entry", payment_entry.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_2C_AGED_COLLECTION_LABEL,
		"sales_invoice": _summarize_doc(sales_invoice),
		"payment_entry": {
			"doctype": payment_entry.doctype,
			"name": payment_entry.name,
			"docstatus": payment_entry.docstatus,
			"status": getattr(payment_entry, "status", None),
			"posting_date": payment_entry.posting_date,
			"mode_of_payment": payment_entry.mode_of_payment,
			"paid_from": payment_entry.paid_from,
			"paid_to": payment_entry.paid_to,
			"paid_amount": payment_entry.paid_amount,
			"received_amount": payment_entry.received_amount,
			"reference_no": payment_entry.reference_no,
			"references": [
				{
					"reference_doctype": row.reference_doctype,
					"reference_name": row.reference_name,
					"allocated_amount": row.allocated_amount,
				}
				for row in payment_entry.references
			],
		},
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_2d_importer_ap_payment(dry_run: bool = False) -> dict[str, Any]:
	"""Create a rounded staged payment against an overdue Myanmar Tech import payable."""

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_2D_IMPORTER_AP_PAYMENT
	purchase_invoice = frappe.get_doc("Purchase Invoice", spec["purchase_invoice"])

	if purchase_invoice.docstatus != 1:
		frappe.throw(f"Purchase Invoice {purchase_invoice.name} must be submitted before payment.")
	if float(purchase_invoice.outstanding_amount or 0) <= 0:
		frappe.throw(f"Purchase Invoice {purchase_invoice.name} has no outstanding amount left.")

	payment_entry = get_payment_entry("Purchase Invoice", purchase_invoice.name)
	partial_amount = float(spec["paid_amount"])
	if partial_amount > float(purchase_invoice.outstanding_amount):
		frappe.throw(
			f"Configured partial payment {partial_amount} exceeds outstanding {purchase_invoice.outstanding_amount} "
			f"for {purchase_invoice.name}."
		)

	payment_entry.posting_date = spec["posting_date"]
	payment_entry.paid_from = spec["paid_from"]
	payment_entry.mode_of_payment = spec["mode_of_payment"]
	payment_entry.reference_no = spec["reference_no"]
	payment_entry.reference_date = spec["reference_date"]
	payment_entry.paid_amount = partial_amount
	payment_entry.received_amount = partial_amount
	payment_entry.source_exchange_rate = 1.0
	payment_entry.target_exchange_rate = 1.0
	payment_entry.remarks = (
		f"{spec['remarks']}\n"
		f"Amount MMK {partial_amount} paid against Purchase Invoice {purchase_invoice.name}"
	)
	if payment_entry.references:
		payment_entry.references[0].allocated_amount = partial_amount

	payment_entry.flags.ignore_permissions = True
	payment_entry.insert(ignore_permissions=True)
	payment_entry.submit()

	purchase_invoice = frappe.get_doc("Purchase Invoice", purchase_invoice.name)
	payment_entry = frappe.get_doc("Payment Entry", payment_entry.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_2D_IMPORTER_AP_PAYMENT_LABEL,
		"purchase_invoice": _summarize_doc(purchase_invoice),
		"payment_entry": {
			"doctype": payment_entry.doctype,
			"name": payment_entry.name,
			"docstatus": payment_entry.docstatus,
			"status": getattr(payment_entry, "status", None),
			"posting_date": payment_entry.posting_date,
			"mode_of_payment": payment_entry.mode_of_payment,
			"paid_from": payment_entry.paid_from,
			"paid_to": payment_entry.paid_to,
			"paid_amount": payment_entry.paid_amount,
			"received_amount": payment_entry.received_amount,
			"reference_no": payment_entry.reference_no,
			"references": [
				{
					"reference_doctype": row.reference_doctype,
					"reference_name": row.reference_name,
					"allocated_amount": row.allocated_amount,
				}
				for row in payment_entry.references
			],
		},
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_4b_capital_npt_aged_collection(dry_run: bool = False) -> dict[str, Any]:
	"""Create a rounded late-April collection against Capital Telecom's oldest large FY2526-Q4 overdue invoice."""

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_4B_CAPITAL_NPT_AGED_COLLECTION
	sales_invoice = frappe.get_doc("Sales Invoice", spec["sales_invoice"])

	if sales_invoice.docstatus != 1:
		frappe.throw(f"Sales Invoice {sales_invoice.name} must be submitted before collection.")
	if float(sales_invoice.outstanding_amount or 0) <= 0:
		frappe.throw(f"Sales Invoice {sales_invoice.name} has no outstanding amount left.")

	payment_entry = get_payment_entry(
		"Sales Invoice",
		sales_invoice.name,
		bank_account=spec["paid_to"],
		reference_date=spec["reference_date"],
	)
	partial_amount = float(spec["received_amount"])
	if partial_amount > float(sales_invoice.outstanding_amount):
		frappe.throw(
			f"Configured partial collection {partial_amount} exceeds outstanding {sales_invoice.outstanding_amount} "
			f"for {sales_invoice.name}."
		)

	payment_entry.posting_date = spec["posting_date"]
	payment_entry.paid_to = spec["paid_to"]
	payment_entry.mode_of_payment = spec["mode_of_payment"]
	payment_entry.reference_no = spec["reference_no"]
	payment_entry.reference_date = spec["reference_date"]
	payment_entry.paid_amount = partial_amount
	payment_entry.received_amount = partial_amount
	payment_entry.source_exchange_rate = 1.0
	payment_entry.target_exchange_rate = 1.0
	payment_entry.remarks = (
		f"{spec['remarks']}\n"
		f"Amount MMK {partial_amount} received against Sales Invoice {sales_invoice.name}"
	)
	if payment_entry.references:
		payment_entry.references[0].allocated_amount = partial_amount

	payment_entry.flags.ignore_permissions = True
	payment_entry.insert(ignore_permissions=True)
	payment_entry.submit()

	sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice.name)
	payment_entry = frappe.get_doc("Payment Entry", payment_entry.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_4B_CAPITAL_NPT_AGED_COLLECTION_LABEL,
		"sales_invoice": _summarize_doc(sales_invoice),
		"payment_entry": {
			"doctype": payment_entry.doctype,
			"name": payment_entry.name,
			"docstatus": payment_entry.docstatus,
			"status": getattr(payment_entry, "status", None),
			"posting_date": payment_entry.posting_date,
			"mode_of_payment": payment_entry.mode_of_payment,
			"paid_from": payment_entry.paid_from,
			"paid_to": payment_entry.paid_to,
			"paid_amount": payment_entry.paid_amount,
			"received_amount": payment_entry.received_amount,
			"reference_no": payment_entry.reference_no,
			"references": [
				{
					"reference_doctype": row.reference_doctype,
					"reference_name": row.reference_name,
					"allocated_amount": row.allocated_amount,
				}
				for row in payment_entry.references
			],
		},
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_4c_golden_dragon_aged_ap_payment(dry_run: bool = False) -> dict[str, Any]:
	"""Create a rounded late-April payment against a major Golden Dragon January handset replenishment invoice."""

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_4C_GOLDEN_DRAGON_AGED_AP_PAYMENT
	purchase_invoice = frappe.get_doc("Purchase Invoice", spec["purchase_invoice"])

	if purchase_invoice.docstatus != 1:
		frappe.throw(f"Purchase Invoice {purchase_invoice.name} must be submitted before payment.")
	if float(purchase_invoice.outstanding_amount or 0) <= 0:
		frappe.throw(f"Purchase Invoice {purchase_invoice.name} has no outstanding amount left.")

	payment_entry = get_payment_entry("Purchase Invoice", purchase_invoice.name)
	partial_amount = float(spec["paid_amount"])
	if partial_amount > float(purchase_invoice.outstanding_amount):
		frappe.throw(
			f"Configured partial payment {partial_amount} exceeds outstanding {purchase_invoice.outstanding_amount} "
			f"for {purchase_invoice.name}."
		)

	payment_entry.posting_date = spec["posting_date"]
	payment_entry.paid_from = spec["paid_from"]
	payment_entry.mode_of_payment = spec["mode_of_payment"]
	payment_entry.reference_no = spec["reference_no"]
	payment_entry.reference_date = spec["reference_date"]
	payment_entry.paid_amount = partial_amount
	payment_entry.received_amount = partial_amount
	payment_entry.source_exchange_rate = 1.0
	payment_entry.target_exchange_rate = 1.0
	payment_entry.remarks = (
		f"{spec['remarks']}\n"
		f"Amount MMK {partial_amount} paid against Purchase Invoice {purchase_invoice.name}"
	)
	if payment_entry.references:
		payment_entry.references[0].allocated_amount = partial_amount

	payment_entry.flags.ignore_permissions = True
	payment_entry.insert(ignore_permissions=True)
	payment_entry.submit()

	purchase_invoice = frappe.get_doc("Purchase Invoice", purchase_invoice.name)
	payment_entry = frappe.get_doc("Payment Entry", payment_entry.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_4C_GOLDEN_DRAGON_AGED_AP_PAYMENT_LABEL,
		"purchase_invoice": _summarize_doc(purchase_invoice),
		"payment_entry": {
			"doctype": payment_entry.doctype,
			"name": payment_entry.name,
			"docstatus": payment_entry.docstatus,
			"status": getattr(payment_entry, "status", None),
			"posting_date": payment_entry.posting_date,
			"mode_of_payment": payment_entry.mode_of_payment,
			"paid_from": payment_entry.paid_from,
			"paid_to": payment_entry.paid_to,
			"paid_amount": payment_entry.paid_amount,
			"received_amount": payment_entry.received_amount,
			"reference_no": payment_entry.reference_no,
			"references": [
				{
					"reference_doctype": row.reference_doctype,
					"reference_name": row.reference_name,
					"allocated_amount": row.allocated_amount,
				}
				for row in payment_entry.references
			],
		},
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_2e_purchase_return(dry_run: bool = False) -> dict[str, Any]:
	"""Create a controlled supplier return and matching debit note for the recent Sunflower purchase."""

	from erpnext.controllers.sales_and_purchase_return import make_return_doc

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_2E_PURCHASE_RETURN
	purchase_receipt = frappe.get_doc("Purchase Receipt", spec["purchase_receipt"])
	purchase_invoice = frappe.get_doc("Purchase Invoice", spec["purchase_invoice"])

	if purchase_receipt.docstatus != 1:
		frappe.throw(f"Purchase Receipt {purchase_receipt.name} must be submitted before return.")
	if purchase_invoice.docstatus != 1:
		frappe.throw(f"Purchase Invoice {purchase_invoice.name} must be submitted before return.")
	if purchase_receipt.supplier != purchase_invoice.supplier:
		frappe.throw(
			f"Purchase Receipt {purchase_receipt.name} supplier {purchase_receipt.supplier} does not match "
			f"Purchase Invoice {purchase_invoice.name} supplier {purchase_invoice.supplier}."
		)

	return_qty = float(spec["qty"])
	if return_qty <= 0:
		frappe.throw("Return quantity must be positive.")

	receipt_return = make_return_doc("Purchase Receipt", purchase_receipt.name)
	_receipt_return_trimmed = False
	for row in list(receipt_return.items):
		if row.item_code != spec["item_code"]:
			receipt_return.remove(row)
			continue
		row.qty = -1 * return_qty
		row.received_qty = -1 * return_qty
		row.received_stock_qty = -1 * return_qty * float(row.conversion_factor or 1.0)
		row.stock_qty = -1 * return_qty * float(row.conversion_factor or 1.0)
		row.warehouse = spec["warehouse"]
		_receipt_return_trimmed = True

	if not _receipt_return_trimmed or not receipt_return.items:
		frappe.throw(
			f"Item {spec['item_code']} not found on Purchase Receipt {purchase_receipt.name} for return mapping."
		)

	receipt_return.set_posting_time = 1
	receipt_return.posting_date = spec["posting_date"]
	receipt_return.posting_time = spec["posting_time"]
	receipt_return.remarks = spec["remarks_receipt"]
	receipt_return.run_method("calculate_taxes_and_totals")
	receipt_return.flags.ignore_permissions = True
	receipt_return.insert(ignore_permissions=True)
	receipt_return.submit()

	invoice_return = make_return_doc("Purchase Invoice", purchase_invoice.name)
	_invoice_return_trimmed = False
	for row in list(invoice_return.items):
		if row.item_code != spec["item_code"]:
			invoice_return.remove(row)
			continue
		row.qty = -1 * return_qty
		row.stock_qty = -1 * return_qty * float(row.conversion_factor or 1.0)
		row.warehouse = spec["warehouse"]
		_invoice_return_trimmed = True

	if not _invoice_return_trimmed or not invoice_return.items:
		frappe.throw(
			f"Item {spec['item_code']} not found on Purchase Invoice {purchase_invoice.name} for return mapping."
		)

	invoice_return.set_posting_time = 1
	invoice_return.posting_date = spec["posting_date"]
	invoice_return.posting_time = spec["posting_time"]
	invoice_return.due_date = spec["posting_date"]
	invoice_return.payment_terms_template = ""
	invoice_return.set("payment_schedule", [])
	invoice_return.remarks = spec["remarks_invoice"]
	invoice_return.run_method("calculate_taxes_and_totals")
	invoice_return.flags.ignore_permissions = True
	invoice_return.insert(ignore_permissions=True)
	invoice_return.submit()

	receipt_return = frappe.get_doc("Purchase Receipt", receipt_return.name)
	invoice_return = frappe.get_doc("Purchase Invoice", invoice_return.name)
	purchase_invoice = frappe.get_doc("Purchase Invoice", purchase_invoice.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_2E_PURCHASE_RETURN_LABEL,
		"purchase_receipt_return": _summarize_doc(receipt_return),
		"purchase_invoice_return": _summarize_doc(invoice_return),
		"source_purchase_invoice": _summarize_doc(purchase_invoice),
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_2f_replacement_receipt(dry_run: bool = False) -> dict[str, Any]:
	"""Receive replacement stock against the open balance left by the recent supplier return."""

	from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_2F_REPLACEMENT_RECEIPT
	purchase_order = frappe.get_doc("Purchase Order", spec["purchase_order"])
	source_return_receipt = frappe.get_doc("Purchase Receipt", spec["source_return_receipt"])
	source_return_invoice = frappe.get_doc("Purchase Invoice", spec["source_return_invoice"])

	if purchase_order.docstatus != 1:
		frappe.throw(f"Purchase Order {purchase_order.name} must be submitted before replacement receipt.")
	if source_return_receipt.docstatus != 1 or not int(source_return_receipt.is_return or 0):
		frappe.throw(
			f"Purchase Receipt {source_return_receipt.name} must be a submitted supplier return before replacement receipt."
		)
	if source_return_invoice.docstatus != 1 or not int(source_return_invoice.is_return or 0):
		frappe.throw(
			f"Purchase Invoice {source_return_invoice.name} must be a submitted supplier debit note before replacement receipt."
		)
	if purchase_order.supplier != source_return_receipt.supplier or purchase_order.supplier != source_return_invoice.supplier:
		frappe.throw(
			f"Supplier mismatch between Purchase Order {purchase_order.name} and the linked supplier-return documents."
		)
	if float(purchase_order.per_received or 0) >= 100:
		frappe.throw(f"Purchase Order {purchase_order.name} is already fully received.")
	if float(purchase_order.per_billed or 0) < 100:
		frappe.throw(
			f"Purchase Order {purchase_order.name} is not fully billed yet; Mini-Phase 2F expects a replacement-only receipt."
		)

	purchase_order_row = next((row for row in purchase_order.items if row.item_code == spec["item_code"]), None)
	if not purchase_order_row:
		frappe.throw(f"Item {spec['item_code']} not found on Purchase Order {purchase_order.name}.")

	outstanding_qty = float(purchase_order_row.qty or 0) - float(purchase_order_row.received_qty or 0)
	replacement_qty = float(spec["qty"])
	if replacement_qty <= 0:
		frappe.throw("Replacement quantity must be positive.")
	if replacement_qty > outstanding_qty:
		frappe.throw(
			f"Replacement quantity {replacement_qty} exceeds open Purchase Order quantity {outstanding_qty} "
			f"for item {spec['item_code']} on {purchase_order.name}."
		)

	purchase_receipt = make_purchase_receipt(purchase_order.name)
	item_mapped = False
	for row in list(purchase_receipt.items):
		if row.item_code != spec["item_code"]:
			purchase_receipt.remove(row)
			continue
		row.qty = replacement_qty
		row.received_qty = replacement_qty
		row.stock_qty = replacement_qty * float(row.conversion_factor or 1.0)
		row.warehouse = spec["warehouse"]
		item_mapped = True

	if not item_mapped or not purchase_receipt.items:
		frappe.throw(
			f"Purchase Receipt mapping did not produce an open receipt row for item {spec['item_code']} "
			f"from Purchase Order {purchase_order.name}."
		)

	purchase_receipt.set_posting_time = 1
	purchase_receipt.posting_date = spec["posting_date"]
	purchase_receipt.posting_time = spec["posting_time"]
	purchase_receipt.supplier_delivery_note = spec["supplier_delivery_note"]
	purchase_receipt.remarks = spec["remarks"]
	purchase_receipt.run_method("calculate_taxes_and_totals")
	purchase_receipt.flags.ignore_permissions = True
	purchase_receipt.insert(ignore_permissions=True)
	purchase_receipt.submit()

	purchase_order = frappe.get_doc("Purchase Order", purchase_order.name)
	purchase_receipt = frappe.get_doc("Purchase Receipt", purchase_receipt.name)
	source_return_invoice = frappe.get_doc("Purchase Invoice", source_return_invoice.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_2F_REPLACEMENT_RECEIPT_LABEL,
		"purchase_order": _summarize_doc(purchase_order),
		"replacement_receipt": _summarize_doc(purchase_receipt),
		"source_supplier_debit_note": _summarize_doc(source_return_invoice),
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_3a_showroom_topup_transfer(dry_run: bool = False) -> dict[str, Any]:
	"""Transfer a small Xiaomi handset buffer into Yangon showroom after live stock-pressure review."""

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_3A_SHOWROOM_TOPUP["stock_entry"]
	item_rows = []

	for row in spec["items"]:
		source_bin = frappe.get_all(
			"Bin",
			filters={"item_code": row["item_code"], "warehouse": row["s_warehouse"]},
			fields=["actual_qty", "reserved_qty", "ordered_qty", "projected_qty"],
			limit=1,
		)
		target_bin = frappe.get_all(
			"Bin",
			filters={"item_code": row["item_code"], "warehouse": row["t_warehouse"]},
			fields=["actual_qty", "reserved_qty", "ordered_qty", "projected_qty"],
			limit=1,
		)
		if not source_bin:
			frappe.throw(f"No Bin found for source item {row['item_code']} in {row['s_warehouse']}.")
		if not target_bin:
			frappe.throw(f"No Bin found for target item {row['item_code']} in {row['t_warehouse']}.")

		available_actual = float(source_bin[0]["actual_qty"] or 0)
		projected_after_transfer = float(source_bin[0]["projected_qty"] or 0) - float(row["qty"])
		target_pressure = float(target_bin[0]["projected_qty"] or 0)

		if float(row["qty"]) <= 0:
			frappe.throw("Transfer quantity must be positive.")
		if available_actual < float(row["qty"]):
			frappe.throw(
				f"Source warehouse {row['s_warehouse']} only has actual_qty {available_actual} for {row['item_code']}."
			)
		if projected_after_transfer < 0:
			frappe.throw(
				f"Transfer would push projected_qty below zero in {row['s_warehouse']} for {row['item_code']}."
			)
		if target_pressure > 0:
			frappe.throw(
				f"Target warehouse {row['t_warehouse']} does not currently show stock pressure for {row['item_code']} "
				f"(projected_qty={target_pressure})."
			)

		item_rows.append(
			{
				"item_code": row["item_code"],
				"qty": row["qty"],
				"s_warehouse": row["s_warehouse"],
				"t_warehouse": row["t_warehouse"],
				"uom": "Nos",
				"stock_uom": "Nos",
				"conversion_factor": 1.0,
			}
		)

	doc = frappe.get_doc(
		{
			"doctype": "Stock Entry",
			"naming_series": spec["naming_series"],
			"company": spec["company"],
			"posting_date": spec["posting_date"],
			"posting_time": spec["posting_time"],
			"set_posting_time": 1,
			"stock_entry_type": spec["stock_entry_type"],
			"purpose": spec["purpose"],
			"from_warehouse": spec["from_warehouse"],
			"to_warehouse": spec["to_warehouse"],
			"remarks": spec["remarks"],
			"items": item_rows,
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	doc.submit()

	doc = frappe.get_doc("Stock Entry", doc.name)
	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_3A_SHOWROOM_TOPUP_LABEL,
		"stock_entry": {
			**_summarize_doc(doc),
			"stock_entry_type": doc.stock_entry_type,
			"purpose": doc.purpose,
			"from_warehouse": doc.from_warehouse,
			"to_warehouse": doc.to_warehouse,
		},
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_4e_transit_router_continuity_release(dry_run: bool = False) -> dict[str, Any]:
	"""Release the remaining old transit router stock into Yangon Main to improve warehouse continuity."""

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_4E_TRANSIT_ROUTER_CONTINUITY_RELEASE["stock_entry"]
	item_rows = []

	for row in spec["items"]:
		source_bin = frappe.get_all(
			"Bin",
			filters={"item_code": row["item_code"], "warehouse": row["s_warehouse"]},
			fields=["actual_qty", "reserved_qty", "ordered_qty", "projected_qty"],
			limit=1,
		)
		target_bin = frappe.get_all(
			"Bin",
			filters={"item_code": row["item_code"], "warehouse": row["t_warehouse"]},
			fields=["actual_qty", "reserved_qty", "ordered_qty", "projected_qty"],
			limit=1,
		)
		if not source_bin:
			frappe.throw(f"No Bin found for source item {row['item_code']} in {row['s_warehouse']}.")
		if not target_bin:
			frappe.throw(f"No Bin found for target item {row['item_code']} in {row['t_warehouse']}.")

		source_actual = float(source_bin[0]["actual_qty"] or 0)
		target_actual = float(target_bin[0]["actual_qty"] or 0)
		qty = float(row["qty"])

		if qty <= 0:
			frappe.throw("Transfer quantity must be positive.")
		if source_actual < qty:
			frappe.throw(
				f"Source warehouse {row['s_warehouse']} only has actual_qty {source_actual} for {row['item_code']}."
			)
		if target_actual > 0:
			frappe.throw(
				f"Target warehouse {row['t_warehouse']} already has actual_qty {target_actual} for {row['item_code']}; "
				"Mini-Phase 4E expects a zero-stock target for this continuity release."
			)

		item_rows.append(
			{
				"item_code": row["item_code"],
				"qty": qty,
				"s_warehouse": row["s_warehouse"],
				"t_warehouse": row["t_warehouse"],
				"uom": "Nos",
				"stock_uom": "Nos",
				"conversion_factor": 1.0,
			}
		)

	doc = frappe.get_doc(
		{
			"doctype": "Stock Entry",
			"naming_series": spec["naming_series"],
			"company": spec["company"],
			"posting_date": spec["posting_date"],
			"posting_time": spec["posting_time"],
			"set_posting_time": 1,
			"stock_entry_type": spec["stock_entry_type"],
			"purpose": spec["purpose"],
			"from_warehouse": spec["from_warehouse"],
			"to_warehouse": spec["to_warehouse"],
			"remarks": spec["remarks"],
			"items": item_rows,
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	doc.submit()

	doc = frappe.get_doc("Stock Entry", doc.name)
	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_4E_TRANSIT_ROUTER_CONTINUITY_RELEASE_LABEL,
		"stock_entry": {
			**_summarize_doc(doc),
			"stock_entry_type": doc.stock_entry_type,
			"purpose": doc.purpose,
			"from_warehouse": doc.from_warehouse,
			"to_warehouse": doc.to_warehouse,
		},
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_4e_legacy_kingston_memory_release(dry_run: bool = False) -> dict[str, Any]:
	"""Release the oldest untouched Kingston memory balances from transit into Yangon Main."""

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_4E_LEGACY_KINGSTON_MEMORY_RELEASE["stock_entry"]
	item_rows = []

	for row in spec["items"]:
		source_bin = frappe.get_all(
			"Bin",
			filters={"item_code": row["item_code"], "warehouse": row["s_warehouse"]},
			fields=["actual_qty", "reserved_qty", "ordered_qty", "projected_qty"],
			limit=1,
		)
		target_bin = frappe.get_all(
			"Bin",
			filters={"item_code": row["item_code"], "warehouse": row["t_warehouse"]},
			fields=["actual_qty", "reserved_qty", "ordered_qty", "projected_qty"],
			limit=1,
		)
		if not source_bin:
			frappe.throw(f"No Bin found for source item {row['item_code']} in {row['s_warehouse']}.")
		if not target_bin:
			frappe.throw(f"No Bin found for target item {row['item_code']} in {row['t_warehouse']}.")

		source_actual = float(source_bin[0]["actual_qty"] or 0)
		source_reserved = float(source_bin[0]["reserved_qty"] or 0)
		source_ordered = float(source_bin[0]["ordered_qty"] or 0)
		target_actual = float(target_bin[0]["actual_qty"] or 0)
		qty = float(row["qty"])

		if qty <= 0:
			frappe.throw("Transfer quantity must be positive.")
		if source_actual < qty:
			frappe.throw(
				f"Source warehouse {row['s_warehouse']} only has actual_qty {source_actual} for {row['item_code']}."
			)
		if not math.isclose(source_actual, qty, rel_tol=0.0, abs_tol=0.0001):
			frappe.throw(
				f"Mini-Phase 4E expects {row['item_code']} transit actual_qty to be exactly {qty}, "
				f"but found {source_actual}. Review continuity assumptions before posting."
			)
		if source_reserved != 0 or source_ordered != 0:
			frappe.throw(
				f"Source warehouse {row['s_warehouse']} for {row['item_code']} is not clean: "
				f"reserved_qty={source_reserved}, ordered_qty={source_ordered}."
			)
		if target_actual <= 0:
			frappe.throw(
				f"Target warehouse {row['t_warehouse']} should already be an active stock lane for {row['item_code']}, "
				f"but actual_qty is {target_actual}."
			)

		item_rows.append(
			{
				"item_code": row["item_code"],
				"qty": qty,
				"s_warehouse": row["s_warehouse"],
				"t_warehouse": row["t_warehouse"],
				"uom": "Nos",
				"stock_uom": "Nos",
				"conversion_factor": 1.0,
			}
		)

	doc = frappe.get_doc(
		{
			"doctype": "Stock Entry",
			"naming_series": spec["naming_series"],
			"company": spec["company"],
			"posting_date": spec["posting_date"],
			"posting_time": spec["posting_time"],
			"set_posting_time": 1,
			"stock_entry_type": spec["stock_entry_type"],
			"purpose": spec["purpose"],
			"from_warehouse": spec["from_warehouse"],
			"to_warehouse": spec["to_warehouse"],
			"remarks": spec["remarks"],
			"items": item_rows,
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	doc.submit()

	doc = frappe.get_doc("Stock Entry", doc.name)
	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_4E_LEGACY_KINGSTON_MEMORY_RELEASE_LABEL,
		"stock_entry": {
			**_summarize_doc(doc),
			"stock_entry_type": doc.stock_entry_type,
			"purpose": doc.purpose,
			"from_warehouse": doc.from_warehouse,
			"to_warehouse": doc.to_warehouse,
		},
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_6q_partial_transit_gadget_release(dry_run: bool = False) -> dict[str, Any]:
	"""Partially release active small-gadget stock from transit into Yangon Main without emptying transit."""

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_6Q_PARTIAL_TRANSIT_GADGET_RELEASE["stock_entry"]
	item_rows = []

	for row in spec["items"]:
		source_bin = frappe.get_all(
			"Bin",
			filters={"item_code": row["item_code"], "warehouse": row["s_warehouse"]},
			fields=["actual_qty", "reserved_qty", "ordered_qty", "projected_qty"],
			limit=1,
		)
		target_bin = frappe.get_all(
			"Bin",
			filters={"item_code": row["item_code"], "warehouse": row["t_warehouse"]},
			fields=["actual_qty", "reserved_qty", "ordered_qty", "projected_qty"],
			limit=1,
		)
		if not source_bin:
			frappe.throw(f"No Bin found for source item {row['item_code']} in {row['s_warehouse']}.")
		if not target_bin:
			frappe.throw(f"No Bin found for target item {row['item_code']} in {row['t_warehouse']}.")

		source_actual = float(source_bin[0]["actual_qty"] or 0)
		source_reserved = float(source_bin[0]["reserved_qty"] or 0)
		source_ordered = float(source_bin[0]["ordered_qty"] or 0)
		target_actual = float(target_bin[0]["actual_qty"] or 0)
		qty = float(row["qty"])

		if qty <= 0:
			frappe.throw("Transfer quantity must be positive.")
		if source_actual < qty:
			frappe.throw(
				f"Source warehouse {row['s_warehouse']} only has actual_qty {source_actual} for {row['item_code']}."
			)
		if source_reserved != 0 or source_ordered != 0:
			frappe.throw(
				f"Source warehouse {row['s_warehouse']} for {row['item_code']} is not clean: "
				f"reserved_qty={source_reserved}, ordered_qty={source_ordered}."
			)
		if target_actual <= 0:
			frappe.throw(
				f"Target warehouse {row['t_warehouse']} should already be an active stock lane for {row['item_code']}, "
				f"but actual_qty is {target_actual}."
			)
		if math.isclose(source_actual, qty, rel_tol=0.0, abs_tol=0.0001):
			frappe.throw(
				f"Mini-Phase 6Q expects a partial release for {row['item_code']}, "
				f"but source actual_qty would fall to zero."
			)

		item_rows.append(
			{
				"item_code": row["item_code"],
				"qty": qty,
				"s_warehouse": row["s_warehouse"],
				"t_warehouse": row["t_warehouse"],
				"uom": "Nos",
				"stock_uom": "Nos",
				"conversion_factor": 1.0,
			}
		)

	doc = frappe.get_doc(
		{
			"doctype": "Stock Entry",
			"naming_series": spec["naming_series"],
			"company": spec["company"],
			"posting_date": spec["posting_date"],
			"posting_time": spec["posting_time"],
			"set_posting_time": 1,
			"stock_entry_type": spec["stock_entry_type"],
			"purpose": spec["purpose"],
			"from_warehouse": spec["from_warehouse"],
			"to_warehouse": spec["to_warehouse"],
			"remarks": spec["remarks"],
			"items": item_rows,
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	doc.submit()

	doc = frappe.get_doc("Stock Entry", doc.name)
	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_6Q_PARTIAL_TRANSIT_GADGET_RELEASE_LABEL,
		"stock_entry": {
			**_summarize_doc(doc),
			"stock_entry_type": doc.stock_entry_type,
			"purpose": doc.purpose,
			"from_warehouse": doc.from_warehouse,
			"to_warehouse": doc.to_warehouse,
		},
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_6t_myanmar_tech_balance_receipt(dry_run: bool = False) -> dict[str, Any]:
	"""Receive the clean remaining balance on the legacy Myanmar Tech importer PO as a second tranche."""

	from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_6T_MYANMAR_TECH_BALANCE_RECEIPT
	purchase_order = frappe.get_doc("Purchase Order", spec["purchase_order"])

	if purchase_order.docstatus != 1:
		frappe.throw(f"Purchase Order {purchase_order.name} must be submitted before downstream receipt mapping.")
	if purchase_order.supplier != spec["supplier"]:
		frappe.throw(
			f"Purchase Order {purchase_order.name} belongs to {purchase_order.supplier}, expected {spec['supplier']}."
		)
	if purchase_order.company != spec["company"]:
		frappe.throw(f"Purchase Order {purchase_order.name} does not belong to {spec['company']}.")
	if float(purchase_order.per_received or 0) <= 0 or float(purchase_order.per_received or 0) >= 100:
		frappe.throw(
			f"Purchase Order {purchase_order.name} must be partially received before Mini-Phase 6T. "
			f"Current per_received={purchase_order.per_received}."
		)

	existing_receipt_rows = frappe.get_all(
		"Purchase Receipt Item",
		filters={"purchase_order": purchase_order.name, "docstatus": 1},
		fields=["parent"],
	)
	existing_receipt_names = sorted({row["parent"] for row in existing_receipt_rows if row.get("parent")})
	if not existing_receipt_names:
		frappe.throw(
			f"Purchase Order {purchase_order.name} has no submitted prior Purchase Receipt rows. "
			"Mini-Phase 6T expects a true second-tranche receipt."
		)

	expected_remaining = spec["expected_remaining_items"]
	actual_remaining = {}
	for row in purchase_order.items:
		open_qty = float(row.qty or 0) - float(row.received_qty or 0) + float(row.returned_qty or 0)
		if open_qty > 0:
			actual_remaining[row.item_code] = float(open_qty)

	if set(actual_remaining) != set(expected_remaining):
		frappe.throw(
			f"Remaining Purchase Order items for {purchase_order.name} do not match Mini-Phase 6T expectations. "
			f"Actual={actual_remaining}, expected={expected_remaining}."
		)

	for item_code, expected_qty in expected_remaining.items():
		actual_qty = float(actual_remaining.get(item_code, 0.0))
		if not math.isclose(actual_qty, float(expected_qty), rel_tol=0.0, abs_tol=0.0001):
			frappe.throw(
				f"Remaining quantity mismatch for {item_code} on {purchase_order.name}: "
				f"actual={actual_qty}, expected={expected_qty}."
			)

	purchase_receipt = make_purchase_receipt(purchase_order.name)
	mapped_items = {}
	for row in list(purchase_receipt.items):
		expected_qty = expected_remaining.get(row.item_code)
		if expected_qty is None:
			purchase_receipt.remove(row)
			continue
		if not math.isclose(float(row.qty or 0), float(expected_qty), rel_tol=0.0, abs_tol=0.0001):
			frappe.throw(
				f"Mapped Purchase Receipt quantity mismatch for {row.item_code}: "
				f"mapped={row.qty}, expected={expected_qty}."
			)
		row.received_qty = expected_qty
		row.stock_qty = float(expected_qty) * float(row.conversion_factor or 1.0)
		mapped_items[row.item_code] = float(row.qty or 0)

	if set(mapped_items) != set(expected_remaining):
		frappe.throw(
			f"Mapped Purchase Receipt rows for {purchase_order.name} do not match expected balance items. "
			f"Mapped={mapped_items}, expected={expected_remaining}."
		)

	purchase_receipt.set_posting_time = 1
	purchase_receipt.posting_date = spec["posting_date"]
	purchase_receipt.posting_time = spec["posting_time"]
	purchase_receipt.supplier_delivery_note = spec["supplier_delivery_note"]
	purchase_receipt.remarks = spec["remarks"]
	purchase_receipt.run_method("calculate_taxes_and_totals")
	purchase_receipt.flags.ignore_permissions = True
	purchase_receipt.insert(ignore_permissions=True)
	purchase_receipt.submit()

	purchase_order = frappe.get_doc("Purchase Order", purchase_order.name)
	purchase_receipt = frappe.get_doc("Purchase Receipt", purchase_receipt.name)
	remaining_open_after = {
		row.item_code: float(row.qty or 0) - float(row.received_qty or 0) + float(row.returned_qty or 0)
		for row in purchase_order.items
		if (float(row.qty or 0) - float(row.received_qty or 0) + float(row.returned_qty or 0)) > 0
	}

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_6T_MYANMAR_TECH_BALANCE_RECEIPT_LABEL,
		"purchase_order": _summarize_doc(purchase_order),
		"purchase_receipt": _summarize_doc(purchase_receipt),
		"existing_receipts_before": existing_receipt_names,
		"mapped_remaining_items": mapped_items,
		"remaining_open_after": remaining_open_after,
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_4f_defective_earbuds_quarantine_transfer(dry_run: bool = False) -> dict[str, Any]:
	"""Quarantine one historically returned defective earbuds unit into Returns and Damaged."""

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_4F_DEFECTIVE_EARBUDS_QUARANTINE["stock_entry"]
	row = spec["items"][0]

	source_bin = frappe.get_all(
		"Bin",
		filters={"item_code": row["item_code"], "warehouse": row["s_warehouse"]},
		fields=["actual_qty", "reserved_qty", "ordered_qty", "projected_qty"],
		limit=1,
	)
	target_bin = frappe.get_all(
		"Bin",
		filters={"item_code": row["item_code"], "warehouse": row["t_warehouse"]},
		fields=["actual_qty", "reserved_qty", "ordered_qty", "projected_qty"],
		limit=1,
	)
	if not source_bin:
		frappe.throw(f"No Bin found for source item {row['item_code']} in {row['s_warehouse']}.")

	source_actual = float(source_bin[0]["actual_qty"] or 0)
	source_reserved = float(source_bin[0]["reserved_qty"] or 0)
	source_ordered = float(source_bin[0]["ordered_qty"] or 0)
	target_actual = float(target_bin[0]["actual_qty"] or 0) if target_bin else 0.0
	qty = float(row["qty"])

	if qty <= 0:
		frappe.throw("Transfer quantity must be positive.")
	if source_actual < qty:
		frappe.throw(
			f"Source warehouse {row['s_warehouse']} only has actual_qty {source_actual} for {row['item_code']}."
		)
	if source_reserved < 0 or source_ordered < 0:
		frappe.throw(
			f"Unexpected negative source reservation posture for {row['item_code']} in {row['s_warehouse']}."
		)
	if target_actual > 0:
		frappe.throw(
			f"Target warehouse {row['t_warehouse']} already has actual_qty {target_actual} for {row['item_code']}; "
			"Mini-Phase 4F expects to open the first damaged-stock lane for this SKU."
		)

	doc = frappe.get_doc(
		{
			"doctype": "Stock Entry",
			"naming_series": spec["naming_series"],
			"company": spec["company"],
			"posting_date": spec["posting_date"],
			"posting_time": spec["posting_time"],
			"set_posting_time": 1,
			"stock_entry_type": spec["stock_entry_type"],
			"purpose": spec["purpose"],
			"from_warehouse": spec["from_warehouse"],
			"to_warehouse": spec["to_warehouse"],
			"remarks": spec["remarks"],
			"items": [
				{
					"item_code": row["item_code"],
					"qty": qty,
					"s_warehouse": row["s_warehouse"],
					"t_warehouse": row["t_warehouse"],
					"uom": "Nos",
					"stock_uom": "Nos",
					"conversion_factor": 1.0,
				}
			],
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	doc.submit()

	doc = frappe.get_doc("Stock Entry", doc.name)
	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_4F_DEFECTIVE_EARBUDS_QUARANTINE_LABEL,
		"reference_return_invoice": spec["reference_return_invoice"],
		"stock_entry": {
			**_summarize_doc(doc),
			"stock_entry_type": doc.stock_entry_type,
			"purpose": doc.purpose,
			"from_warehouse": doc.from_warehouse,
			"to_warehouse": doc.to_warehouse,
		},
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_4g_capital_key_account_sales_order(dry_run: bool = False) -> dict[str, Any]:
	"""Create a late-April key-account Sales Order for Capital Telecom (NPT) using MMOB key-account pricing."""

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_4G_CAPITAL_KEY_ACCOUNT_SALE["sales_order"]
	item_rows = []

	for row in spec["items"]:
		rate = _get_pilot_price_rate(row["item_code"], spec["selling_price_list"])
		item_rows.append(
			{
				"item_code": row["item_code"],
				"qty": row["qty"],
				"warehouse": row["warehouse"],
				"delivery_date": row["delivery_date"],
				"uom": "Nos",
				"conversion_factor": 1.0,
				"price_list_rate": rate,
				"rate": rate,
			}
		)

	doc = frappe.get_doc(
		{
			"doctype": "Sales Order",
			"naming_series": spec["naming_series"],
			"customer": spec["customer"],
			"company": spec["company"],
			"transaction_date": spec["transaction_date"],
			"delivery_date": spec["delivery_date"],
			"po_no": spec["po_no"],
			"po_date": spec["po_date"],
			"currency": spec["currency"],
			"conversion_rate": spec["conversion_rate"],
			"selling_price_list": spec["selling_price_list"],
			"price_list_currency": spec["price_list_currency"],
			"plc_conversion_rate": spec["plc_conversion_rate"],
			"payment_terms_template": spec["payment_terms_template"],
			"set_warehouse": spec["set_warehouse"],
			"items": item_rows,
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	doc.submit()

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_4G_CAPITAL_KEY_ACCOUNT_SALE_LABEL,
		"sales_order": _summarize_doc(doc),
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def complete_miniphase_4g_capital_key_account_sale_from_sales_order(
	sales_order_name: str, dry_run: bool = False
) -> dict[str, Any]:
	"""Map the late-April Capital Telecom Sales Order through delivery and invoice."""

	from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
	from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_4G_CAPITAL_KEY_ACCOUNT_SALE

	sales_order = frappe.get_doc("Sales Order", sales_order_name)
	if sales_order.docstatus != 1:
		frappe.throw(f"Sales Order {sales_order_name} must be submitted before downstream mapping.")
	if sales_order.customer != spec["sales_order"]["customer"]:
		frappe.throw(
			f"Sales Order {sales_order_name} belongs to {sales_order.customer}, expected {spec['sales_order']['customer']}."
		)
	if sales_order.company != COMPANY_NAME:
		frappe.throw(f"Sales Order {sales_order_name} does not belong to {COMPANY_NAME}.")
	if float(sales_order.per_delivered or 0) > 0 or float(sales_order.per_billed or 0) > 0:
		frappe.throw(
			f"Sales Order {sales_order_name} already has downstream activity "
			f"(delivered={sales_order.per_delivered}, billed={sales_order.per_billed})."
		)

	delivery_note = make_delivery_note(sales_order.name)
	delivery_note.set_posting_time = 1
	delivery_note.posting_date = spec["delivery_note"]["posting_date"]
	delivery_note.posting_time = spec["delivery_note"]["posting_time"]
	delivery_note.lr_date = spec["delivery_note"]["posting_date"]
	delivery_note.remarks = spec["delivery_note"]["remarks"]
	delivery_note.flags.ignore_permissions = True
	delivery_note.insert(ignore_permissions=True)
	delivery_note.submit()

	sales_invoice = make_sales_invoice(delivery_note.name)
	sales_invoice.set_posting_time = 1
	sales_invoice.posting_date = spec["sales_invoice"]["posting_date"]
	sales_invoice.posting_time = spec["sales_invoice"]["posting_time"]
	sales_invoice.due_date = spec["sales_invoice"]["due_date"]
	sales_invoice.payment_terms_template = sales_order.payment_terms_template
	sales_invoice.remarks = spec["sales_invoice"]["remarks"]
	sales_invoice.flags.ignore_permissions = True
	sales_invoice.insert(ignore_permissions=True)
	sales_invoice.submit()

	sales_order = frappe.get_doc("Sales Order", sales_order_name)
	delivery_note = frappe.get_doc("Delivery Note", delivery_note.name)
	sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_4G_CAPITAL_KEY_ACCOUNT_SALE_LABEL,
		"sales_order": _summarize_doc(sales_order),
		"delivery_note": _summarize_doc(delivery_note),
		"sales_invoice": _summarize_doc(sales_invoice),
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_4g_bayint_month_end_collection(dry_run: bool = False) -> dict[str, Any]:
	"""Create a late-April rounded bank-transfer collection against Bayint's active April wholesale invoice."""

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_4G_BAYINT_MONTH_END_COLLECTION
	sales_invoice = frappe.get_doc("Sales Invoice", spec["sales_invoice"])

	if sales_invoice.docstatus != 1:
		frappe.throw(f"Sales Invoice {sales_invoice.name} must be submitted before collection.")
	if float(sales_invoice.outstanding_amount or 0) <= 0:
		frappe.throw(f"Sales Invoice {sales_invoice.name} has no outstanding amount left.")

	payment_entry = get_payment_entry(
		"Sales Invoice",
		sales_invoice.name,
		bank_account=spec["paid_to"],
		reference_date=spec["reference_date"],
	)
	partial_amount = float(spec["received_amount"])
	if partial_amount > float(sales_invoice.outstanding_amount):
		frappe.throw(
			f"Configured partial collection {partial_amount} exceeds outstanding {sales_invoice.outstanding_amount} "
			f"for {sales_invoice.name}."
		)

	payment_entry.posting_date = spec["posting_date"]
	payment_entry.paid_to = spec["paid_to"]
	payment_entry.mode_of_payment = spec["mode_of_payment"]
	payment_entry.reference_no = spec["reference_no"]
	payment_entry.reference_date = spec["reference_date"]
	payment_entry.paid_amount = partial_amount
	payment_entry.received_amount = partial_amount
	payment_entry.source_exchange_rate = 1.0
	payment_entry.target_exchange_rate = 1.0
	payment_entry.remarks = (
		f"{spec['remarks']}\n"
		f"Amount MMK {partial_amount} received against Sales Invoice {sales_invoice.name}"
	)
	if payment_entry.references:
		payment_entry.references[0].allocated_amount = partial_amount

	payment_entry.flags.ignore_permissions = True
	payment_entry.insert(ignore_permissions=True)
	payment_entry.submit()

	sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice.name)
	payment_entry = frappe.get_doc("Payment Entry", payment_entry.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_4G_BAYINT_MONTH_END_COLLECTION_LABEL,
		"sales_invoice": _summarize_doc(sales_invoice),
		"payment_entry": {
			"doctype": payment_entry.doctype,
			"name": payment_entry.name,
			"docstatus": payment_entry.docstatus,
			"status": getattr(payment_entry, "status", None),
			"posting_date": payment_entry.posting_date,
			"mode_of_payment": payment_entry.mode_of_payment,
			"paid_from": payment_entry.paid_from,
			"paid_to": payment_entry.paid_to,
			"paid_amount": payment_entry.paid_amount,
			"received_amount": payment_entry.received_amount,
			"reference_no": payment_entry.reference_no,
			"references": [
				{
					"reference_doctype": row.reference_doctype,
					"reference_name": row.reference_name,
					"allocated_amount": row.allocated_amount,
				}
				for row in payment_entry.references
			],
		},
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_6a_ko_nay_lin_aged_collection(dry_run: bool = False) -> dict[str, Any]:
	"""Create a rounded April bank-transfer collection against one clean overdue Ko Nay Lin wholesale invoice."""

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_6A_KO_NAY_LIN_AGED_COLLECTION
	sales_invoice = frappe.get_doc("Sales Invoice", spec["sales_invoice"])

	if sales_invoice.docstatus != 1:
		frappe.throw(f"Sales Invoice {sales_invoice.name} must be submitted before collection.")
	if float(sales_invoice.outstanding_amount or 0) <= 0:
		frappe.throw(f"Sales Invoice {sales_invoice.name} has no outstanding amount left.")

	payment_entry = get_payment_entry(
		"Sales Invoice",
		sales_invoice.name,
		bank_account=spec["paid_to"],
		reference_date=spec["reference_date"],
	)
	partial_amount = float(spec["received_amount"])
	if partial_amount > float(sales_invoice.outstanding_amount):
		frappe.throw(
			f"Configured partial collection {partial_amount} exceeds outstanding {sales_invoice.outstanding_amount} "
			f"for {sales_invoice.name}."
		)

	payment_entry.posting_date = spec["posting_date"]
	payment_entry.paid_to = spec["paid_to"]
	payment_entry.mode_of_payment = spec["mode_of_payment"]
	payment_entry.reference_no = spec["reference_no"]
	payment_entry.reference_date = spec["reference_date"]
	payment_entry.paid_amount = partial_amount
	payment_entry.received_amount = partial_amount
	payment_entry.source_exchange_rate = 1.0
	payment_entry.target_exchange_rate = 1.0
	payment_entry.remarks = (
		f"{spec['remarks']}\n"
		f"Amount MMK {partial_amount} received against Sales Invoice {sales_invoice.name}"
	)
	if payment_entry.references:
		payment_entry.references[0].allocated_amount = partial_amount

	payment_entry.flags.ignore_permissions = True
	payment_entry.insert(ignore_permissions=True)
	payment_entry.submit()

	sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice.name)
	payment_entry = frappe.get_doc("Payment Entry", payment_entry.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_6A_KO_NAY_LIN_AGED_COLLECTION_LABEL,
		"sales_invoice": _summarize_doc(sales_invoice),
		"payment_entry": {
			"doctype": payment_entry.doctype,
			"name": payment_entry.name,
			"docstatus": payment_entry.docstatus,
			"status": getattr(payment_entry, "status", None),
			"posting_date": payment_entry.posting_date,
			"mode_of_payment": payment_entry.mode_of_payment,
			"paid_from": payment_entry.paid_from,
			"paid_to": payment_entry.paid_to,
			"paid_amount": payment_entry.paid_amount,
			"received_amount": payment_entry.received_amount,
			"reference_no": payment_entry.reference_no,
			"references": [
				{
					"reference_doctype": row.reference_doctype,
					"reference_name": row.reference_name,
					"allocated_amount": row.allocated_amount,
				}
				for row in payment_entry.references
			],
		},
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_6b_myanmar_tech_followon_ap_payment(dry_run: bool = False) -> dict[str, Any]:
	"""Create a second rounded staged payment against the February Myanmar Tech importer payable."""

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_6B_MYANMAR_TECH_FOLLOWON_AP_PAYMENT
	purchase_invoice = frappe.get_doc("Purchase Invoice", spec["purchase_invoice"])

	if purchase_invoice.docstatus != 1:
		frappe.throw(f"Purchase Invoice {purchase_invoice.name} must be submitted before payment.")
	if float(purchase_invoice.outstanding_amount or 0) <= 0:
		frappe.throw(f"Purchase Invoice {purchase_invoice.name} has no outstanding amount left.")

	payment_entry = get_payment_entry("Purchase Invoice", purchase_invoice.name)
	partial_amount = float(spec["paid_amount"])
	if partial_amount > float(purchase_invoice.outstanding_amount):
		frappe.throw(
			f"Configured partial payment {partial_amount} exceeds outstanding {purchase_invoice.outstanding_amount} "
			f"for {purchase_invoice.name}."
		)

	payment_entry.posting_date = spec["posting_date"]
	payment_entry.paid_from = spec["paid_from"]
	payment_entry.mode_of_payment = spec["mode_of_payment"]
	payment_entry.reference_no = spec["reference_no"]
	payment_entry.reference_date = spec["reference_date"]
	payment_entry.paid_amount = partial_amount
	payment_entry.received_amount = partial_amount
	payment_entry.source_exchange_rate = 1.0
	payment_entry.target_exchange_rate = 1.0
	payment_entry.remarks = (
		f"{spec['remarks']}\n"
		f"Amount MMK {partial_amount} paid against Purchase Invoice {purchase_invoice.name}"
	)
	if payment_entry.references:
		payment_entry.references[0].allocated_amount = partial_amount

	payment_entry.flags.ignore_permissions = True
	payment_entry.insert(ignore_permissions=True)
	payment_entry.submit()

	purchase_invoice = frappe.get_doc("Purchase Invoice", purchase_invoice.name)
	payment_entry = frappe.get_doc("Payment Entry", payment_entry.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_6B_MYANMAR_TECH_FOLLOWON_AP_PAYMENT_LABEL,
		"purchase_invoice": _summarize_doc(purchase_invoice),
		"payment_entry": {
			"doctype": payment_entry.doctype,
			"name": payment_entry.name,
			"docstatus": payment_entry.docstatus,
			"status": getattr(payment_entry, "status", None),
			"posting_date": payment_entry.posting_date,
			"mode_of_payment": payment_entry.mode_of_payment,
			"paid_from": payment_entry.paid_from,
			"paid_to": payment_entry.paid_to,
			"paid_amount": payment_entry.paid_amount,
			"received_amount": payment_entry.received_amount,
			"reference_no": payment_entry.reference_no,
			"references": [
				{
					"reference_doctype": row.reference_doctype,
					"reference_name": row.reference_name,
					"allocated_amount": row.allocated_amount,
				}
				for row in payment_entry.references
			],
		},
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_6c_mandalay_device_followon_ap_payment(dry_run: bool = False) -> dict[str, Any]:
	"""Create a rounded follow-on payment against the February Mandalay Device local-supplier payable."""

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_6C_MANDALAY_DEVICE_FOLLOWON_AP_PAYMENT
	purchase_invoice = frappe.get_doc("Purchase Invoice", spec["purchase_invoice"])

	if purchase_invoice.docstatus != 1:
		frappe.throw(f"Purchase Invoice {purchase_invoice.name} must be submitted before payment.")
	if float(purchase_invoice.outstanding_amount or 0) <= 0:
		frappe.throw(f"Purchase Invoice {purchase_invoice.name} has no outstanding amount left.")

	payment_entry = get_payment_entry("Purchase Invoice", purchase_invoice.name)
	partial_amount = float(spec["paid_amount"])
	if partial_amount > float(purchase_invoice.outstanding_amount):
		frappe.throw(
			f"Configured partial payment {partial_amount} exceeds outstanding {purchase_invoice.outstanding_amount} "
			f"for {purchase_invoice.name}."
		)

	payment_entry.posting_date = spec["posting_date"]
	payment_entry.paid_from = spec["paid_from"]
	payment_entry.mode_of_payment = spec["mode_of_payment"]
	payment_entry.reference_no = spec["reference_no"]
	payment_entry.reference_date = spec["reference_date"]
	payment_entry.paid_amount = partial_amount
	payment_entry.received_amount = partial_amount
	payment_entry.source_exchange_rate = 1.0
	payment_entry.target_exchange_rate = 1.0
	payment_entry.remarks = (
		f"{spec['remarks']}\n"
		f"Amount MMK {partial_amount} paid against Purchase Invoice {purchase_invoice.name}"
	)
	if payment_entry.references:
		payment_entry.references[0].allocated_amount = partial_amount

	payment_entry.flags.ignore_permissions = True
	payment_entry.insert(ignore_permissions=True)
	payment_entry.submit()

	purchase_invoice = frappe.get_doc("Purchase Invoice", purchase_invoice.name)
	payment_entry = frappe.get_doc("Payment Entry", payment_entry.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_6C_MANDALAY_DEVICE_FOLLOWON_AP_PAYMENT_LABEL,
		"purchase_invoice": _summarize_doc(purchase_invoice),
		"payment_entry": {
			"doctype": payment_entry.doctype,
			"name": payment_entry.name,
			"docstatus": payment_entry.docstatus,
			"status": getattr(payment_entry, "status", None),
			"posting_date": payment_entry.posting_date,
			"mode_of_payment": payment_entry.mode_of_payment,
			"paid_from": payment_entry.paid_from,
			"paid_to": payment_entry.paid_to,
			"paid_amount": payment_entry.paid_amount,
			"received_amount": payment_entry.received_amount,
			"reference_no": payment_entry.reference_no,
			"references": [
				{
					"reference_doctype": row.reference_doctype,
					"reference_name": row.reference_name,
					"allocated_amount": row.allocated_amount,
				}
				for row in payment_entry.references
			],
		},
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_6e_35th_street_followon_collection(dry_run: bool = False) -> dict[str, Any]:
	"""Create a rounded follow-on collection against the February 35th Street wholesale invoice."""

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_6E_35TH_STREET_FOLLOWON_COLLECTION
	sales_invoice = frappe.get_doc("Sales Invoice", spec["sales_invoice"])

	if sales_invoice.docstatus != 1:
		frappe.throw(f"Sales Invoice {sales_invoice.name} must be submitted before collection.")
	if float(sales_invoice.outstanding_amount or 0) <= 0:
		frappe.throw(f"Sales Invoice {sales_invoice.name} has no outstanding amount left.")

	payment_entry = get_payment_entry(
		"Sales Invoice",
		sales_invoice.name,
		bank_account=spec["paid_to"],
		reference_date=spec["reference_date"],
	)
	partial_amount = float(spec["received_amount"])
	if partial_amount > float(sales_invoice.outstanding_amount):
		frappe.throw(
			f"Configured partial collection {partial_amount} exceeds outstanding {sales_invoice.outstanding_amount} "
			f"for {sales_invoice.name}."
		)

	payment_entry.posting_date = spec["posting_date"]
	payment_entry.paid_to = spec["paid_to"]
	payment_entry.mode_of_payment = spec["mode_of_payment"]
	payment_entry.reference_no = spec["reference_no"]
	payment_entry.reference_date = spec["reference_date"]
	payment_entry.paid_amount = partial_amount
	payment_entry.received_amount = partial_amount
	payment_entry.source_exchange_rate = 1.0
	payment_entry.target_exchange_rate = 1.0
	payment_entry.remarks = (
		f"{spec['remarks']}\n"
		f"Amount MMK {partial_amount} received against Sales Invoice {sales_invoice.name}"
	)
	if payment_entry.references:
		payment_entry.references[0].allocated_amount = partial_amount

	payment_entry.flags.ignore_permissions = True
	payment_entry.insert(ignore_permissions=True)
	payment_entry.submit()

	sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice.name)
	payment_entry = frappe.get_doc("Payment Entry", payment_entry.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_6E_35TH_STREET_FOLLOWON_COLLECTION_LABEL,
		"sales_invoice": _summarize_doc(sales_invoice),
		"payment_entry": {
			"doctype": payment_entry.doctype,
			"name": payment_entry.name,
			"docstatus": payment_entry.docstatus,
			"status": getattr(payment_entry, "status", None),
			"posting_date": payment_entry.posting_date,
			"mode_of_payment": payment_entry.mode_of_payment,
			"paid_from": payment_entry.paid_from,
			"paid_to": payment_entry.paid_to,
			"paid_amount": payment_entry.paid_amount,
			"received_amount": payment_entry.received_amount,
			"reference_no": payment_entry.reference_no,
			"references": [
				{
					"reference_doctype": row.reference_doctype,
					"reference_name": row.reference_name,
					"allocated_amount": row.allocated_amount,
				}
				for row in payment_entry.references
			],
		},
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_6g_asia_connect_followon_ap_payment(dry_run: bool = False) -> dict[str, Any]:
	"""Create a rounded follow-on payment against the August Asia Connect logistics-and-customs payable."""

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_6G_ASIA_CONNECT_FOLLOWON_AP_PAYMENT
	purchase_invoice = frappe.get_doc("Purchase Invoice", spec["purchase_invoice"])

	if purchase_invoice.docstatus != 1:
		frappe.throw(f"Purchase Invoice {purchase_invoice.name} must be submitted before payment.")
	if float(purchase_invoice.outstanding_amount or 0) <= 0:
		frappe.throw(f"Purchase Invoice {purchase_invoice.name} has no outstanding amount left.")

	payment_entry = get_payment_entry("Purchase Invoice", purchase_invoice.name)
	partial_amount = float(spec["paid_amount"])
	if partial_amount > float(purchase_invoice.outstanding_amount):
		frappe.throw(
			f"Configured partial payment {partial_amount} exceeds outstanding {purchase_invoice.outstanding_amount} "
			f"for {purchase_invoice.name}."
		)

	payment_entry.posting_date = spec["posting_date"]
	payment_entry.paid_from = spec["paid_from"]
	payment_entry.mode_of_payment = spec["mode_of_payment"]
	payment_entry.reference_no = spec["reference_no"]
	payment_entry.reference_date = spec["reference_date"]
	payment_entry.paid_amount = partial_amount
	payment_entry.received_amount = partial_amount
	payment_entry.source_exchange_rate = 1.0
	payment_entry.target_exchange_rate = 1.0
	payment_entry.remarks = (
		f"{spec['remarks']}\n"
		f"Amount MMK {partial_amount} paid against Purchase Invoice {purchase_invoice.name}"
	)
	if payment_entry.references:
		payment_entry.references[0].allocated_amount = partial_amount

	payment_entry.flags.ignore_permissions = True
	payment_entry.insert(ignore_permissions=True)
	payment_entry.submit()

	purchase_invoice = frappe.get_doc("Purchase Invoice", purchase_invoice.name)
	payment_entry = frappe.get_doc("Payment Entry", payment_entry.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_6G_ASIA_CONNECT_FOLLOWON_AP_PAYMENT_LABEL,
		"purchase_invoice": _summarize_doc(purchase_invoice),
		"payment_entry": {
			"doctype": payment_entry.doctype,
			"name": payment_entry.name,
			"docstatus": payment_entry.docstatus,
			"status": getattr(payment_entry, "status", None),
			"posting_date": payment_entry.posting_date,
			"mode_of_payment": payment_entry.mode_of_payment,
			"paid_from": payment_entry.paid_from,
			"paid_to": payment_entry.paid_to,
			"paid_amount": payment_entry.paid_amount,
			"received_amount": payment_entry.received_amount,
			"reference_no": payment_entry.reference_no,
			"references": [
				{
					"reference_doctype": row.reference_doctype,
					"reference_name": row.reference_name,
					"allocated_amount": row.allocated_amount,
				}
				for row in payment_entry.references
			],
		},
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_6i_shwe_taung_followon_ap_payment(dry_run: bool = False) -> dict[str, Any]:
	"""Create a rounded follow-on payment against the January Shwe Taung supplier payable."""

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_6I_SHWE_TAUNG_FOLLOWON_AP_PAYMENT
	purchase_invoice = frappe.get_doc("Purchase Invoice", spec["purchase_invoice"])

	if purchase_invoice.docstatus != 1:
		frappe.throw(f"Purchase Invoice {purchase_invoice.name} must be submitted before payment.")
	if float(purchase_invoice.outstanding_amount or 0) <= 0:
		frappe.throw(f"Purchase Invoice {purchase_invoice.name} has no outstanding amount left.")

	payment_entry = get_payment_entry("Purchase Invoice", purchase_invoice.name)
	partial_amount = float(spec["paid_amount"])
	if partial_amount > float(purchase_invoice.outstanding_amount):
		frappe.throw(
			f"Configured partial payment {partial_amount} exceeds outstanding {purchase_invoice.outstanding_amount} "
			f"for {purchase_invoice.name}."
		)

	payment_entry.posting_date = spec["posting_date"]
	payment_entry.paid_from = spec["paid_from"]
	payment_entry.mode_of_payment = spec["mode_of_payment"]
	payment_entry.reference_no = spec["reference_no"]
	payment_entry.reference_date = spec["reference_date"]
	payment_entry.paid_amount = partial_amount
	payment_entry.received_amount = partial_amount
	payment_entry.source_exchange_rate = 1.0
	payment_entry.target_exchange_rate = 1.0
	payment_entry.remarks = (
		f"{spec['remarks']}\n"
		f"Amount MMK {partial_amount} paid against Purchase Invoice {purchase_invoice.name}"
	)
	if payment_entry.references:
		payment_entry.references[0].allocated_amount = partial_amount

	payment_entry.flags.ignore_permissions = True
	payment_entry.insert(ignore_permissions=True)
	payment_entry.submit()

	purchase_invoice = frappe.get_doc("Purchase Invoice", purchase_invoice.name)
	payment_entry = frappe.get_doc("Payment Entry", payment_entry.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_6I_SHWE_TAUNG_FOLLOWON_AP_PAYMENT_LABEL,
		"purchase_invoice": _summarize_doc(purchase_invoice),
		"payment_entry": {
			"doctype": payment_entry.doctype,
			"name": payment_entry.name,
			"docstatus": payment_entry.docstatus,
			"status": getattr(payment_entry, "status", None),
			"posting_date": payment_entry.posting_date,
			"mode_of_payment": payment_entry.mode_of_payment,
			"paid_from": payment_entry.paid_from,
			"paid_to": payment_entry.paid_to,
			"paid_amount": payment_entry.paid_amount,
			"received_amount": payment_entry.received_amount,
			"reference_no": payment_entry.reference_no,
			"references": [
				{
					"reference_doctype": row.reference_doctype,
					"reference_name": row.reference_name,
					"allocated_amount": row.allocated_amount,
				}
				for row in payment_entry.references
			],
		},
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_6k_capital_followon_collection(dry_run: bool = False) -> dict[str, Any]:
	"""Create a rounded follow-on collection against the March Capital Telecom key-account invoice."""

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_6K_CAPITAL_FOLLOWON_COLLECTION
	sales_invoice = frappe.get_doc("Sales Invoice", spec["sales_invoice"])

	if sales_invoice.docstatus != 1:
		frappe.throw(f"Sales Invoice {sales_invoice.name} must be submitted before collection.")
	if float(sales_invoice.outstanding_amount or 0) <= 0:
		frappe.throw(f"Sales Invoice {sales_invoice.name} has no outstanding amount left.")

	payment_entry = get_payment_entry(
		"Sales Invoice",
		sales_invoice.name,
		bank_account=spec["paid_to"],
		reference_date=spec["reference_date"],
	)
	partial_amount = float(spec["received_amount"])
	if partial_amount > float(sales_invoice.outstanding_amount):
		frappe.throw(
			f"Configured partial collection {partial_amount} exceeds outstanding {sales_invoice.outstanding_amount} "
			f"for {sales_invoice.name}."
		)

	payment_entry.posting_date = spec["posting_date"]
	payment_entry.paid_to = spec["paid_to"]
	payment_entry.mode_of_payment = spec["mode_of_payment"]
	payment_entry.reference_no = spec["reference_no"]
	payment_entry.reference_date = spec["reference_date"]
	payment_entry.paid_amount = partial_amount
	payment_entry.received_amount = partial_amount
	payment_entry.source_exchange_rate = 1.0
	payment_entry.target_exchange_rate = 1.0
	payment_entry.remarks = (
		f"{spec['remarks']}\n"
		f"Amount MMK {partial_amount} received against Sales Invoice {sales_invoice.name}"
	)
	if payment_entry.references:
		payment_entry.references[0].allocated_amount = partial_amount

	payment_entry.flags.ignore_permissions = True
	payment_entry.insert(ignore_permissions=True)
	payment_entry.submit()

	sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice.name)
	payment_entry = frappe.get_doc("Payment Entry", payment_entry.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_6K_CAPITAL_FOLLOWON_COLLECTION_LABEL,
		"sales_invoice": _summarize_doc(sales_invoice),
		"payment_entry": {
			"doctype": payment_entry.doctype,
			"name": payment_entry.name,
			"docstatus": payment_entry.docstatus,
			"status": getattr(payment_entry, "status", None),
			"posting_date": payment_entry.posting_date,
			"mode_of_payment": payment_entry.mode_of_payment,
			"paid_from": payment_entry.paid_from,
			"paid_to": payment_entry.paid_to,
			"paid_amount": payment_entry.paid_amount,
			"received_amount": payment_entry.received_amount,
			"reference_no": payment_entry.reference_no,
			"references": [
				{
					"reference_doctype": row.reference_doctype,
					"reference_name": row.reference_name,
					"allocated_amount": row.allocated_amount,
				}
				for row in payment_entry.references
			],
		},
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_6m_golden_dragon_followon_ap_payment(dry_run: bool = False) -> dict[str, Any]:
	"""Create a rounded follow-on payment against the late-January Golden Dragon supplier payable."""

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_6M_GOLDEN_DRAGON_FOLLOWON_AP_PAYMENT
	purchase_invoice = frappe.get_doc("Purchase Invoice", spec["purchase_invoice"])

	if purchase_invoice.docstatus != 1:
		frappe.throw(f"Purchase Invoice {purchase_invoice.name} must be submitted before payment.")
	if float(purchase_invoice.outstanding_amount or 0) <= 0:
		frappe.throw(f"Purchase Invoice {purchase_invoice.name} has no outstanding amount left.")

	payment_entry = get_payment_entry("Purchase Invoice", purchase_invoice.name)
	partial_amount = float(spec["paid_amount"])
	if partial_amount > float(purchase_invoice.outstanding_amount):
		frappe.throw(
			f"Configured partial payment {partial_amount} exceeds outstanding {purchase_invoice.outstanding_amount} "
			f"for {purchase_invoice.name}."
		)

	payment_entry.posting_date = spec["posting_date"]
	payment_entry.paid_from = spec["paid_from"]
	payment_entry.mode_of_payment = spec["mode_of_payment"]
	payment_entry.reference_no = spec["reference_no"]
	payment_entry.reference_date = spec["reference_date"]
	payment_entry.paid_amount = partial_amount
	payment_entry.received_amount = partial_amount
	payment_entry.source_exchange_rate = 1.0
	payment_entry.target_exchange_rate = 1.0
	payment_entry.remarks = (
		f"{spec['remarks']}\n"
		f"Amount MMK {partial_amount} paid against Purchase Invoice {purchase_invoice.name}"
	)
	if payment_entry.references:
		payment_entry.references[0].allocated_amount = partial_amount

	payment_entry.flags.ignore_permissions = True
	payment_entry.insert(ignore_permissions=True)
	payment_entry.submit()

	purchase_invoice = frappe.get_doc("Purchase Invoice", purchase_invoice.name)
	payment_entry = frappe.get_doc("Payment Entry", payment_entry.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_6M_GOLDEN_DRAGON_FOLLOWON_AP_PAYMENT_LABEL,
		"purchase_invoice": _summarize_doc(purchase_invoice),
		"payment_entry": {
			"doctype": payment_entry.doctype,
			"name": payment_entry.name,
			"docstatus": payment_entry.docstatus,
			"status": getattr(payment_entry, "status", None),
			"posting_date": payment_entry.posting_date,
			"mode_of_payment": payment_entry.mode_of_payment,
			"paid_from": payment_entry.paid_from,
			"paid_to": payment_entry.paid_to,
			"paid_amount": payment_entry.paid_amount,
			"received_amount": payment_entry.received_amount,
			"reference_no": payment_entry.reference_no,
			"references": [
				{
					"reference_doctype": row.reference_doctype,
					"reference_name": row.reference_name,
					"allocated_amount": row.allocated_amount,
				}
				for row in payment_entry.references
			],
		},
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_7f_chan_aye_followon_collection(dry_run: bool = False) -> dict[str, Any]:
	"""Create a small rounded follow-on collection against the overdue Chan Aye wholesale invoice."""

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_7F_CHAN_AYE_FOLLOWON_COLLECTION
	sales_invoice = frappe.get_doc("Sales Invoice", spec["sales_invoice"])

	if sales_invoice.docstatus != 1:
		frappe.throw(f"Sales Invoice {sales_invoice.name} must be submitted before collection.")
	if float(sales_invoice.outstanding_amount or 0) <= 0:
		frappe.throw(f"Sales Invoice {sales_invoice.name} has no outstanding amount left.")

	payment_entry = get_payment_entry(
		"Sales Invoice",
		sales_invoice.name,
		bank_account=spec["paid_to"],
		reference_date=spec["reference_date"],
	)
	collection_amount = float(spec["received_amount"])
	if collection_amount > float(sales_invoice.outstanding_amount):
		frappe.throw(
			f"Configured follow-on collection {collection_amount} exceeds outstanding {sales_invoice.outstanding_amount} "
			f"for {sales_invoice.name}."
		)

	payment_entry.posting_date = spec["posting_date"]
	payment_entry.paid_to = spec["paid_to"]
	payment_entry.mode_of_payment = spec["mode_of_payment"]
	payment_entry.reference_no = spec["reference_no"]
	payment_entry.reference_date = spec["reference_date"]
	payment_entry.paid_amount = collection_amount
	payment_entry.received_amount = collection_amount
	payment_entry.source_exchange_rate = 1.0
	payment_entry.target_exchange_rate = 1.0
	payment_entry.remarks = (
		f"{spec['remarks']}\n"
		f"Amount MMK {collection_amount} received against Sales Invoice {sales_invoice.name}"
	)
	if payment_entry.references:
		payment_entry.references[0].allocated_amount = collection_amount

	payment_entry.flags.ignore_permissions = True
	payment_entry.insert(ignore_permissions=True)
	payment_entry.submit()

	sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice.name)
	payment_entry = frappe.get_doc("Payment Entry", payment_entry.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_7F_CHAN_AYE_FOLLOWON_COLLECTION_LABEL,
		"sales_invoice": _summarize_doc(sales_invoice),
		"payment_entry": {
			"doctype": payment_entry.doctype,
			"name": payment_entry.name,
			"docstatus": payment_entry.docstatus,
			"status": getattr(payment_entry, "status", None),
			"posting_date": payment_entry.posting_date,
			"mode_of_payment": payment_entry.mode_of_payment,
			"paid_from": payment_entry.paid_from,
			"paid_to": payment_entry.paid_to,
			"paid_amount": payment_entry.paid_amount,
			"received_amount": payment_entry.received_amount,
			"reference_no": payment_entry.reference_no,
			"references": [
				{
					"reference_doctype": row.reference_doctype,
					"reference_name": row.reference_name,
					"allocated_amount": row.allocated_amount,
				}
				for row in payment_entry.references
			],
		},
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_7g_hledan_followon_collection(dry_run: bool = False) -> dict[str, Any]:
	"""Create a rounded follow-on collection against the overdue Hledan wholesale power-bank invoice."""

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_7G_HLEDAN_FOLLOWON_COLLECTION
	sales_invoice = frappe.get_doc("Sales Invoice", spec["sales_invoice"])

	if sales_invoice.docstatus != 1:
		frappe.throw(f"Sales Invoice {sales_invoice.name} must be submitted before collection.")
	if float(sales_invoice.outstanding_amount or 0) <= 0:
		frappe.throw(f"Sales Invoice {sales_invoice.name} has no outstanding amount left.")

	payment_entry = get_payment_entry(
		"Sales Invoice",
		sales_invoice.name,
		bank_account=spec["paid_to"],
		reference_date=spec["reference_date"],
	)
	collection_amount = float(spec["received_amount"])
	if collection_amount > float(sales_invoice.outstanding_amount):
		frappe.throw(
			f"Configured follow-on collection {collection_amount} exceeds outstanding {sales_invoice.outstanding_amount} "
			f"for {sales_invoice.name}."
		)

	payment_entry.posting_date = spec["posting_date"]
	payment_entry.paid_to = spec["paid_to"]
	payment_entry.mode_of_payment = spec["mode_of_payment"]
	payment_entry.reference_no = spec["reference_no"]
	payment_entry.reference_date = spec["reference_date"]
	payment_entry.paid_amount = collection_amount
	payment_entry.received_amount = collection_amount
	payment_entry.source_exchange_rate = 1.0
	payment_entry.target_exchange_rate = 1.0
	payment_entry.remarks = (
		f"{spec['remarks']}\n"
		f"Amount MMK {collection_amount} received against Sales Invoice {sales_invoice.name}"
	)
	if payment_entry.references:
		payment_entry.references[0].allocated_amount = collection_amount

	payment_entry.flags.ignore_permissions = True
	payment_entry.insert(ignore_permissions=True)
	payment_entry.submit()

	sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice.name)
	payment_entry = frappe.get_doc("Payment Entry", payment_entry.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_7G_HLEDAN_FOLLOWON_COLLECTION_LABEL,
		"sales_invoice": _summarize_doc(sales_invoice),
		"payment_entry": {
			"doctype": payment_entry.doctype,
			"name": payment_entry.name,
			"docstatus": payment_entry.docstatus,
			"status": getattr(payment_entry, "status", None),
			"posting_date": payment_entry.posting_date,
			"mode_of_payment": payment_entry.mode_of_payment,
			"paid_from": payment_entry.paid_from,
			"paid_to": payment_entry.paid_to,
			"paid_amount": payment_entry.paid_amount,
			"received_amount": payment_entry.received_amount,
			"reference_no": payment_entry.reference_no,
			"references": [
				{
					"reference_doctype": row.reference_doctype,
					"reference_name": row.reference_name,
					"allocated_amount": row.allocated_amount,
				}
				for row in payment_entry.references
			],
		},
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_7i_ko_nay_lin_mandalay_sales_order(
	dry_run: bool = False, auto_commit: bool = True
) -> dict[str, Any]:
	"""Create a current-date Mandalay wholesale top-up Sales Order for an already active Ko Nay Lin lane."""

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_7I_KO_NAY_LIN_MANDALAY_TOPUP["sales_order"]
	item_rows = []

	for row in spec["items"]:
		rate = _get_pilot_price_rate(row["item_code"], spec["selling_price_list"])
		item_rows.append(
			{
				"item_code": row["item_code"],
				"qty": row["qty"],
				"warehouse": row["warehouse"],
				"delivery_date": row["delivery_date"],
				"uom": "Nos",
				"conversion_factor": 1.0,
				"price_list_rate": rate,
				"rate": rate,
			}
		)

	doc = frappe.get_doc(
		{
			"doctype": "Sales Order",
			"naming_series": spec["naming_series"],
			"customer": spec["customer"],
			"company": spec["company"],
			"transaction_date": spec["transaction_date"],
			"delivery_date": spec["delivery_date"],
			"po_no": spec["po_no"],
			"po_date": spec["po_date"],
			"currency": spec["currency"],
			"conversion_rate": spec["conversion_rate"],
			"selling_price_list": spec["selling_price_list"],
			"price_list_currency": spec["price_list_currency"],
			"plc_conversion_rate": spec["plc_conversion_rate"],
			"payment_terms_template": spec["payment_terms_template"],
			"set_warehouse": spec["set_warehouse"],
			"items": item_rows,
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	doc.submit()

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_7I_KO_NAY_LIN_MANDALAY_TOPUP_LABEL,
		"sales_order": _summarize_doc(doc),
	}

	if dry_run:
		frappe.db.rollback()
	elif auto_commit:
		frappe.db.commit()

	return result


def complete_miniphase_7i_ko_nay_lin_mandalay_sale_from_sales_order(
	sales_order_name: str, dry_run: bool = False, auto_commit: bool = True
) -> dict[str, Any]:
	"""Map the current-date Ko Nay Lin Mandalay wholesale Sales Order through delivery and invoice."""

	from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
	from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_7I_KO_NAY_LIN_MANDALAY_TOPUP

	sales_order = frappe.get_doc("Sales Order", sales_order_name)
	if sales_order.docstatus != 1:
		frappe.throw(f"Sales Order {sales_order_name} must be submitted before downstream mapping.")
	if sales_order.customer != spec["sales_order"]["customer"]:
		frappe.throw(
			f"Sales Order {sales_order_name} belongs to {sales_order.customer}, expected {spec['sales_order']['customer']}."
		)
	if sales_order.company != COMPANY_NAME:
		frappe.throw(f"Sales Order {sales_order_name} does not belong to {COMPANY_NAME}.")
	if float(sales_order.per_delivered or 0) > 0 or float(sales_order.per_billed or 0) > 0:
		frappe.throw(
			f"Sales Order {sales_order_name} already has downstream activity "
			f"(delivered={sales_order.per_delivered}, billed={sales_order.per_billed})."
		)

	delivery_note = make_delivery_note(sales_order.name)
	delivery_note.set_posting_time = 1
	delivery_note.posting_date = spec["delivery_note"]["posting_date"]
	delivery_note.posting_time = spec["delivery_note"]["posting_time"]
	delivery_note.lr_date = spec["delivery_note"]["posting_date"]
	delivery_note.remarks = spec["delivery_note"]["remarks"]
	delivery_note.flags.ignore_permissions = True
	delivery_note.insert(ignore_permissions=True)
	delivery_note.submit()

	sales_invoice = make_sales_invoice(delivery_note.name)
	sales_invoice.set_posting_time = 1
	sales_invoice.posting_date = spec["sales_invoice"]["posting_date"]
	sales_invoice.posting_time = spec["sales_invoice"]["posting_time"]
	sales_invoice.due_date = spec["sales_invoice"]["due_date"]
	sales_invoice.payment_terms_template = sales_order.payment_terms_template
	sales_invoice.remarks = spec["sales_invoice"]["remarks"]
	sales_invoice.flags.ignore_permissions = True
	sales_invoice.insert(ignore_permissions=True)
	sales_invoice.submit()

	sales_order = frappe.get_doc("Sales Order", sales_order_name)
	delivery_note = frappe.get_doc("Delivery Note", delivery_note.name)
	sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_7I_KO_NAY_LIN_MANDALAY_TOPUP_LABEL,
		"sales_order": _summarize_doc(sales_order),
		"delivery_note": _summarize_doc(delivery_note),
		"sales_invoice": _summarize_doc(sales_invoice),
	}

	if dry_run:
		frappe.db.rollback()
	elif auto_commit:
		frappe.db.commit()

	return result


def rollout_miniphase_7i_ko_nay_lin_mandalay_sale(dry_run: bool = False) -> dict[str, Any]:
	"""Create and complete the governed current-period Ko Nay Lin Mandalay wholesale lane in one transaction."""

	dry_run = _normalize_truthy(dry_run)

	order_result = create_miniphase_7i_ko_nay_lin_mandalay_sales_order(dry_run=False, auto_commit=False)
	sales_order_name = order_result["sales_order"]["name"]
	downstream_result = complete_miniphase_7i_ko_nay_lin_mandalay_sale_from_sales_order(
		sales_order_name,
		dry_run=False,
		auto_commit=False,
	)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_7I_KO_NAY_LIN_MANDALAY_TOPUP_LABEL,
		"sales_order": downstream_result["sales_order"],
		"delivery_note": downstream_result["delivery_note"],
		"sales_invoice": downstream_result["sales_invoice"],
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def _summarize_quotation(doc: Any) -> dict[str, Any]:
	summary = _summarize_doc(doc)
	summary.update(
		{
			"transaction_date": getattr(doc, "transaction_date", None),
			"valid_till": getattr(doc, "valid_till", None),
			"workflow_state": getattr(doc, "workflow_state", None),
			"party_name": getattr(doc, "party_name", None),
			"selling_price_list": getattr(doc, "selling_price_list", None),
			"payment_terms_template": getattr(doc, "payment_terms_template", None),
			"additional_discount_percentage": getattr(doc, "additional_discount_percentage", None),
			"discount_amount": getattr(doc, "discount_amount", None),
		}
	)
	return summary


def _summarize_sales_order_for_approval(doc: Any) -> dict[str, Any]:
	summary = _summarize_doc(doc)
	summary.update(
		{
			"transaction_date": getattr(doc, "transaction_date", None),
			"delivery_date": getattr(doc, "delivery_date", None),
			"workflow_state": getattr(doc, "workflow_state", None),
			"payment_terms_template": getattr(doc, "payment_terms_template", None),
			"additional_discount_percentage": getattr(doc, "additional_discount_percentage", None),
			"discount_amount": getattr(doc, "discount_amount", None),
		}
	)
	return summary


def _build_sales_console_demo_item_rows(
	items: tuple[dict[str, Any], ...],
	price_list: str,
	warehouse: str,
	delivery_date: str | None = None,
) -> list[dict[str, Any]]:
	rows = []
	for row in items:
		rate = _get_live_item_price_rate(row["item_code"], price_list)
		item_row = {
			"item_code": row["item_code"],
			"qty": row["qty"],
			"uom": "Nos",
			"conversion_factor": 1.0,
			"warehouse": warehouse,
			"price_list_rate": rate,
			"rate": rate,
		}
		if delivery_date:
			item_row["delivery_date"] = delivery_date
		rows.append(item_row)
	return rows


def _create_sales_console_demo_quotation(
	spec: dict[str, Any], dry_run: bool = False, auto_commit: bool = True
) -> dict[str, Any]:
	from frappe.model.workflow import apply_workflow

	dry_run = _normalize_truthy(dry_run)
	existing_names = frappe.get_all(
		"Quotation",
		filters={"party_name": spec["customer"], "terms": spec["terms"]},
		pluck="name",
		limit=2,
	)
	if len(existing_names) > 1:
		frappe.throw(
			f"Found multiple matching demo quotations for {spec['customer']} and terms '{spec['terms']}'."
		)
	if existing_names:
		doc = frappe.get_doc("Quotation", existing_names[0])
		change_type = "existing"
	else:
		item_rows = []
		for row in spec["items"]:
			rate = _get_live_item_price_rate(row["item_code"], spec["selling_price_list"])
			item_rows.append(
				{
					"item_code": row["item_code"],
					"qty": row["qty"],
					"uom": "Nos",
					"conversion_factor": 1.0,
					"warehouse": spec["set_warehouse"],
					"price_list_rate": rate,
					"rate": rate,
				}
			)

		doc = frappe.get_doc(
			{
				"doctype": "Quotation",
				"naming_series": "SAL-QTN-.YYYY.-",
				"quotation_to": "Customer",
				"party_name": spec["customer"],
				"company": spec["company"],
				"order_type": spec["order_type"],
				"transaction_date": spec["transaction_date"],
				"valid_till": spec["valid_till"],
				"currency": "MMK",
				"conversion_rate": 1.0,
				"selling_price_list": spec["selling_price_list"],
				"price_list_currency": "MMK",
				"plc_conversion_rate": 1.0,
				"payment_terms_template": spec["payment_terms_template"],
				"set_warehouse": spec["set_warehouse"],
				"terms": spec["terms"],
				"apply_discount_on": spec.get("apply_discount_on", "Grand Total"),
				"additional_discount_percentage": spec.get("additional_discount_percentage", 0.0),
				"items": item_rows,
			}
		)
		doc.flags.ignore_permissions = True
		doc.insert(ignore_permissions=True)
		change_type = "insert"

	for action in spec["workflow_actions"]:
		doc.reload()
		if doc.workflow_state == spec["target_workflow_state"]:
			break
		doc = apply_workflow(doc, action)
		doc.flags.ignore_permissions = True

	doc.reload()
	if doc.workflow_state != spec["target_workflow_state"]:
		frappe.throw(
			f"Quotation {doc.name} ended in workflow state {doc.workflow_state}, "
			f"expected {spec['target_workflow_state']}."
		)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": PARALLEL_SALES_CONSOLE_QUOTATION_APPROVAL_DEMO_LABEL,
		"change_type": change_type,
		"demo_key": spec["demo_key"],
		"approval_note": spec["approval_note"],
		"quotation": _summarize_quotation(doc),
	}

	if dry_run:
		frappe.db.rollback()
	elif auto_commit:
		frappe.db.commit()

	return result


def rollout_sales_console_quotation_approval_demo(dry_run: bool = False) -> dict[str, Any]:
	"""Create a small realistic quotation set for manager and GM/executive approval queues in Sales Console."""

	dry_run = _normalize_truthy(dry_run)
	results = []

	for spec in SALES_CONSOLE_APPROVAL_DEMO_QUOTATIONS:
		results.append(_create_sales_console_demo_quotation(spec, dry_run=False, auto_commit=False))

	state_counts: dict[str, int] = {}
	for row in results:
		workflow_state = row["quotation"]["workflow_state"]
		state_counts[workflow_state] = state_counts.get(workflow_state, 0) + 1

	final_result = {
		"ok": True,
		"dry_run": dry_run,
		"label": PARALLEL_SALES_CONSOLE_QUOTATION_APPROVAL_DEMO_LABEL,
		"count": len(results),
		"workflow_state_counts": state_counts,
		"quotations": results,
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return final_result


def list_sales_console_quotation_approval_snapshot() -> dict[str, Any]:
	"""Return the current quotation approval snapshot for Sales Console verification."""

	rows = frappe.get_all(
		"Quotation",
		fields=[
			"name",
			"party_name",
			"transaction_date",
			"valid_till",
			"grand_total",
			"workflow_state",
			"docstatus",
			"selling_price_list",
			"payment_terms_template",
			"additional_discount_percentage",
			"discount_amount",
		],
		order_by="creation asc",
	)
	return {
		"ok": True,
		"label": PARALLEL_SALES_CONSOLE_QUOTATION_APPROVAL_DEMO_LABEL,
		"count": len(rows),
		"quotations": rows,
	}


def _create_sales_console_order_demo_chain(
	spec: dict[str, Any], dry_run: bool = False, auto_commit: bool = True
) -> dict[str, Any]:
	from frappe.model.workflow import apply_workflow
	from erpnext.selling.doctype.quotation.quotation import make_sales_order

	dry_run = _normalize_truthy(dry_run)
	quotation_spec = spec["quotation"]
	order_spec = spec["sales_order"]

	existing_quote_names = frappe.get_all(
		"Quotation",
		filters={"party_name": spec["customer"], "terms": quotation_spec["terms"]},
		pluck="name",
		limit=2,
	)
	if len(existing_quote_names) > 1:
		frappe.throw(
			f"Found multiple matching demo quotations for {spec['customer']} and terms '{quotation_spec['terms']}'."
		)

	if existing_quote_names:
		quotation = frappe.get_doc("Quotation", existing_quote_names[0])
		quotation_change_type = "existing"
	else:
		quotation = frappe.get_doc(
			{
				"doctype": "Quotation",
				"naming_series": "SAL-QTN-.YYYY.-",
				"quotation_to": "Customer",
				"party_name": spec["customer"],
				"company": spec["company"],
				"order_type": quotation_spec["order_type"],
				"transaction_date": quotation_spec["transaction_date"],
				"valid_till": quotation_spec["valid_till"],
				"currency": "MMK",
				"conversion_rate": 1.0,
				"selling_price_list": quotation_spec["selling_price_list"],
				"price_list_currency": "MMK",
				"plc_conversion_rate": 1.0,
				"payment_terms_template": quotation_spec["payment_terms_template"],
				"set_warehouse": quotation_spec["set_warehouse"],
				"terms": quotation_spec["terms"],
				"apply_discount_on": quotation_spec.get("apply_discount_on", "Grand Total"),
				"additional_discount_percentage": quotation_spec.get("additional_discount_percentage", 0.0),
				"items": _build_sales_console_demo_item_rows(
					spec["items"],
					quotation_spec["selling_price_list"],
					quotation_spec["set_warehouse"],
				),
			}
		)
		quotation.flags.ignore_permissions = True
		quotation.insert(ignore_permissions=True)
		quotation_change_type = "insert"

	for action in quotation_spec["workflow_actions"]:
		quotation.reload()
		if quotation.workflow_state == quotation_spec["target_workflow_state"]:
			break
		quotation = apply_workflow(quotation, action)
		quotation.flags.ignore_permissions = True

	quotation.reload()
	if quotation.workflow_state != quotation_spec["target_workflow_state"]:
		frappe.throw(
			f"Quotation {quotation.name} ended in workflow state {quotation.workflow_state}, "
			f"expected {quotation_spec['target_workflow_state']}."
		)

	existing_order_names = frappe.get_all(
		"Sales Order",
		filters={"customer": spec["customer"], "po_no": order_spec["po_no"]},
		pluck="name",
		limit=2,
	)
	if len(existing_order_names) > 1:
		frappe.throw(
			f"Found multiple matching demo Sales Orders for {spec['customer']} and PO no {order_spec['po_no']}."
		)

	if existing_order_names:
		sales_order = frappe.get_doc("Sales Order", existing_order_names[0])
		order_change_type = "existing"
	else:
		sales_order = make_sales_order(quotation.name)
		sales_order.transaction_date = quotation_spec["transaction_date"]
		sales_order.delivery_date = order_spec["delivery_date"]
		sales_order.po_no = order_spec["po_no"]
		sales_order.po_date = order_spec["po_date"]
		sales_order.payment_terms_template = order_spec["payment_terms_template"]
		sales_order.set_warehouse = order_spec["set_warehouse"]
		sales_order.remarks = order_spec["remarks"]
		sales_order.apply_discount_on = order_spec.get(
			"apply_discount_on",
			quotation.apply_discount_on or "Grand Total",
		)
		sales_order.additional_discount_percentage = order_spec.get(
			"additional_discount_percentage",
			quotation.additional_discount_percentage or 0.0,
		)
		for item in sales_order.items:
			item.warehouse = order_spec["set_warehouse"]
			item.delivery_date = order_spec["delivery_date"]
		sales_order.flags.ignore_permissions = True
		sales_order.insert(ignore_permissions=True)
		order_change_type = "insert"

	for action in order_spec["workflow_actions"]:
		sales_order.reload()
		if sales_order.workflow_state == order_spec["target_workflow_state"]:
			break
		sales_order = apply_workflow(sales_order, action)
		sales_order.flags.ignore_permissions = True

	sales_order.reload()
	if sales_order.workflow_state != order_spec["target_workflow_state"]:
		frappe.throw(
			f"Sales Order {sales_order.name} ended in workflow state {sales_order.workflow_state}, "
			f"expected {order_spec['target_workflow_state']}."
		)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": PARALLEL_SALES_CONSOLE_SALES_ORDER_APPROVAL_DEMO_LABEL,
		"demo_key": spec["demo_key"],
		"quotation_change_type": quotation_change_type,
		"sales_order_change_type": order_change_type,
		"quotation_approval_note": quotation_spec["approval_note"],
		"quotation": _summarize_quotation(quotation),
		"sales_order": _summarize_sales_order_for_approval(sales_order),
	}

	if dry_run:
		frappe.db.rollback()
	elif auto_commit:
		frappe.db.commit()

	return result


def rollout_sales_console_sales_order_approval_demo(dry_run: bool = False) -> dict[str, Any]:
	"""Create approved quotation upstream docs and blocked Sales Orders for Sales Console approval demo."""

	dry_run = _normalize_truthy(dry_run)
	results = []

	for spec in SALES_CONSOLE_ORDER_APPROVAL_DEMO_CHAINS:
		results.append(_create_sales_console_order_demo_chain(spec, dry_run=False, auto_commit=False))

	state_counts: dict[str, int] = {}
	for row in results:
		workflow_state = row["sales_order"]["workflow_state"]
		state_counts[workflow_state] = state_counts.get(workflow_state, 0) + 1

	final_result = {
		"ok": True,
		"dry_run": dry_run,
		"label": PARALLEL_SALES_CONSOLE_SALES_ORDER_APPROVAL_DEMO_LABEL,
		"count": len(results),
		"workflow_state_counts": state_counts,
		"chains": results,
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return final_result


def list_sales_console_sales_order_approval_snapshot() -> dict[str, Any]:
	"""Return the current blocked Sales Order approval snapshot for Sales Console verification."""

	rows = frappe.get_all(
		"Sales Order",
		fields=[
			"name",
			"customer",
			"transaction_date",
			"delivery_date",
			"po_no",
			"grand_total",
			"workflow_state",
			"docstatus",
			"selling_price_list",
			"payment_terms_template",
			"additional_discount_percentage",
			"discount_amount",
		],
		filters={"workflow_state": ["in", ["Pending Sales Approval", "Pending Executive Approval"]]},
		order_by="creation asc",
	)
	return {
		"ok": True,
		"label": PARALLEL_SALES_CONSOLE_SALES_ORDER_APPROVAL_DEMO_LABEL,
		"count": len(rows),
		"sales_orders": rows,
	}


def rollout_miniphase_6o_supplier_policy_defaults(dry_run: bool = False) -> dict[str, Any]:
	"""Normalize remaining supplier defaults for the procurement control layer."""

	dry_run = _normalize_truthy(dry_run)
	changes = []

	for spec in MINIPHASE_6O_SUPPLIER_POLICY_DEFAULTS:
		supplier = frappe.get_doc("Supplier", spec["supplier"])
		before = {
			"default_price_list": supplier.default_price_list,
			"payment_terms": supplier.payment_terms,
		}

		supplier.default_price_list = spec["default_price_list"]
		supplier.payment_terms = spec["payment_terms"]
		supplier.flags.ignore_permissions = True
		supplier.save(ignore_permissions=True)

		changes.append(
			{
				"supplier": supplier.name,
				"before": before,
				"after": {
					"default_price_list": supplier.default_price_list,
					"payment_terms": supplier.payment_terms,
				},
			}
		)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_6O_SUPPLIER_POLICY_DEFAULTS_LABEL,
		"updated_suppliers": changes,
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_4g_myanmar_tech_realme_replenishment_po(dry_run: bool = False) -> dict[str, Any]:
	"""Create a month-end Myanmar Tech importer PO for Realme C55 based on low projected Yangon Main stock."""

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_4G_MYANMAR_TECH_REALME_PO["purchase_order"]
	expected_bin = spec["expected_bin"]
	item_rows = []

	bin_rows = frappe.get_all(
		"Bin",
		filters={
			"item_code": expected_bin["item_code"],
			"warehouse": expected_bin["warehouse"],
		},
		fields=["actual_qty", "reserved_qty", "ordered_qty", "projected_qty"],
		limit=1,
	)
	if not bin_rows:
		frappe.throw(
			f"No Bin found for {expected_bin['item_code']} in {expected_bin['warehouse']} before month-end replenishment review."
		)

	current_bin = bin_rows[0]
	for fieldname in ("actual_qty", "reserved_qty", "ordered_qty", "projected_qty"):
		expected_value = float(expected_bin[fieldname])
		current_value = float(current_bin.get(fieldname) or 0)
		if not math.isclose(current_value, expected_value, rel_tol=0.0, abs_tol=0.0001):
			frappe.throw(
				f"Mini-Phase 4G month-end PO expects {expected_bin['item_code']} {fieldname} in "
				f"{expected_bin['warehouse']} to be {expected_value}, but found {current_value}."
			)

	for row in spec["items"]:
		item_rows.append(
			{
				"item_code": row["item_code"],
				"qty": row["qty"],
				"warehouse": row["warehouse"],
				"schedule_date": row["schedule_date"],
				"uom": "Nos",
				"conversion_factor": 1.0,
				"price_list_rate": row["rate"],
				"rate": row["rate"],
			}
		)

	doc = frappe.get_doc(
		{
			"doctype": "Purchase Order",
			"naming_series": spec["naming_series"],
			"supplier": spec["supplier"],
			"company": spec["company"],
			"transaction_date": spec["transaction_date"],
			"schedule_date": spec["schedule_date"],
			"currency": spec["currency"],
			"conversion_rate": spec["conversion_rate"],
			"buying_price_list": spec["buying_price_list"],
			"price_list_currency": spec["price_list_currency"],
			"plc_conversion_rate": spec["plc_conversion_rate"],
			"payment_terms_template": spec["payment_terms_template"],
			"set_warehouse": spec["set_warehouse"],
			"remarks": spec["remarks"],
			"items": item_rows,
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	doc.submit()

	doc = frappe.get_doc("Purchase Order", doc.name)
	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_4G_MYANMAR_TECH_REALME_PO_LABEL,
		"purchase_order": _summarize_doc(doc),
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_5a_hledan_catchup_billing(dry_run: bool = False) -> dict[str, Any]:
	"""Catch up billing for an already-delivered Hledan wholesale lane after late-March operational review."""

	from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_5A_HLEDAN_CATCHUP_BILLING

	delivery_note = frappe.get_doc("Delivery Note", spec["delivery_note"])
	if delivery_note.docstatus != 1:
		frappe.throw(f"Delivery Note {delivery_note.name} must be submitted before catch-up billing.")
	if delivery_note.is_return:
		frappe.throw(f"Delivery Note {delivery_note.name} is a return and cannot be used for this catch-up billing.")
	if delivery_note.customer != spec["expected_customer"]:
		frappe.throw(
			f"Delivery Note {delivery_note.name} belongs to {delivery_note.customer}, expected {spec['expected_customer']}."
		)
	if not math.isclose(float(delivery_note.grand_total or 0), float(spec["expected_grand_total"]), rel_tol=0.0, abs_tol=0.0001):
		frappe.throw(
			f"Delivery Note {delivery_note.name} grand total {delivery_note.grand_total} does not match expected "
			f"{spec['expected_grand_total']}."
		)
	if float(delivery_note.per_billed or 0) > 0:
		frappe.throw(
			f"Delivery Note {delivery_note.name} already has billed activity (per_billed={delivery_note.per_billed})."
		)

	source_sales_orders = {row.against_sales_order for row in delivery_note.items if row.against_sales_order}
	if source_sales_orders != {spec["expected_sales_order"]}:
		frappe.throw(
			f"Delivery Note {delivery_note.name} links to sales orders {sorted(source_sales_orders)}, expected "
			f"{spec['expected_sales_order']}."
		)

	sales_order = frappe.get_doc("Sales Order", spec["expected_sales_order"])
	if sales_order.docstatus != 1:
		frappe.throw(f"Sales Order {sales_order.name} must be submitted before catch-up billing.")
	if sales_order.customer != spec["expected_customer"]:
		frappe.throw(
			f"Sales Order {sales_order.name} belongs to {sales_order.customer}, expected {spec['expected_customer']}."
		)
	if float(sales_order.per_delivered or 0) < 100:
		frappe.throw(
			f"Sales Order {sales_order.name} is not fully delivered yet (per_delivered={sales_order.per_delivered})."
		)
	if float(sales_order.per_billed or 0) > 0:
		frappe.throw(
			f"Sales Order {sales_order.name} already has billed activity (per_billed={sales_order.per_billed})."
		)

	sales_invoice = make_sales_invoice(delivery_note.name)
	sales_invoice.set_posting_time = 1
	sales_invoice.posting_date = spec["posting_date"]
	sales_invoice.posting_time = spec["posting_time"]
	sales_invoice.due_date = spec["due_date"]
	sales_invoice.payment_terms_template = spec["payment_terms_template"]
	sales_invoice.remarks = spec["remarks"]
	sales_invoice.flags.ignore_permissions = True
	sales_invoice.insert(ignore_permissions=True)
	sales_invoice.submit()

	delivery_note = frappe.get_doc("Delivery Note", delivery_note.name)
	sales_order = frappe.get_doc("Sales Order", sales_order.name)
	sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_5A_HLEDAN_CATCHUP_BILLING_LABEL,
		"sales_order": _summarize_doc(sales_order),
		"delivery_note": _summarize_doc(delivery_note),
		"sales_invoice": _summarize_doc(sales_invoice),
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_5b_hledan_microsd_catchup_billing(dry_run: bool = False) -> dict[str, Any]:
	"""Catch up billing for the second already-delivered Hledan support lane after late-March operational review."""

	from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_5B_HLEDAN_MICROSD_CATCHUP_BILLING

	delivery_note = frappe.get_doc("Delivery Note", spec["delivery_note"])
	if delivery_note.docstatus != 1:
		frappe.throw(f"Delivery Note {delivery_note.name} must be submitted before catch-up billing.")
	if delivery_note.is_return:
		frappe.throw(f"Delivery Note {delivery_note.name} is a return and cannot be used for this catch-up billing.")
	if delivery_note.customer != spec["expected_customer"]:
		frappe.throw(
			f"Delivery Note {delivery_note.name} belongs to {delivery_note.customer}, expected {spec['expected_customer']}."
		)
	if not math.isclose(float(delivery_note.grand_total or 0), float(spec["expected_grand_total"]), rel_tol=0.0, abs_tol=0.0001):
		frappe.throw(
			f"Delivery Note {delivery_note.name} grand total {delivery_note.grand_total} does not match expected "
			f"{spec['expected_grand_total']}."
		)
	if float(delivery_note.per_billed or 0) > 0:
		frappe.throw(
			f"Delivery Note {delivery_note.name} already has billed activity (per_billed={delivery_note.per_billed})."
		)

	source_sales_orders = {row.against_sales_order for row in delivery_note.items if row.against_sales_order}
	if source_sales_orders != {spec["expected_sales_order"]}:
		frappe.throw(
			f"Delivery Note {delivery_note.name} links to sales orders {sorted(source_sales_orders)}, expected "
			f"{spec['expected_sales_order']}."
		)

	sales_order = frappe.get_doc("Sales Order", spec["expected_sales_order"])
	if sales_order.docstatus != 1:
		frappe.throw(f"Sales Order {sales_order.name} must be submitted before catch-up billing.")
	if sales_order.customer != spec["expected_customer"]:
		frappe.throw(
			f"Sales Order {sales_order.name} belongs to {sales_order.customer}, expected {spec['expected_customer']}."
		)
	if float(sales_order.per_delivered or 0) <= 0:
		frappe.throw(
			f"Sales Order {sales_order.name} has no delivered quantity yet (per_delivered={sales_order.per_delivered})."
		)
	if float(sales_order.per_billed or 0) >= 100:
		frappe.throw(
			f"Sales Order {sales_order.name} is already fully billed (per_billed={sales_order.per_billed})."
		)

	sales_invoice = make_sales_invoice(delivery_note.name)
	sales_invoice.set_posting_time = 1
	sales_invoice.posting_date = spec["posting_date"]
	sales_invoice.posting_time = spec["posting_time"]
	sales_invoice.due_date = spec["due_date"]
	sales_invoice.payment_terms_template = spec["payment_terms_template"]
	sales_invoice.remarks = spec["remarks"]
	sales_invoice.flags.ignore_permissions = True
	sales_invoice.insert(ignore_permissions=True)
	sales_invoice.submit()

	delivery_note = frappe.get_doc("Delivery Note", delivery_note.name)
	sales_order = frappe.get_doc("Sales Order", sales_order.name)
	sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_5B_HLEDAN_MICROSD_CATCHUP_BILLING_LABEL,
		"sales_order": _summarize_doc(sales_order),
		"delivery_note": _summarize_doc(delivery_note),
		"sales_invoice": _summarize_doc(sales_invoice),
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_3b_showroom_sales_order(
	dry_run: bool = False, auto_commit: bool = True
) -> dict[str, Any]:
	"""Create the approved Hledan showroom Sales Order that consumes part of the Mini-Phase 3A top-up."""

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_3B_SHOWROOM_SALE["sales_order"]
	item_rows = []

	for row in spec["items"]:
		rate = _get_pilot_price_rate(row["item_code"], spec["selling_price_list"])
		item_rows.append(
			{
				"item_code": row["item_code"],
				"qty": row["qty"],
				"warehouse": row["warehouse"],
				"delivery_date": row["delivery_date"],
				"uom": "Nos",
				"conversion_factor": 1.0,
				"price_list_rate": rate,
				"rate": rate,
			}
		)

	doc = frappe.get_doc(
		{
			"doctype": "Sales Order",
			"naming_series": spec["naming_series"],
			"customer": spec["customer"],
			"company": spec["company"],
			"transaction_date": spec["transaction_date"],
			"delivery_date": spec["delivery_date"],
			"po_no": spec["po_no"],
			"po_date": spec["po_date"],
			"currency": spec["currency"],
			"conversion_rate": spec["conversion_rate"],
			"selling_price_list": spec["selling_price_list"],
			"price_list_currency": spec["price_list_currency"],
			"plc_conversion_rate": spec["plc_conversion_rate"],
			"payment_terms_template": spec["payment_terms_template"],
			"set_warehouse": spec["set_warehouse"],
			"items": item_rows,
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	doc.submit()

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_3B_SHOWROOM_SALE_LABEL,
		"sales_order": _summarize_doc(doc),
	}

	if dry_run:
		frappe.db.rollback()
	elif auto_commit:
		frappe.db.commit()

	return result


def complete_miniphase_3b_showroom_sale_from_sales_order(
	sales_order_name: str, dry_run: bool = False, auto_commit: bool = True
) -> dict[str, Any]:
	"""Map the approved Hledan showroom Sales Order through delivery, invoice, and KBZ Pay settlement."""

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
	from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
	from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_3B_SHOWROOM_SALE

	sales_order = frappe.get_doc("Sales Order", sales_order_name)
	if sales_order.docstatus != 1:
		frappe.throw(f"Sales Order {sales_order_name} must be submitted before downstream mapping.")
	if sales_order.customer != spec["sales_order"]["customer"]:
		frappe.throw(
			f"Sales Order {sales_order_name} belongs to {sales_order.customer}, expected {spec['sales_order']['customer']}."
		)
	if sales_order.company != COMPANY_NAME:
		frappe.throw(f"Sales Order {sales_order_name} does not belong to {COMPANY_NAME}.")
	if float(sales_order.per_delivered or 0) > 0 or float(sales_order.per_billed or 0) > 0:
		frappe.throw(
			f"Sales Order {sales_order_name} already has downstream activity "
			f"(delivered={sales_order.per_delivered}, billed={sales_order.per_billed})."
		)

	delivery_note = make_delivery_note(sales_order.name)
	delivery_note.set_posting_time = 1
	delivery_note.posting_date = spec["delivery_note"]["posting_date"]
	delivery_note.posting_time = spec["delivery_note"]["posting_time"]
	delivery_note.lr_date = spec["delivery_note"]["posting_date"]
	delivery_note.remarks = spec["delivery_note"]["remarks"]
	delivery_note.flags.ignore_permissions = True
	delivery_note.insert(ignore_permissions=True)
	delivery_note.submit()

	sales_invoice = make_sales_invoice(delivery_note.name)
	sales_invoice.set_posting_time = 1
	sales_invoice.posting_date = spec["sales_invoice"]["posting_date"]
	sales_invoice.posting_time = spec["sales_invoice"]["posting_time"]
	sales_invoice.due_date = spec["sales_invoice"]["due_date"]
	sales_invoice.payment_terms_template = sales_order.payment_terms_template
	sales_invoice.remarks = spec["sales_invoice"]["remarks"]
	sales_invoice.flags.ignore_permissions = True
	sales_invoice.insert(ignore_permissions=True)
	sales_invoice.submit()

	payment_entry = get_payment_entry(
		"Sales Invoice",
		sales_invoice.name,
		bank_account=spec["payment_entry"]["bank_account"],
		reference_date=spec["payment_entry"]["reference_date"],
	)
	payment_entry.posting_date = spec["payment_entry"]["posting_date"]
	payment_entry.mode_of_payment = spec["payment_entry"]["mode_of_payment"]
	payment_entry.reference_no = spec["payment_entry"]["reference_no"]
	payment_entry.reference_date = spec["payment_entry"]["reference_date"]
	payment_entry.remarks = (
		f"{spec['payment_entry']['remarks']}\n"
		f"Amount MMK {payment_entry.received_amount} received against Sales Invoice {sales_invoice.name}"
	)
	payment_entry.flags.ignore_permissions = True
	payment_entry.insert(ignore_permissions=True)
	payment_entry.submit()

	sales_order = frappe.get_doc("Sales Order", sales_order_name)
	delivery_note = frappe.get_doc("Delivery Note", delivery_note.name)
	sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice.name)
	payment_entry = frappe.get_doc("Payment Entry", payment_entry.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_3B_SHOWROOM_SALE_LABEL,
		"sales_order": _summarize_doc(sales_order),
		"delivery_note": _summarize_doc(delivery_note),
		"sales_invoice": _summarize_doc(sales_invoice),
		"payment_entry": {
			"doctype": payment_entry.doctype,
			"name": payment_entry.name,
			"docstatus": payment_entry.docstatus,
			"status": getattr(payment_entry, "status", None),
			"posting_date": payment_entry.posting_date,
			"mode_of_payment": payment_entry.mode_of_payment,
			"paid_from": payment_entry.paid_from,
			"paid_to": payment_entry.paid_to,
			"paid_amount": payment_entry.paid_amount,
			"received_amount": payment_entry.received_amount,
			"reference_no": payment_entry.reference_no,
			"references": [
				{
					"reference_doctype": row.reference_doctype,
					"reference_name": row.reference_name,
					"allocated_amount": row.allocated_amount,
				}
				for row in payment_entry.references
			],
		},
	}

	if dry_run:
		frappe.db.rollback()
	elif auto_commit:
		frappe.db.commit()

	return result


def preview_miniphase_3b_showroom_sale_end_to_end(dry_run: bool = True) -> dict[str, Any]:
	"""Create and map the Mini-Phase 3B showroom sale in one dry-run transaction."""

	dry_run = _normalize_truthy(dry_run)
	order_result = create_miniphase_3b_showroom_sales_order(dry_run=False, auto_commit=False)
	flow_result = complete_miniphase_3b_showroom_sale_from_sales_order(
		order_result["sales_order"]["name"], dry_run=False, auto_commit=False
	)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_3B_SHOWROOM_SALE_LABEL,
		"sales_order": flow_result["sales_order"],
		"delivery_note": flow_result["delivery_note"],
		"sales_invoice": flow_result["sales_invoice"],
		"payment_entry": flow_result["payment_entry"],
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def _cancel_stale_showroom_order(spec: dict[str, str], label: str, dry_run: bool = False) -> dict[str, Any]:
	"""Cancel one stale Sales Order after review confirms the lane should no longer remain open."""

	dry_run = _normalize_truthy(dry_run)
	sales_order = frappe.get_doc("Sales Order", spec["sales_order"])
	replacement_sales_order = None
	if spec.get("replacement_sales_order"):
		replacement_sales_order = frappe.get_doc("Sales Order", spec["replacement_sales_order"])

	if sales_order.docstatus != 1:
		frappe.throw(f"Sales Order {sales_order.name} must be submitted before cancellation.")
	if sales_order.customer != spec["expected_customer"]:
		frappe.throw(
			f"Sales Order {sales_order.name} belongs to {sales_order.customer}, expected {spec['expected_customer']}."
		)
	if sales_order.po_no != spec["expected_po_no"]:
		frappe.throw(
			f"Sales Order {sales_order.name} has PO {sales_order.po_no}, expected {spec['expected_po_no']}."
		)
	if float(sales_order.per_delivered or 0) > 0 or float(sales_order.per_billed or 0) > 0:
		frappe.throw(
			f"Sales Order {sales_order.name} already has downstream activity "
			f"(delivered={sales_order.per_delivered}, billed={sales_order.per_billed})."
		)
	if replacement_sales_order is not None:
		if replacement_sales_order.docstatus != 1 or replacement_sales_order.customer != sales_order.customer:
			frappe.throw(
				f"Replacement Sales Order {replacement_sales_order.name} is not a valid submitted customer follow-on order."
			)
		if float(replacement_sales_order.per_delivered or 0) < 100 or float(replacement_sales_order.per_billed or 0) < 100:
			frappe.throw(
				f"Replacement Sales Order {replacement_sales_order.name} must be fully delivered and billed before stale-order release."
			)

	before = _summarize_doc(sales_order)
	sales_order.cancel()
	sales_order = frappe.get_doc("Sales Order", sales_order.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": label,
		"before_cancel": before,
		"cancelled_sales_order": _summarize_doc(sales_order),
		"replacement_sales_order": _summarize_doc(replacement_sales_order) if replacement_sales_order else None,
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_3c_stale_showroom_order_release(dry_run: bool = False) -> dict[str, Any]:
	"""Cancel the stale January Hledan showroom Sales Order after the fresh April replacement sale."""

	return _cancel_stale_showroom_order(
		MINIPHASE_3C_STALE_SHOWROOM_ORDER_CANCEL,
		MINIPHASE_3C_STALE_SHOWROOM_ORDER_CANCEL_LABEL,
		dry_run=dry_run,
	)


def create_miniphase_3d_stale_showroom_order_release(dry_run: bool = False) -> dict[str, Any]:
	"""Cancel the stale January City Mobile Mart showroom Sales Order after the fresh April replacement sale."""

	return _cancel_stale_showroom_order(
		MINIPHASE_3D_STALE_SHOWROOM_ORDER_CANCEL,
		MINIPHASE_3D_STALE_SHOWROOM_ORDER_CANCEL_LABEL,
		dry_run=dry_run,
	)


def create_miniphase_3e_stale_showroom_order_release(dry_run: bool = False) -> dict[str, Any]:
	"""Cancel the stale January Pazundaung showroom Sales Order after it aged into an expired below-cost lane."""

	return _cancel_stale_showroom_order(
		MINIPHASE_3E_STALE_SHOWROOM_ORDER_CANCEL,
		MINIPHASE_3E_STALE_SHOWROOM_ORDER_CANCEL_LABEL,
		dry_run=dry_run,
	)


def create_miniphase_3f_stale_showroom_order_release(dry_run: bool = False) -> dict[str, Any]:
	"""Cancel the stale January Lanmadaw showroom Sales Order after review confirmed a weak legacy lane."""

	return _cancel_stale_showroom_order(
		MINIPHASE_3F_STALE_SHOWROOM_ORDER_CANCEL,
		MINIPHASE_3F_STALE_SHOWROOM_ORDER_CANCEL_LABEL,
		dry_run=dry_run,
	)


def create_miniphase_4d_stale_wholesale_order_release(dry_run: bool = False) -> dict[str, Any]:
	"""Cancel the stale January Shwe Li wholesale Sales Order after whole-period review confirmed it was abandoned."""

	return _cancel_stale_showroom_order(
		MINIPHASE_4D_STALE_WHOLESALE_ORDER_CANCEL,
		MINIPHASE_4D_STALE_WHOLESALE_ORDER_CANCEL_LABEL,
		dry_run=dry_run,
	)


def create_miniphase_4d_mandalay_stale_wholesale_order_release(dry_run: bool = False) -> dict[str, Any]:
	"""Cancel the stale January Mandalay Mobile Hub wholesale Sales Order after whole-period review confirmed it was abandoned."""

	return _cancel_stale_showroom_order(
		MINIPHASE_4D_MANDALAY_STALE_WHOLESALE_ORDER_CANCEL,
		MINIPHASE_4D_MANDALAY_STALE_WHOLESALE_ORDER_CANCEL_LABEL,
		dry_run=dry_run,
	)


def create_miniphase_4d_latha_stale_wholesale_order_release(dry_run: bool = False) -> dict[str, Any]:
	"""Cancel the stale January Latha wholesale Sales Order after whole-period review confirmed it was abandoned."""

	return _cancel_stale_showroom_order(
		MINIPHASE_4D_LATHA_STALE_WHOLESALE_ORDER_CANCEL,
		MINIPHASE_4D_LATHA_STALE_WHOLESALE_ORDER_CANCEL_LABEL,
		dry_run=dry_run,
	)


def create_miniphase_4d_amarapura_stale_retail_order_release(dry_run: bool = False) -> dict[str, Any]:
	"""Cancel the stale January Amarapura retail Sales Order after whole-period review confirmed it was abandoned."""

	return _cancel_stale_showroom_order(
		MINIPHASE_4D_AMARAPURA_STALE_RETAIL_ORDER_CANCEL,
		MINIPHASE_4D_AMARAPURA_STALE_RETAIL_ORDER_CANCEL_LABEL,
		dry_run=dry_run,
	)


def create_miniphase_4d_mandalay_accessories_stale_wholesale_order_release(dry_run: bool = False) -> dict[str, Any]:
	"""Cancel the stale January Mandalay Accessories wholesale Sales Order after whole-period review confirmed it was abandoned."""

	return _cancel_stale_showroom_order(
		MINIPHASE_4D_MANDALAY_ACCESSORIES_STALE_WHOLESALE_ORDER_CANCEL,
		MINIPHASE_4D_MANDALAY_ACCESSORIES_STALE_WHOLESALE_ORDER_CANCEL_LABEL,
		dry_run=dry_run,
	)


def create_miniphase_4d_zegyo_market_stale_retail_order_release(dry_run: bool = False) -> dict[str, Any]:
	"""Cancel the stale January Zegyo Market retail Sales Order after whole-period review confirmed it was abandoned."""

	return _cancel_stale_showroom_order(
		MINIPHASE_4D_ZEGYO_MARKET_STALE_RETAIL_ORDER_CANCEL,
		MINIPHASE_4D_ZEGYO_MARKET_STALE_RETAIL_ORDER_CANCEL_LABEL,
		dry_run=dry_run,
	)


MINIPHASE_12F_CURRENT_WINDOW_ENTERPRISE_PILOT_LABEL = "Mini-Phase 12F Current-Window Enterprise Pilot Bundle"

MINIPHASE_12F_WHOLESALE_FULL_CHAIN = {
	"customer": "35th Street Mobile Wholesale",
	"company": COMPANY_NAME,
	"items": (
		{"item_code": "SPH-XMI-RN13-8/256", "qty": 2},
		{"item_code": "ACC-PWB-BAS-20K", "qty": 10},
		{"item_code": "ACC-CHR-XMI-33W", "qty": 20},
	),
	"quotation": {
		"transaction_date": "2026-04-11",
		"valid_till": "2026-04-18",
		"selling_price_list": "Wholesale Selling - MMOB",
		"payment_terms_template": "30 Days - MMOB",
		"set_warehouse": "Mandalay Warehouse - MMOB",
		"order_type": "Sales",
		"terms": "Mini-Phase 12F current-window approved quotation / 35th Street / enterprise full-chain replenishment",
		"workflow_actions": ("Submit Quote", "Approve"),
		"target_workflow_state": "Approved",
	},
	"sales_order": {
		"delivery_date": "2026-04-11",
		"po_no": "35ST-MDY-0411-CW1",
		"po_date": "2026-04-11",
		"payment_terms_template": "30 Days - MMOB",
		"set_warehouse": "Mandalay Warehouse - MMOB",
		"remarks": (
			"Mini-Phase 12F current-window approved Mandalay wholesale sales order for 35th Street "
			"after quotation approval and same-day dispatch planning"
		),
		"workflow_actions": ("Submit Order", "Approve"),
		"target_workflow_state": "Approved",
	},
	"delivery_note": {
		"posting_date": "2026-04-11",
		"posting_time": "15:20:00",
		"remarks": "Mini-Phase 12F current-window 35th Street wholesale delivery / Mandalay replenishment lane",
	},
	"sales_invoice": {
		"posting_date": "2026-04-11",
		"posting_time": "15:35:00",
		"due_date": "2026-05-11",
		"remarks": "Mini-Phase 12F current-window 35th Street wholesale invoice / 30-day credit terms",
	},
}

MINIPHASE_12F_SUNFLOWER_PROCUREMENT_FULL_CHAIN = {
	"purchase_order": {
		"naming_series": "PUR-ORD-.YYYY.-",
		"supplier": "Sunflower Accessories Co.",
		"company": COMPANY_NAME,
		"transaction_date": "2026-04-11",
		"schedule_date": "2026-04-11",
		"currency": "MMK",
		"conversion_rate": 1.0,
		"buying_price_list": "Standard Buying - MMOB",
		"price_list_currency": "MMK",
		"plc_conversion_rate": 1.0,
		"payment_terms_template": "15 Days - MMOB",
		"set_warehouse": "Yangon Main Warehouse - MMOB",
		"remarks": (
			"Mini-Phase 12F current-window Sunflower accessories replenishment PO / planned fast-moving "
			"power-bank and charger top-up"
		),
		"items": (
			{
				"item_code": "ACC-PWB-BAS-20K",
				"qty": 50,
				"warehouse": "Yangon Main Warehouse - MMOB",
				"schedule_date": "2026-04-11",
			},
			{
				"item_code": "ACC-CBL-BAS-TC1M",
				"qty": 100,
				"warehouse": "Yangon Main Warehouse - MMOB",
				"schedule_date": "2026-04-11",
			},
			{
				"item_code": "ACC-CHR-XMI-33W",
				"qty": 50,
				"warehouse": "Yangon Main Warehouse - MMOB",
				"schedule_date": "2026-04-11",
			},
		),
	},
	"purchase_receipt": {
		"posting_date": "2026-04-11",
		"posting_time": "16:10:00",
		"supplier_delivery_note": "SFL-DN-0411-CW1",
		"remarks": "Mini-Phase 12F current-window Sunflower accessories receipt / Yangon Main replenishment",
	},
	"purchase_invoice": {
		"posting_date": "2026-04-11",
		"posting_time": "16:25:00",
		"bill_no": "SFL-APR-0411-CW1",
		"bill_date": "2026-04-11",
		"due_date": "2026-04-26",
		"remarks": "Mini-Phase 12F current-window Sunflower supplier invoice / 15-day credit",
	},
}

MINIPHASE_12G_CURRENT_WINDOW_SETTLEMENT_LABEL = "Mini-Phase 12G Current-Window Partial Settlement"

MINIPHASE_12G_35TH_STREET_PARTIAL_COLLECTION = {
	"sales_invoice": "ACC-SINV-2026-00209",
	"posting_date": "2026-04-11",
	"received_amount": 1_500_000,
	"paid_to": "AYA-001-000456 - AYA Bank - Current - MMOB",
	"mode_of_payment": "Bank Transfer",
	"reference_no": "AYA-35ST-0411-CW1",
	"reference_date": "2026-04-11",
	"remarks": (
		"Mini-Phase 12G current-window staged customer collection against the 35th Street "
		"Mandalay replenishment invoice after 12F enterprise pilot execution"
	),
}

MINIPHASE_12G_SUNFLOWER_PARTIAL_SUPPLIER_PAYMENT = {
	"purchase_invoice": "ACC-PINV-2026-00073",
	"posting_date": "2026-04-11",
	"paid_amount": 2_000_000,
	"paid_from": "KBZ-001-000123 - KBZ Bank - Current - MMOB",
	"mode_of_payment": "Bank Transfer",
	"reference_no": "KBZ-SFL-0411-CW1",
	"reference_date": "2026-04-11",
	"remarks": (
		"Mini-Phase 12G current-window staged supplier payment against the Sunflower "
		"accessories replenishment invoice after 12F enterprise pilot execution"
	),
}

MINIPHASE_12H_CURRENT_WINDOW_RETURN_LABEL = "Mini-Phase 12H Current-Window Return Proof"

MINIPHASE_12H_35TH_STREET_SMALL_SALES_RETURN = {
	"delivery_note": "MAT-DN-2026-00024",
	"sales_invoice": "ACC-SINV-2026-00209",
	"posting_date": "2026-04-11",
	"posting_time": "17:10:00",
	"item_code": "ACC-PWB-BAS-20K",
	"qty": 1,
	"warehouse": "Mandalay Warehouse - MMOB",
	"remarks_delivery": (
		"Mini-Phase 12H same-day customer return note / 35th Street / 1 dented power bank "
		"returned before secondary resale in Mandalay"
	),
	"remarks_invoice": (
		"Mini-Phase 12H same-day customer credit note / 35th Street / 1 dented power bank "
		"returned after delivery review in Mandalay"
	),
}

MINIPHASE_12H_SUNFLOWER_SMALL_PURCHASE_RETURN = {
	"purchase_receipt": "MAT-PRE-2026-00016",
	"purchase_invoice": "ACC-PINV-2026-00073",
	"posting_date": "2026-04-11",
	"posting_time": "17:25:00",
	"item_code": "ACC-CHR-XMI-33W",
	"qty": 10,
	"warehouse": "Yangon Main Warehouse - MMOB",
	"remarks_receipt": (
		"Mini-Phase 12H same-day supplier return note / 10 Xiaomi chargers isolated during "
		"Yangon incoming quality review"
	),
	"remarks_invoice": (
		"Mini-Phase 12H same-day supplier debit note / 10 Xiaomi chargers returned after "
		"incoming quality review"
	),
}

MINIPHASE_12I_CURRENT_WINDOW_RECONCILIATION_LABEL = (
	"Mini-Phase 12I Current-Window Reconciliation And Replacement"
)

MINIPHASE_12I_35TH_STREET_CREDIT_SETTLEMENT = {
	"company": COMPANY_NAME,
	"sales_order": "SAL-ORD-2026-00037",
	"sales_invoice": "ACC-SINV-2026-00209",
	"credit_note": "ACC-SINV-2026-00210",
	"posting_date": "2026-04-11",
}

MINIPHASE_12I_SUNFLOWER_REPLACEMENT_AND_DEBIT_SETTLEMENT = {
	"company": COMPANY_NAME,
	"purchase_order": "PUR-ORD-2026-00011",
	"source_return_receipt": "MAT-PRE-2026-00017",
	"purchase_invoice": "ACC-PINV-2026-00073",
	"debit_note": "ACC-PINV-2026-00074",
	"posting_date": "2026-04-11",
	"posting_time": "18:05:00",
	"supplier_delivery_note": "SFL-RPL-0411-CW1",
	"item_code": "ACC-CHR-XMI-33W",
	"qty": 10,
	"warehouse": "Yangon Main Warehouse - MMOB",
	"remarks": (
		"Mini-Phase 12I same-day supplier replacement receipt / 10 Xiaomi chargers "
		"re-delivered after 12H quality return without new supplier billing"
	),
}


def create_miniphase_12f_wholesale_full_chain(
	dry_run: bool = False, auto_commit: bool = True
) -> dict[str, Any]:
	"""Create an approved quotation-to-invoice current-window wholesale chain for 35th Street."""

	from frappe.model.workflow import apply_workflow
	from erpnext.selling.doctype.quotation.quotation import make_sales_order
	from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
	from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_12F_WHOLESALE_FULL_CHAIN
	quotation_spec = spec["quotation"]
	order_spec = spec["sales_order"]

	existing_quote_names = frappe.get_all(
		"Quotation",
		filters={"party_name": spec["customer"], "terms": quotation_spec["terms"]},
		pluck="name",
		limit=2,
	)
	if len(existing_quote_names) > 1:
		frappe.throw(
			f"Found multiple matching 12F quotations for {spec['customer']} and terms '{quotation_spec['terms']}'."
		)

	if existing_quote_names:
		quotation = frappe.get_doc("Quotation", existing_quote_names[0])
		quotation_change_type = "existing"
	else:
		quotation = frappe.get_doc(
			{
				"doctype": "Quotation",
				"naming_series": "SAL-QTN-.YYYY.-",
				"quotation_to": "Customer",
				"party_name": spec["customer"],
				"company": spec["company"],
				"order_type": quotation_spec["order_type"],
				"transaction_date": quotation_spec["transaction_date"],
				"valid_till": quotation_spec["valid_till"],
				"currency": "MMK",
				"conversion_rate": 1.0,
				"selling_price_list": quotation_spec["selling_price_list"],
				"price_list_currency": "MMK",
				"plc_conversion_rate": 1.0,
				"payment_terms_template": quotation_spec["payment_terms_template"],
				"set_warehouse": quotation_spec["set_warehouse"],
				"terms": quotation_spec["terms"],
				"items": _build_sales_console_demo_item_rows(
					spec["items"],
					quotation_spec["selling_price_list"],
					quotation_spec["set_warehouse"],
				),
			}
		)
		quotation.flags.ignore_permissions = True
		quotation.insert(ignore_permissions=True)
		quotation_change_type = "insert"

	for action in quotation_spec["workflow_actions"]:
		quotation.reload()
		if quotation.workflow_state == quotation_spec["target_workflow_state"]:
			break
		quotation = apply_workflow(quotation, action)
		quotation.flags.ignore_permissions = True

	quotation.reload()
	if quotation.workflow_state != quotation_spec["target_workflow_state"]:
		frappe.throw(
			f"Quotation {quotation.name} ended in workflow state {quotation.workflow_state}, "
			f"expected {quotation_spec['target_workflow_state']}."
		)

	existing_order_names = frappe.get_all(
		"Sales Order",
		filters={"customer": spec["customer"], "po_no": order_spec["po_no"]},
		pluck="name",
		limit=2,
	)
	if len(existing_order_names) > 1:
		frappe.throw(
			f"Found multiple matching 12F Sales Orders for {spec['customer']} and PO no {order_spec['po_no']}."
		)

	if existing_order_names:
		sales_order = frappe.get_doc("Sales Order", existing_order_names[0])
		order_change_type = "existing"
	else:
		sales_order = make_sales_order(quotation.name)
		sales_order.transaction_date = quotation_spec["transaction_date"]
		sales_order.delivery_date = order_spec["delivery_date"]
		sales_order.po_no = order_spec["po_no"]
		sales_order.po_date = order_spec["po_date"]
		sales_order.payment_terms_template = order_spec["payment_terms_template"]
		sales_order.set_warehouse = order_spec["set_warehouse"]
		sales_order.remarks = order_spec["remarks"]
		for item in sales_order.items:
			item.warehouse = order_spec["set_warehouse"]
			item.delivery_date = order_spec["delivery_date"]
		sales_order.flags.ignore_permissions = True
		sales_order.insert(ignore_permissions=True)
		order_change_type = "insert"

	for action in order_spec["workflow_actions"]:
		sales_order.reload()
		if sales_order.workflow_state == order_spec["target_workflow_state"]:
			break
		sales_order = apply_workflow(sales_order, action)
		sales_order.flags.ignore_permissions = True

	sales_order.reload()
	if sales_order.workflow_state != order_spec["target_workflow_state"]:
		frappe.throw(
			f"Sales Order {sales_order.name} ended in workflow state {sales_order.workflow_state}, "
			f"expected {order_spec['target_workflow_state']}."
		)

	existing_delivery_names = frappe.get_all(
		"Delivery Note",
		filters={"customer": spec["customer"], "po_no": order_spec["po_no"]},
		pluck="name",
		limit=2,
	)
	if len(existing_delivery_names) > 1:
		frappe.throw(f"Found multiple matching 12F Delivery Notes for {spec['customer']}.")

	if existing_delivery_names:
		delivery_note = frappe.get_doc("Delivery Note", existing_delivery_names[0])
		delivery_change_type = "existing"
	else:
		delivery_note = make_delivery_note(sales_order.name)
		delivery_note.set_posting_time = 1
		delivery_note.posting_date = spec["delivery_note"]["posting_date"]
		delivery_note.posting_time = spec["delivery_note"]["posting_time"]
		delivery_note.lr_date = spec["delivery_note"]["posting_date"]
		delivery_note.remarks = spec["delivery_note"]["remarks"]
		delivery_note.flags.ignore_permissions = True
		delivery_note.insert(ignore_permissions=True)
		delivery_note.submit()
		delivery_change_type = "insert"

	existing_invoice_names = frappe.get_all(
		"Sales Invoice",
		filters={"customer": spec["customer"], "po_no": order_spec["po_no"]},
		pluck="name",
		limit=2,
	)
	if len(existing_invoice_names) > 1:
		frappe.throw(f"Found multiple matching 12F Sales Invoices for {spec['customer']}.")

	if existing_invoice_names:
		sales_invoice = frappe.get_doc("Sales Invoice", existing_invoice_names[0])
		invoice_change_type = "existing"
	else:
		sales_invoice = make_sales_invoice(delivery_note.name)
		sales_invoice.set_posting_time = 1
		sales_invoice.posting_date = spec["sales_invoice"]["posting_date"]
		sales_invoice.posting_time = spec["sales_invoice"]["posting_time"]
		sales_invoice.due_date = spec["sales_invoice"]["due_date"]
		sales_invoice.payment_terms_template = sales_order.payment_terms_template
		sales_invoice.remarks = spec["sales_invoice"]["remarks"]
		sales_invoice.flags.ignore_permissions = True
		sales_invoice.insert(ignore_permissions=True)
		sales_invoice.submit()
		invoice_change_type = "insert"

	quotation = frappe.get_doc("Quotation", quotation.name)
	sales_order = frappe.get_doc("Sales Order", sales_order.name)
	delivery_note = frappe.get_doc("Delivery Note", delivery_note.name)
	sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_12F_CURRENT_WINDOW_ENTERPRISE_PILOT_LABEL,
		"quotation_change_type": quotation_change_type,
		"sales_order_change_type": order_change_type,
		"delivery_note_change_type": delivery_change_type,
		"sales_invoice_change_type": invoice_change_type,
		"quotation": _summarize_quotation(quotation),
		"sales_order": _summarize_doc(sales_order),
		"delivery_note": _summarize_doc(delivery_note),
		"sales_invoice": _summarize_doc(sales_invoice),
	}

	if dry_run:
		frappe.db.rollback()
	elif auto_commit:
		frappe.db.commit()

	return result


def create_miniphase_12f_sunflower_procurement_full_chain(
	dry_run: bool = False, auto_commit: bool = True
) -> dict[str, Any]:
	"""Create a current-window PO to PR to PI accessories replenishment chain for Sunflower."""

	from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt
	from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_12F_SUNFLOWER_PROCUREMENT_FULL_CHAIN
	po_spec = spec["purchase_order"]

	existing_po_names = frappe.get_all(
		"Purchase Order",
		filters={
			"supplier": po_spec["supplier"],
			"transaction_date": po_spec["transaction_date"],
			"schedule_date": po_spec["schedule_date"],
			"set_warehouse": po_spec["set_warehouse"],
		},
		pluck="name",
		limit=2,
	)
	if len(existing_po_names) > 1:
		frappe.throw(f"Found multiple matching 12F Purchase Orders for {po_spec['supplier']}.")

	if existing_po_names:
		purchase_order = frappe.get_doc("Purchase Order", existing_po_names[0])
		order_change_type = "existing"
	else:
		item_rows = []
		for row in po_spec["items"]:
			rate = _get_pilot_purchase_rate(row["item_code"])
			item_rows.append(
				{
					"item_code": row["item_code"],
					"qty": row["qty"],
					"warehouse": row["warehouse"],
					"schedule_date": row["schedule_date"],
					"uom": "Nos",
					"conversion_factor": 1.0,
					"price_list_rate": rate,
					"rate": rate,
				}
			)

		purchase_order = frappe.get_doc(
			{
				"doctype": "Purchase Order",
				"naming_series": po_spec["naming_series"],
				"supplier": po_spec["supplier"],
				"company": po_spec["company"],
				"transaction_date": po_spec["transaction_date"],
				"schedule_date": po_spec["schedule_date"],
				"currency": po_spec["currency"],
				"conversion_rate": po_spec["conversion_rate"],
				"buying_price_list": po_spec["buying_price_list"],
				"price_list_currency": po_spec["price_list_currency"],
				"plc_conversion_rate": po_spec["plc_conversion_rate"],
				"payment_terms_template": po_spec["payment_terms_template"],
				"set_warehouse": po_spec["set_warehouse"],
				"remarks": po_spec["remarks"],
				"items": item_rows,
			}
		)
		purchase_order.flags.ignore_permissions = True
		purchase_order.insert(ignore_permissions=True)
		purchase_order.submit()
		order_change_type = "insert"

	existing_receipt_names = frappe.get_all(
		"Purchase Receipt",
		filters={
			"supplier": po_spec["supplier"],
			"supplier_delivery_note": spec["purchase_receipt"]["supplier_delivery_note"],
		},
		pluck="name",
		limit=2,
	)
	if len(existing_receipt_names) > 1:
		frappe.throw(f"Found multiple matching 12F Purchase Receipts for {po_spec['supplier']}.")

	if existing_receipt_names:
		purchase_receipt = frappe.get_doc("Purchase Receipt", existing_receipt_names[0])
		receipt_change_type = "existing"
	else:
		purchase_receipt = make_purchase_receipt(purchase_order.name)
		purchase_receipt.set_posting_time = 1
		purchase_receipt.posting_date = spec["purchase_receipt"]["posting_date"]
		purchase_receipt.posting_time = spec["purchase_receipt"]["posting_time"]
		purchase_receipt.supplier_delivery_note = spec["purchase_receipt"]["supplier_delivery_note"]
		purchase_receipt.remarks = spec["purchase_receipt"]["remarks"]
		purchase_receipt.flags.ignore_permissions = True
		purchase_receipt.insert(ignore_permissions=True)
		purchase_receipt.submit()
		receipt_change_type = "insert"

	existing_invoice_names = frappe.get_all(
		"Purchase Invoice",
		filters={"supplier": po_spec["supplier"], "bill_no": spec["purchase_invoice"]["bill_no"]},
		pluck="name",
		limit=2,
	)
	if len(existing_invoice_names) > 1:
		frappe.throw(f"Found multiple matching 12F Purchase Invoices for {po_spec['supplier']}.")

	if existing_invoice_names:
		purchase_invoice = frappe.get_doc("Purchase Invoice", existing_invoice_names[0])
		invoice_change_type = "existing"
	else:
		purchase_invoice = make_purchase_invoice(purchase_receipt.name)
		purchase_invoice.set_posting_time = 1
		purchase_invoice.posting_date = spec["purchase_invoice"]["posting_date"]
		purchase_invoice.posting_time = spec["purchase_invoice"]["posting_time"]
		purchase_invoice.bill_no = spec["purchase_invoice"]["bill_no"]
		purchase_invoice.bill_date = spec["purchase_invoice"]["bill_date"]
		purchase_invoice.payment_terms_template = purchase_order.payment_terms_template
		purchase_invoice.due_date = spec["purchase_invoice"]["due_date"]
		for row in purchase_invoice.payment_schedule or []:
			row.due_date = spec["purchase_invoice"]["due_date"]
		purchase_invoice.remarks = spec["purchase_invoice"]["remarks"]
		purchase_invoice.flags.ignore_permissions = True
		purchase_invoice.insert(ignore_permissions=True)
		purchase_invoice.submit()
		invoice_change_type = "insert"

	purchase_order = frappe.get_doc("Purchase Order", purchase_order.name)
	purchase_receipt = frappe.get_doc("Purchase Receipt", purchase_receipt.name)
	purchase_invoice = frappe.get_doc("Purchase Invoice", purchase_invoice.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_12F_CURRENT_WINDOW_ENTERPRISE_PILOT_LABEL,
		"purchase_order_change_type": order_change_type,
		"purchase_receipt_change_type": receipt_change_type,
		"purchase_invoice_change_type": invoice_change_type,
		"purchase_order": _summarize_doc(purchase_order),
		"purchase_receipt": _summarize_doc(purchase_receipt),
		"purchase_invoice": _summarize_doc(purchase_invoice),
	}

	if dry_run:
		frappe.db.rollback()
	elif auto_commit:
		frappe.db.commit()

	return result


def rollout_miniphase_12f_current_window_enterprise_pilot(
	dry_run: bool = False,
) -> dict[str, Any]:
	"""Create a bounded current-window enterprise pilot bundle for both sales and procurement."""

	dry_run = _normalize_truthy(dry_run)

	sales_result = create_miniphase_12f_wholesale_full_chain(dry_run=False, auto_commit=False)
	procurement_result = create_miniphase_12f_sunflower_procurement_full_chain(
		dry_run=False,
		auto_commit=False,
	)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_12F_CURRENT_WINDOW_ENTERPRISE_PILOT_LABEL,
		"sales": sales_result,
		"procurement": procurement_result,
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_12g_35th_street_partial_collection(
	dry_run: bool = False, auto_commit: bool = True
) -> dict[str, Any]:
	"""Create a rounded staged bank-transfer collection against the 12F 35th Street invoice."""

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_12G_35TH_STREET_PARTIAL_COLLECTION
	sales_invoice = frappe.get_doc("Sales Invoice", spec["sales_invoice"])

	if sales_invoice.docstatus != 1:
		frappe.throw(f"Sales Invoice {sales_invoice.name} must be submitted before collection.")
	if float(sales_invoice.outstanding_amount or 0) <= 0:
		frappe.throw(f"Sales Invoice {sales_invoice.name} has no outstanding amount left.")

	existing_payment_names = frappe.get_all(
		"Payment Entry",
		filters={"party_name": sales_invoice.customer, "reference_no": spec["reference_no"]},
		pluck="name",
		limit=2,
	)
	if len(existing_payment_names) > 1:
		frappe.throw(
			f"Found multiple matching 12G customer collections for {sales_invoice.customer} and "
			f"reference {spec['reference_no']}."
		)

	if existing_payment_names:
		payment_entry = frappe.get_doc("Payment Entry", existing_payment_names[0])
		change_type = "existing"
	else:
		payment_entry = get_payment_entry(
			"Sales Invoice",
			sales_invoice.name,
			bank_account=spec["paid_to"],
			reference_date=spec["reference_date"],
		)
		collection_amount = float(spec["received_amount"])
		if collection_amount > float(sales_invoice.outstanding_amount):
			frappe.throw(
				f"Configured 12G collection {collection_amount} exceeds outstanding "
				f"{sales_invoice.outstanding_amount} for {sales_invoice.name}."
			)

		payment_entry.posting_date = spec["posting_date"]
		payment_entry.paid_to = spec["paid_to"]
		payment_entry.mode_of_payment = spec["mode_of_payment"]
		payment_entry.reference_no = spec["reference_no"]
		payment_entry.reference_date = spec["reference_date"]
		payment_entry.paid_amount = collection_amount
		payment_entry.received_amount = collection_amount
		payment_entry.source_exchange_rate = 1.0
		payment_entry.target_exchange_rate = 1.0
		payment_entry.remarks = (
			f"{spec['remarks']}\n"
			f"Amount MMK {collection_amount} received against Sales Invoice {sales_invoice.name}"
		)
		if payment_entry.references:
			payment_entry.references[0].allocated_amount = collection_amount

		payment_entry.flags.ignore_permissions = True
		payment_entry.insert(ignore_permissions=True)
		payment_entry.submit()
		change_type = "insert"

	sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice.name)
	payment_entry = frappe.get_doc("Payment Entry", payment_entry.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_12G_CURRENT_WINDOW_SETTLEMENT_LABEL,
		"customer_collection_change_type": change_type,
		"sales_invoice": _summarize_doc(sales_invoice),
		"payment_entry": _summarize_payment_entry(payment_entry),
	}

	if dry_run:
		frappe.db.rollback()
	elif auto_commit:
		frappe.db.commit()

	return result


def create_miniphase_12g_sunflower_partial_supplier_payment(
	dry_run: bool = False, auto_commit: bool = True
) -> dict[str, Any]:
	"""Create a rounded staged supplier payment against the 12F Sunflower invoice."""

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_12G_SUNFLOWER_PARTIAL_SUPPLIER_PAYMENT
	purchase_invoice = frappe.get_doc("Purchase Invoice", spec["purchase_invoice"])

	if purchase_invoice.docstatus != 1:
		frappe.throw(f"Purchase Invoice {purchase_invoice.name} must be submitted before payment.")
	if float(purchase_invoice.outstanding_amount or 0) <= 0:
		frappe.throw(f"Purchase Invoice {purchase_invoice.name} has no outstanding amount left.")

	existing_payment_names = frappe.get_all(
		"Payment Entry",
		filters={"party_name": purchase_invoice.supplier, "reference_no": spec["reference_no"]},
		pluck="name",
		limit=2,
	)
	if len(existing_payment_names) > 1:
		frappe.throw(
			f"Found multiple matching 12G supplier payments for {purchase_invoice.supplier} and "
			f"reference {spec['reference_no']}."
		)

	if existing_payment_names:
		payment_entry = frappe.get_doc("Payment Entry", existing_payment_names[0])
		change_type = "existing"
	else:
		payment_entry = get_payment_entry("Purchase Invoice", purchase_invoice.name)
		paid_amount = float(spec["paid_amount"])
		if paid_amount > float(purchase_invoice.outstanding_amount):
			frappe.throw(
				f"Configured 12G supplier payment {paid_amount} exceeds outstanding "
				f"{purchase_invoice.outstanding_amount} for {purchase_invoice.name}."
			)

		payment_entry.posting_date = spec["posting_date"]
		payment_entry.paid_from = spec["paid_from"]
		payment_entry.mode_of_payment = spec["mode_of_payment"]
		payment_entry.reference_no = spec["reference_no"]
		payment_entry.reference_date = spec["reference_date"]
		payment_entry.paid_amount = paid_amount
		payment_entry.received_amount = paid_amount
		payment_entry.source_exchange_rate = 1.0
		payment_entry.target_exchange_rate = 1.0
		payment_entry.remarks = (
			f"{spec['remarks']}\n"
			f"Amount MMK {paid_amount} paid against Purchase Invoice {purchase_invoice.name}"
		)
		if payment_entry.references:
			payment_entry.references[0].allocated_amount = paid_amount

		payment_entry.flags.ignore_permissions = True
		payment_entry.insert(ignore_permissions=True)
		payment_entry.submit()
		change_type = "insert"

	purchase_invoice = frappe.get_doc("Purchase Invoice", purchase_invoice.name)
	payment_entry = frappe.get_doc("Payment Entry", payment_entry.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_12G_CURRENT_WINDOW_SETTLEMENT_LABEL,
		"supplier_payment_change_type": change_type,
		"purchase_invoice": _summarize_doc(purchase_invoice),
		"payment_entry": _summarize_payment_entry(payment_entry),
	}

	if dry_run:
		frappe.db.rollback()
	elif auto_commit:
		frappe.db.commit()

	return result


def rollout_miniphase_12g_current_window_partial_settlement(
	dry_run: bool = False,
) -> dict[str, Any]:
	"""Create one bounded customer receipt and one bounded supplier payment after 12F."""

	dry_run = _normalize_truthy(dry_run)

	customer_result = create_miniphase_12g_35th_street_partial_collection(
		dry_run=False,
		auto_commit=False,
	)
	supplier_result = create_miniphase_12g_sunflower_partial_supplier_payment(
		dry_run=False,
		auto_commit=False,
	)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_12G_CURRENT_WINDOW_SETTLEMENT_LABEL,
		"customer_collection": customer_result,
		"supplier_payment": supplier_result,
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def create_miniphase_12h_35th_street_small_sales_return(
	dry_run: bool = False, auto_commit: bool = True
) -> dict[str, Any]:
	"""Create one bounded same-day customer return against the 12F 35th Street lane."""

	from erpnext.controllers.sales_and_purchase_return import make_return_doc

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_12H_35TH_STREET_SMALL_SALES_RETURN
	delivery_note = frappe.get_doc("Delivery Note", spec["delivery_note"])
	sales_invoice = frappe.get_doc("Sales Invoice", spec["sales_invoice"])

	if delivery_note.docstatus != 1:
		frappe.throw(f"Delivery Note {delivery_note.name} must be submitted before return.")
	if sales_invoice.docstatus != 1:
		frappe.throw(f"Sales Invoice {sales_invoice.name} must be submitted before return.")
	if delivery_note.customer != sales_invoice.customer:
		frappe.throw(
			f"Delivery Note {delivery_note.name} customer {delivery_note.customer} does not match "
			f"Sales Invoice {sales_invoice.name} customer {sales_invoice.customer}."
		)

	return_qty = float(spec["qty"])
	if return_qty <= 0:
		frappe.throw("Return quantity must be positive.")

	existing_delivery_return_names = frappe.get_all(
		"Delivery Note",
		filters={
			"is_return": 1,
			"return_against": delivery_note.name,
			"posting_date": spec["posting_date"],
		},
		pluck="name",
		limit=2,
	)
	if len(existing_delivery_return_names) > 1:
		frappe.throw(
			f"Found multiple matching 12H delivery returns against Delivery Note {delivery_note.name}."
		)

	if existing_delivery_return_names:
		delivery_return = frappe.get_doc("Delivery Note", existing_delivery_return_names[0])
		delivery_change_type = "existing"
	else:
		delivery_return = make_return_doc("Delivery Note", delivery_note.name)
		item_trimmed = False
		for row in list(delivery_return.items):
			if row.item_code != spec["item_code"]:
				delivery_return.remove(row)
				continue
			row.qty = -1 * return_qty
			row.stock_qty = -1 * return_qty * float(row.conversion_factor or 1.0)
			row.warehouse = spec["warehouse"]
			item_trimmed = True

		if not item_trimmed or not delivery_return.items:
			frappe.throw(
				f"Item {spec['item_code']} not found on Delivery Note {delivery_note.name} for 12H return mapping."
			)

		delivery_return.set_posting_time = 1
		delivery_return.posting_date = spec["posting_date"]
		delivery_return.posting_time = spec["posting_time"]
		delivery_return.lr_date = spec["posting_date"]
		delivery_return.run_method("calculate_taxes_and_totals")
		delivery_return.flags.ignore_permissions = True
		delivery_return.insert(ignore_permissions=True)
		delivery_return.submit()
		delivery_change_type = "insert"

	existing_sales_return_names = frappe.get_all(
		"Sales Invoice",
		filters={
			"is_return": 1,
			"return_against": sales_invoice.name,
			"posting_date": spec["posting_date"],
		},
		pluck="name",
		limit=2,
	)
	if len(existing_sales_return_names) > 1:
		frappe.throw(
			f"Found multiple matching 12H sales returns against Sales Invoice {sales_invoice.name}."
		)

	if existing_sales_return_names:
		sales_return = frappe.get_doc("Sales Invoice", existing_sales_return_names[0])
		invoice_change_type = "existing"
	else:
		sales_return = make_return_doc("Sales Invoice", sales_invoice.name)
		item_trimmed = False
		for row in list(sales_return.items):
			if row.item_code != spec["item_code"]:
				sales_return.remove(row)
				continue
			row.qty = -1 * return_qty
			row.stock_qty = -1 * return_qty * float(row.conversion_factor or 1.0)
			row.warehouse = spec["warehouse"]
			item_trimmed = True

		if not item_trimmed or not sales_return.items:
			frappe.throw(
				f"Item {spec['item_code']} not found on Sales Invoice {sales_invoice.name} for 12H return mapping."
			)

		sales_return.set_posting_time = 1
		sales_return.posting_date = spec["posting_date"]
		sales_return.posting_time = spec["posting_time"]
		sales_return.due_date = spec["posting_date"]
		sales_return.payment_terms_template = ""
		sales_return.set("payment_schedule", [])
		sales_return.remarks = spec["remarks_invoice"]
		sales_return.run_method("calculate_taxes_and_totals")
		sales_return.flags.ignore_permissions = True
		sales_return.insert(ignore_permissions=True)
		sales_return.submit()
		invoice_change_type = "insert"

	delivery_return = frappe.get_doc("Delivery Note", delivery_return.name)
	sales_return = frappe.get_doc("Sales Invoice", sales_return.name)
	sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_12H_CURRENT_WINDOW_RETURN_LABEL,
		"delivery_return_change_type": delivery_change_type,
		"sales_return_change_type": invoice_change_type,
		"delivery_return": _summarize_doc(delivery_return),
		"sales_return": _summarize_doc(sales_return),
		"source_sales_invoice": _summarize_doc(sales_invoice),
	}

	if dry_run:
		frappe.db.rollback()
	elif auto_commit:
		frappe.db.commit()

	return result


def create_miniphase_12h_sunflower_small_purchase_return(
	dry_run: bool = False, auto_commit: bool = True
) -> dict[str, Any]:
	"""Create one bounded same-day supplier return against the 12F Sunflower lane."""

	from erpnext.controllers.sales_and_purchase_return import make_return_doc

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_12H_SUNFLOWER_SMALL_PURCHASE_RETURN
	purchase_receipt = frappe.get_doc("Purchase Receipt", spec["purchase_receipt"])
	purchase_invoice = frappe.get_doc("Purchase Invoice", spec["purchase_invoice"])

	if purchase_receipt.docstatus != 1:
		frappe.throw(f"Purchase Receipt {purchase_receipt.name} must be submitted before return.")
	if purchase_invoice.docstatus != 1:
		frappe.throw(f"Purchase Invoice {purchase_invoice.name} must be submitted before return.")
	if purchase_receipt.supplier != purchase_invoice.supplier:
		frappe.throw(
			f"Purchase Receipt {purchase_receipt.name} supplier {purchase_receipt.supplier} does not match "
			f"Purchase Invoice {purchase_invoice.name} supplier {purchase_invoice.supplier}."
		)

	return_qty = float(spec["qty"])
	if return_qty <= 0:
		frappe.throw("Return quantity must be positive.")

	existing_receipt_return_names = frappe.get_all(
		"Purchase Receipt",
		filters={
			"is_return": 1,
			"return_against": purchase_receipt.name,
			"posting_date": spec["posting_date"],
		},
		pluck="name",
		limit=2,
	)
	if len(existing_receipt_return_names) > 1:
		frappe.throw(
			f"Found multiple matching 12H supplier return receipts against Purchase Receipt {purchase_receipt.name}."
		)

	if existing_receipt_return_names:
		receipt_return = frappe.get_doc("Purchase Receipt", existing_receipt_return_names[0])
		receipt_change_type = "existing"
	else:
		receipt_return = make_return_doc("Purchase Receipt", purchase_receipt.name)
		item_trimmed = False
		for row in list(receipt_return.items):
			if row.item_code != spec["item_code"]:
				receipt_return.remove(row)
				continue
			row.qty = -1 * return_qty
			row.received_qty = -1 * return_qty
			row.received_stock_qty = -1 * return_qty * float(row.conversion_factor or 1.0)
			row.stock_qty = -1 * return_qty * float(row.conversion_factor or 1.0)
			row.warehouse = spec["warehouse"]
			item_trimmed = True

		if not item_trimmed or not receipt_return.items:
			frappe.throw(
				f"Item {spec['item_code']} not found on Purchase Receipt {purchase_receipt.name} for 12H return mapping."
			)

		receipt_return.set_posting_time = 1
		receipt_return.posting_date = spec["posting_date"]
		receipt_return.posting_time = spec["posting_time"]
		receipt_return.remarks = spec["remarks_receipt"]
		receipt_return.run_method("calculate_taxes_and_totals")
		receipt_return.flags.ignore_permissions = True
		receipt_return.insert(ignore_permissions=True)
		receipt_return.submit()
		receipt_change_type = "insert"

	existing_invoice_return_names = frappe.get_all(
		"Purchase Invoice",
		filters={
			"is_return": 1,
			"return_against": purchase_invoice.name,
			"posting_date": spec["posting_date"],
		},
		pluck="name",
		limit=2,
	)
	if len(existing_invoice_return_names) > 1:
		frappe.throw(
			f"Found multiple matching 12H supplier debit notes against Purchase Invoice {purchase_invoice.name}."
		)

	if existing_invoice_return_names:
		invoice_return = frappe.get_doc("Purchase Invoice", existing_invoice_return_names[0])
		invoice_change_type = "existing"
	else:
		invoice_return = make_return_doc("Purchase Invoice", purchase_invoice.name)
		item_trimmed = False
		for row in list(invoice_return.items):
			if row.item_code != spec["item_code"]:
				invoice_return.remove(row)
				continue
			row.qty = -1 * return_qty
			row.stock_qty = -1 * return_qty * float(row.conversion_factor or 1.0)
			row.warehouse = spec["warehouse"]
			item_trimmed = True

		if not item_trimmed or not invoice_return.items:
			frappe.throw(
				f"Item {spec['item_code']} not found on Purchase Invoice {purchase_invoice.name} for 12H return mapping."
			)

		invoice_return.set_posting_time = 1
		invoice_return.posting_date = spec["posting_date"]
		invoice_return.posting_time = spec["posting_time"]
		invoice_return.due_date = spec["posting_date"]
		invoice_return.payment_terms_template = ""
		invoice_return.set("payment_schedule", [])
		invoice_return.remarks = spec["remarks_invoice"]
		invoice_return.run_method("calculate_taxes_and_totals")
		invoice_return.flags.ignore_permissions = True
		invoice_return.insert(ignore_permissions=True)
		invoice_return.submit()
		invoice_change_type = "insert"

	receipt_return = frappe.get_doc("Purchase Receipt", receipt_return.name)
	invoice_return = frappe.get_doc("Purchase Invoice", invoice_return.name)
	purchase_invoice = frappe.get_doc("Purchase Invoice", purchase_invoice.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_12H_CURRENT_WINDOW_RETURN_LABEL,
		"purchase_receipt_return_change_type": receipt_change_type,
		"purchase_invoice_return_change_type": invoice_change_type,
		"purchase_receipt_return": _summarize_doc(receipt_return),
		"purchase_invoice_return": _summarize_doc(invoice_return),
		"source_purchase_invoice": _summarize_doc(purchase_invoice),
	}

	if dry_run:
		frappe.db.rollback()
	elif auto_commit:
		frappe.db.commit()

	return result


def rollout_miniphase_12h_current_window_return_proof(
	dry_run: bool = False,
) -> dict[str, Any]:
	"""Create one bounded customer return and one bounded supplier return after 12F and 12G."""

	dry_run = _normalize_truthy(dry_run)

	sales_result = create_miniphase_12h_35th_street_small_sales_return(
		dry_run=False,
		auto_commit=False,
	)
	purchase_result = create_miniphase_12h_sunflower_small_purchase_return(
		dry_run=False,
		auto_commit=False,
	)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_12H_CURRENT_WINDOW_RETURN_LABEL,
		"sales_return": sales_result,
		"purchase_return": purchase_result,
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result


def _reconcile_return_note_against_invoice(
	company: str,
	party_type: str,
	party: str,
	invoice_doctype: str,
	source_invoice_name: str,
	return_note_name: str,
	posting_date: str,
) -> dict[str, Any]:
	"""Reconcile one submitted credit/debit note against its live source invoice."""

	from erpnext.accounts.party import get_party_account

	source_invoice = frappe.get_doc(invoice_doctype, source_invoice_name)
	return_note = frappe.get_doc(invoice_doctype, return_note_name)

	if source_invoice.docstatus != 1:
		frappe.throw(f"{invoice_doctype} {source_invoice.name} must be submitted before reconciliation.")
	if return_note.docstatus != 1 or not int(return_note.is_return or 0):
		frappe.throw(
			f"{invoice_doctype} {return_note.name} must be a submitted return document before reconciliation."
		)

	return_outstanding = abs(float(return_note.outstanding_amount or 0))
	if return_outstanding < 0.5:
		return {
			"change_type": "existing",
			"source_invoice": _summarize_doc(source_invoice),
			"return_note": _summarize_doc(return_note),
		}

	pr = frappe.new_doc("Payment Reconciliation")
	pr.company = company
	pr.party_type = party_type
	pr.party = party
	pr.receivable_payable_account = get_party_account(party_type, party, company)
	pr.invoice_name = source_invoice.name
	pr.payment_name = return_note.name
	pr.from_invoice_date = pr.to_invoice_date = source_invoice.posting_date
	pr.from_payment_date = pr.to_payment_date = return_note.posting_date
	pr.get_unreconciled_entries()

	invoice_row = next(
		(row.as_dict() for row in pr.get("invoices") if row.invoice_number == source_invoice.name),
		None,
	)
	if not invoice_row:
		frappe.throw(
			f"Payment Reconciliation could not find source invoice {source_invoice.name} for {party_type} {party}."
		)

	payment_row = next(
		(row.as_dict() for row in pr.get("payments") if row.reference_name == return_note.name),
		None,
	)
	if not payment_row:
		frappe.throw(
			f"Payment Reconciliation could not find return note {return_note.name} for {party_type} {party}."
		)

	pr.allocate_entries(frappe._dict({"invoices": [invoice_row], "payments": [payment_row]}))
	if not pr.get("allocation"):
		frappe.throw(
			f"Payment Reconciliation produced no allocation rows for {return_note.name} against {source_invoice.name}."
		)

	for row in pr.get("allocation"):
		row.debit_or_credit_note_posting_date = posting_date

	pr.validate_allocation()
	pr.reconcile_allocations()

	source_invoice = frappe.get_doc(invoice_doctype, source_invoice.name)
	return_note = frappe.get_doc(invoice_doctype, return_note.name)

	return {
		"change_type": "reconciled",
		"source_invoice": _summarize_doc(source_invoice),
		"return_note": _summarize_doc(return_note),
	}


def create_miniphase_12i_35th_street_credit_settlement(
	dry_run: bool = False, auto_commit: bool = True
) -> dict[str, Any]:
	"""Consume the 12H credit note and formally short-close the live sales order."""

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_12I_35TH_STREET_CREDIT_SETTLEMENT
	sales_order = frappe.get_doc("Sales Order", spec["sales_order"])
	sales_invoice = frappe.get_doc("Sales Invoice", spec["sales_invoice"])
	credit_note = frappe.get_doc("Sales Invoice", spec["credit_note"])

	if sales_order.docstatus != 1:
		frappe.throw(f"Sales Order {sales_order.name} must be submitted before 12I credit settlement.")
	if sales_invoice.customer != sales_order.customer or credit_note.customer != sales_order.customer:
		frappe.throw(
			f"Customer mismatch between Sales Order {sales_order.name}, Sales Invoice {sales_invoice.name}, "
			f"and credit note {credit_note.name}."
		)

	reconciliation_result = _reconcile_return_note_against_invoice(
		spec["company"],
		"Customer",
		sales_order.customer,
		"Sales Invoice",
		sales_invoice.name,
		credit_note.name,
		spec["posting_date"],
	)

	order_close_change_type = "existing"
	sales_order.reload()
	if sales_order.status != "Closed":
		sales_order.update_status("Closed")
		order_close_change_type = "closed"

	sales_order = frappe.get_doc("Sales Order", sales_order.name)
	sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice.name)
	credit_note = frappe.get_doc("Sales Invoice", credit_note.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_12I_CURRENT_WINDOW_RECONCILIATION_LABEL,
		"reconciliation_change_type": reconciliation_result["change_type"],
		"sales_order_close_change_type": order_close_change_type,
		"sales_order": _summarize_doc(sales_order),
		"source_sales_invoice": _summarize_doc(sales_invoice),
		"credit_note": _summarize_doc(credit_note),
	}

	if dry_run:
		frappe.db.rollback()
	elif auto_commit:
		frappe.db.commit()

	return result


def create_miniphase_12i_sunflower_replacement_and_debit_settlement(
	dry_run: bool = False, auto_commit: bool = True
) -> dict[str, Any]:
	"""Receive same-day supplier replacement stock and consume the 12H debit note."""

	from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt

	dry_run = _normalize_truthy(dry_run)
	spec = MINIPHASE_12I_SUNFLOWER_REPLACEMENT_AND_DEBIT_SETTLEMENT
	purchase_order = frappe.get_doc("Purchase Order", spec["purchase_order"])
	source_return_receipt = frappe.get_doc("Purchase Receipt", spec["source_return_receipt"])
	purchase_invoice = frappe.get_doc("Purchase Invoice", spec["purchase_invoice"])
	debit_note = frappe.get_doc("Purchase Invoice", spec["debit_note"])

	if purchase_order.docstatus != 1:
		frappe.throw(
			f"Purchase Order {purchase_order.name} must be submitted before 12I replacement handling."
		)
	if source_return_receipt.docstatus != 1 or not int(source_return_receipt.is_return or 0):
		frappe.throw(
			f"Purchase Receipt {source_return_receipt.name} must be a submitted supplier return before 12I replacement handling."
		)
	if purchase_invoice.supplier != purchase_order.supplier or debit_note.supplier != purchase_order.supplier:
		frappe.throw(
			f"Supplier mismatch between Purchase Order {purchase_order.name}, Purchase Invoice {purchase_invoice.name}, "
			f"and debit note {debit_note.name}."
		)
	if float(purchase_order.per_billed or 0) < 100:
		frappe.throw(
			f"Purchase Order {purchase_order.name} is not fully billed yet; 12I expects a replacement-only receipt."
		)

	existing_receipt_names = frappe.get_all(
		"Purchase Receipt",
		filters={
			"supplier": purchase_order.supplier,
			"supplier_delivery_note": spec["supplier_delivery_note"],
		},
		pluck="name",
		limit=2,
	)
	if len(existing_receipt_names) > 1:
		frappe.throw(
			f"Found multiple matching 12I replacement receipts for {purchase_order.supplier} and "
			f"supplier delivery note {spec['supplier_delivery_note']}."
		)

	if existing_receipt_names:
		replacement_receipt = frappe.get_doc("Purchase Receipt", existing_receipt_names[0])
		receipt_change_type = "existing"
	else:
		purchase_order_row = next(
			(row for row in purchase_order.items if row.item_code == spec["item_code"]),
			None,
		)
		if not purchase_order_row:
			frappe.throw(f"Item {spec['item_code']} not found on Purchase Order {purchase_order.name}.")

		outstanding_qty = float(purchase_order_row.qty or 0) - float(purchase_order_row.received_qty or 0)
		replacement_qty = float(spec["qty"])
		if replacement_qty <= 0:
			frappe.throw("12I replacement quantity must be positive.")
		if replacement_qty > outstanding_qty:
			frappe.throw(
				f"12I replacement quantity {replacement_qty} exceeds open Purchase Order quantity "
				f"{outstanding_qty} for item {spec['item_code']} on {purchase_order.name}."
			)

		replacement_receipt = make_purchase_receipt(purchase_order.name)
		item_mapped = False
		for row in list(replacement_receipt.items):
			if row.item_code != spec["item_code"]:
				replacement_receipt.remove(row)
				continue
			row.qty = replacement_qty
			row.received_qty = replacement_qty
			row.stock_qty = replacement_qty * float(row.conversion_factor or 1.0)
			row.warehouse = spec["warehouse"]
			item_mapped = True

		if not item_mapped or not replacement_receipt.items:
			frappe.throw(
				f"12I replacement mapping did not produce an open receipt row for item {spec['item_code']} "
				f"from Purchase Order {purchase_order.name}."
			)

		replacement_receipt.set_posting_time = 1
		replacement_receipt.posting_date = spec["posting_date"]
		replacement_receipt.posting_time = spec["posting_time"]
		replacement_receipt.supplier_delivery_note = spec["supplier_delivery_note"]
		replacement_receipt.remarks = spec["remarks"]
		replacement_receipt.run_method("calculate_taxes_and_totals")
		replacement_receipt.flags.ignore_permissions = True
		replacement_receipt.insert(ignore_permissions=True)
		replacement_receipt.submit()
		receipt_change_type = "insert"

	reconciliation_result = _reconcile_return_note_against_invoice(
		spec["company"],
		"Supplier",
		purchase_order.supplier,
		"Purchase Invoice",
		purchase_invoice.name,
		debit_note.name,
		spec["posting_date"],
	)

	purchase_order = frappe.get_doc("Purchase Order", purchase_order.name)
	replacement_receipt = frappe.get_doc("Purchase Receipt", replacement_receipt.name)
	purchase_invoice = frappe.get_doc("Purchase Invoice", purchase_invoice.name)
	debit_note = frappe.get_doc("Purchase Invoice", debit_note.name)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_12I_CURRENT_WINDOW_RECONCILIATION_LABEL,
		"replacement_receipt_change_type": receipt_change_type,
		"reconciliation_change_type": reconciliation_result["change_type"],
		"purchase_order": _summarize_doc(purchase_order),
		"replacement_receipt": _summarize_doc(replacement_receipt),
		"source_purchase_invoice": _summarize_doc(purchase_invoice),
		"debit_note": _summarize_doc(debit_note),
	}

	if dry_run:
		frappe.db.rollback()
	elif auto_commit:
		frappe.db.commit()

	return result


def rollout_miniphase_12i_current_window_reconciliation_and_replacement(
	dry_run: bool = False,
) -> dict[str, Any]:
	"""Settle the 12H return documents and restore the supplier lane operationally."""

	dry_run = _normalize_truthy(dry_run)

	customer_result = create_miniphase_12i_35th_street_credit_settlement(
		dry_run=False,
		auto_commit=False,
	)
	supplier_result = create_miniphase_12i_sunflower_replacement_and_debit_settlement(
		dry_run=False,
		auto_commit=False,
	)

	result = {
		"ok": True,
		"dry_run": dry_run,
		"label": MINIPHASE_12I_CURRENT_WINDOW_RECONCILIATION_LABEL,
		"customer_side": customer_result,
		"supplier_side": supplier_result,
	}

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	return result
