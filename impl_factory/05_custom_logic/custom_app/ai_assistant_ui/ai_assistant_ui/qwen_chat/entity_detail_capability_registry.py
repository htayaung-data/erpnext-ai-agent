from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict


REGISTRY_TYPE = "qwen_entity_detail_capability_binding_registry"
REGISTRY_FILE = "entity_detail_capability_bindings.json"


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _normalize_key(value: Any) -> str:
	return _clean_text(value).lower()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


@lru_cache(maxsize=1)
def entity_detail_capability_binding_registry() -> Dict[str, Any]:
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


def capability_id_for_entity_detail(entity_type: str) -> str:
	"""Resolve entity-detail capability from governed binding metadata."""

	bindings = _clean_dict(entity_detail_capability_binding_registry().get("entity_capability_bindings"))
	return _clean_text(bindings.get(_normalize_key(entity_type)))
