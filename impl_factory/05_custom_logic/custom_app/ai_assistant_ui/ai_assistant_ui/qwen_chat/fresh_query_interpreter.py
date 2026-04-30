from __future__ import annotations

import datetime as dt
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.compiler import CompilerOutcome, compile_fresh_query
from ai_assistant_ui.qwen_chat.composite_reads import execute_composite_read_plan, plan_composite_read
from ai_assistant_ui.qwen_chat.contracts import (
	FreshQueryInterpretationContract,
	_infer_followup_requested_time_scope,
	build_compiled_execution_audit_contract,
	build_fresh_query_interpretation_contract,
	build_interaction_contract,
	build_response_policy_contract,
)
from ai_assistant_ui.qwen_chat.artifact_narrative import (
	build_artifact_narrative_context,
	build_artifact_narrative_contract,
	narrate_governed_artifact,
)
from ai_assistant_ui.qwen_chat.entity_reference_resolution import (
	infer_entity_grains_from_message,
	normalize_master_data_lookup_slots,
	resolve_entity_reference_from_message,
)
from ai_assistant_ui.qwen_chat.family_adapters import build_normalized_family_artifact
from ai_assistant_ui.qwen_chat.family_rendering import render_normalized_family_response
from ai_assistant_ui.qwen_chat.family_validator import validate_normalized_family_artifact
from ai_assistant_ui.qwen_chat.governed_scope_registry import (
	active_listing_view_aliases,
	master_data_lookup_mode_allowed,
)
from ai_assistant_ui.qwen_chat.governed_report_executor import execute_governed_report
from ai_assistant_ui.qwen_chat.metadata import (
	capability_report_names,
	capability_default_report_name,
	capability_fresh_query_defaults,
	capability_intent_classes,
	capability_ontology_concepts,
	entity_grain_display_label,
	get_entity_reference_policy_spec,
	get_report_family_spec,
	get_report_spec,
	financial_statement_report_name,
	list_capability_specs,
	list_composite_read_specs,
	list_intent_class_specs,
	load_semantic_resolution_registry,
	ontology_detect_concepts,
	report_business_family_ids,
	report_capability_ids,
	report_direct_query_filter_value_aliases,
	report_family_capability_ids,
	report_family_ids_for_intent_class,
	report_semantic_tags,
	report_supported_dimensions,
	report_supported_intent_classes,
	report_supported_metrics,
)
from ai_assistant_ui.qwen_chat.runtime_client import (
	QwenRuntimeClientError,
	call_qwen_runtime_chat,
	call_qwen_runtime_fresh_query_interpretation,
)
from ai_assistant_ui.qwen_chat.probes.fresh_query_diagnostics import (
	run_phase4_audit_observability_smoke,
	run_phase4_compiled_execution_smoke,
	run_phase4_fresh_query_cache_smoke,
	run_phase4_fresh_query_inflight_smoke,
	run_phase4_fresh_query_interpreter_selftests,
	run_phase4_fresh_query_pipeline_smokes,
	run_phase4_semantic_validation_smoke,
	run_phase4_slice5_selftests,
	run_phase4_slice6_selftests,
	run_phase4b_aging_family_probe,
	run_phase4b_aging_family_smoke,
	run_phase4b_broad_financial_report_ambiguity_probe,
	run_phase4b_composite_read_debug,
	run_phase4b_composite_read_probe,
	run_phase4b_composite_read_smoke,
	run_phase4b_family_rendering_smoke,
	run_phase4b_financial_statement_family_probe,
	run_phase4b_financial_statement_family_smoke,
	run_phase4b_inventory_product_family_probe,
	run_phase4b_inventory_product_family_smoke,
	run_phase4b_ranking_trend_family_probe,
	run_phase4b_ranking_trend_family_smoke,
)
from ai_assistant_ui.qwen_chat.semantic_resolution import (
	resolve_interpretation_semantically,
)
from ai_assistant_ui.qwen_chat.semantic_resolution_registry import (
	semantic_slot_alias_match_details,
	semantic_resolution_governs_intent,
)
from ai_assistant_ui.qwen_chat.semantic_aliases import detect_canonical_keys, get_erp_field_mapping
from ai_assistant_ui.qwen_chat.semantic_validator import (
	validate_compiled_semantic_result,
)
try:
	import frappe  # type: ignore
except Exception:  # pragma: no cover
	frappe = None


_ALLOWED_PRESENTATION_MODES = {"presentation_transform", "table_presentation"}
_ALLOWED_AMBIGUITY_FLAGS = {
	"missing_time_scope",
	"missing_metric",
	"missing_dimension",
	"ambiguous_business_object",
	"ambiguous_capability",
	"ambiguous_report",
	"underspecified_request",
	"unsupported_request",
}
_RUNTIME_DEFAULT_MODEL_OVERRIDE = "__runtime_default__"


def _family_narrative_prefers_rendered_response(
	*,
	family_id: str,
	response_policy: Dict[str, Any] | None,
) -> bool:
	clean_family = str(family_id or "").strip().lower()
	policy = dict(response_policy or {}) if isinstance(response_policy, dict) else {}
	if clean_family == "financial_statement":
		if bool(policy.get("analysis_requested")):
			return False
		if bool(policy.get("implication_allowed")) or bool(policy.get("recommendation_allowed")):
			return False
		return True
	if clean_family in {"ranking_analytics", "product_profitability"}:
		if bool(policy.get("analysis_requested")):
			return False
		if bool(policy.get("implication_allowed")) or bool(policy.get("recommendation_allowed")):
			return False
		return True
	if clean_family != "aging":
		return False
	if bool(policy.get("analysis_requested")):
		return False
	if bool(policy.get("implication_allowed")) or bool(policy.get("recommendation_allowed")):
		return False
	return True


@dataclass(frozen=True)
class SemanticFreshQueryResult:
	status: str
	interpretation: FreshQueryInterpretationContract | None = None
	confidence_threshold: float = 0.72
	runtime_error: str = ""
	validation_error: str = ""
	agent_meta: Dict[str, Any] = field(default_factory=dict)

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_semantic_fresh_query_interpretation",
			"contract_version": "1.0",
			"status": self.status,
			"confidence_threshold": self.confidence_threshold,
			"runtime_error": self.runtime_error,
			"validation_error": self.validation_error,
			"interpretation": self.interpretation.to_payload() if self.interpretation else {},
			"agent_meta": self.agent_meta if isinstance(self.agent_meta, dict) else {},
		}


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def _normalize_key(value: Any) -> str:
	text = str(value or "").strip().lower()
	text = re.sub(r"[^a-z0-9]+", "_", text)
	return text.strip("_")


def _extract_structural_target_limit_seed(message: str) -> int:
	text = str(message or "").strip().lower()
	if not text:
		return 0
	match = re.search(r"\b(?:top|last|latest)\s+(\d{1,2})\b", text)
	if not match:
		return 0
	if re.match(
		r"\s+(?:day|days|week|weeks|month|months|year|years|quarter|quarters)\b",
		text[match.end():],
	):
		return 0
	try:
		return max(0, min(50, int(match.group(1) or 0)))
	except Exception:
		return 0


def _normalized_lookup(values: List[str]) -> Dict[str, str]:
	out: Dict[str, str] = {}
	for value in values:
		clean = str(value or "").strip()
		if not clean:
			continue
		out[_normalize_key(clean)] = clean
	return out


def _governed_time_scope_aliases(canonical_scope: str) -> List[str]:
	scope = _normalize_time_scope(canonical_scope)
	if not scope:
		return []
	out: List[str] = []
	registry = load_semantic_resolution_registry()
	alias_maps = registry.get("alias_maps") if isinstance(registry.get("alias_maps"), dict) else {}
	entries = alias_maps.get("time_scope") if isinstance(alias_maps.get("time_scope"), list) else []
	for entry in entries:
		if not isinstance(entry, dict):
			continue
		if _normalize_time_scope(entry.get("canonical_value")) != scope:
			continue
		out.extend(str(value or "").strip() for value in (entry.get("aliases") or []) if str(value or "").strip())
	return list(dict.fromkeys(out))


def _message_explicitly_requests_time_scope(message: str, canonical_scope: str) -> bool:
	return any(_message_contains_phrase(message, alias) for alias in _governed_time_scope_aliases(canonical_scope))


def _strip_structural_limit_time_scope_conflict(
	*,
	message: str,
	intent_class: str,
	requested_time_scope: str,
	target_limit: int,
) -> str:
	current = str(requested_time_scope or "").strip()
	if intent_class not in {"ranked_entities", "transaction_listing"}:
		return current
	limit = int(max(0, target_limit or 0))
	if not current or limit <= 0:
		return current
	normalized_scope = _normalize_key(current)
	message_text = str(message or "").strip().lower()
	if normalized_scope == "as_of_today":
		if _message_explicitly_requests_time_scope(message, normalized_scope):
			return current
		if _extract_structural_target_limit_seed(message_text) == limit:
			return ""
	if normalized_scope == "latest":
		if re.search(
			r"\b(?:last|latest)\s+"
			+ re.escape(str(limit))
			+ r"\s+(?:day|days|week|weeks|month|months|year|years|quarter|quarters)\b",
			message_text,
		):
			return current
		return ""
	latest_limit_match = re.fullmatch(r"latest_(\d{1,2})", normalized_scope)
	if latest_limit_match:
		try:
			latest_count = int(latest_limit_match.group(1) or 0)
		except Exception:
			latest_count = 0
		if latest_count == limit:
			if re.search(
				r"\b(?:last|latest)\s+"
				+ re.escape(str(limit))
				+ r"\s+(?:day|days|week|weeks|month|months|year|years|quarter|quarters)\b",
				message_text,
			):
				return current
			return ""
	match = re.fullmatch(
		r"last_(\d{1,2})_(days|weeks|months|years|quarters)",
		normalized_scope,
	)
	if not match:
		return current
	try:
		scope_count = int(match.group(1) or 0)
	except Exception:
		return current
	if scope_count != limit:
		return current
	if re.search(
		r"\b(?:last|past|previous|prior)\s+"
		+ re.escape(str(limit))
		+ r"\s+(?:day|days|week|weeks|month|months|year|years|quarter|quarters)\b",
		message_text,
	):
		return current
	return ""


def _clear_time_scope_slots(extracted_slots: Dict[str, Any]) -> Dict[str, Any]:
	if not isinstance(extracted_slots, dict):
		return {}
	cleaned = dict(extracted_slots)
	for fieldname in ("report_date", "from_date", "to_date", "period_start_date", "period_end_date"):
		cleaned.pop(fieldname, None)
	slot_filters = cleaned.get("filters")
	if isinstance(slot_filters, dict):
		cleaned_filters = dict(slot_filters)
		for fieldname in ("report_date", "from_date", "to_date", "period_start_date", "period_end_date"):
			cleaned_filters.pop(fieldname, None)
		cleaned["filters"] = cleaned_filters
	return cleaned


def _message_contains_explicit_date_literal(message: str) -> bool:
	text = str(message or "").strip()
	if not text:
		return False
	if re.search(r"\d{4}-\d{2}-\d{2}", text):
		return True
	if re.search(r"\d{1,2}/\d{1,2}/\d{2,4}", text):
		return True
	return False


def _strip_unrequested_today_scope_for_transaction_listing(
	*,
	message: str,
	intent_class: str,
	requested_time_scope: str,
	extracted_slots: Dict[str, Any],
) -> str:
	current = str(requested_time_scope or "").strip()
	if intent_class != "transaction_listing":
		return current
	if _normalize_time_scope(current) != "as_of_today":
		return current
	if _message_explicitly_requests_time_scope(message, "as_of_today"):
		return current
	if _message_contains_explicit_date_literal(message):
		return current
	return ""


def _normalize_time_scope(value: Any) -> str:
	key = _normalize_key(value)
	if not key:
		return ""
	if key in {"undefined", "none", "null", "na", "n_a", "unknown"}:
		return ""
	if re.fullmatch(r"\d{4}_\d{2}_\d{2}", key):
		return ""
	if key in {"as_of_today", "as_of_now", "today", "now", "current_date", "current_date_utc"}:
		return "as_of_today"
	if key in {"current_period", "this_period", "this_month", "current_month"}:
		return "current_period"
	if key in {"last_month", "previous_month", "prior_month"}:
		return "last_month"
	if key == "last_year":
		return "last_year"
	if key in {"current_fiscal_year_to_date", "fiscal_year_to_date", "year_to_date", "this_fiscal_year"}:
		return "current_fiscal_year_to_date"
	if key in {"all_period", "all_time", "overall"}:
		return "all_period"
	return key


def _confidence_threshold() -> float:
	default = 0.72
	if frappe is None:
		return default
	try:
		raw = (getattr(frappe, "conf", None) or {}).get("qwen_fresh_query_min_confidence", default)
		return max(0.0, min(1.0, float(raw)))
	except Exception:
		return default


def _current_date_iso() -> str:
	return dt.datetime.now(dt.timezone.utc).date().isoformat()


def _clean_iso_date(value: Any) -> str:
	text = str(value or "").strip()
	if not text:
		return ""
	try:
		return dt.date.fromisoformat(text).isoformat()
	except Exception:
		return ""


def _sanitize_extracted_slots(
	extracted_slots: Dict[str, Any],
) -> Dict[str, Any]:
	clean_slots: Dict[str, Any] = {}
	for key in ("report_date", "from_date", "to_date"):
		normalized = _clean_iso_date(extracted_slots.get(key))
		if normalized:
			clean_slots[key] = normalized
	slot_filters = extracted_slots.get("filters")
	if isinstance(slot_filters, dict):
		filters = {
			str(key or "").strip(): value
			for key, value in slot_filters.items()
			if str(key or "").strip() and str(key or "").strip().lower() != "company"
		}
		if filters:
			clean_slots["filters"] = filters
	composite_profile_lookup = {
		str(item.get("plan_id") or "").strip()
		for item in list_composite_read_specs()
		if isinstance(item, dict) and str(item.get("plan_id") or "").strip()
	}
	composite_profile_context = [
		value
		for value in _clean_list(extracted_slots.get("composite_profile_context"))
		if value in composite_profile_lookup
	]
	if composite_profile_context:
		clean_slots["composite_profile_context"] = list(dict.fromkeys(composite_profile_context))
	return clean_slots


def _build_interpretation_context() -> Dict[str, Any]:
	registry = load_semantic_resolution_registry()
	slot_definitions = [
		{
			"slot_name": str(item.get("slot_name") or "").strip(),
			"allowed_values": _clean_list(item.get("allowed_values")),
		}
		for item in (registry.get("slot_definitions") or [])
		if isinstance(item, dict) and str(item.get("slot_name") or "").strip()
	]
	alias_maps = (
		{str(key): value for key, value in registry.get("alias_maps", {}).items()}
		if isinstance(registry.get("alias_maps"), dict)
		else {}
	)
	intent_classes = [
		{
			"intent_class_id": str(item.get("intent_class_id") or "").strip(),
			"semantic_tags": _clean_list(item.get("semantic_tags")),
		}
		for item in list_intent_class_specs()
		if isinstance(item, dict) and str(item.get("intent_class_id") or "").strip()
	]
	capabilities = [
		{
			"capability_id": str(item.get("capability_id") or "").strip(),
			"intent_classes": _clean_list(item.get("intent_classes")),
			"report_names": _clean_list(item.get("report_names")),
			"dimensions": _clean_list(item.get("dimensions")),
			"metrics": _clean_list(item.get("metrics")),
			"ontology_concepts": _clean_list(item.get("ontology_concepts")),
		}
		for item in list_capability_specs()
		if isinstance(item, dict) and str(item.get("capability_id") or "").strip()
	]
	composite_profiles = [
		{
			"plan_id": str(item.get("plan_id") or "").strip(),
			"supported_intent_classes": _clean_list(item.get("supported_intent_classes")),
			"required_concepts_all": _clean_list(item.get("required_concepts_all")),
			"preferred_concepts_any": _clean_list(item.get("preferred_concepts_any")),
		}
		for item in list_composite_read_specs()
		if isinstance(item, dict) and str(item.get("plan_id") or "").strip()
	]
	report_names: List[str] = []
	for capability in capabilities:
		for report_name in _clean_list(capability.get("report_names")):
			if report_name not in report_names:
				report_names.append(report_name)
	reports = [
		{
			"report_name": report_name,
			"capability_ids": _clean_list(report_capability_ids(report_name)),
			"supported_intent_classes": _clean_list(report_supported_intent_classes(report_name)),
			"supported_dimensions": _clean_list(report_supported_dimensions(report_name)),
			"supported_metrics": _clean_list(report_supported_metrics(report_name)),
			"semantic_tags": _clean_list(report_semantic_tags(report_name)),
		}
		for report_name in report_names
		if str(report_name or "").strip()
	]
	return {
		"current_date_utc": _current_date_iso(),
		"single_company_mode": True,
		"company_handling": "compiler_injected_invariant",
		"intent_classes": intent_classes,
		"capabilities": capabilities,
		"reports": reports,
		"composite_profiles": composite_profiles,
		"slot_definitions": slot_definitions,
		"alias_maps": alias_maps,
		"allowed_presentations": sorted(_ALLOWED_PRESENTATION_MODES),
		"allowed_ambiguity_flags": sorted(_ALLOWED_AMBIGUITY_FLAGS),
	}


def _capability_scope(
	intent_class: str,
	candidate_capability_ids: List[str],
	context: Dict[str, Any],
) -> List[Dict[str, Any]]:
	capabilities = [
		dict(item)
		for item in (context.get("capabilities") or [])
		if isinstance(item, dict) and str(item.get("capability_id") or "").strip()
	]
	if candidate_capability_ids:
		selected = {
			str(capability_id or "").strip()
			for capability_id in candidate_capability_ids
			if str(capability_id or "").strip()
		}
		return [item for item in capabilities if str(item.get("capability_id") or "").strip() in selected]
	if intent_class:
		return [
			item
			for item in capabilities
			if intent_class in _clean_list(item.get("intent_classes"))
		]
	return capabilities


def _message_tokens(value: str) -> set[str]:
	text = str(value or "").strip().lower()
	text = re.sub(r"[^a-z0-9]+", " ", text)
	return {token for token in text.split() if token}


def _semantic_resolution_governs_intent(intent_class: str) -> bool:
	return semantic_resolution_governs_intent(intent_class)


def _default_spec_values(spec: Dict[str, Any], key: str) -> List[str]:
	values = spec.get(key)
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def _ordered_capability_ids_for_family(
	*,
	family_id: str,
	intent_class: str,
	message_concepts: List[str],
) -> List[str]:
	candidate_ids = report_family_capability_ids(family_id)
	if not candidate_ids:
		return []
	concept_set = {str(value or "").strip() for value in message_concepts if str(value or "").strip()}
	scored: List[tuple[int, int, str]] = []
	for order_index, capability_id in enumerate(candidate_ids):
		score = 0
		if intent_class and intent_class in capability_intent_classes(capability_id):
			score += 20
		overlap = concept_set & set(capability_ontology_concepts(capability_id))
		score += 25 * len(overlap)
		scored.append((score, order_index, capability_id))
	scored.sort(key=lambda item: (-item[0], item[1]))
	return [capability_id for _score, _order_index, capability_id in scored]


def _resolve_default_report_name(
	*,
	capability_id: str,
	intent_class: str,
	message_concepts: List[str],
	candidate_reports: List[str],
) -> str:
	for report_name in candidate_reports:
		if capability_id in report_capability_ids(report_name):
			return report_name
	spec = capability_fresh_query_defaults(capability_id, intent_class=intent_class)
	report_overrides = spec.get("report_overrides_by_concept")
	if isinstance(report_overrides, dict):
		for concept_id in message_concepts:
			value = str(report_overrides.get(str(concept_id or "").strip()) or "").strip()
			if value:
				return value
	value = str(spec.get("default_report_name") or "").strip()
	if value:
		return value
	return capability_default_report_name(capability_id)


def _intent_supported_reports_for_capability(*, capability_id: str, intent_class: str) -> List[str]:
	allowed_reports = [
		report_name
		for report_name in capability_report_names(capability_id)
		if capability_id in report_capability_ids(report_name)
	]
	if not intent_class:
		return list(dict.fromkeys(_clean_list(allowed_reports)))
	out: List[str] = []
	for report_name in allowed_reports:
		supported_intents = set(report_supported_intent_classes(report_name))
		if not supported_intents or intent_class in supported_intents:
			out.append(report_name)
	return list(dict.fromkeys(_clean_list(out)))


def _resolve_governed_report_candidates(
	*,
	capability_id: str,
	intent_class: str,
	message_concepts: List[str],
	candidate_reports: List[str],
) -> List[str]:
	supported_reports = _intent_supported_reports_for_capability(
		capability_id=capability_id,
		intent_class=intent_class,
	)
	explicit_candidates = [
		report_name
		for report_name in _clean_list(candidate_reports)
		if report_name in supported_reports
	]
	if explicit_candidates:
		return list(dict.fromkeys(explicit_candidates))
	spec = capability_fresh_query_defaults(capability_id, intent_class=intent_class)
	report_overrides = spec.get("report_overrides_by_concept")
	if isinstance(report_overrides, dict):
		override_candidates: List[str] = []
		for concept_id in message_concepts:
			value = str(report_overrides.get(str(concept_id or "").strip()) or "").strip()
			if value and value in supported_reports and value not in override_candidates:
				override_candidates.append(value)
		if override_candidates:
			return override_candidates
	if len(supported_reports) <= 1:
		return supported_reports
	return supported_reports


def _supported_labels_for_report(report_name: str, *, dimension_or_metric: str) -> List[str]:
	if dimension_or_metric == "dimension":
		values = report_supported_dimensions(report_name)
	else:
		values = report_supported_metrics(report_name)
	return [str(value or "").strip() for value in values if str(value or "").strip()]


def _resolve_supported_labels_for_canonical_keys(
	*,
	report_name: str,
	capability_id: str,
	canonical_keys: List[str],
	dimension_or_metric: str,
) -> List[str]:
	supported = _supported_labels_for_report(report_name, dimension_or_metric=dimension_or_metric)
	if not supported:
		return []
	supported_lookup = {_normalize_key(value): value for value in supported}
	out: List[str] = []
	for canonical_key in canonical_keys:
		for field_name in get_erp_field_mapping(canonical_key, report_name):
			canonical = supported_lookup.get(_normalize_key(field_name))
			if canonical and canonical not in out:
				out.append(canonical)
	return out


def _default_labels_from_spec(
	*,
	spec: Dict[str, Any],
	message_concepts: List[str],
	dimension_or_metric: str,
) -> List[str]:
	if dimension_or_metric == "dimension":
		override_key = "dimension_overrides_by_concept"
		default_key = "default_dimensions"
	else:
		override_key = "metric_overrides_by_canonical_key"
		default_key = "default_metrics"
	overrides = spec.get(override_key)
	if dimension_or_metric == "dimension" and isinstance(overrides, dict):
		for concept_id in message_concepts:
			values = overrides.get(str(concept_id or "").strip())
			if isinstance(values, list):
				clean = [str(x or "").strip() for x in values if str(x or "").strip()]
				if clean:
					return clean
	return _default_spec_values(spec, default_key)


def _resolve_requested_labels(
	*,
	message: str,
	report_name: str,
	capability_id: str,
	intent_class: str,
	existing_values: List[str],
	dimension_or_metric: str,
) -> List[str]:
	if existing_values:
		return list(dict.fromkeys(_clean_list(existing_values)))
	spec = capability_fresh_query_defaults(capability_id, intent_class=intent_class)
	canonical_keys = detect_canonical_keys(
		message,
		capability_id=capability_id,
		dimension_or_metric=dimension_or_metric,
	)
	if dimension_or_metric == "metric":
		metric_overrides = spec.get("metric_overrides_by_canonical_key")
		if isinstance(metric_overrides, dict):
			for canonical_key in canonical_keys:
				values = metric_overrides.get(str(canonical_key or "").strip())
				if isinstance(values, list):
					clean = [str(x or "").strip() for x in values if str(x or "").strip()]
					if clean:
						return clean
	resolved = _resolve_supported_labels_for_canonical_keys(
		report_name=report_name,
		capability_id=capability_id,
		canonical_keys=canonical_keys,
		dimension_or_metric=dimension_or_metric,
	)
	if resolved:
		return resolved
	return _default_labels_from_spec(
		spec=spec,
		message_concepts=ontology_detect_concepts(message),
		dimension_or_metric=dimension_or_metric,
	)


def _apply_governed_interpretation_biases(
	*,
	intent_class: str,
	message: str,
	candidate_capability_ids: List[str],
	candidate_reports: List[str],
	requested_dimensions: List[str],
	requested_metrics: List[str],
) -> tuple[List[str], List[str]]:
	intent_key = str(intent_class or "").strip()
	if _semantic_resolution_governs_intent(intent_key):
		return (
			list(dict.fromkeys(_clean_list(candidate_capability_ids))),
			list(dict.fromkeys(_clean_list(candidate_reports))),
		)
	message_concepts = ontology_detect_concepts(message)
	capability_ids = list(dict.fromkeys(_clean_list(candidate_capability_ids)))
	if not capability_ids and intent_key:
		family_id = ""
		if not family_id:
			family_ids = report_family_ids_for_intent_class(intent_key)
			family_id = str((family_ids or [""])[0] or "").strip()
		if family_id:
			capability_ids = _ordered_capability_ids_for_family(
				family_id=family_id,
				intent_class=intent_key,
				message_concepts=message_concepts,
			)
			if capability_ids:
				capability_ids = capability_ids[:1]
	if not capability_ids:
		return [], []
	report_candidates = _resolve_governed_report_candidates(
		capability_id=capability_ids[0],
		intent_class=intent_key,
		message_concepts=message_concepts,
		candidate_reports=_clean_list(candidate_reports),
	)
	if report_candidates:
		return capability_ids, report_candidates
	report_name = _resolve_default_report_name(
		capability_id=capability_ids[0],
		intent_class=intent_key,
		message_concepts=message_concepts,
		candidate_reports=_clean_list(candidate_reports),
	)
	return capability_ids, [report_name] if report_name else []


def _apply_governed_request_defaults(
	*,
	intent_class: str,
	message: str,
	candidate_capability_ids: List[str],
	candidate_reports: List[str],
	requested_dimensions: List[str],
	requested_metrics: List[str],
	requested_time_scope: str,
) -> tuple[List[str], List[str], str]:
	if _semantic_resolution_governs_intent(intent_class):
		return (
			list(dict.fromkeys(_clean_list(requested_dimensions))),
			list(dict.fromkeys(_clean_list(requested_metrics))),
			str(requested_time_scope or "").strip(),
		)
	capability_id = str((_clean_list(candidate_capability_ids) or [""])[0] or "").strip()
	report_name = str((_clean_list(candidate_reports) or [""])[0] or "").strip()
	dimensions = _resolve_requested_labels(
		message=message,
		report_name=report_name,
		capability_id=capability_id,
		intent_class=intent_class,
		existing_values=requested_dimensions,
		dimension_or_metric="dimension",
	)
	metrics = _resolve_requested_labels(
		message=message,
		report_name=report_name,
		capability_id=capability_id,
		intent_class=intent_class,
		existing_values=requested_metrics,
		dimension_or_metric="metric",
	)
	time_scope = str(requested_time_scope or "").strip()
	if not time_scope:
		spec = capability_fresh_query_defaults(capability_id, intent_class=intent_class)
		time_scope = str(spec.get("default_time_scope") or "").strip()
	return dimensions, metrics, time_scope


def _allow_deterministic_family_surface_fallback(intent_class: str) -> bool:
	target_intent = str(intent_class or "").strip()
	if not target_intent:
		return False
	rules = load_semantic_resolution_registry().get("family_resolution_rules")
	if not isinstance(rules, list):
		return False
	signatures: Dict[tuple[str, tuple[tuple[str, str], ...]], int] = {}
	for rule in rules:
		if not isinstance(rule, dict):
			continue
		rule_intent = str(rule.get("intent_class") or "").strip()
		required_slots = rule.get("required_slots") if isinstance(rule.get("required_slots"), dict) else {}
		if not rule_intent or not required_slots:
			continue
		signature = (
			rule_intent,
			tuple(
				sorted(
					(
						str(key or "").strip(),
						str(value or "").strip(),
					)
					for key, value in required_slots.items()
					if str(key or "").strip() and str(value or "").strip()
				)
			),
		)
		if signature[1]:
			signatures[signature] = int(signatures.get(signature, 0) or 0) + 1
	for (rule_intent, _signature), count in signatures.items():
		if rule_intent == target_intent and count > 1:
			return False
	return any(rule_intent == target_intent for rule_intent, _signature in signatures)


def _slot_alias_matches(slot_name: str, message: str) -> List[str]:
	matches: List[tuple[str, str]] = list(semantic_slot_alias_match_details(slot_name, message))
	if str(slot_name or "").strip() == "listing_view":
		for canonical_value, aliases in active_listing_view_aliases().items():
			for alias in aliases:
				if _message_contains_phrase(message, alias):
					matches.append((canonical_value, alias))
					break
	if str(slot_name or "").strip() != "listing_view":
		return list(dict.fromkeys(canonical_value for canonical_value, _alias in matches))
	suppressed: set[str] = set()
	for canonical_value, alias in matches:
		for other_canonical_value, other_alias in matches:
			if canonical_value == other_canonical_value:
				continue
			if len(_normalized_message_phrase(other_alias)) <= len(_normalized_message_phrase(alias)):
				continue
			if _message_contains_phrase(other_alias, alias):
				suppressed.add(canonical_value)
				break
	out: List[str] = []
	for canonical_value, _alias in matches:
		if canonical_value in suppressed:
			continue
		out.append(canonical_value)
	return list(dict.fromkeys(out))


def _financial_statement_family_markers() -> List[str]:
	spec = get_report_family_spec("financial_statement")
	if not isinstance(spec, dict):
		return []
	routing_hints = spec.get("routing_hints") if isinstance(spec.get("routing_hints"), dict) else {}
	intent_markers = _clean_list(routing_hints.get("intent_markers"))
	family_label = str(spec.get("family_label") or "").strip()
	markers = list(intent_markers)
	if family_label:
		markers.append(family_label)
	return list(dict.fromkeys([marker for marker in markers if str(marker or "").strip()]))


def _message_requests_generic_financial_statement(message: str) -> bool:
	if _slot_alias_matches("statement_variant", message):
		return False
	return any(_message_contains_phrase(message, marker) for marker in _financial_statement_family_markers())


def _reconcile_generic_financial_statement_request_from_message(
	*,
	message: str,
	interpretation: FreshQueryInterpretationContract | None,
) -> FreshQueryInterpretationContract | None:
	if interpretation is None:
		return None
	if str(interpretation.intent_class or "").strip() != "financial_statement":
		return interpretation
	if not _message_requests_generic_financial_statement(message):
		return interpretation
	extracted_slots = (
		dict(interpretation.extracted_slots)
		if isinstance(interpretation.extracted_slots, dict)
		else {}
	)
	extracted_slots.pop("statement_variant", None)
	current_reports = list(interpretation.candidate_reports or [])
	current_capabilities = list(interpretation.candidate_capability_ids or [])
	if not current_reports and not extracted_slots.get("statement_variant"):
		return interpretation
	if "financial_statement_read" not in current_capabilities:
		current_capabilities = ["financial_statement_read"] + current_capabilities
	return build_fresh_query_interpretation_contract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class=interpretation.intent_class,
		candidate_capability_ids=list(dict.fromkeys(current_capabilities)),
		candidate_reports=[],
		requested_dimensions=list(interpretation.requested_dimensions),
		requested_metrics=list(interpretation.requested_metrics),
		requested_time_scope=interpretation.requested_time_scope,
		target_limit=interpretation.target_limit,
		requested_presentation=list(interpretation.requested_presentation),
		extracted_slots=extracted_slots,
		ambiguity_flags=list(dict.fromkeys(_clean_list(interpretation.ambiguity_flags) + ["ambiguous_report"])),
		ambiguity_reason="Financial statement requests require an explicit statement view before execution.",
		confidence=float(interpretation.confidence or 0.0),
	)


def _slot_value_matches_message(
	*,
	slot_name: str,
	required_value: str,
	message: str,
	message_concepts: set[str],
) -> bool:
	target = str(required_value or "").strip()
	if not target:
		return False
	matched_aliases = _slot_alias_matches(slot_name, message)
	if target in matched_aliases:
		return True
	if str(slot_name or "").strip() == "listing_view" and matched_aliases:
		return False
	return target in message_concepts


_GENERIC_DETERMINISTIC_SURFACE_SLOTS = {"entity_grain"}


def _deterministic_surface_rule_specificity(rule: Dict[str, Any]) -> tuple[int, int, int]:
	required_slots = rule.get("required_slots") if isinstance(rule.get("required_slots"), dict) else {}
	non_generic_slots = [
		str(slot_name or "").strip()
		for slot_name in required_slots
		if str(slot_name or "").strip()
		and str(slot_name or "").strip() not in _GENERIC_DETERMINISTIC_SURFACE_SLOTS
	]
	candidate_reports = _clean_list(rule.get("candidate_reports"))
	candidate_capability_ids = _clean_list(rule.get("candidate_capability_ids"))
	return (
		len(non_generic_slots),
		len([slot_name for slot_name in required_slots if str(slot_name or "").strip()]),
		len(candidate_reports) + len(candidate_capability_ids),
	)


def _select_deterministic_surface_rule(matched_rules: List[Dict[str, Any]]) -> Dict[str, Any] | None:
	if len(matched_rules) == 1:
		return matched_rules[0]
	if not matched_rules:
		return None
	scored_rules = [
		(_deterministic_surface_rule_specificity(rule), rule)
		for rule in matched_rules
	]
	best_score = max(score for score, _rule in scored_rules)
	best_rules = [rule for score, rule in scored_rules if score == best_score]
	if len(best_rules) != 1:
		return None
	return best_rules[0]


def _reconcile_explicit_transaction_listing_view_from_message(
	*,
	message: str,
	interpretation: FreshQueryInterpretationContract | None,
) -> FreshQueryInterpretationContract | None:
	if interpretation is None:
		return None
	if str(interpretation.intent_class or "").strip() != "transaction_listing":
		return interpretation
	explicit_listing_views = _slot_alias_matches("listing_view", message)
	if len(explicit_listing_views) != 1:
		return interpretation
	explicit_listing_view = str((explicit_listing_views or [""])[0] or "").strip()
	if not explicit_listing_view:
		return interpretation
	extracted_slots = (
		dict(interpretation.extracted_slots)
		if isinstance(interpretation.extracted_slots, dict)
		else {}
	)
	current_listing_view = str(extracted_slots.get("listing_view") or "").strip()
	if current_listing_view == explicit_listing_view:
		return interpretation
	extracted_slots["listing_view"] = explicit_listing_view
	return build_fresh_query_interpretation_contract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class=interpretation.intent_class,
		candidate_capability_ids=list(interpretation.candidate_capability_ids),
		candidate_reports=list(interpretation.candidate_reports),
		requested_dimensions=list(interpretation.requested_dimensions),
		requested_metrics=list(interpretation.requested_metrics),
		requested_time_scope=interpretation.requested_time_scope,
		target_limit=interpretation.target_limit,
		requested_presentation=list(interpretation.requested_presentation),
		extracted_slots=extracted_slots,
		ambiguity_flags=list(interpretation.ambiguity_flags),
		ambiguity_reason=str(interpretation.ambiguity_reason or "").strip(),
		confidence=float(interpretation.confidence or 0.0),
	)



def _reconcile_explicit_time_scope_from_message(
	*,
	message: str,
	interpretation: FreshQueryInterpretationContract | None,
) -> FreshQueryInterpretationContract | None:
	if interpretation is None:
		return None
	explicit_time_scopes = _slot_alias_matches("time_scope", message)
	if len(explicit_time_scopes) != 1:
		return interpretation
	explicit_time_scope = str((explicit_time_scopes or [""])[0] or "").strip()
	if not explicit_time_scope:
		return interpretation
	current_time_scope = str(interpretation.requested_time_scope or "").strip()
	if current_time_scope == explicit_time_scope:
		return interpretation
	if current_time_scope:
		return interpretation
	return build_fresh_query_interpretation_contract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class=interpretation.intent_class,
		candidate_capability_ids=list(interpretation.candidate_capability_ids),
		candidate_reports=list(interpretation.candidate_reports),
		requested_dimensions=list(interpretation.requested_dimensions),
		requested_metrics=list(interpretation.requested_metrics),
		requested_time_scope=explicit_time_scope,
		target_limit=interpretation.target_limit,
		requested_presentation=list(interpretation.requested_presentation),
		extracted_slots=dict(interpretation.extracted_slots) if isinstance(interpretation.extracted_slots, dict) else {},
		ambiguity_flags=list(interpretation.ambiguity_flags),
		ambiguity_reason=str(interpretation.ambiguity_reason or "").strip(),
		confidence=float(interpretation.confidence or 0.0),
	)


def _reconcile_financial_statement_default_time_scope_from_message(
	*,
	message: str,
	interpretation: FreshQueryInterpretationContract | None,
) -> FreshQueryInterpretationContract | None:
	if interpretation is None:
		return None
	if str(interpretation.intent_class or "").strip() != "financial_statement":
		return interpretation
	current_time_scope = str(interpretation.requested_time_scope or "").strip()
	if _slot_alias_matches("time_scope", message) or (
		current_time_scope and _message_explicitly_requests_time_scope(message, current_time_scope)
	) or _infer_followup_requested_time_scope(message=message, requested_time_scope=""):
		return interpretation
	defaults = capability_fresh_query_defaults(
		"financial_statement_read",
		intent_class="financial_statement",
	)
	default_time_scope = str(defaults.get("default_time_scope") or "").strip()
	if not default_time_scope:
		return interpretation
	if current_time_scope == default_time_scope:
		return interpretation
	return build_fresh_query_interpretation_contract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class=interpretation.intent_class,
		candidate_capability_ids=list(interpretation.candidate_capability_ids),
		candidate_reports=list(interpretation.candidate_reports),
		requested_dimensions=list(interpretation.requested_dimensions),
		requested_metrics=list(interpretation.requested_metrics),
		requested_time_scope=default_time_scope,
		target_limit=interpretation.target_limit,
		requested_presentation=list(interpretation.requested_presentation),
		extracted_slots=dict(interpretation.extracted_slots) if isinstance(interpretation.extracted_slots, dict) else {},
		ambiguity_flags=list(interpretation.ambiguity_flags),
		ambiguity_reason=str(interpretation.ambiguity_reason or "").strip(),
		confidence=float(interpretation.confidence or 0.0),
	)


def _apply_governed_time_scope_default(
	*,
	intent_class: str,
	candidate_capability_ids: List[str],
	requested_time_scope: str,
) -> str:
	current = str(requested_time_scope or "").strip()
	if current or not _semantic_resolution_governs_intent(intent_class):
		return current
	capability_id = str((_clean_list(candidate_capability_ids) or [""])[0] or "").strip()
	if not capability_id:
		return ""
	spec = capability_fresh_query_defaults(capability_id, intent_class=intent_class)
	return str(spec.get("default_time_scope") or "").strip()


def _normalized_message_phrase(value: Any) -> str:
	return " ".join(str(value or "").strip().lower().split())


def _message_contains_phrase(value: str, phrase: str) -> bool:
	text = _normalized_message_phrase(value)
	target = _normalized_message_phrase(phrase)
	if not text or not target:
		return False
	pattern = r"(^|[^a-z0-9])" + re.escape(target) + r"([^a-z0-9]|$)"
	return bool(re.search(pattern, text))


def _direct_query_filterable_fields(report_name: str) -> List[str]:
	report_spec = get_report_spec(report_name)
	query_spec = report_spec.get("direct_query") if isinstance(report_spec.get("direct_query"), dict) else {}
	fields = {
		str(value or "").strip()
		for value in (query_spec.get("fields") or [])
		if str(value or "").strip()
	}
	filterable_fields = [
		str(value or "").strip()
		for value in (query_spec.get("filterable_fields") or [])
		if str(value or "").strip()
	]
	return [field for field in filterable_fields if field in fields]


def _direct_query_distinct_scalar_values(
	*,
	report_name: str,
	field_name: str,
) -> List[str]:
	if frappe is None:
		return []
	report_spec = get_report_spec(report_name)
	query_spec = report_spec.get("direct_query") if isinstance(report_spec.get("direct_query"), dict) else {}
	doctype = str(query_spec.get("doctype") or "").strip()
	if not doctype or not str(field_name or "").strip():
		return []
	fixed_filters = query_spec.get("fixed_filters") if isinstance(query_spec.get("fixed_filters"), dict) else {}
	try:
		rows = frappe.get_all(
			doctype,
			fields=[str(field_name or "").strip()],
			filters={str(key): value for key, value in fixed_filters.items() if str(key or "").strip()},
			order_by="modified desc",
			limit_page_length=200,
		)
	except Exception:
		return []
	out: List[str] = []
	for row in rows or []:
		if not isinstance(row, dict):
			continue
		value = str(row.get(field_name) or "").strip()
		if value and value not in out:
			out.append(value)
	return out


def _match_message_to_direct_query_value(
	*,
	message: str,
	candidate_values: List[str],
) -> str:
	scored: List[tuple[int, str]] = []
	for value in _clean_list(candidate_values):
		if _message_contains_phrase(message, value):
			scored.append((len(_normalized_message_phrase(value)), value))
	if not scored:
		return ""
	scored.sort(key=lambda item: (-int(item[0] or 0), str(item[1] or "")))
	return str(scored[0][1] or "").strip()


def _match_message_to_governed_filter_value(
	*,
	message: str,
	value_specs: List[Dict[str, Any]],
) -> str:
	scored: List[tuple[int, str]] = []
	for spec in value_specs:
		if not isinstance(spec, dict):
			continue
		value = str(spec.get("value") or "").strip()
		if not value:
			continue
		phrases = [value]
		phrases.extend(
			str(alias or "").strip()
			for alias in (spec.get("aliases") or [])
			if str(alias or "").strip()
		)
		best_len = 0
		for phrase in phrases:
			if _message_contains_phrase(message, phrase):
				best_len = max(best_len, len(_normalized_message_phrase(phrase)))
		if best_len > 0:
			scored.append((best_len, value))
	if not scored:
		return ""
	scored.sort(key=lambda item: (-int(item[0] or 0), str(item[1] or "")))
	best_len = int(scored[0][0] or 0)
	best_values = list(
		dict.fromkeys(
			str(value or "").strip()
			for length, value in scored
			if int(length or 0) == best_len and str(value or "").strip()
		)
	)
	if len(best_values) != 1:
		return ""
	return best_values[0]


def _augment_direct_query_scalar_filters_from_message(
	*,
	message: str,
	interpretation: FreshQueryInterpretationContract,
) -> FreshQueryInterpretationContract:
	report_name = str((_clean_list(interpretation.candidate_reports) or [""])[0] or "").strip()
	capability_id = str((_clean_list(interpretation.candidate_capability_ids) or [""])[0] or "").strip()
	if not report_name or not capability_id or not str(message or "").strip():
		return interpretation
	filterable_fields = _direct_query_filterable_fields(report_name)
	if not filterable_fields:
		return interpretation
	extracted_slots = (
		dict(interpretation.extracted_slots)
		if isinstance(interpretation.extracted_slots, dict)
		else {}
	)
	existing_filters = (
		dict(extracted_slots.get("filters"))
		if isinstance(extracted_slots.get("filters"), dict)
		else {}
	)
	dimension_keys = detect_canonical_keys(
		message,
		capability_id=capability_id,
		dimension_or_metric="dimension",
	)
	updated_filters = dict(existing_filters)
	for canonical_key in dimension_keys:
		mapped_fields = [
			str(field_name or "").strip()
			for field_name in get_erp_field_mapping(canonical_key, report_name)
			if str(field_name or "").strip()
		]
		for field_name in mapped_fields:
			if field_name not in filterable_fields or updated_filters.get(field_name):
				continue
			candidate_values = _direct_query_distinct_scalar_values(
				report_name=report_name,
				field_name=field_name,
			)
			matched_value = _match_message_to_direct_query_value(
				message=message,
				candidate_values=candidate_values,
			)
			if matched_value:
				updated_filters[field_name] = matched_value
	for field_name in filterable_fields:
		if updated_filters.get(field_name):
			continue
		governed_value_specs = report_direct_query_filter_value_aliases(report_name, field_name)
		if not governed_value_specs:
			continue
		matched_value = _match_message_to_governed_filter_value(
			message=message,
			value_specs=governed_value_specs,
		)
		if matched_value:
			updated_filters[field_name] = matched_value
	if updated_filters == existing_filters:
		return interpretation
	extracted_slots["filters"] = updated_filters
	return build_fresh_query_interpretation_contract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class=interpretation.intent_class,
		candidate_capability_ids=list(interpretation.candidate_capability_ids),
		candidate_reports=list(interpretation.candidate_reports),
		requested_dimensions=list(interpretation.requested_dimensions),
		requested_metrics=list(interpretation.requested_metrics),
		requested_time_scope=interpretation.requested_time_scope,
		target_limit=interpretation.target_limit,
		requested_presentation=list(interpretation.requested_presentation),
		extracted_slots=extracted_slots,
		ambiguity_flags=list(interpretation.ambiguity_flags),
		ambiguity_reason=str(interpretation.ambiguity_reason or "").strip(),
		confidence=float(interpretation.confidence or 0.0),
	)


def _frontdoor_master_data_assessment_payload(front_door_contract: Dict[str, Any] | None) -> Dict[str, Any]:
	payload = front_door_contract if isinstance(front_door_contract, dict) else {}
	response_payload = (
		payload.get("response_payload")
		if isinstance(payload.get("response_payload"), dict)
		else {}
	)
	assessment = (
		response_payload.get("master_data_frontdoor_assessment")
		if isinstance(response_payload.get("master_data_frontdoor_assessment"), dict)
		else {}
	)
	return dict(assessment) if assessment else {}


def _apply_master_data_frontdoor_assessment_to_interpretation(
	*,
	request_id: str,
	session_id: str,
	interpretation: FreshQueryInterpretationContract | None,
	assessment_payload: Dict[str, Any] | None,
) -> FreshQueryInterpretationContract | None:
	assessment = assessment_payload if isinstance(assessment_payload, dict) else {}
	if str(assessment.get("status") or "").strip() != "resolved":
		return interpretation
	scope_id = str(assessment.get("scope_id") or "").strip()
	entity_grain = str(assessment.get("entity_grain") or "").strip()
	request_mode = str(assessment.get("request_mode") or "").strip()
	if not entity_grain or not request_mode:
		return interpretation
	projection = str(assessment.get("lookup_projection") or "").strip()
	search_text = str(assessment.get("lookup_search_text") or "").strip()
	capability_id = str(assessment.get("capability_id") or "").strip()
	report_name = str(assessment.get("report_name") or "").strip()
	allowed_lookup_modes = [
		str(value or "").strip()
		for value in (assessment.get("allowed_lookup_modes") or [])
		if str(value or "").strip()
	]
	internal_details = assessment.get("internal_details") if isinstance(assessment.get("internal_details"), dict) else {}
	lookup_limit = int(max(0, internal_details.get("lookup_limit") or 0))
	if scope_id and not str(internal_details.get("scope_id") or "").strip():
		internal_details = {**internal_details, "scope_id": scope_id}
	if capability_id and not str(internal_details.get("capability_id") or "").strip():
		internal_details = {**internal_details, "capability_id": capability_id}
	if report_name and not str(internal_details.get("report_name") or "").strip():
		internal_details = {**internal_details, "report_name": report_name}
	if allowed_lookup_modes and not internal_details.get("allowed_lookup_modes"):
		internal_details = {**internal_details, "allowed_lookup_modes": list(allowed_lookup_modes)}

	base_slots: Dict[str, Any] = {}
	if interpretation is not None and isinstance(interpretation.extracted_slots, dict):
		base_slots = dict(interpretation.extracted_slots)
	if scope_id:
		base_slots["scope_id"] = scope_id
	base_slots["entity_grain"] = entity_grain
	base_slots["lookup_mode"] = request_mode
	if projection:
		base_slots["lookup_projection"] = projection
	if search_text:
		base_slots["lookup_search_text"] = search_text
	if lookup_limit > 0 and not int(max(0, base_slots.get("lookup_limit") or 0)):
		base_slots["lookup_limit"] = lookup_limit

	requested_dimensions = []
	if interpretation is not None:
		requested_dimensions = list(interpretation.requested_dimensions)
	if not requested_dimensions:
		dimension_label = entity_grain_display_label(entity_grain, plural=False).title()
		requested_dimensions = [dimension_label or entity_grain.title()]

	if interpretation is None or str(interpretation.intent_class or "").strip() != "master_data_lookup":
		return build_fresh_query_interpretation_contract(
			request_id=request_id,
			session_id=session_id,
			intent_class="master_data_lookup",
			candidate_capability_ids=[capability_id] if capability_id else [],
			candidate_reports=[report_name] if report_name else [],
			requested_dimensions=requested_dimensions,
			requested_metrics=[],
			requested_time_scope="",
			target_limit=lookup_limit,
			requested_presentation=[],
			extracted_slots=base_slots,
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.95,
		)

	return build_fresh_query_interpretation_contract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class=interpretation.intent_class,
		candidate_capability_ids=list(
			dict.fromkeys([capability_id] + list(interpretation.candidate_capability_ids))
		)
		if capability_id
		else list(interpretation.candidate_capability_ids),
		candidate_reports=list(
			dict.fromkeys([report_name] + list(interpretation.candidate_reports))
		)
		if report_name
		else list(interpretation.candidate_reports),
		requested_dimensions=requested_dimensions,
		requested_metrics=list(interpretation.requested_metrics),
		requested_time_scope=interpretation.requested_time_scope,
		target_limit=int(max(lookup_limit, interpretation.target_limit or 0)),
		requested_presentation=list(interpretation.requested_presentation),
		extracted_slots=base_slots,
		ambiguity_flags=list(interpretation.ambiguity_flags),
		ambiguity_reason=str(interpretation.ambiguity_reason or "").strip(),
		confidence=max(float(interpretation.confidence or 0.0), 0.95),
	)


def _augment_master_data_lookup_interpretation_from_message(
	*,
	message: str,
	interpretation: FreshQueryInterpretationContract | None,
) -> FreshQueryInterpretationContract | None:
	if interpretation is None:
		return None
	if str(interpretation.intent_class or "").strip() != "master_data_lookup":
		return interpretation
	extracted_slots = (
		dict(interpretation.extracted_slots)
		if isinstance(interpretation.extracted_slots, dict)
		else {}
	)
	updated_slots = dict(extracted_slots)
	entity_grain = str(extracted_slots.get("entity_grain") or "").strip()
	if not entity_grain:
		inferred_entity_grains = [
			str(value or "").strip()
			for value in infer_entity_grains_from_message(message)
			if str(value or "").strip()
		]
		if len(inferred_entity_grains) == 1:
			entity_grain = inferred_entity_grains[0]
			updated_slots["entity_grain"] = entity_grain
	if not entity_grain:
		return interpretation
	policy = get_entity_reference_policy_spec(entity_grain)
	if not policy or str(policy.get("activation_state") or "").strip() != "active":
		if updated_slots == extracted_slots:
			return interpretation
		return build_fresh_query_interpretation_contract(
			request_id=interpretation.request_id,
			session_id=interpretation.session_id,
			intent_class=interpretation.intent_class,
			candidate_capability_ids=list(interpretation.candidate_capability_ids),
			candidate_reports=list(interpretation.candidate_reports),
			requested_dimensions=list(interpretation.requested_dimensions),
			requested_metrics=list(interpretation.requested_metrics),
			requested_time_scope=interpretation.requested_time_scope,
			target_limit=interpretation.target_limit,
			requested_presentation=list(interpretation.requested_presentation),
			extracted_slots=updated_slots,
			ambiguity_flags=list(interpretation.ambiguity_flags),
			ambiguity_reason=str(interpretation.ambiguity_reason or "").strip(),
			confidence=float(interpretation.confidence or 0.0),
		)
	normalized_slots = normalize_master_data_lookup_slots(
		message=message,
		entity_grain=entity_grain,
		preferred_slots=updated_slots,
	)
	for key, value in normalized_slots.items():
		if key == "lookup_limit":
			if not updated_slots.get(key):
				updated_slots[key] = int(max(0, value or 0))
			continue
		if not str(updated_slots.get(key) or "").strip() and str(value or "").strip():
			updated_slots[key] = value
	lookup_mode = str(updated_slots.get("lookup_mode") or "").strip()
	if lookup_mode and not master_data_lookup_mode_allowed(entity_grain, lookup_mode):
		if updated_slots == extracted_slots:
			return interpretation
		return build_fresh_query_interpretation_contract(
			request_id=interpretation.request_id,
			session_id=interpretation.session_id,
			intent_class=interpretation.intent_class,
			candidate_capability_ids=list(interpretation.candidate_capability_ids),
			candidate_reports=list(interpretation.candidate_reports),
			requested_dimensions=list(interpretation.requested_dimensions),
			requested_metrics=list(interpretation.requested_metrics),
			requested_time_scope=interpretation.requested_time_scope,
			target_limit=interpretation.target_limit,
			requested_presentation=list(interpretation.requested_presentation),
			extracted_slots=updated_slots,
			ambiguity_flags=list(interpretation.ambiguity_flags),
			ambiguity_reason=str(interpretation.ambiguity_reason or "").strip(),
			confidence=float(interpretation.confidence or 0.0),
		)
	if lookup_mode in {"candidate_resolution", "profile_target"}:
		existing_filters = (
			dict(updated_slots.get("filters"))
			if isinstance(updated_slots.get("filters"), dict)
			else {}
		)
		filter_field = str(policy.get("filter_field") or "").strip()
		if filter_field and not str(existing_filters.get(filter_field) or "").strip():
			resolution_payload = resolve_entity_reference_from_message(
				request_id=interpretation.request_id,
				entity_grain=entity_grain,
				message=message,
				lookup_mode=lookup_mode,
				search_text=str(updated_slots.get("lookup_search_text") or "").strip(),
			)
			if isinstance(resolution_payload, dict) and resolution_payload:
				updated_slots["entity_reference_resolution"] = resolution_payload
				resolved_entity = (
					resolution_payload.get("resolved_entity")
					if isinstance(resolution_payload.get("resolved_entity"), dict)
					else {}
				)
				resolved_entity_key = str(resolved_entity.get("entity_key") or "").strip()
				if str(resolution_payload.get("resolution_status") or "").strip() == "resolved" and resolved_entity_key:
					updated_filters = dict(existing_filters)
					updated_filters[filter_field] = resolved_entity_key
					updated_slots["filters"] = updated_filters
	if updated_slots == extracted_slots:
		return interpretation
	return build_fresh_query_interpretation_contract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class=interpretation.intent_class,
		candidate_capability_ids=list(interpretation.candidate_capability_ids),
		candidate_reports=list(interpretation.candidate_reports),
		requested_dimensions=list(interpretation.requested_dimensions),
		requested_metrics=list(interpretation.requested_metrics),
		requested_time_scope=interpretation.requested_time_scope,
		target_limit=interpretation.target_limit,
		requested_presentation=list(interpretation.requested_presentation),
		extracted_slots=updated_slots,
		ambiguity_flags=list(interpretation.ambiguity_flags),
		ambiguity_reason=str(interpretation.ambiguity_reason or "").strip(),
		confidence=float(interpretation.confidence or 0.0),
	)


def _report_entity_scope_specs(report_name: str) -> List[Dict[str, Any]]:
	spec = get_report_spec(report_name)
	values = spec.get("entity_scope_support")
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def _report_entity_scope_spec_for_grain(report_name: str, entity_grain: str) -> Dict[str, Any]:
	clean_grain = str(entity_grain or "").strip()
	if not clean_grain:
		return {}
	for item in _report_entity_scope_specs(report_name):
		if str(item.get("entity_grain") or "").strip() == clean_grain:
			return item
	return {}


def _report_supports_entity_scope(
	*,
	report_name: str,
	entity_grain: str,
	requested_dimensions: List[str],
) -> bool:
	spec = _report_entity_scope_spec_for_grain(report_name, entity_grain)
	if not spec:
		return False
	supported_dimensions = [
		str(value or "").strip()
		for value in (spec.get("supported_dimensions") or [])
		if str(value or "").strip()
	]
	if not supported_dimensions:
		return True
	requested = _clean_list(requested_dimensions)
	if not requested:
		return True
	supported_keys = {_normalize_key(value) for value in supported_dimensions}
	return all(_normalize_key(value) in supported_keys for value in requested)


def _single_entity_grain_for_message(
	*,
	message: str,
	extracted_slots: Dict[str, Any],
) -> str:
	slot_grain = str(extracted_slots.get("entity_grain") or "").strip()
	if slot_grain:
		return slot_grain
	inferred = [
		str(value or "").strip()
		for value in infer_entity_grains_from_message(message)
		if str(value or "").strip()
	]
	if len(inferred) == 1:
		return inferred[0]
	return ""


def _resolve_entity_scoped_report_candidate(
	*,
	capability_id: str,
	intent_class: str,
	current_report: str,
	entity_grain: str,
	requested_dimensions: List[str],
) -> str:
	candidates = []
	if current_report:
		candidates.append(current_report)
	for report_name in _intent_supported_reports_for_capability(
		capability_id=capability_id,
		intent_class=intent_class,
	):
		if report_name not in candidates:
			candidates.append(report_name)
	for report_name in candidates:
		if _report_supports_entity_scope(
			report_name=report_name,
			entity_grain=entity_grain,
			requested_dimensions=requested_dimensions,
		):
			return report_name
	return current_report


def _augment_entity_scoped_report_interpretation_from_message(
	*,
	message: str,
	interpretation: FreshQueryInterpretationContract | None,
) -> FreshQueryInterpretationContract | None:
	if interpretation is None:
		return None
	if not str(message or "").strip():
		return interpretation
	if str(interpretation.intent_class or "").strip() == "master_data_lookup":
		return interpretation
	capability_id = str((_clean_list(interpretation.candidate_capability_ids) or [""])[0] or "").strip()
	current_report = str((_clean_list(interpretation.candidate_reports) or [""])[0] or "").strip()
	if not capability_id:
		return interpretation
	extracted_slots = (
		dict(interpretation.extracted_slots)
		if isinstance(interpretation.extracted_slots, dict)
		else {}
	)
	entity_grain = _single_entity_grain_for_message(
		message=message,
		extracted_slots=extracted_slots,
	)
	if not entity_grain:
		return interpretation
	target_report = _resolve_entity_scoped_report_candidate(
		capability_id=capability_id,
		intent_class=str(interpretation.intent_class or "").strip(),
		current_report=current_report,
		entity_grain=entity_grain,
		requested_dimensions=list(interpretation.requested_dimensions),
	)
	scope_spec = _report_entity_scope_spec_for_grain(target_report, entity_grain)
	filter_field = str(scope_spec.get("filter_field") or "").strip()
	if not filter_field:
		return interpretation
	existing_filters = (
		dict(extracted_slots.get("filters"))
		if isinstance(extracted_slots.get("filters"), dict)
		else {}
	)
	resolution_payload = (
		dict(extracted_slots.get("entity_reference_resolution"))
		if isinstance(extracted_slots.get("entity_reference_resolution"), dict)
		else {}
	)
	resolved_entity = (
		dict(resolution_payload.get("resolved_entity"))
		if isinstance(resolution_payload.get("resolved_entity"), dict)
		else {}
	)
	resolution_status = str(resolution_payload.get("resolution_status") or "").strip()
	if resolution_status != "resolved" or not str(resolved_entity.get("entity_key") or "").strip():
		resolution_payload = resolve_entity_reference_from_message(
			request_id=interpretation.request_id,
			entity_grain=entity_grain,
			message=message,
			lookup_mode="profile_target",
			search_text="",
		)
		if not isinstance(resolution_payload, dict) or not resolution_payload:
			return interpretation
		resolved_entity = (
			dict(resolution_payload.get("resolved_entity"))
			if isinstance(resolution_payload.get("resolved_entity"), dict)
			else {}
		)
		resolution_status = str(resolution_payload.get("resolution_status") or "").strip()
		if resolution_status != "resolved":
			return interpretation
	resolved_entity_key = str(resolved_entity.get("entity_key") or "").strip()
	if not resolved_entity_key:
		return interpretation
	updated_slots = dict(extracted_slots)
	updated_slots["entity_grain"] = entity_grain
	updated_slots["entity_reference_resolution"] = resolution_payload
	updated_filters = dict(existing_filters)
	updated_filters[filter_field] = resolved_entity_key
	updated_slots["filters"] = updated_filters
	candidate_reports = list(_clean_list(interpretation.candidate_reports))
	if target_report:
		candidate_reports = [target_report]
	if (
		candidate_reports == list(_clean_list(interpretation.candidate_reports))
		and updated_slots == extracted_slots
	):
		return interpretation
	return build_fresh_query_interpretation_contract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class=interpretation.intent_class,
		candidate_capability_ids=list(interpretation.candidate_capability_ids),
		candidate_reports=candidate_reports,
		requested_dimensions=list(interpretation.requested_dimensions),
		requested_metrics=list(interpretation.requested_metrics),
		requested_time_scope=interpretation.requested_time_scope,
		target_limit=interpretation.target_limit,
		requested_presentation=list(interpretation.requested_presentation),
		extracted_slots=updated_slots,
		ambiguity_flags=list(interpretation.ambiguity_flags),
		ambiguity_reason=str(interpretation.ambiguity_reason or "").strip(),
		confidence=float(interpretation.confidence or 0.0),
	)


def _preferred_family_id_for_message(
	*,
	message: str,
	compiler_contract: Dict[str, Any],
	interpretation_contract: Dict[str, Any] | None = None,
) -> str:
	report_name = str(compiler_contract.get("selected_report") or "").strip()
	capability_id = str(compiler_contract.get("capability_id") or "").strip()
	intent_class = str((interpretation_contract or {}).get("intent_class") or "").strip()
	report_family_ids = report_business_family_ids(report_name)
	if not report_family_ids:
		return ""
	intent_family_ids = set(report_family_ids_for_intent_class(intent_class))
	if intent_family_ids:
		matching = [family_id for family_id in report_family_ids if family_id in intent_family_ids]
		if len(matching) == 1:
			return matching[0]
		if capability_id:
			capability_families = set(report_business_family_ids(report_name))
			for family_id in report_family_ids:
				if family_id in capability_families:
					return family_id
		if intent_class == "trend_analysis":
			for family_id in matching:
				if family_id == "trend_analytics":
					return family_id
		if intent_class == "ranked_entities":
			for family_id in matching:
				if family_id == "ranking_analytics":
					return family_id
		if intent_class == "product_performance":
			for family_id in matching:
				if family_id == "product_profitability":
					return family_id
		if matching:
			return matching[0]
	return report_family_ids[0]


def _validate_semantic_payload(
	*,
	request_id: str,
	session_id: str,
	payload: Dict[str, Any],
	context: Dict[str, Any],
	message: str = "",
) -> FreshQueryInterpretationContract | None:
	if not isinstance(payload, dict):
		return None

	intent_lookup = _normalized_lookup(
		[
			str(item.get("intent_class_id") or "").strip()
			for item in (context.get("intent_classes") or [])
			if isinstance(item, dict)
		]
	)
	raw_intent_class = str(payload.get("intent_class") or "").strip()
	intent_class = intent_lookup.get(_normalize_key(raw_intent_class), "")

	capabilities = [
		dict(item)
		for item in (context.get("capabilities") or [])
		if isinstance(item, dict)
	]
	capability_lookup = _normalized_lookup(
		[str(item.get("capability_id") or "").strip() for item in capabilities]
	)
	candidate_capability_ids: List[str] = []
	for value in _clean_list(payload.get("candidate_capability_ids")):
		canonical = capability_lookup.get(_normalize_key(value), "")
		if not canonical:
			return None
		candidate_capability_ids.append(canonical)
	candidate_capability_ids = list(dict.fromkeys(candidate_capability_ids))

	for capability_id in candidate_capability_ids:
		spec = next(
			(
				item
				for item in capabilities
				if str(item.get("capability_id") or "").strip() == capability_id
			),
			{},
		)
		if intent_class and intent_class not in _clean_list(spec.get("intent_classes")):
			return None

	scoped_capabilities = _capability_scope(intent_class, candidate_capability_ids, context)
	report_lookup = _normalized_lookup(
		[
			report_name
			for capability in scoped_capabilities
			for report_name in _clean_list(capability.get("report_names"))
		]
	)
	if not report_lookup:
		report_lookup = _normalized_lookup(
			[
				report_name
				for capability in capabilities
				for report_name in _clean_list(capability.get("report_names"))
			]
		)
	candidate_reports: List[str] = []
	for value in _clean_list(payload.get("candidate_reports"))[:3]:
		canonical = report_lookup.get(_normalize_key(value), "")
		if not canonical:
			return None
		candidate_reports.append(canonical)
	candidate_reports = list(dict.fromkeys(candidate_reports))

	raw_requested_dimensions = list(dict.fromkeys(_clean_list(payload.get("requested_dimensions"))))
	raw_requested_metrics = list(dict.fromkeys(_clean_list(payload.get("requested_metrics"))))

	scoped_capabilities = _capability_scope(intent_class, candidate_capability_ids, context)
	dimension_lookup = _normalized_lookup(
		[
			dimension
			for capability in scoped_capabilities
			for dimension in _clean_list(capability.get("dimensions"))
		]
		+ [
			dimension
			for report_name in candidate_reports
			for dimension in _clean_list(report_supported_dimensions(report_name))
		]
	)
	metric_lookup = _normalized_lookup(
		[
			metric
			for capability in scoped_capabilities
			for metric in _clean_list(capability.get("metrics"))
		]
		+ [
			metric
			for report_name in candidate_reports
			for metric in _clean_list(report_supported_metrics(report_name))
		]
	)
	requested_dimensions: List[str] = []
	for value in raw_requested_dimensions:
		canonical = dimension_lookup.get(_normalize_key(value), "")
		if not canonical:
			return None
		requested_dimensions.append(canonical)
	requested_dimensions = list(dict.fromkeys(requested_dimensions))

	requested_metrics: List[str] = []
	for value in raw_requested_metrics:
		canonical = metric_lookup.get(_normalize_key(value), "")
		if not canonical:
			return None
		requested_metrics.append(canonical)
	requested_metrics = list(dict.fromkeys(requested_metrics))

	presentation_lookup = _normalized_lookup(sorted(_ALLOWED_PRESENTATION_MODES))
	requested_presentation: List[str] = []
	for value in _clean_list(payload.get("requested_presentation")):
		canonical = presentation_lookup.get(_normalize_key(value), "")
		if not canonical:
			return None
		requested_presentation.append(canonical)
	requested_presentation = list(dict.fromkeys(requested_presentation))

	ambiguity_lookup = _normalized_lookup(sorted(_ALLOWED_AMBIGUITY_FLAGS))
	ambiguity_flags: List[str] = []
	for value in _clean_list(payload.get("ambiguity_flags")):
		canonical = ambiguity_lookup.get(_normalize_key(value), "")
		if not canonical:
			return None
		ambiguity_flags.append(canonical)
	ambiguity_flags = list(dict.fromkeys(ambiguity_flags))

	extracted_slots = payload.get("extracted_slots")
	if not isinstance(extracted_slots, dict):
		extracted_slots = {}
	clean_slots = _sanitize_extracted_slots(extracted_slots)

	try:
		confidence = float(payload.get("confidence") or 0.0)
	except Exception:
		confidence = 0.0
	confidence = max(0.0, min(1.0, confidence))
	try:
		target_limit = int(payload.get("target_limit") or 0)
	except Exception:
		target_limit = 0
	target_limit = max(0, min(50, target_limit))
	requested_time_scope = _normalize_time_scope(payload.get("requested_time_scope"))
	requested_time_scope = _apply_governed_time_scope_default(
		intent_class=intent_class,
		candidate_capability_ids=candidate_capability_ids,
		requested_time_scope=requested_time_scope,
	)
	ambiguity_reason = str(payload.get("ambiguity_reason") or "").strip()

	if not any(
		[
			intent_class,
			candidate_capability_ids,
			candidate_reports,
			requested_dimensions,
			requested_metrics,
			requested_time_scope,
			requested_presentation,
			ambiguity_flags,
			ambiguity_reason,
		]
	):
		return None

	candidate_capability_ids, candidate_reports = _apply_governed_interpretation_biases(
		intent_class=intent_class,
		message=message,
		candidate_capability_ids=candidate_capability_ids,
		candidate_reports=candidate_reports,
		requested_dimensions=requested_dimensions,
		requested_metrics=requested_metrics,
	)
	if len(candidate_reports) > 1 and "ambiguous_report" not in ambiguity_flags:
		ambiguity_flags.append("ambiguous_report")
		if not ambiguity_reason:
			ambiguity_reason = "The request matches multiple governed reports and needs clarification before execution."
	requested_dimensions, requested_metrics, requested_time_scope = _apply_governed_request_defaults(
		intent_class=intent_class,
		message=message,
		candidate_capability_ids=candidate_capability_ids,
		candidate_reports=candidate_reports,
		requested_dimensions=requested_dimensions,
		requested_metrics=requested_metrics,
		requested_time_scope=requested_time_scope,
	)

	contract = build_fresh_query_interpretation_contract(
		request_id=request_id,
		session_id=session_id,
		intent_class=intent_class,
		candidate_capability_ids=candidate_capability_ids,
		candidate_reports=candidate_reports,
		requested_dimensions=requested_dimensions,
		requested_metrics=requested_metrics,
		requested_time_scope=requested_time_scope,
		target_limit=target_limit,
		requested_presentation=requested_presentation,
		extracted_slots=clean_slots,
		ambiguity_flags=ambiguity_flags,
		ambiguity_reason=ambiguity_reason,
		confidence=confidence,
	)
	return contract


def interpret_fresh_query_semantically(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	recent_messages: List[Dict[str, str]],
	model_override: str = "",
) -> SemanticFreshQueryResult:
	threshold = _confidence_threshold()
	context = _build_interpretation_context()
	try:
		data = call_qwen_runtime_fresh_query_interpretation(
			request_id=request_id,
			session_id=session_id,
			user_id=user_id,
			site_name=site_name,
			message=message,
			recent_messages=recent_messages,
			interpretation_context=context,
			model_override=model_override,
		)
	except QwenRuntimeClientError as exc:
		return SemanticFreshQueryResult(
			status="runtime_error",
			confidence_threshold=threshold,
			runtime_error=str(exc),
		)

	agent_meta = data.get("agent_meta") if isinstance(data.get("agent_meta"), dict) else {}
	if data.get("ok") is False:
		return SemanticFreshQueryResult(
			status="runtime_error",
			confidence_threshold=threshold,
			runtime_error=str(data.get("error") or "Runtime fresh-query interpreter returned an error.").strip(),
			agent_meta=agent_meta,
		)
	interpretation = data.get("interpretation")
	if not isinstance(interpretation, dict):
		return SemanticFreshQueryResult(
			status="invalid_response",
			confidence_threshold=threshold,
			validation_error="Runtime fresh-query interpreter returned no valid interpretation object.",
			agent_meta=agent_meta,
		)

	contract = _validate_semantic_payload(
		request_id=request_id,
		session_id=session_id,
		payload=interpretation,
		context=context,
		message=message,
	)
	if contract is None:
		return SemanticFreshQueryResult(
			status="invalid_response",
			confidence_threshold=threshold,
			validation_error="Runtime fresh-query interpretation did not pass governed validation.",
			agent_meta=agent_meta,
		)

	if contract.confidence < threshold:
		return SemanticFreshQueryResult(
			status="low_confidence",
			interpretation=contract,
			confidence_threshold=threshold,
			validation_error="Semantic fresh-query interpretation fell below the governed confidence threshold.",
			agent_meta=agent_meta,
		)

	return SemanticFreshQueryResult(
		status="accepted",
		interpretation=contract,
		confidence_threshold=threshold,
		agent_meta=agent_meta,
	)


def _merge_fallback_agent_meta(
	primary: Dict[str, Any],
	fallback: Dict[str, Any],
	primary_status: str,
) -> Dict[str, Any]:
	merged = dict(fallback or {})
	telemetry = merged.get("telemetry") if isinstance(merged.get("telemetry"), dict) else {}
	merged["telemetry"] = {
		**telemetry,
		"fallback_attempted": True,
		"fallback_used": True,
		"primary_status": str(primary_status or "").strip(),
		"primary_model": str((primary or {}).get("model") or "").strip(),
		"primary_latency_ms": int(
			max(
				0,
				(
					((primary or {}).get("telemetry") or {}).get("latency_ms")
					if isinstance((primary or {}).get("telemetry"), dict)
					else 0
				)
				or 0,
			)
		),
	}
	return merged


def _should_retry_with_runtime_default(result: SemanticFreshQueryResult, model_override: str) -> bool:
	if str(model_override or "").strip() == _RUNTIME_DEFAULT_MODEL_OVERRIDE:
		return False
	return str(result.status or "").strip() in {"runtime_error", "invalid_response", "low_confidence"}


def _deterministic_family_surface_interpretation(
	*,
	request_id: str,
	session_id: str,
	message: str,
	confidence_threshold: float,
) -> FreshQueryInterpretationContract | None:
	if _message_requests_generic_financial_statement(message):
		defaults = capability_fresh_query_defaults(
			"financial_statement_read",
			intent_class="financial_statement",
		)
		return build_fresh_query_interpretation_contract(
			request_id=request_id,
			session_id=session_id,
			intent_class="financial_statement",
			candidate_capability_ids=["financial_statement_read"],
			candidate_reports=[],
			requested_dimensions=_clean_list(defaults.get("default_dimensions")),
			requested_metrics=_clean_list(defaults.get("default_metrics")),
			requested_time_scope=str(defaults.get("default_time_scope") or "").strip(),
			target_limit=0,
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=["ambiguous_report"],
			ambiguity_reason="Financial statement requests require an explicit statement view before execution.",
			confidence=max(float(confidence_threshold or 0.0), 0.9),
		)
	registry = load_semantic_resolution_registry()
	rules = registry.get("family_resolution_rules")
	if not isinstance(rules, list):
		return None
	message_concepts = {
		str(value or "").strip()
		for value in ontology_detect_concepts(message)
		if str(value or "").strip()
	}
	matched_rules: List[Dict[str, Any]] = []
	for rule in rules:
		if not isinstance(rule, dict):
			continue
		intent_class = str(rule.get("intent_class") or "").strip()
		required_slots = rule.get("required_slots") if isinstance(rule.get("required_slots"), dict) else {}
		if not intent_class or not required_slots:
			continue
		if not _allow_deterministic_family_surface_fallback(intent_class):
			continue
		if not all(
			_slot_value_matches_message(
				slot_name=str(slot_name or "").strip(),
				required_value=str(slot_value or "").strip(),
				message=message,
				message_concepts=message_concepts,
			)
			for slot_name, slot_value in required_slots.items()
			if str(slot_name or "").strip() and str(slot_value or "").strip()
		):
			continue
		matched_rules.append(rule)
	selected_rule = _select_deterministic_surface_rule(matched_rules)
	if selected_rule is None:
		return None
	intent_class = str(selected_rule.get("intent_class") or "").strip()
	candidate_capability_ids = _clean_list(selected_rule.get("candidate_capability_ids"))
	candidate_reports = _clean_list(selected_rule.get("candidate_reports"))
	primary_capability_id = str((candidate_capability_ids or [""])[0] or "").strip()
	defaults = capability_fresh_query_defaults(primary_capability_id, intent_class=intent_class)
	detected_metrics = detect_canonical_keys(
		message,
		capability_id=primary_capability_id or None,
		dimension_or_metric="metric",
	)
	requested_metrics = list(dict.fromkeys(_clean_list(defaults.get("default_metrics")) + detected_metrics))
	contract = build_fresh_query_interpretation_contract(
		request_id=request_id,
		session_id=session_id,
		intent_class=intent_class,
		candidate_capability_ids=candidate_capability_ids,
		candidate_reports=candidate_reports,
		requested_dimensions=_clean_list(defaults.get("default_dimensions")),
		requested_metrics=requested_metrics,
		requested_time_scope=str(defaults.get("default_time_scope") or "").strip(),
		target_limit=0,
		requested_presentation=[],
		extracted_slots={
			str(slot_name or "").strip(): str(slot_value or "").strip()
			for slot_name, slot_value in (
				(selected_rule.get("required_slots") if isinstance(selected_rule.get("required_slots"), dict) else {}).items()
			)
			if str(slot_name or "").strip() and str(slot_value or "").strip()
		},
		ambiguity_flags=[],
		ambiguity_reason="",
		confidence=max(float(confidence_threshold or 0.0), 0.9),
	)
	return _augment_master_data_lookup_interpretation_from_message(
		message=message,
		interpretation=contract,
	)


def _normalize_transaction_listing_requested_metrics_from_message(
	*,
	message: str,
	interpretation: FreshQueryInterpretationContract | None,
) -> FreshQueryInterpretationContract | None:
	if interpretation is None:
		return None
	if str(interpretation.intent_class or "").strip() != "transaction_listing":
		return interpretation
	candidate_capability_ids = list(interpretation.candidate_capability_ids or [])
	candidate_reports = list(interpretation.candidate_reports or [])
	capability_id = str((candidate_capability_ids or [""])[0] or "").strip()
	report_name = str((candidate_reports or [""])[0] or "").strip()
	if not capability_id or not report_name:
		return interpretation
	explicit_supported_metric_labels = [
		label
		for label in _supported_labels_for_report(report_name, dimension_or_metric="metric")
		if _message_contains_phrase(message, label)
	]
	normalized_metrics = (
		list(dict.fromkeys(explicit_supported_metric_labels))
		if explicit_supported_metric_labels
		else _resolve_requested_labels(
			message=message,
			report_name=report_name,
			capability_id=capability_id,
			intent_class="transaction_listing",
			existing_values=[],
			dimension_or_metric="metric",
		)
	)
	if not normalized_metrics:
		return interpretation
	if normalized_metrics == list(interpretation.requested_metrics or []):
		return interpretation
	return build_fresh_query_interpretation_contract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class=interpretation.intent_class,
		candidate_capability_ids=list(interpretation.candidate_capability_ids),
		candidate_reports=list(interpretation.candidate_reports),
		requested_dimensions=list(interpretation.requested_dimensions),
		requested_metrics=normalized_metrics,
		requested_time_scope=interpretation.requested_time_scope,
		target_limit=interpretation.target_limit,
		requested_presentation=list(interpretation.requested_presentation),
		extracted_slots=dict(interpretation.extracted_slots),
		ambiguity_flags=list(interpretation.ambiguity_flags),
		ambiguity_reason=interpretation.ambiguity_reason,
		confidence=interpretation.confidence,
	)


def _augment_semantic_interpretation_with_detected_metrics(
	*,
	semantic_result: SemanticFreshQueryResult,
	message: str,
) -> SemanticFreshQueryResult:
	interpretation = semantic_result.interpretation
	if interpretation is None:
		return semantic_result
	if str(interpretation.intent_class or "").strip() == "trend_analysis":
		return semantic_result
	candidate_capability_ids = list(interpretation.candidate_capability_ids or [])
	primary_capability_id = str(candidate_capability_ids[0] or "").strip() if candidate_capability_ids else ""
	detected_metrics = detect_canonical_keys(
		message,
		capability_id=primary_capability_id or None,
		dimension_or_metric="metric",
	)
	if not detected_metrics:
		return semantic_result
	combined_metrics = list(dict.fromkeys(list(interpretation.requested_metrics) + detected_metrics))
	if combined_metrics == list(interpretation.requested_metrics):
		return semantic_result
	augmented = build_fresh_query_interpretation_contract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class=interpretation.intent_class,
		candidate_capability_ids=list(interpretation.candidate_capability_ids),
		candidate_reports=list(interpretation.candidate_reports),
		requested_dimensions=list(interpretation.requested_dimensions),
		requested_metrics=combined_metrics,
		requested_time_scope=interpretation.requested_time_scope,
		target_limit=interpretation.target_limit,
		requested_presentation=list(interpretation.requested_presentation),
		extracted_slots=dict(interpretation.extracted_slots),
		ambiguity_flags=list(interpretation.ambiguity_flags),
		ambiguity_reason=interpretation.ambiguity_reason,
		confidence=interpretation.confidence,
	)
	return SemanticFreshQueryResult(
		status=semantic_result.status,
		confidence_threshold=semantic_result.confidence_threshold,
		interpretation=augmented,
		runtime_error=semantic_result.runtime_error,
		validation_error=semantic_result.validation_error,
		agent_meta=semantic_result.agent_meta,
	)


def _normalize_trend_requested_metrics_from_message(
	*,
	message: str,
	interpretation: FreshQueryInterpretationContract | None,
) -> FreshQueryInterpretationContract | None:
	if interpretation is None:
		return None
	if str(interpretation.intent_class or "").strip() != "trend_analysis":
		return interpretation
	candidate_capability_ids = list(interpretation.candidate_capability_ids or [])
	candidate_reports = list(interpretation.candidate_reports or [])
	capability_id = str((candidate_capability_ids or [""])[0] or "").strip()
	report_name = str((candidate_reports or [""])[0] or "").strip()
	if not capability_id:
		return interpretation
	detected_metrics = detect_canonical_keys(
		message,
		capability_id=capability_id,
		dimension_or_metric="metric",
	)
	if not detected_metrics:
		return interpretation
	normalized_metrics = _resolve_requested_labels(
		message=message,
		report_name=report_name,
		capability_id=capability_id,
		intent_class="trend_analysis",
		existing_values=[],
		dimension_or_metric="metric",
	)
	if not normalized_metrics or normalized_metrics == list(interpretation.requested_metrics):
		return interpretation
	return build_fresh_query_interpretation_contract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class=interpretation.intent_class,
		candidate_capability_ids=list(interpretation.candidate_capability_ids),
		candidate_reports=list(interpretation.candidate_reports),
		requested_dimensions=list(interpretation.requested_dimensions),
		requested_metrics=normalized_metrics,
		requested_time_scope=interpretation.requested_time_scope,
		target_limit=interpretation.target_limit,
		requested_presentation=list(interpretation.requested_presentation),
		extracted_slots=dict(interpretation.extracted_slots),
		ambiguity_flags=list(interpretation.ambiguity_flags),
		ambiguity_reason=interpretation.ambiguity_reason,
		confidence=interpretation.confidence,
	)


def _compile_pipeline_from_semantic_result(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	clarification_resolution: Dict[str, Any] | None,
	front_door_contract: Dict[str, Any] | None,
	semantic_result: SemanticFreshQueryResult,
	proposal_generation_latency_ms: int,
) -> Dict[str, Any]:
	master_data_frontdoor_assessment = _frontdoor_master_data_assessment_payload(front_door_contract)
	if master_data_frontdoor_assessment:
		semantic_result = SemanticFreshQueryResult(
			status=semantic_result.status,
			interpretation=_apply_master_data_frontdoor_assessment_to_interpretation(
				request_id=request_id,
				session_id=session_id,
				interpretation=semantic_result.interpretation,
				assessment_payload=master_data_frontdoor_assessment,
			),
			confidence_threshold=semantic_result.confidence_threshold,
			runtime_error=semantic_result.runtime_error,
			validation_error=semantic_result.validation_error,
			agent_meta={
				**(semantic_result.agent_meta if isinstance(semantic_result.agent_meta, dict) else {}),
				"master_data_frontdoor_assessment_applied": True,
			},
		)
	if semantic_result.interpretation is not None:
		semantic_result = _augment_semantic_interpretation_with_detected_metrics(
			semantic_result=semantic_result,
			message=message,
		)
		semantic_result = SemanticFreshQueryResult(
			status=semantic_result.status,
			interpretation=_reconcile_financial_statement_default_time_scope_from_message(
				message=message,
				interpretation=_reconcile_generic_financial_statement_request_from_message(
					message=message,
					interpretation=semantic_result.interpretation,
				),
			),
			confidence_threshold=semantic_result.confidence_threshold,
			runtime_error=semantic_result.runtime_error,
			validation_error=semantic_result.validation_error,
			agent_meta=semantic_result.agent_meta,
		)
	interaction_contract = build_interaction_contract(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		raw_message=message,
	)
	response_policy = build_response_policy_contract(
		interaction_contract=interaction_contract,
	)
	reconciled_interpretation = _reconcile_explicit_transaction_listing_view_from_message(
		message=message,
		interpretation=semantic_result.interpretation,
	)
	reconciled_interpretation = _reconcile_explicit_time_scope_from_message(
		message=message,
		interpretation=reconciled_interpretation,
	)
	reconciled_interpretation = _augment_master_data_lookup_interpretation_from_message(
		message=message,
		interpretation=reconciled_interpretation,
	)
	reconciled_interpretation = _augment_entity_scoped_report_interpretation_from_message(
		message=message,
		interpretation=reconciled_interpretation,
	)
	if reconciled_interpretation != semantic_result.interpretation:
		semantic_result = SemanticFreshQueryResult(
			status=semantic_result.status,
			interpretation=reconciled_interpretation,
			confidence_threshold=semantic_result.confidence_threshold,
			runtime_error=semantic_result.runtime_error,
			validation_error=semantic_result.validation_error,
			agent_meta=dict(semantic_result.agent_meta or {}),
		)
	compilation_latency_ms = 0
	out: Dict[str, Any] = {
		"request_id": request_id,
		"interaction_contract": interaction_contract.to_payload(),
		"response_policy_contract": response_policy.to_payload(),
		"fresh_query_interpretation": semantic_result.to_payload(),
	}
	if isinstance(clarification_resolution, dict) and clarification_resolution:
		out["clarification_resolution"] = dict(clarification_resolution)
	if master_data_frontdoor_assessment:
		out["master_data_frontdoor_assessment"] = dict(master_data_frontdoor_assessment)
	if semantic_result.interpretation is None:
		out["phase4_latency_breakdown"] = {
			"proposal_generation_latency_ms": proposal_generation_latency_ms,
			"compilation_latency_ms": 0,
		}
		return out
	interpretation_for_compile = _apply_clarification_resolution_to_interpretation(
		interpretation=semantic_result.interpretation,
		clarification_resolution=clarification_resolution,
	)
	if interpretation_for_compile != semantic_result.interpretation:
		semantic_result = SemanticFreshQueryResult(
			status="clarification_resolution_override",
			interpretation=interpretation_for_compile,
			confidence_threshold=semantic_result.confidence_threshold,
			runtime_error=semantic_result.runtime_error,
			validation_error=semantic_result.validation_error,
			agent_meta={
				**(semantic_result.agent_meta if isinstance(semantic_result.agent_meta, dict) else {}),
				"clarification_resolution_applied": True,
			},
		)
	trend_normalized_interpretation = _normalize_trend_requested_metrics_from_message(
		message=message,
		interpretation=semantic_result.interpretation,
	)
	if trend_normalized_interpretation != semantic_result.interpretation:
		semantic_result = SemanticFreshQueryResult(
			status=semantic_result.status,
			interpretation=trend_normalized_interpretation,
			confidence_threshold=semantic_result.confidence_threshold,
			runtime_error=semantic_result.runtime_error,
			validation_error=semantic_result.validation_error,
			agent_meta={
				**(semantic_result.agent_meta if isinstance(semantic_result.agent_meta, dict) else {}),
				"trend_metric_reconciled_from_message": True,
			},
		)
	semantic_resolution = resolve_interpretation_semantically(semantic_result.interpretation)
	if semantic_resolution is not None:
		out["semantic_resolution_contract"] = semantic_resolution.contract.to_payload()
		semantic_result = SemanticFreshQueryResult(
			status="semantic_resolution_applied",
			interpretation=semantic_resolution.interpretation,
			confidence_threshold=semantic_result.confidence_threshold,
			runtime_error=semantic_result.runtime_error,
			validation_error=semantic_result.validation_error,
			agent_meta={
				**(semantic_result.agent_meta if isinstance(semantic_result.agent_meta, dict) else {}),
				"semantic_resolution_applied": True,
			},
		)
		semantic_result = _augment_semantic_interpretation_with_detected_metrics(
			semantic_result=semantic_result,
			message=message,
		)
		semantic_result = SemanticFreshQueryResult(
			status=semantic_result.status,
			interpretation=_augment_entity_scoped_report_interpretation_from_message(
				message=message,
				interpretation=semantic_result.interpretation,
			),
			confidence_threshold=semantic_result.confidence_threshold,
			runtime_error=semantic_result.runtime_error,
			validation_error=semantic_result.validation_error,
			agent_meta=dict(semantic_result.agent_meta or {}),
		)
	semantic_result = SemanticFreshQueryResult(
		status=semantic_result.status,
		interpretation=_normalize_transaction_listing_requested_metrics_from_message(
			message=message,
			interpretation=semantic_result.interpretation,
		),
		confidence_threshold=semantic_result.confidence_threshold,
		runtime_error=semantic_result.runtime_error,
		validation_error=semantic_result.validation_error,
		agent_meta=dict(semantic_result.agent_meta or {}),
	)
	augmented_interpretation = _augment_direct_query_scalar_filters_from_message(
		message=message,
		interpretation=semantic_result.interpretation,
	)
	augmented_interpretation = _augment_master_data_lookup_interpretation_from_message(
		message=message,
		interpretation=augmented_interpretation,
	)
	if augmented_interpretation != semantic_result.interpretation:
		semantic_result = SemanticFreshQueryResult(
			status=semantic_result.status,
			interpretation=augmented_interpretation,
			confidence_threshold=semantic_result.confidence_threshold,
			runtime_error=semantic_result.runtime_error,
			validation_error=semantic_result.validation_error,
			agent_meta=dict(semantic_result.agent_meta or {}),
		)
	compilation_started = time.perf_counter()
	compiler_outcome: CompilerOutcome = compile_fresh_query(
		request_id=request_id,
		session_id=session_id,
		interpretation=semantic_result.interpretation,
		response_policy=response_policy.to_runtime_payload(),
	)
	compilation_latency_ms = int((time.perf_counter() - compilation_started) * 1000)
	out["fresh_query_compiler"] = compiler_outcome.compiler_contract.to_payload()
	out["fresh_query_interpretation"] = semantic_result.to_payload()
	if compiler_outcome.compiled_request_contract is not None:
		out["compiled_query_request"] = compiler_outcome.compiled_request_contract.to_payload()
	out["phase4_latency_breakdown"] = {
		"proposal_generation_latency_ms": proposal_generation_latency_ms,
		"compilation_latency_ms": compilation_latency_ms,
	}
	return out


def _pipeline_requires_deterministic_surface_rescue(pipeline: Dict[str, Any]) -> bool:
	fresh_query_payload = (
		pipeline.get("fresh_query_interpretation")
		if isinstance(pipeline.get("fresh_query_interpretation"), dict)
		else {}
	)
	interpretation_payload = (
		fresh_query_payload.get("interpretation")
		if isinstance(fresh_query_payload.get("interpretation"), dict)
		else {}
	)
	if interpretation_payload:
		candidate_capability_ids = _clean_list(interpretation_payload.get("candidate_capability_ids"))
		candidate_reports = _clean_list(interpretation_payload.get("candidate_reports"))
		return not bool(candidate_capability_ids or candidate_reports)
	status = str(fresh_query_payload.get("status") or "").strip()
	return status in {"runtime_error", "invalid_response", "low_confidence"}


def _semantic_result_requires_deterministic_surface_rescue(result: SemanticFreshQueryResult) -> bool:
	interpretation = result.interpretation
	if interpretation is None:
		return str(result.status or "").strip() in {"runtime_error", "invalid_response", "low_confidence"}
	return not bool(
		list(getattr(interpretation, "candidate_capability_ids", []) or [])
		or list(getattr(interpretation, "candidate_reports", []) or [])
	)


def _recover_pipeline_with_deterministic_surface_fallback(
	*,
	pipeline: Dict[str, Any],
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	clarification_resolution: Dict[str, Any] | None,
) -> Dict[str, Any]:
	if not _pipeline_requires_deterministic_surface_rescue(pipeline):
		return pipeline
	fresh_query_payload = (
		pipeline.get("fresh_query_interpretation")
		if isinstance(pipeline.get("fresh_query_interpretation"), dict)
		else {}
	)
	try:
		confidence_threshold = float(fresh_query_payload.get("confidence_threshold") or _confidence_threshold())
	except Exception:
		confidence_threshold = _confidence_threshold()
	request_id = str(pipeline.get("request_id") or uuid.uuid4().hex).strip()
	deterministic_interpretation = _deterministic_family_surface_interpretation(
		request_id=request_id,
		session_id=session_id,
		message=message,
		confidence_threshold=confidence_threshold,
	)
	if deterministic_interpretation is None:
		return pipeline
	latency_breakdown = (
		pipeline.get("phase4_latency_breakdown")
		if isinstance(pipeline.get("phase4_latency_breakdown"), dict)
		else {}
	)
	semantic_result = SemanticFreshQueryResult(
		status="deterministic_surface_fallback",
		interpretation=deterministic_interpretation,
		confidence_threshold=confidence_threshold,
		runtime_error=str(fresh_query_payload.get("runtime_error") or "").strip(),
		validation_error=str(fresh_query_payload.get("validation_error") or "").strip(),
		agent_meta={
			**(
				fresh_query_payload.get("agent_meta")
				if isinstance(fresh_query_payload.get("agent_meta"), dict)
				else {}
			),
			"deterministic_surface_fallback": True,
			"deterministic_surface_pipeline_rescue": True,
		},
	)
	return _compile_pipeline_from_semantic_result(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		message=message,
		clarification_resolution=clarification_resolution,
		front_door_contract=None,
		semantic_result=semantic_result,
		proposal_generation_latency_ms=int(
			max(0, (latency_breakdown.get("proposal_generation_latency_ms") or 0))
		),
	)


def compile_from_fresh_query_message(
	*,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	recent_messages: List[Dict[str, str]] | None = None,
	clarification_resolution: Dict[str, Any] | None = None,
	front_door_contract: Dict[str, Any] | None = None,
	governed_target_limit: int = 0,
) -> Dict[str, Any]:
	request_id = uuid.uuid4().hex
	proposal_started = time.perf_counter()
	semantic_result = interpret_fresh_query_semantically(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		message=message,
		recent_messages=list(recent_messages or []),
	)
	if _should_retry_with_runtime_default(semantic_result, ""):
		fallback_result = interpret_fresh_query_semantically(
			request_id=request_id,
			session_id=session_id,
			user_id=user_id,
			site_name=site_name,
			message=message,
			recent_messages=list(recent_messages or []),
			model_override=_RUNTIME_DEFAULT_MODEL_OVERRIDE,
		)
		if fallback_result.interpretation is not None:
			fallback_result = SemanticFreshQueryResult(
				status=fallback_result.status,
				interpretation=fallback_result.interpretation,
				confidence_threshold=fallback_result.confidence_threshold,
				runtime_error=fallback_result.runtime_error,
				validation_error=fallback_result.validation_error,
				agent_meta=_merge_fallback_agent_meta(
					semantic_result.agent_meta,
					fallback_result.agent_meta,
					semantic_result.status,
				),
			)
			semantic_result = fallback_result
	master_data_frontdoor_assessment = _frontdoor_master_data_assessment_payload(front_door_contract)
	if master_data_frontdoor_assessment:
		semantic_result = SemanticFreshQueryResult(
			status=semantic_result.status,
			interpretation=_apply_master_data_frontdoor_assessment_to_interpretation(
				request_id=request_id,
				session_id=session_id,
				interpretation=semantic_result.interpretation,
				assessment_payload=master_data_frontdoor_assessment,
			),
			confidence_threshold=semantic_result.confidence_threshold,
			runtime_error=semantic_result.runtime_error,
			validation_error=semantic_result.validation_error,
			agent_meta={
				**(semantic_result.agent_meta if isinstance(semantic_result.agent_meta, dict) else {}),
				"master_data_frontdoor_assessment_applied": True,
			},
		)
	governed_target_limit = int(max(0, governed_target_limit or 0))
	semantic_status = str(getattr(semantic_result, "status", "") or "").strip()
	semantic_intent_class = str(
		getattr(getattr(semantic_result, "interpretation", None), "intent_class", "") or ""
	).strip()
	if (
		governed_target_limit == 0
		and semantic_status == "accepted"
		and semantic_intent_class in {"ranked_entities", "transaction_listing"}
	):
		governed_target_limit = _extract_structural_target_limit_seed(message)
	if (
		governed_target_limit > 0
		and semantic_result.interpretation is not None
		and int(max(0, getattr(semantic_result.interpretation, "target_limit", 0) or 0)) == 0
	):
		seeded_interpretation = build_fresh_query_interpretation_contract(
			request_id=str(getattr(semantic_result.interpretation, "request_id", "") or request_id).strip(),
			session_id=str(getattr(semantic_result.interpretation, "session_id", "") or session_id).strip(),
			intent_class=str(getattr(semantic_result.interpretation, "intent_class", "") or "").strip(),
			candidate_capability_ids=list(getattr(semantic_result.interpretation, "candidate_capability_ids", []) or []),
			candidate_reports=list(getattr(semantic_result.interpretation, "candidate_reports", []) or []),
			requested_dimensions=list(getattr(semantic_result.interpretation, "requested_dimensions", []) or []),
			requested_metrics=list(getattr(semantic_result.interpretation, "requested_metrics", []) or []),
			requested_time_scope=str(getattr(semantic_result.interpretation, "requested_time_scope", "") or "").strip(),
			target_limit=governed_target_limit,
			requested_presentation=list(getattr(semantic_result.interpretation, "requested_presentation", []) or []),
			extracted_slots=dict(getattr(semantic_result.interpretation, "extracted_slots", {}) or {}),
			ambiguity_flags=list(getattr(semantic_result.interpretation, "ambiguity_flags", []) or []),
			ambiguity_reason=str(getattr(semantic_result.interpretation, "ambiguity_reason", "") or "").strip(),
			confidence=float(getattr(semantic_result.interpretation, "confidence", 0.0) or 0.0),
		)
		semantic_result = SemanticFreshQueryResult(
			status=semantic_result.status,
			interpretation=seeded_interpretation,
			confidence_threshold=semantic_result.confidence_threshold,
			runtime_error=semantic_result.runtime_error,
			validation_error=semantic_result.validation_error,
			agent_meta=dict(semantic_result.agent_meta or {}),
		)
	if semantic_result.interpretation is not None:
		current_time_scope = str(getattr(semantic_result.interpretation, "requested_time_scope", "") or "").strip()
		reconciled_time_scope = _strip_structural_limit_time_scope_conflict(
			message=message,
			intent_class=str(getattr(semantic_result.interpretation, "intent_class", "") or "").strip(),
			requested_time_scope=current_time_scope,
			target_limit=int(max(0, getattr(semantic_result.interpretation, "target_limit", 0) or 0)),
		)
		reconciled_slots = dict(getattr(semantic_result.interpretation, "extracted_slots", {}) or {})
		reconciled_time_scope = _strip_unrequested_today_scope_for_transaction_listing(
			message=message,
			intent_class=str(getattr(semantic_result.interpretation, "intent_class", "") or "").strip(),
			requested_time_scope=reconciled_time_scope,
			extracted_slots=reconciled_slots,
		)
		if reconciled_time_scope != current_time_scope:
			if not reconciled_time_scope:
				reconciled_slots = _clear_time_scope_slots(reconciled_slots)
			reconciled_interpretation = build_fresh_query_interpretation_contract(
				request_id=str(getattr(semantic_result.interpretation, "request_id", "") or request_id).strip(),
				session_id=str(getattr(semantic_result.interpretation, "session_id", "") or session_id).strip(),
				intent_class=str(getattr(semantic_result.interpretation, "intent_class", "") or "").strip(),
				candidate_capability_ids=list(getattr(semantic_result.interpretation, "candidate_capability_ids", []) or []),
				candidate_reports=list(getattr(semantic_result.interpretation, "candidate_reports", []) or []),
				requested_dimensions=list(getattr(semantic_result.interpretation, "requested_dimensions", []) or []),
				requested_metrics=list(getattr(semantic_result.interpretation, "requested_metrics", []) or []),
				requested_time_scope=reconciled_time_scope,
				target_limit=int(max(0, getattr(semantic_result.interpretation, "target_limit", 0) or 0)),
				requested_presentation=list(getattr(semantic_result.interpretation, "requested_presentation", []) or []),
				extracted_slots=reconciled_slots,
				ambiguity_flags=list(getattr(semantic_result.interpretation, "ambiguity_flags", []) or []),
				ambiguity_reason=str(getattr(semantic_result.interpretation, "ambiguity_reason", "") or "").strip(),
				confidence=float(getattr(semantic_result.interpretation, "confidence", 0.0) or 0.0),
			)
			semantic_result = SemanticFreshQueryResult(
				status=semantic_result.status,
				interpretation=reconciled_interpretation,
				confidence_threshold=semantic_result.confidence_threshold,
				runtime_error=semantic_result.runtime_error,
				validation_error=semantic_result.validation_error,
				agent_meta=dict(semantic_result.agent_meta or {}),
			)
	if _semantic_result_requires_deterministic_surface_rescue(semantic_result):
		deterministic_interpretation = _deterministic_family_surface_interpretation(
			request_id=request_id,
			session_id=session_id,
			message=message,
			confidence_threshold=semantic_result.confidence_threshold,
		)
		if deterministic_interpretation is not None:
			semantic_result = SemanticFreshQueryResult(
				status="deterministic_surface_fallback",
				interpretation=deterministic_interpretation,
				confidence_threshold=semantic_result.confidence_threshold,
				runtime_error=semantic_result.runtime_error,
				validation_error=semantic_result.validation_error,
				agent_meta={
					**(semantic_result.agent_meta if isinstance(semantic_result.agent_meta, dict) else {}),
					"deterministic_surface_fallback": True,
				},
			)
	proposal_generation_latency_ms = int((time.perf_counter() - proposal_started) * 1000)
	return _compile_pipeline_from_semantic_result(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		message=message,
		clarification_resolution=clarification_resolution,
		front_door_contract=front_door_contract,
		semantic_result=semantic_result,
		proposal_generation_latency_ms=proposal_generation_latency_ms,
	)


def _proposal_cache_hit_from_pipeline(pipeline: Dict[str, Any]) -> bool:
	fresh_query_payload = (
		pipeline.get("fresh_query_interpretation")
		if isinstance(pipeline.get("fresh_query_interpretation"), dict)
		else {}
	)
	agent_meta = (
		fresh_query_payload.get("agent_meta")
		if isinstance(fresh_query_payload.get("agent_meta"), dict)
		else {}
	)
	telemetry = agent_meta.get("telemetry") if isinstance(agent_meta.get("telemetry"), dict) else {}
	return bool(telemetry.get("cache_hit"))


def _proposal_shared_inflight_hit_from_pipeline(pipeline: Dict[str, Any]) -> bool:
	fresh_query_payload = (
		pipeline.get("fresh_query_interpretation")
		if isinstance(pipeline.get("fresh_query_interpretation"), dict)
		else {}
	)
	agent_meta = (
		fresh_query_payload.get("agent_meta")
		if isinstance(fresh_query_payload.get("agent_meta"), dict)
		else {}
	)
	telemetry = agent_meta.get("telemetry") if isinstance(agent_meta.get("telemetry"), dict) else {}
	return bool(telemetry.get("shared_inflight_hit"))


def _interpretation_contract_from_pipeline(pipeline: Dict[str, Any]) -> FreshQueryInterpretationContract | None:
	fresh_query_payload = (
		pipeline.get("fresh_query_interpretation")
		if isinstance(pipeline.get("fresh_query_interpretation"), dict)
		else {}
	)
	interpretation = (
		fresh_query_payload.get("interpretation")
		if isinstance(fresh_query_payload.get("interpretation"), dict)
		else {}
	)
	if not interpretation:
		return None
	return build_fresh_query_interpretation_contract(
		request_id=str(interpretation.get("request_id") or pipeline.get("request_id") or "").strip(),
		session_id=str(interpretation.get("session_id") or pipeline.get("session_id") or "").strip(),
		intent_class=str(interpretation.get("intent_class") or "").strip(),
		candidate_capability_ids=_clean_list(interpretation.get("candidate_capability_ids")),
		candidate_reports=_clean_list(interpretation.get("candidate_reports")),
		requested_dimensions=_clean_list(interpretation.get("requested_dimensions")),
		requested_metrics=_clean_list(interpretation.get("requested_metrics")),
		requested_time_scope=str(interpretation.get("requested_time_scope") or "").strip(),
		requested_presentation=_clean_list(interpretation.get("requested_presentation")),
		extracted_slots=interpretation.get("extracted_slots") if isinstance(interpretation.get("extracted_slots"), dict) else {},
		ambiguity_flags=_clean_list(interpretation.get("ambiguity_flags")),
		ambiguity_reason=str(interpretation.get("ambiguity_reason") or "").strip(),
		confidence=float(interpretation.get("confidence") or 0.0),
	)


def _resolve_capability_ids_for_business_area(option: str) -> List[str]:
	normalized_option = _normalize_key(option)
	if not normalized_option:
		return []
	option_concepts = set(ontology_detect_concepts(option))
	matches: List[str] = []
	for spec in list_capability_specs():
		capability_id = str(spec.get("capability_id") or "").strip()
		if not capability_id:
			continue
		aliases = {
			_normalize_key(capability_id),
			_normalize_key(spec.get("label")),
			_normalize_key(spec.get("name")),
			_normalize_key(spec.get("capability_label")),
		}
		if normalized_option in aliases:
			matches.append(capability_id)
			continue
		capability_concepts = set(capability_ontology_concepts(capability_id))
		if option_concepts and capability_concepts and option_concepts == capability_concepts:
			matches.append(capability_id)
	return list(dict.fromkeys(matches))


def _apply_clarification_resolution_to_interpretation(
	*,
	interpretation: FreshQueryInterpretationContract,
	clarification_resolution: Dict[str, Any] | None = None,
) -> FreshQueryInterpretationContract:
	payload = clarification_resolution if isinstance(clarification_resolution, dict) else {}
	if str(payload.get("decision") or "").strip() != "resolved_option":
		return interpretation
	resolved_slot = payload.get("resolved_slot") if isinstance(payload.get("resolved_slot"), dict) else {}
	if not resolved_slot:
		return interpretation

	candidate_capability_ids = list(_clean_list(interpretation.candidate_capability_ids))
	candidate_reports = list(_clean_list(interpretation.candidate_reports))
	requested_time_scope = str(interpretation.requested_time_scope or "").strip()
	extracted_slots = dict(interpretation.extracted_slots)
	requested_dimensions = list(interpretation.requested_dimensions)
	ambiguity_flags = [
		flag
		for flag in _clean_list(interpretation.ambiguity_flags)
		if flag not in {"ambiguous_report", "ambiguous_capability", "missing_time_scope"}
	]
	ambiguity_reason = str(interpretation.ambiguity_reason or "").strip()

	selected_report = str(resolved_slot.get("selected_report") or "").strip()
	statement_variant = str(resolved_slot.get("statement_variant") or "").strip()
	if not selected_report and statement_variant and str(interpretation.intent_class or "").strip() == "financial_statement":
		selected_report = str(financial_statement_report_name(statement_variant) or "").strip()
	if selected_report:
		candidate_reports = [selected_report]
		report_capabilities = report_capability_ids(selected_report)
		if report_capabilities:
			candidate_capability_ids = list(report_capabilities)
		ambiguity_reason = ""

	selected_time_scope = _normalize_time_scope(resolved_slot.get("selected_time_scope"))
	if selected_time_scope:
		requested_time_scope = selected_time_scope
		ambiguity_reason = ""

	if statement_variant:
		extracted_slots["statement_variant"] = statement_variant
		ambiguity_reason = ""

	for slot_key in ("entity_grain", "lookup_mode", "lookup_projection", "lookup_search_text", "scope_id"):
		slot_value = str(resolved_slot.get(slot_key) or "").strip()
		if slot_value:
			extracted_slots[slot_key] = slot_value
			ambiguity_reason = ""

	if not requested_dimensions:
		entity_grain = str(extracted_slots.get("entity_grain") or "").strip()
		if entity_grain:
			dimension_label = entity_grain_display_label(entity_grain, plural=False).title()
			requested_dimensions = [dimension_label or entity_grain.title()]

	selected_business_area = str(resolved_slot.get("selected_business_area") or "").strip()
	if selected_business_area:
		business_capability_ids = _resolve_capability_ids_for_business_area(selected_business_area)
		if len(business_capability_ids) == 1:
			candidate_capability_ids = list(business_capability_ids)
			default_reports = capability_report_names(business_capability_ids[0])
			if len(default_reports) == 1:
				candidate_reports = list(default_reports)
			ambiguity_reason = ""

	return build_fresh_query_interpretation_contract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class=interpretation.intent_class,
		candidate_capability_ids=candidate_capability_ids,
		candidate_reports=candidate_reports,
		requested_dimensions=requested_dimensions,
		requested_metrics=list(interpretation.requested_metrics),
		requested_time_scope=requested_time_scope,
		requested_presentation=list(interpretation.requested_presentation),
		extracted_slots=extracted_slots,
		ambiguity_flags=ambiguity_flags,
		ambiguity_reason=ambiguity_reason,
		confidence=float(interpretation.confidence or 0.0),
	)
def execute_compiled_fresh_query_message(
	*,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	recent_messages: List[Dict[str, str]] | None = None,
	clarification_resolution: Dict[str, Any] | None = None,
	front_door_contract: Dict[str, Any] | None = None,
	governed_target_limit: int = 0,
) -> Dict[str, Any]:
	total_started = time.perf_counter()
	pipeline = compile_from_fresh_query_message(
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		message=message,
		recent_messages=list(recent_messages or []),
		clarification_resolution=clarification_resolution,
		front_door_contract=front_door_contract,
		governed_target_limit=governed_target_limit,
	)
	pipeline = _recover_pipeline_with_deterministic_surface_fallback(
		pipeline=pipeline,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		message=message,
		clarification_resolution=clarification_resolution,
	)
	latency_breakdown = (
		dict(pipeline.get("phase4_latency_breakdown"))
		if isinstance(pipeline.get("phase4_latency_breakdown"), dict)
		else {}
	)
	proposal_generation_latency_ms = int(max(0, latency_breakdown.get("proposal_generation_latency_ms") or 0))
	compilation_latency_ms = int(max(0, latency_breakdown.get("compilation_latency_ms") or 0))
	composite_plan_started = time.perf_counter()
	interpretation_contract = _interpretation_contract_from_pipeline(pipeline)
	composite_plan_outcome = None
	if interpretation_contract is not None:
		response_policy_contract = (
			pipeline.get("response_policy_contract")
			if isinstance(pipeline.get("response_policy_contract"), dict)
			else {}
		)
		response_policy_payload = {}
		if response_policy_contract:
			response_policy_payload = {
				"analysis_requested": bool(response_policy_contract.get("analysis_requested")),
				"policy_mode": str(response_policy_contract.get("policy_mode") or "").strip(),
				"insight_allowed": bool(response_policy_contract.get("insight_allowed")),
				"recommendation_allowed": bool(response_policy_contract.get("recommendation_allowed")),
				"grounding_rule": str(response_policy_contract.get("grounding_rule") or "").strip(),
				"structure": list(response_policy_contract.get("structure") or []),
			}
		composite_plan_outcome = plan_composite_read(
			request_id=str(pipeline.get("request_id") or uuid.uuid4().hex),
			session_id=session_id,
			message=message,
			interpretation=interpretation_contract,
			response_policy=response_policy_payload if isinstance(response_policy_payload, dict) else {},
		)
		if composite_plan_outcome.plan_contract is not None:
			pipeline["composite_read_plan"] = composite_plan_outcome.plan_contract.to_payload()
		if (
			composite_plan_outcome is not None
			and composite_plan_outcome.compiler_contract is not None
			and str(composite_plan_outcome.status or "").strip() in {"execute", "clarify", "reject"}
		):
			pipeline["fresh_query_compiler"] = composite_plan_outcome.compiler_contract.to_payload()
			if str(composite_plan_outcome.status or "").strip() in {"clarify", "reject"}:
				pipeline.pop("compiled_query_request", None)
	compilation_latency_ms += int((time.perf_counter() - composite_plan_started) * 1000)
	runtime_execution_latency_ms = 0
	semantic_validation_latency_ms = 0
	normalized_family_artifact_payload: Dict[str, Any] = {}
	family_validation_payload: Dict[str, Any] = {}
	rendered_response_payload: Dict[str, Any] = {}
	narrative_response_payload: Dict[str, Any] = {}
	if composite_plan_outcome is not None and str(composite_plan_outcome.status or "").strip() == "execute":
		return execute_composite_read_plan(
			session_id=session_id,
			user_id=user_id,
			site_name=site_name,
			message=message,
			recent_messages=list(recent_messages or []),
			pipeline=pipeline,
			plan_outcome=composite_plan_outcome,
			proposal_generation_latency_ms=proposal_generation_latency_ms,
			compilation_latency_ms=compilation_latency_ms,
			total_started=total_started,
		)
	compiled_query = pipeline.get("compiled_query_request")
	compiler_contract = (
		pipeline.get("fresh_query_compiler")
		if isinstance(pipeline.get("fresh_query_compiler"), dict)
		else {}
	)
	if not isinstance(compiled_query, dict) or not compiled_query:
		total_pipeline_latency_ms = int((time.perf_counter() - total_started) * 1000)
		audit_contract = build_compiled_execution_audit_contract(
			request_id=str(pipeline.get("request_id") or uuid.uuid4().hex),
			session_id=session_id,
			compiler_decision=str(compiler_contract.get("decision") or "").strip(),
			compiler_reason=str(compiler_contract.get("compiler_reason") or "").strip(),
			governed_resolution_details=(
				compiler_contract.get("governed_resolution_details")
				if isinstance(compiler_contract.get("governed_resolution_details"), dict)
				else {}
			),
			capability_id=str(compiler_contract.get("capability_id") or "").strip(),
			selected_report=str(compiler_contract.get("selected_report") or "").strip(),
			governed_family_id=str(compiler_contract.get("selected_report_family") or "").strip(),
			composite_plan_id="",
			proposal_cache_hit=_proposal_cache_hit_from_pipeline(pipeline),
			proposal_shared_inflight_hit=_proposal_shared_inflight_hit_from_pipeline(pipeline),
			compiled_query_available=False,
			runtime_invoked=False,
			runtime_ok=False,
			grounded_validation_status="not_run",
			family_validation_status="not_run",
			semantic_validation_status="not_run",
			proposal_generation_latency_ms=proposal_generation_latency_ms,
			compilation_latency_ms=compilation_latency_ms,
			runtime_execution_latency_ms=0,
			semantic_validation_latency_ms=0,
			total_pipeline_latency_ms=total_pipeline_latency_ms,
			tool_count=0,
			tool_names=[],
		)
		return {
			"pipeline": pipeline,
			"runtime_payload": {},
			"normalized_family_artifact": {},
			"rendered_response": {},
			"family_validation": {},
			"semantic_intent_validation": {},
			"compiled_execution_audit": audit_contract.to_payload(),
			"phase4_latency_breakdown": {
				"proposal_generation_latency_ms": proposal_generation_latency_ms,
				"compilation_latency_ms": compilation_latency_ms,
				"runtime_execution_latency_ms": 0,
				"semantic_validation_latency_ms": 0,
				"total_pipeline_latency_ms": total_pipeline_latency_ms,
			},
		}
	response_policy = (
		compiled_query.get("response_policy")
		if isinstance(compiled_query.get("response_policy"), dict)
		else {}
	)
	runtime_started = time.perf_counter()
	runtime_payload = execute_governed_report(
		report_name=str(compiled_query.get("selected_report") or "").strip(),
		filters=compiled_query.get("filters") if isinstance(compiled_query.get("filters"), dict) else {},
		user=user_id,
		mode="compiled_read_query",
		target_limit=int(max(0, compiled_query.get("target_limit") or 0)),
	)
	if not bool(runtime_payload.get("ok")) or not list(runtime_payload.get("tool_trace") or []):
		try:
			runtime_payload = call_qwen_runtime_chat(
				session_id=session_id,
				user_id=user_id,
				site_name=site_name,
				message=message,
				recent_messages=list(recent_messages or []),
				response_policy=response_policy,
				family_tool_context={},
				mode="compiled_read_query",
				compiled_query=compiled_query,
				request_id=str(pipeline.get("request_id") or uuid.uuid4().hex),
			)
		except QwenRuntimeClientError as exc:
			runtime_payload = {
				"ok": False,
				"tool_trace": [],
				"agent_meta": {"engine": "unavailable", "mode": "compiled_read_query"},
				"error": str(exc),
			}
	runtime_execution_latency_ms = int((time.perf_counter() - runtime_started) * 1000)
	adapter_outcome = build_normalized_family_artifact(
		request_id=str(pipeline.get("request_id") or uuid.uuid4().hex),
		compiler_contract=compiler_contract,
		runtime_payload=runtime_payload if isinstance(runtime_payload, dict) else {},
		intent_class=str(
			(((pipeline.get("fresh_query_interpretation") or {}).get("interpretation") or {}).get("intent_class"))
			if isinstance(pipeline.get("fresh_query_interpretation"), dict)
			else ""
		),
		preferred_family_id=_preferred_family_id_for_message(
			message=message,
			compiler_contract=compiler_contract,
			interpretation_contract=(
				(pipeline.get("fresh_query_interpretation") or {}).get("interpretation")
				if isinstance(pipeline.get("fresh_query_interpretation"), dict)
				and isinstance((pipeline.get("fresh_query_interpretation") or {}).get("interpretation"), dict)
				else {}
			),
		),
	)
	if adapter_outcome.artifact_contract is not None:
		normalized_family_artifact_payload = adapter_outcome.artifact_contract.to_payload()
	family_validation = validate_normalized_family_artifact(
		request_id=str(pipeline.get("request_id") or uuid.uuid4().hex),
		compiler_contract=compiler_contract,
		artifact_contract=adapter_outcome.artifact_contract,
		family_id=adapter_outcome.family_id,
		adapter_errors=adapter_outcome.errors,
		adapter_warnings=adapter_outcome.warnings,
	)
	if family_validation is not None:
		family_validation_payload = family_validation.to_payload()
	render_outcome = render_normalized_family_response(
		request_id=str(pipeline.get("request_id") or uuid.uuid4().hex),
		artifact_contract=adapter_outcome.artifact_contract,
	)
	if render_outcome.contract is not None:
		rendered_response_payload = render_outcome.contract.to_payload()
	semantic_validation_payload: Dict[str, Any] = {}
	if isinstance(runtime_payload, dict) and isinstance(runtime_payload.get("tool_trace"), list) and runtime_payload.get("tool_trace"):
		semantic_started = time.perf_counter()
		semantic_validation = validate_compiled_semantic_result(
			interaction_contract=(
				pipeline.get("interaction_contract")
				if isinstance(pipeline.get("interaction_contract"), dict)
				else {}
			),
			interpretation_contract=(
				(pipeline.get("fresh_query_interpretation") or {}).get("interpretation")
				if isinstance(pipeline.get("fresh_query_interpretation"), dict)
				and isinstance((pipeline.get("fresh_query_interpretation") or {}).get("interpretation"), dict)
				else {}
			),
			compiler_contract=compiler_contract,
			runtime_payload=runtime_payload if isinstance(runtime_payload, dict) else {},
			normalized_family_artifact=normalized_family_artifact_payload,
			family_validation_payload=family_validation_payload,
		)
		semantic_validation_latency_ms = int((time.perf_counter() - semantic_started) * 1000)
		semantic_validation_payload = semantic_validation.to_payload()
	if (
		normalized_family_artifact_payload
		and rendered_response_payload
		and str(family_validation_payload.get("status") or "").strip() == "pass"
		and str(semantic_validation_payload.get("status") or "").strip() == "pass"
	):
		artifact_context = build_artifact_narrative_context(
			request_id=str(pipeline.get("request_id") or uuid.uuid4().hex),
			artifact_payload=normalized_family_artifact_payload,
			rendered_response_payload=rendered_response_payload,
			response_policy=response_policy,
			validation_payload=family_validation_payload,
		)
		narrative_runtime_payload = narrate_governed_artifact(
			session_id=session_id,
			user_id=user_id,
			site_name=site_name,
			message=message,
			request_id=str(pipeline.get("request_id") or uuid.uuid4().hex),
			artifact_context=artifact_context,
			response_policy=response_policy,
		)
		narrative_contract = build_artifact_narrative_contract(
			request_id=str(pipeline.get("request_id") or uuid.uuid4().hex),
			artifact_context=artifact_context,
			runtime_payload=narrative_runtime_payload,
		)
		if narrative_contract is not None:
			narrative_response_payload = narrative_contract.to_payload()
		if _family_narrative_prefers_rendered_response(
			family_id=str(adapter_outcome.family_id or compiler_contract.get("selected_report_family") or "").strip(),
			response_policy=response_policy,
		):
			narrative_response_payload = {}
	total_pipeline_latency_ms = int((time.perf_counter() - total_started) * 1000)
	tool_trace = runtime_payload.get("tool_trace") if isinstance(runtime_payload.get("tool_trace"), list) else []
	tool_names = [
		str(item.get("tool") or "").strip()
		for item in tool_trace
		if isinstance(item, dict) and str(item.get("tool") or "").strip()
	]
	agent_meta = runtime_payload.get("agent_meta") if isinstance(runtime_payload.get("agent_meta"), dict) else {}
	runtime_validation = agent_meta.get("validation") if isinstance(agent_meta.get("validation"), dict) else {}
	audit_contract = build_compiled_execution_audit_contract(
		request_id=str(pipeline.get("request_id") or uuid.uuid4().hex),
		session_id=session_id,
		compiler_decision=str(compiler_contract.get("decision") or "").strip(),
		compiler_reason=str(compiler_contract.get("compiler_reason") or "").strip(),
		governed_resolution_details=(
			compiler_contract.get("governed_resolution_details")
			if isinstance(compiler_contract.get("governed_resolution_details"), dict)
			else {}
		),
		capability_id=str(compiler_contract.get("capability_id") or "").strip(),
		selected_report=str(compiler_contract.get("selected_report") or "").strip(),
		governed_family_id=str(adapter_outcome.family_id or compiler_contract.get("selected_report_family") or "").strip(),
		composite_plan_id="",
		proposal_cache_hit=_proposal_cache_hit_from_pipeline(pipeline),
		proposal_shared_inflight_hit=_proposal_shared_inflight_hit_from_pipeline(pipeline),
		compiled_query_available=True,
		runtime_invoked=True,
		runtime_ok=bool(runtime_payload.get("ok")),
		runtime_engine=str(agent_meta.get("engine") or "").strip(),
		runtime_model=str(agent_meta.get("model") or "").strip(),
		grounded_validation_status=str(runtime_validation.get("status") or "unknown").strip(),
		family_validation_status=str(family_validation_payload.get("status") or "not_run").strip(),
		semantic_validation_status=str(semantic_validation_payload.get("status") or "not_run").strip(),
		semantic_validation_errors=(
			semantic_validation_payload.get("errors")
			if isinstance(semantic_validation_payload.get("errors"), list)
			else []
		),
		semantic_validation_warnings=(
			semantic_validation_payload.get("warnings")
			if isinstance(semantic_validation_payload.get("warnings"), list)
			else []
		),
		proposal_generation_latency_ms=proposal_generation_latency_ms,
		compilation_latency_ms=compilation_latency_ms,
		runtime_execution_latency_ms=runtime_execution_latency_ms,
		semantic_validation_latency_ms=semantic_validation_latency_ms,
		total_pipeline_latency_ms=total_pipeline_latency_ms,
		tool_count=len(tool_names),
		tool_names=tool_names,
	)
	return {
		"pipeline": pipeline,
		"runtime_payload": runtime_payload,
		"normalized_family_artifact": normalized_family_artifact_payload,
		"rendered_response": rendered_response_payload,
		"narrative_response": narrative_response_payload,
		"family_validation": family_validation_payload,
		"semantic_intent_validation": semantic_validation_payload,
		"compiled_execution_audit": audit_contract.to_payload(),
		"phase4_latency_breakdown": {
			"proposal_generation_latency_ms": proposal_generation_latency_ms,
			"compilation_latency_ms": compilation_latency_ms,
			"runtime_execution_latency_ms": runtime_execution_latency_ms,
			"semantic_validation_latency_ms": semantic_validation_latency_ms,
			"total_pipeline_latency_ms": total_pipeline_latency_ms,
		},
	}
