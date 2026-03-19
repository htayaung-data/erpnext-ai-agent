from __future__ import annotations

from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status

from app.schemas import ChatRequest, ChatResponse
from app.service import handle_chat
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
	return {
		"ok": True,
		"engine_mode": settings.engine_mode,
		"qwen_model": settings.qwen_model,
		"fac_mcp_configured": bool(settings.fac_mcp_url or settings.fac_mcp_config_json),
	}


@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(_require_auth)])
def chat(request: ChatRequest, settings: Settings = Depends(get_settings)) -> ChatResponse:
	return handle_chat(request, settings)
