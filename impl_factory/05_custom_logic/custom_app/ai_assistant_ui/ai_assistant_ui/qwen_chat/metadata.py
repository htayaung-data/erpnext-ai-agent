from __future__ import annotations

import json
import os
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


def load_business_ontology() -> Dict[str, Any]:
	return _load_json("business_ontology.json")


def load_capability_registry() -> Dict[str, Any]:
	return _load_json("capability_registry.json")


def load_report_registry() -> Dict[str, Any]:
	return _load_json("report_registry.json")


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


def ontology_followup_aliases(mode: str, language: str = "en") -> List[str]:
	entries = load_business_ontology().get("follow_up_classes")
	if not isinstance(entries, list):
		return []
	for item in entries:
		if not isinstance(item, dict):
			continue
		if str(item.get("mode") or "").strip() != str(mode or "").strip():
			continue
		aliases = item.get("aliases")
		if not isinstance(aliases, dict):
			return []
		values = aliases.get(language)
		if not isinstance(values, list):
			return []
		return [str(x or "").strip().lower() for x in values if str(x or "").strip()]
	return []


def ontology_detect_followup_modes(message: str, language: str = "en") -> List[str]:
	text = " ".join(str(message or "").strip().lower().split())
	if not text:
		return []
	entries = load_business_ontology().get("follow_up_classes")
	if not isinstance(entries, list):
		return []
	out: List[str] = []
	for item in entries:
		if not isinstance(item, dict):
			continue
		mode = str(item.get("mode") or "").strip()
		if not mode:
			continue
		aliases = item.get("aliases")
		if not isinstance(aliases, dict):
			continue
		values = aliases.get(language)
		if not isinstance(values, list):
			continue
		if any(str(alias or "").strip().lower() in text for alias in values if str(alias or "").strip()):
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
		aliases = item.get("aliases")
		if not isinstance(aliases, dict):
			continue
		values = aliases.get(language)
		if not isinstance(values, list):
			continue
		out.extend(str(x or "").strip().lower() for x in values if str(x or "").strip())
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


def report_capability_ids(report_name: str) -> List[str]:
	spec = get_report_spec(report_name)
	values = spec.get("capability_ids")
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
