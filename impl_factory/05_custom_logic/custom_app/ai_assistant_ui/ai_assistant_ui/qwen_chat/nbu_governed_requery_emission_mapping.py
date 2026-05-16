from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


NBU_GOVERNED_REQUERY_EMISSION_MAPPING_CONTRACT_TYPE = "qwen_ec4j_nbu_governed_requery_emission_mapping_report"
CONTRACT_VERSION = "1.0"

PROJECT_RELATIVE_NBU_GOVERNED_REQUERY = (
	"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/"
	"qwen_chat/natural_business_understanding_governed_requery_activation.py"
)
PROJECT_RELATIVE_SERVICE = (
	"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/"
	"qwen_chat/service.py"
)
PROJECT_RELATIVE_DRY_RUN = (
	"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/"
	"qwen_chat/final_answer_emission_dry_run.py"
)
DEFAULT_EC4J_OUT_DIR = (
	"impl_factory/00_governance/current_docs/generated/"
	"ec_4j_nbu_governed_requery_emission_mapping"
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
		if " = None" in line:
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
		"nbu_governed_requery_imported_by_service": bool(
			_line_numbers_containing(
				service_text,
				"from ai_assistant_ui.qwen_chat.natural_business_understanding_governed_requery_activation import",
			)
		),
		"nbu_governed_requery_import_lines": _line_numbers_containing(
			service_text,
			"from ai_assistant_ui.qwen_chat.natural_business_understanding_governed_requery_activation import",
		),
		"nbu_governed_requery_alias_lines": _line_numbers_containing(
			service_text,
			"try_activate_nbu_governed_requery_response as _try_activate_nbu_governed_requery_response",
		),
		"service_call_sites": {
			"_try_activate_nbu_governed_requery_response": _line_numbers_containing(
				service_text,
				"_try_activate_nbu_governed_requery_response(",
			),
			"activation_level_governed_requery": _line_numbers_containing(
				service_text,
				'activation_level="governed_requery"',
			),
		},
	}


def _nbu_governed_requery_emitters(
	*,
	root_path: Path,
	service_evidence: Dict[str, Any],
) -> List[Dict[str, Any]]:
	text = _read_text(root_path, PROJECT_RELATIVE_NBU_GOVERNED_REQUERY)
	append_lines = _line_numbers_containing(text, _assistant_append_needle())
	helper_lines = _line_numbers_containing(text, _authorized_emission_needle())
	audit_lines = _call_line_numbers(text, "build_audit_envelope(")
	grounded_payload_lines = _line_numbers_containing(text, "grounded_turn_payload")
	artifact_payload_lines = _line_numbers_containing(text, "artifact_payload")
	rendered_payload_lines = _line_numbers_containing(text, "rendered_response_payload")
	activation_contract_lines = _line_numbers_containing(text, "_activation_contract(")
	execution_path_lines = _line_numbers_containing(text, "execution_path_payload")
	direct_response_lines = _line_numbers_containing(text, "direct_response")
	save_session_lines = _line_numbers_containing(text, "save_session(session_doc")
	return_lines = _line_numbers_containing(text, '"mode": "nbu_governed_requery_entity_detail"')
	service_imported = bool(service_evidence.get("nbu_governed_requery_imported_by_service"))
	migrated = bool(helper_lines) and not append_lines
	return [
		{
			"path_id": "nbu_governed_requery_entity_detail",
			"relative_file_path": PROJECT_RELATIVE_NBU_GOVERNED_REQUERY,
			"function_name": "try_activate_nbu_governed_requery_response",
			"function_lines": _line_numbers_starting_with(text, "def try_activate_nbu_governed_requery_response("),
			"answer_type": "business_facing_factual_answer_or_governed_report_answer",
			"answer_type_candidates": [
				"business_facing_factual_answer",
				"governed_report_answer",
			],
			"direct_assistant_append_lines": append_lines,
			"direct_assistant_append_count": len(append_lines),
			"authorized_emission_helper_lines": helper_lines,
			"authorized_emission_helper_count": len(helper_lines),
			"build_audit_envelope_lines": audit_lines,
			"grounded_turn_payload_lines": grounded_payload_lines,
			"artifact_payload_lines": artifact_payload_lines,
			"rendered_response_payload_lines": rendered_payload_lines,
			"activation_contract_lines": activation_contract_lines,
			"execution_path_payload_lines": execution_path_lines,
			"direct_response_lines": direct_response_lines,
			"save_session_lines": save_session_lines,
			"return_payload_mode_lines": return_lines,
			"append_mechanism": "authorized_assistant_emission_helper" if migrated else "direct_append_message",
			"audit_timing": (
				"audit_envelope_and_authorized_emission_contract_before_assistant_append"
				if migrated
				else "audit_envelope_after_assistant_append_conditioned_on_contract_imports"
			),
			"authority_availability_status": (
				"authority_validated_before_assistant_append"
				if migrated
				else "entity_artifact_and_grounded_turn_before_append_final_authority_after_append"
			),
			"authority_inputs_before_append": [
				"nbu_trace_payload",
				"current_artifact",
				"latest_grounded_turn",
				"activation_assessment",
				"entity_reference",
				"execute_entity_drilldown.outcome",
				"outcome.artifact_payload",
				"outcome.grounded_turn_payload",
				"outcome.rendered_response_payload",
				"direct_evidence_response.answer_text",
				"activation_contract",
				"execution_path_payload",
			],
			"authority_inputs_after_append": [] if migrated else [
				"build_followup_resolution_contract",
				"build_audit_envelope",
				"audit_envelope.final_answer_authority",
			],
			"missing_before_append": [] if migrated else [
				"final_answer_authority",
				"authorized_emission_contract",
				"mandatory_preflight_status",
				"non_optional_interaction_contract",
				"non_optional_followup_resolution",
			],
			"conditional_audit_gap": not migrated,
			"api_payload_answer_text_surface": False,
			"active_classification": (
				"active_runtime_primary_migrated_to_authorized_helper"
				if migrated
				else "active_runtime_primary_unmigrated"
			),
			"service_imported": service_imported,
			"risk_level": "high",
			"risk_reason": (
				"NBU governed requery emits an entity-detail business answer before centralized final-answer "
				"authority validation; the audit envelope is conditional on contract objects being available."
			),
			"migration_recommendation": (
				"ec_4k_migration_complete_counterpart_review_required_before_next_lane"
				if migrated
				else (
					"EC-4K should route this entity-detail answer through emit_authorized_assistant_answer, "
					"build authority before append, and block any missing authority without assistant/API answer leakage."
				)
			),
		}
	]


def build_nbu_governed_requery_emission_mapping_report(
	*,
	root_path: str | Path = ".",
	reviewer: str = "codex_ec4j_nbu_governed_requery_mapping",
) -> Dict[str, Any]:
	root = Path(root_path).resolve()
	text = _read_text(root, PROJECT_RELATIVE_NBU_GOVERNED_REQUERY)
	service_text = _read_text(root, PROJECT_RELATIVE_SERVICE)
	service_evidence = _service_import_evidence(service_text)
	emitters = _nbu_governed_requery_emitters(root_path=root, service_evidence=service_evidence)
	direct_count = sum(int(item.get("direct_assistant_append_count") or 0) for item in emitters)
	helper_count = sum(int(item.get("authorized_emission_helper_count") or 0) for item in emitters)
	return {
		"type": NBU_GOVERNED_REQUERY_EMISSION_MAPPING_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"slice_id": "ec_4j_nbu_governed_requery_emission_mapping",
		"scope": "EC-4J/EC-4K NBU governed-requery emission mapping and post-migration governance",
		"created_at": _utc_now(),
		"reviewer": _clean_text(reviewer),
		"branch": _git_branch(root),
		"head": _git_short_head(root),
		"current_dirty_status_count": _git_status_count(root),
		"runtime_behavior_changed": bool(helper_count > 0 and direct_count == 0),
		"authorized_emission_runtime_migration_done": bool(helper_count > 0 and direct_count == 0),
		"hard_runtime_blocking_enabled": False,
		"nbu_governed_requery_emitter_count": len(emitters),
		"nbu_governed_requery_direct_assistant_append_count": direct_count,
		"nbu_governed_requery_authorized_emission_helper_count": helper_count,
		"active_runtime_emitter_count": len([item for item in emitters if item.get("service_imported")]),
		"excluded_non_runtime_emitter_count": 0,
		"service_import_evidence": service_evidence,
		"nbu_governed_requery_emitters": emitters,
		"source_scan": {
			"assistant_append_needle": _assistant_append_needle(),
			"assistant_append_lines": _line_numbers_containing(text, _assistant_append_needle()),
			"authorized_emission_needle": _authorized_emission_needle(),
			"authorized_emission_helper_lines": _line_numbers_containing(text, _authorized_emission_needle()),
			"all_assistant_appends_mapped": sorted(_line_numbers_containing(text, _assistant_append_needle()))
			== sorted(
				line
				for item in emitters
				for line in item.get("direct_assistant_append_lines", [])
			),
		},
		"completed_ec4k_write_scope": {
			"allowed_files": [
				PROJECT_RELATIVE_NBU_GOVERNED_REQUERY,
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/nbu_governed_requery_emission_mapping.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_nbu_governed_requery_authorized_emission_contracts.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_nbu_governed_requery_emission_mapping_contracts.py",
				PROJECT_RELATIVE_DRY_RUN,
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_final_answer_emission_dry_run_contracts.py",
			],
			"forbidden_files": [
				PROJECT_RELATIVE_SERVICE,
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/entity_drilldown_lane.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_followup_support.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_lane.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/legacy_runtime_lane.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/reasoning_lane.py",
			],
			"write_scope_decision": "ec_4k_nbu_governed_requery_migration_complete_no_next_lane_until_counterpart_acceptance",
		},
		"ec4k_test_requirements": [
			"governed NBU entity-detail answer emits through authorized helper before assistant answer",
			"missing entity-detail authority blocks with no assistant message and no returned answer_text",
			"direct-evidence-first answer preserves selected answer text through authorized emission",
			"rich entity-detail answer preserves rendered response text through authorized emission",
			"audit envelope and authorized emission contract appear before assistant answer",
			"no duplicate audit envelope appears after assistant answer",
			"EC-3 inventory removes nbu_governed_requery_entity_detail after migration",
		],
		"non_goals": [
			"ec4j_was_mapping_only_ec4k_performed_bounded_nbu_governed_requery_migration",
			"no_service_py_changes",
			"no_entity_followup_lane_migration",
			"no_root_frontdoor_duplicate_cleanup",
			"no_model_role_strict_enforcement",
			"no_release_packaging_cleanup",
		],
		"final_recommendation": (
			"enterprise_cleanup_ec_4k_ready_for_counterpart_review"
			if helper_count > 0 and direct_count == 0
			else "enterprise_cleanup_ec_4j_ready_for_counterpart_review"
		),
		"file_sha256": _sha256(text) if text else "",
		"line_count": len(text.splitlines()),
	}


def render_nbu_governed_requery_emission_mapping_markdown(report: Dict[str, Any]) -> str:
	lines = [
		"# EC-4J/EC-4K NBU Governed-Requery Emission Mapping",
		"",
		f"- Branch: `{_clean_text(report.get('branch'))}`",
		f"- Head: `{_clean_text(report.get('head'))}`",
		f"- Dirty status count: `{report.get('current_dirty_status_count')}`",
		f"- Runtime behavior changed: `{bool(report.get('runtime_behavior_changed'))}`",
		f"- Authorized emission runtime migration done: `{bool(report.get('authorized_emission_runtime_migration_done'))}`",
		f"- Hard runtime blocking enabled: `{bool(report.get('hard_runtime_blocking_enabled'))}`",
		f"- Final recommendation: `{_clean_text(report.get('final_recommendation'))}`",
		"",
		"## NBU Governed-Requery Emitters",
		"",
	]
	for item in list(report.get("nbu_governed_requery_emitters") or []):
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
	lines.append(f"- Imported by service: `{bool(service.get('nbu_governed_requery_imported_by_service'))}`")
	lines.append(f"- Import lines: `{service.get('nbu_governed_requery_import_lines')}`")
	lines.append(f"- Call sites: `{service.get('service_call_sites')}`")
	lines.extend(["", "## Completed EC-4K Write Scope", ""])
	write_scope = dict(report.get("completed_ec4k_write_scope") or {})
	lines.append("Allowed files:")
	for path in list(write_scope.get("allowed_files") or []):
		lines.append(f"- `{path}`")
	lines.append("")
	lines.append("Forbidden files:")
	for path in list(write_scope.get("forbidden_files") or []):
		lines.append(f"- `{path}`")
	lines.extend(["", "## EC-4K Test Requirements", ""])
	for test_id in list(report.get("ec4k_test_requirements") or []):
		lines.append(f"- `{_clean_text(test_id)}`")
	lines.extend(["", "## Non-Goals", ""])
	for non_goal in list(report.get("non_goals") or []):
		lines.append(f"- `{_clean_text(non_goal)}`")
	lines.append("")
	return "\n".join(lines)


def write_nbu_governed_requery_emission_mapping_files(
	*,
	root_path: str | Path = ".",
	out_dir: str | Path = DEFAULT_EC4J_OUT_DIR,
	reviewer: str = "codex_ec4j_nbu_governed_requery_mapping",
) -> Dict[str, Any]:
	out_path = Path(root_path) / out_dir if not Path(out_dir).is_absolute() else Path(out_dir)
	out_path.mkdir(parents=True, exist_ok=True)
	report = build_nbu_governed_requery_emission_mapping_report(root_path=root_path, reviewer=reviewer)
	json_path = out_path / "qwen_ec4j_nbu_governed_requery_emission_mapping_report.json"
	markdown_path = out_path / "qwen_ec4j_nbu_governed_requery_emission_mapping_report.md"
	json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
	markdown_path.write_text(render_nbu_governed_requery_emission_mapping_markdown(report), encoding="utf-8")
	return {
		"report": report,
		"json_path": str(json_path),
		"markdown_path": str(markdown_path),
	}


def main(argv: List[str] | None = None) -> int:
	parser = argparse.ArgumentParser(description="Generate the EC-4J NBU governed-requery emission mapping report.")
	parser.add_argument("--root-path", default=".")
	parser.add_argument("--out-dir", default=DEFAULT_EC4J_OUT_DIR)
	parser.add_argument("--reviewer", default="codex_ec4j_nbu_governed_requery_mapping")
	args = parser.parse_args(argv)
	result = write_nbu_governed_requery_emission_mapping_files(
		root_path=args.root_path,
		out_dir=args.out_dir,
		reviewer=args.reviewer,
	)
	print(json.dumps({**result, "ok": True}, indent=2, sort_keys=True))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
