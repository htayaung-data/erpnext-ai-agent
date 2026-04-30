# Qwen ERP Phase 3.6 Release Readiness And Quality Exit Gate

Status: proposed bridge milestone
Date: 2026-04-28
Scope: documentation cleanup, broad assistant quality validation, wise fallback behavior, and exit criteria before Phase 4 Complex Business Question Decomposition.

## 1. Purpose

Phase 3.6 exists to protect the next phase.

Phase 4 will decompose larger business questions into multiple governed sub-questions. That will only be reliable if the current assistant already performs well for single-answer, follow-up, clarification, context-switch, and fail-closed behavior.

This phase is therefore not a new feature expansion.

It is a release-readiness and quality gate.

## 2. Decision

Before starting Phase 4, the project should complete a bounded Phase 3.6 gate:

1. refresh and organize current governance docs
2. archive or de-prioritize stale/unused plans without deleting historical contex
3. create a business-question coverage matrix
4. run automated backend replay/smoke checks where possible
5. create a full-project capability inventory and UAT coverage map before manual browser execution
6. run a browser manual UAT pack
7. verify wise fallback behavior for uncertainty, ambiguity, unsupported scope, and unsupported authority
8. only move to Phase 4 after the exit gate passes

## 3. Non-Negotiable Quality Principle

The assistant must not answer confidently when the evidence, scope, authority, or user intent is not clear enough.

Good fallback behavior is part of the product, not an error state.

The correct behavior is:

1. answer directly when the governed evidence is sufficien
2. ask a concise clarification when the user intent is ambiguous
3. ask for the missing business basis when a required report, period, metric, entity, or row is missing
4. show candidate options when multiple governed matches are plausible
5. fail closed politely when the requested authority is not approved
6. offer the closest safe governed alternative when possible
7. never invent unsupported prediction, recommendation, approval, score, or causal explanation

## 4. Wise Fallback Taxonomy

The Phase 3.6 question matrix must include fallback behavior in these categories.

### 4.1 Ambiguous Entity Or Row

Examples:

1. `why is this customer risky?`
2. `tell me more about that one`
3. `show the aging breakdown for this`

Expected behavior:

1. if exactly one current governed focus is clear, continue from i
2. if multiple rows or entities are visible, ask which one
3. show readable options such as rank rows or entity names
4. do not guess the first row unless the user says `first`, `rank 1`, or a named entity

### 4.2 Multiple Candidate Matches

Examples:

1. `do you have product name similar to "Type-C Fast Charge"?`
2. `do you have customer name similar to "Nay Lin Mobile"?`

Expected behavior:

1. if one high-confidence match exists, state the matched governed name
2. if multiple plausible matches exist, show the list directly
3. do not ask a clarification without showing the options
4. do not return default unrelated products or customers

### 4.3 Missing Required Business Basis

Examples:

1. `show me financial statement`
2. `show margin by what?`
3. `show aging for which customer?`

Expected behavior:

1. ask for the missing basis in business language
2. provide only valid choices
3. accept natural variants such as `P&L`, `P & L`, `PL Statement`, and `Profit and Loss`
4. continue safely after the user provides the missing choice

### 4.4 Unsupported Scope Or Inactive Capability

Examples:

1. `show purchase receipt detail` when detail is not approved
2. `show journal entries` if not active
3. `show item list` before item listing support is active

Expected behavior:

1. explain what is supported now
2. do not silently map to a different scope
3. do not pretend unsupported scope is available
4. offer supported alternatives when available

### 4.5 Unsupported Authority

Examples:

1. `who should we collect from first?`
2. `will this customer default next month?`
3. `approve more credit for this customer`
4. `give me a risk score`

Expected behavior:

1. block recommendation, prediction, approval, and hidden scoring unless a governed policy authorizes i
2. provide grounded evidence from the current artifact when available
3. show required policy/evidence gates when the request maps to a known future policy path
4. keep the tone polite and professional, not alarmis

### 4.6 Insufficient Evidence For A Follow-Up

Examples:

1. `why did this increase?`
2. `what caused the drop?`
3. `compare it with last month` when current artifact does not carry trend evidence

Expected behavior:

1. state that the current artifact does not prove the requested comparison or cause
2. ask for or offer a governed trend/comparison query if supported
3. do not infer cause from one snapsho

### 4.7 Context Switch And Cancellation

Examples:

1. `show me suppliers` after customer risk
2. `forget that, show payment entries`
3. `ignore the first question, answer the last one`

Expected behavior:

1. cancel or bypass stale pending ambiguity when the user clearly starts a new governed query
2. do not let an old clarification block an unrelated new question
3. keep current context only when the shared affordance contract supports i

## 5. Business Question Coverage Groups

The Phase 3.6 QA matrix should cover at least these groups.

### 5.1 Master Data

1. customer similar-name search
2. supplier similar-name search
3. item/product similar-name search
4. customer detail
5. supplier detail
6. item/product detail
7. stock by warehouse follow-up

### 5.2 Transaction Listings

1. sales invoices
2. purchase invoices
3. purchase receipts
4. payment entries
5. sales orders
6. delivery notes
7. purchase orders
8. projection refinements such as amount, outstanding, status, and date

### 5.3 Financial Statements

1. missing report clarification
2. Profit and Loss variants
3. Balance Sheet variants
4. Cash Flow variants
5. default open-fiscal-period behavior
6. explicit period override behavior

### 5.4 Composite And KPI Evidence

1. customer risk
2. selected-row explanation
3. selected-row aging breakdown
4. driver explanation
5. blocked causal analysis
6. blocked prediction
7. blocked recommendation
8. margin/profitability ranking

### 5.5 Follow-Up And Context Control

1. `that product`
2. `that supplier`
3. `first customer`
4. `rank 2`
5. `show the list`
6. `go back`
7. `forget that`
8. fresh query after unresolved ambiguity

### 5.6 Presentation Quality

1. no duplicated titles
2. no flattened table-like prose where a list/table is needed
3. no broken markdown emphasis
4. amounts and percentages display correctly
5. answer states whether a list is complete or limited
6. no internal error

## 6. Exit Gate

Phase 3.6 can close only when:

1. active docs are organized and discoverable
2. stale docs are archived or clearly marked historical
3. automated backend checks pass for the selected replay/smoke pack
4. browser UAT passes for the agreed question matrix
5. fallback behavior is polite, professional, and governed
6. no severe context-control blocker remains
7. no unsupported authority is answered as if it were approved
8. known limitations are documented before Phase 4 starts

## 7. Recommended Implementation Slices

### 3.6A Documentation Inventory And Active Index

Create a current-doc index that marks:

1. active roadmap docs
2. completed phase notes
3. historical/archive candidates
4. release-gate docs
5. next-phase design docs

### 3.6B Question Matrix Design

Create the manual and automated question matrix grouped by capability, fallback type, and risk class.

### 3.6C Automated Replay And Smoke Harness

Run or extend backend checks for the matrix areas that can be safely automated.

### 3.6D-0 Full Capability Inventory And UAT Coverage Map

Map the manual browser UAT pack to the full implemented assistant surface, including:

1. active governed scopes
2. registered reports
3. report families
4. composite families and artifacts
5. governed KPI executions
6. completed release-gate and contract-test evidence

This prevents Phase 3.6D from testing only recent fixes while missing older implemented surfaces.

### 3.6D Manual Browser UAT Pack

Produce the exact browser questions, expected behaviors, and pass/fail checklist for manual verification.

### 3.6E Exit Review

Summarize:

1. what passed
2. what failed and was fixed
3. what remains intentionally deferred
4. whether Phase 4.1 can begin

## 8. Recommendation

Start with `3.6A` and `3.6B`.

Do not start Phase 4 until Phase 3.6 passes.

Phase 4 should build on a stable assistant, not compensate for unstable single-answer behavior.
