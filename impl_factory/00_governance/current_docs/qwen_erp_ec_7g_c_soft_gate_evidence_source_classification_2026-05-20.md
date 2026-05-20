# EC-7G-C Soft-Gate Evidence Source Classification / Runtime Trace Readiness Plan

Decision: ec_7g_c_soft_gate_evidence_source_classification_ready_for_counterpart_review

Date: 2026-05-20
Generated: 2026-05-19T18:00:36+00:00
Branch: feature/ec-7b0-runtime-import-integrity
Head: 2641458
Runtime effect: `none`
Strict enforcement enabled: `false`
Staging/commit/push/deployment: `not performed`

## Scope

EC-7G-C is report/audit only. It classifies the evidence backing each accepted EC-7G-B soft-gate lane and defines what extra evidence is needed before live UAT or hard enforcement can be discussed.

No runtime blocking, strict enforcement, behavior change, route change, answer-text change, model change, report-selection change, final-answer authority change, staging, commit, push, deployment, UX, Filter, MI, family expansion, or service refactor was performed.

## Evidence Source Taxonomy

| Evidence source | Meaning | Sufficiency boundary |
|---|---|---|
| `live_runtime_trace_evidence` | Evidence captured from real application/runtime execution with real integration surfaces. | Required before future live UAT closure and before any hard-enforcement decision. |
| `mocked_runtime_probe_evidence` | Real interpreter/helper/lane call path exercised with mocked model/runtime/ERP responses. | Sufficient for backend metadata/provenance readiness, not sufficient for production UAT or hard enforcement. |
| `metadata_helper_evidence` | Direct helper or envelope construction validated by focused tests. | Sufficient for deterministic/control coverage when paired with authority/no-leak contracts; not sufficient alone for AI hard enforcement. |
| `closure/no-leak evidence` | Existing no-leak, blocked-authority, final-answer authority, and trace/audit closure tests. | Sufficient for backend safety regression control; must be paired with live traces for enforcement. |
| `static_report_evidence` | Generated inventories, raw append scans, soft-gate reports, and governance docs. | Sufficient for review/packaging traceability, not sufficient alone for runtime enforcement. |

## Sufficiency Decisions

| Decision area | Current EC-7G-C position | Required before moving further |
|---|---|---|
| Backend release readiness | Sufficient to keep EC-7G soft-gate dry-run accepted, because EC-7F probes and EC-7G-B report shape are green. | Counterpart/QA acceptance of this evidence-source classification. |
| Staging / PR packaging | Sufficient as a candidate evidence bundle only. Packaging must remain manifest-driven because the worktree is dirty. | A future packaging gate must include exact EC-7 files/reports/tests and rerun cached-index checks. |
| Future live UAT | Not sufficient yet. Current evidence is backend/mocked/helper/static, not live browser/ERP trace evidence. | Representative live UAT traces for AI semantic, reasoning, helper/tool, deterministic/control, boundary, fallback, and blocked-authority cases. |
| Future hard enforcement consideration | Not sufficient yet and not approved. | Live UAT evidence, staged package verification, fail-open/fail-closed policy, owner/QA decision, and explicit EC-7H enforcement decision. |

## Lane Evidence Classification

| Lane | Lane class | Model role | Probe evidence | Primary evidence source | Evidence details | Readiness implication |
|---|---|---|---|---|---|---|
| `frontdoor_semantic_classification` | `ai_semantic` | `light_semantic` | `EC-7F-B` | `mocked_runtime_probe_evidence` | real interpreter path with mocked model response; static EC-7G-B observed/expected row | Backend readiness sufficient; live UAT trace still required before hard enforcement. |
| `fresh_query_interpretation` | `ai_semantic` | `light_semantic` | `EC-7F-B` | `mocked_runtime_probe_evidence` | real interpreter path with mocked model response; fallback/low-confidence probes | Backend readiness sufficient; live UAT trace still required before hard enforcement. |
| `followup_interpretation` | `ai_semantic` | `light_semantic` | `EC-7F-B` | `mocked_runtime_probe_evidence` | real interpreter path with mocked model response; degraded/rejected status probes | Backend readiness sufficient; live UAT trace still required before hard enforcement. |
| `semantic_reasoning_activation` | `ai_semantic` | `light_semantic` | `EC-7F-B` | `mocked_runtime_probe_evidence` | real interpreter path with mocked model response; runtime-error probes | Backend readiness sufficient; live UAT trace still required before hard enforcement. |
| `semantic_repair_intent` | `ai_semantic` | `light_semantic` | `EC-7F-B` | `mocked_runtime_probe_evidence` | real interpreter path with mocked model response; not-applicable/runtime-error probes | Backend readiness sufficient; live UAT trace still required before hard enforcement. |
| `business_reasoning_answer` | `ai_reasoning` | `heavy_reasoning` | `EC-7F-C` | `mocked_runtime_probe_evidence` | real reasoning helper/lane surface with mocked runtime; authority-separation probe | Backend readiness sufficient; hard enforcement requires live reasoning traces and failure-mode policy. |
| `nbu_shadow_observation` | `shadow_observer` | `shadow_observer` | `EC-7F-C` | `mocked_runtime_probe_evidence` | real NBU shadow/runtime observation path with mocked runtime; observe-only proof | Backend readiness sufficient; hard enforcement must keep shadow observe-only. |
| `frontdoor_render` | `model_backed_helper` | `model_backed_helper` | `EC-7F-D-A` | `mocked_runtime_probe_evidence` | real helper path with mocked model response; final-authority separation proof | Backend readiness sufficient for helper provenance; live UAT trace needed for enforcement discussion. |
| `clarification_system` | `model_backed_helper` | `model_backed_helper` | `EC-7F-D-A` | `mocked_runtime_probe_evidence` | real helper path plus template fallback; missing-model/runtime-failure proof | Backend readiness sufficient for helper provenance; live UAT trace needed for enforcement discussion. |
| `artifact_narrative` | `model_backed_helper` | `model_backed_helper` | `EC-7F-D-A` | `mocked_runtime_probe_evidence` | real helper path with mocked model response; invalid/runtime-failure proof | Backend readiness sufficient for helper provenance; live UAT trace needed for enforcement discussion. |
| `composite_reads` | `governed_tool_runtime` | `governed_tool_runtime` | `EC-7F-D-A` | `mocked_runtime_probe_evidence` | real runtime helper path and deterministic path; helper/tool authority separation | Backend readiness sufficient; hard enforcement requires live governed-tool failure traces. |
| `fresh_query_compiled_read_runtime` | `governed_tool_runtime` | `governed_tool_runtime` | `EC-7F-D-A` | `mocked_runtime_probe_evidence` | real execute_compiled_fresh_query_message path with mocked report/model fallback | Backend readiness sufficient; hard enforcement requires live governed-tool failure traces. |
| `compiled_support_result_answer` | `deterministic_report` | `deterministic` | `EC-7F-E` | `metadata_helper_evidence` | real lane helper metadata probe; final-answer authority/no-leak contracts | Backend readiness sufficient; deterministic lane not AI strict-enforcement target. |
| `legacy_runtime_business_or_boundary_answer` | `deterministic_report` | `deterministic` | `EC-7F-E` | `metadata_helper_evidence` | real lane helper metadata probe; final-answer authority/no-leak contracts | Backend readiness sufficient; deterministic lane not AI strict-enforcement target. |
| `artifact_boundary` | `deterministic_report` | `deterministic` | `EC-7F-E` | `metadata_helper_evidence` | real lane helper metadata probe; blocked/no-leak contracts | Backend readiness sufficient; deterministic lane not AI strict-enforcement target. |
| `local_followup_transform` | `deterministic_visible_context` | `deterministic` | `EC-7F-E` | `metadata_helper_evidence` | real lane helper metadata probe; visible-context authority/no-leak contracts | Backend readiness sufficient; deterministic visible-context lane not AI strict-enforcement target. |
| `entity_followup` | `deterministic_report` | `deterministic` | `EC-7F-E` | `metadata_helper_evidence` | real lane helper metadata probe; error fallback and no-leak contracts | Backend readiness sufficient; deterministic lane not AI strict-enforcement target. |
| `nbu_governed_requery_entity_detail` | `deterministic_report` | `deterministic` | `EC-7F-E` | `metadata_helper_evidence` | real lane helper metadata probe; missing-authority no-leak contracts | Backend readiness sufficient; deterministic lane not AI strict-enforcement target. |
| `visible_context_followup` | `deterministic_visible_context` | `deterministic` | `EC-7F-E` | `closure/no-leak evidence` | visible-context suite plus runtime blocked-authority proof; metadata helper coverage | Backend readiness sufficient; live UAT trace still needed before hard enforcement. |
| `runtime_gate` | `policy_boundary` | `policy_boundary` | `EC-7F-E` | `metadata_helper_evidence` | real lane helper metadata probe; bounded policy authority proof | Backend readiness sufficient; policy boundary not AI strict-enforcement target. |
| `service_policy_control_responses` | `policy_boundary` | `policy_boundary` | `EC-7F-E` | `metadata_helper_evidence` | focused service helper contracts; bounded policy/control authority proof | Backend readiness sufficient; service-level live trace recommended before hard enforcement. |
| `clarification_control` | `control_meta` | `control_meta` | `EC-7F-E` | `metadata_helper_evidence` | real lane helper metadata probe; explicit control authority proof | Backend readiness sufficient; control lane not AI strict-enforcement target. |
| `nbu_safe_response_activation` | `control_meta` | `control_meta` | `EC-7F-E` | `metadata_helper_evidence` | real control lane coverage; explicit control authority proof | Backend readiness sufficient; control lane not AI strict-enforcement target. |
| `visible_context_trace_inspection` | `control_meta` | `control_meta` | `EC-7F-E` | `closure/no-leak evidence` | visible trace inspection suite plus trace_debug metadata helper proof | Backend readiness sufficient; trace/control lane not AI strict-enforcement target. |

## Evidence Coverage Summary

- Live runtime trace evidence: `0 lanes currently closed by live trace evidence`.
- Mocked runtime probe evidence: `12 lanes`, covering light semantic, heavy reasoning, NBU shadow, model-backed helpers, and governed-tool runtime helpers.
- Metadata helper evidence: `10 lanes`, covering deterministic, policy, control, and service helper paths where direct helper/contract proof is appropriate.
- Closure/no-leak evidence: `2 lanes` as the primary evidence source, with additional no-leak evidence supporting many deterministic/control lanes.
- Static report evidence: applies globally through EC-7F-F and EC-7G-B/B-A reports, direct assistant append inventory, raw assistant append scan, and generated governance reports.

## Runtime Trace Readiness Plan

Before future live UAT:

- Capture real runtime traces for at least one accepted success path and one degraded/fallback path for each AI semantic lane group.
- Capture real runtime traces for business reasoning success, missing metadata, runtime error, and authority-separation cases.
- Capture NBU shadow traces proving observe-only behavior under success and degraded states.
- Capture helper/tool traces proving helper strict-readiness remains provenance-only and cannot grant final-answer business authority.
- Capture deterministic/control traces proving explicit authority source, not-applicable strict-readiness, and no answer/payload leak on blocked authority.
- Capture raw append and final-answer inventory evidence from the same build under review.

Before future hard enforcement consideration:

- Prove every strict-ready AI/helper lane has live runtime trace evidence, not only mocked probe evidence.
- Define fail-open versus fail-closed behavior for missing metadata, fallback, runtime error, and trace unavailability.
- Prove hard enforcement cannot change routing, answer text, report selection, or final-answer authority without explicit approval.
- Re-run EC-7G soft gate against staged/cached-index package evidence, not only the dirty worktree.
- Obtain explicit EC-7H Counterpart/QA/owner decision. EC-7G-C does not approve enforcement.

## Release Blockers And Warnings

- Release blockers in EC-7G-B-A report: `0`.
- Evidence-source blocker for hard enforcement: `live_runtime_trace_evidence_missing_for_all_lanes`.
- Packaging warning: worktree remains dirty; future packaging must be manifest-driven and cached-index verified.
- Production warning: EC-7F/EC-7G are backend provenance gates, not production UAT or browser validation.

## Non-Goals

- `no_runtime_blocking`
- `no_strict_enforcement`
- `no_behavior_changes`
- `no_staging_commit_push_or_deployment`
- `no_ux_filter_mi_or_family_expansion`
- `no_service_refactor`
- `no_packaging_execution`

## Final Recommendation

`ec_7g_c_soft_gate_evidence_source_classification_ready_for_counterpart_review`

EC-7G-C is sufficient to clarify the evidence boundary for backend soft-gate readiness. It is not sufficient for live UAT closure or hard enforcement. The next step, if accepted, should remain evidence/readiness planning unless Counterpart and QA explicitly approve a narrow next EC-7 slice.
