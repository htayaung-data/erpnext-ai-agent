# Qwen ERP Enterprise Tech Debt Register

Status: active debt register  
Date: 2026-04-04  
Scope: active structural debt that should inform roadmap execution without replacing it

## 1. Purpose

This register exists so the team can:

1. keep important debt visible
2. avoid forgetting known risks
3. prevent the roadmap from turning into a cleanup dump
4. decide which debt must be handled before or during a phase

This is not a “fix everything now” list.
It is a decision tool.

## 2. Classification Rule

Every debt item must be one of:

1. `blocker`
   - cannot safely proceed with the next relevant phase until addressed or explicitly governed
2. `near_blocker`
   - phase can proceed, but this debt may force a bounded fix during execution
3. `monitor`
   - real debt, but not worth stopping current delivery for

Each item should also have:

1. why it matters
2. when it should be revisited
3. what would escalate it

## 3. Current Active Debt

### 3.1 External Qwen Runtime Governance

Status:

1. `near_blocker`

Scope:

1. `experimental/qwen_agent_runtime`
2. [runtime_client.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/runtime_client.py)

Why it matters:

1. governed fresh-query and follow-up interpretation depend on this runtime path
2. its production governance boundary must be explicit
3. degraded-mode behavior must be known if the external runtime is unavailable or unstable

Needed before or during the next phase:

1. treat this runtime as a governed external dependency for Phase 1.1
2. document timeout, failure, and degraded-mode behavior more explicitly over time
3. confirm whether and when its own contract suite should become first-class in the main release matrix

Escalation trigger:

1. if a new capability phase depends on this runtime and runtime-governance uncertainty starts blocking delivery

### 3.2 Service-User / Administrator Boundary

Status:

1. `near_blocker`

Scope:

1. current runtime and support paths using `Administrator` defaults
2. blueprint security requirement for a dedicated least-privilege service user

Why it matters:

1. the blueprint explicitly rejects long-term Administrator credential usage
2. if production runtime still depends on Administrator, security posture is weaker than documented

Needed before or during the next phase:

1. classify which `Administrator` usages are:
   - test/support only
   - smoke-only
   - real runtime/security debt
2. document or fix production-path usage if discovered

Escalation trigger:

1. if any production execution path still requires Administrator privilege

### 3.3 `service.py` Orchestration Concentration

Status:

1. `near_blocker`

Scope:

1. [service.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py)

Why it matters:

1. orchestration concentration increases merge conflict and regression risk
2. every new phase may touch the same high-traffic file

Why it is not a blocker right now:

1. current release gate is green
2. the system is stable enough to continue product expansion
3. a broad refactor now would repeat the mixed refactor/hardening mistake

How to handle it:

1. do not launch a large refactor-first chapter
2. measure how much each new phase depends on `service.py`
3. if Phase 1.1 or Phase 1.2 becomes too Python-heavy, promote a bounded orchestration reduction slice later

Escalation trigger:

1. if every new domain requires meaningful `service.py` changes and merge/test pain becomes persistent

### 3.4 Lane Dependency Injection Shape

Status:

1. `near_blocker`

Scope:

1. lane modules that receive many callable dependencies

Why it matters:

1. it makes lanes harder to test in isolation
2. it increases the cost of new lane or capability work

Why it is not a blocker right now:

1. lanes still helped us close the current hardening chapter
2. this is structural friction, not immediate correctness failure

How to handle it:

1. avoid expanding parameter lists casually
2. if Phase 1.x shows real testing friction, plan a bounded context-object refactor later

Escalation trigger:

1. if lane testing becomes materially slower or feature slices start bypassing lanes to avoid injection complexity

### 3.5 `fresh_query_interpreter.py` Size And Scope

Status:

1. `near_blocker`

Scope:

1. [fresh_query_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py)

Why it matters:

1. large interpreter scope suggests too much behavior is still concentrated there
2. future capability growth may keep adding logic in a file that is already too large

How to handle it:

1. do not refactor it preemptively
2. watch whether new phases require domain-specific Python additions there
3. if they do, treat that as a signal to extract reusable compiler/interpreter seams later

Escalation trigger:

1. if new capabilities repeatedly require intent-specific interpreter branches

### 3.6 Contract Versioning And Compatibility Policy

Status:

1. `monitor`

Why it matters:

1. contracts are now runtime currency
2. long-term growth will need compatibility discipline

Why it is not urgent yet:

1. current team surface is still relatively concentrated
2. it is not the biggest risk for the immediate next domain slice

How to handle it:

1. keep contract evolution simple for now
2. revisit once multiple domains or teams start changing producer/consumer seams concurrently

Escalation trigger:

1. contract changes begin to break consumers often

### 3.7 Distributed Tracing Across ERP -> Runtime -> FAC

Status:

1. `monitor`

Why it matters:

1. incident diagnosis becomes harder without end-to-end correlation

Why it is not urgent yet:

1. current observability is materially strong enough for the present release surface

How to handle it:

1. plan as a future observability improvement
2. escalate if incident diagnosis becomes a recurring pain point

### 3.8 SLO / Degradation Policy Formalization

Status:

1. `monitor`

Why it matters:

1. latency metrics without budgets are incomplete enterprise operations

Why it is not urgent yet:

1. release-gate stability and capability correctness are still more immediate priorities

How to handle it:

1. add once the next chapters make latency tradeoffs more visible

## 4. How To Use This Register

Before starting a new phase:

1. check whether any `blocker` applies directly
2. decide whether any `near_blocker` must be watched in that phase
3. leave `monitor` items alone unless the phase exposes them

During a phase:

1. if a `monitor` item starts actively hurting delivery, reclassify it
2. if a `near_blocker` repeatedly forces code churn, promote it to a blocker for the next phase

After a phase:

1. record whether a debt item got better, worse, or was unchanged

## 5. Current Recommendation

The current decision is:

1. do not stop the roadmap for broad refactor
2. explicitly govern blocker candidates before starting the next phase
3. proceed with Phase 1.1
4. measure whether `service.py`, lane-shape, or interpreter debt actually interferes with delivery
