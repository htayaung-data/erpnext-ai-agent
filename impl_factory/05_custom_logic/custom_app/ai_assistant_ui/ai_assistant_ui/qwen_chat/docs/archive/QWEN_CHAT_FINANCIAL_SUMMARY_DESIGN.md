# Qwen Chat Financial Summary Design

Status: design note with bounded wave-two runtime now active  
Audience: AI/ML, backend, ERP governance maintainers  
Goal: define the correct enterprise-grade treatment for `financial_summary` before any runtime migration

Current runtime note:

1. the original first-wave normalize-and-clarify design remains active
2. one bounded second-wave composite execution path is now active:
   `receivable` + `payable` + `cross_domain_health` -> `working_capital_health`
3. this document remains the source design rationale for anything beyond that approved ceiling

## 1. Current Judgment

`financial_summary` should not be migrated the same way as:

1. `financial_statement`
2. `inventory_summary`
3. `aging_analysis`
4. `trend_analysis`
5. `ranked_entities`
6. `product_performance`
7. `transaction_listing`

Those intents are narrow enough to resolve into one governed family or one governed report shape.

`financial_summary` is different.

It is currently a broad summary umbrella spanning multiple governed read domains.

That means:

1. it is acceptable to keep `financial_summary` explicitly legacy for now
2. it is not acceptable to migrate it with message keywords, hardcoded phrases, or one-off report forcing
3. it needs a dedicated semantic design before any runtime migration

## 2. What `financial_summary` Actually Covers Today

From current governed registries, `financial_summary` can map into all of these capability areas:

1. `sales_read`
2. `stock_read`
3. `accounts_payable_read`
4. `accounts_receivable_read`
5. `financial_statement_read`
6. `product_performance_read`

That makes it a cross-family intent, not a single-family intent.

It currently spans these family/report shapes:

1. sales summary via `Sales Analytics`
2. inventory value/balance via `Stock Balance` or `Warehouse Wise Stock Balance`
3. receivable summary via `Accounts Receivable Summary`
4. payable summary via `Accounts Payable Summary`
5. statement summary via `Profit and Loss Statement`, `Balance Sheet`, or `Cash Flow`
6. product profitability summary via `Gross Profit`

## 3. Why Direct Migration Would Be Wrong

If we migrate `financial_summary` too quickly, the likely failure modes are:

1. reintroducing lexical routing through disguised slot logic
2. forcing one family as the default answer for a broad summary request
3. collapsing composite requests into a single report when the user is really asking for health synthesis
4. mixing statement intent, aging intent, inventory intent, and product intent under one unresolved semantic surface

That would violate the enterprise rules already established in this refactor:

1. no keyword routing
2. no hardcoded business phrase logic
3. no single-case runtime fixes

## 4. Correct Enterprise-Grade Interpretation

`financial_summary` should be treated as one of these two things only:

1. a governed composite-summary intent
2. a temporary legacy umbrella pending explicit decomposition

It should not be treated as:

1. a synonym for `financial_statement`
2. a synonym for `aging_analysis`
3. a shortcut to whichever report happens to be easiest to execute

## 5. Recommended Target Architecture

The correct long-term design is to split `financial_summary` into one of two governed paths.

### 5.1 Path A: Semantic Decomposition

The interpreter resolves whether the user really means:

1. statement summary
2. receivable or payable summary
3. inventory balance/value summary
4. product profitability summary
5. sales summary

If one domain is dominant, the request should normalize into the narrower semantic-governed intent instead of staying `financial_summary`.

Examples:

1. “show current inventory value” -> `inventory_summary`
2. “how much receivable do we have” -> `aging_analysis`
3. “show P&L” -> `financial_statement`
4. “which products are profitable” -> `product_performance`

### 5.2 Path B: Governed Composite Summary

If the request is truly cross-domain, `financial_summary` should become a governed composite-summary intent with explicit plan selection.

That means:

1. semantic slots identify requested domains
2. metadata determines whether one domain or multiple domains are required
3. compiler selects either:
4. a narrowed governed single-domain route
5. or a governed composite plan

The current `working_capital_health` composite profile is the correct pattern to build on.

## 6. Proposed Slot Model

If `financial_summary` is migrated later, it should use structured slots like:

1. `summary_domains`
2. `summary_focus`
3. `summary_metric_family`
4. `summary_grain`
5. `time_scope`

Suggested slot meanings:

1. `summary_domains`
   Values:
   `sales`, `inventory`, `receivable`, `payable`, `statement`, `product_profitability`

2. `summary_focus`
   Values:
   `current_position`, `outstanding_amount`, `value_snapshot`, `profitability_snapshot`, `statement_view`, `cross_domain_health`

3. `summary_metric_family`
   Values:
   `sales_amount`, `balance_value`, `outstanding_total`, `gross_profit`, `net_profit`

4. `summary_grain`
   Values:
   `overall`, `customer`, `supplier`, `item`, `warehouse`, `account`

This is deliberately broader than the current migrated domains, which is why this needs its own design pass.

## 7. Migration Rule

Until those slots and resolution rules exist:

1. keep `financial_summary` explicitly legacy
2. do not extend `family_tool_surface`
3. do not add new defaults, keywords, aliases, or runtime rescue logic for it
4. prefer migrating narrower user intents into existing semantic-governed classes instead

## 8. Proposed Decision Contract

Before any runtime migration, `financial_summary` should have its own intermediate decision contract.

Suggested name:

1. `qwen_financial_summary_resolution_contract`

Its job is not to select a report directly.

Its job is to decide one of four governed outcomes:

1. `normalize_intent`
2. `execute_composite`
3. `clarify`
4. `reject`

### 8.1 Normalize Intent

Use this when one domain is dominant and the request can safely become one narrower semantic-governed intent.

Examples:

1. `statement` + `statement_view` -> `financial_statement`
2. `receivable` + `outstanding_amount` -> `aging_analysis`
3. `inventory` + `value_snapshot` -> `inventory_summary`
4. `product_profitability` + `profitability_snapshot` -> `product_performance`

Current constraint:

1. `sales` is a recognized summary domain
2. but it does not yet have an approved first-wave normalize target under this design
3. sales-only `financial_summary` requests should therefore remain clarification-first until that target is explicitly modeled

### 8.2 Execute Composite

Use this only when the request is truly cross-domain and a governed composite profile exists.

Current valid example:

1. `receivable` + `payable` + `cross_domain_health` -> `working_capital_health`

### 8.3 Clarify

Use this when:

1. no summary domain is resolved
2. one domain is resolved but the requested focus is still unclear
3. multiple domains are resolved but the request does not clearly ask for a cross-domain health synthesis

### 8.4 Reject

Use this only if the request falls outside governed ERP summary scope entirely.

## 9. Proposed Ambiguity Policy

The first enterprise-grade ambiguity policy should be conservative:

1. if no domain is resolved, clarify
2. if one domain is resolved but focus is missing, clarify
3. if multiple domains are resolved without explicit cross-domain health intent, clarify
4. only execute composite when a governed profile matches exactly

This bias is intentional.

It is better to ask one clean clarification than to force a broad summary request into the wrong governed family.

## 10. Design Artifacts

The current design artifacts for this intent are:

1. `QWEN_CHAT_FINANCIAL_SUMMARY_DESIGN.md`
2. `impl_factory/03_config/qwen_enterprise_metadata/financial_summary_semantic_design.json`
3. `impl_factory/03_config/qwen_enterprise_metadata/financial_summary_signal_extraction_design.json`
4. `QWEN_CHAT_FINANCIAL_SUMMARY_RUNTIME_CONTRACT_PLAN.md`
5. `impl_factory/03_config/qwen_enterprise_metadata/financial_summary_clarification_design.json`
6. `impl_factory/03_config/qwen_enterprise_metadata/financial_summary_test_matrix.json`

The JSON artifact now defines:

1. proposed slots
2. decomposition rules
3. composite profile mapping
4. decision contract design
5. initial ambiguity policies
6. governed signal extraction design for future `summary_domains` and `summary_focus`
7. clarification reason types, governed option sets, and attempt policy
8. acceptance cases for normalize, composite, and clarify behavior

These artifacts are design-only and must not drive runtime routing yet.

## 11. Next Safe Step

The next safe enterprise-grade step is design, not runtime mutation.

Recommended order:

1. finalize the decomposition-versus-composite decision contract
2. finalize how the interpreter will produce `summary_domains` and `summary_focus` from structured signals only
3. define the minimal runtime contract extension needed to carry those signals safely
4. only after that, implement one governed composite-summary slice if still needed

## 12. Current Recommendation

For the current phase:

1. keep `financial_summary` legacy-only
2. continue using semantic resolution for the already migrated narrow intents
3. do not resume aggressive `service.py` trimming until the `financial_summary` strategy is settled

This is the most enterprise-grade choice because it favors explicit modeling over premature migration.

## 13. Signal-Extraction Rule

When `financial_summary` is eventually migrated, the extractor must use only:

1. ontology concepts
2. requested dimensions
3. requested metrics
4. requested time scope
5. composite profile metadata

It must not use:

1. raw message keyword matching
2. direct phrase-to-domain routing
3. direct phrase-to-focus routing

That rule is now captured in:

1. `impl_factory/03_config/qwen_enterprise_metadata/financial_summary_signal_extraction_design.json`

## 14. Runtime Contract Rule

`financial_summary` should not be forced into the current narrow semantic runtime contract too early.

The runtime contract plan is:

1. keep the existing `SemanticResolutionContract` unchanged for narrow governed intents
2. add a separate `FinancialSummaryResolutionContract` later if migration is approved
3. use that contract to decide:
4. normalize into a narrower intent
5. execute a composite plan
6. clarify
7. reject

That rule is now captured in:

1. `QWEN_CHAT_FINANCIAL_SUMMARY_RUNTIME_CONTRACT_PLAN.md`

## 15. Clarification Rule

When `financial_summary` eventually migrates:

1. reuse the existing clarification contracts
2. reuse the existing clarification lane
3. add governed `reason_type` values only if needed
4. do not create a financial-summary-only clarification subsystem

That rule is now captured in:

1. `impl_factory/03_config/qwen_enterprise_metadata/financial_summary_clarification_design.json`

## 17. Current Open Constraint

The current package has one deliberate unresolved area:

1. `sales` is recognized as a valid `summary_domains` value
2. but the first migration wave does not yet define whether sales-only summaries should normalize into:
3. `trend_analysis`
4. `ranked_entities`
5. another governed summary intent

Rule for now:

1. sales-only `financial_summary` requests must stay on governed clarification
2. runtime must not guess a sales target until product and governance approve one

## 16. Test Matrix Rule

`financial_summary` should not enter runtime implementation without an explicit acceptance matrix.

That matrix must cover:

1. normalize-to-narrow-intent cases
2. governed composite cases
3. domain clarification cases
4. focus clarification cases
5. unsupported cross-domain clarification cases

That rule is now captured in:

1. `impl_factory/03_config/qwen_enterprise_metadata/financial_summary_test_matrix.json`
