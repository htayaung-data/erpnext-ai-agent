from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any, Dict, Tuple

from app.report_registry import (
	approved_modules,
	is_report_approved,
	report_defaultable_filters,
	validate_report_filters,
)
from app.settings import Settings


class ToolGatewayPolicyError(RuntimeError):
	pass


def _normalize_params(params: Any) -> Tuple[Any, Dict[str, Any] | None]:
	if isinstance(params, dict):
		return params, json.loads(json.dumps(params))
	if isinstance(params, str):
		text = str(params or "").strip()
		if not text:
			return params, None
		try:
			parsed = json.loads(text)
		except Exception:
			return params, None
		return params, parsed if isinstance(parsed, dict) else None
	return params, None


def _serialize_like_original(original: Any, params_obj: Dict[str, Any]) -> Any:
	if isinstance(original, str):
		return json.dumps(params_obj, ensure_ascii=False)
	return params_obj


def _normalize_family_tool_context(value: Any) -> Dict[str, Any]:
	if not isinstance(value, dict):
		return {}
	return json.loads(json.dumps(value))


def _family_allowed_report_names(family_tool_context: Dict[str, Any]) -> set[str]:
	values = family_tool_context.get("allowed_report_names")
	if not isinstance(values, list):
		return set()
	return {
		str(item or "").strip().lower()
		for item in values
		if str(item or "").strip()
	}


def _family_report_discovery_allowed(family_tool_context: Dict[str, Any]) -> bool:
	if not family_tool_context:
		return True
	return bool(family_tool_context.get("report_discovery_allowed", True))


def _apply_defaultable_filters(report_name: str, params_obj: Dict[str, Any], settings: Settings) -> Dict[str, Any]:
	filters = params_obj.get("filters")
	if not isinstance(filters, dict):
		return params_obj
	updated = json.loads(json.dumps(params_obj))
	updated_filters = updated.get("filters") or {}
	changed = False
	for item in report_defaultable_filters(report_name):
		fieldname = str(item.get("fieldname") or "").strip()
		strategy = str(item.get("strategy") or "").strip()
		if not fieldname or updated_filters.get(fieldname) not in (None, ""):
			continue
		value = None
		if strategy == "single_company_invariant":
			value = str(settings.erp_default_company or "").strip()
		elif strategy == "current_date":
			value = datetime.now(timezone.utc).date().isoformat()
		elif strategy == "compiler_default":
			value = item.get("value")
		if value in (None, ""):
			continue
		updated_filters[fieldname] = value
		if fieldname == "company" and isinstance(updated.get("company"), str):
			updated["company"] = value
		changed = True
	if not changed:
		return params_obj
	updated["filters"] = updated_filters
	return updated


def _normalize_filters(value: Any) -> Dict[str, Any]:
	if not isinstance(value, dict):
		return {}
	return {
		str(key or "").strip(): value[key]
		for key in value
		if str(key or "").strip()
	}


def _enforce_compiled_query_contract(
	*,
	tool_name: str,
	original_params: Any,
	params_obj: Dict[str, Any],
	compiled_query: Dict[str, Any],
) -> Any:
	name = str(tool_name or "").strip()
	if name != "erp_fac-generate_report":
		raise ToolGatewayPolicyError(
			f"Compiled read mode only allows erp_fac-generate_report, not {name}."
		)

	report_name = str(params_obj.get("report_name") or "").strip()
	expected_report = str(compiled_query.get("selected_report") or "").strip()
	if not report_name or report_name != expected_report:
		raise ToolGatewayPolicyError(
			f"Compiled read mode requires the exact governed report: {expected_report or 'missing'}."
		)

	expected_filters = _normalize_filters(compiled_query.get("filters"))
	actual_filters = _normalize_filters(params_obj.get("filters"))
	if actual_filters != expected_filters:
		raise ToolGatewayPolicyError("Compiled read mode requires exact governed filters.")

	return _serialize_like_original(original_params, params_obj)


def enforce_tool_gateway_policy(
	tool_name: str,
	params: Any,
	settings: Settings,
	compiled_query: Dict[str, Any] | None = None,
	family_tool_context: Dict[str, Any] | None = None,
) -> Any:
	name = str(tool_name or "").strip()
	original_params, params_obj = _normalize_params(params)
	compiled = compiled_query if isinstance(compiled_query, dict) else {}
	family_context = _normalize_family_tool_context(family_tool_context)
	family_allowed_reports = _family_allowed_report_names(family_context)
	report_discovery_allowed = _family_report_discovery_allowed(family_context)

	if name == "erp_fac-report_list":
		if compiled:
			raise ToolGatewayPolicyError("Compiled read mode does not allow report discovery.")
		if family_allowed_reports and not report_discovery_allowed:
			raise ToolGatewayPolicyError(
				"Governed family routing is active for this request, so report discovery is disabled."
			)
		if isinstance(params_obj, dict):
			module = str(params_obj.get("module") or "").strip()
			if module and module not in approved_modules():
				raise ToolGatewayPolicyError(f"Disallowed report module requested: {module}")
		return params

	if name not in {"erp_fac-report_requirements", "erp_fac-generate_report"}:
		return params

	if not isinstance(params_obj, dict):
		raise ToolGatewayPolicyError(f"Structured params are required for tool: {name}")

	report_name = str(params_obj.get("report_name") or "").strip()
	if not report_name:
		raise ToolGatewayPolicyError(f"Missing report_name for tool: {name}")
	if not is_report_approved(report_name):
		raise ToolGatewayPolicyError(f"Report is not approved for this runtime: {report_name}")
	if family_allowed_reports and report_name.lower() not in family_allowed_reports:
		raise ToolGatewayPolicyError(
			f"Report is outside the governed family tool surface for this request: {report_name}"
		)

	if compiled:
		prepared_compiled = _enforce_compiled_query_contract(
			tool_name=name,
			original_params=original_params,
			params_obj=params_obj,
			compiled_query=compiled,
		)
		errors = validate_report_filters(report_name, params_obj.get("filters"))
		if errors:
			raise ToolGatewayPolicyError(" ".join(errors))
		return prepared_compiled

	if name == "erp_fac-report_requirements":
		return params

	prepared = _apply_defaultable_filters(report_name, params_obj, settings)
	errors = validate_report_filters(report_name, prepared.get("filters"))
	if errors:
		raise ToolGatewayPolicyError(" ".join(errors))
	return _serialize_like_original(original_params, prepared)
