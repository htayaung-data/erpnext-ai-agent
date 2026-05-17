from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ENTITY_FOLLOWUP_EMISSION_MAPPING_CONTRACT_TYPE = "qwen_ec4l_entity_followup_emission_mapping_report"
CONTRACT_VERSION = "1.0"

PROJECT_RELATIVE_ENTITY_FOLLOWUP = (
	"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/"
	"qwen_chat/entity_followup_support.py"
)
PROJECT_RELATIVE_SERVICE = (
	"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/"
	"qwen_chat/service.py"
)
PROJECT_RELATIVE_DRY_RUN = (
	"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/"
	"qwen_chat/final_answer_emission_dry_run.py"
)
DEFAULT_EC4L_OUT_DIR = (
	"impl_factory/00_governance/current_docs/generated/"
	"ec_4l_entity_followup_emission_mapping"
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


def _assistant_append_line_numbers(text: str) -> List[int]:
	lines = text.splitlines()
	results: List[int] = []
	inline_needle = _assistant_append_needle()
	for index, line in enumerate(lines, start=1):
		if inline_needle in line:
			results.append(index)
			continue
		if ("append_" + "message(") not in line:
			continue
		window = "\n".join(lines[index - 1 : index + 6])
		if '"assistant"' in window:
			results.append(index)
	return list(dict.fromkeys(results))


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
	return {
		"entity_followup_imported_by_service": bool(
			_line_numbers_containing(
				service_text,
				"from ai_assistant_ui.qwen_chat.entity_followup_support import",
			)
		),
		"entity_followup_import_lines": _line_numbers_containing(
			service_text,
			"from ai_assistant_ui.qwen_chat.entity_followup_support import",
		),
		"entity_followup_alias_lines": _line_numbers_containing(
			service_text,
			"try_entity_detail_followup as _try_entity_detail_followup_helper",
		),
		"service_call_sites": {
			"_try_entity_detail_followup": _line_numbers_containing(
				service_text,
				"_try_entity_detail_followup(",
			),
			"_try_entity_detail_followup_helper": _line_numbers_containing(
				service_text,
				"_try_entity_detail_followup_helper(",
			),
		},
	}


def _entity_followup_emitters(
	*,
	root_path: Path,
	service_evidence: Dict[str, Any],
) -> List[Dict[str, Any]]:
	text = _read_text(root_path, PROJECT_RELATIVE_ENTITY_FOLLOWUP)
	append_lines = _assistant_append_line_numbers(text)
	helper_lines = _line_numbers_containing(text, _authorized_emission_needle())
	success_start_candidates = _line_numbers_containing(text, 'if not bool(outcome.get("ok")):')
	if not success_start_candidates:
		success_start_candidates = _line_numbers_containing(text, "answer_text =")
	success_start_line = success_start_candidates[0] if success_start_candidates else 65
	error_append_lines = [line for line in append_lines if line < success_start_line]
	success_append_lines = [line for line in append_lines if line >= success_start_line]
	error_helper_lines = [line for line in helper_lines if line < success_start_line]
	success_helper_lines = [line for line in helper_lines if line >= success_start_line]
	artifact_lines = _line_numbers_containing(text, "artifact_payload")
	rendered_lines = _line_numbers_containing(text, "rendered_response_payload")
	narrative_lines = _line_numbers_containing(text, "narrative_contract_payload")
	grounded_lines = _line_numbers_containing(text, "grounded_turn_payload")
	trace_lines = _line_numbers_containing(text, "tool_trace_message(")
	save_lines = _line_numbers_containing(text, "save_session(session_doc")
	service_imported = bool(service_evidence.get("entity_followup_imported_by_service"))
	error_migrated = bool(error_helper_lines) and not error_append_lines
	success_migrated = bool(success_helper_lines) and not success_append_lines
	return [
		{
			"path_id": "entity_followup_failure",
			"relative_file_path": PROJECT_RELATIVE_ENTITY_FOLLOWUP,
			"function_name": "try_entity_detail_followup",
			"function_lines": _line_numbers_starting_with(text, "def try_entity_detail_followup("),
			"answer_type": "error_fallback_answer",
			"answer_type_candidates": ["error_fallback_answer"],
			"direct_assistant_append_lines": error_append_lines,
			"direct_assistant_append_count": len(error_append_lines),
			"authorized_emission_helper_lines": error_helper_lines,
			"authorized_emission_helper_count": len(error_helper_lines),
			"append_mechanism": "authorized_assistant_emission_helper" if error_migrated else "direct_append_message",
			"audit_timing": (
				"authorized_emission_contract_before_error_assistant_append"
				if error_migrated
				else "no_audit_envelope_observed_in_path"
			),
			"authority_availability_status": (
				"explicit_error_authority_validated_before_append"
				if error_migrated
				else "missing_explicit_error_authority"
			),
			"authority_inputs_before_append": [
				"interaction_contract",
				"entity_reference",
				"safe_error_text",
				"tool_trace_message",
			],
			"authority_inputs_after_append": [],
			"missing_before_append": [] if error_migrated else [
				"explicit_error_fallback_authority",
				"authorized_emission_contract",
			],
			"api_payload_answer_text_surface": False,
			"active_classification": (
				"active_runtime_error_fallback_migrated_to_authorized_helper"
				if error_migrated
				else "active_runtime_error_fallback_unmigrated"
			),
			"service_imported": service_imported,
			"risk_level": "medium",
			"risk_reason": "Entity follow-up error fallback appends assistant text before explicit error authority.",
			"migration_recommendation": (
				"EC-4M should emit this fallback through authorized error/control authority."
				if not error_migrated
				else "EC-4M migration complete for entity follow-up error fallback."
			),
		},
		{
			"path_id": "entity_followup_success",
			"relative_file_path": PROJECT_RELATIVE_ENTITY_FOLLOWUP,
			"function_name": "try_entity_detail_followup",
			"function_lines": _line_numbers_starting_with(text, "def try_entity_detail_followup("),
			"answer_type": "business_facing_factual_answer_or_governed_report_answer",
			"answer_type_candidates": [
				"business_facing_factual_answer",
				"governed_report_answer",
			],
			"direct_assistant_append_lines": success_append_lines,
			"direct_assistant_append_count": len(success_append_lines),
			"authorized_emission_helper_lines": success_helper_lines,
			"authorized_emission_helper_count": len(success_helper_lines),
			"artifact_payload_lines": artifact_lines,
			"rendered_response_payload_lines": rendered_lines,
			"narrative_contract_payload_lines": narrative_lines,
			"grounded_turn_payload_lines": grounded_lines,
			"tool_trace_message_lines": trace_lines,
			"save_session_lines": save_lines,
			"append_mechanism": "authorized_assistant_emission_helper" if success_migrated else "direct_append_message",
			"audit_timing": (
				"audit_envelope_and_authorized_emission_contract_before_assistant_append"
				if success_migrated
				else "artifact_tool_trace_and_no_audit_after_assistant_append"
			),
			"authority_availability_status": (
				"authority_validated_before_assistant_append"
				if success_migrated
				else "missing_final_answer_authority"
			),
			"authority_inputs_before_append": [
				"interaction_contract",
				"response_policy_contract",
				"latest_grounded_turn",
				"entity_reference",
				"execute_entity_drilldown.outcome",
				"outcome.answer_text",
				"outcome.artifact_payload",
				"outcome.grounded_turn_payload",
			],
			"authority_inputs_after_append": [] if success_migrated else [
				"artifact_payload",
				"rendered_response_payload",
				"narrative_contract_payload",
				"grounded_turn_payload",
				"tool_trace_message",
			],
			"missing_before_append": [] if success_migrated else [
				"final_answer_authority",
				"authorized_emission_contract",
				"execution_path_contract",
				"followup_resolution_contract",
			],
			"api_payload_answer_text_surface": False,
			"active_classification": (
				"active_runtime_primary_migrated_to_authorized_helper"
				if success_migrated
				else "active_runtime_primary_unmigrated"
			),
			"service_imported": service_imported,
			"risk_level": "high",
			"risk_reason": (
				"Entity follow-up emits governed entity-detail text before artifact/tool payloads and without a "
				"final-answer authority envelope."
			),
			"migration_recommendation": (
				"EC-4M should build entity-detail authority before append, emit through the authorized helper, "
				"and block missing authority with no assistant/API answer leakage."
				if not success_migrated
				else "EC-4M migration complete for entity follow-up success."
			),
		},
	]


def build_entity_followup_emission_mapping_report(
	*,
	root_path: str | Path = ".",
	reviewer: str = "codex_ec4l_entity_followup_mapping",
) -> Dict[str, Any]:
	root = Path(root_path).resolve()
	text = _read_text(root, PROJECT_RELATIVE_ENTITY_FOLLOWUP)
	service_text = _read_text(root, PROJECT_RELATIVE_SERVICE)
	service_evidence = _service_import_evidence(service_text)
	emitters = _entity_followup_emitters(root_path=root, service_evidence=service_evidence)
	direct_count = sum(int(item.get("direct_assistant_append_count") or 0) for item in emitters)
	helper_count = sum(int(item.get("authorized_emission_helper_count") or 0) for item in emitters)
	return {
		"type": ENTITY_FOLLOWUP_EMISSION_MAPPING_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"slice_id": "ec_4l_entity_followup_emission_mapping",
		"scope": "EC-4L/EC-4M entity-followup emission mapping and post-migration governance",
		"created_at": _utc_now(),
		"reviewer": _clean_text(reviewer),
		"branch": _git_branch(root),
		"head": _git_short_head(root),
		"current_dirty_status_count": _git_status_count(root),
		"runtime_behavior_changed": bool(helper_count > 0 and direct_count == 0),
		"authorized_emission_runtime_migration_done": bool(helper_count > 0 and direct_count == 0),
		"hard_runtime_blocking_enabled": False,
		"entity_followup_emitter_count": len(emitters),
		"entity_followup_direct_assistant_append_count": direct_count,
		"entity_followup_authorized_emission_helper_count": helper_count,
		"active_runtime_emitter_count": len([item for item in emitters if item.get("service_imported")]),
		"excluded_non_runtime_emitter_count": 0,
		"service_import_evidence": service_evidence,
		"entity_followup_emitters": emitters,
		"source_scan": {
			"assistant_append_needle": _assistant_append_needle(),
			"assistant_append_lines": _assistant_append_line_numbers(text),
			"authorized_emission_needle": _authorized_emission_needle(),
			"authorized_emission_helper_lines": _line_numbers_containing(text, _authorized_emission_needle()),
			"all_assistant_appends_mapped": sorted(_assistant_append_line_numbers(text))
			== sorted(
				line
				for item in emitters
				for line in item.get("direct_assistant_append_lines", [])
			),
		},
		"completed_ec4m_write_scope": {
			"allowed_files": [
				PROJECT_RELATIVE_ENTITY_FOLLOWUP,
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_followup_emission_mapping.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_entity_followup_authorized_emission_contracts.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_entity_followup_emission_mapping_contracts.py",
				PROJECT_RELATIVE_DRY_RUN,
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_final_answer_emission_dry_run_contracts.py",
			],
			"forbidden_files": [
				PROJECT_RELATIVE_SERVICE,
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_lane.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_governed_requery_activation.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/entity_drilldown_lane.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/reasoning_lane.py",
			],
			"write_scope_decision": "ec_4m_entity_followup_migration_complete_no_next_lane_until_counterpart_acceptance",
		},
		"ec4m_test_requirements": [
			"entity follow-up success emits through authorized helper before assistant answer",
			"entity follow-up error emits through explicit error fallback authority",
			"missing entity follow-up authority blocks with no assistant message and no returned answer_text",
			"artifact, grounded turn, trace, audit, and authorized emission ordering is pre-answer",
			"no duplicate audit envelope after assistant answer",
			"EC-3 inventory removes entity_followup_success and entity_followup_failure after migration",
		],
		"non_goals": [
			"ec4l_was_mapping_only_ec4m_performed_bounded_entity_followup_migration",
			"no_service_py_changes",
			"no_root_frontdoor_duplicate_cleanup",
			"no_model_role_strict_enforcement",
			"no_release_packaging_cleanup",
		],
		"final_recommendation": (
			"enterprise_cleanup_ec_4m_ready_for_counterpart_review"
			if helper_count > 0 and direct_count == 0
			else "enterprise_cleanup_ec_4l_ready_for_counterpart_review"
		),
		"file_sha256": _sha256(text) if text else "",
		"line_count": len(text.splitlines()),
	}


def render_entity_followup_emission_mapping_markdown(report: Dict[str, Any]) -> str:
	lines = [
		"# EC-4L/EC-4M Entity Follow-Up Emission Mapping",
		"",
		f"- Branch: `{_clean_text(report.get('branch'))}`",
		f"- Head: `{_clean_text(report.get('head'))}`",
		f"- Dirty status count: `{report.get('current_dirty_status_count')}`",
		f"- Runtime behavior changed: `{bool(report.get('runtime_behavior_changed'))}`",
		f"- Authorized emission runtime migration done: `{bool(report.get('authorized_emission_runtime_migration_done'))}`",
		f"- Hard runtime blocking enabled: `{bool(report.get('hard_runtime_blocking_enabled'))}`",
		f"- Final recommendation: `{_clean_text(report.get('final_recommendation'))}`",
		"",
		"## Entity Follow-Up Emitters",
		"",
	]
	for item in list(report.get("entity_followup_emitters") or []):
		lines.extend(
			[
				f"### `{_clean_text(item.get('path_id'))}`",
				"",
				f"- File: `{_clean_text(item.get('relative_file_path'))}`",
				f"- Function: `{_clean_text(item.get('function_name'))}`",
				f"- Direct assistant append lines: `{item.get('direct_assistant_append_lines')}`",
				f"- Authorized helper lines: `{item.get('authorized_emission_helper_lines')}`",
				f"- Append mechanism: `{_clean_text(item.get('append_mechanism'))}`",
				f"- Audit timing: `{_clean_text(item.get('audit_timing'))}`",
				f"- Authority status: `{_clean_text(item.get('authority_availability_status'))}`",
				f"- Risk: `{_clean_text(item.get('risk_level'))}`",
				f"- API payload answer surface: `{bool(item.get('api_payload_answer_text_surface'))}`",
				f"- Recommendation: `{_clean_text(item.get('migration_recommendation'))}`",
				"",
			]
		)
	lines.extend(["## Service Evidence", ""])
	service = dict(report.get("service_import_evidence") or {})
	lines.append(f"- Imported by service: `{bool(service.get('entity_followup_imported_by_service'))}`")
	lines.append(f"- Import lines: `{service.get('entity_followup_import_lines')}`")
	lines.append(f"- Call sites: `{service.get('service_call_sites')}`")
	lines.extend(["", "## Completed EC-4M Write Scope", ""])
	write_scope = dict(report.get("completed_ec4m_write_scope") or {})
	lines.append("Allowed files:")
	for path in list(write_scope.get("allowed_files") or []):
		lines.append(f"- `{path}`")
	lines.append("")
	lines.append("Forbidden files:")
	for path in list(write_scope.get("forbidden_files") or []):
		lines.append(f"- `{path}`")
	lines.extend(["", "## EC-4M Test Requirements", ""])
	for test_id in list(report.get("ec4m_test_requirements") or []):
		lines.append(f"- `{_clean_text(test_id)}`")
	lines.extend(["", "## Non-Goals", ""])
	for non_goal in list(report.get("non_goals") or []):
		lines.append(f"- `{_clean_text(non_goal)}`")
	lines.append("")
	return "\n".join(lines)


def write_entity_followup_emission_mapping_files(
	*,
	root_path: str | Path = ".",
	out_dir: str | Path = DEFAULT_EC4L_OUT_DIR,
	reviewer: str = "codex_ec4l_entity_followup_mapping",
) -> Dict[str, Any]:
	out_path = Path(root_path) / out_dir if not Path(out_dir).is_absolute() else Path(out_dir)
	out_path.mkdir(parents=True, exist_ok=True)
	report = build_entity_followup_emission_mapping_report(root_path=root_path, reviewer=reviewer)
	json_path = out_path / "qwen_ec4l_entity_followup_emission_mapping_report.json"
	markdown_path = out_path / "qwen_ec4l_entity_followup_emission_mapping_report.md"
	json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
	markdown_path.write_text(render_entity_followup_emission_mapping_markdown(report), encoding="utf-8")
	return {
		"report": report,
		"json_path": str(json_path),
		"markdown_path": str(markdown_path),
	}


def main(argv: List[str] | None = None) -> int:
	parser = argparse.ArgumentParser(description="Generate the EC-4L entity follow-up emission mapping report.")
	parser.add_argument("--root-path", default=".")
	parser.add_argument("--out-dir", default=DEFAULT_EC4L_OUT_DIR)
	parser.add_argument("--reviewer", default="codex_ec4l_entity_followup_mapping")
	args = parser.parse_args(argv)
	result = write_entity_followup_emission_mapping_files(
		root_path=args.root_path,
		out_dir=args.out_dir,
		reviewer=args.reviewer,
	)
	print(json.dumps({**result, "ok": True}, indent=2, sort_keys=True))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
