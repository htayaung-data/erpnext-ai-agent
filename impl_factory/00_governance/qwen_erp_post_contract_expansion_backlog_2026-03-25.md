# Qwen ERP Post-Contract Expansion Backlog (2026-03-25)

Status: active post-contract expansion backlog  
Scope: record bounded governed coverage expansion after the core contract architecture is stable  
Decision: complete Mini-phase 8 and post-contract hardening first; then expand business coverage in controlled waves instead of jumping directly to complex decomposition

## 1. Executive Rule

Current priority is:

1. finish the core mini-phase stack
2. complete post-contract hardening
3. then expand governed business coverage in bounded waves
4. only after Wave 1 coverage, move into complex request decomposition

This backlog exists to prevent product-expansion work from being mixed into contract stabilization.

## 2. Why Expansion Is Deferred

Expanding families too early would create avoidable risk:

1. architecture decisions would be hidden by new features
2. unknown-handling gaps would remain unsolved
3. future family growth would rest on unstable decision logic
4. regressions would be harder to diagnose

So the current branch should first become better at:

1. knowing what is covered
2. knowing what is unclear
3. knowing what is not yet covered
4. responding safely and consistently in each case

## 3. Expansion Strategy After Stability

After Mini-phase 8 and post-contract hardening, expansion should proceed in this order:

1. Wave 1 operational coverage expansion
2. then complex request decomposition
3. then multilingual, visual, OCR, and action-layer expansion later

Rationale:

1. complex decomposition becomes much more valuable when there are more governed targets to decompose into
2. operational read coverage is lower risk than OCR or CRUD
3. this sequence widens enterprise usefulness without destabilizing authority boundaries

## 4. Wave 1 Operational Coverage Expansion

Recommended first governed expansion wave:

1. Delivery / Fulfillment
2. Sales Order Status
3. Purchase Order Tracking
4. Customer Credit Status

Why this wave comes first:

1. these are high-frequency enterprise asks
2. they complete more of the commercial lifecycle:
   - pre-invoice tracking
   - fulfillment visibility
   - procurement visibility
   - customer credit risk
3. they are still primarily read-only and compatible with the current governed architecture
4. they improve later complex decomposition by giving the assistant more legitimate governed endpoints

Wave 1 rules:

1. do not reopen Mini-phase 6 or 7 to add them
2. implement as post-contract governed coverage work
3. add each domain with:
   - metadata/discovery support
   - governed artifact surface
   - clarification handling where needed
   - reasoning eligibility where appropriate
   - regression coverage
4. ship one domain at a time, not all four in one uncontrolled burst

## 5. Deferred Wave 2 Candidates

These are valid, but should come after Wave 1:

1. Inventory Movement / Stock Ledger
2. Production Orders

Why later:

1. they are operationally denser and easier to answer noisily
2. they usually need tighter bounded semantics
3. production/manufacturing only makes sense if it is truly active in the business

## 6. Later Platform Expansion

These are enterprise-worthy, but should come after the core read architecture and Wave 1 coverage are stable:

1. long prompt / complex request decomposition
2. Burmese language understanding
3. governed charts / graphs / dashboard views
4. CSV / Excel export
5. OCR understanding
6. CRUD / write actions with approvals

Recommended relative order:

1. complex request decomposition
2. Burmese understanding
3. chart / graph / dashboard + export
4. OCR ingestion
5. CRUD last

## 7. Deferred Expansion Candidates

These are valid candidates for later governed expansion once contracts are stable.

### 3.1 Finance-adjacent analysis

Potential asks observed or expected:

1. cash flow insight
2. liquidity pressure
3. working capital outlook
4. collections strategy
5. supplier payment pressure
6. short-term financial health outlook

Current rule:

1. do not expand these yet inside the contract-migration stream
2. first improve Contract 2 handling so the system can distinguish:
   - covered finance
   - finance-adjacent but unclear
   - valid ERP domain but not yet covered
   - unsupported request

### 3.2 Advisory follow-ups over governed finance artifacts

Potential asks:

1. what should we do next
2. give me business recommendations
3. how should we collect AR
4. how should we negotiate AP

Current rule:

1. preserve governed grounding first
2. do not add ad hoc recommendation logic during contract migration
3. revisit only after clarification and scope-decision contracts are stable

### 3.3 Conversational front-door capability/help layer

Potential asks:

1. greetings
2. thanks
3. what can you do
4. how can you help me
5. what reports can you analyze
6. okay / continue / go on

Current rule:

1. this should be implemented after Contract 2
2. do not mix it into current contract stabilization

## 8. Revisit Trigger

Revisit this backlog only when these are true:

1. Mini-phase 8 is complete
2. post-contract hardening is complete enough for safe family expansion
3. the browser regression pack is stable on current covered families
4. rollout / observability is good enough to detect regressions from new governed domains

## 9. What To Do Next Instead Of Expanding

The next implementation priority remains:

1. finish Mini-phase 8
2. complete post-contract hardening
3. then start Wave 1 operational coverage expansion before complex decomposition
