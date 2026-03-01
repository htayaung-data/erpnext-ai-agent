from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional


def normalize_option_label(value: str) -> str:
    return " ".join(str(value or "").strip().lower().replace("_", " ").replace("-", " ").split())


def match_option_choice(message: str, options: List[str]) -> str:
    msg = str(message or "").strip()
    if (not msg) or (not options):
        return ""
    normalized = [str(x).strip() for x in list(options or []) if str(x or "").strip()]
    if not normalized:
        return ""
    msg_norm = normalize_option_label(msg)

    match_idx = re.search(r"\b(\d{1,2})\b", msg_norm)
    if match_idx:
        try:
            idx = int(match_idx.group(1)) - 1
        except Exception:
            idx = -1
        if 0 <= idx < len(normalized):
            return normalized[idx]

    for opt in normalized:
        opt_norm = normalize_option_label(opt)
        if msg_norm == opt_norm:
            return opt
    for opt in normalized:
        opt_norm = normalize_option_label(opt)
        if opt_norm and (opt_norm in msg_norm or msg_norm in opt_norm):
            return opt
    return ""


def planner_option_actions(*, options: List[str], pending: Dict[str, Any]) -> Dict[str, str]:
    raw_pending = pending if isinstance(pending, dict) else {}
    raw_map = raw_pending.get("option_actions") if isinstance(raw_pending.get("option_actions"), dict) else {}
    out: Dict[str, str] = {}
    for key, value in raw_map.items():
        norm_key = normalize_option_label(str(key or ""))
        norm_value = str(value or "").strip().lower()
        if norm_key and norm_value:
            out[norm_key] = norm_value
    if out:
        return out
    vals = [str(x).strip() for x in list(options or []) if str(x or "").strip()]
    if len(vals) >= 2:
        out[normalize_option_label(vals[0])] = "switch_report"
        out[normalize_option_label(vals[1])] = "keep_current"
    return out


def looks_like_scope_answer_text(text: str) -> bool:
    tokens = [tok for tok in re.findall(r"[A-Za-z0-9_]+", str(text or "").strip().lower()) if tok]
    if not tokens:
        return False
    if len(tokens) > 4:
        return False
    if any(tok.isdigit() for tok in tokens):
        return False
    return True


def first_int_in_text(text: str) -> int:
    match = re.search(r"\b(\d{1,3})\b", str(text or ""))
    if not match:
        return 0
    try:
        return int(match.group(1))
    except Exception:
        return 0


def recover_latest_record_followup_spec(
    *,
    spec_obj: Dict[str, Any],
    message: str,
    previous_topic_state: Dict[str, Any],
    resolve_record_doctype_candidates: Callable[[str, Dict[str, Any]], List[str]],
    resolve_explicit_doctype_name: Callable[[str], str],
    load_submittable_doctypes: Callable[[], List[str]],
) -> Dict[str, Any]:
    spec = dict(spec_obj or {})
    prev = previous_topic_state if isinstance(previous_topic_state, dict) else {}
    active_topic = prev.get("active_topic") if isinstance(prev.get("active_topic"), dict) else {}
    unresolved = prev.get("unresolved_blocker") if isinstance(prev.get("unresolved_blocker"), dict) else {}

    if not bool(unresolved.get("present")):
        return spec
    if not looks_like_scope_answer_text(message):
        return spec
    active_task = str(active_topic.get("task_class") or "").strip().lower()
    active_subject = str(active_topic.get("subject") or "").strip().lower()
    unresolved_q = str(unresolved.get("question") or "").strip().lower()
    likely_record_type_followup = (
        active_task == "list_latest_records"
        or ("invoice" in active_subject)
        or ("record type" in unresolved_q)
    )
    if not likely_record_type_followup:
        return spec

    infer_spec: Dict[str, Any] = {
        "subject": str(active_topic.get("subject") or spec.get("subject") or "").strip(),
        "metric": str(active_topic.get("metric") or spec.get("metric") or "").strip(),
        "filters": dict(spec.get("filters") or {}) if isinstance(spec.get("filters"), dict) else {},
        "domain": str(active_topic.get("domain") or spec.get("domain") or "").strip(),
    }
    doctype_candidates = resolve_record_doctype_candidates(message, infer_spec)
    typed = str(message or "").strip().lower()
    all_doctypes = load_submittable_doctypes()
    exact = [dt for dt in all_doctypes if str(dt or "").strip().lower() == typed]
    if exact:
        doctype_candidates = [str(exact[0] or "").strip()]
    if not doctype_candidates:
        return spec

    chosen = str(doctype_candidates[0] or "").strip()
    if len(doctype_candidates) > 1:
        domain_hint = str(active_topic.get("domain") or infer_spec.get("domain") or "").strip().lower()
        if domain_hint == "sales":
            for dt in doctype_candidates:
                if "sales" in str(dt or "").strip().lower():
                    chosen = str(dt or "").strip()
                    break
        elif domain_hint in {"purchasing", "purchase"}:
            for dt in doctype_candidates:
                if "purchase" in str(dt or "").strip().lower():
                    chosen = str(dt or "").strip()
                    break
    if not chosen:
        return spec

    out = dict(spec)
    out["intent"] = "READ"
    out["task_type"] = "detail"
    out["task_class"] = "list_latest_records"
    out["output_mode"] = "top_n"

    filters = dict(out.get("filters") or {}) if isinstance(out.get("filters"), dict) else {}
    filters["doctype"] = chosen
    out["filters"] = filters

    try:
        top_n = int(out.get("top_n") or active_topic.get("top_n") or 0)
    except Exception:
        top_n = 0
    if top_n <= 0:
        top_n = first_int_in_text(str((prev.get("turn_meta") or {}).get("message_preview") or ""))
    if top_n <= 0:
        top_n = 20
    out["top_n"] = max(1, min(top_n, 200))

    output_contract = dict(out.get("output_contract") or {}) if isinstance(out.get("output_contract"), dict) else {}
    output_contract["mode"] = "top_n"
    out["output_contract"] = output_contract

    if not str(out.get("subject") or "").strip():
        out["subject"] = str(active_topic.get("subject") or "invoices").strip()
    if not str(out.get("domain") or "").strip():
        out["domain"] = str(active_topic.get("domain") or infer_spec.get("domain") or "sales").strip()
    return out


def prepare_resume_from_pending(
    *,
    message: str,
    pending: Dict[str, Any],
    session_name: Optional[str],
    is_new_business_request_structured: Callable[[str, Optional[str]], bool],
    resolve_record_doctype_candidates: Callable[[str, Dict[str, Any]], List[str]],
    resolve_explicit_doctype_name: Callable[[str], str],
    load_submittable_doctypes: Callable[[], List[str]],
    default_clarification_question_fn: Callable[[str], str],
) -> Dict[str, Any]:
    raw_pending = pending if isinstance(pending, dict) else {}
    mode = str(raw_pending.get("mode") or "").strip().lower()
    base_question = str(raw_pending.get("base_question") or "").strip()
    if mode not in {"need_filters", "planner_clarify"}:
        return {"active": False}
    if not base_question:
        return {"active": False}

    options = [
        str(x).strip()
        for x in list(raw_pending.get("options") or raw_pending.get("clarification_options") or [])
        if str(x or "").strip()
    ]
    report_name = str(raw_pending.get("report_name") or "").strip()
    filters_so_far = dict(raw_pending.get("filters_so_far") or {}) if isinstance(raw_pending.get("filters_so_far"), dict) else {}
    spec_so_far = raw_pending.get("spec_so_far") if isinstance(raw_pending.get("spec_so_far"), dict) else {}
    pending_reason = str(raw_pending.get("clarification_reason") or "").strip().lower()
    target_filter_key = str(raw_pending.get("target_filter_key") or "").strip()
    raw_input = str(message or "").strip()
    new_request_decision: Optional[bool] = None

    def _plan_seed_from_pending_spec(*, include_filters: bool) -> Dict[str, Any]:
        seed: Dict[str, Any] = {"action": "run_report"}
        task_class = str(spec_so_far.get("task_class") or "").strip().lower()
        if task_class:
            seed["task_class"] = task_class
        try:
            top_n = int(spec_so_far.get("top_n") or 0)
        except Exception:
            top_n = 0
        if top_n > 0:
            seed["top_n"] = top_n
            seed["output_mode"] = "top_n"
        output_contract = spec_so_far.get("output_contract") if isinstance(spec_so_far.get("output_contract"), dict) else {}
        minimal_columns = [str(x).strip() for x in list(output_contract.get("minimal_columns") or []) if str(x or "").strip()]
        if minimal_columns:
            seed["minimal_columns"] = minimal_columns[:12]
        if include_filters and filters_so_far:
            seed["filters"] = dict(filters_so_far)
        return seed

    def _is_new_request() -> bool:
        nonlocal new_request_decision
        if new_request_decision is None:
            new_request_decision = is_new_business_request_structured(raw_input, session_name)
        return bool(new_request_decision)

    if mode == "planner_clarify":
        planner_options = options or ["Switch to compatible report", "Keep current scope"]
        option_actions = planner_option_actions(options=planner_options, pending=raw_pending)
        chosen = match_option_choice(raw_input, planner_options)
        if not chosen:
            if looks_like_scope_answer_text(raw_input):
                merged = f"{base_question}. {raw_input}".strip()
                seed = _plan_seed_from_pending_spec(include_filters=False)
                infer_spec: Dict[str, Any] = {
                    "subject": str(spec_so_far.get("subject") or "").strip(),
                    "metric": str(spec_so_far.get("metric") or "").strip(),
                    "filters": dict(filters_so_far),
                    "domain": str(spec_so_far.get("domain") or "").strip(),
                }
                doctype_candidates = resolve_record_doctype_candidates(raw_input, infer_spec)
                explicit_doctype = resolve_explicit_doctype_name(raw_input)
                if explicit_doctype:
                    all_doctypes = load_submittable_doctypes()
                    if explicit_doctype in all_doctypes:
                        doctype_candidates = [explicit_doctype]
                if not doctype_candidates:
                    pending_task_class = str(spec_so_far.get("task_class") or "").strip().lower()
                    is_record_type_followup = (
                        pending_task_class == "list_latest_records"
                        or ("invoice" in str(base_question or "").strip().lower())
                    )
                    if is_record_type_followup and explicit_doctype:
                        doctype_candidates = [explicit_doctype]
                synthetic_query = merged
                if len(doctype_candidates) == 1:
                    chosen_doctype = str(doctype_candidates[0] or "").strip()
                    seed_filters = dict(seed.get("filters") or {})
                    seed_filters["doctype"] = chosen_doctype
                    seed["filters"] = seed_filters
                    seed["task_class"] = "list_latest_records"
                    seed["output_mode"] = "top_n"
                    try:
                        top_n = int(spec_so_far.get("top_n") or 0)
                    except Exception:
                        top_n = 0
                    if top_n <= 0:
                        top_n = first_int_in_text(base_question)
                    if top_n > 0:
                        seed["top_n"] = max(1, min(top_n, 200))
                        synthetic_query = f"Show me the latest {seed['top_n']} {chosen_doctype}"
                    else:
                        synthetic_query = f"Show me the latest records for {chosen_doctype}"
                return {
                    "active": True,
                    "resume_message": synthetic_query,
                    "plan_seed": seed,
                    "clear_pending": True,
                    "source": "report_qa_start",
                }
            if pending_reason == "no_candidate":
                merged = f"{base_question}. {raw_input}".strip()
                return {
                    "active": True,
                    "resume_message": merged,
                    "plan_seed": _plan_seed_from_pending_spec(include_filters=False),
                    "clear_pending": True,
                    "source": "report_qa_start",
                }
            if _is_new_request():
                return {
                    "active": True,
                    "resume_message": raw_input,
                    "plan_seed": {"action": "run_report"},
                    "clear_pending": True,
                    "source": "report_qa_start",
                }
            merged = f"{base_question}. {raw_input}".strip()
            return {
                "active": True,
                "resume_message": merged,
                "plan_seed": _plan_seed_from_pending_spec(include_filters=False),
                "clear_pending": True,
                "source": "report_qa_start",
            }
        chosen_action = str(option_actions.get(normalize_option_label(chosen)) or "").strip().lower()
        if chosen_action == "keep_current":
            return {
                "active": False,
                "payload": {
                    "type": "text",
                    "text": default_clarification_question_fn("missing_required_filter_value"),
                    "_clear_pending_state": True,
                },
            }
        return {
            "active": True,
            "resume_message": base_question,
            "plan_seed": dict(_plan_seed_from_pending_spec(include_filters=True), report_name=report_name),
            "clear_pending": True,
            "source": "report_qa_start",
        }

    if mode == "need_filters":
        selected_value = ""
        if options:
            selected_value = match_option_choice(raw_input, options)
            if not selected_value:
                if _is_new_request():
                    return {
                        "active": True,
                        "resume_message": raw_input,
                        "plan_seed": {"action": "run_report"},
                        "clear_pending": True,
                        "source": "report_qa_start",
                    }
                text = default_clarification_question_fn("entity_ambiguous")
                return {
                    "active": False,
                    "payload": {
                        "type": "text",
                        "text": text,
                        "_pending_state": {
                            "mode": "need_filters",
                            "base_question": base_question,
                            "report_name": report_name,
                            "filters_so_far": filters_so_far,
                            "clarification_question": text,
                            "clarification_options": options,
                            "options": options,
                            "target_filter_key": target_filter_key,
                            "clarification_round": int(raw_pending.get("clarification_round") or 1),
                        },
                    },
                }
        else:
            if _is_new_request():
                return {
                    "active": True,
                    "resume_message": raw_input,
                    "plan_seed": {"action": "run_report"},
                    "clear_pending": True,
                    "source": "report_qa_start",
                }
            selected_value = raw_input

        if target_filter_key and selected_value:
            filters_so_far[target_filter_key] = selected_value
        elif selected_value:
            for key in list(filters_so_far.keys()):
                if str(key or "").strip():
                    filters_so_far[key] = selected_value
                    break

        return {
            "active": True,
            "resume_message": base_question,
            "plan_seed": {
                "action": "run_report",
                "report_name": report_name,
                "filters": filters_so_far,
            },
            "clear_pending": True,
            "source": "report_qa_start",
        }

    return {"active": False}
