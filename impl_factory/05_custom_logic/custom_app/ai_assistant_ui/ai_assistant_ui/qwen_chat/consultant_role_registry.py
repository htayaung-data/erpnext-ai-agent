from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List


REGISTRY_TYPE = "qwen_consultant_role_registry"
REGISTRY_FILE = "consultant_role_registry.json"
SAFE_DEFAULT_ROLE = "business_consultant"


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


@lru_cache(maxsize=1)
def consultant_role_registry() -> Dict[str, Any]:
	path = Path(__file__).with_name(REGISTRY_FILE)
	try:
		payload = json.loads(path.read_text(encoding="utf-8"))
	except Exception:
		payload = {}
	if not isinstance(payload, dict):
		return {}
	if _clean_text(payload.get("type")) != REGISTRY_TYPE:
		return {}
	return payload


def consultant_business_role_for_context(
	*,
	family_id: str = "",
	capability_id: str = "",
	semantic_tags: List[str] | None = None,
) -> str:
	"""Resolve consultant role from governed source metadata.

	This lookup is intentionally metadata-owned. It does not inspect user
	message wording.
	"""

	registry = consultant_role_registry()
	default_role = _clean_text(registry.get("default_role")) or SAFE_DEFAULT_ROLE
	capability_roles = _clean_dict(registry.get("capability_roles"))
	role = _clean_text(capability_roles.get(_clean_text(capability_id)))
	if role:
		return role
	family_roles = _clean_dict(registry.get("family_roles"))
	role = _clean_text(family_roles.get(_clean_text(family_id)))
	if role:
		return role
	tag_roles = _clean_dict(registry.get("semantic_tag_roles"))
	for tag in _clean_list(semantic_tags or []):
		role = _clean_text(tag_roles.get(tag))
		if role:
			return role
	return default_role
