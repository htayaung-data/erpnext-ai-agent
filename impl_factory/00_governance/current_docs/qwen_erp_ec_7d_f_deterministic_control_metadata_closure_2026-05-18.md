# Qwen ERP EC-7D-F Deterministic / Control Metadata Coverage Closure

Date: 2026-05-18
Slice: EC-7D-F
Decision: ec_7d_deterministic_control_metadata_coverage_closed

## 1. Scope

EC-7D-F is a report/audit-only closure slice. It verifies that the deterministic, policy-boundary, control/meta, visible-context, error-fallback, and NBU deterministic/control paths identified in EC-7B are now covered by the EC-7C runtime metadata envelope.

No new lane wiring was performed in EC-7D-F.

Explicit non-goals:

- No strict enforcement.
- No AI runtime metadata provenance work.
- No routing changes.
- No answer text changes.
- No report selection changes.
- No model behavior changes.
- No UX, Filter, MI, or family expansion.
- No staging, commit, push, or deployment.

## 2. Baseline

- Branch: feature/ec-7b0-runtime-import-integrity
- HEAD: 2641458
- Worktree status count before EC-7D-F report: 81
- Expected worktree status count after EC-7D-F report: 82
- Staged files: 0
- Active runtime direct assistant append count: 0
- Remaining inventory count: 1
- Migrated authorized paths length: 27
- Remaining inventory item: service_append_message_wrapper, monitor-only infrastructure wrapper

## 3. Coverage Table

| Path | File/function | Answer modes covered | Lane class | Model role | Authority source | Preflight status | Metadata source | Tests proving valid envelope | Blocked-path leak test status | Strict readiness status | EC-7D complete |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| runtime_gate | qwen_chat/lanes/runtime_gate_lane.py::try_runtime_gate_boundary | runtime gate policy boundary | policy_boundary | policy_boundary | policy_boundary | bounded | runtime_gate_authorized_emission | test_runtime_gate_authorized_emission_contracts, test_runtime_metadata_contract | Forced missing-boundary authority blocks with no assistant/payload leak | not_applicable | yes |
| clarification_control | qwen_chat/lanes/clarification_lane.py::emit clarification/control responses | clarification/control response | control_meta | control_meta | control_meta | passed | clarification_control_authorized_emission | test_control_authorized_emission_contracts, test_runtime_metadata_contract | Missing control authority blocks with no assistant/payload leak | not_applicable | yes |
| compiled_support_result_answer | qwen_chat/compiled_support.py::handle_compiled_first_turn_result | compiled governed/report, policy boundary, control/clarification, error fallback | deterministic_report, policy_boundary, control_meta, error_fallback | deterministic, policy_boundary, control_meta, not_applicable | governed_erp_report, policy_boundary, control_meta, error_fallback | passed or bounded | compiled_support_authorized_emission | test_compiled_support_authorized_emission_contracts, test_runtime_metadata_contract | Missing governed authority blocks with no assistant/payload leak | not_applicable | yes |
| legacy_runtime_business_or_boundary_answer | qwen_chat/lanes/legacy_runtime_lane.py::try_legacy_runtime_response | legacy governed/report, policy boundary, runtime error fallback | deterministic_report, policy_boundary, error_fallback | deterministic, policy_boundary, not_applicable | governed_erp_report, policy_boundary, error_fallback | passed or bounded | legacy_runtime_authorized_emission | test_legacy_runtime_authorized_emission_contracts, test_runtime_metadata_contract | Missing governed authority blocks with no assistant/payload leak | not_applicable | yes |
| artifact_boundary | qwen_chat/lanes/artifact_boundary_lane.py::try_artifact_boundary_response | artifact evidence answer, grounded evidence boundary, enrichment boundary | deterministic_report, policy_boundary | deterministic, policy_boundary | governed_erp_report, policy_boundary | passed or bounded | artifact_boundary_authorized_emission | test_artifact_boundary_authorized_emission_contracts, test_runtime_metadata_contract | Missing/invalid authority blocks with no assistant/evidence leak | not_applicable | yes |
| local_followup_transform | qwen_chat/local_followup_support.py::try_local_followup_transform_response | local grounded visible-context transform | deterministic_visible_context | deterministic | frontdoor_composite | passed | local_followup_transform_authorized_emission | test_local_followup_authorized_emission_contracts, test_runtime_metadata_contract | Missing transform authority blocks with no assistant/payload leak | not_applicable | yes |
| entity_followup | qwen_chat/entity_followup_support.py::try_entity_detail_followup | entity detail governed answer, entity detail error fallback | deterministic_report, error_fallback | deterministic, not_applicable | deterministic_tool, error_fallback | passed | entity_followup_authorized_emission | test_entity_followup_authorized_emission_contracts, test_runtime_metadata_contract | Missing/invalid entity authority blocks with no assistant/business payload leak | not_applicable | yes |
| service_policy_control_responses | qwen_chat/service.py::_emit_service_policy_boundary_answer and qwen_chat/service.py::_emit_service_control_answer | service policy boundary, prior-branch restore, compound continue, compound stop | policy_boundary, control_meta | policy_boundary, control_meta | policy_boundary, control_meta | bounded or passed | service_policy_control_authorized_emission | test_service_policy_boundary_authorized_emission_contracts, test_service_control_authorized_emission_contracts, test_runtime_metadata_contract | Missing boundary/control authority blocks with no assistant/payload leak | not_applicable | yes |
| nbu_governed_requery_entity_detail | qwen_chat/natural_business_understanding_governed_requery_activation.py::try_activate_nbu_governed_requery_response | direct-evidence-first entity detail, rich entity detail | deterministic_report | deterministic | deterministic_tool | passed | nbu_governed_requery_authorized_emission | test_nbu_governed_requery_authorized_emission_contracts, test_runtime_metadata_contract | Missing/invalid authority blocks with no assistant/business payload leak | not_applicable | yes |
| nbu_safe_response_activation | qwen_chat/natural_business_understanding_service_activation.py::try_activate_nbu_presentation_response | NBU presentation/control safe response | control_meta | control_meta | control_meta | passed | nbu_safe_response_authorized_emission | test_natural_business_understanding_service_activation, test_runtime_metadata_contract | Current path is control/meta; existing NBU tests preserve no activation on unsupported/shadow-only cases | not_applicable | yes |
| visible_context_followup | qwen_chat/visible_context_followup_activation.py::_emit_authorized_visible_context_answer | visible context answer, visible context boundary, visible context clarification/control | deterministic_visible_context, policy_boundary, control_meta | deterministic, policy_boundary, control_meta | frontdoor_composite, policy_boundary, control_meta | passed or bounded | visible_context_followup_authorized_emission | test_visible_context_followup_activation, test_runtime_metadata_contract | Blocked-authority proof remains covered by visible-context follow-up tests and EC-4 leakage gates | not_applicable | yes |
| visible_context_trace_inspection | qwen_chat/visible_context_trace_inspection.py::try_activate_visible_context_trace_inspection_response | visible context authority trace inspection | control_meta | control_meta | trace_debug | passed | visible_context_trace_inspection_authorized_emission | test_visible_context_trace_inspection, test_runtime_metadata_contract | Diagnostic/control response uses authorized emission; no business answer payload leak path | not_applicable | yes |

## 4. Closure Findings

- Every EC-7B deterministic/control path listed for EC-7D now emits or carries an EC-7C runtime metadata envelope.
- All deterministic/report paths explicitly declare model_role=deterministic.
- All policy-boundary paths explicitly declare model_role=policy_boundary and preflight_status=bounded.
- All control/meta paths explicitly declare model_role=control_meta and an authority_source.
- Error fallback paths explicitly declare model_role=not_applicable with error/control authority.
- Visible-context follow-up and trace inspection had small EC-7C consistency gaps and were covered in EC-7D-E.
- No strict enforcement was added; deterministic/control strict readiness remains not_applicable by EC-7C contract semantics.

## 5. Verification

Commands/results:

- Guardrail: PASS
- EC-7C through EC-7D-E cumulative focused tests: 149 passed
- NBU discovery suite: 153 passed
- Visible-context suite: 78 passed
- Final-answer authority/emission subset: 47 passed
- Fake-Frappe service.py import probe: PASS
- Active runtime direct assistant append count: 0
- Inventory count: 1
- Migrated authorized paths length: 27
- Scoped AI diff check: PASS
- Excluded stream scan: clean
- Staged files: 0

## 6. Accepted Residuals

- service_append_message_wrapper remains monitor-only infrastructure and is not a user-facing answer lane.
- EC-7D does not cover AI runtime provenance for semantic/reasoning model calls.
- EC-7D does not enable strict model-role enforcement.
- EC-7D does not replace final-answer authority; it adds metadata observability alongside already-accepted authority hardening.

## 7. Final Decision

ec_7d_deterministic_control_metadata_coverage_closed

Next recommended action: submit EC-7D-F to Counterpart and QA_Risk Auditor. If accepted, proceed to EC-7E AI Runtime Metadata Provenance; do not start strict enforcement until EC-7F/EC-7G dry-run evidence exists.
