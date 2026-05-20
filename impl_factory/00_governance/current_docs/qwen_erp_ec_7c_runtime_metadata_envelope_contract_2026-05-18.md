# EC-7C Runtime Metadata Envelope Contract

Date: 2026-05-18
Worktree: `/tmp/erpai_ec7b0_import_integrity`
Branch: `feature/ec-7b0-runtime-import-integrity`
HEAD: `2641458`
Slice: `EC-7C Metadata Envelope Contract`
Decision: `ec_7c_metadata_envelope_contract_ready_for_counterpart_review`
Revision: validator hardening added before QA review

## Executive Summary

EC-7C defines the canonical runtime metadata envelope before any broad lane wiring. This is a contract/schema slice only. It does not enable strict enforcement, does not wire metadata into active lanes, and does not change runtime answer behavior.

The revised contract now validates allowed values, role compatibility by lane class, and forged/inconsistent envelopes. `validate_runtime_metadata_envelope(...)` recomputes missing fields, metadata status, strict-readiness status, and strict-enforcement readiness instead of trusting caller-supplied values.

## Scope Control

Implemented:

- Added `qwen_chat/runtime_metadata_contract.py`.
- Added focused tests in `tests/test_runtime_metadata_contract.py`.
- Defined canonical fields, allowed role values, lane classes, metadata statuses, strict-readiness statuses, and validation rules.
- Added role/lane compatibility rules and tests for mismatch handling.
- Hardened validation against forged `covered`, `strict_ready`, empty `missing_fields`, and inconsistent `strict_enforcement_ready` claims.

Not implemented:

- No broad lane wiring.
- No strict enforcement.
- No model-role hard blocking.
- No service.py refactor.
- No UX, Filter, MI, or family expansion.
- No staging, commit, push, cleanup, delete, move, or archive.

## Canonical Envelope Fields

The envelope defines these canonical fields:

- `model_role`
- `model_name`
- `fallback_used`
- `fallback_reason`
- `role_compliance`
- `authority_source`
- `evidence_scope`
- `answer_mode`
- `preflight_status`
- `metadata_status`
- `strict_readiness_status`
- `lane_id`
- `lane_class`
- `metadata_source`
- `runtime_probe_required`

The contract also records `expected_model_role`, `compatible_model_roles`, `role_lane_compatible`, `missing_fields`, `strict_enforcement_ready`, `contract_version`, and `created_at`.

## Role Compatibility Matrix

| Lane class | Compatible role values |
| --- | --- |
| `ai_semantic` | `light_semantic` only |
| `ai_reasoning` | `heavy_reasoning` only |
| `deterministic_report` | `deterministic` only |
| `deterministic_visible_context` | `deterministic` only |
| `policy_boundary` | `policy_boundary` only |
| `shadow_observer` | `shadow_observer` only |
| `control_meta` | `control_meta`, `not_applicable` |
| `error_fallback` | `not_applicable` only |
| `unknown` | `unknown` only |

## Validator Hardening

The validator now independently recomputes:

- role/lane compatibility
- required missing fields
- `metadata_status`
- `strict_readiness_status`
- `strict_enforcement_ready`

The validator rejects:

- supplied `missing_fields` that omit recomputed missing fields
- supplied `metadata_status` inconsistent with recomputed status
- supplied `strict_readiness_status` inconsistent with recomputed readiness
- supplied `strict_enforcement_ready=True` when recomputed readiness is not `strict_ready`
- AI lanes marked `strict_ready` without complete model name, fallback state, and compliant role metadata
- AI lanes marked `strict_ready` when fallback is used
- deterministic report lanes marked `covered` without `authority_source`
- policy boundary lanes marked `covered` unless `preflight_status=bounded`
- control/meta lanes using `model_role=control_meta` without explicit `authority_source`
- role/lane mismatches such as deterministic report + `light_semantic`

## Compliance Rules Captured

- AI lanes must provide `model_role`, `model_name`, `fallback_used`, and `role_compliance` before they can be strict-ready.
- AI lanes with fallback use are classified as `soft_block`, even when the role matches.
- Runtime probe requirements force `not_ready_runtime_probe_required`.
- Deterministic lanes must explicitly declare metadata rather than silently omitting it.
- Deterministic/control/policy lanes are not AI strict-enforcement targets and classify as `not_applicable` once metadata is complete.
- Policy-boundary lanes must use `model_role=policy_boundary` and `preflight_status=bounded`; otherwise metadata is incomplete.
- Control/meta paths using `control_meta` must carry explicit `authority_source=control_meta` to be covered.
- Control/meta paths may use `not_applicable`; user-visible control output should still carry authority when later wired.
- Error-fallback paths may use only `not_applicable`.
- `unknown` is allowed as a dry-run inventory state only under `lane_class=unknown`; it is never strict-ready.

## Files Added Or Revised

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/runtime_metadata_contract.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_runtime_metadata_contract.py`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_7c_runtime_metadata_envelope_contract_2026-05-18.md`

## Tests Added For Counterpart And QA Cases

Role/lane mismatch tests:

- Deterministic report with `light_semantic` fails.
- Policy boundary with `deterministic` fails.
- Shadow observer with `light_semantic` fails.
- AI semantic with `heavy_reasoning` fails.
- Control meta accepts `control_meta`.
- Control meta accepts `not_applicable`.
- Error fallback accepts `not_applicable`.

Adversarial validator tests:

- AI semantic forged as `strict_ready` with `model_name=unknown` is invalid.
- AI semantic forged as `strict_ready` with `fallback_used=None` is invalid.
- AI semantic forged as `strict_ready` with `fallback_used=True` is invalid.
- Deterministic report forged as `covered` without `authority_source` is invalid.
- Policy boundary forged as `covered` with `preflight_status=passed` is invalid.
- Control/meta forged as `covered` without `authority_source` is invalid.
- `strict_enforcement_ready=True` inconsistent with recomputed readiness is invalid.
- Supplied `missing_fields=[]` is invalid when recomputed missing fields are non-empty.

## Verification

Verification run from `/tmp/erpai_ec7b0_import_integrity`:

- `python3 scripts/check_qwen_enterprise_guardrails.py`: PASS
- `git diff --check -- impl_factory/05_custom_logic/custom_app/ai_assistant_ui`: PASS
- `python3 -m py_compile runtime_metadata_contract.py test_runtime_metadata_contract.py`: PASS
- `python3 -m unittest ai_assistant_ui.tests.test_runtime_metadata_contract ai_assistant_ui.tests.test_model_role_observability_contracts ai_assistant_ui.tests.test_model_role_strict_readiness_contracts`: PASS after validator hardening
- Fake-Frappe import probe for `ai_assistant_ui.qwen_chat.service`: PASS
- Final-answer emission dry-run source scan:
  - `active_runtime_direct_assistant_append_count=0`
  - `inventory_count=1`
  - `migrated_authorized_paths_length=27`
- Staged files: 0
- Excluded status scan for ERP UI, seed/data, temp/probe/cache, and PrimeAxis paths: clean

## Known Limits

- EC-7C is not runtime metadata wiring.
- EC-7C is not strict model-role enforcement.
- EC-7C does not prove runtime model metadata completeness by lane.
- EC-7C does not change answer emission behavior.

## Recommended Next Sequence

1. `EC-7D Deterministic / Control Metadata Wiring`: apply this envelope to runtime gate, compiled support, legacy runtime, artifact boundary, local follow-up, entity follow-up, clarification, and service policy/control paths.
2. `EC-7E AI Runtime Metadata Provenance`: normalize model name, fallback state, fallback reason, and role compliance for frontdoor, fresh query, follow-up semantic interpretation, reasoning, and NBU shadow.
3. `EC-7F Runtime Probe Suite`: prove metadata completeness by lane and outcome.
4. `EC-7G Strict Readiness Gate`: dry-run or soft-block only.
5. `EC-7H Strict Enforcement Decision`: decide whether hard enforcement is safe or whether release-promotion blocking remains the enterprise posture.

Final recommendation: `ec_7c_metadata_envelope_contract_ready_for_counterpart_review`
