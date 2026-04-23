# Qwen ERP `service.py` Refactor SR0 Baseline Lock

Status: active baseline checkpoint  
Date: 2026-04-22  
Scope: dedicated `service.py` refactor chapter baseline after `IC6` closure

## 1. Purpose

This note freezes the real starting point for the dedicated `service.py` refactor chapter.

It exists to prevent the refactor from drifting into:

1. starting from zero when the project already has meaningful extracted seams
2. creating duplicate ownership homes
3. using the wrong test suite as the primary safety gate

## 2. Current Position

The project is not entering the refactor from a raw monolith state.

Conversation-control implementation has already matured through:

1. `IC4` recent-focus hardening
2. `IC5` restore and owner-precedence hardening
3. `IC6` bounded multi-step execution hardening

That means the refactor chapter is now:

1. seam completion
2. orchestration normalization
3. ownership clarification

It is not:

1. a fresh architecture rewrite
2. a general feature-expansion chapter

## 3. Current File Baseline

Primary target:

`impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`

Current observed metrics:

1. line count: `13,917`
2. top-level defs/classes: `382`

High-level in-file cluster counts observed during the audit:

1. snapshot cluster: `22` defs
2. conversation-control cluster: `23` defs
3. runtime-message cluster still visible in facade: `2` direct anchor defs
4. evaluation / smoke / probe cluster: `176` defs

Practical reading:

1. `service.py` is still too large
2. but a large part of its current gravity is accumulated evaluation code and residual subsystem ownership, not only top-level request orchestration

## 4. Existing Extracted Seams Already In Use

The refactor must integrate with the following live extracted modules rather than behaving as if no extractions exist.

### 4.1 Shared Modules Already Imported By `service.py`

1. `conversation_control_support.py`  
   lines: `1152`
2. `recent_focus_support.py`  
   lines: `919`
3. `restore_support.py`  
   lines: `542`
4. `snapshot_defaults.py`  
   lines: `259`
5. `compound_request_support.py`  
   lines: `831`
6. `compiled_support.py`  
   lines: `463`
7. `boundary_support.py`  
   lines: `1509`
8. `requery_message_support.py`  
   lines: `460`

### 4.2 Existing Package Seams

1. `qwen_chat/evaluation/`
2. `qwen_chat/lanes/`
3. `qwen_chat/context/`

### 4.3 Baseline Ownership Conclusion

These modules are not dead experiments.

They are already live imports in `service.py`, which means:

1. the project has already been refactoring incrementally
2. the dedicated refactor chapter must complete and normalize these seams
3. the chapter should avoid building a second parallel architecture beside them

## 5. Guarded Test Baseline

### 5.1 Primary Refactor Guard Suite

The current focused characterization pack is green and should be treated as the main safety gate for early refactor slices:

```text
python3 -m unittest \
  ai_assistant_ui.tests.test_post_contract_state_integrity \
  ai_assistant_ui.tests.test_compound_request_support \
  ai_assistant_ui.tests.test_compiled_support_contracts \
  ai_assistant_ui.tests.test_frontdoor_lane_compound_request
```

Observed result at this checkpoint:

1. `397` tests
2. `OK`

### 5.2 Secondary Broader Characterization Check

A broader pack was also attempted:

```text
python3 -m unittest \
  ai_assistant_ui.tests.test_post_contract_state_integrity \
  ai_assistant_ui.tests.test_compound_request_support \
  ai_assistant_ui.tests.test_compiled_support_contracts \
  ai_assistant_ui.tests.test_frontdoor_lane_compound_request \
  ai_assistant_ui.tests.test_clarification_resolution_contracts \
  ai_assistant_ui.tests.test_restore_support_contracts \
  ai_assistant_ui.tests.test_followup_interpreter_contracts \
  ai_assistant_ui.tests.test_family_followup_contracts
```

Observed result at this checkpoint:

1. `456` tests ran
2. `1` existing failure

Current failing test:

1. `test_artifact_boundary_option_resolution_beats_new_request_detection`
2. file: `ai_assistant_ui/tests/test_clarification_resolution_contracts.py`
3. observed mismatch:
   expected `resolved_option`
   actual `new_request`

### 5.3 Testing Governance Rule

Until that broader failure is triaged and either fixed or explicitly accepted as unrelated, the early refactor slices should use:

1. the green `397`-test suite as the primary hard gate
2. the broader `456`-test suite as a monitoring suite, not as the primary chapter progress signal

## 6. SR0 Ownership Map

This is the baseline ownership map for the refactor chapter.

It is intentionally practical and should guide the next slices.

| Cluster | Current location | Intended ownership home | Extraction type | Notes |
|---|---|---|---|---|
| Evaluation bodies | `service.py` lines ~`5940+` | existing `qwen_chat/evaluation/` package | full move plus thin wrappers where needed | safest first extraction; largest immediate gravity reduction |
| Snapshot assembly | `service.py` lines ~`3467-4110` | shared snapshot seam, reusing `snapshot_defaults.py`; introduce orchestration snapshot module only if needed | full move | do not duplicate default-state shaping already in `snapshot_defaults.py` |
| Recent-focus runtime message shaping | `service.py` lines around `_compile_recent_focus_runtime_message` | `recent_focus_support.py` plus `requery_message_support.py` / `compiled_support.py` as appropriate | full move or seam completion | do not create new runtime-message module unless current homes become conceptually mixed |
| Prior-branch restore policy and restore-affordance helpers | `service.py` lines ~`2154-2715` | `restore_support.py` and `conversation_control_support.py` | full move | keep only top-level orchestration in facade |
| Compound continuation / completion / cancellation policy | `service.py` lines ~`2856-2961` | `compound_request_support.py` plus `conversation_control_support.py` | full move | policy logic should not stay inline in facade |
| Conversation-control decision helpers | `service.py` lines ~`1194-2732` | `conversation_control_support.py`, `recent_focus_support.py`, `restore_support.py`, `compound_request_support.py` | full move where policy-owned | use existing ownership homes first |
| Runtime compiled-turn support | already partly extracted | `compiled_support.py` | stay as extracted home and widen only if ownership is clear | do not pull back into facade |
| Boundary/evidence helpers | already partly extracted | `boundary_support.py` and related boundary modules | stay as extracted home | only facade orchestration should remain |
| Turn entry and final orchestration | `handle_qwen_user_message` | `service.py` | stay in facade for now | this is the true orchestration shell target |
| Persistence / append ordering | mixed in facade | likely dedicated journal seam later | stay in facade for now, then revisit in later slice | do not extract before snapshot/control seams are cleaner |

## 7. What Should Stay In The Facade For Now

At this baseline, the following are still legitimate facade responsibilities:

1. session and request loading
2. top-level stage ordering
3. lane handoff orchestration
4. final response routing
5. persistence orchestration until a dedicated journal seam is justified by the later slice

## 8. What Should Not Stay In The Facade

The following should be treated as residual gravity to remove during the chapter:

1. large smoke / probe / debug bodies
2. snapshot assembly details
3. recent-focus policy details
4. prior-branch restore policy details
5. compound step transition / continuation / completion policy
6. runtime message shaping details that already have stable shared ownership candidates

## 9. Practical Reading Of The Plan

The existing dedicated refactor mini-phase sequence remains correct:

1. `SR0`
2. `SR1`
3. `SR2`
4. `SR3`
5. `SR4`
6. `SR5`
7. `SR6`
8. `SR7`

But this baseline sharpens the execution rule:

1. every extraction must first check whether an already-live module is the correct ownership home
2. creating a new module is allowed only when existing homes are clearly wrong or would become unstable
3. “move out of `service.py`” does not mean “create a new file by default”

## 10. Immediate Next Step

With `SR0` baseline lock now established, the next practical move should be:

1. start `SR1` evaluation seam completion

Reason:

1. it is the lowest-risk extraction seam
2. it offers the largest immediate gravity reduction
3. the codebase already has an `evaluation/` package, so this is seam completion rather than greenfield design

## 11. Honest Status Conclusion

This project is in a good position to refactor `service.py` in an enterprise-grade way.

Why:

1. the current refactor chapter is not pretending prior extractions never happened
2. the baseline now distinguishes green guard suites from noisy broader suites
3. the next slice is bounded, practical, and aligned with existing ownership seams

## 12. SR1 Progress Update

`SR1` is now in progress.

Completed in the first live `SR1` extraction slice:

1. moved the remaining H3 conversation-control smoke bodies out of `service.py` into `qwen_chat/evaluation/conversation_control_smokes.py`
2. extended the existing `ConversationControlSmokeDependencies` bundle so the extracted module owns the detailed smoke logic without reaching back into facade globals
3. reduced `service.py` to thin compatibility wrappers for those H3 smoke entrypoints
4. kept the refactor on the existing evaluation seam rather than creating a second smoke ownership path

Observed post-slice file position:

1. `service.py` line count reduced from `13,917` to `13,117`
2. extracted `conversation_control_smokes.py` now owns both the earlier targeted-restore smokes and the broader H3 conversation-control smoke cluster

Verification after the extraction:

1. `python3 -m py_compile ai_assistant_ui/qwen_chat/service.py ai_assistant_ui/qwen_chat/evaluation/conversation_control_smokes.py`
2. primary `397`-test refactor guard suite remains `OK`
3. broader `456`-test monitoring suite still shows the same pre-existing clarification-resolution failure:
   `test_artifact_boundary_option_resolution_beats_new_request_detection`

Practical status reading:

1. this confirms the evaluation seam can be reduced safely without changing the current hard gate result
2. the broader monitoring failure still exists, but this slice did not introduce a new regression signal

Next recommended `SR1` move:

1. continue the evaluation seam by extracting the remaining late debug / hardening evaluation bodies that still live in `service.py`
2. keep using the green `397`-test suite as the hard gate and the `456`-test suite as monitoring until the known clarification-resolution failure is triaged

Completed in the second live `SR1` extraction slice:

1. moved `run_phase6_reasoning_live_debug`, `run_phase8c_repair_handling_debug`, and `run_phase8_recovery_execution_debug` out of `service.py`
2. placed those bodies in the existing `qwen_chat/probes/service_diagnostics.py` seam, which is the correct ownership home for debug-oriented runners
3. converted the matching `service.py` functions into thin compatibility wrappers
4. kept the refactor aligned with the role boundary that diagnostics belong in the probe seam, not in the facade

Observed post-second-slice file position:

1. `service.py` line count reduced further from `13,117` to `12,881`
2. `service_diagnostics.py` now owns those late debug bodies instead of `service.py`

Verification after the second extraction:

1. `python3 -m py_compile ai_assistant_ui/qwen_chat/service.py ai_assistant_ui/qwen_chat/probes/service_diagnostics.py`
2. primary `397`-test refactor guard suite remains `OK`
3. broader `456`-test monitoring suite still shows the same single pre-existing clarification-resolution failure:
   `test_artifact_boundary_option_resolution_beats_new_request_detection`

Updated practical reading:

1. `SR1` is progressing through real seam reduction, not wrapper-only churn
2. both the evaluation seam and the probe seam are now being used according to role
3. the next `SR1` slice should continue removing late smoke / debug gravity from `service.py` before we move to later seam chapters

Completed in the third live `SR1` extraction slice:

1. moved the branch-restore precedence H3 smoke family out of `service.py`
2. placed those bodies into the existing `qwen_chat/evaluation/conversation_control_smokes.py` seam, extending the shared smoke dependency bundle with `build_conversation_state_snapshot`
3. converted five matching `service.py` entrypoints into thin compatibility wrappers:
   `run_h3_branch_restore_prefers_newer_focus_smoke`
   `run_h3_discard_prefixed_branch_restore_prefers_newer_focus_smoke`
   `run_h3_branch_restore_prefers_recent_focus_over_historical_prior_focus_smoke`
   `run_h3_discard_prefixed_branch_restore_prefers_recent_focus_over_historical_prior_focus_smoke`
   `run_h3_question_restore_prefers_newer_focus_smoke`
4. kept the extraction inside the already-approved evaluation seam rather than adding a new module

Observed post-third-slice file position:

1. `service.py` line count reduced further from `12,881` to `12,418`
2. `conversation_control_smokes.py` now owns another coherent restore-precedence smoke family instead of leaving that cluster inline in the facade

Verification after the third extraction:

1. local structural `py_compile` passed before syncing back to the server
2. server-side `python3 -m py_compile ai_assistant_ui/qwen_chat/service.py ai_assistant_ui/qwen_chat/evaluation/conversation_control_smokes.py` passed
3. the primary `397`-test refactor guard suite remained `OK`
4. targeted broader monitoring on `test_clarification_resolution_contracts` still shows the same pre-existing failure:
   `test_artifact_boundary_option_resolution_beats_new_request_detection`

Updated practical reading after the third slice:

1. `SR1` is still reducing real orchestration gravity, not just shuffling code
2. the conversation-control evaluation seam is now clearly the ownership home for these H3 restore-precedence smokes
3. the next bounded move can keep trimming the remaining late H3 smoke cluster before we enter the later seam chapters

Completed in the fourth live `SR1` extraction slice:

1. moved the first targeted-restore H3 family out of `service.py`
2. placed those bodies into the existing `qwen_chat/evaluation/conversation_control_smokes.py` seam
3. added two small seam-local helpers there so the extracted module does not inherit repeated supplier/customer directory restore logic or repeated transaction-listing restore logic
4. converted five matching `service.py` entrypoints into thin compatibility wrappers:
   `run_h3_targeted_restore_prefers_named_branch_smoke`
   `run_h3_targeted_restore_prefers_collection_branch_over_newer_detail_smoke`
   `run_h3_targeted_restore_prefers_customer_collection_over_newer_detail_smoke`
   `run_h3_targeted_restore_prefers_sales_invoice_listing_over_newer_detail_smoke`
   `run_h3_targeted_restore_prefers_purchase_order_listing_over_newer_detail_smoke`

Observed post-fourth-slice file position:

1. `service.py` line count reduced further from `12,418` to `11,934`
2. the evaluation seam now owns both the earlier item-collection restore coverage and the first broader targeted-restore branch family

Verification target for the fourth extraction:

1. local structural `py_compile` passed before syncing back to the server
2. server-side hard-gate verification should again use the `397`-test refactor guard suite
3. broader monitoring should remain informative only; the known clarification-resolution failure is still tracked separately

Updated practical reading after the fourth slice:

1. `SR1` is continuing to remove real late-stage conversation-control smoke gravity from the facade
2. the extracted seam is getting more coherent instead of becoming a dumping ground, because repeated restore patterns are now factored locally
3. the next `SR1` slice can continue with the discard-prefixed / recovery-targeted targeted-restore family that still remains inline in `service.py`

Completed in the fifth live `SR1` extraction slice:

1. moved the next targeted-restore transaction-listing family out of `service.py`
2. placed those bodies into the existing `qwen_chat/evaluation/conversation_control_smokes.py` seam
3. reused the seam-local transaction-listing restore helper for the discard-prefixed sales-invoice and purchase-order listing cases
4. added one seam-local cross-listing restore helper so the two “recover sales invoice listing over newer purchase order listing” smokes do not stay duplicated in extracted form
5. converted four matching `service.py` entrypoints into thin compatibility wrappers:
   `run_h3_discard_prefixed_targeted_restore_prefers_sales_invoice_listing_over_newer_detail_smoke`
   `run_h3_discard_prefixed_targeted_restore_prefers_purchase_order_listing_over_newer_detail_smoke`
   `run_h3_targeted_restore_recovers_sales_invoice_listing_over_newer_purchase_order_listing_smoke`
   `run_h3_discard_prefixed_targeted_restore_recovers_sales_invoice_listing_over_newer_purchase_order_listing_smoke`

Observed post-fifth-slice file position:

1. `service.py` line count reduced further from `11,934` to `11,520`
2. the evaluation seam now owns both the direct targeted-restore listing family and the first discard-prefixed / cross-listing transaction-listing restore family

Verification target for the fifth extraction:

1. local structural `py_compile` passed before syncing back to the server
2. server-side hard-gate verification should again use the `397`-test refactor guard suite
3. targeted monitoring should still check the known clarification-resolution failure separately

Updated practical reading after the fifth slice:

1. `SR1` is still reducing meaningful facade gravity rather than polishing around the edges
2. the extracted evaluation seam is staying structured through shared helper ownership, which lowers the chance that we simply recreate `service.py` elsewhere
3. the next natural `SR1` move is the pending-discard / stock-follow-up follow-up cluster that still remains inline

Completed in the sixth live `SR1` extraction slice:

1. moved the direct follow-up H3 family out of `service.py`
2. placed those bodies into the existing `qwen_chat/evaluation/conversation_control_smokes.py` seam without creating a new service-level branch
3. converted four matching `service.py` entrypoints into thin compatibility wrappers:
   `run_h3_exact_item_focus_stock_followup_smoke`
   `run_h3_seeded_transaction_document_followup_smoke`
   `run_h3_financial_statement_switch_followup_smoke`
   `run_h3_master_data_single_row_detail_followup_smoke`
4. kept the extraction enterprise-safe by moving a coherent continuation / follow-up family together rather than mixing it with the later active-sequence restore branch

Observed post-sixth-slice file position:

1. `service.py` line count reduced further from `11,520` to `11,094`
2. `conversation_control_smokes.py` now owns both targeted-restore families and the first direct follow-up family instead of leaving those late conversation-control smokes inline in the facade

Verification after the sixth extraction:

1. local structural `py_compile` passed before syncing back to the server
2. server-side `python3 -m py_compile ai_assistant_ui/qwen_chat/service.py ai_assistant_ui/qwen_chat/evaluation/conversation_control_smokes.py` passed
3. the primary `397`-test refactor guard suite remained `OK`
4. targeted broader monitoring on `test_clarification_resolution_contracts` still shows the same single pre-existing failure:
   `test_artifact_boundary_option_resolution_beats_new_request_detection`

Updated practical reading after the sixth slice:

1. `SR1` is still moving in the planned direction: shrinking facade gravity by ownership seam, not by one-off cleanup
2. the evaluation seam now owns a broader portion of the conversation-control continuation surface, which makes the later `service.py` orchestration split safer
3. the next bounded `SR1` move should be the remaining active-sequence / targeted-restore H3 cluster that still remains inline in `service.py`

Completed in the seventh live `SR1` extraction slice:

1. moved the resumable-prior-recovery targeted-restore family out of `service.py`
2. moved the active-sequence "answer the last question" H3 family out of `service.py`
3. extended the shared evaluation seam contract so it can receive the accepted-repair contract builder instead of assembling those artifacts inside the facade
4. converted seven matching `service.py` entrypoints into thin compatibility wrappers:
   `run_h3_targeted_restore_replays_resumable_prior_recovery_smoke`
   `run_h3_discard_prefixed_targeted_restore_replays_resumable_prior_recovery_smoke`
   `run_h3_targeted_restore_replays_resumable_prior_recovery_over_active_sequence_smoke`
   `run_h3_discard_prefixed_targeted_restore_replays_resumable_prior_recovery_over_active_sequence_smoke`
   `run_h3_question_restore_resumes_active_sequence_smoke`
   `run_h3_discard_prefixed_question_restore_resumes_active_sequence_smoke`
   `run_h3_pronoun_discard_question_restore_resumes_active_sequence_smoke`

Observed post-seventh-slice file position:

1. `service.py` line count reduced further from `11,094` to `10,257`
2. `conversation_control_smokes.py` now owns the next coherent late conversation-control restore family instead of leaving that replay / active-sequence seam inline in the facade

Verification after the seventh extraction:

1. local structural `py_compile` passed before syncing back to the server
2. server-side `python3 -m py_compile ai_assistant_ui/qwen_chat/service.py ai_assistant_ui/qwen_chat/evaluation/conversation_control_smokes.py` passed
3. the primary `397`-test refactor guard suite remained `OK`
4. targeted broader monitoring on `test_clarification_resolution_contracts` still shows the same single pre-existing failure:
   `test_artifact_boundary_option_resolution_beats_new_request_detection`

Updated practical reading after the seventh slice:

1. `SR1` is still reducing real orchestration gravity in the right place: late conversation-control ownership is moving into the evaluation seam rather than expanding the facade
2. the extracted seam now covers both targeted resumable-prior restore cases and active-sequence resume cases, which lowers the risk of precedence drift during the later stage split
3. the next bounded `SR1` move should be the remaining pending-clarification / explicit-override late H3 cluster that still remains inline in `service.py`

Completed in the eighth live `SR1` extraction slice:

1. moved the remaining inline H3 recovery-authority precedence family out of `service.py`
2. placed those bodies into the existing `qwen_chat/evaluation/conversation_control_smokes.py` seam
3. added one seam-local recovery seeding helper so the extracted module owns repeated recovery-authority fixture construction instead of keeping that duplication in the facade
4. converted three matching `service.py` entrypoints into thin compatibility wrappers:
   `run_h3_latest_seeded_recovery_wins_smoke`
   `run_h3_newer_recovery_survives_older_consumed_recovery_smoke`
   `run_h3_duplicate_acceptance_after_newer_recovery_execution_smoke`

Observed post-eighth-slice file position:

1. `service.py` line count reduced further from `10,257` to `9,706`
2. `conversation_control_smokes.py` now owns the newest recovery-authority selection family instead of leaving that precedence logic inline in the facade

Verification after the eighth extraction:

1. local structural `py_compile` passed before syncing back to the server
2. server-side `python3 -m py_compile ai_assistant_ui/qwen_chat/service.py ai_assistant_ui/qwen_chat/evaluation/conversation_control_smokes.py` passed
3. the primary `397`-test refactor guard suite remained `OK`
4. targeted broader monitoring on `test_clarification_resolution_contracts` still shows the same single pre-existing failure:
   `test_artifact_boundary_option_resolution_beats_new_request_detection`

Updated practical reading after the eighth slice:

1. `SR1` is still progressing the right way: the facade is losing late recovery-authority logic by subsystem rather than by ad hoc cleanup
2. the evaluation seam now owns a wider share of conversation-control precedence behavior, which makes the later stage-based service split safer and easier to reason about
3. the next bounded `SR1` move should start from the remaining non-H3 late inline evaluation / hardening gravity that still lives in `service.py`, because the inline H3 recovery-authority cluster is now cleared

Completed in the ninth live `SR1` extraction slice:

1. moved the entire late inline `H4` adversarial-boundary evaluation family out of `service.py`
2. moved the late inline `H5` release-gate evaluation family out of `service.py`
3. moved the post-contract regression-suite aggregator out of `service.py`
4. extended the shared `ConversationControlSmokeDependencies` contract so the evaluation seam can receive rollout-status helpers and hardening-suite entrypoints instead of reaching back into the facade
5. converted eight matching `service.py` entrypoints into thin compatibility wrappers:
   `run_h4_inferred_operational_evidence_stays_bounded_smoke`
   `run_h4_mixed_metric_request_stays_bounded_smoke`
   `run_h4_long_multisentence_followup_stays_bounded_smoke`
   `run_h4_creative_followup_after_reasoning_is_refused_smoke`
   `run_h4_recommendation_guarantee_stays_bounded_smoke`
   `run_h4_adversarial_suite`
   `run_h5_release_gate_rollout_probe`
   `run_h5_release_gate_sanity_pack`
   `run_h5_release_gate_suite`
   `run_post_contract_regression_suite`

Observed post-ninth-slice file position:

1. `service.py` line count reduced further from `9,706` to `9,225`
2. `conversation_control_smokes.py` now owns the late adversarial-boundary, release-gate, and regression evaluation families instead of leaving that tail-end test gravity inline in the facade

Verification after the ninth extraction:

1. local structural `py_compile` passed before syncing back to the server
2. server-side `python3 -m py_compile ai_assistant_ui/qwen_chat/service.py ai_assistant_ui/qwen_chat/evaluation/conversation_control_smokes.py` passed
3. the primary `397`-test refactor guard suite remained `OK`
4. targeted broader monitoring on `test_clarification_resolution_contracts` still shows the same single pre-existing failure:
   `test_artifact_boundary_option_resolution_beats_new_request_detection`

Updated practical reading after the ninth slice:

1. `SR1` continues to move in the right enterprise direction: the facade is shedding evaluation-only ownership by seam, not by cosmetic trimming
2. the evaluation seam now owns almost all of the late post-contract smoke and release-gate gravity that used to sit at the end of `service.py`
3. the next bounded `SR1` move should inspect the remaining inline non-evaluation orchestration gravity and decide whether any small compatible extraction can still happen before we declare `SR1` stable enough to begin the next dedicated refactor seam

Completed in the tenth live `SR1` extraction slice:

1. moved the remaining late inline `H3` fresh-grounded replacement family out of `service.py`
2. placed those bodies into the existing `qwen_chat/evaluation/conversation_control_smokes.py` seam
3. converted three matching `service.py` entrypoints into thin compatibility wrappers:
   `run_h3_latest_fresh_grounded_query_wins_smoke`
   `run_h3_repeated_identical_fresh_query_replaces_grounding_smoke`
   `run_h3_repeated_identical_composite_grounded_query_replaces_grounding_smoke`
4. removed the now-unused inline retry helpers from `service.py`:
   `_run_smoke_reasoning_followup_with_retry`
   `_run_smoke_fresh_query_turn_with_retry`

Observed post-tenth-slice file position:

1. `service.py` line count reduced further from `9,226` to `8,773`
2. `conversation_control_smokes.py` now owns the late fresh-grounding replacement family instead of leaving that continuity / replacement validation inline in the facade

Verification after the tenth extraction:

1. local structural `py_compile` passed before syncing back to the server
2. server-side `python3 -m py_compile ai_assistant_ui/qwen_chat/service.py ai_assistant_ui/qwen_chat/evaluation/conversation_control_smokes.py` passed
3. the primary `397`-test refactor guard suite remained `OK`
4. targeted broader monitoring on `test_clarification_resolution_contracts` still shows the same single pre-existing failure:
   `test_artifact_boundary_option_resolution_beats_new_request_detection`

Updated practical reading after the tenth slice:

1. `SR1` is still progressing correctly: late conversation-control evaluation gravity continues moving out by ownership seam, not by one-off cleanup
2. removing the now-unused retry helpers is a good sign that this slice reduced true facade gravity instead of just moving bodies elsewhere
3. the next bounded `SR1` decision should inspect the remaining inline H3 clusters and stop if the next candidate would require a larger subsystem move rather than another clean small seam

Completed in the eleventh live `SR1` extraction slice:

1. verified and stabilized the remaining late inline `H3` pending-clarification reopen / redirect seam after its move into `qwen_chat/evaluation/conversation_control_smokes.py`
2. confirmed that six matching `service.py` entrypoints are now thin compatibility wrappers instead of inline facade-owned bodies:
   `run_h3_option_list_then_override_switches_focus_smoke`
   `run_h3_branch_restore_reopens_pending_clarification_smoke`
   `run_h3_question_restore_reopens_pending_clarification_smoke`
   `run_h3_pending_discard_redirects_to_fresh_supplier_focus_smoke`
   `run_h3_soft_chained_pending_redirect_to_fresh_supplier_focus_smoke`
   `run_h3_pending_discard_redirects_to_balance_sheet_smoke`
3. kept this slice intentionally small: no new facade behavior was added, and no new orchestration authority was introduced into `service.py`

Observed post-eleventh-slice file position:

1. `service.py` line count is now `8,299`
2. `conversation_control_smokes.py` line count is now `5,345`
3. the facade keeps shrinking while the extracted evaluation seam absorbs the bounded late `H3` continuation hardening coverage

Verification after the eleventh extraction:

1. local structural `py_compile` passed for `service.py`
2. local structural `py_compile` passed for `conversation_control_smokes.py`
3. server-side verification is the next step before we treat this slice as live

Updated practical reading after the eleventh slice:

1. `SR1` is still moving in the right enterprise direction: we are reducing true facade gravity by seam ownership, not by cosmetic line shuffling
2. this slice is a good example of disciplined refactor behavior because it closed a known pending-clarification seam without introducing new service-level branching
3. the next bounded `SR1` move should inspect the remaining late inline conversation-control hardening clusters and stop if the next candidate would force a broader subsystem extraction instead of another narrow seam win

Completed in the twelfth live `SR1` extraction slice:

1. moved the remaining late inline `H3` item-list-to-item-detail-to-stock follow-up family out of `service.py`
2. placed that family into `qwen_chat/evaluation/conversation_control_smokes.py` behind one shared seam-local helper instead of duplicating near-identical flow bodies
3. converted two matching `service.py` entrypoints into thin compatibility wrappers:
   `run_h3_ambiguous_item_list_to_stock_followup_smoke`
   `run_h3_option_list_that_you_found_to_stock_followup_smoke`

Observed post-twelfth-slice file position:

1. `service.py` line count reduced further from `8,299` to `8,082`
2. `conversation_control_smokes.py` line count increased from `5,345` to `5,499`
3. this is acceptable for the current refactor chapter because the growth stayed inside the extracted evaluation seam while the facade lost more late hardening ownership

Verification after the twelfth extraction:

1. local structural `py_compile` passed for `service.py`
2. local structural `py_compile` passed for `conversation_control_smokes.py`
3. server-side verification is the next step before we decide whether `SR1` should continue with another bounded seam or stop

Updated practical reading after the twelfth slice:

1. `SR1` continues to move in the right enterprise direction: we are extracting seam-owned evaluation logic, not solving one-off item cases inside the facade
2. using one shared helper for the two item-follow-up variants is materially better than copying two more story-sized blocks into the evaluation module
3. the next bounded `SR1` decision should inspect whether the remaining inline late `H3` active-sequence / historical-branch hardening block is still narrow enough for one more clean extraction; if not, `SR1` should stop and hand off to the next planned refactor seam

Completed in the thirteenth live `SR1` extraction slice:

1. moved the remaining late inline `H3` active-sequence / historical-branch-over-active-sequence hardening family out of `service.py`
2. placed that family into `qwen_chat/evaluation/conversation_control_smokes.py`
3. used one shared seam-local helper for the three targeted-restore-over-active-sequence variants instead of carrying near-duplicate flow bodies in the facade
4. converted four matching `service.py` entrypoints into thin compatibility wrappers:
   `run_h3_active_sequence_override_clears_prior_sequence_smoke`
   `run_h3_targeted_restore_recovers_historical_branch_over_active_sequence_smoke`
   `run_h3_discard_prefixed_targeted_restore_recovers_historical_branch_over_active_sequence_smoke`
   `run_h3_pronoun_discard_targeted_restore_over_active_sequence_smoke`

Observed post-thirteenth-slice file position:

1. `service.py` line count reduced further from `8,082` to `7,670`
2. `conversation_control_smokes.py` line count increased from `5,499` to `5,768`
3. this remains acceptable for the current chapter because the new growth stayed inside the extracted conversation-control evaluation seam while the facade lost another real ownership cluster

Verification after the thirteenth extraction:

1. local structural `py_compile` passed for `service.py`
2. local structural `py_compile` passed for `conversation_control_smokes.py`
3. server-side verification is the next step before we decide whether `SR1` should continue with another bounded seam or stop

Updated practical reading after the thirteenth slice:

1. `SR1` is still moving in the right enterprise direction: we are extracting a shared conversation-control hardening family, not solving special customer or supplier cases inline
2. the active-sequence helper shape is a better enterprise pattern than continuing to duplicate restore-over-sequence flows in the facade
3. after this slice, the remaining inline late `H3` bodies are much smaller and easier to classify, so the next decision should be whether one final bounded `SR1` seam still exists or whether the facade is now stable enough to stop `SR1` and hand off to the next planned refactor seam

## 13. SR2 Progress Update

`SR2` is now in progress.

Completed in the first live `SR2` extraction slice:

1. started the conversation snapshot seam by moving the snapshot assembly subgraph out of `service.py`
2. introduced a dedicated helper module:
   `qwen_chat/conversation_snapshot.py`
3. moved the snapshot-state assembly, historical-branch recovery snapshotting, recent-focus snapshot derivation, and resumable-prior-request arbitration into that module
4. kept `service.py` to thin compatibility wrappers for `_build_conversation_state_snapshot`, `_snapshot_recent_focus_state`, and existing state-integrity test seams
5. used an explicit `ConversationSnapshotDependencies` bundle so the new module reuses existing ownership homes instead of reintroducing facade-only imports
6. preserved shared snapshot utility aliases in `service.py` where restore/control code still depends on them, avoiding a mixed behavior-plus-refactor patch

Observed post-first-`SR2`-slice file position:

1. `service.py` line count reduced further from `7,670` to `7,052`
2. new `conversation_snapshot.py` line count is `745`
3. this is an acceptable enterprise trade because the facade lost one of its largest remaining non-evaluation ownership clusters while the extracted module now owns a coherent snapshot subsystem

Verification after the first `SR2` extraction:

1. local structural `py_compile` passed for `service.py`
2. local structural `py_compile` passed for `conversation_snapshot.py`
3. server-side structural `py_compile` passed for `service.py` and `conversation_snapshot.py`
4. the primary `397`-test refactor guard suite remained `OK`
5. the monitored clarification-resolution suite still shows the same single pre-existing failure:
   `test_artifact_boundary_option_resolution_beats_new_request_detection`

Updated practical reading after the first `SR2` slice:

1. this is not a cosmetic wrapper move; it is the start of the planned snapshot seam extraction
2. the dependency-bundle approach keeps the module integrated with the existing extraction architecture instead of creating a second parallel design
3. the next `SR2` decision should inspect whether the remaining snapshot-adjacent helper surface now justifies a second bounded seam-completion slice or whether the seam is stable enough to pause while another planned refactor track advances
4. any next extraction should keep compatibility wrappers only when they preserve existing contract-test seams; new behavior should continue to live outside the facade

Completed in the second live `SR2` extraction slice:

1. moved single-row recent-focus derivation helpers out of `service.py` and into `qwen_chat/recent_focus_support.py`
2. kept service-level compatibility wrappers for the existing helper names, so contract tests and downstream seams do not need to change during this refactor
3. made `recent_focus_support.py` the owner of both row-column selection and single-row focus state construction for governed master-data and transaction-listing rows
4. kept `conversation_snapshot.py` dependency injection intact; it still receives explicit callbacks, but those callbacks now route to the proper recent-focus support module instead of carrying implementation logic in the facade

Observed post-second-`SR2`-slice file position:

1. `service.py` line count reduced further from `7,052` to `6,991`
2. `conversation_snapshot.py` remains `745` lines
3. `recent_focus_support.py` increased to `1,073` lines because it now owns a coherent recent-focus subdomain that previously lived in the facade

Verification target after the second `SR2` extraction:

1. local structural `py_compile` passed for `service.py`
2. local structural `py_compile` passed for `recent_focus_support.py`
3. server-side structural `py_compile` passed for `service.py`, `recent_focus_support.py`, and `conversation_snapshot.py`
4. the primary `397`-test refactor guard suite remained `OK`
5. the monitored clarification-resolution suite still shows the same single pre-existing failure:
   `test_artifact_boundary_option_resolution_beats_new_request_detection`

Updated practical reading after the second `SR2` slice:

1. this is still enterprise-grade refactoring: we moved policy-backed focus derivation to the existing recent-focus module, not to a one-off product/customer branch
2. the facade is now less responsible for snapshot assembly and row-level recent-focus derivation
3. the remaining snapshot utilities in `service.py` are now compatibility glue or restore/control dependencies, not a standalone snapshot assembly cluster
4. `SR2` can be treated as stable for this chapter unless a later guard test identifies another snapshot-owned helper with meaningful extraction value
5. the next planned service-refactor seam should move to the conversation-control / restore-policy cluster rather than continuing to chase cosmetic snapshot references

## 14. SR3 Progress Update

`SR3` is now in progress.

Completed in the first live `SR3` extraction slice:

1. started the conversation-control / restore-policy seam by moving pure prior-branch restore contract construction out of `service.py`
2. extended `qwen_chat/restore_support.py` so it owns restore-policy construction for:
   - recent-focus restore contracts
   - resumable-prior-request restore contracts
   - active-sequence restore contracts
   - latest non-clarification restore arbitration to contract construction
   - authoritative pending-clarification restore contracts
   - direct restore fallback contracts
   - prior-branch restore contract construction from a conversation snapshot
3. kept route handlers that append messages, write tool payloads, save sessions, or replay governed runtime work inside `service.py`; those are orchestration / journal responsibilities, not pure restore policy
4. preserved service-level compatibility wrappers for existing contract tests and downstream call sites

Observed post-first-`SR3`-slice file position:

1. `service.py` line count reduced from `6,991` to `6,721`
2. `restore_support.py` increased to `969` lines because it now owns a coherent restore-policy construction subdomain

Verification target after the first `SR3` extraction:

1. local structural `py_compile` passed for `service.py`
2. local structural `py_compile` passed for `restore_support.py`
3. server-side structural `py_compile` passed for `service.py` and `restore_support.py`
4. the primary `397`-test refactor guard suite remained `OK`
5. the monitored clarification-resolution suite still shows the same single pre-existing failure:
   `test_artifact_boundary_option_resolution_beats_new_request_detection`

Updated practical reading after the first `SR3` slice:

1. this is not a single-case fix; the extracted code handles shared prior-branch restore behavior across pending clarifications, active sequences, recent focus, and resumable prior requests
2. `service.py` is now closer to the target facade role: route selection and session side effects remain there, while restore-policy construction moves to the restore seam
3. `restore_support.py` intentionally keeps the prior-branch restore contract import lazy, because several contract tests import this support module before the Frappe test stub is installed
4. the next `SR3` decision should inspect whether conversation-control decision construction can move next, or whether that belongs to a separate control-decision module rather than `restore_support.py`

Completed in the second live `SR3` extraction slice:

1. moved shared conversation-control decision construction out of `service.py` and into a dedicated helper module:
   `qwen_chat/conversation_control_decisions.py`
2. made the new module own construction of control decision contracts for:
   - clarification-response reentry
   - compound completion reentry
   - compound continuation
   - compound cancellation
   - recent-focus runtime continuation
   - prior-branch restore projection
   - repair-contract follow-up recovery
3. kept session mutation, message appending, tool-payload recording, runtime replay, and final persistence in `service.py`, because those remain orchestration / journal responsibilities until the later turn-journal seam
4. preserved service-level compatibility wrappers for existing test and downstream call sites, so the patch is extraction-oriented rather than a behavior rewrite
5. kept the contract builder import lazy in the new module, matching the existing enterprise guard against importing Frappe-backed contract modules before test stubs are installed

Observed post-second-`SR3`-slice file position:

1. `service.py` line count reduced from `6,721` to `6,515`
2. new `conversation_control_decisions.py` line count is `421`
3. this is an acceptable enterprise trade because a coherent control-decision construction subdomain left the facade, while route ordering and side effects stayed at the orchestration layer

Verification after the second `SR3` extraction:

1. local structural `py_compile` passed for `service.py`
2. local structural `py_compile` passed for `conversation_control_decisions.py`
3. server-side structural `py_compile` passed for `service.py` and `conversation_control_decisions.py`
4. the primary `397`-test refactor guard suite remained `OK`
5. the monitored clarification-resolution suite still shows only the known pre-existing failure:
   `test_artifact_boundary_option_resolution_beats_new_request_detection`

Updated practical reading after the second `SR3` slice:

1. this continues the planned enterprise-grade refactor path: shared control-decision construction is now module-owned instead of embedded as inline facade logic
2. the extraction does not add a payment-entry, customer, supplier, item, or statement-specific branch; it moves a cross-family conversation-control seam
3. `service.py` is now closer to a turn facade, but it still owns too much restore routing and journal-like side-effect sequencing
4. the next `SR3` decision should inspect the remaining inline prior-branch / restore route handlers and only extract a bounded seam if it can be separated without changing route precedence

Completed in the third live `SR3` extraction slice:

1. extracted the pure fresh-governed-replay planning portion of the prior-branch restore route into:
   `qwen_chat/restore_support.py`
2. added `build_prior_branch_restore_fresh_query_plan`, which now owns:
   - restore-mode validation for replay-as-fresh governed query
   - prior recovery payload extraction
   - synthesized governed query message construction
   - governed target-limit extraction
   - follow-up resolution contract construction
   - prior-branch restore execution-path construction
   - governed scope decision contract construction for the replay
3. deliberately kept the route handler in `service.py` responsible for:
   - appending user and assistant/session artifacts
   - recording tool payloads
   - executing the compiled fresh-query lane
   - finalizing and saving the session
4. preserved route precedence and side-effect ordering by replacing only the pure pre-route construction block with the shared plan helper

Observed post-third-`SR3`-slice file position:

1. `service.py` line count reduced from `6,515` to `6,483`
2. `restore_support.py` increased from `969` to `1,047` lines because it now owns one more coherent restore-policy / replay-plan subdomain
3. this is an intentional enterprise trade: route planning moved to a support module, while orchestration and journaling stayed in the facade until the later turn-journal seam

Verification after the third `SR3` extraction:

1. local structural `py_compile` passed for `service.py`
2. local structural `py_compile` passed for `restore_support.py`
3. server-side structural `py_compile` passed for `service.py`, `restore_support.py`, and `conversation_control_decisions.py`
4. the primary `397`-test refactor guard suite remained `OK`
5. the monitored clarification-resolution suite still shows only the known pre-existing failure:
   `test_artifact_boundary_option_resolution_beats_new_request_detection`

Updated practical reading after the third `SR3` slice:

1. this remains a shared-control refactor, not a single business-case fix
2. the facade has less restore-specific construction logic, but still retains the correct route-handler responsibility for runtime side effects
3. further `SR3` extraction should pause unless another pure restore/control construction seam is obvious; moving route handlers themselves should wait for the later journal/orchestration seam

## 15. SR4 Progress Update

`SR4` is now in progress.

Completed in the first live `SR4` extraction slice:

1. started the runtime message compilation seam by moving contextual runtime-message construction out of `service.py`
2. introduced a dedicated helper module:
   `qwen_chat/runtime_message_compilation.py`
3. made the new module own shared runtime-facing message compilation for:
   - runtime text cleanup and normalization
   - contextual detail-request detection
   - grounded entity reference selection
   - recent-focus contextual reference selection
   - contextual entity breakout message construction
   - recent-focus runtime message routing between local transform and shared affordance requery
4. kept `service.py` to compatibility wrappers and the actual orchestration decision of when to call the runtime-message compiler
5. did not add any business-object-specific case branch; the extracted logic applies across supported entity/document focus kinds through shared recent-focus affordance metadata

Observed post-first-`SR4`-slice file position:

1. `service.py` line count reduced from `6,483` to `6,366`
2. new `runtime_message_compilation.py` line count is `210`
3. this is an enterprise-safe extraction because message rewriting now has a coherent module home, while lane ordering and session side effects remain in the facade

Verification after the first `SR4` extraction:

1. local structural `py_compile` passed for `service.py`
2. local structural `py_compile` passed for `runtime_message_compilation.py`
3. server-side structural `py_compile` passed for `service.py` and `runtime_message_compilation.py`
4. the primary `397`-test refactor guard suite remained `OK`
5. the monitored clarification-resolution suite still shows only the known pre-existing failure:
   `test_artifact_boundary_option_resolution_beats_new_request_detection`

Updated practical reading after the first `SR4` slice:

1. this starts the planned runtime-message compilation seam without mixing behavior change into the refactor
2. `service.py` is closer to the target facade shape because runtime message construction is now delegated to a named stage helper
3. the next `SR4` decision should inspect whether capability requery and recovery-message wrappers can be consolidated into this seam, but only if doing so does not duplicate ownership already held by `requery_message_support.py` or `recovery_support.py`

`SR4` wrapper inspection result:

1. capability requery message construction is already owned by `qwen_chat/requery_message_support.py`
2. recovery governed-query and recovery-guidance message construction is already owned by `qwen_chat/recovery_support.py`
3. those wrappers should not be moved again just to reduce line count, because that would create duplicate ownership instead of an enterprise seam
4. the practical next seam is evidence / boundary response construction, which still had non-trivial rendering and contract assembly inside `service.py`

## 16. SR5 Progress Update

`SR5` is now in progress.

Completed in the first live `SR5` extraction slice:

1. started the evidence / boundary response seam by moving entity-detail direct-evidence response construction out of `service.py`
2. introduced a dedicated helper module:
   `qwen_chat/evidence_response_support.py`
3. made the new module own:
   - entity-detail evidence request payload construction
   - entity-detail clarification signal payload construction
   - direct grounded artifact evidence answer fallback selection
   - rendered response payload selection
   - narrative rendering / narrative contract construction for direct evidence answers
   - stable response payload assembly for evidence direct-answer outputs
4. kept `service.py` as compatibility wrappers plus the orchestration owner that decides when to use direct evidence response handling
5. removed now-unused entity-detail evidence contract imports and semantic alias detection imports from `service.py`

Observed post-first-`SR5`-slice file position:

1. `service.py` line count reduced from `6,365` to `6,278`
2. new `evidence_response_support.py` line count is `169`
3. `runtime_message_compilation.py` remains `210` lines

Verification after the first `SR5` extraction:

1. local structural `py_compile` passed for `service.py`
2. local structural `py_compile` passed for `evidence_response_support.py`
3. server-side structural `py_compile` passed for `service.py`, `evidence_response_support.py`, and `runtime_message_compilation.py`
4. the primary `397`-test refactor guard suite remained `OK`
5. the monitored clarification-resolution suite still shows only the known pre-existing failure:
   `test_artifact_boundary_option_resolution_beats_new_request_detection`

Updated practical reading after the first `SR5` slice:

1. this is a real enterprise seam, not a single-case customer/supplier/product fix
2. direct evidence response construction now has an implementation home separate from the turn facade
3. session mutation and lane ordering remain in `service.py`, which is correct until the later turn-journal / orchestration-stage refactor
4. the next `SR5` decision should inspect remaining boundary/evidence wrappers and stop if the rest is only compatibility glue

Completed in the second live `SR5` extraction slice:

1. moved evidence/direct-boundary follow-up preservation policy out of `service.py` and into `qwen_chat/evidence_response_support.py`
2. made the evidence response module own:
   - artifact-boundary clarification continuation preservation
   - current-artifact direct-evidence follow-up preservation
   - requested-mode augmentation for `entity_detail_evidence` and `direct_evidence_followup`
   - safe conversion from would-be capability requery back to grounded follow-up when the current artifact is authoritative
3. kept `service.py` wrappers and call sites stable so lane ordering and contract-test seams are unchanged
4. confirmed the remaining append-boundary / append-recovery wrappers are side-effect bridges into session tool payloads and should stay in the facade until the later turn-journal seam

Observed post-second-`SR5`-slice file position:

1. `service.py` line count reduced from `6,278` to `6,224`
2. `evidence_response_support.py` increased from `169` to `260` lines because it now owns the direct-evidence response and preservation policy subdomain

Verification after the second `SR5` extraction:

1. local structural `py_compile` passed for `service.py`
2. local structural `py_compile` passed for `evidence_response_support.py`
3. server-side structural `py_compile` passed for `service.py` and `evidence_response_support.py`
4. the primary `397`-test refactor guard suite remained `OK`
5. the monitored clarification-resolution suite still shows only the known pre-existing failure:
   `test_artifact_boundary_option_resolution_beats_new_request_detection`

Updated practical reading after the second `SR5` slice:

1. this remains an enterprise refactor: evidence follow-up preservation is shared policy, not a single-case repair
2. `service.py` is closer to a facade because it no longer owns the detailed evidence-preservation contract construction
3. further `SR5` extraction should be conservative; the remaining boundary/recovery appenders are tied to session mutation and should wait for the turn-journal seam unless a pure construction block is found

`SR5` wrapper inspection result:

1. remaining boundary/recovery appenders are side-effect bridges into session tool payloads
2. moving those appenders under `SR5` would mix evidence policy extraction with journal/persistence ownership
3. evidence-response extraction should pause here; the next appropriate `SR5` seam is the turn-journal / persistence seam, where session append sequencing can be centralized intentionally

## 17. SR5 Turn Journal And Persistence Progress Update

`SR5` is now in progress.

Completed in the first live `SR5` turn-journal extraction slice:

1. started the turn-journal seam with a deliberately small utility module:
   `qwen_chat/turn_journal.py`
2. introduced shared journal helpers for:
   - coercing either contract objects or dict payloads into safe tool payload dictionaries
   - appending ordered optional payload lists while skipping empty or unsupported values
3. replaced repeated optional payload append blocks in:
   - prior-branch restore pending-clarification reopen route
   - prior-branch restore fresh-governed replay route
   - compound completion reentry route
   - compound cancellation route
   - main turn artifact append sequence
4. preserved exact append order by passing ordered value lists from `service.py`
5. deliberately did not move route handlers, session save calls, or assistant-message writes; those remain facade responsibilities until a larger journal-stage refactor is explicitly approved

Observed post-first-`SR5` turn-journal slice file position:

1. `service.py` line count moved from `6,224` to `6,232`
2. new `turn_journal.py` line count is `27`
3. the facade line count is approximately flat because this first journal slice adds compatibility wiring while reducing repeated append bodies; the value is ownership consolidation, not immediate line reduction

Verification after the first `SR5` turn-journal extraction:

1. local structural `py_compile` passed for `service.py`
2. local structural `py_compile` passed for `turn_journal.py`
3. server-side structural `py_compile` passed for `service.py` and `turn_journal.py`
4. the primary `397`-test refactor guard suite remained `OK`
5. the monitored clarification-resolution suite still shows only the known pre-existing failure:
   `test_artifact_boundary_option_resolution_beats_new_request_detection`

Updated practical reading after the first `SR5` turn-journal slice:

1. this is the right place to centralize session append mechanics, but it must remain conservative because journal ordering is high-risk
2. this slice is intentionally small and characterization-test guarded
3. the next `SR5` decision should inspect whether more repeated append blocks can use the same helper without changing ordering; if not, pause `SR5` until the dedicated `SR6` stage-based `handle_qwen_user_message` split is ready

Completed in the second live `SR5` turn-journal extraction slice:

1. extended the shared turn-journal payload helper to two additional simple append paths:
   - repair-handled cleanup plus repair-control decision append
   - pending-clarification handled conversation-control decision append
2. preserved existing save behavior: repair cleanup still only forces a save when a repair-control decision contract is produced
3. inspected the remaining direct `_append_tool_payload(session_doc, ...)` uses and found only a single execution-path append outside the wrapper itself; converting that alone would add noise rather than architectural value

Observed post-second-`SR5` turn-journal slice file position:

1. `service.py` line count is `6,235`
2. `turn_journal.py` remains `27` lines
3. this slice does not target line-count reduction; it reduces journal idiom drift while keeping route ordering explicit

Verification after the second `SR5` turn-journal extraction:

1. local structural `py_compile` passed for `service.py`
2. local structural `py_compile` passed for `turn_journal.py`
3. server-side structural `py_compile` passed for `service.py` and `turn_journal.py`
4. the primary `397`-test refactor guard suite remained `OK`
5. the monitored clarification-resolution suite still shows only the known pre-existing failure:
   `test_artifact_boundary_option_resolution_beats_new_request_detection`

Updated practical reading after the second `SR5` turn-journal slice:

1. `SR5` should pause after this cleanup unless we intentionally begin the larger `SR6` facade stage split
2. additional piecemeal conversions would now be mostly cosmetic and could increase precedence risk
3. the next practical refactor decision should be whether to start a dedicated stage split for `handle_qwen_user_message` or return to feature implementation with the current facade gravity reduced

## 18. Refactor Pause Gate

Decision: pause piecemeal `service.py` extraction after the second `SR5` turn-journal slice.

Reason:

1. the highest-value low-risk seams from the current chapter have already been extracted
2. remaining direct boundary/recovery appenders are mostly session side-effect bridges, not pure policy helpers
3. remaining direct journal append points are no longer broad repeated blocks; further piecemeal conversion would be mostly cosmetic
4. the primary guard suite has stayed stable through each extraction slice
5. the known clarification-resolution failure remains unchanged and should not be mixed into the refactor chapter

Current extracted seam map:

1. `conversation_control_smokes.py` owns extracted smoke / evaluation helpers
2. `conversation_snapshot.py` owns conversation snapshot assembly
3. `recent_focus_support.py` owns recent-focus derivation and affordance helpers
4. `restore_support.py` owns prior-branch restore policy and replay planning
5. `conversation_control_decisions.py` owns shared conversation-control decision construction
6. `runtime_message_compilation.py` owns contextual runtime-message construction
7. `evidence_response_support.py` owns direct evidence response and evidence-preservation policy
8. `turn_journal.py` owns the first shared journal payload append utility for `SR5`

Enterprise assessment:

1. the refactor moved shared ownership seams, not single-case customer / supplier / item fixes
2. `service.py` is still large, but it is now less responsible for policy construction and helper-domain behavior
3. the next meaningful reduction requires `SR6`: a stage-based split of `handle_qwen_user_message`, not more wrapper trimming
4. `SR6` is higher risk because it can change route precedence, so it should be planned as a dedicated chapter with characterization coverage

Recommended next path:

1. stop current piecemeal refactor work here
2. return to the active governed assistant feature roadmap if feature delivery is the priority
3. separately plan `SR6` only when the team is ready for a larger stage-based facade split
4. keep the current guard suite mandatory for any further facade or journal work

Proposed future `SR6` shape, not started:

1. introduce a typed turn context object for loaded session/request state
2. split `handle_qwen_user_message` into named stages without changing behavior
3. move stage-local journal writes behind a recorder interface only after stage split is stable
4. add characterization tests for lane precedence before moving route handlers
5. only then reduce the remaining facade route blocks

`SR7` remains the closure review and is not started.

Correct phase meaning from this point forward:

1. `SR5` = turn journal and persistence seam; currently paused after two guarded journal slices
2. `SR6` = facade stage split for `handle_qwen_user_message`; not started
3. `SR7` = refactor closure review; not started

Definition of done for this refactor pause:

1. all extracted modules compile on server
2. primary `397`-test guard suite remains `OK`
3. current known clarification-resolution failure is documented as unchanged
4. no further cosmetic extraction is queued under `SR1` through `SR5`
5. next work is either feature-roadmap continuation or a separately approved `SR6` stage-split chapter
