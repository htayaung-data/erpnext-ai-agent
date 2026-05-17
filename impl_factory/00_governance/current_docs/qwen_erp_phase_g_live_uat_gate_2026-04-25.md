# Qwen ERP Phase G Live UAT Gate

Status: draft release gate
Date: 2026-04-25
Scope: live/manual verification for the currently activated governed scope packages

## 1. Purpose

This gate verifies that the code-level Phase G closure is visible in real user behavior.

The registry and contract tests already prove the governance structure. This UAT gate checks the final surface:

1. business-natural prompts route to the approved governed scope
2. follow-up questions use the current context when safe
3. scope switching breaks out cleanly
4. ambiguity is clarified naturally
5. unsupported requests fail closed without pretending

## 2. Non-Negotiable Rules

1. Do not accept a pass if the assistant answers through a keyword-only or single-case rescue path.
2. Do not accept a pass if a pending clarification blocks an unrelated new business question.
3. Do not accept a pass if a compatible follow-up loses the previously resolved entity or document context.
4. Do not accept a pass if an unsupported scope is answered by guessing.
5. Do not accept a pass if the answer uses stale local/sample data instead of live governed ERP data.

## 3. Master Data UAT

### 3.1 Customer Similar-Name Discovery

Prompt:

```tex
do u have customer name similar to "Nay Lin Mobile"?
```

Expected:

1. returns a customer match or candidate list from governed customer scope
2. does not ask for unrelated scope clarification
3. does not remain blocked by any previous item/supplier ambiguity

Follow-up:

```tex
tell me more about that customer
```

Expected:

1. opens the resolved customer detail
2. includes governed profile and credit/status data where available

### 3.2 Supplier Similar-Name Discovery

Prompt:

```tex
do u have supplier name similar to "Myanmar Tech Import"?
```

Expected:

1. returns `Myanmar Tech Import Services` or a candidate list if confidence is not high
2. uses supplier master scope, not customer or item scope

Follow-up:

```tex
tell me more about that supplier
```

Expected:

1. opens supplier profile/detail
2. includes recent governed purchase invoice summary where available

### 3.3 Item Similar-Name Discovery

Prompt:

```tex
do u have product name similar to "Type-C Fast Charge"?
```

Expected:

1. if multiple confident candidates exist, shows the candidate list directly
2. does not return unrelated default fixed-asset items
3. does not force clarification before showing the found lis

Follow-up:

```tex
tell me more about Type-C Cable 2m Fast Charge
```

Expected:

1. opens the selected item/product detail
2. includes item profile, recent sales, and stock summary where governed data is available

Stock follow-up:

```tex
how many stocks do we have for that product, and in which warehouse?
```

Expected:

1. uses the current item contex
2. returns warehouse-level quantity where governed inventory fields are available
3. otherwise fails closed with a natural business explanation and does not produce an internal error

## 4. Transaction Listing UAT

Run each base prompt in a fresh context and after an unrelated prior context.

Prompts:

```tex
show me sales invoices
show me sales orders
show me delivery notes
show me purchase orders
show me purchase invoices
show me purchase receipts
show me payment entries
```

Expected:

1. each prompt routes through the approved transaction-listing scope
2. document count and title match the actual returned row coun
3. amount label matches the governed primary metric for that scope
4. unsupported or unavailable fields do not cause internal errors

Follow-up examples:

```tex
show me today
show me this month
show me by outstanding amoun
show me only overdue
```

Expected:

1. compatible refinements preserve the same listing scope
2. bare base re-ask resets inappropriate prior filters
3. impossible refinements clarify or fail closed naturally

## 5. Financial Statement UAT

Prompt:

```tex
show me financial statemen
```

Expected:

1. asks which statement: Profit and Loss, Balance Sheet, or Cash Flow
2. accepts natural variants such as `P & L`, `P&L`, `PL statement`, `Balance sheet`, and `Cash flow`
3. does not keep asking after a valid statement choice

Default period expectation:

1. uses the configured fiscal period from the last closed fiscal boundary to today, unless the user explicitly asks for another period
2. does not silently revert to a short current-month period in a new cha

## 6. Context Control UAT

### 6.1 Show Found Lis

Prompt sequence:

```tex
do u have product name similar to "Type-C Fast Charge"?
show me the lis
```

Expected:

1. second prompt shows the previously found candidate lis
2. does not ask for unrelated master-data area

### 6.2 New Question Breakou

Prompt sequence:

```tex
do u have product name similar to "Type-C Fast Charge"?
do u have customer name similar to "Nay Lin Mobile"?
```

Expected:

1. second prompt is treated as a new customer lookup
2. unresolved item ambiguity does not block the new customer question

### 6.3 Explicit Ignore / Forge

Prompt sequence:

```tex
do u have product name similar to "Type-C Fast Charge"?
forget the first question, answer the last question
ignore that, show me suppliers
go back to the customer
```

Expected:

1. explicit ignore/forget cancels or bypasses the pending ambiguity
2. new requested scope is answered directly when governed
3. "go back" restores a previously resolved compatible focus when safe
4. if the requested prior focus is not safe to restore, the assistant clarifies naturally

## 7. Lifecycle And Event UAT

Customer lifecycle prompt:

```tex
tell me more about Ko Nay Lin Mobile Center
how long have we worked with that customer?
```

Expected:

1. asks for lifecycle basis only if required
2. supported bases remain customer-created date, first sales order date, and first sales invoice date

Document event prompt:

```tex
tell me more about PUR-ORD-2026-00010
what is the delivery or receipt status?
```

Expected:

1. answers only from supported document event/date/status fields
2. does not activate broad event search

## 8. Pass Criteria

This gate passes only when:

1. no internal error appears
2. no unrelated clarification blocks a new business query
3. no unsupported scope is answered by guessing
4. candidate lists are shown naturally when multiple matches are found
5. follow-ups preserve context only when the shared affordance contract allows i
6. live data matches the ERP state at test time

## 9. Current Status

Code-level Phase G registry/contract readiness is complete.

Live browser/UAT has started.

Manual checks passed for:

1. item similar-name discovery with multiple candidates
2. item detail with governed sales and stock summary
3. customer similar-name discovery after unresolved item ambiguity
4. customer detail continuation
5. financial statement clarification and statement execution
6. purchase invoice, purchase receipt, payment entry, and sales invoice listings

One blocker was found:

1. stock-by-warehouse follow-up after item detail produced an internal error

Fix status:

1. fixed in the shared deterministic direct-evidence response seam
2. backend-container targeted item stock direct-evidence regression passed
3. backend-container full entity-detail contract suite passed with 85 tests
4. backend-container nearby post-contract direct-evidence follow-up guard passed
5. browser retest still exposed a second upstream crash before evidence rendering
6. root cause was a stale helper call in the shared follow-up boundary builder after entity-domain extraction
7. follow-up boundary builder now uses the extracted `entity_detail_context_domains(...)` helper consistently
8. backend-container browser-equivalent reproduction now passes for product detail followed by stock-by-warehouse question
9. backend-container full follow-up interpreter contract suite passed with 10 tests
10. backend workers were reloaded after the follow-up boundary fix
11. stock-by-warehouse direct answer formatting was improved to include a `Stock by Warehouse:` section with bullet rows instead of flattening warehouse quantities into one paragraph
12. backend-container item-stock boundary formatter suite passed with 4 tests

Current gate state:

1. backend reload completed
2. manual browser retest passed for the stock-by-warehouse follow-up prompt: no internal error, current item context was preserved, and warehouse-level quantities were returned
3. manual browser retest passed for context switching from unresolved product ambiguity to customer similar-name lookup
4. manual browser retest passed for financial statement clarification continuation using `P&L`
5. item detail narrative markdown cleanup is implemented in the shared entity-detail final-answer seam:
   - unbalanced emphasis markers are repaired generically before the answer is returned
   - this is not product-specific and does not change governed facts
6. financial statement default period was rechecked against live ERP fiscal closing state:
   - the contract now preserves the `open_fiscal_year_to_date` default for financial statements when the user does not explicitly ask for another period
   - live ERP contains submitted closing voucher `ACC-PCV-2026-00004` for `2025-04-01` to `2026-03-31`, so the current open period resolves to `2026-04-01` through the current test date
   - therefore April-only financial statement output is consistent with the live ERP closing data at this time
7. verification completed:
   - backend-container focused entity-detail markdown regression passed
   - backend-container entity-detail contract suite passed with 86 tests
   - backend-container focused financial default-period and compiler guardrails passed
   - backend-container compile passed for touched modules and tests
8. remaining G4 action before final signoff:
   - reload/restart backend workers
   - rerun a short browser retest for item detail narrative and financial statement period behavior
