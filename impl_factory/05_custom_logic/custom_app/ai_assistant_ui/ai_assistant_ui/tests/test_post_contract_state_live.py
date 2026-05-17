import unittest
from typing import Any, Dict

from ai_assistant_ui.qwen_chat.service import (
	run_h3_clarification_resolution_does_not_resurrect_stale_recovery_smoke,
	run_h3_active_sequence_override_clears_prior_sequence_smoke,
	run_h3_targeted_restore_recovers_historical_branch_over_active_sequence_smoke,
	run_h3_discard_prefixed_targeted_restore_recovers_historical_branch_over_active_sequence_smoke,
	run_h3_targeted_restore_replays_resumable_prior_recovery_smoke,
	run_h3_discard_prefixed_targeted_restore_replays_resumable_prior_recovery_smoke,
	run_h3_targeted_restore_replays_resumable_prior_recovery_over_active_sequence_smoke,
	run_h3_discard_prefixed_targeted_restore_replays_resumable_prior_recovery_over_active_sequence_smoke,
	run_h3_question_restore_resumes_active_sequence_smoke,
	run_h3_branch_restore_prefers_newer_focus_smoke,
	run_h3_discard_prefixed_branch_restore_prefers_newer_focus_smoke,
	run_h3_branch_restore_reopens_pending_clarification_smoke,
	run_h3_question_restore_reopens_pending_clarification_smoke,
	run_h3_branch_restore_prefers_recent_focus_over_historical_prior_focus_smoke,
	run_h3_discard_prefixed_branch_restore_prefers_recent_focus_over_historical_prior_focus_smoke,
	run_h3_discard_prefixed_question_restore_resumes_active_sequence_smoke,
	run_h3_pronoun_discard_question_restore_resumes_active_sequence_smoke,
	run_h3_clarification_preempts_recovery_smoke,
	run_h3_duplicate_acceptance_after_newer_recovery_execution_smoke,
	run_h3_discard_prefixed_question_restore_smoke,
	run_h3_discard_prefixed_targeted_restore_smoke,
	run_h3_discard_prefixed_targeted_restore_prefers_purchase_order_listing_over_newer_detail_smoke,
	run_h3_discard_prefixed_targeted_restore_prefers_item_collection_over_newer_detail_smoke,
	run_h3_discard_prefixed_targeted_restore_recovers_sales_invoice_listing_over_newer_purchase_order_listing_smoke,
	run_h3_discard_prefixed_targeted_restore_prefers_sales_invoice_listing_over_newer_detail_smoke,
	run_h3_pronoun_discard_targeted_restore_over_active_sequence_smoke,
	run_h3_exact_item_focus_stock_followup_smoke,
	run_h3_ambiguous_item_list_to_stock_followup_smoke,
	run_h3_option_list_that_you_found_to_stock_followup_smoke,
	run_h3_seeded_transaction_document_followup_smoke,
	run_h3_financial_statement_switch_followup_smoke,
	run_h3_master_data_single_row_detail_followup_smoke,
	run_h3_duplicate_recovery_acceptance_smoke,
	run_h3_fresh_query_replaces_grounded_context_smoke,
	run_h3_latest_fresh_grounded_query_wins_smoke,
	run_h3_latest_seeded_recovery_wins_smoke,
	run_h3_master_data_pending_override_switches_focus_smoke,
	run_h3_option_list_then_override_switches_focus_smoke,
	run_h3_pending_discard_redirects_to_fresh_supplier_focus_smoke,
	run_h3_soft_chained_pending_redirect_to_fresh_supplier_focus_smoke,
	run_h3_pending_discard_redirects_to_balance_sheet_smoke,
	run_h3_targeted_restore_prefers_customer_collection_over_newer_detail_smoke,
	run_h3_targeted_restore_prefers_item_collection_over_newer_detail_smoke,
	run_h3_targeted_restore_prefers_purchase_order_listing_over_newer_detail_smoke,
	run_h3_targeted_restore_recovers_sales_invoice_listing_over_newer_purchase_order_listing_smoke,
	run_h3_targeted_restore_prefers_sales_invoice_listing_over_newer_detail_smoke,
	run_h3_question_restore_prefers_newer_focus_smoke,
	run_h3_targeted_restore_prefers_collection_branch_over_newer_detail_smoke,
	run_h3_targeted_restore_prefers_named_branch_smoke,
	run_h3_newer_recovery_survives_older_consumed_recovery_smoke,
	run_h3_pending_override_replaces_with_new_grounded_context_smoke,
	run_h3_post_stop_clarification_repeat_smoke,
	run_h3_repeated_identical_composite_grounded_query_replaces_grounding_smoke,
	run_h3_repeated_identical_fresh_query_replaces_grounding_smoke,
	run_h3_stale_recovery_invalidated_by_fresh_override_smoke,
	run_phase_d2a_transaction_listing_today_requery_smoke,
)


class TestPostContractStateLive(unittest.TestCase):
	def _assert_ok_tree(self, payload: Dict[str, Any], path: str) -> None:
		self.assertIsInstance(payload, dict, f"{path} must return a dict payload.")
		self.assertTrue(bool(payload.get("ok")), f"{path} did not report ok=True: {payload!r}")
		for key, value in payload.items():
			if key == "ok":
				continue
			if isinstance(value, dict) and "ok" in value:
				self._assert_ok_tree(value, f"{path}.{key}")

	def test_question_restore_resumes_active_sequence_smoke(self):
		self._assert_ok_tree(
			run_h3_question_restore_resumes_active_sequence_smoke(),
			"h3_question_restore_resumes_active_sequence",
		)

	def test_branch_restore_prefers_newer_focus_smoke(self):
		self._assert_ok_tree(
			run_h3_branch_restore_prefers_newer_focus_smoke(),
			"h3_branch_restore_prefers_newer_focus",
		)

	def test_discard_prefixed_branch_restore_prefers_newer_focus_smoke(self):
		self._assert_ok_tree(
			run_h3_discard_prefixed_branch_restore_prefers_newer_focus_smoke(),
			"h3_discard_prefixed_branch_restore_prefers_newer_focus",
		)

	def test_branch_restore_reopens_pending_clarification_smoke(self):
		self._assert_ok_tree(
			run_h3_branch_restore_reopens_pending_clarification_smoke(),
			"h3_branch_restore_reopens_pending_clarification",
		)

	def test_question_restore_reopens_pending_clarification_smoke(self):
		self._assert_ok_tree(
			run_h3_question_restore_reopens_pending_clarification_smoke(),
			"h3_question_restore_reopens_pending_clarification",
		)

	def test_branch_restore_prefers_recent_focus_over_historical_prior_focus_smoke(self):
		self._assert_ok_tree(
			run_h3_branch_restore_prefers_recent_focus_over_historical_prior_focus_smoke(),
			"h3_branch_restore_prefers_recent_focus_over_historical_prior_focus",
		)

	def test_discard_prefixed_branch_restore_prefers_recent_focus_over_historical_prior_focus_smoke(self):
		self._assert_ok_tree(
			run_h3_discard_prefixed_branch_restore_prefers_recent_focus_over_historical_prior_focus_smoke(),
			"h3_discard_prefixed_branch_restore_prefers_recent_focus_over_historical_prior_focus",
		)

	def test_discard_prefixed_question_restore_resumes_active_sequence_smoke(self):
		self._assert_ok_tree(
			run_h3_discard_prefixed_question_restore_resumes_active_sequence_smoke(),
			"h3_discard_prefixed_question_restore_resumes_active_sequence",
		)

	def test_pronoun_discard_question_restore_resumes_active_sequence_smoke(self):
		self._assert_ok_tree(
			run_h3_pronoun_discard_question_restore_resumes_active_sequence_smoke(),
			"h3_pronoun_discard_question_restore_resumes_active_sequence",
		)

	def test_discard_prefixed_question_restore_smoke(self):
		self._assert_ok_tree(
			run_h3_discard_prefixed_question_restore_smoke(),
			"h3_discard_prefixed_question_restore",
		)

	def test_active_sequence_override_clears_prior_sequence_smoke(self):
		self._assert_ok_tree(
			run_h3_active_sequence_override_clears_prior_sequence_smoke(),
			"h3_active_sequence_override_clears_prior_sequence",
		)

	def test_targeted_restore_recovers_historical_branch_over_active_sequence_smoke(self):
		self._assert_ok_tree(
			run_h3_targeted_restore_recovers_historical_branch_over_active_sequence_smoke(),
			"h3_targeted_restore_recovers_historical_branch_over_active_sequence",
		)

	def test_discard_prefixed_targeted_restore_recovers_historical_branch_over_active_sequence_smoke(self):
		self._assert_ok_tree(
			run_h3_discard_prefixed_targeted_restore_recovers_historical_branch_over_active_sequence_smoke(),
			"h3_discard_prefixed_targeted_restore_recovers_historical_branch_over_active_sequence",
		)

	def test_pronoun_discard_targeted_restore_over_active_sequence_smoke(self):
		self._assert_ok_tree(
			run_h3_pronoun_discard_targeted_restore_over_active_sequence_smoke(),
			"h3_pronoun_discard_targeted_restore_over_active_sequence",
		)

	def test_targeted_restore_replays_resumable_prior_recovery_smoke(self):
		self._assert_ok_tree(
			run_h3_targeted_restore_replays_resumable_prior_recovery_smoke(),
			"h3_targeted_restore_replays_resumable_prior_recovery",
		)

	def test_discard_prefixed_targeted_restore_replays_resumable_prior_recovery_smoke(self):
		self._assert_ok_tree(
			run_h3_discard_prefixed_targeted_restore_replays_resumable_prior_recovery_smoke(),
			"h3_discard_prefixed_targeted_restore_replays_resumable_prior_recovery",
		)

	def test_targeted_restore_replays_resumable_prior_recovery_over_active_sequence_smoke(self):
		self._assert_ok_tree(
			run_h3_targeted_restore_replays_resumable_prior_recovery_over_active_sequence_smoke(),
			"h3_targeted_restore_replays_resumable_prior_recovery_over_active_sequence",
		)

	def test_discard_prefixed_targeted_restore_replays_resumable_prior_recovery_over_active_sequence_smoke(self):
		self._assert_ok_tree(
			run_h3_discard_prefixed_targeted_restore_replays_resumable_prior_recovery_over_active_sequence_smoke(),
			"h3_discard_prefixed_targeted_restore_replays_resumable_prior_recovery_over_active_sequence",
		)

	def test_soft_chained_pending_redirect_to_fresh_supplier_focus_smoke(self):
		self._assert_ok_tree(
			run_h3_soft_chained_pending_redirect_to_fresh_supplier_focus_smoke(),
			"h3_soft_chained_pending_redirect_to_fresh_supplier_focus",
		)

	def test_option_list_that_you_found_to_stock_followup_smoke(self):
		self._assert_ok_tree(
			run_h3_option_list_that_you_found_to_stock_followup_smoke(),
			"h3_option_list_that_you_found_to_stock_followup",
		)

	def test_discard_prefixed_targeted_restore_smoke(self):
		self._assert_ok_tree(
			run_h3_discard_prefixed_targeted_restore_smoke(),
			"h3_discard_prefixed_targeted_restore",
		)

	def test_discard_prefixed_targeted_restore_prefers_sales_invoice_listing_over_newer_detail_smoke(self):
		self._assert_ok_tree(
			run_h3_discard_prefixed_targeted_restore_prefers_sales_invoice_listing_over_newer_detail_smoke(),
			"h3_discard_prefixed_targeted_restore_prefers_sales_invoice_listing_over_newer_detail",
		)

	def test_discard_prefixed_targeted_restore_prefers_purchase_order_listing_over_newer_detail_smoke(self):
		self._assert_ok_tree(
			run_h3_discard_prefixed_targeted_restore_prefers_purchase_order_listing_over_newer_detail_smoke(),
			"h3_discard_prefixed_targeted_restore_prefers_purchase_order_listing_over_newer_detail",
		)

	def test_discard_prefixed_targeted_restore_recovers_sales_invoice_listing_over_newer_purchase_order_listing_smoke(self):
		self._assert_ok_tree(
			run_h3_discard_prefixed_targeted_restore_recovers_sales_invoice_listing_over_newer_purchase_order_listing_smoke(),
			"h3_discard_prefixed_targeted_restore_recovers_sales_invoice_listing_over_newer_purchase_order_listing",
		)

	def test_targeted_restore_prefers_item_collection_over_newer_detail_smoke(self):
		self._assert_ok_tree(
			run_h3_targeted_restore_prefers_item_collection_over_newer_detail_smoke(),
			"h3_targeted_restore_prefers_item_collection_over_newer_detail",
		)

	def test_discard_prefixed_targeted_restore_prefers_item_collection_over_newer_detail_smoke(self):
		self._assert_ok_tree(
			run_h3_discard_prefixed_targeted_restore_prefers_item_collection_over_newer_detail_smoke(),
			"h3_discard_prefixed_targeted_restore_prefers_item_collection_over_newer_detail",
		)

	def test_duplicate_recovery_acceptance_smoke(self):
		self._assert_ok_tree(
			run_h3_duplicate_recovery_acceptance_smoke(),
			"h3_duplicate_recovery_acceptance",
		)

	def test_duplicate_acceptance_after_newer_recovery_execution_smoke(self):
		self._assert_ok_tree(
			run_h3_duplicate_acceptance_after_newer_recovery_execution_smoke(),
			"h3_duplicate_acceptance_after_newer_recovery_execution",
		)

	def test_post_stop_clarification_repeat_smoke(self):
		self._assert_ok_tree(
			run_h3_post_stop_clarification_repeat_smoke(),
			"h3_post_stop_clarification_repeat",
		)

	def test_clarification_preempts_recovery_smoke(self):
		self._assert_ok_tree(
			run_h3_clarification_preempts_recovery_smoke(),
			"h3_clarification_preempts_recovery",
		)

	def test_clarification_resolution_does_not_resurrect_stale_recovery_smoke(self):
		self._assert_ok_tree(
			run_h3_clarification_resolution_does_not_resurrect_stale_recovery_smoke(),
			"h3_clarification_resolution_does_not_resurrect_stale_recovery",
		)

	def test_fresh_query_replaces_grounded_context_smoke(self):
		self._assert_ok_tree(
			run_h3_fresh_query_replaces_grounded_context_smoke(),
			"h3_fresh_query_replaces_grounded_context",
		)

	def test_pending_override_replaces_with_new_grounded_context_smoke(self):
		self._assert_ok_tree(
			run_h3_pending_override_replaces_with_new_grounded_context_smoke(),
			"h3_pending_override_replaces_with_new_grounded_context",
		)

	def test_master_data_pending_override_switches_focus_smoke(self):
		self._assert_ok_tree(
			run_h3_master_data_pending_override_switches_focus_smoke(),
			"h3_master_data_pending_override_switches_focus",
		)

	def test_option_list_then_override_switches_focus_smoke(self):
		self._assert_ok_tree(
			run_h3_option_list_then_override_switches_focus_smoke(),
			"h3_option_list_then_override_switches_focus",
		)

	def test_question_restore_prefers_newer_focus_smoke(self):
		self._assert_ok_tree(
			run_h3_question_restore_prefers_newer_focus_smoke(),
			"h3_question_restore_prefers_newer_focus",
		)

	def test_targeted_restore_prefers_named_branch_smoke(self):
		self._assert_ok_tree(
			run_h3_targeted_restore_prefers_named_branch_smoke(),
			"h3_targeted_restore_prefers_named_branch",
		)

	def test_targeted_restore_prefers_collection_branch_over_newer_detail_smoke(self):
		self._assert_ok_tree(
			run_h3_targeted_restore_prefers_collection_branch_over_newer_detail_smoke(),
			"h3_targeted_restore_prefers_collection_branch_over_newer_detail",
		)

	def test_targeted_restore_prefers_customer_collection_over_newer_detail_smoke(self):
		self._assert_ok_tree(
			run_h3_targeted_restore_prefers_customer_collection_over_newer_detail_smoke(),
			"h3_targeted_restore_prefers_customer_collection_over_newer_detail",
		)

	def test_targeted_restore_prefers_purchase_order_listing_over_newer_detail_smoke(self):
		self._assert_ok_tree(
			run_h3_targeted_restore_prefers_purchase_order_listing_over_newer_detail_smoke(),
			"h3_targeted_restore_prefers_purchase_order_listing_over_newer_detail",
		)

	def test_targeted_restore_recovers_sales_invoice_listing_over_newer_purchase_order_listing_smoke(self):
		self._assert_ok_tree(
			run_h3_targeted_restore_recovers_sales_invoice_listing_over_newer_purchase_order_listing_smoke(),
			"h3_targeted_restore_recovers_sales_invoice_listing_over_newer_purchase_order_listing",
		)

	def test_targeted_restore_prefers_sales_invoice_listing_over_newer_detail_smoke(self):
		self._assert_ok_tree(
			run_h3_targeted_restore_prefers_sales_invoice_listing_over_newer_detail_smoke(),
			"h3_targeted_restore_prefers_sales_invoice_listing_over_newer_detail",
		)

	def test_pending_discard_redirects_to_fresh_supplier_focus_smoke(self):
		self._assert_ok_tree(
			run_h3_pending_discard_redirects_to_fresh_supplier_focus_smoke(),
			"h3_pending_discard_redirects_to_fresh_supplier_focus",
		)

	def test_pending_discard_redirects_to_balance_sheet_smoke(self):
		self._assert_ok_tree(
			run_h3_pending_discard_redirects_to_balance_sheet_smoke(),
			"h3_pending_discard_redirects_to_balance_sheet",
		)

	def test_exact_item_focus_stock_followup_smoke(self):
		self._assert_ok_tree(
			run_h3_exact_item_focus_stock_followup_smoke(),
			"h3_exact_item_focus_stock_followup",
		)

	def test_ambiguous_item_list_to_stock_followup_smoke(self):
		self._assert_ok_tree(
			run_h3_ambiguous_item_list_to_stock_followup_smoke(),
			"h3_ambiguous_item_list_to_stock_followup",
		)

	def test_seeded_transaction_document_followup_smoke(self):
		self._assert_ok_tree(
			run_h3_seeded_transaction_document_followup_smoke(),
			"h3_seeded_transaction_document_followup",
		)

	def test_financial_statement_switch_followup_smoke(self):
		self._assert_ok_tree(
			run_h3_financial_statement_switch_followup_smoke(),
			"h3_financial_statement_switch_followup",
		)

	def test_master_data_single_row_detail_followup_smoke(self):
		self._assert_ok_tree(
			run_h3_master_data_single_row_detail_followup_smoke(),
			"h3_master_data_single_row_detail_followup",
		)

	def test_latest_fresh_grounded_query_wins_smoke(self):
		self._assert_ok_tree(
			run_h3_latest_fresh_grounded_query_wins_smoke(),
			"h3_latest_fresh_grounded_query_wins",
		)

	def test_latest_seeded_recovery_wins_smoke(self):
		self._assert_ok_tree(
			run_h3_latest_seeded_recovery_wins_smoke(),
			"h3_latest_seeded_recovery_wins",
		)

	def test_newer_recovery_survives_older_consumed_recovery_smoke(self):
		self._assert_ok_tree(
			run_h3_newer_recovery_survives_older_consumed_recovery_smoke(),
			"h3_newer_recovery_survives_older_consumed_recovery",
		)

	def test_repeated_identical_fresh_query_replaces_grounding_smoke(self):
		self._assert_ok_tree(
			run_h3_repeated_identical_fresh_query_replaces_grounding_smoke(),
			"h3_repeated_identical_fresh_query_replaces_grounding",
		)

	def test_repeated_identical_composite_grounded_query_replaces_grounding_smoke(self):
		self._assert_ok_tree(
			run_h3_repeated_identical_composite_grounded_query_replaces_grounding_smoke(),
			"h3_repeated_identical_composite_grounded_query_replaces_grounding",
		)

	def test_stale_recovery_invalidated_by_fresh_override_smoke(self):
		self._assert_ok_tree(
			run_h3_stale_recovery_invalidated_by_fresh_override_smoke(),
			"h3_stale_recovery_invalidated_by_fresh_override",
		)

	def test_phase_d2a_transaction_listing_today_requery_smoke(self):
		self._assert_ok_tree(
			run_phase_d2a_transaction_listing_today_requery_smoke(),
			"phase_d2a_transaction_listing_today_requery",
		)
