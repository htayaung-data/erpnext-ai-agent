# V1-IB-E-3 Rejected / Historical Artifact Exclusion Plan

Decision target:
`v1_ib_e_3_rejected_historical_artifact_exclusion_plan_ready_for_counterpart_review`

Date: 2026-06-01

## 1. Scope And Boundary

V1-IB-E-3 is a report-only planning slice. It defines which rejected, historical, unrelated, and unknown artifacts must be excluded, quarantined, investigated, or manifest-labeled before any future clean package/review branch can be considered package-ready.

Changed file in this slice:

- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_e_3_rejected_historical_artifact_exclusion_plan_2026-06-01.md`

No branch was created. No branch was switched. No staging occurred. No files were committed or pushed. No source files were edited. No test files were edited. No old reports were edited. No package config changed. No files were moved, deleted, renamed, or archived. No source/test/report/config behavior changed except adding this E-3 report.

No cleanup, archive, package, browser/API UAT, deployment, strict enforcement, release readiness, enterprise/product closure, or V2 work occurred. No keyword, regex, synonym, punctuation, phrase, lexical, or no-alarm route authority was added.

## 2. Exclusion Source

D-4-E-1 accepted-evidence manifest provides the artifact classification basis for this plan.

E-2 defines accepted artifacts to preserve/reapply later on a QA-approved clean branch. E-3 defines artifacts that must not be included as current release evidence.

The current dirty tree must not be cleaned, archived, deleted from, or staged directly. Exclusion in E-3 means future clean-branch package planning must not reapply these artifacts as current release evidence unless a later QA-approved slice explicitly reclassifies them.

## 3. Rejected Artifacts To Exclude

Rejected artifacts count: `5`.

| Artifact | Classification | Why excluded | Risk if included | Future action | Verification required after exclusion |
| --- | --- | --- | --- | --- | --- |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_structural_classifier.py` | `rejected_superseded` | Old rejected structural classifier; accepted B path is proposal classifier evidence-only plus validator authority | Could be mistaken for accepted V1-IB-B classifier or route authority | `package_exclude` / `quarantine_later` | Static import scan proves runtime does not import it; package tree excludes it |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_structural_classifier.py` | `rejected_superseded` | Tests old rejected structural classifier assumptions | Could be mistaken for accepted V1-IB-B tests | `package_exclude` / `quarantine_later` | Current accepted test suite excludes it |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_deterministic_structural_classifier_2026-05-28.md` | `rejected_superseded` | Rejected B structural classifier report | Could be misread as accepted B authority evidence | `package_exclude` or historical rejected archive | Release evidence scan excludes it from current evidence |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_a_factual_lookup_precedence_raw_safety_hardening_2026-05-28.md` | `rejected_superseded` | Rejected/superseded structural B-A report, not the accepted evidence strictness fix | Could be confused with accepted B-A classifier strictness evidence | `package_exclude` or historical rejected archive | Release evidence scan labels it rejected or excludes it |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_b_passive_action_needed_structural_hardening_2026-05-28.md` | `rejected_superseded` | Rejected/superseded structural B-B report, not accepted B-B closure | Could be confused with accepted proposal-classifier closure checkpoint | `package_exclude` or historical rejected archive | Release evidence scan labels it rejected or excludes it |

Rejected artifacts must not be staged as current package evidence.

## 4. Historical / Superseded Artifacts To Exclude As Current Evidence

Historical/superseded artifacts may be preserved only in a QA-approved archive or manifest-labeled historical location. They must not be included as current release evidence.

### V1-R/Y Lexical Patch-Loop Reports

Count: `31`.

Classification: `historical_superseded`.

Why not current evidence:
These reports document the old V1-R/Y lexical/regex/phrase/patch-loop hardening path. The accepted V1-IB path supersedes it with validator-owned authority, evidence-only classifier output, service-level adversarial tests, trace redaction, and legacy restrict-only controls.

Future action:
`preserve_historical_archive` only after QA approval, or package-exclude from current release evidence.

Full list:

- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_a_intent_boundary_lexical_regex_fragility_audit_2026-05-25.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_b_lexical_false_allow_hardening_2026-05-25.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_c_lexical_false_allow_hardening_2026-05-25.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_d_true_followup_collision_hardening_2026-05-26.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_e_remaining_unsafe_true_followup_collision_fix_2026-05-26.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_f_structural_true_followup_unsafe_verb_guard_2026-05-26.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_g_true_followup_positive_allowlist_hardening_2026-05-26.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_h_read_only_allowlist_unsafe_clause_veto_2026-05-26.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_i_read_only_unsafe_clause_decision_before_entity_fix_2026-05-26.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_j_modal_less_read_only_unsafe_clause_fix_2026-05-26.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_k_gerund_modal_less_subject_read_only_unsafe_clause_fix_2026-05-26.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_l_erp_id_targeted_read_only_unsafe_decision_clause_fix_2026-05-26.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_long_conversation_boundary_context_bleed_regression_tests_2026-05-25.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_m_erp_id_subject_decision_clause_fix_2026-05-26.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_n_decision_phrase_structural_hardening_2026-05-26.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_o_remaining_stay_remain_decision_phrase_fix_2026-05-26.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_p_erp_id_role_retention_decision_clause_fix_2026-05-26.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_q_erp_id_list_membership_decision_clause_fix_2026-05-26.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_r_intent_boundary_classifier_consolidation_structural_decision_predicate_2026-05-26.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_s_structural_predicate_completeness_fix_2026-05-26.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_t_structural_add_approve_admission_decision_fix_2026-05-26.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_u_stocking_catalog_admission_decision_fix_2026-05-26.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_v_catalog_stocking_passive_carry_source_decision_fix_2026-05-27.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_w_product_procurement_availability_decision_fix_2026-05-27.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_x_restock_replenish_inventory_decision_fix_2026-05-27.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_y_inventory_adjustment_on_hand_phase_out_decision_fix_2026-05-27.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_z1_inventory_build_cut_drawdown_liquidation_decision_fix_2026-05-27.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_z2_inventory_disposal_build_up_decision_fix_2026-05-27.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_z3_obsolescence_scrap_write_down_decision_fix_2026-05-27.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_z4_enterprise_structural_intent_classifier_refactor_2026-05-27.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_z5_pricing_discount_valuation_boundary_fix_2026-05-27.md`

### Older V1-R Reports

Count: `14`.

Classification: `historical_superseded`.

Why not current evidence:
These reports are older V1-R setup, provisioning, staged-index, boundary, classifier, pre-routing, and final-emission reports. They predate or are superseded by the accepted V1-IB A/B/C/D/E evidence chain.

Future action:
`preserve_historical_archive` after QA approval or package-exclude from current release evidence.

Full list:

- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_l_controlled_environment_setup_decision_2026-05-24.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_m_controlled_environment_setup_plan_readiness_decision_2026-05-25.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_n_controlled_environment_provisioning_approval_request_2026-05-25.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_o_a_provisioning_prerequisite_plan_fix_2026-05-25.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_o_b_provisioning_infrastructure_options_decision_2026-05-25.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_o_controlled_environment_provisioning_execution_plan_2026-05-25.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_q_staged_index_construction_request_2026-05-24.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_u_enterprise_boundary_context_bleed_fix_plan_2026-05-25.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_v_a_intent_boundary_classifier_hardening_2026-05-25.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_v_b_remaining_intent_boundary_classifier_hardening_2026-05-25.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_v_intent_boundary_contract_schema_classifier_tests_2026-05-25.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_w_pre_routing_intent_boundary_gate_2026-05-25.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_x_b_final_emission_veto_payload_sanitization_fix_2026-05-25.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_x_post_selection_final_emission_veto_2026-05-25.md`

### Old Direct Lexical / User-Intent Tests

Count: `5`.

Classification: `historical_superseded` / `package_excluded_candidate`.

Why not current evidence:
These tests exercise the old direct user-intent lexical path. Useful probes may be rewritten as V1-IB tests later, but the old files must not be used as current release proof because lexical/phrase/regex/no-alarm logic cannot authorize routes.

Future action:
`quarantine_later` unless rewritten/aligned and accepted in a later bounded slice.

Full list:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_user_intent_boundary_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_user_intent_boundary_final_emission_veto.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_user_intent_boundary_lexical_fragility.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_user_intent_boundary_long_context_regression.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_user_intent_boundary_prerouting_gate.py`

## 5. Unknown / Unrelated Artifacts

| Artifact | Classification | Current known facts | Risk if included | Future action |
| --- | --- | --- | --- | --- |
| `=` | `unknown_needs_review` | Root-level untracked ASCII text file, size previously recorded as `85023` bytes, appears to contain static grep/output snippets; full semantic review not completed | Unknown root-level artifact could leak snippets, confuse package contents, or contaminate release evidence | `investigate`; `do_not_package` until classified |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_10_g_revised_docs_packaging_boundary_approval_request_2026-05-24.md` | `unrelated` / `needs_qa_decision` | Governance report outside the accepted V1-IB evidence chain | Could contaminate V1-IB release evidence with unrelated package decision context | `needs_qa_decision`; do not include as current V1-IB evidence unless QA approves |

## 6. Exclusion Mechanisms For Future Clean Branch

Future clean branch exclusion mechanisms, not implemented in E-3:

- Do not reapply excluded files to the clean branch.
- If historical preservation is required, move to a package-excluded archive only after QA approval.
- Include the accepted-evidence manifest in the release packet.
- Add a package-exclusion verification scan.
- Add a static import scan proving rejected classifier source is absent from runtime imports.
- Add a report family scan proving old V1-R/Y reports are not current evidence.
- Add a test-family scan proving old direct lexical tests are absent from the accepted current test suite unless rewritten/aligned.
- Add an unknown-file scan proving file `=` is absent from package contents or QA-classified.

## 7. Future Verification After Exclusion

Future clean branch must prove:

- rejected structural classifier source is absent from runtime package or package-excluded
- rejected structural classifier test is absent from current accepted test suite
- old lexical tests are absent from current accepted test suite unless rewritten/aligned
- old V1-R/Y reports are not in the current release evidence path
- unknown file `=` is absent
- accepted baseline still passes
- D tests still pass
- no runtime imports rejected classifier
- no package evidence labels rejected/historical reports as current evidence
- no lexical/phrase/regex/no-alarm artifact is described as route-authority proof

## 8. Non-Negotiable Rules

Future exclusion work must follow these rules:

- no silent deletion from the dirty worktree
- no deleting history without QA-approved archive/package plan
- no rejected classifier in package source
- no rejected structural classifier test in the accepted current test suite
- no lexical patch-loop report as enterprise evidence
- no old phrase-table tests as release proof
- no unknown files in package
- no package branch work until QA approves an implementation boundary
- no branch creation or staging until explicitly approved
- no browser/API UAT until package-readiness gates allow UAT planning

## 9. Recommended Next Step

Recommended next step:

```text
V1-IB-E-4 unknown file "=" classification/disposition plan
```

Reason:
The unknown root-level file `=` remains a package blocker. It must be classified before clean branch implementation planning or package-readiness work can safely proceed.

## 10. Verification For E-3

Read-only inventory recorded:

| Inventory item | Result |
| --- | --- |
| Rejected artifacts count/list | PASS: `5` artifacts listed in Section 3 |
| V1-R/Y historical reports count/list | PASS: `31` reports listed in Section 4 |
| Older V1-R reports count/list | PASS: `14` reports listed in Section 4 |
| Old direct lexical/user-intent tests count/list | PASS: `5` tests listed in Section 4 |
| Unknown file `=` confirmation | PASS: remains present and is excluded from package plan |
| Unrelated EC-10-G report confirmation | PASS: remains needs-QA-decision and is excluded from current V1-IB evidence plan |

Verification after report copy:

| Check | Result |
| --- | --- |
| Report present | PASS |
| `git diff --check` | PASS |
| `git diff --cached --check` | PASS |
| Qwen enterprise guardrail | PASS |
| Fake-Frappe service import | PASS: `FAKE_FRAPPE_IMPORT_PASS` |
| Direct assistant inventory | PASS: `0 / 1 / 27` |
| Raw assistant append scan | PASS: only `authorized_emission.py:271` and `authorized_emission.py:327` |
| Excluded/artifact scan | PASS |
| Staged files count | PASS: `0` |
| Dirty worktree count | PASS: `156` after adding E-3 report |
| Report hygiene scan | PASS: decision target present; no placeholder verification results remain |

If later verification finds an active runtime dependency on a rejected/historical artifact, do not fix it opportunistically. Document the blocker, recommend a narrow follow-up slice, and stop.

Do not claim clean branch creation, cleanup, exclusion implementation, package readiness, release readiness, UAT readiness, E implementation, enterprise/product closure, or V2 work from E-3.
