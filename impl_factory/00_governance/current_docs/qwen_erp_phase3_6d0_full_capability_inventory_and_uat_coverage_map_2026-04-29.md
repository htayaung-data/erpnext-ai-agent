# Qwen ERP Phase 3.6D-0 Full Capability Inventory And UAT Coverage Map

Status: implemented as pre-UAT coverage-control plan
Date: 2026-04-29
Scope: full-project capability inventory and browser-UAT coverage map before Phase 3.6D manual browser execution and Phase 4 Complex Business Question Decomposition.

## 1. Purpose

Phase 3.6B and 3.6C created a strong minimum exit pack for current quality gates.

After re-evaluating the whole assistant surface, that minimum pack is directionally correct but not enough by itself to represent the full historical project.

This document adds a pre-UAT control step:

1. inventory the implemented governed business surfaces
2. map manual browser tests to the real implemented capability surface
3. prevent recent-conversation bias in the UAT pack
4. keep Phase 4 blocked until the broader current assistant is proven stable

This is not a new feature phase.

It is a quality-control expansion layer.

## 2. Decision

Before Phase 3.6D manual browser UAT is executed, the team must use this full capability map to build the browser checklist.

The Phase 3.6D checklist must not be generated only from recent fixes such as item stock, customer risk, financial statement aliases, or recommendation boundaries.

It must cover the full active assistant surface represented by:

1. capability registry
2. report registry
3. governed scope registry
4. report family registry
5. composite family and artifact registries
6. governed KPI execution registry
7. completed release-gate and contract-test evidence

## 3. Current Implemented Surface Inventory

This inventory is based on the current metadata and test surface available at the time of this review.

### 3.1 Capability Registry

Current capability count: 15.

Capabilities:

1. `accounts_payable_read`
2. `accounts_receivable_read`
3. `collections_read`
4. `customer_master_read`
5. `financial_statement_read`
6. `fulfillment_read`
7. `item_master_read`
8. `product_performance_read`
9. `purchase_invoice_read`
10. `purchase_order_read`
11. `purchase_receipt_read`
12. `sales_order_read`
13. `sales_read`
14. `stock_read`
15. `supplier_master_read`

### 3.2 Report Registry

Current report count: 25.

Reports:

1. `Accounts Payable`
2. `Accounts Payable Summary`
3. `Accounts Receivable`
4. `Accounts Receivable Summary`
5. `Balance Sheet`
6. `Cash Flow`
7. `Customer Master List`
8. `Delivery Note List`
9. `Delivery Note Trends`
10. `Gross Profit`
11. `Item Master List`
12. `Item-wise Sales History`
13. `Payment Entry List`
14. `Profit and Loss Statement`
15. `Purchase Invoice List`
16. `Purchase Order List`
17. `Purchase Receipt List`
18. `Sales Analytics`
19. `Sales Invoice Item List`
20. `Sales Invoice List`
21. `Sales Order Item List`
22. `Sales Order List`
23. `Stock Balance`
24. `Supplier Master List`
25. `Warehouse Wise Stock Balance`

### 3.3 Active Governed Scopes

Current active governed scope count: 10.

Active scopes:

1. `customer_master`: `active_reference`
2. `delivery_note`: `active_broad`
3. `item_master`: `active_reference`
4. `payment_entry`: `active_broad`
5. `purchase_invoice`: `active_broad`
6. `purchase_order`: `active_broad`
7. `purchase_receipt`: `active_reference`
8. `sales_invoice`: `active_broad`
9. `sales_order`: `active_broad`
10. `supplier_master`: `active_reference`

Important policy note:

`purchase_receipt` is active for listing/reference behavior, but detail promotion remains intentionally restricted unless separately approved.

### 3.4 Active Report Families

Current active report family count: 8.

Families:

1. `aging`
2. `financial_statement`
3. `inventory_snapshot`
4. `master_data_directory`
5. `product_profitability`
6. `ranking_analytics`
7. `transaction_listing`
8. `trend_analytics`

### 3.5 Active Composite Families And Artifacts

Current active composite family count: 3.

Families:

1. `customer_commercial_ranking`
2. `customer_risk_as_of`
3. `product_commercial_ranking`

Current active composite artifact count: 5.

Artifacts:

1. `customer_commercial_ranking_sales_invoice_composite`
2. `customer_commercial_ranking_sales_order_composite`
3. `customer_risk_as_of_default_composite`
4. `product_commercial_ranking_sales_invoice_composite`
5. `product_commercial_ranking_sales_order_composite`

### 3.6 Governed KPI Runtime Execution

Current governed KPI execution count: 24.

Covered KPI surfaces include:

1. average order value by sales order
2. average order value by sales invoice
3. collection ratio
4. customer revenue ranking
5. customer quantity ranking
6. customer average order value ranking
7. customer average invoice value ranking
8. product/item revenue ranking
9. product/item quantity ranking
10. product/item average selling price ranking
11. customer tenure from created date
12. customer tenure from first sales order
13. customer tenure from first sales invoice
14. customer overdue amount scalar and ranking
15. customer overdue ratio scalar and ranking
16. credit utilization scalar and ranking

## 4. Coverage-Control Principle

Every manual browser UAT question in Phase 3.6D must map to at least one coverage source.

Allowed coverage sources:

1. active governed scope
2. registered repor
3. active report family
4. active composite family or artifac
5. governed KPI execution
6. completed release-gate tes
7. existing contract tes
8. explicit exploratory/adversarial boundary case

If a browser question cannot be mapped to one of these sources, it should be marked exploratory and must not become a release blocker unless it exposes a severe shared-seam regression.

## 5. Full UAT Coverage Groups

Phase 3.6D should organize manual browser checks into these groups.

### 5.1 Master Data Discovery And Detail

Required surfaces:

1. customer similar-name search
2. supplier similar-name search
3. item/product similar-name search
4. customer detail
5. supplier detail
6. item/product detail
7. deictic follow-up such as `that customer`, `that supplier`, and `that product`
8. candidate-list behavior when multiple plausible matches exis

Representative prompts:

1. `do u have customer name similar to "Nay Lin Mobile"?`
2. `tell me more about that customer`
3. `do u have supplier name similar to "Myanmar Tech Import"?`
4. `tell me more about that supplier`
5. `do u have product name similar to "Type-C Fast Charge"?`
6. `tell me more about Type-C Cable 2m Fast Charge`

### 5.2 Inventory And Stock Position

Required surfaces:

1. item stock summary in item detail
2. stock by warehouse follow-up
3. stock balance family
4. warehouse-wise stock balance family
5. readable stock output formatting
6. fail-closed behavior when warehouse rows are not carried

Representative prompts:

1. `how many stocks do we have for that product, and in which warehouse?`
2. `show stock balance`
3. `show stock by warehouse`

### 5.3 Transaction Listings

Required surfaces:

1. sales invoices
2. purchase invoices
3. purchase receipts
4. payment entries
5. sales orders
6. delivery notes
7. purchase orders
8. date and projection follow-ups such as `today`, `by outstanding`, `by status`

Representative prompts:

1. `show me sales invoices`
2. `show me purchase invoices`
3. `show me purchase receipts`
4. `show me payment entries`
5. `show me sales orders`
6. `show me delivery notes`
7. `show me purchase orders`
8. `show me today`

### 5.4 Document Detail And Operational Evidence

Required surfaces:

1. sales invoice delivery proof
2. delivery note detail
3. sales order delivery progress
4. sales order billing progress
5. sales order planned delivery date
6. purchase order receipt progress
7. purchase order billing progress
8. purchase order planned receipt date
9. unsupported actual event-date boundaries when evidence is insufficien

Representative prompts:

1. `tell me more about the first sales invoice`
2. `was this invoice delivered?`
3. `tell me more about the first sales order`
4. `what is its delivery status?`
5. `what is its billing status?`
6. `tell me more about the first purchase order`
7. `what is its receipt status?`
8. `when was it actually received?`

### 5.5 Financial Statements

Required surfaces:

1. financial statement clarification
2. Profit and Loss aliases
3. Balance Sheet aliases
4. Cash Flow aliases
5. configured open-fiscal-period defaul
6. explicit period override
7. deterministic financial statement rendering

Representative prompts:

1. `show me financial statement`
2. `P & L`
3. `PL Statement`
4. `Balance Sheet`
5. `Cash Flow`
6. `show me P&L for this month`

### 5.6 AR, AP, Credit, And Aging

Required surfaces:

1. accounts receivable aging
2. accounts payable aging
3. overdue amoun
4. overdue ratio
5. customer credit status
6. credit utilization
7. credit limit status
8. credit balance
9. payment terms and default price list when carried by customer detail

Representative prompts:

1. `show accounts receivable aging`
2. `show accounts payable aging`
3. `tell me more about Ko Nay Lin Mobile Center`
4. `what is this customer's credit limit status?`
5. `what is this customer's overdue ratio?`
6. `what payment terms does this customer have?`

### 5.7 Commercial KPI And Rankings

Required surfaces:

1. average order value
2. average invoice value
3. collection ratio
4. top customers by revenue
5. top customers by quantity
6. top products by revenue
7. top products by quantity
8. top products by average selling price
9. credit utilization ranking
10. customers above credit limit where supported

Representative prompts:

1. `what was our average order value last month?`
2. `what was our collection ratio last month?`
3. `show top customers by sales`
4. `show top products by revenue`
5. `show top customers by credit utilization`
6. `show customers above credit limit`

### 5.8 Product Profitability And Margin

Required surfaces:

1. gross profit / margin view
2. product profitability ranking
3. row-count/title alignment when fewer rows exist than requested
4. negative margin display
5. item-level commercial follow-up if supported by artifact evidence

Representative prompts:

1. `show me margin`
2. `show top products by gross profit`
3. `show top products by gross profit percent`

### 5.9 Trends And Time-Series

Required surfaces:

1. sales analytics trend
2. delivery note trends
3. explicit period handling
4. fail-closed behavior for unsupported causal trend questions
5. comparison-basis clarification where period or metric is missing

Representative prompts:

1. `show sales trend`
2. `show delivery trend`
3. `compare sales this month with last month`
4. `why did sales drop?`

### 5.10 Customer Risk And Composite Evidence

Required surfaces:

1. customer risk as-of lis
2. selected-row explanation
3. selected-row aging breakdown
4. driver explanation within current artifact evidence
5. blocked causal change analysis
6. blocked prediction
7. blocked collection recommendation unless policy/evidence/execution gates are approved

Representative prompts:

1. `show customer risk`
2. `why is this customer risky?`
3. `why is the first customer risky?`
4. `show me the aging breakdown for the first customer`
5. `what drives the first customer risk?`
6. `what caused the first customer's risk to increase?`
7. `who should we collect from first?`
8. `will the first customer default next month?`

### 5.11 Context Control, Clarification, And Cancellation

Required surfaces:

1. unresolved candidate list then `show me the list`
2. unresolved ambiguity then unrelated fresh query
3. `forget that` and `ignore that`
4. `go back` only when safe
5. rank and ordinal references
6. deictic references
7. stale context must not block new governed requests

Representative prompts:

1. `do u have product name similar to "Type-C Fast Charge"?`
2. `show me the list`
3. `do u have customer name similar to "Nay Lin Mobile"?`
4. `ignore that, show me suppliers`
5. `show customer risk`
6. `explain rank 2`
7. `go back to the customer`

### 5.12 Unsupported Scope, Unsupported Authority, And Wise Fallback

Required surfaces:

1. unsupported document scope
2. inactive detail promotion
3. missing period
4. missing report type
5. missing entity or row
6. unapproved recommendation
7. unapproved prediction
8. unapproved approval action
9. unapproved hidden score
10. non-ERP or out-of-scope reques

Representative prompts:

1. `show journal entries`
2. `show purchase receipt detail`
3. `approve more credit for this customer`
4. `give me a risk score for this customer`
5. `will this customer default next month?`
6. `who should we collect from first?`

### 5.13 Presentation And Live-Data Quality

Required checks:

1. no internal error
2. no duplicated title tex
3. no misleading `Top 10` title when fewer rows are displayed unless explained
4. list count says whether result is complete or limited
5. tables and lists are readable in browser
6. amounts, signs, percentages, and dates are formatted correctly
7. no broken markdown emphasis
8. answer states period/as-of date where relevan
9. data reflects live ERP and current configured date behavior

Representative prompts:

1. any master-data list resul
2. any transaction listing
3. any financial statemen
4. any stock-by-warehouse answer
5. any selected-row composite evidence answer

## 6. Tiered UAT Execution Model

To avoid endless testing, Phase 3.6D should use tiers.

### 6.1 Tier A: Must-Pass Full-Project Critical

This tier blocks Phase 4.

It must include:

1. every active governed scope
2. every primary report family
3. financial statement default and explicit periods
4. master-data discovery and detail
5. transaction listings
6. stock by warehouse
7. customer risk selected-row follow-up
8. recommendation/prediction/approval boundaries
9. context switching and cancellation
10. browser presentation quality

### 6.2 Tier B: Regression Confidence

This tier should pass before Phase 4, but approved exceptions can be documented if the issue is non-critical and already understood.

It should include:

1. document detail/event evidence
2. operational status follow-ups
3. KPI calculation/detail-on-demand
4. trend/report variants
5. margin/product profitability variants

### 6.3 Tier C: Exploratory And Adversarial

This tier is used to find future backlog.

It should include:

1. noisy spelling
2. mixed-domain compound prompts
3. unclear business language
4. unsupported but plausible executive questions
5. requests that combine prediction, recommendation, approval, or causal explanation

Tier C failures do not block Phase 4 unless they expose a severe shared-seam regression.

## 7. Pass/Fail Recording Requirements

Every Phase 3.6D manual browser row should record:

1. question sequence
2. expected family or scope
3. expected evidence source
4. expected fallback or boundary if applicable
5. actual answer title
6. pass/fail
7. internal error observed: yes/no
8. presentation issue observed: yes/no
9. context-control issue observed: yes/no
10. live-data concern observed: yes/no
11. severity if failed
12. shared seam classification if failed

Allowed failure seam classifications:

1. scope activation
2. semantic resolution
3. entity reference resolution
4. family execution
5. artifact/evidence rendering
6. recent-focus or continuation
7. clarification continuation
8. unsupported authority policy
9. unsupported scope boundary
10. presentation formatting
11. live-data freshness
12. browser/runtime stability

## 8. Exit Criteria Added By This Step

Phase 3.6 cannot close until:

1. Phase 3.6B minimum `A` rows are still represented
2. this full-project inventory has been translated into a manual UAT pack
3. Tier A manual browser checks pass or have approved exceptions
4. Tier B critical regressions are fixed or explicitly deferred
5. no severe internal error remains in supported flows
6. no stale clarification blocks unrelated fresh governed queries
7. no unsupported recommendation, prediction, approval, score, or causal explanation is answered as approved authority
8. docs record what was tested, what passed, what failed, and what remains known limitation

## 9. Next Implementation Step

The next step is Phase 3.6D manual browser UAT pack generation.

That pack should be produced from:

1. the Phase 3.6B minimum quality matrix
2. this Phase 3.6D-0 full capability map
3. active metadata registries
4. completed release-gate evidence
5. known recent live-browser issues and fixes

Only after that pack is executed should the team decide whether Phase 4 can begin.
