from __future__ import annotations

from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.contracts import (
	ArtifactNarrativeResponseContract,
	build_artifact_narrative_response_contract,
)
from ai_assistant_ui.qwen_chat.model_backed_helper_metadata import (
	attach_helper_metadata_to_agent_meta,
	build_model_backed_helper_runtime_metadata_bundle,
)
from ai_assistant_ui.qwen_chat.runtime_client import (
	QwenRuntimeClientError,
	call_qwen_runtime_chat,
)


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _markdown_table(columns: List[str], rows: List[List[str]]) -> str:
	clean_columns = [_clean_text(item) for item in columns if _clean_text(item)]
	if not clean_columns or not rows:
		return ""
	lines = [
		"| " + " | ".join(clean_columns) + " |",
		"| " + " | ".join("---" for _ in clean_columns) + " |",
	]
	for row in rows:
		if not isinstance(row, list):
			continue
		values = [_clean_text(cell) for cell in row]
		if values:
			lines.append("| " + " | ".join(values) + " |")
	return "\n".join(lines).strip()


def _block_markdown(block: Dict[str, Any]) -> str:
	if not isinstance(block, dict):
		return ""
	block_type = _clean_text(block.get("block_type"))
	title = _clean_text(block.get("title"))
	lines: List[str] = []
	if title:
		lines.append(f"### {title}")
	if block_type in {"summary_table", "data_table"}:
		columns = block.get("columns") if isinstance(block.get("columns"), list) else []
		rows = block.get("rows") if isinstance(block.get("rows"), list) else []
		table = _markdown_table(
			[_clean_text(item) for item in columns],
			[
				[_clean_text(cell) for cell in row]
				for row in rows
				if isinstance(row, list)
			],
		)
		if table:
			lines.append(table)
	elif block_type == "bullet_list":
		items = [_clean_text(item) for item in (block.get("items") or []) if _clean_text(item)]
		for item in items:
			lines.append(f"- {item}")
	return "\n".join(line for line in lines if line).strip()


def _attach_artifact_narrative_metadata(
	runtime_payload: Dict[str, Any],
	*,
	fallback_used: bool,
	fallback_reason: str = "",
) -> Dict[str, Any]:
	payload = dict(runtime_payload or {})
	agent_meta = payload.get("agent_meta") if isinstance(payload.get("agent_meta"), dict) else {}
	metadata_bundle = build_model_backed_helper_runtime_metadata_bundle(
		lane_id="artifact_narrative",
		role_owner="artifact_narrative",
		agent_meta=agent_meta,
		runtime_source="artifact_narrative_runtime_agent_meta" if agent_meta else "artifact_narrative_without_runtime_agent_meta",
		answer_mode="artifact_narrative",
		evidence_scope="governed_artifact",
		authority_source="artifact_context",
		preflight_status="passed",
		fallback_used=fallback_used,
		fallback_reason=fallback_reason,
	)
	agent_meta = attach_helper_metadata_to_agent_meta(agent_meta, metadata_bundle)
	payload["agent_meta"] = agent_meta
	payload["model_role_observability"] = metadata_bundle["model_role_observability"]
	payload["model_role_strict_readiness"] = metadata_bundle["model_role_strict_readiness"]
	payload["runtime_metadata_envelope"] = metadata_bundle["runtime_metadata_envelope"]
	return payload


def _presentation_hints(
	blocks: List[Dict[str, Any]],
	response_policy: Dict[str, Any],
) -> Dict[str, Any]:
	types = [str(item.get("block_type") or "").strip() for item in blocks if isinstance(item, dict)]
	preferred_formats = [
		_clean_text(item)
		for item in list((response_policy or {}).get("preferred_formats") or [])
		if _clean_text(item)
	]
	return {
		"has_summary_table": "summary_table" in types,
		"has_data_table": "data_table" in types,
		"has_bullet_list": "bullet_list" in types,
		"preferred_formats": preferred_formats,
		"max_paragraph_sentences": int(max(1, (response_policy or {}).get("max_paragraph_sentences") or 2)),
		"recommended_layout": [
			_clean_text(item)
			for item in list((response_policy or {}).get("structure") or [])
			if _clean_text(item)
		],
	}


def build_artifact_narrative_context(
	*,
	request_id: str,
	artifact_payload: Dict[str, Any] | None,
	rendered_response_payload: Dict[str, Any] | None,
	response_policy: Dict[str, Any] | None,
	validation_payload: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	artifact = dict(artifact_payload or {}) if isinstance(artifact_payload, dict) else {}
	rendered = dict(rendered_response_payload or {}) if isinstance(rendered_response_payload, dict) else {}
	validation = dict(validation_payload or {}) if isinstance(validation_payload, dict) else {}
	support_blocks = list(rendered.get("blocks") or []) if isinstance(rendered.get("blocks"), list) else []
	response_policy_payload = dict(response_policy or {}) if isinstance(response_policy, dict) else {}
	support_block_markdown = [
		{
			"title": _clean_text(block.get("title")),
			"block_type": _clean_text(block.get("block_type")),
			"markdown": _block_markdown(block),
		}
		for block in support_blocks
		if isinstance(block, dict) and _block_markdown(block)
	]
	return {
		"request_id": _clean_text(request_id),
		"family_id": _clean_text(artifact.get("family_id") or rendered.get("family_id")),
		"artifact_payload": artifact,
		"support_blocks": support_blocks,
		"support_block_markdown": support_block_markdown,
		"render_title": _clean_text(rendered.get("title")),
		"source_reports": [
			_clean_text(item)
			for item in list(rendered.get("source_reports") or artifact.get("source_reports") or [])
			if _clean_text(item)
		],
		"response_policy": response_policy_payload,
		"presentation_hints": _presentation_hints(support_blocks, response_policy_payload),
		"validation_payload": validation,
	}


def narrate_governed_artifact(
	*,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	request_id: str,
	artifact_context: Dict[str, Any],
	response_policy: Dict[str, Any] | None,
) -> Dict[str, Any]:
	try:
		runtime_payload = call_qwen_runtime_chat(
			session_id=session_id,
			user_id=user_id,
			site_name=site_name,
			message=message,
			recent_messages=[],
			response_policy=response_policy if isinstance(response_policy, dict) else {},
			family_tool_context={},
			mode="artifact_narrative",
			compiled_query={},
			artifact_context=artifact_context,
			request_id=request_id,
		)
	except QwenRuntimeClientError as exc:
		return _attach_artifact_narrative_metadata(
			{
				"ok": False,
				"answer_text": "",
				"agent_meta": {"engine": "artifact_narrative", "mode": "artifact_narrative"},
				"error": str(exc),
			},
			fallback_used=True,
			fallback_reason=str(exc),
		)
	if not isinstance(runtime_payload, dict):
		return _attach_artifact_narrative_metadata(
			{
				"ok": False,
				"answer_text": "",
				"agent_meta": {"engine": "artifact_narrative", "mode": "artifact_narrative"},
				"error": "Artifact narrative runtime returned an invalid payload.",
			},
			fallback_used=True,
			fallback_reason="invalid_runtime_payload",
		)
	return _attach_artifact_narrative_metadata(
		runtime_payload,
		fallback_used=not bool(runtime_payload.get("ok")),
		fallback_reason=_clean_text(runtime_payload.get("error")),
	)


def build_artifact_narrative_contract(
	*,
	request_id: str,
	artifact_context: Dict[str, Any],
	runtime_payload: Dict[str, Any],
) -> ArtifactNarrativeResponseContract | None:
	answer_text = _clean_text((runtime_payload or {}).get("answer_text"))
	if not answer_text:
		return None
	agent_meta = (runtime_payload or {}).get("agent_meta") if isinstance((runtime_payload or {}).get("agent_meta"), dict) else {}
	response_policy = artifact_context.get("response_policy") if isinstance(artifact_context.get("response_policy"), dict) else {}
	return build_artifact_narrative_response_contract(
		request_id=request_id,
		family_id=_clean_text(artifact_context.get("family_id")),
		narrative_engine=_clean_text(agent_meta.get("engine") or "artifact_narrative"),
		answer_style=_clean_text(response_policy.get("answer_style")),
		answer_text=answer_text,
		source_reports=[
			_clean_text(item)
			for item in list(artifact_context.get("source_reports") or [])
			if _clean_text(item)
		],
		support_block_count=len(list(artifact_context.get("support_blocks") or [])),
		warnings=[
			_clean_text(item)
			for item in list(((artifact_context.get("artifact_payload") or {}).get("warnings") or []))
			if _clean_text(item)
		],
	)
