from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List


CONTRACT_TYPE = "qwen_consultant_drilldown_playbook_plan"
CONTRACT_VERSION = "1.0"
REGISTRY_FILE = "consultant_drilldown_playbooks.json"


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


@lru_cache(maxsize=1)
def consultant_drilldown_playbook_registry() -> Dict[str, Any]:
	path = Path(__file__).with_name(REGISTRY_FILE)
	try:
		payload = json.loads(path.read_text(encoding="utf-8"))
	except Exception:
		payload = {}
	if not isinstance(payload, dict):
		return {}
	if _clean_text(payload.get("type")) != "qwen_consultant_drilldown_playbook_registry":
		return {}
	return payload


def _feature_set(evidence_features: Dict[str, Any]) -> set[str]:
	features = set(_clean_list(evidence_features.get("features")))
	for key, value in evidence_features.items():
		if isinstance(value, bool) and value:
			features.add(_clean_text(key))
	return {feature for feature in features if feature}


def _source_matches(playbook: Dict[str, Any], source_signature: Dict[str, Any]) -> bool:
	family_id = _clean_text(source_signature.get("family_id"))
	capability_id = _clean_text(source_signature.get("capability_id"))
	composite_grounding = bool(source_signature.get("composite_grounding"))
	family_ids = set(_clean_list(playbook.get("source_family_ids")))
	capability_ids = set(_clean_list(playbook.get("source_capability_ids")))
	allow_composite = bool(playbook.get("allow_composite_grounding"))
	if not family_ids and not capability_ids and not allow_composite:
		return True
	return bool(
		(family_id and family_id in family_ids)
		or (capability_id and capability_id in capability_ids)
		or (allow_composite and composite_grounding)
	)


def _entity_scope_from_registry(
	*,
	registry: Dict[str, Any],
	source_signature: Dict[str, Any],
	evidence_features: Dict[str, Any],
) -> str:
	scope = _clean_text(evidence_features.get("entity_scope"))
	if scope:
		return scope
	scopes = _clean_dict(registry.get("capability_entity_scopes"))
	return _clean_text(scopes.get(_clean_text(source_signature.get("capability_id"))) or "parties")


def _render_next_action(
	*,
	registry: Dict[str, Any],
	playbook: Dict[str, Any],
	source_signature: Dict[str, Any],
	evidence_features: Dict[str, Any],
) -> Dict[str, Any]:
	action_template = _clean_dict(playbook.get("next_action"))
	action_id = _clean_text(action_template.get("action_id"))
	execution_mode = _clean_text(action_template.get("execution_mode"))
	if not action_id or execution_mode != "current_governed_artifact":
		return {}
	action = {
		"action_id": action_id,
		"execution_mode": execution_mode,
		"playbook_id": _clean_text(playbook.get("playbook_id")),
		"source_family_id": _clean_text(source_signature.get("family_id")),
		"source_report_count": int(source_signature.get("source_report_count") or 0),
	}
	comparison_metrics = _clean_list(action_template.get("comparison_metrics"))
	if comparison_metrics:
		action["comparison_metrics"] = comparison_metrics
	entity_scope = _entity_scope_from_registry(
		registry=registry,
		source_signature=source_signature,
		evidence_features=evidence_features,
	)
	prompts_by_scope = _clean_dict(action_template.get("entity_scope_prompts"))
	if prompts_by_scope:
		action["entity_scope"] = entity_scope
		action["user_prompt"] = _clean_text(prompts_by_scope.get(entity_scope) or prompts_by_scope.get("parties"))
	else:
		action["user_prompt"] = _clean_text(action_template.get("user_prompt"))
	if not _clean_text(action.get("user_prompt")):
		return {}
	return action


def build_consultant_drilldown_playbook_plan(
	*,
	source_signature: Dict[str, Any],
	evidence_features: Dict[str, Any],
) -> Dict[str, Any]:
	"""Select an executable consultant drilldown action from governed evidence features.

	The selector reads source/capability metadata and artifact features only. It
	does not inspect the user's natural-language wording.
	"""

	source = _clean_dict(source_signature)
	features = _feature_set(_clean_dict(evidence_features))
	registry = consultant_drilldown_playbook_registry()
	base = {
		"type": CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"source_family_id": _clean_text(source.get("family_id")),
		"source_capability_id": _clean_text(source.get("capability_id")),
		"source_report_count": int(source.get("source_report_count") or 0),
		"features": sorted(features),
	}
	if not registry:
		return {
			**base,
			"status": "registry_unavailable",
			"can_execute": False,
			"reason": "No governed consultant drilldown playbook registry is available.",
		}
	playbooks = [
		dict(item)
		for item in registry.get("playbooks") or []
		if isinstance(item, dict)
	]
	playbooks.sort(key=lambda item: int(item.get("priority") or 999))
	for playbook in playbooks:
		required_features = set(_clean_list(playbook.get("required_features")))
		if required_features and not required_features.issubset(features):
			continue
		if not _source_matches(playbook, source):
			continue
		next_action = _render_next_action(
			registry=registry,
			playbook=playbook,
			source_signature=source,
			evidence_features=_clean_dict(evidence_features),
		)
		if not next_action:
			continue
		return {
			**base,
			"status": "executable_playbook_available",
			"can_execute": True,
			"playbook_id": _clean_text(playbook.get("playbook_id")),
			"next_action": next_action,
			"reason": "An approved consultant drilldown playbook matches the governed artifact features.",
		}
	return {
		**base,
		"status": "no_executable_playbook",
		"can_execute": False,
		"reason": "No approved consultant drilldown playbook matched the governed artifact features.",
	}
