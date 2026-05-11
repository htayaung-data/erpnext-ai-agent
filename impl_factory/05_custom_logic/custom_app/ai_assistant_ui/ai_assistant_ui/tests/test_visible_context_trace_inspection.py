import json
import unittest
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.visible_context_trace_inspection import (
	INSPECTION_PAYLOAD_TYPE,
	try_activate_visible_context_trace_inspection_response,
	visible_context_trace_inspection_requested,
)
from ai_assistant_ui.tests.test_visible_context_conversation_regression import (
	ConversationTurnResult,
	VisibleConversationHarness,
	_ap_top_5_text,
	_cogs_source_detail_text,
)


class TraceInspectionHarness(VisibleConversationHarness):
	def inspect(self, raw_message: str) -> ConversationTurnResult:
		messages = []
		payloads: List[Dict[str, Any]] = []

		def append_message(session_doc, role, text):
			messages.append((role, text))
			session_doc.setdefault("messages", []).append({"role": role, "content": text})

		def append_payload(session_doc, payload):
			payloads.append(payload)
			session_doc.setdefault("messages", []).append({"role": "tool", "content": json.dumps(payload)})

		def save_session(session_doc, **kwargs):
			session_doc["saved"] = True

		handled, payload = try_activate_visible_context_trace_inspection_response(
			session_doc=self.session_doc,
			request_id="req-visible-trace-inspection",
			session_id="session-visible-trace-inspection",
			user_id="user@example.com",
			site_name="erpai_prj1",
			raw_message=raw_message,
			append_message=append_message,
			append_tool_payload=append_payload,
			assistant_text_payload=lambda text: text,
			save_session=save_session,
		)
		return ConversationTurnResult(
			handled=handled,
			payload=payload,
			answer="\n".join(message[1] for message in messages if message[0] == "assistant"),
			payloads=payloads,
		)


class VisibleContextTraceInspectionTests(unittest.TestCase):
	def test_trace_intent_is_explicit_and_does_not_steal_business_questions(self):
		self.assertTrue(visible_context_trace_inspection_requested("show latest context authority trace"))
		self.assertTrue(visible_context_trace_inspection_requested("inspect the frame arbitration"))
		self.assertFalse(visible_context_trace_inspection_requested("who is second in the above table?"))
		self.assertFalse(visible_context_trace_inspection_requested("Explain the overdue risk in this accounts receivable summary."))

	def test_trace_inspection_renders_latest_selected_frame(self):
		chat = TraceInspectionHarness()
		chat.assistant(_cogs_source_detail_text())
		lookup = chat.ask("who is second in the above table?")
		self.assertTrue(lookup.handled)

		inspection = chat.inspect("show latest context authority trace")

		self.assertTrue(inspection.handled)
		self.assertEqual(inspection.payload["mode"], "visible_context_trace_inspection")
		self.assertIn("Context Authority Trace", inspection.answer)
		self.assertIn("Status: resolved", inspection.answer)
		self.assertIn("Relation: current_table", inspection.answer)
		self.assertIn("Selected object type: document", inspection.answer)
		self.assertIn("Selection strategy: current_table:authority_rank", inspection.answer)
		self.assertIn("Delivery Note MAT-DN-2026-00336", inspection.answer)
		inspection_contract = inspection.latest_payload(INSPECTION_PAYLOAD_TYPE)
		self.assertEqual(inspection_contract.get("trace_status"), "resolved")
		self.assertEqual(inspection_contract.get("selected_business_object_type"), "document")
		self.assertEqual(inspection.execution_path.get("path"), "visible_context_trace_inspection")
		self.assertFalse(inspection.execution_path.get("requires_runtime"))

	def test_trace_inspection_exposes_missing_object_boundary(self):
		chat = TraceInspectionHarness()
		chat.assistant(_cogs_source_detail_text())
		chat.ask("who is second in the above table?")
		chat.assistant(_ap_top_5_text())
		missing_invoice = chat.ask("who is second invoice in the above context?")
		self.assertTrue(missing_invoice.handled)
		self.assertEqual(missing_invoice.payload["mode"], "visible_context_boundary")

		inspection = chat.inspect("show latest visible context authority trace")

		self.assertTrue(inspection.handled)
		self.assertIn("Status: missing_requested_object", inspection.answer)
		self.assertIn("Requested object: invoice", inspection.answer)
		self.assertIn("Selected frame: none", inspection.answer)
		self.assertIn("requested_object_type_mismatch", inspection.answer)
		inspection_contract = inspection.latest_payload(INSPECTION_PAYLOAD_TYPE)
		self.assertEqual(inspection_contract.get("trace_status"), "missing_requested_object")
		self.assertEqual(inspection_contract.get("requested_object_label"), "invoice")
		self.assertGreaterEqual(inspection_contract.get("rejected_frame_count") or 0, 1)

	def test_trace_inspection_reports_trace_frame_recovery_source(self):
		chat = TraceInspectionHarness()
		chat.assistant(_cogs_source_detail_text())
		chat.ask("who is second in the above table?")
		chat.session_doc["messages"] = [
			message
			for message in chat.session_doc["messages"]
			if "Breakdown by source document" not in str(message.get("content", ""))
		]
		recovered_lookup = chat.ask("who is second in the above table?")
		self.assertTrue(recovered_lookup.handled)

		inspection = chat.inspect("show latest context authority trace")

		self.assertIn("Recovery source: visible_context_trace_frame", inspection.answer)
		inspection_contract = inspection.latest_payload(INSPECTION_PAYLOAD_TYPE)
		self.assertEqual(inspection_contract.get("selected_recovery_source"), "visible_context_trace_frame")


if __name__ == "__main__":
	unittest.main()
