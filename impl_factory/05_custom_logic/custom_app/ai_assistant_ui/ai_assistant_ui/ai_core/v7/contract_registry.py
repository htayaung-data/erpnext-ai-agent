from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Set


_DEFAULT_SPEC_CONTRACT: Dict[str, Any] = {
    "version": "fallback",
    "allowed": {
        "intents": ["READ", "TRANSFORM_LAST", "TUTOR", "WRITE_DRAFT", "WRITE_CONFIRM", "EXPORT"],
        "task_types": ["kpi", "ranking", "trend", "detail"],
        "task_classes": ["analytical_read", "list_latest_records", "detail_projection", "transform_followup"],
        "aggregations": ["sum", "count", "avg", "none"],
        "time_modes": ["as_of", "range", "relative", "none"],
        "output_modes": ["kpi", "top_n", "detail"],
        "domains": ["unknown", "sales", "finance", "inventory", "purchasing", "operations", "hr", "cross_functional"],
    },
    "canonical_dimensions": ["customer", "supplier", "item", "warehouse", "company", "territory"],
    "dimension_domain_map": {
        "customer": "sales",
        "supplier": "purchasing",
        "warehouse": "inventory",
        "company": "finance",
    },
}

_DEFAULT_CLARIFICATION_CONTRACT: Dict[str, Any] = {
    "version": "fallback",
    "allowed_blocker_reasons": [
        "missing_required_filter_value",
        "hard_constraint_not_supported",
        "entity_no_match",
        "entity_ambiguous",
        "no_candidate",
        "low_confidence_candidate",
        "resolver_pipeline_error",
    ],
    "default_questions_by_reason": {
        "missing_required_filter_value": "Which required filter value should I use (for example company, warehouse, customer, or supplier)?",
        "hard_constraint_not_supported": "I couldn't satisfy all requested constraints in one report. Should I switch to a compatible report or keep current scope?",
        "entity_no_match": "I couldn't find a matching value for that filter. Which exact value should I use?",
        "entity_ambiguous": "I found multiple matches for that filter. Which one should I use?",
    },
    "fallback_question": "Please provide one concrete missing detail so I can run the correct report.",
}


def _contracts_dir() -> Path:
    return Path(__file__).resolve().parent / "contracts_data"


def _repo_root() -> Path:
    cur = Path(__file__).resolve()
    for p in [cur] + list(cur.parents):
        if (p / "impl_factory").is_dir():
            return p
    return cur.parent


def _default_override_path() -> Path:
    return _repo_root() / "impl_factory/04_automation/capability_v7/latest_contract_overrides.json"


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(dict(out.get(k) or {}), v)
        else:
            out[k] = v
    return out


@lru_cache(maxsize=1)
def get_contract_overrides() -> Dict[str, Any]:
    env_path = str(os.environ.get("AI_ASSISTANT_V7_CONTRACT_OVERRIDE") or "").strip()
    if env_path:
        obj = _read_json(Path(env_path))
        if obj:
            return obj
    default_path = _default_override_path()
    if default_path.exists():
        obj = _read_json(default_path)
        if obj:
            return obj
    return {}


@lru_cache(maxsize=1)
def get_spec_contract() -> Dict[str, Any]:
    path = _contracts_dir() / "spec_contract_v1.json"
    loaded = _read_json(path)
    out = _deep_merge(dict(_DEFAULT_SPEC_CONTRACT), loaded if loaded else {})
    overrides = get_contract_overrides()
    spec_override = overrides.get("spec_contract") if isinstance(overrides.get("spec_contract"), dict) else {}
    return _deep_merge(out, spec_override)


@lru_cache(maxsize=1)
def get_clarification_contract() -> Dict[str, Any]:
    path = _contracts_dir() / "clarification_contract_v1.json"
    loaded = _read_json(path)
    out = _deep_merge(dict(_DEFAULT_CLARIFICATION_CONTRACT), loaded if loaded else {})
    overrides = get_contract_overrides()
    clar_override = overrides.get("clarification_contract") if isinstance(overrides.get("clarification_contract"), dict) else {}
    return _deep_merge(out, clar_override)


def allowed_spec_values(key: str) -> Set[str]:
    allowed = get_spec_contract().get("allowed") if isinstance(get_spec_contract().get("allowed"), dict) else {}
    vals = allowed.get(key) if isinstance(allowed, dict) else []
    return {str(v).strip().lower() for v in list(vals or []) if str(v).strip()}


def canonical_dimensions() -> Set[str]:
    vals = get_spec_contract().get("canonical_dimensions")
    return {str(v).strip().lower() for v in list(vals or []) if str(v).strip()}


def domain_from_dimension(dim: str) -> str:
    mapping = get_spec_contract().get("dimension_domain_map")
    mm = mapping if isinstance(mapping, dict) else {}
    return str(mm.get(str(dim or "").strip().lower()) or "").strip().lower()


def allowed_blocker_reasons() -> Set[str]:
    vals = get_clarification_contract().get("allowed_blocker_reasons")
    return {str(v).strip().lower() for v in list(vals or []) if str(v).strip()}


def default_clarification_question(reason: str) -> str:
    c = get_clarification_contract()
    by_reason = c.get("default_questions_by_reason") if isinstance(c.get("default_questions_by_reason"), dict) else {}
    q = str(by_reason.get(str(reason or "").strip().lower()) or "").strip()
    if q:
        return q
    return str(c.get("fallback_question") or "").strip()


def clarification_question_for_filter_kind(kind: str) -> str:
    c = get_clarification_contract()
    by_kind = c.get("questions_by_filter_kind") if isinstance(c.get("questions_by_filter_kind"), dict) else {}
    q = str(by_kind.get(str(kind or "").strip().lower()) or "").strip()
    if q:
        return q
    human = re.sub(r"\s+", " ", re.sub(r"[_\-]+", " ", str(kind or "").strip().lower())).strip()
    if human:
        return f"Which value should I use for {human}?"
    return str(c.get("fallback_question") or "").strip()


def clear_contract_cache() -> None:
    get_contract_overrides.cache_clear()
    get_spec_contract.cache_clear()
    get_clarification_contract.cache_clear()
