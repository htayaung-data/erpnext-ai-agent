# Qwen ERP Phase 3.3B / 3.3C Entity Lookup And Evidence Seam Design

Status: active bounded design note
Date: 2026-04-12
Scope: bounded implementation design for Phase `3.3B` and `3.3C` to remove lexical authority drift from entity-oriented lookup and evidence behavior without introducing a parallel architecture

## 1. Purpose

This note turns the current project-level evaluation into one bounded implementation design.

It exists to answer five practical questions before runtime code changes begin:

1. what exact contract changes should be made
2. what exact metadata changes should be made
3. what exact runtime seams should be touched
4. what recent behavior should be removed or reworked
5. how the change should be verified safely

This note is intentionally narrow.

It does not open a new architecture chapter.

It stays inside the active Phase `3.3` authority-alignment work already defined in:

1. `phase3_entity_lookup_scope/qwen_erp_phase3_3_ranking_projection_and_evidence_contract_design_2026-04-11.md`

## 2. Executive Decision

The next bounded move should be:

1. keep the existing enterprise architecture
2. reuse the current `master_data_lookup`, entity-detail, follow-up, metadata, and validation ecosystem
3. remove customer-specific and phrase-led rescue behavior from shared runtime seams
4. add one missing typed seam for:
   - directory-style entity lookup
   - candidate entity resolution
   - typed handoff into entity-detail/profile behavior

This is not a new parallel subsystem.

It is a bounded seam-completion slice inside the current architecture.

## 3. Why This Belongs In `3.3B / 3.3C`

This work belongs in the current roadmap for two reasons.

### 3.1 `3.3B` Ownership

`3.3B` already owns:

1. entity-detail evidence request contract cleanup
2. removal of raw-message business branching from governed entity-detail rendering

The current customer-focused rescue drift is part of that same authority problem.

### 3.2 `3.3C` Ownership

`3.3C` already owns:

1. metadata and semantic completion for missing typed distinctions

The current lookup/detail gap exists because some distinctions are still not represented cleanly enough in typed contracts and metadata.

So the current problem is not outside the roadmap.

It is an active Phase `3.3` seam.

## 4. Problem Statemen

The assistant already performs well for:

1. governed KPI asks
2. governed composite ranking asks
3. operational list/detail/status asks
4. customer-credit detail asks
5. typed follow-up continuity inside proven families

The current weak area is a narrower class of valid ERP read questions such as:

1. `give me some customer names`
2. `give me some supplier names`
3. `give me some item names`
4. `do we have a customer similar to Ko Nay Lin Mobile`
5. `tell me details about Ko Nay Lin Mobile Center`

These asks are:

1. in-domain
2. governed read-only in nature
3. adjacent to entity detail and master data
4. not yet represented by a fully clean typed seam across supported grains

Because that seam is incomplete, recent runtime behavior drifted into:

1. phrase-led detection
2. customer-specific rescue logic
3. customer-specific fuzzy resolution imported into shared seams

That drift must now be removed.

## 5. Design Goal

The design goal is not:

1. answer every unseen ERP question
2. create a generic free-form fallback
3. build one giant universal entity resolver

The design goal is:

1. make valid lookup-style ERP requests representable in typed state
2. let metadata govern what grains and projections are approved
3. let runtime execute only approved lookup/detail paths
4. fail closed when the entity grain or supported mode is not yet approved

## 6. Contract Changes

The contract changes should stay as small as possible while still eliminating lexical rescue.

### 6.1 Extend `FreshQueryInterpretationContract`

Current `FreshQueryInterpretationContract` already carries:

1. `intent_class`
2. candidate capabilities and reports
3. requested dimensions and metrics
4. requested time scope
5. extracted slots

For `master_data_lookup`, add one typed request-shape block through `extracted_slots` first rather than creating a brand-new top-level contract family.

Required typed additions:

1. `lookup_mode`
   - allowed values:
     - `directory_list`
     - `candidate_resolution`
     - `profile_target`
2. `lookup_projection`
   - allowed values:
     - `names_only`
     - `standard_directory`
     - `selected_columns`
3. `lookup_search_text`
   - free text extracted by the semantic layer for candidate resolution
4. `lookup_limit`
   - bounded integer, defaulted by metadata when omitted
5. `lookup_filters`
   - typed filter object only for approved filterable fields

Reason:

1. this keeps the front-door / fresh-query seam consisten
2. it avoids inventing a second top-level interpretation channel
3. it lets the compiler/runtime remain the contract consumer

### 6.2 Extend `EntityDetailEvidenceRequestContract`

`EntityDetailEvidenceRequestContract` already exists and should be reused.

Current shape is close, but too focused on evidence rendering only.

Add the following fields:

1. `question_shape`
   - allowed values such as:
     - `boolean_status`
     - `scalar_amount`
     - `scalar_ratio`
     - `date_lookup`
     - `dimension_lookup`
     - `profile_request`
2. `value_mode`
   - allowed values such as:
     - `current_value`
     - `first_value`
     - `dominant_value`
3. `resolved_entity_ref`
   - object with:
     - `entity_type`
     - `entity_key`
     - `entity_label`
     - `resolution_status`
     - `resolution_source`
4. `profile_sections`
   - list of approved sections when the ask is profile-oriented

Reason:

1. the renderer should consume typed resolved meaning
2. the renderer should not rediscover target entity or question shape from raw English tex

### 6.3 Add One Small Shared Resolution Contrac

Add a small dedicated typed contract for shared entity resolution:

`EntityReferenceResolutionContract`

Required fields:

1. `request_id`
2. `entity_grain`
3. `lookup_mode`
4. `search_text`
5. `resolution_status`
   - `resolved`
   - `ambiguous`
   - `not_found`
   - `unsupported_grain`
   - `unsupported_mode`
6. `candidate_entities`
7. `resolved_entity`
8. `reason`

Reason:

1. this isolates entity resolution from customer KPI helpers
2. this gives a typed handoff point between lookup and detail/profile behavior
3. it is small enough to fit the current ecosystem

This is the only new contract recommended in this slice.

## 7. Metadata Changes

The metadata changes should be explicit and narrow.

### 7.1 Extend `semantic_resolution_registry.json`

Do not turn this registry into a phrase whitelist.

Use it to define only the typed distinctions that matter.

Required additions:

1. `lookup_mode` slo
   - `directory_list`
   - `candidate_resolution`
   - `profile_target`
2. `lookup_projection` slo
   - `names_only`
   - `standard_directory`
   - `selected_columns`
3. family-resolution rules for approved lookup grains only

Initial approved rule shape:

1. customer directory / resolution / profile targe
2. supplier directory / resolution / profile target only if approved report or direct-query authority is already confirmed
3. item directory / resolution / profile target only if approved report or direct-query authority is already confirmed

Important:

1. do not activate grains speculatively
2. activation must follow approved governed source authority

### 7.2 Extend `capability_registry.json`

Do not add generic unfenced capabilities.

Required additions or normalization:

1. keep `customer_master_read`
2. add parallel capabilities only where approved source authority exists:
   - `supplier_master_read`
   - `item_master_read`
3. each capability must declare:
   - report names
   - supported intent classes
   - ontology concepts
   - dimensions
   - fresh-query defaults for `master_data_lookup`

### 7.3 Extend `report_registry.json`

For each approved master-data report or direct-query path, define:

1. filterable identity fields
2. allowed discovery fields
3. supported intent classes
4. approved follow-up modes

This keeps the execution side governed.

### 7.4 Add Metadata For Entity Resolution Policy

Do **not** embed fuzzy-match policy in customer-only Python code.

Add a small metadata home for entity reference policy.

Recommended new file:

1. `entity_reference_policy_registry.json`

Required fields per approved grain:

1. `entity_grain`
2. `doctype`
3. `identity_field`
4. `display_field`
5. `search_fields`
6. `allowed_lookup_modes`
7. `default_projection`
8. `default_limit`
9. `match_policy`
   - `exact_only`
   - `exact_then_alias`
   - `exact_then_governed_fuzzy`
10. `clarify_on_ambiguity`
11. `activation_state`

Reason:

1. this keeps grain-specific identity/search behavior metadata-owned
2. it avoids hardcoded customer-first lookup order in runtime code

### 7.5 Complete Existing `3.3C` Evidence Distinctions

The active `3.3C` design note is still correct and should remain part of this slice.

Required semantic/evidence distinctions:

1. tenure basis
2. first-activity date basis
3. overdue question shape
4. credit-balance question shape
5. dominant aging bucket dimension
6. outstanding vs total-due distinction

These should be completed together with the lookup seam, not separately.

Reason:

1. both problems are the same authority problem
2. both require typed business distinctions to replace lexical rescue

## 8. Runtime Seams To Touch

The implementation must stay narrowly scoped.

### 8.1 Primary Runtime Files To Change

These are the intended primary seams:

1. `contracts.py`
   - contract additions only
2. `semantic_resolution_registry.py`
   - registry validation for new slots / rules
3. `fresh_query_interpreter.py`
   - consume typed `master_data_lookup` request shape
   - stop customer-only rescue behavior
4. `entity_detail.py`
   - stop phrase-led target extraction as authority
   - consume typed resolved entity reference
5. `boundary_support.py`
   - consume typed evidence contract fields only
6. `metadata.py`
   - load new metadata registry if added

### 8.2 Supporting Runtime Files That May Need Bounded Edits

Only if required:

1. `clarification_resolution.py`
2. `followup_interpreter.py`
3. `family_validator.py`
4. `service_diagnostics.py`

### 8.3 File To Stop Using As Shared Lookup Authority

Reduce shared routing dependence on:

1. `customer_kpi_runtime_support.py`

Customer-specific helper logic can remain for customer KPI execution itself.

But entity lookup and resolution should not use that module as the shared authority seam.

## 9. Behavior To Remove Or Rework

These are the specific runtime shapes that should be removed or replaced.

### 9.1 Remove Phrase-Led Detail Ownership

Replace as primary authority:

1. `_explicit_detail_request(...)`
2. `_detail_target_from_message(...)`
3. `_resolve_named_entity_from_detail_request(...)`

These may survive only as bounded audit or legacy fallback scaffolding if explicitly governed and temporary.

They must not remain the main business-meaning path.

### 9.2 Remove Customer-Specific Fresh Query Rescue

Replace:

1. `_augment_customer_master_scope_filters_from_message(...)`

with:

1. one shared typed entity-reference augmentation step driven by metadata and typed interpretation

### 9.3 Remove Customer-Specific Shared Resolution Ownership

Replace broad routing dependence on:

1. `resolve_customer_scope_from_message(...)`

with:

1. metadata-driven shared entity reference resolution

Customer-specific helper usage may remain only inside customer KPI execution where that helper belongs.

### 9.4 Replace Output-Text Assertions With Contract Assertions

Update new and modified tests so they assert primarily on:

1. contract state
2. resolution state
3. selected capability/report/family
4. fail-closed behavior

Output text checks should be secondary and narrow.

## 10. Verification Plan

The verification must prove seam behavior, not just one prompt.

### 10.1 Contract Tests Firs

Add or update deterministic tests for:

1. `master_data_lookup` interpretation with `lookup_mode`
2. entity reference resolution contract states
3. evidence request contract fields
4. semantic registry validation for new slots/rules

### 10.2 Runtime Contract / Consumer Tests

Add bounded tests for:

1. directory lookup on approved grain
2. candidate resolution on approved grain
3. handoff from resolved entity into entity detail
4. fail-closed behavior for unsupported grain
5. fail-closed behavior for ambiguous entity resolution

### 10.3 Regression Protection

Explicitly revalidate:

1. ranking projection continuity
2. customer KPI execution
3. customer detail evidence behavior
4. subject-switch ranking behavior
5. unsupported request boundary behavior

### 10.4 Manual UAT Only After Code-Level Green

Recommended manual prompts after implementation:

1. `give me some customer names`
2. `do you have customer name similar to Ko Nay Lin Mobile`
3. `tell me details about Ko Nay Lin Mobile Center`
4. `give me some supplier names`
5. `give me some item names`
6. `what is this customer's tenure`
7. `by first sales order`

## 11. Out Of Scope For This Slice

This slice must not widen into:

1. all master-data domains
2. multilingual redesign
3. advisory reasoning
4. write flows
5. broad service orchestration refactor
6. generic fuzzy search across all ERP doctypes

The activation should stay limited to approved grains with approved governed read authority.

## 12. Stop Rule

This bounded slice is complete when:

1. valid lookup-style ERP asks no longer depend on raw phrase rescue
2. shared entity lookup/resolution behavior is metadata-owned and typed
3. entity-detail rendering consumes typed evidence request state only
4. customer-specific lookup rescue is removed from shared seams
5. existing KPI/composite/detail behavior remains stable
6. unsupported lookup asks still fail closed honestly

## 13. Final Implementation Posture

The right posture for this slice is:

1. contract firs
2. metadata second
3. narrow runtime consumer changes third
4. deterministic verification before browser checks

Do not treat the latest prompt examples as the architecture.

Treat them as evidence that the current typed seam is incomplete.

The implementation should therefore complete the seam, not patch the prompts.
