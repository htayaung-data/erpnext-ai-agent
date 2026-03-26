from __future__ import annotations

import datetime as dt
import json
from typing import Any, Dict

try:
	import frappe  # type: ignore
except Exception:  # pragma: no cover
	frappe = None


def _utc_now() -> str:
	return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def build_phase55_observability_event(
	*,
	request_id: str,
	session_id: str,
	event_family: str,
	event_name: str,
	details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	return {
		"type": "qwen_phase55_observability_event",
		"contract_version": "1.0",
		"request_id": str(request_id or "").strip(),
		"session_id": str(session_id or "").strip(),
		"event_family": str(event_family or "").strip(),
		"event_name": str(event_name or "").strip(),
		"details": dict(details or {}),
		"created_at": _utc_now(),
	}


def record_phase55_observability_event(
	*,
	request_id: str,
	session_id: str,
	event_family: str,
	event_name: str,
	details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	event = build_phase55_observability_event(
		request_id=request_id,
		session_id=session_id,
		event_family=event_family,
		event_name=event_name,
		details=details,
	)
	if frappe is not None:
		try:
			logger = frappe.logger("qwen_phase55", allow_site=True)
			logger.info(json.dumps(event, ensure_ascii=True, sort_keys=True))
		except Exception:
			pass
	return event


def build_phase6_observability_event(
	*,
	request_id: str,
	session_id: str,
	event_family: str,
	event_name: str,
	event_level: str = "info",
	details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	level = str(event_level or "info").strip().lower() or "info"
	if level not in {"info", "warning", "error"}:
		level = "info"
	return {
		"type": "qwen_phase6_observability_event",
		"contract_version": "1.0",
		"request_id": str(request_id or "").strip(),
		"session_id": str(session_id or "").strip(),
		"event_family": str(event_family or "").strip(),
		"event_name": str(event_name or "").strip(),
		"event_level": level,
		"details": dict(details or {}),
		"created_at": _utc_now(),
	}


def record_phase6_observability_event(
	*,
	request_id: str,
	session_id: str,
	event_family: str,
	event_name: str,
	event_level: str = "info",
	details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	event = build_phase6_observability_event(
		request_id=request_id,
		session_id=session_id,
		event_family=event_family,
		event_name=event_name,
		event_level=event_level,
		details=details,
	)
	if frappe is not None:
		try:
			logger = frappe.logger("qwen_phase6", allow_site=True)
			payload = json.dumps(event, ensure_ascii=True, sort_keys=True)
			if event["event_level"] == "error":
				logger.error(payload)
			elif event["event_level"] == "warning":
				logger.warning(payload)
			else:
				logger.info(payload)
		except Exception:
			pass
	return event


def build_phase6_performance_metric(
	*,
	request_id: str,
	session_id: str,
	metric_name: str,
	metric_value: float,
	metric_unit: str = "ms",
	details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	return {
		"type": "qwen_phase6_performance_metric",
		"contract_version": "1.0",
		"request_id": str(request_id or "").strip(),
		"session_id": str(session_id or "").strip(),
		"metric_name": str(metric_name or "").strip(),
		"metric_value": float(metric_value or 0.0),
		"metric_unit": str(metric_unit or "ms").strip() or "ms",
		"details": dict(details or {}),
		"created_at": _utc_now(),
	}


def record_phase6_performance_metric(
	*,
	request_id: str,
	session_id: str,
	metric_name: str,
	metric_value: float,
	metric_unit: str = "ms",
	details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	event = build_phase6_performance_metric(
		request_id=request_id,
		session_id=session_id,
		metric_name=metric_name,
		metric_value=metric_value,
		metric_unit=metric_unit,
		details=details,
	)
	if frappe is not None:
		try:
			logger = frappe.logger("qwen_phase6", allow_site=True)
			logger.info(json.dumps(event, ensure_ascii=True, sort_keys=True))
		except Exception:
			pass
	return event
