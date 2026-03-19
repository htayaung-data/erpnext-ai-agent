from __future__ import annotations

from app.schemas import ChatRequest, ChatResponse


def run_mock_engine(request: ChatRequest) -> ChatResponse:
	text = request.message.strip()
	answer = (
		"Mock runtime connected successfully. "
		f"I received your ERP question: \"{text[:280]}\". "
		"The real Qwen-Agent + FAC MCP loop is not enabled yet, so this response is a safe prototype confirmation."
	)
	return ChatResponse(
		ok=True,
		answer_text=answer,
		tool_trace=[],
		agent_meta={
			"engine": "mock",
			"mode": str(request.mode or "read_only"),
			"grounded": False,
		},
		error="",
	)
