# V1-R-C Controlled Browser UAT Execution Request

Decision target: `v1_r_c_controlled_browser_uat_execution_request_ready_for_counterpart_qa_owner_review`

## Scope

V1-R-C is a request-only/report-only approval packet for a future controlled browser UAT run against a non-production ERPNext AI Assistant site.

This report does not run browser automation, capture screenshots, collect live traces, create or seed datasets, edit source/test files, stage, commit, push, deploy, enable strict enforcement, or implement V2 work.

## Baseline

| Field | Value |
| --- | --- |
| Worktree | `/tmp/erpai_pr5_postmerge_verify` |
| Baseline HEAD | `a9f34e4` |
| Baseline source | `origin/main` after PR #7 merge |
| Question bank source | V1-R-A scenarios `V1RA-001` through `V1RA-066` |
| Harness plan source | V1-R-B Browser UAT Automation Harness Plan |
| Slice type | Request-only/report-only |
| Browser execution | Not approved by this report |
| Current execution readiness | Blocked until owner/QA fill all required inputs |

## Execution Inputs Required

All inputs below must be filled and approved before any V1-R-C browser automation execution can begin.

| Input | Required value before execution | Current value | Execution effect if missing |
| --- | --- | --- | --- |
| Exact non-production site URL or site label | Owner/QA-approved non-production ERPNext/Frappe site URL or stable site label | `TBD_OWNER_QA_REQUIRED` | `uat_blocked_environment` |
| QA username | Dedicated non-production QA user | `TBD_OWNER_QA_REQUIRED` | `uat_blocked_environment` |
| Password/secret handling method | External secret manager, secure prompt, or approved runtime-only credential handoff | `TBD_OWNER_QA_REQUIRED` | `uat_blocked_environment` |
| Company/context selection | Company, fiscal year, branch, warehouse, or workspace context if site requires it | `TBD_IF_REQUIRED` | `uat_blocked_environment` |
| Synthetic dataset manifest path/name | Approved synthetic/QA dataset manifest mapping V1-R-A records | `TBD_OWNER_QA_REQUIRED` | `uat_blocked_dataset` |
| Artifact output path | Approved safe/redacted output path outside forbidden streams | `TBD_OWNER_QA_REQUIRED` | `uat_blocked_environment` |
| Screenshot policy | Approved yes/no/redaction policy for screenshots | `TBD_OWNER_QA_REQUIRED` | `uat_blocked_environment` |
| Visible-context/trace policy | Whether visible context or trace panel may be inspected/captured, and how redaction applies | `TBD_OWNER_QA_REQUIRED` | `uat_blocked_environment` |
| Reviewer/custodian | Named QA/Owner reviewer and artifact custodian | `TBD_OWNER_QA_REQUIRED` | `uat_blocked_environment` |
| Stop conditions | Exact conditions requiring immediate stop | Proposed below; must be approved | `uat_blocked_environment` |

## Proposed Stop Conditions

Future execution must stop immediately if any of these occur:

| Stop condition | Required action |
| --- | --- |
| Site appears to be production | Stop run; classify `uat_blocked_environment` |
| Login uses non-approved user | Stop run; classify `uat_blocked_environment` |
| Dataset mapping missing for concrete identifier | Skip scenario; classify `uat_blocked_dataset` |
| Real customer/vendor/entity/document appears in prompt, response, screenshot, or artifact | Stop run; quarantine artifact externally for QA/Owner review |
| Browser exposes secrets, session tokens, cookies, or credentials | Stop run; do not store artifact in repo |
| AI Assistant emits unsafe prediction/recommendation/action instead of boundary | Mark scenario `uat_fail`; continue only if QA-approved |
| Repeated runtime/browser errors prevent reliable execution | Stop run; classify remaining scenarios `uat_blocked_environment` |
| Trace/visible-context panel exposes raw sensitive payload | Stop trace capture; continue response-only if safe and approved |

## Scenario Scope

### Default Proposed Run

Default proposed run: all accepted V1-R-A scenarios:

`V1RA-001` through `V1RA-066`

This full run should be used only if:

- non-production site is verified,
- QA user works,
- synthetic dataset manifest covers required identifiers,
- artifact policy is approved,
- owner/QA approve full-scope execution.

### Optional Safer First-Run Smoke Subset

If owner/QA prefer a smaller first run, use this 10-scenario smoke subset:

| Scenario ID | Coverage |
| --- | --- |
| `V1RA-001` | AR/customer outstanding |
| `V1RA-009` | AP/supplier payable |
| `V1RA-017` | P&L/profit summary |
| `V1RA-025` | Sales/customer performance |
| `V1RA-033` | Invoice lookup/detail with dataset mapping gate |
| `V1RA-041` | Follow-up explanation/detail |
| `V1RA-049` | Vague business overview |
| `V1RA-055` | Messy/mobile AR shorthand |
| `V1RA-061` | Recommendation boundary |
| `V1RA-064` | Write/action boundary |

Exact scenario scope must be explicitly owner/QA-approved before execution. Without approval, no scenarios run.

## Dataset Mapping Gate

Every scenario with concrete identifiers must be mapped to synthetic or QA-approved records before execution.

Required rules:

| Rule | Required behavior |
| --- | --- |
| Concrete identifiers require manifest mapping | Invoice IDs, customer names, supplier names, item names, company names, warehouses, and document names must be approved before use |
| Placeholder IDs are not automatically valid | Examples like `SINV-0001` must not run unless the manifest explicitly includes that synthetic record |
| Missing mapping blocks scenario | Mark `uat_blocked_dataset`, do not execute |
| No production identifiers | Real customer/vendor/document/entity names are forbidden |
| Synthetic substitutions must be logged safely | Store scenario ID and synthetic mapping key, not raw sensitive data |

High-priority mapping checks:

| Scenario ID | Mapping needed |
| --- | --- |
| `V1RA-033` | Synthetic sales invoice ID |
| `V1RA-040` | Synthetic customer name for invoice search |
| `V1RA-060` | Synthetic invoice shorthand mapping or expected clarification path |
| AR/AP customer/supplier scenarios | Approved synthetic customer/supplier records |
| Product/inventory scenarios | Approved synthetic item/product records |

## Execution Command Proposal

No executable browser-UAT harness command exists or is run in V1-R-C. The future command shape should be implemented or approved in a later slice before execution.

Recommended future dry-run/preflight command shape:

```bash
python3 scripts/run_v1_browser_uat.py \
  --config /path/to/approved/v1_r_c_browser_uat_config.json \
  --question-bank impl_factory/00_governance/current_docs/qwen_erp_v1_r_a_human_like_browser_uat_question_bank_automation_plan_2026-05-24.md \
  --dataset-manifest /path/to/approved/synthetic_manifest.json \
  --scenario-scope smoke-10 \
  --mode preflight \
  --no-browser-execution
```

Recommended future execution command shape, only after explicit approval:

```bash
python3 scripts/run_v1_browser_uat.py \
  --config /path/to/approved/v1_r_c_browser_uat_config.json \
  --question-bank impl_factory/00_governance/current_docs/qwen_erp_v1_r_a_human_like_browser_uat_question_bank_automation_plan_2026-05-24.md \
  --dataset-manifest /path/to/approved/synthetic_manifest.json \
  --scenario-scope approved \
  --artifact-output /approved/safe/redacted/output/path \
  --mode execute
```

If the harness is operated manually or through Codex browser tooling instead of a script, V1-R-C execution approval must still provide the same inputs and must produce the same safe/redacted run summary.

## Artifact Handling

| Artifact | Rule |
| --- | --- |
| Raw screenshots | Not stored in repo; only safe/redacted screenshots may be retained after QA approval |
| Raw browser logs | External QA/Owner custody only if sensitive |
| Raw traces | Not stored in repo |
| Redacted trace summaries | Allowed only after EC-7H-compatible redaction and QA approval |
| Response text | Store redacted/safe excerpts only |
| Dataset manifest | Synthetic/QA-approved only; no production identifiers |
| Secrets/passwords/tokens/cookies | Never stored in repo or artifacts |
| Artifact output path | Must avoid ERP UI, seed/data, temp/probe/cache, PrimeAxis, generated scratch, raw trace, redacted trace JSON, site config, secret, and archive content paths |

Recommended summary output fields:

| Field | Purpose |
| --- | --- |
| `run_id` | Synthetic run identifier |
| `site_label` | Non-sensitive approved site label |
| `scenario_scope` | `full-66`, `smoke-10`, or approved custom list |
| `scenario_id` | V1-R-A scenario ID |
| `dataset_mapping_status` | `mapped`, `not_required`, or `uat_blocked_dataset` |
| `result_classification` | UAT classification |
| `expected_result_type` | Scenario expected result type |
| `response_excerpt_redacted` | Safe excerpt only |
| `screenshot_reference` | Safe/redacted reference only if approved |
| `visible_context_reference` | Safe reference only if approved |
| `reviewer` | Named QA/Owner reviewer |
| `notes` | Redacted QA notes |

## Approval Boundary

V1-R-C is not execution approval by itself. Execution may begin only if owner/QA explicitly approve:

- exact site URL or site label,
- QA username,
- secret handling method,
- context/company settings,
- dataset manifest,
- scenario scope,
- artifact path,
- screenshot policy,
- visible-context/trace policy,
- reviewer/custodian,
- stop conditions.

If any required input remains missing, the next execution slice must close as blocked, not executed.

## Forbidden In V1-R-C

V1-R-C does not approve:

- browser automation execution,
- screenshots,
- live trace collection,
- dataset creation or seeding,
- source edits,
- test edits,
- staging,
- commit,
- push,
- deployment,
- strict enforcement,
- V2 implementation.

## Verification Results

| Check | Result |
| --- | --- |
| Guardrail | PASS |
| Durable helper presence | PASS: `/tmp/ec8b_verify.py` exists |
| Fake-Frappe `service.py` import | PASS |
| Direct assistant inventory | PASS: `0 / 1 / 27` |
| Raw assistant append scan | PASS: `authorized_emission.py:271`, `authorized_emission.py:327` only |
| Browser automation | Not run |
| Screenshots | Not captured |
| Live trace collection | Not run |
| Dataset creation/seeding | Not run |
| Staging | Not performed |

## Possible Decisions After Review

| Decision | Meaning |
| --- | --- |
| `v1_r_c_execution_request_ready_for_owner_input` | Request packet is acceptable, but inputs still need owner/QA values |
| `v1_r_c_blocked_missing_execution_inputs` | Required inputs are missing or unsafe |
| `v1_r_c_approved_for_smoke_10_execution` | Owner/QA approve smoke subset execution in a later execution slice |
| `v1_r_c_approved_for_full_66_execution` | Owner/QA approve full question bank execution in a later execution slice |

## Recommended Next Step

If Counterpart/QA accept this request packet, owner should either:

1. fill the missing execution inputs and approve a V1-R-D preflight/dry-run harness check, or
2. close as blocked until a controlled non-production site, QA user, synthetic dataset, and artifact policy exist.

## V1-R-C Decision

`v1_r_c_controlled_browser_uat_execution_request_ready_for_counterpart_qa_owner_review`
