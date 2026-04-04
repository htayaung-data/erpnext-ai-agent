from __future__ import annotations

from typing import Any, Callable, Dict, List

from ai_assistant_ui.qwen_chat.smoke_fixtures import require_smoke_fixture, smoke_fixture_action_message


def run_clarification_attempt_smoke(
	*,
	run_smoke_session: Callable[..., Dict[str, Any]],
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	get_clarification_state,
	latest_assistant_payload,
) -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		handle_qwen_user_message(
			session_name=doc.name,
			message="show me financial statement",
			user="Administrator",
		)
		session_doc = frappe_module.get_doc(session_doctype, doc.name)
		initial_state = get_clarification_state(session_doc)
		if not initial_state.has_pending:
			raise RuntimeError("Phase 5.5 clarification-attempt smoke failed: initial clarification state was not persisted.")
		if int(initial_state.attempt_count) != 0:
			raise RuntimeError("Phase 5.5 clarification-attempt smoke failed: initial attempt count did not start at zero.")

		ok, first_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="yes",
			user="Administrator",
		)
		if not ok or str((first_payload or {}).get("mode") or "").strip() != "clarification":
			raise RuntimeError("Phase 5.5 clarification-attempt smoke failed on first unresolved reply.")
		if str(((first_payload or {}).get("agent_meta") or {}).get("mode") or "").strip() != "empty_ack":
			raise RuntimeError("Phase 5.5 clarification-attempt smoke failed: first unresolved reply was not attributed to empty_ack.")
		session_doc = frappe_module.get_doc(session_doctype, doc.name)
		state_after_first = get_clarification_state(session_doc)
		if int(state_after_first.attempt_count) != 1:
			raise RuntimeError("Phase 5.5 clarification-attempt smoke failed: attempt count did not increment to one.")

		ok, second_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="yes",
			user="Administrator",
		)
		if not ok or str((second_payload or {}).get("mode") or "").strip() != "clarification":
			raise RuntimeError("Phase 5.5 clarification-attempt smoke failed on second unresolved reply.")
		if str(((second_payload or {}).get("agent_meta") or {}).get("mode") or "").strip() != "empty_ack":
			raise RuntimeError("Phase 5.5 clarification-attempt smoke failed: second unresolved reply was not attributed to empty_ack.")
		session_doc = frappe_module.get_doc(session_doctype, doc.name)
		state_after_second = get_clarification_state(session_doc)
		if int(state_after_second.attempt_count) != 2:
			raise RuntimeError("Phase 5.5 clarification-attempt smoke failed: attempt count did not increment to two.")

		ok, final_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="yes",
			user="Administrator",
		)
		if not ok or str((final_payload or {}).get("mode") or "").strip() != "clarification":
			raise RuntimeError("Phase 5.5 clarification-attempt smoke failed on bounded-stop reply.")
		if str(((final_payload or {}).get("agent_meta") or {}).get("mode") or "").strip() != "fallback_stop":
			raise RuntimeError("Phase 5.5 clarification-attempt smoke failed: third unresolved reply did not exit through fallback_stop.")
		session_doc = frappe_module.get_doc(session_doctype, doc.name)
		final_state = get_clarification_state(session_doc)
		if final_state.has_pending:
			raise RuntimeError("Phase 5.5 clarification-attempt smoke failed: pending clarification state was not cleared after bounded stop.")
		return {
			"ok": True,
			"attempt_counts": [0, 1, 2],
			"final_mode": str(((final_payload or {}).get("agent_meta") or {}).get("mode") or "").strip(),
			"final_answer": str(latest_assistant_payload(session_doc).get("text") or "").strip(),
		}

	return run_smoke_session(
		"Phase 5.5 Clarification Attempt Smoke",
		_runner,
		frappe_module=frappe_module,
		session_doctype=session_doctype,
	)


def run_clarification_meta_question_smoke(
	*,
	run_smoke_session: Callable[..., Dict[str, Any]],
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	get_clarification_state,
	latest_assistant_payload,
) -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		handle_qwen_user_message(
			session_name=doc.name,
			message="show me financial statement",
			user="Administrator",
		)
		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message="what do you mean?",
			user="Administrator",
		)
		if not ok or str((payload or {}).get("mode") or "").strip() != "clarification":
			raise RuntimeError("Phase 5.5 meta-question smoke failed: clarification did not stay active.")
		if str(((payload or {}).get("agent_meta") or {}).get("mode") or "").strip() != "meta_question":
			raise RuntimeError("Phase 5.5 meta-question smoke failed: reply was not attributed to meta_question.")
		session_doc = frappe_module.get_doc(session_doctype, doc.name)
		state = get_clarification_state(session_doc)
		if not state.has_pending or int(state.attempt_count) != 1:
			raise RuntimeError("Phase 5.5 meta-question smoke failed: pending clarification state did not persist correctly.")
		return {
			"ok": True,
			"mode": str(((payload or {}).get("agent_meta") or {}).get("mode") or "").strip(),
			"attempt_count": int(state.attempt_count),
			"answer_text": str(latest_assistant_payload(session_doc).get("text") or "").strip(),
		}

	return run_smoke_session(
		"Phase 5.5 Meta Question Smoke",
		_runner,
		frappe_module=frappe_module,
		session_doctype=session_doctype,
	)


def run_pending_override_smoke(
	*,
	run_smoke_session: Callable[..., Dict[str, Any]],
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	get_clarification_state,
	latest_assistant_payload,
) -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		handle_qwen_user_message(
			session_name=doc.name,
			message="show me financial statement",
			user="Administrator",
		)
		override_message = smoke_fixture_action_message("recovery_interaction_defaults", "fresh_override_to_ar")
		_, payload = handle_qwen_user_message(
			session_name=doc.name,
			message=override_message,
			user="Administrator",
		)
		if str((payload or {}).get("mode") or "").strip() == "clarification":
			raise RuntimeError("Phase 5.5 pending-override smoke failed: fresh ERP request remained trapped in clarification.")
		session_doc = frappe_module.get_doc(session_doctype, doc.name)
		state = get_clarification_state(session_doc)
		if state.has_pending:
			raise RuntimeError("Phase 5.5 pending-override smoke failed: pending clarification was not cleared by the fresh ERP request.")
		return {
			"ok": True,
			"mode": str((payload or {}).get("mode") or "").strip(),
			"answer_text": str(latest_assistant_payload(session_doc).get("text") or "").strip(),
		}

	return run_smoke_session(
		"Phase 5.5 Pending Override Smoke",
		_runner,
		frappe_module=frappe_module,
		session_doctype=session_doctype,
	)


def run_frontdoor_boundary_smoke(
	*,
	run_smoke_session: Callable[..., Dict[str, Any]],
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	get_clarification_state,
	latest_assistant_payload,
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
			raise RuntimeError("Phase 5.5 front-door boundary smoke failed: setup governed ERP turn did not complete.")
		ok, thanks_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="Really Great, thank you",
			user="Administrator",
		)
		if not ok or str((thanks_payload or {}).get("mode") or "").strip() != "front_door":
			raise RuntimeError("Phase 5.5 front-door boundary smoke failed: gratitude after grounded ERP answer did not stay in front door.")
		if str((((thanks_payload or {}).get("agent_meta") or {}).get("intent_class") or "")).strip() != "thanks":
			raise RuntimeError("Phase 5.5 front-door boundary smoke failed: gratitude turn was not classified as thanks.")

		ok, signoff_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="as of now, enough , I will come back later",
			user="Administrator",
		)
		if not ok or str((signoff_payload or {}).get("mode") or "").strip() != "front_door":
			raise RuntimeError("Phase 5.5 front-door boundary smoke failed: closure turn leaked into ERP routing.")
		if str((((signoff_payload or {}).get("agent_meta") or {}).get("intent_class") or "")).strip() != "closure_signoff":
			raise RuntimeError("Phase 5.5 front-door boundary smoke failed: closure turn was not classified as closure_signoff.")

		session_doc = frappe_module.get_doc(session_doctype, doc.name)
		state = get_clarification_state(session_doc)
		if state.has_pending:
			raise RuntimeError("Phase 5.5 front-door boundary smoke failed: front-door path left stale clarification state behind.")
		return {
			"ok": True,
			"thanks_intent": str((((thanks_payload or {}).get("agent_meta") or {}).get("intent_class") or "")).strip(),
			"closure_intent": str((((signoff_payload or {}).get("agent_meta") or {}).get("intent_class") or "")).strip(),
			"final_answer": str(latest_assistant_payload(session_doc).get("text") or "").strip(),
		}

	return run_smoke_session(
		"Phase 5.5 Front Door Boundary Smoke",
		_runner,
		frappe_module=frappe_module,
		session_doctype=session_doctype,
	)


def run_ap_ar_default_policy_smoke(
	*,
	run_smoke_session: Callable[..., Dict[str, Any]],
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	get_clarification_state,
	latest_assistant_payload,
) -> Dict[str, Any]:
	cases = {
		"ar_insight": "give me AR insight",
		"ap_amount": "show me payable amount as of now",
		"ar_ap_insight": "give me AR / AP insight",
	}
	results: Dict[str, Any] = {}

	for case_id, message in cases.items():
		def _runner(doc, case_message: str = message, current_case_id: str = case_id) -> Dict[str, Any]:
			_, payload = handle_qwen_user_message(
				session_name=doc.name,
				message=case_message,
				user="Administrator",
			)
			if str((payload or {}).get("mode") or "").strip() == "clarification":
				raise RuntimeError(
					f"Phase 5.5 AP/AR default-policy smoke failed: case `{current_case_id}` reopened report ambiguity."
				)
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			state = get_clarification_state(session_doc)
			if state.has_pending:
				raise RuntimeError(
					f"Phase 5.5 AP/AR default-policy smoke failed: case `{current_case_id}` left pending clarification state."
				)
			return {
				"mode": str((payload or {}).get("mode") or "").strip(),
				"answer_text": str(latest_assistant_payload(session_doc).get("text") or "").strip(),
			}

		results[case_id] = run_smoke_session(
			f"Phase 5.5 AP AR Policy Smoke {case_id}",
			_runner,
			frappe_module=frappe_module,
			session_doctype=session_doctype,
		)

	return {
		"ok": True,
		"cases": results,
	}


def run_observability_smoke(
	*,
	run_smoke_session: Callable[..., Dict[str, Any]],
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
) -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		ok, hello_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="hello",
			user="Administrator",
		)
		if not ok or str((hello_payload or {}).get("mode") or "").strip() != "front_door":
			raise RuntimeError("Phase 5.5 observability smoke failed: hello was not handled in front door.")
		handle_qwen_user_message(
			session_name=doc.name,
			message="show me financial statement",
			user="Administrator",
		)
		ok, clarification_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="yes",
			user="Administrator",
		)
		if not ok or str((clarification_payload or {}).get("mode") or "").strip() != "clarification":
			raise RuntimeError("Phase 5.5 observability smoke failed: clarification path did not remain active.")
		session_doc = frappe_module.get_doc(session_doctype, doc.name)
		events = [
			item
			for item in session_tool_payloads(session_doc)
			if str(item.get("type") or "").strip() == "qwen_phase55_observability_event"
		]
		if len(events) < 2:
			raise RuntimeError("Phase 5.5 observability smoke failed: expected both front-door and clarification observability events.")
		frontdoor_event = {}
		clarification_event = {}
		for item in events:
			if str(item.get("event_family") or "").strip() == "front_door":
				frontdoor_event = item
			if str(item.get("event_family") or "").strip() == "clarification":
				clarification_event = item
		if str(frontdoor_event.get("event_name") or "").strip() != "handled":
			raise RuntimeError("Phase 5.5 observability smoke failed: missing front-door handled event.")
		if str(clarification_event.get("event_name") or "").strip() != "empty_ack":
			raise RuntimeError("Phase 5.5 observability smoke failed: missing clarification empty_ack event.")
		for item in (frontdoor_event, clarification_event):
			if str(item.get("session_id") or "").strip() != str(doc.name):
				raise RuntimeError("Phase 5.5 observability smoke failed: observability event session_id mismatch.")
			if not str(item.get("request_id") or "").strip():
				raise RuntimeError("Phase 5.5 observability smoke failed: observability event request_id was empty.")
		return {
			"ok": True,
			"event_count": len(events),
			"frontdoor_event": frontdoor_event,
			"clarification_event": clarification_event,
		}

	return run_smoke_session(
		"Phase 5.5 Observability Smoke",
		_runner,
		frappe_module=frappe_module,
		session_doctype=session_doctype,
	)


def run_hardening_suite(
	*,
	clarification_attempt_smoke,
	clarification_meta_question_smoke,
	pending_override_smoke,
	frontdoor_boundary_smoke,
	ap_ar_default_policy_smoke,
	observability_smoke,
) -> Dict[str, Any]:
	return {
		"ok": True,
		"clarification_attempt": clarification_attempt_smoke(),
		"meta_question": clarification_meta_question_smoke(),
		"pending_override": pending_override_smoke(),
		"frontdoor_boundary": frontdoor_boundary_smoke(),
		"ap_ar_default_policy": ap_ar_default_policy_smoke(),
		"observability": observability_smoke(),
	}
