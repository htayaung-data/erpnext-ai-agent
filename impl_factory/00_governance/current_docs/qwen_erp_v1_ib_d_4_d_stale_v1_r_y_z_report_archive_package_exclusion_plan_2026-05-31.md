# V1-IB-D-4-D Stale V1-R/Y/Z Report Archive / Package-Exclusion Plan

Decision target:
`v1_ib_d_4_d_stale_v1_r_y_z_report_archive_package_exclusion_plan_ready_for_counterpart_review`

Date: 2026-05-31

## 1. Scope And Boundary

V1-IB-D-4-D is a report-only planning slice. It defines how stale V1-R/Y lexical patch-loop reports and rejected structural-classifier reports should be archived, labeled, or package-excluded later so they cannot be mistaken for current V1-IB release evidence.

No source, test, runtime, packaging config, old report, import, deletion, move, rename, archive, package-exclusion, staging, commit, push, deployment, browser/API UAT, strict enforcement, release-readiness, or V2 work occurred.

No old reports were edited, moved, renamed, deleted, archived, or package-excluded. This slice only adds the D-4-D governance report.

## 2. Accepted Evidence Model

### Accepted Current V1-IB Evidence

Current release evidence is the accepted V1-IB chain, including:

- V1-IB-0 architecture plan and amendments.
- V1-IB-A through V1-IB-A-Q contract/validator foundation and closure.
- V1-IB-B proposal-classifier implementation, B-A evidence strictness fix, and B-B closure.
- V1-IB-C runtime integration plan, implementation, fixes, C-3 adversarial service evidence, and C-5 formal runtime integration closure.
- V1-IB-D authority inventory, D-2 authority consistency, D-3 trace/diagnostic redaction audit, and D-4 legacy/rejected artifact planning through D-4-C.

Current enterprise evidence is contract authority, validator-owned replay/invariants, fail-closed runtime gates, current-message identity checks, trace redaction, final-emission vetoes, adversarial service tests, and legacy restrict-only tests. It is not lexical phrase patch-loop report evidence.

### Historical / Superseded Evidence

The V1-R/Y lexical hardening reports are historical and superseded. They document an earlier lexical/structural patch-loop path and should not be used as current release authority.

### Rejected / Superseded Evidence

The 2026-05-28 V1-IB-B deterministic structural classifier reports are rejected/superseded by accepted V1-IB-B proposal-classifier evidence. They are not accepted V1-IB-B release evidence.

### Unknown / Unclassified Evidence

The requested V1-R/Y/Z and rejected V1-IB-B structural families can be classified without a blocker.

Static keyword scan also found older non-D-4-D families with lexical/regex/phrase wording, including EC-7H/EC-7I safety reports and V1-R-V/V1-R-X reports. These are outside this D-4-D primary inventory. They should be included in a later accepted-evidence manifest/package-readiness review, but they do not block the D-4-D plan because they are not V1-R/Y/Z or rejected V1-IB-B structural reports.

## 3. Stale Report Inventory

### V1-R/Y Reports

Count: `31`

All scanned V1-R/Y reports are currently `??` untracked dirty artifacts and classified as historical/superseded evidence. They are not current release evidence because V1-IB superseded the lexical/structural patch-loop authority model with contract authority, accepted validator invariants, and runtime fail-closed gates.

Package/release risk if left in `current_docs`:
future agents, QA reviewers, or package reviewers may mistake old lexical/phrase hardening reports for current enterprise closure evidence.

Proposed future action:
include them in an accepted-evidence manifest, then move to a package-excluded historical archive or label/package-exclude them in an approved cleanup/package-refresh branch.

Files:

| Path | Git status | Classification | Proposed future action |
| --- | --- | --- | --- |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_a_intent_boundary_lexical_regex_fragility_audit_2026-05-25.md` | `??` | Historical/superseded lexical audit | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_b_lexical_false_allow_hardening_2026-05-25.md` | `??` | Historical/superseded lexical false-allow hardening | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_c_lexical_false_allow_hardening_2026-05-25.md` | `??` | Historical/superseded lexical false-allow hardening | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_d_true_followup_collision_hardening_2026-05-26.md` | `??` | Historical/superseded followup collision hardening | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_e_remaining_unsafe_true_followup_collision_fix_2026-05-26.md` | `??` | Historical/superseded followup collision fix | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_f_structural_true_followup_unsafe_verb_guard_2026-05-26.md` | `??` | Historical/superseded structural/lexical guard | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_g_true_followup_positive_allowlist_hardening_2026-05-26.md` | `??` | Historical/superseded allowlist hardening | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_h_read_only_allowlist_unsafe_clause_veto_2026-05-26.md` | `??` | Historical/superseded allowlist unsafe-clause veto | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_i_read_only_unsafe_clause_decision_before_entity_fix_2026-05-26.md` | `??` | Historical/superseded lexical ordering fix | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_j_modal_less_read_only_unsafe_clause_fix_2026-05-26.md` | `??` | Historical/superseded phrase hardening | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_k_gerund_modal_less_subject_read_only_unsafe_clause_fix_2026-05-26.md` | `??` | Historical/superseded phrase hardening | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_l_erp_id_targeted_read_only_unsafe_decision_clause_fix_2026-05-26.md` | `??` | Historical/superseded ERP-ID lexical fix | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_long_conversation_boundary_context_bleed_regression_tests_2026-05-25.md` | `??` | Historical context-bleed evidence, superseded by C-3-6/D tests | Archive/package-exclude after useful probes are preserved in V1-IB tests if needed |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_m_erp_id_subject_decision_clause_fix_2026-05-26.md` | `??` | Historical/superseded ERP-ID decision clause fix | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_n_decision_phrase_structural_hardening_2026-05-26.md` | `??` | Historical/superseded decision phrase hardening | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_o_remaining_stay_remain_decision_phrase_fix_2026-05-26.md` | `??` | Historical/superseded phrase hardening | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_p_erp_id_role_retention_decision_clause_fix_2026-05-26.md` | `??` | Historical/superseded role retention clause fix | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_q_erp_id_list_membership_decision_clause_fix_2026-05-26.md` | `??` | Historical/superseded list-membership clause fix | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_r_intent_boundary_classifier_consolidation_structural_decision_predicate_2026-05-26.md` | `??` | Historical/superseded structural decision predicate consolidation | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_s_structural_predicate_completeness_fix_2026-05-26.md` | `??` | Historical/superseded predicate completeness fix | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_t_structural_add_approve_admission_decision_fix_2026-05-26.md` | `??` | Historical/superseded decision predicate fix | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_u_stocking_catalog_admission_decision_fix_2026-05-26.md` | `??` | Historical/superseded stocking/catalog decision fix | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_v_catalog_stocking_passive_carry_source_decision_fix_2026-05-27.md` | `??` | Historical/superseded catalog stocking decision fix | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_w_product_procurement_availability_decision_fix_2026-05-27.md` | `??` | Historical/superseded procurement/availability decision fix | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_x_restock_replenish_inventory_decision_fix_2026-05-27.md` | `??` | Historical/superseded inventory decision fix | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_y_inventory_adjustment_on_hand_phase_out_decision_fix_2026-05-27.md` | `??` | Historical/superseded inventory adjustment decision fix | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_z1_inventory_build_cut_drawdown_liquidation_decision_fix_2026-05-27.md` | `??` | Historical/superseded inventory decision fix | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_z2_inventory_disposal_build_up_decision_fix_2026-05-27.md` | `??` | Historical/superseded inventory disposal decision fix | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_z3_obsolescence_scrap_write_down_decision_fix_2026-05-27.md` | `??` | Historical/superseded write-down decision fix | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_z4_enterprise_structural_intent_classifier_refactor_2026-05-27.md` | `??` | Historical/superseded structural/lexical classifier refactor | Archive/package-exclude as historical |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y_z5_pricing_discount_valuation_boundary_fix_2026-05-27.md` | `??` | Historical/superseded pricing/discount boundary fix | Archive/package-exclude as historical |

### V1-R/Z Reports

Count: `0`

No `qwen_erp_v1_r_z*.md` reports were found.

### Rejected V1-IB-B Structural Reports

Count: `3`

All three are currently `??` untracked dirty artifacts. They are rejected/superseded evidence because accepted V1-IB-B is the evidence-only proposal classifier plus V1-IB-A/Q validator path, not the 2026-05-28 deterministic structural classifier path.

| Path | Git status | Classification | Why not current release evidence | Package/release risk | Proposed future action |
| --- | --- | --- | --- | --- | --- |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_deterministic_structural_classifier_2026-05-28.md` | `??` | Rejected/superseded | Superseded by accepted V1-IB-B proposal-classifier closure; old structural classifier is not accepted authority | Title/body can be mistaken for accepted V1-IB-B evidence | Archive/package-exclude or clearly label as rejected in approved cleanup branch |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_a_factual_lookup_precedence_raw_safety_hardening_2026-05-28.md` | `??` | Rejected/superseded | Part of old structural classifier hardening chain, not accepted B-A proposal evidence | Could confuse rejected B-A with accepted B-A evidence strictness fix | Archive/package-exclude or clearly label as rejected in approved cleanup branch |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_b_passive_action_needed_structural_hardening_2026-05-28.md` | `??` | Rejected/superseded | Part of old structural classifier hardening chain, not accepted B-B proposal closure | Could confuse rejected B-B with accepted B-B closure checkpoint | Archive/package-exclude or clearly label as rejected in approved cleanup branch |

### Other Keyword-Matched Report Families

The keyword scan found additional reports with lexical, regex, synonym, phrase, structural classifier, false-allow, or decision-predicate language. Many are accepted V1-IB reports that mention these terms to prohibit lexical authority. A small number are older non-D-4-D families such as EC-7H/EC-7I and V1-R-V/V1-R-X.

Classification:
not a D-4-D blocker, but future accepted-evidence manifest should explicitly classify all governance report families before packaging.

## 4. Accepted V1-IB Superseding Evidence

Accepted V1-IB evidence superseding lexical patch-loop reports includes:

- `qwen_erp_v1_ib_0_enterprise_intent_boundary_rebuild_architecture_plan_2026-05-27.md`
- `qwen_erp_v1_ib_0_b_two_model_intent_boundary_authority_amendment_2026-05-27.md`
- `qwen_erp_v1_ib_0_c_proposal_completeness_constraint_addendum_2026-05-27.md`
- `qwen_erp_v1_ib_a_q_contract_validator_foundation_closure_gate_2026-05-29.md`
- `qwen_erp_v1_ib_b_b_proposal_classifier_closure_checkpoint_2026-05-29.md`
- `qwen_erp_v1_ib_c_5_runtime_integration_formal_closure_checkpoint_2026-05-31.md`
- `qwen_erp_v1_ib_d_1_authority_surface_inventory_call_site_map_2026-05-31.md`
- `qwen_erp_v1_ib_d_2_b_authority_consistency_closure_checkpoint_2026-05-31.md`
- `qwen_erp_v1_ib_d_3_b_trace_diagnostic_audit_closure_checkpoint_2026-05-31.md`
- `qwen_erp_v1_ib_d_4_legacy_authority_retirement_quarantine_plan_2026-05-31.md`
- `qwen_erp_v1_ib_d_4_a_legacy_restrict_only_assertion_tests_2026-05-31.md`
- `qwen_erp_v1_ib_d_4_b_rejected_structural_classifier_quarantine_removal_plan_2026-05-31.md`
- `qwen_erp_v1_ib_d_4_c_legacy_lexical_tests_classification_alignment_plan_2026-05-31.md`

Current enterprise evidence is:

- V1-IB contract authority.
- Validator-owned safe factual replay and invariants.
- Evidence-only proposal classifier output.
- Fail-closed runtime gates.
- Current raw/normalized message identity checks.
- Final-emission veto and payload sanitization.
- Trace/diagnostic redaction.
- Adversarial service tests.
- Legacy restrict-only proof.

It is not:

- lexical phrase matching,
- synonym patch loops,
- no-alarm logic,
- old structural-classifier hardening,
- or old V1-R/Y false-allow reports.

## 5. Archive / Package-Exclusion Options

### Option A: Move Stale Reports To Package-Excluded Historical Archive

Pros:

- Preserves forensic history.
- Removes stale reports from active `current_docs`.
- Makes package exclusion explicit.

Cons:

- Requires move approvals and path/reference scan.
- Requires package config or manifest rules.
- Archive labels must be strong to prevent future confusion.

### Option B: Keep In Current Docs But Add Explicit Rejected/Superseded Labels

Pros:

- Lowest operational risk.
- Avoids move/delete churn in dirty worktree.
- Preserves local references.

Cons:

- Leaves stale reports in active current docs.
- Does not fully solve package/release confusion.
- Requires editing many old reports or adding a manifest that readers actually consult.

### Option C: Delete Stale Reports From Package Branch After Historical Archive Snapshot

Pros:

- Cleanest release tree.
- Reduces reviewer and agent confusion.

Cons:

- Must not be done silently.
- Requires historical snapshot and QA approval.
- Risky from current dirty worktree.

### Option D: Generate Accepted-Evidence Manifest Separating Current, Historical, Rejected, And Unknown Evidence

Pros:

- Low-risk first step.
- Makes classification explicit before moves/deletes.
- Supports package review and future cleanup.

Cons:

- Does not remove stale files by itself.
- Must be enforced by later package/exclusion checks.

Recommended path:

Use Option D first, then Option A for historical archive/package exclusion in an approved cleanup/package-refresh branch. Do not silently delete stale reports from the dirty worktree.

## 6. Proposed Future Slice Sequence

No implementation occurs in D-4-D. Future bounded slices should be:

1. `D-4-D-1 accepted-evidence manifest plan/report`
   - Report-only.
   - Define manifest schema and classify current/historical/rejected/unknown governance evidence.

2. `D-4-D-2 historical/rejected report archive implementation in approved cleanup branch`
   - Implementation only after explicit QA/Counterpart approval.
   - Move or label stale reports according to the accepted manifest.

3. `D-4-D-3 package-exclusion verification`
   - Static/package scan.
   - Prove stale reports are excluded from release evidence/package surfaces.

4. `D-4-D-4 post-archive QA report`
   - Report verification, no release claim by itself.

5. `D-4-E package-readiness cleanup plan after D closure and QA approval`
   - Report-only first.
   - Should define package branch/worktree refresh, staging strategy, and final cleanup order.

## 7. Non-Negotiable Rules

- No old report may be treated as current release authority unless explicitly accepted in the V1-IB chain.
- No lexical patch-loop report may be used as enterprise closure evidence.
- No rejected structural report may be treated as accepted V1-IB-B evidence.
- No silent deletion from the dirty worktree.
- No archive/package config change without QA/Counterpart approval.
- No packaging until clean branch/worktree refresh and manifest approval.
- Current dirty worktree remains not package-ready.
- Browser/API UAT, staging, commit, push, deployment, strict enforcement, release readiness, enterprise closure, and V2 work remain out of scope.

## 8. Recommended Next Step

Audit result:

- No V1-R/Z reports were found.
- The V1-R/Y family is large but clearly classifiable as historical/superseded lexical patch-loop evidence.
- The three 2026-05-28 V1-IB-B structural reports are clearly rejected/superseded by accepted V1-IB-B proposal-classifier evidence.
- Additional keyword-matched non-D-4-D report families should be captured later in an accepted-evidence manifest, but they do not block this plan.

Recommended next step:

`V1-IB-D-4-E package-readiness cleanup plan`, report-only.

If QA/Counterpart wants a standalone manifest before D-4-E, use:
`V1-IB-D-4-D-1 accepted-evidence manifest plan/report`, report-only.

## 9. Verification

| Check | Result |
| --- | --- |
| Report present | PASS: `qwen_erp_v1_ib_d_4_d_stale_v1_r_y_z_report_archive_package_exclusion_plan_2026-05-31.md` exists |
| Counts of V1-R/Y and V1-R/Z reports | PASS: 31 V1-R/Y reports; 0 V1-R/Z reports |
| Rejected V1-IB-B structural reports | PASS: 3 files found |
| Scan for accepted V1-IB reports | PASS: accepted V1-IB report chain identified |
| `git diff --check` | PASS |
| `git diff --cached --check` | PASS |
| Qwen enterprise guardrail | PASS |
| Fake-Frappe service import | PASS: `FAKE_FRAPPE_IMPORT_PASS` |
| Direct assistant inventory | PASS: `0 / 1 / 27` |
| Raw assistant append scan | PASS: only `authorized_emission.py:271` and `authorized_emission.py:327` |
| Excluded/artifact scan | PASS: forbidden artifact status count `0` |
| Staged files count | PASS: `0` |
| Dirty worktree count | Recorded: `149` |
| Report hygiene scan | PASS: decision target present; no placeholder verification results remain |

Do not claim D-4 closure or V1-IB-D closure from D-4-D.
