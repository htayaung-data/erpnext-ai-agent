from __future__ import annotations

from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.contracts import (
	build_artifact_enrichment_compatibility_contract,
	clone_followup_resolution,
)
from ai_assistant_ui.qwen_chat.metadata import report_capability_ids
from ai_assistant_ui.qwen_chat.metric_union_support import (
	artifact_metric_columns_available,
	canonical_metric_keys_for_values,
	resolve_metric_union_requery_target,
)


def artifact_rank_row_count(artifact_payload: Dict[str, Any], grounded_turn: Dict[str, Any]) -> int:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	sections = artifact.get("sections") if isinstance(artifact.get("sections"), dict) else {}
	for key in ("ranked_rows", "rows", "series", "document_rows"):
		rows = sections.get(key)
		if isinstance(rows, list) and rows:
			return len(rows)
	turn = grounded_turn if isinstance(grounded_turn, dict) else {}
	table_rows = turn.get("table_rows")
	if isinstance(table_rows, list) and table_rows:
		return len(table_rows)
	try:
		return int(max(0, turn.get("row_count") or 0))
	except Exception:
		return 0


def authoritative_continuation_resolution(
	*,
	request_id: str,
	followup_resolution,
	continuation_contract,
	artifact_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any],
):
	if continuation_contract is None or not bool(getattr(continuation_contract, "preserve_grounded_context", False)):
		return followup_resolution
	requested_modes = {
		str(value or "").strip()
		for value in (getattr(followup_resolution, "requested_modes", []) or [])
		if str(value or "").strip()
	}
	source_family_id = str(getattr(continuation_contract, "source_family_id", "") or "").strip()
	source_composite_family_id = str(getattr(continuation_contract, "source_composite_family_id", "") or "").strip()
	source_capability_id = str(getattr(continuation_contract, "source_capability_id", "") or "").strip()
	source_report = str(getattr(continuation_contract, "source_report", "") or "").strip()
	current_row_count = artifact_rank_row_count(artifact_payload, grounded_turn)
	if current_row_count <= 0:
		current_row_count = int(max(0, getattr(continuation_contract, "source_row_count", 0) or 0))
	target_dimension = str(getattr(followup_resolution, "target_dimension", "") or "").strip()
	target_metric = str(getattr(followup_resolution, "target_metric", "") or "").strip()
	requested_columns = [
		str(value or "").strip()
		for value in (getattr(followup_resolution, "requested_columns", []) or [])
		if str(value or "").strip()
	]
	local_metric_columns = list(requested_columns)
	if target_metric and target_metric not in local_metric_columns:
		local_metric_columns.append(target_metric)
	target_limit = int(max(0, getattr(followup_resolution, "target_limit", 0) or 0))
	sort_direction = str(getattr(followup_resolution, "sort_direction", "") or "").strip()
	requested_time_scope = str(getattr(followup_resolution, "requested_time_scope", "") or "").strip()
	preserve_rank_membership = bool(getattr(continuation_contract, "preserve_rank_membership", False))
	preserve_rank_order = bool(getattr(continuation_contract, "preserve_rank_order", False))
	if source_family_id != "ranking_analytics":
		preserve_rank_membership = False
		preserve_rank_order = False

	if not target_dimension:
		target_dimension = str(
			getattr(continuation_contract, "preserved_dimension", "")
			or getattr(continuation_contract, "source_dimension", "")
			or ""
		).strip()
	if not target_metric:
		target_metric = str(
			getattr(continuation_contract, "preserved_metric_key", "")
			or getattr(continuation_contract, "source_metric_key", "")
			or ""
		).strip()
	if not requested_columns and bool(getattr(continuation_contract, "preserve_projection_shape", False)):
		requested_columns = [
			str(value or "").strip()
			for value in (
				getattr(continuation_contract, "preserved_requested_columns", [])
				or getattr(continuation_contract, "source_requested_columns", [])
				or []
			)
			if str(value or "").strip()
		]
	if not target_limit and preserve_rank_membership:
		target_limit = int(
			max(
				0,
				getattr(continuation_contract, "preserved_limit", 0)
				or getattr(continuation_contract, "source_limit", 0)
				or 0,
			)
		)
	if not sort_direction and preserve_rank_order:
		sort_direction = str(
			getattr(continuation_contract, "preserved_sort_direction", "")
			or getattr(continuation_contract, "source_sort_direction", "")
			or ""
		).strip()
	if not requested_time_scope:
		requested_time_scope = str(
			getattr(continuation_contract, "preserved_time_scope", "")
			or getattr(continuation_contract, "source_time_scope", "")
			or ""
		).strip()
	source_time_scope = str(
		getattr(continuation_contract, "preserved_time_scope", "")
		or getattr(continuation_contract, "source_time_scope", "")
		or ""
	).strip()

	mode = str(getattr(followup_resolution, "mode", "") or "").strip()
	if (
		(source_family_id == "ranking_analytics" or source_composite_family_id)
		and requested_modes.issubset({"column_refinement", "metric_refinement"})
		and local_metric_columns
		and artifact_metric_columns_available(artifact_payload, local_metric_columns)
	):
		return clone_followup_resolution(
			followup_resolution,
			request_id=request_id,
			mode=mode or "local_grounded_transform",
			target_dimension=target_dimension,
			target_limit=target_limit,
			sort_direction=sort_direction,
			target_metric=target_metric,
			requested_columns=requested_columns,
			requested_time_scope=requested_time_scope,
			depends_on_grounded_turn=True,
			self_contained=False,
			reason=(
				"Composite column refinements stay local when the grounded artifact already exposes "
				"the requested governed columns."
				if source_composite_family_id
				else "Ranking column refinements stay local when the grounded artifact already exposes the requested governed columns."
			),
		)
	if source_composite_family_id and requested_modes.intersection(
		{"sort_or_limit", "metric_refinement", "column_refinement", "time_scope_restatement"}
	):
		return clone_followup_resolution(
			followup_resolution,
			request_id=request_id,
			mode="capability_requery",
			target_dimension=target_dimension,
			target_limit=target_limit,
			sort_direction=sort_direction,
			target_metric=target_metric,
			requested_columns=requested_columns,
			requested_time_scope=requested_time_scope,
			target_capability_id=source_capability_id,
			target_report=source_report,
			depends_on_grounded_turn=True,
			self_contained=False,
			reason=(
				"Composite ranking follow-ups that change governed scope, ranking depth, or period "
				"must re-enter the preserved governed composite family runtime."
			),
		)
	if source_family_id == "ranking_analytics" and requested_modes.intersection({"sort_or_limit", "metric_refinement", "column_refinement"}):
		return clone_followup_resolution(
			followup_resolution,
			request_id=request_id,
			mode="capability_requery",
			target_dimension=target_dimension,
			target_limit=target_limit,
			sort_direction=sort_direction,
			target_metric=target_metric,
			requested_columns=requested_columns,
			requested_time_scope=requested_time_scope,
			target_capability_id=source_capability_id,
			target_report=source_report,
			depends_on_grounded_turn=True,
			self_contained=False,
			reason="Ranking follow-up transforms are governed through continuation requery so scope and metric stay anchored to the prior artifact.",
		)
	if (
		mode in {"local_grounded_transform", "grounded_follow_up"}
		and requested_time_scope
		and requested_time_scope != source_time_scope
	):
		return clone_followup_resolution(
			followup_resolution,
			request_id=request_id,
			mode="capability_requery",
			target_dimension=target_dimension,
			target_limit=target_limit,
			sort_direction=sort_direction,
			target_metric=target_metric,
			requested_columns=requested_columns,
			requested_time_scope=requested_time_scope,
			target_capability_id=source_capability_id,
			target_report=source_report,
			depends_on_grounded_turn=True,
			self_contained=False,
			reason="The requested time scope changes the governed data window and requires requery against the preserved capability.",
		)
	if (
		mode in {"local_grounded_transform", "grounded_follow_up"}
		and "sort_or_limit" in requested_modes
		and target_limit > 0
		and current_row_count > 0
		and target_limit > current_row_count
	):
		return clone_followup_resolution(
			followup_resolution,
			request_id=request_id,
			mode="capability_requery",
			target_dimension=target_dimension,
			target_limit=target_limit,
			sort_direction=sort_direction,
			target_metric=target_metric,
			requested_columns=requested_columns,
			requested_time_scope=requested_time_scope,
			target_capability_id=str(getattr(continuation_contract, "source_capability_id", "") or "").strip(),
			target_report=str(getattr(continuation_contract, "source_report", "") or "").strip(),
			depends_on_grounded_turn=True,
			self_contained=False,
			reason="The requested continuation scope exceeds the current artifact and requires governed requery with preserved context.",
		)

	return clone_followup_resolution(
		followup_resolution,
		request_id=request_id,
		mode=mode,
		target_dimension=target_dimension,
		target_limit=target_limit,
		sort_direction=sort_direction,
		target_metric=target_metric,
		requested_columns=requested_columns,
		requested_time_scope=requested_time_scope,
	)


def requery_resolution_for_unsupported_local_columns(
	*,
	request_id: str,
	followup_resolution,
	artifact_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any],
	continuation_contract=None,
) -> tuple[Any | None, Any | None]:
	requested_columns = [
		str(value or "").strip()
		for value in (getattr(followup_resolution, "requested_columns", []) or [])
		if str(value or "").strip()
	]
	requested_modes = {
		str(value or "").strip()
		for value in (getattr(followup_resolution, "requested_modes", []) or [])
		if str(value or "").strip()
	}
	target_metric = str(getattr(followup_resolution, "target_metric", "") or "").strip()
	columns_to_validate = list(requested_columns)
	if target_metric and target_metric not in columns_to_validate:
		columns_to_validate.append(target_metric)
	if not requested_modes.intersection({"column_refinement", "metric_refinement"}):
		return None, None
	if not columns_to_validate:
		return None, None
	if artifact_metric_columns_available(artifact_payload, columns_to_validate):
		return None, None
	artifact_dimensions = artifact_payload.get("dimensions") if isinstance(artifact_payload.get("dimensions"), dict) else {}
	contract_preserved_dimension = str(getattr(continuation_contract, "preserved_dimension", "") or "").strip()
	contract_source_dimension = str(getattr(continuation_contract, "source_dimension", "") or "").strip()
	contract_preserved_metric = str(getattr(continuation_contract, "preserved_metric_key", "") or "").strip()
	contract_source_metric = str(getattr(continuation_contract, "source_metric_key", "") or "").strip()
	contract_source_report = str(getattr(continuation_contract, "source_report", "") or "").strip()
	contract_source_capability = str(getattr(continuation_contract, "source_capability_id", "") or "").strip()
	contract_preserved_limit = int(max(0, getattr(continuation_contract, "preserved_limit", 0) or 0))
	contract_source_limit = int(max(0, getattr(continuation_contract, "source_limit", 0) or 0))
	fallback_dimension = str(
		getattr(followup_resolution, "target_dimension", "")
		or contract_preserved_dimension
		or contract_source_dimension
		or artifact_dimensions.get("entity_dimension")
		or ""
	).strip()
	fallback_limit = int(max(0, getattr(followup_resolution, "target_limit", 0) or 0))
	if not fallback_limit:
		try:
			fallback_limit = int(
				max(
					0,
					contract_preserved_limit
					or contract_source_limit
					or artifact_dimensions.get("requested_top_n")
					or 0,
				)
			)
		except Exception:
			fallback_limit = 0
	fallback_metric = str(
		target_metric
		or contract_preserved_metric
		or contract_source_metric
		or artifact_dimensions.get("requested_metric_key")
		or artifact_dimensions.get("primary_metric_key")
		or ""
	).strip()
	fallback_report = str(
		contract_source_report
		or (grounded_turn or {}).get("source_name")
		or ""
	).strip()
	fallback_capability_id = str(
		getattr(followup_resolution, "target_capability_id", "")
		or contract_source_capability
		or ""
	).strip()
	if not fallback_capability_id and fallback_report:
		fallback_capability_id = str((report_capability_ids(fallback_report) or [""])[0] or "").strip()
	required_metric_keys = canonical_metric_keys_for_values(
		[
			target_metric,
			str(artifact_dimensions.get("requested_metric_key") or "").strip(),
			str(artifact_dimensions.get("primary_metric_key") or "").strip(),
			*columns_to_validate,
		],
		capability_id=fallback_capability_id,
	)
	enrichment_contract = build_artifact_enrichment_compatibility_contract(
		request_id=request_id,
		followup_resolution=followup_resolution,
		artifact_payload=artifact_payload,
		grounded_turn=grounded_turn,
		continuation_contract=continuation_contract,
		required_metric_keys=required_metric_keys,
	)
	if not bool(getattr(enrichment_contract, "compatible", False)):
		return None, enrichment_contract
	selected_capability_id, selected_report = resolve_metric_union_requery_target(
		artifact_payload=artifact_payload,
		source_report=str(getattr(enrichment_contract, "target_report", "") or fallback_report).strip(),
		current_capability_id=str(getattr(enrichment_contract, "target_capability_id", "") or fallback_capability_id).strip(),
		required_metric_keys=required_metric_keys,
	)
	return clone_followup_resolution(
		followup_resolution,
		request_id=request_id,
		mode="capability_requery",
		target_dimension=fallback_dimension,
		target_limit=fallback_limit,
		target_metric=fallback_metric,
		requested_columns=requested_columns,
		target_capability_id=str(getattr(enrichment_contract, "target_capability_id", "") or selected_capability_id).strip(),
		target_report=str(getattr(enrichment_contract, "target_report", "") or selected_report).strip(),
		depends_on_grounded_turn=True,
		self_contained=False,
		reason=str(getattr(enrichment_contract, "reason", "") or "").strip()
		or "The requested columns or metric are not populated in the current grounded artifact and need a governed requery.",
	), enrichment_contract
