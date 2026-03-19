from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Set


_METADATA_DIR = Path(os.getenv("QWEN_ENTERPRISE_METADATA_DIR", "/app/metadata"))
_REPORT_REGISTRY_PATH = _METADATA_DIR / "report_registry.json"
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
def load_capability_registry() -> Dict[str, Any]:
	return _load_json(_CAPABILITY_REGISTRY_PATH)


@lru_cache(maxsize=1)
def load_validation_rules() -> Dict[str, Any]:
	return _load_json(_VALIDATION_RULES_PATH)


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


def report_validation_profile(report_name: str) -> str:
	return str(get_report_spec(report_name).get("validation_profile") or "").strip()


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
