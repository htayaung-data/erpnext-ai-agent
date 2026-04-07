from __future__ import annotations

from typing import Any, Callable, Dict, List

from ai_assistant_ui.qwen_chat.smoke_fixtures import (
	require_smoke_fixture,
	smoke_fixture_followup_messages,
	smoke_fixture_reasoning_message,
	smoke_fixture_replacement_message,
)


def run_reasoning_live_rollout_smoke(
	*,
	run_phase55_smoke_session: Callable[..., Dict[str, Any]],
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	parse_payload,
	latest_tool_payload_by_type,
	latest_assistant_payload,
) -> Dict[str, Any]:
	flag_key = "qwen_enable_erp_business_reasoning"
	percent_key = "qwen_erp_business_reasoning_rollout_percentage"
	users_key = "qwen_erp_business_reasoning_rollout_users"
	conf = getattr(frappe_module, "conf", None) or {}
	originals = {
		flag_key: conf.get(flag_key),
		percent_key: conf.get(percent_key),
		users_key: conf.get(users_key),
	}
	presence = {
		flag_key: flag_key in conf,
		percent_key: percent_key in conf,
		users_key: users_key in conf,
	}
	try:
		conf[flag_key] = True
		conf[percent_key] = 0
		conf[users_key] = ["Administrator"]

		def _runner(doc) -> Dict[str, Any]:
			ok, first_payload = handle_qwen_user_message(
				session_name=doc.name,
				message=smoke_fixture_replacement_message("fresh_query_override_to_ar"),
				user="Administrator",
			)
			if not ok or str((first_payload or {}).get("mode") or "").strip() not in {
				"compiled_first_turn",
				"legacy_runtime",
				"legacy_runtime_rollout_fallback",
			}:
				raise RuntimeError("Phase 6 live reasoning rollout smoke failed: first turn did not produce grounded ERP output.")

			ok, second_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="Explain the overdue risk in this accounts receivable summary.",
				user="Administrator",
			)
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			tool_payloads: List[Dict[str, Any]] = []
			for row in session_doc.get("messages") or []:
				if str(row.role or "").strip().lower() != "tool":
					continue
				payload_obj = parse_payload(str(row.content or ""))
				if payload_obj:
					tool_payloads.append(payload_obj)
			if not ok or str((second_payload or {}).get("mode") or "").strip() != "erp_business_reasoning":
				raise RuntimeError(
					f"Phase 6 live reasoning rollout smoke failed: second payload was {second_payload!r}, tool types were {[item.get('type') for item in tool_payloads]!r}."
				)
			activation = latest_tool_payload_by_type(tool_payloads, "qwen_erp_business_reasoning_activation_contract")
			reasoning_contract = latest_tool_payload_by_type(tool_payloads, "qwen_erp_business_reasoning_contract")
			execution = latest_tool_payload_by_type(tool_payloads, "qwen_erp_business_reasoning_execution")
			if not activation or not reasoning_contract or not execution:
				raise RuntimeError("Phase 6 live reasoning rollout smoke failed: reasoning audit payloads were not persisted.")
			return {
				"ok": True,
				"first_mode": str((first_payload or {}).get("mode") or "").strip(),
				"second_mode": str((second_payload or {}).get("mode") or "").strip(),
				"reasoning_type": str(reasoning_contract.get("reasoning_type") or "").strip(),
				"answer_text": str(latest_assistant_payload(session_doc).get("text") or "").strip(),
			}

		return run_phase55_smoke_session(
			"Phase 6 Live Reasoning Rollout Smoke",
			_runner,
			frappe_module=frappe_module,
			session_doctype=session_doctype,
		)
	finally:
		for key, was_present in presence.items():
			if was_present:
				conf[key] = originals.get(key)
			else:
				try:
					conf.pop(key, None)
				except Exception:
					pass


def run_reasoning_without_grounding_smoke(
	*,
	run_phase6_smoke_session: Callable[..., Dict[str, Any]],
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
	latest_assistant_payload,
) -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message="what does this mean",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Phase 6 reasoning-without-grounding smoke failed: request did not complete.")
		if str((payload or {}).get("mode") or "").strip() == "erp_business_reasoning":
			raise RuntimeError("Phase 6 reasoning-without-grounding smoke failed: reasoning activated without governed grounding.")
		session_doc = frappe_module.get_doc(session_doctype, doc.name)
		tool_payloads = session_tool_payloads(session_doc)
		if latest_tool_payload_by_type(tool_payloads, "qwen_erp_business_reasoning_contract"):
			raise RuntimeError("Phase 6 reasoning-without-grounding smoke failed: reasoning contract was persisted without grounding.")
		return {
			"ok": True,
			"mode": str((payload or {}).get("mode") or "").strip(),
			"answer_text": str(latest_assistant_payload(session_doc).get("text") or "").strip(),
		}

	return run_phase6_smoke_session(
		"Phase 6 No Grounding Smoke",
		_runner,
		frappe_module=frappe_module,
		session_doctype=session_doctype,
	)


def run_reasoning_frontdoor_boundary_smoke(
	*,
	run_phase6_smoke_session: Callable[..., Dict[str, Any]],
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
) -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		frappe_module.clear_cache()
		ok, first_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_replacement_message("fresh_query_override_to_ar"),
			user="Administrator",
		)
		if not ok or str((first_payload or {}).get("mode") or "").strip() not in {
			"compiled_first_turn",
			"legacy_runtime",
			"legacy_runtime_rollout_fallback",
		}:
			raise RuntimeError("Phase 6 front-door boundary smoke failed: first turn did not produce grounded ERP output.")
		ok, second_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="Really Great, thank you",
			user="Administrator",
		)
		if not ok or str((second_payload or {}).get("mode") or "").strip() != "front_door":
			raise RuntimeError("Phase 6 front-door boundary smoke failed: gratitude after grounded reasoning context did not remain front door.")
		if str((((second_payload or {}).get("agent_meta") or {}).get("intent_class") or "")).strip() != "thanks":
			raise RuntimeError("Phase 6 front-door boundary smoke failed: gratitude turn was not classified as thanks.")
		session_doc = frappe_module.get_doc(session_doctype, doc.name)
		tool_payloads = session_tool_payloads(session_doc)
		events = [
			item
			for item in tool_payloads
			if str(item.get("type") or "").strip() == "qwen_phase6_observability_event"
			and str(item.get("event_family") or "").strip() == "reasoning_activation"
		]
		if not events:
			raise RuntimeError("Phase 6 front-door boundary smoke failed: no reasoning activation observability event was emitted.")
		latest_event = events[-1]
		if str(latest_event.get("event_name") or "").strip() == "accepted":
			raise RuntimeError("Phase 6 front-door boundary smoke failed: gratitude turn was incorrectly accepted as reasoning activation.")
		if latest_tool_payload_by_type(tool_payloads, "qwen_erp_business_reasoning_contract"):
			raise RuntimeError("Phase 6 front-door boundary smoke failed: reasoning contract was persisted for gratitude turn.")
		return {
			"ok": True,
			"frontdoor_mode": str((second_payload or {}).get("mode") or "").strip(),
			"intent_class": str((((second_payload or {}).get("agent_meta") or {}).get("intent_class") or "")).strip(),
			"activation_status": str(latest_event.get("event_name") or "").strip(),
		}

	return run_phase6_smoke_session(
		"Phase 6 Front Door Boundary Smoke",
		_runner,
		frappe_module=frappe_module,
		session_doctype=session_doctype,
	)


def run_nonadvisory_recommendation_boundary_smoke(
	*,
	run_phase6_smoke_session: Callable[..., Dict[str, Any]],
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
	latest_assistant_payload,
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
			raise RuntimeError("Phase 6 non-advisory boundary smoke failed: first turn did not produce grounded transactional output.")
		ok, second_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="what should management do next",
			user="Administrator",
		)
		session_doc = frappe_module.get_doc(session_doctype, doc.name)
		tool_payloads = session_tool_payloads(session_doc)
		execution_payload = latest_tool_payload_by_type(tool_payloads, "qwen_erp_business_reasoning_execution")
		second_mode = str((second_payload or {}).get("mode") or "").strip()
		clarification_reason = latest_tool_payload_by_type(tool_payloads, "qwen_clarification_reason_contract")
		clarification_signal = latest_tool_payload_by_type(tool_payloads, "qwen_clarification_signal_contract")
		answer_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
		clarification_reason_type = str(clarification_reason.get("reason_type") or "").strip()
		execution_status = str(execution_payload.get("status") or "").strip()
		clarification_ok = (
			second_mode in {"compiled_first_turn", "clarification"}
			and clarification_reason_type == "financial_summary_sales_scope_clarification"
		)
		reasoning_guardrail_ok = (
			second_mode == "erp_business_reasoning"
			and execution_status == "insufficient_grounding"
		)
		if not clarification_ok and not reasoning_guardrail_ok:
			raise RuntimeError(
				f"Phase 6 non-advisory boundary smoke failed: second turn landed in unexpected bounded state mode={second_mode!r} execution_status={execution_status!r} clarification_reason_type={clarification_reason_type!r}."
			)
		if clarification_ok:
			user_question = str(clarification_signal.get("user_question") or "").strip()
			if not user_question or "what kind of sales summary do you want" not in user_question.lower():
				raise RuntimeError(
					"Phase 6 non-advisory boundary smoke failed: clarification question did not explain the sales-summary scope choice."
				)
			if not answer_text or user_question.lower() not in answer_text.lower():
				raise RuntimeError("Phase 6 non-advisory boundary smoke failed: assistant answer did not surface the governed clarification question.")
		elif not answer_text:
			raise RuntimeError("Phase 6 non-advisory boundary smoke failed: missing governed guardrail answer text.")
		return {
			"ok": True,
			"mode": second_mode,
			"clarification_reason_type": clarification_reason_type,
			"execution_status": execution_status,
			"answer_text": answer_text,
		}

	return run_phase6_smoke_session(
		"Phase 6 Non-Advisory Recommendation Boundary Smoke",
		_runner,
		frappe_module=frappe_module,
		session_doctype=session_doctype,
	)


def run_artifact_refinement_precedence_smoke(
	*,
	run_phase6_smoke_session: Callable[..., Dict[str, Any]],
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
) -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		fixture = require_smoke_fixture("ranking_limit_refinement")
		ok, first_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=str(fixture.get("initial_message") or "").strip(),
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Phase 6 artifact-refinement precedence smoke failed on initial ranking request.")
		initial_rendered = latest_tool_payload_by_type(
			session_tool_payloads(frappe_module.get_doc(session_doctype, doc.name)),
			"qwen_rendered_family_response_contract",
		)
		if str(initial_rendered.get("family_id") or "").strip() != str(fixture.get("expected_family_id") or "").strip():
			raise RuntimeError("Phase 6 artifact-refinement precedence smoke failed: initial governed family did not match the governed smoke fixture.")
		refinement_messages = smoke_fixture_followup_messages("ranking_limit_refinement")
		second_payload: Dict[str, Any] = {}
		rows: List[Any] = []
		last_ok = False
		for refinement_message in refinement_messages:
			last_ok, second_payload = handle_qwen_user_message(
				session_name=doc.name,
				message=refinement_message,
				user="Administrator",
			)
			if str((second_payload or {}).get("mode") or "").strip() == "erp_business_reasoning":
				raise RuntimeError("Phase 6 artifact-refinement precedence smoke failed: refinement was incorrectly intercepted by reasoning.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			rendered = latest_tool_payload_by_type(session_tool_payloads(session_doc), "qwen_rendered_family_response_contract")
			blocks = rendered.get("blocks") if isinstance(rendered.get("blocks"), list) else []
			data_table = next((item for item in blocks if isinstance(item, dict) and str(item.get("block_type") or "").strip() == "data_table"), {})
			rows = data_table.get("rows") if isinstance(data_table.get("rows"), list) else []
			if last_ok and len(rows) == 3:
				break
		if not last_ok:
			raise RuntimeError("Phase 6 artifact-refinement precedence smoke failed on top-3 refinement.")
		if len(rows) != 3:
			raise RuntimeError(
				f"Phase 6 artifact-refinement precedence smoke failed: expected 3 rows after refinement, observed {len(rows)}."
			)
		return {
			"ok": True,
			"first_mode": str((first_payload or {}).get("mode") or "").strip(),
			"second_mode": str((second_payload or {}).get("mode") or "").strip(),
			"row_count": len(rows),
		}

	return run_phase6_smoke_session(
		"Phase 6 Artifact Refinement Precedence Smoke",
		_runner,
		frappe_module=frappe_module,
		session_doctype=session_doctype,
	)


def run_continuation_fulfillment_smoke(
	*,
	run_phase6_smoke_session: Callable[..., Dict[str, Any]],
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
) -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		ok, first_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="give me AR / AP insight",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Phase 6 continuation-fulfillment smoke failed on AR/AP insight request.")
		ok, second_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="what should management do next",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Phase 6 continuation-fulfillment smoke failed on management recommendation request.")
		third_message = "give me with bullet style recommendation so that I can understand more easily"
		ok, third_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=third_message,
			user="Administrator",
		)
		third_agent_meta = (third_payload or {}).get("agent_meta") if isinstance((third_payload or {}).get("agent_meta"), dict) else {}
		if (
			ok
			and str((third_payload or {}).get("mode") or "").strip() == "erp_business_reasoning"
			and str(third_agent_meta.get("engine") or "").strip() == "erp_business_reasoning_guardrail"
			and str(third_agent_meta.get("status") or "").strip() == "invalid_payload"
		):
			ok, third_payload = handle_qwen_user_message(
				session_name=doc.name,
				message=third_message,
				user="Administrator",
			)
		if not ok or str((third_payload or {}).get("mode") or "").strip() != "erp_business_reasoning":
			raise RuntimeError("Phase 6 continuation-fulfillment smoke failed: bullet-style continuation did not stay in reasoning.")
		answer_text = str((third_payload or {}).get("answer_text") or "").strip()
		if not answer_text or answer_text.endswith(":"):
			raise RuntimeError("Phase 6 continuation-fulfillment smoke failed: continuation returned an incomplete teaser.")
		if "\n-" not in answer_text and "\n•" not in answer_text and not answer_text.startswith("- "):
			raise RuntimeError("Phase 6 continuation-fulfillment smoke failed: bullet-style continuation did not render bullet content.")
		return {
			"ok": True,
			"initial_mode": str((first_payload or {}).get("mode") or "").strip(),
			"recommendation_mode": str((second_payload or {}).get("mode") or "").strip(),
			"continuation_mode": str((third_payload or {}).get("mode") or "").strip(),
			"answer_text": answer_text,
		}

	return run_phase6_smoke_session(
		"Phase 6 Continuation Fulfillment Smoke",
		_runner,
		frappe_module=frappe_module,
		session_doctype=session_doctype,
	)


def run_grounded_source_reset_smoke(
	*,
	run_phase6_smoke_session: Callable[..., Dict[str, Any]],
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
) -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		fixture = require_smoke_fixture("fresh_query_override_to_ar_ap_health")
		expected_replacement_source_names = {
			str(value or "").strip()
			for value in (fixture.get("expected_replacement_source_names") or [])
			if str(value or "").strip()
		}
		ok, _ = handle_qwen_user_message(
			session_name=doc.name,
			message="Top 7 customers by revenue",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Phase 6 grounded-source reset smoke failed on initial revenue ranking.")
		ok, _ = handle_qwen_user_message(
			session_name=doc.name,
			message="show only 3 rows",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Phase 6 grounded-source reset smoke failed on top-3 refinement.")
		ok = False
		replacement_payload: Dict[str, Any] = {}
		replacement_reports: set[str] = set()
		for _attempt in range(2):
			frappe_module.db.commit()
			frappe_module.clear_cache()
			ok, candidate_payload = handle_qwen_user_message(
				session_name=doc.name,
				message=smoke_fixture_replacement_message("fresh_query_override_to_ar_ap_health"),
				user="Administrator",
			)
			replacement_payload = candidate_payload if isinstance(candidate_payload, dict) else {"error": candidate_payload}
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			tool_payloads = session_tool_payloads(session_doc)
			grounded_turn = latest_tool_payload_by_type(tool_payloads, "qwen_grounded_turn_context")
			replacement_reports = {
				str(value or "").strip()
				for value in (grounded_turn.get("artifact_source_reports") or [])
				if str(value or "").strip()
			}
			replacement_mode = str((replacement_payload or {}).get("mode") or "").strip()
			if ok and replacement_mode in {
				"compiled_first_turn",
				"legacy_runtime",
				"legacy_runtime_rollout_fallback",
			} and replacement_reports == expected_replacement_source_names:
				break
		if not ok or replacement_reports != expected_replacement_source_names:
			raise RuntimeError(
				"Phase 6 grounded-source reset smoke failed: AR/AP reset did not land on the expected grounded reports. "
				f"payload={replacement_payload!r} reports={sorted(replacement_reports)!r}"
			)
		ok = False
		payload: Dict[str, Any] = {}
		for _attempt in range(2):
			frappe_module.db.commit()
			frappe_module.clear_cache()
			ok, candidate_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="what should management do next",
				user="Administrator",
			)
			payload = candidate_payload if isinstance(candidate_payload, dict) else {"error": candidate_payload}
			if ok and str((payload or {}).get("mode") or "").strip() == "erp_business_reasoning":
				break
		if not ok or str((payload or {}).get("mode") or "").strip() != "erp_business_reasoning":
			raise RuntimeError("Phase 6 grounded-source reset smoke failed: management follow-up did not stay in reasoning.")
		answer_text = str((payload or {}).get("answer_text") or "").strip().lower()
		if "top 3 customers by sales" in answer_text or "39.7% of sales" in answer_text:
			raise RuntimeError("Phase 6 grounded-source reset smoke failed: stale sales-ranking context leaked into AR/AP reasoning.")
		tool_payloads = session_tool_payloads(frappe_module.get_doc(session_doctype, doc.name))
		reasoning_contract = latest_tool_payload_by_type(tool_payloads, "qwen_erp_business_reasoning_contract")
		source_reports = {
			str(value or "").strip()
			for value in (reasoning_contract.get("grounding_source_reports") or [])
			if str(value or "").strip()
		}
		if source_reports != {"Accounts Receivable Summary", "Accounts Payable Summary"}:
			raise RuntimeError(
				f"Phase 6 grounded-source reset smoke failed: reasoning grounded on unexpected reports {sorted(source_reports)!r}."
			)
		return {
			"ok": True,
			"mode": str((payload or {}).get("mode") or "").strip(),
			"answer_text": str((payload or {}).get("answer_text") or "").strip(),
			"source_reports": sorted(source_reports),
		}

	return run_phase6_smoke_session(
		"Phase 6 Grounded Source Reset Smoke",
		_runner,
		frappe_module=frappe_module,
		session_doctype=session_doctype,
	)


def run_observability_smoke(
	*,
	run_phase6_smoke_session: Callable[..., Dict[str, Any]],
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
) -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		ok, first_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_replacement_message("fresh_query_override_to_ar"),
			user="Administrator",
		)
		if not ok or str((first_payload or {}).get("mode") or "").strip() not in {
			"compiled_first_turn",
			"legacy_runtime",
			"legacy_runtime_rollout_fallback",
		}:
			raise RuntimeError("Phase 6 observability smoke failed: first turn did not produce grounded ERP output.")
		frappe_module.db.commit()
		frappe_module.clear_cache()
		ok, second_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="what does this mean",
			user="Administrator",
		)
		if not ok or str((second_payload or {}).get("mode") or "").strip() != "erp_business_reasoning":
			raise RuntimeError("Phase 6 observability smoke failed: second turn was not handled in the reasoning lane.")
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
		activation_event = next(
			(
				item
				for item in reversed(events)
				if str(item.get("event_family") or "").strip() == "reasoning_activation"
				and str(item.get("event_name") or "").strip() == "accepted"
			),
			{},
		)
		execution_event = next(
			(
				item
				for item in reversed(events)
				if str(item.get("event_family") or "").strip() == "reasoning_execution"
				and str(item.get("event_name") or "").strip() == "answered"
			),
			{},
		)
		if not activation_event:
			raise RuntimeError("Phase 6 observability smoke failed: missing reasoning activation accepted event.")
		if not execution_event:
			raise RuntimeError("Phase 6 observability smoke failed: missing reasoning execution answered event.")
		if str(activation_event.get("event_level") or "").strip() != "info":
			raise RuntimeError("Phase 6 observability smoke failed: activation event level was not info.")
		if str(execution_event.get("event_level") or "").strip() != "info":
			raise RuntimeError("Phase 6 observability smoke failed: execution event level was not info.")
		for item in (activation_event, execution_event):
			if str(item.get("session_id") or "").strip() != str(doc.name):
				raise RuntimeError("Phase 6 observability smoke failed: observability event session_id mismatch.")
			if not str(item.get("request_id") or "").strip():
				raise RuntimeError("Phase 6 observability smoke failed: observability event request_id was empty.")
		metric_names = {
			str(item.get("metric_name") or "").strip()
			for item in metrics
			if str(item.get("metric_name") or "").strip()
		}
		if "reasoning_activation_latency" not in metric_names or "reasoning_execution_latency" not in metric_names:
			raise RuntimeError("Phase 6 observability smoke failed: missing reasoning latency metrics.")
		for item in metrics:
			if str(item.get("session_id") or "").strip() != str(doc.name):
				raise RuntimeError("Phase 6 observability smoke failed: performance metric session_id mismatch.")
			if not str(item.get("request_id") or "").strip():
				raise RuntimeError("Phase 6 observability smoke failed: performance metric request_id was empty.")
		return {
			"ok": True,
			"activation_event": activation_event,
			"execution_event": execution_event,
			"metric_names": sorted(metric_names),
		}

	return run_phase6_smoke_session(
		"Phase 6 Observability Smoke",
		_runner,
		frappe_module=frappe_module,
		session_doctype=session_doctype,
	)


def run_hardening_suite(
	*,
	recommendation_policy_probe,
	reasoning_live_rollout_smoke,
	reasoning_without_grounding_smoke,
	reasoning_frontdoor_boundary_smoke,
	nonadvisory_recommendation_boundary_smoke,
	artifact_refinement_precedence_smoke,
	continuation_fulfillment_smoke,
	grounded_source_reset_smoke,
	continuation_guardrail_smoke,
	observability_smoke,
) -> Dict[str, Any]:
	return {
		"ok": True,
		"recommendation_policy": recommendation_policy_probe(),
		"live_rollout": reasoning_live_rollout_smoke(),
		"no_grounding": reasoning_without_grounding_smoke(),
		"frontdoor_boundary": reasoning_frontdoor_boundary_smoke(),
		"nonadvisory_boundary": nonadvisory_recommendation_boundary_smoke(),
		"artifact_refinement_precedence": artifact_refinement_precedence_smoke(),
		"continuation_fulfillment": continuation_fulfillment_smoke(),
		"grounded_source_reset": grounded_source_reset_smoke(),
		"continuation_guardrail": continuation_guardrail_smoke(),
		"observability": observability_smoke(),
	}
