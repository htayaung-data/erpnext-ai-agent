import unittest

from ai_assistant_ui.qwen_chat.restore_support import (
	pending_clarification_is_non_authoritative_fallback,
	pending_clarification_is_restore_authoritative,
	recent_focus_matches_targeted_restore,
	resumable_prior_request_matches_targeted_restore,
	state_precedes_pending_clarification,
	targeted_restore_focus_kind_matches,
)


class TestRestoreSupportContracts(unittest.TestCase):
	def test_targeted_restore_focus_kind_matches_statement_and_report(self):
		self.assertTrue(
			targeted_restore_focus_kind_matches(
				candidate_focus_kind="report",
				target_focus_kind="statement",
			)
		)
		self.assertTrue(
			targeted_restore_focus_kind_matches(
				candidate_focus_kind="statement",
				target_focus_kind="report",
			)
		)
		self.assertFalse(
			targeted_restore_focus_kind_matches(
				candidate_focus_kind="listing",
				target_focus_kind="statement",
			)
		)

	def test_recent_focus_matches_targeted_restore_by_grain_and_hint(self):
		recent_focus = {
			"available": True,
			"focus_kind": "listing",
			"focus_grain": "supplier",
			"focus_label": "Suppliers as of 2026-04-17",
			"source_report": "Supplier Master List",
		}
		self.assertTrue(
			recent_focus_matches_targeted_restore(
				recent_focus,
				target_hint="suppliers",
				target_grain="supplier",
				target_focus_kind="listing",
			)
		)
		self.assertFalse(
			recent_focus_matches_targeted_restore(
				recent_focus,
				target_hint="balance sheet",
				target_grain="balance_sheet",
				target_focus_kind="statement",
			)
		)

	def test_resumable_prior_request_matches_targeted_restore_from_scope_surface(self):
		resumable_prior_request = {
			"available": True,
			"branch_label": "customer detail follow-up",
			"target_family": "entity_detail",
			"branch_kind": "entity",
			"target_scope": {
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_label": "Ko Nay Lin Mobile Center",
				"source_report": "Customer Master List",
				"source_capability": "master_data_detail",
			},
		}
		self.assertTrue(
			resumable_prior_request_matches_targeted_restore(
				resumable_prior_request,
				target_hint="ko nay lin",
				target_grain="customer",
				target_focus_kind="entity",
			)
		)
		self.assertFalse(
			resumable_prior_request_matches_targeted_restore(
				resumable_prior_request,
				target_hint="payment entries",
				target_grain="payment_entry",
				target_focus_kind="listing",
			)
		)

	def test_pending_clarification_precedence_helpers(self):
		pending_fallback = {
			"available": True,
			"source_kind": "message_fallback",
			"source_tool_index": -1,
		}
		recent_focus = {
			"available": True,
			"source_tool_index": 5,
		}
		self.assertTrue(pending_clarification_is_non_authoritative_fallback(pending_fallback))
		self.assertFalse(pending_clarification_is_restore_authoritative(pending_fallback))
		self.assertTrue(state_precedes_pending_clarification(recent_focus, pending_fallback))
		authoritative_pending = {
			"available": True,
			"source_kind": "stored_state",
			"source_tool_index": 8,
		}
		self.assertFalse(pending_clarification_is_non_authoritative_fallback(authoritative_pending))
		self.assertTrue(pending_clarification_is_restore_authoritative(authoritative_pending))
		self.assertFalse(state_precedes_pending_clarification(recent_focus, authoritative_pending))


if __name__ == "__main__":
	unittest.main()
