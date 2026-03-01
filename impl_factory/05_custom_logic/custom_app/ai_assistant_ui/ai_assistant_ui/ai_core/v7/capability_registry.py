from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List


def _repo_root() -> Path:
    cur = Path(__file__).resolve()
    for p in [cur] + list(cur.parents):
        if (p / "impl_factory").is_dir():
            return p
    return cur.parent


def _overrides_path() -> Path:
    local = Path(__file__).resolve().parent / "contracts_data" / "capability_registry_overrides_v1.json"
    if local.exists():
        return local
    return _repo_root() / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/capability_registry_overrides_v1.json"


def _merge_unique_list(base: List[Any], extra: List[Any]) -> List[Any]:
    out: List[Any] = []
    seen = set()
    for source in (list(base or []), list(extra or [])):
        for value in source:
            key = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
            if key in seen:
                continue
            seen.add(key)
            out.append(value)
    return out


def _merge_dict(base: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base or {})
    for key, value in (extra or {}).items():
        current = out.get(key)
        if isinstance(current, list) and isinstance(value, list):
            out[key] = _merge_unique_list(current, value)
            continue
        if isinstance(current, dict) and isinstance(value, dict):
            out[key] = _merge_dict(current, value)
            continue
        out[key] = value
    return out


@lru_cache(maxsize=1)
def _load_registry_overrides() -> Dict[str, Any]:
    path = _overrides_path()
    if not path.exists():
        return {}
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def clear_registry_override_cache() -> None:
    _load_registry_overrides.cache_clear()


def report_override_by_name(report_name: str) -> Dict[str, Any]:
    name = str(report_name or "").strip()
    if not name:
        return {}
    overrides = _load_registry_overrides()
    reports_by_name = overrides.get("reports_by_name") if isinstance(overrides.get("reports_by_name"), dict) else {}
    row = reports_by_name.get(name)
    return dict(row) if isinstance(row, dict) else {}


def report_semantics_contract(report_name: str) -> Dict[str, Any]:
    row = report_override_by_name(report_name)
    semantics = row.get("semantics") if isinstance(row.get("semantics"), dict) else {}
    presentation = row.get("presentation") if isinstance(row.get("presentation"), dict) else {}
    return {
        "semantics": dict(semantics),
        "presentation": dict(presentation),
    }


def apply_registry_overrides(cap: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply versioned capability metadata overrides from governed JSON.
    Runtime stays generic; semantic corrections live in auditable data.
    """
    out = dict(cap or {})
    report_name = str(out.get("report_name") or out.get("name") or "").strip()
    if not report_name:
        return out

    overrides = _load_registry_overrides()
    reports_by_name = overrides.get("reports_by_name") if isinstance(overrides.get("reports_by_name"), dict) else {}
    report_override = reports_by_name.get(report_name)
    if not isinstance(report_override, dict):
        return out
    return _merge_dict(out, report_override)
