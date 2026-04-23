from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple


def _normalize_text(message: str) -> str:
	text = str(message or "").strip().lower()
	if not text:
		return ""
	text = re.sub(r"[\u2018\u2019]", "'", text)
	text = re.sub(r"[\u201c\u201d]", '"', text)
	text = re.sub(r"[^a-z0-9\s&/.-]+", " ", text)
	text = re.sub(r"\s+", " ", text)
	return text.strip()


def _word_tokens(message: str) -> List[str]:
	normalized = _normalize_text(message)
	if not normalized:
		return []
	return [token for token in re.split(r"[^a-z0-9]+", normalized) if token]


_OPTION_LIST_DIRECT_PHRASES = (
	"show me the list",
	"show the list",
	"show me the list you found",
	"show the list you found",
	"show me the options",
	"show the options",
	"show me the options you found",
	"show the options you found",
	"what are the options",
	"show me what you found",
	"show what you found",
	"what did you find",
	"which ones did you find",
	"list them",
	"show them",
	"show both",
	"show me both",
	"show me the matches",
	"show the matches",
	"show me the list that you found",
	"show me the found list",
	"show me the found items",
	"show me the found options",
	"show me the found matches",
)

_DISCARD_ONLY_PHRASES = (
	"ignore that",
	"ignore it",
	"ignore this",
	"forget that",
	"forget it",
	"forget this",
	"skip that",
	"skip it",
	"skip this",
	"cancel that",
	"cancel this",
	"leave that",
	"leave it",
	"leave this",
	"not that",
	"not that one",
	"skip that one",
	"cancel that one",
)

_DISCARD_PREFIX_PATTERNS = (
	r"ignore\s+(?:that|it|this)",
	r"forget\s+(?:that|it|this)",
	r"skip\s+(?:that|it|this)",
	r"cancel\s+(?:that|it|this)",
	r"leave\s+(?:that|it|this)",
	r"ignore\s+the\s+first\s+question",
	r"forget\s+the\s+first\s+question",
	r"ignore\s+the\s+first\s+one",
	r"forget\s+the\s+first\s+one",
	r"ignore\s+the\s+previous\s+question",
	r"forget\s+the\s+previous\s+question",
	r"ignore\s+the\s+previous\s+request",
	r"forget\s+the\s+previous\s+request",
)

_QUESTION_RESTORE_PHRASES = (
	"answer the last question",
	"answer the last one",
	"answer the last request",
	"answer the previous question",
	"answer the previous one",
	"answer the previous request",
	"repeat the last question",
	"repeat the last one",
	"repeat the previous question",
	"repeat the previous one",
	"go back to the question",
)

_QUESTION_RESTORE_PATTERNS = (
	r"^(?:please\s+)?(?:answer|repeat)\s+the\s+(?:last|previous)\s+(?:question|one|request)(?:\s+please)?$",
	r"^(?:please\s+)?(?:go\s+back|return)\s+to\s+(?:that|the)\s+question(?:\s+please)?$",
)

_SEQUENCE_RESTORE_PHRASES = (
	"continue the previous sequence",
	"resume the previous sequence",
	"go back to the remaining steps",
)

_SEQUENCE_CONTINUATION_PHRASES = (
	"continue",
	"next",
	"yes",
	"ok",
	"okay",
	"go ahead",
	"proceed",
	"continue please",
	"next please",
)

_SEQUENCE_CONTINUATION_PATTERNS = (
	r"^(?:please\s+)?(?:go\s+ahead|continue|proceed)(?:\s+with\s+(?:that|this|the\s+next\s+(?:one|step|part|question)|the\s+remaining\s+steps))?(?:\s+please)?$",
)

_SEQUENCE_STOP_PHRASES = (
	"stop",
	"stop here",
	"no",
	"no thanks",
	"not now",
	"cancel",
	"cancel it",
)

_SEQUENCE_STOP_PATTERNS = (
	r"^(?:please\s+)?stop(?:\s+(?:this|that|the))?\s+(?:sequence|steps?|flow|request)(?:\s+here)?(?:\s+please)?$",
)

_BRANCH_RESTORE_PHRASES = (
	"go back",
	"go back to the previous one",
	"return to the previous one",
	"go back to the previous branch",
)

_TARGETED_BRANCH_RESTORE_PATTERNS = (
	r"^(?:go\s+back|return|switch\s+back|take\s+me\s+back)\s+to\s+(?:the\s+)?(?P<hint>[a-z0-9\s/&.-]+?)\s*$",
	r"^(?:back)\s+to\s+(?:the\s+)?(?P<hint>[a-z0-9\s/&.-]+?)\s*$",
)

_TARGET_RESTORE_TARGETS = {
	"customer": {"target_grain": "customer", "target_focus_kind": "entity"},
	"customers": {"target_grain": "customer", "target_focus_kind": "listing"},
	"customer detail": {"target_grain": "customer", "target_focus_kind": "entity"},
	"customer details": {"target_grain": "customer", "target_focus_kind": "entity"},
	"supplier": {"target_grain": "supplier", "target_focus_kind": "entity"},
	"suppliers": {"target_grain": "supplier", "target_focus_kind": "listing"},
	"supplier detail": {"target_grain": "supplier", "target_focus_kind": "entity"},
	"supplier details": {"target_grain": "supplier", "target_focus_kind": "entity"},
	"item": {"target_grain": "item", "target_focus_kind": "entity"},
	"items": {"target_grain": "item", "target_focus_kind": "listing"},
	"product": {"target_grain": "item", "target_focus_kind": "entity"},
	"products": {"target_grain": "item", "target_focus_kind": "listing"},
	"product detail": {"target_grain": "item", "target_focus_kind": "entity"},
	"product details": {"target_grain": "item", "target_focus_kind": "entity"},
	"item detail": {"target_grain": "item", "target_focus_kind": "entity"},
	"item details": {"target_grain": "item", "target_focus_kind": "entity"},
	"sales invoice": {"target_grain": "sales_invoice", "target_focus_kind": "document"},
	"sales invoices": {"target_grain": "sales_invoice", "target_focus_kind": "listing"},
	"sales invoice detail": {"target_grain": "sales_invoice", "target_focus_kind": "document"},
	"sales invoice details": {"target_grain": "sales_invoice", "target_focus_kind": "document"},
	"purchase invoice": {"target_grain": "purchase_invoice", "target_focus_kind": "document"},
	"purchase invoices": {"target_grain": "purchase_invoice", "target_focus_kind": "listing"},
	"purchase invoice detail": {"target_grain": "purchase_invoice", "target_focus_kind": "document"},
	"purchase invoice details": {"target_grain": "purchase_invoice", "target_focus_kind": "document"},
	"sales order": {"target_grain": "sales_order", "target_focus_kind": "document"},
	"sales orders": {"target_grain": "sales_order", "target_focus_kind": "listing"},
	"sales order detail": {"target_grain": "sales_order", "target_focus_kind": "document"},
	"sales order details": {"target_grain": "sales_order", "target_focus_kind": "document"},
	"purchase order": {"target_grain": "purchase_order", "target_focus_kind": "document"},
	"purchase orders": {"target_grain": "purchase_order", "target_focus_kind": "listing"},
	"purchase order detail": {"target_grain": "purchase_order", "target_focus_kind": "document"},
	"purchase order details": {"target_grain": "purchase_order", "target_focus_kind": "document"},
	"delivery note": {"target_grain": "delivery_note", "target_focus_kind": "document"},
	"delivery notes": {"target_grain": "delivery_note", "target_focus_kind": "listing"},
	"delivery note detail": {"target_grain": "delivery_note", "target_focus_kind": "document"},
	"delivery note details": {"target_grain": "delivery_note", "target_focus_kind": "document"},
	"payment entry": {"target_grain": "payment_entry", "target_focus_kind": "document"},
	"payment entries": {"target_grain": "payment_entry", "target_focus_kind": "listing"},
	"payment entry detail": {"target_grain": "payment_entry", "target_focus_kind": "document"},
	"payment entry details": {"target_grain": "payment_entry", "target_focus_kind": "document"},
	"purchase receipt": {"target_grain": "purchase_receipt", "target_focus_kind": "document"},
	"purchase receipts": {"target_grain": "purchase_receipt", "target_focus_kind": "listing"},
	"purchase receipt detail": {"target_grain": "purchase_receipt", "target_focus_kind": "document"},
	"purchase receipt details": {"target_grain": "purchase_receipt", "target_focus_kind": "document"},
	"statement": {"target_grain": "statement", "target_focus_kind": "statement"},
	"financial statement": {"target_grain": "statement", "target_focus_kind": "statement"},
	"financial statements": {"target_grain": "statement", "target_focus_kind": "statement"},
	"p&l": {"target_grain": "profit_and_loss", "target_focus_kind": "statement"},
	"profit and loss": {"target_grain": "profit_and_loss", "target_focus_kind": "statement"},
	"profit and loss statement": {"target_grain": "profit_and_loss", "target_focus_kind": "statement"},
	"balance sheet": {"target_grain": "balance_sheet", "target_focus_kind": "statement"},
	"cash flow": {"target_grain": "cash_flow", "target_focus_kind": "statement"},
}

_TARGETED_COLLECTION_ALIAS_SUFFIXES = (
	"list",
	"lists",
	"directory",
	"directories",
	"master list",
	"master lists",
)

_TARGETED_COLLECTION_ALIAS_BASES = {
	"customer": ("customer", "customers"),
	"supplier": ("supplier", "suppliers"),
	"item": ("item", "items", "product", "products"),
	"sales_invoice": ("sales invoice", "sales invoices"),
	"purchase_invoice": ("purchase invoice", "purchase invoices"),
	"sales_order": ("sales order", "sales orders"),
	"purchase_order": ("purchase order", "purchase orders"),
	"delivery_note": ("delivery note", "delivery notes"),
	"payment_entry": ("payment entry", "payment entries"),
	"purchase_receipt": ("purchase receipt", "purchase receipts"),
}


def _targeted_collection_alias_target(normalized_hint: str) -> Dict[str, str]:
	for target_grain, surfaces in _TARGETED_COLLECTION_ALIAS_BASES.items():
		for surface in surfaces:
			for suffix in _TARGETED_COLLECTION_ALIAS_SUFFIXES:
				if normalized_hint == f"{surface} {suffix}":
					return {
						"target_grain": target_grain,
						"target_focus_kind": "listing",
					}
	return {}


def _targeted_restore_target_for_hint(hint: str) -> Dict[str, str]:
	normalized_hint = _normalize_text(hint)
	if not normalized_hint:
		return {}
	target = _TARGET_RESTORE_TARGETS.get(normalized_hint)
	if not isinstance(target, dict):
		target = _targeted_collection_alias_target(normalized_hint)
	if not isinstance(target, dict):
		return {}
	return {
		"target_grain": str(target.get("target_grain") or "").strip(),
		"target_focus_kind": str(target.get("target_focus_kind") or "").strip(),
	}


def _matches_any_pattern(normalized: str, patterns: tuple[str, ...]) -> bool:
	for pattern in patterns:
		if re.match(pattern, normalized, flags=re.IGNORECASE):
			return True
	return False


def _looks_like_soft_chained_remainder(message: str) -> bool:
	text = str(message or "").strip()
	if not text:
		return False
	remainder_evidence = _classify_conversation_control_evidence(
		text,
		allow_discard_prefix=False,
	)
	if str(remainder_evidence.get("action_id") or "").strip():
		return True
	tokens = _word_tokens(text)
	if len(tokens) < 2:
		return False
	if re.search(r"[\"“'][^\"”']+[\"”']", text):
		return True
	first_token = tokens[0]
	return first_token in {
		"show",
		"tell",
		"give",
		"list",
		"find",
		"check",
		"do",
		"what",
		"when",
		"which",
		"who",
		"how",
		"where",
		"go",
		"return",
		"back",
		"answer",
		"repeat",
		"resume",
		"continue",
		"stop",
	}


def _extract_discard_prefix_remainder(message: str) -> str:
	text = str(message or "").strip()
	if not text:
		return ""
	separator_pattern = r"(?:\s*[,;:.-]\s*|\s+and\s+|\s+then\s+)"
	regex = rf"^\s*(?:{'|'.join(_DISCARD_PREFIX_PATTERNS)}){separator_pattern}(?P<remainder>.+?)\s*$"
	match = re.match(regex, text, flags=re.IGNORECASE)
	if not match:
		soft_regex = rf"^\s*(?:{'|'.join(_DISCARD_PREFIX_PATTERNS)})\s+(?P<remainder>.+?)\s*$"
		soft_match = re.match(soft_regex, text, flags=re.IGNORECASE)
		if not soft_match:
			return ""
		soft_remainder = str(soft_match.group("remainder") or "").strip()
		if not _looks_like_soft_chained_remainder(soft_remainder):
			return ""
		return soft_remainder
	return str(match.group("remainder") or "").strip()


def _targeted_branch_restore_payload(message: str, normalized: str) -> Dict[str, Any]:
	for pattern in _TARGETED_BRANCH_RESTORE_PATTERNS:
		match = re.match(pattern, normalized, flags=re.IGNORECASE)
		if not match:
			continue
		hint = str(match.group("hint") or "").strip()
		if not hint or hint in {"question", "previous one", "previous branch", "remaining steps"}:
			return {}
		target = _targeted_restore_target_for_hint(hint)
		target_grain = str(target.get("target_grain") or "").strip()
		target_focus_kind = str(target.get("target_focus_kind") or "").strip()
		return {
			"evidence_class": "resume_prior_branch",
			"action_id": "replay_or_restore_prior_branch",
			"evidence_strength": "strong" if target_grain else "moderate",
			"matched_surface_form": normalized,
			"embedded_business_message": "",
			"internal_details": {
				"target_hint": hint,
				"target_grain": target_grain,
				"target_focus_kind": target_focus_kind,
				"targeted_restore": True,
			},
		}
	return {}


def _classify_conversation_control_evidence(message: str, *, allow_discard_prefix: bool) -> Dict[str, Any]:
	normalized = _normalize_text(message)
	if not normalized:
		return {}
	if allow_discard_prefix:
		remainder = _extract_discard_prefix_remainder(message)
		if remainder:
			remainder_evidence = _classify_conversation_control_evidence(
				remainder,
				allow_discard_prefix=False,
			)
			remainder_action_id = str(remainder_evidence.get("action_id") or "").strip()
			if remainder_action_id:
				internal_details = dict(remainder_evidence.get("internal_details") or {})
				internal_details.update(
					{
						"discard_prefix_applied": True,
						"discard_prefix_surface": normalized,
						"discarded_branch_before_action": True,
						"chained_remainder_message": str(remainder or "").strip(),
					}
				)
				return {
					**remainder_evidence,
					"matched_surface_form": normalized,
					"internal_details": internal_details,
				}
			return {
				"evidence_class": "fresh_request_redirect",
				"action_id": "override_with_new_request",
				"evidence_strength": "strong",
				"matched_surface_form": normalized,
				"embedded_business_message": remainder,
				"internal_details": {
					"discard_prefix_applied": True,
					"discard_prefix_surface": normalized,
				},
			}
	if normalized in _DISCARD_ONLY_PHRASES:
		return {
			"evidence_class": "override_discard",
			"action_id": "abandon_current_branch",
			"evidence_strength": "strong",
			"matched_surface_form": normalized,
			"embedded_business_message": "",
			"internal_details": {},
		}
	if normalized in _QUESTION_RESTORE_PHRASES or _matches_any_pattern(normalized, _QUESTION_RESTORE_PATTERNS):
		return {
			"evidence_class": "resume_prior_branch",
			"action_id": "reopen_pending_clarification",
			"evidence_strength": "strong",
			"matched_surface_form": normalized,
			"embedded_business_message": "",
			"internal_details": {},
		}
	if normalized in _SEQUENCE_RESTORE_PHRASES:
		return {
			"evidence_class": "sequence_continuation",
			"action_id": "resume_active_sequence",
			"evidence_strength": "strong",
			"matched_surface_form": normalized,
			"embedded_business_message": "",
			"internal_details": {},
		}
	if normalized in _SEQUENCE_CONTINUATION_PHRASES or _matches_any_pattern(normalized, _SEQUENCE_CONTINUATION_PATTERNS):
		return {
			"evidence_class": "sequence_continuation",
			"action_id": "resume_active_sequence",
			"evidence_strength": "strong" if normalized not in {"yes", "ok", "okay"} else "weak",
			"matched_surface_form": normalized,
			"embedded_business_message": "",
			"internal_details": {},
		}
	if normalized in _SEQUENCE_STOP_PHRASES or _matches_any_pattern(normalized, _SEQUENCE_STOP_PATTERNS):
		return {
			"evidence_class": "sequence_stop",
			"action_id": "stop_active_sequence",
			"evidence_strength": "strong" if normalized not in {"no", "no thanks"} else "weak",
			"matched_surface_form": normalized,
			"embedded_business_message": "",
			"internal_details": {},
		}
	if normalized in _BRANCH_RESTORE_PHRASES:
		return {
			"evidence_class": "resume_prior_branch",
			"action_id": "replay_or_restore_prior_branch",
			"evidence_strength": "strong",
			"matched_surface_form": normalized,
			"embedded_business_message": "",
			"internal_details": {},
		}
	targeted_branch_restore = _targeted_branch_restore_payload(message, normalized)
	if targeted_branch_restore:
		return targeted_branch_restore
	if any(phrase in normalized for phrase in _OPTION_LIST_DIRECT_PHRASES):
		return {
			"evidence_class": "option_list_request",
			"action_id": "show_pending_options",
			"evidence_strength": "strong",
			"matched_surface_form": normalized,
			"embedded_business_message": "",
			"internal_details": {},
		}
	word_set = set(_word_tokens(message))
	if (
		{"list", "found"} <= word_set
		or {"options", "found"} <= word_set
		or {"matches", "found"} <= word_set
	):
		return {
			"evidence_class": "option_list_request",
			"action_id": "show_pending_options",
			"evidence_strength": "moderate",
			"matched_surface_form": normalized,
			"embedded_business_message": "",
			"internal_details": {},
		}
	return {
		"evidence_class": "",
		"action_id": "",
		"evidence_strength": "",
		"matched_surface_form": normalized,
		"embedded_business_message": "",
		"internal_details": {},
	}


def classify_conversation_control_evidence(message: str) -> Dict[str, Any]:
	return _classify_conversation_control_evidence(message, allow_discard_prefix=True)


_STRONG_CONTROL_OWNER_ACTIONS = {
	"abandon_current_branch",
	"override_with_new_request",
	"show_pending_options",
	"reopen_pending_clarification",
	"resume_active_sequence",
	"stop_active_sequence",
	"replay_or_restore_prior_branch",
}


def control_action_id(control_evidence_payload: Dict[str, Any] | None) -> str:
	if not isinstance(control_evidence_payload, dict):
		return ""
	return str(control_evidence_payload.get("action_id") or "").strip()


def control_action_id_from_message_or_evidence(
	message: str,
	control_evidence_payload: Dict[str, Any] | None,
) -> str:
	action_id = control_action_id(control_evidence_payload)
	if action_id:
		return action_id
	classified = dict(classify_conversation_control_evidence(message) or {})
	return control_action_id(classified)


def control_action_is_strong_owner(control_evidence_payload: Dict[str, Any] | None) -> bool:
	return control_action_id(control_evidence_payload) in _STRONG_CONTROL_OWNER_ACTIONS


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def conversation_control_evidence_internal_details(evidence: Dict[str, Any]) -> Dict[str, Any]:
	internal_details = dict(evidence.get("internal_details") or {}) if isinstance(evidence, dict) else {}
	internal_details["source_contract_type"] = "qwen_conversation_control_language_classifier"
	return internal_details


def targeted_restore_hint_from_control_evidence(
	control_evidence_payload: Dict[str, Any] | None,
) -> Tuple[str, str, str]:
	if not isinstance(control_evidence_payload, dict):
		return "", "", ""
	internal_details = (
		control_evidence_payload.get("internal_details")
		if isinstance(control_evidence_payload.get("internal_details"), dict)
		else {}
	)
	return (
		_clean_text(internal_details.get("target_hint")),
		_clean_text(internal_details.get("target_grain")),
		_clean_text(internal_details.get("target_focus_kind")),
	)


def targeted_restore_hint_from_message(message: str) -> Tuple[str, str, str]:
	evidence = dict(classify_conversation_control_evidence(message) or {})
	return targeted_restore_hint_from_control_evidence(evidence)


def prior_branch_phrase_type_from_control_action(control_evidence_payload: Dict[str, Any] | None) -> str:
	action_id = control_action_id(control_evidence_payload)
	return {
		"reopen_pending_clarification": "question_restore",
		"resume_active_sequence": "sequence_restore",
		"replay_or_restore_prior_branch": "branch_restore",
	}.get(action_id, "")


def looks_like_option_list_request(message: str) -> bool:
	evidence = classify_conversation_control_evidence(message)
	return str(evidence.get("action_id") or "").strip() == "show_pending_options"


def strip_leading_control_discard_preamble(message: str) -> str:
	return _extract_discard_prefix_remainder(message)


def prior_branch_restore_phrase_type(message: str) -> str:
	evidence = classify_conversation_control_evidence(message)
	action_id = str(evidence.get("action_id") or "").strip()
	if action_id == "reopen_pending_clarification":
		return "question_restore"
	if action_id == "resume_active_sequence":
		return "sequence_restore"
	if action_id == "replay_or_restore_prior_branch":
		return "branch_restore"
	return ""
