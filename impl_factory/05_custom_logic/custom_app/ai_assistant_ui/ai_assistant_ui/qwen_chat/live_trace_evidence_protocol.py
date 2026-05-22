"""EC-7H live trace evidence fixture and redaction protocol.

This module is intentionally passive: it defines schema/redaction helpers for
review artifacts and test fixtures. It does not collect traces, enforce strict
readiness, or participate in runtime routing.
"""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any, Dict, Iterable, List, Mapping, Sequence

TRACE_PROTOCOL_SLICE_ID = "ec_7h_b_trace_fixture_redaction_protocol"
RUNTIME_EFFECT_NONE = "none"

REDACTED_VALUE = "<redacted>"

REQUIRED_LIVE_TRACE_FIELDS: Sequence[str] = (
	"trace_id",
	"session_id_hash",
	"request_id_hash",
	"scenario_id",
	"lane_id",
	"lane_class",
	"model_role",
	"model_name",
	"fallback_used",
	"fallback_reason",
	"role_compliance",
	"metadata_status",
	"strict_readiness_status",
	"strict_enforcement_ready",
	"runtime_probe_required",
	"metadata_source",
	"authority_source",
	"final_answer_authority_status",
	"final_answer_authority_source",
	"preflight_status",
	"answer_type",
	"authorized_emission.emitted",
	"authorized_emission.blocked",
	"authorized_emission.block_reason",
	"payload_order_summary",
	"assistant_message_count_delta",
	"tool_payload_count_delta",
	"leak_check_result",
	"redaction_status",
)

SAFE_REDACTION_STATUSES = {"redacted", "not_sensitive"}

SENSITIVE_KEY_FRAGMENTS: Sequence[str] = (
	"answer_text",
	"assistant_text",
	"customer",
	"customer_name",
	"docname",
	"document_id",
	"document_name",
	"entity",
	"entity_name",
	"freeform",
	"invoice_id",
	"message_text",
	"model_output",
	"monetary_value",
	"party",
	"prompt",
	"raw_answer",
	"raw_message",
	"raw_model",
	"rendered_response",
	"request_id",
	"session_id",
	"source_text",
	"supplier",
	"user_text",
	"vendor",
	"vendor_name",
)

SENSITIVE_EXACT_KEYS = {
	"customer",
	"docname",
	"document",
	"document_name",
	"entity",
	"invoice",
	"invoice_id",
	"party",
	"request_id",
	"session_id",
	"supplier",
	"vendor",
}

ALLOWED_HASH_IDENTIFIER_KEYS = {"session_id_hash", "request_id_hash"}
HASH_REQUIRED_FIELDS = set(ALLOWED_HASH_IDENTIFIER_KEYS)

ALLOWED_TOP_LEVEL_FIELDS = {
	*(field.split(".", 1)[0] for field in REQUIRED_LIVE_TRACE_FIELDS),
	"extra_metadata",
}

ALLOWED_EXTRA_METADATA_VALUE_TYPES = (str, int, float, bool, type(None))

ALLOWED_EXTRA_METADATA_KEYS = {
	"attempt",
	"capture_version",
	"fixture_version",
	"probe_variant",
	"reviewer_note_classification",
	"schema_version",
	"synthetic",
}

EXTRA_METADATA_INTEGER_KEYS = {"attempt"}
EXTRA_METADATA_BOOLEAN_KEYS = {"synthetic"}
EXTRA_METADATA_VERSION_KEYS = {"capture_version", "fixture_version", "schema_version"}
EXTRA_METADATA_ENUM_VALUES = {
	"probe_variant": {
		"blocked_authority",
		"boundary",
		"fallback",
		"missing_metadata",
		"runtime_error",
		"success",
	},
	"reviewer_note_classification": {
		"none",
		"qa_note",
		"redacted",
		"synthetic",
	},
}
VERSION_EXTRA_METADATA_PATTERN = re.compile(r"^v?\d+(?:\.\d+){0,2}$")

HIGH_RISK_UNKNOWN_KEY_FRAGMENTS: Sequence[str] = (
	"answer",
	"amount",
	"customer",
	"docname",
	"document",
	"entity",
	"evidence",
	"freeform",
	"invoice",
	"message",
	"model",
	"monetary",
	"party",
	"payload",
	"raw",
	"source",
	"supplier",
	"vendor",
	"value",
)

RAW_BUSINESS_TEXT_MARKERS: Sequence[str] = (
	" acme",
	" amount",
	"balance",
	"customer",
	"docname",
	"document",
	"erp source",
	"inv-",
	"invoice",
	"mmk",
	"owes",
	"party",
	"raw ",
	"sinv",
	"supplier",
	" usd",
	"vendor",
)

_MISSING = object()

TRACE_STORAGE_POLICY: Mapping[str, str] = {
	"schema_and_redaction_protocol": "repo_governance_doc",
	"synthetic_redacted_fixture": "repo_allowed",
	"redacted_live_trace_summary": "repo_or_qa_archive_with_owner_approval",
	"raw_live_trace": "external_secure_archive_only",
	"unredacted_sensitive_trace": "not_versioned",
}


def required_live_trace_fields() -> List[str]:
	"""Return the canonical EC-7H live trace fixture field list."""

	return list(REQUIRED_LIVE_TRACE_FIELDS)


def trace_storage_policy() -> Dict[str, str]:
	"""Return the proposed storage policy for EC-7H trace artifacts."""

	return dict(TRACE_STORAGE_POLICY)


def _clean_key(value: Any) -> str:
	return str(value or "").strip().lower()


def _is_sensitive_key(key: Any) -> bool:
	cleaned = _clean_key(key)
	if cleaned in ALLOWED_HASH_IDENTIFIER_KEYS:
		return False
	if cleaned in SENSITIVE_EXACT_KEYS:
		return True
	return any(fragment in cleaned for fragment in SENSITIVE_KEY_FRAGMENTS)


def _is_high_risk_unknown_key(key: Any) -> bool:
	cleaned = _clean_key(key)
	return any(fragment in cleaned for fragment in HIGH_RISK_UNKNOWN_KEY_FRAGMENTS)


def _looks_like_raw_business_text(value: Any) -> bool:
	if not isinstance(value, str) or value in {"", REDACTED_VALUE}:
		return False
	cleaned = f" {value.strip().lower()}"
	return any(marker in cleaned for marker in RAW_BUSINESS_TEXT_MARKERS)


def _is_synthetic_safe_extra_metadata_string(value: Any) -> bool:
	if not isinstance(value, str):
		return False
	if value == REDACTED_VALUE:
		return True
	return False


def _is_allowed_extra_metadata_scalar(key: Any, value: Any) -> bool:
	cleaned_key = str(key)
	if cleaned_key in EXTRA_METADATA_INTEGER_KEYS:
		return isinstance(value, int) and not isinstance(value, bool)
	if cleaned_key in EXTRA_METADATA_BOOLEAN_KEYS:
		return isinstance(value, bool)
	if cleaned_key in EXTRA_METADATA_VERSION_KEYS:
		return value == REDACTED_VALUE or (
			isinstance(value, str)
			and bool(VERSION_EXTRA_METADATA_PATTERN.fullmatch(value))
			and not _looks_like_raw_business_text(value)
		)
	if cleaned_key in EXTRA_METADATA_ENUM_VALUES:
		return value == REDACTED_VALUE or value in EXTRA_METADATA_ENUM_VALUES[cleaned_key]
	return False


def _is_redacted(value: Any) -> bool:
	if value is None:
		return True
	if isinstance(value, str):
		return value == REDACTED_VALUE or value == ""
	if isinstance(value, (int, float, bool)):
		return False
	if isinstance(value, list):
		return all(_is_redacted(item) for item in value)
	if isinstance(value, dict):
		return all(_is_redacted(item) for item in value.values())
	return False


def _get_path(record: Mapping[str, Any], path: str) -> Any:
	current: Any = record
	for part in path.split("."):
		if not isinstance(current, Mapping) or part not in current:
			return _MISSING
		current = current[part]
	return current


def missing_live_trace_fields(record: Mapping[str, Any]) -> List[str]:
	"""Return required EC-7H fields missing from a candidate fixture."""

	missing: List[str] = []
	for field in REQUIRED_LIVE_TRACE_FIELDS:
		value = _get_path(record, field)
		if value is _MISSING or value is None:
			missing.append(field)
	return missing


def _redact_value(value: Any) -> Any:
	if value is None:
		return None
	return REDACTED_VALUE


def redact_live_trace_record(record: Mapping[str, Any]) -> Dict[str, Any]:
	"""Return a redacted copy of a live trace fixture candidate.

	Redaction is key-based so structural metadata remains useful while user text,
	entity names, document IDs, monetary values, and freeform model output are
	replaced before the fixture can be shared or versioned.
	"""

	def redact_extra_metadata_node(node: Any) -> Any:
		if isinstance(node, Mapping):
			redacted: Dict[str, Any] = {}
			for key, value in node.items():
				if _is_sensitive_key(key) or _is_high_risk_unknown_key(key):
					redacted[key] = _redact_value(value)
				elif str(key) in ALLOWED_EXTRA_METADATA_KEYS:
					redacted[key] = redact_allowed_extra_metadata_value(key, value)
				else:
					redacted[key] = redact_unknown_extra_metadata_value(value)
			return redacted
		if isinstance(node, list):
			return [redact_unknown_extra_metadata_value(item) for item in node]
		if isinstance(node, str):
			return REDACTED_VALUE
		return REDACTED_VALUE

	def redact_allowed_extra_metadata_value(key: Any, value: Any) -> Any:
		if _is_allowed_extra_metadata_scalar(key, value):
			return deepcopy(value)
		return REDACTED_VALUE

	def redact_unknown_extra_metadata_value(value: Any) -> Any:
		if isinstance(value, Mapping):
			return redact_extra_metadata_node(value)
		if isinstance(value, list):
			return [redact_unknown_extra_metadata_value(item) for item in value]
		return REDACTED_VALUE

	def redact_node(node: Any, *, top_level: bool = False) -> Any:
		if isinstance(node, Mapping):
			redacted: Dict[str, Any] = {}
			for key, value in node.items():
				if top_level and str(key) not in ALLOWED_TOP_LEVEL_FIELDS:
					continue
				if top_level and str(key) == "extra_metadata":
					redacted[key] = redact_extra_metadata_node(value)
				else:
					redacted[key] = _redact_value(value) if _is_sensitive_key(key) else redact_node(value)
			return redacted
		if isinstance(node, list):
			return [redact_node(item) for item in node]
		return deepcopy(node)

	redacted_record = redact_node(record, top_level=True)
	redacted_record["redaction_status"] = "redacted"
	return redacted_record


def _sensitive_field_violations(record: Mapping[str, Any], prefix: str = "") -> List[str]:
	violations: List[str] = []
	for key, value in record.items():
		path = f"{prefix}.{key}" if prefix else str(key)
		is_unknown_top_level = not prefix and str(key) not in ALLOWED_TOP_LEVEL_FIELDS
		is_extra_metadata_path = path == "extra_metadata" or path.startswith("extra_metadata.")
		key_is_sensitive = _is_sensitive_key(key)
		key_is_high_risk = _is_high_risk_unknown_key(key)
		if key_is_sensitive or (is_unknown_top_level and key_is_high_risk) or (is_extra_metadata_path and key_is_high_risk):
			if not _is_redacted(value):
				violations.append(path)
		elif isinstance(value, Mapping):
			violations.extend(_sensitive_field_violations(value, path))
		elif isinstance(value, list):
			for index, item in enumerate(value):
				if isinstance(item, Mapping):
					violations.extend(_sensitive_field_violations(item, f"{path}[{index}]"))
	return violations


def _unknown_top_level_fields(record: Mapping[str, Any]) -> List[str]:
	return sorted(str(key) for key in record.keys() if str(key) not in ALLOWED_TOP_LEVEL_FIELDS)


def _extra_metadata_violations(value: Any, prefix: str = "extra_metadata") -> List[str]:
	violations: List[str] = []
	if value is None:
		return violations
	if not isinstance(value, Mapping):
		return [prefix]
	for key, item in value.items():
		path = f"{prefix}.{key}"
		if _is_sensitive_key(key) or _is_high_risk_unknown_key(key):
			if not _is_redacted(item):
				violations.append(path)
			continue
		if str(key) in ALLOWED_EXTRA_METADATA_KEYS:
			if not _is_allowed_extra_metadata_scalar(key, item):
				violations.append(path)
			continue
		violations.extend(_unknown_extra_metadata_value_violations(item, path))
	return violations


def _unknown_extra_metadata_value_violations(value: Any, prefix: str) -> List[str]:
	violations: List[str] = []
	if isinstance(value, Mapping):
		violations.extend(_extra_metadata_violations(value, prefix))
	elif isinstance(value, list):
		for index, child in enumerate(value):
			violations.extend(_unknown_extra_metadata_value_violations(child, f"{prefix}[{index}]"))
	elif isinstance(value, str):
		if value != REDACTED_VALUE:
			violations.append(prefix)
	else:
		violations.append(prefix)
	return violations


def validate_live_trace_fixture(record: Mapping[str, Any]) -> Dict[str, Any]:
	"""Validate a redacted EC-7H live trace fixture shape.

	The validator is deliberately evidence-only. It reports schema/redaction
	problems but never blocks runtime execution or changes answer behavior.
	"""

	missing = missing_live_trace_fields(record)
	redaction_status = _clean_key(record.get("redaction_status"))
	redaction_violations = _sensitive_field_violations(record)
	unknown_field_violations = _unknown_top_level_fields(record)
	extra_metadata_violations = _extra_metadata_violations(record.get("extra_metadata"))
	hash_field_violations = [
		field
		for field in HASH_REQUIRED_FIELDS
		if _get_path(record, field) is _MISSING or _get_path(record, field) in {None, "", REDACTED_VALUE}
	]
	schema_violations = sorted(set(unknown_field_violations + extra_metadata_violations))
	valid = (
		not missing
		and not redaction_violations
		and not hash_field_violations
		and not schema_violations
		and redaction_status in SAFE_REDACTION_STATUSES
	)
	return {
		"slice_id": TRACE_PROTOCOL_SLICE_ID,
		"runtime_effect": RUNTIME_EFFECT_NONE,
		"valid": valid,
		"missing_fields": missing,
		"redaction_status": redaction_status,
		"redaction_violations": redaction_violations,
		"hash_field_violations": hash_field_violations,
		"unknown_field_violations": unknown_field_violations,
		"schema_violations": schema_violations,
	}


def build_minimal_redacted_live_trace_fixture(**overrides: Any) -> Dict[str, Any]:
	"""Build a safe synthetic fixture for tests and documentation examples."""

	fixture: Dict[str, Any] = {
		"trace_id": "trace_fixture_001",
		"session_id_hash": "sha256:session-fixture",
		"request_id_hash": "sha256:request-fixture",
		"scenario_id": "ec7h_fixture_success",
		"lane_id": "frontdoor_semantic_classification",
		"lane_class": "ai_semantic",
		"model_role": "light_semantic",
		"model_name": "qwen-fixture",
		"fallback_used": False,
		"fallback_reason": "",
		"role_compliance": "compliant",
		"metadata_status": "covered",
		"strict_readiness_status": "strict_ready",
		"strict_enforcement_ready": True,
		"runtime_probe_required": False,
		"metadata_source": "runtime_metadata_envelope",
		"authority_source": "semantic_runtime_metadata",
		"final_answer_authority_status": "not_applicable",
		"final_answer_authority_source": "not_applicable",
		"preflight_status": "passed",
		"answer_type": "metadata_provenance",
		"authorized_emission": {
			"emitted": False,
			"blocked": False,
			"block_reason": "",
		},
		"payload_order_summary": ["runtime_metadata_envelope", "qwen_tool_trace"],
		"assistant_message_count_delta": 0,
		"tool_payload_count_delta": 2,
		"leak_check_result": "no_sensitive_payload_leak",
		"redaction_status": "redacted",
	}
	fixture.update(overrides)
	return fixture
