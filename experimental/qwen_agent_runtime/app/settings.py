from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List


def _env(name: str, default: str = "") -> str:
	return str(os.getenv(name, default) or "").strip()


def _env_int(name: str, default: int) -> int:
	try:
		return int(_env(name, str(default)))
	except Exception:
		return default


@dataclass(frozen=True)
class Settings:
	app_host: str
	app_port: int
	runtime_api_token: str
	engine_mode: str
	chat_timeout_seconds: int
	response_char_limit: int
	max_tool_calls: int
	qwen_base_url: str
	qwen_model: str
	qwen_api_key: str
	erp_default_company: str
	fac_mcp_url: str
	fac_mcp_server_name: str
	fac_mcp_transport: str
	fac_allowed_tools: List[str]
	fac_auth_bearer_token: str
	fac_auth_header_name: str
	fac_auth_header_value: str
	fac_mcp_config_json: str

	@property
	def fac_allowed_tools_set(self) -> set[str]:
		return {x for x in self.fac_allowed_tools if x}

	def fac_mcp_config(self) -> Dict[str, Any]:
		if self.fac_mcp_config_json:
			try:
				obj = json.loads(self.fac_mcp_config_json)
				if isinstance(obj, dict):
					return obj
			except Exception:
				return {}
		if not self.fac_mcp_url:
			return {}

		server_cfg: Dict[str, Any] = {"url": self.fac_mcp_url}
		if self.fac_mcp_transport:
			server_cfg["type"] = self.fac_mcp_transport
		headers: Dict[str, str] = {}
		if self.fac_auth_bearer_token:
			headers["Authorization"] = f"Bearer {self.fac_auth_bearer_token}"
		if self.fac_auth_header_name and self.fac_auth_header_value:
			headers[self.fac_auth_header_name] = self.fac_auth_header_value
		if headers:
			server_cfg["headers"] = headers
		return {"mcpServers": {self.fac_mcp_server_name or "erp_fac": server_cfg}}


def load_settings() -> Settings:
	return Settings(
		app_host=_env("APP_HOST", "0.0.0.0"),
		app_port=_env_int("APP_PORT", 8010),
		runtime_api_token=_env("RUNTIME_API_TOKEN"),
		engine_mode=_env("ENGINE_MODE", "mock").lower() or "mock",
		chat_timeout_seconds=max(5, _env_int("CHAT_TIMEOUT_SECONDS", 45)),
		response_char_limit=max(256, _env_int("RESPONSE_CHAR_LIMIT", 4000)),
		max_tool_calls=max(1, _env_int("MAX_TOOL_CALLS", 6)),
		qwen_base_url=_env("QWEN_BASE_URL"),
		qwen_model=_env("QWEN_MODEL", "Qwen/Qwen3-30B-A3B-Instruct-2507"),
		qwen_api_key=_env("QWEN_API_KEY", "EMPTY"),
		erp_default_company=_env("ERP_DEFAULT_COMPANY"),
		fac_mcp_url=_env("FAC_MCP_URL"),
		fac_mcp_server_name=_env("FAC_MCP_SERVER_NAME", "erp_fac"),
		fac_mcp_transport=_env("FAC_MCP_TRANSPORT"),
		fac_allowed_tools=[x.strip() for x in _env("FAC_ALLOWED_TOOLS").split(",") if x.strip()],
		fac_auth_bearer_token=_env("FAC_AUTH_BEARER_TOKEN"),
		fac_auth_header_name=_env("FAC_AUTH_HEADER_NAME"),
		fac_auth_header_value=_env("FAC_AUTH_HEADER_VALUE"),
		fac_mcp_config_json=_env("FAC_MCP_CONFIG_JSON"),
	)
