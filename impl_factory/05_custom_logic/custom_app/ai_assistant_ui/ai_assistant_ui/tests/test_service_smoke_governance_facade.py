from __future__ import annotations

import ast
import sys
import types
import unittest
from pathlib import Path


def _install_fake_frappe() -> None:
	fake_frappe = types.ModuleType("frappe")
	fake_frappe._ = lambda value, *args, **kwargs: value
	fake_frappe.whitelist = lambda *args, **kwargs: (
		args[0] if args and callable(args[0]) else (lambda fn: fn)
	)
	fake_frappe.get_doc = lambda *args, **kwargs: None
	fake_frappe.new_doc = lambda *args, **kwargs: None
	fake_frappe.get_all = lambda *args, **kwargs: []
	fake_frappe.has_permission = lambda *args, **kwargs: True
	fake_frappe.delete_doc = lambda *args, **kwargs: None
	fake_frappe.throw = lambda *args, **kwargs: (_ for _ in ()).throw(
		Exception(args[0] if args else "frappe.throw")
	)
	fake_frappe.session = types.SimpleNamespace(user="qa_ec8f_fake_user")
	fake_frappe.local = types.SimpleNamespace(site="")
	fake_frappe.conf = {}
	fake_frappe.db = types.SimpleNamespace(
		exists=lambda *args, **kwargs: False,
		get_value=lambda *args, **kwargs: None,
		sql=lambda *args, **kwargs: [],
	)
	fake_frappe.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
	fake_frappe.ValidationError = type("ValidationError", (Exception,), {})

	fake_utils = types.ModuleType("frappe.utils")
	fake_utils.now_datetime = lambda: None
	fake_utils.now = lambda: "2026-05-23 00:00:00"
	fake_utils.cint = lambda value=0: int(value or 0)
	fake_utils.flt = lambda value=0, *args, **kwargs: float(value or 0)
	fake_utils.getdate = lambda value=None: value
	fake_utils.today = lambda: "2026-05-23"
	fake_utils.add_days = lambda date, days: date
	fake_frappe.utils = fake_utils

	sys.modules.setdefault("frappe", fake_frappe)
	sys.modules.setdefault("frappe.utils", fake_utils)


_install_fake_frappe()

from ai_assistant_ui.qwen_chat import service
from ai_assistant_ui.qwen_chat import service_smoke_governance_facade as facade


SELECTED_WRAPPERS = (
	"run_phase4_compiled_rollout_smoke",
	"run_phase4_compiled_rollout_governance_selftests",
	"run_phase4_compiled_rollout_monitoring_smoke",
)


class ServiceSmokeGovernanceFacadeTests(unittest.TestCase):
	def _patch_helper(self, helper_name: str, payload: dict):
		original = getattr(facade, helper_name)
		setattr(facade, helper_name, lambda: dict(payload))
		self.addCleanup(setattr, facade, helper_name, original)

	def test_facade_exports_selected_wrappers(self):
		for name in SELECTED_WRAPPERS:
			self.assertTrue(hasattr(facade, name), name)
			self.assertTrue(callable(getattr(facade, name)), name)

	def test_service_keeps_selected_public_wrapper_imports(self):
		for name in SELECTED_WRAPPERS:
			self.assertTrue(hasattr(service, name), name)
			self.assertTrue(callable(getattr(service, name)), name)

	def test_facade_and_service_wrappers_return_identical_payloads(self):
		cases = (
			(
				"_run_phase4_compiled_rollout_smoke_helper",
				"run_phase4_compiled_rollout_smoke",
				{"ok": True, "source": "ec8f-smoke"},
			),
			(
				"_run_phase4_compiled_rollout_governance_selftests_helper",
				"run_phase4_compiled_rollout_governance_selftests",
				{"ok": True, "source": "ec8f-governance"},
			),
			(
				"_run_phase4_compiled_rollout_monitoring_smoke_helper",
				"run_phase4_compiled_rollout_monitoring_smoke",
				{"ok": True, "source": "ec8f-monitoring"},
			),
		)
		for helper_name, wrapper_name, payload in cases:
			with self.subTest(wrapper=wrapper_name):
				self._patch_helper(helper_name, payload)
				self.assertEqual(getattr(facade, wrapper_name)(), payload)
				self.assertEqual(getattr(service, wrapper_name)(), payload)

	def test_public_service_export_inventory_does_not_drop_required_names(self):
		service_path = Path(service.__file__).resolve()
		tree = ast.parse(service_path.read_text(encoding="utf-8"))
		public_functions = {
			node.name
			for node in tree.body
			if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_")
		}
		self.assertGreaterEqual(len(public_functions), 215)
		for name in SELECTED_WRAPPERS:
			self.assertIn(name, public_functions)
		self.assertIn("handle_qwen_user_message", public_functions)
		self.assertTrue(hasattr(service, "QWEN_SESSION_DOCTYPE"))
