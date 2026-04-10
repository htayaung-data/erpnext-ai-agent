# Qwen Chat Refactor Map

Status: active Phase 2 refactor guidance  
Audience: maintainers working on `qwen_chat`  
Goal: keep the refactor fast, safe, and enterprise-grade

## 1. Current Refactor Direction

The current refactor direction is correct.

We are moving from:

1. one large monolithic `service.py`
2. mixed dispatcher, runtime, helper, and smoke logic in one place
3. difficult-to-isolate regression risk

Toward:

1. `service.py` as orchestration shell
2. runtime and lane behavior in explicit modules
3. support logic grouped by domain
4. targeted hardening based on slice risk

This refactor is successful when the code becomes easier to reason about without changing governed behavior.

## 2. Ownership Rules

### 2.1 What Stays In `service.py`

`service.py` should keep:

1. top-level orchestration entrypoints
2. lane precedence and routing order
3. rollout application at the dispatcher level
4. contract-critical glue between lanes, context, and support helpers
5. thin wrappers that preserve stable internal call points when useful

`service.py` should not keep:

1. large helper bodies
2. evaluation suite plumbing
3. smoke session scaffolding
4. repeated parsing or formatting helpers
5. artifact, boundary, or follow-up support bodies that already have a natural module home

### 2.2 What Belongs In `lanes/`

`lanes/` owns bounded runtime paths that represent a distinct conversational lane, for example:

1. clarification
2. front door
3. repair
4. compiled query
5. reasoning
6. artifact boundary
7. entity drilldown
8. runtime gate
9. legacy runtime handling

Rule:

- if the code decides how one lane behaves after the dispatcher chooses it, it belongs in `lanes/`

### 2.3 What Belongs In `context/`

`context/` owns read and persistence helpers around session state, message history, and grounded context.

Rule:

- if the code is about retrieving or safely saving chat state, it belongs in `context/`

### 2.4 What Belongs In Support Modules

Support modules own non-dispatcher helper logic grouped by domain, for example:

1. `compiled_support.py`
2. `boundary_support.py`
3. `local_followup_support.py`
4. `family_evaluation_support.py`
5. `smoke_session_support.py`

Rule:

- if the code is sizeable, pure support logic, and not a lane or persistence concern, it belongs in a domain support module

## 3. Verification Tiers

### 3.1 Tier 1: Low-Risk Support Slices

Use Tier 1 for:

1. evaluation support extraction
2. smoke harness extraction
3. duplicate helper collapse
4. non-runtime reporting helpers
5. support code consolidation that does not alter dispatcher behavior

Required checks:

1. `python3 -m py_compile ...`
2. `python3 scripts/check_qwen_enterprise_guardrails.py`
3. fast guard probes
4. targeted smoke only if the slice touches a specific smoke path

### 3.2 Tier 2: Runtime-Sensitive Slices

Use Tier 2 for:

1. lane behavior
2. runtime result handling
3. recovery flow
4. compiled/reasoning/follow-up orchestration glue
5. any slice that changes user-visible runtime handling or contract precedence

Required checks:

1. everything in Tier 1
2. wrapped regression

Rule:

- default to Tier 2 when uncertain

## 4. Current Module Shape

The current refactor already established these important seams:

1. `lanes/` for lane execution
2. `context/` for session and grounded context
3. support modules for compiled, boundary, follow-up, rollout, evaluation, and smoke helpers

This means the project is no longer in the dangerous “single giant file” phase.  
The next job is consolidation, not heroic redesign.

## 5. Active Phase 2 Wave

Current Phase 2 priority:

1. finish moving remaining Phase 4B evaluation and reporting support out of `service.py`
2. keep smoke harness support grouped together
3. continue collapsing duplicate helper bodies into their existing domain modules

Recommended order:

1. finish `family_evaluation_support.py`
2. finish `smoke_session_support.py` and any smoke-case helpers if needed
3. collapse remaining duplicate helper bodies in `service.py`
4. stop and reassess before touching any major runtime path again

## 6. Stop Rule

Do not refactor forever.

Pause active micro-refactoring when these are true:

1. `service.py` is roughly in the `5.5k-6.5k` range
2. no large support bodies remain in the dispatcher
3. new engineers can easily tell where code belongs
4. remaining reductions are mostly cosmetic rather than architectural

At that point:

1. return focus to product delivery
2. refactor only when new feature work naturally touches an area

### 6.1 Current Status

This stop rule has now been reached.

Current checkpoint:

1. [service.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py) is below `5k` lines
2. the remaining `service.py` mass is mostly orchestration, stable wrappers, debug helpers, and scenario suites
3. continued micro-slicing is now optional and should be justified by architecture value, not line-count pressure

See:

1. [QWEN_CHAT_SERVICE_REFACTOR_CHECKPOINT.md](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/QWEN_CHAT_SERVICE_REFACTOR_CHECKPOINT.md)

## 7. Team Safety Rules

1. Never mix feature expansion into a refactor slice.
2. Never redefine dispatcher precedence casually.
3. Prefer extending an existing support module over creating many tiny one-off files.
4. Treat runtime/model variability, test instability, and product regressions as different classes of issues.
5. Keep unrelated UI work out of this refactor wave.

## 8. Practical Decision Rule

When deciding the next slice, ask:

1. Is this dispatcher logic or support logic?
2. Does this change runtime behavior or only organization?
3. Which existing module family already owns this concern?
4. What is the minimum verification tier that still preserves enterprise trust?

If the answer is unclear, the slice is probably too big.

## 9. Semantic Boundary

The project now has an explicit architecture boundary between:

1. semantic-governed governed-query intents
2. legacy family-surface fallback behavior

### 9.1 Semantic-Governed Intents

These intents are now owned by the semantic-resolution registry and runtime:

1. `financial_statement`
2. `inventory_summary`
3. `aging_analysis`
4. `trend_analysis`
5. `ranked_entities`
6. `product_performance`
7. `transaction_listing`

Rule:

- these intents must not be re-steered by lexical `family_tool_surface` routing once an interpretation or fallback artifact identifies them

### 9.2 Legacy Family-Surface Scope

`family_tool_surface` is now legacy-only support for:

1. non-migrated intents
2. bounded discovery/probe tooling
3. true legacy runtime paths where no semantic-governed intent has been established

Rule:

- if a request is already known to be one of the semantic-governed intents, the family-surface layer is not allowed to override, refine, or rescue it

### 9.3 Enterprise Enforcement Rule

Any new routing change must answer this first:

1. is the target intent already semantic-governed?

If yes:

1. extend the semantic-resolution registry and resolver
2. do not add message-driven fallback logic
3. do not add family-surface refinement for that intent

If no:

1. either keep it explicitly legacy
2. or plan a semantic migration first

## 10. Remaining Legacy Intent

After the current semantic migration wave, the only remaining legacy-only business intent is:

1. `financial_summary`

This intent should not be treated as a routine next migration slice.

Reason:

1. it is a cross-family summary umbrella over sales, inventory, receivable, payable, statement, and product-profitability reads
2. it likely needs either semantic decomposition into narrower governed intents or a governed composite-summary design
3. migrating it casually would create pressure toward keywords, hardcoded report forcing, or one-off rescue logic

Rule:

1. do not resume aggressive `service.py` trimming or runtime migration work that assumes `financial_summary` is solved
2. settle the `financial_summary` architecture first
