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
	config = request_config if isinstance(request_config, dict) else {}
	base_url = str(config.get("base_url") or "").strip().rstrip("/") or _base_url()
	if not base_url:
		raise QwenRuntimeClientError("Qwen runtime base URL is not configured.")
	headers = config.get("headers") if isinstance(config.get("headers"), dict) else _auth_headers()
	timeout_seconds = config.get("timeout_seconds")
	try:
		timeout = max(3.0, float(timeout_seconds))
	except Exception:
		timeout = _timeout_seconds()

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

	url = f"{base_url}/chat"
	try:
		resp = requests.post(
			url,
			headers=headers,
			data=json.dumps(payload),
			timeout=timeout,
		)
	except requests.RequestException as exc:
		raise QwenRuntimeClientError(f"Qwen runtime request failed: {exc}") from exc

	try:
		data = resp.json()
	except Exception as exc:
		raise QwenRuntimeClientError(
			f"Qwen runtime returned non-JSON response ({resp.status_code})."
		) from exc

	if resp.status_code >= 400:
		msg = ""
		if isinstance(data, dict):
			msg = str(data.get("error") or data.get("detail") or "").strip()
		raise QwenRuntimeClientError(msg or f"Qwen runtime error ({resp.status_code}).")

	if not isinstance(data, dict):
		raise QwenRuntimeClientError("Qwen runtime returned invalid payload.")

	return data


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
	base_url = _base_url()
	if not base_url:
		raise QwenRuntimeClientError("Qwen runtime base URL is not configured.")

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

	url = f"{base_url}/interpret-followup"
	try:
		resp = requests.post(
			url,
			headers=_auth_headers(),
			data=json.dumps(payload),
			timeout=_timeout_seconds(),
		)
	except requests.RequestException as exc:
		raise QwenRuntimeClientError(f"Qwen runtime follow-up interpretation failed: {exc}") from exc

	try:
		data = resp.json()
	except Exception as exc:
		raise QwenRuntimeClientError(
			f"Qwen runtime follow-up interpreter returned non-JSON response ({resp.status_code})."
		) from exc

	if resp.status_code >= 400:
		msg = ""
		if isinstance(data, dict):
			msg = str(data.get("error") or data.get("detail") or "").strip()
		raise QwenRuntimeClientError(msg or f"Qwen runtime follow-up interpreter error ({resp.status_code}).")

	if not isinstance(data, dict):
		raise QwenRuntimeClientError("Qwen runtime follow-up interpreter returned invalid payload.")

	return data


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
	base_url = _base_url()
	if not base_url:
		raise QwenRuntimeClientError("Qwen runtime base URL is not configured.")

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

	url = f"{base_url}/interpret-fresh-query"
	try:
		resp = requests.post(
			url,
			headers=_auth_headers(),
			data=json.dumps(payload),
			timeout=_fresh_query_timeout_seconds(),
		)
	except requests.RequestException as exc:
		raise QwenRuntimeClientError(f"Qwen runtime fresh-query interpretation failed: {exc}") from exc

	try:
		data = resp.json()
	except Exception as exc:
		raise QwenRuntimeClientError(
			f"Qwen runtime fresh-query interpreter returned non-JSON response ({resp.status_code})."
		) from exc

	if resp.status_code >= 400:
		msg = ""
		if isinstance(data, dict):
			msg = str(data.get("error") or data.get("detail") or "").strip()
		raise QwenRuntimeClientError(
			msg or f"Qwen runtime fresh-query interpreter error ({resp.status_code})."
		)

	if not isinstance(data, dict):
		raise QwenRuntimeClientError("Qwen runtime fresh-query interpreter returned invalid payload.")

	return data
