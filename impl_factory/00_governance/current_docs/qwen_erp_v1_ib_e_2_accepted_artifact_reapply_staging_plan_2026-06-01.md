# V1-IB-E-2 Accepted Artifact Reapply / Staging Plan

Decision target:
`v1_ib_e_2_accepted_artifact_reapply_staging_plan_ready_for_counterpart_review`

Date: 2026-06-01

## 1. Scope And Boundary

V1-IB-E-2 is a report-only planning slice. It maps accepted source, test, and governance artifacts to their acceptance decisions and defines a future staging order and verification gates for a later QA-approved clean package/review branch.

Changed file in this slice:

- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_e_2_accepted_artifact_reapply_staging_plan_2026-06-01.md`

No branch was created. No branch was switched. No staging occurred. No files were committed or pushed. No source files were edited. No test files were edited. No old reports were edited. No package config changed. No files were moved, deleted, renamed, or archived. No source/test/report/config behavior changed except adding this E-2 report.

No cleanup, package, browser/API UAT, deployment, strict enforcement, release readiness, enterprise/product closure, or V2 work occurred. No keyword, regex, synonym, punctuation, phrase, lexical, or no-alarm route authority was added.

## 2. Accepted Artifact Source

D-4-E-1 accepted-evidence manifest is the source of accepted artifact classifications.

Accepted artifacts may be reapplied later only on a QA-approved clean branch. The current dirty tree must not be staged directly and must not be used as the package branch.

E-2 is a planning map only. It does not perform reapply, staging, cleanup, branch creation, branch switching, package creation, commit, push, or UAT.

## 3. Accepted Source Files To Reapply

Future clean-branch reapply should preserve these accepted source/runtime artifacts.

| Source file | Dirty-tree status | Accepted decision reference | Reason to preserve | Required verification after reapply | Staging order recommendation |
| --- | --- | --- | --- | --- | --- |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py` | `M` | C-2/C-3/C-4/C-5, D-2-A, D-3-A, D-4-A | Runtime integration, pre-routing/report/visible-context/model/trace authority gates, stale report-routing fix, diagnostic redaction behavior, legacy restrict-only merge behavior | Runtime integration tests, C-3 service tests, D tests, accepted baseline, guardrail, fake-Frappe import, diff check | Phase 1 |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py` | `M` | C-2-A/C-2-B/C-2-C, D closure evidence | Final-emission V1-IB contract veto, stale contract rejection, payload sanitization, authorized assistant append sinks | Final-emission veto tests, authorized-emission tests, raw append scan, accepted baseline | Phase 1 |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_contract.py` | `??` | V1-IB-A/Q | Accepted validator foundation and sole authority contract schema | Contract validator tests, runtime integration tests, compile | Phase 1 |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_runtime_integration.py` | `??` | V1-IB-C-2/C-5, D-2-B | Accepted runtime glue for proposal evidence -> validator-owned V1-IB authority path | Runtime integration tests, D authority consistency tests, compile | Phase 1 |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_proposal_classifier.py` | `??` | V1-IB-B/B-B | Accepted evidence-only proposal classifier feeding validator; not route authority | Proposal classifier tests, contract validator integration tests, compile | Phase 1 |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/user_intent_boundary.py` | `??` | D-4-A | Retain only if still required by runtime as legacy restrict-only/fail-closed dependency; never allow authority | D-4-A legacy restrict-only tests, D authority tests, import scan confirming it cannot expand V1-IB authority | Phase 1 only if still imported and documented restrict-only |

Source staging rule:
Only accepted source/runtime files should be staged on a future approved clean branch. Rejected structural classifier source must not be staged as current evidence.

## 4. Accepted Test Files To Reapply

Future clean-branch reapply should preserve accepted test coverage and exclude old direct lexical tests unless rewritten/aligned and accepted in a later slice.

| Test family | Path / pattern | Decision reference | Reason to preserve | Required test command |
| --- | --- | --- | --- | --- |
| Contract validator tests | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_intent_boundary_contract_validator.py` | A-Q | Verifies validator-owned route authority and fail-closed contract invariants | `python3 -m unittest ai_assistant_ui.tests.test_v1_ib_intent_boundary_contract_validator` |
| Proposal classifier tests | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_intent_boundary_proposal_classifier.py` | B-B | Verifies classifier remains evidence-only and does not emit route-authority fields | `python3 -m unittest ai_assistant_ui.tests.test_v1_ib_intent_boundary_proposal_classifier` |
| Runtime integration tests | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_integration.py` | C-2/C-2-B/C-5 | Verifies runtime gates and helper alignment with current V1-IB contract authority | `python3 -m unittest ai_assistant_ui.tests.test_v1_ib_runtime_integration` |
| Final-emission veto tests | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_final_emission_contract_veto.py` | C-2-A/C-2-C | Verifies stale/missing/mismatched V1-IB contracts cannot authorize final emission | `python3 -m unittest ai_assistant_ui.tests.test_v1_ib_runtime_final_emission_contract_veto` |
| Runtime adversarial pre-routing/final-emission tests | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_adversarial_prerouting.py`; `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_adversarial_final_emission.py` | C-3-2 | Verifies unsafe/mixed prompts block before routing and final-emission leak proof holds | `python3 -m unittest ai_assistant_ui.tests.test_v1_ib_runtime_adversarial_prerouting ai_assistant_ui.tests.test_v1_ib_runtime_adversarial_final_emission` |
| C-3 service adversarial tests | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_service_adversarial_*.py` | C-3-4/C-3-5/C-3-6/C-3-7 | Verifies visible-context, report routing, model reasoning, report selector, trace redaction, and long-context full-stack adversarial service lanes | `python3 -m unittest ai_assistant_ui.tests.test_v1_ib_service_adversarial_visible_context ai_assistant_ui.tests.test_v1_ib_service_adversarial_report_routing ai_assistant_ui.tests.test_v1_ib_service_adversarial_model_reasoning ai_assistant_ui.tests.test_v1_ib_service_adversarial_report_selector ai_assistant_ui.tests.test_v1_ib_service_adversarial_trace_redaction ai_assistant_ui.tests.test_v1_ib_service_adversarial_long_context_full_stack` |
| D-2 authority consistency tests | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_d_cross_lane_contract_identity.py`; `test_v1_ib_d_authority_surface_consistency.py`; `test_v1_ib_d_trace_diagnostic_authority_consistency.py` | D-2/D-2-A/D-2-B | Verifies cross-lane current-contract identity and no optimistic signal can override V1-IB | `python3 -m unittest ai_assistant_ui.tests.test_v1_ib_d_cross_lane_contract_identity ai_assistant_ui.tests.test_v1_ib_d_authority_surface_consistency ai_assistant_ui.tests.test_v1_ib_d_trace_diagnostic_authority_consistency` |
| D-3 trace/diagnostic tests | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_d_trace_diagnostic_contract_audit.py` | D-3/D-3-A/D-3-B | Verifies blocked-turn diagnostic raw-message redaction and non-authoritative trace behavior | `python3 -m unittest ai_assistant_ui.tests.test_v1_ib_d_trace_diagnostic_contract_audit` |
| D-4-A legacy restrict-only tests | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_d_legacy_restrict_only.py` | D-4-A | Verifies legacy boundary can restrict/fail closed but cannot authorize beyond V1-IB | `python3 -m unittest ai_assistant_ui.tests.test_v1_ib_d_legacy_restrict_only` |
| Authorized-emission alignment tests | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_authorized_emission_contracts.py`; `test_service_control_authorized_emission_contracts.py` | C-2-B | Verifies legacy authorized-emission expectations require current V1-IB authority for governed business output | `python3 -m unittest ai_assistant_ui.tests.test_authorized_emission_contracts ai_assistant_ui.tests.test_service_control_authorized_emission_contracts` |

Excluded test note:
Old lexical `test_user_intent_boundary_*.py` files are not accepted current V1-IB release evidence unless rewritten/aligned and accepted in a later slice. `test_v1_ib_structural_classifier.py` is rejected/superseded and must not be reapplied as current evidence.

## 5. Accepted Governance Reports To Reapply

Future clean-branch reapply should preserve accepted-current governance evidence only.

| Governance report family | Classification | Package action | Notes |
| --- | --- | --- | --- |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_0*.md` | `accepted_current` | `preserve_reapply` | V1-IB architecture plan/amendments. |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_a_*.md` | `accepted_current` | `preserve_reapply` | Accepted A through A-Q validator/contract foundation reports. |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_*.md` excluding rejected 2026-05-28 structural reports | `accepted_current` | `preserve_reapply` | Accepted proposal-classifier evidence-only reports through B/B-B. |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_*.md` | `accepted_current` | `preserve_reapply` | Accepted runtime integration and adversarial service evidence through C-5. |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_*.md` through D-5 | `accepted_current` | `preserve_reapply` | Accepted authority consistency, trace/diagnostic, legacy/quarantine, manifest, and D closure evidence. |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_e_*.md` through E-2 | `accepted_current` after acceptance | `preserve_reapply` | E package-readiness planning boundary reports. |

Rejected/historical governance reports must not be presented as current evidence. If retained later, they must be clearly manifest-labeled historical/rejected or package-excluded.

## 6. Do-Not-Reapply As Current Evidence

The following must not be reapplied/staged as current V1-IB package evidence:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_structural_classifier.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_structural_classifier.py`
- old `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_user_intent_boundary_*.py` files unless rewritten/aligned and accepted
- old V1-R/Y lexical reports
- older V1-R reports unless QA explicitly classifies them as historical archive
- rejected 2026-05-28 V1-IB-B structural reports:
  - `qwen_erp_v1_ib_b_deterministic_structural_classifier_2026-05-28.md`
  - `qwen_erp_v1_ib_b_a_factual_lookup_precedence_raw_safety_hardening_2026-05-28.md`
  - `qwen_erp_v1_ib_b_b_passive_action_needed_structural_hardening_2026-05-28.md`
- unknown root-level file `=`
- unrelated EC-10-G governance report unless QA decides otherwise

## 7. Staging Order Plan For Future Approved Clean Branch

Future staging order, only after explicit QA approval:

| Future phase | Artifact scope | Required checks before next phase | Stop conditions |
| --- | --- | --- | --- |
| Phase 1 | Accepted V1-IB source modules | Python compile; import scan; runtime integration focused tests; no rejected structural classifier import | Any compile/import/test failure; unexpected source diff; legacy allow authority introduced |
| Phase 2 | Accepted V1-IB tests | Test discovery review; accepted baseline; D tests; C-3 service tests | Any failing accepted test unless explicitly documented as blocker-discovery; old lexical/rejected tests staged as current evidence |
| Phase 3 | Accepted governance reports | Manifest classification review; report hygiene; rejected/historical report exclusion check | Rejected/historical report staged as current evidence; unknown file `=` included |
| Phase 4 | Manifest/package-readiness reports | D-4-E-1 and E reports reviewed; package-readiness boundary statements preserved | Package readiness or release readiness claimed prematurely |
| Phase 5 | Verification-only before commit | Full verification gates; staged-file review; clean branch status review | Any verification failure; unexpected staged files; unclassified artifact present |

Rollback principle:
If reapply or staging fails on a future clean branch, abandon or reset only the clean branch under the separately approved procedure. Do not destructively modify the dirty evidence tree.

## 8. Verification Gates After Future Reapply

Future clean branch must pass:

- Python compile for accepted source/tests
- accepted baseline
- D tests
- C-3 service adversarial tests
- contract validator tests
- proposal classifier tests
- final-emission veto tests
- trace/diagnostic leak tests
- legacy restrict-only tests
- Qwen enterprise guardrail
- fake-Frappe import
- direct assistant inventory
- raw assistant append scan only authorized sinks
- rejected structural classifier import scan
- old lexical tests excluded or explicitly aligned
- historical reports not current evidence
- clean git status except explicitly intended staged files

Future package work must preserve the accepted authority model: only current, validated, hash-matching, trace-safe V1-IB contract authority can allow runtime business routing.

## 9. Current Risks

Current risks:

- No clean branch exists for package-readiness work.
- Dirty worktree count remains high.
- Unknown root-level file `=` remains unclassified.
- Rejected/historical artifacts remain physically present.
- No staging is approved.
- Package readiness is not approved.
- Browser/API UAT is not approved.
- Release readiness is not approved.
- Deployment is not approved.
- Strict enforcement is not approved.
- Enterprise/product closure is not approved.

The current dirty tree remains not package-ready.

## 10. Decision Requested

QA/Counterpart decision requested:

```text
accept_v1_ib_e_2_accepted_artifact_reapply_staging_plan
```

If accepted, the next step should be:

```text
V1-IB-E-3 rejected/historical artifact exclusion plan, report-only
```

E-2 does not approve clean branch creation, staging, package readiness, release readiness, browser/API UAT readiness, E implementation, enterprise/product closure, or V2.

## 11. Verification For E-2

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
| Dirty worktree count | PASS: `155` after adding E-2 report |
| Report hygiene scan | PASS: decision target present; no placeholder verification results remain |

If any future verification fails, do not fix source opportunistically. Document the failure, recommend a narrow follow-up slice, and stop.

Do not claim clean branch creation, staging, package readiness, release readiness, UAT readiness, E implementation, enterprise/product closure, or V2 work from E-2.
