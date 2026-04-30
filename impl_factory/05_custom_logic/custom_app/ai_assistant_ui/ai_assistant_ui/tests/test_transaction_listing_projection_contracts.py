import sys
import types
import unittest


_previous_frappe = sys.modules.get("frappe")
fake_frappe = types.ModuleType("frappe")
fake_frappe.get_all = lambda *args, **kwargs: []
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
fake_frappe.db = types.SimpleNamespace(
	exists=lambda *args, **kwargs: False,
	get_value=lambda *args, **kwargs: None,
	sql=lambda *args, **kwargs: [],
)
fake_frappe.get_doc = lambda *args, **kwargs: None
fake_frappe.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
fake_frappe.ValidationError = type("ValidationError", (Exception,), {})
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat.family_adapters import build_normalized_family_artifact
from ai_assistant_ui.qwen_chat.family_rendering import render_normalized_family_response

if _previous_frappe is None and sys.modules.get("frappe") is fake_frappe:
	del sys.modules["frappe"]
elif _previous_frappe is not None:
	sys.modules["frappe"] = _previous_frappe


class TestTransactionListingProjectionContracts(unittest.TestCase):
	def test_payment_entry_adapter_carries_scope_id(self):
		outcome = build_normalized_family_artifact(
			request_id="payment-entry-scope-id",
			compiler_contract={
				"request_id": "payment-entry-scope-id",
				"capability_id": "collections_read",
				"selected_report": "Payment Entry List",
				"requested_dimensions": [],
				"requested_metrics": [],
				"requested_time_scope": "",
			},
			runtime_payload={
				"tool_trace": [
					{
						"tool": "erp_fac-generate_report",
						"detail_obj": {
							"report_name": "Payment Entry List",
							"filters": {"company": "Enterprise Co"},
						},
						"output_obj": {
							"result": {
								"data": [
									{
										"name": "ACC-PAY-0001",
										"posting_date": "2026-04-16",
										"party": "Sunflower Accessories Co.",
										"party_type": "Supplier",
										"received_amount": 2000000,
										"total_allocated_amount": 3500000,
										"docstatus": 1,
									}
								]
							}
						},
					}
				]
			},
			intent_class="transaction_listing",
			preferred_family_id="transaction_listing",
		)
		self.assertEqual(outcome.status, "adapted")
		self.assertEqual(dict(outcome.artifact_contract.dimensions).get("scope_id"), "payment_entry")

	def test_payment_entry_renderer_uses_scope_projection_defaults_when_columns_not_explicit(self):
		artifact_contract = build_normalized_family_artifact(
			request_id="payment-entry-registry-defaults",
			compiler_contract={
				"request_id": "payment-entry-registry-defaults",
				"capability_id": "collections_read",
				"selected_report": "Payment Entry List",
				"requested_dimensions": [],
				"requested_metrics": [],
				"requested_time_scope": "",
			},
			runtime_payload={
				"tool_trace": [
					{
						"tool": "erp_fac-generate_report",
						"detail_obj": {
							"report_name": "Payment Entry List",
							"filters": {"company": "Enterprise Co"},
						},
						"output_obj": {
							"result": {
								"data": [
									{
										"name": "ACC-PAY-0001",
										"posting_date": "2026-04-16",
										"party": "Sunflower Accessories Co.",
										"party_type": "Supplier",
										"received_amount": 2000000,
										"total_allocated_amount": 3500000,
										"docstatus": 1,
									}
								]
							}
						},
					}
				]
			},
			intent_class="transaction_listing",
			preferred_family_id="transaction_listing",
		).artifact_contract
		rendered = render_normalized_family_response(
			request_id="payment-entry-registry-defaults",
			artifact_contract=artifact_contract,
		)
		self.assertEqual(rendered.status, "rendered")
		answer_text = str((rendered.contract.to_payload() if rendered.contract is not None else {}).get("answer_text") or "")
		self.assertIn("| Payment Entry | Posting Date | Party | Received Amount |", answer_text)
		self.assertNotIn("Grand Total", answer_text)

	def test_transaction_listing_title_uses_displayed_row_count_when_limit_exceeds_rows(self):
		artifact_contract = build_normalized_family_artifact(
			request_id="payment-entry-title-display-count",
			compiler_contract={
				"request_id": "payment-entry-title-display-count",
				"capability_id": "collections_read",
				"selected_report": "Payment Entry List",
				"requested_dimensions": [],
				"requested_metrics": [],
				"requested_time_scope": "",
				"target_limit": 10,
			},
			runtime_payload={
				"tool_trace": [
					{
						"tool": "erp_fac-generate_report",
						"detail_obj": {
							"report_name": "Payment Entry List",
							"filters": {"company": "Enterprise Co"},
						},
						"output_obj": {
							"result": {
								"data": [
									{
										"name": "ACC-PAY-0001",
										"posting_date": "2026-04-16",
										"party": "Sunflower Accessories Co.",
										"party_type": "Supplier",
										"received_amount": 2000000,
										"docstatus": 1,
									}
								]
							}
						},
					}
				]
			},
			intent_class="transaction_listing",
			preferred_family_id="transaction_listing",
		).artifact_contract
		rendered = render_normalized_family_response(
			request_id="payment-entry-title-display-count",
			artifact_contract=artifact_contract,
		)
		self.assertEqual(rendered.status, "rendered")
		answer_text = str((rendered.contract.to_payload() if rendered.contract is not None else {}).get("answer_text") or "")
		self.assertIn("Last 1 Payment Entry", answer_text)
		self.assertNotIn("Last 10 Payment Entries", answer_text)

	def test_sales_order_renderer_uses_delivery_date_from_scope_projection_defaults(self):
		artifact_contract = build_normalized_family_artifact(
			request_id="sales-order-registry-defaults",
			compiler_contract={
				"request_id": "sales-order-registry-defaults",
				"capability_id": "sales_order_read",
				"selected_report": "Sales Order List",
				"requested_dimensions": [],
				"requested_metrics": [],
				"requested_time_scope": "",
			},
			runtime_payload={
				"tool_trace": [
					{
						"tool": "erp_fac-generate_report",
						"detail_obj": {
							"report_name": "Sales Order List",
							"filters": {"company": "Enterprise Co"},
						},
						"output_obj": {
							"result": {
								"data": [
									{
										"name": "SAL-ORD-0001",
										"transaction_date": "2026-04-16",
										"delivery_date": "2026-04-18",
										"customer": "Ko Nay Lin Mobile Center",
										"status": "To Deliver and Bill",
										"grand_total": 2600000,
										"total_qty": 10,
										"docstatus": 1,
									}
								]
							}
						},
					}
				]
			},
			intent_class="transaction_listing",
			preferred_family_id="transaction_listing",
		).artifact_contract
		rendered = render_normalized_family_response(
			request_id="sales-order-registry-defaults",
			artifact_contract=artifact_contract,
		)
		self.assertEqual(rendered.status, "rendered")
		answer_text = str((rendered.contract.to_payload() if rendered.contract is not None else {}).get("answer_text") or "")
		self.assertIn("| Sales Order | Transaction Date | Customer | Status | Delivery Date | Grand Total | Quantity |", answer_text)
		self.assertIn("| SAL-ORD-0001 | 2026-04-16 | Ko Nay Lin Mobile Center | To Deliver and Bill | 2026-04-18 | 2,600,000 | 10 |", answer_text)

	def test_purchase_invoice_renderer_uses_supplier_and_outstanding_amount_projection_defaults(self):
		artifact_contract = build_normalized_family_artifact(
			request_id="purchase-invoice-registry-defaults",
			compiler_contract={
				"request_id": "purchase-invoice-registry-defaults",
				"capability_id": "purchase_invoice_read",
				"selected_report": "Purchase Invoice List",
				"requested_dimensions": [],
				"requested_metrics": [],
				"requested_time_scope": "",
			},
			runtime_payload={
				"tool_trace": [
					{
						"tool": "erp_fac-generate_report",
						"detail_obj": {
							"report_name": "Purchase Invoice List",
							"filters": {"company": "Enterprise Co"},
						},
						"output_obj": {
							"result": {
								"data": [
									{
										"name": "ACC-PINV-0001",
										"posting_date": "2026-04-16",
										"supplier": "Myanmar Tech Import Services",
										"status": "Unpaid",
										"grand_total": 22730000,
										"total_qty": 10,
										"outstanding_amount": 17730000,
										"docstatus": 1,
									}
								]
							}
						},
					}
				]
			},
			intent_class="transaction_listing",
			preferred_family_id="transaction_listing",
		).artifact_contract
		rendered = render_normalized_family_response(
			request_id="purchase-invoice-registry-defaults",
			artifact_contract=artifact_contract,
		)
		self.assertEqual(rendered.status, "rendered")
		answer_text = str((rendered.contract.to_payload() if rendered.contract is not None else {}).get("answer_text") or "")
		self.assertIn(
			"| Purchase Invoice | Posting Date | Supplier | Status | Grand Total | Quantity | Outstanding Amount |",
			answer_text,
		)
		self.assertIn(
			"| ACC-PINV-0001 | 2026-04-16 | Myanmar Tech Import Services | Unpaid | 22,730,000 | 10 | 17,730,000 |",
			answer_text,
		)

	def test_purchase_order_renderer_uses_schedule_date_from_scope_projection_defaults(self):
		artifact_contract = build_normalized_family_artifact(
			request_id="purchase-order-registry-defaults",
			compiler_contract={
				"request_id": "purchase-order-registry-defaults",
				"capability_id": "purchase_order_read",
				"selected_report": "Purchase Order List",
				"requested_dimensions": [],
				"requested_metrics": [],
				"requested_time_scope": "",
			},
			runtime_payload={
				"tool_trace": [
					{
						"tool": "erp_fac-generate_report",
						"detail_obj": {
							"report_name": "Purchase Order List",
							"filters": {"company": "Enterprise Co"},
						},
						"output_obj": {
							"result": {
								"data": [
									{
										"name": "PUR-ORD-0001",
										"transaction_date": "2026-04-16",
										"schedule_date": "2026-04-20",
										"supplier": "Myanmar Tech Import Services",
										"status": "To Receive and Bill",
										"grand_total": 7900000,
										"total_qty": 10,
										"docstatus": 1,
									}
								]
							}
						},
					}
				]
			},
			intent_class="transaction_listing",
			preferred_family_id="transaction_listing",
		).artifact_contract
		rendered = render_normalized_family_response(
			request_id="purchase-order-registry-defaults",
			artifact_contract=artifact_contract,
		)
		self.assertEqual(rendered.status, "rendered")
		answer_text = str((rendered.contract.to_payload() if rendered.contract is not None else {}).get("answer_text") or "")
		self.assertIn("| Purchase Order | Transaction Date | Supplier | Status | Schedule Date | Grand Total | Quantity |", answer_text)
		self.assertIn("| PUR-ORD-0001 | 2026-04-16 | Myanmar Tech Import Services | To Receive and Bill | 2026-04-20 | 7,900,000 | 10 |", answer_text)

	def test_purchase_receipt_renderer_uses_supplier_and_quantity_projection_defaults(self):
		artifact_contract = build_normalized_family_artifact(
			request_id="purchase-receipt-registry-defaults",
			compiler_contract={
				"request_id": "purchase-receipt-registry-defaults",
				"capability_id": "purchase_receipt_read",
				"selected_report": "Purchase Receipt List",
				"requested_dimensions": [],
				"requested_metrics": [],
				"requested_time_scope": "",
			},
			runtime_payload={
				"tool_trace": [
					{
						"tool": "erp_fac-generate_report",
						"detail_obj": {
							"report_name": "Purchase Receipt List",
							"filters": {"company": "Enterprise Co"},
						},
						"output_obj": {
							"result": {
								"data": [
									{
										"name": "MAT-PRE-0001",
										"posting_date": "2026-04-16",
										"supplier": "Myanmar Tech Import Services",
										"status": "Completed",
										"grand_total": 22730000,
										"total_qty": 22,
										"docstatus": 1,
									}
								]
							}
						},
					}
				]
			},
			intent_class="transaction_listing",
			preferred_family_id="transaction_listing",
		).artifact_contract
		rendered = render_normalized_family_response(
			request_id="purchase-receipt-registry-defaults",
			artifact_contract=artifact_contract,
		)
		self.assertEqual(rendered.status, "rendered")
		answer_text = str((rendered.contract.to_payload() if rendered.contract is not None else {}).get("answer_text") or "")
		self.assertIn("| Purchase Receipt | Posting Date | Supplier | Status | Grand Total | Quantity |", answer_text)
		self.assertIn("| MAT-PRE-0001 | 2026-04-16 | Myanmar Tech Import Services | Completed | 22,730,000 | 22 |", answer_text)

	def test_purchase_receipt_adapter_carries_scope_id_without_promoting_detail(self):
		outcome = build_normalized_family_artifact(
			request_id="purchase-receipt-scope-id",
			compiler_contract={
				"request_id": "purchase-receipt-scope-id",
				"capability_id": "purchase_receipt_read",
				"selected_report": "Purchase Receipt List",
				"requested_dimensions": [],
				"requested_metrics": [],
				"requested_time_scope": "",
			},
			runtime_payload={
				"tool_trace": [
					{
						"tool": "erp_fac-generate_report",
						"detail_obj": {
							"report_name": "Purchase Receipt List",
							"filters": {"company": "Enterprise Co"},
						},
						"output_obj": {
							"result": {
								"data": [
									{
										"name": "MAT-PRE-0001",
										"posting_date": "2026-04-16",
										"supplier": "Myanmar Tech Import Services",
										"grand_total": 22730000,
										"total_qty": 22,
										"docstatus": 1,
									}
								]
							}
						},
					}
				]
			},
			intent_class="transaction_listing",
			preferred_family_id="transaction_listing",
		)
		self.assertEqual(outcome.status, "adapted")
		self.assertEqual(dict(outcome.artifact_contract.dimensions).get("scope_id"), "purchase_receipt")
		self.assertEqual(dict(outcome.artifact_contract.dimensions).get("source_grain"), "document_list")

	def test_purchase_invoice_adapter_carries_scope_id(self):
		outcome = build_normalized_family_artifact(
			request_id="purchase-invoice-scope-id",
			compiler_contract={
				"request_id": "purchase-invoice-scope-id",
				"capability_id": "purchase_invoice_read",
				"selected_report": "Purchase Invoice List",
				"requested_dimensions": [],
				"requested_metrics": [],
				"requested_time_scope": "",
			},
			runtime_payload={
				"tool_trace": [
					{
						"tool": "erp_fac-generate_report",
						"detail_obj": {
							"report_name": "Purchase Invoice List",
							"filters": {"company": "Enterprise Co"},
						},
						"output_obj": {
							"result": {
								"data": [
									{
										"name": "ACC-PINV-0001",
										"posting_date": "2026-04-16",
										"supplier": "Myanmar Tech Import Services",
										"grand_total": 22730000,
										"outstanding_amount": 17730000,
										"docstatus": 1,
									}
								]
							}
						},
					}
				]
			},
			intent_class="transaction_listing",
			preferred_family_id="transaction_listing",
		)
		self.assertEqual(outcome.status, "adapted")
		self.assertEqual(dict(outcome.artifact_contract.dimensions).get("scope_id"), "purchase_invoice")


if __name__ == "__main__":
	unittest.main()
