from __future__ import annotations

from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.contracts import (
	build_knowledge_boundary_contract,
)


def _payload(value: Any) -> Dict[str, Any]:
	return dict(value or {}) if isinstance(value, dict) else {}


def _status(value: Any) -> str:
	return str(value or "").strip()


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [str(value or "").strip() for value in values if str(value or "").strip()]


def _join_boundary_sections(*sections: str) -> str:
	parts: List[str] = []
	seen = set()
	for section in sections:
		text = str(section or "").strip()
		if not text:
			continue
		key = text.casefold()
		if key in seen:
			continue
		seen.add(key)
		parts.append(text)
	return "\n\n".join(parts)


def _clarification_active(
	*,
	clarification_resolution: Dict[str, Any],
	clarification_reason: Dict[str, Any],
) -> bool:
	decision = _status(clarification_resolution.get("decision"))
	if decision in {"reask_pending_clarification", "meta_question", "empty_ack", "fallback_stop"}:
		return True
	if bool(clarification_reason.get("clarification_required")) and _status(clarification_reason.get("recommended_next_lane")) == "clarification":
		return True
	return False


def _artifact_lane_confirmed(
	*,
	governed_scope_contract: Dict[str, Any],
	compiled_execution_audit: Dict[str, Any],
	family_validation: Dict[str, Any],
	semantic_validation: Dict[str, Any],
) -> bool:
	governed_scope_status = _status(governed_scope_contract.get("governed_scope_status"))
	if governed_scope_status not in {"covered_family", "fresh_query_breakout"}:
		return False
	if not bool(compiled_execution_audit.get("runtime_ok")):
		return False
	family_status = _status(compiled_execution_audit.get("family_validation_status")) or _status(family_validation.get("status")) or "not_run"
	semantic_status = _status(compiled_execution_audit.get("semantic_validation_status")) or _status(semantic_validation.get("status")) or "not_run"
	return family_status in {"", "pass", "not_run"} and semantic_status in {"", "pass", "not_run"}


def _reasoning_lane_confirmed(
	*,
	reasoning_contract: Dict[str, Any],
) -> bool:
	return bool(reasoning_contract.get("allowed_to_answer")) and bool(reasoning_contract.get("grounding_sufficient"))


def _front_door_confirmed(
	*,
	front_door_contract: Dict[str, Any],
) -> bool:
	return bool(front_door_contract.get("handle_in_front_door")) and _status(front_door_contract.get("route_target")) in {
		"front_door",
		"handled",
		"",
	}


def _valid_erp_domain(
	*,
	governed_scope_contract: Dict[str, Any],
	reasoning_activation_contract: Dict[str, Any],
	grounded_turn: Dict[str, Any],
	clarification_reason: Dict[str, Any],
) -> bool:
	governed_scope_status = _status(governed_scope_contract.get("governed_scope_status"))
	if governed_scope_status == "unsupported_request":
		return False
	if governed_scope_status in {"covered_family", "fresh_query_breakout", "clarification_needed", "out_of_scope_but_valid_erp_domain"}:
		return True
	if bool(reasoning_activation_contract.get("grounded_context_available")):
		return True
	if bool(grounded_turn.get("grounded")):
		return True
	if _status(clarification_reason.get("primary_domain")):
		return True
	return False


def evaluate_knowledge_boundary(
	*,
	request_id: str,
	session_id: str,
	proposed_lane: str,
	clarification_resolution: Dict[str, Any] | None = None,
	clarification_reason: Dict[str, Any] | None = None,
	front_door_contract: Dict[str, Any] | None = None,
	governed_scope_contract: Dict[str, Any] | None = None,
	compiled_execution_audit: Dict[str, Any] | None = None,
	family_validation: Dict[str, Any] | None = None,
	semantic_validation: Dict[str, Any] | None = None,
	reasoning_activation_contract: Dict[str, Any] | None = None,
	reasoning_contract: Dict[str, Any] | None = None,
	grounded_turn: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	clarification_resolution_payload = _payload(clarification_resolution)
	clarification_reason_payload = _payload(clarification_reason)
	front_door_payload = _payload(front_door_contract)
	governed_scope_payload = _payload(governed_scope_contract)
	compiled_audit_payload = _payload(compiled_execution_audit)
	family_validation_payload = _payload(family_validation)
	semantic_validation_payload = _payload(semantic_validation)
	reasoning_activation_payload = _payload(reasoning_activation_contract)
	reasoning_payload = _payload(reasoning_contract)
	grounded_turn_payload = _payload(grounded_turn)

	proposed = _status(proposed_lane)
	clarification_active = _clarification_active(
		clarification_resolution=clarification_resolution_payload,
		clarification_reason=clarification_reason_payload,
	)
	artifact_confirmed = _artifact_lane_confirmed(
		governed_scope_contract=governed_scope_payload,
		compiled_execution_audit=compiled_audit_payload,
		family_validation=family_validation_payload,
		semantic_validation=semantic_validation_payload,
	)
	reasoning_confirmed = _reasoning_lane_confirmed(
		reasoning_contract=reasoning_payload,
	)
	front_door_confirmed = _front_door_confirmed(
		front_door_contract=front_door_payload,
	)
	valid_erp_domain = _valid_erp_domain(
		governed_scope_contract=governed_scope_payload,
		reasoning_activation_contract=reasoning_activation_payload,
		grounded_turn=grounded_turn_payload,
		clarification_reason=clarification_reason_payload,
	)

	boundary_flags: List[str] = []
	if clarification_active:
		boundary_flags.append("clarification_active")
	if artifact_confirmed:
		boundary_flags.append("artifact_lane_confirmed")
	if reasoning_confirmed:
		boundary_flags.append("reasoning_lane_confirmed")
	if valid_erp_domain:
		boundary_flags.append("valid_erp_domain")
	if bool(grounded_turn_payload.get("grounded")):
		boundary_flags.append("grounded_turn_available")

	if clarification_active:
		return build_knowledge_boundary_contract(
			request_id=request_id,
			session_id=session_id,
			proposed_lane=proposed,
			final_lane="clarification",
			boundary_status="reclassified" if proposed != "clarification" else "confirmed",
			lane_appropriate=(proposed == "clarification"),
			valid_erp_domain=valid_erp_domain,
			grounding_required=False,
			grounding_available=bool(grounded_turn_payload.get("grounded")),
			knowledge_coverage_state="covered",
			reclassification_reason="Clarification authority still owns the turn.",
			boundary_flags=boundary_flags,
			allowed_to_answer=False,
			safe_next_action="route_to_clarification",
			user_response_mode="boundary_explanation",
			confidence=1.0,
		).to_payload()

	if proposed == "front_door":
		if reasoning_confirmed:
			return build_knowledge_boundary_contract(
				request_id=request_id,
				session_id=session_id,
				proposed_lane=proposed,
				final_lane="reasoning_lane",
				boundary_status="reclassified",
				lane_appropriate=False,
				valid_erp_domain=True,
				grounding_required=True,
				grounding_available=bool(grounded_turn_payload.get("grounded")),
				knowledge_coverage_state="covered_but_wrong_lane",
				reclassification_reason="Grounded reasoning is already available, so front door is not the appropriate final lane.",
				boundary_flags=boundary_flags,
				allowed_to_answer=True,
				safe_next_action="route_to_reasoning_lane",
				user_response_mode="boundary_explanation",
				confidence=0.95,
			).to_payload()
		if artifact_confirmed:
			return build_knowledge_boundary_contract(
				request_id=request_id,
				session_id=session_id,
				proposed_lane=proposed,
				final_lane="artifact_lane",
				boundary_status="reclassified",
				lane_appropriate=False,
				valid_erp_domain=True,
				grounding_required=False,
				grounding_available=bool(grounded_turn_payload.get("grounded")),
				knowledge_coverage_state="covered_but_wrong_lane",
				reclassification_reason="An ERP result is already supported, so front door should not own the turn.",
				boundary_flags=boundary_flags,
				allowed_to_answer=True,
				safe_next_action="route_to_artifact_lane",
				user_response_mode="boundary_explanation",
				confidence=0.95,
			).to_payload()
		if front_door_confirmed:
			return build_knowledge_boundary_contract(
				request_id=request_id,
				session_id=session_id,
				proposed_lane=proposed,
				final_lane="front_door",
				boundary_status="confirmed",
				lane_appropriate=True,
				valid_erp_domain=False,
				grounding_required=False,
				grounding_available=bool(grounded_turn_payload.get("grounded")),
				knowledge_coverage_state="covered",
				reclassification_reason="",
				boundary_flags=boundary_flags,
				allowed_to_answer=True,
				safe_next_action="allow_current_lane",
				user_response_mode="normal_answer",
				confidence=max(0.0, min(1.0, float(front_door_payload.get("confidence") or 0.0))),
			).to_payload()

	if proposed == "artifact_lane":
		governed_scope_status = _status(governed_scope_payload.get("governed_scope_status"))
		if artifact_confirmed:
			return build_knowledge_boundary_contract(
				request_id=request_id,
				session_id=session_id,
				proposed_lane=proposed,
				final_lane="artifact_lane",
				boundary_status="confirmed",
				lane_appropriate=True,
				valid_erp_domain=True,
				grounding_required=False,
				grounding_available=bool(grounded_turn_payload.get("grounded")),
				knowledge_coverage_state="covered",
				reclassification_reason="",
				boundary_flags=boundary_flags,
				allowed_to_answer=True,
				safe_next_action="allow_current_lane",
				user_response_mode="normal_answer",
				confidence=0.96,
			).to_payload()
		if reasoning_confirmed:
			return build_knowledge_boundary_contract(
				request_id=request_id,
				session_id=session_id,
				proposed_lane=proposed,
				final_lane="reasoning_lane",
				boundary_status="reclassified",
				lane_appropriate=False,
				valid_erp_domain=True,
				grounding_required=True,
				grounding_available=bool(grounded_turn_payload.get("grounded")),
				knowledge_coverage_state="covered_but_wrong_lane",
				reclassification_reason="The grounded source supports reasoning directly, so artifact lane is not the appropriate final lane.",
				boundary_flags=boundary_flags,
				allowed_to_answer=True,
				safe_next_action="route_to_reasoning_lane",
				user_response_mode="boundary_explanation",
				confidence=0.9,
			).to_payload()
		if governed_scope_status == "out_of_scope_but_valid_erp_domain":
			return build_knowledge_boundary_contract(
				request_id=request_id,
				session_id=session_id,
				proposed_lane=proposed,
				final_lane="valid_erp_domain_uncovered",
				boundary_status="reclassified",
				lane_appropriate=False,
				valid_erp_domain=True,
				grounding_required=False,
				grounding_available=bool(grounded_turn_payload.get("grounded")),
				knowledge_coverage_state="valid_erp_domain_uncovered",
				reclassification_reason="The request is a valid ERP/business domain ask but is not yet covered by the previous-answer lane.",
				boundary_flags=boundary_flags,
				allowed_to_answer=False,
				safe_next_action="respond_uncovered_erp_domain",
				user_response_mode="coverage_gap_explanation",
				confidence=0.88,
			).to_payload()
		if governed_scope_status == "unsupported_request" and not valid_erp_domain:
			return build_knowledge_boundary_contract(
				request_id=request_id,
				session_id=session_id,
				proposed_lane=proposed,
				final_lane="unsupported_request",
				boundary_status="blocked",
				lane_appropriate=False,
				valid_erp_domain=False,
				grounding_required=False,
				grounding_available=bool(grounded_turn_payload.get("grounded")),
				knowledge_coverage_state="unsupported_non_erp",
				reclassification_reason="The request is outside the supported ERP/business surface.",
				boundary_flags=boundary_flags,
				allowed_to_answer=False,
				safe_next_action="respond_unsupported",
				user_response_mode="safe_refusal",
				confidence=0.9,
			).to_payload()

	if proposed == "reasoning_lane":
		if reasoning_confirmed:
			return build_knowledge_boundary_contract(
				request_id=request_id,
				session_id=session_id,
				proposed_lane=proposed,
				final_lane="reasoning_lane",
				boundary_status="confirmed",
				lane_appropriate=True,
				valid_erp_domain=True,
				grounding_required=True,
				grounding_available=bool(grounded_turn_payload.get("grounded")),
				knowledge_coverage_state="covered",
				reclassification_reason="",
				boundary_flags=boundary_flags,
				allowed_to_answer=True,
				safe_next_action="allow_current_lane",
				user_response_mode="normal_answer",
				confidence=max(0.0, min(1.0, float(reasoning_payload.get("confidence") or 0.0))),
			).to_payload()
		if artifact_confirmed:
			return build_knowledge_boundary_contract(
				request_id=request_id,
				session_id=session_id,
				proposed_lane=proposed,
				final_lane="artifact_lane",
				boundary_status="reclassified",
				lane_appropriate=False,
				valid_erp_domain=True,
				grounding_required=False,
				grounding_available=bool(grounded_turn_payload.get("grounded")),
				knowledge_coverage_state="covered_but_wrong_lane",
				reclassification_reason="An ERP result is available, so reasoning lane is not the appropriate final lane for this turn.",
				boundary_flags=boundary_flags,
				allowed_to_answer=True,
				safe_next_action="route_to_artifact_lane",
				user_response_mode="boundary_explanation",
				confidence=0.9,
			).to_payload()
		if valid_erp_domain:
			return build_knowledge_boundary_contract(
				request_id=request_id,
				session_id=session_id,
				proposed_lane=proposed,
				final_lane="valid_erp_domain_uncovered",
				boundary_status="reclassified",
				lane_appropriate=False,
				valid_erp_domain=True,
				grounding_required=bool(reasoning_activation_payload.get("grounded_context_available") or grounded_turn_payload.get("grounded")),
				grounding_available=bool(grounded_turn_payload.get("grounded")),
				knowledge_coverage_state="valid_erp_domain_uncovered",
				reclassification_reason="This is a valid ERP/business ask, but the currently available reasoning support is insufficient.",
				boundary_flags=boundary_flags + _clean_list(reasoning_payload.get("grounding_gaps")),
				allowed_to_answer=False,
				safe_next_action="respond_uncovered_erp_domain",
				user_response_mode="coverage_gap_explanation",
				confidence=0.86,
			).to_payload()

	if valid_erp_domain:
		return build_knowledge_boundary_contract(
			request_id=request_id,
			session_id=session_id,
			proposed_lane=proposed,
			final_lane="valid_erp_domain_uncovered",
			boundary_status="blocked",
			lane_appropriate=False,
			valid_erp_domain=True,
			grounding_required=bool(reasoning_activation_payload.get("grounded_context_available") or grounded_turn_payload.get("grounded")),
			grounding_available=bool(grounded_turn_payload.get("grounded")),
			knowledge_coverage_state="valid_erp_domain_uncovered",
			reclassification_reason="The request stays within ERP/business scope, but no current lane can safely answer it.",
			boundary_flags=boundary_flags,
			allowed_to_answer=False,
			safe_next_action="respond_uncovered_erp_domain",
			user_response_mode="coverage_gap_explanation",
			confidence=0.82,
		).to_payload()

	return build_knowledge_boundary_contract(
		request_id=request_id,
		session_id=session_id,
		proposed_lane=proposed,
		final_lane="unsupported_request",
		boundary_status="blocked",
		lane_appropriate=False,
		valid_erp_domain=False,
		grounding_required=False,
		grounding_available=bool(grounded_turn_payload.get("grounded")),
		knowledge_coverage_state="unsupported_non_erp",
		reclassification_reason="The request is outside the supported ERP/business scope.",
		boundary_flags=boundary_flags,
		allowed_to_answer=False,
		safe_next_action="respond_unsupported",
		user_response_mode="safe_refusal",
		confidence=0.9,
	).to_payload()


def render_knowledge_boundary_answer(
	*,
	boundary_contract: Dict[str, Any] | None,
	detail_answer: str = "",
) -> str:
	boundary_payload = _payload(boundary_contract)
	knowledge_coverage_state = _status(boundary_payload.get("knowledge_coverage_state"))
	user_response_mode = _status(boundary_payload.get("user_response_mode"))
	safe_next_action = _status(boundary_payload.get("safe_next_action"))
	final_lane = _status(boundary_payload.get("final_lane"))
	grounding_required = bool(boundary_payload.get("grounding_required"))
	grounding_available = bool(boundary_payload.get("grounding_available"))
	reclassification_reason = _status(boundary_payload.get("reclassification_reason"))
	detail = str(detail_answer or "").strip()

	if user_response_mode == "coverage_gap_explanation" or knowledge_coverage_state == "valid_erp_domain_uncovered":
		if detail:
			return detail
		base = (
			"I can help with that business question, but I don't have the right ERP result in this chat to answer it accurately yet."
		)
		if grounding_required and not grounding_available:
			base = (
				"I need the relevant ERP data first before I can answer that accurately."
			)
		return _join_boundary_sections(base, detail)

	if user_response_mode == "safe_refusal" or knowledge_coverage_state == "unsupported_non_erp":
		base = (
			"This request falls outside the current ERP assistant coverage, so I can't answer it confidently here."
		)
		return _join_boundary_sections(base, detail)

	if user_response_mode == "boundary_explanation":
		action_messages = {
			"route_to_clarification": "I need one more detail before I can answer accurately.",
			"route_to_artifact_lane": "Let's continue from the ERP result already shown instead of starting a new answer.",
			"route_to_reasoning_lane": "Let's continue from the ERP analysis already in progress.",
			"route_to_front_door": "I can answer that as a general assistant question rather than from the current ERP result.",
		}
		base = action_messages.get(safe_next_action) or (
			"I need to use a safer ERP path before answering."
			if final_lane
			else "This turn should be handled through a safer ERP path."
		)
		return _join_boundary_sections(base, detail or reclassification_reason)

	return detail


def run_phase7b_lane_validation_probe() -> Dict[str, Any]:
	frontdoor_to_artifact = evaluate_knowledge_boundary(
		request_id="phase7b-frontdoor-artifact",
		session_id="phase7b",
		proposed_lane="front_door",
		front_door_contract={
			"handle_in_front_door": True,
			"route_target": "front_door",
			"confidence": 0.92,
		},
		governed_scope_contract={
			"governed_scope_status": "covered_family",
		},
		compiled_execution_audit={
			"runtime_ok": True,
			"family_validation_status": "pass",
			"semantic_validation_status": "pass",
		},
	)
	if _status(frontdoor_to_artifact.get("final_lane")) != "artifact_lane":
		raise RuntimeError("Phase 7B probe failed: front-door case did not reclassify to artifact lane.")
	if _status(frontdoor_to_artifact.get("knowledge_coverage_state")) != "covered_but_wrong_lane":
		raise RuntimeError("Phase 7B probe failed: front-door case coverage state mismatch.")

	reasoning_confirmed = evaluate_knowledge_boundary(
		request_id="phase7b-reasoning-confirmed",
		session_id="phase7b",
		proposed_lane="reasoning_lane",
		reasoning_contract={
			"allowed_to_answer": True,
			"grounding_sufficient": True,
			"confidence": 0.91,
		},
		grounded_turn={
			"grounded": True,
		},
	)
	if _status(reasoning_confirmed.get("final_lane")) != "reasoning_lane":
		raise RuntimeError("Phase 7B probe failed: reasoning case did not confirm reasoning lane.")
	if not bool(reasoning_confirmed.get("lane_appropriate")):
		raise RuntimeError("Phase 7B probe failed: reasoning case should be lane-appropriate.")

	reasoning_uncovered = evaluate_knowledge_boundary(
		request_id="phase7b-reasoning-uncovered",
		session_id="phase7b",
		proposed_lane="reasoning_lane",
		reasoning_activation_contract={
			"grounded_context_available": True,
		},
		reasoning_contract={
			"allowed_to_answer": False,
			"grounding_sufficient": False,
			"grounding_gaps": ["missing_grounded_support"],
		},
		grounded_turn={
			"grounded": True,
		},
	)
	if _status(reasoning_uncovered.get("final_lane")) != "valid_erp_domain_uncovered":
		raise RuntimeError("Phase 7B probe failed: reasoning uncovered case did not classify as valid ERP domain uncovered.")
	if _status(reasoning_uncovered.get("safe_next_action")) != "respond_uncovered_erp_domain":
		raise RuntimeError("Phase 7B probe failed: reasoning uncovered safe_next_action mismatch.")

	return {
		"ok": True,
		"frontdoor_to_artifact": frontdoor_to_artifact,
		"reasoning_confirmed": reasoning_confirmed,
		"reasoning_uncovered": reasoning_uncovered,
	}


def run_phase7d_boundary_response_probe() -> Dict[str, Any]:
	uncovered_boundary = evaluate_knowledge_boundary(
		request_id="phase7d-uncovered",
		session_id="phase7d",
		proposed_lane="reasoning_lane",
		reasoning_activation_contract={
			"grounded_context_available": False,
		},
		reasoning_contract={
			"allowed_to_answer": False,
			"grounding_sufficient": False,
		},
		governed_scope_contract={
			"governed_scope_status": "out_of_scope_but_valid_erp_domain",
		},
	)
	uncovered_answer = render_knowledge_boundary_answer(
		boundary_contract=uncovered_boundary,
		detail_answer="This finance area is not yet covered by the current answer path.",
	)
	if "valid ERP/business question" not in uncovered_answer and "ERP/business scope" not in uncovered_answer:
		raise RuntimeError("Phase 7D probe failed: uncovered response did not explain the coverage gap.")

	unsupported_boundary = evaluate_knowledge_boundary(
		request_id="phase7d-unsupported",
		session_id="phase7d",
		proposed_lane="artifact_lane",
		governed_scope_contract={
			"governed_scope_status": "unsupported_request",
		},
	)
	unsupported_answer = render_knowledge_boundary_answer(
		boundary_contract=unsupported_boundary,
		detail_answer="I can help with ERP reporting and analysis, but not with this request here.",
	)
	if "outside the current ERP assistant coverage" not in unsupported_answer:
		raise RuntimeError("Phase 7D probe failed: unsupported response did not explain the supported boundary.")

	redirect_boundary = evaluate_knowledge_boundary(
		request_id="phase7d-redirect",
		session_id="phase7d",
		proposed_lane="reasoning_lane",
		governed_scope_contract={
			"governed_scope_status": "covered_family",
		},
		compiled_execution_audit={
			"runtime_ok": True,
			"family_validation_status": "pass",
			"semantic_validation_status": "pass",
		},
	)
	redirect_answer = render_knowledge_boundary_answer(
		boundary_contract=redirect_boundary,
		detail_answer="An ERP result is already available for this turn.",
	)
	if "previous ERP answer" not in redirect_answer:
		raise RuntimeError("Phase 7D probe failed: redirect response did not explain the safer lane.")

	return {
		"ok": True,
		"uncovered_answer": uncovered_answer,
		"unsupported_answer": unsupported_answer,
		"redirect_answer": redirect_answer,
	}
