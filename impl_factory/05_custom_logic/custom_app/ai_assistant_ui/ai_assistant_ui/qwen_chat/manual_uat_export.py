from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .manual_uat_capture_template import (
	build_manual_uat_capture_template_pack,
	render_capture_template_section,
)
from .manual_uat_evidence import build_manual_uat_checklist_contract
from .manual_uat_renderer import (
	render_manual_uat_pack_markdown,
	render_manual_uat_release_summary_markdown,
)
from .manual_uat_workflow import (
	REQUIRED_MODEL_ROLE_CAPTURE_FIELDS,
	REQUIRED_TRACE_CAPTURE_FIELDS,
	build_manual_uat_release_summary_from_workflow_evidence,
	build_manual_uat_workflow_pack_contract,
)
from .natural_business_understanding_contracts import CONTRACT_VERSION


MANUAL_UAT_EXPORT_CONTRACT_TYPE = "qwen_manual_uat_artifact_export_contract"
MANUAL_UAT_EXPORT_SUITE_ID = "s7_manual_uat_artifact_export_contracts"

DEFAULT_MANUAL_UAT_EXPORT_PATH = (
	"impl_factory/00_governance/current_docs/generated/"
	"qwen_s7_manual_browser_uat_pack.md"
)


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


def _workflow_lines(workflow_pack_contract: Dict[str, Any]) -> List[str]:
	lines: List[str] = ["**Manual UAT Execution Workflows**", ""]
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	lines.append(f"| Contract complete | {bool(workflow_pack_contract.get('contract_complete'))} |")
	lines.append(f"| Workflow count | {_clean_text(workflow_pack_contract.get('workflow_count')) or '0'} |")
	lines.append(f"| Incomplete workflows | {', '.join(_clean_list(workflow_pack_contract.get('incomplete_workflows'))) or 'none'} |")
	for workflow in workflow_pack_contract.get("workflows") or []:
		if not isinstance(workflow, dict):
			continue
		lines.extend(["", f"### Workflow: {_clean_text(workflow.get('scenario_id'))}", ""])
		lines.append("| Field | Value |")
		lines.append("|---|---|")
		lines.append(f"| Workflow ID | {_clean_text(workflow.get('workflow_id')) or 'missing'} |")
		lines.append(f"| Pack | {_clean_text(workflow.get('pack_id')) or 'missing'} |")
		lines.append(f"| Family | {_clean_text(workflow.get('family')) or 'missing'} |")
		lines.append(f"| Manual UAT prompt | {_clean_text(workflow.get('manual_uat_prompt')) or 'missing'} |")
		lines.append(f"| Release blocking rule | {_clean_text(workflow.get('release_blocking_rule')) or 'missing'} |")
		lines.append(f"| Failure handling rule | {_clean_text(workflow.get('failure_handling_rule')) or 'missing'} |")
		lines.extend(["", "Prompt Sequence"])
		for turn in _clean_list(workflow.get("turns")):
			lines.append(f"- {turn}")
		lines.extend(["", "Workflow Stages"])
		for stage in workflow.get("execution_stages") or []:
			if isinstance(stage, dict):
				lines.append(
					f"- {stage.get('stage_id')}: {stage.get('operator_instruction')} "
					f"(required: {', '.join(_clean_list(stage.get('required_capture_fields'))) or 'none'})"
				)
		lines.extend(["", "Required Trace Capture Fields"])
		for field in REQUIRED_TRACE_CAPTURE_FIELDS:
			lines.append(f"- observed_trace_fields.{field}")
		lines.extend(["", "Required Model-Role Capture Fields"])
		for field in REQUIRED_MODEL_ROLE_CAPTURE_FIELDS:
			lines.append(f"- observed_model_role_fields.{field}")
	return lines


def build_manual_uat_export_contract(
	*,
	artifact_path: str = DEFAULT_MANUAL_UAT_EXPORT_PATH,
	evidence_records: Iterable[Dict[str, Any]] | None = None,
	registry: Iterable[Dict[str, Any]] | None = None,
	expected_scenario_ids: Iterable[str] | None = None,
	export_id: str = "s7_manual_browser_uat_pack",
	generated_at: str = "",
	contract_owner: str = "s7_manual_uat_artifact_export",
) -> Dict[str, Any]:
	checklist = build_manual_uat_checklist_contract(registry=registry)
	workflow_pack = build_manual_uat_workflow_pack_contract(registry=registry)
	capture_template_pack = build_manual_uat_capture_template_pack(registry=registry, generated_at=generated_at)
	records = _clean_records(evidence_records)
	expected_ids = (
		[_clean_text(value) for value in expected_scenario_ids if _clean_text(value)]
		if expected_scenario_ids is not None
		else _clean_list(workflow_pack.get("scenario_ids"))
	)
	release_summary = build_manual_uat_release_summary_from_workflow_evidence(
		evidence_records=records,
		registry=registry,
		expected_scenario_ids=expected_ids,
	)
	artifact_path_text = _clean_text(artifact_path)
	source_complete = bool(checklist.get("contract_complete")) and bool(workflow_pack.get("contract_complete"))
	artifact_complete = bool(source_complete and artifact_path_text and release_summary.get("checklist_contract_complete"))
	return {
		"type": MANUAL_UAT_EXPORT_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"contract_owner": _clean_text(contract_owner),
		"export_id": _clean_text(export_id),
		"artifact_path": artifact_path_text,
		"source_checklist_contract": checklist.get("type"),
		"source_workflow_pack_contract": workflow_pack.get("type"),
		"source_capture_template_pack_contract": capture_template_pack.get("type"),
		"source_release_summary_contract": release_summary.get("type"),
		"checklist_contract": checklist,
		"workflow_pack_contract": workflow_pack,
		"capture_template_pack_contract": capture_template_pack,
		"release_summary_contract": release_summary,
		"evidence_records": records,
		"scenario_count": int(checklist.get("row_count") or 0),
		"manual_only_count": int(checklist.get("manual_only_row_count") or 0),
		"deterministic_reference_count": int(checklist.get("deterministic_reference_row_count") or 0),
		"release_ready": bool(release_summary.get("release_ready")),
		"blocking_failure_scenario_ids": _clean_list(release_summary.get("blocking_failure_scenario_ids")),
		"manual_only_scenario_ids": _clean_list(checklist.get("manual_only_scenario_ids")),
		"generated_at": _clean_text(generated_at) or _utc_now(),
		"artifact_complete": artifact_complete,
		"incomplete_source_contracts": [
			name
			for name, complete in [
				("checklist_contract", bool(checklist.get("contract_complete"))),
				("workflow_pack_contract", bool(workflow_pack.get("contract_complete"))),
				("capture_template_pack_contract", bool(capture_template_pack.get("template_pack_complete"))),
				("release_summary_contract", bool(release_summary.get("checklist_contract_complete"))),
			]
			if not complete
		],
	}


def render_manual_uat_export_markdown(export_contract: Dict[str, Any]) -> str:
	contract = dict(export_contract or {})
	checklist = dict(contract.get("checklist_contract") or {})
	workflow_pack = dict(contract.get("workflow_pack_contract") or {})
	capture_template_pack = dict(contract.get("capture_template_pack_contract") or {})
	release_summary = dict(contract.get("release_summary_contract") or {})
	evidence_records = _clean_records(contract.get("evidence_records"))
	lines: List[str] = ["# S7 Manual Browser UAT Pack", ""]
	lines.append("## Export Metadata")
	lines.append("")
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	lines.append(f"| Export ID | {_clean_text(contract.get('export_id')) or 'missing'} |")
	lines.append(f"| Generated at | {_clean_text(contract.get('generated_at')) or 'missing'} |")
	lines.append(f"| Artifact path | {_clean_text(contract.get('artifact_path')) or 'missing'} |")
	lines.append(f"| Artifact complete | {bool(contract.get('artifact_complete'))} |")
	lines.append(f"| Scenario count | {_clean_text(contract.get('scenario_count')) or '0'} |")
	lines.append(f"| Manual-only count | {_clean_text(contract.get('manual_only_count')) or '0'} |")
	lines.append(f"| Deterministic reference count | {_clean_text(contract.get('deterministic_reference_count')) or '0'} |")
	lines.append(f"| Release ready | {bool(contract.get('release_ready'))} |")
	lines.append(f"| Blocking failures | {', '.join(_clean_list(contract.get('blocking_failure_scenario_ids'))) or 'none'} |")
	lines.append(f"| Incomplete source contracts | {', '.join(_clean_list(contract.get('incomplete_source_contracts'))) or 'none'} |")
	lines.extend(["", "## Required Capture Fields", "", "### Trace"])
	for field in REQUIRED_TRACE_CAPTURE_FIELDS:
		lines.append(f"- observed_trace_fields.{field}")
	lines.extend(["", "### Model Role"])
	for field in REQUIRED_MODEL_ROLE_CAPTURE_FIELDS:
		lines.append(f"- observed_model_role_fields.{field}")
	lines.extend(["", "## Manual-Only Scenarios"])
	for scenario_id in _clean_list(contract.get("manual_only_scenario_ids")):
		lines.append(f"- {scenario_id}")
	if not _clean_list(contract.get("manual_only_scenario_ids")):
		lines.append("- none")
	lines.extend(["", "## Release Summary", "", render_manual_uat_release_summary_markdown(release_summary)])
	lines.extend(["", "## Workflow Instructions", "", "\n".join(_workflow_lines(workflow_pack))])
	lines.extend(["", "## Operator Capture Templates", ""])
	for template in capture_template_pack.get("templates") or []:
		if isinstance(template, dict):
			lines.append(render_capture_template_section(template))
			lines.append("")
	lines.extend(["", "## Checklist And Evidence", "", render_manual_uat_pack_markdown(
		checklist,
		evidence_records=evidence_records,
		summary_contract=release_summary,
	)])
	return "\n".join(lines).strip() + "\n"


def write_manual_uat_export_file(
	*,
	artifact_path: str = DEFAULT_MANUAL_UAT_EXPORT_PATH,
	evidence_records: Iterable[Dict[str, Any]] | None = None,
	registry: Iterable[Dict[str, Any]] | None = None,
	expected_scenario_ids: Iterable[str] | None = None,
	export_id: str = "s7_manual_browser_uat_pack",
	generated_at: str = "",
) -> Dict[str, Any]:
	contract = build_manual_uat_export_contract(
		artifact_path=artifact_path,
		evidence_records=evidence_records,
		registry=registry,
		expected_scenario_ids=expected_scenario_ids,
		export_id=export_id,
		generated_at=generated_at,
	)
	target = Path(contract["artifact_path"])
	if not target.is_absolute():
		target = Path.cwd() / target
	target.parent.mkdir(parents=True, exist_ok=True)
	markdown = render_manual_uat_export_markdown(contract)
	target.write_text(markdown, encoding="utf-8")
	contract["artifact_path"] = str(target)
	contract["artifact_written"] = target.exists()
	contract["artifact_size_bytes"] = target.stat().st_size if target.exists() else 0
	contract["artifact_complete"] = bool(contract.get("artifact_complete") and contract["artifact_written"])
	return contract
