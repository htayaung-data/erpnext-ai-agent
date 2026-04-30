from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.metadata import (
	capability_dimensions_for_report,
	capability_metrics_for_report,
	get_report_family_spec,
	get_report_spec,
	report_approved_followup_modes,
	report_capability_ids,
	report_family_semantic_tags,
	report_local_followup_adapter,
	report_semantic_tags,
	report_sibling_capability_specs,
)
from ai_assistant_ui.qwen_chat.business_language_guards import looks_like_predictive_guarantee_claim
from ai_assistant_ui.qwen_chat.semantic_aliases import detect_canonical_keys
from ai_assistant_ui.qwen_chat.semantic_resolution_registry import semantic_slot_alias_matches
from ai_assistant_ui.qwen_chat.runtime_client import (
	QwenRuntimeClientError,
	call_qwen_runtime_followup_interpretation,
)

try:
	import frappe  # type: ignore
except Exception:  # pragma: no cover
	frappe = None


_ARTIFACT_LOCAL_FOLLOWUP_FAMILIES = {
	"ranking_analytics",
	"product_profitability",
	"trend_analytics",
	"financial_statement",
	"aging",
	"inventory_snapshot",
}
_ARTIFACT_LOCAL_PROJECTION_CUE_PATTERN = re.compile(
	r"\b(column|columns|only|just|show|give|display|keep)\b",
	re.IGNORECASE,
)
_TOP_N_PATTERN = re.compile(r"\btop\s+\d{1,3}\b", re.IGNORECASE)


@dataclass(frozen=True)
class SemanticFollowUpIntent:
	requested_modes: List[str]
	target_dimension: str = ""
	target_limit: int = 0
	sort_direction: str = ""
	target_metric: str = ""
	requested_columns: List[str] = field(default_factory=list)
	requested_time_scope: str = ""
	target_capability_id: str = ""
	self_contained: bool = False
	confidence: float = 0.0
	reason: str = ""
	source: str = "semantic"


@dataclass(frozen=True)
class SemanticFollowUpResult:
	status: str
	intent: SemanticFollowUpIntent | None = None
	confidence_threshold: float = 0.72
	fallback_policy: str = "no_heuristic_fallback"
	runtime_error: str = ""
	validation_error: str = ""
	agent_meta: Dict[str, Any] = field(default_factory=dict)

	def to_payload(self, *, fallback_used: bool = False, fallback_reason: str = "") -> Dict[str, Any]:
		intent_payload: Dict[str, Any] = {}
		if self.intent is not None:
			intent_payload = {
				"requested_modes": list(self.intent.requested_modes),
				"target_dimension": self.intent.target_dimension,
				"target_limit": self.intent.target_limit,
				"sort_direction": self.intent.sort_direction,
				"target_metric": self.intent.target_metric,
				"requested_columns": list(self.intent.requested_columns),
				"requested_time_scope": self.intent.requested_time_scope,
				"target_capability_id": self.intent.target_capability_id,
				"self_contained": self.intent.self_contained,
				"confidence": self.intent.confidence,
				"reason": self.intent.reason,
			}
		return {
			"type": "qwen_semantic_followup_interpretation",
			"contract_version": "1.0",
			"status": self.status,
			"confidence_threshold": self.confidence_threshold,
			"fallback_policy": self.fallback_policy,
			"fallback_used": bool(fallback_used),
			"fallback_reason": str(fallback_reason or "").strip(),
			"runtime_error": self.runtime_error,
			"validation_error": self.validation_error,
			"intent": intent_payload,
			"agent_meta": self.agent_meta if isinstance(self.agent_meta, dict) else {},
		}


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def _looks_like_predictive_guarantee_claim(message: str) -> bool:
	return looks_like_predictive_guarantee_claim(message)


def _normalize_direction(value: Any) -> str:
	clean = str(value or "").strip().lower()
	return clean if clean in {"asc", "desc"} else ""


def _confidence_threshold() -> float:
	default = 0.72
	if frappe is None:
		return default
	try:
		raw = (getattr(frappe, "conf", None) or {}).get("qwen_semantic_followup_min_confidence", default)
		return max(0.0, min(1.0, float(raw)))
	except Exception:
		return default


def _build_interpretation_context(
	*,
	latest_grounded_turn: Dict[str, Any],
	latest_assistant_payload: Dict[str, Any],
) -> Dict[str, Any]:
	source_name = str(latest_grounded_turn.get("source_name") or "").strip()
	source_family_id = str(latest_grounded_turn.get("artifact_family_id") or "").strip()
	source_report_names = [
		str(value or "").strip()
		for value in (latest_grounded_turn.get("artifact_source_reports") or [])
		if str(value or "").strip()
	]
	report_name = source_name if get_report_spec(source_name) else ""
	if not report_name and source_family_id and get_report_family_spec(source_family_id):
		for candidate in source_report_names:
			if get_report_spec(candidate):
				report_name = candidate
				break
	source_capability_ids = report_capability_ids(report_name)
	siblings: List[Dict[str, Any]] = []
	for item in report_sibling_capability_specs(report_name):
		capability_id = str(item.get("capability_id") or "").strip()
		if not capability_id:
			continue
		siblings.append(
			{
				"capability_id": capability_id,
				"label": str(item.get("label") or capability_id).strip(),
				"ontology_concepts": _clean_list(item.get("ontology_concepts")),
				"dimensions": _clean_list(item.get("dimensions")),
				"metrics": _clean_list(item.get("metrics")),
				"report_names": _clean_list(item.get("report_names")),
			}
		)

	adapter = report_local_followup_adapter(report_name, "dimension_breakdown")
	available_dimensions = capability_dimensions_for_report(report_name)
	approved_follow_up_modes = report_approved_followup_modes(report_name)
	display_dimension = str(adapter.get("display_dimension_label") or "").strip()
	if display_dimension and display_dimension not in available_dimensions:
		available_dimensions = [display_dimension] + available_dimensions

	return {
		"source_surface_name": source_name,
		"source_report_name": report_name or source_name,
		"source_family_id": source_family_id,
		"source_capability_ids": source_capability_ids,
		"source_semantic_tags": list(
			dict.fromkeys(
				[
					*report_semantic_tags(report_name),
					*report_family_semantic_tags(source_family_id),
				]
			)
		),
		"latest_grounded_source_reports": source_report_names,
		"approved_follow_up_modes": approved_follow_up_modes,
		"grounded_followup_supported": bool(approved_follow_up_modes),
		"available_dimensions": available_dimensions,
		"available_metrics": capability_metrics_for_report(report_name),
		"returned_schema": list(latest_grounded_turn.get("returned_schema") or []),
		"row_count": int(latest_grounded_turn.get("row_count") or 0),
		"latest_assistant_title": str(latest_assistant_payload.get("title") or "").strip(),
		"available_sibling_capabilities": siblings,
	}


def _normalize_message_text(value: Any) -> str:
	return " ".join(str(value or "").strip().lower().split())


def _word_boundary_pattern(value: str) -> str:
	return r"(^|[^a-z0-9])(" + re.escape(value) + r")([^a-z0-9]|$)"


def _slot_alias_present(slot_name: str, message: str) -> bool:
	return bool(semantic_slot_alias_matches(slot_name, message))


def _artifact_column_alias_targets(
	*,
	message: str,
	artifact_payload: Dict[str, Any],
) -> List[str]:
	dimensions = artifact_payload.get("dimensions") if isinstance(artifact_payload.get("dimensions"), dict) else {}
	column_alias_map = (
		dimensions.get("requested_column_alias_map")
		if isinstance(dimensions.get("requested_column_alias_map"), dict)
		else {}
	)
	normalized_message = _normalize_message_text(message)
	if not normalized_message or not column_alias_map:
		return []
	matches: List[tuple[int, str]] = []
	for alias, target in column_alias_map.items():
		alias_text = _normalize_message_text(alias)
		target_key = str(target or "").strip().lower().replace(" ", "_")
		if not alias_text or not target_key:
			continue
		for match in re.finditer(_word_boundary_pattern(alias_text), normalized_message):
			matches.append((match.start(2), target_key))
	matches.sort(key=lambda item: item[0])
	out: List[str] = []
	for _position, target in matches:
		if target not in out:
			out.append(target)
	return out


def interpret_artifact_local_projection_deterministically(
	*,
	message: str,
	latest_grounded_turn: Dict[str, Any],
	latest_family_artifact: Dict[str, Any],
) -> SemanticFollowUpResult:
	artifact_payload = latest_family_artifact if isinstance(latest_family_artifact, dict) else {}
	family_id = str(artifact_payload.get("family_id") or "").strip()
	if family_id not in _ARTIFACT_LOCAL_FOLLOWUP_FAMILIES:
		return SemanticFollowUpResult(status="not_applicable", confidence_threshold=_confidence_threshold())
	normalized_message = _normalize_message_text(message)
	if not normalized_message:
		return SemanticFollowUpResult(status="not_applicable", confidence_threshold=_confidence_threshold())
	if _TOP_N_PATTERN.search(normalized_message):
		return SemanticFollowUpResult(status="not_applicable", confidence_threshold=_confidence_threshold())
	if _slot_alias_present("time_scope", normalized_message) or _slot_alias_present("listing_view", normalized_message):
		return SemanticFollowUpResult(status="not_applicable", confidence_threshold=_confidence_threshold())
	requested_columns = _artifact_column_alias_targets(
		message=normalized_message,
		artifact_payload=artifact_payload,
	)
	projection_cue_present = bool(_ARTIFACT_LOCAL_PROJECTION_CUE_PATTERN.search(normalized_message))
	if not requested_columns:
		return SemanticFollowUpResult(status="not_applicable", confidence_threshold=_confidence_threshold())
	if len(requested_columns) < 2 and not projection_cue_present:
		return SemanticFollowUpResult(status="not_applicable", confidence_threshold=_confidence_threshold())
	if "entity" not in requested_columns and "entity_code" not in requested_columns:
		requested_columns.insert(0, "entity")
	metric_targets = [value for value in requested_columns if value not in {"entity", "entity_code"}]
	return SemanticFollowUpResult(
		status="accepted",
		confidence_threshold=_confidence_threshold(),
		intent=SemanticFollowUpIntent(
			requested_modes=["column_projection"],
			target_dimension="",
			target_limit=0,
			sort_direction="",
			target_metric=str(metric_targets[0] if metric_targets else "").strip(),
			requested_columns=requested_columns,
			requested_time_scope="",
			target_capability_id="",
			self_contained=False,
			confidence=0.81,
			reason=(
				"Artifact-local deterministic follow-up fallback matched requested projection columns from the "
				"grounded family artifact alias map."
			),
			source="artifact_local_projection_fallback",
		),
	)


def _validate_semantic_payload(
	*,
	payload: Dict[str, Any],
	context: Dict[str, Any],
	message: str = "",
) -> SemanticFollowUpIntent | None:
	if not isinstance(payload, dict):
		return None
	allowed_modes = {
		str(x or "").strip()
		for x in (context.get("approved_follow_up_modes") or [])
		if str(x or "").strip()
	}
	requested_modes = [
		mode
		for mode in _clean_list(payload.get("requested_modes"))
		if mode in allowed_modes and mode != "new_query"
	]
	available_dimensions = {
		str(x or "").strip().lower(): str(x or "").strip()
		for x in (context.get("available_dimensions") or [])
		if str(x or "").strip()
	}
	target_dimension_raw = str(payload.get("target_dimension") or "").strip()
	target_dimension = available_dimensions.get(target_dimension_raw.lower(), "")
	target_limit = max(0, min(50, int(payload.get("target_limit") or 0)))
	sort_direction = _normalize_direction(payload.get("sort_direction"))
	target_metric = str(payload.get("target_metric") or "").strip().lower()
	requested_columns = [
		str(value or "").strip().lower()
		for value in _clean_list(payload.get("requested_columns"))
		if str(value or "").strip()
	]
	requested_time_scope = str(payload.get("requested_time_scope") or "").strip()
	sibling_capabilities = {
		str(item.get("capability_id") or "").strip()
		for item in (context.get("available_sibling_capabilities") or [])
		if isinstance(item, dict) and str(item.get("capability_id") or "").strip()
	}
	target_capability_id = str(payload.get("target_capability_id") or "").strip()
	if target_capability_id not in sibling_capabilities:
		target_capability_id = ""

	if "dimension_breakdown" in requested_modes and not target_dimension:
		requested_modes = [mode for mode in requested_modes if mode != "dimension_breakdown"]
	if "sort_or_limit" in requested_modes and not (target_limit or sort_direction):
		requested_modes = [mode for mode in requested_modes if mode != "sort_or_limit"]
	if not set(requested_modes).intersection({"column_projection", "column_refinement"}):
		requested_columns = []
	if "time_scope_restatement" not in requested_modes:
		requested_time_scope = ""
	if target_capability_id and "sibling_switch" not in requested_modes and "sibling_switch" in allowed_modes:
		requested_modes.append("sibling_switch")
	if _looks_like_predictive_guarantee_claim(message):
		return None

	try:
		confidence = float(payload.get("confidence") or 0.0)
	except Exception:
		confidence = 0.0
	confidence = max(0.0, min(1.0, confidence))
	self_contained = bool(payload.get("self_contained"))
	reason = str(payload.get("reason") or "").strip()
	if "column_projection" in requested_modes and not requested_columns and not target_metric:
		reason_metric_keys = detect_canonical_keys(reason, dimension_or_metric="metric")
		if reason_metric_keys:
			target_metric = str(reason_metric_keys[0] or "").strip().lower()
			if target_metric:
				requested_columns = [target_metric]

	if not requested_modes and not target_capability_id and not self_contained:
		return None

	return SemanticFollowUpIntent(
		requested_modes=list(dict.fromkeys(requested_modes)),
		target_dimension=target_dimension,
		target_limit=target_limit,
		sort_direction=sort_direction,
		target_metric=target_metric,
		requested_columns=requested_columns,
		requested_time_scope=requested_time_scope,
		target_capability_id=target_capability_id,
		self_contained=self_contained,
		confidence=confidence,
		reason=reason,
	)


def interpret_followup_semantically(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	recent_messages: List[Dict[str, str]],
	latest_grounded_turn: Dict[str, Any],
	latest_assistant_payload: Dict[str, Any],
) -> SemanticFollowUpResult:
	report_name = str(latest_grounded_turn.get("source_name") or "").strip()
	threshold = _confidence_threshold()
	if not report_name:
		return SemanticFollowUpResult(
			status="not_applicable",
			confidence_threshold=threshold,
		)

	context = _build_interpretation_context(
		latest_grounded_turn=latest_grounded_turn,
		latest_assistant_payload=latest_assistant_payload,
	)
	try:
		data = call_qwen_runtime_followup_interpretation(
			request_id=request_id,
			session_id=session_id,
			user_id=user_id,
			site_name=site_name,
			message=message,
			recent_messages=recent_messages,
			latest_grounded_turn=latest_grounded_turn,
			latest_assistant_payload=latest_assistant_payload,
			interpretation_context=context,
		)
	except QwenRuntimeClientError as exc:
		return SemanticFollowUpResult(
			status="runtime_error",
			confidence_threshold=threshold,
			runtime_error=str(exc),
		)

	agent_meta = data.get("agent_meta") if isinstance(data.get("agent_meta"), dict) else {}
	interpretation = data.get("interpretation")
	if not isinstance(interpretation, dict):
		return SemanticFollowUpResult(
			status="invalid_response",
			confidence_threshold=threshold,
			validation_error="Runtime follow-up interpreter returned no valid interpretation object.",
			agent_meta=agent_meta,
		)
	intent = _validate_semantic_payload(payload=interpretation, context=context, message=message)
	if intent is None:
		return SemanticFollowUpResult(
			status="invalid_response",
			confidence_threshold=threshold,
			validation_error="Runtime follow-up interpretation did not pass governed validation.",
			agent_meta=agent_meta,
		)
	if intent.confidence < threshold:
		return SemanticFollowUpResult(
			status="low_confidence",
			intent=intent,
			confidence_threshold=threshold,
			validation_error="Semantic follow-up interpretation fell below the governed confidence threshold.",
			agent_meta=agent_meta,
		)
	return SemanticFollowUpResult(
		status="accepted",
		intent=intent,
		confidence_threshold=threshold,
		agent_meta=agent_meta,
	)
