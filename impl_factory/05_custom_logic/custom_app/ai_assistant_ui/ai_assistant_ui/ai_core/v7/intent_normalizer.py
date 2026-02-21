from __future__ import annotations

from typing import Any, Dict


def normalize_business_request(*, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phase 1 skeleton.
    Full normalization is implemented in later phases.
    """
    return {
        "intent": "READ",
        "task_type": "detail",
        "subject": "",
        "metric": "",
        "aggregation": "none",
        "group_by": [],
        "time_scope": {"mode": "none", "value": ""},
        "filters": {},
        "top_n": 0,
        "output_contract": {"mode": "detail", "minimal_columns": []},
        "ambiguities": [],
        "needs_clarification": False,
        "_phase": "phase1_skeleton",
        "_message_preview": str(message or "").strip()[:120],
    }
