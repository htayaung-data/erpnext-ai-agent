from __future__ import annotations

import re
from typing import Any, Dict, List, Set, Tuple

from ai_assistant_ui.qwen_chat.business_definition_formula_registry import RegistryValidationResult
from ai_assistant_ui.qwen_chat.metadata import (
	get_capability_spec,
	get_entity_reference_policy_spec,
	get_family_scope_compatibility_spec,
	get_governed_scope_spec,
	get_report_spec,
	list_entity_reference_policy_specs,
	load_family_scope_compatibility_registry,
	load_governed_scope_registry,
	load_scope_clarification_registry,
	load_scope_owner_registry,
    load_scope_projection_registry,
	entity_grain_display_label,
)


def _as_str_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    items: List[str] = []
    for item in value:
        text = str(item or "").strip()
        if text:
            items.append(text)
    return items


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _normalized_scope_token(value: Any) -> str:
	text = _clean_text(value).lower()
	if not text:
		return ""
	return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def _scope_items() -> List[Dict[str, Any]]:
	return [
		item
		for item in (load_governed_scope_registry().get("scopes") or [])
		if isinstance(item, dict)
	]


def _scope_authority(scope_spec: Dict[str, Any]) -> Dict[str, Any]:
	authority = scope_spec.get("approved_source_authority")
	return authority if isinstance(authority, dict) else {}


def _scope_is_active_report_approved(scope_spec: Dict[str, Any]) -> bool:
	authority = _scope_authority(scope_spec)
	return (
		_clean_text(scope_spec.get("status")) == "active"
		and _clean_text(authority.get("authority_status")) == "approved"
		and _clean_text(authority.get("source_kind")) == "report"
	)


def _scope_canonical_tokens(scope_spec: Dict[str, Any]) -> List[str]:
	return list(
		dict.fromkeys(
			[
				token
				for token in [
					_clean_text(scope_spec.get("scope_id")),
					_clean_text(scope_spec.get("scope_label")),
					*_as_str_list(scope_spec.get("canonical_grains")),
					*_as_str_list(scope_spec.get("canonical_alias_groups")),
				]
				if token
			]
		)
	)


def canonical_scope_aliases(scope_id: str) -> List[str]:
	scope_spec = governed_scope_spec(scope_id)
	if not scope_spec:
		return []
	return _scope_canonical_tokens(scope_spec)


def _scope_matches_alias(scope_spec: Dict[str, Any], alias: str) -> bool:
	normalized_alias = _normalized_scope_token(alias)
	if not normalized_alias:
		return False
	return any(
		_normalized_scope_token(token) == normalized_alias
		for token in _scope_canonical_tokens(scope_spec)
	)


def _canonical_policy_entity_grain_for_scope(scope_spec: Dict[str, Any]) -> str:
	for grain in _as_str_list(scope_spec.get("canonical_grains")):
		if get_entity_reference_policy_spec(grain):
			return grain
	return ""


def _scope_ids(items: List[Dict[str, Any]]) -> Set[str]:
    return {
        str(item.get("scope_id") or "").strip()
        for item in items
        if str(item.get("scope_id") or "").strip()
    }


def _family_ids(data: Dict[str, Any]) -> Set[str]:
    return set(_as_str_list(data.get("allowed_family_ids")))


_LISTING_VIEW_SCOPE_MAP: Dict[str, str] = {}


def scope_id_for_canonical_alias(alias: str, *, scope_class: str = "") -> str:
	clean_scope_class = _clean_text(scope_class)
	for item in _scope_items():
		if clean_scope_class and _clean_text(item.get("scope_class")) != clean_scope_class:
			continue
		if _scope_matches_alias(item, alias):
			return _clean_text(item.get("scope_id"))
	return ""


def scope_id_for_entity_grain(entity_grain: str) -> str:
	return scope_id_for_canonical_alias(entity_grain, scope_class="master_data")


def canonical_master_data_entity_grain(entity_grain: str) -> str:
	scope_id = scope_id_for_entity_grain(entity_grain)
	if not scope_id:
		return _clean_text(entity_grain)
	return _canonical_policy_entity_grain_for_scope(governed_scope_spec(scope_id)) or _clean_text(entity_grain)


def canonical_scope_aliases_for_entity_grain(entity_grain: str) -> List[str]:
	scope_id = scope_id_for_entity_grain(entity_grain)
	if not scope_id:
		return []
	return canonical_scope_aliases(scope_id)


def scope_id_for_listing_view(listing_view: str) -> str:
	clean_listing_view = _clean_text(listing_view)
	if not clean_listing_view:
		return ""
	mapped_scope_id = _clean_text(_LISTING_VIEW_SCOPE_MAP.get(clean_listing_view))
	if mapped_scope_id:
		return mapped_scope_id
	scope_spec = governed_scope_spec(clean_listing_view)
	if _scope_is_active_report_approved(scope_spec):
		return clean_listing_view
	report_scope_id = scope_id_for_report_name(clean_listing_view)
	if report_scope_id:
		return report_scope_id
	alias_scope_id = scope_id_for_canonical_alias(clean_listing_view)
	alias_scope_spec = governed_scope_spec(alias_scope_id)
	if _scope_is_active_report_approved(alias_scope_spec):
		return alias_scope_id
	return ""


def _pluralize_scope_label_word(word: str) -> str:
	text = str(word or "").strip()
	if not text:
		return ""
	lower = text.lower()
	if lower.endswith("y") and len(text) > 1 and lower[-2] not in {"a", "e", "i", "o", "u"}:
		return f"{text[:-1]}ies"
	if lower.endswith(("s", "x", "z", "ch", "sh")):
		return f"{text}es"
	return f"{text}s"


def governed_scope_display_label(scope_id: str, *, plural: bool = False, lowercase: bool = False) -> str:
	scope_spec = governed_scope_spec(scope_id)
	label = str(scope_spec.get("scope_label") or "").strip()
	if not label:
		label = str(scope_id or "").strip().replace("_", " ")
	if plural and label:
		parts = label.split()
		if parts:
			parts[-1] = _pluralize_scope_label_word(parts[-1])
			label = " ".join(parts)
	return label.lower() if lowercase else label


def listing_view_display_label(listing_view: str, *, plural: bool = True, lowercase: bool = True) -> str:
	scope_id = scope_id_for_listing_view(listing_view)
	if scope_id:
		return governed_scope_display_label(scope_id, plural=plural, lowercase=lowercase)
	label = str(listing_view or "").strip().replace("_", " ")
	if plural and label:
		parts = label.split()
		if parts:
			parts[-1] = _pluralize_scope_label_word(parts[-1])
			label = " ".join(parts)
	return label.lower() if lowercase else label


def scope_id_for_report_name(report_name: str) -> str:
	clean_report_name = str(report_name or "").strip().lower()
	if not clean_report_name:
		return ""
	for item in _scope_items():
		authority = _scope_authority(item)
		authority_report_name = str(authority.get("report_name") or "").strip().lower()
		if authority_report_name == clean_report_name:
			return str(item.get("scope_id") or "").strip()
	return ""


def listing_view_for_report_name(report_name: str) -> str:
	scope_id = scope_id_for_report_name(report_name)
	if not scope_id:
		return ""
	scope_spec = governed_scope_spec(scope_id)
	if (
		_scope_is_active_report_approved(scope_spec)
		and _clean_text(scope_spec.get("scope_class")) != "master_data"
	):
		return scope_id
	return ""


def entity_grain_for_report_name(report_name: str) -> str:
	scope_id = scope_id_for_report_name(report_name)
	if not scope_id:
		return ""
	scope_spec = governed_scope_spec(scope_id)
	canonical_grains = [
		str(value or "").strip()
		for value in (scope_spec.get("canonical_grains") or [])
		if str(value or "").strip()
	]
	for grain in canonical_grains:
		if get_entity_reference_policy_spec(grain):
			return grain
	return ""


def governed_scope_family_policy(scope_id: str, family_id: str) -> Dict[str, Any]:
	if not str(scope_id or "").strip() or not str(family_id or "").strip():
		return {}
	return get_family_scope_compatibility_spec(scope_id, family_id)


def governed_scope_spec(scope_id: str) -> Dict[str, Any]:
	if not str(scope_id or "").strip():
		return {}
	return get_governed_scope_spec(scope_id)


def master_data_scope_activation(entity_grain: str) -> Dict[str, Any]:
	grain = canonical_master_data_entity_grain(entity_grain)
	if not grain:
		return {}
	policy = get_entity_reference_policy_spec(grain)
	if not policy or str(policy.get("activation_state") or "").strip() != "active":
		return {}
	scope_id = str(policy.get("scope_id") or "").strip() or scope_id_for_entity_grain(grain)
	scope_spec = governed_scope_spec(scope_id)
	if str(scope_spec.get("status") or "").strip() != "active":
		return {}
	authority = (
		scope_spec.get("approved_source_authority")
		if isinstance(scope_spec.get("approved_source_authority"), dict)
		else {}
	)
	if str(authority.get("authority_status") or "").strip() != "approved":
		return {}
	if str(authority.get("source_kind") or "").strip() != "report":
		return {}
	report_name = str(authority.get("report_name") or "").strip()
	capability_id = str(authority.get("capability_id") or "").strip()
	if not report_name or not capability_id:
		return {}
	family_policy = governed_scope_family_policy(scope_id, "master_data_lookup")
	if str(family_policy.get("compatibility_level") or "").strip() != "full_consumption":
		return {}
	allowed_lookup_modes = [
		mode
		for mode in _as_str_list(family_policy.get("allowed_modes"))
		if mode in set(_as_str_list(policy.get("allowed_lookup_modes")))
	]
	if not allowed_lookup_modes:
		return {}
	return {
		"scope_id": scope_id,
		"scope_label": str(scope_spec.get("scope_label") or "").strip(),
		"entity_grain": grain,
		"capability_id": capability_id,
		"report_name": report_name,
		"allowed_lookup_modes": allowed_lookup_modes,
		"default_projection": str(policy.get("default_projection") or "").strip(),
		"default_limit": int(max(0, policy.get("default_limit") or 0)),
		"followup_compatibility": str(family_policy.get("followup_compatibility") or "").strip(),
		"entity_label": entity_grain_display_label(grain, plural=False) or grain,
		"entity_plural_label": entity_grain_display_label(grain, plural=True) or f"{grain}s",
	}


def list_active_master_data_scope_activations(*, request_mode: str = "") -> List[Dict[str, Any]]:
	required_mode = str(request_mode or "").strip()
	out: List[Dict[str, Any]] = []
	for policy in list_entity_reference_policy_specs():
		grain = str(policy.get("entity_grain") or "").strip()
		if not grain:
			continue
		activation = master_data_scope_activation(grain)
		if not activation:
			continue
		if required_mode and required_mode not in _as_str_list(activation.get("allowed_lookup_modes")):
			continue
		out.append(activation)
	return out


def master_data_lookup_mode_allowed(entity_grain: str, lookup_mode: str) -> bool:
	mode = str(lookup_mode or "").strip()
	if not mode:
		return True
	activation = master_data_scope_activation(entity_grain)
	if not activation:
		return False
	return mode in _as_str_list(activation.get("allowed_lookup_modes"))


def validate_governed_scope_registry(
    payload: Dict[str, Any] | None = None,
) -> RegistryValidationResult:
    data = payload if isinstance(payload, dict) else load_governed_scope_registry()
    errors: List[str] = []
    warnings: List[str] = []

    if str(data.get("contract_version") or "").strip() != "1.0":
        errors.append("contract_version must be '1.0'.")

    allowed_scope_classes = set(_as_str_list(data.get("allowed_scope_classes")))
    allowed_statuses = set(_as_str_list(data.get("allowed_statuses")))
    allowed_support_states = set(_as_str_list(data.get("allowed_support_states")))
    allowed_source_kinds = set(_as_str_list(data.get("allowed_source_kinds")))
    allowed_authority_statuses = set(_as_str_list(data.get("allowed_authority_statuses")))

    if not allowed_scope_classes:
        errors.append("allowed_scope_classes must be a non-empty list.")
    if not allowed_statuses:
        errors.append("allowed_statuses must be a non-empty list.")
    if not allowed_support_states:
        errors.append("allowed_support_states must be a non-empty list.")
    if not allowed_source_kinds:
        errors.append("allowed_source_kinds must be a non-empty list.")
    if not allowed_authority_statuses:
        errors.append("allowed_authority_statuses must be a non-empty list.")

    scopes = data.get("scopes")
    if not isinstance(scopes, list) or not scopes:
        errors.append("scopes must be a non-empty list.")
        scopes = []

    seen_scope_ids: Set[str] = set()
    status_counts: Dict[str, int] = {}
    for idx, item in enumerate(scopes):
        if not isinstance(item, dict):
            errors.append(f"scopes[{idx}] must be an object.")
            continue
        scope_id = str(item.get("scope_id") or "").strip()
        if not scope_id:
            errors.append(f"scopes[{idx}].scope_id must be a non-empty string.")
            continue
        if scope_id in seen_scope_ids:
            errors.append(f"scopes contains duplicate scope_id '{scope_id}'.")
        seen_scope_ids.add(scope_id)

        for field_name in ("scope_label", "primary_owner_family", "notes"):
            if not str(item.get(field_name) or "").strip():
                errors.append(f"scopes[{idx}].{field_name} must be a non-empty string.")

        scope_class = str(item.get("scope_class") or "").strip()
        if scope_class not in allowed_scope_classes:
            errors.append(f"scopes[{idx}].scope_class must be one of {sorted(allowed_scope_classes)}.")

        status = str(item.get("status") or "").strip()
        if status not in allowed_statuses:
            errors.append(f"scopes[{idx}].status must be one of {sorted(allowed_statuses)}.")
        else:
            status_counts[status] = status_counts.get(status, 0) + 1

        support_state = str(item.get("support_state") or "").strip()
        if support_state not in allowed_support_states:
            errors.append(f"scopes[{idx}].support_state must be one of {sorted(allowed_support_states)}.")

        canonical_grains = _as_str_list(item.get("canonical_grains"))
        if not canonical_grains:
            errors.append(f"scopes[{idx}].canonical_grains must be a non-empty list.")

        canonical_alias_groups = _as_str_list(item.get("canonical_alias_groups"))
        if not canonical_alias_groups:
            errors.append(f"scopes[{idx}].canonical_alias_groups must be a non-empty list.")

        authority = item.get("approved_source_authority")
        if not isinstance(authority, dict):
            errors.append(f"scopes[{idx}].approved_source_authority must be an object.")
            continue

        source_kind = str(authority.get("source_kind") or "").strip()
        authority_status = str(authority.get("authority_status") or "").strip()
        report_name = str(authority.get("report_name") or "").strip()
        capability_id = str(authority.get("capability_id") or "").strip()

        if source_kind not in allowed_source_kinds:
            errors.append(f"scopes[{idx}].approved_source_authority.source_kind must be one of {sorted(allowed_source_kinds)}.")
        if authority_status not in allowed_authority_statuses:
            errors.append(f"scopes[{idx}].approved_source_authority.authority_status must be one of {sorted(allowed_authority_statuses)}.")

        if status == "active" and source_kind == "pending":
            errors.append(f"scopes[{idx}] is active but still uses pending source authority.")
        if support_state == "runtime_real_frontdoor_inactive" and status == "active":
            errors.append(f"scopes[{idx}] cannot be active while support_state is runtime_real_frontdoor_inactive.")

        if source_kind == "report":
            if not report_name:
                errors.append(f"scopes[{idx}] must declare approved_source_authority.report_name for report-backed scope.")
            elif not get_report_spec(report_name):
                errors.append(f"scopes[{idx}] references unknown report '{report_name}'.")

            if capability_id and not get_capability_spec(capability_id):
                errors.append(f"scopes[{idx}] references unknown capability_id '{capability_id}'.")

            if report_name and capability_id and get_capability_spec(capability_id):
                declared_reports = _as_str_list(get_capability_spec(capability_id).get("report_names"))
                if report_name not in declared_reports:
                    errors.append(f"scopes[{idx}] report '{report_name}' is not declared by capability '{capability_id}'.")

    return RegistryValidationResult(
        registry_name="governed_scope_registry",
        status="pass" if not errors else "fail",
        errors=errors,
        warnings=warnings,
        stats={
            "scope_count": len([item for item in scopes if isinstance(item, dict)]),
            "status_counts": status_counts,
        },
    )


def validate_scope_owner_registry(
    payload: Dict[str, Any] | None = None,
) -> RegistryValidationResult:
    data = payload if isinstance(payload, dict) else load_scope_owner_registry()
    errors: List[str] = []
    warnings: List[str] = []

    if str(data.get("contract_version") or "").strip() != "1.0":
        errors.append("contract_version must be '1.0'.")

    allowed_family_ids = _family_ids(data)
    if not allowed_family_ids:
        errors.append("allowed_family_ids must be a non-empty list.")

    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        errors.append("entries must be a non-empty list.")
        entries = []

    seen_scope_ids: Set[str] = set()
    for idx, item in enumerate(entries):
        if not isinstance(item, dict):
            errors.append(f"entries[{idx}] must be an object.")
            continue
        scope_id = str(item.get("scope_id") or "").strip()
        if not scope_id:
            errors.append(f"entries[{idx}].scope_id must be a non-empty string.")
            continue
        if scope_id in seen_scope_ids:
            errors.append(f"entries contains duplicate scope_id '{scope_id}'.")
        seen_scope_ids.add(scope_id)

        primary_owner = str(item.get("primary_owner_family") or "").strip()
        if primary_owner not in allowed_family_ids:
            errors.append(f"entries[{idx}].primary_owner_family must be one of {sorted(allowed_family_ids)}.")

        secondary = _as_str_list(item.get("secondary_compatible_families"))
        prohibited = _as_str_list(item.get("prohibited_families"))
        for family_id in secondary + prohibited:
            if family_id not in allowed_family_ids:
                errors.append(f"entries[{idx}] references unknown family_id '{family_id}'.")

        overlap = sorted(set(secondary).intersection(prohibited))
        if overlap:
            errors.append(f"entries[{idx}] secondary_compatible_families and prohibited_families overlap: {', '.join(overlap)}.")

        for field_name in ("ownership_reason", "policy_notes"):
            if not str(item.get(field_name) or "").strip():
                errors.append(f"entries[{idx}].{field_name} must be a non-empty string.")

    return RegistryValidationResult(
        registry_name="scope_owner_registry",
        status="pass" if not errors else "fail",
        errors=errors,
        warnings=warnings,
        stats={"entry_count": len([item for item in entries if isinstance(item, dict)])},
    )


def validate_family_scope_compatibility_registry(
    payload: Dict[str, Any] | None = None,
) -> RegistryValidationResult:
    data = payload if isinstance(payload, dict) else load_family_scope_compatibility_registry()
    errors: List[str] = []
    warnings: List[str] = []

    if str(data.get("contract_version") or "").strip() != "1.0":
        errors.append("contract_version must be '1.0'.")

    allowed_family_ids = _family_ids(data)
    allowed_levels = set(_as_str_list(data.get("allowed_compatibility_levels")))
    allowed_modes = set(_as_str_list(data.get("allowed_modes")))
    allowed_followup = set(_as_str_list(data.get("allowed_followup_compatibility")))

    if not allowed_family_ids:
        errors.append("allowed_family_ids must be a non-empty list.")
    if not allowed_levels:
        errors.append("allowed_compatibility_levels must be a non-empty list.")
    if not allowed_modes:
        errors.append("allowed_modes must be a non-empty list.")
    if not allowed_followup:
        errors.append("allowed_followup_compatibility must be a non-empty list.")

    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        errors.append("entries must be a non-empty list.")
        entries = []

    seen_pairs: Set[Tuple[str, str]] = set()
    level_counts: Dict[str, int] = {}
    for idx, item in enumerate(entries):
        if not isinstance(item, dict):
            errors.append(f"entries[{idx}] must be an object.")
            continue
        scope_id = str(item.get("scope_id") or "").strip()
        family_id = str(item.get("family_id") or "").strip()
        if not scope_id:
            errors.append(f"entries[{idx}].scope_id must be a non-empty string.")
            continue
        if family_id not in allowed_family_ids:
            errors.append(f"entries[{idx}].family_id must be one of {sorted(allowed_family_ids)}.")
        pair = (scope_id, family_id)
        if pair in seen_pairs:
            errors.append(f"entries contains duplicate scope/family pair '{scope_id}/{family_id}'.")
        seen_pairs.add(pair)

        compatibility_level = str(item.get("compatibility_level") or "").strip()
        if compatibility_level not in allowed_levels:
            errors.append(f"entries[{idx}].compatibility_level must be one of {sorted(allowed_levels)}.")
        else:
            level_counts[compatibility_level] = level_counts.get(compatibility_level, 0) + 1

        entry_modes = _as_str_list(item.get("allowed_modes"))
        for mode in entry_modes:
            if mode not in allowed_modes:
                errors.append(f"entries[{idx}] references unsupported mode '{mode}'.")

        if compatibility_level == "not_allowed" and entry_modes:
            errors.append(f"entries[{idx}] must not declare allowed_modes when compatibility_level is not_allowed.")
        if compatibility_level != "not_allowed" and not entry_modes:
            errors.append(f"entries[{idx}] must declare allowed_modes when compatibility_level is '{compatibility_level}'.")

        followup_compatibility = str(item.get("followup_compatibility") or "").strip()
        if followup_compatibility not in allowed_followup:
            errors.append(f"entries[{idx}].followup_compatibility must be one of {sorted(allowed_followup)}.")

        blocked_reason = str(item.get("blocked_reason") or "").strip()
        if compatibility_level == "not_allowed" and not blocked_reason:
            errors.append(f"entries[{idx}] must provide blocked_reason when compatibility_level is not_allowed.")
        if compatibility_level != "not_allowed" and blocked_reason:
            warnings.append(f"entries[{idx}] provides blocked_reason even though compatibility_level is {compatibility_level}.")

        if not str(item.get("policy_notes") or "").strip():
            errors.append(f"entries[{idx}].policy_notes must be a non-empty string.")

    return RegistryValidationResult(
        registry_name="family_scope_compatibility_registry",
        status="pass" if not errors else "fail",
        errors=errors,
        warnings=warnings,
        stats={
            "entry_count": len([item for item in entries if isinstance(item, dict)]),
            "compatibility_level_counts": level_counts,
        },
    )


def validate_scope_projection_registry(
    payload: Dict[str, Any] | None = None,
) -> RegistryValidationResult:
    data = payload if isinstance(payload, dict) else load_scope_projection_registry()
    errors: List[str] = []
    warnings: List[str] = []

    if str(data.get("contract_version") or "").strip() != "1.0":
        errors.append("contract_version must be '1.0'.")

    allowed_family_ids = _family_ids(data)
    allowed_shapes = set(_as_str_list(data.get("allowed_default_projection_shapes")))
    if not allowed_family_ids:
        errors.append("allowed_family_ids must be a non-empty list.")
    if not allowed_shapes:
        errors.append("allowed_default_projection_shapes must be a non-empty list.")

    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        errors.append("entries must be a non-empty list.")
        entries = []

    seen_keys: Set[Tuple[str, str, str]] = set()
    for idx, item in enumerate(entries):
        if not isinstance(item, dict):
            errors.append(f"entries[{idx}] must be an object.")
            continue
        scope_id = str(item.get("scope_id") or "").strip()
        family_id = str(item.get("family_id") or "").strip()
        projection_group_id = str(item.get("projection_group_id") or "").strip()

        if not scope_id:
            errors.append(f"entries[{idx}].scope_id must be a non-empty string.")
            continue
        if family_id not in allowed_family_ids:
            errors.append(f"entries[{idx}].family_id must be one of {sorted(allowed_family_ids)}.")
        if not projection_group_id:
            errors.append(f"entries[{idx}].projection_group_id must be a non-empty string.")

        key = (scope_id, family_id, projection_group_id)
        if key in seen_keys:
            errors.append(f"entries contains duplicate projection entry '{scope_id}/{family_id}/{projection_group_id}'.")
        seen_keys.add(key)

        default_projection_shape = str(item.get("default_projection_shape") or "").strip()
        if default_projection_shape not in allowed_shapes:
            errors.append(f"entries[{idx}].default_projection_shape must be one of {sorted(allowed_shapes)}.")

        if not str(item.get("projection_notes") or "").strip():
            errors.append(f"entries[{idx}].projection_notes must be a non-empty string.")

    return RegistryValidationResult(
        registry_name="scope_projection_registry",
        status="pass" if not errors else "fail",
        errors=errors,
        warnings=warnings,
        stats={"entry_count": len([item for item in entries if isinstance(item, dict)])},
    )


def validate_scope_clarification_registry(
    payload: Dict[str, Any] | None = None,
) -> RegistryValidationResult:
    data = payload if isinstance(payload, dict) else load_scope_clarification_registry()
    errors: List[str] = []
    warnings: List[str] = []

    if str(data.get("contract_version") or "").strip() not in {"1.0", "1.2"}:
        errors.append("contract_version must be '1.0' or '1.2'.")

    allowed_family_ids = _family_ids(data)
    allowed_ambiguity_classes = set(_as_str_list(data.get("allowed_ambiguity_classes")))
    allowed_template_groups = set(_as_str_list(data.get("allowed_template_groups")))
    if not allowed_family_ids:
        errors.append("allowed_family_ids must be a non-empty list.")
    if not allowed_ambiguity_classes:
        errors.append("allowed_ambiguity_classes must be a non-empty list.")
    if not allowed_template_groups:
        errors.append("allowed_template_groups must be a non-empty list.")

    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        errors.append("entries must be a non-empty list.")
        entries = []

    seen_pairs: Set[Tuple[str, str]] = set()
    for idx, item in enumerate(entries):
        if not isinstance(item, dict):
            errors.append(f"entries[{idx}] must be an object.")
            continue
        scope_id = str(item.get("scope_id") or "").strip()
        family_id = str(item.get("family_id") or "").strip()
        if not scope_id:
            errors.append(f"entries[{idx}].scope_id must be a non-empty string.")
            continue
        if family_id not in allowed_family_ids:
            errors.append(f"entries[{idx}].family_id must be one of {sorted(allowed_family_ids)}.")

        pair = (scope_id, family_id)
        if pair in seen_pairs:
            errors.append(f"entries contains duplicate clarification entry '{scope_id}/{family_id}'.")
        seen_pairs.add(pair)

        ambiguity_classes = _as_str_list(item.get("supported_ambiguity_classes"))
        if not ambiguity_classes:
            errors.append(f"entries[{idx}].supported_ambiguity_classes must be a non-empty list.")
        for ambiguity_class in ambiguity_classes:
            if ambiguity_class not in allowed_ambiguity_classes:
                errors.append(f"entries[{idx}] references unsupported ambiguity class '{ambiguity_class}'.")

        clarification_template_group = str(item.get("clarification_template_group") or "").strip()
        if clarification_template_group not in allowed_template_groups:
            errors.append(f"entries[{idx}].clarification_template_group must be one of {sorted(allowed_template_groups)}.")

        for field_name in ("required_basis_slots", "required_event_slots"):
            if not isinstance(item.get(field_name), list):
                errors.append(f"entries[{idx}].{field_name} must be a list.")

        if not str(item.get("clarification_notes") or "").strip():
            errors.append(f"entries[{idx}].clarification_notes must be a non-empty string.")

    return RegistryValidationResult(
        registry_name="scope_clarification_registry",
        status="pass" if not errors else "fail",
        errors=errors,
        warnings=warnings,
        stats={"entry_count": len([item for item in entries if isinstance(item, dict)])},
    )


def validate_governed_scope_access_model() -> RegistryValidationResult:
    results = [
        validate_governed_scope_registry(),
        validate_scope_owner_registry(),
        validate_family_scope_compatibility_registry(),
        validate_scope_projection_registry(),
        validate_scope_clarification_registry(),
    ]
    errors: List[str] = []
    warnings: List[str] = []
    for result in results:
        errors.extend([f"{result.registry_name}: {message}" for message in result.errors])
        warnings.extend([f"{result.registry_name}: {message}" for message in result.warnings])

    scope_data = load_governed_scope_registry()
    owner_data = load_scope_owner_registry()
    compatibility_data = load_family_scope_compatibility_registry()
    projection_data = load_scope_projection_registry()
    clarification_data = load_scope_clarification_registry()

    scope_list = scope_data.get("scopes") if isinstance(scope_data.get("scopes"), list) else []
    owner_list = owner_data.get("entries") if isinstance(owner_data.get("entries"), list) else []
    compatibility_list = compatibility_data.get("entries") if isinstance(compatibility_data.get("entries"), list) else []
    projection_list = projection_data.get("entries") if isinstance(projection_data.get("entries"), list) else []
    clarification_list = clarification_data.get("entries") if isinstance(clarification_data.get("entries"), list) else []

    known_scope_ids = _scope_ids(scope_list)
    owner_scope_ids = _scope_ids(owner_list)

    compatibility_family_ids = _family_ids(compatibility_data)
    if compatibility_family_ids != _family_ids(owner_data):
        errors.append("allowed_family_ids must match between scope_owner_registry and family_scope_compatibility_registry.")
    if compatibility_family_ids != _family_ids(projection_data):
        errors.append("allowed_family_ids must match between scope_projection_registry and family_scope_compatibility_registry.")
    if compatibility_family_ids != _family_ids(clarification_data):
        errors.append("allowed_family_ids must match between scope_clarification_registry and family_scope_compatibility_registry.")

    compatibility_pairs: Dict[Tuple[str, str], Dict[str, Any]] = {}
    compatible_families_by_scope: Dict[str, List[Dict[str, Any]]] = {}
    for item in compatibility_list:
        if not isinstance(item, dict):
            continue
        scope_id = str(item.get("scope_id") or "").strip()
        family_id = str(item.get("family_id") or "").strip()
        if scope_id and scope_id not in known_scope_ids:
            errors.append(f"family_scope_compatibility_registry references unknown scope '{scope_id}'.")
        if family_id and family_id not in compatibility_family_ids:
            errors.append(f"family_scope_compatibility_registry references unknown family '{family_id}'.")
        compatibility_pairs[(scope_id, family_id)] = item
        compatible_families_by_scope.setdefault(scope_id, []).append(item)

    projection_pairs: Set[Tuple[str, str]] = set()
    for item in projection_list:
        if not isinstance(item, dict):
            continue
        scope_id = str(item.get("scope_id") or "").strip()
        family_id = str(item.get("family_id") or "").strip()
        if scope_id and scope_id not in known_scope_ids:
            errors.append(f"scope_projection_registry references unknown scope '{scope_id}'.")
        if (scope_id, family_id) not in compatibility_pairs:
            errors.append(f"scope_projection_registry requires a matching compatibility entry for '{scope_id}/{family_id}'.")
        projection_pairs.add((scope_id, family_id))

    clarification_pairs: Set[Tuple[str, str]] = set()
    for item in clarification_list:
        if not isinstance(item, dict):
            continue
        scope_id = str(item.get("scope_id") or "").strip()
        family_id = str(item.get("family_id") or "").strip()
        if scope_id and scope_id not in known_scope_ids:
            errors.append(f"scope_clarification_registry references unknown scope '{scope_id}'.")
        if (scope_id, family_id) not in compatibility_pairs:
            errors.append(f"scope_clarification_registry requires a matching compatibility entry for '{scope_id}/{family_id}'.")
        clarification_pairs.add((scope_id, family_id))

    owner_map = {
        str(item.get("scope_id") or "").strip(): item
        for item in owner_list
        if isinstance(item, dict)
    }

    active_scope_count = 0
    for item in scope_list:
        if not isinstance(item, dict):
            continue
        scope_id = str(item.get("scope_id") or "").strip()
        if not scope_id:
            continue

        if scope_id not in owner_scope_ids:
            errors.append(f"Scope '{scope_id}' does not have a matching scope_owner_registry entry.")
            continue

        primary_owner = str(item.get("primary_owner_family") or "").strip()
        owner_spec = owner_map.get(scope_id) or {}
        if str(owner_spec.get("primary_owner_family") or "").strip() != primary_owner:
            errors.append(f"Scope '{scope_id}' has mismatched primary owner between scope registry and owner registry.")

        if str(item.get("status") or "").strip() != "active":
            continue

        active_scope_count += 1
        compatible_entries = [
            entry
            for entry in compatible_families_by_scope.get(scope_id, [])
            if str(entry.get("compatibility_level") or "").strip() != "not_allowed"
        ]
        if not compatible_entries:
            errors.append(f"Active scope '{scope_id}' must declare at least one compatible family.")
            continue

        if not any(str(entry.get("family_id") or "").strip() == primary_owner for entry in compatible_entries):
            errors.append(f"Active scope '{scope_id}' must include its primary owner family in compatible families.")

        has_projection = False
        for entry in compatible_entries:
            family_id = str(entry.get("family_id") or "").strip()
            compatibility_level = str(entry.get("compatibility_level") or "").strip()
            pair = (scope_id, family_id)
            if pair not in clarification_pairs:
                errors.append(f"Active scope '{scope_id}' missing clarification coverage for family '{family_id}'.")
            if compatibility_level in {"full_consumption", "projection_only"}:
                if pair not in projection_pairs:
                    errors.append(f"Active scope '{scope_id}' missing projection policy for family '{family_id}'.")
                else:
                    has_projection = True

        if not has_projection:
            errors.append(f"Active scope '{scope_id}' must have at least one projection policy entry.")

    return RegistryValidationResult(
        registry_name="governed_scope_access_model",
        status="pass" if not errors else "fail",
        errors=errors,
        warnings=warnings,
        stats={
            "validated_registry_count": len(results),
            "active_scope_count": active_scope_count,
            "known_scope_count": len(known_scope_ids),
        },
    )
