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


def _artifact_column_alias_map(artifact_contract) -> Dict[str, str]:
	dimensions = artifact_contract.dimensions if isinstance(getattr(artifact_contract, "dimensions", None), dict) else {}
	values = dimensions.get("requested_column_alias_map")
	if not isinstance(values, dict):
		return {}
	out: Dict[str, str] = {}
	for key, value in values.items():
		alias_key = str(key or "").strip().lower().replace(" ", "_")
		target_value = str(value or "").strip().lower().replace(" ", "_")
		if alias_key and target_value:
			out[alias_key] = target_value
	return out


def _artifact_metric_label_map(artifact_contract) -> Dict[str, str]:
	dimensions = artifact_contract.dimensions if isinstance(getattr(artifact_contract, "dimensions", None), dict) else {}
	values = dimensions.get("metric_label_map")
	if not isinstance(values, dict):
		return {}
	out: Dict[str, str] = {}
	for key, value in values.items():
		metric_key = str(key or "").strip().lower().replace(" ", "_")
		metric_label = str(value or "").strip()
		if metric_key and metric_label:
			out[metric_key] = metric_label
	return out


def _normalize_requested_columns_for_artifact(
	artifact_contract,
	requested_columns: list[str],
) -> list[str]:
	alias_map = _artifact_column_alias_map(artifact_contract)
	out: list[str] = []
	for value in requested_columns:
		key = str(value or "").strip().lower().replace(" ", "_")
		if not key:
			continue
		out.append(alias_map.get(key, key))
	return list(dict.fromkeys(out))


def _requested_columns_are_explicit_selection(
	*,
	requested_columns: list[str],
	primary_metric_key: str,
) -> bool:
	requested = [value for value in requested_columns if value]
	if not requested:
		return False
	return len(requested) >= 2


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
	if _requested_columns_are_explicit_selection(
		requested_columns=requested,
		primary_metric_key=primary_metric_key,
	):
		selected = list(requested)
		if "entity" not in selected and "entity_code" not in selected and "document_name" not in selected:
			selected.insert(0, "entity")
		return list(dict.fromkeys(selected))
	selected = list(current or ["entity"])
	for value in requested:
		if value not in selected:
			selected.append(value)
	if primary_metric_key and primary_metric_key not in selected:
		insert_at = 1 if selected and selected[0] in {"entity", "entity_code", "document_name"} else len(selected)
		selected.insert(insert_at, primary_metric_key)
	if "entity" not in selected and "entity_code" not in selected and "document_name" not in selected:
		selected.insert(0, "entity")
	return list(dict.fromkeys(selected))


def _artifact_time_scope(artifact_payload: Dict[str, Any]) -> str:
	period = artifact_payload.get("period") if isinstance(artifact_payload.get("period"), dict) else {}
	dimensions = artifact_payload.get("dimensions") if isinstance(artifact_payload.get("dimensions"), dict) else {}
	filters = artifact_payload.get("filters") if isinstance(artifact_payload.get("filters"), dict) else {}
	return str(
		period.get("time_scope")
		or period.get("requested_time_scope")
		or dimensions.get("source_composite_time_scope")
		or filters.get("composite_time_scope")
		or ""
	).strip()


def _summary_total_metric_label(metric_label: str) -> str:
	label = str(metric_label or "").strip()
	if not label:
		return "Total Amount"
	if label.lower().startswith("total "):
		return label
	return f"Total {label}"


def _transaction_listing_rows_with_metric(
	rows: Any,
	*,
	primary_metric_key: str,
) -> list[Dict[str, Any]]:
	if not isinstance(rows, list):
		return []
	out: list[Dict[str, Any]] = []
	for row in rows:
		if not isinstance(row, dict):
			continue
		refined_row = dict(row)
		metric_values = dict(refined_row.get("metric_values")) if isinstance(refined_row.get("metric_values"), dict) else {}
		if primary_metric_key and primary_metric_key not in refined_row and primary_metric_key in metric_values:
			refined_row[primary_metric_key] = metric_values.get(primary_metric_key)
		out.append(refined_row)
	return out


def _refine_transaction_listing_payload(
	updated_payload: Dict[str, Any],
	*,
	primary_metric_key: str,
	primary_metric_label: str,
) -> None:
	sections = updated_payload.get("sections") if isinstance(updated_payload.get("sections"), dict) else {}
	metrics = updated_payload.get("metrics") if isinstance(updated_payload.get("metrics"), dict) else {}
	dimensions = updated_payload.get("dimensions") if isinstance(updated_payload.get("dimensions"), dict) else {}
	document_rows = _transaction_listing_rows_with_metric(
		sections.get("transaction_rows"),
		primary_metric_key=primary_metric_key,
	)
	if not document_rows:
		return
	sections = dict(sections)
	metrics = dict(metrics)
	sections["transaction_rows"] = document_rows
	total_amount = sum(float(row.get(primary_metric_key) or 0) for row in document_rows)
	total_quantity = sum(float(row.get("quantity") or 0) for row in document_rows)
	total_outstanding = sum(float(row.get("outstanding_amount") or 0) for row in document_rows)
	metrics["document_count"] = len(document_rows)
	metrics["total_amount"] = total_amount
	if any(float(row.get("quantity") or 0) for row in document_rows):
		metrics["quantity"] = total_quantity
	if any(float(row.get("outstanding_amount") or 0) for row in document_rows):
		metrics["outstanding_amount"] = total_outstanding
	requested_columns = {
		str(value or "").strip()
		for value in (dimensions.get("requested_columns") or [])
		if str(value or "").strip()
	}
	include_primary_total = bool(primary_metric_key) and (
		not requested_columns or primary_metric_key in requested_columns
	)
	summary = [{"label": "Document Count", "metric_key": "document_count", "value": len(document_rows)}]
	if "quantity" in metrics:
		summary.append({"label": "Total Quantity", "metric_key": "quantity", "value": total_quantity})
	if include_primary_total:
		summary.append(
			{
				"label": "Total Amount" if primary_metric_key == "grand_total" else _summary_total_metric_label(primary_metric_label),
				"metric_key": "total_amount",
				"amount": total_amount,
			}
		)
	if "outstanding_amount" in metrics:
		summary.append(
			{"label": "Outstanding Amount", "metric_key": "outstanding_amount", "amount": total_outstanding}
		)
	sections["summary"] = summary
	updated_payload["sections"] = sections
	updated_payload["metrics"] = metrics


def refine_local_family_artifact(
	*,
	request_id: str,
	artifact_payload: Dict[str, Any],
	target_limit: int = 0,
	sort_direction: str = "",
	target_metric: str = "",
	requested_columns: list[str] | None = None,
	requested_modes: list[str] | None = None,
) -> Dict[str, Any]:
	artifact_contract = _artifact_contract_from_payload(artifact_payload)
	if artifact_contract is None:
		return {}
	updated_payload = artifact_contract.to_payload()
	dimensions = updated_payload.get("dimensions") if isinstance(updated_payload.get("dimensions"), dict) else {}
	dimensions = dict(dimensions)
	modes = {
		str(value or "").strip()
		for value in (requested_modes or [])
		if str(value or "").strip()
	}
	primary_metric_key = str(target_metric or "").strip() or _artifact_primary_metric_key(artifact_contract)
	existing_columns = _artifact_requested_columns(artifact_contract, primary_metric_key)
	projection_mode = str(dimensions.get("requested_projection_mode") or "").strip()
	if int(max(0, target_limit or 0)) > 0:
		dimensions["requested_top_n"] = int(max(0, target_limit or 0))
	if str(sort_direction or "").strip() in {"asc", "desc"}:
		dimensions["requested_sort_direction"] = str(sort_direction or "").strip()
	if primary_metric_key:
		dimensions["requested_metric_key"] = primary_metric_key
		dimensions["primary_metric_key"] = primary_metric_key
		metric_label_map = _artifact_metric_label_map(artifact_contract)
		if metric_label_map.get(primary_metric_key):
			dimensions["primary_metric_label"] = metric_label_map.get(primary_metric_key)
		if str(updated_payload.get("family_id") or "").strip() == "transaction_listing":
			_refine_transaction_listing_payload(
				updated_payload,
				primary_metric_key=primary_metric_key,
				primary_metric_label=str(dimensions.get("primary_metric_label") or "").strip(),
			)
	if isinstance(requested_columns, list):
		clean_columns = [str(value or "").strip() for value in requested_columns if str(value or "").strip()]
		if clean_columns:
			clean_columns = _normalize_requested_columns_for_artifact(
				artifact_contract,
				clean_columns,
			)
			dimensions["requested_columns"] = _refined_requested_columns(
				existing_columns=existing_columns,
				requested_columns=clean_columns,
				primary_metric_key=primary_metric_key,
			)
			projection_mode = (
				"explicit_selection"
				if _requested_columns_are_explicit_selection(
					requested_columns=clean_columns,
					primary_metric_key=primary_metric_key,
				)
				else "default"
			)
			dimensions["has_explicit_projection_request"] = True
	elif "column_refinement" in modes:
		dimensions["requested_columns"] = existing_columns
	elif str(target_metric or "").strip():
		dimensions["has_explicit_projection_request"] = True
	refined_requested_columns = [
		str(value or "").strip()
		for value in (dimensions.get("requested_columns") or [])
		if str(value or "").strip()
	]
	if str(dimensions.get("source_composite_family_id") or "").strip():
		if primary_metric_key:
			dimensions["source_composite_primary_metric_id"] = primary_metric_key
		dimensions["source_composite_secondary_metric_ids"] = [
			value
			for value in refined_requested_columns
			if value not in {"entity", "entity_code", primary_metric_key}
		]
	if projection_mode:
		dimensions["requested_projection_mode"] = projection_mode
	updated_payload["request_id"] = str(request_id or updated_payload.get("request_id") or "").strip()
	updated_payload["dimensions"] = dimensions
	return updated_payload


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
	- ranking_analytics, product_profitability, trend_analytics, financial_statement,
	  aging, inventory_snapshot, master_data_directory, transaction_listing
	- sort_or_limit, metric_refinement, column_refinement
	- presentation_transform (million)
	"""
	if not isinstance(artifact_payload, dict) or not artifact_payload:
		return False
	family_id = str(artifact_payload.get("family_id") or "").strip()
	if family_id not in {
		"ranking_analytics",
		"product_profitability",
		"trend_analytics",
		"financial_statement",
		"aging",
		"inventory_snapshot",
		"master_data_directory",
		"transaction_listing",
	}:
		return False
	modes = {
		str(value or "").strip()
		for value in (requested_modes or [])
		if str(value or "").strip()
	}
	requested_time_scope = str(requested_time_scope or "").strip()
	if requested_time_scope:
		# Local family follow-ups may carry the artifact's preserved time scope,
		# but explicit scope changes must re-enter governed requery.
		if "time_scope_restatement" in modes:
			return False
		if requested_time_scope != _artifact_time_scope(artifact_payload):
			return False
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
	updated_artifact_payload = refine_local_family_artifact(
		request_id=request_id,
		artifact_payload=artifact_payload,
		target_limit=target_limit,
		sort_direction=sort_direction,
		target_metric=target_metric,
		requested_columns=requested_columns,
		requested_modes=requested_modes,
	)
	artifact_contract = _artifact_contract_from_payload(updated_artifact_payload or artifact_payload)
	if artifact_contract is None:
		return {}
	overrides: Dict[str, Any] = {}
	modes = {
		str(value or "").strip()
		for value in (requested_modes or [])
		if str(value or "").strip()
	}
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
