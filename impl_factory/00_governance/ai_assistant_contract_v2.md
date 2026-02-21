# AI Assistant Contract Specification (Commercial v7.0)

Version: 7.0  
Effective date: 2026-02-21  
System: ERPNext Desk Embedded Assistant (`ai_assistant_ui`)  
Primary data source: FAC tools (`frappe_assistant_core`)  
Supersedes: v3.1 (2026-02-21)

Note: file path keeps `v2` name for repository continuity; active contract version is `v7.0`.

## 1) Purpose
Define the production contract for an enterprise ERP Assistant that is correct on broad business asks, stable in multi-turn chains, safe for write operations, and auditable for commercial operations.

## 2) Scope and Boundaries
1. Build and release `v7` in parallel with existing engines.
2. Legacy `v2` and `v3` engines are removed from active runtime and source path.
3. Read path reliability is delivered before write path activation.
4. Forecasting, policy Q&A, and broad RAG chat are out of scope until read-path KPI gates pass.

## 3) Non-Negotiable Principles
1. ERP/FAC outputs are the only source of business facts.
2. No hallucination of numeric values, entities, dates, or document details.
3. Runtime core decisions are schema + constraints + capability graph + state; not phrase scoring.
4. Clarification is blocker-only; never meta-planner questioning on clear asks.
5. One-turn correctness is required for clear executable asks.
6. Multi-turn continuity is first-class: 3-4 turn chains must remain semantically anchored.
7. Read and write paths are isolated state machines.
8. No release without deterministic replay evidence and first-run KPI gates.

## 4) Explicitly Prohibited Patterns
1. Keyword/regex/phrase-list routing as core resolver logic.
2. Report-name text matching as primary route decision.
3. Runtime one-off patches for single transcript cases without stage-level root cause.
4. Mixed read/write orchestration trees.
5. Shipping on rerun success when first-run failed.

## 5) Architecture Contract (V7)

### 5.1 Online Runtime Plane
1. `state_loader`: load `active_topic_id`, `active_result_id`, `active_constraints`, unresolved blocker state.
2. `intent_parser`: LLM structured parse to `BusinessRequestSpec` only.
3. `constraints_builder`: deterministic hard-constraint construction.
4. `capability_resolver`: metadata-feasible candidate retrieval from capability graph.
5. `candidate_ranker`: select among feasible candidates only.
6. `execution_planner`: build typed FAC execution plan.
7. `fac_executor`: execute with retries/timeouts/idempotency.
8. `result_validator`: deterministic semantic and shape checks.
9. `clarification_engine`: one blocker question with reason code and dedupe.
10. `response_composer`: natural response from validated facts only (fact-locked).
11. `state_writer`: persist canonical turn state and transform anchors.
12. `audit_writer`: persist `TurnAuditEnvelope` per actionable turn.

### 5.2 Offline Control Plane
1. `capability_ingestion_job`: sync FAC/ERP metadata to capability graph.
2. `ontology_normalization`: canonical business terms and lexical aliases.
3. `drift_monitor`: schema and capability freshness/drift detection.
4. `replay_suite_manager`: deterministic core/multi-turn/transform/no-data/unsupported/write-safety suites.
5. `kpi_gate_service`: first-run scoring and promotion blocking.
6. `prompt_model_registry`: version pinning and rollback pointer.

### 5.3 Security Plane
1. RBAC, row-level policy, and field-level masking at tool boundary.
2. PII redaction in logs and user-visible responses where required.
3. Isolated write state machine: `draft -> confirm -> execute -> audit`.
4. Any write without explicit confirm is a hard-stop incident.

## 6) Contract-As-Code Guardrails
1. Only `ontology_normalization` may contain lexical alias dictionaries.
2. Resolver/planner/context/validator modules must not import banned keyword routing maps.
3. CI must fail if runtime core modules define phrase-scored routing tables.
4. Every actionable turn must emit `TurnAuditEnvelope`; CI/integration tests fail if absent.
5. Release pipeline must fail when mandatory replay/KPI gates fail.

## 7) Mandatory V7 Data Contracts

### 7.1 BusinessRequestSpec
Minimum fields:
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
Minimum fields:
1. `polarity_constraints`
2. `required_filters`
3. `entity_constraints`
4. `followup_bindings`
5. `security_scope`

### 7.3 CapabilityCandidateSet
Minimum fields:
1. `candidates[]`
2. `feasible_only=true`
3. `reject_reasons[]`

### 7.4 ExecutionPlan
Minimum fields:
1. `tool`
2. `report_name`
3. `params`
4. `retries`
5. `timeout_ms`
6. `idempotency_key`

### 7.5 ValidationResult
Minimum fields:
1. `verdict` (`PASS|REPAIRABLE_FAIL|HARD_FAIL`)
2. `check_ids_failed[]`
3. `check_details[]`
4. `repair_hint`

### 7.6 ClarificationEnvelope
Minimum fields:
1. `reason_code`
2. `question`
3. `expected_answer_type`
4. `options[]`
5. `dedupe_key`

### 7.7 ResponseEnvelope
Minimum fields:
1. `type`
2. `text` or `table`
3. `factual_lock_hash`

### 7.8 TurnAuditEnvelope
Minimum fields:
1. `trace_id`
2. `engine_version`
3. `model_version`
4. `prompt_version`
5. `selected_candidate`
6. `execution_plan`
7. `validation_result`
8. `latency_ms`
9. `final_response_hash`

## 8) Runtime Flow Contract
1. Parser returns strict JSON schema output; invalid schema may retry once only.
2. Constraint builder merges current spec + persisted state + security scope.
3. Resolver may choose only capability-feasible candidates.
4. Planner must produce typed FAC call plan; bounded retry/timeout applies.
5. Validator is deterministic and authoritative for semantic correctness.
6. `REPAIRABLE_FAIL` allows one bounded repair path only.
7. `HARD_FAIL` produces blocker clarification or explicit envelope (`unsupported`, `no_data`, `permission`).
8. Composer may improve language only; cannot change factual values or totals.

## 9) Context and Multi-Turn Contract
1. Persist and enforce `active_topic_id`, `active_result_id`, and `active_filter_context`.
2. Follow-up references (`that`, `those`, `same`, `previous`) must bind to persisted prior result context.
3. Correction phrases (`I mean`, `not X use Y`) must mutate constraints, not reset unrelated context.
4. Cross-topic contamination is a hard failure.
5. Transforms run only on persisted prior result, never by silent report switch.

## 10) Clarification and Error Envelope Contract
1. Clarify only for true blockers:
   - missing required filter not safely inferable
   - ambiguous entity resolution
   - no matching entity
   - unsupported hard constraint
2. Ask exactly one clarification question per blocker cycle.
3. Do not repeat the same blocker question once user answered; use dedupe key memory.
4. For unsupported/no-data/permission, return explicit envelope and no unrelated fallback report output.
5. Greeting or capability questions must return concise capability summary, not blocker clarification.

## 11) Output Contract
1. Default numeric format: thousands separators + exactly 2 decimals.
2. Million conversion must preserve numeric correctness and 2-decimal display.
3. Output shape must match user request contract (`kpi`, `top_n`, `detail`, `comparison`, `trend`).
4. Return minimal relevant columns unless user explicitly asks for full detail.

## 12) Write Safety Contract
1. Write features disabled by default until write phase gates pass.
2. No write execution without explicit user confirmation.
3. Confirmation must echo target doctype/document and key mutations.
4. Idempotency key required for execution.
5. Write safety violation (`execute` without confirm) is release-blocking Sev1.

## 13) Observability and Traceability Contract
Every actionable turn must persist:
1. parsed spec and constraints
2. feasible candidates and selected candidate reasons
3. execution plan and tool summary
4. validation verdict + failed check IDs
5. clarification reason code (if any)
6. response envelope type
7. topic/result linkage
8. latencies and retry counts
9. security policy decisions (mask/filter)

## 14) Non-Negotiable KPI Gates
Promotion permitted only when all pass:
1. wrong-report rate <= 5% (first-run, sample >= 300)
2. follow-up accuracy: 3-turn >= 95%, 4-turn >= 90% (sample >= 150 chains)
3. unnecessary clarification rate <= 5%
4. clarification loop rate < 1%
5. first-run mandatory-suite pass >= 90%
6. output-shape pass rate = 100% on mandatory suite
7. unsupported/no-data/permission envelope correctness >= 98%
8. write safety violations = 0
9. P95 latency within class-specific SLA

## 15) Canary Stop and Rollback Rules
1. Immediate rollback on any write safety violation.
2. Stop stage when wrong-report rate breaches gate by >20% relative margin.
3. Stop stage when clarification loop breaches threshold in two consecutive windows.
4. Rollback rehearsal is mandatory at each canary stage.
5. Promotion requires signed go/no-go evidence.

## 16) Change Control
1. Contract changes require version bump, changelog, and linked test-plan update.
2. Roadmap and contract must change together when gating policy changes.
3. No merge for runtime logic changes without replay and KPI evidence links.

## 17) Acceptance Criteria (Commercial V7)
Commercial-ready means:
1. clear business asks return semantically correct results on first run.
2. 3-4 turn follow-up chains remain context-correct and contamination-free.
3. clarifications are blocker-only and non-repetitive.
4. unsupported and no-data behavior is explicit, polite, and correct.
5. output shape and numeric formatting consistently match contract.
6. write path is safe, permission-correct, and fully audited.
7. all KPI gates pass with versioned evidence.

## 18) Changelog
1. `v7.0` (2026-02-21): enterprise architecture contract (runtime/control/security planes), contract-as-code guardrails, mandatory V7 data contracts, deterministic gate policy, stop/rollback criteria.
2. `v3.1` (2026-02-21): reliability-first reset with stage tagging and clarification envelope hardening.
3. `v3.0` (2026-02-19): major reset for parallel v3 engine and stricter release criteria.
