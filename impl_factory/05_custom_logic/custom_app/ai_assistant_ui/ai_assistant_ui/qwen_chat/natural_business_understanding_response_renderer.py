from __future__ import annotations

import re
from typing import Any, Dict, List

from .metadata import get_capability_spec
from .natural_business_understanding_contracts import CONTRACT_VERSION


INTERNAL_USER_TEXT_TERMS = {
	"qwen",
	"contract",
	"planner",
	"shadow",
	"runtime",
	"validation_status",
	"blocked_missing_policy",
	"approved_policy_artifact_required",
	"live activation",
}


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


def _sentence(values: List[str], *, limit: int = 3) -> str:
	clean = _clean_list(values)[:limit]
	if not clean:
		return ""
	if len(clean) == 1:
		return clean[0]
	return ", ".join(clean[:-1]) + f", or {clean[-1]}"


def _humanize(value: Any) -> str:
	text = _clean_text(value).replace("_", " ").replace("-", " ")
	return " ".join(part for part in text.split() if part)


def _strip_trailing_read_label(label: str) -> str:
	clean = _clean_text(label)
	if clean.lower().endswith(" read"):
		return clean[:-5].strip()
	return clean


def _business_option_label(value: Any) -> str:
	text = _clean_text(value)
	if not text:
		return ""
	spec = get_capability_spec(text)
	if spec:
		for key in ("clarification_business_area_label", "label"):
			label = _strip_trailing_read_label(_clean_text(spec.get(key)))
			if label:
				return label
	if re.fullmatch(r"[a-z][a-z0-9_]*(?:_[a-z0-9]+)*", text):
		label = _strip_trailing_read_label(_humanize(text))
		return label or text
	return text


def _dedupe_business_options(values: List[str]) -> List[str]:
	out: List[str] = []
	seen: set[str] = set()
	for value in values:
		label = _business_option_label(value)
		if not label:
			continue
		key = label.strip().casefold()
		if key in seen:
			continue
		seen.add(key)
		out.append(label)
	return out


def _selected_candidate(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	trace = _clean_dict(trace_payload)
	selected_id = _clean_text(trace.get("selected_candidate_id"))
	for candidate in trace.get("candidate_interpretations") or []:
		candidate_dict = _clean_dict(candidate)
		if selected_id and _clean_text(candidate_dict.get("candidate_id")) == selected_id:
			return candidate_dict
	candidates = trace.get("candidate_interpretations")
	if isinstance(candidates, list) and candidates:
		return _clean_dict(candidates[0])
	return {}


def _entity_label(trace_payload: Dict[str, Any]) -> str:
	context = _clean_dict(_clean_dict(trace_payload).get("context_resolution"))
	entity = _clean_dict(context.get("resolved_entity"))
	candidate_entity = _clean_dict(_selected_candidate(trace_payload).get("target_entity"))
	for source in (entity, candidate_entity):
		for key in ("entity_label", "label", "entity_name", "name", "entity_key", "key"):
			value = _clean_text(source.get(key))
			if value:
				return value
	return ""


def _alternative_label(alternative: Dict[str, Any]) -> str:
	alt = _clean_dict(alternative)
	for key in ("report_name", "label", "family_id", "execution_id"):
		value = _clean_text(alt.get(key))
		if value:
			return _business_option_label(value)
	return _business_option_label(alt.get("target_type")) or "ERP option"


def _alternative_lines(alternatives: List[Dict[str, Any]], *, limit: int = 3) -> List[str]:
	lines: List[str] = []
	for alternative in alternatives[:limit]:
		alt = _clean_dict(alternative)
		label = _alternative_label(alt)
		metrics = _sentence(_clean_list(alt.get("supported_metrics")), limit=3)
		dimensions = _sentence(_clean_list(alt.get("supported_dimensions") or alt.get("required_dimensions")), limit=2)
		suffix_parts = []
		if metrics:
			suffix_parts.append(f"metrics: {metrics}")
		if dimensions:
			suffix_parts.append(f"dimensions: {dimensions}")
		suffix = f" ({'; '.join(suffix_parts)})" if suffix_parts else ""
		lines.append(f"{label}{suffix}")
	return lines


def _options_from_trace(trace_payload: Dict[str, Any]) -> List[str]:
	trace = _clean_dict(trace_payload)
	decision = _clean_dict(trace.get("conversation_action_decision"))
	context = _clean_dict(trace.get("context_resolution"))
	requery = _clean_dict(trace.get("governed_requery_plan"))
	options: List[str] = []
	options.extend(_clean_list(context.get("ambiguity_options")))
	options.extend(_clean_list(decision.get("suggested_options")))
	options.extend(_alternative_lines(_clean_dict_list(requery.get("suggested_alternatives"))))
	return _dedupe_business_options(options)


def _clean_dict_list(values: Any) -> List[Dict[str, Any]]:
	if not isinstance(values, list):
		return []
	return [dict(value) for value in values if isinstance(value, dict)]


def _technical_summary(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	trace = _clean_dict(trace_payload)
	decision = _clean_dict(trace.get("conversation_action_decision"))
	requery = _clean_dict(trace.get("governed_requery_plan"))
	validation = _clean_dict(trace.get("validation_result"))
	return {
		"action": _clean_text(decision.get("action")),
		"response_mode": _clean_text(decision.get("response_mode")),
		"validation_status": _clean_text(validation.get("status")),
		"requery_status": _clean_text(requery.get("status")),
		"planner_mode": _clean_text(requery.get("planner_mode")),
		"shadow_mode": bool(trace.get("shadow_mode", True)),
		"live_execution_enabled": False,
	}


def _candidate_targets(trace_payload: Dict[str, Any]) -> List[str]:
	candidate = _selected_candidate(trace_payload)
	targets: List[str] = []
	targets.extend(_clean_list(candidate.get("candidate_report_names")))
	targets.extend([_humanize(value) for value in _clean_list(candidate.get("candidate_composite_family_ids"))])
	targets.extend([_humanize(value) for value in _clean_list(candidate.get("candidate_capability_ids"))])
	return list(dict.fromkeys(targets))


def _business_area_phrase(trace_payload: Dict[str, Any]) -> str:
	candidate = _selected_candidate(trace_payload)
	domain = _humanize(candidate.get("business_domain"))
	if domain and domain != "unknown":
		return domain
	metrics = _missing_evidence_fields(trace_payload)
	return _sentence(metrics, limit=2)


def _safe_user_text_warnings(response_payload: Dict[str, Any]) -> List[str]:
	if not bool(response_payload.get("safe_to_show")):
		return []
	text_parts = [_clean_text(response_payload.get("title")), _clean_text(response_payload.get("answer_text"))]
	text_parts.extend(_clean_list(response_payload.get("next_steps")))
	full_text = " ".join(text_parts).lower()
	return [
		f"user_text_internal_term:{term}"
		for term in sorted(INTERNAL_USER_TEXT_TERMS)
		if term in full_text
	]


def _missing_evidence_fields(trace_payload: Dict[str, Any]) -> List[str]:
	trace = _clean_dict(trace_payload)
	evidence = _clean_dict(trace.get("evidence_plan"))
	requery = _clean_dict(trace.get("governed_requery_plan"))
	candidate = _selected_candidate(trace)
	values: List[str] = []
	values.extend(_clean_list(evidence.get("missing_fields")))
	values.extend(_clean_list(requery.get("missing_fields")))
	values.extend(_clean_list(candidate.get("requested_metrics")))
	values.extend(_clean_list(candidate.get("requested_dimensions")))
	return list(dict.fromkeys([_humanize(value) for value in values if _humanize(value)]))


def _missing_evidence_phrase(trace_payload: Dict[str, Any]) -> str:
	fields = _missing_evidence_fields(trace_payload)
	return _sentence(fields, limit=3) or "the requested evidence"


def _render_boundary(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	authority = _clean_dict(_clean_dict(trace_payload).get("authority_plan"))
	requery = _clean_dict(_clean_dict(trace_payload).get("governed_requery_plan"))
	authority_class = _humanize(authority.get("authority_class")) or "that decision"
	alternatives = _alternative_lines(_clean_dict_list(requery.get("suggested_alternatives")))
	return {
		"title": "Decision Not Available Yet",
		"answer_text": (
			f"I can show the ERP facts we have, but I cannot safely provide {authority_class} "
			"until the required company rule or approved analysis exists."
		),
		"next_steps": alternatives or [
			"ask for the supporting ERP facts such as aging, overdue balance, payment history, or credit usage",
			"define the company rule for this decision before asking me to recommend, approve, or predict",
		],
		"boundary_class": _clean_text(authority.get("authority_class")) or "unknown",
	}


def _render_clarification(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	context = _clean_dict(_clean_dict(trace_payload).get("context_resolution"))
	options = _options_from_trace(trace_payload)
	if options:
		return {
			"title": "Clarification Needed",
			"answer_text": "I can help with that, but I need to know which option you mean before I continue.",
			"next_steps": options[:8],
			"boundary_class": "",
		}
	target_reference = _humanize(context.get("target_reference"))
	reference_text = f" for the {target_reference} reference" if target_reference and target_reference != "none" else ""
	return {
		"title": "Clarification Needed",
		"answer_text": f"I can help with that, but I need one more detail{reference_text} before I can answer safely.",
		"next_steps": ["name the customer, supplier, item, document, or row you want me to use"],
		"boundary_class": "",
	}


def _render_supported_options(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	options = _options_from_trace(trace_payload)
	return {
		"title": "Available ERP Options",
		"answer_text": "Here are the ERP options I can use next.",
		"next_steps": options[:8] or ["ask for a supported ERP report, entity, metric, or follow-up target"],
		"boundary_class": "",
	}


def _render_governed_query(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	requery = _clean_dict(_clean_dict(trace_payload).get("governed_requery_plan"))
	entity = _entity_label(trace_payload)
	reports = _clean_list(requery.get("target_report_names"))
	composites = _clean_list(requery.get("target_composite_family_ids"))
	kpis = _clean_list(requery.get("target_governed_kpi_ids"))
	targets = reports or composites or kpis or _clean_list(requery.get("target_capability_ids"))
	target_text = _sentence(targets, limit=3)
	entity_text = f" for {entity}" if entity else ""
	return {
		"title": "ERP Source Available",
		"answer_text": (
			f"I can answer that by using an approved ERP source{entity_text}."
			+ (f" The planned source is {target_text}." if target_text else "")
		),
		"next_steps": ["use the ERP source above to answer this request"],
		"boundary_class": "",
	}


def _render_out_of_scope(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	area = _business_area_phrase(trace_payload)
	area_text = f" If you meant this as an ERP question about {area}, please include the business entity, metric, or report." if area else ""
	return {
		"title": "Outside ERP Scope",
		"answer_text": (
			"I can help with ERP and business questions, but this request appears outside that scope."
			+ area_text
		),
		"next_steps": [
			"ask about a financial statement, AR/AP, sales, purchasing, inventory, customer, supplier, item, or invoice",
			"rephrase the request with the ERP report, entity, metric, or period you want",
		],
		"boundary_class": "out_of_scope",
	}


def _render_capability_guidance(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	targets = _candidate_targets(trace_payload)
	area = _business_area_phrase(trace_payload)
	area_text = f" For this request, the closest business area is {area}." if area else ""
	next_steps = targets[:5] or [
		"ask for a report",
		"ask about a customer, supplier, item, or invoice",
		"ask a follow-up about the current result",
	]
	return {
		"title": "What I Can Help With",
		"answer_text": (
			"I can help with ERP reporting, follow-up analysis, entity details, and evidence-based business questions."
			+ area_text
		),
		"next_steps": next_steps,
		"boundary_class": "",
	}


def _render_unsupported(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	requery = _clean_dict(_clean_dict(trace_payload).get("governed_requery_plan"))
	alternatives = _alternative_lines(_clean_dict_list(requery.get("suggested_alternatives")))
	missing_phrase = _missing_evidence_phrase(trace_payload)
	if alternatives:
		return {
			"title": "Nearest ERP Options",
			"answer_text": (
				f"I cannot prove {missing_phrase} from the answer above, "
				"but these nearby ERP options are available."
			),
			"next_steps": alternatives,
			"boundary_class": "unsupported_evidence",
		}
	return {
		"title": "Missing Data For This Answer",
		"answer_text": (
			f"I can help with this business area, but the answer above does not safely expose {missing_phrase}."
		),
		"next_steps": ["ask for an ERP report or source that includes that data", "provide a more specific metric, entity, or period"],
		"boundary_class": "unsupported_evidence",
	}


def render_nbu_professional_response(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	"""Render a business-natural response draft from an NBU trace.

	The renderer is pure and non-executing. It hides internal contract vocabulary
	from user-facing text while preserving technical status for audit and future
	activation gates.
	"""

	trace = _clean_dict(trace_payload)
	decision = _clean_dict(trace.get("conversation_action_decision"))
	requery = _clean_dict(trace.get("governed_requery_plan"))
	response_mode = _clean_text(decision.get("response_mode")) or "shadow_trace_only"
	action = _clean_text(decision.get("action")) or "observe_only"
	safe_to_show = response_mode not in {"shadow_trace_only", "direct_answer"} and action != "answer_from_current_artifact"
	if response_mode == "boundary" or action == "reject_with_boundary":
		body = _render_boundary(trace)
	elif _clean_text(requery.get("status")) == "unsupported":
		body = _render_unsupported(trace)
	elif response_mode == "clarification" or action == "ask_clarification":
		body = _render_clarification(trace)
	elif response_mode == "supported_options" or action == "show_supported_options":
		body = _render_supported_options(trace)
	elif response_mode == "governed_query" or action in {"execute_governed_requery", "execute_fresh_governed_query"}:
		if _clean_text(requery.get("status")) == "unsupported":
			body = _render_unsupported(trace)
		else:
			body = _render_governed_query(trace)
	elif response_mode == "out_of_scope" or action == "out_of_scope_response":
		body = _render_out_of_scope(trace)
	elif response_mode == "capability_guidance" or action == "answer_capability_question":
		body = _render_capability_guidance(trace)
	else:
		body = {
			"title": "NBU Shadow Trace",
			"answer_text": "I have a safe interpretation trace for this request, but live NBU response activation is not enabled yet.",
			"next_steps": ["continue through the existing governed assistant flow"],
			"boundary_class": "",
		}
	response_payload = {
		"type": "qwen_nbu_professional_response_contract",
		"contract_version": CONTRACT_VERSION,
		"response_mode": response_mode,
		"action": action,
		"title": body["title"],
		"answer_text": body["answer_text"],
		"next_steps": _clean_list(body.get("next_steps")),
		"boundary_class": _clean_text(body.get("boundary_class")),
		"safe_to_show": safe_to_show,
		"technical_details": _technical_summary(trace),
	}
	response_payload["quality_warnings"] = _safe_user_text_warnings(response_payload)
	return response_payload
