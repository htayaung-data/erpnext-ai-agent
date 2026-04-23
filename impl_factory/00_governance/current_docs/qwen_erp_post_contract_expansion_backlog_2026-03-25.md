# Qwen ERP Post-Contract Expansion Backlog (2026-03-25)

Status: active post-contract expansion backlog  
Scope: record bounded governed coverage expansion after the core contract architecture is stable  
Decision: complete Mini-phase 8 and post-contract hardening first; then expand business coverage in controlled waves instead of jumping directly to complex decomposition

Primary hardening artifact:

1. `qwen_erp_post_contract_hardening_plan_2026-03-26.md`

Current hardening status note:

1. H1 regression / CI hardening is materially complete
2. H2 observability hardening is materially strong and live-validated
3. H3 state / concurrency hardening is materially strong for the currently intended contract surface
4. H4 adversarial hardening is closure-ready for the currently intended contract surface
5. H5 rollout and release gates are closure-ready for the automated surface; only optional manual live signoff remains

## 1. Executive Rule

Current priority is:

1. finish the core mini-phase stack
2. complete post-contract hardening
3. then expand governed business coverage in bounded waves
4. after Wave 1 coverage, add bounded composite governed artifacts
5. then add governed business definitions and formulas
6. only then move into complex request decomposition

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
2. Wave 1.5 composite governed artifact expansion
3. Wave 1.75 business definition and formula registry
4. then complex request decomposition
5. then multilingual, visual, OCR, and action-layer expansion later

Rationale:

1. complex decomposition becomes much more valuable when there are more governed targets to decompose into
2. operational read coverage is lower risk than OCR or CRUD
3. composite governed artifacts expand the safe read surface before decomposition starts combining many asks
4. business definitions and formulas prevent semantic drift on company-specific metrics before decomposition becomes more ambitious
5. this sequence widens enterprise usefulness without destabilizing authority boundaries

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

## 6. Wave 1.5 Composite Governed Artifact Expansion

Recommended next governed artifact expansion after Wave 1:

1. `CompositeRankingArtifactContract`
2. safe multi-metric customer rankings
3. safe multi-metric product rankings

Why this wave fits here:

1. it expands the governed read surface without introducing write risk
2. it unlocks common enterprise asks such as:
   - customers in Yangon with revenue, AOV, and tenure
   - top customers by revenue with quantity and overdue balance
   - top products by revenue with quantity and average selling price
3. complex request decomposition becomes much more useful once these richer governed artifacts already exist

Wave 1.5 rules:

1. primary ranking metric must be explicit
2. supplemental metrics must share a governed scope signature:
   - company
   - date range
   - entity grain
   - filter basis
   - aggregation semantics
3. if join compatibility is not proven, composition must be blocked safely
4. start with same-grain, low-ambiguity composites first

Recommended first candidates:

1. customer revenue + quantity + average order value
2. product revenue + quantity + average selling price
3. overdue customers + overdue amount + last payment date

Defer until later:

1. tenure-heavy composites unless tenure definition is governed clearly
2. gross-margin composites unless cost basis is governed consistently
3. operational metrics with ambiguous grain or disputed business definition

## 6.5 Wave 1.75 Business Definition And Formula Registry

Recommended governed semantic layer after Wave 1.5:

1. `BusinessDefinitionRegistry`
2. `GovernedFormulaRegistry`
3. company-specific KPI, ratio, and threshold definitions

Why this wave fits here:

1. composite artifacts and later decomposition both depend on stable business meanings
2. enterprise teams often have company-specific definitions that the AI should not invent
3. this reduces drift on derived metrics before they are used widely in reasoning and multi-metric artifacts

Representative examples:

1. tenure:
   - first invoice date
   - first sales order date
   - customer creation date
2. average order value
3. collection ratio
4. credit utilization
5. overdue risk thresholds
6. inventory turnover

Wave 1.75 rules:

1. do not store formulas only in prompts
2. do not let AI invent company KPI definitions at runtime
3. definitions must include:
   - name
   - business meaning
   - scope / grain
   - formula or derivation rule
   - threshold logic if applicable
   - effective owner / source of truth
4. ambiguous business terms such as tenure must be blocked or clarified until governed

Recommended first candidates:

1. tenure
2. average order value
3. collection ratio
4. credit utilization
5. overdue severity thresholds

## 7. Later Platform Expansion

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

## 8. Deferred Expansion Candidates

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

### 3.4 Customer ranking clarification and report-routing ambiguity

Observed case:

1. `Top 5 customers by revenue last month`
2. current browser/runtime behavior may clarify with:
   - `Which report would you like me to use?`

Why this is deferred:

1. this is not a `Delivery / Fulfillment` blocker
2. this belongs to governed ranking expansion rather than transaction-listing hardening
3. safe customer-ranking behavior depends on clearer governed metric/report resolution for ranking asks
4. the right long-term fix should come from ranking architecture and metadata, not from one-off prompt or keyword patches

Current rule:

1. keep this case deferred while `1.1 Delivery / Fulfillment` is being stabilized
2. do not fix it with ad hoc routing, keyword matching, or single-case report forcing
3. revisit it under the later governed ranking chapter:
   - Phase 3 `Composite Governed Artifact Expansion`
4. when revisited, solve it through:
   - governed ranking report selection
   - explicit metric semantics for `revenue`
   - stable clarification policy only if true ambiguity remains after governed ranking resolution

## 9. Revisit Trigger

Revisit this backlog only when these are true:

1. Mini-phase 8 is complete
2. post-contract hardening is complete enough for safe family expansion
3. the browser regression pack is stable on current covered families
4. rollout / observability is good enough to detect regressions from new governed domains

## 10. What To Do Next Instead Of Expanding

The next implementation priority remains:

1. complete post-contract hardening
2. then start Wave 1 operational coverage expansion
3. then add Wave 1.5 composite governed artifact expansion
4. then add Wave 1.75 business definition and formula registry
5. then move into complex decomposition
