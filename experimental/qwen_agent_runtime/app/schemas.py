from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
	role: Literal["user", "assistant"]
	content: str = ""


class ChatRequest(BaseModel):
	session_id: str
	user_id: str
	site_name: str
	message: str
	recent_messages: List[ChatMessage] = Field(default_factory=list)
	mode: str = "read_only"
	request_id: str


class ToolTraceItem(BaseModel):
	tool: str
	status: str
	detail: str = ""
	detail_obj: Optional[Any] = None
	output_preview: str = ""
	output_obj: Optional[Any] = None
	duration_ms: Optional[int] = None


class ChatResponse(BaseModel):
	ok: bool
	answer_text: str = ""
	tool_trace: List[ToolTraceItem] = Field(default_factory=list)
	agent_meta: Dict[str, Any] = Field(default_factory=dict)
	error: str = ""
