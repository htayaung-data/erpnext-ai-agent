# Qwen ERP Governed Scope Coverage Round 3 Phase 3 Behavior Truthing

Status: active research note  
Date: 2026-04-13  
Scope: Round 3 Phase 3 behavior truthing for the alignment targets mapped in Round 3 Phases 1 and 2

## 1. Purpose

Round 3 Phase 1 established the declared metadata shape.

Round 3 Phase 2 established the runtime seam shape.

Round 3 Phase 3 now answers the practical behavior question:

1. which Round 3 alignment targets are proven by executed tests
2. which ones are proven narrow by direct runtime behavior
3. which ones are proven misaligned between metadata and runtime
4. which ones remain only partially supported
5. which ones are strong enough to reuse as enterprise seams later

This phase is still bounded truthing.

It is not yet the implementation phase.

## 2. Evidence Basis

This note is based on:

1. [qwen_erp_governed_scope_coverage_round3_phase1_frontdoor_inventory_2026-04-13.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/phase3_entity_lookup_scope/qwen_erp_governed_scope_coverage_round3_phase1_frontdoor_inventory_2026-04-13.md)
2. [qwen_erp_governed_scope_coverage_round3_phase2_runtime_seam_mapping_2026-04-13.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/phase3_entity_lookup_scope/qwen_erp_governed_scope_coverage_round3_phase2_runtime_seam_mapping_2026-04-13.md)
3. targeted unit-test execution in:
   1. [test_customer_master_lookup_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_customer_master_lookup_contracts.py)
   2. [test_entity_detail_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_entity_detail_contracts.py)
   3. [test_semantic_resolution_registry.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_semantic_resolution_registry.py)
4. direct runtime scripts against:
   1. [entity_reference_resolution.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_reference_resolution.py)
   2. [fresh_query_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py)
   3. [entity_detail.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_detail.py)
   4. [boundary_support.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/boundary_support.py)

## 3. Truthing Method

The truthing approach for this phase was:

1. reuse existing targeted tests where available
2. prefer narrow proof over broad speculative runs
3. use direct runtime scripts only for the exact mixed seams identified in Phase 2
4. distinguish clearly between:
   1. working
   2. working but narrow
   3. misrouted
   4. inactive by design

## 4. Executed Verification

## 4.1 Targeted Round 3 Test Slice Passed

The following targeted test slice was executed together and passed:

1. customer master lookup contracts
2. entity detail contracts
3. semantic resolution registry validation

Result:

1. `Ran 60 tests`
2. `OK`

Interpretation:

The current Round 3 customer-lookup and entity-detail seams are not hypothetical.

They have active executable test coverage.

## 4.2 Customer Lookup Is Proven Active

Direct script behavior confirmed:

1. `infer_master_data_lookup_slots(message="give me some customer names", entity_grain="customer")`
   returns:
   1. `lookup_mode = directory_list`
   2. `lookup_projection = names_only`
   3. `lookup_limit = 10`
2. `_deterministic_family_surface_interpretation("give me some customer names", ...)`
   returns a real fresh-query interpretation contract with:
   1. `intent_class = master_data_lookup`
   2. `candidate_capability_ids = ["customer_master_read"]`
   3. `candidate_reports = ["Customer Master List"]`

Interpretation:

Customer direct lookup is proven active end to end at the current bounded scope.

## 4.3 Supplier And Item Lookup Are Proven Narrow, Not Fully Activated

Direct script behavior confirmed:

1. supplier slot inference works lexically:
   `infer_master_data_lookup_slots(..., entity_grain="supplier")`
   still derives `directory_list`
2. item slot inference works lexically:
   `infer_master_data_lookup_slots(..., entity_grain="item")`
   still derives `directory_list`
3. but typed resolution fails closed:
   `resolve_entity_reference_from_message(..., entity_grain="supplier", ...)`
   returns `resolution_status = unsupported_grain`
4. item behaves the same:
   `resolve_entity_reference_from_message(..., entity_grain="item", ...)`
   returns `resolution_status = unsupported_grain`
5. front-door deterministic interpretation stays inactive:
   `_deterministic_family_surface_interpretation("give me some supplier names", ...)`
   returned `null`

Interpretation:

This proves an important enterprise fact:

1. the system already recognizes the grain vocabulary
2. but the typed activation path is still customer-only
3. supplier and item are not simply "missing words"
4. they are structurally unactivated in the current policy layer

## 4.4 Purchase Invoice Is Proven Runtime-Real But Front-Door-Misaligned

Two different behaviors were confirmed.

### 4.4.1 Purchase Invoice Explicit Detail Resolution Works

Direct script behavior confirmed:

1. `detect_entity_drilldown_request("tell me more about ACC-PINV-2026-00048", ...)`
   resolved:
   1. `entity_type = purchase_invoice`
   2. `source = explicit_identifier`

Interpretation:

Purchase invoice is a real document-detail runtime path.

### 4.4.2 Generic Purchase Invoice Surface Is Misrouted

Direct script behavior confirmed:

1. `_deterministic_family_surface_interpretation("show me purchase invoices", ...)`
   did not resolve to a purchase-invoice path
2. instead it produced:
   1. `intent_class = transaction_listing`
   2. `candidate_capability_ids = ["sales_read"]`
   3. `candidate_reports = ["Sales Invoice List"]`
   4. `extracted_slots.listing_view = sales_invoice`

Interpretation:

This is stronger than "unsupported."

It is a real misalignment:

1. purchase invoice exists in runtime detail
2. but generic front-door interpretation currently collapses into the wrong sales-invoice family

## 4.5 Payment Entry Is Proven Partial

Direct script behavior confirmed:

1. `_deterministic_family_surface_interpretation("show me payment entries", ...)`
   returned `null`

Combined with earlier phases:

1. capability metadata exists for `collections_read`
2. specialized runtime support exists in collections logic
3. but no strong generic semantic-family path was activated in this proof run

Interpretation:

Payment Entry is confirmed partial:

1. present in the ecosystem
2. not active as a strong generic direct-navigation surface

## 4.6 Clarification Behavior Is Proven Real But Narrow

Direct runtime scripts confirmed two useful behaviors.

### 4.6.1 Customer Operational Clarification Works

For a customer detail artifact plus the question `when was it delivered?`, the system returned a clarification asking for:

1. exact sales document
2. first sales order date
3. first sales invoice date

Interpretation:

The system can already stop safely and ask for a narrower basis instead of inventing facts.

### 4.6.2 Sales Order Evidence Boundary Works

For a sales-order detail artifact plus the question `when was it delivered?`, the system returned a boundary answer explaining that:

1. the sales order shows planned delivery date and progress
2. but it does not prove the actual shipment event date
3. downstream delivery-note evidence is needed

Interpretation:

This is a strong example of the current contract-based evidence boundary working correctly.

### 4.6.3 Clarification Breadth Is Still Narrow

Even though the clarification behavior works, the active reason family is still narrow and centered on customer/document follow-up situations.

Interpretation:

The ambiguity system itself is real.

The missing piece is breadth and generalization.

## 5. Truth Classification By Round 3 Target

## 5.1 Verified Strong

The following Round 3 behaviors are strongly verified in this phase:

1. customer master-data lookup
2. customer partial-name resolution
3. explicit entity-detail identifier resolution for covered document types
4. customer operational clarification for missing delivery basis
5. sales-order evidence boundary for actual-delivery questions
6. semantic resolution registry validation for the current metadata

## 5.2 Verified Narrow

The following behaviors are real but clearly narrow:

1. entity-reference activation
   Reason:
   lookup machinery exists, but active policy is still customer-only
2. clarification coverage
   Reason:
   clarification machinery exists, but the active reason vocabulary is still narrow

## 5.3 Verified Misaligned

The following behaviors are now proven misaligned rather than simply missing:

1. purchase invoice
   Reason:
   explicit detail path works, but generic front-door routing misroutes to sales invoice
2. supplier/item direct navigation
   Reason:
   alias vocabulary exists, but typed policy activation still fails closed as `unsupported_grain`

## 5.4 Verified Partial

The following behavior is present but not strong enough to claim as a generic family path:

1. payment entry
   Reason:
   specialized capability/runtime evidence exists, but generic direct-navigation behavior was inactive in this phase

## 6. Main Behavior Findings

Round 3 Phase 3 reveals six important truths.

### 6.1 The Existing Contract Foundation Is Valuable

The current system already has enough typed seams to support enterprise-grade alignment work:

1. fresh-query interpretation contracts
2. entity-reference resolution contracts
3. entity-detail evidence contracts
4. clarification fields
5. evidence-boundary behavior

This foundation should be extended, not replaced.

### 6.2 The Main Problem Is Activation Asymmetry

The major issue is not missing architecture.

It is that:

1. some grains are declared in alias space but not in policy space
2. some documents are supported in detail runtime but not in generic interpretation
3. some finance surfaces are present in specialized modules but not activated as shared family paths

### 6.3 Supplier And Item Should Not Be Described As Unsupported Vocabulary Problems

The system already recognizes supplier/item language.

The failure is deeper:

1. policy activation is missing
2. semantic-family activation is missing
3. the system correctly fails closed instead of inventing a path

That is a better enterprise posture than guessing, but still incomplete.

### 6.4 Purchase Invoice Is The Clearest Alignment Defect

Purchase invoice is the strongest Round 3 example of runtime-versus-front-door mismatch.

That makes it a high-value target for later implementation because:

1. the runtime seam already exists
2. the missing work is alignment
3. alignment can likely be bounded without inventing a parallel subsystem

### 6.5 Payment Entry Needs Ownership Clarification Before Activation

Payment Entry should not be activated casually just because the capability exists.

This phase confirms that it still needs a cleaner ownership decision:

1. shared transaction family
2. collections-specific family
3. or another approved finance-navigation seam

### 6.6 Clarification Expansion Should Reuse The Existing Contract Layer

This phase confirms that ambiguity handling should be expanded through the existing typed clarification layer, not by new phrase-specific repairs.

## 7. Practical Round 3 Status

After Round 3 Phase 3, the practical status is:

1. customer direct lookup is verified strong
2. supplier and item direct lookup are verified narrow and inactive at policy level
3. purchase invoice is verified as runtime-real but front-door-misaligned
4. payment entry is verified partial
5. clarification is verified real but still narrow in activation breadth

## 8. What This Means For The Next Round 3 Step

The next safe step after this phase is not implementation yet if we are keeping the research sequence disciplined.

The next step should be Round 3 Phase 4:

1. rank the proven misalignments by enterprise priority
2. separate:
   1. alignment fixes
   2. activation expansions
   3. ownership decisions
3. identify which ones belong inside current Phase `3.3` and which ones should wait for later governed scope expansion

This phase now gives enough factual basis to do that honestly.
