from __future__ import annotations

from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.metadata import get_scope_clarification_template_spec


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def scope_clarification_question(
	*,
	reason_type: str,
	template_group: str,
	variant: str,
	default_question: str = "",
	template_values: Dict[str, str] | None = None,
) -> str:
	spec = get_scope_clarification_template_spec(reason_type, template_group=template_group)
	question_templates = spec.get("question_templates") if isinstance(spec.get("question_templates"), dict) else {}
	template = _clean_text(question_templates.get(variant)) or _clean_text(question_templates.get("default"))
	fallback_question = _clean_text(default_question)
	if not fallback_question and template_group == "shared_clarification":
		fallback_spec = get_scope_clarification_template_spec(
			"generic_clarification",
			template_group="shared_clarification",
		)
		fallback_templates = (
			fallback_spec.get("question_templates")
			if isinstance(fallback_spec.get("question_templates"), dict)
			else {}
		)
		fallback_question = _clean_text(fallback_templates.get("default"))
	if not template:
		return fallback_question
	try:
		return template.format(**dict(template_values or {}))
	except KeyError:
		return fallback_question or template


def shared_clarification_question(
	*,
	reason_type: str,
	variant: str,
	default_question: str = "",
	template_values: Dict[str, str] | None = None,
) -> str:
	return scope_clarification_question(
		reason_type=reason_type,
		template_group="shared_clarification",
		variant=variant,
		default_question=default_question,
		template_values=dict(template_values or {}),
	)


def render_shared_choice_list_clarification(
	*,
	reason_type: str,
	variant: str,
	template_values: Dict[str, str] | None,
	options: List[str],
	default_question: str = "",
	default_heading: str = "Choose one:",
) -> str:
	spec = get_scope_clarification_template_spec(
		reason_type,
		template_group="shared_clarification",
	)
	question = shared_clarification_question(
		reason_type=reason_type,
		variant=variant,
		default_question=default_question,
		template_values=dict(template_values or {}),
	)
	clean_question = _clean_text(question)
	clean_options = [value for value in options if _clean_text(value)]
	if not clean_options:
		return clean_question
	list_heading_templates = (
		spec.get("list_heading_templates")
		if isinstance(spec.get("list_heading_templates"), dict)
		else {}
	)
	list_heading = (
		_clean_text(list_heading_templates.get(variant))
		or _clean_text(list_heading_templates.get("default"))
		or _clean_text(default_heading)
	)
	lines = [clean_question]
	if list_heading:
		lines.extend(["", list_heading])
	for option in clean_options:
		lines.append(f"- {option}")
	return "\n".join(lines).strip()
