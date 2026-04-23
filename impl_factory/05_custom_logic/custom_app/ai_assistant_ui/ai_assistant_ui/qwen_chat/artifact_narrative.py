from __future__ import annotations

from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.contracts import (
	ArtifactNarrativeResponseContract,
	build_artifact_narrative_response_contract,
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


def _artifact_narrative_system_prompt(
	*,
	family_id: str,
	source_reports: List[str],
	response_policy: Dict[str, Any],
) -> str:
	answer_style = _clean_text((response_policy or {}).get("answer_style"))
	implication_allowed = bool((response_policy or {}).get("implication_allowed"))
	recommendation_allowed = bool((response_policy or {}).get("recommendation_allowed"))
	direct_answer_first = bool((response_policy or {}).get("direct_answer_first", True))
	report_names = {_clean_text(item) for item in list(source_reports or []) if _clean_text(item)}
	rules = [
		"You are an ERP business assistant narrating a governed artifact.",
		"Use only facts and explicit derived calculations already present in the governed artifact and support blocks.",
		"Never expose technical internals such as families, capabilities, contracts, or runtime mechanics.",
	]
	if direct_answer_first:
		rules.append("Lead with the direct business answer before any supporting detail.")
	if answer_style in {"simple_factual", "operational_list", "followup_refinement"}:
		rules.append("Keep the wording descriptive and factual. Do not add interpretive business commentary unless it is explicitly requested.")
	if not implication_allowed:
		rules.append(
			"Do not infer causes, customer intent, business health judgments, chronicity, urgency, risk severity, or behavioral patterns from the data."
		)
	if not recommendation_allowed:
		rules.append(
			"Do not recommend actions, escalation, collections strategy, policy changes, or management decisions."
		)
	if family_id == "financial_statement":
		rules.append(
			"For financial statements, keep the answer factual unless the response policy explicitly allows analysis."
		)
		rules.append(
			"Use the exact amounts and units already shown in the governed support blocks."
		)
		rules.append(
			"Do not rescale full MMK amounts into abbreviated MMK, MMK million, or rounded shorthand unless that unit is already present in the support blocks or the user explicitly asked for it."
		)
		rules.append(
			"Do not add a 'Business implication' section or interpretive commentary unless the response policy explicitly allows implications."
		)
	if family_id == "aging":
		rules.append(
			"For aging and customer credit exposure artifacts, describe overdue, current, due, and negative balances only as reported facts or explicit derived percentages."
		)
		rules.append(
			"Do not characterize the balances as chronic issues, short-term delays, collection problems, payment behavior, or credit policy outcomes unless the user explicitly asks for analysis and the artifact proves it."
		)
	if "Accounts Receivable Summary" in report_names:
		rules.append(
			"Do not mention credit limits, credit holds, or credit policy unless the artifact explicitly includes those fields."
		)
	return "\n".join(["Rules:"] + [f"{idx}. {rule}" for idx, rule in enumerate(rules, start=1)]).strip()


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
		"system_prompt": _artifact_narrative_system_prompt(
			family_id=_clean_text(artifact.get("family_id") or rendered.get("family_id")),
			source_reports=[
				_clean_text(item)
				for item in list(rendered.get("source_reports") or artifact.get("source_reports") or [])
				if _clean_text(item)
			],
			response_policy=response_policy_payload,
		),
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
		return {
			"ok": False,
			"answer_text": "",
			"agent_meta": {"engine": "artifact_narrative", "mode": "artifact_narrative"},
			"error": str(exc),
		}
	if not isinstance(runtime_payload, dict):
		return {
			"ok": False,
			"answer_text": "",
			"agent_meta": {"engine": "artifact_narrative", "mode": "artifact_narrative"},
			"error": "Artifact narrative runtime returned an invalid payload.",
		}
	return runtime_payload


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
