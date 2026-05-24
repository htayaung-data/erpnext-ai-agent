# EC-10-A V1/V2 Docs Readiness Baseline

Decision target: `ec_10_a_v1_v2_docs_readiness_baseline_ready_for_counterpart_qa_review`

## Scope

EC-10-A is an investigation/report-only baseline for V1/V2 documentation readiness after EC-4 through EC-9 cleanup and stabilization work.

This report does not move, archive, stage, commit, push, deploy, or execute release work. It maps the current documentation estate into V1 source-of-truth candidates, release evidence, operational governance, EC audit trail, V2 roadmap candidates, stale/superseded retained evidence, and review-required gaps.

## Baseline State

| Field | Value |
| --- | --- |
| Worktree | `/tmp/erpai_pr5_postmerge_verify` |
| Branch | `main` |
| HEAD | `46ed5ef` |
| Current docs files scanned | `64` |
| Generated evidence files scanned | `16` |
| Staged files before report | `0` |
| Dirty files before EC-10-A | EC-9-A, EC-9-B, EC-9-C reports only |
| Runtime/source edits in EC-10-A | None |
| Doc moves/archives in EC-10-A | None |

## Current Documentation Shape

The current documentation set is primarily an EC cleanup and packaging audit trail. It is strong as governance evidence, but it is not yet a consolidated V1 product/readiness documentation set.

The accepted EC trail provides high-quality evidence for:

| Area | Current evidence |
| --- | --- |
| Final-answer authority | EC-4 and EC-6 acceptance reports |
| AI Assistant package stabilization | EC-5/EC-6 package dry-run, staged-index, and clean-branch reports |
| Runtime metadata/provenance | EC-7B through EC-7G reports and probes |
| Live trace readiness | EC-7H/EC-7I passive readiness reports and harness package |
| Service containment | EC-8 service containment and facade canary reports |
| Duplicate/legacy cleanup | EC-9 baseline/feasibility/closure reports |

The current documentation set is missing a concise V1 source-of-truth layer that product, QA, owner, and deployment reviewers can read without replaying every EC micro-slice.

## EC-4 Through EC-9 Accepted Closure Mapping

| Slice range | Current state | Documentation role |
| --- | --- | --- |
| EC-4 | Final-answer emission authority closure accepted and carried forward | V1 architecture/source-of-truth candidate; EC cleanup audit trail |
| EC-5 | Release packaging/worktree control baseline and dry-run manifest evidence retained | V1 release gate evidence; stale/superseded retained where later EC-6/EC-7 package work replaced details |
| EC-6 | AI Assistant stabilization package cleaned, staged, committed, merged, and verified through clean branch | V1 release gate evidence; EC cleanup audit trail |
| EC-7B0 | Runtime import integrity repaired and accepted | V1 architecture/source-of-truth candidate; V1 operational governance |
| EC-7B | Runtime metadata coverage inventory accepted | V1 architecture/source-of-truth candidate |
| EC-7C | Runtime metadata envelope contract accepted | V1 architecture/source-of-truth candidate |
| EC-7D | Deterministic/control metadata coverage closed | V1 architecture/source-of-truth candidate; release evidence |
| EC-7E | AI/helper metadata provenance and guards closed | V1 architecture/source-of-truth candidate; release evidence |
| EC-7F | Runtime metadata/provenance probes closed | V1 release gate evidence |
| EC-7G | Strict-readiness soft-gate plan/report/evidence classification accepted | V1 operational governance; V1 release readiness candidate |
| EC-7H | Live runtime trace plan/protocols created, but collection blocked/deferred | V1 operational governance; pending release evidence |
| EC-7I | Passive environment readiness harnesses merged; controlled environment still missing | V1 operational governance; pending release evidence |
| EC-8 | Service containment baseline, facade feasibility, and tiny facade canary merged | V1 architecture/source-of-truth candidate; EC cleanup audit trail |
| EC-9 | Duplicate/legacy cleanup closed with no implementation required | V1 operational governance; EC cleanup audit trail |

## Classification Summary

| Classification | Current documents | Readiness result |
| --- | --- | --- |
| V1 architecture/source-of-truth | EC-4 closure, EC-7B/7C/7D/7E, EC-8 containment/facade, EC-9 closure | Available as EC evidence, but needs consolidated AI Assistant Doc V1 |
| V1 release gate evidence | EC-5/EC-6/EC-7P/EC-7J packaging, EC-7F probes, EC-8 package proof | Strong backend evidence exists; real product validation still pending |
| V1 operational governance | EC-7G soft gate, EC-7H/7I live trace readiness, EC-8/EC-9 guardrails | Good operational baseline; live environment blocker remains |
| EC cleanup audit trail | EC-4 through EC-9 reports | Complete enough to retain; not user-facing V1 docs |
| V2 roadmap candidate | Deferred UX, Filter, MI, family expansion, complex-question planning | Missing dedicated V2 roadmap docs |
| Stale/superseded but retained | Earlier EC-5/EC-6 dry-runs and rejected/partial packaging paths | Retain as audit trail, not current release source-of-truth |
| Unknown/review-required | Any non-current docs outside this scanned current_docs set | Requires owner review before archiving or deleting |

## V1 Architecture / Source-Of-Truth Candidates

These should inform the future AI Assistant Doc V1. They should not be copied blindly; they should be distilled into a coherent architecture and authority narrative.

| Candidate | Why it matters | V1 treatment |
| --- | --- | --- |
| `qwen_erp_ec_4_final_answer_emission_authority_closure_2026-05-16.md` | Establishes final-answer authority and emission closure | Convert into final-answer authority section |
| `qwen_erp_ec_7b0_b_runtime_import_integrity_repair_2026-05-17.md` | Documents service import integrity repair and restored dependencies | Convert into runtime import/dependency baseline section |
| `qwen_erp_ec_7b_runtime_metadata_coverage_inventory_2026-05-17.md` | Maps runtime metadata coverage before wiring | Retain as inventory evidence; summarize in V1 |
| `qwen_erp_ec_7c_runtime_metadata_envelope_contract_2026-05-18.md` | Defines canonical runtime metadata envelope | Promote to V1 metadata contract source |
| `qwen_erp_ec_7d_f_deterministic_control_metadata_closure_2026-05-18.md` | Closes deterministic/control metadata coverage | Promote to V1 deterministic/control metadata section |
| `qwen_erp_ec_7e_c2_c1_light_semantic_outcome_strict_readiness_guard_2026-05-19.md` | Ensures degraded semantic outcomes cannot become strict-ready | Promote to V1 AI provenance safety section |
| `qwen_erp_ec_7f_f_runtime_metadata_probe_closure_2026-05-19.md` | Closes backend metadata/provenance probe evidence | Promote as backend readiness evidence, not production UAT |
| `qwen_erp_ec_7g_a_strict_readiness_soft_gate_plan_2026-05-19.md` | Defines observe/report-only soft gate | Promote to release-readiness governance section |
| `qwen_erp_ec_7g_b_strict_readiness_soft_gate_dry_run_report_2026-05-19.md` | Implements soft-gate dry-run evidence shape | Promote to release-readiness evidence section |
| `qwen_erp_ec_7g_c_soft_gate_evidence_source_classification_2026-05-20.md` | Classifies evidence source quality | Promote to evidence-quality section |
| `qwen_erp_ec_8_a_service_py_containment_baseline_2026-05-23.md` | Captures service.py containment risk | Promote to service containment section |
| `qwen_erp_ec_8_b_public_service_surface_caller_audit_2026-05-23.md` | Captures public service surface/caller audit | Promote to public API stability section |
| `qwen_erp_ec_8_f_tiny_facade_implementation_2026-05-23.md` | Documents the merged facade canary | Promote to containment implementation note |
| `qwen_erp_ec_9_c_duplicate_legacy_cleanup_closure_2026-05-24.md` | Closes duplicate/legacy cleanup with no deletion | Promote to compatibility/legacy retention note |

## V1 Release Gate Evidence

These documents support readiness review, but they do not by themselves approve production release.

| Evidence area | Documents | Current readiness |
| --- | --- | --- |
| Stabilization packaging | EC-5, EC-6, EC-7P, EC-7J package reports | Backend/package evidence exists |
| Runtime metadata probes | EC-7F closure | Backend metadata/provenance evidence exists |
| Soft readiness | EC-7G A/B/C | Dry-run/observe-only evidence exists; no strict enforcement approved |
| Live trace protocol | EC-7H B through C-C | Protocol exists; collection blocked/deferred |
| Environment readiness | EC-7I A through G-D | Passive harnesses exist; no real controlled environment exists |
| Service containment canary | EC-8 H/I and PR #6 verification | Tiny facade canary merged and verified |
| Duplicate cleanup | EC-9 closure | No implementation needed for V1 |

## V1 Operational Governance

These should remain current operational governance until replaced by consolidated release docs.

| Governance topic | Current source |
| --- | --- |
| Final-answer authority and direct assistant append policy | EC-4, EC-6, EC-7F/G evidence |
| Runtime metadata envelope and strict-readiness soft gate | EC-7C through EC-7G |
| Live trace redaction and fixture safety | EC-7H-B through EC-7H-B-D |
| Controlled environment prerequisites | EC-7H-C through EC-7I-G-D |
| Packaging discipline | EC-6, EC-7P, EC-7J, EC-8 H/I |
| service.py containment guardrail | EC-8 A through I |
| Legacy/compatibility retention | EC-9 A through C |

## EC Cleanup Audit Trail

The EC reports are valuable as detailed audit history, but they are too granular to serve as V1 operator-facing docs. They should be retained as audit trail and referenced from a smaller V1 doc index.

Recommended treatment:

| EC range | Retention treatment |
| --- | --- |
| EC-4 | Retain; promote final-answer authority summary into V1 |
| EC-5 | Retain as early packaging trail; mark superseded by later accepted package evidence where applicable |
| EC-6 | Retain as accepted AI stabilization package history |
| EC-7B through EC-7G | Retain and promote selected contract/probe/soft-gate content into V1 |
| EC-7H/EC-7I | Retain as live-trace readiness and environment blocker evidence |
| EC-7P/EC-7J | Retain as packaging evidence |
| EC-8 | Retain and promote service containment/facade canary content into V1 |
| EC-9 | Retain as no-cleanup-required closure |

## Stale / Superseded But Retained

Some documents describe rejected, partial, or replaced packaging approaches. They should not drive future staging decisions unless the later accepted closure explicitly points back to them.

Examples:

| Document family | Reason retained | Current use |
| --- | --- | --- |
| EC-5 early package dry-run and mixed hunk audit | Documents earlier packaging discipline and risks | Audit trail only |
| EC-6 intermediate package proposals before final staged/clean package | Documents boundary evolution and blockers | Audit trail; use final accepted EC-6 closure for current baseline |
| EC-7P intermediate dirty-path/package proposals | Documents package discipline before accepted EC-7 package | Audit trail; use final staged package reports for current baseline |
| EC-7H-C collection preflight | Correctly blocked due missing environment | Evidence of owner boundary compliance |
| EC-7I setup architecture/planning blockers | Correctly blocked setup execution until environment is real | Evidence of safe live-trace deferral |

## V2 Roadmap Candidates

The current docs repeatedly defer UX, Filter, MI, family expansion, strict enforcement, and complex-question expansion. Those deferrals are good boundaries, but they are not a V2 roadmap.

Missing V2 planning documents:

| Missing doc | Purpose |
| --- | --- |
| V2 roadmap and scope boundary | Define what is explicitly post-V1 |
| MI/family expansion plan | Define model-intelligence/family expansion goals and gates |
| Filter/query planning roadmap | Define filter support, query decomposition, and report-selection future work |
| Complex/multi-intent question strategy | Define unsupported/partial support and future design |
| V2 strict enforcement decision record | Decide when or whether EC-7G soft gate becomes hard enforcement |
| V2 live validation and observability plan | Define live trace/UAT expansion after controlled environment exists |

## Required Status Callouts

### EC-7H Live Trace Status

EC-7H live trace collection is blocked/deferred because no controlled non-production environment exists. EC-7H/EC-7I produced redaction protocol, collection protocol, environment setup plans, and passive readiness harnesses, but no live traces were collected and no raw/redacted trace artifacts are present in the repo.

### EC-8 Status

EC-8 closed for the approved scope. The tiny `service.py` facade canary was merged and verified. The missing optional `ai_assistant_ui.qwen_chat.probes.service_diagnostics` dependency remains a carry-forward limitation, so unmocked smoke-wrapper execution coverage is still deferred.

### EC-9 Status

EC-9 closed with no cleanup implementation required for V1. Root `qwen_chat/frontdoor_lane.py` remains a compatibility facade, package `qwen_chat/lanes/frontdoor_lane.py` remains active runtime, and `qwen_chat/lanes/legacy_runtime_lane.py` remains active runtime fallback.

### V1 Readiness Gate Status

V1 release readiness is not complete. Backend authority, metadata, packaging, and containment evidence is strong, but real product validation is still pending:

| Pending V1 gate | Status |
| --- | --- |
| Browser/manual UAT | Pending |
| ERP scenario validation | Pending |
| Controlled-environment live trace evidence | Blocked/deferred |
| Unsupported prediction/recommendation boundary validation | Pending |
| Deployment/rollback readiness | Pending |
| Product/operator release checklist | Missing |

## Missing V1 Documentation

| Missing V1 doc | Why needed |
| --- | --- |
| AI Assistant Doc V1 architecture/source-of-truth | Consolidates EC authority, metadata, runtime, service, and legacy decisions |
| V1 release readiness checklist | Turns EC evidence into release gate decisions |
| V1 manual/browser UAT plan and evidence template | Captures product validation outside backend unit/probe tests |
| ERP scenario validation matrix | Defines core ERP scenarios, supported answers, and boundary cases |
| Live trace evidence results report | Cannot be completed until controlled environment exists |
| Deployment and rollback readiness plan | Required before production launch |
| Unsupported prediction/recommendation boundary policy | Required for user-facing V1 safety expectations |
| Release package index | Maps accepted PRs/commits/reports to release evidence |

## Docs That Should Become AI Assistant Doc V1

Recommended V1 document sections:

| V1 section | Source material |
| --- | --- |
| Purpose and supported scope | EC-4, EC-7B, EC-9 closure, future UAT docs |
| Runtime architecture | EC-7B0, EC-7B, EC-8 baseline |
| Final-answer authority | EC-4, EC-6, authorized-emission evidence |
| Runtime metadata envelope | EC-7C |
| Deterministic/control metadata | EC-7D-F |
| AI/helper provenance | EC-7E-C2-C1 and EC-7F-F |
| Strict-readiness soft gate | EC-7G A/B/C |
| Live trace protocol and blocker | EC-7H/EC-7I |
| service.py containment | EC-8 A through I |
| Compatibility/legacy retention | EC-9 C |
| V1 release gates | Future EC-10 release gate checklist |

## Docs That Should Remain Operational Governance

| Governance doc family | Keep current because |
| --- | --- |
| EC-7G soft-gate docs | They define observe/report-only release readiness behavior |
| EC-7H redaction/protocol docs | They protect future live trace collection |
| EC-7I passive harness docs | They define safe environment readiness checks |
| EC-7P/EC-7J package docs | They prove packaging discipline and exclusions |
| EC-8 staging/package docs | They prove `service.py` hunk discipline and facade canary boundary |
| EC-9 closure | It prevents accidental deletion of compatibility/runtime fallback files |

## Docs That Should Move To V2 Planning

No files should be moved during EC-10-A. Future V2 docs should be created separately rather than moving EC audit reports.

Recommended V2 planning targets:

| Future V2 doc | Initial source |
| --- | --- |
| V2 roadmap and phase plan | Deferrals captured across EC-7/EC-8/EC-9 |
| MI/family expansion scope | Explicitly forbidden scope from EC-6 through EC-9 |
| Filter/query planning | Deferred filter work from roadmap notes |
| Complex-question strategy | Deferred complex/multi-intent handling |
| Hard enforcement decision record | EC-7G soft gate evidence and future EC-7H live trace results |

## Packaging / Archive Guidance

EC-10-A does not approve packaging. For future EC-10 packaging:

| Candidate | Treatment |
| --- | --- |
| EC-10-A report | Full-file governance candidate after review |
| EC-9 reports | Already dirty/untracked; package only after explicit boundary approval |
| V1/V2 consolidated docs | Future EC-10-B+ outputs, not present yet |
| Existing EC reports | Do not move/archive without a separate owner-approved archive plan |
| Generated evidence JSON | Do not include unless explicitly approved |
| Raw/redacted traces | Must remain absent from repo unless a future approved redacted summary is created |

## Risks

| Risk | Mitigation |
| --- | --- |
| Treating EC audit trail as product-ready docs | Create consolidated V1 architecture and release-gate docs |
| Premature V1 release claim | Keep V1 gate pending real product validation |
| Live trace pressure without environment | Keep EC-7H blocked until controlled environment exists |
| Accidental V2 scope creep | Separate V2/MI/filter/complex-question roadmap from V1 release docs |
| Accidental archive/move churn | Require separate EC-10 archive plan and owner approval |

## Recommended Next Sequence

1. EC-10-B: AI Assistant Doc V1 source-of-truth outline and consolidation plan, report-only.
2. EC-10-C: V1 release readiness checklist and evidence matrix, report-only.
3. EC-10-D: V2/MI/filter/complex-question roadmap stub, report-only.
4. EC-10-E: Docs packaging/archive proposal, if owner wants to package EC-9/EC-10 docs.

No deployment, V1 release execution, V2 implementation, doc move/archive, staging, commit, or push should occur before separate owner approval.

## EC-10-A Decision

`ec_10_a_v1_v2_docs_readiness_baseline_ready_for_counterpart_qa_review`
