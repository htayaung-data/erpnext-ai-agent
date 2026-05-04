# Qwen ERP Current Roadmap Reconciliation And Next Implementation Plan

Date: 2026-05-04
Status: active roadmap reconciliation plan
Scope: AI Assistant roadmap alignment after Phase 3.6, NBU stabilization, zero-keyword cleanup, and Qwen runtime contract work
Branch: `feature/ai-assistant`

## 1. Purpose

This document reconciles the main roadmap with the nested stabilization roadmaps created during implementation.

The project has a macro roadmap, but recent work correctly created smaller roadmaps inside it because manual browser testing found shared quality issues. Those nested roadmaps were not distractions. They were quality-control gates needed before Phase 4 Complex Business Question Decomposition.

The current goal is to make the next path clear:

1. do not restart old completed phases;
2. do not jump into Phase 4 too early;
3. finish the remaining Phase 3.6 / NBU stabilization gates;
4. then enter Phase 4 with a stable assistant foundation.

## 2. Current Executive Truth

The main roadmap answer is:

1. Phase 1 operational expansion is complete for the currently approved active surfaces.
2. Phase 2 business definitions, formulas, thresholds, and governed KPI runtime execution are complete for the current approved scope.
3. Phase 3 composite governed artifacts are complete through the current customer/product/commercial/risk surfaces.
4. Phase 3.4 Customer Risk is complete for the current delivery chapter.
5. Phase 3.5 reasoning and recommendation authority boundaries are complete for blocked-authority safety.
6. Phase 3.6 Release Readiness is the active bridge before Phase 4.
7. NBU-S0 through NBU-S7 are automated-green.
8. NBU-S8 Manual Browser UAT is the active next product-quality gate.
9. NBU-S9 service and duplicate-lane consolidation remains pending as structural hardening before or alongside Phase 4 preflight.
10. Phase 4 has not started and should not start until S8 is green and S9 risk is either reduced or explicitly accepted.

Current repository state checked on 2026-05-04:

1. `feature/ai-assistant` is aligned with `origin/feature/ai-assistant`.
2. Enterprise guardrail audit passes.
3. Latest pushed checkpoints include:
   - `1f834b0 feat(qwen-runtime): add semantic business understanding contract`
   - `b693ec2 chore(infra): stabilize live app asset routing`
   - `7e97db3 Stabilize NBU release gate contracts`
   - `97f30cd Stabilize NBU zero-keyword guardrails`

## 3. Roadmap Layers

### 3.1 Macro Product Roadmap

The macro roadmap is still useful for long-range ordering:

1. governed operational coverage;
2. business definition and formula governance;
3. composite governed artifacts;
4. complex business question decomposition;
5. later multilingual, visual, OCR, and controlled actions.

However, it is no longer sufficient by itself to decide the current next task because Phase 3.6 and NBU stabilization added release-quality gates.

### 3.2 Active Bridge Roadmap: Phase 3.6

Phase 3.6 exists to protect Phase 4.

It proves that the assistant can already handle:

1. direct governed answers;
2. follow-ups;
3. visible table references;
4. entity detail enrichment;
5. clarification;
6. fallback;
7. unsupported authority boundaries;
8. context switching;
9. browser presentation quality.

Phase 3.6 is still active until Manual Browser UAT is complete.

### 3.3 Nested Stabilization Roadmap: NBU-S0 To NBU-S9

The NBU stabilization roadmap became necessary because browser tests proved the assistant was fragile with natural English and visible-context follow-ups.

Current state:

1. `NBU-S0` freeze and baseline: complete.
2. `NBU-S0.5` verification harness baseline: complete.
3. `NBU-S1` visible artifact intent contract: implemented and verified through S7.
4. `NBU-S2` projection contract: implemented and verified through S7.
5. `NBU-S3` latest relevant artifact selection: implemented and verified through S7.
6. `NBU-S4` detail enrichment contract: implemented and verified through S7.
7. `NBU-S5` professional clarification and fallback language: implemented and verified through S7.
8. `NBU-S6` guardrail closure: green.
9. `NBU-S7` automated regression matrix: green.
10. `NBU-S8` manual browser UAT: active next gate.
11. `NBU-S9` service and duplicate-lane consolidation: pending.

### 3.4 Zero-Keyword Stabilization Roadmap

The zero-keyword roadmap was a correction layer inside NBU stabilization.

It was needed because some successful fixes still risked becoming phrase patches instead of contract-led behavior.

Current state:

1. strengthened enterprise guardrail is green;
2. duplicate runtime tree was removed after archive and approval;
3. visible-context and detail-enrichment seams were moved toward structured contracts;
4. official guardrail passing does not mean the project is absolutely free from every lexical helper;
5. zero-keyword remains a continuous standard: no new protected runtime phrase routing and no single-prompt fixes.

### 3.5 Qwen Runtime Contract Work

The Qwen runtime now has a semantic business-understanding contract endpoint and related test coverage.

Current state:

1. runtime source and tests were committed as a coherent runtime slice;
2. runtime-image tests passed;
3. this is foundation work, not permission to activate full Phase 4 routing yet;
4. deeper activation belongs to later NBU front-controller slices such as governed requery and fresh query routing.

## 4. Current Blockers Before Phase 4

The remaining blockers are quality gates, not missing feature ambition.

### 4.1 NBU-S8 Manual Browser UAT

S8 must verify browser behavior for:

1. customer risk rank follow-ups;
2. supplier AP rank and detail follow-ups;
3. sales invoice row follow-ups;
4. revenue ranking projections;
5. financial statement follow-ups;
6. unsupported recommendation and prediction boundaries;
7. natural-language confusion recovery;
8. non-executable option prevention.

Known recent concern:

1. the assistant must not offer a combined health-summary option unless that option is executable;
2. if it asks a clarification question, every offered choice must be something it can actually answer;
3. if the user challenges a bad clarification, the assistant should recover in business language instead of routing to an unrelated statement.

### 4.2 NBU-S9 Structural Consolidation

S9 should not be a large rewrite, but it should reduce regression risk before complex decomposition.

Minimum S9 scope:

1. confirm canonical lane ownership;
2. prevent duplicate lane/runtime paths from silently drifting;
3. keep `service.py` as orchestration only where practical;
4. add guardrails or tests for duplicate path recurrence;
5. avoid mixing cleanup with new business behavior.

### 4.3 Documentation Truth And Discoverability

The docs are better than before, but there are still discoverability risks:

1. older macro-roadmap docs still contain completed phase history and should not be treated as current next-step authority alone;
2. `current_docs` includes some copied docs with visible text corruption, so doc consolidation must be careful and content-parity based;
3. this reconciliation doc should be the near-term "where are we now" entry until Phase 3.6 closes.

## 5. Updated Implementation Plan

### Step 1: Record This Roadmap Reconciliation

Goal:

Make the current direction discoverable and prevent roadmap confusion.

Work:

1. add this document to `current_docs`;
2. reference it from the current docs README;
3. do not archive or delete older docs in this step.

Exit gate:

1. branch remains clean after commit/push;
2. no governance doc deletion is bundled into this step.

### Step 2: Resume NBU-S8 Manual Browser UAT

Goal:

Finish the real browser quality gate before Phase 4.

Process:

1. run one UAT group at a time;
2. user reports exact failing answer;
3. developer classifies the shared seam;
4. fixes must be contract-led, not keyword-led;
5. rerun guardrail and targeted tests after each fix.

Immediate first group to revisit:

1. Group 4: Financial Statement Clarification And Section Follow-Up.
2. Group 6: Natural Confusion Recovery.

Reason:

Recent browser results showed the most serious remaining product-quality risk here: non-executable options and fallback recovery.

Exit gate:

1. all S8 groups pass or have approved documented exceptions;
2. no internal technical language leaks to users;
3. no unsupported option is offered as executable;
4. guardrail remains green.

### Step 3: Run Post-S8 Automated Regression

Goal:

Prove manual fixes did not break automated guarantees.

Minimum gate:

1. enterprise guardrail;
2. NBU regression suite;
3. S7 segmented profiles;
4. bounded release-gate profile;
5. focused tests for any touched modules.

Exit gate:

1. automated gate is green;
2. slow gate results are recorded if rerun;
3. any known latency issue is documented separately from correctness.

### Step 4: Execute Bounded NBU-S9 Structural Consolidation

Goal:

Reduce structural regression risk before Phase 4.

Work:

1. inventory lane modules and duplicate path risks;
2. decide canonical ownership;
3. leave compatibility wrappers only where needed;
4. add direct tests or guardrails against drift;
5. avoid a broad `service.py` rewrite.

Exit gate:

1. canonical lane ownership documented;
2. duplicate runtime/lane paths cannot silently reappear;
3. guardrail and NBU tests pass;
4. no behavior regression in browser-critical flows.

### Step 5: Phase 3.6 Closure Review

Goal:

Decide whether Phase 4 can begin.

Inputs:

1. S8 manual browser UAT result;
2. post-S8 automated gate result;
3. S9 structural risk result;
4. updated known limitations;
5. current branch and deployment state.

Exit gate:

1. user and developer agree Phase 3.6 is closed;
2. accepted risks are explicit;
3. docs state what was tested and what remains deferred;
4. Phase 4 starts only after this decision.

### Step 6: Phase 4 Preflight Design

Goal:

Design, not immediately implement, complex business question decomposition.

Phase 4 should start with:

1. complex-request interpretation contract;
2. decomposition planner;
3. governed sub-question execution plan;
4. evidence compatibility and join rules;
5. answer composer with provenance;
6. failure and partial-answer policy;
7. no recommendation, prediction, or approval expansion unless policy exists.

Exit gate:

1. Phase 4 design doc approved;
2. first narrow Phase 4 slice selected;
3. rollback and test gates defined.

## 6. What Not To Do Next

Do not:

1. start new HR, CRM, OCR, charts, or write-action work;
2. start Phase 4 implementation before S8 and S9 decisions;
3. fix browser issues by adding prompt-specific keyword branches;
4. delete old governance docs because a newer copy seems similar;
5. commit Qwen runtime or infra changes without runtime-specific verification;
6. treat automated tests as a replacement for browser UAT.

## 7. Recommended Immediate Next Action

The next implementation action should be:

1. commit this roadmap reconciliation doc;
2. run NBU-S8 Group 4 and Group 6 carefully in browser;
3. fix any failure through shared NBU/clarification/option-contract seams;
4. rerun S7 and guardrail after the fixes;
5. only then continue through the remaining S8 groups.

## 8. Phase 4 Entry Statement

Phase 4 is the right next major product milestone, but not the immediate next coding task.

The immediate next coding task is still Phase 3.6 / NBU-S8 stabilization.

The safe project posture is:

1. finish S8;
2. reduce or accept S9 structural risk;
3. close Phase 3.6;
4. design Phase 4;
5. implement Phase 4 one narrow slice at a time.
