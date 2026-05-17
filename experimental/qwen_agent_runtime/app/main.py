from __future__ import annotations

from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status

from app.schemas import (
	BusinessUnderstandingInterpretRequest,
	BusinessUnderstandingInterpretResponse,
	ChatRequest,
	ChatResponse,
	FrontDoorInterpretRequest,
	FrontDoorInterpretResponse,
	FrontDoorRenderRequest,
	FrontDoorRenderResponse,
	FreshQueryInterpretRequest,
	FreshQueryInterpretResponse,
	FollowUpInterpretRequest,
	FollowUpInterpretResponse,
	ReasoningActivationInterpretRequest,
	ReasoningActivationInterpretResponse,
	RepairIntentInterpretRequest,
	RepairIntentInterpretResponse,
	ReasoningRenderRequest,
	ReasoningRenderResponse,
)
from app.service import (
	handle_business_understanding_interpretation,
	handle_chat,
	handle_frontdoor_interpretation,
	handle_frontdoor_render,
	handle_followup_interpretation,
	handle_fresh_query_interpretation,
	handle_repair_intent_interpretation,
	handle_reasoning_activation_interpretation,
	handle_reasoning_render,
)
from app.settings import Settings, load_settings

app = FastAPI(title="Qwen Agent Runtime", version="0.1.0")


def get_settings() -> Settings:
	return load_settings()


def _require_auth(
	settings: Settings = Depends(get_settings),
	authorization: Optional[str] = Header(default=None),
) -> None:
	if not settings.runtime_api_token:
		return
	expected = f"Bearer {settings.runtime_api_token}"
	if str(authorization or "").strip() != expected:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


@app.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict[str, object]:
	multi_model_mode = bool(
		settings.semantic_frontdoor_override_active()
		or settings.semantic_fresh_query_override_active()
		or settings.semantic_followup_override_active()
		or settings.semantic_reasoning_override_active()
	)
	return {
		"ok": True,
		"engine_mode": settings.engine_mode,
		"qwen_model": settings.qwen_model,
		"semantic_frontdoor_model": settings.effective_semantic_frontdoor_model(),
		"semantic_frontdoor_override_active": settings.semantic_frontdoor_override_active(),
		"semantic_fresh_query_model": settings.effective_semantic_fresh_query_model(),
		"semantic_fresh_query_override_active": settings.semantic_fresh_query_override_active(),
		"semantic_followup_model": settings.effective_semantic_followup_model(),
		"semantic_followup_override_active": settings.semantic_followup_override_active(),
		"semantic_reasoning_model": settings.effective_semantic_reasoning_model(),
		"semantic_reasoning_override_active": settings.semantic_reasoning_override_active(),
		"single_model_mode": not multi_model_mode,
		"multi_model_mode": multi_model_mode,
		"fac_mcp_configured": bool(settings.fac_mcp_url or settings.fac_mcp_config_json),
	}


@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(_require_auth)])
def chat(request: ChatRequest, settings: Settings = Depends(get_settings)) -> ChatResponse:
	return handle_chat(request, settings)


@app.post(
	"/interpret-front-door",
	response_model=FrontDoorInterpretResponse,
	dependencies=[Depends(_require_auth)],
)
def interpret_front_door(
	request: FrontDoorInterpretRequest,
	settings: Settings = Depends(get_settings),
) -> FrontDoorInterpretResponse:
	return handle_frontdoor_interpretation(request, settings)


@app.post(
	"/render-front-door",
	response_model=FrontDoorRenderResponse,
	dependencies=[Depends(_require_auth)],
)
def render_front_door(
	request: FrontDoorRenderRequest,
	settings: Settings = Depends(get_settings),
) -> FrontDoorRenderResponse:
	return handle_frontdoor_render(request, settings)


@app.post(
	"/interpret-followup",
	response_model=FollowUpInterpretResponse,
	dependencies=[Depends(_require_auth)],
)
def interpret_followup(
	request: FollowUpInterpretRequest,
	settings: Settings = Depends(get_settings),
) -> FollowUpInterpretResponse:
	return handle_followup_interpretation(request, settings)


@app.post(
	"/interpret-fresh-query",
	response_model=FreshQueryInterpretResponse,
	dependencies=[Depends(_require_auth)],
)
def interpret_fresh_query(
	request: FreshQueryInterpretRequest,
	settings: Settings = Depends(get_settings),
) -> FreshQueryInterpretResponse:
	return handle_fresh_query_interpretation(request, settings)


@app.post(
	"/interpret-reasoning-activation",
	response_model=ReasoningActivationInterpretResponse,
	dependencies=[Depends(_require_auth)],
)
def interpret_reasoning_activation(
	request: ReasoningActivationInterpretRequest,
	settings: Settings = Depends(get_settings),
) -> ReasoningActivationInterpretResponse:
	return handle_reasoning_activation_interpretation(request, settings)


@app.post(
	"/interpret-repair-intent",
	response_model=RepairIntentInterpretResponse,
	dependencies=[Depends(_require_auth)],
)
def interpret_repair_intent(
	request: RepairIntentInterpretRequest,
	settings: Settings = Depends(get_settings),
) -> RepairIntentInterpretResponse:
	return handle_repair_intent_interpretation(request, settings)


@app.post(
	"/interpret-business-understanding",
	response_model=BusinessUnderstandingInterpretResponse,
	dependencies=[Depends(_require_auth)],
)
def interpret_business_understanding(
	request: BusinessUnderstandingInterpretRequest,
	settings: Settings = Depends(get_settings),
) -> BusinessUnderstandingInterpretResponse:
	return handle_business_understanding_interpretation(request, settings)


@app.post(
	"/render-erp-business-reasoning",
	response_model=ReasoningRenderResponse,
	dependencies=[Depends(_require_auth)],
)
def render_erp_business_reasoning(
	request: ReasoningRenderRequest,
	settings: Settings = Depends(get_settings),
) -> ReasoningRenderResponse:
	return handle_reasoning_render(request, settings)
