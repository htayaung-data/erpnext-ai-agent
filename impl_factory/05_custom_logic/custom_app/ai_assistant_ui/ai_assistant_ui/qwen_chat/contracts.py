from __future__ import annotations

import datetime as dt
import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.capability_adapters import (
	extract_grounded_table,
	supports_local_followup_mode,
)
from ai_assistant_ui.qwen_chat.followup_interpreter import (
	detect_followup_intent,
	is_million_transform_intent as _is_million_transform_intent,
	is_self_contained_business_request as _is_self_contained_business_request,
)
from ai_assistant_ui.qwen_chat.metadata import (
	resolve_followup_report_switch,
	resolve_target_report_for_capability,
)


def _utc_now() -> str:
	return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _safe_json_loads(value: Any) -> Any:
	if isinstance(value, (dict, list)):
		return value
	text = str(value or "").strip()
	if not text:
		return None
	try:
		return json.loads(text)
	except Exception:
		return None


def detect_language(text: str) -> str:
	value = str(text or "")
	has_myanmar = bool(re.search(r"[\u1000-\u109F\uA9E0-\uA9FF\uAA60-\uAA7F]", value))
	has_latin = bool(re.search(r"[A-Za-z]", value))
	if has_myanmar and has_latin:
		return "mixed"
	if has_myanmar:
		return "my"
	return "en"


def detect_explicit_analysis_request(text: str) -> bool:
	value = str(text or "").strip().lower()
	if not value:
		return False
	return bool(
		re.search(
			r"\b(analyze|analysis|insight|insights|interpret|interpretation|recommend|recommendation|compare|comparison|ratio|evaluate|evaluation)\b",
			value,
		)
	)


def is_million_transform_request(message: str) -> bool:
	return _is_million_transform_intent(message)

def is_self_contained_business_request(message: str) -> bool:
	return _is_self_contained_business_request(message)


@dataclass(frozen=True)
class InteractionContract:
	request_id: str
	session_id: str
	user_id: str
	site_name: str
	raw_message: str
	detected_language: str
	analysis_requested: bool = False
	response_policy_mode: str = "factual_default"
	ui_channel: str = "erpnext_qwen_chat"
	received_at: str = ""

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_interaction_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"session_id": self.session_id,
			"user_id": self.user_id,
			"site_name": self.site_name,
			"raw_message": self.raw_message,
			"detected_language": self.detected_language,
			"analysis_requested": self.analysis_requested,
			"response_policy_mode": self.response_policy_mode,
			"ui_channel": self.ui_channel,
			"received_at": self.received_at or _utc_now(),
		}


@dataclass(frozen=True)
class ResponsePolicyContract:
	request_id: str
	session_id: str
	analysis_requested: bool
	policy_mode: str
	insight_allowed: bool
	recommendation_allowed: bool
	grounding_rule: str
	structure: List[str]

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_response_policy_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"session_id": self.session_id,
			"analysis_requested": self.analysis_requested,
			"policy_mode": self.policy_mode,
			"insight_allowed": self.insight_allowed,
			"recommendation_allowed": self.recommendation_allowed,
			"grounding_rule": self.grounding_rule,
			"structure": self.structure,
			"created_at": _utc_now(),
		}

	def to_runtime_payload(self) -> Dict[str, Any]:
		return {
			"analysis_requested": self.analysis_requested,
			"policy_mode": self.policy_mode,
			"insight_allowed": self.insight_allowed,
			"recommendation_allowed": self.recommendation_allowed,
			"grounding_rule": self.grounding_rule,
			"structure": list(self.structure),
		}


@dataclass(frozen=True)
class FreshQueryInterpretationContract:
	request_id: str
	session_id: str
	intent_class: str
	candidate_capability_ids: List[str]
	candidate_reports: List[str]
	requested_dimensions: List[str]
	requested_metrics: List[str]
	requested_time_scope: str
	requested_presentation: List[str]
	extracted_slots: Dict[str, Any]
	ambiguity_flags: List[str]
	ambiguity_reason: str
	confidence: float

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_fresh_query_interpretation_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"session_id": self.session_id,
			"intent_class": self.intent_class,
			"candidate_capability_ids": list(self.candidate_capability_ids),
			"candidate_reports": list(self.candidate_reports),
			"requested_dimensions": list(self.requested_dimensions),
			"requested_metrics": list(self.requested_metrics),
			"requested_time_scope": self.requested_time_scope,
			"requested_presentation": list(self.requested_presentation),
			"extracted_slots": dict(self.extracted_slots),
			"ambiguity_flags": list(self.ambiguity_flags),
			"ambiguity_reason": self.ambiguity_reason,
			"confidence": float(max(0.0, min(1.0, self.confidence or 0.0))),
			"created_at": _utc_now(),
		}


@dataclass(frozen=True)
class FreshQueryCompilerContract:
	request_id: str
	session_id: str
	capability_id: str
	selected_report: str
	selected_report_family: str
	completed_filters: Dict[str, Any]
	requested_dimensions: List[str]
	requested_metrics: List[str]
	requested_time_scope: str
	decision: str
	clarification_required: bool
	compiler_reason: str

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_fresh_query_compiler_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"session_id": self.session_id,
			"capability_id": self.capability_id,
			"selected_report": self.selected_report,
			"selected_report_family": self.selected_report_family,
			"completed_filters": dict(self.completed_filters),
			"requested_dimensions": list(self.requested_dimensions),
			"requested_metrics": list(self.requested_metrics),
			"requested_time_scope": self.requested_time_scope,
			"decision": self.decision,
			"clarification_required": self.clarification_required,
			"compiler_reason": self.compiler_reason,
			"created_at": _utc_now(),
		}


@dataclass(frozen=True)
class CompiledQueryRequestContract:
	request_id: str
	capability_id: str
	selected_report: str
	filters: Dict[str, Any]
	requested_dimensions: List[str]
	requested_metrics: List[str]
	response_policy: Dict[str, Any]
	mode: str = "compiled_read_query"

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_compiled_query_request_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"mode": self.mode,
			"capability_id": self.capability_id,
			"selected_report": self.selected_report,
			"filters": dict(self.filters),
			"requested_dimensions": list(self.requested_dimensions),
			"requested_metrics": list(self.requested_metrics),
			"response_policy": dict(self.response_policy),
			"created_at": _utc_now(),
		}


@dataclass(frozen=True)
class SemanticIntentValidationContract:
	request_id: str
	requested_capability_id: str
	returned_report: str
	expected_semantic_tags: List[str]
	observed_semantic_tags: List[str]
	time_scope_match: bool
	dimension_match: bool
	decision: str

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_semantic_intent_validation_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"requested_capability_id": self.requested_capability_id,
			"returned_report": self.returned_report,
			"expected_semantic_tags": list(self.expected_semantic_tags),
			"observed_semantic_tags": list(self.observed_semantic_tags),
			"time_scope_match": self.time_scope_match,
			"dimension_match": self.dimension_match,
			"decision": self.decision,
			"created_at": _utc_now(),
		}


@dataclass(frozen=True)
class ReportFamilyContract:
	family_id: str
	family_label: str
	description: str
	supported_intent_classes: List[str]
	canonical_metrics: List[str]
	canonical_dimensions: List[str]
	adapter_id: str
	renderer_id: str
	composite_allowed: bool
	capability_ids: List[str]
	report_names: List[str]
	semantic_tags: List[str]
	validation_profile: str

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_report_family_contract",
			"contract_version": "1.0",
			"family_id": self.family_id,
			"family_label": self.family_label,
			"description": self.description,
			"supported_intent_classes": list(self.supported_intent_classes),
			"canonical_metrics": list(self.canonical_metrics),
			"canonical_dimensions": list(self.canonical_dimensions),
			"adapter_id": self.adapter_id,
			"renderer_id": self.renderer_id,
			"composite_allowed": self.composite_allowed,
			"capability_ids": list(self.capability_ids),
			"report_names": list(self.report_names),
			"semantic_tags": list(self.semantic_tags),
			"validation_profile": self.validation_profile,
			"created_at": _utc_now(),
		}


@dataclass(frozen=True)
class NormalizedFamilyArtifactContract:
	request_id: str
	family_id: str
	artifact_type: str
	source_reports: List[str]
	period: Dict[str, Any]
	filters: Dict[str, Any]
	dimensions: Dict[str, Any]
	metrics: Dict[str, Any]
	sections: Dict[str, Any]
	warnings: List[str]

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_normalized_family_artifact_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"family_id": self.family_id,
			"artifact_type": self.artifact_type,
			"source_reports": list(self.source_reports),
			"period": dict(self.period),
			"filters": dict(self.filters),
			"dimensions": dict(self.dimensions),
			"metrics": dict(self.metrics),
			"sections": dict(self.sections),
			"warnings": list(self.warnings),
			"created_at": _utc_now(),
		}


@dataclass(frozen=True)
class CompositeReadPlanContract:
	plan_id: str
	request_id: str
	decision: str
	steps: List[Dict[str, Any]]
	compiler_reason: str

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_composite_read_plan_contract",
			"contract_version": "1.0",
			"plan_id": self.plan_id,
			"request_id": self.request_id,
			"decision": self.decision,
			"steps": [dict(item) for item in self.steps if isinstance(item, dict)],
			"compiler_reason": self.compiler_reason,
			"created_at": _utc_now(),
		}


@dataclass(frozen=True)
class FamilyValidationContract:
	request_id: str
	family_id: str
	requested_metrics: List[str]
	observed_metrics: List[str]
	time_scope_match: bool
	family_schema_match: bool
	decision: str
	validation_errors: List[str]
	validation_warnings: List[str]

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_family_validation_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"family_id": self.family_id,
			"requested_metrics": list(self.requested_metrics),
			"observed_metrics": list(self.observed_metrics),
			"time_scope_match": self.time_scope_match,
			"family_schema_match": self.family_schema_match,
			"decision": self.decision,
			"validation_errors": list(self.validation_errors),
			"validation_warnings": list(self.validation_warnings),
			"created_at": _utc_now(),
		}


@dataclass(frozen=True)
class CompositeReadValidationContract:
	request_id: str
	plan_id: str
	status: str
	step_count: int
	completed_steps: int
	observed_metrics: List[str]
	validation_errors: List[str]
	validation_warnings: List[str]

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_composite_read_validation_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"plan_id": self.plan_id,
			"status": self.status,
			"step_count": int(max(0, self.step_count)),
			"completed_steps": int(max(0, self.completed_steps)),
			"observed_metrics": list(self.observed_metrics),
			"validation_errors": list(self.validation_errors),
			"validation_warnings": list(self.validation_warnings),
			"created_at": _utc_now(),
		}


@dataclass(frozen=True)
class RenderedFamilyResponseContract:
	request_id: str
	family_id: str
	renderer_id: str
	title: str
	answer_text: str
	source_reports: List[str]
	blocks: List[Dict[str, Any]]
	warnings: List[str]

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_rendered_family_response_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"family_id": self.family_id,
			"renderer_id": self.renderer_id,
			"title": self.title,
			"answer_text": self.answer_text,
			"source_reports": list(self.source_reports),
			"blocks": [dict(item) for item in self.blocks if isinstance(item, dict)],
			"warnings": list(self.warnings),
			"created_at": _utc_now(),
		}


@dataclass(frozen=True)
class FollowUpResolution:
	request_id: str
	mode: str
	requested_modes: List[str]
	target_dimension: str
	target_limit: int
	sort_direction: str
	target_capability_id: str
	target_report: str
	depends_on_grounded_turn: bool
	self_contained: bool
	latest_grounded_turn_available: bool
	reason: str

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_followup_resolution",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"mode": self.mode,
			"requested_modes": self.requested_modes,
			"target_dimension": self.target_dimension,
			"target_limit": self.target_limit,
			"sort_direction": self.sort_direction,
			"target_capability_id": self.target_capability_id,
			"target_report": self.target_report,
			"depends_on_grounded_turn": self.depends_on_grounded_turn,
			"self_contained": self.self_contained,
			"latest_grounded_turn_available": self.latest_grounded_turn_available,
			"reason": self.reason,
			"resolved_at": _utc_now(),
		}


@dataclass(frozen=True)
class ExecutionPath:
	request_id: str
	path: str
	reason: str
	requires_runtime: bool
	grounded_required: bool = True

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_execution_path",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"path": self.path,
			"reason": self.reason,
			"requires_runtime": self.requires_runtime,
			"grounded_required": self.grounded_required,
			"chosen_at": _utc_now(),
		}


@dataclass(frozen=True)
class GroundedTurnContext:
	request_id: str
	trace_request_id: str
	grounded: bool
	source_kind: str
	source_name: str
	company: str
	date_range: Dict[str, Any]
	filters: Dict[str, Any]
	dimensions: List[str]
	metrics: List[str]
	returned_schema: List[str]
	table_rows: List[Dict[str, Any]]
	row_count: int
	base_language: str
	transform_chain: List[str]

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"trace_request_id": self.trace_request_id,
			"grounded": self.grounded,
			"source_kind": self.source_kind,
			"source_name": self.source_name,
			"company": self.company,
			"date_range": self.date_range,
			"filters": self.filters,
			"dimensions": self.dimensions,
			"metrics": self.metrics,
			"returned_schema": self.returned_schema,
			"table_rows": self.table_rows,
			"row_count": self.row_count,
			"base_language": self.base_language,
			"transform_chain": self.transform_chain,
			"created_at": _utc_now(),
		}


@dataclass(frozen=True)
class AuditEnvelope:
	request_id: str
	session_id: str
	followup_mode: str
	execution_path: str
	grounded: bool
	source_kind: str
	source_name: str
	runtime_engine: str
	runtime_model: str
	runtime_latency_ms: int
	tool_count: int
	tool_names: List[str]
	validation_status: str
	validation_errors: List[str]
	answer_chars: int

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_audit_envelope",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"session_id": self.session_id,
			"followup_mode": self.followup_mode,
			"execution_path": self.execution_path,
			"grounded": self.grounded,
			"source_kind": self.source_kind,
			"source_name": self.source_name,
			"runtime_engine": self.runtime_engine,
			"runtime_model": self.runtime_model,
			"runtime_latency_ms": self.runtime_latency_ms,
			"tool_count": self.tool_count,
			"tool_names": self.tool_names,
			"validation_status": self.validation_status,
			"validation_errors": self.validation_errors,
			"answer_chars": self.answer_chars,
			"created_at": _utc_now(),
		}


@dataclass(frozen=True)
class CompiledExecutionAuditContract:
	request_id: str
	session_id: str
	execution_mode: str
	compiler_decision: str
	compiler_reason: str
	capability_id: str
	selected_report: str
	proposal_cache_hit: bool
	proposal_shared_inflight_hit: bool
	compiled_query_available: bool
	runtime_invoked: bool
	runtime_ok: bool
	runtime_engine: str
	runtime_model: str
	grounded_validation_status: str
	semantic_validation_status: str
	semantic_validation_errors: List[str]
	semantic_validation_warnings: List[str]
	proposal_generation_latency_ms: int
	compilation_latency_ms: int
	runtime_execution_latency_ms: int
	semantic_validation_latency_ms: int
	total_pipeline_latency_ms: int
	tool_count: int
	tool_names: List[str]

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_compiled_execution_audit_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"session_id": self.session_id,
			"execution_mode": self.execution_mode,
			"compiler_decision": self.compiler_decision,
			"compiler_reason": self.compiler_reason,
			"capability_id": self.capability_id,
			"selected_report": self.selected_report,
			"proposal_cache_hit": self.proposal_cache_hit,
			"proposal_shared_inflight_hit": self.proposal_shared_inflight_hit,
			"compiled_query_available": self.compiled_query_available,
			"runtime_invoked": self.runtime_invoked,
			"runtime_ok": self.runtime_ok,
			"runtime_engine": self.runtime_engine,
			"runtime_model": self.runtime_model,
			"grounded_validation_status": self.grounded_validation_status,
			"semantic_validation_status": self.semantic_validation_status,
			"semantic_validation_errors": list(self.semantic_validation_errors),
			"semantic_validation_warnings": list(self.semantic_validation_warnings),
			"proposal_generation_latency_ms": int(max(0, self.proposal_generation_latency_ms)),
			"compilation_latency_ms": int(max(0, self.compilation_latency_ms)),
			"runtime_execution_latency_ms": int(max(0, self.runtime_execution_latency_ms)),
			"semantic_validation_latency_ms": int(max(0, self.semantic_validation_latency_ms)),
			"total_pipeline_latency_ms": int(max(0, self.total_pipeline_latency_ms)),
			"tool_count": int(max(0, self.tool_count)),
			"tool_names": list(self.tool_names),
			"created_at": _utc_now(),
		}


def build_interaction_contract(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	raw_message: str,
) -> InteractionContract:
	analysis_requested = detect_explicit_analysis_request(raw_message)
	return InteractionContract(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		raw_message=raw_message,
		detected_language=detect_language(raw_message),
		analysis_requested=analysis_requested,
		response_policy_mode="explicit_analysis" if analysis_requested else "factual_default",
		received_at=_utc_now(),
	)


def build_response_policy_contract(
	*,
	interaction_contract: InteractionContract,
) -> ResponsePolicyContract:
	analysis_requested = bool(interaction_contract.analysis_requested)
	return ResponsePolicyContract(
		request_id=interaction_contract.request_id,
		session_id=interaction_contract.session_id,
		analysis_requested=analysis_requested,
		policy_mode="explicit_analysis" if analysis_requested else "factual_default",
		insight_allowed=True,
		recommendation_allowed=analysis_requested,
		grounding_rule="Business interpretation and recommendations must be grounded in ERP facts or explicit derived calculations.",
		structure=[
			"grounded_facts_first",
			"supporting_table_or_breakdown_when_relevant",
			"concise_interpretation_only_when_grounded",
			"recommendations_only_on_explicit_request",
		],
	)


def build_fresh_query_interpretation_contract(
	*,
	request_id: str,
	session_id: str,
	intent_class: str = "",
	candidate_capability_ids: List[str] | None = None,
	candidate_reports: List[str] | None = None,
	requested_dimensions: List[str] | None = None,
	requested_metrics: List[str] | None = None,
	requested_time_scope: str = "",
	requested_presentation: List[str] | None = None,
	extracted_slots: Dict[str, Any] | None = None,
	ambiguity_flags: List[str] | None = None,
	ambiguity_reason: str = "",
	confidence: float = 0.0,
) -> FreshQueryInterpretationContract:
	return FreshQueryInterpretationContract(
		request_id=request_id,
		session_id=session_id,
		intent_class=str(intent_class or "").strip(),
		candidate_capability_ids=[str(x or "").strip() for x in (candidate_capability_ids or []) if str(x or "").strip()],
		candidate_reports=[str(x or "").strip() for x in (candidate_reports or []) if str(x or "").strip()],
		requested_dimensions=[str(x or "").strip() for x in (requested_dimensions or []) if str(x or "").strip()],
		requested_metrics=[str(x or "").strip() for x in (requested_metrics or []) if str(x or "").strip()],
		requested_time_scope=str(requested_time_scope or "").strip(),
		requested_presentation=[str(x or "").strip() for x in (requested_presentation or []) if str(x or "").strip()],
		extracted_slots=dict(extracted_slots or {}),
		ambiguity_flags=[str(x or "").strip() for x in (ambiguity_flags or []) if str(x or "").strip()],
		ambiguity_reason=str(ambiguity_reason or "").strip(),
		confidence=float(max(0.0, min(1.0, confidence or 0.0))),
	)


def build_fresh_query_compiler_contract(
	*,
	request_id: str,
	session_id: str,
	capability_id: str = "",
	selected_report: str = "",
	selected_report_family: str = "",
	completed_filters: Dict[str, Any] | None = None,
	requested_dimensions: List[str] | None = None,
	requested_metrics: List[str] | None = None,
	requested_time_scope: str = "",
	decision: str = "clarify",
	clarification_required: bool = False,
	compiler_reason: str = "",
) -> FreshQueryCompilerContract:
	return FreshQueryCompilerContract(
		request_id=request_id,
		session_id=session_id,
		capability_id=str(capability_id or "").strip(),
		selected_report=str(selected_report or "").strip(),
		selected_report_family=str(selected_report_family or "").strip(),
		completed_filters=dict(completed_filters or {}),
		requested_dimensions=[str(x or "").strip() for x in (requested_dimensions or []) if str(x or "").strip()],
		requested_metrics=[str(x or "").strip() for x in (requested_metrics or []) if str(x or "").strip()],
		requested_time_scope=str(requested_time_scope or "").strip(),
		decision=str(decision or "clarify").strip(),
		clarification_required=bool(clarification_required),
		compiler_reason=str(compiler_reason or "").strip(),
	)


def build_compiled_query_request_contract(
	*,
	request_id: str,
	capability_id: str,
	selected_report: str,
	filters: Dict[str, Any] | None = None,
	requested_dimensions: List[str] | None = None,
	requested_metrics: List[str] | None = None,
	response_policy: Dict[str, Any] | None = None,
) -> CompiledQueryRequestContract:
	return CompiledQueryRequestContract(
		request_id=request_id,
		capability_id=str(capability_id or "").strip(),
		selected_report=str(selected_report or "").strip(),
		filters=dict(filters or {}),
		requested_dimensions=[str(x or "").strip() for x in (requested_dimensions or []) if str(x or "").strip()],
		requested_metrics=[str(x or "").strip() for x in (requested_metrics or []) if str(x or "").strip()],
		response_policy=dict(response_policy or {}),
	)


def build_semantic_intent_validation_contract(
	*,
	request_id: str,
	requested_capability_id: str,
	returned_report: str,
	expected_semantic_tags: List[str] | None = None,
	observed_semantic_tags: List[str] | None = None,
	time_scope_match: bool = False,
	dimension_match: bool = False,
	decision: str = "clarify",
) -> SemanticIntentValidationContract:
	return SemanticIntentValidationContract(
		request_id=request_id,
		requested_capability_id=str(requested_capability_id or "").strip(),
		returned_report=str(returned_report or "").strip(),
		expected_semantic_tags=[str(x or "").strip() for x in (expected_semantic_tags or []) if str(x or "").strip()],
		observed_semantic_tags=[str(x or "").strip() for x in (observed_semantic_tags or []) if str(x or "").strip()],
		time_scope_match=bool(time_scope_match),
		dimension_match=bool(dimension_match),
		decision=str(decision or "clarify").strip(),
	)


def build_report_family_contract(
	*,
	family_id: str,
	family_label: str = "",
	description: str = "",
	supported_intent_classes: List[str] | None = None,
	canonical_metrics: List[str] | None = None,
	canonical_dimensions: List[str] | None = None,
	adapter_id: str = "",
	renderer_id: str = "",
	composite_allowed: bool = False,
	capability_ids: List[str] | None = None,
	report_names: List[str] | None = None,
	semantic_tags: List[str] | None = None,
	validation_profile: str = "",
) -> ReportFamilyContract:
	return ReportFamilyContract(
		family_id=str(family_id or "").strip(),
		family_label=str(family_label or "").strip(),
		description=str(description or "").strip(),
		supported_intent_classes=[str(x or "").strip() for x in (supported_intent_classes or []) if str(x or "").strip()],
		canonical_metrics=[str(x or "").strip() for x in (canonical_metrics or []) if str(x or "").strip()],
		canonical_dimensions=[str(x or "").strip() for x in (canonical_dimensions or []) if str(x or "").strip()],
		adapter_id=str(adapter_id or "").strip(),
		renderer_id=str(renderer_id or "").strip(),
		composite_allowed=bool(composite_allowed),
		capability_ids=[str(x or "").strip() for x in (capability_ids or []) if str(x or "").strip()],
		report_names=[str(x or "").strip() for x in (report_names or []) if str(x or "").strip()],
		semantic_tags=[str(x or "").strip() for x in (semantic_tags or []) if str(x or "").strip()],
		validation_profile=str(validation_profile or "").strip(),
	)


def build_normalized_family_artifact_contract(
	*,
	request_id: str,
	family_id: str,
	artifact_type: str = "normalized_family_artifact",
	source_reports: List[str] | None = None,
	period: Dict[str, Any] | None = None,
	filters: Dict[str, Any] | None = None,
	dimensions: Dict[str, Any] | None = None,
	metrics: Dict[str, Any] | None = None,
	sections: Dict[str, Any] | None = None,
	warnings: List[str] | None = None,
) -> NormalizedFamilyArtifactContract:
	return NormalizedFamilyArtifactContract(
		request_id=str(request_id or "").strip(),
		family_id=str(family_id or "").strip(),
		artifact_type=str(artifact_type or "normalized_family_artifact").strip(),
		source_reports=[str(x or "").strip() for x in (source_reports or []) if str(x or "").strip()],
		period=dict(period or {}),
		filters=dict(filters or {}),
		dimensions=dict(dimensions or {}),
		metrics=dict(metrics or {}),
		sections=dict(sections or {}),
		warnings=[str(x or "").strip() for x in (warnings or []) if str(x or "").strip()],
	)


def build_composite_read_plan_contract(
	*,
	plan_id: str,
	request_id: str,
	decision: str = "clarify",
	steps: List[Dict[str, Any]] | None = None,
	compiler_reason: str = "",
) -> CompositeReadPlanContract:
	return CompositeReadPlanContract(
		plan_id=str(plan_id or "").strip(),
		request_id=str(request_id or "").strip(),
		decision=str(decision or "clarify").strip(),
		steps=[dict(item) for item in (steps or []) if isinstance(item, dict)],
		compiler_reason=str(compiler_reason or "").strip(),
	)


def build_family_validation_contract(
	*,
	request_id: str,
	family_id: str,
	requested_metrics: List[str] | None = None,
	observed_metrics: List[str] | None = None,
	time_scope_match: bool = False,
	family_schema_match: bool = False,
	decision: str = "clarify",
	validation_errors: List[str] | None = None,
	validation_warnings: List[str] | None = None,
) -> FamilyValidationContract:
	return FamilyValidationContract(
		request_id=str(request_id or "").strip(),
		family_id=str(family_id or "").strip(),
		requested_metrics=[str(x or "").strip() for x in (requested_metrics or []) if str(x or "").strip()],
		observed_metrics=[str(x or "").strip() for x in (observed_metrics or []) if str(x or "").strip()],
		time_scope_match=bool(time_scope_match),
		family_schema_match=bool(family_schema_match),
		decision=str(decision or "clarify").strip(),
		validation_errors=[str(x or "").strip() for x in (validation_errors or []) if str(x or "").strip()],
		validation_warnings=[str(x or "").strip() for x in (validation_warnings or []) if str(x or "").strip()],
	)


def build_composite_read_validation_contract(
	*,
	request_id: str,
	plan_id: str,
	status: str = "clarify",
	step_count: int = 0,
	completed_steps: int = 0,
	observed_metrics: List[str] | None = None,
	validation_errors: List[str] | None = None,
	validation_warnings: List[str] | None = None,
) -> CompositeReadValidationContract:
	return CompositeReadValidationContract(
		request_id=str(request_id or "").strip(),
		plan_id=str(plan_id or "").strip(),
		status=str(status or "clarify").strip(),
		step_count=int(max(0, step_count or 0)),
		completed_steps=int(max(0, completed_steps or 0)),
		observed_metrics=[str(x or "").strip() for x in (observed_metrics or []) if str(x or "").strip()],
		validation_errors=[str(x or "").strip() for x in (validation_errors or []) if str(x or "").strip()],
		validation_warnings=[str(x or "").strip() for x in (validation_warnings or []) if str(x or "").strip()],
	)


def build_rendered_family_response_contract(
	*,
	request_id: str,
	family_id: str,
	renderer_id: str = "",
	title: str = "",
	answer_text: str = "",
	source_reports: List[str] | None = None,
	blocks: List[Dict[str, Any]] | None = None,
	warnings: List[str] | None = None,
) -> RenderedFamilyResponseContract:
	return RenderedFamilyResponseContract(
		request_id=str(request_id or "").strip(),
		family_id=str(family_id or "").strip(),
		renderer_id=str(renderer_id or "").strip(),
		title=str(title or "").strip(),
		answer_text=str(answer_text or "").strip(),
		source_reports=[str(x or "").strip() for x in (source_reports or []) if str(x or "").strip()],
		blocks=[dict(item) for item in (blocks or []) if isinstance(item, dict)],
		warnings=[str(x or "").strip() for x in (warnings or []) if str(x or "").strip()],
	)


def build_compiled_execution_audit_contract(
	*,
	request_id: str,
	session_id: str,
	execution_mode: str = "compiled_first_turn",
	compiler_decision: str = "",
	compiler_reason: str = "",
	capability_id: str = "",
	selected_report: str = "",
	proposal_cache_hit: bool = False,
	proposal_shared_inflight_hit: bool = False,
	compiled_query_available: bool = False,
	runtime_invoked: bool = False,
	runtime_ok: bool = False,
	runtime_engine: str = "",
	runtime_model: str = "",
	grounded_validation_status: str = "",
	semantic_validation_status: str = "",
	semantic_validation_errors: List[str] | None = None,
	semantic_validation_warnings: List[str] | None = None,
	proposal_generation_latency_ms: int = 0,
	compilation_latency_ms: int = 0,
	runtime_execution_latency_ms: int = 0,
	semantic_validation_latency_ms: int = 0,
	total_pipeline_latency_ms: int = 0,
	tool_count: int = 0,
	tool_names: List[str] | None = None,
) -> CompiledExecutionAuditContract:
	return CompiledExecutionAuditContract(
		request_id=str(request_id or "").strip(),
		session_id=str(session_id or "").strip(),
		execution_mode=str(execution_mode or "compiled_first_turn").strip(),
		compiler_decision=str(compiler_decision or "").strip(),
		compiler_reason=str(compiler_reason or "").strip(),
		capability_id=str(capability_id or "").strip(),
		selected_report=str(selected_report or "").strip(),
		proposal_cache_hit=bool(proposal_cache_hit),
		proposal_shared_inflight_hit=bool(proposal_shared_inflight_hit),
		compiled_query_available=bool(compiled_query_available),
		runtime_invoked=bool(runtime_invoked),
		runtime_ok=bool(runtime_ok),
		runtime_engine=str(runtime_engine or "").strip(),
		runtime_model=str(runtime_model or "").strip(),
		grounded_validation_status=str(grounded_validation_status or "").strip(),
		semantic_validation_status=str(semantic_validation_status or "").strip(),
		semantic_validation_errors=[str(x or "").strip() for x in (semantic_validation_errors or []) if str(x or "").strip()],
		semantic_validation_warnings=[str(x or "").strip() for x in (semantic_validation_warnings or []) if str(x or "").strip()],
		proposal_generation_latency_ms=int(max(0, proposal_generation_latency_ms or 0)),
		compilation_latency_ms=int(max(0, compilation_latency_ms or 0)),
		runtime_execution_latency_ms=int(max(0, runtime_execution_latency_ms or 0)),
		semantic_validation_latency_ms=int(max(0, semantic_validation_latency_ms or 0)),
		total_pipeline_latency_ms=int(max(0, total_pipeline_latency_ms or 0)),
		tool_count=int(max(0, tool_count or 0)),
		tool_names=[str(x or "").strip() for x in (tool_names or []) if str(x or "").strip()],
	)


def build_followup_resolution(
	*,
	request_id: str,
	message: str,
	latest_grounded_turn_available: bool,
	latest_grounded_turn: Dict[str, Any] | None = None,
	semantic_intent: Any | None = None,
	allow_heuristic_fallback: bool = True,
	degraded_reason: str = "",
) -> FollowUpResolution:
	if semantic_intent is not None:
		requested_modes = list(getattr(semantic_intent, "requested_modes", []) or [])
		target_dimension = str(getattr(semantic_intent, "target_dimension", "") or "").strip()
		target_limit = int(max(0, getattr(semantic_intent, "target_limit", 0) or 0))
		sort_direction = str(getattr(semantic_intent, "sort_direction", "") or "").strip()
		target_capability_id = str(getattr(semantic_intent, "target_capability_id", "") or "").strip()
		self_contained = bool(getattr(semantic_intent, "self_contained", False))
		semantic_reason = str(getattr(semantic_intent, "reason", "") or "").strip()
	elif allow_heuristic_fallback:
		intent = detect_followup_intent(message, grounded_turn=latest_grounded_turn)
		requested_modes = intent.requested_modes
		target_dimension = intent.target_dimension
		target_limit = intent.target_limit
		sort_direction = intent.sort_direction
		target_capability_id = ""
		self_contained = _is_self_contained_business_request(message, grounded_turn=latest_grounded_turn, intent=intent)
		semantic_reason = ""
	else:
		requested_modes = []
		target_dimension = ""
		target_limit = 0
		sort_direction = ""
		target_capability_id = ""
		self_contained = False
		semantic_reason = ""
	grounded_turn = latest_grounded_turn if isinstance(latest_grounded_turn, dict) else {}
	local_grounded_modes = {"presentation_transform", "table_presentation"}
	if supports_local_followup_mode(grounded_turn, "aging_bucket_view"):
		local_grounded_modes.add("aging_bucket_view")
	if supports_local_followup_mode(grounded_turn, "dimension_breakdown", target_dimension=target_dimension):
		local_grounded_modes.add("dimension_breakdown")
	if supports_local_followup_mode(grounded_turn, "sort_or_limit"):
		local_grounded_modes.add("sort_or_limit")
	source_report = str(grounded_turn.get("source_name") or "").strip()
	switch = resolve_followup_report_switch(requested_modes, source_report) if latest_grounded_turn_available else {}
	target_report = ""
	if latest_grounded_turn_available and target_capability_id:
		target_report = resolve_target_report_for_capability(source_report, target_capability_id)

	if latest_grounded_turn_available and requested_modes and set(requested_modes).issubset(local_grounded_modes):
		return FollowUpResolution(
			request_id=request_id,
			mode="local_grounded_transform",
			requested_modes=requested_modes,
			target_dimension=target_dimension,
			target_limit=target_limit,
			sort_direction=sort_direction,
			target_capability_id="",
			target_report="",
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="The request can be resolved deterministically from the latest grounded answer using local capability adapters.",
		)
	if latest_grounded_turn_available and (target_report or switch):
		return FollowUpResolution(
			request_id=request_id,
			mode="capability_requery",
			requested_modes=requested_modes,
			target_dimension=target_dimension,
			target_limit=target_limit,
			sort_direction=sort_direction,
			target_capability_id=target_capability_id or str(switch.get("capability_id") or "").strip(),
			target_report=target_report or str(switch.get("target_report") or "").strip(),
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason=semantic_reason or "The request needs a governed report switch within the same business capability.",
		)
	if latest_grounded_turn_available and not self_contained:
		return FollowUpResolution(
			request_id=request_id,
			mode="grounded_follow_up",
			requested_modes=requested_modes,
			target_dimension=target_dimension,
			target_limit=target_limit,
			sort_direction=sort_direction,
			target_capability_id="",
			target_report="",
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason=degraded_reason or semantic_reason or "The request depends on prior grounded context and is not self-contained.",
		)
	return FollowUpResolution(
		request_id=request_id,
		mode="new_query",
		requested_modes=requested_modes,
		target_dimension=target_dimension,
		target_limit=target_limit,
		sort_direction=sort_direction,
		target_capability_id="",
		target_report="",
		depends_on_grounded_turn=False,
		self_contained=self_contained,
		latest_grounded_turn_available=latest_grounded_turn_available,
		reason=degraded_reason or semantic_reason or "The request is self-contained enough to be treated as a new ERP query.",
	)


def build_execution_path(
	*,
	request_id: str,
	followup_resolution: FollowUpResolution,
	local_transform_applied: bool,
) -> ExecutionPath:
	if local_transform_applied:
		return ExecutionPath(
			request_id=request_id,
			path="local_transform",
			reason="The follow-up was resolved deterministically from the existing grounded answer.",
			requires_runtime=False,
		)
	return ExecutionPath(
		request_id=request_id,
		path="erp_requery",
		reason="The assistant must use FAC/ERP tools to produce or refresh a grounded answer.",
		requires_runtime=True,
	)


def build_grounded_turn_context(
	*,
	request_id: str,
	interaction_contract: InteractionContract,
	assistant_payload: Dict[str, Any],
	runtime_payload: Dict[str, Any],
) -> GroundedTurnContext | None:
	tool_trace = runtime_payload.get("tool_trace")
	if not isinstance(tool_trace, list) or not tool_trace:
		return None

	report_tool = None
	for item in reversed(tool_trace):
		if not isinstance(item, dict):
			continue
		if str(item.get("tool") or "").strip() == "erp_fac-generate_report":
			report_tool = item
			break
	if report_tool is None:
		for item in reversed(tool_trace):
			if not isinstance(item, dict):
				continue
			if str(item.get("tool") or "").strip().startswith("erp_fac-"):
				report_tool = item
				break
	if report_tool is None:
		return None

	tool_name = str(report_tool.get("tool") or "").strip()
	tool_args = report_tool.get("detail_obj")
	if not isinstance(tool_args, dict):
		tool_args = _safe_json_loads(report_tool.get("detail"))
	if not isinstance(tool_args, dict):
		tool_args = {}

	filters = tool_args.get("filters")
	if not isinstance(filters, dict):
		filters = {}

	source_kind = "report" if tool_name == "erp_fac-generate_report" else "tool"
	source_name = str(tool_args.get("report_name") or tool_name or "").strip()
	date_range = {
		"from_date": filters.get("from_date"),
		"to_date": filters.get("to_date"),
		"report_date": filters.get("report_date"),
	}
	company = str(filters.get("company") or "").strip()

	tables = assistant_payload.get("tables")
	first_table = tables[0] if isinstance(tables, list) and tables and isinstance(tables[0], dict) else {}
	headers = first_table.get("headers") if isinstance(first_table.get("headers"), list) else []
	rows = first_table.get("rows") if isinstance(first_table.get("rows"), list) else []
	headers, rows = extract_grounded_table(report_tool, assistant_payload)

	dimensions: List[str] = []
	tree_type = str(filters.get("tree_type") or "").strip()
	if tree_type:
		dimensions.append(tree_type)
	if headers:
		first_header = str(headers[0] or "").strip()
		if first_header and first_header not in dimensions:
			dimensions.append(first_header)

	metrics: List[str] = []
	value_quantity = str(filters.get("value_quantity") or "").strip()
	if value_quantity:
		metrics.append(value_quantity)
	for header in headers[1:]:
		header_text = str(header or "").strip()
		if header_text and header_text not in metrics:
			metrics.append(header_text)

	trace_request_id = str(runtime_payload.get("request_id") or request_id).strip()
	return GroundedTurnContext(
		request_id=request_id,
		trace_request_id=trace_request_id,
		grounded=bool(runtime_payload.get("ok")),
		source_kind=source_kind,
		source_name=source_name,
		company=company,
		date_range=date_range,
		filters=filters,
		dimensions=dimensions,
		metrics=metrics,
		returned_schema=[str(x or "").strip() for x in headers if str(x or "").strip()],
		table_rows=[row for row in rows[:100] if isinstance(row, dict)],
		row_count=len(rows),
		base_language=interaction_contract.detected_language,
		transform_chain=[],
	)


def build_audit_envelope(
	*,
	interaction_contract: InteractionContract,
	followup_resolution: FollowUpResolution,
	execution_path: ExecutionPath,
	runtime_trace_payload: Dict[str, Any] | None,
	grounded_turn_context: Dict[str, Any] | None,
	answer_text: str,
) -> AuditEnvelope:
	trace = runtime_trace_payload if isinstance(runtime_trace_payload, dict) else {}
	grounded_turn = grounded_turn_context if isinstance(grounded_turn_context, dict) else {}
	agent_meta = trace.get("agent_meta") if isinstance(trace.get("agent_meta"), dict) else {}
	validation = agent_meta.get("validation") if isinstance(agent_meta.get("validation"), dict) else {}
	tool_trace = trace.get("tool_trace") if isinstance(trace.get("tool_trace"), list) else []
	tool_names = [
		str(item.get("tool") or "").strip()
		for item in tool_trace
		if isinstance(item, dict) and str(item.get("tool") or "").strip()
	]
	grounded = bool(grounded_turn.get("grounded"))
	if not grounded and execution_path.path == "local_transform" and bool(followup_resolution.depends_on_grounded_turn):
		grounded = True
	source_kind = str(grounded_turn.get("source_kind") or ("transform" if execution_path.path == "local_transform" else "")).strip()
	source_name = str(grounded_turn.get("source_name") or "").strip()
	validation_status = str(validation.get("status") or ("pass" if execution_path.path == "local_transform" else "unknown")).strip()
	validation_errors = validation.get("errors") if isinstance(validation.get("errors"), list) else []
	return AuditEnvelope(
		request_id=interaction_contract.request_id,
		session_id=interaction_contract.session_id,
		followup_mode=followup_resolution.mode,
		execution_path=execution_path.path,
		grounded=grounded,
		source_kind=source_kind,
		source_name=source_name,
		runtime_engine=str(agent_meta.get("engine") or "").strip(),
		runtime_model=str(agent_meta.get("model") or "").strip(),
		runtime_latency_ms=int(max(0, trace.get("runtime_latency_ms") or 0)),
		tool_count=len(tool_names),
		tool_names=tool_names,
		validation_status=validation_status,
		validation_errors=[str(x or "").strip() for x in validation_errors if str(x or "").strip()],
		answer_chars=len(str(answer_text or "").strip()),
	)
