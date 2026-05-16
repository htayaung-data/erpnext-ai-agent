from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .natural_business_understanding_contracts import CONTRACT_VERSION
from .regression_scenario_packs import (
	S7_REGRESSION_SCENARIO_REGISTRY,
	build_regression_scenario_contract,
)


MANUAL_UAT_BROWSER_BATCH_RUNNER_CONTRACT_TYPE = "qwen_manual_uat_browser_batch_runner_contract"
MANUAL_UAT_BROWSER_BATCH_SCENARIO_CONTRACT_TYPE = "qwen_manual_uat_browser_batch_scenario_contract"
MANUAL_UAT_BROWSER_BATCH_RUNNER_SUITE_ID = "s7_browser_batch_resilience_runner_contracts"

DEFAULT_BROWSER_BATCH_RUNNER_JSON_PATH = (
	"impl_factory/00_governance/current_docs/generated/"
	"qwen_s7_browser_batch_resilience_runner_contract.json"
)
DEFAULT_BROWSER_BATCH_RUNNER_MARKDOWN_PATH = (
	"impl_factory/00_governance/current_docs/generated/"
	"qwen_s7_browser_batch_resilience_runner_contract.md"
)

BROWSER_BATCH_STATUS_RELEASE_READY = "release_ready"
BROWSER_BATCH_STATUS_PARTIAL_BLOCKED = "partial_blocked"
BROWSER_BATCH_STATUS_BLOCKED = "blocked"

SCENARIO_STATUS_PASSED = "passed"
SCENARIO_STATUS_BLOCKED = "blocked"

CHECKPOINT_QUEUED = "queued"
CHECKPOINT_SESSION_STARTED = "session_started"
CHECKPOINT_PROMPTS_SENT = "prompts_sent"
CHECKPOINT_ANSWER_CAPTURED = "answer_captured"
CHECKPOINT_TRACE_REQUESTED = "trace_requested"
CHECKPOINT_TRACE_CAPTURED = "trace_captured"
CHECKPOINT_NORMALIZED = "normalized"
CHECKPOINT_IMPORT_READY = "import_ready"
CHECKPOINT_IMPORTED = "imported"
CHECKPOINT_CLEANED_UP = "cleaned_up"

REQUIRED_CHECKPOINT_STATES = [
	CHECKPOINT_QUEUED,
	CHECKPOINT_SESSION_STARTED,
	CHECKPOINT_PROMPTS_SENT,
	CHECKPOINT_ANSWER_CAPTURED,
	CHECKPOINT_TRACE_REQUESTED,
	CHECKPOINT_TRACE_CAPTURED,
	CHECKPOINT_NORMALIZED,
	CHECKPOINT_IMPORT_READY,
	CHECKPOINT_IMPORTED,
	CHECKPOINT_CLEANED_UP,
]

ALLOWED_CLEANUP_STATES = [
	"session_checkpointed",
	"signed_out",
	"browser_session_closed",
	"cleaned_up",
]

REQUIRED_BROWSER_BATCH_REASON_CODES = [
	"capture_result_missing",
	"scenario_not_registered",
	"unexpected_scenario_capture",
	"duplicate_capture_result",
	"expected_contract_missing",
	"missing_answer_text",
	"missing_trace_text",
	"browser_timeout",
	"background_run_continued",
	"manual_interrupt",
	"login_redirect",
	"unknown_browser_state",
	"stale_trace_reused",
	"cleanup_not_confirmed",
	"checkpoint_state_unknown",
	"retry_value_invalid",
	"max_retries_exceeded",
]

RETRYABLE_BROWSER_BATCH_REASON_CODES = [
	"capture_result_missing",
	"missing_answer_text",
	"missing_trace_text",
	"browser_timeout",
	"background_run_continued",
	"manual_interrupt",
	"login_redirect",
	"unknown_browser_state",
	"cleanup_not_confirmed",
]

TIMEOUT_REASON_CODES = [
	"browser_timeout",
	"background_run_continued",
	"manual_interrupt",
	"login_redirect",
	"unknown_browser_state",
]

FORBIDDEN_BROWSER_BATCH_ACTIONS = [
	"Do not promote a scenario without captured final answer text.",
	"Do not promote a scenario without its own latest context authority trace.",
	"Do not reuse a trace from another scenario or earlier browser session.",
	"Do not infer missing row, entity, policy, or model-role fields from memory.",
	"Do not mark a timed-out scenario as passed because the browser continued in the background.",
	"Do not include blocked scenario ids in the strict S7-6P import expected-scenario list.",
]


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


def _dedupe(values: Iterable[str]) -> List[str]:
	seen = set()
	out: List[str] = []
	for value in values:
		text = _clean_text(value)
		if text and text not in seen:
			seen.add(text)
			out.append(text)
	return out


def _scenario_registry_map(registry: Iterable[Dict[str, Any]] | None = None) -> Dict[str, Dict[str, Any]]:
	out: Dict[str, Dict[str, Any]] = {}
	for entry in registry or S7_REGRESSION_SCENARIO_REGISTRY:
		if not isinstance(entry, dict):
			continue
		scenario = build_regression_scenario_contract(entry)
		scenario_id = _clean_text(scenario.get("scenario_id"))
		if scenario_id:
			out[scenario_id] = scenario
	return out


def _scenario_ids_from_registry(registry: Iterable[Dict[str, Any]] | None = None) -> List[str]:
	return list(_scenario_registry_map(registry).keys())


def _checkpoint_rank(checkpoint_state: str) -> int:
	try:
		return REQUIRED_CHECKPOINT_STATES.index(_clean_text(checkpoint_state))
	except ValueError:
		return -1


def _safe_int(value: Any, *, default: int = 0) -> Dict[str, Any]:
	if value is None or value == "":
		return {"value": default, "valid": True}
	try:
		return {"value": int(value), "valid": True}
	except (TypeError, ValueError):
		return {"value": default, "valid": False}


def _infer_checkpoint(result: Dict[str, Any]) -> str:
	checkpoint = _clean_text(result.get("checkpoint_state"))
	if checkpoint:
		return checkpoint
	if _raw_trace_text(result):
		return CHECKPOINT_TRACE_CAPTURED
	if _raw_answer_text(result):
		return CHECKPOINT_ANSWER_CAPTURED
	if _clean_text(result.get("browser_session_id")):
		return CHECKPOINT_SESSION_STARTED
	return CHECKPOINT_QUEUED


def _raw_answer_text(result: Dict[str, Any]) -> str:
	return _clean_text(result.get("raw_answer_text")) or _clean_text(result.get("answer_text"))


def _raw_trace_text(result: Dict[str, Any]) -> str:
	return _clean_text(result.get("raw_trace_text")) or _clean_text(result.get("trace_text"))


def _answer_capture_state(result: Dict[str, Any]) -> str:
	return "captured" if _raw_answer_text(result) else "missing"


def _trace_capture_state(result: Dict[str, Any]) -> str:
	return "captured" if _raw_trace_text(result) else "missing"


def _resume_from_checkpoint(blocking_reasons: List[str], checkpoint_state: str) -> str:
	reasons = set(blocking_reasons)
	if "capture_result_missing" in reasons:
		return CHECKPOINT_QUEUED
	if "missing_answer_text" in reasons:
		return CHECKPOINT_PROMPTS_SENT
	if "missing_trace_text" in reasons or reasons.intersection(TIMEOUT_REASON_CODES):
		return checkpoint_state if checkpoint_state in REQUIRED_CHECKPOINT_STATES else CHECKPOINT_ANSWER_CAPTURED
	if "cleanup_not_confirmed" in reasons:
		return CHECKPOINT_TRACE_CAPTURED
	if "stale_trace_reused" in reasons:
		return CHECKPOINT_TRACE_REQUESTED
	return checkpoint_state if checkpoint_state in REQUIRED_CHECKPOINT_STATES else CHECKPOINT_QUEUED


def _strict_import_command(*, capture_bundle_path: str, scenario_ids: List[str], reviewer: str, out_dir: str) -> str:
	if not scenario_ids:
		return "not_available_no_promotion_eligible_scenarios"
	return (
		"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
		"python3 scripts/qwen_manual_uat_operator_evidence_import.py "
		f"--captures {capture_bundle_path} "
		f"--expected-scenarios {','.join(scenario_ids)} "
		f"--reviewer {reviewer or 'operator@example.com'} "
		f"--out-dir {out_dir} "
		"--strict --overwrite"
	)


def strict_import_command_argv(*, capture_bundle_path: str, scenario_ids: List[str], reviewer: str, out_dir: str) -> List[str]:
	if not scenario_ids:
		return []
	return [
		"python3",
		"scripts/qwen_manual_uat_operator_evidence_import.py",
		"--captures",
		capture_bundle_path,
		"--expected-scenarios",
		",".join(scenario_ids),
		"--reviewer",
		reviewer or "operator@example.com",
		"--out-dir",
		out_dir,
		"--strict",
		"--overwrite",
	]


def evaluate_browser_batch_scenario(
	scenario_id: str,
	result: Dict[str, Any] | None = None,
	*,
	registry: Iterable[Dict[str, Any]] | None = None,
	expected: bool = True,
	ordinal: int = 1,
	generated_at: str = "",
	max_retries: int = 1,
) -> Dict[str, Any]:
	generated_at_text = _clean_text(generated_at) or _utc_now()
	registry_map = _scenario_registry_map(registry)
	scenario = _clean_dict(registry_map.get(_clean_text(scenario_id)))
	source = _clean_dict(result)
	blocking_reasons: List[str] = []
	if not source:
		blocking_reasons.append("capture_result_missing")
	if not expected:
		blocking_reasons.append("unexpected_scenario_capture")
	if not scenario:
		blocking_reasons.append("scenario_not_registered")
	elif not bool(scenario.get("scenario_complete")):
		blocking_reasons.append("expected_contract_missing")

	answer_text = _raw_answer_text(source)
	trace_text = _raw_trace_text(source)
	if not answer_text:
		blocking_reasons.append("missing_answer_text")
	if not trace_text:
		blocking_reasons.append("missing_trace_text")

	timeout_state = _clean_text(source.get("timeout_state")) or "none"
	if timeout_state in TIMEOUT_REASON_CODES:
		blocking_reasons.append(timeout_state)
	elif timeout_state and timeout_state not in {"none", "completed", "not_started"}:
		blocking_reasons.append("unknown_browser_state")

	checkpoint_state = _infer_checkpoint(source)
	if checkpoint_state not in REQUIRED_CHECKPOINT_STATES:
		blocking_reasons.append("checkpoint_state_unknown")

	trace_scenario_id = _clean_text(source.get("trace_scenario_id"))
	if trace_scenario_id and trace_scenario_id != _clean_text(scenario_id):
		blocking_reasons.append("stale_trace_reused")

	retry_result = _safe_int(source.get("retry_count"), default=0)
	max_retry_result = _safe_int(source.get("max_retries"), default=max_retries)
	retry_count = int(retry_result["value"])
	effective_max_retries = int(max_retry_result["value"])
	if not retry_result["valid"] or not max_retry_result["valid"]:
		blocking_reasons.append("retry_value_invalid")
	if retry_count > effective_max_retries:
		blocking_reasons.append("max_retries_exceeded")

	cleanup_state = _clean_text(source.get("cleanup_state")) or "pending"
	if cleanup_state not in ALLOWED_CLEANUP_STATES:
		blocking_reasons.append("cleanup_not_confirmed")

	blocking_reasons = sorted(set(blocking_reasons))
	promotion_eligible = not blocking_reasons
	retryable = bool(
		not promotion_eligible
		and retry_count < effective_max_retries
		and set(blocking_reasons).intersection(RETRYABLE_BROWSER_BATCH_REASON_CODES)
		and "scenario_not_registered" not in blocking_reasons
		and "unexpected_scenario_capture" not in blocking_reasons
	)
	return {
		"type": MANUAL_UAT_BROWSER_BATCH_SCENARIO_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"scenario_id": _clean_text(scenario_id),
		"ordinal": int(ordinal),
		"generated_at": generated_at_text,
		"registered": bool(scenario),
		"expected": bool(expected),
		"expected_route": _clean_text(scenario.get("expected_route")),
		"expected_artifact_family": _clean_text(scenario.get("expected_artifact_family")),
		"expected_entity_type": _clean_text(scenario.get("expected_entity_type")),
		"expected_row_reference": _clean_text(scenario.get("expected_row_reference")),
		"expected_authority_source": _clean_text(scenario.get("expected_authority_source")),
		"expected_policy_boundary": _clean_text(scenario.get("expected_policy_boundary")),
		"expected_answer_mode": _clean_text(scenario.get("expected_answer_mode")),
		"expected_model_role_lane": _clean_text(scenario.get("expected_model_role_lane")),
		"execution_envelope_id": _clean_text(source.get("execution_envelope_id")) or f"s7_6t:{scenario_id}:{ordinal}",
		"browser_session_id": _clean_text(source.get("browser_session_id")),
		"prompt_turn_count": int(source.get("prompt_turn_count") or len(_clean_list(scenario.get("turns")))),
		"checkpoint_state": checkpoint_state,
		"checkpoint_rank": _checkpoint_rank(checkpoint_state),
		"answer_capture_state": _answer_capture_state(source),
		"trace_capture_state": _trace_capture_state(source),
		"timeout_state": timeout_state,
		"retry_count": retry_count,
		"max_retries": effective_max_retries,
		"retryable": retryable,
		"resume_from_checkpoint": _resume_from_checkpoint(blocking_reasons, checkpoint_state),
		"cleanup_state": cleanup_state,
		"promotion_eligible": promotion_eligible,
		"scenario_status": SCENARIO_STATUS_PASSED if promotion_eligible else SCENARIO_STATUS_BLOCKED,
		"blocking_reasons": blocking_reasons,
		"raw_answer_present": bool(answer_text),
		"raw_trace_present": bool(trace_text),
		"trace_scenario_id": trace_scenario_id,
	}


def build_browser_batch_runner_contract(
	scenario_ids: Iterable[str] | None = None,
	*,
	capture_results: Iterable[Dict[str, Any]] | None = None,
	registry: Iterable[Dict[str, Any]] | None = None,
	batch_id: str = "s7_browser_batch_resilience_runner",
	generated_at: str = "",
	reviewer: str = "",
	capture_bundle_path: str = "path/to/operator_capture.json",
	out_dir: str = "impl_factory/00_governance/current_docs/generated",
	max_retries: int = 1,
	contract_owner: str = "s7_browser_batch_resilience_runner",
) -> Dict[str, Any]:
	generated_at_text = _clean_text(generated_at) or _utc_now()
	expected_ids = _dedupe(scenario_ids or _scenario_ids_from_registry(registry))
	results = _clean_records(capture_results)
	results_by_id: Dict[str, Dict[str, Any]] = {}
	duplicate_capture_ids: List[str] = []
	for result in results:
		scenario_id = _clean_text(result.get("scenario_id"))
		if scenario_id and scenario_id not in results_by_id:
			results_by_id[scenario_id] = result
		elif scenario_id:
			duplicate_capture_ids.append(scenario_id)

	scenario_contracts: List[Dict[str, Any]] = []
	for index, scenario_id in enumerate(expected_ids, start=1):
		scenario_contracts.append(
			evaluate_browser_batch_scenario(
				scenario_id,
				results_by_id.get(scenario_id),
				registry=registry,
				expected=True,
				ordinal=index,
				generated_at=generated_at_text,
				max_retries=max_retries,
			)
		)
	for result in results:
		scenario_id = _clean_text(result.get("scenario_id"))
		if scenario_id and scenario_id not in expected_ids:
			scenario_contracts.append(
				evaluate_browser_batch_scenario(
					scenario_id,
					result,
					registry=registry,
					expected=False,
					ordinal=len(scenario_contracts) + 1,
					generated_at=generated_at_text,
					max_retries=max_retries,
				)
			)
	for duplicate_id in sorted(set(duplicate_capture_ids)):
		scenario_contracts.append(
			{
				"type": MANUAL_UAT_BROWSER_BATCH_SCENARIO_CONTRACT_TYPE,
				"contract_version": CONTRACT_VERSION,
				"scenario_id": duplicate_id,
				"ordinal": len(scenario_contracts) + 1,
				"generated_at": generated_at_text,
				"registered": duplicate_id in _scenario_registry_map(registry),
				"expected": duplicate_id in expected_ids,
				"execution_envelope_id": f"s7_6t:duplicate:{duplicate_id}",
				"browser_session_id": "",
				"prompt_turn_count": 0,
				"checkpoint_state": CHECKPOINT_QUEUED,
				"checkpoint_rank": _checkpoint_rank(CHECKPOINT_QUEUED),
				"answer_capture_state": "missing",
				"trace_capture_state": "missing",
				"timeout_state": "none",
				"retry_count": 0,
				"max_retries": int(max_retries),
				"retryable": False,
				"resume_from_checkpoint": CHECKPOINT_QUEUED,
				"cleanup_state": "pending",
				"promotion_eligible": False,
				"scenario_status": SCENARIO_STATUS_BLOCKED,
				"blocking_reasons": ["duplicate_capture_result"],
				"raw_answer_present": False,
				"raw_trace_present": False,
				"trace_scenario_id": "",
			}
		)

	promotion_eligible_ids = [
		_clean_text(entry.get("scenario_id"))
		for entry in scenario_contracts
		if bool(entry.get("promotion_eligible")) and bool(entry.get("expected"))
	]
	blocked_ids = [
		_clean_text(entry.get("scenario_id"))
		for entry in scenario_contracts
		if not bool(entry.get("promotion_eligible"))
	]
	retryable_ids = [
		_clean_text(entry.get("scenario_id"))
		for entry in scenario_contracts
		if bool(entry.get("retryable"))
	]
	failure_reason_codes = sorted(
		{
			reason
			for entry in scenario_contracts
			for reason in _clean_list(entry.get("blocking_reasons"))
		}
	)
	supported_reason_codes = list(REQUIRED_BROWSER_BATCH_REASON_CODES)
	missing_reason_codes = [
		code
		for code in REQUIRED_BROWSER_BATCH_REASON_CODES
		if code not in supported_reason_codes
	]
	release_ready = bool(expected_ids and len(promotion_eligible_ids) == len(expected_ids) and not blocked_ids)
	batch_status = (
		BROWSER_BATCH_STATUS_RELEASE_READY
		if release_ready
		else BROWSER_BATCH_STATUS_PARTIAL_BLOCKED
		if promotion_eligible_ids
		else BROWSER_BATCH_STATUS_BLOCKED
	)
	return {
		"type": MANUAL_UAT_BROWSER_BATCH_RUNNER_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"contract_owner": _clean_text(contract_owner),
		"linked_regression_suite_id": MANUAL_UAT_BROWSER_BATCH_RUNNER_SUITE_ID,
		"batch_id": _clean_text(batch_id),
		"generated_at": generated_at_text,
		"reviewer": _clean_text(reviewer),
		"batch_status": batch_status,
		"release_ready": release_ready,
		"batch_runner_complete": True,
		"partial_capture_safe": all(
			not bool(entry.get("promotion_eligible")) or not _clean_list(entry.get("blocking_reasons"))
			for entry in scenario_contracts
		),
		"expected_scenario_ids": expected_ids,
		"expected_scenario_count": len(expected_ids),
		"observed_capture_count": len(results),
		"scenario_count": len(scenario_contracts),
		"promotion_eligible_scenario_ids": promotion_eligible_ids,
		"strict_import_expected_scenario_ids": promotion_eligible_ids,
		"blocked_scenario_ids": blocked_ids,
		"excluded_from_promotion_scenario_ids": blocked_ids,
		"retryable_scenario_ids": retryable_ids,
		"resume_required": bool(retryable_ids),
		"failure_reason_codes": failure_reason_codes,
		"supported_reason_codes": supported_reason_codes,
		"required_reason_codes": list(REQUIRED_BROWSER_BATCH_REASON_CODES),
		"missing_reason_codes": missing_reason_codes,
		"required_checkpoint_states": list(REQUIRED_CHECKPOINT_STATES),
		"allowed_cleanup_states": list(ALLOWED_CLEANUP_STATES),
		"forbidden_actions": list(FORBIDDEN_BROWSER_BATCH_ACTIONS),
		"scenario_contracts": scenario_contracts,
		"strict_import_command": _strict_import_command(
			capture_bundle_path=capture_bundle_path,
			scenario_ids=promotion_eligible_ids,
			reviewer=_clean_text(reviewer),
			out_dir=out_dir,
		),
		"strict_import_command_argv": strict_import_command_argv(
			capture_bundle_path=capture_bundle_path,
			scenario_ids=promotion_eligible_ids,
			reviewer=_clean_text(reviewer),
			out_dir=out_dir,
		),
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


def render_browser_batch_runner_markdown(contract: Dict[str, Any]) -> str:
	source = _clean_dict(contract)
	lines: List[str] = ["# S7 Browser Batch Resilience Runner Contract", ""]
	lines.extend(["## Batch Summary", ""])
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	for field in [
		"batch_id",
		"generated_at",
		"reviewer",
		"batch_status",
		"release_ready",
		"partial_capture_safe",
		"resume_required",
		"expected_scenario_count",
		"observed_capture_count",
		"scenario_count",
	]:
		lines.append(f"| {_md_cell(field)} | {_md_cell(source.get(field))} |")
	lines.extend(["", "## Promotion Boundary", ""])
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	lines.append(f"| Promotion eligible scenarios | {_md_cell(_join(source.get('promotion_eligible_scenario_ids')))} |")
	lines.append(f"| Strict import expected scenarios | {_md_cell(_join(source.get('strict_import_expected_scenario_ids')))} |")
	lines.append(f"| Excluded from promotion | {_md_cell(_join(source.get('excluded_from_promotion_scenario_ids')))} |")
	lines.append(f"| Retryable scenarios | {_md_cell(_join(source.get('retryable_scenario_ids')))} |")
	lines.append(f"| Failure reason codes | {_md_cell(_join(source.get('failure_reason_codes')))} |")
	lines.extend(["", "## Scenario Contracts", ""])
	lines.append("| Scenario | Status | Promotion eligible | Checkpoint | Resume from | Timeout | Cleanup | Blocking reasons |")
	lines.append("|---|---|---|---|---|---|---|---|")
	for entry in source.get("scenario_contracts") or []:
		if not isinstance(entry, dict):
			continue
		lines.append(
			"| "
			+ " | ".join(
				[
					_md_cell(entry.get("scenario_id")),
					_md_cell(entry.get("scenario_status")),
					_md_cell(entry.get("promotion_eligible")),
					_md_cell(entry.get("checkpoint_state")),
					_md_cell(entry.get("resume_from_checkpoint")),
					_md_cell(entry.get("timeout_state")),
					_md_cell(entry.get("cleanup_state")),
					_md_cell(_join(entry.get("blocking_reasons"))),
				]
			)
			+ " |"
		)
	lines.extend(["", "## Checkpoint States", ""])
	for state in _clean_list(source.get("required_checkpoint_states")):
		lines.append(f"- {state}")
	lines.extend(["", "## Forbidden Actions", ""])
	for action in _clean_list(source.get("forbidden_actions")):
		lines.append(f"- {action}")
	lines.extend(["", "## Strict Import Command", ""])
	lines.append(f"`{_md_cell(source.get('strict_import_command'))}`")
	return "\n".join(lines).strip() + "\n"


def _write_text(path: str, text: str) -> None:
	target = Path(path)
	if not target.is_absolute():
		target = Path.cwd() / target
	target.parent.mkdir(parents=True, exist_ok=True)
	target.write_text(text, encoding="utf-8")


def _write_json(path: str, payload: Dict[str, Any]) -> None:
	_write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_browser_batch_runner_files(
	scenario_ids: Iterable[str] | None = None,
	*,
	capture_results: Iterable[Dict[str, Any]] | None = None,
	registry: Iterable[Dict[str, Any]] | None = None,
	json_path: str = DEFAULT_BROWSER_BATCH_RUNNER_JSON_PATH,
	markdown_path: str = DEFAULT_BROWSER_BATCH_RUNNER_MARKDOWN_PATH,
	batch_id: str = "s7_browser_batch_resilience_runner",
	generated_at: str = "",
	reviewer: str = "",
	capture_bundle_path: str = "path/to/operator_capture.json",
	out_dir: str = "impl_factory/00_governance/current_docs/generated",
	max_retries: int = 1,
) -> Dict[str, Any]:
	contract = build_browser_batch_runner_contract(
		scenario_ids,
		capture_results=capture_results,
		registry=registry,
		batch_id=batch_id,
		generated_at=generated_at,
		reviewer=reviewer,
		capture_bundle_path=capture_bundle_path,
		out_dir=out_dir,
		max_retries=max_retries,
	)
	_write_json(json_path, contract)
	_write_text(markdown_path, render_browser_batch_runner_markdown(contract))
	contract["json_artifact_path"] = str(Path(json_path))
	contract["markdown_artifact_path"] = str(Path(markdown_path))
	contract["json_artifact_written"] = True
	contract["markdown_artifact_written"] = True
	return contract
