from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.business_reasoning_policy import (
	render_business_reasoning_policy_boundary_answer,
)
from ai_assistant_ui.qwen_chat.business_language_guards import (
	looks_like_predictive_guarantee_claim,
	looks_like_unsupported_operational_inference_claim,
)
from ai_assistant_ui.qwen_chat.contracts import (
	build_erp_business_reasoning_contract,
)
from ai_assistant_ui.qwen_chat.evidence_expansion_support import (
	build_evidence_expansion_plan,
	evidence_expansion_user_guidance,
)
from ai_assistant_ui.qwen_chat.runtime_client import (
	QwenRuntimeClientError,
	call_qwen_runtime_reasoning_render,
)

try:
	import frappe  # type: ignore
except Exception:  # pragma: no cover
	frappe = None


@dataclass(frozen=True)
class ERPBusinessReasoningExecutionResult:
	status: str
	answer_text: str = ""
	reasoning_contract: Dict[str, Any] = field(default_factory=dict)
	runtime_error: str = ""
	validation_error: str = ""
	agent_meta: Dict[str, Any] = field(default_factory=dict)

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_erp_business_reasoning_execution",
			"contract_version": "1.0",
			"status": self.status,
			"answer_text": self.answer_text,
			"runtime_error": self.runtime_error,
			"validation_error": self.validation_error,
			"reasoning_contract": dict(self.reasoning_contract or {}),
			"agent_meta": dict(self.agent_meta or {}),
		}


def _site_name() -> str:
	if frappe is None:
		return ""
	return str(getattr(getattr(frappe, "local", None), "site", "") or "").strip()


_NUMBER_RE = re.compile(r"(?<![A-Za-z0-9_])-?\d[\d,]*(?:\.\d+)?%?")
_TABLE_COLUMN_DELIMITER = chr(9)
_MARKDOWN_TABLE_DELIMITER = chr(124)


def _normalize_numeric_evidence_text(text: str) -> str:
	# Governed artifacts often encode numeric business labels as keys such as
	# 61_90 or bucket_121_above. Normalize only underscores adjacent to digits
	# so evidence validation sees those label numbers without opening free-form text.
	return re.sub(r"(?<=\d)_|_(?=\d)", " ", str(text or ""))


def _normalize_number_token(value: str) -> str:
	raw = str(value or "").strip()
	if not raw:
		return ""
	cleaned = raw.rstrip("%").replace(",", "").strip()
	if not cleaned:
		return ""
	try:
		decimal_value = Decimal(cleaned)
	except (InvalidOperation, ValueError):
		return ""
	normalized = format(decimal_value.normalize(), "f")
	if "." in normalized:
		normalized = normalized.rstrip("0").rstrip(".")
	return normalized or "0"


def _number_variants_for_decimal(decimal_value: Decimal) -> List[str]:
	variants = set()
	normalized = format(decimal_value.normalize(), "f")
	if "." in normalized:
		normalized = normalized.rstrip("0").rstrip(".")
	if normalized:
		variants.add(normalized)
	if abs(decimal_value) >= Decimal("1000000"):
		million_value = decimal_value / Decimal("1000000")
		for scale in (0, 1, 2, 3, 4):
			quantizer = Decimal("1") if scale == 0 else Decimal("1").scaleb(-scale)
			scaled = million_value.quantize(quantizer, rounding=ROUND_HALF_UP)
			scaled_text = format(scaled.normalize(), "f")
			if "." in scaled_text:
				scaled_text = scaled_text.rstrip("0").rstrip(".")
			if scaled_text:
				variants.add(scaled_text)
	return sorted(variants)


def _number_token_variants(value: str) -> List[str]:
	normalized = _normalize_number_token(value)
	if not normalized:
		return []
	try:
		decimal_value = Decimal(str(value or "").rstrip("%").replace(",", "").strip())
	except (InvalidOperation, ValueError):
		return [normalized]
	return _number_variants_for_decimal(decimal_value)


def _extract_number_tokens_from_text(text: str) -> List[str]:
	tokens = set()
	for match in _NUMBER_RE.findall(_normalize_numeric_evidence_text(text)):
		tokens.update(_number_token_variants(match))
	return sorted(tokens)


def _extract_decimal_values_from_text(text: str) -> List[str]:
	values: List[str] = []
	seen = set()
	for match in _NUMBER_RE.findall(_normalize_numeric_evidence_text(text)):
		cleaned = str(match or "").rstrip("%").replace(",", "").strip()
		if not cleaned:
			continue
		try:
			decimal_value = Decimal(cleaned)
		except (InvalidOperation, ValueError):
			continue
		normalized = format(decimal_value.normalize(), "f")
		if "." in normalized:
			normalized = normalized.rstrip("0").rstrip(".")
		if normalized and normalized not in seen:
			seen.add(normalized)
			values.append(normalized)
	return values


def _collect_evidence_fragments(value: Any, *, limit: int = 220, max_fragment_length: int = 360) -> List[str]:
	fragments: List[str] = []

	def visit(obj: Any, path: str = "") -> None:
		if len(fragments) >= limit:
			return
		if isinstance(obj, dict):
			for key, item in obj.items():
				if len(fragments) >= limit:
					return
				key_text = str(key or "").strip()
				next_path = key_text or path
				if isinstance(item, (dict, list, tuple)):
					visit(item, next_path)
				else:
					item_text = str(item if item is not None else "").strip()
					if item_text:
						fragment = f"{next_path}: {item_text}" if next_path else item_text
						fragments.append(fragment[:max_fragment_length])
			return
		if isinstance(obj, (list, tuple)):
			for item in obj:
				if len(fragments) >= limit:
					return
				visit(item, path)
			return
		text = str(obj if obj is not None else "").strip()
		if text:
			fragments.append(text[:max_fragment_length])

	visit(value)
	deduped: List[str] = []
	seen = set()
	for fragment in fragments:
		if fragment in seen:
			continue
		seen.add(fragment)
		deduped.append(fragment)
	return deduped


def _visible_text_from_payload(
	*,
	latest_assistant_payload: Dict[str, Any],
	recent_assistant_text: str = "",
) -> str:
	payload = dict(latest_assistant_payload or {})
	parts = [
		str(payload.get("answer_text") or "").strip(),
		str(payload.get("text") or "").strip(),
		str(recent_assistant_text or "").strip(),
	]
	seen = set()
	out: List[str] = []
	for part in parts:
		if not part or part in seen:
			continue
		seen.add(part)
		out.append(part)
	return "\n".join(out)[:12000]


def _build_evidence_catalog(
	*,
	activation_contract: Dict[str, Any],
	latest_grounded_turn: Dict[str, Any],
	latest_family_artifact: Dict[str, Any],
	latest_assistant_payload: Dict[str, Any],
	recent_assistant_text: str = "",
) -> Dict[str, Any]:
	visible_text_source = _visible_text_from_payload(
		latest_assistant_payload=latest_assistant_payload,
		recent_assistant_text=recent_assistant_text,
	)
	visible_fragments = _collect_evidence_fragments(
		{
			"latest_assistant_payload": latest_assistant_payload,
			"recent_assistant_text": visible_text_source,
		},
		limit=160,
	)
	full_fragments = _collect_evidence_fragments(
		{
			"activation_contract": activation_contract,
			"latest_grounded_turn": latest_grounded_turn,
			"latest_family_artifact": latest_family_artifact,
			"latest_assistant_payload": latest_assistant_payload,
			"recent_assistant_text": visible_text_source,
		},
		limit=260,
	)
	visible_text = "\n".join([*visible_fragments, visible_text_source])
	full_text = "\n".join(full_fragments)
	visible_numbers = set(_extract_number_tokens_from_text(visible_text))
	full_numbers = set(_extract_number_tokens_from_text(full_text))
	return {
		"visible_fragments": visible_fragments[:80],
		"visible_text_excerpt": visible_text_source,
		"grounded_fragments": full_fragments[:160],
		"visible_number_tokens": sorted(visible_numbers),
		"grounded_number_tokens": sorted(full_numbers),
		"visible_numeric_values": _extract_decimal_values_from_text(visible_text),
		"grounded_numeric_values": _extract_decimal_values_from_text(full_text),
		"numeric_grounding_mode": "visible_result_first" if visible_numbers else "grounded_context",
	}


def _latest_recent_assistant_text(recent_messages: List[Dict[str, str]] | None) -> str:
	for message in reversed(list(recent_messages or [])):
		if not isinstance(message, dict):
			continue
		if str(message.get("role") or "").strip().lower() != "assistant":
			continue
		content = str(message.get("content") or "").strip()
		if content:
			return content[:12000]
	return ""


def _build_reasoning_context(
	*,
	activation_contract: Dict[str, Any],
	semantic_activation_result: Dict[str, Any],
	latest_grounded_turn: Dict[str, Any],
	latest_family_artifact: Dict[str, Any],
	latest_assistant_payload: Dict[str, Any],
	recent_messages: List[Dict[str, str]] | None = None,
	presentation_preferences: Dict[str, Any] | None = None,
	prior_reasoning_contract: Dict[str, Any] | None = None,
	prior_answer_text: str = "",
) -> Dict[str, Any]:
	intent = dict(semantic_activation_result.get("intent") or {})
	grounding_summary = dict(activation_contract.get("grounding_summary") or {})
	grounded_turn = dict(latest_grounded_turn or {})
	family_artifact = dict(latest_family_artifact or {})
	assistant_payload = dict(latest_assistant_payload or {})
	grounded_findings: List[str] = []
	for row in list(grounded_turn.get("table_rows") or [])[:5]:
		if not isinstance(row, dict):
			continue
		pairs = [
			f"{str(key or '').strip()}: {str(value or '').strip()}"
			for key, value in row.items()
			if str(key or "").strip() and str(value or "").strip()
		]
		if pairs:
			grounded_findings.append("; ".join(pairs[:4]))
	report_name = str(activation_contract.get("grounded_source_name") or grounded_turn.get("source_name") or "").strip()
	if report_name:
		grounding_summary.setdefault("report_name", report_name)
	title = str(assistant_payload.get("title") or "").strip()
	if title:
		grounding_summary.setdefault("latest_assistant_title", title)
	evidence_catalog = _build_evidence_catalog(
		activation_contract=activation_contract,
		latest_grounded_turn=grounded_turn,
		latest_family_artifact=family_artifact,
		latest_assistant_payload=assistant_payload,
		recent_assistant_text=_latest_recent_assistant_text(recent_messages),
	)
	context = {
		"reasoning_type": str(intent.get("reasoning_type") or "").strip(),
		"detail_level": str(intent.get("detail_level") or "default").strip() or "default",
		"presentation_style": str(intent.get("presentation_style") or "default").strip() or "default",
		"consultant_response_mode": str(intent.get("response_mode") or "factual_grounded_answer").strip()
		or "factual_grounded_answer",
		"evidence_policy": str(intent.get("evidence_policy") or "current_result_only").strip()
		or "current_result_only",
		"answer_obligation": str(intent.get("answer_obligation") or "explain_grounded_meaning").strip()
		or "explain_grounded_meaning",
		"bounded_domain": "erp_business_reasoning",
		"recommendation_allowed": bool(activation_contract.get("recommendation_allowed")),
		"recommendation_policy_basis": [
			str(value or "").strip()
			for value in (activation_contract.get("recommendation_policy_basis") or [])
			if str(value or "").strip()
		],
		"grounding_summary": grounding_summary,
		"grounded_source": {
			"source_kind": str(activation_contract.get("grounded_source_kind") or "").strip(),
			"source_name": report_name,
			"family_id": str(activation_contract.get("grounded_family_id") or family_artifact.get("family_id") or "").strip(),
			"artifact_type": str(activation_contract.get("grounded_artifact_type") or family_artifact.get("artifact_type") or "").strip(),
			"source_reports": [
				str(value or "").strip()
				for value in (activation_contract.get("grounded_source_reports") or family_artifact.get("source_reports") or [])
				if str(value or "").strip()
			],
			"source_report_count": int(
				len(
					[
						str(value or "").strip()
						for value in (activation_contract.get("grounded_source_reports") or family_artifact.get("source_reports") or [])
						if str(value or "").strip()
					]
				)
			),
			"composite_grounding": bool(
				len(
					[
						str(value or "").strip()
						for value in (activation_contract.get("grounded_source_reports") or family_artifact.get("source_reports") or [])
						if str(value or "").strip()
					]
				)
				> 1
			),
			"capability_id": str(activation_contract.get("grounded_capability_id") or family_artifact.get("capability_id") or "").strip(),
		},
		"grounded_findings": grounded_findings,
		"grounded_rows": [dict(row) for row in list(grounded_turn.get("table_rows") or [])[:40] if isinstance(row, dict)],
		"evidence_catalog": evidence_catalog,
		"artifact_metrics": dict(family_artifact.get("metrics") or {}) if isinstance(family_artifact.get("metrics"), dict) else {},
		"artifact_sections": dict(family_artifact.get("sections") or {}) if isinstance(family_artifact.get("sections"), dict) else {},
		"table_schema": [str(value or "").strip() for value in (grounded_turn.get("returned_schema") or []) if str(value or "").strip()],
		"row_count": int(grounded_turn.get("row_count") or 0),
		"presentation_preferences": dict(presentation_preferences or {}),
	}
	prior_contract = dict(prior_reasoning_contract or {})
	if prior_contract:
		context["prior_reasoning"] = {
			"reasoning_type": str(prior_contract.get("reasoning_type") or "").strip(),
			"reason": str(prior_contract.get("reason") or "").strip(),
			"supported_claims": [dict(item) for item in (prior_contract.get("supported_claims") or []) if isinstance(item, dict)],
			"recommendations": [dict(item) for item in (prior_contract.get("recommendations") or []) if isinstance(item, dict)],
			"offered_next_actions": [dict(item) for item in (prior_contract.get("offered_next_actions") or []) if isinstance(item, dict)],
			"speculation_flags": [str(item or "").strip() for item in (prior_contract.get("speculation_flags") or []) if str(item or "").strip()],
			"answer_text": str(prior_answer_text or "").strip(),
		}
	elif str(prior_answer_text or "").strip():
		context["prior_grounded_answer"] = {
			"answer_text": str(prior_answer_text or "").strip(),
			"source_name": report_name,
			"family_id": context["grounded_source"]["family_id"],
			"grounding_mode": "grounded_answer_continuation",
		}
	return context


def build_reasoning_boundary_answer(
	*,
	execution_result: ERPBusinessReasoningExecutionResult,
	activation_contract: Dict[str, Any],
	semantic_activation_result: Dict[str, Any],
) -> str:
	intent = dict(semantic_activation_result.get("intent") or {})
	reasoning_type = str(intent.get("reasoning_type") or "").strip()
	source_name = str(activation_contract.get("grounded_source_name") or "").strip()
	source_label = source_name or "the answer above"
	grounding_gaps = {
		str(item or "").strip()
		for item in ((execution_result.reasoning_contract or {}).get("grounding_gaps") or [])
		if str(item or "").strip()
	}
	if execution_result.status == "insufficient_grounding" and "predictive_guarantee_requires_governed_policy" in grounding_gaps:
		return (
			f"I can't answer it safely as a guarantee or prediction from {source_label}. "
			"The current ERP data can support facts and explanations, but it does not include an approved prediction policy, "
			"payment-commitment evidence, or collection/default model needed to say who will pay or default. "
			"Please ask for the current ERP facts, aging breakdown, or an approved prediction or collections policy first."
		)
	if execution_result.status == "insufficient_grounding" and "unsupported_operational_inference_requires_governed_evidence" in grounding_gaps:
		return (
			f"I can't answer that safely as a causal or subjective operational inference from {source_label}. "
			"The current ERP data can show recorded facts, but it does not include customer sentiment, complaint, dispute, "
			"or delay-reason evidence needed to infer dissatisfaction or intent. Please ask for the recorded fields, "
			"or use a complaint, dispute, or delay-reason view first."
		)
	grounding_summary = activation_contract.get("grounding_summary") if isinstance(activation_contract.get("grounding_summary"), dict) else {}
	policy_boundary_answer = render_business_reasoning_policy_boundary_answer(
		dict(grounding_summary.get("business_reasoning_authority_policy") or {})
	)
	if policy_boundary_answer:
		return policy_boundary_answer
	if execution_result.status == "insufficient_grounding":
		if (
			reasoning_type in {"recommendation", "continuation_detail"}
			and not bool(activation_contract.get("recommendation_allowed"))
		):
			return (
				f"I can explain {source_label}, but I can't safely give management recommendations from this result alone. "
				"This is a detailed operational view, so recommendations should come from an approved summary or analysis view first."
			)
		if "prior_reasoning_source_mismatch" in grounding_gaps or "prior_reasoning_report_mismatch" in grounding_gaps:
			return (
				"I can't safely continue that prior recommendation because the current ERP context no longer matches the original analysis. "
				"Please return to the original analysis or ask for a fresh summary before continuing."
			)
		return (
			f"I couldn't safely complete that ERP explanation from {source_label} without going beyond the available data. "
			"Please ask for a broader summary or reframe the question around the current result."
		)
	if execution_result.status in {"invalid_payload", "runtime_error"}:
		return (
			f"I stopped rather than guess because I couldn't safely generate a bounded reasoning answer from {source_label} just now. "
			"Please try the follow-up again or ask for a summary view."
		)
	return (
		f"I couldn't safely continue reasoning from {source_label}. "
		"Please ask for a summary view or a narrower explanation request."
	)


_EXPANSION_EVIDENCE_POLICIES = {"evidence_expansion_preferred", "evidence_expansion_required"}
_CONSULTANT_EXPANSION_RESPONSE_MODES = {"consultant_detail", "consultant_interpretation"}


def _has_current_grounding_identity(
	*,
	activation_contract: Dict[str, Any],
	latest_grounded_turn: Dict[str, Any],
) -> bool:
	if str(activation_contract.get("grounded_source_request_id") or latest_grounded_turn.get("trace_request_id") or "").strip():
		return True
	if str(activation_contract.get("grounded_source_name") or latest_grounded_turn.get("source_name") or "").strip():
		return True
	for value in (activation_contract.get("grounded_source_reports") or latest_grounded_turn.get("artifact_source_reports") or []):
		if str(value or "").strip():
			return True
	return False


def _prior_grounded_answer_continuation_allowed(
	*,
	activation_contract: Dict[str, Any],
	semantic_activation_result: Dict[str, Any],
	latest_grounded_turn: Dict[str, Any],
	prior_answer_text: str,
) -> bool:
	intent = dict(semantic_activation_result.get("intent") or {})
	if str(intent.get("reasoning_type") or "").strip() != "continuation_detail":
		return False
	if str(intent.get("evidence_policy") or "").strip() not in _EXPANSION_EVIDENCE_POLICIES:
		return False
	if str(intent.get("answer_obligation") or "").strip() != "expand_grounded_detail":
		return False
	if str(intent.get("response_mode") or "").strip() not in _CONSULTANT_EXPANSION_RESPONSE_MODES:
		return False
	if not str(prior_answer_text or "").strip():
		return False
	return _has_current_grounding_identity(
		activation_contract=activation_contract,
		latest_grounded_turn=latest_grounded_turn,
	)


def _continuation_compatible(
	*,
	activation_contract: Dict[str, Any],
	semantic_activation_result: Dict[str, Any],
	latest_grounded_turn: Dict[str, Any],
	prior_reasoning_contract: Dict[str, Any],
	prior_answer_text: str = "",
) -> tuple[bool, List[str]]:
	gaps: List[str] = []
	prior_contract = dict(prior_reasoning_contract or {})
	if not prior_contract:
		if _prior_grounded_answer_continuation_allowed(
			activation_contract=activation_contract,
			semantic_activation_result=semantic_activation_result,
			latest_grounded_turn=latest_grounded_turn,
			prior_answer_text=prior_answer_text,
		):
			return True, gaps
		gaps.append("missing_prior_reasoning_contract")
		return False, gaps
	if not bool(prior_contract.get("allowed_to_answer")):
		gaps.append("prior_reasoning_not_answerable")
	if not bool(prior_contract.get("grounding_sufficient")):
		gaps.append("prior_reasoning_insufficient_grounding")
	prior_source_request_id = str(prior_contract.get("grounding_source_request_id") or "").strip()
	current_source_request_id = str(
		activation_contract.get("grounded_source_request_id")
		or latest_grounded_turn.get("trace_request_id")
		or latest_grounded_turn.get("request_id")
		or ""
	).strip()
	if prior_source_request_id and current_source_request_id and prior_source_request_id != current_source_request_id:
		gaps.append("prior_reasoning_source_mismatch")
	prior_family_id = str(prior_contract.get("grounding_family_id") or "").strip()
	current_family_id = str(
		activation_contract.get("grounded_family_id")
		or latest_grounded_turn.get("artifact_family_id")
		or ""
	).strip()
	if prior_family_id and current_family_id and prior_family_id != current_family_id:
		gaps.append("prior_reasoning_family_mismatch")
	prior_reports = {
		str(value or "").strip()
		for value in (prior_contract.get("grounding_source_reports") or [])
		if str(value or "").strip()
	}
	current_reports = {
		str(value or "").strip()
		for value in (activation_contract.get("grounded_source_reports") or latest_grounded_turn.get("artifact_source_reports") or [])
		if str(value or "").strip()
	}
	if prior_reports and current_reports and prior_reports != current_reports:
		gaps.append("prior_reasoning_report_mismatch")
	return (not gaps, gaps)


def _answer_text_is_incomplete(answer_text: str) -> bool:
	text = str(answer_text or "").strip()
	if not text:
		return True
	# A dangling lead-in is not an acceptable fulfilled reasoning answer.
	if text.endswith(":"):
		return True
	return False


def _payload_text_for_grounding(payload: Dict[str, Any]) -> str:
	parts = [str(payload.get("answer_text") or "").strip()]
	for item in payload.get("supported_claims") or []:
		if not isinstance(item, dict):
			continue
		parts.append(str(item.get("claim") or "").strip())
		parts.append(str(item.get("support") or "").strip())
	for item in payload.get("recommendations") or []:
		if not isinstance(item, dict):
			continue
		parts.append(str(item.get("action") or "").strip())
		parts.append(str(item.get("rationale") or "").strip())
	return "\n".join(part for part in parts if part)


def _parse_decimal_token(value: str) -> Decimal | None:
	try:
		return Decimal(str(value or "").strip())
	except (InvalidOperation, ValueError):
		return None


def _rounded_decimal_tokens(value: Decimal, *, max_scale: int = 4) -> set[str]:
	tokens = set()
	for scale in range(0, max_scale + 1):
		quantizer = Decimal("1") if scale == 0 else Decimal("1").scaleb(-scale)
		rounded = value.quantize(quantizer, rounding=ROUND_HALF_UP)
		text = format(rounded.normalize(), "f")
		if "." in text:
			text = text.rstrip("0").rstrip(".")
		if text:
			tokens.add(text)
	return tokens


def _number_token_is_derived_from_evidence(token: str, evidence_numeric_values: List[str]) -> bool:
	target = _parse_decimal_token(token)
	if target is None:
		return False
	values: List[Decimal] = []
	for item in evidence_numeric_values[:80]:
		parsed = _parse_decimal_token(item)
		if parsed is not None:
			values.append(parsed)
	if not values:
		return False
	large_values = [value for value in values if abs(value) >= Decimal("1000000")][:36]
	candidate_values: List[Decimal] = []
	for value in large_values:
		candidate_values.append(value / Decimal("1000000"))
	ratio_values = [value for value in values if Decimal("-1") <= value <= Decimal("1")][:36]
	for value in ratio_values:
		candidate_values.append(value * Decimal("100"))
	for candidate in candidate_values:
		if token in _rounded_decimal_tokens(candidate, max_scale=4):
			return True
	return False


def _unsupported_payload_number_tokens(
	*,
	payload: Dict[str, Any],
	grounding_context: Dict[str, Any] | None = None,
	verified_numeric_values: List[str] | None = None,
) -> List[str]:
	context = dict(grounding_context or {})
	catalog = context.get("evidence_catalog") if isinstance(context.get("evidence_catalog"), dict) else {}
	visible_tokens = {
		str(item or "").strip()
		for item in (catalog.get("visible_number_tokens") or [])
		if str(item or "").strip()
	}
	grounded_tokens = {
		str(item or "").strip()
		for item in (catalog.get("grounded_number_tokens") or [])
		if str(item or "").strip()
	}
	allowed_tokens = visible_tokens.union(grounded_tokens)
	for item in verified_numeric_values or []:
		for token in _extract_number_tokens_from_text(str(item or "")):
			allowed_tokens.add(token)
	if not allowed_tokens:
		return []
	evidence_numeric_values = [
		str(item or "").strip()
		for item in [
			*(catalog.get("visible_numeric_values") or []),
			*(catalog.get("grounded_numeric_values") or []),
			*(verified_numeric_values or []),
		]
		if str(item or "").strip()
	]
	output_tokens = set(_extract_number_tokens_from_text(_payload_text_for_grounding(payload)))
	return sorted(
		token
		for token in output_tokens
		if token not in allowed_tokens
		and not _number_token_is_derived_from_evidence(token, evidence_numeric_values)
	)


def _grounding_sufficient(
	*,
	activation_contract: Dict[str, Any],
	semantic_activation_result: Dict[str, Any],
	latest_grounded_turn: Dict[str, Any],
	prior_reasoning_contract: Dict[str, Any] | None = None,
	prior_answer_text: str = "",
) -> tuple[bool, List[str]]:
	gaps: List[str] = []
	if str(activation_contract.get("activation_state") or "").strip() != "eligible":
		gaps.append("reasoning_not_eligible")
	if str(semantic_activation_result.get("status") or "").strip() != "accepted":
		gaps.append("semantic_activation_not_accepted")
	intent = dict(semantic_activation_result.get("intent") or {})
	reasoning_type = str(intent.get("reasoning_type") or "").strip()
	if not reasoning_type:
		gaps.append("missing_reasoning_type")
	allowed_types = {
		str(value or "").strip()
		for value in (activation_contract.get("allowed_reasoning_types") or [])
		if str(value or "").strip()
	}
	if reasoning_type and reasoning_type not in allowed_types:
		gaps.append("reasoning_type_not_allowed")
	if reasoning_type == "recommendation" and not bool(activation_contract.get("recommendation_allowed")):
		gaps.append("recommendation_policy_not_allowed")
	grounding_summary = activation_contract.get("grounding_summary") if isinstance(activation_contract.get("grounding_summary"), dict) else {}
	authority_policy = grounding_summary.get("business_reasoning_authority_policy")
	if isinstance(authority_policy, dict) and str(authority_policy.get("policy_state") or "").strip() == "blocked":
		gaps.append("business_reasoning_policy_blocked_variation")
	if not bool(latest_grounded_turn.get("grounded")):
		gaps.append("missing_grounded_turn")
	if reasoning_type == "continuation_detail":
		compatible, continuation_gaps = _continuation_compatible(
			activation_contract=activation_contract,
			semantic_activation_result=semantic_activation_result,
			latest_grounded_turn=latest_grounded_turn,
			prior_reasoning_contract=dict(prior_reasoning_contract or {}),
			prior_answer_text=prior_answer_text,
		)
		if not compatible:
			gaps.extend(continuation_gaps)
	return (not gaps, gaps)


def _insufficient_grounding_result(
	*,
	request_id: str,
	session_id: str,
	reasoning_type: str,
	activation_contract: Dict[str, Any],
	grounding_gaps: List[str],
	reason: str,
) -> ERPBusinessReasoningExecutionResult:
	contract = build_erp_business_reasoning_contract(
		request_id=request_id,
		session_id=session_id,
		reasoning_type=reasoning_type,
		grounding_source_request_id=str(activation_contract.get("grounded_source_request_id") or "").strip(),
		grounding_source_kind=str(activation_contract.get("grounded_source_kind") or "").strip(),
		grounding_family_id=str(activation_contract.get("grounded_family_id") or "").strip(),
		grounding_artifact_type=str(activation_contract.get("grounded_artifact_type") or "").strip(),
		grounding_source_reports=list(activation_contract.get("grounded_source_reports") or []),
		grounding_sufficient=False,
		grounding_gaps=grounding_gaps,
		bounded_domain="erp_business_reasoning",
		reasoning_scope="grounded_only",
		supported_claims=[],
		recommendations=[],
		speculation_flags=[],
		allowed_to_answer=False,
		reason=reason,
		confidence=0.0,
	)
	return ERPBusinessReasoningExecutionResult(
		status="insufficient_grounding",
		reasoning_contract=contract.to_payload(),
		validation_error=reason,
	)


def _validate_runtime_payload(
	*,
	payload: Dict[str, Any],
	reasoning_type: str,
	activation_contract: Dict[str, Any],
	presentation_preferences: Dict[str, Any] | None = None,
	grounding_context: Dict[str, Any] | None = None,
	verified_numeric_values: List[str] | None = None,
) -> tuple[bool, str]:
	if not isinstance(payload, dict):
		return False, "Runtime reasoning renderer returned invalid payload."
	answer_text = str(payload.get("answer_text") or "").strip()
	if _answer_text_is_incomplete(answer_text):
		return False, "Runtime reasoning renderer returned no answer text."
	supported_claims = payload.get("supported_claims") or []
	if not isinstance(supported_claims, list):
		return False, "Runtime reasoning renderer returned invalid supported_claims."
	recommendations = payload.get("recommendations") or []
	if not isinstance(recommendations, list):
		return False, "Runtime reasoning renderer returned invalid recommendations."
	speculation_flags = payload.get("speculation_flags") or []
	if not isinstance(speculation_flags, list):
		return False, "Runtime reasoning renderer returned invalid speculation_flags."
	supported_claim_count = len(supported_claims)
	recommendation_allowed = bool(activation_contract.get("recommendation_allowed"))
	if recommendations and not recommendation_allowed:
		return False, "Runtime reasoning renderer returned recommendations outside the governed recommendation policy."
	if str(reasoning_type or "").strip() in {"interpretation", "explanation"} and recommendations:
		return False, "Interpretation/explanation reasoning returned recommendations outside the allowed reasoning scope."
	if str(reasoning_type or "").strip() in {"recommendation", "continuation_detail"}:
		if str(reasoning_type or "").strip() == "recommendation" and not recommendations:
			return False, "Runtime reasoning renderer returned recommendation reasoning without governed recommendations."
		if str(reasoning_type or "").strip() == "continuation_detail" and not supported_claims and not recommendations:
			return False, "Runtime reasoning renderer returned continuation detail without substantive grounded content."
		for item in recommendations:
			if not isinstance(item, dict):
				return False, "Runtime reasoning renderer returned invalid recommendation item."
			action = str(item.get("action") or "").strip()
			rationale = str(item.get("rationale") or "").strip()
			basis_claim_refs = item.get("basis_claim_refs") or []
			if not action or not rationale:
				return False, "Runtime reasoning renderer returned recommendation without action/rationale."
			if not isinstance(basis_claim_refs, list) or not basis_claim_refs:
				return False, "Runtime reasoning renderer returned recommendation without basis_claim_refs."
			for ref in basis_claim_refs:
				if not isinstance(ref, int):
					return False, "Runtime reasoning renderer returned non-integer basis_claim_refs."
				if ref < 0 or ref >= supported_claim_count:
					return False, "Runtime reasoning renderer returned out-of-range basis_claim_refs."
	prefs = dict(presentation_preferences or {})
	if bool(prefs.get("bullet")) and not re.search(r"(^|\n)\s*[-•]\s+", answer_text):
		return False, "Runtime reasoning renderer did not honor requested bullet presentation."
	unsupported_numbers = _unsupported_payload_number_tokens(
		payload=payload,
		grounding_context=grounding_context,
		verified_numeric_values=verified_numeric_values,
	)
	if unsupported_numbers:
		return (
			False,
			"Runtime reasoning renderer used numeric facts not present in the grounded ERP evidence: "
			+ ", ".join(unsupported_numbers[:8]),
		)
	return True, ""


def _sanitize_runtime_payload(
	*,
	payload: Dict[str, Any],
	reasoning_type: str,
	presentation_preferences: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	out = dict(payload or {})
	if str(reasoning_type or "").strip() in {"interpretation", "explanation"}:
		out["recommendations"] = []
	prefs = dict(presentation_preferences or {})
	answer_text = str(out.get("answer_text") or "").strip()
	if bool(prefs.get("bullet")) and not re.search(r"(^|\n)\s*[-•]\s+", answer_text):
		recommendations = [dict(item) for item in (out.get("recommendations") or []) if isinstance(item, dict)]
		supported_claims = [dict(item) for item in (out.get("supported_claims") or []) if isinstance(item, dict)]
		bullets: List[str] = []
		if str(reasoning_type or "").strip() in {"recommendation", "continuation_detail"} and recommendations:
			for item in recommendations:
				action = str(item.get("action") or "").strip()
				rationale = str(item.get("rationale") or "").strip()
				if action and rationale:
					bullets.append(f"- {action} {rationale}")
				elif action:
					bullets.append(f"- {action}")
		elif supported_claims:
			for item in supported_claims:
				claim = str(item.get("claim") or "").strip()
				support = str(item.get("support") or "").strip()
				if claim and support:
					bullets.append(f"- {claim} {support}")
				elif claim:
					bullets.append(f"- {claim}")
		if bullets:
			out["answer_text"] = "\n".join(bullets)
	return out


def _row_primary_value(row: Dict[str, Any]) -> str:
	candidates: List[tuple[int, str]] = []
	for value in row.values():
		text = str(value if value is not None else "").strip()
		if not text or not re.search(r"[A-Za-z]", text):
			continue
		score = len(text)
		if " " in text:
			score += 20
		if not _extract_number_tokens_from_text(text):
			score += 5
		candidates.append((score, text))
	if candidates:
		candidates.sort(key=lambda item: item[0], reverse=True)
		return candidates[0][1]
	for value in row.values():
		text = str(value if value is not None else "").strip()
		if text:
			return text
	return ""


def _format_numeric_display_value(value_text: str) -> str:
	text = str(value_text or "").strip()
	if not re.fullmatch(r"-?\d[\d,]*(?:\.\d+)?", text):
		return text
	try:
		value = Decimal(text.replace(",", ""))
	except (InvalidOperation, ValueError):
		return text
	if value == value.to_integral_value():
		return f"{int(value):,}"
	normalized = format(value.normalize(), "f")
	if "." in normalized:
		whole, fractional = normalized.split(".", 1)
		return f"{int(whole):,}.{fractional}"
	return f"{int(value):,}"


def _row_numeric_pairs(row: Dict[str, Any], *, limit: int = 3) -> List[str]:
	pairs: List[str] = []
	for key, value in row.items():
		key_text = str(key or "").strip()
		value_text = str(value if value is not None else "").strip()
		if not key_text or not value_text:
			continue
		if not _extract_number_tokens_from_text(value_text):
			continue
		if re.search(r"[A-Za-z]", value_text):
			continue
		pairs.append(f"{key_text}: {_format_numeric_display_value(value_text)}")
		if len(pairs) >= limit:
			break
	return pairs


def _text_tokens(text: str) -> set[str]:
	return {
		token
		for token in re.findall(r"[A-Za-z0-9]+", str(text or "").lower())
		if len(token) >= 2
	}


def _candidate_text_values(row: Dict[str, Any]) -> List[str]:
	values: List[str] = []
	seen = set()
	for value in row.values():
		text = str(value if value is not None else "").strip()
		if not text or not re.search(r"[A-Za-z]", text):
			continue
		for candidate in (text, text.split(" - ", 1)[0].strip()):
			if not candidate or candidate in seen:
				continue
			seen.add(candidate)
			values.append(candidate)
	return values


def _candidate_acronym(text: str) -> str:
	parts = [token for token in re.findall(r"[A-Za-z0-9]+", str(text or "")) if token]
	if len(parts) < 2:
		return ""
	return "".join(part[0] for part in parts).lower()


def _row_focus_score(row: Dict[str, Any], focus_text: str) -> int:
	focus = re.sub(r"\s+", " ", str(focus_text or "").lower()).strip()
	if not focus:
		return 0
	focus_tokens = _text_tokens(focus)
	if not focus_tokens:
		return 0
	best = 0
	for candidate in _candidate_text_values(row):
		candidate_norm = re.sub(r"\s+", " ", candidate.lower()).strip()
		if not candidate_norm:
			continue
		candidate_tokens = _text_tokens(candidate_norm)
		if not candidate_tokens:
			continue
		if candidate_norm in focus:
			best = max(best, 120 + min(len(candidate_norm), 40))
		acronym = _candidate_acronym(candidate_norm)
		if acronym and acronym in focus_tokens:
			best = max(best, 110 + len(candidate_tokens))
		overlap = candidate_tokens.intersection(focus_tokens)
		if len(overlap) >= min(2, len(candidate_tokens)):
			coverage = len(overlap) / max(len(candidate_tokens), 1)
			if coverage >= 0.6:
				best = max(best, int(coverage * 90) + len(overlap))
	return best


def _context_candidate_rows(context: Dict[str, Any]) -> List[Dict[str, Any]]:
	rows: List[Dict[str, Any]] = []
	for row in (context.get("grounded_rows") or []):
		if isinstance(row, dict):
			rows.append(dict(row))
	sections = context.get("artifact_sections") if isinstance(context.get("artifact_sections"), dict) else {}
	for section in sections.values():
		if not isinstance(section, list):
			continue
		for row in section:
			if isinstance(row, dict):
				rows.append(dict(row))
	catalog = context.get("evidence_catalog") if isinstance(context.get("evidence_catalog"), dict) else {}
	for table in _parse_visible_tables(str(catalog.get("visible_text_excerpt") or "")):
		for row in table.get("rows") or []:
			if isinstance(row, dict):
				rows.append(dict(row))
	deduped: List[Dict[str, Any]] = []
	seen = set()
	for row in rows:
		key = tuple(sorted((str(k), str(v)) for k, v in row.items()))
		if key in seen:
			continue
		seen.add(key)
		deduped.append(row)
	return deduped[:80]


def _prior_grounded_focus_text(context: Dict[str, Any]) -> str:
	prior_reasoning = context.get("prior_reasoning") if isinstance(context.get("prior_reasoning"), dict) else {}
	prior_grounded = context.get("prior_grounded_answer") if isinstance(context.get("prior_grounded_answer"), dict) else {}
	return (
		str(prior_reasoning.get("answer_text") or "").strip()
		or str(prior_grounded.get("answer_text") or "").strip()
	)


def _row_focus_identity(row: Dict[str, Any]) -> str:
	identity = _statement_row_identity(row) or _row_primary_value(row)
	return re.sub(r"\s+", " ", str(identity or "").strip().lower())


def _row_descriptive_pairs(row: Dict[str, Any], *, limit: int = 4) -> List[str]:
	pairs: List[str] = []
	for key, value in row.items():
		key_text = str(key or "").strip()
		value_text = str(value if value is not None else "").strip()
		if not key_text or not value_text:
			continue
		if not re.search(r"[A-Za-z]", value_text):
			continue
		if len(value_text) > 120:
			continue
		pairs.append(f"{key_text}: {value_text}")
		if len(pairs) >= limit:
			break
	return pairs


def _parse_visible_tables(visible_text: str) -> List[Dict[str, Any]]:
	lines = [line.strip() for line in str(visible_text or "").splitlines()]
	tables: List[Dict[str, Any]] = []
	last_title = ""
	index = 0
	while index < len(lines):
		line = lines[index]
		if not line:
			index += 1
			continue
		pipe_headers = _pipe_table_cells(line)
		if (
			len(pipe_headers) >= 2
			and index + 1 < len(lines)
			and _pipe_separator_cells(_pipe_table_cells(lines[index + 1]))
		):
			rows: List[Dict[str, str]] = []
			index += 2
			while index < len(lines):
				cells = _pipe_table_cells(lines[index])
				if len(cells) < 2:
					break
				row: Dict[str, str] = {}
				for cell_index, header in enumerate(pipe_headers):
					if cell_index < len(cells):
						value = cells[cell_index].strip()
						if value:
							row[header] = value
				if row:
					rows.append(row)
				index += 1
			if rows:
				tables.append({"title": last_title, "headers": pipe_headers, "rows": rows})
			continue
		if _TABLE_COLUMN_DELIMITER not in line:
			if not line.startswith(("-", "*", "•")):
				last_title = line
			index += 1
			continue
		headers = [part.strip() for part in line.split(_TABLE_COLUMN_DELIMITER) if part.strip()]
		if len(headers) < 2:
			index += 1
			continue
		rows: List[Dict[str, str]] = []
		index += 1
		while index < len(lines):
			row_line = lines[index]
			if not row_line:
				index += 1
				break
			if _TABLE_COLUMN_DELIMITER not in row_line:
				break
			cells = [part.strip() for part in row_line.split(_TABLE_COLUMN_DELIMITER)]
			if len(cells) >= 2:
				row: Dict[str, str] = {}
				for cell_index, header in enumerate(headers):
					if cell_index < len(cells):
						value = cells[cell_index].strip()
						if value:
							row[header] = value
				if row:
					rows.append(row)
			index += 1
		if rows:
			tables.append({"title": last_title, "headers": headers, "rows": rows})
	return tables


def _pipe_table_cells(line: str) -> List[str]:
	text = str(line or "").strip()
	if len(text.split(_MARKDOWN_TABLE_DELIMITER)) < 2:
		return []
	if text.startswith(_MARKDOWN_TABLE_DELIMITER):
		text = text[1:]
	if text.endswith(_MARKDOWN_TABLE_DELIMITER):
		text = text[:-1]
	cells = [cell.strip() for cell in text.split(_MARKDOWN_TABLE_DELIMITER)]
	return [cell for cell in cells if cell]


def _pipe_separator_cells(cells: List[str]) -> bool:
	if not cells:
		return False
	for cell in cells:
		text = str(cell or "").strip().replace(" ", "")
		if not re.fullmatch(r":?-{3,}:?", text):
			return False
	return True


def _join_visible_table_items(items: List[str], *, limit: int = 5) -> str:
	return "; ".join(item for item in items[:limit] if item)


def _table_key_value_items(table: Dict[str, Any], *, limit: int = 5) -> List[str]:
	headers = [str(item or "").strip() for item in (table.get("headers") or []) if str(item or "").strip()]
	if len(headers) < 2:
		return []
	items: List[str] = []
	key_header = headers[0]
	value_header = headers[1]
	for row in table.get("rows") or []:
		if not isinstance(row, dict):
			continue
		key = str(row.get(key_header) or "").strip()
		value = str(row.get(value_header) or "").strip()
		if key and value:
			items.append(f"{key}: {value}")
		if len(items) >= limit:
			break
	return items


def _table_ranked_row_items(table: Dict[str, Any], *, limit: int = 3) -> List[str]:
	headers = [str(item or "").strip() for item in (table.get("headers") or []) if str(item or "").strip()]
	if len(headers) < 3:
		return []
	entity_header = headers[0]
	metric_headers = headers[1:4]
	items: List[str] = []
	for row in table.get("rows") or []:
		if not isinstance(row, dict):
			continue
		entity = str(row.get(entity_header) or "").strip()
		if not entity:
			continue
		metrics = [
			f"{header}: {str(row.get(header) or '').strip()}"
			for header in metric_headers
			if str(row.get(header) or "").strip()
		]
		if metrics:
			items.append(f"{entity} ({', '.join(metrics)})")
		if len(items) >= limit:
			break
	return items


def _parse_display_decimal(value_text: str) -> Decimal | None:
	text = str(value_text or "").strip().rstrip("%").replace(",", "")
	if not text:
		return None
	try:
		return Decimal(text)
	except (InvalidOperation, ValueError):
		return None


def _clean_metric_label(label: str) -> str:
	return re.sub(r"\s+", " ", str(label or "").replace("(MMK)", "").strip()).strip()


def _canonical_metric_key(label: str) -> str:
	normalized = re.sub(r"[^A-Za-z0-9]+", "_", str(label or "").replace("(MMK)", " ").strip().lower())
	return re.sub(r"_+", "_", normalized).strip("_")


def _percent_value(number: Decimal, raw_value: Any = "") -> Decimal:
	raw_text = str(raw_value if raw_value is not None else "").strip()
	if raw_text.endswith("%") or abs(number) > Decimal("1"):
		return number
	return number * Decimal("100")


def _format_percent_decimal(value: Decimal) -> str:
	return f"{format(value.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP).normalize(), 'f')}%"


def _format_amount_decimal(value: Decimal) -> str:
	return _format_numeric_display_value(format(value, "f"))


def _format_management_amount(value: Decimal) -> str:
	if abs(value) >= Decimal("1000000"):
		millions = (value / Decimal("1000000")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
		return f"{format(millions.normalize(), 'f')} MMK million"
	return f"{_format_amount_decimal(value)} MMK"


def _numeric_values_from_rendered_claims(items: List[tuple[str, str]]) -> List[str]:
	values: List[str] = []
	for claim, support in items:
		for fragment in (claim, support):
			for token in re.findall(r"-?\d[\d,]*(?:\.\d+)?", str(fragment or "")):
				cleaned = token.replace(",", "").strip()
				if cleaned:
					values.append(cleaned)
	return values


def _safe_ratio(numerator: Decimal | None, denominator: Decimal | None) -> Decimal | None:
	if numerator is None or denominator is None or abs(denominator) <= Decimal("0.0001"):
		return None
	return numerator / denominator


def _aging_lens_from_capability(capability_id: str) -> Dict[str, str]:
	capability = str(capability_id or "").strip()
	if capability == "accounts_payable_read":
		return {
			"balance_plural": "payables",
			"entity_plural": "suppliers",
			"entity_singular": "supplier",
			"pressure_label": "Supplier payment pressure",
			"normal_timing": "normal supplier payment timing",
			"takeaway_theme": "supplier-payment timing and concentration problem",
			"decision_intensity": "settlement intensity",
			"current_protection": "payment plan discipline",
		}
	if capability == "accounts_receivable_read":
		return {
			"balance_plural": "receivables",
			"entity_plural": "customers",
			"entity_singular": "customer",
			"pressure_label": "Collection pressure",
			"normal_timing": "normal collection timing",
			"takeaway_theme": "collection-timing and concentration problem",
			"decision_intensity": "follow-up intensity",
			"current_protection": "collection prevention",
		}
	return {
		"balance_plural": "balances",
		"entity_plural": "parties",
		"entity_singular": "party",
		"pressure_label": "Aging pressure",
		"normal_timing": "normal operating timing",
		"takeaway_theme": "aging-timing and concentration problem",
		"decision_intensity": "follow-up intensity",
		"current_protection": "timing prevention",
	}


def _aging_lens_from_context(context: Dict[str, Any]) -> Dict[str, str]:
	source = context.get("grounded_source") if isinstance(context.get("grounded_source"), dict) else {}
	capability = (
		str(source.get("capability_id") or "").strip()
		or str(context.get("grounded_capability_id") or "").strip()
		or str(context.get("artifact_capability_id") or "").strip()
	)
	lens = _aging_lens_from_capability(capability)
	if capability:
		return lens
	reports = [
		str(item or "").strip()
		for item in (
			context.get("artifact_source_reports")
			or context.get("grounded_source_reports")
			or source.get("source_reports")
			or []
		)
	]
	report_text = " ".join(reports).lower()
	if "payable" in report_text:
		return _aging_lens_from_capability("accounts_payable_read")
	if "receivable" in report_text:
		return _aging_lens_from_capability("accounts_receivable_read")
	return lens


def _aging_lens_from_tables(tables: List[Dict[str, Any]]) -> Dict[str, str]:
	header_text = " ".join(
		str(header or "").strip()
		for table in tables
		for header in (table.get("headers") or [])
	).lower()
	if "supplier" in header_text:
		return _aging_lens_from_capability("accounts_payable_read")
	if "customer" in header_text:
		return _aging_lens_from_capability("accounts_receivable_read")
	return _aging_lens_from_capability("")


def _entity_scope_from_tables(tables: List[Dict[str, Any]]) -> str:
	header_text = " ".join(
		str(header or "").strip()
		for table in tables
		for header in (table.get("headers") or [])
	).lower()
	if "supplier" in header_text:
		return "suppliers"
	if "customer" in header_text:
		return "customers"
	return "parties"


def _table_metric_map(table: Dict[str, Any]) -> Dict[str, tuple[str, Decimal, str]]:
	headers = [str(item or "").strip() for item in (table.get("headers") or []) if str(item or "").strip()]
	if len(headers) != 2:
		return {}
	key_header, value_header = headers[0], headers[1]
	metrics: Dict[str, tuple[str, Decimal, str]] = {}
	for row in table.get("rows") or []:
		if not isinstance(row, dict):
			continue
		label = str(row.get(key_header) or "").strip()
		value = str(row.get(value_header) or "").strip()
		number = _parse_display_decimal(value)
		if not label or number is None:
			continue
		metrics[_canonical_metric_key(label)] = (label, number, value)
	return metrics


def _artifact_summary_metric_map(sections: Dict[str, Any]) -> Dict[str, tuple[str, Decimal, Any]]:
	summary = sections.get("summary")
	metrics: Dict[str, tuple[str, Decimal, Any]] = {}
	if isinstance(summary, dict):
		for key, value in summary.items():
			number = _artifact_numeric_decimal(value)
			if number is not None:
				metrics[_canonical_metric_key(str(key))] = (str(key), number, value)
		return metrics
	for label, number, raw_value in _artifact_section_numeric_items(summary):
		if label:
			metrics[_canonical_metric_key(label)] = (label, number, raw_value)
	return metrics


def _metric_entry(
	metrics: Dict[str, tuple[str, Decimal, Any]],
	*keys: str,
) -> tuple[str, Decimal, Any] | None:
	for key in keys:
		entry = metrics.get(_canonical_metric_key(key))
		if entry:
			return entry
	return None


def _distribution_entries_from_table(table: Dict[str, Any]) -> List[tuple[str, Decimal, str]]:
	headers = [str(item or "").strip() for item in (table.get("headers") or []) if str(item or "").strip()]
	if len(headers) != 2:
		return []
	label_header, value_header = headers[0], headers[1]
	entries: List[tuple[str, Decimal, str]] = []
	for row in table.get("rows") or []:
		if not isinstance(row, dict):
			continue
		label = str(row.get(label_header) or "").strip()
		value = str(row.get(value_header) or "").strip()
		number = _parse_display_decimal(value)
		if label and number is not None:
			entries.append((label, number, value))
	return entries


def _distribution_entries_from_artifact(section: Any) -> List[tuple[str, Decimal, Any]]:
	return [(label, number, raw_value) for label, number, raw_value in _artifact_section_numeric_items(section)]


def _ranked_table_numeric_rows(table: Dict[str, Any]) -> tuple[str, List[Dict[str, Any]]]:
	headers = [str(item or "").strip() for item in (table.get("headers") or []) if str(item or "").strip()]
	if len(headers) < 2:
		return "", []
	entity_header = headers[0]
	rows: List[Dict[str, Any]] = []
	for row in table.get("rows") or []:
		if not isinstance(row, dict):
			continue
		entity = str(row.get(entity_header) or "").strip()
		if not entity:
			continue
		normalized_row: Dict[str, Any] = {"entity": entity}
		for header in headers[1:]:
			number = _parse_display_decimal(str(row.get(header) or "").strip())
			if number is not None:
				normalized_row[_canonical_metric_key(header)] = number
		rows.append(normalized_row)
	return entity_header, rows


def _party_numeric_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
	normalized_rows: List[Dict[str, Any]] = []
	for row in rows:
		if not isinstance(row, dict):
			continue
		entity = _artifact_row_entity(row)
		if not entity:
			continue
		normalized_row: Dict[str, Any] = {"entity": entity}
		for key, value in row.items():
			number = _artifact_numeric_decimal(value)
			if number is not None:
				normalized_row[_canonical_metric_key(str(key))] = number
		normalized_rows.append(normalized_row)
	return normalized_rows


def _party_row_overdue_amount(row: Dict[str, Any]) -> Decimal | None:
	for key in ("overdue", "overdue_31", "overdue_total", "overdue_total_31"):
		value = row.get(key)
		if isinstance(value, Decimal):
			return value
	bucket_values: List[Decimal] = []
	for key, value in row.items():
		key_text = str(key or "").strip()
		if not key_text.startswith("bucket_"):
			continue
		if key_text in {"bucket_0_30", "bucket_current", "bucket_future"}:
			continue
		if key_text.endswith("_total"):
			continue
		if not isinstance(value, Decimal):
			continue
		bucket_values.append(value)
	if bucket_values:
		return sum(bucket_values, Decimal("0"))
	return None


def _aging_consultant_insights_from_components(
	*,
	metrics: Dict[str, tuple[str, Decimal, Any]],
	bucket_entries: List[tuple[str, Decimal, Any]],
	party_rows: List[Dict[str, Any]],
	lens: Dict[str, str] | None = None,
) -> List[tuple[str, str]]:
	aging_lens = lens or _aging_lens_from_capability("")
	outstanding_entry = _metric_entry(metrics, "outstanding_total")
	current_entry = _metric_entry(metrics, "current_bucket_0_30", "current_bucket")
	overdue_entry = _metric_entry(metrics, "overdue_total_31", "overdue_total")
	overdue_ratio_entry = _metric_entry(metrics, "overdue_ratio")
	outstanding = outstanding_entry[1] if outstanding_entry else None
	current = current_entry[1] if current_entry else None
	overdue = overdue_entry[1] if overdue_entry else None
	claims: List[tuple[str, str]] = []
	if overdue_ratio_entry and overdue is not None and current is not None:
		ratio_percent = _percent_value(overdue_ratio_entry[1], overdue_ratio_entry[2])
		claim = (
			f"{aging_lens['pressure_label']} is structural: {_format_percent_decimal(ratio_percent)} of {aging_lens['balance_plural']} are overdue, "
			f"and overdue balances are {_format_management_amount(overdue)} versus only {_format_management_amount(current)} still current."
		)
		claims.append((claim, claim))
	elif overdue is not None and current is not None:
		claim = (
			f"Overdue balances are {_format_management_amount(overdue)} versus {_format_management_amount(current)} still current, "
			"so the cash-conversion issue is already visible in the aging mix."
		)
		claims.append((claim, claim))
	if bucket_entries:
		positive_buckets = [(label, number, raw) for label, number, raw in bucket_entries if number > 0]
		if positive_buckets:
			label, number, raw_value = max(positive_buckets, key=lambda item: abs(item[1]))
			display_label = _artifact_label_from_key(label)
			share_of_overdue = _safe_ratio(number, overdue)
			share_text = f", about {_format_percent_decimal(share_of_overdue * Decimal('100'))} of overdue balances" if share_of_overdue is not None else ""
			claim = (
				f"The heaviest timing bucket is {display_label} at {_format_management_amount(number)}{share_text}, "
				"which points to aging momentum rather than only a few newly issued invoices."
			)
			claims.append((claim, claim))
		deep_overdue = sum(
			number
			for label, number, _raw in positive_buckets
			if _canonical_metric_key(label) in {"91_120", "121_above"}
		)
		if deep_overdue > 0:
			share_of_outstanding = _safe_ratio(deep_overdue, outstanding)
			share_text = f" ({_format_percent_decimal(share_of_outstanding * Decimal('100'))} of outstanding)" if share_of_outstanding is not None else ""
			claim = (
				f"Deep overdue exposure in 91+ day buckets is {_format_management_amount(deep_overdue)}{share_text}, "
				f"so part of the balance is moving beyond {aging_lens['normal_timing']}."
			)
			claims.append((claim, claim))
	if party_rows:
		top_outstanding_rows = [
			row for row in party_rows
			if _artifact_numeric_decimal(row.get("outstanding")) is not None
		]
		top_outstanding_rows.sort(key=lambda row: abs(_artifact_numeric_decimal(row.get("outstanding")) or Decimal("0")), reverse=True)
		if outstanding is not None and top_outstanding_rows:
			top_total = sum((_artifact_numeric_decimal(row.get("outstanding")) or Decimal("0")) for row in top_outstanding_rows[:3])
			share = _safe_ratio(top_total, outstanding)
			if share is not None:
				claim = (
					f"The top three listed {aging_lens['entity_plural']} represent {_format_management_amount(top_total)} "
					f"({_format_percent_decimal(share * Decimal('100'))} of outstanding), so concentration matters alongside aging."
				)
				claims.append((claim, claim))
		intensity_rows: List[tuple[Decimal, str, Decimal, Decimal]] = []
		for row in party_rows:
			entity = _artifact_row_entity(row)
			row_outstanding = _artifact_numeric_decimal(row.get("outstanding"))
			row_overdue = (
				_artifact_numeric_decimal(row.get("overdue"))
				or _artifact_numeric_decimal(row.get("overdue_total"))
				or _artifact_numeric_decimal(row.get("overdue_31"))
			)
			intensity = _safe_ratio(row_overdue, row_outstanding)
			if entity and row_outstanding is not None and row_overdue is not None and intensity is not None:
				intensity_rows.append((intensity, entity, row_overdue, row_outstanding))
		if intensity_rows:
			intensity, entity, row_overdue, row_outstanding = max(intensity_rows, key=lambda item: item[0])
			claim = (
				f"Among the listed {aging_lens['entity_plural']}, {entity} has the highest overdue intensity at "
				f"{_format_percent_decimal(intensity * Decimal('100'))} of its outstanding balance "
				f"({_format_management_amount(row_overdue)} overdue out of {_format_management_amount(row_outstanding)})."
			)
			claims.append((claim, claim))
	if claims:
		claim = (
			f"Consultant takeaway: this is mainly a {aging_lens['takeaway_theme']}; "
			f"management should separate recently due balances from deep-overdue exposure before deciding {aging_lens['decision_intensity']}."
		)
		claims.append((claim, "The takeaway follows from overdue mix, aging buckets, and ranked party concentration."))
	return claims[:6]


def _aging_consultant_diagnosis_from_components(
	*,
	metrics: Dict[str, tuple[str, Decimal, Any]],
	bucket_entries: List[tuple[str, Decimal, Any]],
	party_rows: List[Dict[str, Any]],
	lens: Dict[str, str] | None = None,
) -> List[tuple[str, str]]:
	aging_lens = lens or _aging_lens_from_capability("")
	outstanding_entry = _metric_entry(metrics, "outstanding_total")
	current_entry = _metric_entry(metrics, "current_bucket_0_30", "current_bucket")
	overdue_entry = _metric_entry(metrics, "overdue_total_31", "overdue_total")
	overdue_ratio_entry = _metric_entry(metrics, "overdue_ratio")
	outstanding = outstanding_entry[1] if outstanding_entry else None
	current = current_entry[1] if current_entry else None
	overdue = overdue_entry[1] if overdue_entry else None
	diagnosis: List[tuple[str, str]] = []
	if overdue_ratio_entry and overdue is not None and current is not None:
		ratio = _percent_value(overdue_ratio_entry[1], overdue_ratio_entry[2])
		if ratio >= Decimal("50"):
			claim = (
				f"This is a cash-timing control problem, not a normal balance review: {_format_percent_decimal(ratio)} "
				f"of the balance is overdue, and overdue exposure is {_format_management_amount(overdue)} versus "
				f"{_format_management_amount(current)} still current."
			)
			diagnosis.append((claim, claim))
	if not diagnosis and overdue is not None and outstanding is not None:
		share = _safe_ratio(overdue, outstanding)
		if share is not None and share >= Decimal("0.5"):
			claim = (
				f"Overdue exposure dominates the position at {_format_management_amount(overdue)} "
				f"({_format_percent_decimal(share * Decimal('100'))} of outstanding), so timing quality is the core issue."
			)
			diagnosis.append((claim, claim))
	if bucket_entries:
		deep_overdue = sum(
			number
			for label, number, _raw in bucket_entries
			if number > 0 and _canonical_metric_key(label) in {"91_120", "121_above"}
		)
		if deep_overdue > 0:
			share = _safe_ratio(deep_overdue, outstanding)
			share_text = f" ({_format_percent_decimal(share * Decimal('100'))} of outstanding)" if share is not None else ""
			claim = (
				f"The risk is not only size but aging depth: {_format_management_amount(deep_overdue)}{share_text} "
				"is already in 91+ day exposure, where normal follow-up usually becomes escalation or resolution work."
			)
			diagnosis.append((claim, claim))
	if party_rows and outstanding is not None:
		top_rows = [
			row for row in party_rows
			if _artifact_numeric_decimal(row.get("outstanding")) is not None
		]
		top_rows.sort(key=lambda row: abs(_artifact_numeric_decimal(row.get("outstanding")) or Decimal("0")), reverse=True)
		if top_rows:
			top_total = sum((_artifact_numeric_decimal(row.get("outstanding")) or Decimal("0")) for row in top_rows[:3])
			share = _safe_ratio(top_total, outstanding)
			if share is not None and share >= Decimal("0.25"):
				claim = (
					f"Management should treat this as a concentration problem too: the top three listed {aging_lens['entity_plural']} carry "
					f"{_format_management_amount(top_total)}, or {_format_percent_decimal(share * Decimal('100'))} of outstanding."
				)
				diagnosis.append((claim, claim))
	return diagnosis[:3]


def _aging_action_guidance_from_components(
	*,
	metrics: Dict[str, tuple[str, Decimal, Any]],
	bucket_entries: List[tuple[str, Decimal, Any]],
	party_rows: List[Dict[str, Any]],
	lens: Dict[str, str] | None = None,
) -> List[tuple[str, str]]:
	aging_lens = lens or _aging_lens_from_capability("")
	outstanding_entry = _metric_entry(metrics, "outstanding_total")
	overdue_entry = _metric_entry(metrics, "overdue_total_31", "overdue_total")
	overdue_ratio_entry = _metric_entry(metrics, "overdue_ratio")
	outstanding = outstanding_entry[1] if outstanding_entry else None
	overdue = overdue_entry[1] if overdue_entry else None
	guidance: List[tuple[str, str]] = []
	if overdue_ratio_entry and overdue is not None:
		ratio = _percent_value(overdue_ratio_entry[1], overdue_ratio_entry[2])
		if ratio >= Decimal("50"):
			claim = (
				f"Run the overdue balance as a weekly operating control: {_format_management_amount(overdue)} "
				f"and {_format_percent_decimal(ratio)} overdue is too material to leave as a monthly report review."
			)
			guidance.append((claim, claim))
	if bucket_entries:
		positive_buckets = [(label, number, raw) for label, number, raw in bucket_entries if number > 0]
		if positive_buckets:
			label, number, _raw_value = max(positive_buckets, key=lambda item: abs(item[1]))
			claim = (
				f"Create a focused aging lane for the heaviest bucket, {_artifact_label_from_key(label)} at "
				f"{_format_management_amount(number)}, so the largest timing pocket has a named owner and follow-up cadence."
			)
			guidance.append((claim, claim))
		deep_overdue = sum(
			number
			for label, number, _raw in positive_buckets
			if _canonical_metric_key(label) in {"91_120", "121_above"}
		)
		if deep_overdue > 0:
			claim = (
				f"Separate the 91+ day exposure of {_format_management_amount(deep_overdue)} from normal follow-up; "
				"that older balance needs escalation, dispute review, or resolution ownership."
			)
			guidance.append((claim, claim))
	comparable_rows: List[tuple[Decimal, Decimal, str]] = []
	for row in party_rows:
		entity = _artifact_row_entity(row)
		row_outstanding = _artifact_numeric_decimal(row.get("outstanding"))
		row_overdue = (
			_artifact_numeric_decimal(row.get("overdue"))
			or _artifact_numeric_decimal(row.get("overdue_total"))
			or _artifact_numeric_decimal(row.get("overdue_31"))
		)
		if entity and row_outstanding is not None and row_overdue is not None and row_outstanding > 0:
			comparable_rows.append((row_overdue, row_outstanding, entity))
	if comparable_rows:
		row_overdue, row_outstanding, entity = max(comparable_rows, key=lambda item: (item[0], _safe_ratio(item[0], item[1]) or Decimal("0")))
		intensity = _safe_ratio(row_overdue, row_outstanding)
		intensity_text = f" at {_format_percent_decimal(intensity * Decimal('100'))} overdue intensity" if intensity is not None else ""
		claim = (
			f"Prioritize the {aging_lens['entity_singular']} with the largest listed overdue cash impact first: {entity} carries "
			f"{_format_management_amount(row_overdue)} overdue{intensity_text}."
		)
		guidance.append((claim, claim))
	if outstanding is not None and overdue is not None:
		current_quality = outstanding - overdue
		if current_quality > 0:
			claim = (
				f"Protect the still-current portion of {_format_management_amount(current_quality)} from aging into the overdue book; "
				f"{aging_lens['current_protection']} is cheaper than recovery once balances cross into older buckets."
			)
			guidance.append((claim, claim))
	return guidance[:4]


def _working_capital_consultant_insights_from_metrics(
	metrics: Dict[str, tuple[str, Decimal, Any]],
) -> List[tuple[str, str]]:
	ar_entry = _metric_entry(metrics, "accounts_receivable_outstanding")
	ap_entry = _metric_entry(metrics, "accounts_payable_outstanding")
	net_entry = _metric_entry(metrics, "net_ar_minus_ap")
	ar_ratio_entry = _metric_entry(metrics, "ar_overdue_ratio")
	ap_ratio_entry = _metric_entry(metrics, "ap_overdue_ratio")
	ar_value = ar_entry[1] if ar_entry else None
	ap_value = ap_entry[1] if ap_entry else None
	net_value = net_entry[1] if net_entry else None
	claims: List[tuple[str, str]] = []
	if ar_value is not None and ap_value is not None:
		gap = ap_value - ar_value
		ratio = _safe_ratio(ap_value, ar_value)
		if gap > 0 and ratio is not None:
			claim = (
				f"Supplier obligations exceed customer receivables by {_format_management_amount(gap)}; "
				f"payables are {_format_percent_decimal(ratio * Decimal('100'))} of receivables, so supplier pressure is larger than the customer balance pool."
			)
			claims.append((claim, claim))
	if net_value is not None:
		if net_value < 0:
			claim = (
				f"Net AR minus AP is {_format_management_amount(net_value)}, which means collections alone do not fully cover the payable exposure shown here."
			)
		else:
			claim = (
				f"Net AR minus AP is {_format_management_amount(net_value)}, so receivables exceed payable exposure in this view."
			)
		claims.append((claim, claim))
	if ar_ratio_entry and ap_ratio_entry:
		ar_ratio = _percent_value(ar_ratio_entry[1], ar_ratio_entry[2])
		ap_ratio = _percent_value(ap_ratio_entry[1], ap_ratio_entry[2])
		claim = (
			f"This is two-sided working-capital stress: AR overdue ratio is {_format_percent_decimal(ar_ratio)} "
			f"and AP overdue ratio is {_format_percent_decimal(ap_ratio)}, so collection delays and supplier-payment delays are happening together."
		)
		claims.append((claim, claim))
	if ar_value is not None and ap_value is not None and ar_ratio_entry and ap_ratio_entry:
		ar_overdue = ar_value * _percent_value(ar_ratio_entry[1], ar_ratio_entry[2]) / Decimal("100")
		ap_overdue = ap_value * _percent_value(ap_ratio_entry[1], ap_ratio_entry[2]) / Decimal("100")
		claim = (
			f"Using the overdue ratios, timing exposure is about {_format_management_amount(ar_overdue)} on receivables and "
			f"{_format_management_amount(ap_overdue)} on payables, so the issue is not only total balance size but timing quality."
		)
		claims.append((claim, claim))
	if claims:
		claim = (
			"Consultant takeaway: treat AR recovery and supplier settlement as one working-capital plan; "
			"solving only one side can leave the cash cycle under pressure."
		)
		claims.append((claim, "The takeaway follows from AR/AP balance, net position, and overdue ratio evidence."))
	return claims[:6]


def _working_capital_diagnosis_from_metrics(
	metrics: Dict[str, tuple[str, Decimal, Any]],
) -> List[tuple[str, str]]:
	ar_entry = _metric_entry(metrics, "accounts_receivable_outstanding")
	ap_entry = _metric_entry(metrics, "accounts_payable_outstanding")
	net_entry = _metric_entry(metrics, "net_ar_minus_ap")
	ar_ratio_entry = _metric_entry(metrics, "ar_overdue_ratio")
	ap_ratio_entry = _metric_entry(metrics, "ap_overdue_ratio")
	ar_value = ar_entry[1] if ar_entry else None
	ap_value = ap_entry[1] if ap_entry else None
	net_value = net_entry[1] if net_entry else None
	diagnosis: List[tuple[str, str]] = []
	if ar_value is not None and ap_value is not None and net_value is not None:
		if net_value < 0:
			claim = (
				f"This is a working-capital squeeze: AP is larger than AR by {_format_management_amount(abs(net_value))}, "
				"so the visible customer balance pool cannot fully fund supplier obligations."
			)
		else:
			claim = (
				f"This is a positive AR/AP position, but it still depends on collection quality because AR exceeds AP by "
				f"{_format_management_amount(net_value)}."
			)
		diagnosis.append((claim, claim))
	if ar_value is not None and ap_value is not None and ar_ratio_entry and ap_ratio_entry:
		ar_ratio = _percent_value(ar_ratio_entry[1], ar_ratio_entry[2])
		ap_ratio = _percent_value(ap_ratio_entry[1], ap_ratio_entry[2])
		if ar_ratio >= Decimal("50") and ap_ratio >= Decimal("50"):
			ar_overdue = ar_value * ar_ratio / Decimal("100")
			ap_overdue = ap_value * ap_ratio / Decimal("100")
			claim = (
				f"The problem is synchronized on both sides of the cash cycle: about {_format_management_amount(ar_overdue)} "
				f"of AR and {_format_management_amount(ap_overdue)} of AP are overdue, so collections and supplier settlement must be managed together."
			)
			diagnosis.append((claim, claim))
	return diagnosis[:3]


def _working_capital_action_guidance_from_metrics(
	metrics: Dict[str, tuple[str, Decimal, Any]],
) -> List[tuple[str, str]]:
	ar_entry = _metric_entry(metrics, "accounts_receivable_outstanding")
	ap_entry = _metric_entry(metrics, "accounts_payable_outstanding")
	net_entry = _metric_entry(metrics, "net_ar_minus_ap")
	ar_ratio_entry = _metric_entry(metrics, "ar_overdue_ratio")
	ap_ratio_entry = _metric_entry(metrics, "ap_overdue_ratio")
	ar_value = ar_entry[1] if ar_entry else None
	ap_value = ap_entry[1] if ap_entry else None
	net_value = net_entry[1] if net_entry else None
	guidance: List[tuple[str, str]] = []
	if ar_value is not None and ap_value is not None:
		gap = ap_value - ar_value
		if gap > 0:
			claim = (
				f"Pair AR recovery with AP settlement planning: AP exceeds AR by {_format_management_amount(gap)}, "
				"so cash collected from customers should be allocated against supplier commitments instead of treated as free operating cash."
			)
			guidance.append((claim, claim))
		elif gap < 0:
			claim = (
				f"Protect the AR surplus discipline: AR exceeds AP by {_format_management_amount(abs(gap))}, "
				"so management can use the cushion only if receivable timing remains collectible."
			)
			guidance.append((claim, claim))
	if ar_value is not None and ap_value is not None and ar_ratio_entry and ap_ratio_entry:
		ar_ratio = _percent_value(ar_ratio_entry[1], ar_ratio_entry[2])
		ap_ratio = _percent_value(ap_ratio_entry[1], ap_ratio_entry[2])
		ar_overdue = ar_value * ar_ratio / Decimal("100")
		ap_overdue = ap_value * ap_ratio / Decimal("100")
		if ar_overdue > 0 and ap_overdue > 0:
			claim = (
				f"Run a two-track weekly control: one owner should drive collections on about {_format_management_amount(ar_overdue)} "
				f"of overdue AR while another manages about {_format_management_amount(ap_overdue)} of overdue AP with suppliers."
			)
			guidance.append((claim, claim))
		if ar_ratio >= Decimal("50") and ap_ratio >= Decimal("50"):
			claim = (
				f"Treat this as a timing-quality issue, not just a balance-size issue: AR overdue is {_format_percent_decimal(ar_ratio)} "
				f"and AP overdue is {_format_percent_decimal(ap_ratio)}, so both collection discipline and payment discipline need governance."
			)
			guidance.append((claim, claim))
	if net_value is not None and net_value < 0:
		claim = (
			f"Use the net gap as the short-term cash target: closing the {_format_management_amount(abs(net_value))} negative AR/AP gap "
			"should be the first checkpoint before expanding discretionary spending."
		)
		guidance.append((claim, claim))
	return guidance[:4]


def _grounded_capability_ids(context: Dict[str, Any]) -> set[str]:
	source = context.get("grounded_source") if isinstance(context.get("grounded_source"), dict) else {}
	capability_id = str(source.get("capability_id") or "").strip()
	return {capability_id} if capability_id else set()


def _grounded_source_report_count(context: Dict[str, Any]) -> int:
	source = context.get("grounded_source") if isinstance(context.get("grounded_source"), dict) else {}
	reports = source.get("source_reports") if isinstance(source.get("source_reports"), list) else []
	report_count = int(source.get("source_report_count") or 0)
	list_count = len([item for item in reports if str(item or "").strip()])
	return max(report_count, list_count)


def _current_result_has_ranked_parties(context: Dict[str, Any]) -> bool:
	sections = context.get("artifact_sections") if isinstance(context.get("artifact_sections"), dict) else {}
	parties = sections.get("parties")
	if isinstance(parties, list) and any(isinstance(row, dict) and _artifact_row_entity(row) for row in parties):
		return True
	catalog = context.get("evidence_catalog") if isinstance(context.get("evidence_catalog"), dict) else {}
	for table in _parse_visible_tables(str(catalog.get("visible_text_excerpt") or "")):
		headers = [str(item or "").strip() for item in (table.get("headers") or []) if str(item or "").strip()]
		if len(headers) >= 3 and any(isinstance(row, dict) for row in (table.get("rows") or [])):
			return True
	return False


def _contextual_next_step_action(context: Dict[str, Any]) -> Dict[str, Any]:
	capability_ids = _grounded_capability_ids(context)
	report_count = _grounded_source_report_count(context)
	source = context.get("grounded_source") if isinstance(context.get("grounded_source"), dict) else {}
	family_id = str(source.get("family_id") or "").strip()
	composite_grounding = bool(source.get("composite_grounding")) or report_count >= 2
	sections = context.get("artifact_sections") if isinstance(context.get("artifact_sections"), dict) else {}
	summary_metrics = _artifact_summary_metric_map(sections)
	if (
		_metric_entry(summary_metrics, "accounts_receivable_outstanding")
		and _metric_entry(summary_metrics, "accounts_payable_outstanding")
		and (
			composite_grounding
			or family_id == "working_capital"
			or capability_ids.intersection({"working_capital_health_read", "ar_ap_analysis_read"})
		)
	):
		return {
			"action_id": "compare_ar_ap_pressure_side_by_side",
			"user_prompt": (
				"Would you like me to compare the customer collection pressure and supplier payment pressure "
				"side by side next, using the same AR/AP evidence?"
			),
			"source_family_id": family_id,
			"source_report_count": report_count,
			"execution_mode": "current_governed_artifact",
		}
	if _current_result_has_ranked_parties(context):
		if str(source.get("capability_id") or "").strip() == "accounts_receivable_read":
			entity_scope = "customers"
			prompt = "Would you like me to compare the listed customers by overdue amount and overdue intensity next?"
		if str(source.get("capability_id") or "").strip() == "accounts_payable_read":
			entity_scope = "suppliers"
			prompt = "Would you like me to compare the listed suppliers by overdue amount and overdue intensity next?"
		if str(source.get("capability_id") or "").strip() not in {"accounts_receivable_read", "accounts_payable_read"}:
			entity_scope = "parties"
			prompt = "Would you like me to compare the listed parties by overdue amount and overdue intensity next?"
		return {
			"action_id": "compare_listed_parties_by_overdue_and_intensity",
			"user_prompt": prompt,
			"entity_scope": entity_scope,
			"source_family_id": family_id,
			"source_report_count": report_count,
			"execution_mode": "current_governed_artifact",
			"comparison_metrics": ["overdue_amount", "overdue_intensity"],
		}
	return {}


def _contextual_next_step_prompt(context: Dict[str, Any]) -> str:
	return str(_contextual_next_step_action(context).get("user_prompt") or "").strip()


def _payload_with_contextual_next_step(
	payload: Dict[str, Any],
	context: Dict[str, Any],
) -> Dict[str, Any]:
	next_step_action = _contextual_next_step_action(dict(context or {}))
	next_step_prompt = str(next_step_action.get("user_prompt") or "").strip()
	if not next_step_prompt:
		return dict(payload or {})
	out = dict(payload or {})
	answer_text = str(out.get("answer_text") or "").strip()
	if not answer_text:
		return out
	if "Recommended next step" in answer_text or next_step_prompt in answer_text:
		out["offered_next_actions"] = [next_step_action]
		return out
	out["answer_text"] = f"{answer_text}\n\nRecommended next step\n\n{next_step_prompt}"
	out["offered_next_actions"] = [next_step_action]
	return out


def _prior_offered_next_action(context: Dict[str, Any]) -> Dict[str, Any]:
	prior_reasoning = context.get("prior_reasoning") if isinstance(context.get("prior_reasoning"), dict) else {}
	actions = prior_reasoning.get("offered_next_actions")
	if not isinstance(actions, list):
		return {}
	for action in actions:
		if not isinstance(action, dict):
			continue
		action_id = str(action.get("action_id") or "").strip()
		execution_mode = str(action.get("execution_mode") or "").strip()
		if action_id and execution_mode == "current_governed_artifact":
			return dict(action)
	return {}


def _consultant_answer_text(
	*,
	source_name: str,
	insights: List[tuple[str, str]],
	diagnosis: List[tuple[str, str]] | None = None,
	action_guidance: List[tuple[str, str]] | None = None,
	next_step_prompt: str = "",
	presentation_preferences: Dict[str, Any] | None = None,
) -> str:
	opening = f"Here is the business reading from {source_name}."
	lines: List[str] = [opening]
	diagnosis_items = list(diagnosis or [])
	if diagnosis_items:
		lines.extend(["", "Executive diagnosis", ""])
		for claim, _support in diagnosis_items:
			lines.append(f"- {claim}")
			lines.append("")
	lines.extend(["", "Key findings", ""])
	for claim, _support in insights:
		lines.append(f"- {claim}")
		lines.append("")
	guidance_items = list(action_guidance or [])
	if guidance_items:
		lines.append("Management priorities")
		lines.append("")
		for claim, _support in guidance_items:
			lines.append(f"- {claim}")
			lines.append("")
	if next_step_prompt:
		lines.append("Recommended next step")
		lines.append("")
		lines.append(next_step_prompt)
	return "\n".join(lines).strip()


def _comparison_source_name(context: Dict[str, Any]) -> str:
	summary = context.get("grounding_summary") if isinstance(context.get("grounding_summary"), dict) else {}
	source = context.get("grounded_source") if isinstance(context.get("grounded_source"), dict) else {}
	return (
		str(summary.get("latest_assistant_title") or "").strip()
		or str(source.get("source_name") or "").strip()
		or "the current ERP result"
	)


def _party_comparison_rows(context: Dict[str, Any]) -> List[Dict[str, Any]]:
	rows = _party_numeric_rows(_context_candidate_rows(context))
	comparable: List[Dict[str, Any]] = []
	seen = set()
	for row in rows:
		entity = str(row.get("entity") or "").strip()
		outstanding = row.get("outstanding")
		overdue = _party_row_overdue_amount(row)
		total_due = row.get("total_due")
		if not entity or outstanding is None or overdue is None:
			continue
		key = entity.lower()
		if key in seen:
			continue
		seen.add(key)
		intensity = _safe_ratio(overdue, outstanding)
		comparable.append(
			{
				"entity": entity,
				"outstanding": outstanding,
				"total_due": total_due,
				"overdue": overdue,
				"intensity": intensity,
			}
		)
	comparable.sort(
		key=lambda row: (
			row.get("overdue") or Decimal("0"),
			row.get("intensity") or Decimal("0"),
			row.get("outstanding") or Decimal("0"),
		),
		reverse=True,
	)
	return comparable[:10]


def _build_party_overdue_comparison_payload(
	*,
	context: Dict[str, Any],
	action: Dict[str, Any],
) -> Dict[str, Any]:
	rows = _party_comparison_rows(context)
	if len(rows) < 2:
		return {}
	source_name = _comparison_source_name(context)
	top_overdue = max(rows, key=lambda row: row.get("overdue") or Decimal("0"))
	intensity_rows = [row for row in rows if row.get("intensity") is not None]
	top_intensity = max(intensity_rows, key=lambda row: row.get("intensity") or Decimal("0")) if intensity_rows else {}
	supported_claims: List[Dict[str, str]] = []
	verified_values: List[str] = []
	claims: List[str] = [
		f"Here is the comparison from {source_name}.",
	]
	overdue_claim = (
		f"{top_overdue['entity']} has the largest listed overdue amount at "
		f"{_format_management_amount(top_overdue['overdue'])}."
	)
	claims.append(overdue_claim)
	supported_claims.append({"claim": overdue_claim, "support": overdue_claim})
	verified_values.append(format(top_overdue["overdue"], "f"))
	if top_intensity:
		intensity_claim = (
			f"{top_intensity['entity']} has the highest overdue intensity at "
			f"{_format_percent_decimal(top_intensity['intensity'] * Decimal('100'))} "
			f"({_format_management_amount(top_intensity['overdue'])} overdue out of "
			f"{_format_management_amount(top_intensity['outstanding'])})."
		)
		claims.append(intensity_claim)
		supported_claims.append({"claim": intensity_claim, "support": intensity_claim})
		verified_values.extend(
			[
				format(top_intensity["overdue"], "f"),
				format(top_intensity["outstanding"], "f"),
				format((top_intensity["intensity"] * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP), "f"),
			]
		)
	lines: List[str] = [
		f"Here is the comparison from {source_name}.",
		"",
		"Key findings",
		"",
		f"- {overdue_claim}",
		"",
	]
	if top_intensity:
		lines.extend([f"- {intensity_claim}", ""])
	lines.extend(
		[
			"Comparison table",
			"",
			"| Party | Outstanding | Overdue | Overdue intensity |",
			"| --- | ---: | ---: | ---: |",
		]
	)
	for row in rows[:7]:
		intensity = row.get("intensity")
		intensity_text = _format_percent_decimal(intensity * Decimal("100")) if intensity is not None else ""
		lines.append(
			"| "
			f"{row['entity']} | "
			f"{_format_management_amount(row['outstanding'])} | "
			f"{_format_management_amount(row['overdue'])} | "
			f"{intensity_text} |"
		)
		verified_values.extend([format(row["outstanding"], "f"), format(row["overdue"], "f")])
		if intensity is not None:
			verified_values.append(format((intensity * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP), "f"))
	lines.extend(
		[
			"",
			"Consultant takeaway",
			"",
			"Large overdue amount shows cash impact; high overdue intensity shows urgency. The strongest follow-up candidates are parties that score high on both.",
		]
	)
	return {
		"answer_text": "\n".join(lines).strip(),
		"supported_claims": supported_claims,
		"recommendations": [],
		"offered_next_actions": [],
		"speculation_flags": ["executed_prior_offered_next_action", str(action.get("action_id") or "").strip()],
		"confidence": 0.82,
		"reason": "The answer executes the prior offered next action using the current governed party rows.",
		"_verified_numeric_values": verified_values,
	}


def _build_ar_ap_pressure_comparison_payload(
	*,
	context: Dict[str, Any],
	action: Dict[str, Any],
) -> Dict[str, Any]:
	sections = context.get("artifact_sections") if isinstance(context.get("artifact_sections"), dict) else {}
	metrics = _artifact_summary_metric_map(sections)
	ar_entry = _metric_entry(metrics, "accounts_receivable_outstanding")
	ap_entry = _metric_entry(metrics, "accounts_payable_outstanding")
	ar_ratio_entry = _metric_entry(metrics, "ar_overdue_ratio")
	ap_ratio_entry = _metric_entry(metrics, "ap_overdue_ratio")
	if not (ar_entry and ap_entry and ar_ratio_entry and ap_ratio_entry):
		return {}
	source_name = _comparison_source_name(context)
	ar_value = ar_entry[1]
	ap_value = ap_entry[1]
	ar_ratio = _percent_value(ar_ratio_entry[1], ar_ratio_entry[2])
	ap_ratio = _percent_value(ap_ratio_entry[1], ap_ratio_entry[2])
	ar_overdue = ar_value * ar_ratio / Decimal("100")
	ap_overdue = ap_value * ap_ratio / Decimal("100")
	gap = ap_value - ar_value
	lines = [
		f"Here is the side-by-side pressure comparison from {source_name}.",
		"",
		"Key findings",
		"",
		f"- Supplier pressure is larger by {_format_management_amount(gap)} because AP outstanding is {_format_management_amount(ap_value)} versus AR outstanding at {_format_management_amount(ar_value)}.",
		"",
		f"- Timing quality is weak on both sides: AR overdue ratio is {_format_percent_decimal(ar_ratio)} and AP overdue ratio is {_format_percent_decimal(ap_ratio)}.",
		"",
		"Comparison table",
		"",
		"| Area | Outstanding | Overdue ratio | Estimated overdue exposure |",
		"| --- | ---: | ---: | ---: |",
		f"| Receivables | {_format_management_amount(ar_value)} | {_format_percent_decimal(ar_ratio)} | {_format_management_amount(ar_overdue)} |",
		f"| Payables | {_format_management_amount(ap_value)} | {_format_percent_decimal(ap_ratio)} | {_format_management_amount(ap_overdue)} |",
		"",
		"Consultant takeaway",
		"",
		"Treat this as one working-capital plan: collections must improve while supplier settlements are managed, otherwise cash recovered from customers may be immediately absorbed by overdue payables.",
	]
	verified_values = [
		format(value, "f")
		for value in (gap, ap_value, ar_value, ar_ratio, ap_ratio, ar_overdue, ap_overdue)
	]
	return {
		"answer_text": "\n".join(lines).strip(),
		"supported_claims": [
			{"claim": lines[4].lstrip("- "), "support": lines[4].lstrip("- ")},
			{"claim": lines[6].lstrip("- "), "support": lines[6].lstrip("- ")},
		],
		"recommendations": [],
		"offered_next_actions": [],
		"speculation_flags": ["executed_prior_offered_next_action", str(action.get("action_id") or "").strip()],
		"confidence": 0.82,
		"reason": "The answer executes the prior offered next action using the current governed working-capital metrics.",
		"_verified_numeric_values": verified_values,
	}


def _build_offered_next_action_execution_payload(
	*,
	reasoning_type: str,
	context: Dict[str, Any],
) -> Dict[str, Any]:
	if str(reasoning_type or "").strip() != "continuation_detail":
		return {}
	action = _prior_offered_next_action(context)
	action_id = str(action.get("action_id") or "").strip()
	if action_id == "compare_listed_parties_by_overdue_and_intensity":
		return _build_party_overdue_comparison_payload(context=context, action=action)
	if action_id == "compare_ar_ap_pressure_side_by_side":
		return _build_ar_ap_pressure_comparison_payload(context=context, action=action)
	return {}


def _summary_table_insight_items(table: Dict[str, Any]) -> List[tuple[str, str]]:
	headers = [str(item or "").strip() for item in (table.get("headers") or []) if str(item or "").strip()]
	if len(headers) != 2:
		return []
	key_header, value_header = headers[0], headers[1]
	numeric_rows: List[tuple[Decimal, str, str]] = []
	ratio_rows: List[tuple[str, str]] = []
	for row in table.get("rows") or []:
		if not isinstance(row, dict):
			continue
		label = str(row.get(key_header) or "").strip()
		value = str(row.get(value_header) or "").strip()
		number = _parse_display_decimal(value)
		if not label or number is None:
			continue
		numeric_rows.append((abs(number), label, value))
		if value.endswith("%"):
			ratio_rows.append((label, value))
	claims: List[tuple[str, str]] = []
	if ratio_rows:
		label, value = ratio_rows[0]
		claim = f"The summary ratio signal is {_clean_metric_label(label)} at {value}, so the report is showing a proportion problem, not only a currency total."
		claims.append((claim, claim))
	if numeric_rows:
		numeric_rows.sort(key=lambda item: item[0], reverse=True)
		_, label, value = numeric_rows[0]
		claim = f"The largest visible summary amount is {_clean_metric_label(label)} at {_format_numeric_display_value(value)}, which sets the scale of the exposure."
		claims.append((claim, claim))
	return claims[:2]


def _distribution_table_insight_items(table: Dict[str, Any]) -> List[tuple[str, str]]:
	headers = [str(item or "").strip() for item in (table.get("headers") or []) if str(item or "").strip()]
	if len(headers) != 2:
		return []
	label_header, value_header = headers[0], headers[1]
	numeric_rows: List[tuple[Decimal, str, str]] = []
	for row in table.get("rows") or []:
		if not isinstance(row, dict):
			continue
		label = str(row.get(label_header) or "").strip()
		value = str(row.get(value_header) or "").strip()
		number = _parse_display_decimal(value)
		if not label or number is None:
			continue
		numeric_rows.append((number, label, value))
	if len(numeric_rows) < 3:
		return []
	numeric_rows.sort(key=lambda item: item[0], reverse=True)
	top_number, top_label, top_value = numeric_rows[0]
	if top_number <= 0:
		return []
	title = str(table.get("title") or "The distribution table").strip()
	claim = f"{title} is concentrated most heavily in {top_label} at {_format_numeric_display_value(top_value)}, so the distribution matters as much as the total."
	return [(claim, claim)]


def _ranked_table_insight_items(table: Dict[str, Any]) -> List[tuple[str, str]]:
	headers = [str(item or "").strip() for item in (table.get("headers") or []) if str(item or "").strip()]
	if len(headers) < 3:
		return []
	entity_header = headers[0]
	claims: List[tuple[str, str]] = []
	seen_claims = set()
	for metric_header in headers[1:4]:
		best: tuple[Decimal, str, str] | None = None
		for row in table.get("rows") or []:
			if not isinstance(row, dict):
				continue
			entity = str(row.get(entity_header) or "").strip()
			value = str(row.get(metric_header) or "").strip()
			number = _parse_display_decimal(value)
			if not entity or number is None:
				continue
			candidate = (number, entity, value)
			if best is None or candidate[0] > best[0]:
				best = candidate
		if best is None or best[0] <= 0:
			continue
		_, entity, value = best
		metric_label = _clean_metric_label(metric_header)
		claim = f"Within the ranked rows, {entity} carries the largest visible {metric_label} at {_format_numeric_display_value(value)}."
		if claim in seen_claims:
			continue
		seen_claims.add(claim)
		claims.append((claim, claim))
		if len(claims) >= 2:
			break
	return claims


def _visible_table_consultant_insights(tables: List[Dict[str, Any]]) -> List[tuple[str, str]]:
	insights: List[tuple[str, str]] = []
	summary_tables = [
		table for table in tables
		if len([item for item in (table.get("headers") or []) if str(item or "").strip()]) == 2
	]
	ranked_tables = [
		table for table in tables
		if len([item for item in (table.get("headers") or []) if str(item or "").strip()]) >= 3
	]
	if summary_tables:
		summary_metrics = _table_metric_map(summary_tables[0])
		if _metric_entry(summary_metrics, "accounts_receivable_outstanding") and _metric_entry(summary_metrics, "accounts_payable_outstanding"):
			working_capital_insights = _working_capital_consultant_insights_from_metrics(summary_metrics)
			if working_capital_insights:
				return working_capital_insights
		if _metric_entry(summary_metrics, "outstanding_total") and _metric_entry(summary_metrics, "overdue_total_31", "overdue_total"):
			lens = _aging_lens_from_tables(tables)
			bucket_entries = _distribution_entries_from_table(summary_tables[1]) if len(summary_tables) > 1 else []
			_entity_header, ranked_rows = _ranked_table_numeric_rows(ranked_tables[0]) if ranked_tables else ("", [])
			aging_insights = _aging_consultant_insights_from_components(
				metrics=summary_metrics,
				bucket_entries=bucket_entries,
				party_rows=ranked_rows,
				lens=lens,
			)
			if aging_insights:
				return aging_insights
	if summary_tables:
		insights.extend(_summary_table_insight_items(summary_tables[0]))
	for table in summary_tables[1:3]:
		insights.extend(_distribution_table_insight_items(table))
	if ranked_tables:
		insights.extend(_ranked_table_insight_items(ranked_tables[0]))
	if insights:
		claim = "Consultant takeaway: the result points to scale, timing distribution, and concentration; treat those as the decision lenses before making predictions or assigning causes."
		insights.append((claim, "This takeaway is derived from the visible summary, distribution, and ranked-row evidence."))
	return insights[:6]


def _visible_table_diagnosis_items(tables: List[Dict[str, Any]]) -> List[tuple[str, str]]:
	summary_tables = [
		table for table in tables
		if len([item for item in (table.get("headers") or []) if str(item or "").strip()]) == 2
	]
	ranked_tables = [
		table for table in tables
		if len([item for item in (table.get("headers") or []) if str(item or "").strip()]) >= 3
	]
	if not summary_tables:
		return []
	summary_metrics = _table_metric_map(summary_tables[0])
	if _metric_entry(summary_metrics, "accounts_receivable_outstanding") and _metric_entry(summary_metrics, "accounts_payable_outstanding"):
		return _working_capital_diagnosis_from_metrics(summary_metrics)
	if _metric_entry(summary_metrics, "outstanding_total") and _metric_entry(summary_metrics, "overdue_total_31", "overdue_total"):
		lens = _aging_lens_from_tables(tables)
		bucket_entries = _distribution_entries_from_table(summary_tables[1]) if len(summary_tables) > 1 else []
		_entity_header, ranked_rows = _ranked_table_numeric_rows(ranked_tables[0]) if ranked_tables else ("", [])
		return _aging_consultant_diagnosis_from_components(
			metrics=summary_metrics,
			bucket_entries=bucket_entries,
			party_rows=ranked_rows,
			lens=lens,
		)
	return []


def _visible_table_action_guidance_items(tables: List[Dict[str, Any]]) -> List[tuple[str, str]]:
	summary_tables = [
		table for table in tables
		if len([item for item in (table.get("headers") or []) if str(item or "").strip()]) == 2
	]
	ranked_tables = [
		table for table in tables
		if len([item for item in (table.get("headers") or []) if str(item or "").strip()]) >= 3
	]
	if not summary_tables:
		return []
	summary_metrics = _table_metric_map(summary_tables[0])
	if _metric_entry(summary_metrics, "accounts_receivable_outstanding") and _metric_entry(summary_metrics, "accounts_payable_outstanding"):
		return _working_capital_action_guidance_from_metrics(summary_metrics)
	if _metric_entry(summary_metrics, "outstanding_total") and _metric_entry(summary_metrics, "overdue_total_31", "overdue_total"):
		lens = _aging_lens_from_tables(tables)
		bucket_entries = _distribution_entries_from_table(summary_tables[1]) if len(summary_tables) > 1 else []
		_entity_header, ranked_rows = _ranked_table_numeric_rows(ranked_tables[0]) if ranked_tables else ("", [])
		return _aging_action_guidance_from_components(
			metrics=summary_metrics,
			bucket_entries=bucket_entries,
			party_rows=ranked_rows,
			lens=lens,
		)
	return []


def _artifact_label_from_key(key: str) -> str:
	label = str(key or "").strip().replace("_", " ")
	label = re.sub(r"\bbucket\b", "", label, flags=re.IGNORECASE).strip()
	label = label.replace("0 30", "0-30").replace("31 60", "31-60").replace("61 90", "61-90")
	label = label.replace("91 120", "91-120").replace("121 above", "121-Above")
	return re.sub(r"\s+", " ", label).strip().title()


def _artifact_numeric_decimal(value: Any) -> Decimal | None:
	if isinstance(value, bool) or value is None:
		return None
	try:
		return Decimal(str(value).replace(",", "").strip())
	except (InvalidOperation, ValueError):
		return None


def _artifact_numeric_display(key: str, value: Any) -> str:
	number = _artifact_numeric_decimal(value)
	if number is None:
		return str(value if value is not None else "").strip()
	key_text = str(key or "").strip().lower()
	if "ratio" in key_text and abs(number) <= Decimal("1"):
		percent = (number * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
		return f"{format(percent.normalize(), 'f')}%"
	return _format_numeric_display_value(format(number, "f"))


def _artifact_section_numeric_items(section: Any) -> List[tuple[str, Decimal, Any]]:
	if isinstance(section, list):
		items: List[tuple[str, Decimal, Any]] = []
		for index, row in enumerate(section):
			if not isinstance(row, dict):
				continue
			label = (
				str(row.get("metric") or "").strip()
				or str(row.get("label") or "").strip()
				or str(row.get("bucket") or "").strip()
				or str(row.get("name") or "").strip()
				or str(row.get("account") or "").strip()
				or f"row_{index + 1}"
			)
			preferred_value_keys = ("value", "amount", "total", "balance")
			candidate_values = [
				row.get(key)
				for key in preferred_value_keys
				if key in row and _artifact_numeric_decimal(row.get(key)) is not None
			]
			if not candidate_values:
				candidate_values = [
					value
					for key, value in row.items()
					if key not in {"metric", "label", "bucket", "name", "account"}
					and _artifact_numeric_decimal(value) is not None
				]
			if not candidate_values:
				continue
			value = candidate_values[0]
			number = _artifact_numeric_decimal(value)
			if number is None:
				continue
			items.append((label, number, value))
		return items
	if not isinstance(section, dict):
		return []
	items: List[tuple[str, Decimal, Any]] = []
	for key, value in section.items():
		number = _artifact_numeric_decimal(value)
		if number is None:
			continue
		items.append((str(key or "").strip(), number, value))
	return items


def _artifact_row_entity(row: Dict[str, Any]) -> str:
	candidates: List[tuple[int, str]] = []
	for key, value in row.items():
		text = str(value if value is not None else "").strip()
		if not text or not re.search(r"[A-Za-z]", text):
			continue
		score = len(text)
		key_text = str(key or "").strip().lower()
		if key_text in {"party", "customer", "supplier", "item", "product", "document", "invoice"}:
			score += 80
		if " " in text:
			score += 20
		candidates.append((score, text))
	if not candidates:
		return _row_primary_value(row)
	candidates.sort(key=lambda item: item[0], reverse=True)
	return candidates[0][1]


def _artifact_party_metric_keys(rows: List[Dict[str, Any]]) -> List[str]:
	available = {
		str(key or "").strip()
		for row in rows
		for key, value in row.items()
		if _artifact_numeric_decimal(value) is not None
	}
	preferred = [
		"outstanding",
		"total_due",
		"overdue",
		"overdue_total",
		"invoiced",
		"paid",
		"amount",
		"total_amount",
		"revenue",
		"quantity",
	]
	selected = [key for key in preferred if key in available]
	if selected:
		return selected[:3]
	return sorted(available)[:3]


def _artifact_party_bucket_insight_items(rows: List[Dict[str, Any]]) -> List[tuple[str, str]]:
	bucket_totals: Dict[str, Decimal] = {}
	for row in rows:
		for key, value in row.items():
			key_text = str(key or "").strip()
			if not key_text.startswith("bucket_"):
				continue
			number = _artifact_numeric_decimal(value)
			if number is None:
				continue
			bucket_totals[key_text] = bucket_totals.get(key_text, Decimal("0")) + number
	if not bucket_totals:
		return []
	key, number = max(bucket_totals.items(), key=lambda item: abs(item[1]))
	claim = (
		f"The heaviest aging bucket across listed parties is {_artifact_label_from_key(key)} at "
		f"{_format_numeric_display_value(format(number, 'f'))}, so timing distribution is a key part of the risk picture."
	)
	return [(claim, claim)]


def _artifact_sections_verified_numeric_values(context: Dict[str, Any]) -> List[str]:
	sections = context.get("artifact_sections") if isinstance(context.get("artifact_sections"), dict) else {}
	values: List[str] = []
	for section in sections.values():
		for _label, number, _raw_value in _artifact_section_numeric_items(section):
			values.append(format(number, "f"))
	rows = [dict(row) for row in (sections.get("parties") or []) if isinstance(row, dict)]
	bucket_totals: Dict[str, Decimal] = {}
	for row in rows:
		for key, value in row.items():
			key_text = str(key or "").strip()
			if not key_text.startswith("bucket_"):
				continue
			number = _artifact_numeric_decimal(value)
			if number is None:
				continue
			bucket_totals[key_text] = bucket_totals.get(key_text, Decimal("0")) + number
	for number in bucket_totals.values():
		values.append(format(number, "f"))
	return values


def _artifact_sections_insight_items(context: Dict[str, Any]) -> List[tuple[str, str]]:
	sections = context.get("artifact_sections") if isinstance(context.get("artifact_sections"), dict) else {}
	if not sections:
		return []
	summary_metrics = _artifact_summary_metric_map(sections)
	if _metric_entry(summary_metrics, "accounts_receivable_outstanding") and _metric_entry(summary_metrics, "accounts_payable_outstanding"):
		working_capital_insights = _working_capital_consultant_insights_from_metrics(summary_metrics)
		if working_capital_insights:
			return working_capital_insights
	if _metric_entry(summary_metrics, "outstanding_total") and _metric_entry(summary_metrics, "overdue_total_31", "overdue_total"):
		lens = _aging_lens_from_context(context)
		aging_insights = _aging_consultant_insights_from_components(
			metrics=summary_metrics,
			bucket_entries=_distribution_entries_from_artifact(sections.get("bucket_totals")),
			party_rows=[dict(row) for row in (sections.get("parties") or []) if isinstance(row, dict)],
			lens=lens,
		)
		if aging_insights:
			return aging_insights
	insights: List[tuple[str, str]] = []
	summary_items = _artifact_section_numeric_items(sections.get("summary"))
	ratio_items = [(key, number, value) for key, number, value in summary_items if "ratio" in key.lower()]
	if ratio_items:
		key, _number, value = ratio_items[0]
		claim = (
			f"The main ratio signal is {_artifact_label_from_key(key)} at {_artifact_numeric_display(key, value)}, "
			"so the result is highlighting a proportion issue, not only an amount."
		)
		insights.append((claim, claim))
	if summary_items:
		key, _number, value = max(summary_items, key=lambda item: abs(item[1]))
		claim = (
			f"The largest summary amount is {_artifact_label_from_key(key)} at {_artifact_numeric_display(key, value)}, "
			"which sets the scale of the business exposure."
		)
		if claim not in {item[0] for item in insights}:
			insights.append((claim, claim))
	bucket_items = _artifact_section_numeric_items(sections.get("bucket_totals"))
	if bucket_items:
		key, _number, value = max(bucket_items, key=lambda item: abs(item[1]))
		claim = (
			f"The heaviest aging bucket is {_artifact_label_from_key(key)} at {_artifact_numeric_display(key, value)}, "
			"so timing distribution is a key part of the risk picture."
		)
		insights.append((claim, claim))
	rows = [dict(row) for row in (sections.get("parties") or []) if isinstance(row, dict)]
	if rows and not bucket_items:
		for claim, support in _artifact_party_bucket_insight_items(rows):
			if claim not in {item[0] for item in insights}:
				insights.append((claim, support))
	for metric_key in _artifact_party_metric_keys(rows):
		ranked: List[tuple[Decimal, str, Any]] = []
		for row in rows:
			number = _artifact_numeric_decimal(row.get(metric_key))
			entity = _artifact_row_entity(row)
			if number is None or not entity:
				continue
			ranked.append((number, entity, row.get(metric_key)))
		if not ranked:
			continue
		_number, entity, value = max(ranked, key=lambda item: abs(item[0]))
		claim = (
			f"Among the listed parties, {entity} has the highest {_artifact_label_from_key(metric_key)} at "
			f"{_artifact_numeric_display(metric_key, value)}."
		)
		if claim not in {item[0] for item in insights}:
			insights.append((claim, claim))
		if len(insights) >= 6:
			break
	if len(insights) >= 3:
		return insights[:6]
	return []


def _artifact_sections_diagnosis_items(context: Dict[str, Any]) -> List[tuple[str, str]]:
	sections = context.get("artifact_sections") if isinstance(context.get("artifact_sections"), dict) else {}
	if not sections:
		return []
	summary_metrics = _artifact_summary_metric_map(sections)
	if _metric_entry(summary_metrics, "accounts_receivable_outstanding") and _metric_entry(summary_metrics, "accounts_payable_outstanding"):
		return _working_capital_diagnosis_from_metrics(summary_metrics)
	if _metric_entry(summary_metrics, "outstanding_total") and _metric_entry(summary_metrics, "overdue_total_31", "overdue_total"):
		lens = _aging_lens_from_context(context)
		return _aging_consultant_diagnosis_from_components(
			metrics=summary_metrics,
			bucket_entries=_distribution_entries_from_artifact(sections.get("bucket_totals")),
			party_rows=[dict(row) for row in (sections.get("parties") or []) if isinstance(row, dict)],
			lens=lens,
		)
	return []


def _artifact_sections_action_guidance_items(context: Dict[str, Any]) -> List[tuple[str, str]]:
	sections = context.get("artifact_sections") if isinstance(context.get("artifact_sections"), dict) else {}
	if not sections:
		return []
	summary_metrics = _artifact_summary_metric_map(sections)
	if _metric_entry(summary_metrics, "accounts_receivable_outstanding") and _metric_entry(summary_metrics, "accounts_payable_outstanding"):
		return _working_capital_action_guidance_from_metrics(summary_metrics)
	if _metric_entry(summary_metrics, "outstanding_total") and _metric_entry(summary_metrics, "overdue_total_31", "overdue_total"):
		lens = _aging_lens_from_context(context)
		return _aging_action_guidance_from_components(
			metrics=summary_metrics,
			bucket_entries=_distribution_entries_from_artifact(sections.get("bucket_totals")),
			party_rows=[dict(row) for row in (sections.get("parties") or []) if isinstance(row, dict)],
			lens=lens,
		)
	return []


def _visible_tables_action_guidance_items(tables: List[Dict[str, Any]]) -> List[tuple[str, str]]:
	return _visible_table_action_guidance_items(tables)


def _artifact_metric_decimal(context: Dict[str, Any], *keys: str) -> tuple[Decimal | None, Any]:
	wanted = {
		str(key or "").strip().lower()
		for key in keys
		if str(key or "").strip()
	}
	metrics = context.get("artifact_metrics") if isinstance(context.get("artifact_metrics"), dict) else {}
	for key, value in metrics.items():
		if str(key or "").strip().lower() not in wanted:
			continue
		number = _artifact_numeric_decimal(value)
		if number is not None:
			return number, value
	sections = context.get("artifact_sections") if isinstance(context.get("artifact_sections"), dict) else {}
	for label, number, raw_value in _artifact_section_numeric_items(sections.get("summary")):
		normalized = str(label or "").strip().lower().replace(" ", "_")
		if normalized in wanted:
			return number, raw_value
	return None, None


def _artifact_section_rows(context: Dict[str, Any], *section_keys: str) -> List[Dict[str, Any]]:
	sections = context.get("artifact_sections") if isinstance(context.get("artifact_sections"), dict) else {}
	rows: List[Dict[str, Any]] = []
	for section_key in section_keys:
		section = sections.get(section_key)
		if isinstance(section, list):
			rows.extend([dict(row) for row in section if isinstance(row, dict)])
	return rows


def _statement_row_identity(row: Dict[str, Any]) -> str:
	return (
		str(row.get("account") or "").strip()
		or str(row.get("label") or "").strip()
		or str(row.get("line") or "").strip()
	)


def _row_structural_depth(row: Dict[str, Any]) -> int:
	value = _artifact_numeric_decimal(row.get("indent"))
	if value is None:
		return 0
	return int(value)


def _preferred_detail_numeric_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
	numeric_rows = [
		dict(row)
		for row in rows
		if isinstance(row, dict)
		and _statement_row_identity(row)
		and _artifact_numeric_decimal(row.get("amount") if row.get("amount") not in (None, "") else row.get("value")) is not None
	]
	if not numeric_rows:
		return []
	parent_accounts = {
		str(row.get("parent_account") or "").strip()
		for row in numeric_rows
		if str(row.get("parent_account") or "").strip()
	}
	if parent_accounts:
		leaf_rows = [
			row
			for row in numeric_rows
			if _statement_row_identity(row) not in parent_accounts
		]
		if leaf_rows:
			numeric_rows = leaf_rows
	depths = [_row_structural_depth(row) for row in numeric_rows]
	if depths and max(depths) > min(depths):
		max_depth = max(depths)
		deeper_rows = [row for row in numeric_rows if _row_structural_depth(row) == max_depth]
		if deeper_rows:
			numeric_rows = deeper_rows
	return numeric_rows


def _largest_numeric_row(rows: List[Dict[str, Any]]) -> tuple[str, Decimal | None, Any]:
	candidates: List[tuple[Decimal, str, Any]] = []
	for row in _preferred_detail_numeric_rows(rows):
		label = (
			str(row.get("label") or "").strip()
			or str(row.get("account") or "").strip()
			or str(row.get("line") or "").strip()
			or str(row.get("metric") or "").strip()
		)
		value = row.get("amount") if row.get("amount") not in (None, "") else row.get("value")
		number = _artifact_numeric_decimal(value)
		if label and number is not None:
			candidates.append((number, label, value))
	if not candidates:
		return "", None, None
	number, label, value = max(candidates, key=lambda item: abs(item[0]))
	return label, number, value


def _ratio_percent(numerator: Decimal, denominator: Decimal) -> str:
	if abs(denominator) <= Decimal("0.0001"):
		return ""
	value = (numerator / denominator * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
	return f"{format(value.normalize(), 'f')}%"


def _verified_ratio_percent_value(numerator: Decimal | None, denominator: Decimal | None) -> str:
	if numerator is None or denominator is None:
		return ""
	if abs(denominator) <= Decimal("0.0001"):
		return ""
	value = (numerator / denominator * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
	return format(value.normalize(), "f")


def _financial_statement_type(context: Dict[str, Any]) -> str:
	metrics = context.get("artifact_metrics") if isinstance(context.get("artifact_metrics"), dict) else {}
	statement_type = str(metrics.get("statement_type") or "").strip().lower()
	if statement_type:
		return statement_type
	sections = context.get("artifact_sections") if isinstance(context.get("artifact_sections"), dict) else {}
	section_keys = {str(key or "").strip().lower() for key in sections.keys()}
	if {"income", "expense"} & section_keys:
		return "profit_and_loss"
	if {"assets", "liabilities", "equity"} & section_keys:
		return "balance_sheet"
	if {"operations", "investing", "financing"} & section_keys:
		return "cash_flow"
	return ""


def _financial_statement_insight_items(context: Dict[str, Any]) -> List[tuple[str, str]]:
	source = context.get("grounded_source") if isinstance(context.get("grounded_source"), dict) else {}
	if str(source.get("family_id") or "").strip() != "financial_statement":
		return []
	statement_type = _financial_statement_type(context)
	insights: List[tuple[str, str]] = []
	if statement_type == "profit_and_loss":
		total_income, income_raw = _artifact_metric_decimal(context, "total_income")
		total_expense, expense_raw = _artifact_metric_decimal(context, "total_expense")
		net_profit, profit_raw = _artifact_metric_decimal(context, "net_profit")
		if total_income is not None and total_expense is not None:
			if total_expense > total_income:
				claim = (
					f"Expenses exceed income by {_artifact_numeric_display('gap', total_expense - total_income)}, "
					"so the current period is loss-making before any deeper drilldown."
				)
			else:
				claim = (
					f"Income exceeds expenses by {_artifact_numeric_display('gap', total_income - total_expense)}, "
					"so the current period is profitable on the visible statement."
				)
			insights.append((claim, f"Total Income: {income_raw}; Total Expense: {expense_raw}"))
			ratio = _ratio_percent(abs(total_expense), abs(total_income))
			if ratio:
				claim = f"Expense burden is {ratio} of income, which explains most of the profit pressure."
				insights.append((claim, f"Total Expense / Total Income = {expense_raw} / {income_raw}"))
		if net_profit is not None and total_income is not None:
			margin = _ratio_percent(net_profit, total_income)
			if margin:
				if net_profit < 0:
					claim = f"Net margin is {margin}, so the statement is showing negative profitability relative to sales."
				else:
					claim = f"Net margin is {margin}, so the statement is showing profitability relative to sales."
				insights.append((claim, f"Net Profit / Total Income = {profit_raw} / {income_raw}"))
		label, number, raw_value = _largest_numeric_row(_artifact_section_rows(context, "expense"))
		if label and number is not None and total_income is not None:
			ratio = _ratio_percent(abs(number), abs(total_income))
			claim = f"The largest visible expense driver is {label} at {_artifact_numeric_display('amount', raw_value)}."
			if ratio:
				claim += f" That is {ratio} of income."
			insights.append((claim, claim))
	elif statement_type == "cash_flow":
		operations, operations_raw = _artifact_metric_decimal(context, "net_cash_from_operations")
		investing, investing_raw = _artifact_metric_decimal(context, "net_cash_from_investing")
		financing, financing_raw = _artifact_metric_decimal(context, "net_cash_from_financing")
		net_change, net_change_raw = _artifact_metric_decimal(context, "net_change_in_cash")
		if operations is not None and net_change is not None:
			if operations > 0 and net_change < 0:
				claim = (
					"Operations generated positive cash, but total cash still decreased, "
					"so the pressure is outside core operating cash generation."
				)
			elif operations < 0:
				claim = "Operations consumed cash, so the cash-flow pressure starts inside the operating cycle."
			else:
				claim = "Operating cash flow is near break-even, so non-operating movements drive the cash result."
			insights.append((claim, f"Net Cash from Operations: {operations_raw}; Net Change in Cash: {net_change_raw}"))
		if financing is not None and net_change is not None and financing < 0:
			claim = (
				f"Financing cash flow is {_artifact_numeric_display('amount', financing_raw)}, "
				"which is the main visible drag on the period cash movement."
			)
			insights.append((claim, claim))
		if investing is not None and investing == 0:
			claim = "Investing cash flow is zero, so the statement does not show major asset-purchase or disposal cash movement in this period."
			insights.append((claim, f"Net Cash from Investing: {investing_raw}"))
		label, number, raw_value = _largest_numeric_row(_artifact_section_rows(context, "operations"))
		if label and number is not None:
			claim = f"The largest visible operating movement is {label} at {_artifact_numeric_display('amount', raw_value)}."
			insights.append((claim, claim))
	elif statement_type == "balance_sheet":
		total_asset, asset_raw = _artifact_metric_decimal(context, "total_asset", "total_assets")
		total_liability, liability_raw = _artifact_metric_decimal(context, "total_liability", "total_liabilities")
		total_equity, equity_raw = _artifact_metric_decimal(context, "total_equity")
		if total_asset is not None and total_liability is not None:
			ratio = _ratio_percent(abs(total_liability), abs(total_asset))
			if ratio:
				claim = f"Liabilities are {ratio} of assets, so leverage is a major part of the balance-sheet picture."
				insights.append((claim, f"Total Liabilities / Total Assets = {liability_raw} / {asset_raw}"))
		if total_asset is not None and total_equity is not None:
			ratio = _ratio_percent(abs(total_equity), abs(total_asset))
			if ratio:
				claim = f"Equity funds {ratio} of assets, showing how much of the asset base is supported by owner capital."
				insights.append((claim, f"Total Equity / Total Assets = {equity_raw} / {asset_raw}"))
		label, number, raw_value = _largest_numeric_row(_artifact_section_rows(context, "assets"))
		if label and number is not None and total_asset is not None:
			ratio = _ratio_percent(abs(number), abs(total_asset))
			claim = f"The largest visible asset line is {label} at {_artifact_numeric_display('amount', raw_value)}."
			if ratio:
				claim += f" That is {ratio} of assets."
			insights.append((claim, claim))
		label, number, raw_value = _largest_numeric_row(_artifact_section_rows(context, "liabilities"))
		if label and number is not None and total_liability is not None:
			ratio = _ratio_percent(abs(number), abs(total_liability))
			claim = f"The largest visible liability line is {label} at {_artifact_numeric_display('amount', raw_value)}."
			if ratio:
				claim += f" That is {ratio} of liabilities."
			insights.append((claim, claim))
	return insights[:6]


def _financial_statement_diagnosis_items(context: Dict[str, Any]) -> List[tuple[str, str]]:
	source = context.get("grounded_source") if isinstance(context.get("grounded_source"), dict) else {}
	if str(source.get("family_id") or "").strip() != "financial_statement":
		return []
	statement_type = _financial_statement_type(context)
	diagnosis: List[tuple[str, str]] = []
	if statement_type == "profit_and_loss":
		total_income, income_raw = _artifact_metric_decimal(context, "total_income")
		total_expense, expense_raw = _artifact_metric_decimal(context, "total_expense")
		net_profit, profit_raw = _artifact_metric_decimal(context, "net_profit")
		if total_income is not None and total_expense is not None and net_profit is not None:
			margin = _ratio_percent(net_profit, total_income) or ""
			if net_profit < 0:
				claim = (
					f"The company is loss-making in this period: expenses exceed income by "
					f"{_artifact_numeric_display('gap', total_expense - total_income)} and net margin is {margin}."
				)
			else:
				claim = (
					f"The company is profitable in this period: income covers expenses and net margin is {margin}."
				)
			diagnosis.append((claim, f"Total Income: {income_raw}; Total Expense: {expense_raw}; Net Profit: {profit_raw}"))
		label, number, raw_value = _largest_numeric_row(_artifact_section_rows(context, "expense"))
		if label and number is not None and total_income is not None:
			ratio = _ratio_percent(abs(number), abs(total_income))
			if ratio:
				claim = (
					f"The main management question is margin quality: {label} consumes {ratio} of income, "
					"so profitability cannot improve materially without understanding this cost driver."
				)
				diagnosis.append((claim, f"{label}: {raw_value}; Total Income: {income_raw}"))
	elif statement_type == "cash_flow":
		operations, operations_raw = _artifact_metric_decimal(context, "net_cash_from_operations")
		financing, financing_raw = _artifact_metric_decimal(context, "net_cash_from_financing")
		net_change, net_change_raw = _artifact_metric_decimal(context, "net_change_in_cash")
		if operations is not None and net_change is not None:
			if operations > 0 and net_change < 0:
				claim = (
					f"Liquidity is being pulled down despite positive operations: operations generated "
					f"{_artifact_numeric_display('amount', operations_raw)}, but net cash still fell by "
					f"{_artifact_numeric_display('amount', abs(net_change))}."
				)
			elif operations < 0:
				claim = (
					f"The operating cycle is consuming cash: operations are {_artifact_numeric_display('amount', operations_raw)}, "
					"so liquidity pressure starts before financing or investing choices."
				)
			else:
				claim = "Cash health is close to operating break-even, so management should focus on non-operating movements and working-capital timing."
			diagnosis.append((claim, f"Operations: {operations_raw}; Net Change in Cash: {net_change_raw}"))
		if financing is not None and financing < 0:
			claim = (
				f"Financing activity is a visible cash drain at {_artifact_numeric_display('amount', financing_raw)}, "
				"so management should confirm whether this is planned capital return or avoidable cash leakage."
			)
			diagnosis.append((claim, claim))
	elif statement_type == "balance_sheet":
		total_asset, asset_raw = _artifact_metric_decimal(context, "total_asset", "total_assets")
		total_liability, liability_raw = _artifact_metric_decimal(context, "total_liability", "total_liabilities")
		total_equity, equity_raw = _artifact_metric_decimal(context, "total_equity")
		if total_asset is not None and total_liability is not None:
			liability_ratio = _ratio_percent(abs(total_liability), abs(total_asset))
			if liability_ratio:
				claim = (
					f"The balance sheet is liability-heavy: liabilities fund {liability_ratio} of assets, "
					"so solvency quality depends on collectable assets and creditor discipline."
				)
				diagnosis.append((claim, f"Total Liabilities: {liability_raw}; Total Assets: {asset_raw}"))
		if total_asset is not None and total_equity is not None:
			equity_ratio = _ratio_percent(abs(total_equity), abs(total_asset))
			if equity_ratio:
				claim = (
					f"Equity support is {equity_ratio} of assets, so management should protect asset quality before taking on more pressure."
				)
				diagnosis.append((claim, f"Total Equity: {equity_raw}; Total Assets: {asset_raw}"))
	return diagnosis[:3]


def _financial_statement_verified_numeric_values(context: Dict[str, Any]) -> List[str]:
	values: List[str] = []
	statement_type = _financial_statement_type(context)
	if statement_type == "profit_and_loss":
		total_income, _income_raw = _artifact_metric_decimal(context, "total_income")
		total_expense, _expense_raw = _artifact_metric_decimal(context, "total_expense")
		net_profit, _profit_raw = _artifact_metric_decimal(context, "net_profit")
		if total_income is not None and total_expense is not None:
			values.append(format(abs(total_expense - total_income), "f"))
			ratio = _verified_ratio_percent_value(abs(total_expense), abs(total_income))
			if ratio:
				values.append(ratio)
		if net_profit is not None and total_income is not None:
			ratio = _verified_ratio_percent_value(net_profit, total_income)
			if ratio:
				values.append(ratio)
		_label, number, _raw_value = _largest_numeric_row(_artifact_section_rows(context, "expense"))
		if number is not None and total_income is not None:
			ratio = _verified_ratio_percent_value(abs(number), abs(total_income))
			if ratio:
				values.append(ratio)
	elif statement_type == "balance_sheet":
		total_asset, _asset_raw = _artifact_metric_decimal(context, "total_asset", "total_assets")
		total_liability, _liability_raw = _artifact_metric_decimal(context, "total_liability", "total_liabilities")
		total_equity, _equity_raw = _artifact_metric_decimal(context, "total_equity")
		if total_asset is not None and total_liability is not None:
			ratio = _verified_ratio_percent_value(abs(total_liability), abs(total_asset))
			if ratio:
				values.append(ratio)
		if total_asset is not None and total_equity is not None:
			ratio = _verified_ratio_percent_value(abs(total_equity), abs(total_asset))
			if ratio:
				values.append(ratio)
		_label, number, _raw_value = _largest_numeric_row(_artifact_section_rows(context, "assets"))
		if number is not None and total_asset is not None:
			ratio = _verified_ratio_percent_value(abs(number), abs(total_asset))
			if ratio:
				values.append(ratio)
		_label, number, _raw_value = _largest_numeric_row(_artifact_section_rows(context, "liabilities"))
		if number is not None and total_liability is not None:
			ratio = _verified_ratio_percent_value(abs(number), abs(total_liability))
			if ratio:
				values.append(ratio)
	return values


def _financial_statement_takeaway(context: Dict[str, Any]) -> str:
	statement_type = _financial_statement_type(context)
	if statement_type == "profit_and_loss":
		return "Consultant takeaway: focus first on margin pressure, expense burden, and the largest cost drivers before assigning causes."
	if statement_type == "cash_flow":
		return "Consultant takeaway: separate operating cash generation from financing or investing movements before judging liquidity health."
	if statement_type == "balance_sheet":
		return "Consultant takeaway: read this as capital structure plus asset quality; liabilities, receivables, stock, and equity support should be reviewed together."
	return "Consultant takeaway: use the statement totals and major lines as the decision evidence before assigning unsupported causes."


def _financial_statement_action_guidance_items(context: Dict[str, Any]) -> List[tuple[str, str]]:
	statement_type = _financial_statement_type(context)
	guidance: List[tuple[str, str]] = []
	if statement_type == "profit_and_loss":
		total_income, income_raw = _artifact_metric_decimal(context, "total_income")
		total_expense, expense_raw = _artifact_metric_decimal(context, "total_expense")
		net_profit, profit_raw = _artifact_metric_decimal(context, "net_profit")
		label, number, raw_value = _largest_numeric_row(_artifact_section_rows(context, "expense"))
		if total_income is not None and total_expense is not None and total_expense > total_income:
			claim = (
				f"Set the first profit-recovery target at {_artifact_numeric_display('gap', total_expense - total_income)}: "
				"management needs either cost reduction, margin improvement, or sales mix improvement of at least that scale to return to break-even."
			)
			guidance.append((claim, f"Total Expense: {expense_raw}; Total Income: {income_raw}"))
		if label and number is not None and total_income is not None:
			ratio = _ratio_percent(abs(number), abs(total_income))
			if ratio:
				claim = (
					f"Start with {label}, not small overhead lines: it represents {ratio} of income, "
					"so even a modest improvement there can move profit more than scattered minor cuts."
				)
				guidance.append((claim, f"{label}: {raw_value}; Total Income: {income_raw}"))
		if net_profit is not None and total_income is not None:
			margin = _ratio_percent(net_profit, total_income)
			if margin and net_profit < 0:
				claim = (
					f"Track recovery using net margin, currently {margin}; a positive margin target is clearer than only watching absolute profit."
				)
				guidance.append((claim, f"Net Profit: {profit_raw}; Total Income: {income_raw}"))
	elif statement_type == "cash_flow":
		operations, operations_raw = _artifact_metric_decimal(context, "net_cash_from_operations")
		financing, financing_raw = _artifact_metric_decimal(context, "net_cash_from_financing")
		net_change, net_change_raw = _artifact_metric_decimal(context, "net_change_in_cash")
		operation_rows = _artifact_section_rows(context, "operations")
		if operations is not None and operations > 0:
			claim = (
				f"Protect the positive operating cash base of {_artifact_numeric_display('amount', operations_raw)} before approving discretionary outflows."
			)
			guidance.append((claim, f"Net Cash from Operations: {operations_raw}"))
		if financing is not None and financing < 0:
			claim = (
				f"Review the financing outflow of {_artifact_numeric_display('amount', financing_raw)} as a board-level cash decision; "
				"confirm whether it is one-off, policy-driven, or avoidable."
			)
			guidance.append((claim, f"Net Cash from Financing: {financing_raw}"))
		for key in ("Net Change in Accounts Receivable", "Net Change in Inventory", "Net Change in Trade Payables"):
			for row in operation_rows:
				label = str(row.get("label") or row.get("line") or row.get("account") or "").strip()
				if label != key:
					continue
				value = row.get("amount")
				number = _artifact_numeric_decimal(value)
				if number is None:
					continue
				direction = "cash drag" if number < 0 else "cash support"
				claim = f"Treat {label} as a working-capital lever: it is {_artifact_numeric_display('amount', value)}, a visible {direction} in operating cash."
				guidance.append((claim, claim))
				break
		if net_change is not None and net_change < 0:
			claim = (
				f"Use the net cash decrease of {_artifact_numeric_display('amount', abs(net_change))} as the immediate liquidity checkpoint."
			)
			guidance.append((claim, f"Net Change in Cash: {net_change_raw}"))
	elif statement_type == "balance_sheet":
		total_asset, asset_raw = _artifact_metric_decimal(context, "total_asset", "total_assets")
		total_liability, liability_raw = _artifact_metric_decimal(context, "total_liability", "total_liabilities")
		asset_label, asset_number, asset_value = _largest_numeric_row(_artifact_section_rows(context, "assets"))
		liability_label, liability_number, liability_value = _largest_numeric_row(_artifact_section_rows(context, "liabilities"))
		if total_asset is not None and total_liability is not None:
			ratio = _ratio_percent(abs(total_liability), abs(total_asset))
			if ratio:
				claim = (
					f"Manage leverage before growth: liabilities are {ratio} of assets, so new commitments should be tied to cash recovery or asset quality improvement."
				)
				guidance.append((claim, f"Total Liabilities: {liability_raw}; Total Assets: {asset_raw}"))
		if asset_label and asset_number is not None:
			claim = (
				f"Review the quality of the largest asset line, {asset_label} at {_artifact_numeric_display('amount', asset_value)}, "
				"because balance-sheet strength depends on whether that asset converts to cash or economic value."
			)
			guidance.append((claim, claim))
		if liability_label and liability_number is not None:
			claim = (
				f"Negotiate or schedule the largest liability pressure, {liability_label} at {_artifact_numeric_display('amount', liability_value)}, "
				"before it constrains supplier or lender confidence."
			)
			guidance.append((claim, claim))
	return guidance[:4]


def _financial_statement_recommendations(context: Dict[str, Any], supported_claims: List[Dict[str, str]]) -> List[Dict[str, Any]]:
	statement_type = _financial_statement_type(context)
	if not bool(context.get("recommendation_allowed")):
		return []
	claim_count = len(supported_claims)
	default_refs = list(range(min(claim_count, 4)))
	if not default_refs:
		return []
	if statement_type == "profit_and_loss":
		return [
			{
				"action": "Investigate the largest cost driver before making broad cost cuts.",
				"rationale": "The current statement shows margin pressure and identifies the largest visible expense driver, so targeted review is safer than across-the-board action.",
				"basis_claim_refs": default_refs,
			},
			{
				"action": "Review product margin, purchase cost, stock movement, and sales mix with a supporting detail view.",
				"rationale": "The statement proves account-level pressure, but source-level causes require governed transaction or item detail.",
				"basis_claim_refs": default_refs,
			},
		]
	if statement_type == "cash_flow":
		return [
			{
				"action": "Separate operating cash performance from financing movement before judging liquidity health.",
				"rationale": "The statement shows positive operating cash while total cash still decreases, so the cash problem is not explained by operations alone.",
				"basis_claim_refs": default_refs,
			},
			{
				"action": "Review receivable movement, inventory movement, payables movement, and the financing outflow together.",
				"rationale": "Those visible cash-flow lines explain the working-capital and financing levers that management can investigate next.",
				"basis_claim_refs": default_refs,
			},
		]
	if statement_type == "balance_sheet":
		return [
			{
				"action": "Review debtor quality and creditor pressure together before deciding the next financing action.",
				"rationale": "The statement shows liabilities, equity support, Debtors, and Creditors as major balance-sheet drivers.",
				"basis_claim_refs": default_refs,
			},
			{
				"action": "Use AR aging, AP aging, and inventory detail as the next supporting views.",
				"rationale": "The balance sheet identifies where exposure sits, but those supporting views explain collectability, payment pressure, and stock quality.",
				"basis_claim_refs": default_refs,
			},
		]
	return []


def _build_financial_statement_consultant_payload(
	*,
	reasoning_type: str,
	grounding_context: Dict[str, Any],
	presentation_preferences: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	if str(reasoning_type or "").strip() not in {"interpretation", "explanation", "recommendation", "continuation_detail"}:
		return {}
	context = dict(grounding_context or {})
	insights = _financial_statement_insight_items(context)
	if len(insights) < 3:
		return {}
	verified_numeric_values = _artifact_sections_verified_numeric_values(context)
	for value in (context.get("artifact_metrics") or {}).values():
		number = _artifact_numeric_decimal(value)
		if number is not None:
			verified_numeric_values.append(format(number, "f"))
	verified_numeric_values.extend(_financial_statement_verified_numeric_values(context))
	source_name = (
		str((context.get("grounding_summary") or {}).get("latest_assistant_title") or "").strip()
		or str((context.get("grounded_source") or {}).get("source_name") or "").strip()
		or "the current financial statement"
	)
	diagnosis = _financial_statement_diagnosis_items(context)
	action_guidance = _financial_statement_action_guidance_items(context)
	takeaway = _financial_statement_takeaway(context)
	rendered_insights = list(insights[:5])
	rendered_insights.append((takeaway, "The current governed financial statement exposes summary metrics and major line sections."))
	verified_numeric_values.extend(_numeric_values_from_rendered_claims(diagnosis))
	verified_numeric_values.extend(_numeric_values_from_rendered_claims(rendered_insights))
	verified_numeric_values.extend(_numeric_values_from_rendered_claims(action_guidance))
	supported_claims = [{"claim": f"Here is the business reading from {source_name}.", "support": f"Here is the business reading from {source_name}."}]
	for claim, support in diagnosis:
		supported_claims.append({"claim": claim, "support": support})
	for claim, support in rendered_insights:
		supported_claims.append({"claim": claim, "support": support})
	for claim, support in action_guidance:
		supported_claims.append({"claim": claim, "support": support})
	recommendations = _financial_statement_recommendations(context, supported_claims)
	answer_text = _consultant_answer_text(
		source_name=source_name,
		diagnosis=diagnosis,
		insights=rendered_insights,
		action_guidance=action_guidance,
		presentation_preferences=presentation_preferences,
	)
	if str(reasoning_type or "").strip() == "recommendation" and recommendations:
		lines = [answer_text, "", "Recommended next steps:"]
		for item in recommendations:
			action = str(item.get("action") or "").strip()
			rationale = str(item.get("rationale") or "").strip()
			if action and rationale:
				lines.append(f"- {action} {rationale}")
		answer_text = "\n".join(lines)
	return {
		"answer_text": answer_text,
		"supported_claims": supported_claims,
		"recommendations": recommendations if str(reasoning_type or "").strip() == "recommendation" else [],
		"speculation_flags": ["runtime_repaired_to_financial_statement_consultant_sections"],
		"confidence": 0.84,
		"reason": "The answer was rendered from governed financial statement metrics and sections.",
		"_verified_numeric_values": verified_numeric_values,
	}


def _build_artifact_sections_fallback_payload(
	*,
	reasoning_type: str,
	grounding_context: Dict[str, Any],
	presentation_preferences: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	if str(reasoning_type or "").strip() not in {"interpretation", "explanation", "continuation_detail"}:
		return {}
	insights = _artifact_sections_insight_items(dict(grounding_context or {}))
	if len(insights) < 3:
		return {}
	verified_numeric_values = _artifact_sections_verified_numeric_values(dict(grounding_context or {}))
	verified_numeric_values.extend(_numeric_values_from_rendered_claims(insights))
	source_name = (
		str(((grounding_context or {}).get("grounding_summary") or {}).get("latest_assistant_title") or "").strip()
		or str(((grounding_context or {}).get("grounded_source") or {}).get("source_name") or "").strip()
		or "the current ERP result"
	)
	rendered_insights = list(insights[:6])
	if not any("Consultant takeaway:" in str(claim or "") for claim, _support in rendered_insights):
		rendered_insights.append(
			(
				"Consultant takeaway: use scale, timing, and concentration as the first decision lenses before assigning causes or making predictions.",
				"The current artifact exposes summary metrics, distribution, and ranked rows.",
			)
		)
	diagnosis = _artifact_sections_diagnosis_items(dict(grounding_context or {}))
	verified_numeric_values.extend(_numeric_values_from_rendered_claims(diagnosis))
	action_guidance = _artifact_sections_action_guidance_items(dict(grounding_context or {}))
	verified_numeric_values.extend(_numeric_values_from_rendered_claims(action_guidance))
	next_step_action = _contextual_next_step_action(dict(grounding_context or {}))
	next_step_prompt = str(next_step_action.get("user_prompt") or "").strip()
	answer_text = _consultant_answer_text(
		source_name=source_name,
		diagnosis=diagnosis,
		insights=rendered_insights,
		action_guidance=action_guidance,
		next_step_prompt=next_step_prompt,
		presentation_preferences=presentation_preferences,
	)
	supported_claims = [{"claim": f"Here is the business reading from {source_name}.", "support": f"Here is the business reading from {source_name}."}]
	for claim, support in diagnosis:
		supported_claims.append({"claim": claim, "support": support})
	for claim, support in rendered_insights:
		supported_claims.append({"claim": claim, "support": support})
	for claim, support in action_guidance:
		supported_claims.append({"claim": claim, "support": support})
	return {
		"answer_text": answer_text,
		"supported_claims": supported_claims,
		"recommendations": [],
		"offered_next_actions": [next_step_action] if next_step_action else [],
		"speculation_flags": ["runtime_repaired_to_governed_artifact_sections"],
		"confidence": 0.8,
		"reason": "The answer was rendered from governed artifact sections.",
		"_verified_numeric_values": verified_numeric_values,
	}


def _build_prior_grounded_row_detail_payload(
	*,
	reasoning_type: str,
	grounding_context: Dict[str, Any],
	presentation_preferences: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	if str(reasoning_type or "").strip() not in {"interpretation", "explanation", "continuation_detail"}:
		return {}
	context = dict(grounding_context or {})
	if str(context.get("answer_obligation") or "").strip() != "expand_grounded_detail":
		return {}
	if str(context.get("evidence_policy") or "").strip() not in _EXPANSION_EVIDENCE_POLICIES:
		return {}
	focus_text = _prior_grounded_focus_text(context)
	if not focus_text:
		return {}
	scored_rows = [
		(_row_focus_score(row, focus_text), row)
		for row in _context_candidate_rows(context)
	]
	scored_rows = [(score, row) for score, row in scored_rows if score >= 70]
	if not scored_rows:
		return {}
	scored_rows.sort(key=lambda item: item[0], reverse=True)
	close_rows = [
		row
		for score, row in scored_rows
		if score >= max(70, scored_rows[0][0] - 10)
	]
	close_identities = {
		_row_focus_identity(row)
		for row in close_rows
		if _row_focus_identity(row)
	}
	if len(close_identities) > 1:
		return {}
	row = dict(scored_rows[0][1])
	row_label = _row_primary_value(row)
	if not row_label:
		return {}
	numeric_pairs = _row_numeric_pairs(row, limit=6)
	descriptive_pairs = _row_descriptive_pairs(row, limit=5)
	source_name = (
		str(((context or {}).get("grounding_summary") or {}).get("latest_assistant_title") or "").strip()
		or str(((context or {}).get("grounded_source") or {}).get("source_name") or "").strip()
		or "the current ERP result"
	)
	bullets = [f"- The follow-up is about {row_label} from {source_name}."]
	supported_claims = [
		{
			"claim": f"The follow-up is about {row_label} from {source_name}.",
			"support": "The prior grounded answer and a current result row refer to the same line item or entity.",
		}
	]
	if numeric_pairs:
		claim = f"Visible numeric fields: {'; '.join(numeric_pairs)}."
		bullets.append(f"- {claim}")
		supported_claims.append({"claim": claim, "support": claim})
	if descriptive_pairs:
		claim = f"Visible descriptive fields: {'; '.join(descriptive_pairs)}."
		bullets.append(f"- {claim}")
		supported_claims.append({"claim": claim, "support": claim})
	expansion_plan = build_evidence_expansion_plan(
		grounding_context=context,
		focused_row=row,
	)
	guidance = evidence_expansion_user_guidance(expansion_plan)
	if guidance:
		claim = guidance
		bullets.append(f"- {claim}")
		supported_claims.append({"claim": claim, "support": str(expansion_plan.get("reason") or "").strip()})
	answer_text = "\n".join(bullets)
	return {
		"answer_text": answer_text,
		"supported_claims": supported_claims,
		"recommendations": [],
		"speculation_flags": [
			"runtime_repaired_to_prior_grounded_row_detail",
			str(expansion_plan.get("status") or "").strip(),
		],
		"confidence": 0.82,
		"reason": "The answer was rendered from the prior grounded answer and the matching current result row.",
		"evidence_expansion_plan": expansion_plan,
		"_verified_numeric_values": [
			str(value if value is not None else "").replace(",", "").strip()
			for value in row.values()
			if _artifact_numeric_decimal(value) is not None
		],
	}


def _build_visible_table_fallback_payload(
	*,
	reasoning_type: str,
	grounding_context: Dict[str, Any],
	presentation_preferences: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	context = dict(grounding_context or {})
	catalog = context.get("evidence_catalog") if isinstance(context.get("evidence_catalog"), dict) else {}
	visible_text = str(catalog.get("visible_text_excerpt") or "").strip()
	tables = _parse_visible_tables(visible_text)
	if not tables:
		return {}
	summary_tables = [
		table for table in tables
		if len([item for item in (table.get("headers") or []) if str(item or "").strip()]) == 2
	]
	ranked_tables = [
		table for table in tables
		if len([item for item in (table.get("headers") or []) if str(item or "").strip()]) >= 3
	]
	bullets: List[str] = []
	supported_claims: List[Dict[str, str]] = []
	visible_heading = _visible_result_heading(visible_text)
	source_name = (
		visible_heading
		or
		str((context.get("grounding_summary") or {}).get("latest_assistant_title") or "").strip()
		or str((context.get("grounded_source") or {}).get("source_name") or "").strip()
		or "the result above"
	)
	if source_name:
		claim = f"Here is the business reading from {source_name}."
		support = "The explanation uses only the visible result above."
		supported_claims.append({"claim": claim, "support": support})
	consultant_insights = _visible_table_consultant_insights(tables)
	rendered_insights = list(consultant_insights[:6])
	if not any("Consultant takeaway:" in str(claim or "") for claim, _support in rendered_insights):
		rendered_insights.append(
			(
				"Consultant takeaway: treat the visible totals, distribution, and ranked rows as the decision evidence; avoid predictions or causes that are not supported by the current ERP result.",
				"This takeaway is derived from the visible summary, distribution, and ranked-row evidence.",
			)
		)
	for claim, support in rendered_insights:
		supported_claims.append({"claim": claim, "support": support})
	if len(rendered_insights) < 3:
		return {}
	diagnosis = _visible_table_diagnosis_items(tables)
	for claim, support in diagnosis:
		supported_claims.append({"claim": claim, "support": support})
	action_guidance = _visible_tables_action_guidance_items(tables)
	for claim, support in action_guidance:
		supported_claims.append({"claim": claim, "support": support})
	next_step_action = _contextual_next_step_action(context)
	if (
		next_step_action
		and str(next_step_action.get("action_id") or "").strip() == "compare_listed_parties_by_overdue_and_intensity"
	):
		entity_scope = _entity_scope_from_tables(tables)
		if entity_scope in {"customers", "suppliers"}:
			next_step_action = dict(next_step_action)
			next_step_action["entity_scope"] = entity_scope
			next_step_action["user_prompt"] = f"Would you like me to compare the listed {entity_scope} by overdue amount and overdue intensity next?"
	next_step_prompt = str(next_step_action.get("user_prompt") or "").strip()
	answer_text = _consultant_answer_text(
		source_name=source_name,
		diagnosis=diagnosis,
		insights=rendered_insights,
		action_guidance=action_guidance,
		next_step_prompt=next_step_prompt,
		presentation_preferences=presentation_preferences,
	)
	verified_numeric_values = _numeric_values_from_rendered_claims(rendered_insights)
	verified_numeric_values.extend(_numeric_values_from_rendered_claims(diagnosis))
	verified_numeric_values.extend(_numeric_values_from_rendered_claims(action_guidance))
	return {
		"answer_text": answer_text,
		"supported_claims": supported_claims,
		"recommendations": [],
		"offered_next_actions": [next_step_action] if next_step_action else [],
		"speculation_flags": ["runtime_numeric_claim_repaired_to_visible_result_sections"],
		"confidence": 0.78,
		"reason": "Runtime answer contained unsupported numeric claims, so the assistant rendered a bounded answer from visible result sections.",
		"_verified_numeric_values": verified_numeric_values,
	}


def _visible_result_heading(visible_text: str) -> str:
	for line in str(visible_text or "").splitlines():
		text = line.strip()
		if not text:
			continue
		if _pipe_table_cells(text) or len(text.split(_TABLE_COLUMN_DELIMITER)) > 1:
			continue
		if text.startswith(("-", "*", "•")):
			continue
		return text[:120]
	return ""


def _build_visible_evidence_fallback_payload(
	*,
	reasoning_type: str,
	grounding_context: Dict[str, Any],
	latest_grounded_turn: Dict[str, Any],
	presentation_preferences: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	if str(reasoning_type or "").strip() not in {"interpretation", "explanation", "continuation_detail"}:
		return {}
	prior_row_detail_payload = _build_prior_grounded_row_detail_payload(
		reasoning_type=reasoning_type,
		grounding_context=grounding_context,
		presentation_preferences=presentation_preferences,
	)
	if prior_row_detail_payload:
		return prior_row_detail_payload
	financial_statement_payload = _build_financial_statement_consultant_payload(
		reasoning_type=reasoning_type,
		grounding_context=grounding_context,
		presentation_preferences=presentation_preferences,
	)
	if financial_statement_payload:
		return financial_statement_payload
	visible_table_payload = _build_visible_table_fallback_payload(
		reasoning_type=reasoning_type,
		grounding_context=grounding_context,
		presentation_preferences=presentation_preferences,
	)
	if visible_table_payload:
		return visible_table_payload
	artifact_sections_payload = _build_artifact_sections_fallback_payload(
		reasoning_type=reasoning_type,
		grounding_context=grounding_context,
		presentation_preferences=presentation_preferences,
	)
	if artifact_sections_payload:
		return artifact_sections_payload
	context = dict(grounding_context or {})
	source = dict(context.get("grounded_source") or {})
	summary = dict(context.get("grounding_summary") or {})
	source_name = (
		str(summary.get("latest_assistant_title") or "").strip()
		or str(source.get("source_name") or "").strip()
		or "the current ERP result"
	)
	rows = [dict(row) for row in (latest_grounded_turn.get("table_rows") or []) if isinstance(row, dict)]
	bullets: List[str] = []
	supported_claims: List[Dict[str, str]] = []
	if source_name:
		claim = f"This answer is limited to {source_name}."
		support = "The current visible ERP result is the grounding source for this follow-up."
		bullets.append(f"- {claim}")
		supported_claims.append({"claim": claim, "support": support})
	if rows:
		claim = "The result includes visible business rows, so it can support a bounded explanation of the current picture."
		support = "The current result shows named rows with numeric facts."
		bullets.append(f"- {claim}")
		supported_claims.append({"claim": claim, "support": support})
	for row in rows[:3]:
		primary = _row_primary_value(row)
		numeric_pairs = _row_numeric_pairs(row, limit=3)
		if not primary or not numeric_pairs:
			continue
		claim = f"A visible row stands out as {primary}."
		support = "; ".join(numeric_pairs)
		bullets.append(f"- {claim} {support}.")
		supported_claims.append({"claim": claim, "support": support})
	if len(bullets) < 2:
		return {}
	if str(reasoning_type or "").strip() == "continuation_detail":
		bullets.append(
			"- I do not have deeper source rows in the current result, so I should not invent transaction-level or item-level detail."
		)
	else:
		bullets.append(
			"- The safe business reading is to treat these visible amounts and rankings as the evidence base, without adding prediction or unsupported causes."
		)
	answer_text = "\n".join(bullets)
	return {
		"answer_text": answer_text,
		"supported_claims": supported_claims,
		"recommendations": [],
		"speculation_flags": ["runtime_numeric_claim_repaired_to_visible_evidence_only"],
		"confidence": 0.75,
		"reason": "Runtime answer contained unsupported numeric claims, so the assistant rendered a bounded visible-evidence fallback.",
	}


_DETERMINISTIC_CONSULTANT_RESPONSE_MODES = {
	"consultant_detail",
	"consultant_interpretation",
	"consultant_recommendation",
}


def _consultant_interpretation_should_use_deterministic_renderer(
	*,
	reasoning_type: str,
	context: Dict[str, Any],
) -> bool:
	reasoning = str(reasoning_type or "").strip()
	if reasoning not in {"interpretation", "explanation"}:
		return False
	response_mode = str((context or {}).get("consultant_response_mode") or "").strip()
	if response_mode not in _DETERMINISTIC_CONSULTANT_RESPONSE_MODES:
		return False
	answer_obligation = str((context or {}).get("answer_obligation") or "").strip()
	if answer_obligation not in {"explain_grounded_meaning", "expand_grounded_detail"}:
		return False
	evidence_policy = str((context or {}).get("evidence_policy") or "").strip()
	return evidence_policy in {"current_result_only", "evidence_expansion_preferred"}


def _build_deterministic_consultant_payload(
	*,
	reasoning_type: str,
	grounding_context: Dict[str, Any],
	presentation_preferences: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	for payload in (
		_build_prior_grounded_row_detail_payload(
			reasoning_type=reasoning_type,
			grounding_context=grounding_context,
			presentation_preferences=presentation_preferences,
		),
		_build_financial_statement_consultant_payload(
			reasoning_type=reasoning_type,
			grounding_context=grounding_context,
			presentation_preferences=presentation_preferences,
		),
		_build_visible_table_fallback_payload(
			reasoning_type=reasoning_type,
			grounding_context=grounding_context,
			presentation_preferences=presentation_preferences,
		),
		_build_artifact_sections_fallback_payload(
			reasoning_type=reasoning_type,
			grounding_context=grounding_context,
			presentation_preferences=presentation_preferences,
		),
	):
		if payload:
			return payload
	return {}


def _answered_execution_result_from_payload(
	*,
	request_id: str,
	session_id: str,
	reasoning_type: str,
	activation_contract: Dict[str, Any],
	payload: Dict[str, Any],
	agent_meta: Dict[str, Any] | None = None,
) -> ERPBusinessReasoningExecutionResult:
	contract = build_erp_business_reasoning_contract(
		request_id=request_id,
		session_id=session_id,
		reasoning_type=reasoning_type,
		grounding_source_request_id=str(activation_contract.get("grounded_source_request_id") or "").strip(),
		grounding_source_kind=str(activation_contract.get("grounded_source_kind") or "").strip(),
		grounding_family_id=str(activation_contract.get("grounded_family_id") or "").strip(),
		grounding_artifact_type=str(activation_contract.get("grounded_artifact_type") or "").strip(),
		grounding_source_reports=list(activation_contract.get("grounded_source_reports") or []),
		grounding_sufficient=True,
		grounding_gaps=[],
		bounded_domain="erp_business_reasoning",
		reasoning_scope="grounded_only",
		supported_claims=[dict(item) for item in (payload.get("supported_claims") or []) if isinstance(item, dict)],
		recommendations=[dict(item) for item in (payload.get("recommendations") or []) if isinstance(item, dict)],
		offered_next_actions=[dict(item) for item in (payload.get("offered_next_actions") or []) if isinstance(item, dict)],
		speculation_flags=[str(item or "").strip() for item in (payload.get("speculation_flags") or []) if str(item or "").strip()],
		allowed_to_answer=True,
		reason=str(payload.get("reason") or "").strip(),
		confidence=float(payload.get("confidence") or 0.0),
	)
	return ERPBusinessReasoningExecutionResult(
		status="answered",
		answer_text=str(payload.get("answer_text") or "").strip(),
		reasoning_contract=contract.to_payload(),
		agent_meta=dict(agent_meta or {}),
	)


def _current_result_continuation_should_use_deterministic_renderer(
	*,
	reasoning_type: str,
	context: Dict[str, Any],
	prior_reasoning_contract: Dict[str, Any] | None,
	prior_answer_text: str,
) -> bool:
	if str(reasoning_type or "").strip() != "continuation_detail":
		return False
	try:
		prior_contract = dict(prior_reasoning_contract or {})
	except (TypeError, ValueError):
		prior_contract = {}
	evidence_policy = str((context or {}).get("evidence_policy") or "").strip()
	if evidence_policy == "current_result_only":
		return bool(prior_contract)
	if evidence_policy not in _EXPANSION_EVIDENCE_POLICIES:
		return False
	if str((context or {}).get("answer_obligation") or "").strip() != "expand_grounded_detail":
		return False
	if str((context or {}).get("consultant_response_mode") or "").strip() not in _CONSULTANT_EXPANSION_RESPONSE_MODES:
		return False
	if not str(prior_answer_text or "").strip():
		return False
	source = dict((context or {}).get("grounded_source") or {})
	has_source_identity = bool(str(source.get("source_name") or "").strip() or source.get("source_reports"))
	return has_source_identity


def execute_erp_business_reasoning(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	message: str,
	recent_messages: List[Dict[str, str]],
	activation_contract: Dict[str, Any],
	semantic_activation_result: Dict[str, Any],
	latest_grounded_turn: Dict[str, Any],
	latest_family_artifact: Dict[str, Any],
	latest_assistant_payload: Dict[str, Any],
	presentation_preferences: Dict[str, Any] | None = None,
	prior_reasoning_contract: Dict[str, Any] | None = None,
	prior_answer_text: str = "",
) -> ERPBusinessReasoningExecutionResult:
	grounding_sufficient, grounding_gaps = _grounding_sufficient(
		activation_contract=activation_contract,
		semantic_activation_result=semantic_activation_result,
		latest_grounded_turn=latest_grounded_turn,
		prior_reasoning_contract=prior_reasoning_contract,
		prior_answer_text=prior_answer_text,
	)
	intent = dict(semantic_activation_result.get("intent") or {})
	reasoning_type = str(intent.get("reasoning_type") or "").strip()
	if not grounding_sufficient:
		return _insufficient_grounding_result(
			request_id=request_id,
			session_id=session_id,
			reasoning_type=reasoning_type,
			activation_contract=activation_contract,
			grounding_gaps=grounding_gaps,
			reason="Grounding is insufficient for ERP business reasoning execution.",
		)
	if looks_like_predictive_guarantee_claim(message):
		return _insufficient_grounding_result(
			request_id=request_id,
			session_id=session_id,
			reasoning_type=reasoning_type,
			activation_contract=activation_contract,
			grounding_gaps=["predictive_guarantee_requires_governed_policy"],
			reason="Predictive guarantees require an approved governed prediction or collection policy.",
		)
	if looks_like_unsupported_operational_inference_claim(message):
		return _insufficient_grounding_result(
			request_id=request_id,
			session_id=session_id,
			reasoning_type=reasoning_type,
			activation_contract=activation_contract,
			grounding_gaps=["unsupported_operational_inference_requires_governed_evidence"],
			reason="Causal or subjective operational inference requires governed complaint, dispute, sentiment, or delay-reason evidence.",
		)

	context = _build_reasoning_context(
		activation_contract=activation_contract,
		semantic_activation_result=semantic_activation_result,
		latest_grounded_turn=latest_grounded_turn,
		latest_family_artifact=latest_family_artifact,
		latest_assistant_payload=latest_assistant_payload,
		recent_messages=recent_messages,
		presentation_preferences=presentation_preferences,
		prior_reasoning_contract=prior_reasoning_contract,
		prior_answer_text=prior_answer_text,
	)
	offered_next_action_payload = _build_offered_next_action_execution_payload(
		reasoning_type=reasoning_type,
		context=context,
	)
	if offered_next_action_payload:
		offered_action_ok, _offered_action_error = _validate_runtime_payload(
			payload=offered_next_action_payload,
			reasoning_type=reasoning_type,
			activation_contract=activation_contract,
			presentation_preferences=presentation_preferences,
			grounding_context=context,
			verified_numeric_values=[
				str(item or "").strip()
				for item in (offered_next_action_payload.get("_verified_numeric_values") or [])
				if str(item or "").strip()
			],
		)
		if offered_action_ok:
			return _answered_execution_result_from_payload(
				request_id=request_id,
				session_id=session_id,
				reasoning_type=reasoning_type,
				activation_contract=activation_contract,
				payload=offered_next_action_payload,
				agent_meta={"executed_prior_offered_next_action": True},
			)
	if reasoning_type == "recommendation":
		deterministic_recommendation_payload = _build_financial_statement_consultant_payload(
			reasoning_type=reasoning_type,
			grounding_context=context,
			presentation_preferences=presentation_preferences,
		)
		if deterministic_recommendation_payload:
			recommendation_ok, _recommendation_error = _validate_runtime_payload(
				payload=deterministic_recommendation_payload,
				reasoning_type=reasoning_type,
				activation_contract=activation_contract,
				presentation_preferences=presentation_preferences,
				grounding_context=context,
				verified_numeric_values=[
					str(item or "").strip()
					for item in (deterministic_recommendation_payload.get("_verified_numeric_values") or [])
					if str(item or "").strip()
				],
			)
			if recommendation_ok:
				return _answered_execution_result_from_payload(
					request_id=request_id,
					session_id=session_id,
					reasoning_type=reasoning_type,
					activation_contract=activation_contract,
					payload=deterministic_recommendation_payload,
					agent_meta={"deterministic_financial_statement_recommendation": True},
				)
	if _consultant_interpretation_should_use_deterministic_renderer(
		reasoning_type=reasoning_type,
		context=context,
	):
		deterministic_consultant_payload = _build_deterministic_consultant_payload(
			reasoning_type=reasoning_type,
			grounding_context=context,
			presentation_preferences=presentation_preferences,
		)
		if deterministic_consultant_payload:
			consultant_ok, _consultant_error = _validate_runtime_payload(
				payload=deterministic_consultant_payload,
				reasoning_type=reasoning_type,
				activation_contract=activation_contract,
				presentation_preferences=presentation_preferences,
				grounding_context=context,
				verified_numeric_values=[
					str(item or "").strip()
					for item in (deterministic_consultant_payload.get("_verified_numeric_values") or [])
					if str(item or "").strip()
				],
			)
			if consultant_ok:
				return _answered_execution_result_from_payload(
					request_id=request_id,
					session_id=session_id,
					reasoning_type=reasoning_type,
					activation_contract=activation_contract,
					payload=deterministic_consultant_payload,
					agent_meta={"deterministic_consultant_interpretation": True},
				)
	if _current_result_continuation_should_use_deterministic_renderer(
		reasoning_type=reasoning_type,
		context=context,
		prior_reasoning_contract=prior_reasoning_contract,
		prior_answer_text=prior_answer_text,
	):
		continuation_candidates: List[Dict[str, Any]] = []
		for continuation_payload in (
			_build_prior_grounded_row_detail_payload(
				reasoning_type=reasoning_type,
				grounding_context=context,
				presentation_preferences=presentation_preferences,
			),
			_build_financial_statement_consultant_payload(
				reasoning_type=reasoning_type,
				grounding_context=context,
				presentation_preferences=presentation_preferences,
			),
			_build_visible_table_fallback_payload(
				reasoning_type=reasoning_type,
				grounding_context=context,
				presentation_preferences=presentation_preferences,
			),
			_build_artifact_sections_fallback_payload(
				reasoning_type=reasoning_type,
				grounding_context=context,
				presentation_preferences=presentation_preferences,
			),
		):
			if continuation_payload:
				continuation_candidates.append(continuation_payload)
		for continuation_payload in continuation_candidates:
			continuation_ok, _continuation_error = _validate_runtime_payload(
				payload=continuation_payload,
				reasoning_type=reasoning_type,
				activation_contract=activation_contract,
				presentation_preferences=presentation_preferences,
				grounding_context=context,
				verified_numeric_values=[
					str(item or "").strip()
					for item in (continuation_payload.get("_verified_numeric_values") or [])
					if str(item or "").strip()
				],
			)
			if continuation_ok:
				return _answered_execution_result_from_payload(
					request_id=request_id,
					session_id=session_id,
					reasoning_type=reasoning_type,
					activation_contract=activation_contract,
					payload=continuation_payload,
					agent_meta={"deterministic_current_result_continuation": True},
				)
	try:
		data = call_qwen_runtime_reasoning_render(
			request_id=request_id,
			session_id=session_id,
			user_id=user_id,
			site_name=_site_name(),
			message=message,
			recent_messages=recent_messages,
			reasoning_context=context,
		)
	except QwenRuntimeClientError as exc:
		return ERPBusinessReasoningExecutionResult(
			status="runtime_error",
			runtime_error=str(exc),
		)

	payload = dict(data.get("payload") or {})
	payload = _sanitize_runtime_payload(
		payload=payload,
		reasoning_type=reasoning_type,
		presentation_preferences=presentation_preferences,
	)
	ok, validation_error = _validate_runtime_payload(
		payload=payload,
		reasoning_type=reasoning_type,
		activation_contract=activation_contract,
		presentation_preferences=presentation_preferences,
		grounding_context=context,
	)
	if not ok:
		if "numeric facts not present" in str(validation_error or ""):
			fallback_payload = _build_visible_evidence_fallback_payload(
				reasoning_type=reasoning_type,
				grounding_context=context,
				latest_grounded_turn=latest_grounded_turn,
				presentation_preferences=presentation_preferences,
			)
			if fallback_payload:
				fallback_ok, _fallback_error = _validate_runtime_payload(
					payload=fallback_payload,
					reasoning_type=reasoning_type,
					activation_contract=activation_contract,
					presentation_preferences=presentation_preferences,
					grounding_context=context,
					verified_numeric_values=[
						str(item or "").strip()
						for item in (fallback_payload.get("_verified_numeric_values") or [])
						if str(item or "").strip()
					],
				)
				if fallback_ok:
					agent_meta = data.get("agent_meta") if isinstance(data.get("agent_meta"), dict) else {}
					agent_meta = dict(agent_meta or {})
					agent_meta["visible_evidence_fallback"] = True
					agent_meta["discarded_validation_error"] = validation_error
					return _answered_execution_result_from_payload(
						request_id=request_id,
						session_id=session_id,
						reasoning_type=reasoning_type,
						activation_contract=activation_contract,
						payload=fallback_payload,
						agent_meta=agent_meta,
					)
		return ERPBusinessReasoningExecutionResult(
			status="invalid_payload",
			validation_error=validation_error,
			agent_meta=data.get("agent_meta") if isinstance(data.get("agent_meta"), dict) else {},
		)

	payload = _payload_with_contextual_next_step(payload, context)
	return _answered_execution_result_from_payload(
		request_id=request_id,
		session_id=session_id,
		reasoning_type=reasoning_type,
		activation_contract=activation_contract,
		payload=payload,
		agent_meta=data.get("agent_meta") if isinstance(data.get("agent_meta"), dict) else {},
	)


def run_phase6c_reasoning_execution_smoke() -> Dict[str, Any]:
	result = execute_erp_business_reasoning(
		request_id="phase6c-reasoning",
		session_id="phase6c",
		user_id="Administrator",
		message="what does this mean",
		recent_messages=[
			{"role": "assistant", "content": "Accounts Receivable Summary for the company shows severe overdue concentration."},
		],
		activation_contract={
			"activation_state": "eligible",
			"grounded_context_available": True,
			"grounded_source_request_id": "artifact-trace-1",
			"grounded_source_kind": "report",
			"grounded_source_name": "Accounts Receivable Summary",
			"grounded_family_id": "aging",
			"grounded_artifact_type": "normalized_family_artifact",
			"grounded_source_reports": ["Accounts Receivable Summary"],
			"grounded_capability_id": "accounts_receivable_read",
			"grounding_summary": {
				"company": "Mingalar Mobile Distribution Co., Ltd.",
				"report_date": "2026-03-26",
				"response_policy_mode": "grounded_analysis",
			},
			"allowed_reasoning_types": ["interpretation", "explanation", "recommendation", "continuation_detail"],
			"route_target": "reasoning_lane",
		},
		semantic_activation_result={
			"status": "accepted",
			"intent": {
				"reasoning_type": "interpretation",
				"confidence": 0.95,
				"reason": "Grounded meaning question over prior AR summary.",
			},
		},
		latest_grounded_turn={
			"grounded": True,
			"trace_request_id": "artifact-trace-1",
			"source_kind": "report",
			"source_name": "Accounts Receivable Summary",
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"date_range": {"report_date": "2026-03-26"},
			"artifact_family_id": "aging",
			"artifact_type": "normalized_family_artifact",
			"artifact_source_reports": ["Accounts Receivable Summary"],
			"returned_schema": ["customer", "outstanding", "over_121_days"],
			"table_rows": [
				{"customer": "35th Street Mobile Wholesale", "outstanding": "44,324,000", "over_121_days": "33,447,000"},
				{"customer": "Bayint Naung Wholesale Mobile", "outstanding": "37,565,500", "over_121_days": "26,430,500"},
			],
			"row_count": 10,
		},
		latest_family_artifact={
			"family_id": "aging",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Accounts Receivable Summary"],
			"capability_id": "accounts_receivable_read",
		},
		latest_assistant_payload={"title": "Accounts Receivable Summary"},
	)
	if result.status != "answered":
		raise RuntimeError(f"Phase 6C reasoning execution smoke failed with status `{result.status}`.")
	contract = dict(result.reasoning_contract or {})
	if not bool(contract.get("allowed_to_answer")):
		raise RuntimeError("Phase 6C reasoning execution smoke failed: allowed_to_answer is false.")
	if str(contract.get("reasoning_type") or "").strip() != "interpretation":
		raise RuntimeError("Phase 6C reasoning execution smoke failed: reasoning_type mismatch.")
	if not str(result.answer_text or "").strip():
		raise RuntimeError("Phase 6C reasoning execution smoke failed: empty answer_text.")
	return {
		"ok": True,
		"result": result.to_payload(),
	}


def run_phase6d_reasoning_continuation_smoke() -> Dict[str, Any]:
	result = execute_erp_business_reasoning(
		request_id="phase6d-continuation",
		session_id="phase6d",
		user_id="Administrator",
		message="explain that recommendation more",
		recent_messages=[
			{"role": "assistant", "content": "Management should prioritize overdue receivables collection on the largest balances first and open supplier payment-plan discussions."},
		],
		activation_contract={
			"activation_state": "eligible",
			"grounded_context_available": True,
			"grounded_source_request_id": "artifact-trace-2",
			"grounded_source_kind": "report",
			"grounded_source_name": "AR / AP Summary",
			"grounded_family_id": "aging",
			"grounded_artifact_type": "normalized_family_artifact",
			"grounded_source_reports": ["Accounts Receivable Summary", "Accounts Payable Summary"],
			"grounded_capability_id": "ar_ap_analysis_read",
			"grounding_summary": {
				"company": "Mingalar Mobile Distribution Co., Ltd.",
				"report_date": "2026-03-26",
				"response_policy_mode": "grounded_analysis",
			},
			"allowed_reasoning_types": ["interpretation", "explanation", "recommendation", "continuation_detail"],
			"route_target": "reasoning_lane",
		},
		semantic_activation_result={
			"status": "accepted",
			"intent": {
				"reasoning_type": "continuation_detail",
				"confidence": 0.93,
				"reason": "User is asking to expand the prior grounded recommendation.",
			},
		},
		latest_grounded_turn={
			"grounded": True,
			"trace_request_id": "artifact-trace-2",
			"source_kind": "report",
			"source_name": "AR / AP Summary",
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"date_range": {"report_date": "2026-03-26"},
			"artifact_family_id": "aging",
			"artifact_type": "normalized_family_artifact",
			"artifact_source_reports": ["Accounts Receivable Summary", "Accounts Payable Summary"],
			"returned_schema": ["metric", "value"],
			"table_rows": [
				{"metric": "Accounts Receivable Outstanding", "value": "288,345,000"},
				{"metric": "Accounts Payable Outstanding", "value": "701,339,600"},
				{"metric": "AR Overdue Ratio", "value": "92.9%"},
				{"metric": "AP Overdue Ratio", "value": "91.9%"},
			],
			"row_count": 4,
		},
		latest_family_artifact={
			"family_id": "aging",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Accounts Receivable Summary", "Accounts Payable Summary"],
			"capability_id": "ar_ap_analysis_read",
		},
		latest_assistant_payload={"title": "AR / AP working capital analysis"},
		prior_reasoning_contract={
			"type": "qwen_erp_business_reasoning_contract",
			"grounding_source_request_id": "artifact-trace-2",
			"grounding_source_kind": "report",
			"grounding_family_id": "aging",
			"grounding_artifact_type": "normalized_family_artifact",
			"grounding_source_reports": ["Accounts Receivable Summary", "Accounts Payable Summary"],
			"grounding_sufficient": True,
			"allowed_to_answer": True,
			"reasoning_type": "recommendation",
			"reason": "Recommendations are tied directly to the grounded AR/AP imbalance and overdue ratios.",
			"supported_claims": [
				{
					"claim": "Working-capital pressure is severe.",
					"support": "Payables exceed receivables by more than 400 MMK Million and both overdue ratios exceed 91%.",
				}
			],
			"recommendations": [
				{
					"action": "Prioritize overdue receivables collection on the largest balances first.",
					"rationale": "AR is heavily overdue, so cash recovery is the fastest grounded lever.",
				},
				{
					"action": "Open supplier payment-plan discussions with the most exposed vendors.",
					"rationale": "AP is also heavily overdue, so supplier stability needs immediate containment.",
				},
			],
			"speculation_flags": [],
		},
		prior_answer_text="Management should prioritize overdue receivables collection on the largest balances first and open supplier payment-plan discussions with major suppliers.",
	)
	if result.status != "answered":
		raise RuntimeError(f"Phase 6D reasoning continuation smoke failed with status `{result.status}`.")
	contract = dict(result.reasoning_contract or {})
	if str(contract.get("reasoning_type") or "").strip() != "continuation_detail":
		raise RuntimeError("Phase 6D reasoning continuation smoke failed: reasoning_type mismatch.")
	if not bool(contract.get("allowed_to_answer")):
		raise RuntimeError("Phase 6D reasoning continuation smoke failed: allowed_to_answer is false.")
	if not str(result.answer_text or "").strip():
		raise RuntimeError("Phase 6D reasoning continuation smoke failed: empty answer_text.")
	return {
		"ok": True,
		"result": result.to_payload(),
	}


def run_phase6d_reasoning_continuation_guardrail_smoke() -> Dict[str, Any]:
	result = execute_erp_business_reasoning(
		request_id="phase6d-continuation-guardrail",
		session_id="phase6d",
		user_id="Administrator",
		message="explain that recommendation more",
		recent_messages=[
			{"role": "assistant", "content": "Management should prioritize overdue receivables collection on the largest balances first."},
		],
		activation_contract={
			"activation_state": "eligible",
			"grounded_context_available": True,
			"grounded_source_request_id": "artifact-trace-current",
			"grounded_source_kind": "report",
			"grounded_source_name": "Accounts Receivable Summary",
			"grounded_family_id": "aging",
			"grounded_artifact_type": "normalized_family_artifact",
			"grounded_source_reports": ["Accounts Receivable Summary"],
			"grounded_capability_id": "accounts_receivable_read",
			"grounding_summary": {
				"company": "Mingalar Mobile Distribution Co., Ltd.",
				"report_date": "2026-03-26",
				"response_policy_mode": "grounded_analysis",
			},
			"allowed_reasoning_types": ["interpretation", "explanation", "recommendation", "continuation_detail"],
			"route_target": "reasoning_lane",
		},
		semantic_activation_result={
			"status": "accepted",
			"intent": {
				"reasoning_type": "continuation_detail",
				"confidence": 0.91,
				"reason": "User is asking to expand the prior grounded recommendation.",
			},
		},
		latest_grounded_turn={
			"grounded": True,
			"trace_request_id": "artifact-trace-current",
			"source_kind": "report",
			"source_name": "Accounts Receivable Summary",
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"date_range": {"report_date": "2026-03-26"},
			"artifact_family_id": "aging",
			"artifact_type": "normalized_family_artifact",
			"artifact_source_reports": ["Accounts Receivable Summary"],
			"row_count": 10,
		},
		latest_family_artifact={
			"family_id": "aging",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Accounts Receivable Summary"],
			"capability_id": "accounts_receivable_read",
		},
		latest_assistant_payload={"title": "Accounts Receivable Summary"},
		prior_reasoning_contract={
			"type": "qwen_erp_business_reasoning_contract",
			"grounding_source_request_id": "artifact-trace-prior",
			"grounding_source_kind": "report",
			"grounding_family_id": "aging",
			"grounding_artifact_type": "normalized_family_artifact",
			"grounding_source_reports": ["Accounts Receivable Summary"],
			"grounding_sufficient": True,
			"allowed_to_answer": True,
			"reasoning_type": "recommendation",
			"reason": "Recommendations are tied to grounded AR facts.",
			"supported_claims": [],
			"recommendations": [],
			"speculation_flags": [],
		},
		prior_answer_text="Management should prioritize overdue receivables collection first.",
	)
	if result.status != "insufficient_grounding":
		raise RuntimeError(
			f"Phase 6D reasoning continuation guardrail smoke failed with status `{result.status}`."
		)
	contract = dict(result.reasoning_contract or {})
	if bool(contract.get("allowed_to_answer")):
		raise RuntimeError("Phase 6D reasoning continuation guardrail smoke failed: allowed_to_answer should be false.")
	grounding_gaps = {str(item or "").strip() for item in (contract.get("grounding_gaps") or []) if str(item or "").strip()}
	if "prior_reasoning_source_mismatch" not in grounding_gaps:
		raise RuntimeError(
			f"Phase 6D reasoning continuation guardrail smoke failed: expected source mismatch, got {sorted(grounding_gaps)!r}."
		)
	return {
		"ok": True,
		"result": result.to_payload(),
	}
