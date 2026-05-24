# V1-R-G Synthetic Dataset Manifest Creation Approval Request

Decision target: `v1_r_g_manifest_creation_request_ready_for_counterpart_qa_owner_review`

## Scope

V1-R-G is an approval-request/report-only slice. It requests approval to create an actual synthetic dataset manifest file later, based on the accepted V1-R-F template.

This report does not create a manifest file, JSON/YAML artifact, seed/data file, ERP record, browser run, screenshot, trace, source/test edit, staged change, commit, push, deployment, strict enforcement, or V2 implementation.

## Proposed Manifest File

| Field | Proposal |
| --- | --- |
| Manifest name | `V1_BROWSER_UAT_SYNTHETIC_SET_001` |
| Proposed filename | `v1_browser_uat_synthetic_set_001.json` |
| Proposed path | `impl_factory/00_governance/current_docs/v1_uat_manifests/v1_browser_uat_synthetic_set_001.json` |
| Proposed format | JSON |
| Path location | Inside repo, under governance docs, only if owner/QA explicitly approve |
| Alternative safer path | External QA-controlled path outside repo if QA prefers no dataset artifact in repo |
| Creation status | Not created in V1-R-G |
| Execution status | Not executable until validator and owner/QA approval exist |

## Proposed Include / Exclude Boundary

If a future slice approves manifest creation, the include boundary should be exactly one synthetic manifest file and no other artifacts.

| Boundary | Rule |
| --- | --- |
| Include | One JSON manifest file matching the approved schema |
| Exclude | Source files |
| Exclude | Test files unless a later validator-test slice is separately approved |
| Exclude | Seed/data files |
| Exclude | ERP writes or fixtures that create ERP records |
| Exclude | Browser screenshots |
| Exclude | Raw/redacted trace artifacts |
| Exclude | Browser logs |
| Exclude | Secrets, cookies, tokens, passwords, session IDs |
| Exclude | Site configs |
| Exclude | Archive content |
| Exclude | Generated scratch artifacts |
| Exclude | ERP UI, temp/probe/cache, PrimeAxis paths |

## Safety Requirements

The future manifest must satisfy all requirements below before acceptance.

| Requirement | Required behavior |
| --- | --- |
| Synthetic records only | All customers, suppliers, items, companies, invoices, and summaries must be clearly synthetic |
| No ERP writes | Manifest creation must not write, seed, insert, migrate, or modify ERP records |
| No seed/data files | Manifest is not a seed fixture and must not live under seed/data paths |
| No browser execution | Manifest creation does not run browser UAT |
| No screenshots/traces | Manifest must not contain or reference screenshots, raw traces, redacted trace JSON, or trace payloads |
| No secrets | Manifest must not contain credentials, cookies, tokens, passwords, session IDs, or site configs |
| Narrow synthetic IDs only | IDs must match explicitly approved schemas |
| No production-like bare IDs | Bare `SINV-0001`, `SO-0001`, `PO-0001`, and similar must be rejected |
| No real-like names | Real bank/company/customer/vendor/person names must be rejected |

## Synthetic Identifier Schema

Allowed only if explicitly approved by future manifest creation slice:

| Record type | Allowed schema | Example |
| --- | --- | --- |
| Customer ID | `EC7H-CUST-[A-Z]` | `EC7H-CUST-A` |
| Supplier ID | `EC7H-SUP-[A-Z]` | `EC7H-SUP-A` |
| Item ID | `EC7H-ITEM-[A-Z]` | `EC7H-ITEM-A` |
| Sales invoice ID | `EC7H-SINV-[0-9]{4}` | `EC7H-SINV-0001` |
| Purchase invoice ID | `EC7H-PINV-[0-9]{4}` | `EC7H-PINV-0001` |
| Company label | Exact approved synthetic label | `EC7H Synthetic Company` |
| Scenario ID | Existing V1-R-A IDs only | `V1RA-001` |

Important rule:

`EC7H-SINV-0001` is allowed only because it matches the narrow approved synthetic sales-invoice schema. It is not allowed merely because it contains a synthetic-looking marker.

Forbidden examples:

| Forbidden value | Reason |
| --- | --- |
| `SINV-0001` | Bare production-style document ID |
| `SO-0001` | Bare production-style document ID |
| `PO-0001` | Bare production-style document ID |
| `EC7H_SYNTH_SINV-0001` | Synthetic marker laundering a production-style document shape |
| `Yoma Bank` | Real-like bank/entity name |
| `Global Trading Ltd` | Real-like company/vendor name |
| `John Smith` | Real-like person name |

## Validator Requirements

No future manifest should be accepted until a validator or equivalent QA review proves:

| Validator rule | Required result |
| --- | --- |
| Manifest name check | Reject anything other than `V1_BROWSER_UAT_SYNTHETIC_SET_001` |
| Schema check | Reject missing required top-level sections |
| Synthetic ID schema check | Accept approved schemas; reject unknown ID formats |
| Bare document ID check | Reject `SINV-0001`, `SO-0001`, `PO-0001`, and similar |
| Real-like name check | Reject bank/company/customer/supplier/person-like real names |
| Scenario ID check | Reject unknown scenario IDs |
| Smoke-10 completeness check | Reject missing mappings for `V1RA-001`, `V1RA-009`, `V1RA-017`, `V1RA-025`, `V1RA-033`, `V1RA-041`, `V1RA-049`, `V1RA-055`, `V1RA-061`, `V1RA-064` |
| Forbidden path check | Reject seed/data, ERP UI, temp/probe/cache, PrimeAxis, generated scratch, raw trace, redacted trace JSON, site config, secret, or archive-content paths |
| Secret field check | Reject credentials, tokens, cookies, passwords, session IDs |
| Trace/log/screenshot check | Reject raw logs, screenshots, trace payloads, browser artifacts |
| Missing mapping behavior | Mark scenario `uat_blocked_dataset`, not executable |

Required proof cases before acceptance:

| Test case | Expected |
| --- | --- |
| `EC7H-CUST-A` | Pass |
| `EC7H-SUP-A` | Pass |
| `EC7H-ITEM-A` | Pass |
| `EC7H-SINV-0001` | Pass only under sales-invoice field |
| `SINV-0001` | Fail |
| `SO-0001` | Fail |
| `PO-0001` | Fail |
| Unknown `V1RA-999` | Fail |
| Missing `V1RA-033` mapping | Fail manifest completeness |
| Real-like bank/customer/vendor name | Fail |

## Future Approval Decisions

Counterpart/QA/Owner may choose one of these later:

| Future decision | Meaning |
| --- | --- |
| Approve inside-repo JSON manifest creation | Create one JSON governance manifest under the proposed path |
| Approve external QA manifest only | Keep manifest outside repo and reference it by label/path |
| Require validator implementation first | Implement validator before any manifest artifact |
| Keep browser UAT blocked | Do not create manifest until site/user/custodian are ready |

V1-R-G recommends requiring validator behavior before any manifest is accepted for execution.

## Current Safety Assessment

The request is safe for review because it does not create the actual manifest. It specifies a narrow future schema and explicitly rejects synthetic-marker laundering, bare production IDs, real-like names, secrets, trace artifacts, site configs, and seed/data behavior.

## Verification Results

| Check | Result |
| --- | --- |
| Guardrail | PASS |
| Durable helper presence | PASS: `/tmp/ec8b_verify.py` exists |
| Fake-Frappe `service.py` import | PASS |
| Direct assistant inventory | PASS: `0 / 1 / 27` |
| Raw assistant append scan | PASS: `authorized_emission.py:271`, `authorized_emission.py:327` only |
| Actual manifest file | Not created |
| JSON/YAML data artifact | Not created |
| Seed/data files | Not created |
| ERP writes | Not performed |
| Browser execution | Not run |
| Screenshots/traces | Not captured |
| Source/test edits | None |
| Staging | Not performed |

## V1-R-G Decision

`v1_r_g_manifest_creation_request_ready_for_counterpart_qa_owner_review`
