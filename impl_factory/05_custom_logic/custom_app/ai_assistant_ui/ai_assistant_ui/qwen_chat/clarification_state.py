from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict


DEFAULT_MAX_CLARIFICATION_ATTEMPTS = 3


@dataclass(frozen=True)
class ClarificationState:
	state: str
	attempt_count: int
	max_attempts: int
	pending_signal: Dict[str, Any]

	@property
	def has_pending(self) -> bool:
		return self.state == "pending" and bool(self.pending_signal)

	def to_storage_payload(self) -> Dict[str, Any]:
		if not self.has_pending:
			return {}
		return {
			"type": "qwen_pending_clarification_state",
			"state": self.state,
			"attempt_count": int(max(0, self.attempt_count)),
			"max_attempts": int(max(1, self.max_attempts)),
			"pending_signal": dict(self.pending_signal),
		}

	def next_attempt(self) -> "ClarificationState":
		if not self.has_pending:
			return self
		return ClarificationState(
			state=self.state,
			attempt_count=int(max(0, self.attempt_count)) + 1,
			max_attempts=int(max(1, self.max_attempts)),
			pending_signal=dict(self.pending_signal),
		)

	def clear(self) -> "ClarificationState":
		return empty_clarification_state()

	@property
	def max_attempts_reached(self) -> bool:
		return self.has_pending and int(max(0, self.attempt_count)) >= int(max(1, self.max_attempts))


def empty_clarification_state() -> ClarificationState:
	return ClarificationState(
		state="no_pending",
		attempt_count=0,
		max_attempts=DEFAULT_MAX_CLARIFICATION_ATTEMPTS,
		pending_signal={},
	)


def build_pending_clarification_state(
	signal_payload: Dict[str, Any],
	*,
	attempt_count: int = 0,
	max_attempts: int = DEFAULT_MAX_CLARIFICATION_ATTEMPTS,
) -> ClarificationState:
	payload = dict(signal_payload or {})
	if str(payload.get("type") or "").strip() != "qwen_clarification_signal_contract":
		return empty_clarification_state()
	return ClarificationState(
		state="pending",
		attempt_count=int(max(0, attempt_count)),
		max_attempts=int(max(1, max_attempts)),
		pending_signal=payload,
	)


def _parse_payload(raw_value: Any) -> Dict[str, Any]:
	try:
		obj = json.loads(str(raw_value or ""))
	except Exception:
		return {}
	return obj if isinstance(obj, dict) else {}


def clarification_state_from_storage(raw_value: Any) -> ClarificationState:
	payload = _parse_payload(raw_value)
	if not payload:
		return empty_clarification_state()
	payload_type = str(payload.get("type") or "").strip()
	if payload_type == "qwen_pending_clarification_state":
		pending_signal = payload.get("pending_signal")
		if not isinstance(pending_signal, dict):
			return empty_clarification_state()
		return build_pending_clarification_state(
			pending_signal,
			attempt_count=int(max(0, payload.get("attempt_count") or 0)),
			max_attempts=int(max(1, payload.get("max_attempts") or DEFAULT_MAX_CLARIFICATION_ATTEMPTS)),
		)
	if payload_type == "qwen_clarification_signal_contract":
		# Backward compatibility with the pre-5.5A storage shape.
		return build_pending_clarification_state(payload)
	return empty_clarification_state()


def get_clarification_state(session_doc) -> ClarificationState:
	raw_value = str(getattr(session_doc, "pending_clarification_state_json", "") or "").strip()
	return clarification_state_from_storage(raw_value)


def store_clarification_state(session_doc, state: ClarificationState) -> None:
	payload = state.to_storage_payload()
	if not payload:
		session_doc.pending_clarification_state_json = ""
		return
	session_doc.pending_clarification_state_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
