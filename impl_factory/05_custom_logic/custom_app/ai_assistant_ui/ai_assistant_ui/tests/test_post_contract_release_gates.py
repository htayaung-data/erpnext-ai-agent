import unittest
from typing import Any, Dict

from ai_assistant_ui.qwen_chat.service import (
	run_h5_release_gate_rollout_probe,
	run_h5_release_gate_sanity_pack,
	run_phase1_1_delivery_note_last_year_trend_smoke,
	run_phase1_1_delivery_note_date_scope_smoke,
	run_phase1_1_delivery_note_detail_smoke,
	run_phase1_1_delivery_note_listing_smoke,
	run_phase1_1_delivery_note_session_reset_smoke,
	run_phase1_1_delivery_note_status_smoke,
	run_phase1_1_delivery_note_trend_smoke,
	run_phase1_1_fresh_chat_invoice_delivery_proof_smoke,
	run_phase1_1_invoice_delivery_proof_smoke,
	run_phase1_1_invoice_detail_delivery_trend_smoke,
	run_phase1_2_sales_order_detail_smoke,
	run_phase1_2_sales_order_status_followup_smoke,
	run_phase1_3_purchase_order_detail_smoke,
	run_phase1_3_purchase_order_status_followup_smoke,
	run_phase1_4_customer_credit_balance_smoke,
	run_phase1_4_customer_credit_detail_followup_smoke,
	run_phase1_4_customer_credit_exposure_smoke,
	run_phase1_4_customer_credit_overdue_smoke,
	run_phase1_4_customer_credit_policy_followup_smoke,
	run_phase1_4_customer_credit_scope_reset_smoke,
	run_phase2_4_governed_kpi_frontdoor_smoke,
	run_phase2_5_governed_kpi_customer_execution_smoke,
	run_phase2_5_governed_kpi_period_execution_smoke,
)


class TestPostContractReleaseGates(unittest.TestCase):
	def _assert_ok_tree(self, payload: Dict[str, Any], path: str) -> None:
		self.assertIsInstance(payload, dict, f"{path} must return a dict payload.")
		self.assertTrue(bool(payload.get("ok")), f"{path} did not report ok=True: {payload!r}")
		for key, value in payload.items():
			if key == "ok":
				continue
			if isinstance(value, dict) and "ok" in value:
				self._assert_ok_tree(value, f"{path}.{key}")

	def test_h5_release_gate_rollout_probe(self):
		self._assert_ok_tree(
			run_h5_release_gate_rollout_probe(),
			"h5_release_gate_rollout_probe",
		)

	def test_h5_release_gate_sanity_pack(self):
		self._assert_ok_tree(
			run_h5_release_gate_sanity_pack(),
			"h5_release_gate_sanity_pack",
		)

	def test_phase1_1a_delivery_note_listing_smoke(self):
		self._assert_ok_tree(
			run_phase1_1_delivery_note_listing_smoke(),
			"phase1_1_delivery_note_listing_smoke",
		)

	def test_phase1_1a_delivery_note_detail_smoke(self):
		self._assert_ok_tree(
			run_phase1_1_delivery_note_detail_smoke(),
			"phase1_1_delivery_note_detail_smoke",
		)

	def test_phase1_1b_delivery_note_date_scope_smoke(self):
		self._assert_ok_tree(
			run_phase1_1_delivery_note_date_scope_smoke(),
			"phase1_1_delivery_note_date_scope_smoke",
		)

	def test_phase1_1b_delivery_note_status_smoke(self):
		self._assert_ok_tree(
			run_phase1_1_delivery_note_status_smoke(),
			"phase1_1_delivery_note_status_smoke",
		)

	def test_phase1_1b_delivery_note_session_reset_smoke(self):
		self._assert_ok_tree(
			run_phase1_1_delivery_note_session_reset_smoke(),
			"phase1_1_delivery_note_session_reset_smoke",
		)

	def test_phase1_1c_delivery_note_trend_smoke(self):
		self._assert_ok_tree(
			run_phase1_1_delivery_note_trend_smoke(),
			"phase1_1_delivery_note_trend_smoke",
		)

	def test_phase1_1c_delivery_note_last_year_trend_smoke(self):
		self._assert_ok_tree(
			run_phase1_1_delivery_note_last_year_trend_smoke(),
			"phase1_1_delivery_note_last_year_trend_smoke",
		)

	def test_phase1_1c_invoice_detail_delivery_trend_smoke(self):
		self._assert_ok_tree(
			run_phase1_1_invoice_detail_delivery_trend_smoke(),
			"phase1_1_invoice_detail_delivery_trend_smoke",
		)

	def test_phase1_1d_invoice_delivery_proof_smoke(self):
		self._assert_ok_tree(
			run_phase1_1_invoice_delivery_proof_smoke(),
			"phase1_1_invoice_delivery_proof_smoke",
		)

	def test_phase1_1d_fresh_chat_invoice_delivery_proof_smoke(self):
		self._assert_ok_tree(
			run_phase1_1_fresh_chat_invoice_delivery_proof_smoke(),
			"phase1_1_fresh_chat_invoice_delivery_proof_smoke",
		)

	def test_phase1_2c_sales_order_detail_smoke(self):
		self._assert_ok_tree(
			run_phase1_2_sales_order_detail_smoke(),
			"phase1_2_sales_order_detail_smoke",
		)

	def test_phase1_2d_sales_order_status_followup_smoke(self):
		self._assert_ok_tree(
			run_phase1_2_sales_order_status_followup_smoke(),
			"phase1_2_sales_order_status_followup_smoke",
		)

	def test_phase1_3c_purchase_order_detail_smoke(self):
		self._assert_ok_tree(
			run_phase1_3_purchase_order_detail_smoke(),
			"phase1_3_purchase_order_detail_smoke",
		)

	def test_phase1_3d_purchase_order_status_followup_smoke(self):
		self._assert_ok_tree(
			run_phase1_3_purchase_order_status_followup_smoke(),
			"phase1_3_purchase_order_status_followup_smoke",
		)

	def test_phase1_4a_customer_credit_exposure_smoke(self):
		self._assert_ok_tree(
			run_phase1_4_customer_credit_exposure_smoke(),
			"phase1_4_customer_credit_exposure_smoke",
		)

	def test_phase1_4b_customer_credit_overdue_smoke(self):
		self._assert_ok_tree(
			run_phase1_4_customer_credit_overdue_smoke(),
			"phase1_4_customer_credit_overdue_smoke",
		)

	def test_phase1_4b_customer_credit_balance_smoke(self):
		self._assert_ok_tree(
			run_phase1_4_customer_credit_balance_smoke(),
			"phase1_4_customer_credit_balance_smoke",
		)

	def test_phase1_4b_customer_credit_scope_reset_smoke(self):
		self._assert_ok_tree(
			run_phase1_4_customer_credit_scope_reset_smoke(),
			"phase1_4_customer_credit_scope_reset_smoke",
		)

	def test_phase1_4d_customer_credit_detail_followup_smoke(self):
		self._assert_ok_tree(
			run_phase1_4_customer_credit_detail_followup_smoke(),
			"phase1_4_customer_credit_detail_followup_smoke",
		)

	def test_phase1_4e_customer_credit_policy_followup_smoke(self):
		self._assert_ok_tree(
			run_phase1_4_customer_credit_policy_followup_smoke(),
			"phase1_4_customer_credit_policy_followup_smoke",
		)

	def test_phase2_4_governed_kpi_frontdoor_smoke(self):
		self._assert_ok_tree(
			run_phase2_4_governed_kpi_frontdoor_smoke(),
			"phase2_4_governed_kpi_frontdoor_smoke",
		)

	def test_phase2_5_governed_kpi_period_execution_smoke(self):
		self._assert_ok_tree(
			run_phase2_5_governed_kpi_period_execution_smoke(),
			"phase2_5_governed_kpi_period_execution_smoke",
		)

	def test_phase2_5_governed_kpi_customer_execution_smoke(self):
		self._assert_ok_tree(
			run_phase2_5_governed_kpi_customer_execution_smoke(),
			"phase2_5_governed_kpi_customer_execution_smoke",
		)
