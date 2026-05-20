# EC-7E-C2-C1 Light Semantic Outcome Strict-Readiness Guard

Decision: `ec_7e_c2_c1_light_semantic_strict_readiness_guard_ready_for_counterpart_review`

## Scope

EC-7E-C2-C1 was a narrow metadata guard fix. It did not change routing, answer text, report selection, final-answer authority, model behavior, strict enforcement, UX/Filter/MI/family expansion, staging, commit, push, or deployment.

## Branch / Head

- Branch: `feature/ec-7b0-runtime-import-integrity`
- Head: `2641458`
- Staged files: `0`

## Fix Summary

The shared light-semantic metadata helper now accepts a semantic result status. Only `status="accepted"` remains eligible for strict readiness when model metadata is complete.

For every non-accepted status, the helper forces degraded provenance:

- `fallback_used=True`
- `fallback_reason=semantic_status_<status>` when no explicit fallback reason is supplied
- explicit `fallback_used=True` and explicit `fallback_reason` remain preserved
- runtime metadata envelope remains valid but cannot become `strict_ready`

Updated light-semantic result payload builders:

- `SemanticFrontDoorResult`
- `SemanticFreshQueryResult`
- `SemanticFollowUpResult`
- `SemanticReasoningActivationResult`
- `SemanticRepairIntentResult`

Payload-level fallback fields now match the computed runtime metadata envelope for these light-semantic payloads.

## Permanent Test Coverage

Focused tests prove:

- accepted light-semantic result with complete model metadata can still become `strict_ready`
- `invalid_response`, `low_confidence`, `runtime_error`, `not_applicable`, and synthetic follow-up `rejected` cannot become `strict_ready`
- explicit fallback arguments still propagate
- payload-level fallback fields match envelope-level fallback fields
- degraded outcomes remain valid runtime metadata envelopes but are not strict-enforcement ready

## Verification Summary

Required verification was run after the fix:

- Guardrail: PASS
- EC-7C runtime metadata contract tests: PASS
- Light semantic metadata tests: PASS
- C2-C provenance probe checks: PASS
- Fake-Frappe service import: PASS
- Direct assistant append inventory: active direct append count `0`, inventory count `1`, migrated authorized paths `27`
- Scoped AI/governance diff check: PASS
- Excluded stream scan: clean
- Staged files: `0`

## Remaining Notes

Semantic validation still does not forge strict readiness from upstream runtime metadata. Failed compiled-read helper provenance remains visible through the governed-tool runtime metadata envelope.

EC-7F runtime probes should not begin until Counterpart and QA accept this C2-C1 correction.

Final recommendation: `ec_7e_c2_c1_light_semantic_strict_readiness_guard_ready_for_counterpart_review`
## Counterpart Hardening Addendum

Counterpart requested one fail-closed hardening before QA: `semantic_status` is now a required keyword argument on `build_light_semantic_runtime_metadata_bundle(...)`; it no longer defaults to `"accepted"`.

A static AST contract test now scans parseable `qwen_chat` source files and proves every external call to `build_light_semantic_runtime_metadata_bundle(...)` explicitly supplies `semantic_status`. The test intentionally skips the known `manual_uat_evidence.py` BOM parse issue, which is tracked outside EC-7E-C2-C1 and was not modified in this slice.