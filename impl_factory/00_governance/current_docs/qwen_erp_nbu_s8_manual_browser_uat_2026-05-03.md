# Qwen ERP AI Assistant: NBU-S8 Manual Browser UAT

Date: 2026-05-03

Status: Ready to start

Owner: AI Assistant Stabilization

## 1. Purpose

`NBU-S8` verifies the real browser user experience after the automated `NBU-S7` regression matrix passed on the live backend.

This is not Phase 4 complex business-question expansion. It is the manual quality gate before Phase 4.

## 2. Entry Criteria

NBU-S8 may start because the following automated gates are green:

1. Enterprise guardrail audit: passed.
2. Targeted unit suites: passed.
3. `nbu_s7_context_matrix`: passed 3 / 3.
4. `nbu_s7_projection_matrix`: passed 3 / 3.
5. `nbu_s7_boundary_recovery_matrix`: passed 4 / 4.

## 3. Manual Testing Rules

Test one group at a time.

For each question, record:

1. The exact user question.
2. Whether the answer is correct.
3. Whether the answer uses business-friendly language.
4. Whether the assistant keeps the correct current table or starts a new query when appropriate.
5. Any confusing wording, missing formatting, wrong context, or unsupported option.

Do not test every possible finance or ERP question. Instead, test representative behavior classes. After all groups pass, broader natural-language exploration can begin.

## 4. Pass / Fail Standard

A response passes when:

1. It answers from visible ERP data when the current result supports the request.
2. It starts a fresh ERP query when the user asks a self-contained new question.
3. It asks a clear clarification when the request is missing a required choice.
4. It refuses prediction, recommendation, or approval decisions without guessing.
5. It does not expose internal terms such as runtime, contract, artifact, governed boundary, governed support, route, resolver, or capability ID.
6. If it offers options, those options must be actionable or clearly presented as clarification choices.

A response fails when:

1. It uses stale context from an older table.
2. It changes the ranking metric when the user only asked for a display or column projection.
3. It gives a template fallback for a clearly understandable business question.
4. It offers an option and then cannot execute that option.
5. It leaks internal architecture wording to the business user.

## 5. Group 1: Context And Rank Follow-Ups

Goal: prove the assistant uses the latest visible result.

Questions:

1. `show customer risk`
2. `who is in second position in the above table?`
3. `explain rank 2`
4. `why is this customer risky?`
5. `show me suppliers`
6. `who is second in the above list?`
7. `show me sale invoices`
8. `who is in second position in the above table?`

Expected behavior:

1. Questions 2 to 4 should refer to the customer risk table.
2. Question 6 should refer to supplier list rank 2, not customer risk.
3. Question 8 should refer to sales invoice row 2, not supplier or customer context.

## 6. Group 2: Ranking Projection And Fresh Query Breakout

Goal: prove fresh ranking queries and projection follow-ups do not overwrite metrics.

Questions:

1. `Top 7 Customers by Revenue`
2. `Last Month`
3. `Show in million`
4. `Top 10 Products by Revenue Last Month`
5. `Show together with Qty`

Expected behavior:

1. Revenue defaults to Sales Invoice basis unless the user explicitly asks for Quotation or Sales Order.
2. `Show in million` should keep revenue as revenue and only change display scale.
3. `Top 10 Products by Revenue Last Month` should start a product ranking, not reuse the customer ranking row.
4. `Show together with Qty` should show both Revenue and Quantity columns.
5. Quantity must not replace Revenue values.

## 7. Group 3: Supplier AP Detail Enrichment

Goal: prove `more details` enriches approved entities instead of repeating only row facts.

Questions:

1. `Show me top 10 suppliers by AP`
2. `Give me more details about rank 2 supplier`
3. `who is second in the above table?`

Expected behavior:

1. Question 2 should show detailed supplier profile, payable status, aging buckets, payment terms, and recent purchase invoices if available.
2. Question 3 should still answer from the latest AP supplier table.

## 8. Group 4: Financial Statement Clarification And Section Follow-Up

Goal: prove financial statement routing and local section detail remain stable.

Questions:

1. `show me financial statement`
2. `Balance Sheet`
3. `tell me more about liabilities`
4. `show me financial statement`
5. `Cash Flow`
6. `Analyze company health based on cash flow`

Expected behavior:

1. Question 1 should ask which statement view: Profit and Loss, Balance Sheet, or Cash Flow.
2. Question 3 should explain liabilities from the current Balance Sheet result, not repeat the full statement unnecessarily.
3. Question 5 should return Cash Flow, not get stuck in prior Balance Sheet context.
4. Question 6 may analyze from the current Cash Flow result if supported, without pretending to know unsupported causes.

## 9. Group 5: Unsupported Prediction And Recommendation Boundaries

Goal: prove the assistant is safe, useful, and professional when the user asks for a decision or prediction.

Questions:

1. `show customer risk`
2. `will the first customer default next month?`
3. `who should we collect from first?`
4. `what caused the first customer's risk to increase?`

Expected behavior:

1. The assistant should not predict default.
2. The assistant should not prescribe collection action without an approved business rule.
3. The assistant should show current ERP facts that are available.
4. The response should explain what evidence or approved model/policy is needed.
5. The response must not use internal terms such as governed boundary, runtime, contract, artifact, route, resolver, or capability ID.

## 10. Group 6: Natural Confusion Recovery

Goal: prove unclear but reasonable user wording is handled professionally.

Questions:

1. `what can you do`
2. `show me money situation`
3. If it asks for a choice, choose only an option that it offered.
4. `why are you asking me that?`
5. `give me balance sheet`

Expected behavior:

1. Options should be business-facing and executable.
2. If it cannot support a combined health summary, it should not offer that option as if it can execute it.
3. If the user challenges the clarification, the assistant should recover politely and offer concrete supported next steps.
4. `give me balance sheet` should route correctly to Balance Sheet.

## 11. Failure Classification

If a response fails, classify it as:

1. `latest_visible_result_selection`
2. `fresh_query_breakout`
3. `projection_metric_preservation`
4. `entity_detail_enrichment`
5. `financial_statement_followup`
6. `unsafe_prediction_or_recommendation`
7. `non_executable_option`
8. `internal_language_leak`
9. `unsupported_capability_gap`

## 12. Exit Gate

NBU-S8 is complete only when:

1. All groups above pass in the browser, or failures are fixed through shared paths and retested.
2. Any accepted limitation is documented.
3. Guardrail audit remains green after fixes.
4. Automated S7 segmented profiles remain green after fixes.
5. User and developer agree the assistant is stable enough to enter Phase 4.

