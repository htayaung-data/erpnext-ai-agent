# Qwen ERP Phase 5 Reconciled Implementation Plan (2026-03-24)

Status: proposed reconciliation plan  
Scope: align the pushed Phase 4B governed Qwen architecture, the local metadata-driven Phase 5 work, and the clarified product rules around covered families, graceful fallback, and contextual clarification  
Decision: continue with enterprise-governed architecture, but stop allowing business-language understanding to drift into Python phrase patches

Update on 2026-03-24:

This plan now has an active re-entry guardrail companion:
- [qwen_erp_phase5_enterprise_reentry_guardrails_2026-03-24.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/qwen_erp_phase5_enterprise_reentry_guardrails_2026-03-24.md)

That guardrail document should be treated as the stricter rulebook before any new runtime implementation resumes. In particular:

1. no token-rule registries as the primary interpretation architecture
2. no phrase-heavy Python follow-up logic
3. metadata cleanup must happen before contract reintroduction

## 1. Executive Decision

The correct direction is:

1. keep the current Qwen-only governed architecture from Phase 4B
2. keep the local metadata-driven Phase 5 additions that move business semantics into registries
3. remove or rewrite the local exploratory logic that reintroduces phrase-heavy behavior in Python
4. add first-class governed handling for:
   - covered family execution
   - out-of-scope fallback
   - fresh-query clarification
   - contextual follow-up clarification

This plan explicitly rejects two extremes:

1. do not go back to tactical keyword fixing
2. do not pretend all ERP domains are already governed

The product model should be:

1. strong governed execution for covered families
2. honest, useful fallback for uncovered families
3. natural clarification for ambiguous fresh questions
4. contextual clarification for ambiguous follow-ups

## 2. Governing Product Rule

The visible assistant must support exactly four user-facing outcomes:

1. `governed_execute`
2. `clarify`
3. `contextual_followup_clarify`
4. `governed_out_of_scope`

The system must never expose:

1. compiler internals
2. capability ids
3. raw ambiguity diagnostics
4. blunt "grounded ERP lookup failed" wording for understandable user requests

The system must also never rely on:

1. ad hoc Python `if "term" in text`
2. large hardcoded domain token sets as the primary architecture
3. case-specific phrase patches

## 3. Reconciled Architecture

### 3.1 What remains unchanged

Keep these as core enterprise infrastructure:

1. `Qwen-Agent proposes`
2. `compiler enforces`
3. `validator confirms`
4. report-family abstraction
5. normalized family artifacts
6. single-company invariant injection
7. governed composite execution
8. natural narrative from governed artifacts

### 3.2 What changes

Move business-language understanding toward:

1. metadata registries
2. ontology-driven concept matching
3. prior-artifact continuation contracts
4. structured clarification reasons
5. structured scope/fallback decisions

Reduce or remove:

1. service-layer exploratory confirmation logic
2. phrase-heavy follow-up detection in Python
3. debug-heavy audit/log branches added during local Qwen experimentation
4. raw internal exception leakage to API clients

## 4. Keep / Change / Remove

### 4.1 Keep

Keep and integrate these local additions:

1. [semantic_alias_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/semantic_alias_registry.json)
2. [semantic_aliases.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/semantic_aliases.py)
3. [intent_bias_rules_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/intent_bias_rules_registry.json)
4. [intent_rules_engine.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_rules_engine.py)
5. [clarification_templates_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/clarification_templates_registry.json)
6. [clarification_system.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/clarification_system.py)
7. ontology extensions in [business_ontology.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/business_ontology.json)

### 4.2 Change

Refactor these to fit the enterprise model:

1. [followup_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/followup_interpreter.py)
2. [service.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py)
3. [family_followup.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_followup.py)
4. [compiler.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/compiler.py)
5. [fresh_query_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py)

### 4.3 Remove or rollback

Do not keep these patterns in final enterprise form:

1. raw exception text returned from [api.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/api.py)
2. confirmation-detection microflow in [service.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py) that depends on an ad hoc classifier prompt
3. debug-only logging branches added to force-fit follow-up execution
4. phrase-specific metric/time/domain interpretation remaining in Python where a registry or continuation contract should own it

## 5. Concrete Workstreams

### Workstream A: Reconciliation Cleanup

Goal:

Bring the local Phase 5 additions into the current Phase 4B codebase without preserving exploratory regressions.

Changes:

1. restore safe API error behavior in [api.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/api.py)
2. remove debug-oriented confirmation scaffolding from [service.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py)
3. keep registry modules and wire them through clean interfaces
4. document the new metadata-first rule in governance

Acceptance:

1. no raw internal exception text exposed to users
2. no exploratory confirmation loop code left in service orchestration
3. registry-driven modules remain available and testable

### Workstream B: Governed Scope and Fallback Contract

Goal:

Make covered vs uncovered ERP domains a first-class governed decision.

New contract:

`GovernedScopeDecisionContract`

Minimum outcomes:

1. `covered_family`
2. `clarification_needed`
3. `out_of_scope_but_valid_erp_domain`
4. `unsupported_request`

Data sources:

1. family registry
2. business ontology
3. semantic alias registry
4. future scope router hooks

Behavior:

1. covered family -> execute
2. uncovered but valid ERP domain -> graceful fallback
3. unclear request -> clarification
4. unsupported/non-ERP ask -> safe generic handling

Example user-facing fallback:

- "I understand you're asking about staff headcount. That HR area is not yet available in the current governed ERP assistant. I can still help with finance, sales, receivables/payables, inventory, and product performance."

Acceptance:

1. no more accidental reuse of the previous artifact for uncovered domains
2. out-of-scope queries produce helpful business-language fallback
3. no technical leakage

### Workstream C: Clarification Reason Contract

Goal:

Stop generating clarifications in an ad hoc way from service-layer failure branches.

New contract:

`ClarificationReasonContract`

Reason types:

1. `missing_time_scope`
2. `missing_metric_choice`
3. `missing_entity_scope`
4. `ambiguous_followup_transform`
5. `ambiguous_business_area`
6. `unsupported_drilldown_detail`

Flow:

1. compiler/follow-up layer produces structured clarification reason
2. clarification system turns it into business-language question
3. UI sees optional suggested actions/options

Important:

The clarification system remains AI-first with template fallback, but it is driven by structured reason types rather than arbitrary failure text.

Acceptance:

1. no user sees raw compiler internals
2. understandable ambiguous requests ask business-language clarification
3. follow-up ambiguities reference prior context naturally

### Workstream D: Structured Continuation Contract

Goal:

Replace brittle follow-up interpretation with prior-artifact continuation state.

New contract:

`ArtifactContinuationContract`

Minimum fields:

1. prior artifact family
2. prior entity focus
3. prior metric
4. prior dimensions
5. prior time scope
6. prior table shape / presentation shape
7. allowed local transformations

Use cases:

1. "show in million"
2. "show me by supplier"
3. "include qty column"
4. "how about last year"
5. "show me with table"

Rule:

If a follow-up is plausibly a continuation over the prior artifact, resolve it through continuation state first.
Only if continuation is still ambiguous should the system ask a contextual clarification.

Example clarification:

- "Do you want me to add Quantity to the previous product performance table?"
- "Do you want the same revenue ranking for full-year 2025?"

Acceptance:

1. same-session follow-ups stop relying mainly on phrase checks
2. ambiguous follow-ups clarify contextually instead of failing
3. compatible presentation/column/time refinements stay local whenever safe

### Workstream E: Metadata-Driven Follow-Up Interpretation

Goal:

Shrink Python phrase logic in [followup_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/followup_interpreter.py) and move it into metadata or continuation semantics.

Approach:

1. move canonical metric/time/presentation aliases into registries
2. reuse ontology and semantic aliases for concept recognition
3. keep only minimal generic parsing code in Python:
   - top/bottom number extraction
   - id extraction
   - safe normalization helpers

Explicit non-goal:

Do not replace Python keyword sets with giant JSON keyword sets and call that "enterprise."
Metadata must represent semantic concepts, not ad hoc phrase patches.

Acceptance:

1. business semantics mostly loaded from metadata
2. Python remains an interpreter of metadata plus structural context
3. grep count of phrase-heavy logic materially drops

### Workstream F: Entity Drilldown Enrichment

Goal:

Keep the current entity drilldown path, but make it the canonical answer for detail/history questions instead of falling back incorrectly.

Scope:

1. invoice detail
2. customer detail
3. supplier detail
4. item detail

Enhancements:

1. support richer detail requests through structured drilldown reasoning
2. enrich invoice detail with fulfillment/delivery status when governed ERP fields or linked docs support it
3. enrich entity detail with recent history where already covered by governed data access

Acceptance:

1. invoice detail and customer/supplier detail remain on governed entity path
2. "is it delivered?" resolves through entity detail enrichment or gracefully explains what is not yet governed

## 6. Workstream Order

Implement in this order:

1. Workstream A: Reconciliation cleanup
2. Workstream B: governed scope and fallback contract
3. Workstream C: clarification reason contract
4. Workstream D: structured continuation contract
5. Workstream E: metadata-driven follow-up interpretation
6. Workstream F: entity drilldown enrichment
7. browser acceptance pass

Rationale:

1. first clean the architecture boundary
2. then define the allowed user-facing outcomes
3. then improve follow-up/context
4. then enrich drilldown details

## 7. File Ownership

### Primary files to edit

1. [service.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py)
2. [followup_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/followup_interpreter.py)
3. [fresh_query_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py)
4. [compiler.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/compiler.py)
5. [family_followup.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_followup.py)
6. [entity_detail.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_detail.py)
7. [contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py)
8. [api.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/api.py)

### Primary metadata files

1. [business_ontology.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/business_ontology.json)
2. [semantic_alias_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/semantic_alias_registry.json)
3. [intent_bias_rules_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/intent_bias_rules_registry.json)
4. [clarification_templates_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/clarification_templates_registry.json)

### New files expected

1. `qwen_chat/scope_contracts.py` or equivalent contract grouping
2. `qwen_chat/continuation_state.py` or equivalent helper
3. metadata for scope/fallback mapping if not embedded into existing ontology cleanly

## 8. Browser Acceptance Before Closure

The following scenarios must pass before calling this reconciliation successful:

1. covered family factual query:
   - `How much payable do we have as of now`

2. uncovered ERP domain graceful fallback:
   - `How many staff do we have`

3. ambiguous fresh question clarification:
   - `Analyze company health and suggest areas to improve`

4. contextual follow-up clarification:
   - prior product table -> `include qty column`

5. contextual time-scope follow-up:
   - `Top 7 customers by revenue last month` -> `how about 2025`

6. presentation-only follow-up:
   - `Show me with table and bullet points`

7. invoice detail and fulfillment:
   - `give me details of ACC-SINV-2026-00120`
   - `is it already delivered?`

8. valid uncovered detail fallback:
   - if delivery status is not yet governed, answer honestly and explain nearby supported details

## 9. Exit Criteria

This reconciliation is complete when:

1. local metadata-driven additions are integrated cleanly into the Phase 4B base
2. no new enterprise logic depends mainly on Python keyword/phrase checks
3. uncovered ERP-domain questions fall back gracefully
4. ambiguous fresh questions clarify naturally
5. ambiguous follow-ups clarify contextually
6. entity drilldowns remain governed and useful
7. API and service layers no longer contain exploratory regressions
8. browser validation confirms the assistant behaves naturally without hallucinating beyond governed scope

## 10. Implementation Discipline

Non-negotiable rules for the next coding slice:

1. no keyword patching
2. no case-specific "just fix this query" logic
3. no technical error leakage to the user
4. no reviving the old manual agent path
5. no pretending uncovered ERP domains are supported
6. no weakening compiler or validator governance

The correct enterprise standard is:

1. governed where covered
2. honest where uncovered
3. natural where ambiguous
4. contextual where continuing
