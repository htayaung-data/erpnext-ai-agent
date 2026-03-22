from __future__ import annotations

import re
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.contracts import (
	FamilyToolSurfaceContract,
	build_family_tool_surface_contract,
)
from ai_assistant_ui.qwen_chat.metadata import (
	list_report_family_specs,
	ontology_detect_concepts,
	report_family_agent_prompt_hint,
	report_family_agent_tool_id,
	report_family_capability_ids,
	report_family_report_names,
	report_family_routing_hints,
	report_family_supported_intent_classes,
)


def _normalize_text(value: str) -> str:
	return " ".join(str(value or "").strip().lower().split())


def _normalize_phrase(value: str) -> str:
	text = _normalize_text(value)
	text = re.sub(r"[^a-z0-9&/\-\s]+", " ", text)
	return " ".join(text.split())


def _unique_strings(values: List[str]) -> List[str]:
	return list(dict.fromkeys(str(item or "").strip() for item in values if str(item or "").strip()))


def _matched_phrases(text: str, values: List[str]) -> List[str]:
	normalized_text = _normalize_phrase(text)
	out: List[str] = []
	for item in values:
		candidate = _normalize_phrase(item)
		if candidate and candidate in normalized_text:
			out.append(str(item or "").strip())
	return _unique_strings(out)


def build_family_tool_surface_for_message(
	*,
	request_id: str,
	session_id: str,
	message: str,
	preferred_intent_class: str = "",
	preferred_capability_id: str = "",
) -> FamilyToolSurfaceContract | None:
	text = _normalize_text(message)
	if not text:
		return None

	detected_concepts = set(ontology_detect_concepts(message))
	candidate_entries: List[Dict[str, Any]] = []
	for family_spec in list_report_family_specs():
		family_id = str(family_spec.get("family_id") or "").strip()
		if not family_id:
			continue
		routing_hints = report_family_routing_hints(family_id)
		concept_hints = [
			str(item or "").strip()
			for item in (routing_hints.get("ontology_concepts") or [])
			if str(item or "").strip()
		]
		intent_markers = [
			str(item or "").strip()
			for item in (routing_hints.get("intent_markers") or [])
			if str(item or "").strip()
		]
		matched_concepts = [item for item in concept_hints if item in detected_concepts]
		matched_markers = _matched_phrases(text, intent_markers)
		matched_report_names = _matched_phrases(text, report_family_report_names(family_id))

		score = 0
		if matched_concepts:
			score += 14 * len(matched_concepts)
		if matched_markers:
			score += 12 * len(matched_markers)
		if matched_report_names:
			score += 18 * len(matched_report_names)
		if preferred_intent_class and preferred_intent_class in report_family_supported_intent_classes(family_id):
			score += 20
		if preferred_capability_id and preferred_capability_id in report_family_capability_ids(family_id):
			score += 20
		if score <= 0:
			continue

		report_names = report_family_report_names(family_id)
		candidate_entries.append(
			{
				"family_id": family_id,
				"family_label": str(family_spec.get("family_label") or family_id).strip(),
				"tool_id": report_family_agent_tool_id(family_id),
				"prompt_hint": report_family_agent_prompt_hint(family_id),
				"report_names": report_names,
				"matched_concepts": matched_concepts,
				"matched_markers": matched_markers,
				"matched_report_names": matched_report_names,
				"score": score,
			}
		)

	if not candidate_entries:
		return None

	candidate_entries.sort(key=lambda item: (-int(item.get("score") or 0), str(item.get("family_id") or "")))
	top_score = int(candidate_entries[0].get("score") or 0)
	selection_floor = max(18, top_score - 8)
	selected_entries = [item for item in candidate_entries if int(item.get("score") or 0) >= selection_floor][:3]
	if not selected_entries:
		return None

	candidate_family_ids = [str(item.get("family_id") or "").strip() for item in selected_entries]
	preferred_tool_ids = _unique_strings([str(item.get("tool_id") or "").strip() for item in selected_entries])
	allowed_report_names = _unique_strings(
		[
			str(report_name or "").strip()
			for item in selected_entries
			for report_name in list(item.get("report_names") or [])
			if str(report_name or "").strip()
		]
	)
	report_discovery_allowed = False
	reason_parts: List[str] = []
	if detected_concepts:
		reason_parts.append(f"ontology concepts: {', '.join(sorted(detected_concepts))}")
	reason_parts.append(f"selected families: {', '.join(candidate_family_ids)}")

	return build_family_tool_surface_contract(
		request_id=request_id,
		session_id=session_id,
		candidate_family_ids=candidate_family_ids,
		preferred_tool_ids=preferred_tool_ids,
		allowed_report_names=allowed_report_names,
		report_discovery_allowed=report_discovery_allowed,
		reason="; ".join(reason_parts),
		family_entries=selected_entries,
	)
