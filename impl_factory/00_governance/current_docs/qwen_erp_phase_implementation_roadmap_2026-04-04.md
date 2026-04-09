# Qwen ERP Phase Implementation Roadmap

Status: active implementation roadmap  
Date: 2026-04-04  
Scope: enterprise implementation order after refactor, hardening, and follow-up-boundary closure

## 1. Executive Summary

The current refactor and hardening chapter is sufficiently closed for now.

That means the project should move from:

1. architecture cleanup
2. verification hardening
3. lexical-boundary removal

to:

1. governed business-surface expansion
2. richer governed artifact capability
3. business-definition governance
4. later multilingual, visual, OCR, and controlled action expansion

This roadmap replaces scattered wave notes with one active phase-by-phase delivery order.

## 2. Current Starting Point

The following are already materially complete for the current surface:

1. enterprise contract foundation
2. read-query hardening
3. semantic family layer and governed fresh-query compilation
4. post-contract hardening and full release-gate validation
5. bounded `financial_summary` second-wave rollout
6. `FollowUpBoundaryContract` redesign and closure

The release gate remains:

```bash
scripts/qwen_verify_enterprise_matrix.sh full
```

## 3. Delivery Principles

Every new phase must follow these rules:

1. implement one domain or one governed capability slice at a time
2. metadata and contracts own business policy
3. runtime consumes typed contracts and fails closed when evidence is insufficient
4. no phrase-specific routing or prompt-led business logic
5. full release gate must be green at each phase checkpoint

## 4. Phase Preflight And Debt Rule

The roadmap is product-first, but it must stay debt-aware.

That means each phase must begin with a short preflight review:

1. which debts are true blockers for this phase
2. which debts are near-blockers and may become expensive during this phase
3. which debts should be monitored but not solved now

Use the active debt register:

1. [qwen_erp_enterprise_tech_debt_register_2026-04-04.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/qwen_erp_enterprise_tech_debt_register_2026-04-04.md)

Rules:

1. do not stop a phase for non-blocking debt
2. do not defer blocker debt into “later”
3. do not turn the roadmap into a cleanup-only plan
4. solve debt gradually when it is phase-relevant
5. if a phase reveals that a monitored debt is now a blocker, update the register and pause only that phase

### 4.1 Phase Debt Classification

Use these categories:

1. `blocker`
   - must be resolved or explicitly governed before the phase starts
2. `near_blocker`
   - does not stop the phase immediately, but must be watched during the phase and may need a bounded fix
3. `monitor`
   - real debt, but not worth stopping current delivery for

### 4.2 Current Standing Preflight For The Next Chapter

Before Phase 1.1:

1. confirm the governance status of the external Qwen runtime dependency
2. confirm whether service-user / Administrator usage is production debt or test/support-only debt
3. keep `service.py` and lane-shape debt tracked as near-blockers, not stop-work blockers
4. prefer delivery progress over speculative pre-refactor unless a real blocker is proven

Current preflight note:

1. [qwen_erp_phase1_1_preflight_note_2026-04-04.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/qwen_erp_phase1_1_preflight_note_2026-04-04.md)

## 5. Phase 1: Operational Coverage Expansion

Goal: expand governed read coverage across high-value operational business asks.

This is the next implementation chapter.

### Mini-phase 1.1: Delivery / Fulfillment

Deliver:

1. governed capability metadata for fulfillment visibility
2. report-family mapping for delivery / shipment / fulfillment status
3. clarification rules for missing scope such as company, date, or status basis
4. bounded reasoning support where grounded facts are sufficient
5. regression and live verification

Current checkpoint:

1. the first strict `Delivery Note List` checkpoint is green
2. exact numeric scope is proven for:
   - `show me the last 5 delivery notes`
3. browser/UAT is now green for:
   - `show me the last 5 delivery notes`
   - `show me the last 5 delivery notes from last month`
   - `show me delivery notes with status Completed`
4. `Show me last 7 sale invoices` and invoice-detail follow-up still work after the Delivery Note sequence
5. the remaining `Top 5 customers by revenue last month` clarification should be treated as a separate governed ranking item, not as a Delivery / Fulfillment blocker
6. the next Phase 1.1 step should remain bounded and should not widen into broad fulfillment expansion without another explicit checkpoint decision
7. `1.1C` discovery should begin with `Delivery Note Trends`, while `Delivery Trip` remains deferred until live records exist in the deployment
8. `Delivery Note Trends` is now active through the existing governed `trend_analytics` family with the explicit contract:
   - required filters: `company`, `fiscal_year`, `period`, `based_on`
   - trusted scope: `Customer` + `Monthly`
   - no delivery-specific runtime branch was introduced
9. current `1.1C` checkpoint is now validated for:
   - `show monthly delivery note trend by customer this fiscal year`
   - `show monthly delivery note trend by customer last year`
   - invoice-detail to delivery-trend breakout continuity
10. current `1.1C` operational note:
   - `last_year` support was restored by propagating the existing governed time-scope contract through metadata, compiler fiscal-year resolution, and validator behavior
   - the external Qwen runtime required an image rebuild because runtime code changes are not mounted live into the container
11. `Delivery Trip` remains deferred until live records exist in the deployment
12. browser/UAT is now also green for governed `Delivery Note` detail continuity:
   - `give me latest 5 delivery note`
   - `tell me more about MAT-DN-2026-00016`
13. the release-gate module is green with the new `Delivery Note` detail smoke included

Current correction-track note:

1. the bounded `1.1R` Delivery correction track is now closed
2. what it restored:
   - shared `latest N` document-listing inheritance
   - shared transaction-listing continuation behavior during time-scope refinement
   - governed `Delivery Note` detail drilldown parity from the listing surface
3. `Top 5 customers by revenue last month` remains a separate live-path ranking issue and should not be bundled into Delivery acceptance
4. the next bounded Phase `1.1` slice should be `1.1D` Invoice-to-Delivery Proof
5. `1.1D` should stay a narrow operational evidence chain, not a general composite reconciliation engine

Current `1.1D-0` foundation note:

1. the live deployment already exposes the right evidence links through `Sales Invoice Item`:
   - `delivery_note`
   - `dn_detail`
   - `sales_order`
   - `so_detail`
2. the first trusted proof slice can stay narrower than expected:
   - `update_stock = 1` invoices
   - invoices whose items are all linked to submitted `Delivery Note` rows
   - otherwise fail closed
3. direct live census did not find any current `sales_order only` invoice bucket in this deployment
4. `Sales Invoice Item.delivered_qty` should not be used as the primary proof signal
5. return invoices must be handled explicitly as reversal context, not as ordinary outbound delivery confirmation

Current `1.1D-1` implementation note:

1. the narrow invoice-to-delivery proof path now reuses the existing `entity_detail` and artifact-boundary contracts
2. direct proof is currently admitted only for:
   - submitted invoices with `update_stock = 1`
   - invoices whose items are all linked to submitted `Delivery Note` rows
3. unsupported invoices still fail closed at the governed evidence boundary
4. targeted live smokes are green for:
   - supported invoice proof
   - unsupported invoice fail-closed behavior
5. the same governed proof path now answers the bounded date follow-up `when it was delivered?` from linked delivery-note posting dates
6. browser/UAT revalidation is the next required step before release-gate promotion

Current `1.1D-2` closure note:

1. supported invoice proof is now browser-valid in fresh chat and continued chat:
   - `tell me more about ACC-SINV-2026-00194`
   - `that item already delivered to the customer?`
   - `when it was delivered?`
2. explicit invoice identifiers now route through the shared governed `entity_detail` path even in a new chat
3. both the standard invoice-delivery proof smoke and the fresh-chat parity smoke are release-gated
4. the release-gate module is green with those smokes included
5. `1.1D` should now be treated as closed

Phase `1.1` closure note:

1. the bounded Delivery / Fulfillment chapter is now checkpoint-complete
2. what is closed inside `1.1`:
   - `1.1A` Delivery Note listing
   - `1.1B` date-scope and status enrichment
   - `1.1C` Delivery Note trend checkpoint
   - `1.1R` Delivery correction track
   - `1.1D` invoice-to-delivery proof
3. current next operational expansion should move to `1.2` Sales Order Status

Phase `1.1.5` stabilization note:

1. a medium stabilization slice is approved before `1.2`, but it must stay bounded and non-redesign
2. `1.1.5A` is now complete:
   - the heaviest non-production compiled-rollout and Phase `1.1` diagnostic helpers were extracted out of [service.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py)
   - those helpers now live in [service_diagnostics.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/probes/service_diagnostics.py)
   - public helper names exported from `service.py` remain compatibility-stable
   - live production turn orchestration was not redesigned in this slice
3. `1.1.5B` is now complete:
   - the non-production Phase `4` / `4B` probe, smoke, and selftest helpers were extracted out of [fresh_query_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py)
   - those helpers now live in [fresh_query_diagnostics.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/probes/fresh_query_diagnostics.py)
   - `fresh_query_interpreter.py` now focuses on production fresh-query compilation and execution, while keeping compatibility-stable public helper names through imports
   - production `execute_compiled_fresh_query_message(...)` was not repartitioned in this slice
4. `1.1.5C` is now complete:
   - compiler defaults and fiscal-year/company lookups are now isolated behind [defaults_repository.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/defaults_repository.py) and the Frappe adapter [frappe_defaults_repository.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/framework/frappe_defaults_repository.py)
   - [compiler.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/compiler.py) no longer imports `frappe` directly for company and fiscal-year defaults
   - [runtime_client.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/runtime_client.py) now centralizes repeated HTTP/JSON/error handling through one shared request primitive while preserving endpoint-specific error labels
   - new targeted contract coverage was added in [test_runtime_client_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_runtime_client_contracts.py)
5. bounded revalidation is green after the stabilization pass:
   - `py_compile`
   - enterprise guardrails
   - `test_runtime_client_contracts`
   - `test_semantic_financial_resolution`
   - site `test_post_contract_release_gates`
6. one release-gate rerun was required after a transient `last year delivery trend` red; the exact site-backed smoke passed immediately after, and the full site release-gate rerun finished green
7. `1.1.5D` is now complete:
   - direct knowledge-boundary semantics are now asserted in [test_knowledge_boundary_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_knowledge_boundary_contracts.py)
   - the slice covers front-door lane ownership, clarification preemption, valid-ERP uncovered reasoning fallback, unsupported non-ERP blocking, and user-facing artifact-lane boundary messaging
   - this converts critical shared-core boundary behavior from probe-only confidence into direct contract assertions
8. bounded revalidation remains green after `1.1.5D`:
   - enterprise guardrails
   - `test_knowledge_boundary_contracts`
   - `test_post_contract_state_integrity`
   - `test_post_contract_guard_probes`
   - `test_semantic_financial_resolution`
   - site `test_post_contract_release_gates`
9. `1.1.5` is now closure-ready:
   - the medium stabilization slice stayed bounded and non-redesign
   - the next planned implementation move should now be `1.2` Sales Order Status

Phase 1.1 preflight:

1. verify which ERPNext delivery / fulfillment doctypes and reports are truly active in this deployment
2. verify whether the external Qwen runtime dependency is governed enough for another compiled capability slice
3. measure whether Delivery / Fulfillment can be added metadata-first or whether Python routing debt is still too high
4. do not refactor `service.py` as part of this slice unless a real blocker appears

Current design note:

1. [qwen_erp_phase1_1_delivery_fulfillment_design_2026-04-04.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/qwen_erp_phase1_1_delivery_fulfillment_design_2026-04-04.md)

### Mini-phase 1.2: Sales Order Status

Deliver:

1. governed sales-order tracking capability
2. status-driven summary and detail paths
3. blocked clarification behavior for ambiguous order scope
4. bounded follow-up support from grounded order-status artifacts
5. regression and live verification

Current design note:

1. [qwen_erp_phase1_2_sales_order_status_design_2026-04-08.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/qwen_erp_phase1_2_sales_order_status_design_2026-04-08.md)

Current checkpoint:

1. `1.2A` Sales Order listing baseline is now implemented at the governed contract level
2. the assistant now has:
   - capability `sales_order_read`
   - report `Sales Order List`
   - `transaction_listing` family admission for submitted sales orders
3. shared-core reuse stayed bounded:
   - no new lane
   - no sales-order-specific routing patch
   - shared direct-query and transaction-listing adapters were generalized where needed
4. deterministic validation is green:
   - guardrails
   - [test_sales_order_listing_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_sales_order_listing_contracts.py)
   - `test_semantic_financial_resolution`
5. browser/UAT is the next gate before widening scope
6. the next planned slice remains `1.2B` Status Normalization And Date-Scope Enrichment
7. `1.2B` is now browser-valid and ERP-validated:
   - Sales Order status values and aliases are now governed in metadata for `Sales Order List`
   - shared direct-query scalar-filter grounding now consumes governed filter-value aliases generically
   - bounded prompts like `show sales orders to bill` and `show sales orders to deliver last month` compile correctly in deterministic validation
   - browser/UAT and direct ERP record checks both matched the governed Sales Order results
8. `1.2C` Sales Order detail drilldown parity is now browser-valid:
   - explicit `SAL-ORD-...` identifiers now route through the existing governed `entity_detail` path
   - governed `Sales Order` detail rendering stays bounded to order authority:
     - status
     - delivery status
     - billing status
     - planned delivery date
     - delivered percentage
     - billed percentage
     - totals and item rows
   - deterministic validation is green:
     - [test_entity_detail_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_entity_detail_contracts.py)
     - [test_sales_order_listing_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_sales_order_listing_contracts.py)
   - bounded live/site smoke is green:
     - `run_phase1_2_sales_order_detail_smoke`
   - browser/UAT matched the governed single-order detail behavior on exact prompts
9. `1.2D` Sales Order status follow-up is now browser-valid:
   - the follow-up stays on the existing grounded artifact evidence path, not a new lane
   - governed aliases now cover the bounded follow-up classes:
     - delivered progress
     - billed progress
     - planned delivery date
   - supported follow-ups now answer from Sales Order authority:
     - `is it delivered?`
     - `how much is delivered?`
     - `is it billed?`
     - `how much is billed?`
     - `when is delivery due?`
   - unsupported widening now fails closed:
     - `when was it delivered?` requires downstream fulfillment evidence and now stops at the governed boundary
   - deterministic validation is green:
     - [test_entity_detail_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_entity_detail_contracts.py)
     - [test_sales_order_listing_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_sales_order_listing_contracts.py)
   - site-backed validation is green:
     - `run_phase1_2_sales_order_status_followup_smoke`
     - site `test_entity_detail_contracts`
     - site `test_sales_order_listing_contracts`
   - browser/UAT matched the intended authority split:
     - delivered / billed / due-date asks answer from `Sales Order`
     - actual shipment-event date still fails closed and asks for downstream fulfillment evidence
10. Phase `1.2` is now checkpoint-complete:
   - `1.2A` listing baseline is browser-valid
   - `1.2B` status normalization is browser-valid and ERP-validated
   - `1.2C` detail drilldown parity is browser-valid
   - `1.2D` order-status follow-up is browser-valid
   - `1.2C` and `1.2D` are now promoted into [test_post_contract_release_gates.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_post_contract_release_gates.py)
   - the site-backed release-gate module is green after the promotion
11. the next approved phase step is `1.3` Purchase Order Tracking

### Mini-phase 1.3: Purchase Order Tracking

Deliver:

1. governed purchase-order tracking capability
2. procurement visibility surface
3. safe clarification and status normalization
4. bounded reasoning over grounded procurement artifacts
5. regression and live verification

Current approved preflight:

1. do not open a `1.2.5` stabilization slice by default
2. use a design-first readiness step instead:
   - [qwen_erp_phase1_3_purchase_order_tracking_design_2026-04-08.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/qwen_erp_phase1_3_purchase_order_tracking_design_2026-04-08.md)
3. live ERP evidence confirms the first bounded chapter is viable:
   - `Purchase Order` count is `8`
   - all current live rows are submitted
   - current live statuses include `To Bill` and `To Receive and Bill`
   - the order authority fields already exist for the intended first chapter:
     - `status`
     - `docstatus`
     - `transaction_date`
     - `schedule_date`
     - `per_received`
     - `per_billed`
4. the next approved implementation order is:
   - `1.3A` submitted purchase-order listing baseline
   - `1.3B` status normalization and date-scope enrichment
   - `1.3C` purchase-order detail drilldown parity
   - `1.3D` order-status follow-up from detail
   - `1.3E` optional draft / receipt extension only if justified
   - `1.3F` closure
5. `1.3A` Purchase Order listing baseline is now implemented at the governed contract level:
   - capability `purchase_order_read`
   - report `Purchase Order List`
   - `transaction_listing` family admission for submitted purchase orders
6. shared-core reuse stayed bounded:
   - no new lane
   - no purchase-order-specific routing patch
   - no status-alias widening yet
7. deterministic validation is green:
   - guardrails
   - [test_purchase_order_listing_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_purchase_order_listing_contracts.py)
   - `test_semantic_financial_resolution`
8. bounded live/site smoke is green:
   - `run_phase1_3_purchase_order_listing_smoke`
9. browser/UAT exposed a real shared follow-up seam:
   - a full re-ask like `show me purchase orders with status To Bill` could inherit the prior March date scope implicitly
10. that seam is now corrected generically:
   - self-contained governed re-asks break out of prior date context before continuation backfill
   - zero-row transaction summaries now preserve `Document Count = 0`
11. `1.3A` is now closure-ready
12. `1.3B` is now partially implemented at the governed contract level:
   - `Purchase Order List` now owns governed status aliases
   - the shared fresh-query filter-alias bridge no longer depends on prior dimension-key detection
13. bounded live/site regression coverage is green:
   - `run_phase1_3_purchase_order_status_scope_reset_smoke`
14. shared transaction-listing projection is now corrected for status-filtered purchase-order lists:
   - `Supplier` is preserved as the party column
   - `Status` is preserved as the filtered status column
15. browser/UAT is now green for `1.3B`:
   - month-scoped zero-row listing stays bounded to March
   - full re-ask status listing correctly breaks out of March
   - filtered purchase-order listing now preserves both `Supplier` and `Status`
16. `1.3C` Purchase Order detail drilldown parity is now implemented at the governed contract level:
   - explicit `PUR-ORD-...` identifiers now resolve through the shared `entity_detail` path
   - detail authority stays on purchase-order fields and derived order-level status only
   - Purchase Order detail now uses governed local narration for this slice after AI narrative overreach was observed in browser/UAT
17. deterministic and site-backed validation are green for `1.3C`:
   - `test_entity_detail_contracts`
   - `test_purchase_order_listing_contracts`
   - `run_phase1_3_purchase_order_detail_smoke`
18. browser/UAT is now green for `1.3C`:
   - explicit `PUR-ORD-...` drilldowns stay on single-document purchase-order detail
   - detail remains bounded to purchase-order authority only
   - unsupported receipt-event and payable-style claims are no longer present
19. `1.3D` Purchase Order status follow-up is now implemented at the governed contract level:
   - the follow-up stays on the existing grounded artifact evidence path, not a new lane
   - governed aliases now cover:
     - received progress
     - billed progress
     - planned receipt date
   - supported follow-ups now answer from Purchase Order authority:
     - `is it received?`
     - `how much is received?`
     - `is it billed?`
     - `how much is billed?`
     - `when is receipt due?`
20. unsupported widening now fails closed:
   - `when was it received?` requires downstream purchase-receipt evidence and now stops at the governed boundary
21. deterministic and site-backed validation are green for `1.3D`:
   - `test_entity_detail_contracts`
   - `test_purchase_order_listing_contracts`
   - `test_semantic_financial_resolution`
   - `run_phase1_3_purchase_order_status_followup_smoke`
22. browser/UAT is now green for `1.3D`:
   - receipt-progress follow-up stays anchored to the current purchase-order detail artifact
   - billed-progress and planned-receipt-date follow-ups answer from purchase-order authority only
   - actual receipt-event date still stops safely at the governed boundary
23. `1.3C` and `1.3D` are now promoted into [test_post_contract_release_gates.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_post_contract_release_gates.py)
24. the site-backed release-gate module is green after that promotion
25. Phase `1.3` is now checkpoint-complete:
   - `1.3A` listing baseline is browser-valid
   - `1.3B` status normalization and date-scope enrichment are browser-valid
   - `1.3C` detail drilldown parity is browser-valid
   - `1.3D` order-status follow-up is browser-valid
   - `1.3E` remained intentionally closed because no justified draft/receipt-widening need appeared
   - the `1.3` stop rule is now met without keyword routing or single-case purchase-order fixes

### Mini-phase 1.4: Customer Credit Status

Deliver:

1. governed credit-status capability
2. safe read-only credit risk surface
3. clarification for scope and thresholds where needed
4. bounded reasoning over grounded customer credit outputs
5. regression and live verification

Current approved preflight:

1. do not open a `1.3.5` stabilization slice by default
2. use a design-first readiness step instead:
   - [qwen_erp_phase1_4_customer_credit_status_design_2026-04-09.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/qwen_erp_phase1_4_customer_credit_status_design_2026-04-09.md)
3. live ERP evidence shows the strongest first authority seam is receivable exposure, not configured credit-limit policy:
   - governed `Accounts Receivable Summary` data is rich and already active
   - current phase customers already show meaningful outstanding, overdue, and negative-balance variation
   - live `Customer Credit Limit` rows are currently empty
4. the codebase already has strong reuse candidates:
   - governed `accounts_receivable_read`
   - governed aging and ranking support over `Accounts Receivable Summary`
   - the existing customer detail seam in [entity_detail.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_detail.py)
5. the approved `1.4` implementation order is:
   - `1.4A` Customer Credit Exposure Baseline
   - `1.4B` Status Normalization And As-Of-Date Enrichment
   - `1.4C` Customer Credit Detail Parity
   - `1.4D` Credit-Status Follow-Up From Detail
   - `1.4E` Optional Configured Credit-Limit Extension Checkpoint
   - `1.4F` Closure And Stop Rule
6. `1.4A` and `1.4B` are complete, `1.4C` and `1.4D` are complete, `1.4E` is deferred, and `1.4F` is complete:
   - bounded customer-credit phrasing now resolves to `Accounts Receivable Summary` through the existing `aging` family, not a new lane
   - the first slice is intentionally limited to customer credit exposure / status visibility
   - overdue-only and negative-balance-only filtered asks now resolve through governed metadata (no keyword routing)
   - shared aging rendering is being tightened to show customer exposure columns that better fit credit visibility:
     - Outstanding
     - Total Due
     - Overdue (31+)
   - governed artifact narration for `1.4A` is now explicitly constrained to factual exposure description, so aging answers do not drift into collection-behavior or credit-policy commentary
   - non-analysis aging reads now prefer the governed rendered response when that is the safer way to stay within receivable authority
   - targeted contract coverage now lives in [test_customer_credit_status_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_customer_credit_status_contracts.py)
   - a bounded live/site smoke now exists via `run_phase1_4_customer_credit_exposure_smoke`
   - the same-session scope-reset seam is now fixed for `1.4A`:
     - `show customer credit status as of today`
     - then `show me customer credit exposure`
     - now resolves as `followup_mode = new_query` with governed scope status `fresh_query_breakout`, instead of drifting into `erp_business_reasoning`
   - browser/UAT confirmed overdue-only and credit-balance-only filters in fresh sessions
7. `1.4E` is deferred for the current tenant because configured credit-limit rows are absent; Phase `1.4` is now closed pending future credit-limit activation

### Mini-phase 1.5: Operational Phase Closure

Deliver:

1. full-gate pass with all Wave 1 operational slices active
2. updated metadata audit
3. updated active baseline docs

Current closure checkpoint:

1. active closure note:
   - [qwen_erp_phase1_5_operational_phase_closure_2026-04-09.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/qwen_erp_phase1_5_operational_phase_closure_2026-04-09.md)
2. the site release-gate module now includes the promoted `1.4` operational smokes:
   - exposure
   - overdue-only
   - credit-balance-only
   - scope-reset
   - customer detail follow-up
3. closure verification exposed and fixed one shared transaction-listing validator drift:
   - canonical outstanding requests now validate correctly against document-list `outstanding_amount`
4. closure verification also exposed and fixed one shared reasoning-lane orchestration drift:
   - contradictory presentation-only follow-up payloads are now suppressed when grounded reasoning is already the accepted lane
5. the former `H5` reasoning-lane blocker is now green through direct site smoke and instrumented sanity-pack reruns
6. Phase `1.5` is now closure-complete:
   - [qwen_erp_phase1_5_operational_phase_closure_2026-04-09.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/qwen_erp_phase1_5_operational_phase_closure_2026-04-09.md)

## 6. Phase 2: Business Definition and Formula Registry

Goal: prevent KPI drift before composite expansion and more ambitious decomposition.

This phase intentionally comes before composite governed artifacts.

Why:

1. composite metrics should not be built on undefined business semantics
2. company-specific KPI and threshold meaning must be governed before multi-metric composition grows
3. this reduces migration debt later

### Mini-phase 2.1: Registry Contracts

Deliver:

1. `BusinessDefinitionRegistry`
2. `GovernedFormulaRegistry`
3. metadata schema for ownership, scope, formula, and threshold logic

### Mini-phase 2.2: Core KPI Definitions

Deliver:

1. tenure
2. average order value
3. collection ratio
4. credit utilization

### Mini-phase 2.3: Threshold and Risk Semantics

Deliver:

1. overdue severity thresholds
2. customer credit-risk thresholds
3. company-specific business-rule registry

### Mini-phase 2.4: Formula Phase Closure

Deliver:

1. registry-backed runtime usage
2. blocked-safe behavior for undefined KPIs
3. full-gate pass and doc refresh

## 7. Phase 3: Composite Governed Artifact Expansion

Goal: support richer multi-metric governed business questions without loosening authority boundaries.

### Mini-phase 3.1: Composite Artifact Contract

Deliver:

1. `CompositeRankingArtifactContract`
2. governed compatibility rules for multi-metric joins
3. blocked-safe behavior when scope compatibility is unproven

### Mini-phase 3.2: Customer Ranking Composites

Deliver:

1. customer revenue + quantity + AOV composite
2. explicit primary metric rule
3. governed same-grain validation

### Mini-phase 3.3: Product Ranking Composites

Deliver:

1. product revenue + quantity + average selling price composite
2. governed scope compatibility checks
3. bounded render and follow-up support

### Mini-phase 3.4: Overdue Customer Composite

Deliver:

1. overdue customer + overdue amount + last payment date composite
2. governed join and freshness rules
3. safe clarify or block behavior if compatibility is weak

### Mini-phase 3.5: Composite Phase Closure

Deliver:

1. full-gate pass
2. composite artifact checkpoint docs
3. updated current baseline docs

## 8. Phase 4: Complex Business Question Decomposition

Goal: support larger business asks only after enough governed endpoints exist.

### Mini-phase 4.1: Decomposition Contract

Deliver:

1. typed decomposition request contract
2. bounded sub-question planning
3. auditability for sub-plan generation

### Mini-phase 4.2: Governed Read-Only Planner

Deliver:

1. decomposition only into governed read capabilities
2. no free-form agent synthesis as business authority
3. explicit block/clarify behavior for unsupported plans

### Mini-phase 4.3: Composite Execution and Merge Policy

Deliver:

1. safe merge rules for decomposed outputs
2. governed synthesis policy
3. structured answer provenance

### Mini-phase 4.4: Decomposition Phase Closure

Deliver:

1. replay packs for long/complex business prompts
2. full-gate pass
3. enterprise checkpoint docs

## 9. Phase 5: Multilingual Enterprise UX

Goal: make Burmese and English first-class product behavior, not UI translation afterthoughts.

### Mini-phase 5.1: Language Layer

Deliver:

1. language detection contract
2. Burmese Unicode normalization
3. language-aware audit envelope

### Mini-phase 5.2: Business Glossary Layer

Deliver:

1. bilingual governed glossary
2. business-label localization policy
3. clarification-safe multilingual rendering

### Mini-phase 5.3: Same-Language Reply Policy

Deliver:

1. Burmese input -> Burmese reply
2. English input -> English reply
3. no fact drift across language transformation

### Mini-phase 5.4: Multilingual Verification

Deliver:

1. multilingual replay packs
2. validation support
3. full-gate pass with multilingual additions

## 10. Phase 6: Chart, Graph, Dashboard, and Export Artifacts

Goal: deliver governed visual artifacts from grounded structured data.

### Mini-phase 6.1: Chart Artifact Contract

Deliver:

1. chart artifact contract
2. chartable-field policy from report metadata
3. grounded chart generation path

### Mini-phase 6.2: Dashboard Proposal Layer

Deliver:

1. dashboard proposal contract
2. governed dashboard composition rules
3. save/proposal UX contract

### Mini-phase 6.3: Export Artifacts

Deliver:

1. PNG download path
2. CSV export
3. Excel export
4. export auditability

### Mini-phase 6.4: Visual Phase Closure

Deliver:

1. chart/dashboard/export replay packs
2. full-gate pass
3. updated current baseline docs

## 11. Phase 7: OCR and Document Ingestion

Goal: support governed OCR-driven read workflows only after the read and artifact surface is strong.

### Mini-phase 7.1: OCR Input Contract

Deliver:

1. OCR ingestion contract
2. document-source metadata
3. extraction confidence and audit fields

### Mini-phase 7.2: Extraction Validation

Deliver:

1. grounded validation rules for OCR output
2. reject/clarify behavior for low-confidence extraction
3. deterministic field normalization

### Mini-phase 7.3: OCR-to-ERP Read Flow

Deliver:

1. OCR-assisted read/query path
2. bounded document-to-ERP interpretation
3. no silent fact invention from OCR text

### Mini-phase 7.4: OCR Phase Closure

Deliver:

1. replay packs
2. full-gate pass
3. updated baseline docs

## 12. Phase 8: Controlled Write and Approval Layer

Goal: add enterprise write capability last, under strict preview and confirmation control.

### Mini-phase 8.1: Action Proposal Contracts

Deliver:

1. `ActionProposalContract`
2. preview card contract
3. propose -> preview -> confirm state model

### Mini-phase 8.2: Controlled CRUD Paths

Deliver:

1. safe create/update/delete paths
2. destructive-action policies
3. approval-aware write boundaries

### Mini-phase 8.3: Write Audit and Security

Deliver:

1. dedicated write audit trail
2. permission and secret isolation
3. least-privilege execution path

### Mini-phase 8.4: Write Phase Closure

Deliver:

1. full-gate pass
2. write-specific replay and approval tests
3. updated enterprise baseline docs

## 13. Recommended Immediate Next Slice

Start with:

1. Phase 1
2. Mini-phase 1.1
3. Delivery / Fulfillment

Why:

1. highest-value next business expansion from the written roadmap
2. read-only and low-risk relative to OCR or CRUD
3. fits the current contract-governed runtime cleanly
4. expands enterprise usefulness without reopening finished hardening chapters

## 14. Stop Rule For The Current Chapter

Do not reopen refactor/hardening by default while executing this roadmap.

Only reopen old cleanup chapters when:

1. a real regression appears
2. the full gate points to a genuine architectural red
3. a new phase cannot proceed safely without a bounded fix
