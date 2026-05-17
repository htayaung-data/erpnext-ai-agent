from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


FRONTDOOR_EMISSION_MAPPING_CONTRACT_TYPE = "qwen_ec4b_frontdoor_emission_mapping_report"
CONTRACT_VERSION = "1.2"

PROJECT_RELATIVE_PACKAGE_FRONTDOOR = (
	"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/"
	"qwen_chat/lanes/frontdoor_lane.py"
)
PROJECT_RELATIVE_ROOT_FRONTDOOR = (
	"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/"
	"qwen_chat/frontdoor_lane.py"
)
PROJECT_RELATIVE_SERVICE = (
	"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/"
	"qwen_chat/service.py"
)
TESTS_ROOT = "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests"


def _assistant_append_needle() -> str:
	return "append_" + "message(session_doc, " + json.dumps("assistant")


def _authorized_emission_needle() -> str:
	return "emit_authorized_assistant_answer("


def _utc_now() -> str:
	return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _read_text(root_path: Path, relative_path: str) -> str:
	path = root_path / relative_path
	return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def _sha256(text: str) -> str:
	return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _line_numbers_containing(text: str, needle: str) -> List[int]:
	return [index for index, line in enumerate(text.splitlines(), start=1) if needle in line]


def _line_numbers_starting_with(text: str, prefix: str) -> List[int]:
	return [index for index, line in enumerate(text.splitlines(), start=1) if line.startswith(prefix)]


def _root_frontdoor_is_facade(text: str) -> bool:
	return (
		"Compatibility facade" in text
		and "ai_assistant_ui.qwen_chat.lanes.frontdoor_lane" in text
		and not _line_numbers_containing(text, _assistant_append_needle())
	)


def _git_short_head(root_path: Path) -> str:
	try:
		return subprocess.check_output(
			["git", "rev-parse", "--short", "HEAD"],
			cwd=str(root_path),
			text=True,
			stderr=subprocess.DEVNULL,
		).strip()
	except Exception:
		return ""


def _git_branch(root_path: Path) -> str:
	try:
		return subprocess.check_output(
			["git", "branch", "--show-current"],
			cwd=str(root_path),
			text=True,
			stderr=subprocess.DEVNULL,
		).strip()
	except Exception:
		return ""


def _git_status_count(root_path: Path) -> int:
	try:
		output = subprocess.check_output(
			["git", "status", "--short"],
			cwd=str(root_path),
			text=True,
			stderr=subprocess.DEVNULL,
		)
	except Exception:
		return 0
	return len([line for line in output.splitlines() if line.strip()])


def _service_import_evidence(service_text: str) -> Dict[str, Any]:
	lines = service_text.splitlines()
	package_import_lines = [
		index
		for index, line in enumerate(lines, start=1)
		if "from ai_assistant_ui.qwen_chat.lanes.frontdoor_lane import" in line
	]
	root_import_lines = [
		index
		for index, line in enumerate(lines, start=1)
		if "from ai_assistant_ui.qwen_chat.frontdoor_lane import" in line
	]
	return {
		"package_imported_by_service": bool(package_import_lines),
		"package_import_lines": package_import_lines,
		"root_imported_by_service": bool(root_import_lines),
		"root_import_lines": root_import_lines,
		"service_call_sites": {
			"evaluate_frontdoor_lane": _line_numbers_containing(service_text, "evaluate_frontdoor_lane("),
			"handle_frontdoor_turn": _line_numbers_containing(service_text, "handle_frontdoor_turn("),
		},
	}


def _test_import_evidence(root_path: Path) -> Dict[str, Any]:
	tests_dir = root_path / TESTS_ROOT
	package_imports: List[Dict[str, Any]] = []
	root_imports: List[Dict[str, Any]] = []
	if not tests_dir.exists():
		return {"package_imports": [], "root_imports": []}
	for path in sorted(tests_dir.rglob("*.py")):
		text = path.read_text(encoding="utf-8", errors="ignore")
		for index, line in enumerate(text.splitlines(), start=1):
			relative = str(path.relative_to(root_path))
			if "ai_assistant_ui.qwen_chat.lanes.frontdoor_lane" in line:
				package_imports.append({"file": relative, "line": index, "text": line.strip()})
			if "ai_assistant_ui.qwen_chat.frontdoor_lane" in line:
				root_imports.append({"file": relative, "line": index, "text": line.strip()})
	return {
		"package_imports": package_imports,
		"root_imports": root_imports,
	}


def _frontdoor_file_summary(
	*,
	root_path: Path,
	relative_path: str,
	path_id: str,
	active_classification: str,
	migration_recommendation: str,
	reason: str,
	service_imported: bool,
) -> Dict[str, Any]:
	text = _read_text(root_path, relative_path)
	append_lines = _line_numbers_containing(text, _assistant_append_needle())
	authorized_helper_lines = _line_numbers_containing(text, _authorized_emission_needle())
	uses_authorized_helper = bool(authorized_helper_lines)
	if append_lines:
		append_mechanism = "direct_append_message"
		audit_timing = "audit_envelope_after_assistant_append"
		authority_status = "audit_created_after_append"
	elif uses_authorized_helper:
		append_mechanism = "authorized_assistant_emission_helper"
		audit_timing = "audit_and_emission_contract_before_assistant_append"
		authority_status = "authority_validated_before_append"
	else:
		append_mechanism = "none_observed"
		audit_timing = "none_observed"
		authority_status = "no_assistant_append_observed"
	return {
		"path_id": path_id,
		"relative_file_path": relative_path,
		"function_names": {
			"evaluate_frontdoor_lane": _line_numbers_starting_with(text, "def evaluate_frontdoor_lane("),
			"handle_frontdoor_turn": _line_numbers_starting_with(text, "def handle_frontdoor_turn("),
		},
		"direct_assistant_append_lines": append_lines,
		"direct_assistant_append_count": len(append_lines),
		"authorized_emission_helper_lines": authorized_helper_lines,
		"authorized_emission_helper_count": len(authorized_helper_lines),
		"answer_type": "governed_report_or_policy_boundary_or_control",
		"append_mechanism": append_mechanism,
		"audit_timing": audit_timing,
		"authority_availability_status": authority_status,
		"active_classification": active_classification,
		"service_imported": bool(service_imported),
		"runtime_behavior_changed": uses_authorized_helper,
		"migration_recommendation": migration_recommendation,
		"reason": reason,
		"line_count": len(text.splitlines()),
		"sha256": _sha256(text) if text else "",
	}


def _frontdoor_diff_summary(*, package_text: str, root_text: str) -> Dict[str, Any]:
	root_is_facade = _root_frontdoor_is_facade(root_text)
	return {
		"files_identical": bool(package_text and root_text and package_text == root_text),
		"package_line_count": len(package_text.splitlines()),
		"root_line_count": len(root_text.splitlines()),
		"line_count_delta_package_minus_root": len(package_text.splitlines()) - len(root_text.splitlines()),
		"package_has_fresh_breakout_helper": "_frontdoor_contract_can_handle_fresh_breakout" in package_text,
		"root_has_fresh_breakout_helper": "_frontdoor_contract_can_handle_fresh_breakout" in root_text,
		"root_is_compatibility_facade": root_is_facade,
		"root_duplicate_drift_reason": (
			"Root frontdoor module is now an EC-4U compatibility facade over the active package lane."
			if root_is_facade
			else (
				"Root frontdoor module is duplicate drift: a full implementation that is not imported by service.py and lacks "
				"the newer fresh-breakout helper present in the active package lane."
			)
		),
	}


def build_frontdoor_emission_mapping_report(
	*,
	root_path: str | Path = ".",
	reviewer: str = "codex_ec4b_frontdoor_mapping",
) -> Dict[str, Any]:
	root = Path(root_path).resolve()
	package_text = _read_text(root, PROJECT_RELATIVE_PACKAGE_FRONTDOOR)
	root_text = _read_text(root, PROJECT_RELATIVE_ROOT_FRONTDOOR)
	root_is_facade = _root_frontdoor_is_facade(root_text)
	service_text = _read_text(root, PROJECT_RELATIVE_SERVICE)
	service_evidence = _service_import_evidence(service_text)
	test_evidence = _test_import_evidence(root)

	package_migrated = (
		_frontdoor_file_summary(
			root_path=root,
			relative_path=PROJECT_RELATIVE_PACKAGE_FRONTDOOR,
			path_id="frontdoor_lane_package_governed_report_or_projection",
			active_classification="active_runtime_primary",
			migration_recommendation="migrate_this_path_first_in_ec_4c",
			reason=(
				"service.py imports evaluate_frontdoor_lane and handle_frontdoor_turn from "
				"ai_assistant_ui.qwen_chat.lanes.frontdoor_lane and calls both runtime functions."
			),
			service_imported=bool(service_evidence["package_imported_by_service"]),
		).get("authorized_emission_helper_count", 0)
		> 0
	)
	package_emitter = _frontdoor_file_summary(
		root_path=root,
		relative_path=PROJECT_RELATIVE_PACKAGE_FRONTDOOR,
		path_id="frontdoor_lane_package_governed_report_or_projection",
		active_classification=(
			"active_runtime_primary_migrated_to_authorized_helper"
			if package_migrated
			else "active_runtime_primary"
		),
		migration_recommendation=(
			"ec_4c_migration_complete_keep_root_for_ec_9_duplicate_cleanup"
			if package_migrated
			else "migrate_this_path_first_in_ec_4c"
		),
		reason=(
			"service.py imports this package lane and the active EC-4C runtime path now uses "
			"emit_authorized_assistant_answer."
			if package_migrated
			else (
				"service.py imports evaluate_frontdoor_lane and handle_frontdoor_turn from "
				"ai_assistant_ui.qwen_chat.lanes.frontdoor_lane and calls both runtime functions."
			)
		),
		service_imported=bool(service_evidence["package_imported_by_service"]),
	)
	root_emitter = _frontdoor_file_summary(
		root_path=root,
		relative_path=PROJECT_RELATIVE_ROOT_FRONTDOOR,
		path_id="frontdoor_lane_root_duplicate",
		active_classification=(
			"compatibility_facade_not_service_runtime"
			if root_is_facade
			else "duplicate_drift_not_service_runtime"
		),
		migration_recommendation=(
			"ec_4u_duplicate_closure_complete_keep_facade"
			if root_is_facade
			else "do_not_migrate_in_ec_4c_convert_to_facade_in_ec_9"
		),
		reason=(
			"service.py does not import the root module; EC-4U converted it to a compatibility facade "
			"so older imports cannot execute duplicate answer-emission behavior."
			if root_is_facade
			else (
				"service.py does not import the root module; it remains duplicate drift and should be handled "
				"by duplicate-lane cleanup instead of frontdoor hard-gate migration."
			)
		),
		service_imported=bool(service_evidence["root_imported_by_service"]),
	)
	emitters = [package_emitter, root_emitter]
	append_site_count = sum(int(item.get("direct_assistant_append_count") or 0) for item in emitters)
	return {
		"type": FRONTDOOR_EMISSION_MAPPING_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"reviewer": _clean_text(reviewer),
		"created_at": _utc_now(),
		"branch": _git_branch(root),
		"head": _git_short_head(root),
		"current_dirty_status_count": _git_status_count(root),
		"scope": (
			"EC-4U duplicate/wrapper closure refresh after root frontdoor facade conversion"
			if root_is_facade
			else (
				"EC-4C frontdoor emission mapping refresh after active package migration"
				if package_migrated
				else "EC-4B frontdoor emission mapping only"
			)
		),
		"runtime_behavior_changed": bool(package_migrated),
		"hard_runtime_blocking_enabled": False,
		"frontdoor_emitter_count": len(emitters),
		"frontdoor_direct_assistant_append_count": append_site_count,
		"active_runtime_emitter_count": sum(
			1 for item in emitters if str(item.get("active_classification") or "").startswith("active_runtime_primary")
		),
		"active_runtime_migrated_to_authorized_helper_count": sum(
			1
			for item in emitters
			if item.get("active_classification") == "active_runtime_primary_migrated_to_authorized_helper"
		),
		"duplicate_drift_emitter_count": sum(
			1 for item in emitters if item.get("active_classification") == "duplicate_drift_not_service_runtime"
		),
		"compatibility_facade_emitter_count": sum(
			1 for item in emitters if item.get("active_classification") == "compatibility_facade_not_service_runtime"
		),
		"service_import_evidence": service_evidence,
		"test_import_evidence": test_evidence,
		"frontdoor_emitters": emitters,
		"diff_summary": _frontdoor_diff_summary(package_text=package_text, root_text=root_text),
		"proposed_ec4c_write_scope": {
			"allowed_files": [
				PROJECT_RELATIVE_PACKAGE_FRONTDOOR,
				*( [PROJECT_RELATIVE_ROOT_FRONTDOOR] if root_is_facade else [] ),
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_emission_mapping.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_frontdoor_authorized_emission_contracts.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_frontdoor_emission_mapping_contracts.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/final_answer_emission_dry_run.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_final_answer_emission_dry_run_contracts.py",
			],
			"forbidden_files": [
				PROJECT_RELATIVE_SERVICE,
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/reasoning_lane.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/legacy_runtime_lane.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/entity_drilldown_lane.py",
			],
			"write_scope_decision": (
				"ec_4u_root_duplicate_converted_to_facade_service_unchanged"
				if root_is_facade
				else (
					"ec_4c_active_package_frontdoor_migrated_root_and_service_forbidden"
					if package_migrated
					else "migrate_active_package_frontdoor_only_after_counterpart_approval"
				)
			),
		},
		"non_goals": [
			(
				"no_additional_runtime_migration_beyond_active_package_frontdoor_in_ec4c"
				if package_migrated
				else "no_runtime_migration_in_ec4b"
			),
			"no_service_py_changes",
			"no_active_package_frontdoor_behavior_change",
			"no_model_role_strict_enforcement",
			"no_release_packaging_cleanup",
			"no_reasoning_nbu_entity_or_legacy_lane_migration",
		],
		"final_recommendation": (
			"enterprise_cleanup_ec_4u_frontdoor_duplicate_facade_closed"
			if root_is_facade
			else (
				"enterprise_cleanup_ec_4c_frontdoor_mapping_refreshed_after_migration"
				if package_migrated
				else "enterprise_cleanup_ec_4b_ready_for_counterpart_review"
			)
		),
	}


def render_frontdoor_emission_mapping_markdown(report: Dict[str, Any]) -> str:
	lines = [
		"# EC-4B Frontdoor Emission Mapping",
		"",
		f"- Branch: `{_clean_text(report.get('branch'))}`",
		f"- Head: `{_clean_text(report.get('head'))}`",
		f"- Dirty status count: `{report.get('current_dirty_status_count')}`",
		f"- Runtime behavior changed: `{bool(report.get('runtime_behavior_changed'))}`",
		f"- Hard runtime blocking enabled: `{bool(report.get('hard_runtime_blocking_enabled'))}`",
		f"- Final recommendation: `{_clean_text(report.get('final_recommendation'))}`",
		"",
		"## Frontdoor Emitters",
		"",
		"| Path | Classification | Append lines | Service imported | Recommendation |",
		"|---|---|---:|---:|---|",
	]
	for item in list(report.get("frontdoor_emitters") or []):
		lines.append(
			"| {path} | {classification} | {lines} | {service_imported} | {recommendation} |".format(
				path=_clean_text(item.get("path_id")),
				classification=_clean_text(item.get("active_classification")),
				lines=", ".join(str(value) for value in list(item.get("direct_assistant_append_lines") or [])),
				service_imported=bool(item.get("service_imported")),
				recommendation=_clean_text(item.get("migration_recommendation")),
			)
		)
	service = dict(report.get("service_import_evidence") or {})
	lines.extend(
		[
			"",
			"## Service Evidence",
			"",
			f"- Package lane imported by service: `{bool(service.get('package_imported_by_service'))}`",
			f"- Root lane imported by service: `{bool(service.get('root_imported_by_service'))}`",
			f"- Service evaluate call sites: `{list((service.get('service_call_sites') or {}).get('evaluate_frontdoor_lane') or [])}`",
			f"- Service handle call sites: `{list((service.get('service_call_sites') or {}).get('handle_frontdoor_turn') or [])}`",
			"",
			"## Duplicate Drift",
			"",
		]
	)
	diff_summary = dict(report.get("diff_summary") or {})
	lines.extend(
		[
			f"- Files identical: `{bool(diff_summary.get('files_identical'))}`",
			f"- Package line count: `{diff_summary.get('package_line_count')}`",
			f"- Root line count: `{diff_summary.get('root_line_count')}`",
			f"- Package has fresh-breakout helper: `{bool(diff_summary.get('package_has_fresh_breakout_helper'))}`",
			f"- Root has fresh-breakout helper: `{bool(diff_summary.get('root_has_fresh_breakout_helper'))}`",
			f"- Drift reason: {_clean_text(diff_summary.get('root_duplicate_drift_reason'))}",
			"",
			"## Proposed EC-4C Write Scope",
			"",
		]
	)
	write_scope = dict(report.get("proposed_ec4c_write_scope") or {})
	lines.append("Allowed files:")
	for path in list(write_scope.get("allowed_files") or []):
		lines.append(f"- `{path}`")
	lines.append("")
	lines.append("Forbidden files:")
	for path in list(write_scope.get("forbidden_files") or []):
		lines.append(f"- `{path}`")
	lines.extend(["", "## Non-Goals", ""])
	for non_goal in list(report.get("non_goals") or []):
		lines.append(f"- `{non_goal}`")
	lines.append("")
	return "\n".join(lines)


def write_frontdoor_emission_mapping_files(
	*,
	root_path: str | Path = ".",
	out_dir: str | Path,
	reviewer: str = "codex_ec4b_frontdoor_mapping",
) -> Dict[str, Any]:
	out_path = Path(out_dir)
	out_path.mkdir(parents=True, exist_ok=True)
	report = build_frontdoor_emission_mapping_report(root_path=root_path, reviewer=reviewer)
	json_path = out_path / "qwen_ec4b_frontdoor_emission_mapping_report.json"
	markdown_path = out_path / "qwen_ec4b_frontdoor_emission_mapping_report.md"
	json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
	markdown_path.write_text(render_frontdoor_emission_mapping_markdown(report), encoding="utf-8")
	return {
		"report": report,
		"json_path": str(json_path),
		"markdown_path": str(markdown_path),
	}


def main(argv: List[str] | None = None) -> int:
	parser = argparse.ArgumentParser(description="Generate the EC-4B frontdoor emission mapping report.")
	parser.add_argument("--root-path", default=".")
	parser.add_argument(
		"--out-dir",
		default=(
			"impl_factory/00_governance/current_docs/generated/"
			"ec_4b_frontdoor_emission_mapping"
		),
	)
	parser.add_argument("--reviewer", default="codex_ec4b_frontdoor_mapping")
	args = parser.parse_args(argv)
	result = write_frontdoor_emission_mapping_files(
		root_path=args.root_path,
		out_dir=args.out_dir,
		reviewer=args.reviewer,
	)
	print(json.dumps({"ok": True, **result}, indent=2, sort_keys=True))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
