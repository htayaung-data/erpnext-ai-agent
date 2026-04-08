from __future__ import annotations

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
