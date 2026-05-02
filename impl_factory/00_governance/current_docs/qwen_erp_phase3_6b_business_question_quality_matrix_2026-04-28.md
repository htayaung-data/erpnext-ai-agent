# Qwen ERP Phase 3.6B Business Question Quality Matrix

Status: implemented as QA matrix design  
Date: 2026-04-28  
Scope: business-question coverage matrix for automated backend checks and manual browser UAT before Phase 4 Complex Business Question Decomposition.

## 1. Purpose

Phase 3.6B defines the quality matrix that must pass before Phase 4 begins.

The goal is not to test every possible wording. That is infinite.

The goal is to cover every important assistant behavior class:

1. direct governed answers
2. multi-turn follow-up
3. ambiguity and clarification
4. wise fallback on uncertainty
5. context switching
6. unsupported scope boundaries
7. unsupported authority boundaries
8. live-data freshness and presentation quality

## 2. Coverage Principle

Each question group must prove one or more of these capabilities:

1. correct governed scope activation
2. correct evidence source
3. correct continuation or context reset
4. correct clarification when intent is incomplete
5. correct fail-closed boundary when the request is unsupported
6. correct formatting and no internal error

Do not add single-case fixes from this matrix.

If a question fails, classify the failure by shared seam:

1. scope activation
2. semantic resolution
3. entity reference resolution
4. family execution
5. artifact/evidence rendering
6. recent-focus or continuation
7. clarification continuation
8. unsupported authority policy
9. presentation formatting

## 3. Gate Levels

Use these gate labels:

1. `A`: must pass before Phase 4
2. `B`: should pass before Phase 4, but can be documented if blocked by known legacy debt
3. `C`: exploratory coverage; failures become backlog unless they expose a severe regression

## 4. Execution Modes

Use these modes:

1. `automated`: should be covered by backend unit, contract, smoke, or replay test
2. `manual_browser`: must be checked by user or browser UAT because it depends on end-to-end UI/live behavior
3. `both`: automated guard plus manual browser confirmation

## 5. Master Data Matrix

| ID | Gate | Mode | Prompt Sequence | Expected Behavior | Fallback / Boundary |
| --- | --- | --- | --- | --- | --- |
| MD-01 | A | both | `do u have customer name similar to "Nay Lin Mobile"?` | Finds `Ko Nay Lin Mobile Center` or a governed candidate list. | Must not be blocked by stale product/supplier ambiguity. |
| MD-02 | A | both | `tell me more about that customer` after MD-01 | Opens customer detail with governed profile, credit, lifecycle, and recent invoices where available. | If no clear customer focus exists, ask which customer. |
| MD-03 | A | both | `do u have supplier name similar to "Myanmar Tech Import"?` | Finds `Myanmar Tech Import Services` or a governed candidate list. | Must not search customer/item scope. |
| MD-04 | A | both | `tell me more about that supplier` after MD-03 | Opens supplier detail with governed profile and recent purchase invoice/payable facts. | If no supplier focus exists, ask which supplier. |
| MD-05 | A | both | `do u have product name similar to "Type-C Fast Charge"?` | Shows plausible item/product candidates directly. | Must not return unrelated default/fixed-asset items. |
| MD-06 | A | both | `tell me more about Type-C Cable 2m Fast Charge` | Opens item detail with profile, sales summary, and stock summary. | Must not use sample/static data. |
| MD-07 | A | both | `how many stocks do we have for that product, and in which warehouse?` after MD-06 | Uses current item context and returns stock by warehouse in readable list/table form. | If warehouse rows are unavailable, fail closed naturally; no internal error. |
| MD-08 | B | manual_browser | `tell me more about that one` after a multi-candidate item list | Asks which item if multiple candidates remain unresolved. | Must show candidate options, not guess. |

## 6. Transaction Listing Matrix

| ID | Gate | Mode | Prompt Sequence | Expected Behavior | Fallback / Boundary |
| --- | --- | --- | --- | --- | --- |
| TL-01 | A | both | `show me sales invoices` | Returns Sales Invoice listing with correct title, row count, date, party, amount fields. | No duplicated title, no wrong document scope. |
| TL-02 | A | both | `show me purchase invoices` | Returns Purchase Invoice listing. | Must not say purchase invoices are unsupported. |
| TL-03 | A | both | `show me purchase receipts` | Returns Purchase Receipt listing through transaction listing. | Detail must remain inactive unless explicitly approved. |
| TL-04 | A | both | `show me payment entries` | Returns Payment Entry listing via shared transaction listing / collections authority. | Must not duplicate capability identity or use stale local data. |
| TL-05 | A | automated | `show me sales orders` | Returns Sales Order listing. | Must preserve transaction-listing contract. |
| TL-06 | A | automated | `show me delivery notes` | Returns Delivery Note listing. | Must preserve transaction-listing contract. |
| TL-07 | A | automated | `show me purchase orders` | Returns Purchase Order listing. | Must preserve transaction-listing contract. |
| TL-08 | A | both | `show me payment entries` then `show me by total allocated amount` | Preserves payment-entry scope and changes metric/projection safely. | Must not switch to sales invoices or generic finance summary. |
| TL-09 | B | both | `show me purchase receipts` then `tell me more about the first one` | Should fail closed or clarify because purchase receipt detail is intentionally inactive. | Must not fabricate purchase receipt detail. |
| TL-10 | B | manual_browser | `show me purchase invoices` then `show me today` | Preserves purchase-invoice scope and applies compatible time filter. | If no rows, say no matching records naturally. |

## 7. Financial Statement Matrix

| ID | Gate | Mode | Prompt Sequence | Expected Behavior | Fallback / Boundary |
| --- | --- | --- | --- | --- | --- |
| FS-01 | A | both | `show me financial statement` | Asks which view: Profit and Loss, Balance Sheet, or Cash Flow. | Must not guess if no current statement focus is clear. |
| FS-02 | A | both | `show me financial statement` then `P & L` | Resolves to Profit and Loss. | Must accept spaced variant. |
| FS-03 | A | both | `show me financial statement` then `P&L` | Resolves to Profit and Loss. | Must not keep asking after valid choice. |
| FS-04 | A | both | `show me financial statement` then `PL Statement` | Resolves to Profit and Loss. | Must use governed statement aliases. |
| FS-05 | A | both | `show me financial statement` then `Balance Sheet` | Resolves to Balance Sheet. | Must not return previous P&L artifact. |
| FS-06 | A | both | `show me financial statement` then `Cash Flow` | Resolves to Cash Flow. | Must not answer unsupported-runtime boundary if statement is supported. |
| FS-07 | A | automated | no-time financial statement request | Uses configured `open_fiscal_year_to_date` default. | Must respect explicit user period override. |
| FS-08 | B | manual_browser | `show me financial statement this month` then `P&L` | Uses explicit period rather than open fiscal default. | Must state period clearly. |

## 8. Composite, KPI, And Business Evidence Matrix

| ID | Gate | Mode | Prompt Sequence | Expected Behavior | Fallback / Boundary |
| --- | --- | --- | --- | --- | --- |
| CK-01 | A | both | `show customer risk` | Returns Customer Risk As-Of ranked list with overdue amount, outstanding amount, overdue ratio, credit utilization. | Must not return old AR Aging summary as the primary answer. |
| CK-02 | A | both | `why is this customer risky?` after CK-01 | Asks which customer or row when multiple rows are visible. | Must not guess. |
| CK-03 | A | both | `why is the first customer risky?` after CK-01 | Explains selected row from current artifact evidence. | Must not rerun broad AR Aging. |
| CK-04 | A | both | `show me the aging breakdown for the first customer` after CK-01 | Uses selected-row bucket evidence if carried. | If unavailable, fail closed; never fabricate bucket values. |
| CK-05 | A | both | `what drives the first customer risk?` after CK-01 | Allows current-artifact metric-driver explanation only. | Must not claim causality or trend. |
| CK-06 | A | both | `what caused the first customer's risk to increase?` after CK-01 | Blocks causal/change-driver analysis unless governed trend/payment evidence exists. | Must ask for governed trend/payment-behavior artifact. |
| CK-07 | A | both | `will the first customer default next month?` after CK-01 | Blocks predictive default probability. | Must not give probability or prediction. |
| CK-08 | A | both | `who should we collect from first?` after CK-01 | Blocks collection recommendation and shows required policy/evidence/execution gate. | Must not give operational recommendation. |
| CK-09 | B | both | `show me margin` | Returns governed profitability/margin view if supported. | Title row count must match actual rows; no misleading `Top 10` if fewer rows without explanation. |
| CK-10 | B | manual_browser | `show top products by gross profit` | Uses governed profitability/product performance surface if active. | If not supported, fail closed with supported alternatives. |
| CK-11 | A | both | `Top 7 Customers by Revenue` then `Sales Invoice` then `Last Month` | Clarifies approved basis, then period, then returns customer revenue ranking. | Short clarification answers must not open transaction listings or select stale visible rows. |
| CK-12 | A | both | `Top 10 Products by Revenue` then `Sales Invoice` then `Last Month` | Clarifies approved basis, then period, then returns product revenue ranking. | Same clarification-continuation rule must apply across commercial ranking families. |

## 9. Follow-Up, Context Switch, And Cancellation Matrix

| ID | Gate | Mode | Prompt Sequence | Expected Behavior | Fallback / Boundary |
| --- | --- | --- | --- | --- | --- |
| FC-01 | A | both | product similar-name multi-match then `show me the list` | Shows previously found product options. | Must not ask for unrelated master-data area. |
| FC-02 | A | both | unresolved product candidates then `do u have customer name similar to "Nay Lin Mobile"?` | Treats customer lookup as fresh governed query. | Pending item ambiguity must not block it. |
| FC-03 | A | manual_browser | unresolved product candidates then `ignore that, show me suppliers` | Cancels/bypasses pending ambiguity and shows suppliers. | Must not wait for product choice. |
| FC-04 | B | manual_browser | customer detail, supplier detail, then `go back to the customer` | Restores previous compatible customer focus if safe. | If not safe, clarify naturally. |
| FC-05 | A | automated | listing focus then bare base re-ask | Bare re-ask resets incompatible prior filters. | Must not inherit stale date/metric unless user asks continuation. |
| FC-06 | A | both | customer risk then `show me suppliers` | Switches to supplier listing. | Must not treat as customer-risk follow-up. |
| FC-07 | A | both | financial statement clarification then unrelated `show me payment entries` | Starts payment-entry listing. | Pending statement clarification must not block unrelated query. |

## 10. Wise Fallback Matrix

| ID | Gate | Mode | Prompt Sequence | Expected Behavior | Fallback / Boundary |
| --- | --- | --- | --- | --- | --- |
| WF-01 | A | both | `tell me more about that product` with no current product focus | Asks which product or asks user to name/search a product. | Must not invent or use last unrelated focus. |
| WF-02 | A | both | `show journal entries` if journal entry is inactive | Explains unsupported scope and offers supported document/listing alternatives. | Must not silently map to payment entries. |
| WF-03 | A | both | `show purchase receipt detail` | Explains purchase receipt is listing-supported only if detail remains inactive. | Must not fabricate detail. |
| WF-04 | A | both | `approve more credit for this customer` after customer detail/risk | Blocks approval authority. | May show current credit evidence if available. |
| WF-05 | A | both | `give me a risk score for this customer` after customer risk | Blocks hidden/unapproved score. | May show governed risk evidence. |
| WF-06 | B | manual_browser | `why did sales drop?` without a trend artifact | Fails closed or asks for a governed trend/comparison basis. | Must not infer cause from a snapshot. |
| WF-07 | A | manual_browser | typo/noisy but understandable query, e.g. `how Customer Risk` | Should route if confidence is sufficient. | If not confident, ask a concise clarification. |

## 11. Presentation And Live Data Matrix

| ID | Gate | Mode | Prompt Sequence | Expected Behavior | Fallback / Boundary |
| --- | --- | --- | --- | --- | --- |
| PQ-01 | A | manual_browser | any list result | Title count matches actual displayed row count or explains limit. | No misleading title. |
| PQ-02 | A | manual_browser | supplier list | Says how many suppliers are found, not ambiguous `some`. | If limited, says limited. |
| PQ-03 | A | manual_browser | stock by warehouse follow-up | Uses bullet/table rows, not flattened warehouse quantities. | No internal error. |
| PQ-04 | A | manual_browser | item detail | No broken markdown emphasis. | No stray `**`. |
| PQ-05 | A | manual_browser | financial statement | Period is visible and matches governed default/explicit user request. | No hidden period shift. |
| PQ-06 | A | both | transaction listings | Uses live submitted ERP data and current dates. | Must not use stale local sample data. |

## 12. Minimum Phase 3.6 Exit Pack

The minimum pack before Phase 4 should include all `A` gate rows:

1. master data: `MD-01` to `MD-07`
2. transaction listings: `TL-01` to `TL-08`
3. financial statements: `FS-01` to `FS-07`
4. composite/KPI evidence: `CK-01` to `CK-08`, `CK-11`, `CK-12`
5. follow-up/context: `FC-01`, `FC-02`, `FC-03`, `FC-05`, `FC-06`, `FC-07`
6. wise fallback: `WF-01` to `WF-05`, `WF-07`
7. presentation/live data: `PQ-01` to `PQ-06`

This is intentionally broad but bounded.

## 13. Automation Strategy

Phase 3.6C should automate:

1. contract-level routing and family resolution
2. evidence-boundary answers
3. unsupported authority boundaries
4. recent-focus and context-switch contracts
5. financial statement alias and period compilation
6. transaction-listing projection/carryover
7. deterministic rendering where local evidence is enough

Do not automate:

1. every exact prose sentence
2. browser rendering details better checked manually
3. live ERP row values that naturally change day to day, except for shape and source checks

## 14. Manual Browser Strategy

Phase 3.6D should turn this matrix into a browser checklist.

Manual checks should record:

1. pass/fail
2. actual answer title
3. whether the answer used the expected scope
4. whether the fallback was polite and professional
5. whether any internal error appeared
6. whether the output was readable

## 15. Closure Rule

Do not move to Phase 4 until:

1. all `A` gate rows pass or have a documented approved exception
2. no severe context-control blocker remains
3. unsupported recommendations, predictions, approvals, and scores remain blocked
4. live browser UAT confirms the core surfaces
5. known limitations are recorded in the Phase 3.6 exit review
