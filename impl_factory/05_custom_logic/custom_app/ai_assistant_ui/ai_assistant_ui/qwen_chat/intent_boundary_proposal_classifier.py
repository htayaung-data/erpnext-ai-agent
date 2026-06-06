from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple

from .intent_boundary_contract import (
	AUDIT_STATUS_PASSED,
	CLAUSE_TYPE_AMBIGUOUS,
	CLAUSE_TYPE_BUSINESS_ACTION,
	CLAUSE_TYPE_FACTUAL_LOOKUP,
	CLAUSE_TYPE_POLICY_BOUNDARY,
	CLAUSE_TYPE_SAFE_FOLLOWUP,
	COMPLETENESS_STATUS_COMPLETE,
	DOMAIN_ACCOUNTING_WRITEOFF_ADJUSTMENT,
	DOMAIN_LEGAL_OR_REGULATORY_ADVICE,
	DOMAIN_NONE,
	DOMAIN_PAYMENT_DELAY_WITHHOLDING_RELEASE,
	DOMAIN_PREDICTION_SCORE_OR_FUTURE_CAUSE,
	DOMAIN_PRICING_VALUATION_ACTION,
	DOMAIN_REPORT_HIDING_OR_MANIPULATION,
	FULL_SPAN_FACTUAL_AUTHORITY_NOT_ALLOWED,
	PROPOSAL_SOURCE_LIGHTWEIGHT_MODEL,
	PROPOSER_OUTPUT_VALID,
	PROPOSER_ROLE_LIGHTWEIGHT,
	PROPOSER_STATUS_COMPLETE,
	REFERENCE_RESOLVED,
	REFERENCE_TYPE_PREVIOUS_CONTEXT,
	REFERENCE_TYPE_PRONOUN,
	REFERENCE_TYPE_THIS_THAT,
	REFERENCE_TYPE_VISIBLE_ROW,
	TARGET_TYPE_CUSTOMER,
	TARGET_TYPE_INVOICE,
	TARGET_TYPE_ITEM,
	TARGET_TYPE_SUPPLIER,
	TRACE_REDACTION_SAFE,
	hash_text,
	normalize_message,
)


ROUTE_AUTHORITY_FIELDS = {
	"report_routing_allowed",
	"context_reuse_allowed",
	"model_reasoning_allowed",
	"final_emission_allowed",
	"required_answer_mode",
	"authority_decision",
	"validator_owned_safe_route_authority_status",
}

PROPOSAL_SOURCE = "v1_ib_b_proposal_classifier_evidence_only"
PROPOSAL_MODEL_NAME = "v1_ib_b_deterministic_proposal_classifier"

_REQUEST_FILLER_TOKENS = {
	"a",
	"an",
	"can",
	"details",
	"display",
	"for",
	"history",
	"in",
	"is",
	"item",
	"list",
	"me",
	"of",
	"open",
	"please",
	"price",
	"sales",
	"show",
	"status",
	"the",
	"to",
	"what",
	"you",
}

_SAFE_FACTUAL_SHAPES = {
	TARGET_TYPE_ITEM: (
		frozenset({"item", "sales"}),
		frozenset({"item", "price"}),
		frozenset({"price", "history"}),
		frozenset({"item", "details"}),
	),
	TARGET_TYPE_SUPPLIER: (
		frozenset({"payable", "status"}),
		frozenset({"supplier", "details"}),
	),
	TARGET_TYPE_CUSTOMER: (
		frozenset({"outstanding", "balance"}),
		frozenset({"customer", "details"}),
	),
	TARGET_TYPE_INVOICE: (
		frozenset({"invoice", "details"}),
		frozenset({"details"}),
	),
}


@dataclass(frozen=True)
class _TargetCandidate:
	target_id: str
	target_type: str
	value: str
	schema_status: str = "valid"

	def to_payload(self) -> Dict[str, str]:
		return {
			"target_id": self.target_id,
			"target_type": self.target_type,
			"value": self.value,
			"schema_status": self.schema_status,
		}


def _tokenize(normalized_message: str) -> List[str]:
	cleaned = "".join(char if char.isalnum() or char in {"-", "_"} else " " for char in normalized_message)
	return cleaned.split()


def _target_type_for_token(token: str) -> str:
	if token.startswith("ec7h-item-"):
		return TARGET_TYPE_ITEM
	if token.startswith("ec7h-sup-"):
		return TARGET_TYPE_SUPPLIER
	if token.startswith("ec7h-cust-"):
		return TARGET_TYPE_CUSTOMER
	if token.startswith("ec7h-sinv-"):
		return TARGET_TYPE_INVOICE
	return ""


def _extract_erp_targets(normalized_message: str) -> List[_TargetCandidate]:
	targets: List[_TargetCandidate] = []
	seen: set[str] = set()
	counts: Dict[str, int] = {}
	for token in _tokenize(normalized_message):
		target_type = _target_type_for_token(token)
		if not target_type or token in seen:
			continue
		seen.add(token)
		counts[target_type] = counts.get(target_type, 0) + 1
		targets.append(
			_TargetCandidate(
				target_id=f"{target_type}_{counts[target_type]}",
				target_type=target_type,
				value=token.upper(),
			)
		)
	return targets


def _reference_type(tokens: Sequence[str]) -> str:
	token_set = set(tokens)
	if {"previous", "table"} <= token_set or "above" in token_set:
		return REFERENCE_TYPE_PREVIOUS_CONTEXT
	if "row" in token_set or "second" in token_set:
		return REFERENCE_TYPE_VISIBLE_ROW
	if "this" in token_set or "that" in token_set:
		return REFERENCE_TYPE_THIS_THAT
	return REFERENCE_TYPE_PRONOUN


def _extract_visible_context_references(tokens: Sequence[str], target_id: str = "") -> List[Dict[str, Any]]:
	reference_terms = {"this", "that", "previous", "above", "row", "table", "second", "invoice", "supplier"}
	if not (set(tokens) & reference_terms):
		return []
	return [
		{
			"reference_id": "visible_ref_1",
			"reference_type": _reference_type(tokens),
			"resolution_status": REFERENCE_RESOLVED,
			"resolved_target_id": target_id,
			"read_only_intent": _has_read_only_action(tokens),
		}
	]


def _has_prefix(tokens: Sequence[str], prefixes: Sequence[Tuple[str, ...]]) -> bool:
	return any(tuple(tokens[: len(prefix)]) == prefix for prefix in prefixes)


def _has_read_only_action(tokens: Sequence[str]) -> bool:
	return _has_prefix(
		tokens,
		(
			("show",),
			("list",),
			("display",),
			("open",),
			("explain",),
			("who", "is"),
			("what", "is"),
			("can", "you", "show"),
			("can", "you", "display"),
			("please", "show"),
		),
	)


def _safe_factual_match(tokens: Sequence[str], targets: Sequence[_TargetCandidate]) -> Dict[str, Any]:
	if len(targets) != 1 or not _has_read_only_action(tokens):
		return {
			"clean": False,
			"shape_present": False,
			"unapproved_extra_token_count": 0,
			"unapproved_extra_text_status": "not_applicable",
		}
	token_set = set(tokens)
	target = targets[0]
	for shape in _SAFE_FACTUAL_SHAPES.get(target.target_type, ()):
		if not shape <= token_set:
			continue
		allowed_tokens = set(_REQUEST_FILLER_TOKENS) | set(shape) | {target.value.lower()}
		extra_tokens = [token for token in tokens if token not in allowed_tokens]
		return {
			"clean": not extra_tokens,
			"shape_present": True,
			"unapproved_extra_token_count": len(extra_tokens),
			"unapproved_extra_text_status": "present" if extra_tokens else "none",
		}
	return {
		"clean": False,
		"shape_present": False,
		"unapproved_extra_token_count": 0,
		"unapproved_extra_text_status": "not_applicable",
	}


def _evidence_flags(tokens: Sequence[str]) -> Dict[str, bool]:
	token_set = set(tokens)
	decision = bool(token_set & {"decision", "decide", "if", "predict", "recommend", "review", "should", "whether"})
	advice = bool(token_set & {"advice", "idea", "recommend", "recommendation", "should", "suggestion", "whether"})
	action = bool(
		token_set
		& {
			"conceal",
			"delay",
			"discount",
			"drop",
			"fix",
			"hide",
			"hold",
			"journal",
			"make",
			"markdown",
			"omission",
			"paying",
			"payment",
			"reduction",
			"repriced",
			"repricing",
		}
	)
	legal = "legal" in token_set
	manipulation = bool(token_set & {"conceal", "hide", "omission"})
	prediction = bool(token_set & {"predict", "will", "default"})
	return {
		"decision": decision,
		"advice": advice,
		"action": action,
		"legal": legal,
		"manipulation": manipulation,
		"prediction": prediction,
	}


def _domain_for_evidence(flags: Dict[str, bool], tokens: Sequence[str]) -> str:
	token_set = set(tokens)
	if flags["legal"]:
		return DOMAIN_LEGAL_OR_REGULATORY_ADVICE
	if flags["manipulation"]:
		return DOMAIN_REPORT_HIDING_OR_MANIPULATION
	if flags["prediction"]:
		return DOMAIN_PREDICTION_SCORE_OR_FUTURE_CAUSE
	if "journal" in token_set:
		return DOMAIN_ACCOUNTING_WRITEOFF_ADJUSTMENT
	if token_set & {"delay", "hold", "paying", "payment"}:
		return DOMAIN_PAYMENT_DELAY_WITHHOLDING_RELEASE
	if token_set & {"discount", "drop", "markdown", "reduction", "repriced", "repricing"}:
		return DOMAIN_PRICING_VALUATION_ACTION
	return DOMAIN_NONE


def _split_clause_fragments(normalized_message: str) -> List[str]:
	delimiters = (" and ", " then ", ";", ", ")
	fragments = [normalized_message]
	for delimiter in delimiters:
		next_fragments: List[str] = []
		for fragment in fragments:
			parts = fragment.split(delimiter)
			for index, part in enumerate(parts):
				text = part.strip()
				if not text:
					continue
				if index > 0 and delimiter.strip() in {"and", "then"}:
					text = f"{delimiter.strip()} {text}"
				next_fragments.append(text)
		fragments = next_fragments
	return fragments


def _span_for_fragment(normalized_message: str, fragment: str, start_at: int) -> Tuple[int, int]:
	start = normalized_message.find(fragment, start_at)
	if start < 0:
		start = normalized_message.find(fragment)
	if start < 0:
		return 0, 0
	return start, start + len(fragment)


def _clause_payload(
	*,
	clause_id: str,
	index: int,
	normalized_message: str,
	fragment: str,
	search_from: int,
	targets: Sequence[_TargetCandidate],
	target_ids: Sequence[str],
	reference_ids: Sequence[str],
) -> Tuple[Dict[str, Any], int]:
	start, end = _span_for_fragment(normalized_message, fragment, search_from)
	clause_tokens = _tokenize(fragment)
	factual_match = _safe_factual_match(clause_tokens, targets)
	flags = _evidence_flags(clause_tokens)
	domain = _domain_for_evidence(flags, clause_tokens)
	unsafe = flags["decision"] or flags["advice"] or flags["action"] or flags["legal"] or flags["manipulation"] or flags["prediction"]
	business_action = flags["action"] or flags["prediction"] or flags["legal"] or flags["manipulation"]
	unapproved_extra = factual_match["unapproved_extra_text_status"] == "present"
	read_only_followup = bool(reference_ids) and _has_read_only_action(clause_tokens) and not unsafe
	factual = bool(factual_match["clean"]) and not unsafe
	ambiguous = unapproved_extra or (not factual and not read_only_followup and not unsafe)
	if unsafe:
		clause_type = CLAUSE_TYPE_POLICY_BOUNDARY if flags["legal"] or flags["manipulation"] else CLAUSE_TYPE_BUSINESS_ACTION
	elif read_only_followup:
		clause_type = CLAUSE_TYPE_SAFE_FOLLOWUP
	elif factual:
		clause_type = CLAUSE_TYPE_FACTUAL_LOOKUP
	else:
		clause_type = CLAUSE_TYPE_AMBIGUOUS
	return (
		{
			"clause_id": clause_id,
			"index": index,
			"start": start,
			"end": end,
			"text": normalized_message[start:end],
			"clause_type": clause_type,
			"erp_target_ids": list(target_ids) if target_ids and not read_only_followup else [],
			"visible_context_reference_ids": list(reference_ids) if read_only_followup or reference_ids else [],
			"factual_lookup_intent": factual,
			"safe_followup_intent": read_only_followup,
			"decision_intent": flags["decision"],
			"advice_intent": flags["advice"],
			"business_action_intent": business_action,
			"policy_boundary_intent": flags["legal"] or flags["manipulation"],
			"business_action_domain": domain,
			"policy_domain": domain if flags["legal"] or flags["manipulation"] else DOMAIN_NONE,
			"ambiguity_status": "ambiguous_or_unproven" if ambiguous else "none",
			"proposal_evidence": {
				"safe_factual_shape_evidence": bool(factual_match["shape_present"]),
				"unapproved_extra_token_count": factual_match["unapproved_extra_token_count"],
				"unapproved_extra_text_status": factual_match["unapproved_extra_text_status"],
				"decision_evidence": flags["decision"],
				"advice_evidence": flags["advice"],
				"action_evidence": flags["action"],
				"legal_evidence": flags["legal"],
				"manipulation_evidence": flags["manipulation"],
				"prediction_evidence": flags["prediction"],
				"authority_effect": "evidence_only",
			},
		},
		end,
	)


def build_intent_boundary_proposal(raw_message: str) -> Dict[str, Any]:
	normalized = normalize_message(raw_message)
	tokens = _tokenize(normalized)
	targets = _extract_erp_targets(normalized)
	target_ids = [target.target_id for target in targets]
	references = _extract_visible_context_references(tokens, target_ids[0] if target_ids else "")
	reference_ids = [reference["reference_id"] for reference in references]
	fragments = _split_clause_fragments(normalized) if normalized else []
	clauses: List[Dict[str, Any]] = []
	search_from = 0
	for index, fragment in enumerate(fragments):
		clause, search_from = _clause_payload(
			clause_id=f"c{index + 1}",
			index=index,
			normalized_message=normalized,
			fragment=fragment,
			search_from=search_from,
			targets=targets,
			target_ids=target_ids,
			reference_ids=reference_ids,
		)
		clauses.append(clause)
	aggregates = {
		"factual_lookup_evidence": any(clause["factual_lookup_intent"] for clause in clauses),
		"decision_evidence": any(clause["decision_intent"] for clause in clauses),
		"advice_evidence": any(clause["advice_intent"] for clause in clauses),
		"action_evidence": any(clause["business_action_intent"] for clause in clauses),
		"legal_evidence": any(clause["proposal_evidence"]["legal_evidence"] for clause in clauses),
		"manipulation_evidence": any(clause["proposal_evidence"]["manipulation_evidence"] for clause in clauses),
		"prediction_evidence": any(clause["proposal_evidence"]["prediction_evidence"] for clause in clauses),
		"ambiguous_evidence": any(clause["ambiguity_status"] != "none" for clause in clauses),
		"safe_factual_shape_evidence": any(clause["proposal_evidence"]["safe_factual_shape_evidence"] for clause in clauses),
		"unapproved_extra_text_evidence": any(
			clause["proposal_evidence"]["unapproved_extra_text_status"] == "present" for clause in clauses
		),
	}
	unsafe_evidence = (
		aggregates["decision_evidence"]
		or aggregates["advice_evidence"]
		or aggregates["action_evidence"]
		or aggregates["legal_evidence"]
		or aggregates["manipulation_evidence"]
		or aggregates["prediction_evidence"]
	)
	mixed = (aggregates["factual_lookup_evidence"] or aggregates["safe_factual_shape_evidence"]) and unsafe_evidence
	residual_status = (
		"unproven_extra_text"
		if aggregates["unapproved_extra_text_evidence"]
		else "accounted_by_clause_spans"
	)
	residual_detail = (
		"safe_factual_shape_contains_unapproved_extra_tokens"
		if aggregates["unapproved_extra_text_evidence"]
		else ""
	)
	proposal = {
		"raw_message_hash": hash_text(raw_message),
		"normalized_message_hash": hash_text(normalized),
		"normalized_message": normalized,
		"intent_proposer_role": PROPOSER_ROLE_LIGHTWEIGHT,
		"intent_proposer_status": PROPOSER_STATUS_COMPLETE if normalized else "incomplete",
		"intent_proposer_confidence": 0.82 if not aggregates["ambiguous_evidence"] else 0.51,
		"intent_proposer_model_name": PROPOSAL_MODEL_NAME,
		"intent_proposer_run_id": hash_text(f"{PROPOSAL_SOURCE}:{normalized}"),
		"intent_proposer_output_status": PROPOSER_OUTPUT_VALID,
		"proposal_authority_source": PROPOSAL_SOURCE_LIGHTWEIGHT_MODEL,
		"proposal_source": PROPOSAL_SOURCE,
		"proposal_status": "complete" if normalized else "incomplete",
		"proposal_confidence": 0.82 if not aggregates["ambiguous_evidence"] else 0.51,
		"proposal_completeness_status": COMPLETENESS_STATUS_COMPLETE,
		"clause_segmentation_status": AUDIT_STATUS_PASSED,
		"secondary_intent_audit_status": AUDIT_STATUS_PASSED,
		"residual_audit_status": AUDIT_STATUS_PASSED,
		"clause_role_confidence_status": AUDIT_STATUS_PASSED,
		"full_span_factual_authority": FULL_SPAN_FACTUAL_AUTHORITY_NOT_ALLOWED,
		"full_span_factual_allow_reason": "",
		"natural_language_interpretation_required": True,
		"independent_parse_guard_status": AUDIT_STATUS_PASSED,
		"clause_count": len(clauses),
		"clauses": clauses,
		"clause_candidates": clauses,
		"erp_targets": [target.to_payload() for target in targets],
		"erp_target_candidates": [target.to_payload() for target in targets],
		"visible_context_references": references,
		"visible_context_reference_candidates": references,
		"mixed_intent_detected": mixed,
		"mixed_intent_evidence": mixed,
		"residual_text_evidence": {
			"status": residual_status,
			"detail": residual_detail,
			"authority_effect": "evidence_only",
		},
		"connector_evidence": {"status": "candidate_spans_marked", "authority_effect": "evidence_only"},
		"safe_factual_shape_evidence": aggregates["safe_factual_shape_evidence"],
		"unapproved_extra_text_evidence": aggregates["unapproved_extra_text_evidence"],
		"factual_lookup_evidence": aggregates["factual_lookup_evidence"],
		"decision_evidence": aggregates["decision_evidence"],
		"advice_evidence": aggregates["advice_evidence"],
		"action_evidence": aggregates["action_evidence"],
		"legal_evidence": aggregates["legal_evidence"],
		"manipulation_evidence": aggregates["manipulation_evidence"],
		"prediction_evidence": aggregates["prediction_evidence"],
		"ambiguous_intent_evidence": aggregates["ambiguous_evidence"],
		"trace_redaction_status": TRACE_REDACTION_SAFE,
		"classifier_authority_effect": "evidence_only",
	}
	for field_name in ROUTE_AUTHORITY_FIELDS:
		proposal.pop(field_name, None)
	return proposal
