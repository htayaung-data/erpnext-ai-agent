# EC-7B Runtime Metadata Coverage Inventory

Date: 2026-05-17
Worktree: `/tmp/erpai_ec7b0_import_integrity`
Branch: `feature/ec-7b0-runtime-import-integrity`
HEAD: `2641458`
Scope: investigation/report only
Runtime behavior changed by EC-7B: `False`
Staging/commit/push: `none`

## Executive Decision

`ec_7b_metadata_coverage_inventory_ready_for_counterpart_review`

EC-7B found no new runtime-import or final-answer-emission blocker. EC-4 final-answer authority is broadly present through the authorized emission helper, and active direct assistant append inventory remains clean. The important finding is that model-role metadata is uneven: visible-context and reasoning lanes already have strong model-role contracts, while several deterministic/control/report lanes carry final-answer authority but not normalized model-role observability/readiness metadata. Strict model-role enforcement is therefore not safe yet.

## Scope Guard

This slice did not add model-role wiring, strict enforcement, service refactor, cleanup, staging, commit, push, UX, Filter, MI, or family expansion. This is a baseline map for EC-7C+ only.

## Metadata Legend

Model-role fields: `model_role`, `model_name`, `fallback_used`, `fallback_reason`, `role_compliance`.

Authority fields: `authority_source`, `evidence_scope`, `answer_mode`, `preflight_status`.

Recommendations:

- `covered`: requested metadata is present for the current lane purpose.
- `partial`: final authority or runtime metadata is present, but normalized model-role coverage is incomplete.
- `missing`: expected metadata is absent or only raw `agent_meta` exists.
- `not_applicable_deterministic`: deterministic lane is audited and should remain outside AI strict enforcement.
- `needs_runtime_probe`: source has hooks, but runtime completeness must be proven before enforcement.

## Inventory Matrix

| Lane/path | Entry point | Lane class | Expected model role | Current metadata present | Missing metadata | Metadata source | Strict safe now | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `frontdoor_semantic_classification` | `qwen_chat/frontdoor_intent_gate.py::SemanticFrontDoorResult.to_payload` | AI semantic | `light_semantic` | Model-role fields are built when `agent_meta` exists; strict readiness contract is generated; answer authority is downstream. | Runtime probe needed for `model_name` and fallback completeness when `agent_meta` is absent or incomplete. | Runtime `agent_meta` converted by `build_model_role_contract_bundle`. | No, not until runtime metadata is proven for all frontdoor outcomes. | `partial`, `needs_runtime_probe` |
| `frontdoor_governed_report_answer` | `qwen_chat/lanes/frontdoor_lane.py::handle_frontdoor_turn` | deterministic/report + policy/control | `deterministic` for governed report answers; control/policy where applicable | Final-answer authority fields are built through `emit_authorized_assistant_answer` and `_frontdoor_authority_context`. | No normalized model-role observability is attached at the frontdoor answer emission layer. | Final-answer authority helper plus frontdoor authority context. | No. Authority is safe; model-role coverage is partial. | `partial` |
| `fresh_query_interpretation` | `qwen_chat/fresh_query_interpreter.py::interpret_fresh_query_semantically` | AI semantic | `light_semantic` | Raw runtime `agent_meta` is captured; fallback merge metadata exists. | No model-role observability/readiness contract is emitted from the semantic result; strict fields are not normalized. | Runtime response `agent_meta`; fallback metadata merge. | No. | `missing`, `needs_runtime_probe` |
| `followup_interpretation` | `qwen_chat/semantic_interpreter.py::interpret_followup_semantically`; deterministic resolver in `qwen_chat/followup_interpreter.py` | AI semantic plus deterministic resolver | `light_semantic` for semantic interpreter; `deterministic` for resolver | Raw runtime `agent_meta`, `fallback_used`, and `fallback_reason` appear in semantic follow-up payload; deterministic resolver has no AI runtime. | No normalized model-role observability/readiness contract on semantic follow-up payload. | Runtime `agent_meta`; deterministic resolver contracts. | No for semantic interpreter; deterministic resolver can be `not_applicable` after explicit contract. | `partial`, `needs_runtime_probe` |
| `visible_context_followup` | `qwen_chat/visible_context_followup_activation.py::try_activate_visible_context_followup_response`; `_emit_authorized_visible_context_answer` | deterministic visible context | `deterministic` | Model-role fields, strict-readiness, policy model-role, model-role coverage, final-answer authority fields, and authorized emission metadata are present. | None for current deterministic lane. | Deterministic construction plus visible-context trace and final-answer authority helper. | Yes as `not_applicable_deterministic`, not as AI strict enforcement. | `covered`, `not_applicable_deterministic` |
| `visible_context_trace_inspection` | `qwen_chat/visible_context_trace_inspection.py::try_handle_visible_context_trace_inspection` | deterministic trace/debug | `deterministic` | Model-role fields, strict-readiness, final-answer authority extraction, trace inspection contract, and trace/debug authorized emission are present. | None for current deterministic trace lane. | Deterministic construction plus latest trace/final-authority contract. | Yes as `not_applicable_deterministic`. | `covered`, `not_applicable_deterministic` |
| `erp_report_execution` | Turn-level trace publication in `visible_context_trace_inspection.py`; report answer paths in `compiled_support.py`, `legacy_runtime_lane.py`, `frontdoor_lane.py` | deterministic ERP report | `deterministic` | Turn-level trace publication has deterministic model-role and final-answer authority. Report answer emissions have final-answer authority. | Model-role observability is not uniformly attached across compiled/frontdoor/legacy report emissions. | Deterministic trace contracts and final-answer authority helper. | Partially. Trace publication is safe; all report answer emitters need normalized deterministic contracts before global strict readiness. | `partial` |
| `policy_boundary_rendering` | `visible_context_followup_activation.py`; `runtime_gate_lane.py`; service policy-boundary helper; reasoning/compiled/artifact boundaries | deterministic policy | `deterministic` | Visible-context policy renderer has deterministic model-role bundle; all migrated policy answers use final-answer authority with bounded preflight. | Runtime gate, service boundary, compiled/reasoning/artifact boundary paths do not uniformly emit normalized model-role observability. | Deterministic policy contracts where present; final-answer authority helper. | Partially; not globally safe until every policy boundary path has explicit deterministic/not-applicable role metadata. | `partial` |
| `business_reasoning_answer` | `qwen_chat/lanes/reasoning_lane.py::try_handle_reasoning_lane` | AI reasoning | `heavy_reasoning` | Model-role fields and strict readiness are built from runtime `agent_meta`; final-answer authority is present; returned payload includes authorized emission. | Runtime probe needed to prove `model_name` and fallback completeness across success and guardrail outcomes. | Runtime `agent_meta`, `build_model_role_contract_bundle`, final-answer authority helper. | Not yet. Source is wired, but strict enforcement needs runtime coverage proof. | `covered`, `needs_runtime_probe` |
| `nbu_shadow_observation` | `qwen_chat/natural_business_understanding_service_activation.py::build_nbu_always_on_shadow_trace`; `natural_business_understanding_runtime.py::interpret_natural_business_understanding_shadow` | shadow observer | `shadow_observer` | Shadow trace, always-on shadow audit, and observe-only activation metadata are present. | No normalized model-role observability/readiness contract for the NBU shadow runtime call. | NBU shadow trace contracts and runtime response interpretation. | No. | `missing`, `needs_runtime_probe` |
| `nbu_safe_response_activation` | `qwen_chat/natural_business_understanding_service_activation.py::try_activate_nbu_response` | control/shadow-safe response | `not_applicable` or `shadow_observer` depending final EC-7 policy | Control authority and final-answer authorization are present. | No normalized model-role contract; no strict readiness field. | Control meta authority plus NBU activation/audit payloads. | No until lane policy is decided: control-only exemption or shadow-observer metadata. | `partial` |
| `nbu_governed_requery_entity_detail` | `qwen_chat/natural_business_understanding_governed_requery_activation.py::try_activate_nbu_governed_requery_response` | deterministic governed report from NBU plan | `deterministic` | Final-answer authority fields are present through normalized family artifact; runtime trace has `agent_meta.engine`. | No normalized deterministic model-role observability/readiness contract. | Final-answer authority helper plus artifact authority context. | No, pending deterministic metadata contract. | `partial` |
| `compiled_support_result_answer` | `qwen_chat/compiled_support.py::handle_compiled_support_result` | deterministic governed report / clarification / boundary | `deterministic` or `not_applicable` control | Final-answer authority fields are present; answer type differentiates governed report, policy boundary, and control. | No normalized model-role observability/readiness contract on compiled support emissions. | Final-answer authority helper plus compiled authority context. | No, pending deterministic/control metadata contract. | `partial` |
| `legacy_runtime_business_or_boundary_answer` | `qwen_chat/lanes/legacy_runtime_lane.py::try_handle_legacy_runtime_lane` | runtime report / policy / error fallback | `deterministic` for grounded report; `not_applicable` for error fallback | Final-answer authority fields are present; runtime trace contains basic `agent_meta.engine/mode`; blocked answer text is suppressed. | No normalized model-role observability/readiness contract. | Runtime trace payload and final-answer authority helper. | No. | `partial`, `needs_runtime_probe` |
| `local_followup_transform` | `qwen_chat/local_followup_support.py::handle_local_grounded_transform` | deterministic visible-context transform | `deterministic` | Final-answer authority fields are present through normalized family artifact; local transform trace is staged through authorized emission. | No normalized deterministic model-role observability/readiness contract. | Final-answer authority helper plus local transform trace. | No, pending deterministic metadata contract. | `partial` |
| `artifact_boundary` | `qwen_chat/lanes/artifact_boundary_lane.py::try_handle_artifact_boundary_lane` | deterministic governed report / policy boundary | `deterministic` | Final-answer authority fields are present for evidence answer and boundary responses. | No normalized model-role observability/readiness contract. | Final-answer authority helper plus artifact or knowledge-boundary authority context. | No, pending deterministic metadata contract. | `partial` |
| `runtime_gate` | `qwen_chat/lanes/runtime_gate_lane.py::try_handle_runtime_gate` | deterministic policy boundary | `deterministic` | Final-answer authority fields are present with bounded policy authority. | No normalized model-role observability/readiness contract. | Runtime-gate trace and final-answer authority helper. | No, pending deterministic metadata contract. | `partial` |
| `entity_followup` | `qwen_chat/entity_followup_support.py::try_entity_detail_followup` | deterministic governed report / error fallback | `deterministic` for entity detail; `not_applicable` for error | Final-answer authority fields are present; runtime trace has basic `agent_meta.engine/mode`. | No normalized model-role observability/readiness contract. | Runtime trace and final-answer authority helper. | No, pending deterministic/control metadata contract. | `partial` |
| `clarification_control` | `qwen_chat/lanes/clarification_lane.py::try_handle_clarification_lane` | control/meta | `not_applicable` | Control authority and authorized emission metadata are present. | No explicit model-role not-applicable/control contract. | Control meta authority plus authorized emission helper. | No, pending explicit exemption contract. | `partial` |
| `service_policy_control_responses` | `qwen_chat/service.py::_emit_service_policy_boundary_answer`; `_emit_service_control_answer` | policy/control | `deterministic` for policy boundary; `not_applicable` for control | Final-answer authority fields are present through service authorized-emission helpers. | No normalized model-role observability/readiness contract on service-level control/policy paths. | Final-answer authority helper; service control/policy payloads. | No, pending deterministic/control metadata contract. | `partial` |

## Coverage Summary

- Final-answer authority coverage: strong for migrated answer emitters. Business, policy, control, trace, and error emissions now pass through `emit_authorized_assistant_answer`.
- Model-role coverage: strong in visible-context follow-up, visible-context trace inspection, frontdoor semantic payloads, and reasoning lane; weak or absent in fresh query, follow-up interpretation, NBU shadow observation, and most deterministic/control/report answer lanes.
- Strict enforcement readiness: not globally safe. AI lanes need runtime probes for `model_name`, `fallback_used`, and `fallback_reason`; deterministic/control lanes need explicit deterministic or not-applicable contracts before strict readiness can be represented honestly.
- Direct assistant append state: active runtime direct assistant append count is `0`; migrated authorized path count is `27`; residual inventory is the low-level wrapper only.

## Recommended EC-7 Sequence

1. `EC-7C Deterministic/Control Metadata Normalization`: add explicit deterministic or not-applicable model-role contracts to ERP report execution, policy boundary rendering, compiled support, legacy runtime, local follow-up, artifact boundary, runtime gate, entity follow-up, clarification, and service-level control/policy paths. No strict enforcement.
2. `EC-7D AI Runtime Metadata Provenance`: normalize `model_name`, `fallback_used`, and `fallback_reason` from frontdoor, fresh query, follow-up semantic interpretation, reasoning, and NBU shadow runtime calls. No strict enforcement.
3. `EC-7E Runtime Probe Suite`: add probes proving metadata completeness by lane and answer outcome, including fallback/error paths.
4. `EC-7F Strict Readiness Gate`: create a dry-run gate that reports which lanes are strict-ready, soft-blocked, or explicitly not applicable.
5. `EC-7G Strict Soft Enforcement Proposal`: only after Counterpart and QA review, decide whether release-promotion blocking or runtime soft-block is appropriate. Hard runtime enforcement remains deferred until coverage is complete.

## Verification Snapshot

Pre-report baseline:

- Branch/head: `feature/ec-7b0-runtime-import-integrity` / `2641458`
- Staged files before report: `0`
- Short status entries before report: `48`
- Excluded stream status scan: no ERP UI, seed/data, temp/probe/cache, or PrimeAxis entries touched by EC-7B.

Verification commands run during EC-7B inventory:

- `python3 scripts/check_qwen_enterprise_guardrails.py`: `PASS`
- Fake-Frappe import probe for `ai_assistant_ui.qwen_chat.service`: `PASS`
- Final-answer emission dry-run source scan: `active_runtime_direct_assistant_append_count=0`, `inventory_count=1`, `migrated_authorized_paths_length=27`, `authorized_runtime_append_sink_count=2`, `excluded_non_runtime_append_count=1`
- Raw `append_message(session_doc, "assistant"` scan under `qwen_chat`: no active runtime direct answer sinks were found in this worktree scan.

## Accepted Limits

- This report is not model-role strict enforcement.
- This report is not production launch approval.
- This report does not claim runtime probes have proven AI metadata completeness.
- The low-level `service_append_message_wrapper` remains monitored only; authority belongs above the raw append layer.

Final recommendation: `ec_7b_metadata_coverage_inventory_ready_for_counterpart_review`
