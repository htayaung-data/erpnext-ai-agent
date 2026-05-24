# V1-R-B Browser UAT Automation Harness Plan

Decision target: `v1_r_b_browser_uat_automation_harness_plan_ready_for_counterpart_qa_review`

## Scope

V1-R-B is a report-only planning slice. It defines the future browser automation harness for executing the accepted V1-R-A human-like UAT question bank safely against a controlled non-production ERPNext site.

This report does not run browser automation, capture screenshots, collect live traces, create or seed datasets, edit source/test files, stage, commit, push, deploy, enable strict enforcement, or implement V2 work.

## Baseline

| Field | Value |
| --- | --- |
| Worktree | `/tmp/erpai_pr5_postmerge_verify` |
| Baseline HEAD | `a9f34e4` |
| Baseline source | `origin/main` after PR #7 merge |
| Question bank source | `qwen_erp_v1_r_a_human_like_browser_uat_question_bank_automation_plan_2026-05-24.md` |
| Scenario range | `V1RA-001` through `V1RA-066` |
| Slice type | Report-only harness plan |
| Browser automation execution | Not approved |
| Dataset creation/seeding | Not approved |

## Harness Inputs

The future browser harness must receive all execution inputs explicitly. It must not infer production environments, credentials, or records.

| Input | Required rule |
| --- | --- |
| Site URL | Required. Must be a controlled non-production ERPNext/Frappe site URL. Production URLs are forbidden unless owner/QA explicitly approve in a later slice. |
| QA username source | Required. Prefer a dedicated QA user such as `qa_ec7h_trace_user` or another owner-approved non-production UAT user. |
| Password/secret handling | Required. Passwords and tokens must come from an external secret source or interactive secure prompt. Secrets must never be stored in repo, reports, screenshots, logs, JSON, or command history. |
| Company/context selection | Optional only if the site requires company, fiscal year, branch, warehouse, or workspace context. If required and missing, mark scenarios `uat_blocked_environment`. |
| Synthetic/approved dataset manifest | Required. The manifest must list approved customers, suppliers, items, invoices, companies, date ranges, and any scenario-specific substitutions. |
| Question bank source | Required. Use V1-R-A scenarios `V1RA-001` through `V1RA-066` as the canonical question bank. |
| Artifact output path | Required. Must be outside forbidden streams and must store only safe/redacted summaries unless QA approves otherwise. |
| Run identifier | Required. Should be synthetic and non-sensitive, such as `v1_r_c_run_YYYYMMDD_nn`. |

## Synthetic Dataset Mapping Requirement

Before any scenario is executed, the harness must resolve concrete identifiers against a synthetic or QA-approved dataset manifest.

Rules:

| Rule | Required behavior |
| --- | --- |
| Concrete identifiers must be mapped | Invoice IDs, customer names, supplier names, item names, warehouse names, company names, and similar records must map to approved synthetic/QA records. |
| Placeholders are not automatically valid | Examples such as `SINV-0001` must not be used unless explicitly present in the manifest. |
| Missing mapping blocks execution | If mapping is missing, classify the scenario as `uat_blocked_dataset`, not `uat_fail` and not executed. |
| No production data | Real customer/vendor/entity/document identifiers must not be used. |
| Redaction before storage | Any captured artifact that includes record text must be validated as safe/redacted before it can be stored. |

Recommended manifest fields:

| Field | Purpose |
| --- | --- |
| `manifest_name` | Expected future value: `V1_BROWSER_UAT_SYNTHETIC_SET_001` or owner-approved equivalent |
| `source_approval` | QA/Owner approval reference |
| `site_url_allowed` | Approved non-production site URL or URL pattern |
| `company_context` | Synthetic company/context name if required |
| `customers` | Approved synthetic customer records |
| `suppliers` | Approved synthetic supplier records |
| `items` | Approved synthetic item/product records |
| `invoices` | Approved synthetic sales/purchase invoice identifiers |
| `date_ranges` | Approved periods such as current month, fiscal year, prior month |
| `scenario_mappings` | Scenario-specific substitution map for `V1RA-*` IDs |

Scenarios with explicit identifier sensitivity:

| Scenario ID | Placeholder or identifier risk | Required pre-run handling |
| --- | --- | --- |
| `V1RA-033` | `SINV-0001` invoice lookup | Must map to approved synthetic invoice or block as `uat_blocked_dataset` |
| `V1RA-040` | Customer-name invoice search | Must map to approved synthetic customer or block |
| `V1RA-060` | `inv 0001` shorthand | Must map to approved synthetic invoice or require clarification path |
| All AR/AP/customer/supplier/item scenarios | Potential entity names in response | Must use synthetic records and redacted artifacts |

## Automation Flow

Future V1-R-C automation should follow this controlled flow:

1. Load approved harness configuration.
2. Validate site URL is non-production and owner/QA-approved.
3. Validate QA username is present and allowed.
4. Resolve password/token through approved external secret handling.
5. Validate synthetic dataset manifest and scenario mappings.
6. Launch browser in controlled mode.
7. Navigate to the non-production ERPNext site.
8. Log in as the approved QA user.
9. Select company/context if required.
10. Open the AI Assistant UI using the approved route or navigation path.
11. For each scenario, check dataset mapping and environment prerequisites.
12. Submit the scenario prompt exactly as specified or with approved synthetic substitutions.
13. Wait for response completion using stable UI state, not fixed sleeps alone.
14. Capture response text.
15. Capture screenshot only if artifact policy permits.
16. Capture visible context or trace panel only if safely exposed in UI.
17. Classify the response result.
18. Redact/sanitize artifact summaries.
19. Write a safe run summary.
20. Do not store raw secrets, raw traces, production data, or unapproved sensitive screenshots.

## Result Classification

| Classification | Meaning |
| --- | --- |
| `uat_pass` | Scenario executed and response matches expected safe behavior. |
| `uat_warn` | Scenario executed safely but needs manual review, has partial grounding, or has unclear UI evidence. |
| `uat_fail` | Scenario executed and response is unsafe, wrong, ungrounded, invents, predicts/recommends/actions improperly, or violates expected result type. |
| `uat_blocked_environment` | Site, login, route, company/context, permissions, or UI prerequisites are missing. |
| `uat_blocked_dataset` | Required synthetic/QA-approved record mapping is missing. |
| `uat_not_automatable` | Scenario requires manual review or evidence unavailable to browser automation. |

## Assertions

The future harness should evaluate these assertions per scenario:

| Assertion | Required check |
| --- | --- |
| Response appears | AI Assistant produces a visible response or safe error state. |
| No browser/runtime error | Page does not show crash, unhandled exception, login failure, or broken UI state. |
| Expected result type matches scenario | Response aligns with governed ERP answer, clarification, follow-up/detail, bounded/refusal, or fallback/error-safe expectation. |
| Governed ERP answers are grounded | Response reflects approved report/evidence path or visible trace/context where available. |
| Clarifications do not invent | Clarification asks for missing scope instead of inventing facts, customers, invoices, suppliers, or periods. |
| Boundary/refusal answers do not predict/recommend/action | Refusals avoid forecasting, advice, write actions, or unsafe manipulation. |
| Follow-ups preserve visible context safely | Follow-up responses use prior context when available and ask for clarification when context is missing. |
| No raw sensitive records in artifacts | Stored output contains only synthetic/approved/redacted data. |
| No secrets in artifacts | Passwords, tokens, cookies, session IDs, and credentials are never stored. |
| No raw traces in repo | Trace payloads, if any, follow EC-7H redaction and external custody rules. |

## Artifact Policy

| Artifact type | Policy |
| --- | --- |
| Screenshots | Redacted/safe only. Do not store screenshots containing real production data or secrets. |
| Response text | Store safe excerpts or redacted summaries only. |
| Raw browser logs | External secure QA archive only if sensitive; not repo. |
| Trace/context payloads | Use EC-7H redaction protocol; raw traces stay external only. |
| Dataset manifest | Synthetic/QA-approved only; no production identifiers. |
| Credentials/secrets | Never stored in repo or artifacts. |
| Cookies/session data | Never stored in repo. |
| Redacted summaries | Allowed only after QA approval and path review. |
| Output path | Must not be ERP UI, seed/data, temp/probe/cache, PrimeAxis, generated scratch, raw trace, redacted trace JSON, site config, secret, or archive content path unless separately approved. |

Recommended safe run-summary shape:

| Field | Purpose |
| --- | --- |
| `run_id` | Synthetic run ID |
| `site_label` | Non-sensitive site label, not full secret URL if sensitive |
| `scenario_id` | V1-R-A scenario ID |
| `persona` | Persona group |
| `prompt_hash` | Optional hash of prompt after synthetic substitution |
| `result_classification` | One of the approved UAT classifications |
| `expected_result_type` | V1-R-A expected result type |
| `response_excerpt_redacted` | Safe/redacted excerpt only |
| `screenshot_reference` | Safe artifact reference if approved |
| `trace_reference` | Redacted/approved trace reference if available |
| `review_notes` | Manual QA notes without raw sensitive data |

## Execution Approval Boundary

V1-R-B is not execution approval.

Future V1-R-C must request explicit owner/QA approval before running browser automation. That approval request must identify:

- exact non-production site URL,
- QA username,
- secret handling method,
- synthetic dataset manifest,
- scenario subset or full `V1RA-001` through `V1RA-066` run scope,
- artifact output path,
- screenshot policy,
- trace/visible-context policy,
- stop conditions,
- reviewer/custodian.

If any required input is missing, V1-R-C must close as blocked, not attempt execution.

## Forbidden In V1-R-B

V1-R-B does not approve:

- browser automation execution,
- screenshots,
- live trace collection,
- dataset creation,
- dataset seeding,
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
| Staging | Not performed |

## Recommended Next Sequence

1. Counterpart/QA review V1-R-B.
2. If accepted, proceed to V1-R-C Controlled Browser UAT Execution Request, not execution by default.
3. Execute browser UAT only after explicit owner/QA approval and complete environment/dataset/artifact inputs.

## V1-R-B Decision

`v1_r_b_browser_uat_automation_harness_plan_ready_for_counterpart_qa_review`
