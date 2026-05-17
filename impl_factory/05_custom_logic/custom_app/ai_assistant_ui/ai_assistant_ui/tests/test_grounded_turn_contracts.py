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

from ai_assistant_ui.qwen_chat.contracts import (
	build_grounded_turn_context,
	build_interaction_contract,
)


class TestGroundedTurnContracts(unittest.TestCase):
	def test_grounded_turn_preserves_family_context_when_report_matches_artifact(self):
		interaction = build_interaction_contract(
			request_id="outer-request",
			session_id="session-1",
			user_id="Administrator",
			site_name="erpai_prj1",
			raw_message="show me purchase invoices",
		)

		grounded_turn = build_grounded_turn_context(
			request_id="outer-request",
			interaction_contract=interaction,
			assistant_payload={},
			runtime_payload={
				"ok": True,
				"request_id": "outer-request",
				"tool_trace": [
					{
						"tool": "erp_fac-generate_report",
						"detail_obj": {
							"report_name": "Purchase Invoice List",
							"filters": {"company": "Enterprise Co"},
						},
						"output_obj": {
							"result": {
								"columns": ["Purchase Invoice", "Posting Date", "Supplier", "Grand Total"],
								"data": [
									{
										"name": "ACC-PINV-0001",
										"posting_date": "2026-04-15",
										"supplier": "Myanmar Tech Import Services",
										"grand_total": 22730000,
									}
								],
							}
						},
					}
				],
			},
			artifact_payload={
				"type": "qwen_normalized_family_artifact_contract",
				"artifact_type": "normalized_family_artifact",
				"request_id": "compiler-request",
				"family_id": "transaction_listing",
				"source_reports": ["Purchase Invoice List"],
				"dimensions": {"scope_id": "purchase_invoice"},
			},
		)

		self.assertIsNotNone(grounded_turn)
		self.assertEqual(str(grounded_turn.artifact_family_id or "").strip(), "transaction_listing")
		self.assertEqual(list(grounded_turn.artifact_source_reports or []), ["Purchase Invoice List"])


if __name__ == "__main__":
	unittest.main()
