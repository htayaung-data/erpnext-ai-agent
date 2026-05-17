from __future__ import annotations

import unittest
from unittest.mock import patch

from app.schemas import FollowUpInterpretRequest
from app.semantic_followup_engine import _system_prompt, run_semantic_followup_engine


class _SettingsStub:
	qwen_base_url = "http://runtime.test"
	qwen_api_key = "token"
	chat_timeout_seconds = 30
	semantic_followup_max_attempts = 1
	semantic_followup_backoff_ms = 0

	def effective_semantic_followup_model(self) -> str:
		return "qwen-test-followup"


class TestSemanticFollowupEngine(unittest.TestCase):
	def test_system_prompt_requires_full_structured_followup_contract(self):
		prompt = _system_prompt()
		self.assertIn("target_metric", prompt)
		self.assertIn("requested_columns", prompt)
		self.assertIn("requested_time_scope", prompt)
		self.assertIn("repeating the same governed business question again", prompt)
		self.assertIn("grounded_followup_supported", prompt)

	@patch("app.semantic_followup_engine._chat_completion_json")
	def test_engine_preserves_extended_structured_fields(self, mock_chat_completion_json):
		mock_chat_completion_json.return_value = (
			{
				"choices": [
					{
						"message": {
							"content": (
								'{"requested_modes":["column_projection","sort_or_limit"],'
								'"target_dimension":"Customer","target_limit":5,"sort_direction":"desc",'
								'"target_metric":"quantity","requested_columns":["quantity"],'
								'"requested_time_scope":"last_month","target_capability_id":"",'
								'"self_contained":false,"confidence":0.93,"reason":"Structured follow-up."}'
							)
						}
					}
				]
			},
			200,
			12,
		)
		request = FollowUpInterpretRequest(
			request_id="followup-engine-test",
			session_id="sess-1",
			user_id="Administrator",
			site_name="erpai_prj1",
			message="show top 5 qty last month",
			latest_grounded_turn={"source_name": "Sales Analytics"},
			latest_assistant_payload={"title": "Sales"},
			interpretation_context={
				"approved_follow_up_modes": ["column_projection", "sort_or_limit"],
				"available_dimensions": ["Customer"],
				"available_metrics": ["Quantity"],
				"available_sibling_capabilities": [],
			},
		)
		response = run_semantic_followup_engine(request, _SettingsStub())
		self.assertTrue(response.ok)
		self.assertIsNotNone(response.interpretation)
		self.assertEqual(response.interpretation.target_metric, "quantity")
		self.assertEqual(response.interpretation.requested_columns, ["quantity"])
		self.assertEqual(response.interpretation.requested_time_scope, "last_month")
		self.assertEqual(response.interpretation.target_limit, 5)


if __name__ == "__main__":
	unittest.main()
