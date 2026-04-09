from __future__ import annotations

from datetime import date, timedelta
import json
import time
import uuid
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.smoke_fixtures import smoke_fixture_replacement_message


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
		frappe_module.db.commit()
		frappe_module.clear_cache()
		conf[flag_key] = True
		conf[percent_key] = 100
		conf[users_key] = []
		frappe_module.db.commit()
		frappe_module.clear_cache()
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
		try:
			frappe_module.db.commit()
			frappe_module.clear_cache()
		except Exception:
			pass


def _create_committed_smoke_session_doc(
	*,
	frappe_module,
	session_doctype: str,
	title: str,
):
	doc = frappe_module.new_doc(session_doctype)
	doc.title = str(title or "").strip()
	doc.insert(ignore_permissions=False)
	# Make the session durable before later save retries rollback transaction state.
	frappe_module.db.commit()
	return doc


def _delete_committed_smoke_session_doc(
	*,
	frappe_module,
	session_doctype: str,
	doc_name: str,
) -> None:
	clean_name = str(doc_name or "").strip()
	if not clean_name:
		return
	try:
		frappe_module.delete_doc(session_doctype, clean_name, ignore_permissions=False)
		frappe_module.db.commit()
	except Exception:
		pass


def _latest_request_scoped_tool_payload_by_type(
	tool_payloads: List[Dict[str, Any]],
	payload_type: str,
	request_id: str,
	*,
	latest_tool_payload_by_type,
) -> Dict[str, Any]:
	clean_type = str(payload_type or "").strip()
	clean_request_id = str(request_id or "").strip()
	if clean_type and clean_request_id:
		for item in reversed(tool_payloads):
			if str(item.get("type") or "").strip() != clean_type:
				continue
			item_request_id = str(
				item.get("request_id")
				or item.get("trace_request_id")
				or item.get("source_request_id")
				or ""
			).strip()
			if item_request_id == clean_request_id:
				return item
	return latest_tool_payload_by_type(tool_payloads, payload_type)


def _stabilize_turn_family_visibility(
	*,
	frappe_module,
	session_doctype: str,
	session_name: str,
	expected_request_id: str,
	prior_rendered_answer_text: str,
	session_tool_payloads,
	latest_tool_payload_by_type,
	attempts: int = 4,
	delay_seconds: float = 0.1,
) -> Dict[str, Any]:
	clean_request_id = str(expected_request_id or "").strip()
	prior_answer_text = str(prior_rendered_answer_text or "").strip()
	last_result = {
		"session_doc": None,
		"tool_payloads": [],
		"grounded_turn": {},
		"rendered": {},
		"artifact": {},
	}
	for attempt in range(max(1, int(attempts))):
		frappe_module.db.commit()
		frappe_module.clear_cache()
		session_doc = frappe_module.get_doc(session_doctype, session_name)
		tool_payloads = session_tool_payloads(session_doc)
		grounded_turn = _latest_request_scoped_tool_payload_by_type(
			tool_payloads,
			"qwen_grounded_turn_context",
			clean_request_id,
			latest_tool_payload_by_type=latest_tool_payload_by_type,
		)
		rendered = latest_tool_payload_by_type(tool_payloads, "qwen_rendered_family_response_contract")
		artifact = latest_tool_payload_by_type(tool_payloads, "qwen_normalized_family_artifact_contract")
		rendered_answer_text = str(rendered.get("answer_text") or "").strip()
		grounded_request_id = str(
			grounded_turn.get("trace_request_id") or grounded_turn.get("request_id") or ""
		).strip()
		grounded_source_name = str(grounded_turn.get("source_name") or "").strip()
		rendered_source_reports = [
			str(item or "").strip()
			for item in (rendered.get("source_reports") or [])
			if str(item or "").strip()
		]
		artifact_source_reports = [
			str(item or "").strip()
			for item in (artifact.get("source_reports") or [])
			if str(item or "").strip()
		]
		report_coherent = (
			not grounded_source_name
			or grounded_source_name in rendered_source_reports
			or grounded_source_name in artifact_source_reports
		)
		last_result = {
			"session_doc": session_doc,
			"tool_payloads": tool_payloads,
			"grounded_turn": grounded_turn,
			"rendered": rendered,
			"artifact": artifact,
		}
		if (
			grounded_request_id == clean_request_id
			and rendered_answer_text
			and rendered_answer_text != prior_answer_text
			and report_coherent
		):
			return last_result
		if attempt + 1 < max(1, int(attempts)):
			time.sleep(max(0.0, float(delay_seconds)))
	return last_result


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


def _run_document_listing_smoke(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
	smoke_title: str,
	request_message: str,
	expected_row_count: int,
	minimum_row_count: int = 0,
	required_title_fragment: str,
	required_column_groups: List[List[str]],
) -> Dict[str, Any]:
	def _transient_listing_retry_allowed(payload: Dict[str, Any], rows: List[Any], columns: List[Any], rendered_title: str) -> bool:
		mode = str((payload or {}).get("mode") or "").strip()
		family_status = str((payload or {}).get("family_validation_status") or "").strip()
		semantic_status = str((payload or {}).get("semantic_validation_status") or "").strip()
		return (
			mode == "compiled_first_turn"
			and not rows
			and not columns
			and not str(rendered_title or "").strip()
			and family_status == "reject_family_inconsistent"
			and semantic_status == "reject_semantically_inconsistent"
		)

	def _run() -> Dict[str, Any]:
		last_error: RuntimeError | None = None
		for attempt in range(4):
			doc = _create_committed_smoke_session_doc(
				frappe_module=frappe_module,
				session_doctype=session_doctype,
				title=smoke_title,
			)
			try:
				ok, payload = handle_qwen_user_message(
					session_name=doc.name,
					message=request_message,
					user="Administrator",
				)
				if not ok:
					raise RuntimeError(f"{smoke_title} failed: governed listing request did not complete.")
				session_doc = frappe_module.get_doc(session_doctype, doc.name)
				rendered = latest_tool_payload_by_type(session_tool_payloads(session_doc), "qwen_rendered_family_response_contract")
				blocks = rendered.get("blocks") if isinstance(rendered.get("blocks"), list) else []
				data_table = next((item for item in blocks if isinstance(item, dict) and str(item.get("block_type") or "").strip() == "data_table"), {})
				rows = data_table.get("rows") if isinstance(data_table.get("rows"), list) else []
				columns = data_table.get("columns") if isinstance(data_table.get("columns"), list) else []
				rendered_title = str(rendered.get("title") or "").strip()
				if int(expected_row_count) > 0:
					if len(rows) != int(expected_row_count):
						raise RuntimeError(
							f"{smoke_title} failed: expected {expected_row_count} rows, observed {len(rows)}. "
							f"mode={str((payload or {}).get('mode') or '').strip()!r} title={rendered_title!r} columns={columns!r}"
						)
				elif len(rows) < int(max(1, minimum_row_count)):
					raise RuntimeError(
						f"{smoke_title} failed: expected at least {max(1, minimum_row_count)} rows, observed {len(rows)}. "
						f"mode={str((payload or {}).get('mode') or '').strip()!r} title={rendered_title!r} columns={columns!r}"
					)
				if required_title_fragment and required_title_fragment not in rendered_title:
					raise RuntimeError(
						f"{smoke_title} failed: expected title fragment {required_title_fragment!r}, observed {rendered_title!r}."
					)
				for column_group in required_column_groups:
					fragments = [str(item or "").strip() for item in (column_group or []) if str(item or "").strip()]
					if not fragments:
						continue
					if not any(any(fragment in str(col or "") for fragment in fragments) for col in columns):
						raise RuntimeError(
							f"{smoke_title} failed: missing required column group {fragments!r}. Observed columns={columns!r}"
						)
				return {
					"ok": True,
					"mode": str((payload or {}).get("mode") or "").strip(),
					"title": rendered_title,
					"row_count": len(rows),
					"columns": columns,
				}
			except RuntimeError as exc:
				last_error = exc
				if attempt >= 3 or not _transient_listing_retry_allowed(payload if isinstance(payload, dict) else {}, rows if 'rows' in locals() else [], columns if 'columns' in locals() else [], rendered_title if 'rendered_title' in locals() else ""):
					raise
				frappe_module.db.commit()
				frappe_module.clear_cache()
				time.sleep(0.25 * (attempt + 1))
			finally:
				_delete_committed_smoke_session_doc(
					frappe_module=frappe_module,
					session_doctype=session_doctype,
					doc_name=doc.name,
				)
		if last_error is not None:
			raise last_error
		raise RuntimeError(f"{smoke_title} failed without an explicit error.")

	return _with_compiled_first_turn_full_rollout(
		frappe_module=frappe_module,
		callback=_run,
	)


def _parse_rendered_iso_date(value: Any) -> date | None:
	text = str(value or "").strip()
	if not text:
		return None
	candidates = [text, text[:10]]
	for candidate in candidates:
		candidate = str(candidate or "").strip()
		if not candidate:
			continue
		try:
			return date.fromisoformat(candidate)
		except Exception:
			continue
	return None


def _last_month_window() -> tuple[date, date]:
	today = date.today()
	first_this_month = today.replace(day=1)
	last_previous_month = first_this_month - timedelta(days=1)
	first_previous_month = last_previous_month.replace(day=1)
	return first_previous_month, last_previous_month


def _select_delivery_note_status_probe_value(frappe_module) -> str:
	rows = frappe_module.get_all(
		"Delivery Note",
		fields=["status"],
		filters={"docstatus": 1},
		order_by="modified desc",
		limit_page_length=100,
	)
	counts: Dict[str, int] = {}
	for row in rows or []:
		if not isinstance(row, dict):
			continue
		status = str(row.get("status") or "").strip()
		if not status:
			continue
		counts[status] = counts.get(status, 0) + 1
	if not counts:
		raise RuntimeError("Delivery Note status probe failed: no submitted Delivery Note statuses were available.")
	preferred_order = [
		"Completed",
		"To Bill",
		"To Deliver and Bill",
		"To Bill and Deliver",
		"Partially Billed",
		"Return Issued",
	]
	for status in preferred_order:
		if counts.get(status):
			return status
	return sorted(counts.items(), key=lambda item: (-int(item[1] or 0), str(item[0] or "")))[0][0]


def _run_document_listing_date_scope_probe(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
	smoke_title: str,
	request_message: str,
	required_title_fragment: str,
	required_column_groups: List[List[str]],
	date_column_fragments: List[str],
	expected_start_date: date,
	expected_end_date: date,
	minimum_row_count: int = 1,
) -> Dict[str, Any]:
	def _run() -> Dict[str, Any]:
		doc = _create_committed_smoke_session_doc(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			title=smoke_title,
		)
		try:
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message=request_message,
				user="Administrator",
			)
			if not ok:
				raise RuntimeError(f"{smoke_title} failed: governed listing request did not complete.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			rendered = latest_tool_payload_by_type(session_tool_payloads(session_doc), "qwen_rendered_family_response_contract")
			blocks = rendered.get("blocks") if isinstance(rendered.get("blocks"), list) else []
			data_table = next((item for item in blocks if isinstance(item, dict) and str(item.get("block_type") or "").strip() == "data_table"), {})
			rows = data_table.get("rows") if isinstance(data_table.get("rows"), list) else []
			columns = data_table.get("columns") if isinstance(data_table.get("columns"), list) else []
			rendered_title = str(rendered.get("title") or "").strip()
			if len(rows) < int(max(1, minimum_row_count)):
				raise RuntimeError(
					f"{smoke_title} failed: expected at least {max(1, minimum_row_count)} rows, observed {len(rows)}. "
					f"mode={str((payload or {}).get('mode') or '').strip()!r} title={rendered_title!r} columns={columns!r}"
				)
			if required_title_fragment and required_title_fragment not in rendered_title:
				raise RuntimeError(
					f"{smoke_title} failed: expected title fragment {required_title_fragment!r}, observed {rendered_title!r}."
				)
			for column_group in required_column_groups:
				fragments = [str(item or "").strip() for item in (column_group or []) if str(item or "").strip()]
				if not fragments:
					continue
				if not any(any(fragment in str(col or "") for fragment in fragments) for col in columns):
					raise RuntimeError(
						f"{smoke_title} failed: missing required column group {fragments!r}. Observed columns={columns!r}"
					)
			date_index = next(
				(
					index
					for index, column_name in enumerate(columns)
					if any(str(fragment or "").strip() in str(column_name or "") for fragment in date_column_fragments)
				),
				-1,
			)
			if date_index < 0:
				raise RuntimeError(
					f"{smoke_title} failed: missing date column fragments {date_column_fragments!r}. Observed columns={columns!r}"
				)
			observed_dates: List[str] = []
			for row_index, row in enumerate(rows):
				if not isinstance(row, list) or date_index >= len(row):
					raise RuntimeError(
						f"{smoke_title} failed: row {row_index} does not contain date column index {date_index}. Row={row!r}"
					)
				rendered_date = _parse_rendered_iso_date(row[date_index])
				if rendered_date is None:
					raise RuntimeError(
						f"{smoke_title} failed: could not parse rendered date {row[date_index]!r} from row {row_index}."
					)
				observed_dates.append(rendered_date.isoformat())
				if rendered_date < expected_start_date or rendered_date > expected_end_date:
					raise RuntimeError(
						f"{smoke_title} failed: observed posting date {rendered_date.isoformat()} outside expected range "
						f"{expected_start_date.isoformat()}..{expected_end_date.isoformat()}."
					)
			return {
				"ok": True,
				"mode": str((payload or {}).get("mode") or "").strip(),
				"title": rendered_title,
				"row_count": len(rows),
				"columns": columns,
				"posting_dates": observed_dates,
				"expected_start_date": expected_start_date.isoformat(),
				"expected_end_date": expected_end_date.isoformat(),
			}
		finally:
			_delete_committed_smoke_session_doc(
				frappe_module=frappe_module,
				session_doctype=session_doctype,
				doc_name=doc.name,
			)

	return _with_compiled_first_turn_full_rollout(
		frappe_module=frappe_module,
		callback=_run,
	)


def _run_document_listing_status_probe(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
	smoke_title: str,
	required_title_fragment: str,
	required_column_groups: List[List[str]],
	status_column_fragments: List[str],
	minimum_row_count: int = 1,
) -> Dict[str, Any]:
	def _run() -> Dict[str, Any]:
		expected_status = _select_delivery_note_status_probe_value(frappe_module)
		request_message = f"show me delivery notes with status {expected_status}"
		doc = _create_committed_smoke_session_doc(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			title=smoke_title,
		)
		try:
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message=request_message,
				user="Administrator",
			)
			if not ok:
				raise RuntimeError(f"{smoke_title} failed: governed listing request did not complete.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			rendered = latest_tool_payload_by_type(session_tool_payloads(session_doc), "qwen_rendered_family_response_contract")
			blocks = rendered.get("blocks") if isinstance(rendered.get("blocks"), list) else []
			data_table = next((item for item in blocks if isinstance(item, dict) and str(item.get("block_type") or "").strip() == "data_table"), {})
			rows = data_table.get("rows") if isinstance(data_table.get("rows"), list) else []
			columns = data_table.get("columns") if isinstance(data_table.get("columns"), list) else []
			rendered_title = str(rendered.get("title") or "").strip()
			if len(rows) < int(max(1, minimum_row_count)):
				raise RuntimeError(
					f"{smoke_title} failed: expected at least {max(1, minimum_row_count)} rows, observed {len(rows)}. "
					f"mode={str((payload or {}).get('mode') or '').strip()!r} title={rendered_title!r} columns={columns!r}"
				)
			if required_title_fragment and required_title_fragment not in rendered_title:
				raise RuntimeError(
					f"{smoke_title} failed: expected title fragment {required_title_fragment!r}, observed {rendered_title!r}."
				)
			for column_group in required_column_groups:
				fragments = [str(item or "").strip() for item in (column_group or []) if str(item or "").strip()]
				if not fragments:
					continue
				if not any(any(fragment in str(col or "") for fragment in fragments) for col in columns):
					raise RuntimeError(
						f"{smoke_title} failed: missing required column group {fragments!r}. Observed columns={columns!r}"
					)
			status_index = next(
				(
					index
					for index, column_name in enumerate(columns)
					if any(str(fragment or "").strip() in str(column_name or "") for fragment in status_column_fragments)
				),
				-1,
			)
			if status_index < 0:
				raise RuntimeError(
					f"{smoke_title} failed: missing status column fragments {status_column_fragments!r}. Observed columns={columns!r}"
				)
			observed_statuses: List[str] = []
			for row_index, row in enumerate(rows):
				if not isinstance(row, list) or status_index >= len(row):
					raise RuntimeError(
						f"{smoke_title} failed: row {row_index} does not contain status column index {status_index}. Row={row!r}"
					)
				observed_status = str(row[status_index] or "").strip()
				if not observed_status:
					raise RuntimeError(
						f"{smoke_title} failed: row {row_index} did not contain a rendered status value. Row={row!r}"
					)
				observed_statuses.append(observed_status)
				if observed_status != expected_status:
					raise RuntimeError(
						f"{smoke_title} failed: observed status {observed_status!r} did not match expected {expected_status!r}."
					)
			return {
				"ok": True,
				"mode": str((payload or {}).get("mode") or "").strip(),
				"title": rendered_title,
				"row_count": len(rows),
				"columns": columns,
				"expected_status": expected_status,
				"observed_statuses": observed_statuses,
				"request_message": request_message,
			}
		finally:
			_delete_committed_smoke_session_doc(
				frappe_module=frappe_module,
				session_doctype=session_doctype,
				doc_name=doc.name,
			)

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
	return _run_document_listing_smoke(
		frappe_module=frappe_module,
		session_doctype=session_doctype,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=session_tool_payloads,
		latest_tool_payload_by_type=latest_tool_payload_by_type,
		smoke_title="Phase4B Transaction Listing Smoke",
		request_message="show me the last 7 sale invoices",
		expected_row_count=7,
		minimum_row_count=0,
		required_title_fragment="Sales Invoice",
		required_column_groups=[["Invoice"], ["Customer"]],
	)


def run_delivery_note_listing_smoke(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
) -> Dict[str, Any]:
	return _run_document_listing_smoke(
		frappe_module=frappe_module,
		session_doctype=session_doctype,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=session_tool_payloads,
		latest_tool_payload_by_type=latest_tool_payload_by_type,
		smoke_title="Phase1.1 Delivery Note Listing Smoke",
		request_message="show me the last 5 delivery notes",
		expected_row_count=5,
		minimum_row_count=0,
		required_title_fragment="Delivery Note",
		required_column_groups=[["Delivery", "Note"], ["Customer"], ["Qty", "Quantity"]],
	)


def run_purchase_order_listing_smoke(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
) -> Dict[str, Any]:
	return _run_document_listing_smoke(
		frappe_module=frappe_module,
		session_doctype=session_doctype,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=session_tool_payloads,
		latest_tool_payload_by_type=latest_tool_payload_by_type,
		smoke_title="Phase1.3 Purchase Order Listing Smoke",
		request_message="show me latest 5 purchase orders",
		expected_row_count=5,
		minimum_row_count=0,
		required_title_fragment="Purchase Order",
		required_column_groups=[["Purchase", "Order"], ["Supplier"], ["Qty", "Quantity"]],
	)


def run_customer_credit_exposure_smoke(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
	latest_assistant_payload,
	) -> Dict[str, Any]:
	def _run() -> Dict[str, Any]:
		doc = _create_committed_smoke_session_doc(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			title="Phase1.4 Customer Credit Exposure Smoke",
		)
		try:
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="show me customer credit exposure",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.4 Customer Credit Exposure Smoke failed on customer-credit request.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			assistant_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			tool_payloads = session_tool_payloads(session_doc)
			artifact_payload = latest_tool_payload_by_type(tool_payloads, "qwen_normalized_family_artifact_contract")
			rendered_payload = latest_tool_payload_by_type(tool_payloads, "qwen_rendered_family_response_contract")
			family_id = str((artifact_payload or {}).get("family_id") or "").strip()
			source_reports = [
				str(item or "").strip()
				for item in ((artifact_payload or {}).get("source_reports") or [])
				if str(item or "").strip()
			]
			parties = [
				item
				for item in (((artifact_payload or {}).get("sections") or {}).get("parties") or [])
				if isinstance(item, dict)
			]
			party_names = {
				str(item.get("party") or "").strip().lower()
				for item in parties
				if str(item.get("party") or "").strip()
			}
			title = str((rendered_payload or {}).get("title") or "").strip()
			lower_text = assistant_text.lower()
			if family_id != "aging":
				raise RuntimeError(
					f"Phase1.4 Customer Credit Exposure Smoke failed: expected family 'aging', observed {family_id!r}."
				)
			if source_reports != ["Accounts Receivable Summary"]:
				raise RuntimeError(
					f"Phase1.4 Customer Credit Exposure Smoke failed: expected Accounts Receivable Summary, observed {source_reports!r}."
				)
			if "Accounts Receivable Aging" not in title:
				raise RuntimeError(
					f"Phase1.4 Customer Credit Exposure Smoke failed: rendered title did not expose receivable aging. Observed={title!r}"
				)
			if "pazundaung mobile distribution" not in party_names:
				raise RuntimeError(
					"Phase1.4 Customer Credit Exposure Smoke failed: governed artifact did not include the expected leading customer exposure row."
				)
			if "thaketa mobile exchange" not in party_names:
				raise RuntimeError(
					"Phase1.4 Customer Credit Exposure Smoke failed: negative-balance customer was not preserved in the governed exposure artifact."
				)
			if "credit limit" in lower_text:
				raise RuntimeError(
					"Phase1.4 Customer Credit Exposure Smoke failed: answer overreached into credit-limit policy."
				)
			if "chronic" in lower_text or "short-term delay" in lower_text or "collection issue" in lower_text:
				raise RuntimeError(
					"Phase1.4 Customer Credit Exposure Smoke failed: answer overreached into interpretive collection commentary."
				)
			return {
				"ok": True,
				"mode": str((payload or {}).get("mode") or "").strip(),
				"title": title,
				"family_id": family_id,
				"source_reports": source_reports,
				"party_names": sorted(party_names),
				"answer_text": assistant_text,
			}
		finally:
			_delete_committed_smoke_session_doc(
				frappe_module=frappe_module,
				session_doctype=session_doctype,
				doc_name=doc.name,
			)

	return _with_compiled_first_turn_full_rollout(
		frappe_module=frappe_module,
		callback=_run,
	)


def run_customer_credit_scope_reset_smoke(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
	latest_assistant_payload,
) -> Dict[str, Any]:
	def _run() -> Dict[str, Any]:
		doc = _create_committed_smoke_session_doc(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			title="Phase1.4 Customer Credit Scope Reset Smoke",
		)
		try:
			ok, first_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="show customer credit status as of today",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.4 Customer Credit Scope Reset Smoke failed on credit-status request.")
			ok, second_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="show me customer credit exposure",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.4 Customer Credit Scope Reset Smoke failed on customer-credit exposure request.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			assistant_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			assistant_lower = assistant_text.lower()
			if "collection risk" in assistant_lower or "chronic" in assistant_lower or "temporary delays" in assistant_lower:
				raise RuntimeError(
					"Phase1.4 Customer Credit Scope Reset Smoke failed: customer-credit re-ask still drifted into unsupported collection-behavior commentary."
				)
			if "accounts receivable aging as of 2026-04-09" not in assistant_lower:
				raise RuntimeError(
					"Phase1.4 Customer Credit Scope Reset Smoke failed: customer-credit re-ask did not return the governed aging artifact."
				)
			tool_payloads = session_tool_payloads(session_doc)
			scope_payload = latest_tool_payload_by_type(tool_payloads, "qwen_governed_scope_decision_contract")
			followup_payload = latest_tool_payload_by_type(tool_payloads, "qwen_followup_resolution")
			scope_status = str((scope_payload or {}).get("governed_scope_status") or "").strip()
			followup_mode = str((followup_payload or {}).get("mode") or "").strip()
			if scope_status != "fresh_query_breakout":
				raise RuntimeError(
					f"Phase1.4 Customer Credit Scope Reset Smoke failed: expected governed scope status 'fresh_query_breakout', observed {scope_status!r}."
				)
			if followup_mode != "new_query":
				raise RuntimeError(
					f"Phase1.4 Customer Credit Scope Reset Smoke failed: expected follow-up mode 'new_query', observed {followup_mode!r}."
				)
			return {
				"ok": True,
				"mode": str((second_payload or {}).get("mode") or "").strip(),
				"scope_status": scope_status,
				"followup_mode": followup_mode,
				"answer_text": assistant_text,
			}
		finally:
			_delete_committed_smoke_session_doc(
				frappe_module=frappe_module,
				session_doctype=session_doctype,
				doc_name=doc.name,
			)

	return _with_compiled_first_turn_full_rollout(
		frappe_module=frappe_module,
		callback=_run,
	)


def run_customer_credit_scope_reset_probe(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
	latest_assistant_payload,
	latest_qwen_trace_payload,
	latest_grounded_turn_contract,
) -> Dict[str, Any]:
	def _run() -> Dict[str, Any]:
		doc = _create_committed_smoke_session_doc(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			title="Phase1.4 Customer Credit Scope Reset Probe",
		)
		try:
			first_ok, first_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="show customer credit status as of today",
				user="Administrator",
			)
			second_ok, second_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="show me customer credit exposure",
				user="Administrator",
			)
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			assistant_payload = latest_assistant_payload(session_doc)
			tool_payloads = session_tool_payloads(session_doc)
			scope_payload = latest_tool_payload_by_type(tool_payloads, "qwen_governed_scope_decision_contract")
			followup_payload = latest_tool_payload_by_type(tool_payloads, "qwen_followup_resolution")
			narrative_payload = latest_tool_payload_by_type(tool_payloads, "qwen_artifact_narrative_response_contract")
			rendered_payload = latest_tool_payload_by_type(tool_payloads, "qwen_rendered_family_response_contract")
			return {
				"ok": True,
				"first_ok": bool(first_ok),
				"second_ok": bool(second_ok),
				"first_payload": first_payload,
				"second_payload": second_payload,
				"assistant_text": str(assistant_payload.get("text") or "").strip(),
				"scope_status": str((scope_payload or {}).get("governed_scope_status") or "").strip(),
				"followup_mode": str((followup_payload or {}).get("mode") or "").strip(),
				"narrative_answer_text": str((narrative_payload or {}).get("answer_text") or "").strip(),
				"rendered_answer_text": str((rendered_payload or {}).get("answer_text") or "").strip(),
				"recent_tool_types": [str(item.get("type") or "").strip() for item in tool_payloads[-12:]],
				"latest_trace": latest_qwen_trace_payload(session_doc),
				"latest_grounded_turn": latest_grounded_turn_contract(session_doc),
			}
		finally:
			_delete_committed_smoke_session_doc(
				frappe_module=frappe_module,
				session_doctype=session_doctype,
				doc_name=doc.name,
			)

	return _with_compiled_first_turn_full_rollout(
		frappe_module=frappe_module,
		callback=_run,
	)


def run_customer_credit_overdue_smoke(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
	latest_assistant_payload,
) -> Dict[str, Any]:
	def _run() -> Dict[str, Any]:
		doc = _create_committed_smoke_session_doc(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			title="Phase1.4 Customer Credit Overdue Smoke",
		)
		try:
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="show overdue customers as of today",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.4 Customer Credit Overdue Smoke failed on overdue request.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			assistant_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			tool_payloads = session_tool_payloads(session_doc)
			artifact_payload = latest_tool_payload_by_type(tool_payloads, "qwen_normalized_family_artifact_contract")
			family_id = str((artifact_payload or {}).get("family_id") or "").strip()
			source_reports = [
				str(item or "").strip()
				for item in ((artifact_payload or {}).get("source_reports") or [])
				if str(item or "").strip()
			]
			filter_mode = str(((artifact_payload or {}).get("dimensions") or {}).get("filter_mode") or "").strip()
			if family_id != "aging":
				raise RuntimeError(
					f"Phase1.4 Customer Credit Overdue Smoke failed: expected family 'aging', observed {family_id!r}."
				)
			if source_reports != ["Accounts Receivable Summary"]:
				raise RuntimeError(
					f"Phase1.4 Customer Credit Overdue Smoke failed: expected Accounts Receivable Summary, observed {source_reports!r}."
				)
			if filter_mode != "overdue_only":
				raise RuntimeError(
					f"Phase1.4 Customer Credit Overdue Smoke failed: expected filter_mode 'overdue_only', observed {filter_mode!r}."
				)
			return {
				"ok": True,
				"mode": str((payload or {}).get("mode") or "").strip(),
				"filter_mode": filter_mode,
				"answer_text": assistant_text,
			}
		finally:
			_delete_committed_smoke_session_doc(
				frappe_module=frappe_module,
				session_doctype=session_doctype,
				doc_name=doc.name,
			)

	return _with_compiled_first_turn_full_rollout(
		frappe_module=frappe_module,
		callback=_run,
	)


def run_customer_credit_balance_smoke(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
	latest_assistant_payload,
) -> Dict[str, Any]:
	def _run() -> Dict[str, Any]:
		doc = _create_committed_smoke_session_doc(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			title="Phase1.4 Customer Credit Balance Smoke",
		)
		try:
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="show customers with credit balance",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.4 Customer Credit Balance Smoke failed on credit-balance request.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			assistant_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			tool_payloads = session_tool_payloads(session_doc)
			artifact_payload = latest_tool_payload_by_type(tool_payloads, "qwen_normalized_family_artifact_contract")
			family_id = str((artifact_payload or {}).get("family_id") or "").strip()
			source_reports = [
				str(item or "").strip()
				for item in ((artifact_payload or {}).get("source_reports") or [])
				if str(item or "").strip()
			]
			filter_mode = str(((artifact_payload or {}).get("dimensions") or {}).get("filter_mode") or "").strip()
			parties = [
				item
				for item in (((artifact_payload or {}).get("sections") or {}).get("parties") or [])
				if isinstance(item, dict)
			]
			party_names = {
				str(item.get("party") or "").strip().lower()
				for item in parties
				if str(item.get("party") or "").strip()
			}
			if family_id != "aging":
				raise RuntimeError(
					f"Phase1.4 Customer Credit Balance Smoke failed: expected family 'aging', observed {family_id!r}."
				)
			if source_reports != ["Accounts Receivable Summary"]:
				raise RuntimeError(
					f"Phase1.4 Customer Credit Balance Smoke failed: expected Accounts Receivable Summary, observed {source_reports!r}."
				)
			if filter_mode != "credit_balance_only":
				raise RuntimeError(
					f"Phase1.4 Customer Credit Balance Smoke failed: expected filter_mode 'credit_balance_only', observed {filter_mode!r}."
				)
			if "thaketa mobile exchange" not in party_names:
				raise RuntimeError(
					"Phase1.4 Customer Credit Balance Smoke failed: expected negative-balance customer was not present."
				)
			return {
				"ok": True,
				"mode": str((payload or {}).get("mode") or "").strip(),
				"filter_mode": filter_mode,
				"party_names": sorted(party_names),
				"answer_text": assistant_text,
			}
		finally:
			_delete_committed_smoke_session_doc(
				frappe_module=frappe_module,
				session_doctype=session_doctype,
				doc_name=doc.name,
			)

	return _with_compiled_first_turn_full_rollout(
		frappe_module=frappe_module,
		callback=_run,
	)


def run_customer_credit_detail_followup_smoke(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	latest_assistant_payload,
) -> Dict[str, Any]:
	def _run() -> Dict[str, Any]:
		doc = _create_committed_smoke_session_doc(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			title="Phase1.4 Customer Credit Detail Followup Smoke",
		)
		try:
			ok, detail_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="tell me more about Zegyo Mobile Supply House",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.4 Customer Credit Detail Followup Smoke failed on customer detail request.")
			if str((detail_payload or {}).get("agent_meta", {}).get("engine") or "").strip() != "entity_detail":
				raise RuntimeError(
					"Phase1.4 Customer Credit Detail Followup Smoke failed: explicit customer request did not use governed entity-detail engine."
				)
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			detail_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			detail_lower = detail_text.lower()
			if "zegyo mobile supply house" not in detail_lower or "credit status" not in detail_lower:
				raise RuntimeError(
					"Phase1.4 Customer Credit Detail Followup Smoke failed: customer detail did not expose the governed credit blocks."
				)

			ok, overdue_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="is this customer overdue?",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.4 Customer Credit Detail Followup Smoke failed on overdue follow-up.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			overdue_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if str((overdue_payload or {}).get("mode") or "").strip() != "grounded_evidence_answer":
				raise RuntimeError(
					"Phase1.4 Customer Credit Detail Followup Smoke failed: overdue follow-up did not use grounded evidence mode."
				)
			if "not overdue" not in overdue_text.lower():
				raise RuntimeError(
					"Phase1.4 Customer Credit Detail Followup Smoke failed: overdue follow-up did not stay anchored to customer credit evidence."
				)

			ok, credit_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="does this customer have a credit balance?",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.4 Customer Credit Detail Followup Smoke failed on credit-balance follow-up.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			credit_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if str((credit_payload or {}).get("mode") or "").strip() != "grounded_evidence_answer":
				raise RuntimeError(
					"Phase1.4 Customer Credit Detail Followup Smoke failed: credit-balance follow-up did not use grounded evidence mode."
				)
			if "does not have a credit balance" not in credit_text.lower():
				raise RuntimeError(
					"Phase1.4 Customer Credit Detail Followup Smoke failed: non-credit-balance follow-up did not stay grounded."
				)

			ok, bucket_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="which aging bucket is highest?",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.4 Customer Credit Detail Followup Smoke failed on aging-bucket follow-up.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			bucket_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if str((bucket_payload or {}).get("mode") or "").strip() != "grounded_evidence_answer":
				raise RuntimeError(
					"Phase1.4 Customer Credit Detail Followup Smoke failed: aging-bucket follow-up did not use grounded evidence mode."
				)
			if "0-30" not in bucket_text:
				raise RuntimeError(
					"Phase1.4 Customer Credit Detail Followup Smoke failed: aging-bucket answer did not expose the governed dominant bucket."
				)

			ok, second_detail_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="tell me more about Thaketa Mobile Exchange",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.4 Customer Credit Detail Followup Smoke failed on second customer detail request.")
			if str((second_detail_payload or {}).get("agent_meta", {}).get("engine") or "").strip() != "entity_detail":
				raise RuntimeError(
					"Phase1.4 Customer Credit Detail Followup Smoke failed: second customer request did not use governed entity-detail engine."
				)
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			second_detail_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if "thaketa mobile exchange" not in second_detail_text.lower():
				raise RuntimeError(
					"Phase1.4 Customer Credit Detail Followup Smoke failed: customer detail did not switch to the requested negative-balance customer."
				)

			ok, second_credit_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="does this customer have a credit balance?",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.4 Customer Credit Detail Followup Smoke failed on positive credit-balance follow-up.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			second_credit_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if str((second_credit_payload or {}).get("mode") or "").strip() != "grounded_evidence_answer":
				raise RuntimeError(
					"Phase1.4 Customer Credit Detail Followup Smoke failed: positive credit-balance follow-up did not use grounded evidence mode."
				)
			if "has a credit balance" not in second_credit_text.lower() or "249,000" not in second_credit_text:
				raise RuntimeError(
					"Phase1.4 Customer Credit Detail Followup Smoke failed: positive credit-balance follow-up did not stay grounded to the negative-balance customer."
				)

			return {
				"ok": True,
				"detail_mode": str((detail_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
				"overdue_mode": str((overdue_payload or {}).get("mode") or "").strip(),
				"credit_mode": str((credit_payload or {}).get("mode") or "").strip(),
				"bucket_mode": str((bucket_payload or {}).get("mode") or "").strip(),
				"second_detail_mode": str((second_detail_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
				"second_credit_mode": str((second_credit_payload or {}).get("mode") or "").strip(),
				"detail_text": detail_text,
				"overdue_text": overdue_text,
				"credit_text": credit_text,
				"bucket_text": bucket_text,
				"second_detail_text": second_detail_text,
				"second_credit_text": second_credit_text,
			}
		finally:
			_delete_committed_smoke_session_doc(
				frappe_module=frappe_module,
				session_doctype=session_doctype,
				doc_name=doc.name,
			)

	return _with_compiled_first_turn_full_rollout(
		frappe_module=frappe_module,
		callback=_run,
	)


def run_customer_credit_policy_followup_smoke(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	latest_assistant_payload,
) -> Dict[str, Any]:
	def _run() -> Dict[str, Any]:
		doc = _create_committed_smoke_session_doc(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			title="Phase1.4 Customer Credit Policy Followup Smoke",
		)
		try:
			ok, detail_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="tell me more about Zegyo Mobile Supply House",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.4 Customer Credit Policy Followup Smoke failed on customer detail request.")
			if str((detail_payload or {}).get("agent_meta", {}).get("engine") or "").strip() != "entity_detail":
				raise RuntimeError(
					"Phase1.4 Customer Credit Policy Followup Smoke failed: explicit customer request did not use governed entity-detail engine."
				)
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			detail_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			detail_lower = detail_text.lower()
			if "commercial policy" not in detail_lower or "10,000,000" not in detail_text:
				raise RuntimeError(
					"Phase1.4 Customer Credit Policy Followup Smoke failed: customer detail did not expose the configured policy block."
				)
			if "15 Days - MMOB" not in detail_text or "Wholesale Selling - MMOB" not in detail_text:
				raise RuntimeError(
					"Phase1.4 Customer Credit Policy Followup Smoke failed: customer detail did not expose live payment terms and default price list."
				)

			ok, status_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="has this customer exceeded credit limit?",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.4 Customer Credit Policy Followup Smoke failed on credit-limit-status follow-up.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			status_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if str((status_payload or {}).get("mode") or "").strip() != "grounded_evidence_answer":
				raise RuntimeError(
					"Phase1.4 Customer Credit Policy Followup Smoke failed: credit-limit-status follow-up did not use grounded evidence mode."
				)
			if "within the configured credit limit" not in status_text.lower() or "10,000,000" not in status_text:
				raise RuntimeError(
					"Phase1.4 Customer Credit Policy Followup Smoke failed: credit-limit-status answer did not stay anchored to configured policy evidence."
				)

			ok, limit_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="what is this customer's credit limit?",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.4 Customer Credit Policy Followup Smoke failed on credit-limit follow-up.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			limit_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if str((limit_payload or {}).get("mode") or "").strip() != "grounded_evidence_answer":
				raise RuntimeError(
					"Phase1.4 Customer Credit Policy Followup Smoke failed: credit-limit follow-up did not use grounded evidence mode."
				)
			if "10,000,000" not in limit_text:
				raise RuntimeError(
					"Phase1.4 Customer Credit Policy Followup Smoke failed: credit-limit answer did not surface the governed configured limit."
				)

			ok, payment_terms_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="what are this customer's payment terms?",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.4 Customer Credit Policy Followup Smoke failed on payment-terms follow-up.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			payment_terms_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if str((payment_terms_payload or {}).get("mode") or "").strip() != "grounded_evidence_answer":
				raise RuntimeError(
					"Phase1.4 Customer Credit Policy Followup Smoke failed: payment-terms follow-up did not use grounded evidence mode."
				)
			if "15 Days - MMOB" not in payment_terms_text:
				raise RuntimeError(
					"Phase1.4 Customer Credit Policy Followup Smoke failed: payment-terms answer did not expose the governed customer policy."
				)

			ok, price_list_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="what is this customer's default price list?",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.4 Customer Credit Policy Followup Smoke failed on default-price-list follow-up.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			price_list_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if str((price_list_payload or {}).get("mode") or "").strip() != "grounded_evidence_answer":
				raise RuntimeError(
					"Phase1.4 Customer Credit Policy Followup Smoke failed: default-price-list follow-up did not use grounded evidence mode."
				)
			if "Wholesale Selling - MMOB" not in price_list_text:
				raise RuntimeError(
					"Phase1.4 Customer Credit Policy Followup Smoke failed: default-price-list answer did not expose the governed customer policy."
				)

			return {
				"ok": True,
				"detail_mode": str((detail_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
				"status_mode": str((status_payload or {}).get("mode") or "").strip(),
				"limit_mode": str((limit_payload or {}).get("mode") or "").strip(),
				"payment_terms_mode": str((payment_terms_payload or {}).get("mode") or "").strip(),
				"price_list_mode": str((price_list_payload or {}).get("mode") or "").strip(),
				"detail_text": detail_text,
				"status_text": status_text,
				"limit_text": limit_text,
				"payment_terms_text": payment_terms_text,
				"price_list_text": price_list_text,
			}
		finally:
			_delete_committed_smoke_session_doc(
				frappe_module=frappe_module,
				session_doctype=session_doctype,
				doc_name=doc.name,
			)

	return _with_compiled_first_turn_full_rollout(
		frappe_module=frappe_module,
		callback=_run,
	)


def run_governed_kpi_frontdoor_smoke(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	latest_assistant_payload,
) -> Dict[str, Any]:
	def _run() -> Dict[str, Any]:
		def _visible_message_text(content: Any) -> str:
			text = str(content or "").strip()
			if not text:
				return ""
			try:
				payload = json.loads(text)
			except Exception:
				return text
			if isinstance(payload, dict):
				payload_text = str(payload.get("text") or "").strip()
				if payload_text:
					return payload_text
			return text

		def _visible_messages(session_doc) -> List[Dict[str, Any]]:
			return [
				{
					"role": str(row.role or "").strip().lower(),
					"content": _visible_message_text(row.content),
				}
				for row in (session_doc.get("messages") or [])
				if str(row.role or "").strip().lower() in {"user", "assistant"}
			]

		doc = _create_committed_smoke_session_doc(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			title="Phase2.4 Governed KPI Frontdoor Smoke",
		)
		try:
			ok, active_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="what is customer credit utilization and why does it matter",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase2.4 Governed KPI Frontdoor Smoke failed on active KPI definition request.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			active_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			active_visible_messages = _visible_messages(session_doc)
			if str((active_payload or {}).get("mode") or "").strip() != "front_door":
				raise RuntimeError("Phase2.4 Governed KPI Frontdoor Smoke failed: active KPI request did not stay in front door.")
			if str((active_payload or {}).get("agent_meta", {}).get("intent_class") or "").strip() != "governed_kpi_definition":
				raise RuntimeError(
					"Phase2.4 Governed KPI Frontdoor Smoke failed: active KPI request did not use governed_kpi_definition intent."
				)
			if "configured customer credit limit" not in active_text.lower() or "it matters because" not in active_text.lower():
				raise RuntimeError(
					"Phase2.4 Governed KPI Frontdoor Smoke failed: active KPI answer did not expose the governed formula basis and business purpose."
				)
			if len(active_visible_messages) != 2:
				raise RuntimeError(
					f"Phase2.4 Governed KPI Frontdoor Smoke failed: expected exactly 2 visible messages after first KPI turn, observed {len(active_visible_messages)}."
				)

			ok, ambiguous_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="what does average order value mean in this ERP",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase2.4 Governed KPI Frontdoor Smoke failed on ambiguous KPI definition request.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			ambiguous_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if str((ambiguous_payload or {}).get("mode") or "").strip() != "front_door":
				raise RuntimeError("Phase2.4 Governed KPI Frontdoor Smoke failed: ambiguous KPI request did not stay in front door.")
			if "Average Order Value by Sales Order" not in ambiguous_text or "Average Order Value by Sales Invoice" not in ambiguous_text:
				raise RuntimeError(
					"Phase2.4 Governed KPI Frontdoor Smoke failed: ambiguous KPI answer did not ask for governed basis clarification."
				)
			ambiguous_visible_messages = _visible_messages(session_doc)
			if len(ambiguous_visible_messages) != 4:
				raise RuntimeError(
					f"Phase2.4 Governed KPI Frontdoor Smoke failed: expected exactly 4 visible messages after second KPI turn, observed {len(ambiguous_visible_messages)}."
				)
			if ambiguous_visible_messages[-1].get("role") != "assistant":
				raise RuntimeError(
					"Phase2.4 Governed KPI Frontdoor Smoke failed: last visible message after ambiguous KPI turn was not assistant-owned."
				)
			if str(ambiguous_visible_messages[-1].get("content") or "").strip() != ambiguous_text:
				raise RuntimeError(
					"Phase2.4 Governed KPI Frontdoor Smoke failed: latest assistant payload and last visible assistant message diverged."
				)
			lower_ambiguous_text = ambiguous_text.lower()
			if "one sales order was processed" in lower_ambiguous_text or "document count" in lower_ambiguous_text:
				raise RuntimeError(
					"Phase2.4 Governed KPI Frontdoor Smoke failed: ambiguous KPI clarification leaked transaction-listing narrative text."
				)

			ok, clarified_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="Sales Order",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase2.4 Governed KPI Frontdoor Smoke failed on governed KPI clarification follow-up.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			clarified_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if str((clarified_payload or {}).get("mode") or "").strip() != "front_door":
				raise RuntimeError(
					"Phase2.4 Governed KPI Frontdoor Smoke failed: clarified KPI follow-up did not re-enter the front-door lane."
				)
			if "Average Order Value by Sales Order" not in clarified_text or "Formula basis" not in clarified_text:
				raise RuntimeError(
					"Phase2.4 Governed KPI Frontdoor Smoke failed: clarified KPI follow-up did not return the governed sales-order AOV definition."
				)
			lower_clarified_text = clarified_text.lower()
			if "one sales order was processed" in lower_clarified_text or "document count" in lower_clarified_text:
				raise RuntimeError(
					"Phase2.4 Governed KPI Frontdoor Smoke failed: clarified KPI follow-up leaked sales-order listing narrative text."
				)
			clarified_visible_messages = _visible_messages(session_doc)
			if len(clarified_visible_messages) != 6:
				raise RuntimeError(
					f"Phase2.4 Governed KPI Frontdoor Smoke failed: expected exactly 6 visible messages after clarification resolution, observed {len(clarified_visible_messages)}."
				)

			ok, blocked_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="what is collection ratio",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase2.4 Governed KPI Frontdoor Smoke failed on blocked KPI definition request.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			blocked_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if str((blocked_payload or {}).get("mode") or "").strip() != "front_door":
				raise RuntimeError("Phase2.4 Governed KPI Frontdoor Smoke failed: blocked KPI request did not stay in front door.")
			if "not runtime-active yet" not in blocked_text.lower() or "collected-amount" not in blocked_text.lower():
				raise RuntimeError(
					"Phase2.4 Governed KPI Frontdoor Smoke failed: blocked KPI answer did not stay blocked-safe."
				)

			ok, undefined_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="define gross margin",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase2.4 Governed KPI Frontdoor Smoke failed on undefined KPI definition request.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			undefined_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if str((undefined_payload or {}).get("mode") or "").strip() != "front_door":
				raise RuntimeError("Phase2.4 Governed KPI Frontdoor Smoke failed: undefined KPI request did not stay in front door.")
			if "no governed kpi definition is currently registered" not in undefined_text.lower():
				raise RuntimeError(
					"Phase2.4 Governed KPI Frontdoor Smoke failed: undefined KPI answer did not explain the governed registry boundary."
				)

			return {
				"ok": True,
				"active_mode": str((active_payload or {}).get("mode") or "").strip(),
				"ambiguous_mode": str((ambiguous_payload or {}).get("mode") or "").strip(),
				"clarified_mode": str((clarified_payload or {}).get("mode") or "").strip(),
				"blocked_mode": str((blocked_payload or {}).get("mode") or "").strip(),
				"undefined_mode": str((undefined_payload or {}).get("mode") or "").strip(),
				"active_text": active_text,
				"ambiguous_text": ambiguous_text,
				"clarified_text": clarified_text,
				"blocked_text": blocked_text,
				"undefined_text": undefined_text,
			}
		finally:
			_delete_committed_smoke_session_doc(
				frappe_module=frappe_module,
				session_doctype=session_doctype,
				doc_name=doc.name,
			)

	return _with_compiled_first_turn_full_rollout(
		frappe_module=frappe_module,
		callback=_run,
	)


def run_customer_credit_balance_probe(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
	latest_assistant_payload,
) -> Dict[str, Any]:
	def _run() -> Dict[str, Any]:
		doc = _create_committed_smoke_session_doc(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			title="Phase1.4 Customer Credit Balance Probe",
		)
		try:
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="show customers with credit balance",
				user="Administrator",
			)
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			tool_payloads = session_tool_payloads(session_doc)
			compiler_payload = latest_tool_payload_by_type(tool_payloads, "qwen_fresh_query_compiler_contract")
			semantic_payload = latest_tool_payload_by_type(tool_payloads, "qwen_semantic_fresh_query_interpretation")
			interpretation_payload = (
				(semantic_payload or {}).get("interpretation")
				if isinstance((semantic_payload or {}).get("interpretation"), dict)
				else {}
			)
			artifact_payload = latest_tool_payload_by_type(tool_payloads, "qwen_normalized_family_artifact_contract")
			compiler_details = (
				compiler_payload.get("governed_resolution_details")
				if isinstance(compiler_payload, dict)
				else {}
			)
			return {
				"ok": bool(ok),
				"mode": str((payload or {}).get("mode") or "").strip(),
				"semantic_status": str((semantic_payload or {}).get("status") or "").strip(),
				"candidate_capability_ids": list((interpretation_payload or {}).get("candidate_capability_ids") or []),
				"requested_metrics": list((interpretation_payload or {}).get("requested_metrics") or []),
				"compiler_requested_metrics": list((compiler_payload or {}).get("requested_metrics") or []),
				"compiler_requested_metric_keys": list((compiler_details or {}).get("requested_metric_keys") or []),
				"filter_mode": str(((artifact_payload or {}).get("dimensions") or {}).get("filter_mode") or "").strip(),
				"answer_text": str(latest_assistant_payload(session_doc).get("text") or "").strip(),
			}
		finally:
			_delete_committed_smoke_session_doc(
				frappe_module=frappe_module,
				session_doctype=session_doctype,
				doc_name=doc.name,
			)

	return _with_compiled_first_turn_full_rollout(
		frappe_module=frappe_module,
		callback=_run,
	)


def run_customer_credit_overdue_probe(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
	latest_assistant_payload,
) -> Dict[str, Any]:
	def _run() -> Dict[str, Any]:
		doc = _create_committed_smoke_session_doc(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			title="Phase1.4 Customer Credit Overdue Probe",
		)
		try:
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="show overdue customers",
				user="Administrator",
			)
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			tool_payloads = session_tool_payloads(session_doc)
			compiler_payload = latest_tool_payload_by_type(tool_payloads, "qwen_fresh_query_compiler_contract")
			semantic_payload = latest_tool_payload_by_type(tool_payloads, "qwen_semantic_fresh_query_interpretation")
			interpretation_payload = (
				(semantic_payload or {}).get("interpretation")
				if isinstance((semantic_payload or {}).get("interpretation"), dict)
				else {}
			)
			artifact_payload = latest_tool_payload_by_type(tool_payloads, "qwen_normalized_family_artifact_contract")
			compiler_details = (
				compiler_payload.get("governed_resolution_details")
				if isinstance(compiler_payload, dict)
				else {}
			)
			return {
				"ok": bool(ok),
				"mode": str((payload or {}).get("mode") or "").strip(),
				"semantic_status": str((semantic_payload or {}).get("status") or "").strip(),
				"candidate_capability_ids": list((interpretation_payload or {}).get("candidate_capability_ids") or []),
				"requested_metrics": list((interpretation_payload or {}).get("requested_metrics") or []),
				"compiler_requested_metrics": list((compiler_payload or {}).get("requested_metrics") or []),
				"compiler_requested_metric_keys": list((compiler_details or {}).get("requested_metric_keys") or []),
				"filter_mode": str(((artifact_payload or {}).get("dimensions") or {}).get("filter_mode") or "").strip(),
				"answer_text": str(latest_assistant_payload(session_doc).get("text") or "").strip(),
			}
		finally:
			_delete_committed_smoke_session_doc(
				frappe_module=frappe_module,
				session_doctype=session_doctype,
				doc_name=doc.name,
			)

	return _with_compiled_first_turn_full_rollout(
		frappe_module=frappe_module,
		callback=_run,
	)


def run_purchase_order_status_scope_reset_smoke(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
	latest_assistant_payload,
) -> Dict[str, Any]:
	def _run() -> Dict[str, Any]:
		doc = _create_committed_smoke_session_doc(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			title="Phase1.3 Purchase Order Status Scope Reset Smoke",
		)
		try:
			ok, first_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="show me submitted purchase orders from last month",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.3 Purchase Order Status Scope Reset Smoke failed on last-month listing request.")
			ok, second_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="show me purchase orders with status To Bill",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.3 Purchase Order Status Scope Reset Smoke failed on status listing request.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			assistant_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			assistant_lower = assistant_text.lower()
			if "march 2026" in assistant_lower or "2026-03-01 to 2026-03-31" in assistant_lower:
				raise RuntimeError(
					"Phase1.3 Purchase Order Status Scope Reset Smoke failed: status re-ask still inherited the prior March date window."
				)
			if "pur-ord-2026-00008" not in assistant_lower and "2026-01-30" not in assistant_lower:
				raise RuntimeError(
					"Phase1.3 Purchase Order Status Scope Reset Smoke failed: status re-ask did not break out to the January Purchase Order result set."
				)
			if "pur-ord-2026-00004" in assistant_lower or "pur-ord-2026-00002" in assistant_lower:
				raise RuntimeError(
					"Phase1.3 Purchase Order Status Scope Reset Smoke failed: status re-ask still included non-'To Bill' purchase orders."
				)
			tool_payloads = session_tool_payloads(session_doc)
			scope_payload = latest_tool_payload_by_type(tool_payloads, "qwen_governed_scope_decision_contract")
			followup_payload = latest_tool_payload_by_type(tool_payloads, "qwen_followup_resolution")
			scope_status = str((scope_payload or {}).get("governed_scope_status") or "").strip()
			followup_mode = str((followup_payload or {}).get("mode") or "").strip()
			if scope_status != "fresh_query_breakout":
				raise RuntimeError(
					f"Phase1.3 Purchase Order Status Scope Reset Smoke failed: expected governed scope status 'fresh_query_breakout', observed {scope_status!r}."
				)
			if followup_mode != "new_query":
				raise RuntimeError(
					f"Phase1.3 Purchase Order Status Scope Reset Smoke failed: expected follow-up mode 'new_query', observed {followup_mode!r}."
				)
			return {
				"ok": True,
				"initial_mode": str((first_payload or {}).get("mode") or "").strip(),
				"followup_mode": followup_mode,
				"governed_scope_status": scope_status,
				"answer_text": assistant_text,
			}
		finally:
			_delete_committed_smoke_session_doc(
				frappe_module=frappe_module,
				session_doctype=session_doctype,
				doc_name=doc.name,
			)

	return _with_compiled_first_turn_full_rollout(
		frappe_module=frappe_module,
		callback=_run,
	)


def run_delivery_note_listing_limit_probe(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
) -> Dict[str, Any]:
	return _run_document_listing_smoke(
		frappe_module=frappe_module,
		session_doctype=session_doctype,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=session_tool_payloads,
		latest_tool_payload_by_type=latest_tool_payload_by_type,
		smoke_title="Phase1.1 Delivery Note Listing Limit Probe",
		request_message="show me the last 5 delivery notes",
		expected_row_count=5,
		minimum_row_count=0,
		required_title_fragment="Delivery Note",
		required_column_groups=[["Delivery", "Note"], ["Customer"], ["Qty", "Quantity"]],
	)


def run_delivery_note_detail_smoke(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
	latest_assistant_payload,
) -> Dict[str, Any]:
	def _run() -> Dict[str, Any]:
		doc = _create_committed_smoke_session_doc(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			title="Phase1.1 Delivery Note Detail Smoke",
		)
		try:
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="give me latest 5 delivery note",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.1 Delivery Note Detail Smoke failed on delivery-note listing request.")
			ok, detail_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="tell me more about MAT-DN-2026-00016",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.1 Delivery Note Detail Smoke failed on delivery-note detail request.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			assistant_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if "mat-dn-2026-00016" not in assistant_text.lower():
				raise RuntimeError(
					"Phase1.1 Delivery Note Detail Smoke failed: detail answer did not switch to the requested delivery note."
				)
			if str((detail_payload or {}).get("agent_meta", {}).get("engine") or "").strip() != "entity_detail":
				raise RuntimeError(
					"Phase1.1 Delivery Note Detail Smoke failed: detail request did not use the governed entity-detail engine."
				)
			tool_payloads = session_tool_payloads(session_doc)
			artifact_payload = latest_tool_payload_by_type(tool_payloads, "qwen_entity_detail_artifact")
			rendered_payload = latest_tool_payload_by_type(tool_payloads, "qwen_entity_detail_rendered_response")
			entity_type = str((artifact_payload or {}).get("dimensions", {}).get("entity_type") or "").strip()
			rendered_title = str((rendered_payload or {}).get("title") or "").strip()
			if entity_type != "delivery_note":
				raise RuntimeError(
					f"Phase1.1 Delivery Note Detail Smoke failed: expected entity_type 'delivery_note', observed {entity_type!r}."
				)
			if "Delivery Note" not in rendered_title:
				raise RuntimeError(
					f"Phase1.1 Delivery Note Detail Smoke failed: expected rendered title to contain 'Delivery Note', observed {rendered_title!r}."
				)
			return {
				"ok": True,
				"mode": str((detail_payload or {}).get("mode") or "").strip(),
				"engine": str((detail_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
				"title": rendered_title,
				"entity_type": entity_type,
				"answer_text": assistant_text,
			}
		finally:
			_delete_committed_smoke_session_doc(
				frappe_module=frappe_module,
				session_doctype=session_doctype,
				doc_name=doc.name,
			)

	return _with_compiled_first_turn_full_rollout(
		frappe_module=frappe_module,
		callback=_run,
	)


def run_sales_order_detail_smoke(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
	latest_assistant_payload,
) -> Dict[str, Any]:
	def _run() -> Dict[str, Any]:
		doc = _create_committed_smoke_session_doc(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			title="Phase1.2 Sales Order Detail Smoke",
		)
		try:
			ok, detail_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="tell me more about SAL-ORD-2026-00022",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.2 Sales Order Detail Smoke failed on sales-order detail request.")
			if str((detail_payload or {}).get("agent_meta", {}).get("engine") or "").strip() != "entity_detail":
				raise RuntimeError(
					"Phase1.2 Sales Order Detail Smoke failed: explicit sales-order request did not use the governed entity-detail engine."
				)
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			assistant_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if "sal-ord-2026-00022" not in assistant_text.lower():
				raise RuntimeError(
					"Phase1.2 Sales Order Detail Smoke failed: detail answer did not anchor to the requested sales order."
				)
			if "document count" in assistant_text.lower():
				raise RuntimeError(
					"Phase1.2 Sales Order Detail Smoke failed: detail answer still looked like a list summary."
				)
			tool_payloads = session_tool_payloads(session_doc)
			artifact_payload = latest_tool_payload_by_type(tool_payloads, "qwen_entity_detail_artifact")
			rendered_payload = latest_tool_payload_by_type(tool_payloads, "qwen_entity_detail_rendered_response")
			entity_type = str((artifact_payload or {}).get("dimensions", {}).get("entity_type") or "").strip()
			rendered_title = str((rendered_payload or {}).get("title") or "").strip()
			if entity_type != "sales_order":
				raise RuntimeError(
					f"Phase1.2 Sales Order Detail Smoke failed: expected entity_type 'sales_order', observed {entity_type!r}."
				)
			if "Sales Order" not in rendered_title:
				raise RuntimeError(
					f"Phase1.2 Sales Order Detail Smoke failed: expected rendered title to contain 'Sales Order', observed {rendered_title!r}."
				)
			return {
				"ok": True,
				"mode": str((detail_payload or {}).get("mode") or "").strip(),
				"engine": str((detail_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
				"title": rendered_title,
				"entity_type": entity_type,
				"answer_text": assistant_text,
			}
		finally:
			_delete_committed_smoke_session_doc(
				frappe_module=frappe_module,
				session_doctype=session_doctype,
				doc_name=doc.name,
			)

	return _with_compiled_first_turn_full_rollout(
		frappe_module=frappe_module,
		callback=_run,
	)


def run_purchase_order_detail_smoke(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
	latest_assistant_payload,
) -> Dict[str, Any]:
	def _run() -> Dict[str, Any]:
		doc = _create_committed_smoke_session_doc(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			title="Phase1.3 Purchase Order Detail Smoke",
		)
		try:
			ok, detail_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="tell me more about PUR-ORD-2026-00008",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.3 Purchase Order Detail Smoke failed on purchase-order detail request.")
			if str((detail_payload or {}).get("agent_meta", {}).get("engine") or "").strip() != "entity_detail":
				raise RuntimeError(
					"Phase1.3 Purchase Order Detail Smoke failed: explicit purchase-order request did not use the governed entity-detail engine."
				)
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			assistant_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if "pur-ord-2026-00008" not in assistant_text.lower():
				raise RuntimeError(
					"Phase1.3 Purchase Order Detail Smoke failed: detail answer did not anchor to the requested purchase order."
				)
			if "document count" in assistant_text.lower():
				raise RuntimeError(
					"Phase1.3 Purchase Order Detail Smoke failed: detail answer still looked like a list summary."
				)
			tool_payloads = session_tool_payloads(session_doc)
			artifact_payload = latest_tool_payload_by_type(tool_payloads, "qwen_entity_detail_artifact")
			rendered_payload = latest_tool_payload_by_type(tool_payloads, "qwen_entity_detail_rendered_response")
			entity_type = str((artifact_payload or {}).get("dimensions", {}).get("entity_type") or "").strip()
			rendered_title = str((rendered_payload or {}).get("title") or "").strip()
			if entity_type != "purchase_order":
				raise RuntimeError(
					f"Phase1.3 Purchase Order Detail Smoke failed: expected entity_type 'purchase_order', observed {entity_type!r}."
				)
			if "Purchase Order" not in rendered_title:
				raise RuntimeError(
					f"Phase1.3 Purchase Order Detail Smoke failed: expected rendered title to contain 'Purchase Order', observed {rendered_title!r}."
				)
			return {
				"ok": True,
				"mode": str((detail_payload or {}).get("mode") or "").strip(),
				"engine": str((detail_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
				"title": rendered_title,
				"entity_type": entity_type,
				"answer_text": assistant_text,
			}
		finally:
			_delete_committed_smoke_session_doc(
				frappe_module=frappe_module,
				session_doctype=session_doctype,
				doc_name=doc.name,
			)

	return _with_compiled_first_turn_full_rollout(
		frappe_module=frappe_module,
		callback=_run,
	)


def run_purchase_order_status_followup_smoke(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	latest_assistant_payload,
) -> Dict[str, Any]:
	def _run() -> Dict[str, Any]:
		doc = _create_committed_smoke_session_doc(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			title="Phase1.3 Purchase Order Status Followup Smoke",
		)
		try:
			ok, detail_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="tell me more about PUR-ORD-2026-00004",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.3 Purchase Order Status Followup Smoke failed on purchase-order detail request.")
			if str((detail_payload or {}).get("agent_meta", {}).get("engine") or "").strip() != "entity_detail":
				raise RuntimeError(
					"Phase1.3 Purchase Order Status Followup Smoke failed: explicit purchase-order request did not use governed entity-detail engine."
				)

			ok, received_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="is it received?",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.3 Purchase Order Status Followup Smoke failed on receipt-status follow-up.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			received_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if str((received_payload or {}).get("mode") or "").strip() != "grounded_evidence_answer":
				raise RuntimeError(
					"Phase1.3 Purchase Order Status Followup Smoke failed: receipt-status follow-up did not use grounded evidence mode."
				)
			if "79.96%" not in received_text or "pur-ord-2026-00004" not in received_text.lower():
				raise RuntimeError(
					"Phase1.3 Purchase Order Status Followup Smoke failed: receipt-status answer did not stay anchored to order evidence."
				)

			ok, billed_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="how much is billed?",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.3 Purchase Order Status Followup Smoke failed on billing follow-up.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			billed_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if str((billed_payload or {}).get("mode") or "").strip() != "grounded_evidence_answer":
				raise RuntimeError(
					"Phase1.3 Purchase Order Status Followup Smoke failed: billing follow-up did not use grounded evidence mode."
				)
			if "0%" not in billed_text or "not been billed yet" not in billed_text.lower():
				raise RuntimeError(
					"Phase1.3 Purchase Order Status Followup Smoke failed: billing answer did not surface the governed order progress."
				)

			ok, due_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="when is receipt due?",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.3 Purchase Order Status Followup Smoke failed on planned-date follow-up.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			due_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if str((due_payload or {}).get("mode") or "").strip() != "grounded_evidence_answer":
				raise RuntimeError(
					"Phase1.3 Purchase Order Status Followup Smoke failed: planned-date follow-up did not use grounded evidence mode."
				)
			if "2026-01-20" not in due_text:
				raise RuntimeError(
					"Phase1.3 Purchase Order Status Followup Smoke failed: planned-date answer did not expose the governed receipt date."
				)

			ok, boundary_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="when was it received?",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.3 Purchase Order Status Followup Smoke failed on actual-receipt-date boundary follow-up.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			boundary_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if str((boundary_payload or {}).get("mode") or "").strip() != "grounded_evidence_boundary":
				raise RuntimeError(
					"Phase1.3 Purchase Order Status Followup Smoke failed: actual-receipt-date follow-up did not stop at the grounded boundary."
				)
			if "actual receipt event date" not in boundary_text.lower():
				raise RuntimeError(
					"Phase1.3 Purchase Order Status Followup Smoke failed: boundary answer did not explain the missing downstream evidence."
				)

			return {
				"ok": True,
				"detail_mode": str((detail_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
				"receipt_mode": str((received_payload or {}).get("mode") or "").strip(),
				"billing_mode": str((billed_payload or {}).get("mode") or "").strip(),
				"due_mode": str((due_payload or {}).get("mode") or "").strip(),
				"boundary_mode": str((boundary_payload or {}).get("mode") or "").strip(),
				"receipt_text": received_text,
				"billing_text": billed_text,
				"due_text": due_text,
				"boundary_text": boundary_text,
			}
		finally:
			_delete_committed_smoke_session_doc(
				frappe_module=frappe_module,
				session_doctype=session_doctype,
				doc_name=doc.name,
			)

	return _with_compiled_first_turn_full_rollout(
		frappe_module=frappe_module,
		callback=_run,
	)


def run_sales_order_status_followup_smoke(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	latest_assistant_payload,
) -> Dict[str, Any]:
	def _run() -> Dict[str, Any]:
		doc = _create_committed_smoke_session_doc(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			title="Phase1.2 Sales Order Status Followup Smoke",
		)
		try:
			ok, detail_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="tell me more about SAL-ORD-2026-00022",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.2 Sales Order Status Followup Smoke failed on sales-order detail request.")
			if str((detail_payload or {}).get("agent_meta", {}).get("engine") or "").strip() != "entity_detail":
				raise RuntimeError(
					"Phase1.2 Sales Order Status Followup Smoke failed: explicit sales-order request did not use governed entity-detail engine."
				)

			ok, delivered_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="is it delivered?",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.2 Sales Order Status Followup Smoke failed on delivery-status follow-up.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			delivered_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if str((delivered_payload or {}).get("mode") or "").strip() != "grounded_evidence_answer":
				raise RuntimeError(
					"Phase1.2 Sales Order Status Followup Smoke failed: delivery-status follow-up did not use grounded evidence mode."
				)
			if "50%" not in delivered_text or "sal-ord-2026-00022" not in delivered_text.lower():
				raise RuntimeError(
					"Phase1.2 Sales Order Status Followup Smoke failed: delivery-status answer did not stay anchored to order evidence."
				)

			ok, billed_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="how much is billed?",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.2 Sales Order Status Followup Smoke failed on billing follow-up.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			billed_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if str((billed_payload or {}).get("mode") or "").strip() != "grounded_evidence_answer":
				raise RuntimeError(
					"Phase1.2 Sales Order Status Followup Smoke failed: billing follow-up did not use grounded evidence mode."
				)
			if "10.46%" not in billed_text and "795,000" not in billed_text:
				raise RuntimeError(
					"Phase1.2 Sales Order Status Followup Smoke failed: billing answer did not surface the grounded order progress."
				)

			ok, due_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="when is delivery due?",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.2 Sales Order Status Followup Smoke failed on planned-date follow-up.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			due_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if str((due_payload or {}).get("mode") or "").strip() != "grounded_evidence_answer":
				raise RuntimeError(
					"Phase1.2 Sales Order Status Followup Smoke failed: planned-date follow-up did not use grounded evidence mode."
				)
			if "2026-04-02" not in due_text:
				raise RuntimeError(
					"Phase1.2 Sales Order Status Followup Smoke failed: planned-date answer did not expose the governed delivery date."
				)

			ok, boundary_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="when was it delivered?",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.2 Sales Order Status Followup Smoke failed on actual-delivery-date boundary follow-up.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			boundary_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if str((boundary_payload or {}).get("mode") or "").strip() != "grounded_evidence_boundary":
				raise RuntimeError(
					"Phase1.2 Sales Order Status Followup Smoke failed: actual-delivery-date follow-up did not stop at the grounded boundary."
				)
			if "actual shipment event date" not in boundary_text.lower():
				raise RuntimeError(
					"Phase1.2 Sales Order Status Followup Smoke failed: boundary answer did not explain the missing downstream evidence."
				)

			return {
				"ok": True,
				"detail_mode": str((detail_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
				"delivery_mode": str((delivered_payload or {}).get("mode") or "").strip(),
				"billing_mode": str((billed_payload or {}).get("mode") or "").strip(),
				"due_mode": str((due_payload or {}).get("mode") or "").strip(),
				"boundary_mode": str((boundary_payload or {}).get("mode") or "").strip(),
				"delivery_text": delivered_text,
				"billing_text": billed_text,
				"due_text": due_text,
				"boundary_text": boundary_text,
			}
		finally:
			_delete_committed_smoke_session_doc(
				frappe_module=frappe_module,
				session_doctype=session_doctype,
				doc_name=doc.name,
			)

	return _with_compiled_first_turn_full_rollout(
		frappe_module=frappe_module,
		callback=_run,
	)


def run_delivery_note_date_scope_probe(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
) -> Dict[str, Any]:
	expected_start_date, expected_end_date = _last_month_window()
	return _run_document_listing_date_scope_probe(
		frappe_module=frappe_module,
		session_doctype=session_doctype,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=session_tool_payloads,
		latest_tool_payload_by_type=latest_tool_payload_by_type,
		smoke_title="Phase1.1 Delivery Note Date Scope Probe",
		request_message="show me delivery notes last month",
		required_title_fragment="Delivery Note",
		required_column_groups=[["Delivery", "Note"], ["Posting Date"]],
		date_column_fragments=["Posting Date"],
		expected_start_date=expected_start_date,
		expected_end_date=expected_end_date,
		minimum_row_count=1,
	)


def run_delivery_note_status_probe(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
) -> Dict[str, Any]:
	return _run_document_listing_status_probe(
		frappe_module=frappe_module,
		session_doctype=session_doctype,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=session_tool_payloads,
		latest_tool_payload_by_type=latest_tool_payload_by_type,
		smoke_title="Phase1.1 Delivery Note Status Probe",
		required_title_fragment="Delivery Note",
		required_column_groups=[["Delivery", "Note"], ["Status"]],
		status_column_fragments=["Status"],
		minimum_row_count=1,
	)


def run_delivery_note_session_reset_smoke(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
) -> Dict[str, Any]:
	def _run() -> Dict[str, Any]:
		doc = _create_committed_smoke_session_doc(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			title="Phase1.1 Delivery Note Session Reset Smoke",
		)
		try:
			steps = [
				("show me the last 5 delivery notes", "transaction_listing", "Delivery Note"),
				("show me the last 5 delivery notes from last month", "transaction_listing", "Delivery Note"),
				("show me delivery notes with status Completed", "transaction_listing", "Completed"),
				("Show me last 7 sale invoices", "transaction_listing", "Sales Invoice"),
				(
					smoke_fixture_replacement_message("fresh_query_override_to_ar"),
					"aging",
					"receivable",
				),
			]
			results: List[Dict[str, Any]] = []
			previous_rendered_answer_text = ""
			for message, expected_family_id, required_text in steps:
				ok, payload = handle_qwen_user_message(
					session_name=doc.name,
					message=message,
					user="Administrator",
				)
				if not ok:
					raise RuntimeError(
						f"Phase1.1 Delivery Note Session Reset Smoke failed: request {message!r} did not complete."
					)
				request_id = str((payload or {}).get("request_id") or "").strip()
				turn_state = _stabilize_turn_family_visibility(
					frappe_module=frappe_module,
					session_doctype=session_doctype,
					session_name=doc.name,
					expected_request_id=request_id,
					prior_rendered_answer_text=previous_rendered_answer_text,
					session_tool_payloads=session_tool_payloads,
					latest_tool_payload_by_type=latest_tool_payload_by_type,
				)
				rendered = dict(turn_state.get("rendered") or {})
				artifact = dict(turn_state.get("artifact") or {})
				assistant_text = str(rendered.get("answer_text") or "").strip()
				mode = str((payload or {}).get("mode") or "").strip()
				family_validation_status = str((payload or {}).get("family_validation_status") or "").strip()
				artifact_family_id = str((artifact or {}).get("family_id") or "").strip()
				if mode != "compiled_first_turn":
					raise RuntimeError(
						f"Phase1.1 Delivery Note Session Reset Smoke failed: request {message!r} used mode {mode!r}."
					)
				if family_validation_status != "pass":
					raise RuntimeError(
						f"Phase1.1 Delivery Note Session Reset Smoke failed: request {message!r} had family_validation_status "
						f"{family_validation_status!r}."
					)
				if artifact_family_id != expected_family_id:
					raise RuntimeError(
						f"Phase1.1 Delivery Note Session Reset Smoke failed: request {message!r} expected family "
						f"{expected_family_id!r}, observed {artifact_family_id!r}."
					)
				if required_text and required_text.lower() not in assistant_text.lower():
					raise RuntimeError(
						f"Phase1.1 Delivery Note Session Reset Smoke failed: request {message!r} did not contain "
						f"required text {required_text!r}. Observed={assistant_text!r}"
					)
				previous_rendered_answer_text = assistant_text
				results.append(
					{
						"message": message,
						"mode": mode,
						"family_validation_status": family_validation_status,
						"artifact_family_id": artifact_family_id,
					}
				)
			return {
				"ok": True,
				"steps": results,
			}
		finally:
			_delete_committed_smoke_session_doc(
				frappe_module=frappe_module,
				session_doctype=session_doctype,
				doc_name=doc.name,
			)

	return _with_compiled_first_turn_full_rollout(
		frappe_module=frappe_module,
		callback=_run,
	)


def run_delivery_note_trend_probe(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	session_tool_payloads,
	latest_tool_payload_by_type,
	latest_assistant_payload=None,
	message: str = "show monthly delivery note trend by customer this fiscal year",
	expected_title_fragment: str = "Trend",
	expected_series_column: str = "Delivered Quantity",
	expected_answer_fragment: str = "",
	expected_summary_metric: str = "",
	minimum_summary_value: float | None = None,
) -> Dict[str, Any]:
	def _run() -> Dict[str, Any]:
		doc = _create_committed_smoke_session_doc(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			title="Phase1.1 Delivery Note Trend Probe",
		)
		try:
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message=message,
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase1.1 Delivery Note Trend Probe failed: governed trend request did not complete.")
			if str((payload or {}).get("mode") or "").strip() != "compiled_first_turn":
				raise RuntimeError(
					f"Phase1.1 Delivery Note Trend Probe failed: expected compiled_first_turn, observed "
					f"{str((payload or {}).get('mode') or '').strip()!r}."
				)
			if str((payload or {}).get("family_validation_status") or "").strip() != "pass":
				raise RuntimeError(
					f"Phase1.1 Delivery Note Trend Probe failed: family validation was "
					f"{str((payload or {}).get('family_validation_status') or '').strip()!r}."
				)
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			rendered = latest_tool_payload_by_type(
				session_tool_payloads(session_doc),
				"qwen_rendered_family_response_contract",
			)
			title = str(rendered.get("title") or "").strip()
			blocks = rendered.get("blocks") if isinstance(rendered.get("blocks"), list) else []
			summary_block = next(
				(
					item
					for item in blocks
					if isinstance(item, dict) and str(item.get("block_type") or "").strip() == "summary_table"
				),
				{},
			)
			series_block = next(
				(
					item
					for item in blocks
					if isinstance(item, dict) and str(item.get("block_type") or "").strip() == "data_table"
				),
				{},
			)
			series_rows = series_block.get("rows") if isinstance(series_block.get("rows"), list) else []
			if expected_title_fragment not in title:
				raise RuntimeError(
					f"Phase1.1 Delivery Note Trend Probe failed: expected title fragment "
					f"{expected_title_fragment!r}, observed {title!r}."
				)
			if not isinstance(summary_block.get("rows"), list) or not summary_block.get("rows"):
				raise RuntimeError("Phase1.1 Delivery Note Trend Probe failed: missing governed trend summary block.")
			if not series_rows:
				raise RuntimeError("Phase1.1 Delivery Note Trend Probe failed: missing governed period series rows.")
			series_columns = [
				str(value or "").strip()
				for value in (series_block.get("columns") if isinstance(series_block.get("columns"), list) else [])
				if str(value or "").strip()
			]
			if expected_series_column and expected_series_column not in series_columns:
				raise RuntimeError(
					f"Phase1.1 Delivery Note Trend Probe failed: expected period-series column "
					f"{expected_series_column!r}, observed {series_columns!r}."
				)
			summary_rows = summary_block.get("rows") if isinstance(summary_block.get("rows"), list) else []
			summary_pairs = {}
			for row in summary_rows:
				if not isinstance(row, list) or len(row) < 2:
					continue
				key = str(row[0] or "").strip()
				value = str(row[1] or "").strip()
				if key:
					summary_pairs[key] = value
			if expected_summary_metric:
				observed_value = summary_pairs.get(expected_summary_metric)
				if observed_value is None:
					raise RuntimeError(
						f"Phase1.1 Delivery Note Trend Probe failed: expected summary metric "
						f"{expected_summary_metric!r}, observed {sorted(summary_pairs.keys())!r}."
					)
				if minimum_summary_value is not None:
					try:
						parsed_value = float(str(observed_value).replace(",", ""))
					except ValueError as exc:
						raise RuntimeError(
							f"Phase1.1 Delivery Note Trend Probe failed: summary metric "
							f"{expected_summary_metric!r} had non-numeric value {observed_value!r}."
						) from exc
					if parsed_value < float(minimum_summary_value):
						raise RuntimeError(
							f"Phase1.1 Delivery Note Trend Probe failed: summary metric "
							f"{expected_summary_metric!r} expected >= {minimum_summary_value!r}, "
							f"observed {parsed_value!r}."
						)
			answer_text = (
				str(latest_assistant_payload(session_doc).get("text") or "").strip()
				if callable(latest_assistant_payload)
				else ""
			)
			if expected_answer_fragment and expected_answer_fragment.lower() not in answer_text.lower():
				raise RuntimeError(
					f"Phase1.1 Delivery Note Trend Probe failed: expected answer fragment "
					f"{expected_answer_fragment!r}, observed {answer_text!r}."
				)
			return {
				"ok": True,
				"message": message,
				"mode": str((payload or {}).get("mode") or "").strip(),
				"family_validation_status": str((payload or {}).get("family_validation_status") or "").strip(),
				"title": title,
				"answer_text": answer_text,
				"series_row_count": len(series_rows),
				"series_columns": series_columns,
			}
		finally:
			_delete_committed_smoke_session_doc(
				frappe_module=frappe_module,
				session_doctype=session_doctype,
				doc_name=doc.name,
			)

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
		doc = _create_committed_smoke_session_doc(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			title="Phase 4B Entity Drilldown Smoke",
		)
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
				message="give me details of ACC-SINV-2026-00192",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Entity drilldown smoke failed on invoice detail request.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			invoice_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if "acc-sinv-2026-00192" not in invoice_text.lower():
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
			_delete_committed_smoke_session_doc(
				frappe_module=frappe_module,
				session_doctype=session_doctype,
				doc_name=doc.name,
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


def run_invoice_delivery_proof_smoke(
	*,
	frappe_module,
	session_doctype: str,
	handle_qwen_user_message,
	latest_assistant_payload,
	session_tool_payloads=None,
	latest_tool_payload_by_type=None,
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
		doc = _create_committed_smoke_session_doc(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			title="Phase 1.1 Invoice Delivery Proof Smoke",
		)
		try:
			ok, _ = handle_qwen_user_message(
				session_name=doc.name,
				message="show me 7 latest sale invoice",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Invoice delivery proof smoke failed on invoice listing request.")
			ok, invoice_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="tell me more about ACC-SINV-2026-00194",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Invoice delivery proof smoke failed on invoice detail request.")
			if str((invoice_payload or {}).get("agent_meta", {}).get("engine") or "").strip() != "entity_detail":
				raise RuntimeError("Invoice delivery proof smoke failed: invoice detail did not use the governed entity-detail engine.")
			ok, delivery_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="items from this invoices are already delivered?",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Invoice delivery proof smoke failed on delivery-proof follow-up.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			answer_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			lower_text = answer_text.lower()
			if str((delivery_payload or {}).get("mode") or "").strip() != "grounded_evidence_answer":
				raise RuntimeError("Invoice delivery proof smoke failed: delivery-proof follow-up did not use grounded evidence answer mode.")
			if "delivered" not in lower_text:
				raise RuntimeError(
					"Invoice delivery proof smoke failed: user-facing answer did not confirm governed delivery proof. "
					f"Observed={answer_text!r}"
				)
			if "delivery note" not in lower_text and "stock movement" not in lower_text and "stock-updating invoice" not in lower_text:
				raise RuntimeError(
					"Invoice delivery proof smoke failed: answer did not cite the governed proof basis. "
					f"Observed={answer_text!r}"
				)
			ok, when_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="what it was delivered",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Invoice delivery proof smoke failed on delivery-date follow-up.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			when_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			lower_when_text = when_text.lower()
			narrative_payload = {}
			if callable(session_tool_payloads) and callable(latest_tool_payload_by_type):
				narrative_payload = latest_tool_payload_by_type(
					session_tool_payloads(session_doc),
					"qwen_artifact_narrative_response_contract",
				)
			if str((when_payload or {}).get("mode") or "").strip() != "grounded_evidence_answer":
				raise RuntimeError("Invoice delivery proof smoke failed: delivery-date follow-up did not use grounded evidence answer mode.")
			if "2026-03-30" not in when_text:
				raise RuntimeError(
					"Invoice delivery proof smoke failed: delivery-date follow-up did not return the governed delivery date. "
					f"Observed={when_text!r}"
				)
			if "delivery note" not in lower_when_text and "zegyo mobile supply house" not in lower_when_text:
				raise RuntimeError(
					"Invoice delivery proof smoke failed: delivery-date follow-up did not retain enough delivery context. "
					f"Observed={when_text!r}"
				)
			return {
				"ok": True,
				"delivery_mode": str((delivery_payload or {}).get("mode") or "").strip(),
				"delivery_text": answer_text,
				"delivery_date_mode": str((when_payload or {}).get("mode") or "").strip(),
				"delivery_date_text": when_text,
				"narrative_contract_answer_text": str(narrative_payload.get("answer_text") or "").strip(),
				"narrative_contract_engine": str(narrative_payload.get("narrative_engine") or "").strip(),
			}
		finally:
			_delete_committed_smoke_session_doc(
				frappe_module=frappe_module,
				session_doctype=session_doctype,
				doc_name=doc.name,
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


def run_fresh_chat_invoice_delivery_proof_smoke(
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
		doc = _create_committed_smoke_session_doc(
			frappe_module=frappe_module,
			session_doctype=session_doctype,
			title="Phase 1.1 Fresh Chat Invoice Delivery Proof Smoke",
		)
		try:
			ok, invoice_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="tell me more about ACC-SINV-2026-00194",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Fresh-chat invoice delivery proof smoke failed on invoice detail request.")
			if str((invoice_payload or {}).get("agent_meta", {}).get("engine") or "").strip() != "entity_detail":
				raise RuntimeError(
					"Fresh-chat invoice delivery proof smoke failed: explicit invoice request did not use governed entity-detail engine."
				)
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			invoice_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			if "acc-sinv-2026-00194" not in invoice_text.lower():
				raise RuntimeError(
					"Fresh-chat invoice delivery proof smoke failed: invoice detail answer did not anchor to the requested invoice."
				)
			if "document count" in invoice_text.lower():
				raise RuntimeError(
					"Fresh-chat invoice delivery proof smoke failed: invoice detail answer still looked like a list summary."
				)

			ok, delivery_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="that item is already delivered to the customer?",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Fresh-chat invoice delivery proof smoke failed on delivery-proof follow-up.")
			session_doc = frappe_module.get_doc(session_doctype, doc.name)
			delivery_text = str(latest_assistant_payload(session_doc).get("text") or "").strip()
			lower_delivery_text = delivery_text.lower()
			if str((delivery_payload or {}).get("mode") or "").strip() != "grounded_evidence_answer":
				raise RuntimeError(
					"Fresh-chat invoice delivery proof smoke failed: delivery-proof follow-up did not use grounded evidence answer mode."
				)
			if "delivered" not in lower_delivery_text or "zegyo mobile supply house" not in lower_delivery_text:
				raise RuntimeError(
					"Fresh-chat invoice delivery proof smoke failed: delivery-proof answer did not stay anchored to invoice evidence. "
					f"Observed={delivery_text!r}"
				)
			return {
				"ok": True,
				"invoice_mode": str((invoice_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
				"invoice_text": invoice_text,
				"delivery_mode": str((delivery_payload or {}).get("mode") or "").strip(),
				"delivery_text": delivery_text,
			}
		finally:
			_delete_committed_smoke_session_doc(
				frappe_module=frappe_module,
				session_doctype=session_doctype,
				doc_name=doc.name,
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
