from __future__ import annotations

from typing import Any, Dict


def apply_registry_overrides(cap: Dict[str, Any]) -> Dict[str, Any]:
    """
    V7 policy: no hardcoded report-name pattern overrides in runtime.
    Capability rows pass through unchanged.
    """
    return dict(cap or {})
