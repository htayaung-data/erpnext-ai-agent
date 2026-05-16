from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .manual_uat_bundle import build_manual_uat_evidence_bundle
from .manual_uat_evidence import MANUAL_UAT_STATUS_PASS
from .natural_business_understanding_contracts import CONTRACT_VERSION
from .regression_scenario_packs import (
	S7_REGRESSION_SCENARIO_REGISTRY,
	build_regression_scenario_contract,
)


MANUAL_UAT_SAMPLE_FIXTURE_CONTRACT_TYPE = "qwen_manual_uat_sample_fixture_contract"
MANUAL_UAT_SAMPLE_FIXTURE_SUITE_ID = "s7_manual_uat_sample_fixture_contracts"

EVIDENCE_MODE_SAMPLE_FIXTURE = "sample_fixture"
SAMPLE_CAPTURE_SOURCE = "sample_fixture_dry_run"
PRODUCTION_RELEASE_BOUNDARY = "not_production_uat_evidence"

DEFAULT_MANUAL_UAT_SAMPLE_CAPTURE_JSON_PATH = (
	"impl_factory/00_governance/current_docs/generated/"
	"qwen_s7_manual_uat_sample_capture_records.json"
)
DEFAULT_MANUAL_UAT_SAMPLE_BUNDLE_JSON_PATH = (
	"impl_factory/00_governance/current_docs/generated/"
	"qwen_s7_manual_uat_sample_dry_run_bundle.json"
)
DEFAULT_MANUAL_UAT_SAMPLE_BUNDLE_MARKDOWN_PATH = (
	"impl_factory/00_governance/current_docs/generated/"
	"qwen_s7_manual_uat_sample_dry_run_bundle.md"
)

DEFAULT_SAMPLE_SCENARIO_IDS = [
	"visible_ar_after_ap_typed_rank_2",
	"visible_ap_current_rank_2",
	"product_projection_qty_preserves_revenue",
	"product_top7_rank_8_out_of_range",
	"pl_cogs_source_document_rank_2",
	"ar_rank_2_default_prediction_boundary",
	"ar_first_customer_cause_boundary",
	"ar_collection_recommendation_boundary",
	"trace_inspection_model_role_coverage",
]

_WILDCARD_TRACE_DEFAULTS = {
	"selected_visible_artifact": "accounts_receivable_aging",
	"selected_visible_entity_type": "customer",
	"selected_visible_row_reference": "rank_2",
	"none_or_selected_boundary": "none",
	"scenario_declared_authority": "visible_rendered_table",
	"scenario_declared_boundary": "none",
}


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


def _scenario_ids(values: Iterable[str] | None) -> List[str]:
	return [_clean_text(value) for value in values or [] if _clean_text(value)]


def _model_role_parts(expected_model_role_lane: str) -> Dict[str, str]:
	model_role_lane = _clean_text(expected_model_role_lane)
	lane, _, model_role = model_role_lane.partition(":")
	return {
		"model_role_lane": model_role_lane,
		"lane": lane or model_role_lane,
		"model_role": model_role or model_role_lane,
		"expected_model_role": model_role or model_role_lane,
		"role_compliance": "compliant",
	}


def _resolved_trace_value(value: Any) -> str:
	text = _clean_text(value)
	return _WILDCARD_TRACE_DEFAULTS.get(text, text)


def _observed_trace_fields(scenario: Dict[str, Any]) -> Dict[str, str]:
	return {
		"route": _resolved_trace_value(scenario.get("expected_route")),
		"artifact_family": _resolved_trace_value(scenario.get("expected_artifact_family")),
		"entity_type": _resolved_trace_value(scenario.get("expected_entity_type")),
		"row_reference": _resolved_trace_value(scenario.get("expected_row_reference")),
		"authority_source": _resolved_trace_value(scenario.get("expected_authority_source")),
		"policy_boundary": _resolved_trace_value(scenario.get("expected_policy_boundary")),
		"answer_mode": _resolved_trace_value(scenario.get("expected_answer_mode")),
	}


def _raw_trace_text(trace_fields: Dict[str, str], model_role_fields: Dict[str, str]) -> str:
	policy_boundary = _clean_text(trace_fields.get("policy_boundary")) or "none"
	preflight_status = "bounded" if policy_boundary != "none" else "passed"
	lines = [
		"Context Authority Trace",
		"",
		"Observed Trace Fields",
		"",
		"| Field | Value |",
		"|---|---|",
	]
	for field in [
		"route",
		"artifact_family",
		"entity_type",
		"row_reference",
		"authority_source",
		"policy_boundary",
		"answer_mode",
	]:
		lines.append(f"| {field} | {_clean_text(trace_fields.get(field))} |")
	lines.extend(
		[
			"",
			"Observed Model Role Fields",
			"",
			"| Field | Value |",
			"|---|---|",
		]
	)
	for field in [
		"model_role_lane",
		"lane",
		"model_role",
		"expected_model_role",
		"role_compliance",
	]:
		lines.append(f"| {field} | {_clean_text(model_role_fields.get(field))} |")
	lines.extend(
		[
			"",
			"Final Answer Authority",
			"",
			"| Field | Value |",
			"|---|---|",
			f"| authority_source | {_clean_text(trace_fields.get('authority_source'))} |",
			"| evidence_scope | visible_rendered_table |",
			"| selected_artifact_id | sample-visible-artifact |",
			f"| selected_report_family | {_clean_text(trace_fields.get('artifact_family'))} |",
			f"| selected_row_reference | {_clean_text(trace_fields.get('row_reference')) or 'none'} |",
			f"| policy_boundary | {policy_boundary} |",
			f"| answer_mode | {_clean_text(trace_fields.get('answer_mode'))} |",
			"| authority_complete | True |",
			f"| preflight_status | {preflight_status} |",
			"| missing_fields | none |",
		]
	)
	return "\n".join(lines)


def build_manual_uat_sample_capture_record(
	scenario: Dict[str, Any],
	*,
	generated_at: str = "",
	reviewer: str = "",
	fixture_id: str = "s7_manual_uat_sample_fixture",
) -> Dict[str, Any]:
	entry = build_regression_scenario_contract(scenario)
	scenario_id = _clean_text(entry.get("scenario_id"))
	trace_fields = _observed_trace_fields(entry)
	model_role_fields = _model_role_parts(_clean_text(entry.get("expected_model_role_lane")))
	answer_summary = f"Sample dry-run answer evidence for {scenario_id}."
	return {
		"scenario_id": scenario_id,
		"reviewer": _clean_text(reviewer) or "sample_fixture",
		"captured_at": _clean_text(generated_at) or _utc_now(),
		"capture_source": SAMPLE_CAPTURE_SOURCE,
		"uat_status": MANUAL_UAT_STATUS_PASS,
		"failure_reason": "",
		"raw_answer_text": answer_summary,
		"raw_trace_text": _raw_trace_text(trace_fields, model_role_fields),
		"observed_answer_summary": answer_summary,
		"observed_trace_fields": trace_fields,
		"observed_model_role_fields": model_role_fields,
		"evidence_mode": EVIDENCE_MODE_SAMPLE_FIXTURE,
		"release_boundary": PRODUCTION_RELEASE_BOUNDARY,
		"dry_run_only": True,
		"sample_fixture_id": _clean_text(fixture_id),
	}


def _sample_release_blocking_reasons(
	*,
	bundle: Dict[str, Any],
	unknown_scenario_ids: List[str],
	sample_roundtrip_complete: bool,
	sample_bundle_release_ready: bool,
) -> List[str]:
	reasons = set(_clean_list(bundle.get("release_blocking_reasons")))
	reasons.add(PRODUCTION_RELEASE_BOUNDARY)
	if unknown_scenario_ids:
		reasons.add("unknown_sample_scenario_ids")
	if not sample_roundtrip_complete:
		reasons.add("sample_roundtrip_not_complete")
	if not sample_bundle_release_ready:
		reasons.add("sample_bundle_not_release_ready")
	return sorted(reasons)


def build_manual_uat_sample_fixture(
	*,
	scenario_ids: Iterable[str] | None = None,
	registry: Iterable[Dict[str, Any]] | None = None,
	fixture_id: str = "s7_manual_uat_sample_fixture",
	generated_at: str = "",
	reviewer: str = "",
	capture_json_path: str = DEFAULT_MANUAL_UAT_SAMPLE_CAPTURE_JSON_PATH,
	bundle_json_path: str = DEFAULT_MANUAL_UAT_SAMPLE_BUNDLE_JSON_PATH,
	bundle_markdown_path: str = DEFAULT_MANUAL_UAT_SAMPLE_BUNDLE_MARKDOWN_PATH,
	contract_owner: str = "s7_manual_uat_sample_fixture",
) -> Dict[str, Any]:
	generated_at_text = _clean_text(generated_at) or _utc_now()
	requested_ids = _scenario_ids(scenario_ids if scenario_ids is not None else DEFAULT_SAMPLE_SCENARIO_IDS)
	scenarios = _scenario_map(registry)
	known_ids = [scenario_id for scenario_id in requested_ids if scenario_id in scenarios]
	unknown_scenario_ids = [scenario_id for scenario_id in requested_ids if scenario_id not in scenarios]
	capture_records = [
		build_manual_uat_sample_capture_record(
			scenarios[scenario_id],
			generated_at=generated_at_text,
			reviewer=reviewer,
			fixture_id=fixture_id,
		)
		for scenario_id in known_ids
	]
	bundle = build_manual_uat_evidence_bundle(
		capture_records,
		registry=registry,
		expected_scenario_ids=requested_ids,
		bundle_id=f"{_clean_text(fixture_id)}:dry_run_bundle",
		generated_at=generated_at_text,
		reviewer=_clean_text(reviewer) or "sample_fixture",
		json_artifact_path=bundle_json_path,
		markdown_artifact_path=bundle_markdown_path,
		contract_owner="s7_manual_uat_sample_fixture_dry_run",
	)
	sample_roundtrip_complete = bool(bundle.get("roundtrip_complete")) and not unknown_scenario_ids
	sample_bundle_release_ready = bool(bundle.get("release_ready")) and not unknown_scenario_ids
	release_blocking_reasons = _sample_release_blocking_reasons(
		bundle=bundle,
		unknown_scenario_ids=unknown_scenario_ids,
		sample_roundtrip_complete=sample_roundtrip_complete,
		sample_bundle_release_ready=sample_bundle_release_ready,
	)
	return {
		"type": MANUAL_UAT_SAMPLE_FIXTURE_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"contract_owner": _clean_text(contract_owner),
		"fixture_id": _clean_text(fixture_id),
		"generated_at": generated_at_text,
		"reviewer": _clean_text(reviewer) or "sample_fixture",
		"evidence_mode": EVIDENCE_MODE_SAMPLE_FIXTURE,
		"release_boundary": PRODUCTION_RELEASE_BOUNDARY,
		"production_release_ready": False,
		"release_ready": False,
		"fixture_complete": bool(sample_roundtrip_complete and sample_bundle_release_ready),
		"sample_roundtrip_complete": sample_roundtrip_complete,
		"sample_bundle_release_ready": sample_bundle_release_ready,
		"release_blocking_reasons": release_blocking_reasons,
		"requested_scenario_ids": requested_ids,
		"sample_scenario_ids": known_ids,
		"unknown_scenario_ids": unknown_scenario_ids,
		"requested_scenario_count": len(requested_ids),
		"sample_scenario_count": len(known_ids),
		"capture_record_count": len(capture_records),
		"sample_capture_records": capture_records,
		"sample_bundle_contract": bundle,
		"sample_bundle_contract_type": bundle.get("type"),
		"raw_evidence_hashes": _clean_list(bundle.get("raw_evidence_hashes")),
		"capture_json_artifact_path": _clean_text(capture_json_path),
		"bundle_json_artifact_path": _clean_text(bundle_json_path),
		"bundle_markdown_artifact_path": _clean_text(bundle_markdown_path),
		"capture_json_artifact_written": False,
		"bundle_json_artifact_written": False,
		"bundle_markdown_artifact_written": False,
		"family_coverage": sorted({_clean_text(scenarios[scenario_id].get("family")) for scenario_id in known_ids}),
		"policy_boundary_coverage": sorted(
			{_clean_text(scenarios[scenario_id].get("expected_policy_boundary")) for scenario_id in known_ids}
		),
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


def render_manual_uat_sample_fixture_markdown(fixture_contract: Dict[str, Any]) -> str:
	contract = dict(fixture_contract or {})
	bundle = dict(contract.get("sample_bundle_contract") or {})
	records = _clean_records(contract.get("sample_capture_records"))
	lines: List[str] = ["# S7 Manual UAT Sample Evidence Dry-Run Bundle", ""]
	lines.append("## Fixture Metadata")
	lines.append("")
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	for field in [
		"fixture_id",
		"generated_at",
		"reviewer",
		"evidence_mode",
		"release_boundary",
		"requested_scenario_count",
		"sample_scenario_count",
		"capture_record_count",
		"fixture_complete",
		"sample_roundtrip_complete",
		"sample_bundle_release_ready",
		"production_release_ready",
		"release_ready",
		"capture_json_artifact_path",
		"bundle_json_artifact_path",
		"bundle_markdown_artifact_path",
	]:
		lines.append(f"| {_md_cell(field)} | {_md_cell(contract.get(field))} |")
	lines.extend(["", "## Production Release Boundary", ""])
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	lines.append(f"| Release blocking reasons | {_md_cell(_join(contract.get('release_blocking_reasons')))} |")
	lines.append(f"| Unknown sample scenarios | {_md_cell(_join(contract.get('unknown_scenario_ids')))} |")
	lines.append("| Production release usage | Sample evidence is dry-run only and cannot satisfy real manual UAT signoff. |")
	lines.extend(["", "## Dry-Run Bundle Status", ""])
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	lines.append(f"| Bundle contract type | {_md_cell(contract.get('sample_bundle_contract_type'))} |")
	lines.append(f"| Bundle roundtrip complete | {_md_cell(bundle.get('roundtrip_complete'))} |")
	lines.append(f"| Bundle release ready | {_md_cell(bundle.get('release_ready'))} |")
	lines.append(f"| Bundle blockers | {_md_cell(_join(bundle.get('release_blocking_reasons')))} |")
	lines.extend(["", "## Sample Scenario Records", ""])
	lines.append("| Scenario | Family | Policy boundary | Row reference | Hash |")
	lines.append("|---|---|---|---|---|")
	hashes = _clean_list(bundle.get("raw_evidence_hashes"))
	hashes_by_scenario = {
		_clean_text(record.get("scenario_id")): _clean_text(record.get("raw_evidence_hash"))
		for record in bundle.get("import_batch_contract", {}).get("records", [])
		if isinstance(record, dict)
	}
	for record in records:
		scenario_id = _clean_text(record.get("scenario_id"))
		trace_fields = dict(record.get("observed_trace_fields") or {})
		lines.append(
			"| "
			+ " | ".join(
				[
					_md_cell(scenario_id),
					_md_cell(trace_fields.get("artifact_family")),
					_md_cell(trace_fields.get("policy_boundary")),
					_md_cell(trace_fields.get("row_reference")),
					_md_cell(hashes_by_scenario.get(scenario_id, "")[:12]),
				]
			)
			+ " |"
		)
	if not records:
		lines.append("| none | none | none | none | none |")
	lines.extend(["", "## Raw Evidence Hashes", ""])
	for evidence_hash in hashes:
		lines.append(f"- {evidence_hash}")
	if not hashes:
		lines.append("- none")
	return "\n".join(lines).strip() + "\n"


def write_manual_uat_sample_fixture_files(
	*,
	scenario_ids: Iterable[str] | None = None,
	registry: Iterable[Dict[str, Any]] | None = None,
	fixture_id: str = "s7_manual_uat_sample_fixture",
	generated_at: str = "",
	reviewer: str = "",
	capture_json_path: str = DEFAULT_MANUAL_UAT_SAMPLE_CAPTURE_JSON_PATH,
	bundle_json_path: str = DEFAULT_MANUAL_UAT_SAMPLE_BUNDLE_JSON_PATH,
	bundle_markdown_path: str = DEFAULT_MANUAL_UAT_SAMPLE_BUNDLE_MARKDOWN_PATH,
) -> Dict[str, Any]:
	fixture = build_manual_uat_sample_fixture(
		scenario_ids=scenario_ids,
		registry=registry,
		fixture_id=fixture_id,
		generated_at=generated_at,
		reviewer=reviewer,
		capture_json_path=capture_json_path,
		bundle_json_path=bundle_json_path,
		bundle_markdown_path=bundle_markdown_path,
	)
	capture_target = Path(fixture["capture_json_artifact_path"])
	bundle_target = Path(fixture["bundle_json_artifact_path"])
	markdown_target = Path(fixture["bundle_markdown_artifact_path"])
	if not capture_target.is_absolute():
		capture_target = Path.cwd() / capture_target
	if not bundle_target.is_absolute():
		bundle_target = Path.cwd() / bundle_target
	if not markdown_target.is_absolute():
		markdown_target = Path.cwd() / markdown_target
	capture_target.parent.mkdir(parents=True, exist_ok=True)
	bundle_target.parent.mkdir(parents=True, exist_ok=True)
	markdown_target.parent.mkdir(parents=True, exist_ok=True)
	capture_target.write_text(
		json.dumps(fixture["sample_capture_records"], indent=2, sort_keys=True) + "\n",
		encoding="utf-8",
	)
	bundle_target.write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n", encoding="utf-8")
	markdown_target.write_text(render_manual_uat_sample_fixture_markdown(fixture), encoding="utf-8")
	written = dict(fixture)
	written["capture_json_artifact_path"] = str(capture_target)
	written["bundle_json_artifact_path"] = str(bundle_target)
	written["bundle_markdown_artifact_path"] = str(markdown_target)
	written["capture_json_artifact_written"] = capture_target.exists()
	written["bundle_json_artifact_written"] = bundle_target.exists()
	written["bundle_markdown_artifact_written"] = markdown_target.exists()
	written["capture_json_artifact_size_bytes"] = capture_target.stat().st_size if capture_target.exists() else 0
	written["bundle_json_artifact_size_bytes"] = bundle_target.stat().st_size if bundle_target.exists() else 0
	written["bundle_markdown_artifact_size_bytes"] = markdown_target.stat().st_size if markdown_target.exists() else 0
	return written
