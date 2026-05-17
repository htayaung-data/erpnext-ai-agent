from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .manual_uat_import import (
	IMPORT_PARSE_ACCEPTED,
	IMPORT_PARSE_BLOCKED,
	IMPORT_PARSE_QUARANTINED,
	build_manual_uat_import_batch,
)
from .natural_business_understanding_contracts import CONTRACT_VERSION
from .regression_scenario_packs import (
	S7_REGRESSION_SCENARIO_REGISTRY,
	build_regression_scenario_contract,
)


MANUAL_UAT_BUNDLE_CONTRACT_TYPE = "qwen_manual_uat_evidence_bundle_contract"
MANUAL_UAT_BUNDLE_SUITE_ID = "s7_manual_uat_evidence_bundle_roundtrip_contracts"

DEFAULT_MANUAL_UAT_BUNDLE_JSON_PATH = (
	"impl_factory/00_governance/current_docs/generated/"
	"qwen_s7_manual_uat_evidence_bundle.json"
)
DEFAULT_MANUAL_UAT_BUNDLE_MARKDOWN_PATH = (
	"impl_factory/00_governance/current_docs/generated/"
	"qwen_s7_manual_uat_evidence_bundle.md"
)


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


def _scenario_ids(registry: Iterable[Dict[str, Any]] | None = None) -> List[str]:
	scenario_ids: List[str] = []
	for entry in registry or S7_REGRESSION_SCENARIO_REGISTRY:
		if not isinstance(entry, dict):
			continue
		scenario = build_regression_scenario_contract(entry)
		scenario_id = _clean_text(scenario.get("scenario_id"))
		if scenario_id:
			scenario_ids.append(scenario_id)
	return scenario_ids


def _duplicate_values(values: List[str]) -> List[str]:
	return sorted({value for value in values if value and values.count(value) > 1})


def _release_blocking_reasons(
	*,
	import_batch: Dict[str, Any],
	archive_index: Dict[str, Any],
	expected_ids: List[str],
	roundtrip_complete: bool,
) -> List[str]:
	reasons: List[str] = []
	if not expected_ids:
		reasons.append("expected_scenarios_missing")
	if not bool(import_batch.get("import_complete")):
		reasons.append("import_batch_not_complete")
	if not bool(archive_index.get("archive_complete")):
		reasons.append("archive_index_not_complete")
	if _clean_list(import_batch.get("blocked_scenario_ids")):
		reasons.append("blocked_import_records")
	if _clean_list(import_batch.get("quarantined_scenario_ids")):
		reasons.append("quarantined_import_records")
	if _clean_list(archive_index.get("missing_evidence_scenario_ids")):
		reasons.append("missing_archive_evidence")
	if _clean_list(archive_index.get("blocking_failure_scenario_ids")):
		reasons.append("archive_blocking_failures")
	if _clean_list(import_batch.get("duplicate_import_record_ids")) or _clean_list(archive_index.get("duplicate_archive_record_ids")):
		reasons.append("duplicate_evidence_records")
	if not bool(import_batch.get("archive_release_ready")):
		reasons.append("import_archive_handoff_not_release_ready")
	if not bool(archive_index.get("release_ready")):
		reasons.append("archive_not_release_ready")
	if not roundtrip_complete:
		reasons.append("roundtrip_not_complete")
	return sorted(set(reasons))


def build_manual_uat_evidence_bundle(
	capture_records: Iterable[Dict[str, Any]] | None = None,
	*,
	registry: Iterable[Dict[str, Any]] | None = None,
	expected_scenario_ids: Iterable[str] | None = None,
	bundle_id: str = "s7_manual_uat_evidence_bundle",
	generated_at: str = "",
	reviewer: str = "",
	json_artifact_path: str = DEFAULT_MANUAL_UAT_BUNDLE_JSON_PATH,
	markdown_artifact_path: str = DEFAULT_MANUAL_UAT_BUNDLE_MARKDOWN_PATH,
	contract_owner: str = "s7_manual_uat_evidence_bundle_roundtrip",
) -> Dict[str, Any]:
	generated_at_text = _clean_text(generated_at) or _utc_now()
	expected_ids = (
		[_clean_text(value) for value in expected_scenario_ids if _clean_text(value)]
		if expected_scenario_ids is not None
		else _scenario_ids(registry)
	)
	records = _clean_records(capture_records)
	import_batch = build_manual_uat_import_batch(
		records,
		registry=registry,
		expected_scenario_ids=expected_ids,
		import_batch_id=f"{_clean_text(bundle_id)}:import",
		generated_at=generated_at_text,
		reviewer=reviewer,
	)
	archive_index = _clean_dict(import_batch.get("archive_index_contract"))
	import_records = [record for record in import_batch.get("records") or [] if isinstance(record, dict)]
	raw_evidence_hashes = [
		_clean_text(record.get("raw_evidence_hash"))
		for record in import_records
		if _clean_text(record.get("raw_evidence_hash"))
	]
	accepted_scenario_ids = [
		_clean_text(record.get("scenario_id"))
		for record in import_records
		if _clean_text(record.get("parse_status")) == IMPORT_PARSE_ACCEPTED and _clean_text(record.get("scenario_id"))
	]
	blocked_scenario_ids = _clean_list(import_batch.get("blocked_scenario_ids"))
	quarantined_scenario_ids = _clean_list(import_batch.get("quarantined_scenario_ids"))
	missing_evidence_scenario_ids = _clean_list(archive_index.get("missing_evidence_scenario_ids"))
	archive_blocking_failure_scenario_ids = _clean_list(archive_index.get("blocking_failure_scenario_ids"))
	duplicate_evidence_ids = sorted(
		set(_clean_list(import_batch.get("duplicate_import_record_ids")))
		| set(_clean_list(archive_index.get("duplicate_archive_record_ids")))
		| set(_duplicate_values([_clean_text(record.get("scenario_id")) for record in import_records]))
	)
	roundtrip_complete = bool(
		expected_ids
		and len(records) == len(expected_ids)
		and bool(import_batch.get("import_complete"))
		and bool(archive_index.get("archive_complete"))
		and not blocked_scenario_ids
		and not quarantined_scenario_ids
		and not missing_evidence_scenario_ids
		and not duplicate_evidence_ids
	)
	release_ready = bool(
		roundtrip_complete
		and bool(import_batch.get("release_ready"))
		and bool(archive_index.get("release_ready"))
	)
	release_blocking_reasons = _release_blocking_reasons(
		import_batch=import_batch,
		archive_index=archive_index,
		expected_ids=expected_ids,
		roundtrip_complete=roundtrip_complete,
	)
	return {
		"type": MANUAL_UAT_BUNDLE_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"contract_owner": _clean_text(contract_owner),
		"bundle_id": _clean_text(bundle_id),
		"generated_at": generated_at_text,
		"reviewer": _clean_text(reviewer),
		"json_artifact_path": _clean_text(json_artifact_path),
		"markdown_artifact_path": _clean_text(markdown_artifact_path),
		"json_artifact_written": False,
		"markdown_artifact_written": False,
		"expected_scenario_ids": expected_ids,
		"expected_scenario_count": len(expected_ids),
		"capture_record_count": len(records),
		"source_capture_records": records,
		"import_batch_contract": import_batch,
		"archive_index_contract": archive_index,
		"raw_evidence_hashes": raw_evidence_hashes,
		"raw_evidence_hash_count": len(raw_evidence_hashes),
		"accepted_scenario_ids": accepted_scenario_ids,
		"blocked_scenario_ids": blocked_scenario_ids,
		"quarantined_scenario_ids": quarantined_scenario_ids,
		"missing_evidence_scenario_ids": missing_evidence_scenario_ids,
		"archive_blocking_failure_scenario_ids": archive_blocking_failure_scenario_ids,
		"duplicate_evidence_ids": duplicate_evidence_ids,
		"roundtrip_complete": roundtrip_complete,
		"release_ready": release_ready,
		"release_blocking_reasons": release_blocking_reasons,
		"bundle_complete": bool(roundtrip_complete and not release_blocking_reasons),
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


def render_manual_uat_evidence_bundle_markdown(bundle_contract: Dict[str, Any]) -> str:
	contract = dict(bundle_contract or {})
	import_batch = _clean_dict(contract.get("import_batch_contract"))
	archive_index = _clean_dict(contract.get("archive_index_contract"))
	lines: List[str] = ["# S7 Manual UAT Evidence Bundle", ""]
	lines.append("## Bundle Metadata")
	lines.append("")
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	for field in [
		"bundle_id",
		"generated_at",
		"reviewer",
		"expected_scenario_count",
		"capture_record_count",
		"raw_evidence_hash_count",
		"roundtrip_complete",
		"release_ready",
		"json_artifact_path",
		"markdown_artifact_path",
	]:
		lines.append(f"| {_md_cell(field)} | {_md_cell(contract.get(field))} |")
	lines.extend(["", "## Release Boundary", ""])
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	lines.append(f"| Release blocking reasons | {_md_cell(_join(contract.get('release_blocking_reasons')))} |")
	lines.append(f"| Blocked imports | {_md_cell(_join(contract.get('blocked_scenario_ids')))} |")
	lines.append(f"| Quarantined imports | {_md_cell(_join(contract.get('quarantined_scenario_ids')))} |")
	lines.append(f"| Missing evidence | {_md_cell(_join(contract.get('missing_evidence_scenario_ids')))} |")
	lines.append(f"| Archive blocking failures | {_md_cell(_join(contract.get('archive_blocking_failure_scenario_ids')))} |")
	lines.append(f"| Duplicate evidence | {_md_cell(_join(contract.get('duplicate_evidence_ids')))} |")
	lines.extend(["", "## Composed Contract Status", ""])
	lines.append("| Contract | Complete | Release ready |")
	lines.append("|---|---|---|")
	lines.append(f"| Import batch | {_md_cell(import_batch.get('import_complete'))} | {_md_cell(import_batch.get('release_ready'))} |")
	lines.append(f"| Archive index | {_md_cell(archive_index.get('archive_complete'))} | {_md_cell(archive_index.get('release_ready'))} |")
	lines.extend(["", "## Scenario Outcomes", ""])
	lines.append("| Scenario | Import status | UAT status | Archive complete | Release blocking | Hash |")
	lines.append("|---|---|---|---|---|---|")
	archive_records = {
		_clean_text(record.get("scenario_id")): record
		for record in archive_index.get("records") or []
		if isinstance(record, dict)
	}
	for record in import_batch.get("records") or []:
		if not isinstance(record, dict):
			continue
		scenario_id = _clean_text(record.get("scenario_id")) or "unknown"
		archive_record = _clean_dict(archive_records.get(scenario_id))
		lines.append(
			"| "
			+ " | ".join(
				[
					_md_cell(scenario_id),
					_md_cell(record.get("parse_status")),
					_md_cell(record.get("uat_status")),
					_md_cell(archive_record.get("archive_complete")),
					_md_cell(record.get("release_blocking") or archive_record.get("release_blocking")),
					_md_cell(_clean_text(record.get("raw_evidence_hash"))[:12]),
				]
			)
			+ " |"
		)
	if not import_batch.get("records"):
		lines.append("| none | none | none | False | False | none |")
	lines.extend(["", "## Raw Evidence Hashes", ""])
	for evidence_hash in _clean_list(contract.get("raw_evidence_hashes")):
		lines.append(f"- {evidence_hash}")
	if not _clean_list(contract.get("raw_evidence_hashes")):
		lines.append("- none")
	return "\n".join(lines).strip() + "\n"


def write_manual_uat_evidence_bundle_files(
	capture_records: Iterable[Dict[str, Any]] | None = None,
	*,
	json_path: str = DEFAULT_MANUAL_UAT_BUNDLE_JSON_PATH,
	markdown_path: str = DEFAULT_MANUAL_UAT_BUNDLE_MARKDOWN_PATH,
	registry: Iterable[Dict[str, Any]] | None = None,
	expected_scenario_ids: Iterable[str] | None = None,
	bundle_id: str = "s7_manual_uat_evidence_bundle",
	generated_at: str = "",
	reviewer: str = "",
) -> Dict[str, Any]:
	bundle = build_manual_uat_evidence_bundle(
		capture_records,
		registry=registry,
		expected_scenario_ids=expected_scenario_ids,
		bundle_id=bundle_id,
		generated_at=generated_at,
		reviewer=reviewer,
		json_artifact_path=json_path,
		markdown_artifact_path=markdown_path,
	)
	json_target = Path(bundle["json_artifact_path"])
	markdown_target = Path(bundle["markdown_artifact_path"])
	if not json_target.is_absolute():
		json_target = Path.cwd() / json_target
	if not markdown_target.is_absolute():
		markdown_target = Path.cwd() / markdown_target
	json_target.parent.mkdir(parents=True, exist_ok=True)
	markdown_target.parent.mkdir(parents=True, exist_ok=True)
	json_target.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
	markdown_target.write_text(render_manual_uat_evidence_bundle_markdown(bundle), encoding="utf-8")
	written = dict(bundle)
	written["json_artifact_path"] = str(json_target)
	written["markdown_artifact_path"] = str(markdown_target)
	written["json_artifact_written"] = json_target.exists()
	written["markdown_artifact_written"] = markdown_target.exists()
	written["json_artifact_size_bytes"] = json_target.stat().st_size if json_target.exists() else 0
	written["markdown_artifact_size_bytes"] = markdown_target.stat().st_size if markdown_target.exists() else 0
	return written
