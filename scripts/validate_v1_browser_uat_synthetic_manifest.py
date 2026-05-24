#!/usr/bin/env python3
"""Validate the V1 browser UAT synthetic dataset manifest.

This script is intentionally passive. It reads a JSON manifest and emits a
deterministic pass/fail report. It never connects to Frappe, reads a database,
seeds records, collects traces, launches a browser, or writes runtime state.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping


EXPECTED_MANIFEST_NAME = "V1_BROWSER_UAT_SYNTHETIC_SET_001"

SMOKE_10_SCENARIOS = {
	"V1RA-001",
	"V1RA-009",
	"V1RA-017",
	"V1RA-025",
	"V1RA-033",
	"V1RA-041",
	"V1RA-049",
	"V1RA-055",
	"V1RA-061",
	"V1RA-064",
}

REQUIRED_TOP_LEVEL_SECTIONS = {
	"manifest_name",
	"site",
	"context",
	"customers",
	"suppliers",
	"items",
	"sales_invoices",
	"summaries",
	"scenario_mappings",
}

ALLOWED_EXPECTED_DATASET_STATUSES = {
	"mapped",
	"boundary_only",
	"clarification_expected",
}

REQUIRED_SUMMARY_KEYS = {
	"ar",
	"ap",
	"pnl",
	"sales",
	"boundary",
}

SUMMARY_RECORD_ID_KEYS = {
	"ar",
	"ap",
	"sales",
}

SCENARIO_ALLOWED_RECORD_FAMILIES = {
	"V1RA-001": {"customer"},
	"V1RA-009": {"supplier"},
	"V1RA-017": {"company"},
	"V1RA-025": {"customer", "item"},
	"V1RA-033": {"invoice", "customer"},
	"V1RA-041": {"customer"},
	"V1RA-049": {"customer", "supplier", "item", "company"},
	"V1RA-055": {"customer"},
	"V1RA-061": set(),
	"V1RA-064": set(),
}

CUSTOMER_ID_PATTERN = re.compile(r"^EC7H-CUST-[A-Z]$")
SUPPLIER_ID_PATTERN = re.compile(r"^EC7H-SUP-[A-Z]$")
ITEM_ID_PATTERN = re.compile(r"^EC7H-ITEM-[A-Z]$")
SALES_INVOICE_ID_PATTERN = re.compile(r"^EC7H-SINV-[0-9]{4}$")

BARE_DOCUMENT_PATTERN = re.compile(r"(?<![A-Za-z0-9-])(?:SINV|SO|PO|PINV)-[0-9]{3,}\b", re.IGNORECASE)
MARKER_LAUNDERED_DOCUMENT_PATTERN = re.compile(r"\bEC7H[_-]SYNTH[_-](?:SINV|SO|PO|PINV)-[0-9]{3,}\b", re.IGNORECASE)
LEGAL_ENTITY_PATTERN = re.compile(
	r"\b[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,5}\s+(?:Co\s+Ltd|Company\s+Limited|Trading\s+Ltd|Ltd|LLC|Inc|Pte\s+Ltd)\b"
)
PERSON_LIKE_PATTERN = re.compile(r"^[A-Z][a-z]+\s+[A-Z][a-z]+$")

REAL_LIKE_MARKERS = (
	"yoma bank",
	"global trading ltd",
	"myanmar apex",
	"acme",
	"real customer",
	"real vendor",
	"real supplier",
)

SECRET_FIELD_MARKERS = (
	"secret",
	"password",
	"token",
	"cookie",
	"session",
	"session_id",
	"api_key",
)

ARTIFACT_FIELD_MARKERS = (
	"artifact",
	"trace",
	"raw_trace",
	"redacted_trace",
	"log",
	"browser_log",
	"path",
	"screenshot",
)

FORBIDDEN_PATH_MARKERS = (
	"02_seed_data",
	"seed/data",
	"dummy_data",
	"erp_workspace_ui",
	"temp/",
	"/temp",
	"tmp/",
	"/tmp",
	"probe/",
	"/probe",
	"cache/",
	"/cache",
	"primeaxis",
	"generated/scratch",
	"raw_trace",
	"redacted_trace",
	"site_config",
	"archive",
)


def _as_text(value: Any) -> str:
	if value is None:
		return ""
	return str(value)


def _path_text(path: tuple[str, ...]) -> str:
	return ".".join(path)


def _load_manifest(path: Path) -> tuple[Mapping[str, Any] | None, list[str]]:
	try:
		loaded = json.loads(path.read_text(encoding="utf-8"))
	except FileNotFoundError:
		return None, [f"manifest_not_found:{path}"]
	except json.JSONDecodeError as exc:
		return None, [f"manifest_invalid_json:{exc.lineno}:{exc.colno}"]
	if not isinstance(loaded, Mapping):
		return None, ["manifest_must_be_object"]
	return loaded, []


def _is_customer_field(path: tuple[str, ...]) -> bool:
	return bool(path) and path[0] == "customers" and path[-1] in {"customer_id", "id"}


def _is_supplier_field(path: tuple[str, ...]) -> bool:
	return bool(path) and path[0] == "suppliers" and path[-1] in {"supplier_id", "id"}


def _is_item_field(path: tuple[str, ...]) -> bool:
	return bool(path) and path[0] == "items" and path[-1] in {"item_id", "id"}


def _is_invoice_field(path: tuple[str, ...]) -> bool:
	return bool(path) and path[0] == "sales_invoices" and path[-1] in {"invoice_id", "id"}


def _is_company_field(path: tuple[str, ...]) -> bool:
	return bool(path) and path[-1] == "company"


def _is_scenario_records_field(path: tuple[str, ...]) -> bool:
	return len(path) >= 4 and path[0] == "scenario_mappings" and path[-2] == "required_records"


def _scenario_records_id(path: tuple[str, ...]) -> str | None:
	if _is_scenario_records_field(path):
		return path[1]
	return None


def _is_summary_record_reference(path: tuple[str, ...]) -> bool:
	return len(path) >= 4 and path[0] == "summaries" and path[-2] == "record_ids"


def _is_invoice_customer_reference(path: tuple[str, ...]) -> bool:
	return len(path) >= 2 and path[0] == "sales_invoices" and path[-1] == "customer_id"


def _allowed_synthetic_id(value: str, path: tuple[str, ...]) -> bool:
	if CUSTOMER_ID_PATTERN.fullmatch(value):
		return (
			_is_customer_field(path)
			or _is_invoice_customer_reference(path)
			or _is_summary_record_reference(path)
			or _is_scenario_records_field(path)
		)
	if SUPPLIER_ID_PATTERN.fullmatch(value):
		return _is_supplier_field(path) or _is_summary_record_reference(path) or _is_scenario_records_field(path)
	if ITEM_ID_PATTERN.fullmatch(value):
		return _is_item_field(path) or _is_summary_record_reference(path) or _is_scenario_records_field(path)
	if SALES_INVOICE_ID_PATTERN.fullmatch(value):
		return _is_invoice_field(path) or _scenario_records_id(path) == "V1RA-033"
	if value == "EC7H Synthetic Company":
		return _is_company_field(path)
	return False


def _looks_real_like_name(value: str) -> bool:
	text = value.strip()
	if not text:
		return False
	lower = text.lower()
	if any(marker in lower for marker in REAL_LIKE_MARKERS):
		return True
	if LEGAL_ENTITY_PATTERN.search(text):
		return True
	if PERSON_LIKE_PATTERN.fullmatch(text) and not text.startswith("EC7H "):
		return True
	return False


def _field_is_forbidden(field_name: str, markers: Iterable[str]) -> bool:
	lower = field_name.lower()
	return any(marker in lower for marker in markers)


def _value_has_forbidden_path_marker(value: str) -> bool:
	lower = value.replace("\\", "/").lower()
	return any(marker in lower for marker in FORBIDDEN_PATH_MARKERS)


def _looks_production_site_label(value: Any) -> bool:
	text = _as_text(value).strip().lower()
	if not text:
		return False
	normalized = re.sub(r"[^a-z0-9]+", " ", text).strip()
	tokens = set(normalized.split())
	if "non production" in normalized or "nonprod" in tokens:
		return False
	return "production" in tokens or "prod" in tokens or "live" in tokens


def _declared_record_ids(manifest: Mapping[str, Any]) -> set[str]:
	declared: set[str] = set()
	for section in ("customers", "suppliers", "items"):
		records = manifest.get(section)
		if not isinstance(records, list):
			continue
		for record in records:
			if isinstance(record, Mapping):
				for field in ("id", "customer_id", "supplier_id", "item_id"):
					value = record.get(field)
					if isinstance(value, str):
						declared.add(value)
	invoices = manifest.get("sales_invoices")
	if isinstance(invoices, list):
		for invoice in invoices:
			if isinstance(invoice, Mapping):
				for field in ("id", "invoice_id"):
					value = invoice.get(field)
					if isinstance(value, str):
						declared.add(value)
	context = manifest.get("context")
	if isinstance(context, Mapping):
		company = context.get("company")
		if isinstance(company, str):
			declared.add(company)
	return declared


def _is_synthetic_reference(value: str) -> bool:
	return (
		CUSTOMER_ID_PATTERN.fullmatch(value) is not None
		or SUPPLIER_ID_PATTERN.fullmatch(value) is not None
		or ITEM_ID_PATTERN.fullmatch(value) is not None
		or SALES_INVOICE_ID_PATTERN.fullmatch(value) is not None
		or value == "EC7H Synthetic Company"
	)


def _record_family(value: str) -> str | None:
	if CUSTOMER_ID_PATTERN.fullmatch(value):
		return "customer"
	if SUPPLIER_ID_PATTERN.fullmatch(value):
		return "supplier"
	if ITEM_ID_PATTERN.fullmatch(value):
		return "item"
	if SALES_INVOICE_ID_PATTERN.fullmatch(value):
		return "invoice"
	if value == "EC7H Synthetic Company":
		return "company"
	return None


def _walk_values(value: Any, path: tuple[str, ...], violations: list[str]) -> None:
	path_label = _path_text(path)
	if path:
		field_name = path[-1]
		if _field_is_forbidden(field_name, SECRET_FIELD_MARKERS):
			violations.append(f"{path_label}:forbidden_secret_field")
		if _field_is_forbidden(field_name, ARTIFACT_FIELD_MARKERS):
			violations.append(f"{path_label}:forbidden_artifact_field")

	if isinstance(value, Mapping):
		for key, child in value.items():
			_walk_values(child, path + (str(key),), violations)
		return

	if isinstance(value, list):
		for index, child in enumerate(value):
			_walk_values(child, path + (str(index),), violations)
		return

	if not isinstance(value, str):
		return

	if _allowed_synthetic_id(value, path):
		return

	if value.startswith("EC7H-") and any(
		pattern.fullmatch(value)
		for pattern in (CUSTOMER_ID_PATTERN, SUPPLIER_ID_PATTERN, ITEM_ID_PATTERN, SALES_INVOICE_ID_PATTERN)
	):
		violations.append(f"{path_label}:synthetic_id_wrong_field:{value}")
		return

	if MARKER_LAUNDERED_DOCUMENT_PATTERN.search(value):
		violations.append(f"{path_label}:marker_laundered_document_id")
	if BARE_DOCUMENT_PATTERN.search(value):
		violations.append(f"{path_label}:bare_production_document_id")
	if _looks_real_like_name(value):
		violations.append(f"{path_label}:real_like_name")
	if _value_has_forbidden_path_marker(value):
		violations.append(f"{path_label}:forbidden_path_value")


def _validate_record_ids(records: Any, allowed_pattern: re.Pattern[str], prefix: str, violations: list[str]) -> None:
	if not isinstance(records, list) or not records:
		violations.append(f"{prefix}:must_be_non_empty_list")
		return
	for index, record in enumerate(records):
		if not isinstance(record, Mapping):
			violations.append(f"{prefix}[{index}]:must_be_object")
			continue
		record_id = record.get("id") or record.get(f"{prefix[:-1]}_id")
		if not isinstance(record_id, str) or not allowed_pattern.fullmatch(record_id):
			violations.append(f"{prefix}[{index}]:invalid_id:{record_id!r}")


def _validate_summaries(summaries: Any, violations: list[str]) -> None:
	if not isinstance(summaries, Mapping):
		violations.append("summaries:must_be_object")
		return
	for key in sorted(REQUIRED_SUMMARY_KEYS - set(str(item) for item in summaries)):
		violations.append(f"summaries:missing_required_summary_key:{key}")
	for key in sorted(REQUIRED_SUMMARY_KEYS & set(str(item) for item in summaries)):
		value = summaries.get(key)
		if not isinstance(value, Mapping):
			violations.append(f"summaries.{key}:must_be_object")
			continue
		if key in SUMMARY_RECORD_ID_KEYS:
			record_ids = value.get("record_ids")
			if not isinstance(record_ids, list) or not record_ids:
				violations.append(f"summaries.{key}.record_ids:must_be_non_empty_list")


def validate_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
	violations: list[str] = []

	manifest_name = manifest.get("manifest_name")
	if manifest_name != EXPECTED_MANIFEST_NAME:
		violations.append(f"manifest_name_mismatch:{manifest_name!r}")

	for section in sorted(REQUIRED_TOP_LEVEL_SECTIONS - set(manifest)):
		violations.append(f"missing_top_level_section:{section}")

	site = manifest.get("site")
	if not isinstance(site, Mapping):
		violations.append("site:must_be_object")
	else:
		environment_type = site.get("environment_type")
		if environment_type != "non_production":
			violations.append(f"site.environment_type_must_be_non_production:{environment_type!r}")
		site_label = site.get("site_label") or site.get("label")
		if _looks_production_site_label(site_label):
			violations.append(f"site.site_label_production_like:{site_label!r}")

	_validate_record_ids(manifest.get("customers"), CUSTOMER_ID_PATTERN, "customers", violations)
	_validate_record_ids(manifest.get("suppliers"), SUPPLIER_ID_PATTERN, "suppliers", violations)
	_validate_record_ids(manifest.get("items"), ITEM_ID_PATTERN, "items", violations)

	invoices = manifest.get("sales_invoices")
	if not isinstance(invoices, list) or not invoices:
		violations.append("sales_invoices:must_be_non_empty_list")
	else:
		for index, invoice in enumerate(invoices):
			if not isinstance(invoice, Mapping):
				violations.append(f"sales_invoices[{index}]:must_be_object")
				continue
			invoice_id = invoice.get("invoice_id") or invoice.get("id")
			if not isinstance(invoice_id, str) or not SALES_INVOICE_ID_PATTERN.fullmatch(invoice_id):
				violations.append(f"sales_invoices[{index}]:invalid_invoice_id:{invoice_id!r}")

	_validate_summaries(manifest.get("summaries"), violations)

	scenario_mappings = manifest.get("scenario_mappings")
	if not isinstance(scenario_mappings, Mapping):
		violations.append("scenario_mappings:must_be_object")
		scenario_mappings = {}

	scenario_ids = set(str(key) for key in scenario_mappings)
	for scenario_id in sorted(scenario_ids - SMOKE_10_SCENARIOS):
		violations.append(f"unknown_scenario_id:{scenario_id}")
	for scenario_id in sorted(SMOKE_10_SCENARIOS - scenario_ids):
		violations.append(f"missing_smoke_10_mapping:{scenario_id}")

	for scenario_id, mapping in scenario_mappings.items():
		prefix = f"scenario_mappings.{scenario_id}"
		if not isinstance(mapping, Mapping):
			violations.append(f"{prefix}:must_be_object")
			continue
		if "required_records" not in mapping:
			violations.append(f"{prefix}:missing_required_records")
		elif not isinstance(mapping["required_records"], list):
			violations.append(f"{prefix}:required_records_must_be_list")
		if "expected_dataset_status" not in mapping:
			violations.append(f"{prefix}:missing_expected_dataset_status")
		elif mapping["expected_dataset_status"] not in ALLOWED_EXPECTED_DATASET_STATUSES:
			violations.append(
				f"{prefix}:invalid_expected_dataset_status:{mapping['expected_dataset_status']!r}"
			)

	declared_ids = _declared_record_ids(manifest)
	for scenario_id, mapping in scenario_mappings.items():
		if not isinstance(mapping, Mapping):
			continue
		required_records = mapping.get("required_records")
		if not isinstance(required_records, list):
			continue
		for index, record_id in enumerate(required_records):
			if isinstance(record_id, str) and _is_synthetic_reference(record_id) and record_id not in declared_ids:
				violations.append(
					f"scenario_mappings.{scenario_id}.required_records.{index}:undeclared_synthetic_reference:{record_id}"
				)
			if isinstance(record_id, str):
				family = _record_family(record_id)
				allowed_families = SCENARIO_ALLOWED_RECORD_FAMILIES.get(str(scenario_id))
				if family is not None and allowed_families is not None and family not in allowed_families:
					violations.append(
						f"scenario_mappings.{scenario_id}.required_records.{index}:wrong_record_family:{family}"
					)

	_walk_values(manifest, tuple(), violations)

	valid = not violations
	return {
		"manifest_name": manifest_name,
		"expected_manifest_name": EXPECTED_MANIFEST_NAME,
		"runtime_effect": "none",
		"valid": valid,
		"smoke_10_scenarios": sorted(SMOKE_10_SCENARIOS),
		"violations": violations,
	}


def validate_manifest_path(path: str | Path) -> dict[str, Any]:
	manifest_path = Path(path)
	manifest, load_violations = _load_manifest(manifest_path)
	if manifest is None:
		return {
			"manifest_name": None,
			"expected_manifest_name": EXPECTED_MANIFEST_NAME,
			"runtime_effect": "none",
			"valid": False,
			"smoke_10_scenarios": sorted(SMOKE_10_SCENARIOS),
			"violations": load_violations,
		}
	return validate_manifest(manifest)


def main(argv: Iterable[str] | None = None) -> int:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("manifest_path", help="Path to V1 browser UAT synthetic manifest JSON.")
	args = parser.parse_args(list(argv) if argv is not None else None)

	report = validate_manifest_path(args.manifest_path)
	print(json.dumps(report, indent=2, sort_keys=True))
	return 0 if report["valid"] else 1


if __name__ == "__main__":
	sys.exit(main())
