# V1-IB-D-4-E-1 Accepted Evidence Manifest

Decision target:
`v1_ib_d_4_e_1_accepted_evidence_manifest_ready_for_counterpart_review`

Date: 2026-05-31

## 1. Scope And Boundary

V1-IB-D-4-E-1 is a report-only manifest slice. It classifies dirty artifacts and governance evidence so a later approved clean package/review branch can preserve accepted evidence and exclude or quarantine historical, rejected, unrelated, and unknown artifacts.

No cleanup implementation occurred. No source, test, old report, runtime, config, import, packaging, deletion, move, rename, archive, package-exclusion, staging, commit, push, deployment, browser/API UAT, strict enforcement, release-readiness, enterprise closure, or V2 work occurred.

No source/test/report/config behavior changed except adding this manifest.

## 2. Manifest Schema

Each artifact or artifact family is classified using these fields:

| Field | Meaning |
| --- | --- |
| `path` | File path or path pattern from `/tmp/erpai_pr5_postmerge_verify` |
| `git_status` | Current `git status --short` classification such as `M` or `??` |
| `artifact_type` | `source`, `test`, `governance_report`, `unknown`, `config`, or `other` |
| `classification` | `accepted_current`, `historical_superseded`, `rejected_superseded`, `legacy_restrict_only`, `package_excluded_candidate`, `unrelated`, `unknown_needs_review`, or `needs_qa_decision` |
| `accepted_decision_reference` | Accepted slice or decision that supports package preservation, if any |
| `package_action` | `preserve_reapply`, `preserve_historical_archive`, `package_exclude`, `quarantine_later`, `investigate`, `do_not_package`, or `needs_qa_decision` |
| `risk_if_packaged_as_is` | Why packaging without manifest discipline is unsafe |
| `required_verification_before_packaging` | Future verification required before package/release inclusion |

## 3. Accepted Current Manifest

Accepted/current artifacts must be preserved and reapplied on a future clean package/review branch. They must still pass the required verification gates before staging or packaging.

| Path / family | Git status | Type | Classification | Decision reference | Package action | Risk if packaged as-is | Required verification before packaging |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py` | `M` | source | accepted_current | C-2/C-3/C-4/C-5, D-2-A, D-3-A, D-4-A | preserve_reapply | Runtime authority fixes could be mixed with unrelated dirty state | C/D service tests, baseline, guardrail, import, diff check |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py` | `M` | source | accepted_current | C-2-A/C-2-B/C-2-C, D closure evidence | preserve_reapply | Final-emission veto changes could be lost or mixed with stale payload logic | final-emission tests, raw append scan, leak tests |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_contract.py` | `??` | source | accepted_current | A-Q | preserve_reapply | Missing validator foundation breaks V1-IB authority | contract validator tests, compile |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_runtime_integration.py` | `??` | source | accepted_current | C-2/C-5, D-2-B | preserve_reapply | Missing runtime glue breaks single-authority path | runtime integration and D authority tests |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_proposal_classifier.py` | `??` | source | accepted_current | B-B | preserve_reapply | Missing evidence-only classifier breaks validator input path | proposal classifier tests |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_intent_boundary_contract_validator.py` | `??` | test | accepted_current | A-Q | preserve_reapply | Validator foundation unverified | accepted baseline |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_intent_boundary_proposal_classifier.py` | `??` | test | accepted_current | B-B | preserve_reapply | Proposal evidence honesty unverified | accepted baseline |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_integration.py` | `??` | test | accepted_current | C-2/C-2-B/C-5 | preserve_reapply | Runtime gates and helper alignment unverified | accepted baseline |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_final_emission_contract_veto.py` | `??` | test | accepted_current | C-2-A/C-2-C | preserve_reapply | Stale final-emission bypass could regress | accepted baseline |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_adversarial_prerouting.py` | `??` | test | accepted_current | C-3-2 | preserve_reapply | Pre-routing adversarial coverage missing | accepted baseline |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_adversarial_final_emission.py` | `??` | test | accepted_current | C-3-2 | preserve_reapply | Final-emission leak evidence missing | accepted baseline |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_service_adversarial_*.py` | `??` | test | accepted_current | C-3-4/C-3-5/C-3-6/C-3-7 | preserve_reapply | Service-level adversarial coverage missing | C-3 service group and accepted baseline |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_d_*.py` | `??` | test | accepted_current | D-2-B/D-3-B/D-4-A | preserve_reapply | D authority/trace/legacy restrict-only evidence missing | D tests and accepted baseline |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_authorized_emission_contracts.py` | `M` | test | accepted_current | C-2-B | preserve_reapply | Authorized-emission alignment could regress | accepted baseline |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_service_control_authorized_emission_contracts.py` | `M` | test | accepted_current | C-2-B | preserve_reapply | Service-control authorized emission alignment could regress | accepted baseline |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_0*.md` | `??` | governance_report | accepted_current | V1-IB architecture/amendments | preserve_reapply | Architecture basis omitted | manifest QA review |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_a_*.md` | `??` | governance_report | accepted_current | A-Q | preserve_reapply | Validator foundation evidence omitted | manifest QA review |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_*.md` excluding 2026-05-28 rejected structural reports | `??` | governance_report | accepted_current | B-B | preserve_reapply | Proposal-classifier evidence omitted or confused | manifest QA review |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_*.md` | `??` | governance_report | accepted_current | C-5 | preserve_reapply | Runtime integration closure evidence omitted | manifest QA review |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_*.md` through D-4-E-1 | `??` | governance_report | accepted_current | D-1 through D-4-E-1 | preserve_reapply | D authority/cleanup evidence omitted | manifest QA review |

Accepted current count before this manifest:

- accepted current source/runtime files: `2`
- accepted current V1-IB modules: `3`
- accepted current tests: `19`
- accepted current governance reports: `68`

This manifest adds one additional accepted governance report.

## 4. Historical / Superseded Manifest

Historical/superseded artifacts must not be treated as current release authority. They may be preserved in a historical archive or package-excluded location after QA approval.

| Path / family | Git status | Type | Classification | Decision reference | Package action | Risk if packaged as-is | Required verification before packaging |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_y*.md` | `??` | governance_report | historical_superseded | D-4-C/D-4-D | preserve_historical_archive | Lexical patch-loop reports could be mistaken for current enterprise evidence | archive/package-exclusion verification |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_r_l*.md` through `qwen_erp_v1_r_x*.md` older V1-R reports | `??` | governance_report | historical_superseded | D-4-E | preserve_historical_archive | Pre-V1-IB governance could confuse release chain | accepted-evidence manifest QA review |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_user_intent_boundary_*.py` | `??` | test | historical_superseded | D-4-C | quarantine_later | Old lexical tests could imply keyword/phrase authority | rewrite useful assertions as V1-IB tests or package-exclude |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_10_g_revised_docs_packaging_boundary_approval_request_2026-05-24.md` | `??` | governance_report | unrelated / needs_qa_decision | none in V1-IB chain | needs_qa_decision | Unrelated packaging report could contaminate V1-IB package evidence | QA decision before inclusion |

Historical inventory counts:

- V1-R/Y reports: `31`
- V1-R/Z reports: `0`
- older V1-R reports outside Y: `14`
- old direct user-intent/lexical tests: `5`
- unrelated governance reports needing QA decision: `1`

The 31 V1-R/Y files are the set enumerated in D-4-D. The older V1-R reports are:

- `qwen_erp_v1_r_l_controlled_environment_setup_decision_2026-05-24.md`
- `qwen_erp_v1_r_m_controlled_environment_setup_plan_readiness_decision_2026-05-25.md`
- `qwen_erp_v1_r_n_controlled_environment_provisioning_approval_request_2026-05-25.md`
- `qwen_erp_v1_r_o_a_provisioning_prerequisite_plan_fix_2026-05-25.md`
- `qwen_erp_v1_r_o_b_provisioning_infrastructure_options_decision_2026-05-25.md`
- `qwen_erp_v1_r_o_controlled_environment_provisioning_execution_plan_2026-05-25.md`
- `qwen_erp_v1_r_q_staged_index_construction_request_2026-05-24.md`
- `qwen_erp_v1_r_u_enterprise_boundary_context_bleed_fix_plan_2026-05-25.md`
- `qwen_erp_v1_r_v_a_intent_boundary_classifier_hardening_2026-05-25.md`
- `qwen_erp_v1_r_v_b_remaining_intent_boundary_classifier_hardening_2026-05-25.md`
- `qwen_erp_v1_r_v_intent_boundary_contract_schema_classifier_tests_2026-05-25.md`
- `qwen_erp_v1_r_w_pre_routing_intent_boundary_gate_2026-05-25.md`
- `qwen_erp_v1_r_x_b_final_emission_veto_payload_sanitization_fix_2026-05-25.md`
- `qwen_erp_v1_r_x_post_selection_final_emission_veto_2026-05-25.md`

## 5. Rejected / Superseded Manifest

Rejected/superseded artifacts must not be packaged as current evidence.

| Path | Git status | Type | Classification | Decision reference | Package action | Risk if packaged as-is | Required verification before packaging |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_structural_classifier.py` | `??` | source | rejected_superseded | D-4-B | package_exclude / quarantine_later | Could be mistaken for accepted V1-IB-B classifier | runtime import scan clean |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_structural_classifier.py` | `??` | test | rejected_superseded | D-4-B | package_exclude / quarantine_later | Could be mistaken for accepted V1-IB-B tests | accepted baseline independence scan |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_deterministic_structural_classifier_2026-05-28.md` | `??` | governance_report | rejected_superseded | D-4-B/D-4-D | package_exclude / historical archive | Could be mistaken for accepted B evidence | accepted-evidence manifest QA review |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_a_factual_lookup_precedence_raw_safety_hardening_2026-05-28.md` | `??` | governance_report | rejected_superseded | D-4-B/D-4-D | package_exclude / historical archive | Could be confused with accepted B-A strictness fix | accepted-evidence manifest QA review |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_b_passive_action_needed_structural_hardening_2026-05-28.md` | `??` | governance_report | rejected_superseded | D-4-B/D-4-D | package_exclude / historical archive | Could be confused with accepted B-B closure | accepted-evidence manifest QA review |

## 6. Legacy Restrict-Only Manifest

Legacy artifacts may remain only if they are required for current runtime restrict/fail-closed behavior and are described as non-authoritative.

| Path / family | Git status | Type | Classification | Decision reference | Package action | Risk if packaged as-is | Required verification before packaging |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/user_intent_boundary.py` | `??` | source | legacy_restrict_only | D-4-A | preserve_reapply only if runtime still imports it; otherwise quarantine later | Could be misdescribed as allow authority | D-4-A tests; legacy restrict-only scan |
| Runtime references to `build_user_intent_boundary_contract` and `merge_v1_ib_with_legacy_boundary` | existing source references | source | legacy_restrict_only | D-4/D-4-A | preserve_reapply while restrictive merge remains | Future edits could let legacy output expand V1-IB authority | D-4-A tests and authority consistency tests |
| `tests/test_user_intent_boundary_*.py` | `??` | test | historical_superseded / package_excluded_candidate | D-4-C | quarantine_later unless rewritten/aligned | Direct old tests can imply lexical authority | rewrite useful probes as V1-IB tests before inclusion |

Legacy rule:
`user_intent_boundary.py` must not be package-described as allow authority. It can only be retained as a restrict-only/fail-closed companion if current source still depends on it.

## 7. Unknown / Needs Review

File:
`=`

Inspection result:

- Path: `/tmp/erpai_pr5_postmerge_verify/=`
- Git status: `??`
- Size: `85023` bytes
- Detected type: ASCII text
- First safe content summary: appears to be static grep/output lines referencing `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py` with line numbers and snippets, for example `service.py:18: return getattr(module, symbol_name)(*args, **kwargs)`.
- Sensitivity: no business data observed in first 512 safe-decoded characters, but the full file was not semantically reviewed.
- Why it exists: likely accidental shell redirection or captured scan output from a prior static audit; not inferable with certainty.

Manifest classification:

| Path | Git status | Type | Classification | Package action | Risk if packaged as-is | Required verification before packaging |
| --- | --- | --- | --- | --- | --- | --- |
| `=` | `??` | unknown / text scan output | unknown_needs_review | investigate / do_not_package until classified | Unknown root-level artifact could leak source snippets or contaminate package | QA classification or approved deletion in cleanup branch |

Do not delete the file in D-4-E-1.

## 8. Package Action Summary

Primary package action counts before adding this manifest:

| Package action | Count | Notes |
| --- | ---: | --- |
| `preserve_reapply` | 93 | accepted runtime/source/modules/tests/reports plus `user_intent_boundary.py` as legacy restrict-only if still imported |
| `preserve_historical_archive` | 45 | 31 V1-R/Y reports plus 14 older V1-R reports |
| `package_exclude` | 5 | rejected structural source/test and three rejected structural reports |
| `quarantine_later` | 5 | old direct `test_user_intent_boundary_*.py` tests unless rewritten/aligned |
| `investigate` | 1 | unknown file `=` |
| `needs_qa_decision` | 1 | unrelated EC-10-G governance report |

Do-not-package-as-current-evidence count:
`57` artifacts/families before this manifest, including historical, rejected, quarantine-later, investigate, and needs-QA-decision categories.

This manifest adds one accepted governance report to preserve/reapply after QA acceptance.

## 9. Clean Branch Reapply Guidance

Future package branch procedure:

1. Refresh from current `main`.
2. Create a clean package/review branch only after QA approval.
3. Reapply only `preserve_reapply` artifacts from the accepted manifest.
4. Exclude/quarantine `historical_superseded` and `rejected_superseded` artifacts.
5. Investigate `unknown_needs_review` artifacts before any package operation.
6. Run accepted baseline, D tests, C-3 service tests, final-emission veto tests, proposal/validator tests, and authorized-emission alignment tests.
7. Run guardrail, fake-Frappe import, direct assistant inventory, raw append scan, trace leak tests, compile, diff checks, and artifact scans.
8. Request QA package approval before staging, commit, push, packaging, or UAT.

Do not package from the current dirty worktree.

## 10. Verification

| Check | Result |
| --- | --- |
| Report present | PASS: `qwen_erp_v1_ib_d_4_e_1_accepted_evidence_manifest_2026-05-31.md` exists |
| Dirty count | Pre-report recorded: `150`; final count recorded: `151` |
| Manifest artifact counts | PASS: action counts recorded above |
| File `=` safe inspection result | PASS: ASCII text, 85023 bytes, likely scan output; classified `unknown_needs_review` |
| `git diff --check` | PASS |
| `git diff --cached --check` | PASS |
| Qwen enterprise guardrail | PASS |
| Fake-Frappe service import | PASS: `FAKE_FRAPPE_IMPORT_PASS` |
| Direct assistant inventory | PASS: `0 / 1 / 27` |
| Raw assistant append scan | PASS: only `authorized_emission.py:271` and `authorized_emission.py:327` |
| Excluded/artifact scan | PASS: forbidden artifact status count `0` |
| Staged files count | PASS: `0` |
| Report hygiene scan | PASS: decision target present; no placeholder verification results remain |

Do not claim package readiness, D-4 closure, V1-IB-D closure, release readiness, or enterprise closure from D-4-E-1.
