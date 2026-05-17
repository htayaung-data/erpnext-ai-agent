# EC-6B-A AI Package Dependency Closure Correction

## Executive Decision

Recommendation:

`ec_6b_a_dependency_closure_correction_ready_for_counterpart_review`

EC-6B-A corrects the EC-6B package boundary so allowed AI Assistant source files are not packaged without dirty dependency files they require. This is a manifest/evidence correction only. It performs no staging, commit, cleanup, delete, move, archive, `.gitignore` change, runtime behavior change, ERP UI work, UX work, Filter work, MI work, family expansion, model-role strict enforcement, or broad `service.py` refactor.

## Baseline

- Branch: `feature/ai-assistant`
- Head: `154be1e`
- Pre-EC-6B-A dirty count: `316`
- Dirty count after adding this EC-6B-A note and EC-6B pointer update: `317`
- Count explanation: EC-6B already existed as an untracked governance document, so adding the EC-6B pointer did not create a new status entry. EC-6B-A added one new governance document.
- Dependency scan result: `69` direct dirty-dependency edges from the EC-6B allowed source set
- Unique dirty dependency files imported by EC-6B allowed source set: `17`

## Blocking Finding Resolved

EC-6B allowed `authorized_emission.py` but excluded `contracts.py`. That is not packaging-safe.

Current dirty `contracts.py` adds:

- `FinalAnswerAuthorityContract`
- `build_final_answer_authority_contract`
- `authority_context` parameter on `build_audit_envelope`
- `final_answer_authority` field in the audit envelope payload

Current `authorized_emission.py` calls `build_audit_envelope(..., authority_context=...)`. In HEAD, `build_audit_envelope` does not accept `authority_context`. Therefore, `contracts.py` must be promoted into the allowed shared S7/EC authority dependency bundle.

## Revised Dependency Closure Table

| Allowed source file examples | Imported dirty file originally not allowed | Dirty change required for allowed package? | Decision | Reason |
|---|---|---|---|---|
| `authorized_emission.py`; migrated runtime lanes; `visible_context_followup_activation.py`; `service.py` | `qwen_chat/contracts.py` | yes | `promote_to_allowed_shared_s7_ec_dependency` | Hard API dependency. Authorized emission requires dirty final-answer authority contract and `build_audit_envelope(..., authority_context=...)`. |
| manual UAT modules; model-role modules; NBU activation; visible-context modules | `qwen_chat/natural_business_understanding_contracts.py` | yes | `promote_to_allowed_shared_s7_ec_dependency` | Dirty context-resolution fields support selected report family/entity/artifact traceability used by S7/EC authority evidence. |
| `visible_context_followup_activation.py`; `visible_context_trace_inspection.py` | `qwen_chat/visible_context_frame_stack.py` | yes | `promote_to_allowed_shared_s7_ec_dependency` | Dirty frame-stack arbitration and requested-limit metadata are part of S7 visible-context authority stabilization. |
| `visible_context_followup_activation.py`; `natural_business_understanding_governed_requery_activation.py` | `qwen_chat/natural_business_understanding_context_graph.py` | yes | `promote_to_allowed_shared_s7_ec_dependency` | Dirty selected-artifact trace fields are paired with the NBU context-resolution contract additions and support authority traceability. |
| `visible_context_followup_activation.py`; `natural_business_understanding_governed_requery_activation.py`; `service.py` | `qwen_chat/natural_business_understanding_request_classification.py` | yes | `promote_to_allowed_shared_s7_ec_dependency` | Dirty visible-context request classification supports correct visible-context vs governed-requery authority routing. |
| `visible_context_followup_activation.py` | `qwen_chat/visible_context_boundary_language.py` | yes | `promote_to_allowed_shared_s7_ec_dependency` | Dirty visible-context boundary wording/rendering is part of S7/EC authority-boundary behavior. |
| `artifact_boundary_lane.py`; `clarification_lane.py`; `reasoning_lane.py`; `runtime_gate_lane.py`; `service.py` | `qwen_chat/knowledge_boundary.py` | yes | `promote_to_allowed_shared_s7_ec_dependency` | Policy-boundary rendering is an authority surface for migrated lanes. Excluding its dirty behavior would make the package boundary inconsistent with current policy-boundary verification. |
| `artifact_boundary_lane.py`; `runtime_gate_lane.py`; `service.py` | `qwen_chat/boundary_support.py` | yes | `promote_to_allowed_shared_s7_ec_dependency_hunk_aware` | Artifact/direct-evidence boundary behavior is used by migrated artifact and runtime gate paths. This remains hunk-aware because the file has a broad diff footprint. |
| `clarification_lane.py`; `service.py` | `qwen_chat/clarification_resolution.py` | yes | `promote_to_allowed_shared_s7_ec_dependency` | Clarification/control decisions are answer-surface authority behavior after EC-4T. |
| `compiled_support.py`; `lanes/frontdoor_lane.py`; `service.py` | `qwen_chat/clarification_translation.py` | yes | `promote_to_allowed_shared_s7_ec_dependency` | Clarification text translation feeds approved control/meta and compiled/frontdoor outputs. |
| `lanes/frontdoor_lane.py`; `clarification_lane.py` | `qwen_chat/frontdoor_intent_gate.py` | conditional | `promote_to_allowed_shared_s7_ec_dependency_hunk_aware` | Active package frontdoor lane depends on this module. Keep hunk-aware because some dirty behavior may predate EC-4. |
| `service.py` | `qwen_chat/assistant_formatting.py` | no direct package API dependency found | `keep_excluded_with_proof` | Imported symbols exist in HEAD; dirty changes are formatting behavior and are not required for the EC-4 authority package boundary. |
| `service.py` | `qwen_chat/context/grounded_context.py` | no direct package API dependency found | `keep_excluded_with_proof` | Imported symbols exist in HEAD; dirty change is not required by EC-4 authorized emission packaging. |
| `service.py` | `qwen_chat/followup_interpreter.py` | no direct package API dependency found | `keep_excluded_with_proof` | Imported symbol exists in HEAD; dirty change is not required by EC-4 authorized emission packaging. |
| `runtime_gate_lane.py`; `service.py` | `qwen_chat/fresh_query_interpreter.py` | not for EC-6B package | `separate_ai_infrastructure_bundle` | Dirty behavior is broad fresh-query/model-role/limit seeding. Imported API exists in HEAD, so do not pull this into the EC-6B authority package unless owner approves a fresh-query package. |
| `service.py` | `qwen_chat/natural_business_understanding_service_activation.py` | not for EC-6B package | `separate_ai_infrastructure_bundle` | Dirty behavior is broader NBU service activation/presentation logic. It should be packaged with NBU infrastructure, not forced into EC-6B. |
| `service.py` | `qwen_chat/scope_support.py` | not for EC-6B package | `separate_ai_infrastructure_bundle` | Dirty behavior is broader scope/reasoning arbitration. It is not required to make the EC-4 authority package import-safe. |

## Additional Transitive Dependency Note

If the `separate_ai_infrastructure_bundle` files are later promoted, they introduce additional dirty dependencies such as `family_adapters.py`, `governed_report_executor.py`, `natural_business_understanding_runtime.py`, `natural_business_understanding_quality_standard.py`, `natural_business_understanding_response_renderer.py`, and `natural_business_understanding_schema_hardening.py`. EC-6B-A does not promote those broad runtime stacks into the AI authority package.

## Revised Allowed Shared Dependency Addendum

The following files are removed from the EC-6B “not allowed without separate owner decision” bucket and added to the allowed shared S7/EC dependency boundary:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_frame_stack.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_context_graph.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_request_classification.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_boundary_language.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/knowledge_boundary.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/boundary_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/clarification_resolution.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/clarification_translation.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_intent_gate.py`

Files marked `hunk_aware` still require hunk-level packaging discipline. This correction allows them into the package boundary; it does not approve whole-file staging.

## Still Excluded Or Separate

These direct dirty imports remain outside the EC-6B authority package unless a later owner-approved bundle includes them:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/assistant_formatting.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/context/grounded_context.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/followup_interpreter.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_service_activation.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/scope_support.py`

## Verification Results

- Guardrail: `PASS`
- Scoped AI diff check: `PASS`
- Source scan using `build_final_answer_emission_dry_run_report(reviewer="codex_ec6b_a_source_scan", status_count=317)`: `active_runtime_direct_assistant_append_count=0`, `inventory_count=1`, `migrated_authorized_paths` length `27`
- Visible-context suite: `90 passed`
- NBU suite: `159 passed`
- Final-authority / emission tests: `47 passed`
- Semantic financial suite: `276 passed`

## Final Recommendation

`ec_6b_a_dependency_closure_correction_ready_for_counterpart_review`

EC-6B-A corrects the dependency-boundary error without changing runtime behavior. EC-6C must not start until Counterpart accepts this revised dependency closure.
