#!/usr/bin/env python3
"""Check EC-7H controlled environment readiness without changing anything."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Dict, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent


def _load_script_module(name: str, path: Path):
	spec = importlib.util.spec_from_file_location(name, path)
	module = importlib.util.module_from_spec(spec)
	assert spec.loader is not None
	spec.loader.exec_module(module)
	return module


dataset_validator = _load_script_module(
	"validate_ec7h_synthetic_dataset",
	SCRIPT_DIR / "validate_ec7h_synthetic_dataset.py",
)
archive_checker = _load_script_module(
	"check_ec7h_archive_readiness",
	SCRIPT_DIR / "check_ec7h_archive_readiness.py",
)

FORBIDDEN_OUTPUT_PATH_PARTS = (
	"/cache/",
	"/erp_ui/",
	"/probe/",
	"/seed/data/",
	"/temp/",
	"erp_workspace_ui",
	"02_seed_data",
	"cache/",
	"dummy_data",
	"erp_ui",
	"probe/",
	"seed/data",
	"temp/",
	"tmp/",
	".codex_tmp",
	"primeaxis",
	"generated/qwen_s7_browser_batch",
)

SOURCE_CHECKOUT_MARKERS = (
	"impl_factory",
	"scripts/check_qwen_enterprise_guardrails.py",
)

SAFE_SITE_NAME_PART_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
FRAPPE_SITE_CONFIG_KEYS = {
	"db_name",
	"db_password",
	"db_type",
	"db_host",
	"db_port",
	"developer_mode",
	"encryption_key",
	"redis_cache",
	"redis_queue",
	"redis_socketio",
	"socketio_port",
}


def _git_lines(args: list[str], repo_root: Path) -> list[str]:
	try:
		result = subprocess.run(
			["git", *args],
			cwd=repo_root,
			text=True,
			stdout=subprocess.PIPE,
			stderr=subprocess.DEVNULL,
			check=False,
		)
	except FileNotFoundError:
		return ["git_not_available"]
	return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _path_has_forbidden_part(path: str | Path) -> bool:
	normalized_path = str(path).replace("\\", "/").lower().strip("/")
	normalized = f"/{normalized_path}/"
	return any(part.lower() in normalized for part in FORBIDDEN_OUTPUT_PATH_PARTS)


def _is_relative_to(path: Path, parent: Path) -> bool:
	try:
		path.resolve().relative_to(parent.resolve())
		return True
	except ValueError:
		return False


def _site_name_validation(bench: Path, site_name: str) -> Dict[str, Any]:
	normalized_site_name = str(site_name or "").strip()
	violations: list[str] = []
	if not normalized_site_name:
		violations.append("site_name_missing")
	if normalized_site_name in {".", ".."}:
		violations.append("site_name_dot_or_parent")
	if "/" in normalized_site_name or "\\" in normalized_site_name:
		violations.append("site_name_contains_path_separator")
	parts = normalized_site_name.split(".") if normalized_site_name else []
	if parts and not all(part and SAFE_SITE_NAME_PART_RE.fullmatch(part) for part in parts):
		violations.append("site_name_invalid_characters_or_empty_part")

	sites_root = bench / "sites"
	site_path = sites_root / normalized_site_name if normalized_site_name else sites_root
	try:
		site_path_inside_sites = site_path.resolve(strict=False).relative_to(
			sites_root.resolve(strict=False)
		) is not None
	except ValueError:
		site_path_inside_sites = False
	if normalized_site_name and not site_path_inside_sites:
		violations.append("site_name_path_escapes_sites")

	return {
		"site_name_normalized": normalized_site_name,
		"site_name_valid": not violations,
		"site_name_violations": violations,
		"site_path_inside_sites": site_path_inside_sites,
		"site_path": site_path,
	}


def _site_config_validation(site_config_path: Path) -> Dict[str, Any]:
	violations: list[str] = []
	expected_keys_present: list[str] = []
	site_config_exists = site_config_path.exists()
	site_config_is_symlink = site_config_path.is_symlink()
	if not site_config_exists:
		violations.append("site_config_missing")
	elif site_config_is_symlink:
		violations.append("site_config_is_symlink")
	elif not site_config_path.is_file():
		violations.append("site_config_not_file")
	else:
		try:
			raw_config = site_config_path.read_text(encoding="utf-8")
		except OSError:
			violations.append("site_config_unreadable")
		else:
			if not raw_config.strip():
				violations.append("site_config_empty")
			else:
				try:
					parsed_config = json.loads(raw_config)
				except json.JSONDecodeError:
					violations.append("site_config_invalid_json")
				else:
					if not isinstance(parsed_config, dict):
						violations.append("site_config_not_object")
					else:
						expected_keys_present = sorted(
							key for key in parsed_config if key in FRAPPE_SITE_CONFIG_KEYS
						)
						if not expected_keys_present:
							violations.append("site_config_missing_expected_frappe_key")

	return {
		"site_config_exists": site_config_exists,
		"site_config_is_symlink": site_config_is_symlink,
		"site_config_valid": not violations,
		"site_config_violations": violations,
		"site_config_expected_keys_present": expected_keys_present,
	}


def _bench_evidence(bench: Path, site_name: str) -> Dict[str, Any]:
	site_validation = _site_name_validation(bench, site_name)
	site_name = site_validation["site_name_normalized"]
	sites_exists = (bench / "sites").is_dir()
	apps_exists = (bench / "apps").is_dir()
	procfile_exists = (bench / "Procfile").is_file()
	common_site_config_exists = (bench / "sites" / "common_site_config.json").is_file()
	site_dir = site_validation["site_path"]
	site_dir_exists = site_validation["site_name_valid"] and site_dir.is_dir()
	site_config_path = site_dir / "site_config.json"
	site_config_report = (
		_site_config_validation(site_config_path)
		if site_validation["site_name_valid"]
		else {
			"site_config_exists": False,
			"site_config_is_symlink": False,
			"site_config_valid": False,
			"site_config_violations": ["site_name_invalid"],
			"site_config_expected_keys_present": [],
		}
	)
	site_config_exists = site_config_report["site_config_exists"]
	evidence_paths = [
		marker
		for marker, exists in (
			("sites", sites_exists),
			("apps", apps_exists),
			("Procfile", procfile_exists),
			("sites/common_site_config.json", common_site_config_exists),
			(f"sites/{site_name}", site_dir_exists),
			(f"sites/{site_name}/site_config.json", site_config_exists),
		)
		if exists
	]
	source_markers = [marker for marker in SOURCE_CHECKOUT_MARKERS if (bench / marker).exists()]
	looks_like_temp = str(bench).replace("\\", "/").startswith(("/tmp/", "/var/tmp/"))
	has_site_specific_evidence = site_config_report["site_config_valid"]
	has_strong_bench_evidence = (
		sites_exists
		and apps_exists
		and site_validation["site_name_valid"]
		and has_site_specific_evidence
		and not source_markers
	)
	return {
		"evidence_paths": evidence_paths,
		"sites_exists": sites_exists,
		"apps_exists": apps_exists,
		"procfile_exists": procfile_exists,
		"common_site_config_exists": common_site_config_exists,
		"site_dir_exists": site_dir_exists,
		"site_config_exists": site_config_exists,
		"site_config_is_symlink": site_config_report["site_config_is_symlink"],
		"site_config_valid": site_config_report["site_config_valid"],
		"site_config_violations": site_config_report["site_config_violations"],
		"site_config_expected_keys_present": site_config_report["site_config_expected_keys_present"],
		"has_site_specific_evidence": has_site_specific_evidence,
		"site_name_valid": site_validation["site_name_valid"],
		"site_name_violations": site_validation["site_name_violations"],
		"site_path_inside_sites": site_validation["site_path_inside_sites"],
		"source_checkout_markers": source_markers,
		"looks_like_temp": looks_like_temp,
		"has_strong_bench_evidence": has_strong_bench_evidence,
	}


def check_environment_readiness(
	*,
	bench_path: str | Path,
	site_name: str,
	qa_user: str,
	dataset_manifest_path: str | Path,
	archive_path: str | Path,
	raw_trace_custodian: str,
	redacted_output_candidate_path: str | Path,
	repo_root: str | Path = ".",
	expected_archive_owner: str | None = None,
	expected_archive_group: str | None = None,
	archive_retention_marker: str | None = None,
) -> Dict[str, Any]:
	repo_root_path = Path(repo_root)
	bench = Path(bench_path)
	dataset_manifest = Path(dataset_manifest_path)
	archive = Path(archive_path)
	redacted_output = Path(redacted_output_candidate_path)

	blockers: list[str] = []
	warnings: list[str] = []

	bench_path_exists = bench.exists() and bench.is_dir()
	if not bench_path_exists:
		blockers.append("bench_path_missing")
	bench_evidence = _bench_evidence(bench, site_name) if bench_path_exists else {
		"evidence_paths": [],
		"sites_exists": False,
		"apps_exists": False,
		"procfile_exists": False,
		"common_site_config_exists": False,
		"site_dir_exists": False,
		"site_config_exists": False,
		"site_config_is_symlink": False,
		"site_config_valid": False,
		"site_config_violations": ["bench_path_missing"],
		"site_config_expected_keys_present": [],
		"has_site_specific_evidence": False,
		"site_name_valid": False,
		"site_name_violations": ["bench_path_missing"],
		"site_path_inside_sites": False,
		"source_checkout_markers": [],
		"looks_like_temp": False,
		"has_strong_bench_evidence": False,
	}
	bench_path_inside_repo = bench_path_exists and _is_relative_to(bench, repo_root_path)
	if bench_path_inside_repo:
		blockers.append("bench_path_inside_repo")
	if bench_evidence["source_checkout_markers"]:
		blockers.append("bench_path_is_source_checkout")
	if bench_evidence["looks_like_temp"] and not bench_evidence["has_strong_bench_evidence"]:
		blockers.append("bench_path_is_temp")
	if bench_path_exists and not bench_evidence["has_strong_bench_evidence"]:
		blockers.append("bench_path_lacks_controlled_bench_evidence")

	site_name_provided = bool(str(site_name or "").strip())
	if not site_name_provided:
		blockers.append("site_name_missing")
	if bench_path_exists and not bench_evidence["site_name_valid"]:
		blockers.append("site_name_invalid")
	if bench_path_exists and bench_evidence["site_name_valid"] and not bench_evidence["site_config_valid"]:
		blockers.append("site_config_invalid")

	qa_user_provided = bool(str(qa_user or "").strip())
	if not qa_user_provided:
		blockers.append("qa_user_missing")
	elif "qa_ec7h_trace_user" not in str(qa_user):
		warnings.append("qa_user_not_preferred_name")

	raw_trace_custodian_named = bool(str(raw_trace_custodian or "").strip())
	if not raw_trace_custodian_named:
		blockers.append("raw_trace_custodian_missing")

	dataset_manifest_exists = dataset_manifest.exists() and dataset_manifest.is_file()
	dataset_report = dataset_validator.validate_manifest_path(dataset_manifest)
	if not dataset_manifest_exists:
		blockers.append("dataset_manifest_missing")
	elif not dataset_report.get("valid"):
		blockers.append("dataset_manifest_invalid")

	archive_report = archive_checker.check_archive_readiness(
		path=archive,
		expected_owner=expected_archive_owner,
		expected_group=expected_archive_group,
		retention_marker=archive_retention_marker,
		repo_root=repo_root_path,
	)
	if not archive_report.get("valid"):
		blockers.append("archive_readiness_invalid")

	redacted_output_policy_defined = bool(str(redacted_output_candidate_path or "").strip())
	redacted_output_forbidden = _path_has_forbidden_part(redacted_output)
	if not redacted_output_policy_defined:
		blockers.append("redacted_output_candidate_missing")
	if redacted_output_forbidden:
		blockers.append("redacted_output_candidate_forbidden_stream")

	staged_files = _git_lines(["diff", "--cached", "--name-only"], repo_root_path)
	no_staged_files = not staged_files
	if not no_staged_files:
		blockers.append("staged_files_present")

	status_lines = _git_lines(["status", "--short"], repo_root_path)
	excluded_status_entries = [
		line for line in status_lines if _path_has_forbidden_part(line)
	]
	excluded_status_clean = not excluded_status_entries
	if not excluded_status_clean:
		blockers.append("excluded_status_entries_present")

	ready = not blockers
	return {
		"runtime_effect": "none",
		"ready": ready,
		"decision": "environment_ready_for_collection_request" if ready else "environment_not_ready",
		"bench_path": str(bench),
		"bench_path_exists": bench_path_exists,
		"bench_path_inside_repo": bench_path_inside_repo,
		"bench_evidence": bench_evidence,
		"site_name": site_name,
		"site_name_provided": site_name_provided,
		"site_name_valid": bench_evidence["site_name_valid"],
		"site_name_violations": bench_evidence["site_name_violations"],
		"qa_user": qa_user,
		"qa_user_provided": qa_user_provided,
		"dataset_manifest_path": str(dataset_manifest),
		"dataset_manifest_exists": dataset_manifest_exists,
		"dataset_report": dataset_report,
		"archive_path": str(archive),
		"archive_report": archive_report,
		"raw_trace_custodian": raw_trace_custodian,
		"raw_trace_custodian_named": raw_trace_custodian_named,
		"redacted_output_candidate_path": str(redacted_output),
		"redacted_output_policy_defined": redacted_output_policy_defined,
		"redacted_output_forbidden": redacted_output_forbidden,
		"staged_file_count": len(staged_files),
		"staged_files": staged_files,
		"excluded_status_entries": excluded_status_entries,
		"blockers": blockers,
		"warnings": warnings,
	}


def main(argv: Iterable[str] | None = None) -> int:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--bench-path", required=True)
	parser.add_argument("--site-name", required=True)
	parser.add_argument("--qa-user", required=True)
	parser.add_argument("--dataset-manifest-path", required=True)
	parser.add_argument("--archive-path", required=True)
	parser.add_argument("--raw-trace-custodian", required=True)
	parser.add_argument("--redacted-output-candidate-path", required=True)
	parser.add_argument("--repo-root", default=".")
	parser.add_argument("--expected-archive-owner", default=None)
	parser.add_argument("--expected-archive-group", default=None)
	parser.add_argument("--archive-retention-marker", default=None)
	args = parser.parse_args(list(argv) if argv is not None else None)

	report = check_environment_readiness(
		bench_path=args.bench_path,
		site_name=args.site_name,
		qa_user=args.qa_user,
		dataset_manifest_path=args.dataset_manifest_path,
		archive_path=args.archive_path,
		raw_trace_custodian=args.raw_trace_custodian,
		redacted_output_candidate_path=args.redacted_output_candidate_path,
		repo_root=args.repo_root,
		expected_archive_owner=args.expected_archive_owner,
		expected_archive_group=args.expected_archive_group,
		archive_retention_marker=args.archive_retention_marker,
	)
	print(json.dumps(report, indent=2, sort_keys=True))
	return 0 if report["ready"] else 1


if __name__ == "__main__":
	sys.exit(main())
