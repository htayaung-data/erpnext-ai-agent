from __future__ import annotations

import datetime as dt
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.compiler import compile_fresh_query
from ai_assistant_ui.qwen_chat.contracts import (
	CompiledExecutionAuditContract,
	CompiledQueryRequestContract,
	CompositeReadPlanContract,
	FreshQueryCompilerContract,
	FreshQueryInterpretationContract,
	build_compiled_execution_audit_contract,
	build_composite_read_plan_contract,
	build_fresh_query_compiler_contract,
	build_fresh_query_interpretation_contract,
)
from ai_assistant_ui.qwen_chat.family_adapters import FamilyArtifactOutcome, build_normalized_family_artifact
from ai_assistant_ui.qwen_chat.family_validator import FamilyValidationOutcome, validate_normalized_family_artifact
from ai_assistant_ui.qwen_chat.metadata import (
	list_composite_read_specs,
	ontology_detect_concepts,
)
from ai_assistant_ui.qwen_chat.runtime_client import QwenRuntimeClientError, call_qwen_runtime_chat


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [str(value or "").strip() for value in values if str(value or "").strip()]


def _normalize_key(value: Any) -> str:
	text = str(value or "").strip().lower()
	return "".join(ch if ch.isalnum() else "_" for ch in text).strip("_")


def _requested_time_scope(primary_scope: str, strategy: str) -> str:
	scope = str(primary_scope or "").strip()
	mode = str(strategy or "").strip()
	if mode == "inherit_or_as_of_today":
		return scope or "as_of_today"
	return scope


def _analysis_requested(message: str) -> bool:
	text = " ".join(str(message or "").strip().lower().split())
	if not text:
		return False
	return any(
		token in text
		for token in (
			"analyze",
			"analysis",
			"evaluate",
			"health",
			"liquidity",
			"working capital",
			"compare",
		)
	)


def _currency_for_artifact(artifact: Dict[str, Any]) -> str:
	sections = artifact.get("sections") if isinstance(artifact.get("sections"), dict) else {}
	for section_name in ("summary", "bucket_totals", "parties"):
		values = sections.get(section_name)
		if not isinstance(values, list):
			continue
		for item in values:
			if not isinstance(item, dict):
				continue
			currency = str(item.get("currency") or "").strip()
			if currency:
				return currency
	return ""


def _amount(value: Any) -> float:
	if isinstance(value, (int, float)):
		return float(value)
	try:
		return float(str(value or "").strip().replace(",", ""))
	except Exception:
		return 0.0


def _percent(value: float) -> float:
	return round(value * 100.0, 1)


def _amount_text(amount: float, currency: str) -> str:
	clean_currency = str(currency or "").strip() or "MMK"
	return f"{amount:,.0f} {clean_currency}"


def _artifact_metric(artifact: Dict[str, Any], key: str) -> float:
	metrics = artifact.get("metrics") if isinstance(artifact.get("metrics"), dict) else {}
	return _amount(metrics.get(key))


def _artifact_period_to_date(artifact: Dict[str, Any]) -> str:
	period = artifact.get("period") if isinstance(artifact.get("period"), dict) else {}
	return str(period.get("to_date") or "").strip()


@dataclass(frozen=True)
class CompositeStepSpec:
	step_id: str
	family_id: str
	capability_id: str
	selected_report: str
	requested_dimensions: List[str] = field(default_factory=list)
	requested_metrics: List[str] = field(default_factory=list)
	requested_time_scope_strategy: str = ""


@dataclass(frozen=True)
class CompositePlanOutcome:
	status: str
	plan_contract: CompositeReadPlanContract | None = None
	compiler_contract: FreshQueryCompilerContract | None = None
	step_compiler_contracts: List[FreshQueryCompilerContract] = field(default_factory=list)
	step_compiled_requests: List[CompiledQueryRequestContract] = field(default_factory=list)
	errors: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class CompositeStepExecution:
	step_id: str
	family_id: str
	compiler_contract: Dict[str, Any]
	compiled_request: Dict[str, Any]
	runtime_payload: Dict[str, Any]
	artifact_payload: Dict[str, Any]
	family_validation_payload: Dict[str, Any]
	runtime_latency_ms: int


def _build_step_interpretation(
	*,
	request_id: str,
	session_id: str,
	interpretation: FreshQueryInterpretationContract,
	step: CompositeStepSpec,
) -> FreshQueryInterpretationContract:
	return build_fresh_query_interpretation_contract(
		request_id=request_id,
		session_id=session_id,
		intent_class=str(interpretation.intent_class or "").strip(),
		candidate_capability_ids=[step.capability_id],
		candidate_reports=[step.selected_report],
		requested_dimensions=list(step.requested_dimensions),
		requested_metrics=list(step.requested_metrics),
		requested_time_scope=_requested_time_scope(
			str(interpretation.requested_time_scope or "").strip(),
			step.requested_time_scope_strategy,
		),
		requested_presentation=[],
		extracted_slots=interpretation.extracted_slots if isinstance(interpretation.extracted_slots, dict) else {},
		ambiguity_flags=[],
		ambiguity_reason="",
		confidence=1.0,
	)


def _composite_profile_match(
	*,
	message: str,
	interpretation: FreshQueryInterpretationContract,
	spec: Dict[str, Any],
) -> bool:
	intent_class = str(interpretation.intent_class or "").strip()
	supported_intents = set(_clean_list(spec.get("supported_intent_classes")))
	if supported_intents and intent_class not in supported_intents:
		return False
	message_concepts = set(ontology_detect_concepts(message))
	required_all = set(_clean_list(spec.get("required_concepts_all")))
	if required_all and not required_all.issubset(message_concepts):
		return False
	preferred_any = set(_clean_list(spec.get("preferred_concepts_any")))
	if preferred_any and message_concepts and message_concepts & preferred_any:
		return True
	return bool(required_all)


def plan_composite_read(
	*,
	request_id: str,
	session_id: str,
	message: str,
	interpretation: FreshQueryInterpretationContract,
	response_policy: Dict[str, Any] | None = None,
) -> CompositePlanOutcome:
	matching_spec: Dict[str, Any] = {}
	for spec in list_composite_read_specs():
		if _composite_profile_match(message=message, interpretation=interpretation, spec=spec):
			matching_spec = spec
			break
	if not matching_spec:
		return CompositePlanOutcome(status="not_applicable")

	steps_raw = matching_spec.get("steps")
	if not isinstance(steps_raw, list) or not steps_raw:
		return CompositePlanOutcome(
			status="reject",
			errors=["Composite profile has no governed execution steps."],
		)

	step_specs: List[CompositeStepSpec] = []
	for item in steps_raw:
		if not isinstance(item, dict):
			continue
		step_specs.append(
			CompositeStepSpec(
				step_id=str(item.get("step_id") or "").strip(),
				family_id=str(item.get("family_id") or "").strip(),
				capability_id=str(item.get("capability_id") or "").strip(),
				selected_report=str(item.get("selected_report") or "").strip(),
				requested_dimensions=_clean_list(item.get("requested_dimensions")),
				requested_metrics=_clean_list(item.get("requested_metrics")),
				requested_time_scope_strategy=str(item.get("requested_time_scope_strategy") or "").strip(),
			)
		)
	step_specs = [
		item
		for item in step_specs
		if item.step_id and item.family_id and item.capability_id and item.selected_report
	]
	if not step_specs:
		return CompositePlanOutcome(
			status="reject",
			errors=["Composite profile did not produce any valid governed steps."],
		)

	step_compiler_contracts: List[FreshQueryCompilerContract] = []
	step_compiled_requests: List[CompiledQueryRequestContract] = []
	step_payloads: List[Dict[str, Any]] = []
	errors: List[str] = []
	for step in step_specs:
		step_request_id = f"{request_id}:{step.step_id}"
		step_interpretation = _build_step_interpretation(
			request_id=step_request_id,
			session_id=session_id,
			interpretation=interpretation,
			step=step,
		)
		step_outcome = compile_fresh_query(
			request_id=step_request_id,
			session_id=session_id,
			interpretation=step_interpretation,
			response_policy=response_policy if isinstance(response_policy, dict) else {},
		)
		step_compiler_contracts.append(step_outcome.compiler_contract)
		if step_outcome.compiled_request_contract is None or step_outcome.compiler_contract.decision != "execute":
			errors.append(
				f"Composite step `{step.step_id}` could not be executed: "
				f"{str(step_outcome.compiler_contract.compiler_reason or '').strip() or 'governed compilation failed.'}"
			)
			continue
		step_compiled_requests.append(step_outcome.compiled_request_contract)
		step_payloads.append(
			{
				"step_id": step.step_id,
				"family_id": step.family_id,
				"capability_id": step.capability_id,
				"selected_report": step.selected_report,
				"requested_dimensions": list(step_outcome.compiler_contract.requested_dimensions),
				"requested_metrics": list(step_outcome.compiler_contract.requested_metrics),
				"requested_time_scope": str(step_outcome.compiler_contract.requested_time_scope or "").strip(),
				"filters": dict(step_outcome.compiler_contract.completed_filters),
			}
		)

	decision = "execute" if not errors and len(step_payloads) == len(step_specs) else "clarify"
	plan_contract = build_composite_read_plan_contract(
		plan_id=str(matching_spec.get("plan_id") or "").strip(),
		request_id=request_id,
		decision=decision,
		steps=step_payloads,
		compiler_reason=(
			f"Compiler approved composite plan `{str(matching_spec.get('plan_label') or matching_spec.get('plan_id') or '').strip()}` "
			f"from governed concepts and step compilation."
			if decision == "execute"
			else " ".join(errors).strip()
		),
	)
	compiler_contract = build_fresh_query_compiler_contract(
		request_id=request_id,
		session_id=session_id,
		capability_id=f"composite::{str(plan_contract.plan_id or '').strip()}",
		selected_report="Composite Read",
		selected_report_family="composite_read",
		completed_filters={},
		requested_dimensions=list(interpretation.requested_dimensions),
		requested_metrics=list(interpretation.requested_metrics),
		requested_time_scope=str(interpretation.requested_time_scope or "").strip(),
		decision=decision,
		clarification_required=decision != "execute",
		compiler_reason=str(plan_contract.compiler_reason or "").strip(),
	)
	return CompositePlanOutcome(
		status=decision,
		plan_contract=plan_contract,
		compiler_contract=compiler_contract,
		step_compiler_contracts=step_compiler_contracts,
		step_compiled_requests=step_compiled_requests,
		errors=errors,
	)


def _execute_composite_step(
	*,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	compiled_request: CompiledQueryRequestContract,
	compiler_contract: FreshQueryCompilerContract,
	step_family_id: str,
	recent_messages: List[Dict[str, str]],
) -> CompositeStepExecution:
	runtime_started = time.perf_counter()
	try:
		runtime_payload = call_qwen_runtime_chat(
			session_id=f"{session_id}:{compiled_request.request_id}",
			user_id=user_id,
			site_name=site_name,
			message=message,
			recent_messages=list(recent_messages or []),
			response_policy=compiled_request.response_policy if isinstance(compiled_request.response_policy, dict) else {},
			mode="compiled_read_query",
			compiled_query=compiled_request.to_payload(),
			request_id=compiled_request.request_id,
		)
	except QwenRuntimeClientError as exc:
		runtime_payload = {
			"ok": False,
			"tool_trace": [],
			"agent_meta": {"engine": "unavailable", "mode": "compiled_read_query"},
			"error": str(exc),
		}
	runtime_latency_ms = int((time.perf_counter() - runtime_started) * 1000)
	adapter_outcome: FamilyArtifactOutcome = build_normalized_family_artifact(
		request_id=compiled_request.request_id,
		compiler_contract=compiler_contract.to_payload(),
		runtime_payload=runtime_payload,
		intent_class="",
		preferred_family_id=step_family_id,
	)
	artifact_payload = (
		adapter_outcome.artifact_contract.to_payload()
		if adapter_outcome.artifact_contract is not None
		else {}
	)
	family_validation: FamilyValidationOutcome | None = validate_normalized_family_artifact(
		request_id=compiled_request.request_id,
		compiler_contract=compiler_contract.to_payload(),
		artifact_contract=adapter_outcome.artifact_contract,
		family_id=adapter_outcome.family_id,
		adapter_errors=adapter_outcome.errors,
		adapter_warnings=adapter_outcome.warnings,
	)
	return CompositeStepExecution(
		step_id=compiled_request.request_id.split(":")[-1],
		family_id=step_family_id,
		compiler_contract=compiler_contract.to_payload(),
		compiled_request=compiled_request.to_payload(),
		runtime_payload=runtime_payload,
		artifact_payload=artifact_payload,
		family_validation_payload=family_validation.to_payload() if family_validation is not None else {},
		runtime_latency_ms=runtime_latency_ms,
	)


def _working_capital_health_summary(
	*,
	message: str,
	plan_id: str,
	step_results: List[CompositeStepExecution],
) -> Dict[str, Any]:
	receivable_artifact = {}
	payable_artifact = {}
	for item in step_results:
		artifact = item.artifact_payload if isinstance(item.artifact_payload, dict) else {}
		dimensions = artifact.get("dimensions") if isinstance(artifact.get("dimensions"), dict) else {}
		aging_type = str(dimensions.get("aging_type") or "").strip()
		if aging_type == "accounts_receivable":
			receivable_artifact = artifact
		if aging_type == "accounts_payable":
			payable_artifact = artifact

	receivable_total = _artifact_metric(receivable_artifact, "outstanding_total")
	payable_total = _artifact_metric(payable_artifact, "outstanding_total")
	receivable_overdue = _artifact_metric(receivable_artifact, "overdue_total")
	payable_overdue = _artifact_metric(payable_artifact, "overdue_total")
	receivable_overdue_ratio = _artifact_metric(receivable_artifact, "overdue_ratio")
	payable_overdue_ratio = _artifact_metric(payable_artifact, "overdue_ratio")
	net_gap = receivable_total - payable_total
	currency = _currency_for_artifact(receivable_artifact) or _currency_for_artifact(payable_artifact) or "MMK"
	report_date = _artifact_period_to_date(receivable_artifact) or _artifact_period_to_date(payable_artifact)

	health = "stable"
	if payable_total > receivable_total or receivable_overdue_ratio >= 0.5 or payable_overdue_ratio >= 0.4:
		health = "high_risk"
	elif receivable_overdue_ratio >= 0.25 or payable_overdue_ratio >= 0.25:
		health = "watch"

	observations: List[str] = []
	if payable_total > receivable_total:
		observations.append(
			f"Payables exceed receivables by {_amount_text(abs(net_gap), currency)}, indicating supplier-side working-capital pressure."
		)
	elif receivable_total > payable_total:
		observations.append(
			f"Receivables exceed payables by {_amount_text(abs(net_gap), currency)}, which improves working-capital coverage if collections convert on time."
		)
	if receivable_overdue_ratio >= 0.4:
		observations.append(
			f"Receivable overdue ratio is {_percent(receivable_overdue_ratio)}%, which is high for collection health."
		)
	if payable_overdue_ratio >= 0.35:
		observations.append(
			f"Payable overdue ratio is {_percent(payable_overdue_ratio)}%, suggesting supplier-payment stress."
		)
	if not observations:
		observations.append("AR and AP posture looks comparatively balanced in the normalized governed read.")

	lines = []
	title_suffix = f" as of {report_date}" if report_date else ""
	lines.append(f"AR/AP Working Capital Health{title_suffix}")
	lines.append("")
	lines.append(f"Accounts Receivable Outstanding: {_amount_text(receivable_total, currency)}")
	lines.append(f"Accounts Payable Outstanding: {_amount_text(payable_total, currency)}")
	lines.append(f"Net AR minus AP: {_amount_text(net_gap, currency)}")
	lines.append(f"AR Overdue Total: {_amount_text(receivable_overdue, currency)} ({_percent(receivable_overdue_ratio)}%)")
	lines.append(f"AP Overdue Total: {_amount_text(payable_overdue, currency)} ({_percent(payable_overdue_ratio)}%)")
	if _analysis_requested(message):
		lines.append("")
		lines.append(
			f"Health Assessment: {'HIGH RISK' if health == 'high_risk' else 'WATCH' if health == 'watch' else 'STABLE'}"
		)
		lines.append("")
		lines.append("Key Observations:")
		for observation in observations:
			lines.append(f"- {observation}")

	return {
		"type": "qwen_composite_family_artifact",
		"contract_version": "1.0",
		"plan_id": plan_id,
		"family_id": "composite_working_capital_health",
		"artifact_type": "normalized_composite_family_artifact",
		"period": {"to_date": report_date},
		"metrics": {
			"accounts_receivable_outstanding_total": receivable_total,
			"accounts_payable_outstanding_total": payable_total,
			"net_receivable_minus_payable": net_gap,
			"accounts_receivable_overdue_total": receivable_overdue,
			"accounts_payable_overdue_total": payable_overdue,
			"accounts_receivable_overdue_ratio": receivable_overdue_ratio,
			"accounts_payable_overdue_ratio": payable_overdue_ratio,
		},
		"sections": {
			"summary": observations,
		},
		"health_assessment": health,
		"answer_text": "\n".join(lines).strip(),
	}


def _composite_validation_payload(
	*,
	request_id: str,
	plan_contract: CompositeReadPlanContract,
	step_results: List[CompositeStepExecution],
	composite_artifact: Dict[str, Any],
) -> Dict[str, Any]:
	errors: List[str] = []
	warnings: List[str] = []
	completed_steps = 0
	periods: List[str] = []
	for item in step_results:
		family_validation = item.family_validation_payload if isinstance(item.family_validation_payload, dict) else {}
		status = str(family_validation.get("status") or "").strip()
		if status == "pass":
			completed_steps += 1
		else:
			errors.append(
				f"Composite step `{item.step_id}` did not pass family validation: "
				f"{status or 'unknown'}"
			)
		artifact = item.artifact_payload if isinstance(item.artifact_payload, dict) else {}
		period = artifact.get("period") if isinstance(artifact.get("period"), dict) else {}
		to_date = str(period.get("to_date") or "").strip()
		if to_date:
			periods.append(to_date)
	if len(set(periods)) > 1:
		warnings.append("Composite family artifacts did not align to one report date cleanly.")
	decision = "pass"
	if errors:
		decision = "reject_composite_incomplete"
	elif len(set(periods)) > 1:
		decision = "clarify"
	return {
		"type": "qwen_composite_read_validation",
		"contract_version": "1.0",
		"request_id": request_id,
		"plan_id": str(plan_contract.plan_id or "").strip(),
		"decision": decision,
		"step_count": len(plan_contract.steps),
		"completed_steps": completed_steps,
		"errors": errors,
		"warnings": warnings,
		"observed_metrics": sorted(
			str(key or "").strip()
			for key in (
				(composite_artifact.get("metrics") or {}).keys()
				if isinstance(composite_artifact.get("metrics"), dict)
				else []
			)
			if str(key or "").strip()
		),
		"created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
	}


def _composite_semantic_payload(
	*,
	request_id: str,
	plan_contract: CompositeReadPlanContract,
	validation_payload: Dict[str, Any],
) -> Dict[str, Any]:
	decision = str(validation_payload.get("decision") or "").strip()
	status = "pass"
	if decision == "clarify":
		status = "clarify"
	if decision == "reject_composite_incomplete":
		status = "reject_semantically_inconsistent"
	return {
		"type": "qwen_composite_semantic_validation",
		"contract_version": "1.0",
		"request_id": request_id,
		"plan_id": str(plan_contract.plan_id or "").strip(),
		"status": status,
		"errors": list(validation_payload.get("errors") or []),
		"warnings": list(validation_payload.get("warnings") or []),
		"created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
	}


def execute_composite_read_plan(
	*,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	recent_messages: List[Dict[str, str]],
	pipeline: Dict[str, Any],
	plan_outcome: CompositePlanOutcome,
	proposal_generation_latency_ms: int = 0,
	compilation_latency_ms: int = 0,
	total_started: float | None = None,
) -> Dict[str, Any]:
	request_id = str(pipeline.get("request_id") or "").strip()
	plan_contract = plan_outcome.plan_contract
	if plan_contract is None or plan_outcome.compiler_contract is None:
		return {}
	parallel_allowed = False
	for spec in list_composite_read_specs():
		if str(spec.get("plan_id") or "").strip() == str(plan_contract.plan_id or "").strip():
			parallel_allowed = bool(spec.get("parallel_execution_allowed"))
			break
	parallel_execution_used = False

	steps = list(zip(plan_outcome.step_compiler_contracts, plan_outcome.step_compiled_requests))
	step_results: List[CompositeStepExecution] = []

	def _run_step(pair: tuple[FreshQueryCompilerContract, CompiledQueryRequestContract]) -> CompositeStepExecution:
		compiler_contract, compiled_request = pair
		step_id = compiled_request.request_id.split(":")[-1]
		family_id = ""
		for item in plan_contract.steps:
			if not isinstance(item, dict):
				continue
			if str(item.get("step_id") or "").strip() == step_id:
				family_id = str(item.get("family_id") or "").strip()
				break
		return _execute_composite_step(
			session_id=session_id,
			user_id=user_id,
			site_name=site_name,
			message=message,
			compiled_request=compiled_request,
			compiler_contract=compiler_contract,
			step_family_id=family_id,
			recent_messages=recent_messages,
		)

	runtime_started = time.perf_counter()
	# Keep composite execution on the current worker thread for now.
	# Frappe configuration is thread-local in this runtime, so parallel child
	# threads can lose access to runtime base URL/auth state and fail before
	# governed report execution starts.
	step_results = [_run_step(item) for item in steps]
	runtime_execution_latency_ms = int((time.perf_counter() - runtime_started) * 1000)

	composite_artifact = _working_capital_health_summary(
		message=message,
		plan_id=str(plan_contract.plan_id or "").strip(),
		step_results=step_results,
	)
	validation_payload = _composite_validation_payload(
		request_id=request_id,
		plan_contract=plan_contract,
		step_results=step_results,
		composite_artifact=composite_artifact,
	)
	semantic_payload = _composite_semantic_payload(
		request_id=request_id,
		plan_contract=plan_contract,
		validation_payload=validation_payload,
	)
	tool_trace: List[Dict[str, Any]] = []
	tool_names: List[str] = []
	runtime_models: List[str] = []
	grounded_statuses: List[str] = []
	for item in step_results:
		runtime_payload = item.runtime_payload if isinstance(item.runtime_payload, dict) else {}
		trace = runtime_payload.get("tool_trace")
		if isinstance(trace, list):
			for tool_item in trace:
				if not isinstance(tool_item, dict):
					continue
				enriched = dict(tool_item)
				enriched["composite_step_id"] = item.step_id
				enriched["composite_family_id"] = item.family_id
				tool_trace.append(enriched)
				tool_name = str(enriched.get("tool") or "").strip()
				if tool_name:
					tool_names.append(tool_name)
		agent_meta = runtime_payload.get("agent_meta") if isinstance(runtime_payload.get("agent_meta"), dict) else {}
		model_name = str(agent_meta.get("model") or "").strip()
		if model_name:
			runtime_models.append(model_name)
		validation = agent_meta.get("validation") if isinstance(agent_meta.get("validation"), dict) else {}
		status = str(validation.get("status") or "").strip()
		if status:
			grounded_statuses.append(status)

	runtime_ok = str(validation_payload.get("decision") or "").strip() == "pass"
	overall_grounded_status = "pass" if grounded_statuses and all(item == "pass" for item in grounded_statuses) else "fail"
	total_pipeline_latency_ms = int((time.perf_counter() - total_started) * 1000) if total_started else 0
	overall_audit: CompiledExecutionAuditContract = build_compiled_execution_audit_contract(
		request_id=request_id,
		session_id=session_id,
		execution_mode="compiled_composite_read",
		compiler_decision=str(plan_outcome.compiler_contract.decision or "").strip(),
		compiler_reason=str(plan_outcome.compiler_contract.compiler_reason or "").strip(),
		capability_id=str(plan_outcome.compiler_contract.capability_id or "").strip(),
		selected_report=" + ".join(
			str(item.get("selected_report") or "").strip()
			for item in plan_contract.steps
			if isinstance(item, dict) and str(item.get("selected_report") or "").strip()
		),
		proposal_cache_hit=False,
		proposal_shared_inflight_hit=False,
		compiled_query_available=True,
		runtime_invoked=True,
		runtime_ok=runtime_ok,
		runtime_engine="composite_compiler",
		runtime_model=", ".join(sorted(set(runtime_models))),
		grounded_validation_status=overall_grounded_status,
		semantic_validation_status=str(semantic_payload.get("status") or "").strip(),
		semantic_validation_errors=list(semantic_payload.get("errors") or []),
		semantic_validation_warnings=list(semantic_payload.get("warnings") or []),
		proposal_generation_latency_ms=proposal_generation_latency_ms,
		compilation_latency_ms=compilation_latency_ms,
		runtime_execution_latency_ms=runtime_execution_latency_ms,
		semantic_validation_latency_ms=0,
		total_pipeline_latency_ms=total_pipeline_latency_ms,
		tool_count=len(tool_trace),
		tool_names=tool_names,
	)
	composite_execution_audit = {
		"type": "qwen_composite_execution_audit",
		"contract_version": "1.0",
		"request_id": request_id,
		"plan_id": str(plan_contract.plan_id or "").strip(),
		"step_count": len(plan_contract.steps),
		"completed_steps": int(validation_payload.get("completed_steps") or 0),
		"parallel_execution_allowed": parallel_allowed,
		"parallel_execution_used": parallel_execution_used,
		"runtime_execution_latency_ms": runtime_execution_latency_ms,
		"step_runtime_latency_ms": {
			item.step_id: item.runtime_latency_ms
			for item in step_results
		},
		"created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
	}
	return {
		"pipeline": pipeline,
		"composite_read_plan": plan_contract.to_payload(),
		"composite_step_runtime_payloads": [item.runtime_payload for item in step_results if isinstance(item.runtime_payload, dict)],
		"composite_family_artifacts": [item.artifact_payload for item in step_results if item.artifact_payload],
		"composite_step_validations": [item.family_validation_payload for item in step_results if item.family_validation_payload],
		"normalized_family_artifact": composite_artifact,
		"family_validation": {
			"status": str(validation_payload.get("decision") or "").strip(),
			"errors": list(validation_payload.get("errors") or []),
			"warnings": list(validation_payload.get("warnings") or []),
			"plan_id": str(plan_contract.plan_id or "").strip(),
		},
		"semantic_intent_validation": semantic_payload,
		"runtime_payload": {
			"ok": runtime_ok,
			"answer_text": str(composite_artifact.get("answer_text") or "").strip(),
			"tool_trace": tool_trace,
			"agent_meta": {
				"engine": "composite_compiler",
				"mode": "compiled_composite_read",
				"model": ", ".join(sorted(set(runtime_models))),
				"validation": {"status": overall_grounded_status},
				"composite_plan_id": str(plan_contract.plan_id or "").strip(),
			},
			"error": "",
		},
		"compiled_execution_audit": overall_audit.to_payload(),
		"composite_execution_audit": composite_execution_audit,
		"phase4_latency_breakdown": {
			"proposal_generation_latency_ms": proposal_generation_latency_ms,
			"compilation_latency_ms": compilation_latency_ms,
			"runtime_execution_latency_ms": runtime_execution_latency_ms,
			"semantic_validation_latency_ms": 0,
			"total_pipeline_latency_ms": total_pipeline_latency_ms,
		},
	}
