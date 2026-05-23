from __future__ import annotations

import importlib
from typing import Any, Dict


def _lazy_symbol(module_name: str, symbol_name: str):
	def _call(*args, **kwargs):
		module = importlib.import_module(module_name)
		return getattr(module, symbol_name)(*args, **kwargs)

	return _call


_run_phase4_compiled_rollout_governance_selftests_helper = _lazy_symbol(
	"ai_assistant_ui.qwen_chat.probes.service_diagnostics",
	"run_phase4_compiled_rollout_governance_selftests",
)
_run_phase4_compiled_rollout_monitoring_smoke_helper = _lazy_symbol(
	"ai_assistant_ui.qwen_chat.probes.service_diagnostics",
	"run_phase4_compiled_rollout_monitoring_smoke",
)
_run_phase4_compiled_rollout_smoke_helper = _lazy_symbol(
	"ai_assistant_ui.qwen_chat.probes.service_diagnostics",
	"run_phase4_compiled_rollout_smoke",
)


def run_phase4_compiled_rollout_smoke() -> Dict[str, Any]:
	return _run_phase4_compiled_rollout_smoke_helper()


def run_phase4_compiled_rollout_governance_selftests() -> Dict[str, Any]:
	return _run_phase4_compiled_rollout_governance_selftests_helper()


def run_phase4_compiled_rollout_monitoring_smoke() -> Dict[str, Any]:
	return _run_phase4_compiled_rollout_monitoring_smoke_helper()
