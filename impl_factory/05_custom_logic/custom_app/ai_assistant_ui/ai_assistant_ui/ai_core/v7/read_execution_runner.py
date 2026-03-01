from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional


def execute_read_loop(
    *,
    message: str,
    mode: str,
    source: str,
    plan_seed: Dict[str, Any],
    max_steps: int,
    spec_obj: Dict[str, Any],
    spec_envelope: Dict[str, Any],
    resolved: Dict[str, Any],
    selected_report: str,
    selected_score: Any,
    candidate_reports: List[str],
    candidate_scores: Dict[str, Any],
    candidate_cursor: int,
    initial_step_trace: List[Dict[str, Any]],
    previous_topic_state: Dict[str, Any],
    session_name: Optional[str],
    user: Optional[str],
    export_requested: bool,
    direct_doc_payload: Optional[Dict[str, Any]],
    direct_latest_payload: Optional[Dict[str, Any]],
    clarify_decision: Dict[str, Any],
    internal_retry_key: str,
    verdict_pass: str,
    verdict_hard_fail: str,
    verdict_repairable_fail: str,
    execute_selected_report_direct_fn: Callable[..., Optional[Dict[str, Any]]],
    legacy_path_unavailable_payload_fn: Callable[[], Dict[str, Any]],
    load_last_result_payload_fn: Callable[..., Optional[Dict[str, Any]]],
    extract_auto_switch_pending_fn: Callable[[Dict[str, Any]], Optional[Dict[str, Any]]],
    capture_source_columns_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
    as_payload_fn: Callable[[Any], Dict[str, Any]],
    apply_transform_last_fn: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]],
    looks_like_system_error_text_fn: Callable[[Dict[str, Any]], bool],
    make_transform_tool_message_fn: Callable[..., str],
    shape_response_fn: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]],
    sanitize_user_payload_fn: Callable[..., Dict[str, Any]],
    apply_requested_entity_row_filters_fn: Callable[..., Dict[str, Any]],
    make_response_shaper_tool_message_fn: Callable[..., str],
    evaluate_quality_gate_fn: Callable[..., Dict[str, Any]],
    should_switch_candidate_on_repairable_fn: Callable[..., bool],
    resolve_business_request_fn: Callable[..., Dict[str, Any]],
    quality_has_repairable_failure_class_fn: Callable[[Dict[str, Any], List[str]], bool],
    unsupported_message_from_spec_fn: Callable[[Dict[str, Any]], str],
    planner_option_actions_fn: Callable[..., Dict[str, str]],
    default_clarification_question_fn: Callable[[str], str],
) -> Dict[str, Any]:
    seen_signatures = set()
    executed_steps = 0
    repair_attempts = 0
    candidate_switch_attempts = 0
    repeated_guard = False
    step_trace: List[Dict[str, Any]] = list(initial_step_trace or [])
    payload: Dict[str, Any] = {"type": "text", "text": "No output generated."}
    quality: Dict[str, Any] = {
        "verdict": verdict_hard_fail,
        "failed_check_ids": ["QG00_NOT_EVALUATED"],
        "hard_fail_check_ids": ["QG00_NOT_EVALUATED"],
        "repairable_check_ids": [],
        "checks": [],
    }
    shaper_tool_msg = ""
    transform_tool_msg = ""

    for step_no in range(1, max(1, int(max_steps)) + 1):
        sig = f"{mode}|{source}|{selected_report}|{str(message or '').strip().lower()}|{json.dumps(plan_seed, sort_keys=True, default=str)}"
        if sig in seen_signatures:
            repeated_guard = True
            step_trace.append({"step": step_no, "action": "guard_stop", "signature_repeated": True})
            payload = {
                "type": "text",
                "text": "I couldn't progress this request safely due to a repeated execution path. Please restate the request in one sentence.",
            }
            quality = evaluate_quality_gate_fn(
                business_spec=(spec_envelope.get("spec") if isinstance(spec_envelope.get("spec"), dict) else {}),
                resolved=resolved,
                payload=payload,
                repeated_call_guard_triggered=True,
            )
            break

        seen_signatures.add(sig)
        if mode == "continue":
            out = execute_selected_report_direct_fn(
                message=message,
                selected_report=selected_report,
                business_spec=spec_obj,
                export=export_requested,
                session_name=session_name,
                user=user,
            )
            if out is None:
                out = legacy_path_unavailable_payload_fn()
                action = "continue_unavailable"
            else:
                action = "direct_selected_report_continue"
        else:
            if str(spec_obj.get("intent") or "").strip().upper() == "TRANSFORM_LAST":
                from_last = load_last_result_payload_fn(session_name=session_name)
                if isinstance(from_last, dict):
                    out = from_last
                    action = "transform_from_last_result"
                else:
                    out = {
                        "type": "text",
                        "text": "I need a previous result in this chat to apply that transform.",
                    }
                    action = "transform_without_prior_result"
            elif isinstance(direct_doc_payload, dict):
                out = dict(direct_doc_payload)
                action = "direct_document_lookup"
            elif isinstance(direct_latest_payload, dict):
                out = dict(direct_latest_payload)
                action = "direct_latest_records_lookup"
            else:
                out = execute_selected_report_direct_fn(
                    message=message,
                    selected_report=selected_report,
                    business_spec=spec_obj,
                    export=export_requested,
                    session_name=session_name,
                    user=user,
                )
                if out is None:
                    out = legacy_path_unavailable_payload_fn()
                    action = "direct_selected_report_failed"
                else:
                    action = "direct_selected_report"

        executed_steps += 1
        auto_pending = extract_auto_switch_pending_fn(out if isinstance(out, dict) else {})
        if auto_pending is not None:
            qc = auto_pending.get("quality_clarification") if isinstance(auto_pending.get("quality_clarification"), dict) else {}
            suggested_report = str(
                qc.get("suggested_report")
                or qc.get("report_name")
                or auto_pending.get("report_name")
                or ""
            ).strip()
            switched = False

            if suggested_report:
                if suggested_report not in candidate_reports:
                    suggested_report = ""
                if suggested_report in candidate_reports and (candidate_switch_attempts < 4):
                    suggested_idx = candidate_reports.index(suggested_report)
                    if suggested_idx != candidate_cursor or suggested_report != selected_report:
                        candidate_switch_attempts += 1
                        candidate_cursor = suggested_idx
                        selected_report = suggested_report
                        selected_score = candidate_scores.get(selected_report, selected_score)
                        resolved = dict(resolved)
                        resolved["selected_report"] = selected_report
                        resolved["selected_score"] = selected_score
                        switched = True
                        step_trace.append(
                            {
                                "step": step_no,
                                "action": "auto_switch_report_from_quality_pending",
                                "selected_report": selected_report,
                                "switch_attempt": candidate_switch_attempts,
                            }
                        )
                        continue

            if (not switched) and (candidate_cursor + 1 < len(candidate_reports)) and (candidate_switch_attempts < 4):
                candidate_switch_attempts += 1
                candidate_cursor += 1
                selected_report = candidate_reports[candidate_cursor]
                selected_score = candidate_scores.get(selected_report, selected_score)
                resolved = dict(resolved)
                resolved["selected_report"] = selected_report
                resolved["selected_score"] = selected_score
                step_trace.append(
                    {
                        "step": step_no,
                        "action": "auto_switch_next_candidate_from_quality_pending",
                        "selected_report": selected_report,
                        "switch_attempt": candidate_switch_attempts,
                    }
                )
                continue

            out = legacy_path_unavailable_payload_fn()
            step_trace.append({"step": step_no, "action": "auto_switch_pending_exhausted", "applied": False})

        wants_retry = bool(out.get(internal_retry_key))
        step_trace.append({"step": step_no, "action": action, "retry_requested": wants_retry})
        out.pop(internal_retry_key, None)
        payload = capture_source_columns_fn(as_payload_fn(out))
        payload = apply_transform_last_fn(payload, spec_obj)
        if looks_like_system_error_text_fn(payload):
            payload = {
                "type": "text",
                "text": "I hit a report execution issue for this request. Please adjust one filter (date/company/warehouse) and retry.",
            }
        transform_tool_msg = make_transform_tool_message_fn(tool=source, mode=mode, payload=payload)
        payload = shape_response_fn(payload, spec_obj)
        payload = sanitize_user_payload_fn(payload=payload, business_spec=spec_obj)
        payload = apply_requested_entity_row_filters_fn(payload=payload, business_spec=spec_obj)
        shaper_tool_msg = make_response_shaper_tool_message_fn(tool=source, mode=mode, shaped_payload=payload)

        payload_report = str(payload.get("report_name") or "").strip()
        if payload_report:
            selected_report = payload_report
            resolved = dict(resolved)
            resolved["selected_report"] = payload_report
            if payload_report not in candidate_reports:
                candidate_reports.append(payload_report)
            try:
                candidate_cursor = candidate_reports.index(payload_report)
            except Exception:
                pass

        quality = evaluate_quality_gate_fn(
            business_spec=spec_obj,
            resolved=resolved,
            payload=payload,
            repeated_call_guard_triggered=False,
        )
        q_table = payload.get("table") if isinstance(payload.get("table"), dict) else {}
        q_rows = q_table.get("rows") if isinstance(q_table.get("rows"), list) else []
        q_cols = q_table.get("columns") if isinstance(q_table.get("columns"), list) else []
        step_trace.append(
            {
                "step": step_no,
                "quality_verdict": quality.get("verdict"),
                "failed_check_ids": list(quality.get("failed_check_ids") or []),
                "report_name": str(payload.get("report_name") or selected_report or ""),
                "row_count": len(q_rows),
                "column_labels": [
                    str((c.get("label") or c.get("fieldname") or "")).strip()
                    for c in q_cols[:10]
                    if isinstance(c, dict)
                ],
            }
        )

        if wants_retry and repair_attempts < 1:
            repair_attempts += 1
            continue
        if quality.get("verdict") == verdict_pass:
            break
        if quality.get("verdict") == verdict_hard_fail:
            break

        if should_switch_candidate_on_repairable_fn(
            quality=quality,
            intent=str(spec_obj.get("intent") or "").strip().upper(),
            task_class=str(spec_obj.get("task_class") or "").strip().lower(),
            candidate_cursor=candidate_cursor,
            candidate_reports=candidate_reports,
            candidate_switch_attempts=candidate_switch_attempts,
        ):
            candidate_switch_attempts += 1
            candidate_cursor += 1
            selected_report = candidate_reports[candidate_cursor]
            selected_score = candidate_scores.get(selected_report, selected_score)
            resolved = dict(resolved)
            resolved["selected_report"] = selected_report
            resolved["selected_score"] = selected_score
            step_trace.append(
                {
                    "step": step_no,
                    "action": "switch_candidate_after_quality_fail",
                    "selected_report": selected_report,
                }
            )
            continue

        if (
            quality.get("verdict") == verdict_repairable_fail
            and (repair_attempts < 1)
            and str(spec_obj.get("intent") or "").strip().upper() != "TRANSFORM_LAST"
        ):
            repair_attempts += 1
            plan_seed["_repair_attempt"] = repair_attempts
            resolve_envelope = resolve_business_request_fn(
                business_spec=spec_obj,
                user=user,
                topic_state=previous_topic_state,
            )
            resolved = resolve_envelope.get("resolved") if isinstance(resolve_envelope.get("resolved"), dict) else {}
            selected_report = str(resolved.get("selected_report") or "").strip()
            selected_score = resolved.get("selected_score")
            continue

        break

    if quality.get("verdict") == verdict_repairable_fail:
        if str(spec_obj.get("intent") or "").strip().upper() != "TRANSFORM_LAST":
            if quality_has_repairable_failure_class_fn(
                quality,
                classes=["shape", "data", "constraint", "semantic"],
            ):
                unsupported = unsupported_message_from_spec_fn(spec_obj)
                clarify_text = default_clarification_question_fn("hard_constraint_not_supported")
                planner_options = ["Switch to compatible report", "Keep current scope"]
                option_actions = planner_option_actions_fn(options=planner_options, pending={})
                payload = {
                    "type": "text",
                    "text": f"{unsupported} {clarify_text}",
                    "_pending_state": {
                        "mode": "planner_clarify",
                        "base_question": str(message or "").strip(),
                        "report_name": str(selected_report or "").strip(),
                        "filters_so_far": dict(spec_obj.get("filters") or {}) if isinstance(spec_obj.get("filters"), dict) else {},
                        "clarification_question": f"{unsupported} {clarify_text}",
                        "clarification_options": list(planner_options),
                        "options": list(planner_options),
                        "option_actions": dict(option_actions),
                        "clarification_reason": "hard_constraint_not_supported",
                        "spec_so_far": {
                            "task_class": str(spec_obj.get("task_class") or "").strip().lower(),
                            "subject": str(spec_obj.get("subject") or "").strip(),
                            "metric": str(spec_obj.get("metric") or "").strip(),
                            "domain": str(spec_obj.get("domain") or "").strip(),
                            "top_n": int(spec_obj.get("top_n") or 0),
                            "output_contract": dict(spec_obj.get("output_contract") or {}) if isinstance(spec_obj.get("output_contract"), dict) else {},
                        },
                        "clarification_round": 1,
                    },
                }
                clarify_decision = {
                    "should_clarify": True,
                    "reason": "hard_constraint_not_supported",
                    "question": f"{unsupported} {clarify_text}",
                    "policy_version": "phase5_blocker_only_v1",
                }
                quality = evaluate_quality_gate_fn(
                    business_spec=spec_obj,
                    resolved=resolved,
                    payload=payload,
                    repeated_call_guard_triggered=False,
                )

    return {
        "payload": payload,
        "quality": quality,
        "shaper_tool_msg": shaper_tool_msg,
        "transform_tool_msg": transform_tool_msg,
        "selected_report": selected_report,
        "selected_score": selected_score,
        "resolved": resolved,
        "step_trace": step_trace,
        "executed_steps": executed_steps,
        "repair_attempts": repair_attempts,
        "repeated_guard": repeated_guard,
        "clarify_decision": clarify_decision,
    }
