from __future__ import annotations

from typing import Any, Optional, Type, Dict, List, Tuple
import importlib
import pkgutil

import frappe

_FAC_API_CLS: Optional[Type] = None


def _try_import_attr(module_path: str, attr: str):
    try:
        m = importlib.import_module(module_path)
        if hasattr(m, attr):
            return getattr(m, attr)
    except Exception:
        return None
    return None


def _score_api_instance(api: object) -> int:
    """
    Capability scoring:
      - generate_report is mandatory (otherwise 0)
      - report_requirements is preferred
      - report_list is nice-to-have
    """
    if not hasattr(api, "generate_report"):
        return 0
    score = 10
    if hasattr(api, "report_requirements"):
        score += 5
    if hasattr(api, "report_list"):
        score += 2
    return score


def _discover_fac_api_class() -> Type:
    """
    Find best FrappeAssistantAPI class across FAC package layouts.
    We do NOT require report_requirements at discovery time; we pick the most capable class.
    """
    global _FAC_API_CLS
    if _FAC_API_CLS is not None:
        return _FAC_API_CLS

    candidates: List[Type] = []

    common_paths = [
        "frappe_assistant_core.api",
        "frappe_assistant_core.api.frappe_assistant_api",
        "frappe_assistant_core.frappe_assistant.api",
        "frappe_assistant_core.frappe_assistant_api",
        "frappe_assistant_core.assistant.api",
    ]
    for p in common_paths:
        cls = _try_import_attr(p, "FrappeAssistantAPI")
        if cls:
            candidates.append(cls)

    try:
        pkg = importlib.import_module("frappe_assistant_core")
    except Exception as e:
        raise RuntimeError(
            "Cannot import frappe_assistant_core Python package. "
            "Confirm frappe_assistant_core is installed on this bench."
        ) from e

    def _interesting(name: str) -> bool:
        n = name.lower()
        return ("api" in n or "assistant" in n) and ("test" not in n)

    for mod in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        name = mod.name
        if not _interesting(name):
            continue
        try:
            m = importlib.import_module(name)
            if hasattr(m, "FrappeAssistantAPI"):
                candidates.append(getattr(m, "FrappeAssistantAPI"))
        except Exception:
            continue

    # De-dup classes
    uniq: List[Type] = []
    seen = set()
    for c in candidates:
        key = f"{getattr(c, '__module__', '')}.{getattr(c, '__name__', '')}"
        if key in seen:
            continue
        seen.add(key)
        uniq.append(c)

    # Pick the best-scoring instance
    best: Optional[Tuple[int, Type]] = None
    for cls in uniq:
        try:
            api = cls(frappe.session.user)
        except Exception:
            continue
        sc = _score_api_instance(api)
        if sc <= 0:
            continue
        if best is None or sc > best[0]:
            best = (sc, cls)

    if not best:
        raise RuntimeError(
            "Cannot locate a usable FrappeAssistantAPI inside frappe_assistant_core "
            "(must support generate_report())."
        )

    _FAC_API_CLS = best[1]
    return _FAC_API_CLS


def get_fac_api(user: Optional[str] = None):
    user = user or frappe.session.user
    cls = _discover_fac_api_class()
    return cls(user)


def fac_report_list(
    *,
    module: Optional[str] = None,
    report_type: Optional[str] = None,
    user: Optional[str] = None,
) -> Any:
    api = get_fac_api(user=user)
    if hasattr(api, "report_list"):
        args: Dict[str, Any] = {}
        if module:
            args["module"] = module
        if report_type:
            args["report_type"] = report_type
        return api.report_list(**args) if args else api.report_list()

    # fallback if FAC doesn't provide report_list
    filters = {"disabled": 0}
    if module:
        filters["module"] = module
    if report_type:
        filters["report_type"] = report_type
    return frappe.get_all(
        "Report",
        filters=filters,
        fields=["name", "report_name", "report_type", "module", "is_standard", "disabled"],
        order_by="name asc",
    )


def fac_report_requirements(report_name: str, *, user: Optional[str] = None) -> Any:
    api = get_fac_api(user=user)
    if not hasattr(api, "report_requirements"):
        raise AttributeError("FAC API has no report_requirements()")
    fn = getattr(api, "report_requirements")
    attempts = [
        ((report_name,), {}),
        ((), {"report_name": report_name}),
        ((), {"report": report_name}),
        ((), {"name": report_name}),
    ]
    last_exc: Optional[Exception] = None
    for args, kwargs in attempts:
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            continue
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("report_requirements invocation failed with no exception details")


def fac_generate_report(
    report_name: str,
    *,
    filters: Optional[dict] = None,
    fmt: str = "json",
    user: Optional[str] = None,
) -> Any:
    api = get_fac_api(user=user)
    return api.generate_report(report_name, filters=filters or {}, format=fmt)
