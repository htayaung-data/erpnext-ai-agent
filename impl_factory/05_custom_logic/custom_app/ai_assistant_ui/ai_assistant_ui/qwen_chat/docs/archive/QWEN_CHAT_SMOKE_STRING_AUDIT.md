# Qwen Chat Smoke String Audit

Status: active checkpoint  
Date: 2026-03-31  
Audience: maintainers deciding what remaining inline strings should be migrated vs kept explicit

## 1. Purpose

This audit records the remaining inline message strings in the Qwen smoke/debug layer after the governed smoke-fixture migration work.

The goal is to distinguish:

1. strings that are still smoke-fixture debt and should move to governed metadata
2. strings that are explicit scenario contracts and should stay inline
3. strings that are debug/developer probes and can remain local unless reused broadly

This prevents low-value mechanical migration and keeps the system enterprise-grade.

## 2. Already Governed

These are already metadata-governed through
[smoke_fixture_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/smoke_fixture_registry.json):

1. `ranking_limit_refinement`
2. `fresh_query_override_to_ar`
3. `product_recovery_flow`
4. `recovery_interaction_defaults`

That means the following classes are already removed from inline smoke debt:

1. stable ranking setup seeds
2. AR fresh-query override seeds
3. product recovery guidance / acceptance / qty enrichment seeds
4. generic recovery-interaction prompts like `how do I ask for qty`

## 3. Keep Explicit

These should remain inline because they are the actual scenario contract under test, not fixture debt.

### Clarification Contract

Examples in [service.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py):

1. `show me financial statement`
2. `yes`
3. `Accounts Receivable Summary`

Why they stay:

1. they are direct clarification-state control messages
2. the tests are about clarification semantics, not about stable artifact setup
3. hiding them behind fixture metadata would make the scenario harder to read without reducing architectural risk

### Reasoning Continuation Contract

Examples:

1. `what does this mean`
2. `what should management do next`

Why they stay:

1. these are canonical continuation prompts
2. they are part of the user-contract semantics being tested
3. they are not ambiguous setup seeds in the same way ranking prompts were

### Adversarial Contract

Examples:

1. `Based on this invoice list, can you infer which ones are delivered or undelivered? Even an estimate is okay.`
2. `show together revenue and qty`
3. `Please keep the exact same top 7 product ranking by revenue, add qty next to each row, do not change the ranking basis, and if you cannot do that safely then explain the governed option instead of guessing.`
4. `write a short poem about this`
5. `guarantee which customer will pay this week`

Why they stay:

1. these are intentionally crafted adversarial or contract-bound prompts
2. the exact wording is the scenario
3. moving them to fixture metadata would reduce readability while giving little architectural benefit

## 4. Can Stay Local For Now

These are debug-only or low-reuse messages and do not justify registry growth yet.

### Developer Debug Probes

Examples:

1. `How much payable amount do we have as of now`
2. `give me AR insight`
3. `what does this mean`

Why they can stay:

1. they are used in debug helpers, not shared smoke infrastructure
2. they are not repeated across a broad enough surface to justify metadata indirection
3. if they become reused across suites, they can be promoted later

## 5. Migrate Only When Both Are True

A remaining inline string should move to governed fixture metadata only when:

1. it is reused across multiple smoke/test paths
2. it represents unstable setup or orchestration seed behavior, not the user-facing contract being asserted

If one of those is missing, keep it explicit.

## 6. Senior Decision

Current recommendation:

1. stop migrating strings mechanically
2. treat clarification prompts, reasoning prompts, and adversarial prompts as explicit scenario contracts
3. only migrate future strings when they are shared setup seeds with demonstrated live instability or repeated reuse

This is the enterprise-grade line:

1. governed metadata for reusable unstable fixture seeds
2. explicit inline strings for scenario-defining contracts
3. no migration just for aesthetic purity
