# EC-10-B AI Assistant Doc V1 Source-of-Truth Outline / Consolidation Plan

Decision target: `ec_10_b_ai_assistant_doc_v1_outline_plan_ready_for_counterpart_qa_review`

## Scope

EC-10-B is a report-only proposal for the future **AI Assistant Doc V1**. It defines the recommended outline and maps each section to accepted EC evidence.

This is not the final Doc V1. It does not move documents, archive documents, approve V1 release, execute browser/manual UAT, run ERP scenario validation, approve deployment, or begin V2/MI/filter/complex-question expansion.

## Baseline

| Field | Value |
| --- | --- |
| Worktree | `/tmp/erpai_pr5_postmerge_verify` |
| Branch | `main` |
| HEAD | `46ed5ef` |
| EC-10-A status | Accepted as docs readiness baseline |
| Current EC-10-B action | New governance report only |
| Staged files before EC-10-B | `0` |
| Doc moves/archives | None |
| Runtime/source changes | None |

## Why Doc V1 Is Needed

The current EC documentation is strong as an audit trail, but it is intentionally granular. A V1 source-of-truth document should give owner, QA, operator, and developer reviewers one coherent view of:

- what the AI Assistant V1 supports,
- what runtime authority and metadata guarantees exist,
- what remains blocked or deferred,
- which evidence proves backend readiness,
- which release gates still require product validation.

Doc V1 should reference the EC reports as evidence rather than duplicating every micro-slice.

## Proposed AI Assistant Doc V1 Outline

| Section | Purpose | Primary EC evidence |
| --- | --- | --- |
| 1. V1 Purpose And Supported Scope | Define what V1 is allowed to do and what is intentionally out of scope | EC-10-A, EC-4, EC-7B, EC-9 |
| 2. Runtime Architecture | Explain active runtime lanes, service entry point, dependency integrity, and lane ownership | EC-7B0, EC-7B, EC-8-A, EC-8-B |
| 3. `service.py` Containment And Public API Surface | Document service API stability, public caller surface, and facade canary | EC-8-A through EC-8-I |
| 4. Final-Answer Authority Model | Define which paths may emit final answers and how authority is proven | EC-4, EC-6, EC-7F, EC-7G |
| 5. Authorized Emission Contract | Document centralized assistant emission sinks and direct append inventory | EC-4, EC-6D/EC-6D-B, EC-7F, EC-8/EC-9 verification |
| 6. Runtime Metadata Envelope | Define canonical metadata fields, roles, lane classes, and validation rules | EC-7C, EC-7E-C2-1 |
| 7. Deterministic / Control Metadata | Explain deterministic report/control/policy/error metadata expectations | EC-7D-F, EC-7F-E |
| 8. AI / Helper Provenance | Explain semantic, reasoning, shadow, model-backed helper, and governed-tool provenance | EC-7E, EC-7F-B/C/D |
| 9. Strict-Readiness Soft Gate | Explain observe/report-only gate, classifications, and release-readiness meaning | EC-7G-A, EC-7G-B, EC-7G-C |
| 10. Live Trace Protocol And Current Blocker | Define trace protocol, redaction, environment prerequisites, and current blocked status | EC-7H-A through EC-7H-E, EC-7I-A through EC-7I-G-D |
| 11. Packaging / PR Evidence | Map accepted commits/PRs and package boundaries that reached main | EC-6, EC-7P/EC-7J, EC-8-H/I, EC-10-A |
| 12. Compatibility And Legacy Retention | Document retained compatibility facades and active legacy runtime fallback | EC-8, EC-9 |
| 13. V1 Release Readiness Gates Still Pending | List gates not yet satisfied by backend evidence | EC-10-A plus future release readiness docs |
| 14. Explicit V2 Exclusions | Record deferred UX, Filter, MI, family expansion, complex-question, and strict enforcement decisions | EC-7G, EC-7H/7I, EC-8, EC-10-A |
| 15. Evidence Index | Provide report/file references for all source evidence | EC-4 through EC-10-A |

## Section Detail And Source Mapping

### 1. V1 Purpose And Supported Scope

Proposed content:

- AI Assistant V1 is a governed backend/runtime assistant for ERP-supported business responses.
- V1 authority is bounded by final-answer authority contracts and authorized-emission rules.
- V1 is not a production launch declaration by itself.
- V1 does not include UX expansion, Filter work, MI/family expansion, complex-question expansion, strict enforcement, or live trace completion.

Source reports:

| Source | Use |
| --- | --- |
| `qwen_erp_ec_10_a_v1_v2_docs_readiness_baseline_2026-05-24.md` | Defines docs readiness posture and missing V1/V2 docs |
| `qwen_erp_ec_4_final_answer_emission_authority_closure_2026-05-16.md` | Establishes final-answer authority safety boundary |
| `qwen_erp_ec_7b_runtime_metadata_coverage_inventory_2026-05-17.md` | Maps runtime lane coverage foundation |
| `qwen_erp_ec_9_c_duplicate_legacy_cleanup_closure_2026-05-24.md` | Records no-cleanup-required compatibility posture |

### 2. Runtime Architecture

Proposed content:

- Main service entry remains `handle_qwen_user_message`.
- Active runtime lanes and deterministic/control/AI/shadow lanes should be described at a conceptual level.
- Dependency integrity from EC-7B0 should be summarized.
- Runtime architecture should avoid exposing every historical EC micro-slice.

Source reports:

| Source | Use |
| --- | --- |
| `qwen_erp_ec_7b0_b_runtime_import_integrity_repair_2026-05-17.md` | Runtime import/dependency integrity baseline |
| `qwen_erp_ec_7b_runtime_metadata_coverage_inventory_2026-05-17.md` | Lane and metadata coverage inventory |
| `qwen_erp_ec_8_a_service_py_containment_baseline_2026-05-23.md` | `service.py` containment risk and shape |
| `qwen_erp_ec_8_b_public_service_surface_caller_audit_2026-05-23.md` | Public service surface and caller evidence |

### 3. `service.py` Containment And Public API Surface

Proposed content:

- `handle_qwen_user_message` remains in `service.py`.
- `QWEN_SESSION_DOCTYPE` remains stable.
- `api.py` import path remains valid.
- `service.py` contains a tiny smoke/governance facade canary, not a broad refactor.
- `service_diagnostics` remains missing/pre-existing, so unmocked smoke-wrapper execution is deferred.

Source reports:

| Source | Use |
| --- | --- |
| `qwen_erp_ec_8_a_service_py_containment_baseline_2026-05-23.md` | Baseline size/risk of service.py |
| `qwen_erp_ec_8_b_public_service_surface_caller_audit_2026-05-23.md` | Public API/caller surface |
| `qwen_erp_ec_8_c_compatibility_facade_extraction_feasibility_plan_2026-05-23.md` | Extraction feasibility |
| `qwen_erp_ec_8_d_smoke_governance_facade_design_2026-05-23.md` | Facade design |
| `qwen_erp_ec_8_f_tiny_facade_implementation_2026-05-23.md` | Implemented three-wrapper facade canary |
| `qwen_erp_ec_8_i_staged_index_package_report_2026-05-23.md` | Package proof |

### 4. Final-Answer Authority Model

Proposed content:

- Final-answer authority is required before business-facing factual answers are emitted.
- Helper/model provenance cannot substitute for final-answer authority.
- Policy boundary, deterministic report, control, and error fallback modes must remain distinguishable.
- Missing authority paths must not leak answer text.

Source reports:

| Source | Use |
| --- | --- |
| `qwen_erp_ec_4_final_answer_emission_authority_closure_2026-05-16.md` | Primary final-answer authority closure |
| `qwen_erp_ec_6d_b_staged_index_dependency_closure_2026-05-17.md` | Staged-index package correction around final-answer closure |
| `qwen_erp_ec_6d_c2_clean_branch_rebuild_package_2026-05-17.md` | Clean branch package proof |
| `qwen_erp_ec_7f_f_runtime_metadata_probe_closure_2026-05-19.md` | Metadata/provenance probes preserving authority separation |
| `qwen_erp_ec_7g_b_strict_readiness_soft_gate_dry_run_report_2026-05-19.md` | Soft-gate release-block behavior for authority failures |

### 5. Authorized Emission Contract

Proposed content:

- Assistant emission must remain centralized in `authorized_emission.py`.
- Direct assistant append inventory remains `0 / 1 / 27`.
- Raw assistant append scan is expected to show only the two authorized sinks.
- Any future direct append outside authorized sinks is a release blocker.

Source reports:

| Source | Use |
| --- | --- |
| `qwen_erp_ec_4_final_answer_emission_authority_closure_2026-05-16.md` | Emission authority foundation |
| `qwen_erp_ec_6d_b_staged_index_dependency_closure_2026-05-17.md` | Staged-index direct append correction |
| `qwen_erp_ec_7g_b_strict_readiness_soft_gate_dry_run_report_2026-05-19.md` | Raw append release-blocker behavior |
| EC-8/EC-9 post-merge verification evidence | Confirms no regression after service containment and cleanup closure |

### 6. Runtime Metadata Envelope

Proposed content:

- Define canonical fields: `model_role`, `model_name`, `fallback_used`, `fallback_reason`, `role_compliance`, `authority_source`, `evidence_scope`, `answer_mode`, `preflight_status`, `metadata_status`, `strict_readiness_status`, `lane_id`, `lane_class`, `metadata_source`, and `runtime_probe_required`.
- Explain role/lane compatibility.
- Explain why forged metadata is rejected.
- State that unknown/degraded/fallback metadata cannot become strict-ready.

Source reports:

| Source | Use |
| --- | --- |
| `qwen_erp_ec_7c_runtime_metadata_envelope_contract_2026-05-18.md` | Canonical contract and validation rules |
| EC-7E-C2-1 taxonomy extension evidence | Adds helper/tool runtime provenance roles |
| `qwen_erp_ec_7e_c2_c1_light_semantic_outcome_strict_readiness_guard_2026-05-19.md` | Guards degraded semantic outcomes |
| `qwen_erp_ec_7f_f_runtime_metadata_probe_closure_2026-05-19.md` | Runtime probe closure |

### 7. Deterministic / Control Metadata

Proposed content:

- Deterministic report/control/policy/error lanes must expose explicit metadata.
- These lanes are covered but not AI strict-ready.
- Policy boundaries use bounded preflight.
- Control/meta responses carry explicit control authority.

Source reports:

| Source | Use |
| --- | --- |
| `qwen_erp_ec_7d_f_deterministic_control_metadata_closure_2026-05-18.md` | Deterministic/control coverage closure |
| `qwen_erp_ec_7f_f_runtime_metadata_probe_closure_2026-05-19.md` | Probe evidence across deterministic/control paths |
| `qwen_erp_ec_7g_b_strict_readiness_soft_gate_dry_run_report_2026-05-19.md` | Soft-gate classification behavior |

### 8. AI / Helper Provenance

Proposed content:

- Light semantic lanes, heavy reasoning, NBU shadow, model-backed helpers, and governed-tool runtime helpers have metadata provenance.
- Accepted complete AI metadata may be strict-ready for provenance.
- Degraded/fallback/runtime-error/missing metadata cannot become strict-ready.
- Helper/tool provenance cannot grant business final-answer authority.
- NBU shadow remains observe-only.

Source reports:

| Source | Use |
| --- | --- |
| EC-7E-A through EC-7E-C2 reports | AI/helper provenance inventory, taxonomy, and wiring |
| `qwen_erp_ec_7e_c2_c1_light_semantic_outcome_strict_readiness_guard_2026-05-19.md` | Degraded semantic outcome guard |
| `qwen_erp_ec_7f_f_runtime_metadata_probe_closure_2026-05-19.md` | Runtime probe closure |
| `qwen_erp_ec_7g_c_soft_gate_evidence_source_classification_2026-05-20.md` | Evidence source classification |

### 9. Strict-Readiness Soft Gate, Observe/Report-Only

Proposed content:

- Soft gate means observe/report only.
- It does not block runtime, change routes, change model calls, change reports, or alter answer text.
- Classifications include `soft_gate_pass`, `soft_gate_warn`, `soft_gate_block_release`, `not_applicable_deterministic`, and `not_applicable_control`.
- Strict enforcement remains not approved.

Source reports:

| Source | Use |
| --- | --- |
| `qwen_erp_ec_7g_a_strict_readiness_soft_gate_plan_2026-05-19.md` | Soft-gate design |
| `qwen_erp_ec_7g_b_strict_readiness_soft_gate_dry_run_report_2026-05-19.md` | Report implementation and dry-run results |
| `qwen_erp_ec_7g_c_soft_gate_evidence_source_classification_2026-05-20.md` | Evidence-source readiness classification |

### 10. Live Trace Protocol And Current Blocker

Proposed content:

- Live trace evidence is required before hard enforcement or production readiness claims.
- No live trace collection has occurred.
- Raw traces must remain external/secure and unversioned.
- Redacted summaries/fixtures require EC-7H-B-D protocol validation.
- Collection is blocked/deferred because no controlled non-production bench/site, dedicated QA user, synthetic dataset, custodian, or archive is active.

Source reports:

| Source | Use |
| --- | --- |
| `qwen_erp_ec_7h_a_live_runtime_trace_evidence_plan_2026-05-20.md` | Live trace plan |
| `qwen_erp_ec_7h_b_trace_fixture_redaction_protocol_2026-05-20.md` | Redaction protocol |
| `qwen_erp_ec_7h_c_c_light_semantic_live_trace_collection_preflight_2026-05-21.md` | Correctly blocked preflight |
| `qwen_erp_ec_7h_e_environment_readiness_verification_2026-05-21.md` | Environment readiness blocked |
| `qwen_erp_ec_7i_a_controlled_environment_preparation_plan_2026-05-21.md` through `qwen_erp_ec_7i_g_d_site_config_validation_fix_2026-05-22.md` | Controlled-environment planning and passive harness hardening |

### 11. Packaging / PR Evidence

Proposed content:

- Accepted stabilization packages reached `main` through clean package PRs.
- Package boundaries excluded ERP UI, seed/data, temp/probe/cache, PrimeAxis docs, raw/redacted trace artifacts, generated scratch artifacts, and unapproved broad AI streams.
- EC-10 Doc V1 should include an evidence index with PR/commit mapping.

Source reports:

| Source | Use |
| --- | --- |
| EC-6 package reports | AI stabilization package and clean branch proof |
| EC-7P/EC-7J package reports | Runtime metadata and passive readiness package proof |
| EC-8-H/I package reports | Service facade canary package proof |
| EC-10-A | Docs readiness baseline and packaging guidance |

### 12. Compatibility And Legacy Retention

Proposed content:

- Root `qwen_chat/frontdoor_lane.py` remains a compatibility facade.
- Package `qwen_chat/lanes/frontdoor_lane.py` remains active runtime.
- `qwen_chat/lanes/legacy_runtime_lane.py` remains active runtime fallback.
- Emission mapping modules remain governance/test evidence.
- No cleanup implementation is required for V1.

Source reports:

| Source | Use |
| --- | --- |
| `qwen_erp_ec_9_a_duplicate_legacy_cleanup_baseline_2026-05-23.md` | Duplicate/legacy baseline |
| `qwen_erp_ec_9_b_compatibility_retirement_deletion_feasibility_plan_2026-05-23.md` | Retirement/deletion feasibility |
| `qwen_erp_ec_9_c_duplicate_legacy_cleanup_closure_2026-05-24.md` | No-implementation closure |

### 13. V1 Release Readiness Gates Still Pending

Proposed content:

- Backend evidence is strong, but V1 release is not approved.
- Browser/manual UAT remains pending.
- ERP scenario validation remains pending.
- Deployment/rollback readiness remains pending.
- Controlled-environment live trace evidence remains blocked/deferred.
- Unsupported prediction/recommendation boundaries still need release-gate validation.

Source reports:

| Source | Use |
| --- | --- |
| `qwen_erp_ec_10_a_v1_v2_docs_readiness_baseline_2026-05-24.md` | Missing V1 release docs and readiness gaps |
| EC-7H/EC-7I reports | Live trace/environment blockers |
| EC-7G reports | Soft-gate evidence, not hard enforcement |

### 14. Explicit V2 Exclusions

Proposed content:

- V2/MI/filter/complex-question work remains excluded from V1.
- Strict enforcement remains excluded until later decision.
- No UX expansion, family expansion, routing rewrite, or broad `service.py` refactor should be inferred from Doc V1.

Source reports:

| Source | Use |
| --- | --- |
| `qwen_erp_ec_10_a_v1_v2_docs_readiness_baseline_2026-05-24.md` | Missing V2 roadmap docs |
| EC-7G reports | Strict enforcement not approved |
| EC-8 reports | No broad service refactor |
| EC-9 reports | No cleanup implementation required for V1 |

### 15. Evidence Index

Proposed content:

- Provide a concise table of accepted EC source reports, commit/PR references, and verification status.
- Point to EC evidence without duplicating full report content.
- Separate backend readiness evidence from product/manual readiness evidence.

Source reports:

| Source | Use |
| --- | --- |
| EC-4 through EC-10-A accepted reports | Evidence index foundation |
| Future EC-10-C release checklist | Release-readiness matrix |

## Source Evidence Matrix

| Evidence family | Proposed Doc V1 usage |
| --- | --- |
| EC-4 authority closure | Final-answer authority and emission safety |
| EC-6 package closure | Stabilization package integrity and authority preservation |
| EC-7B0 import integrity | Runtime dependency/import baseline |
| EC-7B inventory | Runtime lane metadata coverage baseline |
| EC-7C contract | Canonical runtime metadata envelope |
| EC-7D deterministic/control closure | Deterministic/control metadata guarantees |
| EC-7E provenance/guard closure | AI/helper provenance and degraded-status safety |
| EC-7F probe closure | Backend runtime metadata/provenance validation |
| EC-7G soft gate | Observe/report-only release-readiness gate |
| EC-7H/EC-7I readiness | Live trace protocol and blocked controlled environment |
| EC-7P/EC-7J packaging | Runtime metadata/passive readiness package proof |
| EC-8 containment/facade | `service.py` containment and public API stability |
| EC-9 closure | Compatibility/legacy retention and no cleanup implementation |
| EC-10-A | Docs readiness baseline and missing V1/V2 docs |

## Explicit Non-Goals

Doc V1 must clearly state:

- It is not V1 release approval.
- It is not production deployment approval.
- It is not strict enforcement approval.
- It is not live trace completion.
- It is not browser/manual UAT completion.
- It is not ERP scenario validation completion.
- It is not V2/MI/filter/complex-question implementation approval.
- It does not approve doc moves, archives, source changes, staging, commit, or push.

## Pending V1 Release Gates

| Gate | Current status | Required future doc/evidence |
| --- | --- | --- |
| Browser/manual UAT | Pending | V1 manual/browser UAT plan and evidence report |
| ERP scenario validation | Pending | ERP scenario validation matrix and results |
| Live trace evidence | Blocked/deferred | Controlled environment, QA user, synthetic dataset, secure archive, redacted summaries |
| Deployment/rollback readiness | Pending | Deployment/rollback readiness plan |
| Unsupported prediction/recommendation boundaries | Pending | Boundary validation checklist |
| Strict enforcement | Not approved | Future EC-7H/live evidence and EC-7H/EC-7G decision record |

## Recommended Next EC-10 Sequence

| Slice | Purpose | Scope |
| --- | --- | --- |
| EC-10-C | V1 release readiness checklist and evidence matrix | Report-only |
| EC-10-D | V2/MI/filter/complex-question roadmap stub | Report-only |
| EC-10-E | Doc packaging/archive proposal | Proposal only; no moves unless later approved |
| EC-10-F | Draft AI Assistant Doc V1 | Draft doc only after outline and checklist acceptance |

## EC-10-B Decision

`ec_10_b_ai_assistant_doc_v1_outline_plan_ready_for_counterpart_qa_review`
