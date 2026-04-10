from __future__ import annotations

from copy import deepcopy
import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List


def _resolve_metadata_dir() -> Path:
	env_value = str(os.getenv("QWEN_ENTERPRISE_METADATA_DIR") or "").strip()
	if env_value:
		return Path(env_value)

	candidates = [
		Path("/home/frappe/frappe-bench/qwen_enterprise_metadata"),
		Path(__file__).resolve().parents[6] / "impl_factory" / "03_config" / "qwen_enterprise_metadata",
	]
	for path in candidates:
		if path.exists():
			return path
	return candidates[0]


_METADATA_DIR = _resolve_metadata_dir()


@lru_cache(maxsize=8)
def _load_json(name: str) -> Dict[str, Any]:
	path = _METADATA_DIR / name
	with path.open("r", encoding="utf-8") as f:
		obj = json.load(f)
	return obj if isinstance(obj, dict) else {}


def _load_json_copy(name: str) -> Dict[str, Any]:
	return deepcopy(_load_json(name))


def load_business_ontology() -> Dict[str, Any]:
	return _load_json_copy("business_ontology.json")


def load_capability_registry() -> Dict[str, Any]:
	return _load_json_copy("capability_registry.json")


def load_report_registry() -> Dict[str, Any]:
	return _load_json_copy("report_registry.json")


def load_report_family_registry() -> Dict[str, Any]:
	return _load_json_copy("report_family_registry.json")


def load_composite_read_registry() -> Dict[str, Any]:
	return _load_json_copy("composite_read_registry.json")


def load_family_evaluation_registry() -> Dict[str, Any]:
	return _load_json_copy("family_evaluation_registry.json")


def load_frontdoor_intent_registry() -> Dict[str, Any]:
	return _load_json_copy("frontdoor_intent_registry.json")


def load_report_surface_evidence_registry() -> Dict[str, Any]:
	return _load_json_copy("report_surface_evidence_registry.json")


def load_validation_rules() -> Dict[str, Any]:
	return _load_json_copy("validation_rules.json")


def load_semantic_resolution_registry() -> Dict[str, Any]:
	return _load_json_copy("semantic_resolution_registry.json")


def load_financial_summary_clarification_registry() -> Dict[str, Any]:
	return _load_json_copy("financial_summary_clarification_registry.json")


def load_financial_summary_resolution_registry() -> Dict[str, Any]:
	return _load_json_copy("financial_summary_resolution_registry.json")


def load_business_definition_registry() -> Dict[str, Any]:
	return _load_json_copy("business_definition_registry.json")


def load_governed_formula_registry() -> Dict[str, Any]:
	return _load_json_copy("governed_formula_registry.json")


def load_business_threshold_registry() -> Dict[str, Any]:
	return _load_json_copy("business_threshold_registry.json")


def load_business_rule_registry() -> Dict[str, Any]:
	return _load_json_copy("business_rule_registry.json")


def load_governed_kpi_execution_registry() -> Dict[str, Any]:
	return _load_json_copy("governed_kpi_execution_registry.json")


def load_smoke_fixture_registry() -> Dict[str, Any]:
	return _load_json_copy("smoke_fixture_registry.json")


def get_capability_spec(capability_id: str) -> Dict[str, Any]:
	capabilities = load_capability_registry().get("capabilities")
	if not isinstance(capabilities, list):
		return {}
	target = str(capability_id or "").strip()
	for item in capabilities:
		if not isinstance(item, dict):
			continue
		if str(item.get("capability_id") or "").strip() == target:
			return dict(item)
	return {}


def list_capability_specs() -> List[Dict[str, Any]]:
	values = load_capability_registry().get("capabilities")
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def get_report_spec(report_name: str) -> Dict[str, Any]:
	reports = load_report_registry().get("reports")
	if not isinstance(reports, list):
		return {}
	name = str(report_name or "").strip().lower()
	for item in reports:
		if not isinstance(item, dict):
			continue
		if str(item.get("report_name") or "").strip().lower() == name:
			return dict(item)
	return {}


def report_direct_query_filter_value_aliases(report_name: str, field_name: str) -> List[Dict[str, Any]]:
	report_spec = get_report_spec(report_name)
	direct_query = report_spec.get("direct_query") if isinstance(report_spec.get("direct_query"), dict) else {}
	filter_value_aliases = (
		direct_query.get("filter_value_aliases")
		if isinstance(direct_query.get("filter_value_aliases"), dict)
		else {}
	)
	values = filter_value_aliases.get(str(field_name or "").strip())
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def list_report_surface_evidence_specs() -> List[Dict[str, Any]]:
	values = load_report_surface_evidence_registry().get("report_surface_evidence")
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def get_report_surface_evidence_spec(report_name: str) -> Dict[str, Any]:
	name = str(report_name or "").strip().lower()
	for item in list_report_surface_evidence_specs():
		if str(item.get("report_name") or "").strip().lower() == name:
			return item
	return {}


def list_report_family_specs() -> List[Dict[str, Any]]:
	values = load_report_family_registry().get("families")
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def get_report_family_spec(family_id: str) -> Dict[str, Any]:
	target = str(family_id or "").strip()
	for item in list_report_family_specs():
		if str(item.get("family_id") or "").strip() == target:
			return item
	return {}


def list_composite_read_specs() -> List[Dict[str, Any]]:
	values = load_composite_read_registry().get("composite_profiles")
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def get_composite_read_spec(plan_id: str) -> Dict[str, Any]:
	target = str(plan_id or "").strip()
	for item in list_composite_read_specs():
		if str(item.get("plan_id") or "").strip() == target:
			return item
	return {}


def list_family_evaluation_case_sets() -> List[Dict[str, Any]]:
	values = load_family_evaluation_registry().get("case_sets")
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def get_family_evaluation_case_set(set_id: str) -> Dict[str, Any]:
	target = str(set_id or "").strip()
	for item in list_family_evaluation_case_sets():
		if str(item.get("set_id") or "").strip() == target:
			return item
	return {}


def list_family_latency_budget_specs() -> List[Dict[str, Any]]:
	values = load_family_evaluation_registry().get("family_latency_budgets")
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def get_family_latency_budget_spec(family_id: str) -> Dict[str, Any]:
	target = str(family_id or "").strip()
	for item in list_family_latency_budget_specs():
		if str(item.get("family_id") or "").strip() == target:
			return item
	return {}


def list_intent_class_specs() -> List[Dict[str, Any]]:
	values = load_capability_registry().get("intent_classes")
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def get_intent_class_spec(intent_class_id: str) -> Dict[str, Any]:
	target = str(intent_class_id or "").strip()
	for item in list_intent_class_specs():
		if str(item.get("intent_class_id") or "").strip() == target:
			return item
	return {}


def list_semantic_resolution_slot_definitions() -> List[Dict[str, Any]]:
	values = load_semantic_resolution_registry().get("slot_definitions")
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def get_semantic_resolution_slot_definition(slot_name: str) -> Dict[str, Any]:
	target = str(slot_name or "").strip()
	for item in list_semantic_resolution_slot_definitions():
		if str(item.get("slot_name") or "").strip() == target:
			return item
	return {}


def list_semantic_resolution_alias_entries(slot_name: str) -> List[Dict[str, Any]]:
	alias_maps = load_semantic_resolution_registry().get("alias_maps")
	if not isinstance(alias_maps, dict):
		return []
	values = alias_maps.get(str(slot_name or "").strip())
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def list_financial_summary_clarification_specs() -> List[Dict[str, Any]]:
	values = load_financial_summary_clarification_registry().get("reason_types")
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def list_smoke_fixture_specs() -> List[Dict[str, Any]]:
	values = load_smoke_fixture_registry().get("fixtures")
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def list_business_definition_specs() -> List[Dict[str, Any]]:
	values = load_business_definition_registry().get("definitions")
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def get_business_definition_spec(definition_id: str) -> Dict[str, Any]:
	target = str(definition_id or "").strip()
	for item in list_business_definition_specs():
		if str(item.get("definition_id") or "").strip() == target:
			return item
	return {}


def list_governed_formula_specs() -> List[Dict[str, Any]]:
	values = load_governed_formula_registry().get("formulas")
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def get_governed_formula_spec(formula_id: str) -> Dict[str, Any]:
	target = str(formula_id or "").strip()
	for item in list_governed_formula_specs():
		if str(item.get("formula_id") or "").strip() == target:
			return item
	return {}


def list_governed_formula_specs_for_definition(definition_id: str) -> List[Dict[str, Any]]:
	target = str(definition_id or "").strip()
	if not target:
		return []
	return [
		item
		for item in list_governed_formula_specs()
		if str(item.get("definition_id") or "").strip() == target
	]


def list_business_threshold_specs() -> List[Dict[str, Any]]:
	values = load_business_threshold_registry().get("threshold_sets")
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def get_business_threshold_spec(threshold_id: str) -> Dict[str, Any]:
	target = str(threshold_id or "").strip()
	for item in list_business_threshold_specs():
		if str(item.get("threshold_id") or "").strip() == target:
			return item
	return {}


def list_business_threshold_specs_for_definition(definition_id: str) -> List[Dict[str, Any]]:
	target = str(definition_id or "").strip()
	if not target:
		return []
	return [
		item
		for item in list_business_threshold_specs()
		if str(item.get("definition_id") or "").strip() == target
	]


def list_business_threshold_specs_for_formula(formula_id: str) -> List[Dict[str, Any]]:
	target = str(formula_id or "").strip()
	if not target:
		return []
	return [
		item
		for item in list_business_threshold_specs()
		if str(item.get("formula_id") or "").strip() == target
	]


def list_business_rule_specs() -> List[Dict[str, Any]]:
	values = load_business_rule_registry().get("rules")
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def get_business_rule_spec(rule_id: str) -> Dict[str, Any]:
	target = str(rule_id or "").strip()
	for item in list_business_rule_specs():
		if str(item.get("rule_id") or "").strip() == target:
			return item
	return {}


def list_governed_kpi_execution_specs() -> List[Dict[str, Any]]:
	values = load_governed_kpi_execution_registry().get("executions")
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def get_governed_kpi_execution_spec(execution_id: str) -> Dict[str, Any]:
	target = str(execution_id or "").strip()
	for item in list_governed_kpi_execution_specs():
		if str(item.get("execution_id") or "").strip() == target:
			return item
	return {}


def list_governed_kpi_execution_specs_for_definition(definition_id: str) -> List[Dict[str, Any]]:
	target = str(definition_id or "").strip()
	if not target:
		return []
	return [
		item
		for item in list_governed_kpi_execution_specs()
		if str(item.get("definition_id") or "").strip() == target
	]


def list_governed_kpi_execution_specs_for_formula(formula_id: str) -> List[Dict[str, Any]]:
	target = str(formula_id or "").strip()
	if not target:
		return []
	return [
		item
		for item in list_governed_kpi_execution_specs()
		if str(item.get("formula_id") or "").strip() == target
	]


def list_governed_kpi_execution_specs_for_shape(execution_shape: str) -> List[Dict[str, Any]]:
	target = str(execution_shape or "").strip()
	if not target:
		return []
	return [
		item
		for item in list_governed_kpi_execution_specs()
		if str(item.get("execution_shape") or "").strip() == target
	]


def get_smoke_fixture_spec(fixture_id: str) -> Dict[str, Any]:
	target = str(fixture_id or "").strip()
	for item in list_smoke_fixture_specs():
		if str(item.get("fixture_id") or "").strip() == target:
			return item
	return {}


def get_financial_summary_clarification_spec(reason_type: str) -> Dict[str, Any]:
	target = str(reason_type or "").strip()
	for item in list_financial_summary_clarification_specs():
		if str(item.get("reason_type") or "").strip() == target:
			return item
	return {}


def list_financial_summary_domain_rules() -> List[Dict[str, Any]]:
	values = load_financial_summary_resolution_registry().get("domain_rules")
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def list_financial_summary_metric_family_rules() -> List[Dict[str, Any]]:
	values = load_financial_summary_resolution_registry().get("metric_family_rules")
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def list_financial_summary_focus_rules() -> List[Dict[str, Any]]:
	values = load_financial_summary_resolution_registry().get("focus_rules")
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def list_financial_summary_grain_rules() -> List[Dict[str, Any]]:
	values = load_financial_summary_resolution_registry().get("grain_rules")
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def list_financial_summary_normalization_rules() -> List[Dict[str, Any]]:
	values = load_financial_summary_resolution_registry().get("normalization_rules")
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def list_financial_summary_clarification_rules() -> List[Dict[str, Any]]:
	values = load_financial_summary_resolution_registry().get("clarification_rules")
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def get_financial_summary_clarification_policies() -> Dict[str, Any]:
	value = load_financial_summary_resolution_registry().get("clarification_policies")
	return dict(value) if isinstance(value, dict) else {}


def list_frontdoor_intent_specs() -> List[Dict[str, Any]]:
	values = load_frontdoor_intent_registry().get("intent_classes")
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def get_frontdoor_intent_spec(intent_class_id: str) -> Dict[str, Any]:
	target = str(intent_class_id or "").strip()
	for item in list_frontdoor_intent_specs():
		if str(item.get("intent_class_id") or "").strip() == target:
			return item
	return {}


def _normalize_ontology_text(value: str) -> str:
	return " ".join(str(value or "").strip().lower().split())


def _ontology_contains_alias(text: str, alias: str) -> bool:
	value = _normalize_ontology_text(text)
	target = _normalize_ontology_text(alias)
	if not value or not target:
		return False
	pattern = r"(^|[^a-z0-9])" + re.escape(target) + r"([^a-z0-9]|$)"
	return bool(re.search(pattern, value))


def list_followup_class_specs() -> List[Dict[str, Any]]:
	values = load_business_ontology().get("follow_up_classes")
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def get_followup_class_spec(mode: str) -> Dict[str, Any]:
	target = str(mode or "").strip()
	for item in list_followup_class_specs():
		if str(item.get("mode") or "").strip() == target:
			return item
	return {}


def ontology_followup_aliases(mode: str, language: str = "en") -> List[str]:
	item = get_followup_class_spec(mode)
	aliases = item.get("aliases")
	if not isinstance(aliases, dict):
		return []
	values = aliases.get(language)
	if not isinstance(values, list):
		return []
	return [str(x or "").strip().lower() for x in values if str(x or "").strip()]


def ontology_followup_slot_aliases(mode: str, slot_key: str, language: str = "en") -> Dict[str, List[str]]:
	item = get_followup_class_spec(mode)
	slot_aliases = item.get("slot_aliases")
	if not isinstance(slot_aliases, dict):
		return {}
	slot_values = slot_aliases.get(str(slot_key or "").strip())
	if not isinstance(slot_values, dict):
		return {}
	out: Dict[str, List[str]] = {}
	for value_key, language_map in slot_values.items():
		if not isinstance(language_map, dict):
			continue
		values = language_map.get(language)
		if not isinstance(values, list):
			continue
		clean = [str(x or "").strip().lower() for x in values if str(x or "").strip()]
		if clean:
			out[str(value_key or "").strip()] = clean
	return out
	return []


def ontology_detect_followup_modes(message: str, language: str = "en") -> List[str]:
	text = _normalize_ontology_text(message)
	if not text:
		return []
	out: List[str] = []
	for item in list_followup_class_specs():
		mode = str(item.get("mode") or "").strip()
		if not mode:
			continue
		values = ontology_followup_aliases(mode, language=language)
		if any(_ontology_contains_alias(text, alias) for alias in values):
			out.append(mode)
	return list(dict.fromkeys(out))


def ontology_business_terms(language: str = "en") -> List[str]:
	entries = load_business_ontology().get("concepts")
	if not isinstance(entries, list):
		return []
	out: List[str] = []
	for item in entries:
		if not isinstance(item, dict):
			continue
		values = _ontology_alias_values(item, language=language, include_extended=False)
		out.extend(str(x or "").strip().lower() for x in values if str(x or "").strip())
	return list(dict.fromkeys(out))


def all_ontology_concepts() -> List[str]:
	entries = load_business_ontology().get("concepts")
	if not isinstance(entries, list):
		return []
	out: List[str] = []
	for item in entries:
		if not isinstance(item, dict):
			continue
		value = str(item.get("concept_id") or "").strip()
		if value:
			out.append(value)
	return list(dict.fromkeys(out))


def _canonicalize_ontology_values(values: List[Any], language: str = "en") -> List[str]:
	known_concepts = set(all_ontology_concepts())
	out: List[str] = []
	for item in values or []:
		value = str(item or "").strip()
		if not value:
			continue
		if value in known_concepts:
			out.append(value)
			continue
		out.extend(ontology_detect_concepts(value, language=language))
	return list(dict.fromkeys([value for value in out if value]))


def governed_self_contained_business_terms(language: str = "en") -> List[str]:
	out: List[str] = list(ontology_business_terms(language))
	for spec in list_report_family_specs():
		report_names = spec.get("report_names")
		if isinstance(report_names, list):
			out.extend(str(x or "").strip().lower() for x in report_names if str(x or "").strip())
	return list(dict.fromkeys(out))


def ontology_concept_aliases(concept_id: str, language: str = "en") -> List[str]:
	target = str(concept_id or "").strip()
	if not target:
		return []
	entries = load_business_ontology().get("concepts")
	if not isinstance(entries, list):
		return []
	for item in entries:
		if not isinstance(item, dict):
			continue
		if str(item.get("concept_id") or "").strip() != target:
			continue
		values = _ontology_alias_values(item, language=language, include_extended=False)
		return [str(x or "").strip().lower() for x in values if str(x or "").strip()]
	return []


def _ontology_alias_values(item: Dict[str, Any], *, language: str = "en", include_extended: bool = False) -> List[str]:
	aliases = item.get("aliases")
	out: List[str] = []
	if isinstance(aliases, dict):
		values = aliases.get(language)
		if isinstance(values, list):
			out.extend(str(x or "").strip().lower() for x in values if str(x or "").strip())
	if include_extended:
		extended_aliases = item.get("extended_aliases")
		if isinstance(extended_aliases, dict):
			values = extended_aliases.get(language)
			if isinstance(values, list):
				out.extend(str(x or "").strip().lower() for x in values if str(x or "").strip())
	return list(dict.fromkeys(out))


def ontology_detect_concepts(message: str, language: str = "en", include_extended: bool = True) -> List[str]:
	text = _normalize_ontology_text(message)
	if not text:
		return []
	entries = load_business_ontology().get("concepts")
	if not isinstance(entries, list):
		return []
	out: List[str] = []
	for item in entries:
		if not isinstance(item, dict):
			continue
		concept_id = str(item.get("concept_id") or "").strip()
		if not concept_id:
			continue
		values = _ontology_alias_values(item, language=language, include_extended=include_extended)
		if any(_ontology_contains_alias(text, alias) for alias in values if str(alias or "").strip()):
			out.append(concept_id)
	return list(dict.fromkeys(out))


def ontology_self_contained_prefixes(language: str = "en") -> List[str]:
	hints = load_business_ontology().get("interaction_hints")
	if not isinstance(hints, dict):
		return []
	prefixes = hints.get("self_contained_prefixes")
	if not isinstance(prefixes, dict):
		return []
	values = prefixes.get(language)
	if not isinstance(values, list):
		return []
	return [str(x or "").strip().lower() for x in values if str(x or "").strip()]


def ontology_query_slot_aliases(slot_key: str, language: str = "en") -> Dict[str, List[str]]:
	slot_aliases = load_business_ontology().get("query_slot_aliases")
	if not isinstance(slot_aliases, dict):
		return {}
	slot_values = slot_aliases.get(str(slot_key or "").strip())
	if not isinstance(slot_values, dict):
		return {}
	out: Dict[str, List[str]] = {}
	for value_key, language_map in slot_values.items():
		if not isinstance(language_map, dict):
			continue
		values = language_map.get(language)
		if not isinstance(values, list):
			continue
		clean = [str(x or "").strip().lower() for x in values if str(x or "").strip()]
		if clean:
			out[str(value_key or "").strip()] = clean
	return out


def report_capability_ids(report_name: str) -> List[str]:
	spec = get_report_spec(report_name)
	values = spec.get("capability_ids")
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def capability_intent_classes(capability_id: str) -> List[str]:
	values = get_capability_spec(capability_id).get("intent_classes")
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def capability_ontology_concepts(capability_id: str) -> List[str]:
	values = get_capability_spec(capability_id).get("ontology_concepts")
	if not isinstance(values, list):
		return []
	return _canonicalize_ontology_values(values)


def capability_semantic_tags(capability_id: str) -> List[str]:
	values = get_capability_spec(capability_id).get("semantic_tags")
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def capability_report_names(capability_id: str) -> List[str]:
	values = get_capability_spec(capability_id).get("report_names")
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def capability_default_report_name(capability_id: str) -> str:
	return str(get_capability_spec(capability_id).get("default_report_name") or "").strip()


def capability_summary_report_name(capability_id: str) -> str:
	return str(get_capability_spec(capability_id).get("summary_report_name") or "").strip()


def capability_detail_report_name(capability_id: str) -> str:
	return str(get_capability_spec(capability_id).get("detail_report_name") or "").strip()


def capability_fresh_query_defaults(capability_id: str, intent_class: str = "") -> Dict[str, Any]:
	spec = get_capability_spec(capability_id)
	defaults = spec.get("fresh_query_defaults")
	if not isinstance(defaults, dict):
		return {}
	if intent_class:
		value = defaults.get(str(intent_class or "").strip())
		return dict(value) if isinstance(value, dict) else {}
	return dict(defaults)


def capability_business_family_ids(capability_id: str) -> List[str]:
	target = str(capability_id or "").strip()
	if not target:
		return []
	out: List[str] = []
	for spec in list_report_family_specs():
		values = spec.get("capability_ids")
		if not isinstance(values, list):
			continue
		if target in {str(x or "").strip() for x in values if str(x or "").strip()}:
			family_id = str(spec.get("family_id") or "").strip()
			if family_id:
				out.append(family_id)
	return list(dict.fromkeys(out))


def report_supported_intent_classes(report_name: str) -> List[str]:
	values = get_report_spec(report_name).get("supported_intent_classes")
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def report_semantic_tags(report_name: str) -> List[str]:
	values = get_report_spec(report_name).get("semantic_tags")
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def report_supported_dimensions(report_name: str) -> List[str]:
	values = get_report_spec(report_name).get("supported_dimensions")
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def report_supported_metrics(report_name: str) -> List[str]:
	values = get_report_spec(report_name).get("supported_metrics")
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def report_defaultable_filters(report_name: str) -> List[Dict[str, Any]]:
	values = get_report_spec(report_name).get("defaultable_filters")
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def report_validation_profile(report_name: str) -> str:
	return str(get_report_spec(report_name).get("validation_profile") or "").strip()


def report_business_family_ids(report_name: str) -> List[str]:
	target = str(report_name or "").strip().lower()
	if not target:
		return []
	out: List[str] = []
	for spec in list_report_family_specs():
		values = spec.get("report_names")
		if not isinstance(values, list):
			continue
		report_names = {str(x or "").strip().lower() for x in values if str(x or "").strip()}
		if target in report_names:
			family_id = str(spec.get("family_id") or "").strip()
			if family_id:
				out.append(family_id)
	return list(dict.fromkeys(out))


def report_family_supported_intent_classes(family_id: str) -> List[str]:
	values = get_report_family_spec(family_id).get("supported_intent_classes")
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def report_family_default_intent_class(family_id: str) -> str:
	spec = get_report_family_spec(family_id)
	value = str(spec.get("default_intent_class") or "").strip()
	if value:
		return value
	values = report_family_supported_intent_classes(family_id)
	return str((values or [""])[0] or "").strip()


def report_family_canonical_metrics(family_id: str) -> List[str]:
	values = get_report_family_spec(family_id).get("canonical_metrics")
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def report_family_canonical_dimensions(family_id: str) -> List[str]:
	values = get_report_family_spec(family_id).get("canonical_dimensions")
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def report_family_adapter_id(family_id: str) -> str:
	return str(get_report_family_spec(family_id).get("adapter_id") or "").strip()


def report_family_agent_tool_id(family_id: str) -> str:
	return str(get_report_family_spec(family_id).get("agent_tool_id") or "").strip()


def report_family_agent_prompt_hint(family_id: str) -> str:
	return str(get_report_family_spec(family_id).get("agent_prompt_hint") or "").strip()


def report_family_renderer_id(family_id: str) -> str:
	return str(get_report_family_spec(family_id).get("renderer_id") or "").strip()


def report_family_validation_profile(family_id: str) -> str:
	return str(get_report_family_spec(family_id).get("validation_profile") or "").strip()


def report_family_semantic_tags(family_id: str) -> List[str]:
	values = get_report_family_spec(family_id).get("semantic_tags")
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def report_family_composite_allowed(family_id: str) -> bool:
	return bool(get_report_family_spec(family_id).get("composite_allowed"))


def report_family_report_names(family_id: str) -> List[str]:
	values = get_report_family_spec(family_id).get("report_names")
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def report_family_capability_ids(family_id: str) -> List[str]:
	values = get_report_family_spec(family_id).get("capability_ids")
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def report_family_routing_hints(family_id: str) -> Dict[str, Any]:
	value = get_report_family_spec(family_id).get("routing_hints")
	return dict(value) if isinstance(value, dict) else {}


def report_family_display_policies(family_id: str) -> Dict[str, Any]:
	value = get_report_family_spec(family_id).get("display_policies")
	return dict(value) if isinstance(value, dict) else {}


def report_family_entity_dimension_label(
	family_id: str,
	*,
	entity_fields: List[str] | tuple[str, ...] | None = None,
	default_label: str = "",
) -> str:
	policies = report_family_display_policies(family_id)
	label_map = policies.get("entity_dimension_labels")
	if not isinstance(label_map, dict):
		return str(default_label or "").strip()
	for field_name in entity_fields or []:
		key = str(field_name or "").strip()
		if not key:
			continue
		value = str(label_map.get(key) or "").strip()
		if value:
			return value
	return str(default_label or "").strip()


def report_family_ontology_concepts(family_id: str) -> List[str]:
	values = report_family_routing_hints(family_id).get("ontology_concepts")
	if not isinstance(values, list):
		return []
	return _canonicalize_ontology_values(values)


def report_family_transitional_surface_markers(family_id: str) -> List[str]:
	values = report_family_routing_hints(family_id).get("intent_markers")
	if not isinstance(values, list):
		return []
	return [str(x or "").strip().lower() for x in values if str(x or "").strip()]


def report_family_intent_markers(family_id: str) -> List[str]:
	# Backward-compatible wrapper. These markers are transitional phrase-surface
	# hints only and should not be treated as canonical business semantics.
	return report_family_transitional_surface_markers(family_id)


def supported_ontology_concepts() -> List[str]:
	out: List[str] = []
	for spec in list_report_family_specs():
		family_id = str(spec.get("family_id") or "").strip()
		if not family_id:
			continue
		out.extend(report_family_ontology_concepts(family_id))
		for capability_id in report_family_capability_ids(family_id):
			out.extend(capability_ontology_concepts(capability_id))
	return list(dict.fromkeys([value for value in out if value]))


def report_family_ids_for_intent_class(intent_class_id: str) -> List[str]:
	target = str(intent_class_id or "").strip()
	if not target:
		return []
	out: List[str] = []
	for spec in list_report_family_specs():
		values = spec.get("supported_intent_classes")
		if not isinstance(values, list):
			continue
		if target in {str(x or "").strip() for x in values if str(x or "").strip()}:
			family_id = str(spec.get("family_id") or "").strip()
			if family_id:
				out.append(family_id)
	return list(dict.fromkeys(out))


def composite_read_renderer_id(plan_id: str) -> str:
	return str(get_composite_read_spec(plan_id).get("renderer_id") or "").strip()


def get_validation_profile(profile_id: str) -> Dict[str, Any]:
	rules = load_validation_rules().get("profiles")
	if not isinstance(rules, list):
		return {}
	target = str(profile_id or "").strip()
	for item in rules:
		if not isinstance(item, dict):
			continue
		if str(item.get("profile_id") or "").strip() == target:
			return dict(item)
	return {}


def semantic_validation_policy() -> Dict[str, Any]:
	value = load_validation_rules().get("semantic_validation")
	return dict(value) if isinstance(value, dict) else {}


def ambiguity_rules() -> List[Dict[str, Any]]:
	values = load_validation_rules().get("ambiguity_rules")
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def report_approved_followup_modes(report_name: str) -> List[str]:
	values = get_report_spec(report_name).get("approved_follow_up_modes")
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def capability_dimensions_for_report(report_name: str) -> List[str]:
	capability_ids = set(report_capability_ids(report_name))
	if not capability_ids:
		return []
	capabilities = load_capability_registry().get("capabilities")
	if not isinstance(capabilities, list):
		return []
	out: List[str] = []
	for item in capabilities:
		if not isinstance(item, dict):
			continue
		if str(item.get("capability_id") or "").strip() not in capability_ids:
			continue
		values = item.get("dimensions")
		if not isinstance(values, list):
			continue
		out.extend(str(x or "").strip() for x in values if str(x or "").strip())
	return list(dict.fromkeys(out))


def capability_metrics_for_report(report_name: str) -> List[str]:
	capability_ids = set(report_capability_ids(report_name))
	if not capability_ids:
		return []
	capabilities = load_capability_registry().get("capabilities")
	if not isinstance(capabilities, list):
		return []
	out: List[str] = []
	for item in capabilities:
		if not isinstance(item, dict):
			continue
		if str(item.get("capability_id") or "").strip() not in capability_ids:
			continue
		values = item.get("metrics")
		if not isinstance(values, list):
			continue
		out.extend(str(x or "").strip() for x in values if str(x or "").strip())
	return list(dict.fromkeys(out))


def report_sibling_capability_specs(report_name: str) -> List[Dict[str, Any]]:
	out: List[Dict[str, Any]] = []
	seen: set[str] = set()
	for capability_id in report_capability_ids(report_name):
		source_spec = get_capability_spec(capability_id)
		sibling_ids = source_spec.get("sibling_capabilities")
		if not isinstance(sibling_ids, list):
			continue
		for sibling_id in sibling_ids:
			sibling = get_capability_spec(str(sibling_id or "").strip())
			clean_id = str(sibling.get("capability_id") or "").strip()
			if not clean_id or clean_id in seen:
				continue
			out.append(sibling)
			seen.add(clean_id)
	return out


def resolve_target_report_for_capability(source_report_name: str, target_capability_id: str) -> str:
	target = get_capability_spec(target_capability_id)
	if not target:
		return ""
	source_name = str(source_report_name or "").strip().lower()
	if "summary" in source_name:
		value = str(target.get("summary_report_name") or "").strip()
		if value:
			return value
	if source_name and "summary" not in source_name:
		value = str(target.get("detail_report_name") or "").strip()
		if value:
			return value
	return str(target.get("default_report_name") or "").strip()


def report_supplemental_fields(report_name: str) -> List[Dict[str, str]]:
	values = get_report_spec(report_name).get("supplemental_fields")
	if not isinstance(values, list):
		return []
	out: List[Dict[str, str]] = []
	for item in values:
		if not isinstance(item, dict):
			continue
		fieldname = str(item.get("fieldname") or "").strip()
		label = str(item.get("label") or fieldname).strip()
		if fieldname and label:
			out.append({"fieldname": fieldname, "label": label})
	return out


def report_local_followup_adapter(report_name: str, mode: str) -> Dict[str, Any]:
	adapters = get_report_spec(report_name).get("local_followup_adapters")
	if not isinstance(adapters, dict):
		return {}
	value = adapters.get(str(mode or "").strip())
	return dict(value) if isinstance(value, dict) else {}


def resolve_followup_report_switch(requested_modes: List[str], source_report_name: str) -> Dict[str, Any]:
	source_name = str(source_report_name or "").strip()
	if not source_name:
		return {}
	requested = {str(mode or "").strip() for mode in requested_modes if str(mode or "").strip()}
	if not requested:
		return {}
	capabilities = load_capability_registry().get("capabilities")
	if not isinstance(capabilities, list):
		return {}
	source_capability_ids = set(report_capability_ids(source_name))
	if not source_capability_ids:
		return {}
	for capability in capabilities:
		if not isinstance(capability, dict):
			continue
		capability_id = str(capability.get("capability_id") or "").strip()
		if capability_id not in source_capability_ids:
			continue
		switches = capability.get("followup_report_switches")
		if not isinstance(switches, list):
			continue
		for item in switches:
			if not isinstance(item, dict):
				continue
			followup_mode = str(item.get("followup_mode") or "").strip()
			if followup_mode not in requested:
				continue
			from_reports = item.get("from_reports")
			if isinstance(from_reports, list):
				allowed_reports = {str(x or "").strip().lower() for x in from_reports if str(x or "").strip()}
				if allowed_reports and source_name.lower() not in allowed_reports:
					continue
			return {
				"capability_id": capability_id,
				"followup_mode": followup_mode,
				"target_report": str(item.get("target_report") or "").strip(),
				"requery_prompt_hint": str(item.get("requery_prompt_hint") or "").strip(),
			}
	return {}
