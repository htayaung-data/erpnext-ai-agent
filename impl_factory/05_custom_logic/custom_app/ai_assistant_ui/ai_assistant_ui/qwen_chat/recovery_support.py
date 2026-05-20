from __future__ import annotations

from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.semantic_aliases import get_canonical_key, get_metric_label


def recovery_time_phrase(recovery_contract: Dict[str, Any]) -> str:
	time_context = recovery_contract.get("preservable_time_context") if isinstance(recovery_contract.get("preservable_time_context"), dict) else {}
	requested_time_scope = str(time_context.get("requested_time_scope") or "").strip()
	if requested_time_scope:
		return f" for {requested_time_scope.replace('_', ' ')}"
	report_date = str(time_context.get("report_date") or "").strip()
	if report_date:
		return f" as of {report_date}"
	from_date = str(time_context.get("from_date") or "").strip()
	to_date = str(time_context.get("to_date") or "").strip()
	if from_date and to_date:
		return f" from {from_date} to {to_date}"
	return ""


def dimension_query_subject(value: str) -> str:
	canonical = str(get_canonical_key(value, dimension_or_metric="dimension") or "").strip()
	if canonical in {"item", "item_name", "item_code"}:
		return "products"
	if canonical == "customer":
		return "customers"
	if canonical == "supplier":
		return "suppliers"
	if canonical == "territory":
		return "territories"
	if canonical == "warehouse":
		return "warehouses"
	clean = str(value or "").strip().lower().replace("_", " ")
	if clean.endswith(" name"):
		clean = clean[: -len(" name")].strip()
	return clean


def metric_query_phrase(value: str, capability_id: str = "") -> str:
	canonical = str(
		get_canonical_key(value, capability_id=capability_id or None, dimension_or_metric="metric")
		or ""
	).strip()
	if canonical:
		return str(get_metric_label(canonical) or canonical).strip().lower()
	return str(value or "").strip().replace("_", " ").lower()


def structured_governed_query_message(
	*,
	requested_top_n: int,
	dimension: str,
	metric: str,
	time_phrase: str = "",
	report_name: str = "",
	capability_id: str = "",
) -> str:
	subject = dimension_query_subject(dimension)
	metric_phrase = metric_query_phrase(metric, capability_id=capability_id)
	if subject and metric_phrase:
		parts: List[str] = ["show me"]
		if requested_top_n > 0:
			parts.append(f"top {requested_top_n}")
		parts.append(subject)
		parts.append(f"by {metric_phrase}")
		query = " ".join(part for part in parts if part).strip()
		if time_phrase:
			query = f"{query}{time_phrase}"
		return query.strip()
	if report_name:
		base = f"show me {report_name}".strip()
		if metric_phrase:
			base = f"{base} by {metric_phrase}".strip()
		if time_phrase:
			base = f"{base}{time_phrase}"
		return base.strip()
	return ""


def build_recovery_governed_query_message(recovery_contract: Dict[str, Any]) -> str:
	scope = recovery_contract.get("preservable_scope") if isinstance(recovery_contract.get("preservable_scope"), dict) else {}
	dimensions = [
		str(value or "").strip()
		for value in (recovery_contract.get("preservable_dimensions") or [])
		if str(value or "").strip()
	]
	metrics = [
		str(value or "").strip()
		for value in (recovery_contract.get("preservable_metrics") or [])
		if str(value or "").strip()
	]
	try:
		requested_top_n = int(max(0, scope.get("requested_top_n") or 0))
	except Exception:
		requested_top_n = 0
	primary_dimension = dimensions[0] if dimensions else ""
	primary_metric = metrics[0] if metrics else ""
	if primary_dimension or primary_metric or requested_top_n > 0:
		time_phrase = recovery_time_phrase(recovery_contract)
		query = structured_governed_query_message(
			requested_top_n=requested_top_n,
			dimension=primary_dimension,
			metric=primary_metric,
			time_phrase=time_phrase,
			report_name=str(recovery_contract.get("alternative_report") or recovery_contract.get("source_report") or "").strip(),
			capability_id=str(recovery_contract.get("alternative_capability_id") or recovery_contract.get("source_capability_id") or "").strip(),
		)
		if query:
			return query.strip()
	report_name = str(recovery_contract.get("alternative_report") or "").strip()
	if not report_name:
		report_name = str(recovery_contract.get("source_report") or "").strip()
	time_phrase = recovery_time_phrase(recovery_contract)
	if report_name:
		return f"show me {report_name}{time_phrase}".strip()
	metrics = [
		str(value or "").strip()
		for value in (recovery_contract.get("preservable_metrics") or [])
		if str(value or "").strip()
	]
	dimensions = [
		str(value or "").strip()
		for value in (recovery_contract.get("preservable_dimensions") or [])
		if str(value or "").strip()
	]
	metric_phrase = f" {metrics[0]}" if metrics else ""
	dimension_phrase = f" by {dimensions[0]}" if dimensions else ""
	return f"show me a governed query with{metric_phrase}{dimension_phrase}{time_phrase}".strip()


def build_recovery_guidance_answer(recovery_contract: Dict[str, Any]) -> str:
	source_report = str(recovery_contract.get("source_report") or "the current governed artifact").strip()
	alternative_report = str(recovery_contract.get("alternative_report") or "").strip()
	recommended_action = str(recovery_contract.get("recommended_recovery_action") or "").strip()
	guidance_query = build_recovery_governed_query_message(recovery_contract)
	if alternative_report or guidance_query:
		alternative_intro = (
			f"- Ask for the governed alternative `{alternative_report}` directly"
			if alternative_report
			else "- Ask for the governed alternative directly"
		)
		if guidance_query:
			alternative_intro = f"{alternative_intro}: `{guidance_query}`"
		return (
			f"The current governed source cannot safely provide that output from {source_report}.\n\n"
			"Try one of these governed next steps:\n"
			f"{alternative_intro}\n"
			f"- If you want to stay on the current artifact, ask only for fields already present in {source_report}\n"
			f"- Current recommended recovery path: `{recommended_action or 'run_alternative_governed_query'}`"
		)
	return (
		f"The current governed source cannot safely provide that output from {source_report}.\n\n"
		"Try one of these bounded next steps:\n"
		"- Clarify the exact governed output you want\n"
		"- Ask for a governed operational source that directly contains the missing evidence\n"
		f"- Current recommended recovery path: `{recommended_action or 'clarify_target_output'}`"
	)
