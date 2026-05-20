from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from ai_assistant_ui.qwen_chat.authorized_emission import (
	ANSWER_TYPE_VISIBLE_CONTEXT,
	emit_authorized_assistant_answer,
)
from ai_assistant_ui.qwen_chat.contracts import ExecutionPath
from ai_assistant_ui.qwen_chat.runtime_metadata_contract import (
	LANE_CLASS_DETERMINISTIC_VISIBLE_CONTEXT,
	ROLE_DETERMINISTIC,
	build_runtime_metadata_envelope,
)


def _local_followup_metadata_envelope(*, answer_mode: str) -> Dict[str, Any]:
	return build_runtime_metadata_envelope(
		lane_id="local_followup_transform",
		lane_class=LANE_CLASS_DETERMINISTIC_VISIBLE_CONTEXT,
		model_role=ROLE_DETERMINISTIC,
		model_name="none",
		fallback_used=False,
		fallback_reason="",
		role_compliance="compliant",
		authority_source="frontdoor_composite",
		evidence_scope="grounded_visible_context_transform",
		answer_mode=answer_mode,
		preflight_status="passed",
		metadata_source="local_followup_transform_authorized_emission",
	)


def _payload_from_tool_message(value: Any) -> Dict[str, Any]:
	if isinstance(value, dict):
		return dict(value)
	try:
		decoded = json.loads(str(value or ""))
	except Exception:
		decoded = {}
	return dict(decoded) if isinstance(decoded, dict) else {}


def apply_local_followup_transforms(
	*,
	request_id: str,
	initial_text: str,
	requested_modes: List[str],
	family_artifact_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any],
	assistant_payload: Dict[str, Any],
	display_preferences: Dict[str, Any],
	target_dimension: str,
	target_limit: int,
	sort_direction: str,
	target_metric: str,
	requested_columns: List[str],
	requested_time_scope: str,
	show_million: bool,
	supports_local_family_followup,
	render_local_family_followup,
	render_local_followup,
	ensure_table_from_grounded_context,
	transform_markdown_to_million,
	refine_local_family_artifact,
) -> Tuple[str, List[str], Dict[str, Any], Dict[str, Any]]:
	requested_mode_set = {
		str(value or "").strip()
		for value in (requested_modes or [])
		if str(value or "").strip()
	}
	transformed = str(initial_text or "").strip()
	applied_transforms: List[str] = []
	family_followup_payload: Dict[str, Any] = {}
	family_artifact_update_payload: Dict[str, Any] = {}

	if supports_local_family_followup(
		family_artifact_payload,
		target_limit=target_limit,
		target_metric=target_metric,
		requested_columns=requested_columns,
		requested_time_scope=requested_time_scope,
		requested_modes=list(requested_mode_set),
		show_million=show_million,
	):
		family_artifact_update_payload = refine_local_family_artifact(
			request_id=request_id,
			artifact_payload=family_artifact_payload,
			target_limit=target_limit,
			sort_direction=sort_direction,
			target_metric=target_metric,
			requested_columns=requested_columns,
			requested_modes=list(requested_mode_set),
		)
		family_render = render_local_family_followup(
			request_id=request_id,
			artifact_payload=family_artifact_update_payload or family_artifact_payload,
			target_limit=target_limit,
			sort_direction=sort_direction,
			target_metric=target_metric,
			requested_columns=requested_columns,
			requested_modes=list(requested_mode_set),
			show_million=show_million,
		)
		family_text = str(family_render.get("answer_text") or "").strip()
		if family_text:
			transformed = family_text
			family_followup_payload = family_render
			applied_transforms.append("family_followup_render")

	if "aging_bucket_view" in requested_mode_set and "family_followup_render" not in applied_transforms:
		aging_view = render_local_followup("aging_bucket_view", grounded_turn, display_preferences)
		if aging_view:
			transformed = aging_view
			applied_transforms.append("aging_bucket_view")

	if "dimension_breakdown" in requested_mode_set and "family_followup_render" not in applied_transforms:
		breakdown_view = render_local_followup(
			"dimension_breakdown",
			grounded_turn,
			display_preferences,
			target_dimension=target_dimension,
			assistant_payload=assistant_payload,
		)
		if breakdown_view:
			transformed = breakdown_view
			applied_transforms.append("dimension_breakdown")

	if "sort_or_limit" in requested_mode_set and "family_followup_render" not in applied_transforms:
		sorted_view = render_local_followup(
			"sort_or_limit",
			grounded_turn,
			display_preferences,
			target_dimension=target_dimension,
			assistant_payload=assistant_payload,
			target_limit=target_limit,
			sort_direction=sort_direction,
		)
		if sorted_view:
			transformed = sorted_view
			applied_transforms.append("sort_or_limit")

	if "table_presentation" in requested_mode_set:
		with_table = ensure_table_from_grounded_context(transformed, assistant_payload, grounded_turn)
		if with_table and with_table != transformed:
			transformed = with_table
			applied_transforms.append("table_presentation")

	if "presentation_transform" in requested_mode_set:
		scaled = transform_markdown_to_million(transformed)
		if scaled and scaled != transformed:
			transformed = scaled
			applied_transforms.append("presentation_transform")

	return transformed, applied_transforms, family_followup_payload, family_artifact_update_payload


def resolve_local_followup_rendered_payload(
	*,
	family_followup_payload: Dict[str, Any],
	tool_payloads: List[Dict[str, Any]],
) -> Dict[str, Any]:
	rendered_payload = family_followup_payload if isinstance(family_followup_payload, dict) else {}
	if rendered_payload:
		return rendered_payload
	for payload_type in ("qwen_rendered_family_response_contract", "qwen_entity_detail_rendered_response"):
		for item in reversed(tool_payloads or []):
			if str(item.get("type") or "").strip() == payload_type:
				return item
	return {}


def maybe_apply_local_followup_narrative(
	*,
	request_id: str,
	session_name: str,
	raw_message: str,
	interaction_contract,
	response_policy_contract,
	family_artifact_payload: Dict[str, Any],
	family_followup_payload: Dict[str, Any],
	requested_modes: List[str],
	tool_payloads: List[Dict[str, Any]],
	build_artifact_narrative_context,
	narrate_governed_artifact,
	build_artifact_narrative_contract,
) -> Tuple[str, Dict[str, Any], bool]:
	if not family_artifact_payload:
		return "", {}, False
	if family_followup_payload:
		return "", {}, False
	if "bullet_presentation" not in {str(value or "").strip() for value in (requested_modes or []) if str(value or "").strip()}:
		return "", {}, False

	rendered_payload = resolve_local_followup_rendered_payload(
		family_followup_payload=family_followup_payload,
		tool_payloads=tool_payloads,
	)
	artifact_context = build_artifact_narrative_context(
		request_id=request_id,
		artifact_payload=family_artifact_payload,
		rendered_response_payload=rendered_payload,
		response_policy=response_policy_contract.to_runtime_payload(),
		validation_payload={},
	)
	narrative_payload = narrate_governed_artifact(
		session_id=session_name,
		user_id=str(interaction_contract.user_id or "").strip(),
		site_name=str(interaction_contract.site_name or "").strip(),
		message=str(raw_message or "").strip(),
		request_id=request_id,
		artifact_context=artifact_context,
		response_policy=response_policy_contract.to_runtime_payload(),
	)
	narrative_contract = build_artifact_narrative_contract(
		request_id=request_id,
		artifact_context=artifact_context,
		runtime_payload=narrative_payload,
	)
	if narrative_contract is None:
		return "", {}, False
	narrative_contract_payload = narrative_contract.to_payload()
	narrative_text = str(narrative_contract_payload.get("answer_text") or "").strip()
	if not narrative_text:
		return "", narrative_contract_payload, False
	return narrative_text, narrative_contract_payload, True


def try_local_followup_transform(
	session_doc,
	*,
	request_id: str,
	raw_message: str,
	followup_resolution,
	interaction_contract,
	response_policy_contract,
	continuation_contract=None,
	latest_grounded_assistant_context,
	latest_grounded_turn_contract,
	latest_normalized_family_artifact,
	latest_display_preferences,
	session_tool_payloads,
	apply_local_followup_transforms,
	maybe_apply_local_followup_narrative,
	append_message,
	append_tool_payload,
	assistant_text_payload,
	local_transform_trace_message,
	save_session,
	supports_local_family_followup,
	render_local_family_followup,
	render_local_followup,
	ensure_table_from_grounded_context,
	transform_markdown_to_million,
	refine_local_family_artifact,
) -> Tuple[bool, Dict[str, Any]] | None:
	requested_modes = {
		str(mode or "").strip()
		for mode in getattr(followup_resolution, "requested_modes", []) or []
		if str(mode or "").strip()
	}
	target_dimension = str(getattr(followup_resolution, "target_dimension", "") or "").strip()
	target_limit = int(max(0, getattr(followup_resolution, "target_limit", 0) or 0))
	sort_direction = str(getattr(followup_resolution, "sort_direction", "") or "").strip()
	target_metric = str(getattr(followup_resolution, "target_metric", "") or "").strip()
	requested_columns = [
		str(value or "").strip()
		for value in (getattr(followup_resolution, "requested_columns", []) or [])
		if str(value or "").strip()
	]
	requested_time_scope = str(getattr(followup_resolution, "requested_time_scope", "") or "").strip()
	if not requested_modes.intersection(
		{
			"presentation_transform",
			"table_presentation",
			"bullet_presentation",
			"aging_bucket_view",
			"dimension_breakdown",
			"sort_or_limit",
			"metric_refinement",
			"column_refinement",
		}
	):
		return None
	assistant_payload, trace = latest_grounded_assistant_context(session_doc)
	grounded_turn = latest_grounded_turn_contract(session_doc)
	family_artifact_payload = latest_normalized_family_artifact(session_doc)
	contract_preserved_metric = str(getattr(continuation_contract, "preserved_metric_key", "") or "").strip()
	contract_source_metric = str(getattr(continuation_contract, "source_metric_key", "") or "").strip()
	if not target_metric:
		target_metric = str(contract_preserved_metric or contract_source_metric or "").strip()
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

	if not assistant_payload or not trace:
		return None
	text = str(assistant_payload.get("text") or "").strip()
	if not text and not grounded_turn:
		return None
	display_preferences = latest_display_preferences(
		session_doc,
		getattr(followup_resolution, "requested_modes", []) or [],
	)
	show_million = bool((display_preferences or {}).get("million")) or ("presentation_transform" in requested_modes)
	transformed, applied_transforms, family_followup_payload, family_artifact_update_payload = apply_local_followup_transforms(
		request_id=request_id,
		initial_text=text,
		requested_modes=list(requested_modes),
		family_artifact_payload=family_artifact_payload,
		grounded_turn=grounded_turn,
		assistant_payload=assistant_payload,
		display_preferences=display_preferences,
		target_dimension=target_dimension,
		target_limit=target_limit,
		sort_direction=sort_direction,
		target_metric=target_metric,
		requested_columns=requested_columns,
		requested_time_scope=requested_time_scope,
		show_million=show_million,
		supports_local_family_followup=supports_local_family_followup,
		render_local_family_followup=render_local_family_followup,
		render_local_followup=render_local_followup,
		ensure_table_from_grounded_context=ensure_table_from_grounded_context,
		transform_markdown_to_million=transform_markdown_to_million,
		refine_local_family_artifact=refine_local_family_artifact,
	)

	if not transformed or not applied_transforms:
		return None

	effective_family_artifact_payload = family_artifact_update_payload or family_artifact_payload
	narrative_contract_payload: Dict[str, Any] = {}
	narrative_text, narrative_contract_payload, narrative_applied = maybe_apply_local_followup_narrative(
		request_id=request_id,
		session_name=session_doc.name,
		raw_message=raw_message,
		interaction_contract=interaction_contract,
		response_policy_contract=response_policy_contract,
		family_artifact_payload=effective_family_artifact_payload,
		family_followup_payload=family_followup_payload,
		requested_modes=list(requested_modes),
		tool_payloads=session_tool_payloads(session_doc),
	)
	if narrative_applied and narrative_text:
		transformed = narrative_text
		applied_transforms.append("artifact_narrative_followup")

	local_transform_trace_payload = _payload_from_tool_message(
		local_transform_trace_message(
			request_id=request_id,
			source_request_id=str(trace.get("request_id") or "").strip(),
			transforms=applied_transforms,
		)
	)
	execution_path = ExecutionPath(
		request_id=request_id,
		path="local_transform",
		reason="The answer was produced by transforming the latest grounded assistant artifact without a new ERP runtime call.",
		requires_runtime=False,
		grounded_required=True,
	)
	answer_mode = "local_grounded_transform"
	runtime_metadata_envelope = _local_followup_metadata_envelope(answer_mode=answer_mode)
	pre_assistant_tool_payloads: List[Dict[str, Any]] = []
	if family_artifact_update_payload:
		pre_assistant_tool_payloads.append(family_artifact_update_payload)
	if family_followup_payload:
		pre_assistant_tool_payloads.append(family_followup_payload)
	if narrative_contract_payload:
		pre_assistant_tool_payloads.append(narrative_contract_payload)
	if local_transform_trace_payload:
		local_transform_trace_payload["runtime_metadata_envelope"] = runtime_metadata_envelope
		trace_agent_meta = (
			local_transform_trace_payload.get("agent_meta")
			if isinstance(local_transform_trace_payload.get("agent_meta"), dict)
			else {}
		)
		local_transform_trace_payload["agent_meta"] = {
			**trace_agent_meta,
			"runtime_metadata_envelope": runtime_metadata_envelope,
		}
		pre_assistant_tool_payloads.append(local_transform_trace_payload)
	pre_assistant_tool_payloads.append(runtime_metadata_envelope)
	pre_assistant_tool_payloads.append(execution_path.to_payload())

	# EC-4R2 local-transform authority checkpoint: transformed evidence stays staged until allowed.
	authorized_emission = emit_authorized_assistant_answer(
		session_doc=session_doc,
		answer_text=transformed,
		answer_type=ANSWER_TYPE_VISIBLE_CONTEXT,
		append_message=append_message,
		append_tool_payload=append_tool_payload,
		assistant_text_payload=assistant_text_payload,
		interaction_contract=interaction_contract,
		followup_resolution=followup_resolution,
		execution_path=execution_path,
		runtime_trace_payload=local_transform_trace_payload,
		grounded_turn_context=grounded_turn,
		authority_context={"normalized_family_artifact": effective_family_artifact_payload},
		pre_assistant_tool_payloads=pre_assistant_tool_payloads,
	)
	save_session(session_doc, ignore_permissions=False)
	return True, {
		"ok": bool(authorized_emission.emitted),
		"request_id": request_id,
		"mode": answer_mode,
		"agent_meta": {
			"engine": "local_transform",
			"transforms": applied_transforms,
			"runtime_metadata_envelope": runtime_metadata_envelope,
			"authorized_emission": authorized_emission.to_payload(),
		},
	}
