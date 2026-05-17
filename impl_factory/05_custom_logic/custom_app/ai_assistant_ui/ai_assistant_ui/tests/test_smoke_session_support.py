import unittest
from types import SimpleNamespace

from ai_assistant_ui.qwen_chat.smoke_session_support import (
	run_phase55_smoke_session,
	run_phase6_smoke_session,
)


class _FakeDoc:
	def __init__(self):
		self.name = "TEST-SESSION-0001"
		self.title = ""
		self.insert_calls = []

	def insert(self, *, ignore_permissions=False):
		self.insert_calls.append(ignore_permissions)


class _FakeDB:
	def __init__(self):
		self.commit_count = 0

	def commit(self):
		self.commit_count += 1


class _FakeFrappeModule:
	def __init__(self, conf=None):
		self.conf = dict(conf or {})
		self.db = _FakeDB()
		self.created_docs = []
		self.deleted_docs = []
		self.clear_cache_count = 0

	def new_doc(self, doctype):
		doc = _FakeDoc()
		self.created_docs.append((doctype, doc))
		return doc

	def delete_doc(self, doctype, name, *, ignore_permissions=False):
		self.deleted_docs.append((doctype, name, ignore_permissions))

	def clear_cache(self):
		self.clear_cache_count += 1


class TestSmokeSessionSupport(unittest.TestCase):
	def test_phase55_session_commits_create_and_delete_and_restores_conf(self):
		frappe_module = _FakeFrappeModule(
			{
				"qwen_enable_compiled_first_turn": False,
				"qwen_compiled_first_turn_rollout_percentage": 50,
				"qwen_compiled_first_turn_rollout_users": ["someone"],
			}
		)

		result = run_phase55_smoke_session(
			"Phase 5.5 Unit Smoke",
			lambda doc: {"ok": True, "doc_name": doc.name},
			frappe_module=frappe_module,
			session_doctype="Qwen Chat Session",
		)

		self.assertEqual(result["ok"], True)
		self.assertEqual(frappe_module.db.commit_count, 2)
		self.assertEqual(
			frappe_module.deleted_docs,
			[("Qwen Chat Session", "TEST-SESSION-0001", False)],
		)
		self.assertEqual(frappe_module.conf["qwen_enable_compiled_first_turn"], False)
		self.assertEqual(frappe_module.conf["qwen_compiled_first_turn_rollout_percentage"], 50)
		self.assertEqual(frappe_module.conf["qwen_compiled_first_turn_rollout_users"], ["someone"])

	def test_phase55_session_still_deletes_and_restores_conf_on_runner_error(self):
		frappe_module = _FakeFrappeModule()

		def _runner(_doc):
			raise RuntimeError("boom")

		with self.assertRaisesRegex(RuntimeError, "boom"):
			run_phase55_smoke_session(
				"Phase 5.5 Unit Smoke",
				_runner,
				frappe_module=frappe_module,
				session_doctype="Qwen Chat Session",
			)

		self.assertEqual(frappe_module.db.commit_count, 2)
		self.assertEqual(
			frappe_module.deleted_docs,
			[("Qwen Chat Session", "TEST-SESSION-0001", False)],
		)
		self.assertNotIn("qwen_enable_compiled_first_turn", frappe_module.conf)
		self.assertNotIn("qwen_compiled_first_turn_rollout_percentage", frappe_module.conf)
		self.assertNotIn("qwen_compiled_first_turn_rollout_users", frappe_module.conf)

	def test_phase6_session_commits_create_and_delete_and_restores_all_flags(self):
		frappe_module = _FakeFrappeModule(
			{
				"qwen_enable_compiled_first_turn": False,
				"qwen_compiled_first_turn_rollout_percentage": 50,
				"qwen_compiled_first_turn_rollout_users": ["compiled-user"],
				"qwen_enable_erp_business_reasoning": False,
				"qwen_erp_business_reasoning_rollout_percentage": 25,
				"qwen_erp_business_reasoning_rollout_users": ["reasoning-user"],
			}
		)

		result = run_phase6_smoke_session(
			"Phase 6 Unit Smoke",
			lambda doc: {"ok": True, "doc_name": doc.name},
			frappe_module=frappe_module,
			session_doctype="Qwen Chat Session",
		)

		self.assertEqual(result["ok"], True)
		self.assertEqual(frappe_module.db.commit_count, 3)
		self.assertEqual(frappe_module.clear_cache_count, 2)
		self.assertEqual(
			frappe_module.deleted_docs,
			[("Qwen Chat Session", "TEST-SESSION-0001", False)],
		)
		self.assertEqual(frappe_module.conf["qwen_enable_compiled_first_turn"], False)
		self.assertEqual(frappe_module.conf["qwen_compiled_first_turn_rollout_percentage"], 50)
		self.assertEqual(frappe_module.conf["qwen_compiled_first_turn_rollout_users"], ["compiled-user"])
		self.assertEqual(frappe_module.conf["qwen_enable_erp_business_reasoning"], False)
		self.assertEqual(frappe_module.conf["qwen_erp_business_reasoning_rollout_percentage"], 25)
		self.assertEqual(frappe_module.conf["qwen_erp_business_reasoning_rollout_users"], ["reasoning-user"])
