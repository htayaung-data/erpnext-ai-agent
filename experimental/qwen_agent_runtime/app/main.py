from __future__ import annotations

from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status

from app.schemas import (
	ChatRequest,
	ChatResponse,
	FreshQueryInterpretRequest,
	FreshQueryInterpretResponse,
	FollowUpInterpretRequest,
	FollowUpInterpretResponse,
)
from app.service import (
	handle_chat,
	handle_followup_interpretation,
	handle_fresh_query_interpretation,
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
		settings.semantic_fresh_query_override_active()
		or settings.semantic_followup_override_active()
	)
	return {
		"ok": True,
		"engine_mode": settings.engine_mode,
		"qwen_model": settings.qwen_model,
		"semantic_fresh_query_model": settings.effective_semantic_fresh_query_model(),
		"semantic_fresh_query_override_active": settings.semantic_fresh_query_override_active(),
		"semantic_followup_model": settings.effective_semantic_followup_model(),
		"semantic_followup_override_active": settings.semantic_followup_override_active(),
		"single_model_mode": not multi_model_mode,
		"multi_model_mode": multi_model_mode,
		"fac_mcp_configured": bool(settings.fac_mcp_url or settings.fac_mcp_config_json),
	}


@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(_require_auth)])
def chat(request: ChatRequest, settings: Settings = Depends(get_settings)) -> ChatResponse:
	return handle_chat(request, settings)


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
