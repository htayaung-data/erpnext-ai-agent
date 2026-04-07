from __future__ import annotations

from typing import Any, Callable, Dict

from ai_assistant_ui.qwen_chat.smoke_fixtures import (
	require_smoke_fixture,
	smoke_fixture_action_message,
)


def _seed_quantity_recovery_session(
	doc,
	*,
	request_prefix: str,
	top_n: int,
	append_message,
	append_tool_payload,
	assistant_text_payload,
	build_artifact_enrichment_recovery_contract,
	save_session,
) -> None:
	recovery_payload = build_artifact_enrichment_recovery_contract(
		request_id=f"{request_prefix}-recovery",
		session_id=doc.name,
		source_request_id=f"{request_prefix}-grounded-trace",
		source_family_id="customer_rankings",
		source_capability_id="top_customers_by_revenue",
		source_report="Top Customers by Revenue",
		failure_type="artifact_enrichment_incompatible",
		recovery_state="recoverable",
		available_recovery_actions=["keep_current_artifact", "run_alternative_governed_query", "clarify_target_output"],
		recommended_recovery_action="run_alternative_governed_query",
		preservable_scope={"company": "Mingalar Mobile Distribution Co., Ltd.", "requested_top_n": top_n},
		preservable_dimensions=["customer"],
		preservable_metrics=["quantity", "revenue"],
		preservable_time_context={"from_date": "2026-02-01", "to_date": "2026-02-29"},
		alternative_capability_id="top_customers_by_quantity",
		alternative_report="Top Customers by Quantity",
		reason="Quantity requires a governed sibling query.",
		allowed_to_recover=True,
		confidence=0.91,
	).to_payload()
	grounded_turn_payload = {
		"type": "qwen_grounded_turn_context",
		"contract_version": "1.0",
		"request_id": f"{request_prefix}-grounded-request",
		"trace_request_id": f"{request_prefix}-grounded-trace",
		"grounded": True,
		"source_kind": "report",
		"source_name": "Top Customers by Revenue",
		"company": "Mingalar Mobile Distribution Co., Ltd.",
		"date_range": {"from_date": "2026-02-01", "to_date": "2026-02-29"},
		"filters": {"company": "Mingalar Mobile Distribution Co., Ltd."},
		"dimensions": ["customer"],
		"metrics": ["revenue"],
		"returned_schema": ["Customer", "Sales Amount"],
		"table_rows": [],
		"row_count": top_n,
		"base_language": "en",
		"transform_chain": [],
		"artifact_family_id": "customer_rankings",
		"artifact_type": "normalized_family_artifact",
		"artifact_source_reports": ["Top Customers by Revenue"],
		"known_entities": [],
		"known_documents": [],
	}
	append_message(
		doc,
		"assistant",
		assistant_text_payload(
			"I can't safely add quantity to the current ranking, but I can run the governed Top Customers by Quantity report for last month."
		),
	)
	append_tool_payload(doc, grounded_turn_payload)
	append_tool_payload(doc, recovery_payload)
	save_session(doc, ignore_permissions=False)


def run_recovery_authority_smoke(
	*,
	run_phase55_smoke_session: Callable[..., Dict[str, Any]],
	build_followup_resolution_contract,
	append_grounded_evidence_recovery_contract,
	frappe_module,
	session_doctype: str,
) -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		followup_resolution = build_followup_resolution_contract(
			request_id="phase8b-smoke-followup",
			mode="family_followup",
			target_dimension="invoice",
			requested_columns=["delivery_status"],
			depends_on_grounded_turn=True,
			latest_grounded_turn_available=True,
			reason="The user asked for delivery status over a sales-invoice artifact.",
		)
		recovery_payload = append_grounded_evidence_recovery_contract(
			doc,
			request_id="phase8b-smoke-recovery",
			session_id=doc.name,
			artifact_payload={"family_id": "transaction_listing", "source_name": "Sales Invoice List"},
			grounded_turn={
				"request_id": "phase8b-grounded-turn",
				"trace_request_id": "phase8b-grounded-trace",
				"source_name": "Sales Invoice List",
				"company": "Mingalar Mobile Distribution Co., Ltd.",
				"date_range": {"from_date": "2026-03-01", "to_date": "2026-03-31"},
				"filters": {"company": "Mingalar Mobile Distribution Co., Ltd."},
				"dimensions": ["invoice"],
				"metrics": ["grand_total", "outstanding_amount"],
				"artifact_family_id": "transaction_listing",
			},
			followup_resolution=followup_resolution,
			reason="The current governed artifact does not contain direct ERP evidence for the requested operational status.",
		)
		if str(recovery_payload.get("failure_type") or "").strip() != "grounded_evidence_missing":
			raise RuntimeError("Phase 8B recovery smoke failed: failure_type was not grounded_evidence_missing.")
		if str(recovery_payload.get("recommended_recovery_action") or "").strip() != "clarify_target_output":
			raise RuntimeError("Phase 8B recovery smoke failed: grounded evidence boundary did not recommend clarification.")
		if not bool(recovery_payload.get("allowed_to_recover")):
			raise RuntimeError("Phase 8B recovery smoke failed: grounded evidence boundary recovery should remain recoverable via clarification.")
		return {
			"ok": True,
			"mode": "recovery_contract_emitted",
			"recovery_payload": recovery_payload,
		}

	return run_phase55_smoke_session(
		"Phase 8B Recovery Authority Smoke",
		_runner,
		frappe_module=frappe_module,
		session_doctype=session_doctype,
	)


def run_recovery_guidance_observability_smoke(
	*,
	run_phase55_smoke_session: Callable[..., Dict[str, Any]],
	build_artifact_enrichment_recovery_contract,
	append_message,
	append_tool_payload,
	assistant_text_payload,
	save_session,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
) -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		_seed_quantity_recovery_session(
			doc,
			request_prefix="phase8obs-seed",
			top_n=7,
			append_message=append_message,
			append_tool_payload=append_tool_payload,
			assistant_text_payload=assistant_text_payload,
			build_artifact_enrichment_recovery_contract=build_artifact_enrichment_recovery_contract,
			save_session=save_session,
		)
		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_action_message("recovery_interaction_defaults", "guidance"),
			user="Administrator",
		)
		if not ok or str((payload or {}).get("mode") or "").strip() != "recovery_guidance":
			raise RuntimeError("Phase 8 observability smoke failed: guidance turn did not route to recovery guidance.")
		session_doc = frappe_module.get_doc(session_doctype, doc.name)
		tool_payloads = session_tool_payloads(session_doc)
		events = [
			item
			for item in tool_payloads
			if str(item.get("type") or "").strip() == "qwen_phase6_observability_event"
		]
		metrics = [
			item
			for item in tool_payloads
			if str(item.get("type") or "").strip() == "qwen_phase6_performance_metric"
		]
		guidance_event = next(
			(
				item
				for item in reversed(events)
				if str(item.get("event_family") or "").strip() == "recovery_guidance"
			),
			{},
		)
		guidance_metric = next(
			(
				item
				for item in reversed(metrics)
				if str(item.get("metric_name") or "").strip() == "recovery_guidance_latency"
			),
			{},
		)
		if str(guidance_event.get("event_name") or "").strip() != "answered":
			raise RuntimeError("Phase 8 observability smoke failed: recovery guidance event_name mismatch.")
		if str(guidance_event.get("event_level") or "").strip() != "info":
			raise RuntimeError("Phase 8 observability smoke failed: recovery guidance event level was not info.")
		if str(guidance_event.get("session_id") or "").strip() != str(doc.name):
			raise RuntimeError("Phase 8 observability smoke failed: recovery guidance event session_id mismatch.")
		if not str(guidance_event.get("request_id") or "").strip():
			raise RuntimeError("Phase 8 observability smoke failed: recovery guidance event request_id was empty.")
		if str(guidance_metric.get("session_id") or "").strip() != str(doc.name):
			raise RuntimeError("Phase 8 observability smoke failed: recovery guidance metric session_id mismatch.")
		if not str(guidance_metric.get("request_id") or "").strip():
			raise RuntimeError("Phase 8 observability smoke failed: recovery guidance metric request_id was empty.")
		return {
			"ok": True,
			"mode": str((payload or {}).get("mode") or "").strip(),
			"guidance_event": guidance_event,
			"guidance_metric": guidance_metric,
		}

	return run_phase55_smoke_session(
		"Phase 8 Recovery Guidance Observability Smoke",
		_runner,
		frappe_module=frappe_module,
		session_doctype=session_doctype,
	)


def run_evidence_boundary_observability_smoke(
	*,
	run_phase55_smoke_session: Callable[..., Dict[str, Any]],
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
) -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		ok, first_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="show me sales invoice list",
			user="Administrator",
		)
		if not ok or str((first_payload or {}).get("mode") or "").strip() not in {
			"compiled_first_turn",
			"legacy_runtime",
			"legacy_runtime_rollout_fallback",
		}:
			raise RuntimeError("Phase 8 evidence observability smoke failed: setup artifact turn did not complete.")
		ok, second_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="can you also tell me delivery status from here",
			user="Administrator",
		)
		if not ok or str((second_payload or {}).get("mode") or "").strip() != "grounded_evidence_boundary":
			raise RuntimeError("Phase 8 evidence observability smoke failed: evidence boundary turn did not enter grounded_evidence_boundary.")
		session_doc = frappe_module.get_doc(session_doctype, doc.name)
		tool_payloads = session_tool_payloads(session_doc)
		events = [
			item
			for item in tool_payloads
			if str(item.get("type") or "").strip() == "qwen_phase6_observability_event"
		]
		metrics = [
			item
			for item in tool_payloads
			if str(item.get("type") or "").strip() == "qwen_phase6_performance_metric"
		]
		boundary_event = next(
			(
				item
				for item in reversed(events)
				if str(item.get("event_family") or "").strip() == "artifact_boundary"
				and str(item.get("event_name") or "").strip() == "grounded_evidence_boundary"
			),
			{},
		)
		boundary_metric = next(
			(
				item
				for item in reversed(metrics)
				if str(item.get("metric_name") or "").strip() == "grounded_evidence_boundary_latency"
			),
			{},
		)
		if str(boundary_event.get("event_level") or "").strip() != "warning":
			raise RuntimeError("Phase 8 evidence observability smoke failed: boundary event level was not warning.")
		if str(boundary_event.get("session_id") or "").strip() != str(doc.name):
			raise RuntimeError("Phase 8 evidence observability smoke failed: boundary event session_id mismatch.")
		if not str(boundary_event.get("request_id") or "").strip():
			raise RuntimeError("Phase 8 evidence observability smoke failed: boundary event request_id was empty.")
		if str(boundary_metric.get("session_id") or "").strip() != str(doc.name):
			raise RuntimeError("Phase 8 evidence observability smoke failed: boundary metric session_id mismatch.")
		if not str(boundary_metric.get("request_id") or "").strip():
			raise RuntimeError("Phase 8 evidence observability smoke failed: boundary metric request_id was empty.")
		return {
			"ok": True,
			"mode": str((second_payload or {}).get("mode") or "").strip(),
			"boundary_event": boundary_event,
			"boundary_metric": boundary_metric,
		}

	return run_phase55_smoke_session(
		"Phase 8 Evidence Boundary Observability Smoke",
		_runner,
		frappe_module=frappe_module,
		session_doctype=session_doctype,
	)


def run_enrichment_boundary_observability_smoke(
	*,
	run_phase55_smoke_session: Callable[..., Dict[str, Any]],
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
) -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		fixture = require_smoke_fixture("fresh_query_override_to_ar")
		ok, first_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=str(fixture.get("initial_message") or "").strip(),
			user="Administrator",
		)
		if not ok or str((first_payload or {}).get("mode") or "").strip() not in {
			"compiled_first_turn",
			"legacy_runtime",
			"legacy_runtime_rollout_fallback",
		}:
			raise RuntimeError("Phase 8 enrichment observability smoke failed: setup artifact turn did not complete.")
		ok, second_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_action_message("product_recovery_flow", "serial_enrichment"),
			user="Administrator",
		)
		if not ok or str((second_payload or {}).get("mode") or "").strip() != "artifact_enrichment_boundary":
			raise RuntimeError("Phase 8 enrichment observability smoke failed: enrichment boundary turn did not enter artifact_enrichment_boundary.")
		session_doc = frappe_module.get_doc(session_doctype, doc.name)
		tool_payloads = session_tool_payloads(session_doc)
		events = [
			item
			for item in tool_payloads
			if str(item.get("type") or "").strip() == "qwen_phase6_observability_event"
		]
		metrics = [
			item
			for item in tool_payloads
			if str(item.get("type") or "").strip() == "qwen_phase6_performance_metric"
		]
		boundary_event = next(
			(
				item
				for item in reversed(events)
				if str(item.get("event_family") or "").strip() == "artifact_boundary"
				and str(item.get("event_name") or "").strip() == "artifact_enrichment_boundary"
			),
			{},
		)
		boundary_metric = next(
			(
				item
				for item in reversed(metrics)
				if str(item.get("metric_name") or "").strip() == "artifact_enrichment_boundary_latency"
			),
			{},
		)
		if str(boundary_event.get("event_level") or "").strip() != "warning":
			raise RuntimeError("Phase 8 enrichment observability smoke failed: boundary event level was not warning.")
		if str(boundary_event.get("session_id") or "").strip() != str(doc.name):
			raise RuntimeError("Phase 8 enrichment observability smoke failed: boundary event session_id mismatch.")
		if not str(boundary_event.get("request_id") or "").strip():
			raise RuntimeError("Phase 8 enrichment observability smoke failed: boundary event request_id was empty.")
		if str(boundary_metric.get("session_id") or "").strip() != str(doc.name):
			raise RuntimeError("Phase 8 enrichment observability smoke failed: boundary metric session_id mismatch.")
		if not str(boundary_metric.get("request_id") or "").strip():
			raise RuntimeError("Phase 8 enrichment observability smoke failed: boundary metric request_id was empty.")
		return {
			"ok": True,
			"mode": str((second_payload or {}).get("mode") or "").strip(),
			"boundary_event": boundary_event,
			"boundary_metric": boundary_metric,
		}

	return run_phase55_smoke_session(
		"Phase 8 Enrichment Boundary Observability Smoke",
		_runner,
		frappe_module=frappe_module,
		session_doctype=session_doctype,
	)


def run_repair_handling_smoke(
	*,
	run_phase55_smoke_session: Callable[..., Dict[str, Any]],
	build_artifact_enrichment_recovery_contract,
	append_message,
	append_tool_payload,
	assistant_text_payload,
	save_session,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	latest_assistant_payload,
	session_tool_payloads,
	latest_tool_payload_by_type,
) -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		_seed_quantity_recovery_session(
			doc,
			request_prefix="phase8c-seed",
			top_n=7,
			append_message=append_message,
			append_tool_payload=append_tool_payload,
			assistant_text_payload=assistant_text_payload,
			build_artifact_enrichment_recovery_contract=build_artifact_enrichment_recovery_contract,
			save_session=save_session,
		)
		ok, guidance_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_action_message("product_recovery_flow", "guidance"),
			user="Administrator",
		)
		if not ok or str((guidance_payload or {}).get("mode") or "").strip() != "recovery_guidance":
			raise RuntimeError("Phase 8C repair smoke failed: guidance request did not route to recovery guidance.")
		session_doc = frappe_module.get_doc(session_doctype, doc.name)
		guidance_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
		repair_payload = latest_tool_payload_by_type(session_tool_payloads(session_doc), "qwen_conversational_repair_intent_contract")
		if str(repair_payload.get("repair_intent_type") or "").strip() != "guidance_request":
			raise RuntimeError("Phase 8C repair smoke failed: guidance request did not emit guidance_request contract.")
		if "Top Customers by Quantity" not in guidance_text:
			raise RuntimeError("Phase 8C repair smoke failed: guidance answer did not include the governed alternative report.")

		ok, accepted_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_action_message("product_recovery_flow", "accept_governed_alternative"),
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Phase 8C repair smoke failed: accepted recovery action did not complete.")
		session_doc = frappe_module.get_doc(session_doctype, doc.name)
		assistant_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
		repair_payload = latest_tool_payload_by_type(session_tool_payloads(session_doc), "qwen_conversational_repair_intent_contract")
		if str(repair_payload.get("accepted_recovery_action") or "").strip() != "run_alternative_governed_query":
			raise RuntimeError("Phase 8C repair smoke failed: accepted recovery action mismatch.")
		user_messages = [
			str(row.content or "").strip()
			for row in (session_doc.get("messages") or [])
			if str(row.role or "").strip().lower() == "user"
		]
		if smoke_fixture_action_message("product_recovery_flow", "accept_governed_alternative") not in user_messages:
			raise RuntimeError("Phase 8C repair smoke failed: accepted recovery user turn was not persisted.")
		lower_text = assistant_text.lower()
		if "quantity" not in lower_text and "qty" not in lower_text and "unit" not in lower_text:
			raise RuntimeError("Phase 8C repair smoke failed: accepted recovery did not appear to run the governed quantity query.")
		return {
			"ok": True,
			"guidance_mode": str((guidance_payload or {}).get("mode") or "").strip(),
			"guidance_text": guidance_text,
			"accepted_mode": str((accepted_payload or {}).get("mode") or "").strip(),
			"accepted_text": assistant_text,
		}

	return run_phase55_smoke_session(
		"Phase 8C Repair Handling Smoke",
		_runner,
		frappe_module=frappe_module,
		session_doctype=session_doctype,
	)


def run_fresh_query_override_smoke(
	*,
	run_phase55_smoke_session: Callable[..., Dict[str, Any]],
	build_artifact_enrichment_recovery_contract,
	append_message,
	append_tool_payload,
	assistant_text_payload,
	save_session,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	latest_assistant_payload,
	session_tool_payloads,
	latest_tool_payload_by_type,
) -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		_seed_quantity_recovery_session(
			doc,
			request_prefix="phase8d-seed",
			top_n=7,
			append_message=append_message,
			append_tool_payload=append_tool_payload,
			assistant_text_payload=assistant_text_payload,
			build_artifact_enrichment_recovery_contract=build_artifact_enrichment_recovery_contract,
			save_session=save_session,
		)
		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_action_message("product_recovery_flow", "fresh_override_to_ar"),
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Phase 8D fresh-query override smoke failed: explicit fresh query did not complete.")
		if str((payload or {}).get("mode") or "").strip() != "compiled_first_turn":
			raise RuntimeError("Phase 8D fresh-query override smoke failed: explicit fresh query was not treated as a fresh governed query.")
		session_doc = frappe_module.get_doc(session_doctype, doc.name)
		assistant_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
		repair_payload = latest_tool_payload_by_type(session_tool_payloads(session_doc), "qwen_conversational_repair_intent_contract")
		if repair_payload:
			raise RuntimeError("Phase 8D fresh-query override smoke failed: explicit fresh query should not emit a repair contract.")
		if "Top Customers by Quantity" in assistant_text:
			raise RuntimeError("Phase 8D fresh-query override smoke failed: stale recovery guidance leaked into the fresh query answer.")
		if "AR" not in assistant_text and "receivable" not in assistant_text.lower():
			raise RuntimeError("Phase 8D fresh-query override smoke failed: fresh query answer did not switch to AR context.")
		return {
			"ok": True,
			"mode": str((payload or {}).get("mode") or "").strip(),
			"assistant_text": assistant_text,
		}

	return run_phase55_smoke_session(
		"Phase 8D Fresh Query Override Smoke",
		_runner,
		frappe_module=frappe_module,
		session_doctype=session_doctype,
	)


def run_recovery_execution_smoke(
	*,
	run_phase55_smoke_session: Callable[..., Dict[str, Any]],
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	latest_assistant_payload,
	session_tool_payloads,
	latest_tool_payload_by_type,
) -> Dict[str, Any]:
	def _accepted_alternative_runner(doc) -> Dict[str, Any]:
		fixture = require_smoke_fixture("product_recovery_flow")
		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message=str(fixture.get("initial_message") or "").strip(),
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Phase 8 recovery smoke failed on initial products ranking request.")
		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_action_message("product_recovery_flow", "qty_enrichment"),
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Phase 8 recovery smoke failed on quantity enrichment request.")
		initial_mode = str((payload or {}).get("mode") or "").strip()
		session_doc = frappe_module.get_doc(session_doctype, doc.name)
		initial_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
		latest_repair_payload = latest_tool_payload_by_type(
			session_tool_payloads(session_doc),
			"qwen_conversational_repair_intent_contract",
		)
		if str(latest_repair_payload.get("accepted_recovery_action") or "").strip() == "run_alternative_governed_query":
			raise RuntimeError("Phase 8 recovery smoke failed: enrichment request auto-accepted the governed alternative before an explicit acceptance turn.")
		recovery_payload = latest_tool_payload_by_type(session_tool_payloads(session_doc), "qwen_artifact_enrichment_recovery_contract")
		if initial_mode == "artifact_enrichment_boundary" and str(recovery_payload.get("recommended_recovery_action") or "").strip() != "run_alternative_governed_query":
			raise RuntimeError("Phase 8 recovery smoke failed: quantity enrichment did not recommend a governed alternative.")
		accepted_mode = initial_mode
		assistant_text = initial_text
		if initial_mode == "artifact_enrichment_boundary":
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message=smoke_fixture_action_message("product_recovery_flow", "short_acceptance"),
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase 8 recovery smoke failed: accepted alternative did not complete.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			assistant_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			repair_payload = latest_tool_payload_by_type(session_tool_payloads(session_doc), "qwen_conversational_repair_intent_contract")
			if str(repair_payload.get("accepted_recovery_action") or "").strip() != "run_alternative_governed_query":
				raise RuntimeError("Phase 8 recovery smoke failed: accepted recovery action mismatch.")
			accepted_mode = str((payload or {}).get("mode") or "").strip()
			if accepted_mode != "compiled_first_turn":
				raise RuntimeError("Phase 8 recovery smoke failed: accepted alternative did not execute as compiled_first_turn.")
		else:
			compiler_payload = latest_tool_payload_by_type(
				session_tool_payloads(session_doc),
				"qwen_fresh_query_compiler_contract",
			)
			compiler_decision = str(compiler_payload.get("decision") or "").strip()
			if compiler_decision == "clarify":
				clarification_reason_type = str(compiler_payload.get("clarification_reason_type") or "").strip()
				semantic_details = (
					compiler_payload.get("governed_resolution_details")
					if isinstance(compiler_payload.get("governed_resolution_details"), dict)
					else {}
				)
				semantic_contract = (
					semantic_details.get("semantic_resolution_contract")
					if isinstance(semantic_details.get("semantic_resolution_contract"), dict)
					else {}
				)
				intent_class = str(semantic_contract.get("intent_class") or "").strip()
				ambiguity_flags = {
					str(value or "").strip()
					for value in (semantic_contract.get("ambiguity_flags") or [])
					if str(value or "").strip()
				}
				if clarification_reason_type != "report_ambiguity":
					raise RuntimeError("Phase 8 recovery smoke failed: quantity enrichment clarification was not a governed report ambiguity.")
				if intent_class not in {"ranked_entities", "product_performance"}:
					raise RuntimeError("Phase 8 recovery smoke failed: quantity enrichment clarification did not stay within the approved governed intent families.")
				if not ambiguity_flags.intersection({"missing_ranking_metric", "missing_performance_view"}):
					raise RuntimeError("Phase 8 recovery smoke failed: quantity enrichment clarification did not preserve an approved governed ambiguity.")
				if "which report would you like me to use" not in initial_text.lower():
					raise RuntimeError("Phase 8 recovery smoke failed: quantity enrichment clarification prompt changed unexpectedly.")
				return {
					"ok": True,
					"initial_mode": initial_mode,
					"initial_text": initial_text,
					"recovery_payload": recovery_payload,
					"accepted_mode": accepted_mode,
					"accepted_text": assistant_text,
					"compiler_payload": compiler_payload,
				}
			rendered_payload = latest_tool_payload_by_type(
				session_tool_payloads(session_doc),
				"qwen_rendered_family_response_contract",
			)
			blocks = rendered_payload.get("blocks") if isinstance(rendered_payload.get("blocks"), list) else []
			data_table = next(
				(
					item
					for item in blocks
					if isinstance(item, dict) and str(item.get("block_type") or "").strip() == "data_table"
				),
				{},
			)
			columns = data_table.get("columns") if isinstance(data_table.get("columns"), list) else []
			lower_initial = initial_text.lower()
			has_quantity_text = "quantity" in lower_initial or "qty" in lower_initial or "unit" in lower_initial
			has_quantity_column = any(
				"quantity" in str(column or "").strip().lower() or "qty" in str(column or "").strip().lower()
				for column in columns
			)
			if not has_quantity_text and not has_quantity_column:
				raise RuntimeError("Phase 8 recovery smoke failed: direct quantity enrichment did not appear to return a quantity-focused result.")
		return {
			"ok": True,
			"initial_mode": initial_mode,
			"initial_text": initial_text,
			"recovery_payload": recovery_payload,
			"accepted_mode": accepted_mode,
			"accepted_text": assistant_text,
		}

	accepted_flow = run_phase55_smoke_session(
		"Phase 8 Recovery Execution Smoke",
		_accepted_alternative_runner,
		frappe_module=frappe_module,
		session_doctype=session_doctype,
	)
	return {
		"ok": True,
		"accepted_alternative_flow": accepted_flow,
	}


def run_hardening_suite(
	*,
	recovery_authority_smoke,
	repair_handling_smoke,
	fresh_query_override_smoke,
	recovery_execution_smoke,
) -> Dict[str, Any]:
	return {
		"ok": True,
		"recovery_authority": recovery_authority_smoke(),
		"repair_handling": repair_handling_smoke(),
		"fresh_query_override": fresh_query_override_smoke(),
		"recovery_execution": recovery_execution_smoke(),
	}
