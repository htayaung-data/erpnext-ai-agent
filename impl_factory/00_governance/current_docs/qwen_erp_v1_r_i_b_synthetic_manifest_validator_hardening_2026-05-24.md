# V1-R-I-B Synthetic Manifest Validator Hardening

Date: 2026-05-24

Decision: `v1_r_i_b_synthetic_manifest_validator_hardening_ready_for_counterpart_qa_review`

## Scope

V1-R-I-B is a narrow passive validator hardening slice for the future V1 browser UAT synthetic manifest. It does not create a manifest, seed ERP data, execute browser UAT, collect screenshots/traces, or modify runtime source.

Allowed files changed:

- `scripts/validate_v1_browser_uat_synthetic_manifest.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_browser_uat_synthetic_manifest_validator.py`
- this governance report

## Fixes Implemented

### Scenario-Specific Record Families

The validator now applies explicit Smoke-10 scenario-family checks for `scenario_mappings[*].required_records`.

Examples now rejected:

- `V1RA-009` AP/supplier scenario with `EC7H-CUST-A`
- `V1RA-001` AR/customer scenario with `EC7H-SUP-A`
- `V1RA-025` sales/product scenario with `EC7H-SUP-A`

Correct declared records still pass in the approved scenario families:

- AR/customer: customer records
- AP/supplier: supplier records
- sales/product: customer and item records
- invoice lookup: invoice and customer records
- overview/follow-up/boundary scenarios: limited to their documented Smoke-10 families

### Summaries Schema

The validator now requires `summaries` to be an object. String, list, and null values fail.

Accepted minimal shape requires these keys:

- `ar`
- `ap`
- `pnl`
- `sales`
- `boundary`

The `ar`, `ap`, and `sales` summary sections must include a non-empty `record_ids` list.

### Dataset Status Allowlist

The validator now allows only:

- `mapped`
- `boundary_only`
- `clarification_expected`

Unsafe values such as `execute_real_data` fail validation.

## Tests Added

Focused validator tests now prove:

- wrong record family in `V1RA-009`, `V1RA-001`, and `V1RA-025` fails
- correct record families still pass
- malformed `summaries` values fail
- missing required summary keys fail
- allowed `expected_dataset_status` values pass
- `execute_real_data` fails

The existing V1-R-I and V1-R-I-A tests continue to cover manifest name, required sections, Smoke-10 mapping completeness, unknown scenario IDs, approved synthetic IDs, undeclared references, production-like IDs, real-like names, site metadata, artifact/path fields, and passive CLI behavior.

## Verification

- Validator tests: PASS, `22 passed`
- Python compile: PASS
- Guardrail: PASS
- Fake-Frappe `service.py` import: PASS
- Direct assistant inventory: `0 / 1 / 27`
- Raw assistant append scan: only `authorized_emission.py:271` and `authorized_emission.py:327`
- Scoped diff check: PASS
- Path-aware excluded/artifact status scan: clean
- Staged files: `0`

## Boundaries Preserved

- No manifest JSON/YAML file was created.
- No seed/data file was created.
- No ERP writes were performed.
- No browser automation was executed.
- No screenshots or traces were collected.
- No runtime source was edited.
- No staging, commit, or push was performed.
- No deployment, strict enforcement, or V2 implementation was performed.
