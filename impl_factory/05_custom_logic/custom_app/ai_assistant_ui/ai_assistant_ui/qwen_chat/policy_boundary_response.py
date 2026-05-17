from __future__ import annotations

from typing import Any, Dict, Iterable, List

from .natural_business_understanding_contracts import CONTRACT_VERSION


POLICY_BOUNDARY_RESPONSE_CONTRACT_TYPE = "qwen_policy_boundary_response_contract"
POLICY_BOUNDARY_RESPONSE_RENDERER_ID = "policy_boundary_natural_response_renderer"


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _clean_list(value: Any) -> List[Any]:
	return list(value) if isinstance(value, list) else []


def _limited_texts(values: Iterable[Any] | None, limit: int = 8) -> List[str]:
	return [_clean_text(value) for value in (values or []) if _clean_text(value)][:limit]


def _intent_class(boundary_contract: Dict[str, Any]) -> str:
	return _clean_text(_clean_dict(boundary_contract).get("policy_intent_class")) or "unsupported_scope"


def _boundary_class(intent_class: str) -> str:
	if intent_class == "recommendation_action":
		return "recommendation"
	if intent_class == "cause_attribution":
		return "cause"
	if intent_class == "risk_scoring":
		return "risk_scoring"
	if intent_class == "approval_decision":
		return "approval"
	if intent_class == "prediction":
		return "prediction"
	return intent_class or "unsupported_scope"


def _subject_phrase(*, rank_text: str, entity_label: str) -> str:
	rank = _clean_text(rank_text)
	label = _clean_text(entity_label)
	if rank and label:
		return f"{rank} ({label})"
	return label or rank or "the selected row"


def _visible_fact_lines(boundary_contract: Dict[str, Any], metric_lines: Iterable[Any] | None) -> List[str]:
	lines = _limited_texts(metric_lines, 10)
	if lines:
		return lines
	return _limited_texts(_clean_dict(boundary_contract).get("allowed_visible_facts"), 10)


def _missing_authority_phrase(boundary_contract: Dict[str, Any], intent_class: str) -> str:
	contract = _clean_dict(boundary_contract)
	parts: List[str] = []
	if bool(contract.get("approved_model_required")):
		parts.append("an approved model")
	if bool(contract.get("approved_policy_required")):
		parts.append("an approved company decision rule")
	if bool(contract.get("approved_trend_required")):
		parts.append("trend or event-history evidence")
	if not parts:
		available = _clean_dict(contract.get("available_evidence_scope"))
		missing_metrics = _limited_texts(available.get("missing_metrics"), 3)
		missing_artifacts = _limited_texts(available.get("missing_artifacts"), 3)
		if missing_metrics:
			parts.append("the missing evidence metrics")
		if missing_artifacts:
			parts.append("the missing supporting view")
	if not parts:
		if intent_class == "prediction":
			parts.extend(["an approved model", "payment-behavior evidence"])
		elif intent_class == "recommendation_action":
			parts.append("an approved company decision rule")
		elif intent_class == "cause_attribution":
			parts.append("trend or event-history evidence")
		elif intent_class == "risk_scoring":
			parts.append("an approved scoring model")
		elif intent_class == "approval_decision":
			parts.append("an approved approval rule")
		else:
			parts.append("the required supporting evidence")
	if len(parts) == 1:
		return parts[0]
	if len(parts) == 2:
		return f"{parts[0]} and {parts[1]}"
	return ", ".join(parts[:-1]) + f", and {parts[-1]}"


def _boundary_intro(intent_class: str) -> str:
	if intent_class == "prediction":
		return "I can't forecast that outcome from the current table alone."
	if intent_class == "recommendation_action":
		return "I can't recommend a business action from the current table alone."
	if intent_class == "cause_attribution":
		return "I can't attribute cause from this point-in-time table alone."
	if intent_class == "risk_scoring":
		return "I can't assign a risk score from the current table alone."
	if intent_class == "approval_decision":
		return "I can't approve or block a business decision from the current table alone."
	return "I can't make that business judgement from the current evidence alone."


def _supporting_sentence(intent_class: str, subject: str) -> str:
	if intent_class == "prediction":
		return f"The visible table supports risk review for {subject}, but it does not prove a future payment outcome."
	if intent_class == "recommendation_action":
		return f"The visible table supports comparison for {subject}, but it does not authorize a collection, payment, or blocking action."
	if intent_class == "cause_attribution":
		return f"The visible table supports a current reading for {subject}, but it does not show what changed or why."
	if intent_class == "risk_scoring":
		return f"The visible table supports indicator review for {subject}, but it does not contain an approved scoring model."
	if intent_class == "approval_decision":
		return f"The visible table supports evidence review for {subject}, but it does not authorize an approval or block decision."
	return f"The visible table supports evidence review for {subject}, but not the requested judgement."


def _next_step_sentence(intent_class: str, missing_phrase: str) -> str:
	if intent_class == "prediction":
		return f"To answer this as a forecast, we would need {missing_phrase}."
	if intent_class == "recommendation_action":
		return f"To recommend an action, we would need {missing_phrase}."
	if intent_class == "cause_attribution":
		return f"To explain cause or change, we would need {missing_phrase}."
	if intent_class == "risk_scoring":
		return f"To assign a risk score, we would need {missing_phrase}."
	if intent_class == "approval_decision":
		return f"To make an approval or blocking decision, we would need {missing_phrase}."
	return f"To answer that safely, we would need {missing_phrase}."


def _safe_next_steps(boundary_contract: Dict[str, Any], intent_class: str, missing_phrase: str) -> List[str]:
	values = _limited_texts(_clean_dict(boundary_contract).get("safe_alternative_actions"), 3)
	if values:
		return values
	if intent_class == "prediction":
		return ["Review the current ERP facts.", f"Use {missing_phrase} before forecasting."]
	if intent_class == "recommendation_action":
		return ["Compare the visible rows by the metrics shown.", f"Use {missing_phrase} before recommending action."]
	if intent_class == "cause_attribution":
		return ["Review current visible facts.", f"Use {missing_phrase} before attributing cause."]
	if intent_class == "risk_scoring":
		return ["Review current risk indicators.", f"Use {missing_phrase} before assigning a score."]
	if intent_class == "approval_decision":
		return ["Review the supporting ERP facts.", f"Use {missing_phrase} before making an approval decision."]
	return ["Review the current ERP facts.", f"Use {missing_phrase} before making the judgement."]


def render_policy_boundary_response(
	boundary_contract: Dict[str, Any],
	*,
	rank_text: str = "",
	entity_label: str = "",
	metric_lines: Iterable[Any] | None = None,
) -> Dict[str, Any]:
	contract = _clean_dict(boundary_contract)
	intent_class = _intent_class(contract)
	subject = _subject_phrase(rank_text=rank_text, entity_label=entity_label)
	facts = _visible_fact_lines(contract, metric_lines)
	missing_phrase = _missing_authority_phrase(contract, intent_class)
	lines = [
		_boundary_intro(intent_class),
		_supporting_sentence(intent_class, subject),
	]
	if facts:
		label = _clean_text(entity_label) or subject
		lines.extend(["", f"Visible facts for {label}:"])
		lines.extend(facts)
	lines.extend(["", _next_step_sentence(intent_class, missing_phrase)])
	return {
		"type": POLICY_BOUNDARY_RESPONSE_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"renderer_id": POLICY_BOUNDARY_RESPONSE_RENDERER_ID,
		"title": "Evidence Limit",
		"answer_text": "\n".join(lines).strip(),
		"next_steps": _safe_next_steps(contract, intent_class, missing_phrase),
		"boundary_class": _boundary_class(intent_class),
		"policy_intent_class": intent_class,
	}


def render_policy_boundary_text(
	boundary_contract: Dict[str, Any],
	*,
	rank_text: str = "",
	entity_label: str = "",
	metric_lines: Iterable[Any] | None = None,
) -> str:
	return _clean_text(
		render_policy_boundary_response(
			boundary_contract,
			rank_text=rank_text,
			entity_label=entity_label,
			metric_lines=metric_lines,
		).get("answer_text")
	)
