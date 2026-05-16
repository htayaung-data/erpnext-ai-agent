from __future__ import annotations

# Compatibility facade: the live frontdoor lane implementation now lives in
# qwen_chat/lanes/frontdoor_lane.py. Keep this root module as a thin re-export
# so older imports cannot drift into a second answer-emission implementation.
from ai_assistant_ui.qwen_chat.lanes.frontdoor_lane import (
	evaluate_frontdoor_lane,
	handle_frontdoor_turn,
)

__all__ = [
	"evaluate_frontdoor_lane",
	"handle_frontdoor_turn",
]
