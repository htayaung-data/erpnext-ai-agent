# AI Assistant Roadmap 2026 (V7.3 Enterprise Delivery Program)

Version: 7.3  
Effective date: 2026-02-22  
Program window: 2026-02-23 to 2026-07-26 (22 weeks)  
Primary codebase: `ai_assistant_ui`  
Engine policy: `v7` only (legacy runtime engines forbidden)

## 1) Program Objective
Deliver an enterprise-grade ERP AI Assistant that is:
1. correct on first-run business asks,
2. robust in 3-4 turn follow-up chains,
3. deterministic under quality gates,
4. safe and auditable for write operations.

## 2) Delivery Rules (Hard Constraints)
1. Contract-bound implementation only (`ai_assistant_contract_v2.md` v7.3).
2. No keyword-driven runtime routing/scoring logic.
3. No phase overlap without prior phase exit pass.
4. Promotion is first-run only; rerun pass does not override first-run fail.
5. Read GA and write GA are separate release tracks.
6. Acceptance is by behavior-class coverage and class-level KPIs, not by fixed question list only.
7. Any detected core-runtime contract breach triggers immediate breach-recovery mode and feature freeze.
8. Phase advancement is blocked while breach register count is non-zero.

## 3) Workstream Model
1. Runtime Plane: parser, constraints, resolver, planner, executor, validator, context, clarification, composer.
2. Control Plane: benchmark/scoring, ontology contracts, capability ingestion, retrieval grounding, drift monitor, version registry.
3. Security Plane: RBAC, row/field masking, write FSM, audit, PII policy.
4. QA/Ops Plane: replay suites, KPI gates, shadow/champion-challenger, canary, rollback drills.

## 4) Phase Plan (P0 to P10b)

### Phase P0 (Week 1) - Governance Lock
Entry:
1. current system runnable

Work:
1. enforce CI guardrails for banned runtime patterns
2. freeze baseline manifest and scoring path
3. block legacy engine/runtime imports
4. enforce alias-boundary rule (`ontology_normalization` only)

Exit:
1. guardrails hard-fail contract violations
2. baseline locked and immutable for scoring

Evidence:
1. guardrail run logs
2. baseline freeze artifact and checksum

Rollback:
1. not applicable (governance phase)

### Phase P0b (Week 1.5) - Contract Breach Hardening Sprint
Entry:
1. P0 pass
2. breach report exists or contract-drift suspected

Work:
1. publish breach register with file/line evidence
2. remove lexical/regex steering logic from core runtime modules
3. move allowed lexical mappings to ontology boundary only
4. strengthen CI guardrails for recurrence prevention
5. run first-run replay/canary and publish delta

Exit:
1. breach register count = 0
2. CI guardrails fail on recurrence patterns
3. mandatory replay/canary first-run pass meets minimum gate

Evidence:
1. breach register before/after report
2. guardrail execution logs
3. first-run replay/canary artifacts

Rollback:
1. if breach count remains non-zero after 5 working days, stop promotion and trigger go/no-go decision

### Phase P1 (Week 2) - Benchmark and First-Run Scoring Foundation
Entry:
1. P0 and P0b pass

Work:
1. finalize replay packs: `core_read`, `multiturn_context`, `transform_followup`, `no_data_unsupported`, `write_safety`
2. implement deterministic first-run scorer
3. publish baseline KPI report
4. define mandatory behavior-class baseline labels for each replay case

Exit:
1. reproducible baseline KPI pack available
2. scorer reproducibility verified
3. every replay case linked to one behavior class

Evidence:
1. replay manifest and case inventory
2. baseline JSON/MD KPI output
3. behavior-class mapping artifact

Rollback:
1. keep runtime in non-promoting mode

### Phase P2 (Weeks 3-4) - Ontology, Data Contracts, and Behavior Taxonomy
Entry:
1. P1 pass

Work:
1. finalize canonical contracts for metric/dimension/filter/time/output
2. finalize clarification reason-code taxonomy
3. version and validate schema contracts
4. formalize behavior-class taxonomy and task-class schema fields
5. define mandatory task classes: `ranking_top_n`, `kpi_aggregate`, `detail_projection`, `comparison`, `trend_time_series`, `list_latest_records`, `entity_disambiguation_followup`, `correction_rebind`, `transform_last_result`

Exit:
1. contract schema versioned and validated
2. parser and validator consume contract definitions from one source
3. behavior-class definitions published and consumed by scorer

Evidence:
1. contract schema docs + validation report
2. contract version tag and compatibility notes
3. behavior-class contract and mapping report

Rollback:
1. revert contract version pointer

### Phase P3 (Weeks 5-6) - Capability and Schema Platform
Entry:
1. P2 pass

Work:
1. ingest FAC report metadata and ERP schema metadata
2. persist capability confidence/freshness
3. implement drift/staleness alerts
4. publish capability coverage report
5. auto-enrich capability semantics (entity, projection support, default date/sort field, limit support)
6. support minimal manual override file for business/locale synonyms only

Exit:
1. active report-family coverage >= 95%
2. stale/unknown capability alerts active
3. enrichment coverage report published for mandatory task classes

Evidence:
1. coverage report
2. drift monitor test output
3. capability enrichment validation report

Rollback:
1. revert to prior capability snapshot

### Phase P4 (Weeks 7-8) - Retrieval Grounding Layer
Entry:
1. P3 pass

Work:
1. implement top-k retrieval for relevant capability/schema context
2. apply confidence thresholds and miss handling
3. log retrieval evidence per turn
4. include behavior-class and enriched-capability context in retrieval payload

Exit:
1. retrieval relevance KPI passes target
2. no full-schema prompt stuffing path in runtime
3. retrieval hit-rate for mandatory behavior classes meets target

Evidence:
1. retrieval evaluation report (`Top-1`, `Top-3`, misses)
2. trace samples with retrieval context
3. class-wise retrieval scorecard

Rollback:
1. disable retrieval-grounding and fallback to deterministic capability filtering

### Phase P5 (Weeks 9-10) - Parser and Constraint Engine Integration
Entry:
1. P4 pass

Work:
1. strict parser with max 1 retry
2. deterministic constraints for polarity/entity/time/filter requirements
3. convert required-filter misses to blocker clarifications
4. implement task-class parse semantics for missing classes:
- `list_latest_records` (`latest/recent/newest/last N` => sort+limit, not KPI metric)
- `detail_projection` (`show only X columns`)
5. add explicit ambiguity policy for `invoice` entity (`Sales Invoice` vs `Purchase Invoice`)

Exit:
1. parser schema-valid rate >= 99%
2. mandatory-filter runtime errors eliminated
3. mandatory task classes parse correctly in class replay suite

Evidence:
1. parser validity metrics
2. blocker-conversion report
3. task-class parse conformance report

Rollback:
1. revert parser prompt/model/contract version pointer

### Phase P6 (Weeks 11-12) - Resolver, Planner, Executor Refactor
Entry:
1. P5 pass

Work:
1. resolver chooses only feasible candidates
2. typed planner with bounded retries/timeouts/idempotency
3. deterministic executor and confusion-pair hardening
4. planner support for `list_latest_records` with deterministic sort+limit plan template
5. projection-only planner path for minimal column output without report drift

Exit:
1. wrong-report rate improves >= 40% vs baseline
2. confusion-pair suite pass >= 95%
3. latest-list and projection behavior classes pass planner/executor tests

Evidence:
1. confusion-pair scorecard
2. planner/executor contract tests
3. latest-list/projection class test report

Rollback:
1. feature-flag fallback to prior stable resolver/planner

### Phase P7 (Weeks 13-14) - Context and Transform Memory Hardening
Entry:
1. P6 pass

Work:
1. enforce `active_topic_id`, `active_result_id`, `active_filter_context`
2. robust follow-up reference binding (`that`, `those`, `same`, `previous`)
3. correction handling (`I mean`, `not X use Y`)
4. transform idempotency on persisted prior result

Exit:
1. 3-turn accuracy >= 95%
2. 4-turn accuracy >= 90%
3. contamination rate < 5%

Evidence:
1. multi-turn replay scorecards
2. transform idempotency test report

Rollback:
1. disable new context binder and revert to prior stable state-merging strategy

### Phase P8 (Weeks 15-16) - Validator, Clarification, Composer
Entry:
1. P7 pass

Work:
1. deterministic semantic validator with check IDs
2. blocker-only dynamic clarification with dedupe memory
3. fact-locked response composer
4. enforce output contract and number formatting globally
5. enforce class-aware clarification templates (single blocker question, no generic loop fallbacks on clear asks)

Exit:
1. unnecessary clarification <= 5%
2. clarification loop < 1%
3. output-shape pass = 100% on mandatory set
4. class-level clarification pass rate meets threshold on mandatory classes

Evidence:
1. clarification policy report
2. validator check-ID report
3. composer factual-lock tests
4. class-level clarification scorecard

Rollback:
1. bypass composer and return validated deterministic response mode

### Phase P9 (Weeks 17-18) - Security and Write Isolation
Entry:
1. read path gates passed

Work:
1. isolate write FSM (`draft -> confirm -> execute -> audit`)
2. enforce RBAC + row/field masking
3. enforce PII redaction policies
4. execute write safety and permission suites

Exit:
1. write safety violations = 0
2. permission suite pass = 100%

Evidence:
1. write safety report
2. permission test report
3. audit trace samples

Rollback:
1. write engine disabled, read-only mode enforced

### Phase P10a (Weeks 19-20) - Read Path Shadow, Canary, GA
Entry:
1. P8 pass and read-path stability confirmed

Work:
1. run shadow/champion-challenger evaluation
2. canary rollout read path: `10% -> 25% -> 50% -> 100%`
3. monitor KPI gates at each stage
4. perform rollback rehearsal at each stage

Exit:
1. all read KPI gates pass at all stages with required sample sizes
2. read path GA approved

Evidence:
1. stage KPI packs
2. rollback rehearsal records
3. go/no-go approvals

Rollback:
1. automatic fallback to prior stable read runtime on gate breach

### Phase P10b (Weeks 21-22) - Write Path Shadow, Canary, GA
Entry:
1. P9 pass and P10a read GA complete

Work:
1. write-path shadow evaluation
2. write canary rollout with stricter safety thresholds
3. perform rollback rehearsal per stage

Exit:
1. write safety violations remain 0 throughout rollout
2. write path GA approved

Evidence:
1. write canary KPI/safety packs
2. write rollback drill logs
3. final operational signoff

Rollback:
1. immediate write shutdown and read-only fallback

## 5) KPI Gates (Non-Negotiable)
1. wrong-report rate <= 5% (first-run, `n >= 300`)
2. follow-up accuracy: 3-turn >= 95%, 4-turn >= 90% (`>= 150` chains)
3. unnecessary clarification <= 5%
4. clarification loop rate < 1%
5. first-run mandatory-suite pass >= 90%
6. output-shape pass = 100% on mandatory suite
7. unsupported/no-data/permission envelope correctness >= 98%
8. write safety violations = 0
9. P95 latency within SLA by query class
10. behavior-class mandatory coverage >= 95%
11. behavior-class first-run pass rate >= 90% for each mandatory class

## 6) Canary Stop Rules
1. stop stage if wrong-report rate breaches threshold by >20% relative margin
2. stop stage if clarification loop breaches threshold for two consecutive windows
3. stop immediately on any write safety violation
4. block promotion if audit envelope completeness <100%
5. block promotion if critical capability drift is unresolved

## 7) Minimum Artifact Pack (Required Every Phase)
1. changed module list
2. deterministic test and replay outputs
3. KPI delta vs baseline
4. known risks and mitigations
5. rollback verification note
6. phase exit signoff

## 8) Manual QA Checkpoints
1. end P6: wrong-report and confusion-pair validation
2. end P7: 3-4 turn context chains and correction turns
3. end P8: clarification quality and response shape/formatting
4. end P10a: read-path business acceptance
5. end P10b: write-path safety acceptance

## 9) Deferred Scope (Post-GA)
1. forecasting/predictive models
2. policy Q&A and broad enterprise RAG assistant mode
3. open-domain chat extensions

## 10) Governance Notes
1. contract and roadmap versions must change together
2. gate changes require explicit version bump and changelog
3. no merge for runtime logic without replay and KPI evidence links
4. no phase promotion while breach-recovery mode is active

## 11) Current Program Status
1. P0 guardrail foundation exists and is active.
2. P1 replay baseline artifacts exist and are usable.
3. Program now proceeds under v7.3 phase model, with P0b breach-hardening mandatory before next phase promotion.

## 12) Changelog
1. `v7.3` (2026-02-22): added P0b breach-hardening sprint, breach freeze/kill-gate rules, and explicit phase block while contract breaches exist.
2. `v7.2` (2026-02-22): behavior-class coverage and class-level KPI acceptance model.
