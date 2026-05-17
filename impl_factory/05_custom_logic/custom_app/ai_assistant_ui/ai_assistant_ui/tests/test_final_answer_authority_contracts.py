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
	ExecutionPath,
	build_audit_envelope,
	build_final_answer_authority_contract,
	build_followup_resolution_contract,
	build_interaction_contract,
)


class TestFinalAnswerAuthorityContracts(unittest.TestCase):
	def _interaction(self):
		return build_interaction_contract(
			request_id="req-s7-3",
			session_id="session-s7-3",
			user_id="user@example.com",
			site_name="erpai_prj1",
			raw_message="Who is second in the above table?",
		)

	def _followup(self, mode="visible_context_answer"):
		return build_followup_resolution_contract(
			request_id="req-s7-3",
			mode=mode,
			requested_modes=[mode],
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="test",
		)

	def test_audit_envelope_embeds_visible_context_final_answer_authority(self):
		trace = {
			"type": "qwen_visible_context_followup_trace_contract",
			"semantic_ownership_ledger": {
				"type": "qwen_semantic_ownership_ledger_contract",
				"resolved_context": {
					"artifact_id": "visible-assistant-2",
					"report_family": "accounts_receivable_aging",
					"entity_type": "customer",
					"row_reference": "rank_2",
				},
				"authority": {
					"authority_source": "visible_rendered_table",
					"evidence_scope": "visible_rendered_table",
					"policy_boundary": "none",
					"answer_mode": "visible_context_answer",
				},
				"decision_owners": {
					"renderer": "visible_context_followup_renderer",
				},
			},
		}
		audit_payload = build_audit_envelope(
			interaction_contract=self._interaction(),
			followup_resolution=self._followup(),
			execution_path=ExecutionPath(
				request_id="req-s7-3",
				path="visible_context_answer",
				reason="test",
				requires_runtime=False,
				grounded_required=False,
			),
			runtime_trace_payload={
				"agent_meta": {"engine": "visible_context_followup"},
				"visible_context_trace": trace,
			},
			grounded_turn_context={},
			answer_text="Rank 2 is Bayint Naung Wholesale Mobile.",
			authority_context={"visible_context_trace": trace},
		).to_payload()

		authority = audit_payload.get("final_answer_authority", {})
		self.assertEqual(authority.get("type"), "qwen_final_answer_authority_contract")
		self.assertEqual(authority.get("authority_source"), "visible_rendered_table")
		self.assertEqual(authority.get("evidence_scope"), "visible_rendered_table")
		self.assertEqual(authority.get("selected_artifact_id"), "visible-assistant-2")
		self.assertEqual(authority.get("selected_report_family"), "accounts_receivable_aging")
		self.assertEqual(authority.get("selected_row_reference"), "rank_2")
		self.assertEqual(authority.get("renderer_owner"), "visible_context_followup_renderer")
		self.assertEqual(authority.get("preflight_status"), "passed")
		self.assertTrue(authority.get("authority_complete"))

	def test_grounded_report_answer_authority_uses_governed_erp_report_context(self):
		authority = build_final_answer_authority_contract(
			interaction_contract=self._interaction(),
			followup_resolution=self._followup(mode="compiled_first_turn"),
			execution_path=ExecutionPath(
				request_id="req-s7-3",
				path="compiled_first_turn",
				reason="test",
				requires_runtime=True,
				grounded_required=True,
			),
			runtime_trace_payload={"agent_meta": {"engine": "qwen"}, "tool_trace": []},
			grounded_turn_context={
				"type": "qwen_grounded_turn_context",
				"grounded": True,
				"source_kind": "report",
				"source_name": "Accounts Receivable Aging",
				"artifact_family_id": "aging",
				"trace_request_id": "runtime-req-1",
			},
			answer_text="Accounts Receivable Aging as of 2026-05-12.",
			authority_context={
				"normalized_family_artifact": {
					"type": "qwen_normalized_family_artifact_contract",
					"request_id": "artifact-req-1",
					"family_id": "aging",
				}
			},
		).to_payload()

		self.assertEqual(authority.get("authority_source"), "governed_erp_report")
		self.assertEqual(authority.get("evidence_scope"), "grounded_turn_context")
		self.assertEqual(authority.get("selected_artifact_id"), "artifact-req-1")
		self.assertEqual(authority.get("selected_report_family"), "aging")
		self.assertEqual(authority.get("preflight_status"), "passed")
		self.assertTrue(authority.get("authority_complete"))

	def test_policy_boundary_answer_authority_is_bounded_not_uncontrolled(self):
		authority = build_final_answer_authority_contract(
			interaction_contract=self._interaction(),
			followup_resolution=self._followup(mode="reasoning_boundary"),
			execution_path=ExecutionPath(
				request_id="req-s7-3",
				path="reasoning_boundary",
				reason="test",
				requires_runtime=False,
				grounded_required=False,
			),
			runtime_trace_payload={},
			grounded_turn_context={},
			answer_text="I can show current evidence, but I cannot predict default without an approved model.",
			authority_context={
				"knowledge_boundary": {
					"type": "qwen_knowledge_boundary_contract",
					"final_lane": "valid_erp_domain_uncovered",
					"knowledge_coverage_state": "valid_erp_domain_uncovered",
					"user_response_mode": "coverage_gap_explanation",
					"allowed_to_answer": False,
				}
			},
		).to_payload()

		self.assertEqual(authority.get("authority_source"), "policy_boundary")
		self.assertEqual(authority.get("evidence_scope"), "qwen_knowledge_boundary_contract")
		self.assertEqual(authority.get("policy_boundary"), "valid_erp_domain_uncovered")
		self.assertEqual(authority.get("preflight_status"), "bounded")
		self.assertTrue(authority.get("authority_complete"))

	def test_missing_grounded_authority_is_explicitly_not_complete(self):
		authority = build_final_answer_authority_contract(
			interaction_contract=self._interaction(),
			followup_resolution=self._followup(mode="compiled_first_turn"),
			execution_path=ExecutionPath(
				request_id="req-s7-3",
				path="compiled_first_turn",
				reason="test",
				requires_runtime=True,
				grounded_required=True,
			),
			runtime_trace_payload={},
			grounded_turn_context={},
			answer_text="Unsupported answer.",
		).to_payload()

		self.assertEqual(authority.get("preflight_status"), "missing_authority")
		self.assertFalse(authority.get("authority_complete"))
		self.assertIn("authority_source", authority.get("missing_fields", []))
		self.assertIn("evidence_scope", authority.get("missing_fields", []))


if __name__ == "__main__":
	unittest.main()
