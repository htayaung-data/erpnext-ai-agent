from __future__ import annotations

import datetime as dt
import unittest
from unittest.mock import patch

import requests

from ai_assistant_ui.qwen_chat import defaults_repository, runtime_client


class _FakeResponse:
	def __init__(self, *, status_code: int = 200, payload=None):
		self.status_code = status_code
		self._payload = payload

	def json(self):
		if isinstance(self._payload, Exception):
			raise self._payload
		return self._payload


class TestDefaultsRepositoryContracts(unittest.TestCase):
	def test_defaults_repository_derives_company_and_fiscal_years(self):
		rows = [
			{"name": "FY-2025", "year_start_date": "2025-01-01", "year_end_date": "2025-12-31"},
			{"name": "FY-2026", "year_start_date": "2026-01-01", "year_end_date": "2026-12-31"},
		]
		with patch(
			"ai_assistant_ui.qwen_chat.defaults_repository.load_company_names",
			return_value=["Mingalar Mobile Distribution Co., Ltd."],
		), patch(
			"ai_assistant_ui.qwen_chat.defaults_repository.load_fiscal_year_rows",
			return_value=rows,
		):
			self.assertEqual(
				defaults_repository.single_company_name(),
				"Mingalar Mobile Distribution Co., Ltd.",
			)
			self.assertEqual(
				defaults_repository.current_fiscal_year_name(today=dt.date(2026, 4, 7)),
				"FY-2026",
			)
			self.assertEqual(
				defaults_repository.previous_fiscal_year_name(today=dt.date(2026, 4, 7)),
				"FY-2025",
			)
			self.assertEqual(
				defaults_repository.current_fiscal_year_bounds(today=dt.date(2026, 4, 7)),
				("2026-01-01", "2026-12-31"),
			)


class TestRuntimeClientContracts(unittest.TestCase):
	def test_call_qwen_runtime_chat_uses_shared_transport_with_request_config(self):
		response = _FakeResponse(payload={"ok": True, "answer_text": "ready"})
		with patch("ai_assistant_ui.qwen_chat.runtime_client.requests.post", return_value=response) as post_mock:
			payload = runtime_client.call_qwen_runtime_chat(
				session_id="sess-1",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="hello",
				recent_messages=[],
				response_policy={},
				family_tool_context={},
				mode="read_only",
				request_id="req-1",
				request_config={
					"base_url": "http://runtime.example",
					"headers": {"Content-Type": "application/json", "Authorization": "Bearer x"},
					"timeout_seconds": 15,
				},
			)

		self.assertEqual(payload, {"ok": True, "answer_text": "ready"})
		post_mock.assert_called_once()
		self.assertEqual(post_mock.call_args.kwargs["timeout"], 15.0)
		self.assertEqual(post_mock.call_args.args[0], "http://runtime.example/chat")

	def test_frontdoor_interpretation_preserves_endpoint_specific_error_prefix(self):
		with patch(
			"ai_assistant_ui.qwen_chat.runtime_client._base_url",
			return_value="http://runtime.example",
		), patch(
			"ai_assistant_ui.qwen_chat.runtime_client.requests.post",
			side_effect=requests.RequestException("boom"),
		):
			with self.assertRaises(runtime_client.QwenRuntimeClientError) as exc_info:
				runtime_client.call_qwen_runtime_frontdoor_interpretation(
					request_id="req-2",
					session_id="sess-2",
					user_id="Administrator",
					site_name="erpai_prj1",
					message="hello",
					recent_messages=[],
					grounded_context_available=False,
					interpretation_context={},
				)
		self.assertIn("Qwen runtime front-door interpretation failed", str(exc_info.exception))

