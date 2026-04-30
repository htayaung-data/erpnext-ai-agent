from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ai_assistant_ui.qwen_chat.conversation_control_support import (
	recent_focus_restore_runtime_message as _recent_focus_restore_runtime_message_helper,
	recent_focus_state_from_prior_branch_restore_contract as _recent_focus_state_from_prior_branch_restore_contract_helper,
	select_recent_focus_continuation_eligibility as _select_recent_focus_continuation_eligibility_helper,
)
from ai_assistant_ui.qwen_chat.contracts import build_recent_focus_affordance_contract
from ai_assistant_ui.qwen_chat.customer_lifecycle_basis import customer_lifecycle_supported_focus_grains
from ai_assistant_ui.qwen_chat.document_event_basis import document_event_supported_focus_grains
from ai_assistant_ui.qwen_chat.governed_scope_registry import (
	entity_grain_for_report_name,
	governed_scope_runtime_policy,
	governed_scope_spec,
	listing_view_for_report_name,
	scope_id_for_report_name,
	scope_id_for_entity_grain,
	scope_id_for_listing_view,
)
from ai_assistant_ui.qwen_chat.metadata import (
	get_report_spec,
	load_governed_scope_registry,
	normalize_followup_mode_for_runtime,
	report_business_family_ids,
	report_approved_followup_modes,
	report_direct_query_doctype,
	report_direct_query_fields,
	report_grouping_document_key_field,
	report_supported_dimensions,
)
from ai_assistant_ui.qwen_chat.master_data_family_support import is_master_data_listing_family
from ai_assistant_ui.qwen_chat.item_product_support import (
	is_item_product_grain,
	normalize_item_product_grain,
)


_LOCAL_RECENT_FOCUS_FOLLOWUP_MODES = {
	"presentation_transform",
	"table_presentation",
	"bullet_presentation",
	"metric_refinement",
	"column_refinement",
	"aging_bucket_view",
	"dimension_breakdown",
	"sort_or_limit",
}


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	items: List[str] = []
	for value in values:
		text = _clean_text(value)
		if text:
			items.append(text)
	return items


def _append_unique(items: List[str], value: Any) -> None:
	text = _clean_text(value)
	if text and text not in items:
		items.append(text)


def _extend_unique(items: List[str], values: List[Any]) -> None:
	for value in values or []:
		_append_unique(items, value)


def _normalize_text(value: Any) -> str:
	return " ".join(_clean_text(value).lower().split())


def _active_approved_scope_specs() -> List[Dict[str, Any]]:
	values = load_governed_scope_registry().get("scopes")
	if not isinstance(values, list):
		return []
	out: List[Dict[str, Any]] = []
	for item in values:
		if not isinstance(item, dict):
			continue
		authority = item.get("approved_source_authority") if isinstance(item.get("approved_source_authority"), dict) else {}
		if _clean_text(item.get("status")) != "active":
			continue
		if _clean_text(authority.get("authority_status")) != "approved":
			continue
		if _clean_text(authority.get("source_kind")) != "report":
			continue
		out.append(dict(item))
	return out


def detail_capable_document_focus_grains() -> List[str]:
	grains: List[str] = []
	for scope in _active_approved_scope_specs():
		scope_id = _clean_text(scope.get("scope_id"))
		if not scope_id:
			continue
		policy = governed_scope_runtime_policy(scope_id, "entity_detail")
		if not isinstance(policy, dict) or not policy:
			continue
		if _clean_text(policy.get("compatibility_level")) != "full_consumption":
			continue
		allowed_modes = {
			_clean_text(value)
			for value in _clean_list(policy.get("allowed_modes"))
			if _clean_text(value)
		}
		if not allowed_modes.intersection({"document_detail", "profile_section_evidence"}):
			continue
		authority = scope.get("approved_source_authority") if isinstance(scope.get("approved_source_authority"), dict) else {}
		report_name = _clean_text(authority.get("report_name"))
		focus_grain = listing_view_for_report_name(report_name) or scope_id
		_append_unique(grains, focus_grain)
	return grains


def is_detail_capable_document_focus_grain(focus_grain: str) -> bool:
	return _clean_text(focus_grain) in set(detail_capable_document_focus_grains())


def _report_name_for_document_focus_grain(focus_grain: str) -> str:
	scope_id = scope_id_for_listing_view(focus_grain) or _clean_text(focus_grain)
	scope_spec = governed_scope_spec(scope_id)
	authority = scope_spec.get("approved_source_authority") if isinstance(scope_spec.get("approved_source_authority"), dict) else {}
	return _clean_text(authority.get("report_name"))


def document_recent_focus_row_candidate_columns(*, focus_grain: str, source_report: str = "") -> List[str]:
	grain = _clean_text(focus_grain)
	if not is_detail_capable_document_focus_grain(grain):
		return []
	report_name = _clean_text(source_report) or _report_name_for_document_focus_grain(grain)
	scope_id = scope_id_for_listing_view(grain) or scope_id_for_report_name(report_name) or grain
	scope_spec = governed_scope_spec(scope_id)
	scope_label = _clean_text(scope_spec.get("scope_label"))
	doctype = report_direct_query_doctype(report_name)
	document_key_field = report_grouping_document_key_field(report_name)
	candidates: List[str] = []
	for label in (scope_label, doctype):
		_append_unique(candidates, label)
		parts = [part for part in label.split() if part]
		if len(parts) > 1:
			_append_unique(candidates, parts[-1])
	for field_name in report_direct_query_fields(report_name):
		if field_name.lower() == "name":
			_append_unique(candidates, field_name)
	_append_unique(candidates, document_key_field)
	_append_unique(candidates, "name")
	return candidates


def _report_name_for_master_data_focus_grain(focus_grain: str) -> str:
	scope_id = scope_id_for_entity_grain(focus_grain) or _clean_text(focus_grain)
	scope_spec = governed_scope_spec(scope_id)
	authority = scope_spec.get("approved_source_authority") if isinstance(scope_spec.get("approved_source_authority"), dict) else {}
	return _clean_text(authority.get("report_name"))


def _humanized_field_name(field_name: str) -> str:
	text = _clean_text(field_name)
	if not text:
		return ""
	return text.replace("_", " ").title()


def _master_data_dimension_label(source_report: str) -> str:
	for value in report_supported_dimensions(source_report):
		label = _clean_text(value)
		if label and label not in {"Creation", "Modified"}:
			return label
	return ""


def master_data_recent_focus_row_label_columns(*, focus_grain: str, source_report: str = "") -> List[str]:
	grain = normalize_item_product_grain(_clean_text(focus_grain))
	scope_id = scope_id_for_entity_grain(grain) or grain
	scope_spec = governed_scope_spec(scope_id)
	if _clean_text(scope_spec.get("status")) != "active":
		return []
	report_name = _clean_text(source_report) or _report_name_for_master_data_focus_grain(grain)
	doctype = report_direct_query_doctype(report_name)
	scope_label = _clean_text(scope_spec.get("scope_label"))
	dimension_label = _master_data_dimension_label(report_name)
	candidates: List[str] = []
	for field_name in report_direct_query_fields(report_name):
		if field_name.lower().endswith("_name"):
			_append_unique(candidates, _humanized_field_name(field_name))
			_append_unique(candidates, field_name)
	for label in (dimension_label, doctype, scope_label, f"{doctype} Name" if doctype else ""):
		_append_unique(candidates, label)
	for field_name in report_direct_query_fields(report_name):
		if field_name.lower() == "name":
			continue
		_append_unique(candidates, _humanized_field_name(field_name))
		_append_unique(candidates, field_name)
	_append_unique(candidates, "name")
	return candidates


def master_data_recent_focus_row_key_columns(*, focus_grain: str, source_report: str = "") -> List[str]:
	grain = normalize_item_product_grain(_clean_text(focus_grain))
	scope_id = scope_id_for_entity_grain(grain) or grain
	scope_spec = governed_scope_spec(scope_id)
	if _clean_text(scope_spec.get("status")) != "active":
		return []
	report_name = _clean_text(source_report) or _report_name_for_master_data_focus_grain(grain)
	doctype = report_direct_query_doctype(report_name)
	dimension_label = _master_data_dimension_label(report_name)
	candidates: List[str] = []
	_append_unique(candidates, "name")
	for label in (dimension_label, doctype, f"{doctype} Code" if doctype else ""):
		_append_unique(candidates, label)
	for field_name in report_direct_query_fields(report_name):
		if field_name.lower() == "name":
			continue
		_append_unique(candidates, _humanized_field_name(field_name))
		_append_unique(candidates, field_name)
	return candidates


def statement_recent_focus_descriptor_for_report_name(report_name: str) -> Dict[str, str]:
	clean_report_name = _clean_text(report_name)
	if not clean_report_name:
		return {}
	report_spec = get_report_spec(clean_report_name)
	supported_families = {
		_clean_text(value)
		for value in report_business_family_ids(clean_report_name)
		if _clean_text(value)
	}
	if "financial_statement" not in supported_families:
		return {}
	report_family = _clean_text(report_spec.get("family"))
	if report_family.endswith("_statement"):
		report_family = report_family[: -len("_statement")]
	focus_grain = report_family or clean_report_name.lower().replace(" ", "_")
	return {
		"focus_kind": "statement",
		"focus_grain": focus_grain,
		"focus_label": clean_report_name,
		"focus_key": clean_report_name,
	}


def _governed_runtime_policy_from_dimensions(dimensions: Dict[str, Any] | None = None) -> Dict[str, Any]:
	dimension_payload = dimensions if isinstance(dimensions, dict) else {}
	policy = dimension_payload.get("governed_scope_runtime_policy")
	if not isinstance(policy, dict):
		return {}
	return dict(policy)


def _governed_report_surface_descriptor_from_runtime_policy(
	*,
	source_report: str,
	source_kind: str = "",
	source_family: str = "",
	dimensions: Dict[str, Any] | None = None,
) -> Dict[str, str]:
	dimension_payload = dimensions if isinstance(dimensions, dict) else {}
	policy = _governed_runtime_policy_from_dimensions(dimension_payload)
	policy_family = _clean_text(policy.get("family_id") or source_family)
	scope_id = _clean_text(policy.get("scope_id") or dimension_payload.get("scope_id"))
	scope_class = _clean_text(policy.get("scope_class") or dimension_payload.get("scope_class"))
	clean_report_name = _clean_text(source_report)
	if not policy_family and not scope_class:
		return {}
	if policy_family == "financial_statement" or scope_class == "financial_summary":
		return {
			"surface_class": "statement",
			"focus_kind": "statement",
			"focus_grain": scope_id or _clean_text(dimension_payload.get("statement_type")) or clean_report_name.lower().replace(" ", "_"),
			"focus_label": clean_report_name,
			"focus_key": clean_report_name,
			"source_family_default": "financial_statement",
			"derivation_basis": "statement_grounded_turn",
			"scope_id": scope_id,
			"scope_class": scope_class or "financial_summary",
		}
	if _clean_text(source_kind) != "report":
		return {}
	if policy_family in {
		"aging",
		"ranking_analytics",
		"inventory_snapshot",
		"product_profitability",
		"trend_analytics",
	} or scope_class in {
		"aging_analysis",
		"ranked_entities",
		"inventory_summary",
		"product_performance",
		"trend_analysis",
	}:
		return {
			"surface_class": "report",
			"focus_kind": "report",
			"focus_grain": policy_family or clean_report_name.lower().replace(" ", "_"),
			"focus_label": clean_report_name,
			"focus_key": clean_report_name,
			"source_family_default": policy_family or "report",
			"derivation_basis": "report_grounded_turn",
			"scope_id": scope_id,
			"scope_class": scope_class,
		}
	return {}


def report_recent_focus_descriptor_for_report_name(
	report_name: str,
	*,
	source_family: str = "",
) -> Dict[str, str]:
	clean_report_name = _clean_text(report_name)
	if not clean_report_name:
		return {}
	report_spec = get_report_spec(clean_report_name)
	focus_grain = _clean_text(source_family) or _clean_text(report_spec.get("family"))
	if not focus_grain:
		focus_grain = clean_report_name.lower().replace(" ", "_")
	return {
		"focus_kind": "report",
		"focus_grain": focus_grain,
		"focus_label": clean_report_name,
		"focus_key": clean_report_name,
	}


def grounded_recent_focus_surface_descriptor(
	*,
	source_report: str,
	source_kind: str = "",
	source_family: str = "",
	dimensions: Dict[str, Any] | None = None,
) -> Dict[str, str]:
	clean_report_name = _clean_text(source_report)
	clean_source_kind = _clean_text(source_kind)
	clean_source_family = _clean_text(source_family)
	dimension_payload = dimensions if isinstance(dimensions, dict) else {}
	supported_families = {
		_clean_text(value)
		for value in report_business_family_ids(clean_report_name)
		if _clean_text(value)
	}
	entity_grain = _clean_text(
		entity_grain_for_report_name(clean_report_name)
		or dimension_payload.get("entity_type")
	)
	listing_view = _clean_text(
		listing_view_for_report_name(clean_report_name)
		or dimension_payload.get("listing_view")
	)
	is_entity_detail_surface = bool(
		clean_source_family == "entity_detail"
		or "entity_detail" in supported_families
		or clean_report_name.endswith(" Detail")
	)
	if is_entity_detail_surface:
		return {
			"surface_class": "entity_detail",
			"focus_label_fallback": clean_report_name[:-7] if clean_report_name.endswith(" Detail") else "",
		}
	governed_policy_surface = _governed_report_surface_descriptor_from_runtime_policy(
		source_report=clean_report_name,
		source_kind=clean_source_kind,
		source_family=clean_source_family,
		dimensions=dimension_payload,
	)
	if governed_policy_surface:
		return governed_policy_surface
	statement_focus = statement_recent_focus_descriptor_for_report_name(clean_report_name)
	if statement_focus:
		return {
			"surface_class": "statement",
			"focus_kind": _clean_text(statement_focus.get("focus_kind")) or "statement",
			"focus_grain": _clean_text(statement_focus.get("focus_grain")),
			"focus_label": _clean_text(statement_focus.get("focus_label")) or clean_report_name,
			"focus_key": _clean_text(statement_focus.get("focus_key")) or clean_report_name,
			"source_family_default": "financial_statement",
			"derivation_basis": "statement_grounded_turn",
		}
	is_transaction_listing_surface = bool(
		clean_source_family == "transaction_listing"
		or "transaction_listing" in supported_families
		or listing_view
	)
	is_master_data_surface = bool(
		is_master_data_listing_family(clean_source_family)
		or any(is_master_data_listing_family(family_id) for family_id in supported_families)
		or entity_grain
	)
	if is_master_data_surface and not is_transaction_listing_surface:
		return {
			"surface_class": "master_data_listing",
			"focus_grain": entity_grain or "master_data",
			"source_family_default": "master_data_directory",
			"derivation_basis": "master_data_listing_grounded_turn",
		}
	if is_transaction_listing_surface:
		return {
			"surface_class": "transaction_listing",
			"focus_grain": listing_view or "transaction_listing",
			"source_family_default": "transaction_listing",
			"derivation_basis": "transaction_listing_grounded_turn",
		}
	report_focus = report_recent_focus_descriptor_for_report_name(
		clean_report_name,
		source_family=clean_source_family,
	)
	if clean_source_kind == "report" and report_focus:
		return {
			"surface_class": "report",
			"focus_kind": _clean_text(report_focus.get("focus_kind")) or "report",
			"focus_grain": _clean_text(report_focus.get("focus_grain")),
			"focus_label": _clean_text(report_focus.get("focus_label")) or clean_report_name,
			"focus_key": _clean_text(report_focus.get("focus_key")) or clean_report_name,
			"source_family_default": "report",
			"derivation_basis": "report_grounded_turn",
		}
	return {}


def build_grounded_recent_focus_state_from_surface_descriptor(
	*,
	surface_descriptor: Dict[str, Any],
	source_request_id: str,
	source_family: str = "",
	source_capability: str = "",
	source_report: str = "",
	source_tool_index: int = -1,
) -> Dict[str, Any]:
	descriptor = surface_descriptor if isinstance(surface_descriptor, dict) else {}
	surface_class = _clean_text(descriptor.get("surface_class"))
	if surface_class not in {"entity_detail", "statement", "master_data_listing", "transaction_listing", "report"}:
		return {}
	focus_kind = _clean_text(descriptor.get("focus_kind"))
	focus_grain = _clean_text(descriptor.get("focus_grain"))
	focus_label = _clean_text(descriptor.get("focus_label"))
	focus_key = _clean_text(descriptor.get("focus_key"))
	default_source_family = _clean_text(descriptor.get("source_family_default"))
	derivation_basis = _clean_text(descriptor.get("derivation_basis"))
	scope_id = _clean_text(descriptor.get("scope_id"))
	scope_class = _clean_text(descriptor.get("scope_class"))
	confidence = {
		"entity_detail": 0.9,
		"statement": 0.8,
		"master_data_listing": 0.82,
		"transaction_listing": 0.8,
		"report": 0.76,
	}.get(surface_class, 0.0)
	if surface_class == "entity_detail":
		focus_grain = focus_grain or "entity"
		if not focus_kind:
			focus_kind = "document" if is_detail_capable_document_focus_grain(focus_grain) else "entity"
		derivation_basis = derivation_basis or (
			"document_detail_grounded_turn"
			if focus_kind == "document"
			else "entity_detail_grounded_turn"
		)
		focus_label = focus_label or _clean_text(source_report)
		focus_key = focus_key or focus_label
		explicit_named_allowed = True
		deictic_allowed = True
	elif surface_class == "master_data_listing":
		focus_kind = focus_kind or "listing"
		focus_grain = focus_grain or "master_data"
		focus_label = focus_label or _clean_text(source_report)
		focus_key = focus_key or focus_grain or _clean_text(source_report)
		explicit_named_allowed = False
		deictic_allowed = True
	elif surface_class == "transaction_listing":
		focus_kind = focus_kind or "listing"
		focus_grain = focus_grain or "transaction_listing"
		focus_label = focus_label or _clean_text(source_report)
		focus_key = focus_key or focus_grain or _clean_text(source_report)
		explicit_named_allowed = False
		deictic_allowed = True
	elif surface_class == "statement":
		focus_kind = focus_kind or "statement"
		focus_label = focus_label or _clean_text(source_report)
		focus_key = focus_key or _clean_text(source_report)
		explicit_named_allowed = True
		deictic_allowed = False
	else:
		focus_kind = focus_kind or "report"
		focus_label = focus_label or _clean_text(source_report)
		focus_key = focus_key or _clean_text(source_report)
		explicit_named_allowed = True
		deictic_allowed = True
	if not focus_kind or not focus_label:
		return {}
	return {
		"available": True,
		"focus_kind": focus_kind,
		"focus_grain": focus_grain,
		"focus_label": focus_label,
		"focus_key": focus_key,
		"source_request_id": _clean_text(source_request_id),
		"source_family": _clean_text(source_family) or default_source_family,
		"source_capability": _clean_text(source_capability),
		"source_report": _clean_text(source_report),
		"scope_id": scope_id,
		"scope_class": scope_class,
		"deictic_allowed": deictic_allowed,
		"explicit_named_allowed": explicit_named_allowed,
		"derivation_basis": derivation_basis,
		"confidence": confidence,
		"source_tool_index": source_tool_index,
	}


def build_single_row_document_recent_focus_state(
	*,
	focus_grain: str,
	focus_label: str,
	focus_key: str,
	source_request_id: str,
	source_family: str = "",
	source_capability: str = "",
	source_report: str = "",
	source_tool_index: int = -1,
) -> Dict[str, Any]:
	label = _clean_text(focus_label)
	key = _clean_text(focus_key) or label
	return {
		"available": bool(label),
		"focus_kind": "document",
		"focus_grain": _clean_text(focus_grain),
		"focus_label": label,
		"focus_key": key,
		"source_request_id": _clean_text(source_request_id),
		"source_family": _clean_text(source_family) or "transaction_listing",
		"source_capability": _clean_text(source_capability),
		"source_report": _clean_text(source_report),
		"deictic_allowed": True,
		"explicit_named_allowed": True,
		"derivation_basis": "transaction_single_row_grounded_turn",
		"confidence": 0.86,
		"source_tool_index": source_tool_index,
	}


def build_single_row_entity_recent_focus_state(
	*,
	focus_grain: str,
	focus_label: str,
	focus_key: str,
	source_request_id: str,
	source_family: str = "",
	source_capability: str = "",
	source_report: str = "",
	source_tool_index: int = -1,
) -> Dict[str, Any]:
	label = _clean_text(focus_label)
	key = _clean_text(focus_key) or label
	return {
		"available": bool(label),
		"focus_kind": "entity",
		"focus_grain": _clean_text(focus_grain),
		"focus_label": label,
		"focus_key": key,
		"source_request_id": _clean_text(source_request_id),
		"source_family": _clean_text(source_family) or "master_data_directory",
		"source_capability": _clean_text(source_capability),
		"source_report": _clean_text(source_report),
		"deictic_allowed": True,
		"explicit_named_allowed": True,
		"derivation_basis": "master_data_single_row_grounded_turn",
		"confidence": 0.88,
		"source_tool_index": source_tool_index,
	}


def single_row_focus_candidate_value(row: Dict[str, Any], candidate_columns: List[str]) -> str:
	if not isinstance(row, dict) or not row:
		return ""
	for column in candidate_columns:
		value = _clean_text(row.get(column))
		if value:
			return value
	return ""


def document_single_row_focus_label(*, focus_grain: str, row: Dict[str, Any], source_report: str = "") -> str:
	grain = _clean_text(focus_grain)
	candidate_columns = document_recent_focus_row_candidate_columns(
		focus_grain=grain,
		source_report=_clean_text(source_report),
	)
	if not candidate_columns:
		return ""
	return single_row_focus_candidate_value(
		row,
		candidate_columns,
	)


def document_single_row_focus_key(*, focus_grain: str, row: Dict[str, Any], label: str, source_report: str = "") -> str:
	grain = _clean_text(focus_grain)
	candidate_columns = document_recent_focus_row_candidate_columns(
		focus_grain=grain,
		source_report=_clean_text(source_report),
	)
	if not candidate_columns:
		return _clean_text(label)
	value = single_row_focus_candidate_value(
		row,
		candidate_columns,
	)
	return value or _clean_text(label)


def single_row_transaction_document_recent_focus(
	*,
	grounded_payload: Dict[str, Any],
	focus_grain: str,
	source_name: str,
	family_id: str,
	source_request_id: str = "",
	source_capability: str = "",
	source_tool_index: int = -1,
) -> Dict[str, Any]:
	rows = grounded_payload.get("table_rows") if isinstance(grounded_payload.get("table_rows"), list) else []
	if len(rows) != 1 or not isinstance(rows[0], dict):
		return {}
	grain = _clean_text(focus_grain)
	if not is_detail_capable_document_focus_grain(grain):
		return {}
	row = dict(rows[0] or {})
	focus_label = document_single_row_focus_label(
		focus_grain=grain,
		row=row,
		source_report=source_name,
	)
	if not focus_label:
		return {}
	focus_key = document_single_row_focus_key(
		focus_grain=grain,
		row=row,
		label=focus_label,
		source_report=source_name,
	)
	return build_single_row_document_recent_focus_state(
		focus_grain=grain,
		focus_label=focus_label,
		focus_key=focus_key,
		source_request_id=_clean_text(source_request_id),
		source_family=family_id or "transaction_listing",
		source_capability=_clean_text(source_capability),
		source_report=source_name,
		source_tool_index=source_tool_index,
	)


def master_data_single_row_focus_label(
	*,
	focus_grain: str,
	row: Dict[str, Any],
	source_report: str = "",
) -> str:
	if not isinstance(row, dict) or not row:
		return ""
	candidate_columns = master_data_recent_focus_row_label_columns(
		focus_grain=_clean_text(focus_grain),
		source_report=_clean_text(source_report),
	)
	return single_row_focus_candidate_value(row, candidate_columns)


def master_data_single_row_focus_key(
	*,
	focus_grain: str,
	row: Dict[str, Any],
	label: str,
	source_report: str = "",
) -> str:
	if not isinstance(row, dict) or not row:
		return _clean_text(label)
	candidate_columns = master_data_recent_focus_row_key_columns(
		focus_grain=_clean_text(focus_grain),
		source_report=_clean_text(source_report),
	)
	value = single_row_focus_candidate_value(row, candidate_columns)
	if value:
		return value
	return _clean_text(label)


def single_row_master_data_entity_recent_focus(
	*,
	grounded_payload: Dict[str, Any],
	focus_grain: str,
	source_name: str,
	family_id: str,
	source_request_id: str = "",
	source_capability: str = "",
	source_tool_index: int = -1,
) -> Dict[str, Any]:
	rows = grounded_payload.get("table_rows") if isinstance(grounded_payload.get("table_rows"), list) else []
	if len(rows) != 1 or not isinstance(rows[0], dict):
		return {}
	row = dict(rows[0] or {})
	focus_label = master_data_single_row_focus_label(
		focus_grain=focus_grain,
		row=row,
		source_report=source_name,
	)
	if not focus_label:
		return {}
	focus_key = master_data_single_row_focus_key(
		focus_grain=focus_grain,
		row=row,
		label=focus_label,
		source_report=source_name,
	)
	return build_single_row_entity_recent_focus_state(
		focus_grain=focus_grain,
		focus_label=focus_label,
		focus_key=focus_key,
		source_request_id=_clean_text(source_request_id),
		source_family=family_id or "master_data_directory",
		source_capability=_clean_text(source_capability),
		source_report=source_name,
		source_tool_index=source_tool_index,
	)


def empty_recent_focus_state() -> Dict[str, Any]:
	return {
		"available": False,
		"focus_kind": "",
		"focus_grain": "",
		"focus_label": "",
		"focus_key": "",
		"source_request_id": "",
		"source_family": "",
		"source_capability": "",
		"source_report": "",
		"deictic_allowed": False,
		"explicit_named_allowed": False,
		"derivation_basis": "none",
		"confidence": 0.0,
		"source_tool_index": -1,
	}


_RUNTIME_POLICY_MODE_ALIASES = {
	"column_projection": "column_refinement",
	"time_scope_restatement": "time_refinement",
}


def _normalize_policy_followup_mode(mode: str) -> str:
	clean_mode = _clean_text(mode)
	if not clean_mode:
		return ""
	normalized = normalize_followup_mode_for_runtime(clean_mode)
	normalized = _clean_text(normalized) or clean_mode
	return _RUNTIME_POLICY_MODE_ALIASES.get(normalized, normalized)


def _recent_focus_scope_id(recent_focus_state: Dict[str, Any]) -> str:
	explicit_scope_id = _clean_text((recent_focus_state or {}).get("scope_id"))
	if explicit_scope_id:
		return explicit_scope_id
	source_report = _clean_text((recent_focus_state or {}).get("source_report"))
	if source_report:
		report_scope_id = scope_id_for_report_name(source_report)
		if report_scope_id:
			return report_scope_id
	focus_grain = _clean_text((recent_focus_state or {}).get("focus_grain"))
	if not focus_grain:
		return ""
	focus_kind = _clean_text((recent_focus_state or {}).get("focus_kind"))
	if focus_kind == "listing":
		listing_scope_id = scope_id_for_listing_view(focus_grain)
		if listing_scope_id:
			return listing_scope_id
	entity_scope_id = scope_id_for_entity_grain(focus_grain)
	if entity_scope_id:
		return entity_scope_id
	return scope_id_for_listing_view(focus_grain)


def _scope_followup_boundary_modes(scope_id: str) -> List[str]:
	if not _clean_text(scope_id):
		return []
	policy = governed_scope_runtime_policy(scope_id, "followup_boundary")
	if not isinstance(policy, dict):
		return []
	compatibility_level = _clean_text(policy.get("compatibility_level"))
	followup_compatibility = _clean_text(policy.get("followup_compatibility"))
	if compatibility_level not in {"followup_only", "full_consumption"}:
		return []
	if followup_compatibility not in {"preserve_scope", "requery_same_scope"}:
		return []
	return [
		normalized
		for normalized in [
			_normalize_policy_followup_mode(_clean_text(value))
			for value in _clean_list(policy.get("allowed_modes"))
		]
		if normalized
	]


def _runtime_policy_supports_full_consumption(scope_id: str, family_id: str) -> bool:
	policy = governed_scope_runtime_policy(scope_id, family_id)
	if not isinstance(policy, dict):
		return False
	return _clean_text(policy.get("compatibility_level")) == "full_consumption"


def recent_focus_listing_detail_parity_state(recent_focus_state: Dict[str, Any]) -> Dict[str, Any]:
	if not isinstance(recent_focus_state, dict) or not bool(recent_focus_state.get("available")):
		return {
			"listing_supported": False,
			"detail_supported": False,
			"listing_detail_support_status": "neither",
		}
	focus_kind = _clean_text(recent_focus_state.get("focus_kind"))
	source_family = _clean_text(recent_focus_state.get("source_family"))
	scope_id = _recent_focus_scope_id(recent_focus_state)
	listing_supported = False
	detail_supported = False
	if focus_kind == "listing":
		listing_supported = True
		if scope_id:
			detail_supported = _runtime_policy_supports_full_consumption(scope_id, "entity_detail")
	elif focus_kind == "entity":
		detail_supported = True
		if scope_id:
			listing_supported = _runtime_policy_supports_full_consumption(scope_id, "master_data_lookup")
	elif focus_kind == "document":
		detail_supported = True
		if scope_id:
			listing_supported = _runtime_policy_supports_full_consumption(scope_id, "transaction_listing")
	elif is_master_data_listing_family(source_family):
		listing_supported = True
		if scope_id:
			detail_supported = _runtime_policy_supports_full_consumption(scope_id, "entity_detail")
	elif source_family == "transaction_listing":
		listing_supported = True
		if scope_id:
			detail_supported = _runtime_policy_supports_full_consumption(scope_id, "entity_detail")
	status = (
		"both"
		if listing_supported and detail_supported
		else "listing_only"
		if listing_supported
		else "detail_only"
		if detail_supported
		else "neither"
	)
	return {
		"listing_supported": listing_supported,
		"detail_supported": detail_supported,
		"listing_detail_support_status": status,
	}


def _report_followup_modes(source_report: str) -> List[str]:
	return [
		normalized
		for normalized in [
			_normalize_policy_followup_mode(_clean_text(value))
			for value in report_approved_followup_modes(source_report)
		]
		if normalized
	]


def _listing_selection_action_class(recent_focus_state: Dict[str, Any]) -> str:
	parity_state = recent_focus_listing_detail_parity_state(recent_focus_state)
	if not bool(parity_state.get("detail_supported")):
		return ""
	scope_id = _recent_focus_scope_id(recent_focus_state)
	if scope_id:
		detail_policy = governed_scope_runtime_policy(scope_id, "entity_detail")
		allowed_modes = set(_clean_list((detail_policy or {}).get("allowed_modes")))
		if "profile_target" in allowed_modes:
			return "entity_selection_followup"
		if allowed_modes.intersection({"document_detail", "profile_section_evidence"}):
			return "document_selection_followup"
	focus_grain = _clean_text((recent_focus_state or {}).get("focus_grain"))
	if focus_grain in {"customer", "supplier"} or is_item_product_grain(focus_grain):
		return "entity_selection_followup"
	return "document_selection_followup"


def recent_focus_allowed_action_classes(recent_focus_state: Dict[str, Any]) -> List[str]:
	if not isinstance(recent_focus_state, dict) or not bool(recent_focus_state.get("available")):
		return []
	focus_kind = _clean_text(recent_focus_state.get("focus_kind"))
	focus_grain = _clean_text(recent_focus_state.get("focus_grain"))
	action_classes: List[str] = []
	if focus_kind == "entity":
		action_classes.extend(
			[
				"detail_followup",
				"projection_refinement",
				"time_refinement",
				"sibling_view_switch",
			]
		)
		if is_item_product_grain(focus_grain):
			action_classes.append("inventory_position_followup")
		if focus_grain in {"customer", "supplier"}:
			action_classes.append("commercial_status_followup")
		if focus_grain in set(customer_lifecycle_supported_focus_grains()):
			action_classes.append("lifecycle_basis_followup")
	elif focus_kind == "document":
		action_classes.extend(
			[
				"detail_followup",
				"projection_refinement",
				"time_refinement",
				"linked_document_navigation",
				"document_status_followup",
			]
		)
		if focus_grain in set(document_event_supported_focus_grains()):
			action_classes.append("document_event_followup")
	elif focus_kind == "statement":
		action_classes.extend(
			[
				"statement_switch",
				"line_item_followup",
				"projection_refinement",
				"time_refinement",
			]
		)
	elif focus_kind == "listing":
		action_classes.extend(
			[
				"listing_refinement",
				"projection_refinement",
				"time_refinement",
			]
		)
		selection_action = _listing_selection_action_class(recent_focus_state)
		if selection_action:
			action_classes.append(selection_action)
	elif focus_kind == "report":
		action_classes.extend(
			[
				"report_refinement",
				"metric_refinement",
				"projection_refinement",
				"time_refinement",
				"detail_navigation",
			]
		)
	return list(dict.fromkeys(action_classes))


def recent_focus_followup_mode_partition(recent_focus_state: Dict[str, Any]) -> Tuple[List[str], List[str]]:
	if not isinstance(recent_focus_state, dict) or not bool(recent_focus_state.get("available")):
		return [], []
	focus_kind = _clean_text(recent_focus_state.get("focus_kind"))
	source_report = _clean_text(recent_focus_state.get("source_report"))
	approved_modes: List[str] = []
	if focus_kind == "listing":
		approved_modes.extend(_scope_followup_boundary_modes(_recent_focus_scope_id(recent_focus_state)))
	approved_modes.extend(_report_followup_modes(source_report))
	approved_modes = list(dict.fromkeys(mode for mode in approved_modes if _clean_text(mode)))
	if not approved_modes:
		if focus_kind in {"listing", "statement", "report"}:
			# Generated or family-backed focus labels can still support bounded
			# shared continuation even when they are not individually registry-backed.
			approved_modes = ["new_query"]
	elif focus_kind in {"listing", "statement", "report"} and "new_query" not in approved_modes:
		approved_modes.append("new_query")
	local_modes = [mode for mode in approved_modes if mode in _LOCAL_RECENT_FOCUS_FOLLOWUP_MODES]
	requery_modes = [mode for mode in approved_modes if mode not in _LOCAL_RECENT_FOCUS_FOLLOWUP_MODES]
	return local_modes, requery_modes


def recent_focus_affordance_reason(recent_focus_state: Dict[str, Any]) -> str:
	focus_kind = _clean_text((recent_focus_state or {}).get("focus_kind"))
	if focus_kind == "entity":
		return "The recent focus is a specific ERP entity, so follow-up can stay on that entity or pivot to supported sibling views."
	if focus_kind == "document":
		return "The recent focus is a specific ERP document, so follow-up can stay on that document or move to supported linked-document views."
	if focus_kind == "statement":
		return "The recent focus is a financial statement, so follow-up can stay on the same statement or move to a supported statement view."
	if focus_kind == "listing":
		return "The recent focus is a governed list, so follow-up can refine the list or navigate into a supported detail target."
	if focus_kind == "report":
		return "The recent focus is a governed report view, so follow-up can refine the report or navigate into supported downstream detail."
	return "The recent focus exposes a bounded follow-up surface."


def recent_focus_reference_terms(recent_focus_state: Dict[str, Any]) -> Dict[str, List[str]]:
	if not isinstance(recent_focus_state, dict) or not bool(recent_focus_state.get("available")):
		return {}
	focus_kind = _clean_text(recent_focus_state.get("focus_kind"))
	focus_grain = normalize_item_product_grain(_clean_text(recent_focus_state.get("focus_grain")))
	focus_label = _clean_text(recent_focus_state.get("focus_label"))
	focus_key = _clean_text(recent_focus_state.get("focus_key"))
	source_report = _clean_text(recent_focus_state.get("source_report"))
	entity_terms: List[str] = []
	collection_terms: List[str] = []
	explicit_terms: List[str] = []
	if focus_grain == "customer":
		entity_terms = ["that customer", "this customer", "the customer"]
		collection_terms = ["that customer list", "the customer list", "customer directory", "customers"]
	elif focus_grain == "supplier":
		entity_terms = ["that supplier", "this supplier", "the supplier"]
		collection_terms = ["that supplier list", "the supplier list", "supplier directory", "suppliers"]
	elif focus_grain == "item":
		entity_terms = ["that item", "this item", "the item", "that product", "this product", "the product"]
		collection_terms = ["that item list", "the item list", "that product list", "the product list", "items", "products"]
	if focus_kind == "document":
		entity_terms = ["that document", "this document", "that entry", "this entry", "that invoice", "this invoice", "that order", "this order"]
	if focus_kind == "statement":
		entity_terms = ["that statement", "this statement", "the statement"]
		collection_terms = ["financial statements", "statement list"]
	if focus_kind == "report":
		entity_terms = ["that report", "this report", "that view", "this view"]
	if focus_kind == "listing" and not collection_terms:
		collection_terms = ["that list", "this list", "the list", "that directory", "this directory"]
	if focus_kind in {"entity", "document", "statement", "report"}:
		_extend_unique(explicit_terms, [focus_label, focus_key, source_report])
	else:
		_extend_unique(explicit_terms, [source_report, focus_label, focus_key])
	deictic_terms: List[str] = []
	if bool(recent_focus_state.get("deictic_allowed")):
		if focus_kind == "listing":
			_extend_unique(deictic_terms, collection_terms or ["that list", "this list", "the list"])
		else:
			_extend_unique(deictic_terms, entity_terms or ["that one", "this one"])
	if focus_kind == "listing":
		_extend_unique(deictic_terms, ["that one", "this one"])
	elif focus_kind in {"entity", "document"}:
		_extend_unique(deictic_terms, ["that one", "this one"])
	reference_terms = {
		"deictic_terms": deictic_terms,
		"entity_reference_terms": entity_terms,
		"collection_reference_terms": collection_terms,
		"explicit_reference_terms": explicit_terms if bool(recent_focus_state.get("explicit_named_allowed")) else [],
	}
	return {
		key: list(dict.fromkeys(value for value in values if _clean_text(value)))
		for key, values in reference_terms.items()
		if values
	}


def enrich_recent_focus_state_with_affordance(
	recent_focus_state: Dict[str, Any],
	recent_focus_affordance_payload: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	if not isinstance(recent_focus_state, dict) or not bool(recent_focus_state.get("available")):
		return {}
	enriched_state = dict(recent_focus_state or {})
	affordance_payload = (
		recent_focus_affordance_payload
		if isinstance(recent_focus_affordance_payload, dict)
		else {}
	)
	if "deictic_reference_allowed" in affordance_payload:
		enriched_state["deictic_allowed"] = bool(affordance_payload.get("deictic_reference_allowed"))
	if "explicit_named_reference_allowed" in affordance_payload:
		enriched_state["explicit_named_allowed"] = bool(
			affordance_payload.get("explicit_named_reference_allowed")
		)
	if "listing_supported" in affordance_payload:
		enriched_state["listing_supported"] = bool(affordance_payload.get("listing_supported"))
	if "detail_supported" in affordance_payload:
		enriched_state["detail_supported"] = bool(affordance_payload.get("detail_supported"))
	if "listing_detail_support_status" in affordance_payload:
		enriched_state["listing_detail_support_status"] = _clean_text(
			affordance_payload.get("listing_detail_support_status")
		)
	if isinstance(affordance_payload.get("reference_terms"), dict):
		enriched_state["reference_terms"] = dict(affordance_payload.get("reference_terms") or {})
	return enriched_state


def conversation_control_focus_target_from_recent_focus_state(
	recent_focus_state: Dict[str, Any],
	recent_focus_affordance_payload: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	if not isinstance(recent_focus_state, dict) or not bool(recent_focus_state.get("available")):
		return {}
	enriched_state = enrich_recent_focus_state_with_affordance(
		recent_focus_state,
		recent_focus_affordance_payload=recent_focus_affordance_payload,
	)
	return {
		"focus_kind": _clean_text(enriched_state.get("focus_kind")),
		"focus_grain": _clean_text(enriched_state.get("focus_grain")),
		"focus_label": _clean_text(enriched_state.get("focus_label")),
		"focus_key": _clean_text(enriched_state.get("focus_key")),
		"scope_id": _clean_text(enriched_state.get("scope_id")),
		"scope_class": _clean_text(enriched_state.get("scope_class")),
		"source_request_id": _clean_text(enriched_state.get("source_request_id")),
		"source_family": _clean_text(enriched_state.get("source_family")),
		"source_capability": _clean_text(enriched_state.get("source_capability")),
		"source_report": _clean_text(enriched_state.get("source_report")),
		"deictic_allowed": bool(enriched_state.get("deictic_allowed")),
		"explicit_named_allowed": bool(enriched_state.get("explicit_named_allowed")),
		"listing_supported": bool(enriched_state.get("listing_supported")),
		"detail_supported": bool(enriched_state.get("detail_supported")),
		"listing_detail_support_status": _clean_text(enriched_state.get("listing_detail_support_status")),
		"reference_terms": dict(enriched_state.get("reference_terms") or recent_focus_reference_terms(enriched_state)),
	}


def recent_focus_continuation_reason_from_selection(selection: Dict[str, Any]) -> str:
	basis = _clean_text((selection or {}).get("basis"))
	if basis == "shared_affordance_passthrough":
		return "The follow-up stays on the latest grounded business focus through the shared recent-focus affordance surface."
	return "The follow-up was safely expanded using the latest grounded business focus."


def recent_focus_continuation_eligibility(
	*,
	raw_message: str,
	runtime_message: str,
	recent_focus_state: Dict[str, Any],
	followup_resolution,
	has_strong_control_owner: bool,
	routing_basis: str = "",
) -> Dict[str, Any]:
	normalized_runtime_message = _normalize_text(runtime_message)
	normalized_raw_message = _normalize_text(raw_message)
	allow_passthrough = _clean_text(routing_basis) == "shared_affordance"
	return _select_recent_focus_continuation_eligibility_helper(
		has_runtime_message=bool(_clean_text(runtime_message)),
		runtime_matches_raw_without_passthrough=normalized_runtime_message == normalized_raw_message and not allow_passthrough,
		has_strong_control_owner=bool(has_strong_control_owner),
		has_recent_focus=bool(isinstance(recent_focus_state, dict) and recent_focus_state.get("available")),
		has_followup_resolution=followup_resolution is not None,
		followup_mode=_clean_text(getattr(followup_resolution, "mode", "")) if followup_resolution is not None else "",
		depends_on_grounded_turn=bool(getattr(followup_resolution, "depends_on_grounded_turn", False)) if followup_resolution is not None else False,
		allow_passthrough=allow_passthrough,
	)


def recent_focus_runtime_routing_permissions(
	*,
	recent_focus_state: Dict[str, Any],
	requested_modes: List[str],
	allowed_local_followup_modes: List[str],
	allowed_requery_followup_modes: List[str],
	supports_cross_family_followup: bool,
	detail_supported: bool = False,
) -> Dict[str, bool]:
	requested_mode_set = {
		_clean_text(value)
		for value in (requested_modes or [])
		if _clean_text(value)
	}
	allowed_local_mode_set = {
		_clean_text(value)
		for value in (allowed_local_followup_modes or [])
		if _clean_text(value)
	}
	allowed_requery_mode_set = {
		_clean_text(value)
		for value in (allowed_requery_followup_modes or [])
		if _clean_text(value)
	}
	local_transform_allowed = bool(requested_mode_set.intersection(allowed_local_mode_set))
	requery_allowed = bool(requested_mode_set.intersection(allowed_requery_mode_set))
	focus_kind = _clean_text((recent_focus_state or {}).get("focus_kind"))
	if (
		not local_transform_allowed
		and focus_kind in {"entity", "document"}
		and bool(
			(recent_focus_state or {}).get("deictic_allowed")
			or (recent_focus_state or {}).get("explicit_named_allowed")
		)
	):
		local_transform_allowed = True
	if (
		not local_transform_allowed
		and focus_kind == "listing"
		and bool(detail_supported)
		and bool((recent_focus_state or {}).get("deictic_allowed"))
	):
		local_transform_allowed = True
	if not requery_allowed and "new_query" in requested_mode_set:
		requery_allowed = bool(supports_cross_family_followup)
	return {
		"local_transform_allowed": local_transform_allowed,
		"requery_allowed": requery_allowed,
	}


def recent_focus_runtime_route_selection(
	*,
	recent_focus_state: Dict[str, Any],
	followup_resolution,
	recent_focus_affordance_contract,
) -> Dict[str, Any]:
	followup_mode = _clean_text(getattr(followup_resolution, "mode", ""))
	if followup_mode not in {"new_query", "grounded_follow_up", "local_grounded_transform"}:
		return {
			"eligible": False,
			"requested_modes": [],
			"local_transform_allowed": False,
			"requery_allowed": False,
		}
	if not bool(getattr(followup_resolution, "depends_on_grounded_turn", False)):
		return {
			"eligible": False,
			"requested_modes": [],
			"local_transform_allowed": False,
			"requery_allowed": False,
		}
	requested_modes = [
		_clean_text(value)
		for value in (getattr(followup_resolution, "requested_modes", []) or [])
		if _clean_text(value)
	]
	if followup_mode and followup_mode not in requested_modes:
		requested_modes.insert(0, followup_mode)
	requested_modes = list(dict.fromkeys(requested_modes))
	routing_permissions = recent_focus_runtime_routing_permissions(
		recent_focus_state=recent_focus_state,
		requested_modes=requested_modes,
		allowed_local_followup_modes=list(
			getattr(recent_focus_affordance_contract, "allowed_local_followup_modes", []) or []
		),
		allowed_requery_followup_modes=list(
			getattr(recent_focus_affordance_contract, "allowed_requery_followup_modes", []) or []
		),
		supports_cross_family_followup=bool(
			getattr(recent_focus_affordance_contract, "supports_cross_family_followup", False)
		),
		detail_supported=bool(
			getattr(recent_focus_affordance_contract, "detail_supported", False)
		),
	)
	return {
		"eligible": True,
		"requested_modes": requested_modes,
		"local_transform_allowed": bool(routing_permissions.get("local_transform_allowed")),
		"requery_allowed": bool(routing_permissions.get("requery_allowed")),
	}


def build_recent_focus_continuation_decision_spec(
	*,
	recent_focus_state: Dict[str, Any],
	selection: Dict[str, Any],
	followup_resolution,
	recent_focus_affordance_payload: Dict[str, Any],
	control_action_id: str,
	raw_message: str,
	routing_basis: str,
) -> Dict[str, Any]:
	confidence = float(max(0.0, min(1.0, (recent_focus_state or {}).get("confidence", 0.0) or 0.0)))
	return {
		"reason": recent_focus_continuation_reason_from_selection(selection),
		"resolved_focus_target": conversation_control_focus_target_from_recent_focus_state(
			recent_focus_state,
			recent_focus_affordance_payload=recent_focus_affordance_payload,
		),
		"confidence": confidence,
		"internal_details": {
			"source_contract_type": "qwen_conversation_state_snapshot",
			"followup_mode": _clean_text(getattr(followup_resolution, "mode", "")),
			"depends_on_grounded_turn": bool(getattr(followup_resolution, "depends_on_grounded_turn", False)),
			"routing_basis": _clean_text(routing_basis) or "local_transform",
			"control_action_id": _clean_text(control_action_id),
			"recent_focus_affordance": dict(recent_focus_affordance_payload or {}),
			"user_message": _clean_text(raw_message),
		},
	}


def build_prior_branch_restore_recent_focus_projection(
	*,
	request_id: str,
	prior_branch_restore_contract,
) -> Dict[str, Any]:
	recent_focus_state = _recent_focus_state_from_prior_branch_restore_contract_helper(prior_branch_restore_contract)
	if not recent_focus_state:
		return {
			"restored_recent_focus_state": {},
			"runtime_override_message": "",
			"resolved_focus_target": {},
			"recent_focus_affordance_payload": {},
		}
	recent_focus_affordance_contract = build_recent_focus_affordance_contract_from_snapshot(
		request_id=request_id,
		recent_focus_state=recent_focus_state,
	)
	recent_focus_affordance_payload = (
		recent_focus_affordance_contract.to_payload() if recent_focus_affordance_contract is not None else {}
	)
	enriched_recent_focus_state = enrich_recent_focus_state_with_affordance(
		recent_focus_state,
		recent_focus_affordance_payload=recent_focus_affordance_payload,
	)
	return {
		"restored_recent_focus_state": dict(enriched_recent_focus_state or {}),
		"runtime_override_message": _recent_focus_restore_runtime_message_helper(
			recent_focus_state=enriched_recent_focus_state
		),
		"resolved_focus_target": conversation_control_focus_target_from_recent_focus_state(
			enriched_recent_focus_state,
			recent_focus_affordance_payload=recent_focus_affordance_payload,
		),
		"recent_focus_affordance_payload": recent_focus_affordance_payload,
	}


def build_recent_focus_affordance_contract_from_snapshot(
	*,
	request_id: str,
	recent_focus_state: Dict[str, Any],
):
	if not isinstance(recent_focus_state, dict) or not bool(recent_focus_state.get("available")):
		return None
	local_modes, requery_modes = recent_focus_followup_mode_partition(recent_focus_state)
	parity_state = recent_focus_listing_detail_parity_state(recent_focus_state)
	return build_recent_focus_affordance_contract(
		request_id=request_id,
		focus_kind=_clean_text(recent_focus_state.get("focus_kind")),
		focus_grain=_clean_text(recent_focus_state.get("focus_grain")),
		focus_label=_clean_text(recent_focus_state.get("focus_label")),
		source_family=_clean_text(recent_focus_state.get("source_family")),
		source_capability=_clean_text(recent_focus_state.get("source_capability")),
		source_report=_clean_text(recent_focus_state.get("source_report")),
		allowed_action_classes=recent_focus_allowed_action_classes(recent_focus_state),
		allowed_local_followup_modes=local_modes,
		allowed_requery_followup_modes=requery_modes,
		deictic_reference_allowed=bool(recent_focus_state.get("deictic_allowed")),
		explicit_named_reference_allowed=bool(recent_focus_state.get("explicit_named_allowed")),
		supports_cross_family_followup=bool(requery_modes),
		listing_supported=bool(parity_state.get("listing_supported")),
		detail_supported=bool(parity_state.get("detail_supported")),
		listing_detail_support_status=_clean_text(parity_state.get("listing_detail_support_status")),
		reference_terms=recent_focus_reference_terms(recent_focus_state),
		reason=recent_focus_affordance_reason(recent_focus_state),
	)
