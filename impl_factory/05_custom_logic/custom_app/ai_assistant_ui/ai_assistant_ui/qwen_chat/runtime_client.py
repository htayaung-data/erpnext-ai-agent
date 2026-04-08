from __future__ import annotations

import json
from typing import Any, Dict, List

import requests

try:
	import frappe  # type: ignore
except Exception:  # pragma: no cover - allows local import without Frappe runtime
	frappe = None


class QwenRuntimeClientError(RuntimeError):
	pass


def _conf_get(key: str, default: Any = "") -> Any:
	if frappe is None:
		return default
	try:
		return (getattr(frappe, "conf", None) or {}).get(key, default)
	except Exception:
		return default


def _base_url() -> str:
	return str(_conf_get("qwen_agent_runtime_base_url") or "").strip().rstrip("/")


def _timeout_seconds(conf_key: str = "qwen_agent_runtime_timeout", default: float = 30.0) -> float:
	raw = _conf_get(conf_key, default)
	try:
		return max(3.0, float(raw))
	except Exception:
		return float(default)


def _fresh_query_timeout_seconds() -> float:
	configured = _conf_get("qwen_agent_runtime_fresh_query_timeout", "")
	if str(configured or "").strip():
		return _timeout_seconds("qwen_agent_runtime_fresh_query_timeout", 90.0)
	return max(90.0, _timeout_seconds())


def _auth_headers() -> Dict[str, str]:
	headers = {"Content-Type": "application/json"}
	token = str(_conf_get("qwen_agent_runtime_api_token") or "").strip()
	if token:
		headers["Authorization"] = f"Bearer {token}"
	header_name = str(_conf_get("qwen_agent_runtime_auth_header_name") or "").strip()
	header_value = str(_conf_get("qwen_agent_runtime_auth_header_value") or "").strip()
	if header_name and header_value:
		headers[header_name] = header_value
	return headers


def build_qwen_runtime_chat_request_config() -> Dict[str, Any]:
	base_url = _base_url()
	if not base_url:
		raise QwenRuntimeClientError("Qwen runtime base URL is not configured.")
	return {
		"base_url": base_url,
		"headers": _auth_headers(),
		"timeout_seconds": _timeout_seconds(),
	}


def _resolve_request_config(
	request_config: Dict[str, Any] | None = None,
	*,
	timeout_seconds: float | None = None,
) -> Dict[str, Any]:
	config = request_config if isinstance(request_config, dict) else {}
	base_url = str(config.get("base_url") or "").strip().rstrip("/") or _base_url()
	if not base_url:
		raise QwenRuntimeClientError("Qwen runtime base URL is not configured.")
	headers = config.get("headers") if isinstance(config.get("headers"), dict) else _auth_headers()
	timeout_value = timeout_seconds if timeout_seconds is not None else config.get("timeout_seconds")
	try:
		timeout = max(3.0, float(timeout_value))
	except Exception:
		timeout = _timeout_seconds()
	return {
		"base_url": base_url,
		"headers": headers,
		"timeout_seconds": timeout,
	}


def _post_json(
	*,
	path: str,
	payload: Dict[str, Any],
	request_error_prefix: str,
	non_json_prefix: str,
	http_error_prefix: str,
	invalid_payload_message: str,
	timeout_seconds: float | None = None,
	request_config: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	config = _resolve_request_config(request_config, timeout_seconds=timeout_seconds)
	url = f"{str(config.get('base_url') or '').rstrip('/')}/{str(path or '').lstrip('/')}"
	try:
		resp = requests.post(
			url,
			headers=config.get("headers") if isinstance(config.get("headers"), dict) else _auth_headers(),
			data=json.dumps(payload),
			timeout=float(config.get("timeout_seconds") or _timeout_seconds()),
		)
	except requests.RequestException as exc:
		raise QwenRuntimeClientError(f"{request_error_prefix}: {exc}") from exc

	try:
		data = resp.json()
	except Exception as exc:
		raise QwenRuntimeClientError(f"{non_json_prefix} ({resp.status_code}).") from exc

	if resp.status_code >= 400:
		message = ""
		if isinstance(data, dict):
			message = str(data.get("error") or data.get("detail") or "").strip()
		raise QwenRuntimeClientError(message or f"{http_error_prefix} ({resp.status_code}).")

	if not isinstance(data, dict):
		raise QwenRuntimeClientError(invalid_payload_message)

	return data


def call_qwen_runtime_chat(
	*,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	recent_messages: List[Dict[str, str]],
	response_policy: Dict[str, Any] | None,
	family_tool_context: Dict[str, Any] | None,
	mode: str,
	compiled_query: Dict[str, Any] | None = None,
	artifact_context: Dict[str, Any] | None = None,
	request_id: str,
	request_config: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	payload = {
		"session_id": str(session_id or "").strip(),
		"user_id": str(user_id or "").strip(),
		"site_name": str(site_name or "").strip(),
		"message": str(message or "").strip(),
		"recent_messages": list(recent_messages or []),
		"response_policy": response_policy if isinstance(response_policy, dict) else {},
		"family_tool_context": family_tool_context if isinstance(family_tool_context, dict) else {},
		"mode": str(mode or "read_only").strip() or "read_only",
		"compiled_query": compiled_query if isinstance(compiled_query, dict) else {},
		"artifact_context": artifact_context if isinstance(artifact_context, dict) else {},
		"request_id": str(request_id or "").strip(),
	}
	return _post_json(
		path="/chat",
		payload=payload,
		request_error_prefix="Qwen runtime request failed",
		non_json_prefix="Qwen runtime returned non-JSON response",
		http_error_prefix="Qwen runtime error",
		invalid_payload_message="Qwen runtime returned invalid payload.",
		request_config=request_config,
	)


def call_qwen_runtime_followup_interpretation(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	recent_messages: List[Dict[str, str]],
	latest_grounded_turn: Dict[str, Any],
	latest_assistant_payload: Dict[str, Any],
	interpretation_context: Dict[str, Any],
) -> Dict[str, Any]:
	payload = {
		"request_id": str(request_id or "").strip(),
		"session_id": str(session_id or "").strip(),
		"user_id": str(user_id or "").strip(),
		"site_name": str(site_name or "").strip(),
		"message": str(message or "").strip(),
		"recent_messages": list(recent_messages or []),
		"latest_grounded_turn": latest_grounded_turn if isinstance(latest_grounded_turn, dict) else {},
		"latest_assistant_payload": latest_assistant_payload if isinstance(latest_assistant_payload, dict) else {},
		"interpretation_context": interpretation_context if isinstance(interpretation_context, dict) else {},
	}
	return _post_json(
		path="/interpret-followup",
		payload=payload,
		request_error_prefix="Qwen runtime follow-up interpretation failed",
		non_json_prefix="Qwen runtime follow-up interpreter returned non-JSON response",
		http_error_prefix="Qwen runtime follow-up interpreter error",
		invalid_payload_message="Qwen runtime follow-up interpreter returned invalid payload.",
		timeout_seconds=_timeout_seconds(),
	)


def call_qwen_runtime_frontdoor_interpretation(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	recent_messages: List[Dict[str, str]],
	grounded_context_available: bool,
	interpretation_context: Dict[str, Any],
) -> Dict[str, Any]:
	payload = {
		"request_id": str(request_id or "").strip(),
		"session_id": str(session_id or "").strip(),
		"user_id": str(user_id or "").strip(),
		"site_name": str(site_name or "").strip(),
		"message": str(message or "").strip(),
		"recent_messages": list(recent_messages or []),
		"grounded_context_available": bool(grounded_context_available),
		"interpretation_context": interpretation_context if isinstance(interpretation_context, dict) else {},
	}
	return _post_json(
		path="/interpret-front-door",
		payload=payload,
		request_error_prefix="Qwen runtime front-door interpretation failed",
		non_json_prefix="Qwen runtime front-door interpreter returned non-JSON response",
		http_error_prefix="Qwen runtime front-door interpreter error",
		invalid_payload_message="Qwen runtime front-door interpreter returned invalid payload.",
		timeout_seconds=_timeout_seconds(),
	)


def call_qwen_runtime_reasoning_activation_interpretation(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	recent_messages: List[Dict[str, str]],
	latest_grounded_turn: Dict[str, Any],
	latest_family_artifact: Dict[str, Any],
	latest_assistant_payload: Dict[str, Any],
	activation_context: Dict[str, Any],
) -> Dict[str, Any]:
	payload = {
		"request_id": str(request_id or "").strip(),
		"session_id": str(session_id or "").strip(),
		"user_id": str(user_id or "").strip(),
		"site_name": str(site_name or "").strip(),
		"message": str(message or "").strip(),
		"recent_messages": list(recent_messages or []),
		"latest_grounded_turn": latest_grounded_turn if isinstance(latest_grounded_turn, dict) else {},
		"latest_family_artifact": latest_family_artifact if isinstance(latest_family_artifact, dict) else {},
		"latest_assistant_payload": latest_assistant_payload if isinstance(latest_assistant_payload, dict) else {},
		"activation_context": activation_context if isinstance(activation_context, dict) else {},
	}
	return _post_json(
		path="/interpret-reasoning-activation",
		payload=payload,
		request_error_prefix="Qwen runtime reasoning activation interpretation failed",
		non_json_prefix="Qwen runtime reasoning activation interpreter returned non-JSON response",
		http_error_prefix="Qwen runtime reasoning activation interpreter error",
		invalid_payload_message="Qwen runtime reasoning activation interpreter returned invalid payload.",
		timeout_seconds=_timeout_seconds(),
	)


def call_qwen_runtime_repair_intent_interpretation(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	recent_messages: List[Dict[str, str]],
	latest_recovery_contract: Dict[str, Any],
	latest_grounded_turn: Dict[str, Any],
	latest_assistant_payload: Dict[str, Any],
	interpretation_context: Dict[str, Any],
) -> Dict[str, Any]:
	payload = {
		"request_id": str(request_id or "").strip(),
		"session_id": str(session_id or "").strip(),
		"user_id": str(user_id or "").strip(),
		"site_name": str(site_name or "").strip(),
		"message": str(message or "").strip(),
		"recent_messages": list(recent_messages or []),
		"latest_recovery_contract": latest_recovery_contract if isinstance(latest_recovery_contract, dict) else {},
		"latest_grounded_turn": latest_grounded_turn if isinstance(latest_grounded_turn, dict) else {},
		"latest_assistant_payload": latest_assistant_payload if isinstance(latest_assistant_payload, dict) else {},
		"interpretation_context": interpretation_context if isinstance(interpretation_context, dict) else {},
	}
	return _post_json(
		path="/interpret-repair-intent",
		payload=payload,
		request_error_prefix="Qwen runtime repair interpretation failed",
		non_json_prefix="Qwen runtime repair interpreter returned non-JSON response",
		http_error_prefix="Qwen runtime repair interpreter error",
		invalid_payload_message="Qwen runtime repair interpreter returned invalid payload.",
		timeout_seconds=_timeout_seconds(),
	)


def call_qwen_runtime_reasoning_render(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	recent_messages: List[Dict[str, str]],
	reasoning_context: Dict[str, Any],
) -> Dict[str, Any]:
	payload = {
		"request_id": str(request_id or "").strip(),
		"session_id": str(session_id or "").strip(),
		"user_id": str(user_id or "").strip(),
		"site_name": str(site_name or "").strip(),
		"message": str(message or "").strip(),
		"recent_messages": list(recent_messages or []),
		"reasoning_context": reasoning_context if isinstance(reasoning_context, dict) else {},
	}
	return _post_json(
		path="/render-erp-business-reasoning",
		payload=payload,
		request_error_prefix="Qwen runtime ERP business reasoning request failed",
		non_json_prefix="Qwen runtime ERP business reasoning returned non-JSON response",
		http_error_prefix="Qwen runtime ERP business reasoning error",
		invalid_payload_message="Qwen runtime ERP business reasoning returned invalid payload.",
		timeout_seconds=_timeout_seconds(),
	)


def call_qwen_runtime_frontdoor_render(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	recent_messages: List[Dict[str, str]],
	grounded_context_available: bool,
	intent_class: str,
	response_mode: str,
	response_payload: Dict[str, Any],
	reason: str,
) -> Dict[str, Any]:
	payload = {
		"request_id": str(request_id or "").strip(),
		"session_id": str(session_id or "").strip(),
		"user_id": str(user_id or "").strip(),
		"site_name": str(site_name or "").strip(),
		"message": str(message or "").strip(),
		"recent_messages": list(recent_messages or []),
		"grounded_context_available": bool(grounded_context_available),
		"intent_class": str(intent_class or "").strip(),
		"response_mode": str(response_mode or "").strip(),
		"response_payload": response_payload if isinstance(response_payload, dict) else {},
		"reason": str(reason or "").strip(),
	}
	return _post_json(
		path="/render-front-door",
		payload=payload,
		request_error_prefix="Qwen runtime front-door render failed",
		non_json_prefix="Qwen runtime front-door renderer returned non-JSON response",
		http_error_prefix="Qwen runtime front-door renderer error",
		invalid_payload_message="Qwen runtime front-door renderer returned invalid payload.",
		timeout_seconds=_timeout_seconds(),
	)


def call_qwen_runtime_fresh_query_interpretation(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	recent_messages: List[Dict[str, str]],
	interpretation_context: Dict[str, Any],
	model_override: str = "",
) -> Dict[str, Any]:
	payload = {
		"request_id": str(request_id or "").strip(),
		"session_id": str(session_id or "").strip(),
		"user_id": str(user_id or "").strip(),
		"site_name": str(site_name or "").strip(),
		"message": str(message or "").strip(),
		"recent_messages": list(recent_messages or []),
		"interpretation_context": interpretation_context if isinstance(interpretation_context, dict) else {},
		"model_override": str(model_override or "").strip(),
	}
	return _post_json(
		path="/interpret-fresh-query",
		payload=payload,
		request_error_prefix="Qwen runtime fresh-query interpretation failed",
		non_json_prefix="Qwen runtime fresh-query interpreter returned non-JSON response",
		http_error_prefix="Qwen runtime fresh-query interpreter error",
		invalid_payload_message="Qwen runtime fresh-query interpreter returned invalid payload.",
		timeout_seconds=_fresh_query_timeout_seconds(),
	)
