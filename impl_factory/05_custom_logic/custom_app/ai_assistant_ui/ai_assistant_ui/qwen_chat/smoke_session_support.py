from __future__ import annotations

from typing import Any, Callable, Dict


def run_phase55_smoke_session(
	title: str,
	runner: Callable[[Any], Dict[str, Any]],
	*,
	frappe_module,
	session_doctype: str,
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
		doc.title = str(title or "Phase 5.5 Smoke").strip() or "Phase 5.5 Smoke"
		doc.insert(ignore_permissions=False)
		# Make the inserted smoke session visible to later save/check-if-latest calls.
		frappe_module.db.commit()
		try:
			return runner(doc)
		finally:
			frappe_module.delete_doc(session_doctype, doc.name, ignore_permissions=False)
			frappe_module.db.commit()
	finally:
		for key, was_present in presence.items():
			if was_present:
				conf[key] = originals.get(key)
			else:
				try:
					conf.pop(key, None)
				except Exception:
					pass


def run_phase6_smoke_session(
	title: str,
	runner: Callable[[Any], Dict[str, Any]],
	*,
	frappe_module,
	session_doctype: str,
) -> Dict[str, Any]:
	compiled_flag_key = "qwen_enable_compiled_first_turn"
	compiled_percent_key = "qwen_compiled_first_turn_rollout_percentage"
	compiled_users_key = "qwen_compiled_first_turn_rollout_users"
	reasoning_flag_key = "qwen_enable_erp_business_reasoning"
	reasoning_percent_key = "qwen_erp_business_reasoning_rollout_percentage"
	reasoning_users_key = "qwen_erp_business_reasoning_rollout_users"
	conf = getattr(frappe_module, "conf", None) or {}
	keys = [
		compiled_flag_key,
		compiled_percent_key,
		compiled_users_key,
		reasoning_flag_key,
		reasoning_percent_key,
		reasoning_users_key,
	]
	originals = {key: conf.get(key) for key in keys}
	presence = {key: key in conf for key in keys}
	try:
		conf[compiled_flag_key] = True
		conf[compiled_percent_key] = 0
		conf[compiled_users_key] = ["Administrator"]
		conf[reasoning_flag_key] = True
		conf[reasoning_percent_key] = 0
		conf[reasoning_users_key] = ["Administrator"]
		doc = frappe_module.new_doc(session_doctype)
		doc.title = str(title or "Phase 6 Smoke").strip() or "Phase 6 Smoke"
		doc.insert(ignore_permissions=False)
		# Make the inserted smoke session visible to later save/check-if-latest calls.
		frappe_module.db.commit()
		try:
			return runner(doc)
		finally:
			frappe_module.delete_doc(session_doctype, doc.name, ignore_permissions=False)
			frappe_module.db.commit()
	finally:
		for key, was_present in presence.items():
			if was_present:
				conf[key] = originals.get(key)
			else:
				try:
					conf.pop(key, None)
				except Exception:
					pass
