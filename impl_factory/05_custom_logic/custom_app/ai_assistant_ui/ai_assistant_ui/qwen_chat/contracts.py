from __future__ import annotations

import datetime as dt
import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.capability_adapters import (
	extract_grounded_table,
	supports_local_followup_mode,
)
from ai_assistant_ui.qwen_chat.followup_interpreter import (
	detect_followup_intent,
	is_million_transform_intent as _is_million_transform_intent,
	is_self_contained_business_request as _is_self_contained_business_request,
)
from ai_assistant_ui.qwen_chat.metadata import (
	resolve_followup_report_switch,
)


def _utc_now() -> str:
	return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _safe_json_loads(value: Any) -> Any:
	if isinstance(value, (dict, list)):
		return value
	text = str(value or "").strip()
	if not text:
		return None
	try:
		return json.loads(text)
	except Exception:
		return None


def detect_language(text: str) -> str:
	value = str(text or "")
	has_myanmar = bool(re.search(r"[\u1000-\u109F\uA9E0-\uA9FF\uAA60-\uAA7F]", value))
	has_latin = bool(re.search(r"[A-Za-z]", value))
	if has_myanmar and has_latin:
		return "mixed"
	if has_myanmar:
		return "my"
	return "en"


def is_million_transform_request(message: str) -> bool:
	return _is_million_transform_intent(message)

def is_self_contained_business_request(message: str) -> bool:
	return _is_self_contained_business_request(message)


@dataclass(frozen=True)
class InteractionContract:
	request_id: str
	session_id: str
	user_id: str
	site_name: str
	raw_message: str
	detected_language: str
	ui_channel: str = "erpnext_qwen_chat"
	received_at: str = ""

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_interaction_contract",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"session_id": self.session_id,
			"user_id": self.user_id,
			"site_name": self.site_name,
			"raw_message": self.raw_message,
			"detected_language": self.detected_language,
			"ui_channel": self.ui_channel,
			"received_at": self.received_at or _utc_now(),
		}


@dataclass(frozen=True)
class FollowUpResolution:
	request_id: str
	mode: str
	requested_modes: List[str]
	target_dimension: str
	target_capability_id: str
	target_report: str
	depends_on_grounded_turn: bool
	self_contained: bool
	latest_grounded_turn_available: bool
	reason: str

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_followup_resolution",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"mode": self.mode,
			"requested_modes": self.requested_modes,
			"target_dimension": self.target_dimension,
			"target_capability_id": self.target_capability_id,
			"target_report": self.target_report,
			"depends_on_grounded_turn": self.depends_on_grounded_turn,
			"self_contained": self.self_contained,
			"latest_grounded_turn_available": self.latest_grounded_turn_available,
			"reason": self.reason,
			"resolved_at": _utc_now(),
		}


@dataclass(frozen=True)
class ExecutionPath:
	request_id: str
	path: str
	reason: str
	requires_runtime: bool
	grounded_required: bool = True

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_execution_path",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"path": self.path,
			"reason": self.reason,
			"requires_runtime": self.requires_runtime,
			"grounded_required": self.grounded_required,
			"chosen_at": _utc_now(),
		}


@dataclass(frozen=True)
class GroundedTurnContext:
	request_id: str
	trace_request_id: str
	grounded: bool
	source_kind: str
	source_name: str
	company: str
	date_range: Dict[str, Any]
	filters: Dict[str, Any]
	dimensions: List[str]
	metrics: List[str]
	returned_schema: List[str]
	table_rows: List[Dict[str, Any]]
	row_count: int
	base_language: str
	transform_chain: List[str]

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"trace_request_id": self.trace_request_id,
			"grounded": self.grounded,
			"source_kind": self.source_kind,
			"source_name": self.source_name,
			"company": self.company,
			"date_range": self.date_range,
			"filters": self.filters,
			"dimensions": self.dimensions,
			"metrics": self.metrics,
			"returned_schema": self.returned_schema,
			"table_rows": self.table_rows,
			"row_count": self.row_count,
			"base_language": self.base_language,
			"transform_chain": self.transform_chain,
			"created_at": _utc_now(),
		}


@dataclass(frozen=True)
class AuditEnvelope:
	request_id: str
	session_id: str
	followup_mode: str
	execution_path: str
	grounded: bool
	source_kind: str
	source_name: str
	runtime_engine: str
	runtime_model: str
	runtime_latency_ms: int
	tool_count: int
	tool_names: List[str]
	validation_status: str
	validation_errors: List[str]
	answer_chars: int

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_audit_envelope",
			"contract_version": "1.0",
			"request_id": self.request_id,
			"session_id": self.session_id,
			"followup_mode": self.followup_mode,
			"execution_path": self.execution_path,
			"grounded": self.grounded,
			"source_kind": self.source_kind,
			"source_name": self.source_name,
			"runtime_engine": self.runtime_engine,
			"runtime_model": self.runtime_model,
			"runtime_latency_ms": self.runtime_latency_ms,
			"tool_count": self.tool_count,
			"tool_names": self.tool_names,
			"validation_status": self.validation_status,
			"validation_errors": self.validation_errors,
			"answer_chars": self.answer_chars,
			"created_at": _utc_now(),
		}


def build_interaction_contract(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	raw_message: str,
) -> InteractionContract:
	return InteractionContract(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		raw_message=raw_message,
		detected_language=detect_language(raw_message),
		received_at=_utc_now(),
	)


def build_followup_resolution(
	*,
	request_id: str,
	message: str,
	latest_grounded_turn_available: bool,
	latest_grounded_turn: Dict[str, Any] | None = None,
) -> FollowUpResolution:
	intent = detect_followup_intent(message, grounded_turn=latest_grounded_turn)
	requested_modes = intent.requested_modes
	self_contained = _is_self_contained_business_request(message, grounded_turn=latest_grounded_turn, intent=intent)
	grounded_turn = latest_grounded_turn if isinstance(latest_grounded_turn, dict) else {}
	local_grounded_modes = {"presentation_transform", "table_presentation"}
	if supports_local_followup_mode(grounded_turn, "aging_bucket_view"):
		local_grounded_modes.add("aging_bucket_view")
	if supports_local_followup_mode(grounded_turn, "dimension_breakdown", target_dimension=intent.target_dimension):
		local_grounded_modes.add("dimension_breakdown")
	source_report = str(grounded_turn.get("source_name") or "").strip()
	switch = resolve_followup_report_switch(requested_modes, source_report) if latest_grounded_turn_available else {}

	if latest_grounded_turn_available and requested_modes and set(requested_modes).issubset(local_grounded_modes):
		return FollowUpResolution(
			request_id=request_id,
			mode="local_grounded_transform",
			requested_modes=requested_modes,
			target_dimension=intent.target_dimension,
			target_capability_id="",
			target_report="",
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="The request can be resolved deterministically from the latest grounded answer using local capability adapters.",
		)
	if latest_grounded_turn_available and switch:
		return FollowUpResolution(
			request_id=request_id,
			mode="capability_requery",
			requested_modes=requested_modes,
			target_dimension=intent.target_dimension,
			target_capability_id=str(switch.get("capability_id") or "").strip(),
			target_report=str(switch.get("target_report") or "").strip(),
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="The request needs a governed report switch within the same business capability.",
		)
	if latest_grounded_turn_available and not self_contained:
		return FollowUpResolution(
			request_id=request_id,
			mode="grounded_follow_up",
			requested_modes=requested_modes,
			target_dimension=intent.target_dimension,
			target_capability_id="",
			target_report="",
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="The request depends on prior grounded context and is not self-contained.",
		)
	return FollowUpResolution(
		request_id=request_id,
		mode="new_query",
		requested_modes=requested_modes,
		target_dimension=intent.target_dimension,
		target_capability_id="",
		target_report="",
		depends_on_grounded_turn=False,
		self_contained=self_contained,
		latest_grounded_turn_available=latest_grounded_turn_available,
		reason="The request is self-contained enough to be treated as a new ERP query.",
	)


def build_execution_path(
	*,
	request_id: str,
	followup_resolution: FollowUpResolution,
	local_transform_applied: bool,
) -> ExecutionPath:
	if local_transform_applied:
		return ExecutionPath(
			request_id=request_id,
			path="local_transform",
			reason="The follow-up was resolved deterministically from the existing grounded answer.",
			requires_runtime=False,
		)
	return ExecutionPath(
		request_id=request_id,
		path="erp_requery",
		reason="The assistant must use FAC/ERP tools to produce or refresh a grounded answer.",
		requires_runtime=True,
	)


def build_grounded_turn_context(
	*,
	request_id: str,
	interaction_contract: InteractionContract,
	assistant_payload: Dict[str, Any],
	runtime_payload: Dict[str, Any],
) -> GroundedTurnContext | None:
	tool_trace = runtime_payload.get("tool_trace")
	if not isinstance(tool_trace, list) or not tool_trace:
		return None

	report_tool = None
	for item in reversed(tool_trace):
		if not isinstance(item, dict):
			continue
		if str(item.get("tool") or "").strip() == "erp_fac-generate_report":
			report_tool = item
			break
	if report_tool is None:
		for item in reversed(tool_trace):
			if not isinstance(item, dict):
				continue
			if str(item.get("tool") or "").strip().startswith("erp_fac-"):
				report_tool = item
				break
	if report_tool is None:
		return None

	tool_name = str(report_tool.get("tool") or "").strip()
	tool_args = report_tool.get("detail_obj")
	if not isinstance(tool_args, dict):
		tool_args = _safe_json_loads(report_tool.get("detail"))
	if not isinstance(tool_args, dict):
		tool_args = {}

	filters = tool_args.get("filters")
	if not isinstance(filters, dict):
		filters = {}

	source_kind = "report" if tool_name == "erp_fac-generate_report" else "tool"
	source_name = str(tool_args.get("report_name") or tool_name or "").strip()
	date_range = {
		"from_date": filters.get("from_date"),
		"to_date": filters.get("to_date"),
		"report_date": filters.get("report_date"),
	}
	company = str(filters.get("company") or "").strip()

	tables = assistant_payload.get("tables")
	first_table = tables[0] if isinstance(tables, list) and tables and isinstance(tables[0], dict) else {}
	headers = first_table.get("headers") if isinstance(first_table.get("headers"), list) else []
	rows = first_table.get("rows") if isinstance(first_table.get("rows"), list) else []
	headers, rows = extract_grounded_table(report_tool, assistant_payload)

	dimensions: List[str] = []
	tree_type = str(filters.get("tree_type") or "").strip()
	if tree_type:
		dimensions.append(tree_type)
	if headers:
		first_header = str(headers[0] or "").strip()
		if first_header and first_header not in dimensions:
			dimensions.append(first_header)

	metrics: List[str] = []
	value_quantity = str(filters.get("value_quantity") or "").strip()
	if value_quantity:
		metrics.append(value_quantity)
	for header in headers[1:]:
		header_text = str(header or "").strip()
		if header_text and header_text not in metrics:
			metrics.append(header_text)

	trace_request_id = str(runtime_payload.get("request_id") or request_id).strip()
	return GroundedTurnContext(
		request_id=request_id,
		trace_request_id=trace_request_id,
		grounded=bool(runtime_payload.get("ok")),
		source_kind=source_kind,
		source_name=source_name,
		company=company,
		date_range=date_range,
		filters=filters,
		dimensions=dimensions,
		metrics=metrics,
		returned_schema=[str(x or "").strip() for x in headers if str(x or "").strip()],
		table_rows=[row for row in rows[:100] if isinstance(row, dict)],
		row_count=len(rows),
		base_language=interaction_contract.detected_language,
		transform_chain=[],
	)


def build_audit_envelope(
	*,
	interaction_contract: InteractionContract,
	followup_resolution: FollowUpResolution,
	execution_path: ExecutionPath,
	runtime_trace_payload: Dict[str, Any] | None,
	grounded_turn_context: Dict[str, Any] | None,
	answer_text: str,
) -> AuditEnvelope:
	trace = runtime_trace_payload if isinstance(runtime_trace_payload, dict) else {}
	grounded_turn = grounded_turn_context if isinstance(grounded_turn_context, dict) else {}
	agent_meta = trace.get("agent_meta") if isinstance(trace.get("agent_meta"), dict) else {}
	validation = agent_meta.get("validation") if isinstance(agent_meta.get("validation"), dict) else {}
	tool_trace = trace.get("tool_trace") if isinstance(trace.get("tool_trace"), list) else []
	tool_names = [
		str(item.get("tool") or "").strip()
		for item in tool_trace
		if isinstance(item, dict) and str(item.get("tool") or "").strip()
	]
	grounded = bool(grounded_turn.get("grounded"))
	if not grounded and execution_path.path == "local_transform" and bool(followup_resolution.depends_on_grounded_turn):
		grounded = True
	source_kind = str(grounded_turn.get("source_kind") or ("transform" if execution_path.path == "local_transform" else "")).strip()
	source_name = str(grounded_turn.get("source_name") or "").strip()
	validation_status = str(validation.get("status") or ("pass" if execution_path.path == "local_transform" else "unknown")).strip()
	validation_errors = validation.get("errors") if isinstance(validation.get("errors"), list) else []
	return AuditEnvelope(
		request_id=interaction_contract.request_id,
		session_id=interaction_contract.session_id,
		followup_mode=followup_resolution.mode,
		execution_path=execution_path.path,
		grounded=grounded,
		source_kind=source_kind,
		source_name=source_name,
		runtime_engine=str(agent_meta.get("engine") or "").strip(),
		runtime_model=str(agent_meta.get("model") or "").strip(),
		runtime_latency_ms=int(max(0, trace.get("runtime_latency_ms") or 0)),
		tool_count=len(tool_names),
		tool_names=tool_names,
		validation_status=validation_status,
		validation_errors=[str(x or "").strip() for x in validation_errors if str(x or "").strip()],
		answer_chars=len(str(answer_text or "").strip()),
	)
