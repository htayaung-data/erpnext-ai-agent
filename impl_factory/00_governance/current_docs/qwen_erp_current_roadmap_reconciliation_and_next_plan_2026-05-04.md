# Qwen ERP Current Roadmap Reconciliation And Next Implementation Plan

Date: 2026-05-04
Last updated: 2026-05-07
Status: active roadmap reconciliation plan
Scope: AI Assistant roadmap alignment after Phase 3.6, NBU stabilization, zero-keyword cleanup, UX-S5 consultant contract work, and Qwen runtime contract work
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
8. UX-S5 consultant reasoning contracts are implemented and pushed, but manual browser UAT exposed context-authority blockers that must be fixed before declaring S8 green.
9. NBU-S8 Manual Browser UAT remains the active product-quality gate.
10. NBU-S9 service and duplicate-lane consolidation remains pending as structural hardening before or alongside Phase 4 preflight.
11. Phase 4 has not started and should not start until S8 is green and S9 risk is either reduced or explicitly accepted.

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

### 3.6 Active UX Roadmap Inside NBU-S8

Manual browser UAT exposed that NBU-S8 is not only a checklist. It now contains a dedicated UX hardening roadmap.

This UX roadmap is the active quality gate before Phase 4. It must stay inside NBU-S8 / Phase 3.6, not become a disconnected roadmap and not be postponed until after S8.

Current UX roadmap state:

1. `UX-S0` Baseline Current Failures: mostly complete.
   - Current bad behaviors are recorded through browser testing: unrelated fallback, non-executable options, poor typo recovery, shallow "more" answers, context drift, and mechanical consultant responses.
2. `UX-S1` Unified Recovery Contract: partially complete.
   - Several typed contracts exist, but recovery decisions are not yet consistently unified across clarification, fallback, challenge recovery, and evidence expansion.
3. `UX-S2` Executable Clarification Gate: partially complete.
   - Some non-executable options were fixed, but every clarification option still needs executable proof before it is offered to the user.
4. `UX-S3` Typo And Misspelling Handling: partially complete.
   - Common spelling recovery exists in places, but it is not yet consistently validated through governed metadata and browser UAT.
5. `UX-S4` Professional Fallback Renderer: partially complete.
   - Some fallback wording improved, but robotic fallback and weak challenge recovery still appear.
6. `UX-S5` Evidence Expansion / Consultant Mode: active and not complete.
   - This is the current main work.
   - The assistant must not merely repeat visible reports when the user asks for meaning, deeper detail, implications, consultant-style interpretation, or advice.
   - The assistant must first decide whether the current artifact is sufficient, whether deeper governed ERP evidence is needed, or whether a governed formula/definition is needed.
7. `UX-S6` Context Authority Stabilization: active next implementation slice.
   - Browser UAT after UX-S5 showed that latest visible table authority, generic follow-up anchoring, professional fallback wording, and focused line-item continuation are still not stable enough.
8. `UX-S7` Cross-Family Regression And Browser UAT: not complete.
   - Finance, AR/AP, customer, supplier, product, inventory, invoices, unsupported questions, typo questions, and user challenge questions still need cross-family proof after UX-S6.

#### 3.6.1 UX-S5 Checkpoint Truth

`UX-S5` produced a useful checkpoint:

1. semantic detail intent slots were added;
2. governed evidence drilldown registry was added;
3. metadata-backed consultant playbooks were added;
4. consultant role and entity-detail capability bindings were moved into metadata registries;
5. focused tests and guardrail were green at the pushed checkpoint `d5e639d`.

However, browser UAT showed that consultant depth alone is not enough. The next blocker is not wording polish. It is context authority.

Current UX-S6 blockers:

1. latest visible table authority is wrong in some flows;
2. generic follow-ups such as "more insight" can drift to an unrelated family;
3. unsupported prediction fallback can still expose technical language;
4. line-item continuation can lose the active line, such as COGS, and fall back to broad statement interpretation;
5. filter follow-ups can drift to stale artifacts instead of answering from proven context or saying the filter was not proven.

UX-S6 must fix items 1 through 4 directly and add only minimal filter-follow-up safety. Full filtering is deferred to the governed filtering phase.

### 3.7 Roadmap Sequence After UX-S6

The active sequence as of 2026-05-07 is:

1. `UX-S6`: Context Authority Stabilization.
2. `UX-S7`: Cross-Family Regression And Browser UAT.
3. `FILTER-S0+`: Governed Filtering Expansion across families.
4. `MI-S0+`: Management Intelligence core with formula, ratio, and analytics viewpoints.
5. `MI-ADV-S0+`: advanced consultant drilldown, root-cause, scenario, and sensitivity work.
6. `STAB-S0+`: stabilization, release gates, lane consolidation, remaining lexical-debt cleanup, and repeatable UAT harness.
7. `FAM-S0+`: Family Onboarding Standard and new-family test harness.

This order is intentional:

1. context authority must be reliable before any deeper analysis can be trusted;
2. filtering must be governed before MI calculates filtered ratios, filtered trends, or filtered consultant advice;
3. MI should introduce the reusable analysis viewpoints, not one-off family answers;
4. family onboarding should be finalized after context, filtering, and MI contracts are mature enough to become onboarding requirements.

#### UX-S5 Detailed Mini-Slices

`UX-S5` is the correct home for consultant-grade business behavior. It should not be implemented as prompt-specific keyword logic.

`UX-S5A`: Consultant intent and response contract

1. classify requests for interpretation, deeper explanation, business meaning, implications, risk, guidance, or advice through semantic intent and typed contracts;
2. do not add phrase-specific branches for individual prompts;
3. prove that consultant intent can supersede shallow presentation-only transforms.

Exit gate:

1. consultant-intent tests pass for at least AR/AP, financial statements, products, and document rows;
2. ordinary presentation requests still use presentation transforms;
3. enterprise guardrail remains green.

`UX-S5B`: Evidence expansion planner

1. decide whether the current visible artifact is enough;
2. if shallow, plan related governed ERP evidence before answering;
3. if deeper evidence is unavailable, answer professionally with the current evidence and state the missing evidence in business language.

Exit gate:

1. no repeated-table answer is treated as a consultant answer;
2. no unsupported data is invented;
3. expansion decisions are observable through typed contracts.

`UX-S5C`: Consultant interpretation renderer

1. convert governed facts into business interpretation;
2. separate facts, interpretation, risk/impact, and possible next steps;
3. use visible table sections such as summary, distribution, ranked rows, and line-item sections as evidence;
4. avoid hidden unrelated rows when the user is asking about the visible result.

Exit gate:

1. AR Aging consultant explanation interprets overdue ratio, aging bucket distribution, chronic aging exposure, and customer concentration;
2. AP Aging consultant explanation interprets payable pressure, supplier concentration, and aging distribution;
3. P&L / Balance Sheet / Cash Flow explanations interpret business meaning instead of restating rows;
4. answers remain grounded and numeric validation rejects unsupported derived totals.

`UX-S5D`: Governed formula and MI handoff

1. when the user asks for company health, ratios, or formula-based meaning, use the existing business-definition / formula registry where available;
2. calculate ratios only from governed ERP evidence and approved formulas;
3. if the formula or data is missing, explain the missing piece professionally and offer the nearest executable evidence path.

Exit gate:

1. current ratio, debt-to-equity, gross margin, net margin, AR overdue ratio, AP overdue ratio, and working-capital indicators use governed definitions when available;
2. formula output includes formula, inputs, result, and interpretation;
3. no unsupported management recommendation is produced without policy.

`UX-S5E`: Consultant challenge recovery

1. when the user challenges a shallow or wrong answer, the assistant should acknowledge the issue and recover through the correct contract path;
2. challenge recovery must not route to unrelated reports;
3. recovery must preserve the active business context unless the user clearly switches context.

Exit gate:

1. user challenge after AR explanation recovers into AR consultant interpretation;
2. user challenge after financial statement explanation recovers into the active statement context;
3. user challenge after unsupported request does not invent capability and does not blame the user.

#### UX-S5 Definition Of Done

`UX-S5` is done only when:

1. consultant requests produce interpretation, not table repetition;
2. evidence expansion is attempted when current evidence is shallow and a governed related path exists;
3. missing evidence is explained in professional business language;
4. formulas and ratios use MI/business-definition contracts, not ad hoc arithmetic;
5. no lexical / keyword / hardcoded single-case routing is introduced;
6. targeted automated tests and exact browser-flow probes pass;
7. enterprise guardrail remains green.

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

### Step 2: Resume NBU-S8 / UX Manual Browser UAT

Goal:

Finish the real browser quality gate before Phase 4.

Process:

1. run one UAT group at a time;
2. user reports exact failing answer;
3. developer classifies the shared seam;
4. fixes must be contract-led, not keyword-led;
5. rerun guardrail and targeted tests after each fix.

Immediate first group to revisit:

1. `UX-S5A`: consultant intent and response contract.
2. `UX-S5B`: evidence expansion planner.
3. `UX-S5C`: consultant interpretation renderer.
4. `UX-S5D`: governed formula and MI handoff.
5. `UX-S5E`: consultant challenge recovery.

Reason:

Recent browser results showed the most serious remaining product-quality risk: the assistant can retrieve governed reports, but it still repeats data instead of interpreting the business meaning when the user asks for consultant-style explanation, deeper detail, or guidance.

Exit gate:

1. `UX-S5` passes its detailed definition of done;
2. all remaining S8 groups pass or have approved documented exceptions;
3. no internal technical language leaks to users;
4. no unsupported option is offered as executable;
5. guardrail remains green.

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
