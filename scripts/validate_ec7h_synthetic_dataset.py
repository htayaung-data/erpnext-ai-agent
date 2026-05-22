#!/usr/bin/env python3
"""Validate the EC-7H light-semantic synthetic dataset manifest.

This script is intentionally passive. It reads a JSON manifest and emits a
deterministic pass/fail report. It never connects to Frappe, reads a database,
seeds records, collects traces, or writes runtime state.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping


EXPECTED_DATASET_ID = "EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001"

REQUIRED_LANES = {
	"frontdoor_semantic_classification",
	"fresh_query_interpretation",
	"followup_interpretation",
	"semantic_reasoning_activation",
	"semantic_repair_intent",
}

ALLOWED_SCENARIO_TYPES = {
	"accepted_success",
	"degraded_low_confidence",
	"missing_metadata",
	"not_applicable",
	"rejected",
	"runtime_error_fallback",
}

REQUIRED_SCENARIO_FIELDS = {
	"scenario_id",
	"lane_id",
	"scenario_type",
	"synthetic_prompt",
	"synthetic_record_reference",
	"expected_metadata_status",
	"expected_strict_readiness_status",
	"expected_fallback_used",
	"expected_fallback_reason",
	"expected_authority_status",
	"redaction_expectation",
}

SYNTHETIC_MARKERS = (
	"ec7h synthetic",
	"ec7h_synth",
	"synthetic only",
	"synthetic_",
)

RAW_BUSINESS_MARKERS = (
	"acme",
	"global trading",
	"myanmar apex",
	"yoma",
	"customer ltd",
	"vendor llc",
	"supplier inc",
	"real customer",
	"real vendor",
	"real supplier",
)

PRODUCTION_DOC_PATTERN = re.compile(r"(?<![A-Za-z0-9])(?:SINV|SO|PO|ACC|DN|PI)-\d{3,}\b", re.IGNORECASE)
LEGAL_ENTITY_PATTERN = re.compile(
	r"\b[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,5}\s+(?:Co\s+Ltd|Company\s+Limited|Ltd|LLC|Inc|Pte\s+Ltd)\b"
)


def _as_text(value: Any) -> str:
	if value is None:
		return ""
	return str(value)


def _has_synthetic_marker(value: Any) -> bool:
	text = _as_text(value).strip().lower()
	return any(marker in text for marker in SYNTHETIC_MARKERS)


def _looks_like_raw_business_identifier(value: Any) -> bool:
	text = _as_text(value).strip()
	if not text:
		return False
	lower = text.lower()
	if any(marker in lower for marker in RAW_BUSINESS_MARKERS):
		return True
	if PRODUCTION_DOC_PATTERN.search(text):
		return True
	if LEGAL_ENTITY_PATTERN.search(text):
		return True
	return False


def _load_manifest(path: Path) -> tuple[Dict[str, Any] | None, List[str]]:
	try:
		return json.loads(path.read_text(encoding="utf-8")), []
	except FileNotFoundError:
		return None, [f"manifest_not_found:{path}"]
	except json.JSONDecodeError as exc:
		return None, [f"manifest_invalid_json:{exc.lineno}:{exc.colno}"]


def validate_manifest(manifest: Mapping[str, Any]) -> Dict[str, Any]:
	violations: List[str] = []

	dataset_id = manifest.get("dataset_id")
	if dataset_id != EXPECTED_DATASET_ID:
		violations.append(f"dataset_id_mismatch:{dataset_id!r}")

	if manifest.get("data_classification") != "synthetic_only":
		violations.append("data_classification_must_be_synthetic_only")

	if not manifest.get("schema_version"):
		violations.append("missing_schema_version")

	if not manifest.get("qa_owner"):
		violations.append("missing_qa_owner")

	scenarios = manifest.get("scenarios")
	if not isinstance(scenarios, list) or not scenarios:
		violations.append("scenarios_must_be_non_empty_list")
		scenarios = []

	lane_coverage = {lane: 0 for lane in REQUIRED_LANES}
	scenario_type_coverage = {scenario_type: 0 for scenario_type in ALLOWED_SCENARIO_TYPES}

	for index, scenario in enumerate(scenarios):
		prefix = f"scenarios[{index}]"
		if not isinstance(scenario, Mapping):
			violations.append(f"{prefix}:must_be_object")
			continue

		missing = sorted(field for field in REQUIRED_SCENARIO_FIELDS if field not in scenario)
		for field in missing:
			violations.append(f"{prefix}:missing_{field}")

		lane_id = scenario.get("lane_id")
		if lane_id not in REQUIRED_LANES:
			violations.append(f"{prefix}:unknown_lane:{lane_id!r}")
		else:
			lane_coverage[lane_id] += 1

		scenario_type = scenario.get("scenario_type")
		if scenario_type not in ALLOWED_SCENARIO_TYPES:
			violations.append(f"{prefix}:unknown_scenario_type:{scenario_type!r}")
		else:
			scenario_type_coverage[scenario_type] += 1

		prompt = scenario.get("synthetic_prompt")
		record_ref = scenario.get("synthetic_record_reference")
		if not _has_synthetic_marker(prompt) and not _has_synthetic_marker(record_ref):
			violations.append(f"{prefix}:missing_synthetic_marker")

		for field in ("synthetic_prompt", "synthetic_record_reference"):
			value = scenario.get(field)
			if _looks_like_raw_business_identifier(value):
				violations.append(f"{prefix}:{field}_raw_business_identifier")

		for field, value in scenario.items():
			if field in {"synthetic_prompt", "synthetic_record_reference"}:
				continue
			if isinstance(value, str) and _looks_like_raw_business_identifier(value):
				violations.append(f"{prefix}:{field}_raw_business_identifier")

	missing_lanes = sorted(lane for lane, count in lane_coverage.items() if count == 0)
	for lane in missing_lanes:
		violations.append(f"missing_lane_coverage:{lane}")

	valid = not violations
	return {
		"dataset_id": dataset_id,
		"expected_dataset_id": EXPECTED_DATASET_ID,
		"runtime_effect": "none",
		"valid": valid,
		"scenario_count": len(scenarios),
		"lane_coverage": lane_coverage,
		"scenario_type_coverage": scenario_type_coverage,
		"violations": violations,
	}


def validate_manifest_path(path: str | Path) -> Dict[str, Any]:
	manifest_path = Path(path)
	manifest, load_violations = _load_manifest(manifest_path)
	if manifest is None:
		return {
			"dataset_id": None,
			"expected_dataset_id": EXPECTED_DATASET_ID,
			"runtime_effect": "none",
			"valid": False,
			"scenario_count": 0,
			"lane_coverage": {lane: 0 for lane in REQUIRED_LANES},
			"scenario_type_coverage": {scenario_type: 0 for scenario_type in ALLOWED_SCENARIO_TYPES},
			"violations": load_violations,
		}
	return validate_manifest(manifest)


def main(argv: Iterable[str] | None = None) -> int:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("manifest_path", help="Path to EC-7H synthetic dataset manifest JSON.")
	args = parser.parse_args(list(argv) if argv is not None else None)

	report = validate_manifest_path(args.manifest_path)
	print(json.dumps(report, indent=2, sort_keys=True))
	return 0 if report["valid"] else 1


if __name__ == "__main__":
	sys.exit(main())
