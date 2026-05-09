# Qwen ERP AI Assistant Enterprise Context, Filtering, MI, And Onboarding Roadmap

Date: 2026-05-07
Last Updated: 2026-05-09
Status: active next-sequence implementation roadmap
Branch: `feature/ai-assistant`
Owner: AI Assistant stabilization and enterprise architecture track

## 1. Purpose

This document defines the implementation sequence after the UX-S5 consultant-reasoning checkpoint.

It exists because browser UAT proved that the assistant is improving, but still has foundational reliability blockers:

1. visible-table references can bind to stale artifacts;
2. generic follow-ups can drift to unrelated families;
3. technical fallback wording can leak to users;
4. line-item follow-ups can lose the active object;
5. filter follow-ups can be misunderstood or answered from an unrelated context.

The goal is not to add more isolated features. The goal is to make the assistant reliable enough that future filtering, MI, HR, CRM, and Manufacturing expansion can be added through shared contracts and metadata rather than one-off family patches.

After browser UAT on 2026-05-09, this roadmap now treats `UX-S6A Orchestration Foundation Enforcement` as the mandatory first gate inside `UX-S6`. This gate exists because row, entity, table, and drilldown follow-ups must be solved as a generic conversation-orchestration problem, not as individual fixes for phrases such as "second row", "third row", or "above table".

## 2. Current Position

Implemented and pushed:

1. NBU stabilization guardrails;
2. visible-context and projection foundations;
3. UX-S5 consultant reasoning contracts;
4. semantic detail intent contract;
5. governed evidence drilldown registry;
6. metadata-backed consultant playbooks;
7. metadata-owned consultant role and entity-detail capability bindings.

Still not enterprise-complete:

1. latest visible table authority;
2. follow-up intent anchoring;
3. professional fallback wording;
4. focused line-item continuation;
5. universal governed filtering;
6. Management Intelligence analysis contracts;
7. family onboarding standard and harness.

## 3. Non-Negotiable Implementation Principles

Every slice must follow these rules:

1. no prompt-specific keyword fixes;
2. no family-specific user phrase routing in protected runtime paths;
3. no unsupported option should be offered to the user;
4. no stale artifact should answer a current follow-up;
5. every answer should be grounded in current artifact authority, governed requery, or explicit unsupported-safe fallback;
6. new family behavior should be added through metadata, contracts, adapters, and tests;
7. browser UAT failures should be fixed at the shared seam, not by hardcoding the failing sentence.

Family-specific adapters are allowed when raw ERP shapes differ, but they must sit behind shared contracts and must not own user-language behavior.

Every proposed roadmap change, design, and implementation plan must pass the Enterprise Gate before coding starts:

1. Problem class: state the general system failure being solved, not the individual UAT sentence.
2. Rejected MVP approach: explicitly name the shortcut that must not be used.
3. Enterprise design: describe the shared, governed, reusable mechanism.
4. Metadata / contract dependency: identify what must come from artifacts, registries, contracts, adapters, or family metadata rather than code assumptions.
5. Cross-family tests: define the proof across finance, AR/AP, product, customer, supplier, transaction, unsupported, typo, and challenge flows where applicable.
6. Definition of done: define objective exit conditions before the slice can be called complete.

If any of these six items is missing, the work is not authorized as enterprise-grade implementation.

## 4. Implementation Sequence

### UX-S6: Context Authority Stabilization

Goal:

Make the assistant reliably understand the current conversation object before expanding capability.

`UX-S6` is no longer allowed to proceed as a collection of independent browser-failure fixes. It starts with `UX-S6A`, an enforced orchestration foundation gate. Only after `UX-S6A` passes may the remaining UX-S6 cleanup work continue.

#### UX-S6A: Orchestration Foundation Enforcement

Problem class:

The failure class is conversation orchestration instability. The assistant can have valid ERP data and still answer wrongly if it binds a follow-up to a stale table, stale drilldown, old family, or rendered prose instead of the current structured ERP artifact.

Rejected MVP approach:

Do not add phrase fixes for ordinal words, table-reference words, family labels, or known UAT sentences. Do not parse rendered assistant text as the primary source of truth. Do not add `if AR`, `if AP`, `if product`, or `if customer` behavior in user-language paths. Do not treat each browser failure as a new isolated branch.

Enterprise design:

Create an enforceable orchestration foundation that resolves follow-ups through structured artifacts and typed contracts before any renderer or family handler answers. The foundation must:

1. maintain a conversation evidence ledger of visible ERP artifacts, tables, sections, rows, columns, source family, source report, evidence scope, and supported follow-up actions;
2. normalize user follow-ups into typed reference and intent objects without deciding family behavior from user keywords;
3. resolve the target artifact by structured authority signals such as visibility, recency, explicit reference, entity continuity, selected row, evidence scope, and capability compatibility;
4. allow family-specific ERP shape adapters only behind shared contracts;
5. pass the selected artifact, row, entity, and evidence scope to consultant, detail, comparison, or safe-fallback renderers.

Metadata / contract dependency:

`UX-S6A` requires these contracts or their equivalent runtime structures:

1. `VisibleArtifactContract`: report id, family id, capability id, table id, section id, row id, column ids, display labels, semantic measure roles, entity roles, rank, and evidence scope.
2. `ReferenceIntentContract`: abstract follow-up intent such as selected row, selected entity, latest visible table, previous visible table, line-item continuation, explanation, comparison, detail expansion, unsupported prediction, or clarification.
3. `ContextAuthorityContract`: rules for choosing among candidate artifacts using structured authority signals instead of rendered text similarity.
4. `FamilyCapabilityContract`: metadata-owned declarations for what each family can answer, drill into, compare, filter, refuse, or hand off.
5. `EvidenceScopeContract`: summary-level, row-level, source-detail, calculated, unsupported-prediction, or clarification-required evidence state.

Cross-family tests:

Before `UX-S6A` can pass, automated and browser UAT coverage must prove the behavior across:

1. AR aging: latest table row selection, risk explanation, source invoice detail, unsupported default prediction.
2. AP aging: latest supplier table row selection, supplier concern explanation, source purchase invoice detail.
3. Product rankings: row selection after formatting transformations such as showing values in millions.
4. Finance statements: P&L explanation, COGS continuation, Cash Flow insight, Balance Sheet conclusion.
5. Mixed-family switching: AR to AP to product to AR must answer from the latest intended artifact, not stale context.
6. Drilldown interruption: after invoice detail, a new visible ranking or aging table must regain context authority.
7. Ambiguous references: ask clarification only when structured context is genuinely ambiguous.

Definition of done:

`UX-S6A` is complete only when:

1. the runtime can resolve visible-context follow-ups from structured artifacts rather than old rendered prose;
2. ordinal and entity references work generically for all row positions supported by the visible artifact, not only `first`, `second`, or `third`;
3. current artifact authority beats older drilldown artifacts unless the user explicitly refers to the older artifact;
4. unsupported predictions produce business-friendly fallback language with useful next evidence suggestions;
5. focused tests and guardrails pass;
6. browser UAT passes the mixed-family conversation checklist;
7. any remaining limitation is documented in the deferred register instead of hidden inside runtime behavior.

Scope:

1. latest visible table authority;
2. generic follow-up anchoring;
3. professional safe fallback;
4. focused line-item continuation;
5. minimal filter-follow-up safety.

Required behaviors:

1. after a comparison table, "who is second in the above table?" binds to that comparison table;
2. after AR/AP, "give me more insight" stays on AR/AP;
3. unsupported prediction requests use business-friendly wording;
4. after COGS detail, "break down details" remains attached to COGS;
5. filter follow-ups inspect the latest artifact/provenance or say the filter was not proven, instead of drifting to another family.

Exit gate:

1. focused automated tests pass;
2. enterprise guardrail passes;
3. browser UAT passes for latest table, more insight, fallback, COGS continuation, and filter-follow-up safety;
4. `UX-S6A` definition of done is satisfied;
5. no lexical or keyword routing is introduced.

### UX-S7: Cross-Family Regression And Browser UAT

Goal:

Freeze UX-S6 behavior across all currently governed families.

Coverage:

1. finance statements;
2. AR and AP aging;
3. AR/AP working capital;
4. customer and supplier master data;
5. product rankings;
6. transaction listings;
7. inventory;
8. unsupported prediction and recommendation boundaries;
9. typo and clarification flows;
10. user challenge recovery.

Exit gate:

1. automated regression matrix passes;
2. browser UAT checklist passes;
3. known limitations are documented;
4. any accepted exception is explicit.

### FILTER-S0: Governed Filter Inventory

Goal:

Define filtering as a platform capability, not as region-only logic.

Inventory must cover where appropriate:

1. period and report date;
2. company;
3. customer, supplier, item, product;
4. customer group, supplier group, item group, brand, product category;
5. territory, region, country, warehouse;
6. document status and document type;
7. aging type and aging buckets;
8. payment terms and commercial policy fields;
9. ownership or organizational dimensions where future families support them.

Exit gate:

1. filterable fields are listed per family;
2. each filter has source field, allowed operators, value validation strategy, and join path;
3. unsupported filters fail closed with user-friendly language.

### FILTER-S1: Filter Contract And Provenance

Goal:

Create a shared filter contract for all families.

Contract must distinguish:

1. grouping dimension;
2. filter condition;
3. projection column;
4. ranking subject;
5. metric;
6. pre-aggregation filter;
7. post-aggregation filter;
8. local artifact filter versus governed requery.

Exit gate:

1. applied filters appear in artifact provenance;
2. answer text can show the business scope;
3. follow-up questions can inspect whether a filter was actually applied.

### FILTER-S2: Filtered Requery Execution

Goal:

Execute governed filters only where the family declares support.

Examples:

1. top customers by revenue in a territory;
2. products by revenue for an item group or brand;
3. inventory by warehouse;
4. invoices by status;
5. AR/AP by party group or aging bucket where supported.

Exit gate:

1. supported filtered queries execute correctly;
2. unsupported filtered queries fail safely;
3. filtered ranking does not confuse group-by with filter-by.

### MI-S0: Management Intelligence Contract Baseline

Goal:

Make MI a governed reasoning layer, not free-form advice.

Inputs:

1. business definition registry;
2. formula registry;
3. approved KPI calculations;
4. normalized family artifacts;
5. governed filters and provenance.

Exit gate:

1. MI requests produce a typed analysis plan;
2. formula inputs are explicit;
3. calculated values include formula, inputs, output, and interpretation;
4. unsupported MI requests fail safely.

### MI-S1: Core Analysis Viewpoints

Goal:

Implement reusable senior-consultant viewpoints.

Required viewpoints:

1. trend;
2. variance;
3. contribution;
4. concentration;
5. aging and time quality;
6. margin quality;
7. cash conversion;
8. risk priority;
9. action plan.

Exit gate:

1. each viewpoint is contract-backed;
2. each viewpoint works across applicable families;
3. each viewpoint has tests for finance, AR/AP, product, customer, supplier, and transaction contexts where applicable.

### MI-S2: Business Consultant Renderer

Goal:

Render MI outputs like a senior business consultant.

Structure:

1. executive diagnosis;
2. key evidence;
3. business interpretation;
4. risk or opportunity;
5. management priorities;
6. one executable next step where available.

Exit gate:

1. answers are readable and not robotic;
2. answers do not merely repeat report rows;
3. next-step questions are context-natural and executable;
4. no unsupported management authority is invented.

### MI-ADV-S0: Advanced Consultant Drilldown

Goal:

Add deeper source-backed analysis after MI core is stable.

Scope:

1. root-cause drilldown;
2. source transaction expansion;
3. scenario and sensitivity analysis;
4. budget or target comparison if approved data exists;
5. guarded prediction only if approved model and policy exist.

Exit gate:

1. no causal claim without evidence;
2. no prediction without approved model/policy;
3. partial answers clearly state missing evidence.

### STAB-S0: Release Stabilization

Goal:

Make the system stable enough for broader production usage.

Scope:

1. broader release gates;
2. slow gate reliability;
3. lane consolidation;
4. remaining lexical-debt audit;
5. service orchestration cleanup;
6. repeatable browser UAT pack;
7. documentation truth review.

Exit gate:

1. guardrail green;
2. focused tests green;
3. broader regression gate green or documented with accepted timeout limitations;
4. no known critical browser UAT failure remains.

### FAM-S0: Family Onboarding Standard

Goal:

Make HR, CRM, Manufacturing, or future ERP families pluggable through contracts.

Onboarding standard must require:

1. family identity;
2. capability declarations;
3. data source declaration;
4. dimensions;
5. metrics;
6. filters;
7. supported intents;
8. follow-up modes;
9. renderers;
10. boundaries and policy restrictions;
11. consultant playbooks;
12. regression tests;
13. browser UAT examples.

Exit gate:

1. onboarding doc is approved;
2. test harness exists;
3. adding a sample family proves no existing family breaks.

## 5. What Comes After This Roadmap

After `FAM-S0`, the next macro roadmap should be:

1. onboard one new family as a pilot, preferably the least risky family with strong data availability;
2. validate the family onboarding harness;
3. expand to the next operational family;
4. only then consider larger capabilities such as write actions, charts, OCR, or multilingual output.

Do not start write actions, forecasting, or broad automation until context authority, filtering, MI, and onboarding standards are stable.

## 6. Immediate Next Step

The immediate implementation task is `UX-S6A Orchestration Foundation Enforcement`, inside `UX-S6`.

Start with:

1. structured visible artifact authority;
2. generic reference and intent contracts;
3. context authority resolution that does not depend on rendered prose;
4. cross-family regression for AR, AP, product rankings, and finance statements;
5. professional unsupported fallback wording;
6. focused line-item continuation;
7. minimal filter-follow-up safety only where needed to prevent context drift.

Do not begin universal filtering or MI implementation until UX-S6A, the remaining UX-S6 cleanup, and UX-S7 are green.
