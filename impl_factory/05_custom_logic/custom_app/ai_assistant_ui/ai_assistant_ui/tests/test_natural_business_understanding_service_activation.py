import json
import unittest

from ai_assistant_ui.qwen_chat.natural_business_understanding_service_activation import (
	build_nbu_always_on_shadow_trace,
	build_nbu_current_artifact_answer_response,
	build_nbu_presentation_activation_response,
	try_activate_nbu_presentation_response,
)


def _eligible_trace(action="reject_with_boundary", response_mode="boundary"):
	return {
		"type": "qwen_nbu_trace_contract",
		"request_id": "req-nbu-live",
		"candidate_interpretations": [{"candidate_id": "candidate-1"}],
		"professional_response": {
			"type": "qwen_nbu_professional_response_contract",
			"action": action,
			"response_mode": response_mode,
			"title": "Decision Not Available Yet",
			"answer_text": "I can show the ERP facts we have, but I cannot safely provide that decision yet.",
			"next_steps": ["ask for the supporting ERP facts behind this topic"],
			"safe_to_show": True,
			"quality_warnings": [],
		},
		"activation_assessment": {
			"type": "qwen_nbu_activation_assessment_contract",
			"activation_state": "eligible_shadow",
			"activation_mode": "presentation_only",
			"eligible_for_controlled_activation": True,
			"action": action,
			"response_mode": response_mode,
			"blockers": [],
			"warnings": [],
		},
	}


def _observe_trace(request_id="req-visible-context"):
	return {
		"type": "qwen_natural_business_understanding_trace_contract",
		"request_id": request_id,
		"candidate_interpretations": [],
		"conversation_action_decision": {
			"action": "observe_only",
			"response_mode": "shadow_trace_only",
		},
		"professional_response": {"safe_to_show": False, "quality_warnings": []},
		"activation_assessment": {
			"activation_state": "blocked_shadow",
			"activation_mode": "none",
			"eligible_for_controlled_activation": False,
			"action": "observe_only",
			"response_mode": "shadow_trace_only",
			"blockers": ["action_not_in_controlled_activation_allowlist"],
		},
		"schema_hardening_assessment": {"ok": True, "errors": [], "warnings": []},
	}


def _ar_artifact():
	return {
		"type": "qwen_normalized_family_artifact_contract",
		"artifact_id": "ar-aging-1",
		"title": "Accounts Receivable Aging",
		"family_id": "accounts_receivable_aging",
		"sections": {
			"top_customers": [
				{
					"rank": 1,
					"customer": "Capital Telecom (NPT)",
					"outstanding_amount": 97309500,
					"overdue_amount": 35274500,
				},
				{
					"rank": 2,
					"customer": "35th Street Mobile Wholesale",
					"outstanding_amount": 84837000,
					"overdue_amount": 58212000,
				},
			]
		},
	}


def _supplier_artifact():
	return {
		"type": "qwen_normalized_family_artifact_contract",
		"artifact_id": "supplier-list-1",
		"title": "Supplier Master List",
		"family_id": "supplier_master",
		"rows": [
			{"rank": 1, "supplier": "Shan Yoma Electronics"},
			{"rank": 2, "supplier": "Shwe Taung Electronics Supply"},
		],
	}


def _tool_message(payload):
	return {"role": "tool", "content": json.dumps(payload)}


def _assistant_message(text):
	return {"role": "assistant", "content": json.dumps({"type": "text", "text": text, "format": "markdown"})}


def _ar_visible_text():
	return """Accounts Receivable Aging as of 2026-05-01

Summary
| Metric | Value (MMK) |
| --- | --- |
| Outstanding Total | 790,855,000 |

Top Customers
| Customer | Outstanding (MMK) | Total Due (MMK) | Overdue (31+) (MMK) |
| --- | --- | --- | --- |
| Capital Telecom (NPT) | 97,309,500 | 63,654,500 | 35,274,500 |
| 35th Street Mobile Wholesale | 84,837,000 | 82,527,000 | 58,212,000 |
"""


class NaturalBusinessUnderstandingServiceActivationTests(unittest.TestCase):
	def test_always_on_shadow_trace_records_observation_without_behavior_change(self):
		def fake_runtime_call(**kwargs):
			return {
				"ok": True,
				"interpretation": {
					"candidate_interpretations": [
						{
							"candidate_id": "candidate-1",
							"intent_scope": "capability_question",
							"business_domain": "erp_reporting",
							"requested_action": "show",
							"evidence_need": "unknown",
							"authority_class": "safe_read",
							"model_confidence": 0.88,
						}
					]
				},
			}

		trace = build_nbu_always_on_shadow_trace(
			request_id="req-shadow",
			session_id="session-shadow",
			user_id="user@example.com",
			raw_message="what can you do",
			runtime_call=fake_runtime_call,
		)

		audit = trace["always_on_shadow_audit"]
		self.assertEqual(audit["type"], "qwen_nbu_always_on_shadow_audit_contract")
		self.assertEqual(audit["shadow_state"], "observed")
		self.assertFalse(audit["live_behavior_changed"])
		self.assertFalse(audit["runtime_execution_enabled"])
		self.assertEqual(audit["request_id"], "req-shadow")
		self.assertIn("schema_hardening_ok", audit)

	def test_always_on_shadow_trace_fails_open_when_runtime_raises(self):
		def fake_runtime_call(**kwargs):
			raise RuntimeError("runtime unavailable")

		trace = build_nbu_always_on_shadow_trace(
			request_id="req-shadow-fail",
			session_id="session-shadow",
			user_id="user@example.com",
			raw_message="show customer risk",
			runtime_call=fake_runtime_call,
		)

		self.assertEqual(trace["conversation_action_decision"]["action"], "observe_only")
		self.assertFalse(trace["always_on_shadow_audit"]["live_behavior_changed"])
		self.assertEqual(trace["always_on_shadow_audit"]["shadow_state"], "observed")

	def test_eligible_presentation_response_builds_live_activation_contract(self):
		activation = build_nbu_presentation_activation_response(_eligible_trace())

		self.assertTrue(activation["activated"])
		self.assertIn("Decision Not Available Yet", activation["answer_text"])
		self.assertIn("- ask for the supporting ERP facts behind this topic", activation["answer_text"])
		contract = activation["activation_contract"]
		self.assertEqual(contract["type"], "qwen_nbu_presentation_activation_contract")
		self.assertEqual(contract["activation_state"], "activated")
		self.assertEqual(contract["activation_mode"], "presentation_only")
		self.assertFalse(contract["runtime_execution_enabled"])

	def test_delegated_direct_answer_stays_out_of_live_activation(self):
		trace = _eligible_trace(action="answer_from_current_artifact", response_mode="direct_answer")
		trace["professional_response"]["safe_to_show"] = False
		trace["activation_assessment"].update(
			{
				"activation_state": "blocked_shadow",
				"eligible_for_controlled_activation": False,
				"blockers": ["delegated_to_existing_artifact_renderer"],
			}
		)

		activation = build_nbu_presentation_activation_response(trace)

		self.assertFalse(activation["activated"])
		self.assertIn("delegated_to_existing_artifact_renderer", activation["blockers"])

	def test_quality_warning_blocks_live_activation(self):
		trace = _eligible_trace()
		trace["professional_response"]["quality_warnings"] = ["user_text_internal_term:runtime"]

		activation = build_nbu_presentation_activation_response(trace)

		self.assertFalse(activation["activated"])
		self.assertIn("professional_response_quality_warnings", activation["blockers"])

	def test_nbu_live_clarification_activates_as_safe_presentation(self):
		trace = _eligible_trace(action="ask_clarification", response_mode="clarification")

		activation = build_nbu_presentation_activation_response(trace)

		self.assertTrue(activation["activated"])
		self.assertEqual(activation["activation_contract"]["activation_level"], "presentation_only")
		self.assertEqual(activation["activation_contract"]["required_action_lane"], "presentation")
		self.assertFalse(activation["activation_contract"]["runtime_execution_enabled"])

	def test_supported_options_activates_as_safe_presentation(self):
		trace = _eligible_trace(action="show_supported_options", response_mode="supported_options")

		activation = build_nbu_presentation_activation_response(trace)

		self.assertTrue(activation["activated"])
		self.assertEqual(activation["activation_contract"]["action"], "show_supported_options")
		self.assertEqual(activation["activation_contract"]["required_action_lane"], "presentation")

	def test_execution_required_action_stays_out_of_presentation_activation(self):
		trace = _eligible_trace(action="execute_governed_requery", response_mode="governed_query")
		trace["activation_assessment"].update(
			{
				"activation_state": "blocked_shadow",
				"eligible_for_controlled_activation": False,
				"activation_mode": "none",
				"blockers": ["requires_execution_lane_activation"],
			}
		)

		activation = build_nbu_presentation_activation_response(trace)

		self.assertFalse(activation["activated"])
		self.assertIn("requires_execution_lane_activation", activation["blockers"])

	def test_current_artifact_answer_is_not_activated_by_fc4_try_path(self):
		appended_payloads = []
		messages = []

		def append_message(session_doc, role, text):
			messages.append((role, text))

		def append_payload(session_doc, payload):
			appended_payloads.append(payload)

		def assistant_text_payload(text):
			return text

		def save_session(session_doc, **kwargs):
			session_doc["saved"] = True

		trace = _eligible_trace(action="answer_from_current_artifact", response_mode="direct_answer")
		trace["professional_response"]["safe_to_show"] = False
		trace["activation_assessment"].update(
			{
				"activation_state": "blocked_shadow",
				"eligible_for_controlled_activation": False,
				"blockers": ["delegated_to_existing_artifact_renderer"],
			}
		)

		handled, payload = try_activate_nbu_presentation_response(
			session_doc={},
			request_id="req-direct-answer",
			session_id="session-live",
			user_id="user@example.com",
			raw_message="explain rank 2",
			nbu_trace_payload=trace,
			nbu_trace_already_appended=True,
			activation_level="presentation_only",
			append_message=append_message,
			append_tool_payload=append_payload,
			assistant_text_payload=assistant_text_payload,
			save_session=save_session,
		)

		self.assertFalse(handled)
		self.assertIsNone(payload)
		self.assertEqual(messages, [])
		self.assertEqual(appended_payloads, [])

	def test_current_artifact_answer_blocks_when_activation_level_is_presentation_only(self):
		trace = {
			"request_id": "req-rank-2",
			"selected_candidate_id": "candidate-rank-2",
			"candidate_interpretations": [
				{"candidate_id": "candidate-rank-2", "requested_metrics": ["overdue_amount"]}
			],
			"conversation_action_decision": {
				"action": "answer_from_current_artifact",
				"response_mode": "direct_answer",
			},
			"evidence_plan": {"current_artifact_supported": True},
			"authority_plan": {"approval_state": "safe_read_authority"},
			"context_resolution": {
				"status": "resolved",
				"resolved_rank": 2,
				"resolved_entity": {
					"entity_label": "35th Street Mobile Wholesale",
					"row": {
						"rank": 2,
						"customer": "35th Street Mobile Wholesale",
						"overdue_amount": 58212000,
					},
				},
			},
			"schema_hardening_assessment": {"ok": True, "errors": [], "warnings": []},
		}

		activation = build_nbu_current_artifact_answer_response(
			trace,
			activation_level="presentation_only",
		)

		self.assertFalse(activation["activated"])
		self.assertEqual(activation["required_action_lane"], "current_artifact")
		self.assertIn("nbu_action_lane_not_enabled", activation["blockers"])

	def test_current_artifact_rank_answer_uses_resolved_row_facts(self):
		trace = {
			"request_id": "req-rank-2",
			"selected_candidate_id": "candidate-rank-2",
			"candidate_interpretations": [
				{
					"candidate_id": "candidate-rank-2",
					"requested_metrics": ["overdue_amount", "outstanding_amount"],
				}
			],
			"conversation_action_decision": {
				"action": "answer_from_current_artifact",
				"response_mode": "direct_answer",
			},
			"evidence_plan": {"current_artifact_supported": True},
			"authority_plan": {"approval_state": "safe_read_authority"},
			"schema_hardening_assessment": {"ok": True, "errors": [], "warnings": []},
			"context_resolution": {
				"status": "resolved",
				"resolved_rank": 2,
				"resolved_entity": {
					"entity_label": "35th Street Mobile Wholesale",
					"row": {
						"rank": 2,
						"customer": "35th Street Mobile Wholesale",
						"outstanding_amount": 84837000,
						"overdue_amount": 58212000,
					},
				},
			},
		}

		activation = build_nbu_current_artifact_answer_response(trace)

		self.assertTrue(activation["activated"])
		self.assertIn("Rank 2 is 35th Street Mobile Wholesale", activation["answer_text"])
		self.assertIn("Overdue Amount: 58,212,000 MMK", activation["answer_text"])
		self.assertIn("Outstanding Amount: 84,837,000 MMK", activation["answer_text"])
		self.assertEqual(
			activation["activation_contract"]["type"],
			"qwen_nbu_current_artifact_answer_activation_contract",
		)
		self.assertEqual(activation["activation_contract"]["activation_level"], "current_artifact_answer")
		self.assertEqual(activation["activation_contract"]["required_action_lane"], "current_artifact")
		self.assertTrue(activation["activation_contract"]["live_behavior_changed_by_fc5"])

	def test_current_artifact_rank_answer_blocks_when_schema_hardening_fails(self):
		trace = {
			"request_id": "req-rank-2",
			"selected_candidate_id": "candidate-rank-2",
			"candidate_interpretations": [{"candidate_id": "candidate-rank-2"}],
			"conversation_action_decision": {
				"action": "answer_from_current_artifact",
				"response_mode": "direct_answer",
			},
			"evidence_plan": {"current_artifact_supported": True},
			"authority_plan": {"approval_state": "safe_read_authority"},
			"schema_hardening_assessment": {"ok": False, "errors": ["context_resolution_required"], "warnings": []},
			"context_resolution": {
				"status": "resolved",
				"resolved_rank": 2,
				"resolved_entity": {
					"entity_label": "35th Street Mobile Wholesale",
					"row": {"rank": 2, "customer": "35th Street Mobile Wholesale"},
				},
			},
		}

		activation = build_nbu_current_artifact_answer_response(trace)

		self.assertFalse(activation["activated"])
		self.assertIn("context_resolution_required", activation["blockers"])

	def test_try_path_activates_current_artifact_answer_under_fc5_level(self):
		appended_payloads = []
		messages = []

		def append_message(session_doc, role, text):
			messages.append((role, text))

		def append_payload(session_doc, payload):
			appended_payloads.append(payload)

		def assistant_text_payload(text):
			return text

		def save_session(session_doc, **kwargs):
			session_doc["saved"] = True

		trace = {
			"request_id": "req-rank-2",
			"selected_candidate_id": "candidate-rank-2",
			"candidate_interpretations": [
				{
					"candidate_id": "candidate-rank-2",
					"requested_metrics": ["overdue_amount", "outstanding_amount"],
				}
			],
			"conversation_action_decision": {
				"action": "answer_from_current_artifact",
				"response_mode": "direct_answer",
			},
			"evidence_plan": {"current_artifact_supported": True},
			"authority_plan": {"approval_state": "safe_read_authority"},
			"schema_hardening_assessment": {"ok": True, "errors": [], "warnings": []},
			"context_resolution": {
				"status": "resolved",
				"resolved_rank": 2,
				"resolved_entity": {
					"entity_label": "35th Street Mobile Wholesale",
					"row": {
						"rank": 2,
						"customer": "35th Street Mobile Wholesale",
						"outstanding_amount": 84837000,
						"overdue_amount": 58212000,
					},
				},
			},
		}

		handled, payload = try_activate_nbu_presentation_response(
			session_doc={},
			request_id="req-rank-2",
			session_id="session-live",
			user_id="user@example.com",
			raw_message="explain rank 2",
			nbu_trace_payload=trace,
			nbu_trace_already_appended=True,
			append_message=append_message,
			append_tool_payload=append_payload,
			assistant_text_payload=assistant_text_payload,
			save_session=save_session,
		)

		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "current_artifact_answer")
		self.assertTrue(any("Rank 2 is 35th Street Mobile Wholesale" in message[1] for message in messages))
		activation_contract = next(
			item for item in appended_payloads if item.get("type") == "qwen_nbu_current_artifact_answer_activation_contract"
		)
		self.assertTrue(activation_contract["live_behavior_changed_by_fc5"])
		self.assertFalse(activation_contract["runtime_execution_enabled"])

	def test_presentation_activation_reuses_precomputed_shadow_trace_without_second_runtime_call(self):
		calls = {"count": 0}
		appended_payloads = []
		messages = []

		def runtime_call(**kwargs):
			calls["count"] += 1
			raise AssertionError("runtime should not be called when trace is precomputed")

		def append_message(session_doc, role, text):
			messages.append((role, text))

		def append_payload(session_doc, payload):
			appended_payloads.append(payload)

		def assistant_text_payload(text):
			return text

		def save_session(session_doc, **kwargs):
			session_doc["saved"] = True

		handled, payload = try_activate_nbu_presentation_response(
			session_doc={},
			request_id="req-nbu-live",
			session_id="session-live",
			user_id="user@example.com",
			raw_message="will the first customer default next month?",
			nbu_trace_payload=_eligible_trace(),
			nbu_trace_already_appended=True,
			append_message=append_message,
			append_tool_payload=append_payload,
			assistant_text_payload=assistant_text_payload,
			save_session=save_session,
			runtime_call=runtime_call,
		)

		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "presentation_only")
		self.assertEqual(calls["count"], 0)
		self.assertFalse(any(item.get("type") == "qwen_nbu_trace_contract" for item in appended_payloads))
		self.assertTrue(any(item.get("type") == "qwen_nbu_presentation_activation_contract" for item in appended_payloads))
		activation_contract = next(item for item in appended_payloads if item.get("type") == "qwen_nbu_presentation_activation_contract")
		self.assertTrue(activation_contract["live_behavior_changed_by_fc4"])
		self.assertEqual(activation_contract["activation_level"], "current_artifact_answer")
		self.assertEqual(activation_contract["required_action_lane"], "presentation")

	def test_early_activation_requirement_does_not_intercept_fresh_query_clarification(self):
		appended_payloads = []
		messages = []

		def append_message(session_doc, role, text):
			messages.append((role, text))

		def append_payload(session_doc, payload):
			appended_payloads.append(payload)

		def assistant_text_payload(text):
			return text

		def save_session(session_doc, **kwargs):
			session_doc["saved"] = True

		handled, payload = try_activate_nbu_presentation_response(
			session_doc={},
			request_id="req-fresh-customer-risk",
			session_id="session-live",
			user_id="user@example.com",
			raw_message="show customer risk",
			nbu_trace_payload=_eligible_trace(action="ask_clarification", response_mode="clarification"),
			append_message=append_message,
			append_tool_payload=append_payload,
			assistant_text_payload=assistant_text_payload,
			save_session=save_session,
			require_visible_context_reference=True,
		)

		self.assertFalse(handled)
		self.assertIsNone(payload)
		self.assertEqual(messages, [])
		self.assertEqual(appended_payloads, [])

	def test_visible_context_fallback_answers_named_prior_artifact_rank(self):
		appended_payloads = []
		messages = []
		session_doc = {
			"messages": [
				_tool_message(_ar_artifact()),
				_tool_message(_supplier_artifact()),
			]
		}

		def append_message(session_doc, role, text):
			messages.append((role, text))

		def append_payload(session_doc, payload):
			appended_payloads.append(payload)

		def assistant_text_payload(text):
			return text

		def save_session(session_doc, **kwargs):
			session_doc["saved"] = True

		handled, payload = try_activate_nbu_presentation_response(
			session_doc=session_doc,
			request_id="req-visible-prior",
			session_id="session-live",
			user_id="user@example.com",
			raw_message="who is in second position in the above AR table?",
			current_artifact=_supplier_artifact(),
			nbu_trace_payload=_observe_trace("req-visible-prior"),
			append_message=append_message,
			append_tool_payload=append_payload,
			assistant_text_payload=assistant_text_payload,
			save_session=save_session,
		)

		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "current_artifact_answer")
		self.assertTrue(any("Rank 2 is 35th Street Mobile Wholesale" in message[1] for message in messages))

	def test_visible_context_rank_resolution_overrides_generic_nbu_clarification(self):
		appended_payloads = []
		messages = []
		session_doc = {"messages": [_tool_message(_ar_artifact())]}

		def append_message(session_doc, role, text):
			messages.append((role, text))

		def append_payload(session_doc, payload):
			appended_payloads.append(payload)

		def assistant_text_payload(text):
			return text

		def save_session(session_doc, **kwargs):
			session_doc["saved"] = True

		handled, payload = try_activate_nbu_presentation_response(
			session_doc=session_doc,
			request_id="req-visible-overrides-clarify",
			session_id="session-live",
			user_id="user@example.com",
			raw_message="who is in second position in the above table?",
			current_artifact=_ar_artifact(),
			nbu_trace_payload=_eligible_trace(action="ask_clarification", response_mode="clarification"),
			append_message=append_message,
			append_tool_payload=append_payload,
			assistant_text_payload=assistant_text_payload,
			save_session=save_session,
			require_visible_context_reference=True,
		)

		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "current_artifact_answer")
		self.assertTrue(any("Rank 2 is 35th Street Mobile Wholesale" in message[1] for message in messages))
		self.assertFalse(any("Clarification Needed" in message[1] for message in messages))

	def test_visible_markdown_table_context_answers_when_structured_artifact_missing(self):
		appended_payloads = []
		messages = []
		session_doc = {"messages": [_assistant_message(_ar_visible_text())]}

		def append_message(session_doc, role, text):
			messages.append((role, text))

		def append_payload(session_doc, payload):
			appended_payloads.append(payload)

		def assistant_text_payload(text):
			return text

		def save_session(session_doc, **kwargs):
			session_doc["saved"] = True

		handled, payload = try_activate_nbu_presentation_response(
			session_doc=session_doc,
			request_id="req-visible-markdown",
			session_id="session-live",
			user_id="user@example.com",
			raw_message="who is in second position in the above table?",
			current_artifact={},
			nbu_trace_payload=_eligible_trace(action="ask_clarification", response_mode="clarification"),
			append_message=append_message,
			append_tool_payload=append_payload,
			assistant_text_payload=assistant_text_payload,
			save_session=save_session,
			require_visible_context_reference=True,
		)

		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "current_artifact_answer")
		self.assertTrue(any("Rank 2 is 35th Street Mobile Wholesale" in message[1] for message in messages))
		self.assertTrue(any("Overdue Amount: 58,212,000 MMK" in message[1] for message in messages))

	def test_visible_context_uses_raw_message_when_effective_message_is_rewritten(self):
		appended_payloads = []
		messages = []
		session_doc = {"messages": [_assistant_message(_ar_visible_text())]}

		def append_message(session_doc, role, text):
			messages.append((role, text))

		def append_payload(session_doc, payload):
			appended_payloads.append(payload)

		def assistant_text_payload(text):
			return text

		def save_session(session_doc, **kwargs):
			session_doc["saved"] = True

		handled, payload = try_activate_nbu_presentation_response(
			session_doc=session_doc,
			request_id="req-visible-raw-over-effective",
			session_id="session-live",
			user_id="user@example.com",
			raw_message="who is in second position in the above table?",
			effective_message="accounts_receivable_read",
			current_artifact={},
			nbu_trace_payload=_eligible_trace(action="ask_clarification", response_mode="clarification"),
			append_message=append_message,
			append_tool_payload=append_payload,
			assistant_text_payload=assistant_text_payload,
			save_session=save_session,
			require_visible_context_reference=True,
		)

		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "current_artifact_answer")
		self.assertTrue(any("Rank 2 is 35th Street Mobile Wholesale" in message[1] for message in messages))

	def test_visible_context_fallback_keeps_above_table_on_current_artifact(self):
		appended_payloads = []
		messages = []
		session_doc = {
			"messages": [
				_tool_message(_supplier_artifact()),
				_tool_message(_ar_artifact()),
			]
		}

		def append_message(session_doc, role, text):
			messages.append((role, text))

		def append_payload(session_doc, payload):
			appended_payloads.append(payload)

		def assistant_text_payload(text):
			return text

		def save_session(session_doc, **kwargs):
			session_doc["saved"] = True

		handled, payload = try_activate_nbu_presentation_response(
			session_doc=session_doc,
			request_id="req-visible-current",
			session_id="session-live",
			user_id="user@example.com",
			raw_message="who is in second position in the above table?",
			current_artifact=_ar_artifact(),
			nbu_trace_payload=_observe_trace("req-visible-current"),
			append_message=append_message,
			append_tool_payload=append_payload,
			assistant_text_payload=assistant_text_payload,
			save_session=save_session,
		)

		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "current_artifact_answer")
		self.assertTrue(any("Rank 2 is 35th Street Mobile Wholesale" in message[1] for message in messages))

	def test_visible_context_fallback_clarifies_ambiguous_deictic_row(self):
		appended_payloads = []
		messages = []
		session_doc = {"messages": [_tool_message(_ar_artifact())]}

		def append_message(session_doc, role, text):
			messages.append((role, text))

		def append_payload(session_doc, payload):
			appended_payloads.append(payload)

		def assistant_text_payload(text):
			return text

		def save_session(session_doc, **kwargs):
			session_doc["saved"] = True

		handled, payload = try_activate_nbu_presentation_response(
			session_doc=session_doc,
			request_id="req-visible-ambiguous",
			session_id="session-live",
			user_id="user@example.com",
			raw_message="why is this customer risky?",
			current_artifact=_ar_artifact(),
			nbu_trace_payload=_observe_trace("req-visible-ambiguous"),
			append_message=append_message,
			append_tool_payload=append_payload,
			assistant_text_payload=assistant_text_payload,
			save_session=save_session,
		)

		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "presentation_only")
		assistant_answers = [text for role, text in messages if role == "assistant"]
		self.assertTrue(any("Clarification Needed" in answer for answer in assistant_answers))
		self.assertTrue(any("Capital Telecom (NPT)" in answer for answer in assistant_answers))
		self.assertTrue(any("35th Street Mobile Wholesale" in answer for answer in assistant_answers))


if __name__ == "__main__":
	unittest.main()
