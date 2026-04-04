# Qwen Chat Next Wave Plan

Status: completed historical wave  
Date: 2026-04-04  
Audience: AI/ML, backend, ERP governance maintainers  
Goal: record the enterprise-grade follow-up boundary wave that followed the bounded `financial_summary` wave-two rollout

Wave checkpoint:

1. [QWEN_CHAT_FOLLOWUP_BOUNDARY_WAVE_CHECKPOINT.md](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/QWEN_CHAT_FOLLOWUP_BOUNDARY_WAVE_CHECKPOINT.md)

## 1. Fresh Independent Conclusion

The previously designed next wave was correct for its time:

1. `financial_summary` needed a design-first wave two
2. that wave required a governed composite-intent signal
3. runtime expansion had to stay narrow and structured

That wave is now no longer theoretical.

The repo already has the approved bounded result:

1. `financial_summary` first-wave normalize/clarify behavior
2. one approved second-wave composite path only:
   `receivable` + `payable` + `cross_domain_health` -> `working_capital_health`
3. preserved governed provenance across semantic resolution, compiler, composite planning, and execution audit

So the earlier plan was not wrong.
It has been substantially executed and is now under an explicit stop rule.

## 2. Why The Next Wave Must Change

A fresh repository-level evaluation shows that the main architectural risk is no longer:

1. `service.py` size
2. `financial_summary` under-modeling
3. verification immaturity

Those concerns have already been reduced materially.

The clearest remaining enterprise risk is different:

1. residual lexical authority still exists in the follow-up boundary seam
2. that authority is much smaller than before, but it still lives in runtime follow-up isolation logic
3. continued micro-cleanup inside `followup_interpreter.py` alone is now approaching diminishing returns

That means the next correct move is not another local cleanup streak.
It is a contract-first redesign of the follow-up boundary itself.

## 3. New Next Wave

The next enterprise-grade wave is:

1. `Governed Follow-Up Boundary Contract`

This wave supersedes further ad hoc lexical-removal micro-slices as the default focus.

## 4. Relationship To The Previous Plan

The previous wave plan should now be treated this way:

1. `financial_summary` wave two remains approved and active
2. its stop boundary remains in force
3. no additional `financial_summary` widening should happen by default
4. the new follow-up-boundary wave should be executed without widening product scope in the same slice

This keeps the already-approved `financial_summary` work stable while we fix the next real architectural seam.

## 5. Problem Statement

Today, the system still relies on a mixed boundary path for grounded follow-up handling:

1. structured semantic follow-up already exists
2. governed report and family metadata already exist
3. but the final grounded-vs-fresh decision still retains residual lexical/domain fallback logic

That is not the final enterprise-grade endpoint.

The enterprise endpoint is:

1. producers generate a structured boundary contract
2. boundary consumers evaluate that contract
3. runtime does not rediscover business meaning from raw follow-up text

## 6. Wave Goal

Replace residual lexical follow-up boundary authority with one governed structured contract that becomes the runtime decision surface for:

1. grounded follow-up continuation
2. grounded follow-up breakout into fresh governed query
3. contradiction handling
4. context-affinity checks
5. fail-closed behavior when structured evidence is insufficient

## 7. Proposed New Contract

Suggested name:

1. `FollowUpBoundaryContract`

Suggested responsibilities:

1. carry structured requested business domains
2. carry grounded artifact business domains
3. carry structured follow-up action class
4. record whether the request is grounded-compatible, contradictory, or breakout-worthy
5. record whether breakout is supported by governed evidence versus lexical fallback
6. make the final fresh-vs-grounded boundary inspectable and auditable

### 7.1 Proposed Minimal Fields

1. `request_id`
2. `session_id`
3. `source_family_id`
4. `source_report_name`
5. `grounded_context_domains`
6. `requested_domains`
7. `structured_followup_modes`
8. `structured_business_signals_present`
9. `grounded_followup_supported`
10. `self_contained_signal`
11. `contradictory_payload`
12. `domain_affinity`
13. `recommended_boundary_decision`
14. `decision_reason`
15. `resolution_source`

### 7.2 Allowed Decision Values

1. `stay_grounded`
2. `force_fresh_query`
3. `fail_closed_to_reasoning`

No decision value should imply direct report routing.
That remains downstream.

## 8. Producer Rule

This contract must be produced from structured sources first:

1. accepted semantic follow-up payload
2. grounded artifact metadata
3. report-family and capability metadata
4. governed contradiction rules

Only bounded metadata-backed normalization may remain around the edges.

It must not be produced from:

1. free-form phrase bags
2. direct report-name substring routing
3. direct metric/dimension extraction from raw follow-up text
4. lexical rescue logic after structured interpretation is available

## 9. Consumer Rule

`followup_interpreter.py` should become a consumer of this contract, not the place where business meaning is inferred.

That means:

1. evaluate the contract
2. decide breakout vs grounded continuation
3. fail closed when contract evidence is insufficient
4. stop rediscovering business domains from raw message text

## 10. Scope Of This Wave

In scope:

1. design the contract
2. add the contract to `contracts.py`
3. add unit coverage for contract shape
4. produce the contract from existing structured semantic and grounded metadata
5. refactor `followup_interpreter.py` to consume the contract
6. expand guardrails so the retired lexical seam cannot quietly return

Out of scope:

1. new `financial_summary` composite profiles
2. sales-summary widening
3. `service.py` cosmetic refactoring
4. smoke-fixture migration work unless a red appears
5. changes to `sales_console.js`

## 11. Delivery Order

### 11.1 Design

1. finalize contract schema
2. define producer inputs
3. define decision rules
4. define fail-closed rules

### 11.2 Contract Introduction

1. add `FollowUpBoundaryContract` to `contracts.py`
2. add serialization and validation tests

### 11.3 Producer Wiring

1. add a governed builder that reads:
   - accepted semantic follow-up payload
   - grounded artifact metadata
   - report/capability semantic metadata
2. ensure no direct lexical routing authority is introduced during the build step

### 11.4 Consumer Simplification

1. reduce `followup_interpreter.py` to contract evaluation
2. remove remaining boundary-domain lexical fallback from that file
3. preserve current verified H3 and Phase 6 behavior under structured evidence only

### 11.5 Guardrails

1. encode the new forbidden seams in `scripts/check_qwen_enterprise_guardrails.py`
2. guard against raw-message domain breakout logic reappearing in the follow-up boundary lane

### 11.6 Verification

Use:

```bash
scripts/qwen_verify_enterprise_matrix.sh semantic
```

while designing and wiring the contract.

Before the wave is accepted:

```bash
scripts/qwen_verify_enterprise_matrix.sh full
```

## 12. Enterprise Stop Rules

Stop and checkpoint when all are true:

1. `followup_interpreter.py` is no longer the authority for raw follow-up domain inference
2. fresh-vs-grounded breakout is driven by the new structured boundary contract
3. H3 and Phase 6 live behaviors remain green
4. semantic gate is green
5. full enterprise gate is green

Do not continue shaving residual utility code after that point just for purity.

Residual degraded fallback may remain only when all are true:

1. it is explicitly documented
2. it is test-protected as an approved bounded exception
3. it no longer acts as a broad lexical rescue path

## 13. Senior Decision

The previous `financial_summary` wave-two plan remains valid and completed to its approved boundary.

The next best enterprise-grade wave is therefore not:

1. more `financial_summary` widening
2. more `service.py` trimming
3. more endless micro-cleanup in `followup_interpreter.py`

It is:

1. a contract-first follow-up boundary redesign

That is the cleanest path from the current repo state to the next serious enterprise architecture gain.

## 14. Completion Status

This wave is now complete to its stop rule.

The contract-first redesign was implemented, narrowed, audited, and revalidated with the full enterprise gate. This document should now be treated as a completed wave record, not the active next-step plan.

## 15. What Comes After This

The next chapter should be selected fresh from current product/runtime value, not by continuing local cleanup in the follow-up boundary seam.

Recommended order:

1. identify the highest-value governed capability gap or runtime pain point
2. design that chapter first
3. implement it under the same `full` enterprise gate
## 16. Out-Of-Scope Reminder

This plan does not change the standing rule:

1. [sales_console.js](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/sales_console/sales_console.js) remains outside this task and must not be touched
