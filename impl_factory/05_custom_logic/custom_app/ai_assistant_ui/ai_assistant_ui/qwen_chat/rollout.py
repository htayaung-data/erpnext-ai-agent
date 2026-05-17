from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List

import frappe


def _conf_get(key: str, default: Any = None) -> Any:
	try:
		return (getattr(frappe, "conf", None) or {}).get(key, default)
	except Exception:
		return default


def _conf_string_list(key: str) -> List[str]:
	raw = _conf_get(key, [])
	if isinstance(raw, (list, tuple, set)):
		return [str(item or "").strip() for item in raw if str(item or "").strip()]
	if isinstance(raw, str):
		return [
			part
			for part in [str(item or "").strip() for item in re.split(r"[,\n;]+", raw)]
			if part
		]
	return []


def _rollout_percentage(key: str) -> float:
	raw = _conf_get(key, None)
	if raw is None:
		return 100.0
	if isinstance(raw, str) and not str(raw).strip():
		return 100.0
	try:
		return max(0.0, min(100.0, float(raw)))
	except Exception:
		return 100.0


def _rollout_allow_users(key: str) -> List[str]:
	return list(dict.fromkeys(_conf_string_list(key)))


def _rollout_bucket(*, seed_prefix: str, session_name: str, user: str, site_name: str) -> float:
	seed = f"{seed_prefix}{str(site_name or '').strip()}::{str(user or '').strip()}::{str(session_name or '').strip()}"
	digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
	bucket_basis_points = int(digest[:8], 16) % 10_000
	return round(bucket_basis_points / 100.0, 2)


def _rollout_decision(*, enabled: bool, rollout_percentage: float, allow_users: List[str], canonical_user: str, bucket: float) -> Dict[str, Any]:
	if not enabled:
		return {
			"enabled": False,
			"reason": "master_disabled",
			"rollout_percentage": rollout_percentage,
			"rollout_bucket": bucket,
			"allow_users": allow_users,
		}
	if canonical_user and canonical_user in allow_users:
		return {
			"enabled": True,
			"reason": "allow_user",
			"rollout_percentage": rollout_percentage,
			"rollout_bucket": bucket,
			"allow_users": allow_users,
		}
	if rollout_percentage <= 0.0:
		return {
			"enabled": False,
			"reason": "percentage_zero",
			"rollout_percentage": rollout_percentage,
			"rollout_bucket": bucket,
			"allow_users": allow_users,
		}
	if rollout_percentage >= 100.0:
		return {
			"enabled": True,
			"reason": "percentage_full",
			"rollout_percentage": rollout_percentage,
			"rollout_bucket": bucket,
			"allow_users": allow_users,
		}
	return {
		"enabled": bucket < rollout_percentage,
		"reason": "percentage_canary",
		"rollout_percentage": rollout_percentage,
		"rollout_bucket": bucket,
		"allow_users": allow_users,
	}


def _compiled_first_turn_rollout_enabled() -> bool:
	try:
		return bool((getattr(frappe, "conf", None) or {}).get("qwen_enable_compiled_first_turn", False))
	except Exception:
		return False


def _compiled_first_turn_rollout_percentage() -> float:
	return _rollout_percentage("qwen_compiled_first_turn_rollout_percentage")


def _compiled_first_turn_rollout_allow_users() -> List[str]:
	return _rollout_allow_users("qwen_compiled_first_turn_rollout_users")


def _compiled_first_turn_rollout_bucket(*, session_name: str, user: str, site_name: str) -> float:
	return _rollout_bucket(
		seed_prefix="",
		session_name=session_name,
		user=user,
		site_name=site_name,
	)


def _compiled_first_turn_rollout_decision(
	*,
	session_name: str,
	user: str,
	site_name: str,
) -> Dict[str, Any]:
	return _rollout_decision(
		enabled=_compiled_first_turn_rollout_enabled(),
		rollout_percentage=_compiled_first_turn_rollout_percentage(),
		allow_users=_compiled_first_turn_rollout_allow_users(),
		canonical_user=str(user or "").strip(),
		bucket=_compiled_first_turn_rollout_bucket(
			session_name=session_name,
			user=user,
			site_name=site_name,
		),
	)


def get_compiled_first_turn_rollout_status(
	session_name: str = "phase4-rollout-sample",
	user: str = "Administrator",
	site_name: str = "",
) -> Dict[str, Any]:
	decision = _compiled_first_turn_rollout_decision(
		session_name=str(session_name or "").strip(),
		user=str(user or "").strip(),
		site_name=str(site_name or "").strip(),
	)
	return {
		"master_enabled": _compiled_first_turn_rollout_enabled(),
		"rollout_percentage": _compiled_first_turn_rollout_percentage(),
		"allow_users": _compiled_first_turn_rollout_allow_users(),
		"sample_decision": decision,
	}


def _erp_business_reasoning_rollout_enabled() -> bool:
	try:
		return bool((getattr(frappe, "conf", None) or {}).get("qwen_enable_erp_business_reasoning", False))
	except Exception:
		return False


def _erp_business_reasoning_rollout_percentage() -> float:
	return _rollout_percentage("qwen_erp_business_reasoning_rollout_percentage")


def _erp_business_reasoning_rollout_allow_users() -> List[str]:
	return _rollout_allow_users("qwen_erp_business_reasoning_rollout_users")


def _erp_business_reasoning_rollout_bucket(*, session_name: str, user: str, site_name: str) -> float:
	return _rollout_bucket(
		seed_prefix="reasoning::",
		session_name=session_name,
		user=user,
		site_name=site_name,
	)


def _erp_business_reasoning_rollout_decision(
	*,
	session_name: str,
	user: str,
	site_name: str,
) -> Dict[str, Any]:
	return _rollout_decision(
		enabled=_erp_business_reasoning_rollout_enabled(),
		rollout_percentage=_erp_business_reasoning_rollout_percentage(),
		allow_users=_erp_business_reasoning_rollout_allow_users(),
		canonical_user=str(user or "").strip(),
		bucket=_erp_business_reasoning_rollout_bucket(
			session_name=session_name,
			user=user,
			site_name=site_name,
		),
	)


def get_erp_business_reasoning_rollout_status(
	session_name: str = "phase6-rollout-sample",
	user: str = "Administrator",
	site_name: str = "",
) -> Dict[str, Any]:
	decision = _erp_business_reasoning_rollout_decision(
		session_name=str(session_name or "").strip(),
		user=str(user or "").strip(),
		site_name=str(site_name or "").strip(),
	)
	return {
		"master_enabled": _erp_business_reasoning_rollout_enabled(),
		"rollout_percentage": _erp_business_reasoning_rollout_percentage(),
		"allow_users": _erp_business_reasoning_rollout_allow_users(),
		"sample_decision": decision,
	}
