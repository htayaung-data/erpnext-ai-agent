from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Set

from ai_assistant_ui.qwen_chat.metadata import load_smoke_fixture_registry


@dataclass(frozen=True)
class SmokeFixtureRegistryValidationResult:
	status: str
	errors: List[str]
	warnings: List[str]
	stats: Dict[str, Any]

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_smoke_fixture_registry_validation",
			"contract_version": "1.0",
			"status": self.status,
			"errors": list(self.errors),
			"warnings": list(self.warnings),
			"stats": dict(self.stats),
		}


def _as_str_list(value: Any) -> List[str]:
	if not isinstance(value, list):
		return []
	return [str(item or "").strip() for item in value if str(item or "").strip()]


def _as_str_dict(value: Any) -> Dict[str, str]:
	if not isinstance(value, dict):
		return {}
	result: Dict[str, str] = {}
	for key, item in value.items():
		normalized_key = str(key or "").strip()
		normalized_value = str(item or "").strip()
		if normalized_key and normalized_value:
			result[normalized_key] = normalized_value
	return result


def validate_smoke_fixture_registry(
	payload: Dict[str, Any] | None = None,
) -> SmokeFixtureRegistryValidationResult:
	data = payload if isinstance(payload, dict) else load_smoke_fixture_registry()
	errors: List[str] = []
	warnings: List[str] = []

	if str(data.get("contract_version") or "").strip() != "1.0":
		errors.append("contract_version must be '1.0'.")

	fixtures = data.get("fixtures")
	if not isinstance(fixtures, list) or not fixtures:
		errors.append("fixtures must be a non-empty list.")
		fixtures = []

	seen_ids: Set[str] = set()
	for idx, fixture in enumerate(fixtures):
		if not isinstance(fixture, dict):
			errors.append(f"fixtures[{idx}] must be an object.")
			continue
		fixture_kind = str(fixture.get("fixture_kind") or "artifact_flow").strip()
		fixture_id = str(fixture.get("fixture_id") or "").strip()
		if not fixture_id:
			errors.append(f"fixtures[{idx}].fixture_id must be a non-empty string.")
		elif fixture_id in seen_ids:
			errors.append(f"fixtures contains duplicate fixture_id '{fixture_id}'.")
		seen_ids.add(fixture_id)

		fixture_family = str(fixture.get("fixture_family") or "").strip()
		if not fixture_family:
			errors.append(f"fixtures[{idx}].fixture_family must be a non-empty string.")

		initial_message = str(fixture.get("initial_message") or "").strip()
		expected_initial_source_name = str(fixture.get("expected_initial_source_name") or "").strip()
		if fixture_kind != "interaction_actions":
			if not initial_message:
				errors.append(f"fixtures[{idx}].initial_message must be a non-empty string.")
			if not expected_initial_source_name:
				errors.append(f"fixtures[{idx}].expected_initial_source_name must be a non-empty string.")

		followup_messages = _as_str_list(fixture.get("followup_messages"))
		replacement_message = str(fixture.get("replacement_message") or "").strip()
		action_messages = _as_str_dict(fixture.get("action_messages"))
		message_mode_count = int(bool(followup_messages)) + int(bool(replacement_message)) + int(bool(action_messages))
		if message_mode_count == 0:
			errors.append(
				f"fixtures[{idx}] must define followup_messages, replacement_message, or action_messages."
			)
		if message_mode_count > 1:
			errors.append(
				f"fixtures[{idx}] must not define more than one message mode."
			)
		if followup_messages:
			if len(set(followup_messages)) != len(followup_messages):
				errors.append(f"fixtures[{idx}].followup_messages must not contain duplicates.")
			if not str(fixture.get("expected_family_id") or "").strip():
				errors.append(
					f"fixtures[{idx}].expected_family_id must be a non-empty string when followup_messages are used."
				)
		if replacement_message:
			expected_replacement_source_names = _as_str_list(
				fixture.get("expected_replacement_source_names")
			)
			if not expected_replacement_source_names:
				errors.append(
					f"fixtures[{idx}].expected_replacement_source_names must be a non-empty list when replacement_message is used."
				)
		if action_messages:
			if len(set(action_messages)) != len(action_messages):
				errors.append(f"fixtures[{idx}].action_messages must not contain duplicate keys.")
			if fixture_kind != "interaction_actions" and not str(fixture.get("expected_family_id") or "").strip():
				errors.append(
					f"fixtures[{idx}].expected_family_id must be a non-empty string when action_messages are used."
				)

	status = "pass" if not errors else "fail"
	return SmokeFixtureRegistryValidationResult(
		status=status,
		errors=errors,
		warnings=warnings,
		stats={"fixture_count": len(fixtures), "fixture_ids": sorted(seen_ids)},
	)
