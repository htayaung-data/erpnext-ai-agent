# Qwen ERP Governed Scope Coverage Round 1 Phase 2 Runtime Seam Mapping

Status: active research note  
Date: 2026-04-12  
Scope: Round 1 Phase 2 runtime seam mapping for `customer`, `supplier`, and `item/product`

## 1. Purpose

This note records the runtime seam mapping for Round 1.

Round 1 scope:

1. customer
2. supplier
3. item or product

Phase 1 already established what is declared in metadata.

Phase 2 answers the next question:

1. how that metadata is actually consumed in runtime
2. which seams are shared and governed
3. which seams are still customer-weighted
4. where supplier and item/product stop in the current path

This is still research.
It does not yet claim behavior closure.

## 2. Evidence Sources

The mapping was based on direct inspection of these runtime modules:

1. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py`
2. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_reference_resolution.py`
3. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_detail.py`
4. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/followup_interpreter.py`
5. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_adapters.py`
6. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_rendering.py`
7. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/metadata.py`
8. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py`
9. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_customer_master_lookup_contracts.py`
10. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_entity_detail_contracts.py`
11. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_followup_interpreter_contracts.py`

## 3. High-Level Runtime Finding

The Round 1 runtime is neither fully generic nor fully hardcoded.

It is mixed.

The cleanest summary is:

1. metadata access and entity-reference resolution are already shared seams
2. fresh-query augmentation is shared, but only activates when metadata exists for the grain
3. end-to-end master-data artifact adaptation and rendering are currently customer-specific
4. entity-detail drilldown still contains direct grain branching
5. follow-up breakout logic is more shared than rendering, but still depends on the available artifact families

This means the current system is not a fake customer-only patch from top to bottom.

But it is also not yet fully generalized for Round 1 grains.

## 4. Shared Runtime Seams

### 4.1 Metadata Access Layer Is Shared

`metadata.py` exposes generic registry accessors such as:

1. `get_entity_reference_policy_spec(entity_grain)`
2. `list_entity_reference_policy_specs()`
3. `list_semantic_resolution_slot_definitions()`
4. `list_semantic_resolution_alias_entries(slot_name)`

Important conclusion:

1. registry loading itself is not customer-specific
2. runtime can already consume grain-specific policy from metadata in a shared way

### 4.2 Entity Reference Resolution Is Shared And Policy-Driven

`entity_reference_resolution.py` is one of the cleanest shared seams.

It already provides:

1. `infer_lookup_mode_from_message(...)`
2. `infer_lookup_projection_from_message(...)`
3. `infer_master_data_lookup_slots(...)`
4. `resolve_entity_reference_from_message(...)`

Important runtime pattern:

1. it loads the entity reference policy by grain
2. it checks activation state
3. it checks allowed lookup modes
4. it uses policy fields such as:
   - doctype
   - identity field
   - display field
   - search fields
   - match policy

Important conclusion:

1. this seam is already generic in design
2. if supplier/item policies existed, this resolver could consume them without needing a new customer-only branch here

### 4.3 Fresh Query Augmentation Is Shared, But Gated By Active Policy

`fresh_query_interpreter.py` contains `_augment_master_data_lookup_interpretation_from_message(...)`.

That function already does the right kind of shared thing:

1. runs only for `master_data_lookup`
2. reads `entity_grain` from extracted slots
3. loads policy by grain
4. skips augmentation if the policy is not active
5. infers lookup slots through the shared entity-reference module
6. runs governed entity resolution for:
   - `candidate_resolution`
   - `profile_target`

Important conclusion:

1. this seam is already reasonably enterprise-shaped
2. the main limiter here is active policy coverage, not obvious customer-only logic in this function itself

### 4.4 Deterministic Surface Interpretation Is Rule-Driven

`fresh_query_interpreter.py` also contains `_deterministic_family_surface_interpretation(...)`.

That path:

1. scans governed family-resolution rules
2. allows deterministic fallback only when the metadata signature is unique
3. builds interpretation from the selected rule
4. then passes through the shared master-data augmentation step

Important conclusion:

1. deterministic fresh-query fallback is metadata-driven
2. customer works here because there is one unique `master_customer_directory` rule
3. supplier/item do not work in the same seam because the equivalent rules are not present

This is a good example of:

1. shared runtime
2. uneven metadata activation

not a pure code hardcode.

## 5. Customer-Weighted Runtime Seams

### 5.1 Family Adaptation For Master Lookup Is Customer-Specific

`family_adapters.py` currently has a dedicated `_build_customer_master_artifact(...)` path and a dispatch branch for:

1. `customer_master_list`

No equivalent runtime artifact builders were found for:

1. supplier master list
2. item master list
3. product master list

Important conclusion:

1. even if supplier/item metadata were added later, this runtime seam is not yet generalized for parallel master-data families
2. current end-to-end lookup artifact adaptation is customer-scoped

### 5.2 Family Rendering For Master Lookup Is Customer-Specific

`family_rendering.py` currently has:

1. `_customer_master_blocks(...)`
2. a family dispatch branch for `customer_master_list`

That renderer also contains typed handling for:

1. names-only rendering
2. candidate-resolution rendering
3. customer table projection

No equivalent supplier/item master renderers were found.

Important conclusion:

1. current master-data rendering is customer-specific
2. this is one of the strongest runtime asymmetries in Round 1

### 5.3 Entity Detail Named-Entity Resolution Still Branches By Grain

`entity_detail.py` contains `_resolve_named_entity_from_detail_request(...)`.

That function currently:

1. checks Customer directly
2. checks Supplier directly
3. checks Item directly
4. calls governed entity-reference resolution only for customer partial-name matching

Important conclusion:

1. this is not the desired end-state
2. it is one of the clearest remaining grain-branching seams
3. it mixes shared governed resolution with direct grain branches in one function

This is a real Phase 2 finding and should be treated as architectural debt, not hidden.

## 6. Detail Handoff And Deictic Continuity

### 6.1 Artifact Candidate Extraction Is Partially Shared

`entity_detail.py` contains `_artifact_entity_candidates(...)`.

It already supports extracting entity candidates from multiple families:

1. `transaction_listing`
2. `aging`
3. `ranking_analytics`
4. `product_profitability`
5. `customer_master_list`

Important conclusion:

1. artifact-based drilldown continuity is broader than customer-only
2. but the specific direct master-data lane is currently richer for customer because only `customer_master_list` exists there

### 6.2 Customer Master Artifacts Are Explicitly Wired Into Deictic Detail

Inside `_artifact_entity_candidates(...)`, the `customer_master_list` family explicitly:

1. emits customer entity candidates from `customer_rows`
2. emits the resolved customer from `entity_reference_resolution`
3. adds alias support like `that customer`

Important conclusion:

1. the recent customer master detail handoff is not accidental
2. it is explicitly wired
3. there is no equivalent supplier/item master artifact path because those artifact families do not exist yet

### 6.3 Follow-Up Breakout Logic Is Shared And Better Than Rendering

`followup_interpreter.py` contains `_entity_reference_breakout_signal(...)`.

That function is relatively shared:

1. it detects entity-navigation style follow-ups from an `entity_detail` artifact
2. it uses lookup-mode inference
3. it reads `entity_grain` slot values from the message
4. it checks message domains and context domains
5. it already treats `product` specially in domain detection for breakout

Important conclusion:

1. the system already knows how to break out of stale entity detail context for a new navigation ask
2. this breakout logic is more generalized than the actual master-data rendering lane
3. therefore some failures are not context-isolation failures
4. they are downstream activation failures after the breakout happens

## 7. Item/Product Runtime Unevenness

A real runtime translation seam exists between `item` and `product`.

Examples:

1. follow-up subject alias logic maps `item` to `product`
2. `product_profitability` artifact candidates emit `item`
3. semantic slots may carry `item`
4. ranking and business language often use `product`

Important conclusion:

1. the runtime already contains translation helpers for this seam
2. but the naming is still uneven enough that it should be treated as a real runtime complexity point
3. this is not yet proof of a defect by itself
4. it is a real factor in future generalization work

## 8. Test Surface Findings

The current regression surface is also customer-weighted.

### 8.1 Customer Master Lookup Has Direct Contract Tests

`test_customer_master_lookup_contracts.py` directly asserts:

1. deterministic customer directory interpretation
2. customer lookup slot inference
3. customer entity-reference resolution
4. customer master family rendering
5. customer candidate-resolution rendering

### 8.2 Follow-Up Breakout Has Limited Non-Customer Coverage

`test_followup_interpreter_contracts.py` includes:

1. customer-resolution breakout from customer detail context
2. supplier directory breakout from customer detail context
3. grounded deictic customer follow-up staying in context

Important conclusion:

1. breakout intent is already tested for supplier
2. end-to-end supplier directory execution is not proven by equivalent family/rendering tests

### 8.3 Entity Detail Tests Still Lean Customer-Heavy

`test_entity_detail_contracts.py` includes strong customer detail cases and customer name resolution cases.

It does not provide equivalent direct master-data lookup proof for:

1. supplier master navigation
2. item master navigation

Important conclusion:

1. current test evidence matches the runtime reality
2. customer has the strongest proof slice
3. supplier/item are not yet proven through the same full path

## 9. Round 1 Phase 2 Classification Matrix

| Runtime seam | Shared / grain-specific | Customer | Supplier | Item/Product | Phase 2 reading |
| --- | --- | --- | --- | --- | --- |
| Metadata policy access | Shared | Yes | Yes if policy exists | Yes if policy exists | Generic seam |
| Entity reference resolution | Shared | Active through policy | Inactive because no active policy | Inactive because no active policy | Generic seam gated by metadata |
| Fresh-query master lookup augmentation | Shared | Active | Stops early without active policy | Stops early without active policy | Generic seam gated by metadata |
| Deterministic family-surface fallback | Shared rule engine | Active through unique rule | No direct rule | No direct rule | Rule-driven, not hardcoded |
| Master-data family adaptation | Grain-specific today | Active | Not present | Not present | Customer-weighted runtime |
| Master-data family rendering | Grain-specific today | Active | Not present | Not present | Customer-weighted runtime |
| Explicit named-entity detail resolution | Mixed | Direct branch plus governed fuzzy | Direct branch only | Direct branch only | Non-ideal mixed seam |
| Artifact-based deictic detail handoff | Partially shared | Richest via customer master | Present via aging/document contexts only | Present via ranking/product profitability only | Shared but uneven |
| Follow-up breakout from stale entity detail | Shared | Yes | Yes at breakout level | Partial via domain logic | More generalized than execution lane |

## 10. Phase 2 Conclusions

Round 1 Phase 2 establishes these facts:

1. the project already has some genuinely shared runtime seams
2. the cleanest shared seam is entity-reference resolution
3. fresh-query augmentation is also shared in structure
4. customer works end to end because customer has both metadata activation and customer-specific downstream family adaptation/rendering
5. supplier and item/product do not fail only because the model cannot understand them
6. supplier and item/product also fail because the current direct master-data execution lane is not yet generalized for them
7. entity-detail resolution still contains direct grain branching and is not yet fully enterprise-clean
8. follow-up breakout logic is ahead of the direct master-data execution lane in terms of generality

## 11. What This Phase Does Not Yet Claim

This note does not yet claim:

1. whether the current live behavior always matches the mapped seams
2. whether supplier/item have hidden governed source routes that could be activated with metadata only
3. whether a future supplier/item expansion should reuse the customer master lane shape exactly or generalize the family layer first

Those belong to Phase 3 behavior truthing and then Phase 4 gap classification.

## 12. Next Step

Next step:

1. Round 1, Phase 3
2. behavior truthing for customer, supplier, and item/product

Phase 3 should verify:

1. where the mapped runtime seams behave as expected
2. where breakout succeeds but execution still stops
3. whether any supplier/item path is stronger in live/runtime truth than it appears from static seam mapping
