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

from ai_assistant_ui.qwen_chat.authorized_emission import (
	ANSWER_TYPE_CONTROL,
	ANSWER_TYPE_BUSINESS_FACTUAL,
	ANSWER_TYPE_GOVERNED_REPORT,
	ANSWER_TYPE_POLICY_BOUNDARY,
	ANSWER_TYPE_REASONING,
	ANSWER_TYPE_VISIBLE_CONTEXT,
	AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE,
	EMISSION_STATUS_BLOCKED,
	EMISSION_STATUS_EMITTED,
	USER_INTENT_FINAL_EMISSION_VETO_CONTRACT_TYPE,
	emit_authorized_assistant_answer,
)
from ai_assistant_ui.qwen_chat.contracts import (
	ExecutionPath,
	build_followup_resolution_contract,
	build_interaction_contract,
)
from ai_assistant_ui.qwen_chat.intent_boundary_contract import (
	ANSWER_MODE_GOVERNED_ERP,
	AUTHORITY_DECISION_ALLOW_REPORT,
	AUTHORITY_DECISION_BLOCK,
	TRACE_REDACTION_SAFE,
	hash_text,
	normalize_message,
)
from ai_assistant_ui.qwen_chat.intent_boundary_runtime_integration import USER_INTENT_BOUNDARY_CONTRACT_TYPE


class FakeSessionDoc:
	def __init__(self):
		self.messages = []


def _append_message(session_doc, role, content):
	session_doc.messages.append({"role": role, "content": content})


def _append_tool_payload(session_doc, payload):
	session_doc.messages.append({"role": "tool", "content": payload})


def _assistant_text_payload(text):
	return {"text": str(text or "")}


class AuthorizedEmissionContractTests(unittest.TestCase):
	def _interaction(self, raw_message="Who is second in the above table?"):
		return build_interaction_contract(
			request_id="req-ec4",
			session_id="session-ec4",
			user_id="user@example.com",
			site_name="erpai_prj1",
			raw_message=raw_message,
		)

	def _followup(self, mode="visible_context_answer", *, grounded=True):
		return build_followup_resolution_contract(
			request_id="req-ec4",
			mode=mode,
			requested_modes=[mode],
			depends_on_grounded_turn=grounded,
			self_contained=not grounded,
			latest_grounded_turn_available=grounded,
			reason="contract test",
		)

	def _execution_path(self, path="visible_context_answer", *, requires_runtime=False, grounded_required=False):
		return ExecutionPath(
			request_id="req-ec4",
			path=path,
			reason="contract test",
			requires_runtime=requires_runtime,
			grounded_required=grounded_required,
		)

	def _visible_trace(self):
		return {
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
				"decision_owners": {"renderer": "visible_context_followup_renderer"},
			},
		}

	def _governed_artifact_policy_boundary_trace(self):
		trace = self._visible_trace()
		ledger = trace["semantic_ownership_ledger"]
		ledger["resolved_context"] = {
			"artifact_id": "item-rows-1",
			"report_family": "item_stock_summary",
			"entity_type": "item",
			"row_reference": "rank_1",
		}
		ledger["authority"] = {
			"authority_source": "governed_artifact",
			"evidence_scope": "governed_artifact",
			"policy_boundary": "recommendation_boundary",
			"answer_mode": "visible_context_boundary",
		}
		return trace

	def _visible_context_resolution_boundary_trace(self):
		trace = self._visible_trace()
		ledger = trace["semantic_ownership_ledger"]
		ledger["resolved_context"] = {
			"artifact_id": "",
			"report_family": "",
			"entity_type": "",
			"row_reference": "none",
		}
		ledger["authority"] = {
			"authority_source": "visible_context_resolution",
			"evidence_scope": "visible_context_resolution",
			"policy_boundary": "visible_context_boundary",
			"answer_mode": "visible_context_boundary",
		}
		return trace

	def _policy_boundary(self):
		return {
			"type": "qwen_knowledge_boundary_contract",
			"final_lane": "valid_erp_domain_uncovered",
			"knowledge_coverage_state": "valid_erp_domain_uncovered",
			"user_response_mode": "coverage_gap_explanation",
			"allowed_to_answer": False,
		}

	def _grounded_turn(self):
		return {
			"type": "qwen_grounded_turn_context",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Accounts Receivable Aging",
			"artifact_family_id": "aging",
			"trace_request_id": "runtime-req-1",
		}

	def _normalized_artifact(self):
		return {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "artifact-req-1",
			"family_id": "aging",
		}

	def _control_authority(self):
		return {
			"authority_source": "control_meta",
			"answer_mode": "clarification",
			"reason": "The assistant is asking a clarification question, not emitting a business answer.",
			"preflight_status": "passed",
		}

	def _v1_ib_boundary(self, raw_message: str, *, allow_report=False, allow_context=False):
		normalized_message = normalize_message(raw_message)
		allowed = bool(allow_report or allow_context)
		return {
			"type": USER_INTENT_BOUNDARY_CONTRACT_TYPE,
			"contract_version": "test-v1-ib",
			"raw_message_hash": hash_text(raw_message),
			"normalized_message_hash": hash_text(normalized_message),
			"clause_count": 1,
			"category": "factual_erp_query" if allow_report else "true_visible_context_followup",
			"required_answer_mode": ANSWER_MODE_GOVERNED_ERP if allowed else "clarification",
			"context_reuse_allowed": bool(allow_context),
			"report_routing_allowed": bool(allow_report),
			"model_reasoning_allowed": bool(allow_report),
			"final_emission_allowed": allowed,
			"authority_decision": AUTHORITY_DECISION_ALLOW_REPORT if allowed else AUTHORITY_DECISION_BLOCK,
			"boundary_reason": "validated_safe_factual_intent" if allowed else "v1_ib_contract_blocked_runtime_authority",
			"validator_status": "valid" if allowed else "invalid",
			"trace_redaction_status": TRACE_REDACTION_SAFE,
			"replayed_raw_message_safety_final_decision": "safe" if allowed else "blocked",
		}

	def _assert_v1_veto_without_selected_answer_leak(self, session_doc, selected_text: str):
		serialized = str(session_doc.messages)
		self.assertNotIn(selected_text, serialized)
		self.assertIn(USER_INTENT_FINAL_EMISSION_VETO_CONTRACT_TYPE, serialized)

	def test_missing_business_authority_blocks_without_assistant_append(self):
		session_doc = FakeSessionDoc()
		selected_text = "Unsupported business answer."
		result = emit_authorized_assistant_answer(
			session_doc=session_doc,
			answer_text=selected_text,
			answer_type=ANSWER_TYPE_GOVERNED_REPORT,
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			assistant_text_payload=_assistant_text_payload,
			interaction_contract=self._interaction(),
			followup_resolution=self._followup(mode="compiled_first_turn", grounded=True),
			execution_path=self._execution_path(path="compiled_first_turn", requires_runtime=True, grounded_required=True),
		)

		self.assertFalse(result.blocked)
		self.assertTrue(result.emitted)
		self.assertEqual(result.answer_type, ANSWER_TYPE_CONTROL)
		self._assert_v1_veto_without_selected_answer_leak(session_doc, selected_text)

	def test_complete_visible_context_authority_allows_emission(self):
		session_doc = FakeSessionDoc()
		trace = self._visible_trace()
		result = emit_authorized_assistant_answer(
			session_doc=session_doc,
			answer_text="Rank 2 is Bayint Naung Wholesale Mobile.",
			answer_type=ANSWER_TYPE_VISIBLE_CONTEXT,
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			assistant_text_payload=_assistant_text_payload,
			interaction_contract=self._interaction(),
			followup_resolution=self._followup(),
			execution_path=self._execution_path(),
			runtime_trace_payload={"agent_meta": {"engine": "visible_context_followup"}, "visible_context_trace": trace},
			authority_context={
				"visible_context_trace": trace,
				"user_intent_boundary": self._v1_ib_boundary(
					"Who is second in the above table?",
					allow_context=True,
				),
			},
		)

		self.assertTrue(result.emitted)
		self.assertFalse(result.blocked)
		self.assertEqual(result.preflight_status, "passed")
		self.assertEqual([message["role"] for message in session_doc.messages], ["tool", "tool", "assistant"])
		self.assertEqual(session_doc.messages[0]["content"]["type"], "qwen_audit_envelope")
		self.assertEqual(session_doc.messages[1]["content"]["type"], AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE)
		self.assertEqual(session_doc.messages[2]["content"]["text"], "Rank 2 is Bayint Naung Wholesale Mobile.")

	def test_complete_governed_report_authority_allows_emission(self):
		session_doc = FakeSessionDoc()
		raw_message = "Show EC7H-ITEM-A item sales"
		result = emit_authorized_assistant_answer(
			session_doc=session_doc,
			answer_text="Accounts Receivable Aging as of 2026-05-12.",
			answer_type=ANSWER_TYPE_GOVERNED_REPORT,
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			assistant_text_payload=_assistant_text_payload,
			interaction_contract=self._interaction(raw_message),
			followup_resolution=self._followup(mode="compiled_first_turn", grounded=True),
			execution_path=self._execution_path(path="compiled_first_turn", requires_runtime=True, grounded_required=True),
			runtime_trace_payload={"agent_meta": {"engine": "qwen"}, "tool_trace": []},
			grounded_turn_context=self._grounded_turn(),
			authority_context={
				"normalized_family_artifact": self._normalized_artifact(),
				"user_intent_boundary": self._v1_ib_boundary(raw_message, allow_report=True),
			},
		)

		self.assertTrue(result.emitted)
		self.assertEqual(result.preflight_status, "passed")
		self.assertEqual(result.final_answer_authority["authority_source"], "governed_erp_report")
		self.assertEqual(result.final_answer_authority["selected_report_family"], "aging")

	def test_pre_assistant_tool_payloads_append_only_after_authority_passes(self):
		session_doc = FakeSessionDoc()
		raw_message = "Show EC7H-ITEM-A item sales"
		result = emit_authorized_assistant_answer(
			session_doc=session_doc,
			answer_text="Accounts Receivable Aging as of 2026-05-12.",
			answer_type=ANSWER_TYPE_GOVERNED_REPORT,
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			assistant_text_payload=_assistant_text_payload,
			interaction_contract=self._interaction(raw_message),
			followup_resolution=self._followup(mode="compiled_first_turn", grounded=True),
			execution_path=self._execution_path(path="compiled_first_turn", requires_runtime=True, grounded_required=True),
			runtime_trace_payload={"agent_meta": {"engine": "qwen"}, "tool_trace": []},
			grounded_turn_context=self._grounded_turn(),
			authority_context={
				"normalized_family_artifact": self._normalized_artifact(),
				"user_intent_boundary": self._v1_ib_boundary(raw_message, allow_report=True),
			},
			pre_assistant_tool_payloads=[{"type": "qwen_pre_authorized_payload", "value": "safe after authority"}],
		)

		self.assertTrue(result.emitted)
		self.assertEqual([message["role"] for message in session_doc.messages], ["tool", "tool", "tool", "assistant"])
		self.assertEqual(session_doc.messages[0]["content"]["type"], "qwen_pre_authorized_payload")
		self.assertEqual(session_doc.messages[1]["content"]["type"], "qwen_audit_envelope")
		self.assertEqual(session_doc.messages[2]["content"]["type"], AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE)

	def test_blocked_business_authority_does_not_append_pre_assistant_tool_payloads(self):
		session_doc = FakeSessionDoc()
		selected_text = "This business text must not leak."
		result = emit_authorized_assistant_answer(
			session_doc=session_doc,
			answer_text=selected_text,
			answer_type=ANSWER_TYPE_GOVERNED_REPORT,
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			assistant_text_payload=_assistant_text_payload,
			interaction_contract=self._interaction(),
			followup_resolution=self._followup(mode="compiled_first_turn", grounded=True),
			execution_path=self._execution_path(path="compiled_first_turn", requires_runtime=True, grounded_required=True),
			pre_assistant_tool_payloads=[
				{"type": "qwen_pre_authorized_payload", "value": "This business text must not leak."}
			],
		)

		self.assertFalse(result.blocked)
		self.assertTrue(result.emitted)
		self.assertEqual(result.answer_type, ANSWER_TYPE_CONTROL)
		self._assert_v1_veto_without_selected_answer_leak(session_doc, selected_text)
		self.assertNotIn("qwen_pre_authorized_payload", str(session_doc.messages))

	def test_final_answer_authority_without_v1_ib_contract_vetoes_governed_report(self):
		session_doc = FakeSessionDoc()
		selected_text = "FINAL_AUTHORITY_ONLY_SELECTED_ANSWER_SHOULD_NOT_LEAK"
		result = emit_authorized_assistant_answer(
			session_doc=session_doc,
			answer_text=selected_text,
			answer_type=ANSWER_TYPE_GOVERNED_REPORT,
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			assistant_text_payload=_assistant_text_payload,
			interaction_contract=self._interaction("Show EC7H-ITEM-A item sales"),
			followup_resolution=self._followup(mode="compiled_first_turn", grounded=True),
			execution_path=self._execution_path(path="compiled_first_turn", requires_runtime=True, grounded_required=True),
			runtime_trace_payload={"agent_meta": {"engine": "qwen"}, "tool_trace": []},
			grounded_turn_context=self._grounded_turn(),
			authority_context={"normalized_family_artifact": self._normalized_artifact()},
		)

		self.assertFalse(result.blocked)
		self.assertTrue(result.emitted)
		self.assertEqual(result.answer_type, ANSWER_TYPE_CONTROL)
		self._assert_v1_veto_without_selected_answer_leak(session_doc, selected_text)

	def test_stale_v1_ib_contract_vetoes_legacy_style_governed_report(self):
		session_doc = FakeSessionDoc()
		current_message = "Show EC7H-ITEM-A item sales and tell me whether to discount it"
		selected_text = "STALE_V1_CONTRACT_SELECTED_ANSWER_SHOULD_NOT_LEAK"
		result = emit_authorized_assistant_answer(
			session_doc=session_doc,
			answer_text=selected_text,
			answer_type=ANSWER_TYPE_GOVERNED_REPORT,
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			assistant_text_payload=_assistant_text_payload,
			interaction_contract=self._interaction(current_message),
			followup_resolution=self._followup(mode="compiled_first_turn", grounded=True),
			execution_path=self._execution_path(path="compiled_first_turn", requires_runtime=True, grounded_required=True),
			runtime_trace_payload={"agent_meta": {"engine": "qwen"}, "tool_trace": []},
			grounded_turn_context=self._grounded_turn(),
			authority_context={
				"normalized_family_artifact": self._normalized_artifact(),
				"user_intent_boundary": self._v1_ib_boundary("Show EC7H-ITEM-A item sales", allow_report=True),
			},
		)

		self.assertFalse(result.blocked)
		self.assertTrue(result.emitted)
		self.assertEqual(result.answer_type, ANSWER_TYPE_CONTROL)
		self._assert_v1_veto_without_selected_answer_leak(session_doc, selected_text)

	def test_bounded_policy_refusal_allows_only_with_boundary_metadata(self):
		session_doc = FakeSessionDoc()
		result = emit_authorized_assistant_answer(
			session_doc=session_doc,
			answer_text="I can show current evidence, but I cannot predict default without an approved model.",
			answer_type=ANSWER_TYPE_POLICY_BOUNDARY,
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			assistant_text_payload=_assistant_text_payload,
			interaction_contract=self._interaction(),
			followup_resolution=self._followup(mode="reasoning_boundary", grounded=False),
			execution_path=self._execution_path(path="reasoning_boundary"),
			authority_context={"knowledge_boundary": self._policy_boundary()},
		)

		self.assertTrue(result.emitted)
		self.assertEqual(result.preflight_status, "bounded")
		self.assertEqual(result.final_answer_authority["authority_source"], "policy_boundary")

	def test_governed_artifact_policy_boundary_refusal_allows_emission(self):
		session_doc = FakeSessionDoc()
		result = emit_authorized_assistant_answer(
			session_doc=session_doc,
			answer_text="I can't recommend a reorder without an approved company decision rule.",
			answer_type=ANSWER_TYPE_POLICY_BOUNDARY,
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			assistant_text_payload=_assistant_text_payload,
			interaction_contract=self._interaction(),
			followup_resolution=self._followup(mode="visible_context_boundary", grounded=True),
			execution_path=self._execution_path(path="visible_context_boundary"),
			authority_context={"visible_context_trace": self._governed_artifact_policy_boundary_trace()},
			grounded_turn_context=self._grounded_turn(),
		)

		self.assertTrue(result.emitted)
		self.assertFalse(result.blocked)
		self.assertEqual(result.preflight_status, "bounded")
		self.assertEqual(result.final_answer_authority["authority_source"], "governed_artifact")
		self.assertEqual(result.final_answer_authority["policy_boundary"], "recommendation_boundary")

	def test_visible_context_resolution_policy_boundary_refusal_allows_emission(self):
		session_doc = FakeSessionDoc()
		result = emit_authorized_assistant_answer(
			session_doc=session_doc,
			answer_text="The current context has no visible invoice table.",
			answer_type=ANSWER_TYPE_POLICY_BOUNDARY,
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			assistant_text_payload=_assistant_text_payload,
			interaction_contract=self._interaction(),
			followup_resolution=self._followup(mode="visible_context_boundary", grounded=True),
			execution_path=self._execution_path(path="visible_context_boundary"),
			authority_context={"visible_context_trace": self._visible_context_resolution_boundary_trace()},
		)

		self.assertTrue(result.emitted)
		self.assertFalse(result.blocked)
		self.assertEqual(result.preflight_status, "bounded")
		self.assertEqual(result.final_answer_authority["authority_source"], "visible_context_resolution")
		self.assertEqual(result.final_answer_authority["policy_boundary"], "visible_context_boundary")

	def test_business_factual_answer_with_bounded_policy_authority_blocks(self):
		session_doc = FakeSessionDoc()
		result = emit_authorized_assistant_answer(
			session_doc=session_doc,
			answer_text="This customer will default next month.",
			answer_type=ANSWER_TYPE_BUSINESS_FACTUAL,
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			assistant_text_payload=_assistant_text_payload,
			interaction_contract=self._interaction("Show EC7H-CUST-A customer details"),
			followup_resolution=self._followup(mode="prediction", grounded=False),
			execution_path=self._execution_path(path="prediction"),
			authority_context={
				"knowledge_boundary": self._policy_boundary(),
				"user_intent_boundary": self._v1_ib_boundary("Show EC7H-CUST-A customer details", allow_report=True),
			},
		)

		self.assertTrue(result.blocked)
		self.assertFalse(result.emitted)
		self.assertEqual(result.block_reason, "business_answer_bounded_preflight_requires_policy_boundary_answer_type")
		self.assertNotIn("assistant", [message["role"] for message in session_doc.messages])

	def test_reasoning_business_answer_with_bounded_policy_authority_blocks(self):
		session_doc = FakeSessionDoc()
		result = emit_authorized_assistant_answer(
			session_doc=session_doc,
			answer_text="Collect from this customer first.",
			answer_type=ANSWER_TYPE_REASONING,
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			assistant_text_payload=_assistant_text_payload,
			interaction_contract=self._interaction("Show EC7H-CUST-A customer details"),
			followup_resolution=self._followup(mode="reasoning_boundary", grounded=False),
			execution_path=self._execution_path(path="reasoning_boundary"),
			authority_context={
				"knowledge_boundary": self._policy_boundary(),
				"user_intent_boundary": self._v1_ib_boundary("Show EC7H-CUST-A customer details", allow_report=True),
			},
		)

		self.assertTrue(result.blocked)
		self.assertFalse(result.emitted)
		self.assertEqual(result.block_reason, "business_answer_bounded_preflight_requires_policy_boundary_answer_type")
		self.assertNotIn("assistant", [message["role"] for message in session_doc.messages])

	def test_policy_boundary_without_boundary_metadata_blocks(self):
		session_doc = FakeSessionDoc()
		result = emit_authorized_assistant_answer(
			session_doc=session_doc,
			answer_text="I cannot answer that.",
			answer_type=ANSWER_TYPE_POLICY_BOUNDARY,
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			assistant_text_payload=_assistant_text_payload,
			interaction_contract=self._interaction(),
			followup_resolution=self._followup(mode="reasoning_boundary", grounded=False),
			execution_path=self._execution_path(path="reasoning_boundary"),
		)

		self.assertTrue(result.blocked)
		self.assertFalse(result.emitted)
		self.assertEqual(result.block_reason, "policy_boundary_authority_source_not_allowed")
		self.assertNotIn("assistant", [message["role"] for message in session_doc.messages])

	def test_control_meta_answer_requires_explicit_non_business_authority(self):
		missing_session = FakeSessionDoc()
		missing_result = emit_authorized_assistant_answer(
			session_doc=missing_session,
			answer_text="Which report do you mean?",
			answer_type=ANSWER_TYPE_CONTROL,
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			assistant_text_payload=_assistant_text_payload,
		)

		self.assertTrue(missing_result.blocked)
		self.assertEqual(missing_result.block_reason, "missing_control_authority_fields:authority_source,answer_mode,reason")

		allowed_session = FakeSessionDoc()
		allowed_result = emit_authorized_assistant_answer(
			session_doc=allowed_session,
			answer_text="Which report do you mean?",
			answer_type=ANSWER_TYPE_CONTROL,
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			assistant_text_payload=_assistant_text_payload,
			control_meta_authority=self._control_authority(),
		)

		self.assertTrue(allowed_result.emitted)
		self.assertEqual(allowed_result.emission_contract["emission_status"], EMISSION_STATUS_EMITTED)
		self.assertEqual([message["role"] for message in allowed_session.messages], ["tool", "assistant"])


if __name__ == "__main__":
	unittest.main()
