# Qwen ERP Enterprise Development Guidelines

Status: active development guide  
Date: 2026-04-04  
Scope: future implementation, refactor, hardening, and expansion work for the governed Qwen ERP assistant

## 1. Purpose

This document captures the development lessons earned during the full Qwen ERP journey so far:

1. contract foundation
2. read-query hardening
3. semantic family expansion
4. follow-up redesign
5. post-contract hardening
6. release-gate closure

Its purpose is to preserve engineering judgment, not just history.

Future work should use this guide to:

1. avoid repeating mistakes
2. choose the right implementation direction early
3. stay enterprise-grade under delivery pressure
4. expand product capability without destabilizing architecture

## 2. Executive Lessons

### 2.1 What We Did Right

These were the strongest success patterns:

1. we moved business meaning into contracts and metadata instead of prompt hacks
2. we enforced the rule `model proposes, compiler enforces`
3. we used typed grounded context instead of relying on raw chat text
4. we hardened behavior in bounded slices rather than broad uncontrolled rewrites
5. we used executable release gates instead of manual confidence
6. we kept docs honest about what was closed, partial, exploratory, or deferred
7. we added stop rules so completed chapters did not consume the whole roadmap

### 2.2 What We Did Wrong

These were the most expensive or misleading patterns:

1. letting raw message text steer runtime decisions after structured interpretation already existed
2. patching single user phrases instead of fixing the authority model
3. mixing large refactor movement with behavior hardening in the same slice
4. promoting desirable but unstable behavior into CI too early
5. checking stale answer wording instead of testing contract authority
6. continuing cleanup after the architectural stop rule was already met
7. treating “more tests” as a substitute for real hardening judgment

## 3. Non-Negotiable Principles

Every future chapter must obey these principles.

### 3.1 Business Fact Authority

1. ERP/FAC outputs are the only business-fact authority
2. the model may classify, propose, summarize, or translate
3. the model must not invent ERP facts, totals, statuses, dates, or entity relationships

### 3.2 Contract First

1. new business behavior should enter through a typed contract
2. runtime should consume contracts, not rediscover business meaning from text
3. if a new behavior cannot be expressed as a stable contract, it is not ready for enterprise runtime

### 3.3 Metadata Owns Business Policy

Business policy belongs in governed registries and definitions, including:

1. capability coverage
2. report family selection rules
3. clarification policy
4. normalization rules
5. business KPI definitions
6. threshold and formula rules
7. chartability and artifact rules

Code should orchestrate.
Metadata should define the business surface.

### 3.4 Fail Closed

When structured evidence is insufficient:

1. clarify
2. reject
3. block
4. fall back only through an explicit, bounded, audited exception

Do not guess.
Do not silently widen.
Do not convert ambiguity into fabricated confidence.

### 3.5 Explicit Authority Order

Authority order must always be visible and testable.

Examples:

1. latest grounded context wins over stale grounded context
2. current unsupported intent must override stale but legitimate prior context
3. accepted semantic payload must outrank raw-message fallback
4. explicit governed contradiction rules must outrank convenience rescue logic

## 4. Forbidden Patterns

These are not acceptable for final enterprise runtime.

### 4.1 Keyword Routing

Do not:

1. route capability by keyword bag
2. route report family by raw phrase match
3. mutate intent class from ad hoc text checks
4. infer time scope from prompt text after semantic payload already exists

### 4.2 Hardcoded Single-Case Fixes

Do not:

1. patch one prompt to make one smoke green
2. add one-off branch logic for a single user wording
3. encode company-specific business definitions directly in code
4. treat one real conversation as architecture

### 4.3 Hidden Fallback

Do not:

1. let raw-message rescue happen silently
2. allow fallback that is not visible in contract state
3. keep degraded behavior implicit in helper code

If fallback exists, it must be:

1. bounded
2. explicit
3. auditable
4. test-protected

### 4.4 Prompt-Led Business Logic

Do not store enterprise policy only in prompts.

This includes:

1. KPI formulas
2. company-specific definitions
3. approval semantics
4. report family routing
5. clarification authority

### 4.5 Architecture Drift By Cleanup

Do not:

1. reopen finished seams because local cleanup still feels possible
2. keep polishing after the release gate and stop rule are already satisfied
3. confuse line-count reduction with meaningful architectural progress

## 5. What “Enterprise Grade” Means In Practice

For this project, enterprise grade means:

1. typed contracts exist for every meaningful runtime seam
2. metadata and policy layers own business decisions
3. runtime behavior is auditable and replayable
4. fallback is bounded and explicit
5. release criteria are executable
6. docs distinguish active truth from historical context
7. expansion follows a governed order instead of opportunistic feature jumps

It does not mean:

1. infinite cleanup
2. perfect theoretical purity before shipping
3. uncontrolled feature bursts
4. manual confidence replacing release gates

## 6. Development Workflow For Any New Chapter

Use this workflow for every new domain or capability.

### 6.1 Define The Real Problem

Before coding, answer:

1. what user/business problem are we solving
2. what contract seam owns this problem
3. what metadata is needed
4. what is in scope
5. what must remain out of scope

If the change is mostly cleanup and does not reduce real risk, do not start it by default.

### 6.2 Define Ownership Early

For each new slice, declare:

1. what metadata owns
2. what contract owns
3. what runtime code owns
4. what docs must be updated

If ownership is fuzzy, implementation should pause until it is clear.

### 6.3 Introduce Contract Before Runtime Breadth

Preferred order:

1. define contract
2. define metadata
3. add contract tests
4. implement producer
5. implement consumer
6. add live verification

Do not start from string-handling or UI behavior first.

### 6.4 Ship In Bounded Slices

For a multi-domain phase:

1. ship one domain at a time
2. fully verify it
3. document its stop point
4. then move to the next domain

Never ship four domains in one uncontrolled burst.

## 7. Architecture Rules By Layer

### 7.1 Front Door

Front door owns:

1. low-signal refusal
2. unsupported non-business isolation
3. first transport/UI normalization

Front door must not own:

1. business fact generation
2. ERP truth
3. report routing from user phrases

### 7.2 Compiler Layer

Compiler owns:

1. capability family resolution
2. report-family/report selection
3. invariant injection
4. default completion when policy allows
5. clarify vs execute vs reject

Compiler must remain deterministic and policy-controlled.

### 7.3 Follow-Up Layer

Follow-up behavior must be resolved from:

1. structured grounded context
2. structured semantic follow-up payload
3. governed metadata

It must not be resolved primarily from:

1. regex extraction
2. projection phrase parsing
3. raw domain phrase comparison

### 7.4 Family / Composite Layer

Family and composite layers must:

1. normalize to governed artifacts
2. validate scope compatibility
3. block unsafe joins
4. preserve provenance across execution and rendering

### 7.5 Artifact Layer

Charts, graphs, dashboards, and exports must:

1. be derived from grounded structured data
2. use governed chartability rules
3. preserve source provenance
4. avoid freeform visualization fabrication

### 7.6 Multilingual Layer

Burmese and English behavior must be treated as product behavior, not cosmetic translation.

That means:

1. language detection is contract state
2. normalization is governed
3. same-language reply policy is explicit
4. translation must not change business facts

### 7.7 OCR Layer

OCR must enter as:

1. typed extracted evidence
2. confidence-scored input
3. deterministic normalization
4. clarify/reject on weak evidence

OCR text must not become direct business truth on its own.

### 7.8 Write Layer

All write behavior must follow:

1. propose
2. preview
3. confirm
4. execute
5. audit

No exception.

## 8. Verification Rules

### 8.1 Two-Layer Testing Is Required

Use both:

1. fast deterministic contract tests
2. live/persisted-session verification where state or orchestration matters

Neither layer is sufficient alone.

### 8.2 Test Contract Authority First

When a contract field exists:

1. assert on the contract first
2. use user-facing prose only as a secondary anchor

Do not make stale wording the primary test authority.

### 8.3 Promote Only Stable Behavior Into CI

If behavior is:

1. desirable but still drifting
2. not clearly guaranteed
3. dependent on unstable wording or inference

then do not lock it into CI yet.

### 8.4 Stateful Live Verification Often Must Be Sequential

For persisted session, live site, and shared DB state:

1. sequential validation is usually more trustworthy
2. parallel stateful execution can create false failures and deadlocks

Parallelism is good for reading, searching, and non-stateful shell work.
It is not automatically correct for live state validation.

### 8.5 Mixed-State Cases Matter More Than Happy Paths

Always include tests for:

1. latest-turn authority
2. stale context replacement
3. clarification/recovery interaction
4. repeated user actions
5. contradictory payloads

These failures are more enterprise-relevant than simple isolated happy paths.

### 8.6 Use The Real Release Gate

Default enterprise gate:

```bash
scripts/qwen_verify_enterprise_matrix.sh full
```

Use smaller gates only when the change is truly narrower and the active baseline allows it.

## 9. Refactor Rules

### 9.1 Refactor Only For Real Gain

Refactor is justified when it:

1. improves real runtime behavior
2. reduces meaningful architectural risk
3. removes meaningful verification debt
4. clarifies real ownership boundaries

Refactor is not justified merely because:

1. a file is still large
2. more extraction is possible
3. a seam can be made theoretically purer

### 9.2 Do Not Mix Large Refactor With Broad Behavior Change

Preferred order:

1. stabilize
2. refactor in bounded slices
3. rerun locked verification

Mixing big code movement with hardening or product expansion makes failures harder to interpret.

### 9.3 Stop When The Stop Rule Is Met

A chapter is ready to close when:

1. the real authority seam is corrected
2. residual exceptions are explicit and bounded
3. docs are honest
4. the release gate is green

After that, move on.
Do not convert success into endless local cleanup.

## 10. Documentation Rules

### 10.1 Current Vs Archive

Use:

1. `current_docs` for active source-of-truth planning
2. `archive_docs` for historical notes, closed slices, and superseded plans

If a doc is not in `current_docs`, do not treat it as current direction unless it is explicitly referenced there.

### 10.2 Document Honest Status

Docs must state clearly:

1. what is done
2. what is bounded
3. what is deferred
4. what is exploratory
5. what is explicitly out of scope

### 10.3 Write Lessons While They Are Fresh

Capture:

1. failed experiments
2. reverted tests
3. stop-rule decisions
4. reasons for not widening scope

Those decisions are part of the architecture memory.

### 10.4 Keep One Active Roadmap

There must be one current implementation roadmap, not many competing future plans.

Additional notes may exist, but the roadmap must remain singular and active.

## 11. Expansion Rules

### 11.1 Expand Only After Stability

New product expansion should begin only when:

1. the previous architecture chapter is closed
2. release gate is green
3. remaining debt is bounded and not the highest risk

### 11.2 Expand In The Right Order

Preferred order for this project:

1. governed operational coverage
2. governed composite artifacts
3. governed business definitions and formulas
4. complex request decomposition
5. multilingual layer
6. chart/graph/dashboard/export artifacts
7. OCR
8. write actions last

### 11.3 Do Not Jump To “Exciting” Features Too Early

Do not jump into:

1. OCR
2. chart/export
3. multilingual expansion
4. CRUD/write paths

before the governed read surface and formula/business-definition layers are mature enough to support them cleanly.

## 12. Review Checklist For Every Meaningful Change

Before merging a serious change, ask:

1. what contract owns this behavior
2. what metadata owns this policy
3. is any raw text still acting as hidden authority
4. does the change widen scope without an approved plan
5. are degraded exceptions explicit and bounded
6. are we testing the authoritative contract, not only prose
7. is the correct release gate rerun
8. are the current docs updated honestly
9. should this chapter stop now instead of continue polishing

If these questions cannot be answered clearly, the change is not ready.

## 13. Practical Operating Rules

If a team needs a short version, use this:

1. contract first
2. metadata owns business policy
3. compiler and policy layers enforce
4. no keyword routing
5. no single-case patches
6. fail closed when evidence is weak
7. make fallback explicit or remove it
8. test contract authority before wording
9. use live tests where state matters
10. stop polishing when the stop rule is met
11. expand one governed slice at a time
12. keep current docs clean and archive the rest

## 14. Final Rule

The most important discipline we learned is this:

Do not mistake motion for progress.

The right enterprise path is not:

1. more code
2. more patches
3. more tests
4. more docs

The right path is:

1. correct authority model
2. bounded implementation
3. executable verification
4. honest documentation
5. deliberate expansion only after closure
