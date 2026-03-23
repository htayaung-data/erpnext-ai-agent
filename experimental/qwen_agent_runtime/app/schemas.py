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
	response_policy: Dict[str, Any] = Field(default_factory=dict)
	family_tool_context: Dict[str, Any] = Field(default_factory=dict)
	mode: str = "read_only"
	compiled_query: Dict[str, Any] = Field(default_factory=dict)
	artifact_context: Dict[str, Any] = Field(default_factory=dict)
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


class FollowUpInterpretRequest(BaseModel):
	request_id: str
	session_id: str
	user_id: str
	site_name: str
	message: str
	recent_messages: List[ChatMessage] = Field(default_factory=list)
	latest_grounded_turn: Dict[str, Any] = Field(default_factory=dict)
	latest_assistant_payload: Dict[str, Any] = Field(default_factory=dict)
	interpretation_context: Dict[str, Any] = Field(default_factory=dict)


class FollowUpInterpretation(BaseModel):
	requested_modes: List[str] = Field(default_factory=list)
	target_dimension: str = ""
	target_limit: int = 0
	sort_direction: str = ""
	target_capability_id: str = ""
	self_contained: bool = False
	confidence: float = 0.0
	reason: str = ""


class FollowUpInterpretResponse(BaseModel):
	ok: bool
	interpretation: FollowUpInterpretation | None = None
	agent_meta: Dict[str, Any] = Field(default_factory=dict)
	error: str = ""


class FreshQueryInterpretRequest(BaseModel):
	request_id: str
	session_id: str
	user_id: str
	site_name: str
	message: str
	recent_messages: List[ChatMessage] = Field(default_factory=list)
	interpretation_context: Dict[str, Any] = Field(default_factory=dict)
	model_override: str = ""


class FreshQueryInterpretation(BaseModel):
	intent_class: str = ""
	candidate_capability_ids: List[str] = Field(default_factory=list)
	candidate_reports: List[str] = Field(default_factory=list)
	requested_dimensions: List[str] = Field(default_factory=list)
	requested_metrics: List[str] = Field(default_factory=list)
	requested_time_scope: str = ""
	requested_presentation: List[str] = Field(default_factory=list)
	extracted_slots: Dict[str, Any] = Field(default_factory=dict)
	ambiguity_flags: List[str] = Field(default_factory=list)
	ambiguity_reason: str = ""
	confidence: float = 0.0


class FreshQueryInterpretResponse(BaseModel):
	ok: bool
	interpretation: FreshQueryInterpretation | None = None
	agent_meta: Dict[str, Any] = Field(default_factory=dict)
	error: str = ""
