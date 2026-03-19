from __future__ import annotations

import json
from typing import Any, Dict, Tuple

from app.report_registry import approved_modules, is_report_approved, validate_report_filters
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


def _inject_default_company_if_needed(params_obj: Dict[str, Any], settings: Settings) -> Dict[str, Any]:
	if not settings.erp_default_company:
		return params_obj
	filters = params_obj.get("filters")
	if not isinstance(filters, dict):
		return params_obj
	company = str(filters.get("company") or "").strip()
	if company:
		return params_obj
	updated = json.loads(json.dumps(params_obj))
	updated_filters = updated.get("filters") or {}
	updated_filters["company"] = settings.erp_default_company
	updated["filters"] = updated_filters
	if isinstance(updated.get("company"), str):
		updated["company"] = settings.erp_default_company
	return updated


def enforce_tool_gateway_policy(tool_name: str, params: Any, settings: Settings) -> Any:
	name = str(tool_name or "").strip()
	original_params, params_obj = _normalize_params(params)

	if name == "erp_fac-report_list":
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

	if name == "erp_fac-report_requirements":
		return params

	prepared = _inject_default_company_if_needed(params_obj, settings)
	errors = validate_report_filters(report_name, prepared.get("filters"))
	if errors:
		raise ToolGatewayPolicyError(" ".join(errors))
	return _serialize_like_original(original_params, prepared)
