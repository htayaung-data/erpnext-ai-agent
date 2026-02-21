# AI Assistant Contract Specification (Commercial v7.1)

Version: 7.1  
Effective date: 2026-02-21  
System: ERPNext Desk Embedded Assistant (`ai_assistant_ui`)  
Primary data source: FAC tools (`frappe_assistant_core`)  
Supersedes: v7.0 (2026-02-21)

Note: file path keeps `v2` name for repository continuity; active contract version is `v7.1`.

## 1) Purpose
Define the enterprise production contract for an ERP assistant that is:
1. semantically correct on first-run business asks,
2. stable in 3-4 turn context chains,
3. safe for write operations,
4. auditable and releasable by deterministic gates.

## 2) Scope and Boundaries
1. `v7` is the only active runtime engine path.
2. Legacy `v2`/`v3` runtime paths are forbidden.
3. Read-path GA and write-path GA are separate release tracks.
4. Forecasting, policy Q&A, and broad open-domain RAG are deferred until read GA gates pass.

## 3) Non-Negotiable Principles
1. ERP/FAC outputs are the only business-fact source.
2. No fabrication of metrics, entities, dates, document IDs, or totals.
3. Runtime decisions are `spec + constraints + capability + state`, never keyword routing.
4. Clarification is blocker-only; no meta-planner clarification on clear asks.
5. Every actionable turn must be traceable through deterministic audit envelopes.
6. No promotion without first-run replay evidence.
7. No phase overlap without prior phase exit pass.
8. Any write without explicit confirm is Sev1 release blocker.

## 4) Explicitly Prohibited Patterns
1. Keyword/regex/phrase-list routing as primary resolver logic.
2. Report-name text matching as primary selection logic.
3. One-off runtime patches for single transcript outcomes without generalized stage-level fix.
4. Mixed read/write state machines.
5. Promotion based on rerun success when first-run fails.

## 5) Architecture Contract

### 5.1 Online Runtime Plane
1. `state_loader`: load `active_topic_id`, `active_result_id`, blocker state, active constraints.
2. `intent_parser`: LLM structured parse to `BusinessRequestSpec` only.
3. `constraint_builder`: deterministic hard constraints from spec + state + security scope.
4. `capability_retrieval`: feasible candidate retrieval from capability graph.
5. `candidate_ranker`: rank among feasible candidates only.
6. `execution_planner`: typed FAC plan (`tool`, `report`, `params`, retries, timeout, idempotency).
7. `fac_executor`: bounded execution with retry and timeout policy.
8. `result_validator`: deterministic semantic/output checks, authoritative verdict.
9. `clarification_engine`: one blocker question with reason code and dedupe key.
10. `response_composer`: natural-language rendering from validated facts only (fact-locked).
11. `state_writer`: persist topic/result/transform/breakpoint state.
12. `audit_writer`: persist `TurnAuditEnvelope` for every actionable turn.

### 5.2 Offline Control Plane
1. `benchmark_manager`: fixed replay manifests and golden datasets.
2. `ontology_registry`: canonical metric/dimension/filter/time/output contracts.
3. `capability_platform`: FAC + ERP schema/capability ingestion with confidence/freshness.
4. `retrieval_grounder`: top-k metadata retrieval with confidence thresholding.
5. `drift_monitor`: schema/capability drift and staleness alerts.
6. `kpi_gate_service`: first-run scoring and gate evaluation.
7. `version_registry`: model/prompt/capability versions + rollback pointer.

### 5.3 Security Plane
1. RBAC + row-level and field-level policy at tool boundary.
2. PII redaction for logs and responses where required.
3. Isolated write engine with `draft -> confirm -> execute -> audit`.
4. Permission failure must return explicit envelope, never fallback data leakage.

## 6) Contract-As-Code Guardrails
1. Lexical alias dictionaries are allowed only in `ontology_normalization`.
2. Resolver/planner/context/validator modules must not define inline lexical maps.
3. CI must fail on banned legacy imports (`v2`, `v3`, old report_qa monolith path).
4. CI must fail if mandatory audit envelope fields are absent.
5. CI must fail when mandatory replay/KPI gates fail.

## 7) Mandatory Data Contracts

### 7.1 BusinessRequestSpec
Required fields:
1. `intent`
2. `task_type`
3. `domain`
4. `metric`
5. `dimensions[]`
6. `filters{}`
7. `time_scope{}`
8. `output_contract{}`
9. `confidence`

### 7.2 ConstraintSet
Required fields:
1. `polarity_constraints`
2. `required_filters`
3. `entity_constraints`
4. `followup_bindings`
5. `security_scope`

### 7.3 CapabilityCandidateSet
Required fields:
1. `candidates[]`
2. `feasible_only=true`
3. `reject_reasons[]`

### 7.4 ExecutionPlan
Required fields:
1. `tool`
2. `report_name`
3. `params`
4. `retries`
5. `timeout_ms`
6. `idempotency_key`

### 7.5 ValidationResult
Required fields:
1. `verdict` (`PASS|REPAIRABLE_FAIL|HARD_FAIL`)
2. `check_ids_failed[]`
3. `check_details[]`
4. `repair_hint`

### 7.6 ClarificationEnvelope
Required fields:
1. `reason_code`
2. `question`
3. `expected_answer_type`
4. `options[]`
5. `dedupe_key`

### 7.7 ResponseEnvelope
Required fields:
1. `type`
2. `text` or `table`
3. `factual_lock_hash`

### 7.8 TurnAuditEnvelope
Required fields:
1. `trace_id`
2. `engine_version`
3. `model_version`
4. `prompt_version`
5. `capability_version`
6. `selected_candidate`
7. `execution_plan`
8. `validation_result`
9. `latency_ms`
10. `final_response_hash`

## 8) Runtime Behavior Contract
1. Parser may retry invalid JSON once only.
2. Constraint builder is deterministic and mandatory before resolver.
3. Resolver cannot select outside feasible capability set.
4. Planner must produce typed call plan before execution.
5. `REPAIRABLE_FAIL` allows one bounded repair path.
6. `HARD_FAIL` returns blocker clarification or explicit envelope (`unsupported`, `no_data`, `permission`).
7. Composer cannot alter factual values returned by validated payload.

## 9) Context and Follow-Up Contract
1. Persist and enforce `active_topic_id`, `active_result_id`, `active_filter_context`.
2. Follow-up references (`that`, `those`, `same`, `previous`) bind to persisted prior result context.
3. Correction turns (`I mean`, `not X use Y`) mutate relevant constraints only.
4. Cross-topic contamination is hard failure.
5. Transforms operate on persisted prior result; no silent report switch.

## 10) Clarification and Error Envelope Contract
1. Clarify only for true blockers:
- missing required filter not safely inferable
- ambiguous entity resolution
- no matching entity
- unsupported hard constraint
2. Ask exactly one clarification question per blocker cycle.
3. Do not repeat same blocker question after answer (dedupe key required).
4. `unsupported`, `no_data`, `permission` responses must be explicit envelopes.
5. Greeting/capability asks must return concise capability summary, not blocker clarification.

## 11) Output Contract
1. Numeric format default: thousand separators + exactly 2 decimals.
2. Million transform must preserve numeric correctness.
3. Output mode must match request contract (`kpi`, `top_n`, `detail`, `comparison`, `trend`).
4. Minimal relevant columns by default unless user requests full detail.

## 12) Security and Write Contract
1. Write execution disabled until write-gate phase enabled.
2. No write without explicit confirmation.
3. Confirmation must echo target and intended mutation.
4. Idempotency key required for write execute.
5. Any unconfirmed write is immediate rollback trigger.

## 13) Observability Contract
Each actionable turn must persist:
1. parsed spec and constraints,
2. candidate set + selected candidate reason,
3. execution plan and executor summary,
4. validation verdict and failed check IDs,
5. clarification reason code (if any),
6. response envelope type,
7. topic/result linkage,
8. latency/retry counts,
9. security policy outcomes.

## 14) KPI Gates (Non-Negotiable)
Promotion allowed only when all pass:
1. wrong-report rate <= 5% (first-run, `n >= 300`)
2. follow-up accuracy: 3-turn >= 95%, 4-turn >= 90% (`>= 150` chains)
3. unnecessary clarification rate <= 5%
4. clarification loop rate < 1%
5. first-run mandatory-suite pass >= 90%
6. output-shape pass rate = 100% on mandatory set
7. unsupported/no-data/permission envelope correctness >= 98%
8. write safety violations = 0
9. P95 latency within class-specific SLA

## 15) Rollout Contract (Read/Write Split)
1. Read rollout track: `shadow -> 10% -> 25% -> 50% -> 100%`.
2. Write rollout track starts only after read GA is stable and signed.
3. Write rollout repeats separate `shadow -> canary -> GA` with stricter safety gates.
4. Each stage requires rollback rehearsal evidence.

## 16) Stop and Rollback Rules
1. Immediate rollback on any write safety violation.
2. Stop canary when wrong-report gate breaches by >20% relative margin.
3. Stop canary when clarification loop breaches threshold for two consecutive windows.
4. Promotion blocked if audit envelope completeness <100% on actionable turns.
5. Promotion blocked if critical capability drift is unresolved.

## 17) Phase Evidence Contract
Every phase must publish:
1. entry checklist completion,
2. changed module list,
3. deterministic test and replay results,
4. KPI deltas vs baseline,
5. known risk and mitigation,
6. rollback verification note,
7. formal exit signoff.

## 18) Change Control
1. Contract and roadmap versions must move together.
2. Any gate change requires version bump and changelog.
3. Runtime logic merge requires linked replay/KPI evidence.
4. No emergency bypass of guardrails without written incident record.

## 19) Acceptance Criteria (Commercial v7.1)
Commercial-ready means:
1. clear business asks are correct on first run,
2. 3-4 turn follow-up chains are context-correct and contamination-free,
3. clarifications are blocker-only and non-repetitive,
4. unsupported/no-data/permission behavior is explicit and correct,
5. output shape and numeric formatting are contract-compliant,
6. write path is safe, permission-correct, and fully audited,
7. all KPI gates pass with versioned evidence.

## 20) Changelog
1. `v7.1` (2026-02-21): added read/write split rollout contract, explicit sample-size KPI gates, per-phase evidence contract, and version-registry requirement.
2. `v7.0` (2026-02-21): enterprise architecture contract with runtime/control/security planes and deterministic gate policy.
