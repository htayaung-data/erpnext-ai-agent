import json
import unittest
from unittest.mock import patch

from ai_assistant_ui.qwen_chat import natural_business_understanding_governed_requery_activation as activation


class _InteractionContract:
	request_id = "req-nbu-fc6"
	session_id = "session-1"
	user_id = "Administrator"
	site_name = "erpai_prj1"


class _ResponsePolicyContract:
	def to_runtime_payload(self):
		return {"presentation": "concise"}


def _trace_payload(*, entity_type="customer", planner_mode="entity_detail_requery", status="ready_shadow"):
	return {
		"type": "qwen_natural_business_understanding_trace_contract",
		"request_id": "req-nbu-fc6",
		"session_id": "session-1",
		"raw_message": "what is the credit limit of that customer?",
		"selected_candidate_id": "candidate-1",
		"candidate_interpretations": [
			{
				"candidate_id": "candidate-1",
				"intent_scope": "visible_context_followup",
				"business_domain": "customer_credit",
				"requested_action": "lookup",
				"target_reference": "selected_entity",
				"candidate_route": "entity_detail",
				"candidate_capability_ids": ["accounts_receivable_read"],
				"requested_metrics": ["credit_limit_amount"],
				"requested_dimensions": ["customer"],
				"evidence_need": "needs_governed_requery",
				"authority_class": "safe_read",
			}
		],
		"conversation_action_decision": {
			"action": "execute_governed_requery",
			"response_mode": "governed_query",
			"selected_candidate_id": "candidate-1",
			"requires_routing_change": True,
			"safe_to_execute": True,
		},
		"governed_requery_plan": {
			"status": status,
			"planner_mode": planner_mode,
			"target_route": "entity_detail",
			"target_capability_ids": ["accounts_receivable_read"],
			"target_report_names": ["Customer Credit Detail"],
			"target_entity": {
				"entity_type": entity_type,
				"entity_key": "35th Street Mobile Wholesale",
				"entity_label": "35th Street Mobile Wholesale",
			},
			"requested_metrics": ["credit_limit_amount"],
			"requested_dimensions": ["customer"],
			"missing_fields": ["credit_limit"],
			"required_context": [],
			"shadow_execution_ready": True,
		},
	}


def _detail_trace_payload(*, entity_type="supplier", entity_key="Sunflower Accessories Co."):
	payload = _trace_payload(entity_type=entity_type)
	payload["raw_message"] = f"give me more information about rank 2 {entity_type}s"
	candidate = payload["candidate_interpretations"][0]
	candidate["business_domain"] = f"{entity_type}_detail"
	candidate["requested_action"] = "detail"
	candidate["requested_metrics"] = []
	candidate["requested_dimensions"] = [entity_type]
	plan = payload["governed_requery_plan"]
	plan["target_entity"] = {
		"entity_type": entity_type,
		"entity_key": entity_key,
		"entity_label": entity_key,
	}
	plan["requested_metrics"] = []
	plan["requested_dimensions"] = [entity_type]
	plan["missing_fields"] = []
	return payload


def _selected_row_tool_message():
	return {
		"role": "tool",
		"content": json.dumps(
			{
				"type": "qwen_nbu_current_artifact_answer_activation_contract",
				"resolved_rank": 2,
				"resolved_entity": {
					"entity_type": "customer",
					"entity_key": "35th Street Mobile Wholesale",
					"entity_label": "35th Street Mobile Wholesale",
					"row": {
						"rank": 2,
						"customer": "35th Street Mobile Wholesale",
						"outstanding_amount": 84837000,
						"total_due": 82527000,
						"overdue_amount": 58212000,
					},
				},
			}
		),
	}


def _ap_supplier_artifact_message():
	return {
		"role": "tool",
		"content": json.dumps(
			{
				"type": "qwen_normalized_family_artifact_contract",
				"artifact_id": "ap-aging-1",
				"title": "Accounts Payable Aging",
				"family_id": "accounts_payable_aging",
				"sections": {
					"top_suppliers": [
						{
							"rank": 1,
							"supplier": "Myanmar Tech Import Services",
							"outstanding_amount": 268298000,
							"total_due": 250568000,
							"overdue_amount": 193478000,
						},
						{
							"rank": 2,
							"supplier": "Sunflower Accessories Co.",
							"outstanding_amount": 222526500,
							"total_due": 222526500,
							"overdue_amount": 136661500,
						},
					]
				},
			}
		),
	}


def _raw_summary_table_message():
	return {
		"role": "tool",
		"content": json.dumps(
			{
				"data": [
					["Outstanding Total", "906,366,600 MMK"],
					["Total Amount Due", "878,396,600 MMK"],
				]
			}
		),
	}


class NaturalBusinessUnderstandingGovernedRequeryActivationTests(unittest.TestCase):
	def test_ready_entity_detail_requery_activation_is_generic_by_entity_policy(self):
		with patch.object(activation, "entity_detail_runtime_policy", return_value={"can_execute": True}):
			result = activation.build_nbu_governed_requery_activation(
				_trace_payload(entity_type="supplier"),
				activation_level="governed_requery",
			)

		self.assertEqual(result["activation_state"], "ready")
		self.assertEqual(result["activation_mode"], "governed_requery_entity_detail")
		self.assertEqual(result["target_entity"]["entity_type"], "supplier")
		self.assertEqual(result["requested_metrics"], ["credit_limit_amount"])
		self.assertEqual(result["blockers"], [])

	def test_ready_entity_detail_requery_accepts_contract_name_target(self):
		trace = _detail_trace_payload()
		trace["conversation_action_decision"] = {
			"action": "ask_clarification",
			"response_mode": "clarification",
			"safe_to_execute": False,
		}
		trace["governed_requery_plan"]["target_entity"] = {
			"entity_type": "supplier",
			"name": "Sunflower Accessories Co.",
		}

		with patch.object(activation, "entity_detail_runtime_policy", return_value={"can_execute": True}):
			result = activation.build_nbu_governed_requery_activation(
				trace,
				activation_level="governed_requery",
			)

		self.assertEqual(result["activation_state"], "ready")
		self.assertEqual(result["target_entity"]["entity_key"], "Sunflower Accessories Co.")
		self.assertEqual(result["target_entity"]["entity_label"], "Sunflower Accessories Co.")
		self.assertEqual(result["blockers"], [])

	def test_selected_detail_candidate_can_activate_without_shadow_plan_when_entity_is_resolved(self):
		trace = _detail_trace_payload()
		trace["conversation_action_decision"] = {
			"action": "ask_clarification",
			"response_mode": "clarification",
			"safe_to_execute": False,
		}
		trace["candidate_interpretations"][0]["target_entity"] = {
			"name": "Sunflower Accessories Co.",
			"type": "supplier",
		}
		trace["governed_requery_plan"] = {
			"status": "not_required",
			"planner_mode": "none",
			"target_entity": {},
			"required_context": ["target_entity"],
			"shadow_execution_ready": False,
		}

		with patch.object(activation, "entity_detail_runtime_policy", return_value={"can_execute": True}):
			result = activation.build_nbu_governed_requery_activation(
				trace,
				activation_level="governed_requery",
			)

		self.assertEqual(result["activation_state"], "ready")
		self.assertEqual(result["planner_mode"], "entity_detail_requery")
		self.assertEqual(result["target_entity"]["entity_type"], "supplier")
		self.assertEqual(result["target_entity"]["entity_key"], "Sunflower Accessories Co.")
		self.assertEqual(result["blockers"], [])

	def test_local_followup_plan_does_not_hijack_visible_row_identity_question(self):
		trace = _trace_payload(entity_type="supplier")
		candidate = trace["candidate_interpretations"][0]
		candidate["intent_scope"] = "context_reference"
		candidate["requested_action"] = "show"
		candidate["candidate_route"] = "local_followup"
		candidate["target_entity"] = {
			"type": "supplier",
			"name": "Sunflower Accessories Co.",
		}
		trace["governed_requery_plan"].update(
			{
				"status": "ready_shadow",
				"planner_mode": "entity_detail_requery",
				"target_route": "local_followup",
				"target_entity": {
					"type": "supplier",
					"name": "Sunflower Accessories Co.",
				},
				"shadow_execution_ready": True,
			}
		)

		with patch.object(activation, "entity_detail_runtime_policy", return_value={"can_execute": True}):
			result = activation.build_nbu_governed_requery_activation(
				trace,
				activation_level="governed_requery",
			)

		self.assertEqual(result["activation_state"], "blocked")
		self.assertIn("governed_requery_plan_not_ready", result["blockers"])

	def test_non_entity_detail_candidate_route_does_not_activate_entity_detail_plan(self):
		trace = _trace_payload(entity_type="supplier")
		candidate = trace["candidate_interpretations"][0]
		candidate["intent_scope"] = "unknown"
		candidate["requested_action"] = "show"
		candidate["candidate_route"] = "governed_kpi"
		candidate["target_entity"] = {
			"entity_type": "supplier",
			"name": "Sunflower Accessories Co.",
		}
		trace["governed_requery_plan"].update(
			{
				"status": "ready_shadow",
				"planner_mode": "entity_detail_requery",
				"target_route": "governed_kpi",
				"target_entity": {
					"entity_type": "supplier",
					"name": "Sunflower Accessories Co.",
				},
				"shadow_execution_ready": True,
			}
		)

		with patch.object(activation, "entity_detail_runtime_policy", return_value={"can_execute": True}):
			result = activation.build_nbu_governed_requery_activation(
				trace,
				activation_level="governed_requery",
			)

		self.assertEqual(result["activation_state"], "blocked")
		self.assertIn("governed_requery_plan_not_ready", result["blockers"])

	def test_fresh_query_entity_detail_plan_does_not_hijack_new_business_question(self):
		trace = _trace_payload(entity_type="supplier")
		candidate = trace["candidate_interpretations"][0]
		candidate["intent_scope"] = "fresh_query"
		candidate["requested_action"] = "show"
		candidate["candidate_route"] = "entity_detail"
		candidate["target_entity"] = {
			"entity_type": "supplier",
			"name": "Sunflower Accessories Co.",
		}
		trace["governed_requery_plan"].update(
			{
				"status": "ready_shadow",
				"planner_mode": "entity_detail_requery",
				"target_route": "entity_detail",
				"target_entity": {
					"entity_type": "supplier",
					"name": "Sunflower Accessories Co.",
				},
				"shadow_execution_ready": True,
			}
		)

		with patch.object(activation, "entity_detail_runtime_policy", return_value={"can_execute": True}):
			result = activation.build_nbu_governed_requery_activation(
				trace,
				activation_level="governed_requery",
			)

		self.assertEqual(result["activation_state"], "blocked")
		self.assertIn("governed_requery_plan_not_ready", result["blockers"])

	def test_non_entity_detail_planner_mode_remains_shadow_only(self):
		with patch.object(activation, "entity_detail_runtime_policy", return_value={"can_execute": True}):
			result = activation.build_nbu_governed_requery_activation(
				_trace_payload(planner_mode="composite_requery"),
				activation_level="governed_requery",
			)

		self.assertEqual(result["activation_state"], "blocked")
		self.assertIn("planner_mode_not_live_enabled", result["blockers"])

	def test_not_ready_plan_does_not_execute(self):
		execute_calls = []

		def execute_entity_drilldown(**kwargs):
			execute_calls.append(kwargs)
			return {"ok": True}

		with patch.object(activation, "entity_detail_runtime_policy", return_value={"can_execute": True}):
			handled, payload = activation.try_activate_nbu_governed_requery_response(
				session_doc={"name": "session-1", "messages": []},
				request_id="req-nbu-fc6",
				session_id="session-1",
				user_id="Administrator",
				raw_message="what is the credit limit of that customer?",
				nbu_trace_payload=_trace_payload(status="needs_clarification"),
				latest_grounded_turn={"grounded": True},
				interaction_contract=_InteractionContract(),
				response_policy_contract=_ResponsePolicyContract(),
				append_message=lambda session, role, content: session["messages"].append({"role": role, "content": content}),
				append_tool_payload=lambda session, payload: session["messages"].append({"role": "tool", "content": json.dumps(payload)}),
				assistant_text_payload=lambda text: text,
				save_session=lambda session, **kwargs: session.update({"saved": True}),
				execute_entity_drilldown=execute_entity_drilldown,
				direct_evidence_response=lambda **kwargs: {"answer_text": "unused"},
			)

		self.assertFalse(handled)
		self.assertIsNone(payload)
		self.assertEqual(execute_calls, [])

	def test_current_entity_detail_boundary_preempts_requery_execution(self):
		session_doc = {"name": "session-1", "messages": []}
		execute_calls = []

		def execute_entity_drilldown(**kwargs):
			execute_calls.append(kwargs)
			return {"ok": True}

		with patch.object(activation, "entity_detail_runtime_policy", return_value={"can_execute": True}):
			handled, payload = activation.try_activate_nbu_governed_requery_response(
				session_doc=session_doc,
				request_id="req-nbu-fc6",
				session_id="session-1",
				user_id="Administrator",
				raw_message="when was it received?",
				nbu_trace_payload=_trace_payload(entity_type="purchase_order"),
				current_artifact={
					"family_id": "entity_detail",
					"dimensions": {
						"entity_type": "purchase_order",
						"entity_label": "PUR-ORD-2026-00004",
						"entity_key": "PUR-ORD-2026-00004",
					},
				},
				latest_grounded_turn={"grounded": True, "family_id": "entity_detail"},
				interaction_contract=_InteractionContract(),
				response_policy_contract=_ResponsePolicyContract(),
				append_message=lambda session, role, content: session["messages"].append({"role": role, "content": content}),
				append_tool_payload=lambda session, payload: session["messages"].append({"role": "tool", "content": json.dumps(payload)}),
				assistant_text_payload=lambda text: text,
				save_session=lambda session, **kwargs: session.update({"saved": True}),
				execute_entity_drilldown=execute_entity_drilldown,
				direct_evidence_response=lambda **kwargs: {"answer_text": "unused"},
			)

		self.assertFalse(handled)
		self.assertIsNone(payload)
		self.assertEqual(execute_calls, [])
		self.assertFalse(session_doc.get("messages"))

	def test_registry_visible_entity_fallback_uses_semantic_aliases_not_phrase_case(self):
		session_doc = {"name": "session-1", "messages": [_selected_row_tool_message()]}

		def detect_keys(message, capability_id=None, dimension_or_metric=None):
			if dimension_or_metric == "metric":
				return ["credit_limit_amount"]
			return ["customer"]

		with patch.object(activation, "entity_detail_runtime_policy", return_value={"can_execute": True}), patch.object(
			activation, "detect_canonical_keys", side_effect=detect_keys
		):
			result = activation.build_nbu_registry_visible_entity_requery_activation(
				session_doc=session_doc,
				raw_message="do you know the credit limit of that customer?",
				current_artifact={},
				activation_level="governed_requery",
			)

		self.assertEqual(result["activation_state"], "ready")
		self.assertEqual(result["activation_source"], "registry_visible_entity_requery")
		self.assertEqual(result["target_entity"]["entity_key"], "35th Street Mobile Wholesale")
		self.assertEqual(result["requested_metrics"], ["credit_limit_amount"])

	def test_registry_visible_entity_fallback_defers_when_row_already_has_requested_metric(self):
		session_doc = {"name": "session-1", "messages": [_selected_row_tool_message()]}

		def detect_keys(message, capability_id=None, dimension_or_metric=None):
			if dimension_or_metric == "metric":
				return ["outstanding_amount"]
			return ["customer"]

		with patch.object(activation, "entity_detail_runtime_policy", return_value={"can_execute": True}), patch.object(
			activation, "detect_canonical_keys", side_effect=detect_keys
		):
			result = activation.build_nbu_registry_visible_entity_requery_activation(
				session_doc=session_doc,
				raw_message="what is the outstanding amount of that customer?",
				current_artifact={},
				activation_level="governed_requery",
			)

		self.assertEqual(result["activation_state"], "blocked")
		self.assertIn("requested_field_not_proven_entity_detail_requery", result["blockers"])

	def test_registry_visible_entity_requery_does_not_activate_broad_detail_without_nbu_plan(self):
		session_doc = {
			"name": "session-1",
			"messages": [
				_selected_row_tool_message(),
				_ap_supplier_artifact_message(),
				_raw_summary_table_message(),
			],
		}

		with patch.object(activation, "entity_detail_runtime_policy", return_value={"can_execute": True}):
			result = activation.build_nbu_registry_visible_entity_requery_activation(
				session_doc=session_doc,
				raw_message="give me more information about rank 2 suppliers",
				current_artifact={
					"sections": {
						"top_customers": [
							{
								"rank": 2,
								"customer": "35th Street Mobile Wholesale",
								"outstanding_amount": 84837000,
							}
						]
					}
				},
				activation_level="governed_requery",
			)

		self.assertEqual(result["activation_state"], "blocked")
		self.assertIn("requested_field_not_proven_entity_detail_requery", result["blockers"])

	def test_entity_detail_requery_executes_and_prefers_direct_evidence_answer(self):
		session_doc = {"name": "session-1", "messages": []}
		clear_calls = []

		def append_message(session, role, content):
			session["messages"].append({"role": role, "content": content})

		def append_payload(session, payload):
			session["messages"].append({"role": "tool", "content": json.dumps(payload)})

		def execute_entity_drilldown(**kwargs):
			self.assertEqual(kwargs["entity_reference"]["entity_type"], "customer")
			self.assertEqual(kwargs["entity_reference"]["entity_key"], "35th Street Mobile Wholesale")
			return {
				"ok": True,
				"answer_text": "Full customer profile fallback",
				"artifact_payload": {
					"type": "qwen_entity_detail_artifact",
					"family_id": "entity_detail",
					"dimensions": {
						"entity_type": "customer",
						"entity_key": "35th Street Mobile Wholesale",
						"entity_label": "35th Street Mobile Wholesale",
					},
					"metrics": {"credit_limit": 75000000},
				},
				"rendered_response_payload": {"type": "qwen_rendered_response", "title": "Customer Detail"},
				"grounded_turn_payload": {"grounded": True, "family_id": "entity_detail"},
				"entity_reference": kwargs["entity_reference"],
			}

		def direct_evidence_response(**kwargs):
			self.assertEqual(kwargs["artifact_payload"]["family_id"], "entity_detail")
			return {
				"answer_text": "The configured credit limit for 35th Street Mobile Wholesale is 75,000,000 MMK.",
				"evidence_request_contract_payload": {"type": "qwen_entity_detail_evidence_request_contract"},
			}

		with patch.object(activation, "entity_detail_runtime_policy", return_value={"can_execute": True}):
			handled, payload = activation.try_activate_nbu_governed_requery_response(
				session_doc=session_doc,
				request_id="req-nbu-fc6",
				session_id="session-1",
				user_id="Administrator",
				site_name="erpai_prj1",
				raw_message="what is the credit limit of that customer?",
				nbu_trace_payload=_trace_payload(),
				current_artifact={},
				latest_grounded_turn={"grounded": True, "family_id": "accounts_receivable_aging"},
				interaction_contract=_InteractionContract(),
				response_policy_contract=_ResponsePolicyContract(),
				append_message=append_message,
				append_tool_payload=append_payload,
				assistant_text_payload=lambda text: text,
				save_session=lambda session, **kwargs: session.update({"saved": True}),
				execute_entity_drilldown=execute_entity_drilldown,
				direct_evidence_response=direct_evidence_response,
				clear_pending_clarification_signal=lambda session: clear_calls.append(session["name"]),
				additional_tool_payloads=[{"type": "qwen_natural_business_understanding_trace_contract"}],
			)

		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "nbu_governed_requery_entity_detail")
		answer_texts = [row["content"] for row in session_doc["messages"] if row["role"] == "assistant"]
		self.assertEqual(answer_texts[-1], "The configured credit limit for 35th Street Mobile Wholesale is 75,000,000 MMK.")
		self.assertTrue(session_doc["saved"])
		self.assertEqual(clear_calls, ["session-1"])
		tool_payloads = [
			json.loads(row["content"])
			for row in session_doc["messages"]
			if row["role"] == "tool"
		]
		self.assertTrue(any(row.get("type") == "qwen_nbu_governed_requery_activation_contract" for row in tool_payloads))
		self.assertTrue(any(row.get("type") == "qwen_entity_detail_evidence_request_contract" for row in tool_payloads))

	def test_broad_detail_requery_prefers_rich_entity_detail_over_direct_evidence(self):
		session_doc = {"name": "session-1", "messages": []}
		direct_calls = []
		trace_payload = _detail_trace_payload()
		trace_payload["governed_requery_plan"]["requested_metrics"] = ["Outstanding", "Total Due", "Overdue (31+)"]
		trace_payload["governed_requery_plan"]["missing_fields"] = ["outstanding", "total_due", "overdue__31"]

		def append_message(session, role, content):
			session["messages"].append({"role": role, "content": content})

		def append_payload(session, payload):
			session["messages"].append({"role": "tool", "content": json.dumps(payload)})

		def execute_entity_drilldown(**kwargs):
			self.assertEqual(kwargs["entity_reference"]["entity_type"], "supplier")
			self.assertEqual(kwargs["entity_reference"]["entity_key"], "Sunflower Accessories Co.")
			return {
				"ok": True,
				"answer_text": "Narrow supplier narrative only.",
				"artifact_payload": {
					"type": "qwen_entity_detail_artifact",
					"family_id": "entity_detail",
					"dimensions": {
						"entity_type": "supplier",
						"entity_key": "Sunflower Accessories Co.",
						"entity_label": "Sunflower Accessories Co.",
					},
				},
				"rendered_response_payload": {
					"type": "qwen_rendered_response",
					"title": "Sunflower Accessories Co. Details",
					"blocks": [
						{
							"block_type": "summary_table",
							"title": "Profile",
							"columns": ["Field", "Value"],
							"rows": [["Name", "Sunflower Accessories Co."], ["Group", "Accessories Supplier"]],
						},
						{
							"block_type": "data_table",
							"title": "Recent Purchase Invoices",
							"columns": ["Invoice", "Amount (MMK)"],
							"rows": [["ACC-PINV-2026-00336", "10,420,000"]],
						},
					],
				},
				"grounded_turn_payload": {"grounded": True, "family_id": "entity_detail"},
			}

		def direct_evidence_response(**kwargs):
			direct_calls.append(kwargs)
			return {"answer_text": "Narrow AP aging row only."}

		with patch.object(activation, "entity_detail_runtime_policy", return_value={"can_execute": True}):
			handled, payload = activation.try_activate_nbu_governed_requery_response(
				session_doc=session_doc,
				request_id="req-nbu-fc6",
				session_id="session-1",
				user_id="Administrator",
				site_name="erpai_prj1",
				raw_message="give me more information about rank 2 suppliers",
				nbu_trace_payload=trace_payload,
				current_artifact={},
				latest_grounded_turn={"grounded": True, "family_id": "accounts_payable_aging"},
				interaction_contract=_InteractionContract(),
				response_policy_contract=_ResponsePolicyContract(),
				append_message=append_message,
				append_tool_payload=append_payload,
				assistant_text_payload=lambda text: text,
				save_session=lambda session, **kwargs: session.update({"saved": True}),
				execute_entity_drilldown=execute_entity_drilldown,
				direct_evidence_response=direct_evidence_response,
			)

		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "nbu_governed_requery_entity_detail")
		answer_texts = [row["content"] for row in session_doc["messages"] if row["role"] == "assistant"]
		self.assertIn("Sunflower Accessories Co. Details", answer_texts[-1])
		self.assertIn("Recent Purchase Invoices", answer_texts[-1])
		self.assertNotIn("Narrow supplier narrative only", answer_texts[-1])
		self.assertNotIn("Narrow AP aging row only", answer_texts[-1])
		self.assertEqual(direct_calls, [])

	def test_not_ready_nbu_trace_does_not_execute_registry_backed_visible_entity_requery(self):
		session_doc = {"name": "session-1", "messages": [_selected_row_tool_message()]}

		def detect_keys(message, capability_id=None, dimension_or_metric=None):
			if dimension_or_metric == "metric":
				return ["credit_limit_amount"]
			return ["customer"]

		def execute_entity_drilldown(**kwargs):
			return {
				"ok": True,
				"answer_text": "Full customer profile fallback",
				"artifact_payload": {
					"type": "qwen_entity_detail_artifact",
					"family_id": "entity_detail",
					"dimensions": {"entity_type": "customer"},
				},
				"grounded_turn_payload": {"grounded": True, "family_id": "entity_detail"},
			}

		with patch.object(activation, "entity_detail_runtime_policy", return_value={"can_execute": True}), patch.object(
			activation, "detect_canonical_keys", side_effect=detect_keys
		):
			handled, payload = activation.try_activate_nbu_governed_requery_response(
				session_doc=session_doc,
				request_id="req-nbu-fc6",
				session_id="session-1",
				user_id="Administrator",
				raw_message="what is the credit limit of that customer?",
				nbu_trace_payload=_trace_payload(status="needs_clarification"),
				current_artifact={},
				latest_grounded_turn={"grounded": True},
				interaction_contract=_InteractionContract(),
				response_policy_contract=_ResponsePolicyContract(),
				append_message=lambda session, role, content: session["messages"].append({"role": role, "content": content}),
				append_tool_payload=lambda session, payload: session["messages"].append({"role": "tool", "content": json.dumps(payload)}),
				assistant_text_payload=lambda text: text,
				save_session=lambda session, **kwargs: session.update({"saved": True}),
				execute_entity_drilldown=execute_entity_drilldown,
				direct_evidence_response=lambda **kwargs: {"answer_text": "The configured credit limit is 75,000,000 MMK."},
			)

		self.assertFalse(handled)
		self.assertIsNone(payload)
		self.assertFalse(session_doc.get("saved"))


if __name__ == "__main__":
	unittest.main()
