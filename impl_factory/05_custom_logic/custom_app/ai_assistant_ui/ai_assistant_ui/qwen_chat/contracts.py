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
from ai_assistant_ui.qwen_chat.erp_metadata_discovery import get_report_surface_summary
from ai_assistant_ui.qwen_chat.metadata import (
	all_ontology_concepts,
	capability_default_report_name,
	capability_report_names,
	capability_semantic_tags,
	governed_self_contained_business_terms,
	get_frontdoor_intent_spec,
	ontology_detect_concepts,
	ontology_self_contained_prefixes,
	report_capability_ids,
	report_family_report_names,
	report_semantic_tags,
	report_supported_dimensions,
	report_supported_metrics,
	resolve_followup_report_switch,
	resolve_target_report_for_capability,
	list_capability_specs,
	supported_ontology_concepts,
)
from ai_assistant_ui.qwen_chat.response_policy import derive_response_policy
from ai_assistant_ui.qwen_chat.semantic_aliases import detect_canonical_keys, get_canonical_key
from ai_assistant_ui.qwen_chat.scope_decision_input import (
	ScopeDecisionInputContract,
	build_known_unsupported_scope_decision_input,
	build_scope_decision_input,
	normalize_scope_decision_input,
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


def _message_looks_like_self_contained_governed_business_query(
	*,
	message: str,
	language: str = "en",
) -> bool:
	text = " ".join(str(message or "").strip().lower().split())
	if not text:
		return False
	prefixes = [
		str(value or "").strip().lower()
		for value in ontology_self_contained_prefixes(language)
		if str(value or "").strip()
	]
	if prefixes and not any(text.startswith(prefix) for prefix in prefixes):
		return False
	if ontology_detect_concepts(text, language=language, include_extended=False):
		return True
	for term in governed_self_contained_business_terms(language):
		clean = str(term or "").strip().lower()
		if clean and re.search(rf"(?<!\\w){re.escape(clean)}(?!\\w)", text):
			return True
	return False

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
	answer_style: str
	direct_answer_first: bool
	highlight_allowed: bool
	implication_allowed: bool
	insight_allowed: bool
	recommendation_allowed: bool
	supporting_table_preference: str
	followup_conversational: bool
	grounding_rule: str
	structure: List[str]
	user_sections: List[str]
	preferred_formats: List[str]
	max_paragraph_sentences: int

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_response_policy_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"session_id": self.session_id,
			"analysis_requested": self.analysis_requested,
			"policy_mode": self.policy_mode,
			"answer_style": self.answer_style,
			"direct_answer_first": self.direct_answer_first,
			"highlight_allowed": self.highlight_allowed,
			"implication_allowed": self.implication_allowed,
			"insight_allowed": self.insight_allowed,
			"recommendation_allowed": self.recommendation_allowed,
			"supporting_table_preference": self.supporting_table_preference,
			"followup_conversational": self.followup_conversational,
			"grounding_rule": self.grounding_rule,
			"structure": self.structure,
			"user_sections": list(self.user_sections),
			"preferred_formats": list(self.preferred_formats),
			"max_paragraph_sentences": int(max(1, self.max_paragraph_sentences)),
			"created_at": _utc_now(),
		}

	def to_runtime_payload(self) -> Dict[str, Any]:
		return {
			"analysis_requested": self.analysis_requested,
			"policy_mode": self.policy_mode,
			"answer_style": self.answer_style,
			"direct_answer_first": self.direct_answer_first,
			"highlight_allowed": self.highlight_allowed,
			"implication_allowed": self.implication_allowed,
			"insight_allowed": self.insight_allowed,
			"recommendation_allowed": self.recommendation_allowed,
			"supporting_table_preference": self.supporting_table_preference,
			"followup_conversational": self.followup_conversational,
			"grounding_rule": self.grounding_rule,
			"structure": list(self.structure),
			"user_sections": list(self.user_sections),
			"preferred_formats": list(self.preferred_formats),
			"max_paragraph_sentences": int(max(1, self.max_paragraph_sentences)),
		}


@dataclass(frozen=True)
class ClarificationSignalContract:
	request_id: str
	stage: str
	reason_type: str
	user_question: str
	suggested_options: List[str]
	internal_reason: str
	internal_details: Dict[str, Any]

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_clarification_signal_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"stage": self.stage,
			"reason_type": self.reason_type,
			"user_question": self.user_question,
			"suggested_options": list(self.suggested_options),
			"internal_reason": self.internal_reason,
			"internal_details": dict(self.internal_details),
			"created_at": _utc_now(),
		}


@dataclass(frozen=True)
class ClarificationReasonContract:
	request_id: str
	stage: str
	source_contract_type: str
	reason_type: str
	clarification_required: bool
	blocking: bool
	recommended_next_lane: str
	primary_domain: str
	missing_fields: List[str]
	ambiguity_flags: List[str]
	candidate_capability_ids: List[str]
	candidate_reports: List[str]
	suggested_options: List[str]
	internal_reason: str
	internal_details: Dict[str, Any]

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_clarification_reason_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"stage": self.stage,
			"source_contract_type": self.source_contract_type,
			"reason_type": self.reason_type,
			"clarification_required": self.clarification_required,
			"blocking": self.blocking,
			"recommended_next_lane": self.recommended_next_lane,
			"primary_domain": self.primary_domain,
			"missing_fields": list(self.missing_fields),
			"ambiguity_flags": list(self.ambiguity_flags),
			"candidate_capability_ids": list(self.candidate_capability_ids),
			"candidate_reports": list(self.candidate_reports),
			"suggested_options": list(self.suggested_options),
			"internal_reason": self.internal_reason,
			"internal_details": dict(self.internal_details),
			"created_at": _utc_now(),
		}


@dataclass(frozen=True)
class ClarificationResolutionContract:
	request_id: str
	session_id: str
	pending_stage: str
	pending_reason_type: str
	pending_user_question: str
	pending_suggested_options: List[str]
	decision: str
	resolved_option: str
	matched_by: str
	confidence: float
	reason: str
	resolved_slot: Dict[str, Any]
	clarification_attempt_count: int
	is_final_attempt: bool

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_clarification_resolution_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"session_id": self.session_id,
			"pending_stage": self.pending_stage,
			"pending_reason_type": self.pending_reason_type,
			"pending_user_question": self.pending_user_question,
			"pending_suggested_options": list(self.pending_suggested_options),
			"decision": self.decision,
			"resolved_option": self.resolved_option,
			"matched_by": self.matched_by,
			"confidence": max(0.0, min(1.0, float(self.confidence))),
			"reason": self.reason,
			"resolved_slot": dict(self.resolved_slot),
			"clarification_attempt_count": int(max(0, self.clarification_attempt_count)),
			"is_final_attempt": bool(self.is_final_attempt),
			"created_at": _utc_now(),
		}


@dataclass(frozen=True)
class SemanticResolutionContract:
	request_id: str
	session_id: str
	intent_class: str
	primary_business_area: str
	resolved_slots: Dict[str, str]
	slot_confidence: Dict[str, float]
	candidate_family_ids: List[str]
	candidate_capability_ids: List[str]
	candidate_reports: List[str]
	ambiguity_flags: List[str]
	ambiguity_reason: str
	resolution_source: Dict[str, str]
	governed_decision: str
	governed_reason: str

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_semantic_resolution_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"session_id": self.session_id,
			"intent_class": self.intent_class,
			"primary_business_area": self.primary_business_area,
			"resolved_slots": {
				str(key): str(value)
				for key, value in dict(self.resolved_slots).items()
				if str(key or "").strip()
			},
			"slot_confidence": {
				str(key): float(value)
				for key, value in dict(self.slot_confidence).items()
				if str(key or "").strip()
			},
			"candidate_family_ids": [
				str(value) for value in list(self.candidate_family_ids) if str(value or "").strip()
			],
			"candidate_capability_ids": [
				str(value) for value in list(self.candidate_capability_ids) if str(value or "").strip()
			],
			"candidate_reports": [
				str(value) for value in list(self.candidate_reports) if str(value or "").strip()
			],
			"ambiguity_flags": [
				str(value) for value in list(self.ambiguity_flags) if str(value or "").strip()
			],
			"ambiguity_reason": self.ambiguity_reason,
			"resolution_source": {
				str(key): str(value)
				for key, value in dict(self.resolution_source).items()
				if str(key or "").strip()
			},
			"governed_decision": self.governed_decision,
			"governed_reason": self.governed_reason,
			"created_at": _utc_now(),
		}


@dataclass(frozen=True)
class FinancialSummaryResolutionContract:
	request_id: str
	session_id: str
	intent_class: str
	resolved_summary_domains: List[str]
	resolved_summary_focus: str
	resolved_summary_metric_family: str
	resolved_summary_grain: str
	resolved_time_scope: str
	decision: str
	target_intent_class: str
	target_composite_plan_id: str
	ambiguity_flags: List[str]
	ambiguity_reason: str
	decision_reason: str
	candidate_capability_ids: List[str]
	candidate_reports: List[str]

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_financial_summary_resolution_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"session_id": self.session_id,
			"intent_class": self.intent_class,
			"resolved_summary_domains": list(self.resolved_summary_domains),
			"resolved_summary_focus": self.resolved_summary_focus,
			"resolved_summary_metric_family": self.resolved_summary_metric_family,
			"resolved_summary_grain": self.resolved_summary_grain,
			"resolved_time_scope": self.resolved_time_scope,
			"decision": self.decision,
			"target_intent_class": self.target_intent_class,
			"target_composite_plan_id": self.target_composite_plan_id,
			"ambiguity_flags": list(self.ambiguity_flags),
			"ambiguity_reason": self.ambiguity_reason,
			"decision_reason": self.decision_reason,
			"candidate_capability_ids": list(self.candidate_capability_ids),
			"candidate_reports": list(self.candidate_reports),
			"created_at": _utc_now(),
		}


@dataclass(frozen=True)
class ERPBusinessReasoningActivationContract:
	request_id: str
	session_id: str
	grounded_context_available: bool
	grounded_source_request_id: str
	grounded_source_kind: str
	grounded_source_name: str
	grounded_family_id: str
	grounded_artifact_type: str
	grounded_source_reports: List[str]
	grounded_capability_id: str
	grounded_semantic_tags: List[str]
	grounding_summary: Dict[str, Any]
	recommendation_allowed: bool
	recommendation_policy_basis: List[str]
	allowed_reasoning_types: List[str]
	activation_state: str
	route_target: str
	reason: str

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_erp_business_reasoning_activation_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"session_id": self.session_id,
			"grounded_context_available": bool(self.grounded_context_available),
			"grounded_source_request_id": self.grounded_source_request_id,
			"grounded_source_kind": self.grounded_source_kind,
			"grounded_source_name": self.grounded_source_name,
			"grounded_family_id": self.grounded_family_id,
			"grounded_artifact_type": self.grounded_artifact_type,
			"grounded_source_reports": list(self.grounded_source_reports),
			"grounded_capability_id": self.grounded_capability_id,
			"grounded_semantic_tags": list(self.grounded_semantic_tags),
			"grounding_summary": dict(self.grounding_summary),
			"recommendation_allowed": bool(self.recommendation_allowed),
			"recommendation_policy_basis": list(self.recommendation_policy_basis),
			"allowed_reasoning_types": list(self.allowed_reasoning_types),
			"activation_state": self.activation_state,
			"route_target": self.route_target,
			"reason": self.reason,
			"created_at": _utc_now(),
		}


@dataclass(frozen=True)
class ERPBusinessReasoningContract:
	request_id: str
	session_id: str
	reasoning_type: str
	grounding_source_request_id: str
	grounding_source_kind: str
	grounding_family_id: str
	grounding_artifact_type: str
	grounding_source_reports: List[str]
	grounding_sufficient: bool
	grounding_gaps: List[str]
	bounded_domain: str
	reasoning_scope: str
	supported_claims: List[Dict[str, Any]]
	recommendations: List[Dict[str, Any]]
	speculation_flags: List[str]
	allowed_to_answer: bool
	reason: str
	confidence: float

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_erp_business_reasoning_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"session_id": self.session_id,
			"reasoning_type": self.reasoning_type,
			"grounding_source_request_id": self.grounding_source_request_id,
			"grounding_source_kind": self.grounding_source_kind,
			"grounding_family_id": self.grounding_family_id,
			"grounding_artifact_type": self.grounding_artifact_type,
			"grounding_source_reports": list(self.grounding_source_reports),
			"grounding_sufficient": bool(self.grounding_sufficient),
			"grounding_gaps": list(self.grounding_gaps),
			"bounded_domain": self.bounded_domain,
			"reasoning_scope": self.reasoning_scope,
			"supported_claims": [dict(item) for item in self.supported_claims if isinstance(item, dict)],
			"recommendations": [dict(item) for item in self.recommendations if isinstance(item, dict)],
			"speculation_flags": list(self.speculation_flags),
			"allowed_to_answer": bool(self.allowed_to_answer),
			"reason": self.reason,
			"confidence": float(max(0.0, min(1.0, self.confidence))),
			"created_at": _utc_now(),
		}


@dataclass(frozen=True)
class KnowledgeBoundaryContract:
	request_id: str
	session_id: str
	proposed_lane: str
	final_lane: str
	boundary_status: str
	lane_appropriate: bool
	valid_erp_domain: bool
	grounding_required: bool
	grounding_available: bool
	knowledge_coverage_state: str
	reclassification_reason: str
	boundary_flags: List[str]
	allowed_to_answer: bool
	safe_next_action: str
	user_response_mode: str
	confidence: float

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_knowledge_boundary_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"session_id": self.session_id,
			"proposed_lane": self.proposed_lane,
			"final_lane": self.final_lane,
			"boundary_status": self.boundary_status,
			"lane_appropriate": bool(self.lane_appropriate),
			"valid_erp_domain": bool(self.valid_erp_domain),
			"grounding_required": bool(self.grounding_required),
			"grounding_available": bool(self.grounding_available),
			"knowledge_coverage_state": self.knowledge_coverage_state,
			"reclassification_reason": self.reclassification_reason,
			"boundary_flags": list(self.boundary_flags),
			"allowed_to_answer": bool(self.allowed_to_answer),
			"safe_next_action": self.safe_next_action,
			"user_response_mode": self.user_response_mode,
			"confidence": float(max(0.0, min(1.0, self.confidence))),
			"created_at": _utc_now(),
		}


@dataclass(frozen=True)
class ArtifactEnrichmentRecoveryContract:
	request_id: str
	session_id: str
	source_request_id: str
	source_family_id: str
	source_capability_id: str
	source_report: str
	failure_type: str
	recovery_state: str
	available_recovery_actions: List[str]
	recommended_recovery_action: str
	preservable_scope: Dict[str, Any]
	preservable_dimensions: List[str]
	preservable_metrics: List[str]
	preservable_time_context: Dict[str, Any]
	alternative_capability_id: str
	alternative_report: str
	reason: str
	allowed_to_recover: bool
	confidence: float

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_artifact_enrichment_recovery_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"session_id": self.session_id,
			"source_request_id": self.source_request_id,
			"source_family_id": self.source_family_id,
			"source_capability_id": self.source_capability_id,
			"source_report": self.source_report,
			"failure_type": self.failure_type,
			"recovery_state": self.recovery_state,
			"available_recovery_actions": list(self.available_recovery_actions),
			"recommended_recovery_action": self.recommended_recovery_action,
			"preservable_scope": dict(self.preservable_scope),
			"preservable_dimensions": list(self.preservable_dimensions),
			"preservable_metrics": list(self.preservable_metrics),
			"preservable_time_context": dict(self.preservable_time_context),
			"alternative_capability_id": self.alternative_capability_id,
			"alternative_report": self.alternative_report,
			"reason": self.reason,
			"allowed_to_recover": bool(self.allowed_to_recover),
			"confidence": float(max(0.0, min(1.0, self.confidence))),
			"created_at": _utc_now(),
		}


@dataclass(frozen=True)
class ConversationalRepairIntentContract:
	request_id: str
	session_id: str
	repair_intent_type: str
	repair_state: str
	targets_prior_recovery: bool
	accepted_recovery_action: str
	guidance_topic: str
	fresh_query_override: bool
	preserve_scope: bool
	preserve_entity_dimension: bool
	preserve_time_context: bool
	reason: str
	allowed_next_lane: str
	confidence: float

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_conversational_repair_intent_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"session_id": self.session_id,
			"repair_intent_type": self.repair_intent_type,
			"repair_state": self.repair_state,
			"targets_prior_recovery": bool(self.targets_prior_recovery),
			"accepted_recovery_action": self.accepted_recovery_action,
			"guidance_topic": self.guidance_topic,
			"fresh_query_override": bool(self.fresh_query_override),
			"preserve_scope": bool(self.preserve_scope),
			"preserve_entity_dimension": bool(self.preserve_entity_dimension),
			"preserve_time_context": bool(self.preserve_time_context),
			"reason": self.reason,
			"allowed_next_lane": self.allowed_next_lane,
			"confidence": float(max(0.0, min(1.0, self.confidence))),
			"created_at": _utc_now(),
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
	target_limit: int = 0

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
			"target_limit": int(max(0, self.target_limit or 0)),
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
	governed_resolution_details: Dict[str, Any]
	clarification_reason_type: str
	clarification_details: Dict[str, Any]
	target_limit: int = 0

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_fresh_query_compiler_contract",
			"contract_version": "1.1",
			"request_id": self.request_id,
			"session_id": self.session_id,
			"capability_id": self.capability_id,
			"selected_report": self.selected_report,
			"selected_report_family": self.selected_report_family,
			"completed_filters": dict(self.completed_filters),
			"requested_dimensions": list(self.requested_dimensions),
			"requested_metrics": list(self.requested_metrics),
			"requested_time_scope": self.requested_time_scope,
			"target_limit": int(max(0, self.target_limit or 0)),
			"decision": self.decision,
			"clarification_required": self.clarification_required,
			"compiler_reason": self.compiler_reason,
			"governed_resolution_details": dict(self.governed_resolution_details),
			"clarification_reason_type": self.clarification_reason_type,
			"clarification_details": dict(self.clarification_details),
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
	target_limit: int = 0
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
			"target_limit": int(max(0, self.target_limit or 0)),
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
class ArtifactNarrativeResponseContract:
	request_id: str
	family_id: str
	narrative_engine: str
	answer_style: str
	answer_text: str
	source_reports: List[str]
	support_block_count: int
	warnings: List[str]

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_artifact_narrative_response_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"family_id": self.family_id,
			"narrative_engine": self.narrative_engine,
			"answer_style": self.answer_style,
			"answer_text": self.answer_text,
			"source_reports": list(self.source_reports),
			"support_block_count": int(max(0, self.support_block_count)),
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
	target_metric: str
	requested_columns: List[str]
	requested_time_scope: str
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
			"target_metric": self.target_metric,
			"requested_columns": list(self.requested_columns),
			"requested_time_scope": self.requested_time_scope,
			"target_capability_id": self.target_capability_id,
			"target_report": self.target_report,
			"depends_on_grounded_turn": self.depends_on_grounded_turn,
			"self_contained": self.self_contained,
			"latest_grounded_turn_available": self.latest_grounded_turn_available,
			"reason": self.reason,
			"resolved_at": _utc_now(),
		}


def build_followup_resolution_contract(
	*,
	request_id: str,
	mode: str,
	requested_modes: List[str] | None = None,
	target_dimension: str = "",
	target_limit: int = 0,
	sort_direction: str = "",
	target_metric: str = "",
	requested_columns: List[str] | None = None,
	requested_time_scope: str = "",
	target_capability_id: str = "",
	target_report: str = "",
	depends_on_grounded_turn: bool = False,
	self_contained: bool = False,
	latest_grounded_turn_available: bool = False,
	reason: str = "",
) -> FollowUpResolution:
	return FollowUpResolution(
		request_id=str(request_id or "").strip(),
		mode=str(mode or "").strip(),
		requested_modes=[str(value or "").strip() for value in (requested_modes or []) if str(value or "").strip()],
		target_dimension=str(target_dimension or "").strip(),
		target_limit=int(max(0, target_limit or 0)),
		sort_direction=str(sort_direction or "").strip(),
		target_metric=str(target_metric or "").strip(),
		requested_columns=[str(value or "").strip() for value in (requested_columns or []) if str(value or "").strip()],
		requested_time_scope=str(requested_time_scope or "").strip(),
		target_capability_id=str(target_capability_id or "").strip(),
		target_report=str(target_report or "").strip(),
		depends_on_grounded_turn=bool(depends_on_grounded_turn),
		self_contained=bool(self_contained),
		latest_grounded_turn_available=bool(latest_grounded_turn_available),
		reason=str(reason or "").strip(),
	)


def build_followup_boundary_contract(
	*,
	request_id: str,
	session_id: str,
	source_family_id: str = "",
	source_report_name: str = "",
	grounded_context_domains: List[str] | None = None,
	requested_domains: List[str] | None = None,
	structured_followup_modes: List[str] | None = None,
	structured_business_signals_present: bool = False,
	grounded_followup_supported: bool = False,
	self_contained_signal: bool = False,
	contradictory_payload: bool = False,
	degraded_message_fallback_allowed: bool = False,
	degraded_message_fallback_used: bool = False,
	out_of_scope_signal: bool = False,
	primary_domain: str = "",
	domain_affinity: str = "unknown",
	recommended_boundary_decision: str = "fail_closed_to_reasoning",
	decision_reason: str = "",
	resolution_source: Dict[str, str] | None = None,
) -> FollowUpBoundaryContract:
	allowed_affinity = {"same_domain", "partial_overlap", "disjoint", "unknown"}
	allowed_decisions = {"stay_grounded", "force_fresh_query", "fail_closed_to_reasoning"}
	clean_affinity = str(domain_affinity or "unknown").strip() or "unknown"
	if clean_affinity not in allowed_affinity:
		clean_affinity = "unknown"
	clean_decision = str(recommended_boundary_decision or "fail_closed_to_reasoning").strip() or "fail_closed_to_reasoning"
	if clean_decision not in allowed_decisions:
		clean_decision = "fail_closed_to_reasoning"
	return FollowUpBoundaryContract(
		request_id=str(request_id or "").strip(),
		session_id=str(session_id or "").strip(),
		source_family_id=str(source_family_id or "").strip(),
		source_report_name=str(source_report_name or "").strip(),
		grounded_context_domains=list(
			dict.fromkeys(
				str(value or "").strip()
				for value in (grounded_context_domains or [])
				if str(value or "").strip()
			)
		),
		requested_domains=list(
			dict.fromkeys(
				str(value or "").strip()
				for value in (requested_domains or [])
				if str(value or "").strip()
			)
		),
		structured_followup_modes=list(
			dict.fromkeys(
				str(value or "").strip()
				for value in (structured_followup_modes or [])
				if str(value or "").strip()
			)
		),
		structured_business_signals_present=bool(structured_business_signals_present),
		grounded_followup_supported=bool(grounded_followup_supported),
		self_contained_signal=bool(self_contained_signal),
		contradictory_payload=bool(contradictory_payload),
		degraded_message_fallback_allowed=bool(degraded_message_fallback_allowed),
		degraded_message_fallback_used=bool(degraded_message_fallback_used),
		out_of_scope_signal=bool(out_of_scope_signal),
		primary_domain=str(primary_domain or "").strip(),
		domain_affinity=clean_affinity,
		recommended_boundary_decision=clean_decision,
		decision_reason=str(decision_reason or "").strip(),
		resolution_source={
			str(key): str(value)
			for key, value in dict(resolution_source or {}).items()
			if str(key or "").strip()
		},
	)


def clone_followup_resolution(
	resolution: FollowUpResolution,
	*,
	request_id: str = "",
	mode: str | None = None,
	requested_modes: List[str] | None = None,
	target_dimension: str | None = None,
	target_limit: int | None = None,
	sort_direction: str | None = None,
	target_metric: str | None = None,
	requested_columns: List[str] | None = None,
	requested_time_scope: str | None = None,
	target_capability_id: str | None = None,
	target_report: str | None = None,
	depends_on_grounded_turn: bool | None = None,
	self_contained: bool | None = None,
	latest_grounded_turn_available: bool | None = None,
	reason: str | None = None,
) -> FollowUpResolution:
	return build_followup_resolution_contract(
		request_id=request_id or str(getattr(resolution, "request_id", "") or "").strip(),
		mode=str(mode if mode is not None else getattr(resolution, "mode", "") or "").strip(),
		requested_modes=(
			requested_modes
			if requested_modes is not None
			else list(getattr(resolution, "requested_modes", []) or [])
		),
		target_dimension=(
			target_dimension
			if target_dimension is not None
			else str(getattr(resolution, "target_dimension", "") or "").strip()
		),
		target_limit=(
			target_limit
			if target_limit is not None
			else int(max(0, getattr(resolution, "target_limit", 0) or 0))
		),
		sort_direction=(
			sort_direction
			if sort_direction is not None
			else str(getattr(resolution, "sort_direction", "") or "").strip()
		),
		target_metric=(
			target_metric
			if target_metric is not None
			else str(getattr(resolution, "target_metric", "") or "").strip()
		),
		requested_columns=(
			requested_columns
			if requested_columns is not None
			else list(getattr(resolution, "requested_columns", []) or [])
		),
		requested_time_scope=(
			requested_time_scope
			if requested_time_scope is not None
			else str(getattr(resolution, "requested_time_scope", "") or "").strip()
		),
		target_capability_id=(
			target_capability_id
			if target_capability_id is not None
			else str(getattr(resolution, "target_capability_id", "") or "").strip()
		),
		target_report=(
			target_report
			if target_report is not None
			else str(getattr(resolution, "target_report", "") or "").strip()
		),
		depends_on_grounded_turn=(
			depends_on_grounded_turn
			if depends_on_grounded_turn is not None
			else bool(getattr(resolution, "depends_on_grounded_turn", False))
		),
		self_contained=(
			self_contained
			if self_contained is not None
			else bool(getattr(resolution, "self_contained", False))
		),
		latest_grounded_turn_available=(
			latest_grounded_turn_available
			if latest_grounded_turn_available is not None
			else bool(getattr(resolution, "latest_grounded_turn_available", False))
		),
		reason=reason if reason is not None else str(getattr(resolution, "reason", "") or "").strip(),
	)


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
	artifact_family_id: str = ""
	artifact_type: str = ""
	artifact_source_reports: List[str] = None
	known_entities: List[Dict[str, Any]] = None
	known_documents: List[str] = None

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
			"artifact_family_id": self.artifact_family_id,
			"artifact_type": self.artifact_type,
			"artifact_source_reports": list(self.artifact_source_reports or []),
			"known_entities": [dict(item) for item in (self.known_entities or []) if isinstance(item, dict)],
			"known_documents": [str(item or "").strip() for item in (self.known_documents or []) if str(item or "").strip()],
			"created_at": _utc_now(),
		}


@dataclass(frozen=True)
class FollowUpBoundaryContract:
	request_id: str
	session_id: str
	source_family_id: str
	source_report_name: str
	grounded_context_domains: List[str]
	requested_domains: List[str]
	structured_followup_modes: List[str]
	structured_business_signals_present: bool
	grounded_followup_supported: bool
	self_contained_signal: bool
	contradictory_payload: bool
	degraded_message_fallback_allowed: bool
	degraded_message_fallback_used: bool
	out_of_scope_signal: bool
	primary_domain: str
	domain_affinity: str
	recommended_boundary_decision: str
	decision_reason: str
	resolution_source: Dict[str, str]

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_followup_boundary_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"session_id": self.session_id,
			"source_family_id": self.source_family_id,
			"source_report_name": self.source_report_name,
			"grounded_context_domains": list(self.grounded_context_domains),
			"requested_domains": list(self.requested_domains),
			"structured_followup_modes": list(self.structured_followup_modes),
			"structured_business_signals_present": bool(self.structured_business_signals_present),
			"grounded_followup_supported": bool(self.grounded_followup_supported),
			"self_contained_signal": bool(self.self_contained_signal),
			"contradictory_payload": bool(self.contradictory_payload),
			"degraded_message_fallback_allowed": bool(self.degraded_message_fallback_allowed),
			"degraded_message_fallback_used": bool(self.degraded_message_fallback_used),
			"out_of_scope_signal": bool(self.out_of_scope_signal),
			"primary_domain": str(self.primary_domain or "").strip(),
			"domain_affinity": self.domain_affinity,
			"recommended_boundary_decision": self.recommended_boundary_decision,
			"decision_reason": self.decision_reason,
			"resolution_source": {
				str(key): str(value)
				for key, value in dict(self.resolution_source).items()
				if str(key or "").strip()
			},
			"created_at": _utc_now(),
		}


@dataclass(frozen=True)
class ArtifactContinuationContract:
	request_id: str
	source_family_id: str
	source_capability_id: str
	source_report: str
	source_artifact_type: str
	source_dimension: str
	source_metric_key: str
	source_requested_columns: List[str]
	source_available_columns: List[str]
	source_row_count: int
	source_limit: int
	source_sort_direction: str
	source_time_scope: str
	continuation_mode: str
	preserve_grounded_context: bool
	preserve_metric_context: bool
	preserve_projection_shape: bool
	preserve_date_context: bool
	preserved_dimension: str
	preserved_metric_key: str
	preserved_requested_columns: List[str]
	preserved_limit: int
	preserved_sort_direction: str
	preserved_time_scope: str
	preserved_report_date: str
	preserved_from_date: str
	preserved_to_date: str
	preserve_rank_membership: bool
	preserve_rank_order: bool
	preserved_entities: List[str]
	requested_modes: List[str]
	reason: str

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_artifact_continuation_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"source_family_id": self.source_family_id,
			"source_capability_id": self.source_capability_id,
			"source_report": self.source_report,
			"source_artifact_type": self.source_artifact_type,
			"source_dimension": self.source_dimension,
			"source_metric_key": self.source_metric_key,
			"source_requested_columns": list(self.source_requested_columns),
			"source_available_columns": list(self.source_available_columns),
			"source_row_count": int(max(0, self.source_row_count)),
			"source_limit": int(max(0, self.source_limit)),
			"source_sort_direction": self.source_sort_direction,
			"source_time_scope": self.source_time_scope,
			"continuation_mode": self.continuation_mode,
			"preserve_grounded_context": self.preserve_grounded_context,
			"preserve_metric_context": self.preserve_metric_context,
			"preserve_projection_shape": self.preserve_projection_shape,
			"preserve_date_context": self.preserve_date_context,
			"preserved_dimension": self.preserved_dimension,
			"preserved_metric_key": self.preserved_metric_key,
			"preserved_requested_columns": list(self.preserved_requested_columns),
			"preserved_limit": int(max(0, self.preserved_limit)),
			"preserved_sort_direction": self.preserved_sort_direction,
			"preserved_time_scope": self.preserved_time_scope,
			"preserved_report_date": self.preserved_report_date,
			"preserved_from_date": self.preserved_from_date,
			"preserved_to_date": self.preserved_to_date,
			"preserve_rank_membership": self.preserve_rank_membership,
			"preserve_rank_order": self.preserve_rank_order,
			"preserved_entities": list(self.preserved_entities),
			"requested_modes": list(self.requested_modes),
			"reason": self.reason,
			"created_at": _utc_now(),
		}


@dataclass(frozen=True)
class GovernedScopeDecisionContract:
	request_id: str
	stage: str
	governed_scope_status: str
	execution_mode: str
	reason: str
	requested_domains: List[str]
	context_domains: List[str]
	known_request_domains: List[str]
	supported_request_domains: List[str]
	unsupported_known_request_domains: List[str]
	latest_grounded_turn_available: bool
	preserve_grounded_context: bool
	self_contained: bool
	out_of_scope: bool
	clarification_required: bool
	primary_domain: str
	recommended_next_lane: str
	target_capability_id: str
	target_report: str

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_governed_scope_decision_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"stage": self.stage,
			"governed_scope_status": self.governed_scope_status,
			"execution_mode": self.execution_mode,
			"reason": self.reason,
			"requested_domains": list(self.requested_domains),
			"context_domains": list(self.context_domains),
			"known_request_domains": list(self.known_request_domains),
			"supported_request_domains": list(self.supported_request_domains),
			"unsupported_known_request_domains": list(self.unsupported_known_request_domains),
			"latest_grounded_turn_available": self.latest_grounded_turn_available,
			"preserve_grounded_context": self.preserve_grounded_context,
			"self_contained": self.self_contained,
			"out_of_scope": self.out_of_scope,
			"clarification_required": self.clarification_required,
			"primary_domain": self.primary_domain,
			"recommended_next_lane": self.recommended_next_lane,
			"target_capability_id": self.target_capability_id,
			"target_report": self.target_report,
			"created_at": _utc_now(),
		}


@dataclass(frozen=True)
class ArtifactEnrichmentCompatibilityContract:
	request_id: str
	source_family_id: str
	source_capability_id: str
	source_report: str
	source_dimension: str
	target_metric: str
	requested_columns: List[str]
	required_metric_keys: List[str]
	compatibility_status: str
	compatible: bool
	target_capability_id: str
	target_report: str
	candidate_reports_considered: List[str]
	source_surface_sources: List[str]
	source_selector_filters: List[str]
	reason: str

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_artifact_enrichment_compatibility_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"source_family_id": self.source_family_id,
			"source_capability_id": self.source_capability_id,
			"source_report": self.source_report,
			"source_dimension": self.source_dimension,
			"target_metric": self.target_metric,
			"requested_columns": list(self.requested_columns),
			"required_metric_keys": list(self.required_metric_keys),
			"compatibility_status": self.compatibility_status,
			"compatible": bool(self.compatible),
			"target_capability_id": self.target_capability_id,
			"target_report": self.target_report,
			"candidate_reports_considered": list(self.candidate_reports_considered),
			"source_surface_sources": list(self.source_surface_sources),
			"source_selector_filters": list(self.source_selector_filters),
			"reason": self.reason,
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
class FamilyToolSurfaceContract:
	request_id: str
	session_id: str
	candidate_family_ids: List[str]
	preferred_tool_ids: List[str]
	allowed_report_names: List[str]
	report_discovery_allowed: bool
	reason: str
	family_entries: List[Dict[str, Any]]

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_family_tool_surface_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"session_id": self.session_id,
			"candidate_family_ids": list(self.candidate_family_ids),
			"preferred_tool_ids": list(self.preferred_tool_ids),
			"allowed_report_names": list(self.allowed_report_names),
			"report_discovery_allowed": self.report_discovery_allowed,
			"reason": self.reason,
			"family_entries": [dict(item) for item in self.family_entries if isinstance(item, dict)],
			"created_at": _utc_now(),
		}

	def to_runtime_payload(self) -> Dict[str, Any]:
		return {
			"candidate_family_ids": list(self.candidate_family_ids),
			"preferred_tool_ids": list(self.preferred_tool_ids),
			"allowed_report_names": list(self.allowed_report_names),
			"report_discovery_allowed": self.report_discovery_allowed,
			"reason": self.reason,
			"family_entries": [dict(item) for item in self.family_entries if isinstance(item, dict)],
		}


@dataclass(frozen=True)
class FrontDoorIntentGateContract:
	request_id: str
	intent_class: str
	confidence: float
	handle_in_front_door: bool
	response_mode: str
	response_payload: Dict[str, Any]
	route_target: str
	reason: str

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_front_door_intent_gate_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"intent_class": self.intent_class,
			"confidence": float(max(0.0, min(1.0, self.confidence))),
			"handle_in_front_door": bool(self.handle_in_front_door),
			"response_mode": self.response_mode,
			"response_payload": dict(self.response_payload),
			"route_target": self.route_target,
			"reason": self.reason,
			"created_at": _utc_now(),
		}

	def to_runtime_payload(self) -> Dict[str, Any]:
		return {
			"intent_class": self.intent_class,
			"confidence": float(max(0.0, min(1.0, self.confidence))),
			"handle_in_front_door": bool(self.handle_in_front_door),
			"response_mode": self.response_mode,
			"response_payload": dict(self.response_payload),
			"route_target": self.route_target,
			"reason": self.reason,
		}


@dataclass(frozen=True)
class CompiledExecutionAuditContract:
	request_id: str
	session_id: str
	execution_mode: str
	compiler_decision: str
	compiler_reason: str
	governed_resolution_details: Dict[str, Any]
	capability_id: str
	selected_report: str
	governed_family_id: str
	composite_plan_id: str
	proposal_cache_hit: bool
	proposal_shared_inflight_hit: bool
	compiled_query_available: bool
	runtime_invoked: bool
	runtime_ok: bool
	runtime_engine: str
	runtime_model: str
	grounded_validation_status: str
	family_validation_status: str
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
			"contract_version": "1.1",
			"request_id": self.request_id,
			"session_id": self.session_id,
			"execution_mode": self.execution_mode,
			"compiler_decision": self.compiler_decision,
			"compiler_reason": self.compiler_reason,
			"governed_resolution_details": dict(self.governed_resolution_details),
			"capability_id": self.capability_id,
			"selected_report": self.selected_report,
			"governed_family_id": self.governed_family_id,
			"composite_plan_id": self.composite_plan_id,
			"proposal_cache_hit": self.proposal_cache_hit,
			"proposal_shared_inflight_hit": self.proposal_shared_inflight_hit,
			"compiled_query_available": self.compiled_query_available,
			"runtime_invoked": self.runtime_invoked,
			"runtime_ok": self.runtime_ok,
			"runtime_engine": self.runtime_engine,
			"runtime_model": self.runtime_model,
			"grounded_validation_status": self.grounded_validation_status,
			"family_validation_status": self.family_validation_status,
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


def _front_door_capability_summary_payload() -> Dict[str, Any]:
	capability_labels = []
	for item in list_capability_specs():
		label = str(item.get("label") or "").strip()
		if label and label not in capability_labels:
			capability_labels.append(label)
	supported_areas = [
		"financial statements",
		"AR / AP",
		"sales",
		"inventory",
		"product performance",
		"invoices",
	]
	text = (
		"I can help with governed ERP reporting and follow-up analysis across "
		+ ", ".join(supported_areas[:-1])
		+ ", and "
		+ supported_areas[-1]
		+ "."
	)
	return {
		"text": text,
		"supported_areas": supported_areas,
		"capability_labels": capability_labels,
		"suggested_prompts": [
			"Show me sales trend",
			"Analyze AR / AP",
			"Give me the financial statement",
		],
	}


def translate_front_door_intent_gate_contract(
	*,
	intent_class: str,
	response_mode: str,
	grounded_context_available: bool = False,
) -> Dict[str, Any]:
	intent = str(intent_class or "").strip()
	mode = str(response_mode or "").strip()
	if mode == "capability_summary":
		return _front_door_capability_summary_payload()
	if mode == "continue_current_flow":
		if grounded_context_available:
			return {
				"text": "I can continue the current ERP context. Ask for more details, another view, or a new governed query.",
				"suggested_prompts": [
					"Give me more details",
					"Show another view",
					"Start a new query",
				],
			}
		return {
			"text": "There is no current governed result to continue yet. Ask a new ERP question and I can start from there.",
			"suggested_prompts": [
				"Show me sales trend",
				"Analyze inventory",
				"Give me the financial statement",
			],
		}
	text_by_intent = {
		"greeting": "I can help with governed ERP reports and follow-up analysis. What would you like to look at?",
		"thanks": "You're welcome. If you want, I can continue the current ERP analysis or start a new governed query.",
		"acknowledgement": "Okay. When you're ready, ask for the next ERP view or a new governed query.",
		"closure_signoff": "Understood. Feel free to come back anytime, and we can pick up from a new ERP question or continue from there.",
		"governed_kpi_definition": "I can explain governed KPI definitions and approved formula bases from the active business-definition registry.",
		"low_signal_non_business": "That request is outside this ERP/business assistant. I’m ready when you want to return to the current ERP analysis or continue with an ERP question or follow-up.",
		"route_onward": "",
	}
	return {
		"text": str(text_by_intent.get(intent) or "").strip(),
		"suggested_prompts": [],
	}


def build_front_door_intent_gate_contract(
	*,
	request_id: str,
	intent_class: str,
	confidence: float,
	grounded_context_available: bool = False,
	reason: str = "",
) -> FrontDoorIntentGateContract:
	intent = str(intent_class or "").strip() or "route_onward"
	spec = get_frontdoor_intent_spec(intent)
	if not spec:
		spec = get_frontdoor_intent_spec("route_onward")
		intent = str(spec.get("intent_class_id") or "route_onward").strip()
	response_mode = str(spec.get("response_mode") or "route_onward").strip()
	route_target = str(spec.get("route_target") or "artifact_lane").strip()
	handle_in_front_door = bool(spec.get("handle_in_front_door", False))
	final_reason = str(reason or "").strip()
	if bool(spec.get("requires_grounded_context")) and not grounded_context_available:
		intent = "route_onward"
		spec = get_frontdoor_intent_spec(intent)
		response_mode = str(spec.get("response_mode") or "route_onward").strip()
		route_target = str(spec.get("route_target") or "artifact_lane").strip()
		handle_in_front_door = bool(spec.get("handle_in_front_door", False))
		final_reason = "The turn looks like session flow, but there is no grounded context yet, so it should route onward."
	response_payload = translate_front_door_intent_gate_contract(
		intent_class=intent,
		response_mode=response_mode,
		grounded_context_available=grounded_context_available,
	)
	return FrontDoorIntentGateContract(
		request_id=str(request_id or "").strip(),
		intent_class=intent,
		confidence=float(max(0.0, min(1.0, confidence))),
		handle_in_front_door=handle_in_front_door,
		response_mode=response_mode,
		response_payload=dict(response_payload),
		route_target=route_target,
		reason=final_reason,
	)


def build_response_policy_contract(
	*,
	interaction_contract: InteractionContract,
	followup_resolution: "FollowUpResolution | None" = None,
) -> ResponsePolicyContract:
	analysis_requested = bool(interaction_contract.analysis_requested)
	followup_mode = ""
	self_contained = True
	if followup_resolution is not None:
		followup_mode = str(getattr(followup_resolution, "mode", "") or "").strip()
		self_contained = bool(getattr(followup_resolution, "self_contained", True))
	policy = derive_response_policy(
		raw_message=interaction_contract.raw_message,
		analysis_requested=analysis_requested,
		followup_mode=followup_mode,
		self_contained=self_contained,
	)
	return ResponsePolicyContract(
		request_id=interaction_contract.request_id,
		session_id=interaction_contract.session_id,
		analysis_requested=analysis_requested,
		policy_mode=str(policy.get("policy_mode") or "factual_default").strip(),
		answer_style=str(policy.get("answer_style") or "simple_factual").strip(),
		direct_answer_first=bool(policy.get("direct_answer_first", True)),
		highlight_allowed=bool(policy.get("highlight_allowed", True)),
		implication_allowed=bool(policy.get("implication_allowed", False)),
		insight_allowed=bool(policy.get("insight_allowed", True)),
		recommendation_allowed=bool(policy.get("recommendation_allowed", analysis_requested)),
		supporting_table_preference=str(policy.get("supporting_table_preference") or "when_helpful").strip(),
		followup_conversational=bool(policy.get("followup_conversational", False)),
		grounding_rule=str(
			policy.get("grounding_rule")
			or "Business interpretation and recommendations must be grounded in ERP facts or explicit derived calculations."
		).strip(),
		structure=[str(x or "").strip() for x in (policy.get("structure") or []) if str(x or "").strip()],
		user_sections=[str(x or "").strip() for x in (policy.get("user_sections") or []) if str(x or "").strip()],
		preferred_formats=[str(x or "").strip() for x in (policy.get("preferred_formats") or []) if str(x or "").strip()],
		max_paragraph_sentences=int(max(1, policy.get("max_paragraph_sentences") or 2)),
	)


def build_clarification_signal_contract(
	*,
	request_id: str,
	stage: str,
	reason_type: str,
	user_question: str,
	suggested_options: List[str] | None = None,
	internal_reason: str = "",
	internal_details: Dict[str, Any] | None = None,
) -> ClarificationSignalContract:
	return ClarificationSignalContract(
		request_id=str(request_id or "").strip(),
		stage=str(stage or "").strip(),
		reason_type=str(reason_type or "").strip(),
		user_question=str(user_question or "").strip(),
		suggested_options=[str(x or "").strip() for x in (suggested_options or []) if str(x or "").strip()],
		internal_reason=str(internal_reason or "").strip(),
		internal_details=dict(internal_details or {}),
	)


def build_clarification_reason_contract(
	*,
	request_id: str,
	stage: str,
	source_contract_type: str,
	reason_type: str,
	clarification_required: bool = True,
	blocking: bool = True,
	recommended_next_lane: str = "clarification",
	primary_domain: str = "",
	missing_fields: List[str] | None = None,
	ambiguity_flags: List[str] | None = None,
	candidate_capability_ids: List[str] | None = None,
	candidate_reports: List[str] | None = None,
	suggested_options: List[str] | None = None,
	internal_reason: str = "",
	internal_details: Dict[str, Any] | None = None,
) -> ClarificationReasonContract:
	return ClarificationReasonContract(
		request_id=str(request_id or "").strip(),
		stage=str(stage or "").strip(),
		source_contract_type=str(source_contract_type or "").strip(),
		reason_type=str(reason_type or "").strip(),
		clarification_required=bool(clarification_required),
		blocking=bool(blocking),
		recommended_next_lane=str(recommended_next_lane or "clarification").strip() or "clarification",
		primary_domain=str(primary_domain or "").strip(),
		missing_fields=[str(x or "").strip() for x in (missing_fields or []) if str(x or "").strip()],
		ambiguity_flags=[str(x or "").strip() for x in (ambiguity_flags or []) if str(x or "").strip()],
		candidate_capability_ids=[str(x or "").strip() for x in (candidate_capability_ids or []) if str(x or "").strip()],
		candidate_reports=[str(x or "").strip() for x in (candidate_reports or []) if str(x or "").strip()],
		suggested_options=[str(x or "").strip() for x in (suggested_options or []) if str(x or "").strip()],
		internal_reason=str(internal_reason or "").strip(),
		internal_details=dict(internal_details or {}),
	)


def build_clarification_resolution_contract(
	*,
	request_id: str,
	session_id: str = "",
	pending_stage: str,
	pending_reason_type: str,
	pending_user_question: str = "",
	pending_suggested_options: List[str] | None = None,
	decision: str,
	resolved_option: str = "",
	matched_by: str = "",
	confidence: float = 0.0,
	reason: str = "",
	resolved_slot: Dict[str, Any] | None = None,
	clarification_attempt_count: int = 0,
	is_final_attempt: bool = False,
) -> ClarificationResolutionContract:
	return ClarificationResolutionContract(
		request_id=str(request_id or "").strip(),
		session_id=str(session_id or "").strip(),
		pending_stage=str(pending_stage or "").strip(),
		pending_reason_type=str(pending_reason_type or "").strip(),
		pending_user_question=str(pending_user_question or "").strip(),
		pending_suggested_options=[
			str(x or "").strip()
			for x in (pending_suggested_options or [])
			if str(x or "").strip()
		],
		decision=str(decision or "").strip(),
		resolved_option=str(resolved_option or "").strip(),
		matched_by=str(matched_by or "").strip(),
		confidence=max(0.0, min(1.0, float(confidence or 0.0))),
		reason=str(reason or "").strip(),
		resolved_slot=dict(resolved_slot or {}),
		clarification_attempt_count=int(max(0, clarification_attempt_count or 0)),
		is_final_attempt=bool(is_final_attempt),
	)


def build_clarification_response_resolution_contract(
	*,
	request_id: str,
	pending_stage: str,
	pending_reason_type: str,
	decision: str,
	resolved_option: str = "",
	matched_by: str = "",
	reason: str = "",
) -> ClarificationResolutionContract:
	# Backward-compatible wrapper for the earlier transitional contract surface.
	return build_clarification_resolution_contract(
		request_id=request_id,
		pending_stage=pending_stage,
		pending_reason_type=pending_reason_type,
		decision=decision,
		resolved_option=resolved_option,
		matched_by=matched_by,
		confidence=1.0 if str(decision or "").strip() == "resolved_option" else 0.0,
		reason=reason,
	)


def build_erp_business_reasoning_activation_contract(
	*,
	request_id: str,
	session_id: str,
	grounded_context_available: bool,
	grounded_source_request_id: str = "",
	grounded_source_kind: str = "",
	grounded_source_name: str = "",
	grounded_family_id: str = "",
	grounded_artifact_type: str = "",
	grounded_source_reports: List[str] | None = None,
	grounded_capability_id: str = "",
	grounded_semantic_tags: List[str] | None = None,
	grounding_summary: Dict[str, Any] | None = None,
	recommendation_allowed: bool = False,
	recommendation_policy_basis: List[str] | None = None,
	allowed_reasoning_types: List[str] | None = None,
	activation_state: str = "not_eligible",
	route_target: str = "artifact_lane",
	reason: str = "",
) -> ERPBusinessReasoningActivationContract:
	return ERPBusinessReasoningActivationContract(
		request_id=str(request_id or "").strip(),
		session_id=str(session_id or "").strip(),
		grounded_context_available=bool(grounded_context_available),
		grounded_source_request_id=str(grounded_source_request_id or "").strip(),
		grounded_source_kind=str(grounded_source_kind or "").strip(),
		grounded_source_name=str(grounded_source_name or "").strip(),
		grounded_family_id=str(grounded_family_id or "").strip(),
		grounded_artifact_type=str(grounded_artifact_type or "").strip(),
		grounded_source_reports=[str(x or "").strip() for x in (grounded_source_reports or []) if str(x or "").strip()],
		grounded_capability_id=str(grounded_capability_id or "").strip(),
		grounded_semantic_tags=[str(x or "").strip() for x in (grounded_semantic_tags or []) if str(x or "").strip()],
		grounding_summary=dict(grounding_summary or {}),
		recommendation_allowed=bool(recommendation_allowed),
		recommendation_policy_basis=[str(x or "").strip() for x in (recommendation_policy_basis or []) if str(x or "").strip()],
		allowed_reasoning_types=[str(x or "").strip() for x in (allowed_reasoning_types or []) if str(x or "").strip()],
		activation_state=str(activation_state or "not_eligible").strip() or "not_eligible",
		route_target=str(route_target or "artifact_lane").strip() or "artifact_lane",
		reason=str(reason or "").strip(),
	)


def build_erp_business_reasoning_contract(
	*,
	request_id: str,
	session_id: str,
	reasoning_type: str,
	grounding_source_request_id: str = "",
	grounding_source_kind: str = "",
	grounding_family_id: str = "",
	grounding_artifact_type: str = "",
	grounding_source_reports: List[str] | None = None,
	grounding_sufficient: bool = False,
	grounding_gaps: List[str] | None = None,
	bounded_domain: str = "erp_business",
	reasoning_scope: str = "",
	supported_claims: List[Dict[str, Any]] | None = None,
	recommendations: List[Dict[str, Any]] | None = None,
	speculation_flags: List[str] | None = None,
	allowed_to_answer: bool = False,
	reason: str = "",
	confidence: float = 0.0,
) -> ERPBusinessReasoningContract:
	return ERPBusinessReasoningContract(
		request_id=str(request_id or "").strip(),
		session_id=str(session_id or "").strip(),
		reasoning_type=str(reasoning_type or "").strip(),
		grounding_source_request_id=str(grounding_source_request_id or "").strip(),
		grounding_source_kind=str(grounding_source_kind or "").strip(),
		grounding_family_id=str(grounding_family_id or "").strip(),
		grounding_artifact_type=str(grounding_artifact_type or "").strip(),
		grounding_source_reports=[str(x or "").strip() for x in (grounding_source_reports or []) if str(x or "").strip()],
		grounding_sufficient=bool(grounding_sufficient),
		grounding_gaps=[str(x or "").strip() for x in (grounding_gaps or []) if str(x or "").strip()],
		bounded_domain=str(bounded_domain or "erp_business").strip() or "erp_business",
		reasoning_scope=str(reasoning_scope or "").strip(),
		supported_claims=[dict(item) for item in (supported_claims or []) if isinstance(item, dict)],
		recommendations=[dict(item) for item in (recommendations or []) if isinstance(item, dict)],
		speculation_flags=[str(x or "").strip() for x in (speculation_flags or []) if str(x or "").strip()],
		allowed_to_answer=bool(allowed_to_answer),
		reason=str(reason or "").strip(),
		confidence=float(max(0.0, min(1.0, confidence or 0.0))),
	)


def build_knowledge_boundary_contract(
	*,
	request_id: str,
	session_id: str,
	proposed_lane: str,
	final_lane: str,
	boundary_status: str = "confirmed",
	lane_appropriate: bool = False,
	valid_erp_domain: bool = False,
	grounding_required: bool = False,
	grounding_available: bool = False,
	knowledge_coverage_state: str = "unsupported_non_erp",
	reclassification_reason: str = "",
	boundary_flags: List[str] | None = None,
	allowed_to_answer: bool = False,
	safe_next_action: str = "respond_unsupported",
	user_response_mode: str = "safe_refusal",
	confidence: float = 0.0,
) -> KnowledgeBoundaryContract:
	return KnowledgeBoundaryContract(
		request_id=str(request_id or "").strip(),
		session_id=str(session_id or "").strip(),
		proposed_lane=str(proposed_lane or "").strip(),
		final_lane=str(final_lane or "").strip(),
		boundary_status=str(boundary_status or "confirmed").strip() or "confirmed",
		lane_appropriate=bool(lane_appropriate),
		valid_erp_domain=bool(valid_erp_domain),
		grounding_required=bool(grounding_required),
		grounding_available=bool(grounding_available),
		knowledge_coverage_state=str(knowledge_coverage_state or "unsupported_non_erp").strip() or "unsupported_non_erp",
		reclassification_reason=str(reclassification_reason or "").strip(),
		boundary_flags=[str(x or "").strip() for x in (boundary_flags or []) if str(x or "").strip()],
		allowed_to_answer=bool(allowed_to_answer),
		safe_next_action=str(safe_next_action or "respond_unsupported").strip() or "respond_unsupported",
		user_response_mode=str(user_response_mode or "safe_refusal").strip() or "safe_refusal",
		confidence=float(max(0.0, min(1.0, confidence or 0.0))),
	)


def build_artifact_enrichment_recovery_contract(
	*,
	request_id: str,
	session_id: str,
	source_request_id: str = "",
	source_family_id: str = "",
	source_capability_id: str = "",
	source_report: str = "",
	failure_type: str = "artifact_enrichment_incompatible",
	recovery_state: str = "unavailable",
	available_recovery_actions: List[str] | None = None,
	recommended_recovery_action: str = "",
	preservable_scope: Dict[str, Any] | None = None,
	preservable_dimensions: List[str] | None = None,
	preservable_metrics: List[str] | None = None,
	preservable_time_context: Dict[str, Any] | None = None,
	alternative_capability_id: str = "",
	alternative_report: str = "",
	reason: str = "",
	allowed_to_recover: bool = False,
	confidence: float = 0.0,
) -> ArtifactEnrichmentRecoveryContract:
	return ArtifactEnrichmentRecoveryContract(
		request_id=str(request_id or "").strip(),
		session_id=str(session_id or "").strip(),
		source_request_id=str(source_request_id or "").strip(),
		source_family_id=str(source_family_id or "").strip(),
		source_capability_id=str(source_capability_id or "").strip(),
		source_report=str(source_report or "").strip(),
		failure_type=str(failure_type or "artifact_enrichment_incompatible").strip() or "artifact_enrichment_incompatible",
		recovery_state=str(recovery_state or "unavailable").strip() or "unavailable",
		available_recovery_actions=[str(x or "").strip() for x in (available_recovery_actions or []) if str(x or "").strip()],
		recommended_recovery_action=str(recommended_recovery_action or "").strip(),
		preservable_scope=dict(preservable_scope or {}),
		preservable_dimensions=[str(x or "").strip() for x in (preservable_dimensions or []) if str(x or "").strip()],
		preservable_metrics=[str(x or "").strip() for x in (preservable_metrics or []) if str(x or "").strip()],
		preservable_time_context=dict(preservable_time_context or {}),
		alternative_capability_id=str(alternative_capability_id or "").strip(),
		alternative_report=str(alternative_report or "").strip(),
		reason=str(reason or "").strip(),
		allowed_to_recover=bool(allowed_to_recover),
		confidence=float(max(0.0, min(1.0, confidence or 0.0))),
	)


def build_conversational_repair_intent_contract(
	*,
	request_id: str,
	session_id: str,
	repair_intent_type: str = "not_applicable",
	repair_state: str = "unresolved",
	targets_prior_recovery: bool = False,
	accepted_recovery_action: str = "",
	guidance_topic: str = "",
	fresh_query_override: bool = False,
	preserve_scope: bool = False,
	preserve_entity_dimension: bool = False,
	preserve_time_context: bool = False,
	reason: str = "",
	allowed_next_lane: str = "",
	confidence: float = 0.0,
) -> ConversationalRepairIntentContract:
	return ConversationalRepairIntentContract(
		request_id=str(request_id or "").strip(),
		session_id=str(session_id or "").strip(),
		repair_intent_type=str(repair_intent_type or "not_applicable").strip() or "not_applicable",
		repair_state=str(repair_state or "unresolved").strip() or "unresolved",
		targets_prior_recovery=bool(targets_prior_recovery),
		accepted_recovery_action=str(accepted_recovery_action or "").strip(),
		guidance_topic=str(guidance_topic or "").strip(),
		fresh_query_override=bool(fresh_query_override),
		preserve_scope=bool(preserve_scope),
		preserve_entity_dimension=bool(preserve_entity_dimension),
		preserve_time_context=bool(preserve_time_context),
		reason=str(reason or "").strip(),
		allowed_next_lane=str(allowed_next_lane or "").strip(),
		confidence=float(max(0.0, min(1.0, confidence or 0.0))),
	)


def build_clarification_reason_contract_from_sources(
	*,
	request_id: str,
	compiler_reason: str = "",
	compiler_reason_type: str = "",
	compiler_details: Dict[str, Any] | None = None,
	family_validation: Dict[str, Any] | None = None,
	semantic_validation: Dict[str, Any] | None = None,
) -> ClarificationReasonContract | None:
	reason_type = str(compiler_reason_type or "").strip()
	if reason_type:
		details = dict(compiler_details or {})
		return build_clarification_reason_contract(
			request_id=request_id,
			stage="compiler",
			source_contract_type="fresh_query_compiler",
			reason_type=reason_type,
			clarification_required=True,
			blocking=True,
			recommended_next_lane="clarification",
			missing_fields=details.get("missing_fields") if isinstance(details.get("missing_fields"), list) else [],
			ambiguity_flags=details.get("ambiguity_flags") if isinstance(details.get("ambiguity_flags"), list) else [],
			candidate_capability_ids=details.get("capability_candidates") if isinstance(details.get("capability_candidates"), list) else [],
			candidate_reports=details.get("report_candidates") if isinstance(details.get("report_candidates"), list) else [],
			suggested_options=details.get("suggested_time_scope_options") if isinstance(details.get("suggested_time_scope_options"), list) else [],
			internal_reason=str(compiler_reason or "").strip(),
			internal_details=details,
		)
	if isinstance(family_validation, dict) and str(family_validation.get("status") or "").strip() == "clarify":
		payload = dict(family_validation or {})
		reason_type = "time_scope_clarification" if payload.get("time_scope_match") is False else "validation_clarification"
		suggested_options = ["today", "last month", "all time"] if payload.get("time_scope_match") is False else []
		return build_clarification_reason_contract(
			request_id=request_id,
			stage="family_validation",
			source_contract_type="family_validation",
			reason_type=reason_type,
			clarification_required=True,
			blocking=True,
			recommended_next_lane="clarification",
			missing_fields=payload.get("missing_fields") if isinstance(payload.get("missing_fields"), list) else [],
			suggested_options=suggested_options,
			internal_reason=str(payload.get("decision") or "").strip(),
			internal_details=payload,
		)
	if isinstance(semantic_validation, dict) and str(semantic_validation.get("status") or "").strip() == "clarify":
		payload = dict(semantic_validation or {})
		reason_type = "time_scope_clarification" if payload.get("time_scope_match") is False else "validation_clarification"
		suggested_options = ["today", "last month", "all time"] if payload.get("time_scope_match") is False else []
		return build_clarification_reason_contract(
			request_id=request_id,
			stage="semantic_validation",
			source_contract_type="semantic_validation",
			reason_type=reason_type,
			clarification_required=True,
			blocking=True,
			recommended_next_lane="clarification",
			missing_fields=payload.get("missing_fields") if isinstance(payload.get("missing_fields"), list) else [],
			suggested_options=suggested_options,
			internal_reason=str(payload.get("decision") or "").strip(),
			internal_details=payload,
		)
	return None


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
	target_limit: int = 0,
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
		target_limit=int(max(0, target_limit or 0)),
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
	target_limit: int = 0,
	decision: str = "clarify",
	clarification_required: bool = False,
	compiler_reason: str = "",
	governed_resolution_details: Dict[str, Any] | None = None,
	clarification_reason_type: str = "",
	clarification_details: Dict[str, Any] | None = None,
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
		target_limit=int(max(0, target_limit or 0)),
		decision=str(decision or "clarify").strip(),
		clarification_required=bool(clarification_required),
		compiler_reason=str(compiler_reason or "").strip(),
		governed_resolution_details=dict(governed_resolution_details or {}),
		clarification_reason_type=str(clarification_reason_type or "").strip(),
		clarification_details=dict(clarification_details or {}),
	)


def build_compiled_query_request_contract(
	*,
	request_id: str,
	capability_id: str,
	selected_report: str,
	filters: Dict[str, Any] | None = None,
	requested_dimensions: List[str] | None = None,
	requested_metrics: List[str] | None = None,
	target_limit: int = 0,
	response_policy: Dict[str, Any] | None = None,
) -> CompiledQueryRequestContract:
	return CompiledQueryRequestContract(
		request_id=request_id,
		capability_id=str(capability_id or "").strip(),
		selected_report=str(selected_report or "").strip(),
		filters=dict(filters or {}),
		requested_dimensions=[str(x or "").strip() for x in (requested_dimensions or []) if str(x or "").strip()],
		requested_metrics=[str(x or "").strip() for x in (requested_metrics or []) if str(x or "").strip()],
		target_limit=int(max(0, target_limit or 0)),
		response_policy=dict(response_policy or {}),
	)


def build_financial_summary_resolution_contract(
	*,
	request_id: str,
	session_id: str,
	intent_class: str = "financial_summary",
	resolved_summary_domains: List[str] | None = None,
	resolved_summary_focus: str = "",
	resolved_summary_metric_family: str = "",
	resolved_summary_grain: str = "",
	resolved_time_scope: str = "",
	decision: str = "clarify",
	target_intent_class: str = "",
	target_composite_plan_id: str = "",
	ambiguity_flags: List[str] | None = None,
	ambiguity_reason: str = "",
	decision_reason: str = "",
	candidate_capability_ids: List[str] | None = None,
	candidate_reports: List[str] | None = None,
) -> FinancialSummaryResolutionContract:
	return FinancialSummaryResolutionContract(
		request_id=str(request_id or "").strip(),
		session_id=str(session_id or "").strip(),
		intent_class=str(intent_class or "financial_summary").strip() or "financial_summary",
		resolved_summary_domains=[str(x or "").strip() for x in (resolved_summary_domains or []) if str(x or "").strip()],
		resolved_summary_focus=str(resolved_summary_focus or "").strip(),
		resolved_summary_metric_family=str(resolved_summary_metric_family or "").strip(),
		resolved_summary_grain=str(resolved_summary_grain or "").strip(),
		resolved_time_scope=str(resolved_time_scope or "").strip(),
		decision=str(decision or "clarify").strip() or "clarify",
		target_intent_class=str(target_intent_class or "").strip(),
		target_composite_plan_id=str(target_composite_plan_id or "").strip(),
		ambiguity_flags=[str(x or "").strip() for x in (ambiguity_flags or []) if str(x or "").strip()],
		ambiguity_reason=str(ambiguity_reason or "").strip(),
		decision_reason=str(decision_reason or "").strip(),
		candidate_capability_ids=[str(x or "").strip() for x in (candidate_capability_ids or []) if str(x or "").strip()],
		candidate_reports=[str(x or "").strip() for x in (candidate_reports or []) if str(x or "").strip()],
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


def build_artifact_narrative_response_contract(
	*,
	request_id: str,
	family_id: str,
	narrative_engine: str = "",
	answer_style: str = "",
	answer_text: str = "",
	source_reports: List[str] | None = None,
	support_block_count: int = 0,
	warnings: List[str] | None = None,
) -> ArtifactNarrativeResponseContract:
	return ArtifactNarrativeResponseContract(
		request_id=str(request_id or "").strip(),
		family_id=str(family_id or "").strip(),
		narrative_engine=str(narrative_engine or "").strip(),
		answer_style=str(answer_style or "").strip(),
		answer_text=str(answer_text or "").strip(),
		source_reports=[str(x or "").strip() for x in (source_reports or []) if str(x or "").strip()],
		support_block_count=int(max(0, support_block_count or 0)),
		warnings=[str(x or "").strip() for x in (warnings or []) if str(x or "").strip()],
	)


def build_family_tool_surface_contract(
	*,
	request_id: str,
	session_id: str,
	candidate_family_ids: List[str] | None = None,
	preferred_tool_ids: List[str] | None = None,
	allowed_report_names: List[str] | None = None,
	report_discovery_allowed: bool = True,
	reason: str = "",
	family_entries: List[Dict[str, Any]] | None = None,
) -> FamilyToolSurfaceContract:
	return FamilyToolSurfaceContract(
		request_id=str(request_id or "").strip(),
		session_id=str(session_id or "").strip(),
		candidate_family_ids=[str(x or "").strip() for x in (candidate_family_ids or []) if str(x or "").strip()],
		preferred_tool_ids=[str(x or "").strip() for x in (preferred_tool_ids or []) if str(x or "").strip()],
		allowed_report_names=[str(x or "").strip() for x in (allowed_report_names or []) if str(x or "").strip()],
		report_discovery_allowed=bool(report_discovery_allowed),
		reason=str(reason or "").strip(),
		family_entries=[dict(item) for item in (family_entries or []) if isinstance(item, dict)],
	)


def build_compiled_execution_audit_contract(
	*,
	request_id: str,
	session_id: str,
	execution_mode: str = "compiled_first_turn",
	compiler_decision: str = "",
	compiler_reason: str = "",
	governed_resolution_details: Dict[str, Any] | None = None,
	capability_id: str = "",
	selected_report: str = "",
	governed_family_id: str = "",
	composite_plan_id: str = "",
	proposal_cache_hit: bool = False,
	proposal_shared_inflight_hit: bool = False,
	compiled_query_available: bool = False,
	runtime_invoked: bool = False,
	runtime_ok: bool = False,
	runtime_engine: str = "",
	runtime_model: str = "",
	grounded_validation_status: str = "",
	family_validation_status: str = "",
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
		governed_resolution_details=dict(governed_resolution_details or {}),
		capability_id=str(capability_id or "").strip(),
		selected_report=str(selected_report or "").strip(),
		governed_family_id=str(governed_family_id or "").strip(),
		composite_plan_id=str(composite_plan_id or "").strip(),
		proposal_cache_hit=bool(proposal_cache_hit),
		proposal_shared_inflight_hit=bool(proposal_shared_inflight_hit),
		compiled_query_available=bool(compiled_query_available),
		runtime_invoked=bool(runtime_invoked),
		runtime_ok=bool(runtime_ok),
		runtime_engine=str(runtime_engine or "").strip(),
		runtime_model=str(runtime_model or "").strip(),
		grounded_validation_status=str(grounded_validation_status or "").strip(),
		family_validation_status=str(family_validation_status or "").strip(),
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


def _first_canonical_metric_key(values: List[str] | None) -> str:
	for value in values or []:
		candidates = detect_canonical_keys(str(value or "").strip(), dimension_or_metric="metric")
		if candidates:
			return str(candidates[0] or "").strip()
	return ""


def _ranked_entity_labels(grounded_turn: Dict[str, Any], limit: int) -> List[str]:
	known_entities = grounded_turn.get("known_entities")
	if isinstance(known_entities, list):
		values: List[str] = []
		for item in known_entities:
			if not isinstance(item, dict):
				continue
			for key in ("label", "name", "entity_name", "entity"):
				clean = str(item.get(key) or "").strip()
				if clean:
					values.append(clean)
					break
			if limit > 0 and len(values) >= limit:
				return values[:limit]
		if values:
			return values[:limit] if limit > 0 else values

	rows = grounded_turn.get("table_rows")
	if not isinstance(rows, list):
		rows = []
	values = []
	for row in rows:
		if not isinstance(row, dict):
			continue
		for key in ("entity_name", "entity", "item_name", "customer", "supplier", "party", "name", "label"):
			clean = str(row.get(key) or "").strip()
			if clean:
				values.append(clean)
				break
		if limit > 0 and len(values) >= limit:
			break
	return values[:limit] if limit > 0 else values


def _clean_string_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	out: List[str] = []
	for value in values:
		clean = str(value or "").strip()
		if clean and clean not in out:
			out.append(clean)
	return out


def _normalized_key_fallback(value: str) -> str:
	clean = str(value or "").strip().lower()
	if not clean:
		return ""
	return re.sub(r"[^a-z0-9]+", "_", clean).strip("_")


def _canonical_metric_keys(values: List[str] | None, capability_id: str = "") -> List[str]:
	out: List[str] = []
	for value in values or []:
		clean = str(value or "").strip()
		if not clean:
			continue
		canonical = get_canonical_key(clean, capability_id=capability_id or None, dimension_or_metric="metric")
		final_value = str(canonical or _normalized_key_fallback(clean) or clean).strip()
		if final_value and final_value not in out:
			out.append(final_value)
	return out


def _canonical_dimension_key(value: str, capability_id: str = "") -> str:
	clean = str(value or "").strip()
	if not clean:
		return ""
	canonical = get_canonical_key(clean, capability_id=capability_id or None, dimension_or_metric="dimension")
	if canonical:
		return str(canonical or "").strip()
	return _normalized_key_fallback(clean) or clean.lower()


def _surface_declared_metric_keys(
	*,
	report_name: str,
	capability_id: str,
	surface_summary: Dict[str, Any],
) -> List[str]:
	values: List[str] = []
	for item in surface_summary.get("columns") or []:
		if not isinstance(item, dict):
			continue
		for key in ("label", "fieldname"):
			clean = str(item.get(key) or "").strip()
			if clean:
				values.append(clean)
	governed_hints = surface_summary.get("governed_surface_hints") if isinstance(surface_summary.get("governed_surface_hints"), dict) else {}
	direct_query = governed_hints.get("direct_query") if isinstance(governed_hints.get("direct_query"), dict) else {}
	for clean in _clean_string_list(direct_query.get("fields")):
		values.append(clean)
	return _canonical_metric_keys(values, capability_id=capability_id)


def _surface_selector_filters(
	*,
	report_name: str,
	capability_id: str,
	surface_summary: Dict[str, Any],
) -> List[str]:
	supported_metric_keys = set(
		_canonical_metric_keys(report_supported_metrics(report_name), capability_id=capability_id)
	)
	if not supported_metric_keys:
		return []
	governed_hints = surface_summary.get("governed_surface_hints") if isinstance(surface_summary.get("governed_surface_hints"), dict) else {}
	defaultable_filters = governed_hints.get("defaultable_filters")
	if not isinstance(defaultable_filters, list):
		defaultable_filters = []
	out: List[str] = []
	for item in defaultable_filters:
		if not isinstance(item, dict):
			continue
		fieldname = str(item.get("fieldname") or "").strip()
		default_value = str(item.get("value") or "").strip()
		if not fieldname or not default_value:
			continue
		canonical_value = _canonical_metric_keys([default_value], capability_id=capability_id)
		if canonical_value and canonical_value[0] in supported_metric_keys and fieldname not in out:
			out.append(fieldname)
	return out


def _dimensions_compatible(
	*,
	source_dimension: str,
	report_name: str,
	capability_id: str,
) -> bool:
	clean_source = str(source_dimension or "").strip()
	if not clean_source:
		return True
	supported = [
		str(value or "").strip()
		for value in report_supported_dimensions(report_name)
		if str(value or "").strip()
	]
	if not supported:
		return True
	source_canonical = _canonical_dimension_key(clean_source, capability_id=capability_id)
	if source_canonical in {_canonical_dimension_key(value, capability_id=capability_id) for value in supported}:
		return True
	return clean_source.lower() in {value.lower() for value in supported}


def _report_surface_can_cover_metric_union(
	*,
	report_name: str,
	capability_id: str,
	required_metric_keys: List[str],
	surface_summary: Dict[str, Any],
) -> tuple[bool, List[str]]:
	required = [
		str(value or "").strip()
		for value in (required_metric_keys or [])
		if str(value or "").strip()
	]
	if not required:
		return False, []
	supported = set(_canonical_metric_keys(report_supported_metrics(report_name), capability_id=capability_id))
	if not set(required).issubset(supported):
		return False, []
	if len(required) <= 1:
		return True, []
	declared_metrics = set(
		_surface_declared_metric_keys(
			report_name=report_name,
			capability_id=capability_id,
			surface_summary=surface_summary,
		)
	)
	if set(required).issubset(declared_metrics):
		return True, []
	selector_filters = _surface_selector_filters(
		report_name=report_name,
		capability_id=capability_id,
		surface_summary=surface_summary,
	)
	if selector_filters:
		return False, selector_filters
	return True, []


def build_artifact_enrichment_compatibility_contract(
	*,
	request_id: str,
	followup_resolution: FollowUpResolution,
	artifact_payload: Dict[str, Any] | None = None,
	grounded_turn: Dict[str, Any] | None = None,
	continuation_contract: ArtifactContinuationContract | None = None,
	required_metric_keys: List[str] | None = None,
) -> ArtifactEnrichmentCompatibilityContract:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	turn = grounded_turn if isinstance(grounded_turn, dict) else {}
	source_family_id = str(getattr(continuation_contract, "source_family_id", "") or artifact.get("family_id") or "").strip()
	source_capability_id = str(getattr(continuation_contract, "source_capability_id", "") or "").strip()
	source_report = str(getattr(continuation_contract, "source_report", "") or turn.get("source_name") or "").strip()
	if not source_capability_id and source_report:
		source_capability_id = str((report_capability_ids(source_report) or [""])[0] or "").strip()
	source_dimension = str(
		getattr(followup_resolution, "target_dimension", "")
		or getattr(continuation_contract, "preserved_dimension", "")
		or getattr(continuation_contract, "source_dimension", "")
		or ""
	).strip()
	target_metric = str(getattr(followup_resolution, "target_metric", "") or "").strip()
	requested_columns = _clean_string_list(getattr(followup_resolution, "requested_columns", []) or [])
	required_keys = _canonical_metric_keys(required_metric_keys or [], capability_id=source_capability_id)
	source_surface = get_report_surface_summary(source_report)
	source_surface_sources = _clean_string_list(source_surface.get("surface_sources"))
	source_selector_filters = _surface_selector_filters(
		report_name=source_report,
		capability_id=source_capability_id,
		surface_summary=source_surface,
	) if source_report and source_capability_id and source_surface else []
	if len(required_keys) > 1 and (
		"value_quantity" in source_selector_filters
		or source_family_id == "ranking_analytics"
	):
		reason = (
			"The current governed ranking path is anchored to one primary metric basis, so it cannot safely combine "
			"multiple metric bases into one ranking artifact."
		)
		return ArtifactEnrichmentCompatibilityContract(
			request_id=str(request_id or "").strip(),
			source_family_id=source_family_id,
			source_capability_id=source_capability_id,
			source_report=source_report,
			source_dimension=source_dimension,
			target_metric=target_metric,
			requested_columns=requested_columns,
			required_metric_keys=required_keys,
			compatibility_status="unavailable_in_current_governed_path",
			compatible=False,
			target_capability_id="",
			target_report="",
			candidate_reports_considered=[],
			source_surface_sources=source_surface_sources,
			source_selector_filters=source_selector_filters,
			reason=reason,
		)
	candidate_reports: List[str] = []
	family_reports = set(report_family_report_names(source_family_id)) if source_family_id else set()
	for report_name in [source_report, *capability_report_names(source_capability_id)]:
		clean = str(report_name or "").strip()
		if not clean or clean in candidate_reports:
			continue
		if family_reports and clean not in family_reports:
			continue
		candidate_reports.append(clean)

	candidates: List[tuple[int, str, str]] = []
	for report_name in candidate_reports:
		capability_id = source_capability_id or str((report_capability_ids(report_name) or [""])[0] or "").strip()
		if not capability_id:
			continue
		surface = get_report_surface_summary(report_name)
		if not surface:
			continue
		surface_assessment = surface.get("surface_assessment") if isinstance(surface.get("surface_assessment"), dict) else {}
		if not bool(surface_assessment.get("erp_declared_surface")) and not bool(surface_assessment.get("governed_hint_surface")):
			continue
		if not _dimensions_compatible(
			source_dimension=source_dimension,
			report_name=report_name,
			capability_id=capability_id,
		):
			continue
		can_cover, _ = _report_surface_can_cover_metric_union(
			report_name=report_name,
			capability_id=capability_id,
			required_metric_keys=required_keys,
			surface_summary=surface,
		)
		if not can_cover:
			continue
		score = 0
		if report_name == source_report:
			score += 1000
		if capability_id == source_capability_id:
			score += 250
		if report_name == capability_default_report_name(capability_id):
			score += 40
		source_tags = {
			str(value or "").strip()
			for value in report_semantic_tags(source_report)
			if str(value or "").strip()
		}
		candidate_tags = {
			str(value or "").strip()
			for value in report_semantic_tags(report_name)
			if str(value or "").strip()
		}
		if source_tags and candidate_tags:
			score += len(source_tags.intersection(candidate_tags)) * 10
		capability_tags = {
			str(value or "").strip()
			for value in capability_semantic_tags(capability_id)
			if str(value or "").strip()
		}
		if capability_tags and candidate_tags:
			score += len(capability_tags.intersection(candidate_tags)) * 20
		if bool(surface_assessment.get("erp_declared_surface")):
			score += 10
		if bool(surface_assessment.get("governed_hint_surface")):
			score += 5
		candidates.append((score, capability_id, report_name))

	if candidates:
		_, target_capability_id, target_report = max(candidates, key=lambda item: item[0])
		reason = (
			"The requested column or metric is not populated in the current artifact, "
			"but a compatible governed enrichment path exists within the current family and capability boundary."
		)
		return ArtifactEnrichmentCompatibilityContract(
			request_id=str(request_id or "").strip(),
			source_family_id=source_family_id,
			source_capability_id=source_capability_id,
			source_report=source_report,
			source_dimension=source_dimension,
			target_metric=target_metric,
			requested_columns=requested_columns,
			required_metric_keys=required_keys,
			compatibility_status="governed_requery_compatible",
			compatible=True,
			target_capability_id=target_capability_id,
			target_report=target_report,
			candidate_reports_considered=candidate_reports,
			source_surface_sources=source_surface_sources,
			source_selector_filters=source_selector_filters,
			reason=reason,
		)

	reason = (
		"The current governed artifact does not expose the requested column or metric, "
		"and no compatible governed enrichment path was proven inside the current family and capability boundary."
	)
	if source_selector_filters and len(required_keys) > 1:
		reason = (
			"The current governed report uses a metric-selector surface, so it cannot safely add the requested metric union "
			"without switching the report basis."
		)
	return ArtifactEnrichmentCompatibilityContract(
		request_id=str(request_id or "").strip(),
		source_family_id=source_family_id,
		source_capability_id=source_capability_id,
		source_report=source_report,
		source_dimension=source_dimension,
		target_metric=target_metric,
		requested_columns=requested_columns,
		required_metric_keys=required_keys,
		compatibility_status="unavailable_in_current_governed_path",
		compatible=False,
		target_capability_id="",
		target_report="",
		candidate_reports_considered=candidate_reports,
		source_surface_sources=source_surface_sources,
		source_selector_filters=source_selector_filters,
		reason=reason,
	)


def _recovery_scope_from_grounded_turn(
	grounded_turn: Dict[str, Any] | None,
	followup_resolution: FollowUpResolution | None = None,
) -> Dict[str, Any]:
	turn = grounded_turn if isinstance(grounded_turn, dict) else {}
	scope: Dict[str, Any] = {}
	company = str(turn.get("company") or "").strip()
	if company:
		scope["company"] = company
	filters = turn.get("filters") if isinstance(turn.get("filters"), dict) else {}
	preserved_filters: Dict[str, Any] = {}
	for raw_key, raw_value in filters.items():
		key = str(raw_key or "").strip()
		if not key or key in {"company", "from_date", "to_date", "report_date"}:
			continue
		if isinstance(raw_value, (list, tuple, set)):
			values = [value for value in raw_value if value not in {None, ""}]
			if values:
				preserved_filters[key] = list(values)
			continue
		if isinstance(raw_value, dict):
			if raw_value:
				preserved_filters[key] = dict(raw_value)
			continue
		if raw_value not in {None, ""}:
			preserved_filters[key] = raw_value
	if preserved_filters:
		scope["filters"] = preserved_filters
	try:
		requested_top_n = int(
			max(
				0,
				getattr(followup_resolution, "target_limit", 0) if followup_resolution is not None else 0,
			)
		)
	except Exception:
		requested_top_n = 0
	if requested_top_n <= 0:
		try:
			requested_top_n = int(max(0, turn.get("row_count") or 0))
		except Exception:
			requested_top_n = 0
	if requested_top_n > 0:
		scope["requested_top_n"] = requested_top_n
	return scope


def _recovery_time_context(
	grounded_turn: Dict[str, Any] | None,
	followup_resolution: FollowUpResolution | None = None,
) -> Dict[str, Any]:
	turn = grounded_turn if isinstance(grounded_turn, dict) else {}
	time_context: Dict[str, Any] = {}
	date_range = turn.get("date_range") if isinstance(turn.get("date_range"), dict) else {}
	for key in ("from_date", "to_date", "report_date"):
		value = date_range.get(key)
		if value not in {None, ""}:
			time_context[key] = value
	requested_time_scope = str(getattr(followup_resolution, "requested_time_scope", "") or "").strip()
	if requested_time_scope:
		time_context["requested_time_scope"] = requested_time_scope
	return time_context


def _recovery_dimensions(
	*,
	grounded_turn: Dict[str, Any] | None = None,
	source_dimension: str = "",
	followup_resolution: FollowUpResolution | None = None,
) -> List[str]:
	turn = grounded_turn if isinstance(grounded_turn, dict) else {}
	values: List[str] = []
	for candidate in [
		str(source_dimension or "").strip(),
		str(getattr(followup_resolution, "target_dimension", "") or "").strip(),
		*[str(item or "").strip() for item in (turn.get("dimensions") or []) if str(item or "").strip()],
	]:
		if candidate and candidate not in values:
			values.append(candidate)
	return values


def _recovery_metrics(
	*,
	grounded_turn: Dict[str, Any] | None = None,
	target_metric: str = "",
	required_metric_keys: List[str] | None = None,
	followup_resolution: FollowUpResolution | None = None,
) -> List[str]:
	turn = grounded_turn if isinstance(grounded_turn, dict) else {}
	values: List[str] = []
	requested_columns = getattr(followup_resolution, "requested_columns", []) if followup_resolution is not None else []
	source_metric_key = ""
	for candidate in (turn.get("metrics") or []):
		clean = str(candidate or "").strip()
		if clean:
			source_metric_key = str(
				get_canonical_key(clean, dimension_or_metric="metric")
				or _normalized_key_fallback(clean)
				or clean.lower()
			).strip()
			break
	if not source_metric_key:
		filters = turn.get("filters") if isinstance(turn.get("filters"), dict) else {}
		value_quantity = str(filters.get("value_quantity") or "").strip()
		if value_quantity:
			source_metric_key = str(
				get_canonical_key(value_quantity, dimension_or_metric="metric")
				or _normalized_key_fallback(value_quantity)
				or value_quantity.lower()
			).strip()
	for candidate in [
		str(target_metric or "").strip(),
		*[str(item or "").strip() for item in (requested_columns or []) if str(item or "").strip()],
		*[str(item or "").strip() for item in (required_metric_keys or []) if str(item or "").strip()],
		*[str(item or "").strip() for item in (turn.get("metrics") or []) if str(item or "").strip()],
	]:
		if candidate and candidate not in values:
			values.append(candidate)
	if source_metric_key and len(values) > 1:
		alternative_first = [
			value
			for value in values
			if (_normalized_key_fallback(value) or value.lower()) != source_metric_key
		]
		source_metrics = [
			value
			for value in values
			if (_normalized_key_fallback(value) or value.lower()) == source_metric_key
		]
		values = alternative_first + source_metrics
	return values


def build_recovery_contract_from_enrichment_compatibility(
	*,
	request_id: str,
	session_id: str,
	compatibility_contract: ArtifactEnrichmentCompatibilityContract,
	grounded_turn: Dict[str, Any] | None = None,
	followup_resolution: FollowUpResolution | None = None,
) -> ArtifactEnrichmentRecoveryContract:
	turn = grounded_turn if isinstance(grounded_turn, dict) else {}
	source_report = str(getattr(compatibility_contract, "source_report", "") or turn.get("source_name") or "").strip()
	source_capability_id = str(getattr(compatibility_contract, "source_capability_id", "") or "").strip()
	if not source_capability_id and source_report:
		source_capability_id = str((report_capability_ids(source_report) or [""])[0] or "").strip()
	alternative_capability_id = str(getattr(compatibility_contract, "target_capability_id", "") or "").strip()
	alternative_report = str(getattr(compatibility_contract, "target_report", "") or "").strip()
	source_selector_filters = {
		str(value or "").strip()
		for value in (getattr(compatibility_contract, "source_selector_filters", []) or [])
		if str(value or "").strip()
	}
	recoverable_metrics = _recovery_metrics(
		grounded_turn=turn,
		target_metric=str(getattr(compatibility_contract, "target_metric", "") or "").strip(),
		required_metric_keys=list(getattr(compatibility_contract, "required_metric_keys", []) or []),
		followup_resolution=followup_resolution,
	)
	recoverable_dimensions = _recovery_dimensions(
		grounded_turn=turn,
		source_dimension=str(getattr(compatibility_contract, "source_dimension", "") or "").strip(),
		followup_resolution=followup_resolution,
	)
	has_synthetic_alternative = bool(
		not alternative_capability_id
		and not alternative_report
		and "value_quantity" in source_selector_filters
		and recoverable_dimensions
		and recoverable_metrics
	)
	if has_synthetic_alternative:
		alternative_capability_id = source_capability_id
	has_governed_alternative = bool(alternative_capability_id or alternative_report)
	available_actions = ["keep_current_artifact"]
	if has_governed_alternative:
		available_actions.append("run_alternative_governed_query")
	available_actions.append("clarify_target_output")
	recovery_state = "recoverable" if has_governed_alternative else "clarify_recovery_target"
	recommended_action = "run_alternative_governed_query" if has_governed_alternative else "clarify_target_output"
	reason = str(getattr(compatibility_contract, "reason", "") or "").strip()
	if not reason:
		reason = (
			"The current governed artifact cannot satisfy the requested enrichment safely, "
			"so recovery must stay within governed requery or clarified target output."
		)
	return build_artifact_enrichment_recovery_contract(
		request_id=request_id,
		session_id=session_id,
		source_request_id=str(turn.get("trace_request_id") or turn.get("request_id") or request_id or "").strip(),
		source_family_id=str(getattr(compatibility_contract, "source_family_id", "") or turn.get("artifact_family_id") or "").strip(),
		source_capability_id=source_capability_id,
		source_report=source_report,
		failure_type="artifact_enrichment_incompatible",
		recovery_state=recovery_state,
		available_recovery_actions=available_actions,
		recommended_recovery_action=recommended_action,
		preservable_scope=_recovery_scope_from_grounded_turn(turn, followup_resolution),
		preservable_dimensions=recoverable_dimensions,
		preservable_metrics=recoverable_metrics,
		preservable_time_context=_recovery_time_context(turn, followup_resolution),
		alternative_capability_id=alternative_capability_id,
		alternative_report=alternative_report,
		reason=reason,
		allowed_to_recover=bool(has_governed_alternative or "clarify_target_output" in available_actions),
		confidence=0.93 if has_governed_alternative else 0.82,
	)


def build_recovery_contract_from_evidence_boundary(
	*,
	request_id: str,
	session_id: str,
	artifact_payload: Dict[str, Any] | None = None,
	grounded_turn: Dict[str, Any] | None = None,
	followup_resolution: FollowUpResolution | None = None,
	reason: str = "",
) -> ArtifactEnrichmentRecoveryContract:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	turn = grounded_turn if isinstance(grounded_turn, dict) else {}
	source_report = str(turn.get("source_name") or artifact.get("source_name") or artifact.get("title") or "").strip()
	source_capability_id = str((report_capability_ids(source_report) or [""])[0] or "").strip() if source_report else ""
	recovery_reason = str(reason or "").strip()
	if not recovery_reason:
		recovery_reason = (
			"The current grounded artifact does not contain direct governed evidence for the requested operational status, "
			"so the next safe step is to clarify the target output or switch to a governed operational source."
		)
	return build_artifact_enrichment_recovery_contract(
		request_id=request_id,
		session_id=session_id,
		source_request_id=str(turn.get("trace_request_id") or turn.get("request_id") or request_id or "").strip(),
		source_family_id=str(artifact.get("family_id") or turn.get("artifact_family_id") or "").strip(),
		source_capability_id=source_capability_id,
		source_report=source_report,
		failure_type="grounded_evidence_missing",
		recovery_state="clarify_recovery_target",
		available_recovery_actions=["keep_current_artifact", "clarify_target_output"],
		recommended_recovery_action="clarify_target_output",
		preservable_scope=_recovery_scope_from_grounded_turn(turn),
		preservable_dimensions=_recovery_dimensions(grounded_turn=turn, followup_resolution=followup_resolution),
		preservable_metrics=_recovery_metrics(grounded_turn=turn, followup_resolution=followup_resolution),
		preservable_time_context=_recovery_time_context(turn, followup_resolution),
		alternative_capability_id="",
		alternative_report="",
		reason=recovery_reason,
		allowed_to_recover=True,
		confidence=0.79,
	)


def _artifact_requested_columns(turn: Dict[str, Any], artifact: Dict[str, Any], source_metric_key: str) -> List[str]:
	dimensions = artifact.get("dimensions") if isinstance(artifact.get("dimensions"), dict) else {}
	stored_columns = _clean_string_list(dimensions.get("requested_columns"))
	if stored_columns:
		return stored_columns
	return _clean_string_list([
		*(turn.get("returned_schema") or [] if isinstance(turn.get("returned_schema"), list) else []),
		"entity" if source_metric_key else "",
		source_metric_key,
	])


def _artifact_available_columns(turn: Dict[str, Any], artifact: Dict[str, Any], source_metric_key: str) -> List[str]:
	dimensions = artifact.get("dimensions") if isinstance(artifact.get("dimensions"), dict) else {}
	sections = artifact.get("sections") if isinstance(artifact.get("sections"), dict) else {}
	values: List[str] = []
	for column in _clean_string_list(turn.get("returned_schema")):
		if column not in values:
			values.append(column)
	for column in _clean_string_list(dimensions.get("available_metric_keys")):
		if column not in values:
			values.append(column)
	for column in (
		str(dimensions.get("requested_metric_key") or "").strip(),
		str(dimensions.get("primary_metric_key") or "").strip(),
		source_metric_key,
	):
		if column and column not in values:
			values.append(column)
	row_lists = []
	table_rows = turn.get("table_rows")
	if isinstance(table_rows, list):
		row_lists.append(table_rows)
	for key in ("ranked_rows", "rows", "series", "document_rows", "product_rows"):
		rows = sections.get(key)
		if isinstance(rows, list):
			row_lists.append(rows)
	for rows in row_lists:
		for row in rows:
			if not isinstance(row, dict):
				continue
			for key in row.keys():
				clean = str(key or "").strip()
				if clean and clean not in values:
					values.append(clean)
	return values


def _artifact_row_count(turn: Dict[str, Any], artifact: Dict[str, Any]) -> int:
	for key in ("row_count",):
		try:
			value = int(max(0, turn.get(key) or 0))
		except Exception:
			value = 0
		if value > 0:
			return value
	table_rows = turn.get("table_rows")
	if isinstance(table_rows, list) and table_rows:
		return len(table_rows)
	sections = artifact.get("sections") if isinstance(artifact.get("sections"), dict) else {}
	for key in ("ranked_rows", "rows", "series", "document_rows", "product_rows"):
		rows = sections.get(key)
		if isinstance(rows, list) and rows:
			return len(rows)
	return 0


def build_artifact_continuation_contract(
	*,
	request_id: str,
	followup_resolution: FollowUpResolution,
	grounded_turn: Dict[str, Any] | None = None,
	artifact_payload: Dict[str, Any] | None = None,
) -> ArtifactContinuationContract:
	turn = grounded_turn if isinstance(grounded_turn, dict) else {}
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	artifact_dimensions = artifact.get("dimensions") if isinstance(artifact.get("dimensions"), dict) else {}
	artifact_period = artifact.get("period") if isinstance(artifact.get("period"), dict) else {}
	filters = turn.get("filters") if isinstance(turn.get("filters"), dict) else {}
	date_range = turn.get("date_range") if isinstance(turn.get("date_range"), dict) else {}
	requested_modes = [
		str(value or "").strip()
		for value in (getattr(followup_resolution, "requested_modes", []) or [])
		if str(value or "").strip()
	]
	source_report = str(turn.get("source_name") or "").strip()
	source_family_id = str(turn.get("artifact_family_id") or artifact.get("family_id") or "").strip()
	source_capability_id = str((report_capability_ids(source_report) or [""])[0] or "").strip() if source_report else ""
	source_artifact_type = str(turn.get("artifact_type") or artifact.get("artifact_type") or "").strip()
	source_dimension = str(
		artifact_dimensions.get("entity_dimension")
		or ((turn.get("dimensions") or [""])[0] if isinstance(turn.get("dimensions"), list) else "")
		or ""
	).strip()
	source_metric_key = str(
		artifact_dimensions.get("requested_metric_key")
		or artifact_dimensions.get("primary_metric_key")
		or _first_canonical_metric_key(turn.get("metrics") or [])
		or ""
	).strip()
	source_requested_columns = _artifact_requested_columns(turn, artifact, source_metric_key)
	source_available_columns = _artifact_available_columns(turn, artifact, source_metric_key)
	source_row_count = _artifact_row_count(turn, artifact)
	source_limit = 0
	try:
		source_limit = int(max(0, artifact_dimensions.get("requested_top_n") or 0))
	except Exception:
		source_limit = 0
	source_sort_direction = str(
		artifact_dimensions.get("sort_direction")
		or artifact_dimensions.get("requested_sort_direction")
		or ""
	).strip()
	source_time_scope = str(
		artifact_period.get("time_scope")
		or artifact_period.get("requested_time_scope")
		or ""
	).strip()
	preserved_dimension = str(getattr(followup_resolution, "target_dimension", "") or source_dimension or "").strip()
	preserved_metric_key = str(getattr(followup_resolution, "target_metric", "") or source_metric_key or "").strip()
	preserved_requested_columns = _clean_string_list(getattr(followup_resolution, "requested_columns", []) or [])
	if not preserved_requested_columns:
		preserved_requested_columns = list(source_requested_columns)
	rank_membership_eligible = source_family_id == "ranking_analytics"
	preserved_limit = int(max(0, getattr(followup_resolution, "target_limit", 0) or 0))
	if not preserved_limit and rank_membership_eligible:
		preserved_limit = source_limit
	preserved_sort_direction = str(
		getattr(followup_resolution, "sort_direction", "")
		or source_sort_direction
		or ""
	).strip()
	preserved_time_scope = str(
		getattr(followup_resolution, "requested_time_scope", "")
		or source_time_scope
		or ""
	).strip()
	preserved_report_date = str(date_range.get("report_date") or filters.get("report_date") or "").strip()
	preserved_from_date = str(date_range.get("from_date") or filters.get("from_date") or "").strip()
	preserved_to_date = str(date_range.get("to_date") or filters.get("to_date") or "").strip()
	continuation_mode = {
		"local_grounded_transform": "exact_local_continuation",
		"capability_requery": "governed_requery_continuation",
		"grounded_follow_up": "grounded_context_continuation",
		"entity_drilldown": "entity_drilldown_continuation",
		"new_query": "fresh_query_breakout",
	}.get(str(getattr(followup_resolution, "mode", "") or "").strip(), "unknown")
	preserve_grounded_context = bool(getattr(followup_resolution, "depends_on_grounded_turn", False))
	mode_set = set(requested_modes)
	preserve_metric_context = bool(preserve_grounded_context and "metric_refinement" not in mode_set)
	preserve_projection_shape = bool(
		preserve_grounded_context
		and not mode_set.intersection({"column_refinement", "dimension_breakdown", "grouping_change", "time_scope_restatement"})
	)
	preserve_date_context = bool(
		preserve_grounded_context
		and not str(getattr(followup_resolution, "requested_time_scope", "") or "").strip()
		and "time_scope_restatement" not in mode_set
	)
	preserve_rank_membership = bool(
		preserve_grounded_context
		and rank_membership_eligible
		and preserved_limit > 0
		and not mode_set.intersection({"dimension_breakdown", "grouping_change", "time_scope_restatement"})
	)
	preserve_rank_order = bool(preserve_rank_membership and not str(getattr(followup_resolution, "sort_direction", "") or "").strip())
	return ArtifactContinuationContract(
		request_id=str(request_id or "").strip(),
		source_family_id=source_family_id,
		source_capability_id=source_capability_id,
		source_report=source_report,
		source_artifact_type=source_artifact_type,
		source_dimension=source_dimension,
		source_metric_key=source_metric_key,
		source_requested_columns=source_requested_columns,
		source_available_columns=source_available_columns,
		source_row_count=source_row_count,
		source_limit=source_limit,
		source_sort_direction=source_sort_direction,
		source_time_scope=source_time_scope,
		continuation_mode=continuation_mode,
		preserve_grounded_context=preserve_grounded_context,
		preserve_metric_context=preserve_metric_context,
		preserve_projection_shape=preserve_projection_shape,
		preserve_date_context=preserve_date_context,
		preserved_dimension=preserved_dimension,
		preserved_metric_key=preserved_metric_key,
		preserved_requested_columns=preserved_requested_columns,
		preserved_limit=preserved_limit,
		preserved_sort_direction=preserved_sort_direction,
		preserved_time_scope=preserved_time_scope,
		preserved_report_date=preserved_report_date,
		preserved_from_date=preserved_from_date,
		preserved_to_date=preserved_to_date,
		preserve_rank_membership=preserve_rank_membership,
		preserve_rank_order=preserve_rank_order,
		preserved_entities=_ranked_entity_labels(turn, preserved_limit),
		requested_modes=requested_modes,
		reason=str(getattr(followup_resolution, "reason", "") or "").strip(),
	)


def build_governed_scope_decision_contract(
	*,
	request_id: str,
	stage: str,
	followup_resolution: FollowUpResolution | None = None,
	context_isolation: ScopeDecisionInputContract | Dict[str, Any] | None = None,
	latest_grounded_turn_available: bool = False,
	entity_drilldown: Dict[str, Any] | None = None,
	continuation_contract: ArtifactContinuationContract | None = None,
	clarification_required: bool = False,
) -> GovernedScopeDecisionContract:
	context = normalize_scope_decision_input(context_isolation)
	resolution = followup_resolution
	mode = str(getattr(resolution, "mode", "") or "").strip()
	execution_mode = {
		"new_query": "fresh_query",
	}.get(mode, mode or ("fresh_query" if not latest_grounded_turn_available else ""))
	if entity_drilldown is not None:
		execution_mode = "entity_drilldown"
	requested_domains = [
		str(value or "").strip()
		for value in (context.requested_domains or [])
		if str(value or "").strip()
	]
	context_domains = [
		str(value or "").strip()
		for value in (context.context_domains or [])
		if str(value or "").strip()
	]
	known_domain_surface = set(all_ontology_concepts())
	supported_domain_surface = set(supported_ontology_concepts())
	known_request_domains = [value for value in requested_domains if value in known_domain_surface]
	supported_request_domains = [value for value in requested_domains if value in supported_domain_surface]
	unsupported_known_request_domains = [
		value for value in requested_domains
		if value in known_domain_surface and value not in supported_domain_surface
	]

	primary_domain = str(context.primary_domain or "").strip()
	if not primary_domain:
		if {
			"tax",
			"balance_sheet",
			"cash_flow",
			"profit_and_loss",
			"working_capital",
			"payable",
			"receivable",
		} & set(unsupported_known_request_domains):
			primary_domain = "finance"
		elif {"employee"} & set(unsupported_known_request_domains):
			primary_domain = "hr"

	out_of_scope = bool(context.out_of_scope)
	if out_of_scope and unsupported_known_request_domains:
		governed_scope_status = "out_of_scope_but_valid_erp_domain"
	elif out_of_scope:
		governed_scope_status = "unsupported_request"
	elif clarification_required:
		governed_scope_status = "clarification_needed"
	elif execution_mode == "fresh_query" and latest_grounded_turn_available:
		governed_scope_status = "fresh_query_breakout"
	elif execution_mode in {
		"local_grounded_transform",
		"capability_requery",
		"grounded_follow_up",
		"entity_drilldown",
		"fresh_query",
	}:
		governed_scope_status = "covered_family"
	else:
		governed_scope_status = "unsupported_request"
	recommended_next_lane = "governed_artifact"
	if governed_scope_status == "clarification_needed":
		recommended_next_lane = "clarification"
	elif governed_scope_status == "out_of_scope_but_valid_erp_domain":
		recommended_next_lane = "future_erp_business_reasoning"
	elif governed_scope_status == "unsupported_request":
		recommended_next_lane = "unsupported"
	return GovernedScopeDecisionContract(
		request_id=str(request_id or "").strip(),
		stage=str(stage or "").strip() or "followup_orchestration",
		governed_scope_status=governed_scope_status,
		execution_mode=execution_mode or "unresolved",
		reason=str(context.reason or getattr(resolution, "reason", "") or "").strip(),
		requested_domains=requested_domains,
		context_domains=context_domains,
		known_request_domains=known_request_domains,
		supported_request_domains=supported_request_domains,
		unsupported_known_request_domains=unsupported_known_request_domains,
		latest_grounded_turn_available=bool(latest_grounded_turn_available),
		preserve_grounded_context=bool(
			getattr(continuation_contract, "preserve_grounded_context", False)
			or getattr(resolution, "depends_on_grounded_turn", False)
		),
		self_contained=bool(getattr(resolution, "self_contained", False)),
		out_of_scope=governed_scope_status in {"out_of_scope_but_valid_erp_domain", "unsupported_request"},
		clarification_required=bool(clarification_required),
		primary_domain=primary_domain,
		recommended_next_lane=recommended_next_lane,
		target_capability_id=str(getattr(resolution, "target_capability_id", "") or "").strip(),
		target_report=str(getattr(resolution, "target_report", "") or "").strip(),
	)


def governed_scope_decision_requires_fresh_query(scope_decision_contract: GovernedScopeDecisionContract | None) -> bool:
	return str(getattr(scope_decision_contract, "governed_scope_status", "") or "").strip() in {
		"fresh_query_breakout",
	}


def governed_scope_decision_is_out_of_scope(scope_decision_contract: GovernedScopeDecisionContract | None) -> bool:
	return bool(getattr(scope_decision_contract, "out_of_scope", False))


def governed_scope_decision_public_decision(
	scope_decision_contract: GovernedScopeDecisionContract | None,
) -> Dict[str, Any]:
	return {
		"force_new_query": governed_scope_decision_requires_fresh_query(scope_decision_contract),
		"out_of_scope": governed_scope_decision_is_out_of_scope(scope_decision_contract),
		"reason": str(getattr(scope_decision_contract, "reason", "") or "").strip(),
		"requested_domains": [
			str(value or "").strip()
			for value in (getattr(scope_decision_contract, "requested_domains", []) or [])
			if str(value or "").strip()
		],
		"context_domains": [
			str(value or "").strip()
			for value in (getattr(scope_decision_contract, "context_domains", []) or [])
			if str(value or "").strip()
		],
		"primary_domain": str(getattr(scope_decision_contract, "primary_domain", "") or "").strip(),
	}


def coerce_followup_resolution_from_scope_decision(
	*,
	request_id: str,
	followup_resolution: FollowUpResolution,
	scope_decision_contract: GovernedScopeDecisionContract | None,
) -> FollowUpResolution:
	if not governed_scope_decision_requires_fresh_query(scope_decision_contract):
		return followup_resolution
	if str(getattr(followup_resolution, "mode", "") or "").strip() == "capability_requery":
		return followup_resolution
	return clone_followup_resolution(
		followup_resolution,
		request_id=request_id,
		mode="new_query",
		target_capability_id="",
		target_report="",
		depends_on_grounded_turn=False,
		self_contained=True,
		reason=(
			str(getattr(scope_decision_contract, "reason", "") or "").strip()
			or str(getattr(followup_resolution, "reason", "") or "").strip()
			or "The request should be treated as a fresh governed ERP query."
		),
	)


def _infer_followup_requested_time_scope(
	*,
	message: str,
	requested_time_scope: str,
) -> str:
	current = str(requested_time_scope or "").strip()
	if current:
		return current
	text = str(message or "").strip().lower()
	if not text:
		return ""
	if re.search(r"\b(?:last|previous|prior)\s+month\b", text):
		return "last_month"
	if re.search(r"\b(?:this|current)\s+month\b", text):
		return "current_period"
	if re.search(r"\b(?:year\s+to\s+date|fiscal\s+year)\b", text):
		return "current_fiscal_year_to_date"
	if re.search(r"\b(?:today|as of today|as of now|now)\b", text):
		return "as_of_today"
	if re.search(r"\b(?:all\s+time|overall|full\s+available\s+time\s+range)\b", text):
		return "all_period"
	return ""


def _message_has_structural_followup_limit(message: str) -> bool:
	text = str(message or "").strip().lower()
	if not text:
		return False
	match = re.search(r"\b(?:top|last|latest)\s+(\d{1,2})\b", text)
	if not match:
		return False
	return not bool(
		re.match(
			r"\s+(?:day|days|week|weeks|month|months|year|years|quarter|quarters)\b",
			text[match.end():],
		)
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
	message_language = detect_language(message)
	if semantic_intent is not None:
		requested_modes = [
			"column_refinement" if str(mode or "").strip() == "column_projection" else str(mode or "").strip()
			for mode in (getattr(semantic_intent, "requested_modes", []) or [])
			if str(mode or "").strip()
		]
		target_dimension = str(getattr(semantic_intent, "target_dimension", "") or "").strip()
		target_limit = int(max(0, getattr(semantic_intent, "target_limit", 0) or 0))
		sort_direction = str(getattr(semantic_intent, "sort_direction", "") or "").strip()
		target_metric = str(getattr(semantic_intent, "target_metric", "") or "").strip()
		requested_columns = [
			str(value or "").strip()
			for value in (getattr(semantic_intent, "requested_columns", []) or [])
			if str(value or "").strip()
		]
		requested_time_scope = str(getattr(semantic_intent, "requested_time_scope", "") or "").strip()
		target_capability_id = str(getattr(semantic_intent, "target_capability_id", "") or "").strip()
		self_contained = bool(getattr(semantic_intent, "self_contained", False))
		semantic_reason = str(getattr(semantic_intent, "reason", "") or "").strip()
	else:
		requested_modes = []
		target_dimension = ""
		target_limit = 0
		sort_direction = ""
		target_metric = ""
		requested_columns = []
		requested_time_scope = ""
		target_capability_id = ""
		self_contained = False
		semantic_reason = ""
	original_requested_time_scope = str(requested_time_scope or "").strip()
	requested_time_scope = _infer_followup_requested_time_scope(
		message=message,
		requested_time_scope=requested_time_scope,
	)
	if requested_time_scope and not original_requested_time_scope and target_limit > 0 and not _message_has_structural_followup_limit(message):
		target_limit = 0
	non_presentation_requested_modes = {
		str(mode or "").strip()
		for mode in (requested_modes or [])
		if str(mode or "").strip() and str(mode or "").strip() not in {"presentation_transform", "table_presentation", "bullet_presentation"}
	}
	explicit_query_shape = bool(
		target_capability_id
		or requested_time_scope
		or target_metric
		or requested_columns
		or target_dimension
		or target_limit
		or sort_direction
		or non_presentation_requested_modes
	)
	grounded_turn_payload = latest_grounded_turn if isinstance(latest_grounded_turn, dict) else {}
	grounded_date_range = grounded_turn_payload.get("date_range") if isinstance(grounded_turn_payload.get("date_range"), dict) else {}
	grounded_filters = grounded_turn_payload.get("filters") if isinstance(grounded_turn_payload.get("filters"), dict) else {}
	inherited_date_context_present = bool(
		str(grounded_date_range.get("from_date") or "").strip()
		or str(grounded_date_range.get("to_date") or "").strip()
		or str(grounded_date_range.get("report_date") or "").strip()
		or str(grounded_filters.get("from_date") or "").strip()
		or str(grounded_filters.get("to_date") or "").strip()
		or str(grounded_filters.get("report_date") or "").strip()
	)
	message_looks_self_contained_business_query = _message_looks_like_self_contained_governed_business_query(
		message=message,
		language=message_language,
	)
	presentation_only_request = bool(set(requested_modes).intersection({"presentation_transform", "table_presentation", "bullet_presentation"})) and set(
		str(mode or "").strip() for mode in (requested_modes or []) if str(mode or "").strip()
	).issubset({"presentation_transform", "table_presentation", "bullet_presentation"})
	if (
		latest_grounded_turn_available
		and inherited_date_context_present
		and not requested_time_scope
		and not self_contained
		and message_looks_self_contained_business_query
	):
		self_contained = True
	grounded_turn = latest_grounded_turn if isinstance(latest_grounded_turn, dict) else {}
	local_grounded_modes = {
		"presentation_transform",
		"table_presentation",
		"bullet_presentation",
		"metric_refinement",
		"column_refinement",
	}
	if supports_local_followup_mode(grounded_turn, "aging_bucket_view"):
		local_grounded_modes.add("aging_bucket_view")
	if supports_local_followup_mode(grounded_turn, "dimension_breakdown", target_dimension=target_dimension):
		local_grounded_modes.add("dimension_breakdown")
	if supports_local_followup_mode(grounded_turn, "sort_or_limit"):
		local_grounded_modes.add("sort_or_limit")
	requested_mode_set = {
		str(mode or "").strip()
		for mode in (requested_modes or [])
		if str(mode or "").strip()
	}
	grounded_dimensions = {
		str(value or "").strip().lower()
		for value in (
			list(grounded_turn.get("dimensions") or [])
			+ list(grounded_turn.get("returned_schema") or [])
		)
		if str(value or "").strip()
	}
	target_dimension_present = not target_dimension or str(target_dimension or "").strip().lower() in grounded_dimensions
	dimension_change_requested = bool(target_dimension) and not target_dimension_present
	presentation_only_request = bool(requested_mode_set) and requested_mode_set.issubset(
		{"presentation_transform", "table_presentation", "bullet_presentation"}
	)
	structured_breakout_request = bool(
		dimension_change_requested
		or target_limit
		or sort_direction
		or target_metric
		or requested_time_scope
		or target_capability_id
	)
	local_transform_only = (
		bool(requested_mode_set)
		and requested_mode_set.issubset(local_grounded_modes)
		and not dimension_change_requested
		and not (presentation_only_request and structured_breakout_request)
	)
	source_report = str(grounded_turn.get("source_name") or "").strip()
	switch = resolve_followup_report_switch(requested_modes, source_report) if latest_grounded_turn_available else {}
	target_report = ""
	if latest_grounded_turn_available and target_capability_id:
		target_report = resolve_target_report_for_capability(source_report, target_capability_id)
	if latest_grounded_turn_available and not target_report and requested_mode_set.intersection({"filter_refinement"}):
		target_report = source_report
	if latest_grounded_turn_available and not target_report and requested_time_scope:
		target_report = source_report
	requery_requested = bool(
		target_capability_id
		or target_report
		or switch
		or requested_mode_set.intersection({"filter_refinement"})
		or dimension_change_requested
		or requested_time_scope
		or (
			bool(target_dimension)
			and not local_transform_only
			and bool(requested_mode_set.intersection({"dimension_breakdown", "grouping_change"}))
		)
	)
	if latest_grounded_turn_available and self_contained and (
		explicit_query_shape or message_looks_self_contained_business_query
	):
		return build_followup_resolution_contract(
			request_id=request_id,
			mode="new_query",
			requested_modes=requested_modes,
			target_dimension=target_dimension,
			target_limit=target_limit,
			sort_direction=sort_direction,
			target_metric=target_metric,
			requested_columns=requested_columns,
			requested_time_scope=requested_time_scope,
			target_capability_id="",
			target_report="",
			depends_on_grounded_turn=False,
			self_contained=True,
			latest_grounded_turn_available=True,
			reason=semantic_reason or "The request restates a full governed ERP query and should not inherit the prior grounded date context implicitly.",
		)

	if latest_grounded_turn_available and local_transform_only and not target_capability_id and not requested_time_scope and not self_contained:
		return build_followup_resolution_contract(
			request_id=request_id,
			mode="local_grounded_transform",
			requested_modes=requested_modes,
			target_dimension=target_dimension,
			target_limit=target_limit,
			sort_direction=sort_direction,
			target_metric=target_metric,
			requested_columns=requested_columns,
			requested_time_scope=requested_time_scope,
			target_capability_id="",
			target_report="",
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="The request can be resolved deterministically from the latest grounded answer using local capability adapters.",
		)
	if latest_grounded_turn_available and requery_requested:
		return build_followup_resolution_contract(
			request_id=request_id,
			mode="capability_requery",
			requested_modes=requested_modes,
			target_dimension=target_dimension,
			target_limit=target_limit,
			sort_direction=sort_direction,
			target_metric=target_metric,
			requested_columns=requested_columns,
			requested_time_scope=requested_time_scope,
			target_capability_id=target_capability_id or str(switch.get("capability_id") or "").strip(),
			target_report=target_report or str(switch.get("target_report") or "").strip(),
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason=semantic_reason or "The request needs a governed report switch within the same business capability.",
		)
	if latest_grounded_turn_available and not self_contained:
		return build_followup_resolution_contract(
			request_id=request_id,
			mode="grounded_follow_up",
			requested_modes=requested_modes,
			target_dimension=target_dimension,
			target_limit=target_limit,
			sort_direction=sort_direction,
			target_metric=target_metric,
			requested_columns=requested_columns,
			requested_time_scope=requested_time_scope,
			target_capability_id="",
			target_report="",
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason=degraded_reason or semantic_reason or "The request depends on prior grounded context and is not self-contained.",
		)
	return build_followup_resolution_contract(
		request_id=request_id,
		mode="new_query",
		requested_modes=requested_modes,
		target_dimension=target_dimension,
		target_limit=target_limit,
		sort_direction=sort_direction,
		target_metric=target_metric,
		requested_columns=requested_columns,
		requested_time_scope=requested_time_scope,
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


def _entity_type_from_dimension(value: str) -> str:
	dimension_keys = detect_canonical_keys(str(value or ""), dimension_or_metric="dimension")
	for key in dimension_keys:
		if key == "supplier":
			return "supplier"
		if key == "customer":
			return "customer"
		if key in {"item_code", "item_name"}:
			return "item"
		if key == "document_name":
			return "sales_invoice"
	return ""


def _artifact_known_references(artifact_payload: Dict[str, Any] | None) -> tuple[List[Dict[str, Any]], List[str]]:
	artifact = dict(artifact_payload or {}) if isinstance(artifact_payload, dict) else {}
	sections = dict(artifact.get("sections") or {}) if isinstance(artifact.get("sections"), dict) else {}
	dimensions = dict(artifact.get("dimensions") or {}) if isinstance(artifact.get("dimensions"), dict) else {}
	family_id = str(artifact.get("family_id") or "").strip()
	known_entities: List[Dict[str, Any]] = []
	known_documents: List[str] = []

	def _append_entity(entity_type: str, label: Any, code: Any = "") -> None:
		name = str(label or "").strip()
		if not name:
			return
		payload = {
			"entity_type": str(entity_type or "").strip(),
			"name": name,
		}
		code_value = str(code or "").strip()
		if code_value:
			payload["code"] = code_value
		if payload not in known_entities:
			known_entities.append(payload)

	if family_id == "transaction_listing":
		document_entity_type = str(
			dimensions.get("document_entity_type")
			or dimensions.get("transaction_type")
			or "sales_invoice"
		).strip()
		for row in sections.get("transaction_rows") or []:
			if not isinstance(row, dict):
				continue
			document_name = str(row.get("document_name") or "").strip()
			customer = str(row.get("customer") or row.get("party_name") or "").strip()
			if document_name:
				known_documents.append(document_name)
				_append_entity(document_entity_type, document_name)
			if customer:
				_append_entity("customer", customer)
	elif family_id == "aging":
		entity_type = "supplier" if str(dimensions.get("aging_type") or "").strip() == "accounts_payable" else "customer"
		for row in sections.get("parties") or []:
			if not isinstance(row, dict):
				continue
			_append_entity(entity_type, row.get("party"))
			voucher_no = str(row.get("voucher_no") or "").strip()
			if voucher_no:
				known_documents.append(voucher_no)
	elif family_id in {"ranking_analytics", "inventory_snapshot"}:
		entity_type = _entity_type_from_dimension(str(dimensions.get("entity_dimension") or "").strip())
		for row in sections.get("ranked_rows") or []:
			if not isinstance(row, dict):
				continue
			_append_entity(entity_type, row.get("entity_name") or row.get("entity"), row.get("entity_code"))
	elif family_id == "product_profitability":
		for row in sections.get("product_rows") or []:
			if not isinstance(row, dict):
				continue
			_append_entity("item", row.get("item_name") or row.get("item_code"), row.get("item_code"))
	elif family_id == "entity_detail":
		entity_type = str(dimensions.get("entity_type") or "").strip()
		entity_label = str(dimensions.get("entity_label") or "").strip()
		entity_key = str(dimensions.get("entity_key") or "").strip()
		if entity_label:
			_append_entity(entity_type, entity_label, entity_key)
		if entity_type in {"sales_invoice", "purchase_invoice"} and entity_key:
			known_documents.append(entity_key)

	return known_entities[:25], list(dict.fromkeys(known_documents))[:25]


def _artifact_matches_runtime_execution(
	*,
	artifact_payload: Dict[str, Any] | None,
	request_id: str,
	source_name: str,
) -> bool:
	artifact = dict(artifact_payload or {})
	if not artifact:
		return False
	artifact_request_id = str(artifact.get("request_id") or "").strip()
	if artifact_request_id:
		return artifact_request_id == str(request_id or "").strip()
	artifact_source_name = str(artifact.get("source_name") or artifact.get("title") or "").strip()
	if artifact_source_name and artifact_source_name == str(source_name or "").strip():
		return True
	artifact_reports = {
		str(item or "").strip()
		for item in (artifact.get("source_reports") or [])
		if str(item or "").strip()
	}
	return bool(source_name) and str(source_name or "").strip() in artifact_reports


def build_grounded_turn_context(
	*,
	request_id: str,
	interaction_contract: InteractionContract,
	assistant_payload: Dict[str, Any],
	runtime_payload: Dict[str, Any],
	artifact_payload: Dict[str, Any] | None = None,
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
	artifact = dict(artifact_payload or {}) if isinstance(artifact_payload, dict) else {}
	if artifact and not _artifact_matches_runtime_execution(
		artifact_payload=artifact,
		request_id=request_id,
		source_name=source_name,
	):
		artifact = {}
	artifact_type = str(artifact.get("artifact_type") or artifact.get("type") or "").strip()
	artifact_source_name = str(artifact.get("source_name") or artifact.get("title") or "").strip()
	is_composite_artifact = artifact_type == "normalized_composite_family_artifact"
	if is_composite_artifact:
		source_kind = "composite_artifact"
		if artifact_source_name:
			source_name = artifact_source_name
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
	artifact_dimensions = artifact.get("dimensions") if isinstance(artifact.get("dimensions"), dict) else {}
	if isinstance(artifact_dimensions, dict):
		for key in (
			"entity_dimension",
			"product_dimension",
			"aging_type",
			"transaction_type",
			"document_label",
		):
			value = str(artifact_dimensions.get(key) or "").strip()
			if value and value not in dimensions:
				dimensions.append(value)
		for metric_key in artifact_dimensions.get("available_metric_keys") or []:
			clean_metric = str(metric_key or "").strip()
			if clean_metric and clean_metric not in metrics:
				metrics.append(clean_metric)
		for metric_key in (
			str(artifact_dimensions.get("requested_metric_key") or "").strip(),
			str(artifact_dimensions.get("primary_metric_key") or "").strip(),
			str(artifact_dimensions.get("primary_metric_label") or "").strip(),
		):
			if metric_key and metric_key not in metrics:
				metrics.append(metric_key)
	known_entities, known_documents = _artifact_known_references(artifact)
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
		artifact_family_id=str(artifact.get("family_id") or "").strip(),
		artifact_type=str(artifact.get("artifact_type") or artifact.get("type") or "").strip(),
		artifact_source_reports=[
			str(item or "").strip()
			for item in (artifact.get("source_reports") or [])
			if str(item or "").strip()
		],
		known_entities=known_entities,
		known_documents=known_documents,
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


def run_phase7a_knowledge_boundary_contract_probe() -> Dict[str, Any]:
	confirmed = build_knowledge_boundary_contract(
		request_id="phase7a-confirmed",
		session_id="phase7a",
		proposed_lane="artifact_lane",
		final_lane="artifact_lane",
		boundary_status="confirmed",
		lane_appropriate=True,
		valid_erp_domain=True,
		grounding_required=False,
		grounding_available=False,
		knowledge_coverage_state="covered",
		reclassification_reason="",
		boundary_flags=[],
		allowed_to_answer=True,
		safe_next_action="allow_current_lane",
		user_response_mode="normal_answer",
		confidence=0.97,
	)
	reclassified = build_knowledge_boundary_contract(
		request_id="phase7a-reclassified",
		session_id="phase7a",
		proposed_lane="reasoning_lane",
		final_lane="valid_erp_domain_uncovered",
		boundary_status="reclassified",
		lane_appropriate=False,
		valid_erp_domain=True,
		grounding_required=True,
		grounding_available=False,
		knowledge_coverage_state="valid_erp_domain_uncovered",
		reclassification_reason="Grounded reasoning is not available for this otherwise valid ERP/business ask.",
		boundary_flags=["missing_grounded_support"],
		allowed_to_answer=False,
		safe_next_action="respond_uncovered_erp_domain",
		user_response_mode="coverage_gap_explanation",
		confidence=0.84,
	)
	confirmed_payload = confirmed.to_payload()
	reclassified_payload = reclassified.to_payload()
	if str(confirmed_payload.get("type") or "").strip() != "qwen_knowledge_boundary_contract":
		raise RuntimeError("Phase 7A probe failed: confirmed boundary payload type mismatch.")
	if str(confirmed_payload.get("boundary_status") or "").strip() != "confirmed":
		raise RuntimeError("Phase 7A probe failed: confirmed boundary status mismatch.")
	if not bool(confirmed_payload.get("lane_appropriate")):
		raise RuntimeError("Phase 7A probe failed: confirmed lane should be appropriate.")
	if str(reclassified_payload.get("knowledge_coverage_state") or "").strip() != "valid_erp_domain_uncovered":
		raise RuntimeError("Phase 7A probe failed: reclassified coverage state mismatch.")
	if str(reclassified_payload.get("safe_next_action") or "").strip() != "respond_uncovered_erp_domain":
		raise RuntimeError("Phase 7A probe failed: safe_next_action mismatch.")
	return {
		"ok": True,
		"confirmed": confirmed_payload,
		"reclassified": reclassified_payload,
	}


def run_phase8a_recovery_contract_probe() -> Dict[str, Any]:
	recovery = build_artifact_enrichment_recovery_contract(
		request_id="phase8a-recovery",
		session_id="phase8a",
		source_request_id="artifact-trace-1",
		source_family_id="customer_rankings",
		source_capability_id="top_customers_by_revenue",
		source_report="Top Customers by Revenue",
		failure_type="artifact_enrichment_incompatible",
		recovery_state="recoverable",
		available_recovery_actions=[
			"keep_current_artifact",
			"run_alternative_governed_query",
			"clarify_target_output",
		],
		recommended_recovery_action="run_alternative_governed_query",
		preservable_scope={"company": "Mingalar Mobile Distribution Co., Ltd."},
		preservable_dimensions=["customer"],
		preservable_metrics=["revenue"],
		preservable_time_context={"range_label": "last month"},
		alternative_capability_id="top_customers_by_quantity",
		alternative_report="Top Customers by Quantity",
		reason="The current artifact cannot provide quantity columns safely, but a governed sibling query exists.",
		allowed_to_recover=True,
		confidence=0.91,
	)
	repair = build_conversational_repair_intent_contract(
		request_id="phase8a-repair",
		session_id="phase8a",
		repair_intent_type="accept_recovery_action",
		repair_state="accepted",
		targets_prior_recovery=True,
		accepted_recovery_action="run_alternative_governed_query",
		guidance_topic="",
		fresh_query_override=False,
		preserve_scope=True,
		preserve_entity_dimension=True,
		preserve_time_context=True,
		reason="The user accepted the governed alternative recovery action.",
		allowed_next_lane="artifact_lane",
		confidence=0.93,
	)
	recovery_payload = recovery.to_payload()
	repair_payload = repair.to_payload()
	if str(recovery_payload.get("type") or "").strip() != "qwen_artifact_enrichment_recovery_contract":
		raise RuntimeError("Phase 8A probe failed: recovery payload type mismatch.")
	if str(recovery_payload.get("recovery_state") or "").strip() != "recoverable":
		raise RuntimeError("Phase 8A probe failed: recovery_state mismatch.")
	if str(recovery_payload.get("recommended_recovery_action") or "").strip() != "run_alternative_governed_query":
		raise RuntimeError("Phase 8A probe failed: recommended recovery action mismatch.")
	if str(repair_payload.get("type") or "").strip() != "qwen_conversational_repair_intent_contract":
		raise RuntimeError("Phase 8A probe failed: repair payload type mismatch.")
	if str(repair_payload.get("repair_intent_type") or "").strip() != "accept_recovery_action":
		raise RuntimeError("Phase 8A probe failed: repair_intent_type mismatch.")
	if not bool(repair_payload.get("targets_prior_recovery")):
		raise RuntimeError("Phase 8A probe failed: repair contract should target prior recovery.")
	return {
		"ok": True,
		"recovery": recovery_payload,
		"repair": repair_payload,
	}


def run_phase8b_recovery_authority_probe() -> Dict[str, Any]:
	compatibility_contract = ArtifactEnrichmentCompatibilityContract(
		request_id="phase8b-compatibility",
		source_family_id="product_rankings",
		source_capability_id="top_products_by_revenue",
		source_report="Top Products by Revenue",
		source_dimension="item_code",
		target_metric="qty",
		requested_columns=["qty"],
		required_metric_keys=["qty"],
		compatibility_status="governed_requery_compatible",
		compatible=False,
		target_capability_id="top_products_by_quantity",
		target_report="Top Products by Quantity",
		candidate_reports_considered=["Top Products by Revenue", "Top Products by Quantity"],
		source_surface_sources=["erp_declared_surface"],
		source_selector_filters=[],
		reason="Quantity cannot be added safely to the current artifact, but a governed sibling query exists.",
	)
	grounded_turn = {
		"request_id": "grounded-turn-1",
		"trace_request_id": "grounded-trace-1",
		"source_name": "Top Products by Revenue",
		"company": "Mingalar Mobile Distribution Co., Ltd.",
		"date_range": {"from_date": "2026-02-01", "to_date": "2026-02-29"},
		"filters": {"company": "Mingalar Mobile Distribution Co., Ltd.", "warehouse": "Yangon Main Warehouse"},
		"dimensions": ["item_code"],
		"metrics": ["revenue"],
		"artifact_family_id": "product_rankings",
	}
	followup_resolution = build_followup_resolution_contract(
		request_id="phase8b-followup",
		mode="family_followup",
		target_dimension="item_code",
		target_metric="qty",
		requested_columns=["qty"],
		requested_time_scope="last month",
		depends_on_grounded_turn=True,
		latest_grounded_turn_available=True,
		reason="The user requested quantity columns over the existing ranking artifact.",
	)
	enrichment_recovery = build_recovery_contract_from_enrichment_compatibility(
		request_id="phase8b-enrichment-recovery",
		session_id="phase8b",
		compatibility_contract=compatibility_contract,
		grounded_turn=grounded_turn,
		followup_resolution=followup_resolution,
	)
	evidence_recovery = build_recovery_contract_from_evidence_boundary(
		request_id="phase8b-evidence-recovery",
		session_id="phase8b",
		artifact_payload={"family_id": "transaction_listing", "source_name": "Sales Invoice List"},
		grounded_turn={
			"request_id": "grounded-turn-2",
			"trace_request_id": "grounded-trace-2",
			"source_name": "Sales Invoice List",
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"date_range": {"from_date": "2026-03-01", "to_date": "2026-03-31"},
			"filters": {"company": "Mingalar Mobile Distribution Co., Ltd."},
			"dimensions": ["invoice"],
			"metrics": ["grand_total", "outstanding_amount"],
			"artifact_family_id": "transaction_listing",
		},
		reason="The current artifact does not include governed delivery evidence.",
	)
	enrichment_payload = enrichment_recovery.to_payload()
	evidence_payload = evidence_recovery.to_payload()
	if str(enrichment_payload.get("recommended_recovery_action") or "").strip() != "run_alternative_governed_query":
		raise RuntimeError("Phase 8B probe failed: governed enrichment recovery did not recommend the governed alternative.")
	if str(enrichment_payload.get("alternative_report") or "").strip() != "Top Products by Quantity":
		raise RuntimeError("Phase 8B probe failed: alternative report mismatch.")
	if str(evidence_payload.get("failure_type") or "").strip() != "grounded_evidence_missing":
		raise RuntimeError("Phase 8B probe failed: evidence-boundary failure type mismatch.")
	if str(evidence_payload.get("recommended_recovery_action") or "").strip() != "clarify_target_output":
		raise RuntimeError("Phase 8B probe failed: evidence-boundary recovery did not recommend clarification.")
	return {
		"ok": True,
		"enrichment_recovery": enrichment_payload,
		"evidence_recovery": evidence_payload,
	}
