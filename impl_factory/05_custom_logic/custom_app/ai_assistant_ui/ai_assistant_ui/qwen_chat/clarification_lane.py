from __future__ import annotations

# Compatibility facade: the live clarification lane implementation now lives in
# qwen_chat/lanes/clarification_lane.py. Keep this module as a thin re-export
# so older imports cannot drift into a second behavior copy.
from ai_assistant_ui.qwen_chat.lanes.clarification_lane import (
    build_pending_clarification_frontdoor_skip,
    handle_pending_clarification_turn,
)

__all__ = [
    "build_pending_clarification_frontdoor_skip",
    "handle_pending_clarification_turn",
]
