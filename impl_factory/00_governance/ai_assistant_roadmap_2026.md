# AI Assistant Roadmap 2026 (V7 Enterprise Delivery Program)

Version: 7.0  
Effective date: 2026-02-21  
Program window: 2026-02-23 to 2026-07-12 (20 weeks)  
Primary codebase: `ai_assistant_ui`  
Engine policy: `v7` only (legacy engines removed)

## 1) Program Objective
Deliver an enterprise-level ERP AI Assistant that is reliable on first-run business queries, robust over 3-4 turn follow-up chains, and safe for write operations with full auditability.

## 2) Delivery Policy (Hard Rules)
1. Contract-bound implementation: all phases must satisfy `ai_assistant_contract_v2.md` version `v7.0`.
2. No keyword-driven routing/scoring in runtime core modules.
3. No phase overlap without exit criteria pass from previous phase.
4. No promotion on rerun-based success; first-run evidence only.
5. Legacy `v2`/`v3` engine code is not allowed in active runtime path.

## 3) Workstream Structure
1. Runtime Plane: parser, constraints, resolver, planner, executor, validator, context, clarification, composer.
2. Control Plane: capability ingestion, ontology normalization, replay manager, KPI gate service, model/prompt registry, drift monitor.
3. Security Plane: RBAC boundary enforcement, row/field masking, PII redaction, isolated write engine.
4. QA/Ops Plane: deterministic scoring, dashboards, canary operations, rollback runbooks.

## 4) Phase Plan (V7)

## Current Execution Status (as of 2026-02-21)
1. Phase 0: complete at code-governance level (legacy cleanup + contract guardrails + governance policy file + passing guardrail checks).
2. Phase 1: complete (golden replay packs + manifest validation + deterministic first-run scorer + baseline runner finalized).
3. Latest baseline artifacts: `impl_factory/04_automation/logs/20260221T145649Z_phase1_first_run_baseline.json` and `impl_factory/04_automation/logs/20260221T145649Z_phase1_first_run_baseline.md`.
4. Baseline first-run KPI snapshot (current build): total=26, passed=17, failed=9, first_run_pass_rate=0.6538.
5. Phase 2 is now unblocked for capability-platform implementation, with baseline failures tracked as improvement targets.

## Phase 0 (Week 1: 2026-02-23 to 2026-03-01) - Governance Lock
Entry:
1. current system runnable (`v7`)

Work:
1. freeze ad-hoc runtime behavior changes
2. define allowed/forbidden runtime patterns
3. implement CI static guardrails for banned keyword routing in core modules
4. pin baseline environment versions and data snapshot references

Exit:
1. CI blocks contract violations
2. no ungoverned runtime logic changes merge

Evidence:
1. CI rule logs and failed-sample proof
2. governance policy file and approval record

Rollback:
1. not applicable (governance phase)

## Phase 1 (Weeks 2-3: 2026-03-02 to 2026-03-15) - Benchmark and First-Run Scoring
Entry:
1. Phase 0 complete

Work:
1. build labeled golden suites:
   - single-turn core read
   - 3-turn and 4-turn context chains
   - transform follow-ups
   - no-data and unsupported
   - write safety checks
2. implement deterministic first-run scorer and artifact emitter
3. publish baseline KPI report

Exit:
1. baseline KPIs published and versioned
2. scorer reproducibility verified

Evidence:
1. replay pack manifests
2. baseline KPI artifact set

Rollback:
1. maintain current engine mode; block V7 promotion

## Phase 2 (Weeks 4-5: 2026-03-16 to 2026-03-29) - Capability Platform
Entry:
1. scoring infrastructure active

Work:
1. implement capability schema v1 (`metric`, `dimension`, `filter`, `time`, `constraints`, `confidence`, `freshness`)
2. implement FAC/ERP capability ingestion job
3. add schema-drift and stale-capability alerts
4. produce capability coverage report

Exit:
1. active report-family capability coverage >=95%
2. stale and unknown capabilities are flagged automatically

Evidence:
1. capability coverage report
2. drift-alert test artifacts

Rollback:
1. disable v7 resolver selection; keep shadow collection only

## Phase 3 (Weeks 6-7: 2026-03-30 to 2026-04-12) - Spec Parser and Constraint Engine
Entry:
1. capability graph stable

Work:
1. implement strict `BusinessRequestSpec` parser (one retry max)
2. implement deterministic `ConstraintSet` builder
3. persist canonical turn-state schema
4. convert required-filter runtime failures into blocker clarifications

Exit:
1. parser schema-valid rate >=99%
2. mandatory-filter runtime errors eliminated from read path

Evidence:
1. parser validation suite
2. blocker-conversion suite

Rollback:
1. route traffic back to stable engine while keeping V7 replay

## Phase 4 (Weeks 8-10: 2026-04-13 to 2026-05-03) - Resolver and Planner Refactor
Entry:
1. parser and constraints stable

Work:
1. feasible candidate retrieval strictly from capability graph
2. rank only feasible candidates
3. typed FAC execution planner with bounded retries/timeouts/idempotency
4. confusion-pair test hardening (receivable/payable, customer/supplier, sold/received)

Exit:
1. wrong-report rate improves >=40% from baseline
2. confusion-pair suite pass >=95%

Evidence:
1. resolver regression report
2. planner typed-call contract tests

Rollback:
1. disable V7 active route; keep V7 shadow metrics collection

## Phase 5 (Weeks 11-12: 2026-05-04 to 2026-05-17) - Validator and Audit Envelope
Entry:
1. resolver/planner stable

Work:
1. implement deterministic validator check IDs for metric/dimension/time/filter/shape
2. enforce `PASS`, `REPAIRABLE_FAIL`, `HARD_FAIL` policy
3. enforce mandatory `TurnAuditEnvelope` persistence
4. add no-data/unsupported correctness checks

Exit:
1. output-shape pass rate = 100% on mandatory set
2. audit envelope completeness = 100% on actionable turns

Evidence:
1. validator check-ID report
2. audit completeness report

Rollback:
1. fail gate and halt promotion

## Phase 6 (Weeks 13-14: 2026-05-18 to 2026-05-31) - Context Engine and Transform State
Entry:
1. validator stable

Work:
1. enforce `active_topic_id`, `active_result_id`, `active_filter_context`
2. implement reference binding (`that`, `those`, `same`, `previous`)
3. implement correction handling (`I mean`, `not X use Y`)
4. make transform state idempotent and anchored to prior result

Exit:
1. 3-turn follow-up accuracy >=95%
2. 4-turn follow-up accuracy >=90%
3. contamination rate <5%

Evidence:
1. multi-turn replay scorecards
2. contamination incident report

Rollback:
1. disable context-dependent V7 follow-up routing and return to stable path

## Phase 7 (Weeks 15-16: 2026-06-01 to 2026-06-14) - Clarification and Response Layer
Entry:
1. context gates passed

Work:
1. blocker-only clarification engine with reason-code dedupe
2. non-analytic conversational response policy (greeting/capability prompts)
3. fact-locked LLM response composer (cannot alter validated values)
4. global output formatting contract enforcement (thousand separator + 2 decimals)
5. UI typing/status indicator integration for long-running turns

Exit:
1. clarification loop <1%
2. unnecessary clarification <=5%
3. repeated same blocker after user answer = 0 in mandatory suite

Evidence:
1. clarification policy suite report
2. composer factual-lock test results
3. UI status indicator demo and logs

Rollback:
1. fallback to deterministic plain response mode without composer

## Phase 8 (Weeks 17-18: 2026-06-15 to 2026-06-28) - Security and Write Isolation
Entry:
1. read path quality gates pass

Work:
1. implement isolated write state machine (`draft -> confirm -> execute -> audit`)
2. enforce RBAC + row/field masking at tool boundary
3. enforce PII redaction policy
4. execute write safety and permission test suites

Exit:
1. unconfirmed write violations = 0
2. permission suite pass = 100%

Evidence:
1. write safety report
2. permission enforcement artifacts

Rollback:
1. keep write features disabled and retain read-only deployment

## Phase 9 (Weeks 19-20: 2026-06-29 to 2026-07-12) - Observability, Canary, and Activation
Entry:
1. end-to-end V7 gates green

Work:
1. complete dashboards and SRE runbooks
2. perform shadow reliability verification on production-like traffic
3. canary rollout: 10% -> 25% -> 50% -> 100%
4. run rollback rehearsal at each canary stage

Exit:
1. all KPI gates pass at each stage with minimum sample size
2. rollback rehearsal proven
3. full V7 activation approved

Evidence:
1. canary stage KPI snapshots
2. go/no-go records
3. rollback rehearsal records

Rollback:
1. automatic fallback to prior stable engine on gate breach

## 5) Non-Negotiable KPI Gates
1. wrong-report rate <=5% (first-run, sample >=300)
2. follow-up accuracy: 3-turn >=95%, 4-turn >=90% (sample >=150 chains)
3. unnecessary clarification <=5%
4. clarification loop rate <1%
5. first-run pass >=90%
6. output-shape pass =100% on mandatory suite
7. unsupported/no-data/permission envelope correctness >=98%
8. write safety violations =0
9. P95 latency within SLA by query class

## 6) Canary Stop Rules
1. stop stage if wrong-report rate breaches threshold by >20% relative margin
2. stop stage if clarification loop breaches threshold for two consecutive windows
3. stop immediately on any write safety violation
4. require explicit go/no-go signoff to continue

## 7) Minimum Artifact Pack Per Phase
1. changed modules and migration notes
2. deterministic test report
3. KPI delta from baseline
4. known risks and mitigations
5. rollback verification note

## 8) Manual QA Checkpoints
1. end Phase 4: wrong-report and confusion-pair stability
2. end Phase 6: multi-turn follow-up and correction chains
3. end Phase 7: clarification quality, response quality, formatting, typing indicator behavior
4. end Phase 9: full business acceptance before 100% activation

## 9) Deferred Scope Until Post-V7 Stabilization
1. advanced forecasting and predictive ML
2. company policy Q&A and broad RAG assistant behavior
3. generalized open-domain chat

## 10) Governance Notes
1. roadmap and contract versions must move together (`v7.x`)
2. any scope change requires explicit phase impact and gate updates
3. promotion is blocked if evidence pack is incomplete

## 11) Phase 0 Execution Checklist (Operational)
Phase window: 2026-02-23 to 2026-03-01

Owner roles:
1. `AI_LEAD`: architecture owner and contract reviewer
2. `BE_OWNER`: CI/static-check implementation owner
3. `QA_OWNER`: baseline replay and evidence owner
4. `DEVOPS_OWNER`: pipeline and branch protection owner
5. `PRODUCT_OWNER`: final signoff owner

Day 1 (Kickoff and freeze scope):
1. Lock Phase 0 scope to governance-only changes.
2. Freeze ad-hoc runtime behavior edits on active branches.
3. Publish short Phase 0 execution brief with owner assignments.
4. Open Phase 0 tracking ticket and acceptance checklist.

Day 2 (Baseline capture and replay lock):
1. Capture current first-run baseline from existing replay suites.
2. Record current engine mode and environment fingerprints.
3. Snapshot known failure ledger and classify by stage tag.
4. Mark baseline artifacts as immutable for Phase 0.

Day 3 (Contract-as-code rule definition):
1. Define banned runtime patterns for keyword-driven routing/scoring.
2. Define allowed lexical-alias boundary (`ontology_normalization` only).
3. Define import-boundary rules for resolver/planner/context modules.
4. Draft CI failure messages with actionable remediation text.

Day 4 (CI guardrail implementation):
1. Implement static checks for banned phrase-scoring maps in core runtime modules.
2. Implement dependency checks blocking forbidden imports.
3. Add mandatory check that actionable-turn tests emit audit envelope.
4. Wire checks into PR pipeline as blocking status checks.

Day 5 (Negative tests and proof of enforcement):
1. Run synthetic negative samples to prove CI blocks banned patterns.
2. Run positive samples to verify non-keyword modules remain unaffected.
3. Capture fail/pass logs and attach them to Phase 0 evidence.
4. Confirm no bypass path exists in branch protections.

Day 6 (Governance artifact finalization):
1. Publish approved allowed/forbidden runtime pattern document.
2. Publish Phase 0 baseline KPI snapshot and replay lock note.
3. Publish CI guardrail rule summary and ownership transfer note.
4. Prepare Phase 0 exit review package for signoff.

Day 7 (Exit review and handoff to Phase 1):
1. Run final checklist walkthrough against Phase 0 exit criteria.
2. Verify CI blocks contract violations on a controlled test PR.
3. Confirm baseline KPI artifact is versioned and immutable.
4. Record go/no-go decision for Phase 1 start.

Mandatory Phase 0 evidence bundle:
1. `phase0_governance_lock.md`
2. `phase0_baseline_kpi_snapshot.json`
3. `phase0_ci_guardrail_proof.md`
4. `phase0_exit_signoff.md`

Phase 0 exit gate checklist:
1. CI must fail on banned runtime patterns in protected modules.
2. CI must fail on forbidden cross-module keyword-routing imports.
3. Baseline KPI snapshot must be published and versioned.
4. Replay baseline must be locked and referenced by version ID.
5. Product and engineering signoff must be recorded.
