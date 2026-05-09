import unittest
import sys
import types


fake_frappe = types.SimpleNamespace(
	get_all=lambda *args, **kwargs: [],
	get_doc=lambda *args, **kwargs: None,
	db=types.SimpleNamespace(
		exists=lambda *args, **kwargs: False,
		get_value=lambda *args, **kwargs: None,
		sql=lambda *args, **kwargs: [],
	),
	conf={},
	local=types.SimpleNamespace(site=""),
)
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat.family_adapters import _aging_sections, _build_aging_artifact
from ai_assistant_ui.qwen_chat.family_rendering import _aging_blocks, render_normalized_family_response


class AgingArtifactRowOrderTests(unittest.TestCase):
	def test_party_rows_follow_display_order_by_outstanding_amount(self):
		sections = _aging_sections(
			[
				{"party": "Aung Aung Telecom", "party_type": "Customer", "outstanding": 24260000, "total_due": 20000000},
				{"party": "Capital Telecom (NPT)", "party_type": "Customer", "outstanding": 97309500, "total_due": 63654500},
				{"party": "35th Street Mobile Wholesale", "party_type": "Customer", "outstanding": 84837000, "total_due": 82527000},
			],
			aging_type="receivable",
			currency="MMK",
		)

		self.assertEqual(
			[row["party"] for row in sections["parties"][:3]],
			[
				"Capital Telecom (NPT)",
				"35th Street Mobile Wholesale",
				"Aung Aung Telecom",
			],
		)

	def test_aging_renderer_honors_requested_top_n_display_scope(self):
		artifact = types.SimpleNamespace(
			dimensions={
				"aging_type": "accounts_payable",
				"currency": "MMK",
				"party_dimension_label": "Supplier",
				"requested_top_n": 5,
			},
			sections={
				"summary": [],
				"bucket_totals": [],
				"parties": [
					{"party": f"Supplier {index}", "outstanding": 1000000 - index, "total_due": 900000 - index}
					for index in range(1, 8)
				],
			},
			period={},
		)

		_title, blocks = _aging_blocks(artifact)
		top_supplier_block = blocks[-1]

		self.assertEqual(top_supplier_block["title"], "Top 5 Suppliers")
		self.assertEqual(len(top_supplier_block["rows"]), 5)
		self.assertEqual(top_supplier_block["rows"][0][0], "Supplier 1")
		self.assertNotIn("Supplier 6", [row[0] for row in top_supplier_block["rows"]])

	def test_aging_adapter_carries_requested_top_n_into_renderer(self):
		rows = [
			{
				"party": f"Supplier {index}",
				"party_type": "Supplier",
				"currency": "MMK",
				"outstanding": 1000000 - index,
				"total_due": 900000 - index,
			}
			for index in range(1, 8)
		]
		adapted = _build_aging_artifact(
			request_id="test-aging-limit",
			report_name="Accounts Payable Aging",
			report_tool={"output_obj": {"result": {"data": rows}}},
			compiler_contract={"target_limit": 5},
		)

		self.assertEqual(adapted.status, "adapted")
		self.assertEqual(adapted.artifact_contract.dimensions.get("requested_top_n"), 5)

		rendered = render_normalized_family_response(
			request_id="test-aging-limit",
			artifact_contract=adapted.artifact_contract,
		)

		self.assertEqual(rendered.status, "rendered")
		answer_text = rendered.contract.answer_text
		self.assertIn("Top 5 Suppliers", answer_text)
		self.assertIn("Supplier 5", answer_text)
		self.assertNotIn("Supplier 6", answer_text)


if __name__ == "__main__":
	unittest.main()
