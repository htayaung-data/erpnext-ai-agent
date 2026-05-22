# EC-7H-B Trace Fixture And Redaction Protocol

Decision: ec_7h_b_d_extra_metadata_enum_constraint_ready_for_counterpart_review

Date: 2026-05-20
Generated: 2026-05-21T00:35:00+00:00
Base: `main` post-PR #4 verification worktree
Head: `1504158`
Runtime effect: `none`
Strict enforcement enabled: `false`
Deployment performed: `false`
Staging/commit/push performed: `false`

## Purpose

EC-7H-B defines a safe trace fixture and redaction protocol before any live trace collection. It adds a passive validation harness for trace artifact shape, redaction, storage policy, and schema checks. It does not collect live traces and does not change runtime behavior.

## Files Added For Review

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/live_trace_evidence_protocol.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_live_trace_evidence_protocol.py`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_7h_b_trace_fixture_redaction_protocol_2026-05-20.md`

The protocol module is intentionally passive. It does not import Frappe, does not register runtime hooks, and does not participate in routing, final-answer authority, model selection, answer rendering, or strict enforcement.

## Trace Artifact Schema

Each EC-7H live trace fixture must include these fields or a documented missing reason during validation:

| Field | Purpose |
|---|---|
| `trace_id` | Synthetic or redacted trace identifier. |
| `session_id_hash` | Hashed session identifier; raw session IDs are not allowed. |
| `request_id_hash` | Hashed request identifier; raw request IDs are not allowed. |
| `scenario_id` | Stable EC-7H scenario identifier. |
| `lane_id` | Runtime lane being evidenced. |
| `lane_class` | EC-7C lane class. |
| `model_role` | EC-7C model role. |
| `model_name` | Runtime model identity or `unknown` if missing. |
| `fallback_used` | Whether fallback/degraded path was used. |
| `fallback_reason` | Fallback/degradation reason; may be empty for non-fallback success. |
| `role_compliance` | Role compliance status. |
| `metadata_status` | Runtime metadata coverage status. |
| `strict_readiness_status` | Soft strict-readiness status. |
| `strict_enforcement_ready` | Boolean readiness flag; evidence only. |
| `runtime_probe_required` | Whether further runtime probe is required. |
| `metadata_source` | Source of metadata envelope/provenance. |
| `authority_source` | Runtime authority source. |
| `final_answer_authority_status` | Final-answer authority status. |
| `final_answer_authority_source` | Final-answer authority source. |
| `preflight_status` | Final-answer preflight status. |
| `answer_type` | Final-answer or metadata answer type. |
| `authorized_emission.emitted` | Whether authorized assistant emission occurred. |
| `authorized_emission.blocked` | Whether authorized emission blocked output. |
| `authorized_emission.block_reason` | Block reason, empty for non-blocked success. |
| `payload_order_summary` | Redacted structural order of relevant payloads. |
| `assistant_message_count_delta` | Assistant message delta for the scenario. |
| `tool_payload_count_delta` | Tool/audit payload delta for the scenario. |
| `leak_check_result` | No-leak validation result. |
| `redaction_status` | `redacted` or `not_sensitive`. |

## EC-7H-B-A Redaction Hardening

Counterpart found that raw identifier/entity keys such as `session_id`, `request_id`, `customer`, `vendor`, and `invoice_id` could pass validation when supplied as extra fields. EC-7H-B-A hardens the protocol so raw identifier/entity/document keys are sensitive unless they are the explicitly allowed hash fields `session_id_hash` and `request_id_hash`.

Additional sensitive keys now include close variants such as `supplier`, `docname`, `document_name`, `entity`, and `party`, including nested dictionaries and list payloads. The adversarial test suite now proves raw identifier/entity keys are invalid before redaction and valid after redaction.

## EC-7H-B-B Strict Schema Allowlist

QA found that arbitrary unknown fields could still carry raw business text under generic keys such as `evidence`, `payload.value`, or `raw_payload`. EC-7H-B-B closes that gap by making the fixture schema allowlist explicit:

- unknown top-level fields fail validation by default;
- `unknown_field_violations` and `schema_violations` are reported by the validator;
- redaction removes unknown top-level fields from the shareable fixture shape;
- only `extra_metadata` is allowed as a controlled extension container;
- `extra_metadata` is recursively validated and redacted for high-risk keys and raw business-text markers;
- canonical schema fields such as `model_name`, `metadata_source`, `authority_source`, and `payload_order_summary` remain allowed and are not falsely rejected just because their names contain `model`, `source`, or `payload`.

This remains a passive evidence protocol only. It does not collect live traces, enforce strict readiness, block runtime behavior, or change answer output.

## EC-7H-B-C Extra Metadata Redaction Hardening

QA found that the controlled `extra_metadata` container was still too permissive for generic scalar strings. Values such as `{"note": "Yoma Bank"}` or `{"owner": "Global Trading Ltd"}` could validate unless they matched a known raw-business marker. EC-7H-B-C changes `extra_metadata` to safe-by-default:

- only explicitly allowlisted keys may carry non-redacted synthetic scalar values;
- allowed keys are `fixture_version`, `attempt`, `synthetic`, `capture_version`, `schema_version`, `probe_variant`, and `reviewer_note_classification`;
- synthetic string values must use constrained token-like values and must not look like raw business text;
- numeric/bool values are accepted only for explicitly safe keys such as `attempt` and `synthetic`;
- any non-allowlisted string under `extra_metadata` must be `<redacted>`;
- nested `extra_metadata` dictionaries/lists follow the same recursive rule;
- high-risk keys such as `payload`, `source`, `value`, and `raw` still require redaction.

The adversarial tests now prove raw generic entity/customer/vendor-like strings are invalid before redaction, are redacted into a safe shape, and validate only after redaction.

## EC-7H-B-D Extra Metadata Enum Constraint

Counterpart found one remaining gap in EC-7H-B-C: allowlisted `extra_metadata` string keys still accepted arbitrary token-like values, so entity names such as `Yoma_Bank` or `GlobalTradingLtd` could fit the token regex. EC-7H-B-D removes broad token acceptance and replaces it with explicit safe constraints:

- `fixture_version`, `schema_version`, and `capture_version` must be numeric or `v`-prefixed numeric versions, such as `1`, `1.0`, or `v1`;
- `probe_variant` must be one of `success`, `fallback`, `runtime_error`, `missing_metadata`, `blocked_authority`, or `boundary`;
- `reviewer_note_classification` must be one of `none`, `synthetic`, `redacted`, or `qa_note`;
- `attempt` remains integer-only;
- `synthetic` remains boolean-only;
- values outside those constraints fail unless already set to `<redacted>`.

The new tests prove `probe_variant="Yoma_Bank"` and `fixture_version="GlobalTradingLtd"` fail validation before redaction, redact to `<redacted>`, and validate only after redaction.

## Redaction Rules

The protocol redacts fields whose keys indicate sensitive content, including:

- `user_text`
- `message_text`
- `answer_text`
- `assistant_text`
- `raw_answer`
- `raw_message`
- `model_output`
- `raw_model`
- `prompt`
- `source_text`
- `rendered_response`
- `session_id`
- `request_id`
- `customer`
- `vendor`
- `supplier`
- `invoice_id`
- `docname`
- `document_name`
- `entity`
- `party`
- `entity_name`
- `customer_name`
- `vendor_name`
- `document_id`
- `monetary_value`
- `freeform`

Redaction replaces sensitive values with `<redacted>` and preserves structural metadata needed for QA review. Hash identifiers such as `session_id_hash` and `request_id_hash` must remain present and must not be blank or redacted.

Unknown top-level fields are not preserved in redacted fixtures. If future trace evidence needs additional metadata, it must use `extra_metadata` and remain synthetic/redacted-safe under recursive validation.

## Safe Fixture Format

Safe fixtures are dictionaries containing only redacted/synthetic values. They may be used in tests and governance reports if they satisfy:

- all required schema fields present;
- only allowlisted top-level fields are present;
- `redaction_status` is `redacted` or `not_sensitive`;
- no sensitive field contains raw text;
- `extra_metadata`, when present, contains only allowlisted enum/version synthetic-safe scalar values or recursively redacted nested values;
- session/request identifiers are hashed;
- runtime effect remains `none`;
- no live trace collection is required to run validation.

The helper `build_minimal_redacted_live_trace_fixture(...)` creates a synthetic valid fixture for schema tests only.

## Validation Checks

The harness validates:

- missing required fields, including dotted nested fields such as `authorized_emission.emitted`;
- redaction status;
- sensitive key violations;
- unknown top-level field violations;
- schema violations, including unsafe `extra_metadata` content;
- blank/redacted hash identifiers;
- storage policy constants;
- runtime effect remains `none`.

The validator reports evidence quality only. It must not block runtime execution.

## Storage Policy Proposal

| Artifact type | Storage policy |
|---|---|
| Schema and redaction protocol | `repo_governance_doc` |
| Synthetic redacted fixture | `repo_allowed` |
| Redacted live trace summary | `repo_or_qa_archive_with_owner_approval` |
| Raw live trace | `external_secure_archive_only` |
| Unredacted sensitive trace | `not_versioned` |

Bundle/packaging implication: raw live traces, unredacted traces, and sensitive artifacts must not be committed. Future redacted live trace summaries require explicit owner/QA approval before repo inclusion.

## Test Coverage

Focused schema/redaction tests added:

- valid minimal redacted fixture with runtime effect `none`;
- missing required field detection;
- sensitive text redaction while preserving metadata;
- unredacted sensitive field rejection;
- hash identifier validation;
- raw identifier/entity/document keys are invalid before redaction;
- unknown top-level fields carrying raw business text fail validation;
- `evidence`, `payload.value`, and `raw_payload` cannot validate with raw content;
- redaction removes unknown top-level fields into a safe fixture shape;
- `extra_metadata` accepts safe synthetic scalars but rejects/redacts unsafe nested content;
- generic `extra_metadata.note` and `extra_metadata.owner` raw strings fail until redacted;
- nested generic strings under `extra_metadata` fail until redacted;
- generic numeric/bool values are accepted only under explicitly safe keys;
- allowlisted string keys reject entity-like token values such as `Yoma_Bank` and `GlobalTradingLtd` unless redacted;
- storage policy assertions.

Test command:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest -q ai_assistant_ui.tests.test_live_trace_evidence_protocol
```

Expected result after EC-7H-B-D hardening: `17 passed`.

## Required Verification

EC-7H-B verification should show:

- Guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: `0 / 1 / 27`
- Formal raw assistant append scan: only `authorized_emission.py:271` and `authorized_emission.py:327`
- Excluded status scan: clean
- Schema/redaction tests: `17 passed`
- Staged files: `0`

## Non-Goals

- `no_live_trace_collection`
- `no_strict_enforcement`
- `no_runtime_blocking`
- `no_deployment`
- `no_runtime_behavior_change`
- `no_route_model_report_selection_change`
- `no_answer_text_change`
- `no_cleanup`
- `no_ux_filter_mi_family_expansion`
- `no_commit_or_push`

## Final Recommendation

`ec_7h_b_d_extra_metadata_enum_constraint_ready_for_counterpart_review`

If accepted, Counterpart and QA can decide whether EC-7H-C live trace collection planning may begin. No live trace collection, strict enforcement, deployment, staging, commit, or runtime behavior change is approved by EC-7H-B-D.
