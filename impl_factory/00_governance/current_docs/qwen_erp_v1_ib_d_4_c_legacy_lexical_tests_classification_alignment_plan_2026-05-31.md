# V1-IB-D-4-C Legacy Lexical Tests Classification / Alignment Plan

Decision target:
`v1_ib_d_4_c_legacy_lexical_tests_classification_alignment_plan_ready_for_counterpart_review`

Date: 2026-05-31

## 1. Scope And Boundary

V1-IB-D-4-C is a report-only planning slice. It classifies old lexical/user-intent tests and old V1-R/Y lexical hardening reports so they are not mistaken for current V1-IB release evidence.

No source, test, runtime, import, deletion, move, rename, quarantine, alignment, packaging, staging, commit, push, deployment, browser/API UAT, strict enforcement, release-readiness, or V2 work occurred.

No runtime or test behavior changed. No compatibility fallback was added. No keyword, regex, synonym, punctuation, phrase, or no-alarm authority was added.

## 2. Accepted Authority Model

Accepted V1-IB authority remains:

- Current, hash-matching, trace-safe, validated V1-IB contract is the sole runtime authority.
- Legacy lexical `user_intent_boundary.py` may only restrict or fail closed.
- Old lexical tests and old V1-R/Y reports are not current release authority.
- Lexical, regex, keyword, synonym, punctuation, phrase, and no-alarm logic cannot authorize routing.
- Classifier/proposer/semantic/model/report-selector/final-answer outputs cannot authorize routing without current V1-IB contract authority.

Old lexical artifacts may preserve useful historical safety intent, but any future retained assertion must be rewritten as V1-IB contract, restrict-only, fail-closed, redaction, or non-authority evidence.

## 3. Legacy Test Inventory

Static scan found five `test_user_intent_boundary_*.py` files. All five are currently untracked dirty artifacts and none is part of the accepted baseline group.

| Test file | Current git status | Imports legacy boundary? | Imports service? | Accepted baseline? | Purpose / behavior asserted | Useful safety intent? | Proposed future action | Risk if left unclassified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `tests/test_user_intent_boundary_contracts.py` | `??` | Yes | No | No | Direct tests for old `build_user_intent_boundary_contract`, categories, allowed values, report/context flags, validation, safe factual allows, unsafe policy/control boundaries, and phrase families. | Yes: broad unsafe family coverage and validator-shape ideas. | D-4-C-1 classify; D-4-C-2 rewrite useful unsafe/safe-neighbor probes as V1-IB contract/proposal-validator/restrict-only tests; quarantine direct legacy allow assertions. | Could imply legacy lexical contract validity is current authority. |
| `tests/test_user_intent_boundary_final_emission_veto.py` | `??` | Yes | No | No | Legacy final-emission veto tests, including policy/control/clarification vetoes, safe factual pass, visible-context pass, forged helper metadata, and selected-payload leak checks. | Yes: late-answer veto and leak-drop behavior overlaps with accepted V1-IB final-emission goals. | Rewrite useful leak/veto cases against current V1-IB final-emission helpers; quarantine legacy safe-pass allow assumptions. | Could duplicate or conflict with accepted V1-IB final-emission tests and confuse legacy allow as authority. |
| `tests/test_user_intent_boundary_lexical_fragility.py` | `??` | Yes | No | No | Phrase/table-driven lexical fragility probes for retention, catalog/product lifecycle, payment, prediction, mixed lookup+decision, true followups, and vague prompts. | Partly: prompt families are useful as adversarial probes. | Convert selected families into V1-IB proposal/contract/service fail-closed tests; do not retain phrase tables as enterprise-understanding evidence. | Highest patch-loop risk: phrase/synonym tables can be mistaken for current semantic safety proof. |
| `tests/test_user_intent_boundary_long_context_regression.py` | `??` | Yes | Yes | No | Legacy long-context/context-bleed and late final-veto tests using prior report/context artifacts and unsafe later prompts. | Yes: context-bleed and leak-prevention intent is valuable. | Compare against accepted C-3-6 long-context/full-stack tests; rewrite only unique gaps as V1-IB service tests; quarantine outdated helper expectations. | Could encode pre-V1-IB helper behavior and conflict with current raw-message-mandatory fail-closed rules. |
| `tests/test_user_intent_boundary_prerouting_gate.py` | `??` | Yes | Yes | No | Legacy pre-routing order, policy/control/clarification responses, visible-context suppression, safe factual and followup allow, pending clarification, and authorized-emission ordering. | Yes: order-of-gates and suppression intent can be useful. | Rewrite as V1-IB authority-path tests only where not already covered by C/D tests; align raw-message-mandatory helper expectations; quarantine direct legacy allow expectations. | Could imply legacy boundary should be built/applied as allow authority before V1-IB. |

Additional static scan:

- No `*v1_r_y*.py` or `*v1_r_z*.py` test files were found.
- `*lexical*.py` found only `test_user_intent_boundary_lexical_fragility.py`.
- `*long_context*.py` found `test_user_intent_boundary_long_context_regression.py` and accepted C-3 `test_v1_ib_service_adversarial_long_context_full_stack.py`.
- Accepted C/D tests may mock `build_user_intent_boundary_contract` to prove V1-IB dominance. Those are current non-authority dominance tests, not old lexical release evidence.

Accepted baseline dependency scan:

```text
ACCEPTED_BASELINE_LEGACY_TEST_DEPENDENCIES=[]
ACCEPTED_BASELINE_STRUCTURAL_DEPENDENCIES=[]
```

## 4. Legacy Report Inventory

Static governance scan:

- `qwen_erp_v1_r_y*.md` count: `31`
- `qwen_erp_v1_r_z*.md` count: `0`
- Rejected 2026-05-28 V1-IB structural reports count: `3`

Representative old V1-R/Y lexical hardening reports:

- `qwen_erp_v1_r_y_a_intent_boundary_lexical_regex_fragility_audit_2026-05-25.md`
- `qwen_erp_v1_r_y_b_lexical_false_allow_hardening_2026-05-25.md`
- `qwen_erp_v1_r_y_c_lexical_false_allow_hardening_2026-05-25.md`
- `qwen_erp_v1_r_y_d_true_followup_collision_hardening_2026-05-26.md`
- `qwen_erp_v1_r_y_g_true_followup_positive_allowlist_hardening_2026-05-26.md`
- `qwen_erp_v1_r_y_h_read_only_allowlist_unsafe_clause_veto_2026-05-26.md`
- `qwen_erp_v1_r_y_n_decision_phrase_structural_hardening_2026-05-26.md`
- `qwen_erp_v1_r_y_r_intent_boundary_classifier_consolidation_structural_decision_predicate_2026-05-26.md`
- `qwen_erp_v1_r_y_z4_enterprise_structural_intent_classifier_refactor_2026-05-27.md`
- `qwen_erp_v1_r_y_z5_pricing_discount_valuation_boundary_fix_2026-05-27.md`

Rejected/superseded V1-IB structural reports already identified by D-4-B:

- `qwen_erp_v1_ib_b_deterministic_structural_classifier_2026-05-28.md`
- `qwen_erp_v1_ib_b_a_factual_lookup_precedence_raw_safety_hardening_2026-05-28.md`
- `qwen_erp_v1_ib_b_b_passive_action_needed_structural_hardening_2026-05-28.md`

Accepted current V1-IB evidence that supersedes old lexical/structural evidence:

- V1-IB-A/Q contract/validator foundation and closure.
- V1-IB-B proposal classifier implementation, B-A strictness fix, and B-B closure.
- V1-IB-C runtime integration and C-3 adversarial service closure.
- V1-IB-D-1 authority surface inventory.
- V1-IB-D-2/D-2-A/D-2-B authority consistency and stale report-routing fix.
- V1-IB-D-3/D-3-A/D-3-B trace/diagnostic redaction audit and closure.
- V1-IB-D-4/D-4-A/D-4-B legacy restrict-only and rejected structural quarantine planning.

Classification:

| Artifact family | Classification | Package/release treatment |
| --- | --- | --- |
| V1-R/Y lexical hardening reports | Historical audit trail and superseded lexical patch-loop evidence | Package/release exclusion candidate or clearly marked historical archive |
| V1-R/Y long-conversation/context-bleed report | Historical audit trail; safety intent partly superseded by C-3-6 | Preserve only as history unless unique probes are rewritten under V1-IB |
| Rejected V1-IB-B 2026-05-28 structural reports | Rejected/superseded evidence | Quarantine/package-exclude per D-4-B |
| Accepted V1-IB-A/B/C/D reports | Current evidence | Retain as accepted V1-IB authority model evidence |

## 5. Alignment Strategy

Future bounded slices should be:

### D-4-C-1: Classify Old Lexical Tests

Report/test-inspection only.

Output:
file-by-file decision table:

- historical only
- rewrite as V1-IB contract/restrict-only test
- align with accepted fail-closed behavior
- quarantine/package-exclude
- delete only in approved cleanup branch

### D-4-C-2: Rewrite Useful Tests As V1-IB Assertions

Tests-only after approval.

Possible conversions:

- Unsafe prompt families become V1-IB contract validator/proposal classifier fail-closed probes.
- Long-context leak probes become V1-IB service/final-emission redaction tests if not already covered by C-3-6/D-3.
- Legacy final-emission veto probes become V1-IB final-emission current-contract-veto tests.
- Legacy pre-routing gate order probes become V1-IB single-authority-path tests.

### D-4-C-3: Quarantine Obsolete Lexical Phrase Tests

Report-only first, cleanup later only with approval.

Goal:
remove phrase-table and synonym-patch tests from active release evidence unless rewritten as V1-IB non-authority/adversarial probes.

### D-4-C-4: Verify Accepted Baseline And D Tests Do Not Depend On Old Lexical Tests

Static/test-only.

Required proof:

- accepted baseline passes without old lexical tests
- D-level tests pass without old lexical tests
- no runtime import depends on old lexical tests
- legacy `user_intent_boundary.py` remains restrict-only if still retained

### D-4-C-5: Docs/Report Archive And Package-Exclusion Plan

Report-only first.

Goal:
classify 31 V1-R/Y reports, rejected V1-IB structural reports, and any stale docs as historical/package-excluded before packaging.

## 6. Non-Negotiable Rules

- Do not silently delete legacy tests.
- Do not keep phrase/synonym tests as proof of enterprise understanding.
- Do not use old lexical tests as release acceptance evidence.
- Do not rewrite lexical tests into new keyword/regex/synonym route authority.
- Useful old tests must be converted into V1-IB contract, restrict-only, fail-closed, redaction, or non-authority assertions.
- Any cleanup requires QA/Counterpart approval and a package branch/refresh plan.
- Current dirty worktree is not package-ready.
- Browser/API UAT, packaging, staging, commit, push, deployment, strict enforcement, release readiness, enterprise closure, and V2 work remain out of scope.

## 7. Risk Assessment

Can old lexical tests mislead future agents?

Yes. Several tests use phrase tables, direct legacy builder calls, safe factual allow expectations, and old helper expectations that can look like enterprise safety proof if read without the V1-IB authority context.

Can old lexical tests authorize runtime today?

Expected no. Tests cannot authorize runtime, and accepted runtime authority remains V1-IB contract-gated. D-4-A also proved legacy output is restrict-only in runtime merge/fallback paths.

Are old lexical tests part of accepted baseline?

No. Static scan found no old `test_user_intent_boundary_*.py` dependency in the accepted baseline group.

Should they remain in current release evidence?

No, unless rewritten/aligned as V1-IB restrict-only, fail-closed, redaction, or non-authority tests.

Is immediate deletion safe?

No. The tree is dirty and not package-ready. Deletion/quarantine must wait for explicit QA/Counterpart approval and a cleanup/package-refresh branch.

Recommended approach:

Classify, rewrite useful restrict-only and leak-prevention assertions, then quarantine old phrase-patch evidence later.

## 8. Recommended Next Step

Audit result:

- No active accepted-baseline dependency on old lexical tests was found.
- No `v1_r_y` or `v1_r_z` Python test files were found.
- Five old `test_user_intent_boundary_*.py` files remain as untracked dirty artifacts.
- Old V1-R/Y lexical reports remain numerous and need archive/package-exclusion planning.

Recommended next step:

`V1-IB-D-4-D stale V1-R/Y/Z report archive/package-exclusion plan`, report-only.

No D-4-C-A blocker slice is required by this audit unless QA/Counterpart wants legacy lexical test alignment before D-4-D.

## 9. Verification

| Check | Result |
| --- | --- |
| Report present | PASS: `qwen_erp_v1_ib_d_4_c_legacy_lexical_tests_classification_alignment_plan_2026-05-31.md` exists |
| Static list of `test_user_intent_boundary_*.py` | PASS: 5 files found |
| Static imports of `user_intent_boundary.py` | PASS: old direct imports identified; accepted V1-IB tests use legacy mocks only for dominance evidence |
| Accepted baseline dependency scan | PASS: `[]` |
| V1-R/Y/Z report count scan | PASS: 31 V1-R/Y reports; 0 V1-R/Z reports |
| `git diff --check` | PASS |
| `git diff --cached --check` | PASS |
| Qwen enterprise guardrail | PASS |
| Fake-Frappe service import | PASS: `FAKE_FRAPPE_IMPORT_PASS` |
| Direct assistant inventory | PASS: `0 / 1 / 27` |
| Raw assistant append scan | PASS: only `authorized_emission.py:271` and `authorized_emission.py:327` |
| Excluded/artifact scan | PASS: forbidden artifact status count `0` |
| Staged files count | PASS: `0` |
| Dirty worktree count | Recorded: `148` |
| Report hygiene scan | PASS: decision target present; no placeholder verification results remain |

Do not claim D-4 closure or V1-IB-D closure from D-4-C.
