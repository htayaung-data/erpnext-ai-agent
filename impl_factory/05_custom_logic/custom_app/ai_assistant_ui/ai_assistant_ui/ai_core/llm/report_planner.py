from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

try:
    import frappe  # type: ignore
except Exception:  # pragma: no cover - local unit tests without Frappe runtime
    frappe = None

from ai_assistant_ui.ai_core.llm.openai_client import chat_completions_json
from ai_assistant_ui.ai_core.llm.few_shot_examples import (
    REPORT_PLANNER_FEW_SHOTS,
    REPORT_PLANNER_FEW_SHOTS_VERSION,
    BUSINESS_REQUEST_SPEC_FEW_SHOTS,
    BUSINESS_REQUEST_SPEC_FEW_SHOTS_VERSION,
)
from ai_assistant_ui.ai_core.llm.few_shot_selector import select_few_shots, selector_version

_PLAN_KEYS = {
    'action',
    'report_name',
    'filters',
    'export',
    'needs_clarification',
    'ask',
    'filters_so_far',
    'operation',
    'params',
    'doctype',
    'payload',
    'confirmation_text',
    'post_transform',
}

_ALLOWED_ACTIONS = ('run_report', 'clarify', 'transform_last', 'write_draft')
_ALLOWED_POST_OPS = ('total', 'sum', 'top', 'top_n', 'sort', 'filter', 'summary')
_ALLOWED_TRANSFORM_OPS = ('total', 'sum', 'top', 'top_n', 'sort', 'filter', 'summary')
_ALLOWED_SPEC_INTENTS = ('READ', 'TRANSFORM', 'TUTOR', 'WRITE_DRAFT', 'WRITE_CONFIRM', 'EXPORT')
_ALLOWED_SPEC_TASK_TYPES = ('kpi', 'ranking', 'trend', 'detail')
_ALLOWED_SPEC_AGG = ('sum', 'count', 'avg', 'none')
_ALLOWED_SPEC_TIME_MODES = ('as_of', 'range', 'relative', 'none')
_ALLOWED_SPEC_OUTPUT_MODES = ('kpi', 'top_n', 'detail')
_PLAN_PROMPT_VERSION = "planner_prompt_v2026_02_19_now1"
_SPEC_PROMPT_VERSION = "spec_prompt_v2026_02_19_now1"
_FEW_SHOT_LIMIT = 6


def _clip(s: str, n: int = 1200) -> str:
    s = (s or '').strip()
    return s if len(s) <= n else (s[:n] + '…')


def _safe_json(x: Any) -> str:
    try:
        return json.dumps(x, ensure_ascii=False, default=str)
    except Exception:
        return json.dumps(str(x), ensure_ascii=False)


def _preferred_model(slot: str) -> Optional[str]:
    """
    Optional strong-model routing by slot.
    Falls back to default openai_model when slot keys are unset.
    """
    if frappe is None:
        return None
    try:
        conf = getattr(frappe, "conf", None) or {}
    except Exception:
        conf = {}
    slot_lc = str(slot or "").strip().lower()
    if slot_lc == "spec":
        keys = ("openai_model_spec", "openai_model_planner", "openai_model_strong")
    elif slot_lc == "plan":
        keys = ("openai_model_planner", "openai_model_strong")
    else:
        keys = ("openai_model_strong",)
    for key in keys:
        val = str(conf.get(key) or "").strip()
        if val:
            return val
    return None


def _call_validated_json_once_retry(
    *,
    system: str,
    user_payload: Dict[str, Any],
    validate_fn,
    temperature: float,
    max_tokens: int,
    timeout: int,
    model: Optional[str] = None,
) -> tuple[Dict[str, Any], int]:
    """
    Strict schema guard with one bounded retry:
    if first LLM output is invalid/unparseable, try exactly once more.
    """
    last_err: Optional[Exception] = None
    user_text = _safe_json(user_payload)
    for attempt in (1, 2):
        try:
            obj = chat_completions_json(
                system=system,
                user=user_text,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
                model=model,
            )
            return validate_fn(obj), attempt
        except Exception as ex:
            last_err = ex
    if last_err is not None:
        raise last_err
    raise RuntimeError("LLM validated call failed without exception.")


def _validate_plan(obj: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(obj, dict):
        raise ValueError('Planner output must be a JSON object.')

    action = obj.get('action')
    if action not in _ALLOWED_ACTIONS:
        raise ValueError(f'Invalid action: {action}')

    pruned: Dict[str, Any] = {k: obj.get(k) for k in obj.keys() if k in _PLAN_KEYS}
    pruned['action'] = action
    if "export" in pruned:
        pruned["export"] = bool(pruned.get("export"))

    # Validate post_transform if provided
    pt = pruned.get('post_transform')
    if pt is not None:
        if not isinstance(pt, dict):
            pruned.pop('post_transform', None)
        else:
            op = str(pt.get('operation') or '').strip().lower()
            if op not in _ALLOWED_POST_OPS:
                pruned.pop('post_transform', None)
            else:
                params = pt.get('params') if isinstance(pt.get('params'), dict) else {}
                pruned['post_transform'] = {'operation': op, 'params': params}

    if action == "run_report":
        report_name = str(pruned.get("report_name") or "").strip()
        if not report_name:
            raise ValueError("run_report requires non-empty report_name")
        pruned["report_name"] = report_name
        if not isinstance(pruned.get("filters"), dict):
            pruned["filters"] = {}
        pruned["needs_clarification"] = False
        return pruned

    if action == "clarify":
        ask = pruned.get("ask") if isinstance(pruned.get("ask"), dict) else {}
        q = str(ask.get("question") or "").strip()
        if not q:
            q = "Could you clarify what ERP data you want, and include date/company/warehouse if relevant?"
        pruned["ask"] = {"question": q}
        pruned["report_name"] = str(pruned.get("report_name") or "").strip()
        if not isinstance(pruned.get("filters_so_far"), dict):
            pruned["filters_so_far"] = {}
        pruned["needs_clarification"] = True
        return pruned

    if action == "transform_last":
        op = str(pruned.get("operation") or "").strip().lower()
        if op not in _ALLOWED_TRANSFORM_OPS:
            raise ValueError(f"transform_last operation not supported: {op}")
        pruned["operation"] = op
        if not isinstance(pruned.get("params"), dict):
            pruned["params"] = {}
        return pruned

    # write_draft
    doctype = str(pruned.get("doctype") or "").strip()
    operation = str(pruned.get("operation") or "").strip().lower()
    if not doctype or operation not in ("create", "update", "delete", "submit", "cancel"):
        raise ValueError("write_draft requires valid doctype and operation")
    if not isinstance(pruned.get("payload"), dict):
        pruned["payload"] = {}
    pruned["doctype"] = doctype
    pruned["operation"] = operation
    pruned["confirmation_text"] = str(pruned.get("confirmation_text") or "").strip()
    return pruned


def _fallback_clarify_plan() -> Dict[str, Any]:
    return {
        "action": "clarify",
        "report_name": "",
        "filters_so_far": {},
        "ask": {
            "question": "Could you clarify what ERP data you want, and include date/company/warehouse if relevant?",
        },
        "needs_clarification": True,
        "export": False,
    }


def _default_business_request_spec() -> Dict[str, Any]:
    return {
        "intent": "READ",
        "task_type": "detail",
        "domain": "unknown",
        "subject": "",
        "metric": "",
        "dimensions": [],
        "aggregation": "none",
        "group_by": [],
        "time_scope": {"mode": "none", "value": ""},
        "filters": {},
        "top_n": 0,
        "output_contract": {"mode": "detail", "minimal_columns": []},
        "ambiguities": [],
        "needs_clarification": False,
        "clarification_question": "",
        "confidence": 0.0,
    }


def _safe_list_str(x: Any, *, limit: int = 12) -> List[str]:
    if not isinstance(x, list):
        return []
    out: List[str] = []
    for v in x[: max(0, limit)]:
        s = str(v or "").strip()
        if s:
            out.append(s)
    return out


def _validate_business_request_spec(obj: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(obj, dict):
        raise ValueError("Business request spec must be a JSON object.")

    out = _default_business_request_spec()

    intent = str(obj.get("intent") or "").strip().upper()
    if intent in _ALLOWED_SPEC_INTENTS:
        out["intent"] = intent

    task_type = str(obj.get("task_type") or "").strip().lower()
    if task_type in _ALLOWED_SPEC_TASK_TYPES:
        out["task_type"] = task_type

    aggregation = str(obj.get("aggregation") or "").strip().lower()
    if aggregation in _ALLOWED_SPEC_AGG:
        out["aggregation"] = aggregation

    subject = str(obj.get("subject") or "").strip()
    metric = str(obj.get("metric") or "").strip()
    domain = str(obj.get("domain") or "").strip().lower()
    if subject:
        out["subject"] = subject
    if metric:
        out["metric"] = metric
    if domain:
        out["domain"] = domain

    out["group_by"] = _safe_list_str(obj.get("group_by"), limit=8)
    out["dimensions"] = _safe_list_str(obj.get("dimensions"), limit=8)

    time_scope = obj.get("time_scope") if isinstance(obj.get("time_scope"), dict) else {}
    mode = str(time_scope.get("mode") or "").strip().lower()
    value = str(time_scope.get("value") or "").strip()
    if mode in _ALLOWED_SPEC_TIME_MODES:
        out["time_scope"] = {"mode": mode, "value": value}

    filters = obj.get("filters")
    if isinstance(filters, dict):
        out["filters"] = filters

    top_n_raw = obj.get("top_n")
    try:
        top_n = int(top_n_raw)
    except Exception:
        top_n = 0
    out["top_n"] = max(0, min(top_n, 200))

    output_contract = obj.get("output_contract") if isinstance(obj.get("output_contract"), dict) else {}
    out_mode = str(output_contract.get("mode") or "").strip().lower()
    if out_mode in _ALLOWED_SPEC_OUTPUT_MODES:
        out["output_contract"]["mode"] = out_mode
    out["output_contract"]["minimal_columns"] = _safe_list_str(output_contract.get("minimal_columns"), limit=8)

    out["ambiguities"] = _safe_list_str(obj.get("ambiguities"), limit=8)
    out["needs_clarification"] = bool(obj.get("needs_clarification"))
    out["clarification_question"] = str(obj.get("clarification_question") or "").strip()[:280]
    try:
        out["confidence"] = max(0.0, min(float(obj.get("confidence") or 0.0), 1.0))
    except Exception:
        out["confidence"] = 0.0

    if out["needs_clarification"] and not out["clarification_question"]:
        out["clarification_question"] = "Could you clarify the missing business detail (for example company, warehouse, date, or target field)?"

    return out


def _fallback_business_request_spec(*, user_message: str, plan: Dict[str, Any], has_last_result: bool) -> Dict[str, Any]:
    spec = _default_business_request_spec()
    action = str((plan or {}).get("action") or "").strip().lower()

    if action == "transform_last":
        spec["intent"] = "TRANSFORM"
        spec["task_type"] = "detail"
        op = str((plan.get("operation") or "")).strip().lower()
        params = plan.get("params") if isinstance(plan.get("params"), dict) else {}
        spec["metric"] = str(params.get("column") or params.get("column_hint") or "").strip()
        if op in ("top", "top_n"):
            spec["task_type"] = "ranking"
            spec["output_contract"]["mode"] = "top_n"
            try:
                spec["top_n"] = max(0, min(int(params.get("n") or params.get("limit") or 0), 200))
            except Exception:
                spec["top_n"] = 0
        elif op in ("total", "sum"):
            spec["task_type"] = "kpi"
            spec["output_contract"]["mode"] = "kpi"
            spec["aggregation"] = "sum"
    elif action == "write_draft":
        spec["intent"] = "WRITE_DRAFT"
    elif action == "clarify":
        spec["intent"] = "READ"
        spec["needs_clarification"] = True
        ask = plan.get("ask") if isinstance(plan.get("ask"), dict) else {}
        spec["clarification_question"] = str(ask.get("question") or "").strip()[:280]
    else:
        spec["intent"] = "READ"
        post = plan.get("post_transform") if isinstance(plan.get("post_transform"), dict) else {}
        post_op = str(post.get("operation") or "").strip().lower()
        post_params = post.get("params") if isinstance(post.get("params"), dict) else {}
        if post_op in ("top", "top_n"):
            spec["task_type"] = "ranking"
            spec["output_contract"]["mode"] = "top_n"
            try:
                spec["top_n"] = max(0, min(int(post_params.get("n") or post_params.get("limit") or 0), 200))
            except Exception:
                spec["top_n"] = 0
            spec["metric"] = str(post_params.get("column") or post_params.get("column_hint") or "").strip()
        elif post_op in ("total", "sum"):
            spec["task_type"] = "kpi"
            spec["output_contract"]["mode"] = "kpi"
            spec["aggregation"] = "sum"
            spec["metric"] = str(post_params.get("column") or post_params.get("column_hint") or "").strip()

        report_name = str(plan.get("report_name") or "").strip()
        if report_name:
            spec["subject"] = report_name
        filters = plan.get("filters") if isinstance(plan.get("filters"), dict) else {}
        spec["filters"] = filters

    if bool((plan or {}).get("export")):
        spec["intent"] = "EXPORT"

    # Keep fallback neutral; context carry-forward is handled in v7 memory/state module.
    return spec


def choose_business_request_spec(
    *,
    user_message: str,
    recent_messages: List[Dict[str, str]],
    planner_plan: Dict[str, Any],
    has_last_result: bool,
    today_iso: str,
    time_context: Dict[str, Any],
    last_result_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Produce semantic business request spec (LLM-guided + deterministic validation).
    """
    system = "\n".join(
        [
            "You are an ERP business request normalizer.",
            "Output ONLY one JSON object. No markdown. No extra commentary.",
            "Never output ERP facts or numbers from memory.",
            "Infer semantic request intent and desired output shape.",
            "If key semantics are ambiguous, set needs_clarification=true and add one clarification_question.",
            "Use planner_plan as current action context, but normalize business semantics independently.",
        ]
    )

    selected_few_shot = select_few_shots(
        examples=BUSINESS_REQUEST_SPEC_FEW_SHOTS,
        user_message=user_message,
        recent_messages=recent_messages,
        limit=_FEW_SHOT_LIMIT,
    )

    payload = {
        "user_message": _clip(user_message, 1200),
        "recent_messages": (recent_messages or [])[-10:],
        "planner_plan": planner_plan or {},
        "has_last_result": bool(has_last_result),
        "today_iso": today_iso,
        "time_context": time_context,
        "last_result_meta": last_result_meta or None,
        "few_shot_examples": selected_few_shot,
        "output_schema_example": {
            "intent": "READ",
            "task_type": "ranking",
            "domain": "sales",
            "subject": "products",
            "metric": "sold quantity",
            "dimensions": ["item"],
            "aggregation": "sum",
            "group_by": ["item"],
            "time_scope": {"mode": "relative", "value": "last_month"},
            "filters": {},
            "top_n": 5,
            "output_contract": {"mode": "top_n", "minimal_columns": ["item", "sold quantity"]},
            "ambiguities": [],
            "needs_clarification": False,
            "clarification_question": "",
            "confidence": 0.9,
        },
    }

    try:
        spec, attempt_count = _call_validated_json_once_retry(
            system=system,
            user_payload=payload,
            validate_fn=_validate_business_request_spec,
            temperature=0.0,
            max_tokens=500,
            timeout=35,
            model=_preferred_model("spec"),
        )
        spec["llm_meta"] = {
            "prompt_version": _SPEC_PROMPT_VERSION,
            "few_shot_version": f"{BUSINESS_REQUEST_SPEC_FEW_SHOTS_VERSION}+{selector_version()}",
            "few_shot_count": len(selected_few_shot),
            "attempt_count": attempt_count,
            "fallback_used": False,
        }
        return spec
    except Exception:
        fallback = _fallback_business_request_spec(
            user_message=user_message,
            plan=planner_plan or {},
            has_last_result=has_last_result,
        )
        fallback["llm_meta"] = {
            "prompt_version": _SPEC_PROMPT_VERSION,
            "few_shot_version": f"{BUSINESS_REQUEST_SPEC_FEW_SHOTS_VERSION}+{selector_version()}",
            "few_shot_count": len(selected_few_shot),
            "attempt_count": 2,
            "fallback_used": True,
        }
        return fallback


def choose_candidate_report(
    *,
    user_message: str,
    business_spec: Dict[str, Any],
    candidate_reports: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Select exactly one report from a feasible candidate set.
    The selector must only choose from provided candidates.
    """
    candidates: List[Dict[str, Any]] = []
    allowed_names = set()
    for row in list(candidate_reports or [])[:20]:
        if not isinstance(row, dict):
            continue
        name = str(row.get("report_name") or row.get("name") or "").strip()
        if not name:
            continue
        allowed_names.add(name)
        candidates.append(
            {
                "report_name": name,
                "module": row.get("module") or row.get("report_family"),
                "report_type": row.get("report_type"),
                "required_filter_names": list(row.get("required_filter_names") or []),
                "required_filter_kinds": list(row.get("required_filter_kinds") or []),
                "supported_filter_kinds": list(row.get("supported_filter_kinds") or []),
                "domain_hints": list(row.get("domain_hints") or row.get("domain_tags") or []),
                "dimension_hints": list(row.get("dimension_hints") or row.get("dimension_tags") or []),
            }
        )

    if not candidates:
        return {"selected_report": "", "confidence": 0.0, "reason": "no_candidates"}

    system = "\n".join(
        [
            "You are an ERP report candidate selector.",
            "Output ONLY one JSON object.",
            "Select exactly one report_name from the provided candidate list.",
            "Never invent report names outside the candidate list.",
            "Use user request semantics + business spec + candidate metadata.",
        ]
    )
    payload = {
        "user_message": _clip(user_message, 1200),
        "business_spec": business_spec if isinstance(business_spec, dict) else {},
        "candidates": candidates,
        "output_schema_example": {
            "selected_report": candidates[0]["report_name"],
            "confidence": 0.8,
            "reason": "best semantic fit among feasible candidates",
        },
    }

    def _validate(obj: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(obj, dict):
            raise ValueError("candidate selector output must be JSON object")
        selected = str(obj.get("selected_report") or "").strip()
        if selected and selected not in allowed_names:
            raise ValueError("selected_report must be one of candidate reports")
        try:
            conf = float(obj.get("confidence") or 0.0)
        except Exception:
            conf = 0.0
        return {
            "selected_report": selected,
            "confidence": max(0.0, min(conf, 1.0)),
            "reason": str(obj.get("reason") or "").strip()[:240],
        }

    try:
        selected, _ = _call_validated_json_once_retry(
            system=system,
            user_payload=payload,
            validate_fn=_validate,
            temperature=0.0,
            max_tokens=220,
            timeout=30,
            model=_preferred_model("plan"),
        )
        if str(selected.get("selected_report") or "").strip():
            return selected
    except Exception:
        pass

    return {
        "selected_report": str(candidates[0].get("report_name") or ""),
        "confidence": 0.0,
        "reason": "fallback_first_candidate",
    }


def choose_plan(
    *,
    user_message: str,
    recent_messages: List[Dict[str, str]],
    reports: List[Dict[str, Any]],
    requirements_by_report: Dict[str, Any],
    has_last_result: bool,
    today_iso: str,
    time_context: Dict[str, Any],
    last_result_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Planner only: chooses report + filters OR one clarification question OR transform_last.
    No ERP facts. Output ONLY one JSON object.
    """

    report_brief = [
        {'name': r.get('name'), 'module': r.get('module'), 'report_type': r.get('report_type')}
        for r in (reports or [])
        if isinstance(r, dict) and r.get('name')
    ][:120]

    req_brief: Dict[str, Any] = {}
    for k, v in (requirements_by_report or {}).items():
        try:
            if isinstance(v, dict):
                req_brief[k] = {
                    'required_filter_names': v.get('required_filter_names'),
                    'filters_definition': v.get('filters_definition'),
                }
            else:
                req_brief[k] = {
                    'required_filter_names': getattr(v, 'required_filter_names', None),
                    'filters_definition': getattr(v, 'filters_definition', None),
                }
        except Exception:
            continue

    system_lines = [
        'You are an ERPNext assistant planner.',
        'Output ONLY one JSON object. No markdown. No extra keys.',
        '',
        'You NEVER output ERP data/facts. You ONLY decide what to do next.',
        '',
        'Allowed actions:',
        '- run_report: pick an existing report + provide ERP-safe filters.',
        '- clarify: ask ONE question to obtain missing/ambiguous required input.',
        '- transform_last: ONLY if user clearly refers to the LAST RESULT and operation is one of total/sum/top/top_n/sort/filter/summary.',
        '- write_draft: draft-only for create/update/delete/workflow, never execute.',
        '',
        'Hard rules:',
        '- Ask ONLY ONE question when clarifying.',
        '- Date values MUST be ISO strings YYYY-MM-DD (use today_iso/time_context provided). NEVER output literal "today"/"last month".',
        '- Set export=true ONLY if user explicitly asks download/csv/xlsx/excel.',
        '- If user asks for a report AND also asks for an operation (total/top/sort/filter), prefer:',
        '  action=run_report WITH post_transform so it completes in one turn.',
        '- Use transform_last ONLY when user clearly refers to the previous result (e.g., "total that", "sum outstanding").',
        '- Output must be valid JSON.',
    ]
    system = '\n'.join(system_lines)

    few_shot = select_few_shots(
        examples=REPORT_PLANNER_FEW_SHOTS,
        user_message=user_message,
        recent_messages=recent_messages,
        limit=_FEW_SHOT_LIMIT,
    )

    user = {
        'user_message': _clip(user_message, 1200),
        'recent_messages': recent_messages[-10:],
        'has_last_result': bool(has_last_result),
        'today_iso': today_iso,
        'time_context': time_context,
        'last_result_meta': last_result_meta or None,
        'candidate_reports': report_brief,
        'report_requirements': req_brief,
        'few_shot_examples': few_shot,
        'output_schema_examples': {
            'run_report': {
                'action': 'run_report',
                'report_name': 'Accounts Receivable Summary',
                'filters': {'report_date': today_iso},
                'export': False,
                'needs_clarification': False,
                'post_transform': {'operation': 'total', 'params': {'column_hint': 'Outstanding Amount'}},
            },
            'clarify': {
                'action': 'clarify',
                'report_name': 'Stock Balance',
                'filters_so_far': {'company': 'X'},
                'ask': {'question': 'Which warehouse should I use?'},
                'needs_clarification': True,
            },
            'transform_last': {'action': 'transform_last', 'operation': 'total', 'params': {'column_hint': 'Outstanding Amount'}},
            'write_draft': {
                'action': 'write_draft',
                'doctype': 'Sales Invoice',
                'operation': 'create',
                'payload': {'customer': '...'},
                'confirmation_text': 'Create a Sales Invoice for ...?',
            },
        },
    }

    try:
        plan, attempt_count = _call_validated_json_once_retry(
            system=system,
            user_payload=user,
            validate_fn=_validate_plan,
            temperature=0.0,
            max_tokens=900,
            timeout=45,
            model=_preferred_model("plan"),
        )
        plan["llm_meta"] = {
            "prompt_version": _PLAN_PROMPT_VERSION,
            "few_shot_version": f"{REPORT_PLANNER_FEW_SHOTS_VERSION}+{selector_version()}",
            "few_shot_count": len(few_shot),
            "attempt_count": attempt_count,
            "fallback_used": False,
        }
        return plan
    except Exception:
        fallback = _fallback_clarify_plan()
        fallback["llm_meta"] = {
            "prompt_version": _PLAN_PROMPT_VERSION,
            "few_shot_version": f"{REPORT_PLANNER_FEW_SHOTS_VERSION}+{selector_version()}",
            "few_shot_count": len(few_shot),
            "attempt_count": 2,
            "fallback_used": True,
        }
        return fallback


def choose_pending_mode(
    *,
    user_message: str,
    pending_state: Dict[str, Any],
    recent_messages: List[Dict[str, str]],
) -> str:
    """
    Decide whether current user message continues pending clarification
    or starts a new request/topic.
    Returns: "continue_pending" or "start_new".
    """
    system = "\n".join(
        [
            "You are a conversation flow controller for ERP assistant.",
            "Output ONLY one JSON object with key: mode.",
            "mode must be exactly one of: continue_pending, start_new.",
            "Use continue_pending only when user is clearly answering the pending question.",
            "Use start_new when user changed topic, asks a new request, or overrides direction.",
            "If uncertain, prefer start_new.",
        ]
    )

    few_shot = [
        {
            "pending": {"mode": "need_filters", "asked": "warehouse"},
            "in": "Main Warehouse",
            "out": {"mode": "continue_pending"},
        },
        {
            "pending": {"mode": "need_filters", "asked": "company"},
            "in": "Show AR aging as of today",
            "out": {"mode": "start_new"},
        },
        {
            "pending": {"mode": "need_filters", "asked": "from_date"},
            "in": "Cancel that. Show this month sales by customer.",
            "out": {"mode": "start_new"},
        },
    ]

    payload = {
        "user_message": _clip(user_message, 800),
        "pending_state": pending_state or {},
        "recent_messages": (recent_messages or [])[-10:],
        "few_shot_examples": few_shot,
        "output_schema_example": {"mode": "continue_pending"},
    }

    try:
        obj = chat_completions_json(
            system=system,
            user=_safe_json(payload),
            temperature=0.0,
            max_tokens=120,
            timeout=25,
        )
        mode = str((obj or {}).get("mode") or "").strip().lower()
        if mode in ("continue_pending", "start_new"):
            return mode
    except Exception:
        pass

    # Safety fallback: short direct replies usually continue pending; otherwise start new.
    word_count = len([w for w in (user_message or "").strip().split() if w])
    return "continue_pending" if 0 < word_count <= 4 else "start_new"
