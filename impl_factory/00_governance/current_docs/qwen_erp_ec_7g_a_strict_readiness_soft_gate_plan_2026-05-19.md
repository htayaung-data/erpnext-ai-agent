# EC-7G-A Strict-Readiness Soft-Gate Plan / Dry-Run Design

Decision: ec_7g_a_strict_readiness_soft_gate_plan_ready_for_counterpart_review

Date: 2026-05-19
Branch: feature/ec-7b0-runtime-import-integrity
Head: 2641458
Staged files: 0

## Scope

EC-7G-A is plan/report only. It defines a strict-readiness soft gate for future dry-run implementation.

No enforcement, runtime blocking, behavior changes, route changes, model changes, answer-text changes, final-answer authority changes, staging, commit, push, deployment, UX, Filter, MI, family expansion, or service refactor were performed.

## Definition: Soft Gate

A soft gate is observe/report only. It does not block a user-facing answer at runtime, does not change routing, does not select or change a model, does not rewrite responses, and does not alter final-answer authority.

The soft gate classifies release readiness from already-emitted metadata and evidence. Its output is a dry-run report used by engineering, Counterpart, QA, and release governance to decide whether strict enforcement can be considered later.

A soft gate may mark a lane as release-blocking, but that means release-readiness blocking only. It must not create a runtime hard block or user-facing refusal.

## Gate Inputs

The future EC-7G dry-run gate should consume only existing evidence surfaces:

- Runtime metadata envelopes: canonical EC-7C `qwen_runtime_metadata_envelope_contract` payloads.
- Model-role observability: `qwen_model_role_observability_contract` where present.
- Model-role strict-readiness contracts: `qwen_model_role_strict_readiness_contract` where present.
- Fallback state: `fallback_used`, `fallback_reason`, degraded semantic status, runtime error state.
- Final-answer authority status: final authority contract, preflight status, answer type, authority source, blocked/emitted state.
- Direct assistant append inventory: active direct append count, low-level wrapper count, migrated authorized paths.
- EC-7F probe closure evidence: lane coverage, probe type, missing metadata behavior, fallback behavior, authority separation behavior.

The gate must not invent authority. Helper/tool provenance is never a substitute for final-answer business authority.

## Soft-Gate Classifications

| Classification | Meaning | Runtime effect | Release readiness impact |
| --- | --- | --- | --- |
| `soft_gate_pass` | Metadata and authority evidence satisfy the expected lane rule. | None | Lane may proceed to soft-gate closure. |
| `soft_gate_warn` | Metadata is present but degraded, fallback, partial, or non-strict in a way that should be reviewed but does not by itself block release. | None | Lane requires release note or follow-up backlog item. |
| `soft_gate_block_release` | Evidence is missing, contradictory, forged/inconsistent, authority failed, direct append inventory regressed, or strict-readiness claims are unsafe. | None | Release readiness is blocked until corrected or explicitly waived by owner/QA. |
| `not_applicable_deterministic` | Deterministic/report or deterministic visible-context lane is explicit, covered, and not an AI strict-enforcement target. | None | Acceptable non-AI state. |
| `not_applicable_control` | Control/meta, policy boundary, trace/debug, or error-fallback lane is explicit and not an AI strict-enforcement target. | None | Acceptable non-AI state unless authority is missing or inconsistent. |

## Lane Rules

### AI Semantic Lanes

Applies to:

- `frontdoor_semantic_classification`
- `fresh_query_interpretation`
- `followup_interpretation`
- `semantic_reasoning_activation`
- `semantic_repair_intent`

Rules:

- Accepted result with complete metadata, role-compatible `light_semantic`, model name present, `fallback_used=False`, compliant role metadata, valid envelope, and EC-7F probe coverage may be `soft_gate_pass`.
- Missing model metadata, fallback, degraded status, low confidence, rejected, invalid, not-applicable, or runtime-error state must not be `strict_ready`; classify as `soft_gate_warn` or `soft_gate_block_release` depending on whether it is expected/degraded or contradictory.
- Any AI semantic envelope claiming `strict_ready` while fallback/degraded/missing metadata is present is `soft_gate_block_release`.
- Semantic classifier metadata is provenance only and cannot satisfy final-answer authority.

### AI Heavy Reasoning

Applies to:

- `business_reasoning_answer`

Rules:

- Complete `heavy_reasoning` provenance can pass the soft gate for provenance if EC-7F authority separation remains green.
- Missing model metadata, fallback, degraded, or runtime-error state is not strict-ready and should warn or block release depending on severity.
- Heavy reasoning metadata must never bypass final-answer authority. Any business answer emitted without final-answer authority is `soft_gate_block_release`.

### Shadow Observer

Applies to:

- `nbu_shadow_observation`

Rules:

- Shadow observer metadata may be strict-ready only for observe-only provenance.
- Shadow output must remain observe-only and must not alter routing or final-answer authority.
- Any shadow metadata used as final-answer authority or as a route-forcing signal is `soft_gate_block_release`.

### Deterministic Report / Visible-Context Lanes

Applies to:

- `compiled_support_result_answer`
- `legacy_runtime_business_or_boundary_answer`
- `artifact_boundary`
- `local_followup_transform`
- `entity_followup`
- `nbu_governed_requery_entity_detail`
- `visible_context_followup` deterministic answer path

Rules:

- Explicit deterministic metadata with valid envelope, role-compatible `deterministic`, `metadata_status=covered`, authority source present, `preflight_status=passed`, and EC-7F coverage is `not_applicable_deterministic`.
- Deterministic/control lanes must not be silently omitted from metadata once wired.
- Deterministic lanes must not claim AI strict-readiness.
- Missing `authority_source`, missing final-answer authority, or blocked final-answer emission is `soft_gate_block_release` for release readiness.

### Policy Boundary Lanes

Applies to:

- `runtime_gate`
- service policy boundary responses
- policy-boundary branches in compiled support, legacy runtime, artifact boundary, and visible context

Rules:

- Valid policy-boundary metadata must use `lane_class=policy_boundary`, `model_role=policy_boundary`, `authority_source=policy_boundary`, and `preflight_status=bounded`.
- Policy-boundary lanes are `not_applicable_control` for AI strict enforcement.
- A bounded policy answer must remain distinct from business factual/report answers.
- Policy-boundary metadata with `preflight_status=passed` or missing boundary authority is `soft_gate_block_release`.

### Control / Trace / Error Fallback Lanes

Applies to:

- `clarification_control`
- `service_policy_control_responses` control/meta paths
- `nbu_safe_response_activation`
- `visible_context_trace_inspection`
- error fallback paths in compiled support, legacy runtime, and entity follow-up

Rules:

- Control/meta metadata must carry explicit `authority_source` such as `control_meta` or `trace_debug`.
- Error fallback metadata must carry explicit non-business `error_fallback` authority and `model_role=not_applicable`.
- These paths are `not_applicable_control` for AI strict enforcement.
- Missing authority source, forged covered status, or user-visible output without explicit control authority is `soft_gate_block_release`.

### Model-Backed Helper / Governed-Tool Runtime Helpers

Applies to:

- `frontdoor_render`
- `clarification_system`
- `artifact_narrative`
- `composite_reads` fallback helper
- `fresh_query_compiled_read_runtime`

Rules:

- Complete helper/tool metadata may be `soft_gate_pass` for helper/tool provenance only.
- Fallback, degraded, runtime-error, `ok=False`, or missing model metadata must not be strict-ready.
- Helper/tool provenance cannot satisfy final-answer business authority.
- Any helper/tool metadata used as final-answer business authority is `soft_gate_block_release`.

### Final-Answer Authority And Direct Append Inventory

Global release-readiness rules:

- Final-answer authority failure always blocks release readiness, even if runtime metadata looks complete.
- Active direct assistant append inventory must remain `0 / 1 / 27`: zero active direct append lanes, one low-level wrapper inventory item, 27 migrated authorized paths.
- Any new active direct assistant append outside authorized emission is `soft_gate_block_release`.
- Raw assistant append scan should remain centralized in `authorized_emission.py` only.

## Future Dry-Run Report Format

The EC-7G dry-run report should emit a stable JSON/Markdown structure. Minimum per-lane fields:

| Field | Description |
| --- | --- |
| `lane_id` | Canonical lane/path id. |
| `lane_class` | Observed EC-7C lane class. |
| `model_role` | Observed EC-7C model role. |
| `expected_lane_class` | Expected lane class from EC-7B/EC-7F closure. |
| `expected_model_role` | Expected role from EC-7C compatibility matrix. |
| `metadata_status` | Observed metadata status. |
| `strict_readiness_status` | Observed strict-readiness status. |
| `strict_enforcement_ready` | Observed boolean from envelope. |
| `fallback_used` | Observed fallback flag. |
| `fallback_reason` | Observed fallback/degraded reason. |
| `role_compliance` | Observed role compliance. |
| `authority_source` | Observed metadata authority source. |
| `final_answer_authority_status` | Passed, bounded, missing, blocked, or not-applicable. |
| `final_answer_authority_source` | Source from final-answer authority if applicable. |
| `preflight_status` | Final-answer / metadata preflight status. |
| `probe_evidence_slice` | EC-7F slice proving this lane. |
| `observed_metadata` | Compact metadata excerpt. |
| `expected_metadata` | Expected class/role/status/fallback/authority pattern. |
| `soft_gate_decision` | One of the classifications above. |
| `reason` | Human-readable reason. |
| `release_readiness_impact` | Pass, warning, release-blocking, or not-applicable. |
| `runtime_effect` | Must always be `none` for EC-7G soft gate. |

Suggested top-level report fields:

- `slice_id`
- `branch`
- `head`
- `generated_at`
- `runtime_effect: none`
- `strict_enforcement_enabled: false`
- `summary_counts`
- `direct_assistant_append_inventory`
- `raw_assistant_append_scan`
- `probe_closure_evidence`
- `lane_results`
- `release_blockers`
- `warnings`
- `non_goals`

## Initial Lane Decision Expectations

Based on EC-7F closure, initial EC-7G dry-run should start with these expected decisions:

| Lane group | Expected initial soft-gate decision |
| --- | --- |
| Accepted complete AI semantic metadata | `soft_gate_pass` |
| AI missing/fallback/degraded/runtime-error metadata | `soft_gate_warn` if expected degraded path; `soft_gate_block_release` if contradictory strict-ready claim appears |
| Heavy reasoning complete provenance | `soft_gate_pass` for provenance only |
| NBU shadow complete provenance | `soft_gate_pass` for observe-only provenance |
| Deterministic report/visible-context lanes | `not_applicable_deterministic` |
| Policy boundary/control/trace/error lanes | `not_applicable_control` |
| Helper/tool runtime complete provenance | `soft_gate_pass` for helper/tool provenance only |
| Helper/tool fallback/missing/runtime-error | `soft_gate_warn` unless it claims strict-ready or grants authority, then `soft_gate_block_release` |
| Final-answer authority failure | `soft_gate_block_release` |
| Direct assistant append regression | `soft_gate_block_release` |

## Required Verification For Future EC-7G-B Implementation

When EC-7G-B implements the dry-run report, run at minimum:

```bash
python3 scripts/check_qwen_enterprise_guardrails.py

PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest -q \
  ai_assistant_ui.tests.test_runtime_metadata_contract \
  ai_assistant_ui.tests.test_light_semantic_runtime_metadata_contracts \
  ai_assistant_ui.tests.test_light_semantic_runtime_probes \
  ai_assistant_ui.tests.test_heavy_shadow_runtime_metadata_contracts \
  ai_assistant_ui.tests.test_heavy_reasoning_nbu_shadow_runtime_probes \
  ai_assistant_ui.tests.test_model_backed_helper_metadata_wiring \
  ai_assistant_ui.tests.test_governed_tool_runtime_metadata_wiring \
  ai_assistant_ui.tests.test_service_validator_provenance_probes \
  ai_assistant_ui.tests.test_helper_tool_runtime_probes \
  ai_assistant_ui.tests.test_deterministic_control_runtime_metadata_probes

PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest -q \
  ai_assistant_ui.tests.test_authorized_emission_contracts
```

Also verify:

- Fake-Frappe service import: PASS.
- Direct assistant append inventory remains `0 / 1 / 27`.
- Raw assistant append scan remains only `authorized_emission.py:271` and `authorized_emission.py:327`.
- Scoped diff check passes.
- Excluded scans via both `git diff --name-only` and `git status --short` are clean.
- Staged files remain `0` unless a later packaging gate explicitly approves staging.

## Non-Goals

- No strict enforcement.
- No runtime blocking.
- No model-role hard gate.
- No route/model/answer/report-selection changes.
- No service.py refactor.
- No production UAT claim.
- No live ERP/browser validation claim.
- No staging, commit, push, or deployment.
- No ERP UI, seed/data/temp/probe/cache, PrimeAxis docs, UX, Filter, MI, or family expansion.

## Recommendation

EC-7G-A soft-gate planning is ready for Counterpart and QA review.

If accepted, proceed only to EC-7G-B dry-run report implementation. EC-7G-B should remain observe/report only and must not introduce runtime hard enforcement.
