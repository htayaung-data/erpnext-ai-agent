# Qwen ERP Governed Scope Coverage Round 2 Phase 3 Behavior Truthing

Status: active research note
Date: 2026-04-13
Scope: Round 2 Phase 3 behavior truthing for document-navigation, finance-operation, and inventory-operation surfaces mapped in Round 2 Phases 1 and 2

## 1. Purpose

Round 2 Phase 1 established the declared metadata surface.

Round 2 Phase 2 established the runtime seam shape.

Round 2 Phase 3 now answers the practical truth question:

1. which Round 2 paths are verified by executable tests
2. which are verified only by code inspection
3. which have no clean generic truthing path ye
4. which existing failures are relevant to this scope
5. which existing failures are unrelated noise

This note is not a full browser/UAT chapter.

It is bounded code-level and runtime-level truthing.

## 2. Evidence Basis

This note is based on:

1. [qwen_erp_governed_scope_coverage_round2_phase1_frontdoor_inventory_2026-04-13.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/phase3_entity_lookup_scope/qwen_erp_governed_scope_coverage_round2_phase1_frontdoor_inventory_2026-04-13.md)
2. [qwen_erp_governed_scope_coverage_round2_phase2_runtime_seam_mapping_2026-04-13.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/phase3_entity_lookup_scope/qwen_erp_governed_scope_coverage_round2_phase2_runtime_seam_mapping_2026-04-13.md)
3. targeted unit-test execution in:
   1. [test_semantic_financial_resolution.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_semantic_financial_resolution.py)
   2. [test_entity_detail_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_entity_detail_contracts.py)
4. direct inspection of existing probe utilities in:
   [fresh_query_diagnostics.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/probes/fresh_query_diagnostics.py)

## 3. Truthing Method

The truthing approach for this phase was:

1. reuse existing targeted tests where available
2. prefer Round 2-specific tests over very broad suite runs
3. separate unrelated historical failures from Round 2 evidence
4. avoid claiming untested paths as verified

## 4. Executed Verification

## 4.1 Targeted Round 2 Semantic And Family Tests Passed

The following targeted tests were executed together and passed:

1. sales invoice transaction-listing default resolution
2. delivery note transaction-listing execution
3. explicit date-slot application for sales invoice listing
4. warehouse inventory summary resolution
5. item inventory summary default resolution
6. receivable aging execution
7. payable aging execution
8. aging clarification for missing aging view
9. delivery note transaction-listing family adapter generalization
10. delivery note transaction-listing family validation without outstanding amoun

Result:

1. `Ran 10 tests`
2. `OK`

Interpretation:

The strongest Round 2 family paths already have concrete executable test evidence.

## 4.2 Entity Detail Contract Suite Passed

The targeted entity-detail suite was also executed.

Result:

1. `Ran 51 tests`
2. `OK`

Important relevant coverage found inside that suite includes tests for:

1. explicit sales invoice identifier resolution
2. explicit delivery note identifier resolution
3. explicit purchase order identifier resolution
4. delivery note detail drilldown
5. purchase order detail drilldown
6. sales invoice delivery proof
7. sales order delivery progress and planned delivery date
8. purchase order receipt progress and planned receipt date
9. typed contract mapping for actual sales-order delivery event and actual purchase-order receipt even

Interpretation:

This confirms that Round 2 document-detail and evidence behavior is not only present in code.
It is also covered by active tests.

## 4.3 Broad Semantic Suite Has Existing Unrelated Noise

A broader combined test run including the large semantic suite produced:

1. `Ran 258 tests`
2. `FAILED (failures=3)`

The three failures observed were in composite-profile-related areas, not in the Round 2 document, aging, or inventory surfaces targeted in this phase.

Interpretation:

1. this broad suite is not clean enough to use as a direct Round 2 pass/fail gate by itself
2. the targeted Round 2 tests remain the more reliable truthing evidence for this phase

## 4.4 Existing Probe Utilities Were Found But Not Directly Usable In This Shell Contex

The repo already contains family smoke probes for:

1. aging
2. inventory/produc
3. financial statemen

However, a direct attempt to run the probe utilities from the current shell context failed because the standalone invocation could not import the full `frappe` environment.

Interpretation:

1. probe infrastructure exists
2. but in this research turn the cleaner trustworthy evidence came from targeted test execution
3. this is a tooling-context limitation, not proof that the families themselves are broken

## 5. Truth Classification By Scope

## 5.1 Verified Strong

The following Round 2 paths now have meaningful truth evidence from executed tests:

1. sales invoice transaction listing
2. delivery note transaction listing
3. inventory summary by warehouse
4. inventory summary by item
5. receivable aging
6. payable aging
7. delivery note listing family adaptation
8. delivery note listing family validation
9. sales invoice detail evidence
10. sales order detail evidence
11. purchase order detail evidence
12. delivery note detail drilldown

## 5.2 Verified Mixed

The following Round 2 paths are verified as real, but still structurally mixed:

1. purchase order detail
2. sales order detail
3. sales invoice detail
4. delivery note detail

Reason:

1. tests prove they work
2. but Round 2 Phase 2 showed they still rely on direct entity/document branching in `entity_detail.py`

So these are working paths with shared-value, but not yet fully generalized seams.

## 5.3 Partially Verified

The following Round 2 paths are supported by partial evidence only:

1. purchase invoice
   Evidence:
   runtime/code-level support exists in `entity_detail.py`
   but no direct executed Round 2-specific test was run in this phase

2. payment entry
   Evidence:
   specialized support exists in KPI/collections runtime
   but no generic family-path truthing passed through this phase

Interpretation:

These should not be promoted to "strongly verified generic family paths" yet.

## 5.4 Not Verified In Current Phase

The following Round 2 candidate scopes remain unverified in this phase:

1. purchase receip
2. journal entry

And based on earlier phases, they also remain absent or weak in the inspected metadata/runtime path.

## 6. Main Behavior Findings

Round 2 Phase 3 reveals five important truths.

### 6.1 Core Round 2 Family Paths Are Real

The strongest Round 2 document, aging, and inventory surfaces are not theoretical.

They are backed by executable tests.

### 6.2 The Biggest Remaining Risk Is Not Immediate Breakage

The biggest remaining risk is architectural unevenness:

1. mixed detail branching
2. partial activation
3. metadata/runtime mismatch

This is more important than isolated pass/fail on the strongest paths.

### 6.3 Delivery Note Is A Good Shared Runtime Success Example

Delivery note now has:

1. metadata presence
2. semantic resolution coverage
3. transaction-listing family adaptation
4. transaction-listing family validation
5. detail drilldown coverage
6. evidence-follow-up coverage

This makes it one of the strongest Round 2 reference surfaces.

### 6.4 Inventory Snapshot Is More Mature Than It First Appears

Both warehouse and item inventory paths have verified resolution behavior.

That means Round 2 inventory should be treated as an active shared family surface, not a weak side path.

### 6.5 Payment Entry And Purchase Invoice Must Be Classified Carefully

These are exactly the kinds of surfaces where the system can look "partly supported" from one angle and "missing" from another.

This phase confirms:

1. purchase invoice is not absent everywhere
2. payment entry is not fully active everywhere

So they need precise priority treatment in Phase 4 rather than blanket claims.

## 7. Practical Truth Status

Current truth status:

1. Round 2 strong family paths are verified enough to support gap prioritization
2. partial paths remain partial
3. no evidence from this phase justifies claiming purchase receipt or journal entry suppor
4. the remaining work is now mainly classification and sequencing, not fresh discovery of the strongest paths
