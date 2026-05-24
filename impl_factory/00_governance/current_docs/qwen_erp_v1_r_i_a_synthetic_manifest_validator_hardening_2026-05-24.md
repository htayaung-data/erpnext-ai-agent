# V1-R-I-A Synthetic Manifest Validator Hardening

Decision target: `v1_r_i_a_synthetic_manifest_validator_hardening_ready_for_counterpart_qa_review`

## Scope

V1-R-I-A is a narrow hardening slice for the passive V1 browser UAT synthetic manifest validator.

Allowed files changed:

- `scripts/validate_v1_browser_uat_synthetic_manifest.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_browser_uat_synthetic_manifest_validator.py`
- this V1-R-I-A governance report

This slice does not create a manifest JSON/YAML artifact, seed/data file, ERP record, browser run, screenshot, trace, runtime source edit, staged change, commit, push, deployment, strict enforcement, or V2 implementation.

## Required Fixes Implemented

| Fix | Status |
| --- | --- |
| Reject undeclared synthetic references | Implemented |
| Require `site.environment_type = "non_production"` | Implemented |
| Reject missing/unknown/production environment types | Implemented |
| Reject production-looking site labels | Implemented |
| Reject unknown artifact/path containers | Implemented |

## Validator Behavior Added

### P1: Declared Record References Required

Scenario `required_records` must now reference records actually declared in the manifest. Pattern-valid IDs are no longer enough.

Examples that fail when undeclared:

- `EC7H-CUST-Z`
- `EC7H-SUP-Z`
- `EC7H-ITEM-Z`
- `EC7H-SINV-9999`

Declared synthetic records continue to pass.

### P1: Non-Production Site Metadata

The validator now requires:

```text
site.environment_type = "non_production"
```

It rejects:

- `production`,
- `unknown`,
- missing environment type,
- production-looking site labels such as `erp-production-main`.

### P2: Generic Artifact / Path Containers

The validator now rejects generic artifact/path containers unless a future allowlist is explicitly approved.

Example rejected field:

```text
artifact.output_path = "/var/qa/artifacts"
```

## Tests Added

| Test | Result |
| --- | --- |
| Undeclared synthetic customer reference fails | PASS |
| Undeclared synthetic supplier reference fails | PASS |
| Undeclared synthetic item reference fails | PASS |
| Undeclared synthetic invoice reference fails | PASS |
| Declared synthetic records pass | PASS |
| `environment_type = "production"` fails | PASS |
| Missing environment type fails | PASS |
| Unknown environment type fails | PASS |
| Production-looking site label fails | PASS |
| Unknown artifact/path container fails | PASS |

Full focused validator test result:

```text
16 tests passed
```

## Boundary Notes

This remains a passive local validator. It reads JSON only when a future manifest path is supplied. It does not create a manifest, write ERP records, connect to Frappe, launch a browser, capture screenshots, capture traces, or alter runtime behavior.

## Verification Results

| Check | Result |
| --- | --- |
| Validator tests | PASS: `16 passed` |
| Python compile | PASS for validator script and test |
| Guardrail | PASS |
| Durable helper presence | PASS: `/tmp/ec8b_verify.py` exists |
| Fake-Frappe `service.py` import | PASS |
| Direct assistant inventory | PASS: `0 / 1 / 27` |
| Raw assistant append scan | PASS: `authorized_emission.py:271`, `authorized_emission.py:327` only |
| Scoped diff check | PASS |
| Path-aware excluded/artifact status scan | PASS |
| Staged files | PASS: `0` |
| Manifest JSON/YAML artifact | Not created |
| Seed/data files | Not created |
| ERP writes | Not performed |
| Browser execution | Not run |
| Screenshots/traces | Not captured |

## V1-R-I-A Decision

`v1_r_i_a_synthetic_manifest_validator_hardening_ready_for_counterpart_qa_review`
