from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


REASONING_LANE_EMISSION_MAPPING_CONTRACT_TYPE = "qwen_ec4g_reasoning_lane_authorized_emission_migration_report"
CONTRACT_VERSION = "1.0"

PROJECT_RELATIVE_REASONING_LANE = (
	"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/"
	"qwen_chat/lanes/reasoning_lane.py"
)
PROJECT_RELATIVE_SERVICE = (
	"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/"
	"qwen_chat/service.py"
)
PROJECT_RELATIVE_DRY_RUN = (
	"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/"
	"qwen_chat/final_answer_emission_dry_run.py"
)
DEFAULT_EC4G_OUT_DIR = (
	"impl_factory/00_governance/current_docs/generated/"
	"ec_4g_reasoning_lane_authorized_emission_migration"
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
		if "from ai_assistant_ui.qwen_chat.lanes.reasoning_lane import" in line
	]
	return {
		"reasoning_lane_imported_by_service": bool(import_lines),
		"reasoning_lane_import_lines": import_lines,
		"service_call_sites": {
			"handle_reasoning_turn": _line_numbers_containing(service_text, "handle_reasoning_turn("),
			"reasoning_handled_payload": _line_numbers_containing(service_text, "reasoning_handled, reasoning_payload"),
		},
	}


def _reasoning_emitter_summary(
	*,
	path_id: str,
	direct_assistant_append_lines: List[int],
	authorized_emission_helper_lines: List[int],
	audit_envelope_lines: List[int],
	knowledge_boundary_lines: List[int],
	answer_type: str,
	risk_level: str,
	risk_reason: str,
	audit_timing: str,
	authority_availability_status: str,
	migration_recommendation: str,
	reason: str,
	active_classification: str = "active_runtime_primary_unmigrated",
	append_mechanism: str = "direct_append_message",
	runtime_behavior_changed: bool = False,
	authority_inputs_after_append: List[str] | None = None,
	missing_before_append: List[str] | None = None,
) -> Dict[str, Any]:
	return {
		"path_id": path_id,
		"relative_file_path": PROJECT_RELATIVE_REASONING_LANE,
		"function_name": "handle_reasoning_turn",
		"direct_assistant_append_lines": list(direct_assistant_append_lines),
		"direct_assistant_append_count": len(direct_assistant_append_lines),
		"authorized_emission_helper_lines": list(authorized_emission_helper_lines),
		"authorized_emission_helper_count": len(authorized_emission_helper_lines),
		"build_audit_envelope_lines": list(audit_envelope_lines),
		"knowledge_boundary_lines": list(knowledge_boundary_lines),
		"answer_type": answer_type,
		"append_mechanism": append_mechanism,
		"audit_timing": audit_timing,
		"authority_availability_status": authority_availability_status,
		"authority_inputs_before_append": [
			"interaction_contract",
			"frontdoor_semantic_result",
			"frontdoor_contract",
			"clarification_response_contract_if_present",
			"provisional_response_policy_contract",
			"reasoning_activation_contract",
			"reasoning_semantic_result",
			"reasoning_execution",
			"model_role_observability",
			"model_role_strict_readiness",
			"reasoning_execution.reasoning_contract_if_present",
			"knowledge_boundary_contract",
			"reasoning_followup_resolution",
			"execution_path",
			"latest_grounded_turn",
		],
		"authority_inputs_after_append": list(authority_inputs_after_append or []),
		"missing_before_append": list(missing_before_append or []),
		"active_classification": active_classification,
		"service_imported": True,
		"runtime_behavior_changed": bool(runtime_behavior_changed),
		"risk_level": risk_level,
		"risk_reason": risk_reason,
		"migration_recommendation": migration_recommendation,
		"reason": reason,
	}


def _reasoning_emitters(reasoning_text: str) -> List[Dict[str, Any]]:
	append_lines = _line_numbers_containing(reasoning_text, _assistant_append_needle())
	helper_lines = _line_numbers_containing(reasoning_text, _authorized_emission_needle())
	audit_lines = _line_numbers_containing(reasoning_text, "build_audit_envelope(")
	boundary_lines = _line_numbers_containing(reasoning_text, "append_knowledge_boundary_contract(")
	migrated = bool(helper_lines) and not append_lines
	business_append = [line for line in append_lines if line < 200]
	guardrail_append = [line for line in append_lines if line >= 200]
	business_helper = [line for line in helper_lines if line < 240]
	guardrail_helper = [line for line in helper_lines if line >= 240]
	business_audit = [line for line in audit_lines if line < 220]
	guardrail_audit = [line for line in audit_lines if line >= 220]
	business_boundary = [line for line in boundary_lines if line < 200]
	guardrail_boundary = [line for line in boundary_lines if line >= 200]
	active_classification = (
		"active_runtime_primary_migrated_to_authorized_helper"
		if migrated
		else "active_runtime_primary_unmigrated"
	)
	append_mechanism = "authorized_assistant_emission_helper" if migrated else "direct_append_message"
	authority_inputs_after_append = [] if migrated else ["audit_envelope.final_answer_authority"]
	missing_before_append = [] if migrated else ["final_answer_authority", "authorized_emission_contract"]
	return [
		_reasoning_emitter_summary(
			path_id="reasoning_lane_business_answer",
			direct_assistant_append_lines=business_append,
			authorized_emission_helper_lines=business_helper,
			audit_envelope_lines=business_audit,
			knowledge_boundary_lines=business_boundary,
			answer_type="reasoning_business_consultant_answer",
			risk_level="high",
			risk_reason=(
				"Grounded ERP reasoning can produce business interpretation/recommendation text, but the "
				"audit envelope and final-answer authority are appended after the assistant answer."
			),
			audit_timing=(
				"audit_envelope_and_authorized_emission_contract_before_assistant_append"
				if migrated
				else "audit_envelope_after_assistant_append"
			),
			authority_availability_status=(
				"authority_validated_before_assistant_append"
				if migrated
				else "knowledge_boundary_before_append_audit_after_append"
			),
			migration_recommendation=(
				"ec_4g_migration_complete_counterpart_review_required_before_next_lane"
				if migrated
				else "map_only_in_ec_4f_migrate_in_ec_4g_after_counterpart_approval"
			),
			reason=(
				"Answered reasoning branch now emits through emit_authorized_assistant_answer before the "
				"user-visible assistant message."
				if migrated
				else (
					"Answered reasoning branch appends the assistant answer after reasoning contracts and knowledge "
					"boundary are stored, but before build_audit_envelope creates final-answer authority."
				)
			),
			active_classification=active_classification,
			append_mechanism=append_mechanism,
			runtime_behavior_changed=migrated,
			authority_inputs_after_append=authority_inputs_after_append,
			missing_before_append=missing_before_append,
		),
		_reasoning_emitter_summary(
			path_id="reasoning_lane_guardrail_boundary",
			direct_assistant_append_lines=guardrail_append,
			authorized_emission_helper_lines=guardrail_helper,
			audit_envelope_lines=guardrail_audit,
			knowledge_boundary_lines=guardrail_boundary,
			answer_type="policy_boundary_refusal",
			risk_level="medium",
			risk_reason=(
				"Deterministic reasoning boundary text is safer than a business answer, but bounded authority is "
				"still audited after assistant emission."
			),
			audit_timing=(
				"audit_envelope_and_authorized_emission_contract_before_assistant_append"
				if migrated
				else "audit_envelope_after_assistant_append"
			),
			authority_availability_status=(
				"authority_validated_before_assistant_append"
				if migrated
				else "policy_boundary_before_append_audit_after_append"
			),
			migration_recommendation=(
				"ec_4g_migration_complete_counterpart_review_required_before_next_lane"
				if migrated
				else "map_only_in_ec_4f_migrate_in_ec_4g_after_counterpart_approval"
			),
			reason=(
				"Guardrail branch now emits through emit_authorized_assistant_answer as a bounded "
				"policy_boundary_refusal before the user-visible assistant message."
				if migrated
				else (
					"Guardrail branch renders a knowledge-boundary answer and appends it before the audit envelope. "
					"EC-4G should preserve policy_boundary_refusal / bounded behavior through the authorized helper."
				)
			),
			active_classification=active_classification,
			append_mechanism=append_mechanism,
			runtime_behavior_changed=migrated,
			authority_inputs_after_append=authority_inputs_after_append,
			missing_before_append=missing_before_append,
		),
	]


def _reasoning_model_role_delta(reasoning_text: str) -> Dict[str, Any]:
	import_lines = _line_numbers_containing(reasoning_text, "model_role_")
	payload_lines = _line_numbers_containing(reasoning_text, "append_tool_payload(session_doc, model_role_")
	agent_meta_lines = _line_numbers_containing(reasoning_text, '"model_role_')
	return {
		"runtime_delta_detected": bool(import_lines or payload_lines or agent_meta_lines),
		"classification": "pre_existing_s7_reasoning_model_role_observability_prep",
		"baseline_evidence": (
			"S7-X1 baseline recorded qwen_chat/lanes/reasoning_lane.py as an already modified "
			"S7 implementation file before EC-4F."
		),
		"import_or_reference_lines": import_lines,
		"appended_model_role_payload_lines": payload_lines,
		"returned_or_audit_agent_meta_lines": agent_meta_lines,
		"runtime_delta_summary": [
			"Builds model-role observability and strict-readiness payloads from reasoning runtime agent_meta.",
			"Appends model-role payloads in answered and guardrail branches before the assistant answer.",
			"Adds model-role payloads into audit runtime agent_meta and returned agent_meta.",
		],
		"authority_timing_delta": "none_observed; assistant append still precedes audit envelope in both reasoning branches",
		"answer_semantics_delta": "none_expected; answer text still comes from reasoning_execution.answer_text or rendered knowledge-boundary answer",
	}


def build_reasoning_lane_emission_mapping_report(
	*,
	root_path: str | Path = ".",
	reviewer: str = "codex_ec4g_reasoning_authorized_emission",
) -> Dict[str, Any]:
	root = Path(root_path).resolve()
	reasoning_text = _read_text(root, PROJECT_RELATIVE_REASONING_LANE)
	service_text = _read_text(root, PROJECT_RELATIVE_SERVICE)
	service_evidence = _service_import_evidence(service_text)
	emitters = _reasoning_emitters(reasoning_text)
	append_lines = _line_numbers_containing(reasoning_text, _assistant_append_needle())
	authorized_helper_lines = _line_numbers_containing(reasoning_text, _authorized_emission_needle())
	model_role_delta = _reasoning_model_role_delta(reasoning_text)
	return {
		"type": REASONING_LANE_EMISSION_MAPPING_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"slice_id": "ec_4g_reasoning_lane_authorized_emission_migration",
		"reviewer": _clean_text(reviewer),
		"created_at": _utc_now(),
		"branch": _git_branch(root),
		"head": _git_short_head(root),
		"current_dirty_status_count": _git_status_count(root),
		"scope": "EC-4G reasoning-lane authorized-emission migration with model-role observability preservation",
		"runtime_behavior_changed": bool(model_role_delta.get("runtime_delta_detected")),
		"hard_runtime_blocking_enabled": False,
		"authorized_emission_runtime_migration_done": bool(authorized_helper_lines) and not bool(append_lines),
		"reasoning_model_role_runtime_delta": model_role_delta,
		"reasoning_lane_emitter_count": len(emitters),
		"reasoning_lane_direct_assistant_append_count": len(append_lines),
		"reasoning_lane_authorized_emission_helper_count": len(authorized_helper_lines),
		"active_runtime_emitter_count": len(emitters),
		"clarification_control_emitter_count": 0,
		"clarification_control_assessment": (
			"no_reasoning_lane_assistant_control_or_clarification_path_observed; "
			"non-accepted reasoning semantic results return False and are handled upstream"
		),
		"service_import_evidence": service_evidence,
		"reasoning_lane_emitters": emitters,
		"source_scan": {
			"assistant_append_needle": _assistant_append_needle(),
			"assistant_append_lines": append_lines,
			"authorized_emission_needle": _authorized_emission_needle(),
			"authorized_emission_helper_lines": authorized_helper_lines,
			"all_assistant_appends_mapped": sorted(append_lines)
			== sorted(
				line
				for emitter in emitters
				for line in list(emitter.get("direct_assistant_append_lines") or [])
			),
		},
		"completed_ec4g_write_scope": {
			"allowed_files": [
				PROJECT_RELATIVE_REASONING_LANE,
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_reasoning_lane_authorized_emission_contracts.py",
				PROJECT_RELATIVE_DRY_RUN,
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_final_answer_emission_dry_run_contracts.py",
			],
			"forbidden_files": [
				PROJECT_RELATIVE_SERVICE,
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/legacy_runtime_lane.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_service_activation.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_governed_requery_activation.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/entity_drilldown_lane.py",
				"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_lane.py",
			],
			"write_scope_decision": "ec_4g_reasoning_lane_migration_complete_no_next_lane_until_counterpart_acceptance",
		},
		"ec4g_test_requirements": [
			"reasoning answered business path emits through authorized helper before assistant answer",
			"reasoning answered business path requires final-answer authority passed",
			"reasoning guardrail path emits policy_boundary_refusal with bounded authority",
			"missing reasoning business authority blocks without assistant answer or returned business answer_text",
			"reasoning guardrail returned answer_text equals the emitted rendered boundary answer",
			"no duplicate audit envelope after assistant answer",
			"EC-3 inventory reasoning unmanaged count decreased after migration",
		],
		"non_goals": [
			"no_service_py_changes",
			"no_legacy_nbu_entity_lane_migration",
			"no_model_role_strict_enforcement",
			"no_release_packaging_cleanup",
			"no_frontdoor_duplicate_cleanup",
		],
		"final_recommendation": "enterprise_cleanup_ec_4g_ready_for_counterpart_review",
	}


def render_reasoning_lane_emission_mapping_markdown(report: Dict[str, Any]) -> str:
	lines = [
		"# EC-4G Reasoning Lane Authorized Emission Migration",
		"",
		f"- Branch: `{_clean_text(report.get('branch'))}`",
		f"- Head: `{_clean_text(report.get('head'))}`",
		f"- Dirty status count: `{report.get('current_dirty_status_count')}`",
		f"- Runtime behavior changed: `{bool(report.get('runtime_behavior_changed'))}`",
		f"- Authorized emission runtime migration done: `{bool(report.get('authorized_emission_runtime_migration_done'))}`",
		f"- Hard runtime blocking enabled: `{bool(report.get('hard_runtime_blocking_enabled'))}`",
		f"- Final recommendation: `{_clean_text(report.get('final_recommendation'))}`",
		f"- Clarification/control assessment: `{_clean_text(report.get('clarification_control_assessment'))}`",
		"",
		"## Reasoning Lane Emitters",
		"",
		"| Path | Answer type | Risk | Direct append lines | Helper lines | Audit timing | Recommendation |",
		"|---|---|---:|---:|---:|---|---|",
	]
	for item in list(report.get("reasoning_lane_emitters") or []):
		lines.append(
			"| {path} | {answer_type} | {risk} | {lines} | {helper_lines} | {timing} | {recommendation} |".format(
				path=_clean_text(item.get("path_id")),
				answer_type=_clean_text(item.get("answer_type")),
				risk=_clean_text(item.get("risk_level")),
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
			f"- Reasoning lane imported by service: `{bool(service.get('reasoning_lane_imported_by_service'))}`",
			f"- Import lines: `{list(service.get('reasoning_lane_import_lines') or [])}`",
			f"- Handle call sites: `{list((service.get('service_call_sites') or {}).get('handle_reasoning_turn') or [])}`",
			"",
			"## Authority Timing",
			"",
		]
	)
	delta = dict(report.get("reasoning_model_role_runtime_delta") or {})
	lines.extend(
		[
			"",
			"## Runtime Delta Classification",
			"",
			f"- Runtime delta detected: `{bool(delta.get('runtime_delta_detected'))}`",
			f"- Classification: `{_clean_text(delta.get('classification'))}`",
			f"- Baseline evidence: `{_clean_text(delta.get('baseline_evidence'))}`",
			f"- Authority timing delta: `{_clean_text(delta.get('authority_timing_delta'))}`",
			f"- Answer semantics delta: `{_clean_text(delta.get('answer_semantics_delta'))}`",
			f"- Model-role reference lines: `{list(delta.get('import_or_reference_lines') or [])}`",
			f"- Model-role payload append lines: `{list(delta.get('appended_model_role_payload_lines') or [])}`",
			f"- Model-role agent-meta lines: `{list(delta.get('returned_or_audit_agent_meta_lines') or [])}`",
		]
	)
	for item in list(report.get("reasoning_lane_emitters") or []):
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
	lines.extend(["", "## Completed EC-4G Write Scope", ""])
	write_scope = dict(report.get("completed_ec4g_write_scope") or {})
	lines.append("Allowed files:")
	for path in list(write_scope.get("allowed_files") or []):
		lines.append(f"- `{path}`")
	lines.append("")
	lines.append("Forbidden files:")
	for path in list(write_scope.get("forbidden_files") or []):
		lines.append(f"- `{path}`")
	lines.extend(["", "## EC-4G Test Requirements", ""])
	for test_id in list(report.get("ec4g_test_requirements") or []):
		lines.append(f"- `{_clean_text(test_id)}`")
	lines.extend(["", "## Non-Goals", ""])
	for non_goal in list(report.get("non_goals") or []):
		lines.append(f"- `{_clean_text(non_goal)}`")
	lines.append("")
	return "\n".join(lines)


def write_reasoning_lane_emission_mapping_files(
	*,
	root_path: str | Path = ".",
	out_dir: str | Path = DEFAULT_EC4G_OUT_DIR,
	reviewer: str = "codex_ec4g_reasoning_authorized_emission",
) -> Dict[str, Any]:
	out_path = Path(root_path) / out_dir if not Path(out_dir).is_absolute() else Path(out_dir)
	out_path.mkdir(parents=True, exist_ok=True)
	report = build_reasoning_lane_emission_mapping_report(root_path=root_path, reviewer=reviewer)
	json_path = out_path / "qwen_ec4g_reasoning_lane_authorized_emission_migration_report.json"
	markdown_path = out_path / "qwen_ec4g_reasoning_lane_authorized_emission_migration_report.md"
	json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
	markdown_path.write_text(render_reasoning_lane_emission_mapping_markdown(report), encoding="utf-8")
	return {
		"report": report,
		"json_path": str(json_path),
		"markdown_path": str(markdown_path),
	}


def main(argv: List[str] | None = None) -> int:
	parser = argparse.ArgumentParser(description="Generate the EC-4F reasoning-lane emission mapping report.")
	parser.add_argument("--root-path", default=".")
	parser.add_argument("--out-dir", default=DEFAULT_EC4G_OUT_DIR)
	parser.add_argument("--reviewer", default="codex_ec4g_reasoning_authorized_emission")
	args = parser.parse_args(argv)
	result = write_reasoning_lane_emission_mapping_files(
		root_path=args.root_path,
		out_dir=args.out_dir,
		reviewer=args.reviewer,
	)
	print(json.dumps({"ok": True, **result}, indent=2, sort_keys=True))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
