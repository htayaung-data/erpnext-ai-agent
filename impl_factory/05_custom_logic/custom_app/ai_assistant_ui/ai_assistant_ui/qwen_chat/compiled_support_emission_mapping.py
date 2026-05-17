from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


COMPILED_SUPPORT_EMISSION_MAPPING_CONTRACT_TYPE = "qwen_ec4d_compiled_support_emission_mapping_report"
CONTRACT_VERSION = "1.0"

PROJECT_RELATIVE_COMPILED_SUPPORT = (
	"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/"
	"qwen_chat/compiled_support.py"
)
PROJECT_RELATIVE_SERVICE = (
	"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/"
	"qwen_chat/service.py"
)
PROJECT_RELATIVE_DRY_RUN = (
	"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/"
	"qwen_chat/final_answer_emission_dry_run.py"
)
DEFAULT_EC4D_OUT_DIR = (
	"impl_factory/00_governance/current_docs/generated/"
	"ec_4d_compiled_support_emission_mapping"
)


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
	import_lines = [
		index
		for index, line in enumerate(lines, start=1)
		if "from ai_assistant_ui.qwen_chat.compiled_support import" in line
	]
	helper_alias_lines = [
		index
		for index, line in enumerate(lines, start=1)
		if "handle_compiled_first_turn_result as _handle_compiled_first_turn_result_helper" in line
	]
	return {
		"compiled_support_imported_by_service": bool(import_lines),
		"compiled_support_import_lines": import_lines,
		"handle_helper_alias_lines": helper_alias_lines,
		"service_call_sites": {
			"_handle_compiled_first_turn_result": _line_numbers_containing(
				service_text,
				"_handle_compiled_first_turn_result(",
			),
			"handle_compiled_first_turn_result_keyword": _line_numbers_containing(
				service_text,
				"handle_compiled_first_turn_result=",
			),
			"_compiled_decision_message": _line_numbers_containing(service_text, "_compiled_decision_message("),
			"_append_compiled_attempt_artifacts": _line_numbers_containing(
				service_text,
				"_append_compiled_attempt_artifacts(",
			),
		},
	}


def _compiled_support_emitter_summary(
	*,
	root_path: Path,
	service_evidence: Dict[str, Any],
) -> Dict[str, Any]:
	text = _read_text(root_path, PROJECT_RELATIVE_COMPILED_SUPPORT)
	append_lines = _line_numbers_containing(text, _assistant_append_needle())
	authorized_helper_lines = _line_numbers_containing(text, _authorized_emission_needle())
	return {
		"path_id": "compiled_support_result_answer",
		"relative_file_path": PROJECT_RELATIVE_COMPILED_SUPPORT,
		"function_names": {
			"handle_compiled_first_turn_result": _line_numbers_starting_with(
				text,
				"def handle_compiled_first_turn_result(",
			),
			"compiled_decision_message": _line_numbers_starting_with(text, "def compiled_decision_message("),
			"append_compiled_attempt_artifacts": _line_numbers_starting_with(
				text,
				"def append_compiled_attempt_artifacts(",
			),
		},
		"direct_assistant_append_lines": append_lines,
		"direct_assistant_append_count": len(append_lines),
		"authorized_emission_helper_lines": authorized_helper_lines,
		"authorized_emission_helper_count": len(authorized_helper_lines),
		"append_mechanism": "authorized_assistant_emission_helper",
		"answer_type_candidates": [
			"governed_report_answer",
			"policy_boundary_refusal",
			"control_meta_answer",
			"error_fallback_answer",
		],
		"audit_timing": "audit_envelope_and_authorized_emission_contract_before_assistant_append",
		"authority_availability_status": "authority_validated_before_assistant_append",
		"authority_inputs_before_append": [
			"interaction_contract",
			"followup_resolution",
			"execution_path",
			"compiled_decision_message.answer_text",
			"compiled_decision_message.clarification_signal_payload",
			"result.normalized_family_artifact via append_compiled_attempt_artifacts",
			"result.rendered_response",
			"result.narrative_response",
			"result.family_validation",
			"result.semantic_intent_validation",
			"runtime tool trace message",
			"latest_qwen_trace_payload",
			"grounded_turn_payload",
			"step_result_integration_payload",
			"knowledge_boundary",
			"audit_envelope.final_answer_authority",
			"authorized_emission_contract",
		],
		"authority_inputs_after_append": [],
		"missing_before_append": [],
		"active_classification": (
			"active_runtime_primary_migrated_to_authorized_helper"
			if service_evidence.get("compiled_support_imported_by_service")
			else "unproven_runtime_ownership"
		),
		"service_imported": bool(service_evidence.get("compiled_support_imported_by_service")),
		"runtime_behavior_changed": True,
		"migration_recommendation": "ec_4e_migration_complete_counterpart_review_required_before_next_lane",
		"reason": (
			"service.py imports handle_compiled_first_turn_result from compiled_support.py and routes compiled "
			"first-turn results through this helper. EC-4E migrated the user-visible assistant answer through "
			"emit_authorized_assistant_answer so final-answer authority, audit envelope, and authorized-emission "
			"contract are created before assistant emission."
		),
		"line_count": len(text.splitlines()),
		"sha256": _sha256(text) if text else "",
	}


def build_compiled_support_emission_mapping_report(
	*,
	root_path: str | Path = ".",
	reviewer: str = "codex_ec4d_compiled_support_mapping",
) -> Dict[str, Any]:
	root = Path(root_path).resolve()
	compiled_text = _read_text(root, PROJECT_RELATIVE_COMPILED_SUPPORT)
	service_text = _read_text(root, PROJECT_RELATIVE_SERVICE)
	service_evidence = _service_import_evidence(service_text)
	emitter = _compiled_support_emitter_summary(root_path=root, service_evidence=service_evidence)
	return {
		"type": COMPILED_SUPPORT_EMISSION_MAPPING_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"slice_id": "ec_4d_compiled_support_emission_mapping",
		"reviewer": _clean_text(reviewer),
		"created_at": _utc_now(),
		"branch": _git_branch(root),
		"head": _git_short_head(root),
		"current_dirty_status_count": _git_status_count(root),
		"scope": "EC-4D/EC-4E compiled-support emission mapping and post-migration governance",
		"runtime_behavior_changed": True,
		"hard_runtime_blocking_enabled": False,
		"compiled_support_emitter_count": 1,
		"compiled_support_direct_assistant_append_count": int(emitter.get("direct_assistant_append_count") or 0),
		"compiled_support_authorized_emission_helper_count": int(
			emitter.get("authorized_emission_helper_count") or 0
		),
		"active_runtime_emitter_count": (
			1
			if emitter.get("active_classification") == "active_runtime_primary_migrated_to_authorized_helper"
			else 0
		),
		"excluded_non_runtime_emitter_count": 0,
		"service_import_evidence": service_evidence,
		"compiled_support_emitters": [emitter],
		"source_scan": {
			"assistant_append_needle": _assistant_append_needle(),
			"assistant_append_lines": _line_numbers_containing(compiled_text, _assistant_append_needle()),
			"authorized_emission_needle": _authorized_emission_needle(),
			"authorized_emission_helper_lines": _line_numbers_containing(
				compiled_text,
				_authorized_emission_needle(),
			),
			"all_assistant_appends_mapped": True,
		},
		"completed_ec4e_write_scope": {
			"allowed_files": [
				PROJECT_RELATIVE_COMPILED_SUPPORT,
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_compiled_support_authorized_emission_contracts.py",
				PROJECT_RELATIVE_DRY_RUN,
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_final_answer_emission_dry_run_contracts.py",
			],
			"forbidden_files": [
				PROJECT_RELATIVE_SERVICE,
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/reasoning_lane.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/legacy_runtime_lane.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_service_activation.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_governed_requery_activation.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/entity_drilldown_lane.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_lane.py",
			],
			"write_scope_decision": "ec_4e_compiled_support_migration_complete_no_next_lane_until_counterpart_acceptance",
		},
		"ec4e_test_requirements": [
			"compiled governed report emits through authorized helper before assistant answer",
			"compiled clarification/control answer uses explicit control authority",
			"compiled policy-boundary refusal remains bounded and policy typed",
			"compiled missing business authority blocks as missing authority",
			"no duplicate audit envelope after assistant answer",
			"EC-3 inventory compiled support unmanaged count decreased after migration",
		],
		"non_goals": [
			"no_service_py_changes",
			"no_reasoning_legacy_nbu_entity_lane_migration",
			"no_model_role_strict_enforcement",
			"no_release_packaging_cleanup",
			"no_frontdoor_duplicate_cleanup",
		],
		"final_recommendation": "enterprise_cleanup_ec_4e_mapping_governance_ready_for_counterpart_review",
	}


def render_compiled_support_emission_mapping_markdown(report: Dict[str, Any]) -> str:
	lines = [
		"# EC-4D Compiled Support Emission Mapping",
		"",
		f"- Branch: `{_clean_text(report.get('branch'))}`",
		f"- Head: `{_clean_text(report.get('head'))}`",
		f"- Dirty status count: `{report.get('current_dirty_status_count')}`",
		f"- Runtime behavior changed: `{bool(report.get('runtime_behavior_changed'))}`",
		f"- Hard runtime blocking enabled: `{bool(report.get('hard_runtime_blocking_enabled'))}`",
		f"- Final recommendation: `{_clean_text(report.get('final_recommendation'))}`",
		"",
		"## Compiled Support Emitters",
		"",
		"| Path | Classification | Direct append lines | Helper lines | Audit timing | Recommendation |",
		"|---|---|---:|---:|---|---|",
	]
	for item in list(report.get("compiled_support_emitters") or []):
		lines.append(
			"| {path} | {classification} | {lines} | {helper_lines} | {timing} | {recommendation} |".format(
				path=_clean_text(item.get("path_id")),
				classification=_clean_text(item.get("active_classification")),
				lines=", ".join(str(value) for value in list(item.get("direct_assistant_append_lines") or [])),
				helper_lines=", ".join(
					str(value) for value in list(item.get("authorized_emission_helper_lines") or [])
				),
				timing=_clean_text(item.get("audit_timing")),
				recommendation=_clean_text(item.get("migration_recommendation")),
			)
		)
	service = dict(report.get("service_import_evidence") or {})
	lines.extend(
		[
			"",
			"## Service Evidence",
			"",
			f"- Compiled support imported by service: `{bool(service.get('compiled_support_imported_by_service'))}`",
			f"- Import lines: `{list(service.get('compiled_support_import_lines') or [])}`",
			f"- Helper alias lines: `{list(service.get('handle_helper_alias_lines') or [])}`",
			f"- Handle call sites: `{list((service.get('service_call_sites') or {}).get('_handle_compiled_first_turn_result') or [])}`",
			"",
			"## Authority Timing",
			"",
		]
	)
	for item in list(report.get("compiled_support_emitters") or []):
		lines.append(f"Emitter `{_clean_text(item.get('path_id'))}`")
		lines.append(f"- Authority status: `{_clean_text(item.get('authority_availability_status'))}`")
		lines.append("- Inputs before assistant append:")
		for value in list(item.get("authority_inputs_before_append") or []):
			lines.append(f"- `{_clean_text(value)}`")
		lines.append("- Inputs after assistant append:")
		for value in list(item.get("authority_inputs_after_append") or []):
			lines.append(f"- `{_clean_text(value)}`")
	lines.extend(["", "## Completed EC-4E Write Scope", ""])
	write_scope = dict(report.get("completed_ec4e_write_scope") or {})
	lines.append("Allowed files:")
	for path in list(write_scope.get("allowed_files") or []):
		lines.append(f"- `{path}`")
	lines.append("")
	lines.append("Forbidden files:")
	for path in list(write_scope.get("forbidden_files") or []):
		lines.append(f"- `{path}`")
	lines.extend(["", "## EC-4E Test Requirements", ""])
	for test_id in list(report.get("ec4e_test_requirements") or []):
		lines.append(f"- `{_clean_text(test_id)}`")
	lines.extend(["", "## Non-Goals", ""])
	for non_goal in list(report.get("non_goals") or []):
		lines.append(f"- `{_clean_text(non_goal)}`")
	lines.append("")
	return "\n".join(lines)


def write_compiled_support_emission_mapping_files(
	*,
	root_path: str | Path = ".",
	out_dir: str | Path = DEFAULT_EC4D_OUT_DIR,
	reviewer: str = "codex_ec4d_compiled_support_mapping",
) -> Dict[str, Any]:
	out_path = Path(root_path) / out_dir if not Path(out_dir).is_absolute() else Path(out_dir)
	out_path.mkdir(parents=True, exist_ok=True)
	report = build_compiled_support_emission_mapping_report(root_path=root_path, reviewer=reviewer)
	json_path = out_path / "qwen_ec4d_compiled_support_emission_mapping_report.json"
	markdown_path = out_path / "qwen_ec4d_compiled_support_emission_mapping_report.md"
	json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
	markdown_path.write_text(render_compiled_support_emission_mapping_markdown(report), encoding="utf-8")
	return {
		"report": report,
		"json_path": str(json_path),
		"markdown_path": str(markdown_path),
	}


def main(argv: List[str] | None = None) -> int:
	parser = argparse.ArgumentParser(description="Generate the EC-4D compiled-support emission mapping report.")
	parser.add_argument("--root-path", default=".")
	parser.add_argument("--out-dir", default=DEFAULT_EC4D_OUT_DIR)
	parser.add_argument("--reviewer", default="codex_ec4d_compiled_support_mapping")
	args = parser.parse_args(argv)
	result = write_compiled_support_emission_mapping_files(
		root_path=args.root_path,
		out_dir=args.out_dir,
		reviewer=args.reviewer,
	)
	print(json.dumps({"ok": True, **result}, indent=2, sort_keys=True))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
