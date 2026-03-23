from __future__ import annotations

from typing import Any, Optional, Type
import importlib
import pkgutil

import frappe

_FAC_API_CLS: Optional[Type] = None


def _try_import_attr(module_path: str, attr: str):
    try:
        module = importlib.import_module(module_path)
    except Exception:
        return None
    return getattr(module, attr, None)


def _score_api_instance(api: object) -> int:
    if not hasattr(api, "generate_report"):
        return 0
    score = 10
    if hasattr(api, "report_requirements"):
        score += 5
    if hasattr(api, "report_list"):
        score += 2
    return score


def _discover_fac_api_class() -> Type:
    global _FAC_API_CLS
    if _FAC_API_CLS is not None:
        return _FAC_API_CLS

    candidates: list[Type] = []
    common_paths = [
        "frappe_assistant_core.api",
        "frappe_assistant_core.api.frappe_assistant_api",
        "frappe_assistant_core.frappe_assistant.api",
        "frappe_assistant_core.frappe_assistant_api",
        "frappe_assistant_core.assistant.api",
    ]
    for module_path in common_paths:
        cls = _try_import_attr(module_path, "FrappeAssistantAPI")
        if cls:
            candidates.append(cls)

    try:
        pkg = importlib.import_module("frappe_assistant_core")
    except Exception as exc:
        raise RuntimeError(
            "Cannot import frappe_assistant_core Python package. Confirm frappe_assistant_core is installed on this bench."
        ) from exc

    def _interesting(name: str) -> bool:
        lower = name.lower()
        return ("api" in lower or "assistant" in lower) and ("test" not in lower)

    for mod in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        if not _interesting(mod.name):
            continue
        try:
            module = importlib.import_module(mod.name)
        except Exception:
            continue
        cls = getattr(module, "FrappeAssistantAPI", None)
        if cls:
            candidates.append(cls)

    unique: list[Type] = []
    seen: set[str] = set()
    for cls in candidates:
        key = f"{getattr(cls, '__module__', '')}.{getattr(cls, '__name__', '')}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(cls)

    best: Optional[tuple[int, Type]] = None
    for cls in unique:
        try:
            api = cls(frappe.session.user)
        except Exception:
            continue
        score = _score_api_instance(api)
        if score <= 0:
            continue
        if best is None or score > best[0]:
            best = (score, cls)

    if best is None:
        raise RuntimeError(
            "Cannot locate a usable FrappeAssistantAPI inside frappe_assistant_core (must support generate_report())."
        )

    _FAC_API_CLS = best[1]
    return _FAC_API_CLS


def get_fac_api(user: Optional[str] = None):
    resolved_user = user or frappe.session.user
    cls = _discover_fac_api_class()
    return cls(resolved_user)


def fac_generate_report(
    report_name: str,
    *,
    filters: Optional[dict] = None,
    fmt: str = "json",
    user: Optional[str] = None,
) -> Any:
    api = get_fac_api(user=user)
    return api.generate_report(report_name, filters=filters or {}, format=fmt)
