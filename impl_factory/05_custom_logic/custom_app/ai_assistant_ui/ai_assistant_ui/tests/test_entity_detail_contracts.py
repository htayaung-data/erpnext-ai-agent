import sys
import types
import unittest
from unittest.mock import patch


fake_frappe = types.ModuleType("frappe")
fake_frappe.db = types.SimpleNamespace(
	exists=lambda *args, **kwargs: False,
	get_value=lambda *args, **kwargs: None,
	sql=lambda *args, **kwargs: [],
)
fake_frappe.get_doc = lambda *args, **kwargs: None
fake_frappe.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
fake_frappe.ValidationError = type("ValidationError", (Exception,), {})
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat import entity_detail as entity_detail_module
from ai_assistant_ui.qwen_chat import boundary_support as boundary_support_module


class _FakeDoc:
	def __init__(self, **kwargs):
		self._payload = dict(kwargs)
		for key, value in kwargs.items():
			setattr(self, key, value)

	def get(self, key, default=None):
		return self._payload.get(key, default)


class TestEntityDetailContracts(unittest.TestCase):
	def test_detect_entity_drilldown_request_resolves_explicit_sales_invoice_identifier(self):
		with patch.object(
			entity_detail_module.frappe.db,
			"exists",
			side_effect=lambda doctype, name: doctype == "Sales Invoice" and name == "ACC-SINV-2026-00194",
		), patch.object(entity_detail_module, "_resolve_item_name", return_value=("", "")):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="tell me more about ACC-SINV-2026-00194",
				artifact_payload=None,
				grounded_turn=None,
			)
		self.assertEqual(outcome["entity_type"], "sales_invoice")
		self.assertEqual(outcome["entity_key"], "ACC-SINV-2026-00194")
		self.assertEqual(outcome["source"], "explicit_identifier")

	def test_detect_entity_drilldown_request_resolves_explicit_delivery_note_identifier(self):
		with patch.object(
			entity_detail_module.frappe.db,
			"exists",
			side_effect=lambda doctype, name: doctype == "Delivery Note" and name == "MAT-DN-2026-00016",
		), patch.object(entity_detail_module, "_resolve_item_name", return_value=("", "")):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="tell me more about MAT-DN-2026-00016",
				artifact_payload=None,
				grounded_turn=None,
			)
		self.assertEqual(outcome["entity_type"], "delivery_note")
		self.assertEqual(outcome["entity_key"], "MAT-DN-2026-00016")
		self.assertEqual(outcome["source"], "explicit_identifier")

	def test_detect_entity_drilldown_request_uses_transaction_listing_delivery_note_context(self):
		with patch.object(entity_detail_module.frappe.db, "exists", return_value=False):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="tell me more about MAT-DN-2026-00016",
				artifact_payload={
					"family_id": "transaction_listing",
					"dimensions": {"document_entity_type": "delivery_note"},
					"sections": {"transaction_rows": [{"document_name": "MAT-DN-2026-00016"}]},
				},
				grounded_turn=None,
			)
		self.assertEqual(outcome["entity_type"], "delivery_note")
		self.assertEqual(outcome["entity_key"], "MAT-DN-2026-00016")
		self.assertEqual(outcome["source"], "artifact_context")

	def test_execute_entity_drilldown_supports_delivery_note(self):
		fake_doc = _FakeDoc(
			name="MAT-DN-2026-00016",
			posting_date="2026-03-30",
			customer="Thaketa Mobile Exchange",
			status="Return",
			return_against="MAT-DN-2026-00014",
			total_qty=-2,
			grand_total=-36000,
			delivery_trip="",
			company="Mingalar Mobile Distribution Co., Ltd.",
			is_return=1,
			per_billed=0,
			items=[
				types.SimpleNamespace(
					item_code="ACC-CHR-XMI-33W",
					item_name="Xiaomi Fast Charger 33W",
					qty=-2,
					amount=-36000,
					net_amount=-36000,
					against_sales_order="SAL-ORD-2026-00025",
				)
			],
		)
		with patch.object(entity_detail_module.frappe, "get_doc", return_value=fake_doc), patch.object(
			entity_detail_module,
			"narrate_governed_artifact",
			return_value={
				"ok": True,
				"answer_text": "MAT-DN-2026-00016 is a return delivery note.",
				"agent_meta": {"engine": "artifact_narrative"},
			},
		):
			outcome = entity_detail_module.execute_entity_drilldown(
				request_id="delivery-note-detail",
				session_id="session-1",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="tell me more about MAT-DN-2026-00016",
				entity_reference={"entity_type": "delivery_note", "entity_key": "MAT-DN-2026-00016"},
				response_policy={},
				grounded_turn={"company": "Mingalar Mobile Distribution Co., Ltd."},
			)
		self.assertTrue(outcome["ok"])
		self.assertIn("MAT-DN-2026-00016", outcome["answer_text"])
		artifact = outcome["artifact_payload"]
		self.assertEqual(artifact["dimensions"]["entity_type"], "delivery_note")
		self.assertEqual(artifact["sections"]["document_rows"][0]["return_against"], "MAT-DN-2026-00014")
		self.assertEqual(artifact["sections"]["item_rows"][0]["against_sales_order"], "SAL-ORD-2026-00025")
		self.assertEqual(outcome["rendered_response_payload"]["source_reports"], ["Delivery Note"])
		grounded = outcome["grounded_turn_payload"]
		self.assertEqual(grounded["known_entities"][0]["entity_type"], "delivery_note")
		self.assertIn("MAT-DN-2026-00016", grounded["known_documents"])

	def test_execute_entity_drilldown_populates_sales_invoice_delivery_proof(self):
		fake_doc = _FakeDoc(
			name="ACC-SINV-2026-00194",
			posting_date="2026-03-30",
			customer="Zegyo Mobile Supply House",
			status="Partly Paid",
			due_date="2026-04-07",
			grand_total=795000,
			outstanding_amount=495000,
			company="Mingalar Mobile Distribution Co., Ltd.",
			is_return=0,
			update_stock=0,
			items=[
				types.SimpleNamespace(
					item_code="SPH-OPP-A58-6/128",
					item_name="OPPO A58 (6GB 128GB)",
					qty=1,
					amount=795000,
					net_amount=795000,
					delivery_note="MAT-DN-2026-00011",
					dn_detail="a9uhijifia",
					sales_order="SAL-ORD-2026-00022",
				)
			],
		)
		with patch.object(entity_detail_module.frappe, "get_doc", return_value=fake_doc), patch.object(
			entity_detail_module.frappe.db,
			"get_value",
			side_effect=lambda doctype, name, fields, as_dict=False: {
				"name": "MAT-DN-2026-00011",
				"docstatus": 1,
				"status": "Completed",
				"posting_date": "2026-03-30",
				"is_return": 0,
				"return_against": "",
			}
			if doctype == "Delivery Note" and name == "MAT-DN-2026-00011"
			else None,
		), patch.object(
			entity_detail_module,
			"narrate_governed_artifact",
			return_value={
				"ok": True,
				"answer_text": "ACC-SINV-2026-00194 has governed delivery proof.",
				"agent_meta": {"engine": "artifact_narrative"},
			},
		):
			outcome = entity_detail_module.execute_entity_drilldown(
				request_id="sales-invoice-proof",
				session_id="session-1",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="tell me more about ACC-SINV-2026-00194",
				entity_reference={"entity_type": "sales_invoice", "entity_key": "ACC-SINV-2026-00194"},
				response_policy={},
				grounded_turn={"company": "Mingalar Mobile Distribution Co., Ltd."},
			)
		self.assertTrue(outcome["ok"])
		artifact = outcome["artifact_payload"]
		delivery_proof = artifact["sections"]["delivery_proof"][0]
		self.assertEqual(delivery_proof["proof_state"], "direct_delivery_proven_via_linked_delivery_note")
		self.assertEqual(delivery_proof["submitted_delivery_notes"], ["MAT-DN-2026-00011"])
		self.assertEqual(delivery_proof["submitted_delivery_dates"], ["2026-03-30"])
		self.assertEqual(delivery_proof["sales_orders"], ["SAL-ORD-2026-00022"])
		self.assertEqual(artifact["sections"]["item_rows"][0]["delivery_note"], "MAT-DN-2026-00011")

	def test_grounded_artifact_direct_evidence_answer_confirms_supported_invoice_delivery_proof(self):
		answer = boundary_support_module.grounded_artifact_direct_evidence_answer(
			raw_message="items from this invoice are already delivered?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {"entity_type": "sales_invoice", "entity_label": "ACC-SINV-2026-00194"},
				"sections": {
					"document_rows": [{"customer": "Zegyo Mobile Supply House"}],
					"item_rows": [{"item_name": "OPPO A58 (6GB 128GB)", "qty": 1}],
					"delivery_proof": [
						{
							"proof_state": "direct_delivery_proven_via_linked_delivery_note",
							"submitted_delivery_notes": ["MAT-DN-2026-00011"],
						}
					]
				},
			},
			grounded_turn={"source_name": "ACC-SINV-2026-00194 Detail"},
		)
		self.assertIn("has already been delivered", answer)
		self.assertIn("Zegyo Mobile Supply House", answer)
		self.assertIn("OPPO A58", answer)
		self.assertIn("MAT-DN-2026-00011", answer)
		self.assertNotIn("direct governed proof", answer.lower())

	def test_grounded_artifact_direct_evidence_answer_returns_delivery_date_when_requested(self):
		answer = boundary_support_module.grounded_artifact_direct_evidence_answer(
			raw_message="what it was delivered",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {"entity_type": "sales_invoice", "entity_label": "ACC-SINV-2026-00194"},
				"sections": {
					"document_rows": [{"customer": "Zegyo Mobile Supply House", "posting_date": "2026-03-30"}],
					"item_rows": [{"item_name": "OPPO A58 (6GB 128GB)", "qty": 1}],
					"delivery_proof": [
						{
							"proof_state": "direct_delivery_proven_via_linked_delivery_note",
							"submitted_delivery_notes": ["MAT-DN-2026-00011"],
							"submitted_delivery_dates": ["2026-03-30"],
						}
					]
				},
			},
			grounded_turn={"source_name": "ACC-SINV-2026-00194 Detail"},
		)
		self.assertIn("2026-03-30", answer)
		self.assertIn("MAT-DN-2026-00011", answer)

	def test_build_grounded_artifact_direct_evidence_rendered_payload_includes_relevant_delivery_context(self):
		rendered = boundary_support_module.build_grounded_artifact_direct_evidence_rendered_payload(
			raw_message="that item is already delivered to the customer?",
			artifact_payload={
				"family_id": "entity_detail",
				"request_id": "delivery-proof-render",
				"source_reports": ["Sales Invoice"],
				"dimensions": {"entity_type": "sales_invoice", "entity_label": "ACC-SINV-2026-00194"},
				"sections": {
					"document_rows": [{"customer": "Zegyo Mobile Supply House"}],
					"item_rows": [{"item_name": "OPPO A58 (6GB 128GB)", "qty": 1}],
					"delivery_proof": [
						{
							"proof_state": "direct_delivery_proven_via_linked_delivery_note",
							"proof_method": "linked_delivery_note",
							"submitted_delivery_notes": ["MAT-DN-2026-00011"],
							"submitted_delivery_dates": ["2026-03-30"],
							"sales_orders": ["SAL-ORD-2026-00022"],
							"delivery_notes": [
								{
									"delivery_note": "MAT-DN-2026-00011",
									"docstatus": 1,
									"status": "Completed",
									"posting_date": "2026-03-30",
									"is_return": 0,
									"return_against": "",
								}
							],
						}
					],
				},
			},
			grounded_turn={"source_name": "ACC-SINV-2026-00194 Detail"},
		)
		self.assertEqual(rendered["renderer_id"], "grounded_artifact_direct_evidence")
		self.assertIn("Delivery Note", rendered["source_reports"])
		blocks = rendered["blocks"]
		self.assertTrue(any(block.get("title") == "Delivery Evidence" for block in blocks))
		self.assertTrue(any(block.get("title") == "Linked Delivery Notes" for block in blocks))
		summary_rows = next(block for block in blocks if block.get("title") == "Delivery Evidence")["rows"]
		self.assertIn(["Recorded Delivery Date", "2026-03-30"], summary_rows)
		self.assertIn(["Linked Delivery Notes", "MAT-DN-2026-00011"], summary_rows)
		self.assertIn(["Linked Sales Orders", "SAL-ORD-2026-00022"], summary_rows)

	def test_grounded_artifact_direct_evidence_answer_stays_empty_without_direct_proof(self):
		answer = boundary_support_module.grounded_artifact_direct_evidence_answer(
			raw_message="items from this invoice are already delivered?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {"entity_type": "sales_invoice", "entity_label": "ACC-SINV-2026-00192"},
				"sections": {
					"delivery_proof": [
						{
							"proof_state": "insufficient_governed_delivery_evidence",
							"submitted_delivery_notes": [],
						}
					]
				},
			},
			grounded_turn={"source_name": "ACC-SINV-2026-00192 Detail"},
		)
		self.assertEqual(answer, "")
