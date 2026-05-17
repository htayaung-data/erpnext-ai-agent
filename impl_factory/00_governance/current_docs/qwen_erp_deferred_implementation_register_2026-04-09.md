# Qwen ERP Deferred Implementation Register

Status: active deferred implementation register
Date: 2026-04-09
Scope: record concrete governed items that were intentionally deferred during Phase 1 and should be reopened later through explicit design rather than memory or ad hoc fixes

## 1. Purpose

This register exists to keep deferred work visible and reopenable.

Use it when:

1. a bounded slice proves valuable but should not widen ye
2. tenant data is absent or unreliable
3. authority is real but narrower than the user question
4. a future phase should pick the work up cleanly without rediscovery

This is the active place to park deferred implementation items.

Do not rely on scattered phase-note mentions alone.

## 2. Deferral Rule

A deferred item is valid only when all of the following are true:

1. the business ask is real
2. the current governed authority is insufficient or not yet approved
3. implementing it now would widen the runtime unsafely
4. there is a clear reopen trigger
5. there is a likely future phase or bounded design checkpoint where it belongs

If those conditions are not true, the item should be:

1. implemented now
2. rejected as out of scope
3. or removed as stale

## 3. Current Deferred Items And Reopen Trace

### 3.1 Delivery Trip Coverage

Origin:

1. Phase `1.1` Delivery / Fulfillmen

Current state:

1. deferred

Why deferred:

1. live deployment did not provide enough active `Delivery Trip` evidence to justify governed rollou
2. building the slice without live records would encourage speculative runtime behavior

Reopen trigger:

1. live `Delivery Trip` rows exist in the tenan
2. a bounded operational ask is confirmed
3. report or direct-query authority is verifiable in ERP

Recommended future home:

1. future operational coverage chapter after an explicit design note

### 3.2 Sales Order Actual Delivery-Event Proof

Origin:

1. Phase `1.2` Sales Order Status

Current state:

1. deferred beyond current order-authority coverage

Why deferred:

1. `Sales Order` authority supports planned delivery date and delivered percentage
2. it does not by itself prove the actual shipment event date
3. widening directly into downstream fulfillment evidence would have mixed two authority seams too early

Reopen trigger:

1. a bounded follow-on slice is approved for sales-order-to-delivery evidence
2. downstream `Delivery Note` linkage is explicitly governed for this path
3. browser/UAT confirms no hidden composite drif

Recommended future home:

1. future fulfillment-evidence extension after explicit design approval

### 3.3 Purchase Order Actual Receipt-Event Proof

Origin:

1. Phase `1.3` Purchase Order Tracking

Current state:

1. deferred beyond current purchase-order authority

Why deferred:

1. `Purchase Order` authority supports planned receipt date and received percentage
2. it does not by itself prove the actual receipt event date
3. purchase-receipt evidence should not be smuggled into order-status logic without a bounded source-of-truth design

Reopen trigger:

1. a bounded purchase-receipt evidence slice is approved
2. downstream `Purchase Receipt` linkage is explicitly governed
3. live verification proves that event-date answers are stable and auditable

Recommended future home:

1. future procurement evidence extension after explicit design approval

### 3.4 Customer Credit Limit Extension

Origin:

1. Phase `1.4E` Customer Credit Status

Current state:

1. reopened and completed on 2026-04-09 for the current tenan
2. no longer an active deferred item

Original defer reason:

1. live `Customer Credit Limit` rows are absen
2. credit-limit comparison without real tenant data would be fabricated policy
3. credit utilization and breach logic require both data presence and approved business basis

Reopen trigger that was satisfied:

1. real `Customer Credit Limit` records exist in the tenan
2. the business basis is approved explicitly:
   - outstanding vs credit limi
   - total due vs credit limi
   - overdue vs credit limi
3. the approved definition is recorded in the business-definition and formula registries

Implemented outcome:

1. `1.4E` was implemented as a bounded read-only extension on the customer detail path
2. approved runtime basis:
   - `Outstanding Amount > Configured Credit Limit`
3. supporting governed context:
   - `payment_terms`
   - `default_price_list`
   - available credi
   - utilization
4. still deferred beyond this implemented slice:
   - approval / hold decisioning
   - collection recommendations
   - alternative policy bases without explicit approval

### 3.5 HR / Headcount / Employee Coverage

Origin:

1. unsupported but recognized business domain during Phase `1`

Current state:

1. deferred as a future governed domain, not a current capability

Why deferred:

1. the ontology recognizes the domain, but governed HR answer paths are not implemented
2. employee and headcount questions need their own authority model, privacy posture, and report-surface verification
3. it should not be mixed into customer-credit or formula work opportunistically

Reopen trigger:

1. an HR preflight confirms active doctypes and report surfaces
2. privacy and access boundaries are documented
3. a dedicated design note approves the first bounded HR slice

Recommended future home:

1. later operational expansion after Phase `2` or later, not before

### 3.6 Advisory Credit Policy And Predictive Collection Behavior

Origin:

1. bounded credit and reasoning guardrails during Phase `1.4` and Phase `1.5`

Current state:

1. deferred

Why deferred:

1. recommendations such as who should receive credit, who will likely pay, or what collections action should happen next are policy-heavy
2. current governed authority supports exposure visibility, not approved predictive or management policy
3. these asks would drift quickly without stable definitions, thresholds, and owner-approved formulas

Reopen trigger:

1. Phase `2` business-definition and threshold registries are active
2. policy ownership is documented
3. bounded recommendation rules are approved explicitly

Recommended future home:

1. later advisory layer after formula and threshold governance, not before

### 3.7 Customer-Created Tenure Basis

Origin:

1. Phase `2.2A` Core KPI Definitions

Current state:

1. resolved on 2026-04-10
2. active in the governed KPI registry and customer lifecycle suppor

Resolution note:

1. a governed customer-master read capability now exists
2. customer creation date is now exposed through governed metadata and customer lifecycle suppor
3. the basis is active without silently overriding generic tenure clarification

Recommended future home:

1. closed as part of the 2026-04-10 blocked-item reactivation slice

### 3.8 User-Facing Overdue Severity Activation

Origin:

1. Phase `2.3` Threshold And Risk Semantics

Current state:

1. deferred for user-facing activation
2. threshold metadata exists, but activation remains blocked by policy
3. approval-pack note now exists:
   - [qwen_erp_overdue_severity_policy_pack_2026-04-10.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/qwen_erp_overdue_severity_policy_pack_2026-04-10.md)

Why deferred:

1. AR aging authority is strong enough to support overdue-ratio calculation
2. however labels such as `watch`, `elevated`, and `critical` are still business-policy claims
3. those labels should not reach runtime answers until finance explicitly approves the policy bands

Reopen trigger:

1. finance approves overdue severity labels and numeric bands explicitly
2. the approved labels are confirmed for user-facing wording
3. browser/UAT confirms blocked-safe behavior can widen without advisory drif

Recommended future home:

1. later Phase `2` or post-Phase `2` risk-presentation activation slice

### 3.9 Collection Ratio Runtime Activation

Origin:

1. Phase `2.2A` Core KPI Definitions
2. Phase `2.3` Threshold And Risk Semantics

Current state:

1. resolved on 2026-04-10 for definition and formula activation
2. collection-ratio threshold labels remain separately deferred by policy

Resolution note:

1. an approved governed source basis now exists using allocated customer receipt amounts against submitted sales invoices for the requested invoice period
2. capability and report metadata now record the finance authority path explicitly
3. threshold labels remain blocked-safe until finance approves user-facing wording

Recommended future home:

1. closed for KPI activation; threshold presentation remains deferred under user-facing policy control

### 3.10 Metadata-Owned Consultant Detail Intent Role Mapping

Origin:

1. UX-S5A Semantic Detail Intent Contract
2. NBU stabilization freeze consultant-response hardening

Current state:

1. closed by UX-S5D Lexical Debt Audit And Removal
2. semantic detail intent now carries typed slots such as `answer_goal`, `evidence_depth`, `business_role`, `target_reference`, and `risk_level`
3. `business_role` defaults are now resolved from the metadata-owned `consultant_role_registry.json`
4. protected runtime code no longer owns the family/capability-to-role selection table

Resolution note:

1. UX-S5D moved consultant role selection into `consultant_role_registry.json`
2. the Python runtime now only calls the registry lookup using governed source metadata and semantic tags
3. focused registry tests and semantic activation tests prove the role comes from metadata/contract fields, not user wording

Reopen trigger:

1. any new family-specific consultant role is requested beyond the current registry
2. a future audit finds role selection reintroduced as code-owned branching in protected paths

Required closure condition:

1. satisfied in UX-S5D

Recommended future home:

1. keep closed unless new family role ownership is added outside the registry

### 3.11 Metadata-Owned Entity Drilldown Capability Binding

Origin:

1. UX-S5B Governed Evidence Drilldown Registry
2. prior entity detail request support bridge

Current state:

1. closed by UX-S5D Lexical Debt Audit And Removal
2. the governed drilldown registry uses typed semantic intent and active scope metadata to decide whether a row can be expanded
3. entity grain to capability binding is now resolved from `entity_detail_capability_bindings.json`
4. the existing `entity_detail_capability_id` function remains only as a compatibility wrapper over the metadata registry

Resolution note:

1. UX-S5D moved entity-grain-to-capability bindings into a metadata-owned registry file
2. unsupported entity grains still fail closed
3. focused registry tests prove entity drilldown capability availability is selected from metadata, not user wording

Reopen trigger:

1. a new entity grain or family drilldown is added outside `entity_detail_capability_bindings.json`
2. a future audit finds code-owned entity/capability branching reintroduced in protected paths

Required closure condition:

1. satisfied in UX-S5D

Recommended future home:

1. keep closed unless new entity detail binding ownership is added outside the registry

### 3.12 Universal Governed Filtering Expansion

Origin:

1. browser UAT after UX-S5 consultant reasoning checkpoint
2. filtered ranking and filter follow-up discussion on 2026-05-07

Current state:

1. deferred as a dedicated post-UX-S7 mini-phase
2. current system has partial filter support through report metadata, direct query fields, and semantic aliases
3. current system does not yet have a universal filter contract across all families
4. filter follow-ups currently require minimal safety so they do not drift to stale artifacts

Deferred scope:

1. territory, region, country, warehouse, item group, brand, product category, customer group, supplier group, document status, aging type, aging buckets, payment terms, company, period, and future family dimensions where appropriate
2. pre-aggregation filter versus post-aggregation filter
3. group-by versus filter-by distinction
4. value validation and join path declaration
5. applied-filter provenance in normalized artifacts

Reopen trigger:

1. UX-S6 context authority is green
2. UX-S7 cross-family regression and browser UAT are green
3. the team is ready to start `FILTER-S0`

Recommended future home:

1. `FILTER-S0` Governed Filter Inventory
2. `FILTER-S1` Filter Contract And Provenance
3. `FILTER-S2` Filtered Requery Execution

### 3.13 Management Intelligence Analysis Viewpoints

Origin:

1. UX-S5 consultant depth discussion
2. management intelligence roadmap discussion on 2026-05-07

Current state:

1. deferred until context authority and governed filtering are stable
2. existing business-definition and formula foundations should be reused
3. current consultant renderer is improving, but does not yet provide the full reusable MI viewpoint layer

Deferred scope:

1. trend
2. variance
3. contribution
4. concentration
5. aging and time quality
6. margin quality
7. cash conversion
8. risk priority
9. action plan
10. later root-cause drilldown, scenario, sensitivity, and guarded prediction

Reopen trigger:

1. `FILTER-S2` is green or the MI slice explicitly does not require filtered scope
2. formula inputs and data provenance are available for the selected MI viewpoint

Recommended future home:

1. `MI-S0` Management Intelligence Contract Baseline
2. `MI-S1` Core Analysis Viewpoints
3. `MI-S2` Business Consultant Renderer
4. `MI-ADV-S0` Advanced Consultant Drilldown

### 3.14 Family Onboarding Standard And Test Harness

Origin:

1. future HR, CRM, and Manufacturing expansion discussion on 2026-05-07
2. concern that new families must not require start-from-scratch implementation

Current state:

1. deferred until context authority, filtering, and MI contracts are mature enough to become onboarding requirements
2. an NBU onboarding guide exists, but it should not be treated as final family onboarding standard yet

Deferred scope:

1. family identity
2. capability declarations
3. data sources
4. dimensions
5. metrics
6. filters
7. supported intents
8. follow-up modes
9. renderers
10. policy boundaries
11. consultant playbooks
12. automated tests
13. browser UAT examples

Reopen trigger:

1. `MI-S2` is green
2. the team is ready to onboard a new family or pilot family without breaking existing families

Recommended future home:

1. `FAM-S0` Family Onboarding Standard
2. new-family test harness and pilot onboarding slice

## 4. How Future Work Should Use This Register

Before starting a new phase:

1. check whether a proposed feature already exists here as deferred work
2. confirm the reopen trigger instead of re-discovering the problem from scratch
3. either move the item into an approved design note or leave it deferred

When a deferred item is reopened:

1. link the new design note here
2. change its state from `deferred` to `active`
3. record the closure or stop rule when the bounded slice ends

## 5. Current Recommendation

The current decision is:

1. keep the remaining deferred items visible
2. treat overdue severity as the remaining Phase `2` blocked item pending explicit finance policy
3. use the overdue-severity policy pack as the central approval and future-adjustment note for label or band changes
4. do not start universal filtering until UX-S6 and UX-S7 are green
5. do not start MI viewpoints until governed scope and filter provenance are stable enough for safe calculation
6. do not finalize new-family onboarding until filtering and MI contracts are mature enough to become required onboarding gates
