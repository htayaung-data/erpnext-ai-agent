from __future__ import annotations

from typing import Any, Dict

from ai_assistant_ui.qwen_chat.contracts import build_normalized_family_artifact_contract
from ai_assistant_ui.qwen_chat.family_rendering import render_normalized_family_response


def _artifact_contract_from_payload(payload: Dict[str, Any]):
	if not isinstance(payload, dict) or not payload:
		return None
	family_id = str(payload.get("family_id") or "").strip()
	if not family_id:
		return None
	return build_normalized_family_artifact_contract(
		request_id=str(payload.get("request_id") or "").strip(),
		family_id=family_id,
		artifact_type=str(payload.get("artifact_type") or "normalized_family_artifact").strip(),
		source_reports=payload.get("source_reports") if isinstance(payload.get("source_reports"), list) else [],
		period=payload.get("period") if isinstance(payload.get("period"), dict) else {},
		filters=payload.get("filters") if isinstance(payload.get("filters"), dict) else {},
		dimensions=payload.get("dimensions") if isinstance(payload.get("dimensions"), dict) else {},
		metrics=payload.get("metrics") if isinstance(payload.get("metrics"), dict) else {},
		sections=payload.get("sections") if isinstance(payload.get("sections"), dict) else {},
		warnings=payload.get("warnings") if isinstance(payload.get("warnings"), list) else [],
	)


def _clean_columns(values: Any) -> list[str]:
	if not isinstance(values, list):
		return []
	return [str(value or "").strip() for value in values if str(value or "").strip()]


def _artifact_primary_metric_key(artifact_contract) -> str:
	dimensions = artifact_contract.dimensions if isinstance(getattr(artifact_contract, "dimensions", None), dict) else {}
	return str(dimensions.get("requested_metric_key") or dimensions.get("primary_metric_key") or "").strip()


def _artifact_requested_columns(artifact_contract, primary_metric_key: str) -> list[str]:
	dimensions = artifact_contract.dimensions if isinstance(getattr(artifact_contract, "dimensions", None), dict) else {}
	stored_columns = _clean_columns(dimensions.get("requested_columns"))
	if stored_columns:
		return stored_columns
	if primary_metric_key:
		return ["entity", primary_metric_key]
	return ["entity"]


def _refined_requested_columns(
	*,
	existing_columns: list[str],
	requested_columns: list[str],
	primary_metric_key: str,
) -> list[str]:
	current = [value for value in existing_columns if value]
	requested = [value for value in requested_columns if value]
	if not requested:
		return current
	requested_set = set(requested)
	explicit_selection = len(requested) >= 2 and bool(
		requested_set.intersection({"entity", "entity_code", primary_metric_key})
	)
	if explicit_selection:
		selected = list(requested)
		if "entity" not in selected and "entity_code" not in selected:
			selected.insert(0, "entity")
		return list(dict.fromkeys(selected))
	selected = list(current or ["entity"])
	for value in requested:
		if value not in selected:
			selected.append(value)
	if primary_metric_key and primary_metric_key not in selected:
		insert_at = 1 if selected and selected[0] in {"entity", "entity_code"} else len(selected)
		selected.insert(insert_at, primary_metric_key)
	if "entity" not in selected and "entity_code" not in selected:
		selected.insert(0, "entity")
	return list(dict.fromkeys(selected))


def supports_local_family_followup(
	artifact_payload: Dict[str, Any],
	*,
	target_limit: int = 0,
	target_metric: str = "",
	requested_columns: list[str] | None = None,
	requested_time_scope: str = "",
	requested_modes: list[str] | None = None,
	show_million: bool = False,
) -> bool:
	"""
	Check if family follow-up can be handled locally.
	
	Supports:
	- ranking_analytics, product_profitability, trend_analytics, financial_statement, aging, inventory_snapshot
	- sort_or_limit, metric_refinement, column_refinement
	- presentation_transform (million)
	"""
	if not isinstance(artifact_payload, dict) or not artifact_payload:
		return False
	family_id = str(artifact_payload.get("family_id") or "").strip()
	if family_id not in {"ranking_analytics", "product_profitability", "trend_analytics", "financial_statement", "aging", "inventory_snapshot"}:
		return False
	if str(requested_time_scope or "").strip():
		return False
	modes = {
		str(value or "").strip()
		for value in (requested_modes or [])
		if str(value or "").strip()
	}
	supported_modes = {"sort_or_limit", "metric_refinement", "column_refinement", "presentation_transform"}
	return bool(
		int(max(0, target_limit or 0))
		or str(target_metric or "").strip()
		or list(requested_columns or [])
		or modes.intersection(supported_modes)
		or show_million
	)


def render_local_family_followup(
	*,
	request_id: str,
	artifact_payload: Dict[str, Any],
	target_limit: int = 0,
	sort_direction: str = "",
	target_metric: str = "",
	requested_columns: list[str] | None = None,
	requested_modes: list[str] | None = None,
	show_million: bool = False,
) -> Dict[str, Any]:
	"""
	Render family follow-up with support for all transformation types.
	
	Handles:
	- top_n changes
	- metric changes
	- column refinement
	- presentation_transform (million)
	"""
	artifact_contract = _artifact_contract_from_payload(artifact_payload)
	if artifact_contract is None:
		return {}
	overrides: Dict[str, Any] = {}
	clean_columns: list[str] = []
	modes = {
		str(value or "").strip()
		for value in (requested_modes or [])
		if str(value or "").strip()
	}
	primary_metric_key = str(target_metric or "").strip() or _artifact_primary_metric_key(artifact_contract)
	existing_columns = _artifact_requested_columns(artifact_contract, primary_metric_key)
	if int(max(0, target_limit or 0)) > 0:
		overrides["top_n"] = int(max(0, target_limit or 0))
	if str(sort_direction or "").strip() in {"asc", "desc"}:
		overrides["sort_direction"] = str(sort_direction or "").strip()
	if str(target_metric or "").strip():
		overrides["metric_key"] = str(target_metric or "").strip()
	if isinstance(requested_columns, list):
		clean_columns = [str(value or "").strip() for value in requested_columns if str(value or "").strip()]
		if clean_columns:
			overrides["requested_columns"] = _refined_requested_columns(
				existing_columns=existing_columns,
				requested_columns=clean_columns,
				primary_metric_key=primary_metric_key,
			)
	elif "column_refinement" in modes:
		overrides["requested_columns"] = existing_columns
	# Handle presentation_transform (million)
	if show_million or "presentation_transform" in modes:
		overrides["show_million"] = True
	render_outcome = render_normalized_family_response(
		request_id=request_id,
		artifact_contract=artifact_contract,
		response_overrides=overrides,
	)
	if render_outcome.contract is None:
		return {}
	return render_outcome.contract.to_payload()
