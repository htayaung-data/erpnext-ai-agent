# Qwen Chat Enterprise Baseline

Status: active baseline  
Date: 2026-04-04  
Audience: maintainers shipping changes in `qwen_chat`

## 1. Current Baseline

The current Qwen Chat baseline is considered enterprise-ready at the verification level.

As of this checkpoint:

1. guardrail audit is green
2. scripted semantic verification is green
3. scripted post-contract verification is green
4. the full enterprise release gate `scripts/qwen_verify_enterprise_matrix.sh full` has been rerun successfully end to end
5. `financial_summary` second wave is now active in one bounded form only:
   `receivable` + `payable` + `cross_domain_health` -> `working_capital_health`
6. the approved `financial_summary` composite path is now runtime-reachable from governed semantic payloads because validated `composite_profile_context` survives extracted-slot sanitization
7. smoke-fixture setup prompts have been moved into governed metadata where they were shared and unstable
8. remaining inline smoke strings have been audited and separated into:
   - governed fixture debt already migrated
   - explicit scenario contracts that should stay inline
   - debug-only local probes
9. protected smoke-support files are now guardrailed against reintroducing shared governed fixture literals inline
10. direct site-backed smoke sessions are explicitly committed on create/delete, so live hardening runs do not depend on implicit transaction visibility
11. append-only Qwen session saves now tolerate one timestamp-mismatch retry by reloading and restoring pending local session state conservatively
12. the follow-up boundary redesign wave is now closed to its stop rule:
   - `FollowUpBoundaryContract` exists
   - the contract producer and evaluator exist
   - residual degraded fallback is explicit, bounded, and test-protected
   - the wave has been revalidated with the full enterprise gate
13. residual degraded follow-up fallback is now materially narrower:
   - blank semantic payloads fail closed on supported grounded follow-up families
   - unsupported grounded artifacts do not break out on a single disjoint raw domain when semantic follow-up is present but blank
   - explicit multi-domain asks, contradictory presentation payloads, and governed uncovered-domain routing remain the bounded fallback exceptions
14. the mixed-metric adversarial lane is aligned to the approved bounded outcomes, including safe ERP reasoning that explicitly states the grounded limitation
15. Phase 1.1 now has its first strict governed operational checkpoint:
   - `Delivery Note List`
   - exact `last 5` scope preserved on the live compiled path
   - strict checkpoint smoke promoted into the release-gate path
   - full enterprise gate rerun green after that promotion
16. Phase 1.1 now also has a bounded governed trend checkpoint:
   - `Delivery Note Trends` is admitted through the existing `trend_analytics` family
   - both current-fiscal-year and `last_year` delivery-trend asks are release-gated
   - invoice-detail to delivery-trend breakout continuity is release-gated
   - `last_year` works through reused governed time-scope contracts, not a delivery-specific routing patch
17. the bounded Delivery correction track is now closed:
   - `latest N` Delivery Note listing behavior is browser-valid again
   - full-month Delivery Note listing no longer leaks a prior numeric limit
   - governed `Delivery Note` detail drilldown now works from the listing surface
   - the Delivery Note detail smoke is now in the release-gate module
18. the bounded invoice-to-delivery proof slice is now closed:
   - supported invoices answer delivery proof from governed evidence
   - rough delivery-date follow-ups are grounded to linked submitted delivery-note dates
   - fresh-chat explicit invoice identifiers now route through governed `entity_detail` before compiled-first-turn handling
   - both the standard and fresh-chat invoice proof smokes are release-gated
19. Phase `1.1` is now checkpoint-complete:
   - Delivery Note listing, date-scope, status, trend, detail, and invoice-to-delivery proof are release-gated
   - the next bounded operational expansion remains `1.2` Sales Order Status
20. Phase `1.1.5A` stabilization is now complete:
   - the heaviest non-production compiled-rollout and Phase `1.1` diagnostic helpers no longer live inline inside `service.py`
   - those helpers were moved into the dedicated probes module [service_diagnostics.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/probes/service_diagnostics.py)
   - `service.py` keeps compatibility-stable exports for those helpers, while production turn orchestration remains in place
   - guardrails and the site release-gate module are green after the extraction
21. Phase `1.1.5B` stabilization is now complete:
   - the non-production Phase `4` / `4B` probe, smoke, and selftest helpers no longer live inline inside [fresh_query_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py)
   - those helpers were moved into [fresh_query_diagnostics.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/probes/fresh_query_diagnostics.py)
   - `fresh_query_interpreter.py` dropped from `3588` lines to `2230` lines without repartitioning the live execution path
   - guardrails, the semantic suite, and the site release-gate module are green after the extraction
22. Phase `1.1.5C` stabilization is now complete:
   - compiler defaults and fiscal-year/company lookups are now isolated behind [defaults_repository.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/defaults_repository.py) and the Frappe adapter [frappe_defaults_repository.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/framework/frappe_defaults_repository.py)
   - [compiler.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/compiler.py) no longer imports `frappe` directly for company and fiscal-year defaults
   - [runtime_client.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/runtime_client.py) now centralizes repeated HTTP/JSON/error handling through one shared request primitive while preserving endpoint-specific error labels
   - targeted transport/defaults coverage now lives in [test_runtime_client_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_runtime_client_contracts.py)
23. Phase `1.1.5D` stabilization is now complete:
   - critical shared-core boundary behavior is now asserted directly in [test_knowledge_boundary_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_knowledge_boundary_contracts.py)
   - the bounded assertions cover front-door route ownership, clarification preemption, valid-ERP uncovered reasoning fallback, unsupported non-ERP blocking, and artifact-lane boundary messaging
   - the site-backed release-gate module remains green after adding those assertions, so `1.1.5` is closure-ready
24. Phase `1.2A` Sales Order listing baseline is now implemented at the governed contract level:
   - capability `sales_order_read` and report `Sales Order List` are now active
   - `transaction_listing` now admits submitted `Sales Order` rows without a new family or lane
   - shared direct-query column labeling and transaction-listing date handling were generalized to support `transaction_date`
   - targeted `Sales Order` listing coverage now lives in [test_sales_order_listing_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_sales_order_listing_contracts.py)
   - guardrails and the combined semantic plus Sales Order contract suites are green
   - browser/UAT is still the next required gate before widening into `1.2B`
25. Phase `1.2B` Sales Order status normalization is now browser-valid and ERP-validated:
   - governed Sales Order status values and aliases are active for `Sales Order List`
   - shared direct-query scalar-filter grounding consumes governed filter-value aliases generically, without Sales-Order-only branching
   - browser/UAT prompts and direct ERP validation matched for:
     - `show sales orders to bill`
     - `show sales orders to deliver last month`
     - `show completed sales orders`
26. Phase `1.2C` Sales Order detail drilldown parity is now browser-valid:
   - explicit `SAL-ORD-...` identifiers now resolve through the existing governed `entity_detail` path
   - governed `Sales Order` detail rendering stays bounded to order authority, including status, delivery status, billing status, planned delivery date, percentages, totals, and item rows
   - targeted entity-detail coverage is green in [test_entity_detail_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_entity_detail_contracts.py)
   - a bounded live/site smoke is green via `run_phase1_2_sales_order_detail_smoke`
   - browser/UAT matched the governed single-order detail behavior on exact prompts
27. Phase `1.2D` Sales Order status follow-up is now browser-valid:
   - the follow-up stays on the existing grounded artifact evidence path, not a new lane
   - governed aliases now cover:
     - `delivery_progress_percent`
     - `billing_progress_percent`
     - `planned_delivery_date`
   - supported order-authority follow-ups now answer directly from the grounded `Sales Order` artifact:
     - delivered?
     - how much delivered?
     - billed?
     - how much billed?
     - delivery due date
   - unsupported widening like actual delivery-event date now stops at the governed boundary and asks for downstream fulfillment evidence
   - targeted local and site validation is green:
     - [test_entity_detail_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_entity_detail_contracts.py)
     - [test_sales_order_listing_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_sales_order_listing_contracts.py)
     - `run_phase1_2_sales_order_status_followup_smoke`
   - browser/UAT matched the intended order-authority / downstream-evidence boundary
28. Phase `1.2` is now checkpoint-complete:
   - `1.2A` listing baseline is browser-valid
   - `1.2B` status normalization is browser-valid and ERP-validated
   - `1.2C` detail drilldown parity is browser-valid
   - `1.2D` order-status follow-up is browser-valid
   - `1.2C` and `1.2D` are now promoted into the release-gate module
   - the site-backed release-gate module remains green after that promotion
29. Phase `1.3A` Purchase Order listing baseline is now implemented and locally/site validated:
   - capability `purchase_order_read` and report `Purchase Order List` now exist as governed direct-query surfaces
   - `transaction_listing` now admits submitted `Purchase Order` rows without a new family or lane
   - listing-view metadata now explicitly admits `purchase_order`
   - targeted `Purchase Order` listing coverage now lives in [test_purchase_order_listing_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_purchase_order_listing_contracts.py)
   - a bounded live/site smoke is green via `run_phase1_3_purchase_order_listing_smoke`
   - browser/UAT uncovered and closed a shared continuation seam where a full re-ask could inherit the prior date window implicitly
   - `1.3A` is now closure-ready
30. Phase `1.3B` has now started at the governed metadata/shared-runtime seam:
   - `Purchase Order List` now owns governed status aliases
   - the shared fresh-query filter-alias bridge now grounds scalar status values without requiring prior dimension-key detection
   - the exact two-turn regression path is green via `run_phase1_3_purchase_order_status_scope_reset_smoke`
   - shared transaction-listing projection now preserves `Supplier` and `Status` on status-filtered Purchase Order lists
   - browser/UAT is now green for the scoped month-boundary and status-filtered Purchase Order listing prompts
31. Phase `1.3C` Purchase Order detail drilldown parity is now implemented and locally/site validated:
   - explicit `PUR-ORD-...` identifiers now resolve through the shared governed `entity_detail` path
   - Purchase Order detail stays on order authority only and does not inject downstream receipt-proof language
   - the current `1.3C` detail answer uses governed local narration for this slice because free AI narration leaked unsupported receipt-event and payable-style implications
   - targeted detail coverage is now included in [test_entity_detail_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_entity_detail_contracts.py)
   - a bounded live/site smoke is green via `run_phase1_3_purchase_order_detail_smoke`
   - browser/UAT is now green for `1.3C`
32. Phase `1.3D` Purchase Order status follow-up is now implemented and locally/site validated:
   - the follow-up stays on the existing grounded artifact evidence path, not a new lane
   - governed semantic aliases now cover:
     - `receipt_progress_percent`
     - `billing_progress_percent`
     - `planned_receipt_date`
   - supported follow-ups now answer from Purchase Order authority:
     - `is it received?`
     - `how much is received?`
     - `is it billed?`
     - `how much is billed?`
     - `when is receipt due?`
   - unsupported widening like actual receipt-event date now stops at the governed boundary and asks for downstream purchase-receipt evidence
   - targeted follow-up coverage is now included in [test_entity_detail_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_entity_detail_contracts.py)
   - a bounded live/site smoke is green via `run_phase1_3_purchase_order_status_followup_smoke`
   - browser/UAT is now green for `1.3D`
33. Phase `1.3` is now checkpoint-complete:
   - `1.3A` listing baseline is browser-valid
   - `1.3B` status normalization and date-scope enrichment are browser-valid
   - `1.3C` detail drilldown parity is browser-valid
   - `1.3D` order-status follow-up is browser-valid
   - `1.3C` and `1.3D` are now promoted into the site release-gate module
   - the site-backed release-gate module is green after that promotion
   - `1.3E` remained intentionally closed because no justified widening need appeared
34. Phase `1.4` is now checkpoint-complete:
   - `1.4A` customer credit exposure is browser-valid
   - `1.4B` overdue / credit-balance normalization is browser-valid
   - `1.4C` customer credit detail parity is browser-valid
   - `1.4D` customer credit detail follow-up is browser-valid
   - `1.4E` configured credit-policy visibility is now live for the current tenant:
     - configured credit limit
     - available credit
     - utilization
     - payment terms
     - default price list
   - `1.4E` uses the explicitly approved basis only:
     - `Outstanding Amount > Configured Credit Limit`
   - targeted contract coverage now lives in:
     - [test_customer_credit_status_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_customer_credit_status_contracts.py)
     - [test_entity_detail_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_entity_detail_contracts.py)
   - the site release-gate module now includes the promoted `1.4` smokes:
     - exposure
     - overdue-only
     - credit-balance-only
     - configured credit-policy follow-up
   - the site-backed release-gate module is green after the `1.4E` promotion
     - scope-reset
     - customer detail follow-up
35. Phase `1.5` operational closure is now complete:
   - Wave 1 operational seams from `1.1` through `1.4` are now materially represented together in the site release-gate pack
   - closure verification exposed one shared validator drift where canonical outstanding requests were being checked as `outstanding_total` against document-list artifacts that correctly emit `outstanding_amount`
   - that drift is now fixed in [family_validator.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_validator.py)
   - closure verification also exposed one shared reasoning-orchestration drift where contradictory presentation-only follow-up payloads could preempt an already-accepted grounded reasoning lane
   - that drift is now fixed in [scope_support.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/scope_support.py) and wired through [service.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py)
   - targeted regression coverage now lives in [test_semantic_financial_resolution.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_semantic_financial_resolution.py)
   - the direct site reruns of `run_phase1_1_delivery_note_session_reset_smoke` and `run_h4_recommendation_guarantee_stays_bounded_smoke` are green after the fixes
   - the instrumented `H5` sanity components now run green end to end, so `1.5` is now globally closure-ready for the next phase
36. Phase `2.1` registry foundation is now complete:
   - governed metadata homes now exist for business definitions, formulas, thresholds, and company-specific rule semantics
   - typed definition and formula state resolution is active in [business_definition_state.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/business_definition_state.py)
   - deterministic registry validation is active in [business_definition_formula_registry.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/business_definition_formula_registry.py)
37. Phase `2.2` first governed KPI definitions are now complete:
   - active KPI definitions now include average order value by sales order, average order value by sales invoice, customer overdue ratio as of date, customer credit utilization as of date, collection ratio by sales invoice period, and customer tenure by customer created date / first sales order / first sales invoice
   - generic `tenure` remains clarification-gated across multiple approved bases instead of silently defaulting
38. Phase `2.3` threshold and company-rule semantics are now complete:
   - threshold semantics now exist for credit-utilization policy bands plus blocked-safe overdue-severity and collection-ratio health presentation
   - company-specific policy rules now live in [business_rule_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/business_rule_registry.json)
39. Phase `2.4` formula phase closure is now complete:
   - governed KPI-definition runtime behavior now lives in [governed_kpi_support.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_kpi_support.py) and is wired through [frontdoor_lane.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/frontdoor_lane.py)
   - the frontdoor lane now answers governed KPI-definition asks safely for active, blocked, ambiguous, and explicit-definition undefined KPI states
   - customer detail now exposes governed lifecycle evidence through [customer_lifecycle_support.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/customer_lifecycle_support.py) and [entity_detail.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_detail.py)
   - deterministic coverage now lives in [test_governed_kpi_frontdoor.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_governed_kpi_frontdoor.py)
   - the site release-gate module now includes `run_phase2_4_governed_kpi_frontdoor_smoke`
   - the callable seam `run_governed_kpi_frontdoor_probe` and the live smoke `run_phase2_4_governed_kpi_frontdoor_smoke` are green
40. Phase `2.5A` KPI value artifact contract is now complete:
   - governed KPI execution metadata now exists in [governed_kpi_execution_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/governed_kpi_execution_registry.json)
   - typed execution-state and KPI-value artifact contracts are active in [governed_kpi_execution_state.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_kpi_execution_state.py)
   - deterministic registry validation is active in [governed_kpi_execution_registry.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_kpi_execution_registry.py)
   - deterministic coverage now lives in [test_governed_kpi_execution_state.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_governed_kpi_execution_state.py)
   - callable seam verification is green through:
     - `run_governed_kpi_execution_registry_probe`
     - `run_governed_kpi_execution_contract_probe`
41. Phase `2.5B` period KPI execution is now complete:
   - governed KPI value execution now lives in [governed_kpi_runtime_execution.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_kpi_runtime_execution.py) and is wired through [frontdoor_lane.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/frontdoor_lane.py)
   - the frontdoor now distinguishes KPI definition asks from KPI value asks without widening into phrase-specific business routing
   - active runtime coverage now includes:
     - average order value by sales order
     - average order value by sales invoice
     - collection ratio by approved period basis
   - bounded clarification is active for ambiguous basis and missing required period scope, and clarification continuation re-enters the governed KPI runtime path instead of transaction listing execution
   - explicit document-basis asks such as `sales orders` and `sales invoices` now resolve directly without unnecessary basis clarification
   - missing-period KPI asks no longer reuse the prior KPI period from the same session; they stop at governed period clarification instead
   - governed clarification signals now include alias-aware option metadata, so shorthand replies like `Sales Order` resolve as first-class governed basis selections instead of being misread as new listing requests
   - deterministic coverage now lives in [test_governed_kpi_runtime_execution.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_governed_kpi_runtime_execution.py)
   - the site release-gate module now includes `run_phase2_5_governed_kpi_period_execution_smoke`
   - the callable seam `run_phase2_5_governed_kpi_period_execution_probe` and the live smoke `run_phase2_5_governed_kpi_period_execution_smoke` are green

42. Phase `2.5C` customer-scoped KPI execution is now complete:
   - shared customer KPI runtime support now lives in [customer_kpi_runtime_support.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/customer_kpi_runtime_support.py)
   - active customer-scoped KPI runtime coverage now includes:
     - customer credit utilization as of date
     - customer overdue ratio as of date
     - customer tenure by customer created date
     - customer tenure by first sales order
     - customer tenure by first sales invoice
     - single-metric customer ranking by credit utilization
   - governed customer KPI execution now reuses the same receivable, policy, and lifecycle snapshot support across runtime execution and entity detail enrichment
   - scalar-vs-ranking detection now fails closed, so singular customer KPI asks do not drift into ranking execution
   - deterministic coverage now lives in:
     - [test_customer_kpi_runtime_support.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_customer_kpi_runtime_support.py)
     - [test_governed_kpi_runtime_execution.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_governed_kpi_runtime_execution.py)
     - [test_entity_detail_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_entity_detail_contracts.py)
   - the site release-gate module now includes `run_phase2_5_governed_kpi_customer_execution_smoke`
   - the callable seam `run_phase2_5_governed_kpi_customer_execution_probe` and the live smoke `run_phase2_5_governed_kpi_customer_execution_smoke` are green

## 2. Release-Gate Command

Default enterprise verification command:

```bash
scripts/qwen_verify_enterprise_matrix.sh full
```

This is the current authoritative baseline gate for Qwen Chat.

## 3. When To Use Less Than Full

Use targeted verification only when the change is clearly narrower than the full baseline.

### Semantic-only changes

Examples:

1. semantic registry updates
2. financial summary semantic contract changes
3. non-live semantic unit work

Run:

```bash
scripts/qwen_verify_enterprise_matrix.sh semantic
```

### Post-contract live/hardening changes

Examples:

1. smoke-fixture metadata changes
2. live hardening/support changes
3. H3/H4/H5 scenario changes

Run:

```bash
scripts/qwen_verify_enterprise_matrix.sh post-contract
```

### Runtime or policy changes touching both planes

Examples:

1. compiler behavior
2. interpreter behavior
3. semantic-to-runtime routing
4. governed recovery behavior

Run:

```bash
scripts/qwen_verify_enterprise_matrix.sh full
```

## 4. Senior Rule For Future Work

Before making the next change, choose the work type explicitly:

1. product/runtime improvement
2. governed semantic design
3. verification architecture
4. refactor hygiene

If the change is mostly refactor hygiene and does not reduce risk materially, do not do it by default.

## 5. Service.py Rule

Do not resume `service.py` trimming just to reduce line count.

Touch `service.py` only when:

1. the change improves real runtime behavior
2. the change removes meaningful verification debt
3. the affected block is clearly harming architecture or maintainability

## 6. Fixture Rule

Move prompts into governed smoke metadata only when both are true:

1. the prompt is a shared setup seed across multiple smokes
2. the prompt is not itself the scenario contract under test

Keep prompts inline when they are:

1. explicit clarification contracts
2. explicit reasoning follow-up contracts
3. adversarial wording contracts

Protected smoke-support files should not inline shared governed setup prompts again. Use fixture helpers instead.

## 7. Recommended Next Focus

Preferred next work after this checkpoint:

1. finish browser/UAT for `1.3B` Purchase Order status normalization before widening into `1.3C`
2. keep future stabilization slices bounded to shared-core risk, not broad architecture churn
3. keep the `1.1D` invoice-to-delivery proof slice narrow and evidence-based if it is later expanded
4. verification burn-down only when a real red appears

Avoid:

1. cosmetic refactors without architectural gain
2. new prompt migrations without reuse evidence
3. speculative cleanup while the current baseline is already green
4. adding more `financial_summary` composite paths without a new checkpoint

Active plan reference:

1. [qwen_erp_phase_implementation_roadmap_2026-04-04.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/qwen_erp_phase_implementation_roadmap_2026-04-04.md)
2. [qwen_erp_post_contract_expansion_backlog_2026-03-25.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/qwen_erp_post_contract_expansion_backlog_2026-03-25.md)
3. [QWEN_CHAT_FINANCIAL_SUMMARY_RUNTIME_BOUNDARY.md](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/docs/current/QWEN_CHAT_FINANCIAL_SUMMARY_RUNTIME_BOUNDARY.md)

## 8. Out-Of-Scope Reminder

This baseline does not change the standing rule:

1. [sales_console.js](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/sales_console/sales_console.js) remains outside this task and must not be touched
