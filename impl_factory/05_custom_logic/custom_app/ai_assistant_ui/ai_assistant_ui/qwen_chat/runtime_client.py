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


def _timeout_seconds() -> float:
	raw = _conf_get("qwen_agent_runtime_timeout", 30)
	try:
		return max(3.0, float(raw))
	except Exception:
		return 30.0


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


def call_qwen_runtime_chat(
	*,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	recent_messages: List[Dict[str, str]],
	mode: str,
	request_id: str,
) -> Dict[str, Any]:
	base_url = _base_url()
	if not base_url:
		raise QwenRuntimeClientError("Qwen runtime base URL is not configured.")

	payload = {
		"session_id": str(session_id or "").strip(),
		"user_id": str(user_id or "").strip(),
		"site_name": str(site_name or "").strip(),
		"message": str(message or "").strip(),
		"recent_messages": list(recent_messages or []),
		"mode": str(mode or "read_only").strip() or "read_only",
		"request_id": str(request_id or "").strip(),
	}

	url = f"{base_url}/chat"
	try:
		resp = requests.post(
			url,
			headers=_auth_headers(),
			data=json.dumps(payload),
			timeout=_timeout_seconds(),
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
