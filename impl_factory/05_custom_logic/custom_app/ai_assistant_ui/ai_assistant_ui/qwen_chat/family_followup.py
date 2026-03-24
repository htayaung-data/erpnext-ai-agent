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
	clean_columns = []
	modes = {
		str(value or "").strip()
		for value in (requested_modes or [])
		if str(value or "").strip()
	}
	if int(max(0, target_limit or 0)) > 0:
		overrides["top_n"] = int(max(0, target_limit or 0))
	if str(target_metric or "").strip():
		overrides["metric_key"] = str(target_metric or "").strip()
	if isinstance(requested_columns, list):
		clean_columns = [str(value or "").strip() for value in requested_columns if str(value or "").strip()]
		if clean_columns:
			overrides["requested_columns"] = clean_columns
	if "metric_key" not in overrides and "amount" in clean_columns:
		overrides["metric_key"] = "amount"
	if "metric_key" not in overrides and modes.intersection({"metric_refinement", "column_refinement"}):
		overrides["metric_key"] = "amount"
	if "requested_columns" not in overrides and "metric_key" in overrides and str(overrides.get("metric_key") or "").strip() == "amount":
		overrides["requested_columns"] = ["entity", "amount"]
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
