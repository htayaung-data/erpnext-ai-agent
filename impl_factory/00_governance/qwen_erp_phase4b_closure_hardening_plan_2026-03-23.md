# Qwen ERP Phase 4B Closure Hardening Plan (2026-03-23)

Status: planned  
Scope: close the remaining Phase 4B gaps between enterprise-grade governed execution and business-user-ready assistant behavior  
Goal: preserve the governed family architecture while fixing follow-up fidelity, missing read coverage, natural clarification, and business-insight rendering.

## 1. Why This Closure Plan Exists

Phase 4B is now strong in architecture and governed breadth for the current family scope.

The system now has:

1. governed family routing
2. normalized family artifacts
3. composite read planning
4. deterministic validation
5. enterprise-stable latency and pass posture for the current governed family scope

However, recent browser testing shows the product is not yet ready to be judged as a strong business assistant from the user perspective.

The current remaining gap is not mainly:

1. fresh-query compilation
2. family normalization
3. base report-family governance

The current remaining gap is:

1. follow-up refinement fidelity
2. strict preservation of requested ranking/metric/column/time constraints
3. missing governed transaction-list coverage
4. broader business-health composite coverage
5. human clarification generation
6. response policy by intent
7. consultant-style business insight and recommendation rendering

This closure plan exists to solve those remaining gaps without reopening the core architecture.

## 2. Current Diagnosis

### 2.1 What is already working

The following are now materially stronger than before:

1. first-turn governed family execution for:
   - payable / receivable
   - financial statements
   - ranking analytics
   - trend analytics
   - inventory snapshot
   - product profitability
2. normalized family rendering
3. governed composite AR/AP working-capital health
4. family-level semantic validation

### 2.2 What still feels weak to the user

Recent browser validation shows the remaining weaknesses are concentrated in these areas:

1. short corrective follow-ups such as:
   - `I mean top 5`
   - `show me with their amount`
   - `the last sale invoices, not supplier`
2. strict fidelity to requested business shape such as:
   - top N limit
   - requested metric
   - requested columns
   - requested time scope
3. unsupported but common ERP reads such as:
   - recent sales invoices
   - recent purchase invoices
   - recent payments / stock transactions
4. broad business-health requests such as:
   - `analyze the company health and suggest the area to improve`
5. robotic clarification wording that leaks compiler internals
6. robotic answer style that returns correct data but weak business interpretation

### 2.3 Core product judgment

The current system is no longer mainly failing at enterprise governance.

It is now failing mainly at:

1. business-user communication quality
2. follow-up continuity quality
3. common operational read coverage

So the correct next move is not to weaken governance.

The correct next move is to add a stronger business-user experience layer on top of the governed family/composite foundation.

## 3. Governing Rule For Closure Hardening

This closure work must preserve the existing enterprise rule:

- `Qwen-Agent proposes`
- `compiler enforces`
- `validator confirms`

Additional closure rule:

- `assistant communicates like an ERP consultant, not like a compiler trace`

Important consequences:

1. no rollback to free-form raw-agent report discovery
2. no direct exposure of internal ambiguity or compiler objects to end users
3. no response-style improvement that bypasses governed family artifacts
4. no follow-up convenience behavior that silently weakens metric/time/filter fidelity

## 4. Closure Workstreams

### 4.1 Workstream A: Follow-Up Contract Hardening

Purpose:

- make same-session corrections and refinements behave like a competent analyst rather than a brittle workflow engine

Main deliverables:

1. stronger distinction between:
   - new business query
   - follow-up refinement
   - presentation-only transform
   - metric/dimension switch
   - time-scope restatement
2. explicit follow-up request contract fields for:
   - target family
   - target metric
   - target dimension
   - target top_n
   - target requested columns
   - carry-forward vs override time scope
3. confidence-driven rule:
   - if follow-up interpretation confidence is low, ask a human clarification instead of drifting into the wrong family

Success criteria:

1. `I mean top 5` keeps the same ranking family and only changes limit
2. `show me with their amount` keeps the same family and changes only the requested metric/columns
3. contradictory follow-ups clarify instead of silently switching reports

### 4.2 Workstream B: Ranking / Metric / Column Fidelity

Purpose:

- ensure governed ranking and tabular answers respect the exact business request shape

Main deliverables:

1. strict propagation of:
   - `top_n`
   - metric id
   - dimension id
   - requested output columns
   - contribution / ratio / amount flags
2. renderer support for:
   - exact top 5
   - exact top 10
   - item name + revenue + contribution percent
   - revenue vs gross profit vs buying amount separation
3. family validation rules that reject mismatched metric/column outputs

Success criteria:

1. `Top 5 customers by revenue` renders only 5 rows
2. `top 10 products last month by revenue with item name, revenue, and contribution percent` returns the requested metric set, not profitability drift
3. ranking corrections stay inside the governed ranking family unless the user explicitly changes family

### 4.3 Workstream C: Transaction-List Family

Purpose:

- cover common operational ERP reads that are not statement/trend/ranking questions

Main deliverables:

1. new governed family for recent transactional lists, for example:
   - sales invoices
   - purchase invoices
   - payment entries
   - stock ledger movements
2. normalized transaction-list artifact contract
3. list-specific rendering policy for:
   - last N documents
   - selected fields
   - optional summary line

Success criteria:

1. `show me the last 7 sale invoices` routes to a governed document-list family instead of drifting into supplier or aging context
2. corrections like `not supplier` reset properly into the correct list family

### 4.4 Workstream D: Broader Company-Health Composite

Purpose:

- expand beyond the current narrow AR/AP working-capital composite into a more natural business-health analysis path

Main deliverables:

1. broader composite profile for:
   - liquidity pressure
   - receivable/payable posture
   - profitability posture
   - cash-flow pressure
   - inventory drag where supported
2. compiler-approved composite plan templates for:
   - `company_health_summary`
   - `finance_health_summary`
   - `working_capital_plus_profitability`
3. governed recommendation slots derived from normalized composite findings

Success criteria:

1. `analyze the company health and suggest the area to improve` resolves into a governed composite path when enough data families exist
2. clarification only happens when the composite truly needs missing scope, not when the system already has a safe default health profile

### 4.5 Workstream E: Human Clarification Layer

Purpose:

- replace technical clarification messages with business-user-friendly prompts

Main deliverables:

1. clarification rendering contract with:
   - user-friendly question
   - suggested business options
   - hidden internal reasoning retained only in audit
2. clarification templates by ambiguity type:
   - family ambiguity
   - time-scope ambiguity
   - metric ambiguity
   - entity ambiguity
3. explicit rule that internal compiler labels are not shown directly to the user
4. clarification translation policy that converts internal ambiguity into business-language choices such as:
   - `Which area would you like me to analyze: AR/AP, cash flow, profitability, or inventory?`
   - `Would you like to see this for last month, this quarter, or all time?`

Success criteria:

1. the user never sees messages such as:
   - `Ambiguous capability candidates: ...`
2. the user instead sees questions such as:
   - `Which area would you like me to analyze: AR/AP, cash flow, profitability, or inventory?`
3. clarification wording never exposes:
   - capability ids
   - contract names
   - validator labels
   - compiler-internal ambiguity reasons
4. clarification remains conversational even when the compiler is the underlying decision-maker

### 4.6 Workstream F: Business-Insight Response Renderer

Purpose:

- restore the helpful consultant-like feel without weakening governed correctness

Main deliverables:

1. answer-style policy by request type:
   - direct factual answer
   - analysis answer
   - statement answer
   - ranking / trend answer
   - operational list answer
   - follow-up refinement answer
2. renderer slots for:
   - direct answer
   - key highlight
   - risk / anomaly
   - recommendation / next action when requested or appropriate
3. artifact-grounded explanation step that uses normalized family/composite artifacts as the only factual source
4. explicit response policy by intent:
   - simple factual question:
     - short direct answer
     - optional highlight
   - analysis question:
     - direct answer
     - key insight
     - recommendation / suggested action when grounded
   - statement question:
     - summary
     - notable line items
     - implication
   - follow-up refinement:
     - preserve prior family/artifact context
     - behave conversationally
     - avoid re-dumping the full result unless needed
5. natural-narrative generation from governed artifacts, so deterministic family blocks support the answer instead of replacing the answer voice

Success criteria:

1. simple questions answer directly first, without dumping a full table unless needed
2. analysis questions include useful insight and recommendations
3. statement questions explain what matters, not only what the statement contains
4. follow-up refinements sound like a continuing conversation, not a fresh compiler run
5. answers feel more like an ERP consultant and less like a fixed-format robot

### 4.7 Workstream G: Closure Evaluation and Browser Acceptance

Purpose:

- prove that the system is strong both internally and from the real browser user perspective

Main deliverables:

1. evaluation set expansion for:
   - follow-up corrections
   - ranking fidelity
   - transaction-list reads
   - company-health composites
   - clarification UX
2. browser acceptance checklist across:
   - correctness
   - naturalness
   - useful insight
   - follow-up continuity
   - latency perception
3. explicit closure review before Phase 4B is considered fully wrapped

Success criteria:

1. automated suites stay green
2. browser same-session business tests stay green
3. user experience improves materially from the current `5/10` perception

## 5. Recommended Implementation Order

The safest next order is:

1. Workstream A: follow-up contract hardening
2. Workstream B: ranking / metric / column fidelity
3. Workstream C: transaction-list family
4. Workstream D: broader company-health composite
5. Workstream E: human clarification layer
6. Workstream F: business-insight response renderer and response policy by intent
7. Workstream G: closure evaluation and browser acceptance

Reason for this order:

1. correctness and scope fidelity must be fixed before polishing language
2. common operational coverage must exist before we optimize conversational style
3. clarification and insight rendering should be built on top of already-correct family/composite behavior

## 6. Exit Criteria

Phase 4B should only be treated as fully wrapped from the business-user perspective when:

1. same-session follow-up corrections preserve family, metric, and time intent correctly
2. ranking and tabular outputs obey exact requested limits and columns
3. transaction-list questions are supported by a governed family or clearly clarified
4. broad company-health analysis has a safe governed composite path
5. clarification messages are human-friendly and never leak compiler internals
6. simple factual questions answer briefly with optional highlight
7. analysis questions provide grounded insight and recommendations
8. statement questions summarize notable lines and business implications
9. follow-up refinements preserve previous context conversationally
10. answers provide direct business meaning, not only rigid report output
11. browser validation confirms the assistant feels materially more natural and useful while keeping governed correctness

## 7. Immediate Next Step

The immediate next step after this closure plan is:

1. implement Workstream A: follow-up contract hardening
2. treat Workstream B as the first coupled follow-up deliverable
3. keep every fix family-driven and contract-driven, not query-by-query

This keeps the current enterprise foundation intact while making the assistant meaningfully better for real business use.
