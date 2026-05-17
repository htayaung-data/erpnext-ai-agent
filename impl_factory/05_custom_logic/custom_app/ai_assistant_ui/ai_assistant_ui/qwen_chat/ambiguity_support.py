from __future__ import annotations

from typing import Any, Dict, Tuple

from ai_assistant_ui.qwen_chat.clarification_translation import translate_clarification_reason_contract
from ai_assistant_ui.qwen_chat.contracts import build_clarification_reason_contract


def followup_report_ambiguity_contract(
	*,
	request_id: str,
	ambiguity_payload: Dict[str, Any],
) -> Tuple[Any, Any]:
	reports = [
		str(value or "").strip()
		for value in (ambiguity_payload.get("report_candidates") or [])
		if str(value or "").strip()
	]
	internal_reason = str(ambiguity_payload.get("reason") or "").strip()
	reason_contract = build_clarification_reason_contract(
		request_id=request_id,
		stage="followup_scope",
		source_contract_type="governed_scope_decision",
		reason_type="report_ambiguity",
		clarification_required=True,
		blocking=True,
		recommended_next_lane="clarification",
		primary_domain=str(ambiguity_payload.get("family_id") or "").strip(),
		ambiguity_flags=["ambiguous_report"],
		candidate_reports=reports,
		suggested_options=reports,
		internal_reason=internal_reason or "The follow-up does not identify a unique governed report view.",
		internal_details={
			"family_id": str(ambiguity_payload.get("family_id") or "").strip(),
			"report_candidates": reports,
			"ambiguity_flags": ["ambiguous_report"],
			"reason": internal_reason,
		},
	)
	return reason_contract, translate_clarification_reason_contract(reason_contract=reason_contract)
