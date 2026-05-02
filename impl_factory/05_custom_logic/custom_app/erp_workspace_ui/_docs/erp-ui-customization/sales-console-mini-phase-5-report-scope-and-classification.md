# Sales Console Mini-Phase 5 Report Scope And Classification

Status: active report-family alignment note
Date: 2026-04-18
Last updated: 2026-04-23
Source of truth: `sales_console.js`, `sales_console/service.py`, current role-based report catalog

## 1. Purpose

This note defines the report scope still remaining inside the Sales Console domain.

It exists to answer:

1. which native reports are still opened from Sales Console
2. what each report is actually meant to support in business terms
3. which reports belong to the same report family
4. what order they should be productized in

Mini-Phase 5 should not begin with page drawing.

It should begin with business classification, because these report names come from native ERP vocabulary, not productized user intent.

## 2. Current Report Scope

The current Sales Console report family is centered on these productized report-card meanings:

1. `Sales Analytics`
2. `Sales Order Analysis`
3. `Trend Analysis`
4. `Lost Quotations`
5. `Collections Status`
6. `Item-wise Sales History`

`Collections Status` replaces the earlier payment-terms direction because invoice settlement and receivable exposure are the stronger sales truth.

`Trend Analysis` replaces the earlier visible `Quotation Trends` direction. It uses one controlled Sales Console page with a Document Type filter for `Sales Invoice`, `Sales Order`, and `Quotation`.

So the remaining Sales Console scope is not “more worklists”.

It is now a report-family replacement problem.

## 3. Core Product Decision

The report family should be treated as a separate archetype from the operational worklists.

Reason:

1. worklists answer “what needs action now”
2. reports answer “what pattern, exposure, or performance story is true”
3. reports need stronger summary structure and more filter trust
4. reports still need dense readable tables, but not every report is a queue

Therefore Mini-Phase 5 should introduce a dedicated shared report shell.

It should stay in the same visual system as the worklists, but it should not simply clone the worklist page.

## 4. Report Families

The current report set falls into four business families.

### 4.1 Performance summary reports

Purpose:

1. answer high-level commercial performance questions
2. support management review before deeper drilling

Reports:

1. `Sales Analytics`

Primary user:

1. sales manager
2. executive review roles

Primary decision:

1. are sales results moving in the right direction
2. where should deeper review start

### 4.2 Execution review reports

Purpose:

1. review order quality and downstream execution posture
2. expose operational and commercial follow-through issues

Reports:

1. `Sales Order Analysis`
2. `Collections Status`

Primary user:

1. sales manager
2. sales executive
3. key account sales

Primary decision:

1. which orders need deeper execution or settlement review
2. where receivable exposure or settlement delay creates customer-facing risk

### 4.3 Trend and conversion reports

Purpose:

1. understand quotation and order movement over time
2. understand conversion direction, slowing momentum, and loss patterns

Reports:

1. `Trend Analysis`
2. `Lost Quotations`

Primary user:

1. sales manager
2. executive review
3. selected sales executives for quotation review

Primary decision:

1. whether pipeline is strengthening or weakening
2. where commercial loss is happening
3. which quotation behavior needs intervention

### 4.4 Product and customer history reports

Purpose:

1. review item-level commercial history during customer discussion or deeper analysis

Reports:

1. `Item-wise Sales History`

Primary user:

1. sales executive
2. key account sales
3. sales manager

Primary decision:

1. what has already been sold, at what level, and in what pattern

## 5. Report Classification Matrix

| Report | Family | Main user | Main question | Recommended first surface | Priority |
| --- | --- | --- | --- | --- | --- |
| Sales Analytics | Performance summary | Manager / executive | Are sales results moving correctly? | summary + KPI + table | 1 |
| Sales Order Analysis | Execution review | Manager / sales | Which orders need deeper execution review? | KPI + dense table | 1 |
| Trend Analysis | Trend and conversion | Manager / sales | Are billed, ordered, or quoted values moving correctly? | Document Type filter + KPI + trend summary + table | 1 |
| Lost Quotations | Trend and conversion / exception | Manager / executive | Why are we losing business? | exception summary + table | 2 |
| Collections Status | Settlement / receivables review | Manager / sales | Which customers or invoices carry real receivable exposure? | exposure summary + table | 2 |
| Item-wise Sales History | Product history | Sales / manager | What item history should guide this discussion? | filter-first history table | 2 |

## 6. Recommended Implementation Order

Mini-Phase 5 should not implement reports in native route order.

It should implement them in archetype order.

### 6.1 First report cluster

Build these first:

1. `Sales Analytics`
2. `Sales Order Analysis`
3. `Trend Analysis`

Reason:

1. together they define the report shell
2. together they cover summary, execution review, and trend review
3. they are broad enough to expose architecture flaws early

### 6.2 Second report cluster

Build these next:

1. `Lost Quotations`
2. `Collections Status`
3. `Item-wise Sales History`

Reason:

1. they are more specialized
2. they depend on the report shell already being stable
3. they add exception, collections, and history variants after the base is proven

## 7. Product Rules For Sales Console Reports

Every Sales Console report page should follow these product rules:

1. table-first, not chart-first
2. summary must answer the first business question quickly
3. filters must be operational and minimal
4. row density must support real review, not decorative spacing
5. export/readability beats visual novelty
6. no duplicated information across header, KPI row, and table
7. if a chart is used later, it must clarify a pattern better than the table

## 8. Immediate Next Move

The next implementation slice after this classification is:

1. define the shared report archetype
2. define the normalized backend payload contract
3. build one shared report runtime before implementing the first report page
