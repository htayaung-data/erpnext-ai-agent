from __future__ import annotations

from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.contracts import build_entity_detail_evidence_request_contract
from ai_assistant_ui.qwen_chat.metadata import ontology_detect_concepts
from ai_assistant_ui.qwen_chat.semantic_aliases import detect_canonical_keys


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _numeric(value: Any) -> float:
	try:
		return float(value or 0.0)
	except Exception:
		return 0.0


def _money(value: Any) -> str:
	return f"{_numeric(value):,.2f}".rstrip("0").rstrip(".")


def _summary_block(title: str, rows: List[List[str]]) -> Dict[str, Any]:
	return {
		"block_type": "summary_table",
		"title": _clean_text(title),
		"columns": ["Metric", "Value"],
		"rows": [[_clean_text(row[0]), _clean_text(row[1])] for row in rows if len(row) >= 2 and _clean_text(row[1])],
	}


def _data_block(title: str, columns: List[str], rows: List[List[str]]) -> Dict[str, Any]:
	return {
		"block_type": "data_table",
		"title": _clean_text(title),
		"columns": [_clean_text(column) for column in columns if _clean_text(column)],
		"rows": [[_clean_text(cell) for cell in row] for row in rows],
	}


def _ensure_entity_detail_evidence_request_contract(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	evidence_request_contract: Dict[str, Any] | None,
) -> Dict[str, Any]:
	if isinstance(evidence_request_contract, dict):
		return dict(evidence_request_contract)
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	return build_entity_detail_evidence_request_contract(
		request_id=_clean_text(artifact.get("request_id")),
		raw_message=raw_message,
		artifact_payload=artifact,
	).to_payload()


def _artifact_stock_rows(artifact_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	sections = artifact.get("sections") if isinstance(artifact.get("sections"), dict) else {}
	rows = sections.get("stock_rows") if isinstance(sections.get("stock_rows"), list) else []
	return [dict(row or {}) for row in rows if isinstance(row, dict)]


def _artifact_warehouse_totals(artifact_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	sections = artifact.get("sections") if isinstance(artifact.get("sections"), dict) else {}
	rows = sections.get("warehouse_totals") if isinstance(sections.get("warehouse_totals"), list) else []
	return [dict(row or {}) for row in rows if isinstance(row, dict)]


def _artifact_item_totals(artifact_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	sections = artifact.get("sections") if isinstance(artifact.get("sections"), dict) else {}
	rows = sections.get("item_totals") if isinstance(sections.get("item_totals"), list) else []
	return [dict(row or {}) for row in rows if isinstance(row, dict)]


def _stock_metric_alias(value: Any) -> str:
	key = _clean_text(value)
	return {
		"quantity": "balance_qty",
		"qty": "balance_qty",
		"stock_qty": "balance_qty",
		"stock_quantity": "balance_qty",
		"value": "balance_value",
		"stock_value": "balance_value",
		"inventory_value": "balance_value",
	}.get(key, key)


def stock_position_request_signal(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	evidence_request_contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	family_id = _clean_text(artifact.get("family_id"))
	dimensions = artifact.get("dimensions") if isinstance(artifact.get("dimensions"), dict) else {}
	entity_type = _clean_text(dimensions.get("entity_type")).lower()
	requested_metrics: List[str] = []
	requested_dimensions: List[str] = []
	requested_concepts: List[str] = []
	entity_question_type = ""
	if family_id == "entity_detail":
		typed_request = _ensure_entity_detail_evidence_request_contract(
			raw_message=raw_message,
			artifact_payload=artifact,
			evidence_request_contract=evidence_request_contract,
		)
		requested_metrics = [
			_stock_metric_alias(value)
			for value in (typed_request.get("requested_metrics") or [])
			if _stock_metric_alias(value)
		]
		requested_dimensions = [
			_clean_text(value)
			for value in (typed_request.get("requested_dimensions") or [])
			if _clean_text(value)
		]
		requested_concepts = [
			_clean_text(value)
			for value in (typed_request.get("requested_concepts") or [])
			if _clean_text(value)
		]
		entity_question_type = _clean_text(typed_request.get("entity_question_type"))
	else:
		requested_metrics = [
			_stock_metric_alias(value)
			for value in detect_canonical_keys(raw_message, capability_id="stock_read", dimension_or_metric="metric")
			if _stock_metric_alias(value)
		]
		requested_dimensions = [
			_clean_text(value)
			for value in detect_canonical_keys(raw_message, capability_id="stock_read", dimension_or_metric="dimension")
			if _clean_text(value)
		]
		requested_concepts = [
			_clean_text(value)
			for value in ontology_detect_concepts(raw_message)
			if _clean_text(value)
		]
	metric_set = set(requested_metrics)
	dimension_set = set(requested_dimensions)
	concept_set = set(requested_concepts)
	stock_position_requested = bool(
		entity_question_type == "item_stock_position"
		or metric_set.intersection({"balance_qty", "balance_value"})
		or "warehouse" in dimension_set
		or "inventory" in concept_set
	)
	wants_warehouse = "warehouse" in dimension_set
	return {
		"family_id": family_id,
		"entity_type": entity_type,
		"requested_metrics": requested_metrics,
		"requested_dimensions": requested_dimensions,
		"requested_concepts": requested_concepts,
		"entity_question_type": entity_question_type,
		"stock_position_requested": stock_position_requested,
		"wants_warehouse": wants_warehouse,
		"wants_quantity": "balance_qty" in metric_set or (stock_position_requested and wants_warehouse and "balance_value" not in metric_set),
		"wants_value": "balance_value" in metric_set,
	}


def _item_stock_subject_label(artifact_payload: Dict[str, Any]) -> str:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	dimensions = artifact.get("dimensions") if isinstance(artifact.get("dimensions"), dict) else {}
	return _clean_text(dimensions.get("entity_label") or dimensions.get("entity_key") or "this item")


def _item_stock_uom(artifact_payload: Dict[str, Any]) -> str:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	sections = artifact.get("sections") if isinstance(artifact.get("sections"), dict) else {}
	summary_rows = sections.get("summary") if isinstance(sections.get("summary"), list) else []
	for row in summary_rows:
		if not isinstance(row, dict):
			continue
		if _clean_text(row.get("label")).lower() == "uom" and _clean_text(row.get("value")):
			return _clean_text(row.get("value"))
	return "units"


def stock_position_context(artifact_payload: Dict[str, Any]) -> Dict[str, Any]:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	family_id = _clean_text(artifact.get("family_id"))
	dimensions = artifact.get("dimensions") if isinstance(artifact.get("dimensions"), dict) else {}
	metrics = artifact.get("metrics") if isinstance(artifact.get("metrics"), dict) else {}
	entity_type = _clean_text(dimensions.get("entity_type")).lower()
	if family_id == "entity_detail" and entity_type == "item":
		rows = _artifact_stock_rows(artifact)
		return {
			"title": f"Stock Position for {_item_stock_subject_label(artifact)}",
			"subject_label": _item_stock_subject_label(artifact),
			"subject_kind": "item",
			"row_label": "warehouse",
			"rows": rows,
			"uom": _item_stock_uom(artifact),
			"total_qty": _numeric(metrics.get("balance_qty")) or sum(_numeric(row.get("balance_qty")) for row in rows),
			"total_value": _numeric(metrics.get("balance_value")) or sum(_numeric(row.get("balance_value")) for row in rows),
			"row_count": int(metrics.get("warehouse_count") or len(rows) or 0),
		}
	if family_id == "inventory_snapshot":
		warehouse_rows = _artifact_warehouse_totals(artifact)
		item_rows = _artifact_item_totals(artifact)
		rows = warehouse_rows or item_rows
		return {
			"title": "Inventory Snapshot Evidence",
			"subject_label": "the current inventory snapshot",
			"subject_kind": "snapshot",
			"row_label": "warehouse" if warehouse_rows else "item",
			"rows": rows,
			"uom": "units",
			"total_qty": _numeric(metrics.get("balance_qty")) or sum(_numeric(row.get("balance_qty")) for row in rows),
			"total_value": _numeric(metrics.get("balance_value")) or sum(_numeric(row.get("balance_value")) for row in rows),
			"row_count": int(metrics.get("warehouse_count") or metrics.get("item_count") or len(rows) or 0),
		}
	return {}


def item_stock_direct_evidence_rendered_payload(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	evidence_request_contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	family_id = _clean_text(artifact.get("family_id"))
	if family_id not in {"entity_detail", "inventory_snapshot"}:
		return {}
	stock_signal = stock_position_request_signal(
		raw_message=raw_message,
		artifact_payload=artifact,
		evidence_request_contract=evidence_request_contract,
	)
	stock_context = stock_position_context(artifact)
	if not stock_signal.get("stock_position_requested") or not stock_context:
		return {}
	rows = list(stock_context.get("rows") or [])
	if not rows:
		return {}
	row_label = _clean_text(stock_context.get("row_label")) or "warehouse"
	primary_label = "Warehouse" if row_label == "warehouse" else "Item"
	summary_label = "Item" if _clean_text(stock_context.get("subject_kind")) == "item" else "Scope"
	return {
		"type": "qwen_rendered_family_response_contract",
		"contract_version": "1.0",
		"request_id": _clean_text(artifact.get("request_id")),
		"family_id": family_id,
		"renderer_id": "grounded_artifact_direct_evidence",
		"title": _clean_text(stock_context.get("title")) or "Stock Position",
		"answer_text": "",
		"source_reports": [_clean_text(value) for value in (artifact.get("source_reports") or []) if _clean_text(value)],
		"blocks": [
			_summary_block(
				"Stock Summary",
				[
					[summary_label, _clean_text(stock_context.get("subject_label"))],
					["Total On Hand Qty", _money(stock_context.get("total_qty"))],
					["Total Stock Value (MMK)", _money(stock_context.get("total_value"))],
					["Warehouse Count" if row_label == "warehouse" else "Item Count", str(int(stock_context.get("row_count") or 0))],
				],
			),
			_data_block(
				"Stock by Warehouse" if row_label == "warehouse" else "Stock by Item",
				[primary_label, "Qty", "Stock Value (MMK)"],
				[
					[_clean_text(row.get(row_label)), _money(row.get("balance_qty")), _money(row.get("balance_value"))]
					for row in rows
					if _clean_text(row.get(row_label))
				],
			),
		],
		"warnings": [_clean_text(value) for value in (artifact.get("warnings") or []) if _clean_text(value)],
	}


def item_stock_direct_evidence_answer(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	evidence_request_contract: Dict[str, Any] | None = None,
) -> str:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	if _clean_text(artifact.get("family_id")) not in {"entity_detail", "inventory_snapshot"}:
		return ""
	stock_signal = stock_position_request_signal(
		raw_message=raw_message,
		artifact_payload=artifact,
		evidence_request_contract=evidence_request_contract,
	)
	stock_context = stock_position_context(artifact)
	if not stock_signal.get("stock_position_requested") or not stock_context:
		return ""
	rows = list(stock_context.get("rows") or [])
	if not rows:
		return ""
	subject_label = _clean_text(stock_context.get("subject_label")) or "this item"
	uom = _clean_text(stock_context.get("uom")) or "units"
	total_qty = _numeric(stock_context.get("total_qty"))
	total_value = _numeric(stock_context.get("total_value"))
	row_count = int(stock_context.get("row_count") or len(rows) or 0)
	wants_warehouse = bool(stock_signal.get("wants_warehouse"))
	wants_quantity = bool(stock_signal.get("wants_quantity"))
	wants_value = bool(stock_signal.get("wants_value"))
	subject_is_item = _clean_text(stock_context.get("subject_kind")) == "item"
	if wants_warehouse:
		header = (
			f"{subject_label} currently has {_money(total_qty)} {uom} on hand across {row_count} warehouses."
			if subject_is_item
			else f"The current inventory snapshot shows {_money(total_qty)} {uom} across {row_count} warehouses."
		)
		label_key = _clean_text(stock_context.get("row_label")) or "warehouse"
		lines = []
		for row in rows:
			label_value = _clean_text(row.get(label_key))
			if not label_value:
				continue
			if wants_value and not wants_quantity:
				lines.append(f"- {label_value}: {_money(row.get('balance_value'))} MMK")
			elif wants_value:
				lines.append(f"- {label_value}: {_money(row.get('balance_qty'))} {uom}, {_money(row.get('balance_value'))} MMK")
			else:
				lines.append(f"- {label_value}: {_money(row.get('balance_qty'))} {uom}")
		return header + ("\n\nStock by Warehouse:\n" + "\n".join(lines) if lines else "")
	if wants_value and not wants_quantity:
		if subject_is_item:
			return f"The current stock value for {subject_label} is {_money(total_value)} MMK across {row_count} warehouses."
		return f"The current inventory snapshot value is {_money(total_value)} MMK."
	if subject_is_item:
		return f"{subject_label} currently has {_money(total_qty)} {uom} on hand across {row_count} warehouses."
	return f"The current inventory snapshot shows {_money(total_qty)} {uom} across {row_count} warehouses."


def item_stock_evidence_boundary_answer(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	evidence_request_contract: Dict[str, Any] | None = None,
) -> str:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	if _clean_text(artifact.get("family_id")) not in {"entity_detail", "transaction_listing", "inventory_snapshot"}:
		return ""
	stock_signal = stock_position_request_signal(
		raw_message=raw_message,
		artifact_payload=artifact,
		evidence_request_contract=evidence_request_contract,
	)
	stock_context = stock_position_context(artifact)
	if not stock_signal.get("stock_position_requested") or bool(stock_context.get("rows")):
		return ""
	if _clean_text(artifact.get("family_id")) == "entity_detail":
		entity_label = _item_stock_subject_label(artifact)
		return (
			f"I can help with the stock position for {entity_label}, but the current result does not include warehouse-level stock rows.\n\n"
			"Please ask me to refresh the stock view for this item so I can show quantity by warehouse."
		)
	return (
		"The current inventory result does not include the warehouse-level stock rows needed for that answer.\n\n"
		"Please ask for a warehouse stock view so I can show the quantity by warehouse."
	)
