from __future__ import annotations

from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.metadata import get_smoke_fixture_spec


def require_smoke_fixture(fixture_id: str) -> Dict[str, Any]:
	fixture = get_smoke_fixture_spec(fixture_id)
	if fixture:
		return fixture
	raise RuntimeError(f"Smoke fixture '{fixture_id}' is missing from governed metadata.")


def smoke_fixture_initial_message(fixture_id: str) -> str:
	fixture = require_smoke_fixture(fixture_id)
	value = str(fixture.get("initial_message") or "").strip()
	if value:
		return value
	raise RuntimeError(
		f"Smoke fixture '{fixture_id}' is missing initial_message in governed metadata."
	)


def smoke_fixture_replacement_message(fixture_id: str) -> str:
	fixture = require_smoke_fixture(fixture_id)
	value = str(fixture.get("replacement_message") or "").strip()
	if value:
		return value
	raise RuntimeError(
		f"Smoke fixture '{fixture_id}' is missing replacement_message in governed metadata."
	)


def smoke_fixture_reasoning_message(fixture_id: str) -> str:
	fixture = require_smoke_fixture(fixture_id)
	value = str(fixture.get("reasoning_message") or "").strip()
	if value:
		return value
	raise RuntimeError(
		f"Smoke fixture '{fixture_id}' is missing reasoning_message in governed metadata."
	)


def smoke_fixture_followup_messages(fixture_id: str) -> List[str]:
	fixture = require_smoke_fixture(fixture_id)
	return [
		str(item or "").strip()
		for item in (fixture.get("followup_messages") or [])
		if str(item or "").strip()
	]


def smoke_fixture_action_message(fixture_id: str, action_key: str) -> str:
	fixture = require_smoke_fixture(fixture_id)
	action_messages = fixture.get("action_messages") if isinstance(fixture.get("action_messages"), dict) else {}
	value = str(action_messages.get(action_key) or "").strip()
	if value:
		return value
	raise RuntimeError(
		f"Smoke fixture '{fixture_id}' is missing action_messages['{action_key}'] in governed metadata."
	)
