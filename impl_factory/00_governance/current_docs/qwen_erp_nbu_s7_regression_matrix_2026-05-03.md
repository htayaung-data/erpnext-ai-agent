# Qwen ERP AI Assistant: NBU-S7 Regression Matrix

Date: 2026-05-03

Status: Automated gate complete

Owner: AI Assistant Stabilization

## 1. Purpose

`NBU-S7` converts the Natural Business Understanding stabilization work into a repeatable regression matrix.

This is not Phase 4 feature expansion. It is a quality gate that proves the assistant can keep the right business context, select the latest relevant result, preserve requested metrics, add requested projections, and fail politely when a request needs unsupported policy, prediction, or cross-domain reasoning.

## 2. Enterprise Principle

User question flow:

1. User asks in natural business language.
2. NBU interprets intent, current visible context, entity references, confidence, and authority.
3. Contracts verify whether the request can be answered from the current result, requires a governed requery, requires clarification, or must stop at a safe boundary.
4. Governed families execute only when supported.
5. Renderers explain results in professional business language without leaking implementation terms.

This matrix protects that principle across common business-user behavior, not just one browser prompt.

## 3. Matrix Groups

### 3.1 Context Matrix

Goal: prove the assistant chooses the latest relevant visible result and does not reuse stale AR, AP, supplier, customer, product, or document context.

Automated profile:

```text
nbu_s7_context_matrix
```

Cases:

1. `nbu_s7_same_session_fresh_query`
2. `nbu_s7_visible_context_latest_artifact`
3. `nbu_governed_requery`

Required behavior:

1. A self-contained new question must route as a new governed query.
2. A rank/list follow-up must bind to the latest visible compatible table or list.
3. "Who is second" after supplier list must answer supplier rank 2, not stale customer rank 2.
4. "Who is second" after sales invoices must answer invoice row 2, not stale supplier or AR context.

### 3.2 Projection Matrix

Goal: prove follow-up projections add or reshape requested fields while preserving the original ranking metric unless the user explicitly asks to switch metrics.

Automated profile:

```text
nbu_s7_projection_matrix
```

Cases:

1. `nbu_s7_subject_switch`
2. `nbu_s7_ranking_projection_continuation`
3. `nbu_s7_product_quantity_projection`

Required behavior:

1. "Show in million" must preserve the ranked metric and only change display scale.
2. "Show together with Qty" must add quantity while preserving revenue as revenue.
3. A subject switch must not drag stale focus into the new family.

### 3.3 Boundary And Recovery Matrix

Goal: prove unsupported decisions, predictions, guarantees, and policy asks are handled professionally without internal terminology or fake certainty.

Automated profile:

```text
nbu_s7_boundary_recovery_matrix
```

Cases:

1. `nbu_s7_safe_boundary_language`
2. `phase8_fresh_query_override`
3. `phase8_recovery_execution`
4. `h4_recommendation_guarantee`

Required behavior:

1. A prediction request such as "will this customer default next month?" must not predict without an approved model or policy.
2. A decision request such as "who should we collect from first?" must show available evidence but not prescribe action without an approved rule.
3. The assistant must not expose terms such as runtime, contract, artifact, governed boundary, internal tool names, or registry IDs to business users.
4. If options are offered, every option must be executable or clearly marked as a clarification path.

## 4. Full Automated Profile

The full NBU-S7 profile combines the segmented profiles:

```text
nbu_s7_regression_matrix
```

It should be used only after the segmented profiles pass, because segmented execution identifies the failing seam faster and avoids hiding failures inside a long aggregate run.

## 5. Exit Gate

`NBU-S7` is complete only when all of the following are true:

1. Enterprise guardrail audit is green.
2. Bounded release-gate unit tests are green.
3. Live bounded-gate inventory exposes all NBU-S7 profiles and cases.
4. `nbu_s7_context_matrix` is green.
5. `nbu_s7_projection_matrix` is green.
6. `nbu_s7_boundary_recovery_matrix` is green.
7. No NBU-S7 failure is fixed by a one-off browser phrase patch.
8. Any failure is fixed through shared NBU contracts, context selection, renderers, or governed family support.
9. Manual browser UAT questions are prepared for `NBU-S8`.

## 5.1 Automated Verification Record - 2026-05-03

Current automated status:

1. Enterprise guardrail audit: passed.
2. Targeted unit suites: passed.
3. `nbu_s7_context_matrix`: passed 3 / 3 cases in 218.790 seconds.
4. `nbu_s7_projection_matrix`: passed 3 / 3 cases in 93.581 seconds.
5. `nbu_s7_boundary_recovery_matrix`: passed 4 / 4 cases in 167.352 seconds.

Targeted unit suites run:

```text
python3 -m unittest \
  ai_assistant_ui.tests.test_composite_evidence_support \
  ai_assistant_ui.tests.test_financial_statement_followup_clarification_contracts \
  ai_assistant_ui.tests.test_bounded_release_gate
```

Result:

```text
Ran 51 tests in 0.168s
OK
```

Guardrail command:

```text
python3 scripts/check_qwen_enterprise_guardrails.py
```

Result:

```text
Qwen enterprise guardrail audit: PASS
```

Important interpretation:

1. The S7 matrix is green on the live backend container path, not only in local code.
2. The final boundary/recovery rerun confirmed business-facing wrapper language after removing user-facing internal wording such as `current governed support`.
3. The S7 fixes were applied through shared context, projection, boundary, and renderer seams rather than one prompt-specific browser patches.
4. S7 does not authorize Phase 4 by itself; it authorizes moving to NBU-S8 Manual Browser UAT.

## 6. Manual Browser UAT Hand-Off

Automated NBU-S7 is green. The next step is `NBU-S8` Manual Browser UAT.

Manual UAT should cover:

1. AR/customer risk context and rank follow-ups.
2. Supplier/AP context and rank/detail follow-ups.
3. Sales invoice document context and row follow-ups.
4. Product/customer revenue ranking projections, including million display and quantity additions.
5. Financial statement clarifications and section details.
6. Unsupported prediction/recommendation boundaries.
7. Natural-language confusion recovery and professional clarification.

Manual script:

```text
qwen_erp_nbu_s8_manual_browser_uat_2026-05-03.md
```

No Phase 4 complex business questions should start until `NBU-S8` confirms the browser behavior is aligned with the automated gates.
