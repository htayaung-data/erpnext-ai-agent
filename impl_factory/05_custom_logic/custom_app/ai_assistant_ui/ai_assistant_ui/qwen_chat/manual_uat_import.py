from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from .manual_uat_archive import build_manual_uat_archive_index
from .manual_uat_evidence import (
	MANUAL_UAT_STATUS_BLOCKED,
	MANUAL_UAT_STATUS_FAIL,
	MANUAL_UAT_STATUS_NOT_RUN,
	MANUAL_UAT_STATUS_PASS,
	REQUIRED_OBSERVED_MODEL_ROLE_KEYS,
	REQUIRED_OBSERVED_TRACE_KEYS,
	VALID_MANUAL_UAT_STATUSES,
)
from .natural_business_understanding_contracts import CONTRACT_VERSION
from .regression_scenario_packs import (
	S7_REGRESSION_SCENARIO_REGISTRY,
	build_regression_scenario_contract,
)


MANUAL_UAT_IMPORT_RECORD_CONTRACT_TYPE = "qwen_manual_uat_import_record_contract"
MANUAL_UAT_IMPORT_BATCH_CONTRACT_TYPE = "qwen_manual_uat_import_batch_contract"
MANUAL_UAT_IMPORT_SUITE_ID = "s7_manual_uat_evidence_import_contracts"

IMPORT_PARSE_ACCEPTED = "accepted"
IMPORT_PARSE_BLOCKED = "blocked"
IMPORT_PARSE_QUARANTINED = "quarantined"

REQUIRED_IMPORT_ENVELOPE_FIELDS = [
	"scenario_id",
	"reviewer",
	"captured_at",
	"capture_source",
	"uat_status",
	"failure_reason",
	"raw_answer_text",
	"raw_trace_text",
	"observed_answer_summary",
]

FINAL_ANSWER_AUTHORITY_FIELDS = [
	"authority_source",
	"evidence_scope",
	"selected_artifact_id",
	"selected_report_family",
	"selected_row_reference",
	"policy_boundary",
	"answer_mode",
	"authority_complete",
	"preflight_status",
	"missing_fields",
]

REQUIRED_FINAL_ANSWER_AUTHORITY_KEYS = [
	"authority_source",
	"evidence_scope",
	"answer_mode",
	"authority_complete",
	"preflight_status",
]

DEFAULT_MANUAL_UAT_IMPORT_JSON_PATH = (
	"impl_factory/00_governance/current_docs/generated/"
	"qwen_s7_manual_uat_evidence_import_batch.json"
)
DEFAULT_MANUAL_UAT_IMPORT_MARKDOWN_PATH = (
	"impl_factory/00_governance/current_docs/generated/"
	"qwen_s7_manual_uat_evidence_import_batch.md"
)

TAB_SEPARATOR = chr(9)

_SECTION_ALIASES = {
	"observed_trace_fields": {
		"observed_trace_fields",
		"normalized_trace_evidence",
		"trace_evidence",
	},
	"observed_model_role_fields": {
		"observed_model_role_fields",
		"normalized_model_role_evidence",
		"model_role_evidence",
	},
	"authority_summary": {"authority_summary"},
	"semantic_ownership_ledger": {"semantic_ownership_ledger"},
	"policy_boundary_uniformity": {"policy_boundary_uniformity"},
	"final_answer_authority": {"final_answer_authority"},
	"model_role_observability": {"model_role_observability"},
}

_TRACE_FIELD_SOURCES = {
	"route": [
		("observed_trace_fields", "route"),
		("authority_summary", "route"),
		("final_answer_authority", "route"),
	],
	"artifact_family": [
		("observed_trace_fields", "artifact_family"),
		("authority_summary", "selected_report_family"),
		("semantic_ownership_ledger", "ledger_report_family"),
		("final_answer_authority", "selected_report_family"),
	],
	"entity_type": [
		("observed_trace_fields", "entity_type"),
		("authority_summary", "selected_object_type"),
		("semantic_ownership_ledger", "ledger_entity_type"),
		("final_answer_authority", "selected_entity_type"),
		("policy_boundary_uniformity", "entity_type"),
	],
	"row_reference": [
		("observed_trace_fields", "row_reference"),
		("semantic_ownership_ledger", "ledger_row_reference"),
		("final_answer_authority", "selected_row_reference"),
	],
	"authority_source": [
		("observed_trace_fields", "authority_source"),
		("semantic_ownership_ledger", "authority_source"),
		("final_answer_authority", "authority_source"),
	],
	"policy_boundary": [
		("observed_trace_fields", "policy_boundary"),
		("semantic_ownership_ledger", "policy_boundary"),
		("policy_boundary_uniformity", "policy_boundary"),
		("final_answer_authority", "policy_boundary"),
	],
	"answer_mode": [
		("observed_trace_fields", "answer_mode"),
		("final_answer_authority", "answer_mode"),
		("policy_boundary_uniformity", "allowed_answer_mode"),
	],
}

_MODEL_ROLE_FIELD_SOURCES = {
	"model_role_lane": [
		("observed_model_role_fields", "model_role_lane"),
		("model_role_observability", "model_role_lane"),
	],
	"lane": [
		("observed_model_role_fields", "lane"),
		("model_role_observability", "lane"),
	],
	"model_role": [
		("observed_model_role_fields", "model_role"),
		("model_role_observability", "model_role"),
	],
	"expected_model_role": [
		("observed_model_role_fields", "expected_model_role"),
		("model_role_observability", "expected_model_role"),
	],
	"role_compliance": [
		("observed_model_role_fields", "role_compliance"),
		("model_role_observability", "role_compliance"),
	],
}


def _utc_now() -> str:
	return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _clean_records(values: Iterable[Dict[str, Any]] | None) -> List[Dict[str, Any]]:
	return [dict(value) for value in values or [] if isinstance(value, dict)]


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


def _normalized_key(value: Any) -> str:
	return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", _clean_text(value).lower())).strip("_")


def _scenario_map(registry: Iterable[Dict[str, Any]] | None = None) -> Dict[str, Dict[str, Any]]:
	scenarios: Dict[str, Dict[str, Any]] = {}
	for entry in registry or S7_REGRESSION_SCENARIO_REGISTRY:
		if not isinstance(entry, dict):
			continue
		scenario = build_regression_scenario_contract(entry)
		scenario_id = _clean_text(scenario.get("scenario_id"))
		if scenario_id:
			scenarios[scenario_id] = scenario
	return scenarios


def _scenario_ids(registry: Iterable[Dict[str, Any]] | None = None) -> List[str]:
	return list(_scenario_map(registry).keys())


def _section_key(line: str) -> str:
	normalized = _normalized_key(line.rstrip(":"))
	for section_key, aliases in _SECTION_ALIASES.items():
		if normalized in aliases:
			return section_key
	return ""


def _markdown_cells(line: str) -> List[str]:
	text = _clean_text(line)
	if not text.startswith("|") or "|" not in text[1:]:
		return []
	cells = [cell.strip() for cell in text.strip("|").split("|")]
	if len(cells) < 2:
		return []
	if all(set(cell) <= {"-", ":"} for cell in cells if cell):
		return []
	if _normalized_key(cells[0]) == "field" and _normalized_key(cells[1]) == "value":
		return []
	return cells


def _field_value_from_line(line: str) -> Tuple[str, str]:
	cells = _markdown_cells(line)
	if len(cells) >= 2:
		return cells[0], cells[1]
	text = _clean_text(line)
	if TAB_SEPARATOR in text:
		field, value = text.split(TAB_SEPARATOR, 1)
		return field, value
	if ":" in text:
		field, value = text.split(":", 1)
		if len(field) <= 80:
			return field, value
	return "", ""


def parse_capture_tables(raw_trace_text: str) -> Dict[str, Dict[str, str]]:
	sections: Dict[str, Dict[str, str]] = {section_key: {} for section_key in _SECTION_ALIASES}
	current_section = ""
	for raw_line in _clean_text(raw_trace_text).replace("\ufeff", "").splitlines():
		line = _clean_text(raw_line)
		if not line:
			continue
		section_key = _section_key(line)
		if section_key:
			current_section = section_key
			continue
		if not current_section:
			continue
		field, value = _field_value_from_line(line)
		field_key = _normalized_key(field)
		value_text = _clean_text(value)
		if field_key and value_text:
			sections[current_section][field_key] = value_text
	return sections


def _first_section_value(sections: Dict[str, Dict[str, str]], sources: List[Tuple[str, str]]) -> str:
	for section_key, field_key in sources:
		value = _clean_text(_clean_dict(sections.get(section_key)).get(field_key))
		if value:
			return value
	return ""


def _merge_supplied_fields(parsed_fields: Dict[str, str], supplied_fields: Dict[str, Any]) -> Dict[str, str]:
	merged = dict(parsed_fields)
	for key, value in supplied_fields.items():
		field_key = _normalized_key(key)
		if field_key and _clean_text(value) and not merged.get(field_key):
			merged[field_key] = _clean_text(value)
	return merged


def extract_observed_trace_fields(raw_trace_text: str, supplied_fields: Dict[str, Any] | None = None) -> Dict[str, str]:
	sections = parse_capture_tables(raw_trace_text)
	if supplied_fields:
		sections["observed_trace_fields"] = _merge_supplied_fields(
			sections.get("observed_trace_fields", {}),
			supplied_fields,
		)
	return {
		key: _first_section_value(sections, sources)
		for key, sources in _TRACE_FIELD_SOURCES.items()
	}


def extract_observed_model_role_fields(
	raw_trace_text: str,
	supplied_fields: Dict[str, Any] | None = None,
) -> Dict[str, str]:
	sections = parse_capture_tables(raw_trace_text)
	if supplied_fields:
		sections["observed_model_role_fields"] = _merge_supplied_fields(
			sections.get("observed_model_role_fields", {}),
			supplied_fields,
		)
	fields = {
		key: _first_section_value(sections, sources)
		for key, sources in _MODEL_ROLE_FIELD_SOURCES.items()
	}
	if not fields.get("model_role_lane") and fields.get("lane") and fields.get("model_role"):
		fields["model_role_lane"] = f"{fields['lane']}:{fields['model_role']}"
	return fields


def _section_value(sections: Dict[str, Dict[str, str]], section_key: str, *field_keys: str) -> str:
	section = _clean_dict(sections.get(section_key))
	for field_key in field_keys:
		value = _clean_text(section.get(_normalized_key(field_key)))
		if value:
			return value
	return ""


def extract_final_answer_authority_fields(
	raw_trace_text: str,
	supplied_fields: Dict[str, Any] | None = None,
) -> Dict[str, str]:
	sections = parse_capture_tables(raw_trace_text)
	if supplied_fields:
		sections["final_answer_authority"] = _merge_supplied_fields(
			sections.get("final_answer_authority", {}),
			supplied_fields,
		)
	return {
		"authority_source": _section_value(sections, "final_answer_authority", "authority_source"),
		"evidence_scope": _section_value(sections, "final_answer_authority", "evidence_scope"),
		"selected_artifact_id": _section_value(
			sections,
			"final_answer_authority",
			"selected_artifact_id",
			"selected_artifact",
		),
		"selected_report_family": _section_value(sections, "final_answer_authority", "selected_report_family"),
		"selected_row_reference": _section_value(sections, "final_answer_authority", "selected_row_reference"),
		"policy_boundary": _section_value(sections, "final_answer_authority", "policy_boundary"),
		"answer_mode": _section_value(sections, "final_answer_authority", "answer_mode"),
		"authority_complete": _section_value(sections, "final_answer_authority", "authority_complete"),
		"preflight_status": _section_value(sections, "final_answer_authority", "preflight_status"),
		"missing_fields": _section_value(sections, "final_answer_authority", "missing_fields"),
	}


def _truthy_authority_value(value: Any) -> bool:
	return _clean_text(value).lower() in {"true", "1", "yes"}


def _none_like_authority_value(value: Any) -> bool:
	text = _clean_text(value).lower()
	return not text or text in {"none", "[]", "null", "-"}


def _missing_final_answer_authority_fields(fields: Dict[str, str]) -> List[str]:
	final_fields = _clean_dict(fields)
	missing = [
		f"final_answer_authority.{key}"
		for key in REQUIRED_FINAL_ANSWER_AUTHORITY_KEYS
		if not _clean_text(final_fields.get(key))
	]
	authority_source = _clean_text(final_fields.get("authority_source"))
	policy_boundary = _clean_text(final_fields.get("policy_boundary"))
	if _clean_text(final_fields.get("authority_complete")) and not _truthy_authority_value(final_fields.get("authority_complete")):
		missing.append("final_answer_authority.authority_complete_true")
	preflight_status = _clean_text(final_fields.get("preflight_status"))
	if preflight_status and preflight_status not in {"passed", "bounded"}:
		missing.append("final_answer_authority.preflight_status_allowed")
	if not _none_like_authority_value(final_fields.get("missing_fields")):
		missing.append("final_answer_authority.missing_fields_none")
	if authority_source == "visible_rendered_table":
		for key in ("selected_artifact_id", "selected_report_family"):
			if not _clean_text(final_fields.get(key)):
				missing.append(f"final_answer_authority.{key}")
	elif authority_source == "governed_erp_report":
		if not _clean_text(final_fields.get("selected_report_family")):
			missing.append("final_answer_authority.selected_report_family")
	elif authority_source == "policy_boundary":
		if not policy_boundary or policy_boundary == "none":
			missing.append("final_answer_authority.policy_boundary")
	return sorted(dict.fromkeys(missing))


def _raw_evidence_hash(source: Dict[str, Any]) -> str:
	payload = {
		"capture_source": _clean_text(source.get("capture_source")),
		"raw_answer_text": _clean_text(source.get("raw_answer_text")),
		"raw_trace_text": _clean_text(source.get("raw_trace_text")),
		"scenario_id": _clean_text(source.get("scenario_id")),
	}
	return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _answer_summary(raw_answer_text: str, supplied_summary: str = "") -> str:
	summary = _clean_text(supplied_summary)
	if summary:
		return summary
	for line in _clean_text(raw_answer_text).splitlines():
		text = _clean_text(line)
		if text:
			return text[:240]
	return ""


def _input_status(source: Dict[str, Any]) -> str:
	return _clean_text(source.get("uat_status")) or _clean_text(source.get("status")) or MANUAL_UAT_STATUS_NOT_RUN


def _missing_capture_fields(
	*,
	raw_answer_text: str,
	raw_trace_text: str,
	status: str,
	failure_reason: str,
	observed_trace_fields: Dict[str, str],
	observed_model_role_fields: Dict[str, str],
	final_answer_authority_fields: Dict[str, str],
) -> List[str]:
	missing: List[str] = []
	if not raw_answer_text:
		missing.append("raw_answer_text")
	if not raw_trace_text:
		missing.append("raw_trace_text")
	if status not in VALID_MANUAL_UAT_STATUSES:
		missing.append("uat_status")
	if status in {MANUAL_UAT_STATUS_FAIL, MANUAL_UAT_STATUS_BLOCKED} and not failure_reason:
		missing.append("failure_reason")
	missing.extend(
		[f"observed_trace_fields.{key}" for key in REQUIRED_OBSERVED_TRACE_KEYS if not _clean_text(observed_trace_fields.get(key))]
	)
	missing.extend(
		[
			f"observed_model_role_fields.{key}"
			for key in REQUIRED_OBSERVED_MODEL_ROLE_KEYS
			if not _clean_text(observed_model_role_fields.get(key))
		]
	)
	missing.extend(_missing_final_answer_authority_fields(final_answer_authority_fields))
	return missing


def _parse_status(
	*,
	scenario_registered: bool,
	raw_trace_text: str,
	parsed_sections: Dict[str, Dict[str, str]],
	missing_capture_sections: List[str],
	field_mismatches: List[Dict[str, str]],
	status_valid: bool,
) -> Tuple[str, str]:
	if not scenario_registered:
		return IMPORT_PARSE_QUARANTINED, "unknown_scenario"
	if raw_trace_text and not any(parsed_sections.values()):
		return IMPORT_PARSE_QUARANTINED, "trace_not_structured"
	if missing_capture_sections or field_mismatches or not status_valid:
		return IMPORT_PARSE_BLOCKED, ""
	return IMPORT_PARSE_ACCEPTED, ""


def build_manual_uat_import_record(
	capture_record: Dict[str, Any],
	*,
	registry: Iterable[Dict[str, Any]] | None = None,
	import_batch_id: str = "",
	captured_at: str = "",
	reviewer: str = "",
) -> Dict[str, Any]:
	source = dict(capture_record or {})
	scenario_id = _clean_text(source.get("scenario_id"))
	scenario = _scenario_map(registry).get(scenario_id)
	raw_answer_text = _clean_text(source.get("raw_answer_text"))
	raw_trace_text = _clean_text(source.get("raw_trace_text"))
	status = _input_status(source)
	failure_reason = _clean_text(source.get("failure_reason"))
	parsed_sections = parse_capture_tables(raw_trace_text)
	observed_trace_fields = extract_observed_trace_fields(raw_trace_text, _clean_dict(source.get("observed_trace_fields")))
	observed_model_role_fields = extract_observed_model_role_fields(
		raw_trace_text,
		_clean_dict(source.get("observed_model_role_fields")),
	)
	final_answer_authority_fields = extract_final_answer_authority_fields(
		raw_trace_text,
		_clean_dict(source.get("final_answer_authority")),
	)
	record_captured_at = _clean_text(source.get("captured_at")) or _clean_text(captured_at) or _utc_now()
	record_reviewer = _clean_text(source.get("reviewer")) or _clean_text(reviewer)
	archive_import_record = {
		"scenario_id": scenario_id,
		"observed_answer_summary": _answer_summary(raw_answer_text, _clean_text(source.get("observed_answer_summary"))),
		"observed_trace_fields": observed_trace_fields,
		"observed_model_role_fields": observed_model_role_fields,
		"uat_status": status,
		"failure_reason": failure_reason,
		"reviewed_at": record_captured_at,
		"reviewer": record_reviewer,
	}
	archive_index = build_manual_uat_archive_index(
		[archive_import_record],
		registry=registry,
		expected_scenario_ids=[scenario_id] if scenario_id else [],
		generated_at=record_captured_at,
		reviewer=record_reviewer,
	)
	archive_record = dict((archive_index.get("records") or [{}])[0])
	field_mismatches = list(archive_record.get("mismatches") or [])
	missing_capture_sections = _missing_capture_fields(
		raw_answer_text=raw_answer_text,
		raw_trace_text=raw_trace_text,
		status=status,
		failure_reason=failure_reason,
		observed_trace_fields=observed_trace_fields,
		observed_model_role_fields=observed_model_role_fields,
		final_answer_authority_fields=final_answer_authority_fields,
	)
	parse_status, quarantine_reason = _parse_status(
		scenario_registered=bool(scenario),
		raw_trace_text=raw_trace_text,
		parsed_sections=parsed_sections,
		missing_capture_sections=missing_capture_sections,
		field_mismatches=field_mismatches,
		status_valid=status in VALID_MANUAL_UAT_STATUSES,
	)
	return {
		"type": MANUAL_UAT_IMPORT_RECORD_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"import_record_id": f"{_clean_text(import_batch_id) or 'manual-uat-import'}:{scenario_id or 'unknown'}",
		"import_batch_id": _clean_text(import_batch_id),
		"scenario_id": scenario_id,
		"scenario_registered": bool(scenario),
		"scenario_pack": _clean_text((scenario or {}).get("pack_id")),
		"family": _clean_text((scenario or {}).get("family")),
		"reviewer": record_reviewer,
		"captured_at": record_captured_at,
		"capture_source": _clean_text(source.get("capture_source")) or "manual_browser_uat",
		"raw_answer_text": raw_answer_text,
		"raw_trace_text": raw_trace_text,
		"raw_evidence_hash": _raw_evidence_hash(source),
		"observed_answer_summary": archive_import_record["observed_answer_summary"],
		"observed_trace_fields": observed_trace_fields,
		"observed_model_role_fields": observed_model_role_fields,
		"final_answer_authority_fields": final_answer_authority_fields,
		"uat_status": status,
		"status_valid": status in VALID_MANUAL_UAT_STATUSES,
		"parse_status": parse_status,
		"missing_capture_sections": missing_capture_sections,
		"field_mismatches": field_mismatches,
		"quarantine_reason": quarantine_reason,
		"archive_import_record": archive_import_record,
		"archive_record_contract": archive_record,
		"release_blocking": bool(archive_record.get("release_blocking")) or parse_status != IMPORT_PARSE_ACCEPTED,
	}


def _status_counts(records: List[Dict[str, Any]]) -> Dict[str, int]:
	counts = {
		IMPORT_PARSE_ACCEPTED: 0,
		IMPORT_PARSE_BLOCKED: 0,
		IMPORT_PARSE_QUARANTINED: 0,
	}
	for record in records:
		status = _clean_text(record.get("parse_status"))
		if status in counts:
			counts[status] += 1
	return counts


def _duplicate_values(values: List[str]) -> List[str]:
	return sorted({value for value in values if value and values.count(value) > 1})


def build_manual_uat_import_batch(
	capture_records: Iterable[Dict[str, Any]] | None = None,
	*,
	registry: Iterable[Dict[str, Any]] | None = None,
	expected_scenario_ids: Iterable[str] | None = None,
	import_batch_id: str = "s7_manual_uat_evidence_import_batch",
	generated_at: str = "",
	reviewer: str = "",
	json_artifact_path: str = DEFAULT_MANUAL_UAT_IMPORT_JSON_PATH,
	markdown_artifact_path: str = DEFAULT_MANUAL_UAT_IMPORT_MARKDOWN_PATH,
	contract_owner: str = "s7_manual_uat_evidence_import",
) -> Dict[str, Any]:
	generated_at_text = _clean_text(generated_at) or _utc_now()
	records = [
		build_manual_uat_import_record(
			record,
			registry=registry,
			import_batch_id=import_batch_id,
			captured_at=generated_at_text,
			reviewer=reviewer,
		)
		for record in _clean_records(capture_records)
	]
	expected_ids = (
		[_clean_text(value) for value in expected_scenario_ids if _clean_text(value)]
		if expected_scenario_ids is not None
		else _scenario_ids(registry)
	)
	archive_import_records = [
		record.get("archive_import_record")
		for record in records
		if isinstance(record.get("archive_import_record"), dict)
	]
	archive_index = build_manual_uat_archive_index(
		archive_import_records,
		registry=registry,
		expected_scenario_ids=expected_ids,
		generated_at=generated_at_text,
		reviewer=reviewer,
	)
	counts = _status_counts(records)
	duplicate_import_record_ids = _duplicate_values([_clean_text(record.get("import_record_id")) for record in records])
	quarantined_scenario_ids = [
		_clean_text(record.get("scenario_id")) or "unknown"
		for record in records
		if _clean_text(record.get("parse_status")) == IMPORT_PARSE_QUARANTINED
	]
	blocked_scenario_ids = [
		_clean_text(record.get("scenario_id")) or "unknown"
		for record in records
		if _clean_text(record.get("parse_status")) == IMPORT_PARSE_BLOCKED
	]
	import_complete = bool(not quarantined_scenario_ids and not duplicate_import_record_ids)
	release_ready = bool(import_complete and archive_index.get("release_ready"))
	return {
		"type": MANUAL_UAT_IMPORT_BATCH_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"contract_owner": _clean_text(contract_owner),
		"import_batch_id": _clean_text(import_batch_id),
		"generated_at": generated_at_text,
		"reviewer": _clean_text(reviewer),
		"json_artifact_path": _clean_text(json_artifact_path),
		"markdown_artifact_path": _clean_text(markdown_artifact_path),
		"json_artifact_written": False,
		"markdown_artifact_written": False,
		"expected_scenario_count": len(expected_ids),
		"expected_scenario_ids": expected_ids,
		"capture_record_count": len(records),
		"accepted_record_count": counts[IMPORT_PARSE_ACCEPTED],
		"blocked_record_count": counts[IMPORT_PARSE_BLOCKED],
		"quarantined_record_count": counts[IMPORT_PARSE_QUARANTINED],
		"parse_status_counts": counts,
		"blocked_scenario_ids": blocked_scenario_ids,
		"quarantined_scenario_ids": quarantined_scenario_ids,
		"duplicate_import_record_ids": duplicate_import_record_ids,
		"archive_import_record_count": len(archive_import_records),
		"archive_release_ready": bool(archive_index.get("release_ready")),
		"release_ready": release_ready,
		"import_complete": import_complete,
		"archive_index_contract": archive_index,
		"records": records,
	}


def _md_cell(value: Any) -> str:
	if value is None:
		text = ""
	elif isinstance(value, bool):
		text = "True" if value else "False"
	else:
		text = str(value).strip()
	return text.replace("|", "\\|").replace("\n", "<br>")


def _join(values: Any) -> str:
	items = _clean_list(values)
	return ", ".join(items) if items else "none"


def render_manual_uat_import_markdown(batch_contract: Dict[str, Any]) -> str:
	contract = dict(batch_contract or {})
	lines: List[str] = ["# S7 Manual UAT Evidence Import Batch", ""]
	lines.append("## Import Metadata")
	lines.append("")
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	for field in [
		"import_batch_id",
		"generated_at",
		"reviewer",
		"expected_scenario_count",
		"capture_record_count",
		"accepted_record_count",
		"blocked_record_count",
		"quarantined_record_count",
		"import_complete",
		"archive_release_ready",
		"release_ready",
		"json_artifact_path",
		"markdown_artifact_path",
	]:
		lines.append(f"| {_md_cell(field)} | {_md_cell(contract.get(field))} |")
	lines.extend(["", "## Import Boundary", ""])
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	lines.append(f"| Blocked scenarios | {_md_cell(_join(contract.get('blocked_scenario_ids')))} |")
	lines.append(f"| Quarantined scenarios | {_md_cell(_join(contract.get('quarantined_scenario_ids')))} |")
	lines.append(f"| Duplicate import records | {_md_cell(_join(contract.get('duplicate_import_record_ids')))} |")
	archive_index = dict(contract.get("archive_index_contract") or {})
	lines.append(f"| Archive missing evidence | {_md_cell(_join(archive_index.get('missing_evidence_scenario_ids')))} |")
	lines.append(f"| Archive blocking failures | {_md_cell(_join(archive_index.get('blocking_failure_scenario_ids')))} |")
	lines.extend(["", "## Records", ""])
	lines.append(
		"| Scenario | Pack | Parse status | UAT status | Release blocking | Missing capture | Mismatches | Quarantine reason | Hash |"
	)
	lines.append("|---|---|---|---|---|---|---|---|---|")
	for record in contract.get("records") or []:
		if not isinstance(record, dict):
			continue
		mismatch_fields = [
			_clean_text(mismatch.get("field"))
			for mismatch in record.get("field_mismatches") or []
			if isinstance(mismatch, dict)
		]
		lines.append(
			"| "
			+ " | ".join(
				[
					_md_cell(record.get("scenario_id") or "unknown"),
					_md_cell(record.get("scenario_pack")),
					_md_cell(record.get("parse_status")),
					_md_cell(record.get("uat_status")),
					_md_cell(record.get("release_blocking")),
					_md_cell(_join(record.get("missing_capture_sections"))),
					_md_cell(_join(mismatch_fields)),
					_md_cell(record.get("quarantine_reason") or "none"),
					_md_cell(_clean_text(record.get("raw_evidence_hash"))[:12]),
				]
			)
			+ " |"
		)
	if not contract.get("records"):
		lines.append("| none | none | none | none | False | none | none | none | none |")
	return "\n".join(lines).strip() + "\n"


def write_manual_uat_import_files(
	capture_records: Iterable[Dict[str, Any]] | None = None,
	*,
	json_path: str = DEFAULT_MANUAL_UAT_IMPORT_JSON_PATH,
	markdown_path: str = DEFAULT_MANUAL_UAT_IMPORT_MARKDOWN_PATH,
	registry: Iterable[Dict[str, Any]] | None = None,
	expected_scenario_ids: Iterable[str] | None = None,
	import_batch_id: str = "s7_manual_uat_evidence_import_batch",
	generated_at: str = "",
	reviewer: str = "",
) -> Dict[str, Any]:
	batch = build_manual_uat_import_batch(
		capture_records,
		registry=registry,
		expected_scenario_ids=expected_scenario_ids,
		import_batch_id=import_batch_id,
		generated_at=generated_at,
		reviewer=reviewer,
		json_artifact_path=json_path,
		markdown_artifact_path=markdown_path,
	)
	json_target = Path(batch["json_artifact_path"])
	markdown_target = Path(batch["markdown_artifact_path"])
	if not json_target.is_absolute():
		json_target = Path.cwd() / json_target
	if not markdown_target.is_absolute():
		markdown_target = Path.cwd() / markdown_target
	json_target.parent.mkdir(parents=True, exist_ok=True)
	markdown_target.parent.mkdir(parents=True, exist_ok=True)
	json_target.write_text(json.dumps(batch, indent=2, sort_keys=True) + "\n", encoding="utf-8")
	markdown_target.write_text(render_manual_uat_import_markdown(batch), encoding="utf-8")
	written = dict(batch)
	written["json_artifact_path"] = str(json_target)
	written["markdown_artifact_path"] = str(markdown_target)
	written["json_artifact_written"] = json_target.exists()
	written["markdown_artifact_written"] = markdown_target.exists()
	written["json_artifact_size_bytes"] = json_target.stat().st_size if json_target.exists() else 0
	written["markdown_artifact_size_bytes"] = markdown_target.stat().st_size if markdown_target.exists() else 0
	return written
