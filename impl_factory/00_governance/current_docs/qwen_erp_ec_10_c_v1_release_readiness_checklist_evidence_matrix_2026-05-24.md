# EC-10-C V1 Release Readiness Checklist And Evidence Matrix

Decision target: `ec_10_c_v1_release_readiness_checklist_evidence_matrix_ready_for_counterpart_qa_review`

## Scope

EC-10-C is a report-only release-readiness checklist and evidence matrix for AI Assistant V1. It maps each V1 readiness gate to current evidence, missing evidence, owner, and required closure gate.

This report does not approve V1 release. It does not move or archive documents, package changes, stage, commit, push, deploy, collect live traces, enable strict enforcement, or start V2/MI/filter/complex-question implementation.

## Baseline

| Field | Value |
| --- | --- |
| Worktree | `/tmp/erpai_pr5_postmerge_verify` |
| Branch | `main` |
| HEAD | `46ed5ef` |
| EC-10-A | Accepted docs readiness baseline |
| EC-10-B | QA-accepted AI Assistant Doc V1 outline/consolidation plan |
| EC-10-C action | New governance report only |
| V1 release approval | Not approved |
| V2/MI/filter/complex-question expansion | Out of scope |

## Readiness Classification

| Classification | Meaning |
| --- | --- |
| `ec_supported` | Current EC evidence supports this gate for backend/governance review |
| `partially_supported` | EC evidence exists, but product/release evidence is incomplete |
| `missing_release_evidence` | Required V1 release evidence has not been produced |
| `blocked_external_input` | Gate is blocked by missing environment, owner/QA input, or external setup |
| `not_applicable_v1` | Gate is explicitly outside V1 |
| `not_approved` | Work is not approved for V1 release |

## Executive Readiness Summary

| Area | Current status | Release impact |
| --- | --- | --- |
| Backend final-answer authority | `ec_supported` | Strong EC evidence exists |
| Authorized emission contract | `ec_supported` | Strong EC evidence exists |
| Runtime metadata/provenance | `ec_supported` | Strong backend evidence exists |
| Strict-readiness soft gate | `ec_supported` as observe/report only | Does not approve strict enforcement |
| Browser/manual UAT | `missing_release_evidence` | Blocks V1 release |
| ERP scenario validation | `missing_release_evidence` | Blocks V1 release |
| Live trace evidence | `blocked_external_input` | Blocks hard-enforcement consideration and weakens release readiness |
| Deployment/rollback readiness | `missing_release_evidence` | Blocks production launch |
| Unsupported prediction/recommendation boundary validation | `missing_release_evidence` | Blocks V1 product safety signoff |
| V2/MI/filter/complex-question expansion | `not_applicable_v1` | Must remain out of scope |

## V1 Release Readiness Checklist

| Gate | Current evidence | Missing evidence | Owner | Required closure gate | Status |
| --- | --- | --- | --- | --- | --- |
| Final-answer authority model | EC-4 authority closure; EC-6 package corrections; EC-7F/G authority separation probes | None for backend gate; product UAT still needed for user-facing confidence | Development + QA_Risk | Authority/emission regression remains green in release candidate | `ec_supported` |
| Authorized emission contract | Direct assistant inventory repeatedly verified as `0 / 1 / 27`; raw scan limited to `authorized_emission.py` sinks | None for backend gate | Development + QA_Risk | Release candidate inventory and raw scan remain clean | `ec_supported` |
| Runtime metadata envelope | EC-7C contract; EC-7D/E wiring; EC-7F probes | None for backend metadata gate | Development + QA_Risk | EC-7 metadata/probe tests remain green | `ec_supported` |
| Strict-readiness soft gate | EC-7G-A/B/C observe/report-only design and dry-run report | Hard enforcement evidence and approval are missing by design | Owner + QA_Risk | Separate future strict-enforcement decision after live trace evidence | `ec_supported` as observe/report only |
| Browser/manual UAT | No accepted V1 browser/manual UAT evidence | Browser interaction scripts or manual QA evidence; screenshots/logs; pass/fail summary | QA + Owner | V1 browser/manual UAT report accepted | `missing_release_evidence` |
| ERP scenario validation | Backend probes exist, but no accepted ERP scenario matrix/results | Named ERP scenarios, expected outputs, actual results, boundary cases | QA + Owner + Development | ERP scenario validation matrix accepted | `missing_release_evidence` |
| Trace inspection | EC-7H/7I protocol and passive harnesses exist | Controlled environment, QA user, synthetic dataset, secure archive, collected redacted summaries | QA/Owner custodian + Development | EC-7H live trace evidence accepted | `blocked_external_input` |
| Unsupported prediction/recommendation boundaries | Authority and policy boundary evidence exists | Product-level validation for unsupported predictions/recommendations | QA + Owner | Boundary validation checklist accepted | `missing_release_evidence` |
| Deployment readiness | No production deployment approval; no deployment gate evidence in EC-10 | Deployment plan, environment target, smoke checks, owner approval | Owner + DevOps/Development | Deployment readiness report accepted | `missing_release_evidence` |
| Rollback readiness | No rollback evidence in EC-10 | Rollback procedure, restore point, verification steps | Owner + DevOps/Development | Rollback readiness report accepted | `missing_release_evidence` |
| Packaging integrity | EC-6, EC-7P/J, EC-8 package/PR evidence | Future EC-10 docs packaging boundary if these reports are committed | Development + Counterpart + QA_Risk | EC-10 packaging gate accepted before commit | `partially_supported` |
| Compatibility/legacy retention | EC-9 closed with no cleanup implementation | None for V1; future retirement would require external caller audit | Owner + Development | No deletion/import movement before separate approval | `ec_supported` |
| `service.py` containment | EC-8 containment baseline and facade canary merged | Unmocked smoke-wrapper execution remains deferred because `service_diagnostics` is missing | Development + QA_Risk | Keep EC-8 limitation documented; no broad refactor | `partially_supported` |
| Live environment readiness | EC-7I passive harnesses exist and prevent false readiness | Actual controlled bench/site, QA user, dataset, archive, custodian | Owner + QA | EC-7H/EC-7I environment readiness verified | `blocked_external_input` |
| V2/MI/filter/complex-question work | Explicitly deferred across EC reports | Dedicated V2 roadmap doc only, not implementation | Owner + Product/Development | EC-10-D roadmap stub, if approved | `not_applicable_v1` |

## Evidence Matrix By Source

| Evidence source | Supports | Does not prove |
| --- | --- | --- |
| EC-4 authority closure | Final-answer authority, authorized emission safety | Browser UAT, ERP product correctness, deployment readiness |
| EC-6 stabilization package | Clean package boundary, authority preservation, staged-index discipline | Current product release approval |
| EC-7B0 runtime import repair | Runtime importability and dependency integrity | Live environment readiness |
| EC-7C metadata contract | Canonical metadata envelope and validation rules | Runtime live trace evidence |
| EC-7D deterministic/control closure | Deterministic/control metadata coverage | Browser/manual UAT |
| EC-7E AI/helper provenance | AI/helper metadata provenance and degraded outcome safety | Product scenario correctness |
| EC-7F probe closure | Backend runtime metadata/provenance probe coverage | Production/live ERP behavior |
| EC-7G soft gate | Observe/report-only release readiness classification | Hard runtime enforcement approval |
| EC-7H live trace protocol | Redaction, fixture protocol, collection plan | Actual live trace evidence |
| EC-7I passive readiness harnesses | Safe environment readiness checks | Existence of controlled environment |
| EC-8 service containment | Public API audit and tiny facade canary | Broad service refactor or unmocked smoke-wrapper execution |
| EC-9 cleanup closure | No deletion needed for V1; compatibility retained | Future root facade retirement |
| EC-10-A docs baseline | V1/V2 docs readiness map | Final Doc V1 |
| EC-10-B Doc V1 outline | Proposed consolidated source-of-truth structure | Release approval or finished Doc V1 |

## Browser / Manual UAT Gate

| Item | Required evidence | Current status |
| --- | --- | --- |
| Browser entry into AI Assistant | Manual/browser steps and pass/fail evidence | Missing |
| Session continuity | Multi-turn validation evidence | Missing |
| Visible context correctness | Manual validation of visible context in UI | Missing |
| Final answer display behavior | Evidence that backend authority maps to expected UI output | Missing |
| Failure/boundary presentation | UI behavior for unsupported/bounded answers | Missing |

Closure gate: create and accept a V1 browser/manual UAT report. This must be separate from backend unit/probe evidence.

## ERP Scenario Validation Gate

| Scenario class | Required evidence | Current status |
| --- | --- | --- |
| Governed ERP report answer | Named synthetic or QA-approved ERP scenario with expected result | Missing |
| Entity/detail follow-up | Named scenario and expected behavior | Missing |
| Follow-up interpretation | Named multi-turn scenario | Missing |
| Policy boundary/refusal | Unsupported/bounded scenario evidence | Missing |
| Error/fallback behavior | Controlled failure scenario and expected safe output | Missing |

Closure gate: create and accept an ERP scenario validation matrix with scenario IDs, prompts, expected behavior, actual behavior, evidence source, and pass/fail decision.

## Trace Inspection Gate

| Item | Current status |
| --- | --- |
| Live trace protocol | Exists |
| Redaction protocol | Exists and hardened |
| Passive environment harnesses | Exist and hardened |
| Controlled non-production bench/site | Missing |
| Dedicated QA test user | Missing |
| Synthetic dataset `EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001` | Missing |
| Secure external raw archive | Missing |
| Raw trace custodian | Missing |
| Redacted live trace summaries | Not collected |

Closure gate: EC-7H live trace evidence can resume only after EC-7I environment readiness is verified. Until then, trace inspection remains blocked/deferred.

## Unsupported Prediction / Recommendation Boundary Gate

| Boundary | Required evidence | Current status |
| --- | --- | --- |
| Unsupported prediction requests | Product-level expected refusal/boundary behavior | Missing |
| Unsupported recommendation requests | Product-level expected refusal/boundary behavior | Missing |
| Speculative financial/business advice | Boundary decision and UI/backend evidence | Missing |
| Out-of-scope model assertions | Boundary examples and pass/fail evidence | Missing |

Closure gate: V1 boundary validation checklist accepted by QA/Owner.

## Deployment / Rollback Readiness Gate

| Gate | Required evidence | Current status |
| --- | --- | --- |
| Deployment target | Named environment and release package | Missing |
| Deployment procedure | Exact commands or runbook | Missing |
| Pre-deploy checks | Guardrail, imports, inventories, UAT prerequisites | Missing |
| Post-deploy checks | Smoke/UAT/rollback verification | Missing |
| Rollback plan | Exact rollback commands and owner approval | Missing |
| Secrets/environment handling | No secrets in repo; safe environment handling | Missing |

Closure gate: deployment/rollback readiness report accepted before production launch.

## Strict Enforcement Status

Strict enforcement remains not approved.

| Item | Status |
| --- | --- |
| Soft gate | Accepted as observe/report only |
| Runtime blocking | Not approved |
| Hard model-role enforcement | Not approved |
| Live trace prerequisite | Blocked/deferred |
| Future enforcement decision | Requires separate owner/QA approval |

## V2 Exclusions

The following remain explicitly out of scope for V1 readiness:

| Exclusion | V1 treatment |
| --- | --- |
| UX expansion | Out of scope |
| Filter work | Out of scope |
| MI/family expansion | Out of scope |
| Complex/multi-question expansion | Out of scope |
| Broad `service.py` refactor | Out of scope |
| Strict enforcement | Out of scope until separate decision |
| Live trace collection without controlled environment | Forbidden |

## Release Decision Rules

| Condition | Release-readiness decision |
| --- | --- |
| Backend EC evidence remains green but UAT/ERP/deployment gates missing | Not ready for V1 release |
| Direct assistant inventory regresses | Block release |
| Raw append scan shows non-authorized sink | Block release |
| Final-answer authority regression appears | Block release |
| Live trace remains blocked | Do not approve hard enforcement; release decision requires owner risk acceptance |
| Browser/manual UAT missing | Block product release approval |
| Deployment/rollback readiness missing | Block production launch |

## Recommended Next Sequence

1. EC-10-D: V2/MI/filter/complex-question roadmap stub, report-only.
2. EC-10-E: Doc packaging/archive proposal for EC-9/EC-10 docs, proposal only.
3. EC-10-F: Draft AI Assistant Doc V1, after outline/checklist acceptance.
4. V1 Release Readiness Gate: browser/manual UAT, ERP scenario validation, trace/environment decision, deployment/rollback readiness.

## EC-10-C Decision

`ec_10_c_v1_release_readiness_checklist_evidence_matrix_ready_for_counterpart_qa_review`
