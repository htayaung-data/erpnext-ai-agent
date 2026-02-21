from __future__ import annotations

from typing import Optional

from ai_assistant_ui.ai_core.tools.registry import ToolInvocation

def export_requested(message: str) -> bool:
    # Export intent is resolved by the LLM planner; no regex/keyword routing.
    return False


def route_fast_tools(message: str) -> Optional[ToolInvocation]:
    """
    Commercial rule: NO keyword hard-routing for business questions.
    The LLM planner in report_qa decides all report/tool actions.
    """
    return None
