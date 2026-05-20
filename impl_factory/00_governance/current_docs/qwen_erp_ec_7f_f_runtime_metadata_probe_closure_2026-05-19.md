# EC-7F-F Runtime Metadata Probe Closure

Decision: ec_7f_runtime_metadata_probe_closure_ready_for_counterpart_review

Date: 2026-05-19
Branch: feature/ec-7b0-runtime-import-integrity
Head: 2641458
Staged files: 0

## Scope

EC-7F is backend runtime metadata/provenance validation. It validates that runtime payloads, helper payloads, deterministic/control envelopes, and final-answer authority boundaries carry trustworthy provenance before any strict model-role enforcement is considered.

EC-7F is not production UAT. EC-7F is not live ERP/browser validation. EC-7F does not approve strict enforcement, runtime hard blocking, production launch, deployment, UX, Filter, MI, or family expansion.

EC-7F-F is report/audit only. No runtime probes were added in this closure slice because the EC-7F-A through EC-7F-E evidence did not reveal a factual gap requiring one.

## EC-7F Slice Summary

| Slice | Purpose | Deliverable | Result |
| --- | --- | --- | --- |
| EC-7F-A | Runtime metadata probe plan | `qwen_erp_ec_7f_a_runtime_metadata_probe_plan_2026-05-19.md` | Accepted plan basis |
| EC-7F-B | Light semantic runtime probes | `test_light_semantic_runtime_probes.py`, EC-7F-B report | Covered light semantic model provenance |
| EC-7F-C | Heavy reasoning + NBU shadow runtime probes | `test_heavy_reasoning_nbu_shadow_runtime_probes.py`, EC-7F-C report | Covered heavy reasoning and shadow observer provenance |
| EC-7F-D-A | Model-backed helper + governed-tool runtime helper probes | `test_helper_tool_runtime_probes.py`, EC-7F-D report | Covered helper/tool provenance and real fresh-query compiled-read fallback path |
| EC-7F-E | Deterministic/control runtime metadata probes | `test_deterministic_control_runtime_metadata_probes.py`, EC-7F-E report | Covered deterministic, policy, control, error, visible-context, and NBU deterministic/control paths |

## Lane Closure Matrix

| Lane / path | Probe type | Success path | Missing metadata | Fallback / degraded / runtime-error | Strict-readiness result | Final-answer authority separation | EC-7G soft-gate consideration |
| --- | --- | --- | --- | --- | --- | --- | --- |
| frontdoor_semantic_classification | real interpreter path | accepted complete metadata can be `strict_ready` | missing model metadata is valid but not strict-ready | invalid/runtime-error statuses not strict-ready | strict-ready only for accepted complete metadata | semantic metadata is provenance-only | ready for soft-gate consideration |
| fresh_query_interpretation | real interpreter path | accepted complete metadata can be `strict_ready` | missing model metadata not strict-ready | low-confidence/runtime-error not strict-ready | strict-ready only for accepted complete metadata | downstream report authority remains separate | ready for soft-gate consideration |
| followup_interpretation | real interpreter path | accepted complete metadata can be `strict_ready` | missing model metadata not strict-ready | rejected/not-applicable/runtime-error not strict-ready | degraded statuses forced non-strict | follow-up classifier metadata is provenance-only | ready for soft-gate consideration |
| semantic_reasoning_activation | real interpreter path | accepted complete metadata can be `strict_ready` | missing model metadata not strict-ready | rejected/runtime-error not strict-ready | strict-ready only for accepted complete metadata | activation metadata does not replace reasoning answer authority | ready for soft-gate consideration |
| semantic_repair_intent | real interpreter path | accepted complete metadata can be `strict_ready` | missing model metadata not strict-ready | not-applicable/runtime-error not strict-ready | strict-ready only for accepted complete metadata | repair metadata is classifier provenance-only | ready for soft-gate consideration |
| business_reasoning_answer | real runtime helper path plus authority-boundary probe | complete heavy reasoning metadata can be strict-ready for provenance | missing model metadata not strict-ready | fallback/runtime-error not strict-ready | strict-ready only for complete heavy reasoning provenance | heavy reasoning metadata cannot bypass final-answer authority | ready for soft-gate consideration |
| nbu_shadow_observation | real runtime helper path | complete shadow metadata can be strict-ready for shadow provenance | missing model metadata not strict-ready | fallback/runtime-error not strict-ready | strict-ready only for complete observe-only provenance | shadow observer remains observe-only and does not affect final-answer authority | ready for soft-gate consideration |
| frontdoor_render | real runtime helper path | complete helper metadata can be strict-ready for helper provenance | missing model metadata not strict-ready | runtime failure not strict-ready | helper strict-ready is provenance-only | helper metadata cannot satisfy business final-answer authority | ready for soft-gate consideration |
| clarification_system | real runtime helper path and template fallback path | AI clarification success can be helper strict-ready | missing model metadata not strict-ready | runtime failure/template fallback not strict-ready | fallback/template non-strict | helper/control metadata cannot satisfy business final-answer authority | ready for soft-gate consideration |
| artifact_narrative | real runtime helper path | complete helper metadata can be strict-ready for narrative provenance | missing model metadata not strict-ready | invalid/runtime failure not strict-ready | strict-ready only for complete helper provenance | narrative metadata remains release-evidence provenance | ready for soft-gate consideration |
| composite_reads | real runtime helper path and deterministic path | deterministic governed report path remains deterministic | missing helper metadata not strict-ready where helper path is used | model fallback/runtime failure not strict-ready | deterministic path not AI strict-ready; fallback path non-strict | helper/tool metadata cannot grant final-answer authority | ready for soft-gate consideration |
| fresh_query_compiled_read_runtime | real `execute_compiled_fresh_query_message(...)` path plus helper checks | direct complete helper metadata can be strict-ready for tool provenance | missing model metadata not strict-ready | governed-report failure triggers fallback with visible non-strict metadata | fallback tool path not strict-ready | governed-tool metadata cannot satisfy business final-answer authority | ready for soft-gate consideration |
| runtime_gate | real lane harness plus metadata helper probe | policy-boundary metadata covered | not applicable deterministic/control metadata pattern | missing-boundary block remains no-leak | not_applicable | policy-boundary final authority remains bounded | ready for soft-gate consideration |
| clarification_control | real lane harness plus metadata helper probe | control metadata covered with explicit authority | not applicable deterministic/control metadata pattern | control/fallback remains non-AI strict | not_applicable | control authority remains explicit non-business authority | ready for soft-gate consideration |
| compiled_support_result_answer | real lane harness plus metadata helper probe | deterministic report metadata covered | blocked missing authority covered by existing no-leak tests | policy/control/error variants covered and non-strict | not_applicable | governed report / policy / control authority remains separate | ready for soft-gate consideration |
| legacy_runtime_business_or_boundary_answer | real lane harness plus metadata helper probe | deterministic report metadata covered | blocked missing authority covered by existing no-leak tests | policy/error variants covered and non-strict | not_applicable | final-answer authority remains governed/policy/error | ready for soft-gate consideration |
| artifact_boundary | real lane harness plus metadata helper probe | deterministic evidence metadata covered | blocked missing authority covered by no-leak tests | policy-boundary refusals covered | not_applicable | final-answer authority remains governed/policy | ready for soft-gate consideration |
| local_followup_transform | real lane harness plus metadata helper probe | deterministic visible-context metadata covered | missing authority block covered by existing tests | no AI fallback path | not_applicable | visible-context authority remains deterministic/control | ready for soft-gate consideration |
| entity_followup | real lane harness plus metadata helper probe | deterministic entity detail metadata covered | missing authority block covered by existing tests | error fallback explicit non-business authority | not_applicable | entity detail authority remains deterministic_tool/error_fallback | ready for soft-gate consideration |
| service_policy_control_responses | metadata helper probe and focused service contracts | service policy/control metadata covered | blocked authority behavior covered in focused service tests | policy/control variants non-strict | not_applicable | service policy/control authority remains explicit | ready for soft-gate consideration |
| nbu_governed_requery_entity_detail | real lane harness plus metadata helper probe | deterministic entity detail metadata covered | missing authority block covered by existing tests | no AI fallback path | not_applicable | NBU detail authority remains deterministic_tool | ready for soft-gate consideration |
| nbu_safe_response_activation | real control lane coverage plus metadata helper probe | control metadata covered | not applicable deterministic/control metadata pattern | safe/control response remains non-AI strict | not_applicable | control authority remains explicit | ready for soft-gate consideration |
| visible_context_followup | real visible-context suite plus metadata helper probe | deterministic visible-context metadata covered | visible-context blocked-authority proof remains green | policy/control variants non-strict | not_applicable | visible-context metadata does not bypass final-answer authority | ready for soft-gate consideration |
| visible_context_trace_inspection | real trace inspection suite plus metadata helper probe | trace/control metadata covered | not applicable deterministic/control metadata pattern | trace debug is control, not AI strict | not_applicable | trace metadata remains trace_debug control authority | ready for soft-gate consideration |

## Verification Commands And Results

Guardrail:

```bash
python3 scripts/check_qwen_enterprise_guardrails.py
```

Result:

```text
Qwen enterprise guardrail audit: PASS
```

Metadata/probe group, reproduced as the accepted EC-7F closure count:

```bash
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
```

Result:

```text
Ran 86 tests in 4.476s
OK
```

Authorized-emission checks, recorded separately:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest -q \
  ai_assistant_ui.tests.test_authorized_emission_contracts
```

Result:

```text
Ran 13 tests in 0.005s
OK
```

Fake-Frappe service import:

```text
fake_frappe_service_import=PASS
```

Direct assistant append inventory:

```text
active_runtime_direct_assistant_append_count=0
inventory_count=1
migrated_authorized_paths_length=27
```

Raw assistant append scan:

```text
impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py:271:append_message(session_doc, "assistant", assistant_text_payload(answer_text))
impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py:327:append_message(session_doc, "assistant", assistant_text_payload(answer_text))
```

Scoped diff check:

```bash
git diff --check -- impl_factory/05_custom_logic/custom_app/ai_assistant_ui impl_factory/00_governance/current_docs
```

Result: PASS.

Excluded stream scans:

```bash
git diff --name-only | grep -E 'erp_workspace_ui|02_seed_data|dummy_data|tmp/|\.codex_tmp|primeaxis' || true
git status --short | grep -E 'erp_workspace_ui|02_seed_data|dummy_data|tmp/|\.codex_tmp|primeaxis' || true
```

Result: both scans clean.

Staged files:

```text
0
```

## Evidence Count Hygiene

This closure packet does not use the earlier broad `124 passed` number as closure evidence. The reproduced EC-7F metadata/probe command above is the accepted closure evidence count: `86 passed`.

Authorized-emission checks are recorded separately as `13 passed`.

## Remaining Boundaries And Non-Goals

EC-7F does not approve strict enforcement. EC-7F only shows the backend metadata/provenance evidence is ready to be considered by an EC-7G soft gate.

EC-7F does not prove production UAT, live ERP/browser behavior, deployment readiness, UX readiness, Filter, MI, or family expansion.

No staging, commit, push, deployment, runtime blocking, route changes, answer text changes, report selection changes, service refactor, model-role hard enforcement, ERP UI, seed/data/temp/probe/cache, or PrimeAxis work was performed.

## Recommendation

EC-7F runtime metadata probe closure is ready for Counterpart and QA review.

If accepted, the next slice should be EC-7G strict-readiness soft gate planning or dry-run gate design only. Do not implement hard enforcement until EC-7G/EC-7H explicitly approve it.
