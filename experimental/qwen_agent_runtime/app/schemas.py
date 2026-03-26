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


class FrontDoorInterpretRequest(BaseModel):
	request_id: str
	session_id: str
	user_id: str
	site_name: str
	message: str
	recent_messages: List[ChatMessage] = Field(default_factory=list)
	grounded_context_available: bool = False
	interpretation_context: Dict[str, Any] = Field(default_factory=dict)


class FrontDoorInterpretation(BaseModel):
	intent_class: str = ""
	confidence: float = 0.0
	reason: str = ""


class FrontDoorInterpretResponse(BaseModel):
	ok: bool
	interpretation: FrontDoorInterpretation | None = None
	agent_meta: Dict[str, Any] = Field(default_factory=dict)
	error: str = ""


class FrontDoorRenderRequest(BaseModel):
	request_id: str
	session_id: str
	user_id: str
	site_name: str
	message: str
	recent_messages: List[ChatMessage] = Field(default_factory=list)
	grounded_context_available: bool = False
	intent_class: str = ""
	response_mode: str = ""
	response_payload: Dict[str, Any] = Field(default_factory=dict)
	reason: str = ""


class FrontDoorRenderResponse(BaseModel):
	ok: bool
	answer_text: str = ""
	agent_meta: Dict[str, Any] = Field(default_factory=dict)
	error: str = ""


class ReasoningActivationInterpretRequest(BaseModel):
	request_id: str
	session_id: str
	user_id: str
	site_name: str
	message: str
	recent_messages: List[ChatMessage] = Field(default_factory=list)
	latest_grounded_turn: Dict[str, Any] = Field(default_factory=dict)
	latest_family_artifact: Dict[str, Any] = Field(default_factory=dict)
	latest_assistant_payload: Dict[str, Any] = Field(default_factory=dict)
	activation_context: Dict[str, Any] = Field(default_factory=dict)


class ReasoningActivationInterpretation(BaseModel):
	reasoning_type: str = ""
	detail_level: str = ""
	presentation_style: str = ""
	confidence: float = 0.0
	reason: str = ""


class ReasoningActivationInterpretResponse(BaseModel):
	ok: bool
	interpretation: ReasoningActivationInterpretation | None = None
	agent_meta: Dict[str, Any] = Field(default_factory=dict)
	error: str = ""


class RepairIntentInterpretRequest(BaseModel):
	request_id: str
	session_id: str
	user_id: str
	site_name: str
	message: str
	recent_messages: List[ChatMessage] = Field(default_factory=list)
	latest_recovery_contract: Dict[str, Any] = Field(default_factory=dict)
	latest_grounded_turn: Dict[str, Any] = Field(default_factory=dict)
	latest_assistant_payload: Dict[str, Any] = Field(default_factory=dict)
	interpretation_context: Dict[str, Any] = Field(default_factory=dict)


class RepairIntentInterpretation(BaseModel):
	repair_intent_type: str = ""
	accepted_recovery_action: str = ""
	guidance_topic: str = ""
	preserve_scope: bool = False
	preserve_entity_dimension: bool = False
	preserve_time_context: bool = False
	confidence: float = 0.0
	reason: str = ""


class RepairIntentInterpretResponse(BaseModel):
	ok: bool
	interpretation: RepairIntentInterpretation | None = None
	agent_meta: Dict[str, Any] = Field(default_factory=dict)
	error: str = ""


class ReasoningRenderRequest(BaseModel):
	request_id: str
	session_id: str
	user_id: str
	site_name: str
	message: str
	recent_messages: List[ChatMessage] = Field(default_factory=list)
	reasoning_context: Dict[str, Any] = Field(default_factory=dict)


class ReasoningRenderPayload(BaseModel):
	answer_text: str = ""
	supported_claims: List[Dict[str, Any]] = Field(default_factory=list)
	recommendations: List[Dict[str, Any]] = Field(default_factory=list)
	speculation_flags: List[str] = Field(default_factory=list)
	confidence: float = 0.0
	reason: str = ""


class ReasoningRenderResponse(BaseModel):
	ok: bool
	payload: ReasoningRenderPayload | None = None
	agent_meta: Dict[str, Any] = Field(default_factory=dict)
	error: str = ""
