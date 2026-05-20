from __future__ import annotations

import json
import time
from typing import Any, Dict


_TRANSIENT_DB_ERROR_NAMES = {"QueryDeadlockError", "QueryTimeoutError"}
_TRANSIENT_DB_ERROR_MARKERS = (
	"lock wait timeout exceeded",
	"deadlock found when trying to get lock",
)
_TIMESTAMP_MISMATCH_ERROR_NAMES = {"TimestampMismatchError"}
_TIMESTAMP_MISMATCH_ERROR_MARKERS = (
	"has been modified after you have opened it",
)
_SAVE_RETRY_DELAYS_SECONDS = (0.05, 0.1, 0.2, 0.4)


def safe_json_dumps(obj: Any) -> str:
	try:
		return json.dumps(obj, ensure_ascii=False, default=str)
	except Exception:
		try:
			return json.dumps({"type": "text", "text": str(obj or "")}, ensure_ascii=False)
		except Exception:
			return "{\"type\":\"text\",\"text\":\"Internal serialization error.\"}"


def _is_transient_session_save_error(exc: Exception) -> bool:
	error_name = type(exc).__name__
	if error_name in _TRANSIENT_DB_ERROR_NAMES:
		return True
	error_text = str(exc or "").strip().lower()
	return any(marker in error_text for marker in _TRANSIENT_DB_ERROR_MARKERS)


def _is_timestamp_mismatch_session_save_error(exc: Exception) -> bool:
	error_name = type(exc).__name__
	if error_name in _TIMESTAMP_MISMATCH_ERROR_NAMES:
		return True
	error_text = str(exc or "").strip().lower()
	return any(marker in error_text for marker in _TIMESTAMP_MISMATCH_ERROR_MARKERS)


def _rollback_session_transaction() -> None:
	try:
		import frappe  # type: ignore
	except Exception:
		return
	try:
		db = getattr(frappe, "db", None)
		if db is not None and hasattr(db, "rollback"):
			db.rollback()
	except Exception:
		return


def _snapshot_message_rows(session_doc: Any) -> list[dict[str, str]]:
	rows = session_doc.get("messages") if hasattr(session_doc, "get") else []
	if not isinstance(rows, list):
		return []
	out: list[dict[str, str]] = []
	for row in rows:
		role = str(getattr(row, "role", "") or (row.get("role") if isinstance(row, dict) else "") or "").strip()
		content = str(getattr(row, "content", "") or (row.get("content") if isinstance(row, dict) else "") or "")
		if not role and not content:
			continue
		out.append({"role": role, "content": content})
	return out


def _reload_and_restore_append_only_session_state(session_doc: Any, snapshot: dict[str, Any]) -> bool:
	reload_method = getattr(session_doc, "reload", None)
	if callable(reload_method):
		reload_method()
	else:
		load_from_db = getattr(session_doc, "load_from_db", None)
		if not callable(load_from_db):
			return False
		load_from_db()

	current_messages = _snapshot_message_rows(session_doc)
	target_messages = list(snapshot.get("messages") or [])
	if len(current_messages) > len(target_messages):
		return False
	if current_messages != target_messages[: len(current_messages)]:
		return False
	for row in target_messages[len(current_messages) :]:
		session_doc.append("messages", dict(row))
	if hasattr(session_doc, "pending_clarification_state_json"):
		setattr(
			session_doc,
			"pending_clarification_state_json",
			str(snapshot.get("pending_clarification_state_json") or ""),
		)
	return True


def _restore_session_state_after_retryable_error(session_doc: Any, snapshot: dict[str, Any]) -> bool:
	try:
		return _reload_and_restore_append_only_session_state(session_doc, snapshot)
	except Exception:
		return False


class SessionContext:
	"""Thin mutation wrapper used to make session writes explicit during refactor."""

	def __init__(self, session_doc: Any):
		self.session_doc = session_doc

	def append_message(self, role: str, content: str) -> None:
		self.session_doc.append("messages", {"role": str(role or "").strip(), "content": str(content or "")})

	def append_tool_payload(self, payload: Dict[str, Any]) -> None:
		self.append_message("tool", safe_json_dumps(payload))

	def save(self, *, ignore_permissions: bool = False) -> None:
		last_error: Exception | None = None
		snapshot = {
			"messages": _snapshot_message_rows(self.session_doc),
			"pending_clarification_state_json": str(
				getattr(self.session_doc, "pending_clarification_state_json", "") or ""
			),
		}
		for attempt, delay_seconds in enumerate((0.0, *_SAVE_RETRY_DELAYS_SECONDS), start=1):
			try:
				self.session_doc.save(ignore_permissions=ignore_permissions)
				return
			except Exception as exc:
				last_error = exc
				if _is_timestamp_mismatch_session_save_error(exc) and attempt <= len(_SAVE_RETRY_DELAYS_SECONDS):
					_rollback_session_transaction()
					if not _restore_session_state_after_retryable_error(self.session_doc, snapshot):
						raise
					time.sleep(delay_seconds)
					continue
				if not _is_transient_session_save_error(exc) or attempt > len(_SAVE_RETRY_DELAYS_SECONDS):
					raise
				_rollback_session_transaction()
				_restore_session_state_after_retryable_error(self.session_doc, snapshot)
				time.sleep(delay_seconds)
		if last_error is not None:
			raise last_error


def append_message(session_doc: Any, role: str, content: str) -> None:
	SessionContext(session_doc).append_message(role, content)


def append_tool_payload(session_doc: Any, payload: Dict[str, Any]) -> None:
	SessionContext(session_doc).append_tool_payload(payload)


def save_session(session_doc: Any, *, ignore_permissions: bool = False) -> None:
	SessionContext(session_doc).save(ignore_permissions=ignore_permissions)
