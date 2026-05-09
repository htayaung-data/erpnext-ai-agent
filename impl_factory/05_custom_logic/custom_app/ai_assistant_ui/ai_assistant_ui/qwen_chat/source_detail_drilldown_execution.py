from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.evidence_drilldown_registry import (
	build_governed_drilldown_plan,
)
from ai_assistant_ui.qwen_chat.governed_report_executor import (
	execute_governed_report,
)
from ai_assistant_ui.qwen_chat.semantic_resolution_registry import semantic_alias_phrase_matches


def _artifact_numeric_decimal(value: Any) -> Decimal | None:
	if isinstance(value, bool) or value is None:
		return None
	try:
		return Decimal(str(value).replace(",", "").strip())
	except (InvalidOperation, ValueError):
		return None


def _canonical_metric_key(label: str) -> str:
	normalized = re.sub(r"[^A-Za-z0-9]+", "_", str(label or "").replace("(MMK)", " ").strip().lower())
	return re.sub(r"_+", "_", normalized).strip("_")


def _format_numeric_display_value(value_text: str) -> str:
	text = str(value_text or "").strip()
	if not re.fullmatch(r"-?\d[\d,]*(?:\.\d+)?", text):
		return text
	try:
		value = Decimal(text.replace(",", ""))
	except (InvalidOperation, ValueError):
		return text
	if value == value.to_integral_value():
		return f"{int(value):,}"
	normalized = format(value.normalize(), "f")
	if "." in normalized:
		whole, fractional = normalized.split(".", 1)
		return f"{int(whole):,}.{fractional}"
	return f"{int(value):,}"


def _format_amount_decimal(value: Decimal) -> str:
	return _format_numeric_display_value(format(value, "f"))


def _format_management_amount(value: Decimal) -> str:
	if abs(value) >= Decimal("1000000"):
		millions = (value / Decimal("1000000")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
		return f"{format(millions.normalize(), 'f')} MMK million"
	return f"{_format_amount_decimal(value)} MMK"


def _format_percent_decimal(value: Decimal) -> str:
	return f"{format(value.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP).normalize(), 'f')}%"


def _safe_ratio(numerator: Decimal | None, denominator: Decimal | None) -> Decimal | None:
	if numerator is None or denominator is None or abs(denominator) <= Decimal("0.0001"):
		return None
	return numerator / denominator


def _row_primary_value(row: Dict[str, Any]) -> str:
	for key in ("label", "account_name", "account", "metric", "line", "name", "party", "entity", "entity_name", "customer", "supplier", "item_name", "item_code"):
		text = str(row.get(key) if row.get(key) is not None else "").strip()
		if text:
			return text
	candidates: List[tuple[int, str]] = []
	for value in row.values():
		text = str(value if value is not None else "").strip()
		if not text or not re.search(r"[A-Za-z]", text):
			continue
		score = len(text)
		if " " in text:
			score += 20
		if not re.search(r"-?\d[\d,]*(?:\.\d+)?", text):
			score += 5
		candidates.append((score, text))
	if candidates:
		candidates.sort(key=lambda item: item[0], reverse=True)
		return candidates[0][1]
	for value in row.values():
		text = str(value if value is not None else "").strip()
		if text:
			return text
	return ""


def _normalized_phrase(value: Any) -> str:
	return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def _row_label_acronyms(label: str) -> List[str]:
	words = [
		token
		for token in re.findall(r"[A-Za-z0-9]+", str(label or ""))
		if token
	]
	if len(words) < 2:
		return []
	acronyms: List[str] = []
	all_words = "".join(word[:1].upper() for word in words if word[:1]).strip()
	if all_words:
		acronyms.append(all_words)
	significant_words = [
		word
		for word in words
		if word.lower() not in {"and", "or", "of", "the", "a", "an"}
	]
	if len(significant_words) >= 2:
		significant = "".join(word[:1].upper() for word in significant_words if word[:1]).strip()
		if significant:
			acronyms.append(significant)
	return list(dict.fromkeys(acronym for acronym in acronyms if len(acronym) >= 3))


def _row_target_phrases(row: Dict[str, Any]) -> List[str]:
	phrases: List[str] = []
	for key in ("label", "account_name", "account", "metric", "line", "name", "party", "entity", "entity_name", "customer", "supplier", "item_name", "item_code"):
		value = str(row.get(key) or "").strip()
		if value:
			phrases.append(value)
			if " - " in value:
				phrases.append(value.split(" - ", 1)[0].strip())
	for phrase in list(phrases):
		phrases.extend(_row_label_acronyms(phrase))
	return list(dict.fromkeys(phrase for phrase in phrases if _normalized_phrase(phrase)))


def source_detail_artifact_line_from_message(raw_message: str, artifact_payload: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	sections = artifact.get("sections") if isinstance(artifact.get("sections"), dict) else {}
	best_key = ""
	best_row: Dict[str, Any] = {}
	best_score = -1
	for section_key, rows in sections.items():
		if not isinstance(rows, list):
			continue
		for row in rows:
			if not isinstance(row, dict):
				continue
			for phrase in _row_target_phrases(row):
				if not semantic_alias_phrase_matches(raw_message, phrase):
					continue
				score = len(_normalized_phrase(phrase))
				if score > best_score:
					best_key = str(section_key or "").strip()
					best_row = dict(row)
					best_score = score
	return best_key, best_row


def source_detail_grounding_context_from_artifact(artifact_payload: Dict[str, Any]) -> Dict[str, Any]:
	artifact = dict(artifact_payload or {})
	filters = dict(artifact.get("filters") or {}) if isinstance(artifact.get("filters"), dict) else {}
	dimensions = dict(artifact.get("dimensions") or {}) if isinstance(artifact.get("dimensions"), dict) else {}
	source_reports = [
		str(value or "").strip()
		for value in (artifact.get("source_reports") or [])
		if str(value or "").strip()
	]
	title = str(artifact.get("title") or artifact.get("source_name") or "").strip()
	source_family_id = (
		str(dimensions.get("source_composite_family_id") or "").strip()
		or str(filters.get("composite_family_id") or "").strip()
		or str(artifact.get("family_id") or "").strip()
	)
	return {
		"answer_goal": "expand_detail",
		"evidence_depth": "drilldown_preferred",
		"target_reference": "current_row",
		"evidence_policy": "evidence_expansion_preferred",
		"answer_obligation": "expand_grounded_detail",
		"grounded_source": {
			"family_id": source_family_id,
			"capability_id": str(artifact.get("capability_id") or "").strip(),
			"source_name": title or (source_reports[0] if source_reports else ""),
			"source_reports": source_reports,
		},
		"artifact_metrics": dict(artifact.get("metrics") or {}) if isinstance(artifact.get("metrics"), dict) else {},
		"artifact_filters": filters,
		"artifact_period": dict(artifact.get("period") or {}) if isinstance(artifact.get("period"), dict) else {},
		"artifact_sections": dict(artifact.get("sections") or {}) if isinstance(artifact.get("sections"), dict) else {},
		"grounding_summary": {
			"latest_assistant_title": title,
		},
	}


def _source_detail_result_rows(report_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
	trace = report_payload.get("tool_trace") if isinstance(report_payload.get("tool_trace"), list) else []
	if not trace or not isinstance(trace[0], dict):
		return []
	output_obj = trace[0].get("output_obj") if isinstance(trace[0].get("output_obj"), dict) else {}
	result = output_obj.get("result") if isinstance(output_obj.get("result"), dict) else {}
	data = result.get("data") if isinstance(result.get("data"), list) else []
	return [dict(row) for row in data if isinstance(row, dict)]


def _source_detail_decimal(row: Dict[str, Any], key: str) -> Decimal:
	value = _artifact_numeric_decimal(row.get(key))
	return value if value is not None else Decimal("0")


def _source_detail_amount(row: Dict[str, Any], rendering: Dict[str, Any]) -> Decimal:
	amount_mode = str(rendering.get("amount_mode") or "net_debit_credit").strip()
	if amount_mode == "field_sum":
		amount_field = str(rendering.get("amount_field") or "amount").strip() or "amount"
		return _source_detail_decimal(row, amount_field)
	return _source_detail_decimal(row, "debit") - _source_detail_decimal(row, "credit")


def _source_detail_line_amount(row: Dict[str, Any], rendering: Dict[str, Any]) -> Decimal | None:
	fields = [
		str(value or "").strip()
		for value in (rendering.get("line_amount_fields") or [])
		if str(value or "").strip()
	]
	for field in fields:
		value = _artifact_numeric_decimal(row.get(field))
		if value is not None:
			return value
	for key, value in row.items():
		normalized_key = _canonical_metric_key(str(key or ""))
		if normalized_key in {"amount", "value"}:
			parsed = _artifact_numeric_decimal(value)
			if parsed is not None:
				return parsed
	return None


def _source_detail_grouped_amounts(rows: List[Dict[str, Any]], rendering: Dict[str, Any]) -> List[Dict[str, Any]]:
	group_fields = [
		str(value or "").strip()
		for value in (rendering.get("group_fields") or [])
		if str(value or "").strip()
	]
	if not group_fields:
		group_fields = ["voucher_type", "voucher_no"]
	date_field = str(rendering.get("date_field") or "posting_date").strip() or "posting_date"
	extra_fields = [
		dict(item)
		for item in (rendering.get("extra_fields") or [])
		if isinstance(item, dict) and str(item.get("field") or "").strip()
	]
	groups: Dict[str, Dict[str, Any]] = {}
	for row in rows:
		key_parts = [str(row.get(field) or "").strip() for field in group_fields if str(row.get(field) or "").strip()]
		if not key_parts:
			continue
		key = " ".join(key_parts)
		net_amount = _source_detail_amount(row, rendering)
		group = groups.setdefault(
			key,
			{
				"label": key,
				"amount": Decimal("0"),
				"row_count": 0,
				"date": str(row.get(date_field) or "").strip(),
				"extra_values": {},
			},
		)
		group["amount"] += net_amount
		group["row_count"] += 1
		if not group.get("date") and str(row.get(date_field) or "").strip():
			group["date"] = str(row.get(date_field) or "").strip()
		for spec in extra_fields:
			field = str(spec.get("field") or "").strip()
			if not field:
				continue
			extra_values = group.setdefault("extra_values", {})
			if str(extra_values.get(field) or "").strip():
				continue
			value = row.get(field)
			if value not in (None, ""):
				extra_values[field] = value
	return sorted(groups.values(), key=lambda item: abs(item.get("amount") or Decimal("0")), reverse=True)


def _source_detail_amount_support_label(report_name: str, rendering: Dict[str, Any]) -> str:
	label = str(rendering.get("amount_support_label") or "").strip()
	if label:
		return label
	if str(rendering.get("amount_mode") or "").strip() == "field_sum":
		amount_field = str(rendering.get("amount_field") or "amount").strip() or "amount"
		return f"Computed from {report_name} rows using `{amount_field}`."
	return f"Computed from {report_name} rows using debit minus credit."


def _source_detail_source_label(rendering: Dict[str, Any]) -> str:
	return str(rendering.get("source_label") or "source rows").strip() or "source rows"


def _source_detail_document_label(rendering: Dict[str, Any]) -> str:
	return str(rendering.get("source_document_label") or "source document").strip() or "source document"


def _source_detail_table_lines(
	*,
	grouped_rows: List[Dict[str, Any]],
	basis_amount: Decimal,
	rendering: Dict[str, Any],
	verified_values: List[str],
) -> List[str]:
	extra_fields = [
		dict(item)
		for item in (rendering.get("extra_fields") or [])
		if isinstance(item, dict) and str(item.get("field") or "").strip()
	]
	document_header = str(rendering.get("document_label") or "Source document").strip() or "Source document"
	amount_header = str(rendering.get("amount_label") or "Net line impact").strip() or "Net line impact"
	share_header = str(rendering.get("share_label") or "Share of line").strip() or "Share of line"
	columns = [document_header]
	alignments = ["---"]
	for spec in extra_fields:
		columns.append(str(spec.get("label") or spec.get("field") or "").strip())
		alignments.append("---")
	columns.extend([amount_header, share_header])
	alignments.extend(["---:", "---:"])
	lines = [
		"| " + " | ".join(columns) + " |",
		"| " + " | ".join(alignments) + " |",
	]
	for group in grouped_rows[:8]:
		amount = group.get("amount") if isinstance(group.get("amount"), Decimal) else Decimal("0")
		share = _safe_ratio(abs(amount), abs(basis_amount))
		share_text = _format_percent_decimal(share * Decimal("100")) if share is not None else ""
		extra_values = group.get("extra_values") if isinstance(group.get("extra_values"), dict) else {}
		row_values = [str(group.get("label") or "").strip()]
		for spec in extra_fields:
			field = str(spec.get("field") or "").strip()
			value = extra_values.get(field, "")
			parsed = _artifact_numeric_decimal(value)
			row_values.append(_format_amount_decimal(parsed) if parsed is not None else str(value or "").strip())
		row_values.extend([_format_management_amount(amount), share_text])
		lines.append("| " + " | ".join(row_values) + " |")
		verified_values.append(str(group.get("label") or ""))
		verified_values.append(format(amount, "f"))
		if share is not None:
			verified_values.append(format((share * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP), "f"))
	return lines


def build_source_detail_drilldown_payload(
	*,
	context: Dict[str, Any],
	focused_row: Dict[str, Any],
	user_id: str,
) -> Dict[str, Any]:
	plan = build_governed_drilldown_plan(
		grounding_context=context,
		focused_row=focused_row,
	)
	if str(plan.get("status") or "").strip() != "source_detail_available":
		return {}
	target_report = plan.get("target_report") if isinstance(plan.get("target_report"), dict) else {}
	report_name = str(target_report.get("report_name") or "").strip()
	filters = dict(target_report.get("filters") or {}) if isinstance(target_report.get("filters"), dict) else {}
	if not report_name or not filters:
		return {}
	report_payload = execute_governed_report(
		report_name=report_name,
		filters=filters,
		user=str(user_id or "Administrator").strip() or "Administrator",
		mode="source_detail_drilldown",
		target_limit=int(target_report.get("target_limit") or 100),
	)
	if not bool(report_payload.get("ok")):
		return {}
	rows = _source_detail_result_rows(report_payload)
	if not rows:
		return {}
	rendering = plan.get("rendering") if isinstance(plan.get("rendering"), dict) else {}
	line_amount = _source_detail_line_amount(focused_row, rendering)
	grouped_rows = _source_detail_grouped_amounts(rows, rendering)
	if not grouped_rows:
		return {}
	total_net = sum((_source_detail_amount(row, rendering)) for row in rows)
	reconciles = line_amount is not None and abs(total_net - line_amount) <= Decimal("1")
	basis_amount = line_amount if line_amount is not None else total_net
	if basis_amount == 0:
		return {}
	line_label = _row_primary_value(focused_row) or str(filters.get("account") or "the selected line").strip()
	source_name = (
		str(((context or {}).get("grounding_summary") or {}).get("latest_assistant_title") or "").strip()
		or str(((context or {}).get("grounded_source") or {}).get("source_name") or "").strip()
		or "the current ERP result"
	)
	top_group = grouped_rows[0]
	top_share = _safe_ratio(abs(top_group.get("amount") or Decimal("0")), abs(basis_amount))
	top_share_text = _format_percent_decimal(top_share * Decimal("100")) if top_share is not None else ""
	source_label = _source_detail_source_label(rendering)
	document_label = _source_detail_document_label(rendering)
	amount_support_label = _source_detail_amount_support_label(report_name, rendering)
	share_context_label = str(rendering.get("share_context_label") or "line").strip() or "line"
	supported_claims: List[Dict[str, str]] = []
	verified_values: List[str] = [
		format(total_net, "f"),
		format(basis_amount, "f"),
		str(len(rows)),
		str(top_group.get("label") or ""),
	]
	if line_amount is not None:
		verified_values.append(format(line_amount, "f"))
		if reconciles:
			diagnosis = (
				f"The approved {report_name} rows reconcile to the {line_label} line: "
				f"{_format_management_amount(total_net)} across {len(rows)} {source_label}."
			)
		else:
			diagnosis = (
				f"The approved {report_name} rows total {_format_management_amount(total_net)}, while the visible line amount is "
				f"{_format_management_amount(line_amount)}; treat this as source-detail evidence that needs reconciliation review."
			)
	else:
		diagnosis = (
			f"The approved {report_name} rows show {_format_management_amount(total_net)} across {len(rows)} {source_label}."
		)
	top_driver_claim = (
		f"The largest {document_label} is {top_group['label']} at "
		f"{_format_management_amount(top_group.get('amount') or Decimal('0'))}"
		+ (f", or {top_share_text} of the {share_context_label}." if top_share_text else ".")
	)
	supported_claims.extend(
		[
			{"claim": diagnosis, "support": amount_support_label},
			{
				"claim": top_driver_claim,
				"support": str(rendering.get("grouping_support_label") or "Source-detail rows were grouped by governed document identity.").strip(),
			},
		]
	)
	consultant_takeaway = str(rendering.get("consultant_takeaway") or "").strip()
	if not consultant_takeaway:
		consultant_takeaway = (
			"The right management lens is source-document concentration: investigate the largest documents first, "
			"then confirm whether the postings reflect expected deliveries, costing, returns, or adjustments."
		)
	breakdown_title = str(rendering.get("breakdown_title") or "Breakdown by source document").strip() or "Breakdown by source document"
	lines: List[str] = [
		f"Here is the source-detail breakdown for {line_label} from {source_name}.",
		"",
		"Executive diagnosis",
		"",
		f"- {diagnosis}",
		"",
		f"- {top_driver_claim}",
		"",
		breakdown_title,
		"",
	]
	lines.extend(
		_source_detail_table_lines(
			grouped_rows=grouped_rows,
			basis_amount=basis_amount,
			rendering=rendering,
			verified_values=verified_values,
		)
	)
	priority_notes = [
		str(value or "").strip()
		for value in (rendering.get("management_priority_notes") or [])
		if str(value or "").strip()
	]
	if not priority_notes:
		priority_notes = [
			f"Review the largest source document first: {top_group['label']}.",
			"Reconcile any negative or reversing entries separately, because those can hide returns, cancellations, or corrections.",
		]
	lines.extend(
		[
			"",
			"Consultant takeaway",
			"",
			consultant_takeaway,
			"",
			"Management priorities",
			"",
		]
	)
	for note in priority_notes:
		lines.extend([f"- {note}", ""])
	return {
		"answer_text": "\n".join(lines).strip(),
		"supported_claims": supported_claims,
		"recommendations": [],
		"offered_next_actions": [],
		"speculation_flags": ["source_detail_drilldown_executed", str(plan.get("source_detail_rule_id") or "").strip()],
		"confidence": 0.86 if reconciles else 0.78,
		"reason": "The answer executed a registered governed source-detail report for the focused result row.",
		"evidence_expansion_plan": plan,
		"_verified_numeric_values": verified_values,
	}


def build_source_detail_drilldown_payload_from_artifact_line(
	*,
	artifact_payload: Dict[str, Any],
	focused_row: Dict[str, Any],
	user_id: str,
) -> Dict[str, Any]:
	context = source_detail_grounding_context_from_artifact(artifact_payload)
	return build_source_detail_drilldown_payload(
		context=context,
		focused_row=focused_row,
		user_id=user_id,
	)
