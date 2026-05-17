# Qwen Chat Financial Summary Runtime Contract Plan

Status: design only  
Audience: AI/ML, backend, contract maintainers  
Goal: define the minimum runtime contract extension required before `financial_summary` can be migrated safely

## 1. Decision

Do not overload the existing [SemanticResolutionContract](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py#L291).

Reason:

1. the current contract fits narrow governed intents that resolve directly to family, capability, and report candidates
2. `financial_summary` first needs an intermediate decision between:
3. decomposition into a narrower semantic-governed intent
4. governed composite execution
5. clarification
6. rejection

That means the clean enterprise path is:

1. keep `SemanticResolutionContract` unchanged for narrow intents
2. add a separate `FinancialSummaryResolutionContract` later, if and only if the migration is approved

## 2. Why A Separate Contract Is Better

If we force `financial_summary` into the current semantic contract too early, we create ambiguity in the contract layer itself.

Problems that would appear:

1. `candidate_family_ids` would be misleading before decomposition versus composite is decided
2. `candidate_reports` would imply single-report routing even when the correct answer is a composite plan
3. `governed_decision=execute` would become ambiguous because it could mean:
4. execute a single-family report
5. or execute a composite plan

That would weaken the clarity we already built into the semantic runtime.

## 3. Proposed New Contract

Suggested name:

1. `FinancialSummaryResolutionContract`

Suggested responsibilities:

1. carry resolved summary-level slots
2. record the decomposition-versus-composite decision
3. record the chosen target intent or composite plan
4. carry ambiguity state before compiler routing begins

## 4. Proposed Minimal Fields

The contract should carry only what is necessary for the decision layer:

1. `request_id`
2. `session_id`
3. `intent_class`
4. `resolved_summary_domains`
5. `resolved_summary_focus`
6. `resolved_summary_metric_family`
7. `resolved_summary_grain`
8. `resolved_time_scope`
9. `decision`
10. `target_intent_class`
11. `target_composite_plan_id`
12. `ambiguity_flags`
13. `ambiguity_reason`
14. `decision_reason`

## 5. Compiler Handoff Rule

The future handoff should be:

1. if decision is `normalize_intent`
2. build a new narrower `FreshQueryInterpretationContract`
3. route through the existing semantic-governed compiler path

And:

1. if decision is `execute_composite`
2. build or reuse the governed composite-read planning input
3. do not force a fake single-report semantic contract

And:

1. if decision is `clarify`
2. emit a clarification reason
3. do not attempt compiler routing

## 6. Clarification Contract Rule

`financial_summary` does not need a brand-new clarification contract family.

The enterprise-grade path is:

1. keep using `ClarificationReasonContract`
2. keep using `ClarificationSignalContract`
3. keep using `ClarificationResolutionContract`
4. introduce only new governed `reason_type` values if needed later

This keeps clarification behavior consistent with the rest of the system and avoids contract sprawl.

The design-only clarification policy is captured in:

1. `impl_factory/03_config/qwen_enterprise_metadata/financial_summary_clarification_design.json`

## 7. No Runtime Change Yet

This plan is intentionally design-only.

It does not require:

1. changing `contracts.py` now
2. changing `compiler.py` now
3. changing `fresh_query_interpreter.py` now

The point is to prevent accidental contract pollution before the semantic extraction model is ready.

## 8. Recommended Future Order

When implementation time comes, the correct order is:

1. add the new contract to `contracts.py`
2. add pure unit tests for the new contract payload
3. implement design-only extractor tests for `summary_domains` and `summary_focus`
4. wire one conservative normalize-or-clarify slice first using the existing clarification contracts
5. only then wire the composite path

## 9. Enterprise Rule

For `financial_summary`, do not:

1. stretch the narrow semantic contract until it means two things
2. represent composite execution as a fake report execution
3. bypass the intermediate decision layer

Use a separate contract when the time comes.
