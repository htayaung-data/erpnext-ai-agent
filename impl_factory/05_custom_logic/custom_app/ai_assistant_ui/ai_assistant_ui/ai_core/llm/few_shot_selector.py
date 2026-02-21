from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

_SELECTOR_VERSION = "few_shot_selector_v2026_02_21_s2_generic"

_STOP = {
    "the",
    "and",
    "for",
    "with",
    "this",
    "that",
    "from",
    "into",
    "show",
    "what",
    "are",
    "was",
    "were",
    "have",
    "has",
    "had",
    "you",
    "your",
    "our",
    "please",
}


def selector_version() -> str:
    return _SELECTOR_VERSION


def _tokenize(text: str) -> Set[str]:
    s = str(text or "").strip().lower()
    if not s:
        return set()
    words = re.findall(r"[a-z0-9_]+", s)
    return {w for w in words if len(w) >= 3 and w not in _STOP}


def _normalize_key(value: Any) -> str:
    return str(value or "").strip().lower()


def _extract_action_or_intent(example: Dict[str, Any]) -> str:
    out = example.get("out") if isinstance(example.get("out"), dict) else {}
    action = _normalize_key(out.get("action"))
    if action:
        return f"action:{action}"
    intent = _normalize_key(out.get("intent"))
    if intent:
        return f"intent:{intent}"
    return ""


def _example_text(example: Dict[str, Any]) -> str:
    inp = str(example.get("in") or "")
    out = example.get("out") if isinstance(example.get("out"), dict) else {}
    out_hint = " ".join(
        [
            str(out.get("action") or ""),
            str(out.get("report_name") or ""),
            str(out.get("intent") or ""),
            str(out.get("task_type") or ""),
            str(out.get("metric") or ""),
            " ".join([str(x) for x in list(out.get("group_by") or [])]),
            " ".join([str(k) for k in list((out.get("filters") or {}).keys())]),
        ]
    )
    return f"{inp} {out_hint}".strip()


def _query_text(*, user_message: str, recent_messages: Optional[List[Dict[str, str]]]) -> str:
    bits = [str(user_message or "")]
    for msg in list(recent_messages or [])[-4:]:
        if _normalize_key(msg.get("role")) != "user":
            continue
        bits.append(str(msg.get("content") or ""))
    return " ".join([x for x in bits if x]).strip().lower()


def _score_example(*, query_tokens: Set[str], example: Dict[str, Any], recency_boost: float) -> Tuple[float, int]:
    ex_text = _example_text(example)
    ex_tokens = _tokenize(ex_text)

    overlap = len(query_tokens & ex_tokens)
    union = len(query_tokens | ex_tokens) or 1
    jaccard = overlap / union

    # Stable lexical score without phrase bonuses.
    score = (jaccard * 100.0) + (min(overlap, 8) * 1.5) + recency_boost
    return score, overlap


def select_few_shots(
    *,
    examples: List[Dict[str, Any]],
    user_message: str,
    recent_messages: Optional[List[Dict[str, str]]] = None,
    limit: int = 6,
) -> List[Dict[str, Any]]:
    rows = [e for e in (examples or []) if isinstance(e, dict) and str(e.get("in") or "").strip()]
    if not rows:
        return []

    n = max(1, int(limit))
    q_text = _query_text(user_message=user_message, recent_messages=recent_messages)
    q_tokens = _tokenize(q_text)

    scored: List[Tuple[float, int, int, Dict[str, Any]]] = []
    total = len(rows)
    for idx, ex in enumerate(rows):
        # Prefer newer examples when lexical similarity ties.
        recency = ((idx + 1) / float(max(1, total))) * 0.75
        score, overlap = _score_example(query_tokens=q_tokens, example=ex, recency_boost=recency)
        scored.append((score, overlap, idx, ex))

    scored.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)

    out: List[Dict[str, Any]] = []
    seen_inputs: Set[str] = set()
    seen_action_intent: Set[str] = set()

    for score, _, _, ex in scored:
        key = _normalize_key(ex.get("in"))
        if not key or key in seen_inputs:
            continue

        ai = _extract_action_or_intent(ex)
        # Keep response-shape diversity when enough candidates exist.
        if ai and ai in seen_action_intent and len(out) >= 3 and score < 30.0:
            continue

        out.append(ex)
        seen_inputs.add(key)
        if ai:
            seen_action_intent.add(ai)
        if len(out) >= n:
            break

    if len(out) < min(3, n):
        for ex in rows:
            key = _normalize_key(ex.get("in"))
            if key in seen_inputs:
                continue
            out.append(ex)
            seen_inputs.add(key)
            if len(out) >= min(3, n):
                break

    return out[:n]
