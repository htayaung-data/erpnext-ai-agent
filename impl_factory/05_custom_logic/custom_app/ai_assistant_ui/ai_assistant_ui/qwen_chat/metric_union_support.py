from __future__ import annotations

import re
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.metadata import (
	capability_default_report_name,
	capability_report_names,
	capability_semantic_tags,
	report_business_family_ids,
	report_capability_ids,
	report_defaultable_filters,
	report_family_capability_ids,
	report_semantic_tags,
	report_supported_metrics,
)
from ai_assistant_ui.qwen_chat.semantic_aliases import get_canonical_key


def artifact_metric_columns_available(
	artifact_payload: Dict[str, Any],
	requested_columns: List[str],
) -> bool:
	def _normalize_column_key(value: Any) -> str:
		return normalized_key_fallback(str(value or "").strip())

	def _collect_row_keys(value: Any) -> set[str]:
		keys: set[str] = set()
		if isinstance(value, list):
			for item in value:
				keys.update(_collect_row_keys(item))
			return keys
		if not isinstance(value, dict):
			return keys
		candidate_keys = {
			str(key or "").strip()
			for key in value.keys()
			if str(key or "").strip()
		}
		if candidate_keys:
			keys.update(candidate_keys)
		for item in value.values():
			if isinstance(item, (dict, list)):
				keys.update(_collect_row_keys(item))
		return keys

	if not isinstance(artifact_payload, dict) or not artifact_payload:
		return True
	requested = [str(value or "").strip() for value in (requested_columns or []) if str(value or "").strip()]
	if not requested:
		return True
	dimensions = artifact_payload.get("dimensions") if isinstance(artifact_payload.get("dimensions"), dict) else {}
	sections = artifact_payload.get("sections") if isinstance(artifact_payload.get("sections"), dict) else {}
	primary_metric_key = str(dimensions.get("requested_metric_key") or dimensions.get("primary_metric_key") or "").strip()
	available_metric_keys = {
		str(value or "").strip()
		for value in (dimensions.get("available_metric_keys") or [])
		if str(value or "").strip()
	}
	column_alias_map = (
		{
			_normalize_column_key(key): str(value or "").strip()
			for key, value in (dimensions.get("requested_column_alias_map") or {}).items()
			if _normalize_column_key(key) and str(value or "").strip()
		}
		if isinstance(dimensions.get("requested_column_alias_map"), dict)
		else {}
	)
	if primary_metric_key:
		available_metric_keys.add(primary_metric_key)
	row_keys = _collect_row_keys(sections)
	if not row_keys and not available_metric_keys:
		return True
	available_metric_keys_normalized = {
		_normalize_column_key(value)
		for value in available_metric_keys
		if _normalize_column_key(value)
	}
	row_keys_normalized = {
		_normalize_column_key(value)
		for value in row_keys
		if _normalize_column_key(value)
	}
	for column in requested:
		candidate_keys = {
			str(column or "").strip(),
			_normalize_column_key(column),
		}
		alias_target = column_alias_map.get(_normalize_column_key(column))
		if alias_target:
			candidate_keys.add(alias_target)
			candidate_keys.add(_normalize_column_key(alias_target))
		canonical_metric_key = get_canonical_key(column, dimension_or_metric="metric")
		if canonical_metric_key:
			candidate_keys.add(str(canonical_metric_key or "").strip())
			candidate_keys.add(_normalize_column_key(canonical_metric_key))
		if any(key in available_metric_keys or key in row_keys for key in candidate_keys if str(key or "").strip()):
			continue
		if any(key in available_metric_keys_normalized or key in row_keys_normalized for key in candidate_keys if str(key or "").strip()):
			continue
		return False
	return True


def normalized_key_fallback(value: str) -> str:
	clean = str(value or "").strip().lower()
	if not clean:
		return ""
	return re.sub(r"[^a-z0-9]+", "_", clean).strip("_")


def canonical_metric_keys_for_values(values: List[str], capability_id: str = "") -> List[str]:
	out: List[str] = []
	for value in values:
		canonical = get_canonical_key(
			value,
			capability_id=capability_id or None,
			dimension_or_metric="metric",
		)
		clean = str(canonical or normalized_key_fallback(value) or value or "").strip()
		if clean and clean not in out:
			out.append(clean)
	return out


def report_can_project_metric_union(report_name: str, required_metric_keys: List[str], capability_id: str) -> bool:
	required = [str(value or "").strip() for value in required_metric_keys if str(value or "").strip()]
	if not required:
		return True
	report_metric_keys = canonical_metric_keys_for_values(report_supported_metrics(report_name), capability_id=capability_id)
	if not set(required).issubset(set(report_metric_keys)):
		return False
	defaultable_fields = {
		str(item.get("fieldname") or "").strip()
		for item in report_defaultable_filters(report_name)
		if isinstance(item, dict) and str(item.get("fieldname") or "").strip()
	}
	if len(required) > 1 and "value_quantity" in defaultable_fields:
		return False
	return True


def metric_union_target_score(
	*,
	report_name: str,
	capability_id: str,
	source_report: str,
	current_capability_id: str,
	required_metric_keys: List[str],
) -> int:
	score = 0
	if report_name and source_report and report_name == source_report:
		score += 1000
	if capability_id and current_capability_id and capability_id == current_capability_id:
		score += 200
	default_report_name = capability_default_report_name(capability_id)
	if report_name and default_report_name and report_name == default_report_name:
		score += 40
	source_report_capability_ids = {
		str(value or "").strip()
		for value in report_capability_ids(source_report)
		if str(value or "").strip()
	}
	if capability_id and capability_id in source_report_capability_ids:
		score += 60
	required = {
		str(value or "").strip()
		for value in required_metric_keys
		if str(value or "").strip()
	}
	if required:
		candidate_metric_keys = {
			str(value or "").strip()
			for value in canonical_metric_keys_for_values(
				report_supported_metrics(report_name),
				capability_id=capability_id,
			)
			if str(value or "").strip()
		}
		score += len(required.intersection(candidate_metric_keys)) * 15
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
		overlap = len(source_tags.intersection(candidate_tags))
		union = len(source_tags.union(candidate_tags))
		score += overlap * 10
		if union:
			score += int((overlap / union) * 100)
	capability_tags = {
		str(value or "").strip()
		for value in capability_semantic_tags(capability_id)
		if str(value or "").strip()
	}
	if capability_tags:
		capability_overlap = len(capability_tags.intersection(candidate_tags))
		score += capability_overlap * 30
		missing_capability_tags = len(capability_tags.difference(candidate_tags))
		score -= missing_capability_tags * 35
	return score


def resolve_metric_union_requery_target(
	*,
	artifact_payload: Dict[str, Any],
	source_report: str,
	current_capability_id: str,
	required_metric_keys: List[str],
) -> tuple[str, str]:
	family_id = str(artifact_payload.get("family_id") or "").strip()
	candidate_families = [family_id] if family_id else report_business_family_ids(source_report)
	candidates: List[tuple[int, str, str]] = []
	if current_capability_id and report_can_project_metric_union(source_report, required_metric_keys, current_capability_id):
		candidates.append(
			(
				metric_union_target_score(
					report_name=source_report,
					capability_id=current_capability_id,
					source_report=source_report,
					current_capability_id=current_capability_id,
					required_metric_keys=required_metric_keys,
				),
				current_capability_id,
				source_report,
			)
		)
	for family_candidate in candidate_families:
		for capability_id in report_family_capability_ids(family_candidate):
			for report_name in capability_report_names(capability_id):
				if not report_can_project_metric_union(report_name, required_metric_keys, capability_id):
					continue
				candidates.append(
					(
						metric_union_target_score(
							report_name=report_name,
							capability_id=capability_id,
							source_report=source_report,
							current_capability_id=current_capability_id,
							required_metric_keys=required_metric_keys,
						),
						capability_id,
						report_name,
					)
				)
	if candidates:
		_best_score, best_capability_id, best_report = max(candidates, key=lambda item: item[0])
		if best_report:
			return best_capability_id, best_report
	return current_capability_id, ""
