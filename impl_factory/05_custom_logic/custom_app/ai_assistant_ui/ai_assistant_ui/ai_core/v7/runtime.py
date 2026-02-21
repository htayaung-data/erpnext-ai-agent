from __future__ import annotations

from typing import Any, Dict, Optional

from ai_assistant_ui.ai_core.v7.read_engine import execute_unified_read_turn


def report_qa_start_v7(*, message: str, export: bool = False, session_name: Optional[str] = None, user: Optional[str] = None) -> Dict[str, Any]:
    """Unified v7 runtime for new turns."""
    return execute_unified_read_turn(
        message=message,
        session_name=session_name,
        user=user,
        export=export,
        pending_state=None,
        source_tool="report_qa_start",
    )


def report_qa_continue_v7(
    *,
    message: str,
    pending_state: Dict[str, Any],
    session_name: Optional[str] = None,
    user: Optional[str] = None,
) -> Dict[str, Any]:
    """Unified v7 runtime for continuation turns."""
    return execute_unified_read_turn(
        message=message,
        session_name=session_name,
        user=user,
        export=False,
        pending_state=(pending_state if isinstance(pending_state, dict) else {}),
        source_tool="report_qa_continue",
    )
