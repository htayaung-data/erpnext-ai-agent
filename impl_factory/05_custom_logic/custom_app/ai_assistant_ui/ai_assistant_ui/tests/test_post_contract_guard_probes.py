import json
import unittest
from dataclasses import dataclass
from typing import Any, Dict

from ai_assistant_ui.qwen_chat.contracts import (
	build_artifact_enrichment_recovery_contract,
	build_conversational_repair_intent_contract,
	run_phase7a_knowledge_boundary_contract_probe,
	run_phase8a_recovery_contract_probe,
)
from ai_assistant_ui.qwen_chat.knowledge_boundary import (
	render_knowledge_boundary_answer,
	run_phase7d_boundary_response_probe,
)
from ai_assistant_ui.qwen_chat.reasoning_execution import (
	run_phase6d_reasoning_continuation_guardrail_smoke,
)
from ai_assistant_ui.qwen_chat.service import (
	_build_recovery_guidance_answer,
	_latest_recovery_contract,
)
from ai_assistant_ui.qwen_chat.semantic_repair_intent import (
	SemanticRepairIntent,
	SemanticRepairIntentResult,
	_validate_semantic_payload,
	build_repair_intent_contract_from_semantic_result,
)


@dataclass
class _FakeMessage:
	role: str
	content: str


class _FakeSessionDoc:
	def __init__(self, messages):
		self._messages = list(messages)

	def get(self, key, default=None):
		if key == "messages":
			return list(self._messages)
		return default


class TestPostContractGuardProbes(unittest.TestCase):
	def _assert_ok_tree(self, payload: Dict[str, Any], path: str) -> None:
		self.assertIsInstance(payload, dict, f"{path} must return a dict payload.")
		self.assertTrue(bool(payload.get("ok")), f"{path} did not report ok=True: {payload!r}")
		for key, value in payload.items():
			if key == "ok":
				continue
			if isinstance(value, dict) and "ok" in value:
				self._assert_ok_tree(value, f"{path}.{key}")

	def test_phase6_continuation_guardrail_probe(self):
		self._assert_ok_tree(
			run_phase6d_reasoning_continuation_guardrail_smoke(),
			"phase6_continuation_guardrail",
		)

	def test_phase7a_boundary_contract_probe(self):
		self._assert_ok_tree(
			run_phase7a_knowledge_boundary_contract_probe(),
			"phase7a_boundary_contract",
		)

	def test_phase7d_boundary_response_probe(self):
		self._assert_ok_tree(
			run_phase7d_boundary_response_probe(),
			"phase7d_boundary_response",
		)

	def test_phase8a_recovery_contract_probe(self):
		self._assert_ok_tree(
			run_phase8a_recovery_contract_probe(),
			"phase8a_recovery_contract",
		)

	def test_semantic_repair_rejects_substantive_followup_as_acceptance(self):
		intent = _validate_semantic_payload(
			payload={
				"repair_intent_type": "accept_recovery_action",
				"accepted_recovery_action": "run_alternative_governed_query",
				"confidence": 0.94,
				"reason": "User wants the governed alternative.",
				"preserve_scope": True,
				"preserve_entity_dimension": True,
				"preserve_time_context": True,
			},
			context={
				"available_recovery_actions": ["run_alternative_governed_query", "clarify_target_output"],
				"preservable_scope_available": True,
				"preservable_dimension_available": True,
				"preservable_time_available": True,
			},
			message="include qty column",
			latest_grounded_turn={"grounded": True, "artifact_family_id": "ranking_analytics"},
		)
		self.assertIsNone(
			intent,
			"Substantive follow-up requests must not be auto-treated as recovery acceptance.",
		)

	def test_semantic_repair_acceptance_allows_explicit_confirmation(self):
		intent = _validate_semantic_payload(
			payload={
				"repair_intent_type": "accept_recovery_action",
				"accepted_recovery_action": "run_alternative_governed_query",
				"confidence": 0.94,
				"reason": "User explicitly accepted the governed alternative.",
				"preserve_scope": True,
				"preserve_entity_dimension": True,
				"preserve_time_context": True,
			},
			context={
				"available_recovery_actions": ["run_alternative_governed_query", "clarify_target_output"],
				"preservable_scope_available": True,
				"preservable_dimension_available": True,
				"preservable_time_available": True,
			},
			message="yes run that",
			latest_grounded_turn={"grounded": True, "artifact_family_id": "ranking_analytics"},
		)
		self.assertIsNotNone(intent, "Explicit confirmation should remain a valid recovery acceptance.")
		self.assertEqual(intent.repair_intent_type, "accept_recovery_action")
		self.assertEqual(intent.accepted_recovery_action, "run_alternative_governed_query")

	def test_boundary_renderer_tolerates_partial_contract(self):
		answer = render_knowledge_boundary_answer(
			boundary_contract={
				"knowledge_coverage_state": "unsupported_non_erp",
			},
			detail_answer="I can help with governed ERP reporting instead.",
		)
		self.assertIn("governed ERP assistant coverage", answer)
		self.assertIn("I can help with governed ERP reporting instead.", answer)

	def test_semantic_repair_rejects_unknown_recovery_action(self):
		intent = _validate_semantic_payload(
			payload={
				"repair_intent_type": "accept_recovery_action",
				"accepted_recovery_action": "unknown_action",
				"confidence": 0.94,
				"reason": "User accepted something invalid.",
			},
			context={
				"available_recovery_actions": ["run_alternative_governed_query", "clarify_target_output"],
				"preservable_scope_available": True,
				"preservable_dimension_available": True,
				"preservable_time_available": True,
			},
			message="yes run that",
			latest_grounded_turn={"grounded": True, "artifact_family_id": "ranking_analytics"},
		)
		self.assertIsNone(intent, "Unknown recovery actions must be rejected by governed validation.")

	def test_rejected_semantic_repair_result_builds_unresolved_contract(self):
		payload = build_repair_intent_contract_from_semantic_result(
			request_id="repair-rejected",
			session_id="phase8a",
			semantic_result=SemanticRepairIntentResult(
				status="rejected",
				intent=SemanticRepairIntent(
					repair_intent_type="accept_recovery_action",
					accepted_recovery_action="run_alternative_governed_query",
					confidence=0.41,
					reason="Low-confidence interpretation.",
				),
				validation_error="Runtime repair interpretation did not pass governed validation.",
			),
		)
		self.assertEqual(payload.get("repair_intent_type"), "not_applicable")
		self.assertEqual(payload.get("repair_state"), "unresolved")
		self.assertTrue(bool(payload.get("targets_prior_recovery")))

	def test_latest_recovery_contract_is_invalidated_by_accepted_repair(self):
		recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="recovery-1",
			session_id="phase8a",
			source_request_id="grounded-1",
			source_family_id="ranking_analytics",
			source_capability_id="sales_read",
			source_report="Sales Analytics",
			recovery_state="recoverable",
			available_recovery_actions=["run_alternative_governed_query"],
			recommended_recovery_action="run_alternative_governed_query",
			allowed_to_recover=True,
			confidence=0.9,
		).to_payload()
		accepted_repair_payload = build_conversational_repair_intent_contract(
			request_id="repair-accepted-1",
			session_id="phase8a",
			repair_intent_type="accept_recovery_action",
			repair_state="accepted",
			targets_prior_recovery=True,
			accepted_recovery_action="run_alternative_governed_query",
			reason="User accepted the governed recovery action.",
			allowed_next_lane="artifact_lane",
			confidence=0.96,
		).to_payload()
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(recovery_payload)),
				_FakeMessage(role="tool", content=json.dumps(accepted_repair_payload)),
			]
		)
		self.assertEqual(
			_latest_recovery_contract(session_doc),
			{},
			"Accepted repair should invalidate the stale prior recovery contract.",
		)

	def test_latest_recovery_contract_prefers_newer_recovery_after_prior_acceptance(self):
		old_recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="recovery-old",
			session_id="phase8a",
			source_request_id="grounded-old",
			source_family_id="ranking_analytics",
			source_capability_id="sales_read",
			source_report="Sales Analytics",
			recovery_state="recoverable",
			available_recovery_actions=["run_alternative_governed_query"],
			recommended_recovery_action="run_alternative_governed_query",
			allowed_to_recover=True,
			confidence=0.9,
		).to_payload()
		accepted_repair_payload = build_conversational_repair_intent_contract(
			request_id="repair-accepted-old",
			session_id="phase8a",
			repair_intent_type="accept_recovery_action",
			repair_state="accepted",
			targets_prior_recovery=True,
			accepted_recovery_action="run_alternative_governed_query",
			reason="User accepted the first recovery action.",
			allowed_next_lane="artifact_lane",
			confidence=0.96,
		).to_payload()
		new_recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="recovery-new",
			session_id="phase8a",
			source_request_id="grounded-new",
			source_family_id="transaction_listing",
			source_capability_id="sales_read",
			source_report="Sales Invoice List",
			recovery_state="clarify_recovery_target",
			available_recovery_actions=["clarify_target_output"],
			recommended_recovery_action="clarify_target_output",
			allowed_to_recover=True,
			confidence=0.78,
		).to_payload()
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(old_recovery_payload)),
				_FakeMessage(role="tool", content=json.dumps(accepted_repair_payload)),
				_FakeMessage(role="tool", content=json.dumps(new_recovery_payload)),
			]
		)
		latest = _latest_recovery_contract(session_doc)
		self.assertEqual(latest.get("request_id"), "recovery-new")
		self.assertEqual(latest.get("recommended_recovery_action"), "clarify_target_output")

	def test_latest_recovery_contract_ignores_malformed_tool_payloads(self):
		recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="recovery-valid",
			session_id="phase8a",
			source_request_id="grounded-valid",
			source_family_id="ranking_analytics",
			source_capability_id="sales_read",
			source_report="Sales Analytics",
			recovery_state="recoverable",
			available_recovery_actions=["run_alternative_governed_query"],
			recommended_recovery_action="run_alternative_governed_query",
			allowed_to_recover=True,
			confidence=0.9,
		).to_payload()
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content="{this is not valid json"),
				_FakeMessage(role="tool", content=json.dumps(recovery_payload)),
			]
		)
		latest = _latest_recovery_contract(session_doc)
		self.assertEqual(latest.get("request_id"), "recovery-valid")

	def test_recovery_guidance_answer_tolerates_partial_recovery_contract(self):
		answer = _build_recovery_guidance_answer(
			{
				"source_report": "",
				"alternative_report": None,
				"recommended_recovery_action": None,
				"preservable_scope": "not-a-dict",
				"preservable_dimensions": "not-a-list",
				"preservable_metrics": {"unexpected": True},
				"preservable_time_context": "not-a-dict",
			}
		)
		self.assertIn("the current governed artifact", answer)
		self.assertIn("Current recommended recovery path", answer)
