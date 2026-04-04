from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Set

from ai_assistant_ui.qwen_chat.metadata import (
	capability_ontology_concepts,
	capability_semantic_tags,
	capability_dimensions_for_report,
	get_report_spec,
	ontology_detect_concepts,
	report_capability_ids,
	report_approved_followup_modes,
	report_family_semantic_tags,
	report_local_followup_adapter,
	report_family_ontology_concepts,
	report_semantic_tags,
)
from ai_assistant_ui.qwen_chat.contracts import (
	FollowUpBoundaryContract,
	build_followup_boundary_contract,
)
from ai_assistant_ui.qwen_chat.semantic_aliases import detect_canonical_keys
from ai_assistant_ui.qwen_chat.scope_decision_input import (
	ScopeDecisionInputContract,
	build_known_unsupported_scope_decision_input,
	build_scope_decision_input,
)


def _normalize_text(text: str) -> str:
	return " ".join(str(text or "").strip().lower().split())


_GOVERNED_DOMAIN_CONCEPTS = {
	"payable",
	"receivable",
	"sales",
	"product",
	"inventory",
	"supplier",
	"customer",
}

_PRIMARY_FRESH_QUERY_FALLBACK_CONCEPTS = {
	"payable",
	"receivable",
	"sales",
	"product",
	"inventory",
}

_PRIMARY_FRESH_QUERY_FALLBACK_ALIASES = {
	"warehouse": "inventory",
}


@dataclass(frozen=True)
class ArtifactContextSignal:
	has_grounded_turn: bool
	report_name: str
	family_id: str
	context_concepts: Set[str]
	available_dimensions: Dict[str, str]
	available_metrics: Dict[str, str]
	available_metric_keys: Set[str]


@dataclass(frozen=True)
class MessageSignal:
	text: str
	concepts: Set[str]


def _clean_governed_domain_concepts(values: List[str] | Set[str] | tuple[str, ...]) -> Set[str]:
	return {
		str(value or "").strip()
		for value in (values or [])
		if str(value or "").strip() in _GOVERNED_DOMAIN_CONCEPTS
	}


def _normalized_dimension_candidates(grounded_turn: Dict[str, object] | None) -> Dict[str, str]:
	turn = grounded_turn if isinstance(grounded_turn, dict) else {}
	report_name = str(turn.get("source_name") or "").strip()
	candidates: Dict[str, str] = {}

	adapter = report_local_followup_adapter(report_name, "dimension_breakdown")
	display_dimension = str(adapter.get("display_dimension_label") or "").strip()
	if display_dimension:
		candidates[_normalize_text(display_dimension)] = display_dimension

	for value in capability_dimensions_for_report(report_name):
		clean = str(value or "").strip()
		if clean:
			candidates.setdefault(_normalize_text(clean), clean)

	for value in turn.get("dimensions") or []:
		clean = str(value or "").strip()
		if clean:
			candidates.setdefault(_normalize_text(clean), clean)

	returned_schema = turn.get("returned_schema")
	if isinstance(returned_schema, list):
		for value in returned_schema[:2]:
			clean = str(value or "").strip()
			if clean:
				candidates.setdefault(_normalize_text(clean), clean)

	return candidates


def _normalized_metric_candidates(grounded_turn: Dict[str, object] | None) -> Dict[str, str]:
	turn = grounded_turn if isinstance(grounded_turn, dict) else {}
	candidates: Dict[str, str] = {}
	for value in turn.get("metrics") or []:
		clean = str(value or "").strip()
		if clean:
			candidates.setdefault(_normalize_text(clean), clean)
	return candidates


def _capability_domain_concepts(capability_id: str) -> Set[str]:
	target = str(capability_id or "").strip()
	if not target:
		return set()
	return _clean_governed_domain_concepts(
		list(capability_ontology_concepts(target)) + list(capability_semantic_tags(target))
	)


def _semantic_reason_domain_concepts(semantic_intent: Any) -> Set[str]:
	if semantic_intent is None:
		return set()
	reason = _normalize_text(str(getattr(semantic_intent, "reason", "") or ""))
	if not reason:
		return set()
	return {
		value
		for value in _clean_governed_domain_concepts(
			ontology_detect_concepts(reason, language="en", include_extended=False)
		)
		if value in _PRIMARY_FRESH_QUERY_FALLBACK_CONCEPTS
	}


def _report_domain_concepts(report_name: str, family_id: str = "") -> Set[str]:
	out: Set[str] = set()
	report_value = str(report_name or "").strip()
	family_value = str(family_id or "").strip()
	if report_value:
		out.update(_clean_governed_domain_concepts(report_semantic_tags(report_value)))
	if family_value:
		out.update(_clean_governed_domain_concepts(report_family_semantic_tags(family_value)))
	if out:
		return out
	if report_value:
		for capability_id in report_capability_ids(report_value):
			out.update(_clean_governed_domain_concepts(capability_semantic_tags(capability_id)))
	if out:
		return out
	if family_value:
		out.update(_clean_governed_domain_concepts(report_family_ontology_concepts(family_value)))
	return out


def _semantic_requested_domains(
	semantic_intent: Any,
	artifact_signal: ArtifactContextSignal,
) -> Set[str]:
	if semantic_intent is None:
		return set()
	requested_modes = {
		str(mode or "").strip()
		for mode in (getattr(semantic_intent, "requested_modes", []) or [])
		if str(mode or "").strip()
	}
	target_capability_id = str(getattr(semantic_intent, "target_capability_id", "") or "").strip()
	target_dimension = str(getattr(semantic_intent, "target_dimension", "") or "").strip()
	target_limit = int(getattr(semantic_intent, "target_limit", 0) or 0)
	sort_direction = str(getattr(semantic_intent, "sort_direction", "") or "").strip()
	target_metric = str(getattr(semantic_intent, "target_metric", "") or "").strip()
	requested_columns = list(getattr(semantic_intent, "requested_columns", []) or [])
	requested_time_scope = str(getattr(semantic_intent, "requested_time_scope", "") or "").strip()

	out = _capability_domain_concepts(target_capability_id)
	if not out:
		out.update(_semantic_reason_domain_concepts(semantic_intent))
	structured_followup_signals = bool(
		target_capability_id
		or requested_time_scope
		or target_metric
		or requested_columns
		or (target_dimension and requested_modes.intersection({"dimension_breakdown", "grouping_change"}))
		or ((target_limit or sort_direction) and "sort_or_limit" in requested_modes)
	)
	if not out and structured_followup_signals:
		out.update(artifact_signal.context_concepts)
	return out


def _artifact_context_signal(grounded_turn: Dict[str, object] | None) -> ArtifactContextSignal:
	turn = grounded_turn if isinstance(grounded_turn, dict) else {}
	report_name = str(turn.get("source_name") or "").strip()
	family_id = str(turn.get("artifact_family_id") or "").strip()
	context_concepts = _report_domain_concepts(report_name, family_id)
	if not context_concepts:
		for source_report in (turn.get("artifact_source_reports") or []):
			clean_report = str(source_report or "").strip()
			if clean_report:
				context_concepts.update(_report_domain_concepts(clean_report))
	available_metrics = _normalized_metric_candidates(turn)
	available_metric_keys: Set[str] = set()
	for label in available_metrics.values():
		available_metric_keys.update(detect_canonical_keys(label, dimension_or_metric="metric"))
	return ArtifactContextSignal(
		has_grounded_turn=bool(turn.get("grounded")),
		report_name=report_name,
		family_id=family_id,
		context_concepts=context_concepts,
		available_dimensions=_normalized_dimension_candidates(turn),
		available_metrics=available_metrics,
		available_metric_keys=available_metric_keys,
	)

def _message_signal(
	message: str,
	*,
	language: str = "en",
) -> MessageSignal:
	text = _normalize_text(message)
	detection_text = text.replace("/", " ")
	concepts = set(ontology_detect_concepts(detection_text, language=language, include_extended=False))
	return MessageSignal(
		text=text,
		concepts=concepts,
	)


def _domain_affinity(requested_domains: Set[str], context_domains: Set[str]) -> str:
	if not requested_domains or not context_domains:
		return "unknown"
	if requested_domains.isdisjoint(context_domains):
		return "disjoint"
	if requested_domains.issubset(context_domains) or context_domains.issubset(requested_domains):
		return "same_domain"
	return "partial_overlap"


def _allow_message_domain_fallback(
	message_concepts: Set[str],
	artifact_signal: ArtifactContextSignal,
	*,
	grounded_followup_supported: bool,
	semantic_payload_blank_for_domain_fallback: bool = False,
	contradictory_presentation_hint: bool = False,
) -> bool:
	if not message_concepts:
		return False
	if not artifact_signal.has_grounded_turn:
		return True
	context_domains = set(artifact_signal.context_concepts)
	if not grounded_followup_supported:
		if semantic_payload_blank_for_domain_fallback and not contradictory_presentation_hint:
			return len(message_concepts) >= 2
		if not context_domains:
			return True
		if len(message_concepts) >= 2:
			return True
		return message_concepts.isdisjoint(context_domains)
	if not context_domains:
		return True
	return message_concepts.isdisjoint(context_domains)


def _degraded_message_fallback_concepts(message_concepts: Set[str]) -> Set[str]:
	out: Set[str] = set()
	for value in (message_concepts or set()):
		clean = str(value or "").strip()
		if not clean:
			continue
		if clean in _PRIMARY_FRESH_QUERY_FALLBACK_CONCEPTS:
			out.add(clean)
			continue
		alias = str(_PRIMARY_FRESH_QUERY_FALLBACK_ALIASES.get(clean) or "").strip()
		if alias:
			out.add(alias)
	return out


def _semantic_reason_indicates_creative_non_business_request(semantic_intent: Any) -> bool:
	if semantic_intent is None:
		return False
	requested_modes = {
		str(mode or "").strip()
		for mode in (getattr(semantic_intent, "requested_modes", []) or [])
		if str(mode or "").strip()
	}
	if not requested_modes or requested_modes.difference({"presentation_transform", "table_presentation", "bullet_presentation"}):
		return False
	target_capability_id = str(getattr(semantic_intent, "target_capability_id", "") or "").strip()
	requested_time_scope = str(getattr(semantic_intent, "requested_time_scope", "") or "").strip()
	requested_columns = [str(value or "").strip() for value in (getattr(semantic_intent, "requested_columns", []) or []) if str(value or "").strip()]
	if target_capability_id or requested_time_scope or requested_columns:
		return False
	reason = _normalize_text(str(getattr(semantic_intent, "reason", "") or ""))
	return "creative" in reason


def _reasoning_semantic_result_indicates_creative_non_business_request(reasoning_semantic_result: Any) -> bool:
	if reasoning_semantic_result is None:
		return False
	if str(getattr(reasoning_semantic_result, "status", "") or "").strip() != "accepted":
		return False
	intent = getattr(reasoning_semantic_result, "intent", None)
	if intent is None:
		return False
	reason = _normalize_text(str(getattr(intent, "reason", "") or ""))
	return "creative" in reason


def build_followup_boundary_contract_from_context(
	message: str,
	*,
	request_id: str = "",
	session_id: str = "",
	language: str = "en",
	grounded_turn: Dict[str, Any] | None = None,
	semantic_intent: Any | None = None,
	reasoning_semantic_result: Any | None = None,
) -> FollowUpBoundaryContract:
	artifact_signal = _artifact_context_signal(grounded_turn)
	grounded_followup_supported = bool(report_approved_followup_modes(artifact_signal.report_name)) if artifact_signal.report_name else False
	semantic_requested_domains = _semantic_requested_domains(semantic_intent, artifact_signal)
	semantic_payload_has_structured_signals = False
	contradictory_presentation_hint = False
	semantic_requested_mode_set: Set[str] = set()
	if semantic_intent is not None:
		semantic_requested_mode_set = {
			str(mode or "").strip()
			for mode in (getattr(semantic_intent, "requested_modes", []) or [])
			if str(mode or "").strip()
		}
		target_capability_id = str(getattr(semantic_intent, "target_capability_id", "") or "").strip()
		target_dimension = str(getattr(semantic_intent, "target_dimension", "") or "").strip()
		target_limit = int(getattr(semantic_intent, "target_limit", 0) or 0)
		sort_direction = str(getattr(semantic_intent, "sort_direction", "") or "").strip()
		target_metric = str(getattr(semantic_intent, "target_metric", "") or "").strip()
		requested_columns = list(getattr(semantic_intent, "requested_columns", []) or [])
		requested_time_scope = str(getattr(semantic_intent, "requested_time_scope", "") or "").strip()
		non_presentation_requested_modes = [
			mode
			for mode in semantic_requested_mode_set
			if mode not in {"presentation_transform", "table_presentation", "bullet_presentation"}
		]
		query_like_payload_fields_present = bool(
			target_capability_id
			or requested_time_scope
			or target_metric
			or requested_columns
			or target_dimension
			or target_limit
			or sort_direction
		)
		semantic_payload_has_structured_signals = bool(
			target_capability_id
			or requested_time_scope
			or target_metric
			or requested_columns
			or (target_dimension and semantic_requested_mode_set.intersection({"dimension_breakdown", "grouping_change"}))
			or ((target_limit or sort_direction) and "sort_or_limit" in semantic_requested_mode_set)
		)
		contradictory_presentation_hint = bool(semantic_requested_mode_set) and not non_presentation_requested_modes and query_like_payload_fields_present
	message_concepts: Set[str] = set()
	degraded_message_fallback_allowed = False
	degraded_message_fallback_used = False
	known_uncovered_decision = None
	requested_domain_source = "semantic_runtime" if semantic_intent is not None else "none"
	semantic_payload_blank_for_domain_fallback = bool(
		semantic_intent is not None
		and not semantic_payload_has_structured_signals
		and not semantic_requested_mode_set
	)
	semantic_payload_allows_degraded_domain_fallback = bool(
		semantic_intent is None
		or (
			semantic_payload_blank_for_domain_fallback
			and (not artifact_signal.has_grounded_turn or not grounded_followup_supported)
		)
		or contradictory_presentation_hint
	)
	if not semantic_requested_domains:
		known_uncovered_decision = build_known_unsupported_scope_decision_input(
			raw_message=message,
			context_domains=sorted(artifact_signal.context_concepts),
		)
		if known_uncovered_decision is not None:
			requested_domain_source = "known_uncovered_scope"
		elif semantic_payload_allows_degraded_domain_fallback:
			signal = _message_signal(message, language=language)
			candidate_message_concepts = _degraded_message_fallback_concepts(set(signal.concepts))
			degraded_message_fallback_allowed = _allow_message_domain_fallback(
				candidate_message_concepts,
				artifact_signal,
				grounded_followup_supported=grounded_followup_supported,
				semantic_payload_blank_for_domain_fallback=semantic_payload_blank_for_domain_fallback,
				contradictory_presentation_hint=contradictory_presentation_hint,
			)
			if degraded_message_fallback_allowed:
				message_concepts = candidate_message_concepts
				degraded_message_fallback_used = bool(message_concepts)
				requested_domain_source = "message_fallback" if semantic_intent is None else "degraded_semantic_message_fallback"
			elif candidate_message_concepts:
				requested_domain_source = "message_fallback_denied"
	requested_domains = set(
		semantic_requested_domains
		or (
			list(getattr(known_uncovered_decision, "requested_domains", []) or [])
			if known_uncovered_decision is not None
			else message_concepts
		)
	)
	business_signals = bool(requested_domains)
	has_semantic_intent = semantic_intent is not None
	semantic_grounded_followup = False
	self_contained = False
	contradictory_presentation_payload = False
	out_of_scope_signal = bool(getattr(known_uncovered_decision, "out_of_scope", False))
	primary_domain = str(getattr(known_uncovered_decision, "primary_domain", "") or "").strip()
	structured_followup_modes: List[str] = []
	structured_followup_signals_present = False
	target_dimension = ""
	target_metric = ""
	if has_semantic_intent:
		structured_followup_modes = [
			str(mode or "").strip()
			for mode in (getattr(semantic_intent, "requested_modes", []) or [])
			if str(mode or "").strip()
		]
		requested_mode_set = set(structured_followup_modes)
		non_presentation_requested_modes = [
			mode
			for mode in structured_followup_modes
			if mode not in {"presentation_transform", "table_presentation", "bullet_presentation"}
		]
		target_capability_id = str(getattr(semantic_intent, "target_capability_id", "") or "").strip()
		target_dimension = str(getattr(semantic_intent, "target_dimension", "") or "").strip()
		target_limit = int(getattr(semantic_intent, "target_limit", 0) or 0)
		sort_direction = str(getattr(semantic_intent, "sort_direction", "") or "").strip()
		target_metric = str(getattr(semantic_intent, "target_metric", "") or "").strip()
		requested_columns = list(getattr(semantic_intent, "requested_columns", []) or [])
		requested_time_scope = str(getattr(semantic_intent, "requested_time_scope", "") or "").strip()
		query_like_payload_fields_present = bool(
			target_capability_id
			or requested_time_scope
			or target_metric
			or requested_columns
			or target_dimension
			or target_limit
			or sort_direction
		)
		structured_followup_signals_present = bool(
			target_capability_id
			or requested_time_scope
			or target_metric
			or requested_columns
			or (target_dimension and requested_mode_set.intersection({"dimension_breakdown", "grouping_change"}))
			or ((target_limit or sort_direction) and "sort_or_limit" in requested_mode_set)
		)
		contradictory_presentation_payload = bool(structured_followup_modes) and not non_presentation_requested_modes and query_like_payload_fields_present
		self_contained = bool(getattr(semantic_intent, "self_contained", False)) and bool(
			requested_domains
			or target_capability_id
			or requested_time_scope
			or target_metric
			or requested_columns
			or (target_dimension and requested_mode_set.intersection({"dimension_breakdown", "grouping_change"}))
		)
		creative_non_business_signal = _semantic_reason_indicates_creative_non_business_request(semantic_intent)
		semantic_grounded_followup = bool(
			non_presentation_requested_modes
			or structured_followup_signals_present
		) and not self_contained and not contradictory_presentation_payload and not creative_non_business_signal
	else:
		creative_non_business_signal = False
	if not creative_non_business_signal:
		creative_non_business_signal = _reasoning_semantic_result_indicates_creative_non_business_request(
			reasoning_semantic_result
		)
	if not semantic_grounded_followup and not self_contained:
		if not artifact_signal.has_grounded_turn and business_signals:
			self_contained = True
		elif artifact_signal.has_grounded_turn and business_signals and not grounded_followup_supported:
			self_contained = True

	context_domains = set(artifact_signal.context_concepts)
	affinity = _domain_affinity(requested_domains, context_domains)
	ranking_projection_safe = bool(
		contradictory_presentation_payload
		and artifact_signal.family_id == "ranking_analytics"
		and target_dimension
		and _normalize_text(target_dimension) in artifact_signal.available_dimensions
		and (
			not target_metric
			or _normalize_text(target_metric) in artifact_signal.available_metrics
			or bool(
				set(detect_canonical_keys(target_metric, dimension_or_metric="metric")).intersection(
					artifact_signal.available_metric_keys
				)
			)
		)
	)
	decision = "stay_grounded"
	reason = ""
	if out_of_scope_signal:
		decision = "force_fresh_query"
		reason = str(getattr(known_uncovered_decision, "reason", "") or "").strip()
	elif creative_non_business_signal:
		out_of_scope_signal = True
		decision = "force_fresh_query"
		reason = "The request asks for creative content generation rather than a governed ERP/business follow-up."
	elif (
		not semantic_grounded_followup
		and not self_contained
		and requested_domains
		and context_domains
		and requested_domains.isdisjoint(context_domains)
	):
		decision = "force_fresh_query"
		reason = "The request shifts to a different governed business area and should not inherit the prior artifact."
	elif (
		contradictory_presentation_payload
		and not ranking_projection_safe
		and (business_signals or has_semantic_intent)
	):
		decision = "force_fresh_query"
		reason = "The presentation-only semantic payload carries conflicting query fields and must break out to a fresh governed query."
	elif self_contained:
		decision = "force_fresh_query"
		reason = "The request is self-contained and should be treated as a fresh governed ERP question."
	elif not semantic_grounded_followup and not business_signals:
		decision = "fail_closed_to_reasoning"
	else:
		decision = "stay_grounded"

	return build_followup_boundary_contract(
		request_id=request_id,
		session_id=session_id,
		source_family_id=artifact_signal.family_id,
		source_report_name=artifact_signal.report_name,
		grounded_context_domains=sorted(context_domains),
		requested_domains=sorted(requested_domains),
		structured_followup_modes=structured_followup_modes,
		structured_business_signals_present=structured_followup_signals_present,
		grounded_followup_supported=grounded_followup_supported,
		self_contained_signal=self_contained,
		contradictory_payload=contradictory_presentation_payload,
		degraded_message_fallback_allowed=degraded_message_fallback_allowed,
		degraded_message_fallback_used=degraded_message_fallback_used,
		out_of_scope_signal=out_of_scope_signal,
		primary_domain=primary_domain,
		domain_affinity=affinity,
		recommended_boundary_decision=decision,
		decision_reason=reason,
		resolution_source={
			"requested_domains": requested_domain_source,
			"context_domains": "grounded_metadata",
			"boundary_decision": "governed_boundary_rules",
		},
	)


def evaluate_followup_boundary_contract(
	boundary_contract: FollowUpBoundaryContract,
) -> ScopeDecisionInputContract:
	requested_domains = [
		str(value or "").strip()
		for value in (getattr(boundary_contract, "requested_domains", []) or [])
		if str(value or "").strip()
	]
	context_domains = [
		str(value or "").strip()
		for value in (getattr(boundary_contract, "grounded_context_domains", []) or [])
		if str(value or "").strip()
	]
	primary_domain = str(getattr(boundary_contract, "primary_domain", "") or "").strip()
	decision = str(getattr(boundary_contract, "recommended_boundary_decision", "") or "").strip()
	reason = str(getattr(boundary_contract, "decision_reason", "") or "").strip()
	if bool(getattr(boundary_contract, "out_of_scope_signal", False)):
		return build_scope_decision_input(
			force_new_query=True,
			out_of_scope=True,
			reason=reason,
			requested_domains=requested_domains,
			context_domains=context_domains,
			primary_domain=primary_domain,
		)
	if decision == "force_fresh_query":
		return build_scope_decision_input(
			force_new_query=True,
			out_of_scope=False,
			reason=reason,
			requested_domains=requested_domains,
			context_domains=context_domains,
			primary_domain=primary_domain,
		)
	return build_scope_decision_input(
		force_new_query=False,
		out_of_scope=False,
		reason="",
		requested_domains=requested_domains,
		context_domains=context_domains,
		primary_domain=primary_domain,
	)


def assess_context_isolation(
	message: str,
	*,
	language: str = "en",
	grounded_turn: Dict[str, Any] | None = None,
	semantic_intent: Any | None = None,
	reasoning_semantic_result: Any | None = None,
) -> ScopeDecisionInputContract:
	boundary_contract = build_followup_boundary_contract_from_context(
		message,
		language=language,
		grounded_turn=grounded_turn,
		semantic_intent=semantic_intent,
		reasoning_semantic_result=reasoning_semantic_result,
	)
	return evaluate_followup_boundary_contract(boundary_contract)
