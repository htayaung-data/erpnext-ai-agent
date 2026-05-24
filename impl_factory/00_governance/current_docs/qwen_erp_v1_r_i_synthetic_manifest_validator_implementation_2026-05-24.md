# V1-R-I Synthetic Manifest Validator Implementation

Decision target: `v1_r_i_synthetic_manifest_validator_implementation_ready_for_counterpart_qa_review`

## Scope

V1-R-I implements the passive synthetic manifest validator required before any future V1 browser UAT synthetic manifest can be created or used.

This slice adds only:

- `scripts/validate_v1_browser_uat_synthetic_manifest.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_browser_uat_synthetic_manifest_validator.py`
- this V1-R-I governance report

It does not create a manifest JSON/YAML artifact, seed/data file, ERP record, browser run, screenshot, trace, runtime source edit, staged change, commit, push, deployment, strict enforcement, or V2 implementation.

## Implemented Validator Behavior

| Requirement | Implementation |
| --- | --- |
| Passive local validation only | Reads JSON from a supplied path and returns deterministic pass/fail report |
| No ERP/Frappe connection | Script imports only standard library modules |
| No browser automation | No browser code or browser dependency |
| No manifest creation | Validator only reads an input path; it does not generate a manifest |
| No seed/data behavior | No ERP writes, no fixture creation, no seed path use |
| Safe for future JSON manifest validation | CLI accepts a manifest path and prints JSON validation report |

## Validation Rules Covered

| Rule | Status |
| --- | --- |
| Manifest name must equal `V1_BROWSER_UAT_SYNTHETIC_SET_001` | Implemented |
| Required top-level sections must exist | Implemented |
| Scenario IDs limited to Smoke-10 | Implemented |
| All Smoke-10 mappings required | Implemented |
| `EC7H-CUST-A` schema passes in customer/reference fields | Implemented |
| `EC7H-SUP-A` schema passes in supplier/reference fields | Implemented |
| `EC7H-ITEM-A` schema passes in item/reference fields | Implemented |
| `EC7H-SINV-0001` passes only in invoice field family or `V1RA-033` mapping | Implemented |
| `EC7H-SINV-0001` fails outside invoice fields | Implemented |
| Bare IDs `SINV-0001`, `SO-0001`, `PO-0001` fail | Implemented |
| Marker-laundered `EC7H_SYNTH_SINV-0001` fails | Implemented |
| Real-like names fail, including `Yoma Bank`, `Global Trading Ltd`, `John Smith` | Implemented |
| Secret/session/token/cookie fields fail | Implemented |
| Trace/log/screenshot fields fail | Implemented |
| Forbidden paths fail | Implemented |
| Missing required mapping invalidates manifest | Implemented |

## Test Coverage

Focused tests cover:

| Test area | Result |
| --- | --- |
| Valid minimal Smoke-10 manifest passes | PASS |
| Missing/wrong manifest name fails | PASS |
| Missing top-level section fails | PASS |
| Missing Smoke-10 mapping fails | PASS |
| Unknown `V1RA-999` fails | PASS |
| Approved synthetic IDs pass in correct fields | PASS |
| Approved invoice ID fails in wrong field | PASS |
| Bare production IDs fail | PASS |
| Marker-laundered IDs fail | PASS |
| Real-like names fail | PASS |
| Secret/trace/log/screenshot/path fields fail | PASS |
| CLI emits pass/fail report without DB/browser | PASS |

Focused test command:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui \
python3 -m unittest ai_assistant_ui.tests.test_v1_browser_uat_synthetic_manifest_validator
```

Result: `12 passed`.

## Boundary Notes

The validator is intentionally narrow:

- Smoke-10 only.
- JSON input only.
- No actual manifest artifact is created in this slice.
- No synthetic dataset is seeded.
- No ERPNext/Frappe connection is attempted.
- No browser execution is attempted.
- No runtime behavior is changed.

Future full-66 support should be a separate reviewed expansion after Smoke-10 validator acceptance.

## Verification Results

| Check | Result |
| --- | --- |
| Validator tests | PASS: `12 passed` |
| Python compile | PASS for new script/test |
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

## V1-R-I Decision

`v1_r_i_synthetic_manifest_validator_implementation_ready_for_counterpart_qa_review`
