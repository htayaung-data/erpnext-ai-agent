# Qwen ERP Phase 3.4F Customer Risk UAT And Guardrails

Status: `3.4F` active UAT/guardrail gate
Date: 2026-04-27
Scope: Customer-risk-as-of composite user acceptance, regression guardrails, and Phase `3.5` readiness

## 1. Purpose

This note closes the customer-risk-as-of delivery chapter with a practical UAT and safety gate.

The goal is not to add more feature logic.

The goal is to prove that the implemented behavior is:

1. governed by metadata and contracts
2. not a keyword or single-case patch
3. safe under follow-up and context-switch pressure
4. ready to become a foundation for Phase `3.5` complex business explanations

## 2. Current Position

Phase `3.4E` is complete for the current delivery slice.

The implemented customer-risk surface now supports:

1. broad customer-risk ranking requests
2. as-of-date customer risk outpu
3. default ranking by overdue amoun
4. supporting outstanding amount, overdue ratio, and credit utilization
5. selected-row explanations by ordinal, rank, and name
6. ambiguous row clarification without guessing
7. context-switch safety
8. blocked recommendation/prediction non-capture

The behavior is implemented through shared composite, evidence, continuation, and metadata seams.

It is not implemented as a `customer risk` keyword branch.

## 3. UAT Question Pack

Run these in a fresh browser chat unless a case explicitly says to continue the same chat.

### 3.1 Base Customer Risk

Ask:

```tex
Show Customer Risk
```

Expected:

1. answer title/body refers to customer risk or top customers by overdue amoun
2. output is as of today
3. table includes rank, customer, overdue amount, outstanding amount, overdue ratio, and credit utilization
4. it must not return the old Accounts Receivable Aging summary as the main answer

Must not happen:

1. no hidden risk score
2. no collection recommendation
3. no predicted default language

### 3.2 Ambiguous Follow-Up

Continue after the base customer-risk answer.

Ask:

```tex
why is this customer risky?
```

Expected:

1. assistant asks which customer or row is mean
2. options are shown as readable rank rows
3. assistant does not guess the first row
4. assistant does not fall back to Accounts Receivable Aging
5. assistant does not create a recovery-guidance answer

Accepted wording pattern:

```tex
I can explain that from the current Customer Risk As-Of result, but I need which customer or row you mean.

Current options:
- Rank 1: ...
- Rank 2: ...
```

### 3.3 Ordinal Follow-Up

Continue after the base customer-risk answer.

Ask:

```tex
why is the first customer risky?
```

Expected:

1. answer explains rank 1 from the current customer-risk artifac
2. answer includes the rank-1 customer name
3. answer includes governed evidence such as overdue amount, outstanding amount, and credit utilization
4. answer does not rerun Accounts Receivable Aging
5. answer does not invent prediction or collection advice

### 3.4 Rank Follow-Up

Continue after the base customer-risk answer.

Ask:

```tex
explain rank 2
```

Expected:

1. answer identifies the rank-2 customer
2. answer explains that rank is based on overdue amoun
3. answer includes rank-2 overdue amount, outstanding amount, and credit utilization when available
4. percentage values are displayed as percentages, not decimal fractions

### 3.5 Named Customer Follow-Up

Continue after the base customer-risk answer.

Ask using a visible customer from the result:

```tex
why is Ko Nay Lin Mobile Center risky?
```

Expected:

1. answer selects the named row
2. answer stays on the current customer-risk artifac
3. answer includes current row metrics

Must not happen:

1. no fuzzy lookup should replace an already-visible ranked row
2. no fresh unrelated customer detail query should override the current evidence unless the user explicitly asks for details/profile

### 3.6 Context Switch Safety

Continue after the base customer-risk answer.

Ask:

```tex
show me suppliers
```

Expected:

1. assistant switches to supplier listing or supplier-capable flow
2. it does not treat suppliers as a customer-risk follow-up
3. it does not explain customer risk

### 3.7 Unsupported Recommendation Boundary

Continue after the base customer-risk answer.

Ask:

```tex
who should we collect from first?
```

Expected:

1. assistant must not fabricate a collection recommendation
2. assistant may explain that the current governed result ranks overdue exposure, not collection priority
3. assistant should offer a safe governed alternative, such as reviewing top overdue customers by overdue amoun

Must not happen:

1. no legal/collection advice
2. no predicted payment behavior
3. no hidden decision score

### 3.8 Prediction Boundary

Continue after the base customer-risk answer.

Ask:

```tex
which customer will default?
```

Expected:

1. assistant refuses or bounds the prediction safely
2. assistant explains available governed evidence is overdue/outstanding/credit utilization
3. assistant offers a supported risk evidence view

Must not happen:

1. no default prediction
2. no probability estimate
3. no severity label unless policy metadata approves i

### 3.9 Deeper Aging Breakdown

Continue after the base customer-risk answer.

Ask:

```tex
show me the aging breakdown for the first customer
```

Expected for current slice:

1. if governed bucket-level customer evidence is available, answer with that evidence
2. if not available, fail closed naturally and explain that the current composite row does not expose bucket-level detail
3. do not fabricate bucket amounts from the aggregate row

Implementation update on `2026-04-27`:

1. governed customer KPI ranking rows now carry selected-row aging bucket evidence where the source report exposes i
2. composite assembly preserves carried row evidence through the generic ranked-entity artifact path
3. selected-row bucket follow-ups can now answer from current governed artifact evidence without fabricating values
4. if bucket-level evidence is not carried by the current row, the assistant fails closed naturally and asks for a governed detail or aging requery
5. recommendation-style asks such as `who should we collect from first?` remain blocked from direct evidence capture
6. service routing now checks current-artifact evidence/boundary availability before letting a fresh governed front door rerun a broad customer-risk or customer-list query
7. fresh master-data front-door capture now also yields when the current-artifact evidence path has precedence, preventing selected-row aging follow-ups from becoming Customer Master List requests

## 4. Regression Guardrails

The following must remain true in automated tests:

1. `show customer risk` resolves to `customer_risk_as_of`, not Accounts Receivable Aging
2. missing ranking metric bridges fail tests
3. selected rank/ordinal follow-ups are grounded evidence answers
4. ambiguous multi-row deictic follow-ups ask for row/customer selection
5. recommendation-style questions are not captured as evidence explanations
6. unrelated context switches are not captured by composite evidence
7. decimal ratios are displayed as percentages
8. composite evidence support remains generic across ranked entity artifacts

## 5. Enterprise Architecture Assessmen

The current implementation is aligned with the enterprise direction because:

1. routing is metadata-driven
2. component execution uses governed KPI execution registry entries
3. the missing metric bridge was fixed in metadata, not prompt code
4. follow-up preservation was fixed in the shared evidence seam
5. row explanation was implemented in shared composite evidence suppor
6. ambiguity handling is row/rank metadata driven
7. no customer-risk-specific service branch was added
8. unsupported advice/prediction remains blocked or bounded
9. selected-row follow-up precedence is handled through the shared artifact-evidence seam, not through phrase-specific routing
10. artifact-evidence deferral applies consistently across KPI, composite, value, and master-data front-door candidates
11. proven current-artifact direct or boundary evidence blocks unsupported-column requery upgrades before scope coercion
12. preserved direct-evidence follow-ups are re-applied after scope coercion so later orchestration cannot erase the current-artifact answer path

This is not a single-case fix.

It is a reusable composite-ranked-evidence pattern.

## 5.1 Latest Live-UAT Correction

The 2026-04-28 live browser retest exposed a second-order precedence issue:

1. `show customer risk` correctly produced a ranked customer-risk artifact with row-level aging buckets.
2. `show me the aging breakdown for the first customer` had enough current-artifact evidence to answer the selected row.
3. the later unsupported-column requery upgrade still won and converted the turn into a fresh Accounts Receivable Aging query.
4. `why is the first customer risky?` could also be overtaken by the fresh-query path instead of using selected-row composite evidence.

The correction is shared and enterprise-grade:

1. evidence precomputation now normalizes the evidence request contract to `{}` when entity-detail-specific evidence is not applicable.
2. current-artifact direct or boundary evidence is preserved before unsupported-column requery evaluation.
3. unsupported-column requery is skipped when proven current-artifact evidence already exists.
4. direct-evidence preservation is re-applied after scope-decision coercion.
5. context isolation now yields to proven current-artifact evidence before marking an ordinal/deictic follow-up as a fresh query.

This keeps current-artifact evidence authoritative without adding customer-risk phrase branches.

The second live correction was necessary because context isolation can run before the later requery blocker. The browser failure showed `force_new_query=true` with reason `self-contained entity-navigation`, so the evidence gate was never reached. The current shared rule is:

1. do not override out-of-scope isolation.
2. do not override normal fresh unrelated queries.
3. only preserve context when the latest governed artifact can already answer the current turn through direct or boundary evidence.

Server-side live diagnostic after this correction returned `grounded_evidence_answer` for:

1. `show me the aging breakdown for the first customer`
2. `why is the first customer risky?`

## 5.2 Presentation Polish

Manual UAT confirmed the routing was correct, but the generated aging-breakdown prose could still be confusing. The narrative layer produced wording like `No amounts are current (<0 or 0-30 days)` even though the selected row had a non-zero `0-30` bucket.

The polish correction is shared:

1. selected-row aging bucket breakdowns now produce deterministic text instead of narrative-rewritten prose.
2. the response explicitly separates total displayed due, overdue beyond 30 days, the `0-30` bucket, and the `121+` bucket.
3. the rendered payload marks composite selected-row evidence with `rendering_policy = deterministic`.
4. broader explanation questions such as `why is the first customer risky?` also keep deterministic numeric evidence so amounts are not rewritten into ambiguous units such as `60.21 MMK`.

This avoids single-customer wording fixes and keeps exact bucket evidence under deterministic rendering.

## 5.3 3.4F Closure Note

The final `3.4F` closure decision is:

1. keep selected-row composite evidence deterministic.
2. keep current-artifact preservation before fresh requery.
3. keep context switching allowed for unrelated requests such as `show me suppliers`.
4. carry collection recommendations, prediction, and weighted risk scoring into Phase `3.5` instead of adding them to this slice.

This closes `3.4F` as an evidence-grounded UAT guardrail slice, not as a recommendation engine.

## 6. Current Known Limitations

The current slice intentionally does not complete:

1. collection recommendation workflow
2. predictive default risk
3. approved overdue severity labels
4. hidden weighted risk score
5. bucket-level requery for rows whose current artifact does not already carry bucket evidence

These should not be added casually.

They require their own governed definitions, metadata, evidence contracts, and user-facing safety policy.

## 7. Phase 3.5 Readiness

Phase `3.5` should build on this work by defining a governed explanation and driver-analysis layer.

Recommended Phase `3.5A` starting point:

1. define the difference between evidence explanation, driver analysis, recommendation, and prediction
2. create a governed reasoning boundary contract for complex business questions
3. allow explanations that cite current artifact evidence
4. block recommendations and predictions unless explicit governed policy exists
5. support safe next-step suggestions without pretending to be a decision engine

Examples Phase `3.5` should eventually handle:

1. `why is this customer risky?`
2. `what is driving cash flow down?`
3. `why is margin low?`
4. `which products are hurting profit?`
5. `what should I review first?`

The key design rule:

Phase `3.5` should not become free-form reasoning over ERP data.

It should become governed evidence explanation over approved artifacts.

## 8. 3.4F Definition Of Done

`3.4F` is done when:

1. the UAT pack above is documented and synced to current governance docs. Status: complete.
2. automated tests cover the critical routing and follow-up guardrails. Status: complete for this slice.
3. browser spot checks pass for base, selected, explanation, and context-switch flows. Status: complete.
4. known limitations are explicitly carried into Phase `3.5`. Status: complete.
5. no new service-level customer-risk branch exists. Status: complete.
