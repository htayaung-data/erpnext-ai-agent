# Qwen ERP NBU-0 Failure Inventory And Contract Fit

Status: implemented as baseline inventory
Date: 2026-04-30
Scope: natural business understanding failures found during Phase 3.6 manual browser UAT and how they map to shared NBU seams

## 1. Purpose

NBU-0 records the current natural-language failures as shared-seam evidence.

The goal is not to patch each prompt.

The goal is to ensure NBU-1 and later slices solve the underlying production behavior classes:

1. natural intent understanding
2. context and row reference resolution
3. governed evidence planning
4. authority boundary recognition
5. stale-context isolation
6. professional fallback wording

## 2. Baseline Finding

The assistant already has many governed data surfaces and semantic helper modules.

The quality gap is not missing ERP data alone.

The quality gap is fragmented understanding:

1. frontdoor decides route ownership
2. fresh-query interpreter chooses reports/capabilities
3. follow-up interpreter handles local refinements
4. composite frontdoor handles some governed composites
5. reasoning activation handles some explanation/why/recommendation language
6. boundary support handles unsupported evidence or authority

Because these decisions are split, natural business questions can fall between lanes.

## 3. Failure Inventory

### NBU-F001: Customer Risk Broad Ask Routes To AR Aging

Prompt:

`show customer risk`

Observed:

Returned Accounts Receivable Aging instead of Customer Risk As-Of ranked composite in some browser runs.

Expected:

Resolve to governed `customer_risk_as_of` composite when active.

Shared seam:

1. natural business understanding
2. composite-family candidate validation
3. fresh query versus composite frontdoor precedence

NBU fit:

Candidate interpretations should include `customer_risk_as_of` and `accounts_receivable_aging`, then validation/system confidence should choose the governed customer-risk composite when the request asks for risk/risky customers.

### NBU-F002: Row Reference Not Resolved From Current Table

Prompts:

1. `why is the first customer risky?`
2. `Explain Rank 2 Customer`
3. `In your above Customer by AR table, who is in Second position?`

Observed:

The assistant sometimes repeated the whole report, switched scope, or produced definition-style fallback.

Expected:

Resolve first/rank 2/second position against the current visible ranked/list artifact.

Shared seam:

1. generic row reference resolution
2. artifact evidence compatibility
3. response mode selection

NBU fit:

`target_reference` should normalize to `rank_n`, with row index and artifact id. The action should become `answer_from_current_artifact` when the row and fields exist.

### NBU-F003: Ambiguous Deictic Reference Needs Clarification

Prompt:

`why is this customer risky?`

Observed:

In some cases the assistant guessed or reran a broad report.

Expected:

If multiple customers are visible and no selected row exists, ask which customer/row.

Shared seam:

1. context-reference clarity
2. clarification rendering

NBU fit:

`target_reference` should be `unclear`, action should be `ask_clarification`, and options should be rows from the current artifact.

### NBU-F004: Missing Field Should Requery When Governed Source Exists

Prompt:

`do you know the credit limit of that customer?`

Observed:

The assistant returned a generic boundary that the current AR artifact lacks credit limit.

Expected:

If selected customer is known and a governed customer credit/detail source exists, plan a governed requery. If not available, explain the missing evidence naturally.

Shared seam:

1. evidence need detection
2. governed requery planner
3. selected entity carryover

NBU fit:

`evidence_need` should be `needs_governed_requery`, not a terminal boundary, when a compatible governed source exists.

### NBU-F005: User Correction Should Override Wrong Context

Prompts:

1. `okay show me again your customer risky table`
2. `I am not asking plain list, I am asking customer risky`
3. `you don't understand what I request?`
4. `Show me top 10 customers by Risky`

Observed:

The assistant moved into Customer Master List context and then stayed trapped by that context.

Expected:

User correction should trigger reinterpretation and clear stale context when the new business target is explicit.

Shared seam:

1. correction intent
2. stale-context isolation
3. fresh governed query override

NBU fit:

`requested_action` should include correction/restore semantics where applicable, and action should become `execute_fresh_governed_query` or `ask_clarification`, not continue stale master-data context.

### NBU-F006: Recommendation Or Prediction Must Boundary Professionally

Prompts:

1. `who should we collect from first?`
2. `will the first customer default next month?`
3. `what caused the first customer's risk to increase?`

Observed:

Later hardening improved this for customer risk, but this must be generic.

Expected:

Block recommendation, prediction, and causal/change-driver analysis unless an approved policy/artifact exists. Provide grounded evidence or required policy/evidence path.

Shared seam:

1. authority class recognition
2. policy validation
3. professional boundary response

NBU fit:

`authority_class` should distinguish `recommendation`, `prediction`, and `unsupported_analysis`, then action should become `reject_with_boundary` or `show_supported_options`.

### NBU-F007: AR/AP Health Natural Wording Can Route To AR Aging Only

Prompt:

`evaluate company health based on AR/AP`

Observed:

Sometimes returned Accounts Receivable Aging instead of AR/AP Working Capital Health.

Expected:

Route to governed AR/AP working-capital composite when both AR and AP concepts plus health/evaluation intent are present.

Shared seam:

1. multi-domain concept interpretation
2. composite read planning
3. self-contained fresh query override

NBU fit:

Candidate interpretations should include working-capital health composite and AR aging. System confidence should prefer composite when both receivable and payable are present.

### NBU-F008: Context Switch Must Beat Prior Follow-Up State

Prompts:

1. `show me suppliers` after customer risk
2. `do u have customer name similar to "Nay Lin Mobile"?` after unresolved product candidates
3. `ignore that, show me suppliers`

Observed:

Previously, stale ambiguity or prior context could block unrelated fresh requests.

Expected:

Explicit self-contained new request or cancellation must override pending context.

Shared seam:

1. context priority rules
2. cancellation intent
3. fresh request isolation

NBU fit:

Action should become `clear_pending_context` plus `execute_fresh_governed_query`, or direct `execute_fresh_governed_query` when no cancellation phrase is needed.

### NBU-F009: Fallback Wording Exposes Internal Mechanics

Observed:

Fallback responses sometimes mention internal source/artifact limitations in a way that feels robotic or ugly.

Expected:

User-facing response should be business-natural, with technical details kept in trace.

Shared seam:

1. response rendering
2. boundary/fallback policy

NBU fit:

Action decision should include `response_mode`, and the renderer should use professional wording by default.

## 4. Contract Fit Summary

These failures require the NBU contract to support:

1. ranked candidate interpretations
2. system confidence separate from model confidence
3. target reference normalization
4. current versus previous artifact reference
5. selected entity carryover
6. evidence need classification
7. authority class classification
8. action decision as a first-class payload
9. trace summary for audit and debugging
10. professional response mode selection

## 5. NBU-0 Exit Gate

NBU-0 is complete when:

1. known manual-browser failures are recorded
2. each failure maps to a shared seam
3. each failure maps to required NBU contract fields
4. none are framed as single-prompt hardcoded fixes

Status: complete for the current baseline.
