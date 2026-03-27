import unittest

from ai_assistant_ui.qwen_chat.observability import (
	build_phase55_observability_event,
	build_phase6_observability_event,
	build_phase6_performance_metric,
)


class TestPostContractObservability(unittest.TestCase):
	def test_phase55_observability_event_shape(self):
		event = build_phase55_observability_event(
			request_id="phase55-obs",
			session_id="session-1",
			event_family="clarification",
			event_name="resolved",
			details={"attempt_count": 1},
		)
		self.assertEqual(event.get("type"), "qwen_phase55_observability_event")
		self.assertEqual(event.get("request_id"), "phase55-obs")
		self.assertEqual(event.get("session_id"), "session-1")
		self.assertEqual(event.get("event_family"), "clarification")
		self.assertEqual(event.get("event_name"), "resolved")
		self.assertEqual((event.get("details") or {}).get("attempt_count"), 1)
		self.assertTrue(bool(event.get("created_at")))

	def test_phase6_observability_event_normalizes_invalid_level(self):
		event = build_phase6_observability_event(
			request_id="phase6-obs",
			session_id="session-2",
			event_family="reasoning_execution",
			event_name="answered",
			event_level="SEVERE",
			details={"status": "answered"},
		)
		self.assertEqual(event.get("type"), "qwen_phase6_observability_event")
		self.assertEqual(event.get("event_level"), "info")

	def test_phase6_observability_event_preserves_valid_warning_level(self):
		event = build_phase6_observability_event(
			request_id="phase6-obs-warning",
			session_id="session-3",
			event_family="reasoning_execution",
			event_name="insufficient_grounding",
			event_level="warning",
			details={"grounding_sufficient": False},
		)
		self.assertEqual(event.get("event_level"), "warning")
		self.assertEqual((event.get("details") or {}).get("grounding_sufficient"), False)

	def test_phase6_performance_metric_normalizes_numeric_payload(self):
		metric = build_phase6_performance_metric(
			request_id="phase6-metric",
			session_id="session-4",
			metric_name="reasoning_execution_latency",
			metric_value=12,
			metric_unit="ms",
			details={"status": "answered"},
		)
		self.assertEqual(metric.get("type"), "qwen_phase6_performance_metric")
		self.assertEqual(metric.get("metric_name"), "reasoning_execution_latency")
		self.assertEqual(metric.get("metric_value"), 12.0)
		self.assertEqual(metric.get("metric_unit"), "ms")
		self.assertEqual((metric.get("details") or {}).get("status"), "answered")

	def test_phase6_observability_event_supports_unsupported_non_erp_boundary_warning(self):
		event = build_phase6_observability_event(
			request_id="phase6-unsupported-boundary",
			session_id="session-5",
			event_family="knowledge_boundary",
			event_name="unsupported_non_erp",
			event_level="warning",
			details={"safe_next_action": "respond_unsupported"},
		)
		self.assertEqual(event.get("event_family"), "knowledge_boundary")
		self.assertEqual(event.get("event_name"), "unsupported_non_erp")
		self.assertEqual(event.get("event_level"), "warning")
		self.assertEqual((event.get("details") or {}).get("safe_next_action"), "respond_unsupported")
