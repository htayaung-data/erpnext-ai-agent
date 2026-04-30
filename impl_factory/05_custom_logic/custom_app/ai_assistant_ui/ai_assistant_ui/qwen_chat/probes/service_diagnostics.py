from __future__ import annotations

import datetime as dt
import json
import re
import time
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.audit_support import (
	audit_latency_summary,
	family_metrics_summary,
)


def _service_module():
	from ai_assistant_ui.qwen_chat import service as service_module

	return service_module


def _restore_conf(conf: Dict[str, Any], originals: Dict[str, Any], presence: Dict[str, bool]) -> None:
	for key, was_present in presence.items():
		if was_present:
			conf[key] = originals.get(key)
		else:
			try:
				conf.pop(key, None)
			except Exception:
				pass


def _tool_payloads_from_session_doc(session_doc, *, parse_payload) -> List[Dict[str, Any]]:
	tool_payloads: List[Dict[str, Any]] = []
	for row in session_doc.get("messages") or []:
		if str(row.role or "").strip().lower() != "tool":
			continue
		payload_obj = parse_payload(str(row.content or ""))
		if payload_obj:
			tool_payloads.append(payload_obj)
	return tool_payloads


def _request_scoped_payload(
	tool_payloads: List[Dict[str, Any]],
	payload_type: str,
	request_id: str,
	*,
	latest_tool_payload_by_type,
) -> Dict[str, Any]:
	clean_type = str(payload_type or "").strip()
	clean_request_id = str(request_id or "").strip()
	if clean_type and clean_request_id:
		for item in reversed(tool_payloads):
			if str(item.get("type") or "").strip() != clean_type:
				continue
			item_request_id = str(
				item.get("request_id")
				or item.get("trace_request_id")
				or item.get("source_request_id")
				or ""
			).strip()
			if item_request_id == clean_request_id:
				return item
	return latest_tool_payload_by_type(tool_payloads, payload_type)


def _payload_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
	if not isinstance(payload, dict):
		return {}
	return {
		"type": str(payload.get("type") or "").strip(),
		"request_id": str(payload.get("request_id") or "").strip(),
		"trace_request_id": str(payload.get("trace_request_id") or "").strip(),
		"source_request_id": str(payload.get("source_request_id") or "").strip(),
		"status": str(payload.get("status") or "").strip(),
		"recommended_boundary_decision": str(payload.get("recommended_boundary_decision") or "").strip(),
		"decision_reason": str(payload.get("decision_reason") or "").strip(),
		"resolution_source": dict(payload.get("resolution_source") or {}),
		"governed_scope_status": str(payload.get("governed_scope_status") or "").strip(),
		"execution_mode": str(payload.get("execution_mode") or "").strip(),
		"recommended_next_lane": str(payload.get("recommended_next_lane") or "").strip(),
		"target_capability_id": str(payload.get("target_capability_id") or "").strip(),
		"target_report": str(payload.get("target_report") or "").strip(),
		"mode": str(payload.get("mode") or "").strip(),
		"target_dimension": str(payload.get("target_dimension") or "").strip(),
		"target_metric": str(payload.get("target_metric") or "").strip(),
		"requested_time_scope": str(payload.get("requested_time_scope") or "").strip(),
		"target_limit": int(payload.get("target_limit") or 0),
		"source_name": str(payload.get("source_name") or "").strip(),
		"artifact_family_id": str(payload.get("artifact_family_id") or payload.get("family_id") or "").strip(),
		"title": str(payload.get("title") or "").strip(),
		"answer_text": str(payload.get("answer_text") or "").strip(),
		"family_id": str(payload.get("family_id") or "").strip(),
		"report_name": str(payload.get("report_name") or "").strip(),
		"report_family_id": str(payload.get("report_family_id") or "").strip(),
		"failure_type": str(payload.get("failure_type") or "").strip(),
		"recommended_recovery_action": str(payload.get("recommended_recovery_action") or "").strip(),
		"intent": dict(payload.get("intent") or {}),
	}


def run_phase6_reasoning_live_debug() -> Dict[str, Any]:
	service_module = _service_module()
	frappe = service_module.frappe
	flag_key = "qwen_enable_erp_business_reasoning"
	percent_key = "qwen_erp_business_reasoning_rollout_percentage"
	users_key = "qwen_erp_business_reasoning_rollout_users"
	conf = getattr(frappe, "conf", None) or {}
	originals = {
		flag_key: conf.get(flag_key),
		percent_key: conf.get(percent_key),
		users_key: conf.get(users_key),
	}
	presence = {
		flag_key: flag_key in conf,
		percent_key: percent_key in conf,
		users_key: users_key in conf,
	}
	try:
		conf[flag_key] = True
		conf[percent_key] = 0
		conf[users_key] = ["Administrator"]

		def _runner(doc) -> Dict[str, Any]:
			ok, first_payload = service_module.handle_qwen_user_message(
				session_name=doc.name,
				message=service_module.smoke_fixture_replacement_message("fresh_query_override_to_ar"),
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase 6 live reasoning debug failed: first turn did not complete.")
			session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name)
			latest_grounded_turn = service_module._latest_grounded_turn_contract(session_doc)
			latest_family_artifact = service_module._latest_normalized_family_artifact(
				session_doc,
				grounded_turn=latest_grounded_turn,
			)
			latest_assistant_payload = service_module._latest_assistant_payload(session_doc)
			request_id = "phase6-debug"
			interaction_contract = service_module.build_interaction_contract(
				request_id=request_id,
				session_id=doc.name,
				user_id="Administrator",
				site_name=str(getattr(getattr(frappe, "local", None), "site", "") or "").strip(),
				raw_message="what does this mean",
			)
			response_policy_contract = service_module.build_response_policy_contract(
				interaction_contract=interaction_contract,
			)
			activation = service_module.build_reasoning_activation_contract(
				request_id=request_id,
				session_id=doc.name,
				message="what does this mean",
				latest_grounded_turn=latest_grounded_turn,
				latest_family_artifact=latest_family_artifact,
				latest_assistant_payload=latest_assistant_payload,
				response_policy_contract=response_policy_contract.to_payload(),
			)
			semantic = service_module.interpret_reasoning_activation_semantically(
				request_id=request_id,
				session_id=doc.name,
				user_id="Administrator",
				site_name=str(getattr(getattr(frappe, "local", None), "site", "") or "").strip(),
				message="what does this mean",
				recent_messages=service_module._recent_messages(session_doc, limit=8),
				latest_grounded_turn=latest_grounded_turn,
				latest_family_artifact=latest_family_artifact,
				latest_assistant_payload=latest_assistant_payload,
				activation_contract=activation.to_payload(),
			)
			direct_execution = service_module.execute_erp_business_reasoning(
				request_id=request_id,
				session_id=doc.name,
				user_id="Administrator",
				message="what does this mean",
				recent_messages=service_module._recent_messages(session_doc, limit=10),
				activation_contract=activation.to_payload(),
				semantic_activation_result=semantic.to_payload(),
				latest_grounded_turn=latest_grounded_turn,
				latest_family_artifact=latest_family_artifact,
				latest_assistant_payload=latest_assistant_payload,
				prior_reasoning_contract=service_module._latest_reasoning_contract(session_doc),
				prior_answer_text=str(latest_assistant_payload.get("text") or "").strip(),
			)
			ok2, second_payload = service_module.handle_qwen_user_message(
				session_name=doc.name,
				message="what does this mean",
				user="Administrator",
			)
			second_payload_summary = {
				"request_id": str((second_payload or {}).get("request_id") or "").strip(),
				"mode": str((second_payload or {}).get("mode") or "").strip(),
				"family_validation_status": str((second_payload or {}).get("family_validation_status") or "").strip(),
				"semantic_validation_status": str((second_payload or {}).get("semantic_validation_status") or "").strip(),
				"agent_meta": dict(((second_payload or {}).get("agent_meta") or {})),
			}
			return {
				"ok": True,
				"rollout": service_module._erp_business_reasoning_rollout_decision(
					session_name=doc.name,
					user="Administrator",
					site_name=str(getattr(getattr(frappe, "local", None), "site", "") or "").strip(),
				),
				"first_payload": first_payload,
				"activation": activation.to_payload(),
				"semantic": semantic.to_payload(),
				"direct_execution": direct_execution.to_payload(),
				"second_ok": ok2,
				"second_payload": second_payload_summary,
				"latest_assistant_payload": service_module._latest_assistant_payload(
					frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name)
				),
			}

		return service_module._run_phase55_smoke_session("Phase 6 Live Reasoning Debug", _runner)
	finally:
		_restore_conf(conf, originals, presence)


def run_phase8c_repair_handling_debug() -> Dict[str, Any]:
	service_module = _service_module()
	frappe = service_module.frappe

	def _seed_recovery_session(doc) -> None:
		recovery_payload = service_module.build_artifact_enrichment_recovery_contract(
			request_id="phase8c-debug-recovery",
			session_id=doc.name,
			source_request_id="phase8c-debug-grounded-trace",
			source_family_id="customer_rankings",
			source_capability_id="top_customers_by_revenue",
			source_report="Top Customers by Revenue",
			failure_type="artifact_enrichment_incompatible",
			recovery_state="recoverable",
			available_recovery_actions=["keep_current_artifact", "run_alternative_governed_query", "clarify_target_output"],
			recommended_recovery_action="run_alternative_governed_query",
			preservable_scope={"company": "Mingalar Mobile Distribution Co., Ltd.", "requested_top_n": 7},
			preservable_dimensions=["customer"],
			preservable_metrics=["quantity", "revenue"],
			preservable_time_context={"from_date": "2026-02-01", "to_date": "2026-02-29"},
			alternative_capability_id="top_customers_by_quantity",
			alternative_report="Top Customers by Quantity",
			reason="Quantity requires a governed sibling query.",
			allowed_to_recover=True,
			confidence=0.91,
		).to_payload()
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "phase8c-debug-grounded-request",
			"trace_request_id": "phase8c-debug-grounded-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Top Customers by Revenue",
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"date_range": {"from_date": "2026-02-01", "to_date": "2026-02-29"},
			"filters": {"company": "Mingalar Mobile Distribution Co., Ltd."},
			"dimensions": ["customer"],
			"metrics": ["revenue"],
			"returned_schema": ["Customer", "Sales Amount"],
			"table_rows": [],
			"row_count": 7,
			"base_language": "en",
			"transform_chain": [],
			"artifact_family_id": "customer_rankings",
			"artifact_type": "normalized_family_artifact",
			"artifact_source_reports": ["Top Customers by Revenue"],
			"known_entities": [],
			"known_documents": [],
		}
		service_module._append_message(
			doc,
			"assistant",
			service_module._assistant_text_payload(
				"I can't safely add quantity to the current ranking, but I can run the governed Top Customers by Quantity report for last month."
			),
		)
		service_module._append_tool_payload(doc, grounded_turn_payload)
		service_module._append_tool_payload(doc, recovery_payload)
		service_module._save_session(doc, ignore_permissions=False)

	def _runner(doc) -> Dict[str, Any]:
		_seed_recovery_session(doc)
		fixture_id = "product_recovery_flow"
		ok, guidance_payload = service_module.handle_qwen_user_message(
			session_name=doc.name,
			message=service_module.smoke_fixture_action_message(fixture_id, "guidance"),
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Phase 8C repair debug failed on guidance turn.")
		ok, accepted_payload = service_module.handle_qwen_user_message(
			session_name=doc.name,
			message=service_module.smoke_fixture_action_message(fixture_id, "accept_governed_alternative"),
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Phase 8C repair debug failed on accepted recovery turn.")
		session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name)
		tool_payloads = service_module._session_tool_payloads(session_doc)
		return {
			"ok": True,
			"guidance_mode": str((guidance_payload or {}).get("mode") or "").strip(),
			"accepted_mode": str((accepted_payload or {}).get("mode") or "").strip(),
			"assistant_text": str(service_module._latest_assistant_payload(session_doc).get("text") or "").strip(),
			"repair_contract": service_module._latest_tool_payload_by_type(tool_payloads, "qwen_conversational_repair_intent_contract"),
			"followup_resolution": service_module._latest_tool_payload_by_type(tool_payloads, "qwen_followup_resolution_contract"),
			"compiled_audit": service_module._latest_tool_payload_by_type(tool_payloads, "qwen_compiled_execution_audit_contract"),
			"rendered_family_response": service_module._latest_tool_payload_by_type(tool_payloads, "qwen_rendered_family_response_contract"),
		}

	return service_module._run_phase55_smoke_session("Phase 8C Repair Handling Debug", _runner)


def run_phase8_recovery_execution_debug() -> Dict[str, Any]:
	service_module = _service_module()
	frappe = service_module.frappe

	def _runner(doc) -> Dict[str, Any]:
		fixture_id = "product_recovery_flow"
		fixture = service_module.require_smoke_fixture(fixture_id)
		ok, first_payload = service_module.handle_qwen_user_message(
			session_name=doc.name,
			message=str(fixture.get("initial_message") or "").strip(),
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Phase 8 recovery debug failed on initial products ranking request.")
		session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name)
		first_assistant_text = str(service_module._latest_assistant_payload(session_doc).get("text") or "").strip()
		ok, second_payload = service_module.handle_qwen_user_message(
			session_name=doc.name,
			message=service_module.smoke_fixture_action_message(fixture_id, "qty_enrichment"),
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Phase 8 recovery debug failed on quantity enrichment request.")
		session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name)
		tool_payloads = service_module._session_tool_payloads(session_doc)
		return {
			"ok": True,
			"first_mode": str((first_payload or {}).get("mode") or "").strip(),
			"first_assistant_text": first_assistant_text,
			"mode": str((second_payload or {}).get("mode") or "").strip(),
			"assistant_text": str(service_module._latest_assistant_payload(session_doc).get("text") or "").strip(),
			"recent_tool_types": [str(item.get("type") or "").strip() for item in tool_payloads[-20:]],
			"followup_resolution": service_module._latest_tool_payload_by_type(tool_payloads, "qwen_followup_resolution_contract"),
			"continuation_contract": service_module._latest_tool_payload_by_type(tool_payloads, "qwen_artifact_continuation_contract"),
			"enrichment_compatibility_contract": service_module._latest_tool_payload_by_type(tool_payloads, "qwen_artifact_enrichment_compatibility_contract"),
			"recovery_contract": service_module._latest_tool_payload_by_type(tool_payloads, "qwen_artifact_enrichment_recovery_contract"),
			"scope_decision_contract": service_module._latest_tool_payload_by_type(tool_payloads, "qwen_governed_scope_decision_contract"),
			"grounded_turn_context": service_module._latest_tool_payload_by_type(tool_payloads, "qwen_grounded_turn_context"),
			"compiled_audit": service_module._latest_tool_payload_by_type(tool_payloads, "qwen_compiled_execution_audit_contract"),
			"rendered_family_response": service_module._latest_tool_payload_by_type(tool_payloads, "qwen_rendered_family_response_contract"),
		}

	return service_module._run_phase55_smoke_session("Phase 8 Recovery Execution Debug", _runner)


def _top_ranked_name_from_markdown(text: str) -> str:
	match = re.search(r"^\|\s*1\s*\|\s*([^|]+?)\s*\|", str(text or ""), flags=re.MULTILINE)
	if not match:
		return ""
	return str(match.group(1) or "").strip()


def run_phase4_compiled_rollout_smoke() -> Dict[str, Any]:
	service_module = _service_module()
	frappe = service_module.frappe
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
	original_flag = None
	original_percent = None
	original_users = None
	had_original = False
	had_percent = False
	had_users = False
	try:
		try:
			original_flag = (getattr(frappe, "conf", None) or {}).get(flag_key)
			original_percent = (getattr(frappe, "conf", None) or {}).get(percent_key)
			original_users = (getattr(frappe, "conf", None) or {}).get(users_key)
			had_original = flag_key in (getattr(frappe, "conf", None) or {})
			had_percent = percent_key in (getattr(frappe, "conf", None) or {})
			had_users = users_key in (getattr(frappe, "conf", None) or {})
		except Exception:
			original_flag = None
			original_percent = None
			original_users = None
			had_original = False
			had_percent = False
			had_users = False
		(getattr(frappe, "conf", None) or {})[flag_key] = True
		(getattr(frappe, "conf", None) or {})[percent_key] = 100
		(getattr(frappe, "conf", None) or {})[users_key] = []

		doc = frappe.new_doc(service_module.QWEN_SESSION_DOCTYPE)
		doc.title = "Phase4 Compiled Rollout Smoke"
		doc.insert(ignore_permissions=False)
		try:
			ok, payload = service_module.handle_qwen_user_message(
				session_name=doc.name,
				message="How much payable amount do we have as of now",
				user="Administrator",
			)
			session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name)
			tool_payloads = _tool_payloads_from_session_doc(session_doc, parse_payload=service_module._parse_payload)
			type_names = [str(item.get("type") or "").strip() for item in tool_payloads if isinstance(item, dict)]
			has_compiled_audit = "qwen_compiled_execution_audit_contract" in type_names
			has_semantic_validation = "qwen_semantic_validation_outcome" in type_names
			has_grounded_turn = "qwen_grounded_turn_context" in type_names
			has_rollout_fallback = "qwen_compiled_rollout_fallback" in type_names
			if not ok or not isinstance(payload, dict):
				raise RuntimeError("Compiled rollout smoke failed: live service did not return an ok payload.")
			mode = str(payload.get("mode") or "").strip()
			if mode == "compiled_first_turn":
				if str(payload.get("semantic_validation_status") or "").strip() != "pass":
					raise RuntimeError("Compiled rollout smoke failed: semantic validation did not pass.")
				if not has_compiled_audit or not has_semantic_validation or not has_grounded_turn:
					raise RuntimeError("Compiled rollout smoke failed: required compiled-path audit artifacts were not persisted.")
			elif mode == "legacy_runtime_rollout_fallback":
				if not has_compiled_audit or not has_rollout_fallback:
					raise RuntimeError("Compiled rollout smoke failed: rollout fallback was not persisted auditably.")
			else:
				raise RuntimeError("Compiled rollout smoke failed: live service did not use compiled mode or audited fallback mode.")
			return {
				"ok": ok,
				"payload": payload,
				"session_name": doc.name,
				"persisted_tool_payload_types": type_names,
			}
		finally:
			frappe.delete_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
	finally:
		_restore_conf(
			getattr(frappe, "conf", None) or {},
			{flag_key: original_flag, percent_key: original_percent, users_key: original_users},
			{flag_key: had_original, percent_key: had_percent, users_key: had_users},
		)


def run_phase3_3c_customer_master_lookup_smoke() -> Dict[str, Any]:
	service_module = _service_module()
	frappe = service_module.frappe
	doc = frappe.new_doc(service_module.QWEN_SESSION_DOCTYPE)
	doc.title = "Phase3.3C Customer Master Lookup Smoke"
	doc.insert(ignore_permissions=False)
	try:
		turns: List[Dict[str, Any]] = []
		for prompt in (
			"give me some customer names",
			"do u have customer name similar to Ko Nay Lin Mobile",
			"tell me details about Ko Nay Lin Mobile Center",
		):
			ok, payload = service_module.handle_qwen_user_message(
				session_name=doc.name,
				message=prompt,
				user="Administrator",
			)
			session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name)
			assistant_payload = service_module._latest_assistant_payload(session_doc) or {}
			answer_text = str(assistant_payload.get("text") or assistant_payload.get("answer_text") or "").strip()
			turns.append(
				{
					"prompt": prompt,
					"ok": bool(ok),
					"payload": payload if isinstance(payload, dict) else {},
					"assistant_payload": _payload_summary(assistant_payload),
					"answer_text": answer_text,
				}
			)
		if "Which area would you like me to analyze?" in turns[0]["answer_text"]:
			raise RuntimeError("Customer master lookup smoke failed: generic customer names still fell into area clarification.")
		if "Ko Nay Lin Mobile Center" not in turns[1]["answer_text"]:
			raise RuntimeError("Customer master lookup smoke failed: near-match customer lookup did not resolve the governed customer name.")
		if "Ko Nay Lin Mobile Center Details" not in turns[2]["answer_text"]:
			raise RuntimeError("Customer master lookup smoke failed: exact detail request did not enter governed customer detail.")
		return {
			"ok": True,
			"session_name": doc.name,
			"turns": turns,
		}
	finally:
		frappe.delete_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)


def run_phase4_compiled_rollout_governance_selftests() -> Dict[str, Any]:
	service_module = _service_module()
	conf = getattr(service_module.frappe, "conf", None) or {}
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
	originals = {
		flag_key: conf.get(flag_key),
		percent_key: conf.get(percent_key),
		users_key: conf.get(users_key),
	}
	presence = {
		flag_key: flag_key in conf,
		percent_key: percent_key in conf,
		users_key: users_key in conf,
	}
	try:
		conf[flag_key] = False
		conf[percent_key] = 100
		conf[users_key] = []
		disabled = service_module._compiled_first_turn_rollout_decision(
			session_name="phase4-rollout-disabled",
			user="Administrator",
			site_name="erpai_prj1",
		)
		if bool(disabled.get("enabled")):
			raise RuntimeError("Compiled rollout governance selftest failed: master-disabled rollout still enabled.")

		conf[flag_key] = True
		conf[percent_key] = 0
		conf[users_key] = []
		zero_percent = service_module._compiled_first_turn_rollout_decision(
			session_name="phase4-rollout-zero",
			user="User A",
			site_name="erpai_prj1",
		)
		if bool(zero_percent.get("enabled")):
			raise RuntimeError("Compiled rollout governance selftest failed: zero-percent rollout still enabled.")

		conf[flag_key] = True
		conf[percent_key] = 0
		conf[users_key] = ["Administrator"]
		allow_user = service_module._compiled_first_turn_rollout_decision(
			session_name="phase4-rollout-allow",
			user="Administrator",
			site_name="erpai_prj1",
		)
		if not bool(allow_user.get("enabled")) or str(allow_user.get("reason") or "") != "allow_user":
			raise RuntimeError("Compiled rollout governance selftest failed: allowlisted user was not enabled.")

		conf[flag_key] = True
		conf[percent_key] = 50
		conf[users_key] = []
		first = service_module._compiled_first_turn_rollout_decision(
			session_name="phase4-rollout-stable",
			user="User B",
			site_name="erpai_prj1",
		)
		second = service_module._compiled_first_turn_rollout_decision(
			session_name="phase4-rollout-stable",
			user="User B",
			site_name="erpai_prj1",
		)
		if float(first.get("rollout_bucket") or -1.0) != float(second.get("rollout_bucket") or -2.0):
			raise RuntimeError("Compiled rollout governance selftest failed: rollout bucket was not deterministic.")
		return {
			"ok": True,
			"disabled": disabled,
			"zero_percent": zero_percent,
			"allow_user": allow_user,
			"stable_bucket": first,
		}
	finally:
		_restore_conf(conf, originals, presence)


def summarize_compiled_first_turn_audits(
	limit_sessions: int = 50,
	limit_audits: int = 200,
	session_names: List[str] | None = None,
) -> Dict[str, Any]:
	service_module = _service_module()
	frappe = service_module.frappe
	requested_session_names = [
		str(name or "").strip()
		for name in (session_names or [])
		if str(name or "").strip()
	]
	if requested_session_names:
		session_rows = [{"name": name, "modified": ""} for name in requested_session_names]
	else:
		session_rows = frappe.get_all(
			service_module.QWEN_SESSION_DOCTYPE,
			fields=["name", "modified"],
			order_by="modified desc",
			limit_page_length=max(1, int(limit_sessions or 50)),
		)
	records: List[Dict[str, Any]] = []
	rollout_fallbacks: List[Dict[str, Any]] = []
	for row in session_rows:
		session_name = str((row or {}).get("name") or "").strip()
		if not session_name:
			continue
		try:
			session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, session_name)
		except Exception:
			continue
		for message in reversed(list(session_doc.get("messages") or [])):
			if str(message.role or "").strip().lower() != "tool":
				continue
			payload = service_module._parse_payload(str(message.content or ""))
			payload_type = str(payload.get("type") or "").strip()
			if payload_type == "qwen_compiled_rollout_fallback":
				rollout_fallbacks.append(
					{
						"session_name": session_name,
						"request_id": str(payload.get("request_id") or "").strip(),
						"reason": str(payload.get("reason") or "").strip(),
					}
				)
				continue
			if payload_type != "qwen_compiled_execution_audit_contract":
				continue
			records.append(
				{
					"session_name": session_name,
					"session_modified": str((row or {}).get("modified") or ""),
					"request_id": str(payload.get("request_id") or "").strip(),
					"compiler_decision": str(payload.get("compiler_decision") or "").strip(),
					"selected_report": str(payload.get("selected_report") or "").strip(),
					"governed_family_id": str(payload.get("governed_family_id") or "").strip(),
					"composite_plan_id": str(payload.get("composite_plan_id") or "").strip(),
					"capability_id": str(payload.get("capability_id") or "").strip(),
					"proposal_cache_hit": bool(payload.get("proposal_cache_hit")),
					"proposal_shared_inflight_hit": bool(payload.get("proposal_shared_inflight_hit")),
					"runtime_ok": bool(payload.get("runtime_ok")),
					"grounded_validation_status": str(payload.get("grounded_validation_status") or "").strip(),
					"family_validation_status": str(payload.get("family_validation_status") or "").strip(),
					"semantic_validation_status": str(payload.get("semantic_validation_status") or "").strip(),
					"proposal_generation_latency_ms": int(max(0, payload.get("proposal_generation_latency_ms") or 0)),
					"compilation_latency_ms": int(max(0, payload.get("compilation_latency_ms") or 0)),
					"runtime_execution_latency_ms": int(max(0, payload.get("runtime_execution_latency_ms") or 0)),
					"semantic_validation_latency_ms": int(max(0, payload.get("semantic_validation_latency_ms") or 0)),
					"total_pipeline_latency_ms": int(max(0, payload.get("total_pipeline_latency_ms") or 0)),
					"tool_count": int(max(0, payload.get("tool_count") or 0)),
				}
			)
			if len(records) >= max(1, int(limit_audits or 200)):
				break
		if len(records) >= max(1, int(limit_audits or 200)):
			break

	def count_values(key: str) -> Dict[str, int]:
		out: Dict[str, int] = {}
		for record in records:
			value = str(record.get(key) or "").strip() or "unknown"
			out[value] = int(out.get(value, 0)) + 1
		return out

	total = len(records)
	runtime_ok_count = sum(1 for record in records if bool(record.get("runtime_ok")))
	proposal_cache_hit_count = sum(1 for record in records if bool(record.get("proposal_cache_hit")))
	proposal_shared_inflight_hit_count = sum(
		1 for record in records if bool(record.get("proposal_shared_inflight_hit"))
	)
	rollout_fallback_count = len(rollout_fallbacks)
	return {
		"sessions_scanned": len(session_rows),
		"audits_found": total,
		"rollout_status": service_module.get_compiled_first_turn_rollout_status(),
		"runtime_ok_rate": 0.0 if total == 0 else round(runtime_ok_count / float(total), 4),
		"proposal_cache_hit_rate": 0.0 if total == 0 else round(proposal_cache_hit_count / float(total), 4),
		"proposal_shared_inflight_hit_rate": 0.0
		if total == 0
		else round(proposal_shared_inflight_hit_count / float(total), 4),
		"rollout_fallback_count": rollout_fallback_count,
		"rollout_fallback_rate": 0.0 if total == 0 else round(rollout_fallback_count / float(total), 4),
		"compiler_decision_counts": count_values("compiler_decision"),
		"semantic_validation_status_counts": count_values("semantic_validation_status"),
		"grounded_validation_status_counts": count_values("grounded_validation_status"),
		"proposal_generation_latency": audit_latency_summary(
			[int(record.get("proposal_generation_latency_ms") or 0) for record in records]
		),
		"compilation_latency": audit_latency_summary(
			[int(record.get("compilation_latency_ms") or 0) for record in records]
		),
		"runtime_execution_latency": audit_latency_summary(
			[int(record.get("runtime_execution_latency_ms") or 0) for record in records]
		),
		"semantic_validation_latency": audit_latency_summary(
			[int(record.get("semantic_validation_latency_ms") or 0) for record in records]
		),
		"total_pipeline_latency": audit_latency_summary(
			[int(record.get("total_pipeline_latency_ms") or 0) for record in records]
		),
		"average_tool_count": 0.0
		if total == 0
		else round(sum(int(record.get("tool_count") or 0) for record in records) / float(total), 2),
		"family_metrics": family_metrics_summary(records, rollout_fallbacks),
		"recent_audits": records[:10],
		"recent_rollout_fallbacks": rollout_fallbacks[:10],
	}


def run_phase4_compiled_rollout_monitoring_smoke() -> Dict[str, Any]:
	service_module = _service_module()
	frappe = service_module.frappe
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
	original_flag = None
	original_percent = None
	original_users = None
	had_original = False
	had_percent = False
	had_users = False
	try:
		try:
			original_flag = (getattr(frappe, "conf", None) or {}).get(flag_key)
			original_percent = (getattr(frappe, "conf", None) or {}).get(percent_key)
			original_users = (getattr(frappe, "conf", None) or {}).get(users_key)
			had_original = flag_key in (getattr(frappe, "conf", None) or {})
			had_percent = percent_key in (getattr(frappe, "conf", None) or {})
			had_users = users_key in (getattr(frappe, "conf", None) or {})
		except Exception:
			original_flag = None
			original_percent = None
			original_users = None
			had_original = False
			had_percent = False
			had_users = False
		(getattr(frappe, "conf", None) or {})[flag_key] = True
		(getattr(frappe, "conf", None) or {})[percent_key] = 100
		(getattr(frappe, "conf", None) or {})[users_key] = []

		doc = frappe.new_doc(service_module.QWEN_SESSION_DOCTYPE)
		doc.title = "Phase4 Compiled Rollout Monitoring Smoke"
		doc.insert(ignore_permissions=False)
		try:
			ok, payload = service_module.handle_qwen_user_message(
				session_name=doc.name,
				message="How much payable amount do we have as of now",
				user="Administrator",
			)
			summary = summarize_compiled_first_turn_audits(
				limit_sessions=10,
				limit_audits=50,
				session_names=[doc.name],
			)
			if not ok or not isinstance(payload, dict):
				raise RuntimeError("Compiled rollout monitoring smoke failed: live service did not return an ok payload.")
			if int(summary.get("audits_found") or 0) < 1:
				raise RuntimeError("Compiled rollout monitoring smoke failed: no compiled audits were found.")
			decision_counts = summary.get("compiler_decision_counts") if isinstance(summary.get("compiler_decision_counts"), dict) else {}
			semantic_counts = (
				summary.get("semantic_validation_status_counts")
				if isinstance(summary.get("semantic_validation_status_counts"), dict)
				else {}
			)
			mode = str(payload.get("mode") or "").strip()
			if mode == "compiled_first_turn":
				if int(decision_counts.get("execute") or 0) < 1:
					raise RuntimeError("Compiled rollout monitoring smoke failed: execute decisions were not observed.")
				if int(semantic_counts.get("pass") or 0) < 1:
					raise RuntimeError("Compiled rollout monitoring smoke failed: semantic pass outcomes were not observed.")
			elif mode == "legacy_runtime_rollout_fallback":
				if int(summary.get("rollout_fallback_count") or 0) < 1:
					raise RuntimeError("Compiled rollout monitoring smoke failed: rollout fallback was not observed in summary.")
			else:
				raise RuntimeError("Compiled rollout monitoring smoke failed: unexpected live mode was returned.")
			return {
				"ok": ok,
				"payload": payload,
				"summary": summary,
				"session_name": doc.name,
			}
		finally:
			frappe.delete_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
	finally:
		_restore_conf(
			getattr(frappe, "conf", None) or {},
			{flag_key: original_flag, percent_key: original_percent, users_key: original_users},
			{flag_key: had_original, percent_key: had_percent, users_key: had_users},
		)


def run_first_turn_regression_suite(messages: List[str] | None = None) -> Dict[str, Any]:
	service_module = _service_module()
	frappe = service_module.frappe
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
	default_messages = [
		"How much payable amount do we have as of now",
		"Top 5 customers by revenue",
		"Show monthly sales trend",
		"Analyze AR / AP amount and evaluate the company health",
		"Show me P & L statement, and analyze it",
		"which products are performing well last month",
	]
	test_messages = [
		str(item or "").strip()
		for item in (messages or default_messages)
		if str(item or "").strip()
	]
	conf = getattr(frappe, "conf", None) or {}
	originals = {
		flag_key: conf.get(flag_key),
		percent_key: conf.get(percent_key),
		users_key: conf.get(users_key),
	}
	presence = {
		flag_key: flag_key in conf,
		percent_key: percent_key in conf,
		users_key: users_key in conf,
	}
	try:
		conf[flag_key] = True
		conf[percent_key] = 100
		conf[users_key] = []
		results: List[Dict[str, Any]] = []
		for message in test_messages:
			doc = frappe.new_doc(service_module.QWEN_SESSION_DOCTYPE)
			doc.title = "First Turn Regression Suite"
			doc.insert(ignore_permissions=False)
			try:
				start = time.perf_counter()
				ok, payload = service_module.handle_qwen_user_message(
					session_name=doc.name,
					message=message,
					user="Administrator",
				)
				elapsed_ms = int((time.perf_counter() - start) * 1000)
				session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name)
				assistant_payload = service_module._latest_assistant_payload(session_doc)
				answer_text = str(assistant_payload.get("text") or "").strip()
				tool_payloads = _tool_payloads_from_session_doc(session_doc, parse_payload=service_module._parse_payload)
				type_names = [str(item.get("type") or "").strip() for item in tool_payloads if isinstance(item, dict)]
				compiled_audit = next(
					(
						item
						for item in reversed(tool_payloads)
						if str(item.get("type") or "").strip() == "qwen_compiled_execution_audit_contract"
					),
					{},
				)
				semantic_validation = next(
					(
						item
						for item in reversed(tool_payloads)
						if str(item.get("type") or "").strip() == "qwen_semantic_validation_outcome"
					),
					{},
				)
				fallback_payload = next(
					(
						item
						for item in reversed(tool_payloads)
						if str(item.get("type") or "").strip() == "qwen_compiled_rollout_fallback"
					),
					{},
				)
				results.append(
					{
						"message": message,
						"ok": bool(ok),
						"mode": str((payload or {}).get("mode") or "").strip(),
						"compiled_rollout_fallback_reason": str(
							(payload or {}).get("compiled_rollout_fallback_reason") or ""
						).strip(),
						"answer_text": answer_text,
						"elapsed_ms": elapsed_ms,
						"semantic_validation_status": str(
							(semantic_validation or {}).get("status") or ""
						).strip(),
						"compiler_decision": str((compiled_audit or {}).get("compiler_decision") or "").strip(),
						"selected_report": str((compiled_audit or {}).get("selected_report") or "").strip(),
						"proposal_generation_latency_ms": int(
							max(0, (compiled_audit or {}).get("proposal_generation_latency_ms") or 0)
						),
						"runtime_execution_latency_ms": int(
							max(0, (compiled_audit or {}).get("runtime_execution_latency_ms") or 0)
						),
						"total_pipeline_latency_ms": int(
							max(0, (compiled_audit or {}).get("total_pipeline_latency_ms") or 0)
						),
						"persisted_tool_payload_types": type_names,
						"fallback_payload": fallback_payload,
					}
				)
			finally:
				frappe.delete_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
		return {
			"ok": True,
			"results": results,
			"rollout_status": service_module.get_compiled_first_turn_rollout_status(),
		}
	finally:
		_restore_conf(conf, originals, presence)


def run_same_session_fresh_query_regression_smoke(messages: List[str] | None = None) -> Dict[str, Any]:
	service_module = _service_module()
	frappe = service_module.frappe
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
	default_messages = [
		"How much payable amount do we have as of now",
		"Top 5 customers by revenue",
		"Show monthly sales trend",
		"Show me P & L statement",
		"Which products are performing well last month",
		"Analyze AR / AP amount and evaluate the company health",
		"Show current inventory value by warehouse",
	]
	test_messages = [
		str(item or "").strip()
		for item in (messages or default_messages)
		if str(item or "").strip()
	]
	conf = getattr(frappe, "conf", None) or {}
	originals = {
		flag_key: conf.get(flag_key),
		percent_key: conf.get(percent_key),
		users_key: conf.get(users_key),
	}
	presence = {
		flag_key: flag_key in conf,
		percent_key: percent_key in conf,
		users_key: users_key in conf,
	}
	try:
		conf[flag_key] = True
		conf[percent_key] = 100
		conf[users_key] = []
		doc = frappe.new_doc(service_module.QWEN_SESSION_DOCTYPE)
		doc.title = "Same Session Fresh Query Regression"
		doc.insert(ignore_permissions=False)
		results: List[Dict[str, Any]] = []
		try:
			for message in test_messages:
				start = time.perf_counter()
				ok, payload = service_module.handle_qwen_user_message(
					session_name=doc.name,
					message=message,
					user="Administrator",
				)
				elapsed_ms = int((time.perf_counter() - start) * 1000)
				payload = payload if isinstance(payload, dict) else {}
				mode = str(payload.get("mode") or "").strip()
				semantic_status = str(payload.get("semantic_validation_status") or "").strip()
				results.append(
					{
						"message": message,
						"ok": bool(ok),
						"mode": mode,
						"semantic_validation_status": semantic_status,
						"elapsed_ms": elapsed_ms,
					}
				)
				if not bool(ok):
					raise RuntimeError(
						f"Same-session fresh-query smoke failed: service returned not-ok for `{message}`."
					)
				if mode != "compiled_first_turn":
					raise RuntimeError(
						f"Same-session fresh-query smoke failed: `{message}` did not use compiled first-turn mode."
					)
				if semantic_status and semantic_status != "pass":
					raise RuntimeError(
						f"Same-session fresh-query smoke failed: `{message}` semantic status was `{semantic_status}`."
					)
			return {
				"ok": True,
				"session_name": doc.name,
				"results": results,
				"rollout_status": service_module.get_compiled_first_turn_rollout_status(),
			}
		finally:
			frappe.delete_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
	finally:
		_restore_conf(conf, originals, presence)


def run_phase_d2a_transaction_listing_today_requery_smoke() -> Dict[str, Any]:
	service_module = _service_module()
	frappe = service_module.frappe
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
	today_iso = str(dt.date.today())
	scenarios = [
		{
			"scenario_id": "sales_invoice_today",
			"first_message": "show me sales invoices",
			"second_message": "show me sales invoices today",
			"expected_source_name": "Sales Invoice List",
		},
		{
			"scenario_id": "purchase_order_today",
			"first_message": "show me purchase orders",
			"second_message": "show me purchase orders today",
			"expected_source_name": "Purchase Order List",
		},
		{
			"scenario_id": "payment_entry_today",
			"first_message": "show me payment entries",
			"second_message": "show me payment entries today",
			"expected_source_name": "Payment Entry List",
		},
	]
	conf = getattr(frappe, "conf", None) or {}
	originals = {
		flag_key: conf.get(flag_key),
		percent_key: conf.get(percent_key),
		users_key: conf.get(users_key),
	}
	presence = {
		flag_key: flag_key in conf,
		percent_key: percent_key in conf,
		users_key: users_key in conf,
	}
	try:
		conf[flag_key] = True
		conf[percent_key] = 100
		conf[users_key] = []
		results: List[Dict[str, Any]] = []
		for scenario in scenarios:
			doc = frappe.new_doc(service_module.QWEN_SESSION_DOCTYPE)
			doc.title = f"Phase D2A {scenario['scenario_id']}"
			doc.insert(ignore_permissions=False)
			try:
				first_message = str(scenario.get("first_message") or "").strip()
				second_message = str(scenario.get("second_message") or "").strip()
				expected_source_name = str(scenario.get("expected_source_name") or "").strip()

				first_ok, first_payload = service_module.handle_qwen_user_message(
					session_name=doc.name,
					message=first_message,
					user="Administrator",
				)
				if not first_ok or str((first_payload or {}).get("mode") or "").strip() != "compiled_first_turn":
					raise RuntimeError(
						f"Phase D2A transaction-listing smoke failed: `{first_message}` did not execute through compiled first-turn mode."
					)
				session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name)
				tool_payloads = _tool_payloads_from_session_doc(session_doc, parse_payload=service_module._parse_payload)
				first_request_id = str((first_payload or {}).get("request_id") or "").strip()
				first_grounded = _request_scoped_payload(
					tool_payloads,
					"qwen_grounded_turn_context",
					first_request_id,
					latest_tool_payload_by_type=service_module._latest_tool_payload_by_type,
				)
				first_trace_request_id = str(first_grounded.get("trace_request_id") or first_grounded.get("request_id") or "").strip()
				first_source_name = str(first_grounded.get("source_name") or "").strip()
				first_scope = {
					"date_range": dict(first_grounded.get("date_range") or {}),
					"filters": dict(first_grounded.get("filters") or {}),
				}
				if not first_trace_request_id or not first_source_name:
					raise RuntimeError(
						f"Phase D2A transaction-listing smoke failed: `{first_message}` did not persist a grounded trace."
					)
				if first_source_name != expected_source_name:
					raise RuntimeError(
						f"Phase D2A transaction-listing smoke failed: `{first_message}` used unexpected source `{first_source_name}`."
					)

				second_ok, second_payload = service_module.handle_qwen_user_message(
					session_name=doc.name,
					message=second_message,
					user="Administrator",
				)
				if not second_ok or str((second_payload or {}).get("mode") or "").strip() != "compiled_first_turn":
					raise RuntimeError(
						f"Phase D2A transaction-listing smoke failed: `{second_message}` did not execute through compiled first-turn mode."
					)
				session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name)
				tool_payloads = _tool_payloads_from_session_doc(session_doc, parse_payload=service_module._parse_payload)
				second_request_id = str((second_payload or {}).get("request_id") or "").strip()
				second_grounded = _request_scoped_payload(
					tool_payloads,
					"qwen_grounded_turn_context",
					second_request_id,
					latest_tool_payload_by_type=service_module._latest_tool_payload_by_type,
				)
				second_trace_request_id = str(second_grounded.get("trace_request_id") or second_grounded.get("request_id") or "").strip()
				second_source_name = str(second_grounded.get("source_name") or "").strip()
				second_scope = {
					"date_range": dict(second_grounded.get("date_range") or {}),
					"filters": dict(second_grounded.get("filters") or {}),
				}
				if not second_trace_request_id or not second_source_name:
					raise RuntimeError(
						f"Phase D2A transaction-listing smoke failed: `{second_message}` did not persist a grounded trace."
					)
				if second_trace_request_id == first_trace_request_id:
					raise RuntimeError(
						f"Phase D2A transaction-listing smoke failed: `{second_message}` reused the earlier grounded trace instead of issuing a fresh query."
					)
				if second_source_name != first_source_name:
					raise RuntimeError(
						f"Phase D2A transaction-listing smoke failed: `{second_message}` changed source families unexpectedly from `{first_source_name}` to `{second_source_name}`."
					)
				if second_source_name != expected_source_name:
					raise RuntimeError(
						f"Phase D2A transaction-listing smoke failed: `{second_message}` used unexpected source `{second_source_name}`."
					)
				if first_scope == second_scope:
					raise RuntimeError(
						f"Phase D2A transaction-listing smoke failed: `{second_message}` did not update the grounded time scope."
					)
				second_scope_text = json.dumps(second_scope, sort_keys=True, default=str)
				if today_iso not in second_scope_text:
					raise RuntimeError(
						f"Phase D2A transaction-listing smoke failed: `{second_message}` did not carry today's date into grounded scope."
					)

				results.append(
					{
						"scenario_id": str(scenario.get("scenario_id") or "").strip(),
						"first_message": first_message,
						"second_message": second_message,
						"first_mode": str((first_payload or {}).get("mode") or "").strip(),
						"second_mode": str((second_payload or {}).get("mode") or "").strip(),
						"source_name": second_source_name,
						"expected_source_name": expected_source_name,
						"first_trace_request_id": first_trace_request_id,
						"second_trace_request_id": second_trace_request_id,
						"first_scope": first_scope,
						"second_scope": second_scope,
						"row_count": int(max(0, second_grounded.get("row_count") or 0)),
					}
				)
			finally:
				frappe.delete_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
		return {
			"ok": True,
			"results": results,
			"today": today_iso,
			"rollout_status": service_module.get_compiled_first_turn_rollout_status(),
		}
	finally:
		_restore_conf(conf, originals, presence)


def run_phase_d2c_transaction_listing_base_scope_reset_smoke() -> Dict[str, Any]:
	service_module = _service_module()
	frappe = service_module.frappe
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
	conf = getattr(frappe, "conf", None) or {}
	originals = {
		flag_key: conf.get(flag_key),
		percent_key: conf.get(percent_key),
		users_key: conf.get(users_key),
	}
	presence = {
		flag_key: flag_key in conf,
		percent_key: percent_key in conf,
		users_key: users_key in conf,
	}
	try:
		conf[flag_key] = True
		conf[percent_key] = 100
		conf[users_key] = []
		doc = frappe.new_doc(service_module.QWEN_SESSION_DOCTYPE)
		doc.title = "Phase D2C payment_entry_base_reset"
		doc.insert(ignore_permissions=False)
		try:
			first_ok, first_payload = service_module.handle_qwen_user_message(
				session_name=doc.name,
				message="show me payment entries last month",
				user="Administrator",
			)
			if not first_ok or str((first_payload or {}).get("mode") or "").strip() != "compiled_first_turn":
				raise RuntimeError("Phase D2C smoke failed: scoped payment-entry first turn did not execute through compiled first-turn mode.")
			session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name)
			tool_payloads = _tool_payloads_from_session_doc(session_doc, parse_payload=service_module._parse_payload)
			first_request_id = str((first_payload or {}).get("request_id") or "").strip()
			first_grounded = _request_scoped_payload(
				tool_payloads,
				"qwen_grounded_turn_context",
				first_request_id,
				latest_tool_payload_by_type=service_module._latest_tool_payload_by_type,
			)
			first_scope = dict(first_grounded.get("date_range") or {})
			if str(first_grounded.get("source_name") or "").strip() != "Payment Entry List":
				raise RuntimeError("Phase D2C smoke failed: first payment-entry request used an unexpected source report.")
			if not str(first_scope.get("from_date") or "").strip() or not str(first_scope.get("to_date") or "").strip():
				raise RuntimeError("Phase D2C smoke failed: first payment-entry request did not carry the expected scoped date window.")

			second_ok, second_payload = service_module.handle_qwen_user_message(
				session_name=doc.name,
				message="show me payment entries",
				user="Administrator",
			)
			if not second_ok or str((second_payload or {}).get("mode") or "").strip() != "compiled_first_turn":
				raise RuntimeError("Phase D2C smoke failed: bare payment-entry re-ask did not execute through compiled first-turn mode.")
			session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name)
			tool_payloads = _tool_payloads_from_session_doc(session_doc, parse_payload=service_module._parse_payload)
			second_request_id = str((second_payload or {}).get("request_id") or "").strip()
			second_grounded = _request_scoped_payload(
				tool_payloads,
				"qwen_grounded_turn_context",
				second_request_id,
				latest_tool_payload_by_type=service_module._latest_tool_payload_by_type,
			)
			second_scope = dict(second_grounded.get("date_range") or {})
			if str(second_grounded.get("source_name") or "").strip() != "Payment Entry List":
				raise RuntimeError("Phase D2C smoke failed: bare payment-entry re-ask changed source reports unexpectedly.")
			if first_scope == second_scope:
				raise RuntimeError("Phase D2C smoke failed: bare payment-entry re-ask preserved the prior scoped date window.")
			if any(str(second_scope.get(key) or "").strip() for key in ("from_date", "to_date", "report_date")):
				raise RuntimeError("Phase D2C smoke failed: bare payment-entry re-ask still carried an explicit scoped date window.")
			return {
				"ok": True,
				"session_name": doc.name,
				"first_scope": first_scope,
				"second_scope": second_scope,
				"first_mode": str((first_payload or {}).get("mode") or "").strip(),
				"second_mode": str((second_payload or {}).get("mode") or "").strip(),
			}
		finally:
			frappe.delete_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
	finally:
		_restore_conf(conf, originals, presence)



def run_phase1_1_delivery_note_invoice_switch_debug() -> Dict[str, Any]:
	service_module = _service_module()
	frappe = service_module.frappe

	def _runner(doc) -> Dict[str, Any]:
		frappe.db.commit()
		frappe.clear_cache()
		doc.reload()
		steps = [
			"show me the last 5 delivery notes",
			"show me the last 5 delivery notes from last month",
			"show me delivery notes with status Completed",
			"Show me last 7 sale invoices",
		]
		results: List[Dict[str, Any]] = []
		for message in steps:
			ok, payload = service_module.handle_qwen_user_message(
				session_name=doc.name,
				message=message,
				user="Administrator",
			)
			if not ok:
				raise RuntimeError(
					f"Phase1.1 delivery/invoice switch debug failed: request {message!r} did not complete."
				)
			frappe.db.commit()
			frappe.clear_cache()
			session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name)
			tool_payloads = service_module._session_tool_payloads(session_doc)
			request_id = str((payload or {}).get("request_id") or "").strip()
			results.append(
				{
					"message": message,
					"payload": {
						"request_id": request_id,
						"mode": str((payload or {}).get("mode") or "").strip(),
						"family_validation_status": str((payload or {}).get("family_validation_status") or "").strip(),
						"semantic_validation_status": str((payload or {}).get("semantic_validation_status") or "").strip(),
						"agent_meta": dict(((payload or {}).get("agent_meta") or {})),
					},
					"assistant_text": str(service_module._latest_assistant_payload(session_doc).get("text") or "").strip(),
					"followup_boundary": _payload_summary(
						_request_scoped_payload(
							tool_payloads,
							"qwen_followup_boundary_contract",
							request_id,
							latest_tool_payload_by_type=service_module._latest_tool_payload_by_type,
						)
					),
					"semantic_followup": _payload_summary(
						_request_scoped_payload(
							tool_payloads,
							"qwen_semantic_followup_interpretation",
							request_id,
							latest_tool_payload_by_type=service_module._latest_tool_payload_by_type,
						)
					),
					"scope_decision": _payload_summary(
						_request_scoped_payload(
							tool_payloads,
							"qwen_governed_scope_decision_contract",
							request_id,
							latest_tool_payload_by_type=service_module._latest_tool_payload_by_type,
						)
					),
					"followup_resolution": _payload_summary(
						_request_scoped_payload(
							tool_payloads,
							"qwen_followup_resolution_contract",
							request_id,
							latest_tool_payload_by_type=service_module._latest_tool_payload_by_type,
						)
					),
					"compiled_audit": _payload_summary(
						_request_scoped_payload(
							tool_payloads,
							"qwen_compiled_execution_audit_contract",
							request_id,
							latest_tool_payload_by_type=service_module._latest_tool_payload_by_type,
						)
					),
					"grounded_turn": _payload_summary(
						_request_scoped_payload(
							tool_payloads,
							"qwen_grounded_turn_context",
							request_id,
							latest_tool_payload_by_type=service_module._latest_tool_payload_by_type,
						)
					),
					"rendered_family_response": _payload_summary(
						_request_scoped_payload(
							tool_payloads,
							"qwen_rendered_family_response_contract",
							request_id,
							latest_tool_payload_by_type=service_module._latest_tool_payload_by_type,
						)
					),
					"normalized_family_artifact": _payload_summary(
						_request_scoped_payload(
							tool_payloads,
							"qwen_normalized_family_artifact_contract",
							request_id,
							latest_tool_payload_by_type=service_module._latest_tool_payload_by_type,
						)
					),
				}
			)
		return {
			"ok": True,
			"steps": results,
		}

	return service_module._run_phase55_smoke_session("Phase 1.1 Delivery Note Invoice Switch Debug", _runner)


def run_phase1_1_invoice_detail_delivery_trend_debug() -> Dict[str, Any]:
	service_module = _service_module()
	frappe = service_module.frappe

	def _runner(doc) -> Dict[str, Any]:
		frappe.db.commit()
		frappe.clear_cache()
		doc.reload()
		steps = [
			"Show me last 7 sale invoices",
			"tell me more about ACC-SINV-2026-00194",
			"those items are already delivered to the customer?",
			"give me last year Delivery trend",
		]
		results: List[Dict[str, Any]] = []
		for message in steps:
			ok, payload = service_module.handle_qwen_user_message(
				session_name=doc.name,
				message=message,
				user="Administrator",
			)
			if not ok:
				raise RuntimeError(
					f"Phase1.1 invoice detail -> delivery trend debug failed: request {message!r} did not complete."
				)
			frappe.db.commit()
			frappe.clear_cache()
			session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name)
			tool_payloads = service_module._session_tool_payloads(session_doc)
			request_id = str((payload or {}).get("request_id") or "").strip()
			results.append(
				{
					"message": message,
					"payload": {
						"request_id": request_id,
						"mode": str((payload or {}).get("mode") or "").strip(),
						"family_validation_status": str((payload or {}).get("family_validation_status") or "").strip(),
						"semantic_validation_status": str((payload or {}).get("semantic_validation_status") or "").strip(),
						"agent_meta": dict(((payload or {}).get("agent_meta") or {})),
					},
					"assistant_text": str(service_module._latest_assistant_payload(session_doc).get("text") or "").strip(),
					"followup_boundary": _payload_summary(
						_request_scoped_payload(
							tool_payloads,
							"qwen_followup_boundary_contract",
							request_id,
							latest_tool_payload_by_type=service_module._latest_tool_payload_by_type,
						)
					),
					"scope_decision": _payload_summary(
						_request_scoped_payload(
							tool_payloads,
							"qwen_governed_scope_decision_contract",
							request_id,
							latest_tool_payload_by_type=service_module._latest_tool_payload_by_type,
						)
					),
					"followup_resolution": _payload_summary(
						_request_scoped_payload(
							tool_payloads,
							"qwen_followup_resolution_contract",
							request_id,
							latest_tool_payload_by_type=service_module._latest_tool_payload_by_type,
						)
					),
					"compiled_audit": _payload_summary(
						_request_scoped_payload(
							tool_payloads,
							"qwen_compiled_execution_audit_contract",
							request_id,
							latest_tool_payload_by_type=service_module._latest_tool_payload_by_type,
						)
					),
					"grounded_turn": _payload_summary(
						_request_scoped_payload(
							tool_payloads,
							"qwen_grounded_turn_context",
							request_id,
							latest_tool_payload_by_type=service_module._latest_tool_payload_by_type,
						)
					),
					"recovery_contract": _payload_summary(
						_request_scoped_payload(
							tool_payloads,
							"qwen_artifact_enrichment_recovery_contract",
							request_id,
							latest_tool_payload_by_type=service_module._latest_tool_payload_by_type,
						)
					),
					"rendered_family_response": _payload_summary(
						_request_scoped_payload(
							tool_payloads,
							"qwen_rendered_family_response_contract",
							request_id,
							latest_tool_payload_by_type=service_module._latest_tool_payload_by_type,
						)
					),
					"normalized_family_artifact": _payload_summary(
						_request_scoped_payload(
							tool_payloads,
							"qwen_normalized_family_artifact_contract",
							request_id,
							latest_tool_payload_by_type=service_module._latest_tool_payload_by_type,
						)
					),
				}
			)
		return {
			"ok": True,
			"steps": results,
		}

	return service_module._run_phase55_smoke_session("Phase 1.1 Invoice Detail Delivery Trend Debug", _runner)


def run_phase3_2_projection_followup_debug() -> Dict[str, Any]:
	service_module = _service_module()
	frappe = service_module.frappe
	doc = frappe.new_doc(service_module.QWEN_SESSION_DOCTYPE)
	doc.title = "Phase3.2 Projection Followup Debug"
	doc.insert(ignore_permissions=False)
	try:
		ok, first_payload = service_module.handle_qwen_user_message(
			session_name=doc.name,
			message="show top 5 customers by revenue for sales orders last month",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Phase3.2 projection debug failed on first composite turn.")
		session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name)
		latest_grounded_turn = service_module._latest_grounded_turn_contract(session_doc)
		latest_family_artifact = service_module._latest_normalized_family_artifact(session_doc)
		latest_assistant_payload = service_module._latest_assistant_payload(session_doc)
		recent_messages = service_module._recent_messages(session_doc, limit=6)
		request_id = f"phase3-2-projection-debug-{int(time.time() * 1000)}"
		defer_runtime_value_frontdoor, semantic_result = service_module._artifact_local_refinement_should_defer_runtime_frontdoor(
			request_id=request_id,
			session_id=doc.name,
			user_id="Administrator",
			site_name=str(getattr(frappe.local, "site", "") or ""),
			message="give me customer name and AOV column only",
			recent_messages=recent_messages,
			latest_grounded_turn=latest_grounded_turn,
			latest_family_artifact=latest_family_artifact,
			latest_assistant_payload=latest_assistant_payload,
		)
		followup_resolution_payload: Dict[str, Any] = {}
		continuation_payload: Dict[str, Any] = {}
		requery_upgrade_payload: Dict[str, Any] = {}
		if str(getattr(semantic_result, "status", "") or "").strip() == "accepted" and getattr(semantic_result, "intent", None) is not None:
			followup_resolution = service_module.build_followup_resolution(
				request_id=request_id,
				message="give me customer name and AOV column only",
				latest_grounded_turn_available=True,
				latest_grounded_turn=latest_grounded_turn,
				semantic_intent=semantic_result.intent,
				allow_heuristic_fallback=False,
				degraded_reason="",
			)
			followup_resolution_payload = followup_resolution.to_payload()
			continuation_contract = service_module.build_artifact_continuation_contract(
				request_id=request_id,
				followup_resolution=followup_resolution,
				grounded_turn=latest_grounded_turn,
				artifact_payload=latest_family_artifact,
			)
			if continuation_contract is not None:
				continuation_payload = continuation_contract.to_payload()
				followup_resolution = service_module._authoritative_continuation_resolution(
					request_id=request_id,
					followup_resolution=followup_resolution,
					continuation_contract=continuation_contract,
					artifact_payload=latest_family_artifact,
					grounded_turn=latest_grounded_turn,
				)
				followup_resolution_payload = followup_resolution.to_payload()
				requery_upgrade, _ = service_module._requery_resolution_for_unsupported_local_columns(
					request_id=request_id,
					followup_resolution=followup_resolution,
					artifact_payload=latest_family_artifact,
					grounded_turn=latest_grounded_turn,
					continuation_contract=continuation_contract,
				)
				if requery_upgrade is not None:
					requery_upgrade_payload = requery_upgrade.to_payload()
		frontdoor_semantic_result, frontdoor_contract, _frontdoor_render_result, frontdoor_answer = service_module.evaluate_frontdoor_lane(
			request_id=request_id,
			session_id=doc.name,
			user_id="Administrator",
			site_name=str(getattr(frappe.local, "site", "") or ""),
			message="give me customer name and AOV column only",
			recent_messages=recent_messages,
			grounded_context_available=True,
			latest_grounded_turn=latest_grounded_turn,
			latest_recovery_contract_available=False,
			pre_frontdoor_reasoning_semantic_result=None,
			defer_runtime_value_frontdoor=defer_runtime_value_frontdoor,
			post_clarification_stop_acknowledgement=False,
		)
		ok, second_payload = service_module.handle_qwen_user_message(
			session_name=doc.name,
			message="give me customer name and AOV column only",
			user="Administrator",
		)
		session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name)
		tool_payloads = _tool_payloads_from_session_doc(session_doc, parse_payload=service_module._parse_payload)
		return {
			"ok": bool(ok),
			"session_name": doc.name,
			"first_payload": dict(first_payload or {}),
			"pre_frontdoor": {
				"defer_runtime_value_frontdoor": defer_runtime_value_frontdoor,
				"semantic_result": semantic_result.to_payload() if hasattr(semantic_result, "to_payload") else {},
				"followup_resolution": followup_resolution_payload,
				"continuation_contract": continuation_payload,
				"requery_upgrade": requery_upgrade_payload,
				"latest_grounded_turn": _payload_summary(latest_grounded_turn),
				"latest_family_artifact": _payload_summary(latest_family_artifact),
			},
			"frontdoor_preview": {
				"semantic_result": frontdoor_semantic_result.to_payload() if hasattr(frontdoor_semantic_result, "to_payload") else {},
				"frontdoor_contract": frontdoor_contract.to_payload() if hasattr(frontdoor_contract, "to_payload") else {},
				"frontdoor_answer": str(frontdoor_answer or "").strip(),
			},
			"actual_second_payload": dict(second_payload or {}),
			"actual_second_answer": str(service_module._latest_assistant_payload(session_doc).get("text") or "").strip(),
			"tool_payload_type_tail": [
				str(item.get("type") or "").strip()
				for item in tool_payloads[-12:]
				if isinstance(item, dict)
			],
		}
	finally:
		frappe.delete_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)


def run_phase3_3_ranking_projection_continuation_regression_debug() -> Dict[str, Any]:
	service_module = _service_module()
	frappe = service_module.frappe
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
	doc = frappe.new_doc(service_module.QWEN_SESSION_DOCTYPE)
	doc.title = "Phase3.3 Ranking Projection Continuation Regression Debug"
	doc.insert(ignore_permissions=False)
	try:
		conf = getattr(frappe, "conf", None) or {}
		originals = {
			flag_key: conf.get(flag_key),
			percent_key: conf.get(percent_key),
			users_key: conf.get(users_key),
		}
		presence = {
			flag_key: flag_key in conf,
			percent_key: percent_key in conf,
			users_key: users_key in conf,
		}
		try:
			conf[flag_key] = True
			conf[percent_key] = 100
			conf[users_key] = []
			frappe.db.commit()
			frappe.clear_cache()

			customer_message = "show top 5 customers by revenue for sales orders last month"
			ok_customer, customer_payload = service_module.handle_qwen_user_message(
				session_name=doc.name,
				message=customer_message,
				user="Administrator",
			)
			if not ok_customer:
				raise RuntimeError("Phase3.3 regression failed on the customer ranking base turn.")
			session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name)
			customer_text = str(service_module._latest_assistant_payload(session_doc).get("text") or "").strip()
			if "| Rank | Customer |" not in customer_text or "Revenue" not in customer_text:
				raise RuntimeError("Phase3.3 regression failed: base customer ranking did not render the minimal customer and revenue table.")
			if "Average Order Value" in customer_text or "Quantity" in customer_text:
				raise RuntimeError("Phase3.3 regression failed: base customer ranking exposed extra metrics without an explicit request.")
			top_customer_name = _top_ranked_name_from_markdown(customer_text)

			projection_message = "give me Customer, Revenue and AOV columns only"
			ok_projection, projection_payload = service_module.handle_qwen_user_message(
				session_name=doc.name,
				message=projection_message,
				user="Administrator",
			)
			if not ok_projection:
				raise RuntimeError("Phase3.3 regression failed on the projection refinement turn.")
			session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name)
			projection_text = str(service_module._latest_assistant_payload(session_doc).get("text") or "").strip()
			if "| Rank | Customer | Revenue | Average Order Value |" not in projection_text:
				raise RuntimeError("Phase3.3 regression failed: projection refinement did not keep only the requested Customer, Revenue, and AOV columns.")
			if "Summary" in projection_text:
				raise RuntimeError("Phase3.3 regression failed: explicit projection refinement still leaked the summary block.")
			if "Quantity" in projection_text:
				raise RuntimeError("Phase3.3 regression failed: explicit projection refinement still leaked Quantity.")

			time_message = "I mean last year, not last month"
			ok_time, time_payload = service_module.handle_qwen_user_message(
				session_name=doc.name,
				message=time_message,
				user="Administrator",
			)
			if not ok_time:
				raise RuntimeError("Phase3.3 regression failed on the time correction turn.")
			session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name)
			time_text = str(service_module._latest_assistant_payload(session_doc).get("text") or "").strip()
			tool_payloads = _tool_payloads_from_session_doc(session_doc, parse_payload=service_module._parse_payload)
			time_request_id = str((time_payload or {}).get("request_id") or "").strip()
			time_followup_resolution = _request_scoped_payload(
				tool_payloads,
				"qwen_followup_resolution",
				time_request_id,
				latest_tool_payload_by_type=service_module._latest_tool_payload_by_type,
			)
			time_artifact = _request_scoped_payload(
				tool_payloads,
				"qwen_normalized_family_artifact_contract",
				time_request_id,
				latest_tool_payload_by_type=service_module._latest_tool_payload_by_type,
			)
			time_period = time_artifact.get("period") if isinstance(time_artifact.get("period"), dict) else {}
			if str(time_followup_resolution.get("requested_time_scope") or "").strip() != "last_year":
				raise RuntimeError("Phase3.3 regression failed: time correction was not normalized to the governed last_year scope.")
			if str(time_period.get("time_scope") or time_period.get("requested_time_scope") or "").strip() != "last_year":
				raise RuntimeError("Phase3.3 regression failed: the refreshed artifact did not carry the corrected last_year period.")
			if "2026-03-01 to 2026-03-31" in time_text:
				raise RuntimeError("Phase3.3 regression failed: time correction still reused the prior March month window.")
			if "Quantity" in time_text:
				raise RuntimeError("Phase3.3 regression failed: time correction reintroduced Quantity even though the projection was explicitly narrowed.")
			if "Average Order Value" not in time_text:
				raise RuntimeError("Phase3.3 regression failed: time correction did not preserve the selected AOV projection.")

			product_message = "show top 5 products by revenue last month"
			ok_product, product_payload = service_module.handle_qwen_user_message(
				session_name=doc.name,
				message=product_message,
				user="Administrator",
			)
			if not ok_product:
				raise RuntimeError("Phase3.3 regression failed on the product subject-switch turn.")
			session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name)
			product_text = str(service_module._latest_assistant_payload(session_doc).get("text") or "").strip()
			if "| Rank | Customer |" in product_text:
				raise RuntimeError("Phase3.3 regression failed: product ranking still reused the prior customer artifact.")
			if top_customer_name and top_customer_name in product_text:
				raise RuntimeError("Phase3.3 regression failed: product ranking leaked the previous top customer into the new subject.")
			if "| Rank | Product |" not in product_text and "| Rank | Item |" not in product_text:
				raise RuntimeError("Phase3.3 regression failed: product subject switch did not render a product/item ranking table.")

			return {
				"ok": True,
				"customer_turn": {
					"mode": str((customer_payload or {}).get("mode") or "").strip(),
					"engine": str((customer_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
					"top_name": top_customer_name,
				},
				"projection_turn": {
					"mode": str((projection_payload or {}).get("mode") or "").strip(),
					"engine": str((projection_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
				},
				"time_turn": {
					"mode": str((time_payload or {}).get("mode") or "").strip(),
					"engine": str((time_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
					"requested_time_scope": str(time_followup_resolution.get("requested_time_scope") or "").strip(),
					"artifact_time_scope": str(time_period.get("time_scope") or time_period.get("requested_time_scope") or "").strip(),
				},
				"product_turn": {
					"mode": str((product_payload or {}).get("mode") or "").strip(),
					"engine": str((product_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
					"top_name": _top_ranked_name_from_markdown(product_text),
				},
			}
		finally:
			_restore_conf(conf, originals, presence)
			frappe.db.commit()
			frappe.clear_cache()
	finally:
		frappe.delete_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)


def run_phase3_3_product_quantity_projection_regression_debug() -> Dict[str, Any]:
	service_module = _service_module()
	frappe = service_module.frappe
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
	conf = getattr(frappe, "conf", None) or {}
	originals = {
		flag_key: conf.get(flag_key),
		percent_key: conf.get(percent_key),
		users_key: conf.get(users_key),
	}
	presence = {
		flag_key: flag_key in conf,
		percent_key: percent_key in conf,
		users_key: users_key in conf,
	}
	base_doc = frappe.new_doc(service_module.QWEN_SESSION_DOCTYPE)
	base_doc.title = "Phase3.3 Product Quantity Projection Regression Debug"
	base_doc.insert(ignore_permissions=False)
	direct_doc = frappe.new_doc(service_module.QWEN_SESSION_DOCTYPE)
	direct_doc.title = "Phase3.3 Product Quantity Direct Regression Debug"
	direct_doc.insert(ignore_permissions=False)
	try:
		try:
			conf[flag_key] = True
			conf[percent_key] = 100
			conf[users_key] = []
			frappe.db.commit()
			frappe.clear_cache()

			base_headers = {
				"| Rank | Product | Revenue |",
				"| Rank | Item | Revenue |",
				"| Rank | Product | Sales Amount |",
				"| Rank | Item | Sales Amount |",
				"| Rank | Product | Selling Amount |",
				"| Rank | Item | Selling Amount |",
			}
			qty_headers = {
				"| Rank | Product | Revenue | Quantity |",
				"| Rank | Product | Revenue (MMK) | Quantity |",
				"| Rank | Item | Revenue | Quantity |",
				"| Rank | Item | Revenue (MMK) | Quantity |",
				"| Rank | Product | Sales Amount | Quantity |",
				"| Rank | Item | Sales Amount | Quantity |",
				"| Rank | Product | Selling Amount | Quantity |",
				"| Rank | Item | Selling Amount | Quantity |",
				"| Rank | Product | Revenue | Qty |",
				"| Rank | Product | Revenue (MMK) | Qty |",
				"| Rank | Item | Revenue | Qty |",
				"| Rank | Item | Revenue (MMK) | Qty |",
				"| Rank | Product | Sales Amount | Qty |",
				"| Rank | Item | Sales Amount | Qty |",
				"| Rank | Product | Selling Amount | Qty |",
				"| Rank | Item | Selling Amount | Qty |",
			}
			failure_markers = {
				"can't answer it safely",
				"cannot safely add quantity",
				"governed requery instead of local reshaping",
				"current recommended recovery path",
				"run_alternative_governed_query",
			}

			base_message = "show top 5 products by revenue last month"
			ok_base, base_payload = service_module.handle_qwen_user_message(
				session_name=base_doc.name,
				message=base_message,
				user="Administrator",
			)
			if not ok_base:
				raise RuntimeError("Phase3.3 product regression failed on the base product ranking turn.")
			session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, base_doc.name)
			base_text = str(service_module._latest_assistant_payload(session_doc).get("text") or "").strip()
			if not any(header in base_text for header in base_headers):
				raise RuntimeError("Phase3.3 product regression failed: base product ranking did not render the minimal product and primary metric table.")
			if "| Code |" in base_text:
				raise RuntimeError("Phase3.3 product regression failed: base product ranking still exposed the legacy Code column.")
			if "Quantity" in base_text or "Qty" in base_text:
				raise RuntimeError("Phase3.3 product regression failed: base product ranking exposed quantity without an explicit request.")
			if any(marker in base_text.lower() for marker in {"key highlight", "led all products", "total monthly sales amount"}):
				raise RuntimeError("Phase3.3 product regression failed: base product ranking still used the legacy narrative template instead of the table-first response.")
			top_product_name = _top_ranked_name_from_markdown(base_text)

			followup_message = "include Qty column in the above table"
			ok_followup, followup_payload = service_module.handle_qwen_user_message(
				session_name=base_doc.name,
				message=followup_message,
				user="Administrator",
			)
			if not ok_followup:
				raise RuntimeError("Phase3.3 product regression failed on the product quantity follow-up turn.")
			session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, base_doc.name)
			followup_text = str(service_module._latest_assistant_payload(session_doc).get("text") or "").strip()
			if any(marker in followup_text.lower() for marker in failure_markers):
				raise RuntimeError("Phase3.3 product regression failed: product quantity follow-up still hit the governed boundary fallback instead of the approved composite continuation path.")
			if not any(header in followup_text for header in qty_headers):
				raise RuntimeError("Phase3.3 product regression failed: product quantity follow-up did not render the requested Product, Revenue, and Quantity projection.")
			if "| Code |" in followup_text:
				raise RuntimeError("Phase3.3 product regression failed: product quantity follow-up reintroduced the legacy Code column.")
			if "Summary" in followup_text:
				raise RuntimeError("Phase3.3 product regression failed: product quantity follow-up leaked the summary block.")
			if top_product_name and top_product_name not in followup_text:
				raise RuntimeError("Phase3.3 product regression failed: product quantity follow-up did not preserve the ranked product scope.")

			direct_message = "show top 5 products by revenue last month, show together with Qty column"
			ok_direct, direct_payload = service_module.handle_qwen_user_message(
				session_name=direct_doc.name,
				message=direct_message,
				user="Administrator",
			)
			if not ok_direct:
				raise RuntimeError("Phase3.3 product regression failed on the direct product quantity turn.")
			session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, direct_doc.name)
			direct_text = str(service_module._latest_assistant_payload(session_doc).get("text") or "").strip()
			if any(marker in direct_text.lower() for marker in failure_markers):
				raise RuntimeError("Phase3.3 product regression failed: direct product quantity request still hit the governed boundary fallback instead of the approved composite frontdoor path.")
			if not any(header in direct_text for header in qty_headers):
				raise RuntimeError("Phase3.3 product regression failed: direct product quantity request did not render the requested Product, Revenue, and Quantity table.")
			if "| Code |" in direct_text:
				raise RuntimeError("Phase3.3 product regression failed: direct product quantity request exposed the legacy Code column.")
			if "Summary" in direct_text:
				raise RuntimeError("Phase3.3 product regression failed: direct product quantity request leaked the summary block.")

			return {
				"ok": True,
				"base_turn": {
					"mode": str((base_payload or {}).get("mode") or "").strip(),
					"engine": str((base_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
					"top_name": top_product_name,
				},
				"followup_turn": {
					"mode": str((followup_payload or {}).get("mode") or "").strip(),
					"engine": str((followup_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
				},
				"direct_turn": {
					"mode": str((direct_payload or {}).get("mode") or "").strip(),
					"engine": str((direct_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
					"top_name": _top_ranked_name_from_markdown(direct_text),
				},
			}
		finally:
			_restore_conf(conf, originals, presence)
			frappe.db.commit()
			frappe.clear_cache()
	finally:
		frappe.delete_doc(service_module.QWEN_SESSION_DOCTYPE, base_doc.name, ignore_permissions=False)
		frappe.delete_doc(service_module.QWEN_SESSION_DOCTYPE, direct_doc.name, ignore_permissions=False)


def inspect_phase3_3_product_quantity_projection_debug() -> Dict[str, Any]:
	service_module = _service_module()
	frappe = service_module.frappe
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
	conf = getattr(frappe, "conf", None) or {}
	originals = {
		flag_key: conf.get(flag_key),
		percent_key: conf.get(percent_key),
		users_key: conf.get(users_key),
	}
	presence = {
		flag_key: flag_key in conf,
		percent_key: percent_key in conf,
		users_key: users_key in conf,
	}
	base_doc = frappe.new_doc(service_module.QWEN_SESSION_DOCTYPE)
	base_doc.title = "Phase3.3 Product Quantity Inspection"
	base_doc.insert(ignore_permissions=False)
	direct_doc = frappe.new_doc(service_module.QWEN_SESSION_DOCTYPE)
	direct_doc.title = "Phase3.3 Product Quantity Direct Inspection"
	direct_doc.insert(ignore_permissions=False)
	try:
		try:
			conf[flag_key] = True
			conf[percent_key] = 100
			conf[users_key] = []
			frappe.db.commit()
			frappe.clear_cache()

			ok_base, base_payload = service_module.handle_qwen_user_message(
				session_name=base_doc.name,
				message="show top 5 products by revenue last month",
				user="Administrator",
			)
			session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, base_doc.name)
			base_text = str(service_module._latest_assistant_payload(session_doc).get("text") or "").strip()

			ok_followup, followup_payload = service_module.handle_qwen_user_message(
				session_name=base_doc.name,
				message="include Qty column in the above table",
				user="Administrator",
			)
			session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, base_doc.name)
			followup_text = str(service_module._latest_assistant_payload(session_doc).get("text") or "").strip()

			ok_direct, direct_payload = service_module.handle_qwen_user_message(
				session_name=direct_doc.name,
				message="show top 5 products by revenue last month, show together with Qty column",
				user="Administrator",
			)
			session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, direct_doc.name)
			direct_text = str(service_module._latest_assistant_payload(session_doc).get("text") or "").strip()

			return {
				"ok": True,
				"base": {
					"ok": bool(ok_base),
					"mode": str((base_payload or {}).get("mode") or "").strip(),
					"engine": str((base_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
					"text": base_text,
				},
				"followup": {
					"ok": bool(ok_followup),
					"mode": str((followup_payload or {}).get("mode") or "").strip(),
					"engine": str((followup_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
					"text": followup_text,
				},
				"direct": {
					"ok": bool(ok_direct),
					"mode": str((direct_payload or {}).get("mode") or "").strip(),
					"engine": str((direct_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
					"text": direct_text,
				},
			}
		finally:
			_restore_conf(conf, originals, presence)
			frappe.db.commit()
			frappe.clear_cache()
	finally:
		frappe.delete_doc(service_module.QWEN_SESSION_DOCTYPE, base_doc.name, ignore_permissions=False)
		frappe.delete_doc(service_module.QWEN_SESSION_DOCTYPE, direct_doc.name, ignore_permissions=False)


def run_phase3_2_subject_switch_regression_debug() -> Dict[str, Any]:
	service_module = _service_module()
	frappe = service_module.frappe
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
	doc = frappe.new_doc(service_module.QWEN_SESSION_DOCTYPE)
	doc.title = "Phase3.2 Subject Switch Regression Debug"
	doc.insert(ignore_permissions=False)
	try:
		conf = getattr(frappe, "conf", None) or {}
		originals = {
			flag_key: conf.get(flag_key),
			percent_key: conf.get(percent_key),
			users_key: conf.get(users_key),
		}
		presence = {
			flag_key: flag_key in conf,
			percent_key: percent_key in conf,
			users_key: users_key in conf,
		}
		try:
			conf[flag_key] = True
			conf[percent_key] = 100
			conf[users_key] = []
			frappe.db.commit()
			frappe.clear_cache()

			customer_message = "show top 5 customers by revenue for sales orders last month"
			ok_customer, customer_payload = service_module.handle_qwen_user_message(
				session_name=doc.name,
				message=customer_message,
				user="Administrator",
			)
			if not ok_customer:
				raise RuntimeError("Subject-switch regression failed on the customer composite turn.")
			session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name)
			customer_text = str(service_module._latest_assistant_payload(session_doc).get("text") or "").strip()
			if "| Rank | Customer |" not in customer_text or "Revenue" not in customer_text:
				raise RuntimeError("Subject-switch regression failed: customer ranking did not render the minimal customer/revenue table.")
			if "Average Order Value" in customer_text or "Quantity" in customer_text:
				raise RuntimeError("Subject-switch regression failed: customer ranking exposed extra metrics without an explicit request.")
			top_customer_name = _top_ranked_name_from_markdown(customer_text)

			generic_product_message = "show top 5 products by revenue last month"
			ok_generic_product, generic_product_payload = service_module.handle_qwen_user_message(
				session_name=doc.name,
				message=generic_product_message,
				user="Administrator",
			)
			if not ok_generic_product:
				raise RuntimeError("Subject-switch regression failed on the generic product ranking turn.")
			session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name)
			generic_product_text = str(service_module._latest_assistant_payload(session_doc).get("text") or "").strip()
			if "| Rank | Customer |" in generic_product_text:
				raise RuntimeError("Subject-switch regression failed: generic product ranking reused the prior customer artifact.")
			if top_customer_name and top_customer_name in generic_product_text:
				raise RuntimeError("Subject-switch regression failed: generic product ranking leaked the prior top customer into the new answer.")

			explicit_product_message = "show top 5 products by revenue for sales orders last month"
			ok_explicit_product, explicit_product_payload = service_module.handle_qwen_user_message(
				session_name=doc.name,
				message=explicit_product_message,
				user="Administrator",
			)
			if not ok_explicit_product:
				raise RuntimeError("Subject-switch regression failed on the explicit product composite turn.")
			session_doc = frappe.get_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name)
			explicit_product_text = str(service_module._latest_assistant_payload(session_doc).get("text") or "").strip()
			if "| Rank | Product |" not in explicit_product_text or "Revenue" not in explicit_product_text:
				raise RuntimeError("Subject-switch regression failed: explicit product composite did not render the product ranking table.")
			top_product_name = _top_ranked_name_from_markdown(explicit_product_text)
			if top_product_name and top_product_name not in generic_product_text:
				raise RuntimeError("Subject-switch regression failed: generic product ranking did not align with the later explicit product ranking scope.")

			return {
				"ok": True,
				"customer_turn": {
					"mode": str((customer_payload or {}).get("mode") or "").strip(),
					"engine": str((customer_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
					"top_name": top_customer_name,
				},
				"generic_product_turn": {
					"mode": str((generic_product_payload or {}).get("mode") or "").strip(),
					"engine": str((generic_product_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
					"top_name": _top_ranked_name_from_markdown(generic_product_text),
				},
				"explicit_product_turn": {
					"mode": str((explicit_product_payload or {}).get("mode") or "").strip(),
					"engine": str((explicit_product_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
					"top_name": top_product_name,
				},
			}
		finally:
			_restore_conf(conf, originals, presence)
			frappe.db.commit()
			frappe.clear_cache()
	finally:
		frappe.delete_doc(service_module.QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
