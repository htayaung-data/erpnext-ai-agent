# Qwen ERP Context Authority Acceptance Pack

Date: 2026-05-11
Status: active manual browser acceptance gate
Branch: `feature/ai-assistant`
Owner: AI Assistant context authority stabilization track

## 1. Purpose

This acceptance pack is the manual browser QA gate for `UX-S6` context authority behavior.

It exists because context failures are not normal single-question failures. A wrong answer can happen even when ERP data is correct if the assistant binds a follow-up to the wrong visible table, wrong family, wrong row grain, stale drilldown, or unsupported object type.

This pack must be run before any future context-authority, visible-table, reference resolver, or follow-up routing release is accepted.

## 2. Six-Fact Enterprise Gate

Problem class:

Context authority must be repeatably proven across multi-turn browser flows. The system must bind ordinal, object, table, previous-table, and out-of-range references to the correct visible evidence, not to keyword guesses or stale artifacts.

Rejected MVP approach:

Do not validate by asking a few random questions and judging from memory. Do not accept "it worked once" as proof. Do not fix failures by adding phrase-specific branches for "second", "above table", "same table", "customer", "supplier", or "invoice".

Enterprise design:

Use a canonical acceptance checklist with exact prompt sequences, expected visible answers, expected trace inspection fields, and fail conditions. Trace inspection is used as the operator audit layer, not as business-user-facing behavior.

Metadata / contract dependency:

The acceptance pack depends on these governed contracts and fields:

1. `qwen_visible_context_followup_trace_contract`
2. `qwen_visible_context_authority_trace_inspection_contract`
3. `frame_arbitration.status`
4. `frame_arbitration.relation`
5. `frame_arbitration.requested_object_label`
6. `frame_arbitration.selected_frame_id`
7. `frame_arbitration.selected_business_object_type`
8. `frame_arbitration.selected_evidence_scope`
9. `frame_arbitration.selection_strategy`
10. `frame_arbitration.candidate_frames`
11. `frame_arbitration.rejected_frames`
12. `authority_observability.selected_recovery_source`

Cross-family tests:

The pack covers:

1. Profit and Loss / COGS source documents
2. Accounts Receivable customer aging
3. Accounts Receivable overdue comparison
4. Accounts Payable supplier aging
5. Accounts Payable source invoices
6. Product revenue ranking and projection
7. Mixed-family switching
8. Out-of-range visible rank boundaries
9. Unsupported object-type boundaries
10. Unsupported prediction and decision-policy boundaries

Definition of done:

The pack passes only when:

1. every expected row answer is correct;
2. every inspected trace selects the expected table or safely rejects the unsupported object;
3. no answer reuses a stale table from another family;
4. unsupported requests stop safely without prediction or fake policy;
5. trace output is readable enough for an operator to identify selected and rejected frames;
6. all failures are classified as product defects, deferred limitations, or invalid test setup before release.

## 3. Run Rules

1. Run the pack in the browser against the active backend after deployment.
2. Use a fresh chat/session for each scenario unless the scenario explicitly tests cross-family switching.
3. Do not skip trace-inspection prompts. The visible answer proves user behavior; the trace proves authority reasoning.
4. Treat trace inspection as operator QA output. Business users should not need to ask for traces in normal operation.
5. If a value changes because the ERP date advances, keep the authority expectations but update row values only after confirming the new ERP data.

## 4. Universal Pass / Fail Criteria

Pass criteria:

1. The assistant answers from the latest compatible visible table unless the user explicitly asks for a previous table.
2. "Same table" stays on the selected table from the preceding visible-context answer.
3. Typed references such as customer, supplier, invoice, document, product, and source document must select only compatible visible row types.
4. Out-of-range ranks must refuse from the current visible table row count.
5. Trace inspection must show selected frame, relation, object type, candidate frames, rejected frames, and rejection reason where applicable.
6. Business answers must stay professional and must not expose internal contract names, runtime details, or debug fields.

Fail criteria:

1. Any stale family answer, such as AP answering from AR, product answering from AP, or invoice answering from COGS source documents.
2. Any hallucinated row beyond visible row count.
3. Any unsupported prediction stated as a forecast.
4. Any unsupported decision recommendation stated as policy without an approved decision policy.
5. Any trace where selected table, object type, or rejection reason contradicts the visible answer.
6. Any "Which report would you like me to use?" response when the current visible context is sufficient.

## 5. Scenario A: P&L COGS Source Document Authority

Goal:

Prove a COGS detail table beats the broader P&L summary table for ordinal follow-ups, and unsupported invoice references do not reuse document rows.

Prompt sequence:

```text
give me P & L statement
give me more about COGS
who is second in the above table?
show latest context authority trace
who is second invoice in the above context?
show latest visible context authority trace
who is second in same table?
```

Expected visible answers:

1. `who is second in the above table?` returns `Delivery Note MAT-DN-2026-00336`.
2. The row facts include `Net Line Impact: 11.3 MMK Million` and `Share Of Line: 17.3%`.
3. `who is second invoice in the above context?` refuses because there is no visible invoice table in scope.
4. `who is second in same table?` still returns `Delivery Note MAT-DN-2026-00336`.

Expected trace after the successful ordinal answer:

1. `Status`: `resolved`
2. `Relation`: `current_table`
3. `Selected object type`: `document`
4. `Selected table`: COGS source-detail breakdown
5. `Selection strategy`: `current_table:authority_rank`
6. Rejected frame includes the P&L summary with `lower_authority_candidate`

Expected trace after the invoice boundary:

1. `Status`: `missing_requested_object`
2. `Requested object`: `invoice`
3. `Selected frame`: `none`
4. Candidate/rejected frame is the COGS document table
5. Rejection reason is `requested_object_type_mismatch`

## 6. Scenario B: AR Aging And Overdue Comparison Authority

Goal:

Prove a generated AR comparison table becomes the current visible authority, even when the earlier Top 10 Customers table remains in history.

Prompt sequence:

```text
show customer risk
Give me key insights as Business Consultant
yes
who is fourth in the above table?
who is second in same table?
give me more about Rank 11 customer
show latest context authority trace
```

Expected visible answers:

1. `who is fourth in the above table?` returns `Shwe Li Road Mobile Wholesale`.
2. `who is second in same table?` returns `Ko Nay Lin Mobile Center`.
3. `give me more about Rank 11 customer` refuses from the current comparison table row count, normally `only 7 visible rows`.
4. It must not answer from the earlier Top 10 Customers table.

Expected trace:

1. Selected table is the AR overdue comparison table.
2. Selected object type is `party` or equivalent party/customer row type.
3. Out-of-range evidence references the current comparison table row count, not Top 10 Customers.

## 7. Scenario C: AP Supplier Table And Invoice Detail Boundary

Goal:

Prove supplier rows and invoice rows are typed separately, and typed references can intentionally return to the supplier table after invoice detail.

Prompt sequence:

```text
Show me top 5 suppliers by AP
who is second in the above table?
Why is this supplier concerning?
who is second in same table?
who is second supplier in the above context?
who is second invoice in the above context?
show latest context authority trace
```

Expected visible answers:

1. Supplier rank 2 is `Sunflower Accessories Co.`.
2. After the supplier concern detail, `who is second in same table?` returns invoice `ACC-PINV-2026-00053`.
3. `who is second supplier in the above context?` returns `Sunflower Accessories Co.`, not the invoice row.
4. `who is second invoice in the above context?` returns `ACC-PINV-2026-00053` when the invoice breakdown is visible in the current context.

Expected trace:

1. Supplier typed request selects supplier table with object type `supplier`.
2. Invoice typed request selects invoice breakdown with object type `invoice`.
3. No stale P&L, AR, or product table is selected.

## 8. Scenario D: Product Ranking Projection Authority

Goal:

Prove table projection changes such as showing millions or quantity do not break row rank authority.

Prompt sequence:

```text
Top 7 Products by Revenue Last Year
Show in Million
who is second in the above table?
who is second in same table?
who is fifth product in the above context?
tell me more about Rank 8 product
show latest context authority trace
```

Expected visible answers:

1. Rank 2 is `Xiaomi Redmi Note 13 (8GB 256GB)`.
2. Same-table repeat returns the same product.
3. Fifth product is `Samsung PD Charger 25W`.
4. Rank 8 refuses because the visible table has only 7 rows.

Expected trace:

1. Selected object type is product/item.
2. Selected table is the latest product ranking/projection table.
3. Out-of-range uses row count 7.

## 9. Scenario E: Mixed-Family Previous Table Authority

Goal:

Prove current table, previous table, and typed table references do not collapse into one keyword path.

Prompt sequence:

```text
show customer risk
Top 7 Products by Revenue Last Year
Show together with Qty
Show me top 5 suppliers by AP
who is second in previous table?
who is second supplier in the above context?
who is second product in the previous product table?
show latest context authority trace
```

Expected visible answers:

1. `who is second in previous table?` returns product `Xiaomi Redmi Note 13 (8GB 256GB)` from the product table, not supplier rank 2.
2. `who is second supplier in the above context?` returns `Sunflower Accessories Co.` from the AP supplier table.
3. `who is second product in the previous product table?` returns `Xiaomi Redmi Note 13 (8GB 256GB)`.

Expected trace:

1. Relation should distinguish previous table versus current/typed table.
2. Requested object type must control whether product or supplier table is selected.
3. No AR customer table should answer these prompts.

## 10. Scenario F: Unsupported Prediction And Decision Boundaries

Goal:

Prove context authority does not overreach into prediction or policy decisions.

Prompt sequence:

```text
show customer risk
who is in third row in the above table
will the first customer default next month?
who should we collect from first?
what caused the first customer's risk to increase?
All above customers are from Yangon Region?
```

Expected visible answers:

1. Third row returns `35th Street Mobile Wholesale`.
2. Default prediction refuses without an approved prediction model or policy.
3. Collection priority refuses to prescribe action without approved decision policy, or clearly frames visible evidence only.
4. Cause/increase refuses if no trend, payment history, or transaction trail is visible.
5. Yangon region question refuses if the visible table does not include territory/region fields.

Expected trace / authority posture:

1. Row reference binds to the visible AR customer table.
2. Unsupported prediction, action, cause, and region questions do not invent missing evidence.
3. No hidden ERP field is assumed unless a governed detail view explicitly provides it.

## 11. Release Recording Template

Use this template after each browser run:

```text
Run date:
Backend commit:
Tester:

Scenario A P&L / COGS:
Status: pass / fail
Notes:

Scenario B AR comparison:
Status: pass / fail
Notes:

Scenario C AP supplier / invoice:
Status: pass / fail
Notes:

Scenario D product projection:
Status: pass / fail
Notes:

Scenario E mixed-family previous table:
Status: pass / fail
Notes:

Scenario F unsupported boundaries:
Status: pass / fail
Notes:

Release decision:
Green / hold / defer with documented limitation
```

## 12. Defect Classification

Classify failures before fixing:

1. `P0 context corruption`: stale family/table answers a current reference.
2. `P1 authority boundary breach`: unsupported prediction, policy, or hidden-field answer.
3. `P1 typed-object mismatch`: invoice/customer/supplier/product/document reference selects incompatible row type.
4. `P2 out-of-range boundary`: rank beyond visible rows is answered or wrong row count is used.
5. `P2 trace observability`: visible answer is correct but trace lacks selected/rejected frame evidence.
6. `P3 wording/readability`: behavior is correct but answer or trace is difficult to read.

P0 and P1 failures block release. P2 normally blocks context-authority release unless explicitly deferred. P3 can be deferred when the business answer is safe and the trace is auditable.
