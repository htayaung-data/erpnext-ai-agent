from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Set

from ai_assistant_ui.qwen_chat.metadata import (
	capability_dimensions_for_report,
	get_report_spec,
	ontology_detect_concepts,
	ontology_detect_followup_modes,
	ontology_followup_aliases,
	ontology_followup_slot_aliases,
	ontology_self_contained_prefixes,
	report_family_intent_markers,
	report_family_report_names,
	report_local_followup_adapter,
	report_family_ontology_concepts,
	supported_ontology_concepts,
)
from ai_assistant_ui.qwen_chat.semantic_aliases import detect_canonical_keys
from ai_assistant_ui.qwen_chat.semantic_aliases import get_aliases


def _normalize_text(text: str) -> str:
	return " ".join(str(text or "").strip().lower().split())


def _normalize_key(value: Any) -> str:
	return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def _tokenize(text: str) -> List[str]:
	return [token for token in re.findall(r"[a-z0-9]+", _normalize_text(text)) if token]


def _token_set(text: str) -> Set[str]:
	return set(_tokenize(text))


def _contains_alias(text: str, alias: str) -> bool:
	value = _normalize_text(text)
	target = _normalize_text(alias)
	if not value or not target:
		return False
	pattern = r"(^|[^a-z0-9])" + re.escape(target) + r"([^a-z0-9]|$)"
	return bool(re.search(pattern, value))


def _starts_with_self_contained_prefix(text: str, language: str) -> bool:
	value = _normalize_text(text)
	for prefix in ontology_self_contained_prefixes(language):
		clean = _normalize_text(prefix)
		if clean and (value == clean or value.startswith(f"{clean} ")):
			return True
	return False


@dataclass(frozen=True)
class FollowUpIntent:
	requested_modes: List[str]
	matched_aliases: Dict[str, List[str]]
	target_dimension: str = ""
	target_limit: int = 0
	sort_direction: str = ""
	target_metric: str = ""
	requested_columns: List[str] = field(default_factory=list)
	requested_time_scope: str = ""


@dataclass(frozen=True)
class ArtifactContextSignal:
	has_grounded_turn: bool
	report_name: str
	family_id: str
	context_concepts: Set[str]
	available_dimensions: Dict[str, str]
	available_metrics: Dict[str, str]
	available_metric_keys: Set[str]


@dataclass(frozen=True)
class MessageSignal:
	text: str
	tokens: Set[str]
	concepts: Set[str]
	followup_modes: Set[str]
	dimension_keys: List[str]
	metric_keys: List[str]
	target_dimension: str
	target_limit: int
	sort_direction: str
	requested_time_scope: str
	requested_columns: List[str]
	presentation_modes: List[str]


def _normalized_dimension_candidates(grounded_turn: Dict[str, object] | None) -> Dict[str, str]:
	turn = grounded_turn if isinstance(grounded_turn, dict) else {}
	report_name = str(turn.get("source_name") or "").strip()
	candidates: Dict[str, str] = {}

	adapter = report_local_followup_adapter(report_name, "dimension_breakdown")
	display_dimension = str(adapter.get("display_dimension_label") or "").strip()
	if display_dimension:
		candidates[_normalize_text(display_dimension)] = display_dimension

	for value in capability_dimensions_for_report(report_name):
		clean = str(value or "").strip()
		if clean:
			candidates.setdefault(_normalize_text(clean), clean)

	for value in turn.get("dimensions") or []:
		clean = str(value or "").strip()
		if clean:
			candidates.setdefault(_normalize_text(clean), clean)

	returned_schema = turn.get("returned_schema")
	if isinstance(returned_schema, list):
		for value in returned_schema[:2]:
			clean = str(value or "").strip()
			if clean:
				candidates.setdefault(_normalize_text(clean), clean)

	return candidates


def _normalized_metric_candidates(grounded_turn: Dict[str, object] | None) -> Dict[str, str]:
	turn = grounded_turn if isinstance(grounded_turn, dict) else {}
	candidates: Dict[str, str] = {}
	for value in turn.get("metrics") or []:
		clean = str(value or "").strip()
		if clean:
			candidates.setdefault(_normalize_text(clean), clean)
	return candidates


def _report_domain_concepts(report_name: str) -> Set[str]:
	spec = get_report_spec(report_name)
	values = spec.get("semantic_tags")
	if not isinstance(values, list):
		return set()
	return {
		str(value or "").strip()
		for value in values
		if str(value or "").strip() in {"payable", "receivable", "sales", "product", "inventory", "supplier", "customer"}
	}


def _artifact_context_signal(grounded_turn: Dict[str, object] | None) -> ArtifactContextSignal:
	turn = grounded_turn if isinstance(grounded_turn, dict) else {}
	report_name = str(turn.get("source_name") or "").strip()
	family_id = str(turn.get("artifact_family_id") or "").strip()
	value = " ".join(
		part
		for part in [
			report_name,
			" ".join(str(item or "").strip() for item in (turn.get("dimensions") or []) if str(item or "").strip()),
			" ".join(str(item or "").strip() for item in (turn.get("metrics") or []) if str(item or "").strip()),
		]
		if part
	)
	context_concepts = set(ontology_detect_concepts(value))
	explicit_report_concepts = _report_domain_concepts(report_name)
	if explicit_report_concepts:
		context_concepts.update(explicit_report_concepts)
	for dimension_label in _normalized_dimension_candidates(turn).values():
		context_concepts.update(ontology_detect_concepts(str(dimension_label or "").strip()))
	if not context_concepts:
		context_concepts = set(report_family_ontology_concepts(family_id))
	available_metrics = _normalized_metric_candidates(turn)
	available_metric_keys: Set[str] = set()
	for label in available_metrics.values():
		available_metric_keys.update(detect_canonical_keys(label, dimension_or_metric="metric"))
	return ArtifactContextSignal(
		has_grounded_turn=bool(turn.get("grounded")),
		report_name=report_name,
		family_id=family_id,
		context_concepts=context_concepts,
		available_dimensions=_normalized_dimension_candidates(turn),
		available_metrics=available_metrics,
		available_metric_keys=available_metric_keys,
	)


def _detect_target_dimension(
	text: str,
	artifact_signal: ArtifactContextSignal,
	dimension_keys: List[str],
	followup_modes: Set[str],
) -> str:
	if not artifact_signal.has_grounded_turn:
		return ""
	if not dimension_keys:
		return ""
	if "dimension_breakdown" not in followup_modes:
		return ""
	for key in dimension_keys:
		label = artifact_signal.available_dimensions.get(_normalize_text(key))
		if label:
			return label
	return ""


def _detect_sort_limit_spec(tokens: Set[str], text: str, followup_modes: Set[str]) -> tuple[int, str]:
	limit = 0
	direction = ""
	if "sort_or_limit" not in followup_modes:
		return 0, ""
	limit_prefixes = ontology_followup_slot_aliases("sort_or_limit", "limit_prefix")
	for match in re.finditer(r"\b([a-z]+)\s+(\d+)\b", text):
		label = str(match.group(1) or "").strip().lower()
		value = int(match.group(2))
		for candidate_direction, aliases in limit_prefixes.items():
			if label in {str(alias or "").strip().lower() for alias in aliases}:
				limit = value
				direction = "desc" if candidate_direction == "desc" else "asc"
				break
	sort_direction_aliases = ontology_followup_slot_aliases("sort_or_limit", "sort_direction")
	token_values = {str(token or "").strip().lower() for token in tokens}
	for candidate_direction, aliases in sort_direction_aliases.items():
		if token_values & {str(alias or "").strip().lower() for alias in aliases}:
			direction = "desc" if candidate_direction == "desc" else "asc"
	return max(0, int(limit)), direction


def _detect_requested_time_scope(text: str, followup_modes: Set[str]) -> str:
	if "time_scope_restatement" not in followup_modes:
		return ""
	normalized_text = _normalize_text(text)
	for scope, aliases in ontology_followup_slot_aliases("time_scope_restatement", "requested_time_scope").items():
		for alias in aliases:
			clean = _normalize_text(alias)
			if clean and (clean == normalized_text or clean in normalized_text):
				return scope
	return ""


def _detect_presentation_modes(followup_modes: Set[str]) -> List[str]:
	return [
		mode
		for mode in ("presentation_transform", "table_presentation", "bullet_presentation")
		if mode in followup_modes
	]


def _family_intent_marker_match(text: str, markers: List[str]) -> bool:
	for marker in markers:
		if _contains_alias(text, marker):
			return True
	return False


def _looks_like_ambiguous_family_report_request(
	*,
	signal: MessageSignal,
	artifact_signal: ArtifactContextSignal,
	parsed: FollowUpIntent,
) -> bool:
	if not artifact_signal.has_grounded_turn:
		return False
	family_id = str(artifact_signal.family_id or "").strip()
	if not family_id:
		return False
	family_reports = report_family_report_names(family_id)
	if len(family_reports) <= 1:
		return False
	if set(parsed.requested_modes):
		return False
	intent_markers = report_family_intent_markers(family_id)
	if not _family_intent_marker_match(signal.text, intent_markers):
		return False
	family_concepts = set(report_family_ontology_concepts(family_id))
	if signal.concepts & family_concepts:
		return False
	return True


def detect_ambiguous_family_report_request(
	message: str,
	*,
	language: str = "en",
	grounded_turn: Dict[str, object] | None = None,
) -> Dict[str, Any]:
	artifact_signal = _artifact_context_signal(grounded_turn)
	if not artifact_signal.has_grounded_turn:
		return {}
	signal = _message_signal(message, language=language, grounded_turn=grounded_turn)
	parsed = detect_followup_intent(message, language=language, grounded_turn=grounded_turn)
	if not _looks_like_ambiguous_family_report_request(
		signal=signal,
		artifact_signal=artifact_signal,
		parsed=parsed,
	):
		return {}
	family_id = str(artifact_signal.family_id or "").strip()
	return {
		"family_id": family_id,
		"report_candidates": report_family_report_names(family_id),
		"reason": "The follow-up refers broadly to a governed multi-report family and does not identify a unique report view.",
	}


def _looks_like_column_projection(tokens: Set[str], followup_modes: Set[str]) -> bool:
	if not tokens:
		return False
	return "column_projection" in followup_modes


def _map_requested_columns(
	artifact_signal: ArtifactContextSignal,
	dimension_keys: List[str],
	metric_keys: List[str],
	projection_like: bool,
	target_dimension: str,
) -> List[str]:
	if not artifact_signal.has_grounded_turn or not projection_like:
		return []
	if target_dimension:
		return []
	columns: List[str] = []
	dimension_key_set = set(dimension_keys)
	if {"item_name", "customer", "supplier"} & dimension_key_set:
		columns.append("entity")
	elif "item_code" in dimension_key_set:
		columns.append("entity")
	if "item_code" in dimension_key_set and "item_name" not in dimension_key_set:
		columns.append("entity_code")
	if "territory" in dimension_key_set:
		columns.append("territory")
	compatible_metrics = metric_keys
	if artifact_signal.available_metric_keys:
		compatible_metrics = [metric for metric in metric_keys if metric in artifact_signal.available_metric_keys]
		if not compatible_metrics:
			compatible_metrics = metric_keys
	for metric in compatible_metrics:
		if metric:
			columns.append(metric)
	return list(dict.fromkeys([value for value in columns if value]))


def _metric_alias_score(metric_key: str, text: str) -> int:
	best = 0
	for alias in get_aliases(metric_key):
		normalized_alias = _normalize_text(alias)
		if normalized_alias and normalized_alias in text:
			best = max(best, len(normalized_alias))
	if metric_key.replace("_", " ") in text:
		best = max(best, len(metric_key))
	return best


def _select_target_metric(artifact_signal: ArtifactContextSignal, metric_keys: List[str], text: str) -> str:
	if not metric_keys:
		return ""
	compatible_metrics = list(metric_keys)
	if artifact_signal.available_metric_keys:
		compatible_metrics = [metric for metric in metric_keys if metric in artifact_signal.available_metric_keys] or list(metric_keys)
	best_metric = ""
	best_score = -1
	for metric in compatible_metrics:
		score = _metric_alias_score(metric, text)
		if score > best_score:
			best_metric = metric
			best_score = score
	if best_metric:
		return best_metric
	return str(compatible_metrics[0] or "").strip()


def _message_signal(
	message: str,
	*,
	language: str = "en",
	grounded_turn: Dict[str, object] | None = None,
) -> MessageSignal:
	text = _normalize_text(message)
	tokens = _token_set(text)
	followup_modes = set(ontology_detect_followup_modes(text, language=language))
	dimension_keys = detect_canonical_keys(text, dimension_or_metric="dimension")
	metric_keys = detect_canonical_keys(text, dimension_or_metric="metric")
	artifact_signal = _artifact_context_signal(grounded_turn)
	target_dimension = _detect_target_dimension(text, artifact_signal, dimension_keys, followup_modes)
	target_limit, sort_direction = _detect_sort_limit_spec(tokens, text, followup_modes)
	requested_time_scope = _detect_requested_time_scope(text, followup_modes)
	presentation_modes = _detect_presentation_modes(followup_modes)
	requested_columns = _map_requested_columns(
		artifact_signal,
		dimension_keys,
		metric_keys,
		projection_like=_looks_like_column_projection(tokens, followup_modes),
		target_dimension=target_dimension,
	)
	return MessageSignal(
		text=text,
		tokens=tokens,
		concepts=set(ontology_detect_concepts(text, language=language)),
		followup_modes=followup_modes,
		dimension_keys=dimension_keys,
		metric_keys=metric_keys,
		target_dimension=target_dimension,
		target_limit=target_limit,
		sort_direction=sort_direction,
		requested_time_scope=requested_time_scope,
		requested_columns=requested_columns,
		presentation_modes=presentation_modes,
	)


def detect_followup_intent(message: str, language: str = "en", grounded_turn: Dict[str, object] | None = None) -> FollowUpIntent:
	text = _normalize_text(message)
	if not text:
		return FollowUpIntent(requested_modes=[], matched_aliases={})

	artifact_signal = _artifact_context_signal(grounded_turn)
	signal = _message_signal(text, language=language, grounded_turn=grounded_turn)
	requested_modes: List[str] = []
	matched_aliases: Dict[str, List[str]] = {}

	for mode in signal.presentation_modes:
		if mode not in requested_modes:
			requested_modes.append(mode)
		matched_aliases.setdefault(mode, []).append(mode)

	if signal.target_dimension:
		requested_modes.append("dimension_breakdown")
		matched_aliases.setdefault("dimension_breakdown", []).append(signal.target_dimension)

	if signal.target_limit or signal.sort_direction:
		requested_modes.append("sort_or_limit")
		sort_matches: List[str] = []
		if signal.target_limit:
			sort_matches.append(f"limit:{signal.target_limit}")
		if signal.sort_direction:
			sort_matches.append(signal.sort_direction)
		matched_aliases.setdefault("sort_or_limit", []).extend(sort_matches or ["sort"])

	target_metric = _select_target_metric(artifact_signal, signal.metric_keys, signal.text)
	requested_columns = list(signal.requested_columns)
	if target_metric and requested_columns:
		requested_columns = [
			column
			for column in requested_columns
			if column not in artifact_signal.available_metric_keys or column == target_metric
		]
	if artifact_signal.has_grounded_turn and target_metric:
		requested_modes.append("metric_refinement")
		matched_aliases.setdefault("metric_refinement", []).append(target_metric)

	if requested_columns:
		requested_modes.append("column_refinement")
		matched_aliases.setdefault("column_refinement", []).extend(requested_columns)

	if signal.requested_time_scope:
		requested_modes.append("time_scope_restatement")
		matched_aliases.setdefault("time_scope_restatement", []).append(signal.requested_time_scope)

	return FollowUpIntent(
		requested_modes=list(dict.fromkeys(requested_modes)),
		matched_aliases=matched_aliases,
		target_dimension=signal.target_dimension,
		target_limit=signal.target_limit,
		sort_direction=signal.sort_direction,
		target_metric=target_metric,
		requested_columns=requested_columns,
		requested_time_scope=signal.requested_time_scope,
	)


def is_million_transform_intent(message: str, intent: FollowUpIntent | None = None) -> bool:
	parsed = intent or detect_followup_intent(message)
	return "presentation_transform" in parsed.requested_modes


def is_self_contained_business_request(
	message: str,
	language: str = "en",
	intent: FollowUpIntent | None = None,
	grounded_turn: Dict[str, object] | None = None,
) -> bool:
	artifact_signal = _artifact_context_signal(grounded_turn)
	signal = _message_signal(message, language=language, grounded_turn=grounded_turn)
	parsed = intent or detect_followup_intent(signal.text, language=language, grounded_turn=grounded_turn)
	alias_hits = set(signal.dimension_keys) | set(signal.metric_keys)
	family_marker_hit = _family_intent_marker_match(
		signal.text,
		report_family_intent_markers(str(artifact_signal.family_id or "").strip()),
	)
	business_signals = bool(signal.concepts or alias_hits or family_marker_hit)
	if not business_signals:
		return False

	local_only_modes = {
		"presentation_transform",
		"table_presentation",
		"bullet_presentation",
		"sort_or_limit",
		"metric_refinement",
		"column_refinement",
		"time_scope_restatement",
	}
	if not artifact_signal.has_grounded_turn:
		return True

	if _looks_like_ambiguous_family_report_request(
		signal=signal,
		artifact_signal=artifact_signal,
		parsed=parsed,
	):
		return True

	if set(parsed.requested_modes).issubset(local_only_modes):
		if parsed.requested_modes == ["presentation_transform"]:
			return False
		if parsed.requested_modes == ["table_presentation"]:
			return False
		if parsed.requested_modes == ["bullet_presentation"]:
			return False
		if parsed.requested_modes and not signal.requested_time_scope and not signal.target_dimension and not signal.target_limit:
			return False

	if signal.concepts and artifact_signal.context_concepts and signal.concepts.isdisjoint(artifact_signal.context_concepts):
		return True

	if signal.requested_time_scope:
		return True
	if signal.target_dimension and signal.target_dimension not in artifact_signal.available_dimensions.values():
		return True
	if parsed.target_metric and parsed.target_metric not in artifact_signal.available_metric_keys:
		return True
	if _starts_with_self_contained_prefix(signal.text, language) and business_signals:
		return True
	return False


def is_safe_local_compatibility_intent(
	message: str,
	language: str = "en",
	grounded_turn: Dict[str, object] | None = None,
) -> bool:
	artifact_signal = _artifact_context_signal(grounded_turn)
	if not artifact_signal.has_grounded_turn:
		return False
	parsed = detect_followup_intent(message, language=language, grounded_turn=grounded_turn)
	modes = set(parsed.requested_modes)
	if not modes:
		return False
	if not modes.issubset({"presentation_transform", "table_presentation", "bullet_presentation", "sort_or_limit", "metric_refinement", "column_refinement"}):
		return False
	if "sort_or_limit" in modes and not (parsed.target_limit or parsed.sort_direction):
		return False
	if "column_refinement" in modes and not list(parsed.requested_columns or []):
		return False
	if "time_scope_restatement" in modes:
		return False
	return True


def assess_context_isolation(
	message: str,
	*,
	language: str = "en",
	grounded_turn: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	artifact_signal = _artifact_context_signal(grounded_turn)
	signal = _message_signal(message, language=language, grounded_turn=grounded_turn)
	intent = detect_followup_intent(signal.text, language=language, grounded_turn=grounded_turn)
	requested_modes = {str(mode or "").strip() for mode in (intent.requested_modes or []) if str(mode or "").strip()}
	local_only_modes = {
		"presentation_transform",
		"table_presentation",
		"bullet_presentation",
		"sort_or_limit",
		"metric_refinement",
		"column_refinement",
		"time_scope_restatement",
	}
	message_concepts = set(signal.concepts)
	alias_hits = set(signal.dimension_keys) | set(signal.metric_keys)
	supported_concepts = set(supported_ontology_concepts())
	out_of_scope_concepts = sorted(concept for concept in message_concepts if concept not in supported_concepts)
	if out_of_scope_concepts and not (message_concepts & supported_concepts or alias_hits):
		primary_domain = "hr" if "employee" in out_of_scope_concepts else ""
		return {
			"force_new_query": True,
			"out_of_scope": True,
			"reason": "The request targets a business domain outside the current governed Qwen ERP scope.",
			"requested_domains": sorted(message_concepts),
			"context_domains": sorted(artifact_signal.context_concepts),
			"primary_domain": primary_domain,
		}

	self_contained = is_self_contained_business_request(
		message,
		language=language,
		intent=intent,
		grounded_turn=grounded_turn,
	)
	if (
		message_concepts
		and artifact_signal.context_concepts
		and message_concepts.isdisjoint(artifact_signal.context_concepts)
		and "dimension_breakdown" not in requested_modes
	):
		return {
			"force_new_query": True,
			"out_of_scope": False,
			"reason": "The request shifts to a different governed business area and should not inherit the prior artifact.",
			"requested_domains": sorted(message_concepts),
			"context_domains": sorted(artifact_signal.context_concepts),
		}
	if requested_modes and requested_modes.issubset(local_only_modes) and not self_contained:
		return {
			"force_new_query": False,
			"out_of_scope": False,
			"reason": "",
			"requested_domains": sorted(message_concepts),
			"context_domains": sorted(artifact_signal.context_concepts),
		}
	if self_contained:
		return {
			"force_new_query": True,
			"out_of_scope": False,
			"reason": "The request is self-contained and should be treated as a fresh governed ERP question.",
			"requested_domains": sorted(message_concepts),
			"context_domains": sorted(artifact_signal.context_concepts),
		}

	return {
		"force_new_query": False,
		"out_of_scope": False,
		"reason": "",
		"requested_domains": sorted(message_concepts),
		"context_domains": sorted(artifact_signal.context_concepts),
	}
