from __future__ import annotations

import json
from typing import Any, Dict, Tuple

from .authorized_emission import (
	ANSWER_TYPE_ERROR,
	ANSWER_TYPE_GOVERNED_REPORT,
	emit_authorized_assistant_answer,
)
from .contracts import ExecutionPath, build_followup_resolution_contract


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _payload_dict(value: Any) -> Dict[str, Any]:
	if isinstance(value, dict):
		return dict(value)
	if isinstance(value, str):
		try:
			loaded = json.loads(value)
		except Exception:
			return {}
		return dict(loaded) if isinstance(loaded, dict) else {}
	return {}


def _entity_followup_error_control_authority(*, error: str) -> Dict[str, Any]:
	return {
		"authority_source": "error_fallback",
		"answer_mode": "entity_followup_error",
		"reason": _clean_text(error) or "Entity detail follow-up failed before governed answer authority was available.",
		"preflight_status": "passed",
	}


def _entity_followup_grounded_turn_payload(
	*,
	grounded_turn_payload: Dict[str, Any],
	artifact_payload: Dict[str, Any],
	request_id: str,
) -> Dict[str, Any]:
	grounded = _clean_dict(grounded_turn_payload)
	artifact = _clean_dict(artifact_payload)
	if not artifact or not bool(grounded.get("grounded")):
		return {}
	artifact_family_id = _clean_text(
		grounded.get("artifact_family_id")
		or grounded.get("family_id")
		or artifact.get("family_id")
		or artifact.get("report_family")
		or "entity_detail"
	)
	return {
		**grounded,
		"request_id": _clean_text(grounded.get("request_id")) or _clean_text(request_id),
		"trace_request_id": _clean_text(grounded.get("trace_request_id")) or _clean_text(request_id),
		"grounded": True,
		"source_kind": _clean_text(grounded.get("source_kind")) or "tool",
		"source_name": _clean_text(grounded.get("source_name")) or "entity_detail_lookup",
		"artifact_family_id": artifact_family_id,
		"artifact_type": _clean_text(grounded.get("artifact_type") or artifact.get("type")) or "qwen_entity_detail_artifact",
	}


def try_entity_detail_followup(
	session_doc,
	*,
	request_id: str,
	raw_message: str,
	entity_reference: Dict[str, Any],
	interaction_contract,
	response_policy_contract,
	latest_grounded_turn: Dict[str, Any],
	execute_entity_drilldown,
	log_error,
	append_message,
	append_tool_payload,
	assistant_text_payload,
	tool_trace_message,
	save_session,
) -> Tuple[bool, Dict[str, Any]] | None:
	try:
		outcome = execute_entity_drilldown(
			request_id=request_id,
			session_id=session_doc.name,
			user_id=str(interaction_contract.user_id or "").strip(),
			site_name=str(interaction_contract.site_name or "").strip(),
			message=str(raw_message or "").strip(),
			entity_reference=entity_reference,
			response_policy=response_policy_contract.to_runtime_payload(),
			grounded_turn=latest_grounded_turn,
		)
	except Exception as exc:
		log_error("Qwen Assistant: entity drilldown failed")
		error_text = "I couldn't complete that entity detail confidently from governed ERP data."
		trace_payload = _payload_dict(
			tool_trace_message(
				request_id=request_id,
				ok=False,
				tool_trace=[
					{
						"tool": "entity_detail_lookup",
						"status": "error",
						"detail": str(exc or "").strip(),
						"detail_obj": {
							"entity_type": str(entity_reference.get("entity_type") or "").strip(),
							"entity_key": str(entity_reference.get("entity_key") or "").strip(),
						},
					}
				],
				agent_meta={"engine": "entity_detail", "mode": "entity_drilldown"},
				error=str(exc or "").strip(),
				runtime_latency_ms=0,
			)
		)
		authorized_emission = emit_authorized_assistant_answer(
			session_doc=session_doc,
			answer_text=error_text,
			answer_type=ANSWER_TYPE_ERROR,
			append_message=append_message,
			append_tool_payload=append_tool_payload,
			assistant_text_payload=assistant_text_payload,
			control_meta_authority=_entity_followup_error_control_authority(error=str(exc or "").strip()),
			pre_assistant_tool_payloads=[trace_payload],
		)
		save_session(session_doc, ignore_permissions=False)
		return True, {
			"ok": False,
			"request_id": request_id,
			"error": str(exc or "").strip(),
			"agent_meta": {
				"engine": "entity_detail",
				"authorized_emission": authorized_emission.to_payload(),
			},
		}

	if not bool(outcome.get("ok")):
		return None

	answer_text = str(outcome.get("answer_text") or "").strip()
	artifact_payload = outcome.get("artifact_payload") if isinstance(outcome.get("artifact_payload"), dict) else {}
	rendered_payload = outcome.get("rendered_response_payload") if isinstance(outcome.get("rendered_response_payload"), dict) else {}
	narrative_contract_payload = outcome.get("narrative_contract_payload") if isinstance(outcome.get("narrative_contract_payload"), dict) else {}
	grounded_turn_payload = outcome.get("grounded_turn_payload") if isinstance(outcome.get("grounded_turn_payload"), dict) else {}
	trace_payload = _payload_dict(tool_trace_message(
		request_id=request_id,
		ok=True,
		tool_trace=[
			{
				"tool": "entity_detail_lookup",
				"status": "ok",
				"detail": "Entity detail lookup completed; answer text is emitted only after final-answer authority passes.",
				"detail_obj": {
					"entity_type": str((outcome.get("entity_reference") or {}).get("entity_type") or "").strip(),
					"entity_key": str((outcome.get("entity_reference") or {}).get("entity_key") or "").strip(),
				},
			}
		],
		agent_meta={"engine": "entity_detail", "mode": "entity_drilldown"},
		error="",
		runtime_latency_ms=0,
	))
	pre_assistant_tool_payloads = [
		payload
		for payload in [
			artifact_payload,
			rendered_payload,
			narrative_contract_payload,
			grounded_turn_payload,
			trace_payload,
		]
		if payload
	]
	followup_resolution = build_followup_resolution_contract(
		request_id=request_id,
		mode="entity_followup_detail",
		requested_modes=["entity_followup_detail"],
		depends_on_grounded_turn=True,
		self_contained=False,
		latest_grounded_turn_available=bool(_clean_dict(latest_grounded_turn).get("grounded")),
		reason="Entity follow-up executed a governed entity-detail lookup from current grounded context.",
	)
	execution_path = ExecutionPath(
		request_id=request_id,
		path="entity_followup_detail",
		reason="Entity follow-up executed a governed entity-detail lookup from current grounded context.",
		requires_runtime=False,
		grounded_required=True,
	)
	authorized_emission = emit_authorized_assistant_answer(
		session_doc=session_doc,
		answer_text=answer_text,
		answer_type=ANSWER_TYPE_GOVERNED_REPORT,
		append_message=append_message,
		append_tool_payload=append_tool_payload,
		assistant_text_payload=assistant_text_payload,
		interaction_contract=interaction_contract,
		followup_resolution=followup_resolution,
		execution_path=execution_path,
		runtime_trace_payload={
			"agent_meta": {"engine": "entity_detail", "mode": "entity_drilldown"},
			"runtime_latency_ms": 0,
		},
		grounded_turn_context=_entity_followup_grounded_turn_payload(
			grounded_turn_payload=grounded_turn_payload,
			artifact_payload=artifact_payload,
			request_id=request_id,
		),
		authority_context={"normalized_family_artifact": artifact_payload},
		pre_assistant_tool_payloads=pre_assistant_tool_payloads,
	)
	save_session(session_doc, ignore_permissions=False)
	return True, {
		"ok": bool(authorized_emission.emitted),
		"request_id": request_id,
		"agent_meta": {
			"engine": "entity_detail",
			"mode": "entity_drilldown",
			"authorized_emission": authorized_emission.to_payload(),
		},
	}
