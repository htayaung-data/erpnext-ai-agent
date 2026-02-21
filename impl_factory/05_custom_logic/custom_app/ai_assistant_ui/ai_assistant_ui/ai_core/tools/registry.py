from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from ai_assistant_ui.ai_core.v7.dispatcher import dispatch_report_qa, is_report_qa_tool


@dataclass
class ToolInvocation:
    name: str
    args: Dict[str, Any]


def run_tool(invocation: ToolInvocation, *, session_name: Optional[str] = None, user: Optional[str] = None) -> Dict[str, Any]:
    if is_report_qa_tool(invocation.name):
        return dispatch_report_qa(
            tool_name=invocation.name,
            args=invocation.args or {},
            session_name=session_name,
            user=user,
        )

    raise KeyError(f"Unknown tool: {invocation.name}")
