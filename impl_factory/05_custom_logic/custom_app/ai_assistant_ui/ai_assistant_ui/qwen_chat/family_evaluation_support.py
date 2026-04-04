from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List


def _with_compiled_first_turn_full_rollout(
	*,
	frappe_module,
	callback,
):
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
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
		conf[percent_key] = 100
		conf[users_key] = []
		return callback()
	finally:
		for key, was_present in presence.items():
			if was_present:
				conf[key] = originals.get(key)
			else:
				try:
					conf.pop(key, None)
				except Exception:
					pass


def run_followup_fidelity_smoke(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
	latest_assistant_payload,
) -> Dict[str, Any]:
	def _run() -> Dict[str, Any]:
		results: Dict[str, Any] = {}

		doc = frappe_module.new_doc(session_doctype)
		doc.title = "Phase4B Followup Fidelity Smoke"
		doc.insert(ignore_permissions=False)
		try:
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="Top 10 customers by revenue",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Follow-up fidelity smoke failed on initial top-10 ranking request.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			initial_tool_payloads = session_tool_payloads(session_doc)
			initial_artifact = latest_tool_payload_by_type(initial_tool_payloads, "qwen_normalized_family_artifact_contract")
			results["top_n_followup_initial"] = {
				"mode": str((payload or {}).get("mode") or "").strip(),
				"family_id": str(initial_artifact.get("family_id") or "").strip(),
				"has_artifact": bool(initial_artifact),
			}
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="I mean top 5",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Follow-up fidelity smoke failed on top-5 correction.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			rendered = latest_tool_payload_by_type(session_tool_payloads(session_doc), "qwen_rendered_family_response_contract")
			blocks = rendered.get("blocks") if isinstance(rendered.get("blocks"), list) else []
			data_table = next((item for item in blocks if isinstance(item, dict) and str(item.get("block_type") or "").strip() == "data_table"), {})
			rows = data_table.get("rows") if isinstance(data_table.get("rows"), list) else []
			results["top_n_followup"] = {
				"mode": str((payload or {}).get("mode") or "").strip(),
				"title": str(rendered.get("title") or "").strip(),
				"row_count": len(rows),
				"columns": data_table.get("columns") if isinstance(data_table.get("columns"), list) else [],
			}
			if len(rows) != 5:
				raise RuntimeError(
					f"Follow-up fidelity smoke failed: expected 5 ranking rows after correction, observed {len(rows)}. "
					f"mode={str((payload or {}).get('mode') or '').strip()!r} "
					f"initial={results.get('top_n_followup_initial')!r} "
					f"title={str(rendered.get('title') or '').strip()!r}"
				)
		finally:
			frappe_module.delete_doc(session_doctype, doc.name, ignore_permissions=False)

		doc = frappe_module.new_doc(session_doctype)
		doc.title = "Phase4B Metric Fidelity Smoke"
		doc.insert(ignore_permissions=False)
		try:
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="Which products are performing best last month",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Metric fidelity smoke failed on initial product-performance request.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			initial_tool_payloads = session_tool_payloads(session_doc)
			initial_artifact = latest_tool_payload_by_type(initial_tool_payloads, "qwen_normalized_family_artifact_contract")
			results["amount_followup_initial"] = {
				"mode": str((payload or {}).get("mode") or "").strip(),
				"family_id": str(initial_artifact.get("family_id") or "").strip(),
				"has_artifact": bool(initial_artifact),
			}
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="show me with their amount",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Metric fidelity smoke failed on amount refinement.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			rendered = latest_tool_payload_by_type(session_tool_payloads(session_doc), "qwen_rendered_family_response_contract")
			blocks = rendered.get("blocks") if isinstance(rendered.get("blocks"), list) else []
			data_table = next((item for item in blocks if isinstance(item, dict) and str(item.get("block_type") or "").strip() == "data_table"), {})
			columns = data_table.get("columns") if isinstance(data_table.get("columns"), list) else []
			results["amount_followup"] = {
				"mode": str((payload or {}).get("mode") or "").strip(),
				"title": str(rendered.get("title") or "").strip(),
				"columns": columns,
			}
			if not any("Amount" in str(col or "") for col in columns):
				raise RuntimeError(
					f"Metric fidelity smoke failed: amount refinement did not render an amount column. "
					f"mode={str((payload or {}).get('mode') or '').strip()!r} "
					f"initial={results.get('amount_followup_initial')!r} "
					f"title={str(rendered.get('title') or '').strip()!r} columns={columns!r}"
				)
		finally:
			frappe_module.delete_doc(session_doctype, doc.name, ignore_permissions=False)

		doc = frappe_module.new_doc(session_doctype)
		doc.title = "Phase4B Column Fidelity Smoke"
		doc.insert(ignore_permissions=False)
		try:
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="show me top 10 products last month by revenue with item name, revenue, and contribution percent",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Column fidelity smoke failed on explicit revenue/contribution request.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			rendered = latest_tool_payload_by_type(session_tool_payloads(session_doc), "qwen_rendered_family_response_contract")
			blocks = rendered.get("blocks") if isinstance(rendered.get("blocks"), list) else []
			data_table = next((item for item in blocks if isinstance(item, dict) and str(item.get("block_type") or "").strip() == "data_table"), {})
			rows = data_table.get("rows") if isinstance(data_table.get("rows"), list) else []
			columns = data_table.get("columns") if isinstance(data_table.get("columns"), list) else []
			results["explicit_columns"] = {
				"mode": str((payload or {}).get("mode") or "").strip(),
				"title": str(rendered.get("title") or "").strip(),
				"row_count": len(rows),
				"columns": columns,
			}
			if len(rows) != 10:
				raise RuntimeError(f"Column fidelity smoke failed: expected 10 rows, observed {len(rows)}.")
			if not any("Sales Amount" in str(col or "") for col in columns):
				raise RuntimeError(f"Column fidelity smoke failed: explicit revenue request did not render Sales Amount. Observed columns={columns!r}")
			if not any("Contribution" in str(col or "") for col in columns):
				raise RuntimeError(f"Column fidelity smoke failed: explicit contribution request did not render Contribution %. Observed columns={columns!r}")
		finally:
			frappe_module.delete_doc(session_doctype, doc.name, ignore_permissions=False)

		doc = frappe_module.new_doc(session_doctype)
		doc.title = "Phase4B Projection Scope Smoke"
		doc.insert(ignore_permissions=False)
		try:
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="Top 5 products by revenue",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Projection scope smoke failed on initial revenue ranking request.")
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="sorry I mean top 7",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Projection scope smoke failed on top-7 correction.")
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="include qty column",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Projection scope smoke failed on quantity enrichment request.")
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="Show me Item and Qty only",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Projection scope smoke failed on item-and-qty projection request.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			rendered = latest_tool_payload_by_type(session_tool_payloads(session_doc), "qwen_rendered_family_response_contract")
			assistant_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			blocks = rendered.get("blocks") if isinstance(rendered.get("blocks"), list) else []
			data_table = next((item for item in blocks if isinstance(item, dict) and str(item.get("block_type") or "").strip() == "data_table"), {})
			rows = data_table.get("rows") if isinstance(data_table.get("rows"), list) else []
			columns = data_table.get("columns") if isinstance(data_table.get("columns"), list) else []
			title = str(rendered.get("title") or "").strip()
			results["projection_scope_followup"] = {
				"mode": str((payload or {}).get("mode") or "").strip(),
				"title": title,
				"row_count": len(rows),
				"columns": columns,
				"assistant_text": assistant_text,
			}
			if "gross profit" in title.lower():
				raise RuntimeError(f"Projection scope smoke failed: column refinement drifted into gross profit title {title!r}.")
			if str((payload or {}).get("mode") or "").strip() == "artifact_enrichment_boundary":
				lower_text = assistant_text.lower()
				if "governed" not in lower_text and "separate" not in lower_text:
					raise RuntimeError(
						f"Projection scope smoke failed: expected governed enrichment boundary explanation, observed {assistant_text!r}."
					)
			else:
				if len(rows) != 7:
					raise RuntimeError(f"Projection scope smoke failed: expected 7 rows after projection refinement, observed {len(rows)}.")
				if not any("Item" in str(col or "") or "Product" in str(col or "") for col in columns):
					raise RuntimeError(f"Projection scope smoke failed: expected item/product column, observed {columns!r}.")
				if not any("Qty" in str(col or "") or "Quantity" in str(col or "") for col in columns):
					raise RuntimeError(f"Projection scope smoke failed: expected quantity column, observed {columns!r}.")
		finally:
			frappe_module.delete_doc(session_doctype, doc.name, ignore_permissions=False)

		return {"ok": True, "results": results}

	return _with_compiled_first_turn_full_rollout(
		frappe_module=frappe_module,
		callback=_run,
	)


def run_transaction_listing_smoke(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
) -> Dict[str, Any]:
	def _run() -> Dict[str, Any]:
		doc = frappe_module.new_doc(session_doctype)
		doc.title = "Phase4B Transaction Listing Smoke"
		doc.insert(ignore_permissions=False)
		try:
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="show me the last 7 sale invoices",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Transaction listing smoke failed on invoice-list request.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			rendered = latest_tool_payload_by_type(session_tool_payloads(session_doc), "qwen_rendered_family_response_contract")
			blocks = rendered.get("blocks") if isinstance(rendered.get("blocks"), list) else []
			data_table = next((item for item in blocks if isinstance(item, dict) and str(item.get("block_type") or "").strip() == "data_table"), {})
			rows = data_table.get("rows") if isinstance(data_table.get("rows"), list) else []
			columns = data_table.get("columns") if isinstance(data_table.get("columns"), list) else []
			if len(rows) != 7:
				raise RuntimeError(
					f"Transaction listing smoke failed: expected 7 invoice rows, observed {len(rows)}. "
					f"mode={str((payload or {}).get('mode') or '').strip()!r} title={str(rendered.get('title') or '').strip()!r} columns={columns!r}"
				)
			if not any("Invoice" in str(col or "") for col in columns):
				raise RuntimeError(f"Transaction listing smoke failed: invoice column missing. Observed columns={columns!r}")
			if not any("Customer" in str(col or "") for col in columns):
				raise RuntimeError(f"Transaction listing smoke failed: customer column missing. Observed columns={columns!r}")
			return {
				"ok": True,
				"mode": str((payload or {}).get("mode") or "").strip(),
				"title": str(rendered.get("title") or "").strip(),
				"row_count": len(rows),
				"columns": columns,
			}
		finally:
			frappe_module.delete_doc(session_doctype, doc.name, ignore_permissions=False)

	return _with_compiled_first_turn_full_rollout(
		frappe_module=frappe_module,
		callback=_run,
	)


def run_family_evaluation_case(
	*,
	case: Dict[str, Any],
	user: str = "Administrator",
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	latest_assistant_payload,
	parse_payload,
	latest_tool_payload_by_type,
	case_latency_budget_assessment,
) -> Dict[str, Any]:
	message = str(case.get("message") or "").strip()
	case_id = str(case.get("case_id") or "").strip()
	expected_mode = str(case.get("expected_mode") or "").strip()
	expected_compiler_decision = str(case.get("expected_compiler_decision") or "").strip()
	expected_family_validation_status = str(case.get("expected_family_validation_status") or "").strip()
	expected_semantic_status = str(case.get("expected_semantic_status") or "").strip()
	expected_family_id = str(case.get("family_id") or "").strip()
	expected_composite_plan_id = str(case.get("composite_plan_id") or "").strip()

	doc = frappe_module.new_doc(session_doctype)
	doc.title = f"Phase4B Family Evaluation {case_id or 'case'}"
	doc.insert(ignore_permissions=False)
	start = time.perf_counter()
	try:
		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message=message,
			user=user,
		)
		elapsed_ms = int((time.perf_counter() - start) * 1000)
		session_doc = frappe_module.get_doc(session_doctype, doc.name)
		assistant_payload = latest_assistant_payload(session_doc)
		answer_text = str(assistant_payload.get("text") or "").strip()
		tool_payloads = []
		for row in session_doc.get("messages") or []:
			if str(row.role or "").strip().lower() != "tool":
				continue
			payload_obj = parse_payload(str(row.content or ""))
			if payload_obj:
				tool_payloads.append(payload_obj)
		type_names = [str(item.get("type") or "").strip() for item in tool_payloads if isinstance(item, dict)]
		compiled_audit = latest_tool_payload_by_type(tool_payloads, "qwen_compiled_execution_audit_contract")
		family_validation = latest_tool_payload_by_type(tool_payloads, "qwen_family_validation_outcome")
		composite_validation = latest_tool_payload_by_type(tool_payloads, "qwen_composite_read_validation_contract")
		semantic_validation = latest_tool_payload_by_type(tool_payloads, "qwen_semantic_validation_outcome")
		composite_semantic = latest_tool_payload_by_type(tool_payloads, "qwen_composite_semantic_validation")
		fallback_payload = latest_tool_payload_by_type(tool_payloads, "qwen_compiled_rollout_fallback")
		observed_mode = str((payload or {}).get("mode") or "").strip()
		observed_compiler_decision = str((compiled_audit or {}).get("compiler_decision") or "").strip()
		observed_family_id = str((compiled_audit or {}).get("governed_family_id") or "").strip()
		observed_composite_plan_id = str((compiled_audit or {}).get("composite_plan_id") or "").strip()
		observed_family_validation_status = str((compiled_audit or {}).get("family_validation_status") or "").strip()
		if not observed_family_validation_status:
			observed_family_validation_status = str(
				(family_validation or composite_validation or {}).get("status") or ""
			).strip()
		observed_semantic_status = str((compiled_audit or {}).get("semantic_validation_status") or "").strip()
		if not observed_semantic_status:
			observed_semantic_status = str((semantic_validation or composite_semantic or {}).get("status") or "").strip()

		mismatches: List[str] = []
		if expected_mode and observed_mode != expected_mode:
			mismatches.append(f"mode expected `{expected_mode}` but observed `{observed_mode or 'missing'}`")
		if expected_compiler_decision and observed_compiler_decision != expected_compiler_decision:
			mismatches.append(
				f"compiler decision expected `{expected_compiler_decision}` but observed `{observed_compiler_decision or 'missing'}`"
			)
		if expected_family_id and observed_family_id != expected_family_id:
			mismatches.append(f"family expected `{expected_family_id}` but observed `{observed_family_id or 'missing'}`")
		if expected_composite_plan_id and observed_composite_plan_id != expected_composite_plan_id:
			mismatches.append(
				f"composite plan expected `{expected_composite_plan_id}` but observed `{observed_composite_plan_id or 'missing'}`"
			)
		if expected_family_validation_status and observed_family_validation_status != expected_family_validation_status:
			mismatches.append(
				f"family validation expected `{expected_family_validation_status}` but observed `{observed_family_validation_status or 'missing'}`"
			)
		if expected_semantic_status and observed_semantic_status != expected_semantic_status:
			mismatches.append(
				f"semantic status expected `{expected_semantic_status}` but observed `{observed_semantic_status or 'missing'}`"
			)
		resolved_family_id = observed_family_id or expected_family_id
		latency_assessment = case_latency_budget_assessment(
			family_id=resolved_family_id,
			proposal_generation_latency_ms=int(max(0, (compiled_audit or {}).get("proposal_generation_latency_ms") or 0)),
			runtime_execution_latency_ms=int(max(0, (compiled_audit or {}).get("runtime_execution_latency_ms") or 0)),
			total_pipeline_latency_ms=int(max(0, (compiled_audit or {}).get("total_pipeline_latency_ms") or 0)),
		)

		return {
			"case_id": case_id,
			"session_name": doc.name,
			"message": message,
			"ok": bool(ok),
			"elapsed_ms": elapsed_ms,
			"answer_text": answer_text,
			"expected_mode": expected_mode,
			"observed_mode": observed_mode,
			"expected_compiler_decision": expected_compiler_decision,
			"observed_compiler_decision": observed_compiler_decision,
			"expected_family_id": expected_family_id,
			"observed_family_id": observed_family_id,
			"expected_composite_plan_id": expected_composite_plan_id,
			"observed_composite_plan_id": observed_composite_plan_id,
			"expected_family_validation_status": expected_family_validation_status,
			"observed_family_validation_status": observed_family_validation_status,
			"expected_semantic_status": expected_semantic_status,
			"observed_semantic_status": observed_semantic_status,
			"selected_report": str((compiled_audit or {}).get("selected_report") or "").strip(),
			"proposal_generation_latency_ms": int(max(0, (compiled_audit or {}).get("proposal_generation_latency_ms") or 0)),
			"runtime_execution_latency_ms": int(max(0, (compiled_audit or {}).get("runtime_execution_latency_ms") or 0)),
			"total_pipeline_latency_ms": int(max(0, (compiled_audit or {}).get("total_pipeline_latency_ms") or 0)),
			"latency_assessment": latency_assessment,
			"persisted_tool_payload_types": type_names,
			"fallback_payload": fallback_payload,
			"case_ok": bool(ok) and not mismatches,
			"mismatches": mismatches,
		}
	except Exception:
		frappe_module.delete_doc(session_doctype, doc.name, ignore_permissions=False)
		raise


def run_family_evaluation_suite(
	set_id: str = "core_governed_families",
	*,
	frappe_module,
	session_doctype: str,
	list_family_evaluation_case_sets,
	get_family_evaluation_case_set,
	run_family_evaluation_case,
	summarize_compiled_first_turn_audits,
	family_latency_budget_summary,
	get_compiled_first_turn_rollout_status,
) -> Dict[str, Any]:
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
	available_case_sets = [
		str(item.get("set_id") or "").strip()
		for item in list_family_evaluation_case_sets()
		if isinstance(item, dict) and str(item.get("set_id") or "").strip()
	]
	case_set = get_family_evaluation_case_set(set_id)
	if not case_set:
		raise RuntimeError(
			f"Unknown family evaluation case set `{set_id}`. Available sets: {', '.join(available_case_sets) or 'none'}."
		)
	cases = [item for item in list(case_set.get("cases") or []) if isinstance(item, dict)]
	if not cases:
		raise RuntimeError(f"Family evaluation case set `{set_id}` does not contain any cases.")

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
	session_names: List[str] = []
	try:
		conf[flag_key] = True
		conf[percent_key] = 100
		conf[users_key] = []
		results: List[Dict[str, Any]] = []
		for case in cases:
			case_id = str(case.get("case_id") or "").strip()
			try:
				result = run_family_evaluation_case(case=case, user="Administrator")
			except Exception as exc:
				result = {
					"case_id": case_id,
					"session_name": "",
					"message": str(case.get("message") or "").strip(),
					"ok": False,
					"elapsed_ms": 0,
					"answer_text": "",
					"expected_mode": str(case.get("expected_mode") or "").strip(),
					"observed_mode": "",
					"expected_compiler_decision": str(case.get("expected_compiler_decision") or "").strip(),
					"observed_compiler_decision": "",
					"expected_family_id": str(case.get("family_id") or "").strip(),
					"observed_family_id": "",
					"expected_composite_plan_id": str(case.get("composite_plan_id") or "").strip(),
					"observed_composite_plan_id": "",
					"expected_family_validation_status": str(case.get("expected_family_validation_status") or "").strip(),
					"observed_family_validation_status": "",
					"expected_semantic_status": str(case.get("expected_semantic_status") or "").strip(),
					"observed_semantic_status": "",
					"selected_report": "",
					"proposal_generation_latency_ms": 0,
					"runtime_execution_latency_ms": 0,
					"total_pipeline_latency_ms": 0,
					"latency_assessment": {},
					"persisted_tool_payload_types": [],
					"fallback_payload": {},
					"case_ok": False,
					"mismatches": [f"case execution raised `{str(exc).strip() or type(exc).__name__}`"],
				}
			session_name = str(result.get("session_name") or "").strip()
			if session_name:
				session_names.append(session_name)
			results.append(result)
		summary = summarize_compiled_first_turn_audits(
			limit_sessions=max(10, len(session_names)),
			limit_audits=max(50, len(session_names) * 4),
			session_names=session_names,
		)
		failed_cases = [item for item in results if not bool(item.get("case_ok"))]
		return {
			"ok": len(failed_cases) == 0,
			"set_id": str(case_set.get("set_id") or "").strip(),
			"set_label": str(case_set.get("set_label") or "").strip(),
			"description": str(case_set.get("description") or "").strip(),
			"available_case_sets": available_case_sets,
			"case_count": len(results),
			"passed_case_count": len(results) - len(failed_cases),
			"failed_case_count": len(failed_cases),
			"failed_cases": failed_cases,
			"results": results,
			"latency_budget_summary": family_latency_budget_summary(results),
			"family_metrics": summary.get("family_metrics") if isinstance(summary.get("family_metrics"), dict) else {},
			"audit_summary": summary,
			"rollout_status": get_compiled_first_turn_rollout_status(),
		}
	finally:
		for session_name in session_names:
			try:
				frappe_module.delete_doc(session_doctype, session_name, ignore_permissions=False)
			except Exception:
				pass
		for key, was_present in presence.items():
			if was_present:
				conf[key] = originals.get(key)
			else:
				try:
					conf.pop(key, None)
				except Exception:
					pass


def run_full_family_evaluation_suite(
	*,
	list_family_evaluation_case_sets,
	run_family_evaluation_suite,
	family_latency_budget_summary,
) -> Dict[str, Any]:
	set_ids = [
		str(item.get("set_id") or "").strip()
		for item in list_family_evaluation_case_sets()
		if isinstance(item, dict) and str(item.get("set_id") or "").strip()
	]
	if not set_ids:
		raise RuntimeError("No Phase 4B family evaluation case sets are configured.")

	suite_results: List[Dict[str, Any]] = []
	all_results: List[Dict[str, Any]] = []
	failed_cases: List[Dict[str, Any]] = []
	for set_id in set_ids:
		result = run_family_evaluation_suite(set_id=set_id)
		suite_results.append(result)
		for item in list(result.get("results") or []):
			if isinstance(item, dict):
				enriched = dict(item)
				enriched["set_id"] = set_id
				all_results.append(enriched)
		for item in list(result.get("failed_cases") or []):
			if isinstance(item, dict):
				enriched = dict(item)
				enriched["set_id"] = set_id
				failed_cases.append(enriched)

	return {
		"ok": len(failed_cases) == 0,
		"set_ids": set_ids,
		"suite_count": len(suite_results),
		"case_count": len(all_results),
		"passed_case_count": len(all_results) - len(failed_cases),
		"failed_case_count": len(failed_cases),
		"failed_cases": failed_cases,
		"latency_budget_summary": family_latency_budget_summary(all_results),
		"suite_results": suite_results,
	}


def build_family_latency_budget_report(
	*,
	set_id: str = "",
	run_family_evaluation_suite,
	run_full_family_evaluation_suite,
) -> Dict[str, Any]:
	if str(set_id or "").strip():
		result = run_family_evaluation_suite(set_id=str(set_id or "").strip())
	else:
		result = run_full_family_evaluation_suite()
	latency_budget_summary = (
		result.get("latency_budget_summary")
		if isinstance(result.get("latency_budget_summary"), dict)
		else {}
	)
	families = latency_budget_summary.get("families") if isinstance(latency_budget_summary.get("families"), dict) else {}
	return {
		**result,
		"latency_budget_summary": latency_budget_summary,
		"development_budget_ok": bool(families)
		and all(
			bool(item.get("within_development_budget"))
			for item in families.values()
			if isinstance(item, dict)
		),
		"enterprise_target_ok": bool(families)
		and all(
			bool(item.get("within_enterprise_target"))
			for item in families.values()
			if isinstance(item, dict)
		),
	}


def run_family_evaluation_smoke(
	*,
	set_id: str = "core_governed_families",
	run_family_evaluation_suite,
) -> Dict[str, Any]:
	result = run_family_evaluation_suite(set_id=set_id)
	family_metrics = result.get("family_metrics") if isinstance(result.get("family_metrics"), dict) else {}
	if not family_metrics:
		raise RuntimeError(f"Phase 4B family evaluation smoke failed for set `{set_id}`: no family metrics were produced.")
	if int(result.get("case_count") or 0) <= 0:
		raise RuntimeError(f"Phase 4B family evaluation smoke failed for set `{set_id}`: no evaluation cases were executed.")
	return {
		**result,
		"smoke_ok": True,
		"baseline_ok": bool(result.get("ok")),
	}


def run_full_family_evaluation_smoke(
	*,
	run_full_family_evaluation_suite,
) -> Dict[str, Any]:
	result = run_full_family_evaluation_suite()
	if int(result.get("case_count") or 0) <= 0:
		raise RuntimeError("Phase 4B full family evaluation smoke failed: no evaluation cases were executed.")
	return {
		**result,
		"smoke_ok": True,
		"baseline_ok": bool(result.get("ok")),
	}


def run_family_latency_budget_smoke(
	*,
	run_family_latency_budget_report,
) -> Dict[str, Any]:
	result = run_family_latency_budget_report()
	latency_budget_summary = (
		result.get("latency_budget_summary")
		if isinstance(result.get("latency_budget_summary"), dict)
		else {}
	)
	families = latency_budget_summary.get("families") if isinstance(latency_budget_summary.get("families"), dict) else {}
	if not families:
		raise RuntimeError("Phase 4B family latency budget smoke failed: no family latency budget summary was produced.")
	if not bool(result.get("development_budget_ok")):
		raise RuntimeError(
			"Phase 4B family latency budget smoke failed: one or more families exceeded the current development latency budget."
		)
	return {
		**result,
		"smoke_ok": True,
	}


def run_family_tool_surface_smoke(
	messages: List[str] | None = None,
	*,
	frappe_module,
	session_doctype: str,
	build_family_tool_surface_for_message,
	handle_qwen_user_message,
	parse_payload,
) -> Dict[str, Any]:
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
	default_cases = [
		{
			"message": "Top 5 customers by revenue",
			"preferred_intent_class": "ranked_entities",
			"expected_family_id": "ranking_analytics",
		},
	]
	test_cases = []
	for item in (messages or default_cases):
		if isinstance(item, dict):
			message = str(item.get("message") or "").strip()
			if not message:
				continue
			test_cases.append(
				{
					"message": message,
					"preferred_intent_class": str(item.get("preferred_intent_class") or "").strip(),
					"expected_family_id": str(item.get("expected_family_id") or "").strip(),
				}
			)
			continue
		message = str(item or "").strip()
		if not message:
			continue
		test_cases.append(
			{
				"message": message,
				"preferred_intent_class": "",
				"expected_family_id": "",
			}
		)
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
		conf[flag_key] = False
		conf[percent_key] = 0
		conf[users_key] = []
		results: List[Dict[str, Any]] = []
		for case in test_cases:
			message = str(case.get("message") or "").strip()
			preferred_intent_class = str(case.get("preferred_intent_class") or "").strip()
			expected_family_id = str(case.get("expected_family_id") or "").strip()
			expected_surface = build_family_tool_surface_for_message(
				request_id=f"phase4b-family-tool-{uuid.uuid4().hex[:8]}",
				session_id="phase4b-family-tool-surface",
				message=message,
				preferred_intent_class=preferred_intent_class,
			)
			if expected_surface is None:
				raise RuntimeError(
					f"Phase 4B family tool surface smoke failed: no governed family tool surface was built for `{message}`."
				)
			if expected_family_id and expected_family_id not in list(expected_surface.candidate_family_ids or []):
				raise RuntimeError(
					f"Phase 4B family tool surface smoke failed: expected family `{expected_family_id}` was not present for `{message}`."
				)
			doc = frappe_module.new_doc(session_doctype)
			doc.title = "Phase 4B Family Tool Surface Smoke"
			doc.insert(ignore_permissions=False)
			try:
				ok, payload = handle_qwen_user_message(
					session_name=doc.name,
					message=message,
					user="Administrator",
				)
				session_doc = frappe_module.get_doc(session_doctype, doc.name)
				tool_payloads = []
				for row in session_doc.get("messages") or []:
					if str(row.role or "").strip().lower() != "tool":
						continue
					payload_obj = parse_payload(str(row.content or ""))
					if payload_obj:
						tool_payloads.append(payload_obj)
				family_tool_payload = next(
					(
						item
						for item in reversed(tool_payloads)
						if str(item.get("type") or "").strip() == "qwen_family_tool_surface_contract"
					),
					{},
				)
				runtime_trace = next(
					(
						item
						for item in reversed(tool_payloads)
						if str(item.get("type") or "").strip() == "qwen_runtime_trace"
					),
					{},
				)
				tool_trace = runtime_trace.get("tool_trace") if isinstance(runtime_trace.get("tool_trace"), list) else []
				tool_names = [str(item.get("tool") or "").strip() for item in tool_trace if isinstance(item, dict)]
				agent_meta = runtime_trace.get("agent_meta") if isinstance(runtime_trace.get("agent_meta"), dict) else {}
				if bool(agent_meta.get("family_tool_surface_active")):
					raise RuntimeError(
						f"Phase 4B family tool surface smoke failed: retired family tool routing still appeared active for `{message}`."
					)
				if family_tool_payload:
					raise RuntimeError(
						f"Phase 4B family tool surface smoke failed: retired runtime should not persist family tool surface for `{message}`."
					)
				if not bool(ok):
					raise RuntimeError(
						f"Phase 4B family tool surface smoke failed: live service did not return ok for `{message}`."
					)
				results.append(
					{
						"message": message,
						"ok": bool(ok),
						"mode": str((payload or {}).get("mode") or "").strip(),
						"expected_family_id": expected_family_id,
						"candidate_family_ids": list(expected_surface.candidate_family_ids or []),
						"preferred_tool_ids": list(expected_surface.preferred_tool_ids or []),
						"report_discovery_allowed": False,
						"tool_names": tool_names,
						"agent_meta": agent_meta,
						"runtime_family_tool_surface_retired": True,
						"runtime_used_report_discovery": "erp_fac-report_list" in tool_names,
					}
				)
			finally:
				frappe_module.delete_doc(session_doctype, doc.name, ignore_permissions=False)
		return {"ok": True, "results": results}
	finally:
		for key, was_present in presence.items():
			if was_present:
				conf[key] = originals.get(key)
			else:
				try:
					conf.pop(key, None)
				except Exception:
					pass


def run_family_tool_surface_probe(
	*,
	build_family_tool_surface_for_message,
) -> Dict[str, Any]:
	checks = [
		("financial_statement", "Show me P & L statement", "financial_statement"),
		("aging", "Analyze payable aging as of today", "aging_analysis"),
		("ranking_analytics", "Top 5 customers by revenue", "ranked_entities"),
		("trend_analytics", "Show monthly sales trend", "trend_analysis"),
		("product_profitability", "which products are performing well last month", "product_performance"),
	]
	results: List[Dict[str, Any]] = []
	for expected_family_id, message, preferred_intent_class in checks:
		contract = build_family_tool_surface_for_message(
			request_id=f"phase4b-family-probe-{uuid.uuid4().hex[:8]}",
			session_id="phase4b-family-tool-probe",
			message=message,
			preferred_intent_class=preferred_intent_class,
		)
		if contract is None:
			raise RuntimeError(
				f"Phase 4B family tool surface probe failed: no family tool contract was produced for `{message}`."
			)
		candidate_family_ids = list(contract.candidate_family_ids or [])
		if expected_family_id not in candidate_family_ids:
			raise RuntimeError(
				f"Phase 4B family tool surface probe failed: expected family `{expected_family_id}` was not present for `{message}`."
			)
		if contract.report_discovery_allowed:
			raise RuntimeError(
				f"Phase 4B family tool surface probe failed: report discovery remained enabled for `{message}`."
			)
		results.append(
			{
				"message": message,
				"candidate_family_ids": candidate_family_ids,
				"preferred_tool_ids": list(contract.preferred_tool_ids or []),
				"allowed_report_names": list(contract.allowed_report_names or []),
			}
		)
	return {"ok": True, "results": results}


def run_clarification_translation_probe(
	*,
	translate_clarification_signal,
) -> Dict[str, Any]:
	cases = [
		{
			"message": "Analyze company health and suggest area to improve",
			"compiler_reason": "Capability resolution remained ambiguous.",
			"compiler_reason_type": "capability_ambiguity",
			"compiler_details": {
				"capability_candidates": [
					"financial_statement_read",
					"sales_read",
					"accounts_receivable_read",
					"accounts_payable_read",
					"stock_read",
					"product_performance_read",
				]
			},
			"reason_type": "capability_ambiguity",
		},
		{
			"message": "Show me top 10 products last month by revenue",
			"compiler_reason": "The request needs a period before execution.",
			"compiler_reason_type": "time_scope_missing",
			"compiler_details": {"missing_fields": ["from_date"]},
			"reason_type": "time_scope_missing",
		},
	]
	results: List[Dict[str, Any]] = []
	for index, case in enumerate(cases, start=1):
		signal = translate_clarification_signal(
			request_id=f"phase4b-clarify-{index}",
			raw_message=str(case.get("message") or "").strip(),
			compiler_reason=str(case.get("compiler_reason") or "").strip(),
			compiler_reason_type=str(case.get("compiler_reason_type") or "").strip(),
			compiler_details=dict(case.get("compiler_details") or {}),
		)
		question = str(signal.user_question or "").strip()
		if not question:
			raise RuntimeError("Phase 4B clarification probe failed: translated question was empty.")
		if "Ambiguous capability candidates" in question:
			raise RuntimeError("Phase 4B clarification probe failed: compiler ambiguity leaked into user question.")
		if str(signal.reason_type or "").strip() != str(case.get("reason_type") or "").strip():
			raise RuntimeError("Phase 4B clarification probe failed: clarification reason type did not match expected mapping.")
		results.append(
			{
				"message": str(case.get("message") or "").strip(),
				"reason_type": str(signal.reason_type or "").strip(),
				"user_question": question,
				"suggested_options": list(signal.suggested_options or []),
			}
		)
	return {"ok": True, "results": results}


def run_response_policy_probe(
	*,
	build_interaction_contract,
	build_response_policy_contract,
) -> Dict[str, Any]:
	class _DummyFollowupResolution:
		def __init__(self, mode: str, self_contained: bool) -> None:
			self.mode = mode
			self.self_contained = self_contained

	cases = [
		{
			"message": "How much payable do we have as of now",
			"expected_style": "simple_factual",
		},
		{
			"message": "Analyze AR / AP and evaluate company health",
			"expected_style": "analysis_question",
		},
		{
			"message": "Show me P & L statement",
			"expected_style": "statement_question",
		},
		{
			"message": "show me the latest 7 sale invoices",
			"expected_style": "operational_list",
		},
		{
			"message": "how about all the time",
			"expected_style": "followup_refinement",
			"followup_resolution": _DummyFollowupResolution("local_grounded_transform", False),
		},
	]
	results: List[Dict[str, Any]] = []
	for index, case in enumerate(cases, start=1):
		interaction_contract = build_interaction_contract(
			request_id=f"phase4b-policy-{index}",
			session_id="phase4b-policy-probe",
			user_id="Administrator",
			site_name="erpai_prj1",
			raw_message=str(case.get("message") or "").strip(),
		)
		policy = build_response_policy_contract(
			interaction_contract=interaction_contract,
			followup_resolution=case.get("followup_resolution"),
		)
		if str(policy.answer_style or "").strip() != str(case.get("expected_style") or "").strip():
			raise RuntimeError(
				f"Phase 4B response policy probe failed: `{case.get('message')}` mapped to `{policy.answer_style}` instead of `{case.get('expected_style')}`."
			)
		results.append(policy.to_payload())
	return {"ok": True, "results": results}


def run_clarification_policy_smoke(
	*,
	translate_clarification_signal,
	build_interaction_contract,
	build_response_policy_contract,
) -> Dict[str, Any]:
	clarification = run_clarification_translation_probe(
		translate_clarification_signal=translate_clarification_signal,
	)
	policy = run_response_policy_probe(
		build_interaction_contract=build_interaction_contract,
		build_response_policy_contract=build_response_policy_contract,
	)
	return {
		"ok": True,
		"clarification": clarification,
		"response_policy": policy,
	}


def run_natural_narrative_smoke(
	messages: List[str] | None = None,
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	parse_payload,
	latest_tool_payload_by_type,
	latest_assistant_payload,
	assistant_text_payload,
) -> Dict[str, Any]:
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
	default_messages = [
		"How much payable amount do we have as of now",
		"Analyze AR / AP and evaluate company health",
	]
	test_messages = [
		str(item or "").strip()
		for item in (messages or default_messages)
		if str(item or "").strip()
	]
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
		results: List[Dict[str, Any]] = []
		for message in test_messages:
			doc = frappe_module.new_doc(session_doctype)
			doc.title = "Phase 4B Natural Narrative Smoke"
			doc.insert(ignore_permissions=False)
			try:
				ok, payload = handle_qwen_user_message(
					session_name=doc.name,
					message=message,
					user="Administrator",
				)
				if not ok:
					raise RuntimeError(
						f"Phase 4B natural narrative smoke failed: service returned not-ok for `{message}`."
					)
				session_doc = frappe_module.get_doc(session_doctype, doc.name)
				tool_payloads = []
				for row in session_doc.get("messages") or []:
					if str(row.role or "").strip().lower() != "tool":
						continue
					payload_obj = parse_payload(str(row.content or ""))
					if payload_obj:
						tool_payloads.append(payload_obj)
				narrative_payload = latest_tool_payload_by_type(
					tool_payloads,
					"qwen_artifact_narrative_response_contract",
				)
				if not narrative_payload:
					raise RuntimeError(
						f"Phase 4B natural narrative smoke failed: no narrative response contract was persisted for `{message}`."
					)
				assistant_payload = latest_assistant_payload(session_doc)
				answer_text = str(assistant_payload.get("text") or "").strip()
				narrative_text = str(narrative_payload.get("answer_text") or "").strip()
				expected_payload = parse_payload(assistant_text_payload(narrative_text))
				expected_text = str(expected_payload.get("text") or "").strip()
				if not narrative_text or answer_text != expected_text:
					raise RuntimeError(
						f"Phase 4B natural narrative smoke failed: assistant answer did not come from the narrative contract for `{message}`."
					)
				results.append(
					{
						"message": message,
						"mode": str((payload or {}).get("mode") or "").strip(),
						"answer_text": answer_text,
						"narrative_engine": str(narrative_payload.get("narrative_engine") or "").strip(),
						"answer_style": str(narrative_payload.get("answer_style") or "").strip(),
					}
				)
			finally:
				frappe_module.delete_doc(session_doctype, doc.name, ignore_permissions=False)
		return {"ok": True, "results": results}
	finally:
		for key, was_present in presence.items():
			if was_present:
				conf[key] = originals.get(key)
			else:
				try:
					conf.pop(key, None)
				except Exception:
					pass


def run_structured_presentation_smoke(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	latest_assistant_payload,
) -> Dict[str, Any]:
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
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
		doc = frappe_module.new_doc(session_doctype)
		doc.title = "Phase 4B Structured Presentation Smoke"
		doc.insert(ignore_permissions=False)
		try:
			ok, _ = handle_qwen_user_message(
				session_name=doc.name,
				message="Top 5 customers by revenue",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Structured presentation smoke failed on initial analysis request.")
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="Show this as a markdown table and bullet point summary only",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Structured presentation smoke failed on presentation follow-up.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			assistant_payload = latest_assistant_payload(session_doc)
			answer_text = str(assistant_payload.get("text") or "").strip()
			tables = assistant_payload.get("tables") if isinstance(assistant_payload.get("tables"), list) else []
			agent_meta = payload.get("agent_meta") if isinstance(payload, dict) else {}
			transforms = (
				agent_meta.get("transforms")
				if isinstance(agent_meta.get("transforms"), list)
				else []
			)
			has_structured_summary = "Summary" in answer_text and "Top Ranked Rows" in answer_text
			if not tables:
				raise RuntimeError("Structured presentation smoke failed: expected a markdown table in the final assistant answer.")
			if str(agent_meta.get("engine") or "").strip() != "local_transform":
				raise RuntimeError("Structured presentation smoke failed: expected the follow-up to stay in the local transform path.")
			if not has_structured_summary:
				raise RuntimeError("Structured presentation smoke failed: expected a structured summary around the final table output.")
			return {
				"ok": True,
				"answer_text": answer_text,
				"table_count": len(tables),
				"transforms": transforms,
			}
		finally:
			frappe_module.delete_doc(session_doctype, doc.name, ignore_permissions=False)
	finally:
		for key, was_present in presence.items():
			if was_present:
				conf[key] = originals.get(key)
			else:
				try:
					conf.pop(key, None)
				except Exception:
					pass


def run_context_isolation_smoke(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	latest_assistant_payload,
) -> Dict[str, Any]:
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
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
		doc = frappe_module.new_doc(session_doctype)
		doc.title = "Phase 4B Context Isolation Smoke"
		doc.insert(ignore_permissions=False)
		try:
			ok, _ = handle_qwen_user_message(
				session_name=doc.name,
				message="Show me P & L Statement",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Context isolation smoke failed on initial statement request.")
			ok, trend_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="please perform Monthly Sale Trend by Revenue",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Context isolation smoke failed on same-session monthly trend request.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			trend_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if str((trend_payload or {}).get("mode") or "").strip() != "compiled_first_turn":
				raise RuntimeError("Context isolation smoke failed: monthly trend was not treated as a fresh compiled query.")
			if "could not complete a grounded erp lookup" in trend_text.lower():
				raise RuntimeError("Context isolation smoke failed: monthly trend degraded inside the same chat session.")
			ok, staff_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="total number of staff in our company",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Context isolation smoke failed on staff-count request.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			staff_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if "profit and loss statement artifact" in staff_text.lower():
				raise RuntimeError("Context isolation smoke failed: unsupported staff query leaked prior P&L artifact context.")
			if "governed hr" not in staff_text.lower() and "headcount" not in staff_text.lower():
				raise RuntimeError(
					"Context isolation smoke failed: unsupported staff query did not return the governed out-of-scope guidance."
				)
			return {
				"ok": True,
				"trend_mode": str((trend_payload or {}).get("mode") or "").strip(),
				"trend_text": trend_text,
				"staff_mode": str((staff_payload or {}).get("mode") or "").strip(),
				"staff_text": staff_text,
			}
		finally:
			frappe_module.delete_doc(session_doctype, doc.name, ignore_permissions=False)
	finally:
		for key, was_present in presence.items():
			if was_present:
				conf[key] = originals.get(key)
			else:
				try:
					conf.pop(key, None)
				except Exception:
					pass


def run_followup_report_ambiguity_smoke(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	latest_assistant_payload,
) -> Dict[str, Any]:
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
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
		doc = frappe_module.new_doc(session_doctype)
		doc.title = "Phase 4B Followup Report Ambiguity Smoke"
		doc.insert(ignore_permissions=False)
		try:
			ok, _ = handle_qwen_user_message(
				session_name=doc.name,
				message="give me the statement",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Follow-up report ambiguity smoke failed on initial statement request.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			first_question = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if "which financial view would you like to see" not in first_question.lower():
				raise RuntimeError("Follow-up report ambiguity smoke failed: initial statement request did not clarify report choice.")

			ok, _ = handle_qwen_user_message(
				session_name=doc.name,
				message="Balance Sheet",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Follow-up report ambiguity smoke failed on Balance Sheet selection.")

			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="give me the management report",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Follow-up report ambiguity smoke failed on ambiguous report follow-up.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			final_question = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if str(((payload or {}).get("agent_meta") or {}).get("mode") or "").strip() == "followup_report_ambiguity":
				raise RuntimeError("Follow-up report ambiguity smoke failed: retired lexical ambiguity lane was still used.")
			if "which financial view would you like to see" in final_question.lower():
				raise RuntimeError("Follow-up report ambiguity smoke failed: retired lexical ambiguity clarification question still appeared.")
			return {
				"ok": True,
				"initial_question": first_question,
				"final_text": final_question,
				"followup_mode": str((payload or {}).get("mode") or "").strip(),
			}
		finally:
			frappe_module.delete_doc(session_doctype, doc.name, ignore_permissions=False)
	finally:
		for key, was_present in presence.items():
			if was_present:
				conf[key] = originals.get(key)
			else:
				try:
					conf.pop(key, None)
				except Exception:
					pass


def run_entity_drilldown_probe(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	latest_assistant_payload,
	parse_payload,
	latest_qwen_trace_payload,
	latest_grounded_turn_contract,
	latest_normalized_family_artifact,
) -> Dict[str, Any]:
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
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
		doc = frappe_module.new_doc(session_doctype)
		doc.title = "Phase 4B Entity Drilldown Probe"
		doc.insert(ignore_permissions=False)
		try:
			first = handle_qwen_user_message(
				session_name=doc.name,
				message="show me 7 latest sale invoice",
				user="Administrator",
			)
			second = handle_qwen_user_message(
				session_name=doc.name,
				message="give me details of ACC-SINV-2026-00121",
				user="Administrator",
			)
			third = handle_qwen_user_message(
				session_name=doc.name,
				message="Top 7 customers by revenue last month",
				user="Administrator",
			)
			fourth = handle_qwen_user_message(
				session_name=doc.name,
				message="Tell me more about the 35th Street Mobile Wholesale",
				user="Administrator",
			)
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			assistant_payload = latest_assistant_payload(session_doc)
			tool_payloads = []
			for row in session_doc.get("messages") or []:
				if str(row.role or "").strip().lower() != "tool":
					continue
				payload_obj = parse_payload(str(row.content or ""))
				if payload_obj:
					tool_payloads.append(payload_obj)
			return {
				"ok": True,
				"first": first,
				"second": second,
				"third": third,
				"fourth": fourth,
				"assistant_text": str(assistant_payload.get("text") or "").strip(),
				"assistant_payload": assistant_payload,
				"recent_tool_types": [str(item.get("type") or "").strip() for item in tool_payloads[-12:]],
				"recent_trace": latest_qwen_trace_payload(session_doc),
				"latest_grounded_turn": latest_grounded_turn_contract(session_doc),
				"latest_artifact": latest_normalized_family_artifact(session_doc),
			}
		finally:
			frappe_module.delete_doc(session_doctype, doc.name, ignore_permissions=False)
	finally:
		for key, was_present in presence.items():
			if was_present:
				conf[key] = originals.get(key)
			else:
				try:
					conf.pop(key, None)
				except Exception:
					pass


def run_entity_drilldown_smoke(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	latest_assistant_payload,
) -> Dict[str, Any]:
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
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
		doc = frappe_module.new_doc(session_doctype)
		doc.title = "Phase 4B Entity Drilldown Smoke"
		doc.insert(ignore_permissions=False)
		try:
			ok, _ = handle_qwen_user_message(
				session_name=doc.name,
				message="show me 7 latest sale invoice",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Entity drilldown smoke failed on invoice listing request.")
			ok, invoice_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="give me details of ACC-SINV-2026-00121",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Entity drilldown smoke failed on invoice detail request.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			invoice_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if "acc-sinv-2026-00121" not in invoice_text.lower():
				raise RuntimeError("Entity drilldown smoke failed: invoice detail answer did not switch to the requested invoice.")
			if str((invoice_payload or {}).get("agent_meta", {}).get("engine") or "").strip() != "entity_detail":
				raise RuntimeError("Entity drilldown smoke failed: invoice detail did not use the governed entity-detail engine.")
			ok, delivery_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="these items are already delivered to customers?",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Entity drilldown smoke failed on delivery-status safety follow-up.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			delivery_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if "can't confirm it confidently from this artifact alone" not in delivery_text.lower():
				raise RuntimeError(
					"Entity drilldown smoke failed: unsupported delivery-status follow-up did not stop at a grounded evidence boundary. "
					f"Observed={delivery_text!r}"
				)

			ok, _ = handle_qwen_user_message(
				session_name=doc.name,
				message="Top 7 customers by revenue last month",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Entity drilldown smoke failed on ranking request.")
			ok, customer_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="Tell me more about the 35th Street Mobile Wholesale",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Entity drilldown smoke failed on customer detail request.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			customer_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if "35th street mobile wholesale" not in customer_text.lower():
				raise RuntimeError("Entity drilldown smoke failed: customer detail answer did not switch to the requested customer.")
			if str((customer_payload or {}).get("agent_meta", {}).get("engine") or "").strip() != "entity_detail":
				raise RuntimeError("Entity drilldown smoke failed: customer detail did not use the governed entity-detail engine.")
			return {
				"ok": True,
				"invoice_mode": str((invoice_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
				"invoice_text": invoice_text,
				"delivery_boundary_mode": str((delivery_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
				"delivery_boundary_text": delivery_text,
				"customer_mode": str((customer_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
				"customer_text": customer_text,
			}
		finally:
			frappe_module.delete_doc(session_doctype, doc.name, ignore_permissions=False)
	finally:
		for key, was_present in presence.items():
			if was_present:
				conf[key] = originals.get(key)
			else:
				try:
					conf.pop(key, None)
				except Exception:
					pass
