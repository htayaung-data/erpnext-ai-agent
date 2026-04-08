from __future__ import annotations

import json
import re
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

import requests


def _fresh_query_module():
	from ai_assistant_ui.qwen_chat import fresh_query_interpreter as fresh_query_module

	return fresh_query_module


def _site_name(mod) -> str:
	frappe_module = getattr(mod, "frappe", None)
	if frappe_module is not None:
		return str(getattr(getattr(frappe_module, "local", None), "site", "") or "").strip()
	return ""


def _normalize_message_key(value: str) -> str:
	text = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower())
	return text.strip("-") or "message"


def run_phase4_fresh_query_pipeline_smokes() -> Dict[str, Any]:
	mod = _fresh_query_module()
	site_name = _site_name(mod)
	results: List[Dict[str, Any]] = []
	for message in [
		"How much payable amount do we have as of now",
		"Analyze payable amount",
		"Top 5 customers by revenue",
		"Show monthly sales trend in all regions",
	]:
		results.append(
			mod.compile_from_fresh_query_message(
				session_id="phase4-smoke",
				user_id="Administrator",
				site_name=site_name,
				message=message,
				recent_messages=[],
			)
		)
	return {"smokes": results}


def run_phase4_fresh_query_cache_smoke() -> Dict[str, Any]:
	mod = _fresh_query_module()
	site_name = _site_name(mod)
	message = "How much payable amount do we have as of now"
	first = mod.compile_from_fresh_query_message(
		session_id="phase4-cache-smoke-1",
		user_id="Administrator",
		site_name=site_name,
		message=message,
		recent_messages=[],
	)
	second = mod.compile_from_fresh_query_message(
		session_id="phase4-cache-smoke-2",
		user_id="Administrator",
		site_name=site_name,
		message=message,
		recent_messages=[],
	)
	first_telemetry = (
		((first.get("fresh_query_interpretation") or {}).get("agent_meta") or {}).get("telemetry")
		if isinstance(first.get("fresh_query_interpretation"), dict)
		else {}
	)
	second_telemetry = (
		((second.get("fresh_query_interpretation") or {}).get("agent_meta") or {}).get("telemetry")
		if isinstance(second.get("fresh_query_interpretation"), dict)
		else {}
	)
	if not isinstance(first_telemetry, dict):
		first_telemetry = {}
	if not isinstance(second_telemetry, dict):
		second_telemetry = {}
	if bool(first_telemetry.get("cache_hit")):
		raise RuntimeError("Fresh-query cache smoke failed: first proposal unexpectedly reported a cache hit.")
	if not bool(second_telemetry.get("cache_hit")):
		raise RuntimeError("Fresh-query cache smoke failed: second proposal did not report a cache hit.")
	return {
		"first": {
			"status": (first.get("fresh_query_interpretation") or {}).get("status")
			if isinstance(first.get("fresh_query_interpretation"), dict)
			else "",
			"telemetry": first_telemetry,
			"phase4_latency_breakdown": first.get("phase4_latency_breakdown"),
		},
		"second": {
			"status": (second.get("fresh_query_interpretation") or {}).get("status")
			if isinstance(second.get("fresh_query_interpretation"), dict)
			else "",
			"telemetry": second_telemetry,
			"phase4_latency_breakdown": second.get("phase4_latency_breakdown"),
		},
	}


def run_phase4_fresh_query_inflight_smoke() -> Dict[str, Any]:
	mod = _fresh_query_module()
	site_name = _site_name(mod)
	message = "Please show the current total payable amount as of today"
	barrier = threading.Barrier(2)
	context = mod._build_interpretation_context()
	conf = getattr(mod.frappe, "conf", None) or {}
	base_url = str(conf.get("qwen_agent_runtime_base_url") or "").strip().rstrip("/")
	if not base_url:
		raise RuntimeError("Fresh-query inflight smoke failed: qwen runtime base URL is not configured.")
	headers = {"Content-Type": "application/json"}
	token = str(conf.get("qwen_agent_runtime_api_token") or "").strip()
	if token:
		headers["Authorization"] = f"Bearer {token}"

	def _run(index: int) -> Dict[str, Any]:
		barrier.wait()
		payload = {
			"request_id": f"phase4-inflight-{index}-{uuid.uuid4().hex}",
			"session_id": f"phase4-inflight-smoke-{index}",
			"user_id": "Administrator",
			"site_name": site_name,
			"message": message,
			"recent_messages": [],
			"interpretation_context": context,
		}
		response = requests.post(
			f"{base_url}/interpret-fresh-query",
			headers=headers,
			data=json.dumps(payload),
			timeout=150,
		)
		response.raise_for_status()
		return response.json()

	with ThreadPoolExecutor(max_workers=2) as executor:
		first_future = executor.submit(_run, 1)
		second_future = executor.submit(_run, 2)
		first = first_future.result()
		second = second_future.result()

	def _telemetry(result: Dict[str, Any]) -> Dict[str, Any]:
		agent_meta = result.get("agent_meta") if isinstance(result.get("agent_meta"), dict) else {}
		telemetry = agent_meta.get("telemetry") if isinstance(agent_meta.get("telemetry"), dict) else {}
		return telemetry

	first_telemetry = _telemetry(first)
	second_telemetry = _telemetry(second)
	shared_inflight = bool(first_telemetry.get("shared_inflight_hit")) or bool(second_telemetry.get("shared_inflight_hit"))
	warm_cache = bool(first_telemetry.get("cache_hit")) and bool(second_telemetry.get("cache_hit"))
	if not (shared_inflight or warm_cache):
		raise RuntimeError(
			f"Fresh-query inflight smoke failed: no request reported a shared inflight hit. "
			f"first={first_telemetry!r} second={second_telemetry!r}"
		)
	return {
		"mode": "shared_inflight" if shared_inflight else "warm_cache",
		"first": {
			"telemetry": first_telemetry,
			"phase4_latency_breakdown": first.get("phase4_latency_breakdown"),
		},
		"second": {
			"telemetry": second_telemetry,
			"phase4_latency_breakdown": second.get("phase4_latency_breakdown"),
		},
	}


def run_phase4_fresh_query_interpreter_selftests() -> Dict[str, Any]:
	mod = _fresh_query_module()
	context = mod._build_interpretation_context()
	request_id = "selftest-fresh-query"
	session_id = "selftest-session"
	valid_payload = {
		"intent_class": "financial_summary",
		"candidate_capability_ids": ["accounts_payable_read"],
		"candidate_reports": ["Accounts Payable Summary"],
		"requested_dimensions": [],
		"requested_metrics": ["Outstanding"],
		"requested_time_scope": "as_of_today",
		"requested_presentation": [],
		"extracted_slots": {
			"report_date": mod._current_date_iso(),
			"filters": {
				"company": "Should Be Ignored",
			},
		},
		"ambiguity_flags": [],
		"ambiguity_reason": "",
		"confidence": 0.94,
	}
	contract = mod._validate_semantic_payload(
		request_id=request_id,
		session_id=session_id,
		payload=valid_payload,
		context=context,
	)
	if contract is None:
		raise RuntimeError("Fresh-query validation selftest failed: valid payload did not validate.")
	if "company" in ((contract.extracted_slots or {}).get("filters") or {}):
		raise RuntimeError("Fresh-query validation selftest failed: company leaked into extracted slot filters.")
	compiler_outcome = mod.compile_fresh_query(
		request_id=request_id,
		session_id=session_id,
		interpretation=contract,
		response_policy={"analysis_level": "none"},
	)
	if compiler_outcome.compiler_contract.decision != "execute":
		raise RuntimeError(
			f"Fresh-query compiler selftest failed: expected execute, got {compiler_outcome.compiler_contract.decision}."
		)

	invalid_payload = {
		"intent_class": "financial_summary",
		"candidate_capability_ids": ["accounts_payable_read"],
		"candidate_reports": ["Accounts Payable Summary"],
		"requested_dimensions": ["Warehouse"],
		"requested_metrics": ["Outstanding"],
		"requested_time_scope": "as_of_today",
		"requested_presentation": [],
		"extracted_slots": {},
		"ambiguity_flags": [],
		"ambiguity_reason": "",
		"confidence": 0.9,
	}
	invalid_contract = mod._validate_semantic_payload(
		request_id="selftest-invalid",
		session_id=session_id,
		payload=invalid_payload,
		context=context,
	)
	if invalid_contract is not None:
		raise RuntimeError("Fresh-query validation selftest failed: invalid dimension payload was accepted.")

	return {
		"valid_interpretation": contract.to_payload(),
		"compiler_contract": compiler_outcome.compiler_contract.to_payload(),
		"compiled_query_request": (
			compiler_outcome.compiled_request_contract.to_payload()
			if compiler_outcome.compiled_request_contract is not None
			else {}
		),
		"invalid_payload_rejected": True,
	}


def run_phase4_compiled_execution_smoke() -> Dict[str, Any]:
	mod = _fresh_query_module()
	site_name = _site_name(mod)
	message = "How much payable amount do we have as of now"
	result = mod.execute_compiled_fresh_query_message(
		session_id="phase4-compiled-smoke",
		user_id="Administrator",
		site_name=site_name,
		message=message,
		recent_messages=[],
	)
	semantic_validation = result.get("semantic_intent_validation")
	if not isinstance(semantic_validation, dict) or str(semantic_validation.get("status") or "").strip() != "pass":
		raise RuntimeError("Compiled execution smoke failed: semantic validation did not pass.")
	return result


def _phase4b_financial_statement_case_result(
	*,
	request_id: str,
	session_id: str,
	site_name: str,
	message: str,
	candidate_report: str,
	requested_metrics: List[str],
) -> Dict[str, Any]:
	mod = _fresh_query_module()
	response_policy = {"analysis_level": "none"}
	interaction_contract = mod.build_interaction_contract(
		request_id=request_id,
		session_id=session_id,
		user_id="Administrator",
		site_name=site_name,
		raw_message=message,
	)
	interpretation = mod.build_fresh_query_interpretation_contract(
		request_id=interaction_contract.request_id,
		session_id=session_id,
		intent_class="financial_statement",
		candidate_capability_ids=["financial_statement_read"],
		candidate_reports=[candidate_report],
		requested_dimensions=[],
		requested_metrics=requested_metrics,
		requested_time_scope="current_fiscal_year_to_date",
		requested_presentation=[],
		extracted_slots={},
		ambiguity_flags=[],
		ambiguity_reason="",
		confidence=0.95,
	)
	compiler_outcome = mod.compile_fresh_query(
		request_id=interaction_contract.request_id,
		session_id=session_id,
		interpretation=interpretation,
		response_policy=response_policy,
	)
	runtime_payload: Dict[str, Any] = {}
	if compiler_outcome.compiled_request_contract is not None:
		runtime_payload = mod.call_qwen_runtime_chat(
			session_id=session_id,
			user_id="Administrator",
			site_name=site_name,
			message=message,
			recent_messages=[],
			response_policy=response_policy,
			family_tool_context={},
			mode="compiled_read_query",
			compiled_query=compiler_outcome.compiled_request_contract.to_payload(),
			request_id=interaction_contract.request_id,
		)
	adapter_outcome = mod.build_normalized_family_artifact(
		request_id=interaction_contract.request_id,
		compiler_contract=compiler_outcome.compiler_contract.to_payload(),
		runtime_payload=runtime_payload,
		intent_class="financial_statement",
		preferred_family_id=mod._preferred_family_id_for_message(
			message=message,
			compiler_contract=compiler_outcome.compiler_contract.to_payload(),
			interpretation_contract=interpretation.to_payload(),
		),
	)
	family_validation = mod.validate_normalized_family_artifact(
		request_id=interaction_contract.request_id,
		compiler_contract=compiler_outcome.compiler_contract.to_payload(),
		artifact_contract=adapter_outcome.artifact_contract,
		family_id=adapter_outcome.family_id,
		adapter_errors=adapter_outcome.errors,
		adapter_warnings=adapter_outcome.warnings,
	)
	return {
		"request_id": interaction_contract.request_id,
		"message": message,
		"compiler_contract": compiler_outcome.compiler_contract.to_payload(),
		"compiled_query_request": (
			compiler_outcome.compiled_request_contract.to_payload()
			if compiler_outcome.compiled_request_contract is not None
			else {}
		),
		"runtime_ok": bool(runtime_payload.get("ok")),
		"runtime_answer": str(runtime_payload.get("answer_text") or "").strip(),
		"normalized_family_artifact": (
			adapter_outcome.artifact_contract.to_payload()
			if adapter_outcome.artifact_contract is not None
			else {}
		),
		"family_adapter_status": adapter_outcome.status,
		"family_adapter_errors": list(adapter_outcome.errors),
		"family_validation": family_validation.to_payload() if family_validation else {},
	}


def run_phase4b_financial_statement_family_probe() -> Dict[str, Any]:
	site_name = _site_name(_fresh_query_module())
	return {
		"pnl": _phase4b_financial_statement_case_result(
			request_id="phase4b-probe-pnl",
			session_id="phase4b-financial-family-probe",
			site_name=site_name,
			message="Show me P & L statement, and analyze it",
			candidate_report="Profit and Loss Statement",
			requested_metrics=["Total Income", "Total Expense", "Net Profit"],
		),
		"balance_sheet": _phase4b_financial_statement_case_result(
			request_id="phase4b-probe-balance-sheet",
			session_id="phase4b-financial-family-probe",
			site_name=site_name,
			message="Show balance sheet",
			candidate_report="Balance Sheet",
			requested_metrics=["Total Asset", "Total Liability", "Total Equity"],
		),
		"cash_flow": _phase4b_financial_statement_case_result(
			request_id="phase4b-probe-cash-flow",
			session_id="phase4b-financial-family-probe",
			site_name=site_name,
			message="Show cash flow statement",
			candidate_report="Cash Flow",
			requested_metrics=["Net Cash from Operations", "Net Change in Cash"],
		),
	}


def run_phase4b_broad_financial_report_ambiguity_probe() -> Dict[str, Any]:
	mod = _fresh_query_module()
	site_name = _site_name(mod)
	results: List[Dict[str, Any]] = []
	for message in [
		"give me the statement",
		"give me the financial statement",
		"give me the management report",
	]:
		result = mod.compile_from_fresh_query_message(
			session_id="phase4b-broad-financial-report-ambiguity",
			user_id="Administrator",
			site_name=site_name,
			message=message,
			recent_messages=[],
		)
		compiler = result.get("fresh_query_compiler") if isinstance(result.get("fresh_query_compiler"), dict) else {}
		decision = str(compiler.get("decision") or "").strip()
		reason_type = str(compiler.get("clarification_reason_type") or "").strip()
		details = compiler.get("clarification_details") if isinstance(compiler.get("clarification_details"), dict) else {}
		report_candidates = [str(value or "").strip() for value in (details.get("report_candidates") or []) if str(value or "").strip()]
		if decision != "clarify":
			raise RuntimeError(
				f"Broad financial report ambiguity probe failed: `{message}` resolved as `{decision}` instead of clarification."
			)
		if reason_type != "report_ambiguity":
			raise RuntimeError(
				f"Broad financial report ambiguity probe failed: `{message}` produced `{reason_type}` instead of report_ambiguity."
			)
		if len(report_candidates) < 2:
			raise RuntimeError(
				f"Broad financial report ambiguity probe failed: `{message}` did not preserve multiple report candidates."
			)
		results.append(
			{
				"message": message,
				"decision": decision,
				"reason_type": reason_type,
				"report_candidates": report_candidates,
			}
		)
	return {"ok": True, "results": results}


def run_phase4b_financial_statement_family_smoke() -> Dict[str, Any]:
	site_name = _site_name(_fresh_query_module())
	cases = [
		{
			"request_id": "phase4b-pnl",
			"message": "Show me P & L statement, and analyze it",
			"candidate_reports": ["Profit and Loss Statement"],
			"requested_metrics": ["Total Income", "Total Expense", "Net Profit"],
		},
		{
			"request_id": "phase4b-balance-sheet",
			"message": "Show balance sheet",
			"candidate_reports": ["Balance Sheet"],
			"requested_metrics": ["Total Asset", "Total Liability", "Total Equity"],
		},
		{
			"request_id": "phase4b-cash-flow",
			"message": "Show cash flow statement",
			"candidate_reports": ["Cash Flow"],
			"requested_metrics": ["Net Cash from Operations", "Net Change in Cash"],
		},
	]
	results: List[Dict[str, Any]] = []
	for item in cases:
		case_result = _phase4b_financial_statement_case_result(
			request_id=str(item.get("request_id") or uuid.uuid4().hex),
			session_id="phase4b-financial-family-smoke",
			site_name=site_name,
			message=str(item.get("message") or "").strip(),
			candidate_report=str((item.get("candidate_reports") or [""])[0] or "").strip(),
			requested_metrics=list(item.get("requested_metrics") or []),
		)
		family_validation = case_result.get("family_validation") if isinstance(case_result.get("family_validation"), dict) else {}
		if str(family_validation.get("status") or "").strip() != "pass":
			raise RuntimeError(
				f"Phase 4B financial family smoke failed: family validation did not pass for `{item.get('message')}`."
			)
		results.append(case_result)
	return {"ok": True, "results": results}


def _phase4b_aging_case_result(
	*,
	request_id: str,
	session_id: str,
	site_name: str,
	message: str,
	candidate_capability_id: str,
	candidate_report: str,
	requested_metrics: List[str],
) -> Dict[str, Any]:
	mod = _fresh_query_module()
	response_policy = {"analysis_level": "none"}
	interaction_contract = mod.build_interaction_contract(
		request_id=request_id,
		session_id=session_id,
		user_id="Administrator",
		site_name=site_name,
		raw_message=message,
	)
	interpretation = mod.build_fresh_query_interpretation_contract(
		request_id=interaction_contract.request_id,
		session_id=session_id,
		intent_class="aging_analysis",
		candidate_capability_ids=[candidate_capability_id],
		candidate_reports=[candidate_report],
		requested_dimensions=[],
		requested_metrics=requested_metrics,
		requested_time_scope="as_of_today",
		requested_presentation=[],
		extracted_slots={},
		ambiguity_flags=[],
		ambiguity_reason="",
		confidence=0.95,
	)
	compiler_outcome = mod.compile_fresh_query(
		request_id=interaction_contract.request_id,
		session_id=session_id,
		interpretation=interpretation,
		response_policy=response_policy,
	)
	runtime_payload: Dict[str, Any] = {}
	if compiler_outcome.compiled_request_contract is not None:
		runtime_payload = mod.call_qwen_runtime_chat(
			session_id=session_id,
			user_id="Administrator",
			site_name=site_name,
			message=message,
			recent_messages=[],
			response_policy=response_policy,
			family_tool_context={},
			mode="compiled_read_query",
			compiled_query=compiler_outcome.compiled_request_contract.to_payload(),
			request_id=interaction_contract.request_id,
		)
	adapter_outcome = mod.build_normalized_family_artifact(
		request_id=interaction_contract.request_id,
		compiler_contract=compiler_outcome.compiler_contract.to_payload(),
		runtime_payload=runtime_payload,
		intent_class="aging_analysis",
		preferred_family_id=mod._preferred_family_id_for_message(
			message=message,
			compiler_contract=compiler_outcome.compiler_contract.to_payload(),
			interpretation_contract=interpretation.to_payload(),
		),
	)
	family_validation = mod.validate_normalized_family_artifact(
		request_id=interaction_contract.request_id,
		compiler_contract=compiler_outcome.compiler_contract.to_payload(),
		artifact_contract=adapter_outcome.artifact_contract,
		family_id=adapter_outcome.family_id,
		adapter_errors=adapter_outcome.errors,
		adapter_warnings=adapter_outcome.warnings,
	)
	return {
		"request_id": interaction_contract.request_id,
		"message": message,
		"compiler_contract": compiler_outcome.compiler_contract.to_payload(),
		"compiled_query_request": (
			compiler_outcome.compiled_request_contract.to_payload()
			if compiler_outcome.compiled_request_contract is not None
			else {}
		),
		"runtime_ok": bool(runtime_payload.get("ok")),
		"runtime_answer": str(runtime_payload.get("answer_text") or "").strip(),
		"normalized_family_artifact": (
			adapter_outcome.artifact_contract.to_payload()
			if adapter_outcome.artifact_contract is not None
			else {}
		),
		"family_adapter_status": adapter_outcome.status,
		"family_adapter_errors": list(adapter_outcome.errors),
		"family_validation": family_validation.to_payload() if family_validation else {},
	}


def run_phase4b_aging_family_probe() -> Dict[str, Any]:
	site_name = _site_name(_fresh_query_module())
	return {
		"accounts_payable": _phase4b_aging_case_result(
			request_id="phase4b-probe-aging-payable",
			session_id="phase4b-aging-family-probe",
			site_name=site_name,
			message="Analyze payable aging as of today",
			candidate_capability_id="accounts_payable_read",
			candidate_report="Accounts Payable Summary",
			requested_metrics=["Outstanding Amount", "Total Amount Due"],
		),
		"accounts_receivable": _phase4b_aging_case_result(
			request_id="phase4b-probe-aging-receivable",
			session_id="phase4b-aging-family-probe",
			site_name=site_name,
			message="Analyze receivable aging as of today",
			candidate_capability_id="accounts_receivable_read",
			candidate_report="Accounts Receivable Summary",
			requested_metrics=["Outstanding Amount", "Total Amount Due"],
		),
	}


def run_phase4b_aging_family_smoke() -> Dict[str, Any]:
	site_name = _site_name(_fresh_query_module())
	cases = [
		{
			"request_id": "phase4b-aging-payable",
			"message": "Analyze payable aging as of today",
			"candidate_capability_id": "accounts_payable_read",
			"candidate_report": "Accounts Payable Summary",
			"requested_metrics": ["Outstanding Amount", "Total Amount Due"],
		},
		{
			"request_id": "phase4b-aging-receivable",
			"message": "Analyze receivable aging as of today",
			"candidate_capability_id": "accounts_receivable_read",
			"candidate_report": "Accounts Receivable Summary",
			"requested_metrics": ["Outstanding Amount", "Total Amount Due"],
		},
	]
	results: List[Dict[str, Any]] = []
	for item in cases:
		case_result = _phase4b_aging_case_result(
			request_id=str(item.get("request_id") or uuid.uuid4().hex),
			session_id="phase4b-aging-family-smoke",
			site_name=site_name,
			message=str(item.get("message") or "").strip(),
			candidate_capability_id=str(item.get("candidate_capability_id") or "").strip(),
			candidate_report=str(item.get("candidate_report") or "").strip(),
			requested_metrics=list(item.get("requested_metrics") or []),
		)
		family_validation = case_result.get("family_validation") if isinstance(case_result.get("family_validation"), dict) else {}
		if str(family_validation.get("status") or "").strip() != "pass":
			raise RuntimeError(
				f"Phase 4B aging family smoke failed: family validation did not pass for `{item.get('message')}`."
			)
		results.append(case_result)
	return {"ok": True, "results": results}


def _phase4b_ranking_trend_case_result(
	*,
	request_id: str,
	session_id: str,
	site_name: str,
	message: str,
	intent_class: str,
	candidate_capability_id: str,
	candidate_report: str,
	requested_dimensions: List[str],
	requested_metrics: List[str],
	requested_time_scope: str,
) -> Dict[str, Any]:
	mod = _fresh_query_module()
	response_policy = {"analysis_level": "none"}
	interaction_contract = mod.build_interaction_contract(
		request_id=request_id,
		session_id=session_id,
		user_id="Administrator",
		site_name=site_name,
		raw_message=message,
	)
	interpretation = mod.build_fresh_query_interpretation_contract(
		request_id=interaction_contract.request_id,
		session_id=session_id,
		intent_class=intent_class,
		candidate_capability_ids=[candidate_capability_id],
		candidate_reports=[candidate_report],
		requested_dimensions=requested_dimensions,
		requested_metrics=requested_metrics,
		requested_time_scope=requested_time_scope,
		requested_presentation=[],
		extracted_slots={},
		ambiguity_flags=[],
		ambiguity_reason="",
		confidence=0.95,
	)
	compiler_outcome = mod.compile_fresh_query(
		request_id=interaction_contract.request_id,
		session_id=session_id,
		interpretation=interpretation,
		response_policy=response_policy,
	)
	runtime_payload: Dict[str, Any] = {}
	if compiler_outcome.compiled_request_contract is not None:
		runtime_payload = mod.call_qwen_runtime_chat(
			session_id=session_id,
			user_id="Administrator",
			site_name=site_name,
			message=message,
			recent_messages=[],
			response_policy=response_policy,
			family_tool_context={},
			mode="compiled_read_query",
			compiled_query=compiler_outcome.compiled_request_contract.to_payload(),
			request_id=interaction_contract.request_id,
		)
	adapter_outcome = mod.build_normalized_family_artifact(
		request_id=interaction_contract.request_id,
		compiler_contract=compiler_outcome.compiler_contract.to_payload(),
		runtime_payload=runtime_payload,
		intent_class=intent_class,
		preferred_family_id=mod._preferred_family_id_for_message(
			message=message,
			compiler_contract=compiler_outcome.compiler_contract.to_payload(),
			interpretation_contract=interpretation.to_payload(),
		),
	)
	family_validation = mod.validate_normalized_family_artifact(
		request_id=interaction_contract.request_id,
		compiler_contract=compiler_outcome.compiler_contract.to_payload(),
		artifact_contract=adapter_outcome.artifact_contract,
		family_id=adapter_outcome.family_id,
		adapter_errors=adapter_outcome.errors,
		adapter_warnings=adapter_outcome.warnings,
	)
	return {
		"request_id": interaction_contract.request_id,
		"message": message,
		"compiler_contract": compiler_outcome.compiler_contract.to_payload(),
		"compiled_query_request": (
			compiler_outcome.compiled_request_contract.to_payload()
			if compiler_outcome.compiled_request_contract is not None
			else {}
		),
		"runtime_ok": bool(runtime_payload.get("ok")),
		"runtime_answer": str(runtime_payload.get("answer_text") or "").strip(),
		"normalized_family_artifact": (
			adapter_outcome.artifact_contract.to_payload()
			if adapter_outcome.artifact_contract is not None
			else {}
		),
		"family_adapter_status": adapter_outcome.status,
		"family_adapter_errors": list(adapter_outcome.errors),
		"family_validation": family_validation.to_payload() if family_validation else {},
	}


def run_phase4b_ranking_trend_family_probe() -> Dict[str, Any]:
	site_name = _site_name(_fresh_query_module())
	return {
		"top_customers_revenue": _phase4b_ranking_trend_case_result(
			request_id="phase4b-probe-ranking-customers",
			session_id="phase4b-ranking-trend-family-probe",
			site_name=site_name,
			message="Top 5 customers by revenue",
			intent_class="ranked_entities",
			candidate_capability_id="sales_read",
			candidate_report="Sales Analytics",
			requested_dimensions=["Customer"],
			requested_metrics=["Revenue"],
			requested_time_scope="current_fiscal_year_to_date",
		),
		"monthly_sales_trend": _phase4b_ranking_trend_case_result(
			request_id="phase4b-probe-trend-sales",
			session_id="phase4b-ranking-trend-family-probe",
			site_name=site_name,
			message="Show monthly sales trend",
			intent_class="trend_analysis",
			candidate_capability_id="sales_read",
			candidate_report="Sales Analytics",
			requested_dimensions=[],
			requested_metrics=["Revenue"],
			requested_time_scope="current_fiscal_year_to_date",
		),
		"top_products_gross_profit": _phase4b_ranking_trend_case_result(
			request_id="phase4b-probe-ranking-products",
			session_id="phase4b-ranking-trend-family-probe",
			site_name=site_name,
			message="Top products by gross profit last month",
			intent_class="ranked_entities",
			candidate_capability_id="product_performance_read",
			candidate_report="Gross Profit",
			requested_dimensions=["Item Code"],
			requested_metrics=["Gross Profit"],
			requested_time_scope="last_month",
		),
	}


def run_phase4b_ranking_trend_family_smoke() -> Dict[str, Any]:
	site_name = _site_name(_fresh_query_module())
	cases = [
		{
			"request_id": "phase4b-ranking-customers",
			"message": "Top 5 customers by revenue",
			"intent_class": "ranked_entities",
			"candidate_capability_id": "sales_read",
			"candidate_report": "Sales Analytics",
			"requested_dimensions": ["Customer"],
			"requested_metrics": ["Revenue"],
			"requested_time_scope": "current_fiscal_year_to_date",
		},
		{
			"request_id": "phase4b-trend-sales",
			"message": "Show monthly sales trend",
			"intent_class": "trend_analysis",
			"candidate_capability_id": "sales_read",
			"candidate_report": "Sales Analytics",
			"requested_dimensions": [],
			"requested_metrics": ["Revenue"],
			"requested_time_scope": "current_fiscal_year_to_date",
		},
		{
			"request_id": "phase4b-ranking-products",
			"message": "Top products by gross profit last month",
			"intent_class": "ranked_entities",
			"candidate_capability_id": "product_performance_read",
			"candidate_report": "Gross Profit",
			"requested_dimensions": ["Item Code"],
			"requested_metrics": ["Gross Profit"],
			"requested_time_scope": "last_month",
		},
	]
	results: List[Dict[str, Any]] = []
	for item in cases:
		case_result = _phase4b_ranking_trend_case_result(
			request_id=str(item.get("request_id") or uuid.uuid4().hex),
			session_id="phase4b-ranking-trend-family-smoke",
			site_name=site_name,
			message=str(item.get("message") or "").strip(),
			intent_class=str(item.get("intent_class") or "").strip(),
			candidate_capability_id=str(item.get("candidate_capability_id") or "").strip(),
			candidate_report=str(item.get("candidate_report") or "").strip(),
			requested_dimensions=list(item.get("requested_dimensions") or []),
			requested_metrics=list(item.get("requested_metrics") or []),
			requested_time_scope=str(item.get("requested_time_scope") or "").strip(),
		)
		family_validation = case_result.get("family_validation") if isinstance(case_result.get("family_validation"), dict) else {}
		if str(family_validation.get("status") or "").strip() != "pass":
			raise RuntimeError(
				f"Phase 4B ranking/trend family smoke failed: family validation did not pass for `{item.get('message')}`."
			)
		results.append(case_result)
	return {"ok": True, "results": results}


def _phase4b_inventory_product_case_result(
	*,
	request_id: str,
	session_id: str,
	site_name: str,
	message: str,
	intent_class: str,
	candidate_capability_id: str,
	candidate_report: str,
	requested_dimensions: List[str],
	requested_metrics: List[str],
	requested_time_scope: str,
) -> Dict[str, Any]:
	mod = _fresh_query_module()
	response_policy = {"analysis_level": "none"}
	interaction_contract = mod.build_interaction_contract(
		request_id=request_id,
		session_id=session_id,
		user_id="Administrator",
		site_name=site_name,
		raw_message=message,
	)
	interpretation = mod.build_fresh_query_interpretation_contract(
		request_id=interaction_contract.request_id,
		session_id=session_id,
		intent_class=intent_class,
		candidate_capability_ids=[candidate_capability_id],
		candidate_reports=[candidate_report],
		requested_dimensions=requested_dimensions,
		requested_metrics=requested_metrics,
		requested_time_scope=requested_time_scope,
		requested_presentation=[],
		extracted_slots={},
		ambiguity_flags=[],
		ambiguity_reason="",
		confidence=0.95,
	)
	compiler_outcome = mod.compile_fresh_query(
		request_id=interaction_contract.request_id,
		session_id=session_id,
		interpretation=interpretation,
		response_policy=response_policy,
	)
	runtime_payload: Dict[str, Any] = {}
	if compiler_outcome.compiled_request_contract is not None:
		runtime_payload = mod.call_qwen_runtime_chat(
			session_id=session_id,
			user_id="Administrator",
			site_name=site_name,
			message=message,
			recent_messages=[],
			response_policy=response_policy,
			family_tool_context={},
			mode="compiled_read_query",
			compiled_query=compiler_outcome.compiled_request_contract.to_payload(),
			request_id=interaction_contract.request_id,
		)
	adapter_outcome = mod.build_normalized_family_artifact(
		request_id=interaction_contract.request_id,
		compiler_contract=compiler_outcome.compiler_contract.to_payload(),
		runtime_payload=runtime_payload,
		intent_class=intent_class,
		preferred_family_id=mod._preferred_family_id_for_message(
			message=message,
			compiler_contract=compiler_outcome.compiler_contract.to_payload(),
			interpretation_contract=interpretation.to_payload(),
		),
	)
	family_validation = mod.validate_normalized_family_artifact(
		request_id=interaction_contract.request_id,
		compiler_contract=compiler_outcome.compiler_contract.to_payload(),
		artifact_contract=adapter_outcome.artifact_contract,
		family_id=adapter_outcome.family_id,
		adapter_errors=adapter_outcome.errors,
		adapter_warnings=adapter_outcome.warnings,
	)
	return {
		"request_id": interaction_contract.request_id,
		"message": message,
		"compiler_contract": compiler_outcome.compiler_contract.to_payload(),
		"compiled_query_request": (
			compiler_outcome.compiled_request_contract.to_payload()
			if compiler_outcome.compiled_request_contract is not None
			else {}
		),
		"runtime_ok": bool(runtime_payload.get("ok")),
		"runtime_answer": str(runtime_payload.get("answer_text") or "").strip(),
		"normalized_family_artifact": (
			adapter_outcome.artifact_contract.to_payload()
			if adapter_outcome.artifact_contract is not None
			else {}
		),
		"family_adapter_status": adapter_outcome.status,
		"family_adapter_errors": list(adapter_outcome.errors),
		"family_validation": family_validation.to_payload() if family_validation else {},
	}


def run_phase4b_inventory_product_family_probe() -> Dict[str, Any]:
	site_name = _site_name(_fresh_query_module())
	return {
		"inventory_by_warehouse": _phase4b_inventory_product_case_result(
			request_id="phase4b-probe-inventory-warehouse",
			session_id="phase4b-inventory-product-family-probe",
			site_name=site_name,
			message="Show current inventory value by warehouse",
			intent_class="inventory_summary",
			candidate_capability_id="stock_read",
			candidate_report="Warehouse Wise Stock Balance",
			requested_dimensions=["Warehouse"],
			requested_metrics=["Balance Value (MMK)"],
			requested_time_scope="as_of_today",
		),
		"inventory_by_item": _phase4b_inventory_product_case_result(
			request_id="phase4b-probe-inventory-item",
			session_id="phase4b-inventory-product-family-probe",
			site_name=site_name,
			message="Show stock balance by item",
			intent_class="inventory_summary",
			candidate_capability_id="stock_read",
			candidate_report="Stock Balance",
			requested_dimensions=["Item"],
			requested_metrics=["Balance Qty"],
			requested_time_scope="as_of_today",
		),
		"product_profitability": _phase4b_inventory_product_case_result(
			request_id="phase4b-probe-product-profitability",
			session_id="phase4b-inventory-product-family-probe",
			site_name=site_name,
			message="Which products are performing well last month",
			intent_class="product_performance",
			candidate_capability_id="product_performance_read",
			candidate_report="Gross Profit",
			requested_dimensions=["Item Code"],
			requested_metrics=["Gross Profit", "Gross Profit Percent"],
			requested_time_scope="last_month",
		),
		"product_sales_history": _phase4b_inventory_product_case_result(
			request_id="phase4b-probe-product-history",
			session_id="phase4b-inventory-product-family-probe",
			site_name=site_name,
			message="Show item sales history this fiscal year",
			intent_class="product_performance",
			candidate_capability_id="product_performance_read",
			candidate_report="Item-wise Sales History",
			requested_dimensions=["Item"],
			requested_metrics=["Billed Amount", "Delivered Quantity"],
			requested_time_scope="current_fiscal_year_to_date",
		),
	}


def run_phase4b_inventory_product_family_smoke() -> Dict[str, Any]:
	site_name = _site_name(_fresh_query_module())
	cases = [
		{
			"request_id": "phase4b-inventory-warehouse",
			"message": "Show current inventory value by warehouse",
			"intent_class": "inventory_summary",
			"candidate_capability_id": "stock_read",
			"candidate_report": "Warehouse Wise Stock Balance",
			"requested_dimensions": ["Warehouse"],
			"requested_metrics": ["Balance Value (MMK)"],
			"requested_time_scope": "as_of_today",
		},
		{
			"request_id": "phase4b-inventory-item",
			"message": "Show stock balance by item",
			"intent_class": "inventory_summary",
			"candidate_capability_id": "stock_read",
			"candidate_report": "Stock Balance",
			"requested_dimensions": ["Item"],
			"requested_metrics": ["Balance Qty"],
			"requested_time_scope": "as_of_today",
		},
		{
			"request_id": "phase4b-product-profitability",
			"message": "Which products are performing well last month",
			"intent_class": "product_performance",
			"candidate_capability_id": "product_performance_read",
			"candidate_report": "Gross Profit",
			"requested_dimensions": ["Item Code"],
			"requested_metrics": ["Gross Profit", "Gross Profit Percent"],
			"requested_time_scope": "last_month",
		},
		{
			"request_id": "phase4b-product-history",
			"message": "Show item sales history this fiscal year",
			"intent_class": "product_performance",
			"candidate_capability_id": "product_performance_read",
			"candidate_report": "Item-wise Sales History",
			"requested_dimensions": ["Item"],
			"requested_metrics": ["Billed Amount", "Delivered Quantity"],
			"requested_time_scope": "current_fiscal_year_to_date",
		},
	]
	results: List[Dict[str, Any]] = []
	for item in cases:
		case_result = _phase4b_inventory_product_case_result(
			request_id=str(item.get("request_id") or uuid.uuid4().hex),
			session_id="phase4b-inventory-product-family-smoke",
			site_name=site_name,
			message=str(item.get("message") or "").strip(),
			intent_class=str(item.get("intent_class") or "").strip(),
			candidate_capability_id=str(item.get("candidate_capability_id") or "").strip(),
			candidate_report=str(item.get("candidate_report") or "").strip(),
			requested_dimensions=list(item.get("requested_dimensions") or []),
			requested_metrics=list(item.get("requested_metrics") or []),
			requested_time_scope=str(item.get("requested_time_scope") or "").strip(),
		)
		family_validation = case_result.get("family_validation") if isinstance(case_result.get("family_validation"), dict) else {}
		if str(family_validation.get("status") or "").strip() != "pass":
			raise RuntimeError(
				f"Phase 4B inventory/product family smoke failed: family validation did not pass for `{item.get('message')}`."
			)
		results.append(case_result)
	return {"ok": True, "results": results}


def run_phase4b_composite_read_probe() -> Dict[str, Any]:
	mod = _fresh_query_module()
	request_id = "phase4b-composite-probe"
	session_id = "phase4b-composite-probe"
	interpretation = mod.build_fresh_query_interpretation_contract(
		request_id=request_id,
		session_id=session_id,
		intent_class="financial_summary",
		candidate_capability_ids=[],
		candidate_reports=[],
		requested_dimensions=[],
		requested_metrics=["Outstanding"],
		requested_time_scope="as_of_today",
		requested_presentation=[],
		extracted_slots={},
		ambiguity_flags=[],
		ambiguity_reason="",
		confidence=1.0,
	)
	plan_outcome = mod.plan_composite_read(
		request_id=request_id,
		session_id=session_id,
		message="Analyze AR / AP amount and evaluate the company health",
		interpretation=interpretation,
		response_policy={
			"analysis_requested": True,
			"policy_mode": "grounded_analysis",
			"insight_allowed": True,
			"recommendation_allowed": False,
			"grounding_rule": "Composite analysis must stay grounded in normalized governed family artifacts.",
			"structure": ["grounded_facts_first", "concise_interpretation_only_when_grounded"],
		},
	)
	if str(plan_outcome.status or "").strip() != "execute":
		raise RuntimeError("Phase 4B composite probe failed: composite plan did not execute.")
	return {
		"ok": True,
		"plan": plan_outcome.plan_contract.to_payload() if plan_outcome.plan_contract else {},
		"compiler_contract": (
			plan_outcome.compiler_contract.to_payload()
			if plan_outcome.compiler_contract is not None
			else {}
		),
		"step_compiler_contracts": [item.to_payload() for item in plan_outcome.step_compiler_contracts],
	}


def run_phase4b_composite_read_smoke() -> Dict[str, Any]:
	mod = _fresh_query_module()
	site_name = _site_name(mod)
	request_id = "phase4b-composite-smoke"
	session_id = "phase4b-composite-smoke"
	interpretation = mod.build_fresh_query_interpretation_contract(
		request_id=request_id,
		session_id=session_id,
		intent_class="financial_summary",
		candidate_capability_ids=[],
		candidate_reports=[],
		requested_dimensions=[],
		requested_metrics=["Outstanding"],
		requested_time_scope="as_of_today",
		requested_presentation=[],
		extracted_slots={},
		ambiguity_flags=[],
		ambiguity_reason="",
		confidence=1.0,
	)
	response_policy_payload = {
		"analysis_requested": True,
		"policy_mode": "grounded_analysis",
		"insight_allowed": True,
		"recommendation_allowed": False,
		"grounding_rule": "Composite analysis must stay grounded in normalized governed family artifacts.",
		"structure": ["grounded_facts_first", "concise_interpretation_only_when_grounded"],
	}
	plan_outcome = mod.plan_composite_read(
		request_id=request_id,
		session_id=session_id,
		message="Analyze AR / AP amount and evaluate the company health",
		interpretation=interpretation,
		response_policy=response_policy_payload,
	)
	if str(plan_outcome.status or "").strip() != "execute":
		raise RuntimeError("Phase 4B composite smoke failed: composite plan did not execute.")
	pipeline = {
		"request_id": request_id,
		"response_policy_contract": {
			"analysis_requested": True,
			"policy_mode": "grounded_analysis",
			"insight_allowed": True,
			"recommendation_allowed": False,
			"grounding_rule": "Composite analysis must stay grounded in normalized governed family artifacts.",
			"structure": ["grounded_facts_first", "concise_interpretation_only_when_grounded"],
		},
		"fresh_query_interpretation": {
			"status": "accepted",
			"interpretation": interpretation.to_payload(),
			"agent_meta": {},
		},
		"fresh_query_compiler": plan_outcome.compiler_contract.to_payload() if plan_outcome.compiler_contract else {},
		"composite_read_plan": plan_outcome.plan_contract.to_payload() if plan_outcome.plan_contract else {},
	}
	result = mod.execute_composite_read_plan(
		session_id=session_id,
		user_id="Administrator",
		site_name=site_name,
		message="Analyze AR / AP amount and evaluate the company health",
		recent_messages=[],
		pipeline=pipeline,
		plan_outcome=plan_outcome,
		proposal_generation_latency_ms=0,
		compilation_latency_ms=0,
		total_started=time.perf_counter(),
	)
	family_validation = result.get("family_validation") if isinstance(result.get("family_validation"), dict) else {}
	semantic_validation = (
		result.get("semantic_intent_validation")
		if isinstance(result.get("semantic_intent_validation"), dict)
		else {}
	)
	runtime_payload = result.get("runtime_payload") if isinstance(result.get("runtime_payload"), dict) else {}
	if str(family_validation.get("status") or "").strip() != "pass":
		raise RuntimeError("Phase 4B composite smoke failed: composite validation did not pass.")
	if str(semantic_validation.get("status") or "").strip() != "pass":
		raise RuntimeError("Phase 4B composite smoke failed: composite semantic validation did not pass.")
	if not bool(runtime_payload.get("ok")):
		raise RuntimeError("Phase 4B composite smoke failed: composite runtime payload was not ok.")
	return {
		"ok": True,
		"result": result,
	}


def run_phase4b_composite_read_debug() -> Dict[str, Any]:
	mod = _fresh_query_module()
	site_name = _site_name(mod)
	request_id = "phase4b-composite-debug"
	session_id = "phase4b-composite-debug"
	interpretation = mod.build_fresh_query_interpretation_contract(
		request_id=request_id,
		session_id=session_id,
		intent_class="financial_summary",
		candidate_capability_ids=[],
		candidate_reports=[],
		requested_dimensions=[],
		requested_metrics=["Outstanding"],
		requested_time_scope="as_of_today",
		requested_presentation=[],
		extracted_slots={},
		ambiguity_flags=[],
		ambiguity_reason="",
		confidence=1.0,
	)
	response_policy_payload = {
		"analysis_requested": True,
		"policy_mode": "grounded_analysis",
		"insight_allowed": True,
		"recommendation_allowed": False,
		"grounding_rule": "Composite analysis must stay grounded in normalized governed family artifacts.",
		"structure": ["grounded_facts_first", "concise_interpretation_only_when_grounded"],
	}
	plan_outcome = mod.plan_composite_read(
		request_id=request_id,
		session_id=session_id,
		message="Analyze AR / AP amount and evaluate the company health",
		interpretation=interpretation,
		response_policy=response_policy_payload,
	)
	pipeline = {
		"request_id": request_id,
		"fresh_query_interpretation": {
			"status": "accepted",
			"interpretation": interpretation.to_payload(),
			"agent_meta": {},
		},
		"fresh_query_compiler": plan_outcome.compiler_contract.to_payload() if plan_outcome.compiler_contract else {},
		"composite_read_plan": plan_outcome.plan_contract.to_payload() if plan_outcome.plan_contract else {},
	}
	return mod.execute_composite_read_plan(
		session_id=session_id,
		user_id="Administrator",
		site_name=site_name,
		message="Analyze AR / AP amount and evaluate the company health",
		recent_messages=[],
		pipeline=pipeline,
		plan_outcome=plan_outcome,
		proposal_generation_latency_ms=0,
		compilation_latency_ms=0,
		total_started=time.perf_counter(),
	)


def run_phase4_semantic_validation_smoke() -> Dict[str, Any]:
	mod = _fresh_query_module()
	site_name = _site_name(mod)
	return mod.execute_compiled_fresh_query_message(
		session_id="phase4-semantic-smoke",
		user_id="Administrator",
		site_name=site_name,
		message="How much payable amount do we have as of now",
		recent_messages=[],
	)


def run_phase4_slice5_selftests() -> Dict[str, Any]:
	mod = _fresh_query_module()
	return {
		"fresh_query_interpreter": run_phase4_fresh_query_interpreter_selftests(),
		"semantic_validation": mod.run_phase4_semantic_validation_selftests(),
	}


def run_phase4_slice6_selftests() -> Dict[str, Any]:
	mod = _fresh_query_module()
	audit = mod.build_compiled_execution_audit_contract(
		request_id="slice6-selftest",
		session_id="slice6-session",
		compiler_decision="execute",
		compiler_reason="governed compiler path",
		governed_resolution_details={
			"resolution_mode": "semantic_resolution",
			"semantic_resolution_contract": {"type": "qwen_semantic_resolution_contract"},
		},
		capability_id="accounts_payable_read",
		selected_report="Accounts Payable Summary",
		governed_family_id="aging",
		composite_plan_id="",
		proposal_cache_hit=False,
		proposal_shared_inflight_hit=False,
		compiled_query_available=True,
		runtime_invoked=True,
		runtime_ok=True,
		runtime_engine="qwen_agent",
		runtime_model="qwen3.5-plus",
		grounded_validation_status="pass",
		family_validation_status="pass",
		semantic_validation_status="pass",
		proposal_generation_latency_ms=120,
		compilation_latency_ms=5,
		runtime_execution_latency_ms=950,
		semantic_validation_latency_ms=3,
		total_pipeline_latency_ms=1078,
		tool_count=1,
		tool_names=["erp_fac-generate_report"],
	)
	payload = audit.to_payload()
	if str(payload.get("type") or "").strip() != "qwen_compiled_execution_audit_contract":
		raise RuntimeError("Slice 6 selftest failed: compiled execution audit contract type mismatch.")
	if int(payload.get("total_pipeline_latency_ms") or 0) < int(payload.get("runtime_execution_latency_ms") or 0):
		raise RuntimeError("Slice 6 selftest failed: total latency is inconsistent.")
	if int(payload.get("tool_count") or 0) != 1:
		raise RuntimeError("Slice 6 selftest failed: tool count mismatch.")
	if str(((payload.get("governed_resolution_details") or {}).get("resolution_mode")) or "").strip() != "semantic_resolution":
		raise RuntimeError("Slice 6 selftest failed: governed resolution details were not preserved.")
	if bool(payload.get("proposal_cache_hit")):
		raise RuntimeError("Slice 6 selftest failed: proposal cache flag mismatch.")
	if bool(payload.get("proposal_shared_inflight_hit")):
		raise RuntimeError("Slice 6 selftest failed: proposal inflight flag mismatch.")
	return payload


def run_phase4_audit_observability_smoke() -> Dict[str, Any]:
	mod = _fresh_query_module()
	site_name = _site_name(mod)
	result = mod.execute_compiled_fresh_query_message(
		session_id="phase4-audit-smoke",
		user_id="Administrator",
		site_name=site_name,
		message="How much payable amount do we have as of now",
		recent_messages=[],
	)
	audit = result.get("compiled_execution_audit")
	if not isinstance(audit, dict):
		raise RuntimeError("Slice 6 audit smoke failed: missing compiled execution audit payload.")
	if str(audit.get("semantic_validation_status") or "").strip() != "pass":
		raise RuntimeError("Slice 6 audit smoke failed: semantic validation did not pass.")
	if int(audit.get("tool_count") or 0) < 1:
		raise RuntimeError("Slice 6 audit smoke failed: expected at least one grounded tool call.")
	return result


def run_phase4b_family_rendering_smoke() -> Dict[str, Any]:
	mod = _fresh_query_module()
	site_name = _site_name(mod)
	checks = [
		("financial_statement", "Show me P & L statement"),
		("aging", "How much payable amount do we have as of now"),
		("ranking_analytics", "Top 5 customers by revenue"),
		("trend_analytics", "Show monthly sales trend"),
		("product_profitability", "which products are performing well last month"),
		("composite_working_capital_health", "Analyze AR / AP amount and evaluate the company health"),
	]
	results: List[Dict[str, Any]] = []
	for expected_family, message in checks:
		result = mod.execute_compiled_fresh_query_message(
			session_id=f"phase4b-rendering-{_normalize_message_key(message)}",
			user_id="Administrator",
			site_name=site_name,
			message=message,
			recent_messages=[],
		)
		rendered_response = result.get("rendered_response") if isinstance(result.get("rendered_response"), dict) else {}
		answer_text = str(rendered_response.get("answer_text") or "").strip()
		if not answer_text:
			raise RuntimeError(f"Phase 4B rendering smoke failed: missing rendered response for `{message}`.")
		family_id = str(rendered_response.get("family_id") or "").strip()
		if family_id != expected_family:
			raise RuntimeError(
				f"Phase 4B rendering smoke failed: expected family `{expected_family}`, got `{family_id or 'unknown'}` for `{message}`."
			)
		family_validation = result.get("family_validation") if isinstance(result.get("family_validation"), dict) else {}
		if str(family_validation.get("status") or "").strip() != "pass":
			raise RuntimeError(
				f"Phase 4B rendering smoke failed: family validation did not pass for `{message}`."
			)
		results.append(
			{
				"message": message,
				"family_id": family_id,
				"title": str(rendered_response.get("title") or "").strip(),
				"answer_text": answer_text,
				"phase4_latency_breakdown": result.get("phase4_latency_breakdown"),
			}
		)
	return {"renders": results}
