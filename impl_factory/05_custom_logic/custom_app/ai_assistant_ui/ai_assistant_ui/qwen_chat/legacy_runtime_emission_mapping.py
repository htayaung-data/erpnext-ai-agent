from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


LEGACY_RUNTIME_EMISSION_MAPPING_CONTRACT_TYPE = "qwen_ec4h_legacy_runtime_emission_mapping_report"
CONTRACT_VERSION = "1.0"

PROJECT_RELATIVE_LEGACY_RUNTIME = (
	"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/"
	"qwen_chat/lanes/legacy_runtime_lane.py"
)
PROJECT_RELATIVE_SERVICE = (
	"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/"
	"qwen_chat/service.py"
)
PROJECT_RELATIVE_DRY_RUN = (
	"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/"
	"qwen_chat/final_answer_emission_dry_run.py"
)
DEFAULT_EC4H_OUT_DIR = (
	"impl_factory/00_governance/current_docs/generated/"
	"ec_4h_legacy_runtime_emission_mapping"
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


def _call_line_numbers(text: str, needle: str) -> List[int]:
	lines: List[int] = []
	for index, line in enumerate(text.splitlines(), start=1):
		if needle not in line:
			continue
		if line.strip().startswith("from "):
			continue
		lines.append(index)
	return lines


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
		"legacy_runtime_imported_by_service": bool(
			_line_numbers_containing(
				service_text,
				"from ai_assistant_ui.qwen_chat.lanes.legacy_runtime_lane import handle_legacy_runtime_turn",
			)
		),
		"legacy_runtime_import_lines": _line_numbers_containing(
			service_text,
			"from ai_assistant_ui.qwen_chat.lanes.legacy_runtime_lane import handle_legacy_runtime_turn",
		),
		"service_call_sites": {
			"handle_legacy_runtime_turn": _line_numbers_containing(
				service_text,
				"handle_legacy_runtime_turn(",
			),
			"legacy_runtime_mode_checks": _line_numbers_containing(service_text, "legacy_runtime"),
		},
	}


def _legacy_runtime_emitters(
	*,
	root_path: Path,
	service_evidence: Dict[str, Any],
) -> List[Dict[str, Any]]:
	text = _read_text(root_path, PROJECT_RELATIVE_LEGACY_RUNTIME)
	append_lines = _line_numbers_containing(text, _assistant_append_needle())
	authorized_helper_lines = _line_numbers_containing(text, _authorized_emission_needle())
	normal_runtime_start_lines = _line_numbers_containing(text, 'ok = bool(runtime_payload.get("ok"))')
	normal_runtime_start = normal_runtime_start_lines[0] if normal_runtime_start_lines else 130
	error_helper_lines = [line for line in authorized_helper_lines if line < normal_runtime_start]
	business_helper_lines = [line for line in authorized_helper_lines if line >= normal_runtime_start]
	audit_lines = _call_line_numbers(text, "build_audit_envelope(")
	grounded_context_lines = _call_line_numbers(text, "build_grounded_turn_context(")
	latest_assistant_payload_lines = _line_numbers_containing(text, "latest_assistant_payload(")
	latest_artifact_lines = _line_numbers_containing(text, "latest_normalized_family_artifact(")
	trace_payload_lines = _line_numbers_containing(text, "latest_qwen_trace_payload(")
	error_append_lines = [line for line in append_lines if line < normal_runtime_start]
	business_append_lines = [line for line in append_lines if line >= normal_runtime_start]
	error_audit_lines = [line for line in audit_lines if line < normal_runtime_start]
	business_audit_lines = [line for line in audit_lines if line >= normal_runtime_start]
	service_imported = bool(service_evidence.get("legacy_runtime_imported_by_service"))
	error_migrated = bool(error_helper_lines) and not error_append_lines
	business_migrated = bool(business_helper_lines) and not business_append_lines
	return [
		{
			"path_id": "legacy_runtime_client_error",
			"relative_file_path": PROJECT_RELATIVE_LEGACY_RUNTIME,
			"function_name": "handle_legacy_runtime_turn",
			"function_lines": _line_numbers_starting_with(text, "def handle_legacy_runtime_turn("),
			"answer_type": "error_fallback_answer",
			"answer_type_candidates": ["error_fallback_answer"],
			"direct_assistant_append_lines": error_append_lines,
			"direct_assistant_append_count": len(error_append_lines),
			"authorized_emission_helper_lines": error_helper_lines,
			"authorized_emission_helper_count": len(error_helper_lines),
			"build_audit_envelope_lines": error_audit_lines,
			"append_mechanism": "authorized_assistant_emission_helper" if error_migrated else "direct_append_message",
			"audit_timing": (
				"authorized_emission_contract_before_error_assistant_append"
				if error_migrated
				else "audit_envelope_after_error_append"
			),
			"authority_availability_status": (
				"explicit_error_authority_validated_before_append"
				if error_migrated
				else "audit_created_after_append"
			),
			"authority_inputs_before_append": [
				"interaction_contract",
				"followup_resolution",
				"execution_path",
				"safe_runtime_failure_message",
				"runtime_client_error",
				"tool_trace_payload",
			],
			"authority_inputs_after_append": [
				"build_audit_envelope",
				"audit_envelope.final_answer_authority",
			] if not error_migrated else [],
			"missing_before_append": [] if error_migrated else [
				"explicit_error_fallback_authority",
				"authorized_emission_contract",
			],
			"returned_payload_answer_text_surface": False,
			"active_classification": (
				"active_runtime_error_fallback_migrated_to_authorized_helper"
				if error_migrated
				else "active_runtime_error_fallback_unmigrated"
			),
			"service_imported": service_imported,
			"risk_level": "medium",
			"risk_reason": (
				"Runtime-client failures emit user-visible fallback text before explicit error/control authority "
				"and before the audit envelope."
			),
			"migration_recommendation": (
				"EC-4I migration complete: runtime errors now emit through the authorized helper as explicit "
				"error/control fallback."
				if error_migrated
				else (
					"EC-4I should emit runtime errors through the authorized helper as explicit error/control "
					"fallback, with no business answer_text surface when blocked."
				)
			),
		},
		{
			"path_id": "legacy_runtime_business_or_boundary_answer",
			"relative_file_path": PROJECT_RELATIVE_LEGACY_RUNTIME,
			"function_name": "handle_legacy_runtime_turn",
			"function_lines": _line_numbers_starting_with(text, "def handle_legacy_runtime_turn("),
			"answer_type": "governed_report_answer_or_policy_boundary_refusal",
			"answer_type_candidates": [
				"governed_report_answer",
				"policy_boundary_refusal",
				"error_fallback_answer",
			],
			"direct_assistant_append_lines": business_append_lines,
			"direct_assistant_append_count": len(business_append_lines),
			"authorized_emission_helper_lines": business_helper_lines,
			"authorized_emission_helper_count": len(business_helper_lines),
			"build_audit_envelope_lines": business_audit_lines,
			"build_grounded_turn_context_lines": grounded_context_lines,
			"latest_assistant_payload_lines": latest_assistant_payload_lines,
			"latest_qwen_trace_payload_lines": trace_payload_lines,
			"latest_normalized_family_artifact_lines": latest_artifact_lines,
			"append_mechanism": "authorized_assistant_emission_helper" if business_migrated else "direct_append_message",
			"audit_timing": (
				"grounded_turn_audit_and_authorized_emission_contract_before_assistant_append"
				if business_migrated
				else "grounded_turn_and_audit_after_assistant_append"
			),
			"authority_availability_status": (
				"authority_validated_before_assistant_append"
				if business_migrated
				else "audit_created_after_append"
			),
			"authority_inputs_before_append": [
				"runtime_payload.ok",
				"runtime_payload.answer_text",
				"runtime_payload.tool_trace",
				"runtime_payload.agent_meta",
				"runtime_payload.error",
				"grounded_validation_failed_flag",
			],
			"authority_inputs_after_append": [] if business_migrated else [
				"tool_trace_message",
				"latest_qwen_trace_payload",
				"latest_assistant_payload",
				"latest_normalized_family_artifact",
				"build_grounded_turn_context",
				"grounded_turn_context",
				"build_audit_envelope",
				"audit_envelope.final_answer_authority",
			],
			"missing_before_append": [] if business_migrated else [
				"final_answer_authority",
				"grounded_turn_context",
				"policy_boundary_answer_type",
				"authorized_emission_contract",
			],
			"returned_payload_answer_text_surface": False,
			"active_classification": (
				"active_runtime_primary_migrated_to_authorized_helper"
				if business_migrated
				else "active_runtime_primary_unmigrated"
			),
			"service_imported": service_imported,
			"risk_level": "high",
			"risk_reason": (
				"Legacy runtime can emit a business answer or grounded-validation boundary before grounded-turn "
				"and final-answer authority are built."
			),
			"migration_recommendation": (
				"EC-4I migration complete: legacy normal grounded output and grounded-validation boundaries now "
				"emit through the authorized helper before assistant append."
				if business_migrated
				else (
					"EC-4I should build authority before emission, type normal grounded output as governed_report_answer, "
					"type grounded-validation failure as policy_boundary_refusal, and block missing authority without "
					"assistant or API answer_text leakage."
				)
			),
		},
	]


def build_legacy_runtime_emission_mapping_report(
	*,
	root_path: str | Path = ".",
	reviewer: str = "codex_ec4h_legacy_runtime_mapping",
) -> Dict[str, Any]:
	root = Path(root_path).resolve()
	legacy_text = _read_text(root, PROJECT_RELATIVE_LEGACY_RUNTIME)
	service_text = _read_text(root, PROJECT_RELATIVE_SERVICE)
	service_evidence = _service_import_evidence(service_text)
	emitters = _legacy_runtime_emitters(root_path=root, service_evidence=service_evidence)
	direct_count = sum(int(item.get("direct_assistant_append_count") or 0) for item in emitters)
	helper_count = sum(int(item.get("authorized_emission_helper_count") or 0) for item in emitters)
	return {
		"type": LEGACY_RUNTIME_EMISSION_MAPPING_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"slice_id": "ec_4h_legacy_runtime_emission_mapping",
		"reviewer": _clean_text(reviewer),
		"created_at": _utc_now(),
		"branch": _git_branch(root),
		"head": _git_short_head(root),
		"current_dirty_status_count": _git_status_count(root),
		"scope": "EC-4H/EC-4I legacy-runtime emission mapping and post-migration governance",
		"runtime_behavior_changed": helper_count > 0,
		"hard_runtime_blocking_enabled": False,
		"legacy_runtime_emitter_count": len(emitters),
		"legacy_runtime_direct_assistant_append_count": direct_count,
		"legacy_runtime_authorized_emission_helper_count": helper_count,
		"active_runtime_emitter_count": len([item for item in emitters if item.get("service_imported")]),
		"excluded_non_runtime_emitter_count": 0,
		"service_import_evidence": service_evidence,
		"legacy_runtime_emitters": emitters,
		"source_scan": {
			"assistant_append_needle": _assistant_append_needle(),
			"assistant_append_lines": _line_numbers_containing(legacy_text, _assistant_append_needle()),
			"authorized_emission_needle": _authorized_emission_needle(),
			"authorized_emission_helper_lines": _line_numbers_containing(
				legacy_text,
				_authorized_emission_needle(),
			),
			"build_audit_envelope_lines": _call_line_numbers(legacy_text, "build_audit_envelope("),
			"all_assistant_appends_mapped": (
				sorted(_line_numbers_containing(legacy_text, _assistant_append_needle()))
				== sorted(
					line
					for item in emitters
					for line in list(item.get("direct_assistant_append_lines") or [])
				)
			),
		},
		"completed_ec4i_write_scope": {
			"allowed_files": [
				PROJECT_RELATIVE_LEGACY_RUNTIME,
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/legacy_runtime_emission_mapping.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_legacy_runtime_authorized_emission_contracts.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_legacy_runtime_emission_mapping_contracts.py",
				PROJECT_RELATIVE_DRY_RUN,
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_final_answer_emission_dry_run_contracts.py",
			],
			"forbidden_files": [
				PROJECT_RELATIVE_SERVICE,
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/reasoning_lane.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_service_activation.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_governed_requery_activation.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/entity_drilldown_lane.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_lane.py",
			],
			"write_scope_decision": "ec_4i_legacy_runtime_migration_complete_no_next_lane_until_counterpart_acceptance",
		},
		"ec4i_test_requirements": [
			"legacy normal governed output emits through authorized helper before assistant answer",
			"legacy grounded-validation failure emits as policy_boundary_refusal with bounded authority",
			"legacy runtime-client error emits as explicit error/control fallback and not as business answer",
			"missing legacy business authority blocks without assistant or returned answer_text leakage",
			"no duplicate audit envelope after assistant answer",
			"EC-3 inventory legacy unmanaged count decreases after migration",
		],
		"non_goals": [
			"ec4h_was_mapping_only_ec4i_performed_bounded_legacy_runtime_migration",
			"no_service_py_changes",
			"no_nbu_entity_lane_migration",
			"no_root_frontdoor_duplicate_cleanup",
			"no_model_role_strict_enforcement",
			"no_release_packaging_cleanup",
		],
		"final_recommendation": (
			"enterprise_cleanup_ec_4i_ready_for_counterpart_review"
			if helper_count > 0 and direct_count == 0
			else "enterprise_cleanup_ec_4h_ready_for_counterpart_review"
		),
		"file_sha256": _sha256(legacy_text) if legacy_text else "",
		"line_count": len(legacy_text.splitlines()),
	}


def render_legacy_runtime_emission_mapping_markdown(report: Dict[str, Any]) -> str:
	lines = [
		"# EC-4H/EC-4I Legacy Runtime Emission Mapping",
		"",
		f"- Branch: `{_clean_text(report.get('branch'))}`",
		f"- Head: `{_clean_text(report.get('head'))}`",
		f"- Dirty status count: `{report.get('current_dirty_status_count')}`",
		f"- Runtime behavior changed: `{bool(report.get('runtime_behavior_changed'))}`",
		f"- Hard runtime blocking enabled: `{bool(report.get('hard_runtime_blocking_enabled'))}`",
		f"- Final recommendation: `{_clean_text(report.get('final_recommendation'))}`",
		"",
		"## Legacy Runtime Emitters",
		"",
		"| Path | Classification | Answer type | Direct append lines | Audit timing | Recommendation |",
		"|---|---|---|---:|---|---|",
	]
	for item in list(report.get("legacy_runtime_emitters") or []):
		lines.append(
			"| {path} | {classification} | {answer_type} | {lines} | {timing} | {recommendation} |".format(
				path=_clean_text(item.get("path_id")),
				classification=_clean_text(item.get("active_classification")),
				answer_type=_clean_text(item.get("answer_type")),
				lines=", ".join(str(value) for value in list(item.get("direct_assistant_append_lines") or [])),
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
			f"- Legacy runtime imported by service: `{bool(service.get('legacy_runtime_imported_by_service'))}`",
			f"- Import lines: `{list(service.get('legacy_runtime_import_lines') or [])}`",
			f"- Handle call sites: `{list((service.get('service_call_sites') or {}).get('handle_legacy_runtime_turn') or [])}`",
			"",
			"## Authority Timing",
			"",
		]
	)
	for item in list(report.get("legacy_runtime_emitters") or []):
		lines.append(f"Emitter `{_clean_text(item.get('path_id'))}`")
		lines.append(f"- Authority status: `{_clean_text(item.get('authority_availability_status'))}`")
		lines.append("- Inputs before assistant append:")
		for value in list(item.get("authority_inputs_before_append") or []):
			lines.append(f"- `{_clean_text(value)}`")
		lines.append("- Inputs after assistant append:")
		for value in list(item.get("authority_inputs_after_append") or []):
			lines.append(f"- `{_clean_text(value)}`")
		lines.append("- Missing before append:")
		for value in list(item.get("missing_before_append") or []):
			lines.append(f"- `{_clean_text(value)}`")
	lines.extend(["", "## Completed EC-4I Write Scope", ""])
	write_scope = dict(report.get("completed_ec4i_write_scope") or {})
	lines.append("Allowed files:")
	for path in list(write_scope.get("allowed_files") or []):
		lines.append(f"- `{path}`")
	lines.append("")
	lines.append("Forbidden files:")
	for path in list(write_scope.get("forbidden_files") or []):
		lines.append(f"- `{path}`")
	lines.extend(["", "## EC-4I Test Requirements", ""])
	for test_id in list(report.get("ec4i_test_requirements") or []):
		lines.append(f"- `{_clean_text(test_id)}`")
	lines.extend(["", "## Non-Goals", ""])
	for non_goal in list(report.get("non_goals") or []):
		lines.append(f"- `{_clean_text(non_goal)}`")
	lines.append("")
	return "\n".join(lines)


def write_legacy_runtime_emission_mapping_files(
	*,
	root_path: str | Path = ".",
	out_dir: str | Path = DEFAULT_EC4H_OUT_DIR,
	reviewer: str = "codex_ec4h_legacy_runtime_mapping",
) -> Dict[str, Any]:
	out_path = Path(root_path) / out_dir if not Path(out_dir).is_absolute() else Path(out_dir)
	out_path.mkdir(parents=True, exist_ok=True)
	report = build_legacy_runtime_emission_mapping_report(root_path=root_path, reviewer=reviewer)
	json_path = out_path / "qwen_ec4h_legacy_runtime_emission_mapping_report.json"
	markdown_path = out_path / "qwen_ec4h_legacy_runtime_emission_mapping_report.md"
	json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
	markdown_path.write_text(render_legacy_runtime_emission_mapping_markdown(report), encoding="utf-8")
	return {
		"report": report,
		"json_path": str(json_path),
		"markdown_path": str(markdown_path),
	}


def main(argv: List[str] | None = None) -> int:
	parser = argparse.ArgumentParser(description="Generate the EC-4H legacy-runtime emission mapping report.")
	parser.add_argument("--root-path", default=".")
	parser.add_argument("--out-dir", default=DEFAULT_EC4H_OUT_DIR)
	parser.add_argument("--reviewer", default="codex_ec4h_legacy_runtime_mapping")
	args = parser.parse_args(argv)
	result = write_legacy_runtime_emission_mapping_files(
		root_path=args.root_path,
		out_dir=args.out_dir,
		reviewer=args.reviewer,
	)
	print(json.dumps({"ok": True, **result}, indent=2, sort_keys=True))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
