# Qwen ERP Post-Contract Expansion Backlog (2026-03-25)

Status: deferred product-expansion backlog  
Scope: record business areas that may deserve governed coverage expansion after the contract architecture is stable  
Decision: prioritize unknown-handling and decision quality first; defer family expansion until contract migration is stable

## 1. Executive Rule

Current priority is:

1. finish contract migration
2. improve unknown-handling and scope decision quality
3. only then expand governed business coverage

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

## 3. Deferred Expansion Candidates

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

## 4. Revisit Trigger

Revisit this backlog only when these are true:

1. `ArtifactContinuationContract` is authoritative enough for continuation behavior
2. `GovernedScopeDecisionContract` is authoritative enough for local vs requery vs clarify vs out-of-scope decisions
3. `ClarificationReasonContract` exists and drives clarification behavior cleanly
4. the browser regression pack is stable on current covered families

## 5. What To Do Next Instead Of Expanding

The next implementation priority remains:

1. improve unknown-handling in Contract 2
2. distinguish:
   - `covered_family`
   - `clarification_needed`
   - `out_of_scope_but_valid_erp_domain`
   - `unsupported_request`
3. keep product-expansion ideas documented here until the architecture is ready
