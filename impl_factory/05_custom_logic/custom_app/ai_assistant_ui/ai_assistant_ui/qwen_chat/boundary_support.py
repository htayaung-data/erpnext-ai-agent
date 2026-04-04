from __future__ import annotations

from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.metadata import ontology_concept_aliases, ontology_detect_concepts
from ai_assistant_ui.qwen_chat.observability import (
	record_phase6_observability_event,
	record_phase6_performance_metric,
)
from ai_assistant_ui.qwen_chat.semantic_aliases import get_canonical_key, get_metric_label


def grounded_artifact_evidence_boundary_answer(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any],
) -> str:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	if str(artifact.get("family_id") or "").strip() not in {"entity_detail", "transaction_listing"}:
		return ""
	entity_type = ""
	if isinstance(artifact.get("dimensions"), dict):
		entity_type = str((artifact.get("dimensions") or {}).get("entity_type") or "").strip().lower()
	request_concepts = {
		str(value or "").strip()
		for value in ontology_detect_concepts(raw_message)
		if str(value or "").strip()
	}
	if not request_concepts:
		return ""
	evidence_concepts = artifact_evidence_concepts(artifact, grounded_turn)
	if entity_type in {"sales_invoice", "purchase_invoice"}:
		evidence_concepts = {concept for concept in evidence_concepts if concept != "fulfillment"}
	missing_concepts = request_concepts.difference(evidence_concepts)
	high_risk_missing = [concept for concept in missing_concepts if concept in {"fulfillment"}]
	if not high_risk_missing:
		return ""
	concept_aliases = ontology_concept_aliases(high_risk_missing[0])
	concept_label = str(concept_aliases[0] or "").strip() if concept_aliases else high_risk_missing[0].replace("_", " ")
	return (
		"The current governed artifact does not include direct fields proving that "
		f"{concept_label} status, so I can't confirm it confidently from this artifact alone.\n\n"
		"I can confirm the billing and payment fields shown here, but this question needs governed operational evidence such as "
		"delivery or stock-movement records."
	)


def artifact_enrichment_boundary_answer(
	*,
	followup_resolution,
	compatibility_contract,
) -> str:
	source_capability_id = str(getattr(compatibility_contract, "source_capability_id", "") or "").strip()
	requested_columns = [
		str(item or "").strip()
		for item in (getattr(followup_resolution, "requested_columns", []) or [])
		if str(item or "").strip()
	]
	target_metric = str(getattr(followup_resolution, "target_metric", "") or "").strip()

	def _label_for(value: str) -> str:
		canonical = get_canonical_key(value, capability_id=source_capability_id or None, dimension_or_metric="metric")
		if canonical:
			return str(get_metric_label(canonical) or value or "").strip()
		return str(value or "").replace("_", " ").strip()

	def _join_labels(values: List[str]) -> str:
		clean = [str(value or "").strip() for value in values if str(value or "").strip()]
		if not clean:
			return ""
		if len(clean) == 1:
			return clean[0]
		return ", ".join(clean[:-1]) + f", and {clean[-1]}"

	requested_targets = list(requested_columns or ([target_metric] if target_metric else []))
	raw_requested = [value for value in requested_targets if value]
	requested_labels = []
	for value in requested_targets:
		label = _label_for(value)
		if label and label not in requested_labels:
			requested_labels.append(label)
	label_text = _join_labels(requested_labels) or "the requested columns or metrics"
	base_metric_label = _label_for(target_metric) if target_metric else ""
	source_report = str(getattr(compatibility_contract, "source_report", "") or "").strip()
	report_basis = source_report or "the current governed report"
	missing_reason = str(getattr(compatibility_contract, "reason", "") or "").strip()
	if raw_requested:
		return (
			f"The current governed source cannot safely add {label_text} from {report_basis}.\n\n"
			f"This artifact does not expose those requested fields directly, so this follow-up needs a governed requery instead of local reshaping."
			+ (f"\n\nWhy: {missing_reason}" if missing_reason else "")
		)
	if base_metric_label:
		return (
			f"The current governed source cannot safely switch this artifact to {base_metric_label} from {report_basis}.\n\n"
			"This follow-up needs a governed requery because the requested metric is not directly populated in the current grounded artifact."
			+ (f"\n\nWhy: {missing_reason}" if missing_reason else "")
		)
	return (
		f"The current governed source cannot safely produce that enriched output from {report_basis}.\n\n"
		"This follow-up needs a governed requery instead of local reshaping."
		+ (f"\n\nWhy: {missing_reason}" if missing_reason else "")
	)


def knowledge_boundary_event_level(boundary_payload: Dict[str, Any]) -> str:
	coverage_state = str(boundary_payload.get("knowledge_coverage_state") or "").strip().lower()
	boundary_status = str(boundary_payload.get("boundary_status") or "").strip().lower()
	if coverage_state in {"valid_erp_domain_uncovered", "unsupported_non_erp"}:
		return "warning"
	if boundary_status in {"blocked", "reclassified"}:
		return "warning"
	return "info"


def append_knowledge_boundary_observability(
	session_doc,
	*,
	request_id: str,
	session_id: str,
	boundary_payload: Dict[str, Any],
	latency_ms: int,
	append_tool_payload,
) -> None:
	coverage_state = str(boundary_payload.get("knowledge_coverage_state") or "").strip()
	append_tool_payload(
		session_doc,
		record_phase6_observability_event(
			request_id=request_id,
			session_id=session_id,
			event_family="knowledge_boundary",
			event_name=coverage_state or "answered",
			event_level=knowledge_boundary_event_level(boundary_payload),
			details={
				"final_lane": str(boundary_payload.get("final_lane") or "").strip(),
				"safe_next_action": str(boundary_payload.get("safe_next_action") or "").strip(),
				"user_response_mode": str(boundary_payload.get("user_response_mode") or "").strip(),
				"latency_ms": int(max(0, latency_ms)),
			},
		),
	)
	append_tool_payload(
		session_doc,
		record_phase6_performance_metric(
			request_id=request_id,
			session_id=session_id,
			metric_name="knowledge_boundary_latency",
			metric_value=float(max(0, latency_ms)),
			metric_unit="ms",
			details={
				"knowledge_coverage_state": coverage_state,
				"final_lane": str(boundary_payload.get("final_lane") or "").strip(),
			},
		),
	)


def append_artifact_boundary_observability(
	session_doc,
	*,
	request_id: str,
	session_id: str,
	boundary_name: str,
	latency_ms: int,
	recovery_payload: Dict[str, Any] | None = None,
	grounded_turn_available: bool = False,
	append_tool_payload,
) -> None:
	recovery = dict(recovery_payload or {})
	append_tool_payload(
		session_doc,
		record_phase6_observability_event(
			request_id=request_id,
			session_id=session_id,
			event_family="artifact_boundary",
			event_name=str(boundary_name or "").strip() or "artifact_boundary",
			event_level="warning",
			details={
				"recommended_recovery_action": str(recovery.get("recommended_recovery_action") or "").strip(),
				"recovery_state": str(recovery.get("recovery_state") or "").strip(),
				"source_report": str(recovery.get("source_report") or "").strip(),
				"grounded_context_available": bool(grounded_turn_available),
				"latency_ms": int(max(0, latency_ms)),
			},
		),
	)
	append_tool_payload(
		session_doc,
		record_phase6_performance_metric(
			request_id=request_id,
			session_id=session_id,
			metric_name=f"{str(boundary_name or '').strip() or 'artifact_boundary'}_latency",
			metric_value=float(max(0, latency_ms)),
			metric_unit="ms",
			details={
				"recommended_recovery_action": str(recovery.get("recommended_recovery_action") or "").strip(),
				"recovery_state": str(recovery.get("recovery_state") or "").strip(),
			},
		),
	)


def artifact_evidence_concepts(artifact_payload: Dict[str, Any], grounded_turn: Dict[str, Any]) -> set[str]:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	turn = grounded_turn if isinstance(grounded_turn, dict) else {}
	parts: List[str] = []
	parts.extend(str(item or "").strip() for item in (artifact.get("source_reports") or []) if str(item or "").strip())
	parts.extend(
		str(value or "").strip()
		for value in (
			artifact.get("family_id"),
			(artifact.get("dimensions") or {}).get("entity_type") if isinstance(artifact.get("dimensions"), dict) else "",
			(artifact.get("dimensions") or {}).get("source_grain") if isinstance(artifact.get("dimensions"), dict) else "",
			turn.get("source_name"),
		)
		if str(value or "").strip()
	)
	dimensions = artifact.get("dimensions") if isinstance(artifact.get("dimensions"), dict) else {}
	metrics = artifact.get("metrics") if isinstance(artifact.get("metrics"), dict) else {}
	sections = artifact.get("sections") if isinstance(artifact.get("sections"), dict) else {}
	parts.extend(str(key or "").strip() for key in dimensions.keys() if str(key or "").strip())
	parts.extend(str(key or "").strip() for key in metrics.keys() if str(key or "").strip())
	parts.extend(str(key or "").strip() for key in sections.keys() if str(key or "").strip())
	for value in sections.values():
		if isinstance(value, list):
			for row in value[:3]:
				if isinstance(row, dict):
					parts.extend(str(key or "").strip() for key in row.keys() if str(key or "").strip())
	joined = " ".join(part for part in parts if part)
	return {
		str(value or "").strip()
		for value in ontology_detect_concepts(joined)
		if str(value or "").strip()
	}
