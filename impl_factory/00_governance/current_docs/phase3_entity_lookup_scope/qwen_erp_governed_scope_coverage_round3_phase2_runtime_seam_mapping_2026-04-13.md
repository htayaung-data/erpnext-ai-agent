# Qwen ERP Governed Scope Coverage Round 3 Phase 2 Runtime Seam Mapping

Status: active research note
Date: 2026-04-13
Scope: Round 3 Phase 2 runtime seam mapping for the cross-layer alignment targets identified in Round 3 Phase 1

## 1. Purpose

Round 3 Phase 1 confirmed that the next work should not widen into unrelated ERP families first.

It should instead map the mixed seams where the system already has meaningful runtime support, but ownership is still split across:

1. metadata
2. typed contracts
3. direct runtime branching
4. family-specific artifact handoff
5. narrow clarification activation

So Round 3 Phase 2 asks:

1. which Round 3 targets already have real runtime execution
2. which ones are still controlled by direct Python branching
3. where runtime is ahead of metadata
4. where typed contracts already exist but activation is still narrow
5. where clarification is shared in architecture but narrow in reason coverage

This phase is still seam mapping, not behavior proofing yet.

## 2. Evidence Basis

This note is based on direct inspection of:

1. [entity_detail.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_detail.py)
2. [entity_reference_resolution.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_reference_resolution.py)
3. [contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py)
4. [boundary_support.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/boundary_support.py)
5. [lanes/entity_drilldown_lane.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/entity_drilldown_lane.py)
6. [lanes/artifact_boundary_lane.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/artifact_boundary_lane.py)
7. [metadata.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/metadata.py)
8. [collections_support.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/collections_support.py)
9. [customer_kpi_runtime_support.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/customer_kpi_runtime_support.py)
10. [fresh_query_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py)
11. [capability_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/capability_registry.json)
12. [semantic_resolution_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/semantic_resolution_registry.json)
13. [entity_reference_policy_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/entity_reference_policy_registry.json)

## 3. Round 3 Targets Mapped

This phase mapped five alignment targets:

1. document entity-detail alignmen
2. purchase invoice metadata/runtime alignmen
3. payment entry ownership and activation
4. ambiguity and clarification activation breadth
5. direct entity-reference breadth versus current activation

## 4. Strong Runtime Seams Already Presen

## 4.1 Entity Drilldown Is A Real Lane

The runtime already has a dedicated entity-drilldown lane.

Observed shared pieces:

1. `detect_entity_drilldown_request(...)`
2. `handle_entity_drilldown_turn(...)`
3. `execute_entity_drilldown(...)`

Interpretation:

1. document and entity drilldown is not an ad-hoc browser-only behavior
2. it is already a first-class execution path
3. the weakness is ownership shape, not total absence

## 4.2 Typed Entity-Reference Resolution Already Exists

The runtime already has a typed entity-reference seam through:

1. `infer_lookup_mode_from_message(...)`
2. `extract_lookup_search_text(...)`
3. `infer_master_data_lookup_slots(...)`
4. `resolve_entity_reference_from_message(...)`
5. `EntityReferenceResolutionContract`

Important meaning:

Round 3 does not need to invent direct lookup architecture from zero.

The contract seam already exists.

The main problem is narrow activation and uneven consumption.

## 4.3 Artifact Context Handoff Already Exists

`entity_detail.py` already reads entity candidates from family artifacts through `_artifact_entity_candidates(...)`.

Observed artifact families feeding candidates include:

1. `transaction_listing`
2. `aging`
3. `ranking_analytics`
4. `product_profitability`
5. `customer_master_list`

Interpretation:

1. entity follow-up is not purely phrase-based
2. there is already a meaningful artifact-to-detail handoff seam
3. but the handoff remains family-shaped and partly hardcoded

## 4.4 Clarification Architecture Is Already Shared

The runtime already has a shared clarification lane and boundary lane.

Observed control points include:

1. `handle_artifact_boundary_turn(...)`
2. clarification state management in the broader service flow
3. typed entity detail evidence contract fields:
   - `clarification_required`
   - `clarification_reason_type`
   - `clarification_options`

Interpretation:

The clarification problem is not lack of architecture.

It is narrow activation and narrow typed reason coverage.

## 5. Mixed Or Asymmetric Runtime Seams

## 5.1 Document Detail Execution Is Real But Branch-Driven

`execute_entity_drilldown(...)` still dispatches directly by `entity_type`.

Observed explicit execution branches:

1. sales invoice
2. purchase invoice
3. sales order
4. purchase order
5. delivery note
6. customer
7. supplier
8. item

Interpretation:

1. document detail coverage is broader than some metadata surfaces imply
2. but the runtime still owns document/entity dispatch directly
3. this is a mixed-authority seam, not a fully metadata-governed one

## 5.2 Explicit Identifier Resolution Is Still Hardcoded

`_resolve_explicit_identifier(...)` still checks concrete doctypes directly.

Observed direct identifier support includes:

1. `Sales Invoice`
2. `Purchase Invoice`
3. `Sales Order`
4. `Purchase Order`
5. `Delivery Note`
6. `Item`

Interpretation:

This confirms that document-detail support exists, but direct identifier routing is still owned in code rather than through a more generic declared registry path.

## 5.3 Named Entity Resolution Is Still Uneven By Grain

`_resolve_named_entity_from_detail_request(...)` still resolves named targets through direct grain-specific logic.

Observed pattern:

1. customer: direct DB checks plus typed entity-reference resolution
2. supplier: direct DB checks only
3. item: direct item-name resolution helper

Important interpretation:

1. customer already consumes the stronger typed lookup seam
2. supplier and item still rely on direct branch logic
3. this is one of the clearest uneven-consumption seams in the current system

## 5.4 Purchase Invoice Is Runtime-Real But Metadata-Weak

`entity_detail.py` already contains a full `_purchase_invoice_detail(...)` handler with:

1. purchase-invoice summary blocks
2. item rows
3. entity-detail artifact payload
4. rendered response payload

But Round 3 Phase 1 already confirmed that purchase invoice is still weak in the inspected semantic and reference metadata surfaces.

Interpretation:

Purchase invoice remains a textbook runtime-ahead-of-metadata seam.

## 5.5 Payment Entry Remains Specialized Rather Than Family-Owned

The current inspected runtime shows Payment Entry support mainly through specialized finance support, not a strong generic family seam.

Observed evidence:

1. `collections_read` capability exists and points to `Payment Entry List`
2. `collections_support.py` uses Payment Entry tables in specialized receipt/collection logic
3. no strong semantic family-resolution rule for payment entry was found in the current semantic registry
4. `collections_read.intent_classes` is still empty

Interpretation:

1. payment entry is not absent from the system
2. but it is not yet owned by a strong generic semantic-family route
3. it remains partial and specialized

## 5.6 Deterministic Surface Rescue Still Exists In Fresh Query Runtime

`fresh_query_interpreter.py` still contains `_pipeline_requires_deterministic_surface_rescue(...)`.

Interpretation:

1. the system still uses bounded rescue behavior when the semantic surface is under-specified
2. this should be audited carefully during later activation work
3. Round 3 should treat it as a risk-control seam, not as business-meaning authority

## 6. Clarification And Ambiguity Mapping

## 6.1 Clarification Payload Support Is Already Typed

`EntityDetailEvidenceRequestContract` already carries:

1. `entity_question_type`
2. `basis`
3. `question_shape`
4. `value_mode`
5. `profile_sections`
6. `clarification_required`
7. `clarification_reason_type`
8. `clarification_options`

Interpretation:

This is a strong enterprise asset.

The system already has the right typed seam to express ambiguity without dropping back to raw-message repair.

## 6.2 Boundary Clarification Coverage Is Still Narrow

The current boundary support still shows narrow reason-type coverage such as:

1. `customer_operational_document_missing`

Observed result:

1. the runtime can ask for missing basis
2. but the active reason vocabulary is still strongly customer/lifecycle oriented
3. broader document ambiguity is not yet generalized into a reusable reason family

## 6.3 The Ambiguity Problem Is Breadth, Not Existence

Based on the current seam map:

1. ambiguity handling exists
2. continuation handling exists
3. typed clarification fields exis
4. boundary rendering exists

So the architecture gap is not "we need an ambiguity system."

The real gap is:

1. broader typed ambiguity families
2. broader activation across entity/document families
3. cleaner handoff between artifact evidence, entity detail, and clarification

## 7. Ownership Map By Round 3 Targe

## 7.1 Document Entity Detail Alignmen

Current ownership:

1. active runtime lane exists
2. artifact handoff exists
3. execution is still direct-branching in `entity_detail.py`

Status:

Partially aligned, still mixed authority.

## 7.2 Purchase Invoice Alignmen

Current ownership:

1. strong runtime detail handler exists
2. weak inspected metadata declaration
3. no strong declared reference policy in current activation surface

Status:

Runtime ahead of metadata.

## 7.3 Payment Entry Ownership

Current ownership:

1. capability metadata exists
2. specialized runtime support exists
3. strong generic semantic-family path not yet established

Status:

Partial and specialized.

## 7.4 Ambiguity And Clarification Breadth

Current ownership:

1. strong shared architecture exists
2. typed clarification fields exis
3. active reason coverage still narrow

Status:

Architecturally present, activation still narrow.

## 7.5 Direct Entity Reference Breadth

Current ownership:

1. typed lookup contract and resolver exis
2. alias maps already recognize `customer`, `supplier`, and `item`
3. active policy registry still exposes only `customer`

Status:

Contract-ready, activation narrow.

## 8. Main Enterprise Conclusion

Round 3 Phase 2 shows that the current system is not dealing with a single missing feature.

It is dealing with a repeated alignment pattern:

1. the repo already has stronger typed contracts than the live activation breadth
2. the runtime already supports more ERP surfaces than the current metadata declares
3. the remaining enterprise work is to align ownership, not to invent parallel logic

That means the right next move after this phase is still the same:

1. preserve the shared typed seams already presen
2. remove direct branch ownership only where a stronger shared seam is ready
3. avoid widening activation faster than evidence, metadata, and clarification can suppor

## 9. What This Means For Round 3 Phase 3

Round 3 Phase 3 should now truth these specific behaviors:

1. document detail paths that are runtime-real but metadata-mixed
2. purchase invoice detail behavior as a runtime-ahead-of-metadata case
3. payment entry behavior as a partial specialized case
4. entity-reference breadth behavior versus customer-only activation
5. clarification behavior for ambiguous document and lifecycle follow-ups

The goal of Phase 3 should be behavioral proof, not design invention.
