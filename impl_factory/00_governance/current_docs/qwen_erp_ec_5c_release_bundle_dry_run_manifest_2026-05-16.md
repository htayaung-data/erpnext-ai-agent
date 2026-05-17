# EC-5C Release Bundle Dry-Run Manifest

## Executive Decision

Recommendation:

`enterprise_cleanup_ec_5c_ready_for_counterpart_review`

EC-5C is a dry-run manifest only. It creates an exact candidate bundle map and hunk-level ownership plan, but performs no staging, commit, delete, move, archive, cleanup, `.gitignore` edit, source behavior change, UX work, Filter work, MI work, or family expansion.

## Baseline

- Branch: `feature/ai-assistant`
- Head: `154be1e`
- Pre-EC-5C dirty count: `310`
- Expected dirty count after adding this EC-5C manifest: `311`
- EC-4 evidence dirty count recorded in source-of-truth reports: `307`
- Post-EC-4-evidence governance-document delta: `4`
- Post-EC-4-evidence governance delta files:
- `impl_factory/00_governance/current_docs/qwen_erp_ec_4_final_answer_emission_authority_closure_2026-05-16.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_5a_release_packaging_worktree_control_baseline_2026-05-16.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_5b_release_packaging_plan_2026-05-16.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_5c_release_bundle_dry_run_manifest_2026-05-16.md`

The EC-4 final closure note plus EC-5A, EC-5B, and EC-5C are governance/reporting artifacts only. No runtime or test behavior is intentionally changed by these four documents.

## Scope Guard

Blocked in EC-5C:

- `no staging`
- `no commit`
- `no delete`
- `no move`
- `no archive`
- `no cleanup`
- `no .gitignore edit`
- `no source implementation`
- `no broad service.py refactor`
- `no model-role strict enforcement`
- `no UX, Filter, MI, or family expansion`

## Exact Dry-Run Bundle Manifest

### Pure EC-4 Source Candidates

These files are candidate EC-4 source bundle entries because EC-5B classified them as pure EC-4 closure support, mapping, leakage audit, or gate-report source. They still require normal review before staging, but they are not currently marked as mixed runtime files.

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/compiled_support_emission_mapping.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/enterprise_cleanup_gate_report.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_followup_emission_mapping.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/final_answer_emission_closure_checkpoint.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/final_answer_emission_dry_run.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/final_answer_emission_leakage_audit.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/final_answer_remaining_append_mapping.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_emission_mapping.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/legacy_runtime_emission_mapping.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/nbu_governed_requery_emission_mapping.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/reasoning_lane_emission_mapping.py`

### Mixed Runtime Files

These files must not be packaged whole-file as EC-4-owned without hunk-level review. EC-5C records ownership by function/line area and keeps non-EC or pre-existing hunks under owner review.

| File | Diff footprint | Function or line-range summary | EC slice ownership | Why it belongs in EC-4 | Tests proving it | Non-EC/pre-existing hunks remain? | Packaging decision |
|---|---:|---|---|---|---|---|---|
| `qwen_chat/compiled_support.py` | `+307/-58`, `5` hunks | imports and helpers around `8-447`; `handle_compiled_first_turn_result` around `485-698` | `EC-4E`, `EC-4O` | migrated compiled-support governed/report, clarification, policy-boundary, and error-fallback emissions to authorized emission with no blocked payload leak | `test_compiled_support_authorized_emission_contracts`, `test_compiled_support_emission_mapping_contracts`, `test_compiled_support_contracts`, `test_semantic_financial_resolution` | yes | include EC-4 hunks only; owner review for pre-existing compiled-support hunks |
| `qwen_chat/entity_followup_support.py` | `+148/-23`, `2` hunks | helpers around `14-43`; `try_entity_detail_followup` around `72-226` | `EC-4M`, `EC-4M-A` | migrated entity follow-up success/failure, added pre-authority payload staging through helper, fixed blocked tool/evidence leak | `test_entity_followup_authorized_emission_contracts`, `test_entity_followup_emission_mapping_contracts`, EC-4N leakage audit | yes | include EC-4 hunks only; owner review for any non-EC entity follow-up edits |
| `qwen_chat/frontdoor_lane.py` | `+12/-626`, `1` hunk | whole root duplicate converted to compatibility facade | `EC-4U` | closes root duplicate frontdoor append risk by facade to active package lane | `test_frontdoor_authorized_emission_contracts`, `test_frontdoor_emission_mapping_contracts` | no, if facade is accepted as whole-file replacement | include whole file as EC-4U facade only after owner accepts duplicate cleanup |
| `qwen_chat/lanes/artifact_boundary_lane.py` | `+187/-67`, `3` hunks | `_ToolPayloadCollector` around `16-52`; `handle_artifact_boundary_turn` around `58-395` | `EC-4R1` | migrated artifact-boundary answer paths with staged evidence/recovery/observability payloads | `test_artifact_boundary_authorized_emission_contracts`, EC-4Q-A mapping, EC-4N leakage audit | yes | include EC-4 hunks only; owner review for any pre-existing artifact-boundary behavior |
| `qwen_chat/lanes/clarification_lane.py` | `+129/-69`, `3` hunks | control authority helper around `73-101`; `handle_pending_clarification_turn` around `101-309` | `EC-4T1` | migrated non-service clarification/control outputs through explicit control authority | `test_control_authorized_emission_contracts`, EC-4Q-A mapping, EC-4N leakage audit | yes | include EC-4 hunks only; owner review for unrelated clarification behavior |
| `qwen_chat/lanes/frontdoor_lane.py` | `+391/-47`, `6` hunks | authority helpers around `237-454`; `handle_frontdoor_turn` around `801-982` | `EC-4C`, `EC-4O` | migrated active package frontdoor governed/report, KPI definition, boundary, and control outputs through authorized emission; fixed blocked post-helper payload leakage | `test_frontdoor_authorized_emission_contracts`, `test_frontdoor_emission_mapping_contracts`, frontdoor suites, `test_semantic_financial_resolution` | yes | include EC-4 hunks only; owner review for pre-existing frontdoor changes |
| `qwen_chat/lanes/legacy_runtime_lane.py` | `+154/-45`, `2` hunks | helpers around `22-95`; `handle_legacy_runtime_turn` around `95-267` | `EC-4I`, `EC-4O` | migrated legacy runtime business/boundary/error output; removed latest assistant payload dependency for final authority | `test_legacy_runtime_authorized_emission_contracts`, `test_legacy_runtime_emission_mapping_contracts`, `test_semantic_financial_resolution` | yes | include EC-4 hunks only; owner review for pre-existing legacy fallback wording |
| `qwen_chat/lanes/reasoning_lane.py` | `+117/-59`, `3` hunks | model-role/runtime trace helpers around `19-53`; `handle_reasoning_turn` around `53-321` | `EC-4F-A`, `EC-4G`, `EC-4O` | mapped/model-role-prepped reasoning lane, migrated reasoning answer and guardrail boundary through authorized emission, fixed returned answer leak | `test_reasoning_lane_emission_mapping_contracts`, pure reasoning suites, `test_semantic_financial_resolution` | yes | include EC-4 hunks only; owner review for observability-prep and pre-existing reasoning edits |
| `qwen_chat/lanes/runtime_gate_lane.py` | `+96/-27`, `4` hunks | boundary payload helpers around `17-64`; `handle_runtime_gate_turn` around `64-220` | `EC-4S1` | migrated runtime gate policy-boundary response through authorized emission with staged boundary/observability payloads | `test_runtime_gate_authorized_emission_contracts`, EC-4Q-A mapping, EC-4N leakage audit | yes | include EC-4 hunks only; owner review for non-EC runtime gate edits |
| `qwen_chat/local_followup_support.py` | `+60/-13`, `2` hunks | payload helpers around `13-23`; `try_local_followup_transform` around `208-384` | `EC-4R2`, `EC-4R2-A` | migrated local follow-up transforms; service guard prevents duplicate post-helper audit | `test_local_followup_authorized_emission_contracts`, EC-4Q-A mapping, EC-4N leakage audit | yes | include EC-4 hunks only; owner review for non-EC local transform behavior |
| `qwen_chat/natural_business_understanding_activation.py` | `+2/-1`, `2` hunks | presentation activation classification around `8-93` | `EC-4T1` | supports NBU presentation/control classification used by authorized control path | NBU suite, `test_control_authorized_emission_contracts` | yes | owner review; include only if needed by EC-4T1 proof |
| `qwen_chat/natural_business_understanding_governed_requery_activation.py` | `+102/-58`, `3` hunks | outcome payload helpers around `706-734`; authority payload around `734-763`; `try_activate_nbu_governed_requery_response` around `763-949` | `EC-4J`, `EC-4K`, `EC-4O` | migrated NBU governed requery entity-detail output through authorized emission with no returned answer surface | `test_nbu_governed_requery_authorized_emission_contracts`, `test_nbu_governed_requery_emission_mapping_contracts`, NBU suite, `test_semantic_financial_resolution` | yes | include EC-4 hunks only; owner review for other NBU changes |
| `qwen_chat/recovery_guidance_support.py` | `+46/-22`, `2` hunks | `handle_recovery_guidance_response` around `21-138` | `EC-4T1` | migrated recovery guidance/control output through explicit control authority | `test_control_authorized_emission_contracts`, EC-4Q-A mapping, EC-4N leakage audit | yes | include EC-4 hunks only; owner review for recovery text behavior |
| `qwen_chat/service.py` | `+261/-106`, `6` hunks | imports around `18-237`; payload helpers around `1048-1056`; policy helper around `3253-3369`; local follow-up/service control regions within `3731-5796` | `EC-4R2-A`, `EC-4S2`, `EC-4T2` | added narrow service guards/helpers for local-transform post-helper audit, two service policy-boundary branches, and three service control branches | `test_service_policy_boundary_authorized_emission_contracts`, `test_service_control_authorized_emission_contracts`, EC-4Q-A mapping, EC-4N leakage audit, `test_semantic_financial_resolution` | yes, high risk | include only reviewed EC-4 hunks; whole-file packaging is unsafe without owner/hunk review |
| `qwen_chat/visible_context_followup_activation.py` | `+332/-62`, `11` hunks | authority helpers around `1355-1406`; `_emit_authorized_visible_context_answer` around `1406-1492`; return paths around `1492-1727` | `EC-4A`, `EC-4U`, `EC-4U-A` | migrated visible-context answers/boundaries; preserved runtime metadata; fixed blocked-authority return `ok=False` | `test_visible_context_followup_activation`, visible-context suite, visible-context blocked-authority probe | yes | include EC-4 hunks only; owner review for pre-existing resolver changes |
| `qwen_chat/visible_context_trace_inspection.py` | `+659/-15`, `9` hunks | trace synthesis/rendering around `197-903`; `try_activate_visible_context_trace_inspection_response` around `903-1001` | `EC-4T1` | migrated trace/debug inspection output through authorized trace/control authority and strengthened trace publication | `test_visible_context_trace_inspection`, `test_control_authorized_emission_contracts`, visible-context suite | yes | include EC-4 hunks only; owner review for expanded trace rendering surface |

## EC-4 Test Bundle Candidates

### Direct Emission-Authority Tests

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_artifact_boundary_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_compiled_support_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_control_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_entity_followup_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_frontdoor_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_legacy_runtime_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_local_followup_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_nbu_governed_requery_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_runtime_gate_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_service_control_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_service_policy_boundary_authorized_emission_contracts.py`

### Mapping, Leakage, And Closure Tests

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_compiled_support_emission_mapping_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_entity_followup_emission_mapping_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_final_answer_emission_closure_checkpoint_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_final_answer_emission_dry_run_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_final_answer_emission_leakage_audit_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_final_answer_remaining_append_mapping_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_frontdoor_emission_mapping_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_legacy_runtime_emission_mapping_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_nbu_governed_requery_emission_mapping_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_reasoning_lane_emission_mapping_contracts.py`

### Shared Tests Not Automatically In EC-4 Bundle

Manual UAT, model-role, policy-boundary, shared final-answer authority, semantic financial, and regression-governance tests remain shared infrastructure or release verification tests. They should not be swept wholesale into the EC-4 bundle without owner approval, even though EC-4 verification depends on selected shared suites.

## Selected Source-Of-Truth Evidence Candidates

Only these `10` generated evidence files are EC-4 source-of-truth candidates. Do not package the whole `current_docs/generated/` directory.

- `impl_factory/00_governance/current_docs/generated/ec_3_final_answer_hard_gate_dry_run/qwen_ec3_final_answer_emission_dry_run_report.json`
- `impl_factory/00_governance/current_docs/generated/ec_3_final_answer_hard_gate_dry_run/qwen_ec3_final_answer_emission_dry_run_report.md`
- `impl_factory/00_governance/current_docs/generated/ec_4b_frontdoor_emission_mapping/qwen_ec4b_frontdoor_emission_mapping_report.json`
- `impl_factory/00_governance/current_docs/generated/ec_4b_frontdoor_emission_mapping/qwen_ec4b_frontdoor_emission_mapping_report.md`
- `impl_factory/00_governance/current_docs/generated/ec_4n_final_answer_emission_leakage_audit/qwen_ec4n_final_answer_emission_leakage_audit_report.json`
- `impl_factory/00_governance/current_docs/generated/ec_4n_final_answer_emission_leakage_audit/qwen_ec4n_final_answer_emission_leakage_audit_report.md`
- `impl_factory/00_governance/current_docs/generated/ec_4q_a_remaining_append_mapping/qwen_ec4q_a_remaining_append_mapping_report.json`
- `impl_factory/00_governance/current_docs/generated/ec_4q_a_remaining_append_mapping/qwen_ec4q_a_remaining_append_mapping_report.md`
- `impl_factory/00_governance/current_docs/generated/ec_4u_duplicate_wrapper_visible_context_closure/qwen_ec4u_final_answer_emission_closure_packet.json`
- `impl_factory/00_governance/current_docs/generated/ec_4u_duplicate_wrapper_visible_context_closure/qwen_ec4u_final_answer_emission_closure_packet.md`

### Evidence Freshness Notes

- Official EC-3 report records `active_runtime_direct_assistant_append_count=0`.
- Official EC-3 report records `migrated_authorized_paths` length `27`.
- EC-4Q-A report records `inventory_item_count=1`, `active_direct_assistant_append_count=0`, `low_level_wrapper_count=1`.
- EC-4N report records `migrated_path_count=27`, `blocked_leakage_potential_leak_count=0`.
- EC-4 evidence reports record `current_dirty_status_count=307`.
- Current pre-EC-5C dirty count is `310`.
- The expected EC-5C manifest raises the dirty count to `311`.
- The `307 -> 311` difference is governance documentation only: EC-4 final closure note plus EC-5A, EC-5B, and EC-5C. It is not a runtime/test behavior change.

### EC-4B Frontdoor Evidence Relabeling

The `ec_4b_frontdoor_emission_mapping` folder name is historical. Its current JSON/Markdown report is retained as source-of-truth only because it was refreshed after EC-4U and now records the duplicate-frontdoor closure state:

- `frontdoor_direct_assistant_append_count=0`
- `duplicate_drift_emitter_count=0`
- `compatibility_facade_emitter_count=1`
- root duplicate status: `closed_by_compatibility_facade`

For release packaging, label these files as refreshed duplicate/facade closure evidence, not as stale EC-4B-only mapping evidence.

## Governance Docs Candidate Policy

Candidate governance docs for current EC traceability:

- `impl_factory/00_governance/current_docs/qwen_erp_ec_4_final_answer_emission_authority_closure_2026-05-16.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_5a_release_packaging_worktree_control_baseline_2026-05-16.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_5b_release_packaging_plan_2026-05-16.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_5c_release_bundle_dry_run_manifest_2026-05-16.md`

Historical six-fact gates, intermediate slice notes, and non-source-of-truth generated evidence should be archived or excluded only in a future approved cleanup slice. EC-5C does not move or archive them.

## Explicitly Excluded Streams

The following streams remain excluded from EC-4 release packaging:

- ERP UI stream: `erp_workspace_ui/*`
- seed/data stream
- dummy data stream
- temp/probe/cache files
- owner-decision PrimeAxis docs and UI program docs
- broad `service.py` refactor work
- model-role strict enforcement work
- UX, Filter, MI, and family expansion work

## Owner-Decision Files

These files remain blocked from EC packaging until owner decision:

- `impl_factory/00_governance/current_docs/README.md`
- `impl_factory/00_governance/current_docs/primeaxis_business_notes_for_future_ai_discussions_2026-04-17.md`
- `impl_factory/00_governance/current_docs/primeaxis_business_strategy_master_plan_2026-04-05.md`
- `impl_factory/00_governance/current_docs/primeaxis_ui_program/`
- `impl_factory/00_governance/current_docs/primeaxis_v1_parallel_execution_miniphase_plan_2026-04-12.md`

## Proposed Packaging Groups

| Group | Packaging action | Approval needed |
|---|---|---|
| Pure EC-4 source candidates | candidate for bundle after normal review | Counterpart/owner |
| Mixed runtime EC-4 hunks | include only EC-owned hunks after hunk-level review | Counterpart/owner, high attention |
| Mixed runtime non-EC hunks | exclude or route to separate AI cleanup stream | owner |
| EC-4 direct tests | candidate for EC-4 test bundle | Counterpart |
| EC-4 mapping/leakage/closure tests | candidate for EC-4 governance test bundle | Counterpart |
| Shared manual/model-role/policy/regression tests | keep as shared verification, not automatic EC-4 package | owner |
| Selected 10 evidence files | source-of-truth candidates only | Counterpart/QA |
| Historical generated evidence | archive separately later | owner/QA |
| ERP UI and seed/data | exclude from EC bundle | owner |
| temp/probe/cache | cleanup later only with explicit approval | owner |

## Verification Results

Required EC-5C verification:

- `python3 scripts/check_qwen_enterprise_guardrails.py`: `PASS`
- `git diff --check`: `FAIL`, due to excluded ERP UI stream trailing whitespace, beginning with `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/public/js/sales_order_form.js`
- scoped `git diff --check` for this EC-5C manifest and `ai_assistant_ui`: `PASS`
- source scan using `build_final_answer_emission_dry_run_report(reviewer="codex_ec5c_source_scan", status_count=311)`: `active_runtime_direct_assistant_append_count=0`, `inventory_count=1`, `migrated_authorized_paths` length `27`
- EC-4 closure/mapping/leakage tests: `49 passed`
- semantic financial suite: `276 passed`

The unscoped `git diff --check` failure is not fixed in EC-5C because the failing files are in an explicitly excluded ERP UI stream. This remains a release-packaging blocker for a later owner-approved cleanup stream, not an EC-5C source behavior change.

## Final Recommendation

`enterprise_cleanup_ec_5c_ready_for_counterpart_review_with_excluded_stream_diff_check_blocker`

EC-5C gives Counterpart an exact dry-run bundle manifest, but it does not approve packaging. The next step after Counterpart review should be a narrowly approved packaging or hunk-review slice, not staging or cleanup by category.
