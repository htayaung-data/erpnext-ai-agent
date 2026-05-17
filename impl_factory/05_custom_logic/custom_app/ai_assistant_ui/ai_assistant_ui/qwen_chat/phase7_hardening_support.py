from __future__ import annotations

import time
from typing import Any, Callable, Dict

from ai_assistant_ui.qwen_chat.smoke_fixtures import (
	require_smoke_fixture,
	smoke_fixture_replacement_message,
)


def _latest_boundary_payload(session_doc, *, session_tool_payloads, latest_tool_payload_by_type) -> Dict[str, Any]:
	tool_payloads = session_tool_payloads(session_doc)
	return latest_tool_payload_by_type(tool_payloads, "qwen_knowledge_boundary_contract")


def _stabilize_boundary_smoke_visibility(
	*,
	frappe_module,
	session_doctype: str,
	session_name: str,
	latest_assistant_payload,
	latest_grounded_turn_contract=None,
	attempts: int = 3,
	delay_seconds: float = 0.05,
) -> None:
	for attempt in range(max(1, int(attempts))):
		frappe_module.db.commit()
		frappe_module.clear_cache()
		session_doc = frappe_module.get_doc(session_doctype, session_name)
		assistant_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
		grounded_ready = True
		if latest_grounded_turn_contract is not None:
			try:
				grounded_ready = bool((latest_grounded_turn_contract(session_doc) or {}).get("grounded"))
			except Exception:
				grounded_ready = False
		if assistant_text and grounded_ready:
			return
		if attempt + 1 < max(1, int(attempts)):
			time.sleep(max(0.0, float(delay_seconds)))


def _run_uncovered_domain_boundary_turn(
	*,
	frappe_module,
	session_doctype: str,
	session_name: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
	message: str,
	user: str = "Administrator",
	attempts: int = 3,
	delay_seconds: float = 0.05,
):
	last_payload: Dict[str, Any] = {}
	last_boundary_payload: Dict[str, Any] = {}
	last_session_doc = None
	for attempt in range(max(1, int(attempts))):
		ok, payload = handle_qwen_user_message(
			session_name=session_name,
			message=message,
			user=user,
		)
		last_payload = dict(payload or {}) if isinstance(payload, dict) else {}
		frappe_module.db.commit()
		frappe_module.clear_cache()
		last_session_doc = frappe_module.get_doc(session_doctype, session_name)
		last_boundary_payload = latest_tool_payload_by_type(
			session_tool_payloads(last_session_doc),
			"qwen_knowledge_boundary_contract",
		)
		if ok and str(last_boundary_payload.get("knowledge_coverage_state") or "").strip() == "valid_erp_domain_uncovered":
			return True, last_payload, last_session_doc, last_boundary_payload
		if attempt + 1 < max(1, int(attempts)):
			time.sleep(max(0.0, float(delay_seconds)))
	return False, last_payload, last_session_doc, last_boundary_payload


def run_live_boundary_orchestration_smoke(
	*,
	run_phase55_smoke_session: Callable[..., Dict[str, Any]],
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
) -> Dict[str, Any]:
	def _frontdoor_runner(doc) -> Dict[str, Any]:
		ok, frontdoor_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="hello",
			user="Administrator",
		)
		if not ok or str((frontdoor_payload or {}).get("mode") or "").strip() != "front_door":
			raise RuntimeError("Phase 7C live boundary smoke failed: front-door turn did not complete in the front-door lane.")
		session_doc = frappe_module.get_doc(session_doctype, doc.name)
		frontdoor_boundary = _latest_boundary_payload(
			session_doc,
			session_tool_payloads=session_tool_payloads,
			latest_tool_payload_by_type=latest_tool_payload_by_type,
		)
		if str(frontdoor_boundary.get("final_lane") or "").strip() != "front_door":
			raise RuntimeError("Phase 7C live boundary smoke failed: front-door boundary did not confirm front_door.")
		return {
			"ok": True,
			"frontdoor_boundary": frontdoor_boundary,
		}

	def _artifact_runner(doc) -> Dict[str, Any]:
		ok, artifact_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="show me sales invoices",
			user="Administrator",
		)
		if not ok or str((artifact_payload or {}).get("mode") or "").strip() not in {
			"compiled_first_turn",
			"legacy_runtime",
			"legacy_runtime_rollout_fallback",
		}:
			raise RuntimeError("Phase 7C live boundary smoke failed: artifact turn did not produce governed ERP output.")
		session_doc = frappe_module.get_doc(session_doctype, doc.name)
		artifact_boundary = _latest_boundary_payload(
			session_doc,
			session_tool_payloads=session_tool_payloads,
			latest_tool_payload_by_type=latest_tool_payload_by_type,
		)
		if str(artifact_boundary.get("final_lane") or "").strip() != "artifact_lane":
			raise RuntimeError("Phase 7C live boundary smoke failed: artifact boundary did not confirm artifact_lane.")
		return {
			"ok": True,
			"artifact_boundary": artifact_boundary,
		}

	def _reasoning_runner(doc) -> Dict[str, Any]:
		ok, setup_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_replacement_message("fresh_query_override_to_ar"),
			user="Administrator",
		)
		if not ok or str((setup_payload or {}).get("mode") or "").strip() not in {
			"compiled_first_turn",
			"legacy_runtime",
			"legacy_runtime_rollout_fallback",
		}:
			raise RuntimeError("Phase 7C live boundary smoke failed: reasoning setup replacement artifact turn did not complete.")

		ok, reasoning_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="Explain the overdue risk in this accounts receivable summary.",
			user="Administrator",
		)
		if not ok or str((reasoning_payload or {}).get("mode") or "").strip() != "erp_business_reasoning":
			raise RuntimeError("Phase 7C live boundary smoke failed: grounded reasoning turn did not enter the reasoning lane.")
		session_doc = frappe_module.get_doc(session_doctype, doc.name)
		reasoning_boundary = _latest_boundary_payload(
			session_doc,
			session_tool_payloads=session_tool_payloads,
			latest_tool_payload_by_type=latest_tool_payload_by_type,
		)
		if str(reasoning_boundary.get("final_lane") or "").strip() != "reasoning_lane":
			raise RuntimeError("Phase 7C live boundary smoke failed: reasoning boundary did not confirm reasoning_lane.")

		return {
			"ok": True,
			"reasoning_boundary": reasoning_boundary,
		}

	frontdoor_result = run_phase55_smoke_session(
		"Phase 7C Front Door Boundary Smoke",
		_frontdoor_runner,
		frappe_module=frappe_module,
		session_doctype=session_doctype,
	)
	artifact_result = run_phase55_smoke_session(
		"Phase 7C Artifact Boundary Smoke",
		_artifact_runner,
		frappe_module=frappe_module,
		session_doctype=session_doctype,
	)
	reasoning_result = run_phase55_smoke_session(
		"Phase 7C Reasoning Boundary Smoke",
		_reasoning_runner,
		frappe_module=frappe_module,
		session_doctype=session_doctype,
	)
	return {
		"ok": True,
		"frontdoor_boundary": dict(frontdoor_result.get("frontdoor_boundary") or {}),
		"artifact_boundary": dict(artifact_result.get("artifact_boundary") or {}),
		"reasoning_boundary": dict(reasoning_result.get("reasoning_boundary") or {}),
	}


def run_boundary_response_live_smoke(
	*,
	run_phase55_smoke_session: Callable[..., Dict[str, Any]],
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	latest_assistant_payload,
	latest_grounded_turn_contract,
	latest_tool_payload_by_type,
	session_tool_payloads,
) -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		frappe_module.clear_cache()
		ok, first_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="show me sales invoices",
			user="Administrator",
		)
		if not ok or str((first_payload or {}).get("mode") or "").strip() not in {
			"compiled_first_turn",
			"legacy_runtime",
			"legacy_runtime_rollout_fallback",
		}:
			raise RuntimeError("Phase 7D live boundary smoke failed: setup governed artifact turn did not complete.")

		_stabilize_boundary_smoke_visibility(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			session_name=doc.name,
			latest_assistant_payload=latest_assistant_payload,
			latest_grounded_turn_contract=latest_grounded_turn_contract,
		)
		ok, second_payload, session_doc, boundary_payload = _run_uncovered_domain_boundary_turn(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			session_name=doc.name,
			handle_qwen_user_message=handle_qwen_user_message,
			session_tool_payloads=session_tool_payloads,
			latest_tool_payload_by_type=latest_tool_payload_by_type,
			message="show employee headcount by department",
		)
		if not ok:
			raise RuntimeError("Phase 7D live boundary smoke failed: uncovered-domain turn did not complete.")
		assistant_payload = latest_assistant_payload(session_doc)
		answer_text = str(assistant_payload.get("text") or "").strip()
		if str(boundary_payload.get("knowledge_coverage_state") or "").strip() != "valid_erp_domain_uncovered":
			raise RuntimeError("Phase 7D live boundary smoke failed: employee headcount by department did not classify as valid_erp_domain_uncovered.")
		if str(boundary_payload.get("user_response_mode") or "").strip() != "coverage_gap_explanation":
			raise RuntimeError("Phase 7D live boundary smoke failed: uncovered-domain response mode was not coverage_gap_explanation.")
		lower_answer = answer_text.lower()
		has_scope_signal = any(
			snippet in lower_answer
			for snippet in (
				"erp/business scope",
				"business scope",
				"erp data",
			)
		)
		has_coverage_signal = any(
			snippet in lower_answer
			for snippet in (
				"coverage",
				"headcount",
				"staff-count",
				"hr",
				"can't answer",
			)
		)
		if not answer_text or not has_scope_signal or not has_coverage_signal:
			raise RuntimeError("Phase 7D live boundary smoke failed: user-facing answer did not explain the governed coverage gap clearly enough.")
		return {
			"ok": True,
			"mode": str((second_payload or {}).get("mode") or "").strip(),
			"boundary_payload": boundary_payload,
			"answer_text": answer_text,
		}

	return run_phase55_smoke_session(
		"Phase 7D Boundary Response Live Smoke",
		_runner,
		frappe_module=frappe_module,
		session_doctype=session_doctype,
	)


def run_observability_smoke(
	*,
	run_phase55_smoke_session: Callable[..., Dict[str, Any]],
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	latest_assistant_payload,
	latest_grounded_turn_contract,
	latest_tool_payload_by_type,
	session_tool_payloads,
) -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		ok, first_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="show me sales invoices",
			user="Administrator",
		)
		if not ok or str((first_payload or {}).get("mode") or "").strip() not in {
			"compiled_first_turn",
			"legacy_runtime",
			"legacy_runtime_rollout_fallback",
		}:
			raise RuntimeError("Phase 7 observability smoke failed: setup governed artifact turn did not complete.")
		_stabilize_boundary_smoke_visibility(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			session_name=doc.name,
			latest_assistant_payload=latest_assistant_payload,
			latest_grounded_turn_contract=latest_grounded_turn_contract,
		)
		ok, second_payload, session_doc, boundary_payload = _run_uncovered_domain_boundary_turn(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			session_name=doc.name,
			handle_qwen_user_message=handle_qwen_user_message,
			session_tool_payloads=session_tool_payloads,
			latest_tool_payload_by_type=latest_tool_payload_by_type,
			message="show employee headcount by department",
		)
		if not ok:
			raise RuntimeError("Phase 7 observability smoke failed: uncovered-domain turn did not complete.")
		tool_payloads = session_tool_payloads(session_doc)
		second_mode = str((second_payload or {}).get("mode") or "").strip()
		events = [
			item
			for item in tool_payloads
			if str(item.get("type") or "").strip() == "qwen_phase6_observability_event"
		]
		metrics = [
			item
			for item in tool_payloads
			if str(item.get("type") or "").strip() == "qwen_phase6_performance_metric"
		]
		if str(boundary_payload.get("knowledge_coverage_state") or "").strip() != "valid_erp_domain_uncovered":
			raise RuntimeError("Phase 7 observability smoke failed: knowledge boundary payload did not classify as valid_erp_domain_uncovered.")
		if second_mode in {"known_unsupported_erp_domain", "out_of_scope_domain"}:
			boundary_event = next(
				(
					item
					for item in reversed(events)
					if str(item.get("event_family") or "").strip() == "knowledge_boundary"
				),
				{},
			)
			boundary_metric = next(
				(
					item
					for item in reversed(metrics)
					if str(item.get("metric_name") or "").strip() == "knowledge_boundary_latency"
				),
				{},
			)
			if str(boundary_event.get("event_name") or "").strip() != "valid_erp_domain_uncovered":
				raise RuntimeError("Phase 7 observability smoke failed: knowledge boundary event_name mismatch.")
		elif second_mode in {"artifact_enrichment_boundary", "grounded_evidence_boundary"}:
			boundary_event = next(
				(
					item
					for item in reversed(events)
					if str(item.get("event_family") or "").strip() == "artifact_boundary"
					and str(item.get("event_name") or "").strip() == second_mode
				),
				{},
			)
			boundary_metric = next(
				(
					item
					for item in reversed(metrics)
					if str(item.get("metric_name") or "").strip() == f"{second_mode}_latency"
				),
				{},
			)
		else:
			raise RuntimeError("Phase 7 observability smoke failed: uncovered-domain turn did not stay on an approved governed boundary path.")
		if str(boundary_event.get("event_level") or "").strip() != "warning":
			raise RuntimeError("Phase 7 observability smoke failed: knowledge boundary event level was not warning.")
		if str(boundary_event.get("session_id") or "").strip() != str(doc.name):
			raise RuntimeError("Phase 7 observability smoke failed: boundary event session_id mismatch.")
		if not str(boundary_event.get("request_id") or "").strip():
			raise RuntimeError("Phase 7 observability smoke failed: boundary event request_id was empty.")
		if str(boundary_metric.get("session_id") or "").strip() != str(doc.name):
			raise RuntimeError("Phase 7 observability smoke failed: boundary metric session_id mismatch.")
		if not str(boundary_metric.get("request_id") or "").strip():
			raise RuntimeError("Phase 7 observability smoke failed: boundary metric request_id was empty.")
		return {
			"ok": True,
			"mode": second_mode,
			"boundary_payload": boundary_payload,
			"boundary_event": boundary_event,
			"boundary_metric": boundary_metric,
		}

	return run_phase55_smoke_session(
		"Phase 7 Observability Smoke",
		_runner,
		frappe_module=frappe_module,
		session_doctype=session_doctype,
	)


def run_hardening_suite(
	*,
	live_boundary_orchestration_smoke,
	boundary_response_live_smoke,
) -> Dict[str, Any]:
	return {
		"ok": True,
		"boundary_orchestration": live_boundary_orchestration_smoke(),
		"boundary_responses": boundary_response_live_smoke(),
	}
