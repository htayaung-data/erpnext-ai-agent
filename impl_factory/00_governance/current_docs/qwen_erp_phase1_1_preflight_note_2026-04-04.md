# Qwen ERP Phase 1.1 Preflight Note

Status: active preflight decision  
Date: 2026-04-04  
Scope: go/no-go decision for Phase 1.1 `Delivery / Fulfillment`

## 1. Purpose

This note records the short preflight review required before starting:

1. Phase 1
2. Mini-phase 1.1
3. Delivery / Fulfillment

The goal is to answer only the debts that could realistically block the next chapter.

## 2. Questions Reviewed

The preflight reviewed these two active blocker candidates from the debt register:

1. external Qwen runtime governance
2. service-user / Administrator boundary

## 3. Preflight Finding: External Qwen Runtime Governance

### 3.1 What The Repo Shows

1. the governed runtime path clearly depends on [runtime_client.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/runtime_client.py)
2. that client uses explicit config for:
   - base URL
   - auth token / auth header
   - timeout
   - fresh-query timeout override
3. the external service under [experimental/qwen_agent_runtime/README.md](/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/README.md) is not a throwaway stub:
   - it documents production-style endpoints
   - it documents mock mode and qwen-agent mode
   - it documents auth and deployment posture
4. the enterprise guardrail audit already scans `experimental/qwen_agent_runtime/app`
5. the full enterprise gate does not run the runtime app as its own first-class module suite, but the governed ERP-side integration paths are exercised through the existing semantic and post-contract verification

### 3.2 Enterprise Judgment

This is real architectural debt, but the repo evidence does not support stopping Phase 1.1 for it.

Current decision:

1. treat the external runtime as a governed external dependency, not as an ignored prototype
2. proceed with Phase 1.1
3. keep runtime-governance debt active because:
   - it still lives under `experimental/`
   - its own contract coverage is not yet first-class in the main release matrix
   - degraded-mode behavior should be documented more explicitly later

### 3.3 Preflight Outcome

Result:

1. not a stop-work blocker for Phase 1.1
2. remains active debt
3. reclassified to `near_blocker`

## 4. Preflight Finding: Service-User / Administrator Boundary

### 4.1 What The Repo Shows

1. many `Administrator` references exist in:
   - smoke helpers
   - hardening support
   - selftests
   - local governance probes
2. the primary runtime path [handle_qwen_user_message(...)](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py#L919) takes `user` from the caller instead of hardcoding `Administrator`
3. the semantic/runtime modules mostly take `user_id` as an input parameter in their real execution functions
4. the strongest remaining `Administrator` usage appears concentrated in:
   - support and smoke flows
   - rollout/test helpers
   - selftest execution paths

### 4.2 Enterprise Judgment

This is still real security debt, but the current evidence does not justify treating it as a Phase 1.1 blocker.

Current decision:

1. do not declare the production path to be Administrator-bound without a narrower runtime-security audit
2. do not ignore the debt
3. treat it as a security-sensitive near-blocker that must stay visible

### 4.3 Preflight Outcome

Result:

1. not a stop-work blocker for Phase 1.1
2. remains active debt
3. reclassified to `near_blocker`

## 5. Overall Go / No-Go Decision

Go.

Phase 1.1 may proceed.

Reason:

1. the two previously declared blockers are real but do not currently justify stopping delivery
2. both debts are now explicitly governed as active near-blockers
3. the next chapter should measure whether they interfere with real Delivery / Fulfillment implementation

## 6. Guardrails For Phase 1.1

While executing Phase 1.1:

1. do not expand `service.py` casually
2. do not add new domain-specific routing logic to Python if metadata can own it
3. measure whether Delivery / Fulfillment requires reusable framework changes or domain-specific branches
4. if runtime-governance uncertainty becomes a real blocker during implementation, pause only that phase and update the debt register
5. if a true production-path Administrator dependency is discovered, escalate it immediately

## 7. Immediate Next Step

Proceed to Delivery / Fulfillment discovery and design:

1. identify active ERP doctypes and reports
2. identify capability/report-family metadata gaps
3. design the smallest governed implementation slice
