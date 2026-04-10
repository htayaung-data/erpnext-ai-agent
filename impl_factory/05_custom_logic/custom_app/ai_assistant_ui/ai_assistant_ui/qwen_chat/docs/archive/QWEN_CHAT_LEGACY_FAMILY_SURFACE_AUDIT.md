# Qwen Chat Legacy Family Surface Audit

Status: current-state audit after semantic-resolution migration wave  
Audience: AI/ML, backend, governance maintainers  
Goal: document where `family_tool_surface` still remains active and where it is no longer allowed

## 1. Audit Result

The semantic-governed routing boundary is now active for these intents:

1. `financial_statement`
2. `inventory_summary`
3. `aging_analysis`
4. `trend_analysis`
5. `ranked_entities`
6. `product_performance`
7. `transaction_listing`

These intents must not re-enter lexical `family_tool_surface` routing.

The remaining legacy-only-or-partial intent is:

1. `financial_summary`

This is the important current architecture fact:

1. semantic-governed intents own governed report routing
2. `family_tool_surface` is now legacy-only
3. legacy-only does not mean bad by itself
4. it means those intents have not yet been migrated into structured semantic resolution

## 2. Current Runtime Usage

### 2.1 `fresh_query_interpreter.py`

Remaining active usage:

1. capability/report fallback for non-semantic intents
2. deterministic family-surface fallback for non-semantic intents only

Current protection:

1. `_semantic_resolution_governs_intent(...)` blocks semantic-governed intents from pre-steering
2. `_allow_deterministic_family_surface_fallback(...)` blocks post-clarify fallback for semantic-governed intents
3. `_deterministic_family_surface_interpretation(...)` itself refuses semantic-governed intents

Implication:

1. runtime family-surface fallback is still present
2. but it is no longer allowed to drive the migrated governed analytic intents

### 2.2 `legacy_runtime_lane.py`

Remaining active usage:

1. legacy runtime still builds family-tool context for the runtime assistant when allowed

Current protection:

1. compiled rollout fallback artifacts now carry `interpretation_intent_class`
2. `_legacy_runtime_family_tool_surface_allowed(...)` disables family-surface context when that fallback identifies a semantic-governed intent

Implication:

1. legacy runtime can still use family-tool context for true legacy intents
2. it no longer uses that context for migrated semantic-governed intents when compiled fallback already established the governed intent

## 3. Support And Probe Usage

These files still reference `family_tool_surface` for validation or audit support:

1. `family_evaluation_support.py`
2. `service.py` wrappers for Phase 4B family-tool-surface probe and smoke

This is acceptable because:

1. those paths are evaluation/support surfaces
2. they are not the authoritative governed routing layer
3. they help us verify legacy behavior while migration is incomplete

## 4. Architectural Judgment

Current state is acceptable and enterprise-grade for this phase because:

1. semantic-governed intents are protected from re-entry into lexical fallback
2. remaining family-surface runtime usage is bounded to non-migrated intents
3. production behavior now follows a clear authority rule instead of competing routing systems

Current state is not the final end state because:

1. `financial_summary`

is only partially migrated

Current clarification:

1. `financial_summary` now has a bounded first-wave semantic runtime slice for normalize-or-clarify behavior
2. unsupported first-wave cases still fall back to the broader non-semantic path
3. this is acceptable because the boundary is explicit and conservative

Current supported clarify coverage includes:

1. no-domain clarification
2. sales-scope clarification
3. focus clarification
4. multi-domain clarification

## 5. Recommended Next Actions

Recommended order:

1. keep `family_tool_surface` unchanged for unsupported `financial_summary` cases until later semantic expansion is approved
2. do not expand lexical fallback to cover new governed domains
3. continue expanding `financial_summary` only through governed semantic/runtime design rather than extending family-surface logic
4. once those migrations exist, retire production family-surface routing and keep it only for probes if still useful

## 6. Enterprise Rule

If a future change touches one of these intents:

1. `financial_statement`
2. `inventory_summary`
3. `aging_analysis`
4. `trend_analysis`
5. `ranked_entities`
6. `product_performance`
7. `transaction_listing`

Then the change must go through:

1. semantic-resolution registry
2. semantic resolver
3. governed compiler path

It must not go through:

1. message-driven `family_tool_surface` refinement
2. deterministic lexical fallback
3. report forcing in legacy runtime
