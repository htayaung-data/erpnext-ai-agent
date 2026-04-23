from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict


@dataclass(frozen=True)
class ScopePackageSmokeDependencies:
    frappe_module: Any
    session_doctype: str
    handle_qwen_user_message: Callable[..., Any]
    run_smoke_fresh_query_turn_with_retry: Callable[..., Any]
    run_phase55_smoke_session: Callable[..., Dict[str, Any]]
    latest_assistant_payload: Callable[..., Dict[str, Any]]
    latest_grounded_turn_contract: Callable[..., Dict[str, Any]]
    latest_normalized_family_artifact: Callable[..., Dict[str, Any]]
    entity_detail_evidence_request_payload: Callable[..., Dict[str, Any]]
    grounded_artifact_direct_evidence_answer: Callable[..., Dict[str, Any]]
    grounded_artifact_evidence_boundary_answer: Callable[..., Dict[str, Any]]
    session_tool_payloads: Callable[..., Any]
    latest_tool_payload_by_type: Callable[..., Dict[str, Any]]
    latest_qwen_trace_payload: Callable[..., Dict[str, Any]]


def _contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    lowered = str(text or "").lower()
    return any(phrase in lowered for phrase in phrases)


def run_phase_e2_1b_purchase_invoice_listing_smoke(*, deps: ScopePackageSmokeDependencies) -> Dict[str, Any]:
    def _runner(doc) -> Dict[str, Any]:
        deps.frappe_module.clear_cache()
        ok, first_payload = deps.run_smoke_fresh_query_turn_with_retry(
            session_name=doc.name,
            message="show me purchase invoices",
            user="Administrator",
            allowed_modes={
                "compiled_first_turn",
                "legacy_runtime",
                "legacy_runtime_rollout_fallback",
            },
        )
        if not ok:
            session_doc = deps.frappe_module.get_doc(deps.session_doctype, doc.name)
            raise RuntimeError(
                "Phase E2.1B purchase invoice smoke failed: initial purchase invoice list request did not execute. "
                f"payload={first_payload!r} latest_assistant={deps.latest_assistant_payload(session_doc)!r}"
            )

        session_doc = deps.frappe_module.get_doc(deps.session_doctype, doc.name)
        first_grounded_turn = deps.latest_grounded_turn_contract(session_doc)
        first_artifact = deps.latest_normalized_family_artifact(session_doc, grounded_turn=first_grounded_turn)
        first_assistant_text = str(deps.latest_assistant_payload(session_doc).get("text") or "").strip()
        first_source_name = str(first_grounded_turn.get("source_name") or "").strip()
        first_reports = {
            str(value or "").strip()
            for value in (first_grounded_turn.get("artifact_source_reports") or [])
            if str(value or "").strip()
        }
        first_family_id = str(first_grounded_turn.get("artifact_family_id") or "").strip()
        first_scope_id = str(((first_artifact.get("dimensions") or {}).get("scope_id") or "")).strip()
        if "Purchase Invoice List" not in ({first_source_name} | first_reports):
            raise RuntimeError(
                "Phase E2.1B purchase invoice smoke failed: grounded source did not bind to Purchase Invoice List. "
                f"grounded_turn={first_grounded_turn!r}"
            )
        if first_family_id != "transaction_listing":
            raise RuntimeError(
                "Phase E2.1B purchase invoice smoke failed: purchase invoice list did not land in transaction_listing family. "
                f"grounded_turn={first_grounded_turn!r}"
            )
        if first_scope_id != "purchase_invoice":
            raise RuntimeError(
                "Phase E2.1B purchase invoice smoke failed: normalized artifact did not preserve purchase_invoice scope. "
                f"artifact={first_artifact!r}"
            )
        if _contains_any(
            first_assistant_text,
            (
                "can't show purchase invoices",
                "can't open purchase invoices",
                "which one would you like to see",
            ),
        ):
            raise RuntimeError(
                "Phase E2.1B purchase invoice smoke failed: user-facing answer still reflected the old blocked path. "
                f"assistant_text={first_assistant_text!r}"
            )

        deps.frappe_module.clear_cache()
        ok, second_payload = deps.handle_qwen_user_message(
            session_name=doc.name,
            message="show supplier and outstanding amount only",
            user="Administrator",
        )
        second_mode = str((second_payload or {}).get("mode") or "").strip()
        second_engine = str((((second_payload or {}).get("agent_meta") or {}).get("engine") or "")).strip()
        if not ok or (
            second_mode
            not in {
                "compiled_first_turn",
                "artifact_enrichment_boundary",
                "recovery_guidance",
                "legacy_runtime",
                "legacy_runtime_rollout_fallback",
            }
            and second_engine not in {"local_transform"}
        ):
            session_doc = deps.frappe_module.get_doc(deps.session_doctype, doc.name)
            raise RuntimeError(
                "Phase E2.1B purchase invoice smoke failed: purchase invoice follow-up did not complete in an allowed lane. "
                f"payload={second_payload!r} latest_assistant={deps.latest_assistant_payload(session_doc)!r}"
            )

        session_doc = deps.frappe_module.get_doc(deps.session_doctype, doc.name)
        second_assistant_text = str(deps.latest_assistant_payload(session_doc).get("text") or "").strip()
        second_lower = second_assistant_text.lower()
        if "supplier" not in second_lower or "outstanding" not in second_lower:
            raise RuntimeError(
                "Phase E2.1B purchase invoice smoke failed: follow-up answer did not honor supplier/outstanding projection. "
                f"assistant_text={second_assistant_text!r}"
            )
        if _contains_any(
            second_assistant_text,
            (
                "can't answer it safely",
                "can't safely add",
                "needs a governed requery",
                "which one would you like",
            ),
        ):
            raise RuntimeError(
                "Phase E2.1B purchase invoice smoke failed: follow-up answer fell back to an old blocked/clarify posture. "
                f"assistant_text={second_assistant_text!r}"
            )

        return {
            "ok": True,
            "first_mode": str((first_payload or {}).get("mode") or "").strip(),
            "first_source_name": first_source_name,
            "first_family_id": first_family_id,
            "first_scope_id": first_scope_id,
            "second_mode": second_mode,
            "second_engine": second_engine,
            "first_answer_text": first_assistant_text,
            "second_answer_text": second_assistant_text,
        }

    return deps.run_phase55_smoke_session("Phase E2.1B Purchase Invoice Listing Smoke", _runner)


def run_phase_e1_4_item_master_activation_smoke(*, deps: ScopePackageSmokeDependencies) -> Dict[str, Any]:
    def _runner(doc) -> Dict[str, Any]:
        deps.frappe_module.clear_cache()
        ok, first_payload = deps.run_smoke_fresh_query_turn_with_retry(
            session_name=doc.name,
            message="give me some product list",
            user="Administrator",
            allowed_modes={
                "compiled_first_turn",
                "legacy_runtime",
                "legacy_runtime_rollout_fallback",
            },
        )
        if not ok:
            session_doc = deps.frappe_module.get_doc(deps.session_doctype, doc.name)
            raise RuntimeError(
                "Phase E1.4 item master activation smoke failed: initial product list request did not execute. "
                f"payload={first_payload!r} latest_assistant={deps.latest_assistant_payload(session_doc)!r}"
            )

        session_doc = deps.frappe_module.get_doc(deps.session_doctype, doc.name)
        first_grounded_turn = deps.latest_grounded_turn_contract(session_doc)
        first_artifact = deps.latest_normalized_family_artifact(session_doc, grounded_turn=first_grounded_turn)
        first_assistant_text = str(deps.latest_assistant_payload(session_doc).get("text") or "").strip()
        first_source_name = str(first_grounded_turn.get("source_name") or "").strip()
        first_reports = {
            str(value or "").strip()
            for value in (first_grounded_turn.get("artifact_source_reports") or [])
            if str(value or "").strip()
        }
        first_family_id = str(first_grounded_turn.get("artifact_family_id") or "").strip()
        first_scope_id = str(((first_artifact.get("dimensions") or {}).get("scope_id") or "")).strip()
        if "Item Master List" not in ({first_source_name} | first_reports):
            raise RuntimeError(
                "Phase E1.4 item master activation smoke failed: grounded source did not bind to Item Master List. "
                f"grounded_turn={first_grounded_turn!r}"
            )
        if first_family_id != "master_data_directory":
            raise RuntimeError(
                "Phase E1.4 item master activation smoke failed: product list did not land in master_data_directory family. "
                f"grounded_turn={first_grounded_turn!r}"
            )
        if first_scope_id != "item_master":
            raise RuntimeError(
                "Phase E1.4 item master activation smoke failed: normalized artifact did not preserve item_master scope. "
                f"artifact={first_artifact!r}"
            )
        if _contains_any(
            first_assistant_text,
            (
                "customers or suppliers",
                "can't open items as a list",
                "can't open item as a list",
                "which one would you like",
            ),
        ):
            raise RuntimeError(
                "Phase E1.4 item master activation smoke failed: user-facing answer still reflected the old blocked path. "
                f"assistant_text={first_assistant_text!r}"
            )

        return {
            "ok": True,
            "first_mode": str((first_payload or {}).get("mode") or "").strip(),
            "first_source_name": first_source_name,
            "first_family_id": first_family_id,
            "first_scope_id": first_scope_id,
            "first_answer_text": first_assistant_text,
        }

    return deps.run_phase55_smoke_session("Phase E1.4 Item Master Activation Smoke", _runner)


def run_phase_e1_5_item_deictic_continuity_smoke(*, deps: ScopePackageSmokeDependencies) -> Dict[str, Any]:
    def _runner(doc) -> Dict[str, Any]:
        item_rows = deps.frappe_module.get_all("Item", fields=["name", "item_name"], order_by="modified desc", limit=10)
        selected_item_label = ""
        for row in item_rows or []:
            if not isinstance(row, dict):
                continue
            selected_item_label = str(row.get("item_name") or row.get("name") or "").strip()
            if selected_item_label:
                break
        if not selected_item_label:
            raise RuntimeError(
                "Phase E1.5 item deictic continuity smoke failed: no live item label was available to seed the lookup."
            )

        deps.frappe_module.clear_cache()
        ok, first_payload = deps.run_smoke_fresh_query_turn_with_retry(
            session_name=doc.name,
            message=f'do u have product name similar to "{selected_item_label}"',
            user="Administrator",
            allowed_modes={
                "compiled_first_turn",
                "legacy_runtime",
                "legacy_runtime_rollout_fallback",
            },
        )
        if not ok:
            session_doc = deps.frappe_module.get_doc(deps.session_doctype, doc.name)
            raise RuntimeError(
                "Phase E1.5 item deictic continuity smoke failed: initial product candidate-resolution request did not execute. "
                f"payload={first_payload!r} latest_assistant={deps.latest_assistant_payload(session_doc)!r}"
            )

        session_doc = deps.frappe_module.get_doc(deps.session_doctype, doc.name)
        first_grounded_turn = deps.latest_grounded_turn_contract(session_doc)
        first_artifact = deps.latest_normalized_family_artifact(session_doc, grounded_turn=first_grounded_turn)
        first_assistant_text = str(deps.latest_assistant_payload(session_doc).get("text") or "").strip()
        first_lower = first_assistant_text.lower()
        first_mode = str((first_payload or {}).get("mode") or "").strip()
        first_family_id = str(first_grounded_turn.get("artifact_family_id") or "").strip()
        first_scope_id = str(((first_artifact.get("dimensions") or {}).get("scope_id") or "")).strip()
        first_resolution = (
            (first_artifact.get("sections") or {}).get("entity_reference_resolution")
            if isinstance(first_artifact.get("sections"), dict)
            else {}
        )
        first_directory_rows = (
            (first_artifact.get("sections") or {}).get("directory_rows")
            if isinstance(first_artifact.get("sections"), dict)
            else []
        )
        first_resolved_entity = (
            first_resolution.get("resolved_entity")
            if isinstance(first_resolution, dict) and isinstance(first_resolution.get("resolved_entity"), dict)
            else {}
        )
        first_resolution_status = str((first_resolution or {}).get("resolution_status") or "").strip()
        first_resolved_key = str(
            (first_resolved_entity or {}).get("entity_key") or (first_resolved_entity or {}).get("entity_label") or ""
        ).strip()
        if not first_resolved_key and isinstance(first_directory_rows, list) and len(first_directory_rows) == 1:
            first_directory_row = first_directory_rows[0] if isinstance(first_directory_rows[0], dict) else {}
            first_resolved_key = str(
                first_directory_row.get("entity_code") or first_directory_row.get("entity_name") or first_directory_row.get("entity") or ""
            ).strip()
            if first_resolved_key and not first_resolution_status:
                first_resolution_status = "single_row_context"
        if first_family_id != "master_data_directory" or first_scope_id != "item_master":
            raise RuntimeError(
                "Phase E1.5 item deictic continuity smoke failed: candidate resolution did not stay in shared item master directory family. "
                f"grounded_turn={first_grounded_turn!r} artifact={first_artifact!r}"
            )
        if first_resolution_status not in {"resolved", "single_row_context"} or not first_resolved_key:
            raise RuntimeError(
                "Phase E1.5 item deictic continuity smoke failed: candidate resolution did not produce a single item context. "
                f"artifact={first_artifact!r}"
            )
        if any(
            phrase in first_lower
            for phrase in (
                "customers or suppliers",
                "can't open items as a list",
                "can't open item as a list",
                "which one would you like",
            )
        ):
            raise RuntimeError(
                "Phase E1.5 item deictic continuity smoke failed: candidate resolution answer fell back to an old blocked posture. "
                f"assistant_text={first_assistant_text!r}"
            )

        deps.frappe_module.clear_cache()
        ok, second_payload = deps.handle_qwen_user_message(
            session_name=doc.name,
            message="tell me more about that product",
            user="Administrator",
        )
        second_mode = str((second_payload or {}).get("mode") or "").strip()
        second_engine = str((((second_payload or {}).get("agent_meta") or {}).get("engine") or "")).strip()
        second_agent_mode = str((((second_payload or {}).get("agent_meta") or {}).get("mode") or "")).strip()
        if not ok or (
            second_mode
            not in {
                "compiled_first_turn",
                "legacy_runtime",
                "legacy_runtime_rollout_fallback",
            }
            and second_engine not in {"entity_detail"}
            and second_agent_mode != "entity_drilldown"
        ):
            session_doc = deps.frappe_module.get_doc(deps.session_doctype, doc.name)
            raise RuntimeError(
                "Phase E1.5 item deictic continuity smoke failed: deictic product follow-up did not execute. "
                f"payload={second_payload!r} latest_assistant={deps.latest_assistant_payload(session_doc)!r}"
            )

        session_doc = deps.frappe_module.get_doc(deps.session_doctype, doc.name)
        second_grounded_turn = deps.latest_grounded_turn_contract(session_doc)
        second_artifact = deps.latest_normalized_family_artifact(session_doc, grounded_turn=second_grounded_turn)
        second_assistant_text = str(deps.latest_assistant_payload(session_doc).get("text") or "").strip()
        second_lower = second_assistant_text.lower()
        second_family_id = str(second_grounded_turn.get("artifact_family_id") or "").strip()
        second_entity_type = str(((second_artifact.get("dimensions") or {}).get("entity_type") or "")).strip()
        second_entity_key = str(((second_artifact.get("dimensions") or {}).get("entity_key") or "")).strip()
        if second_family_id != "entity_detail" or second_entity_type != "item":
            raise RuntimeError(
                "Phase E1.5 item deictic continuity smoke failed: deictic product follow-up did not land in shared entity_detail item path. "
                f"grounded_turn={second_grounded_turn!r} artifact={second_artifact!r}"
            )
        if first_resolved_key and second_entity_key and first_resolved_key != second_entity_key:
            raise RuntimeError(
                "Phase E1.5 item deictic continuity smoke failed: deictic product follow-up did not preserve the resolved item identity. "
                f"resolved_key={first_resolved_key!r} detail_key={second_entity_key!r}"
            )
        if any(
            phrase in second_lower
            for phrase in (
                "customers or suppliers",
                "can't open items as a list",
                "can't open item as a list",
                "which one would you like",
            )
        ):
            raise RuntimeError(
                "Phase E1.5 item deictic continuity smoke failed: deictic product follow-up fell back to the wrong path. "
                f"assistant_text={second_assistant_text!r}"
            )
        if not any(phrase in second_lower for phrase in ("item profile", "brand", "item group")):
            raise RuntimeError(
                "Phase E1.5 item deictic continuity smoke failed: detail answer did not render item profile content. "
                f"assistant_text={second_assistant_text!r}"
            )

        return {
            "ok": True,
            "selected_item_label": selected_item_label,
            "first_mode": first_mode,
            "first_family_id": first_family_id,
            "first_scope_id": first_scope_id,
            "first_resolution_status": first_resolution_status,
            "first_resolved_key": first_resolved_key,
            "first_answer_text": first_assistant_text,
            "second_mode": second_mode,
            "second_family_id": second_family_id,
            "second_engine": second_engine,
            "second_agent_mode": second_agent_mode,
            "second_entity_type": second_entity_type,
            "second_entity_key": second_entity_key,
            "second_answer_text": second_assistant_text,
        }

    return deps.run_phase55_smoke_session("Phase E1.5 Item Deictic Continuity Smoke", _runner)


def run_phase_e1_6_item_inventory_followup_debug_smoke(*, deps: ScopePackageSmokeDependencies) -> Dict[str, Any]:
    def _runner(doc) -> Dict[str, Any]:
        third_message = "how many stocks do we have for that products, and in which warehouse?"
        deps.frappe_module.clear_cache()
        ok, first_payload = deps.handle_qwen_user_message(
            session_name=doc.name,
            message='do u have product name similar to "Type-C Cable 1m Fast Charge"?',
            user="Administrator",
        )
        if not ok:
            raise RuntimeError(f"Phase E1.6 debug smoke failed on first turn: {first_payload!r}")

        deps.frappe_module.clear_cache()
        ok, second_payload = deps.handle_qwen_user_message(
            session_name=doc.name,
            message="tell me more about that product",
            user="Administrator",
        )
        if not ok:
            raise RuntimeError(f"Phase E1.6 debug smoke failed on second turn: {second_payload!r}")
        session_doc = deps.frappe_module.get_doc(deps.session_doctype, doc.name)
        second_grounded_turn = deps.latest_grounded_turn_contract(session_doc)
        second_artifact = deps.latest_normalized_family_artifact(session_doc, grounded_turn=second_grounded_turn)
        stock_rows = (
            (second_artifact.get("sections") or {}).get("stock_rows")
            if isinstance((second_artifact.get("sections") or {}), dict)
            else []
        )
        third_evidence_request = deps.entity_detail_evidence_request_payload(
            request_id="phase-e1-6-debug",
            raw_message=third_message,
            artifact_payload=second_artifact,
        )
        third_evidence_answer = deps.grounded_artifact_direct_evidence_answer(
            raw_message=third_message,
            artifact_payload=second_artifact,
            grounded_turn=second_grounded_turn,
            evidence_request_contract=third_evidence_request,
        )
        third_evidence_boundary = deps.grounded_artifact_evidence_boundary_answer(
            raw_message=third_message,
            artifact_payload=second_artifact,
            grounded_turn=second_grounded_turn,
            evidence_request_contract=third_evidence_request,
        )

        try:
            deps.frappe_module.clear_cache()
            ok, third_payload = deps.handle_qwen_user_message(
                session_name=doc.name,
                message=third_message,
                user="Administrator",
            )
            session_doc = deps.frappe_module.get_doc(deps.session_doctype, doc.name)
            return {
                "ok": ok,
                "third_payload": third_payload,
                "second_grounded_turn": second_grounded_turn,
                "second_artifact": second_artifact,
                "second_stock_row_count": len(stock_rows) if isinstance(stock_rows, list) else 0,
                "third_evidence_request": third_evidence_request,
                "third_evidence_answer": third_evidence_answer,
                "third_evidence_boundary": third_evidence_boundary,
                "latest_assistant": deps.latest_assistant_payload(session_doc),
                "latest_grounded_turn": deps.latest_grounded_turn_contract(session_doc),
                "latest_followup_resolution": deps.latest_tool_payload_by_type(
                    deps.session_tool_payloads(session_doc),
                    "qwen_followup_resolution",
                ),
                "latest_execution_path": deps.latest_tool_payload_by_type(
                    deps.session_tool_payloads(session_doc),
                    "qwen_execution_path",
                ),
                "latest_qwen_trace": deps.latest_qwen_trace_payload(session_doc),
                "latest_artifact": deps.latest_normalized_family_artifact(
                    session_doc,
                    grounded_turn=deps.latest_grounded_turn_contract(session_doc),
                ),
            }
        except Exception:
            session_doc = deps.frappe_module.get_doc(deps.session_doctype, doc.name)
            return {
                "ok": False,
                "error_traceback": traceback.format_exc(),
                "second_grounded_turn": second_grounded_turn,
                "second_artifact": second_artifact,
                "second_stock_row_count": len(stock_rows) if isinstance(stock_rows, list) else 0,
                "third_evidence_request": third_evidence_request,
                "third_evidence_answer": third_evidence_answer,
                "third_evidence_boundary": third_evidence_boundary,
                "latest_assistant": deps.latest_assistant_payload(session_doc),
                "latest_grounded_turn": deps.latest_grounded_turn_contract(session_doc),
                "latest_followup_resolution": deps.latest_tool_payload_by_type(
                    deps.session_tool_payloads(session_doc),
                    "qwen_followup_resolution",
                ),
                "latest_execution_path": deps.latest_tool_payload_by_type(
                    deps.session_tool_payloads(session_doc),
                    "qwen_execution_path",
                ),
                "latest_qwen_trace": deps.latest_qwen_trace_payload(session_doc),
                "latest_artifact": deps.latest_normalized_family_artifact(
                    session_doc,
                    grounded_turn=deps.latest_grounded_turn_contract(session_doc),
                ),
            }

    return deps.run_phase55_smoke_session("Phase E1.6 Item Inventory Follow-Up Debug Smoke", _runner)

