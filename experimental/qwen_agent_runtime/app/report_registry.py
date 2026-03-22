from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Set


_METADATA_DIR = Path(os.getenv("QWEN_ENTERPRISE_METADATA_DIR", "/app/metadata"))
_REPORT_REGISTRY_PATH = _METADATA_DIR / "report_registry.json"
_REPORT_FAMILY_REGISTRY_PATH = _METADATA_DIR / "report_family_registry.json"
_CAPABILITY_REGISTRY_PATH = _METADATA_DIR / "capability_registry.json"
_VALIDATION_RULES_PATH = _METADATA_DIR / "validation_rules.json"


@lru_cache(maxsize=1)
def _load_json(path: Path) -> Dict[str, Any]:
	with path.open("r", encoding="utf-8") as f:
		obj = json.load(f)
	return obj if isinstance(obj, dict) else {}


@lru_cache(maxsize=1)
def load_report_registry() -> Dict[str, Any]:
	return _load_json(_REPORT_REGISTRY_PATH)


@lru_cache(maxsize=1)
def load_report_family_registry() -> Dict[str, Any]:
	return _load_json(_REPORT_FAMILY_REGISTRY_PATH)


@lru_cache(maxsize=1)
def load_capability_registry() -> Dict[str, Any]:
	return _load_json(_CAPABILITY_REGISTRY_PATH)


@lru_cache(maxsize=1)
def load_validation_rules() -> Dict[str, Any]:
	return _load_json(_VALIDATION_RULES_PATH)


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


def _reports_by_name() -> Dict[str, Dict[str, Any]]:
	registry = load_report_registry()
	reports = registry.get("reports")
	out: Dict[str, Dict[str, Any]] = {}
	if not isinstance(reports, list):
		return out
	for item in reports:
		if not isinstance(item, dict):
			continue
		name = str(item.get("report_name") or "").strip()
		if name:
			out[name.lower()] = item
	return out


def get_report_spec(report_name: str) -> Dict[str, Any]:
	return dict(_reports_by_name().get(str(report_name or "").strip().lower()) or {})


def approved_report_names() -> Set[str]:
	return {spec.get("report_name") for spec in _reports_by_name().values() if str(spec.get("report_name") or "").strip()}


def approved_modules() -> Set[str]:
	return {str(spec.get("module") or "").strip() for spec in _reports_by_name().values() if str(spec.get("module") or "").strip()}


def is_report_approved(report_name: str) -> bool:
	return bool(get_report_spec(report_name))


def report_family(report_name: str) -> str:
	return str(get_report_spec(report_name).get("family") or "").strip()


def report_capability_ids(report_name: str) -> List[str]:
	spec = get_report_spec(report_name)
	values = spec.get("capability_ids")
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def report_supported_intent_classes(report_name: str) -> List[str]:
	spec = get_report_spec(report_name)
	values = spec.get("supported_intent_classes")
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def report_semantic_tags(report_name: str) -> List[str]:
	spec = get_report_spec(report_name)
	values = spec.get("semantic_tags")
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def report_defaultable_filters(report_name: str) -> List[Dict[str, Any]]:
	spec = get_report_spec(report_name)
	values = spec.get("defaultable_filters")
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


def report_family_supported_intent_classes(family_id: str) -> List[str]:
	spec = get_report_family_spec(family_id)
	values = spec.get("supported_intent_classes")
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def report_family_canonical_metrics(family_id: str) -> List[str]:
	spec = get_report_family_spec(family_id)
	values = spec.get("canonical_metrics")
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def report_family_canonical_dimensions(family_id: str) -> List[str]:
	spec = get_report_family_spec(family_id)
	values = spec.get("canonical_dimensions")
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
	spec = get_report_family_spec(family_id)
	values = spec.get("semantic_tags")
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def report_family_composite_allowed(family_id: str) -> bool:
	return bool(get_report_family_spec(family_id).get("composite_allowed"))


def report_family_report_names(family_id: str) -> List[str]:
	spec = get_report_family_spec(family_id)
	values = spec.get("report_names")
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def report_family_capability_ids(family_id: str) -> List[str]:
	spec = get_report_family_spec(family_id)
	values = spec.get("capability_ids")
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def report_family_routing_hints(family_id: str) -> Dict[str, Any]:
	value = get_report_family_spec(family_id).get("routing_hints")
	return dict(value) if isinstance(value, dict) else {}


def get_validation_profile(profile_id: str) -> Dict[str, Any]:
	rules = load_validation_rules().get("profiles")
	if not isinstance(rules, list):
		return {}
	for item in rules:
		if not isinstance(item, dict):
			continue
		if str(item.get("profile_id") or "").strip() == str(profile_id or "").strip():
			return dict(item)
	return {}


def validate_report_filters(report_name: str, filters: Any) -> List[str]:
	spec = get_report_spec(report_name)
	if not spec:
		return [f"Report is not in the approved registry: {report_name}"]

	if not isinstance(filters, dict):
		return [f"Filters must be an object for report: {report_name}"]

	errors: List[str] = []
	for key in spec.get("required_filters") or []:
		value = filters.get(key)
		if value is None:
			errors.append(f"Missing required filter `{key}` for report `{report_name}`.")
			continue
		if isinstance(value, str) and not value.strip():
			errors.append(f"Empty required filter `{key}` for report `{report_name}`.")
	return errors
