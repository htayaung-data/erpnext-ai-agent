# V1-R-H Synthetic Manifest Validator Plan

Decision target: `v1_r_h_synthetic_manifest_validator_plan_ready_for_counterpart_qa_review`

## Scope

V1-R-H is a validator-plan/report-only slice. It defines the validator required before any actual synthetic dataset manifest file can be created or used for browser UAT.

This report does not implement the validator, create a manifest, create JSON/YAML artifacts, create seed/data files, write to ERP, run browser automation, capture screenshots, collect traces, stage, commit, push, deploy, enable strict enforcement, or implement V2 work.

## Validator Scope

| Scope item | Plan |
| --- | --- |
| Manifest name | Validate future `V1_BROWSER_UAT_SYNTHETIC_SET_001` manifest only |
| Scenario scope | Smoke-10 only for first validator version |
| Manifest artifact | Not created in this slice |
| ERP behavior | No ERP writes, no reads required |
| Browser behavior | No browser execution |
| Data source | Local manifest content only when future implementation is approved |
| Output | Pass/fail validation report only |

The first validator should be intentionally narrow. It should validate schema, naming, mappings, and forbidden content before any manifest can be used.

## Smoke-10 Scenario IDs

The first validator version should allow only these scenario IDs:

| Scenario ID | Purpose |
| --- | --- |
| `V1RA-001` | AR/customer outstanding |
| `V1RA-009` | AP/supplier payable |
| `V1RA-017` | P&L/profit summary |
| `V1RA-025` | Sales/customer performance |
| `V1RA-033` | Invoice lookup/detail |
| `V1RA-041` | Follow-up detail/explanation |
| `V1RA-049` | Vague business overview |
| `V1RA-055` | Messy/mobile AR shorthand |
| `V1RA-061` | Recommendation boundary |
| `V1RA-064` | Write/action boundary |

Unknown scenario IDs, including `V1RA-999`, must fail validation.

## Required Validator Rules

| Rule | Required behavior |
| --- | --- |
| Manifest name | Must equal `V1_BROWSER_UAT_SYNTHETIC_SET_001` |
| Required top-level sections | Identity, site/context, customers, suppliers, items, invoices, summaries, scenario mappings |
| Scenario IDs | Must be known and limited to Smoke-10 |
| Smoke-10 completeness | All ten Smoke-10 mappings must exist |
| Approved customer ID | `EC7H-CUST-A` style IDs pass only in customer fields |
| Approved supplier ID | `EC7H-SUP-A` style IDs pass only in supplier fields |
| Approved item ID | `EC7H-ITEM-A` style IDs pass only in item/product fields |
| Approved sales invoice ID | `EC7H-SINV-0001` passes only in invoice fields |
| Bare document IDs | `SINV-0001`, `SO-0001`, `PO-0001`, and similar fail |
| Marker-laundered IDs | `EC7H_SYNTH_SINV-0001` fails |
| Real-like names | Bank/company/customer/vendor/person-like names fail |
| Secrets/session/token/cookie fields | Fail |
| Trace/log/screenshot fields | Fail |
| Site config/archive/raw trace/redacted trace paths | Fail |
| Seed/data, ERP UI, temp/probe/cache, PrimeAxis, generated scratch paths | Fail |
| Missing required mapping | Manifest invalid; no scenario should execute |

## Approved Synthetic ID Schemas

| Field family | Allowed schema | Example | Field restriction |
| --- | --- | --- | --- |
| Customer IDs | `EC7H-CUST-[A-Z]` | `EC7H-CUST-A` | Customer records and customer scenario mappings only |
| Supplier IDs | `EC7H-SUP-[A-Z]` | `EC7H-SUP-A` | Supplier records and AP scenario mappings only |
| Item IDs | `EC7H-ITEM-[A-Z]` | `EC7H-ITEM-A` | Item/product records and sales/product mappings only |
| Sales invoice IDs | `EC7H-SINV-[0-9]{4}` | `EC7H-SINV-0001` | Sales invoice records and invoice lookup mappings only |
| Company label | Exact approved synthetic label | `EC7H Synthetic Company` | Context/company field only |
| Scenario IDs | Exact Smoke-10 IDs | `V1RA-001` | Scenario mapping keys only |

`EC7H-SINV-0001` must pass only when it appears in the invoice field family. It must not be accepted as a customer, supplier, item, site label, path, or free-form note.

## Forbidden Examples

| Value | Required result | Reason |
| --- | --- | --- |
| `SINV-0001` | Fail | Bare production-style document ID |
| `SO-0001` | Fail | Bare production-style document ID |
| `PO-0001` | Fail | Bare production-style document ID |
| `EC7H_SYNTH_SINV-0001` | Fail | Marker-laundered production-style document ID |
| `Yoma Bank` | Fail | Real-like bank/entity name |
| `Global Trading Ltd` | Fail | Real-like company/vendor name |
| `John Smith` | Fail | Real-like person name |
| `session_id` | Fail | Secret/session field |
| `cookie` | Fail | Secret/session field |
| `raw_trace` | Fail | Raw trace field/path |
| `redacted_trace.json` | Fail | Trace artifact path |
| `site_config.json` | Fail | Site config path |
| `02_seed_data` | Fail | Seed/data path |
| `erp_workspace_ui` | Fail | ERP UI path |
| `tmp/`, `probe/`, `cache/` | Fail | Forbidden temp/probe/cache path |
| `primeaxis` | Fail | Forbidden owner-decision path |
| `generated/scratch` | Fail | Generated scratch path |

## Future Implementation Proposal

Recommended implementation type: passive script plus tests.

| File | Future role | Approved in V1-R-H? |
| --- | --- | --- |
| `scripts/validate_v1_browser_uat_synthetic_manifest.py` | Passive validator script | Proposed only |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_browser_uat_synthetic_manifest_validator.py` | Focused validator tests | Proposed only |
| `impl_factory/00_governance/current_docs/v1_uat_manifests/v1_browser_uat_synthetic_set_001.json` | Future manifest artifact | Not approved in V1-R-H |

Recommended implementation boundaries:

- Script/test only, no runtime source changes.
- No ERP imports required.
- No Frappe connection.
- No browser execution.
- No file creation except test fixtures in temp directories during test runtime.
- Validator output should be pass/fail with explicit violations.

## Future Allowed Files For Implementation Slice

If owner/QA later approve implementation, allow only:

| File | Staging style |
| --- | --- |
| `scripts/validate_v1_browser_uat_synthetic_manifest.py` | Full-file new script |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_browser_uat_synthetic_manifest_validator.py` | Full-file new test |
| Future implementation governance report | Full-file report |

Do not include:

- actual manifest JSON/YAML,
- seed/data files,
- source runtime edits,
- browser harness execution code,
- screenshots/logs/traces,
- site configs,
- secrets.

## Required Tests For Future Implementation

| Test | Expected |
| --- | --- |
| Valid minimal Smoke-10 manifest passes | Pass |
| Missing manifest name fails | Fail |
| Wrong manifest name fails | Fail |
| Missing required top-level section fails | Fail |
| Missing Smoke-10 scenario mapping fails | Fail |
| Unknown `V1RA-999` fails | Fail |
| `EC7H-CUST-A` passes in customer field | Pass |
| `EC7H-SUP-A` passes in supplier field | Pass |
| `EC7H-ITEM-A` passes in item field | Pass |
| `EC7H-SINV-0001` passes only in invoice field | Pass in invoice field; fail in wrong field |
| `SINV-0001` fails | Fail |
| `SO-0001` fails | Fail |
| `PO-0001` fails | Fail |
| `EC7H_SYNTH_SINV-0001` fails | Fail |
| `Yoma Bank` fails | Fail |
| `Global Trading Ltd` fails | Fail |
| `John Smith` fails | Fail |
| Secret/session/token/cookie fields fail | Fail |
| Trace/log/screenshot fields fail | Fail |
| Site config/archive/raw trace/redacted trace paths fail | Fail |
| Seed/data, ERP UI, temp/probe/cache, PrimeAxis, generated scratch paths fail | Fail |

## Acceptance Criteria For Future Validator Slice

Future implementation should be accepted only if:

- all validator tests pass,
- validator is passive and local-only,
- no ERP/Frappe connection occurs,
- no browser automation occurs,
- no manifest JSON/YAML artifact is created,
- no seed/data files are created,
- no source/runtime behavior changes occur,
- staged files match the future approved script/test/report boundary.

## Verification Results

| Check | Result |
| --- | --- |
| Guardrail | PASS |
| Durable helper presence | PASS: `/tmp/ec8b_verify.py` exists |
| Fake-Frappe `service.py` import | PASS |
| Direct assistant inventory | PASS: `0 / 1 / 27` |
| Raw assistant append scan | PASS: `authorized_emission.py:271`, `authorized_emission.py:327` only |
| Validator implementation | Not created |
| Manifest creation | Not performed |
| JSON/YAML artifact | Not created |
| Seed/data files | Not created |
| ERP writes | Not performed |
| Browser execution | Not run |
| Screenshots/traces | Not captured |
| Staging | Not performed |

## V1-R-H Decision

`v1_r_h_synthetic_manifest_validator_plan_ready_for_counterpart_qa_review`
