from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Tuple


@dataclass(frozen=True)
class ConversationSnapshotDependencies:
    session_tool_payloads: Callable[..., List[Dict[str, Any]]]
    get_clarification_state: Callable[..., Any]
    latest_pending_clarification_signal: Callable[..., Dict[str, Any]]
    clarification_continuation_lane: Callable[..., str]
    build_pending_clarification_snapshot_state: Callable[..., Dict[str, Any]]
    latest_tool_payload_position: Callable[..., int]
    latest_grounded_turn_contract: Callable[..., Dict[str, Any]]
    build_latest_grounded_turn_snapshot_state: Callable[..., Dict[str, Any]]
    latest_normalized_family_artifact: Callable[..., Dict[str, Any]]
    artifact_compatible_with_grounded_turn: Callable[..., bool]
    build_latest_artifact_snapshot_state: Callable[..., Dict[str, Any]]
    latest_recovery_contract: Callable[..., Dict[str, Any]]
    build_latest_recovery_contract_snapshot_state: Callable[..., Dict[str, Any]]
    latest_repair_intent_contract: Callable[..., Dict[str, Any]]
    build_latest_repair_intent_snapshot_state: Callable[..., Dict[str, Any]]
    latest_tool_payload_by_type: Callable[..., Dict[str, Any]]
    compound_request_assessment_is_active: Callable[..., bool]
    build_active_sequence_snapshot_state: Callable[..., Dict[str, Any]]
    grounded_recent_focus_surface_descriptor: Callable[..., Dict[str, Any]]
    single_row_transaction_document_recent_focus: Callable[..., Dict[str, Any]]
    single_row_master_data_entity_recent_focus: Callable[..., Dict[str, Any]]
    build_grounded_recent_focus_state_from_surface_descriptor: Callable[..., Dict[str, Any]]
    empty_recent_focus_state: Callable[..., Dict[str, Any]]
    build_historical_recent_focus_snapshot_inputs: Callable[..., Dict[str, Dict[str, Any]]]
    empty_resumable_prior_request_state: Callable[..., Dict[str, Any]]
    build_recent_focus_affordance_contract_from_snapshot: Callable[..., Any]
    build_snapshot_state_quality: Callable[..., Dict[str, Any]]
    build_snapshot_internal_details: Callable[..., Dict[str, Any]]


def _snapshot_clean_text(value: Any) -> str:
    return str(value or "").strip()


def _snapshot_source_tool_index(state_payload: Dict[str, Any]) -> int:
    if not isinstance(state_payload, dict):
        return -1
    try:
        return int(state_payload.get("source_tool_index", -1) or -1)
    except (TypeError, ValueError):
        return -1


def _snapshot_max_source_tool_index(*state_payloads: Dict[str, Any]) -> int:
    indexes = [
        _snapshot_source_tool_index(payload)
        for payload in state_payloads
        if isinstance(payload, dict)
    ]
    valid_indexes = [index for index in indexes if index >= 0]
    return max(valid_indexes) if valid_indexes else -1


def _snapshot_grounded_request_id(state_payload: Dict[str, Any]) -> str:
    if not isinstance(state_payload, dict):
        return ""
    payload = dict(state_payload.get("payload") or {}) if isinstance(state_payload.get("payload"), dict) else {}
    return _snapshot_clean_text(
        state_payload.get("trace_request_id")
        or state_payload.get("request_id")
        or payload.get("trace_request_id")
        or payload.get("request_id")
    )


def _snapshot_recovery_matches_grounded_turn(
    recovery_state: Dict[str, Any],
    grounded_state: Dict[str, Any],
) -> bool:
    recovery_source_request_id = _snapshot_clean_text((recovery_state or {}).get("source_request_id"))
    grounded_request_id = _snapshot_grounded_request_id(grounded_state)
    if not recovery_source_request_id or not grounded_request_id:
        return False
    return recovery_source_request_id == grounded_request_id


def _snapshot_state_is_newer(candidate_state: Dict[str, Any], baseline_state: Dict[str, Any]) -> bool:
    candidate_index = _snapshot_source_tool_index(candidate_state)
    baseline_index = _snapshot_source_tool_index(baseline_state)
    if candidate_index < 0 or baseline_index < 0:
        return False
    return candidate_index > baseline_index


def _snapshot_peer_precedence_basis(candidate_state: Dict[str, Any], baseline_state: Dict[str, Any]) -> str:
    candidate_index = _snapshot_source_tool_index(candidate_state)
    baseline_index = _snapshot_source_tool_index(baseline_state)
    if candidate_index >= 0 and baseline_index < 0:
        return "known_over_unindexed"
    if _snapshot_state_is_newer(candidate_state, baseline_state):
        return "newer"
    return ""


def _snapshot_pending_clarification_state(*, session_doc, deps: ConversationSnapshotDependencies) -> Dict[str, Any]:
    tool_payloads = deps.session_tool_payloads(session_doc)
    state = deps.get_clarification_state(session_doc)
    if getattr(state, "has_pending", False):
        signal = dict(getattr(state, "pending_signal", {}) or {})
        signal_request_id = _snapshot_clean_text(signal.get("request_id"))
        return deps.build_pending_clarification_snapshot_state(
            signal=signal,
            source_kind="stored_state",
            attempt_count=int(max(0, getattr(state, "attempt_count", 0) or 0)),
            max_attempts=int(max(0, getattr(state, "max_attempts", 0) or 0)),
            continuation_lane=deps.clarification_continuation_lane(signal),
            status="pending" if signal else "none",
            source_tool_index=deps.latest_tool_payload_position(
                tool_payloads,
                payload_type="qwen_clarification_signal_contract",
                request_id=signal_request_id,
            ),
        )
    signal = deps.latest_pending_clarification_signal(session_doc)
    signal_request_id = _snapshot_clean_text((signal or {}).get("request_id"))
    return deps.build_pending_clarification_snapshot_state(
        signal=dict(signal or {}),
        source_kind="message_fallback" if signal else "none",
        attempt_count=0,
        max_attempts=0,
        continuation_lane=deps.clarification_continuation_lane(signal) if signal else "",
        status="pending" if signal else "none",
        source_tool_index=deps.latest_tool_payload_position(
            tool_payloads,
            payload_type="qwen_clarification_signal_contract",
            request_id=signal_request_id,
        ),
    )


def _snapshot_latest_grounded_turn_state(*, session_doc, deps: ConversationSnapshotDependencies) -> Dict[str, Any]:
    payload = deps.latest_grounded_turn_contract(session_doc)
    tool_payloads = deps.session_tool_payloads(session_doc)
    request_id = _snapshot_clean_text((payload or {}).get("request_id"))
    return deps.build_latest_grounded_turn_snapshot_state(
        payload=dict(payload or {}),
        source_tool_index=deps.latest_tool_payload_position(
            tool_payloads,
            payload_type="qwen_grounded_turn_context",
            request_id=request_id,
        ),
    )


def _snapshot_latest_artifact_state(
    session_doc,
    *,
    deps: ConversationSnapshotDependencies,
    grounded_turn_payload: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    payload = deps.latest_normalized_family_artifact(
        session_doc,
        grounded_turn=grounded_turn_payload if isinstance(grounded_turn_payload, dict) else {},
    )
    available = bool(isinstance(payload, dict) and payload)
    grounded_compatible = bool(
        available
        and isinstance(grounded_turn_payload, dict)
        and grounded_turn_payload
        and deps.artifact_compatible_with_grounded_turn(
            artifact_payload=dict(payload or {}),
            grounded_turn=dict(grounded_turn_payload or {}),
        )
    )
    tool_payloads = deps.session_tool_payloads(session_doc)
    artifact_request_id = _snapshot_clean_text((payload or {}).get("request_id"))
    artifact_source_tool_index = -1
    for artifact_payload_type in (
        "qwen_normalized_family_artifact_contract",
        "qwen_composite_family_artifact",
        "qwen_entity_detail_artifact",
    ):
        artifact_source_tool_index = max(
            artifact_source_tool_index,
            deps.latest_tool_payload_position(
                tool_payloads,
                payload_type=artifact_payload_type,
                request_id=artifact_request_id,
            ),
        )
    return deps.build_latest_artifact_snapshot_state(
        payload=dict(payload or {}),
        grounded_compatible=grounded_compatible,
        source_tool_index=artifact_source_tool_index,
    )


def _snapshot_latest_recovery_contract_state(*, session_doc, deps: ConversationSnapshotDependencies) -> Dict[str, Any]:
    payload = deps.latest_recovery_contract(session_doc)
    tool_payloads = deps.session_tool_payloads(session_doc)
    return deps.build_latest_recovery_contract_snapshot_state(
        payload=dict(payload or {}),
        source_tool_index=deps.latest_tool_payload_position(
            tool_payloads,
            payload_type="qwen_artifact_enrichment_recovery_contract",
            request_id=_snapshot_clean_text((payload or {}).get("request_id")),
        ),
    )


def _snapshot_latest_repair_intent_state(*, session_doc, deps: ConversationSnapshotDependencies) -> Dict[str, Any]:
    payload = deps.latest_repair_intent_contract(session_doc)
    tool_payloads = deps.session_tool_payloads(session_doc)
    return deps.build_latest_repair_intent_snapshot_state(
        payload=dict(payload or {}),
        source_tool_index=deps.latest_tool_payload_position(
            tool_payloads,
            payload_type="qwen_conversational_repair_intent_contract",
            request_id=_snapshot_clean_text((payload or {}).get("request_id")),
        ),
    )


def _snapshot_active_sequence_state(*, session_doc, deps: ConversationSnapshotDependencies) -> Dict[str, Any]:
    payload = deps.latest_tool_payload_by_type(
        deps.session_tool_payloads(session_doc),
        "qwen_compound_request_assessment_contract",
    )
    tool_payloads = deps.session_tool_payloads(session_doc)
    return deps.build_active_sequence_snapshot_state(
        payload=dict(payload or {}),
        active=deps.compound_request_assessment_is_active(payload),
        source_tool_index=deps.latest_tool_payload_position(
            tool_payloads,
            payload_type="qwen_compound_request_assessment_contract",
            request_id=_snapshot_clean_text((payload or {}).get("request_id")),
        ),
    )


def _snapshot_recent_focus_state(
    *,
    deps: ConversationSnapshotDependencies,
    latest_grounded_turn: Dict[str, Any],
    latest_artifact: Dict[str, Any],
    latest_recovery_contract: Dict[str, Any],
) -> Dict[str, Any]:
    grounded_payload = dict(latest_grounded_turn.get("payload") or {}) if isinstance(latest_grounded_turn, dict) else {}
    artifact_payload = dict(latest_artifact.get("payload") or {}) if isinstance(latest_artifact, dict) else {}
    source_name = _snapshot_clean_text((grounded_payload or {}).get("source_name"))
    source_kind = _snapshot_clean_text((grounded_payload or {}).get("source_kind"))
    family_id = _snapshot_clean_text((artifact_payload or {}).get("family_id") or (grounded_payload or {}).get("artifact_family_id"))
    dimensions = artifact_payload.get("dimensions") if isinstance(artifact_payload.get("dimensions"), dict) else {}
    known_entities = grounded_payload.get("known_entities") if isinstance(grounded_payload.get("known_entities"), list) else []
    grounded_compatible_artifact_state = (
        dict(latest_artifact or {})
        if isinstance(latest_artifact, dict) and bool(latest_artifact.get("grounded_compatible"))
        else {}
    )
    matching_recovery_state = (
        dict(latest_recovery_contract or {})
        if _snapshot_recovery_matches_grounded_turn(latest_recovery_contract, latest_grounded_turn)
        else {}
    )
    branch_source_tool_index = _snapshot_max_source_tool_index(
        latest_grounded_turn,
        grounded_compatible_artifact_state,
        matching_recovery_state,
    )
    surface_descriptor = deps.grounded_recent_focus_surface_descriptor(
        source_report=source_name,
        source_kind=source_kind,
        source_family=family_id,
        dimensions=dimensions,
    )
    surface_class = _snapshot_clean_text((surface_descriptor or {}).get("surface_class"))
    source_request_id = _snapshot_clean_text((grounded_payload or {}).get("request_id"))
    source_capability = _snapshot_clean_text(
        matching_recovery_state.get("source_capability_id") if isinstance(matching_recovery_state, dict) else ""
    )
    if surface_class == "entity_detail":
        entity_payload = known_entities[0] if known_entities and isinstance(known_entities[0], dict) else {}
        focus_grain = _snapshot_clean_text(dimensions.get("entity_type") or entity_payload.get("entity_type"))
        focus_label = _snapshot_clean_text(
            dimensions.get("entity_label")
            or entity_payload.get("entity_label")
            or (surface_descriptor.get("focus_label_fallback") if isinstance(surface_descriptor, dict) else "")
        )
        focus_key = _snapshot_clean_text(
            dimensions.get("entity_key")
            or entity_payload.get("entity_key")
            or focus_label
        )
        if focus_label:
            entity_surface_descriptor = dict(surface_descriptor or {})
            entity_surface_descriptor.update(
                {
                    "focus_grain": focus_grain or "entity",
                    "focus_label": focus_label,
                    "focus_key": focus_key,
                }
            )
            return deps.build_grounded_recent_focus_state_from_surface_descriptor(
                surface_descriptor=entity_surface_descriptor,
                source_request_id=source_request_id,
                source_family=family_id or "entity_detail",
                source_capability=source_capability,
                source_report=source_name,
                source_tool_index=branch_source_tool_index,
            )
    if surface_class == "statement":
        return deps.build_grounded_recent_focus_state_from_surface_descriptor(
            surface_descriptor=surface_descriptor,
            source_request_id=source_request_id,
            source_family=family_id,
            source_capability="",
            source_report=source_name,
            source_tool_index=branch_source_tool_index,
        )
    if surface_class == "master_data_listing":
        focus_grain = _snapshot_clean_text(surface_descriptor.get("focus_grain")) or "master_data"
        single_row_entity_focus = deps.single_row_master_data_entity_recent_focus(
            grounded_payload=grounded_payload,
            latest_grounded_turn=latest_grounded_turn,
            latest_recovery_contract=latest_recovery_contract,
            focus_grain=focus_grain,
            source_name=source_name,
            family_id=family_id,
        )
        if single_row_entity_focus:
            return single_row_entity_focus
        return deps.build_grounded_recent_focus_state_from_surface_descriptor(
            surface_descriptor=surface_descriptor,
            source_request_id=source_request_id,
            source_family=family_id,
            source_capability=source_capability,
            source_report=source_name,
            source_tool_index=branch_source_tool_index,
        )
    if surface_class == "transaction_listing":
        focus_grain = _snapshot_clean_text(surface_descriptor.get("focus_grain")) or "transaction_listing"
        single_row_document_focus = deps.single_row_transaction_document_recent_focus(
            grounded_payload=grounded_payload,
            latest_grounded_turn=latest_grounded_turn,
            latest_recovery_contract=latest_recovery_contract,
            focus_grain=focus_grain,
            source_name=source_name,
            family_id=family_id,
        )
        if single_row_document_focus:
            return single_row_document_focus
        return deps.build_grounded_recent_focus_state_from_surface_descriptor(
            surface_descriptor=surface_descriptor,
            source_request_id=source_request_id,
            source_family=family_id,
            source_capability=source_capability,
            source_report=source_name,
            source_tool_index=branch_source_tool_index,
        )
    if surface_class == "report":
        return deps.build_grounded_recent_focus_state_from_surface_descriptor(
            surface_descriptor=surface_descriptor,
            source_request_id=source_request_id,
            source_family=family_id,
            source_capability=source_capability,
            source_report=source_name,
            source_tool_index=branch_source_tool_index,
        )
    return deps.empty_recent_focus_state()


def _historical_compatible_artifact_payload(
    *,
    deps: ConversationSnapshotDependencies,
    tool_payloads: List[Dict[str, Any]],
    grounded_turn_payload: Dict[str, Any],
) -> Tuple[Dict[str, Any], int]:
    for index in range(len(tool_payloads) - 1, -1, -1):
        payload = dict(tool_payloads[index] or {})
        payload_type = _snapshot_clean_text(payload.get("type")).lower()
        if payload_type not in {
            "qwen_normalized_family_artifact_contract",
            "qwen_composite_family_artifact",
            "qwen_entity_detail_artifact",
        }:
            continue
        if deps.artifact_compatible_with_grounded_turn(
            artifact_payload=payload,
            grounded_turn=grounded_turn_payload,
        ):
            return payload, index
    return {}, -1


def _historical_compatible_recovery_payload(
    *,
    tool_payloads: List[Dict[str, Any]],
    grounded_turn_payload: Dict[str, Any],
) -> Tuple[Dict[str, Any], int]:
    grounded_request_id = _snapshot_clean_text(
        grounded_turn_payload.get("trace_request_id") or grounded_turn_payload.get("request_id")
    )
    if not grounded_request_id:
        return {}, -1
    for index in range(len(tool_payloads) - 1, -1, -1):
        payload = dict(tool_payloads[index] or {})
        if _snapshot_clean_text(payload.get("type")).lower() != "qwen_artifact_enrichment_recovery_contract":
            continue
        if _snapshot_clean_text(payload.get("source_request_id")) != grounded_request_id:
            continue
        return payload, index
    return {}, -1


def _historical_recent_focus_candidate(
    *,
    session_doc,
    recent_focus: Dict[str, Any],
    deps: ConversationSnapshotDependencies,
) -> Dict[str, Any]:
    tool_payloads = deps.session_tool_payloads(session_doc)
    current_request_id = _snapshot_clean_text((recent_focus or {}).get("source_request_id"))
    current_focus_kind = _snapshot_clean_text((recent_focus or {}).get("focus_kind"))
    current_focus_grain = _snapshot_clean_text((recent_focus or {}).get("focus_grain"))
    current_focus_label = _snapshot_clean_text((recent_focus or {}).get("focus_label"))
    for index in range(len(tool_payloads) - 1, -1, -1):
        payload = dict(tool_payloads[index] or {})
        if _snapshot_clean_text(payload.get("type")).lower() != "qwen_grounded_turn_context":
            continue
        if not bool(payload.get("grounded")):
            continue
        candidate_request_id = _snapshot_clean_text(payload.get("trace_request_id") or payload.get("request_id"))
        if not candidate_request_id or candidate_request_id == current_request_id:
            continue
        artifact_payload, artifact_index = _historical_compatible_artifact_payload(
            deps=deps,
            tool_payloads=tool_payloads,
            grounded_turn_payload=payload,
        )
        recovery_payload, recovery_index = _historical_compatible_recovery_payload(
            tool_payloads=tool_payloads,
            grounded_turn_payload=payload,
        )
        historical_snapshot_inputs = deps.build_historical_recent_focus_snapshot_inputs(
            grounded_turn_payload=payload,
            grounded_turn_source_tool_index=index,
            artifact_payload=dict(artifact_payload or {}),
            artifact_source_tool_index=artifact_index,
            recovery_payload=dict(recovery_payload or {}),
            recovery_source_tool_index=recovery_index,
        )
        candidate_recent_focus = _snapshot_recent_focus_state(
            deps=deps,
            latest_grounded_turn=dict(historical_snapshot_inputs.get("latest_grounded_turn") or {}),
            latest_artifact=dict(historical_snapshot_inputs.get("latest_artifact") or {}),
            latest_recovery_contract=dict(historical_snapshot_inputs.get("latest_recovery_contract") or {}),
        )
        if not bool(candidate_recent_focus.get("available")):
            continue
        if (
            _snapshot_clean_text(candidate_recent_focus.get("focus_kind")) == current_focus_kind
            and _snapshot_clean_text(candidate_recent_focus.get("focus_grain")) == current_focus_grain
            and _snapshot_clean_text(candidate_recent_focus.get("focus_label")) == current_focus_label
        ):
            continue
        return candidate_recent_focus
    return {}


def _accepted_repair_resumable_prior_request_state(
    *,
    session_doc,
    latest_repair_intent: Dict[str, Any],
    deps: ConversationSnapshotDependencies,
) -> Dict[str, Any]:
    repair_payload = dict(latest_repair_intent.get("payload") or {}) if isinstance(latest_repair_intent, dict) else {}
    if (
        str(repair_payload.get("repair_state") or "").strip() == "accepted"
        and bool(repair_payload.get("targets_prior_recovery"))
        and str(repair_payload.get("repair_intent_type") or "").strip() == "accept_recovery_action"
    ):
        tool_payloads = deps.session_tool_payloads(session_doc)
        accepted_index = -1
        for index in range(len(tool_payloads) - 1, -1, -1):
            item = tool_payloads[index]
            if str(item.get("type") or "").strip() != "qwen_conversational_repair_intent_contract":
                continue
            if str(item.get("request_id") or "").strip() != str(repair_payload.get("request_id") or "").strip():
                continue
            accepted_index = index
            break
        if accepted_index >= 0:
            prior_recovery = {}
            prior_recovery_index = -1
            for index in range(accepted_index - 1, -1, -1):
                item = tool_payloads[index]
                if str(item.get("type") or "").strip() == "qwen_artifact_enrichment_recovery_contract":
                    prior_recovery = dict(item or {})
                    prior_recovery_index = index
                    break
            newer_grounded_turn = {}
            newer_grounded_turn_index = -1
            for index in range(accepted_index + 1, len(tool_payloads)):
                item = tool_payloads[index]
                if str(item.get("type") or "").strip() == "qwen_grounded_turn_context":
                    newer_grounded_turn = dict(item or {})
                    newer_grounded_turn_index = index
            prior_source_request_id = _snapshot_clean_text(prior_recovery.get("source_request_id"))
            newer_trace_request_id = _snapshot_clean_text(
                newer_grounded_turn.get("trace_request_id") or newer_grounded_turn.get("request_id")
            )
            if prior_source_request_id and newer_trace_request_id and newer_trace_request_id != prior_source_request_id:
                branch_source_tool_index = _snapshot_max_source_tool_index(
                    {"source_tool_index": accepted_index},
                    {"source_tool_index": prior_recovery_index},
                    {"source_tool_index": newer_grounded_turn_index},
                )
                return {
                    "available": True,
                    "branch_kind": "accepted_recovery_origin",
                    "branch_label": _snapshot_clean_text(prior_recovery.get("source_report"))
                    or _snapshot_clean_text(prior_recovery.get("source_family_id")),
                    "source_request_id": prior_source_request_id,
                    "target_family": _snapshot_clean_text(prior_recovery.get("source_family_id")),
                    "target_scope": dict(prior_recovery.get("preservable_scope") or {}),
                    "accepted_recovery_action": _snapshot_clean_text(repair_payload.get("accepted_recovery_action")),
                    "resumable": True,
                    "suggested_restore_mode": "requery_prior_branch",
                    "derivation_basis": "accepted_repair_with_newer_grounded_turn",
                    "confidence": 0.79,
                    "source_tool_index": branch_source_tool_index,
                    "internal_details": {
                        "prior_recovery_payload": prior_recovery,
                        "accepted_repair_source_tool_index": accepted_index,
                        "prior_recovery_source_tool_index": prior_recovery_index,
                        "newer_grounded_turn_source_tool_index": newer_grounded_turn_index,
                    },
                }
    return {}


def _historical_resumable_prior_request_state(
    *,
    session_doc,
    recent_focus: Dict[str, Any],
    deps: ConversationSnapshotDependencies,
) -> Dict[str, Any]:
    candidate_recent_focus = _historical_recent_focus_candidate(
        session_doc=session_doc,
        recent_focus=recent_focus,
        deps=deps,
    )
    if not candidate_recent_focus:
        return {}
    return {
        "available": True,
        "branch_kind": "prior_recent_focus_origin",
        "branch_label": _snapshot_clean_text(candidate_recent_focus.get("focus_label"))
        or _snapshot_clean_text(candidate_recent_focus.get("source_report")),
        "source_request_id": _snapshot_clean_text(candidate_recent_focus.get("source_request_id")),
        "target_family": _snapshot_clean_text(candidate_recent_focus.get("source_family")),
        "target_scope": {
            "focus_kind": _snapshot_clean_text(candidate_recent_focus.get("focus_kind")),
            "focus_grain": _snapshot_clean_text(candidate_recent_focus.get("focus_grain")),
            "focus_key": _snapshot_clean_text(candidate_recent_focus.get("focus_key")),
            "focus_label": _snapshot_clean_text(candidate_recent_focus.get("focus_label")),
            "source_capability": _snapshot_clean_text(candidate_recent_focus.get("source_capability")),
            "source_report": _snapshot_clean_text(candidate_recent_focus.get("source_report")),
            "deictic_allowed": bool(candidate_recent_focus.get("deictic_allowed")),
            "explicit_named_allowed": bool(candidate_recent_focus.get("explicit_named_allowed")),
        },
        "accepted_recovery_action": "",
        "resumable": True,
        "suggested_restore_mode": "restore_recent_focus",
        "derivation_basis": "historical_grounded_branch_before_current_focus",
        "confidence": float(max(0.0, min(1.0, float(candidate_recent_focus.get("confidence") or 0.0) * 0.92))),
        "source_tool_index": _snapshot_source_tool_index(candidate_recent_focus),
        "internal_details": {
            "prior_recent_focus": dict(candidate_recent_focus or {}),
        },
    }


def _annotate_resumable_prior_request_candidate(
    candidate_state: Dict[str, Any],
    *,
    arbitration_basis: str,
) -> Dict[str, Any]:
    annotated = dict(candidate_state or {})
    internal_details = (
        dict(annotated.get("internal_details") or {})
        if isinstance(annotated.get("internal_details"), dict)
        else {}
    )
    internal_details["arbitration_basis"] = _snapshot_clean_text(arbitration_basis)
    annotated["internal_details"] = internal_details
    return annotated


def _select_resumable_prior_request_candidate(
    *,
    accepted_repair_candidate: Dict[str, Any],
    historical_candidate: Dict[str, Any],
) -> Dict[str, Any]:
    accepted_available = bool((accepted_repair_candidate or {}).get("available"))
    historical_available = bool((historical_candidate or {}).get("available"))
    if accepted_available and historical_available:
        historical_basis = _snapshot_peer_precedence_basis(historical_candidate, accepted_repair_candidate)
        if historical_basis == "newer":
            return _annotate_resumable_prior_request_candidate(
                historical_candidate,
                arbitration_basis="historical_prior_focus_precedes_accepted_repair_by_newer_index",
            )
        if historical_basis == "known_over_unindexed":
            return _annotate_resumable_prior_request_candidate(
                historical_candidate,
                arbitration_basis="historical_prior_focus_precedes_accepted_repair_by_known_over_unindexed",
            )
        accepted_basis = _snapshot_peer_precedence_basis(accepted_repair_candidate, historical_candidate)
        if accepted_basis == "newer":
            return _annotate_resumable_prior_request_candidate(
                accepted_repair_candidate,
                arbitration_basis="accepted_repair_precedes_historical_prior_focus_by_newer_index",
            )
        if accepted_basis == "known_over_unindexed":
            return _annotate_resumable_prior_request_candidate(
                accepted_repair_candidate,
                arbitration_basis="accepted_repair_precedes_historical_prior_focus_by_known_over_unindexed",
            )
        return _annotate_resumable_prior_request_candidate(
            accepted_repair_candidate,
            arbitration_basis="accepted_repair_defaults_when_peer_precedence_is_indeterminate",
        )
    if accepted_available:
        return _annotate_resumable_prior_request_candidate(
            accepted_repair_candidate,
            arbitration_basis="accepted_repair_only_available",
        )
    if historical_available:
        return _annotate_resumable_prior_request_candidate(
            historical_candidate,
            arbitration_basis="historical_prior_focus_only_available",
        )
    return {}


def _snapshot_resumable_prior_request_state(
    *,
    session_doc,
    pending_clarification: Dict[str, Any],
    active_sequence: Dict[str, Any],
    recent_focus: Dict[str, Any],
    latest_recovery_contract: Dict[str, Any],
    latest_repair_intent: Dict[str, Any],
    deps: ConversationSnapshotDependencies,
) -> Dict[str, Any]:
    _ = pending_clarification, active_sequence, latest_recovery_contract
    accepted_repair_candidate = _accepted_repair_resumable_prior_request_state(
        session_doc=session_doc,
        latest_repair_intent=latest_repair_intent,
        deps=deps,
    )
    historical_candidate = _historical_resumable_prior_request_state(
        session_doc=session_doc,
        recent_focus=recent_focus,
        deps=deps,
    )
    selected_candidate = _select_resumable_prior_request_candidate(
        accepted_repair_candidate=accepted_repair_candidate,
        historical_candidate=historical_candidate,
    )
    if selected_candidate:
        return selected_candidate
    return deps.empty_resumable_prior_request_state()


def build_conversation_state_snapshot(
    *,
    request_id: str,
    session_doc,
    deps: ConversationSnapshotDependencies,
) -> Dict[str, Any]:
    pending_clarification = _snapshot_pending_clarification_state(session_doc=session_doc, deps=deps)
    latest_grounded_turn = _snapshot_latest_grounded_turn_state(session_doc=session_doc, deps=deps)
    latest_artifact = _snapshot_latest_artifact_state(
        session_doc,
        deps=deps,
        grounded_turn_payload=dict(latest_grounded_turn.get("payload") or {}),
    )
    latest_recovery_contract = _snapshot_latest_recovery_contract_state(session_doc=session_doc, deps=deps)
    latest_repair_intent = _snapshot_latest_repair_intent_state(session_doc=session_doc, deps=deps)
    active_sequence = _snapshot_active_sequence_state(session_doc=session_doc, deps=deps)
    recent_focus = _snapshot_recent_focus_state(
        deps=deps,
        latest_grounded_turn=latest_grounded_turn,
        latest_artifact=latest_artifact,
        latest_recovery_contract=latest_recovery_contract,
    )
    recent_focus_affordance_contract = deps.build_recent_focus_affordance_contract_from_snapshot(
        request_id=request_id,
        recent_focus_state=recent_focus,
    )
    recent_focus_affordance = (
        recent_focus_affordance_contract.to_payload() if recent_focus_affordance_contract is not None else {}
    )
    resumable_prior_request = _snapshot_resumable_prior_request_state(
        session_doc=session_doc,
        pending_clarification=pending_clarification,
        active_sequence=active_sequence,
        recent_focus=recent_focus,
        latest_recovery_contract=latest_recovery_contract,
        latest_repair_intent=latest_repair_intent,
        deps=deps,
    )
    return {
        "type": "qwen_conversation_state_snapshot",
        "snapshot_version": "1.0",
        "request_id": _snapshot_clean_text(request_id),
        "pending_clarification": pending_clarification,
        "latest_grounded_turn": latest_grounded_turn,
        "latest_artifact": latest_artifact,
        "latest_recovery_contract": latest_recovery_contract,
        "latest_repair_intent": latest_repair_intent,
        "active_sequence": active_sequence,
        "recent_focus": recent_focus,
        "recent_focus_affordance": recent_focus_affordance,
        "resumable_prior_request": resumable_prior_request,
        "state_quality": deps.build_snapshot_state_quality(
            pending_clarification=pending_clarification,
            latest_grounded_turn=latest_grounded_turn,
            latest_artifact=latest_artifact,
            latest_recovery_contract=latest_recovery_contract,
            latest_repair_intent=latest_repair_intent,
            active_sequence=active_sequence,
            recent_focus=recent_focus,
            recent_focus_affordance=recent_focus_affordance,
            resumable_prior_request=resumable_prior_request,
        ),
        "internal_details": deps.build_snapshot_internal_details(
            pending_clarification=pending_clarification,
            latest_artifact=latest_artifact,
            latest_repair_intent=latest_repair_intent,
            recent_focus=recent_focus,
            recent_focus_affordance=recent_focus_affordance,
            resumable_prior_request=resumable_prior_request,
        ),
    }
