from __future__ import annotations

from typing import Any, Dict, Iterable


def tool_payload_from_value(value: Any) -> Dict[str, Any]:
	if value is None:
		return {}
	if isinstance(value, dict):
		return dict(value)
	to_payload = getattr(value, "to_payload", None)
	if callable(to_payload):
		payload = to_payload()
		return dict(payload or {}) if isinstance(payload, dict) else {}
	return {}


def append_tool_payload_values(
	session_doc,
	values: Iterable[Any],
	*,
	append_tool_payload,
) -> None:
	for value in values or []:
		payload = tool_payload_from_value(value)
		if payload:
			append_tool_payload(session_doc, payload)
