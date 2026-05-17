import unittest
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import patch

from frappe.utils.file_lock import LockTimeoutError

from ai_assistant_ui import api


@contextmanager
def _noop_lock(*args, **kwargs):
	yield


class TestQwenChatApi(unittest.TestCase):
	def test_qwen_chat_send_uses_session_lock_and_returns_payload(self):
		with patch("ai_assistant_ui.api._get_qwen_session", return_value=object()), patch(
			"ai_assistant_ui.api.filelock",
			side_effect=lambda *args, **kwargs: _noop_lock(),
		) as lock_mock, patch(
			"ai_assistant_ui.api.handle_qwen_user_message",
			return_value=(True, {"ok": True, "mode": "front_door"}),
		) as handle_mock, patch.object(api.frappe, "session", SimpleNamespace(user="Administrator")):
			result = api.qwen_chat_send("TEST-SESSION", "what is average order value")

		self.assertEqual(result, {"ok": True, "mode": "front_door"})
		lock_mock.assert_called_once_with("qwen_chat_session::TEST-SESSION", timeout=1)
		handle_mock.assert_called_once_with(
			session_name="TEST-SESSION",
			message="what is average order value",
			user="Administrator",
		)

	def test_qwen_chat_send_returns_busy_error_when_lock_times_out(self):
		with patch("ai_assistant_ui.api._get_qwen_session", return_value=object()), patch(
			"ai_assistant_ui.api.filelock",
			side_effect=LockTimeoutError("busy"),
		), patch("ai_assistant_ui.api.handle_qwen_user_message") as handle_mock:
			result = api.qwen_chat_send("TEST-SESSION", "what is average order value")

		self.assertEqual(
			result,
			{
				"ok": False,
				"error": "Please wait for the current Qwen response to finish before sending another message in this chat.",
			},
		)
		handle_mock.assert_not_called()
