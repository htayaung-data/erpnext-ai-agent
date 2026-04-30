# Qwen ERP Governed Scope Coverage Round 3 Phase 1 Front-Door Inventory

Status: active research note
Date: 2026-04-13
Scope: Round 3 Phase 1 front-door and metadata inventory for the cross-layer alignment targets identified by Rounds 1 and 2

## 1. Purpose

Round 1 and Round 2 already mapped broad governed scope coverage.

Round 3 is different.

It should not widen into more unrelated ERP domains first.

It should focus on the highest-value mixed and asymmetric seams already discovered.

So Round 3 Phase 1 is not another broad inventory pass.

It is a focused metadata and front-door inventory for these alignment targets:

1. document entity-detail alignmen
2. purchase invoice metadata/runtime alignmen
3. payment entry ownership and activation
4. ambiguity and clarification activation breadth
5. direct entity-reference policy breadth

The goal is to answer:

1. what is already declared for these alignment targets
2. what is still only implicit in runtime
3. where the front door remains too generic
4. where typed contracts already exist but activation is still narrow

## 2. Evidence Basis

This note is based on direct inspection of:

1. [frontdoor_intent_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/frontdoor_intent_registry.json)
2. [semantic_resolution_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/semantic_resolution_registry.json)
3. [capability_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/capability_registry.json)
4. [report_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/report_registry.json)
5. [entity_reference_policy_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/entity_reference_policy_registry.json)
6. [contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py)
7. [entity_reference_resolution.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_reference_resolution.py)
8. [clarification_translation.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/clarification_translation.py)
9. [clarification_resolution.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/clarification_resolution.py)
10. [qwen_erp_governed_scope_coverage_round1_ambiguity_handling_evaluation_2026-04-13.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/phase3_entity_lookup_scope/qwen_erp_governed_scope_coverage_round1_ambiguity_handling_evaluation_2026-04-13.md)
11. [qwen_erp_governed_scope_coverage_round2_phase5_bounded_design_2026-04-13.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/phase3_entity_lookup_scope/qwen_erp_governed_scope_coverage_round2_phase5_bounded_design_2026-04-13.md)

## 3. Scope Groups Examined

Round 3 Phase 1 examined five cross-layer scope groups.

### 3.1 Document Entity Detail Alignmen

1. sales invoice
2. sales order
3. purchase order
4. delivery note
5. purchase invoice

### 3.2 Payment Entry Ownership

1. report-level presence
2. capability-level presence
3. semantic-routing presence
4. family-path presence

### 3.3 Purchase Invoice Alignmen

1. front-door/semantic declaration
2. detail/runtime declaration
3. continuity with related finance/document families

### 3.4 Ambiguity And Clarification Activation

1. compiler-level clarification
2. artifact-boundary clarification
3. entity-detail clarification
4. continuation clarification

### 3.5 Entity Reference Breadth

1. direct governed lookup modes
2. active grains in entity-reference policy
3. relation to the broader runtime support already discovered in earlier rounds

## 4. Front-Door Finding

The front door remains intentionally broad.

Relevant observed intent classes include:

1. `capability_question`
2. generic governed ERP request handling
3. continuation

Important finding:

Round 3 alignment targets are not surfaced through specific front-door intent classes.

That means:

1. payment entry does not appear as a front-door-specific inten
2. purchase invoice does not appear as a front-door-specific inten
3. document entity-detail alignment is not owned by a special front-door class

Interpretation:

The Round 3 problem is not a front-door taxonomy explosion problem.

It is a deeper metadata and seam-alignment problem.

## 5. Metadata Inventory Findings

## 5.1 Master-Data Lookup Metadata Is Still Narrow

The inspected semantic registry still shows only one active `master_data_lookup` execution rule:

1. `master_customer_directory`

Interpretation:

1. the typed direct-lookup ecosystem exists
2. but its activated semantic inventory is still narrow
3. this matters for Round 3 because entity-reference architecture is stronger than current declared activation

## 5.2 Entity Reference Policy Is Still Customer-Only

The entity reference policy registry currently shows one active policy:

1. customer

That customer policy already supports:

1. `directory_list`
2. `candidate_resolution`
3. `profile_target`

Interpretation:

1. the system already has a real typed entity-reference contract seam
2. but active policy breadth is still far narrower than the broader runtime capabilities discovered in Rounds 1 and 2

This is one of the clearest Round 3 front-door/metadata asymmetries.

## 5.3 Payment Entry Is Visible In Capability And Report Metadata, But Not In A Strong Semantic Family Path

Observed metadata:

1. `collections_read` capability exists
2. `collections_read` has default report `Payment Entry List`
3. `Payment Entry List` exists in the report layer

But:

1. no strong semantic family-resolution rule for payment entry was found in the current inspected path
2. `collections_read.intent_classes` is still empty

Interpretation:

Payment Entry is not absent.

It is metadata-visible but not fully declared as a strong generic family route.

This supports the Round 2 finding that payment entry is a partial surface.

## 5.4 Purchase Invoice Is Weak In Metadata

In the current inspected metadata surface for Round 3:

1. no strong purchase-invoice semantic execution route was found
2. no active entity-reference policy was found for purchase invoice

Interpretation:

Purchase invoice remains one of the clearest cases where runtime support and metadata declaration are not aligned.

## 5.5 Typed Lookup Contracts Already Exis

The codebase already contains typed lookup support through:

1. `lookup_mode`
2. `directory_list`
3. `candidate_resolution`
4. `profile_target`

inside the current contracts and entity-reference resolution seam.

Interpretation:

Round 3 does not need to invent a new lookup contract family from zero.

It needs to decide how far to activate and align the one that already exists.

## 6. Clarification Inventory Findings

## 6.1 Shared Clarification Architecture Is Real

The current runtime already has:

1. clarification reason contracts
2. clarification signal contracts
3. pending clarification state and resolution
4. clarification continuation handling

This was already documented in Round 1 and remains true in Round 3.

## 6.2 Artifact-Boundary Clarification Is Still Narrowly Activated

The entity-detail evidence contract currently exposes narrow clarification reasons such as:

1. `customer_tenure_basis_missing`
2. `customer_operational_document_missing`

Interpretation:

1. artifact-boundary clarification exists
2. but its active typed coverage is still narrow
3. this matches the earlier finding that ambiguity handling is present but unevenly activated

## 6.3 Round 3 Alignment Targets Depend On Better Clarification Breadth

This matters directly for:

1. document detail questions
2. event-date questions
3. payment-related questions
4. purchase-invoice support questions

Because these are exactly the areas where support can be:

1. real but narrow
2. partial but not absen
3. ambiguous without stronger typed clarification

## 7. Round 3 Phase 1 Classification

### 7.1 Strongly Present As Reusable Foundations

1. typed lookup-mode contract fields
2. entity-reference resolution seam
3. shared clarification contracts
4. pending clarification continuation engine

### 7.2 Present But Narrowly Activated

1. master-data lookup semantic activation
2. entity-reference policy breadth
3. artifact-boundary clarification breadth

### 7.3 Present But Asymmetric

1. payment entry
   visible in capability/report metadata, but not strongly routed in semantic family metadata

2. purchase invoice
   stronger in runtime than in front-door/family metadata

### 7.4 Not The Main Round 3 Problem

1. front-door genericity by itself

Interpretation:

The front door is broad on purpose.
The Round 3 problem is deeper-layer alignment.

## 8. Main Round 3 Phase 1 Findings

Round 3 Phase 1 reveals four important truths.

### 8.1 The Main Round 3 Work Is Alignment, Not New Contract Invention

The repo already contains meaningful typed foundations for:

1. direct lookup
2. clarification
3. continuation

So the next step should start from adaptation and alignment, not from brand-new architecture.

### 8.2 Payment Entry And Purchase Invoice Are Still The Right Alignment Targets

The metadata inventory reinforces the Round 2 conclusion:

1. payment entry remains partial
2. purchase invoice remains asymmetric

So Round 3 should keep them as central design targets.

### 8.3 Entity Reference Activation Is Still Far Narrower Than The Reusable Lookup Infrastructure

This means the project already has some of the right machinery, but not enough activation breadth.

That is a classic enterprise alignment issue, not a missing-concepts issue.

### 8.4 Ambiguity Expansion Is A Cross-Cutting Round 3 Concern

Because the typed clarification engine already exists, Round 3 should treat ambiguity expansion as a shared activation design item across the alignment targets, not as a separate isolated topic.

## 9. Implication For Round 3 Phase 2

The next step should be runtime seam mapping focused specifically on these Round 3 alignment targets:

1. document entity-detail dispatch and handoff
2. purchase-invoice runtime versus metadata ownership
3. payment-entry specialized versus generic path ownership
4. clarification and ambiguity activation breadth at the artifact/entity-detail level

## 10. Current Status Statemen

Round 3 Phase 1 is now started and documented.

Current status:

1. Round 3 is correctly scoped as alignment research
2. the main targets are payment entry, purchase invoice, document entity detail, and clarification breadth
3. the project already has strong reusable typed foundations
4. the key issue remains activation and alignment, not total absence of architecture
