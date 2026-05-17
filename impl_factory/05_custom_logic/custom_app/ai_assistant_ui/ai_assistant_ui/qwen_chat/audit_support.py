from __future__ import annotations

from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.metadata import get_family_latency_budget_spec


def audit_latency_summary(values: List[int]) -> Dict[str, int]:
	clean = sorted(int(max(0, value or 0)) for value in values if int(max(0, value or 0)) > 0)
	if not clean:
		return {"count": 0, "avg_ms": 0, "p95_ms": 0, "max_ms": 0}
	index = max(0, min(len(clean) - 1, int((len(clean) - 1) * 0.95)))
	return {
		"count": len(clean),
		"avg_ms": int(round(sum(clean) / float(len(clean)))),
		"p95_ms": int(clean[index]),
		"max_ms": int(clean[-1]),
	}


def family_latency_budget_payload(family_id: str) -> Dict[str, Any]:
	spec = get_family_latency_budget_spec(family_id)
	if not spec:
		return {}
	return {
		"family_id": str(spec.get("family_id") or "").strip(),
		"proposal_generation_development_budget_ms": int(
			max(0, spec.get("proposal_generation_development_budget_ms") or 0)
		),
		"runtime_execution_development_budget_ms": int(
			max(0, spec.get("runtime_execution_development_budget_ms") or 0)
		),
		"total_pipeline_development_budget_ms": int(
			max(0, spec.get("total_pipeline_development_budget_ms") or 0)
		),
		"total_pipeline_enterprise_target_ms": int(
			max(0, spec.get("total_pipeline_enterprise_target_ms") or 0)
		),
		"notes": str(spec.get("notes") or "").strip(),
	}


def case_latency_budget_assessment(
	*,
	family_id: str,
	proposal_generation_latency_ms: int,
	runtime_execution_latency_ms: int,
	total_pipeline_latency_ms: int,
) -> Dict[str, Any]:
	budget = family_latency_budget_payload(family_id)
	if not budget:
		return {}

	proposal_budget_ms = int(budget.get("proposal_generation_development_budget_ms") or 0)
	runtime_budget_ms = int(budget.get("runtime_execution_development_budget_ms") or 0)
	total_development_budget_ms = int(budget.get("total_pipeline_development_budget_ms") or 0)
	total_enterprise_target_ms = int(budget.get("total_pipeline_enterprise_target_ms") or 0)
	within_proposal_budget = proposal_budget_ms <= 0 or proposal_generation_latency_ms <= proposal_budget_ms
	within_runtime_budget = runtime_budget_ms <= 0 or runtime_execution_latency_ms <= runtime_budget_ms
	within_development_budget = total_development_budget_ms <= 0 or total_pipeline_latency_ms <= total_development_budget_ms
	within_enterprise_target = total_enterprise_target_ms > 0 and total_pipeline_latency_ms <= total_enterprise_target_ms

	status = "not_configured"
	if budget:
		if within_enterprise_target:
			status = "enterprise_green"
		elif within_development_budget and within_proposal_budget and within_runtime_budget:
			status = "development_green_enterprise_open"
		elif within_development_budget:
			status = "development_green_with_stage_overage"
		else:
			status = "over_development_budget"

	return {
		"budget": budget,
		"observed": {
			"proposal_generation_latency_ms": int(max(0, proposal_generation_latency_ms)),
			"runtime_execution_latency_ms": int(max(0, runtime_execution_latency_ms)),
			"total_pipeline_latency_ms": int(max(0, total_pipeline_latency_ms)),
		},
		"within_proposal_budget": bool(within_proposal_budget),
		"within_runtime_budget": bool(within_runtime_budget),
		"within_development_budget": bool(within_development_budget),
		"within_enterprise_target": bool(within_enterprise_target),
		"development_budget_overage_ms": int(
			max(0, total_pipeline_latency_ms - total_development_budget_ms)
		)
		if total_development_budget_ms > 0
		else 0,
		"enterprise_target_overage_ms": int(
			max(0, total_pipeline_latency_ms - total_enterprise_target_ms)
		)
		if total_enterprise_target_ms > 0
		else 0,
		"status": status,
	}


def family_latency_budget_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
	grouped: Dict[str, List[Dict[str, Any]]] = {}
	for item in results:
		if not isinstance(item, dict):
			continue
		if not bool(item.get("case_ok")):
			continue
		family_id = str(item.get("observed_family_id") or item.get("expected_family_id") or "").strip()
		if not family_id:
			continue
		grouped.setdefault(family_id, []).append(item)

	families: Dict[str, Any] = {}
	development_green_count = 0
	enterprise_green_count = 0
	for family_id, items in grouped.items():
		budget = family_latency_budget_payload(family_id)
		proposal_summary = audit_latency_summary(
			[int(item.get("proposal_generation_latency_ms") or 0) for item in items]
		)
		runtime_summary = audit_latency_summary(
			[int(item.get("runtime_execution_latency_ms") or 0) for item in items]
		)
		total_summary = audit_latency_summary(
			[int(item.get("total_pipeline_latency_ms") or 0) for item in items]
		)
		proposal_budget_ms = int(budget.get("proposal_generation_development_budget_ms") or 0)
		runtime_budget_ms = int(budget.get("runtime_execution_development_budget_ms") or 0)
		total_development_budget_ms = int(budget.get("total_pipeline_development_budget_ms") or 0)
		total_enterprise_target_ms = int(budget.get("total_pipeline_enterprise_target_ms") or 0)
		proposal_p95_ms = int(proposal_summary.get("p95_ms") or 0)
		runtime_p95_ms = int(runtime_summary.get("p95_ms") or 0)
		total_p95_ms = int(total_summary.get("p95_ms") or 0)
		within_proposal_budget = proposal_budget_ms <= 0 or proposal_p95_ms <= proposal_budget_ms
		within_runtime_budget = runtime_budget_ms <= 0 or runtime_p95_ms <= runtime_budget_ms
		within_development_budget = total_development_budget_ms <= 0 or total_p95_ms <= total_development_budget_ms
		within_enterprise_target = total_enterprise_target_ms > 0 and total_p95_ms <= total_enterprise_target_ms
		status = "not_configured"
		if budget:
			if within_enterprise_target:
				status = "enterprise_green"
			elif within_development_budget and within_proposal_budget and within_runtime_budget:
				status = "development_green_enterprise_open"
			elif within_development_budget:
				status = "development_green_with_stage_overage"
			else:
				status = "over_development_budget"
		if status in {"enterprise_green"}:
			enterprise_green_count += 1
		if status in {"enterprise_green", "development_green_enterprise_open", "development_green_with_stage_overage"}:
			development_green_count += 1
		families[family_id] = {
			"case_count": len(items),
			"budget": budget,
			"proposal_generation_latency": proposal_summary,
			"runtime_execution_latency": runtime_summary,
			"total_pipeline_latency": total_summary,
			"within_proposal_budget": bool(within_proposal_budget),
			"within_runtime_budget": bool(within_runtime_budget),
			"within_development_budget": bool(within_development_budget),
			"within_enterprise_target": bool(within_enterprise_target),
			"development_budget_overage_ms": int(max(0, total_p95_ms - total_development_budget_ms))
			if total_development_budget_ms > 0
			else 0,
			"enterprise_target_overage_ms": int(max(0, total_p95_ms - total_enterprise_target_ms))
			if total_enterprise_target_ms > 0
			else 0,
			"status": status,
			"case_ids": [str(item.get("case_id") or "").strip() for item in items if str(item.get("case_id") or "").strip()],
		}

	family_count = len(families)
	return {
		"family_count": family_count,
		"development_green_family_count": development_green_count,
		"enterprise_green_family_count": enterprise_green_count,
		"development_green_rate": 0.0 if family_count == 0 else round(development_green_count / float(family_count), 4),
		"enterprise_green_rate": 0.0 if family_count == 0 else round(enterprise_green_count / float(family_count), 4),
		"families": families,
	}


def family_metrics_summary(records: List[Dict[str, Any]], rollout_fallbacks: List[Dict[str, Any]]) -> Dict[str, Any]:
	fallback_keys = {
		(
			str(item.get("session_name") or "").strip(),
			str(item.get("request_id") or "").strip(),
		)
		for item in rollout_fallbacks
		if str(item.get("session_name") or "").strip() and str(item.get("request_id") or "").strip()
	}
	grouped: Dict[str, List[Dict[str, Any]]] = {}
	for record in records:
		family_id = str(record.get("governed_family_id") or "").strip() or "unknown"
		grouped.setdefault(family_id, []).append(record)

	out: Dict[str, Any] = {}
	for family_id, items in grouped.items():
		total = len(items)
		runtime_ok_count = sum(1 for item in items if bool(item.get("runtime_ok")))
		fallback_count = sum(
			1
			for item in items
			if (
				str(item.get("session_name") or "").strip(),
				str(item.get("request_id") or "").strip(),
			)
			in fallback_keys
		)
		out[family_id] = {
			"audit_count": total,
			"compiler_decision_counts": {
				value: sum(1 for item in items if str(item.get("compiler_decision") or "").strip() == value)
				for value in sorted(
					{
						str(item.get("compiler_decision") or "").strip() or "unknown"
						for item in items
					}
				)
			},
			"semantic_validation_status_counts": {
				value: sum(1 for item in items if str(item.get("semantic_validation_status") or "").strip() == value)
				for value in sorted(
					{
						str(item.get("semantic_validation_status") or "").strip() or "unknown"
						for item in items
					}
				)
			},
			"family_validation_status_counts": {
				value: sum(1 for item in items if str(item.get("family_validation_status") or "").strip() == value)
				for value in sorted(
					{
						str(item.get("family_validation_status") or "").strip() or "unknown"
						for item in items
					}
				)
			},
			"runtime_ok_rate": 0.0 if total == 0 else round(runtime_ok_count / float(total), 4),
			"rollout_fallback_count": fallback_count,
			"rollout_fallback_rate": 0.0 if total == 0 else round(fallback_count / float(total), 4),
			"proposal_generation_latency": audit_latency_summary(
				[int(item.get("proposal_generation_latency_ms") or 0) for item in items]
			),
			"runtime_execution_latency": audit_latency_summary(
				[int(item.get("runtime_execution_latency_ms") or 0) for item in items]
			),
			"total_pipeline_latency": audit_latency_summary(
				[int(item.get("total_pipeline_latency_ms") or 0) for item in items]
			),
		}
	return out
