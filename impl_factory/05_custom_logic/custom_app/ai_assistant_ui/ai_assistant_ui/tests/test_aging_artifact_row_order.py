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

from ai_assistant_ui.qwen_chat.family_adapters import _aging_sections


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


if __name__ == "__main__":
	unittest.main()
