# EC-10-F Draft AI Assistant Doc V1

Decision target: `ec_10_f_draft_ai_assistant_doc_v1_ready_for_counterpart_qa_review`

## Draft Status

This is a draft source-of-truth document for AI Assistant V1. It consolidates accepted EC evidence into one readable V1 architecture and readiness narrative.

This draft is not production-release approval. It does not approve deployment, live trace collection, strict enforcement, V2 implementation, document moves, archive creation, packaging, staging, commit, or push.

## V1 Executive Summary

AI Assistant V1 is a governed ERP assistant backend with strong final-answer authority controls, centralized authorized assistant emission, runtime metadata/provenance coverage, and an observe/report-only strict-readiness soft gate.

The backend stabilization evidence is strong. However, V1 is not production-release ready until product-level release gates are closed:

- browser/manual UAT,
- ERP scenario validation,
- controlled-environment live trace evidence or an explicit owner risk decision,
- unsupported prediction/recommendation boundary validation,
- deployment and rollback readiness.

V2 work remains excluded from V1. This includes MI/family expansion, filter implementation, complex-question expansion, richer insight behavior, future UX/product expansion, and strict runtime enforcement.

## V1 Supported Scope

V1 supports governed backend/runtime AI Assistant behavior where final answers are emitted only through approved authority and emission paths.

Supported V1 capabilities:

| Capability | V1 status |
| --- | --- |
| Final-answer authority enforcement | Supported by EC evidence |
| Authorized assistant emission | Supported by EC evidence |
| Runtime metadata envelope | Supported by EC evidence |
| Deterministic/control metadata | Supported by EC evidence |
| AI/helper provenance metadata | Supported by EC evidence |
| Strict-readiness soft gate | Supported as observe/report only |
| Service containment canary | Supported for the approved tiny facade slice |
| Compatibility/legacy retention | Supported; no cleanup implementation required |

V1 does not yet claim:

| Claim | Status |
| --- | --- |
| Production release readiness | Pending |
| Browser/manual UAT completion | Pending |
| ERP scenario validation completion | Pending |
| Live trace evidence completion | Blocked/deferred |
| Deployment/rollback readiness | Pending |
| Strict enforcement | Not approved |
| V2 feature expansion | Out of scope |

## Runtime Architecture

The primary service entry point remains `handle_qwen_user_message` in `service.py`. The public API surface remains stable, with `api.py` importing `QWEN_SESSION_DOCTYPE` and `handle_qwen_user_message` from `ai_assistant_ui.qwen_chat.service`.

The runtime architecture is organized around active lanes and helper paths, including:

| Area | V1 treatment |
| --- | --- |
| Frontdoor semantic classification | AI semantic lane with light-semantic provenance |
| Fresh query interpretation | AI semantic lane with light-semantic provenance |
| Follow-up interpretation | AI semantic lane with light-semantic provenance |
| Business reasoning | Heavy reasoning provenance |
| NBU shadow observation | Shadow observer provenance, observe-only |
| Deterministic report/control paths | Explicit deterministic/control metadata |
| Policy boundary paths | Policy-boundary metadata and bounded preflight |
| Helper/tool runtime paths | Provenance-only helper metadata, not final-answer authority |
| Legacy runtime lane | Active runtime fallback retained for V1 |
| Root frontdoor facade | Compatibility facade retained for V1 |

Source evidence:

- `qwen_erp_ec_7b0_b_runtime_import_integrity_repair_2026-05-17.md`
- `qwen_erp_ec_7b_runtime_metadata_coverage_inventory_2026-05-17.md`
- `qwen_erp_ec_8_a_service_py_containment_baseline_2026-05-23.md`
- `qwen_erp_ec_8_b_public_service_surface_caller_audit_2026-05-23.md`
- `qwen_erp_ec_9_c_duplicate_legacy_cleanup_closure_2026-05-24.md`

## `service.py` Containment And Public API Surface

`service.py` remains the active service container for V1. EC-8 established a containment baseline and implemented only a tiny smoke/governance facade canary.

Stable V1 rules:

| Rule | Status |
| --- | --- |
| `handle_qwen_user_message` stays in `service.py` | Required |
| `QWEN_SESSION_DOCTYPE` remains stable | Required |
| `api.py` import path remains valid | Required |
| No broad `service.py` refactor | Required |
| Future facade work must be narrow and reviewed | Required |

Implemented EC-8 facade canary:

- `run_phase4_compiled_rollout_smoke`
- `run_phase4_compiled_rollout_governance_selftests`
- `run_phase4_compiled_rollout_monitoring_smoke`

Carry-forward limitation:

`ai_assistant_ui.qwen_chat.probes.service_diagnostics` remains missing/pre-existing, so EC-8 proved facade compatibility and mocked/sentinel delegation only. It did not prove unmocked smoke-wrapper execution.

Source evidence:

- `qwen_erp_ec_8_a_service_py_containment_baseline_2026-05-23.md`
- `qwen_erp_ec_8_b_public_service_surface_caller_audit_2026-05-23.md`
- `qwen_erp_ec_8_c_compatibility_facade_extraction_feasibility_plan_2026-05-23.md`
- `qwen_erp_ec_8_d_smoke_governance_facade_design_2026-05-23.md`
- `qwen_erp_ec_8_f_tiny_facade_implementation_2026-05-23.md`
- `qwen_erp_ec_8_i_staged_index_package_report_2026-05-23.md`

## Final-Answer Authority Model

V1 final answers require explicit authority. Helper metadata, model metadata, runtime provenance, and tool/runtime provenance cannot substitute for final-answer authority.

Core rules:

| Rule | V1 status |
| --- | --- |
| Business-facing factual answers require final-answer authority | Required |
| Missing authority blocks emission | Required |
| Blocked paths must not leak answer text | Required |
| Policy-boundary answers must remain distinguishable from business factual answers | Required |
| Helper/tool provenance cannot grant business authority | Required |
| Shadow observation cannot affect final-answer authority | Required |

Source evidence:

- `qwen_erp_ec_4_final_answer_emission_authority_closure_2026-05-16.md`
- `qwen_erp_ec_6d_b_staged_index_dependency_closure_2026-05-17.md`
- `qwen_erp_ec_6d_c2_clean_branch_rebuild_package_2026-05-17.md`
- `qwen_erp_ec_7f_f_runtime_metadata_probe_closure_2026-05-19.md`
- `qwen_erp_ec_7g_b_strict_readiness_soft_gate_dry_run_report_2026-05-19.md`

## Authorized Emission Contract

Assistant message emission is centralized through authorized helper paths. Direct assistant appends outside authorized sinks are release blockers.

Expected V1 inventory:

| Check | Expected |
| --- | --- |
| Active runtime direct assistant append count | `0` |
| Inventory count | `1` |
| Migrated authorized paths length | `27` |
| Raw assistant append scan | Only two authorized sinks in `authorized_emission.py` |

Expected raw sink lines at this baseline:

- `authorized_emission.py:271`
- `authorized_emission.py:327`

Source evidence:

- EC-4 final-answer authority closure
- EC-6 staged-index and clean-branch package corrections
- EC-7F probe closure
- EC-7G soft-gate raw append blocker behavior
- EC-8 and EC-9 post-merge verification records

## Runtime Metadata Envelope

V1 uses a canonical runtime metadata envelope for runtime provenance and release-readiness assessment.

Canonical fields include:

- `model_role`
- `model_name`
- `fallback_used`
- `fallback_reason`
- `role_compliance`
- `authority_source`
- `evidence_scope`
- `answer_mode`
- `preflight_status`
- `metadata_status`
- `strict_readiness_status`
- `lane_id`
- `lane_class`
- `metadata_source`
- `runtime_probe_required`

Key validation rules:

| Rule | V1 status |
| --- | --- |
| Role/lane compatibility is validated | Required |
| Missing metadata cannot become strict-ready | Required |
| Fallback/degraded/runtime-error metadata cannot become strict-ready | Required |
| Unknown metadata is allowed for inventory only, not strict-ready | Required |
| Helper/tool roles are provenance roles, not authority roles | Required |

Source evidence:

- `qwen_erp_ec_7c_runtime_metadata_envelope_contract_2026-05-18.md`
- EC-7E taxonomy and provenance work
- `qwen_erp_ec_7e_c2_c1_light_semantic_outcome_strict_readiness_guard_2026-05-19.md`
- `qwen_erp_ec_7f_f_runtime_metadata_probe_closure_2026-05-19.md`

## Deterministic / Control Metadata

Deterministic, policy, control, and error-fallback answer paths explicitly expose metadata and authority information.

Coverage includes:

| Lane/path | V1 metadata role |
| --- | --- |
| Runtime gate | Policy/control metadata |
| Clarification control | Control metadata |
| Compiled support result answer | Deterministic report metadata |
| Legacy runtime business/boundary answer | Deterministic/policy metadata |
| Artifact boundary | Deterministic/policy metadata |
| Local follow-up transform | Deterministic visible-context/report metadata |
| Entity follow-up | Deterministic/error metadata |
| Service policy/control responses | Policy/control metadata |
| NBU governed requery entity detail | Deterministic report metadata |
| NBU safe response activation | Control/shadow behavior documented |
| Visible-context follow-up and trace inspection | Deterministic visible-context metadata |

Deterministic/control lanes are covered, but they are not AI strict-ready lanes.

Source evidence:

- `qwen_erp_ec_7d_f_deterministic_control_metadata_closure_2026-05-18.md`
- `qwen_erp_ec_7f_f_runtime_metadata_probe_closure_2026-05-19.md`
- `qwen_erp_ec_7g_b_strict_readiness_soft_gate_dry_run_report_2026-05-19.md`

## AI / Helper Provenance

V1 AI and model-backed helper paths expose provenance metadata. This metadata supports observability and release-readiness assessment, but does not override final-answer authority.

Covered provenance areas:

| Area | V1 status |
| --- | --- |
| Light semantic classifiers | Covered by EC-7E/EC-7F |
| Heavy reasoning | Covered by EC-7E/EC-7F |
| NBU shadow observation | Covered as observe-only |
| Model-backed helpers | Covered as provenance-only |
| Governed-tool runtime helpers | Covered as provenance-only |

Strict-readiness rules:

| Metadata outcome | Strict-readiness result |
| --- | --- |
| Accepted complete AI metadata | May be strict-ready for provenance |
| Missing model metadata | Not strict-ready |
| Fallback/degraded metadata | Not strict-ready |
| Runtime-error metadata | Not strict-ready |
| Helper/tool metadata | Provenance-only; cannot grant final-answer authority |
| Shadow observer metadata | Observe-only |

Source evidence:

- EC-7E AI/helper metadata wiring and taxonomy reports
- `qwen_erp_ec_7e_c2_c1_light_semantic_outcome_strict_readiness_guard_2026-05-19.md`
- `qwen_erp_ec_7f_f_runtime_metadata_probe_closure_2026-05-19.md`
- `qwen_erp_ec_7g_c_soft_gate_evidence_source_classification_2026-05-20.md`

## Strict-Readiness Soft Gate

The V1 strict-readiness gate is observe/report-only.

It does not:

- block runtime,
- change routing,
- change model calls,
- change answer text,
- change report selection,
- grant final-answer authority,
- approve hard strict enforcement.

Soft-gate classifications:

| Classification | Meaning |
| --- | --- |
| `soft_gate_pass` | Metadata/provenance looks release-ready for the lane |
| `soft_gate_warn` | Metadata/provenance has warning conditions |
| `soft_gate_block_release` | Release readiness should block, but runtime is not blocked |
| `not_applicable_deterministic` | Deterministic lane is covered but not AI strict-ready |
| `not_applicable_control` | Control/policy/error lane is covered but not AI strict-ready |

Strict enforcement remains a future, separately approved decision.

Source evidence:

- `qwen_erp_ec_7g_a_strict_readiness_soft_gate_plan_2026-05-19.md`
- `qwen_erp_ec_7g_b_strict_readiness_soft_gate_dry_run_report_2026-05-19.md`
- `qwen_erp_ec_7g_c_soft_gate_evidence_source_classification_2026-05-20.md`

## Live Trace Protocol And Current Blocker

Live trace work is blocked/deferred because the controlled environment prerequisites do not exist yet.

Current state:

| Requirement | Status |
| --- | --- |
| Trace fixture/redaction protocol | Exists and hardened |
| Passive dataset validator | Exists and hardened |
| Passive archive readiness checker | Exists and hardened |
| Passive environment readiness checker | Exists and hardened |
| Controlled non-production bench/site | Missing |
| Dedicated QA test user | Missing |
| Synthetic dataset `EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001` | Missing |
| Secure raw trace archive | Missing |
| Raw trace custodian | Missing |
| Redacted live trace summaries | Not collected |

No live traces have been collected. Raw traces must remain outside the repo under QA/Owner custody. Redacted summaries or fixtures require owner/QA approval and EC-7H-B-D validation.

Source evidence:

- `qwen_erp_ec_7h_a_live_runtime_trace_evidence_plan_2026-05-20.md`
- `qwen_erp_ec_7h_b_trace_fixture_redaction_protocol_2026-05-20.md`
- `qwen_erp_ec_7h_c_c_light_semantic_live_trace_collection_preflight_2026-05-21.md`
- `qwen_erp_ec_7h_e_environment_readiness_verification_2026-05-21.md`
- `qwen_erp_ec_7i_a_controlled_environment_preparation_plan_2026-05-21.md`
- `qwen_erp_ec_7i_g_d_site_config_validation_fix_2026-05-22.md`

## Packaging / PR Evidence

Accepted package history:

| Package | Status |
| --- | --- |
| EC-6 AI Assistant stabilization package | Clean package merged and verified |
| EC-7 runtime metadata/provenance package | Merged and verified |
| EC-7H/EC-7I passive readiness package | Merged and verified |
| EC-8 service facade containment canary | Merged and verified |
| EC-9/EC-10 docs package | Not packaged yet |

EC-10-E proposes a compact future 8-report EC-9/EC-10 docs package. That proposal does not yet approve staging, commit, push, or archive movement.

Source evidence:

- EC-6 package reports
- EC-7P/EC-7J package reports
- EC-8-H/I package reports
- `qwen_erp_ec_10_e_docs_packaging_archive_proposal_2026-05-24.md`

## Compatibility And Legacy Retention

EC-9 closed with no cleanup implementation required for V1.

Current V1 retention rules:

| File/module | V1 treatment |
| --- | --- |
| Root `qwen_chat/frontdoor_lane.py` | Compatibility facade retained |
| Package `qwen_chat/lanes/frontdoor_lane.py` | Active runtime implementation retained |
| `qwen_chat/lanes/legacy_runtime_lane.py` | Active runtime fallback retained |
| Emission mapping modules | Governance/test evidence retained |

Future root frontdoor retirement would require a separate external/operator caller audit and owner approval.

Source evidence:

- `qwen_erp_ec_9_a_duplicate_legacy_cleanup_baseline_2026-05-23.md`
- `qwen_erp_ec_9_b_compatibility_retirement_deletion_feasibility_plan_2026-05-23.md`
- `qwen_erp_ec_9_c_duplicate_legacy_cleanup_closure_2026-05-24.md`

## Pending V1 Release Gates

V1 release is not approved until these gates are closed or explicitly risk-accepted by owner/QA.

| Gate | Current status | Closure requirement |
| --- | --- | --- |
| Browser/manual UAT | Pending | Accepted UAT report |
| ERP scenario validation | Pending | Accepted scenario matrix/results |
| Trace inspection | Blocked/deferred | Controlled environment and accepted live trace evidence, or owner risk decision |
| Unsupported prediction/recommendation boundaries | Pending | Accepted boundary validation checklist |
| Deployment readiness | Pending | Accepted deployment plan and checks |
| Rollback readiness | Pending | Accepted rollback plan and checks |
| Strict enforcement | Not approved | Separate future decision after evidence |

Source evidence:

- `qwen_erp_ec_10_c_v1_release_readiness_checklist_evidence_matrix_2026-05-24.md`

## Explicit V2 Exclusions

V2 work remains excluded from V1.

Not approved in V1:

- MI/family expansion,
- filter implementation,
- complex business question expansion,
- richer insight behavior,
- multi-step reasoning behavior changes,
- future UX/product expansion,
- strict runtime enforcement,
- deployment,
- live trace collection without controlled environment.

Source evidence:

- `qwen_erp_ec_10_d_v2_mi_filter_complex_question_roadmap_stub_2026-05-24.md`

## Release Decision Rules

| Condition | V1 decision |
| --- | --- |
| Backend EC evidence remains green, but UAT/ERP/deployment gates are missing | Not production-release ready |
| Direct assistant inventory regresses | Block release |
| Raw append scan shows non-authorized sink | Block release |
| Final-answer authority regression appears | Block release |
| Browser/manual UAT missing | Block product release approval |
| ERP scenario validation missing | Block product release approval |
| Deployment/rollback readiness missing | Block production launch |
| Live trace evidence missing | Block hard enforcement; release requires owner/QA risk decision |
| V2 scope requested before V1 gates | Defer to V2 roadmap, no implementation |

## Evidence Index

| Topic | Evidence source |
| --- | --- |
| Final-answer authority | EC-4, EC-6, EC-7F/G |
| Authorized emission | EC-4, EC-6, EC-7G, repeated verification |
| Metadata envelope | EC-7C |
| Deterministic/control metadata | EC-7D-F, EC-7F |
| AI/helper provenance | EC-7E, EC-7F |
| Soft gate | EC-7G-A/B/C |
| Live trace protocol/blocker | EC-7H, EC-7I |
| Service containment | EC-8 |
| Duplicate/legacy cleanup | EC-9 |
| Docs readiness | EC-10-A |
| Doc V1 outline | EC-10-B |
| Release checklist | EC-10-C |
| V2 roadmap stub | EC-10-D |
| Docs packaging proposal | EC-10-E |

## Draft Non-Approvals

This draft does not approve:

- production release,
- deployment,
- live trace collection,
- strict enforcement,
- V2 implementation,
- MI/filter/UX code changes,
- source/test edits,
- doc moves,
- archive directory creation,
- packaging execution,
- staging,
- commit,
- push.

## Recommended Next Steps

1. Counterpart/QA review this draft Doc V1.
2. If accepted, create an EC-10-G Doc V1 review correction slice only if reviewers find source-mapping or wording gaps.
3. After draft acceptance, request packaging approval for the EC-9/EC-10 docs package, likely including EC-10-F in addition to the EC-10-E 8-report boundary.
4. Keep V1 release execution separate from docs packaging.

## EC-10-F Decision

`ec_10_f_draft_ai_assistant_doc_v1_ready_for_counterpart_qa_review`
