from __future__ import annotations

import signal
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Sequence


SmokeRunner = Callable[[], Dict[str, Any]]


class BoundedSmokeTimeoutError(TimeoutError):
	"""Raised when a bounded smoke exceeds its per-case budget."""


@dataclass(frozen=True)
class BoundedSmokeCase:
	case_id: str
	label: str
	group: str
	runner: SmokeRunner
	timeout_seconds: float = 120.0
	critical: bool = True


_PROFILE_CASE_IDS: Dict[str, List[str]] = {
	"stabilization_fast": [
		"phase1_1_invoice_delivery_proof",
		"phase1_1_fresh_chat_invoice_delivery_proof",
		"phase1_2_sales_order_status_followup",
		"phase1_3_purchase_order_status_followup",
		"nbu_governed_requery",
	],
	"nbu_s7_regression_matrix": [
		"nbu_s7_same_session_fresh_query",
		"nbu_s7_visible_context_latest_artifact",
		"nbu_governed_requery",
		"nbu_s7_subject_switch",
		"nbu_s7_ranking_projection_continuation",
		"nbu_s7_product_quantity_projection",
		"nbu_s7_safe_boundary_language",
		"phase8_fresh_query_override",
		"phase8_recovery_execution",
		"h4_recommendation_guarantee",
	],
	"nbu_s7_context_matrix": [
		"nbu_s7_same_session_fresh_query",
		"nbu_s7_visible_context_latest_artifact",
		"nbu_governed_requery",
	],
	"nbu_s7_projection_matrix": [
		"nbu_s7_subject_switch",
		"nbu_s7_ranking_projection_continuation",
		"nbu_s7_product_quantity_projection",
	],
	"nbu_s7_boundary_recovery_matrix": [
		"nbu_s7_safe_boundary_language",
		"phase8_fresh_query_override",
		"phase8_recovery_execution",
		"h4_recommendation_guarantee",
	],
	"nbu_s7_same_session_fresh_query": [
		"nbu_s7_same_session_fresh_query",
	],
	"nbu_s7_visible_context_latest_artifact": [
		"nbu_s7_visible_context_latest_artifact",
	],
	"nbu_s7_subject_switch": [
		"nbu_s7_subject_switch",
	],
	"nbu_s7_ranking_projection_continuation": [
		"nbu_s7_ranking_projection_continuation",
	],
	"nbu_s7_product_quantity_projection": [
		"nbu_s7_product_quantity_projection",
	],
	"nbu_s7_safe_boundary_language": [
		"nbu_s7_safe_boundary_language",
	],
	"phase1_core": [
		"phase1_1_delivery_note_detail",
		"phase1_1_invoice_delivery_proof",
		"phase1_1_fresh_chat_invoice_delivery_proof",
		"phase1_2_sales_order_status_followup",
		"phase1_3_purchase_order_detail",
		"phase1_3_purchase_order_status_followup",
		"phase1_4_customer_credit_exposure",
		"phase1_4_customer_credit_scope_reset",
		"phase1_4_customer_credit_detail_followup",
		"phase1_4_customer_credit_policy_followup",
	],
	"phase1_document_detail": [
		"phase1_1_delivery_note_detail",
		"phase1_1_invoice_delivery_proof",
		"phase1_1_fresh_chat_invoice_delivery_proof",
	],
	"phase1_order_followup": [
		"phase1_2_sales_order_status_followup",
		"phase1_3_purchase_order_detail",
		"phase1_3_purchase_order_status_followup",
	],
	"phase1_customer_credit": [
		"phase1_4_customer_credit_exposure",
		"phase1_4_customer_credit_scope_reset",
		"phase1_4_customer_credit_detail_followup",
		"phase1_4_customer_credit_policy_followup",
	],
	"release_sanity": [
		"h5_release_gate_rollout_probe",
		"phase55_frontdoor_boundary",
		"phase6_reasoning_live_debug",
		"phase7d_boundary_response_live",
		"phase8_recovery_execution",
		"h4_recommendation_guarantee",
	],
	"post_contract_suites": [
		"phase55_hardening_suite",
		"phase6_hardening_suite",
		"phase7_hardening_suite",
		"phase8_hardening_suite",
	],
	"post_contract_phase55": [
		"phase55_hardening_suite",
	],
	"post_contract_phase6": [
		"phase6_recommendation_policy_probe",
		"phase6_reasoning_live_rollout",
		"phase6_reasoning_without_grounding",
		"phase6_reasoning_frontdoor_boundary",
		"phase6_nonadvisory_recommendation_boundary",
		"phase6_artifact_refinement_precedence",
		"phase6_continuation_fulfillment",
		"phase6_grounded_source_reset",
		"phase6_continuation_guardrail",
		"phase6_observability",
	],
	"post_contract_phase6_aggregate": [
		"phase6_hardening_suite",
	],
	"post_contract_phase6_recommendation_policy": [
		"phase6_recommendation_policy_probe",
	],
	"post_contract_phase6_reasoning_live_rollout": [
		"phase6_reasoning_live_rollout",
	],
	"post_contract_phase6_reasoning_without_grounding": [
		"phase6_reasoning_without_grounding",
	],
	"post_contract_phase6_reasoning_frontdoor_boundary": [
		"phase6_reasoning_frontdoor_boundary",
	],
	"post_contract_phase6_nonadvisory_recommendation_boundary": [
		"phase6_nonadvisory_recommendation_boundary",
	],
	"post_contract_phase6_artifact_refinement_precedence": [
		"phase6_artifact_refinement_precedence",
	],
	"post_contract_phase6_continuation_fulfillment": [
		"phase6_continuation_fulfillment",
	],
	"post_contract_phase6_grounded_source_reset": [
		"phase6_grounded_source_reset",
	],
	"post_contract_phase6_continuation_guardrail": [
		"phase6_continuation_guardrail",
	],
	"post_contract_phase6_observability": [
		"phase6_observability",
	],
	"post_contract_phase7": [
		"phase7_live_boundary_orchestration",
		"phase7_boundary_response_live",
	],
	"post_contract_phase7_aggregate": [
		"phase7_hardening_suite",
	],
	"post_contract_phase7_live_boundary_orchestration": [
		"phase7_live_boundary_orchestration",
	],
	"post_contract_phase7_boundary_response_live": [
		"phase7_boundary_response_live",
	],
	"post_contract_phase8": [
		"phase8_recovery_authority",
		"phase8_repair_handling",
		"phase8_fresh_query_override",
		"phase8_recovery_execution",
	],
	"post_contract_phase8_aggregate": [
		"phase8_hardening_suite",
	],
	"post_contract_phase8_recovery_authority": [
		"phase8_recovery_authority",
	],
	"post_contract_phase8_repair_handling": [
		"phase8_repair_handling",
	],
	"post_contract_phase8_fresh_query_override": [
		"phase8_fresh_query_override",
	],
	"post_contract_phase8_recovery_execution": [
		"phase8_recovery_execution",
	],
}


_CASE_DEFINITIONS: Dict[str, Dict[str, Any]] = {
	"phase1_1_delivery_note_detail": {
		"label": "Phase 1.1 Delivery Note Detail",
		"group": "phase1_document_detail",
		"timeout_seconds": 180.0,
	},
	"phase1_1_invoice_delivery_proof": {
		"label": "Phase 1.1 Invoice Delivery Proof",
		"group": "phase1_document_detail",
		"timeout_seconds": 180.0,
	},
	"phase1_1_fresh_chat_invoice_delivery_proof": {
		"label": "Phase 1.1 Fresh Chat Invoice Delivery Proof",
		"group": "phase1_document_detail",
		"timeout_seconds": 180.0,
	},
	"phase1_2_sales_order_status_followup": {
		"label": "Phase 1.2 Sales Order Status Follow-Up",
		"group": "phase1_order_followup",
		"timeout_seconds": 180.0,
	},
	"phase1_3_purchase_order_detail": {
		"label": "Phase 1.3 Purchase Order Detail",
		"group": "phase1_order_followup",
		"timeout_seconds": 180.0,
	},
	"phase1_3_purchase_order_status_followup": {
		"label": "Phase 1.3 Purchase Order Status Follow-Up",
		"group": "phase1_order_followup",
		"timeout_seconds": 180.0,
	},
	"phase1_4_customer_credit_exposure": {
		"label": "Phase 1.4 Customer Credit Exposure",
		"group": "phase1_customer_credit",
		"timeout_seconds": 180.0,
	},
	"phase1_4_customer_credit_scope_reset": {
		"label": "Phase 1.4 Customer Credit Scope Reset",
		"group": "phase1_customer_credit",
		"timeout_seconds": 180.0,
	},
	"phase1_4_customer_credit_detail_followup": {
		"label": "Phase 1.4 Customer Credit Detail Follow-Up",
		"group": "phase1_customer_credit",
		"timeout_seconds": 180.0,
	},
	"phase1_4_customer_credit_policy_followup": {
		"label": "Phase 1.4 Customer Credit Policy Follow-Up",
		"group": "phase1_customer_credit",
		"timeout_seconds": 180.0,
	},
	"nbu_governed_requery": {
		"label": "NBU Governed Requery",
		"group": "nbu_context_authority",
		"timeout_seconds": 180.0,
	},
	"nbu_s7_same_session_fresh_query": {
		"label": "NBU-S7 Same-Session Fresh Query Reset",
		"group": "nbu_s7_context_matrix",
		"timeout_seconds": 300.0,
	},
	"nbu_s7_visible_context_latest_artifact": {
		"label": "NBU-S7 Visible Context Latest Artifact",
		"group": "nbu_s7_context_matrix",
		"timeout_seconds": 240.0,
	},
	"nbu_s7_subject_switch": {
		"label": "NBU-S7 Subject Switch",
		"group": "nbu_s7_projection_matrix",
		"timeout_seconds": 300.0,
	},
	"nbu_s7_ranking_projection_continuation": {
		"label": "NBU-S7 Ranking Projection Continuation",
		"group": "nbu_s7_projection_matrix",
		"timeout_seconds": 420.0,
	},
	"nbu_s7_product_quantity_projection": {
		"label": "NBU-S7 Product Quantity Projection",
		"group": "nbu_s7_projection_matrix",
		"timeout_seconds": 420.0,
	},
	"nbu_s7_safe_boundary_language": {
		"label": "NBU-S7 Safe Boundary Language",
		"group": "nbu_s7_boundary_recovery_matrix",
		"timeout_seconds": 240.0,
	},
	"h5_release_gate_rollout_probe": {
		"label": "H5 Release Gate Rollout Probe",
		"group": "release_sanity",
		"timeout_seconds": 60.0,
	},
	"phase55_frontdoor_boundary": {
		"label": "Phase 5.5 Frontdoor Boundary",
		"group": "release_sanity",
		"timeout_seconds": 120.0,
	},
	"phase6_reasoning_live_debug": {
		"label": "Phase 6 Reasoning Live Debug",
		"group": "release_sanity",
		"timeout_seconds": 180.0,
	},
	"phase7d_boundary_response_live": {
		"label": "Phase 7D Boundary Response Live",
		"group": "release_sanity",
		"timeout_seconds": 180.0,
	},
	"phase8_recovery_execution": {
		"label": "Phase 8 Recovery Execution",
		"group": "release_sanity",
		"timeout_seconds": 180.0,
	},
	"h4_recommendation_guarantee": {
		"label": "H4 Recommendation Guarantee Boundary",
		"group": "release_sanity",
		"timeout_seconds": 180.0,
	},
	"phase55_hardening_suite": {
		"label": "Phase 5.5 Hardening Suite",
		"group": "post_contract_phase55",
		"timeout_seconds": 300.0,
	},
	"phase6_recommendation_policy_probe": {
		"label": "Phase 6 Recommendation Policy Probe",
		"group": "post_contract_phase6",
		"timeout_seconds": 60.0,
	},
	"phase6_reasoning_live_rollout": {
		"label": "Phase 6 Reasoning Live Rollout",
		"group": "post_contract_phase6",
		"timeout_seconds": 180.0,
	},
	"phase6_reasoning_without_grounding": {
		"label": "Phase 6 Reasoning Without Grounding",
		"group": "post_contract_phase6",
		"timeout_seconds": 90.0,
	},
	"phase6_reasoning_frontdoor_boundary": {
		"label": "Phase 6 Reasoning Front-Door Boundary",
		"group": "post_contract_phase6",
		"timeout_seconds": 180.0,
	},
	"phase6_nonadvisory_recommendation_boundary": {
		"label": "Phase 6 Non-Advisory Recommendation Boundary",
		"group": "post_contract_phase6",
		"timeout_seconds": 180.0,
	},
	"phase6_artifact_refinement_precedence": {
		"label": "Phase 6 Artifact Refinement Precedence",
		"group": "post_contract_phase6",
		"timeout_seconds": 180.0,
	},
	"phase6_continuation_fulfillment": {
		"label": "Phase 6 Continuation Fulfillment",
		"group": "post_contract_phase6",
		"timeout_seconds": 180.0,
	},
	"phase6_grounded_source_reset": {
		"label": "Phase 6 Grounded Source Reset",
		"group": "post_contract_phase6",
		"timeout_seconds": 240.0,
	},
	"phase6_continuation_guardrail": {
		"label": "Phase 6 Continuation Guardrail",
		"group": "post_contract_phase6",
		"timeout_seconds": 60.0,
	},
	"phase6_observability": {
		"label": "Phase 6 Observability",
		"group": "post_contract_phase6",
		"timeout_seconds": 180.0,
	},
	"phase6_hardening_suite": {
		"label": "Phase 6 Hardening Suite",
		"group": "post_contract_phase6_aggregate",
		"timeout_seconds": 1200.0,
	},
	"phase7_hardening_suite": {
		"label": "Phase 7 Hardening Suite",
		"group": "post_contract_phase7_aggregate",
		"timeout_seconds": 600.0,
	},
	"phase7_live_boundary_orchestration": {
		"label": "Phase 7 Live Boundary Orchestration",
		"group": "post_contract_phase7",
		"timeout_seconds": 300.0,
	},
	"phase7_boundary_response_live": {
		"label": "Phase 7 Boundary Response Live",
		"group": "post_contract_phase7",
		"timeout_seconds": 180.0,
	},
	"phase8_recovery_authority": {
		"label": "Phase 8 Recovery Authority",
		"group": "post_contract_phase8",
		"timeout_seconds": 90.0,
	},
	"phase8_repair_handling": {
		"label": "Phase 8 Repair Handling",
		"group": "post_contract_phase8",
		"timeout_seconds": 240.0,
	},
	"phase8_fresh_query_override": {
		"label": "Phase 8 Fresh Query Override",
		"group": "post_contract_phase8",
		"timeout_seconds": 180.0,
	},
	"phase8_recovery_execution": {
		"label": "Phase 8 Recovery Execution",
		"group": "post_contract_phase8",
		"timeout_seconds": 240.0,
	},
	"phase8_hardening_suite": {
		"label": "Phase 8 Hardening Suite",
		"group": "post_contract_phase8_aggregate",
		"timeout_seconds": 900.0,
	},
}


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _coerce_bool(value: Any, *, default: bool) -> bool:
	if isinstance(value, bool):
		return value
	text = _clean_text(value).lower()
	if text in {"1", "true"}:
		return True
	if text in {"0", "false"}:
		return False
	return default


def _coerce_timeout(value: Any, *, default: float) -> float:
	try:
		number = float(value)
	except Exception:
		return float(default)
	if number <= 0:
		return float(default)
	return number


def _signal_timeout_supported() -> bool:
	return (
		hasattr(signal, "SIGALRM")
		and hasattr(signal, "setitimer")
		and threading.current_thread() is threading.main_thread()
	)


class _SignalTimeout:
	def __init__(self, seconds: float):
		self.seconds = max(0.0, float(seconds or 0.0))
		self._previous_handler: Any = None
		self._previous_timer: tuple[float, float] = (0.0, 0.0)
		self.enforced = False

	def __enter__(self):
		if self.seconds <= 0 or not _signal_timeout_supported():
			return self
		self.enforced = True
		self._previous_handler = signal.getsignal(signal.SIGALRM)
		self._previous_timer = signal.getitimer(signal.ITIMER_REAL)
		signal.signal(signal.SIGALRM, self._handle_timeout)
		signal.setitimer(signal.ITIMER_REAL, self.seconds)
		return self

	def __exit__(self, exc_type, exc, tb):
		if not self.enforced:
			return False
		signal.setitimer(signal.ITIMER_REAL, 0.0)
		signal.signal(signal.SIGALRM, self._previous_handler)
		previous_delay, previous_interval = self._previous_timer
		if previous_delay > 0:
			signal.setitimer(signal.ITIMER_REAL, previous_delay, previous_interval)
		return False

	def _handle_timeout(self, _signum, _frame):
		raise BoundedSmokeTimeoutError(f"Smoke exceeded {self.seconds:.1f}s timeout")


def _summarize_value(value: Any, *, depth: int = 0) -> Any:
	if depth >= 3:
		return _clean_text(value)[:240]
	if isinstance(value, dict):
		summary: Dict[str, Any] = {}
		for index, (key, item) in enumerate(value.items()):
			if index >= 24:
				summary["..."] = "truncated"
				break
			summary[_clean_text(key)[:80]] = _summarize_value(item, depth=depth + 1)
		return summary
	if isinstance(value, (list, tuple)):
		items = list(value)
		return [_summarize_value(item, depth=depth + 1) for item in items[:12]]
	if isinstance(value, str):
		return value[:500]
	return value


def _status_counts(results: Sequence[Dict[str, Any]]) -> Dict[str, int]:
	return {
		"passed": sum(1 for result in results if result.get("status") == "passed"),
		"failed": sum(1 for result in results if result.get("status") == "failed"),
		"timed_out": sum(1 for result in results if result.get("status") == "timeout"),
		"skipped": sum(1 for result in results if result.get("status") == "skipped"),
	}


def build_bounded_release_gate_cases(
	*,
	registry: Dict[str, SmokeRunner],
	profile: str = "stabilization_fast",
	timeout_seconds: Any = None,
) -> List[BoundedSmokeCase]:
	clean_profile = _clean_text(profile) or "stabilization_fast"
	case_ids = _PROFILE_CASE_IDS.get(clean_profile)
	if case_ids is None:
		available = ", ".join(sorted(_PROFILE_CASE_IDS))
		raise ValueError(f"Unknown bounded release-gate profile `{clean_profile}`. Available profiles: {available}.")
	cases: List[BoundedSmokeCase] = []
	for case_id in case_ids:
		runner = registry.get(case_id)
		if runner is None:
			raise ValueError(f"Bounded release-gate registry is missing smoke `{case_id}` for profile `{clean_profile}`.")
		definition = _CASE_DEFINITIONS.get(case_id, {})
		default_timeout = float(definition.get("timeout_seconds") or 120.0)
		cases.append(
			BoundedSmokeCase(
				case_id=case_id,
				label=_clean_text(definition.get("label")) or case_id,
				group=_clean_text(definition.get("group")) or "ungrouped",
				runner=runner,
				timeout_seconds=_coerce_timeout(timeout_seconds, default=default_timeout) if timeout_seconds is not None else default_timeout,
				critical=bool(definition.get("critical", True)),
			)
		)
	return cases


def bounded_release_gate_inventory() -> Dict[str, Any]:
	profiles: Dict[str, Any] = {}
	for profile, case_ids in _PROFILE_CASE_IDS.items():
		profiles[profile] = [
			{
				"case_id": case_id,
				"label": _clean_text(_CASE_DEFINITIONS.get(case_id, {}).get("label")) or case_id,
				"group": _clean_text(_CASE_DEFINITIONS.get(case_id, {}).get("group")) or "ungrouped",
				"timeout_seconds": float(_CASE_DEFINITIONS.get(case_id, {}).get("timeout_seconds") or 120.0),
			}
			for case_id in case_ids
		]
	return {
		"ok": True,
		"profiles": profiles,
		"profile_timeout_budget_seconds": {
			profile: sum(float(_CASE_DEFINITIONS.get(case_id, {}).get("timeout_seconds") or 120.0) for case_id in case_ids)
			for profile, case_ids in _PROFILE_CASE_IDS.items()
		},
		"default_profile": "stabilization_fast",
		"timeout_enforcement": "signal" if _signal_timeout_supported() else "best_effort_no_signal",
	}


def run_bounded_smoke_cases(
	*,
	cases: Iterable[BoundedSmokeCase],
	profile: str,
	fail_fast: Any = True,
) -> Dict[str, Any]:
	started = time.perf_counter()
	should_fail_fast = _coerce_bool(fail_fast, default=True)
	planned_cases = list(cases)
	results: List[Dict[str, Any]] = []
	timeout_enforcement = "signal" if _signal_timeout_supported() else "best_effort_no_signal"
	for case in planned_cases:
		case_started = time.perf_counter()
		result: Dict[str, Any] = {
			"case_id": case.case_id,
			"label": case.label,
			"group": case.group,
			"critical": bool(case.critical),
			"timeout_seconds": float(case.timeout_seconds),
			"timeout_enforcement": timeout_enforcement,
		}
		try:
			with _SignalTimeout(case.timeout_seconds):
				payload = case.runner()
			case_duration = round(time.perf_counter() - case_started, 3)
			if isinstance(payload, dict) and payload.get("ok") is False:
				result.update(
					{
						"status": "failed",
						"duration_seconds": case_duration,
						"error_type": "SmokeReturnedNotOk",
						"error_message": _clean_text(payload.get("error") or payload.get("message") or "Smoke returned ok=false."),
						"payload_excerpt": _summarize_value(payload),
					}
				)
			else:
				result.update(
					{
						"status": "passed",
						"duration_seconds": case_duration,
						"payload_excerpt": _summarize_value(payload),
					}
				)
		except BoundedSmokeTimeoutError as exc:
			result.update(
				{
					"status": "timeout",
					"duration_seconds": round(time.perf_counter() - case_started, 3),
					"error_type": exc.__class__.__name__,
					"error_message": str(exc),
				}
			)
		except Exception as exc:
			result.update(
				{
					"status": "failed",
					"duration_seconds": round(time.perf_counter() - case_started, 3),
					"error_type": exc.__class__.__name__,
					"error_message": str(exc)[:1000],
				}
			)
		results.append(result)
		if should_fail_fast and result.get("status") != "passed":
			break
	counts = _status_counts(results)
	first_failure = next((result for result in results if result.get("status") != "passed"), None)
	return {
		"ok": first_failure is None,
		"profile": _clean_text(profile) or "stabilization_fast",
		"fail_fast": should_fail_fast,
		"timeout_enforcement": timeout_enforcement,
		"profile_timeout_budget_seconds": sum(float(case.timeout_seconds) for case in planned_cases),
		"duration_seconds": round(time.perf_counter() - started, 3),
		"total_planned": len(planned_cases),
		"total_run": len(results),
		**counts,
		"first_failure": first_failure or {},
		"results": results,
		"next_action": (
			"Profile passed. Continue with the next bounded profile or manual UAT gate."
			if first_failure is None
			else "Fix the first failing shared seam, rerun guardrails, then rerun this bounded profile."
		),
	}


def run_bounded_release_gate(
	*,
	registry: Dict[str, SmokeRunner],
	profile: str = "stabilization_fast",
	fail_fast: Any = True,
	timeout_seconds: Any = None,
) -> Dict[str, Any]:
	cases = build_bounded_release_gate_cases(
		registry=registry,
		profile=profile,
		timeout_seconds=timeout_seconds,
	)
	return run_bounded_smoke_cases(
		cases=cases,
		profile=profile,
		fail_fast=fail_fast,
	)
