import sys
import types
import unittest


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
from ai_assistant_ui.qwen_chat.family_followup import (
	refine_local_family_artifact,
	render_local_family_followup,
	supports_local_family_followup,
)


def _payment_entry_artifact():
	outcome = build_normalized_family_artifact(
		request_id="payment-entry-followup",
		compiler_contract={
			"request_id": "payment-entry-followup",
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
									"name": "ACC-PAY-0002",
									"posting_date": "2026-04-16",
									"party": "Sunflower Accessories Co.",
									"party_type": "Supplier",
									"received_amount": 2000000,
									"total_allocated_amount": 3500000,
									"docstatus": 1,
								},
								{
									"name": "ACC-PAY-0001",
									"posting_date": "2026-04-15",
									"party": "Myanmar Tech Import Services",
									"party_type": "Supplier",
									"received_amount": 1000000,
									"total_allocated_amount": 1500000,
									"docstatus": 1,
								},
							]
						}
					},
				}
			]
		},
		intent_class="transaction_listing",
		preferred_family_id="transaction_listing",
	)
	return outcome.artifact_contract.to_payload()


def _purchase_invoice_artifact():
	outcome = build_normalized_family_artifact(
		request_id="purchase-invoice-followup",
		compiler_contract={
			"request_id": "purchase-invoice-followup",
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
									"name": "ACC-PINV-0002",
									"posting_date": "2026-04-16",
									"supplier": "Golden Dragon Trading Co. Ltd.",
									"status": "Overdue",
									"grand_total": 30860000,
									"total_qty": 532,
									"outstanding_amount": 30860000,
									"docstatus": 1,
								},
								{
									"name": "ACC-PINV-0001",
									"posting_date": "2026-04-15",
									"supplier": "Myanmar Tech Import Services",
									"status": "Partly Paid",
									"grand_total": 22730000,
									"total_qty": 10,
									"outstanding_amount": 17730000,
									"docstatus": 1,
								},
							]
						}
					},
				}
			]
		},
		intent_class="transaction_listing",
		preferred_family_id="transaction_listing",
	)
	return outcome.artifact_contract.to_payload()


class TestTransactionListingCarryoverContracts(unittest.TestCase):
	def test_transaction_listing_supports_local_column_refinement(self):
		self.assertTrue(
			supports_local_family_followup(
				_payment_entry_artifact(),
				requested_columns=["document_name", "posting_date", "party_name", "received_amount"],
				requested_modes=["column_refinement"],
			)
		)

	def test_transaction_listing_refine_updates_metric_label_for_local_metric_refinement(self):
		refined = refine_local_family_artifact(
			request_id="payment-entry-metric-refine",
			artifact_payload=_payment_entry_artifact(),
			target_metric="total_allocated_amount",
			requested_modes=["metric_refinement"],
		)
		dimensions = dict(refined.get("dimensions") or {})
		self.assertEqual(dimensions.get("primary_metric_key"), "total_allocated_amount")
		self.assertEqual(dimensions.get("primary_metric_label"), "Total Allocated Amount")

	def test_transaction_listing_local_followup_renders_refined_metric_column(self):
		rendered = render_local_family_followup(
			request_id="payment-entry-metric-render",
			artifact_payload=_payment_entry_artifact(),
			target_metric="total_allocated_amount",
			requested_columns=["document_name", "posting_date", "party_name", "total_allocated_amount"],
			requested_modes=["metric_refinement", "column_refinement"],
		)
		answer_text = str(rendered.get("answer_text") or "")
		self.assertIn("| Payment Entry | Posting Date | Party | Total Allocated Amount |", answer_text)
		self.assertIn("| ACC-PAY-0002 | 2026-04-16 | Sunflower Accessories Co. | 3,500,000 |", answer_text)

	def test_transaction_listing_local_followup_honors_ascending_sort_and_limit(self):
		rendered = render_local_family_followup(
			request_id="payment-entry-ascending-render",
			artifact_payload=_payment_entry_artifact(),
			target_limit=1,
			sort_direction="asc",
			requested_modes=["sort_or_limit"],
		)
		answer_text = str(rendered.get("answer_text") or "")
		self.assertIn("First 1 Payment Entry", answer_text)
		self.assertIn("| ACC-PAY-0001 | 2026-04-15 | Myanmar Tech Import Services | 1,000,000 |", answer_text)
		self.assertNotIn("ACC-PAY-0002", answer_text)

	def test_purchase_invoice_supports_local_column_refinement(self):
		self.assertTrue(
			supports_local_family_followup(
				_purchase_invoice_artifact(),
				requested_columns=["document_name", "posting_date", "supplier", "outstanding_amount"],
				requested_modes=["column_refinement"],
			)
		)

	def test_purchase_invoice_local_followup_renders_supplier_and_outstanding_amount(self):
		rendered = render_local_family_followup(
			request_id="purchase-invoice-column-render",
			artifact_payload=_purchase_invoice_artifact(),
			requested_columns=["document_name", "posting_date", "supplier", "outstanding_amount"],
			requested_modes=["column_refinement"],
		)
		answer_text = str(rendered.get("answer_text") or "")
		self.assertIn("| Purchase Invoice | Posting Date | Supplier | Outstanding Amount |", answer_text)
		self.assertIn("| ACC-PINV-0002 | 2026-04-16 | Golden Dragon Trading Co. Ltd. | 30,860,000 |", answer_text)
		self.assertIn("| ACC-PINV-0001 | 2026-04-15 | Myanmar Tech Import Services | 17,730,000 |", answer_text)
		self.assertNotIn("Total Grand Total", answer_text)
		self.assertNotIn("Grand Total", answer_text)


if __name__ == "__main__":
	unittest.main()
