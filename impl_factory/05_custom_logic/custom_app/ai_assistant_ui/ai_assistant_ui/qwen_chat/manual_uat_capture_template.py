from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .manual_uat_evidence import (
	REQUIRED_OBSERVED_MODEL_ROLE_KEYS,
	REQUIRED_OBSERVED_TRACE_KEYS,
)
from .manual_uat_import import REQUIRED_IMPORT_ENVELOPE_FIELDS
from .manual_uat_import import FINAL_ANSWER_AUTHORITY_FIELDS, REQUIRED_FINAL_ANSWER_AUTHORITY_KEYS
from .natural_business_understanding_contracts import CONTRACT_VERSION
from .regression_scenario_packs import (
	EXECUTION_MANUAL_BROWSER_UAT,
	S7_REGRESSION_SCENARIO_REGISTRY,
	build_regression_scenario_contract,
	build_regression_scenario_pack_contract,
)
from .regression_suite_governance import BLOCKING_MANUAL


MANUAL_UAT_CAPTURE_TEMPLATE_CONTRACT_TYPE = "qwen_manual_uat_capture_template_contract"
MANUAL_UAT_CAPTURE_TEMPLATE_PACK_CONTRACT_TYPE = "qwen_manual_uat_capture_template_pack_contract"
MANUAL_UAT_CAPTURE_TEMPLATE_SUITE_ID = "s7_manual_uat_capture_template_contracts"
MANUAL_UAT_OPERATOR_CAPTURE_PROMOTION_SUITE_ID = "s7_operator_evidence_mode_capture_template_contracts"

EVIDENCE_MODE_OPERATOR_CAPTURED = "operator_captured"
OPERATOR_CAPTURE_SOURCE = "manual_browser_uat"
OPERATOR_RELEASE_BOUNDARY = "none"
OPERATOR_PROMOTION_INTENT = "production_manual_uat"

DEFAULT_MANUAL_UAT_CAPTURE_TEMPLATE_MARKDOWN_PATH = (
	"impl_factory/00_governance/current_docs/generated/"
	"qwen_s7_manual_uat_operator_capture_template.md"
)
DEFAULT_MANUAL_UAT_CAPTURE_TEMPLATE_JSON_PATH = (
	"impl_factory/00_governance/current_docs/generated/"
	"qwen_s7_manual_uat_operator_capture_skeleton.json"
)

IMPORT_READY_JSON_FIELDS = (
	list(REQUIRED_IMPORT_ENVELOPE_FIELDS)
	+ [
		"evidence_mode",
		"release_boundary",
		"dry_run_only",
		"operator_attestation",
		"promotion_intent",
	]
	+ [f"observed_trace_fields.{field}" for field in REQUIRED_OBSERVED_TRACE_KEYS]
	+ [f"observed_model_role_fields.{field}" for field in REQUIRED_OBSERVED_MODEL_ROLE_KEYS]
	+ [f"final_answer_authority.{field}" for field in FINAL_ANSWER_AUTHORITY_FIELDS]
)

REQUIRED_PROMOTION_FIELDS = [
	"evidence_mode",
	"release_boundary",
	"dry_run_only",
	"operator_attestation",
	"promotion_intent",
]


def _utc_now() -> str:
	return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


def _clean_records(values: Iterable[Dict[str, Any]] | None) -> List[Dict[str, Any]]:
	return [dict(value) for value in values or [] if isinstance(value, dict)]


def _scenario_template_value(scenario: Dict[str, Any], field: str, default_value: str = "") -> str:
	return _clean_text(scenario.get(field)) or _clean_text(default_value)


def _json_skeleton_for_scenario(scenario: Dict[str, Any]) -> Dict[str, Any]:
	return {
		"scenario_id": _scenario_template_value(scenario, "scenario_id"),
		"reviewer": "",
		"captured_at": "",
		"capture_source": OPERATOR_CAPTURE_SOURCE,
		"evidence_mode": EVIDENCE_MODE_OPERATOR_CAPTURED,
		"release_boundary": OPERATOR_RELEASE_BOUNDARY,
		"dry_run_only": False,
		"operator_attestation": "",
		"promotion_intent": OPERATOR_PROMOTION_INTENT,
		"uat_status": "",
		"failure_reason": "",
		"raw_answer_text": "",
		"raw_trace_text": "",
		"observed_answer_summary": "",
		"observed_trace_fields": {field: "" for field in REQUIRED_OBSERVED_TRACE_KEYS},
		"observed_model_role_fields": {field: "" for field in REQUIRED_OBSERVED_MODEL_ROLE_KEYS},
		"final_answer_authority": {field: "" for field in FINAL_ANSWER_AUTHORITY_FIELDS},
	}


def _missing_template_fields(template: Dict[str, Any]) -> List[str]:
	missing: List[str] = []
	for field in [
		"scenario_id",
		"scenario_pack",
		"family",
		"manual_uat_prompt",
		"expected_route",
		"expected_artifact_family",
		"expected_entity_type",
		"expected_row_reference",
		"expected_authority_source",
		"expected_policy_boundary",
		"expected_model_role_lane",
		"expected_answer_mode",
		"blocking_level",
		"execution_mode",
	]:
		if not _clean_text(template.get(field)):
			missing.append(field)
	if not _clean_list(template.get("turns")):
		missing.append("turns")
	if not _clean_list(template.get("pass_criteria")):
		missing.append("pass_criteria")
	if not _clean_list(template.get("required_import_fields")):
		missing.append("required_import_fields")
	if not _clean_list(template.get("required_trace_fields")):
		missing.append("required_trace_fields")
	if not _clean_list(template.get("required_model_role_fields")):
		missing.append("required_model_role_fields")
	if not _clean_list(template.get("required_final_answer_authority_fields")):
		missing.append("required_final_answer_authority_fields")
	if not _clean_list(template.get("required_promotion_fields")):
		missing.append("required_promotion_fields")
	json_skeleton = template.get("import_ready_json_skeleton")
	if not isinstance(json_skeleton, dict):
		missing.append("import_ready_json_skeleton")
	else:
		for field in REQUIRED_PROMOTION_FIELDS:
			if field not in json_skeleton:
				missing.append(f"import_ready_json_skeleton.{field}")
	return missing


def build_manual_uat_capture_template(scenario: Dict[str, Any]) -> Dict[str, Any]:
	entry = build_regression_scenario_contract(scenario)
	execution_mode = _scenario_template_value(entry, "execution_mode")
	blocking_level = _scenario_template_value(entry, "blocking_level")
	template = {
		"type": MANUAL_UAT_CAPTURE_TEMPLATE_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"template_id": f"manual_uat_capture_template:{_scenario_template_value(entry, 'scenario_id')}",
		"scenario_id": _scenario_template_value(entry, "scenario_id"),
		"scenario_pack": _scenario_template_value(entry, "pack_id"),
		"family": _scenario_template_value(entry, "family"),
		"turns": _clean_list(entry.get("turns")),
		"manual_uat_prompt": _scenario_template_value(entry, "manual_uat_prompt"),
		"expected_route": _scenario_template_value(entry, "expected_route"),
		"expected_artifact_family": _scenario_template_value(entry, "expected_artifact_family"),
		"expected_entity_type": _scenario_template_value(entry, "expected_entity_type"),
		"expected_row_reference": _scenario_template_value(entry, "expected_row_reference"),
		"expected_authority_source": _scenario_template_value(entry, "expected_authority_source"),
		"expected_policy_boundary": _scenario_template_value(entry, "expected_policy_boundary"),
		"expected_model_role_lane": _scenario_template_value(entry, "expected_model_role_lane"),
		"expected_answer_mode": _scenario_template_value(entry, "expected_answer_mode"),
		"pass_criteria": _clean_list(entry.get("pass_criteria")),
		"blocking_level": blocking_level,
		"execution_mode": execution_mode,
		"manual_only": execution_mode == EXECUTION_MANUAL_BROWSER_UAT or blocking_level == BLOCKING_MANUAL,
		"required_import_fields": list(REQUIRED_IMPORT_ENVELOPE_FIELDS),
		"required_trace_fields": list(REQUIRED_OBSERVED_TRACE_KEYS),
		"required_model_role_fields": list(REQUIRED_OBSERVED_MODEL_ROLE_KEYS),
		"required_final_answer_authority_fields": list(REQUIRED_FINAL_ANSWER_AUTHORITY_KEYS),
		"required_promotion_fields": list(REQUIRED_PROMOTION_FIELDS),
		"promotion_defaults": {
			"capture_source": OPERATOR_CAPTURE_SOURCE,
			"evidence_mode": EVIDENCE_MODE_OPERATOR_CAPTURED,
			"release_boundary": OPERATOR_RELEASE_BOUNDARY,
			"dry_run_only": False,
			"promotion_intent": OPERATOR_PROMOTION_INTENT,
		},
		"operator_attestation_required": True,
		"promotion_ready_by_default": True,
		"import_ready_json_fields": list(IMPORT_READY_JSON_FIELDS),
		"import_ready_json_skeleton": _json_skeleton_for_scenario(entry),
		"operator_capture_sections": [
			"scenario_metadata",
			"prompt_sequence",
			"expected_contract_fields",
			"promotion_boundary_fields",
			"pass_criteria",
			"raw_answer_capture",
			"raw_trace_capture",
			"observed_trace_fields",
			"observed_model_role_fields",
			"final_answer_authority",
			"status_and_failure_reason",
			"import_ready_json_skeleton",
		],
	}
	missing_fields = _missing_template_fields(template)
	template["missing_fields"] = missing_fields
	template["template_complete"] = not missing_fields
	return template


def build_manual_uat_capture_template_pack(
	*,
	registry: Iterable[Dict[str, Any]] | None = None,
	markdown_artifact_path: str = DEFAULT_MANUAL_UAT_CAPTURE_TEMPLATE_MARKDOWN_PATH,
	json_artifact_path: str = DEFAULT_MANUAL_UAT_CAPTURE_TEMPLATE_JSON_PATH,
	generated_at: str = "",
	contract_owner: str = "s7_manual_uat_capture_template",
) -> Dict[str, Any]:
	scenario_pack = build_regression_scenario_pack_contract(registry=registry)
	templates = [build_manual_uat_capture_template(scenario) for scenario in scenario_pack.get("scenarios", [])]
	incomplete_templates = [
		_clean_text(template.get("scenario_id")) or "unknown"
		for template in templates
		if not bool(template.get("template_complete"))
	]
	return {
		"type": MANUAL_UAT_CAPTURE_TEMPLATE_PACK_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"contract_owner": _clean_text(contract_owner),
		"source_scenario_pack_type": scenario_pack.get("type"),
		"source_scenario_pack_complete": bool(scenario_pack.get("contract_complete")),
		"markdown_artifact_path": _clean_text(markdown_artifact_path),
		"json_artifact_path": _clean_text(json_artifact_path),
		"generated_at": _clean_text(generated_at) or _utc_now(),
		"scenario_count": len(templates),
		"manual_only_scenario_ids": [
			_clean_text(template.get("scenario_id"))
			for template in templates
			if bool(template.get("manual_only"))
		],
		"template_ids": [_clean_text(template.get("template_id")) for template in templates],
		"incomplete_templates": incomplete_templates,
		"required_import_fields": list(REQUIRED_IMPORT_ENVELOPE_FIELDS),
		"required_trace_fields": list(REQUIRED_OBSERVED_TRACE_KEYS),
		"required_model_role_fields": list(REQUIRED_OBSERVED_MODEL_ROLE_KEYS),
		"required_final_answer_authority_fields": list(REQUIRED_FINAL_ANSWER_AUTHORITY_KEYS),
		"required_promotion_fields": list(REQUIRED_PROMOTION_FIELDS),
		"import_ready_json_skeletons": [template.get("import_ready_json_skeleton") for template in templates],
		"templates": templates,
		"template_pack_complete": bool(scenario_pack.get("contract_complete")) and bool(templates) and not incomplete_templates,
	}


def _md_cell(value: Any) -> str:
	if value is None:
		text = ""
	elif isinstance(value, bool):
		text = "True" if value else "False"
	else:
		text = str(value).strip()
	return text.replace("|", "\\|").replace("\n", "<br>")


def _json_block(value: Any) -> str:
	return json.dumps(value, indent=2, sort_keys=True)


def render_capture_template_section(template: Dict[str, Any]) -> str:
	entry = dict(template or {})
	lines: List[str] = [f"### Capture Template: {_clean_text(entry.get('scenario_id'))}", ""]
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	for field in [
		"scenario_id",
		"scenario_pack",
		"family",
		"manual_only",
		"blocking_level",
		"execution_mode",
		"expected_route",
		"expected_artifact_family",
		"expected_entity_type",
		"expected_row_reference",
		"expected_authority_source",
		"expected_policy_boundary",
		"expected_model_role_lane",
		"expected_answer_mode",
		"operator_attestation_required",
		"promotion_ready_by_default",
	]:
		lines.append(f"| {_md_cell(field)} | {_md_cell(entry.get(field))} |")
	lines.extend(["", "Promotion Boundary Fields"])
	lines.append("- evidence_mode must remain `operator_captured` for real browser UAT evidence.")
	lines.append("- capture_source must remain `manual_browser_uat`.")
	lines.append("- release_boundary must remain `none` for promotion-eligible operator evidence.")
	lines.append("- dry_run_only must remain `False` for real operator evidence.")
	lines.append("- promotion_intent must remain `production_manual_uat`.")
	lines.append("- operator_attestation must be filled by the reviewer before evidence can be promoted.")
	lines.extend(["", "Prompt Sequence"])
	for turn in _clean_list(entry.get("turns")):
		lines.append(f"- {turn}")
	lines.extend(["", "Pass Criteria"])
	for criterion in _clean_list(entry.get("pass_criteria")):
		lines.append(f"- {criterion}")
	lines.extend(["", "Required Answer Capture"])
	for field in REQUIRED_IMPORT_ENVELOPE_FIELDS:
		lines.append(f"- {field}")
	lines.extend(["", "Observed Trace Fields", "", "| Field | Value |", "|---|---|"])
	for field in REQUIRED_OBSERVED_TRACE_KEYS:
		lines.append(f"| {field} |  |")
	lines.extend(["", "Observed Model Role Fields", "", "| Field | Value |", "|---|---|"])
	for field in REQUIRED_OBSERVED_MODEL_ROLE_KEYS:
		lines.append(f"| {field} |  |")
	lines.extend(["", "Final Answer Authority", "", "| Field | Value |", "|---|---|"])
	for field in FINAL_ANSWER_AUTHORITY_FIELDS:
		lines.append(f"| {field} |  |")
	lines.extend(["", "Raw Evidence Paste Areas", ""])
	lines.append("```text")
	lines.append("raw_answer_text:")
	lines.append("")
	lines.append("raw_trace_text:")
	lines.append("```")
	lines.extend(["", "Import-Ready JSON Skeleton", ""])
	lines.append("```json")
	lines.append(_json_block(entry.get("import_ready_json_skeleton") or {}))
	lines.append("```")
	return "\n".join(lines).strip()


def render_manual_uat_capture_template_markdown(template_pack: Dict[str, Any]) -> str:
	contract = dict(template_pack or {})
	lines: List[str] = ["# S7 Manual UAT Operator Capture Template", ""]
	lines.append("## Template Metadata")
	lines.append("")
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	for field in [
		"generated_at",
		"scenario_count",
		"template_pack_complete",
		"markdown_artifact_path",
		"json_artifact_path",
	]:
		lines.append(f"| {_md_cell(field)} | {_md_cell(contract.get(field))} |")
	lines.append(f"| Incomplete templates | {_md_cell(', '.join(_clean_list(contract.get('incomplete_templates'))) or 'none')} |")
	lines.append(f"| Manual-only scenarios | {_md_cell(', '.join(_clean_list(contract.get('manual_only_scenario_ids'))) or 'none')} |")
	lines.extend(["", "## Required Import Fields"])
	for field in _clean_list(contract.get("required_import_fields")):
		lines.append(f"- {field}")
	lines.extend(["", "## Required Trace Fields"])
	for field in _clean_list(contract.get("required_trace_fields")):
		lines.append(f"- observed_trace_fields.{field}")
	lines.extend(["", "## Required Model Role Fields"])
	for field in _clean_list(contract.get("required_model_role_fields")):
		lines.append(f"- observed_model_role_fields.{field}")
	lines.extend(["", "## Required Final Answer Authority Fields"])
	for field in _clean_list(contract.get("required_final_answer_authority_fields")):
		lines.append(f"- final_answer_authority.{field}")
	lines.extend(["", "## Final Answer Authority Capture Fields"])
	for field in FINAL_ANSWER_AUTHORITY_FIELDS:
		lines.append(f"- final_answer_authority.{field}")
	lines.extend(["", "## Required Promotion Fields"])
	for field in _clean_list(contract.get("required_promotion_fields")):
		lines.append(f"- {field}")
	lines.append("- operator_attestation must be filled by the reviewer; blank attestation blocks S7-6M promotion.")
	lines.extend(["", "## Scenario Capture Templates", ""])
	for template in contract.get("templates") or []:
		if isinstance(template, dict):
			lines.append(render_capture_template_section(template))
			lines.append("")
	return "\n".join(lines).strip() + "\n"


def write_manual_uat_capture_template_files(
	*,
	markdown_path: str = DEFAULT_MANUAL_UAT_CAPTURE_TEMPLATE_MARKDOWN_PATH,
	json_path: str = DEFAULT_MANUAL_UAT_CAPTURE_TEMPLATE_JSON_PATH,
	registry: Iterable[Dict[str, Any]] | None = None,
	generated_at: str = "",
) -> Dict[str, Any]:
	contract = build_manual_uat_capture_template_pack(
		registry=registry,
		markdown_artifact_path=markdown_path,
		json_artifact_path=json_path,
		generated_at=generated_at,
	)
	markdown_target = Path(contract["markdown_artifact_path"])
	json_target = Path(contract["json_artifact_path"])
	if not markdown_target.is_absolute():
		markdown_target = Path.cwd() / markdown_target
	if not json_target.is_absolute():
		json_target = Path.cwd() / json_target
	markdown_target.parent.mkdir(parents=True, exist_ok=True)
	json_target.parent.mkdir(parents=True, exist_ok=True)
	markdown_target.write_text(render_manual_uat_capture_template_markdown(contract), encoding="utf-8")
	json_target.write_text(
		json.dumps(contract.get("import_ready_json_skeletons") or [], indent=2, sort_keys=True) + "\n",
		encoding="utf-8",
	)
	written = dict(contract)
	written["markdown_artifact_path"] = str(markdown_target)
	written["json_artifact_path"] = str(json_target)
	written["markdown_artifact_written"] = markdown_target.exists()
	written["json_artifact_written"] = json_target.exists()
	written["markdown_artifact_size_bytes"] = markdown_target.stat().st_size if markdown_target.exists() else 0
	written["json_artifact_size_bytes"] = json_target.stat().st_size if json_target.exists() else 0
	return written


def capture_templates_for_export(
	registry: Iterable[Dict[str, Any]] | None = None,
) -> List[Dict[str, Any]]:
	return list(build_manual_uat_capture_template_pack(registry=registry).get("templates") or [])
