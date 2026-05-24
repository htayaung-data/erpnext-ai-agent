# EC-10-D V2 / MI / Filter / Complex-Question Roadmap Stub

Decision target: `ec_10_d_v2_mi_filter_complex_question_roadmap_stub_ready_for_counterpart_qa_review`

## Scope

EC-10-D is a report-only roadmap stub for future V2 planning categories. It separates V1 release scope from future V2 exploration and records prerequisites that must be satisfied before V2 implementation begins.

This report does not approve V2 implementation, MI/filter/UX code changes, doc moves, archive creation, packaging, staging, commit, push, deployment, live trace collection, or strict enforcement.

## Baseline

| Field | Value |
| --- | --- |
| Worktree | `/tmp/erpai_pr5_postmerge_verify` |
| Branch | `main` |
| HEAD | `46ed5ef` |
| EC-10-A | Accepted docs readiness baseline |
| EC-10-B | QA-accepted Doc V1 outline/consolidation plan |
| EC-10-C | QA-accepted V1 release readiness checklist/evidence matrix |
| EC-10-D action | New governance report only |
| V2 implementation approval | None |
| Strict enforcement approval | None |
| Live trace collection approval | None |

## V1 Versus V2 Boundary

| Area | V1 scope | V2 scope |
| --- | --- | --- |
| Core assistant behavior | Governed backend/runtime assistant with final-answer authority and authorized emission | Expanded product capabilities after V1 release gates |
| Metadata/provenance | Runtime metadata envelope, deterministic/control metadata, AI/helper provenance, soft-gate reporting | Possible stricter promotion gates after separate evidence and owner approval |
| UI/product experience | Existing product behavior only; no UX expansion in EC-10 | Future UX/product expansion after V1 validation |
| ERP answers | Supported governed/report/entity/detail scenarios only after V1 scenario validation | Broader ERP reasoning, richer insight, multi-step workflows |
| Filters | No new filter implementation | Future filter/query planning and richer report selection |
| MI/family expansion | Out of scope | Future model-intelligence/family planning |
| Complex questions | Out of scope unless already supported by V1 runtime | Future multi-intent/complex-question strategy |
| Strict enforcement | Not approved; soft gate observe/report only | Separate hard-enforcement decision, not automatically V2 |
| Live traces | Blocked/deferred until controlled environment exists | Separate evidence gate, not automatically V2 |

## V2 Roadmap Categories

All items below are future planning categories only. None are implementation-approved.

| Category | Planning purpose | V1 dependency | Implementation approval |
| --- | --- | --- | --- |
| Model Intelligence (MI) | Define future model capability expansion, model-role choices, and evaluation needs | V1 release gates accepted; soft-gate evidence stable | Not approved |
| Filters | Plan filter interpretation, query constraints, and report-selection safety | ERP scenario validation and current report-selection baseline | Not approved |
| Complex business questions | Plan multi-intent, multi-entity, and compound ERP question handling | V1 manual/browser UAT and scenario matrix accepted | Not approved |
| Richer insight | Plan summaries, comparisons, trend explanations, and bounded recommendations | Unsupported prediction/recommendation boundary policy accepted | Not approved |
| Multi-step reasoning | Plan controlled reasoning chains and evidence preservation | Final-answer authority and metadata probes remain green | Not approved |
| Future UX/product expansion | Plan user-facing flows, trace visibility, approvals, and operator controls | Browser/manual UAT and deployment readiness accepted | Not approved |

## Category Detail

### MI

Future planning questions:

- Which model roles are needed beyond current V1 light/heavy/helper/shadow provenance?
- What evaluations prove role compliance before model-family expansion?
- What fallback behavior is acceptable for higher-capability models?
- How should cost, latency, and observability be governed?

Prerequisites before implementation:

- V1 release readiness checklist accepted.
- Browser/manual UAT accepted.
- ERP scenario validation accepted.
- Deployment/rollback readiness accepted.
- Owner approves a dedicated MI planning/implementation slice.

### Filters

Future planning questions:

- Which ERP report filters are safe for user-driven interpretation?
- How should ambiguous filters be clarified?
- How should filter provenance be recorded in runtime metadata?
- What tests prove report-selection behavior does not drift?

Prerequisites before implementation:

- V1 ERP scenario matrix accepted.
- Existing report-selection behavior documented.
- Owner approves filter scope and safety boundaries.

### Complex Business Questions

Future planning questions:

- Which multi-intent questions are supported, partially supported, or refused?
- How should the assistant decompose complex questions without overclaiming?
- How should final-answer authority work for multi-step answers?
- What bounded responses are required for unsupported complexity?

Prerequisites before implementation:

- V1 final-answer authority remains green.
- Browser/manual UAT captures current limits.
- Unsupported prediction/recommendation boundary validation is accepted.
- Owner approves a complex-question planning slice.

### Richer Insight

Future planning questions:

- Which insights are factual summaries versus predictions/recommendations?
- What evidence is required for comparisons, trends, and explanations?
- How should uncertainty be displayed?
- Which insights require explicit policy boundaries?

Prerequisites before implementation:

- V1 boundary policy accepted.
- ERP scenario validation accepted.
- Owner/QA define allowed insight categories.

### Multi-Step Reasoning

Future planning questions:

- What runtime trace/evidence is needed for multi-step chains?
- Which reasoning steps may be exposed to users, auditors, or operators?
- How should helper/tool metadata be preserved across steps?
- What prevents helper provenance from becoming final-answer authority?

Prerequisites before implementation:

- EC-7F/EC-7G evidence remains green.
- Live trace evidence plan is resolved separately.
- Owner approves a multi-step reasoning design slice.

### Future UX / Product Expansion

Future planning questions:

- What user-facing controls or explanations should be added?
- How should boundaries, fallbacks, and trace summaries be shown?
- What operator review or QA workflow is required?
- How should release readiness be displayed or reported?

Prerequisites before implementation:

- Browser/manual UAT accepted.
- Deployment/rollback readiness accepted.
- Product/owner approves UX scope.

## Prerequisites Before Any V2 Implementation

| Prerequisite | Required before V2 starts? | Current status |
| --- | --- | --- |
| V1 release readiness checklist accepted | Yes | EC-10-C accepted as checklist, but gates remain open |
| Browser/manual UAT accepted | Yes | Missing |
| ERP scenario validation accepted | Yes | Missing |
| Deployment/rollback readiness accepted | Yes | Missing |
| Owner approval for V2 scope | Yes | Missing |
| Product/QA acceptance of V1 boundaries | Yes | Missing |
| Packaging plan for V2 work | Yes | Missing |
| Strict enforcement decision | Separate gate, not prerequisite for all V2 work | Not approved |
| Live trace collection | Separate gate, required before hard enforcement; may also inform V2 | Blocked/deferred |

## Separate Gates Not Bundled Into V2

### Strict Enforcement

Strict enforcement remains a separate decision gate. EC-7G soft gate is observe/report-only. V2 planning must not quietly convert soft readiness into runtime blocking.

Required before strict enforcement discussion:

- live trace evidence or explicit owner risk decision,
- QA acceptance of strict-readiness evidence,
- dedicated enforcement decision record,
- rollback and disablement plan.

### Live Trace Work

Live trace work remains blocked/deferred until a controlled non-production environment exists. It is not a V2 feature and should not be used as a reason to start V2 implementation prematurely.

Required before live trace collection:

- controlled bench/site,
- dedicated QA test user,
- synthetic dataset,
- raw trace custodian,
- secure external archive,
- validated redaction protocol.

## Explicit Non-Goals

EC-10-D does not approve:

- MI implementation,
- filter implementation,
- UX/product expansion,
- complex-question handling changes,
- richer insight behavior,
- multi-step reasoning behavior,
- strict enforcement,
- live trace collection,
- deployment,
- doc moves or archives,
- packaging, staging, commit, or push.

## Recommended Future Sequence

| Slice | Purpose | Scope |
| --- | --- | --- |
| EC-10-E | Docs packaging/archive proposal | Proposal only |
| EC-10-F | Draft AI Assistant Doc V1 | Draft/report only |
| V1 Release Gate | Browser/manual UAT, ERP scenarios, deployment/rollback, boundary validation | Product/release validation |
| V2-A | V2 roadmap expansion after V1 gate decision | Planning only unless separately approved |
| Strict Enforcement Decision | Hard enforcement consideration | Separate from V2 |
| Live Trace Collection | Controlled trace evidence | Separate from V2 |

## EC-10-D Decision

`ec_10_d_v2_mi_filter_complex_question_roadmap_stub_ready_for_counterpart_qa_review`
