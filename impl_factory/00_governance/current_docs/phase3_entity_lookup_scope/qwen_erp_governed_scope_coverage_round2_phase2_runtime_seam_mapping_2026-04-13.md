# Qwen ERP Governed Scope Coverage Round 2 Phase 2 Runtime Seam Mapping

Status: active research note
Date: 2026-04-13
Scope: Round 2 Phase 2 runtime seam mapping for document-navigation, finance-operation, and inventory-operation surfaces identified in Round 2 Phase 1

## 1. Purpose

Round 2 Phase 1 established that the next governed scope groups are wider than Round 1 at metadata level.

Round 2 Phase 2 now asks the runtime question:

1. which of those declared surfaces are actually consumed by shared runtime seams
2. where does the runtime still branch directly by entity or document type
3. where is runtime richer than metadata
4. where is metadata richer than runtime
5. which Round 2 scopes are truly active, partial, or absent in end-to-end runtime shape

This phase is about seam ownership, not browser proof yet.

## 2. Evidence Basis

This note is based on direct inspection of:

1. [semantic_resolution.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/semantic_resolution.py)
2. [fresh_query_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py)
3. [family_adapters.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_adapters.py)
4. [family_rendering.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_rendering.py)
5. [followup_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/followup_interpreter.py)
6. [family_followup.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_followup.py)
7. [continuation_support.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/continuation_support.py)
8. [entity_detail.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_detail.py)
9. [lanes/artifact_boundary_lane.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/artifact_boundary_lane.py)
10. [governed_kpi_runtime_execution.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_kpi_runtime_execution.py)
11. [collections_support.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/collections_support.py)

## 3. Round 2 Scope Groups Mapped

This phase mapped these surfaces:

1. sales invoice
2. sales order
3. delivery note
4. purchase order
5. accounts receivable
6. accounts payable
7. inventory snapshot by item
8. inventory snapshot by warehouse
9. payment entry
10. purchase invoice
11. purchase receip
12. journal entry

## 4. Shared Runtime Seams Already Presen

## 4.1 Shared Semantic Resolution Exists For Core Family Paths

The runtime already has dedicated shared semantic-resolution functions for:

1. transaction listing
2. inventory summary
3. aging analysis
4. financial statemen
5. trend analysis

Important examples:

1. `resolve_transaction_listing_interpretation(...)`
2. `resolve_inventory_summary_interpretation(...)`
3. `resolve_aging_analysis_interpretation(...)`

Interpretation:

1. sales invoice
2. sales order
3. delivery note
4. purchase order
5. AR/AP aging
6. item/warehouse inventory snapsho

already participate in real shared semantic runtime seams.

This is a strong enterprise finding because it shows the Round 2 breadth is not only declared in metadata.

## 4.2 Shared Family Adapters Exist For Core Round 2 Families

The runtime already has shared normalized family adapters for:

1. `transaction_listing`
2. `aging`
3. `inventory_snapshot`
4. `ranking_analytics`
5. `trend_analytics`
6. `financial_statement`

Important examples:

1. `_build_transaction_listing_artifact(...)`
2. `_build_aging_artifact(...)`
3. `_build_inventory_snapshot_artifact(...)`

Interpretation:

The following Round 2 surfaces already have a family-adapter path, not just raw report execution:

1. sales invoice listing
2. sales order listing
3. delivery note listing
4. purchase order listing
5. AR/AP aging
6. inventory snapshot by item
7. inventory snapshot by warehouse

## 4.3 Shared Family Rendering Exists For Core Round 2 Families

The runtime already has shared rendering blocks for:

1. transaction listings
2. aging
3. inventory snapsho
4. ranking
5. trend
6. financial statemen

Important examples:

1. `_transaction_listing_blocks(...)`
2. `_aging_blocks(...)`
3. `_inventory_blocks(...)`

Interpretation:

These Round 2 surfaces are not only executable.
They already have a normalized render layer.

## 4.4 Shared Follow-Up And Continuation Logic Exists

The runtime already has shared follow-up handling for family artifacts.

Observed behaviors:

1. transaction-listing target switches are detected in follow-up boundary
2. local family follow-up supports shared refinement behavior for family artifacts
3. continuation support preserves scope or forces governed requery when needed
4. artifact boundary lane handles direct evidence, boundary stop, and enrichment boundary in one shared seam

Important meaning:

The Round 2 weakness is not lack of continuation architecture.

The continuation architecture already exists.

## 5. Strong Round 2 Runtime Paths

## 5.1 Sales Document Listing Paths Are Strong

Sales invoice, sales order, and delivery note all show a strong multi-layer path:

1. semantic resolution
2. shared family adapter
3. shared family renderer
4. follow-up boundary awareness

Interpretation:

These are real active governed runtime surfaces, not only registry entries.

## 5.2 Purchase Order Listing Is Also In The Shared Listing Path

Purchase order is part of the same shared transaction-listing architecture.

Interpretation:

Purchase order belongs to the stronger Round 2 group, even though purchase document coverage as a whole is still uneven.

## 5.3 AR/AP Aging Is Strong

Receivable and payable aging are both clearly mapped through:

1. semantic resolution
2. aging family adapter
3. aging family renderer
4. ranking-style continuation and boundary behavior

Important additional finding:

aging analysis already has explicit clarify behavior when the aging view is unresolved.

That is a concrete example of stronger shared clarification activation in one Round 2 family.

## 5.4 Inventory Snapshot By Item And Warehouse Is Strong

Inventory summary already has a real shared semantic seam and a real shared adapter/renderer seam.

Important detail:

warehouse is handled as an inventory axis in the shared runtime, not merely as a report keyword.

Interpretation:

The inventory snapshot family is more mature than a simple metadata reading would suggest.

## 6. Mixed Or Uneven Runtime Seams

## 6.1 Entity Detail Is Still A Mixed Seam

Entity detail remains partly shared and partly direct-branching.

Observed direct explicit-identifier support includes:

1. sales invoice
2. purchase invoice
3. sales order
4. purchase order
5. delivery note
6. item

Observed explicit drilldown dispatch also branches directly by `entity_type` when executing detail.

Interpretation:

1. entity detail already supports more document types than the Round 2 front-door metadata suggests
2. but it still uses direct document/entity branching in code
3. this is a mixed-authority seam, not a fully metadata-driven shared seam

This is especially important for purchase invoice:

1. purchase invoice is weak or absent in the current front-door metadata inventory
2. but purchase invoice detail exists in runtime through explicit identifier/detail functions

So Round 2 exposes a real pattern:

runtime is richer than metadata for some document-detail surfaces.

## 6.2 Artifact Entity Candidate Handoff Is Uneven

`entity_detail.py` already extracts candidates from normalized family artifacts, including:

1. transaction listings
2. aging artifacts
3. ranking artifacts
4. product profitability
5. customer master lis

This is good shared behavior.

But the entity types injected from those artifacts are still partly inferred through direct family-specific logic.

Interpretation:

The handoff seam is better than a pure phrase parser, but it is not yet fully generalized across all Round 2 document and operation entities.

## 6.3 Payment Entry Is Present In Specialized Runtime, Not Generic Family Runtime

Payment Entry appears in specialized runtime support:

1. `governed_kpi_runtime_execution.py`
2. `collections_support.py`

But in the generic Round 2 family path inspected here, Payment Entry does not appear as:

1. a shared semantic family rule consumer
2. a transaction-listing family adapter targe
3. a generic family renderer targe
4. an entity-detail document type

Interpretation:

Payment Entry is a real example of:

1. capability/report presence
2. some specialized runtime usage
3. but no equivalent shared generic family activation ye

This confirms it is a true partial path, not a fully active one.

## 7. Runtime Gaps Observed

## 7.1 Purchase Receipt Is Not Active In The Shared Runtime Path

No active shared semantic/family/detail path was found for purchase receipt in the inspected Round 2 seams.

Interpretation:

Purchase receipt should remain classified as absent in the current governed runtime path until later evidence proves otherwise.

## 7.2 Journal Entry Is Not Active In The Shared Runtime Path

No active shared semantic/family/detail path was found for journal entry in the inspected Round 2 seams.

Interpretation:

Journal entry should remain classified as absent in the current governed runtime path until later evidence proves otherwise.

## 7.3 Purchase Invoice Is A Runtime-Only Partial Surface

Purchase invoice does not currently look like a strong front-door family path from Round 2 Phase 1.

But Round 2 Phase 2 shows:

1. explicit identifier resolution support exists
2. explicit purchase-invoice detail rendering exists
3. aging family artifacts can expose purchase-invoice references as linked vouchers

Interpretation:

Purchase invoice is not absent everywhere.

It is a partial runtime surface whose activation is uneven across:

1. metadata
2. front-door routing
3. document-detail runtime

## 8. Round 2 Phase 2 Classification

### 8.1 Shared And Strong

1. sales invoice listing
2. sales order listing
3. delivery note listing
4. purchase order listing
5. accounts receivable aging
6. accounts payable aging
7. inventory snapshot by item
8. inventory snapshot by warehouse

### 8.2 Active But Mixed

1. purchase invoice
   Reason:
   detail/runtime support exists, but broad metadata/family activation is uneven

2. document/entity detail handoff
   Reason:
   artifact-based handoff exists, but explicit entity-type branching remains in code

### 8.3 Partial

1. payment entry
   Reason:
   present in specialized collections/KPI runtime, but not active in the shared generic family path inspected here

### 8.4 Not Found In Current Shared Runtime Path

1. purchase receip
2. journal entry

## 9. Main Round 2 Phase 2 Findings

Round 2 Phase 2 reveals four important patterns.

### 9.1 The Shared Family Runtime Is Broader Than Round 1

This is a positive finding.

The project already has mature shared seams for several important Round 2 scopes.

### 9.2 The Biggest Weakness Is Not Family Rendering

The biggest weakness is not:

1. missing family adapters
2. missing family renderers
3. missing continuation framework

The bigger weaknesses are:

1. uneven activation across metadata versus runtime
2. mixed-authority entity-detail handoff
3. specialized side paths that do not yet join the same shared family runtime

### 9.3 Some Surfaces Are Runtime-Richer Than Metadata

Purchase invoice is the clearest example in this phase.

This means later expansion planning must not assume:

1. metadata gap means total runtime absence

The project now clearly contains both patterns:

1. metadata richer than runtime
2. runtime richer than metadata

### 9.4 Payment Entry Needs Careful Later Evaluation

Payment Entry should not be casually declared active just because:

1. the report exists
2. the capability exists
3. specialized support exists somewhere

This phase shows it still lacks the same generic family-path activation seen for stronger Round 2 document families.

## 10. Implication For Round 2 Phase 3

The next step should be behavior truthing for the Round 2 surfaces now classified here.

Phase 3 should verify real runtime behavior for:

1. strong shared paths
2. mixed paths
3. partial paths

Recommended focus areas:

1. sales invoice, sales order, delivery note, purchase order
2. AR/AP aging
3. inventory by item and warehouse
4. purchase invoice identifier/detail behavior
5. payment entry partial behavior

## 11. Current Status Statemen

Round 2 Phase 2 is now documented.

Current status:

1. the shared runtime for Round 2 is meaningfully broader than Round 1
2. several document and analytical families are already strong
3. entity detail remains a mixed seam
4. payment entry is partial, not fully active in the shared generic family path
5. purchase receipt and journal entry remain absent in the current inspected runtime path
