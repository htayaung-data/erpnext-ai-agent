from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Tuple

from .metadata import (
	get_report_spec,
	load_report_registry,
	report_defaultable_filters,
	report_direct_query_fields,
	report_supported_dimensions,
)
from .natural_business_understanding_context_resolution import nbu_artifact_rows
from .natural_business_understanding_contracts import CONTRACT_VERSION
from .semantic_aliases import detect_canonical_keys
from .visible_context_boundary_language import render_missing_field_boundary


FILTER_READINESS_CONTRACT_TYPE = "qwen_filter_readiness_contract"


_REPORT_NAME_KEYS = {
	"report",
	"report_name",
	"report_names",
	"source_report",
	"source_reports",
	"source_report_name",
	"source_report_names",
}

_REPORT_CONTAINER_KEYS = {
	"artifact",
	"authority",
	"authority_plan",
	"context",
	"dimensions",
	"filters",
	"metadata",
	"payload",
	"report_context",
	"source",
}

_REQUESTED_FIELD_HINTS: Tuple[Tuple[str, str], ...] = (
	(r"\bterritor(?:y|ies)\b|\bregion(?:s|al)?\b|\byangon\b|\bmandalay\b|\bnay\s*pyi\s*taw\b", "territory"),
	(r"\bcustomers?\b|\bclient(?:s)?\b", "customer"),
	(r"\bsuppliers?\b|\bvendors?\b", "supplier"),
	(r"\bproducts?\b|\bitems?\b|\bsku(?:s)?\b", "product"),
	(r"\bitem\s+groups?\b|\bproduct\s+categor(?:y|ies)\b|\bcategor(?:y|ies)\b", "item_group"),
	(r"\bwarehouses?\b|\blocations?\b", "warehouse"),
	(r"\baccounts?\b|\bledger\b", "account"),
	(r"\bbuckets?\b|\baging\s+buckets?\b", "aging_bucket"),
	(r"\bsource\s+documents?\b|\bdocuments?\b|\bvouchers?\b|\binvoices?\b", "source_document"),
	(r"\bposting\s+date\b|\bdue\s+date\b|\bdate\b|\bperiod\b", "date"),
)

_FIELD_EQUIVALENCE_GROUPS: Tuple[Tuple[str, ...], ...] = (
	("product", "item", "item_code", "item_name"),
	("source_document", "document", "document_name", "voucher", "voucher_no"),
	("invoice", "purchase_invoice", "sales_invoice"),
	("customer", "customer_name"),
	("supplier", "supplier_name"),
	("territory", "region"),
	("warehouse", "warehouse_name"),
	("account", "account_name"),
	("date", "posting_date", "due_date", "transaction_date"),
)


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def normalize_filter_field_key(value: Any) -> str:
	text = re.sub(r"\([^)]*\)", "", _clean_text(value).lower())
	text = re.sub(r"[^a-z0-9]+", "_", text)
	return re.sub(r"_+", "_", text).strip("_")


def _humanize(key: str) -> str:
	text = re.sub(r"_+", " ", _clean_text(key)).strip()
	return text or _clean_text(key)


def filter_field_label(key: str) -> str:
	return _humanize(key).title()


def _equivalent_keys(key: str) -> List[str]:
	normalized = normalize_filter_field_key(key)
	if not normalized:
		return []
	for group in _FIELD_EQUIVALENCE_GROUPS:
		if normalized in group:
			return list(group)
	return [normalized]


def _matched_available_key(key: str, available_keys: Iterable[str]) -> str:
	available = set(_unique_normalized(available_keys))
	for candidate in _equivalent_keys(key):
		if candidate in available:
			return candidate
	return ""


def _collapse_requested_keys(
	requested_keys: Iterable[str],
	*,
	visible_keys: Iterable[str],
	source_field_keys: Iterable[str],
) -> List[str]:
	out: List[str] = []
	for key in requested_keys:
		preferred = (
			_matched_available_key(key, visible_keys)
			or _matched_available_key(key, source_field_keys)
			or normalize_filter_field_key(key)
		)
		if preferred and preferred not in out:
			out.append(preferred)
	return out


def _unique(values: Iterable[str]) -> List[str]:
	out: List[str] = []
	for value in values:
		clean = _clean_text(value)
		if clean and clean not in out:
			out.append(clean)
	return out


def _unique_normalized(values: Iterable[Any]) -> List[str]:
	return _unique(normalize_filter_field_key(value) for value in values)


def _requested_field_keys_from_message(raw_message: str) -> List[str]:
	message = _clean_text(raw_message)
	requested: List[str] = []
	for key in detect_canonical_keys(text=message, dimension_or_metric="dimension"):
		normalized = normalize_filter_field_key(key)
		if normalized:
			requested.append(normalized)
	for pattern, key in _REQUESTED_FIELD_HINTS:
		if re.search(pattern, message, flags=re.IGNORECASE):
			requested.append(key)
	return _remove_report_title_noise(_unique(requested), message)


def _remove_report_title_noise(requested_keys: List[str], raw_message: str) -> List[str]:
	keys = list(requested_keys)
	if "account" in keys:
		message_without_arap_title = re.sub(
			r"\baccounts?\s+(?:receivable|payable)\b",
			" ",
			_clean_text(raw_message),
			flags=re.IGNORECASE,
		)
		if not re.search(r"\baccounts?\b|\bledger\b", message_without_arap_title, flags=re.IGNORECASE):
			keys = [key for key in keys if key != "account"]
	return keys


def _visible_row_field_keys(rows: List[Dict[str, Any]]) -> List[str]:
	keys: List[str] = []
	for row in rows[:10]:
		keys.extend(normalize_filter_field_key(key) for key in _clean_dict(row).keys())
	return _unique(key for key in keys if key)


def _append_report_name(out: List[str], value: Any) -> None:
	if isinstance(value, str):
		clean = _clean_text(value)
		if clean and clean not in out:
			out.append(clean)
		return
	if isinstance(value, dict):
		for key in _REPORT_NAME_KEYS:
			clean = _clean_text(value.get(key))
			if clean and clean not in out:
				out.append(clean)
		return
	if isinstance(value, list):
		for item in value:
			_append_report_name(out, item)


def _known_report_names_in_text(text: str) -> List[str]:
	clean = _clean_text(text).lower()
	if not clean:
		return []
	names: List[str] = []
	for item in load_report_registry().get("reports") or []:
		if not isinstance(item, dict):
			continue
		name = _clean_text(item.get("report_name"))
		if name and name.lower() in clean:
			names.append(name)
	return names


def artifact_report_names(artifact_payload: Dict[str, Any], *, explicit_report_names: Iterable[str] | None = None) -> List[str]:
	artifact = _clean_dict(artifact_payload)
	report_names: List[str] = []
	for value in explicit_report_names or []:
		_append_report_name(report_names, value)
	for key, value in artifact.items():
		if key in _REPORT_NAME_KEYS:
			_append_report_name(report_names, value)
		elif key in _REPORT_CONTAINER_KEYS:
			container = _clean_dict(value)
			for child_key, child_value in container.items():
				if child_key in _REPORT_NAME_KEYS:
					_append_report_name(report_names, child_value)
	for key in ("title", "name", "label", "source_label"):
		report_names.extend(_known_report_names_in_text(_clean_text(artifact.get(key))))
	return _unique(report_names)


def _direct_query_filterable_fields(report_name: str) -> List[str]:
	report_spec = get_report_spec(report_name)
	query_spec = report_spec.get("direct_query") if isinstance(report_spec.get("direct_query"), dict) else {}
	fields = {normalize_filter_field_key(field) for field in report_direct_query_fields(report_name)}
	filterable = _unique_normalized(query_spec.get("filterable_fields") if isinstance(query_spec.get("filterable_fields"), list) else [])
	if not fields:
		return filterable
	return [field for field in filterable if field in fields]


def _defaultable_filter_keys(report_name: str) -> List[str]:
	return _unique_normalized(item.get("fieldname") for item in report_defaultable_filters(report_name))


def _report_metadata_field_sets(report_names: Iterable[str]) -> Dict[str, List[str]]:
	supported_dimensions: List[str] = []
	filterable_fields: List[str] = []
	defaultable_filters: List[str] = []
	direct_query_fields: List[str] = []
	for report_name in report_names:
		supported_dimensions.extend(report_supported_dimensions(report_name))
		filterable_fields.extend(_direct_query_filterable_fields(report_name))
		defaultable_filters.extend(_defaultable_filter_keys(report_name))
		direct_query_fields.extend(report_direct_query_fields(report_name))
	return {
		"supported_dimension_keys": _unique_normalized(supported_dimensions),
		"direct_query_filterable_keys": _unique_normalized(filterable_fields),
		"defaultable_filter_keys": _unique_normalized(defaultable_filters),
		"direct_query_field_keys": _unique_normalized(direct_query_fields),
	}


def build_filter_readiness_contract(
	*,
	raw_message: str = "",
	artifact_payload: Dict[str, Any] | None = None,
	report_name: str = "",
	report_names: Iterable[str] | None = None,
	requested_filter_fields: Iterable[str] | None = None,
) -> Dict[str, Any]:
	artifact = _clean_dict(artifact_payload)
	rows, rows_source = nbu_artifact_rows(artifact)
	explicit_reports = list(report_names or [])
	if report_name:
		explicit_reports.append(report_name)
	source_report_names = artifact_report_names(artifact, explicit_report_names=explicit_reports)
	metadata_fields = _report_metadata_field_sets(source_report_names)
	raw_requested_keys = _unique_normalized(requested_filter_fields or []) or _requested_field_keys_from_message(raw_message)
	visible_keys = _visible_row_field_keys(rows)
	source_field_keys = _unique(
		visible_keys
		+ metadata_fields["supported_dimension_keys"]
		+ metadata_fields["direct_query_field_keys"]
	)
	requested_keys = _collapse_requested_keys(
		raw_requested_keys,
		visible_keys=visible_keys,
		source_field_keys=source_field_keys,
	)

	field_readiness: List[Dict[str, Any]] = []
	for key in requested_keys:
		visible_key = _matched_available_key(key, visible_keys)
		supported_dimension_key = _matched_available_key(key, metadata_fields["supported_dimension_keys"])
		filterable_key = _matched_available_key(key, metadata_fields["direct_query_filterable_keys"])
		defaultable_key = _matched_available_key(key, metadata_fields["defaultable_filter_keys"])
		direct_query_field_key = _matched_available_key(key, metadata_fields["direct_query_field_keys"])
		visible = bool(visible_key)
		supported_dimension = bool(supported_dimension_key)
		filterable = bool(filterable_key)
		defaultable = bool(defaultable_key)
		direct_query_field = bool(direct_query_field_key)
		if visible:
			support_source = "visible_artifact"
		elif filterable:
			support_source = "direct_query_filterable_field"
		elif supported_dimension:
			support_source = "report_supported_dimension"
		elif defaultable:
			support_source = "report_defaultable_filter"
		elif direct_query_field:
			support_source = "direct_query_field"
		else:
			support_source = "unsupported"
		field_readiness.append(
			{
				"field_key": key,
				"field_label": filter_field_label(key),
				"visible_in_artifact": visible,
				"supported_dimension": supported_dimension,
				"direct_query_filterable": filterable,
				"defaultable_filter": defaultable,
				"direct_query_field": direct_query_field,
				"support_source": support_source,
				"matched_visible_field_key": visible_key,
				"matched_metadata_field_key": filterable_key or supported_dimension_key or defaultable_key or direct_query_field_key,
			}
		)

	missing_visible_keys = [item["field_key"] for item in field_readiness if not item["visible_in_artifact"]]
	unsupported_keys = [item["field_key"] for item in field_readiness if item["support_source"] == "unsupported"]
	if not requested_keys:
		status = "no_filter_requested"
		reason = "No filter or field-readiness terms were detected."
	elif not missing_visible_keys:
		status = "ready_from_visible_artifact"
		reason = "All requested fields are visible in the selected artifact."
	elif not unsupported_keys:
		status = "requires_governed_filtered_view"
		reason = "At least one requested field is not visible, but governed metadata can support a filtered or expanded view."
	else:
		status = "missing_filter_evidence"
		reason = "At least one requested field is not visible and is not supported by the selected artifact metadata."

	return {
		"type": FILTER_READINESS_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"status": status,
		"reason": reason,
		"evidence_scope": "visible_artifact_and_report_metadata",
		"requested_filter_keys": requested_keys,
		"requested_filter_labels": [filter_field_label(key) for key in requested_keys],
		"visible_field_keys": visible_keys,
		"visible_field_labels": [filter_field_label(key) for key in visible_keys],
		"missing_visible_field_keys": missing_visible_keys,
		"missing_visible_field_labels": [filter_field_label(key) for key in missing_visible_keys],
		"unsupported_filter_keys": unsupported_keys,
		"unsupported_filter_labels": [filter_field_label(key) for key in unsupported_keys],
		"source_report_names": source_report_names,
		"rows_source": rows_source,
		"source_field_keys": source_field_keys,
		"source_field_labels": [filter_field_label(key) for key in source_field_keys],
		"supported_dimension_keys": metadata_fields["supported_dimension_keys"],
		"direct_query_filterable_keys": metadata_fields["direct_query_filterable_keys"],
		"defaultable_filter_keys": metadata_fields["defaultable_filter_keys"],
		"field_readiness": field_readiness,
	}


def render_filter_readiness_boundary(contract: Dict[str, Any]) -> str:
	source = _clean_dict(contract)
	missing_labels = source.get("missing_visible_field_labels") if isinstance(source.get("missing_visible_field_labels"), list) else []
	visible_labels = source.get("visible_field_labels") if isinstance(source.get("visible_field_labels"), list) else []
	if not missing_labels or not visible_labels:
		return ""
	return render_missing_field_boundary(
		visible_field_labels=[_clean_text(label) for label in visible_labels if _clean_text(label)],
		missing_field_labels=[_clean_text(label) for label in missing_labels if _clean_text(label)],
	)
